#!/usr/bin/env python
"""A13 (feedforward-hoist): what the tail writes, and whether the loop's own
predicate reads any of it.

The hoist runs the feed-forward nodes once after the fixed point instead of on
every sweep.  That is only sound if the convergence test the loop applies does
not look at anything the tail writes -- otherwise the loop would be testing
state it has deliberately stopped updating, and could stop on a different
criterion than upstream's.

``Caller.call_models`` tests two things: ``objective_function(...)`` and
``constraint_eqns(...)``.  So the question is concrete:

    does any field written by a hoisted node appear in the read set of
    ``objectives.py`` or ``constraints.py``?

This script answers the *write* half by measurement and the *read* half by
name.  It does **not** call the objective or the constraints itself: they are
not pure -- ``constraints.py`` assigns ``data.cs_fatigue.n_cycle_min`` -- so an
instrument that evaluated them an extra time per sweep would perturb the run it
is observing.

Method
------
The tail nodes' ``run`` methods are wrapped from outside, and the whole
``DataStructure`` is fingerprinted immediately before and immediately after
each.  A field whose fingerprint changes across a node was written by it.  The
union over sweeps is the node's run-time write set, for **this deck**.

Two hazards are handled the way ``a3_sequence_census.py`` handles them.

**Trap T7.**  Ten model objects call their own ``run()`` from inside
``output()``.  The recording window is opened and closed at the boundary of
``Caller._call_models_once``; invocations outside it are counted separately and
never contribute to the write set.

**Nesting.**  Only depth-0 invocations are the caller's own; deeper ones belong
to a parent model's internals.

Usage
-----
    PYTHONPATH=<tree> python a13_tail_writeset.py \
        --scenario large_tokamak_nof --outdir <dir> --expect-tree <tree>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import traceback
from collections import Counter
from dataclasses import fields, is_dataclass
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent

#: ``Models.costs`` is a property returning one of the private cost objects.
ALIASES = {"_costs_1990": "costs", "_costs_2015": "costs", "_costs_custom": "costs"}

#: Attribute reads of the form ``data.<namespace>.<field>``.  ``objectives.py``
#: and ``constraints.py`` reach the data structure only this way.
_READ = re.compile(r"\bdata\.(?P<ns>[a-z_][a-z0-9_]*)\.(?P<field>[A-Za-z_][A-Za-z0-9_]*)")


def _fingerprint(value):
    """A cheap, exact fingerprint of one data-structure value."""
    if isinstance(value, np.ndarray):
        return (value.shape, value.dtype.str, value.tobytes())
    if isinstance(value, (list, tuple)):
        try:
            return repr(value)
        except Exception:
            return id(value)
    if isinstance(value, (int, float, np.floating, np.integer, bool, str, type(None))):
        return value if not isinstance(value, float) else float(value).hex()
    return repr(value)


def _snapshot(data) -> dict:
    out = {}
    for ns_field in fields(data):
        ns = getattr(data, ns_field.name, None)
        if ns is None or not is_dataclass(ns):
            continue
        for f in fields(ns):
            try:
                out[f"{ns_field.name}.{f.name}"] = _fingerprint(getattr(ns, f.name))
            except Exception:
                continue
    return out


def _read_set(path: Path) -> set[str]:
    text = path.read_text(errors="replace")
    return {f"{m.group('ns')}.{m.group('field')}" for m in _READ.finditer(text)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--expect-tree", required=True)
    ap.add_argument(
        "--max-sweeps",
        type=int,
        default=400,
        help="stop fingerprinting after this many sweeps; the union is "
        "reported with this denominator beside it",
    )
    args = ap.parse_args()

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    src = HERE / "scenarios" / f"{args.scenario}.IN.DAT"
    dst = outdir / f"{args.scenario}.IN.DAT"
    shutil.copy(src, dst)

    os.environ.pop("PROCESS_IDF_PROBE", None)
    # The write set is a property of the models, not of the arm, so it is
    # measured with the hoist OFF -- the sequence upstream runs.
    os.environ.pop("PROCESS_ARCH_HOIST", None)

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

    tail_nodes = tuple(getattr(caller_mod, "DEFERRABLE_NODES", ("water_use", "costs")))

    state = {"open": False, "depth": 0, "sweeps": 0, "snapped": 0}
    writes: dict[str, set[str]] = {n: set() for n in tail_nodes}
    calls: Counter = Counter()
    refused: Counter = Counter()
    holder: dict = {}

    def wrap(name, fn):
        if getattr(fn, "_a13_wrapped", False):
            return fn

        def wrapped(*a, **kw):
            if not state["open"]:
                refused[name] += 1
                return fn(*a, **kw)
            if state["depth"] != 0:
                return fn(*a, **kw)
            calls[name] += 1
            if state["snapped"] >= args.max_sweeps:
                state["depth"] += 1
                try:
                    return fn(*a, **kw)
                finally:
                    state["depth"] -= 1
            before = _snapshot(holder["data"])
            state["depth"] += 1
            try:
                return fn(*a, **kw)
            finally:
                state["depth"] -= 1
                after = _snapshot(holder["data"])
                for k, v in after.items():
                    if before.get(k, object()) != v:
                        writes[name].add(k)

        wrapped._a13_wrapped = True
        return wrapped

    installed = {"done": False}

    def install(models):
        for attr, obj in list(vars(models).items()):
            name = ALIASES.get(attr, attr)
            if name not in tail_nodes:
                continue
            fn = getattr(obj, "run", None)
            if callable(fn):
                obj.run = wrap(name, fn)
        installed["done"] = True

    original = caller_mod.Caller._call_models_once

    def patched(self, xc, *a, **kw):
        if not installed["done"]:
            holder["data"] = self.data
            install(self.models)
        state["open"] = True
        state["depth"] = 0
        try:
            return original(self, xc, *a, **kw)
        finally:
            state["open"] = False
            state["sweeps"] += 1
            if state["snapped"] < args.max_sweeps:
                state["snapped"] += 1

    caller_mod.Caller._call_models_once = patched

    result = {
        "scenario": args.scenario,
        "tree": str(actual_tree),
        "process_file": str(process_file),
        "tail_nodes_instrumented": list(tail_nodes),
        "max_sweeps_fingerprinted": args.max_sweeps,
    }
    try:
        sr = SingleRun(str(dst), solver="vmcon", update_obsolete=True)
        sr.run()
        result["status"] = "ok"
        result["i_figure_merit"] = int(sr.data.numerics.i_figure_merit)
    except Exception:
        result["status"] = "crashed"
        result["traceback"] = traceback.format_exc()

    # The read halves, by name, from the two files the predicate is made of.
    core = Path(process.__file__).resolve().parent / "core" / "solver"
    reads = {
        "objectives": _read_set(core / "objectives.py"),
        "constraints": _read_set(core / "constraints.py"),
    }

    per_node = {}
    for node in tail_nodes:
        w = sorted(writes[node])
        per_node[node] = {
            "n_calls_depth0_in_sweep": calls[node],
            "n_fields_written": len(w),
            "fields_written": w,
            "read_by_objectives": sorted(set(w) & reads["objectives"]),
            "read_by_constraints": sorted(set(w) & reads["constraints"]),
        }

    result.update({
        "n_sweeps": state["sweeps"],
        "n_sweeps_fingerprinted": state["snapped"],
        "n_fields_in_snapshot": len(_snapshot(holder["data"])) if holder else 0,
        "refused_outside_sweep": dict(refused),
        "per_node": per_node,
        "n_reads_objectives": len(reads["objectives"]),
        "n_reads_constraints": len(reads["constraints"]),
    })
    (outdir / "tail_writeset.json").write_text(json.dumps(result, indent=2))
    brief = {k: v for k, v in result.items() if k != "traceback"}
    brief["per_node"] = {
        n: {k: v for k, v in d.items() if k != "fields_written"}
        for n, d in per_node.items()
    }
    print(json.dumps(brief, indent=2))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
