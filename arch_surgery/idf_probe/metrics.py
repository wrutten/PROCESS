"""MFILE -> metrics dict, plus probe.jsonl rollups."""

from __future__ import annotations

import json
from pathlib import Path


def parse_mfile(path: Path | str) -> dict:
    from process.core.io.mfile import MFile

    mf = MFile(str(path))

    def g(key):
        try:
            v = mf.data[key].get_scan(-1)
        except Exception:
            return None
        return v

    out: dict = {
        "ifail": g("ifail"),
        "norm_objf": g("norm_objf"),
        "nviter": g("nviter"),
        "ncalls": g("ncalls"),
        "process_runtime": g("process_runtime"),
        "sqsumsq": g("sqsumsq"),
        "epsfcn": g("epsfcn"),
    }

    itvars = {}
    names = {}
    for i in range(1, 200):
        key = f"itvar{i:03d}"
        if key not in mf.data:
            break
        itvars[key] = mf.data[key].get_scan(-1)
        names[key] = getattr(mf.data[key], "var_description", "")
    out["itvars"] = itvars
    out["itvar_names"] = names
    return out


def rel_delta(a, b) -> float:
    """Relative delta of b w.r.t. a, robust to zeros."""
    if a is None or b is None:
        return float("nan")
    denom = abs(a) if abs(a) > 1e-30 else 1.0
    return abs(b - a) / denom


def compare_itvars(base: dict, test: dict) -> dict:
    """Compare two parse_mfile() outputs on their common itvar keys."""
    bi, ti = base.get("itvars", {}), test.get("itvars", {})
    common = [k for k in bi if k in ti]
    deltas = {k: rel_delta(bi[k], ti[k]) for k in common}
    vals = sorted(deltas.values()) if deltas else [float("nan")]
    n = len(vals)
    return {
        "n_common": len(common),
        "max_rel": max(vals) if deltas else float("nan"),
        "median_rel": vals[n // 2] if deltas else float("nan"),
        "worst": sorted(deltas.items(), key=lambda kv: -kv[1])[:8],
        "names": {k: base.get("itvar_names", {}).get(k, "") for k, _ in
                  sorted(deltas.items(), key=lambda kv: -kv[1])[:8]},
    }


def load_jsonl(path: Path | str) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    recs = []
    for line in p.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return recs


def sweep_stats(records: list[dict]) -> dict:
    """Sweeps-per-call_models histogram and mean S, split by phase."""
    by_phase: dict[str, list[int]] = {}
    for r in records:
        if r.get("kind") != "call":
            continue
        by_phase.setdefault(r["phase"], []).append(r["sweeps"])
    out = {}
    allv: list[int] = []
    for ph, v in by_phase.items():
        allv.extend(v)
        hist: dict[int, int] = {}
        for s in v:
            hist[s] = hist.get(s, 0) + 1
        out[ph] = {
            "n_calls": len(v),
            "mean_S": sum(v) / len(v) if v else float("nan"),
            "hist": {str(k): hist[k] for k in sorted(hist)},
            "frac_at_floor_2": sum(1 for s in v if s == 2) / len(v) if v else float("nan"),
        }
    hist_all: dict[int, int] = {}
    for s in allv:
        hist_all[s] = hist_all.get(s, 0) + 1
    out["ALL"] = {
        "n_calls": len(allv),
        "total_sweeps": sum(allv),
        "mean_S": sum(allv) / len(allv) if allv else float("nan"),
        "hist": {str(k): hist_all[k] for k in sorted(hist_all)},
        "frac_at_floor_2": sum(1 for s in allv if s == 2) / len(allv) if allv else float("nan"),
    }
    return out


def speedup(S: float, n: int, k: int) -> float:
    """Per-iterate IDF speedup: S*(n+1)/(n+k+1)."""
    return S * (n + 1) / (n + k + 1)
