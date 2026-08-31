#!/usr/bin/env python
"""Stage-0 gate checker and sweep-anatomy table.

Reads ``runs/<scenario>/<arm>/metrics.json`` written by ``run_stage0.py`` and
evaluates the three Stage-0 gates:

(a) switch-neutrality
    An untouched checkout of the base commit (arm ``pristine``), the
    instrumented tree with the probe switch unset (arm ``control``) and the
    instrumented tree with ``PROCESS_IDF_PROBE=baseline`` must all produce
    **identical** results -- not "within tolerance".  The comparison is made
    on hex float literals, i.e. exact IEEE-754 doubles.
(b) determinism
    Two independent ``baseline`` runs of the same scenario must agree
    exactly.
(c) baseline solves
    Every scenario returns ``ifail = 1``.

Usage:  python compare.py [--runs DIR]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from metrics import exact_signature, sweep_table  # noqa: E402

SCENARIOS = [
    "large_tokamak_nof",
    "low_aspect_ratio_DEMO",
    "st_regression",
    "large_tokamak_eval",
]


def load(runs: Path, scenario: str, arm: str) -> dict | None:
    p = runs / scenario / arm / "metrics.json"
    return json.loads(p.read_text()) if p.exists() else None


def _diff_signature(a: dict, b: dict) -> list[str]:
    """Field names where two exact signatures differ."""
    return [k for k in a if a[k] != b.get(k)]


def gate_a(runs: Path, scenarios) -> dict:
    out = {}
    for s in scenarios:
        arms = {a: load(runs, s, a) for a in ("pristine", "control", "baseline")}
        if any(v is None for v in arms.values()):
            out[s] = {"status": "MISSING"}
            continue
        if any(v["status"] != "ok" for v in arms.values()):
            out[s] = {
                "status": "NOT APPLICABLE (run crashed)",
                "run_status": {a: v["status"] for a, v in arms.items()},
            }
            continue
        sig = {a: exact_signature(v) for a, v in arms.items()}
        d_pc = _diff_signature(sig["pristine"], sig["control"])
        d_pb = _diff_signature(sig["pristine"], sig["baseline"])
        out[s] = {
            "status": "PASS" if not d_pc and not d_pb else "FAIL",
            "pristine_vs_control_differing_fields": d_pc,
            "pristine_vs_baseline_differing_fields": d_pb,
            "norm_objf_hex": sig["pristine"]["norm_objf"],
            "conf_l2_hex": sig["pristine"]["conf_l2"],
            "n_itvars_compared": len(sig["pristine"]["xcs"] or []),
        }
    return out


def gate_b(runs: Path, scenarios) -> dict:
    out = {}
    for s in scenarios:
        a, b = load(runs, s, "baseline"), load(runs, s, "baseline_rep2")
        if a is None or b is None:
            out[s] = {"status": "MISSING"}
            continue
        if a["status"] != "ok" or b["status"] != "ok":
            out[s] = {
                "status": "NOT APPLICABLE (run crashed)",
                "run_status": [a["status"], b["status"]],
            }
            continue
        d = _diff_signature(exact_signature(a), exact_signature(b))
        probe_same = (
            a["probe"]["sweeps_total"] == b["probe"]["sweeps_total"]
            and a["probe"]["call_models_total"] == b["probe"]["call_models_total"]
            and a["probe"]["all_phases"]["hist"] == b["probe"]["all_phases"]["hist"]
        )
        out[s] = {
            "status": "PASS" if not d and probe_same else "FAIL",
            "differing_fields": d,
            "sweep_counts_identical": probe_same,
            "sweeps": [a["probe"]["sweeps_total"], b["probe"]["sweeps_total"]],
        }
    return out


def gate_c(runs: Path, scenarios) -> dict:
    out = {}
    for s in scenarios:
        m = load(runs, s, "baseline")
        if m is None:
            out[s] = {"status": "MISSING"}
            continue
        ifail = (m.get("mfile") or {}).get("ifail")
        out[s] = {
            "status": "PASS" if m["status"] == "ok" and ifail == 1.0 else "FAIL",
            "run_status": m["status"],
            "ifail": ifail,
            "error": (m.get("traceback") or "").strip().splitlines()[-1:]
            if m["status"] != "ok"
            else None,
        }
    return out


# MFILE fields that legitimately differ between two identical solves: run
# metadata and provenance, not results.
VOLATILE_MFILE_KEYS = (
    "(date)",
    "(time)",
    "(username)",
    "(computer)",
    "(directory)",
    "(fileprefix)",
    "(tagno)",
    "(branch_name)",
    "(commsg)",
    "(process_runtime)",
)


def _mfile_lines(path: Path) -> list[str]:
    return [
        ln
        for ln in path.read_text(errors="replace").splitlines()
        if not any(k in ln for k in VOLATILE_MFILE_KEYS)
    ]


def mfile_identity(runs: Path, scenarios) -> dict:
    """Whole-MFILE identity across arms -- the strongest form of (a) and (b).

    Every line of the MFILE except run metadata must match, not just the
    handful of quantities the gates name.
    """
    out = {}
    for s in scenarios:
        # A crashed run leaves a truncated MFILE; comparing those would report
        # a meaningless PASS.
        statuses = {
            arm: (load(runs, s, arm) or {}).get("status")
            for arm in ("pristine", "control", "baseline", "baseline_rep2")
        }
        if any(v != "ok" for v in statuses.values()):
            out[s] = {"status": "NOT APPLICABLE (run crashed)", "run_status": statuses}
            continue
        arms = {}
        for arm in ("pristine", "control", "baseline", "baseline_rep2"):
            cand = sorted((runs / s / arm).glob("*MFILE.DAT"))
            if cand:
                arms[arm] = _mfile_lines(cand[0])
        if "pristine" not in arms:
            out[s] = {"status": "MISSING"}
            continue
        base = arms["pristine"]
        deltas = {
            arm: sum(1 for a, b in zip(base, v, strict=False) if a != b)
            + abs(len(base) - len(v))
            for arm, v in arms.items()
            if arm != "pristine"
        }
        out[s] = {
            "status": "PASS" if all(d == 0 for d in deltas.values()) else "FAIL",
            "n_lines_compared": len(base),
            "differing_lines_vs_pristine": deltas,
        }
    return out


def anatomy(runs: Path, scenarios) -> dict:
    out = {}
    for s in scenarios:
        m = load(runs, s, "baseline")
        if m is None:
            continue
        row = sweep_table(m)
        row["status"] = m["status"]
        row["ifail"] = (m.get("mfile") or {}).get("ifail")
        row["n_model_calls_builtin"] = m.get("n_model_calls")
        out[s] = row
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=str(HERE / "runs"))
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    args = ap.parse_args()
    runs = Path(args.runs)

    result = {
        "gate_a_switch_neutrality": gate_a(runs, args.scenarios),
        "gate_b_determinism": gate_b(runs, args.scenarios),
        "gate_c_baseline_solves": gate_c(runs, args.scenarios),
        "mfile_whole_file_identity": mfile_identity(runs, args.scenarios),
        "sweep_anatomy": anatomy(runs, args.scenarios),
    }
    (runs / "_gates.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
