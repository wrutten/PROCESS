"""Env-switched instrumentation for the MDA partitioning experiment.

This module is inert unless the environment variable ``PROCESS_IDF_PROBE`` is
set at interpreter start-up.  When it is unset, :data:`ENABLED` is ``False``,
every hook site in the instrumented modules short-circuits on a single global
boolean load, and no probe state is created or mutated.  No floating-point
work is performed on the disabled path.

Four modes are supported:

``baseline``
    Record the shape of the existing MDA solve without altering control flow:
    sweeps per ``Caller.call_models``, the solver phase each ``call_models``
    belongs to, total model sweeps, and solver retries.  (Stage 0 / A1.)

``modules``
    Everything ``baseline`` records, plus per-module state attribution: which
    of the three candidate modules still has changing state after each sweep,
    and every read/write of a data-structure field attributed to the model
    node performing it.  Implemented in ``_idf_probe_modules``, which is
    imported only in this mode.  (Stage 1 / A2.)

``harvest``
    Everything ``modules`` records, plus a **design-point harvest**: for a
    sampled subset of ``call_models`` invocations the design vector and the
    full entry state are copied out to disk, so that the Phase A fixed-point
    architectures in ``arch_surgery/fixedpoint/`` can be replayed from
    bit-identical starting points without re-running the optimiser once per
    arm.  Also bins the magnitude distribution of ``objf`` and the constraint
    vector.  Implemented in ``_idf_probe_harvest``, imported only in this
    mode.  (A18.)

``frozen``
    Everything ``modules`` records, plus a **replay**: on a sampled subset of
    ``call_models`` invocations the three modules are re-iterated in
    isolation from a saved copy of the data structure, to measure how many
    sweeps each would need with its upstream inputs held *fixed* rather than
    moving.  The data structure is restored exactly afterwards, so the
    optimisation trajectory is unchanged.  Implemented in
    ``_idf_probe_frozen``, imported only in this mode.  (A19.)

Hook sites (see ``arch_surgery/idf_probe/README.md`` for the manifest):

* ``process/core/caller.py``     -- ``call_models`` begin/end, ``_call_models_once``
* ``process/core/solver/evaluators.py`` -- phase markers around fcnvmc1/fcnvmc2
* ``process/core/solver/solver_handler.py`` -- solver retry branches

Terminology
-----------
sweep
    One execution of ``Caller._call_models_once`` -- one pass over the model
    sequence.
call_models
    One execution of ``Caller.call_models`` -- the idempotence loop, which
    performs >= 2 sweeps (the structural floor) and up to 10.
phase
    Which part of the solver requested a ``call_models``:

    ``fn``
        objective/constraint evaluation (``fcnvmc1``)
    ``grad``
        finite-difference gradient perturbations (``fcnvmc2`` inner loop)
    ``grad_reconcile``
        the trailing consistency call at the end of ``fcnvmc2``
    ``init``
        anything before the solver sets a phase
    ``output``
        sweeps issued by ``call_models_and_write_output``; these are not
        inside a ``call_models`` at all and are counted separately
"""

from __future__ import annotations

import json
import os
import time
from collections import Counter

__all__ = [
    "ENABLED",
    "MODE",
    "call_models_begin",
    "call_models_end",
    "objective_begin",
    "objective_end",
    "record_retry",
    "sweep_end",
    "set_phase",
    "summary",
    "sweep",
    "write_summary",
]

VALID_MODES = ("baseline", "modules", "frozen", "harvest")

_raw = os.environ.get("PROCESS_IDF_PROBE", "").strip()
MODE: str | None = _raw or None
ENABLED: bool = MODE is not None

if ENABLED and MODE not in VALID_MODES:
    raise RuntimeError(
        f"PROCESS_IDF_PROBE={MODE!r} is not a recognised probe mode; "
        f"expected one of {VALID_MODES} (or unset to disable the probe)."
    )

#: The module-attribution instrument for Stage 1.  Imported only in ``modules``
#: mode, so that no other arm pays for its existence.
if MODE == "modules":
    from process.core import _idf_probe_modules as _mod
elif MODE == "frozen":
    from process.core import _idf_probe_frozen as _mod
elif MODE == "harvest":
    from process.core import _idf_probe_harvest as _mod
else:
    _mod = None

# --------------------------------------------------------------------------
# Probe state.  Only ever touched when ENABLED is True.
# --------------------------------------------------------------------------

_t_import = time.perf_counter()

#: current solver phase
_phase: str = "init"

#: total number of ``_call_models_once`` executions
_sweeps_total: int = 0

#: sweeps executed while no ``call_models`` is on the stack (i.e. from
#: ``call_models_and_write_output``)
_sweeps_output: int = 0

#: nesting depth of ``call_models`` (expected to be 0 or 1)
_depth: int = 0

#: value of ``_sweeps_total`` when the outermost ``call_models`` began
_sweeps_at_call_start: int = 0

#: total number of ``call_models`` executions
_calls_total: int = 0

#: (phase, sweeps) -> count
_hist: Counter = Counter()

#: ordered (phase, sweeps, converged) records
_records: list = []

#: ``call_models`` invocations that hit the 10-sweep ceiling and raised
_calls_nonconverged: int = 0

#: solver retries: list of {"kind", "ifail_before", "call_index"}
_retries: list = []


def set_phase(phase: str) -> str:
    """Set the current solver phase; return the previous one."""
    global _phase
    previous = _phase
    _phase = phase
    return previous


def sweep(models=None, data=None) -> None:
    """Record one execution of ``Caller._call_models_once``.

    ``models`` and ``data`` are passed so that the ``modules`` mode can install
    its node wrappers on the first sweep.  They are ignored in every other
    mode.
    """
    global _sweeps_total, _sweeps_output
    _sweeps_total += 1
    if _depth == 0:
        _sweeps_output += 1
    if _mod is not None:
        _mod.sweep(models, data)


def call_models_begin() -> None:
    """Record entry into ``Caller.call_models``."""
    global _depth, _sweeps_at_call_start
    if _depth == 0:
        _sweeps_at_call_start = _sweeps_total
        if _mod is not None:
            _mod.call_models_begin()
    _depth += 1


def call_models_end(*, converged: bool = True) -> None:
    """Record exit from ``Caller.call_models``.

    Parameters
    ----------
    converged
        ``False`` if the idempotence loop exhausted its 10 attempts and is
        about to raise.
    """
    global _depth, _calls_total, _calls_nonconverged
    _depth -= 1
    if _depth != 0:
        # Nested call_models is not expected; do not attribute sweeps twice.
        return
    _calls_total += 1
    sweeps = _sweeps_total - _sweeps_at_call_start
    _hist[(_phase, sweeps)] += 1
    _records.append((_phase, sweeps, converged))
    if not converged:
        _calls_nonconverged += 1
    if _mod is not None:
        _mod.call_models_end(_phase, converged)


def record_retry(kind: str, ifail_before) -> None:
    """Record a solver retry taken by ``SolverHandler.run``."""
    _retries.append({
        "kind": kind,
        "ifail_before": int(ifail_before),
        "call_models_before": _calls_total,
        "sweeps_before": _sweeps_total,
    })


def sweep_end() -> None:
    """Mark the end of the model sequence within one sweep."""
    if _mod is not None:
        _mod.sweep_end()


def objective_begin() -> None:
    """Mark entry into the objective/constraint evaluation (DSM rows 54-55)."""
    if _mod is not None:
        _mod.objective_begin()


def objective_end() -> None:
    """Mark exit from the objective/constraint evaluation."""
    if _mod is not None:
        _mod.objective_end()


def _phase_block(pairs) -> dict:
    """Build a stats block from an iterable of (sweeps, count) pairs."""
    hist = {}
    n_calls = 0
    total_sweeps = 0
    for sweeps, count in pairs:
        hist[sweeps] = hist.get(sweeps, 0) + count
        n_calls += count
        total_sweeps += sweeps * count
    at_floor = hist.get(2, 0)
    return {
        "n_call_models": n_calls,
        "total_sweeps": total_sweeps,
        "mean_sweeps_per_call": (total_sweeps / n_calls) if n_calls else None,
        "max_sweeps": max(hist) if hist else None,
        "frac_at_floor_2": (at_floor / n_calls) if n_calls else None,
        "hist": {str(k): hist[k] for k in sorted(hist)},
    }


def summary() -> dict:
    """Return the probe's rollup.  Safe to call when the probe is disabled."""
    if not ENABLED:
        return {"enabled": False, "mode": None}

    phases = sorted({p for p, _ in _hist})
    by_phase = {
        p: _phase_block((s, c) for (pp, s), c in _hist.items() if pp == p)
        for p in phases
    }
    overall = _phase_block((s, c) for (_p, s), c in _hist.items())

    return {
        "enabled": True,
        "mode": MODE,
        "probe_wall_s": time.perf_counter() - _t_import,
        "call_models_total": _calls_total,
        "call_models_nonconverged": _calls_nonconverged,
        "sweeps_total": _sweeps_total,
        "sweeps_inside_call_models": _sweeps_total - _sweeps_output,
        "sweeps_in_output_phase": _sweeps_output,
        "depth_at_summary": _depth,
        "by_phase": by_phase,
        "all_phases": overall,
        "retries": list(_retries),
        "n_retries": len(_retries),
        "modules": _mod.summary() if _mod is not None else None,
    }


def write_summary(path: str | None = None) -> str | None:
    """Write :func:`summary` as JSON.

    Uses ``path`` if given, else ``PROCESS_IDF_PROBE_OUT``.  Returns the path
    written, or ``None`` if the probe is disabled or no path was available.
    """
    if not ENABLED:
        return None
    target = path or os.environ.get("PROCESS_IDF_PROBE_OUT")
    if not target:
        return None
    with open(target, "w") as fh:
        json.dump(summary(), fh, indent=2)
    return target


def records() -> list:
    """Ordered (phase, sweeps, converged) tuples, for later stages."""
    return list(_records)
