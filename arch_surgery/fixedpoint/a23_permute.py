#!/usr/bin/env python
"""A23 (flat-arm-permutation): does the flat arm's node order matter?

Phase A's headline structural comparison is ``A0`` (flat Gauss-Seidel) against
``A1`` (block Gauss-Seidel), and it is supposed to isolate **the module
grouping**.  It does not, quite.  ``arms.loop_nodes`` builds the flat arm from
the harvested run-time order, which is upstream's ``plasma_geom, build,
physics, ...``; ``arms.build_blocks`` groups the same nodes by module, so when
its blocks are concatenated they run ``plasma_geom, physics, build, ...``.  So
``A0 -> A1`` varied the grouping **and** a sequence permutation together, and
nobody named the second one while Phase A was built or measured.

A3 (build-reorder) has since shown that exact permutation is bit-identical and
sweep-count-identical in the incumbent driver.  That makes it very likely inert
in the flat arm too -- but *very likely* is not a measurement, and block versus
flat is a headline.

What this driver does
---------------------
It replays A18's **existing** harvested design points -- no new PROCESS solve,
no new harvest, no ``process/`` change -- through two flat arms:

``A0``
    ``arms.loop_nodes`` order, exactly as A18 ran it.  This arm exists to be
    compared against A18's recorded ``A0``: it is the reproduction gate, and it
    is also the empirical half of the harvest-reuse licence (see ``run_a23.py``
    for the documentary half).  If the models the replay executes had changed
    since the harvest, this arm would not reproduce.

``A0perm``
    The same flat Gauss-Seidel over the same nodes in **the block arm's order**.
    That order is *derived from* ``arms.build_blocks`` by concatenating its
    blocks -- never hardcoded -- so both arms provably share one definition of
    what the block order is.  The driver asserts the two orders are a
    permutation of one another (same multiset of nodes, same length) before it
    runs anything, so a bug that dropped or duplicated a node cannot masquerade
    as a null result.

Everything is compared **per design point, bit-for-bit, with no tolerance
anywhere**: sweep counts, model-evaluation counts, the converged flag, the
moved-constant list, the residual trace (max, argmax name and above-tau count
at every sweep), and the exit audit (objective and constraint L2/Linf at
termination and after one further sweep).  Decks are never pooled.

Showing the comparator can fail (protocol §12)
----------------------------------------------
``--sensitivity`` adds three checks that must all pass before any zero is
accepted.

1.  A **comparator self-test**: one point's own record is copied and perturbed
    by the smallest amount that should register -- one ULP on each compared
    float, plus one on each compared integer, the converged flag flipped, one
    argmax name changed, one moved-constant name added -- and the comparator
    must flag every one of them.  A field that cannot be perturbed in that
    record is reported as skipped, never counted as caught.
2.  An **arm-level 1-ULP perturbation**: arm ``A0ulp`` is arm ``A0`` with one
    component of the **design vector** advanced by one ULP.  The design vector
    is chosen rather than a state field because ``Sweeper.inject`` re-imposes
    it at the head of every pass, so the nudge cannot be silently overwritten
    by the first model that writes the same field -- which would give a false
    negative.  The compared quantities must then differ from unperturbed
    ``A0``: the pipeline, not merely the comparator, resolves one last bit.
3.  A **reordering that is not inert**: arm ``A0rev`` runs the same nodes in
    reverse.  If that also came back identical, the harness would not be
    measuring node order at all and the headline zero would be worthless.

Usage
-----
    PYTHONPATH=<tree> python a23_permute.py --harvest H.pkl --scenario S \\
        --input S.IN.DAT --out result.json --tau 1e-6 \\
        --a18 <a18>/replay_tau1e-06_hoist0/result.json
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import os
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from fixedpoint import arms as A  # noqa: E402
from fixedpoint import engine as E  # noqa: E402
from fixedpoint.nodemap import NodeMap  # noqa: E402
from fixedpoint.replay import _check_ystate  # noqa: E402
from fixedpoint.replay import bind_state, restore, verify_restore  # noqa: E402
from fixedpoint.replay import y_index_by_node  # noqa: E402
from fixedpoint.ystate import YSpec  # noqa: E402

#: Keys of one entry of ``residual_trace``, all compared bit-for-bit.
TRACE_KEYS = (
    "max",
    "argmax",
    "n_above",
    "n_discrete_mismatch",
    "n_constant_moved",
    "n_nan_new",
)

#: Keys of the exit audit that are compared bit-for-bit.  ``objf``/``conf_*``
#: appear twice on purpose: ``*_at_exit`` is the state the arm would hand back,
#: and the unsuffixed ones are after the audit's one further sweep.
AUDIT_KEYS = (
    "max",
    "argmax",
    "n_above",
    "n_discrete_mismatch",
    "n_constant_moved",
    "n_nan_new",
    "converged_at_tau",
    "objf_at_exit",
    "conf_l2_at_exit",
    "conf_linf_at_exit",
    "objf",
    "conf_l2",
    "conf_linf",
    "audit_node_calls",
    "above_tau_fields",
    "moved_constant_fields",
    "discrete_mismatch_fields",
    "nan_new_fields",
)

#: Scalar counts and flags of one arm's result.
COUNT_KEYS = (
    "valid",
    "converged",
    "cap_hit",
    "sweeps",
    "module_sweeps",
    "node_calls",
    "outer",
    "cross_converged_at",
    # Present only when the feed-forward hoist is on; ``dict.get`` returns
    # ``None`` on both sides otherwise, so it compares harmlessly at hoist 0.
    "hoist_tail_node_calls",
)


# --------------------------------------------------------------------------
# The comparator
# --------------------------------------------------------------------------


def _counts(rec: dict) -> list:
    return [rec.get(k) for k in COUNT_KEYS] + [sorted(rec.get("moved_constants", []))]


def _trace(rec: dict) -> list:
    return [[t[k] for k in TRACE_KEYS] for t in rec.get("residual_trace", [])]


def _audit(rec: dict) -> list:
    a = rec.get("audit") or {}
    return [a.get(k) for k in AUDIT_KEYS]


def compare_records(ref: dict, cur: dict) -> list[str]:
    """The three families that differ between two arm records.

    A pure bit-comparison: ``==`` on Python floats, ints, strings and lists.
    No tolerance is applied anywhere, so one changed last bit of one float in
    one sweep of one design point is a difference.
    """
    out = []
    if _counts(ref) != _counts(cur):
        out.append("counts")
    if _trace(ref) != _trace(cur):
        out.append("residual_trace")
    if _audit(ref) != _audit(cur):
        out.append("exit_audit")
    return out


def compare_arms(ref_by_ci: dict, points: list, arm: str) -> dict:
    """Compare one arm of ``points`` against a reference, point by point.

    The denominator is carried explicitly and the verdict requires
    ``n_compared == n_points``: a comparison that quietly skipped points would
    otherwise publish a zero over a smaller population (trap T11), and an empty
    set would otherwise pass vacuously.
    """
    n_cmp = 0
    n_skipped_no_ref = 0
    n_skipped_error = 0
    bad: dict = {"counts": [], "residual_trace": [], "exit_audit": []}
    for row in points:
        ci = row["call_index"]
        r = ref_by_ci.get(ci)
        m = row["arms"].get(arm)
        if r is None:
            n_skipped_no_ref += 1
            continue
        if m is None or "error" in m:
            n_skipped_error += 1
            continue
        n_cmp += 1
        for fam in compare_records(r, m):
            bad[fam].append(ci)
    n_diff = len(set(bad["counts"]) | set(bad["residual_trace"])
                 | set(bad["exit_audit"]))
    return {
        "arm": arm,
        "n_points": len(points),
        "n_compared": n_cmp,
        "n_skipped_no_reference": n_skipped_no_ref,
        "n_skipped_arm_error": n_skipped_error,
        "n_mismatched_counts": len(bad["counts"]),
        "n_mismatched_residual_trace": len(bad["residual_trace"]),
        "n_mismatched_exit_audit": len(bad["exit_audit"]),
        "n_points_differing_anywhere": n_diff,
        "mismatched_call_indices": sorted(
            set(bad["counts"]) | set(bad["residual_trace"])
            | set(bad["exit_audit"])
        )[:40],
        "identical": (n_diff == 0 and n_cmp == len(points) and n_cmp > 0),
    }


# --------------------------------------------------------------------------
# Protocol §12: the comparator must be shown capable of failing
# --------------------------------------------------------------------------


def _ulp(x: float) -> float:
    if not math.isfinite(x):
        return x
    return math.nextafter(x, math.inf)


def comparator_self_test(rec: dict) -> dict:
    """Perturb one record by the smallest registering amount, per field.

    Every entry must come back ``caught: true``.  A field that cannot be
    perturbed in this record (a float that is not finite, an empty list) is
    reported as ``skipped`` with the reason, never silently counted as caught.
    """
    checks = []

    def _check(label, mutate):
        cur = copy.deepcopy(rec)
        why = mutate(cur)
        if why is not None:
            checks.append({"field": label, "skipped": why, "caught": None})
            return
        fams = compare_records(rec, cur)
        checks.append({"field": label, "caught": bool(fams), "families": fams})

    # -- scalar counts and flags ----------------------------------------
    def _bump_int(k):
        def f(c):
            v = c.get(k)
            if not isinstance(v, int) or isinstance(v, bool):
                return f"{k} is {type(v).__name__}, not an int"
            c[k] = v + 1
            return None
        return f

    for k in ("sweeps", "module_sweeps", "node_calls", "outer"):
        _check(f"counts.{k} +1", _bump_int(k))

    def _flip_converged(c):
        c["converged"] = not c["converged"]
        return None

    _check("counts.converged flipped", _flip_converged)

    def _add_moved(c):
        c["moved_constants"] = sorted(
            list(c.get("moved_constants", [])) + ["a23.sentinel"]
        )
        return None

    _check("counts.moved_constants +1 name", _add_moved)

    def _cross(c):
        v = c.get("cross_converged_at")
        c["cross_converged_at"] = (v + 1) if isinstance(v, int) else 1
        return None

    _check("counts.cross_converged_at +1", _cross)

    # -- the residual trace ---------------------------------------------
    def _trace_max_ulp(c):
        tr = c.get("residual_trace") or []
        if not tr:
            return "empty residual_trace"
        if not math.isfinite(tr[0]["max"]):
            return "residual_trace[0].max is not finite"
        tr[0]["max"] = _ulp(tr[0]["max"])
        return None

    _check("residual_trace[0].max +1 ULP", _trace_max_ulp)

    def _trace_last_max_ulp(c):
        tr = c.get("residual_trace") or []
        if not tr:
            return "empty residual_trace"
        if not math.isfinite(tr[-1]["max"]):
            return "residual_trace[-1].max is not finite"
        tr[-1]["max"] = _ulp(tr[-1]["max"])
        return None

    _check("residual_trace[-1].max +1 ULP", _trace_last_max_ulp)

    def _trace_argmax(c):
        tr = c.get("residual_trace") or []
        if not tr:
            return "empty residual_trace"
        tr[0]["argmax"] = "a23.sentinel"
        return None

    _check("residual_trace[0].argmax renamed", _trace_argmax)

    def _trace_nabove(c):
        tr = c.get("residual_trace") or []
        if not tr:
            return "empty residual_trace"
        tr[0]["n_above"] = int(tr[0]["n_above"]) + 1
        return None

    _check("residual_trace[0].n_above +1", _trace_nabove)

    # -- the exit audit --------------------------------------------------
    def _audit_float(k):
        def f(c):
            a = c.get("audit") or {}
            v = a.get(k)
            if not isinstance(v, float) or not math.isfinite(v):
                return f"audit.{k} is not a finite float"
            a[k] = _ulp(v)
            return None
        return f

    for k in ("objf_at_exit", "conf_l2_at_exit", "conf_linf_at_exit",
              "objf", "conf_l2", "conf_linf", "max"):
        _check(f"audit.{k} +1 ULP", _audit_float(k))

    def _audit_calls(c):
        a = c.get("audit") or {}
        a["audit_node_calls"] = int(a.get("audit_node_calls", 0)) + 1
        return None

    _check("audit.audit_node_calls +1", _audit_calls)

    def _audit_fields(c):
        a = c.get("audit") or {}
        a["above_tau_fields"] = list(a.get("above_tau_fields", [])) + [
            "a23.sentinel"
        ]
        return None

    _check("audit.above_tau_fields +1 name", _audit_fields)

    tested = [c for c in checks if c["caught"] is not None]
    return {
        "n_perturbations": len(checks),
        "n_tested": len(tested),
        "n_caught": sum(1 for c in tested if c["caught"]),
        "n_missed": sum(1 for c in tested if not c["caught"]),
        "n_skipped": len(checks) - len(tested),
        "all_tested_caught": bool(tested) and all(c["caught"] for c in tested),
        "checks": checks,
    }


def pick_ulp_component(points) -> dict | None:
    """Which component of the design vector the 1-ULP arm advances.

    The **design vector**, not a state field: ``Sweeper.inject`` re-imposes
    ``x`` at the head of every pass, so a nudge there drives the whole solve
    and cannot be overwritten by the first model that happens to write the same
    field.  Nudging a state field instead would risk a false negative -- the
    field is rewritten a node or two later and the perturbation never
    propagates -- which would make the sensitivity check say "no effect" for a
    reason that has nothing to do with the comparator.

    Deterministic: the lowest-indexed component that is finite and non-zero on
    the first design point.
    """
    if not points:
        return None
    x = np.asarray(points[0]["x"], dtype=float)
    for j in range(x.size):
        if math.isfinite(float(x[j])) and float(x[j]) != 0.0:
            return {
                "component": int(j),
                "n_components": int(x.size),
                "value_hex_point0": float(x[j]).hex(),
                "nudged_hex_point0": _ulp(float(x[j])).hex(),
            }
    return None


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------


def block_order(node_order, node_module, ynode, *, hoist: bool):
    """The flat node sequence the **block arm** executes.

    Derived from :func:`arms.build_blocks` by concatenating its blocks in
    ``arms.BLOCK_ORDER``, so the two arms provably share one definition of what
    the block order is.  Nothing here is hardcoded.
    """
    blocks = A.build_blocks(node_order, node_module, ynode, hoist=hoist)
    return [n for _label, nodes, _sub, _it in blocks for n in nodes], blocks


def describe_permutation(flat, perm) -> dict:
    """How the two orders differ, as data rather than as prose."""
    pos_flat = {n: i for i, n in enumerate(flat)}
    moved = [
        {"node": n, "from": pos_flat[n], "to": j}
        for j, n in enumerate(perm)
        if pos_flat.get(n) != j
    ]
    return {
        "flat_order": list(flat),
        "block_order": list(perm),
        "is_permutation": sorted(flat) == sorted(perm),
        "n_nodes": len(flat),
        "n_positions_changed": len(moved),
        "moved": moved,
        "identical": list(flat) == list(perm),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harvest", required=True)
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--expect-tree", default=None)
    ap.add_argument("--tau", type=float, default=1e-6)
    ap.add_argument("--a18", default=None,
                    help="A18's replay result.json, the A0 of record")
    ap.add_argument("--max-points", type=int, default=0)
    ap.add_argument("--hoist", type=int, default=0,
                    help="feed-forward hoist setting, matching A18's arms")
    ap.add_argument("--sensitivity", action="store_true",
                    help="add the arm-level 1-ULP arm and the comparator "
                         "self-test (protocol §12)")
    args = ap.parse_args()

    import process

    process_file = Path(process.__file__).resolve()
    if args.expect_tree:
        expect = Path(args.expect_tree).resolve()
        actual = process_file.parent.parent
        if actual != expect:
            raise SystemExit(
                f"WRONG TREE: imported {process_file} (tree {actual}), "
                f"expected exactly {expect}. Set PYTHONPATH={expect}."
            )
    if os.environ.get("PROCESS_IDF_PROBE"):
        raise SystemExit("the replay must run with PROCESS_IDF_PROBE unset")
    # A3 (VP1) and A13 (VP2) put two environment switches into caller.py.  The
    # replay does not go through ``Caller._call_models_once`` at all, but the
    # switches are resolved at import and an unset-default is part of the
    # harvest-reuse argument, so it is asserted rather than assumed.
    for var in ("PROCESS_ARCH_SEQUENCE", "PROCESS_ARCH_HOIST"):
        if os.environ.get(var):
            raise SystemExit(f"{var} must be unset for this replay")
    from process.core import caller as _caller

    if _caller.SEQUENCE_NAME != "upstream" or _caller.HOIST_NAME != "off":
        raise SystemExit(
            f"caller resolved SEQUENCE_NAME={_caller.SEQUENCE_NAME!r} "
            f"HOIST_NAME={_caller.HOIST_NAME!r}; both must be at their "
            f"upstream defaults"
        )

    import pickle

    with open(args.harvest, "rb") as fh:
        harvest = pickle.load(fh)
    assert harvest["format"] == "a18-harvest-1", harvest["format"]

    node_order = list(harvest["node_order"])
    node_module = dict(harvest["node_module"])
    writes_by_node = dict(harvest["writes_by_node"])

    all_points = harvest["points"]
    points = all_points[: args.max_points] if args.max_points else all_points

    nmap = NodeMap.load()
    observed = set(node_order) | {n for n, v in writes_by_node.items() if v}
    subset_check = nmap.assert_observed_subset(observed)

    # The load-bearing half of the harvest-reuse argument, measured rather than
    # asserted: A3 and A13 rewrote call sites inside ``Caller``, so the claim
    # "those rewrites are not on the replay's execution path" is only worth
    # having if it is counted.  Every entry to the three rewritten surfaces is
    # tallied, and the counts must be zero across the whole replay.
    caller_entries = Counter()

    def _count(cls, name):
        original = getattr(cls, name)

        def wrapper(*a, **kw):
            caller_entries[name] += 1
            return original(*a, **kw)

        setattr(cls, name, wrapper)

    for _name in ("call_models", "_call_models_once", "_node"):
        if hasattr(_caller.Caller, _name):
            _count(_caller.Caller, _name)

    from process.main import SingleRun

    sr = SingleRun(args.input, solver="vmcon", update_obsolete=True)
    models, data = sr.models, sr.data
    caller_entries_after_init = dict(caller_entries)

    spec = YSpec.from_harvest(harvest["y_keys"], all_points)
    ystate_check = _check_ystate(args.scenario, spec, args.harvest, harvest)
    if ystate_check["status"] == "MISMATCH":
        raise SystemExit(
            f"ystate MISMATCH for {args.scenario}: {ystate_check['detail']}"
        )
    ynode = y_index_by_node(spec, writes_by_node)

    # The DSM cross-check subset, exactly as replay.py resolves it: arm A0 is
    # handed it and records the sweep at which it *would* have converged, so
    # omitting it would not reproduce A18's A0.
    pos = {k: i for i, k in enumerate(spec.keys)}
    cross_subset = set()
    for f in nmap.feedback_fields():
        ns, _, fld = f.partition(".")
        i = pos.get((ns, fld))
        if i is not None:
            cross_subset.add(i)

    hoist = bool(args.hoist)
    ln = A.loop_nodes(node_order, node_module, hoist=hoist)
    hn = A.hoisted_nodes(node_order, node_module, hoist=hoist)
    ln_block, blocks = block_order(node_order, node_module, ynode, hoist=hoist)
    perm = describe_permutation(ln, ln_block)
    if not perm["is_permutation"]:
        raise SystemExit(
            "the block order is not a permutation of the flat order: "
            f"flat={sorted(ln)} block={sorted(ln_block)}"
        )
    if len(ln_block) != len(set(ln_block)):
        raise SystemExit("the block order repeats a node")

    # The exit audit uses the same node set and the same order for every arm,
    # as A18 did, so that a difference in the audit reflects a difference in
    # the terminal state and nothing else.  ``replay.py`` audits with the
    # **hoist-off** node set whatever the arm's hoist setting is, so that the
    # two settings are audited on the same footing; that is reproduced here.
    audit_nodes = A.loop_nodes(node_order, node_module, hoist=False)

    ulp_pick = None
    arm_specs = [("A0", ln), ("A0perm", ln_block)]
    if args.sensitivity:
        ulp_pick = pick_ulp_component(points)
        if ulp_pick:
            arm_specs.append(("A0ulp", ln))
        # A permutation that is **not** inert, as an end-to-end control on the
        # whole pipeline: if reversing the loop order also came back identical,
        # the harness would not be measuring node order at all and the headline
        # zero would mean nothing.
        arm_specs.append(("A0rev", list(reversed(ln))))

    result = {
        "task": "A23 (flat-arm-permutation)",
        "scenario": args.scenario,
        "tau": args.tau,
        "hoist": hoist,
        "hoisted_nodes": hn,
        "tree": str(process_file.parent.parent),
        "caller_switches": {
            "SEQUENCE_NAME": _caller.SEQUENCE_NAME,
            "HOIST_NAME": _caller.HOIST_NAME,
        },
        "harvest": str(Path(args.harvest).resolve()),
        "n_points": len(points),
        "n_harvest_points": len(all_points),
        "node_map_check": subset_check,
        "ystate_record": ystate_check,
        "permutation": perm,
        "block_schedule": [
            {"label": lab, "nodes": n, "iterate": it, "n_y_subset": len(s)}
            for lab, n, s, it in blocks
        ],
        "y_census": spec.census(),
        "dsm_cross_subset_size": len(cross_subset),
        "arms": [a for a, _n in arm_specs],
        "ulp_perturbation": ulp_pick,
        "points": [],
        "errors": [],
        "restore_mismatch_total": 0,
    }

    t0 = time.perf_counter()
    for p in points:
        bound = bind_state(data, p["state"])
        row = {"call_index": p["call_index"], "phase": p.get("phase"),
               "m": p.get("m"), "arms": {}}
        for arm, nodes in arm_specs:
            restore(bound)
            bad = verify_restore(bound)
            result["restore_mismatch_total"] += len(bad)
            x = p["x"]
            if arm == "A0ulp":
                x = np.asarray(p["x"], dtype=float).copy()
                j = ulp_pick["component"]
                x[j] = _ulp(float(x[j]))
            sw = E.Sweeper(models, data, node_order, x, p["nvars"],
                           m=p.get("m"))
            try:
                out = E.solve_flat(
                    sw, spec, nodes, args.tau, floor=1,
                    cross_subset=cross_subset or None,
                )
                if hoist and hn and out["converged"]:
                    # replay.py's convention: the tail runs once, after the
                    # fixed point, on a separate budget that is not charged to
                    # the arm's node_calls.
                    b = E.Budget(0)
                    sw.run_nodes(hn, b)
                    out["hoist_tail_node_calls"] = b.node_calls
                out["audit"] = E.exit_audit(sw, spec, audit_nodes, args.tau)
                out["restore_mismatch"] = len(bad)
            except Exception:
                out = {"valid": False, "converged": False,
                       "error": traceback.format_exc(limit=4)}
                result["errors"].append(
                    f"{arm}@{p['call_index']}: {out['error'].splitlines()[-1]}"
                )
            row["arms"][arm] = out
        result["points"].append(row)
    result["wall_s"] = time.perf_counter() - t0

    result["caller_entry_counts"] = {
        "after_singlerun_init": caller_entries_after_init,
        "after_replay": dict(caller_entries),
        "replay_never_entered_caller": sum(caller_entries.values()) == 0,
        "surfaces_counted": ["call_models", "_call_models_once", "_node"],
    }

    # -- the comparisons --------------------------------------------------
    comparisons = {}
    if args.a18:
        a18 = json.load(open(args.a18))
        if a18["tau"] != args.tau or bool(a18["hoist"]) != hoist:
            raise SystemExit(
                f"reference {args.a18} was run at tau={a18['tau']} "
                f"hoist={a18['hoist']}, not tau={args.tau} hoist={hoist}"
            )
        ref = {p["call_index"]: p["arms"].get("A0") for p in a18["points"]}
        comparisons["a18_reference"] = {
            "path": str(Path(args.a18).resolve()),
            "n_reference_points": len(a18["points"]),
            "reference_tau": a18["tau"],
            "reference_hoist": a18["hoist"],
            "population_matches": len(a18["points"]) == len(points),
        }
        # G1 -- reproduction.  Our A0 against A18's A0.  This is the empirical
        # half of the harvest-reuse licence: had the models the replay executes
        # changed since the harvest, this would not be zero.
        comparisons["G1_A0_vs_a18"] = compare_arms(ref, result["points"], "A0")
        # G2 -- the measurement.  The permuted flat arm against A18's A0.
        comparisons["G2_A0perm_vs_a18"] = compare_arms(
            ref, result["points"], "A0perm"
        )
    # G3 -- the same measurement inside one process: A0perm against our own A0.
    # Independent of A18's file, so a defect in reading that file cannot make
    # the headline look null.
    own = {r["call_index"]: r["arms"].get("A0") for r in result["points"]}
    comparisons["G3_A0perm_vs_own_A0"] = compare_arms(
        own, result["points"], "A0perm"
    )

    if args.sensitivity:
        # (1) the comparator, perturbed field by field
        first_ok = next(
            (r["arms"]["A0"] for r in result["points"]
             if "error" not in r["arms"]["A0"]), None
        )
        comparisons["sensitivity_comparator"] = (
            comparator_self_test(first_ok) if first_ok
            else {"skipped": "no converged A0 record"}
        )
        # (2) the pipeline, perturbed by one ULP of one design-vector component
        if ulp_pick:
            s = compare_arms(own, result["points"], "A0ulp")
            s["design_vector_component"] = ulp_pick
            s["detects_one_ulp"] = (
                s["n_compared"] == len(points)
                and s["n_points_differing_anywhere"] > 0
            )
            comparisons["sensitivity_one_ulp_arm"] = s
        else:
            comparisons["sensitivity_one_ulp_arm"] = {
                "skipped": "no finite non-zero design-vector component"
            }
        # (3) a permutation that is not inert, end to end
        s = compare_arms(own, result["points"], "A0rev")
        s["order"] = "loop_nodes reversed"
        s["detects_a_real_reordering"] = (
            s["n_compared"] + s["n_skipped_arm_error"] == len(points)
            and s["n_points_differing_anywhere"] + s["n_skipped_arm_error"] > 0
        )
        comparisons["sensitivity_reversed_order_arm"] = s

    result["comparisons"] = comparisons

    Path(args.out).write_text(json.dumps(result, default=_default))

    summary = {
        "scenario": args.scenario,
        "tau": args.tau,
        "hoist": hoist,
        "hoisted_nodes": hn,
        "n_points": len(points),
        "n_harvest_points": len(all_points),
        "n_errors": len(result["errors"]),
        "restore_mismatch_total": result["restore_mismatch_total"],
        "caller_entry_counts": result["caller_entry_counts"],
        "permutation": {
            "n_nodes": perm["n_nodes"],
            "n_positions_changed": perm["n_positions_changed"],
            "moved": perm["moved"],
        },
        "comparisons": {
            k: {kk: vv for kk, vv in v.items()
                if kk not in ("checks", "mismatched_call_indices")}
            for k, v in comparisons.items()
        },
        "sweeps_A0": _dist(result["points"], "A0"),
        "sweeps_A0perm": _dist(result["points"], "A0perm"),
        "node_calls_A0": _dist(result["points"], "A0", "node_calls"),
        "node_calls_A0perm": _dist(result["points"], "A0perm", "node_calls"),
    }
    print(json.dumps(summary, indent=2, default=_default))
    return 0


def _dist(points, arm, key="sweeps") -> dict:
    v = [r["arms"][arm].get(key) for r in points
         if r["arms"].get(arm) and r["arms"][arm].get("converged")]
    return {
        "n_converged": len(v),
        "total": sum(v) if v else 0,
        "mean": round(sum(v) / len(v), 6) if v else None,
        "dist": dict(sorted(Counter(v).items())),
    }


def _default(o):
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, set):
        return sorted(o)
    return str(o)


if __name__ == "__main__":
    raise SystemExit(main())
