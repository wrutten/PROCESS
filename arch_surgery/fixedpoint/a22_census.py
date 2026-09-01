#!/usr/bin/env python
"""A22 (outer-pass-census): which fields are still moving on outer pass 2+?

The A18 block arm records, per outer pass, only the *worst* moving component
(``argmax``) and how many were above tolerance.  That is enough to say a second
outer pass was needed and not enough to say **why**.  This driver re-runs the
same block arm on the same harvested design points, with the same tolerance,
and records the **full set** of moving fields at every outer pass and inside
every block's inner solve, together with the model that writes each one.

It adds two counterfactual arms.  Neither changes any physics: both change only
what the driver does with a value.

``A1pin``
    The block arm with ``times.t_plant_pulse_burn`` (the burn time) held at its
    entry value for the whole solve -- re-imposed after every model call, so the
    ``pulse`` model's write to it is discarded before any later model can read
    it.  This is the counterfactual for Phase B, which proposes to lift the burn
    time onto the optimiser and so make it an *input* to the loop rather than
    something the loop computes.  If the burn time is the only quantity closing
    a cycle between modules -- A2's ``k = 1`` -- then under this arm no module's
    state may move on outer pass 2 or later.

``A1ffit``
    The block arm with the feed-forward tail ``FF`` (``water_use``, ``costs``)
    iterated to its own fixed point like the three modules, instead of being run
    once per outer pass.  ``FF`` feeds nothing back into ``M1``/``M2``/``M3``, so
    this cannot change the modules' answers; it can only reveal whether ``FF``
    has an internal fixed point that the *outer* loop is currently resolving on
    its behalf.  That is a within-module effect masquerading as an outer-pass
    count.

The one gate
------------
Arm ``A1`` here must reproduce A18's recorded outer count, inner counts and node
call count **exactly**, per design point, or the recording has changed the thing
being measured.  ``--a18`` points at A18's ``result.json`` and the comparison is
reported as a count of mismatched points; it is a bit-comparison, not a
tolerance.

Usage
-----
    PYTHONPATH=<tree> python a22_census.py --harvest H.pkl --scenario S \\
        --input S.IN.DAT --out census.json --tau 1e-6 \\
        --a18 <a18>/replay_tau1e-06_hoist0/result.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from fixedpoint import arms as A  # noqa: E402
from fixedpoint import engine as E  # noqa: E402
from fixedpoint.nodemap import NodeMap  # noqa: E402
from fixedpoint.replay import bind_state, restore, verify_restore  # noqa: E402
from fixedpoint.replay import y_index_by_node  # noqa: E402
from fixedpoint.ystate import YSpec  # noqa: E402

#: How many moving field names are kept per residual.  A cap, not a sample:
#: the *count* above tolerance is always recorded in full, and the cap is only
#: on how many are named.  60 is above the largest count seen on any outer pass
#: from 2 onwards in A18's data (52), so no diagnostic pass is truncated.
NAME_CAP = 60

#: The field Phase B proposes to lift onto the optimiser.
BURN_TIME = "times.t_plant_pulse_burn"


class Recorder:
    """Collects the named moving fields, per outer pass and per inner sweep."""

    def __init__(self, spec: YSpec, tau: float):
        self.spec = spec
        self.tau = tau
        self.outer_records: list = []
        self.inner_records: list = []

    def _named(self, res):
        idx = res.above(self.tau)
        if not idx:
            return []
        pos = {i: j for j, i in enumerate(res.idx_c)}
        pairs = [(self.spec.name(i), float(res.scaled[pos[i]])) for i in idx]
        pairs.sort(key=lambda p: -p[1])
        return pairs[:NAME_CAP]

    def outer_pass(self, outer: int, res) -> None:
        self.outer_records.append({
            "outer": outer,
            "max": res.max,
            "argmax": None if res.argmax is None else self.spec.name(res.argmax),
            "n_above": res.n_above(self.tau),
            "above": self._named(res),
            "moved_constant": [self.spec.name(i) for i in res.moved_constant],
            "discrete_mismatch": [
                self.spec.name(i) for i in res.mismatch_discrete
            ],
        })

    def inner(self, outer: int, label: str, s: int, res) -> None:
        # Inner sweeps on outer pass 1 are the block finding its own fixed
        # point from an entry state that has not been swept at this design
        # vector; they say nothing about coupling.  From outer pass 2 they do:
        # the block converged in pass 1, so anything that moves now was moved
        # by something outside the block.
        if outer < 2:
            self.inner_records.append({
                "outer": outer, "block": label, "s": s,
                "n_above": res.n_above(self.tau), "above": [],
            })
            return
        self.inner_records.append({
            "outer": outer, "block": label, "s": s,
            "max": res.max,
            "n_above": res.n_above(self.tau),
            "above": self._named(res),
        })


def _ff_iterated(blocks, ynode):
    """``blocks`` with the feed-forward tail iterated like a module."""
    out = []
    for label, nodes, subset, iterate in blocks:
        if label == "FF" and nodes:
            sub = set()
            for n in nodes:
                sub |= ynode.get(n, set())
            out.append((label, nodes, sub, True))
        else:
            out.append((label, nodes, subset, iterate))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harvest", required=True)
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--expect-tree", default=None)
    ap.add_argument("--tau", type=float, default=1e-6)
    ap.add_argument("--a18", default=None, help="A18 result.json, for the gate")
    ap.add_argument("--max-points", type=int, default=0)
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
        raise SystemExit("the census must run with PROCESS_IDF_PROBE unset")

    import pickle

    with open(args.harvest, "rb") as fh:
        harvest = pickle.load(fh)
    assert harvest["format"] == "a18-harvest-1", harvest["format"]

    node_order = list(harvest["node_order"])
    node_module = dict(harvest["node_module"])
    writes_by_node = dict(harvest["writes_by_node"])

    # field -> writing node -> module.  Measured in-loop by the harvest, which
    # closes its sweep at the boundary of ``Caller._call_models_once`` and so
    # never sees an ``output()`` path (traps T1 and T7).
    writer_of: dict = defaultdict(list)
    for node, fields in writes_by_node.items():
        for f in fields:
            writer_of[f].append(node)

    all_points = harvest["points"]
    points = all_points[: args.max_points] if args.max_points else all_points

    nmap = NodeMap.load()
    observed = set(node_order) | {n for n, v in writes_by_node.items() if v}
    subset_check = nmap.assert_observed_subset(observed)

    from process.main import SingleRun

    sr = SingleRun(args.input, solver="vmcon", update_obsolete=True)
    models, data = sr.models, sr.data

    spec = YSpec.from_harvest(harvest["y_keys"], all_points)
    ynode = y_index_by_node(spec, writes_by_node)
    blocks = A.build_blocks(node_order, node_module, ynode, hoist=False)
    blocks_ffit = _ff_iterated(blocks, ynode)
    all_nodes = A.loop_nodes(node_order, node_module, hoist=False)

    pulse_writes_burn = BURN_TIME in writes_by_node.get("pulse", [])

    arm_specs = [
        ("A1", blocks, None),
        ("A1pin", blocks, [BURN_TIME]),
        ("A1ffit", blocks_ffit, None),
    ]

    result = {
        "task": "A22 (outer-pass-census)",
        "scenario": args.scenario,
        "tau": args.tau,
        "tree": str(process_file.parent.parent),
        "harvest": str(Path(args.harvest).resolve()),
        "n_points": len(points),
        "node_map_check": subset_check,
        "block_schedule": [
            {"label": lab, "nodes": n, "iterate": it, "n_y_subset": len(s)}
            for lab, n, s, it in blocks
        ],
        "pulse_writes_burn_time": pulse_writes_burn,
        "burn_time_category": None,
        "y_census": spec.census(),
        "name_cap": NAME_CAP,
        "writer_of": {f: v for f, v in sorted(writer_of.items())},
        "node_module": node_module,
        "points": [],
        "errors": [],
        "restore_mismatch_total": 0,
    }
    pos = {k: i for i, k in enumerate(spec.keys)}
    bt_key = tuple(BURN_TIME.split("."))
    if bt_key in pos:
        result["burn_time_category"] = spec.category[pos[bt_key]]

    t0 = time.perf_counter()
    for p in points:
        bound = bind_state(data, p["state"])
        row = {"call_index": p["call_index"], "phase": p.get("phase"),
               "arms": {}}
        for arm, blks, pin in arm_specs:
            restore(bound)
            bad = verify_restore(bound)
            result["restore_mismatch_total"] += len(bad)
            sw = E.Sweeper(models, data, node_order, p["x"], p["nvars"],
                           m=p.get("m"), pin=pin)
            rec = Recorder(spec, args.tau)
            try:
                out = E.solve_block(sw, spec, blks, args.tau, floor=1,
                                    recorder=rec)
                out["audit"] = E.exit_audit(sw, spec, all_nodes, args.tau)
                out["outer_records"] = rec.outer_records
                out["inner_records"] = rec.inner_records
            except Exception:
                out = {"valid": False, "converged": False,
                       "error": traceback.format_exc(limit=4)}
                result["errors"].append(
                    f"{arm}@{p['call_index']}: {out['error'].splitlines()[-1]}"
                )
            row["arms"][arm] = out
        result["points"].append(row)
    result["wall_s"] = time.perf_counter() - t0

    # -- the gate: A1 must reproduce A18 exactly --------------------------
    gate = {"checked": False}
    if args.a18:
        a18 = json.load(open(args.a18))
        ref = {p["call_index"]: p["arms"].get("A1") for p in a18["points"]}
        # Counts, the float residual trace, and the exit audit's objective and
        # constraint norms.  Bit-comparison throughout: no tolerance is applied
        # anywhere in this gate, so a single changed last bit fails it.
        tkeys = ["max", "argmax", "n_above", "n_discrete_mismatch",
                 "n_constant_moved", "n_nan_new"]
        akeys = ["max", "argmax", "n_above", "objf_at_exit", "conf_l2_at_exit",
                 "conf_linf_at_exit", "objf", "conf_l2", "conf_linf",
                 "audit_node_calls", "above_tau_fields",
                 "moved_constant_fields"]
        n_cmp = 0
        bad_counts, bad_trace, bad_audit = [], [], []
        for row in result["points"]:
            r = ref.get(row["call_index"])
            m = row["arms"]["A1"]
            if r is None or "error" in m:
                continue
            n_cmp += 1
            ci = row["call_index"]
            if (r["outer"], r["node_calls"], r["module_sweeps"],
                    r["inner"]["counts"], r["converged"],
                    sorted(r["moved_constants"])) != (
                    m["outer"], m["node_calls"], m["module_sweeps"],
                    m["inner"]["counts"], m["converged"],
                    sorted(m["moved_constants"])):
                bad_counts.append(ci)
            if ([[x[k] for k in tkeys] for x in r["residual_trace"]]
                    != [[x[k] for k in tkeys] for x in m["residual_trace"]]):
                bad_trace.append(ci)
            if ([r["audit"][k] for k in akeys]
                    != [m["audit"][k] for k in akeys]):
                bad_audit.append(ci)
        gate = {
            "checked": True, "a18": args.a18, "n_compared": n_cmp,
            "n_mismatched_counts": len(bad_counts),
            "n_mismatched_residual_trace": len(bad_trace),
            "n_mismatched_exit_audit": len(bad_audit),
            "mismatched": sorted(set(bad_counts + bad_trace + bad_audit))[:20],
            "pass": (not bad_counts and not bad_trace and not bad_audit
                     and n_cmp == len(result["points"])),
        }
    result["gate_reproduces_a18"] = gate

    Path(args.out).write_text(json.dumps(result, default=_default))
    summary = {
        "scenario": args.scenario, "n_points": len(points),
        "wall_s": result["wall_s"], "n_errors": len(result["errors"]),
        "restore_mismatch_total": result["restore_mismatch_total"],
        "gate": gate,
        "outer_mean": {},
    }
    for arm, _b, _p in arm_specs:
        o = [r["arms"][arm].get("outer") for r in result["points"]
             if r["arms"][arm].get("converged")]
        summary["outer_mean"][arm] = {
            "n_converged": len(o),
            "mean": round(sum(o) / len(o), 4) if o else None,
            "dist": dict(sorted(Counter(o).items())),
        }
    print(json.dumps(summary, indent=2))
    return 0


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
