#!/usr/bin/env python
"""A25's H5 analysis: the delta calibration, the drop census, the distributions.

Everything here is a **count**.  No conclusion rests on a timing (issue I-10):
the cost unit is model node calls -- individual model ``run()`` invocations,
Phase A's and A22's unit -- and the robustness unit is ``ifail`` outcomes.
Wall clock is not read by any function in this file.

Order of reporting is fixed and is not a style choice
-----------------------------------------------------
**Robustness first, then the drop census, then any ratio.**  An architecture
that is cheaper on the starts it solves and fails on more of them has not won
(plan section 2.5), and a ratio over a quietly smaller population is trap T11,
which this project has published three times.  ``gates.cost_comparison``
structurally refuses to produce a ratio without being handed a census, and this
module never calls it without one.

Decisions this implements
-------------------------
``D15(a)``  delta is *calibrated*: the largest of {1 %, 5 %, 10 %} that keeps
            ``ifail = 1`` on most baseline starts, decided per deck and
            reported per deck.
``D15(c)``  a start whose ``norm_objf`` differs beyond tolerance leaves the cost
            comparison and is counted as a **robustness finding**, never
            silently dropped.
``D15(d)``  a per-module solve that fails to converge raises, so it arrives here
            as ``status = crashed`` and counts as a failed start.
``I-12``    net electric power at the returned point is recorded per start and
            the count of degenerate starts is reported beside every cost figure.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import gates as G  # noqa: E402
from a25_gates import OBJF_RTOL  # noqa: E402

SCENARIOS = G.SCENARIOS


# ---------------------------------------------------------------------------
# D15(a): the calibration
# ---------------------------------------------------------------------------


def calibration(runs: Path, scenarios, deltas) -> dict:
    """Which perturbation size the baseline still solves, per deck.

    Reported in full, not just the choice: the rule is "the largest delta that
    keeps ``ifail = 1`` on most starts", and "most" needs the whole table to be
    checkable.
    """
    per: dict = {}
    for s in scenarios:
        rows = {}
        for d in deltas:
            tag = f"delta{int(round(d * 1000)):04d}"
            starts = G.collect_starts(runs, s, tag)
            cen = G.ifail_census(starts)
            rows[f"{d:g}"] = {
                "delta": d,
                "n_starts": cen["n_starts"],
                "n_ifail_1": cen["n_ifail_1"],
                "n_not_ifail_1": cen["n_not_ifail_1"],
                "n_crashed": cen["n_crashed"],
                "ifail_histogram": cen["ifail_histogram"],
                "fraction_ifail_1": (
                    cen["n_ifail_1"] / cen["n_starts"] if cen["n_starts"] else None
                ),
                "keeps_most": (
                    cen["n_starts"] > 0
                    and cen["n_ifail_1"] > cen["n_starts"] / 2
                ),
            }
        ok = [r for r in rows.values() if r["keeps_most"]]
        per[s] = {
            "per_delta": rows,
            "largest_delta_keeping_most": (
                max((r["delta"] for r in ok), default=None)
            ),
            "rule": (
                "D15(a): the largest delta in {1 %, 5 %, 10 %} that keeps "
                "ifail = 1 on more than half the baseline starts"
            ),
        }
    chosen = [
        per[s]["largest_delta_keeping_most"]
        for s in scenarios
        if per[s]["largest_delta_keeping_most"] is not None
    ]
    return {
        "deltas_tried": list(deltas),
        "arm": "baseline only (D15(a): calibration is on the baseline)",
        "per_scenario": per,
        "campaign_delta": min(chosen) if chosen else None,
        "campaign_delta_rule": (
            "the smallest of the per-deck choices, so that one delta runs every "
            "deck and no deck is perturbed beyond what it was shown to survive. "
            "Stated rather than tuned: a per-deck delta would make the four "
            "campaigns non-comparable in perturbation size, which is the one "
            "thing the paired design needs held equal."
        ),
    }


# ---------------------------------------------------------------------------
# H5
# ---------------------------------------------------------------------------


def _cost(m: dict):
    """The cost of one start: model node calls in the solve phase."""
    return m.get("node_calls_solve_phase")


def _quart(xs):
    xs = sorted(xs)
    if not xs:
        return None
    n = len(xs)
    return {
        "n": n,
        "min": xs[0],
        "q1": statistics.quantiles(xs, n=4)[0] if n >= 4 else None,
        "median": statistics.median(xs),
        "q3": statistics.quantiles(xs, n=4)[2] if n >= 4 else None,
        "max": xs[-1],
        "mean": statistics.fmean(xs),
    }


def compare(runs: Path, scenario: str, ref: str, arm: str) -> dict:
    starts_by_arm = {
        a: G.collect_starts(runs, scenario, a) for a in (ref, arm)
    }

    # -- robustness first ------------------------------------------------
    robustness = {
        a: G.ifail_census(starts_by_arm[a]) for a in (ref, arm)
    }

    # -- paired robustness: WHICH starts each arm solves -----------------
    # A per-arm success count answers "how many", which is not the question
    # when the starts are paired.  "The variant solves 11 and the baseline 12"
    # is consistent with the variant solving eleven the baseline cannot; the
    # 2x2 table below is the one that says whether an arm is actually less
    # robust, and it names the starts so a disagreement can be looked at.
    ok = {
        a: {s["start"] for s in starts_by_arm[a]
            if s.get("status") == "ok" and G._ifail(s) == 1}
        for a in (ref, arm)
    }
    allstarts = {s["start"] for a in (ref, arm) for s in starts_by_arm[a]}
    paired_robustness = {
        "denominator_starts_offered": len(allstarts),
        "n_both_solve": len(ok[ref] & ok[arm]),
        "n_only_" + ref: len(ok[ref] - ok[arm]),
        "n_only_" + arm: len(ok[arm] - ok[ref]),
        "n_neither": len(allstarts - ok[ref] - ok[arm]),
        "starts_only_" + ref: sorted(ok[ref] - ok[arm]),
        "starts_only_" + arm: sorted(ok[arm] - ok[ref]),
        "note": (
            "solved means status ok AND ifail == 1.  Robustness outranks cost "
            "(plan section 2.5): an arm that is cheaper on the starts it "
            "solves and fails on more of them has not won."
        ),
    }

    # -- failure mode, per arm, named ------------------------------------
    def _mode(s):
        if s.get("status") == "ok":
            f = G._ifail(s)
            return "ok" if f == 1 else f"ifail_{f}"
        tb = (s.get("traceback") or "").strip().splitlines()
        if not tb:
            return f"crashed:{s.get('status')}"
        last = tb[-1]
        if "ModuleSolveFailure" in last:
            return "crashed:ModuleSolveFailure"
        return "crashed:" + last.split(":")[0].split(".")[-1]

    failure_modes = {}
    for a in (ref, arm):
        h: dict = {}
        for s in starts_by_arm[a]:
            k = _mode(s)
            h[k] = h.get(k, 0) + 1
        failure_modes[a] = dict(sorted(h.items()))

    # -- then the drop census -------------------------------------------
    census = G.drop_census(starts_by_arm, objf_rtol=OBJF_RTOL)

    # -- only then a ratio ----------------------------------------------
    cost_by_arm = {
        a: {
            s["start"]: _cost(s)
            for s in starts_by_arm[a]
            if _cost(s) is not None
        }
        for a in (ref, arm)
    }
    kept = [n for n, v in census["per_start_verdict"].items() if v == "kept"]
    complete = [
        n for n in kept
        if all(n in cost_by_arm[a] for a in (ref, arm))
    ]
    cost = G.cost_comparison(census, cost_by_arm)

    per_start = {
        n: {a: cost_by_arm[a][n] for a in (ref, arm)} for n in complete
    }
    ratios = [
        per_start[n][arm] / per_start[n][ref]
        for n in complete
        if per_start[n][ref]
    ]
    diffs = [per_start[n][arm] - per_start[n][ref] for n in complete]

    # -- attribution (plan section 2.5 step 4) ---------------------------
    def _get(a, key):
        return {
            s["start"]: s.get(key)
            for s in starts_by_arm[a]
            if s.get(key) is not None
        }

    iters = {a: _get(a, "n_solver_iterations") for a in (ref, arm)}
    nvar = {a: _get(a, "nvar") for a in (ref, arm)}
    it_pairs = [
        (iters[ref][n], iters[arm][n])
        for n in complete
        if n in iters[ref] and n in iters[arm]
    ]

    # -- I-12 -------------------------------------------------------------
    # ``status == "ok"`` is load-bearing here, not defensive.  A crashed run
    # still leaves a partial MFILE, and the parser returns 0 for a key that is
    # not in it -- so counting every arm's rows would have reported **10
    # degenerate entries on large_tokamak_eval**, which are its ten crashed
    # variant runs and not degenerate entries at all.  Found by checking the
    # count against the baseline arm, which had none.
    pnet = {
        a: {
            s["start"]: (s.get("mfile") or {}).get("p_plant_electric_net_mw")
            for s in starts_by_arm[a]
            if s.get("status") == "ok"
        }
        for a in (ref, arm)
    }
    degenerate = sorted({
        n for a in (ref, arm) for n, v in pnet[a].items()
        if v is not None and v <= 0.0
    })
    n_pnet_recorded = {a: len(pnet[a]) for a in (ref, arm)}

    return {
        "scenario": scenario,
        "arms": {"reference": ref, "variant": arm},
        "robustness_reported_first": robustness,
        "paired_robustness": paired_robustness,
        "failure_modes": failure_modes,
        "drop_census_reported_before_any_ratio": census,
        "cost_unit": "model node calls in the solve phase",
        "cost": cost,
        "n_starts_in_distribution": len(complete),
        "denominator_starts_offered": census["denominator_starts_offered"],
        "distribution": {
            a: _quart([per_start[n][a] for n in complete]) for a in (ref, arm)
        },
        "paired_ratio_variant_over_reference": _quart(ratios),
        "paired_difference_variant_minus_reference": _quart(diffs),
        "n_starts_variant_cheaper": sum(1 for d in diffs if d < 0),
        "n_starts_variant_dearer": sum(1 for d in diffs if d > 0),
        "n_starts_equal": sum(1 for d in diffs if d == 0),
        "attribution": {
            "n_solver_iterations": {
                a: _quart([iters[a][n] for n in complete if n in iters[a]])
                for a in (ref, arm)
            },
            "paired_iteration_ratio": _quart(
                [b / a for a, b in it_pairs if a]
            ),
            "nvar": {
                a: sorted({v for v in nvar[a].values()}) for a in (ref, arm)
            },
            "finite_difference_dimension_penalty": {
                "note": (
                    "PROCESS takes central differences, so a gradient costs 2n "
                    "MDA solves; one more design variable is 1/n more work "
                    "against the current cost.  Reported as arithmetic on the "
                    "measured nvar, not as a measurement."
                ),
                "per_arm_nvar": {
                    a: sorted({v for v in nvar[a].values()}) for a in (ref, arm)
                },
            },
        },
        "I12_degenerate_entry": {
            "starts_with_non_positive_p_plant_electric_net_mw": degenerate,
            "n_degenerate": len(degenerate),
            "denominator_completed_runs_with_p_net_recorded": n_pnet_recorded,
            "denominator_starts_offered": census["denominator_starts_offered"],
            "n_kept_but_degenerate": census["n_kept_but_degenerate_entry_I12"],
            "why": (
                "PROCESS's 1990 cost model diverges where net electric power is "
                "not positive, which makes a median-scaled relative test "
                "arbitrarily tight there (issue I-12).  Reported alongside "
                "every cost figure, with its denominator."
            ),
        },
    }


def h5(runs: Path, scenarios, arms) -> dict:
    ref = arms[0]
    out: dict = {
        "cost_unit": "model node calls (individual model run() invocations)",
        "never": "no conclusion rests on a timing; wall clock is not read here",
        "scenarios_reported_separately": list(scenarios),
        "comparisons": {},
    }
    for s in scenarios:
        out["comparisons"][s] = {}
        for a in arms[1:]:
            out["comparisons"][s][f"{ref}_vs_{a}"] = compare(runs, s, ref, a)
        if "variant" in arms and "variant_nohoist" in arms:
            out["comparisons"][s]["hoist_share"] = compare(
                runs, s, "variant_nohoist", "variant"
            )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["calibration", "h5"])
    ap.add_argument("--runs", required=True)
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    ap.add_argument(
        "--arms", nargs="*",
        default=["baseline", "variant", "variant_nohoist"],
    )
    ap.add_argument("--deltas", nargs="*", type=float, default=[0.01, 0.05, 0.10])
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    runs = Path(args.runs).resolve()
    if args.command == "calibration":
        res = calibration(runs, args.scenarios, args.deltas)
        name = "_calibration_a25.json"
    else:
        res = h5(runs, args.scenarios, args.arms)
        name = "_h5_a25.json"
    dest = Path(args.out) if args.out else runs / name
    dest.write_text(json.dumps(res, indent=2, default=str))
    print(f"-> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
