#!/usr/bin/env python
"""A26's gates: what must not have changed, and proof each can still fail.

Three of A26's fixes touch code every previously merged arm ran through --- the
subset-aware coupling-state read, the restructured residual, and the
``inner_tau`` parameter.  All three are supposed to be **inert** at A18's
settings.  "Supposed to be" is not a measurement, so this module compares a
fresh replay against A18's recorded artifacts **bit for bit, with no tolerance
anywhere**, and then perturbs the comparison to show it can fail.

What is compared, per design point and per arm
----------------------------------------------

Everything the arm recorded that is not new in A26: pass counts, model
evaluation counts, module sweeps, the converged flag, which cap was hit, the
inner-solve counts per block, the **full residual trace at every pass**, the
named moved constants, the DSM cross-check sweep, and every field of the exit
audit --- floats compared as exact ``repr``, not with ``==`` on a rounded
value.  Fields A26 added (``inner_tau``, ``rep``, ``wall_s``, ``cpu_s``,
``pre_predicate_tail_node_calls``) are excluded **by name and reported**, so
the exclusion list is visible rather than implied.

Why the sensitivity check is not optional
-----------------------------------------

Protocol §12, and this project's own history: a gate whose failure mode has
never been exercised is an assertion.  A read that silently returned a stale
value would reproduce every count and every converged flag --- the residual
trace is the only place it would show --- so the perturbation is applied to a
residual trace value and to an exit-audit float, i.e. to the quantities the
comparison would have to be watching for it to be worth anything.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

#: Result keys A26 added.  Excluded from the comparison **by name**: an
#: A18 artifact does not have them, and a comparison that silently ignored
#: unknown keys would also ignore a key that vanished.
NEW_IN_A26 = (
    "inner_tau",
    "rep",
    "wall_s",
    "cpu_s",
    "reps_wall_s",
    "reps_cpu_s",
    "pre_predicate_tail_node_calls",
)


def _canon(v):
    """Exact, hashable rendering of a recorded value.

    Floats go through ``repr``, which round-trips in Python 3, so two floats
    compare equal here if and only if they are the same double.  No tolerance
    is applied anywhere and none may be added.
    """
    if isinstance(v, float):
        return ("f", repr(v))
    if isinstance(v, dict):
        return ("d", tuple((k, _canon(v[k])) for k in sorted(v)))
    if isinstance(v, (list, tuple)):
        return ("l", tuple(_canon(x) for x in v))
    return ("v", v)


def compare_arm(old: dict, new: dict) -> list:
    """Differing keys between one arm's old and new record."""
    keys = (set(old) | set(new)) - set(NEW_IN_A26)
    return sorted(k for k in keys if _canon(old.get(k)) != _canon(new.get(k)))


def compare_results(old_path: Path, new_path: Path, arms=None) -> dict:
    old = json.loads(Path(old_path).read_text())
    new = json.loads(Path(new_path).read_text())
    arms = list(arms or old["arms"])
    o_by = {p["call_index"]: p for p in old["points"]}
    n_by = {p["call_index"]: p for p in new["points"]}
    common = sorted(set(o_by) & set(n_by))
    rows = []
    n_cmp = 0
    for ci in common:
        for a in arms:
            oa = o_by[ci]["arms"].get(a)
            na = n_by[ci]["arms"].get(a)
            if oa is None or na is None:
                rows.append({"call_index": ci, "arm": a,
                             "diff": ["arm absent on one side"]})
                continue
            n_cmp += len(
                (set(oa) | set(na)) - set(NEW_IN_A26)
            )
            d = compare_arm(oa, na)
            if d:
                rows.append({"call_index": ci, "arm": a, "diff": d,
                             "old": {k: oa.get(k) for k in d},
                             "new": {k: na.get(k) for k in d}})
    return {
        "old": str(old_path),
        "new": str(new_path),
        "arms": arms,
        "n_points_old": len(o_by),
        "n_points_new": len(n_by),
        "n_points_compared": len(common),
        "points_only_in_old": sorted(set(o_by) - set(n_by))[:20],
        "points_only_in_new": sorted(set(n_by) - set(o_by))[:20],
        "n_arm_records_compared": len(common) * len(arms),
        "n_record_keys_compared": n_cmp,
        "keys_excluded_by_name": list(NEW_IN_A26),
        "n_differing_arm_records": len(rows),
        "differences": rows[:20],
        "status": (
            "FAIL -- point sets differ"
            if set(o_by) != set(n_by)
            else ("PASS" if not rows and common else
                  ("EMPTY -- nothing compared" if not common else "FAIL"))
        ),
    }


# --------------------------------------------------------------------------
# Sensitivity: show the comparison capable of failing
# --------------------------------------------------------------------------


def _nudge(x: float) -> float:
    """One unit in the last place, upward."""
    import math

    return math.nextafter(x, math.inf) if x == x else x


def sensitivity(old_path: Path, new_path: Path, arms=None) -> dict:
    """Perturb the *new* artifact and confirm each perturbation is caught.

    Four perturbations, each aimed at a quantity a defect would move and a
    weak comparator would miss:

    1. one model-evaluation count, +1 --- the headline unit;
    2. one residual-trace ``max``, one ULP --- what a stale read would move,
       and the only place it would show;
    3. one exit-audit ``max``, one ULP --- matched final accuracy;
    4. one ``converged`` flag, flipped --- the drop census.

    Each is applied to a deep copy, compared, and then discarded.  A
    perturbation the comparison does not catch is a defect in the comparison.
    """
    import copy

    new = json.loads(Path(new_path).read_text())
    arms = list(arms or new["arms"])
    tmp = Path(new_path).with_suffix(".sensitivity.json")
    out = []

    def run_case(name, mutate):
        d = copy.deepcopy(new)
        applied = mutate(d)
        if not applied:
            out.append({"case": name, "status": "NOT APPLIED -- no target",
                        "caught": None})
            return
        tmp.write_text(json.dumps(d))
        r = compare_results(old_path, tmp, arms)
        out.append({
            "case": name,
            "target": applied,
            "caught": r["status"] != "PASS",
            "n_differing_arm_records": r["n_differing_arm_records"],
        })

    def m_count(d):
        for p in d["points"]:
            for a in arms:
                if "node_calls" in p["arms"].get(a, {}):
                    p["arms"][a]["node_calls"] += 1
                    return f"{a}@{p['call_index']}.node_calls +1"
        return None

    def m_trace(d):
        for p in d["points"]:
            for a in arms:
                tr = p["arms"].get(a, {}).get("residual_trace") or []
                for step in tr:
                    if isinstance(step, dict) and isinstance(
                        step.get("max"), float
                    ) and step["max"] > 0:
                        step["max"] = _nudge(step["max"])
                        return f"{a}@{p['call_index']}.residual_trace.max +1ulp"
        return None

    def m_audit(d):
        for p in d["points"]:
            for a in arms:
                au = p["arms"].get(a, {}).get("audit") or {}
                if isinstance(au.get("objf"), float):
                    au["objf"] = _nudge(au["objf"])
                    return f"{a}@{p['call_index']}.audit.objf +1ulp"
        return None

    def m_flag(d):
        for p in d["points"]:
            for a in arms:
                if "converged" in p["arms"].get(a, {}):
                    p["arms"][a]["converged"] = not p["arms"][a]["converged"]
                    return f"{a}@{p['call_index']}.converged flipped"
        return None

    run_case("model-evaluation count +1", m_count)
    run_case("residual trace max +1 ULP", m_trace)
    run_case("exit-audit objf +1 ULP", m_audit)
    run_case("converged flag flipped", m_flag)
    tmp.unlink(missing_ok=True)
    applied = [c for c in out if c["caught"] is not None]
    return {
        "cases": out,
        "n_applied": len(applied),
        "n_caught": sum(1 for c in applied if c["caught"]),
        "status": (
            "PASS" if applied and all(c["caught"] for c in applied)
            else "FAIL -- the comparison cannot detect a change it must detect"
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--arms", nargs="*", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    rec = {
        "reproduction": compare_results(Path(args.old), Path(args.new),
                                        args.arms),
        "sensitivity": sensitivity(Path(args.old), Path(args.new), args.arms),
    }
    rec["status"] = (
        "PASS"
        if rec["reproduction"]["status"] == "PASS"
        and rec["sensitivity"]["status"] == "PASS"
        else "FAIL"
    )
    if args.out:
        Path(args.out).write_text(json.dumps(rec, indent=2))
    json.dump({k: (v if k == "status" else
                   {kk: vv for kk, vv in v.items() if kk != "differences"})
               for k, v in rec.items()}, sys.stdout, indent=2)
    print()
    return 0 if rec["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
