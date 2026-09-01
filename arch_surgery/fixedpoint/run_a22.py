#!/usr/bin/env python
"""A22 (outer-pass-census) driver: one census subprocess per scenario.

Reuses A18's harvested design points rather than re-harvesting.  That reuse is
legitimate only because the two trees are the same tree: ``arch_surgery/
fixedpoint`` and ``arch_surgery/docs/data/dsm_node_map.json`` are identical
between A18's commit and this branch's base, and ``process/`` has the same git
tree hash, so the models being replayed are the models that were harvested.
The harvest path is taken as an argument so that this is visible at the call
site rather than assumed.

Every subprocess is fresh, has its own working directory, gets an explicit
``PYTHONPATH`` naming the tree under test, and asserts the **exact** tree it
imported (trap T6: in a ``git worktree`` the editable install still points at
the main checkout).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parent.parent
PROBE = TREE / "arch_surgery" / "idf_probe"
RUNS = PROBE / "runs" / "a22"
SCENARIOS_DIR = PROBE / "scenarios"

SCENARIOS = [
    "large_tokamak_nof",
    "low_aspect_ratio_DEMO",
    "st_regression",
    "large_tokamak_eval",
]

TAU = 1e-6


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a18-runs", required=True,
                    help="A18's runs/a18 directory: the harvests and the gate")
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    ap.add_argument("--tau", type=float, default=TAU)
    ap.add_argument("--max-points", type=int, default=0)
    args = ap.parse_args()

    a18 = Path(args.a18_runs).resolve()
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / "_mplconfig").mkdir(exist_ok=True)

    rows = []
    for s in args.scenarios:
        out = RUNS / s
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)
        shutil.copy(SCENARIOS_DIR / f"{s}.IN.DAT", out / f"{s}.IN.DAT")
        harvest = a18 / s / "harvest" / "harvest.pkl"
        ref = a18 / s / f"replay_tau{args.tau:g}_hoist0" / "result.json"
        if not harvest.exists():
            print(f"  MISSING harvest for {s}: {harvest}", flush=True)
            rows.append({"scenario": s, "returncode": 127})
            continue
        cmd = [
            sys.executable, str(HERE / "a22_census.py"),
            "--harvest", str(harvest),
            "--scenario", s,
            "--input", f"{s}.IN.DAT",
            "--out", str(out / "census.json"),
            "--expect-tree", str(TREE),
            "--tau", repr(args.tau),
        ]
        if ref.exists():
            cmd += ["--a18", str(ref)]
        if args.max_points:
            cmd += ["--max-points", str(args.max_points)]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(TREE)
        env["MPLCONFIGDIR"] = str(RUNS / "_mplconfig")
        env.pop("PROCESS_IDF_PROBE", None)
        t0 = time.perf_counter()
        proc = subprocess.run(cmd, env=env, cwd=str(out), capture_output=True,
                              text=True)
        (out / "run.stdout.log").write_text(proc.stdout)
        (out / "run.stderr.log").write_text(proc.stderr)
        rows.append({"scenario": s, "returncode": proc.returncode,
                     "wall_s": time.perf_counter() - t0})
        print(f"  census {s:24s} rc={proc.returncode}", flush=True)
        print(proc.stdout[-2000:] if proc.returncode == 0
              else proc.stderr[-3000:], flush=True)
    (RUNS / "_log.json").write_text(json.dumps(rows, indent=2))
    return 0 if all(r["returncode"] == 0 for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
