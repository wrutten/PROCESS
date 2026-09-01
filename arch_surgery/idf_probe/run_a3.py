#!/usr/bin/env python
"""A3 (build-reorder) driver: three arms x four scenarios, isolated runs.

Arms
----
parent
    A ``git archive`` extraction of this branch's parent commit, with
    ``PROCESS_ARCH_SEQUENCE`` absent from the code entirely.  The reference.
default
    This branch, ``PROCESS_ARCH_SEQUENCE`` unset -- the upstream order,
    reached through the VP1 list.  ``default`` vs ``parent`` is the
    default-path neutrality check.
reordered
    This branch, ``PROCESS_ARCH_SEQUENCE=build_after_physics`` -- ``build``
    moved to the head of M2's span.  ``reordered`` vs ``parent`` is the A3
    gate.

Each arm is run twice: once with the probe switch unset (``control``), which is
the arm the MFILE comparison uses, and once with ``PROCESS_IDF_PROBE=baseline``,
which is where the sweep counts come from.

Every run is a fresh subprocess in its own working directory; see the module
docstring of ``run_one.py`` for why that is mandatory.  ``PYTHONPATH`` is set to
the tree under test for every run and ``run_one.py`` asserts the *exact* tree it
imported (trap T6).
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

SCENARIOS = [
    "large_tokamak_nof",
    "low_aspect_ratio_DEMO",
    "st_regression",
    "large_tokamak_eval",
]

#: (arm, tree key, probe mode, PROCESS_ARCH_SEQUENCE value or None)
ARMS = [
    ("parent", "parent", "control", None),
    ("default", "surgery", "control", None),
    ("reordered", "surgery", "control", "build_after_physics"),
    ("parent_probe", "parent", "baseline", None),
    ("default_probe", "surgery", "baseline", None),
    ("reordered_probe", "surgery", "baseline", "build_after_physics"),
]

#: Arms for the run-time sequence census (a3_sequence_census.py).
CENSUS_ARMS = [
    ("parent", "parent", None),
    ("default", "surgery", None),
    ("reordered", "surgery", "build_after_physics"),
]


def _env(tree: Path, seq: str | None, runs: Path) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(tree)
    env["MPLCONFIGDIR"] = str(runs / "_mplconfig")
    env.pop("PROCESS_IDF_PROBE", None)
    env.pop("PROCESS_ARCH_SEQUENCE", None)
    if seq is not None:
        env["PROCESS_ARCH_SEQUENCE"] = seq
    return env


def _run(cmd, tree, seq, outdir, runs):
    outdir.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    proc = subprocess.run(
        cmd,
        env=_env(tree, seq, runs),
        capture_output=True,
        text=True,
        cwd=str(outdir),
    )
    (outdir / "stdout.log").write_text(proc.stdout)
    (outdir / "stderr.log").write_text(proc.stderr)
    return proc.returncode, time.perf_counter() - t0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parent-tree", required=True)
    ap.add_argument("--runs", default=str(HERE / "runs_a3"))
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--skip-warm", action="store_true")
    ap.add_argument("--census-only", action="store_true")
    args = ap.parse_args()

    runs = Path(args.runs).resolve()
    trees = {"surgery": SURGERY_TREE, "parent": Path(args.parent_tree).resolve()}
    runs.mkdir(parents=True, exist_ok=True)
    (runs / "_mplconfig").mkdir(exist_ok=True)

    def gate_cmd(scenario, arm, tree):
        return [
            sys.executable,
            str(HERE / "run_one.py"),
            "--scenario",
            scenario,
            "--mode",
            arm,
            "--outdir",
            str(runs / scenario / arm),
            "--expect-tree",
            str(tree),
        ]

    if not args.skip_warm:
        # Discarded run: numba JIT compilation dominates a cold run.
        print("Warming JIT caches (discarded):", flush=True)
        for key, tree in trees.items():
            wd = runs / "_warmup" / key
            if wd.exists():
                shutil.rmtree(wd)
            rc, dt = _run(
                gate_cmd("large_tokamak_nof", "control", tree), tree, None, wd, runs
            )
            print(f"  warm {key}: rc={rc} {dt:.1f}s", flush=True)

    log = []

    def do_scenario(scenario):
        rows = []
        if not args.census_only:
            for arm, tkey, mode, seq in ARMS:
                outdir = runs / scenario / arm
                if outdir.exists():
                    shutil.rmtree(outdir)
                cmd = gate_cmd(scenario, mode, trees[tkey])
                cmd[cmd.index("--outdir") + 1] = str(outdir)
                rc, dt = _run(cmd, trees[tkey], seq, outdir, runs)
                print(f"  {scenario:22s} {arm:16s} rc={rc} {dt:6.1f}s", flush=True)
                rows.append({"scenario": scenario, "arm": arm, "rc": rc, "wall_s": dt})
        for arm, tkey, seq in CENSUS_ARMS:
            outdir = runs / scenario / f"census_{arm}"
            if outdir.exists():
                shutil.rmtree(outdir)
            cmd = [
                sys.executable,
                str(HERE / "a3_sequence_census.py"),
                "--scenario",
                scenario,
                "--outdir",
                str(outdir),
                "--expect-tree",
                str(trees[tkey]),
            ]
            rc, dt = _run(cmd, trees[tkey], seq, outdir, runs)
            print(f"  {scenario:22s} census_{arm:9s} rc={rc} {dt:6.1f}s", flush=True)
            rows.append({
                "scenario": scenario,
                "arm": f"census_{arm}",
                "rc": rc,
                "wall_s": dt,
            })
        return rows

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        for rows in ex.map(do_scenario, args.scenarios):
            log.extend(rows)
    print(f"total {time.perf_counter() - t0:.1f}s", flush=True)
    (runs / "_driver_log.json").write_text(json.dumps(log, indent=2))
    return 0 if all(r["rc"] == 0 for r in log) else 1


if __name__ == "__main__":
    raise SystemExit(main())
