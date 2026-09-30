#!/usr/bin/env python
"""Loop sweeps and node calls of one evaluation, down a tolerance ladder, against PROCESS's own loop.

Task A104 (st-stall-mechanism), measurement **M0** -- the user's key check: at the
tighter tolerances, is the flat control still comparable to the reference arm in
the number of loop sweeps it needs?

What is run (``--press``)
-------------------------
Per configuration, from five entries, one evaluation each (the V5 harness's
warmed evaluation child through its pool, :mod:`loop_runs`):

* **displaced** -- the campaign's own phase A entries of seeds 1, 2, 3: the
  campaign's entry reference exit state (``runs/campaign/entry_references/<c>/
  y_exit.json``, read only) displaced by δ = 0.10 on the seed's stream, the pinned
  arms' burn time on the same stream;
* **stencil** -- an entry that mimics an optimiser evaluation: the same reference
  exit state (converged at the input file's design point), with one iteration
  variable multiplied by ``1 + epsfcn`` (the harness's stencil regime), columns
  ``0`` and ``n - 1``.

Loops: the reference ``AR`` (PROCESS's loop: objective and constraints agree
between two successive full sweeps to a relative 1e-6, two to ten sweeps), once;
under the **census** test set the flat ``A0``, on the pulsed configurations the
flat ``A1`` (burn time owned by a constant), and the partitioned ``A2`` at
τ = 1e-8 … 1e-14; under the **whole write set** (``write_set``, V4's predicate,
D39's fallback) the same arms at τ = 1e-6, 1e-8, 1e-10.

What is read (``--tables``)
---------------------------
Per cell (configuration, entry kind, loop): node calls and sweeps per block of the
measured evaluation, averaged over the entries of the kind; how each block loop
ended, from the driver's block trace (``tau`` -- the last sweep's largest scaled
change on the test set was below τ and not zero; ``bit-identical`` -- it was
exactly zero; ``cap`` -- the block reached ``INNER_CAP`` = 20 sweeps and the run
raised); the exit audit's whole-state residual.  Then the ratios of mean node
calls: flat over reference (``A0/AR``; ``A1/AR`` beside on the pulsed
configurations), partitioned over flat (``A2/A1`` pulsed, ``A2/A0`` on st, the
paper's pairing, D34), partitioned over reference (``A2/AR``).

**Comparable** (declared before any count was read): the flat control's mean node
calls per evaluation within 10 % of the reference's, i.e. ``A0/AR`` ≤ 1.10.

A reproduction check: the displaced census 1e-8 cells are the campaign's own jobs
(same entry, same τ; only the timers and the block trace differ, neither of which
moves a count, gate GC); each is compared with the campaign record -- node calls,
sweeps and the objective to the bit.

Usage::

    PYTHONDONTWRITEBYTECODE=1 python loop_sweeps_against_reference.py --press [--configuration st_regression]
    PYTHONDONTWRITEBYTECODE=1 python loop_sweeps_against_reference.py --tables [--json out.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from loop_runs import (
    CAMPAIGN_RUNS,
    CONFIGURATIONS,
    EPSVMC,
    REFERENCE,
    ROOT,
    SHORT,
    Loop,
    campaign_for,
    config_of,
    epsvmc_of,
    evaluation_job,
    mean,
    press,
    read_evaluation,
    records_mod,
)
from harness.gates import reproduction as reproduction_mod  # noqa: E402

LADDER_ROOT = ROOT / "loop_sweeps_ladder"
CENSUS_TAUS = (1e-8, 1e-9, 1e-10, 1e-11, 1e-12, 1e-13, 1e-14)
WRITE_SET_TAUS = (1e-6, 1e-8, 1e-10)
DISPLACED_SEEDS = (1, 2, 3)
DELTA = 0.10
COMPARABLE = 1.10
#: τ = epsvmc × epsfcn (epsfcn = 1e-3 on all three), and one decade tighter.
RULE_TAU = {"large_tokamak_nof": 1e-10, "low_aspect_ratio_DEMO": 1e-11, "st_regression": 1e-12}


def pulsed(config_name: str) -> bool:
    return config_name != "st_regression"


def loops_for(config_name: str) -> list[Loop]:
    arms = ["A0", "A1", "A2"] if pulsed(config_name) else ["A0", "A2"]
    out = [REFERENCE]
    out += [Loop(a, "census", t) for t in CENSUS_TAUS for a in arms]
    out += [Loop(a, "write_set", t) for t in WRITE_SET_TAUS for a in arms]
    return out


def reference_record(config_name: str) -> dict:
    d = CAMPAIGN_RUNS / "entry_references" / config_name
    rec = records_mod.read(d)
    if rec.get("status") != "ok":
        raise SystemExit(f"{config_name}: the campaign's entry reference is not ok")
    return {"dir": d, "snapshot": d / "y_exit.json", "t_plant_pulse_burn_hex": rec.get("t_plant_pulse_burn_hex"), "nvar": rec.get("nvar")}


def entries_for(config_name: str) -> list[dict]:
    ref = reference_record(config_name)
    n = int(ref["nvar"])
    out = [{"kind": "displaced", "name": f"seed{s:03d}", "seed": s} for s in DISPLACED_SEEDS]
    out += [{"kind": "stencil", "name": f"stencil{c:02d}+", "column": c} for c in (0, n - 1)]
    return out


def outdir_for(config_name: str, entry: dict, loop: Loop) -> Path:
    return LADDER_ROOT / config_name / entry["name"] / loop.slug


def jobs(config_names) -> dict[Loop, list]:
    groups: dict[Loop, list] = {}
    for name in config_names:
        epsvmc_of(name)
        ref = reference_record(name)
        for loop in loops_for(name):
            campaign = campaign_for(loop, LADDER_ROOT)
            config = config_of(campaign, name)
            for entry in entries_for(name):
                if entry["kind"] == "displaced":
                    pin = reproduction_mod.entry_pin(config, loop.arm, ref, seed=entry["seed"], delta=DELTA)
                    job = evaluation_job(
                        campaign, config, loop, outdir_for(name, entry, loop),
                        seed=entry["seed"], regime="perturbed", delta=DELTA,
                        entry_state=ref["snapshot"], pin_hex=pin,
                    )
                else:
                    pin = reproduction_mod.entry_pin(config, loop.arm, ref, seed=0, delta=None)
                    job = evaluation_job(
                        campaign, config, loop, outdir_for(name, entry, loop),
                        seed=0, regime="stencil", delta=None,
                        entry_state=ref["snapshot"], stencil_column=entry["column"],
                        stencil_sign=1, pin_hex=pin,
                    )
                groups.setdefault(loop, []).append(job)
    return groups


# --------------------------------------------------------------------------
# tables
# --------------------------------------------------------------------------


def fmt(v, spec=".3g"):
    if v is None:
        return "—"
    if isinstance(v, float):
        return format(v, spec)
    return str(v)


def ratio(a, b):
    return None if a is None or b in (None, 0) else a / b


def summarise(config_name: str) -> dict:
    cells: dict = {}
    for loop in loops_for(config_name):
        for entry in entries_for(config_name):
            r = read_evaluation(outdir_for(config_name, entry, loop), loop)
            cells.setdefault(loop.label, {})[entry["name"]] = {**r, "entry_kind": entry["kind"]}
    return cells


def cell_stats(rows: list[dict]) -> dict:
    ok = [r for r in rows if r.get("status") == "ok"]
    ended: dict[str, int] = {}
    for r in rows:
        ended[r.get("ended") or r.get("status")] = ended.get(r.get("ended") or r.get("status"), 0) + 1
    blocks: dict[str, list] = {}
    block_end: dict[str, dict[str, int]] = {}
    for r in rows:
        for b, n in (r.get("per_block") or {}).items():
            blocks.setdefault(b, []).append(n)
        for b, e in (r.get("ended_per_block") or {}).items():
            block_end.setdefault(b, {})
            block_end[b][e] = block_end[b].get(e, 0) + 1
    return {
        "n": len(rows),
        "n_ok": len(ok),
        "node_calls_mean": mean([r.get("node_calls") for r in rows]) if len(ok) == len(rows) else None,
        "node_calls_mean_all": mean([r.get("node_calls") for r in rows]),
        "sweeps_per_block_mean": {b: mean(v) for b, v in blocks.items()},
        "ended": ended,
        "ended_per_block": block_end,
        "audit_max": max((r.get("audit_residual_max") or 0.0) for r in ok) if ok else None,
        "heads": sorted({r.get("tree_git_head") for r in rows if r.get("tree_git_head")}),
    }


def reproduction_check(config_name: str, cells: dict) -> list[str]:
    lines = []
    for arm in (["AR", "A0", "A1", "A2"] if pulsed(config_name) else ["AR", "A0", "A2"]):
        label = "AR" if arm == "AR" else f"{arm} census 1e-08"
        for s in DISPLACED_SEEDS:
            mine = cells[label][f"seed{s:03d}"]
            camp = records_mod.read(CAMPAIGN_RUNS / "evaluation" / config_name / arm / f"seed{s:03d}")
            same = (
                camp.get("node_calls_single_eval") == mine.get("node_calls")
                and camp.get("n_model_calls_sweeps") == mine.get("sweeps")
                and (camp.get("exact") or {}).get("objf") == (None if mine.get("objf") is None else float(mine["objf"]).hex())
            )
            lines.append(f"{arm} seed{s:03d}: {'identical' if same else 'DIFFERENT'} (node calls {mine.get('node_calls')} vs {camp.get('node_calls_single_eval')})")
    return lines


def campaign_context(config_name: str) -> list[str]:
    """The campaign's own phase A records at census 1e-8, all 25 seeds: context and a check."""
    import statistics  # noqa: PLC0415

    rows = []
    for arm in (["AR", "A0", "A1", "A2"] if pulsed(config_name) else ["AR", "A0", "A2"]):
        recs = [records_mod.read(CAMPAIGN_RUNS / "evaluation" / config_name / arm / f"seed{s:03d}") for s in range(1, 26)]
        ok = [r for r in recs if r.get("status") == "ok"]
        sweeps = [r.get("n_model_calls_sweeps") for r in ok]
        nodes = [r.get("node_calls_single_eval") for r in ok]
        audit = [(r.get("exit_audit") or {}).get("residual_max") for r in ok]
        rows.append(
            f"| {arm} | {len(ok)} of {len(recs)} | {mean(sweeps):.2f} | {mean(nodes):.1f} | "
            f"{statistics.median(audit):.1e} [{min(audit):.1e}, {max(audit):.1e}] |"
        )
    return rows


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--press", action="store_true")
    p.add_argument("--tables", action="store_true")
    p.add_argument("--configuration", action="append", default=None)
    p.add_argument("--json", default=None)
    args = p.parse_args(argv)
    names = tuple(args.configuration or CONFIGURATIONS)
    if args.press:
        press(jobs(names), LADDER_ROOT)
    if not args.tables:
        return 0
    result = {}
    for name in names:
        cells = summarise(name)
        kinds = ("displaced", "stencil")
        stats = {
            label: {k: cell_stats([r for r in per.values() if r["entry_kind"] == k]) for k in kinds}
            for label, per in cells.items()
        }
        result[name] = {"stats": stats, "cells": cells}
        s = SHORT[name]
        print(f"\n## {name} ({s}); epsvmc {EPSVMC[name]:g}; rule τ = epsvmc × epsfcn = {RULE_TAU[name]:g}\n")
        heads = sorted({h for st in stats.values() for k in kinds for h in st[k]["heads"]})
        print(f"records made at: {heads}\n")
        print("Reproduction of the campaign's displaced census 1e-8 records: " + "; ".join(reproduction_check(name, cells)) + "\n")
        print(f"The campaign's own phase A records ({s}, census 1e-8, displaced seeds 1-25; context):\n")
        print("| arm | ok | sweeps per evaluation (mean; dispatch sweeps, the partitioned arm's once-execution included) | node calls (mean) | exit audit, whole state: median [min, max] |")
        print("|---|---|---|---|---|")
        for row in campaign_context(name):
            print(row)
        print()
        for k in kinds:
            n_entries = next(iter(stats.values()))[k]["n"]
            print(f"### {s}, {k} entries ({n_entries} per cell)\n")
            print("| loop | node calls (mean) | sweeps per block (mean) | how the loops ended (runs) | block ends | exit audit max (whole state) |")
            print("|---|---|---|---|---|---|")
            for label, st in stats.items():
                c = st[k]
                sw = ", ".join(f"{b} {fmt(v, '.2f')}" for b, v in c["sweeps_per_block_mean"].items())
                be = "; ".join(f"{b}: " + ", ".join(f"{e} {n}" for e, n in sorted(d.items())) for b, d in c["ended_per_block"].items())
                en = ", ".join(f"{e} {n}" for e, n in sorted(c["ended"].items()))
                nc = c["node_calls_mean"] if c["node_calls_mean"] is not None else c["node_calls_mean_all"]
                n_missing = c["ended"].get("no_record", 0)
                n_raised = c["n"] - c["n_ok"] - n_missing
                flag = ""
                if n_raised:
                    flag += f" ({n_raised} raised at the cap; mean over all, the raised at the node calls they spent)"
                if n_missing:
                    flag += f" ({n_missing} not made)"
                print(f"| {label} | {fmt(nc, '.1f')}{flag} | {sw} | {en} | {be} | {fmt(c['audit_max'], '.1e')} |")
            print()
            # the ratios
            ref = stats["AR"][k]["node_calls_mean"]
            print(f"#### {s}, {k}: ratios of mean node calls per evaluation (comparable: A0/AR ≤ {COMPARABLE})\n")
            flat_pair = "A1" if pulsed(name) else "A0"
            head = "| test set | τ | A0/AR | " + ("A1/AR | " if pulsed(name) else "") + f"A2/{flat_pair} | A2/AR | A0 comparable to AR |"
            print(head)
            print("|" + "---|" * (head.count("|") - 1))
            for ts, taus in (("census", (1e-8, 1e-9, 1e-10, 1e-11, 1e-12, 1e-13, 1e-14)), ("write_set", (1e-6, 1e-8, 1e-10))):
                for t in taus:
                    def m(arm):
                        c = stats.get(f"{arm} {ts} {t:.0e}", {}).get(k)
                        return None if c is None else c["node_calls_mean"]
                    a0, a1, a2 = m("A0"), m("A1") if pulsed(name) else None, m("A2")
                    r0 = ratio(a0, ref)
                    mark = " (rule)" if ts == "census" and t == RULE_TAU[name] else (" (rule/10)" if ts == "census" and t == RULE_TAU[name] / 10 else "")
                    row = f"| {ts} | {t:.0e}{mark} | {fmt(r0, '.2f')} | "
                    if pulsed(name):
                        row += f"{fmt(ratio(a1, ref), '.2f')} | "
                    row += f"{fmt(ratio(a2, a1 if pulsed(name) else a0), '.2f')} | {fmt(ratio(a2, ref), '.2f')} | "
                    row += ("—" if r0 is None else ("yes" if r0 <= COMPARABLE else "no")) + " |"
                    print(row)
            print()
        print(f"#### {s}: the largest scaled change on each block's test set after every sweep (block trace), census set, per entry\n")
        print("| loop | entry | per block: change after sweep 1, 2, ... |")
        print("|---|---|---|")
        for t in (1e-8, 1e-12):
            for arm in (["A0", "A1", "A2"] if pulsed(name) else ["A0", "A2"]):
                label = f"{arm} census {t:.0e}"
                for ename, r in cells[label].items():
                    per = r.get("residual_per_sweep") or {}
                    txt = "; ".join(f"{b}: " + ", ".join(f"{v:.1e}" for v in vals) for b, vals in per.items())
                    print(f"| {label} | {ename} | {txt} |")
        print()
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(result, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
