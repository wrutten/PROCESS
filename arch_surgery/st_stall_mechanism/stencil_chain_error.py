#!/usr/bin/env python
"""The evaluation error along the optimiser's own evaluation sequence, and the block loops along a traced optimisation.

Task A104 (st-stall-mechanism), measurement **M2, second part** (added after M2's
first part found the flat and partitioned loops' errors identical from converged
entries; the report's §7 records the decision).

Part 1 -- the chain (``--press``, ``--tables``)
----------------------------------------------
``evaluation_error_at_optimum.py`` enters every stencil point from the base
point's converged exit (the +h point) or from the +h point's exit (the -h point):
two evaluations deep.  VMCON's evaluator does not: one call of the problem is the
base point, then ``+h`` and ``-h`` of column 0, of column 1, ... of column n-1, then
the reconcile call at the base point, **each entered from the previous
evaluation's exit** (``Evaluators.fcnvmc1``/``fcnvmc2``; the data structure is
never reset between them).  Here that sequence is run as a chain of 2n + 2
single evaluations, each entered from the previous one's ``y_exit.json``, under
every loop of M2, at two design points of st:

* ``B0_seed000`` -- the flat arm's optimum at census 1e-8, entered from its own
  final state (M2's first design point);
* ``B2_seed000`` -- the **partitioned** arm's end point at census 1e-8 (after its
  40 iterations, 30 of them in the near band), entered from **its own** final
  state: the state the stalled arm itself carried.

Against the exact loop's value at the same point (the exact loop's own chain),
per evaluation: the objective error and the largest constraint error; per column
the finite-difference derivative error and the common and non-common parts, as in
M2's first part.

Part 2 -- the traced optimisations (``--trace-press``, ``--trace-tables``)
-------------------------------------------------------------------------
``B0`` and ``B2`` on st, seed 0, at census τ = 1e-8 and 1e-12: the campaign's own
jobs (the supplementary stage's at 1e-12) re-made with the driver's block trace
on (run kind ``smoke``; the trace is observation only, so each must reproduce its
record's iterations, evaluations and ``norm_objf`` to the bit -- checked and
printed).  From the trace: per iteration, over the gradient evaluations, how many
block loops stopped after their **first** sweep with a first-sweep change that was
**not zero** -- a loop that accepted the state it was entered with, carrying the
previous evaluation's lag forward -- and the size of those changes.

Usage::

    PYTHONDONTWRITEBYTECODE=1 python stencil_chain_error.py --press
    PYTHONDONTWRITEBYTECODE=1 python stencil_chain_error.py --trace-press
    PYTHONDONTWRITEBYTECODE=1 python stencil_chain_error.py --tables --trace-tables
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import evaluation_error_at_optimum as m2
from loop_runs import (
    CAMPAIGN_RUNS,
    EPSVMC,
    V5,
    WORKERS,
    Loop,
    campaign_for,
    config_of,
    evaluation_job,
    pool_mod,
    read_evaluation,
    records_mod,
)

NAME = "st_regression"
CHAIN_ROOT = m2.ERROR_ROOT / "chain"
TRACE_ROOT = m2.ROOT / "traced_optimisations"
POINTS = (("B0", 0), ("B2", 0))
STEP = 1e-3
TRACED = (
    ("B0", 1e-8, "campaign/optimisation/st_regression/B0/seed000"),
    ("B2", 1e-8, "campaign/optimisation/st_regression/B2/seed000"),
    ("B0", 1e-12, "supplementary/st_census_exact/st_regression/B0/seed000"),
    ("B2", 1e-12, "supplementary/st_census_exact/st_regression/B2/seed000"),
)


def sequence(n: int) -> list[tuple[str, int | None, int]]:
    """VMCON's evaluation order for one problem call: (label, column, sign)."""
    out = [("base", None, 0)]
    for c in range(n):
        out += [(f"col{c:02d}+", c, 1), (f"col{c:02d}-", c, -1)]
    out.append(("reconcile", None, 0))
    return out


def chain_dir(point: str, loop: Loop, k: int, label: str) -> Path:
    return CHAIN_ROOT / point / loop.slug / f"{k:02d}_{label}"


def _run(args):
    job, loop = args
    return pool_mod.run(job, campaign_for(loop, CHAIN_ROOT), resume=True)


def press_chains() -> None:
    for arm, seed in POINTS:
        opt = m2.optimum(NAME, arm, seed)
        point = m2.point_label(arm, seed)
        inp = m2.derived_input(NAME, opt, STEP, CHAIN_ROOT / point / "input")
        n = len(opt["xcs"])
        seq = sequence(n)
        loops = m2.loops_for(NAME)
        for k, (label, col, sign) in enumerate(seq):
            batch = []
            for loop in loops:
                campaign = campaign_for(loop, CHAIN_ROOT)
                config = config_of(campaign, NAME, inp)
                entry = opt["state_path"] if k == 0 else chain_dir(point, loop, k - 1, seq[k - 1][0]) / "y_exit.json"
                kw = {"entry_state": entry}
                if col is not None:
                    kw.update(regime="stencil", stencil_column=col, stencil_sign=sign)
                batch.append((evaluation_job(campaign, config, loop, chain_dir(point, loop, k, label), **kw), loop))
            print(f"== {point}: step {k} ({label}), {len(batch)} loops", flush=True)
            with ThreadPoolExecutor(max_workers=WORKERS) as ex:
                list(ex.map(_run, batch))


def partition_against_flat(point: str, n: int) -> dict:
    """Per (test set, τ): the partitioned chain against the flat chain at the same setting."""
    seq = sequence(n)
    out = {}
    for lp in m2.loops_for(NAME):
        if lp.arm != "A0":
            continue
        other = Loop("A2", lp.test_set, lp.tau)
        ra = [read_evaluation(chain_dir(point, lp, k, lab), lp) for k, (lab, _c, _s) in enumerate(seq)]
        rb = [read_evaluation(chain_dir(point, other, k, lab), other) for k, (lab, _c, _s) in enumerate(seq)]
        if any(r.get("objf") is None for r in ra + rb):
            out[(lp.test_set, lp.tau)] = None
            continue
        df = dc = 0.0
        for c in range(n):
            kp, km = 1 + 2 * c, 2 + 2 * c
            df = max(df, abs((ra[kp]["objf"] - ra[km]["objf"]) - (rb[kp]["objf"] - rb[km]["objf"])) / (2 * STEP))
            for i in range(len(ra[kp]["conf"])):
                dc = max(dc, abs((ra[kp]["conf"][i] - ra[km]["conf"][i]) - (rb[kp]["conf"][i] - rb[km]["conf"][i])) / (2 * STEP))
        out[(lp.test_set, lp.tau)] = {
            "same": sum(1 for a, b in zip(ra, rb, strict=True) if a["objf"] == b["objf"] and a["conf"] == b["conf"]),
            "n": len(ra),
            "value_f": max(abs(a["objf"] - b["objf"]) for a, b in zip(ra, rb, strict=True)),
            "value_c": max(max(abs(x - y) for x, y in zip(a["conf"], b["conf"], strict=True)) for a, b in zip(ra, rb, strict=True)),
            "deriv_f": df,
            "deriv_c": dc,
        }
    return out


def tables_chains() -> dict:
    eps = EPSVMC[NAME]
    result = {}
    for arm, seed in POINTS:
        opt = m2.optimum(NAME, arm, seed)
        point = m2.point_label(arm, seed)
        n = len(opt["xcs"])
        seq = sequence(n)
        loops = m2.loops_for(NAME)
        runs = {lp: [read_evaluation(chain_dir(point, lp, k, lab), lp) for k, (lab, _c, _s) in enumerate(seq)] for lp in loops}
        exact = runs[m2.EXACT[NAME]]
        heads = sorted({r.get("tree_git_head") for rs in runs.values() for r in rs if r.get("tree_git_head")})
        print(f"\n## Chain at {point} ({arm} seed {seed}'s end point, entered from its own final state); n = {n}; step {STEP:g}; epsvmc {eps:g}\n")
        print(f"records made at: {heads}; objective of the run's record {opt['norm_objf']!r}, exact loop's base "
              f"{exact[0].get('objf')!r}\n")
        # exactness: the exact loop's chain against the check loop's chain
        chk = runs[m2.EXACT_CHECK[NAME]]
        dmax = max(
            max([abs(a["objf"] - b["objf"])] + [abs(x - y) for x, y in zip(a["conf"], b["conf"], strict=True)])
            for a, b in zip(exact, chk, strict=True) if a.get("objf") is not None and b.get("objf") is not None
        )
        print(f"exactness: largest difference between the {m2.EXACT[NAME].label} and {m2.EXACT_CHECK[NAME].label} chains, "
              f"objective and every constraint, all {len(seq)} points: {dmax:.1e}\n")
        print("| loop | runs ok | node calls per evaluation (mean) | value error, largest over the chain: objective / constraints | "
              "f: common / non-common / derivative error | c: common / non-common / derivative error | largest derivative error / epsvmc |")
        print("|---|---|---|---|---|---|---|")
        rows = []
        for lp in loops:
            rs = runs[lp]
            ok = sum(1 for r in rs if r.get("status") == "ok")
            if ok != len(rs):
                print(f"| {lp.label} | {ok}/{len(rs)} | | | | | |")
                continue
            vf = max(abs(r["objf"] - x["objf"]) for r, x in zip(rs, exact, strict=True))
            vc = max(max(abs(a - b) for a, b in zip(r["conf"], x["conf"], strict=True)) for r, x in zip(rs, exact, strict=True))
            cf = ncf = gf = cc = ncc = gc = 0.0
            for c in range(n):
                kp, km = 1 + 2 * c, 2 + 2 * c
                efp, efm = rs[kp]["objf"] - exact[kp]["objf"], rs[km]["objf"] - exact[km]["objf"]
                cf, ncf = max(cf, abs(efp + efm) / 2), max(ncf, abs(efp - efm) / 2)
                gf = max(gf, abs(efp - efm) / (2 * STEP))
                for a, b, xa, xb in zip(rs[kp]["conf"], rs[km]["conf"], exact[kp]["conf"], exact[km]["conf"], strict=True):
                    ea, eb = a - xa, b - xb
                    cc, ncc = max(cc, abs(ea + eb) / 2), max(ncc, abs(ea - eb) / 2)
                    gc = max(gc, abs(ea - eb) / (2 * STEP))
            nodes = statistics.mean(r.get("node_calls") or 0 for r in rs)
            print(f"| {lp.label} | {ok}/{len(rs)} | {nodes:.1f} | {vf:.1e} / {vc:.1e} | {cf:.1e} / {ncf:.1e} / {gf:.1e} | "
                  f"{cc:.1e} / {ncc:.1e} / {gc:.1e} | {max(gf, gc) / eps:.2g} |")
            rows.append({"loop": lp.label, "value_f": vf, "value_c": vc, "grad_f": gf, "grad_c": gc,
                         "common_f": cf, "noncommon_f": ncf, "common_c": cc, "noncommon_c": ncc, "nodes": nodes})
        # the same point twice: the base (entered from the converged state) and the reconcile call (entered
        # after the whole stencil) -- a difference is history dependence, nothing else
        print("\nThe same design point evaluated twice in the chain -- first (the base, entered from the "
              "converged state) and last (the reconcile call, entered after all 2n stencil points): the difference "
              "is what the history alone does to the value.\n")
        print("| loop | objective: reconcile − base | largest constraint: |reconcile − base| |")
        print("|---|---|---|")
        for lp in loops:
            a, b = runs[lp][0], runs[lp][-1]
            if a.get("objf") is None or b.get("objf") is None:
                continue
            print(f"| {lp.label} | {b['objf'] - a['objf']:.1e} | "
                  f"{max(abs(x - y) for x, y in zip(a['conf'], b['conf'], strict=True)):.1e} |")
        # the partitioned loop against the flat loop at the same setting: the partition's own contribution
        print("\nThe partitioned loop against the flat loop at the same test set and τ, along the same chain "
              "(largest over the points or columns; derivative differences at the step):\n")
        print("| setting | points whose objective and constraints are bit-identical | value difference: objective / constraints | "
              "derivative difference: objective / constraints |")
        print("|---|---|---|---|")
        for (ts, tau), d in partition_against_flat(point, n).items():
            if d is None:
                continue
            print(f"| {ts} {tau:.0e} | {d['same']} of {d['n']} | {d['value_f']:.1e} / {d['value_c']:.1e} | "
                  f"{d['deriv_f']:.1e} / {d['deriv_c']:.1e} |")
        # block loops that accepted their entry after one sweep with a nonzero change
        print("\nAlong the chain: per block, evaluations whose loop stopped after its first sweep with a first-sweep "
              "change that was not zero (the entry's lag accepted and carried on), and the largest such change:\n")
        print("| loop | block: evaluations / largest carried change |")
        print("|---|---|")
        for lp in loops:
            if lp.arm == "AR":
                continue
            per: dict = {}
            for r in runs[lp]:
                for b, vals in (r.get("residual_per_sweep") or {}).items():
                    d = per.setdefault(b, [0, 0.0])
                    if len(vals) == 1 and vals[0] != 0.0:
                        d[0] += 1
                        d[1] = max(d[1], vals[0])
            print(f"| {lp.label} | " + "; ".join(f"{b}: {v[0]} / {v[1]:.1e}" for b, v in per.items()) + " |")
        result[point] = rows
    return result


# --------------------------------------------------------------------------
# part 2: the traced optimisations
# --------------------------------------------------------------------------


def trace_jobs():
    out = []
    for arm, tau, _src in TRACED:
        loop = Loop(arm, "census", tau)
        campaign = campaign_for(loop, TRACE_ROOT)
        config = config_of(campaign, NAME)
        outdir = TRACE_ROOT / f"{arm}_census_tau{tau:.0e}" / "seed000"
        job = pool_mod.Job(
            phase="B", arm=arm, config=config, seed=0, outdir=outdir,
            regime="unperturbed", delta=campaign.delta, run_kind="smoke",
            override_env={"PROCESS_ARCH_BLOCK_TRACE": str(outdir / "block_trace.jsonl")},
        )
        out.append((job, loop))
    return out


def _run_trace(args):
    job, loop = args
    return pool_mod.run(job, campaign_for(loop, TRACE_ROOT), resume=True)


def press_traces() -> None:
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        list(ex.map(_run_trace, trace_jobs()))


def tables_traces() -> None:
    print("\n## The traced optimisations (st, seed 0)\n")
    print("| arm, τ | reproduces its record (iterations, evaluations, norm_objf to the bit) | iterations | "
          "evaluations traced | of which gradient evaluations | block loops stopped after one sweep, any change: block: evaluations | "
          "gradient evaluations with a loop that stopped after one sweep carrying a nonzero change: "
          "block: evaluations (share of gradient evaluations), largest change |")
    print("|---|---|---|---|---|---|---|")
    per_iter_all = {}
    for (job, loop), (arm, tau, src) in zip(trace_jobs(), TRACED, strict=True):
        rec = records_mod.read(job.outdir)
        ref = records_mod.read(V5 / "runs" / src)
        same = (
            rec.get("n_solver_iterations") == ref.get("n_solver_iterations")
            and [a.get("n_iterations") for a in rec.get("attempts") or []] == [a.get("n_iterations") for a in ref.get("attempts") or []]
            and [((a.get("sweeps_per_eval") or {}).get("n_evaluations")) for a in rec.get("attempts") or []]
            == [((a.get("sweeps_per_eval") or {}).get("n_evaluations")) for a in ref.get("attempts") or []]
            and (rec.get("exact") or {}).get("norm_objf") == (ref.get("exact") or {}).get("norm_objf")
        )
        path = job.outdir / "block_trace.jsonl"
        lines = [json.loads(s) for s in path.read_text().splitlines() if s.strip()] if path.exists() else []
        lines = [ln for ln in lines if ln.get("kind") != "header"]
        grads = [ln for ln in lines if isinstance(ln.get("evaluation"), list) and ln["evaluation"] and ln["evaluation"][0] == "gradient"]
        per: dict = {}
        per_iter: dict = {}
        single: dict = {}
        for ln in grads:
            it = ln.get("iteration")
            per_iter.setdefault(it, {}).setdefault("_n", [0, 0.0])[0] += 1
            for b, sweeps in (ln.get("per_sweep") or {}).items():
                vals = [max(s["max"].values()) if s["max"] else 0.0 for s in sweeps]
                if len(vals) == 1:
                    single[b] = single.get(b, 0) + 1
                if len(vals) == 1 and vals[0] != 0.0:
                    d = per.setdefault(b, [0, 0.0])
                    d[0] += 1
                    d[1] = max(d[1], vals[0])
                    pi = per_iter.setdefault(it, {}).setdefault(b, [0, 0.0])
                    pi[0] += 1
                    pi[1] = max(pi[1], vals[0])
        per_iter_all[(arm, tau)] = (per_iter, len(grads))
        cells = "; ".join(f"{b}: {v[0]} ({v[0] / max(len(grads), 1):.0%}), {v[1]:.1e}" for b, v in per.items()) or "none"
        one = "; ".join(f"{b}: {v}" for b, v in single.items()) or "none"
        print(f"| {arm}, {tau:g} | {'yes' if same else 'NO'} | {rec.get('n_solver_iterations')} | {len(lines)} | {len(grads)} | {one} | {cells} |")
    print("\nPer iteration (the solver's iteration counter at the evaluation), the partitioned arm at 1e-8 and 1e-12: "
          "M2's gradient evaluations that carried a nonzero change after one sweep, and the largest such change:\n")
    for key in (("B2", 1e-8), ("B2", 1e-12)):
        per_iter, ng = per_iter_all.get(key, ({}, 0))
        txt = ", ".join(f"{it}: {v['M2'][0]} of {v['_n'][0]} ({v['M2'][1]:.0e})" for it, v in sorted(per_iter.items()) if "M2" in v)
        print(f"- {key[0]} at {key[1]:g}: {txt or 'none'}")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--press", action="store_true")
    p.add_argument("--tables", action="store_true")
    p.add_argument("--trace-press", action="store_true")
    p.add_argument("--trace-tables", action="store_true")
    args = p.parse_args(argv)
    if args.trace_press:
        press_traces()
    if args.press:
        press_chains()
    if args.trace_tables:
        tables_traces()
    if args.tables:
        tables_chains()
    return 0


if __name__ == "__main__":
    sys.exit(main())
