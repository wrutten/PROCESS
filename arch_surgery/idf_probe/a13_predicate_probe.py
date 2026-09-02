#!/usr/bin/env python
"""A13: which figures of merit move when a tail node runs.

``Caller.call_models`` stops when the objective function and the constraint
residuals stop changing.  If a hoisted node writes something the objective
reads, the loop would be testing state the hoist has deliberately stopped
updating.  ``caller.py`` carries a table of which figures of merit read a
hoisted node's output; this script **derives that table by measurement**
instead of trusting it.

Method: evaluate every figure of merit immediately before a tail node runs and
again immediately after, and compare the two as hex floats.  A figure of merit
that moves across the node reads something the node wrote.

``objective_function`` is a pure read of the data structure, so evaluating it
extra times cannot perturb the run.  ``constraint_eqns`` is **not** pure -- it
assigns ``data.cs_fatigue.n_cycle_min`` -- so it is deliberately not called
here; the constraint half of the question is answered by the write-set probe's
name intersection instead, cross-checked against the deck's active ``icc``
list, which this script also records.

Usage
-----
    PYTHONPATH=<tree> python a13_predicate_probe.py \
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

ALIASES = {"_costs_1990": "costs", "_costs_2015": "costs", "_costs_custom": "costs"}

#: The contiguous feed-forward tail at the end of ``_call_models_once``.  The
#: articulation point ``pulse`` sits in the middle of the sequence, so an
#: objective difference measured across it would include every model between,
#: and is not attributable; it is excluded here and noted in the report.
TAIL = ("water_use", "costs")


def _fom_reads_node(caller_mod, fom: int, node: str, writes) -> bool:
    """Whether figure of merit *fom* puts *node* in the pre-predicate slot.

    A26's routing rule, evaluated for one figure of merit.  An unrecognised
    figure of merit raises inside ``_predicate_read_fields``; that is not a
    finding about the node, so it is treated as "does not read".
    """
    try:
        reads = caller_mod._predicate_read_fields(fom)
    except Exception:  # noqa: BLE001
        return False
    return bool(writes.get(node, frozenset()) & reads)


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

    os.environ.pop("PROCESS_IDF_PROBE", None)
    os.environ.pop("PROCESS_ARCH_HOIST", None)

    import process

    process_file = Path(process.__file__).resolve()
    actual_tree = process_file.parent.parent
    expect = Path(args.expect_tree).resolve()
    if actual_tree != expect:  # trap T6
        raise SystemExit(
            f"WRONG TREE: imported {process_file} (tree {actual_tree}), "
            f"expected exactly {expect}."
        )

    from process.core import caller as caller_mod
    from process.core.solver.objectives import objective_function
    from process.data_structure.numerics import FiguresOfMerit
    from process.main import SingleRun

    foms = [int(f) for f in FiguresOfMerit]
    state = {"open": False, "depth": 0, "sweeps": 0}
    holder: dict = {}
    moved: dict[str, Counter] = {n: Counter() for n in TAIL}
    evaluated: dict[str, Counter] = {n: Counter() for n in TAIL}
    errors: dict[str, Counter] = {n: Counter() for n in TAIL}

    def evaluate(data):
        out = {}
        for f in foms:
            try:
                out[f] = float(objective_function(f, data)).hex()
            except Exception:
                out[f] = "ERROR"
        return out

    def wrap(name, fn):
        if getattr(fn, "_a13p_wrapped", False):
            return fn

        def wrapped(*a, **kw):
            if not state["open"] or state["depth"] != 0:
                return fn(*a, **kw)
            data = holder["data"]
            before = evaluate(data)
            state["depth"] += 1
            try:
                return fn(*a, **kw)
            finally:
                state["depth"] -= 1
                after = evaluate(data)
                for f in foms:
                    if before[f] == "ERROR" or after[f] == "ERROR":
                        errors[name][f] += 1
                        continue
                    evaluated[name][f] += 1
                    if before[f] != after[f]:
                        moved[name][f] += 1

        wrapped._a13p_wrapped = True
        return wrapped

    installed = {"done": False}

    def install(models):
        for attr, obj in list(vars(models).items()):
            nm = ALIASES.get(attr, attr)
            if nm not in TAIL:
                continue
            fn = getattr(obj, "run", None)
            if callable(fn):
                obj.run = wrap(nm, fn)
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

    caller_mod.Caller._call_models_once = patched

    result = {
        "scenario": args.scenario,
        "tree": str(actual_tree),
        "tail_nodes_probed": list(TAIL),
        "figures_of_merit_probed": foms,
    }
    try:
        sr = SingleRun(str(dst), solver="vmcon", update_obsolete=True)
        sr.run()
        result["status"] = "ok"
        nums = sr.data.numerics
        result["i_figure_merit"] = int(nums.i_figure_merit)
        m = int(nums.n_equality_constraints) + int(nums.n_inequality_constraints)
        result["icc_active"] = [int(v) for v in nums.icc[:m]]
    except Exception:
        result["status"] = "crashed"
        result["traceback"] = traceback.format_exc()

    per_node = {}
    for n in TAIL:
        per_node[n] = {
            "figures_of_merit_that_moved": sorted(moved[n]),
            "sweeps_moved_by_fom": {str(k): v for k, v in sorted(moved[n].items())},
            "sweeps_evaluated_by_fom": {
                str(k): v for k, v in sorted(evaluated[n].items())
            },
            "sweeps_erroring_by_fom": {str(k): v for k, v in sorted(errors[n].items())},
        }
    result["n_sweeps"] = state["sweeps"]
    result["per_node"] = per_node

    # The rule caller.py carries, and whether measurement agrees with it.
    #
    # A26 replaced the hard-coded ``_FOM_READS_NODE`` table with a routing rule
    # derived from the driver's own source (``_predicate_read_fields``) and the
    # committed per-node write census.  So the "declaration" is now derived,
    # per figure of merit, rather than listed --- which is the whole point, and
    # is why this probe recomputes it instead of reading a constant.  If
    # neither is available the probe says so rather than silently comparing
    # against an empty table, which would make the check pass unconditionally.
    declared: dict = {}
    declared_source = "unavailable"
    if hasattr(caller_mod, "_predicate_read_fields") and hasattr(
        caller_mod, "_node_write_sets"
    ):
        try:
            writes = caller_mod._node_write_sets()
            declared_source = "derived: _predicate_read_fields x _node_write_sets"
            for n in TAIL:
                ids = sorted(
                    fom
                    for fom in range(1, 20)
                    if _fom_reads_node(caller_mod, fom, n, writes)
                )
                declared[n] = ids
        except Exception as exc:  # noqa: BLE001
            declared_source = f"derivation failed: {type(exc).__name__}: {exc}"
    elif hasattr(caller_mod, "_FOM_READS_NODE"):
        declared = {
            node: sorted(ids)
            for node, ids in caller_mod._FOM_READS_NODE.items()
        }
        declared_source = "table: _FOM_READS_NODE (pre-A26)"
    result["declared_source"] = declared_source
    measured = {n: sorted(moved[n]) for n in TAIL}
    result["declared_fom_reads_node"] = declared
    result["measured_fom_moves_across_node"] = measured
    result["declaration_covers_measurement"] = (
        declared_source != "unavailable"
        and all(set(measured[n]) <= set(declared.get(n, [])) for n in TAIL)
    )
    (outdir / "predicate_probe.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k != "traceback"}, indent=2))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
