#!/usr/bin/env python
"""Several evaluations in one PROCESS process: the noise stencil, or timed repetitions.

Task A89 (coupling-subset-trial).  One subprocess, its own directory, launched by
``run_trial.py`` with the environment V4's ``pool.environment_for`` composes for
the arm (plus this trial's overrides).  It initialises the input file exactly as
V4's evaluation child does, enters a recorded coupling-state snapshot bit for
bit, installs :mod:`narrowing`, and then:

``--mode noise``
    evaluates the optimiser's own central-difference stencil the way VMCON's
    evaluator builds it — the point ``x``, then for every design variable
    ``x_i (1 + epsfcn)`` and ``x_i (1 − epsfcn)`` — each evaluation entered from
    the previous one's exit, as in an optimisation.  Records the objective,
    the constraint vector (exact hex) and the sweeps of every evaluation.
    The loops' tolerance is the environment's ``PROCESS_ARCH_TAU``.

``--mode timing``
    one warm-up evaluation (discarded: numba's first-call cost lands there),
    then ``--reps`` evaluations, each entered from the same snapshot, each with
    a fresh Caller, each timed: the whole ``call_models``, the coupling-state
    reads and residuals inside it (the predicate's cost), and the once-per-run
    execution.  Node calls and sweeps are recorded per repetition, so the timed
    evaluations can be checked to be the same computation every time.

Writes ``inproc.json`` in the run directory.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
V4_DIR = HERE.parent / "MDA_partitioning_experiment_v4"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", required=True, choices=("noise", "timing"))
    p.add_argument("--tree", required=True)
    p.add_argument("--configuration", required=True)
    p.add_argument("--arm", required=True)
    p.add_argument("--test-set", required=True)
    p.add_argument("--input", required=True)
    p.add_argument("--coupling-state", required=True)
    p.add_argument("--entry-state", required=True)
    p.add_argument("--outdir", required=True)
    p.add_argument("--reps", type=int, default=7)
    a = p.parse_args()
    outdir = Path(a.outdir)
    out: dict = {"mode": a.mode, "configuration": a.configuration, "arm": a.arm,
                 "test_set": a.test_set, "entry_state": a.entry_state}
    try:
        sys.path.insert(0, str(HERE))
        sys.path.insert(0, str(V4_DIR))
        from harness.child import child, predicate as predicate_mod
        import shutil

        out["process_file"] = child.assert_tree(Path(a.tree))
        import narrowing
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
        h = float(num.epsfcn)
        out.update(nvar=n, m=m, epsfcn=h, tau=ms.TAU)
        spec, _ = ms.load_spec(a.coupling_state)
        snapshot = json.loads(Path(a.entry_state).read_text())
        written = predicate_mod.write_entry_state(spec, data, snapshot)
        out["entry_readback_bitexact"] = written.get("readback_bitexact")
        narrowing.install(ms, caller_mod, test_set=a.test_set,
                          configuration=a.configuration, arm=a.arm, outdir=outdir)

        def evaluate(caller, x):
            nodes0, sw0 = caller_mod.NODE_CALLS[0], caller_mod.DISPATCH_SWEEPS[0]
            objf, conf = caller.call_models(x, m)
            return {"objf_hex": float(objf).hex(),
                    "conf_hex": [float(c).hex() for c in conf],
                    "node_calls": caller_mod.NODE_CALLS[0] - nodes0,
                    "sweeps": caller_mod.DISPATCH_SWEEPS[0] - sw0}

        if a.mode == "noise":
            caller = caller_mod.Caller(run.models, data)
            points = [{"point": "x0", **evaluate(caller, x0.copy())}]
            for i in range(n):
                for sign, name in ((1.0, "fwd"), (-1.0, "bwd")):
                    x = x0.copy()
                    x[i] = x0[i] * (1.0 + sign * h)
                    points.append({"point": f"{name}{i}", **evaluate(caller, x)})
            out["points"] = points
        else:
            caller = caller_mod.Caller(run.models, data)
            out["warmup"] = evaluate(caller, x0.copy())
            reps = []
            for _ in range(a.reps):
                predicate_mod.write_entry_state(spec, data, snapshot)
                narrowing.reset_timers()
                caller = caller_mod.Caller(run.models, data)
                t0 = time.perf_counter()
                rec = evaluate(caller, x0.copy())
                rec["wall_s"] = time.perf_counter() - t0
                rec.update(narrowing.TIMERS)
                reps.append(rec)
            out["reps"] = reps
        out["narrowing"] = narrowing.STATE.get("narrowing")
        out["status"] = "ok"
    except BaseException:  # noqa: BLE001 - recorded
        out["status"] = "crashed"
        out["traceback"] = traceback.format_exc()
    (outdir / "inproc.json").write_text(json.dumps(out, indent=1))
    return 0 if out["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
