"""The read-before-write census: which coupling-state components a loop carries.

The instrument behind V5's test set (V5 plan §3; decision D32).  Installed in
the optimisation child when :data:`VARIABLE` is ``on``, it observes every
sweep of every block loop of a whole optimisation and records, per
evaluation and per block, the components of the coupling state ``y`` that a
sweep **reads before it first writes them** and writes later in the same
sweep.  Those are the components through which one sweep's output depends on
the previous sweep's, and so exactly what a loop must test to know it has
stopped moving (the rule below).  Everything else is recomputed from this
sweep's values and is determined once those are fixed.

**The rule.**  In one Gauss–Seidel sweep a read of component ``k`` sees
either a value written earlier *in the same sweep* or — when nothing has
written ``k`` yet in this sweep — the value the previous sweep left.  Only the
second kind carries information between sweeps.  A component is *carried*
when some observed sweep reads it before its first write in that sweep and
writes it later in the same sweep.  This covers the two cases a static
dependency model cannot separate: a model reading another model's output that
runs later in the order (a feedback edge), and a model reading its own
previous output (self-carried state); and it is measured in the execution
order the arm actually runs, block by block, so the partitioned arm's
rearrangement is accounted for.

**How it is observed.**

* reads: ``__getattribute__`` on every data-structure namespace class,
  restricted to the fields of ``y``;
* writes: ``__setattr__`` on the same classes, **plus** a value snapshot of
  every component of ``y`` around every node call, because an in-place array
  mutation never reaches ``__setattr__``.  The snapshot is taken around every
  node whatever a component's type was when the hooks were installed — a
  component that is a list default before the first evaluation and a scalar
  after it is a *type change*, counted as a write (trap T18: a snapshot typed
  once at install is wrong on a cold start).  An in-place mutation is preceded
  by the fetch of the array, so it is recorded as read-then-write and the
  component is **included** — the conservative direction;
* the window is one ``Caller._sweep_block`` call (one sweep of one block, or
  of the flat block); a node is one ``Caller._node`` dispatch; an evaluation
  is one ``Caller.call_models``.  The output path's once-per-run sweep on a
  fresh Caller and the exit audit's sweep are outside every evaluation: the
  first is recorded under the label ``?`` (its node set is no block of the
  schedule) and reaches no evaluation record; the second calls
  ``_call_models_once`` directly and is never seen.

**What it cannot see**: a read through a reference a model kept from an
earlier sweep rather than fetched through the data structure, and coupling
through attributes on model objects, which ``y`` does not hold at all.  The
census is a union over every sweep of the runs it is taken in; a branch never
taken in those runs is never observed (V5 plan §12).

**Observation only.**  Nothing here changes what a loop tests or decides: the
hooks read and record.  The stage that installs it checks, per censused run,
that the run reproduces its uncensused twin on status, exit code, iterations,
evaluations, solve-phase node calls and ``norm_objf`` to the bit.

Ported from ``arch_surgery/coupling_subset_trial/rbw_census.py`` (task A89
(coupling-subset-trial), the instrument; task A92 (optimisation-path-census),
the per-evaluation records and the type-robust snapshot) by task A100
(v5-test-set), as the harness's own module: the prototype reached the driver
through wrappers installed from outside the folder, this one is installed by
the child that makes the record.
"""

from __future__ import annotations

import json
import os
from dataclasses import fields as dc_fields
from pathlib import Path
from typing import Any

import numpy as np

#: The environment variable that installs the census.  **Not** a
#: ``PROCESS_ARCH_`` name: it is a harness instrument and the driver has never
#: heard of it, so it cannot be mistaken for a switch, cannot be cleared as
#: one, and cannot change what any arm is.  The pool digests it, so a censused
#: run is a different job identity from its uncensused twin.
VARIABLE = "HARNESS_READ_BEFORE_WRITE_CENSUS"

#: The value that installs the instrument.  Anything else — ``off``, the
#: twin's value, or the variable unset — installs nothing and the child is
#: byte-identical to one without this module in the tree.
ON = "on"
OFF = "off"

#: Where the census goes: its own file beside the record, never inside it.
#: The record is what the switch-neutrality gate compares value for value.
FILE = "read_before_write_census.json"

FORMAT = "read-before-write-census-1"

#: The label given to a sweep whose node set is no block of the schedule —
#: the output path's once-per-run sweep on a fresh Caller.
UNLABELLED = "?"


def wanted() -> bool:
    """Whether this child was asked to take the census."""
    return os.environ.get(VARIABLE, "").strip() == ON


def _snapshot(data, keys: list[tuple[str, str]]) -> dict:
    """Every component of ``y``, as it stands now, whatever its type.

    Arrays are copied, sequences listed, scalars held.  Never typed once at
    install (trap T18).
    """
    out: dict = {}
    for ns, fld in keys:
        v = getattr(getattr(data, ns), fld)
        if isinstance(v, np.ndarray):
            out[(ns, fld)] = np.array(v, copy=True)
        elif isinstance(v, (list, tuple)):
            out[(ns, fld)] = list(v)
        else:
            out[(ns, fld)] = v
    return out


def _changed(a, b) -> bool:
    """Whether a component's value changed across a node; a type change counts."""
    seq = (np.ndarray, list, tuple)
    if isinstance(a, seq) or isinstance(b, seq):
        if not (isinstance(a, seq) and isinstance(b, seq)):
            return True
        try:
            return not np.array_equal(np.asarray(a), np.asarray(b), equal_nan=True)
        except Exception:  # noqa: BLE001 - an incomparable pair is a change
            return True
    if a is b:
        return False
    try:
        if a != a and b != b:
            return False  # both NaN
        return bool(a != b)
    except Exception:  # noqa: BLE001
        return True


def install(caller_mod, data, spec) -> dict[str, Any]:
    """Install the census on the driver's classes and ``Caller``.  Once per process.

    *data* is the run's data structure, *spec* the coupling-state spec the
    driver loaded (``module_solve.load_spec``).  Returns the state the census
    accumulates into; :func:`write` renders it.
    """
    state: dict[str, Any] = {
        "on": False,          # recording is on inside a sweep window only
        "node": None,         # the node executing now
        "first": None,        # key -> ("r"|"w", node): the first touch this sweep
        "carried": None,      # key -> (reader, writer): read before first write, written later
        "sweeps_by_block": {},
        "by_block": {},       # label -> key -> {"reader","writer","n_sweeps"}
        "evaluations": [],    # per call_models
        "current": None,
        "prev_x": None,
        "label_of": {},       # frozenset(nodes) -> block label, from the schedule
        "n_snapshots": 0,
    }
    keys = list(spec.keys)
    key_names = [spec.name(i) for i in range(len(keys))]
    key_index = {name: i for i, name in enumerate(key_names)}
    state["keys"] = key_names

    y_by_ns: dict[str, set[str]] = {}
    for ns, fld in keys:
        y_by_ns.setdefault(ns, set()).add(fld)
    classes: dict[type, tuple[str, frozenset[str]]] = {}
    for f in dc_fields(data):
        ns = getattr(data, f.name)
        if f.name in y_by_ns:
            if type(ns) in classes:
                raise RuntimeError(
                    f"two coupling-state namespaces share one class "
                    f"({type(ns).__name__}); the read hook cannot tell them apart"
                )
            classes[type(ns)] = (f.name, frozenset(y_by_ns[f.name]))

    def record(key: str, kind: str) -> None:
        first = state["first"]
        if first is None:
            return
        f = first.get(key)
        if f is None:
            first[key] = (kind, state["node"])
        elif f[0] == "r" and kind == "w" and key not in state["carried"]:
            state["carried"][key] = (f[1], state["node"])

    for cls, (ns_name, fset) in classes.items():
        def make(ns_name=ns_name, fset=fset):
            def ga(self, name):
                if state["on"] and name in fset:
                    record(f"{ns_name}.{name}", "r")
                return object.__getattribute__(self, name)

            def sa(self, name, value):
                if state["on"] and name in fset:
                    record(f"{ns_name}.{name}", "w")
                object.__setattr__(self, name, value)
            return ga, sa
        ga, sa = make()
        cls.__getattribute__ = ga
        cls.__setattr__ = sa

    def snap() -> dict:
        on, state["on"] = state["on"], False
        try:
            return _snapshot(data, keys)
        finally:
            state["on"] = on
            state["n_snapshots"] += 1

    orig_node = caller_mod.Caller._node

    def _node(self, name, run):
        if not state["on"] or (
            self._active_nodes is not None and name not in self._active_nodes
        ):
            return orig_node(self, name, run)
        prev, state["node"] = state["node"], name
        before = snap()
        try:
            return orig_node(self, name, run)
        finally:
            after = snap()
            for k, v in before.items():
                if _changed(v, after[k]):
                    record(f"{k[0]}.{k[1]}", "w")
            state["node"] = prev

    caller_mod.Caller._node = _node

    # Which block a node set is, captured from the schedule the driver
    # resolves (once per run since DR9; the wrapper sees every call).
    orig_resolve = caller_mod.resolve_schedule

    def resolve_schedule(i_figure_merit):
        resolved = orig_resolve(i_figure_merit)
        schedule = resolved[2]
        for label, nodes, _iterate in schedule:
            state["label_of"][frozenset(nodes)] = label
        return resolved

    caller_mod.resolve_schedule = resolve_schedule

    orig_sweep = caller_mod.Caller._sweep_block

    def _sweep_block(self, xc, nodes):
        label = state["label_of"].get(frozenset(nodes), UNLABELLED)
        state.update(on=True, node="<sweep>", first={}, carried={})
        try:
            return orig_sweep(self, xc, nodes)
        finally:
            state["on"] = False
            rec = state["by_block"].setdefault(label, {})
            for key, (reader, writer) in state["carried"].items():
                e = rec.setdefault(key, {"reader": reader, "writer": writer, "n_sweeps": 0})
                e["n_sweeps"] += 1
            state["sweeps_by_block"][label] = state["sweeps_by_block"].get(label, 0) + 1
            cur = state["current"]
            if cur is not None:
                cur["sweeps"][label] = cur["sweeps"].get(label, 0) + 1
                cur["carried"].setdefault(label, set()).update(
                    key_index[k] for k in state["carried"]
                )
            state.update(first=None, carried=None)

    caller_mod.Caller._sweep_block = _sweep_block

    orig_call_models = caller_mod.Caller.call_models

    def call_models(self, xc, m):
        x = np.array(xc, dtype=float, copy=True)
        prev = state["prev_x"]
        if prev is None or prev.shape != x.shape:
            n_changed, changed = None, None
        else:
            moved = np.flatnonzero(prev != x)
            n_changed = int(moved.size)
            changed = int(moved[0]) if moved.size == 1 else None
        state["prev_x"] = x
        state["current"] = {
            "i": len(state["evaluations"]),
            "n_x_changed": n_changed,
            "x_changed_index": changed,
            "sweeps": {},
            "carried": {},
        }
        try:
            return orig_call_models(self, xc, m)
        finally:
            cur = state["current"]
            cur["carried"] = {label: sorted(v) for label, v in cur["carried"].items()}
            state["evaluations"].append(cur)
            state["current"] = None

    caller_mod.Caller.call_models = call_models
    return state


def union_by_block(state: dict[str, Any]) -> dict[str, list[str]]:
    """The carried set per block, union over every observed sweep, as key names."""
    return {
        label: sorted(entries)
        for label, entries in sorted(state["by_block"].items())
    }


def write(state: dict[str, Any], outdir: Path) -> Path:
    """The census, to its own file beside the record."""
    path = Path(outdir) / FILE
    path.write_text(
        json.dumps(
            {
                "format": FORMAT,
                "rule": (
                    "a component of y that, in some observed sweep of the "
                    "block, is read before it is first written in that sweep "
                    "and written later in it; observed over every evaluation "
                    "of this run"
                ),
                "keys": state["keys"],
                "n_components": len(state["keys"]),
                "n_evaluations": len(state["evaluations"]),
                "n_snapshots": state["n_snapshots"],
                "sweeps_observed_by_block": dict(sorted(state["sweeps_by_block"].items())),
                "union_by_block": union_by_block(state),
                "n_by_block": {
                    label: len(entries)
                    for label, entries in sorted(state["by_block"].items())
                },
                "detail_by_block": {
                    label: dict(sorted(entries.items()))
                    for label, entries in sorted(state["by_block"].items())
                },
                "what": {
                    "i": "evaluation index: the n-th call_models of the run, from 0",
                    "n_x_changed": (
                        "design-vector components that differ from the previous "
                        "evaluation's vector (null on the first evaluation)"
                    ),
                    "x_changed_index": (
                        "the one moved component when exactly one moved (a "
                        "finite-difference probe), else null"
                    ),
                    "sweeps": "sweeps of each block in this evaluation",
                    "carried": (
                        "per block, indices into `keys` of the components read "
                        "before their first write in at least one sweep of this "
                        "evaluation"
                    ),
                    UNLABELLED: (
                        "a sweep whose node set is no block of the schedule: the "
                        "output path's once-per-run sweep; not a loop, not a set"
                    ),
                },
                "evaluations": state["evaluations"],
            }
        )
    )
    return path
