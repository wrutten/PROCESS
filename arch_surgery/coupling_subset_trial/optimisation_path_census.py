#!/usr/bin/env python
"""The read-before-write census over an optimisation run's evaluations, and its teeth.

Task A92 (optimisation-path-census), V5 improvement list item 6, prerequisite
(2).  A89 measured the read-before-write set — the components of the coupling
state ``y`` a sweep reads before it writes, per block, in the arm's own order —
on 8 displaced entries per configuration and arm (``rbw_sets.json``).  Branches
taken only on the optimiser's path (finite-difference probes of one design
variable, line-search points, retries) are unobserved there.  This script
measures the set over whole optimisation runs, compares it with the 8-entry
sets, and tests the set's teeth in the evaluation phase.

Stages, each reachable from this entry point (protocol §15)::

    --lifted-inputs        derive the lifted input files the partitioned
                           optimisation arm reads, by V4's committed derivation
                           (one gate-kind AR evaluation per pulsed configuration,
                           bytes gated on the declared digest)
    --census               whole optimisation runs of B0 (flat) and B2
                           (partitioned) from the campaign's seed 0 and seed 1,
                           with the census observing every evaluation; serial,
                           one PROCESS process at a time; ``--only`` filters
    --estimate             from the finished runs, the census's wall-clock cost
                           factor against the campaign records, and what the
                           remaining runs would cost (context, for the decision
                           to run them; whole runs only)
    --check-reproduction   each censused run against its campaign record:
                           status, ifail, solver iterations, evaluations, node
                           calls of the solve phase, norm_objf (hex).  A
                           mismatch is a finding
    --summarise-census     per run: the union per block, first appearance of
                           each component, the per-evaluation set-size
                           distribution, the comparison with the 8-entry sets;
                           writes ``optimisation_path_sets.json`` (committed)
    --references           the teeth's entry references (A89's, in this tree)
    --teeth                the evaluation-phase test with one component dropped
                           from the census set, by the rules below
    --summarise-teeth      the teeth table, verdict per row by the criterion
                           below

Arms.  ``B0`` is V4's flat optimisation arm (burn time in the loop, upstream
output loop); ``B2`` its partitioned one (burn time owned by the optimiser,
lifted input file).  The 8-entry sets to compare with are A89's ``A0``
(flat) and ``A2`` (partitioned) — the same loop shapes in the evaluation phase,
with two declared differences: A89's ``A0`` deferred the feed-forward nodes
out of its flat block (``PROCESS_ARCH_DEFER_PER_CALL=feedforward``) where
``B0`` sweeps them, and the burn time is a loop variable in ``B0`` and a
constant in ``A2``/optimiser variable in ``B2``.  The comparison names the
writer's module of every differing component so those two differences can be
told from a branch of the optimiser's path.

**Teeth: the rules, declared before the stage ran.**  Evaluation phase, A89's
``--run`` machinery: displaced entry (seed 1, δ = 0.10 around the entry
reference), arms ``A0`` and ``A2``, τ = 1e-8 (``tolerance.json``), test set =
the arm's 8-entry census set minus one component, the component chosen per
configuration and arm by:

1. ``max_exit_residual_carried`` — the carried component with the largest
   whole-``y`` exit residual under the full census test (read from the full
   ``rbw`` run's ``audit_residual.json``; ties, including a whole set at
   0.0, go to the alphabetically last key — rule 5 breaks ties the same way);
2. ``pf_coil_self_read`` — the alphabetically first ``pf_coil.*`` component
   among the set's DSM-self-read-only components;
3. ``most_sweeps_carried`` — the component carried in the most census sweeps
   (``detail[*][key].n_sweeps`` summed over blocks; ties alphabetical);
4. ``burn_time`` — ``times.t_plant_pulse_burn`` where the set carries it;
5. control ``max_exit_residual_not_carried`` — the component **not** in the
   set with the largest whole-``y`` exit residual under the full census test.

A component satisfying several rules is run once and listed under all of
them.  **Criterion.**  With a carried component dropped, either the loop
stops earlier (some block takes fewer sweeps than with the full set) AND the
whole-``y`` exit audit shows ≥ 1 component ≥ τ (*bites*), or nothing changes
— sweeps identical per block and the exit state bit-identical — in which case
the component is not individually binding on that entry (*not binding*).
Fewer sweeps with a clean audit means the drop escaped the audit at τ
(*escapes*); any other outcome is reported as it is (*other*).  With the
control dropped, nothing may change (*control PASS*/*FAIL*).  No run is
tuned or repeated.

Records under ``arch_surgery/idf_probe/runs/optimisation_path_census/``
(untracked; relocated at retirement).  The campaign's records are read
read-only from the relocated tree named by ``--campaign-records``.  Nothing is
written to the V4 folder.
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
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parent.parent
V4_DIR = HERE.parent / "MDA_partitioning_experiment_v4"
RUNS = TREE / "arch_surgery" / "idf_probe" / "runs" / "optimisation_path_census"
OPT_WRAPPER = HERE / "censused_optimise.py"
RBW_SETS_FILE = HERE / "rbw_sets.json"
PATH_SETS_FILE = HERE / "optimisation_path_sets.json"
SUMMARY = RUNS / "summary"
CAMPAIGN_RECORDS_DEFAULT = Path(
    "/home/wrutten/projects/PROCESS_surgery/arch_surgery/idf_probe/runs/A90_runs/campaign/optimisation"
)

sys.path.insert(0, str(V4_DIR))
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from harness.core import config as config_mod  # noqa: E402
from harness.core import pool as pool_mod  # noqa: E402
from harness.core import records as records_mod  # noqa: E402
from harness.experiment import input_files as input_files_mod  # noqa: E402

import run_trial  # noqa: E402  (A89's stages; its RUNS is rebound to this task's)

run_trial.RUNS = RUNS / "teeth"

OPT_ARMS = ("B0", "B2")
OPT_SEEDS = (0, 1)
OPT_TIMEOUT_S = 6 * 3600
#: The 8-entry set each optimisation arm is compared with: the same loop shape
#: in the evaluation phase (see the module docstring for the two differences).
EVAL_TWIN = {"B0": "A0", "B2": "A2"}
ITERATED = {"B0": ("FLAT",), "B2": ("M1", "M2", "M3")}
TEETH_ARMS = ("A0", "A2")
BURN_TIME = "times.t_plant_pulse_burn"
NODE_MAP = V4_DIR / "harness" / "data" / "dsm_node_map.json"


def campaign(tau=run_trial.V4_TAU):
    base = config_mod.default_campaign()
    return dataclasses.replace(base, runs_dir=RUNS, derived_input_dir=RUNS / "input_files",
                               tau=tau)


def configs(camp, names):
    return [c for c in camp.configurations if not names or c.name in names]


def campaign_dir(campaign_records, config_name, arm, seed):
    """The campaign record's directory: named on disk by the arm's name of its day."""
    recorded = {today: old for old, today in records_mod.RECORDED_ARM_NAMES.items()}
    return Path(campaign_records) / config_name / recorded.get(arm, arm) / f"seed{seed:03d}"


def campaign_record(campaign_records, config_name, arm, seed):
    rec = records_mod.read(campaign_dir(campaign_records, config_name, arm, seed))
    if rec.get("status") != "no_record" and rec.get("campaign_arm") != arm:
        raise SystemExit(f"campaign record for {config_name}/{arm}/seed{seed} reads as arm "
                         f"{rec.get('campaign_arm')!r} after translation")
    return rec


def opt_dir(config_name, arm, seed):
    return RUNS / "optimisation" / config_name / arm / f"seed{seed:03d}"


def opt_job(c, camp, arm, seed, outdir):
    return pool_mod.Job(
        phase="B", arm=arm, config=c, seed=seed, outdir=outdir,
        regime="perturbed" if seed else "unperturbed", delta=camp.delta,
        run_kind="smoke", timeout=OPT_TIMEOUT_S)


def run_optimise(j, camp):
    outdir = Path(j.outdir)
    if (outdir / "metrics.json").exists():
        return
    env, terms = run_trial.environment(j, camp)
    command = pool_mod._command(j, camp, terms)  # V4's own composition
    assert command[1].endswith("optimise.py"), command[:2]
    command = [command[0], str(OPT_WRAPPER), "--", *command[2:]]
    t0 = time.perf_counter()
    rc = run_trial.launch(command, env, outdir, {"arm": j.arm, "seed": j.seed, "census": True,
                                                 "tau": camp.tau}, j.timeout)
    if not (outdir / "metrics.json").exists():
        (outdir / "metrics.json").write_text(json.dumps({"status": "no_record", "returncode": rc}))
    rec = records_mod.read(outdir)
    print(f"  {j.config.name:22s} {j.arm:3s} seed={j.seed} rc={rc} status={rec.get('status')} "
          f"evaluations={(rec.get('sweeps_per_eval') or {}).get('n_evaluations')} "
          f"{time.perf_counter() - t0:6.0f}s", flush=True)


def matrix(camp, names, only):
    """(config, arm, seed) in the declared order: by the campaign record's evaluations."""
    rows = []
    for c in configs(camp, names):
        for arm in OPT_ARMS:
            for seed in OPT_SEEDS:
                rows.append((c, arm, seed))
    if only:
        keep = set(only)
        rows = [r for r in rows if f"{r[0].name}/{r[1]}/{r[2]}" in keep]
    return rows


# --------------------------------------------------------------------------
# stages
# --------------------------------------------------------------------------


def stage_lifted_inputs(names):
    camp = campaign()
    out = []
    for c in configs(camp, names):
        row = input_files_mod.derive_one(c, camp, runs_dir=RUNS / "lifted_inputs")
        out.append(row)
        print(f"  {c.name:22s} {row['verdict']}"
              + (f" sha256 {row['derived_sha256'][:12]} vs recorded {row['recorded_sha256'][:12]}"
                 if row.get("applicable") else ""))
    SUMMARY.mkdir(parents=True, exist_ok=True)
    (SUMMARY / "lifted_inputs.json").write_text(json.dumps(out, indent=1))
    if any(r.get("applicable") and r["verdict"] != "PASS" for r in out):
        raise SystemExit("a lifted input file did not match its recorded digest")


def stage_census(names, only, campaign_records):
    camp = campaign()
    rows = matrix(camp, names, only)

    def n_eval(r):
        rec = campaign_record(campaign_records, r[0].name, r[1], r[2])
        return (rec.get("sweeps_per_eval") or {}).get("n_evaluations") or 0

    rows.sort(key=n_eval)
    for c, arm, seed in rows:
        run_optimise(opt_job(c, camp, arm, seed, opt_dir(c.name, arm, seed)), camp)


def stage_estimate(campaign_records):
    camp = campaign()
    done, todo = [], []
    for c, arm, seed in matrix(camp, None, None):
        mine = records_mod.read(opt_dir(c.name, arm, seed))
        theirs = campaign_record(campaign_records, c.name, arm, seed)
        n = (theirs.get("sweeps_per_eval") or {}).get("n_evaluations")
        w = theirs.get("wall_s")
        if mine.get("status") == "ok":
            done.append((c.name, arm, seed, n, w, mine.get("wall_s"), mine["wall_s"] / w))
        else:
            todo.append((c.name, arm, seed, n, w))
    factors = [d[6] for d in done]
    f = statistics.median(factors) if factors else None
    print("finished (context, wall clock): configuration arm seed evaluations campaign_s censused_s factor")
    for d in done:
        print(f"  {d[0]:22s} {d[1]} {d[2]} {d[3]:6d} {d[4]:7.0f} {d[5]:7.0f} {d[6]:5.2f}")
    print(f"median factor {f}")
    if f is not None:
        print("remaining: configuration arm seed evaluations campaign_s projected_s")
        total = 0.0
        for t in todo:
            total += t[4] * f
            print(f"  {t[0]:22s} {t[1]} {t[2]} {t[3]:6d} {t[4]:7.0f} {t[4] * f:8.0f}")
        print(f"projected total for the remaining runs {total:.0f} s ({total / 3600:.1f} h)")


REPRO_FIELDS = (
    ("status", ("status",)),
    ("ifail", ("exit_forensics", "ifail")),
    ("n_solver_iterations", ("n_solver_iterations",)),
    ("n_evaluations", ("sweeps_per_eval", "n_evaluations")),
    ("node_calls_solve_phase", ("node_calls_solve_phase",)),
    ("norm_objf_hex", ("exact", "norm_objf")),
)
REPRO_CONTEXT = (
    ("dispatch_sweeps_solve_phase", ("dispatch_sweeps_solve_phase",)),
    ("sweeps_by_block", ("block_loop_totals", "sweeps_by_block")),
    ("n_attempts", ("attempt_accounting", "n_attempts")),
    ("tree_git_head", ("tree_git_head",)),
)


def _get(rec, path):
    cur = rec
    for p in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)
    return cur


def stage_check_reproduction(campaign_records):
    camp = campaign()
    out = {"generated_by": "arch_surgery/coupling_subset_trial/optimisation_path_census.py "
                           "--check-reproduction",
           "fields": [f for f, _ in REPRO_FIELDS], "campaign_records": str(campaign_records),
           "rows": []}
    lines = ["| configuration | arm | seed | " + " | ".join(f for f, _ in REPRO_FIELDS)
             + " | sweeps (solve phase) | attempts | wall s campaign / censused (context) | identical |",
             "|---|---|---|" + "---|" * len(REPRO_FIELDS) + "---|---|---|---|"]
    n_ok = n_rows = 0
    for c, arm, seed in matrix(camp, None, None):
        mine = records_mod.read(opt_dir(c.name, arm, seed))
        theirs = campaign_record(campaign_records, c.name, arm, seed)
        if mine.get("status") == "no_record":
            lines.append(f"| {c.name} | {arm} | {seed} | not run |" + " |" * (len(REPRO_FIELDS) + 3))
            out["rows"].append({"configuration": c.name, "arm": arm, "seed": seed, "status": "not run"})
            continue
        row = {"configuration": c.name, "arm": arm, "seed": seed, "fields": {}, "context": {}}
        cells = []
        identical = True
        for name, path in REPRO_FIELDS:
            a, b = _get(theirs, path), _get(mine, path)
            same = a == b
            identical &= same
            row["fields"][name] = {"campaign": a, "censused": b, "identical": same}
            cells.append(f"{b}" if same else f"**{b} vs campaign {a}**")
        for name, path in REPRO_CONTEXT:
            row["context"][name] = {"campaign": _get(theirs, path), "censused": _get(mine, path)}
        row["identical"] = identical
        row["wall_s"] = {"campaign": theirs.get("wall_s"), "censused": mine.get("wall_s")}
        n_rows += 1
        n_ok += identical
        out["rows"].append(row)
        sw_a, sw_b = _get(theirs, ("dispatch_sweeps_solve_phase",)), _get(mine, ("dispatch_sweeps_solve_phase",))
        at_a, at_b = _get(theirs, ("attempt_accounting", "n_attempts")), _get(mine, ("attempt_accounting", "n_attempts"))
        lines.append(
            f"| {c.name} | {arm} | {seed} | " + " | ".join(cells)
            + f" | {sw_b}" + ("" if sw_a == sw_b else f" (campaign {sw_a})")
            + f" | {at_b}" + ("" if at_a == at_b else f" (campaign {at_a})")
            + f" | {theirs.get('wall_s'):.0f} / {mine.get('wall_s'):.0f}"
            + f" | {'yes' if identical else 'NO'} |")
    out["n_identical"] = n_ok
    out["n_compared"] = n_rows
    SUMMARY.mkdir(parents=True, exist_ok=True)
    (SUMMARY / "reproduction_check.json").write_text(json.dumps(out, indent=1))
    heads = sorted({r["context"]["tree_git_head"]["censused"] for r in out["rows"] if "context" in r})
    heads_c = sorted({r["context"]["tree_git_head"]["campaign"] for r in out["rows"] if "context" in r})
    print("\n".join(lines))
    print(f"\n{n_ok} of {n_rows} censused runs reproduce their campaign record on every field; "
          f"censused runs at {heads}, campaign records at {heads_c}")


def node_modules():
    return {n: v["module"] for n, v in json.loads(NODE_MAP.read_text())["nodes"].items()}


def stage_summarise_census(campaign_records):
    camp = campaign()
    rbw = json.loads(RBW_SETS_FILE.read_text())["configurations"]
    modules = node_modules()
    out = {"format": "optimisation-path-sets-1",
           "generated_by": "arch_surgery/coupling_subset_trial/optimisation_path_census.py "
                           "--summarise-census",
           "rule": "a component of y that, in some observed sweep of the block, is read before "
                   "it is first written in that sweep and written later in it; here observed "
                   "over every evaluation of a whole optimisation run",
           "eight_entry_sets": str(RBW_SETS_FILE.name), "twin_of": EVAL_TWIN,
           "configurations": {}}
    lines = []
    for c in camp.configurations:
        out["configurations"][c.name] = {}
        for arm in OPT_ARMS:
            twin = rbw[c.name][EVAL_TWIN[arm]]
            twin_sets = {k: set(v) for k, v in twin["sets"].items()}
            twin_union = set().union(*twin_sets.values())
            per_run = {}
            union_by_block: dict = {}
            first_by_block: dict = {}
            reader_writer: dict = {}
            sizes_by_block: dict = {}
            once_labels: dict = {}
            for seed in OPT_SEEDS:
                d = opt_dir(c.name, arm, seed)
                rec = records_mod.read(d)
                p = d / "rbw_census_per_evaluation.json"
                if rec.get("status") != "ok" or not p.exists():
                    per_run[seed] = {"status": rec.get("status")}
                    continue
                ser = json.loads(p.read_text())
                agg = json.loads((d / "rbw_census.json").read_text())
                keys = ser["keys"]
                ev = ser["evaluations"]
                itvars = rec.get("itvar_names") or []
                run_union: dict = {}
                run_first: dict = {}
                run_sizes: dict = {}
                distinct: dict = {}
                run_count: dict = {}
                run_last: dict = {}
                size_by_sweeps: dict = {}
                for e in ev:
                    for label, idx in e["rbw"].items():
                        names = [keys[i] for i in idx]
                        run_sizes.setdefault(label, []).append(len(names))
                        size_by_sweeps.setdefault(label, {}).setdefault(
                            str(e["sweeps"].get(label)), []).append(len(names))
                        distinct.setdefault(label, set()).add(tuple(sorted(idx)))
                        for k in names:
                            run_union.setdefault(label, set()).add(k)
                            cnt = run_count.setdefault(label, {})
                            cnt[k] = cnt.get(k, 0) + 1
                            run_last.setdefault(label, {})[k] = e["i"]
                            if k not in run_first.setdefault(label, {}):
                                run_first[label][k] = {
                                    "evaluation": e["i"], "n_x_changed": e["n_x_changed"],
                                    "x_changed_index": e["x_changed_index"],
                                    "x_changed_name": (itvars[e["x_changed_index"]]
                                                       if e["x_changed_index"] is not None
                                                       and e["x_changed_index"] < len(itvars)
                                                       else None)}
                for label, keys_ in agg["rbw_by_block"].items():
                    if label not in ITERATED[arm]:
                        once_labels.setdefault(label, set()).update(keys_)
                    for k, e in keys_.items():
                        reader_writer.setdefault(label, {}).setdefault(k, e)
                sizes_by_block_run = {}
                for label, s in run_sizes.items():
                    sizes_by_block_run[label] = {
                        "n_evaluations_with_block": len(s), "min": min(s),
                        "median": statistics.median(s), "max": max(s),
                        "histogram": dict(sorted(Counter(s).items())),
                        "n_distinct_sets": len(distinct[label]),
                        "n_evaluations_equal_to_run_union": sum(
                            1 for t in s if t == len(run_union[label])),
                        "n_carried_in_every_evaluation": sum(
                            1 for k, n in run_count[label].items() if n == len(s)),
                        "size_by_sweeps_in_evaluation": {
                            sw: {"n_evaluations": len(v), "min": min(v),
                                 "median": statistics.median(v), "max": max(v)}
                            for sw, v in sorted(size_by_sweeps[label].items(),
                                                key=lambda kv: int(kv[0]))}}
                    sizes_by_block.setdefault(label, []).extend(s)
                for label, u in run_union.items():
                    union_by_block.setdefault(label, set()).update(u)
                    for k, f in run_first[label].items():
                        cur = first_by_block.setdefault(label, {}).get(k)
                        if cur is None or f["evaluation"] < cur["evaluation"]:
                            first_by_block[label][k] = dict(
                                f, seed=seed,
                                carried_in_evaluations={}, last_evaluation={})
                        ent = first_by_block[label][k]
                        ent["carried_in_evaluations"][str(seed)] = run_count[label][k]
                        ent["last_evaluation"][str(seed)] = run_last[label][k]
                per_run[seed] = {
                    "status": "ok", "n_evaluations": len(ev),
                    "n_evaluations_record": (rec.get("sweeps_per_eval") or {}).get("n_evaluations"),
                    "n_by_block": {k: len(v) for k, v in sorted(run_union.items())},
                    "sizes_by_block": sizes_by_block_run,
                    "n_fd_probes": sum(1 for e in ev if e["x_changed_index"] is not None),
                    "n_x_changed_histogram": dict(sorted(Counter(
                        str(e["n_x_changed"]) for e in ev).items())),
                    "tree_git_head": rec.get("tree_git_head"),
                    "sweeps_observed_by_block": agg["sweeps_observed_by_block"],
                }
            iterated = [lab for lab in ITERATED[arm] if lab in union_by_block]
            path_union = set().union(*(union_by_block[lab] for lab in iterated)) if iterated else set()
            comparison = {}
            for lab in iterated:
                twin_lab = twin_sets.get(lab, set())
                mine = union_by_block[lab]
                comparison[lab] = {
                    "n_path": len(mine), "n_eight_entry": len(twin_lab),
                    "n_common": len(mine & twin_lab),
                    "on_path_not_in_eight_entry": [
                        {"key": k, "reader": reader_writer[lab][k]["reader"],
                         "writer": reader_writer[lab][k]["writer"],
                         "writer_module": modules.get(reader_writer[lab][k]["writer"]),
                         "reader_module": modules.get(reader_writer[lab][k]["reader"]),
                         "first": first_by_block[lab][k],
                         "in_eight_entry_other_block": sorted(
                             l2 for l2, s2 in twin_sets.items() if k in s2)}
                        for k in sorted(mine - twin_lab)],
                    "in_eight_entry_not_on_path": [
                        {"key": k, "reader": twin["detail"][lab][k]["reader"],
                         "writer": twin["detail"][lab][k]["writer"],
                         "writer_module": modules.get(twin["detail"][lab][k]["writer"]),
                         "on_path_other_block": sorted(
                             l2 for l2, s2 in union_by_block.items() if k in s2)}
                        for k in sorted(twin_lab - mine)],
                }
            out["configurations"][c.name][arm] = {
                "runs": per_run,
                "iterated_blocks": iterated,
                "sets": {lab: sorted(union_by_block[lab]) for lab in iterated},
                "n_by_block": {lab: len(union_by_block[lab]) for lab in iterated},
                "n_union": len(path_union),
                "first_appearance": {lab: dict(sorted(first_by_block[lab].items(),
                                                      key=lambda kv: kv[1]["evaluation"]))
                                     for lab in iterated},
                "first_appearance_histogram": {
                    lab: dict(sorted(Counter(
                        str(f["evaluation"]) for f in first_by_block[lab].values()).items(),
                        key=lambda kv: int(kv[0])))
                    for lab in iterated},
                "sizes_by_block_both_runs": {
                    lab: {"min": min(s), "median": statistics.median(s), "max": max(s),
                          "histogram": dict(sorted(Counter(s).items()))}
                    for lab, s in sizes_by_block.items() if lab in iterated},
                "once_run_blocks": {lab: sorted(v) for lab, v in once_labels.items()},
                "comparison_with_eight_entry": comparison,
                "burn_time": {
                    "in_path_union": BURN_TIME in path_union,
                    "in_eight_entry_union": BURN_TIME in twin_union,
                    "blocks_on_path": sorted(l for l, s in union_by_block.items() if BURN_TIME in s),
                    "reader_writer_on_path": {l: reader_writer[l][BURN_TIME]
                                              for l in union_by_block if BURN_TIME in union_by_block[l]},
                },
            }
            for lab in iterated:
                cmp_ = comparison[lab]
                first_h = out["configurations"][c.name][arm]["first_appearance_histogram"][lab]
                n_first0 = int(first_h.get("0", 0))
                sizes = out["configurations"][c.name][arm]["sizes_by_block_both_runs"][lab]
                lines.append(
                    f"| {c.name} | {arm} | {lab} | "
                    f"{'/'.join(str(per_run[s].get('n_evaluations')) for s in OPT_SEEDS)} | "
                    f"{cmp_['n_path']} | {cmp_['n_eight_entry']} | {cmp_['n_common']} | "
                    f"{len(cmp_['on_path_not_in_eight_entry'])} | "
                    f"{len(cmp_['in_eight_entry_not_on_path'])} | "
                    f"{n_first0} / {cmp_['n_path'] - n_first0} | "
                    f"{sizes['min']} / {sizes['median']:g} / {sizes['max']} |")
    PATH_SETS_FILE.write_text(json.dumps(out, indent=1) + "\n")
    header = ["| configuration | arm | block | evaluations (seed 0 / seed 1) | on path | 8-entry | "
              "common | on path, not 8-entry | 8-entry, not on path | first seen at evaluation 0 / later | "
              "set size per evaluation min / median / max |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    print("\n".join(header + lines))
    for cname, arms in out["configurations"].items():
        for arm, d in arms.items():
            for lab, cmp_ in d["comparison_with_eight_entry"].items():
                for e in cmp_["on_path_not_in_eight_entry"]:
                    f = e["first"]
                    print(f"  on path, not 8-entry: {cname} {arm} {lab} {e['key']} "
                          f"(reader {e['reader']} [{e['reader_module']}], writer {e['writer']} "
                          f"[{e['writer_module']}], first at evaluation {f['evaluation']} "
                          f"seed {f['seed']}, n_x_changed {f['n_x_changed']}, "
                          f"probe of {f['x_changed_name']}; carried in evaluations "
                          f"{f['carried_in_evaluations']} of "
                          f"{ {s: d['runs'][int(s)].get('n_evaluations') for s in f['carried_in_evaluations']} }, "
                          f"last at {f['last_evaluation']}; in 8-entry blocks "
                          f"{e['in_eight_entry_other_block']})")
                for e in cmp_["in_eight_entry_not_on_path"]:
                    print(f"  8-entry, not on path: {cname} {arm} {lab} {e['key']} "
                          f"(reader {e['reader']}, writer {e['writer']} [{e['writer_module']}]; "
                          f"on path in blocks {e['on_path_other_block']})")
            print(f"  burn time {cname} {arm}: {d['burn_time']}")
    return out


# --------------------------------------------------------------------------
# teeth
# --------------------------------------------------------------------------


def teeth_dir(config_name, arm, test_set):
    return run_trial.RUNS / config_name / "trial" / "displaced" / arm / test_set.replace(":", "_")


def select_drops(config_name, arm, full_dir):
    """The components to drop, by the rules in the module docstring."""
    rbw = json.loads(RBW_SETS_FILE.read_text())["configurations"][config_name][arm]
    sets = {k: set(v) for k, v in rbw["sets"].items()}
    union = set().union(*sets.values())
    audit = json.loads((full_dir / "audit_residual.json").read_text())["scaled"]
    finite = {k: v for k, v in audit.items() if isinstance(v, (int, float)) and v == v}
    rules: dict = {}

    def pick(rule, key, note):
        if key is None:
            rules[rule] = {"key": None, "note": f"no candidate: {note}"}
        else:
            rules[rule] = {"key": key, "note": note}

    carried = {k: v for k, v in finite.items() if k in union}
    k = max(carried, key=lambda kk: (carried[kk], kk)) if carried else None
    pick("max_exit_residual_carried", k,
         f"exit residual {carried.get(k)!r} under the full census test" if k else "empty")
    self_reads = sorted(x for x in rbw["against_dsm"]["dsm_self_read_only"]
                        if x.startswith("pf_coil."))
    pick("pf_coil_self_read", self_reads[0] if self_reads else None,
         f"first of {len(self_reads)} pf_coil.* self-read components")
    n_sweeps = {}
    for label, det in rbw["detail"].items():
        for kk, e in det.items():
            n_sweeps[kk] = n_sweeps.get(kk, 0) + e["n_sweeps"]
    k = None
    if n_sweeps:  # the maximal count, ties alphabetical
        top = max(n_sweeps.values())
        k = sorted(kk for kk, v in n_sweeps.items() if v == top)[0]
    pick("most_sweeps_carried", k, f"carried in {n_sweeps.get(k)} of the census sweeps" if k else "empty")
    pick("burn_time", BURN_TIME if BURN_TIME in union else None, "in the set" if BURN_TIME in union
         else "the set does not carry the burn time")
    not_carried = {k: v for k, v in finite.items() if k not in union}
    k = max(not_carried, key=lambda kk: (not_carried[kk], kk)) if not_carried else None
    pick("max_exit_residual_not_carried", k,
         f"exit residual {not_carried.get(k)!r} under the full census test; CONTROL (not in the set)"
         if k else "empty")
    return rules


def stage_references(names):
    run_trial.stage_references(names)


def stage_teeth(names):
    camp = run_trial.campaign(run_trial.chosen_tau())
    selection = {}
    for c in configs(camp, names):
        ref = run_trial.reference_of(c)
        for arm in TEETH_ARMS:
            full = teeth_dir(c.name, arm, "rbw")
            run_trial.run_evaluate(run_trial.job(c, camp, arm, "displaced", run_trial.SEED_TRIAL,
                                                 ref, full), camp, arm, "rbw")
            if records_mod.read(full).get("status") != "ok":
                print(f"  {c.name} {arm}: the full rbw run did not finish; no drops run")
                continue
            rules = select_drops(c.name, arm, full)
            selection.setdefault(c.name, {})[arm] = rules
            keys = sorted({r["key"] for r in rules.values() if r["key"]})
            for key in keys:
                ts = f"rbw-minus:{key}"
                run_trial.run_evaluate(run_trial.job(c, camp, arm, "displaced", run_trial.SEED_TRIAL,
                                                     ref, teeth_dir(c.name, arm, ts)), camp, arm, ts)
    SUMMARY.mkdir(parents=True, exist_ok=True)
    (SUMMARY / "teeth_selection.json").write_text(json.dumps(selection, indent=1))


def _sweeps_by_block(rec):
    inner = (rec.get("module_solve_stats") or {}).get("inner_counts") or {}
    return {k: v for k, v in inner.items() if any(v)}


def stage_summarise_teeth():
    from harness.child import predicate as predicate_mod

    tau = run_trial.chosen_tau()
    camp = run_trial.campaign(tau)
    selection = json.loads((SUMMARY / "teeth_selection.json").read_text())
    out = {"generated_by": "arch_surgery/coupling_subset_trial/optimisation_path_census.py "
                           "--summarise-teeth", "tau": tau, "rows": []}
    lines = ["| configuration | arm | dropped component | rule(s) | dropped from blocks | "
             "sweeps per block (full → dropped) | node calls (full → dropped) | "
             "exit audit max (whole y) | above τ at exit | exit state vs full | verdict |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in camp.configurations:
        spec = predicate_mod.load_spec(c.coupling_state_path)
        for arm in TEETH_ARMS:
            rules = (selection.get(c.name) or {}).get(arm)
            if not rules:
                continue
            full_dir = teeth_dir(c.name, arm, "rbw")
            full = records_mod.read(full_dir)
            full_sw = _sweeps_by_block(full)
            full_state = json.loads((full_dir / "y_exit.json").read_text())
            full_y = predicate_mod.restore_snapshot(spec, full_state)
            full_audit = json.loads((full_dir / "audit_residual.json").read_text())["scaled"]
            full_above = sum(1 for v in full_audit.values() if isinstance(v, (int, float)) and v >= tau)
            lines.append(f"| {c.name} | {arm} | — (full census set) | — | — | "
                         + ", ".join(f"{k} {'/'.join(map(str, v))}" for k, v in full_sw.items())
                         + f" | {full.get('node_calls_single_eval')} | "
                         f"{(full.get('exit_audit') or {}).get('residual_max'):.1e} | {full_above} | — | — |")
            by_key: dict = {}
            for rule, r in rules.items():
                if r["key"]:
                    by_key.setdefault(r["key"], []).append(rule)
            for key, rule_names in sorted(by_key.items()):
                ts = f"rbw-minus:{key}"
                d = teeth_dir(c.name, arm, ts)
                rec = records_mod.read(d)
                row = {"configuration": c.name, "arm": arm, "key": key, "rules": rule_names,
                       "status": rec.get("status")}
                if rec.get("status") != "ok":
                    row["error_tail"] = (rec.get("traceback") or "").strip().splitlines()[-1:]
                    out["rows"].append(row)
                    lines.append(f"| {c.name} | {arm} | `{key}` | {', '.join(rule_names)} | ? | "
                                 f"{rec.get('status')} {row['error_tail']} | | | | | |")
                    continue
                nar = json.loads((d / "narrowing.json").read_text())
                dropped_from = nar.get("dropped_from_blocks") or []
                sw = _sweeps_by_block(rec)
                audit = json.loads((d / "audit_residual.json").read_text())["scaled"]
                above = sorted(((k, v) for k, v in audit.items()
                                if isinstance(v, (int, float)) and v >= tau), key=lambda kv: -kv[1])
                state = json.loads((d / "y_exit.json").read_text())
                y = predicate_mod.restore_snapshot(spec, state)
                res = spec.residual(full_y, y)
                bit_identical = state["state"] == full_state["state"]
                fewer = any(sum(sw.get(k, [])) < sum(v) for k, v in full_sw.items())
                same_sweeps = sw == full_sw
                is_control = not dropped_from
                if is_control:
                    verdict = "control PASS" if (same_sweeps and bit_identical) else "control FAIL"
                elif fewer and len(above) >= 1:
                    verdict = "bites"
                elif same_sweeps and bit_identical:
                    verdict = "not binding"
                elif fewer and not above:
                    verdict = "ESCAPES"
                else:
                    verdict = "other"
                row.update({
                    "dropped_from_blocks": dropped_from, "sweeps_full": full_sw, "sweeps_dropped": sw,
                    "node_calls_full": full.get("node_calls_single_eval"),
                    "node_calls_dropped": rec.get("node_calls_single_eval"),
                    "audit_max": (rec.get("exit_audit") or {}).get("residual_max"),
                    "above_tau": [{"key": k, "scaled": v} for k, v in above[:10]],
                    "n_above_tau": len(above),
                    "dropped_component_exit_residual": audit.get(key),
                    "exit_vs_full": {"max": float(res.max), "n_above_tau": int(res.n_above(tau)),
                                     "bit_identical": bit_identical},
                    "verdict": verdict})
                out["rows"].append(row)
                sw_cells = ", ".join(
                    f"{k} {'/'.join(map(str, full_sw.get(k, [])))} → {'/'.join(map(str, sw.get(k, [])))}"
                    for k in sorted(set(full_sw) | set(sw)))
                lines.append(
                    f"| {c.name} | {arm} | `{key}` | {', '.join(rule_names)} | "
                    f"{', '.join(dropped_from) or 'none (control)'} | {sw_cells} | "
                    f"{full.get('node_calls_single_eval')} → {rec.get('node_calls_single_eval')} | "
                    f"{row['audit_max']:.1e} | {len(above)}"
                    + (f" (max `{above[0][0]}` {above[0][1]:.1e})" if above else "")
                    + f" | {'bit-identical' if bit_identical else f'{float(res.max):.1e}'} | {verdict} |")
    out["verdict_counts"] = dict(Counter(r.get("verdict", r.get("status")) for r in out["rows"]))
    (SUMMARY / "teeth_summary.json").write_text(json.dumps(out, indent=1))
    print("\n".join(lines))
    print(f"\nverdicts: {out['verdict_counts']}")
    return out


def main():
    p = argparse.ArgumentParser()
    for s in ("lifted-inputs", "census", "estimate", "check-reproduction", "summarise-census",
              "references", "teeth", "summarise-teeth"):
        p.add_argument(f"--{s}", action="store_true")
    p.add_argument("--configuration", action="append")
    p.add_argument("--only", action="append",
                   help="census: restrict to '<configuration>/<arm>/<seed>' (repeatable)")
    p.add_argument("--campaign-records", type=Path, default=CAMPAIGN_RECORDS_DEFAULT)
    a = p.parse_args()
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    if a.lifted_inputs:
        stage_lifted_inputs(a.configuration)
    if a.census:
        stage_census(a.configuration, a.only, a.campaign_records)
    if a.estimate:
        stage_estimate(a.campaign_records)
    if a.check_reproduction:
        stage_check_reproduction(a.campaign_records)
    if a.summarise_census:
        stage_summarise_census(a.campaign_records)
    if a.references:
        stage_references(a.configuration)
    if a.teeth:
        stage_teeth(a.configuration)
    if a.summarise_teeth:
        stage_summarise_teeth()


if __name__ == "__main__":
    main()
