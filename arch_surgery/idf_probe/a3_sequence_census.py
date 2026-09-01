#!/usr/bin/env python
"""A3 (build-reorder): measure the *executing* model sequence at run time.

Reading ``caller.py`` gives 26 ``.run()`` call sites; a given input deck reaches
only a subset, because the toroidal-field-coil branch and the blanket branch are
switch-selected on the deck.  This script records which nodes actually execute,
in which order, and how many times -- by observation, not by reading source.

It touches no PROCESS code.  It wraps the bound entry points of the model
objects from outside, in the same subprocess that runs the scenario, exactly as
A19's replay harness calls them from outside.

Two hazards are handled structurally rather than by a name filter.

**Trap T7.**  Ten model objects call their own ``run()`` from inside their
``output()`` method, three times each per run, during the final output
idempotence check.  A wrapper on ``run()`` alone would attribute that post-solve
reporting traffic to the model sequence.  So the recording window is opened and
closed at the boundary of ``Caller._call_models_once``; anything entered outside
it is counted separately, under ``refused_outside_sweep``.

**Nesting.**  ``Models`` holds many sub-models (``plasma_confinement``,
``plasma_beta``, ...) that ``_call_models_once`` never calls but that
``physics.run()`` calls internally.  Only calls at nesting depth 0 inside the
window are the caller's sequence; deeper ones are counted under
``nested_calls``.  Depth 0 is the granularity the DSM node map uses.

Usage
-----
    PYTHONPATH=<tree> python a3_sequence_census.py \
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

#: ``Models.costs`` is a property returning one of the private cost objects;
#: ``caller.py`` calls ``models.costs.run()``.  Report it under the name the
#: DSM node map uses.
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
    # Trap T6: a prefix test ("under a directory called PROCESS_surgery") passes
    # for the main checkout too, and would silently measure the wrong tree.
    if actual_tree != expect:
        raise SystemExit(
            f"WRONG TREE: imported {process_file} (tree {actual_tree}), "
            f"expected exactly {expect}."
        )

    from process.core import caller as caller_mod
    from process.main import SingleRun

    state = {"open": False, "depth": 0, "sweeps": 0}
    first_order: list[str] = []
    current: list[str] = []
    order_hist: Counter = Counter()  # tuple(depth-0 order) -> number of sweeps
    calls: Counter = Counter()
    nested: Counter = Counter()
    refused: Counter = Counter()

    def wrap(name, fn):
        if getattr(fn, "_a3_wrapped", False):
            return fn

        def wrapped(*a, **kw):
            if not state["open"]:
                refused[name] += 1
                return fn(*a, **kw)
            if state["depth"] == 0:
                current.append(name)
                calls[name] += 1
            else:
                nested[name] += 1
            state["depth"] += 1
            try:
                return fn(*a, **kw)
            finally:
                state["depth"] -= 1

        wrapped._a3_wrapped = True
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

    def patched(self, xc):
        if not installed["done"]:
            install(self.models)
        current.clear()
        state["open"] = True
        state["depth"] = 0
        try:
            return original(self, xc)
        finally:
            state["open"] = False
            state["sweeps"] += 1
            if not first_order:
                first_order.extend(current)
            order_hist[tuple(current)] += 1

    caller_mod.Caller._call_models_once = patched

    result = {
        "scenario": args.scenario,
        "tree": str(actual_tree),
        "process_file": str(process_file),
        "arch_sequence_env": os.environ.get("PROCESS_ARCH_SEQUENCE"),
        "arch_sequence_name": getattr(caller_mod, "SEQUENCE_NAME", None),
        "arch_sequence_head": list(getattr(caller_mod, "SEQUENCE_HEAD", []) or [])
        or None,
    }
    try:
        SingleRun(str(dst), solver="vmcon", update_obsolete=True).run()
        result["status"] = "ok"
    except Exception:
        result["status"] = "crashed"
        result["traceback"] = traceback.format_exc()

    orders = sorted(order_hist.items(), key=lambda kv: -kv[1])
    result.update({
        "n_sweeps": state["sweeps"],
        "first_sweep_order": first_order,
        "n_calls_first_sweep": len(first_order),
        "distinct_sweep_orders": len(order_hist),
        "sweep_orders": [
            {"n_sweeps": c, "n_calls": len(o), "order": list(o)} for o, c in orders
        ],
        "total_depth0_calls": sum(calls.values()),
        "calls_by_node": dict(sorted(calls.items())),
        "n_distinct_nodes": len(calls),
        "nested_calls_by_node": dict(sorted(nested.items())),
        "n_nested_calls": sum(nested.values()),
        # T7: invocations that arrived from an output() path, i.e. outside any
        # _call_models_once.  Reported, never counted as sequence.
        "refused_outside_sweep": dict(sorted(refused.items())),
        "n_refused_outside_sweep": sum(refused.values()),
    })
    (outdir / "sequence_census.json").write_text(json.dumps(result, indent=2))
    brief = {
        k: v
        for k, v in result.items()
        if k not in ("traceback", "sweep_orders", "nested_calls_by_node")
    }
    brief["n_distinct_sweep_orders"] = result["distinct_sweep_orders"]
    print(json.dumps(brief, indent=2))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
