"""Module-attribution instrument for Stage 1 of the MDA partitioning experiment.

Imported **only** when ``PROCESS_IDF_PROBE=modules``.  With any other value, or
with the variable unset, this file is never imported and costs nothing, so
switch-neutrality holds by construction.

What it measures
----------------

**Per-module convergence.**  ``Caller.call_models`` runs the model sequence
repeatedly (each pass is a *sweep*) until the objective function and the
constraint vector stop changing.  That yields one number, ``S_global``.  This
instrument attributes the state change of each sweep to individual model
nodes, and from there to the three candidate modules of the partition
(M1 Physics, M2 Coils, M3 Plant), giving the counterfactual ``S_1``, ``S_2``,
``S_3`` -- how many sweeps each module would need if iterated alone -- from
the *existing* architecture, with no refactor.

**Cross-module data flow.**  Every read and every write of a data-structure
field is attributed to the model node executing at the time, so a dependency
edge is established by observing traffic rather than by reading a call graph.
Recording is confined to the body of ``Caller._call_models_once`` and to the
objective/constraint evaluation, i.e. to ``run()`` paths.  The ``output()``
methods execute outside that window, so they are excluded structurally rather
than by a name filter (trap T1).

How attribution works
---------------------

*Writes* are captured two ways and the union is used:

1. ``__setattr__`` is overridden on every ``*Data`` dataclass, so a plain
   assignment ``self.data.physics.rmajor = ...`` is recorded exactly.
2. A full snapshot of the data structure is taken at each node boundary and
   consecutive snapshots are differenced, which catches in-place mutation of
   numpy arrays (``arr[:] = ...``) -- that never reaches ``__setattr__``.

*Reads* are captured by overriding ``__getattribute__`` on the same classes.
That is expensive, so it runs only for a bounded budget of sweeps plus a
periodic sample thereafter; the summary reports how many sweeps the read
census covers and how the discovered edge set grew, so saturation can be
judged rather than assumed.

Nothing here mutates model state: the only writes are to this module's own
bookkeeping.
"""

from __future__ import annotations

import os
import time
from collections import Counter
from dataclasses import fields as dc_fields

import numpy as np

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

#: Track attribute *reads* on every sweep up to this global sweep index.  The
#: default is effectively unbounded: a complete read census is what makes the
#: coupler result a measurement rather than a sample.  Lower it (e.g. 200) to
#: trade completeness for speed on a long run.
READ_BUDGET = int(os.environ.get("PROCESS_IDF_PROBE_READ_BUDGET", "1000000000"))

#: After the budget is spent, track reads on every Nth sweep, so a branch first
#: taken late in the optimisation still enters the census.  0 disables it.
READ_STRIDE = int(os.environ.get("PROCESS_IDF_PROBE_READ_STRIDE", "37"))

#: Tolerance of ``Caller.check_agreement``, reproduced exactly so a per-module
#: sweep count is comparable with the global one.
RTOL = 1.0e-6
ATOL = 1.0e-8

#: Module label per node.  Node names are attribute names on
#: ``process.main.Models``, plus two ``Power`` methods, the design-vector
#: injection and the objective/constraint block.  The mapping follows decision
#: D8's collapsed-DSM decomposition: M1 Physics = DSM rows 4 and 6-28,
#: M2 Coils = rows 5 and 29-37, M3 Plant = rows 40-51, ``CsFatigue`` (38) and
#: rows 52-55 feed-forward, ``Pulse`` (39) the articulation point.
NODE_MODULE: dict[str, str] = {
    "<x_inject>": "X",
    # M1 -- Physics (DSM rows 4, 6-28)
    "plasma_geom": "M1",
    "physics": "M1",
    # M2 -- Coils (DSM rows 5, 29-37)
    "build": "M2",
    "cicc_sctfcoil": "M2",
    "croco_sctfcoil": "M2",
    "sctfcoil": "M2",
    "copper_tf_coil": "M2",
    "aluminium_tf_coil": "M2",
    "resistive_tf_coil": "M2",
    "tfcoil": "M2",
    "pfcoil": "M2",
    # the articulation point (DSM row 39)
    "pulse": "PULSE",
    # M3 -- Plant (DSM rows 40-51)
    "divertor": "M3",
    "fw": "M3",
    "shield": "M3",
    "vacuum_vessel": "M3",
    "ccfe_hcpb": "M3",
    "dcll": "M3",
    "cryostat": "M3",
    "structure": "M3",
    "power": "M3",
    "vacuum": "M3",
    "buildings": "M3",
    "power.acpow": "M3",
    "power.plant_electric_production": "M3",
    "availability": "M3",
    # feed-forward outputs (DSM rows 52-55)
    "water_use": "FF",
    "costs": "FF",
    "objective_constraints": "FF",
}

#: Order the modules take in the *post-reorder, post-lift* sequence the
#: partition would impose: all of M1, then all of M2, then ``Pulse``, then M3,
#: then the feed-forward tail.  A read by one module of a field written by a
#: later module is a back edge in that ordering.
MODULE_ORDER = {"X": -1, "M1": 0, "M2": 1, "PULSE": 2, "M3": 3, "FF": 4}

MODULES = ("M1", "M2", "M3")

#: Model objects wrapped as nodes (attribute names on ``Models``).
_WRAP_RUN = (
    "plasma_geom",
    "build",
    "physics",
    "copper_tf_coil",
    "cicc_sctfcoil",
    "croco_sctfcoil",
    "aluminium_tf_coil",
    "resistive_tf_coil",
    "tfcoil",
    "pfcoil",
    "pulse",
    "divertor",
    "fw",
    "shield",
    "vacuum_vessel",
    "ccfe_hcpb",
    "dcll",
    "cryostat",
    "structure",
    "power",
    "vacuum",
    "buildings",
    "availability",
    "water_use",
)


# --------------------------------------------------------------------------
# State
# --------------------------------------------------------------------------

_installed = False
_snap_spec: list = []  # [(ns_name, field_name, ns_object), ...]
_snap_keys: list = []  # [(ns_name, field_name), ...]
_key_index: dict = {}
_field_sets: dict = {}  # ns_name -> (class, frozenset(field names))

#: read/write sets of the node currently executing; None means record nothing
_CUR_READS: set | None = None
_CUR_WRITES: set | None = None

_nodes: list = []
_node_index: dict = {}
_writes_all: dict = {}
_reads_all: dict = {}
_node_calls: Counter = Counter()
#: node -> cumulative seconds spent inside it, excluding this probe's own
#: snapshot work.  Node *cost* is a far better weight for the gate arithmetic
#: than node *count*: ``physics.run()`` and ``cryostat.run()`` are not the same
#: size.  Wall clock cannot resolve a 10 % effect on this machine (I-8), but a
#: cost *share* summed over thousands of sweeps is stable, and it is used only
#: as a weight, never as a timing claim.
_node_time: Counter = Counter()
_t_node: list = []
_nesting_seen: Counter = Counter()
#: ``run()`` invocations reached from an ``output()`` method, refused (trap T1)
_output_path_calls: Counter = Counter()

#: fields observed to change value at least once inside a sweep -- this
#: includes the first assignment away from an initial value, so it is a weak
#: test
_fields_ever_changed: set = set()

#: fields observed to change value *between consecutive sweeps of the same*
#: ``call_models``.  This is the strong test: a dependency edge on a field that
#: never changes between sweeps is degenerate -- it carries a constant, and
#: closing it costs the loop nothing.
_fields_changed_between_sweeps: set = set()

_sweep_open = False
_models_done = False
_sweep_index = 0
_sweep_in_call = 0
_in_call = False
_read_tracking = False
_read_sweeps = 0

_node_stack: list = []
_refused = 0
_last_values: list | None = None
_snaps_cur: dict = {}
_snaps_prev: dict = {}

_module_converged_at: dict = {}
_last_sweep_changes: list = []
_calls: list = []
_changers: Counter = Counter()
_late_changers: Counter = Counter()
_edge_growth: list = []
_module_change_by_sweep: Counter = Counter()


# --------------------------------------------------------------------------
# Snapshot / comparison
# --------------------------------------------------------------------------


def _snapshot() -> list:
    """Full copy of every data-structure field.  Records no reads."""
    global _CUR_READS
    saved = _CUR_READS
    _CUR_READS = None
    vals = []
    ap = vals.append
    for _ns_name, fname, ns in _snap_spec:
        v = getattr(ns, fname)
        c = v.__class__
        if c is np.ndarray:
            v = v.copy()
        elif c is list:
            v = v[:]
        ap(v)
    _CUR_READS = saved
    return vals


def _differs_exact(x, y) -> bool:
    if isinstance(x, np.ndarray) or isinstance(y, np.ndarray):
        try:
            if np.shape(x) != np.shape(y):
                return True
            return not np.array_equal(x, y)
        except Exception:
            return True
    try:
        return bool(x != y)
    except Exception:
        return True


def _diff_keys(before: list, after: list) -> set:
    out = set()
    for i, x in enumerate(before):
        y = after[i]
        if x is y:
            continue
        if x.__class__ is float and y.__class__ is float:
            if x != y:
                out.add(_snap_keys[i])
            continue
        if _differs_exact(x, y):
            out.add(_snap_keys[i])
    return out


def _agrees(previous, current) -> bool:
    """``Caller.check_agreement`` semantics, for an arbitrary field value."""
    try:
        if np.shape(previous) != np.shape(current):
            return False
        return bool(
            np.allclose(previous, current, rtol=RTOL, atol=ATOL, equal_nan=True)
        )
    except Exception:
        return not _differs_exact(previous, current)


# --------------------------------------------------------------------------
# Attribute hooks
# --------------------------------------------------------------------------


def _make_setattr(ns_name):
    def __setattr__(self, name, value):  # noqa: N807
        s = _CUR_WRITES
        if s is not None:
            s.add((ns_name, name))
        object.__setattr__(self, name, value)

    return __setattr__


def _make_getattribute(ns_name, field_set):
    def __getattribute__(self, name):  # noqa: N807
        s = _CUR_READS
        if s is not None and name in field_set:
            s.add((ns_name, name))
        return object.__getattribute__(self, name)

    return __getattribute__


def _read_hooks_on():
    global _read_tracking
    if _read_tracking:
        return
    for ns_name, (cls, field_set) in _field_sets.items():
        cls.__getattribute__ = _make_getattribute(ns_name, field_set)
    _read_tracking = True


def _read_hooks_off():
    global _read_tracking, _CUR_READS
    if not _read_tracking:
        return
    for _ns_name, (cls, _fs) in _field_sets.items():
        try:
            del cls.__getattribute__
        except AttributeError:
            cls.__getattribute__ = object.__getattribute__
    _read_tracking = False
    _CUR_READS = None


# --------------------------------------------------------------------------
# Installation
# --------------------------------------------------------------------------


def _wrap(obj, method_name, node_name):
    original = getattr(obj, method_name)

    def wrapper(*a, **kw):
        node_begin(node_name)
        try:
            return original(*a, **kw)
        finally:
            node_end()

    setattr(obj, method_name, wrapper)


def install(models, data) -> None:
    """Install every hook.  Idempotent; called from the first sweep."""
    global _installed, _snap_spec, _snap_keys
    if _installed:
        return
    _installed = True

    spec = []
    for f in dc_fields(data):
        ns = getattr(data, f.name)
        names = tuple(g.name for g in dc_fields(ns))
        _field_sets[f.name] = (type(ns), frozenset(names))
        for name in names:
            spec.append((f.name, name, ns))
    _snap_spec = spec
    _snap_keys = [(a, b) for a, b, _ in spec]
    _key_index.update({k: i for i, k in enumerate(_snap_keys)})

    for _ns_name, (cls, _fs) in _field_sets.items():
        cls.__setattr__ = _make_setattr(_ns_name)

    for attr in _WRAP_RUN:
        obj = getattr(models, attr, None)
        if obj is not None and hasattr(obj, "run"):
            _wrap(obj, "run", attr)

    costs = models.costs
    if hasattr(costs, "run"):
        _wrap(costs, "run", "costs")

    _wrap(models.power, "acpow", "power.acpow")
    _wrap(models.power, "plant_electric_production", "power.plant_electric_production")

    # The design-vector injection at the top of ``_call_models_once`` is not a
    # model; give it its own pseudo-node so its writes are not charged to the
    # first physics node.
    from process.core import caller as _caller

    _orig_set_x = _caller.set_scaled_iteration_variable

    def _set_x(*a, **kw):
        node_begin("<x_inject>")
        try:
            return _orig_set_x(*a, **kw)
        finally:
            node_end()

    _caller.set_scaled_iteration_variable = _set_x


# --------------------------------------------------------------------------
# Node / sweep lifecycle
# --------------------------------------------------------------------------


def _node_id(name):
    if name not in _node_index:
        _node_index[name] = len(_nodes)
        _nodes.append(name)
        _writes_all[name] = set()
        _reads_all[name] = set()


def node_begin(name: str) -> None:
    global _CUR_READS, _CUR_WRITES, _last_values, _refused
    if not _sweep_open:
        _refused += 1
        return
    if _models_done and name != "objective_constraints":
        # The model sequence for this sweep has finished.  A ``run()`` reaching
        # us here was invoked from an ``output()`` method -- several models call
        # their own ``run()`` from ``output()`` -- and those execute after the
        # solve, outside the MDA.  Counting them would fabricate dependency
        # edges and inflate write sets.  This is trap T1, enforced structurally.
        _output_path_calls[name] += 1
        _refused += 1
        return
    _node_id(name)
    _node_calls[name] += 1
    if _node_stack:
        # nested node: the parent has already run code, so the boundary
        # snapshot must be retaken
        _nesting_seen[(_node_stack[-1][0], name)] += 1
        _last_values = _snapshot()
    _node_stack.append((name, _CUR_READS, _CUR_WRITES, _last_values))
    _CUR_WRITES = set()
    _CUR_READS = set() if _read_tracking else None
    _t_node.append(time.perf_counter())


def node_end() -> None:
    global _CUR_READS, _CUR_WRITES, _last_values, _refused
    if _refused:
        _refused -= 1
        return
    if not _node_stack:
        return
    _t1 = time.perf_counter()
    name, prev_reads, prev_writes, values_at_begin = _node_stack.pop()
    if _t_node:
        _node_time[name] += _t1 - _t_node.pop()
    writes = _CUR_WRITES if _CUR_WRITES is not None else set()
    reads = _CUR_READS if _CUR_READS is not None else set()

    values = _snapshot()
    changed = _diff_keys(values_at_begin, values)
    writes |= changed
    _fields_ever_changed.update(changed)

    _writes_all[name] |= writes
    if reads:
        _reads_all[name] |= reads

    _snaps_cur[name] = (values, writes)
    _last_values = values

    _CUR_READS = prev_reads
    _CUR_WRITES = prev_writes


def _close_sweep() -> None:
    global _sweep_open, _snaps_prev, _snaps_cur, _sweep_in_call
    global _CUR_READS, _CUR_WRITES, _last_sweep_changes
    if not _sweep_open:
        return
    _sweep_open = False
    _CUR_READS = None
    _CUR_WRITES = None
    del _node_stack[:]
    del _t_node[:]

    if not _in_call:
        # sweeps issued by ``call_models_and_write_output``: not an idempotence
        # loop, nothing to compare against
        _snaps_prev = {}
        _snaps_cur = {}
        return

    _sweep_in_call += 1
    if _snaps_prev:
        changes: list = []
        changed_nodes = {}
        for name, (values, wkeys) in _snaps_cur.items():
            prev = _snaps_prev.get(name)
            if prev is None:
                changed_nodes[name] = True
                continue
            pvalues, pwkeys = prev
            diff = [
                k
                for k in (wkeys | pwkeys)
                if not _agrees(pvalues[_key_index[k]], values[_key_index[k]])
            ]
            changed_nodes[name] = bool(diff)
            for k in diff:
                key = (name, f"{k[0]}.{k[1]}")
                _changers[key] += 1
                changes.append(key)
                _fields_changed_between_sweeps.add(k)
        _last_sweep_changes = changes

        for mod in MODULES:
            live = any(
                changed_nodes.get(n, False)
                for n in _snaps_cur
                if NODE_MODULE.get(n) == mod
            )
            if live:
                _module_change_by_sweep[(mod, _sweep_in_call)] += 1
            elif mod not in _module_converged_at:
                _module_converged_at[mod] = _sweep_in_call
    else:
        _last_sweep_changes = []

    _snaps_prev = _snaps_cur
    _snaps_cur = {}


def sweep(models=None, data=None) -> None:
    """Called at the top of ``Caller._call_models_once``."""
    global _sweep_open, _sweep_index, _last_values, _read_sweeps, _models_done
    if not _installed:
        if models is None:
            return
        install(models, data)

    _close_sweep()
    _sweep_index += 1

    if _in_call and (
        _sweep_index <= READ_BUDGET
        or (READ_STRIDE and _sweep_index % READ_STRIDE == 0)
    ):
        _read_hooks_on()
        _read_sweeps += 1
        _edge_growth.append((
            _sweep_index,
            sum(len(v) for v in _reads_all.values()),
        ))
    else:
        _read_hooks_off()

    _sweep_open = True
    _models_done = False
    _last_values = _snapshot()


def sweep_end() -> None:
    """Called at the very end of ``Caller._call_models_once``.

    Marks the model sequence for this sweep as finished, so that a ``run()``
    reaching a node wrapper afterwards -- which can only have come from an
    ``output()`` method -- is refused rather than recorded (trap T1).  The
    objective/constraint block is still admitted, because it executes after
    ``_call_models_once`` returns and is genuinely part of the sweep.
    """
    global _models_done
    _models_done = True


def call_models_begin() -> None:
    global _in_call, _sweep_in_call, _snaps_prev, _snaps_cur, _module_converged_at
    _close_sweep()
    _in_call = True
    _sweep_in_call = 0
    _snaps_prev = {}
    _snaps_cur = {}
    _module_converged_at = {}


def call_models_end(phase: str, converged: bool = True) -> None:
    global _in_call
    _close_sweep()
    rec = {"phase": phase, "s_global": _sweep_in_call, "converged": converged}
    for mod in MODULES:
        rec[mod] = _module_converged_at.get(mod)
    _calls.append(rec)
    for key in _last_sweep_changes:
        _late_changers[key] += 1
    _in_call = False


def objective_begin() -> None:
    node_begin("objective_constraints")


def objective_end() -> None:
    node_end()


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------


def _edges() -> list:
    writers: dict = {}
    for node, keys in _writes_all.items():
        if NODE_MODULE.get(node) == "X":
            continue
        for k in keys:
            writers.setdefault(k, set()).add(node)

    edges = []
    for reader, keys in _reads_all.items():
        rmod = NODE_MODULE.get(reader, "?")
        if rmod == "X":
            continue
        for k in keys:
            for writer in writers.get(k, ()):
                if writer == reader:
                    continue
                wmod = NODE_MODULE.get(writer, "?")
                if wmod == rmod:
                    continue
                edges.append({
                    "field": f"{k[0]}.{k[1]}",
                    "writer": writer,
                    "writer_module": wmod,
                    "reader": reader,
                    "reader_module": rmod,
                    "back": MODULE_ORDER.get(wmod, 99) > MODULE_ORDER.get(rmod, 99),
                    "field_ever_changed": k in _fields_ever_changed,
                    "field_changed_between_sweeps": k in _fields_changed_between_sweeps,
                })
    return edges


def summary() -> dict:
    _close_sweep()
    edges = _edges()
    back = [e for e in edges if e["back"]]
    back_live = [e for e in back if e["field_changed_between_sweeps"]]
    return {
        "mode": "modules",
        "read_budget": READ_BUDGET,
        "read_stride": READ_STRIDE,
        "read_sweeps": _read_sweeps,
        "sweeps_total": _sweep_index,
        "nesting_seen": {f"{a}>{b}": c for (a, b), c in _nesting_seen.items()},
        "output_path_calls_refused": dict(_output_path_calls),
        "nodes": [
            {
                "name": n,
                "module": NODE_MODULE.get(n, "?"),
                "calls": _node_calls[n],
                "n_writes": len(_writes_all.get(n, ())),
                "n_reads": len(_reads_all.get(n, ())),
                "seconds": _node_time.get(n, 0.0),
            }
            for n in _nodes
        ],
        "calls": _calls,
        "edge_growth": _edge_growth,
        "n_edges_cross_module": len(edges),
        "n_back_edges": len(back),
        "back_edges": back,
        "back_edge_fields": sorted({e["field"] for e in back}),
        "back_edge_fields_live": sorted({e["field"] for e in back_live}),
        "module_change_by_sweep": {
            f"{m}:{s}": c for (m, s), c in sorted(_module_change_by_sweep.items())
        },
        "late_changers": [
            {"node": k[0], "field": k[1], "count": c}
            for k, c in _late_changers.most_common(120)
        ],
        "changers_top": [
            {"node": k[0], "field": k[1], "count": c}
            for k, c in _changers.most_common(120)
        ],
        "n_fields_ever_changed": len(_fields_ever_changed),
        "n_fields_changed_between_sweeps": len(_fields_changed_between_sweeps),
        "fields_changed_between_sweeps": sorted(
            f"{a}.{b}" for a, b in _fields_changed_between_sweeps
        ),
        "writes_by_node": {n: sorted(f"{a}.{b}" for a, b in v) for n, v in _writes_all.items()},
    }
