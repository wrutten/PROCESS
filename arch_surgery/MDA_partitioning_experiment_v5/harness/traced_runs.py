"""The traced-run stage: campaign jobs re-made with the block trace on.

Task **A115 (v5-sweep-residual-trace)**.  The driver copy's block trace
(``PROCESS_ARCH_BLOCK_TRACE``; A90, extended by driver change DR13) writes one
JSON line per evaluation: the design point, the evaluation kind, each block's
sweeps and, per sweep, the test's score and the score of the block's census
and non-census components, each with its worst component named.  The switch
was registered and never composed; this stage is the one entry point that sets
it (``experiment_runner.py --traced-runs list | press | check``).

What a traced job is
--------------------
The campaign's own job -- the same phase, arm, configuration, seed, regime,
δ, entry state and burn-time pin, under the run ID's test set and tolerance,
composed as the campaign press composes it (the timers on) -- with three
fields changed:

* ``run_kind = "trace"`` (``records.RUN_KINDS``): never a campaign record,
  never in a published population (``stats.measurable_run_kinds``);
* ``outdir`` under this run ID's ``traced_runs/<job set>/``, one directory per
  job, named;
* ``override_env`` carrying ``PROCESS_ARCH_BLOCK_TRACE`` (a file name,
  relative: the child's working directory is its own run folder) and, under the
  whole-write-set test only, ``PROCESS_ARCH_BLOCK_TRACE_CENSUS_SETS`` (the
  configuration's committed census artifact, which the trace splits the score
  by).  Both are identity fields, so a traced job's digest is one no campaign
  record has and it can never resolve into one (checked before any run:
  :func:`assert_apart`).

The reference arms (``AR``, ``BR``) are not traced: they run upstream's loop,
and the driver refuses the trace without a block loop.

The declared job set (:data:`JOB_SETS`)
---------------------------------------
``sweep_residual``: every loop arm of both phases on every configuration
(phase A ``A0``, ``A1`` where it exists, ``A2``; phase B ``B0``, ``B1`` where it
exists, ``B2``), under whichever run ID the button is pressed with.

* **Phase A**: the displaced seeds 1, 2, 3 -- the first three of the
  campaign's 25, every phase A run having finished in every campaign.
* **Phase B**: per configuration, the three lowest-numbered starts at which
  **every** phase B arm (the reference included) was accepted (``ok``,
  ``ifail = 1``) in **all four** campaigns (census and whole write set, at
  1e-6 and 1e-8).  The rule was written before any trace was read; the four
  campaigns' outcome tables (``campaign_comparison.md``) list the starts it
  excludes.  It gives tok 0, 1, 2 (5, 20, 21 crash in every arm); lad 0, 1, 5
  (2, 3, 4 excluded); st 0, 2, 4 (1 and 3 excluded).  The brief's condition on
  st -- at least one start where the partitioned arm at census 1e-8 ends more
  than 10 % from the flat arm's design and one where it does not -- is checked
  by the reading script against the census 1e-8 records; **declared
  fallback**: if the three starts fall in one class, the lowest-numbered
  qualifying start of the missing class is added.  The reading script
  re-derives these seeds from the four campaigns' records and refuses if they
  differ from the table below.
* ``sweep_residual_st_more``: further st starts, 6, 7, 8 (the next three by
  the same rule), phase B only, pressed if run time allows; reported apart.

The neutrality check (:func:`check`)
------------------------------------
Every traced run against the campaign record of the same job: the declared
count leaves (:data:`COMPARED_B`, :data:`COMPARED_A`) to the digit, the
objective and design as hex floats, and the coupling-state files
(:data:`STATE_FILES`) component by component.  A difference is a result,
printed and recorded, never tuned away.  The trace's own consistency is
recorded beside: lines per evaluation and per-block sweeps summed against the
record's own totals.

Compression
-----------
One compressed trace per run, ``block_trace.jsonl.gz``, written as the pool's
close-out writes ``process.log.gz`` (``process_log``: gzip level 6, no name or
time in the header), verified to decompress to the plain file's SHA-256, and
only then the plain file removed.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping

from . import chain as chain_mod
from .core import framework
from .core import pool as pool_mod
from .core import process_log as process_log_mod
from .core import records as records_mod
from .core.config import Campaign
from .experiment import arms as arms_mod

#: The run kind every traced record is stamped with.
RUN_KIND = "trace"

#: Where the stage's records go, under the run ID's folder.
ROOT_NAME = "traced_runs"

#: The trace file, relative to the run's own working directory.
TRACE_FILE = "block_trace.jsonl"
TRACE_COMPRESSED = TRACE_FILE + ".gz"
TRACE_PARTIAL = TRACE_COMPRESSED + ".partial"

TRACE_VARIABLE = "PROCESS_ARCH_BLOCK_TRACE"
CENSUS_VARIABLE = "PROCESS_ARCH_BLOCK_TRACE_CENSUS_SETS"

#: The reference arms run upstream's loop and are never traced.
REFERENCE_ARMS = ("AR", "BR")

#: The identity fields a traced job changes from its campaign job (the
#: directory is not an identity field).
IDENTITY_FIELDS_CHANGED = ("run_kind", "override_env")


@dataclasses.dataclass(frozen=True)
class JobSet:
    name: str
    what: str
    evaluation_seeds: tuple[int, ...]
    optimisation_seeds: Mapping[str, tuple[int, ...]]


#: The declared job sets.  See the module docstring for the rule.
JOB_SETS: dict[str, JobSet] = {
    "sweep_residual": JobSet(
        name="sweep_residual",
        what=(
            "every loop arm of both phases on every configuration: phase A "
            "seeds 1-3; phase B the three lowest starts accepted by every arm "
            "in all four campaigns"
        ),
        evaluation_seeds=(1, 2, 3),
        optimisation_seeds={
            "large_tokamak_nof": (0, 1, 2),
            "low_aspect_ratio_DEMO": (0, 1, 5),
            "st_regression": (0, 2, 4),
        },
    ),
    "sweep_residual_st_more": JobSet(
        name="sweep_residual_st_more",
        what="st only, phase B only: the next three starts by the same rule",
        evaluation_seeds=(),
        optimisation_seeds={"st_regression": (6, 7, 8)},
    ),
}


def root(campaign: Campaign, job_set: JobSet) -> Path:
    return Path(campaign.runs_dir) / ROOT_NAME / job_set.name


def _override_env(campaign: Campaign, config) -> dict[str, str]:
    env = {TRACE_VARIABLE: TRACE_FILE}
    if campaign.test_set == "write_set":
        env[CENSUS_VARIABLE] = str(config.test_sets_path)
    return env


def pairs(
    campaign: Campaign,
    job_set: JobSet,
    *,
    configurations: Iterable[str] | None = None,
    arms: Iterable[str] | None = None,
) -> list[tuple[pool_mod.Job, pool_mod.Job]]:
    """``(campaign job, traced job)`` for every job of *job_set*.

    The campaign jobs are composed by the chain's own constructors
    (``chain.evaluation_displaced_jobs``, ``chain.optimisation_jobs``) under the
    campaign plan, so they name the campaign's records exactly as the press
    made them; the traced job is a copy with the three fields above changed.
    """
    plan = chain_mod.campaign_plan(campaign)
    wanted_configs = set(configurations) if configurations else None
    wanted_arms = set(arms) if arms else None
    base = root(campaign, job_set)
    out: list[tuple[pool_mod.Job, pool_mod.Job]] = []

    def keep(job: pool_mod.Job, seeds: Iterable[int]) -> bool:
        if job.arm in REFERENCE_ARMS:
            return False
        if wanted_configs is not None and job.config.name not in wanted_configs:
            return False
        if wanted_arms is not None and job.arm not in wanted_arms:
            return False
        return job.seed in tuple(seeds)

    if job_set.evaluation_seeds:
        references = chain_mod.references_from_records(campaign, plan)
        for job in chain_mod.evaluation_displaced_jobs(campaign, plan, references):
            if not keep(job, job_set.evaluation_seeds):
                continue
            traced = dataclasses.replace(
                job,
                run_kind=RUN_KIND,
                outdir=base / "evaluation" / job.config.name / job.arm / pool_mod.seed_directory(job.seed),
                override_env=_override_env(campaign, job.config),
            )
            out.append((job, traced))
    for job in chain_mod.optimisation_jobs(campaign, plan):
        seeds = job_set.optimisation_seeds.get(job.config.name, ())
        if not keep(job, seeds):
            continue
        traced = dataclasses.replace(
            job,
            run_kind=RUN_KIND,
            outdir=base / "optimisation" / job.config.name / job.arm / pool_mod.seed_directory(job.seed),
            override_env=_override_env(campaign, job.config),
        )
        out.append((job, traced))
    return out


def assert_apart(campaign: Campaign, job_pairs: list[tuple[pool_mod.Job, pool_mod.Job]]) -> dict[str, Any]:
    """Refuse unless every traced job is its own identity, in its own folder.

    For every pair: the traced job's digest differs from the campaign job's;
    the traced job resolves to the directory it names (under this stage's
    root, never into the campaign's records); and the campaign job resolves to
    a record on disk, the one compared with.  Nothing is run or written.
    """
    problems: list[str] = []
    stage_root = (Path(campaign.runs_dir) / ROOT_NAME).resolve()
    campaign_root = (Path(campaign.runs_dir) / "campaign").resolve()
    for campaign_job, traced in job_pairs:
        d_campaign = pool_mod.digest_for(campaign_job, campaign)
        d_traced = pool_mod.digest_for(traced, campaign)
        if d_campaign == d_traced:
            problems.append(f"{traced.key}: the traced job has the campaign job's digest")
        resolved = pool_mod.directory_for(traced, campaign).resolve()
        if resolved != Path(traced.outdir).resolve():
            problems.append(f"{traced.key}: resolves to {resolved}, not to its named directory")
        try:
            resolved.relative_to(stage_root)
        except ValueError:
            problems.append(f"{traced.key}: resolves outside {stage_root}")
        try:
            resolved.relative_to(campaign_root)
            problems.append(f"{traced.key}: resolves into the campaign's records")
        except ValueError:
            pass
        source = pool_mod.directory_for(campaign_job, campaign)
        if not (Path(source) / "metrics.json").exists():
            problems.append(f"{campaign_job.key}: no campaign record at {source}")
    if problems:
        raise framework.GateError(
            f"{len(problems)} traced job(s) are not apart from the campaign: {problems[:5]}"
        )
    return {"n_pairs": len(job_pairs), "apart": True}


# --------------------------------------------------------------------------
# compression
# --------------------------------------------------------------------------


def compress_trace(directory: Path) -> dict[str, Any]:
    """``block_trace.jsonl`` -> ``block_trace.jsonl.gz``, verified, plain removed."""
    directory = Path(directory)
    plain = directory / TRACE_FILE
    packed = directory / TRACE_COMPRESSED
    partial = directory / TRACE_PARTIAL
    if partial.exists():
        partial.unlink()
    if not plain.exists():
        return {"directory": str(directory), "outcome": "compressed" if packed.exists() else "no trace"}
    want, n_plain = process_log_mod.sha256_of(plain)
    process_log_mod._write_compressed(plain, partial)
    got, n_got = process_log_mod.sha256_decompressed(partial)
    if (got, n_got) != (want, n_plain):
        partial.unlink()
        return {"directory": str(directory), "outcome": "round trip FAILED; plain kept"}
    os.replace(partial, packed)
    plain.unlink()
    return {
        "directory": str(directory),
        "outcome": "compressed",
        "plain_bytes": n_plain,
        "compressed_bytes": packed.stat().st_size,
        "sha256_plain": want,
    }


def open_trace(directory: Path):
    """The trace's lines, from whichever form is on disk (plain or compressed)."""
    import gzip  # noqa: PLC0415

    directory = Path(directory)
    if (directory / TRACE_COMPRESSED).exists():
        return gzip.open(directory / TRACE_COMPRESSED, "rt")
    if (directory / TRACE_FILE).exists():
        return open(directory / TRACE_FILE)
    return None


# --------------------------------------------------------------------------
# the press
# --------------------------------------------------------------------------


def press(
    campaign: Campaign,
    job_set: JobSet,
    *,
    resume: bool,
    configurations: Iterable[str] | None = None,
    arms: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Run the traced jobs of *job_set* and compress every trace.

    *campaign* must be the campaign press's composition (the timers on): the
    traced job is the campaign job, and the campaign was pressed so.
    """
    job_pairs = pairs(campaign, job_set, configurations=configurations, arms=arms)
    apart = assert_apart(campaign, job_pairs)
    results = pool_mod.run_all([traced for _c, traced in job_pairs], campaign, resume=resume)
    compressed = [compress_trace(Path(traced.outdir)) for _c, traced in job_pairs]
    return {
        "stage": "traced_runs",
        "job_set": job_set.name,
        "run_id": campaign.run_id,
        "tree_git_head": framework.git_head(),
        "n_jobs": len(job_pairs),
        "apart": apart,
        "results": [
            {k: r.get(k) for k in ("key", "status", "outdir", "resumed", "job_digest")}
            for r in results
        ],
        "compression": compressed,
    }


# --------------------------------------------------------------------------
# the neutrality check
# --------------------------------------------------------------------------

#: Count and result leaves compared to the digit, phase B.
COMPARED_B: tuple[str, ...] = (
    "status",
    "failure_class",
    "n_solver_iterations",
    "sweeps_per_eval.n_evaluations",
    "sweeps_per_eval.n_sweeps",
    "sweeps_per_eval.hist",
    "node_calls_total",
    "node_calls_solve_phase",
    "dispatch_sweeps",
    "dispatch_sweeps_solve_phase",
    "n_model_calls",
    "block_loop_totals",
    "predicate_evaluations",
    "components_compared",
    "n_arrangement_method_calls",
    "exit_forensics.n_attempts",
    "exit_forensics.ifail",
    "exit_forensics.n_solver_iterations_summed_over_attempts",
    "mfile.ifail",
    "exact",
    "first_call_models.node_calls",
    "first_call_models.sweeps",
    "first_call_models.objf_hex",
)

#: The same, phase A.
COMPARED_A: tuple[str, ...] = (
    "status",
    "failure_class",
    "node_calls_total",
    "node_calls_single_eval",
    "n_model_calls_sweeps",
    "dispatch_sweeps",
    "block_loop_totals",
    "predicate_evaluations",
    "components_compared",
    "n_arrangement_method_calls",
    "exact",
)

#: Coupling-state files compared component by component where the campaign
#: record's folder has them.
STATE_FILES: tuple[str, ...] = (
    "y_entry.json",
    "y_exit.json",
    "y_before_finalise.json",
    "y_entry_to_write_output_files.json",
)


def _leaves(value: Any, prefix: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(value, dict):
        if not value:
            out[prefix] = "{}"
        for k, v in value.items():
            out.update(_leaves(v, f"{prefix}.{k}"))
    elif isinstance(value, list):
        if not value:
            out[prefix] = "[]"
        for i, v in enumerate(value):
            out.update(_leaves(v, f"{prefix}[{i}]"))
    else:
        out[prefix] = value
    return out


def _compared_leaves(record: Mapping[str, Any], paths: Iterable[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for path in paths:
        if records_mod.has_path(record, path):
            out.update(_leaves(records_mod.resolve_path(record, path), path))
        else:
            out[path] = "<absent>"
    return out


def _state_digest(path: Path) -> tuple[str | None, dict[str, Any] | None]:
    if not path.exists():
        return None, None
    state = json.loads(path.read_text()).get("state")
    blob = json.dumps(state, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest(), state


def compare_pair(campaign_dir: Path, traced_dir: Path, phase: str) -> dict[str, Any]:
    """One traced run against its campaign record."""
    base = records_mod.read(campaign_dir)
    traced = records_mod.read(traced_dir)
    paths = COMPARED_B if phase == "B" else COMPARED_A
    a = _compared_leaves(base, paths)
    b = _compared_leaves(traced, paths)
    differing = sorted(k for k in set(a) | set(b) if a.get(k, "<absent>") != b.get(k, "<absent>"))
    states: list[dict[str, Any]] = []
    n_components = n_components_differing = 0
    for name in STATE_FILES:
        da, sa = _state_digest(Path(campaign_dir) / name)
        db, sb = _state_digest(Path(traced_dir) / name)
        if da is None and db is None:
            continue
        row: dict[str, Any] = {"file": name, "campaign_sha256": da, "traced_sha256": db, "equal": da == db}
        if sa is not None and sb is not None:
            keys = set(sa) | set(sb)
            diff = sorted(k for k in keys if sa.get(k) != sb.get(k))
            row["n_components"] = len(keys)
            row["n_differing"] = len(diff)
            row["differing"] = diff[:20]
            n_components += len(keys)
            n_components_differing += len(diff)
        states.append(row)
    return {
        "campaign": str(campaign_dir),
        "traced": str(traced_dir),
        "campaign_tree_git_head": base.get("tree_git_head"),
        "traced_tree_git_head": traced.get("tree_git_head"),
        "traced_tree_git_dirty": traced.get("tree_git_dirty"),
        "n_leaves_compared": len(set(a) | set(b)),
        "n_leaves_differing": len(differing),
        "differing": [{"leaf": k, "campaign": a.get(k, "<absent>"), "traced": b.get(k, "<absent>")} for k in differing],
        "state_files": states,
        "n_state_components_compared": n_components,
        "n_state_components_differing": n_components_differing,
        "equal": not differing and all(s["equal"] for s in states) and bool(states),
    }


def trace_consistency(traced_dir: Path, record: Mapping[str, Any], phase: str) -> dict[str, Any]:
    """Lines and per-block sweeps of the trace against the record's own totals.

    Phase B: one line per evaluation of the record (``block_loop_totals``),
    the per-block sweeps summed over the lines equal to ``sweeps_by_block``.
    Phase A: the warmed child traces the discarded warm-up and the measured
    evaluation, so two lines; the last line's sweeps equal the record's.
    """
    handle = open_trace(traced_dir)
    if handle is None:
        return {"trace": "absent"}
    n_lines = 0
    header = None
    sums: dict[str, int] = {}
    last: dict[str, int] | None = None
    with handle:
        for raw in handle:
            line = json.loads(raw)
            if line.get("kind") == "header":
                header = line
                continue
            n_lines += 1
            last = dict(line.get("sweeps") or {})
            for block, n in last.items():
                sums[block] = sums.get(block, 0) + int(n)
    totals = record.get("block_loop_totals") or {}
    by_block = {k: int(v) for k, v in (totals.get("sweeps_by_block") or {}).items() if k in sums}
    n_evaluations = totals.get("n_call_models")
    if phase == "B":
        ok = n_lines == n_evaluations and all(sums.get(k) == v for k, v in by_block.items())
    else:
        ok = n_lines == 2 and last is not None and all(last.get(k) == v for k, v in by_block.items())
    return {
        "trace": "present",
        "header": header,
        "n_lines": n_lines,
        "record_n_call_models": n_evaluations,
        "trace_sweeps_by_block": sums if phase == "B" else last,
        "record_sweeps_by_block": by_block,
        "consistent": ok,
    }


def check(
    campaign: Campaign,
    job_set: JobSet,
    *,
    configurations: Iterable[str] | None = None,
    arms: Iterable[str] | None = None,
) -> dict[str, Any]:
    """The neutrality check over every traced run of *job_set* on disk."""
    job_pairs = pairs(campaign, job_set, configurations=configurations, arms=arms)
    rows: list[dict[str, Any]] = []
    for campaign_job, traced in job_pairs:
        campaign_dir = pool_mod.directory_for(campaign_job, campaign)
        traced_dir = Path(traced.outdir)
        key = f"{traced.phase}/{traced.config.name}/{traced.arm}/seed{traced.seed:03d}"
        if not (traced_dir / "metrics.json").exists():
            rows.append({"key": key, "traced": "absent"})
            continue
        row = {"key": key, **compare_pair(campaign_dir, traced_dir, traced.phase)}
        row["trace_consistency"] = trace_consistency(traced_dir, records_mod.read(traced_dir), traced.phase)
        # The traced run is the campaign job but for the declared fields: the
        # campaign record's own digest is the composed campaign job's, and the
        # two stamped identities differ in exactly IDENTITY_FIELDS_CHANGED.
        base = records_mod.read(campaign_dir)
        mine = records_mod.read(traced_dir)
        id_base = base.get("job_identity") or {}
        id_mine = mine.get("job_identity") or {}
        changed = sorted(k for k in set(id_base) | set(id_mine) if id_base.get(k) != id_mine.get(k))
        row["identity"] = {
            "campaign_record_digest_is_the_composed_job": base.get("job_digest")
            == pool_mod.digest_for(campaign_job, campaign),
            "identity_fields_differing": changed,
            "only_the_declared_fields_differ": set(changed) <= set(IDENTITY_FIELDS_CHANGED),
        }
        row["equal"] = bool(
            row["equal"]
            and row["identity"]["campaign_record_digest_is_the_composed_job"]
            and row["identity"]["only_the_declared_fields_differ"]
        )
        rows.append(row)
    present = [r for r in rows if r.get("traced") != "absent"]
    equal = [r for r in present if r["equal"]]
    consistent = [r for r in present if (r.get("trace_consistency") or {}).get("consistent")]
    return {
        "stage": "traced_runs_neutrality",
        "job_set": job_set.name,
        "run_id": campaign.run_id,
        "tree_git_head": framework.git_head(),
        "n_pairs": len(rows),
        "n_traced_present": len(present),
        "n_equal": len(equal),
        "n_differing": len(present) - len(equal),
        "n_trace_consistent": len(consistent),
        "differing_keys": [r["key"] for r in present if not r["equal"]],
        "inconsistent_trace_keys": [r["key"] for r in present if r not in consistent],
        "n_leaves_compared": sum(r["n_leaves_compared"] for r in present),
        "n_leaves_differing": sum(r["n_leaves_differing"] for r in present),
        "n_state_components_compared": sum(r["n_state_components_compared"] for r in present),
        "n_state_components_differing": sum(r["n_state_components_differing"] for r in present),
        "traced_commits": sorted({str(r.get("traced_tree_git_head")) for r in present}),
        "traced_dirty": sorted({str(r.get("traced_tree_git_dirty")) for r in present}),
        "compared_b": list(COMPARED_B),
        "compared_a": list(COMPARED_A),
        "state_files": list(STATE_FILES),
        "rows": rows,
    }


def listing(campaign: Campaign, job_set: JobSet, **narrow) -> list[str]:
    """One line per traced job: its key, directory and the resume decision."""
    lines = []
    for campaign_job, traced in pairs(campaign, job_set, **narrow):
        identity = traced.identity(Path(campaign.runs_dir), campaign=campaign)
        digest = records_mod.job_digest(identity)
        why = pool_mod.why_not_kept(
            traced, campaign, identity=identity, digest=digest, directory=Path(traced.outdir)
        )
        lines.append(
            f"{traced.key}  ->  {Path(traced.outdir).relative_to(campaign.runs_dir)}  "
            f"[{'kept' if why is None else why}]  (campaign: "
            f"{Path(pool_mod.directory_for(campaign_job, campaign)).relative_to(campaign.runs_dir)})"
        )
    return lines
