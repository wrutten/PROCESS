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
"""

from __future__ import annotations

import json
from dataclasses import fields as dc_fields
from pathlib import Path

import numpy as np

import narrowing as narrowing_mod  # the once-per-run flag is shared with it

_S: dict = {"on": False, "node": None, "label": None, "first": None,
            "rbw": None, "installed": False, "arrays": None, "sweeps": {}}
RESULT: dict = {}   # label -> {key: {"reader": node, "writer": node, "n": windows}}


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
            _S.update(first=None, rbw=None)

    caller_mod.Caller._sweep_block = _sweep_block


def write(path):
    Path(path).write_text(json.dumps({
        "format": "rbw-census-1",
        "sweeps_observed_by_block": _S["sweeps"],
        "rbw_by_block": RESULT,
    }, indent=1))
