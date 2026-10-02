#!/usr/bin/env python
"""What the block loops leave moving when they stop: the traced runs, read.

Task **A115 (v5-sweep-residual-trace)**.  Reads the traced runs of
``harness/traced_runs.py`` (``--traced-runs press``) under the four run IDs
(census and whole write set, at τ = 1e-6 and 1e-8), read-only, and prints the
declared statistics below.  No PROCESS run.  Every number in the A115 report is
printed by this script.

DECLARATION -- written and committed before any trace was read
==============================================================

Vocabulary.  A **stop** is the last sweep of one block loop in one evaluation
(``M1``, ``M2``, ``M3`` of the partitioned arms; ``FLAT`` of the flat arms):
the sweep at which the loop's test passed.  At every sweep the trace scores two
**parts** of the block's write set (driver change DR13): ``census`` -- the
block's census test set -- and ``non_census`` -- the rest of the block's write
set (the flat block's write set is the whole coupling state).  Under the census
test set the **out-of-test** part is ``non_census``; under the whole write set
there is none (both parts are tested).  A part is **open** at a sweep when its
largest scaled change is at or above τ or it has a discrete mismatch, a moved
constant or a new NaN.  **Downstream** of a stop: for a partitioned block, a
node of a later block of the schedule or of the deferred tail (the traced
record's ``schedule_resolution``), or the objective-and-constraints layer; for
the flat block, the objective-and-constraints layer.  **Who reads what**: the
run-time read census ``reads_by_node`` of the census stage's record
``runs/census_tau1e-08/census/<configuration>/optimisation/census.json`` (arm
``BR``, seed 0, one whole optimisation, the read half of the census instrument,
closed at the ``_call_models_once`` boundary -- trap T1; the node
``objective_constraints`` is the objective-and-constraints layer); its SHA-256
is printed.  Evaluation kinds (phase B): ``function``, ``gradient``,
``reconcile``, ``other`` (an unlabelled call); phase A: the measured evaluation
(the trace's last line; the warm-up's line is checked equal in sweeps).

Statistics, per configuration, arm, run ID, evaluation kind and block:

S1  the distribution of the out-of-test maximum at the stop (census run IDs):
    n stops, share exactly 0, median, p90, max, share open (≥ τ or flagged),
    share ≥ 10 τ;
S2  one-sweep stops: their number and share of the stops, and S1's open share
    over them;
S3  the component most often worst at the stop, inside the test (the test's
    own argmax) and outside it (the out-of-test argmax, over stops where the
    out-of-test maximum is non-zero, and over open stops), top three with
    counts;
S4  at open stops: the share whose **worst** out-of-test component is read
    downstream (later block or tail; objective and constraints; either), and
    the share with **any** open out-of-test component read downstream;
S5  gradient evaluations: over the finite-difference pairs (the ``+h`` and
    ``−h`` points of one column, consecutive in the trace), the share whose
    sweep count differs, per block and in total;
S6  the mirror, whole-write-set run IDs: the census part's maximum at the stop
    (share exactly 0, median, max); the sweep at which the census part was
    first closed (``k*``), the extra sweeps the write set took after it
    (``s − k*``, distribution), and the non-census maximum at ``k*`` -- what a
    census-tested loop entered from the same state would have stopped on.
    Exact for the flat block and for the first block of the partitioned
    schedule (``M1``), whose entry does not depend on another block's stop; an
    approximation for ``M2`` and ``M3``, which is said where printed;
S7  per run: the evaluations, and E (below).

The primary rate.  **E** = the share of gradient evaluations in which at least
one block stops with an open out-of-test component that is read downstream
(per arm as defined above); **E_obj** the same with "read by the objective and
constraints" alone, for both arm kinds.  Census run IDs only (zero by
construction under the whole write set).

The conjecture (the user's, to be tested and not assumed): *under the census
set some model outputs are not yet converged when a block stops, a later block
(or the optimiser) uses them, and this is the noise the optimiser sees.*  The
cases in which the campaigns measured the optimiser disturbed (D): st, census
1e-8, ``B2``; st, census 1e-6, ``B0`` and ``B2``.  Not disturbed (U): st, census
1e-8, ``B0``; tok, every arm, every setting (its iterations are equal in all four
campaigns).

C1  (outputs not converged at the stop) holds in a D case when at least 5 % of
    the block stops of its gradient evaluations are open out of the test.
C2  (they are used) holds in a D case when at least half of C1's open stops
    have an open out-of-test component read downstream.
C3  (it is what disturbs the optimiser) -- the rate E discriminates the
    disturbed from the undisturbed, in each of three declared comparisons at
    the same setting: T1 st over tok, arm for arm (st ``B0`` against tok
    ``B0``; st ``B2`` against tok ``B2``), census 1e-8 and 1e-6; T2 st census
    1e-8, ``B2`` over ``B0``; T3 st ``B0``, census 1e-6 over census 1e-8.  A
    comparison discriminates when the D side's E is at least twice the U
    side's (and the D side's is non-zero).

**Refuted** in a D case if C1 or C2 fails there.  **Supported** if C1 and C2
hold in every D case and every comparison of C3 discriminates.  Otherwise
**present but not shown to be the cause**: the mechanism is there and E does
not separate the disturbed cases from the undisturbed ones (A104's finding
that error size did not predict the stall is the precedent).  The flat arm is
tested by the same rule as the partitioned one, with downstream meaning the
objective and constraints.

Also printed: the seed rule of ``traced_runs.JOB_SETS`` re-derived from the
four campaigns' records (refused if it disagrees), and st's condition (at least
one traced start where ``B2`` at census 1e-8 ends more than 10 % from ``B0``'s
design, ``compare_campaigns.rel`` over ``exact.xcs``, and one where it does not).

Run: ``python stopping_sweep_residuals.py [--runs runs] [--out file.md]``.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import statistics
import sys
from collections import Counter, defaultdict
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from compare_campaigns import accepted, rel  # noqa: E402
from harness import traced_runs as traced_mod  # noqa: E402
from harness.core import framework  # noqa: E402
from harness.core import records as records_mod  # noqa: E402

RUN_IDS = ("census_tau1e-08", "census_tau1e-06", "write_set_tau1e-08", "write_set_tau1e-06")
CONFIGS = ("large_tokamak_nof", "low_aspect_ratio_DEMO", "st_regression")
SHORT = {"large_tokamak_nof": "tok", "low_aspect_ratio_DEMO": "lad", "st_regression": "st"}
ITERATED = ("M1", "M2", "M3", "FLAT")
OBJECTIVE_NODE = "objective_constraints"
C1_SHARE = 0.05
C2_SHARE = 0.5
C3_FACTOR = 2.0
DISTURBED = (("st_regression", "census_tau1e-08", "B2"), ("st_regression", "census_tau1e-06", "B0"), ("st_regression", "census_tau1e-06", "B2"))


def tau_of(run_id: str) -> float:
    return float(run_id.split("_tau")[1])


def test_set_of(run_id: str) -> str:
    return run_id.split("_tau")[0]


# --------------------------------------------------------------------------
# who reads what
# --------------------------------------------------------------------------


def read_census(runs: Path) -> dict[str, dict[str, Any]]:
    out = {}
    for cfg in CONFIGS:
        path = runs / "census_tau1e-08" / "census" / cfg / "optimisation" / "census.json"
        blob = path.read_bytes()
        data = json.loads(blob)
        out[cfg] = {
            "path": str(path.relative_to(runs)),
            "sha256": hashlib.sha256(blob).hexdigest(),
            "reads": {n: set(v) for n, v in data["reads_by_node"].items()},
            "arm": json.loads((path.parent / "metrics.json").read_text()).get("campaign_arm"),
        }
    return out


def downstream_of(record: dict[str, Any]) -> dict[str, list[str]]:
    """Per iterated block label: the nodes that run after it in one evaluation."""
    res = (record.get("schedule_resolution") or {}).get("resolutions") or []
    out: dict[str, list[str]] = {}
    if not res:
        return out
    schedule = res[0]["schedule"]
    tail = list(res[0].get("pre_predicate") or []) + list(res[0].get("post_predicate") or [])
    labels = [s[0] for s in schedule]
    for i, (label, _nodes, _it) in enumerate(schedule):
        later: list[str] = []
        for _l, nodes, _i in schedule[i + 1:]:
            later.extend(nodes)
        out[label] = later + tail
    out.setdefault("FLAT", tail)
    out["_labels"] = labels
    return out


# --------------------------------------------------------------------------
# the records and traces
# --------------------------------------------------------------------------


def traced_runs(runs: Path, run_id: str, job_set: str):
    base = runs / run_id / traced_mod.ROOT_NAME / job_set
    for phase_dir, phase in (("evaluation", "A"), ("optimisation", "B")):
        root = base / phase_dir
        if not root.exists():
            continue
        for cfg_dir in sorted(root.iterdir()):
            for arm_dir in sorted(cfg_dir.iterdir()):
                for seed_dir in sorted(arm_dir.iterdir()):
                    if (seed_dir / "metrics.json").exists():
                        yield phase, cfg_dir.name, arm_dir.name, int(seed_dir.name[4:]), seed_dir


def kind_of(evaluation: Any) -> str:
    if not evaluation:
        return "other"
    return str(evaluation[0])


def lines_of(seed_dir: Path):
    handle = traced_mod.open_trace(seed_dir)
    header = None
    with handle:
        for raw in handle:
            line = json.loads(raw)
            if line.get("kind") == "header":
                header = line
                continue
            yield header, line


def part_open(part: dict[str, Any] | None, tau: float) -> bool:
    if not part:
        return False
    return (part.get("max") or 0.0) >= tau or any(
        part.get(k) for k in ("discrete_mismatch", "moved_constant", "nan_new")
    )


def open_names(part: dict[str, Any] | None) -> list[str]:
    if not part:
        return []
    names = list(part.get("above") or [])
    for k in ("discrete_mismatch", "moved_constant", "nan_new"):
        names.extend(part.get(k) or [])
    return names


# --------------------------------------------------------------------------
# accumulation
# --------------------------------------------------------------------------


def new_cell() -> dict[str, Any]:
    return {
        "n_stops": 0, "out_max": [], "out_open": 0, "out_10tau": 0,
        "n_one": 0, "one_open": 0, "one_max": [],
        "test_argmax": Counter(), "out_argmax_nonzero": Counter(), "out_argmax_open": Counter(),
        "open_worst_down": 0, "open_worst_obj": 0, "open_worst_either": 0,
        "open_any_down": 0, "open_any_obj": 0, "open_any_either": 0,
        "open_names": Counter(),
        "census_at_stop": [], "kstar_extra": [], "nc_at_kstar": [], "nc_at_kstar_open": 0, "n_mirror": 0,
    }


def stats_line(values: list[float]) -> str:
    if not values:
        return "—"
    v = sorted(values)
    p90 = v[min(len(v) - 1, int(round(0.9 * (len(v) - 1))))]
    zero = sum(1 for x in v if x == 0.0)
    return f"0: {zero}/{len(v)}; med {statistics.median(v):.2e}; p90 {p90:.2e}; max {v[-1]:.2e}"


def share(a: int, b: int) -> str:
    return "—" if not b else f"{a}/{b} = {a / b:.3f}"


def analyse(runs: Path, job_sets: tuple[str, ...]) -> dict[str, Any]:
    census = read_census(runs)
    cells: dict[tuple, dict[str, Any]] = defaultdict(new_cell)
    per_run: dict[tuple, dict[str, Any]] = {}
    pairs: dict[tuple, dict[str, Any]] = defaultdict(lambda: {"n": 0, "differ_total": 0, "differ": Counter(), "blocks": Counter()})
    warmup_mismatch: list[str] = []
    for run_id in RUN_IDS:
        tau = tau_of(run_id)
        ts = test_set_of(run_id)
        for job_set in job_sets:
            for phase, cfg, arm, seed, seed_dir in traced_runs(runs, run_id, job_set):
                record = records_mod.read(seed_dir)
                down = downstream_of(record)
                reads = census[cfg]["reads"]
                obj_reads = reads.get(OBJECTIVE_NODE, set())
                lines = list(lines_of(seed_dir))
                if phase == "A":
                    if len(lines) >= 2 and lines[0][1]["sweeps"] != lines[-1][1]["sweeps"]:
                        warmup_mismatch.append(f"{run_id}/{cfg}/{arm}/seed{seed}")
                    lines = lines[-1:]
                run_key = (cfg, arm, run_id, job_set, seed, phase)
                run_row = {"n_eval": 0, "n_grad": 0, "E": 0, "E_obj": 0, "status": record.get("status"),
                           "ifail": (record.get("mfile") or {}).get("ifail"), "iterations": record.get("n_solver_iterations")}
                prev = None
                for _header, line in lines:
                    kind = "evaluation" if phase == "A" else kind_of(line.get("evaluation"))
                    run_row["n_eval"] += 1
                    grad = kind == "gradient"
                    if grad:
                        run_row["n_grad"] += 1
                    e_hit = e_obj_hit = False
                    for label, entries in (line.get("per_sweep") or {}).items():
                        if label not in ITERATED or not entries:
                            continue
                        stop = entries[-1]
                        parts = stop.get("parts") or {}
                        s = len(entries)
                        cell = cells[(cfg, arm, run_id, phase, kind, label)]
                        cell["n_stops"] += 1
                        if stop.get("test_argmax"):
                            cell["test_argmax"][stop["test_argmax"]] += 1
                        later = set(down.get(label, []))
                        later_reads = set().union(*(reads.get(n, set()) for n in later)) if later else set()
                        if ts == "census":
                            out = parts.get("non_census")
                            m = float((out or {}).get("max") or 0.0)
                            is_open = part_open(out, tau)
                            cell["out_max"].append(m)
                            cell["out_open"] += is_open
                            cell["out_10tau"] += m >= 10 * tau
                            if s == 1:
                                cell["n_one"] += 1
                                cell["one_open"] += is_open
                                cell["one_max"].append(m)
                            if m > 0 and out and out.get("argmax"):
                                cell["out_argmax_nonzero"][out["argmax"]] += 1
                            if is_open:
                                worst = out.get("argmax")
                                if worst:
                                    cell["out_argmax_open"][worst] += 1
                                names = open_names(out)
                                cell["open_names"].update(names)
                                w_down = bool(worst) and worst in later_reads
                                w_obj = bool(worst) and worst in obj_reads
                                a_down = any(n in later_reads for n in names)
                                a_obj = any(n in obj_reads for n in names)
                                cell["open_worst_down"] += w_down
                                cell["open_worst_obj"] += w_obj
                                cell["open_worst_either"] += w_down or w_obj
                                cell["open_any_down"] += a_down
                                cell["open_any_obj"] += a_obj
                                cell["open_any_either"] += a_down or a_obj
                                if a_down or a_obj:
                                    e_hit = True
                                if a_obj:
                                    e_obj_hit = True
                        elif "census" in parts:
                            cpart = parts["census"]
                            cell["census_at_stop"].append(float(cpart.get("max") or 0.0))
                            kstar = None
                            for k, entry in enumerate(entries, start=1):
                                if not part_open((entry.get("parts") or {}).get("census"), tau):
                                    kstar = k
                                    break
                            if kstar is not None:
                                cell["n_mirror"] += 1
                                cell["kstar_extra"].append(s - kstar)
                                nc = (entries[kstar - 1].get("parts") or {}).get("non_census")
                                cell["nc_at_kstar"].append(float((nc or {}).get("max") or 0.0))
                                cell["nc_at_kstar_open"] += part_open(nc, tau)
                    if grad:
                        run_row["E"] += e_hit
                        run_row["E_obj"] += e_obj_hit
                        ev = line.get("evaluation")
                        if prev is not None and prev[0][0] == "gradient" and ev[1] == prev[0][1] and prev[0][2] == 1 and ev[2] == -1:
                            pc = pairs[(cfg, arm, run_id)]
                            pc["n"] += 1
                            a_sw, b_sw = prev[1], line.get("sweeps") or {}
                            if sum(a_sw.values()) != sum(b_sw.values()):
                                pc["differ_total"] += 1
                            for blk in set(a_sw) | set(b_sw):
                                if blk in ITERATED:
                                    pc["blocks"][blk] += 1
                                    pc["differ"][blk] += a_sw.get(blk) != b_sw.get(blk)
                        prev = (ev, line.get("sweeps") or {})
                    else:
                        prev = None
                per_run[run_key] = run_row
    return {"census": census, "cells": cells, "per_run": per_run, "pairs": pairs, "warmup_mismatch": warmup_mismatch}


# --------------------------------------------------------------------------
# the seed rule, re-derived
# --------------------------------------------------------------------------


def seed_rule(runs: Path) -> dict[str, Any]:
    from harness.experiment import arms as arms_mod  # noqa: PLC0415

    out: dict[str, Any] = {}
    for cfg in CONFIGS:
        ok_all: set[int] | None = None
        for run_id in RUN_IDS:
            root = runs / run_id / "campaign" / "optimisation" / cfg
            ok: set[int] = set(range(25))
            for arm_dir in root.iterdir():
                for seed in range(25):
                    d = arm_dir / f"seed{seed:03d}"
                    if not (d / "metrics.json").exists() or not accepted(records_mod.read(d)):
                        ok.discard(seed)
            ok_all = ok if ok_all is None else ok_all & ok
        first3 = tuple(sorted(ok_all)[:3])
        declared = traced_mod.JOB_SETS["sweep_residual"].optimisation_seeds[cfg]
        out[cfg] = {"accepted_everywhere": sorted(ok_all), "first_three": first3, "declared": declared, "agrees": first3 == declared}
    # st's condition at census 1e-8, over every start both arms accepted
    root = runs / "census_tau1e-08" / "campaign" / "optimisation" / "st_regression"
    far: dict[int, float] = {}
    for seed in range(25):
        a = root / "B0" / f"seed{seed:03d}"
        b = root / "B2" / f"seed{seed:03d}"
        ra, rb = records_mod.read(a), records_mod.read(b)
        if not (accepted(ra) and accepted(rb)):
            continue
        xa = [float.fromhex(h) for h in ra["exact"]["xcs"]]
        xb = [float.fromhex(h) for h in rb["exact"]["xcs"]]
        far[seed] = max(rel(p, q) for p, q in zip(xa, xb))
    out["st_far"] = far
    return out


# --------------------------------------------------------------------------
# printing
# --------------------------------------------------------------------------


def top(counter: Counter, n: int = 3) -> str:
    return "; ".join(f"`{k}` {v}" for k, v in counter.most_common(n)) or "—"


def report(runs: Path, job_sets: tuple[str, ...]) -> None:
    head = framework.git_head()
    print(f"# Stopping-sweep residuals — printed by `stopping_sweep_residuals.py` at `{head[:8]}`\n")
    rule = seed_rule(runs)
    print("## 0. The seed rule and the traced population\n")
    for cfg in CONFIGS:
        r = rule[cfg]
        print(f"- {SHORT[cfg]}: starts accepted by every arm in all four campaigns {r['accepted_everywhere']}; first three {r['first_three']}; declared {r['declared']}; agrees: {r['agrees']}")
    far = rule["st_far"]
    traced_st = traced_mod.JOB_SETS["sweep_residual"].optimisation_seeds["st_regression"] + traced_mod.JOB_SETS["sweep_residual_st_more"].optimisation_seeds["st_regression"]
    print(f"- st, census 1e-8, B2 against B0, largest relative design difference per start (both accepted): "
          + ", ".join(f"{s}: {far[s]:.3g}{' (traced)' if s in traced_st else ''}" for s in sorted(far)))
    print()
    res = analyse(runs, job_sets)
    census = res["census"]
    print("**Who reads what**: " + "; ".join(f"{SHORT[c]} `{v['path']}` (arm {v['arm']}) sha256 `{v['sha256'][:16]}`" for c, v in census.items()))
    print(f"\nPhase A warm-up lines whose sweeps differ from the measured line's: {len(res['warmup_mismatch'])} {res['warmup_mismatch'][:5]}\n")

    print("## 1. Per run\n")
    print("| configuration | arm | run ID | job set | seed | phase | status | ifail | iterations | evaluations | gradient evaluations | E | E_obj |")
    print("|---|---|---|---|---:|---|---|---|---:|---:|---:|---:|---:|")
    for key in sorted(res["per_run"]):
        cfg, arm, run_id, js, seed, phase = key
        r = res["per_run"][key]
        print(f"| {SHORT[cfg]} | {arm} | {run_id} | {js} | {seed} | {phase} | {r['status']} | {r['ifail']} | {r['iterations']} | {r['n_eval']} | {r['n_grad']} | {r['E']} | {r['E_obj']} |")

    # E per (cfg, arm, run_id), main job set and with st_more
    def E(cfg, arm, run_id, js=job_sets) -> tuple[int, int, int]:
        e = eo = n = 0
        for (c, a, r, j, _s, ph), row in res["per_run"].items():
            if c == cfg and a == arm and r == run_id and j in js and ph == "B":
                e += row["E"]; eo += row["E_obj"]; n += row["n_grad"]
        return e, eo, n

    print("\n## 2. The primary rate E, gradient evaluations, phase B (census run IDs)\n")
    print("| configuration | arm | run ID | gradient evaluations | E | E_obj |")
    print("|---|---|---|---:|---|---|")
    Erate: dict[tuple, float | None] = {}
    for cfg in CONFIGS:
        for arm in ("B0", "B1", "B2"):
            for run_id in RUN_IDS[:2]:
                e, eo, n = E(cfg, arm, run_id)
                if n == 0:
                    continue
                Erate[(cfg, arm, run_id)] = e / n
                print(f"| {SHORT[cfg]} | {arm} | {run_id} | {n} | {share(e, n)} | {share(eo, n)} |")

    print("\n## 3. Stops, per block (S1–S4)\n")
    for phase, kinds in (("B", ("gradient", "function", "reconcile", "other")), ("A", ("evaluation",))):
        for run_id in RUN_IDS:
            ts = test_set_of(run_id)
            rows = sorted(k for k in res["cells"] if k[2] == run_id and k[3] == phase)
            if not rows:
                continue
            print(f"\n### phase {phase}, {run_id}\n")
            if ts == "census":
                print("| cfg | arm | kind | block | stops | out-of-test max at stop (S1) | open (S1) | ≥10τ | one-sweep stops (S2) | open among one-sweep | worst open read: later / obj / either (S4) | any open read: later / obj / either (S4) |")
                print("|---|---|---|---|---:|---|---|---|---|---|---|---|")
            else:
                print("| cfg | arm | kind | block | stops | census part at stop (S6) | extra sweeps after census closed: med / max (S6) | non-census max at k* (S6) | open at k* |")
                print("|---|---|---|---|---:|---|---|---|---|")
            for key in rows:
                cfg, arm, _r, _p, kind, label = key
                if kind not in kinds:
                    continue
                c = res["cells"][key]
                n = c["n_stops"]
                if ts == "census":
                    o = c["out_open"]
                    print(f"| {SHORT[cfg]} | {arm} | {kind} | {label} | {n} | {stats_line(c['out_max'])} | {share(o, n)} | {share(c['out_10tau'], n)} | {share(c['n_one'], n)} | {share(c['one_open'], c['n_one'])} | {c['open_worst_down']} / {c['open_worst_obj']} / {c['open_worst_either']} of {o} | {c['open_any_down']} / {c['open_any_obj']} / {c['open_any_either']} of {o} |")
                else:
                    ex = c["kstar_extra"]
                    exs = "—" if not ex else f"{statistics.median(ex):g} / {max(ex)} (≥1 extra: {sum(1 for x in ex if x >= 1)}/{len(ex)})"
                    approx = " (approx.)" if label in ("M2", "M3") else ""
                    print(f"| {SHORT[cfg]} | {arm} | {kind} | {label} | {n} | {stats_line(c['census_at_stop'])} | {exs}{approx} | {stats_line(c['nc_at_kstar'])} | {share(c['nc_at_kstar_open'], c['n_mirror'])} |")

    print("\n## 4. Worst components (S3), phase B gradient evaluations\n")
    print("| cfg | arm | run ID | block | in the test, at the stop | out of the test, non-zero | out of the test, open | most frequent open out-of-test names |")
    print("|---|---|---|---|---|---|---|---|")
    for key in sorted(res["cells"]):
        cfg, arm, run_id, phase, kind, label = key
        if phase != "B" or kind != "gradient":
            continue
        c = res["cells"][key]
        print(f"| {SHORT[cfg]} | {arm} | {run_id} | {label} | {top(c['test_argmax'])} | {top(c['out_argmax_nonzero'])} | {top(c['out_argmax_open'])} | {top(c['open_names'], 5)} |")

    print("\n## 5. Finite-difference pairs (S5), phase B\n")
    print("| cfg | arm | run ID | pairs | total sweeps differ | per block: differ / pairs |")
    print("|---|---|---|---:|---|---|")
    for key in sorted(res["pairs"]):
        cfg, arm, run_id = key
        p = res["pairs"][key]
        blocks = ", ".join(f"{b} {p['differ'][b]}/{p['blocks'][b]}" for b in sorted(p["blocks"]))
        print(f"| {SHORT[cfg]} | {arm} | {run_id} | {p['n']} | {share(p['differ_total'], p['n'])} | {blocks} |")

    print("\n## 6. The declaration's verdict\n")
    def pooled(cfg, arm, run_id):
        n = o = d = 0
        for (c, a, r, ph, k, _l), cell in res["cells"].items():
            if c == cfg and a == arm and r == run_id and ph == "B" and k == "gradient":
                n += cell["n_stops"]; o += cell["out_open"]
                d += cell["open_any_either"]
        return n, o, d
    verdicts = []
    for cfg, run_id, arm in DISTURBED:
        n, o, d = pooled(cfg, arm, run_id)
        if arm == "B0":  # flat: downstream is the objective and constraints alone
            d = sum(cell["open_any_obj"] for (c, a, r, ph, k, _l), cell in res["cells"].items()
                    if c == cfg and a == arm and r == run_id and ph == "B" and k == "gradient")
        c1 = n > 0 and o / n >= C1_SHARE
        c2 = o > 0 and d / o >= C2_SHARE
        verdicts.append((c1, c2))
        print(f"- D case {SHORT[cfg]} {run_id} {arm}: C1 open stops {share(o, n)} (needs ≥ {C1_SHARE}) → {'holds' if c1 else 'FAILS'}; "
              f"C2 open stops with an open component read downstream {share(d, o)} (needs ≥ {C2_SHARE}) → {'holds' if c2 else 'FAILS'}")
    comps = []
    for run_id in RUN_IDS[:2]:
        for arm in ("B0", "B2"):
            comps.append((f"T1 st/tok {arm} {run_id}", Erate.get(("st_regression", arm, run_id)), Erate.get(("large_tokamak_nof", arm, run_id))))
    comps.append(("T2 st census 1e-8 B2/B0", Erate.get(("st_regression", "B2", "census_tau1e-08")), Erate.get(("st_regression", "B0", "census_tau1e-08"))))
    comps.append(("T3 st B0 census 1e-6/1e-8", Erate.get(("st_regression", "B0", "census_tau1e-06")), Erate.get(("st_regression", "B0", "census_tau1e-08"))))
    disc_all = True
    for name, dside, uside in comps:
        if dside is None or uside is None:
            print(f"- {name}: not computable ({dside}, {uside})")
            disc_all = False
            continue
        disc = dside > 0 and dside >= C3_FACTOR * uside
        disc_all = disc_all and disc
        ratio = "inf" if uside == 0 and dside > 0 else ("—" if uside == 0 else f"{dside / uside:.2f}")
        print(f"- {name}: E {dside:.4f} against {uside:.4f}, ratio {ratio} → {'discriminates' if disc else 'does NOT discriminate'}")
    refuted = [i for i, (c1, c2) in enumerate(verdicts) if not (c1 and c2)]
    if refuted:
        print(f"\n**Verdict: refuted** in {len(refuted)} of {len(verdicts)} D case(s) (C1 or C2 fails there).")
    elif disc_all:
        print("\n**Verdict: supported** — C1 and C2 hold in every D case and every comparison of C3 discriminates.")
    else:
        print("\n**Verdict: present but not shown to be the cause** — C1 and C2 hold in every D case; C3 does not discriminate in every comparison.")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--runs", type=Path, default=HERE / "runs")
    ap.add_argument("--out", type=Path, default=None, help="also write the printed tables here")
    ap.add_argument("--job-sets", default="sweep_residual,sweep_residual_st_more")
    args = ap.parse_args(argv)
    job_sets = tuple(s for s in args.job_sets.split(",") if s)
    buf = io.StringIO()
    with redirect_stdout(buf):
        report(args.runs, job_sets)
    text = buf.getvalue()
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
