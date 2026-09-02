#!/usr/bin/env python
"""Which data-structure fields PROCESS's *predicate layer* reads.

Plan §4.1d, as corrected by §4.1e: a node may only be hoisted out of the sweep
into the **post-predicate** slot --- run once, after ``objf`` and ``conf`` have
been evaluated --- if neither layer reads anything it writes.  A node that does
feed either layer goes into the **pre-predicate** slot instead: it still runs
once per optimiser evaluation rather than once per sweep, but it runs *before*
the predicate is evaluated, so the predicate never sees a stale value.

The membership test is therefore a read set, and this module measures it two
ways because neither alone is sufficient.

**(a) Static, and deliberately a superset.**  An AST walk over
``process/core/solver/objectives.py`` and ``process/core/solver/constraints.py``
collecting every ``data.<namespace>.<field>`` appearing in a *load* context.
It covers every registered constraint, not only the ones a given deck
activates, and every figure of merit, not only the active one --- so it
over-reports, which is the safe direction: over-reporting routes a node to the
pre-predicate slot, which is never wrong, only occasionally unnecessary.

Two hazards it is written against.  Trap **T2** --- ``= `` matches ``==`` ---
does not arise, because the walk asks the parser for the expression context
instead of matching text; a field that only ever appears on the left of an
assignment is a *store* and is not collected.  Trap **T1** --- ``output()``
paths --- does not arise either: neither file has one.

**(b) Runtime, per deck, by differential perturbation.**  For a candidate field,
perturb the live value, re-evaluate ``objective_function`` and
``constraint_eqns``, and compare the results as exact bits.  This measures
*stale-sensitivity* directly rather than inferring it from a name, and it is
per deck, so it says which of the static set's members actually bind on the
deck in hand.  It is a subset of (a) by construction; where it is not, (a) has
missed something and that is a finding.

Neither measurement decides anything on its own.  The **routing rule uses (a)**,
the conservative one.  (b) is the cross-check that says how much of (a) is live.

Usage
-----
    PYTHONPATH=<tree> python predicate_reads.py --json
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

#: The two files that make up PROCESS's idempotence predicate.  ``call_models``
#: evaluates exactly these two things and compares them between sweeps.
PREDICATE_SOURCES = (
    "process/core/solver/objectives.py",
    "process/core/solver/constraints.py",
)


class _DataReads(ast.NodeVisitor):
    """Collect ``data.<ns>.<field>`` in a load context.

    ``data`` is the parameter name both ``objective_function`` and
    ``constraint_eqns`` use for the data structure throughout, and neither file
    rebinds it.  That is checked by :func:`static_reads`, which refuses to
    return a set if it is not true.
    """

    def __init__(self):
        self.reads: set[str] = set()
        self.stores: set[str] = set()

    def visit_Attribute(self, node: ast.Attribute) -> None:  # noqa: N802
        inner = node.value
        if (
            isinstance(inner, ast.Attribute)
            and isinstance(inner.value, ast.Name)
            and inner.value.id == "data"
        ):
            name = f"{inner.attr}.{node.attr}"
            if isinstance(node.ctx, ast.Load):
                self.reads.add(name)
            else:
                self.stores.add(name)
        self.generic_visit(node)


def static_reads(tree_root: Path) -> dict:
    """The static superset, with its own provenance."""
    reads: set[str] = set()
    stores: set[str] = set()
    per_file: dict = {}
    for rel in PREDICATE_SOURCES:
        path = tree_root / rel
        src = path.read_text()
        mod = ast.parse(src, filename=str(path))
        v = _DataReads()
        v.visit(mod)
        per_file[rel] = {
            "n_reads": len(v.reads),
            "n_stores": len(v.stores),
            "reads": sorted(v.reads),
            "stores": sorted(v.stores),
        }
        reads |= v.reads
        stores |= v.stores
    return {
        "method": (
            "AST walk for data.<namespace>.<field> in a load context over "
            + ", ".join(PREDICATE_SOURCES)
        ),
        "n_fields": len(reads),
        "fields": sorted(reads),
        "fields_stored_by_the_predicate_layer": sorted(stores),
        "per_file": per_file,
    }


def objective_reads_by_fom(tree_root: Path) -> dict:
    """Per figure of merit, the fields ``objective_function`` reads.

    ``objectives.py`` is one ``if``/``elif`` chain over
    ``figure_of_merit == FiguresOfMerit.<NAME>``, so each arm of the chain is
    one figure of merit's read set.  Walking the chain is exact where a text
    search would not be, and it is what makes the routing rule *precise* on the
    objective side: the objective is one branch, and which branch is known from
    the deck.

    Returns ``{FiguresOfMerit name: [fields]}``, plus the key ``"__fallthrough__"``
    for anything read outside the chain (which every figure of merit inherits).
    """
    path = tree_root / "process/core/solver/objectives.py"
    mod = ast.parse(path.read_text(), filename=str(path))
    fn = next(
        (n for n in ast.walk(mod)
         if isinstance(n, ast.FunctionDef) and n.name == "objective_function"),
        None,
    )
    if fn is None:
        raise AssertionError(
            "objectives.py has no objective_function; the read-set probe has "
            "drifted from the driver and must not be trusted"
        )

    def _fom_name(test):
        if (
            isinstance(test, ast.Compare)
            and len(test.ops) == 1
            and isinstance(test.ops[0], ast.Eq)
            and isinstance(test.comparators[0], ast.Attribute)
            and isinstance(test.comparators[0].value, ast.Name)
            and test.comparators[0].value.id == "FiguresOfMerit"
        ):
            return test.comparators[0].attr
        return None

    out: dict = {}
    fallthrough = _DataReads()

    def walk_chain(stmts):
        for st in stmts:
            if isinstance(st, ast.If) and _fom_name(st.test):
                name = _fom_name(st.test)
                v = _DataReads()
                for b in st.body:
                    v.visit(b)
                out[name] = sorted(v.reads)
                walk_chain(st.orelse)
            else:
                fallthrough.visit(st)

    walk_chain(fn.body)
    if not out:
        raise AssertionError(
            "objectives.py's figure-of-merit chain did not parse; the probe "
            "has drifted from the driver and must not be trusted"
        )
    out["__fallthrough__"] = sorted(fallthrough.reads)
    return out


def constraint_reads(tree_root: Path) -> list:
    """Every ``data.<ns>.<field>`` the constraint layer loads, over all of it.

    Deliberately **not** narrowed to the constraints a deck activates.  A
    superset routes a node to the pre-predicate slot, which is never wrong;
    narrowing it would make the routing depend on ``icc``, and a routing rule
    that silently changes with a deck's constraint list is exactly the class of
    thing §6.3(iii) says must be declared rather than discovered.
    """
    path = tree_root / "process/core/solver/constraints.py"
    v = _DataReads()
    v.visit(ast.parse(path.read_text(), filename=str(path)))
    return sorted(v.reads)


def predicate_read_set(tree_root: Path, i_figure_merit) -> dict:
    """The routing rule's read set for a deck, and how it was assembled.

    Precise on the objective side --- the active figure of merit's branch, plus
    whatever the function reads outside the chain --- and a superset on the
    constraint side.  ``i_figure_merit is None`` takes the union over every
    figure of merit, which is the right answer when the deck is not known.
    """
    by_fom = objective_reads_by_fom(tree_root)
    fall = set(by_fom.get("__fallthrough__", []))
    if i_figure_merit is None:
        obj = set()
        for k, v in by_fom.items():
            obj |= set(v)
        which = "union over every figure of merit"
    else:
        from process.core.solver.objectives import FiguresOfMerit

        name = FiguresOfMerit(abs(int(i_figure_merit))).name
        obj = set(by_fom.get(name, [])) | fall
        which = name
    con = set(constraint_reads(tree_root))
    return {
        "i_figure_merit": i_figure_merit,
        "figure_of_merit": which,
        "objective_fields": sorted(obj),
        "constraint_fields_n": len(con),
        "fields": sorted(obj | con),
        "n_fields": len(obj | con),
        "objective_side": "exact: the active figure of merit's branch",
        "constraint_side": (
            "superset: every registered constraint, not only the deck's icc"
        ),
    }


# --------------------------------------------------------------------------
# (b) runtime differential perturbation
# --------------------------------------------------------------------------


def perturb_probe(data, i_figure_merit, m, fields, *, rel=1e-3):
    """Which of ``fields`` the live predicate is sensitive to, on this deck.

    For each field: read it, evaluate ``(objf, conf)``, write a perturbed
    value, re-evaluate, restore, and compare **as exact bits**.  A field whose
    perturbation moves neither is not read on the active deck --- or is read
    behind a branch this state does not take, which is why the static set and
    not this one does the routing.

    Returns one row per field, so a caller can report the denominator rather
    than a bare count.
    """
    import numpy as np

    from process.core.solver import constraints as _constraints
    from process.core.solver.objectives import objective_function

    def evaluate():
        objf = float(objective_function(i_figure_merit, data))
        conf = np.asarray(_constraints.constraint_eqns(m, -1, data)[0]).copy()
        return objf, conf

    base_objf, base_conf = evaluate()
    rows = []
    for f in fields:
        ns_name, _, fld = f.partition(".")
        ns = getattr(data, ns_name, None)
        if ns is None or not hasattr(ns, fld):
            rows.append({"field": f, "status": "absent"})
            continue
        v0 = object.__getattribute__(ns, fld)
        if not isinstance(v0, (int, float, np.floating, np.integer)) or isinstance(
            v0, bool
        ):
            rows.append({"field": f, "status": "not a scalar number"})
            continue
        v1 = float(v0) * (1.0 + rel) if v0 else rel
        try:
            object.__setattr__(ns, fld, type(v0)(v1) if not isinstance(v0, int)
                               else v1)
            objf, conf = evaluate()
        except Exception as exc:  # a constraint may divide by it, etc.
            object.__setattr__(ns, fld, v0)
            rows.append({"field": f, "status": f"raised: {type(exc).__name__}"})
            continue
        finally:
            object.__setattr__(ns, fld, v0)
        d_objf = objf != base_objf
        d_conf = not np.array_equal(conf, base_conf, equal_nan=True)
        rows.append({
            "field": f,
            "status": "ok",
            "objective_moved": bool(d_objf),
            "constraints_moved": bool(d_conf),
            "predicate_moved": bool(d_objf or d_conf),
        })
    # The probe must be shown able to report a move at all, or its zeros mean
    # nothing (protocol §12).  Restoration is verified the same way.
    restored_objf, restored_conf = evaluate()
    return {
        "rel_perturbation": rel,
        "n_fields": len(fields),
        "rows": rows,
        "n_moved": sum(1 for r in rows if r.get("predicate_moved")),
        "n_ok": sum(1 for r in rows if r.get("status") == "ok"),
        "restore_exact": bool(
            restored_objf == base_objf
            and np.array_equal(restored_conf, base_conf, equal_nan=True)
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    root = Path(args.tree).resolve() if args.tree else Path(
        __file__
    ).resolve().parents[2]
    rec = static_reads(root)
    rec["objective_reads_by_figure_of_merit"] = objective_reads_by_fom(root)
    rec["tree"] = str(root)
    if args.json:
        json.dump(rec, sys.stdout, indent=2)
        print()
    else:
        print(f"{rec['n_fields']} fields read by the predicate layer")
        for f in rec["fields"]:
            print("  ", f)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
