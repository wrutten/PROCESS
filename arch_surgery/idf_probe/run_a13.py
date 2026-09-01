#!/usr/bin/env python
"""A13 (feedforward-hoist) driver: three arms x four scenarios, isolated runs.

Arms
----
parent
    A ``git archive`` extraction of this branch's parent commit, in which
    ``PROCESS_ARCH_HOIST`` does not exist in the code at all.  The reference.
default
    This branch, ``PROCESS_ARCH_HOIST`` unset.  ``default`` vs ``parent`` is
    the switch-neutrality gate.
hoisted
    This branch, ``PROCESS_ARCH_HOIST=feedforward``.  ``hoisted`` vs ``parent``
    is the correctness gate.

Each arm runs twice -- once with the probe switch unset (``control``, which is
the arm the MFILE comparison uses) and once with ``PROCESS_IDF_PROBE=baseline``
(where the sweep counts come from) -- plus a node census, which is where the
model-evaluation counts come from.

Every run is a fresh subprocess in its own working directory; see the module
docstring of ``run_one.py`` for why that is mandatory.  ``PYTHONPATH`` is set to
the tree under test for every run and every script asserts the *exact* tree it
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

#: (arm, tree key, probe mode, PROCESS_ARCH_HOIST value or None)
ARMS = [
    ("parent", "parent", "control", None),
    ("default", "surgery", "control", None),
    ("hoisted", "surgery", "control", "feedforward"),
    ("parent_probe", "parent", "baseline", None),
    ("default_probe", "surgery", "baseline", None),
    ("hoisted_probe", "surgery", "baseline", "feedforward"),
]

#: (arm, tree key, PROCESS_ARCH_HOIST value or None) for the node census.
CENSUS_ARMS = [
    ("parent", "parent", None),
    ("default", "surgery", None),
    ("hoisted", "surgery", "feedforward"),
]


def _env(tree: Path, hoist: str | None, runs: Path) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(tree)
    env["MPLCONFIGDIR"] = str(runs / "_mplconfig")
    env.pop("PROCESS_IDF_PROBE", None)
    env.pop("PROCESS_ARCH_SEQUENCE", None)
    env.pop("PROCESS_ARCH_HOIST", None)
    if hoist is not None:
        env["PROCESS_ARCH_HOIST"] = hoist
    return env


def _run(cmd, tree, hoist, outdir, runs):
    outdir.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    proc = subprocess.run(
        cmd,
        env=_env(tree, hoist, runs),
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
    ap.add_argument("--runs", default=str(HERE / "runs" / "a13"))
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--skip-warm", action="store_true")
    ap.add_argument("--census-only", action="store_true")
    ap.add_argument("--writeset-only", action="store_true")
    args = ap.parse_args()

    runs = Path(args.runs).resolve()
    trees = {"surgery": SURGERY_TREE, "parent": Path(args.parent_tree).resolve()}
    runs.mkdir(parents=True, exist_ok=True)
    (runs / "_mplconfig").mkdir(exist_ok=True)

    def gate_cmd(scenario, mode, tree, outdir):
        return [
            sys.executable,
            str(HERE / "run_one.py"),
            "--scenario", scenario,
            "--mode", mode,
            "--outdir", str(outdir),
            "--expect-tree", str(tree),
        ]

    if not args.skip_warm:
        # Discarded run: numba JIT compilation dominates a cold run.
        print("Warming JIT caches (discarded):", flush=True)
        for key, tree in trees.items():
            wd = runs / "_warmup" / key
            if wd.exists():
                shutil.rmtree(wd)
            rc, dt = _run(
                gate_cmd("large_tokamak_nof", "control", tree, wd), tree, None, wd, runs
            )
            print(f"  warm {key}: rc={rc} {dt:.1f}s", flush=True)

    log = []

    def do_scenario(scenario):
        rows = []
        if not args.census_only and not args.writeset_only:
            for arm, tkey, mode, hoist in ARMS:
                outdir = runs / scenario / arm
                if outdir.exists():
                    shutil.rmtree(outdir)
                rc, dt = _run(
                    gate_cmd(scenario, mode, trees[tkey], outdir),
                    trees[tkey], hoist, outdir, runs,
                )
                print(f"  {scenario:22s} {arm:16s} rc={rc} {dt:6.1f}s", flush=True)
                rows.append({"scenario": scenario, "arm": arm, "rc": rc, "wall_s": dt})
        if not args.writeset_only:
            for arm, tkey, hoist in CENSUS_ARMS:
                outdir = runs / scenario / f"census_{arm}"
                if outdir.exists():
                    shutil.rmtree(outdir)
                cmd = [
                    sys.executable,
                    str(HERE / "a13_node_census.py"),
                    "--scenario", scenario,
                    "--outdir", str(outdir),
                    "--expect-tree", str(trees[tkey]),
                ]
                rc, dt = _run(cmd, trees[tkey], hoist, outdir, runs)
                print(f"  {scenario:22s} census_{arm:9s} rc={rc} {dt:6.1f}s", flush=True)
                rows.append({
                    "scenario": scenario, "arm": f"census_{arm}", "rc": rc, "wall_s": dt,
                })
        if not args.census_only:
            outdir = runs / scenario / "writeset"
            if outdir.exists():
                shutil.rmtree(outdir)
            cmd = [
                sys.executable,
                str(HERE / "a13_tail_writeset.py"),
                "--scenario", scenario,
                "--outdir", str(outdir),
                "--expect-tree", str(trees["surgery"]),
            ]
            rc, dt = _run(cmd, trees["surgery"], None, outdir, runs)
            print(f"  {scenario:22s} {'writeset':16s} rc={rc} {dt:6.1f}s", flush=True)
            rows.append({
                "scenario": scenario, "arm": "writeset", "rc": rc, "wall_s": dt,
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
