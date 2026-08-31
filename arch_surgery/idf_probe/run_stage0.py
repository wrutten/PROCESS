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
baseline_rep2 ... baseline_repN
    Further independent ``baseline`` runs.  ``baseline_rep2`` is the reference
    for gate (b); the rest exist so wall clock can be quoted with a spread.
control_rep2 ... control_repN
    Further independent ``control`` runs, so that probe overhead is compared
    between two samples of equal size rather than one run against one run.

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

#: How many independent replicates of `control` and of `baseline` to run.
#: Two bit-identical runs of this code differ by up to ~8 % in wall clock
#: (issue I-8), so a single run is not a timing measurement.  Gates (a) and
#: (b) need only the first two; the extra replicates exist so that the wall
#: clock can be quoted with a spread and an n.
DEFAULT_REPS = 5


def build_arms(reps: int) -> list[tuple[str, str]]:
    """(arm name, tree selector) pairs.

    `pristine` is an untouched checkout of the base commit and is the
    reference for gate (a); one run of it is enough, because it is compared
    for identity, not for time.
    """
    arms = [("pristine", "pristine")]
    for stem in ("control", "baseline"):
        arms.append((stem, "surgery"))
        arms.extend((f"{stem}_rep{i}", "surgery") for i in range(2, reps + 1))
    return arms


ARMS = build_arms(DEFAULT_REPS)


def _env(tree: Path) -> dict:
    """Environment for one run.

    The interpreter is expected to be an environment whose editable install
    already points at this tree (`PROCESS_surgery_env`), so nothing is
    injected for the surgery arms -- runs resolve `process` exactly the way
    every later stage will.  `PYTHONPATH` is set *only* for a tree that is not
    the installed one, which in practice is the `pristine` arm's throwaway
    checkout of the base commit: there is no other way to import a tree that
    is not installed.  Either way `run_one.py` asserts which tree it actually
    imported (`--expect-tree`) and aborts before doing any work if it is
    wrong -- a standing rule, not a workaround.
    """
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    if tree != SURGERY_TREE:
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
    ap.add_argument(
        "--reps",
        type=int,
        default=DEFAULT_REPS,
        help="independent replicates of `control` and of `baseline` (default "
        f"{DEFAULT_REPS}); >= 2 is required by gate (b)",
    )
    ap.add_argument("--skip-warm", action="store_true")
    args = ap.parse_args()

    if args.reps < 2:
        raise SystemExit("--reps must be at least 2: gate (b) needs two baseline runs")
    arms = build_arms(args.reps)
    trees = {"surgery": SURGERY_TREE, "pristine": Path(args.pristine_tree).resolve()}
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / "_mplconfig").mkdir(exist_ok=True)

    if not args.skip_warm:
        print("Warming JIT caches (these runs are discarded):", flush=True)
        for name, tree in trees.items():
            warm(tree, RUNS / "_warmup" / name)

    def do_scenario(scenario: str) -> list:
        rows = []
        for arm, tree_key in arms:
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
