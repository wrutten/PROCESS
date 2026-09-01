#!/usr/bin/env python
"""A13 (feedforward-hoist): count model evaluations, in the loop and after it.

This is the saving gate's instrument.  It is ``a3_sequence_census.py`` with one
addition: the hoisted tail runs **outside** ``Caller._call_models_once``, so a
census that only watches that method would score the tail's evaluations as
trap-T7 reporting traffic and report a saving that is entirely fictitious.  A
second window is therefore opened around ``Caller._run_hoisted_tail``, and its
calls are counted in their own bucket.

The three buckets are disjoint and together account for every depth-0
invocation of a caller-level model node:

``in_loop``
    depth-0 invocations inside ``_call_models_once`` -- the per-sweep cost.
``hoisted``
    depth-0 invocations inside ``_run_hoisted_tail`` -- run once per
    ``call_models``, after the fixed point.
``outside``
    everything else, which is the ``output()``-path traffic of trap T7 and is
    the same in both arms.  Reported, never counted as sequence.

Usage
-----
    PYTHONPATH=<tree> python a13_node_census.py \
        --scenario large_tokamak_nof --outdir <dir> --expect-tree <tree>
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import traceback
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent

#: Non-``run()`` model entry points that ``_call_models_once`` calls directly.
EXTRA_CALLS = (("power", "acpow"), ("power", "plant_electric_production"))

#: ``Models.costs`` is a property returning one of the private cost objects.
ALIASES = {"_costs_1990": "costs", "_costs_2015": "costs", "_costs_custom": "costs"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--expect-tree", required=True)
    args = ap.parse_args()

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    src = HERE / "scenarios" / f"{args.scenario}.IN.DAT"
    dst = outdir / f"{args.scenario}.IN.DAT"
    shutil.copy(src, dst)

    # The probe stays off: this instrument is the measurement.
    os.environ.pop("PROCESS_IDF_PROBE", None)

    import process

    process_file = Path(process.__file__).resolve()
    actual_tree = process_file.parent.parent
    expect = Path(args.expect_tree).resolve()
    # Trap T6: a prefix test passes for the main checkout too.
    if actual_tree != expect:
        raise SystemExit(
            f"WRONG TREE: imported {process_file} (tree {actual_tree}), "
            f"expected exactly {expect}."
        )

    from process.core import caller as caller_mod
    from process.main import SingleRun

    # window: None (nothing open), "in_loop", or "hoisted"
    state = {"window": None, "depth": 0, "sweeps": 0, "tails": 0}
    first_order: list[str] = []
    current: list[str] = []
    order_hist: Counter = Counter()
    in_loop: Counter = Counter()
    hoisted: Counter = Counter()
    nested: Counter = Counter()
    outside: Counter = Counter()

    def wrap(name, fn):
        if getattr(fn, "_a13_wrapped", False):
            return fn

        def wrapped(*a, **kw):
            window = state["window"]
            if window is None:
                outside[name] += 1
                return fn(*a, **kw)
            if state["depth"] == 0:
                if window == "in_loop":
                    current.append(name)
                    in_loop[name] += 1
                else:
                    hoisted[name] += 1
            else:
                nested[name] += 1
            state["depth"] += 1
            try:
                return fn(*a, **kw)
            finally:
                state["depth"] -= 1

        wrapped._a13_wrapped = True
        return wrapped

    installed = {"done": False}

    def install(models):
        for attr, obj in list(vars(models).items()):
            name = ALIASES.get(attr, attr)
            fn = getattr(obj, "run", None)
            if callable(fn):
                obj.run = wrap(name, fn)
        for owner, meth in EXTRA_CALLS:
            obj = getattr(models, owner, None)
            fn = getattr(obj, meth, None)
            if callable(fn):
                setattr(obj, meth, wrap(f"{owner}.{meth}", fn))
        installed["done"] = True

    original = caller_mod.Caller._call_models_once

    def patched(self, xc, *a, **kw):
        if not installed["done"]:
            install(self.models)
        current.clear()
        state["window"] = "in_loop"
        state["depth"] = 0
        try:
            return original(self, xc, *a, **kw)
        finally:
            state["window"] = None
            state["sweeps"] += 1
            if not first_order:
                first_order.extend(current)
            order_hist[tuple(current)] += 1

    caller_mod.Caller._call_models_once = patched

    # VP2: the hoisted tail is a second window.  Absent on a tree that predates
    # the variant point, in which case ``hoisted`` stays empty -- which is the
    # right answer there.
    original_tail = getattr(caller_mod.Caller, "_run_hoisted_tail", None)
    if original_tail is not None:

        def patched_tail(self, pending):
            state["window"] = "hoisted"
            state["depth"] = 0
            try:
                return original_tail(self, pending)
            finally:
                state["window"] = None
                state["tails"] += 1

        caller_mod.Caller._run_hoisted_tail = patched_tail

    result = {
        "scenario": args.scenario,
        "tree": str(actual_tree),
        "process_file": str(process_file),
        "arch_hoist_env": os.environ.get("PROCESS_ARCH_HOIST"),
        "arch_hoist_name": getattr(caller_mod, "HOIST_NAME", None),
        "arch_hoist_nodes": list(getattr(caller_mod, "HOIST_NODES", []) or []),
        "hoist_hook_present": original_tail is not None,
        "arch_sequence_name": getattr(caller_mod, "SEQUENCE_NAME", None),
    }
    try:
        sr = SingleRun(str(dst), solver="vmcon", update_obsolete=True)
        sr.run()
        result["status"] = "ok"
        result["i_figure_merit"] = int(sr.data.numerics.i_figure_merit)
        result["n_model_calls_builtin"] = int(sr.data.numerics.n_model_calls)
        result["arch_hoist_tail_resolved"] = (
            list(caller_mod.resolved_hoist_tail(sr.data.numerics.i_figure_merit))
            if hasattr(caller_mod, "resolved_hoist_tail")
            else None
        )
    except Exception:
        result["status"] = "crashed"
        result["traceback"] = traceback.format_exc()

    orders = sorted(order_hist.items(), key=lambda kv: -kv[1])
    result.update({
        "n_sweeps": state["sweeps"],
        "n_hoisted_tail_runs": state["tails"],
        "first_sweep_order": first_order,
        "n_calls_first_sweep": len(first_order),
        "distinct_sweep_orders": len(order_hist),
        "sweep_orders": [
            {"n_sweeps": c, "n_calls": len(o), "order": list(o)} for o, c in orders
        ],
        # The saving gate's three counts.
        "n_evals_in_loop": sum(in_loop.values()),
        "n_evals_hoisted": sum(hoisted.values()),
        "n_evals_total": sum(in_loop.values()) + sum(hoisted.values()),
        "evals_in_loop_by_node": dict(sorted(in_loop.items())),
        "evals_hoisted_by_node": dict(sorted(hoisted.items())),
        "n_nested_calls": sum(nested.values()),
        "nested_calls_by_node": dict(sorted(nested.items())),
        # T7: output()-path traffic.  Same in both arms; never sequence.
        "outside_any_window": dict(sorted(outside.items())),
        "n_outside_any_window": sum(outside.values()),
    })
    (outdir / "node_census.json").write_text(json.dumps(result, indent=2))
    brief = {
        k: v
        for k, v in result.items()
        if k not in ("traceback", "sweep_orders", "nested_calls_by_node")
    }
    print(json.dumps(brief, indent=2))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
