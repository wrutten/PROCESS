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
behind.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from . import arms as arms_mod
from . import input_files as input_files_mod
from . import records as records_mod
from . import switches as switches_mod
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
    outdir: Path
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
    #: Switch terms this tree does not implement that this job is allowed to
    #: omit.  **Empty except in a gate that says why**; see
    #: :func:`environment_for`.
    allow_pending: tuple[str, ...] = ()
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
    #: position the plan declares for every arm; the reproduction gate is the
    #: only caller that may ask for the previous revision's.
    audit_position: str = "entry_to_write_output_files"

    @property
    def key(self) -> str:
        return f"{self.arm}/{self.config.name}/seed{self.seed:03d}"


def seed_directory(seed: int) -> str:
    """A run directory's name.  ``seed000`` is the undisplaced start."""
    return f"seed{seed:03d}"


# --------------------------------------------------------------------------
# composing one job's environment
# --------------------------------------------------------------------------


def environment_for(job: Job, campaign: Campaign) -> tuple[dict[str, str], dict]:
    """The environment this job runs under, and what it asked for.

    Two things may make a run differ from what the matrix says, and neither is
    silent.

    ``allow_pending`` is the only way a run happens **without** a switch its arm
    declares, and it is for a switch **no tree implements yet**:

    * the terms allowed must be exactly the terms this tree cannot implement —
      allowing a term the tree *does* implement, or failing to allow one it
      does not, is a refusal either way;
    * the allowed terms are written into the record, so a run made under the
      allowance says so;
    * campaign runs never pass it.  No arm of the matrix currently needs it;
      the switch still waiting on its driver change is the convergence
      predicate's mode, which only the trial composes.

    ``reproduction_overrides`` is the only way a run happens with a switch set
    to something **other** than what its arm composes, and it is for a switch
    the tree *does* implement.  The reproduction gate reproduces the previous
    revision, and that revision wrote two arms' output files through upstream's
    output-time loop because the switch that turns it off did not exist yet.
    See :func:`_apply_reproduction_overrides` for the four things that refuse
    one; a campaign run carrying one is the first of them.
    """
    arm = arms_mod.ARMS[job.arm]
    terms = arm.terms(
        job.config,
        pin_hex=job.pin_hex,
        predicate_mode=job.predicate_mode,
        campaign=campaign,
        seed=job.seed,
    )
    pending = set(switches_mod.unimplemented(terms))
    allowed = set(job.allow_pending)
    if allowed != pending:
        unexpected = sorted(allowed - pending)
        unallowed = sorted(pending - allowed)
        if unexpected:
            raise PoolError(
                f"{job.key}: this run allows switch term(s) {unexpected} to be "
                f"omitted, but the tree implements them.  An allowance that "
                f"covers a switch the tree has is an allowance nobody checked."
            )
        raise PoolError(
            f"{job.key}: the tree implements no switch for {unallowed} "
            + "; ".join(
                f"{t} (needs "
                f"{switches_mod.REGISTRY[t].pending_change or 'a driver change'})"
                for t in unallowed
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
        pending_ok=bool(allowed),
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


def input_file_for(job: Job, campaign: Campaign) -> tuple[Path, str]:
    """The input file this job reads, and whether it is committed or lifted."""
    arm = arms_mod.ARMS[job.arm]
    if arm.input_file == "lifted" and job.config.pulsed:
        input_files_mod.assert_lifted(job.config, campaign)
        return input_files_mod.lifted_path(job.config, campaign), "lifted"
    return job.config.input_path, "committed"


# --------------------------------------------------------------------------
# running one job
# --------------------------------------------------------------------------


def _command(job: Job, campaign: Campaign, terms: Mapping[str, str]) -> list[str]:
    here = Path(__file__).resolve().parent
    entry = here / ENTRY_POINT[job.phase]
    input_path, input_kind = input_file_for(job, campaign)
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
    if job.allow_pending:
        command += ["--pending-allowed", ",".join(sorted(job.allow_pending))]
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


def run(job: Job, campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    """One isolated run.  Counts are exact; wall clock is progress information.

    Returns the job's outcome, not its record: the record is on disk, and the
    summary reads it from there so that a summary can be recomputed without
    re-running anything.
    """
    if not campaign.is_experiment_copy:
        raise PoolError(
            f"refusing to run against {campaign.tree}: records are only ever "
            f"made against the experiment's own copy of PROCESS.  Pointing the "
            f"campaign at another tree is for the preflight and the "
            f"self-check, and a measurement of a tree nobody asked for is "
            f"exactly what that separation prevents."
        )
    outdir = Path(job.outdir)
    if resume and (outdir / "metrics.json").exists():
        previous = records_mod.read(outdir)
        if records_mod.is_complete_for(
            previous,
            arm=job.arm,
            configuration=job.config.name,
            seed=job.seed,
            phase=job.phase,
            regime=job.regime,
        ):
            print(
                f"  {job.config.name:24s} {job.arm:4s} seed={job.seed:<3d} "
                f"resumed (complete record kept)",
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
                "status": previous.get("status"),
                "failure_class": previous.get("failure_class"),
            }
    if outdir.exists():
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
                "allow_pending": list(job.allow_pending),
                "override_env": dict(job.override_env or {}),
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
    record = records_mod.read(outdir)
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
        "status": record.get("status"),
        "failure_class": record.get("failure_class"),
        "wall_s": wall,
    }


def run_all(
    jobs: Sequence[Job], campaign: Campaign, *, resume: bool = False
) -> list[dict[str, Any]]:
    """Every job, W at a time.  Deterministic order; nothing is ever retried."""
    width = workers(campaign)
    (Path(campaign.runs_dir) / "_mplconfig").mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=width) as pool:
        futures = [pool.submit(run, job, campaign, resume=resume) for job in jobs]
        for future in futures:
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
