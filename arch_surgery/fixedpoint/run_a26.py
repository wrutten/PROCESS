#!/usr/bin/env python
"""A26 (method-fixes): the reproduction gate, the accuracy ladders, timings.

Every PROCESS import runs in a **fresh subprocess in its own working
directory**, serially (trap T8), with ``PYTHONPATH`` naming this worktree and
the **exact** tree asserted inside the subprocess (trap T6).

Subcommands
-----------
``gate``      replay at A18's settings and compare, bit for bit, against A18's
              recorded artifacts.  Run this first: nothing else means anything
              until the instrument is shown inert where it is supposed to be.
``ladder``    the cost-versus-achieved-accuracy ladders for both arms (fix 1).
``spec``      the A26 coupling-state spec: no exclusion, scale floor, and the
              floor's decade sensitivity (fix 3).
``timing``    repeated replays with CPU and wall time, median and interval
              (fix 5).  Run **after** the subset-aware read lands, or it
              measures our own snapshot bookkeeping.
``all``       gate, ladder, spec, timing, in that order.

The deck list
-------------
**Three decks, from 2026-09-02.**  ``large_tokamak_eval`` is dropped (D17): it
runs 0 solver iterations, so it cannot inform a study about how an architecture
behaves when the optimiser reacts; its inequality constraints are never
enforced, so its "solution" is not a feasible optimum; and A22 found its
evidence weaker than the other pulsed decks.  It was carrying two of the
results report's largest percentages on ten design points.  **Already-merged
four-deck tables stand as the record of what was run** and are not retro-edited;
anything generated from here on is a three-deck table and says so.
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
A18_RUNS = PROBE / "runs" / "a18"
RUNS = PROBE / "runs" / "a26"
SCENARIOS_DIR = PROBE / "scenarios"

#: The study's decks from 2026-09-02 onward.  See the module docstring.
SCENARIOS = [
    "large_tokamak_nof",
    "low_aspect_ratio_DEMO",
    "st_regression",
]

#: Dropped, with the date and the reason, so that nobody reads a three-deck
#: table as a four-deck one with a missing column.
DROPPED_SCENARIOS = {
    "large_tokamak_eval": {
        "dropped": "2026-09-02",
        "decision": "D17 (user)",
        "reasons": [
            "runs 0 solver iterations, so it cannot inform a study about how "
            "an architecture behaves when the optimiser reacts",
            "its inequality constraints are never enforced, so its solution is "
            "not a feasible optimum",
            "A22 found its evidence weaker than the other pulsed decks "
            "(555 of 840 coupling components classified constant from 10 "
            "design points)",
        ],
        "note": (
            "It carried two of the results report's largest percentages "
            "(+27.3 % and -10.7 %, §4.4.1) on ten design points.  Merged "
            "four-deck tables are the record of what was run and are not "
            "retro-edited."
        ),
    }
}

#: fix 1.  The flat arm's ladder is a plain tau ladder.  The block arm's is two
#: families: the joint ladder (outer = inner), and an inner-only ladder at the
#: calibrated outer tau.  Both families give (cost, achieved accuracy) points;
#: the curve is read off the two together.
FLAT_TAUS = (1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-8)
BLOCK_JOINT_TAUS = (1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-8)
BLOCK_INNER_TAUS = (1e-1, 1e-2, 1e-3, 1e-4, 1e-5)
CALIBRATED_TAU = 1e-6

#: fix 3.  The recorded floor, and one decade each way.
SCALE_FLOORS = (0.1, 1.0, 10.0)

#: fix 5.  Repetitions per design point for the timing run.
TIMING_REPS = 5
TIMING_MAX_POINTS = 40


def _env(extra=None) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(TREE)  # T6
    env["MPLCONFIGDIR"] = str(RUNS / "_mplconfig")
    env.pop("PROCESS_IDF_PROBE", None)
    env["PROCESS_IDF_PROBE_READ_BUDGET"] = "0"
    env["PROCESS_IDF_PROBE_READ_STRIDE"] = "0"
    if extra:
        env.update({k: str(v) for k, v in extra.items()})
    return env


_SEQ = [0]


def replay(scenario: str, tag: str, **kw) -> dict:
    """One replay subprocess.  Every parameter is passed explicitly."""
    out = RUNS / scenario / f"replay_{tag}"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copy(SCENARIOS_DIR / f"{scenario}.IN.DAT", out / f"{scenario}.IN.DAT")
    harvest = A18_RUNS / scenario / "harvest" / "harvest.pkl"
    if not harvest.exists():
        return {"scenario": scenario, "tag": tag, "returncode": 127,
                "error": f"no harvest at {harvest}"}
    cmd = [
        sys.executable, str(HERE / "replay.py"),
        # NOT resolved: the harvest may be reached through a symlink into
        # the main checkout's untracked run tree, and resolving it would
        # take the path outside this worktree.
        "--harvest", str(harvest),
        "--scenario", scenario,
        "--input", f"{scenario}.IN.DAT",
        "--out", str(out / "result.json"),
        "--expect-tree", str(TREE),
        "--label", tag,
        "--tau", repr(kw.get("tau", CALIBRATED_TAU)),
        "--hoist", str(int(kw.get("hoist", 0))),
        "--lift", str(int(kw.get("lift", 0))),
        "--spec-mode", kw.get("spec_mode", "a18"),
        "--scale-floor", repr(kw.get("scale_floor", 1.0)),
        "--predicate-guard", str(int(kw.get("predicate_guard", 1))),
        "--reps", str(int(kw.get("reps", 1))),
        "--arms", *kw.get("arms", ["R", "A0", "A0f", "A1"]),
    ]
    if kw.get("inner_tau") is not None:
        cmd += ["--inner-tau", repr(kw["inner_tau"])]
    if kw.get("max_points"):
        cmd += ["--max-points", str(kw["max_points"])]
    _SEQ[0] += 1
    t0 = time.perf_counter()
    proc = subprocess.run(
        cmd, env=_env({"PROCESS_ARCH_SEQUENCE_POSITION": _SEQ[0]}),
        cwd=str(out), capture_output=True, text=True,
    )
    (out / "run.stdout.log").write_text(proc.stdout)
    (out / "run.stderr.log").write_text(proc.stderr)
    row = {
        "scenario": scenario, "tag": tag, "returncode": proc.returncode,
        "wall_s_subprocess": time.perf_counter() - t0,
        "sequence_position": _SEQ[0],
        "result": str(out / "result.json"), "params": dict(kw),
    }
    print(f"  {scenario:24s} {tag:30s} rc={proc.returncode} "
          f"{row['wall_s_subprocess']:7.1f}s", flush=True)
    if proc.returncode:
        print(proc.stderr[-800:], flush=True)
    return row


# --------------------------------------------------------------------------


def cmd_gate(args) -> int:
    """Reproduce A18, bit for bit, at A18's settings.

    The reproduction is run at ``--spec-mode a18 --predicate-guard 0``, which
    is what A18 ran.  Its **purpose** is not to praise the new code: it is the
    licence for reusing A18's harvest at all.  §6.3 licensed that reuse on the
    model sub-trees being hash-identical to the recording commit, and **that is
    no longer true** --- ``process/models/pulse.py`` and
    ``process/data_structure/numerics.py`` have changed since ``ad4e4536``
    (A25's variant points, inert by default).  An empirical reproduction over
    every design point is the replacement, and it is a stronger claim.
    """
    from a26_gates import compare_results, sensitivity  # noqa: PLC0415

    rows, gates = [], {}
    for s in args.scenarios:
        r = replay(s, "gate_a18repro", tau=1e-6, hoist=args.hoist,
                   spec_mode="a18", predicate_guard=0,
                   arms=["R", "A0", "A0f", "A1"],
                   max_points=getattr(args, "max_points", 0))
        rows.append(r)
        old = A18_RUNS / s / (
            f"replay_tau1e-06_hoist{args.hoist}" ) / "result.json"
        new = Path(r["result"])
        if r["returncode"] or not old.exists() or not new.exists():
            gates[s] = {"status": "INCOMPLETE",
                        "old_exists": old.exists(), "new_exists": new.exists(),
                        "returncode": r["returncode"]}
            continue
        gates[s] = {
            "reproduction": compare_results(old, new),
            "sensitivity": sensitivity(old, new),
        }
        gates[s]["status"] = (
            "PASS" if gates[s]["reproduction"]["status"] == "PASS"
            and gates[s]["sensitivity"]["status"] == "PASS" else "FAIL"
        )
        rep = gates[s]["reproduction"]
        print(f"    {s:24s} {gates[s]['status']:5s}  "
              f"{rep['n_differing_arm_records']} differing of "
              f"{rep['n_arm_records_compared']} arm records, "
              f"{rep['n_record_keys_compared']} keys; sensitivity "
              f"{gates[s]['sensitivity']['n_caught']}/"
              f"{gates[s]['sensitivity']['n_applied']} caught", flush=True)
    (RUNS / f"_gate_hoist{args.hoist}.json").write_text(
        json.dumps({"runs": rows, "gates": gates}, indent=2)
    )
    return 0 if all(g.get("status") == "PASS" for g in gates.values()) else 1


def cmd_ladder(args) -> int:
    """fix 1: cost versus achieved accuracy, for both arms, per deck."""
    rows = []
    mp = getattr(args, "max_points", 0)
    flat_t = getattr(args, "flat_taus", None) or FLAT_TAUS
    joint_t = getattr(args, "joint_taus", None) or BLOCK_JOINT_TAUS
    inner_t = getattr(args, "inner_taus", None) or BLOCK_INNER_TAUS
    for s in args.scenarios:
        for t in flat_t:
            rows.append(replay(s, f"acc_flat_tau{t:g}", tau=t,
                               hoist=args.hoist, spec_mode=args.spec_mode,
                               scale_floor=args.scale_floor, arms=["A0"],
                               max_points=mp))
        for t in joint_t:
            rows.append(replay(s, f"acc_block_joint{t:g}", tau=t,
                               hoist=args.hoist, spec_mode=args.spec_mode,
                               scale_floor=args.scale_floor, arms=["A1"],
                               max_points=mp))
        for t in inner_t:
            rows.append(replay(s, f"acc_block_inner{t:g}", tau=CALIBRATED_TAU,
                               inner_tau=t, hoist=args.hoist,
                               spec_mode=args.spec_mode,
                               scale_floor=args.scale_floor, arms=["A1"],
                               max_points=mp))
    (RUNS / f"_ladder_{args.spec_mode}.json").write_text(json.dumps(rows, indent=2))
    return 0 if all(r["returncode"] == 0 for r in rows) else 1


def cmd_spec(args) -> int:
    """fix 3: the A26 spec at the recorded floor, and a decade each way."""
    rows = []
    for s in args.scenarios:
        for f in SCALE_FLOORS:
            rows.append(replay(s, f"spec_a26_floor{f:g}", tau=CALIBRATED_TAU,
                               hoist=0, spec_mode="a26", scale_floor=f,
                               arms=["R", "A0", "A0f", "A1"]))
    (RUNS / "_spec.json").write_text(json.dumps(rows, indent=2))
    return 0 if all(r["returncode"] == 0 for r in rows) else 1


def cmd_timing(args) -> int:
    """fix 5: timings with an interval.  Context, never evidence.

    Taken **after** the subset-aware coupling-state read, deliberately: timing
    the arms before it would have measured the harness's own snapshot
    bookkeeping rather than the architecture.  The first run in a fresh
    environment is discarded --- numba JIT dominates it.
    """
    rows = []
    for s in args.scenarios:
        rows.append(replay(s, "timing_warmup_discarded", tau=CALIBRATED_TAU,
                           hoist=0, arms=["A0"], reps=1,
                           max_points=TIMING_MAX_POINTS))
        rows.append(replay(s, "timing", tau=CALIBRATED_TAU, hoist=0,
                           arms=["R", "A0", "A0f", "A1"], reps=TIMING_REPS,
                           max_points=TIMING_MAX_POINTS))
    (RUNS / "_timing.json").write_text(json.dumps(rows, indent=2))
    return 0 if all(r["returncode"] == 0 for r in rows) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--scenarios", nargs="*", default=SCENARIOS)
        p.add_argument("--hoist", type=int, default=0)
        p.add_argument("--spec-mode", default="a18")
        p.add_argument("--scale-floor", type=float, default=1.0)
        # A smoke run needs every stage to execute without every design point
        # being replayed.  Zero means "all", which is the default and is what
        # every published number was taken at; a smoke run's counts are its
        # own and must not be compared with the report's.
        p.add_argument("--max-points", type=int, default=0)
        p.add_argument("--flat-taus", nargs="*", type=float, default=None)
        p.add_argument("--joint-taus", nargs="*", type=float, default=None)
        p.add_argument("--inner-taus", nargs="*", type=float, default=None)

    for name, fn in (("gate", cmd_gate), ("ladder", cmd_ladder),
                     ("spec", cmd_spec), ("timing", cmd_timing)):
        p = sub.add_parser(name)
        common(p)
        p.set_defaults(fn=fn)

    p = sub.add_parser("all")
    common(p)
    p.set_defaults(fn=lambda a: (
        cmd_gate(a) or cmd_ladder(a) or cmd_spec(a) or cmd_timing(a)
    ))

    args = ap.parse_args()
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / "_mplconfig").mkdir(exist_ok=True)
    sys.path.insert(0, str(HERE))
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
