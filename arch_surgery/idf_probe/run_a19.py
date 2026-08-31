#!/usr/bin/env python
"""A19 (frozen-input-convergence) driver.

Two arms per scenario:

``control``
    probe switch unset -- the neutrality reference.  A19's replay mutates the
    data structure and restores it; if the restore is imperfect the MFILE
    moves, and this arm is what detects it.
``frozen``
    everything A2's ``modules`` instrument records (so the coupled-loop
    ``S_1``, ``S_2``, ``S_3`` are reproduced in the same run), plus the
    frozen-input replay on a sampled subset of ``call_models`` calls.

Every run is a fresh subprocess in its own working directory, and every
subprocess gets an explicit ``PYTHONPATH`` naming the tree under test (trap
T6).  The read census A2 needed for the coupler set is switched off here: A19
does not use it, and it costs several times the run.

Usage
-----
    python run_a19.py --scenarios large_tokamak_eval --arms control frozen
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
RUNS = HERE / "runs" / "a19"

SCENARIOS = [
    "large_tokamak_nof",
    "low_aspect_ratio_DEMO",
    "st_regression",
    "large_tokamak_eval",
]


def _env(extra: dict | None = None) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(TREE)  # T6
    env["MPLCONFIGDIR"] = str(RUNS / "_mplconfig")
    env.pop("PROCESS_IDF_PROBE", None)
    # A19 does not use the read census (A2 established the coupler set); it is
    # the dominant cost of the ``modules`` instrument.
    env["PROCESS_IDF_PROBE_READ_BUDGET"] = "0"
    env["PROCESS_IDF_PROBE_READ_STRIDE"] = "0"
    if extra:
        env.update({k: str(v) for k, v in extra.items()})
    return env


def run_one(scenario: str, arm: str, outdir: Path, extra: dict, mode: str) -> dict:
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(HERE / "run_one.py"),
        "--scenario", scenario,
        "--mode", mode,
        "--outdir", str(outdir),
        "--expect-tree", str(TREE),
    ]
    t0 = time.perf_counter()
    proc = subprocess.run(
        cmd, env=_env(extra), capture_output=True, text=True, cwd=str(outdir)
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
    ap.add_argument("--arms", nargs="*", default=["control", "frozen"])
    ap.add_argument("--grad-stride", type=int, default=10)
    ap.add_argument("--other-stride", type=int, default=1)
    ap.add_argument("--noinject", type=int, default=1)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / "_mplconfig").mkdir(exist_ok=True)

    extra = {
        "PROCESS_IDF_PROBE_FROZEN_GRAD_STRIDE": args.grad_stride,
        "PROCESS_IDF_PROBE_FROZEN_OTHER_STRIDE": args.other_stride,
        "PROCESS_IDF_PROBE_FROZEN_NOINJECT": args.noinject,
    }

    rows = []
    for scenario in args.scenarios:
        for arm in args.arms:
            name = f"{arm}{args.tag}"
            row = run_one(scenario, name, RUNS / scenario / name, extra, arm)
            print(
                f"  {scenario:22s} {name:16s} rc={row['returncode']} "
                f"{row['wall_s_subprocess']:8.1f}s",
                flush=True,
            )
            rows.append(row)

    log = RUNS / f"_driver_log{args.tag or ''}.json"
    log.write_text(json.dumps(rows, indent=2))
    return 0 if all(r["returncode"] == 0 for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
