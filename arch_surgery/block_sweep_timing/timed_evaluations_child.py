#!/usr/bin/env python
"""Timed repetitions of one evaluation, with per-sweep, per-node and per-test timers.

Task A91 (block-sweep-timing).  A89's ``inproc_child.py --mode timing`` with
:mod:`sweep_timers` installed beside A89's ``narrowing`` (test set ``full``:
V4's own whole-``y`` test, unchanged; the once-per-run execution of the per-run
set where the arm defers per run, as A89's arms ``A0`` and ``A2`` do).

One subprocess, its own directory, launched by ``run_survey.py`` with the
environment V4's ``pool.environment_for`` composes for the arm (plus A89's
overrides for its ``A0``).  It initialises the input file exactly as V4's
evaluation child does, asserts the imported tree is the worktree's V4 copy,
enters the recorded displaced entry snapshot bit for bit, then runs **one
warm-up evaluation** (discarded: numba's first-call cost lands there) and
``--reps`` timed evaluations of the same entry, each with a fresh Caller.

Per repetition: the objective and constraint vector (hex), node calls and
dispatch sweeps (the driver's own counters, so the repetitions can be checked
to be the same computation), ``call_models`` wall clock, A89's predicate and
once-per-run timers, and this task's raw sweep events with their aggregate.

Writes ``sweep_timing.json`` in the run directory, stamped with the tree's
git head (A89's in-process records were not; the brief asks for it).
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRIAL_DIR = HERE.parent / "coupling_subset_trial"
V4_DIR = HERE.parent / "MDA_partitioning_experiment_v4"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--tree", required=True)
    p.add_argument("--configuration", required=True)
    p.add_argument("--arm", required=True)
    p.add_argument("--input", required=True)
    p.add_argument("--coupling-state", required=True)
    p.add_argument("--entry-state", required=True)
    p.add_argument("--outdir", required=True)
    p.add_argument("--reps", type=int, default=7)
    a = p.parse_args()
    outdir = Path(a.outdir)
    stamp_clock = lambda: datetime.now().astimezone().isoformat(timespec="seconds")  # noqa: E731
    out: dict = {"format": "block-sweep-timing-1", "configuration": a.configuration,
                 "arm": a.arm, "test_set": "full", "entry_state": a.entry_state,
                 "reps_requested": a.reps,
                 # wall-clock window of this subprocess, so a timed case can be checked
                 # against any contention notice (the orchestrator's, 2026-09-29)
                 "started_at": stamp_clock(), "ended_at": None,
                 "architecture_environment": {k: v for k, v in os.environ.items()
                                              if k.startswith("PROCESS_ARCH")}}
    try:
        sys.path.insert(0, str(HERE))
        sys.path.insert(0, str(TRIAL_DIR))
        sys.path.insert(0, str(V4_DIR))
        from harness.child import child, predicate as predicate_mod
        from harness.core import provenance as prov
        import shutil

        process_file = child.assert_tree(Path(a.tree))
        out.update(prov.stamp(Path(a.tree), process_file=process_file))
        import narrowing
        import sweep_timers
        from process.core import caller as caller_mod
        from process.core.solver import module_solve as ms
        from process.core.solver.iteration_variables import (
            load_iteration_variables, load_scaled_bounds)
        from process.main import SingleRun

        local = outdir / Path(a.input).name
        shutil.copy(a.input, local)
        run = SingleRun(str(local), solver="vmcon", update_obsolete=True)
        data = run.data
        load_iteration_variables(data)
        load_scaled_bounds(data)
        num = data.numerics
        n = int(num.n_iteration_variables)
        m = int(num.n_equality_constraints) + int(num.n_inequality_constraints)
        x0 = num.xcm[:n].copy()
        out.update(nvar=n, m=m, epsfcn=float(num.epsfcn), tau=ms.TAU,
                   i_figure_merit=int(num.i_figure_merit))
        spec, _ = ms.load_spec(a.coupling_state)
        snapshot = json.loads(Path(a.entry_state).read_text())
        written = predicate_mod.write_entry_state(spec, data, snapshot)
        out["entry_readback_bitexact"] = written.get("readback_bitexact")
        narrowing.install(ms, caller_mod, test_set="full", configuration=a.configuration,
                          arm=a.arm, outdir=outdir)
        sweep_timers.install(caller_mod, ms, models=run.models,
                             in_once=lambda: narrowing.STATE.get("in_once", False))

        def evaluate(caller, x):
            nodes0, sw0 = caller_mod.NODE_CALLS[0], caller_mod.DISPATCH_SWEEPS[0]
            objf, conf = caller.call_models(x, m)
            return {"objf_hex": float(objf).hex(),
                    "conf_hex": [float(c).hex() for c in conf],
                    "node_calls": caller_mod.NODE_CALLS[0] - nodes0,
                    "sweeps": caller_mod.DISPATCH_SWEEPS[0] - sw0,
                    "module_solve_stats": caller.module_solve_stats}

        caller = caller_mod.Caller(run.models, data)
        sweep_timers.begin()
        out["warmup"] = evaluate(caller, x0.copy())
        out["warmup"]["timers"] = sweep_timers.aggregate(sweep_timers.end())
        reps = []
        for _ in range(a.reps):
            predicate_mod.write_entry_state(spec, data, snapshot)
            narrowing.reset_timers()
            caller = caller_mod.Caller(run.models, data)
            sweep_timers.begin()
            t0 = time.perf_counter()
            rec = {"taken_at": stamp_clock()}
            rec.update(evaluate(caller, x0.copy()))
            rec["wall_s"] = time.perf_counter() - t0
            raw = sweep_timers.end()
            rec.update(narrowing.TIMERS)
            rec["timers"] = sweep_timers.aggregate(raw)
            rec["raw_sweeps"] = raw["sweeps"]
            rec["pending_read_s_unattributed"] = raw["pending_read_s_unattributed"]
            rec["other"] = raw["other"]
            rec["n_outside_sweep_node_calls"] = raw["n_outside_sweep_node_calls"]
            reps.append(rec)
        out["reps"] = reps
        out["narrowing"] = narrowing.STATE.get("narrowing")
        out["status"] = "ok"
    except BaseException:  # noqa: BLE001 - recorded
        out["status"] = "crashed"
        out["traceback"] = traceback.format_exc()
    out["ended_at"] = stamp_clock()
    out["load_average_at_end"] = list(os.getloadavg()) if hasattr(os, "getloadavg") else None
    (outdir / "sweep_timing.json").write_text(json.dumps(out, indent=1))
    return 0 if out["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
