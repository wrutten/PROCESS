#!/usr/bin/env python
"""Stop V4's evaluation-phase loops on a narrowed test set, and compare.

Task A89 (coupling-subset-trial), 2026-09-29.  The user: *"For each config, do
one run using only the [data-interface] coupling vars, run once using [the
feedback couplings], run in both A0 and A2 arms.  Compare the convergence
properties of these cases.  If you notice that specific variables are missing,
report about this.  Build on the v4 machinery, but do not write any files to the
v4 folder."*

**What is run.**  Per configuration, V4's own evaluation-phase jobs — composed
by V4's ``pool`` / ``arms`` / ``reproduction.entry_pin``, not by hand — for arms
``A0`` (flat) and ``A2`` (partitioned), each under three test sets:

* ``full`` — V4 unchanged, the whole of ``y``: the control;
* ``interface`` and ``feedback`` — from ``test_sets.json``
  (``derive_test_sets.py``).

at two entries: the **displaced** entry V4's campaign uses (seed 1, δ = 0.10
around the configuration's reference fixed point), and the **cold** entry (the
input file's own point, seed 0, no entered state).  The reference fixed point
is V4's own entry-reference job (flat ``A0``, full test, cold entry), made
here, so every entry is derived from a run of this trial.

**Where things go.**  Records under ``arch_surgery/idf_probe/runs/
coupling_subset_trial/`` (untracked); nothing is written to the V4 folder:
bytecode writing is off and numba's cache is redirected into the runs
directory.  The campaign object is V4's ``default_campaign()`` with its two
run directories moved here.

**What is compared** (``--summarise``; no PROCESS run): per run, the status,
node calls and sweeps of the one evaluation, the sweeps per block, the exit
audit (one further full sweep over the whole of ``y``, the restricted
statistic that excludes the once-per-run nodes' components beside it), the
components above τ at exit and whether each was in the test set, and the
distance of the exit state from the ``full`` run's exit at the same arm and
entry.  From the per-pass log, how far the whole state still moved at the pass
the narrowed test stopped on.

Usage::

    python run_trial.py --run [--configuration NAME ...] [--workers 3]
    python run_trial.py --summarise
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parent.parent
V4_DIR = HERE.parent / "MDA_partitioning_experiment_v4"
RUNS = TREE / "arch_surgery" / "idf_probe" / "runs" / "coupling_subset_trial"
TEST_SETS_FILE = HERE / "test_sets.json"
WRAPPER = HERE / "narrowed_evaluate.py"

sys.path.insert(0, str(V4_DIR))
sys.dont_write_bytecode = True

from harness.core import config as config_mod  # noqa: E402
from harness.core import pool as pool_mod  # noqa: E402
from harness.core import records as records_mod  # noqa: E402
from harness.gates import reproduction as reproduction_mod  # noqa: E402

ARMS = ("A0", "A2")
TEST_SETS = ("full", "interface", "feedback")
ENTRIES = ("displaced", "cold")
SEED_DISPLACED = 1


def campaign():
    base = config_mod.default_campaign()
    return dataclasses.replace(
        base, runs_dir=RUNS, derived_input_dir=RUNS / "input_files"
    )


def run_one(job, camp, test_set: str) -> dict:
    """One isolated run through the wrapper: fresh subprocess, own directory."""
    outdir = Path(job.outdir)
    if (outdir / "metrics.json").exists():
        return {"outdir": str(outdir), "kept": True}
    outdir.mkdir(parents=True, exist_ok=True)
    env, terms = pool_mod.environment_for(job, camp)
    command = pool_mod._command(job, camp, terms)  # V4's own composition
    assert command[1].endswith("evaluate.py"), command[:2]
    command = [
        command[0], str(WRAPPER),
        "--test-sets", str(TEST_SETS_FILE), "--test-set", test_set, "--",
        *command[2:],
    ]
    env = dict(env)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["NUMBA_CACHE_DIR"] = str(RUNS / "numba_cache")
    (outdir / "command.json").write_text(json.dumps({
        "command": command,
        "architecture_environment": {k: v for k, v in env.items() if k.startswith("PROCESS_ARCH")},
        "pythonpath": env.get("PYTHONPATH"),
        "test_set": test_set,
        "job": {"arm": job.arm, "configuration": job.config.name, "seed": job.seed,
                "regime": job.regime, "delta": job.delta, "pin_hex": job.pin_hex,
                "entry_state": str(job.entry_state) if job.entry_state else None},
    }, indent=1))
    t0 = time.perf_counter()
    try:
        done = subprocess.run(command, env=env, capture_output=True, text=True,
                              cwd=str(outdir), timeout=job.timeout)
        rc = done.returncode
        (outdir / "stdout.log").write_text(done.stdout)
        (outdir / "stderr.log").write_text(done.stderr)
    except subprocess.TimeoutExpired:
        rc = 124
    if not (outdir / "metrics.json").exists():
        (outdir / "metrics.json").write_text(json.dumps(
            {"status": "no_record", "returncode": rc}))
    rec = records_mod.read(outdir)
    print(f"  {job.config.name:22s} {job.arm} {test_set:9s} {job.regime:11s} "
          f"rc={rc} status={rec.get('status')} {time.perf_counter() - t0:5.0f}s",
          flush=True)
    return {"outdir": str(outdir), "rc": rc, "status": rec.get("status")}


def reference_job(config):
    return pool_mod.Job(phase="A", arm="A0", config=config, seed=0,
                        outdir=RUNS / config.name / "reference",
                        regime="unperturbed", delta=None, run_kind="smoke")


def trial_jobs(config, camp, reference):
    jobs = []
    for entry in ENTRIES:
        for arm in ARMS:
            for test_set in TEST_SETS:
                displaced = entry == "displaced"
                seed = SEED_DISPLACED if displaced else 0
                job = pool_mod.Job(
                    phase="A", arm=arm, config=config, seed=seed,
                    outdir=RUNS / config.name / entry / arm / test_set,
                    regime="perturbed" if displaced else "unperturbed",
                    delta=camp.delta if displaced else None,
                    pin_hex=reproduction_mod.entry_pin(
                        config, arm, reference, seed=seed,
                        delta=camp.delta if displaced else None),
                    entry_state=(Path(reference["snapshot"]) if displaced else None),
                    run_kind="smoke",
                )
                jobs.append((job, test_set))
    return jobs


def do_run(names, workers):
    camp = campaign()
    configs = [c for c in camp.configurations if not names or c.name in names]
    for config in configs:
        ref = reference_job(config)
        run_one(ref, camp, "full")
        rec = records_mod.read(ref.outdir)
        if rec.get("status") != "ok":
            print(f"  reference for {config.name} did not finish; skipped")
            continue
        reference = {"snapshot": str(Path(ref.outdir) / "y_exit.json"),
                     "t_plant_pulse_burn_hex": rec.get("t_plant_pulse_burn_hex")}
        jobs = trial_jobs(config, camp, reference)
        with ThreadPoolExecutor(max_workers=workers) as ex:
            list(ex.map(lambda jt: run_one(jt[0], camp, jt[1]), jobs))


# --------------------------------------------------------------------------
# the comparison
# --------------------------------------------------------------------------


def summarise():
    from harness.child import predicate as predicate_mod

    sets = json.loads(TEST_SETS_FILE.read_text())["configurations"]
    camp = campaign()
    out = {"generated_by": "arch_surgery/coupling_subset_trial/run_trial.py --summarise",
           "tau": camp.tau, "runs": []}
    for config in camp.configurations:
        cs = sets[config.name]
        spec = predicate_mod.load_spec(config.coupling_state_path)
        exits = {}
        for entry in ENTRIES:
            for arm in ARMS:
                for test_set in TEST_SETS:
                    d = RUNS / config.name / entry / arm / test_set
                    if not (d / "metrics.json").exists():
                        continue
                    rec = records_mod.read(d)
                    row = {"configuration": config.name, "entry": entry, "arm": arm,
                           "test_set": test_set, "status": rec.get("status"),
                           "failure_class": rec.get("failure_class")}
                    nar = json.loads((d / "narrowing.json").read_text()) if (d / "narrowing.json").exists() else {}
                    row["n_test"] = nar.get("n_test", cs["n_y"] if test_set == "full" else None)
                    row["n_test_by_block"] = nar.get("n_by_block")
                    row["node_calls"] = rec.get("node_calls_single_eval")
                    row["sweeps"] = rec.get("n_model_calls_sweeps")
                    mss = rec.get("module_solve_stats") or {}
                    row["inner_sweeps_by_block"] = mss.get("inner_counts") or mss.get("inner_sweeps")
                    row["components_compared"] = rec.get("components_compared")
                    row["predicate_evaluations"] = rec.get("predicate_evaluations")
                    if rec.get("status") != "ok":
                        row["error_tail"] = (rec.get("traceback") or "").strip().splitlines()[-1:]
                        out["runs"].append(row)
                        continue
                    audit = rec.get("exit_audit") or {}
                    restricted = audit.get("restricted") or {}
                    row["audit_max"] = audit.get("residual_max")
                    row["audit_n_above"] = (audit.get("brief") or {}).get("n_above")
                    row["audit_argmax"] = (audit.get("brief") or {}).get("argmax")
                    row["audit_restricted_max"] = restricted.get("max")
                    row["audit_restricted_n_above"] = restricted.get("n_above")
                    row["audit_restricted_argmax"] = restricted.get("argmax")
                    vec = json.loads((d / "audit_residual.json").read_text())
                    excluded = set(vec.get("excluded_keys") or ())
                    test = set(cs["sets"].get(test_set, [])) if test_set != "full" else None
                    above = sorted(((k, v) for k, v in vec["scaled"].items()
                                    if v >= camp.tau and k not in excluded),
                                   key=lambda kv: -kv[1])
                    row["above_tau_restricted"] = [
                        {"key": k, "scaled": v,
                         "in_test": (test is None or k in test),
                         "interface": cs["components"][k]["interface"],
                         "feedback": cs["components"][k]["feedback"],
                         "self_read": cs["components"][k]["self_read"],
                         "writers": cs["components"][k]["writers"],
                         "readers": cs["components"][k]["readers"]}
                        for k, v in above]
                    # the per-pass log: where the narrowed test stopped
                    log = d / "pass_log.jsonl"
                    if log.exists():
                        passes = [json.loads(line) for line in log.read_text().splitlines()]
                        stops = [p for p in passes if p["narrow_converged"]]
                        row["passes_logged"] = len(passes)
                        row["at_stop"] = [
                            {"block": p["block"], "width": p["width"], "narrow_max": p["narrow_max"],
                             "full_max": p["full_max"], "full_argmax": p["full_argmax"],
                             "outside_n_above": p["outside_n_above"],
                             "outside_top": p["outside_top"][:5]}
                            for p in stops]
                    exits[(entry, arm, test_set)] = predicate_mod.restore_snapshot(
                        spec, json.loads((d / "y_exit.json").read_text()))
                    row["_excluded"] = sorted(excluded)
                    out["runs"].append(row)
        # distance of each narrowed exit from the full run's exit, same arm and entry
        for row in out["runs"]:
            if row["configuration"] != config.name or row["test_set"] == "full":
                continue
            key = (row["entry"], row["arm"], row["test_set"])
            base = exits.get((row["entry"], row["arm"], "full"))
            if key not in exits or base is None:
                continue
            res = spec.residual(base, exits[key])
            excluded = set(row["_excluded"])
            kept = [(spec.name(int(i)), float(v)) for i, v in zip(res.idx_c, res.scaled)
                    if spec.name(int(i)) not in excluded]
            kept.sort(key=lambda kv: -kv[1])
            row["distance_from_full_exit"] = {
                "whole_max": float(res.max),
                "restricted_max": kept[0][1] if kept else 0.0,
                "restricted_argmax": kept[0][0] if kept else None,
                "restricted_n_above_tau": sum(v >= camp.tau for _, v in kept),
                "top": kept[:8],
                "n_discrete_mismatch": len(res.mismatch_discrete),
            }
    for row in out["runs"]:
        row.pop("_excluded", None)
    path = RUNS / "trial_summary.json"
    path.write_text(json.dumps(out, indent=1))
    print(f"wrote {path}")
    print(render_table(out))
    return out


def render_table(out) -> str:
    """The comparison as a markdown table, one row per run, from the summary."""
    lines = [
        "| configuration | entry | arm | test set | components tested | node calls | "
        "sweeps per block | exit audit max (restricted) | above τ at exit | "
        "distance from `full` exit |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in out["runs"]:
        blocks = {k: v for k, v in (r.get("inner_sweeps_by_block") or {}).items()
                  if any(v)}
        dist = r.get("distance_from_full_exit")
        lines.append(
            f"| {r['configuration']} | {r['entry']} | {r['arm']} | {r['test_set']} | "
            f"{r['n_test']} | {r['node_calls']} | "
            + ", ".join(f"{k} {'/'.join(map(str, v))}" for k, v in blocks.items())
            + f" | {r.get('audit_restricted_max', float('nan')):.1e} | "
            f"{len(r.get('above_tau_restricted') or [])} | "
            + ("—" if dist is None else f"{dist['restricted_max']:.1e}")
            + " |"
        )
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run", action="store_true")
    p.add_argument("--summarise", action="store_true")
    p.add_argument("--configuration", action="append")
    p.add_argument("--workers", type=int, default=3)
    a = p.parse_args()
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    if a.run:
        do_run(a.configuration, a.workers)
    if a.summarise:
        summarise()


if __name__ == "__main__":
    main()
