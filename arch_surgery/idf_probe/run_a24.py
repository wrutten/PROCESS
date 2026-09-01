#!/usr/bin/env python
"""A24 (phase-b-scaffold) driver: two arms x four scenarios, isolated runs.

Arms
----
parent
    A ``git archive`` extraction of this branch's parent commit, in which none
    of the three scaffolding pieces exists -- no ``PROCESS_ARCH_LIFT``, no
    iteration variable 178, no constraint 93.  The reference.
default
    This branch, every new switch unset.

The whole bundle is inert by construction: the registry entries are named by
no deck, the VP5 seam defaults to the model's own solve, and the gate harness
is not in the solve path.  So ``default`` against ``parent`` must be
bit-identical, and any difference at all is a defect in the scaffolding rather
than a finding.

Each arm runs twice -- once with the probe switch unset (``control``, the arm
the MFILE comparison uses) and once with ``PROCESS_IDF_PROBE=baseline``, where
the sweep counts come from.  A seam probe runs once per tree and reports what
the code resolved rather than what the driver asked for.

Every run is a fresh subprocess in its own working directory: ``OutputFileManager``
holds its file handles as class attributes and initialisation mutates a global
data structure, so two runs in one interpreter contaminate each other.
``PYTHONPATH`` is set to the tree under test for every run and every script
asserts the *exact* tree it imported (trap T6 -- the editable install points at
the main checkout, so a worktree's code is imported only when ``PYTHONPATH``
says so, and a prefix test would pass on the wrong tree).
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

#: (arm, tree key, probe mode, PROCESS_ARCH_LIFT value or None)
ARMS = [
    ("parent", "parent", "control", None),
    ("default", "surgery", "control", None),
    ("parent_probe", "parent", "baseline", None),
    ("default_probe", "surgery", "baseline", None),
]


def _env(tree: Path, lift: str | None, runs: Path) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(tree)
    env["MPLCONFIGDIR"] = str(runs / "_mplconfig")
    env.pop("PROCESS_IDF_PROBE", None)
    env.pop("PROCESS_ARCH_SEQUENCE", None)
    env.pop("PROCESS_ARCH_HOIST", None)
    env.pop("PROCESS_ARCH_LIFT", None)
    if lift is not None:
        env["PROCESS_ARCH_LIFT"] = lift
    return env


def _run(cmd, tree, lift, outdir, runs):
    outdir.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    proc = subprocess.run(
        cmd,
        env=_env(tree, lift, runs),
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
    ap.add_argument("--runs", default=str(HERE / "runs" / "a24"))
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--skip-warm", action="store_true")
    ap.add_argument("--seam-only", action="store_true")
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

    log = []

    # -- the seam probe: what the code resolved, per tree and per lift arm ---
    # ``lifted`` is not a gate arm.  It exists so that the claim "with nothing
    # selected the seam is a call-through" is measured against its own
    # counterfactual rather than asserted.
    seam_jobs = [
        ("seam_default", "surgery", None),
        ("seam_lifted", "surgery", "burn_time"),
    ]
    for name, tkey, lift in seam_jobs:
        outdir = runs / "_seam" / name
        if outdir.exists():
            shutil.rmtree(outdir)
        cmd = [
            sys.executable,
            str(HERE / "a24_seam_probe.py"),
            "--outdir", str(outdir),
            "--expect-tree", str(trees[tkey]),
        ]
        if lift is not None:
            cmd.append("--skip-bad-arm")
        rc, dt = _run(cmd, trees[tkey], lift, outdir, runs)
        print(f"  {name:22s} rc={rc} {dt:6.1f}s", flush=True)
        log.append({"scenario": "-", "arm": name, "rc": rc, "wall_s": dt})

    if args.seam_only:
        (runs / "_driver_log.json").write_text(json.dumps(log, indent=2))
        return 0 if all(r["rc"] == 0 for r in log) else 1

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

    def do_scenario(scenario):
        rows = []
        for arm, tkey, mode, lift in ARMS:
            outdir = runs / scenario / arm
            if outdir.exists():
                shutil.rmtree(outdir)
            rc, dt = _run(
                gate_cmd(scenario, mode, trees[tkey], outdir),
                trees[tkey], lift, outdir, runs,
            )
            print(f"  {scenario:22s} {arm:16s} rc={rc} {dt:6.1f}s", flush=True)
            rows.append({"scenario": scenario, "arm": arm, "rc": rc, "wall_s": dt})
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
