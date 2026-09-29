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

Usage::

    python block_binding.py records [--runs <runs root>] [--json out.json]
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    rec = sub.add_parser("records", help="the campaign records' side")
    rec.add_argument("--runs", default=None, help="runs root (default: the experiment's runs/)")
    rec.add_argument("--json", default=None, help="write the full result here")
    args = parser.parse_args(argv)

    campaign = paper.with_runs(default_campaign(), Path(args.runs) if args.runs else None)
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
