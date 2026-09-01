#!/usr/bin/env python
"""A25 (phase-b-variant) driver: the equivalence gate, the delta calibration,
and the H5 multi-start campaign.

Arms
----
``baseline``
    **PROCESS as it currently is** (decision D14(c)): every variant point unset,
    the existing ``objf``/``conf`` idempotence predicate, the existing flat
    loop, the frozen scenario deck.  Not Phase A's reimplemented flat arm --
    that would compare two codebases where this comparison varies one thing.
``variant``
    The proposed architecture, all of it at once, because A19 established the
    pieces are not separable (``max S_i`` was unchanged when the coupler was
    pinned, so the lift alone buys nothing):

    * **VP1** ``PROCESS_ARCH_SEQUENCE=build_after_physics`` (A3) -- M1 becomes
      contiguous in the call order, without which no per-module block exists.
    * **VP5** ``PROCESS_ARCH_LIFT=burn_time`` (A24) plus a derived deck naming
      ``ixc = 178`` / ``icc = 93`` -- the burn time becomes a design variable
      and its residual an equality constraint.
    * **VP4** ``PROCESS_ARCH_MODULE_SOLVE=per_module`` (A25) -- per-module
      solves over M1 / M2 / M3 with Phase A's coupling-state predicate.
    * **VP2** ``PROCESS_ARCH_HOIST=feedforward`` (A13) -- the feed-forward tail
      runs once after the fixed point.  **Inside the variant** by decision
      D15(b), which is why the headline is *the proposed architecture* and
      never *the partition's benefit*.

``st_regression`` runs a **different variant**: modules and hoist, no lift,
because it has no burn-time coupler at all (``i_pulsed_plant = 0``, ``k = 0``,
and its measured PULSE write set is empty).  It is the control, not a fourth
replicate, and the driver records that per run rather than leaving it to a
report to remember.

Multi-start
-----------
Perturbations are applied by ``run_one.py``, keyed on the **iteration-variable
number** rather than on its position, so the two arms give bit-identical
factors to every variable they share even though the variant's design vector is
one longer.  Start 0 is the deck's own unperturbed point in both arms.

Isolation
---------
Every run is a fresh subprocess in its own working directory, ``PYTHONPATH``
pinned to this worktree, and the **exact** tree asserted inside the subprocess
(trap T6).  The first run in a fresh environment is discarded -- numba JIT
compilation dominates it.
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
TREE = HERE.parent.parent
DATA = TREE / "arch_surgery" / "docs" / "data"

SCENARIOS = [
    "large_tokamak_nof",
    "low_aspect_ratio_DEMO",
    "st_regression",
    "large_tokamak_eval",
]

#: Decks with a burn-time coupler.  ``st_regression`` has ``i_pulsed_plant = 0``
#: so ``Pulse`` writes nothing (measured: its PULSE write set is empty) and
#: there is nothing to lift.
PULSED = {"large_tokamak_nof", "low_aspect_ratio_DEMO", "large_tokamak_eval"}


def deck_for(scenario: str, arm: str, decks: Path) -> Path:
    if arm.startswith("variant") and scenario in PULSED:
        return decks / scenario / f"{scenario}_lifted.IN.DAT"
    return HERE / "scenarios" / f"{scenario}.IN.DAT"


def env_for(scenario: str, arm: str, runs: Path, tau: float) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(TREE)
    env["MPLCONFIGDIR"] = str(runs / "_mplconfig")
    for k in (
        "PROCESS_IDF_PROBE",
        "PROCESS_ARCH_SEQUENCE",
        "PROCESS_ARCH_HOIST",
        "PROCESS_ARCH_LIFT",
        "PROCESS_ARCH_MODULE_SOLVE",
        "PROCESS_ARCH_TAU",
        "PROCESS_ARCH_YSTATE",
        "PROCESS_ARCH_WRITESET",
    ):
        env.pop(k, None)
    if arm.startswith("variant"):
        env["PROCESS_ARCH_SEQUENCE"] = "build_after_physics"
        # ``variant_nohoist`` is the excluding arm D15(b) defers: the proposed
        # architecture minus VP2, so the hoist's share of the combined figure is
        # measured inside this variant rather than quoted from A13's flat-arm
        # measurement of a different architecture.
        if arm != "variant_nohoist":
            env["PROCESS_ARCH_HOIST"] = "feedforward"
        env["PROCESS_ARCH_MODULE_SOLVE"] = "per_module"
        env["PROCESS_ARCH_TAU"] = repr(tau)
        env["PROCESS_ARCH_YSTATE"] = str(DATA / f"ystate_{scenario}.json")
        env["PROCESS_ARCH_WRITESET"] = str(DATA / f"writeset_{scenario}.json")
        if scenario in PULSED:
            env["PROCESS_ARCH_LIFT"] = "burn_time"
    return env


def run_one(
    scenario: str,
    arm: str,
    outdir: Path,
    runs: Path,
    decks: Path,
    *,
    tau: float,
    delta: float | None = None,
    seed: int = 0,
    timeout: int = 3600,
) -> dict:
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(HERE / "run_one.py"),
        "--scenario", scenario,
        "--mode", "control",
        "--outdir", str(outdir),
        "--expect-tree", str(TREE),
        "--input", str(deck_for(scenario, arm, decks)),
    ]
    if delta is not None:
        cmd += ["--perturb-delta", repr(delta), "--perturb-seed", str(seed)]
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd,
            env=env_for(scenario, arm, runs, tau),
            capture_output=True,
            text=True,
            cwd=str(outdir),
            timeout=timeout,
        )
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        rc, out, err = 124, exc.stdout or "", (exc.stderr or "") + "\nTIMEOUT"
    (outdir / "stdout.log").write_text(out if isinstance(out, str) else out.decode())
    (outdir / "stderr.log").write_text(err if isinstance(err, str) else err.decode())
    if rc == 124 and not (outdir / "metrics.json").exists():
        # A timeout leaves no metrics; write a row so the census sees the start
        # rather than silently losing it.
        (outdir / "metrics.json").write_text(json.dumps({
            "scenario": scenario, "mode": "control", "status": "timeout",
            "perturb_delta": delta, "perturb_seed": seed,
        }, indent=2))
    return {
        "scenario": scenario,
        "arm": arm,
        "seed": seed,
        "delta": delta,
        "rc": rc,
        "wall_s": time.perf_counter() - t0,
    }


def warm(runs: Path, decks: Path, tau: float) -> None:
    """Discarded first run: numba JIT compilation dominates a cold process."""
    wd = runs / "_warmup"
    print("Warming JIT caches (discarded):", flush=True)
    r = run_one("large_tokamak_nof", "baseline", wd, runs, decks, tau=tau)
    print(f"  rc={r['rc']} {r['wall_s']:.1f}s", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "mode", choices=["gate", "calibrate", "campaign"],
    )
    ap.add_argument("--runs", default=str(HERE / "runs" / "a25"))
    ap.add_argument("--decks", default=None, help="directory of derived decks")
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    ap.add_argument(
        "--arms", nargs="*",
        default=["baseline", "variant", "variant_nohoist"],
    )
    ap.add_argument("--tau", type=float, default=1e-6)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--starts", type=int, default=24)
    ap.add_argument("--deltas", nargs="*", type=float, default=[0.01, 0.05, 0.10])
    ap.add_argument("--delta", type=float, default=None)
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--skip-warm", action="store_true")
    args = ap.parse_args()

    runs = Path(args.runs).resolve()
    runs.mkdir(parents=True, exist_ok=True)
    (runs / "_mplconfig").mkdir(exist_ok=True)
    decks = Path(args.decks).resolve() if args.decks else runs / "_decks"

    if not args.skip_warm:
        warm(runs, decks, args.tau)

    jobs: list[tuple] = []
    if args.mode == "gate":
        root = runs / "gate"
        for s in args.scenarios:
            for a in args.arms:
                jobs.append((s, a, root / s / a, None, 0))
    elif args.mode == "calibrate":
        root = runs / "calibrate"
        for s in args.scenarios:
            for d in args.deltas:
                tag = f"delta{int(round(d * 1000)):04d}"
                for k in range(1, args.starts + 1):
                    jobs.append(
                        (s, "baseline", root / s / tag / f"start{k:03d}", d, k)
                    )
    else:
        if args.delta is None:
            raise SystemExit("campaign needs --delta from the calibration")
        root = runs / "h5"
        for s in args.scenarios:
            for a in args.arms:
                for k in range(0, args.starts + 1):
                    jobs.append(
                        (s, a, root / s / a / f"start{k:03d}", args.delta, k)
                    )

    print(f"{args.mode}: {len(jobs)} runs, {args.jobs} at a time", flush=True)
    log: list[dict] = []
    t0 = time.perf_counter()

    def do(job):
        s, a, outdir, d, k = job
        r = run_one(
            s, a, outdir, runs, decks,
            tau=args.tau, delta=d, seed=k, timeout=args.timeout,
        )
        print(
            f"  {s:22s} {a:9s} d={d} k={k:3d} rc={r['rc']} "
            f"{r['wall_s']:6.1f}s",
            flush=True,
        )
        return r

    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        log.extend(ex.map(do, jobs))

    print(f"total {time.perf_counter() - t0:.1f}s", flush=True)
    (runs / f"_driver_log_{args.mode}.json").write_text(json.dumps(log, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
