#!/usr/bin/env python
"""Cost versus **achieved** accuracy, per arm, per deck.  Fix 1.

The objection this answers
--------------------------

§6.1 of the results report: the blocked arrangement solves each block to
τ = 1e-6 against inputs that are about to change, and the flat arrangement,
having no inner loop, never pays that.  The exit audit shows the blocked arm
terminating roughly **10⁵ times more converged** than the control at the same
nominal setting.  It did more work *and* got more accuracy, and only the work
was in the ratio.  So "+46.8 %" was never a like-for-like comparison, and the
report correctly said "at most".

**This module replaces "at most" with a measurement**, and it does it by
building a curve rather than hunting for a single matched point.  Each arm is
run across a ladder of tolerances; each run gives one ``(achieved accuracy,
cost)`` pair; the arms are then compared at **equal achieved accuracy** by
interpolating along those curves.

What "achieved accuracy" is, and why not the objective
------------------------------------------------------

The **exit audit's global residual**: after an arm terminates, one further full
sweep of the complete model set is run and the same scaled coupling-state
residual is evaluated, for every arm at every setting, on one map.  It measures
what the arm actually delivered, not what it was asked for.  Summarised per
deck as the **p90 over design points**, with p50 and the max reported beside
it, because a single straggler and five hundred movers are different things
and ``max`` alone cannot tell them apart.

It is deliberately *not* the objective.  §4.3 already records that on
``large_tokamak_nof`` the objective is ``0.2 × rmajor`` and ``rmajor`` **is a
design variable**, so that deck's objective cannot move with τ at all and its
zeros are structural rather than evidence.  Plan §4.1e extends the same problem
to ``low_aspect_ratio_DEMO`` under the lift, whose figure of merit is the pulse
length --- which the lift turns into a design variable too.  With
``large_tokamak_eval`` dropped, an objective-movement measure would be
degenerate on two of the three remaining decks in the variant.  The
coupling-state residual is what every arm is actually converging, so it is what
the comparison uses.

The interpolation, stated
--------------------------

Both quantities are positive and span decades, so the curve is fitted and read
in **log-log space**, linearly between the two bracketing rungs::

    log10(cost) = log10(c_i) + (log10(c_j) - log10(c_i))
                  * (log10(a) - log10(a_i)) / (log10(a_j) - log10(a_i))

A target accuracy outside a curve's measured range is **not** extrapolated: it
is reported as out of range, with the range, and no number is produced.  That
is the whole discipline here --- the failure of the original comparison was a
number quoted past the condition that bounded it (trap T11).

Where an arm's ladder is non-monotone --- cost rising as accuracy loosens ---
the rung is kept and flagged.  It is a measurement about the arm, not noise to
be smoothed.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from accounting import net_model_evaluations  # noqa: E402


def _pct(vals, p):
    v = sorted(vals)
    if not v:
        return None
    if len(v) == 1:
        return v[0]
    i = p * (len(v) - 1)
    lo, hi = int(i), min(int(i) + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (i - lo)


def rung(path: Path, arm: str) -> dict | None:
    """One ladder rung: what it cost, and what accuracy it actually reached.

    The population is the design points **this rung converged**, and the count
    is stated: a rung that dropped points is not comparable to one that did
    not, and the drop census comes before the ratio.
    """
    res = json.loads(Path(path).read_text())
    pts = res["points"]
    conv = [p for p in pts if p["arms"].get(arm, {}).get("converged")]
    if not conv:
        return None
    audits = [p["arms"][arm]["audit"]["max"] for p in conv
              if "audit" in p["arms"][arm]]
    cost = sum(net_model_evaluations(p["arms"][arm]) for p in conv)
    return {
        "path": str(path),
        "scenario": res["scenario"],
        "arm": arm,
        "label": res.get("label"),
        "tau": res["tau"],
        "inner_tau": res.get("inner_tau"),
        "inner_tau_explicit": res.get("inner_tau_explicit"),
        "hoist": res.get("hoist"),
        "spec_mode": res.get("spec_mode"),
        "scale_floor": res.get("scale_floor"),
        "n_points": len(pts),
        "n_converged": len(conv),
        "n_dropped": len(pts) - len(conv),
        "net_model_evaluations": cost,
        "mean_model_evaluations": cost / len(conv),
        "achieved_residual_p50": _pct(audits, 0.50),
        "achieved_residual_p90": _pct(audits, 0.90),
        "achieved_residual_max": max(audits) if audits else None,
        "n_audits": len(audits),
        "mean_sweeps": sum(p["arms"][arm]["sweeps"] for p in conv) / len(conv),
    }


#: The accuracy statistic the curves are read on.  p90 rather than max, for the
#: reason in the module docstring; changing it changes every number here, so it
#: is a named constant and is reported with every result.
ACCURACY_STAT = "achieved_residual_p90"


def curve(rungs, *, stat: str = ACCURACY_STAT) -> dict:
    """One arm's cost-versus-achieved-accuracy curve on one deck.

    Rungs whose accuracy statistic is zero are **excluded from the fit and
    named**: log-log cannot represent a zero residual, and a rung that reached
    bit-exactness is not on the same continuum as one that did not.
    """
    usable, zeros = [], []
    for r in rungs:
        a = r.get(stat)
        if a is None:
            continue
        (zeros if a <= 0 else usable).append(r)
    usable.sort(key=lambda r: r[stat])
    return {
        "stat": stat,
        "n_rungs": len(rungs),
        "n_usable": len(usable),
        "rungs_at_zero_residual": [r["label"] for r in zeros],
        "range": (
            {"min": usable[0][stat], "max": usable[-1][stat]}
            if usable else None
        ),
        "points": [
            {"label": r["label"], "tau": r["tau"], "inner_tau": r["inner_tau"],
             "accuracy": r[stat], "cost": r["net_model_evaluations"],
             "n_converged": r["n_converged"], "n_dropped": r["n_dropped"],
             "mean_sweeps": r["mean_sweeps"]}
            for r in usable
        ],
        "monotone_in_cost": all(
            usable[i]["net_model_evaluations"]
            >= usable[i + 1]["net_model_evaluations"]
            for i in range(len(usable) - 1)
        ),
    }


def cost_at(curve_rec: dict, accuracy: float) -> dict:
    """Interpolated cost at a target achieved accuracy.  Never extrapolated."""
    pts = curve_rec["points"]
    if not pts:
        return {"status": "NO CURVE", "cost": None}
    lo, hi = pts[0]["accuracy"], pts[-1]["accuracy"]
    if accuracy <= 0:
        return {"status": "TARGET IS ZERO -- log-log cannot represent it",
                "cost": None, "range": [lo, hi]}
    if not (lo <= accuracy <= hi):
        return {
            "status": "OUT OF MEASURED RANGE -- not extrapolated",
            "cost": None,
            "range": [lo, hi],
            "target": accuracy,
        }
    for i in range(len(pts) - 1):
        a0, a1 = pts[i]["accuracy"], pts[i + 1]["accuracy"]
        if a0 <= accuracy <= a1:
            c0, c1 = pts[i]["cost"], pts[i + 1]["cost"]
            if a1 == a0:
                return {"status": "OK", "cost": float(c0), "bracket":
                        [pts[i]["label"], pts[i + 1]["label"]],
                        "interpolation": "duplicate accuracy; lower rung used"}
            f = (math.log10(accuracy) - math.log10(a0)) / (
                math.log10(a1) - math.log10(a0)
            )
            c = 10 ** (
                math.log10(c0) + f * (math.log10(c1) - math.log10(c0))
            )
            return {
                "status": "OK",
                "cost": c,
                "bracket": [pts[i]["label"], pts[i + 1]["label"]],
                "bracket_accuracy": [a0, a1],
                "bracket_cost": [c0, c1],
                "fraction": f,
                "interpolation": "linear in log10(cost) vs log10(accuracy)",
            }
    return {"status": "NO BRACKET", "cost": None}


def compare(flat_curve: dict, block_curve: dict) -> dict:
    """The block arm's cost against the flat arm's, at equal achieved accuracy.

    Evaluated at **every accuracy the flat arm actually reached** that also
    lies inside the block arm's measured range.  Reporting it at every rung
    rather than at one "matched point" is deliberate: a single point invites
    the reader to treat one interpolation as the answer, and the honest object
    is the pair of curves.
    """
    rows = []
    for p in flat_curve["points"]:
        b = cost_at(block_curve, p["accuracy"])
        rows.append({
            "accuracy": p["accuracy"],
            "flat_label": p["label"],
            "flat_cost": p["cost"],
            "block_cost": b.get("cost"),
            "status": b["status"],
            "bracket": b.get("bracket"),
            "ratio_block_over_flat": (
                b["cost"] / p["cost"] if b.get("cost") and p["cost"] else None
            ),
            "change_pct": (
                100.0 * (b["cost"] / p["cost"] - 1.0)
                if b.get("cost") and p["cost"] else None
            ),
        })
    usable = [r for r in rows if r["ratio_block_over_flat"] is not None]
    return {
        "rows": rows,
        "n_matched_points": len(usable),
        "n_out_of_range": sum(1 for r in rows if r["status"].startswith("OUT")),
        "flat_range": flat_curve["range"],
        "block_range": block_curve["range"],
        "ratio_min": min((r["ratio_block_over_flat"] for r in usable),
                         default=None),
        "ratio_max": max((r["ratio_block_over_flat"] for r in usable),
                         default=None),
    }


def build(runs_root: Path, scenarios) -> dict:
    """Assemble both arms' curves and the matched-accuracy comparison."""
    out = {
        "accuracy_statistic": ACCURACY_STAT,
        "accuracy_definition": (
            "the exit audit's global scaled coupling-state residual, taken one "
            "further full sweep of the complete model set past termination, "
            "identical across arms; p90 over the design points the rung "
            "converged"
        ),
        "cost_definition": (
            "net model evaluations = in-loop calls + hoisted tails "
            "(fixedpoint/accounting.py); the audit sweep is never charged"
        ),
        "per_scenario": {},
    }
    for s in scenarios:
        d = runs_root / s
        flat = [r for r in
                (rung(p / "result.json", "A0")
                 for p in sorted(d.glob("replay_acc_flat_*")))
                if r]
        block = [r for r in
                 (rung(p / "result.json", "A1")
                  for p in sorted(d.glob("replay_acc_block_*")))
                 if r]
        if not flat or not block:
            out["per_scenario"][s] = {"status": "INCOMPLETE",
                                      "n_flat": len(flat), "n_block": len(block)}
            continue
        fc, bc = curve(flat), curve(block)
        # Every rung of both arms must be over the same design-point set, or
        # the costs are not comparable.  Checked, not assumed.
        ns = {r["n_points"] for r in flat + block}
        drops = {r["label"]: r["n_dropped"] for r in flat + block
                 if r["n_dropped"]}
        out["per_scenario"][s] = {
            "status": "OK",
            "design_point_counts": sorted(ns),
            "same_population": len(ns) == 1,
            "rungs_that_dropped_points": drops,
            "flat_rungs": flat,
            "block_rungs": block,
            "flat_curve": fc,
            "block_curve": bc,
            "matched_accuracy": compare(fc, bc),
        }
    return out


def render(rec: dict) -> str:
    L = []
    L.append("COST AT MATCHED ACHIEVED ACCURACY -- block arm A1 vs flat arm A0")
    L.append(f"accuracy = {rec['accuracy_definition']}")
    L.append(f"cost     = {rec['cost_definition']}")
    for s, d in rec["per_scenario"].items():
        L.append("")
        L.append(f"=== {s}")
        if d["status"] != "OK":
            L.append(f"    {d['status']}: {d}")
            continue
        L.append(f"    design points per rung: {d['design_point_counts']}"
                 f"  same population: {d['same_population']}"
                 f"  rungs dropping points: {d['rungs_that_dropped_points'] or 'none'}")
        for nm, c in (("flat A0", d["flat_curve"]), ("block A1", d["block_curve"])):
            L.append(f"    -- {nm} curve ({c['n_usable']} usable of "
                     f"{c['n_rungs']} rungs"
                     + (f"; at zero residual: {c['rungs_at_zero_residual']}"
                        if c["rungs_at_zero_residual"] else "") + ")")
            L.append(f"       {'label':26s} {'achieved p90':>13s} "
                     f"{'model evals':>12s} {'sweeps':>7s}")
            for p in c["points"]:
                L.append(f"       {p['label']:26s} {p['accuracy']:13.3e} "
                         f"{p['cost']:12d} {p['mean_sweeps']:7.3f}")
        m = d["matched_accuracy"]
        L.append(f"    -- matched: {m['n_matched_points']} of "
                 f"{len(m['rows'])} flat rungs inside the block arm's range "
                 f"{m['block_range']}")
        L.append(f"       {'achieved p90':>13s} {'flat cost':>10s} "
                 f"{'block cost':>11s} {'A1/A0':>7s}  bracket / status")
        for r in m["rows"]:
            if r["ratio_block_over_flat"] is None:
                L.append(f"       {r['accuracy']:13.3e} {r['flat_cost']:10d} "
                         f"{'--':>11s} {'--':>7s}  {r['status']}")
            else:
                L.append(f"       {r['accuracy']:13.3e} {r['flat_cost']:10d} "
                         f"{r['block_cost']:11.0f} "
                         f"{r['ratio_block_over_flat']:7.3f}  {r['bracket']}")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=None)
    ap.add_argument("--scenarios", nargs="*", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    runs = Path(args.runs) if args.runs else (
        HERE.parent / "idf_probe" / "runs" / "a26"
    )
    import run_a26

    rec = build(runs, args.scenarios or run_a26.SCENARIOS)
    if args.out:
        Path(args.out).write_text(json.dumps(rec, indent=2))
    print(render(rec))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
