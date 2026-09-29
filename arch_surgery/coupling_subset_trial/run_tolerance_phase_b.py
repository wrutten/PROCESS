#!/usr/bin/env python
"""Whole optimisations with the census test set at the derived tolerance, paired with the campaign.

Task A93 (tolerance-phase-b); V5 improvement list item 6, last prerequisite.
V4's optimisation arms stop every coupling-state loop on the whole state ``y``
at τ = 1e-6.  V5 will stop on the census-measured read-before-write set at
the derived τ = 1e-8 (ruling D32).  A89 measured the effect on single
evaluations; this measures it on **whole optimisations**: does the optimiser
take the same path (iterations, evaluations), reach the same optimum
(``norm_objf``), what does each evaluation cost (node calls, sweeps), and does
the exit audit hold.

Three variants per configuration and seed, each one optimisation of V4's
child through :mod:`narrowed_optimise` (nothing in the V4 folder is edited)::

    B0 rbw    the flat control, the census FLAT set, τ = 1e-8   (V5's control)
    B2 rbw    the partitioned arm, the census M1/M2/M3 sets, τ = 1e-8   (V5's intervention)
    B0 full   the flat control, the whole-y test, τ = 1e-8   (tolerance alone)

The fourth member of each quartet is the campaign's own record of the same
arm and seed at whole-``y`` τ = 1e-6, read from the relocated campaign tree
(read-only, through V4's ``records.read`` so the arm names of its day are
translated: its ``B3`` directory is today's ``B2``).  A run is entry-paired
with that record by the seed: the V4 child displaces the design vector by the
seed, and the pairing is verified by comparing the displaced vector (hex).

Seeds: the first :data:`N_SEEDS` seeds, in ascending order, of the campaign's
every-arm-converged set for the configuration (the V4 report's one seed set,
``stats.every_arm_converged``), so every quartet has a converged campaign
member — 0–4 where those are in the set, the next in the set otherwise.

Stages, each reachable from this entry point::

    --lift         derive the lifted input file (B2's) with V4's own stage,
                   gated on the committed digest, into this task's runs dir
    --run          the optimisations, one PROCESS process at a time
    --summarise    records -> summary.json and every table (no PROCESS run)

Runs one at a time (``workers = 1``): another task runs on the machine, and
the acceptance quantities are counts, which do not care.  Records under
``arch_surgery/idf_probe/runs/tolerance_phase_b/`` (untracked).  The campaign
tree is never written.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parent.parent
V4_DIR = HERE.parent / "MDA_partitioning_experiment_v4"
RUNS = TREE / "arch_surgery" / "idf_probe" / "runs" / "tolerance_phase_b"
WRAPPER = HERE / "narrowed_optimise.py"
TOLERANCE_FILE = HERE / "tolerance.json"
RBW_SETS_FILE = HERE / "rbw_sets.json"
#: The campaign's optimisation records, relocated at A90's retirement.  Read only.
CAMPAIGN_RECORDS = Path(
    "/home/wrutten/projects/PROCESS_surgery/arch_surgery/idf_probe/runs/A90_runs/"
    "campaign/optimisation"
)

sys.path.insert(0, str(V4_DIR))
sys.dont_write_bytecode = True

from harness.core import config as config_mod  # noqa: E402
from harness.core import pool as pool_mod  # noqa: E402
from harness.core import records as records_mod  # noqa: E402
from harness.experiment import input_files as input_files_mod  # noqa: E402
from harness.measurement import stats as stats_mod  # noqa: E402

V4_TAU = 1e-6
#: (optimisation arm, test set) -> label.  Order is the order of the tables.
VARIANTS = (("B0", "rbw"), ("B2", "rbw"), ("B0", "full"))
N_SEEDS = 5
CONFIGURATIONS = ("large_tokamak_nof", "low_aspect_ratio_DEMO", "st_regression")
#: V4's same-optimum yardstick floor (EXPERIMENT_REPORT.md §3.5 check 1).
OBJF_FLOOR_REL = 1e-6
WORKERS = 1


def chosen_tau() -> float:
    return float(json.loads(TOLERANCE_FILE.read_text())["chosen_tau"])


def campaign(tau):
    base = config_mod.default_campaign()
    return dataclasses.replace(base, runs_dir=RUNS, derived_input_dir=RUNS / "input_files",
                               tau=tau, workers=WORKERS)


def variant_label(arm, test_set):
    return f"{arm}_{test_set}"


def run_dir(config_name, arm, test_set, seed):
    return RUNS / config_name / variant_label(arm, test_set) / f"seed{seed:03d}"


# --------------------------------------------------------------------------
# the campaign's records (read-only)
# --------------------------------------------------------------------------


def campaign_records(config_name):
    """``{arm: {seed: record}}`` in today's arm names, through V4's reader."""
    by_arm: dict = {}
    root = CAMPAIGN_RECORDS / config_name
    for d in sorted(root.iterdir()):
        if d.name.startswith(".") or not d.is_dir():
            continue
        for sd in sorted(d.iterdir()):
            if not sd.is_dir() or not sd.name.startswith("seed"):
                continue
            rec = records_mod.read(sd)
            if rec.get("status") == "no_record":
                continue
            rec["_dir"] = str(sd)
            by_arm.setdefault(rec["campaign_arm"], {})[int(rec["campaign_seed"])] = rec
    return by_arm


def seed_set(config_name, by_arm=None):
    """The first N_SEEDS of the campaign's every-arm-converged set, ascending."""
    by_arm = by_arm or campaign_records(config_name)
    seeds = sorted(next(iter(by_arm.values())))
    converged = stats_mod.every_arm_converged(by_arm, seeds)
    return converged[:N_SEEDS], converged


# --------------------------------------------------------------------------
# running
# --------------------------------------------------------------------------


def job(config, camp, arm, seed, outdir):
    return pool_mod.Job(
        phase="B", arm=arm, config=config, seed=seed, outdir=outdir,
        regime="perturbed" if seed else "unperturbed", delta=camp.delta,
        run_kind="smoke")


def environment(j, camp):
    env, terms = pool_mod.environment_for(j, camp)
    env = dict(env)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["NUMBA_CACHE_DIR"] = str(RUNS / "numba_cache")
    return env, terms


def launch(command, env, outdir, meta, timeout):
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "command.json").write_text(json.dumps({
        "command": command, "meta": meta,
        "architecture_environment": {k: v for k, v in env.items() if k.startswith("PROCESS_ARCH")},
        "pythonpath": env.get("PYTHONPATH")}, indent=1))
    try:
        done = subprocess.run(command, env=env, capture_output=True, text=True,
                              cwd=str(outdir), timeout=timeout)
        (outdir / "stdout.log").write_text(done.stdout)
        (outdir / "stderr.log").write_text(done.stderr)
        return done.returncode
    except subprocess.TimeoutExpired:
        return 124


def run_optimise(j, camp, arm, test_set):
    outdir = Path(j.outdir)
    if (outdir / "metrics.json").exists():
        rec = records_mod.read(outdir)
        print(f"  kept   {j.config.name:22s} {arm} {test_set:5s} seed={j.seed} "
              f"status={rec.get('status')}", flush=True)
        return
    env, terms = environment(j, camp)
    command = pool_mod._command(j, camp, terms)  # V4's own composition
    assert command[1].endswith("optimise.py"), command[:2]
    assert env["PYTHONPATH"] == str(camp.tree), env["PYTHONPATH"]  # trap T6
    command = [command[0], str(WRAPPER), "--test-set", test_set, "--", *command[2:]]
    t0 = time.perf_counter()
    rc = launch(command, env, outdir, {"arm": arm, "test_set": test_set, "tau": camp.tau,
                                       "seed": j.seed}, j.timeout)
    wall = time.perf_counter() - t0
    if not (outdir / "metrics.json").exists():
        (outdir / "metrics.json").write_text(json.dumps({"status": "no_record", "returncode": rc}))
    (outdir / "launch.json").write_text(json.dumps({"returncode": rc, "wall_s_launcher": wall}))
    rec = records_mod.read(outdir)
    print(f"  {j.config.name:22s} {arm} {test_set:5s} seed={j.seed} rc={rc} "
          f"status={rec.get('status')} ifail={(rec.get('mfile') or {}).get('ifail')} "
          f"evals={(rec.get('sweeps_per_eval') or {}).get('n_evaluations')} {wall:5.0f}s",
          flush=True)


def stage_lift():
    camp = campaign(chosen_tau())
    rc, record = input_files_mod.stage_derive(camp, resume=True)
    (RUNS / "input_files" / "stage_derive.json").write_text(json.dumps(record, indent=1, default=str))
    print(json.dumps({k: v for k, v in record.items() if k != "configurations"},
                     indent=1, default=str))
    for row in record.get("configurations", []):
        print(row.get("configuration"), row.get("verdict"), row.get("derived_sha256"),
              row.get("recorded_sha256"))
    return rc


def stage_run(names, variants):
    camp = campaign(chosen_tau())
    for c in camp.configurations:
        if names and c.name not in names:
            continue
        seeds, _ = seed_set(c.name)
        print(f"{c.name}: seeds {seeds}", flush=True)
        for arm, test_set in VARIANTS:
            if variants and variant_label(arm, test_set) not in variants:
                continue
            for seed in seeds:
                j = job(c, camp, arm, seed, run_dir(c.name, arm, test_set, seed))
                run_optimise(j, camp, arm, test_set)


# --------------------------------------------------------------------------
# summarising
# --------------------------------------------------------------------------


def hexf(v):
    return None if v is None else float(v).hex()


def rel_diff(a, b):
    if a is None or b is None:
        return None
    d = max(abs(a), abs(b))
    return abs(a - b) / d if d else 0.0


def audit_recount(d, taus=(1e-8, 1e-6)):
    """Components of the whole-y exit residual at or above each τ, from the vector.

    The record's own ``n_above`` is at the run's τ; this recounts the same
    vector (frozen ruler) at both tolerances so the campaign's records and
    this task's read on one ruler.  ``restricted`` excludes the components
    the per-run deferred nodes write (the record's ``excluded_keys``), which
    is V4's statistic for the arm whose per-run nodes have not run at the
    audit position.
    """
    p = Path(d) / "audit_residual.json"
    if not p.exists():
        return None
    a = json.loads(p.read_text())
    sc = {k: float.fromhex(v) for k, v in a["rulers"]["frozen"]["scaled_hex"].items()}
    ex = set(a.get("excluded_keys") or [])
    out = {"n_continuous": len(sc), "n_excluded": len(ex),
           "max": max(sc.values()) if sc else None,
           "max_restricted": max((v for k, v in sc.items() if k not in ex), default=None),
           "n_discrete_mismatch": len(a.get("discrete_mismatch") or []),
           "n_moved_constant": len(a.get("moved_constant") or []),
           "n_nan_new": len(a.get("nan_new") or [])}
    for tau in taus:
        out[f"n_above_{tau:.0e}"] = sum(1 for v in sc.values() if v >= tau)
        out[f"n_above_{tau:.0e}_restricted"] = sum(1 for k, v in sc.items() if k not in ex and v >= tau)
    return out


def perturbation_rows(d):
    p = Path(d) / "perturbation.json"
    if not p.exists():
        return None
    return json.loads(p.read_text())["per_variable"]


def pairing(mine_dir, theirs_dir, seed):
    """The displaced design vector, hex for hex, against the campaign record's."""
    a, b = perturbation_rows(mine_dir), perturbation_rows(theirs_dir)
    if seed == 0:
        return {"n_variables": None, "n_identical": None,
                "identical": a is None and b is None,
                "note": "seed 0 is the input file's own point in both; no displacement to compare"}
    if a is None or b is None:
        return {"identical": False, "note": "a perturbation file is missing"}
    if len(a) != len(b) or [r["ixc"] for r in a] != [r["ixc"] for r in b]:
        return {"identical": False, "n_variables": len(a), "n_identical": 0,
                "note": "the variable lists differ"}
    same = sum(1 for x, y in zip(a, b)
               if hexf(x["factor"]) == hexf(y["factor"])
               and hexf(x["scaled_after"]) == hexf(y["scaled_after"]))
    return {"n_variables": len(a), "n_identical": same, "identical": same == len(a)}


def extract(rec, d):
    """The comparison fields of one record, mine or the campaign's."""
    if rec.get("status") == "no_record":
        return {"status": "no_record", "dir": str(d)}
    ea = rec.get("exit_audit") or {}
    aa = rec.get("attempt_accounting") or {}
    spe = rec.get("sweeps_per_eval") or {}
    blt = rec.get("block_loop_totals") or {}
    c93 = rec.get("constraint_93")
    C = spe.get("n_evaluations")
    N = rec.get("node_calls_solve_phase")
    hist = {int(k): v for k, v in (spe.get("hist") or {}).items()}
    sweeps_sorted = sorted(k for k in hist for _ in range(hist[k]))
    solves = blt.get("solves_by_block") or {}
    sweeps_by_block = blt.get("sweeps_by_block") or {}
    return {
        "dir": str(d),
        "status": rec.get("status"),
        "failure_class": rec.get("failure_class"),
        "ifail": (rec.get("mfile") or {}).get("ifail"),
        "accepted": stats_mod.accepted_optimum(rec),
        "tau": rec.get("campaign_tau"),
        "tree_git_head": rec.get("tree_git_head"),
        "n_attempts": aa.get("n_attempts"),
        "retried": stats_mod.retried(rec) if rec.get("attempts") is not None else None,
        "iterations_per_attempt": aa.get("iterations_per_attempt"),
        "ifail_per_attempt": aa.get("ifail_per_attempt"),
        "n_solver_iterations_final": rec.get("n_solver_iterations"),
        "n_solver_iterations_summed": (rec.get("exit_forensics") or {}).get(
            "n_solver_iterations_summed_over_attempts"),
        "n_evaluations": C,
        "node_calls_solve_phase": N,
        "node_calls_per_evaluation": (N / C) if (N and C) else None,
        "dispatch_sweeps_solve_phase": rec.get("dispatch_sweeps_solve_phase"),
        "sweeps_per_eval_mean": spe.get("mean"),
        "sweeps_per_eval_median": (sweeps_sorted[len(sweeps_sorted) // 2] if sweeps_sorted else None),
        "sweeps_per_eval_min": (sweeps_sorted[0] if sweeps_sorted else None),
        "sweeps_per_eval_max": (sweeps_sorted[-1] if sweeps_sorted else None),
        "sweeps_per_eval_hist": {str(k): hist[k] for k in sorted(hist)},
        "sweeps_by_block": sweeps_by_block,
        "sweeps_per_solve_by_block": {
            b: (sweeps_by_block[b] / solves[b]) for b in sweeps_by_block if solves.get(b)},
        "predicate_evaluations": rec.get("predicate_evaluations"),
        "components_compared": rec.get("components_compared"),
        "norm_objf": (rec.get("values") or {}).get("norm_objf"),
        "norm_objf_hex": (rec.get("exact") or {}).get("norm_objf"),
        "sqsumsq": (rec.get("values") or {}).get("sqsumsq"),
        "audit_tau_of_record": ea.get("tau_for_the_brief"),
        "audit_max": ea.get("residual_max"),
        "audit_n_above_of_record": (ea.get("brief") or {}).get("n_above"),
        "audit_restricted_n_above_of_record": (ea.get("restricted") or {}).get("n_above"),
        "audit": audit_recount(d),
        "constraint_93": None if not c93 or "error" in c93 else {
            "residual_s": c93.get("residual_s"),
            "residual_relative_to_burn_time": c93.get("residual_relative_to_burn_time"),
            "normalised_residual_rcm": c93.get("normalised_residual_rcm")},
        "wall_s": rec.get("wall_s"),
        "cpu_s": rec.get("cpu_s"),
    }


def summarise():
    tau = chosen_tau()
    rbw = json.loads(RBW_SETS_FILE.read_text())["configurations"]
    out = {"generated_by": "arch_surgery/coupling_subset_trial/run_tolerance_phase_b.py --summarise",
           "tau": tau, "v4_tau": V4_TAU, "campaign_records": str(CAMPAIGN_RECORDS),
           "variants": [variant_label(a, t) for a, t in VARIANTS], "configurations": {}}
    for name in CONFIGURATIONS:
        by_arm = campaign_records(name)
        seeds, converged = seed_set(name, by_arm)
        cfg = {"seeds": seeds, "every_arm_converged": converged,
               "n_by_block": {arm: rbw[name][arm]["n_by_block"] for arm in ("A0", "A2")},
               "per_seed": {}}
        for seed in seeds:
            q = {}
            for arm in ("B0", "B2"):
                rec = by_arm[arm][seed]
                q[f"{arm}_campaign"] = extract(rec, Path(rec["_dir"]))
            for arm, ts in VARIANTS:
                d = run_dir(name, arm, ts, seed)
                rec = records_mod.read(d)
                e = extract(rec, d)
                n = Path(d) / "narrowing.json"
                e["narrowing"] = json.loads(n.read_text()) if n.exists() else None
                e["pairing"] = pairing(d, Path(by_arm[arm][seed]["_dir"]), seed)
                base = q[f"{arm}_campaign"]
                e["against_campaign"] = {
                    "objf_rel_diff": rel_diff(e.get("norm_objf"), base.get("norm_objf")),
                    "objf_within_floor": (rel_diff(e.get("norm_objf"), base.get("norm_objf")) or 0.0)
                    <= OBJF_FLOOR_REL if e.get("norm_objf") is not None else None,
                    "d_iterations_summed": (
                        e["n_solver_iterations_summed"] - base["n_solver_iterations_summed"]
                        if e.get("n_solver_iterations_summed") is not None
                        and base.get("n_solver_iterations_summed") is not None else None),
                    "evaluations_ratio": (e["n_evaluations"] / base["n_evaluations"]
                                          if e.get("n_evaluations") and base.get("n_evaluations") else None),
                    "node_calls_ratio": (e["node_calls_solve_phase"] / base["node_calls_solve_phase"]
                                         if e.get("node_calls_solve_phase") and base.get("node_calls_solve_phase") else None),
                    "node_calls_per_evaluation_ratio": (
                        e["node_calls_per_evaluation"] / base["node_calls_per_evaluation"]
                        if e.get("node_calls_per_evaluation") and base.get("node_calls_per_evaluation") else None),
                }
                q[variant_label(arm, ts)] = e
            cfg["per_seed"][str(seed)] = q
        cfg["decomposition"] = decomposition(cfg["per_seed"], seeds)
        out["configurations"][name] = cfg
    (RUNS / "summary.json").write_text(json.dumps(out, indent=1))
    return out


def decomposition(per_seed, seeds):
    """R = ρ × ε for B2/B0, pooled over the seed set and as per-seed medians.

    Two pairs: the campaign's (whole-y, τ = 1e-6) and this task's census pair
    (rbw, τ = 1e-8); a third, B0 full at 1e-8 against B0 campaign, isolates
    the tolerance.  Pooled: sums over the seeds where both members are
    accepted optima (V4's cost population).  R equals ρ × ε exactly on pooled
    sums; the per-seed medians need not multiply.
    """
    pairs = {"campaign_1e-6": ("B2_campaign", "B0_campaign"),
             "census_1e-8": ("B2_rbw", "B0_rbw"),
             "B0_full_1e-8_vs_B0_campaign": ("B0_full", "B0_campaign"),
             "B0_rbw_1e-8_vs_B0_campaign": ("B0_rbw", "B0_campaign"),
             "B2_rbw_1e-8_vs_B2_campaign": ("B2_rbw", "B2_campaign"),
             "B0_rbw_1e-8_vs_B0_full_1e-8": ("B0_rbw", "B0_full")}
    out = {}
    for label, (num, den) in pairs.items():
        used = [s for s in seeds if per_seed[str(s)][num].get("accepted")
                and per_seed[str(s)][den].get("accepted")]
        if not used:
            out[label] = {"seeds_used": [], "note": "no seed with both members accepted"}
            continue
        Nn = sum(per_seed[str(s)][num]["node_calls_solve_phase"] for s in used)
        Nd = sum(per_seed[str(s)][den]["node_calls_solve_phase"] for s in used)
        Cn = sum(per_seed[str(s)][num]["n_evaluations"] for s in used)
        Cd = sum(per_seed[str(s)][den]["n_evaluations"] for s in used)
        per = []
        for s in used:
            a, b = per_seed[str(s)][num], per_seed[str(s)][den]
            per.append({"seed": s,
                        "R": a["node_calls_solve_phase"] / b["node_calls_solve_phase"],
                        "rho": a["node_calls_per_evaluation"] / b["node_calls_per_evaluation"],
                        "eps": a["n_evaluations"] / b["n_evaluations"]})
        med = lambda k: sorted(p[k] for p in per)[len(per) // 2]  # noqa: E731 nearest-rank upper-middle, V4's
        out[label] = {"numerator": num, "denominator": den, "seeds_used": used,
                      "n_seeds_offered": len(seeds),
                      "pooled": {"R": Nn / Nd, "rho": (Nn / Cn) / (Nd / Cd), "eps": Cn / Cd,
                                 "N_num": Nn, "N_den": Nd, "C_num": Cn, "C_den": Cd},
                      "per_seed": per,
                      "median": {"R": med("R"), "rho": med("rho"), "eps": med("eps")},
                      "range": {k: [min(p[k] for p in per), max(p[k] for p in per)]
                                for k in ("R", "rho", "eps")}}
    return out


# --------------------------------------------------------------------------
# tables
# --------------------------------------------------------------------------

MEMBERS = ("B0_campaign", "B0_full", "B0_rbw", "B2_campaign", "B2_rbw")
MEMBER_NAMES = {"B0_campaign": "B0 whole-y 1e-6 (campaign)", "B0_full": "B0 whole-y 1e-8",
                "B0_rbw": "B0 census 1e-8", "B2_campaign": "B2 whole-y 1e-6 (campaign)",
                "B2_rbw": "B2 census 1e-8"}


def f(v, fmt="{:.3g}"):
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float):
        return fmt.format(v)
    return str(v)


def table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(lines)


def print_tables(out):
    tau = out["tau"]
    print(f"\n# Tolerance in phase B — tables (τ = {tau:.0e}; campaign τ = {out['v4_tau']:.0e})\n")
    print("Members: " + "; ".join(f"`{k}` = {v}" for k, v in MEMBER_NAMES.items()) + "\n")

    # 0 — seeds and test-set widths
    rows = []
    for name, cfg in out["configurations"].items():
        rows.append([name, ", ".join(map(str, cfg["seeds"])), len(cfg["every_arm_converged"]),
                     cfg["n_by_block"]["A0"].get("FLAT"),
                     ", ".join(f"{k} {v}" for k, v in cfg["n_by_block"]["A2"].items())])
    print("## T0 — seeds and the census test sets\n")
    print(table(["configuration", "seeds run", "n every-arm-converged (campaign)",
                 "census FLAT width (B0)", "census widths per block (B2)"], rows))

    # 1 — pairing and status
    print("\n## T1 — entry pairing and outcome, per run\n")
    rows = []
    for name, cfg in out["configurations"].items():
        for s, q in cfg["per_seed"].items():
            for m in ("B0_full", "B0_rbw", "B2_rbw"):
                e = q[m]
                pr = e.get("pairing") or {}
                rows.append([name, s, m, e.get("status"), f(e.get("ifail")), e.get("n_attempts"),
                             f"{pr.get('n_identical')}/{pr.get('n_variables')}" if pr.get("n_variables") else
                             ("n/a (seed 0)" if s == "0" else "—"),
                             f(pr.get("identical")), (e.get("tree_git_head") or "")[:8],
                             f(e.get("wall_s"), "{:.0f}")])
    print(table(["configuration", "seed", "run", "status", "ifail", "attempts",
                 "displaced x identical (hex)", "paired", "tree", "wall s (context)"], rows))

    # 2 — path and optimum, per seed, five members
    print("\n## T2 — the optimiser's path and its optimum, per seed\n")
    rows = []
    for name, cfg in out["configurations"].items():
        for s, q in cfg["per_seed"].items():
            for m in MEMBERS:
                e = q[m]
                ag = e.get("against_campaign") or {}
                rows.append([name, s, m, f(e.get("ifail")), e.get("n_attempts"),
                             "/".join(map(str, e.get("iterations_per_attempt") or [])),
                             e.get("n_solver_iterations_summed"), e.get("n_evaluations"),
                             e.get("node_calls_solve_phase"),
                             f(e.get("node_calls_per_evaluation"), "{:.1f}"),
                             f(e.get("sweeps_per_eval_mean"), "{:.2f}"),
                             f(e.get("norm_objf"), "{:.12g}"),
                             f(ag.get("objf_rel_diff"), "{:.1e}") if ag else "—",
                             f(ag.get("d_iterations_summed")) if ag else "—",
                             f(ag.get("evaluations_ratio"), "{:.4f}") if ag else "—",
                             f(ag.get("node_calls_ratio"), "{:.4f}") if ag else "—"])
    print(table(["configuration", "seed", "run", "ifail", "attempts", "iterations per attempt",
                 "iterations Σ", "evaluations C", "node calls N", "N/C", "sweeps/eval mean",
                 "norm_objf", "|Δf|/max rel. to campaign", "Δ iterations Σ", "C ratio", "N ratio"],
                rows))

    # 3 — sweeps per evaluation distribution and per-block sweeps
    print("\n## T3 — sweeps per evaluation and per block, per seed\n")
    rows = []
    for name, cfg in out["configurations"].items():
        for s, q in cfg["per_seed"].items():
            for m in MEMBERS:
                e = q[m]
                if e.get("status") != "ok":
                    rows.append([name, s, m, e.get("status")] + ["—"] * 6)
                    continue
                rows.append([name, s, m, e.get("n_evaluations"),
                             f"{e['sweeps_per_eval_min']}/{e['sweeps_per_eval_median']}/"
                             f"{e['sweeps_per_eval_mean']:.2f}/{e['sweeps_per_eval_max']}",
                             " ".join(f"{k}:{v}" for k, v in e["sweeps_per_eval_hist"].items()),
                             ", ".join(f"{b} {v:.2f}" for b, v in e["sweeps_per_solve_by_block"].items()),
                             e.get("predicate_evaluations"), e.get("components_compared"),
                             f(e["components_compared"] / e["predicate_evaluations"], "{:.0f}")
                             if e.get("predicate_evaluations") else "—"])
    print(table(["configuration", "seed", "run", "evaluations", "sweeps/eval min/median/mean/max",
                 "histogram sweeps:count", "sweeps per solve by block", "predicate evaluations",
                 "components compared", "mean test width"], rows))

    # 4 — exit audit
    print("\n## T4 — exit audit (whole y, frozen ruler, at the entry to the output path), per seed\n")
    rows = []
    for name, cfg in out["configurations"].items():
        for s, q in cfg["per_seed"].items():
            for m in MEMBERS:
                e = q[m]
                a = e.get("audit") or {}
                c93 = e.get("constraint_93") or {}
                rows.append([name, s, m, f(e.get("audit_tau_of_record"), "{:.0e}"),
                             f(a.get("max"), "{:.1e}"), a.get("n_above_1e-06"), a.get("n_above_1e-08"),
                             f(a.get("max_restricted"), "{:.1e}"), a.get("n_above_1e-06_restricted"),
                             a.get("n_above_1e-08_restricted"), a.get("n_excluded"),
                             a.get("n_discrete_mismatch"),
                             f(c93.get("normalised_residual_rcm"), "{:.1e}") if c93 else "—"])
    print(table(["configuration", "seed", "run", "τ of record", "max (all)", "n ≥ 1e-6 (all)",
                 "n ≥ 1e-8 (all)", "max (restricted)", "n ≥ 1e-6 (restr.)", "n ≥ 1e-8 (restr.)",
                 "n excluded", "discrete mismatches", "constraint 93 rcm (B2)"], rows))

    # 5 — decomposition
    print("\n## T5 — R = ρ × ε, per configuration, pooled over the seeds where both members are accepted optima\n")
    rows = []
    for name, cfg in out["configurations"].items():
        for label, d in cfg["decomposition"].items():
            if not d.get("seeds_used"):
                rows.append([name, label] + ["—"] * 10)
                continue
            p, md, rg = d["pooled"], d["median"], d["range"]
            rows.append([name, label, f"{d['numerator']} / {d['denominator']}",
                         f"{len(d['seeds_used'])}/{d['n_seeds_offered']}",
                         f"{p['R']:.4f}", f"{p['rho']:.4f}", f"{p['eps']:.4f}",
                         f"{md['R']:.4f} [{rg['R'][0]:.4f}, {rg['R'][1]:.4f}]",
                         f"{md['rho']:.4f} [{rg['rho'][0]:.4f}, {rg['rho'][1]:.4f}]",
                         f"{md['eps']:.4f} [{rg['eps'][0]:.4f}, {rg['eps'][1]:.4f}]",
                         f"{p['N_num']} / {p['N_den']}", f"{p['C_num']} / {p['C_den']}"])
    print(table(["configuration", "pair", "numerator / denominator", "seeds used", "R pooled",
                 "ρ pooled", "ε pooled", "R median [min, max]", "ρ median [min, max]",
                 "ε median [min, max]", "N num / den", "C num / den"], rows))

    # 6 — timing context
    print("\n## T6 — wall clock (context, never evidence): one run each, another task on the machine\n")
    rows = []
    for name, cfg in out["configurations"].items():
        for m in MEMBERS:
            ws = [q[m].get("wall_s") for q in cfg["per_seed"].values() if q[m].get("wall_s")]
            rows.append([name, m, len(ws), f(sum(ws), "{:.0f}"), f(min(ws), "{:.0f}") if ws else "—",
                         f(max(ws), "{:.0f}") if ws else "—"])
    print(table(["configuration", "run", "n", "Σ wall s", "min", "max"], rows))


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--lift", action="store_true")
    p.add_argument("--run", action="store_true")
    p.add_argument("--summarise", action="store_true")
    p.add_argument("--configuration", action="append", default=[])
    p.add_argument("--variant", action="append", default=[],
                   help="restrict --run to these variant labels (B0_rbw, B2_rbw, B0_full)")
    p.add_argument("--seeds-only", action="store_true", help="print the seed sets and stop")
    a = p.parse_args()
    RUNS.mkdir(parents=True, exist_ok=True)
    if a.seeds_only:
        for name in CONFIGURATIONS:
            seeds, conv = seed_set(name)
            print(name, "seeds", seeds, "of every-arm-converged", conv)
        return 0
    rc = 0
    if a.lift:
        rc = stage_lift() or rc
    if a.run:
        stage_run(a.configuration, a.variant)
    if a.summarise:
        out = summarise()
        print_tables(out)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
