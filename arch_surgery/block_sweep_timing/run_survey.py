#!/usr/bin/env python
"""Survey the wall clock of one block sweep, per block, per node and per test.

Task A91 (block-sweep-timing).  The user, 2026-09-29: *"survey the wallclock
time of individual module sweeps -- I want to know roughly how long each block
takes."*

Built on A89's scratch machinery (``arch_surgery/coupling_subset_trial/``):
the job composition goes through V4's own ``pool.environment_for`` and
``pool._command`` exactly as A89's ``run_trial.py`` composes it, with that
module imported and its records directory re-pointed at this task's.  Nothing
in the V4 folder is edited or run beyond its evaluation child.

Arms (A89 §7.1's definitions, kept so the numbers sit beside A89 §7.5):

``A0v4``  V4's ``A0``: flat, every node in every sweep, whole-``y`` test.
``A0``    A89's flat control: feed-forward nodes once per call after
          convergence, per-run nodes once after convergence.
``A2``    V4's ``A2`` (partitioned), per-run nodes once after convergence.

Test set ``full`` (V4's whole-``y`` test) at V4's τ = 1e-6, evaluation phase,
displaced entry seed 1 from each configuration's reference fixed point.

Stages, each reachable from this entry point::

    --references   V4's entry-reference job per configuration (A0v4, cold)
    --entries      one displaced (seed 1) evaluation per configuration and
                   arm through A89's wrapper: the entry snapshot each timing
                   child enters, and the counts the child is checked against
    --timing       the timed repetitions, serial: one subprocess per
                   configuration and arm, one warm-up, ``REPS`` timed
    --summarise    everything -> survey_summary.json and the report's tables
                   (no PROCESS run)

Records under ``arch_surgery/idf_probe/runs/block_sweep_timing/`` (untracked).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parent.parent
TRIAL_DIR = HERE.parent / "coupling_subset_trial"
V4_DIR = HERE.parent / "MDA_partitioning_experiment_v4"
RUNS = TREE / "arch_surgery" / "idf_probe" / "runs" / "block_sweep_timing"
CHILD = HERE / "timed_evaluations_child.py"
NODE_MAP = V4_DIR / "harness" / "data" / "dsm_node_map.json"

sys.path.insert(0, str(TRIAL_DIR))
sys.path.insert(0, str(V4_DIR))
sys.dont_write_bytecode = True

import run_trial as trial  # noqa: E402  A89's composition, re-pointed below

trial.RUNS = RUNS  # every stage of A89's module reads this global at call time

from harness.core import pool as pool_mod  # noqa: E402
from harness.core import records as records_mod  # noqa: E402

ARMS = ("A0v4", "A0", "A2")
SEED = 1
REPS = 7
BLOCK_ORDER = ("M1", "M2", "PULSE", "M3", "FF", "ONCE_PER_RUN", "FLAT")


def campaign():
    return trial.campaign(trial.V4_TAU)


def configs(camp, names):
    return trial.configs(camp, names)


# --------------------------------------------------------------------------
# stages
# --------------------------------------------------------------------------


def stage_references(names):
    trial.stage_references(names)


def entry_dir(c, arm):
    return RUNS / c.name / "entry" / arm


def stage_entries(names):
    camp = campaign()
    for c in configs(camp, names):
        ref = trial.reference_of(c)
        for arm in ARMS:
            j = trial.job(c, camp, arm, "displaced", SEED, ref, entry_dir(c, arm))
            trial.run_evaluate(j, camp, arm, "full", pass_log=False)


def timing_dir(c, arm, press=1):
    """Press 1 is the survey; a later press is a repeat of identical code, kept apart."""
    return RUNS / c.name / ("timing" if press == 1 else f"timing_press{press}") / arm


def stage_timing(names, press=1):
    camp = campaign()
    for c in configs(camp, names):
        ref = trial.reference_of(c)
        for arm in ARMS:
            outdir = timing_dir(c, arm, press)
            if (outdir / "sweep_timing.json").exists():
                continue
            j = trial.job(c, camp, arm, "displaced", SEED, ref, outdir)
            env, _ = trial.environment(j, camp)
            input_path, _ = pool_mod.assert_input_file_for(j, camp)
            command = [sys.executable, str(CHILD), "--tree", str(camp.tree),
                       "--configuration", c.name, "--arm", arm,
                       "--input", str(input_path),
                       "--coupling-state", str(c.coupling_state_path),
                       "--entry-state", str(entry_dir(c, arm) / "y_entry.json"),
                       "--outdir", str(outdir), "--reps", str(REPS)]
            t0 = time.perf_counter()
            rc = trial.launch(command, env, outdir, {"arm": arm, "tau": camp.tau,
                                                     "seed": SEED, "entry": "displaced",
                                                     "press": press}, 3600)
            status = (json.loads((outdir / "sweep_timing.json").read_text()).get("status")
                      if (outdir / "sweep_timing.json").exists() else "no_record")
            print(f"  timing {c.name:22s} {arm:4s} tau={camp.tau:.0e} rc={rc} "
                  f"status={status} {time.perf_counter() - t0:5.0f}s", flush=True)


# --------------------------------------------------------------------------
# summary
# --------------------------------------------------------------------------


def _stats(values):
    return {"median": statistics.median(values), "min": min(values), "max": max(values)}


def _ms(stat, digits=2):
    f = f"{{:.{digits}f}}"
    return (f"{f.format(1e3 * stat['median'])} [{f.format(1e3 * stat['min'])}, "
            f"{f.format(1e3 * stat['max'])}]")


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def node_modules():
    return {name: e["module"] for name, e in json.loads(NODE_MAP.read_text())["nodes"].items()
            if e.get("in_call_models_once")}


def summarise_case(c, arm, node_module, press=1):
    p = timing_dir(c, arm, press) / "sweep_timing.json"
    if not p.exists():
        return {"configuration": c.name, "arm": arm, "status": "absent"}
    r = json.loads(p.read_text())
    case = {"configuration": c.name, "arm": arm, "status": r.get("status"),
            "tree_git_head": r.get("tree_git_head"), "tree_git_dirty": r.get("tree_git_dirty"),
            "entry_readback_bitexact": r.get("entry_readback_bitexact")}
    if r.get("status") != "ok":
        case["error_tail"] = (r.get("traceback") or "").strip().splitlines()[-1:]
        return case
    reps = r["reps"]
    case["reps"] = len(reps)
    # counts and results: identical across repetitions, or the case is refused
    case["node_calls"] = sorted({x["node_calls"] for x in reps})
    case["sweeps"] = sorted({x["sweeps"] for x in reps})
    case["objf_hex"] = sorted({x["objf_hex"] for x in reps})
    case["conf_identical"] = len({tuple(x["conf_hex"]) for x in reps}) == 1
    case["inner_counts"] = sorted({json.dumps(x["module_solve_stats"]["inner_counts"],
                                              sort_keys=True) for x in reps})
    block_counts = sorted({json.dumps({k: [v["n_sweeps"], v["n_node_calls"], v["n_read"],
                                           v["n_residual"]]
                                       for k, v in x["timers"]["blocks"].items()},
                                      sort_keys=True) for x in reps})
    node_counts = sorted({json.dumps({k: v["n_calls"] for k, v in x["timers"]["nodes"].items()},
                                     sort_keys=True) for x in reps})
    case["counts_identical"] = (len(case["node_calls"]) == 1 and len(case["sweeps"]) == 1
                                and len(block_counts) == 1 and len(node_counts) == 1
                                and len(case["inner_counts"]) == 1)
    case["results_identical"] = len(case["objf_hex"]) == 1 and case["conf_identical"]
    case["n_outside_sweep_node_calls"] = sorted({x["n_outside_sweep_node_calls"] for x in reps})
    case["pending_read_s_unattributed_max"] = max(x["pending_read_s_unattributed"] for x in reps)
    if not case["counts_identical"]:
        case["refused"] = "repetitions differ in counts"
        return case
    case["block_counts"] = json.loads(block_counts[0])
    case["node_counts"] = json.loads(node_counts[0])
    # per evaluation
    ev = {"call_models_s": [x["call_models_s"] for x in reps],
          "wall_s": [x["wall_s"] for x in reps],
          "sweep_wall_s": [x["timers"]["sweep_wall_total_s"] for x in reps],
          "node_s": [sum(b["node_s"] for b in x["timers"]["blocks"].values()) for x in reps],
          "test_s": [sum(b["test_read_s"] + b["test_residual_s"]
                         for b in x["timers"]["blocks"].values()) for x in reps],
          "dispatch_s": [sum(b["dispatch_s"] + b["x_inject_s"] + b["fw_geometry_s"]
                             for b in x["timers"]["blocks"].values()) for x in reps],
          "predicate_a89_s": [x["predicate_read_s"] + x["predicate_residual_s"] for x in reps],
          "once_per_run_s": [x["once_per_run_s"] for x in reps]}
    for key in reps[0]["other"]:
        ev[key] = [x["other"][key] for x in reps]
    ev["other_named_s"] = [sum(x["other"].values()) for x in reps]
    ev["remainder_s"] = [cm - sw - t - o for cm, sw, t, o in
                         zip(ev["call_models_s"], ev["sweep_wall_s"], ev["test_s"],
                             ev["other_named_s"])]
    case["evaluation"] = {k: _stats(v) for k, v in ev.items()}
    # per block, per sweep
    blocks = {}
    for label in reps[0]["timers"]["blocks"]:
        rows = [x["timers"]["blocks"][label] for x in reps]
        ns = rows[0]["n_sweeps"]
        per = lambda key: [row[key] / ns for row in rows] if ns else [0.0] * len(rows)  # noqa: E731
        test = [(row["test_read_s"] + row["test_residual_s"]) / ns if ns else 0.0 for row in rows]
        blocks[label] = {
            "n_sweeps": ns, "n_node_calls_per_sweep": rows[0]["n_node_calls"] / ns if ns else 0,
            "n_nodes_in_block": rows[0]["n_nodes_in_block"],
            "n_read": rows[0]["n_read"], "n_residual": rows[0]["n_residual"],
            "wall_per_sweep": _stats(per("wall_s")),
            "node_per_sweep": _stats(per("node_s")),
            "x_inject_per_sweep": _stats(per("x_inject_s")),
            "fw_geometry_per_sweep": _stats(per("fw_geometry_s")),
            "dispatch_per_sweep": _stats(per("dispatch_s")),
            "test_per_sweep": _stats(test),
            "test_read_per_sweep": _stats(per("test_read_s")),
            "test_residual_per_sweep": _stats(per("test_residual_s")),
            "total_per_sweep": _stats([a + b for a, b in zip(per("wall_s"), test)]),
            "wall_total": _stats([row["wall_s"] for row in rows]),
            "test_total": _stats([row["test_read_s"] + row["test_residual_s"] for row in rows]),
        }
        # members of this block's sweeps by node-map module (a check on A2, the split on flat)
        by_mod = {}
        for row in rows:
            acc = {}
            for name, s in row["node_s_by_node"].items():
                mod = node_module.get(name, "?")
                acc[mod] = acc.get(mod, 0.0) + s
            for mod, s in acc.items():
                by_mod.setdefault(mod, []).append(s / ns if ns else 0.0)
        blocks[label]["node_per_sweep_by_module"] = {k: _stats(v) for k, v in by_mod.items()}
        blocks[label]["node_calls_per_sweep_by_module"] = {}
        for name, n in rows[0]["node_s_by_node"].items():
            mod = node_module.get(name, "?")
            blocks[label]["node_calls_per_sweep_by_module"][mod] = (
                blocks[label]["node_calls_per_sweep_by_module"].get(mod, 0)
                + case["node_counts"].get(name, 0) / ns)
    case["blocks"] = blocks
    nodes = {}
    for name in reps[0]["timers"]["nodes"]:
        calls = reps[0]["timers"]["nodes"][name]["n_calls"]
        nodes[name] = {"module": node_module.get(name, "?"), "n_calls": calls,
                       "per_call": _stats([x["timers"]["nodes"][name]["wall_s"] / calls
                                           for x in reps]),
                       "total": _stats([x["timers"]["nodes"][name]["wall_s"] for x in reps])}
    case["nodes"] = nodes
    return case


def summarise():
    camp = campaign()
    node_module = node_modules()
    out = {"generated_by": "arch_surgery/block_sweep_timing/run_survey.py --summarise",
           "tau": camp.tau, "seed": SEED, "reps": REPS, "arms": list(ARMS),
           "entries": [], "cases": []}
    for c in camp.configurations:
        ref_dir = RUNS / c.name / "reference"
        ref = records_mod.read(ref_dir) if (ref_dir / "metrics.json").exists() else {}
        entry = {"configuration": c.name, "reference_status": ref.get("status"),
                 "reference_tree_git_head": ref.get("tree_git_head"),
                 "reference_node_calls": ref.get("node_calls_single_eval"), "arms": {}}
        for arm in ARMS:
            d = entry_dir(c, arm)
            if not (d / "metrics.json").exists():
                entry["arms"][arm] = {"status": "absent"}
                continue
            rec = records_mod.read(d)
            entry["arms"][arm] = {
                "status": rec.get("status"), "tree_git_head": rec.get("tree_git_head"),
                "node_calls": rec.get("node_calls_single_eval"),
                "inner_counts": (rec.get("module_solve_stats") or {}).get("inner_counts"),
                "exit_audit_max": (rec.get("exit_audit") or {}).get("residual_max"),
                "y_entry_sha256": _sha(d / "y_entry.json") if (d / "y_entry.json").exists() else None}
        shas = {v.get("y_entry_sha256") for v in entry["arms"].values() if v.get("y_entry_sha256")}
        entry["y_entry_identical_across_arms"] = len(shas) == 1
        out["entries"].append(entry)
        for arm in ARMS:
            out["cases"].append(summarise_case(c, arm, node_module))
    # later presses of identical code, for the repeatability table only
    out["presses"] = {}
    press = 2
    while any((timing_dir(c, arm, press) / "sweep_timing.json").exists()
              for c in camp.configurations for arm in ARMS):
        out["presses"][str(press)] = [summarise_case(c, arm, node_module, press)
                                      for c in camp.configurations for arm in ARMS]
        press += 1
    (RUNS / "survey_summary.json").write_text(json.dumps(out, indent=1))
    text = render(out)
    (RUNS / "survey_tables.md").write_text(text)
    print(text)
    return out


def _case(out, cname, arm):
    for k in out["cases"]:
        if k["configuration"] == cname and k["arm"] == arm:
            return k
    return None


def _labels(case):
    return [b for b in BLOCK_ORDER if b in case["blocks"]] + sorted(
        b for b in case["blocks"] if b not in BLOCK_ORDER)


def _flat_cell(case, mod):
    """The flat arm's node time per FLAT sweep of *mod*'s member nodes, and their calls."""
    if case is None or case.get("status") != "ok" or case.get("refused"):
        return "—"
    b = case["blocks"].get("FLAT")
    if b is None or mod not in b["node_per_sweep_by_module"]:
        return "—"
    return f"{_ms(b['node_per_sweep_by_module'][mod])} ({b['node_calls_per_sweep_by_module'][mod]:g})"


def render_verdict(out):
    L = ["| configuration | block | A2 sweeps | A2 node calls per sweep | A2 sweep wall | "
         "A2 model (Σ node) | A2 test (read + residual) | A2 dispatch (x inject + fw geometry + "
         "other) | A2 sweep + test | A0v4 members per FLAT sweep (calls) | A0 members per FLAT "
         "sweep (calls) |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for cname in [e["configuration"] for e in out["entries"]]:
        a2 = _case(out, cname, "A2")
        if a2 is None or a2.get("status") != "ok" or a2.get("refused"):
            L.append(f"| {cname} | — | {(a2 or {}).get('refused') or (a2 or {}).get('status')} "
                     "|||||||||")
            continue
        for label in _labels(a2):
            b = a2["blocks"][label]
            disp = _stats([0.0])
            disp = {k: b["dispatch_per_sweep"][k] + b["x_inject_per_sweep"][k]
                    + b["fw_geometry_per_sweep"][k] for k in ("median", "min", "max")}
            mod = label if label in BLOCK_ORDER[:5] else None
            L.append(f"| {cname} | {label} | {b['n_sweeps']} | {b['n_node_calls_per_sweep']:g} | "
                     f"{_ms(b['wall_per_sweep'])} | {_ms(b['node_per_sweep'])} | "
                     f"{_ms(b['test_per_sweep'])} | {_ms(disp, 3)} | {_ms(b['total_per_sweep'])} | "
                     f"{_flat_cell(_case(out, cname, 'A0v4'), mod) if mod else '—'} | "
                     f"{_flat_cell(_case(out, cname, 'A0'), mod) if mod else '—'} |")
        for arm in ("A0v4", "A0"):
            k = _case(out, cname, arm)
            if k is None or k.get("status") != "ok" or k.get("refused"):
                continue
            b = k["blocks"]["FLAT"]
            disp = {kk: b["dispatch_per_sweep"][kk] + b["x_inject_per_sweep"][kk]
                    + b["fw_geometry_per_sweep"][kk] for kk in ("median", "min", "max")}
            L.append(f"| {cname} | *{arm} FLAT sweep (all nodes)* | {b['n_sweeps']} | "
                     f"{b['n_node_calls_per_sweep']:g} | {_ms(b['wall_per_sweep'])} | "
                     f"{_ms(b['node_per_sweep'])} | {_ms(b['test_per_sweep'])} | {_ms(disp, 3)} | "
                     f"{_ms(b['total_per_sweep'])} | — | — |")
    return "\n".join(L)


def render(out):
    L = [f"τ = {out['tau']:g}, displaced entry seed {out['seed']}, {out['reps']} timed "
         f"repetitions after 1 warm-up per subprocess", "",
         "**Verdict table** (ms per block sweep, median [min, max] over repetitions; the "
         "flat arms' columns are the node time per FLAT sweep of the nodes the node map "
         "assigns to the block, with their calls per sweep).", "", render_verdict(out), ""]
    # --- entries
    L += ["**Entries and counts** (one V4 evaluation per configuration and arm through A89's "
          "wrapper; the timing child enters the arm's own `y_entry.json`).", "",
          "| configuration | arm | status | node calls | sweeps per block | exit audit max | "
          "`y_entry.json` identical across arms | record head |", "|---|---|---|---|---|---|---|---|"]
    for e in out["entries"]:
        for arm, v in e["arms"].items():
            ic = v.get("inner_counts") or {}
            sw = ", ".join(f"{k} {'/'.join(map(str, x))}" for k, x in ic.items() if any(x))
            am = v.get("exit_audit_max")
            L.append(f"| {e['configuration']} | {arm} | {v.get('status')} | {v.get('node_calls')} | "
                     f"{sw} | {'—' if am is None else f'{am:.1e}'} | "
                     f"{e['y_entry_identical_across_arms']} | {str(v.get('tree_git_head'))[:8]} |")
    # --- per evaluation
    L += ["", "**Per evaluation** (ms, median [min, max] over the timed repetitions).", "",
          "| configuration | arm | reps | node calls | sweeps | counts identical | results "
          "identical | call_models | Σ sweep wall | Σ node | Σ test | Σ dispatch | "
          "module_schedule | per-run resolve | bind | objective | constraints | unattributed | "
          "A89 predicate | once-per-run | head |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k in out["cases"]:
        if k.get("status") != "ok" or k.get("refused"):
            L.append(f"| {k['configuration']} | {k['arm']} | {k.get('reps', '—')} | "
                     f"{'/'.join(map(str, k.get('node_calls', [])))} | "
                     f"{'/'.join(map(str, k.get('sweeps', [])))} | {k.get('counts_identical')} | "
                     f"{k.get('results_identical')} | {k.get('refused') or k.get('status')} "
                     f"{k.get('error_tail', '')} ||||||||||||| {str(k.get('tree_git_head'))[:8]} |")
            continue
        e = k["evaluation"]
        L.append(f"| {k['configuration']} | {k['arm']} | {k['reps']} | {k['node_calls'][0]} | "
                 f"{k['sweeps'][0]} | {k['counts_identical']} | {k['results_identical']} | "
                 f"{_ms(e['call_models_s'], 1)} | {_ms(e['sweep_wall_s'], 1)} | "
                 f"{_ms(e['node_s'], 1)} | {_ms(e['test_s'], 1)} | {_ms(e['dispatch_s'], 2)} | "
                 f"{_ms(e['module_schedule_s'], 2)} | {_ms(e['defer_per_run_resolve_s'], 3)} | "
                 f"{_ms(e['bind_s'], 2)} | {_ms(e['objective_s'], 3)} | "
                 f"{_ms(e['constraints_s'], 2)} | {_ms(e['remainder_s'], 2)} | "
                 f"{_ms(e['predicate_a89_s'], 1)} | {_ms(e['once_per_run_s'], 2)} | "
                 f"{str(k['tree_git_head'])[:8]} |")
    # --- per block sweep
    L += ["", "**Per block sweep** (ms per sweep of the block, median [min, max] over "
          "repetitions; each repetition's value is the block's total over the evaluation "
          "divided by its sweep count).", "",
          "| configuration | arm | block | sweeps | nodes in block | node calls per sweep | "
          "sweep wall | model (Σ node) | dispatch: x inject | dispatch: fw geometry | dispatch: "
          "other | test: read | test: residual | sweep + test | reads / residuals |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k in out["cases"]:
        if k.get("status") != "ok" or k.get("refused"):
            continue
        for label in _labels(k):
            b = k["blocks"][label]
            L.append(f"| {k['configuration']} | {k['arm']} | {label} | {b['n_sweeps']} | "
                     f"{b['n_nodes_in_block']} | {b['n_node_calls_per_sweep']:g} | "
                     f"{_ms(b['wall_per_sweep'])} | {_ms(b['node_per_sweep'])} | "
                     f"{_ms(b['x_inject_per_sweep'], 3)} | {_ms(b['fw_geometry_per_sweep'], 3)} | "
                     f"{_ms(b['dispatch_per_sweep'], 3)} | {_ms(b['test_read_per_sweep'])} | "
                     f"{_ms(b['test_residual_per_sweep'])} | {_ms(b['total_per_sweep'])} | "
                     f"{b['n_read']} / {b['n_residual']} |")
    # --- flat arms by module
    L += ["", "**Flat arms, node time per sweep by node-map module** (ms per FLAT sweep of the "
          "nodes the committed node map assigns to each module, median [min, max]; node calls "
          "per sweep in brackets).", "",
          "| configuration | arm | block swept | " + " | ".join(BLOCK_ORDER[:5]) + " |",
          "|---|---|---|" + "---|" * 5]
    for k in out["cases"]:
        if k.get("status") != "ok" or k.get("refused"):
            continue
        for label in _labels(k):
            b = k["blocks"][label]
            bm = b["node_per_sweep_by_module"]
            cm = b["node_calls_per_sweep_by_module"]
            cells = []
            for mod in BLOCK_ORDER[:5]:
                cells.append(f"{_ms(bm[mod])} ({cm[mod]:g})" if mod in bm else "—")
            L.append(f"| {k['configuration']} | {k['arm']} | {label} | " + " | ".join(cells) + " |")
    # --- repeatability across presses
    if out.get("presses"):
        presses = ["1", *sorted(out["presses"])]
        L += ["", "**Repeatability across presses** (ms per block sweep, sweep wall median "
              "[min, max]; each press is a separate serial run of identical code, 7 timed "
              "repetitions after 1 warm-up; counts identical across presses is checked).", "",
              "| configuration | arm | block | " + " | ".join(f"press {p}" for p in presses)
              + " | counts identical across presses |",
              "|---|---|---|" + "---|" * (len(presses) + 1)]
        for k in out["cases"]:
            if k.get("status") != "ok" or k.get("refused"):
                continue
            others = [next((q for q in out["presses"][p] if q["configuration"] == k["configuration"]
                            and q["arm"] == k["arm"]), None) for p in presses[1:]]
            same = all(q is not None and q.get("status") == "ok" and not q.get("refused")
                       and q["block_counts"] == k["block_counts"]
                       and q["node_counts"] == k["node_counts"] for q in others)
            for label in _labels(k):
                cells = [_ms(k["blocks"][label]["wall_per_sweep"])]
                for q in others:
                    b = (q or {}).get("blocks", {}).get(label)
                    cells.append(_ms(b["wall_per_sweep"]) if b else "—")
                L.append(f"| {k['configuration']} | {k['arm']} | {label} | " + " | ".join(cells)
                         + f" | {same} |")
        L += ["", "**Repeatability across presses, per evaluation** (ms, median [min, max]: "
              "`call_models` wall clock, and the `module_schedule` share of it).", "",
              "| configuration | arm | " + " | ".join(f"call_models press {p}" for p in presses)
              + " | " + " | ".join(f"module_schedule press {p}" for p in presses) + " |",
              "|---|---|" + "---|" * (2 * len(presses))]
        for k in out["cases"]:
            if k.get("status") != "ok" or k.get("refused"):
                continue
            others = [next((q for q in out["presses"][p] if q["configuration"] == k["configuration"]
                            and q["arm"] == k["arm"]), None) for p in presses[1:]]
            ok = [k] + [q if (q and q.get("status") == "ok" and not q.get("refused")) else None
                        for q in others]
            cm = [(_ms(q["evaluation"]["call_models_s"], 1) if q else "—") for q in ok]
            sc = [(_ms(q["evaluation"]["module_schedule_s"], 2) if q else "—") for q in ok]
            L.append(f"| {k['configuration']} | {k['arm']} | " + " | ".join(cm) + " | "
                     + " | ".join(sc) + " |")
    # --- per node
    L += ["", "**Per node** (ms per call, median [min, max] over repetitions of the "
          "per-repetition mean; calls per evaluation).", ""]
    for k in out["cases"]:
        if k.get("status") != "ok" or k.get("refused"):
            continue
        L += [f"*{k['configuration']}, {k['arm']}*", "",
              "| node | module | calls | ms per call | ms per evaluation |", "|---|---|---|---|---|"]
        order = sorted(k["nodes"].items(), key=lambda kv: (BLOCK_ORDER.index(kv[1]["module"])
                                                           if kv[1]["module"] in BLOCK_ORDER else 9,
                                                           -kv[1]["per_call"]["median"]))
        for name, v in order:
            L.append(f"| {name} | {v['module']} | {v['n_calls']} | {_ms(v['per_call'], 3)} | "
                     f"{_ms(v['total'], 2)} |")
        L.append("")
    return "\n".join(L)


def main():
    p = argparse.ArgumentParser()
    for s in ("references", "entries", "timing", "summarise"):
        p.add_argument(f"--{s}", action="store_true")
    p.add_argument("--configuration", action="append")
    p.add_argument("--press", type=int, default=1,
                   help="timing press number; 1 is the survey, a later one a repeat")
    a = p.parse_args()
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    if a.references:
        stage_references(a.configuration)
    if a.entries:
        stage_entries(a.configuration)
    if a.timing:
        stage_timing(a.configuration, a.press)
    if a.summarise:
        summarise()


if __name__ == "__main__":
    main()
