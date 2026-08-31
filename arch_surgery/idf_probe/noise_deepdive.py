#!/usr/bin/env python
"""Deep-dive into the 'zero gradient noise' result.

Sub-commands (each must run in a FRESH interpreter -- PROCESS mutates a global
DataStructure and OutputFileManager keeps process-wide file handles):

  info    dump iteration-variable / constraint labels, objective definition,
          confirm the objective's functional form, time one call_models.
  jac     per-variable Jacobian error at x0 or opt, but computing the REALISED
          error |J_loop - J_conv| as well as the triangle-inequality BOUND that
          noise_probe.py reported, plus column-norm-relative measures.
  steps   FD step-size sweep: gradient/Jacobian at epsfcn in a geometric ladder.
          This is the standard way to expose a noise floor: a genuinely noisy
          function makes the FD estimate diverge as delta -> 0.
  scan    fine 1-D line scan along one iteration variable, recording objf, all
          constraints, the sweep count, and the fully-converged values.

Run with PROCESS_IDF_PROBE=baseline so sweep counts are recorded; that mode
delegates to Caller._call_models_original, i.e. semantics are unchanged.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Must be set before `process` is imported.
os.environ.setdefault("PROCESS_IDF_PROBE", "baseline")
os.environ.pop("PROCESS_IDF_PROBE_LOG", None)


def setup(scenario: str, outdir: Path, at: str, optfile: str = ""):
    import numpy as np

    from process.core.caller import Caller
    from process.core.solver.iteration_variables import (
        load_iteration_variables,
        load_scaled_bounds,
    )
    from process.main import SingleRun

    outdir.mkdir(parents=True, exist_ok=True)
    dst = outdir / f"{scenario}.IN.DAT"
    shutil.copy(HERE / "scenarios" / f"{scenario}.IN.DAT", dst)

    sr = SingleRun(str(dst), solver="vmcon")
    data = sr.data
    load_iteration_variables(data)
    load_scaled_bounds(data)

    n = int(data.numerics.nvar)
    m = int(data.numerics.neqns + data.numerics.nineqns)
    eps = float(data.numerics.epsfcn)
    x = np.array(data.numerics.xcm[:n], dtype=np.float64)

    if at == "opt":
        from process.core.io.mfile import MFile

        if not optfile:
            cand = sorted((HERE / "runs" / scenario / "baseline_rep1").glob("*MFILE.DAT"))
            optfile = str(cand[0])
        mf = MFile(optfile)
        x = np.array(
            [float(mf.data[f"xcm{i:03d}"].get_scan(-1)) for i in range(1, n + 1)],
            dtype=np.float64,
        )

    caller = Caller(sr.models, data)
    return sr, data, caller, n, m, eps, x


def sweeps_last() -> int:
    from process.core import _idf_probe

    return int(_idf_probe._SWEEPS_THIS_CALL)


# --------------------------------------------------------------------------
def cmd_info(args) -> int:
    import numpy as np

    outdir = Path(args.outdir).resolve()
    sr, data, caller, n, m, eps, x0 = setup(args.scenario, outdir, "x0")

    names = [str(data.numerics.name_xc[i]).strip() for i in range(n)]
    ixc = [int(data.numerics.ixc[i]) for i in range(n)]
    scale = [float(data.numerics.scale[i]) for i in range(n)]
    icc = [int(data.numerics.icc[j]) for j in range(m)]

    t0 = time.perf_counter()
    objf, conf = caller.call_models(x0, m)
    t1 = time.perf_counter()
    s1 = sweeps_last()
    t2 = time.perf_counter()
    objf2, conf2 = caller.call_models(x0, m)
    t3 = time.perf_counter()

    # Confirm the objective's functional form: objf as a function of x[j] alone.
    lin = {}
    for j in range(n):
        vals = []
        for f in (0.98, 0.99, 1.0, 1.01, 1.02):
            xx = x0.copy()
            xx[j] = x0[j] * f
            try:
                o, _ = caller.call_models(xx, m)
                vals.append((f, float(o)))
            except Exception as exc:  # noqa: BLE001
                vals.append((f, f"RAISED {type(exc).__name__}: {exc}"))
        lin[names[j]] = vals

    res = {
        "scenario": args.scenario,
        "n": n,
        "m": m,
        "epsfcn": eps,
        "minmax": int(data.numerics.minmax),
        "x0": x0.tolist(),
        "names": names,
        "ixc": ixc,
        "scale": scale,
        "icc": icc,
        "objf_x0": float(objf),
        "conf_x0": np.asarray(conf).tolist(),
        "rmajor_x0": float(data.physics.rmajor),
        "wall_first_call": t1 - t0,
        "sweeps_first_call": s1,
        "wall_second_call": t3 - t2,
        "sweeps_second_call": sweeps_last(),
        "objf_vs_scaling": lin,
    }
    (outdir / "info.json").write_text(json.dumps(res, indent=2))
    print(json.dumps({k: v for k, v in res.items() if k != "objf_vs_scaling"}, indent=2))
    print("objective linearity check (f, objf) per variable:")
    for k, v in lin.items():
        print(f"  {k:45s} {[f'{a}:{b:.12g}' for a, b in v]}")
    return 0


# --------------------------------------------------------------------------
def cmd_jac(args) -> int:
    """Realised vs bounded Jacobian error, per column and per constraint."""
    import numpy as np

    from process.core.solver import constraints
    from process.core.solver.objectives import objective_function

    outdir = Path(args.outdir).resolve()
    sr, data, caller, n, m, eps, x0 = setup(args.scenario, outdir, args.at, args.optfile)
    names = [str(data.numerics.name_xc[i]).strip() for i in range(n)]
    icc = [int(data.numerics.icc[j]) for j in range(m)]
    K = args.extra

    def both(x):
        """(loop value, converged value, sweeps) at x."""
        o_l, c_l = caller.call_models(np.asarray(x, dtype=np.float64), m)
        s = sweeps_last()
        for _ in range(K):
            caller._call_models_once(np.asarray(x, dtype=np.float64))
        o_c = objective_function(data.numerics.minmax, data)
        c_c, _, _, _, _ = constraints.constraint_eqns(m, -1, data)
        return (
            float(o_l),
            np.asarray(c_l, np.float64).copy(),
            float(o_c),
            np.asarray(c_c, np.float64).copy(),
            s,
        )

    # warm up so the first column is not measured from a cold state
    caller.call_models(x0, m)

    per_var = []
    for i in range(n):
        xf = x0.copy()
        xf[i] = x0[i] * (1.0 + eps)
        xb = x0.copy()
        xb[i] = x0[i] * (1.0 - eps)
        dx = xf[i] - xb[i]

        ofl, cfl, ofc, cfc, sf = both(xf)
        obl, cbl, obc, cbc, sb = both(xb)

        j_loop = (cfl - cbl) / dx
        j_conv = (cfc - cbc) / dx
        realised = np.abs(j_loop - j_conv)  # what the optimiser actually suffers
        bound = (np.abs(cfl - cfc) + np.abs(cbl - cbc)) / abs(dx)  # noise_probe metric

        colnorm = float(np.linalg.norm(j_conv))
        with np.errstate(divide="ignore", invalid="ignore"):
            rel_elem = np.where(np.abs(j_conv) > 1e-30, realised / np.abs(j_conv), np.nan)
            bnd_elem = np.where(np.abs(j_conv) > 1e-30, bound / np.abs(j_conv), np.nan)
        jmax_r = int(np.nanargmax(rel_elem)) if np.any(~np.isnan(rel_elem)) else -1
        jmax_b = int(np.nanargmax(bnd_elem)) if np.any(~np.isnan(bnd_elem)) else -1

        per_var.append({
            "i": i,
            "name": names[i],
            "dx": float(dx),
            "sweeps_fwd": sf,
            "sweeps_bwd": sb,
            "sweeps_equal": sf == sb,
            "objf_loop_fwd": ofl,
            "objf_conv_fwd": ofc,
            "objf_exit_err_fwd": abs(ofl - ofc),
            "objf_exit_err_bwd": abs(obl - obc),
            "grad_loop": (ofl - obl) / dx,
            "grad_conv": (ofc - obc) / dx,
            "jac_colnorm": colnorm,
            "jac_realised_abs_max": float(np.max(realised)),
            "jac_bound_abs_max": float(np.max(bound)),
            "jac_realised_rel_colnorm": float(np.max(realised) / colnorm) if colnorm > 0 else None,
            "jac_realised_rel_elem_max": float(np.nanmax(rel_elem)) if jmax_r >= 0 else None,
            "jac_bound_rel_elem_max": float(np.nanmax(bnd_elem)) if jmax_b >= 0 else None,
            "worst_realised_constraint": {
                "j": jmax_r, "icc": icc[jmax_r] if jmax_r >= 0 else None,
                "j_conv": float(j_conv[jmax_r]) if jmax_r >= 0 else None,
                "j_loop": float(j_loop[jmax_r]) if jmax_r >= 0 else None,
                "abs_err": float(realised[jmax_r]) if jmax_r >= 0 else None,
            },
            "worst_bound_constraint": {
                "j": jmax_b, "icc": icc[jmax_b] if jmax_b >= 0 else None,
                "j_conv": float(j_conv[jmax_b]) if jmax_b >= 0 else None,
                "abs_err": float(bound[jmax_b]) if jmax_b >= 0 else None,
            },
            "exit_err_fwd_max": float(np.max(np.abs(cfl - cfc))),
            "exit_err_bwd_max": float(np.max(np.abs(cbl - cbc))),
        })

    res = {"scenario": args.scenario, "at": args.at, "n": n, "m": m, "epsfcn": eps,
           "extra_sweeps": K, "icc": icc, "per_var": per_var}
    (outdir / f"jac_{args.at}.json").write_text(json.dumps(res, indent=2))

    hdr = (f"{'i':>3} {'name':<38} {'sw f/b':>7} {'|dJ|real':>11} {'|dJ|bound':>11} "
           f"{'||Jcol||':>10} {'real/col':>10} {'real/elem':>11} {'bound/elem':>11}")
    print(hdr)
    for p in per_var:
        print(f"{p['i']:>3} {p['name'][:38]:<38} "
              f"{p['sweeps_fwd']}/{p['sweeps_bwd']:<5} "
              f"{p['jac_realised_abs_max']:>11.3e} {p['jac_bound_abs_max']:>11.3e} "
              f"{p['jac_colnorm']:>10.3e} {p['jac_realised_rel_colnorm']:>10.3e} "
              f"{(p['jac_realised_rel_elem_max'] or float('nan')):>11.3e} "
              f"{(p['jac_bound_rel_elem_max'] or float('nan')):>11.3e}")
    return 0


# --------------------------------------------------------------------------
def cmd_steps(args) -> int:
    """FD step-size ladder -- the classical noise-floor diagnostic."""
    import numpy as np

    outdir = Path(args.outdir).resolve()
    sr, data, caller, n, m, eps, x0 = setup(args.scenario, outdir, args.at, args.optfile)
    names = [str(data.numerics.name_xc[i]).strip() for i in range(n)]
    icc = [int(data.numerics.icc[j]) for j in range(m)]

    ladder = [float(s) for s in args.steps.split(",")]
    caller.call_models(x0, m)  # warm up

    grads = {}
    jacs = {}
    sweeps = {}
    for d in ladder:
        g = np.zeros(n)
        J = np.zeros((n, m))
        sw = []
        for i in range(n):
            xf = x0.copy()
            xf[i] = x0[i] * (1.0 + d)
            xb = x0.copy()
            xb[i] = x0[i] * (1.0 - d)
            of, cf = caller.call_models(xf, m)
            sf = sweeps_last()
            ob, cb = caller.call_models(xb, m)
            sb = sweeps_last()
            dx = xf[i] - xb[i]
            g[i] = (float(of) - float(ob)) / dx
            J[i, :] = (np.asarray(cf) - np.asarray(cb)) / dx
            sw.append([sf, sb])
        grads[d] = g
        jacs[d] = J
        sweeps[d] = sw

    ref = ladder[0]
    out = {"scenario": args.scenario, "at": args.at, "ladder": ladder,
           "names": names, "icc": icc, "epsfcn_default": eps,
           "grad": {str(d): grads[d].tolist() for d in ladder},
           "jac": {str(d): jacs[d].tolist() for d in ladder},
           "sweeps": {str(d): sweeps[d] for d in ladder}}
    (outdir / f"steps_{args.at}.json").write_text(json.dumps(out))

    # Report: per step, column-wise relative deviation from the smallest-step
    # "least truncation error" reference and from the default 1e-3.
    print(f"reference column comparison, at={args.at}")
    print(f"{'delta':>10} " + " ".join(f"{names[i][:10]:>11}" for i in range(min(n, 8))))
    base = jacs[float(args.base)]
    for d in ladder:
        rel = []
        for i in range(n):
            num = np.linalg.norm(jacs[d][i] - base[i])
            den = np.linalg.norm(base[i])
            rel.append(num / den if den > 0 else np.nan)
        print(f"{d:>10.1e} " + " ".join(f"{rel[i]:>11.3e}" for i in range(min(n, 8))))
        out.setdefault("relcol_vs_base", {})[str(d)] = rel
    (outdir / f"steps_{args.at}.json").write_text(json.dumps(out))

    print("\nmax over columns of ||J(d)-J(base)||/||J(base)||:")
    for d in ladder:
        r = out["relcol_vs_base"][str(d)]
        print(f"  delta={d:9.1e}  max={np.nanmax(r):.4e}  median={np.nanmedian(r):.4e}")
    return 0


# --------------------------------------------------------------------------
def cmd_scan(args) -> int:
    """Fine line scan along one variable."""
    import numpy as np

    from process.core.solver import constraints
    from process.core.solver.objectives import objective_function

    outdir = Path(args.outdir).resolve()
    sr, data, caller, n, m, eps, x0 = setup(args.scenario, outdir, args.at, args.optfile)
    names = [str(data.numerics.name_xc[i]).strip() for i in range(n)]
    icc = [int(data.numerics.icc[j]) for j in range(m)]
    i = args.var
    K = args.extra

    half = args.span * eps
    ts = np.linspace(-half, half, args.points)

    caller.call_models(x0, m)  # warm start at the centre

    rows = []
    t0 = time.perf_counter()
    for t in ts:
        x = x0.copy()
        x[i] = x0[i] * (1.0 + t)
        s_reset = None
        if args.precond:
            # Reproduce fcnvmc2's incoming state: the previous FD column's
            # backward stencil point, evaluated with the ordinary loop.
            pi, prel = args.precond.split(",")
            xp = x0.copy()
            xp[int(pi)] = x0[int(pi)] * (1.0 + float(prel))
            caller.call_models(xp, m)
            s_reset = sweeps_last()
        elif args.reset:
            # Re-home the internal state at the scan centre so every point is
            # reached from the same incoming state (as the FD stencil does).
            caller.call_models(x0, m)
            s_reset = sweeps_last()
        o_l, c_l = caller.call_models(x, m)
        s = sweeps_last()
        row = {"t": float(t), "x": float(x[i]), "sweeps": s, "sweeps_reset": s_reset,
               "objf": float(o_l),
               "conf": np.asarray(c_l, np.float64).tolist()}
        if K:
            for _ in range(K):
                caller._call_models_once(x)
            o_c = objective_function(data.numerics.minmax, data)
            c_c, _, _, _, _ = constraints.constraint_eqns(m, -1, data)
            row["objf_conv"] = float(o_c)
            row["conf_conv"] = np.asarray(c_c, np.float64).tolist()
        rows.append(row)
    wall = time.perf_counter() - t0

    res = {"scenario": args.scenario, "at": args.at, "var": i, "name": names[i],
           "x0_i": float(x0[i]), "epsfcn": eps, "span_in_epsfcn": args.span,
           "points": args.points, "extra_sweeps": K, "icc": icc,
           "wall_s": wall, "rows": rows}
    res["reset"] = bool(args.reset)
    res["precond"] = args.precond
    tag = f"scan_{args.at}_v{i}" + (
        "_pre" + args.precond.replace(",", "_").replace("-", "m").replace(".", "p")
        if args.precond else ("_reset" if args.reset else "_seq"))
    (outdir / f"{tag}.json").write_text(json.dumps(res))
    print(f"wrote {outdir / (tag + '.json')}  ({wall:.1f} s, {args.points} points)")

    C = np.array([r["conf"] for r in rows])
    sw = np.array([r["sweeps"] for r in rows])
    print(f"var {i} = {names[i]}, sweep counts seen: "
          f"{ {int(k): int(v) for k, v in zip(*np.unique(sw, return_counts=True))} }")
    # jump detection: |c(k+1)-c(k)| compared with the local smooth slope
    for j in range(m):
        d = np.diff(C[:, j])
        med = np.median(np.abs(d))
        if med == 0:
            continue
        big = np.where(np.abs(d) > max(20 * med, 1e-14))[0]
        if big.size:
            print(f"  icc={icc[j]:>3} (j={j:>2}): {big.size} steps >20x median; "
                  f"max|step|={np.max(np.abs(d)):.3e}, median|step|={med:.3e}")
    return 0


# --------------------------------------------------------------------------
def cmd_hyst(args) -> int:
    """Is the loop-exit value a function of x, or of (x, incoming state)?

    Evaluate call_models at ONE target point xt after several different
    pre-conditioning histories, and compare with the fixed point.
    """
    import numpy as np

    from process.core.solver import constraints
    from process.core.solver.objectives import objective_function

    outdir = Path(args.outdir).resolve()
    sr, data, caller, n, m, eps, x0 = setup(args.scenario, outdir, args.at, args.optfile)
    names = [str(data.numerics.name_xc[i]).strip() for i in range(n)]
    icc = [int(data.numerics.icc[j]) for j in range(m)]
    i = args.var

    def px(idx, rel):
        x = x0.copy()
        x[idx] = x0[idx] * (1.0 + rel)
        return x

    xt = px(i, eps)  # the forward FD stencil point

    def deep(x, k=25):
        caller.call_models(np.asarray(x), m)
        for _ in range(k):
            caller._call_models_once(np.asarray(x))
        return (objective_function(data.numerics.minmax, data),
                np.asarray(constraints.constraint_eqns(m, -1, data)[0], np.float64).copy())

    # Fixed-point reference at xt
    _, c_star = deep(xt)

    histories = {
        "deep_at_xt": [("deep", xt)],
        "deep_at_x0": [("deep", x0)],
        "loop_at_x0": [("loop", x0)],
        "loop_at_xbac_same_var": [("loop", px(i, -eps))],
        "loop_at_x0_then_other_var_bac": [("loop", x0), ("loop", px((i + 1) % n, -eps))],
        "loop_far_same_var_+2pct": [("loop", px(i, 0.02))],
        "loop_far_other_var_+2pct": [("loop", px((i + 3) % n, 0.02))],
        "loop_at_xt_twice": [("loop", xt), ("loop", xt)],
    }

    rows = []
    for label, hist in histories.items():
        for kind, xx in hist:
            if kind == "deep":
                deep(xx)
            else:
                caller.call_models(np.asarray(xx), m)
        o, c = caller.call_models(np.asarray(xt), m)
        s = sweeps_last()
        err = np.abs(np.asarray(c, np.float64) - c_star)
        jm = int(np.argmax(err))
        rows.append({
            "history": label, "sweeps": s, "objf": float(o),
            "max_abs_exit_err": float(np.max(err)),
            "worst_j": jm, "worst_icc": icc[jm],
            "worst_c_loop": float(np.asarray(c)[jm]), "worst_c_star": float(c_star[jm]),
            "n_constraints_off": int(np.count_nonzero(err)),
        })

    res = {"scenario": args.scenario, "at": args.at, "var": i, "name": names[i],
           "epsfcn": eps, "icc": icc, "c_star": c_star.tolist(), "rows": rows}
    (outdir / f"hyst_{args.at}_v{i}.json").write_text(json.dumps(res, indent=2))
    print(f"target = x0 with x[{i}]={names[i]} scaled by (1+{eps})")
    print(f"{'history':<34} {'sw':>3} {'max|c-c*|':>12} {'#off':>5} {'worst icc':>10} "
          f"{'c_loop':>14} {'c*':>14}")
    for r in rows:
        print(f"{r['history']:<34} {r['sweeps']:>3} {r['max_abs_exit_err']:>12.4e} "
              f"{r['n_constraints_off']:>5} {r['worst_icc']:>10} "
              f"{r['worst_c_loop']:>14.9f} {r['worst_c_star']:>14.9f}")
    return 0


# --------------------------------------------------------------------------
def cmd_fdchain(args) -> int:
    """Reproduce fcnvmc2 exactly, and compare with an order-reversed chain and
    with the FD of the fully-converged MDA. Shows whether the Jacobian VMCON
    receives is even a function of x."""
    import numpy as np

    from process.core.solver import constraints
    from process.core.solver.objectives import objective_function

    outdir = Path(args.outdir).resolve()
    sr, data, caller, n, m, eps, x0 = setup(args.scenario, outdir, args.at, args.optfile)
    names = [str(data.numerics.name_xc[i]).strip() for i in range(n)]
    icc = [int(data.numerics.icc[j]) for j in range(m)]

    def chain(order, deep=0):
        """fcnvmc2's loop over `order`; `deep` extra sweeps at each stencil point."""
        J = np.zeros((n, m))
        g = np.zeros(n)
        sw = {}
        for i in order:
            xf = x0.copy()
            xf[i] = x0[i] * (1.0 + eps)
            xb = x0.copy()
            xb[i] = x0[i] * (1.0 - eps)
            of, cf = caller.call_models(xf, m)
            sf = sweeps_last()
            if deep:
                for _ in range(deep):
                    caller._call_models_once(xf)
                of = objective_function(data.numerics.minmax, data)
                cf = constraints.constraint_eqns(m, -1, data)[0]
            ob, cb = caller.call_models(xb, m)
            sb = sweeps_last()
            if deep:
                for _ in range(deep):
                    caller._call_models_once(xb)
                ob = objective_function(data.numerics.minmax, data)
                cb = constraints.constraint_eqns(m, -1, data)[0]
            dx = xf[i] - xb[i]
            g[i] = (float(of) - float(ob)) / dx
            J[i, :] = (np.asarray(cf, np.float64) - np.asarray(cb, np.float64)) / dx
            sw[i] = (sf, sb)
        caller.call_models(x0, m)  # fcnvmc2's reconciliation call
        return g, J, sw

    fwd = list(range(n))
    rev = list(range(n - 1, -1, -1))

    caller.call_models(x0, m)
    chain(fwd)                             # throwaway: warm the internal state
    gA, JA, sA = chain(fwd)                # exactly what VMCON receives
    gB, JB, sB = chain(fwd)                # identical chain again, same x
    gC, JC, sC = chain(rev)                # same x, reversed evaluation order
    gD, JD, sD = chain(rev)                # reversed again
    gR, JR, _ = chain(fwd, deep=args.extra)      # FD of the converged MDA
    gR2, JR2, _ = chain(rev, deep=args.extra)    # ...in reversed order

    def cmp(Ja, Jb):
        out = []
        for i in range(n):
            den = np.linalg.norm(JR[i])
            out.append(float(np.linalg.norm(Ja[i] - Jb[i]) / den) if den > 0 else np.nan)
        return out

    pairs = {
        "A_vs_B_same_order_repeat": cmp(JA, JB),
        "C_vs_D_rev_order_repeat": cmp(JC, JD),
        "A_vs_C_order_dependence": cmp(JA, JC),
        "A_vs_REF_early_exit": cmp(JA, JR),
        "C_vs_REF_early_exit": cmp(JC, JR),
        "REF_vs_REF2_reference_order": cmp(JR, JR2),
    }
    res = {
        "scenario": args.scenario, "at": args.at, "n": n, "m": m, "epsfcn": eps,
        "names": names, "icc": icc, "deep_extra": args.extra,
        "J_A": JA.tolist(), "J_B": JB.tolist(), "J_C": JC.tolist(),
        "J_REF": JR.tolist(), "J_REF2": JR2.tolist(),
        "grad_A": gA.tolist(), "grad_REF": gR.tolist(),
        "colnorm_REF": [float(np.linalg.norm(JR[i])) for i in range(n)],
        **pairs,
        "sweeps_A": {str(k): v for k, v in sA.items()},
        "sweeps_C": {str(k): v for k, v in sC.items()},
    }
    (outdir / f"fdchain_{args.at}.json").write_text(json.dumps(res, indent=2))

    keys = list(pairs)
    print(f"{'i':>3} {'name':<32} {'||Jcol||':>10} " +
          " ".join(f"{k.split('_')[0] + '-' + k.split('_')[2]:>11}" for k in keys))
    for i in range(n):
        nm = names[i].split("'")[-2] if "'" in names[i] else names[i]
        print(f"{i:>3} {nm[:32]:<32} {np.linalg.norm(JR[i]):>10.3e} " +
              " ".join(f"{pairs[k][i]:>11.3e}" for k in keys))
    print(f"\ngrad (objective) A vs REF max rel diff: "
          f"{np.max(np.abs(gA - gR) / np.maximum(np.abs(gR), 1e-30)):.3e}")
    for k in keys:
        v = np.array(pairs[k])
        print(f"{k:>28}: max={np.nanmax(v):.3e} median={np.nanmedian(v):.3e} "
              f"n_nonzero={int(np.count_nonzero(v))}/{n}")
    return 0


# --------------------------------------------------------------------------
def cmd_trace(args) -> int:
    """Sweep-by-sweep convergence trace at the stencil point that produced the
    largest Jacobian error, replaying the exact preceding history."""
    import numpy as np

    from process.core.solver import constraints
    from process.core.solver.objectives import objective_function

    outdir = Path(args.outdir).resolve()
    sr, data, caller, n, m, eps, x0 = setup(args.scenario, outdir, args.at, args.optfile)
    names = [str(data.numerics.name_xc[i]).strip() for i in range(n)]
    icc = [int(data.numerics.icc[j]) for j in range(m)]
    K = args.extra
    itgt = args.var

    def both(x):
        caller.call_models(np.asarray(x), m)
        for _ in range(K):
            caller._call_models_once(np.asarray(x))

    caller.call_models(x0, m)
    # Replay cmd_jac's chain up to (but excluding) the target column
    for i in range(itgt):
        xf = x0.copy(); xf[i] = x0[i] * (1.0 + eps)
        xb = x0.copy(); xb[i] = x0[i] * (1.0 - eps)
        both(xf)
        both(xb)

    xt = x0.copy(); xt[itgt] = x0[itgt] * (1.0 + eps)

    # Now sweep one at a time at xt, recording everything
    hist = []
    for k in range(args.nsweeps):
        caller._call_models_once(xt)
        o = float(objective_function(data.numerics.minmax, data))
        c = np.asarray(constraints.constraint_eqns(m, -1, data)[0], np.float64).copy()
        hist.append({"sweep": k + 1, "objf": o, "conf": c.tolist(),
                     "temp_margin": float(data.tfcoil.temp_margin),
                     "p_plant_electric_net_mw": float(
                         data.heat_transport.p_plant_electric_net_mw)})

    C = np.array([h["conf"] for h in hist])
    cstar = C[-1]

    # Where would _call_models_original have exited? It compares sweep k with
    # sweep k+1 using np.allclose(rtol=1e-6, atol=1e-8) on objf AND conf.
    exit_at = None
    for k in range(1, len(hist)):
        if np.allclose(hist[k - 1]["objf"], hist[k]["objf"], rtol=1e-6, equal_nan=True) \
           and np.allclose(C[k - 1], C[k], rtol=1e-6, equal_nan=True):
            exit_at = k + 1
            break

    print(f"target: x0 with x[{itgt}]={names[itgt]} scaled by (1+{eps}), "
          f"after replaying the jac chain for columns 0..{itgt - 1}")
    print(f"loop would exit at sweep {exit_at}\n")
    print(f"{'sweep':>5} {'objf':>18} " + " ".join(
        f"{'c'+str(j)+'/icc'+str(icc[j]):>16}" for j in args.cols_list))
    for k, h in enumerate(hist):
        print(f"{k+1:>5} {h['objf']:>18.12f} " + " ".join(
            f"{C[k, j]:>16.12f}" for j in args.cols_list))
    print()
    print(f"{'sweep':>5} " + " ".join(f"{'|c'+str(j)+'-c*|':>14}" for j in args.cols_list)
          + f" {'max|c-c*|':>14} {'||c_k-c_{k-1}||inf':>20}")
    for k in range(len(hist)):
        d = np.abs(C[k] - cstar)
        step = np.max(np.abs(C[k] - C[k - 1])) if k else np.nan
        mark = "  <-- LOOP EXITS HERE" if exit_at == k + 1 else ""
        print(f"{k+1:>5} " + " ".join(f"{d[j]:>14.4e}" for j in args.cols_list)
              + f" {np.max(d):>14.4e} {step:>20.4e}{mark}")

    res = {"scenario": args.scenario, "at": args.at, "var": itgt, "name": names[itgt],
           "epsfcn": eps, "icc": icc, "exit_at_sweep": exit_at, "hist": hist,
           "residual_at_exit": (np.abs(C[exit_at - 1] - cstar).tolist()
                                if exit_at else None)}
    (outdir / f"trace_{args.at}_v{itgt}.json").write_text(json.dumps(res, indent=2))
    if exit_at:
        r = np.abs(C[exit_at - 1] - cstar)
        jm = int(np.argmax(r))
        print(f"\nresidual carried out of the loop: max {r[jm]:.4e} on "
              f"j={jm} (icc={icc[jm]}); implied FD contamination "
              f"{r[jm] / (2 * eps * x0[itgt]):.4e} absolute")
    return 0


# --------------------------------------------------------------------------
def cmd_survey(args) -> int:
    """For every FD stencil point: when does the idempotence loop exit, when does
    the sweep actually reach its fixed point, and what residual is carried out?

    Replays cmd_jac's chain (same K extra sweeps) so numbers are comparable.
    """
    import numpy as np

    from process.core.solver import constraints
    from process.core.solver.objectives import objective_function

    outdir = Path(args.outdir).resolve()
    sr, data, caller, n, m, eps, x0 = setup(args.scenario, outdir, args.at, args.optfile)
    names = [str(data.numerics.name_xc[i]).strip() for i in range(n)]
    icc = [int(data.numerics.icc[j]) for j in range(m)]
    NS = args.nsweeps

    def probe_point(x):
        """Sweep NS times from the current state, return the trace."""
        objs, Cs = [], []
        for _ in range(NS):
            caller._call_models_once(np.asarray(x))
            objs.append(float(objective_function(data.numerics.minmax, data)))
            Cs.append(np.asarray(constraints.constraint_eqns(m, -1, data)[0],
                                 np.float64).copy())
        C = np.array(Cs)
        cstar, ostar = C[-1], objs[-1]
        exit_at = None
        for k in range(1, NS):
            if np.allclose(objs[k - 1], objs[k], rtol=1e-6, equal_nan=True) and \
               np.allclose(C[k - 1], C[k], rtol=1e-6, equal_nan=True):
                exit_at = k + 1
                break
        fp_at = None
        for k in range(NS):
            if np.array_equal(C[k], cstar) and objs[k] == ostar:
                fp_at = k + 1
                break
        r = np.abs(C[exit_at - 1] - cstar) if exit_at else np.full(m, np.nan)
        step = np.max(np.abs(C[exit_at - 1] - C[exit_at - 2])) if exit_at else np.nan
        jm = int(np.nanargmax(r)) if exit_at else -1
        return {"exit_at": exit_at, "fp_at": fp_at,
                "residual_max": float(np.max(r)) if exit_at else None,
                "worst_j": jm, "worst_icc": icc[jm] if jm >= 0 else None,
                "step_at_exit": float(step) if exit_at else None,
                "contraction": float(np.max(r) / step) if exit_at and step > 0 else None,
                "objf_residual": abs(objs[exit_at - 1] - ostar) if exit_at else None}

    caller.call_models(x0, m)
    rows = []
    for i in range(n):
        for side, sgn in (("fwd", +1.0), ("bwd", -1.0)):
            x = x0.copy()
            x[i] = x0[i] * (1.0 + sgn * eps)
            r = probe_point(x)
            r.update({"i": i, "name": names[i], "side": side})
            rows.append(r)

    res = {"scenario": args.scenario, "at": args.at, "epsfcn": eps, "nsweeps": NS,
           "icc": icc, "rows": rows}
    (outdir / f"survey_{args.at}.json").write_text(json.dumps(res, indent=2))

    print(f"{'i':>3} {'name':<34} {'side':>4} {'exit':>5} {'fixpt':>6} {'lead':>5} "
          f"{'residual':>11} {'step@exit':>11} {'rho':>8} {'icc':>4}")
    for r in rows:
        nm = r["name"].split("'")[-2] if "'" in r["name"] else r["name"]
        lead = (r["fp_at"] - r["exit_at"]) if (r["fp_at"] and r["exit_at"]) else None
        print(f"{r['i']:>3} {nm[:34]:<34} {r['side']:>4} {str(r['exit_at']):>5} "
              f"{str(r['fp_at']):>6} {str(lead):>5} "
              f"{(r['residual_max'] if r['residual_max'] is not None else float('nan')):>11.4e} "
              f"{(r['step_at_exit'] if r['step_at_exit'] is not None else float('nan')):>11.4e} "
              f"{(r['contraction'] if r['contraction'] is not None else float('nan')):>8.4f} "
              f"{str(r['worst_icc']):>4}")
    nz = [r for r in rows if r["residual_max"]]
    print(f"\nstencil points with a non-zero residual: {len(nz)}/{len(rows)}")
    print(f"points where exit < fixed point: "
          f"{sum(1 for r in rows if r['fp_at'] and r['exit_at'] and r['fp_at'] > r['exit_at'])}"
          f"/{len(rows)}")
    if nz:
        print(f"residual range: {min(r['residual_max'] for r in nz):.3e} .. "
              f"{max(r['residual_max'] for r in nz):.3e}")
        print(f"contraction rho range: "
              f"{min(r['contraction'] for r in nz if r['contraction']):.4f} .. "
              f"{max(r['contraction'] for r in nz if r['contraction']):.4f}")
    print("objective residual at exit, max over stencil points: "
          f"{max((r['objf_residual'] or 0) for r in rows):.3e}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["info", "jac", "steps", "scan", "hyst", "fdchain",
                                    "trace", "survey"])
    ap.add_argument("--scenario", default="large_tokamak_nof")
    ap.add_argument("--outdir", default=str(HERE / "runs" / "noise_deepdive"))
    ap.add_argument("--at", choices=["x0", "opt"], default="x0")
    ap.add_argument("--optfile", default="")
    ap.add_argument("--extra", type=int, default=10)
    ap.add_argument("--var", type=int, default=13)
    ap.add_argument("--points", type=int, default=801)
    ap.add_argument("--span", type=float, default=2.0)
    ap.add_argument("--steps", default="1e-2,1e-3,1e-4,1e-5,1e-6,1e-7,1e-8")
    ap.add_argument("--base", default="1e-3")
    ap.add_argument("--reset", action="store_true",
                    help="re-evaluate at the scan centre before each point")
    ap.add_argument("--precond", default="",
                    help="'I,REL': before each scan point evaluate at x0 with x[I]*(1+REL)")
    ap.add_argument("--nsweeps", type=int, default=12)
    ap.add_argument("--cols", default="5,10,12,13")
    args = ap.parse_args()
    args.cols_list = [int(s) for s in args.cols.split(",") if s.strip()]
    return {"info": cmd_info, "jac": cmd_jac, "steps": cmd_steps, "scan": cmd_scan,
            "hyst": cmd_hyst, "fdchain": cmd_fdchain, "trace": cmd_trace,
            "survey": cmd_survey}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
