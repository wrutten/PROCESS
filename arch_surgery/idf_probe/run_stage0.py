#!/usr/bin/env python
"""Stage-0 driver: warm the JIT caches, then run every (scenario, arm) pair.

Each run is a fresh subprocess in its own working directory (see the module
docstring of ``run_one.py`` for why that is mandatory).  Scenarios run in
parallel; the arms within a scenario run in sequence, so that timings within a
scenario are taken under comparable machine load.

Arms
----
pristine
    An untouched checkout of the base commit, probe module absent entirely.
    The reference for gate (a).
control
    The instrumented tree with ``PROCESS_IDF_PROBE`` unset.
baseline
    The instrumented tree with ``PROCESS_IDF_PROBE=baseline``.
baseline_rep2
    A second, independent ``baseline`` run.  The reference for gate (b).

Usage
-----
    python run_stage0.py --pristine-tree /path/to/c0ae5b28/checkout
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
SURGERY_TREE = HERE.parent.parent
RUNS = HERE / "runs"

SCENARIOS = [
    "large_tokamak_nof",
    "low_aspect_ratio_DEMO",
    "st_regression",
    "large_tokamak_eval",
]

# (arm name, tree selector)
ARMS = [
    ("pristine", "pristine"),
    ("control", "surgery"),
    ("baseline", "surgery"),
    ("baseline_rep2", "surgery"),
]


def _env(tree: Path) -> dict:
    env = dict(os.environ)
    # THE setup fix.  `pip show process` points the editable install at
    # /home/wrutten/dev_libraries/PROCESS, a different clone at a different
    # commit.  PYTHONPATH precedes site-packages .pth entries in sys.path, so
    # this wins; run_one.py then asserts which tree it actually imported.
    env["PYTHONPATH"] = str(tree)
    env["MPLCONFIGDIR"] = str(RUNS / "_mplconfig")
    env.pop("PROCESS_IDF_PROBE", None)
    return env


def run_one(scenario: str, arm: str, tree: Path, outdir: Path) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(HERE / "run_one.py"),
        "--scenario",
        scenario,
        "--mode",
        "control" if arm.startswith("control") else arm,
        "--outdir",
        str(outdir),
        "--expect-tree",
        str(tree),
    ]
    t0 = time.perf_counter()
    proc = subprocess.run(
        cmd, env=_env(tree), capture_output=True, text=True, cwd=str(outdir)
    )
    (outdir / "stdout.log").write_text(proc.stdout)
    (outdir / "stderr.log").write_text(proc.stderr)
    return {
        "scenario": scenario,
        "arm": arm,
        "returncode": proc.returncode,
        "wall_s_subprocess": time.perf_counter() - t0,
    }


def warm(tree: Path, workdir: Path, scenario: str = "large_tokamak_nof") -> float:
    """Discarded run: numba JIT compilation dominates a cold run."""
    if workdir.exists():
        shutil.rmtree(workdir)
    t0 = time.perf_counter()
    r = run_one(scenario, "control", tree, workdir)
    dt = time.perf_counter() - t0
    print(f"  warm {tree.name}: rc={r['returncode']} {dt:.1f}s", flush=True)
    return dt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pristine-tree", required=True)
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--skip-warm", action="store_true")
    args = ap.parse_args()

    trees = {"surgery": SURGERY_TREE, "pristine": Path(args.pristine_tree).resolve()}
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / "_mplconfig").mkdir(exist_ok=True)

    if not args.skip_warm:
        print("Warming JIT caches (these runs are discarded):", flush=True)
        for name, tree in trees.items():
            warm(tree, RUNS / "_warmup" / name)

    def do_scenario(scenario: str) -> list:
        rows = []
        for arm, tree_key in ARMS:
            outdir = RUNS / scenario / arm
            if outdir.exists():
                shutil.rmtree(outdir)
            row = run_one(scenario, arm, trees[tree_key], outdir)
            print(
                f"  {scenario:22s} {arm:14s} rc={row['returncode']} "
                f"{row['wall_s_subprocess']:6.1f}s",
                flush=True,
            )
            rows.append(row)
        return rows

    print("Running arms:", flush=True)
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        results = list(ex.map(do_scenario, args.scenarios))
    print(f"total {time.perf_counter() - t0:.1f}s", flush=True)

    flat = [r for rows in results for r in rows]
    (RUNS / "_driver_log.json").write_text(json.dumps(flat, indent=2))
    return 0 if all(r["returncode"] == 0 for r in flat) else 1


if __name__ == "__main__":
    raise SystemExit(main())
