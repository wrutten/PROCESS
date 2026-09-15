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
from . import records as records_mod
from ..experiment import switches as switches_mod
from .config import Campaign, Config

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

    def identity(self, runs_dir: Path | None = None) -> dict[str, Any]:
        """Every identity field, rendered as JSON-safe values, in declared order.

        The one construction of "the same job": :attr:`key`, the digest and the
        shared pool's directory are all derived from this dictionary.  Paths
        are rendered relative to *runs_dir* where they lie under it — a seeded
        or relocated worktree carries its records under another absolute path
        and is still the same job — and as given otherwise.  Mappings are
        rendered with sorted keys and string values, ``None`` kept as null.
        """
        rendered: dict[str, Any] = {}
        for name in JOB_IDENTITY_FIELDS:
            if name == "configuration":
                rendered[name] = self.config.name
                continue
            value = getattr(self, name)
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
                    str(k): (None if v is None else str(v))
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
        """
        return readable_key(self.identity())


def _render_path(path: Path, runs_dir: Path | None) -> str:
    path = Path(path)
    if runs_dir is not None:
        try:
            return path.resolve().relative_to(Path(runs_dir).resolve()).as_posix()
        except ValueError:
            pass
    return path.as_posix()


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


def digest_for(job: Job, campaign: Campaign) -> str:
    """The job digest: sha256 over the canonical JSON of :meth:`Job.identity`."""
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
       ``runs/`` — then that directory, whatever it is called, is the job's;
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
    """
    canonical = canonical_directory_for(job, campaign)
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
    hits = _record_index(campaign).get(digest, [])
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
    return hits[0]


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
    ``experiment_runner.py --jobs <gate>`` prints.  ``why_not_complete`` is
    :func:`records.why_not_complete_for`'s sentence, or None where ``--resume``
    would keep the record; it is computed from the record alone (rule (vii)).
    """
    runs_dir = Path(campaign.runs_dir)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for job in jobs:
        identity = job.identity(runs_dir)
        digest = records_mod.job_digest(identity)
        if digest in seen:
            continue
        seen.add(digest)
        directory = directory_for(job, campaign)
        if (directory / "metrics.json").exists():
            why = records_mod.why_not_complete_for(
                records_mod.read(directory), identity=identity, digest=digest
            )
        else:
            why = "no record on disk"
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
    arm = arms_mod.ARMS[job.arm]
    terms = arm.terms(
        job.config,
        pin_hex=job.pin_hex,
        predicate_mode=job.predicate_mode,
        campaign=campaign,
        seed=job.seed,
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
        "--tau", repr(campaign.tau),
        "--run-kind", job.run_kind,
        "--regime", job.regime,
        "--predicate-mode", job.predicate_mode,
        "--switches-asked", json.dumps(dict(terms)),
        "--reproduction-overrides", json.dumps(dict(job.reproduction_overrides or {})),
    ]
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


def _kept(job: Job, identity: Mapping[str, Any], digest: str, outdir: Path) -> dict[str, Any] | None:
    """The outcome of a kept run, or None where the record is not this job's."""
    if not (outdir / "metrics.json").exists():
        return None
    previous = records_mod.read(outdir)
    if not records_mod.is_complete_for(previous, identity=identity, digest=digest):
        return None
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


def stamp_identity(outdir: Path, identity: Mapping[str, Any], digest: str) -> None:
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
            kept = _kept(job, identity, digest, outdir)
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
        stamp_identity(outdir, identity, digest)
        record = records_mod.read(outdir)
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
    (Path(campaign.runs_dir) / "_mplconfig").mkdir(parents=True, exist_ok=True)
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
    (Path(campaign.runs_dir) / "_mplconfig").mkdir(parents=True, exist_ok=True)
    return [run(job, campaign, resume=resume) for job in jobs]
