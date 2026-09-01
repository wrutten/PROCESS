"""Design-point harvest for Phase A of the MDA partition experiment (A18).

Imported **only** when ``PROCESS_IDF_PROBE=harvest``.  With any other value, or
with the variable unset, this file is never imported and costs nothing, so
switch-neutrality holds by construction -- the same argument that already
covers ``_idf_probe_modules`` (A2) and ``_idf_probe_frozen`` (A19).

Why a separate file rather than a fourth branch inside ``_idf_probe``
--------------------------------------------------------------------

``_idf_probe`` is the module every instrumented file imports unconditionally.
Anything placed *in* it is imported on the disabled path too, and the project's
neutrality argument rests on that module staying a bare switch plus counters.
The three existing instruments are separate files for exactly that reason.  A
fourth follows the established shape, and F1 (the probe consolidation) is
scheduled to merge all four afterwards under a bit-identity gate.

**No new hook site is added to PROCESS.**  Everything below hangs off hooks
A1 already installed: ``sweep(models, data)`` at ``caller.py:273`` hands over
both the model registry and the data structure, which is all the harvest needs.

What is harvested
-----------------

For a sampled subset of ``Caller.call_models`` invocations:

``x``
    the design vector, captured at the injection site.
``y0``
    the **entry state**: a full copy of every data-structure field, taken
    immediately *after* the design vector is injected on the first sweep of
    that ``call_models``.  A19 §5.3 established that the injection convention
    does not change any count; the convention is recorded here so that it is
    a stated choice rather than an accident.

A design point is the **pair** ``(x, y0)``.  ``x`` alone would not make the
comparison paired: two architectures started from different entry states are
not solving the same problem.

Alongside those, and as an outstanding commitment to the dependency-analysis
study (architecture evaluation F1 addendum), the harvest bins the **magnitude
distribution of ``objf`` and of the constraint vector** as they are actually
evaluated inside the idempotence loop.  That addendum measured the same
distribution on the MFILE set and left the idempotence loop's own set
explicitly unmeasured; this closes it.

The coupling-variable set ``y`` is *not* declared here.  It is derived from
``_idf_probe_modules``'s per-field write census -- every field written by a
model node executing inside ``Caller._call_models_once`` -- and is emitted in
the summary for the replay to consume.  Set (b) of EXPERIMENT_FRAMEWORK.md
§2.4, measured rather than assumed.

Nothing here mutates model state.  The only writes are to this module's own
bookkeeping and to the harvest file.
"""

from __future__ import annotations

import copy
import os
import pickle
import time
from dataclasses import fields as dc_fields

import numpy as np

from process.core import _idf_probe_modules as M

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

#: Sample every Nth ``call_models`` of the ``grad`` phase (finite-difference
#: perturbations, 94-96 % of all calls).  A19 §5.2 established that perturbed
#: points behave no differently from unperturbed ones, so a 1-in-5 subsample
#: is what keeps a full multi-arm pass inside a few minutes.
GRAD_STRIDE = int(os.environ.get("PROCESS_IDF_PROBE_HARVEST_GRAD_STRIDE", "5"))

#: Sample every Nth ``call_models`` of every other phase (``fn``,
#: ``grad_reconcile``, ``init``).  These are few, so the default takes all.
OTHER_STRIDE = int(os.environ.get("PROCESS_IDF_PROBE_HARVEST_OTHER_STRIDE", "1"))

#: Where the harvested states are written.  Unset means "do not write" -- the
#: summary is still produced, so an inertness check can run without paying the
#: disk cost.
OUT = os.environ.get("PROCESS_IDF_PROBE_HARVEST_OUT", "")

#: Hard ceiling on how many design points are kept, so a long scan cannot fill
#: the disk unnoticed.  0 means unlimited.
MAX_POINTS = int(os.environ.get("PROCESS_IDF_PROBE_HARVEST_MAX_POINTS", "0"))


# --------------------------------------------------------------------------
# Magnitude bins -- the F1-addendum commitment
# --------------------------------------------------------------------------

#: Upper edges, in |value|.  The 1e-2 edge is where ``np.allclose``'s hidden
#: ``atol = 1e-8`` starts to dominate its ``rtol = 1e-6`` term; the 1e-8 edge
#: is where agreement becomes unconditional.
BIN_EDGES = (1e-8, 1e-6, 1e-4, 1e-2, 1.0, 1e3, 1e6)
BIN_LABELS = (
    "<1e-8",
    "1e-8..1e-6",
    "1e-6..1e-4",
    "1e-4..1e-2",
    "1e-2..1",
    "1..1e3",
    "1e3..1e6",
    ">1e6",
)


def _new_hist() -> dict:
    d = {lab: 0 for lab in BIN_LABELS}
    d["zero"] = 0
    d["nonzero"] = 0
    d["nan"] = 0
    d["inf"] = 0
    d["total"] = 0
    return d


_hist_objf: dict = _new_hist()
_hist_conf: dict = _new_hist()


def _bin_into(hist: dict, values) -> None:
    arr = np.atleast_1d(np.asarray(values, dtype=float))
    hist["total"] += arr.size
    nan = ~np.isfinite(arr)
    n_nan = int(np.isnan(arr).sum())
    n_inf = int(nan.sum()) - n_nan
    hist["nan"] += n_nan
    hist["inf"] += n_inf
    finite = np.abs(arr[np.isfinite(arr)])
    n_zero = int((finite == 0.0).sum())
    hist["zero"] += n_zero
    nz = finite[finite > 0.0]
    hist["nonzero"] += int(nz.size)
    if nz.size:
        idx = np.searchsorted(np.asarray(BIN_EDGES), nz, side="left")
        for i, lab in enumerate(BIN_LABELS):
            hist[lab] += int((idx == i).sum())


# --------------------------------------------------------------------------
# State
# --------------------------------------------------------------------------

_models = None
_data = None
_installed = False
_setx = None
_orig_objective = None
_orig_constraint_eqns = None

_call_index = 0
_phase_counts: dict = {}
_sampled = False
_captured_this_call = False
_last_x = None
_last_nvars = None

#: Length of the constraint vector the idempotence loop is comparing.  It is
#: NOT always ``n_equality + n_inequality``: on the fsolve path
#: ``solver.py:383`` calls ``fcnvmc1`` with ``meq`` alone, so an evaluation
#: run's loop compares a 2-vector while its final call compares a 25-vector.
#: Arm R reproduces ``Caller.call_models``, so it has to know which.
_last_m: list = [None]
_m_counts: dict = {}

_points: list = []
_dropped_for_cap = 0
_node_order: list = []
_node_order_seen: dict = {}
_t0 = time.perf_counter()
_capture_s = 0.0
_errors: list = []


# --------------------------------------------------------------------------
# State capture -- serialisable, and the exact analogue of A19's _save_state
# --------------------------------------------------------------------------


def _capture_state(data) -> dict:
    """``{(namespace, field): value}`` for every data-structure field.

    Arrays and lists are copied, so a later mutation of the live structure
    cannot reach back into a harvested point.  A19's ``_save_state`` keeps the
    *object* as well, because it restores into the same interpreter; a harvest
    crosses a process boundary, so it keeps the value only and the replay
    restores by filling the fresh process's own objects in place.
    """
    out = {}
    for f in dc_fields(data):
        ns = getattr(data, f.name)
        for g in dc_fields(ns):
            v = object.__getattribute__(ns, g.name)
            c = v.__class__
            if c is np.ndarray:
                v = v.copy()
            elif c is list:
                v = copy.deepcopy(v)
            out[(f.name, g.name)] = v
    return out


# --------------------------------------------------------------------------
# Installation
# --------------------------------------------------------------------------


def _install(models, data) -> None:
    """Wrap the injection site and the objective/constraint evaluation.

    Both wrappers are installed from inside this module, on the ``harvest``
    path only, so no hook site is added to ``process/`` (EXPERIMENT_FRAMEWORK
    §1.4).  Both are pure pass-throughs: they call the original with the
    original arguments and return its result unchanged.
    """
    global _installed, _models, _data, _setx
    global _orig_objective, _orig_constraint_eqns
    if _installed:
        return
    _installed = True
    _models = models
    _data = data

    import process.core.caller as _caller
    from process.core.solver import constraints as _constraints

    _setx = _caller.set_scaled_iteration_variable

    def _inject(xc, nvars, dat):
        global _last_x, _last_nvars, _captured_this_call, _capture_s
        result = _setx(xc, nvars, dat)
        _last_x = np.asarray(xc, dtype=float).copy()
        _last_nvars = int(nvars)
        if _sampled and not _captured_this_call:
            _captured_this_call = True
            t = time.perf_counter()
            _points.append({
                "call_index": _call_index,
                "x": _last_x,
                "nvars": _last_nvars,
                "state": _capture_state(dat),
            })
            _capture_s += time.perf_counter() - t
        return result

    _caller.set_scaled_iteration_variable = _inject

    _orig_objective = _caller.objective_function

    def _objf(*a, **kw):
        v = _orig_objective(*a, **kw)
        try:
            _bin_into(_hist_objf, v)
        except Exception as exc:  # never let bookkeeping break a run
            _errors.append(f"objf bin: {type(exc).__name__}: {exc}")
        return v

    _caller.objective_function = _objf

    _orig_constraint_eqns = _constraints.constraint_eqns

    def _ceq(*a, **kw):
        out = _orig_constraint_eqns(*a, **kw)
        try:
            _last_m[0] = int(a[0]) if a else None
            _m_counts[_last_m[0]] = _m_counts.get(_last_m[0], 0) + 1
            _bin_into(_hist_conf, out[0])
        except Exception as exc:
            _errors.append(f"conf bin: {type(exc).__name__}: {exc}")
        return out

    _constraints.constraint_eqns = _ceq


# --------------------------------------------------------------------------
# Hooks -- everything A2's instrument does, plus the harvest
# --------------------------------------------------------------------------


def sweep(models=None, data=None) -> None:
    M.sweep(models, data)
    if models is not None and not _installed:
        _install(models, data)


def sweep_end() -> None:
    # ``M._snaps_cur`` holds this sweep's nodes in execution order, and is
    # cleared by the next ``_close_sweep``.  Reading it here is the cheapest
    # way to record the true model sequence: the replay then *measures* the
    # sequence instead of reconstructing ``_call_models_once``'s dispatch,
    # which is what A19 had to do and is the one place that could drift.
    key = tuple(M._snaps_cur.keys())
    if not _node_order:
        _node_order.extend(key)
    _node_order_seen[key] = _node_order_seen.get(key, 0) + 1
    M.sweep_end()


def objective_begin() -> None:
    M.objective_begin()


def objective_end() -> None:
    M.objective_end()


def call_models_begin() -> None:
    global _call_index, _sampled, _captured_this_call
    M.call_models_begin()
    _call_index += 1
    _captured_this_call = False
    _sampled = False
    if not _installed:
        # The very first ``call_models`` begins before the first sweep, so the
        # node registry does not exist yet.  A19 skipped it for the same
        # reason; it is one point out of hundreds.
        return
    if MAX_POINTS and len(_points) >= MAX_POINTS:
        return
    from process.core import _idf_probe as _p

    phase = _p._phase
    n = _phase_counts.get(phase, 0)
    _phase_counts[phase] = n + 1
    stride = GRAD_STRIDE if phase == "grad" else OTHER_STRIDE
    if stride > 0 and n % stride == 0:
        _sampled = True


def call_models_end(phase: str, converged: bool = True) -> None:
    global _dropped_for_cap
    M.call_models_end(phase, converged)
    if not _sampled:
        return
    if not _captured_this_call:
        # sampled but the injection never ran: cannot happen in the tokamak
        # path, recorded rather than assumed
        _dropped_for_cap += 1
        return
    rec = M._calls[-1] if M._calls else {}
    p = _points[-1]
    p["phase"] = phase
    p["s_global"] = rec.get("s_global")
    p["loop_converged"] = bool(converged)
    p["m"] = _last_m[0]


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------


def _y_keys() -> list:
    """Set (b): every field written by a model node inside a sweep.

    ``<x_inject>`` is excluded -- those fields are the design vector, an input
    to the fixed point rather than part of it.  ``objective_constraints`` is
    excluded because it executes after ``_call_models_once`` returns and
    computes the quantities the fixed point is being asked *not* to be judged
    on.  Every other node in the census is a model on a ``run()`` path, which
    ``_idf_probe_modules`` enforces structurally at the sweep boundary
    (traps T1 and T7).
    """
    keys: set = set()
    for node, ks in M._writes_all.items():
        if node in ("<x_inject>", "objective_constraints"):
            continue
        keys |= ks
    return sorted(keys)


def _writes_by_node() -> dict:
    return {
        n: sorted(f"{a}.{b}" for a, b in v)
        for n, v in M._writes_all.items()
    }


def summary() -> dict:
    base = M.summary()
    y_keys = _y_keys()

    written = None
    if OUT:
        try:
            payload = {
                "format": "a18-harvest-1",
                "y_keys": y_keys,
                "node_order": list(_node_order),
                "node_module": dict(M.NODE_MODULE),
                "writes_by_node": _writes_by_node(),
                "points": _points,
            }
            with open(OUT, "wb") as fh:
                pickle.dump(payload, fh, protocol=5)
            written = OUT
        except Exception as exc:
            _errors.append(f"write: {type(exc).__name__}: {exc}")

    base["harvest"] = {
        "grad_stride": GRAD_STRIDE,
        "other_stride": OTHER_STRIDE,
        "max_points": MAX_POINTS,
        "call_models_seen": _call_index,
        "phase_counts": dict(_phase_counts),
        "n_points": len(_points),
        "points_dropped": _dropped_for_cap,
        "n_y_keys": len(y_keys),
        "constraint_vector_lengths_seen": dict(_m_counts),
        "node_order": list(_node_order),
        "node_order_variants": len(_node_order_seen),
        "n_data_fields": len(M._snap_keys),
        "capture_s": _capture_s,
        "wall_s": time.perf_counter() - _t0,
        "written_to": written,
        "errors": list(_errors)[:40],
        "magnitudes": {
            "objf": dict(_hist_objf),
            "conf": dict(_hist_conf),
            "bin_labels": list(BIN_LABELS),
            "bin_edges": list(BIN_EDGES),
        },
        "y_keys": [f"{a}.{b}" for a, b in y_keys],
        "writes_by_node": _writes_by_node(),
        "point_index": [
            {
                "call_index": p["call_index"],
                "phase": p.get("phase"),
                "s_global": p.get("s_global"),
                "loop_converged": p.get("loop_converged"),
            }
            for p in _points
        ],
    }
    return base
