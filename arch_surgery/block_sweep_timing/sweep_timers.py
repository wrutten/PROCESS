"""Wall-clock timers on one block sweep, one node call and one convergence test.

Task A91 (block-sweep-timing).  Installed on V4's driver copy from outside the
V4 folder, after ``process`` is imported, the way A89's ``narrowing`` installs
its substitutions: nothing in ``MDA_partitioning_experiment_v4/`` is edited.

What is timed (``time.perf_counter``, seconds)
---------------------------------------------
* **one block sweep** -- ``Caller._sweep_block(xc, nodes)``: the whole walk of
  the dispatch body (``_call_models_once``) restricted to *nodes*.  Labelled
  by the schedule (``module_schedule``) block whose node set it is, ``FF`` for
  the per-call deferred tail, ``ONCE_PER_RUN`` for the per-run set A89's
  ``narrowing`` runs once after convergence.
* **one node call** -- the ``run()`` a ``Caller._node`` dispatch executes.  The
  wrapper hands ``_node`` a timed closure, so a node ``_node`` drops (outside
  the block, deferred, suppressed) costs a closure allocation and nothing
  else, and ``NODE_CALLS`` is still incremented by the driver's own line.
* **the design-vector injection** (``set_scaled_iteration_variable``) and the
  **first-wall geometry prime** (``models.fw.set_fw_geometry``, A2 only):
  the two named pieces of the dispatch body that are not nodes.
* **the convergence test** -- ``spec.read`` and ``spec.residual``, attributed
  to a block: the read *after* a sweep and the residual belong to the block
  just swept; the read *before* a block's first sweep (``y_prev``) belongs to
  the block swept next.

Per block sweep, ``wall - sum(node) - x_inject - fw_geometry`` is the
**dispatch overhead**: the switch tests, the ``_node`` filtering of the nodes
outside the block, the counter increments -- A89 §7.5's unmeasured hypothesis.

Per evaluation (not per sweep), five more named pieces of ``call_models``
that are neither a sweep nor a test: ``module_schedule`` (which, with the
per-call deferral on, re-reads the committed write sets and re-walks the
objective and constraint source on every call), ``_defer_per_run_nodes``,
``spec.bind``, ``objective_function`` and ``constraint_eqns``.

Usage: :func:`install` once per process; :func:`begin` before an evaluation,
:func:`end` after it, which returns the evaluation's record.  Timings are
context, never evidence (CLAUDE.md).
"""

from __future__ import annotations

import time

PERF = time.perf_counter
TAIL_LABEL = "FF"
ONCE_LABEL = "ONCE_PER_RUN"
OTHER_KEYS = ("module_schedule_s", "defer_per_run_resolve_s", "bind_s", "objective_s",
              "constraints_s")


def _timed_other(key, fn):
    def wrapped(*a, **k):
        ev = STATE["eval"]
        if ev is None:
            return fn(*a, **k)
        t0 = PERF()
        try:
            return fn(*a, **k)
        finally:
            ev.other[key] += PERF() - t0
    return wrapped

STATE: dict = {"installed": False, "eval": None, "labels": {}, "in_once": lambda: False}


class Evaluation:
    """One evaluation's raw events."""

    def __init__(self):
        self.sweeps: list[dict] = []
        self.open_sweep: dict | None = None
        self.test: dict[str, dict] = {}
        self.pending_read_s = 0.0
        self.pending_n_read = 0
        self.last_event: str | None = None
        self.current_label: str | None = None
        self.outside_nodes: dict[str, float] = {}
        self.n_outside_calls = 0
        self.other: dict[str, float] = {k: 0.0 for k in OTHER_KEYS}

    def test_of(self, label):
        return self.test.setdefault(label, {"read_s": 0.0, "residual_s": 0.0,
                                            "n_read": 0, "n_residual": 0})

    def record(self) -> dict:
        return {"sweeps": self.sweeps, "test_by_block": self.test,
                "pending_read_s_unattributed": self.pending_read_s,
                "outside_sweep_nodes": self.outside_nodes,
                "n_outside_sweep_node_calls": self.n_outside_calls,
                "other": self.other}


def _label(caller_mod, self, nodes) -> str:
    cache = STATE["labels"]
    hit = cache.get(nodes)
    if hit is not None:
        return hit
    if STATE["in_once"]():
        label = ONCE_LABEL
    else:
        schedule, tail = caller_mod.module_schedule(self.data.numerics.i_figure_merit)
        by_set = {n: lab for lab, n, _it in schedule if n}
        label = by_set.get(nodes)
        if label is None and nodes == tail:
            label = TAIL_LABEL if TAIL_LABEL not in by_set.values() else TAIL_LABEL + "_tail"
        if label is None:
            label = "UNLABELLED:" + ",".join(sorted(nodes))
    cache[nodes] = label
    return label


def install(caller_mod, ms, *, models=None, in_once=None):
    """Install the wrappers once in this process."""
    if STATE["installed"]:
        return
    STATE["installed"] = True
    if in_once is not None:
        STATE["in_once"] = in_once

    orig_sweep = caller_mod.Caller._sweep_block
    orig_node = caller_mod.Caller._node

    def _sweep_block(self, xc, nodes):
        ev = STATE["eval"]
        if ev is None:
            return orig_sweep(self, xc, nodes)
        label = _label(caller_mod, self, nodes)
        sw = {"label": label, "wall_s": 0.0, "node_s": {}, "n_node_calls": 0,
              "x_inject_s": 0.0, "fw_geometry_s": 0.0, "n_nodes_in_block": len(nodes)}
        if ev.pending_read_s:
            t = ev.test_of(label)
            t["read_s"] += ev.pending_read_s
            t["n_read"] += ev.pending_n_read
            ev.pending_read_s = 0.0
            ev.pending_n_read = 0
        ev.open_sweep = sw
        t0 = PERF()
        try:
            orig_sweep(self, xc, nodes)
        finally:
            sw["wall_s"] = PERF() - t0
            ev.open_sweep = None
            ev.sweeps.append(sw)
            ev.last_event = "sweep"
            ev.current_label = label

    def _node(self, name, run):
        ev = STATE["eval"]
        if ev is None:
            return orig_node(self, name, run)
        sw = ev.open_sweep

        def timed():
            t0 = PERF()
            run()
            dt = PERF() - t0
            if sw is not None:
                sw["node_s"][name] = sw["node_s"].get(name, 0.0) + dt
                sw["n_node_calls"] += 1
            else:
                ev.outside_nodes[name] = ev.outside_nodes.get(name, 0.0) + dt
                ev.n_outside_calls += 1

        orig_node(self, name, timed)

    caller_mod.Caller._sweep_block = _sweep_block
    caller_mod.Caller._node = _node

    orig_inject = caller_mod.set_scaled_iteration_variable

    def inject(xc, nvars, data):
        ev = STATE["eval"]
        if ev is None or ev.open_sweep is None:
            return orig_inject(xc, nvars, data)
        t0 = PERF()
        try:
            return orig_inject(xc, nvars, data)
        finally:
            ev.open_sweep["x_inject_s"] += PERF() - t0

    caller_mod.set_scaled_iteration_variable = inject

    if models is not None and hasattr(getattr(models, "fw", None), "set_fw_geometry"):
        orig_fw = models.fw.set_fw_geometry

        def fw_geometry(*a, **k):
            ev = STATE["eval"]
            if ev is None or ev.open_sweep is None:
                return orig_fw(*a, **k)
            t0 = PERF()
            try:
                return orig_fw(*a, **k)
            finally:
                ev.open_sweep["fw_geometry_s"] += PERF() - t0

        models.fw.set_fw_geometry = fw_geometry

    caller_mod.module_schedule = _timed_other("module_schedule_s", caller_mod.module_schedule)
    caller_mod._defer_per_run_nodes = _timed_other("defer_per_run_resolve_s",
                                                   caller_mod._defer_per_run_nodes)
    caller_mod.objective_function = _timed_other("objective_s", caller_mod.objective_function)
    caller_mod.constraints.constraint_eqns = _timed_other(
        "constraints_s", caller_mod.constraints.constraint_eqns)

    orig_subsets = ms.load_subsets
    wrapped: set = set()

    def load_subsets(spec, path=None):
        out = orig_subsets(spec, path)
        if id(spec) in wrapped:
            return out
        wrapped.add(id(spec))
        inner_read = spec.read
        inner_residual = spec.residual

        def read(bound):
            ev = STATE["eval"]
            if ev is None:
                return inner_read(bound)
            t0 = PERF()
            y = inner_read(bound)
            dt = PERF() - t0
            if ev.last_event == "sweep" and ev.current_label is not None:
                t = ev.test_of(ev.current_label)
                t["read_s"] += dt
                t["n_read"] += 1
            else:
                ev.pending_read_s += dt
                ev.pending_n_read += 1
            ev.last_event = "read"
            return y

        def residual(prev, cur, subset=None, **kw):
            ev = STATE["eval"]
            if ev is None:
                return inner_residual(prev, cur, subset=subset, **kw)
            t0 = PERF()
            res = inner_residual(prev, cur, subset=subset, **kw)
            dt = PERF() - t0
            label = ev.current_label if ev.current_label is not None else "UNATTRIBUTED"
            t = ev.test_of(label)
            t["residual_s"] += dt
            t["n_residual"] += 1
            ev.last_event = "residual"
            return res

        spec.read = read
        spec.residual = residual
        spec.bind = _timed_other("bind_s", spec.bind)
        return out

    ms.load_subsets = load_subsets


def begin() -> None:
    STATE["eval"] = Evaluation()


def end() -> dict:
    ev = STATE["eval"]
    STATE["eval"] = None
    return ev.record()


def aggregate(record: dict) -> dict:
    """Per-block and per-node totals of one evaluation, from its raw sweeps."""
    blocks: dict[str, dict] = {}
    nodes: dict[str, dict] = {}
    for sw in record["sweeps"]:
        b = blocks.setdefault(sw["label"], {
            "n_sweeps": 0, "wall_s": 0.0, "node_s": 0.0, "x_inject_s": 0.0,
            "fw_geometry_s": 0.0, "dispatch_s": 0.0, "n_node_calls": 0,
            "n_nodes_in_block": sw["n_nodes_in_block"], "node_s_by_node": {}})
        node_s = sum(sw["node_s"].values())
        b["n_sweeps"] += 1
        b["wall_s"] += sw["wall_s"]
        b["node_s"] += node_s
        b["x_inject_s"] += sw["x_inject_s"]
        b["fw_geometry_s"] += sw["fw_geometry_s"]
        b["dispatch_s"] += sw["wall_s"] - node_s - sw["x_inject_s"] - sw["fw_geometry_s"]
        b["n_node_calls"] += sw["n_node_calls"]
        for name, s in sw["node_s"].items():
            b["node_s_by_node"][name] = b["node_s_by_node"].get(name, 0.0) + s
            n = nodes.setdefault(name, {"n_calls": 0, "wall_s": 0.0})
            n["n_calls"] += 1
            n["wall_s"] += s
    for label, t in record["test_by_block"].items():
        b = blocks.setdefault(label, {"n_sweeps": 0, "wall_s": 0.0, "node_s": 0.0,
                                      "x_inject_s": 0.0, "fw_geometry_s": 0.0,
                                      "dispatch_s": 0.0, "n_node_calls": 0,
                                      "n_nodes_in_block": None, "node_s_by_node": {}})
        b.update({"test_read_s": t["read_s"], "test_residual_s": t["residual_s"],
                  "n_read": t["n_read"], "n_residual": t["n_residual"]})
    for b in blocks.values():
        b.setdefault("test_read_s", 0.0)
        b.setdefault("test_residual_s", 0.0)
        b.setdefault("n_read", 0)
        b.setdefault("n_residual", 0)
    return {"blocks": blocks, "nodes": nodes,
            "sweep_wall_total_s": sum(sw["wall_s"] for sw in record["sweeps"]),
            "n_sweeps_timed": len(record["sweeps"])}
