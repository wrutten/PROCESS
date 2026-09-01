#!/usr/bin/env python
"""A13 (feedforward-hoist) gate checker.

Three gates, all against the arm ``parent`` -- a ``git archive`` extraction of
this branch's parent commit.

**Gate 1, switch-neutrality** -- ``default`` vs ``parent``.  With
``PROCESS_ARCH_HOIST`` unset, the variant point must reproduce the straight-line
calls it replaced, bit for bit.  Reported per scenario, never pooled.

**Gate 2, correctness with the hook on** -- ``hoisted`` vs ``parent``.  The
project's stated acceptance quantity is ``norm_objf`` plus a feasibility audit
at matched final accuracy, never the iteration variables (decision D6).  Those
are reported explicitly.  The whole-MFILE bit comparison is reported *beside*
them, because if the feed-forward property holds exactly then deferring the
tail cannot change any number at all -- and a difference, if there is one,
names the field the dependency analysis missed.

**Gate 3, the saving** -- a count of model evaluations and of sweeps, from the
node census, ``hoisted`` against ``default``.  Not a timing.

The bit comparator is imported unchanged from ``compare_a3.py``, including its
MFILE line parser: A3's own sensitivity check found that anchoring on the first
``(...)`` in a line silently dropped about a thousand floats per scenario, and
reusing the fixed parser is safer than writing a fourth one.

Every count printed is a count of things actually compared, with its
denominator beside it.  An empty comparison set is reported as ``EMPTY``, never
as a pass.

Usage:  python compare_a13.py --runs runs/a13
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from compare_a3 import compare_pair, load  # noqa: E402

SCENARIOS = [
    "large_tokamak_nof",
    "low_aspect_ratio_DEMO",
    "st_regression",
    "large_tokamak_eval",
]

#: MFILE keys that make up the feasibility audit.  ``ifail`` is the solver's
#: own verdict; ``sqsumsq`` is the sum of squares of the constraint residuals
#: at the returned point, i.e. how far off the feasible manifold it sits.
AUDIT_KEYS = ("ifail", "sqsumsq", "norm_objf")


def acceptance(runs: Path, scenario: str, ref: str, arm: str) -> dict:
    """Decision-D6 acceptance: norm_objf, feasibility, ifail.  Never itvars."""
    mr, ma = load(runs, scenario, ref), load(runs, scenario, arm)
    if mr is None or ma is None:
        return {"status": "MISSING"}
    er, ea = mr.get("exact") or {}, ma.get("exact") or {}
    fr, fa = mr.get("mfile") or {}, ma.get("mfile") or {}
    rows = {}
    for key in ("norm_objf", "sqsumsq"):
        rows[key] = {
            ref: er.get(key),
            arm: ea.get(key),
            "identical": er.get(key) == ea.get(key),
        }
    rows["conf_l2"] = {
        ref: er.get("conf_l2"),
        arm: ea.get("conf_l2"),
        "identical": er.get("conf_l2") == ea.get("conf_l2"),
    }
    rows["ifail"] = {
        ref: fr.get("ifail"),
        arm: fa.get("ifail"),
        "identical": fr.get("ifail") == fa.get("ifail"),
    }
    compared = list(rows)
    ok = all(rows[k]["identical"] for k in compared)
    return {
        "status": ("PASS" if ok else "FAIL") if compared else "EMPTY",
        "quantities_compared": len(compared),
        "quantities": rows,
        "note": (
            "iteration variables are deliberately NOT gated on (decision D6); "
            "they are reported by the bit comparison beside this table but are "
            "not an acceptance quantity"
        ),
        "hoist_tail_resolved": {
            ref: mr.get("arch_hoist_tail_resolved"),
            arm: ma.get("arch_hoist_tail_resolved"),
        },
        "i_figure_merit": {ref: mr.get("i_figure_merit"), arm: ma.get("i_figure_merit")},
    }


def sweeps(runs: Path, scenario: str) -> dict:
    out = {}
    for arm in ("parent_probe", "default_probe", "hoisted_probe"):
        m = load(runs, scenario, arm)
        if m is None:
            out[arm] = None
            continue
        p = m.get("probe") or {}
        out[arm] = {
            "sweeps_total": p.get("sweeps_total"),
            "call_models_total": p.get("call_models_total"),
            "n_model_calls_builtin": m.get("n_model_calls"),
            "n_solver_iterations": m.get("n_solver_iterations"),
            "ifail": (m.get("mfile") or {}).get("ifail"),
            "arch_hoist_name": m.get("arch_hoist_name"),
        }
    vals = [v["sweeps_total"] for v in out.values() if v]
    out["sweeps_identical_across_arms"] = len(set(vals)) == 1 and len(vals) == 3
    return out


def _census(runs: Path, scenario: str, arm: str) -> dict | None:
    p = runs / scenario / f"census_{arm}" / "node_census.json"
    return json.loads(p.read_text()) if p.exists() else None


def saving(runs: Path, scenario: str) -> dict:
    """Gate 3: model evaluations and sweeps, hoisted against default."""
    out: dict = {}
    for arm in ("parent", "default", "hoisted"):
        c = _census(runs, scenario, arm)
        out[arm] = (
            None
            if c is None
            else {
                "status": c["status"],
                "n_sweeps": c["n_sweeps"],
                "n_hoisted_tail_runs": c["n_hoisted_tail_runs"],
                "n_evals_in_loop": c["n_evals_in_loop"],
                "n_evals_hoisted": c["n_evals_hoisted"],
                "n_evals_total": c["n_evals_total"],
                "n_calls_first_sweep": c["n_calls_first_sweep"],
                "n_outside_any_window": c["n_outside_any_window"],
                "arch_hoist_name": c.get("arch_hoist_name"),
                "arch_hoist_tail_resolved": c.get("arch_hoist_tail_resolved"),
                "evals_hoisted_by_node": c.get("evals_hoisted_by_node"),
            }
        )
    d, h, p = out["default"], out["hoisted"], out["parent"]
    if d and h:
        denom = d["n_evals_total"]
        out["denominator_model_evaluations_default_arm"] = denom
        out["model_evaluations_removed"] = denom - h["n_evals_total"]
        out["saving_fraction_of_model_evaluations"] = (
            (denom - h["n_evals_total"]) / denom if denom else None
        )
        out["sweeps_default"] = d["n_sweeps"]
        out["sweeps_hoisted"] = h["n_sweeps"]
        out["sweeps_change"] = h["n_sweeps"] - d["n_sweeps"]
        out["in_loop_evals_removed"] = d["n_evals_in_loop"] - h["n_evals_in_loop"]
        out["evals_moved_to_tail"] = h["n_evals_hoisted"]
    if p and d:
        out["parent_vs_default_evals_identical"] = (
            p["n_evals_total"] == d["n_evals_total"]
            and p["n_sweeps"] == d["n_sweeps"]
        )
    return out


def writeset(runs: Path, scenario: str) -> dict:
    p = runs / scenario / "writeset" / "tail_writeset.json"
    if not p.exists():
        return {"status": "MISSING"}
    w = json.loads(p.read_text())
    per = {
        n: {
            "n_calls_depth0_in_sweep": d["n_calls_depth0_in_sweep"],
            "n_fields_written": d["n_fields_written"],
            "read_by_objectives": d["read_by_objectives"],
            "read_by_constraints": d["read_by_constraints"],
        }
        for n, d in w.get("per_node", {}).items()
    }
    return {
        "status": w.get("status"),
        "i_figure_merit": w.get("i_figure_merit"),
        "n_sweeps": w.get("n_sweeps"),
        "n_sweeps_fingerprinted": w.get("n_sweeps_fingerprinted"),
        "n_fields_in_snapshot": w.get("n_fields_in_snapshot"),
        "per_node": per,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=str(HERE / "runs" / "a13"))
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    args = ap.parse_args()
    runs = Path(args.runs).resolve()

    result = {
        "gate1_neutrality_default_vs_parent": {
            s: compare_pair(runs, s, "parent", "default") for s in args.scenarios
        },
        "gate2_acceptance_hoisted_vs_parent": {
            s: acceptance(runs, s, "parent", "hoisted") for s in args.scenarios
        },
        "gate2_bitwise_hoisted_vs_parent": {
            s: compare_pair(runs, s, "parent", "hoisted") for s in args.scenarios
        },
        "gate3_saving": {s: saving(runs, s) for s in args.scenarios},
        "sweeps": {s: sweeps(runs, s) for s in args.scenarios},
        "tail_writeset": {s: writeset(runs, s) for s in args.scenarios},
    }
    (runs / "_gates_a13.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
