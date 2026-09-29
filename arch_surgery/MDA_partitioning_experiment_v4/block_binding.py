#!/usr/bin/env python
"""Which block binds an evaluation, and why M2 stops binding in the optimisation phase.

Task A90 (m2-phasea-vs-phaseb).  In the evaluation phase the partitioned arm's
second block, M2, sweeps as often as the flat loop does (it *binds*); in the
optimisation phase it sweeps ~15-30 % less per evaluation.  This script
produces every number the task's report cites, in two subcommands:

``records``
    From the campaign's run records (read-only, through the harness's own
    population code, so the arm names are today's — trap T16): per
    configuration and arm, M2 sweeps per evaluation of the model set over the
    paper's seed set, the exact decomposition of the paper's B2/B0 module
    ratio into per-evaluation and evaluation-count factors, whether B1 and B2
    follow the same optimiser path, and whether the per-evaluation ratio
    depends on how long the run is.  Also the evaluation phase's counterpart.

``trace``
    From the per-evaluation block trace (switch ``PROCESS_ARCH_BLOCK_TRACE``)
    of fresh gate runs: the binding block of each flat evaluation, M2's sweeps
    in each partitioned evaluation, both keyed by the kind of evaluation the
    optimiser asked for.  Added with the instrumentation.

**The quantity.**  *M2 sweeps per evaluation* is the solve phase's count, one
number per ``call_models``: ``block_loop_totals.sweeps_by_block`` (``M2`` in
the partitioned arm; ``FLAT`` in a flat arm, whose one block holds every
in-loop node, M2's included) divided by ``block_loop_totals.n_call_models``.
The reference arm ``BR`` runs no block schedule; its count is
``sweeps_per_eval.n_sweeps`` over ``sweeps_per_eval.n_evaluations``.  The
paper's phase B cells are the whole-run census less the exit audit, which
also holds the output path's sweeps; ``records`` reconciles the two per run
and refuses a run where they do not agree.

``trace-runs``
    Makes those runs: each is the campaign's own job with its directory
    (``runs/block_trace/``), its run kind (``gate``) and ``override_env``
    changed, so no campaign record is written and no identity collides.
    Plus untraced controls on the block-schedule path.

Usage::

    python block_binding.py records [--runs <runs root>] [--json out.json]
    python block_binding.py trace-runs [--which controls evaluation optimisation] [--resume] [--list]
    python block_binding.py trace [--json out.json]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from harness.core.config import default_campaign  # noqa: E402
from harness.measurement import paper_tables as paper  # noqa: E402
from harness.measurement import stats as stats_mod  # noqa: E402
from harness.measurement import tally as tally_mod  # noqa: E402
from harness.measurement import tally_evaluation as tally_a  # noqa: E402
from harness.measurement import tally_optimisation as tally_b  # noqa: E402

FLAT = "FLAT"


class BindingError(RuntimeError):
    """A record does not support the construction; refused, never absorbed."""


# --------------------------------------------------------------------------
# per-record quantities
# --------------------------------------------------------------------------


def m2_sweeps_and_evaluations(record: Mapping[str, Any]) -> tuple[int, int]:
    """``(M2 sweeps, evaluations)`` over the solve phase of one run."""
    totals = record.get("block_loop_totals") or {}
    by_block = totals.get("sweeps_by_block") or {}
    if totals.get("n_call_models"):
        n = int(totals["n_call_models"])
        if "M2" in by_block:
            return int(by_block["M2"]), n
        if FLAT in by_block:
            return int(by_block[FLAT]), n
        raise BindingError(f"block totals carry neither M2 nor {FLAT}: {sorted(by_block)}")
    spe = record.get("sweeps_per_eval") or {}
    if spe.get("n_evaluations"):
        return int(spe["n_sweeps"]), int(spe["n_evaluations"])
    raise BindingError("the record carries no per-evaluation sweep count")


def block_sweeps(record: Mapping[str, Any]) -> dict[str, int]:
    """Solve-phase sweeps per block (the partitioned arm's M1/M2/M3)."""
    by_block = ((record.get("block_loop_totals") or {}).get("sweeps_by_block")) or {}
    return {k: int(v) for k, v in by_block.items() if v}


def census_m2(record: Mapping[str, Any], groups) -> float:
    """The paper table's cell for M2 in one run: whole-run census less the audit."""
    return stats_mod.module_sweeps(paper._without_exit_audit(record), groups)["M2"]


def reconcile(record: Mapping[str, Any], groups) -> dict[str, Any]:
    """Paper cell = solve-phase M2 sweeps + output-loop sweeps, per run.

    The output loop (``MDA_Output``, flat arms only) sweeps every node once per
    pass; the partitioned arm's output pass runs the deferred nodes alone, none
    of them in M2.  Stated as an identity and checked, not assumed.
    """
    solve, _ = m2_sweeps_and_evaluations(record)
    output = int(record.get("output_loop_sweeps") or 0)
    cell = census_m2(record, groups)
    return {"solve": solve, "output": output, "cell": cell, "agrees": cell == solve + output}


# --------------------------------------------------------------------------
# summaries
# --------------------------------------------------------------------------


def _median(values: Sequence[float]) -> float | None:
    return stats_mod.median(list(values)) if values else None


def _bracket(values: Sequence[float]) -> list[float] | None:
    return [min(values), max(values)] if values else None


def per_eval_ratio(a: tuple[int, int], b: tuple[int, int]) -> float:
    """``(sweeps_b / evals_b) / (sweeps_a / evals_a)`` for one seed."""
    return (b[0] / b[1]) / (a[0] / a[1])


def series_identity(dir_a: Path, dir_b: Path) -> dict[str, Any]:
    """Compare two runs' per-evaluation entry series element by element.

    ``entry_census_series.json`` holds ``p_plant_electric_net_mw_at_entry`` at
    the head of every ``call_models``: a quantity of the coupling state the
    evaluation is entered from, so two runs that visit the same sequence of
    points read the same sequence.  Bit-identity is counted exactly; the rest
    is the largest relative difference.
    """
    a = json.loads((dir_a / "entry_census_series.json").read_text())
    b = json.loads((dir_b / "entry_census_series.json").read_text())
    if len(a) != len(b):
        return {"same_length": False, "n_a": len(a), "n_b": len(b)}
    identical = sum(1 for x, y in zip(a, b) if float(x).hex() == float(y).hex())
    rel = [
        abs(x - y) / abs(x) if x else (0.0 if y == 0 else math.inf)
        for x, y in zip(a, b)
    ]
    return {
        "same_length": True,
        "n": len(a),
        "n_bit_identical": identical,
        "max_relative_difference": max(rel) if rel else 0.0,
    }


# --------------------------------------------------------------------------
# the optimisation phase
# --------------------------------------------------------------------------


def _paths(campaign) -> dict[tuple[str, str, int], Path]:
    """``(arm, configuration, seed) -> run directory`` for the phase B source."""
    sources = {s.name: s for s in tally_mod.published_sources(campaign)}
    rows, refusals = tally_mod.source_rows(campaign, sources[paper.PHASE_B_SOURCE])
    if refusals:
        raise BindingError(f"{len(refusals)} phase B record(s) refused; first: {refusals[0]}")
    out = {}
    for row in rows:
        r = row.record
        # a row's path is the record file; the series sits beside it
        run_dir = row.path.parent if row.path.name == "metrics.json" else row.path
        out[(str(r["campaign_arm"]), str(r["campaign_configuration"]), int(r["campaign_seed"]))] = run_dir
    return out


def optimisation(campaign) -> list[dict[str, Any]]:
    paths = _paths(campaign)
    blocks: list[dict[str, Any]] = []
    for configuration, by_arm, converged in paper._phase_b_groups(campaign):
        records = [by_arm[a][s] for a in by_arm for s in converged if s in by_arm[a]]
        groups = tally_a.node_grouping(campaign, configuration, records, phase=tally_b.PHASE)
        arms = [a for a in tally_b.LADDER if a in by_arm]
        counts = {a: {s: m2_sweeps_and_evaluations(by_arm[a][s]) for s in converged} for a in arms}

        # the reconciliation with the paper's cells, every run of the seed set
        mismatches = []
        for a in arms:
            for s in converged:
                rec = reconcile(by_arm[a][s], groups)
                if not rec["agrees"]:
                    mismatches.append({"arm": a, "seed": s, **rec})

        pooled = {
            a: {
                "m2_sweeps": sum(c[0] for c in counts[a].values()),
                "evaluations": sum(c[1] for c in counts[a].values()),
            }
            for a in arms
        }
        for a in arms:
            pooled[a]["per_evaluation"] = pooled[a]["m2_sweeps"] / pooled[a]["evaluations"]

        # B2's other blocks, for context
        b2_blocks: dict[str, int] = {}
        for s in converged:
            for k, v in block_sweeps(by_arm["B2"][s]).items():
                b2_blocks[k] = b2_blocks.get(k, 0) + v
        b2_blocks_per_eval = {
            k: v / pooled["B2"]["evaluations"] for k, v in sorted(b2_blocks.items())
        }

        def factor(num: str, den: str, what: str) -> float:
            return pooled[num][what] / pooled[den][what]

        decomposition = {
            "per_run_B2_over_B0": factor("B2", "B0", "m2_sweeps"),
            "per_evaluation_B2_over_B0": factor("B2", "B0", "per_evaluation"),
            "evaluations_B2_over_B0": factor("B2", "B0", "evaluations"),
        }
        if "B1" in arms:
            decomposition["per_evaluation_B1_over_B0"] = factor("B1", "B0", "per_evaluation")
            decomposition["per_evaluation_B2_over_B1"] = factor("B2", "B1", "per_evaluation")
        # the identities the decomposition rests on, checked to rounding
        lhs = decomposition["per_run_B2_over_B0"]
        rhs = decomposition["per_evaluation_B2_over_B0"] * decomposition["evaluations_B2_over_B0"]
        decomposition["identity_residual"] = lhs - rhs

        # the path: B1 against B2 on the same seed
        ref = "B1" if "B1" in arms else "B0"
        path = []
        for s in converged:
            ident = series_identity(paths[(ref, configuration, s)], paths[("B2", configuration, s)])
            path.append({
                "seed": s,
                "evaluations_equal": counts[ref][s][1] == counts["B2"][s][1],
                "iterations_equal": (
                    by_arm[ref][s].get("n_solver_iterations")
                    == by_arm["B2"][s].get("n_solver_iterations")
                ),
                **ident,
            })

        per_seed = sorted(
            (counts["B2"][s][1], per_eval_ratio(counts[ref][s], counts["B2"][s]), s)
            for s in converged
        )
        ratios = [r for _, r, _ in per_seed]
        half = len(per_seed) // 2
        blocks.append({
            "configuration": configuration,
            "n": len(converged),
            "seeds": list(converged),
            "arms": arms,
            "pooled": pooled,
            "B2_blocks_per_evaluation": b2_blocks_per_eval,
            "decomposition": decomposition,
            "paper_reconciliation_mismatches": mismatches,
            "path_reference_arm": ref,
            "path": path,
            "per_seed_ratio_reference": ref,
            "per_seed_ratio": [
                {"seed": s, "B2_evaluations": n, "ratio": r} for n, r, s in per_seed
            ],
            "per_seed_ratio_median": _median(ratios),
            "per_seed_ratio_bracket": _bracket(ratios),
            "shorter_half_median": _median(ratios[:half]),
            "longer_half_median": _median(ratios[half:]),
            "shorter_half_evaluations": _bracket([n for n, _, _ in per_seed[:half]]),
            "longer_half_evaluations": _bracket([n for n, _, _ in per_seed[half:]]),
        })
    return blocks


# --------------------------------------------------------------------------
# the evaluation phase
# --------------------------------------------------------------------------


def evaluation(campaign) -> list[dict[str, Any]]:
    population = paper._population(campaign, paper.PHASE_A_SOURCE, tally_a.PHASE)
    out = []
    for config in campaign.configurations:
        by_seed = tally_a._by_arm_and_seed(population, config.name)
        if not by_seed:
            continue
        flat_ref = "A1" if "A1" in by_seed else "A0"
        seeds = sorted(
            s for s in by_seed.get("A2", {})
            if s in by_seed.get(flat_ref, {})
            and stats_mod.finished(by_seed["A2"][s])
            and stats_mod.finished(by_seed[flat_ref][s])
        )
        rows = []
        for s in seeds:
            flat, nf = m2_sweeps_and_evaluations(by_seed[flat_ref][s])
            part = block_sweeps(by_seed["A2"][s])
            _, np_ = m2_sweeps_and_evaluations(by_seed["A2"][s])
            if nf != 1 or np_ != 1:
                raise BindingError(f"{config.name} seed {s}: a phase A run is one evaluation")
            rows.append({"seed": s, "flat": flat, **{f"A2_{k}": v for k, v in part.items()}})
        m2_equal = sum(1 for r in rows if r.get("A2_M2") == r["flat"])
        m2_max = sum(
            1 for r in rows
            if r.get("A2_M2") == max(r.get("A2_M1", 0), r.get("A2_M2", 0), r.get("A2_M3", 0))
        )
        out.append({
            "configuration": config.name,
            "flat_reference_arm": flat_ref,
            "n": len(rows),
            "n_M2_equals_flat": m2_equal,
            "n_M2_is_largest_block": m2_max,
            "pooled_M2_over_flat": (
                sum(r.get("A2_M2", 0) for r in rows) / sum(r["flat"] for r in rows)
            ) if rows else None,
            "rows": rows,
        })
    return out


# --------------------------------------------------------------------------
# the traced runs
# --------------------------------------------------------------------------

#: Under the experiment's ``runs/``; never under ``runs/campaign/`` (read-only
#: here) nor ``runs/gates/`` (the tally's declared sources live there).
TRACE_ROOT = "block_trace"
TRACE_FILE = "block_trace.jsonl"
TRACE_VARIABLE = "PROCESS_ARCH_BLOCK_TRACE"

#: The traced arms: every flat and partitioned arm active on the
#: configuration.  ``B1``/``A1`` do not exist on ``st_regression``.
TRACED_ARMS = {
    "B": {
        "large_tokamak_nof": ("B0", "B1", "B2"),
        "low_aspect_ratio_DEMO": ("B0", "B1", "B2"),
        "st_regression": ("B0", "B2"),
    },
    "A": {
        "large_tokamak_nof": ("A0", "A1", "A2"),
        "low_aspect_ratio_DEMO": ("A0", "A1", "A2"),
        "st_regression": ("A0", "A2"),
    },
}

#: The untraced controls: the same job with the switch unset, at this tree,
#: to show the hooks change nothing on the block-schedule path with the
#: switch off (gate G1 runs only the arms with every switch unset, which never
#: reach that path).  The first seed of the paper's set, per configuration.
CONTROL_ARMS = {
    "large_tokamak_nof": ("B1", "B2"),
    "low_aspect_ratio_DEMO": ("B2",),
    "st_regression": ("B2",),
}


def _phase_b_seed_sets(campaign) -> dict[str, list[int]]:
    return {c: list(conv) for c, _by_arm, conv in paper._phase_b_groups(campaign)}


def trace_jobs(campaign) -> dict[str, list]:
    """The traced population, composed from the campaign's own jobs.

    Each is the campaign job of the same arm, configuration and seed with
    three fields changed: its directory, its run kind (``gate``) and, for a
    traced job, ``override_env`` naming the trace file -- which also makes its
    identity differ from every campaign job's.  The optimisation phase takes
    the paper's seed set (every arm reached an accepted optimum); the
    evaluation phase takes every displaced seed.
    """
    import dataclasses  # noqa: PLC0415

    from harness import chain as chain_mod  # noqa: PLC0415
    from harness.core import pool as pool_mod  # noqa: PLC0415

    root = Path(campaign.runs_dir) / TRACE_ROOT
    b_seeds = _phase_b_seed_sets(campaign)

    def traced(job, sub: str):
        outdir = root / sub / job.config.name / job.arm / pool_mod.seed_directory(job.seed)
        return dataclasses.replace(
            job, outdir=outdir, run_kind="gate",
            override_env={TRACE_VARIABLE: str(outdir / TRACE_FILE)},
        )

    def untraced(job):
        outdir = root / "untraced" / job.config.name / job.arm / pool_mod.seed_directory(job.seed)
        return dataclasses.replace(job, outdir=outdir, run_kind="gate", override_env={})

    out: dict[str, list] = {"optimisation": [], "evaluation": [], "controls": []}
    for job in chain_mod.campaign_jobs(campaign, "optimisation"):
        c = job.config.name
        if job.arm in TRACED_ARMS["B"].get(c, ()) and job.seed in b_seeds.get(c, ()):
            out["optimisation"].append(traced(job, "optimisation"))
        if job.arm in CONTROL_ARMS.get(c, ()) and b_seeds.get(c) and job.seed == b_seeds[c][0]:
            out["controls"].append(untraced(job))
    for job in chain_mod.campaign_jobs(campaign, "evaluation_displaced"):
        if job.arm in TRACED_ARMS["A"].get(job.config.name, ()):
            out["evaluation"].append(traced(job, "evaluation"))
    return out


def run_traces(campaign, *, which: Sequence[str], resume: bool) -> dict[str, Any]:
    from harness.core import pool as pool_mod  # noqa: PLC0415

    jobs = trace_jobs(campaign)
    summary: dict[str, Any] = {}
    for name in which:
        results = pool_mod.run_all(jobs[name], campaign, resume=resume)
        statuses: dict[str, int] = {}
        for r in results:
            statuses[str(r.get("status"))] = statuses.get(str(r.get("status")), 0) + 1
        summary[name] = {"n_jobs": len(jobs[name]), "statuses": statuses}
        print(f"  {name}: {len(jobs[name])} job(s), statuses {statuses}")
    return summary


# --------------------------------------------------------------------------
# reading a trace
# --------------------------------------------------------------------------


def read_trace(path: Path) -> tuple[dict, list[dict]]:
    lines = [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]
    if not lines or lines[0].get("kind") != "header":
        raise BindingError(f"{path}: no header line")
    return lines[0], lines[1:]


def flat_binding(per_sweep: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """The binding block of one flat evaluation.

    **Definition (stated once, used everywhere).**  The flat loop sweeps every
    in-loop node and stops after the first sweep on which no coupling
    component fails the test at τ.  After each sweep a module is *open* if any
    of its own components (the committed write sets partition the coupling
    state by module, with no overlap and nothing left over) would fail.  Let
    ``L_m`` be the last sweep after which module ``m`` was open (0 if never).
    The loop stops at ``k = 1 + max_m L_m`` -- checked on every evaluation --
    and the **binding** module(s) are those with ``L_m = max L``: the last to
    reach τ.  With ``max L = 0`` the evaluation entered converged and nothing
    binds.
    """
    last: dict[str, int] = {}
    for s, sweep in enumerate(per_sweep, start=1):
        for m in sweep["open"]:
            last[m] = s
    k = len(per_sweep)
    top = max(last.values()) if last else 0
    binders = sorted(m for m, v in last.items() if v == top) if top else []
    return {"k": k, "last_open": last, "max_last_open": top, "binders": binders,
            "consistent": k == top + 1}


def kind_of(line: Mapping[str, Any], itvar_names: Sequence[str] | None) -> tuple[str, str | None]:
    """``(evaluation kind, design variable)`` from the optimiser's own label."""
    ev = line.get("evaluation")
    if ev is None:
        return "unlabelled", None
    if ev[0] == "gradient":
        col = int(ev[1])
        name = itvar_names[col] if itvar_names and col < len(itvar_names) else f"column {col}"
        return "gradient", name
    return str(ev[0]), None


def _run_dirs(campaign, phase_sub: str) -> dict[tuple[str, str, int], Path]:
    root = Path(campaign.runs_dir) / TRACE_ROOT / phase_sub
    out = {}
    if not root.exists():
        return out
    for metrics in sorted(root.glob("*/*/seed*/metrics.json")):
        d = metrics.parent
        out[(d.parent.parent.name, d.parent.name, int(d.name.removeprefix("seed")))] = d
    return out


_CAMPAIGN_INDEX: dict[str, dict[tuple[str, str, int], Mapping[str, Any]]] = {}


def _campaign_record(campaign, phase: str, config: str, arm: str, seed: int) -> Mapping[str, Any]:
    """The campaign record of one job, read through the tally's declared source.

    Not through the job's composed directory: the campaign records sit under
    the arm names of the day they were made (``B3``, ``A0p``), and the source
    reader is where today's names are applied (trap T16).
    """
    name = paper.PHASE_B_SOURCE if phase == "B" else paper.PHASE_A_SOURCE
    index = _CAMPAIGN_INDEX.get(name)
    if index is None:
        sources = {s.name: s for s in tally_mod.published_sources(campaign)}
        rows, refusals = tally_mod.source_rows(campaign, sources[name])
        if refusals:
            raise BindingError(f"[{name}] {len(refusals)} record(s) refused; first: {refusals[0]}")
        index = {}
        for row in rows:
            r = row.record
            index[(str(r["campaign_configuration"]), str(r["campaign_arm"]), int(r["campaign_seed"]))] = r
        _CAMPAIGN_INDEX[name] = index
    record = index.get((config, arm, seed))
    if record is None:
        raise BindingError(f"no campaign record {arm}/{config}/seed{seed} in {name}")
    return record


#: What a traced (or untraced control) run must reproduce of the campaign
#: run of the same job, exactly.
REPRODUCED = (
    ("status", lambda r: r.get("status")),
    ("n_call_models", lambda r: (r.get("block_loop_totals") or {}).get("n_call_models")),
    ("sweeps_by_block", lambda r: (r.get("block_loop_totals") or {}).get("sweeps_by_block")),
    ("n_solver_iterations", lambda r: r.get("n_solver_iterations")),
    ("norm_objf_hex", lambda r: (
        float.hex(float(r["values"]["norm_objf"]))
        if (r.get("values") or {}).get("norm_objf") is not None else None)),
    ("node_calls_solve_phase", lambda r: r.get("node_calls_solve_phase")),
)


def reproduction(campaign, phase: str, config: str, arm: str, seed: int, record) -> dict[str, Any]:
    ref = _campaign_record(campaign, phase, config, arm, seed)
    diffs = {name: {"campaign": f(ref), "here": f(record)}
             for name, f in REPRODUCED if f(ref) != f(record)}
    return {"n_fields": len(REPRODUCED), "differing": diffs}


def _load_runs(campaign, phase: str) -> dict[tuple[str, str, int], dict[str, Any]]:
    """Every traced run of one phase: its record, its trace, its checks."""
    from harness.core import records as records_mod  # noqa: PLC0415

    sub = "optimisation" if phase == "B" else "evaluation"
    runs = {}
    for key, d in _run_dirs(campaign, sub).items():
        config, arm, seed = key
        record = records_mod.read(d)
        header, lines = read_trace(d / TRACE_FILE)
        totals = record.get("block_loop_totals") or {}
        summed: dict[str, int] = {}
        for ln in lines:
            for b, v in ln["sweeps"].items():
                summed[b] = summed.get(b, 0) + int(v)
        recorded = {k: int(v) for k, v in (totals.get("sweeps_by_block") or {}).items()}
        runs[key] = {
            "dir": d, "record": record, "header": header, "lines": lines,
            "checks": {
                "lines_equal_evaluations": len(lines) == int(totals.get("n_call_models") or -1),
                "sweeps_sum_to_record": {b: v for b, v in summed.items() if v} == {b: v for b, v in recorded.items() if v},
                "reproduces_campaign": reproduction(campaign, phase, config, arm, seed, record),
            },
        }
    return runs


# --------------------------------------------------------------------------
# the trace analysis
# --------------------------------------------------------------------------


def _is_flat(line: Mapping[str, Any]) -> bool:
    return FLAT in line["per_sweep"] or FLAT in line["sweeps"]


def _binder_label(binders: Sequence[str]) -> str:
    return "+".join(binders) if binders else "none (entered converged)"


def evaluation_trace(campaign) -> list[dict[str, Any]]:
    """Prediction (d): in the evaluation phase M2 binds the flat loop."""
    runs = _load_runs(campaign, "A")
    out = []
    for config in sorted({k[0] for k in runs}):
        for arm in sorted({k[1] for k in runs if k[0] == config}):
            keys = sorted(k for k in runs if k[0] == config and k[1] == arm)
            if not keys:
                continue
            first = runs[keys[0]]["lines"][0] if runs[keys[0]]["lines"] else None
            if first is None or not _is_flat(first):
                continue
            binders: dict[str, int] = {}
            m2_binds = m2_sole = inconsistent = 0
            for k in keys:
                line = runs[k]["lines"][0]
                b = flat_binding(line["per_sweep"][FLAT])
                inconsistent += not b["consistent"]
                label = _binder_label(b["binders"])
                binders[label] = binders.get(label, 0) + 1
                m2_binds += "M2" in b["binders"]
                m2_sole += b["binders"] == ["M2"]
            out.append({"configuration": config, "arm": arm, "n": len(keys),
                        "M2_binds": m2_binds, "M2_sole_binder": m2_sole,
                        "binders": dict(sorted(binders.items(), key=lambda kv: -kv[1])),
                        "binding_inconsistent": inconsistent})
    return out


def optimisation_trace(campaign) -> list[dict[str, Any]]:
    """Predictions (a)-(c) over the optimisation phase's traced runs."""
    runs = _load_runs(campaign, "B")
    blocks = []
    for config in sorted({k[0] for k in runs}):
        arms = sorted({k[1] for k in runs if k[0] == config})
        flat_ref = "B1" if "B1" in arms else "B0"
        seeds = sorted({k[2] for k in runs if k[0] == config and k[1] == flat_ref}
                       & {k[2] for k in runs if k[0] == config and k[1] == "B2"})
        itvars = None
        # (a) the binder in the flat arms, by evaluation kind and variable
        flat_tables = {}
        for arm in [a for a in arms if a != "B2"]:
            by_kind: dict[str, dict[str, int]] = {}
            by_var: dict[str, dict[str, int]] = {}
            n = inconsistent = 0
            for s in [k[2] for k in runs if k[0] == config and k[1] == arm]:
                run = runs[(config, arm, s)]
                itvars = run["record"].get("itvar_names")
                for ln in run["lines"]:
                    b = flat_binding(ln["per_sweep"].get(FLAT, []))
                    inconsistent += not b["consistent"]
                    n += 1
                    kind, var = kind_of(ln, itvars)
                    label = _binder_label(b["binders"])
                    by_kind.setdefault(kind, {})
                    by_kind[kind][label] = by_kind[kind].get(label, 0) + 1
                    if var is not None:
                        by_var.setdefault(var, {})
                        by_var[var][label] = by_var[var].get(label, 0) + 1
            flat_tables[arm] = {"n_evaluations": n, "binding_inconsistent": inconsistent,
                                "by_kind": by_kind, "by_variable": by_var}

        # (b)/(c) evaluation by evaluation, the flat reference against B2
        paired = {"n": 0, "x_identical": 0, "kind_identical": 0}
        groups: dict[str, dict[str, Any]] = {}
        hist: dict[str, dict[int, int]] = {}
        by_var_pair: dict[str, dict[str, int]] = {}
        for s in seeds:
            fr, pr = runs[(config, flat_ref, s)], runs[(config, "B2", s)]
            for lf, lp in zip(fr["lines"], pr["lines"]):
                paired["n"] += 1
                if lf["x"] != lp["x"]:
                    continue
                paired["x_identical"] += 1
                paired["kind_identical"] += lf.get("evaluation") == lp.get("evaluation")
                b = flat_binding(lf["per_sweep"].get(FLAT, []))
                m2_binds = "M2" in b["binders"]
                g = "M2 binds the flat loop" if m2_binds else "M2 does not bind"
                flat_k = int(lf["sweeps"].get(FLAT, 0))
                m2 = int(lp["sweeps"].get("M2", 0))
                grp = groups.setdefault(g, {"n": 0, "flat_sweeps": 0, "B2_M2_sweeps": 0,
                                            "M2_settle_in_flat": 0})
                grp["n"] += 1
                grp["flat_sweeps"] += flat_k
                grp["B2_M2_sweeps"] += m2
                grp["M2_settle_in_flat"] += b["last_open"].get("M2", 0) + 1
                hist.setdefault(g, {})
                hist[g][m2] = hist[g].get(m2, 0) + 1
                kind, var = kind_of(lf, itvars)
                if var is not None:
                    v = by_var_pair.setdefault(var, {"n": 0, "M2_binds": 0, "flat": 0, "M2": 0})
                    v["n"] += 1
                    v["M2_binds"] += m2_binds
                    v["flat"] += flat_k
                    v["M2"] += m2
        total_flat = sum(g["flat_sweeps"] for g in groups.values())
        total_m2 = sum(g["B2_M2_sweeps"] for g in groups.values())
        saving = total_flat - total_m2
        for g in groups.values():
            g["ratio"] = g["B2_M2_sweeps"] / g["flat_sweeps"] if g["flat_sweeps"] else None
            g["share_of_saving"] = ((g["flat_sweeps"] - g["B2_M2_sweeps"]) / saving) if saving else None
            g["mean_flat"] = g["flat_sweeps"] / g["n"]
            g["mean_B2_M2"] = g["B2_M2_sweeps"] / g["n"]
            g["mean_M2_settle_in_flat"] = g["M2_settle_in_flat"] / g["n"]

        # the same ratio from the campaign records of the same seeds, exactly
        camp_flat = camp_m2 = 0
        for s in seeds:
            f_sw, _ = m2_sweeps_and_evaluations(_campaign_record(campaign, "B", config, flat_ref, s))
            p_sw, _ = m2_sweeps_and_evaluations(_campaign_record(campaign, "B", config, "B2", s))
            camp_flat += f_sw
            camp_m2 += p_sw
        checks = {
            f"{a}/seed{k[2]}": runs[k]["checks"]
            for k in sorted(runs) if k[0] == config for a in [k[1]]
        }
        blocks.append({
            "configuration": config, "flat_reference": flat_ref, "seeds": seeds,
            "flat_tables": flat_tables, "paired": paired, "groups": groups,
            "B2_M2_sweeps_histogram": {g: dict(sorted(h.items())) for g, h in hist.items()},
            "by_variable_paired": by_var_pair,
            "traced_ratio": (total_m2 / total_flat) if total_flat else None,
            "traced_totals": {"flat": total_flat, "B2_M2": total_m2},
            "campaign_totals_same_seeds": {"flat": camp_flat, "B2_M2": camp_m2},
            "campaign_ratio_same_seeds": (camp_m2 / camp_flat) if camp_flat else None,
            "run_checks": checks,
        })
    return blocks


def controls(campaign) -> list[dict[str, Any]]:
    from harness.core import records as records_mod  # noqa: PLC0415

    out = []
    for key, d in _run_dirs(campaign, "untraced").items():
        config, arm, seed = key
        record = records_mod.read(d)
        out.append({"configuration": config, "arm": arm, "seed": seed,
                    "trace_file_absent": not (d / TRACE_FILE).exists(),
                    **reproduction(campaign, "B", config, arm, seed, record)})
    return out


# --------------------------------------------------------------------------
# printing
# --------------------------------------------------------------------------


def _f(x, d=4):
    return "—" if x is None else f"{x:.{d}f}"


def print_records(result: dict[str, Any]) -> None:
    print("## Optimisation phase (paper seed set: every arm reached an accepted optimum)\n")
    for b in result["optimisation"]:
        c = b["configuration"]
        print(f"### {c} (n = {b['n']})")
        for a in b["arms"]:
            p = b["pooled"][a]
            print(f"  {a:3s} M2 sweeps {p['m2_sweeps']:>8d}  evaluations {p['evaluations']:>7d}  "
                  f"per evaluation {p['per_evaluation']:.4f}")
        print("  B2 blocks per evaluation: "
              + ", ".join(f"{k} {v:.4f}" for k, v in b["B2_blocks_per_evaluation"].items()))
        for k, v in b["decomposition"].items():
            print(f"  {k}: {v:.6g}" if k == "identity_residual" else f"  {k}: {v:.4f}")
        print(f"  paper-cell reconciliation mismatches: {len(b['paper_reconciliation_mismatches'])}"
              f" of {b['n'] * len(b['arms'])} runs")
        ref = b["path_reference_arm"]
        pth = b["path"]
        print(f"  path {ref} vs B2: evaluations equal {sum(p['evaluations_equal'] for p in pth)}/{len(pth)}, "
              f"iterations equal {sum(p['iterations_equal'] for p in pth)}/{len(pth)}, "
              f"series same length {sum(p['same_length'] for p in pth)}/{len(pth)}")
        same = [p for p in pth if p["same_length"]]
        if same:
            bit = sum(p["n_bit_identical"] for p in same)
            tot = sum(p["n"] for p in same)
            print(f"    entry series: {bit}/{tot} evaluations bit-identical; "
                  f"seeds wholly identical {sum(p['n_bit_identical'] == p['n'] for p in same)}/{len(same)}; "
                  f"max relative difference {max(p['max_relative_difference'] for p in same):.3e}")
        print(f"  per-seed B2/{b['per_seed_ratio_reference']} M2 per evaluation: median "
              f"{_f(b['per_seed_ratio_median'])} [{_f(b['per_seed_ratio_bracket'][0])}, "
              f"{_f(b['per_seed_ratio_bracket'][1])}]")
        print(f"    shorter half (B2 evaluations {b['shorter_half_evaluations']}): median {_f(b['shorter_half_median'])}; "
              f"longer half ({b['longer_half_evaluations']}): median {_f(b['longer_half_median'])}")
        print()
    print("## Evaluation phase (displaced entries)\n")
    for e in result["evaluation"]:
        print(f"### {e['configuration']} (n = {e['n']}, flat reference {e['flat_reference_arm']})")
        print(f"  A2's M2 sweeps equal the flat loop's on {e['n_M2_equals_flat']}/{e['n']} runs; "
              f"M2 is (joint-)largest of A2's blocks on {e['n_M2_is_largest_block']}/{e['n']}; "
              f"pooled M2/flat {_f(e['pooled_M2_over_flat'])}")
        print()


def _share(part: int, whole: int) -> str:
    return f"{part}/{whole} ({part / whole:.3f})" if whole else f"{part}/0"


def print_trace(result: dict[str, Any]) -> None:
    print("## Checks on every traced run\n")
    n = bad = 0
    for block in result["optimisation"]:
        for key, ch in block["run_checks"].items():
            n += 1
            ok = (ch["lines_equal_evaluations"] and ch["sweeps_sum_to_record"]
                  and not ch["reproduces_campaign"]["differing"])
            if not ok:
                bad += 1
                print(f"  FAILED {block['configuration']} {key}: {ch}")
    print(f"  optimisation phase: {n - bad}/{n} traced runs have one trace line per "
          f"evaluation, trace sweeps summing to the record's, and reproduce the campaign "
          f"run's {len(REPRODUCED)} fields exactly")
    for c in result["controls"]:
        state = "reproduces" if not c["differing"] else f"DIFFERS {c['differing']}"
        print(f"  untraced control {c['arm']}/{c['configuration']}/seed{c['seed']}: {state} "
              f"the campaign run on {c['n_fields']} fields; trace file absent: {c['trace_file_absent']}")
    ea = result.get("evaluation_checks") or {}
    if ea:
        print(f"  evaluation phase: {ea['ok']}/{ea['n']} traced runs pass the same checks")
    print()

    print("## (d) Evaluation phase: which module binds the flat loop\n")
    for e in result["evaluation"]:
        print(f"  {e['configuration']:<22} {e['arm']}: M2 binds {_share(e['M2_binds'], e['n'])}, "
              f"sole binder {_share(e['M2_sole_binder'], e['n'])}; binders {e['binders']}; "
              f"k = 1 + max L violated on {e['binding_inconsistent']}")
    print()

    print("## (a) Optimisation phase: which module binds the flat loop\n")
    for b in result["optimisation"]:
        for arm, t in b["flat_tables"].items():
            print(f"### {b['configuration']} {arm}: {t['n_evaluations']} evaluations "
                  f"(k = 1 + max L violated on {t['binding_inconsistent']})")
            for kind, dist in t["by_kind"].items():
                tot = sum(dist.values())
                m2 = sum(v for k, v in dist.items() if "M2" in k.split("+"))
                print(f"    {kind:<11} n {tot:>6}  M2 binds {_share(m2, tot)}  binders {dist}")
        print()

    print("## (b)/(c) Evaluation by evaluation: the flat reference against B2\n")
    for b in result["optimisation"]:
        p = b["paired"]
        print(f"### {b['configuration']}: {b['flat_reference']} vs B2, seeds {len(b['seeds'])}; "
              f"{p['x_identical']}/{p['n']} evaluation pairs at the identical design vector "
              f"(kind identical on {p['kind_identical']})")
        for g, v in b["groups"].items():
            print(f"    {g:<24} n {v['n']:>6}  flat sweeps {v['mean_flat']:.3f}  "
                  f"B2 M2 sweeps {v['mean_B2_M2']:.3f}  ratio {_f(v['ratio'])}  "
                  f"share of the saving {_f(v['share_of_saving'])}  "
                  f"M2 settles in flat after {v['mean_M2_settle_in_flat']:.3f}")
        for g, h in b["B2_M2_sweeps_histogram"].items():
            print(f"      B2's M2 sweeps when {g}: {h}")
        print(f"    traced ratio B2 M2 / {b['flat_reference']} sweeps over the paired evaluations: "
              f"{_f(b['traced_ratio'])} ({b['traced_totals']}); campaign records, same seeds: "
              f"{_f(b['campaign_ratio_same_seeds'])} ({b['campaign_totals_same_seeds']})")
        print("    by design variable (gradient probes; share where M2 binds, B2 M2 / flat sweeps):")
        for var, v in sorted(b["by_variable_paired"].items(), key=lambda kv: kv[1]["M2"] / kv[1]["flat"]):
            print(f"      {var:<40} n {v['n']:>5}  M2 binds {v['M2_binds'] / v['n']:.3f}  "
                  f"ratio {v['M2'] / v['flat']:.3f}")
        print()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    rec = sub.add_parser("records", help="the campaign records' side")
    rec.add_argument("--runs", default=None, help="runs root (default: the experiment's runs/)")
    rec.add_argument("--json", default=None, help="write the full result here")
    tr = sub.add_parser("trace-runs", help="make the traced gate runs and the untraced controls")
    tr.add_argument("--runs", default=None)
    tr.add_argument("--which", nargs="+", default=["controls", "evaluation", "optimisation"],
                    choices=["controls", "evaluation", "optimisation"])
    tr.add_argument("--resume", action="store_true")
    tr.add_argument("--list", action="store_true", help="list the jobs and stop")
    ta = sub.add_parser("trace", help="analyse the traces")
    ta.add_argument("--runs", default=None)
    ta.add_argument("--json", default=None)
    args = parser.parse_args(argv)

    campaign = paper.with_runs(default_campaign(), Path(args.runs) if args.runs else None)
    if args.command == "trace-runs":
        jobs = trace_jobs(campaign)
        for name in args.which:
            print(f"  {name}: {len(jobs[name])} job(s)")
            if args.list:
                for j in jobs[name]:
                    print(f"    {j.phase} {j.arm:<3} {j.config.name:<22} seed{j.seed:03d} -> {j.outdir}")
        if args.list:
            return 0
        summary = run_traces(campaign, which=args.which, resume=args.resume)
        failed = any(set(s["statuses"]) - {"ok"} for s in summary.values())
        return 1 if failed else 0
    if args.command == "trace":
        ev_runs = _load_runs(campaign, "A")
        ev_ok = sum(
            1 for r in ev_runs.values()
            if r["checks"]["lines_equal_evaluations"] and r["checks"]["sweeps_sum_to_record"]
            and not r["checks"]["reproduces_campaign"]["differing"]
        )
        result = {
            "runs_dir": str(campaign.runs_dir),
            "controls": controls(campaign),
            "evaluation": evaluation_trace(campaign),
            "evaluation_checks": {"n": len(ev_runs), "ok": ev_ok},
            "optimisation": optimisation_trace(campaign),
        }
        print_trace(result)
        if args.json:
            Path(args.json).write_text(json.dumps(result, indent=1, default=str))
        return 0
    if args.command == "records":
        result = {
            "runs_dir": str(campaign.runs_dir),
            "optimisation": optimisation(campaign),
            "evaluation": evaluation(campaign),
        }
        print_records(result)
        if args.json:
            Path(args.json).write_text(json.dumps(result, indent=1, default=str))
        failed = any(b["paper_reconciliation_mismatches"] for b in result["optimisation"])
        return 3 if failed else 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
