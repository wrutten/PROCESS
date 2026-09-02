#!/usr/bin/env python
"""Phase A driver: harvest, gates, tau ladder, arm comparison.

**This file is the one entry point.**  `run_all()` runs the whole of Phase A
end to end; everything else here is a stage of it.  All the settings a reader
might want to change are module constants at the top of this file, listed in
`PARAMETERS` and passed through `run_all`'s keyword arguments, so nothing that
matters is buried elsewhere.

Every PROCESS run is a **fresh subprocess in its own working directory**, run
**serially** (trap T8: ``ps`` and ``pkill`` do not work across sandboxed Bash
calls, so overlapping runs cannot be detected or stopped -- they are never
started).  Every subprocess gets an explicit ``PYTHONPATH`` naming the tree
under test and asserts the **exact** tree it imported (trap T6).

Subcommands
-----------
``all``       everything below, in order -- the one-command entry point
``harvest``   one instrumented run per scenario; writes the design-point cache
``gates``     neutrality, determinism, harvest inertness
``ladder``    the tau calibration ladder -- **run this first**, it is a one-off
``replay``    the arm comparison at a chosen tau

**A26 note.**  This file still runs Phase A exactly as A18 ran it, and its
defaults are A18's --- ``--spec-mode a18``'s categorisation, no
predicate-layer routing, the block arm's inner tolerance equal to its outer
one.  That is deliberate: A18, A22 and A23's recorded artifacts have to keep
reproducing, and ``run_a26.py gate`` checks that they do, bit for bit.
**New measurements go through** :mod:`run_a26`, which exposes the parameters
A26 added --- the inner tolerance, the coupling-state spec mode and its scale
floor, the predicate-layer routing, and repetitions for timing.  The one thing
that changed here is the deck list; see :data:`DROPPED_2026_09_02`.

Usage
-----
    python run_phase_a.py all --pristine-tree /path/to/c0ae5b28/checkout
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
#: Where the recorded design points and every replay land.  A26/A28 made this
#: overridable, with the default unchanged, for two reasons.  A from-scratch
#: reproduction on a clean checkout must be able to write somewhere the caller
#: chooses; and in a task worktree ``runs/a18`` is usually a **symlink into the
#: main checkout's untracked run tree**, so a rebuild here would silently
#: overwrite the shared recording every other task replays.  Set with
#: ``--runs``; ``MDA_partition_experiment.py`` refuses to rebuild through such
#: a symlink rather than doing it.
RUNS = PROBE / "runs" / "a18"
SCENARIOS_DIR = PROBE / "scenarios"

#: **Three decks, from 2026-09-02 (D17).**  ``large_tokamak_eval`` is dropped:
#: it runs 0 solver iterations, so it cannot inform a study about how an
#: architecture behaves when the optimiser reacts; its inequality constraints
#: are never enforced, so its "solution" is not a feasible optimum; and A22
#: found its evidence weaker than the other pulsed decks (555 of 840 coupling
#: components classified constant from a 10-point harvest).  It was carrying
#: two of the results report's largest percentages on ten design points.
#: **Merged four-deck tables stand as the record of what was run** and are not
#: retro-edited; anything generated from here on is a three-deck table.  Pass
#: ``--scenarios`` explicitly to run the dropped deck for a historical
#: re-derivation.
DROPPED_2026_09_02 = ("large_tokamak_eval",)

SCENARIOS = [
    "large_tokamak_nof",
    "low_aspect_ratio_DEMO",
    "st_regression",
]

#: The ladder is a one-off calibration, not a per-arm setting.  tau must be
#: *identical* across arms or the comparison is not paired.
LADDER_TAUS = (1e-4, 1e-6, 1e-8)

#: The convergence tolerance the arm comparison runs at.  Chosen by the ladder
#: (see the report): tightening past this stops moving the objective and the
#: constraint vector, and only costs model evaluations.
TAU = 1e-6

#: The four architectures being compared.  R is today's loop and is a
#: reference, not a competitor; A0 is the control; A0f isolates the two-sweep
#: floor from the convergence test; A1 is the block partition.
DEFAULT_ARMS = ("R", "A0", "A0f", "A1")

#: How much of the optimiser's work is replayed.  Every design point the
#: optimiser actually visits is kept; only 1 in GRAD_STRIDE of the
#: finite-difference perturbations is, because those are 94-96 % of the total
#: and behave no differently.
GRAD_STRIDE = 5
OTHER_STRIDE = 1

#: Iteration ceilings.  Reaching one marks a design point invalid for that
#: architecture; it is never a budget quietly spent.  Defined in
#: ``engine.py`` and re-exported here so every parameter is in one place.
INNER_CAP = 20
OUTER_CAP = 20
GLOBAL_MODULE_SWEEP_CAP = 200

#: Everything above, in one dict, for a caller that wants to print or record
#: the configuration a result was produced under.
PARAMETERS = {
    "scenarios": SCENARIOS,
    "arms": DEFAULT_ARMS,
    "tau": TAU,
    "ladder_taus": LADDER_TAUS,
    "grad_stride": GRAD_STRIDE,
    "other_stride": OTHER_STRIDE,
    "inner_cap": INNER_CAP,
    "outer_cap": OUTER_CAP,
    "global_module_sweep_cap": GLOBAL_MODULE_SWEEP_CAP,
    "runs_dir": str(RUNS),
}


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


def run_all(
    scenarios=SCENARIOS,
    *,
    arms=DEFAULT_ARMS,
    tau: float = TAU,
    ladder_taus=LADDER_TAUS,
    grad_stride: int = GRAD_STRIDE,
    other_stride: int = OTHER_STRIDE,
    pristine_tree: str | None = None,
    reps: int = 2,
    run_gates: bool = True,
    run_hoist_variant: bool = True,
) -> dict:
    """Run the whole comparison, from a standing start, and say where it went.

    What this does, in plain language
    ---------------------------------
    PROCESS solves its plant model by running every model in turn, over and
    over, until the answer stops changing.  This function asks whether that
    repetition is arranged well, by taking the optimiser out of the picture
    entirely and comparing four ways of arranging the same models:

    * **R** -- exactly what PROCESS does today.  A reference point, not a
      competitor.
    * **A0** -- the same models in the same order, but stopping when the
      *engineering state* has stopped changing rather than when two summary
      numbers have, and allowed to stop after a single pass instead of being
      forced to do two.
    * **A0f** -- A0 with the two-pass minimum put back, so the effect of the
      stopping test can be told apart from the effect of the minimum.
    * **A1** -- the models split into three groups (plasma physics, coils,
      balance of plant), each group solved to completion before moving on.

    It runs in four stages, each in its own fresh subprocess:

    1. **Harvest.** Run PROCESS normally once per scenario, with instrumentation
       that copies out, at every model evaluation, the optimiser's parameter
       vector and a complete snapshot of the plant state at that moment.  These
       are the starting points every architecture is later replayed from, so
       all four solve exactly the same problems.
    2. **Checks.** Verify that the instrumentation changes nothing: an
       instrumented run and an untouched copy of the reference version of
       PROCESS must produce byte-identical output files, and two instrumented
       runs must agree exactly.
    3. **Tolerance calibration.** Solve the same points at three different
       convergence tolerances and see how much the final answer moves.  This
       decides the one tolerance every architecture is then held to.
    4. **Comparison.** Replay every harvested starting point through all four
       architectures at that one tolerance, counting model evaluations.

    Nothing is decided on how long anything took.  Every reported quantity is
    a count of model evaluations or an exact comparison of numbers, both of
    which reproduce identically from run to run.

    Parameters
    ----------
    scenarios
        Which input decks to run.  Files live in ``idf_probe/scenarios``.
    arms
        Which architectures to compare.  See above.
    tau
        Convergence tolerance for the comparison: a quantity counts as settled
        when it changes by less than this fraction of its own typical size.
    ladder_taus
        The tolerances the calibration stage tries.
    grad_stride, other_stride
        Sub-sampling.  ``grad_stride = 5`` keeps one in five of the optimiser's
        finite-difference probes; ``other_stride = 1`` keeps every point the
        optimiser actually visits.
    pristine_tree
        Path to an unmodified checkout of the reference version of PROCESS.
        Required for the neutrality check; without it that check is skipped.
        Produce one with ``git archive c0ae5b28 | tar -x -C <dir>``.
    reps
        How many times to repeat the comparison, to show it reproduces exactly.
    run_gates, run_hoist_variant
        Switches for stages 2 and for the extra pass in which the final
        cost/water-use models are lifted out of the repetition, which they can
        be because nothing feeds back into them.

    Returns
    -------
    dict
        ``{"parameters": ..., "stages": {<stage>: <exit status>}, "runs_dir":
        ..., "results": [<paths>]}``.

    Where the output goes
    ---------------------
    Everything lands under ``arch_surgery/idf_probe/runs/a18/`` (untracked):

    * ``<scenario>/harvest/`` -- one instrumented PROCESS run, plus
      ``harvest.pkl`` (the starting points) and ``probe_modules.json``.
    * ``<scenario>/{pristine,control,harvest_inert,harvest_rep2}/`` -- the
      check runs, each with a ``metrics.json`` and its output files.
    * ``<scenario>/replay_<tag>/result.json`` -- one comparison. Per design
      point it records, for each architecture, the number of passes, the number
      of model evaluations, whether it converged, which ceiling it hit if any,
      the residual trace, and a post-hoc audit taken one further pass past
      termination.

    Turn those into tables with ``analyse.py`` and then ``tables.py``.
    """
    import types

    out: dict = {"parameters": dict(PARAMETERS), "stages": {}, "runs_dir": str(RUNS)}
    out["parameters"].update({
        "scenarios": list(scenarios),
        "arms": list(arms),
        "tau": tau,
        "ladder_taus": list(ladder_taus),
        "grad_stride": grad_stride,
        "other_stride": other_stride,
    })
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / "_mplconfig").mkdir(exist_ok=True)

    def ns(**kw):
        base = {
            "scenarios": list(scenarios),
            "grad_stride": grad_stride,
            "other_stride": other_stride,
            "hoist": 0,
            "max_points": 0,
            "phases": None,
            "tau": tau,
            "arms": list(arms),
            "reps": 1,
            "tag": "",
            "pristine_tree": pristine_tree,
        }
        base.update(kw)
        return types.SimpleNamespace(**base)

    out["stages"]["harvest"] = cmd_harvest(ns())
    if run_gates:
        out["stages"]["gates"] = cmd_gates(ns())
    out["stages"]["ladder"] = cmd_ladder(ns())
    out["stages"]["replay"] = cmd_replay(
        ns(hoist=0, reps=reps, tag=f"tau{tau:g}_hoist0")
    )
    if run_hoist_variant:
        out["stages"]["replay_hoist"] = cmd_replay(
            ns(hoist=1, reps=1, tag=f"tau{tau:g}_hoist1")
        )
    out["results"] = sorted(str(p) for p in RUNS.glob("*/replay_*/result.json"))
    out["ok"] = all(v == 0 for v in out["stages"].values())
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("all", help="run the whole of Phase A end to end")
    p.add_argument("--runs", default=None,
                   help="where to write (default: idf_probe/runs/a18)")
    p.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    p.add_argument("--tau", type=float, default=TAU)
    p.add_argument("--arms", nargs="*", default=list(DEFAULT_ARMS))
    p.add_argument("--grad-stride", type=int, default=GRAD_STRIDE)
    p.add_argument("--other-stride", type=int, default=OTHER_STRIDE)
    p.add_argument("--pristine-tree", default=None)
    p.add_argument("--reps", type=int, default=2)
    p.add_argument("--no-gates", action="store_true")
    p.add_argument("--no-hoist-variant", action="store_true")
    p.set_defaults(fn=lambda a: 0 if run_all(
        a.scenarios, arms=a.arms, tau=a.tau, grad_stride=a.grad_stride,
        other_stride=a.other_stride, pristine_tree=a.pristine_tree,
        reps=a.reps, run_gates=not a.no_gates,
        run_hoist_variant=not a.no_hoist_variant,
    )["ok"] else 1)

    def common(p):
        p.add_argument("--scenarios", nargs="*", default=SCENARIOS)

    p = sub.add_parser("harvest")
    p.add_argument("--runs", default=None,
                   help="where to write (default: idf_probe/runs/a18)")
    common(p)
    p.add_argument("--grad-stride", type=int, default=GRAD_STRIDE)
    p.add_argument("--other-stride", type=int, default=OTHER_STRIDE)
    p.set_defaults(fn=cmd_harvest)

    p = sub.add_parser("gates")
    p.add_argument("--runs", default=None,
                   help="where to write (default: idf_probe/runs/a18)")
    common(p)
    p.add_argument("--pristine-tree", default=None)
    p.set_defaults(fn=cmd_gates)

    p = sub.add_parser("ladder")
    p.add_argument("--runs", default=None,
                   help="where to write (default: idf_probe/runs/a18)")
    common(p)
    p.add_argument("--hoist", type=int, default=0)
    p.add_argument("--max-points", type=int, default=0)
    p.add_argument("--phases", nargs="*", default=None)
    p.set_defaults(fn=cmd_ladder)

    p = sub.add_parser("replay")
    p.add_argument("--runs", default=None,
                   help="where to write (default: idf_probe/runs/a18)")
    common(p)
    p.add_argument("--tau", type=float, default=TAU)
    p.add_argument("--arms", nargs="*", default=list(DEFAULT_ARMS))
    p.add_argument("--hoist", type=int, default=0)
    p.add_argument("--max-points", type=int, default=0)
    p.add_argument("--phases", nargs="*", default=None)
    p.add_argument("--reps", type=int, default=1)
    p.add_argument("--tag", default="")
    p.set_defaults(fn=cmd_replay)

    args = ap.parse_args()

    # ``--runs`` redirects everything this script writes.  Rebound on the
    # module rather than threaded through twenty call sites, because every one
    # of them reads the module global and a partial redirection would put half
    # a run in each place -- which is worse than no redirection at all.
    if getattr(args, "runs", None):
        global RUNS
        RUNS = Path(args.runs).resolve()
        PARAMETERS["runs_dir"] = str(RUNS)
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / "_mplconfig").mkdir(exist_ok=True)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
