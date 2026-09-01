#!/usr/bin/env python
"""A3 (build-reorder) gate checker.

Two comparisons, both against the arm ``parent`` -- a ``git archive`` extraction
of this branch's parent commit:

**Neutrality of the default path** -- ``default`` vs ``parent``.  The VP1 list
with ``PROCESS_ARCH_SEQUENCE`` unset must reproduce the three straight-line
calls it replaced, bit for bit.

**The reorder gate** -- ``reordered`` vs ``parent``.  Moving ``build`` must not
change a single number.

Both are bit-comparisons with **no tolerance applied anywhere**.  Three
independent comparisons are made per arm pair:

1. *Whole MFILE, line by line.*  ``ovarre`` writes floats as ``f"{v:.17e}"`` --
   18 significant decimal digits, which round-trips an IEEE-754 double exactly,
   so an identical line is an identical double.  Ten run-metadata keys (date,
   time, username, host, directory, file prefix, git tag, branch, commit
   message, and the wall-clock ``process_runtime``) are excluded by name: they
   are provenance, not results, and they differ between any two runs.
2. *Every MFILE float, re-parsed and compared as a hex float literal.*  This is
   the same content as (1) read a second way, and it is the check that a
   comparison can never pass by both sides being unparseable text.
3. *The in-memory exact signature* from ``metrics.json`` -- ``norm_objf``,
   ``sqsumsq``, ``conf_l2`` and the iteration-variable vectors, as hex floats.

Every count printed is a count of things actually compared, and the denominator
is printed beside it.  An empty comparison set is reported as ``EMPTY``, never
as a pass.

Usage:  python compare_a3.py --runs runs_a3
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from metrics import exact_signature  # noqa: E402

SCENARIOS = [
    "large_tokamak_nof",
    "low_aspect_ratio_DEMO",
    "st_regression",
    "large_tokamak_eval",
]

#: Run metadata and provenance: differs between any two runs of identical code.
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

#: An MFILE data line is
#:     <description padded to 72 with underscores>_ <(varname) padded to 30
#:     with underscores>_ <value> [flag]
#: (``process_output.ovarre``).  Spaces inside the description are replaced by
#: underscores, so the three fields are whitespace-separated and the *second*
#: one carries the variable name.  Anchoring on the first ``(...)`` in the line
#: is wrong: descriptions routinely contain parentheses -- ``Major_radius_(R0)
#: _(m)`` -- and such a line would be parsed as the variable ``R0`` with an
#: unparseable value, i.e. silently dropped from the comparison.
_VARNAME = re.compile(r"^\((?P<key>[^)]+)\)_*$")


def _mfile_path(runs: Path, scenario: str, arm: str) -> Path | None:
    cand = sorted((runs / scenario / arm).glob("*MFILE.DAT"))
    return cand[0] if cand else None


def _lines(path: Path) -> list[str]:
    return [
        ln
        for ln in path.read_text(errors="replace").splitlines()
        if not any(k in ln for k in VOLATILE_MFILE_KEYS)
    ]


def _floats(path: Path) -> dict[str, str]:
    """Every MFILE entry whose value field parses as a float, as a hex literal.

    Keyed by ``varname``; duplicate varnames (scan columns) are suffixed with
    their occurrence index so none is silently dropped from the denominator.
    """
    out: dict[str, str] = {}
    seen: dict[str, int] = {}
    for ln in path.read_text(errors="replace").splitlines():
        if any(k in ln for k in VOLATILE_MFILE_KEYS):
            continue
        parts = ln.split()
        if len(parts) < 3:
            continue
        m = _VARNAME.match(parts[1])
        if not m:
            continue
        try:
            v = float(parts[2].strip('"'))
        except ValueError:
            continue
        key = m.group("key")
        n = seen.get(key, 0)
        seen[key] = n + 1
        out[key if n == 0 else f"{key}#{n}"] = v.hex()
    return out


def float_line_census(path: Path) -> dict:
    """How many MFILE lines carry a float, and what the rest are.

    Printed beside every mismatch count so the denominator of the float
    comparison is stated rather than implied.
    """
    n_lines = n_named = n_float = 0
    for ln in path.read_text(errors="replace").splitlines():
        if any(k in ln for k in VOLATILE_MFILE_KEYS):
            continue
        n_lines += 1
        parts = ln.split()
        if len(parts) < 3 or not _VARNAME.match(parts[1]):
            continue
        n_named += 1
        try:
            float(parts[2].strip('"'))
        except ValueError:
            continue
        n_float += 1
    return {
        "lines_after_volatile_filter": n_lines,
        "lines_with_a_variable_name": n_named,
        "lines_whose_value_parses_as_float": n_float,
    }


def load(runs: Path, scenario: str, arm: str) -> dict | None:
    p = runs / scenario / arm / "metrics.json"
    return json.loads(p.read_text()) if p.exists() else None


def compare_pair(runs: Path, scenario: str, ref: str, arm: str) -> dict:
    mr, ma = load(runs, scenario, ref), load(runs, scenario, arm)
    if mr is None or ma is None:
        return {"status": "MISSING"}
    if mr["status"] != "ok" or ma["status"] != "ok":
        return {
            "status": "NOT APPLICABLE (run crashed)",
            "run_status": {ref: mr["status"], arm: ma["status"]},
        }

    pr, pa = _mfile_path(runs, scenario, ref), _mfile_path(runs, scenario, arm)
    if pr is None or pa is None:
        return {"status": "MISSING MFILE"}

    lr, la = _lines(pr), _lines(pa)
    line_diff = sum(1 for a, b in zip(lr, la, strict=False) if a != b) + abs(
        len(lr) - len(la)
    )

    fr, fa = _floats(pr), _floats(pa)
    common = set(fr) & set(fa)
    float_diff = sorted(k for k in common if fr[k] != fa[k])
    only_ref = sorted(set(fr) - set(fa))
    only_arm = sorted(set(fa) - set(fr))

    sr, sa = exact_signature(mr), exact_signature(ma)
    sig_keys = [k for k in sr if k != "mfile_raw"]
    sig_diff = [k for k in sig_keys if sr[k] != sa.get(k)]
    raw_r, raw_a = sr["mfile_raw"], sa["mfile_raw"]
    raw_common = sorted(set(raw_r) & set(raw_a))
    raw_diff = [k for k in raw_common if raw_r[k] != raw_a[k]]

    n_compared = len(lr) + len(common) + len(sig_keys) + len(raw_common)
    ok = (
        line_diff == 0
        and not float_diff
        and not only_ref
        and not only_arm
        and not sig_diff
        and not raw_diff
    )
    return {
        "status": ("PASS" if ok else "FAIL") if n_compared else "EMPTY",
        "mfile_lines_compared": len(lr),
        "mfile_lines_differing": line_diff,
        "mfile_floats_compared": len(common),
        "mfile_floats_differing": len(float_diff),
        "mfile_floats_differing_keys": float_diff[:20],
        "mfile_keys_only_in_ref": only_ref[:20],
        "mfile_keys_only_in_arm": only_arm[:20],
        "signature_fields_compared": len(sig_keys),
        "signature_fields_differing": sig_diff,
        "raw_fields_compared": len(raw_common),
        "raw_fields_differing": raw_diff,
        "total_quantities_compared": n_compared,
        "mfile_line_census_ref": float_line_census(pr),
        "ifail": {
            ref: (mr.get("mfile") or {}).get("ifail"),
            arm: (ma.get("mfile") or {}).get("ifail"),
        },
        "arch_sequence_head": {
            ref: mr.get("arch_sequence_head"),
            arm: ma.get("arch_sequence_head"),
        },
        "arch_sequence_name": {
            ref: mr.get("arch_sequence_name"),
            arm: ma.get("arch_sequence_name"),
        },
    }


def sweeps(runs: Path, scenario: str) -> dict:
    out = {}
    for arm in ("parent_probe", "default_probe", "reordered_probe"):
        m = load(runs, scenario, arm)
        if m is None:
            out[arm] = None
            continue
        p = m.get("probe") or {}
        out[arm] = {
            "sweeps_total": p.get("sweeps_total"),
            "call_models_total": p.get("call_models_total"),
            "n_model_calls_builtin": m.get("n_model_calls"),
            "n_solver_iterations": m.get("n_solver_iterations"),
            "ifail": (m.get("mfile") or {}).get("ifail"),
            "arch_sequence_name": m.get("arch_sequence_name"),
        }
    vals = [v["sweeps_total"] for v in out.values() if v]
    out["identical"] = len(set(vals)) == 1 and len(vals) == 3
    return out


def census(runs: Path, scenario: str) -> dict:
    out = {}
    for arm in ("parent", "default", "reordered"):
        p = runs / scenario / f"census_{arm}" / "sequence_census.json"
        if not p.exists():
            out[arm] = None
            continue
        c = json.loads(p.read_text())
        out[arm] = {
            "status": c["status"],
            "n_sweeps": c["n_sweeps"],
            "n_calls_per_sweep": c["n_calls_first_sweep"],
            "distinct_sweep_orders": c["distinct_sweep_orders"],
            "sequence": c["first_sweep_order"],
            "total_depth0_calls": c["total_depth0_calls"],
            "calls_by_node": c["calls_by_node"],
            "n_refused_outside_sweep": c["n_refused_outside_sweep"],
            "arch_sequence_name": c.get("arch_sequence_name"),
        }
    p, d, r = out["parent"], out["default"], out["reordered"]
    out["parent_vs_default_sequence_identical"] = bool(
        p and d and p["sequence"] == d["sequence"]
    )
    out["parent_vs_reordered_sequence_identical"] = bool(
        p and r and p["sequence"] == r["sequence"]
    )
    out["calls_per_sweep_identical"] = bool(
        p and d and r and p["n_calls_per_sweep"] == d["n_calls_per_sweep"] == r["n_calls_per_sweep"]
    )
    out["calls_by_node_identical"] = bool(
        p and d and r and p["calls_by_node"] == d["calls_by_node"] == r["calls_by_node"]
    )
    if p and r:
        out["build_index_parent"] = p["sequence"].index("build")
        out["build_index_reordered"] = r["sequence"].index("build")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=str(HERE / "runs_a3"))
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    args = ap.parse_args()
    runs = Path(args.runs).resolve()

    result = {
        "neutrality_default_vs_parent": {
            s: compare_pair(runs, s, "parent", "default") for s in args.scenarios
        },
        "gate_reordered_vs_parent": {
            s: compare_pair(runs, s, "parent", "reordered") for s in args.scenarios
        },
        "probe_arm_reordered_vs_parent": {
            s: compare_pair(runs, s, "parent_probe", "reordered_probe")
            for s in args.scenarios
        },
        "sweeps": {s: sweeps(runs, s) for s in args.scenarios},
        "sequence_census": {s: census(runs, s) for s in args.scenarios},
    }
    (runs / "_gates_a3.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
