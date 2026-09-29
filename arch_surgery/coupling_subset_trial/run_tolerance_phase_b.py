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

The st trajectory ladder (``--ladder``; task A96, st-trajectory-ladder)
-----------------------------------------------------------------------
A93 found that on ``st_regression`` alone the census set at 1e-8 moves the
optimiser's path in both arms and lengthens the partitioned arm's on every
seed (one of five failing at the iteration cap), where on the two pulsed
configurations nothing moves.  The hypothesis (A93 §9): st is the one
configuration where the census-set loop leaves a nonzero objective residual
at 1e-8 (A89's ladder, ``tolerance.json``: 4.9e-11 relative at 1e-8 and
1e-9, 0.0 from 1e-10; the whole-``y`` test reads 0.0 at every τ), and st's
optimiser is fragile enough that this changes finite-difference gradients.
``--ladder`` adds, on ``st_regression`` only and the same five seeds::

    B2 full  1e-8      the partitioned arm, whole-y test   (tolerance alone, partitioned)
    B2 rbw   1e-9, 1e-10, 1e-12   the census arm as the loops approach exact fixed points
    B0 rbw   1e-10     the flat census control at the τ where A89 reads 0.0

Each is one variant label ``<arm>_<set>_<tau>`` (``B2_rbw_1e-10``).  Records
under ``arch_surgery/idf_probe/runs/st_trajectory_ladder/`` (untracked); A93's
own three variants and their records are untouched.  ``--summarise --ladder``
compares every run, per seed, against **three** references — the campaign's
record (whole-``y`` 1e-6), A93's record of the same arm at 1e-8 (the census
run; A93's ``B0_full`` is carried as a fourth member) and the rest of the
ladder — and prints A89's objective / constraint error at each τ beside the
path result.  ``--lift`` is not a ladder stage: st is steady state and no
arm reads a lifted input file (V4's ``input_files.assert_lifted``).
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

# --- the st trajectory ladder (--ladder) ------------------------------------
LADDER_RUNS = TREE / "arch_surgery" / "idf_probe" / "runs" / "st_trajectory_ladder"
LADDER_CONFIGURATION = "st_regression"
#: (optimisation arm, test set, τ) -> label ``<arm>_<set>_<τ>``.  Order is the order of the tables.
LADDER_VARIANTS = (("B2", "full", 1e-8), ("B2", "rbw", 1e-9), ("B2", "rbw", 1e-10),
                   ("B2", "rbw", 1e-12), ("B0", "rbw", 1e-10))
#: The τ column of the ladder's tables: the campaign's, A93's, and the three new rungs.
LADDER_TAUS = (1e-6, 1e-8, 1e-9, 1e-10, 1e-12)
#: A93's records, relocated at its retirement.  Read only.
A93_RECORDS = Path(
    "/home/wrutten/projects/PROCESS_surgery/arch_surgery/idf_probe/runs/A93_runs/"
    "tolerance_phase_b"
)
#: A93's members carried into the ladder, with their arm, test set and τ.
A93_MEMBERS = {"B0_full": ("B0", "full", 1e-8), "B0_rbw": ("B0", "rbw", 1e-8),
               "B2_rbw": ("B2", "rbw", 1e-8)}
#: The A93 record every ladder run of the arm is compared with: the census run at 1e-8.
A93_REFERENCE_FOR = {"B0": "B0_rbw", "B2": "B2_rbw"}
#: A89's ladder rows read beside the path result: the census arm of the loop shape
#: (``rbw``) or the whole-y control (``full``).
A89_VARIANT_FOR = {("B0", "rbw"): "A0_rbw", ("B2", "rbw"): "A2_rbw",
                   ("B0", "full"): "A0_full", ("B2", "full"): "A0_full"}


def chosen_tau() -> float:
    return float(json.loads(TOLERANCE_FILE.read_text())["chosen_tau"])


def campaign(tau, runs=RUNS):
    base = config_mod.default_campaign()
    return dataclasses.replace(base, runs_dir=runs, derived_input_dir=runs / "input_files",
                               tau=tau, workers=WORKERS)


def variant_label(arm, test_set):
    return f"{arm}_{test_set}"


def run_dir(config_name, arm, test_set, seed):
    return RUNS / config_name / variant_label(arm, test_set) / f"seed{seed:03d}"


def ladder_label(arm, test_set, tau):
    return f"{arm}_{test_set}_{tau:.0e}"


def ladder_run_dir(label, seed):
    return LADDER_RUNS / LADDER_CONFIGURATION / label / f"seed{seed:03d}"


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
    env["NUMBA_CACHE_DIR"] = str(Path(camp.runs_dir) / "numba_cache")  # I-31: the pool sets none
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
    # I-31: V4's pool composes no NUMBA_CACHE_DIR; the derivation's child inherits this one.
    os.environ["NUMBA_CACHE_DIR"] = str(RUNS / "numba_cache")
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


def stage_run_ladder(variants):
    """The ladder's optimisations on st_regression: one campaign per τ, serial."""
    seeds, _ = seed_set(LADDER_CONFIGURATION)
    print(f"{LADDER_CONFIGURATION}: seeds {seeds}", flush=True)
    for arm, test_set, tau in LADDER_VARIANTS:
        label = ladder_label(arm, test_set, tau)
        if variants and label not in variants:
            continue
        camp = campaign(tau, runs=LADDER_RUNS)
        c = next(c for c in camp.configurations if c.name == LADDER_CONFIGURATION)
        assert camp.tau == tau
        for seed in seeds:
            j = job(c, camp, arm, seed, ladder_run_dir(label, seed))
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
    for tau in dict.fromkeys(taus):
        out[f"n_above_{tau:.0e}"] = sum(1 for v in sc.values() if v >= tau)
        out[f"n_above_{tau:.0e}_restricted"] = sum(1 for k, v in sc.items() if k not in ex and v >= tau)
    # every restricted component that is not at the exact fixed point (>= 1e-12), largest first
    out["restricted_components_above_1e-12"] = sorted(
        ((k, v) for k, v in sc.items() if k not in ex and v >= RESIDUAL_LISTING_FLOOR),
        key=lambda kv: -kv[1])
    return out


#: Below this a restricted exit-residual component is treated as at the fixed point
#: for the listing of T7 (the audit's own tau is 1e-8; the listing looks four decades under it).
RESIDUAL_LISTING_FLOOR = 1e-12


def set_memberships(config_name):
    """Where a component of y stands in the sets this task compares.

    census: the union of the census sets of the arm's census arm (A0's FLAT for
    B0, A2's blocks for B2); dsm: the DSM interface / feedback flags of
    ``test_sets.json``; writer: the block of V4's committed write set that
    writes it (the partitioned arm's schedule).
    """
    rbw = json.loads(RBW_SETS_FILE.read_text())["configurations"][config_name]
    ts = json.loads((HERE / "test_sets.json").read_text())["configurations"][config_name]["components"]
    ws = json.loads((V4_DIR / "harness" / "data" / f"write_sets_{config_name}.json").read_text())["subsets"]
    writer = {}
    for block, keys in ws.items():
        for k in keys:
            writer.setdefault(k, []).append(block)
    census = {arm: set().union(*(set(v) for v in rbw[arm]["sets"].values())) for arm in rbw}

    def describe(key, census_arm):
        c = ts.get(key) or {}
        return {"in_census": key in census[census_arm],
                "dsm_interface": c.get("interface"), "dsm_feedback": c.get("feedback"),
                "dsm_writers": c.get("writers"), "dsm_readers": c.get("readers"),
                "written_by_block": writer.get(key)}
    return describe


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
        describe = set_memberships(name)
        cfg = {"seeds": seeds, "every_arm_converged": converged,
               "n_by_block": {arm: rbw[name][arm]["n_by_block"] for arm in ("A0", "A2")},
               "per_seed": {}}
        for seed in seeds:
            q = {}
            for arm in ("B0", "B2"):
                rec = by_arm[arm][seed]
                q[f"{arm}_campaign"] = extract(rec, Path(rec["_dir"]))
            for arm in ("B0", "B2"):
                e = q[f"{arm}_campaign"]
                if e.get("audit"):
                    e["audit"]["memberships"] = {
                        k: describe(k, "A0" if arm == "B0" else "A2")
                        for k, _ in e["audit"]["restricted_components_above_1e-12"]}
            for arm, ts in VARIANTS:
                d = run_dir(name, arm, ts, seed)
                rec = records_mod.read(d)
                e = extract(rec, d)
                if e.get("audit"):
                    e["audit"]["memberships"] = {
                        k: describe(k, "A0" if arm == "B0" else "A2")
                        for k, _ in e["audit"]["restricted_components_above_1e-12"]}
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


def decomposition(per_seed, seeds, pairs=None):
    """R = ρ × ε for B2/B0, pooled over the seed set and as per-seed medians.

    Two pairs: the campaign's (whole-y, τ = 1e-6) and this task's census pair
    (rbw, τ = 1e-8); a third, B0 full at 1e-8 against B0 campaign, isolates
    the tolerance.  Pooled: sums over the seeds where both members are
    accepted optima (V4's cost population).  R equals ρ × ε exactly on pooled
    sums; the per-seed medians need not multiply.  ``pairs`` (the ladder's)
    replaces the default set.
    """
    pairs = pairs or {
        "campaign_1e-6": ("B2_campaign", "B0_campaign"),
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
# the st trajectory ladder: summarising
# --------------------------------------------------------------------------


def paired(e, base):
    """The paired comparison of one extracted record against a reference's."""
    if e.get("status") != "ok" or base.get("status") != "ok":
        return {"objf_rel_diff": None, "objf_within_floor": None, "d_iterations_summed": None,
                "evaluations_ratio": None, "node_calls_ratio": None,
                "node_calls_per_evaluation_ratio": None, "path_equal": None}
    rd = rel_diff(e.get("norm_objf"), base.get("norm_objf"))
    same_C = e.get("n_evaluations") == base.get("n_evaluations")
    same_it = (e.get("iterations_per_attempt") or []) == (base.get("iterations_per_attempt") or [])
    return {
        "objf_rel_diff": rd,
        "objf_within_floor": (rd <= OBJF_FLOOR_REL) if rd is not None else None,
        "d_iterations_summed": (e["n_solver_iterations_summed"] - base["n_solver_iterations_summed"]
                                if e.get("n_solver_iterations_summed") is not None
                                and base.get("n_solver_iterations_summed") is not None else None),
        "evaluations_ratio": (e["n_evaluations"] / base["n_evaluations"]
                              if e.get("n_evaluations") and base.get("n_evaluations") else None),
        "node_calls_ratio": (e["node_calls_solve_phase"] / base["node_calls_solve_phase"]
                             if e.get("node_calls_solve_phase") and base.get("node_calls_solve_phase") else None),
        "node_calls_per_evaluation_ratio": (
            e["node_calls_per_evaluation"] / base["node_calls_per_evaluation"]
            if e.get("node_calls_per_evaluation") and base.get("node_calls_per_evaluation") else None),
        # the path: the same iterations per attempt and the same number of evaluations
        "path_equal": bool(same_C and same_it),
        "same_evaluations": bool(same_C),
        "same_iterations_per_attempt": bool(same_it),
    }


def ladder_members():
    """``{label: {arm, test_set, tau, source, dir_of(seed)}}`` in table order."""
    members = {}
    for arm in ("B0", "B2"):
        members[f"{arm}_campaign"] = {"arm": arm, "test_set": "full", "tau": V4_TAU,
                                      "source": "campaign"}
        for label, (a, ts, tau) in A93_MEMBERS.items():
            if a == arm:
                members[label] = {"arm": a, "test_set": ts, "tau": tau, "source": "A93"}
        for a, ts, tau in LADDER_VARIANTS:
            if a == arm:
                members[ladder_label(a, ts, tau)] = {"arm": a, "test_set": ts, "tau": tau,
                                                     "source": "ladder"}
    # a stable order by arm, then τ descending, the campaign first
    return members


def a89_ladder():
    """A89's ladder rows on st (``tolerance.json``) at the ladder's τ values."""
    t = json.loads(TOLERANCE_FILE.read_text())
    out = {"rule": t["rule"], "epsfcn": t["epsfcn"], "threshold": t["threshold"],
           "chosen_tau": t["chosen_tau"], "rows": {}}
    for tau in LADDER_TAUS:
        key = f"{tau:.0e}"
        out["rows"][key] = {}
        for v in ("A0_rbw", "A2_rbw", "A0_full"):
            r = t["variants"][f"{LADDER_CONFIGURATION}/{v}"]["rows"].get(key)
            out["rows"][key][v] = None if r is None else {
                k: r.get(k) for k in ("objf_rel_err", "conf_abs_err", "grad_objf_rel_err",
                                      "grad_conf_rel_err", "meets_h3", "sweeps_mean")}
    return out


def summarise_ladder():
    name = LADDER_CONFIGURATION
    by_arm = campaign_records(name)
    seeds, converged = seed_set(name, by_arm)
    describe = set_memberships(name)
    rbw = json.loads(RBW_SETS_FILE.read_text())["configurations"][name]
    members = ladder_members()
    v4_tree = str((V4_DIR / "PROCESS").resolve())
    out = {"generated_by": "arch_surgery/coupling_subset_trial/run_tolerance_phase_b.py --summarise --ladder",
           "configuration": name, "v4_tau": V4_TAU, "a93_tau": chosen_tau(),
           "campaign_records": str(CAMPAIGN_RECORDS), "a93_records": str(A93_RECORDS),
           "ladder_records": str(LADDER_RUNS), "tree_expected": v4_tree,
           "members": {k: {kk: vv for kk, vv in m.items()} for k, m in members.items()},
           "ladder_taus": list(LADDER_TAUS), "a89": a89_ladder(),
           "seeds": seeds, "every_arm_converged": converged,
           "n_by_block": {arm: rbw[arm]["n_by_block"] for arm in ("A0", "A2")},
           "per_seed": {}}
    for seed in seeds:
        q = {}
        for label, m in members.items():
            arm = m["arm"]
            if m["source"] == "campaign":
                rec = by_arm[arm][seed]
                d = Path(rec["_dir"])
            elif m["source"] == "A93":
                d = A93_RECORDS / name / label / f"seed{seed:03d}"
                rec = records_mod.read(d)
            else:
                d = ladder_run_dir(label, seed)
                rec = records_mod.read(d)
            e = extract(rec, d)
            e["member"] = {"arm": arm, "test_set": m["test_set"], "tau": m["tau"],
                           "source": m["source"]}
            e["process_file"] = rec.get("process_file")
            e["process_file_under_this_tree"] = (
                bool(rec.get("process_file")) and str(rec["process_file"]).startswith(v4_tree)
                if m["source"] == "ladder" else None)
            e["tree_dirty"] = rec.get("tree_git_dirty")
            if e.get("audit"):
                e["audit"] = audit_recount(d, taus=(1e-8, 1e-6, m["tau"]))
                e["audit"]["memberships"] = {
                    k: describe(k, "A0" if arm == "B0" else "A2")
                    for k, _ in e["audit"]["restricted_components_above_1e-12"]}
            if m["source"] != "campaign":
                n = Path(d) / "narrowing.json"
                e["narrowing"] = json.loads(n.read_text()) if n.exists() else None
                e["pairing"] = pairing(d, Path(by_arm[arm][seed]["_dir"]), seed)
                e["against_campaign"] = paired(e, q[f"{arm}_campaign"])
            q[label] = e
        for label, m in members.items():  # second pass: every reference is in by now
            if m["source"] == "campaign":
                continue
            ref = A93_REFERENCE_FOR[m["arm"]]
            q[label]["against_a93_reference"] = (
                {"reference": ref, **paired(q[label], q[ref])} if label != ref else None)
        out["per_seed"][str(seed)] = q
    # per variant: the counts the verdict is stated in
    per_variant = {}
    for label, m in members.items():
        if m["source"] == "campaign":
            continue
        rows = [out["per_seed"][str(s)][label] for s in seeds]
        ok = [r for r in rows if r.get("status") == "ok"]
        acc = [r for r in rows if r.get("accepted")]
        ag = [r["against_campaign"] for r in ok]
        a9 = [r["against_a93_reference"] for r in ok if r.get("against_a93_reference")]
        s1 = out["per_seed"]["1"][label] if 1 in seeds else {}
        a89 = out["a89"]["rows"].get(f"{m['tau']:.0e}", {}).get(A89_VARIANT_FOR[(m["arm"], m["test_set"])])
        per_variant[label] = {
            "arm": m["arm"], "test_set": m["test_set"], "tau": m["tau"], "source": m["source"],
            "n_seeds": len(rows), "n_ok": len(ok), "n_accepted": len(acc),
            "n_ifail_1": sum(1 for r in rows if r.get("ifail") == 1),
            "n_retried": sum(1 for r in rows if r.get("retried")),
            "n_path_equal_campaign": sum(1 for p in ag if p.get("path_equal")),
            "n_path_equal_a93_reference": (sum(1 for p in a9 if p.get("path_equal"))
                                           if a9 else None),
            "a93_reference": A93_REFERENCE_FOR[m["arm"]] if label != A93_REFERENCE_FOR[m["arm"]] else None,
            "n_objf_within_floor": sum(1 for p in ag if p.get("objf_within_floor")),
            "max_objf_rel_diff_accepted": max((r["against_campaign"]["objf_rel_diff"] for r in acc
                                               if r["against_campaign"].get("objf_rel_diff") is not None),
                                              default=None),
            "iterations_summed_by_seed": [r.get("n_solver_iterations_summed") for r in rows],
            "evaluations_by_seed": [r.get("n_evaluations") for r in rows],
            "ifail_by_seed": [r.get("ifail") for r in rows],
            "seed_1": {"status": s1.get("status"), "ifail": s1.get("ifail"),
                       "iterations_per_attempt": s1.get("iterations_per_attempt"),
                       "n_evaluations": s1.get("n_evaluations"),
                       "objf_rel_diff_vs_campaign": (s1.get("against_campaign") or {}).get("objf_rel_diff")},
            "a89_variant": A89_VARIANT_FOR[(m["arm"], m["test_set"])],
            "a89_row": a89,
        }
    out["per_variant"] = per_variant
    pairs = {"campaign_1e-6": ("B2_campaign", "B0_campaign"),
             "census_1e-8 (A93)": ("B2_rbw", "B0_rbw"),
             "whole-y_1e-8": ("B2_full_1e-08", "B0_full"),
             "census_1e-10": ("B2_rbw_1e-10", "B0_rbw_1e-10")}
    for label, m in members.items():
        if m["source"] == "ladder":
            pairs[f"{label}_vs_{m['arm']}_campaign"] = (label, f"{m['arm']}_campaign")
            pairs[f"{label}_vs_{A93_REFERENCE_FOR[m['arm']]}_1e-08"] = (label, A93_REFERENCE_FOR[m["arm"]])
    out["decomposition"] = decomposition(out["per_seed"], seeds, pairs)
    LADDER_RUNS.mkdir(parents=True, exist_ok=True)
    (LADDER_RUNS / "summary.json").write_text(json.dumps(out, indent=1))
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
                rows.append([name, s, m, e.get("status"), f(e.get("ifail")), f(e.get("n_attempts")),
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
                rows.append([name, s, m, f(e.get("ifail")), f(e.get("n_attempts")),
                             "/".join(map(str, e.get("iterations_per_attempt") or [])) or "—",
                             f(e.get("n_solver_iterations_summed")), f(e.get("n_evaluations")),
                             f(e.get("node_calls_solve_phase")),
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

    # 7 — what the loops leave unconverged at exit, by name
    print(f"\n## T7 — restricted exit-residual components at or above {RESIDUAL_LISTING_FLOOR:.0e}, "
          "by name, per run (runs with none are omitted)\n")
    rows = []
    for name, cfg in out["configurations"].items():
        for s, q in cfg["per_seed"].items():
            for m in MEMBERS:
                a = q[m].get("audit") or {}
                comps = a.get("restricted_components_above_1e-12") or []
                if not comps:
                    continue
                mem = a.get("memberships") or {}
                shown = comps[:4]
                rows.append([name, s, m, len(comps),
                             "; ".join(f"`{k}` {v:.1e}" for k, v in shown)
                             + (" …" if len(comps) > 4 else ""),
                             "; ".join(
                                 f"{'census' if mem[k]['in_census'] else 'not census'}, "
                                 f"{'feedback' if mem[k]['dsm_feedback'] else ('interface' if mem[k]['dsm_interface'] else 'no DSM set')}, "
                                 f"by {'/'.join(mem[k]['written_by_block'] or ['?'])}, "
                                 f"read by {','.join(mem[k]['dsm_readers'] or ['—'])}"
                                 for k, _ in shown)])
    print(table(["configuration", "seed", "run", "n ≥ floor", "largest four (name, scaled residual)",
                 "membership of each (census set; DSM set; writing block; DSM readers)"], rows))

    # 6 — timing context
    print("\n## T6 — wall clock (context, never evidence): one run each, another task on the machine\n")
    rows = []
    for name, cfg in out["configurations"].items():
        for m in MEMBERS:
            ws = [q[m].get("wall_s") for q in cfg["per_seed"].values() if q[m].get("wall_s")]
            rows.append([name, m, len(ws), f(sum(ws), "{:.0f}"), f(min(ws), "{:.0f}") if ws else "—",
                         f(max(ws), "{:.0f}") if ws else "—"])
    print(table(["configuration", "run", "n", "Σ wall s", "min", "max"], rows))


def member_name(label, m):
    src = {"campaign": " (campaign)", "A93": " (A93)", "ladder": ""}[m["source"]]
    ts = "whole-y" if m["test_set"] == "full" else "census"
    return f"{m['arm']} {ts} {m['tau']:.0e}{src}"


def print_ladder_tables(out):
    lines = []
    pr = lines.append
    members = out["members"]
    seeds = out["seeds"]
    pr(f"\n# The st trajectory ladder — tables ({out['configuration']}; campaign τ = {out['v4_tau']:.0e}; "
       f"A93's τ = {out['a93_tau']:.0e})\n")
    pr("Members: " + "; ".join(f"`{k}` = {member_name(k, m)}" for k, m in members.items()) + "\n")

    # L0 — the matrix
    pr("## L0 — members, sources and the census test-set widths\n")
    rows = [[k, m["arm"], m["test_set"], f"{m['tau']:.0e}", m["source"],
             ", ".join(map(str, seeds)),
             (str(out["n_by_block"]["A0"].get("FLAT")) if m["arm"] == "B0" else
              ", ".join(f"{b} {n}" for b, n in out["n_by_block"]["A2"].items()))
             if m["test_set"] == "rbw" else "whole y"]
            for k, m in members.items()]
    pr(table(["member", "arm", "test set", "τ", "source", "seeds", "test-set width"], rows))

    # L1 — A89's ladder beside the path result
    pr("\n## L1 — A89's evaluation-phase ladder on st (`tolerance.json`) beside the path result at each τ\n")
    rows = []
    for tau in out["ladder_taus"]:
        key = f"{tau:.0e}"
        a = out["a89"]["rows"][key]
        def cell(v, k, fmt="{:.1e}"):
            r = a.get(v) or {}
            return f(r.get(k), fmt)
        # the path result: n of 5 seeds whose path equals the campaign's, per arm, at this τ
        def path_cell(arm, ts):
            hits = [k for k, m in members.items()
                    if m["arm"] == arm and m["test_set"] == ts and m["tau"] == tau
                    and m["source"] != "campaign"]
            if not hits:
                return "—" if tau != out["v4_tau"] else "(reference)"
            pv = out["per_variant"][hits[0]]
            return f"{pv['n_path_equal_campaign']}/{pv['n_ok']} (`{hits[0]}`)"
        rows.append([key,
                     cell("A0_rbw", "objf_rel_err"), cell("A0_rbw", "conf_abs_err"), cell("A0_rbw", "grad_objf_rel_err"),
                     cell("A2_rbw", "objf_rel_err"), cell("A2_rbw", "conf_abs_err"), cell("A2_rbw", "grad_objf_rel_err"),
                     cell("A0_full", "objf_rel_err"), cell("A0_full", "conf_abs_err"),
                     path_cell("B0", "rbw"), path_cell("B2", "rbw"), path_cell("B0", "full"), path_cell("B2", "full")])
    pr(table(["τ", "A0 census objf rel err", "A0 census conf abs err", "A0 census grad objf rel err",
              "A2 census objf rel err", "A2 census conf abs err", "A2 census grad objf rel err",
              "A0 whole-y objf rel err", "A0 whole-y conf abs err",
              "B0 census: path = campaign", "B2 census: path = campaign",
              "B0 whole-y: path = campaign", "B2 whole-y: path = campaign"], rows))

    # L2 — pairing and outcome, the ladder's runs
    pr("\n## L2 — entry pairing, tree and outcome, per ladder run\n")
    rows = []
    for s, q in out["per_seed"].items():
        for k, m in members.items():
            if m["source"] != "ladder":
                continue
            e = q[k]
            p = e.get("pairing") or {}
            rows.append([s, k, e.get("status"), f(e.get("ifail")), f(e.get("n_attempts")),
                         "/".join(map(str, e.get("ifail_per_attempt") or [])) or "—",
                         f"{p.get('n_identical')}/{p.get('n_variables')}" if p.get("n_variables") else
                         ("n/a (seed 0)" if s == "0" else "—"),
                         f(p.get("identical")), (e.get("tree_git_head") or "")[:8],
                         f(e.get("tree_dirty")), f(e.get("process_file_under_this_tree")),
                         f(((e.get("narrowing") or {}).get("test_set"))),
                         f(e.get("tau"), "{:.0e}"), f(e.get("wall_s"), "{:.0f}")])
    pr(table(["seed", "run", "status", "ifail", "attempts", "ifail per attempt",
              "displaced x identical (hex)", "paired", "tree", "tree dirty",
              "process under this tree", "test set installed", "τ of record", "wall s (context)"], rows))

    # L3 — path and optimum, per seed, every member
    pr("\n## L3 — the optimiser's path and its optimum, per seed, against the campaign's record and A93's census record of the arm at 1e-8\n")
    rows = []
    for s, q in out["per_seed"].items():
        for k, m in members.items():
            e = q[k]
            ag = e.get("against_campaign") or {}
            a9 = e.get("against_a93_reference") or {}
            rows.append([s, k, f(e.get("ifail")), f(e.get("n_attempts")),
                         "/".join(map(str, e.get("iterations_per_attempt") or [])) or "—",
                         f(e.get("n_solver_iterations_summed")), f(e.get("n_evaluations")),
                         f(e.get("node_calls_solve_phase")),
                         f(e.get("node_calls_per_evaluation"), "{:.1f}"),
                         f(e.get("sweeps_per_eval_mean"), "{:.2f}"),
                         f(e.get("norm_objf"), "{:.12g}"),
                         f(ag.get("objf_rel_diff"), "{:.1e}") if ag else "—",
                         f(ag.get("d_iterations_summed")) if ag else "—",
                         f(ag.get("evaluations_ratio"), "{:.4f}") if ag else "—",
                         f(ag.get("path_equal")) if ag else "—",
                         f(a9.get("objf_rel_diff"), "{:.1e}") if a9 else "—",
                         f(a9.get("d_iterations_summed")) if a9 else "—",
                         f(a9.get("evaluations_ratio"), "{:.4f}") if a9 else "—",
                         f(a9.get("path_equal")) if a9 else "—"])
    pr(table(["seed", "run", "ifail", "attempts", "iterations per attempt", "iterations Σ",
              "evaluations C", "node calls N", "N/C", "sweeps/eval mean", "norm_objf",
              "|Δf|/max vs campaign", "Δ iterations Σ vs campaign", "C ratio vs campaign",
              "path = campaign", "|Δf|/max vs A93 1e-8", "Δ iterations Σ vs A93 1e-8",
              "C ratio vs A93 1e-8", "path = A93 1e-8"], rows))

    # L4 — per variant, the counts
    pr("\n## L4 — per variant: the counts the verdict is stated in (5 seeds each)\n")
    rows = []
    for k, pv in out["per_variant"].items():
        a89 = pv.get("a89_row") or {}
        s1 = pv["seed_1"]
        rows.append([k, member_name(k, members[k]), f"{pv['n_ok']}/{pv['n_seeds']}",
                     f"{pv['n_ifail_1']}/{pv['n_seeds']}", f"{pv['n_accepted']}/{pv['n_seeds']}",
                     pv["n_retried"],
                     f"{pv['n_path_equal_campaign']}/{pv['n_ok']}",
                     ("(is the reference)" if pv.get("a93_reference") is None else
                      f"{pv.get('n_path_equal_a93_reference') or 0}/{pv['n_ok']} (`{pv['a93_reference']}`)"),
                     " ".join(map(str, pv["iterations_summed_by_seed"])),
                     " ".join(map(str, pv["evaluations_by_seed"])),
                     f"{pv['n_objf_within_floor']}/{pv['n_ok']}",
                     f(pv["max_objf_rel_diff_accepted"], "{:.1e}"),
                     f"ifail {f(s1.get('ifail'))}, it {'/'.join(map(str, s1.get('iterations_per_attempt') or []))}, "
                     f"C {f(s1.get('n_evaluations'))}",
                     pv["a89_variant"], f(a89.get("objf_rel_err"), "{:.1e}"),
                     f(a89.get("conf_abs_err"), "{:.1e}"), f(a89.get("grad_objf_rel_err"), "{:.1e}")])
    pr(table(["run", "member", "status ok", "ifail = 1", "accepted optimum", "retried",
              "path = campaign", "path = A93 census 1e-8", "iterations Σ by seed",
              "evaluations by seed", "|Δf| ≤ 1e-6 vs campaign", "max |Δf|/max (accepted)",
              "seed 1", "A89 variant", "A89 objf rel err", "A89 conf abs err", "A89 grad objf rel err"],
             rows))

    # L5 — sweeps
    pr("\n## L5 — sweeps per evaluation and per block, per seed\n")
    rows = []
    for s, q in out["per_seed"].items():
        for k in members:
            e = q[k]
            if e.get("status") != "ok":
                rows.append([s, k, e.get("status")] + ["—"] * 6)
                continue
            rows.append([s, k, e.get("n_evaluations"),
                         f"{e['sweeps_per_eval_min']}/{e['sweeps_per_eval_median']}/"
                         f"{e['sweeps_per_eval_mean']:.2f}/{e['sweeps_per_eval_max']}",
                         " ".join(f"{a}:{b}" for a, b in e["sweeps_per_eval_hist"].items()),
                         ", ".join(f"{b} {v:.2f}" for b, v in e["sweeps_per_solve_by_block"].items()),
                         e.get("predicate_evaluations"), e.get("components_compared"),
                         f(e["components_compared"] / e["predicate_evaluations"], "{:.0f}")
                         if e.get("predicate_evaluations") else "—"])
    pr(table(["seed", "run", "evaluations", "sweeps/eval min/median/mean/max",
              "histogram sweeps:count", "sweeps per solve by block", "predicate evaluations",
              "components compared", "mean test width"], rows))

    # L6 — exit audit at the run's own τ
    pr("\n## L6 — exit audit (whole y, frozen ruler, at the entry to the output path), recounted at 1e-6, 1e-8 and the run's own τ\n")
    rows = []
    for s, q in out["per_seed"].items():
        for k, m in members.items():
            e = q[k]
            a = e.get("audit") or {}
            key = f"{m['tau']:.0e}"
            rows.append([s, k, key, f(a.get("max"), "{:.1e}"), a.get("n_above_1e-06"),
                         a.get("n_above_1e-08"), a.get(f"n_above_{key}"),
                         f(a.get("max_restricted"), "{:.1e}"), a.get("n_above_1e-06_restricted"),
                         a.get("n_above_1e-08_restricted"), a.get(f"n_above_{key}_restricted"),
                         a.get("n_excluded"), a.get("n_discrete_mismatch"),
                         len(a.get("restricted_components_above_1e-12") or [])])
    pr(table(["seed", "run", "τ of run", "max (all)", "n ≥ 1e-6 (all)", "n ≥ 1e-8 (all)",
              "n ≥ τ of run (all)", "max (restricted)", "n ≥ 1e-6 (restr.)", "n ≥ 1e-8 (restr.)",
              "n ≥ τ of run (restr.)", "n excluded", "discrete mismatches", "n restr. ≥ 1e-12"], rows))

    # L7 — what the loops leave unconverged at exit, by name
    pr(f"\n## L7 — restricted exit-residual components at or above {RESIDUAL_LISTING_FLOOR:.0e}, "
       "by name, per run (runs with none are omitted)\n")
    rows = []
    for s, q in out["per_seed"].items():
        for k in members:
            a = q[k].get("audit") or {}
            comps = a.get("restricted_components_above_1e-12") or []
            if not comps:
                continue
            mem = a.get("memberships") or {}
            shown = comps[:4]
            rows.append([s, k, len(comps),
                         "; ".join(f"`{n}` {v:.1e}" for n, v in shown) + (" …" if len(comps) > 4 else ""),
                         "; ".join(
                             f"{'census' if mem[n]['in_census'] else 'not census'}, "
                             f"{'feedback' if mem[n]['dsm_feedback'] else ('interface' if mem[n]['dsm_interface'] else 'no DSM set')}, "
                             f"by {'/'.join(mem[n]['written_by_block'] or ['?'])}, "
                             f"read by {','.join(mem[n]['dsm_readers'] or ['—'])}"
                             for n, _ in shown)])
    pr(table(["seed", "run", "n ≥ floor", "largest four (name, scaled residual)",
              "membership of each (census set; DSM set; writing block; DSM readers)"], rows))

    # L8 — decomposition
    pr("\n## L8 — R = ρ × ε, pooled over the seeds where both members are accepted optima\n")
    rows = []
    for label, d in out["decomposition"].items():
        if not d.get("seeds_used"):
            rows.append([label] + ["—"] * 10)
            continue
        p, md, rg = d["pooled"], d["median"], d["range"]
        rows.append([label, f"{d['numerator']} / {d['denominator']}",
                     f"{len(d['seeds_used'])}/{d['n_seeds_offered']}",
                     f"{p['R']:.4f}", f"{p['rho']:.4f}", f"{p['eps']:.4f}",
                     f"{md['R']:.4f} [{rg['R'][0]:.4f}, {rg['R'][1]:.4f}]",
                     f"{md['rho']:.4f} [{rg['rho'][0]:.4f}, {rg['rho'][1]:.4f}]",
                     f"{md['eps']:.4f} [{rg['eps'][0]:.4f}, {rg['eps'][1]:.4f}]",
                     f"{p['N_num']} / {p['N_den']}", f"{p['C_num']} / {p['C_den']}"])
    pr(table(["pair", "numerator / denominator", "seeds used", "R pooled", "ρ pooled", "ε pooled",
              "R median [min, max]", "ρ median [min, max]", "ε median [min, max]",
              "N num / den", "C num / den"], rows))

    # L9 — timing context
    pr("\n## L9 — wall clock (context, never evidence): one run each, another task on the machine\n")
    rows = []
    for k in members:
        ws = [q[k].get("wall_s") for q in out["per_seed"].values() if q[k].get("wall_s")]
        rows.append([k, len(ws), f(sum(ws), "{:.0f}"), f(min(ws), "{:.0f}") if ws else "—",
                     f(max(ws), "{:.0f}") if ws else "—"])
    pr(table(["run", "n", "Σ wall s", "min", "max"], rows))

    text = "\n".join(lines)
    print(text)
    (LADDER_RUNS / "tables.md").write_text(text + "\n")


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--lift", action="store_true")
    p.add_argument("--run", action="store_true")
    p.add_argument("--summarise", action="store_true")
    p.add_argument("--ladder", action="store_true",
                   help="the st trajectory ladder: --run runs LADDER_VARIANTS on st_regression into "
                        "runs/st_trajectory_ladder; --summarise compares them with the campaign's and "
                        "A93's records")
    p.add_argument("--configuration", action="append", default=[])
    p.add_argument("--variant", action="append", default=[],
                   help="restrict --run to these variant labels (B0_rbw, B2_rbw, B0_full; with "
                        "--ladder: B2_full_1e-08, B2_rbw_1e-09, B2_rbw_1e-10, B2_rbw_1e-12, B0_rbw_1e-10)")
    p.add_argument("--seeds-only", action="store_true", help="print the seed sets and stop")
    a = p.parse_args()
    if a.ladder:
        if a.lift:
            raise SystemExit("--lift is not a ladder stage: st_regression is steady state and no "
                             "arm reads a lifted input file (V4's input_files.assert_lifted)")
        if a.configuration and a.configuration != [LADDER_CONFIGURATION]:
            raise SystemExit(f"the ladder runs on {LADDER_CONFIGURATION} only")
        known = [ladder_label(*v) for v in LADDER_VARIANTS]
        unknown = [v for v in a.variant if v not in known]
        if unknown:
            raise SystemExit(f"unknown ladder variant(s) {unknown}; known: {known}")
        LADDER_RUNS.mkdir(parents=True, exist_ok=True)
        if a.run:
            stage_run_ladder(a.variant)
        if a.summarise:
            print_ladder_tables(summarise_ladder())
        return 0
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
