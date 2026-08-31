#!/usr/bin/env python
"""A2 (module-convergence) driver: Stage 1 of the MDA partitioning experiment.

Runs each scenario in three arms:

``control``
    probe switch unset -- the neutrality reference
``baseline``
    the Stage-0 probe (sweep anatomy only)
``modules``
    the Stage-1 instrument: per-module state attribution and a runtime census
    of cross-module reads and writes

Every run is a fresh subprocess in its own working directory (see
``run_one.py``'s module docstring), and every subprocess gets an explicit
``PYTHONPATH`` naming the tree under test -- trap T6, without which a worktree
measures the main checkout's code instead of its own.

Usage
-----
    python run_a2.py                      # all four scenarios, reps=1
    python run_a2.py --reps 3 --arms modules
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
RUNS = HERE / "runs" / "a2"

SCENARIOS = [
    "large_tokamak_nof",
    "low_aspect_ratio_DEMO",
    "st_regression",
    "large_tokamak_eval",
]


def _env() -> dict:
    env = dict(os.environ)
    # T6: name the tree explicitly for every subprocess.
    env["PYTHONPATH"] = str(TREE)
    env["MPLCONFIGDIR"] = str(RUNS / "_mplconfig")
    env.pop("PROCESS_IDF_PROBE", None)
    return env


def run_one(scenario: str, arm: str, outdir: Path) -> dict:
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    mode = "control" if arm.startswith("control") else arm.split("_rep")[0]
    cmd = [
        sys.executable,
        str(HERE / "run_one.py"),
        "--scenario",
        scenario,
        "--mode",
        mode,
        "--outdir",
        str(outdir),
        "--expect-tree",
        str(TREE),
    ]
    t0 = time.perf_counter()
    proc = subprocess.run(
        cmd, env=_env(), capture_output=True, text=True, cwd=str(outdir)
    )
    (outdir / "stdout.log").write_text(proc.stdout)
    (outdir / "stderr.log").write_text(proc.stderr)
    return {
        "scenario": scenario,
        "arm": arm,
        "returncode": proc.returncode,
        "wall_s_subprocess": time.perf_counter() - t0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    ap.add_argument("--arms", nargs="*", default=["control", "baseline", "modules"])
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--skip-warm", action="store_true")
    args = ap.parse_args()

    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / "_mplconfig").mkdir(exist_ok=True)

    if not args.skip_warm:
        print("Warming JIT caches (discarded):", flush=True)
        r = run_one("large_tokamak_nof", "control", RUNS / "_warmup")
        print(f"  warm rc={r['returncode']} {r['wall_s_subprocess']:.1f}s", flush=True)

    arms = []
    for stem in args.arms:
        arms.append(stem)
        arms.extend(f"{stem}_rep{i}" for i in range(2, args.reps + 1))

    rows = []
    for scenario in args.scenarios:
        for arm in arms:
            row = run_one(scenario, arm, RUNS / scenario / arm)
            print(
                f"  {scenario:22s} {arm:14s} rc={row['returncode']} "
                f"{row['wall_s_subprocess']:7.1f}s",
                flush=True,
            )
            rows.append(row)

    (RUNS / "_driver_log.json").write_text(json.dumps(rows, indent=2))
    return 0 if all(r["returncode"] == 0 for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
