"""Read-before-write census: which coupling-state components a loop carries.

Task A89 (coupling-subset-trial), proof of principle of the structural fix.

**The rule.**  In one Gauss–Seidel sweep, a read of component ``k`` sees either
a value written earlier *in the same sweep*, or — if nothing has written ``k``
yet in this sweep — the value the **previous** sweep left.  Only the second kind
makes the sweep's output depend on the previous sweep through ``k``.  So a loop
must test exactly the components that are **read before they are first written
within one of its sweeps** (and written later in it).  Everything else is
recomputed from this sweep's values and is determined once those are fixed.

This covers both cases the DSM cannot separate — a model reading another
model's output that runs later (a feedback edge), and a model reading its own
previous output (a self-read that is carried state) — and it is measured in
the execution order the arm actually runs, block by block, so the partitioned
arm's rearrangement is accounted for.

**How it is observed.**

* reads: ``__getattribute__`` on every data-structure namespace class,
  restricted to the fields of ``y``;
* writes: ``__setattr__`` on the same classes, plus a value diff of every
  array/list-valued ``y`` field across each node, because an in-place array
  mutation never reaches ``__setattr__``.  An in-place mutation is preceded by
  the ``getattr`` that fetched the array, so it is recorded as read-then-write:
  the component is **included** — the conservative direction;
* the window is one ``Caller._sweep_block`` call (one sweep of one block, or
  of the flat block); a node is one ``Caller._node`` dispatch.  The exit audit
  and the once-per-run execution are not recorded: the first calls
  ``_call_models_once`` directly, the second is flagged by :mod:`narrowing`.

**What it cannot see**: a read through a reference a model kept from an
earlier sweep rather than fetched through the data structure, and coupling
through attributes on model objects, which ``y`` does not hold at all.

The census is a union over every sweep of the runs it is taken in; a branch
never taken in those runs is never observed.

**Per-evaluation recording** (task A92 (optimisation-path-census), additive).
With :func:`enable_per_evaluation` on, every ``call_models`` the wrapper
brackets with :func:`begin_evaluation` / :func:`end_evaluation` gets its own
record: the sweeps per block and the read-before-write set per block of
*that* evaluation, plus how many design-vector components moved since the
previous evaluation (one moved component is a finite-difference probe).  The
aggregate ``RESULT`` and the ``rbw_census.json`` :func:`write` produces are
unchanged; the per-evaluation series goes to its own file
(:func:`write_per_evaluation`), so A89's ``--derive-rbw`` reads what it read.
A sweep outside any evaluation — the once-per-run set that
``write_output_files`` sweeps on a fresh Caller — still reaches ``RESULT``
(under the label ``?``, since its node set is no block of the schedule) and
reaches no evaluation record.
"""

from __future__ import annotations

import json
from dataclasses import fields as dc_fields
from pathlib import Path

import numpy as np

import narrowing as narrowing_mod  # the once-per-run flag is shared with it

_S: dict = {"on": False, "node": None, "label": None, "first": None,
            "rbw": None, "installed": False, "arrays": None, "sweeps": {},
            # per-evaluation recording (A92): None = off; a list once enabled
            "per_eval": None, "current": None, "prev_x": None, "key_index": None,
            "key_names": None}
RESULT: dict = {}   # label -> {key: {"reader": node, "writer": node, "n": windows}}


def enable_per_evaluation():
    """Record each bracketed evaluation separately (see the module docstring)."""
    if _S["per_eval"] is None:
        _S["per_eval"] = []


def begin_evaluation(xc):
    """Open the record of one ``call_models``; *xc* is the design vector it gets."""
    if _S["per_eval"] is None:
        return
    x = np.array(xc, dtype=float, copy=True)
    prev = _S["prev_x"]
    if prev is None or prev.shape != x.shape:
        n_changed, changed = None, None
    else:
        moved = np.flatnonzero(prev != x)
        n_changed = int(moved.size)
        changed = int(moved[0]) if moved.size == 1 else None
    _S["prev_x"] = x
    _S["current"] = {"i": len(_S["per_eval"]), "n_x_changed": n_changed,
                     "x_changed_index": changed, "sweeps": {}, "rbw": {}}


def end_evaluation():
    """Close the open evaluation record (a raise inside the evaluation closes it too)."""
    cur = _S["current"]
    if cur is None:
        return
    cur["rbw"] = {label: sorted(v) for label, v in cur["rbw"].items()}
    _S["per_eval"].append(cur)
    _S["current"] = None


def _record(key, kind):
    first = _S["first"]
    if first is None:
        return
    f = first.get(key)
    if f is None:
        first[key] = (kind, _S["node"])
    elif f[0] == "r" and kind == "w" and key not in _S["rbw"]:
        _S["rbw"][key] = (f[1], _S["node"])


def install(caller_mod, ms, data, spec):
    if _S["installed"]:
        return
    _S["installed"] = True
    y_by_ns: dict = {}
    for ns, fld in spec.keys:
        y_by_ns.setdefault(ns, set()).add(fld)
    classes = {}
    for f in dc_fields(data):
        ns = getattr(data, f.name)
        if f.name in y_by_ns:
            if type(ns) in classes:
                raise RuntimeError(f"namespace class shared: {type(ns)}")
            classes[type(ns)] = (f.name, frozenset(y_by_ns[f.name]))
    array_keys = []
    for ns, fld in spec.keys:
        v = object.__getattribute__(getattr(data, ns), fld)
        if isinstance(v, (np.ndarray, list)):
            array_keys.append((ns, fld))
    _S["array_keys"] = array_keys
    _S["data"] = data
    _S["key_names"] = [spec.name(i) for i in range(len(spec.keys))]
    _S["key_index"] = {name: i for i, name in enumerate(_S["key_names"])}

    for cls, (ns_name, fset) in classes.items():
        def make(ns_name=ns_name, fset=fset):
            def ga(self, name):
                if _S["on"] and name in fset:
                    _record(f"{ns_name}.{name}", "r")
                return object.__getattribute__(self, name)

            def sa(self, name, value):
                if _S["on"] and name in fset:
                    _record(f"{ns_name}.{name}", "w")
                object.__setattr__(self, name, value)
            return ga, sa
        ga, sa = make()
        cls.__getattribute__ = ga
        cls.__setattr__ = sa

    def snap():
        on, _S["on"] = _S["on"], False
        out = {}
        for ns, fld in _S["array_keys"]:
            v = getattr(getattr(data, ns), fld)
            out[(ns, fld)] = np.array(v, copy=True) if isinstance(v, np.ndarray) else list(v)
        _S["on"] = on
        return out

    def changed(a, b):
        try:
            return not np.array_equal(np.asarray(a), np.asarray(b), equal_nan=True)
        except Exception:
            return True

    orig_node = caller_mod.Caller._node

    def _node(self, name, run):
        if not _S["on"] or (self._active_nodes is not None and name not in self._active_nodes):
            return orig_node(self, name, run)
        prev, _S["node"] = _S["node"], name
        before = snap()
        try:
            return orig_node(self, name, run)
        finally:
            after = snap()
            for k, v in before.items():
                if changed(v, after[k]):
                    _record(f"{k[0]}.{k[1]}", "w")
            _S["node"] = prev

    caller_mod.Caller._node = _node

    # which block a node set is: captured from the schedule the driver builds
    orig_schedule = caller_mod.module_schedule
    label_of: dict = {}

    def module_schedule(fom):
        schedule, tail = orig_schedule(fom)
        for label, nodes, _it in schedule:
            label_of[frozenset(nodes)] = label
        return schedule, tail

    caller_mod.module_schedule = module_schedule

    orig_sweep = caller_mod.Caller._sweep_block

    def _sweep_block(self, xc, nodes):
        if narrowing_mod.STATE.get("in_once"):
            return orig_sweep(self, xc, nodes)
        label = label_of.get(frozenset(nodes), "?")
        _S.update(on=True, node="<sweep>", first={}, rbw={})
        try:
            return orig_sweep(self, xc, nodes)
        finally:
            _S["on"] = False
            rec = RESULT.setdefault(label, {})
            for key, (reader, writer) in _S["rbw"].items():
                e = rec.setdefault(key, {"reader": reader, "writer": writer, "n": 0})
                e["n"] += 1
            _S["sweeps"][label] = _S["sweeps"].get(label, 0) + 1
            cur = _S["current"]
            if cur is not None:
                cur["sweeps"][label] = cur["sweeps"].get(label, 0) + 1
                idx = _S["key_index"]
                cur["rbw"].setdefault(label, set()).update(idx[k] for k in _S["rbw"])
            _S.update(first=None, rbw=None)

    caller_mod.Caller._sweep_block = _sweep_block


def write(path):
    Path(path).write_text(json.dumps({
        "format": "rbw-census-1",
        "sweeps_observed_by_block": _S["sweeps"],
        "rbw_by_block": RESULT,
    }, indent=1))


def write_per_evaluation(path):
    """The per-evaluation series: keys by the spec's index, one record per evaluation."""
    Path(path).write_text(json.dumps({
        "format": "rbw-census-per-evaluation-1",
        "keys": _S["key_names"],
        "what": {
            "i": "evaluation index: the n-th call_models of the run, from 0",
            "n_x_changed": "design-vector components that differ from the previous "
                           "evaluation's vector (null on the first evaluation)",
            "x_changed_index": "the one moved component when exactly one moved "
                               "(a finite-difference probe), else null",
            "sweeps": "sweeps of each block in this evaluation",
            "rbw": "per block, indices into `keys` of the components read before "
                   "their first write in at least one sweep of this evaluation",
        },
        "n_evaluations": len(_S["per_eval"] or []),
        "evaluations": _S["per_eval"] or [],
    }))
