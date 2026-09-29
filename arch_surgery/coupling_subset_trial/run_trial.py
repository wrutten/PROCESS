#!/usr/bin/env python
"""Stop V4's evaluation-phase loops on narrowed test sets, at a measured tolerance.

Task A89 (coupling-subset-trial).  First pass (2026-09-29, ``9d80c84b``): the
DSM's ``interface`` and ``feedback`` sets at V4's τ = 1e-6.  **Second pass**
(this file), the user, 2026-09-29: *"Rerun the scratch experiment … Build a
proof-of-principle for the read-before-write census to determine the feedback
set to converge (ie. implement the structural fix).  Change the tolerance to a
principled value.  Measure beforehand what that would be.  Compare wall clock
time."* — and: *"the feedforward/post-processing models should be run once in
all A arms."*

Arms (the evaluation phase; V4's own job composition, overrides named):

``A0v4``  V4's ``A0`` exactly: flat, every node in every sweep, full test.
``A0``    flat, the per-call feed-forward deferral and the per-run deferral on
          (``PROCESS_ARCH_DEFER_PER_CALL=feedforward``, the committed per-run
          artifact), the per-run set executed once after convergence.
``A2``    V4's ``A2`` (partitioned), the per-run set executed once after
          convergence.

Test sets: ``full`` (V4), ``interface`` / ``feedback`` (DSM, first pass),
``rbw`` (the read-before-write census of this arm's own execution order).

Stages, each reachable from this entry point::

    --references   V4's entry-reference job per configuration (A0v4, cold)
    --census       rbw census runs: A0 and A2, full test, displaced seeds 2-5
    --derive-rbw   census records -> rbw_sets.json (committed)
    --noise        the stencil at a ladder of τ, three arm/test-set variants
    --choose-tau   noise records -> tolerance.json (committed): the rule below
    --run          the trial at the chosen τ: displaced seed 1 and cold entry
    --timing       timed repetitions, serial, at the chosen τ
    --summarise    everything -> trial_summary.json and tables (no PROCESS run)

**The tolerance rule** (declared before the noise stage ran).  VMCON
differentiates by central differences with relative step ``h = epsfcn``
(1e-3, PROCESS's default; none of the three input files sets it).  The
truncation error of a central difference is O(h²); function noise ε adds
O(ε/h).  They balance at ε ≈ h³ (Gill, Murray & Wright, *Practical
Optimization*, §8.6: the optimal central step is h ≈ ε^{1/3}).  So the loop
tolerance is chosen as the **largest τ on the ladder at which the measured
MDA-induced error of the objective (relative) and of every constraint
(absolute, they are normalised) stays at or below h³ = 1e-9 at every stencil
point**, measured against the ladder's tightest τ, on the control (``A0``,
``rbw``), in every configuration.  One τ for all arms and configurations —
the largest value that satisfies the rule everywhere.

Records under ``arch_surgery/idf_probe/runs/coupling_subset_trial/rerun/``
(untracked).  Nothing is written to the V4 folder.
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
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parent.parent
V4_DIR = HERE.parent / "MDA_partitioning_experiment_v4"
RUNS = TREE / "arch_surgery" / "idf_probe" / "runs" / "coupling_subset_trial" / "rerun"
WRAPPER = HERE / "narrowed_evaluate.py"
INPROC = HERE / "inproc_child.py"
RBW_SETS_FILE = HERE / "rbw_sets.json"
TOLERANCE_FILE = HERE / "tolerance.json"

sys.path.insert(0, str(V4_DIR))
sys.dont_write_bytecode = True

from harness.core import config as config_mod  # noqa: E402
from harness.core import pool as pool_mod  # noqa: E402
from harness.core import records as records_mod  # noqa: E402
from harness.gates import reproduction as reproduction_mod  # noqa: E402

V4_TAU = 1e-6
ARMS = ("A0v4", "A0", "A2")
TEST_SETS = ("full", "interface", "feedback", "rbw")
ENTRIES = ("displaced", "cold")
SEED_TRIAL = 1
SEEDS_CENSUS = (2, 3, 4, 5)
TAU_LADDER = (1e-5, 1e-6, 1e-7, 1e-8, 1e-9, 1e-10, 1e-11, 1e-12)
NOISE_VARIANTS = (("A0", "rbw"), ("A0", "full"), ("A2", "rbw"))
H3_RULE = "h**3"
TIMING_VARIANTS = (("A0v4", "full"), ("A0", "full"), ("A0", "rbw"), ("A2", "full"), ("A2", "rbw"))
TIMING_REPS = 7


def campaign(tau=V4_TAU):
    base = config_mod.default_campaign()
    return dataclasses.replace(base, runs_dir=RUNS, derived_input_dir=RUNS / "input_files",
                               tau=tau)


def v4_arm(arm):
    return "A0" if arm == "A0v4" else arm


def overrides(arm, config):
    """This trial's environment on top of V4's composition for the arm."""
    if arm == "A0":
        return {"PROCESS_ARCH_DEFER_PER_CALL": "feedforward",
                "PROCESS_ARCH_DEFER_PER_RUN": str(config.per_run_artifact(lifted_input_file=False))}
    return {}


def job(config, camp, arm, entry, seed, reference, outdir):
    displaced = entry == "displaced"
    return pool_mod.Job(
        phase="A", arm=v4_arm(arm), config=config, seed=seed, outdir=outdir,
        regime="perturbed" if displaced else "unperturbed",
        delta=camp.delta if displaced else None,
        pin_hex=(reproduction_mod.entry_pin(config, v4_arm(arm), reference, seed=seed,
                                            delta=camp.delta if displaced else None)
                 if reference else None),
        entry_state=(Path(reference["snapshot"]) if displaced else None),
        run_kind="smoke", override_env=overrides(arm, config))


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


def run_evaluate(j, camp, arm, test_set, *, census=False, pass_log=True):
    outdir = Path(j.outdir)
    if (outdir / "metrics.json").exists():
        return
    env, terms = environment(j, camp)
    command = pool_mod._command(j, camp, terms)  # V4's own composition
    assert command[1].endswith("evaluate.py"), command[:2]
    own = ["--test-set", test_set] + (["--census"] if census else []) + (
        ["--pass-log"] if pass_log else [])
    command = [command[0], str(WRAPPER), *own, "--", *command[2:]]
    t0 = time.perf_counter()
    rc = launch(command, env, outdir, {"arm": arm, "test_set": test_set, "census": census,
                                       "tau": camp.tau}, j.timeout)
    if not (outdir / "metrics.json").exists():
        (outdir / "metrics.json").write_text(json.dumps({"status": "no_record", "returncode": rc}))
    rec = records_mod.read(outdir)
    print(f"  {j.config.name:22s} {arm:4s} {test_set:9s} {j.regime:11s} seed={j.seed} "
          f"rc={rc} status={rec.get('status')} {time.perf_counter() - t0:5.0f}s", flush=True)


def run_inproc(mode, config, camp, arm, test_set, entry_state, outdir, reference, seed=0,
               entry="cold"):
    if (outdir / "inproc.json").exists():
        return
    j = job(config, camp, arm, entry, seed, reference, outdir)
    env, _ = environment(j, camp)
    input_path, _ = pool_mod.assert_input_file_for(j, camp)
    command = [sys.executable, str(INPROC), "--mode", mode, "--tree", str(camp.tree),
               "--configuration", config.name, "--arm", arm, "--test-set", test_set,
               "--input", str(input_path), "--coupling-state", str(config.coupling_state_path),
               "--entry-state", str(entry_state), "--outdir", str(outdir),
               "--reps", str(TIMING_REPS)]
    t0 = time.perf_counter()
    rc = launch(command, env, outdir, {"mode": mode, "arm": arm, "test_set": test_set,
                                       "tau": camp.tau}, 3600)
    status = (json.loads((outdir / "inproc.json").read_text()).get("status")
              if (outdir / "inproc.json").exists() else "no_record")
    print(f"  {mode:6s} {config.name:22s} {arm:4s} {test_set:5s} tau={camp.tau:.0e} "
          f"rc={rc} status={status} {time.perf_counter() - t0:5.0f}s", flush=True)


def reference_of(config):
    d = RUNS / config.name / "reference"
    rec = records_mod.read(d)
    if rec.get("status") != "ok":
        raise SystemExit(f"reference for {config.name} did not finish")
    return {"snapshot": str(d / "y_exit.json"),
            "t_plant_pulse_burn_hex": rec.get("t_plant_pulse_burn_hex")}


def configs(camp, names):
    return [c for c in camp.configurations if not names or c.name in names]


# --------------------------------------------------------------------------
# stages
# --------------------------------------------------------------------------


def stage_references(names):
    camp = campaign()
    for c in configs(camp, names):
        j = pool_mod.Job(phase="A", arm="A0", config=c, seed=0,
                         outdir=RUNS / c.name / "reference", regime="unperturbed",
                         delta=None, run_kind="smoke")
        run_evaluate(j, camp, "A0v4", "full", pass_log=False)


def stage_census(names, workers):
    camp = campaign()
    jobs = []
    for c in configs(camp, names):
        ref = reference_of(c)
        for arm in ("A0", "A2"):
            for seed in SEEDS_CENSUS:
                jobs.append(job(c, camp, arm, "displaced", seed, ref,
                                RUNS / c.name / "census" / arm / f"seed{seed:03d}"))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(lambda j: run_evaluate(j, camp, "A0" if j.override_env else j.arm,
                                           "full", census=True, pass_log=False), jobs))


def stage_derive_rbw():
    """Union of the census records per configuration, arm and iterated block."""
    out = {"format": "rbw-sets-1",
           "generated_by": "arch_surgery/coupling_subset_trial/run_trial.py --derive-rbw",
           "rule": "a component of y that, in some observed sweep of the block, is read before "
                   "it is first written in that sweep and written later in it",
           "census_seeds": list(SEEDS_CENSUS), "census_test_set": "full", "census_tau": V4_TAU,
           "configurations": {}}
    ts = json.loads((HERE / "test_sets.json").read_text())["configurations"]
    camp = campaign()
    for c in camp.configurations:
        out["configurations"][c.name] = {}
        for arm in ("A0", "A2"):
            sets: dict = {}
            detail: dict = {}
            sweeps: dict = {}
            runs = []
            for seed in SEEDS_CENSUS:
                d = RUNS / c.name / "census" / arm / f"seed{seed:03d}"
                rec = records_mod.read(d)
                cen = json.loads((d / "rbw_census.json").read_text())
                runs.append({"seed": seed, "status": rec.get("status"),
                             "tree_git_head": rec.get("tree_git_head")})
                for label, n in cen["sweeps_observed_by_block"].items():
                    sweeps[label] = sweeps.get(label, 0) + n
                for label, keys in cen["rbw_by_block"].items():
                    if label == "?":  # the deferred tail's single run: not a loop
                        continue
                    for k, e in keys.items():
                        sets.setdefault(label, set()).add(k)
                        dd = detail.setdefault(label, {}).setdefault(
                            k, {"reader": e["reader"], "writer": e["writer"], "n_sweeps": 0,
                                "n_runs": 0})
                        dd["n_sweeps"] += e["n"]
                        dd["n_runs"] += 1
            comp = ts[c.name]["components"]
            union = set().union(*sets.values()) if sets else set()
            out["configurations"][c.name][arm] = {
                "census_runs": runs,
                "sweeps_observed_by_block": sweeps,
                "sets": {k: sorted(v) for k, v in sorted(sets.items())},
                "n_by_block": {k: len(v) for k, v in sorted(sets.items())},
                "against_dsm": {
                    "n_union": len(union),
                    "in_dsm_feedback": sum(comp[k]["feedback"] for k in union),
                    "in_dsm_interface_not_feedback": sum(
                        comp[k]["interface"] and not comp[k]["feedback"] for k in union),
                    "dsm_self_read_only": sorted(
                        k for k in union if not comp[k]["interface"] and comp[k]["self_read"]),
                    "in_no_dsm_set_not_self_read": sorted(
                        k for k in union if not comp[k]["interface"] and not comp[k]["self_read"]),
                    "dsm_feedback_not_rbw": sorted(
                        k for k in ts[c.name]["sets"]["feedback"] if k not in union),
                },
                "detail": detail,
            }
    RBW_SETS_FILE.write_text(json.dumps(out, indent=1) + "\n")
    for c, arms in out["configurations"].items():
        for arm, d in arms.items():
            print(c, arm, d["n_by_block"], "| vs DSM:",
                  {k: (len(v) if isinstance(v, list) else v) for k, v in d["against_dsm"].items()})


def stage_noise(names, workers):
    tasks = []
    for tau in TAU_LADDER:
        camp = campaign(tau)
        for c in configs(camp, names):
            ref = reference_of(c)
            for arm, ts in NOISE_VARIANTS:
                d = RUNS / c.name / "noise" / f"{arm}_{ts}" / f"tau{tau:.0e}"
                tasks.append((c, camp, arm, ts, ref, d))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(lambda t: run_inproc("noise", t[0], t[1], t[2], t[3], t[4]["snapshot"],
                                         t[5], t[4]), tasks))


def _noise_errors(points, ref_points):
    ef = ec = 0.0
    gf = gc = 0.0
    fx = lambda s: float.fromhex(s)  # noqa: E731
    for p, r in zip(points, ref_points):
        f, fr = fx(p["objf_hex"]), fx(r["objf_hex"])
        ef = max(ef, abs(f - fr) / max(abs(fr), 1e-300))
        c = [fx(v) for v in p["conf_hex"]]
        cr = [fx(v) for v in r["conf_hex"]]
        ec = max(ec, max((abs(a - b) for a, b in zip(c, cr)), default=0.0))
    # central differences, per variable: (value(x+) - value(x-)) / 2  (per unit relative step h)
    def diffs(pts):
        out = []
        for i in range((len(pts) - 1) // 2):
            fw, bw = pts[1 + 2 * i], pts[2 + 2 * i]
            out.append(((fx(fw["objf_hex"]) - fx(bw["objf_hex"])) / 2,
                        [(fx(a) - fx(b)) / 2 for a, b in zip(fw["conf_hex"], bw["conf_hex"])]))
        return out
    d, dr = diffs(points), diffs(ref_points)
    sf = max((abs(x[0]) for x in dr), default=0.0) or 1.0
    sc = max((max((abs(v) for v in x[1]), default=0.0) for x in dr), default=0.0) or 1.0
    for (a, ca), (b, cb) in zip(d, dr):
        gf = max(gf, abs(a - b) / sf)
        gc = max(gc, max((abs(u - v) for u, v in zip(ca, cb)), default=0.0) / sc)
    return ef, ec, gf, gc


def stage_choose_tau():
    camp = campaign()
    result = {"generated_by": "arch_surgery/coupling_subset_trial/run_trial.py --choose-tau",
              "rule": "largest tau on the ladder with max(objective relative error, constraint "
                      "absolute error) <= epsfcn**3 at every stencil point, against the "
                      "ladder's tightest tau, on the control (A0, rbw), every configuration",
              "ladder": list(TAU_LADDER), "variants": {}}
    passing = None
    h = None
    for c in camp.configurations:
        for arm, ts in NOISE_VARIANTS:
            key = f"{c.name}/{arm}_{ts}"
            rows = {}
            recs = {}
            for tau in TAU_LADDER:
                p = RUNS / c.name / "noise" / f"{arm}_{ts}" / f"tau{tau:.0e}" / "inproc.json"
                r = json.loads(p.read_text()) if p.exists() else {"status": "absent"}
                recs[tau] = r
            ok = [t for t in TAU_LADDER if recs[t].get("status") == "ok"]
            if not ok:
                result["variants"][key] = {"error": "no tau finished",
                                           "statuses": {f"{t:.0e}": recs[t].get("status") for t in TAU_LADDER}}
                continue
            tref = min(ok)
            h = recs[tref]["epsfcn"]
            for tau in TAU_LADDER:
                r = recs[tau]
                if r.get("status") != "ok":
                    rows[f"{tau:.0e}"] = {"status": r.get("status"),
                                          "error_tail": (r.get("traceback") or "").strip().splitlines()[-1:]}
                    continue
                ef, ec, gf, gc = _noise_errors(r["points"], recs[tref]["points"])
                sweeps = [pt["sweeps"] for pt in r["points"]]
                rows[f"{tau:.0e}"] = {
                    "status": "ok", "objf_rel_err": ef, "conf_abs_err": ec,
                    "grad_objf_rel_err": gf, "grad_conf_rel_err": gc,
                    "meets_h3": max(ef, ec) <= h ** 3,
                    "sweeps_mean": statistics.mean(sweeps), "sweeps_max": max(sweeps),
                    "node_calls_total": sum(pt["node_calls"] for pt in r["points"]),
                    "n_points": len(sweeps)}
            result["variants"][key] = {"reference_tau": tref, "epsfcn": h, "rows": rows}
            if (arm, ts) == ("A0", "rbw"):
                meets = {float(t) for t, row in rows.items() if row.get("meets_h3")}
                # the largest tau such that it and every tighter tau meet the rule
                ok_here = set()
                for t in sorted(TAU_LADDER):
                    if t in meets:
                        ok_here.add(t)
                    else:
                        break
                passing = ok_here if passing is None else passing & ok_here
    chosen = max(passing) if passing else None
    result["epsfcn"] = h
    result["threshold"] = None if h is None else h ** 3
    result["chosen_tau"] = chosen
    TOLERANCE_FILE.write_text(json.dumps(result, indent=1) + "\n")
    print(f"chosen tau = {chosen}")
    for key, v in result["variants"].items():
        print(key, "ref", v.get("reference_tau"))
        for t, row in (v.get("rows") or {}).items():
            if row.get("status") == "ok":
                print(f"   tau {t}: f {row['objf_rel_err']:.1e} c {row['conf_abs_err']:.1e} "
                      f"grad f {row['grad_objf_rel_err']:.1e} grad c {row['grad_conf_rel_err']:.1e} "
                      f"sweeps {row['sweeps_mean']:.1f}/{row['sweeps_max']} "
                      f"calls {row['node_calls_total']} h3 {row['meets_h3']}")
            else:
                print(f"   tau {t}: {row}")


def chosen_tau():
    return json.loads(TOLERANCE_FILE.read_text())["chosen_tau"]


def trial_matrix():
    for arm in ARMS:
        for ts in (("full",) if arm == "A0v4" else TEST_SETS):
            yield arm, ts


def stage_run(names, workers):
    camp = campaign(chosen_tau())
    jobs = []
    for c in configs(camp, names):
        ref = reference_of(c)
        for entry in ENTRIES:
            seed = SEED_TRIAL if entry == "displaced" else 0
            for arm, ts in trial_matrix():
                jobs.append((job(c, camp, arm, entry, seed, ref,
                                 RUNS / c.name / "trial" / entry / arm / ts), arm, ts))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(lambda t: run_evaluate(t[0], camp, t[1], t[2]), jobs))


def stage_timing(names):
    camp = campaign(chosen_tau())
    for c in configs(camp, names):
        ref = reference_of(c)
        for arm, ts in TIMING_VARIANTS:
            entry_dir = RUNS / c.name / "trial" / "displaced" / arm / ts
            run_inproc("timing", c, camp, arm, ts, entry_dir / "y_entry.json",
                       RUNS / c.name / "timing" / f"{arm}_{ts}", ref,
                       seed=SEED_TRIAL, entry="displaced")


# --------------------------------------------------------------------------
# summary
# --------------------------------------------------------------------------


def summarise():
    from harness.child import predicate as predicate_mod

    tau = chosen_tau()
    camp = campaign(tau)
    ts_all = json.loads((HERE / "test_sets.json").read_text())["configurations"]
    rbw = json.loads(RBW_SETS_FILE.read_text())["configurations"]
    out = {"generated_by": "arch_surgery/coupling_subset_trial/run_trial.py --summarise",
           "tau": tau, "runs": [], "timing": []}
    for c in camp.configurations:
        spec = predicate_mod.load_spec(c.coupling_state_path)
        comp = ts_all[c.name]["components"]
        exits = {}
        for entry in ENTRIES:
            for arm, tset in trial_matrix():
                d = RUNS / c.name / "trial" / entry / arm / tset
                if not (d / "metrics.json").exists():
                    continue
                rec = records_mod.read(d)
                row = {"configuration": c.name, "entry": entry, "arm": arm, "test_set": tset,
                       "status": rec.get("status")}
                nar = json.loads((d / "narrowing.json").read_text()) if (d / "narrowing.json").exists() else {}
                nb = nar.get("n_by_block") or {}
                mss = rec.get("module_solve_stats") or {}
                inner = mss.get("inner_counts") or {}
                iterated = [k for k, v in inner.items() if any(v) and k not in ("FF",)]
                row["n_test"] = {k: nb.get(k) for k in iterated} if nb else None
                row["node_calls"] = rec.get("node_calls_single_eval")
                row["sweeps_by_block"] = {k: inner[k] for k in iterated}
                if rec.get("status") != "ok":
                    row["error_tail"] = (rec.get("traceback") or "").strip().splitlines()[-1:]
                    out["runs"].append(row)
                    continue
                audit = rec.get("exit_audit") or {}
                row["audit_whole_max"] = audit.get("residual_max")
                row["audit_whole_n_above"] = (audit.get("brief") or {}).get("n_above")
                row["audit_whole_argmax"] = (audit.get("brief") or {}).get("argmax")
                vec = json.loads((d / "audit_residual.json").read_text())
                above = sorted(((k, v) for k, v in vec["scaled"].items() if v >= tau),
                               key=lambda kv: -kv[1])
                row["above_tau_whole"] = [
                    {"key": k, "scaled": v, "self_read": comp[k]["self_read"],
                     "dsm_feedback": comp[k]["feedback"], "writers": comp[k]["writers"]}
                    for k, v in above[:20]]
                row["n_above_tau_whole"] = len(above)
                exits[(entry, arm, tset)] = predicate_mod.restore_snapshot(
                    spec, json.loads((d / "y_exit.json").read_text()))
                out["runs"].append(row)
        for row in out["runs"]:
            if row["configuration"] != c.name or row.get("status") != "ok":
                continue
            base = exits.get((row["entry"], row["arm"], "full"))
            me = exits.get((row["entry"], row["arm"], row["test_set"]))
            if base is None or me is None or row["test_set"] == "full":
                continue
            res = spec.residual(base, me)
            row["distance_from_full_exit"] = {
                "max": float(res.max), "argmax": None if res.argmax is None else spec.name(res.argmax),
                "n_above_tau": int(res.n_above(tau)),
                "n_discrete_mismatch": len(res.mismatch_discrete)}
        for arm, tset in TIMING_VARIANTS:
            p = RUNS / c.name / "timing" / f"{arm}_{tset}" / "inproc.json"
            if not p.exists():
                continue
            r = json.loads(p.read_text())
            if r.get("status") != "ok":
                out["timing"].append({"configuration": c.name, "arm": arm, "test_set": tset,
                                      "status": r.get("status")})
                continue
            reps = r["reps"]
            wall = [x["call_models_s"] for x in reps]
            pred = [x["predicate_read_s"] + x["predicate_residual_s"] for x in reps]
            once = [x["once_per_run_s"] for x in reps]
            out["timing"].append({
                "configuration": c.name, "arm": arm, "test_set": tset, "status": "ok",
                "reps": len(reps),
                "node_calls": sorted({x["node_calls"] for x in reps}),
                "sweeps": sorted({x["sweeps"] for x in reps}),
                "call_models_ms_median": 1e3 * statistics.median(wall),
                "call_models_ms_range": [1e3 * min(wall), 1e3 * max(wall)],
                "predicate_ms_median": 1e3 * statistics.median(pred),
                "predicate_ms_range": [1e3 * min(pred), 1e3 * max(pred)],
                "predicate_share_median": statistics.median(p_ / w for p_, w in zip(pred, wall)),
                "once_per_run_ms_median": 1e3 * statistics.median(once),
                "n_read": reps[0]["n_read"], "n_residual": reps[0]["n_residual"],
                "model_ms_per_node_call_median": 1e3 * statistics.median(
                    (w - p_ ) / x["node_calls"] for w, p_, x in zip(wall, pred, reps)),
            })
    (RUNS / "trial_summary.json").write_text(json.dumps(out, indent=1))
    print(render(out, rbw))
    return out


def render(out, rbw):
    lines = [f"τ = {out['tau']:g}", "",
             "| configuration | entry | arm | test set | components tested (iterated blocks) | "
             "node calls | sweeps per block | exit audit max (whole y) | above τ at exit | "
             "distance from `full` exit |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in out["runs"]:
        sw = ", ".join(f"{k} {'/'.join(map(str, v))}" for k, v in (r.get("sweeps_by_block") or {}).items())
        nt = r.get("n_test")
        nt_s = "—" if not nt else ", ".join(f"{k} {v}" for k, v in nt.items())
        d = r.get("distance_from_full_exit")
        if r.get("status") != "ok":
            lines.append(f"| {r['configuration']} | {r['entry']} | {r['arm']} | {r['test_set']} | "
                         f"{nt_s} | — | — | {r['status']} {r.get('error_tail')} | — | — |")
            continue
        lines.append(
            f"| {r['configuration']} | {r['entry']} | {r['arm']} | {r['test_set']} | {nt_s} | "
            f"{r['node_calls']} | {sw} | {r['audit_whole_max']:.1e} | {r['n_above_tau_whole']} | "
            + ("—" if d is None else f"{d['max']:.1e}") + " |")
    lines += ["", "| configuration | arm | test set | reps | node calls | sweeps | "
              "call_models ms, median [min, max] | predicate ms, median [min, max] | "
              "predicate share | once-per-run ms | model ms per node call |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for t in out["timing"]:
        if t.get("status") != "ok":
            lines.append(f"| {t['configuration']} | {t['arm']} | {t['test_set']} | {t['status']} |||||||")
            continue
        lines.append(
            f"| {t['configuration']} | {t['arm']} | {t['test_set']} | {t['reps']} | "
            f"{'/'.join(map(str, t['node_calls']))} | {'/'.join(map(str, t['sweeps']))} | "
            f"{t['call_models_ms_median']:.1f} [{t['call_models_ms_range'][0]:.1f}, {t['call_models_ms_range'][1]:.1f}] | "
            f"{t['predicate_ms_median']:.2f} [{t['predicate_ms_range'][0]:.2f}, {t['predicate_ms_range'][1]:.2f}] | "
            f"{100 * t['predicate_share_median']:.1f} % | {t['once_per_run_ms_median']:.1f} | "
            f"{t['model_ms_per_node_call_median']:.2f} |")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    for s in ("references", "census", "derive-rbw", "noise", "choose-tau", "run", "timing",
              "summarise"):
        p.add_argument(f"--{s}", action="store_true")
    p.add_argument("--configuration", action="append")
    p.add_argument("--workers", type=int, default=3)
    a = p.parse_args()
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    if a.references:
        stage_references(a.configuration)
    if a.census:
        stage_census(a.configuration, a.workers)
    if a.derive_rbw:
        stage_derive_rbw()
    if a.noise:
        stage_noise(a.configuration, a.workers)
    if a.choose_tau:
        stage_choose_tau()
    if a.run:
        stage_run(a.configuration, a.workers)
    if a.timing:
        stage_timing(a.configuration)
    if a.summarise:
        summarise()


if __name__ == "__main__":
    main()
