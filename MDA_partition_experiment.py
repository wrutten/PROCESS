#!/usr/bin/env python
"""Run the MDA partition experiment, Phase A, end to end.

WHAT THE EXPERIMENT ASKS
------------------------
PROCESS designs a fusion power plant by wrapping an optimiser around a loop
that runs twenty-six physics and engineering models over and over until their
outputs stop changing.  This experiment asks whether the *arrangement* of that
machinery -- how many loops there are, what they iterate on, and which models
sit inside them -- changes how much work a solve costs, with not one line of
any physics model altered.

Freezing the models is the point.  A faster program with rewritten models
proves nothing about architecture, because afterwards the rewrite and the
rearrangement cannot be told apart.

Phase A removes the optimiser entirely.  Instead of solving the design problem
again under each arrangement, it records the design points a real optimisation
run visited -- each one a design vector plus the exact plant state the loop was
entered with -- and replays every arrangement over that same list from those
same starting states.  Nothing here is decided on how long anything took: every
reported quantity is a count of model evaluations or an exact comparison of
numbers, and both reproduce identically from run to run.

WHAT IT COMPARES
----------------
Four arrangements of the same frozen models, at one shared tolerance:

  R    today's loop, unmodified.  A reference point, not a competitor.
  A0   one flat loop over all the models, stopping when the *plant state* has
       stopped changing rather than when two summary numbers have, and allowed
       to stop after a single pass.  The control.
  A0f  A0 with today's two-pass minimum put back, so the cost of changing the
       stopping test can be told apart from the saving of dropping the minimum.
  A1   the models split into three groups -- plasma physics, coils, balance of
       plant -- each solved to completion before moving on, inside an outer
       loop over the one quantity that joins them.

plus three controls that make those four readable:

  * a tolerance ladder, run on the flat arrangement alone before anything is
    compared, which fixes the one tolerance every arrangement is then held to;
  * an outer-pass census, which asks which quantities force a second pass of
    the blocked arrangement and what pinning the burn time removes;
  * a node-order control, which checks that the flat and blocked arrangements
    differ by the grouping and not by an incidental reordering that came with
    it.

Two further measurements run against PROCESS's own driver rather than the
replay engine, and they need an unmodified checkout of the base commit to
compare against (--parent-tree).  Without one they are skipped and said to be
skipped:

  * the feed-forward hoist -- running the models that feed nothing back once
    after the loop instead of on every pass;
  * the build/physics reorder that makes the physics group contiguous.

HOW TO RUN IT
-------------
    python MDA_partition_experiment.py

Add --parent-tree to include the two driver-side measurements::

    git archive c0ae5b28 | tar -x -C /some/dir/pristine_c0ae5b28
    python MDA_partition_experiment.py --parent-tree /some/dir/pristine_c0ae5b28

To print the tables from artifacts that already exist, running nothing::

    python MDA_partition_experiment.py --analyse-only --runs-root <dir>

Output lands under ``arch_surgery/idf_probe/runs/`` in this tree, which is not
tracked by git; the tables it prints are what the report quotes.

WHAT THIS FILE IS AND IS NOT
----------------------------
It is a wrapper.  Every measurement below is made by code that was written,
reviewed and gated as its own task -- ``arch_surgery/fixedpoint/run_phase_a.py``
(the four arrangements, the tolerance ladder and the neutrality, determinism,
fidelity and restore gates), ``run_a22.py`` (the outer-pass census),
``run_a23.py`` (the node-order control), ``arch_surgery/idf_probe/run_a13.py``
and ``run_a3.py`` (the two driver-side measurements), and ``analyse.py`` /
``tables.py`` (the tables).  Nothing is reimplemented here, so that running the
whole experiment from one file and running the stages separately are two paths
to the same numbers rather than two implementations of them.  If they ever
disagree, that disagreement is a finding.

A note on where the code comes from.  Every subprocess is given an explicit
PYTHONPATH naming this tree and asserts the exact tree it imported.  This is
not defensive habit: there are sibling conda environments on this machine whose
editable installs point at *different clones of PROCESS at different commits*,
and they import without error.  A run against the wrong tree succeeds and
produces numbers of the wrong program.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

TREE = Path(__file__).resolve().parent
FIXEDPOINT = TREE / "arch_surgery" / "fixedpoint"
PROBE = TREE / "arch_surgery" / "idf_probe"
RUNS_ROOT = PROBE / "runs"

SCENARIOS = [
    "large_tokamak_nof",
    "low_aspect_ratio_DEMO",
    "st_regression",
    "large_tokamak_eval",
]

#: The tolerance the arm comparison runs at.  It is not a free parameter: the
#: ladder stage measures how far the answer moves at 1e-4, 1e-6 and 1e-8 and
#: 1e-6 is where tightening stops moving it.  Every arm is held to the same
#: one, because arms stopped at different standards are not comparable.
TAU = 1e-6

#: The stages, in the order they must run.  ``phase_a`` produces the harvested
#: design points that ``census`` and ``permutation`` replay, so neither can run
#: before it.
STAGES = ("phase_a", "census", "permutation", "driver_hoist", "driver_reorder",
          "tables")

#: Stages needing an unmodified checkout of the base commit to compare against.
NEEDS_PARENT_TREE = ("driver_hoist", "driver_reorder")


def _env(runs_root: Path) -> dict:
    """Environment for a measurement subprocess.

    PYTHONPATH names this tree explicitly.  A ``git worktree`` does not
    redirect an editable install, so without this a subprocess running in its
    own working directory imports the main checkout instead of the tree being
    edited -- silently, and with a passing result.
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = str(TREE)
    env["MPLCONFIGDIR"] = str(runs_root / "_mplconfig")
    # The instrumentation switches are cleared rather than assumed absent: an
    # inherited one would change what is being measured without saying so.
    for k in ("PROCESS_IDF_PROBE", "PROCESS_ARCH_SEQUENCE", "PROCESS_ARCH_HOIST"):
        env.pop(k, None)
    return env


def _run(label: str, cmd: list[str], runs_root: Path) -> int:
    print(f"\n=== {label}\n    {' '.join(cmd)}", flush=True)
    t0 = time.perf_counter()
    rc = subprocess.run(cmd, env=_env(runs_root), cwd=str(TREE)).returncode
    dt = time.perf_counter() - t0
    # The elapsed time is progress information, not a measurement: no
    # conclusion in this experiment rests on a timing, and identical work has
    # been observed to vary by up to 35 % in processor time on this machine.
    print(f"--- {label}: exit {rc} ({dt:.1f} s elapsed, not a measurement)",
          flush=True)
    return rc


def stage_phase_a(args, runs_root: Path) -> int:
    """The four arrangements, the tolerance ladder, and the gates.

    Runs PROCESS once per test case with a recording hook to collect the design
    points, checks that the hook changes nothing, calibrates the tolerance, then
    replays all four arrangements over every recorded point -- twice, so the
    counts can be shown to reproduce exactly -- and once more with the
    feed-forward models lifted out of the loop.
    """
    cmd = [sys.executable, str(FIXEDPOINT / "run_phase_a.py"), "all",
           "--scenarios", *args.scenarios,
           "--tau", repr(args.tau),
           "--reps", str(args.reps)]
    if args.parent_tree:
        cmd += ["--pristine-tree", str(args.parent_tree)]
    else:
        # Said out loud rather than passed over: without a reference checkout
        # the neutrality check has nothing to compare against and does not run.
        print("NOTE: no --parent-tree given, so the neutrality check (this "
              "tree against an untouched copy of the base commit) is skipped.",
              flush=True)
    return _run("phase A: harvest, checks, tolerance ladder, four arrangements",
                cmd, runs_root)


def stage_census(args, runs_root: Path) -> int:
    """Which quantities force a second pass of the blocked arrangement.

    Replays the blocked arrangement three ways over the same recorded points:
    as it stands, with the burn time held at its entry value, and with the
    feed-forward models held fixed.  Reuses phase A's recorded design points
    rather than recording new ones.
    """
    return _run(
        "outer-pass census (which quantity forces a second pass)",
        [sys.executable, str(FIXEDPOINT / "run_a22.py"),
         "--a18-runs", str(runs_root / "a18"),
         "--scenarios", *args.scenarios,
         "--tau", repr(args.tau)],
        runs_root)


def stage_permutation(args, runs_root: Path) -> int:
    """Is the flat-versus-blocked difference the grouping, or the node order?

    Grouping the models by block also transposes two adjacent models relative
    to the flat order.  This replays the flat arrangement in the blocked
    arrangement's node order and checks it reproduces the recorded flat
    arrangement exactly; a reversed-order arm runs alongside it to show the
    check can fail.
    """
    return _run(
        "node-order control (grouping versus ordering)",
        [sys.executable, str(FIXEDPOINT / "run_a23.py"),
         "--a18-runs", str(runs_root / "a18"),
         "--scenarios", *args.scenarios,
         "--tau", repr(args.tau),
         "--sensitivity"],
        runs_root)


def stage_driver_hoist(args, runs_root: Path) -> int:
    """The feed-forward hoist, measured in PROCESS's own driver.

    Runs the models that feed nothing back once after the loop instead of on
    every pass, and checks every number in the output file is bit-identical to
    the reference checkout.  Needs --parent-tree.
    """
    rc = _run(
        "feed-forward hoist, in PROCESS's own driver",
        [sys.executable, str(PROBE / "run_a13.py"),
         "--parent-tree", str(args.parent_tree),
         "--runs", str(runs_root / "a13"),
         "--scenarios", *args.scenarios],
        runs_root)
    if rc == 0:
        rc = _run("feed-forward hoist: gates and saving",
                  [sys.executable, str(PROBE / "compare_a13.py"),
                   "--runs", str(runs_root / "a13"),
                   "--scenarios", *args.scenarios],
                  runs_root)
    return rc


def stage_driver_reorder(args, runs_root: Path) -> int:
    """Moving `build` out of the physics group's span, in PROCESS's own driver.

    The reorder is what makes the physics group contiguous, which a per-group
    solver needs.  Checked the same way: every number in the output file
    against the reference checkout.  Needs --parent-tree.
    """
    rc = _run(
        "build/physics reorder, in PROCESS's own driver",
        [sys.executable, str(PROBE / "run_a3.py"),
         "--parent-tree", str(args.parent_tree),
         "--runs", str(runs_root / "a3"),
         "--scenarios", *args.scenarios],
        runs_root)
    if rc == 0:
        rc = _run("build/physics reorder: gates",
                  [sys.executable, str(PROBE / "compare_a3.py"),
                   "--runs", str(runs_root / "a3"),
                   "--scenarios", *args.scenarios],
                  runs_root)
    return rc


def stage_tables(args, runs_root: Path) -> int:
    """Turn the recorded results into the tables the report quotes.

    Order matters and is not cosmetic: the gates come first, then the census of
    how many design points each arrangement failed to solve, and only then any
    ratio.  Arrangements averaged over different sets of problems are not
    comparable, and an arrangement that cannot solve a point the others can is
    itself a result.
    """
    a18 = runs_root / "a18"
    report_json = runs_root / "phase_a_report.json"
    rc = _run("tables: collate",
              [sys.executable, str(FIXEDPOINT / "analyse.py"),
               "--runs", str(a18),
               "--scenarios", *args.scenarios,
               "--out", str(report_json)],
              runs_root)
    if rc:
        return rc
    rc = _run("tables: print",
              [sys.executable, str(FIXEDPOINT / "tables.py"),
               "--report", str(report_json),
               "--runs", str(a18)],
              runs_root)
    if rc:
        return rc
    # The census tables resolve their own artifacts relative to this tree
    # rather than taking a path, so they are printed only when the census has
    # actually run here.  Said out loud, because a table that is silently
    # absent reads like a table with nothing in it.
    if runs_root == RUNS_ROOT and (RUNS_ROOT / "a22").is_dir():
        rc = _run("tables: outer-pass census",
                  [sys.executable, str(FIXEDPOINT / "a22_tables.py"),
                   *args.scenarios],
                  runs_root)
    else:
        print("NOTE: the outer-pass census tables are not printed -- that "
              "stage reads its artifacts from this tree's own runs directory, "
              "and they are not there.", flush=True)
    return rc


STAGE_FN = {
    "phase_a": stage_phase_a,
    "census": stage_census,
    "permutation": stage_permutation,
    "driver_hoist": stage_driver_hoist,
    "driver_reorder": stage_driver_reorder,
    "tables": stage_tables,
}


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__.split("HOW TO RUN IT")[0].strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS,
                    help="which input decks to run; results are always "
                         "reported per deck and never pooled")
    ap.add_argument("--tau", type=float, default=TAU,
                    help="the shared convergence tolerance (default 1e-6, "
                         "chosen by the ladder stage)")
    ap.add_argument("--reps", type=int, default=2,
                    help="how many times to repeat the comparison, to show "
                         "the counts reproduce exactly")
    ap.add_argument("--parent-tree", default=None,
                    help="an unmodified checkout of the base commit. Enables "
                         "the neutrality check and the two driver-side "
                         "measurements; without it they are skipped and said "
                         "to be skipped")
    ap.add_argument("--stages", nargs="*", default=None,
                    help=f"run only these stages, in order. One or more of: "
                         f"{', '.join(STAGES)}")
    ap.add_argument("--analyse-only", action="store_true",
                    help="run nothing; print the tables from artifacts that "
                         "already exist")
    ap.add_argument("--runs-root", default=str(RUNS_ROOT),
                    help="where the artifacts live (default: this tree's "
                         "arch_surgery/idf_probe/runs)")
    args = ap.parse_args()

    runs_root = Path(args.runs_root).resolve()
    if args.analyse_only:
        stages = ["tables"]
    elif args.stages:
        unknown = [s for s in args.stages if s not in STAGES]
        if unknown:
            print(f"unknown stage(s): {unknown}; known: {list(STAGES)}")
            return 2
        stages = [s for s in STAGES if s in args.stages]
    else:
        stages = list(STAGES)

    skipped = []
    if not args.parent_tree:
        skipped = [s for s in stages if s in NEEDS_PARENT_TREE]
        stages = [s for s in stages if s not in NEEDS_PARENT_TREE]

    print("MDA partition experiment, Phase A")
    print(f"  tree            {TREE}")
    print(f"  artifacts       {runs_root}")
    print(f"  decks           {', '.join(args.scenarios)}")
    print(f"  tolerance       {args.tau:g}")
    print(f"  stages          {', '.join(stages) or '(none)'}")
    if skipped:
        print(f"  SKIPPED         {', '.join(skipped)} -- no --parent-tree, "
              f"so there is nothing to compare against")
    runs_root.mkdir(parents=True, exist_ok=True)
    (runs_root / "_mplconfig").mkdir(exist_ok=True)

    results: dict[str, int] = {}
    for s in stages:
        results[s] = STAGE_FN[s](args, runs_root)
        if results[s] != 0:
            # A failed stage stops the run rather than letting later stages
            # report tables built on a partial result.
            print(f"\nSTOPPING: stage '{s}' exited {results[s]}.", flush=True)
            break

    print("\n=== summary")
    for s in STAGES:
        if s in results:
            print(f"  {s:16s} {'ok' if results[s] == 0 else f'FAILED ({results[s]})'}")
        elif s in skipped:
            print(f"  {s:16s} skipped (no --parent-tree)")
        else:
            print(f"  {s:16s} not run")
    return 0 if all(v == 0 for v in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
