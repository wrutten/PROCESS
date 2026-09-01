#!/usr/bin/env python
"""Render the Phase A analysis JSON as the tables the report quotes.

Counts and bit-comparisons only.  Wall clock appears once, labelled context.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent / "idf_probe" / "runs" / "a18"

SCEN = [
    "large_tokamak_nof",
    "low_aspect_ratio_DEMO",
    "st_regression",
    "large_tokamak_eval",
]


def _g(d, *ks, default=None):
    for k in ks:
        if d is None:
            return default
        d = d.get(k) if isinstance(d, dict) else None
    return default if d is None else d


def magnitudes(runs: Path) -> None:
    print("\n## Magnitude distribution of objf and the constraint vector "
          "(the idempotence loop's own set)\n")
    hdr = ["scenario", "quantity", "n", "<=1e-8", "1e-8..1e-6", "1e-6..1e-4",
           "1e-4..1e-2", "1e-2..1", "1..1e3", ">1e3", "zero", "nan/inf"]
    print("| " + " | ".join(hdr) + " |")
    print("|" + "---|" * len(hdr))
    for s in SCEN:
        p = runs / s / "harvest" / "probe_modules.json"
        if not p.exists():
            continue
        m = json.loads(p.read_text())["harvest"]["magnitudes"]
        for q in ("objf", "conf"):
            h = m[q]
            row = [
                s, q, h["total"], h["<1e-8"], h["1e-8..1e-6"], h["1e-6..1e-4"],
                h["1e-4..1e-2"], h["1e-2..1"], h["1..1e3"],
                h["1e3..1e6"] + h[">1e6"], h["zero"], h["nan"] + h["inf"],
            ]
            print("| " + " | ".join(str(x) for x in row) + " |")
    print("\n(Bin membership is `|v| <= edge`. `zero` is counted separately "
          "from every bin.)\n")


def drop_census(rep: dict) -> None:
    print("\n## Drop census -- reported before any ratio\n")
    hdr = ["scenario", "tau", "hoist", "points", "R", "A0", "A0f", "A1",
           "pairwise-complete", "dropped"]
    print("| " + " | ".join(hdr) + " |")
    print("|" + "---|" * len(hdr))
    for key, r in sorted(rep.get("replays", {}).items()):
        c = r["drop_census"]
        row = [key.split("/")[0], f"{r['tau']:g}", int(r["hoist"]),
               r["n_points"]]
        for a in ("R", "A0", "A0f", "A1"):
            row.append(
                f"{c[a]['n_converged']}/{c[a]['n_points']}" if a in c else "-"
            )
        row += [c["_pairwise_complete"]["n"], c["_pairwise_complete"]["dropped"]]
        print("| " + " | ".join(str(x) for x in row) + " |")


def counts(rep: dict) -> None:
    print("\n## Counts on the pairwise-complete set\n")
    hdr = ["scenario", "tau", "hoist", "n", "arm", "mean sweeps",
           "sweep hist", "total node calls", "node calls vs R"]
    print("| " + " | ".join(hdr) + " |")
    print("|" + "---|" * len(hdr))
    for key, r in sorted(rep.get("replays", {}).items()):
        n = r["drop_census"]["_pairwise_complete"]["n"]
        base = _g(r, "per_arm", "R", "node_calls", "total")
        for a in r["per_arm"]:
            pa = r["per_arm"][a]
            tot = _g(pa, "node_calls", "total")
            print("| " + " | ".join(str(x) for x in [
                key.split("/")[0], f"{r['tau']:g}", int(r["hoist"]), n, a,
                f"{_g(pa, 'sweeps', 'mean', default=float('nan')):.3f}",
                json.dumps(pa["sweep_hist"]),
                tot,
                f"{tot / base:.4f}" if base else "-",
            ]) + " |")


def audit(rep: dict) -> None:
    print("\n## Exit audit -- matched final accuracy, per design point\n")
    hdr = ["scenario", "tau", "arm", "worst exit residual over points",
           "median exit residual", "worst count of components above tau"]
    print("| " + " | ".join(hdr) + " |")
    print("|" + "---|" * len(hdr))
    for key, r in sorted(rep.get("replays", {}).items()):
        for a in r["per_arm"]:
            pa = r["per_arm"][a]
            e = pa.get("exit_residual_max") or {}
            na = pa.get("exit_n_above_tau") or {}
            print("| " + " | ".join(str(x) for x in [
                key.split("/")[0], f"{r['tau']:g}", a,
                f"{e.get('max', float('nan')):.3g}",
                f"{e.get('median', float('nan')):.3g}",
                na.get("max"),
            ]) + " |")


def gates(rep: dict) -> None:
    print("\n## Gates\n")
    g = rep.get("process_side_gates", {})
    hdr = ["scenario", "status", "pristine vs control", "pristine vs harvest",
           "harvest determinism", "control vs harvest (inert)",
           "control vs harvest (cache on)", "ifail"]
    print("| " + " | ".join(hdr) + " |")
    print("|" + "---|" * len(hdr))
    for s, r in g.items():
        def f(k):
            v = r.get(k)
            if not isinstance(v, dict):
                return "-"
            return (f"{v['mfile_differing_lines']} lines / "
                    f"{len(v['exact_signature_differing_fields'])} fields")
        print("| " + " | ".join(str(x) for x in [
            s, r.get("status"),
            f("neutrality_pristine_vs_control"),
            f("neutrality_pristine_vs_harvest"),
            f("determinism_harvest"),
            f("inertness_control_vs_harvest"),
            f("inertness_control_vs_harvest_with_cache"),
            json.dumps(r.get("ifail", {})),
        ]) + " |")

    print("\n### Replay-side gates\n")
    hdr = ["scenario/run", "replay fidelity (R == live loop)",
           "restore exactness"]
    print("| " + " | ".join(hdr) + " |")
    print("|" + "---|" * len(hdr))
    for key, r in sorted(rep.get("replays", {}).items()):
        fd = r["gate_replay_fidelity"]
        rs = r["gate_restore_exactness"]
        print(f"| {key} | {fd['status']} {fd['exact']}/{fd['compared']} | "
              f"{rs['status']} {rs['mismatched_fields_total']} mismatched |")
    det = rep.get("gate_replay_determinism") or {}
    for k, v in det.items():
        print(f"| {k} (determinism) | {v['status']} | |")

    print("\n### Committed scale record (ystate)\n")
    hdr = ["scenario/run", "status", "components sha256", "harvest content sha256",
           "points scales measured over"]
    print("| " + " | ".join(hdr) + " |")
    print("|" + "---|" * len(hdr))
    for key, r in sorted(rep.get("replays", {}).items()):
        y = r.get("gate_ystate_record")
        if not y:
            continue
        print("| " + " | ".join(str(x) for x in [
            key, y.get("status"),
            (y.get("components_sha256") or "")[:16],
            (y.get("harvest_content_sha256") or "")[:16],
            y.get("scales_measured_over_n_design_points"),
        ]) + " |")


def ladder(rep: dict) -> None:
    lad = rep.get("tau_ladder") or {}
    print("\n## tau calibration ladder -- flat arm only, one-off\n")
    hdr = ["scenario", "tau", "converged/points", "mean sweeps",
           "total node calls", "median |d objf| vs tightest",
           "max |d objf| vs tightest", "median |d conf_l2| vs tightest",
           "max exit residual"]
    print("| " + " | ".join(hdr) + " |")
    print("|" + "---|" * len(hdr))
    for s, r in lad.items():
        if r.get("status") == "MISSING":
            continue
        for t, row in r["by_tau"].items():
            do = row["rel_change_objf_vs_tightest"]
            dc = row["rel_change_conf_l2_vs_tightest"]
            print("| " + " | ".join(str(x) for x in [
                s, t, f"{row['n_converged']}/{row['n_points']}",
                f"{_g(row, 'sweeps', 'mean', default=float('nan')):.3f}",
                row["node_calls_total"],
                f"{do.get('median', 0):.3g}" if do else "-",
                f"{do.get('max', 0):.3g}" if do else "-",
                f"{dc.get('median', 0):.3g}" if dc else "-",
                f"{_g(row, 'exit_residual_max', 'max', default=0):.3g}",
            ]) + " |")


def dsm(rep: dict) -> None:
    print("\n## DSM cross-check (C10): set (a) against set (b)\n")
    hdr = ["scenario", "tau", "compared", "DSM set earlier", "agree",
           "DSM set later", "DSM set never", "mean sweeps the DSM set "
           "would have saved"]
    print("| " + " | ".join(hdr) + " |")
    print("|" + "---|" * len(hdr))
    for key, r in sorted(rep.get("replays", {}).items()):
        c = r.get("dsm_cross_check")
        if not c:
            continue
        print("| " + " | ".join(str(x) for x in [
            key.split("/")[0], f"{r['tau']:g}", c["n_compared"],
            c["dsm_set_converged_earlier"], c["agree"],
            c["dsm_set_converged_later"], c["dsm_set_never_converged"],
            f"{c['mean_sweeps_saved_by_dsm_set']:.3f}"
            if c["mean_sweeps_saved_by_dsm_set"] is not None else "-",
        ]) + " |")


def ycensus(rep: dict) -> None:
    print("\n## The coupling state y, categorised by measurement\n")
    hdr = ["scenario", "components", "continuous", "discrete", "constant",
           "NaN in harvest", "harvest points", "scale median",
           "scales below 1e-2"]
    print("| " + " | ".join(hdr) + " |")
    print("|" + "---|" * len(hdr))
    seen = set()
    for key, r in sorted(rep.get("replays", {}).items()):
        s = key.split("/")[0]
        if s in seen:
            continue
        seen.add(s)
        y = r["y_census"]
        sc = r.get("y_scales_summary") or {}
        print("| " + " | ".join(str(x) for x in [
            s, y["n_components"], y["n_continuous"], y["n_discrete"],
            y["n_constant"], y["n_nan_in_harvest"], y["harvest_points_used"],
            f"{sc.get('median', float('nan')):.3g}", sc.get("n_below_1e-2"),
        ]) + " |")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True)
    ap.add_argument("--runs", default=str(RUNS))
    args = ap.parse_args()
    rep = json.loads(Path(args.report).read_text())
    runs = Path(args.runs)
    gates(rep)
    ycensus(rep)
    magnitudes(runs)
    ladder(rep)
    drop_census(rep)
    counts(rep)
    audit(rep)
    dsm(rep)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
