#!/usr/bin/env python
"""A1 gradient-noise study.

Three measurements, all with the probe switch OFF (baseline semantics):

M1 repeat-at-fixed-x
    Call ``call_models`` 20x at the same x. If the loop is deterministic given
    the same starting state this is exactly zero -- which is the expected and
    more interesting outcome, because it means the noise mechanism is NOT
    stochastic.

M2 path dependence
    Alternate x -> x+d -> x -> x-d -> x ... and look at the scatter in f(x).
    In a real FD sweep every ``call_models`` starts from the model state left
    by the previous one, so this is the mechanism that actually injects noise.

M3 loop-exit error -> implied relative gradient error
    The idempotence loop exits when two successive sweeps agree to rtol=1e-6,
    so the value it returns sits somewhere short of the fixed point. Measure
    ``|v_loop - v_converged|`` (v_converged = loop + 10 forced extra sweeps) at
    each FD point x_i +/- eps*x_i, and compare with the FD difference that
    forms the gradient. That ratio is the relative gradient error.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.pop("PROCESS_IDF_PROBE", None)
os.environ.pop("PROCESS_IDF_PROBE_LOG", None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="large_tokamak_nof")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--repeats", type=int, default=20)
    ap.add_argument("--at", choices=["x0", "opt"], default="x0")
    ap.add_argument("--optfile", default="")
    args = ap.parse_args()

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    dst = outdir / f"{args.scenario}.IN.DAT"
    shutil.copy(HERE / "scenarios" / f"{args.scenario}.IN.DAT", dst)

    import numpy as np

    from process.core.caller import Caller
    from process.core.solver import constraints
    from process.core.solver.iteration_variables import (
        load_iteration_variables,
        load_scaled_bounds,
    )
    from process.core.solver.objectives import objective_function
    from process.main import SingleRun

    sr = SingleRun(str(dst), solver="vmcon")
    data = sr.data
    load_iteration_variables(data)
    load_scaled_bounds(data)

    n = int(data.numerics.nvar)
    m = int(data.numerics.neqns + data.numerics.nineqns)
    eps = float(data.numerics.epsfcn)
    x0 = np.array(data.numerics.xcm[:n], dtype=np.float64)

    if args.at == "opt":
        # The scaled solution vector: MFILE 'xcm0NN' is final/initial and the
        # registry normalises every variable to 1.0 at its initial value.
        from process.core.io.mfile import MFile

        if args.optfile:
            optfile = args.optfile
        else:
            cand = sorted((HERE / "runs" / args.scenario / "baseline_rep1").glob("*MFILE.DAT"))
            if not cand:
                raise SystemExit("no baseline MFILE for --at opt")
            optfile = str(cand[0])
        mf = MFile(optfile)
        xopt = []
        for i in range(1, n + 1):
            key = f"xcm{i:03d}"
            if key not in mf.data:
                raise SystemExit(f"{key} missing from {optfile}")
            xopt.append(float(mf.data[key].get_scan(-1)))
        x0 = np.array(xopt, dtype=np.float64)
        res_optfile = optfile
    else:
        res_optfile = None

    caller = Caller(sr.models, data)

    def loop_eval(x):
        return caller.call_models(np.asarray(x, dtype=np.float64), m)

    def converged_eval(x, extra=10):
        """Loop value, then force `extra` more sweeps to approach the fixed point."""
        vo, vc = caller.call_models(np.asarray(x, dtype=np.float64), m)
        for _ in range(extra):
            caller._call_models_once(np.asarray(x, dtype=np.float64))
        co = objective_function(data.numerics.minmax, data)
        cc, _, _, _, _ = constraints.constraint_eqns(m, -1, data)
        return (vo, vc), (co, np.asarray(cc, dtype=np.float64))

    res: dict = {
        "scenario": args.scenario, "n": n, "m": m, "epsfcn": eps, "at": args.at,
        "optfile": res_optfile,
    }

    # ---------------- M1: repeat at fixed x ----------------
    objs, confs = [], []
    for _ in range(args.repeats):
        o, c = loop_eval(x0)
        objs.append(float(o))
        confs.append(np.asarray(c, dtype=np.float64).copy())
    C = np.array(confs)
    res["M1_repeat_fixed_x"] = {
        "repeats": args.repeats,
        "objf_mean": float(np.mean(objs)),
        "objf_std": float(statistics.pstdev(objs)) if len(objs) > 1 else 0.0,
        "objf_ptp": float(np.ptp(objs)),
        "conf_std_max": float(np.max(np.std(C, axis=0))),
        "conf_ptp_max": float(np.max(np.ptp(C, axis=0))),
        "deterministic": bool(np.ptp(objs) == 0.0 and np.max(np.ptp(C, axis=0)) == 0.0),
    }

    # ---------------- M2: path dependence ----------------
    # f(x) evaluated after arriving from x+d, then from x-d, alternating.
    i_probe = min(1, n - 1)
    d = eps
    path_vals, path_confs = [], []
    for rep in range(min(args.repeats, 10)):
        xp = x0.copy(); xp[i_probe] = x0[i_probe] * (1.0 + d)
        loop_eval(xp)
        o, c = loop_eval(x0)
        path_vals.append(float(o)); path_confs.append(np.asarray(c).copy())
        xm = x0.copy(); xm[i_probe] = x0[i_probe] * (1.0 - d)
        loop_eval(xm)
        o, c = loop_eval(x0)
        path_vals.append(float(o)); path_confs.append(np.asarray(c).copy())
    PC = np.array(path_confs)
    res["M2_path_dependence"] = {
        "probe_var_index": i_probe,
        "n_evals_at_x0": len(path_vals),
        "objf_ptp": float(np.ptp(path_vals)),
        "objf_rel_ptp": float(np.ptp(path_vals) / max(abs(np.mean(path_vals)), 1e-30)),
        "conf_ptp_max": float(np.max(np.ptp(PC, axis=0))),
    }

    # ---------------- M3: loop-exit error -> gradient error ----------------
    per_var = []
    for i in range(n):
        xf = x0.copy(); xf[i] = x0[i] * (1.0 + eps)
        xb = x0.copy(); xb[i] = x0[i] * (1.0 - eps)

        (of_loop, cf_loop), (of_conv, cf_conv) = converged_eval(xf)
        (ob_loop, cb_loop), (ob_conv, cb_conv) = converged_eval(xb)

        dx = xf[i] - xb[i]
        g_loop = (float(of_loop) - float(ob_loop)) / dx
        g_conv = (float(of_conv) - float(ob_conv)) / dx
        err_f = abs(float(of_loop) - float(of_conv))
        err_b = abs(float(ob_loop) - float(ob_conv))
        grad_err = (err_f + err_b) / abs(dx)

        # Constraint-side: the loop-exit error and the resulting error in the
        # constraint Jacobian column for this variable.
        cf_l = np.asarray(cf_loop, dtype=np.float64)
        cb_l = np.asarray(cb_loop, dtype=np.float64)
        cf_c = np.asarray(cf_conv, dtype=np.float64)
        cb_c = np.asarray(cb_conv, dtype=np.float64)
        cerr = np.abs(cf_l - cf_c) + np.abs(cb_l - cb_c)
        jac_loop = (cf_l - cb_l) / dx
        jac_conv = (cf_c - cb_c) / dx
        jac_abs_err = cerr / abs(dx)
        denom = np.where(np.abs(jac_conv) > 1e-30, np.abs(jac_conv), np.nan)
        jac_rel_err = jac_abs_err / denom
        per_var.append({
            "i": i,
            "dx": float(dx),
            "g_loop": g_loop,
            "g_converged": g_conv,
            "objf_exit_err_fwd": err_f,
            "objf_exit_err_bwd": err_b,
            "abs_grad_err": grad_err,
            "rel_grad_err": grad_err / abs(g_conv) if abs(g_conv) > 1e-30 else float("inf"),
            "grad_rel_diff": abs(g_loop - g_conv) / abs(g_conv) if abs(g_conv) > 1e-30 else float("inf"),
            "conf_exit_err_max": float(np.max(cerr)),
            "jac_abs_err_max": float(np.max(jac_abs_err)),
            "jac_rel_err_max": float(np.nanmax(jac_rel_err)) if np.any(~np.isnan(jac_rel_err)) else None,
            "jac_col_norm": float(np.linalg.norm(jac_conv)),
        })
    finite = [p["grad_rel_diff"] for p in per_var if p["grad_rel_diff"] != float("inf")]
    finite_s = sorted(finite)
    jr = [p["jac_rel_err_max"] for p in per_var if p["jac_rel_err_max"] is not None]
    res["M3_gradient_error"] = {
        "per_var": per_var,
        "median_rel_grad_diff": finite_s[len(finite_s) // 2] if finite_s else None,
        "max_rel_grad_diff": max(finite) if finite else None,
        "max_objf_exit_err": max(
            max(p["objf_exit_err_fwd"], p["objf_exit_err_bwd"]) for p in per_var),
        "max_conf_exit_err": max(p["conf_exit_err_max"] for p in per_var),
        "max_jac_abs_err": max(p["jac_abs_err_max"] for p in per_var),
        "max_jac_rel_err": max(jr) if jr else None,
        "n_vars": n,
    }

    (outdir / "noise.json").write_text(json.dumps(res, indent=2))
    print(json.dumps({k: v for k, v in res.items() if k != "M3_gradient_error"}, indent=2))
    print("M3 summary:", json.dumps(
        {k: v for k, v in res["M3_gradient_error"].items() if k != "per_var"}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
