#!/usr/bin/env python
"""A/B tables: probe modes vs self-generated baselines."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from metrics import compare_itvars, load_jsonl, rel_delta, speedup, sweep_stats  # noqa: E402

RUNS = HERE / "runs"
OPT_SCENARIOS = ["large_tokamak_nof", "low_aspect_ratio_DEMO", "st_regression"]


def load(scenario: str, mode: str) -> dict | None:
    p = RUNS / scenario / mode / "metrics.json"
    return json.loads(p.read_text()) if p.exists() else None


def repro_gate() -> dict:
    a = load("large_tokamak_nof", "baseline_rep1")
    b = load("large_tokamak_nof", "baseline_rep2")
    if not a or not b:
        return {"status": "missing"}
    cmp = compare_itvars(a["mfile"], b["mfile"])
    return {
        "status": "PASS" if cmp["max_rel"] <= 1e-6 else "FAIL",
        "max_rel_itvar_delta": cmp["max_rel"],
        "n_itvars": cmp["n_common"],
        "norm_objf_rel_delta": rel_delta(a["mfile"]["norm_objf"], b["mfile"]["norm_objf"]),
        "sweeps_a": a["probe"]["n_sweeps"], "sweeps_b": b["probe"]["n_sweeps"],
    }


def baseline_summary() -> dict:
    out = {}
    for s, mode in [(x, "baseline_rep1") for x in OPT_SCENARIOS] + [
        ("large_tokamak_eval", "baseline")
    ]:
        d = load(s, mode)
        if not d:
            continue
        recs = load_jsonl(RUNS / s / mode / "probe.jsonl")
        st = sweep_stats(recs)
        n = d.get("nvar")
        S = st["ALL"]["mean_S"]
        out[s] = {
            "mode": mode,
            "nvar": n, "neqns": d.get("neqns"), "nineqns": d.get("nineqns"),
            "ifail": d["mfile"]["ifail"], "norm_objf": d["mfile"]["norm_objf"],
            "nviter": d["mfile"]["nviter"],
            "n_call_models": d["probe"]["n_call_models"],
            "total_sweeps": d["probe"]["n_sweeps"],
            "n_retries": d["probe"]["n_retries"],
            "epsfcn_final": d.get("epsfcn_final"),
            "wall_s": d["wall_s"],
            "mean_S": S,
            "sweeps": st,
            "idf_speedup_projection": {
                f"k={k}": speedup(S, n, k) for k in (4, 6, 8, 10, 12)
            } if n else {},
            "itvars": d["mfile"]["itvars"],
        }
    return out


def ab_table() -> dict:
    out = {}
    for s in OPT_SCENARIOS:
        base = load(s, "baseline_rep1")
        test = load(s, "single_sweep")
        if not base or not test:
            out[s] = {"status": "missing", "have_base": bool(base), "have_test": bool(test)}
            continue
        row: dict = {
            "base_ifail": base["mfile"]["ifail"], "test_ifail": test["mfile"]["ifail"],
            "test_status": test["status"],
            "base_norm_objf": base["mfile"]["norm_objf"],
            "test_norm_objf": test["mfile"]["norm_objf"],
            "base_nviter": base["mfile"]["nviter"], "test_nviter": test["mfile"]["nviter"],
            "base_sweeps": base["probe"]["n_sweeps"], "test_sweeps": test["probe"]["n_sweeps"],
            "base_calls": base["probe"]["n_call_models"],
            "test_calls": test["probe"]["n_call_models"],
            "base_wall": base["wall_s"], "test_wall": test["wall_s"],
            "base_retries": base["probe"]["n_retries"],
            "test_retries": test["probe"]["n_retries"],
            "base_epsfcn": base.get("epsfcn_final"), "test_epsfcn": test.get("epsfcn_final"),
        }
        if base["mfile"]["norm_objf"] is not None and test["mfile"]["norm_objf"] is not None:
            row["d_norm_objf_abs"] = abs(test["mfile"]["norm_objf"] - base["mfile"]["norm_objf"])
            row["d_norm_objf_rel"] = rel_delta(base["mfile"]["norm_objf"], test["mfile"]["norm_objf"])
        row["itvar"] = compare_itvars(base["mfile"], test["mfile"])
        if row["base_sweeps"] and row["test_sweeps"]:
            row["sweep_ratio"] = row["base_sweeps"] / row["test_sweeps"]
        if row["base_wall"] and row["test_wall"]:
            row["wall_ratio"] = row["base_wall"] / row["test_wall"]
        out[s] = row
    return out


def drift_ranking(scenario="large_tokamak_nof", top=15) -> dict:
    recs = load_jsonl(RUNS / scenario / "single_sweep_debug" / "probe.jsonl")
    drifts = [r for r in recs if r.get("kind") == "drift"]
    if not drifts:
        return {"status": "missing"}
    agg: dict[int, list[float]] = {}
    objf_rel = []
    for r in drifts:
        objf_rel.append(r["objf_rel"])
        for c in r["conf"]:
            agg.setdefault(c["j"], []).append(c["rel"])
    rank = sorted(
        ({"constraint_index": j,
          "max_rel_drift": max(v),
          "mean_rel_drift": sum(v) / len(v),
          "n": len(v)} for j, v in agg.items()),
        key=lambda d: -d["max_rel_drift"],
    )
    objf_rel.sort()
    return {
        "n_drift_records": len(drifts),
        "objf_rel_drift_median": objf_rel[len(objf_rel) // 2],
        "objf_rel_drift_max": objf_rel[-1],
        "top_constraints": rank[:top],
    }


if __name__ == "__main__":
    result = {
        "reproducibility_gate": repro_gate(),
        "baseline_summary": baseline_summary(),
        "ab_single_sweep": ab_table(),
        "drift_ranking": drift_ranking(),
    }
    (RUNS / "baseline_summary.json").write_text(
        json.dumps(result["baseline_summary"], indent=2))
    (RUNS / "comparison.json").write_text(json.dumps(result, indent=2))

    def brief(d):
        if isinstance(d, dict):
            return {k: brief(v) for k, v in d.items() if k not in ("itvars", "sweeps", "per_var")}
        return d

    print(json.dumps(brief(result), indent=2, default=str))
