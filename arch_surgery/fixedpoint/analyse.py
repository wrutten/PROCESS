#!/usr/bin/env python
"""Phase A analysis: gates first, drop census second, ratios last.

The ordering is not cosmetic.  **The drop census comes before any ratio**: a
control that cannot converge a design point is itself a finding, and arms
averaged over different populations are not comparable.  Every number here is
a **count** or a **bit-comparison**; the only wall-clock figures reported are
labelled context and are never used to decide anything.
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = HERE.parent / "idf_probe"
RUNS = PROBE / "runs" / "a18"
sys.path.insert(0, str(PROBE))

VOLATILE_MFILE_KEYS = (
    "(date)", "(time)", "(username)", "(computer)", "(directory)",
    "(fileprefix)", "(tagno)", "(branch_name)", "(commsg)", "(process_runtime)",
)

#: **Three decks, from 2026-09-02 (D17).**  ``large_tokamak_eval`` is dropped:
#: it runs 0 solver iterations, so it cannot inform a study about how an
#: architecture behaves when the optimiser reacts; its inequality constraints
#: are never enforced, so its "solution" is not a feasible optimum; and A22
#: found its evidence weaker than the other pulsed decks (555 of 840 coupling
#: components classified constant from a 10-point harvest).  It was carrying
#: two of the results report's largest percentages on ten design points.
#: **Merged four-deck tables stand as the record of what was run** and are not
#: retro-edited; anything generated from here on is a three-deck table.  Pass
#: ``--scenarios`` explicitly to run the dropped deck for a historical
#: re-derivation.
DROPPED_2026_09_02 = ("large_tokamak_eval",)

SCENARIOS = [
    "large_tokamak_nof",
    "low_aspect_ratio_DEMO",
    "st_regression",
]


def _load(p: Path):
    return json.loads(p.read_text()) if p.exists() else None


def _mfile_lines(d: Path):
    cand = sorted(d.glob("*MFILE.DAT"))
    if not cand:
        return None
    return [
        ln
        for ln in cand[0].read_text(errors="replace").splitlines()
        if not any(k in ln for k in VOLATILE_MFILE_KEYS)
    ]


def _diff_lines(a, b) -> int:
    if a is None or b is None:
        return -1
    return sum(1 for x, y in zip(a, b, strict=False) if x != y) + abs(len(a) - len(b))


# --------------------------------------------------------------------------
# Gates
# --------------------------------------------------------------------------


def gates(runs: Path, scenarios) -> dict:
    from metrics import exact_signature  # noqa: PLC0415

    out = {}
    for s in scenarios:
        arms = {}
        for arm in ("pristine", "control",
                    "harvest_inert", "harvest_rep2", "harvest"):
            m = _load(runs / s / arm / "metrics.json")
            if m:
                arms[arm] = m
        row: dict = {"arms_present": sorted(arms)}
        if any(m.get("status") != "ok" for m in arms.values()):
            row["status"] = "NOT APPLICABLE (a run crashed)"
            row["run_status"] = {a: m.get("status") for a, m in arms.items()}
            out[s] = row
            continue

        sig = {a: exact_signature(m) for a, m in arms.items()}
        lines = {a: _mfile_lines(runs / s / a) for a in arms}

        def cmp(a, b):
            if a not in arms or b not in arms:
                return None
            return {
                "exact_signature_differing_fields": [
                    k for k in sig[a] if sig[a][k] != sig[b].get(k)
                ],
                "mfile_lines_compared": len(lines[a] or []),
                "mfile_differing_lines": _diff_lines(lines[a], lines[b]),
            }

        row["neutrality_pristine_vs_control"] = cmp("pristine", "control")
        row["neutrality_pristine_vs_harvest"] = cmp("pristine", "harvest_inert")
        row["determinism_harvest"] = cmp("harvest_inert", "harvest_rep2")
        row["inertness_control_vs_harvest"] = cmp("control", "harvest_inert")
        row["inertness_control_vs_harvest_with_cache"] = cmp("control", "harvest")

        # A gate with a missing arm is not a gate that passed.  Before this
        # check, an absent run made its comparison ``None`` and the remaining
        # comparisons could still report PASS -- the exact shape of silent
        # failure this suite exists to prevent.
        required = ("pristine", "control", "harvest_inert", "harvest_rep2",
                    "harvest")
        absent = [a for a in required if a not in arms]
        checks = [v for v in row.values() if isinstance(v, dict) and
                  "mfile_differing_lines" in v]
        if absent:
            row["status"] = "INCOMPLETE"
            row["missing_arms"] = absent
        else:
            row["status"] = (
                "PASS"
                if checks and all(
                    not v["exact_signature_differing_fields"]
                    and v["mfile_differing_lines"] == 0
                    for v in checks
                )
                else "FAIL"
            )
        row["ifail"] = {a: (m.get("mfile") or {}).get("ifail") for a, m in arms.items()}

        # Determinism is sweep-for-sweep as well as bit-for-bit.
        def _sw(a):
            pr = (arms.get(a) or {}).get("probe") or {}
            return {
                "sweeps_total": pr.get("sweeps_total"),
                "call_models_total": pr.get("call_models_total"),
                "hist": ((pr.get("all_phases") or {}).get("hist")),
            }

        if "harvest_inert" in arms and "harvest_rep2" in arms:
            a, b = _sw("harvest_inert"), _sw("harvest_rep2")
            row["determinism_harvest_sweepwise"] = {
                "status": "PASS" if a == b else "FAIL",
                "a": a,
                "b": b,
            }
            if a != b:
                row["status"] = "FAIL"
        out[s] = row
    return out


# --------------------------------------------------------------------------
# Replay-side gates and the comparison
# --------------------------------------------------------------------------


def _hist(vals) -> dict:
    h: dict = {}
    for v in vals:
        h[v] = h.get(v, 0) + 1
    return {str(k): h[k] for k in sorted(h)}


def _stats(vals) -> dict:
    vals = [v for v in vals if v is not None]
    if not vals:
        return {}
    return {
        "n": len(vals),
        "total": sum(vals),
        "mean": st.fmean(vals),
        "median": st.median(vals),
        "min": min(vals),
        "max": max(vals),
    }


def replay_report(res: dict) -> dict:
    arms = res["arms"]
    pts = res["points"]

    # ---- gate: replay fidelity (arm R must reproduce the live loop) ----
    fid_ok = fid_n = 0
    fid_bad = []
    if "R" in arms:
        for p in pts:
            live = p.get("s_global_live")
            got = p["arms"]["R"].get("sweeps")
            if live is None:
                continue
            fid_n += 1
            if live == got:
                fid_ok += 1
            elif len(fid_bad) < 20:
                fid_bad.append({"call_index": p["call_index"], "live": live,
                                "replayed": got})

    # ---- drop census, BEFORE any ratio ----------------------------------
    census = {}
    for a in arms:
        conv = [p for p in pts if p["arms"][a].get("converged")]
        caps: dict = {}
        for p in pts:
            c = p["arms"][a].get("cap_hit")
            if c:
                caps[c] = caps.get(c, 0) + 1
        census[a] = {
            "n_points": len(pts),
            "n_converged": len(conv),
            "frac_converged": len(conv) / len(pts) if pts else None,
            "cap_hits": caps,
            "n_errors": sum(1 for p in pts if p["arms"][a].get("error")),
            "n_moved_constants_points": sum(
                1 for p in pts if p["arms"][a].get("moved_constants")
            ),
        }
    complete = [p for p in pts if all(p["arms"][a].get("converged") for a in arms)]
    census["_pairwise_complete"] = {
        "n": len(complete),
        "frac_of_points": len(complete) / len(pts) if pts else None,
        "dropped": len(pts) - len(complete),
    }

    # ---- counts on the pairwise-complete set ---------------------------
    per_arm = {}
    for a in arms:
        per_arm[a] = {
            "sweeps": _stats([p["arms"][a]["sweeps"] for p in complete]),
            "sweep_hist": _hist([p["arms"][a]["sweeps"] for p in complete]),
            "node_calls": _stats([p["arms"][a]["node_calls"] for p in complete]),
            "module_sweeps": _stats(
                [p["arms"][a]["module_sweeps"] for p in complete]
            ),
            "exit_residual_max": _stats(
                [p["arms"][a]["audit"]["max"] for p in complete
                 if "audit" in p["arms"][a]]
            ),
            "exit_n_above_tau": _stats(
                [p["arms"][a]["audit"]["n_above"] for p in complete
                 if "audit" in p["arms"][a]]
            ),
            "objf_at_exit": _stats(
                [p["arms"][a]["audit"]["objf_at_exit"] for p in complete
                 if "audit" in p["arms"][a]]
            ),
            "conf_l2_at_exit": _stats(
                [p["arms"][a]["audit"]["conf_l2_at_exit"] for p in complete
                 if "audit" in p["arms"][a]]
            ),
        }
        inner = [p["arms"][a].get("inner") for p in complete]
        if any(i and i.get("total") for i in inner):
            tot: dict = {}
            for i in inner:
                for k, v in (i.get("total") or {}).items():
                    tot.setdefault(k, []).append(v)
            per_arm[a]["inner_module_sweeps"] = {
                k: _stats(v) for k, v in sorted(tot.items())
            }

    # ---- paired differences (counts, per design point) ------------------
    paired = {}
    ref = "R" if "R" in arms else arms[0]
    for a in arms:
        if a == ref:
            continue
        d_nodes = [
            p["arms"][a]["node_calls"] - p["arms"][ref]["node_calls"]
            for p in complete
        ]
        d_sweeps = [
            p["arms"][a]["sweeps"] - p["arms"][ref]["sweeps"] for p in complete
        ]
        tot_a = sum(p["arms"][a]["node_calls"] for p in complete)
        tot_r = sum(p["arms"][ref]["node_calls"] for p in complete)
        paired[f"{ref}->{a}"] = {
            "delta_node_calls": _stats(d_nodes),
            "delta_node_calls_hist": _hist(d_nodes),
            "delta_sweeps_hist": _hist(d_sweeps),
            "total_node_calls_ratio": (tot_a / tot_r) if tot_r else None,
            "total_node_calls": {ref: tot_r, a: tot_a},
        }

    # ---- C10: the DSM cross-check ---------------------------------------
    cross = None
    if "A0" in arms:
        rows = [
            (p["arms"]["A0"].get("cross_converged_at"), p["arms"]["A0"]["sweeps"])
            for p in complete
            if p["arms"]["A0"].get("cross_converged_at") is not None
        ]
        early = sum(1 for c, f in rows if c < f)
        same = sum(1 for c, f in rows if c == f)
        late = sum(1 for c, f in rows if c > f)
        never = sum(
            1
            for p in complete
            if p["arms"]["A0"].get("cross_converged_at") is None
        )
        cross = {
            "spec": res.get("dsm_cross_check"),
            "n_compared": len(rows),
            "dsm_set_converged_earlier": early,
            "agree": same,
            "dsm_set_converged_later": late,
            "dsm_set_never_converged": never,
            "mean_sweeps_saved_by_dsm_set": (
                st.fmean([f - c for c, f in rows]) if rows else None
            ),
        }

    # ---- constants that moved, named ------------------------------------
    movers: dict = {}
    for p in pts:
        for a in arms:
            for f in p["arms"][a].get("moved_constants") or []:
                movers[f] = movers.get(f, 0) + 1

    return {
        "scenario": res["scenario"],
        "label": res.get("label"),
        "tau": res["tau"],
        "hoist": res["hoist"],
        "n_points": len(pts),
        "n_harvest_points": res.get("n_harvest_points"),
        "y_census": res["y_census"],
        "gate_ystate_record": res.get("ystate_record"),
        "y_scales_summary": res.get("y_scales_summary"),
        "node_map_check": res.get("node_map_check"),
        "node_map_counts": res.get("node_map_counts"),
        "topology": {
            k: v for k, v in (res.get("topology") or {}).items()
            if k != "loop_nodes_by_module"
        },
        "gate_restore_exactness": {
            "mismatched_fields_total": res.get("restore_mismatch_total"),
            "status": "PASS" if res.get("restore_mismatch_total") == 0 else "FAIL",
            "fields": res.get("restore_mismatch_fields"),
        },
        "gate_replay_fidelity": {
            "exact": fid_ok,
            "compared": fid_n,
            "status": ("PASS" if fid_n and fid_ok == fid_n
                       else ("FAIL" if fid_n else "N/A -- arm R not run")),
            "mismatches": fid_bad,
        },
        "dsm_cross_check": cross,
        "drop_census": census,
        "per_arm": per_arm,
        "paired": paired,
        "moved_constants": dict(
            sorted(movers.items(), key=lambda kv: -kv[1])[:40]
        ),
        "errors": res.get("errors", [])[:10],
        "wall_s_context_only": res.get("wall_s"),
    }


def ladder(runs: Path, scenario: str) -> dict:
    """The tau calibration ladder, paired per design point.

    Sweeps-to-converge at each tau, and the *induced* change in ``objf`` and
    the constraint vector relative to the tightest tau on the ladder.  The
    ladder is itself a result: it measures how much the answer depends on the
    tolerance.  The honest distinction -- convergence is on ``y``; tau is
    calibrated by its effect on ``f``.  Calibration is not the predicate.
    """
    found = {}
    for d in sorted((runs / scenario).glob("replay_ladder_tau*")):
        res = _load(d / "result.json")
        if res:
            found[res["tau"]] = res
    if len(found) < 2:
        return {"status": "MISSING", "taus": sorted(found)}
    taus = sorted(found)
    ref = taus[0]  # tightest
    by_tau = {}
    for t in taus:
        res = found[t]
        pts = {p["call_index"]: p for p in res["points"]}
        by_tau[t] = pts
    common = set.intersection(*(set(v) for v in by_tau.values()))
    rows = {}
    for t in taus:
        conv = [
            by_tau[t][c] for c in sorted(common)
            if by_tau[t][c]["arms"]["A0"].get("converged")
        ]
        d_objf, d_conf = [], []
        for c in sorted(common):
            a = by_tau[t][c]["arms"]["A0"]
            b = by_tau[ref][c]["arms"]["A0"]
            if not (a.get("converged") and b.get("converged")):
                continue
            o0 = b["audit"]["objf_at_exit"]
            if o0:
                d_objf.append(abs(a["audit"]["objf_at_exit"] - o0) / abs(o0))
            c0 = b["audit"]["conf_l2_at_exit"]
            if c0:
                d_conf.append(abs(a["audit"]["conf_l2_at_exit"] - c0) / abs(c0))
        rows[f"{t:g}"] = {
            "n_points": len(common),
            "n_converged": len(conv),
            "sweeps": _stats([p["arms"]["A0"]["sweeps"] for p in conv]),
            "sweep_hist": _hist([p["arms"]["A0"]["sweeps"] for p in conv]),
            "node_calls_total": sum(p["arms"]["A0"]["node_calls"] for p in conv),
            "rel_change_objf_vs_tightest": _stats(d_objf),
            "rel_change_conf_l2_vs_tightest": _stats(d_conf),
            "exit_residual_max": _stats(
                [p["arms"]["A0"]["audit"]["max"] for p in conv]
            ),
        }
    return {"scenario": scenario, "tightest_tau": ref, "by_tau": rows}


def _strip_volatile(res: dict) -> str:
    d = dict(res)
    d.pop("wall_s", None)
    d.pop("harvest", None)
    d.pop("tree", None)
    d.pop("label", None)
    return json.dumps(d, sort_keys=True)


def replay_determinism(a: Path, b: Path) -> dict:
    ra, rb = _load(a), _load(b)
    if not ra or not rb:
        return {"status": "MISSING"}
    same = _strip_volatile(ra) == _strip_volatile(rb)
    return {
        "status": "PASS" if same else "FAIL",
        "compared": [str(a), str(b)],
    }


# --------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=str(RUNS))
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    ap.add_argument("--what", nargs="*",
                    default=["gates", "replays", "ladder"])
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    runs = Path(args.runs)

    report: dict = {}
    if "gates" in args.what:
        report["process_side_gates"] = gates(runs, args.scenarios)

    if "replays" in args.what:
        reps: dict = {}
        for s in args.scenarios:
            for d in sorted((runs / s).glob("replay_*")):
                res = _load(d / "result.json")
                if res:
                    reps[f"{s}/{d.name}"] = replay_report(res)
        report["replays"] = reps

        det: dict = {}
        for s in args.scenarios:
            for d in sorted((runs / s).glob("replay_*")):
                if d.name.endswith("_rep2"):
                    base = runs / s / d.name[: -len("_rep2")]
                    det[f"{s}/{d.name}"] = replay_determinism(
                        base / "result.json", d / "result.json"
                    )
        if det:
            report["gate_replay_determinism"] = det

    if "ladder" in args.what:
        report["tau_ladder"] = {s: ladder(runs, s) for s in args.scenarios}

    text = json.dumps(report, indent=2, default=str)
    if args.out:
        Path(args.out).write_text(text)
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
