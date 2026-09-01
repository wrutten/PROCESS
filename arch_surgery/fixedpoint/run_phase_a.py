#!/usr/bin/env python
"""Phase A driver: harvest, gates, tau ladder, arm comparison.

Every PROCESS run is a **fresh subprocess in its own working directory**, run
**serially** (trap T8: ``ps`` and ``pkill`` do not work across sandboxed Bash
calls, so overlapping runs cannot be detected or stopped -- they are never
started).  Every subprocess gets an explicit ``PYTHONPATH`` naming the tree
under test and asserts the **exact** tree it imported (trap T6).

Subcommands
-----------
``harvest``   one instrumented run per scenario; writes the design-point cache
``gates``     neutrality, determinism, harvest inertness
``ladder``    the tau calibration ladder -- **run this first**, it is a one-off
``replay``    the arm comparison at a chosen tau

Usage
-----
    python run_phase_a.py harvest --scenarios large_tokamak_nof
    python run_phase_a.py ladder  --scenarios large_tokamak_nof
    python run_phase_a.py replay  --scenarios large_tokamak_nof --tau 1e-6
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
RUNS = PROBE / "runs" / "a18"
SCENARIOS_DIR = PROBE / "scenarios"

SCENARIOS = [
    "large_tokamak_nof",
    "low_aspect_ratio_DEMO",
    "st_regression",
    "large_tokamak_eval",
]

#: The ladder is a one-off calibration, not a per-arm setting.  tau must be
#: *identical* across arms or the comparison is not paired.
LADDER_TAUS = (1e-4, 1e-6, 1e-8)


def _env(extra: dict | None = None, tree: Path = TREE) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(tree)  # T6
    env["MPLCONFIGDIR"] = str(RUNS / "_mplconfig")
    env.pop("PROCESS_IDF_PROBE", None)
    # A18 does not use A2's read census (the coupler set is already measured)
    # and it is the dominant cost of the ``modules`` instrument.
    env["PROCESS_IDF_PROBE_READ_BUDGET"] = "0"
    env["PROCESS_IDF_PROBE_READ_STRIDE"] = "0"
    if extra:
        env.update({k: str(v) for k, v in extra.items()})
    return env


def _run(cmd, cwd: Path, env: dict, log: Path) -> dict:
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, env=env, cwd=str(cwd), capture_output=True, text=True)
    log.with_suffix(".stdout.log").write_text(proc.stdout)
    log.with_suffix(".stderr.log").write_text(proc.stderr)
    return {
        "returncode": proc.returncode,
        "wall_s_subprocess": time.perf_counter() - t0,
    }


# --------------------------------------------------------------------------
# harvest
# --------------------------------------------------------------------------


def cmd_harvest(args) -> int:
    rows = []
    for s in args.scenarios:
        out = RUNS / s / "harvest"
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)
        cmd = [
            sys.executable,
            str(PROBE / "run_one.py"),
            "--scenario", s,
            "--mode", "harvest",
            "--outdir", str(out),
            "--expect-tree", str(TREE),
        ]
        env = _env({
            "PROCESS_IDF_PROBE_HARVEST_OUT": str(out / "harvest.pkl"),
            "PROCESS_IDF_PROBE_HARVEST_GRAD_STRIDE": args.grad_stride,
            "PROCESS_IDF_PROBE_HARVEST_OTHER_STRIDE": args.other_stride,
        })
        r = _run(cmd, out, env, out / "run")
        r.update({"scenario": s, "arm": "harvest"})
        print(f"  harvest {s:24s} rc={r['returncode']} {r['wall_s_subprocess']:7.1f}s",
              flush=True)
        rows.append(r)
    (RUNS / "_harvest_log.json").write_text(json.dumps(rows, indent=2))
    return 0 if all(r["returncode"] == 0 for r in rows) else 1


# --------------------------------------------------------------------------
# gates
# --------------------------------------------------------------------------


def cmd_gates(args) -> int:
    """Neutrality, determinism and harvest inertness, all bit-comparisons."""
    rows = []
    pristine = Path(args.pristine_tree).resolve() if args.pristine_tree else None
    for s in args.scenarios:
        # ``control_rep2`` is deliberately absent: A1 already gated the tree's
        # own determinism at this base commit, and what is new here is the
        # ``harvest`` arm, whose replicate is below.
        plan = [("control", TREE, "control")]
        if pristine:
            plan.insert(0, ("pristine", pristine, "control"))
        # ``harvest_inert`` is a harvest run with the state cache switched off
        # (no OUT), so the MFILE comparison isolates the *instrument* rather
        # than the disk write.  ``harvest`` is the real one.
        plan += [
            ("harvest_inert", TREE, "harvest"),
            ("harvest_rep2", TREE, "harvest"),
        ]
        for arm, tree, mode in plan:
            out = RUNS / s / arm
            if out.exists():
                shutil.rmtree(out)
            out.mkdir(parents=True)
            cmd = [
                sys.executable,
                str(PROBE / "run_one.py"),
                "--scenario", s,
                "--mode", mode,
                "--outdir", str(out),
                "--expect-tree", str(tree),
            ]
            r = _run(cmd, out, _env(tree=tree), out / "run")
            r.update({"scenario": s, "arm": arm})
            print(f"  gate {s:24s} {arm:16s} rc={r['returncode']} "
                  f"{r['wall_s_subprocess']:7.1f}s", flush=True)
            rows.append(r)
    (RUNS / "_gates_log.json").write_text(json.dumps(rows, indent=2))
    return 0 if all(r["returncode"] == 0 for r in rows) else 1


# --------------------------------------------------------------------------
# replay / ladder
# --------------------------------------------------------------------------


def _replay(scenario: str, tag: str, tau: float, arms, hoist: int,
            max_points: int, phases) -> dict:
    out = RUNS / scenario / f"replay_{tag}"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copy(SCENARIOS_DIR / f"{scenario}.IN.DAT", out / f"{scenario}.IN.DAT")
    harvest = RUNS / scenario / "harvest" / "harvest.pkl"
    if not harvest.exists():
        return {"scenario": scenario, "tag": tag, "returncode": 127,
                "error": f"no harvest at {harvest}"}
    cmd = [
        sys.executable,
        str(HERE / "replay.py"),
        "--harvest", str(harvest),
        "--scenario", scenario,
        "--input", f"{scenario}.IN.DAT",
        "--out", str(out / "result.json"),
        "--expect-tree", str(TREE),
        "--tau", repr(tau),
        "--hoist", str(hoist),
        "--label", tag,
        "--arms", *arms,
    ]
    if max_points:
        cmd += ["--max-points", str(max_points)]
    if phases:
        cmd += ["--phases", *phases]
    r = _run(cmd, out, _env(), out / "run")
    r.update({"scenario": scenario, "tag": tag, "tau": tau, "arms": list(arms),
              "hoist": hoist, "result": str(out / "result.json")})
    print(f"  replay {scenario:24s} {tag:22s} rc={r['returncode']} "
          f"{r['wall_s_subprocess']:7.1f}s", flush=True)
    return r


def cmd_ladder(args) -> int:
    """The tau calibration ladder.

    **Flat arm only, on a subsample**, at tau in {1e-4, 1e-6, 1e-8}.  It is a
    one-off calibration and must produce one tau used by *every* arm, or the
    comparison is not paired.  The ladder is itself a result: it measures how
    much the answer depends on the tolerance.  Note the distinction that keeps
    it honest -- convergence is on ``y``; tau is *calibrated* by its effect on
    ``objf`` and the constraint vector.  Calibration is not the predicate.
    """
    rows = []
    for s in args.scenarios:
        for tau in LADDER_TAUS:
            rows.append(_replay(s, f"ladder_tau{tau:g}", tau, ["A0"],
                                args.hoist, args.max_points, args.phases))
    (RUNS / "_ladder_log.json").write_text(json.dumps(rows, indent=2))
    return 0 if all(r["returncode"] == 0 for r in rows) else 1


def cmd_replay(args) -> int:
    rows = []
    for s in args.scenarios:
        tag = args.tag or f"tau{args.tau:g}_hoist{args.hoist}"
        rows.append(_replay(s, tag, args.tau, args.arms, args.hoist,
                            args.max_points, args.phases))
        if args.reps > 1:
            for i in range(2, args.reps + 1):
                rows.append(_replay(s, f"{tag}_rep{i}", args.tau, args.arms,
                                    args.hoist, args.max_points, args.phases))
    (RUNS / f"_replay_log_{args.tag or 'main'}.json").write_text(
        json.dumps(rows, indent=2)
    )
    return 0 if all(r["returncode"] == 0 for r in rows) else 1


# --------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--scenarios", nargs="*", default=SCENARIOS)

    p = sub.add_parser("harvest")
    common(p)
    p.add_argument("--grad-stride", type=int, default=5)
    p.add_argument("--other-stride", type=int, default=1)
    p.set_defaults(fn=cmd_harvest)

    p = sub.add_parser("gates")
    common(p)
    p.add_argument("--pristine-tree", default=None)
    p.set_defaults(fn=cmd_gates)

    p = sub.add_parser("ladder")
    common(p)
    p.add_argument("--hoist", type=int, default=0)
    p.add_argument("--max-points", type=int, default=0)
    p.add_argument("--phases", nargs="*", default=None)
    p.set_defaults(fn=cmd_ladder)

    p = sub.add_parser("replay")
    common(p)
    p.add_argument("--tau", type=float, default=1e-6)
    p.add_argument("--arms", nargs="*", default=["R", "A0", "A0f", "A1"])
    p.add_argument("--hoist", type=int, default=0)
    p.add_argument("--max-points", type=int, default=0)
    p.add_argument("--phases", nargs="*", default=None)
    p.add_argument("--reps", type=int, default=1)
    p.add_argument("--tag", default="")
    p.set_defaults(fn=cmd_replay)

    args = ap.parse_args()
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / "_mplconfig").mkdir(exist_ok=True)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
