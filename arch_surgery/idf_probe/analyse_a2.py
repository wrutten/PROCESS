#!/usr/bin/env python
"""A2 (module-convergence) analysis: gates, per-module sweep counts, couplers.

Reads ``runs/a2/<scenario>/<arm>/{metrics.json,probe_modules.json}`` written by
``run_a2.py`` and produces:

* **gate N** -- neutrality of the Stage-1 instrument: ``control``, ``baseline``
  and ``modules`` must give identical results and identical sweep counts.
* **per-module convergence** -- ``S_1``, ``S_2``, ``S_3`` against ``S_global``,
  with the censoring rate, and the laggard.
* **the Stage-1 gate** -- predicted saving of the partition, computed from
  exact sweep counts under two weightings: DSM node counts (the plan's own
  arithmetic) and measured per-node cost share.
* **the coupler census** -- every cross-module back edge observed at run time.

Usage:  python analyse_a2.py [--runs DIR] [--json OUT]
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent

SCENARIOS = [
    "large_tokamak_nof",
    "low_aspect_ratio_DEMO",
    "st_regression",
    "large_tokamak_eval",
]
ARMS = ["control", "baseline", "modules"]

#: Collapsed-DSM node counts (decision D8).  M1 = rows 4 and 6-28,
#: M2 = rows 5 and 29-37, M3 = rows 40-51, ``Pulse`` = row 39,
#: feed-forward = rows 38 and 52-55.  Rows 1-3 are the driver stack and row 56
#: is the output node; neither runs inside a sweep.
NODE_COUNTS = {"M1": 24, "M2": 10, "M3": 12, "PULSE": 1, "FF": 5}
N_ALL = sum(NODE_COUNTS.values())  # 52


def load(runs: Path, scenario: str, arm: str) -> dict | None:
    p = runs / scenario / arm / "metrics.json"
    return json.loads(p.read_text()) if p.exists() else None


def load_modules(runs: Path, scenario: str, arm: str = "modules") -> dict | None:
    p = runs / scenario / arm / "probe_modules.json"
    return json.loads(p.read_text()) if p.exists() else None


# --------------------------------------------------------------------------
# Gate N -- neutrality of the Stage-1 instrument
# --------------------------------------------------------------------------


def _signature(m: dict) -> dict:
    exact = m.get("exact") or {}
    raw = dict((m.get("mfile") or {}).get("raw") or {})
    return {
        "norm_objf": exact.get("norm_objf"),
        "xcs": exact.get("xcs"),
        "conf_l2": exact.get("conf_l2"),
        "sqsumsq": exact.get("sqsumsq"),
        "mfile_raw": raw,
    }


def _mfile_lines(runs: Path, scenario: str, arm: str) -> list[str] | None:
    d = runs / scenario / arm
    cands = sorted(d.glob("*MFILE.DAT"))
    if not cands:
        return None
    # The run-metadata header: wall-clock date/time, user, host paths, git
    # identity and measured runtime.  Everything else -- ~16,000-18,700 lines
    # of physics -- must be byte-identical across the arms.
    skip = (
        "fileprefix",
        "process_runtime",
        "date",
        "time",
        "username",
        "procver",
        "tagno",
        "branch_name",
        "commsg",
    )
    return [
        ln
        for ln in cands[0].read_text().splitlines()
        if not any(f"({k})" in ln for k in skip)
    ]


def _sweep_shape(m: dict) -> dict:
    p = m.get("probe") or {}
    return {
        "sweeps_total": p.get("sweeps_total"),
        "call_models_total": p.get("call_models_total"),
        "by_phase": {
            k: v.get("hist") for k, v in (p.get("by_phase") or {}).items()
        },
        "n_retries": p.get("n_retries"),
    }


def gate_neutrality(runs: Path, scenarios) -> dict:
    out = {}
    for s in scenarios:
        arms = {a: load(runs, s, a) for a in ARMS}
        if any(v is None for v in arms.values()):
            out[s] = {"status": "MISSING"}
            continue
        if any(v["status"] != "ok" for v in arms.values()):
            out[s] = {
                "status": "NOT APPLICABLE (run crashed)",
                "run_status": {a: v["status"] for a, v in arms.items()},
            }
            continue
        sig = {a: _signature(v) for a, v in arms.items()}
        lines = {a: _mfile_lines(runs, s, a) for a in ARMS}
        diffs = {}
        for a in ("baseline", "modules"):
            diffs[f"control_vs_{a}_signature_fields"] = [
                k for k in sig["control"] if sig["control"][k] != sig[a][k]
            ]
            la, lb = lines["control"], lines[a]
            diffs[f"control_vs_{a}_mfile_differing_lines"] = (
                None
                if la is None or lb is None
                else sum(1 for x, y in zip(la, lb, strict=False) if x != y)
                + abs(len(la) - len(lb))
            )
        shapes = {a: _sweep_shape(arms[a]) for a in ("baseline", "modules")}
        diffs["baseline_vs_modules_sweep_shape_identical"] = (
            shapes["baseline"] == shapes["modules"]
        )
        ok = (
            not diffs["control_vs_baseline_signature_fields"]
            and not diffs["control_vs_modules_signature_fields"]
            and diffs["control_vs_baseline_mfile_differing_lines"] == 0
            and diffs["control_vs_modules_mfile_differing_lines"] == 0
            and diffs["baseline_vs_modules_sweep_shape_identical"]
        )
        out[s] = {
            "status": "PASS" if ok else "FAIL",
            "mfile_lines_compared": len(lines["control"] or []),
            **diffs,
            "ifail": (arms["control"].get("mfile") or {}).get("ifail"),
        }
    return out


# --------------------------------------------------------------------------
# Per-module convergence
# --------------------------------------------------------------------------


def module_convergence(mod: dict) -> dict:
    calls = mod["calls"]
    mods = ("M1", "M2", "M3")
    n = len(calls)
    sg = [c["s_global"] for c in calls]

    res: dict = {
        "n_call_models": n,
        "sweeps_in_call_models": sum(sg),
        "S_global_mean": statistics.fmean(sg) if sg else None,
        "S_global_hist": _hist(sg),
    }
    for m in mods:
        vals = [c[m] for c in calls]
        cens = [c["s_global"] for c, v in zip(calls, vals, strict=True) if v is None]
        obs = [v for v in vals if v is not None]
        res[m] = {
            "censored": len(cens),
            "censored_frac": len(cens) / n if n else None,
            "S_mean_optimistic": (
                statistics.fmean(obs + cens) if (obs or cens) else None
            ),
            "S_mean_pessimistic": (
                statistics.fmean(obs + [c + 1 for c in cens]) if (obs or cens) else None
            ),
            "S_hist_observed": _hist(obs),
        }
    # who is last?
    last = {m: 0 for m in mods}
    for c in calls:
        eff = {m: (c[m] if c[m] is not None else c["s_global"] + 1) for m in mods}
        mx = max(eff.values())
        for m in mods:
            if eff[m] == mx:
                last[m] += 1
    res["times_module_is_last_or_joint_last"] = last
    return res


def _hist(vals) -> dict:
    h: dict = {}
    for v in vals:
        h[v] = h.get(v, 0) + 1
    return {str(k): h[k] for k in sorted(h)}


# --------------------------------------------------------------------------
# The Stage-1 gate
# --------------------------------------------------------------------------


def cost_weights(mod: dict) -> dict:
    """Measured cost share per module, in seconds inside each node."""
    w: dict = {"M1": 0.0, "M2": 0.0, "M3": 0.0, "PULSE": 0.0, "FF": 0.0, "X": 0.0}
    for nd in mod["nodes"]:
        w[nd["module"]] = w.get(nd["module"], 0.0) + nd["seconds"]
    total = sum(v for k, v in w.items() if k != "X")
    return {
        "seconds": w,
        "share": {k: (v / total if total else 0.0) for k, v in w.items()},
        "total_seconds": total,
    }


def gate(mod: dict, weights: dict, label: str, pessimistic: bool = False) -> dict:
    """Predicted saving from the partition, under a given node weighting.

    ``weights`` maps M1/M2/M3/PULSE/FF to a cost per pass.  Three costs are
    formed for each ``call_models``:

    ``C0``       today: every node re-runs on every sweep
    ``C_hoist``  the feed-forward hoist alone (candidate E1): the modules still
                 re-run on every sweep, the feed-forward tail runs once
    ``C_part``   the full partition: each module iterates alone, tail once
    """
    c0 = ch = cp = 0.0
    wm = weights
    w_mods = wm["M1"] + wm["M2"] + wm["M3"]
    w_tail = wm["PULSE"] + wm["FF"]
    for c in mod["calls"]:
        s = c["s_global"]
        s_i = {}
        for m in ("M1", "M2", "M3"):
            v = c[m]
            s_i[m] = v if v is not None else (s + 1 if pessimistic else s)
        c0 += s * (w_mods + w_tail)
        ch += s * w_mods + w_tail
        cp += sum(s_i[m] * wm[m] for m in ("M1", "M2", "M3")) + w_tail
    return {
        "weighting": label,
        "censored_treated_as": "S_global + 1" if pessimistic else "S_global",
        "C0": c0,
        "C_hoist": ch,
        "C_partition": cp,
        "saving_total_pct": 100 * (1 - cp / c0) if c0 else None,
        "saving_from_hoist_pct": 100 * (1 - ch / c0) if c0 else None,
        "saving_from_partition_pct": 100 * (ch - cp) / c0 if c0 else None,
    }


# --------------------------------------------------------------------------
# Couplers
# --------------------------------------------------------------------------


def couplers(mod: dict) -> dict:
    back = mod["back_edges"]
    by_field: dict = {}
    for e in back:
        f = by_field.setdefault(
            e["field"],
            {
                "field": e["field"],
                "ever_changed": e["field_ever_changed"],
                "edges": [],
            },
        )
        f["changes_between_sweeps"] = e["field_changed_between_sweeps"]
        f["edges"].append(
            f"{e['writer']}({e['writer_module']}) -> {e['reader']}({e['reader_module']})"
        )
    pulse_writes = mod["writes_by_node"].get("pulse", [])
    live = sorted({e["field"] for e in back if e["field_changed_between_sweeps"]})
    return {
        "n_back_edges": len(back),
        "back_edge_fields": sorted(by_field),
        "back_edge_fields_live": live,
        "k_live": len(live),
        "detail": [by_field[k] for k in sorted(by_field)],
        "pulse_writes": pulse_writes,
        "n_pulse_writes": len(pulse_writes),
        "read_sweeps": mod["read_sweeps"],
        "sweeps_total": mod["sweeps_total"],
        "output_path_calls_refused": mod.get("output_path_calls_refused", {}),
    }


# --------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=str(HERE / "runs" / "a2"))
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    runs = Path(args.runs)

    report: dict = {"gate_neutrality": gate_neutrality(runs, args.scenarios)}
    print("== Gate N: instrument neutrality (control / baseline / modules) ==")
    for s, r in report["gate_neutrality"].items():
        print(f"  {s:24s} {r['status']}  {r}")

    report["scenarios"] = {}
    for s in args.scenarios:
        mod = load_modules(runs, s)
        if mod is None:
            continue
        w = cost_weights(mod)
        conv = module_convergence(mod)
        entry = {
            "convergence": conv,
            "cost_weights": w,
            "gates": [
                gate(mod, NODE_COUNTS, "dsm_node_counts"),
                gate(mod, NODE_COUNTS, "dsm_node_counts", pessimistic=True),
                gate(mod, w["seconds"], "measured_cost"),
                gate(mod, w["seconds"], "measured_cost", pessimistic=True),
            ],
            "couplers": couplers(mod),
            "nodes": mod["nodes"],
            "late_changers": mod["late_changers"][:30],
            "edge_growth_tail": mod["edge_growth"][-5:],
        }
        report["scenarios"][s] = entry

        print(f"\n== {s} ==")
        print(
            f"  call_models {conv['n_call_models']}, sweeps {conv['sweeps_in_call_models']}, "
            f"S_global mean {conv['S_global_mean']:.3f} {conv['S_global_hist']}"
        )
        for m in ("M1", "M2", "M3"):
            c = conv[m]
            print(
                f"  {m}: S_mean {c['S_mean_optimistic']:.3f}"
                f"..{c['S_mean_pessimistic']:.3f}  censored "
                f"{c['censored']}/{conv['n_call_models']} "
                f"({100 * c['censored_frac']:.1f}%)  hist {c['S_hist_observed']}"
            )
        print(f"  last-to-settle: {conv['times_module_is_last_or_joint_last']}")
        print(
            "  cost share: "
            + ", ".join(f"{k} {100 * v:.1f}%" for k, v in w["share"].items())
        )
        for g in entry["gates"]:
            print(
                f"  gate[{g['weighting']:18s} cens={g['censored_treated_as']:12s}] "
                f"total {g['saving_total_pct']:6.2f}%  "
                f"hoist {g['saving_from_hoist_pct']:6.2f}%  "
                f"partition {g['saving_from_partition_pct']:6.2f}%"
            )
        cp = entry["couplers"]
        print(
            f"  back edges: {cp['n_back_edges']} over fields {cp['back_edge_fields']}"
        )
        print(f"  LIVE back-edge fields (k = {cp['k_live']}): {cp['back_edge_fields_live']}")
        print(f"  Pulse writes ({cp['n_pulse_writes']}): {cp['pulse_writes']}")

    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
