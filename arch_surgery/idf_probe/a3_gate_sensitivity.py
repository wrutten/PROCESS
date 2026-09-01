#!/usr/bin/env python
"""A3: prove the gate comparator can fail.

Trap T11 records this project publishing a `0` without the condition that
limits it, and a gate that passes vacuously on an empty comparison set has
happened here before.  A zero mismatch count is only evidence if the same
comparator reports a non-zero one when there is something to find.

Two checks, both using ``compare_a3.compare_pair`` unmodified:

**1-ULP sensitivity.**  Copy the ``parent`` run directory, perturb exactly one
MFILE float by one unit in the last place -- the smallest change an IEEE-754
double admits, far below any printed-decimal resolution -- and re-run the
comparison.  It must report exactly one differing line and one differing float.

**Two genuinely different solves.**  Compare one scenario's ``parent`` MFILE
against another scenario's.  It must fail with a large count.

Usage:  python a3_gate_sensitivity.py --runs runs_a3
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from compare_a3 import _floats, _mfile_path, _VARNAME, compare_pair  # noqa: E402

#: A results line that is safe to perturb: a plain float, not run metadata.
TARGET = "(rmajor)"


def ulp_perturb(runs: Path, scenario: str) -> dict:
    src = runs / scenario / "parent"
    dst = runs / scenario / "_ulp"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

    path = _mfile_path(runs, scenario, "_ulp")
    text = path.read_text(errors="replace")
    out, done, before, after = [], False, None, None
    for ln in text.splitlines():
        parts = ln.split()
        if (
            not done
            and len(parts) >= 3
            and _VARNAME.match(parts[1])
            and parts[1].startswith(TARGET)
        ):
            try:
                v = float(parts[2])
            except ValueError:
                out.append(ln)
                continue
            w = math.nextafter(v, math.inf)
            before, after = v.hex(), w.hex()
            out.append(ln.replace(parts[2], f"{w:.17e}", 1))
            done = True
            continue
        out.append(ln)
    if not done:
        return {"status": "TARGET NOT FOUND", "target": TARGET}
    path.write_text("\n".join(out) + "\n")

    res = compare_pair(runs, scenario, "parent", "_ulp")
    n_before = len(_floats(_mfile_path(runs, scenario, "parent")))
    return {
        "target_variable": TARGET,
        "value_hex_before": before,
        "value_hex_after": after,
        "relative_change": abs(
            float.fromhex(after) - float.fromhex(before)
        ) / abs(float.fromhex(before)),
        "comparator_status": res["status"],
        "mfile_lines_differing": res["mfile_lines_differing"],
        "mfile_lines_compared": res["mfile_lines_compared"],
        "mfile_floats_differing": res["mfile_floats_differing"],
        "mfile_floats_compared": res["mfile_floats_compared"],
        "differing_keys": res["mfile_floats_differing_keys"],
        "denominator_floats_in_parent_mfile": n_before,
        "detected": res["status"] == "FAIL"
        and res["mfile_floats_differing"] == 1
        and res["mfile_lines_differing"] == 1,
    }


def cross_scenario(runs: Path, a: str, b: str) -> dict:
    """Compare two different scenarios' `parent` MFILEs: must fail loudly."""
    fa = _floats(_mfile_path(runs, a, "parent"))
    fb = _floats(_mfile_path(runs, b, "parent"))
    common = set(fa) & set(fb)
    diff = [k for k in common if fa[k] != fb[k]]
    return {
        "scenario_a": a,
        "scenario_b": b,
        "floats_compared": len(common),
        "floats_differing": len(diff),
        "detected": len(diff) > 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=str(HERE / "runs_a3"))
    ap.add_argument("--scenario", default="large_tokamak_nof")
    args = ap.parse_args()
    runs = Path(args.runs).resolve()
    result = {
        "ulp_sensitivity": {args.scenario: ulp_perturb(runs, args.scenario)},
        "cross_scenario": cross_scenario(
            runs, "large_tokamak_nof", "low_aspect_ratio_DEMO"
        ),
    }
    (runs / "_gate_sensitivity.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
