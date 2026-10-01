"""The only place a PROCESS run starts.  Jobs, isolation, the pool, resume.

Derived from ``arch_surgery/MDA_partitioning_experiment_v3/v3_runner.py``
(``run_job``, ``run_pool``, ``pool_workers``) and
``phase_a.py::run_eval_job``, read at ``9a8defa6``; task **A50 (harness-run)**.
The previous revision had the two phases' launchers written twice; here one
:class:`Job` covers both and the difference is which entry point it names.

Isolation is mandatory, and these are the reasons
------------------------------------------------
* **A fresh process per run.**  PROCESS holds its output-file handles as *class*
  attributes and its initialisation mutates a global, so two runs in one
  interpreter contaminate each other.  There is no in-process path in this
  package, and adding one would not be an optimisation.
* **Its own working directory.**  PROCESS writes its output files beside its
  input, so two runs sharing a directory overwrite each other's output.
* **``PYTHONPATH`` naming the tree under test.**  The editable install on this
  machine points at the main checkout and a working tree does not redirect it,
  so a run that relies on the install measures a tree nobody asked for.  The
  child asserts the **exact** tree it imported before doing any work.
* **The environment built from nothing.**  Every switch the harness knows about
  is removed and only what the arm declares is set, so an inherited value can
  never change what is measured without saying so.

Three refusals
--------------
A tree that is not the experiment's own copy is refused: records are only ever
made against the copy, and a measurement of some other tree produced by
forgetting a flag is exactly the failure the copy exists to prevent.  A switch
the tree does not implement is refused rather than dropped — running without it
would produce a successful run of a *different* arm under the right name.  And
**a job is never retried**: a crash is a taxonomy row, and re-running until it
works is how a failure stops being reported.

``resume`` skips a run only where the directory holds a **complete record of the
same job**.  A directory alone is never evidence: an interrupted run leaves one
behind.  "The same job" is decided by the **job identity** — every field of
:class:`Job` the pool composes into the run, listed once in
:data:`JOB_IDENTITY_FIELDS` — rendered as one dictionary, digested
(``records.job_digest``) and stamped into the record as ``job_identity`` and
``job_digest``.  It includes the **run kind**: a campaign record is never kept
for a gate's job nor a gate record for a one-seed smoke's, because the kind is
the only thing that afterwards says what a record may be used for, and keeping
one across kinds would launder that stamp by moving a directory.  It also
includes δ, the predicate mode, the pin, the stencil point, the entry state,
the overrides and the audit position: before task **A72
(resume-identity-and-shared-pool)** the comparison was six fields and the
directory layout was what kept two jobs differing only in one of those apart
(issue I-23) — a rule held by convention, not by the record.

The shared run pool (survey item B1)
------------------------------------
A job that names no ``outdir`` runs under **one directory per distinct job
identity**, ``runs/gates/_runs/<phase>_<arm>_<configuration>_seed<NNN>_<kind>_<digest>``
(:func:`directory_for`).  Two gates composing the same job therefore share one
record instead of making it twice, and a gate that deliberately runs the same
arm a second way — a hand-composed environment, a doctored entry state, a
different audit position — differs in an identity field and gets its own
directory by construction.  A job made once in this invocation is not made
again by a later gate of the same press (:data:`_MADE_THIS_INVOCATION`; the
record is still checked, as everywhere).
"""

from __future__ import annotations

import dataclasses
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from ..experiment import arms as arms_mod
from ..experiment import input_files as input_files_mod
from . import process_log as process_log_mod
from . import records as records_mod
from ..experiment import switches as switches_mod
from .config import EXPERIMENT_DIR, TEST_SETS, Campaign, Config, tau_rule_named

#: Default per-run wall-clock limit.  Not a budget: reaching it is a
#: ``timeout`` taxonomy row, recorded and never re-run at a longer limit.
DEFAULT_TIMEOUT_S = 5400

#: Environment variable that overrides the declared pool width, so a task can
#: run light work at one worker while a heavy campaign holds the machine.  The
#: width actually used is stamped into every stage record.
WORKERS_VARIABLE = "HARNESS_WORKERS"

#: The child entry points, by phase.  ``census`` is not a phase of the
#: experiment: it is the stage that observes what the models write and read, and
#: it runs here rather than beside here so that it gets the same isolation every
#: other PROCESS run gets (task A51 (harness-artifacts) added it).
ENTRY_POINT = {"A": "evaluate.py", "B": "optimise.py", "census": "census.py"}

#: Where those entry points live: ``harness/child/``, the subpackage a
#: measurement subprocess imports.  This module is in ``harness/core/``.
CHILD_DIR = Path(__file__).resolve().parent.parent / "child"


class PoolError(RuntimeError):
    """A refusal to start a run.  Never downgraded into a warning."""


def workers(campaign: Campaign) -> int:
    """The pool width: the campaign's declared W unless overridden."""
    try:
        return max(1, int(os.environ.get(WORKERS_VARIABLE, campaign.workers)))
    except ValueError:
        return campaign.workers


@dataclass
class Job:
    """One run: which arm, on which configuration, from which start.

    ``regime`` says how the start is displaced; ``stencil_column`` /
    ``stencil_sign`` name the point when it is a stencil one.  ``entry_state``
    is the snapshot the run is entered from — the reference fixed point for a
    displaced entry, or the forward point's exit for a backward stencil point.
    """

    phase: str
    arm: str
    config: Config
    seed: int
    #: Where the run goes.  ``None`` — the default for every gate job — means
    #: the shared pool: :func:`directory_for` resolves it from the identity,
    #: and :func:`run` writes the resolved path back here.  A chain job and
    #: gate G1's two captures name theirs explicitly.
    outdir: Path | None = None
    regime: str = "unperturbed"
    delta: float | None = None
    pin_hex: str | None = None
    entry_state: Path | None = None
    stencil_column: int | None = None
    stencil_sign: int = 1
    run_kind: str = "campaign"
    predicate_mode: str = "frozen"
    #: Which components the block loops test, and at which tolerance (driver
    #: change DR11).  ``None`` — the default at every construction site —
    #: means *the campaign's*, resolved by :func:`resolve_settings` at the
    #: first pool call and written back here; a value differing from the
    #: campaign's is admitted only for a declared supplementary stage
    #: (``config.SupplementaryStage``) and refused otherwise, so a campaign
    #: never mixes test sets (D39).  Both are identity fields: rendered only
    #: where they differ from V4's (the fallback at 1e-6), so that a fallback
    #: job carries V4's identity and every record made before DR11 is the
    #: fallback's (``records.IDENTITY_DEFAULTS_WHEN_ABSENT``).
    test_set: str | None = None
    tau: float | None = None
    #: The campaign's named tolerance rule, where the job's τ came from one
    #: (``config.TauRule``): resolved by :func:`resolve_settings` — the
    #: campaign's rule for a job that takes the campaign's τ, None for a job
    #: that names its own (a supplementary stage, the reproduction gate).  An
    #: identity field rendered only when set, so no record made without a
    #: rule moves, and a rule's record never resolves into a ``--tau``
    #: campaign's record at the same value.
    tau_rule: str | None = None
    #: The wall-clock timers (DR12): ``None`` means the campaign's, resolved
    #: by :func:`resolve_settings`; an identity field rendered only when on
    #: (``records.IDENTITY_DEFAULTS_WHEN_ABSENT``), so every gate record keeps
    #: its identity and a timed job has a digest no untimed record has.
    timers: bool | None = None
    node_census: bool = True
    #: For a ``census`` job only: which entry the census is taken at, and
    #: whether the read half of the instrument is on.
    census_entry: str = "evaluation"
    census_read: bool = True
    force_maxcal: int | None = None
    timeout: int = DEFAULT_TIMEOUT_S
    #: Environment overrides applied *on top of* the arm's composition, for a
    #: gate that runs an arm with one switch deliberately wrong.  A value of
    #: None removes the variable.
    override_env: Mapping[str, str | None] = field(default_factory=dict)
    #: Switch terms the **reproduction gate** deliberately sets to something
    #: other than the campaign's composition, term -> value, because that gate
    #: reproduces the previous revision and the previous revision ran the arm
    #: that way.  Refused for a campaign run, checked against the arm's own
    #: composition, and stamped into every record it produces; see
    #: :func:`environment_for`.
    reproduction_overrides: Mapping[str, str] = field(default_factory=dict)
    #: Where an optimisation run takes its exit audit.  The default is the
    #: position the plan declares for every arm; the other position,
    #: ``after_run``, may be asked for only by a stage
    #: :data:`harness.core.records.AUDIT_POSITION_AFTER_RUN_CALLERS` names,
    #: which says so in ``audit_position_caller``.  Refused otherwise, and for
    #: every campaign run, by :func:`environment_for`.
    audit_position: str = records_mod.AUDIT_POSITION_DECLARED
    #: The registry name of the stage asking for a position other than the
    #: declared one.  Stamped into the run's ``command.json`` beside the
    #: record, and into the caller's own record; None for a run at the
    #: declared position.
    audit_position_caller: str | None = None

    def identity(
        self, runs_dir: Path | None = None, *, campaign: "Campaign | None" = None
    ) -> dict[str, Any]:
        """Every identity field, rendered as JSON-safe values, in declared order.

        ``campaign`` resolves an unresolved test set and tolerance first
        (:func:`resolve_settings`); a caller outside the pool that renders a
        job it built itself passes it.  Without it an unresolved job is
        refused rather than rendered as V4's.

        The one construction of "the same job": :attr:`key`, the digest and the
        shared pool's directory are all derived from this dictionary.  Paths
        are rendered relative to *runs_dir* where they lie under it — a seeded
        or relocated worktree carries its records under another absolute path
        and is still the same job — and as given otherwise.  Mappings are
        rendered with sorted keys and string values, ``None`` kept as null.
        """
        if campaign is not None and (
            self.test_set is None or self.tau is None or self.timers is None
        ):
            resolve_settings(self, campaign)
        rendered: dict[str, Any] = {}
        for name in JOB_IDENTITY_FIELDS:
            if name == "configuration":
                rendered[name] = self.config.name
                continue
            value = getattr(self, name)
            if name in records_mod.IDENTITY_DEFAULTS_WHEN_ABSENT:
                # DR11: the test set and the tolerance are identity fields
                # rendered only where they differ from V4's, so a fallback
                # job carries V4's identity (see the field's comment).  An
                # unresolved value is refused: a job rendered before the pool
                # resolved it against the campaign would render as V4's.
                if name == "tau_rule" and value is None:
                    # No rule is a resolved value: the default every record
                    # made without one carries, rendered by its absence.
                    continue
                if name == "timers" and value is None:
                    # DR12: an unresolved instrument switch renders as off --
                    # the default every record carries -- never as a refusal:
                    # a job rendered without a campaign (a tooth, a listing)
                    # asks about its architecture, and the timers are not one.
                    continue
                if value is None:
                    raise PoolError(
                        f"the job's {name} is unresolved: identity was asked "
                        f"for before pool.resolve_settings ran against a "
                        f"campaign, and an unresolved {name} would render as "
                        f"V4's"
                    )
                if name == "tau":
                    value = float(value)
                if value == records_mod.IDENTITY_DEFAULTS_WHEN_ABSENT[name]:
                    continue
                rendered[name] = value
                continue
            if name == "audit_position":
                # What the run will stamp, not the field's default: the pool
                # composes a position for an optimisation only, and an
                # evaluation audits at its one position whatever the job says.
                value = records_mod.effective_audit_position(self.phase, value)
            elif name == "audit_position_caller" and self.phase != "B":
                value = None
            if isinstance(value, Path):
                value = _render_path(value, runs_dir)
            elif isinstance(value, Mapping):
                value = {
                    str(k): (None if v is None else _render_string(str(v), runs_dir))
                    for k, v in sorted(value.items())
                }
            rendered[name] = value
        return rendered

    @property
    def key(self) -> str:
        """The readable half of the identity, for messages and listings.

        Derived from :meth:`identity`, not written beside it: the fields that
        distinguish most jobs, in the order a reader wants them, with the ones
        that are usually at their default appended only when they are not.
        Paths and mappings are not rendered here — the digest carries them.
        An unresolved test set or tolerance reads as ``unresolved`` here
        rather than refusing: the key is for messages, the digest is not.
        """
        if self.test_set is None or self.tau is None:
            resolved = dataclasses.replace(
                self,
                test_set=self.test_set or "unresolved",
                tau=self.tau if self.tau is not None else float("nan"),
            )
            return readable_key(resolved.identity())
        return readable_key(self.identity())


def _render_path(path: Path, runs_dir: Path | None) -> str:
    path = Path(path)
    if runs_dir is not None:
        try:
            return path.resolve().relative_to(Path(runs_dir).resolve()).as_posix()
        except ValueError:
            pass
    return path.as_posix()


def _render_string(value: str, runs_dir: Path | None) -> str:
    """A mapping value, with an absolute path under the experiment directory
    made relative to it.

    ``override_env`` values are strings, and gate G5's hand-composed run puts
    the three committed artifact paths in it.  Rendered as the absolute paths
    they are, the identity — and so the digest and the record — was one per
    working tree, and the job never resumed anywhere but where it was made
    (found by A78 (arm-renames)' press: `--jobs all` listed those three jobs
    "no record on disk" in every worktree but the one that made them).  A
    value that is an absolute path under the experiment directory
    (``config.EXPERIMENT_DIR``; it was ``runs/``'s parent until the run-ID
    layout put the campaign's folder one level down, task A107
    (v5-campaign-settings-keys), and naming it keeps every rendering as it
    was) is rendered relative to it, ``experiment:harness/data/…``;
    one under ``runs/`` relative to that, as :func:`_render_path` does; any
    other string is left as it is.  Only G5's three hand-composed jobs carry
    such a value, so only their digests changed.
    """
    if runs_dir is None or not value.startswith("/"):
        return value
    runs = Path(runs_dir).resolve()
    path = Path(value)
    try:
        return path.resolve().relative_to(runs).as_posix()
    except ValueError:
        pass
    try:
        return "experiment:" + path.resolve().relative_to(EXPERIMENT_DIR.resolve()).as_posix()
    except ValueError:
        return value


#: Every field of :class:`Job` the pool composes into a run — the command line
#: (:func:`_command`), the environment (:func:`environment_for`), the entry
#: state — **in one place**.  ``configuration`` stands for ``config.name``.
#: :meth:`Job.identity`, :meth:`Job.key`, the record's ``job_digest`` and the
#: shared pool's directory are all derived from this tuple, so there is one
#: construction of "the same job" and :func:`records.is_complete_for` compares
#: it.  A field added to :class:`Job` must be put here or in
#: :data:`JOB_NON_IDENTITY_FIELDS`; the module refuses to import otherwise.
JOB_IDENTITY_FIELDS: tuple[str, ...] = (
    "phase",
    "arm",
    "configuration",
    "seed",
    "regime",
    "run_kind",
    "delta",
    "pin_hex",
    "entry_state",
    "stencil_column",
    "stencil_sign",
    "predicate_mode",
    "test_set",
    "tau",
    "tau_rule",
    "timers",
    "node_census",
    "census_entry",
    "census_read",
    "force_maxcal",
    "override_env",
    "reproduction_overrides",
    "audit_position",
    "audit_position_caller",
)

#: The fields that are **not** identity, each with the reason: ``config`` is
#: rendered as ``configuration``; ``outdir`` is what the identity *determines*;
#: ``timeout`` is a limit on the run, not a property of it — a run that
#: finished under a shorter limit is the same run, and one that reached the
#: limit has no ``ok`` record and is never kept.
JOB_NON_IDENTITY_FIELDS: tuple[str, ...] = ("config", "outdir", "timeout")


def _assert_every_job_field_is_classified() -> None:
    declared = {f.name for f in dataclasses.fields(Job)}
    classified = (set(JOB_IDENTITY_FIELDS) - {"configuration"}) | set(
        JOB_NON_IDENTITY_FIELDS
    )
    if declared != classified:
        raise TypeError(
            f"pool.Job has fields {sorted(declared ^ classified)} that "
            f"JOB_IDENTITY_FIELDS and JOB_NON_IDENTITY_FIELDS do not classify.  "
            f"A field the pool composes into a run and the identity does not "
            f"name is a job --resume cannot tell from another (I-23)."
        )


_assert_every_job_field_is_classified()


def readable_key(identity: Mapping[str, Any]) -> str:
    """``phase/arm/configuration/seedNNN/regime/kind`` plus what is off default."""
    parts = [
        f"{identity['phase']}",
        f"{identity['arm']}",
        f"{identity['configuration']}",
        f"seed{int(identity['seed']):03d}",
        f"{identity['regime']}",
        f"{identity['run_kind']}",
    ]
    if identity.get("delta") is not None:
        parts.append(f"delta={identity['delta']}")
    if identity.get("predicate_mode") not in (None, "frozen"):
        parts.append(f"mode={identity['predicate_mode']}")
    if identity.get("test_set") is not None:
        parts.append(f"set={identity['test_set']}")
    if identity.get("tau") is not None:
        parts.append(f"tau={identity['tau']!r}")
    if identity.get("tau_rule") is not None:
        parts.append(f"rule={identity['tau_rule']}")
    if identity.get("timers"):
        parts.append("timers")
    usual_position = records_mod.effective_audit_position(
        str(identity.get("phase")), records_mod.AUDIT_POSITION_DECLARED
    )
    if identity.get("audit_position") not in (None, usual_position):
        parts.append(f"audit={identity['audit_position']}")
    if identity.get("audit_position_caller"):
        parts.append(f"asked_by={identity['audit_position_caller']}")
    if identity.get("stencil_column") is not None:
        sign = "+" if int(identity.get("stencil_sign") or 1) > 0 else "-"
        parts.append(f"stencil={identity['stencil_column']}{sign}")
    if identity.get("force_maxcal") is not None:
        parts.append(f"maxcal={identity['force_maxcal']}")
    if identity.get("override_env"):
        parts.append("overridden")
    if identity.get("reproduction_overrides"):
        parts.append("reproduction_overrides")
    if identity.get("phase") == "census":
        parts.append(f"census={identity.get('census_entry')}")
    return "/".join(parts)


def resolve_settings(job: Job, campaign: Campaign) -> Job:
    """Fill the job's test set and tolerance from the campaign, or refuse.

    Driver change DR11, decision D39: the test set is a **campaign-level**
    setting, one value for every arm and both phases, never mixed within a
    campaign; the tolerance follows it (D23).  A job that names neither takes
    the campaign's.  A job that names other values is admitted **only** when
    a declared supplementary stage (``config.SupplementaryStage``) admits its
    phase, configuration and arm at exactly those values — the V5 plan's
    supplementary ``st_regression`` stage at the census set and 1e-12 — and
    is refused otherwise, naming what it asked for and what the campaign
    composes.  Resolved once, written back onto the job, and consulted by
    every pool entry so that a job's identity is never rendered unresolved.
    """
    test_set = campaign.test_set if job.test_set is None else job.test_set
    # A tolerance rule gives each configuration its own τ (config.TauRule);
    # a job that names no τ takes the campaign's for its configuration and
    # carries the rule's name, one that names its own keeps it and no rule.
    campaign_tau = campaign.tau_for(job.config)
    if job.tau is None:
        tau = campaign_tau
        if job.tau_rule is None:
            job.tau_rule = campaign.tau_rule
    else:
        tau = float(job.tau)
    if test_set not in TEST_SETS:
        raise PoolError(
            f"{job.arm}/{job.config.name}/seed{job.seed}: test set "
            f"{test_set!r} is not one this harness composes {TEST_SETS}"
        )
    if job.tau_rule is not None and job.tau_rule != campaign.tau_rule:
        raise PoolError(
            f"{job.arm}/{job.config.name}/seed{job.seed} carries tolerance rule "
            f"{job.tau_rule!r} while the campaign composes "
            f"{campaign.tau_rule!r}; refused rather than run under a rule the "
            f"campaign did not declare"
        )
    if test_set != campaign.test_set or float(tau) != float(campaign_tau):
        stage = campaign.supplementary_stage_for(
            phase=job.phase,
            configuration=job.config.name,
            arm=job.arm,
            test_set=test_set,
            tau=float(tau),
        )
        # The reproduction gate's criterion -- V4's fallback -- is admitted
        # for any job that is not a campaign record: GR's records are V4's
        # own numbers on the copy (D39: GR must PASS under the fallback) and
        # every gate that reads them composes GR's jobs under whatever
        # campaign the button was pressed from.  A campaign record is never
        # admitted at another setting than the campaign's.
        is_v4 = (
            test_set == records_mod.IDENTITY_DEFAULTS_WHEN_ABSENT["test_set"]
            and float(tau) == float(records_mod.IDENTITY_DEFAULTS_WHEN_ABSENT["tau"])
            and job.run_kind != "campaign"
        )
        if stage is None and not is_v4:
            raise PoolError(
                f"{job.arm}/{job.config.name}/seed{job.seed} asks for test set "
                f"{test_set!r} at tau={tau!r} while the campaign composes "
                f"{campaign.test_set!r} at tau={campaign_tau!r}, and no declared "
                f"supplementary stage admits those values for this phase, "
                f"configuration and arm.  A campaign never mixes test sets "
                f"(decision D39); refused rather than run under a setting the "
                f"campaign did not declare."
            )
    job.test_set = test_set
    job.tau = float(tau)
    if job.timers is None:
        job.timers = bool(campaign.timers)
    return job


def digest_for(job: Job, campaign: Campaign) -> str:
    """The job digest: sha256 over the canonical JSON of :meth:`Job.identity`."""
    resolve_settings(job, campaign)
    return records_mod.job_digest(job.identity(Path(campaign.runs_dir)))


#: Where the shared pool lives, relative to the campaign's ``runs/``.  Under
#: ``gates/`` so that every survey of "the gate runs" (``survey_heads``, the
#: run-kind gate, the stamp survey) sees it without a second root.
POOL_SUBPATH = Path("gates") / "_runs"


def pool_root(campaign: Campaign) -> Path:
    return Path(campaign.runs_dir) / POOL_SUBPATH


def canonical_directory_for(job: Job, campaign: Campaign) -> Path:
    """Where this job's record goes when none exists yet: its own ``outdir``,
    or the pool's directory — a pure function of the identity.

    The pool's name carries the readable fields first and the digest's first
    sixteen hex digits last: the digest is what makes it unique, the rest is
    for a reader.
    """
    if job.outdir is not None:
        return Path(job.outdir)
    resolve_settings(job, campaign)
    identity = job.identity(Path(campaign.runs_dir))
    digest = records_mod.job_digest(identity)
    name = (
        f"{identity['phase']}_{identity['arm']}_{identity['configuration']}_"
        f"seed{int(identity['seed']):03d}_{identity['run_kind']}_{digest[:16]}"
    )
    return pool_root(campaign) / name


#: Every record under a campaign's ``runs/``, by job digest — the digest as
#: :func:`records.read` reports it, that is, in today's arm names.  Built once
#: per process per ``runs/`` root, on first use, and kept current by
#: :func:`run` for the records it writes.  It exists because a record's
#: directory can carry a name the record no longer goes by: the arm renaming of
#: 2026-09-15 (``records.RECORDED_ARM_NAMES``) left every campaign directory
#: of a renamed arm under the arm's old name — and, for two of the three, the
#: old name is another arm's new one.  The record is the truth; the path is
#: where the pool found it.
_RECORD_INDEX: dict[str, dict[str, list[Path]]] = {}
_RECORD_INDEX_GUARD = threading.Lock()


def _record_index(campaign: Campaign) -> dict[str, list[Path]]:
    """Every record under **this run ID's folder** by digest — the one place
    step 2 of :func:`directory_for` searches, and so the confinement of that
    search to the run ID: a record in another run ID's folder is not in this
    index and is never a candidate (task A107 (v5-campaign-settings-keys))."""
    key = str(Path(campaign.runs_dir).resolve())
    with _RECORD_INDEX_GUARD:
        index = _RECORD_INDEX.get(key)
        if index is None:
            index = {}
            root = Path(campaign.runs_dir)
            if root.exists():
                for path in sorted(root.rglob("metrics.json")):
                    record = records_mod.read(path.parent)
                    digest = record.get("job_digest")
                    if isinstance(digest, str):
                        index.setdefault(digest, []).append(path.parent.resolve())
            _RECORD_INDEX[key] = index
        return index


def _index_record(campaign: Campaign, digest: str, directory: Path) -> None:
    """Tell the index where :func:`run` just put a record of *digest*."""
    index = _record_index(campaign)
    with _RECORD_INDEX_GUARD:
        index[digest] = [Path(directory).resolve()]


def forget_record_index() -> None:
    """Drop the index so the next resolution re-reads ``runs/``.  For a caller
    that moved records on disk in this process — a tooth, a relocation."""
    with _RECORD_INDEX_GUARD:
        _RECORD_INDEX.clear()


def directory_for(job: Job, campaign: Campaign) -> Path:
    """The directory this job's record is in, or goes in: **resolved by digest**.

    A gate that wants to *read* a job's record resolves it here without running
    anything, and two gates composing the same job resolve to the same place.
    The rule, in order:

    1. the job's canonical directory (:func:`canonical_directory_for`) holds a
       record of the same **readable identity** — arm, configuration, seed,
       phase, regime, run kind, as ``records.read`` reports them — then that
       directory is the job's, whatever the record's state (the resume
       comparison decides whether it is kept);
    2. otherwise, a record of exactly this job's **digest** is on disk under
       **this run ID's folder** ``runs/<run ID>/`` (``campaign.runs_dir``;
       the index :func:`_record_index` is built over that folder and no
       other, so another run ID's records are never candidates) — then that
       directory, whatever it is called, is the job's;
    3. otherwise the canonical directory, where the run will be made.

    Step 2 goes by digest and not by path because a directory name is the
    arm's name *at the time of the run*: after the renaming of 2026-09-15
    (``records.RECORDED_ARM_NAMES``) the directory ``…/evaluation/<config>/A1/``
    holds the records of today's ``A2``, and today's ``A1`` has its records
    under its old name.  A path-based lookup would hand ``A1`` the record of
    ``A2`` and, finding it not the same job, re-make ``A1`` on top of it.
    Step 1 comes first so that a caller naming an explicit directory for a
    deliberate second record of one identity — gate G1's two captures, at two
    commits by construction — keeps the directory it named.

    Two directories holding the same digest at step 2 is a refusal: the pool
    cannot say which record is the job's.

    **A job that names its own directory is resolved to it, and step 2 is
    never consulted for it** (issue I-29, in the form task A99
    (v5-schedule-and-prime) met it).  Gate G1's two captures are one identity
    at two commits in two named directories; on a tree whose ``after``
    directory did not exist yet, step 2 resolved the ``after`` capture by
    digest to the ``before`` records and re-made them in place — and resolved
    the reference arm's capture to *another* gate's record of the same digest
    (the input-file stage's baseline evaluation, the reproduction gate's pool
    record), so neither capture ever held the reference arm and the "before"
    side was destroyed by the press that was to compare against it.  A named
    directory is the caller's statement of where this record lives; a record
    of the same digest elsewhere is another caller's, and the pool has no
    business writing into it.  :func:`run` still refuses to remove a named
    directory that holds another job's record.

    **A directory under another gate's own root is never a candidate for an
    unnamed job** (issue I-36; task A105 (v5-resume-fixes-and-tau-rule)):
    step 2 skips every hit under ``runs/gates/<gate>/`` other than the
    shared pool itself (:func:`is_under_another_gates_root`).  Such a
    directory is a gate's *named* record — gate G1's ``before``/``after``
    captures, a straddle archived at two commits — and is the mirror image
    of I-29: an unnamed job resolved into it would read a capture made at
    another commit as its own record, and a press without ``--resume``
    would remove and re-make it.  Found on the reproduction gate's unnamed
    ``AR`` substitute, whose digest five of G1's captures carry, so that
    ``--jobs reproduction`` refused.  Hits elsewhere under ``runs/`` (the
    campaign's directories under the arms' recorded names, a stage's named
    directory such as the input-file stage's baseline evaluation) stay
    candidates, as before.
    """
    resolve_settings(job, campaign)
    canonical = canonical_directory_for(job, campaign)
    if job.outdir is not None:
        return refuse_another_runs_folder(canonical, campaign, job=job)
    identity = job.identity(Path(campaign.runs_dir))
    if (canonical / "metrics.json").exists():
        existing = records_mod.read(canonical)
        if all(
            existing.get(records_mod.IDENTITY_FIELDS_STAMPED_BY_THE_CHILD[name])
            == identity.get(name)
            for name in records_mod.READABLE_IDENTITY_FIELDS
        ):
            return canonical
    digest = records_mod.job_digest(identity)
    hits = [
        hit
        for hit in _record_index(campaign).get(digest, [])
        if not is_under_another_gates_root(hit, campaign)
    ]
    if not hits:
        return canonical
    resolved_canonical = canonical.resolve()
    if resolved_canonical in hits:
        return canonical
    if len(hits) > 1:
        raise PoolError(
            f"{job.key}: {len(hits)} directories under {campaign.runs_dir} hold "
            f"a record of this job's digest {digest[:16]} and none is the "
            f"canonical {canonical}: {[str(h) for h in hits]}.  The pool cannot "
            f"say which is the job's record; refused rather than picked."
        )
    return refuse_another_runs_folder(hits[0], campaign, job=job)


def other_run_folder(directory: Path, campaign: Campaign) -> str | None:
    """The run ID whose folder *directory* lies in, where that is **not** this
    campaign's; None where it is this campaign's folder, or outside ``runs/``
    altogether, or the campaign is a fixture with no run ID."""
    if campaign.runs_root is None:
        return None
    root = Path(campaign.runs_root).resolve()
    own = Path(campaign.runs_dir).resolve()
    resolved = Path(directory).resolve()
    try:
        resolved.relative_to(own)
        return None
    except ValueError:
        pass
    try:
        relative = resolved.relative_to(root)
    except ValueError:
        return None
    return relative.parts[0] if relative.parts else "(the top level of runs/)"


def refuse_another_runs_folder(directory: Path, campaign: Campaign, *, job: Job | None = None) -> Path:
    """*directory*, or a refusal where it lies in **another run ID's folder**.

    The run-ID layout's one rule (task A107 (v5-campaign-settings-keys)): a
    press under one run ID never reads, re-makes, moves or writes anything
    under another run ID's folder.  Step 2 of :func:`directory_for` cannot
    reach one — :func:`_record_index` is built over this campaign's folder
    alone — so the only way in is a job that **names** its directory there
    (``Job.outdir``, a ``--run --outdir``), and that is refused here, in the
    one function every pool entry resolves through, before any directory is
    made or removed.  A directory outside ``runs/`` altogether is the caller's
    explicit choice and is not this rule's business.
    """
    other = other_run_folder(directory, campaign)
    if other is not None:
        raise PoolError(
            f"{job.key + ': ' if job is not None else ''}{directory} lies under "
            f"runs/{other}/, another run ID's folder, while this press is "
            f"under runs/{campaign.run_id}/.  A press never reads, re-makes or "
            f"writes another run ID's records; refused."
        )
    return Path(directory)


def is_under_another_gates_root(directory: Path, campaign: Campaign) -> bool:
    """Whether *directory* lies under a gate's own root, ``runs/gates/<gate>/``,
    and not under the shared pool ``runs/gates/_runs/`` (issue I-36)."""
    gates_root = (Path(campaign.runs_dir) / POOL_SUBPATH.parent).resolve()
    try:
        relative = Path(directory).resolve().relative_to(gates_root)
    except ValueError:
        return False
    return bool(relative.parts) and relative.parts[0] != POOL_SUBPATH.name


def directories_for(jobs: Sequence[Job], campaign: Campaign) -> list[Path]:
    """One directory per **distinct** job, in first-seen order."""
    seen: dict[str, Path] = {}
    for job in jobs:
        directory = directory_for(job, campaign)
        seen.setdefault(str(directory), directory)
    return list(seen.values())


def job_listing(jobs: Sequence[Job], campaign: Campaign) -> list[dict[str, Any]]:
    """One row per distinct job: key, digest, directory, and whether a complete
    record of it is on disk — the resume decision, shown without running.

    What a gate's ``jobs`` declaration returns to the framework and what
    ``experiment_runner.py --jobs <gate>`` (and ``--jobs campaign``) prints.
    ``why_not_complete`` is :func:`why_not_kept`'s sentence — the whole of the
    decision :func:`run` takes under ``--resume``, the completeness contract
    and the composition check alike — or None where ``--resume`` would keep
    the record; it is computed from the record alone (rule (vii)).
    """
    runs_dir = Path(campaign.runs_dir)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for job in jobs:
        resolve_settings(job, campaign)
        identity = job.identity(runs_dir)
        digest = records_mod.job_digest(identity)
        if digest in seen:
            continue
        seen.add(digest)
        directory = directory_for(job, campaign)
        why = why_not_kept(
            job, campaign, identity=identity, digest=digest, directory=directory
        )
        rows.append(
            {
                "key": job.key,
                "job_digest": digest,
                "path": str(directory),
                "identity": identity,
                "why_not_complete": why,
            }
        )
    return rows


def seed_directory(seed: int) -> str:
    """A run directory's name.  ``seed000`` is the undisplaced start."""
    return f"seed{seed:03d}"


# --------------------------------------------------------------------------
# composing one job's environment
# --------------------------------------------------------------------------


def environment_for(job: Job, campaign: Campaign) -> tuple[dict[str, str], dict]:
    """The environment this job runs under, and what it asked for.

    A switch term the tree does not implement is **refused**, never dropped:
    running without it would produce a successful run of a *different* arm
    under the right name.  Until task **A72 (resume-identity-and-shared-pool)**
    a job could carry an *allowance* naming such terms, for the interval when
    an arm declared a switch no tree implemented yet; the last such switch
    landed with A59 and the mechanism was retired (survey item B4).  The
    refusal it guarded stays.

    ``reproduction_overrides`` is the only way a run happens with a switch set
    to something **other** than what its arm composes, and it is for a switch
    the tree *does* implement.  The reproduction gate reproduces the previous
    revision, and that revision wrote two arms' output files through upstream's
    output-time loop because the switch that turns it off did not exist yet.
    See :func:`_apply_reproduction_overrides` for the four things that refuse
    one; a campaign run carrying one is the first of them.
    """
    _assert_audit_position_declared(job)
    resolve_settings(job, campaign)
    arm = arms_mod.ARMS[job.arm]
    terms = arm.terms(
        job.config,
        pin_hex=job.pin_hex,
        predicate_mode=job.predicate_mode,
        campaign=campaign,
        seed=job.seed,
        test_set=job.test_set,
        tau=job.tau,
        timers=job.timers,
    )
    pending = sorted(switches_mod.unimplemented(terms))
    if pending:
        raise PoolError(
            f"{job.key}: the tree implements no switch for {pending} "
            + "; ".join(
                f"{t} (needs "
                f"{switches_mod.REGISTRY[t].pending_change or 'a driver change'})"
                for t in pending
            )
            + " — refused rather than run without it, which would be a "
            "successful run of a different arm under this arm's name"
        )
    terms = _apply_reproduction_overrides(job, terms)
    env = arms_mod.env_for(
        job.arm,
        job.config,
        seed=job.seed,
        pin_hex=job.pin_hex,
        predicate_mode=job.predicate_mode,
        campaign=campaign,
        test_set=job.test_set,
        tau=job.tau,
        timers=job.timers,
    )
    for term, value in (job.reproduction_overrides or {}).items():
        name = switches_mod.REGISTRY[term].driver_name
        if name is not None:
            env[name] = value
    for name, value in (job.override_env or {}).items():
        if value is None:
            env.pop(name, None)
        else:
            env[name] = str(value)
    return env, terms


def _assert_audit_position_declared(job: Job) -> None:
    """Refuse an audit position off the declared one unless a declared caller asks.

    The second way a run may differ from the campaign, beside
    ``reproduction_overrides``: **where its exit audit is taken**.  The
    plan declares one position for every arm; the other, ``after_run``, reads
    the state PROCESS wrote out rather than the state the solve handed over,
    and a residual table that mixed the two without saying so is the thing the
    per-run ``audit_position`` field exists to prevent.  So the position is
    governed the way the overrides are: a campaign run never leaves the
    declared position, and a gate run leaves it only if the stage asking is
    named in :data:`harness.core.records.AUDIT_POSITION_AFTER_RUN_CALLERS` —
    a table with a reason per row, enforced here on every path a run takes.
    The refusal is :class:`records.RecordError`, re-raised as a
    :class:`PoolError` so the pool's callers see one kind of refusal.
    """
    try:
        records_mod.assert_audit_position_allowed(
            job.audit_position,
            phase=job.phase,
            run_kind=job.run_kind,
            caller=job.audit_position_caller,
            where=job.key,
        )
    except records_mod.RecordError as exc:
        raise PoolError(str(exc)) from exc


def _apply_reproduction_overrides(
    job: Job, terms: dict[str, str]
) -> dict[str, str]:
    """Fold the reproduction gate's overrides into *terms*, or refuse.

    The gate that reproduces the previous revision has to run two arms the way
    that revision ran them, and one of them differs from the campaign in a
    switch that now exists: the output path.  That is a **deliberate departure
    from the matrix**, so it is not allowed to be quiet.  Four things are
    checked and each refuses rather than degrades:

    * **a campaign run may not carry one at all.**  The campaign composes from
      the matrix and nothing else;
    * every term must be one the registry knows and the tree implements —
      overriding a switch that does not exist would silently do nothing;
    * every value must be one the switch declares, so a typo is refused rather
      than resolved by the driver's own guard three layers down;
    * the value must actually **differ** from what the arm composes.  An
      override that changes nothing is an override nobody checked, and it would
      let the declared set drift out of step with the matrix unnoticed.

    The overrides ride into the run record as ``reproduction_overrides``, so a
    record made under one says so on its face.
    """
    overrides = dict(job.reproduction_overrides or {})
    if not overrides:
        return terms
    if job.run_kind == "campaign":
        raise PoolError(
            f"{job.key}: a campaign run may not carry a reproduction override "
            f"({sorted(overrides)}).  The campaign composes each arm from the "
            f"experiment's matrix and nothing else; the override exists so "
            f"that the reproduction gate can run an arm the way the previous "
            f"revision ran it, and it is that gate's alone."
        )
    unknown = sorted(t for t in overrides if t not in switches_mod.REGISTRY)
    if unknown:
        raise PoolError(
            f"{job.key}: reproduction override names {unknown}, which the "
            f"switch registry does not know.  An override on a switch that "
            f"does not exist changes nothing and says it changed something."
        )
    absent = sorted(t for t in overrides if not switches_mod.REGISTRY[t].implemented)
    if absent:
        raise PoolError(
            f"{job.key}: reproduction override names {absent}, which no tree "
            f"implements yet; it would be composed into the environment and "
            f"ignored by the driver."
        )
    for term, value in sorted(overrides.items()):
        legal = switches_mod.REGISTRY[term].values
        if legal and value not in legal:
            raise PoolError(
                f"{job.key}: reproduction override {term}={value!r} is not one "
                f"of {legal}"
            )
        if terms.get(term) == value:
            raise PoolError(
                f"{job.key}: reproduction override {term}={value!r} is what "
                f"the arm composes anyway.  An override that changes nothing "
                f"is an override nobody checked."
            )
    merged = dict(terms)
    merged.update(overrides)
    return merged


def assert_input_file_for(job: Job, campaign: Campaign) -> tuple[Path, str]:
    """The input file this job reads, asserted, and whether it is committed or lifted.

    *Which* file is :func:`harness.experiment.arms.input_file_for`'s one answer;
    this adds the refusal a run needs before it starts: a lifted file must be
    present and carry the recorded digest, or the run is not made.
    """
    path = arms_mod.input_file_for(job.arm, job.config, campaign=campaign)
    if path != job.config.input_path:
        input_files_mod.assert_lifted(job.config, campaign)
        return path, "lifted"
    return path, "committed"


# --------------------------------------------------------------------------
# running one job
# --------------------------------------------------------------------------


def _command(job: Job, campaign: Campaign, terms: Mapping[str, str]) -> list[str]:
    entry = CHILD_DIR / ENTRY_POINT[job.phase]
    input_path, input_kind = assert_input_file_for(job, campaign)
    if job.phase == "census":
        command = [
            sys.executable,
            str(entry),
            "--child",
            "--tree", str(campaign.tree),
            "--configuration", job.config.name,
            "--arm", job.arm,
            "--input", str(input_path),
            "--outdir", str(job.outdir),
            "--entry", job.census_entry,
            "--run-kind", job.run_kind,
        ]
        if job.census_read:
            command.append("--read-census")
        return command
    command = [
        sys.executable,
        str(entry),
        "--tree", str(campaign.tree),
        "--configuration", job.config.name,
        "--arm", job.arm,
        "--outdir", str(job.outdir),
        "--input", str(input_path),
        "--input-kind", input_kind,
        "--coupling-state", str(job.config.coupling_state_path),
        "--seed", str(job.seed),
        "--tau", repr(float(job.tau if job.tau is not None else campaign.tau_for(job.config))),
        "--test-set", str(job.test_set or campaign.test_set),
        "--timers", ("on" if job.timers else "off"),
        "--run-kind", job.run_kind,
        "--regime", job.regime,
        "--predicate-mode", job.predicate_mode,
        "--switches-asked", json.dumps(dict(terms)),
        "--reproduction-overrides", json.dumps(dict(job.reproduction_overrides or {})),
    ]
    if job.tau_rule is not None:
        command += ["--tau-rule", job.tau_rule]
    if job.delta is not None:
        command += ["--delta", repr(job.delta)]
    if job.pin_hex is not None:
        command += ["--pin-hex", job.pin_hex]
    if job.node_census:
        command.append("--node-census")
    if job.phase == "A":
        command += [
            "--per-run-artifact",
            str(job.config.per_run_artifact(lifted_input_file=False)),
            "--node-write-sets",
            str(campaign.data_dir / "node_writesets.json"),
        ]
        if job.entry_state is not None:
            command += ["--entry-state", str(job.entry_state)]
        if job.stencil_column is not None:
            command += [
                "--stencil-column", str(job.stencil_column),
                "--stencil-sign", str(job.stencil_sign),
            ]
    else:
        # The restricted exit-audit statistic needs the same two artifacts in
        # both phases.  The per-run deferral set is the one stamped for the
        # input file this job actually reads -- the lifted one where the
        # optimiser owns the burn time -- so that the excluded set is derived
        # from the run that was made and not from the other one.
        command += [
            "--audit-position", job.audit_position,
            "--per-run-artifact",
            str(job.config.per_run_artifact(lifted_input_file=input_kind == "lifted")),
            "--node-write-sets",
            str(campaign.data_dir / "node_writesets.json"),
        ]
        if job.force_maxcal is not None:
            command += ["--force-maxcal", str(job.force_maxcal)]
    return command


#: Digests of the jobs this process has already made or kept, with where.  A
#: later gate of the same press composing the same job reads that record
#: rather than making it again — which is the shared pool's saving, and what
#: ``gates._ENTRY_REFERENCES_MADE`` did for one job set before A72.  It never
#: decides on its own: :func:`run` still puts the record through
#: :func:`records.is_complete_for`, so a directory this process wrote and then
#: lost would be re-made, not trusted (rule (vii), trap T13).
_MADE_THIS_INVOCATION: dict[str, str] = {}
_LOCKS: dict[str, threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()


def _lock_for(directory: Path) -> threading.Lock:
    with _LOCKS_GUARD:
        return _LOCKS.setdefault(str(directory), threading.Lock())


def why_not_composed_as_today(
    record: Mapping[str, Any], terms: Mapping[str, str]
) -> str | None:
    """Why *record* was not composed from the switch **terms** the arm sets today, or None.

    The job identity names the arm, never the switches the arm composes, so a
    driver change that makes an arm compose one more switch (V5 list item 5:
    the partitioned evaluation arm's once-after-convergence execution of the
    per-run deferred set) leaves every earlier record of that arm with the
    same digest — and ``--resume`` would keep a record of a run the arm no
    longer makes.  The child stamps what it was asked for (``switches_asked``,
    the composed terms), so the comparison is by **term name**: a record
    composed with a term the arm no longer sets, or without one it now sets,
    is not a record of this job.  Values are not compared here — a path term
    differs between two trees by construction (trap T20) and the identity's
    own fields cover the values that matter — and a record made before the
    stamp existed is left to the completeness contract.
    """
    asked = record.get("switches_asked")
    if not isinstance(asked, Mapping):
        return None
    now = set(terms)
    then = set(asked)
    if now == then:
        return None
    gained = sorted(now - then)
    lost = sorted(then - now)
    return (
        "the arm composes "
        + (f"term(s) {gained} the record was made without" if gained else "")
        + (" and " if gained and lost else "")
        + (f"no term {lost}, which the record was made with" if lost else "")
        + ": a driver change made the arm compose differently, so the record is "
        "of a run the arm no longer makes"
    )


def _loadavg() -> tuple[float, float, float] | None:
    try:
        return os.getloadavg()
    except OSError:
        return None


#: What :func:`why_not_kept` says when the directory holds no record at all.
NO_RECORD_ON_DISK = "no record on disk"


def why_not_kept(
    job: Job,
    campaign: Campaign,
    *,
    identity: Mapping[str, Any],
    digest: str,
    directory: Path,
) -> str | None:
    """Why ``--resume`` would re-make this job's record in *directory*, or None.

    The one resume decision, in one place: :func:`run` keeps a record exactly
    when this returns None, and :func:`job_listing` prints this sentence, so
    a listing can never promise a keep the press would not make (task A105
    (v5-resume-fixes-and-tau-rule): the listing consulted the completeness
    contract alone and left the composition check to the press).  Two
    comparisons, both over the record and the job only (rule (vii), trap
    T13): :func:`records.why_not_complete_for` — the identity, the stamps
    and the completeness contract — and :func:`why_not_composed_as_today` —
    the switch terms the arm composes now against those the record was made
    with.
    """
    if not (Path(directory) / "metrics.json").exists():
        return NO_RECORD_ON_DISK
    previous = records_mod.read(directory)
    why = records_mod.why_not_complete_for(previous, identity=identity, digest=digest)
    if why is not None:
        return why
    _env, terms = environment_for(job, campaign)
    return why_not_composed_as_today(previous, terms)


def _kept(
    job: Job,
    identity: Mapping[str, Any],
    digest: str,
    outdir: Path,
    *,
    campaign: Campaign,
) -> dict[str, Any] | None:
    """The outcome of a kept run, or None where the record is not this job's."""
    why = why_not_kept(job, campaign, identity=identity, digest=digest, directory=outdir)
    if why is not None:
        if why != NO_RECORD_ON_DISK:
            print(
                f"  {job.config.name:24s} {job.arm:4s} seed={job.seed:<3d} "
                f"re-made: {why}",
                flush=True,
            )
        return None
    previous = records_mod.read(outdir)
    print(
        f"  {job.config.name:24s} {job.arm:4s} seed={job.seed:<3d} "
        f"resumed (complete record of this job kept; digest {digest[:12]})",
        flush=True,
    )
    return {
        "key": job.key,
        "arm": job.arm,
        "configuration": job.config.name,
        "seed": job.seed,
        "rc": 0,
        "outdir": str(outdir),
        "resumed": True,
        "job_digest": digest,
        "status": previous.get("status"),
        "failure_class": previous.get("failure_class"),
    }


def assert_not_another_jobs_record(
    job: Job, identity: Mapping[str, Any], outdir: Path
) -> None:
    """Refuse to re-make *job* on top of a record of a **different** job.

    Re-making a run removes its directory first.  Before the renaming of
    2026-09-15 a directory could hold only its own job's record, because the
    layout named every directory after the job; since then a canonical
    directory can be occupied by another arm's record — ``…/A1/seed001`` holds
    the arm now called ``A2`` (``records.RECORDED_ARM_NAMES``) — and removing it would destroy a campaign
    record to make room for a gate run.  :func:`directory_for` resolves the
    job's own record by digest wherever one exists, so this is reached only
    when the job has no record anywhere and its canonical directory is taken.
    The readable half of the identity — arm, configuration, seed, phase,
    regime, run kind — decides: a record of the same readable job (a stale or
    incomplete one) is re-made as before; one of another job is refused.
    """
    if not (outdir / "metrics.json").exists():
        return
    existing = records_mod.read(outdir)
    if existing.get("status") == "no_record" and "campaign_arm" not in existing:
        return
    for name in records_mod.READABLE_IDENTITY_FIELDS:
        child_name = records_mod.IDENTITY_FIELDS_STAMPED_BY_THE_CHILD[name]
        if existing.get(child_name) != identity.get(name):
            raise PoolError(
                f"{job.key}: {outdir} holds a record of another job "
                f"({child_name}={existing.get(child_name)!r}, this job's {name} "
                f"is {identity.get(name)!r}; its digest "
                f"{str(existing.get('job_digest'))[:16]}, stamped at "
                f"{str(existing.get('tree_git_head'))[:8]}).  Refusing to remove "
                f"it to make room: the record is the truth and the path is where "
                f"the pool found it — see records.RECORDED_ARM_NAMES and "
                f"pool.directory_for."
            )


def stamp_identity(
    outdir: Path,
    identity: Mapping[str, Any],
    digest: str,
    *,
    launcher: Mapping[str, Any] | None = None,
    tau_rule_derivation: Mapping[str, Any] | None = None,
) -> None:
    """Write ``job_identity`` and ``job_digest`` into the record on disk.

    Stamped by the pool after the child returns, not by the child: the child
    knows what it was asked for, the pool knows what it composed, and the
    identity is the pool's construction.  The child's own ``completeness``
    block was computed before these two fields existed, so it is re-evaluated
    here over the record as it now stands.
    """
    path = Path(outdir) / "metrics.json"
    try:
        record = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return
    record["job_identity"] = dict(identity)
    record["job_digest"] = digest
    if launcher is not None:
        # DR12: the launcher's independent wall of the subprocess and the
        # load average at its spawn and return; context, never evidence.
        record["launcher"] = dict(launcher)
    if tau_rule_derivation is not None:
        # The named tolerance rule's derivation of this job's τ from the
        # configuration's committed input file (config.TauRule): what the
        # rule read, where, and the τ it gave.  Stamped by the pool, which
        # composed it; the child stamps the rule's name it was handed.
        record["tau_rule_derivation"] = dict(tau_rule_derivation)
    # The naming scheme the arm fields are written in.  A record made after
    # the arm renaming of 2026-09-15 says so here, and ``records.read`` then
    # leaves its names alone; one without the stamp is read through
    # ``records.RECORDED_ARM_NAMES``.
    record[records_mod.ARM_NAMING_FIELD] = records_mod.ARM_NAMING
    if isinstance(record.get("completeness"), Mapping):
        try:
            records_mod.assert_usable(record, where="the pool's stamp")
            record["completeness"] = {"complete": True, "missing": []}
        except records_mod.RecordError as exc:
            record["completeness"] = {
                "complete": False,
                "missing": records_mod.missing_fields(record)
                if record.get("campaign_phase") in ("A", "B")
                else [],
                "refusal": str(exc),
            }
    path.write_text(json.dumps(record, indent=2))


def run(
    job: Job, campaign: Campaign, *, resume: bool = False, fresh: bool = False
) -> dict[str, Any]:
    """One isolated run.  Counts are exact; wall clock is progress information.

    Returns the job's outcome, not its record: the record is on disk, and the
    summary reads it from there so that a summary can be recomputed without
    re-running anything.  Resolves ``job.outdir`` where the job named none.

    Without ``resume`` a run is re-made — unless **this process** already made
    or kept this job (:data:`_MADE_THIS_INVOCATION`), in which case the record
    is checked and kept: one press makes each job once, whichever gates share
    it.  ``fresh`` overrides that for a caller that wants the same job made
    again in the same process — gate G7's tooth, which stales a record and
    asks for the run again without resume to show it is re-made.
    """
    if not campaign.is_experiment_copy:
        raise PoolError(
            f"refusing to run against {campaign.tree}: records are only ever "
            f"made against the experiment's own copy of PROCESS.  Pointing the "
            f"campaign at another tree is for the preflight and the "
            f"self-check, and a measurement of a tree nobody asked for is "
            f"exactly what that separation prevents."
        )
    outdir = directory_for(job, campaign)
    job.outdir = outdir
    identity = job.identity(Path(campaign.runs_dir))
    digest = records_mod.job_digest(identity)
    with _lock_for(outdir):
        if resume or (digest in _MADE_THIS_INVOCATION and not fresh):
            kept = _kept(job, identity, digest, outdir, campaign=campaign)
            if kept is not None:
                _MADE_THIS_INVOCATION[digest] = str(outdir)
                return kept
        if outdir.exists():
            assert_not_another_jobs_record(job, identity, outdir)
            shutil.rmtree(outdir)
        outdir.mkdir(parents=True, exist_ok=True)

        env, terms = environment_for(job, campaign)
        command = _command(job, campaign, terms)
        (outdir / "command.json").write_text(
            json.dumps(
                {
                    "command": command,
                    "architecture_environment": {
                        name: env[name]
                        for name in switches_mod.all_names()
                        if name in env
                    },
                    "pythonpath": env.get("PYTHONPATH"),
                    "cwd": str(outdir),
                    "override_env": dict(job.override_env or {}),
                    # Where the exit audit was asked to be taken and, when that is
                    # not the declared position, which declared stage asked.  The
                    # record carries the position itself (``audit_position``); the
                    # caller is stamped here, beside it, and in the caller's own
                    # record.
                    "audit_position": job.audit_position,
                    "audit_position_caller": job.audit_position_caller,
                    "job_identity": identity,
                    "job_digest": digest,
                },
                indent=2,
            )
        )

        started = time.perf_counter()
        launcher: dict[str, Any] = {
            "spawned_at": time.time(),
            "loadavg_at_spawn": _loadavg(),
            "workers": workers(campaign),
        }
        try:
            completed = subprocess.run(
                command,
                env=env,
                capture_output=True,
                text=True,
                cwd=str(outdir),
                timeout=job.timeout,
            )
            rc = completed.returncode
            (outdir / "stdout.log").write_text(completed.stdout)
            (outdir / "stderr.log").write_text(completed.stderr)
        except subprocess.TimeoutExpired as exc:
            rc = 124
            (outdir / "stdout.log").write_text(exc.stdout or "")
            (outdir / "stderr.log").write_text((exc.stderr or "") + "\nTIMEOUT")

        path = outdir / "metrics.json"
        if not path.exists():
            # A run that wrote no record is a machinery failure, not a physics
            # result.  Saying so here is the difference between "the reference arm
            # did not converge" and "the subprocess never started".
            path.write_text(
                json.dumps(
                    {
                        "record_format": records_mod.FORMAT,
                        "campaign_phase": job.phase,
                        "campaign_arm": job.arm,
                        "campaign_configuration": job.config.name,
                        "campaign_seed": job.seed,
                        "campaign_run_kind": job.run_kind,
                        "regime": job.regime,
                        "status": "timeout" if rc == 124 else "no_record",
                        "failure_class": "timeout" if rc == 124 else "machinery",
                        "returncode": rc,
                        "why": (
                            "the subprocess wrote no record; this is a machinery "
                            "failure, not a result about the models"
                        ),
                        "command": command,
                    },
                    indent=2,
                )
            )
        launcher["returned_at"] = time.time()
        launcher["wall_s"] = time.perf_counter() - started
        launcher["loadavg_at_return"] = _loadavg()
        launcher["what"] = (
            "the pool's own wall of the child process, spawn to return, and "
            "the load average at both ends; the fixed per-run term and the "
            "unattributed residual are derived from it (DR12); context, never evidence"
        )
        stamp_identity(
            outdir,
            identity,
            digest,
            launcher=launcher,
            tau_rule_derivation=(
                tau_rule_named(job.tau_rule).derivation(job.config)
                if job.tau_rule is not None
                else None
            ),
        )
        record = records_mod.read(outdir)
        # The close-out: PROCESS wrote its log twice (``process_log``'s
        # docstring says where each comes from); the run folder keeps one,
        # gzip-compressed, once the pair is verified identical and the round
        # trip verified.  After the record is assembled; no record field read
        # or written.
        log = process_log_mod.close_out(outdir)
        if log["action"] not in ("compacted", "no log"):
            print(f"  {job.config.name:24s} {job.arm:4s} seed={job.seed:<3d} process log {log['action']}", flush=True)
        _MADE_THIS_INVOCATION[digest] = str(outdir)
        _index_record(campaign, digest, outdir)
    wall = time.perf_counter() - started
    print(
        f"  {job.config.name:24s} {job.arm:4s} seed={job.seed:<3d} rc={rc} "
        f"status={record.get('status')} {wall:6.1f}s "
        f"(wall clock is progress information, not a measurement)",
        flush=True,
    )
    return {
        "key": job.key,
        "arm": job.arm,
        "configuration": job.config.name,
        "seed": job.seed,
        "rc": rc,
        "outdir": str(outdir),
        "resumed": False,
        "job_digest": digest,
        "status": record.get("status"),
        "failure_class": record.get("failure_class"),
        "wall_s": wall,
    }


def run_all(
    jobs: Sequence[Job], campaign: Campaign, *, resume: bool = False, fresh: bool = False
) -> list[dict[str, Any]]:
    """Every job, W at a time.  Deterministic order; nothing is ever retried."""
    width = workers(campaign)
    (campaign.cache_dir / "_mplconfig").mkdir(parents=True, exist_ok=True)
    # Two jobs of one identity in one list would race on one directory; the
    # second is served the first's outcome (the per-directory lock in ``run``
    # makes even that ordering safe, but there is no reason to start it).
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=width) as pool:
        futures: list = []
        first_by_dir: dict[str, int] = {}
        for index, job in enumerate(jobs):
            directory = str(directory_for(job, campaign))
            if directory in first_by_dir:
                futures.append(first_by_dir[directory])
                continue
            first_by_dir[directory] = index
            futures.append(pool.submit(run, job, campaign, resume=resume, fresh=fresh))
        for index, future in enumerate(futures):
            if isinstance(future, int):
                outcome = dict(futures[future].result())
                jobs[index].outdir = Path(outcome["outdir"])
                results.append(outcome)
            else:
                results.append(future.result())
    return results


def run_serially(
    jobs: Sequence[Job], campaign: Campaign, *, resume: bool = False
) -> list[dict[str, Any]]:
    """Every job, one at a time, in order.

    For a chain whose later members are entered from an earlier member's exit —
    the backward stencil points, and anything anchored on a reference run.
    """
    (campaign.cache_dir / "_mplconfig").mkdir(parents=True, exist_ok=True)
    return [run(job, campaign, resume=resume) for job in jobs]
