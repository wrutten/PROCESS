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

Try the smoke mode first.  It exercises every stage on one deck in a few
minutes, so you can confirm the machinery works before committing hours::

    python MDA_partition_experiment.py --quick

Add --parent-tree to include the two driver-side measurements::

    git archive c0ae5b28 | tar -x -C /some/dir/pristine_c0ae5b28
    python MDA_partition_experiment.py --parent-tree /some/dir/pristine_c0ae5b28

To compare a finished run against the published numbers, running nothing::

    python MDA_partition_experiment.py --verify

To print the tables from artifacts that already exist, running nothing::

    python MDA_partition_experiment.py --analyse-only --runs-root <dir>

Output lands under ``arch_surgery/idf_probe/runs/`` in this tree, which is not
tracked by git; the tables it prints are what the report quotes.  Nothing is
written to the tracked tree.

**Nothing is assumed to exist.**  The recorded design points that every replay
stage reads are treated as a cache to be verified, not a dependency to be
trusted: they are checked before use and rebuilt if they are absent.  Building
them is the expensive part of a from-scratch run and the estimate printed at
startup says so.

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
import json
import sys
from pathlib import Path

TREE = Path(__file__).resolve().parent
sys.path.insert(0, str(TREE / "arch_surgery"))

import experiment_runner as ER  # noqa: E402

FIXEDPOINT = TREE / "arch_surgery" / "fixedpoint"
PROBE = TREE / "arch_surgery" / "idf_probe"
RUNS_ROOT = PROBE / "runs"

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

#: The tolerance the arm comparison runs at.  It is not a free parameter: the
#: ladder stage measures how far the answer moves at 1e-4, 1e-6 and 1e-8 and
#: 1e-6 is where tightening stops moving it.  Every arm is held to the same
#: one, because arms stopped at different standards are not comparable.
TAU = 1e-6

#: The stages, in the order they must run.  ``phase_a`` produces the harvested
#: design points that ``census`` and ``permutation`` replay, so neither can run
#: before it.
STAGES = ("phase_a", "method_gate", "accuracy", "pulse_gate",
          "census", "permutation", "driver_hoist", "driver_reorder",
          "tables")

#: Stages needing an unmodified checkout of the base commit to compare against.
NEEDS_PARENT_TREE = ("driver_hoist", "driver_reorder")


def _env(runs_root: Path) -> dict:
    """Environment for a measurement subprocess.  See experiment_runner."""
    return ER.subprocess_env(runs_root)


def _run(label: str, cmd: list[str], runs_root: Path) -> int:
    """One measurement subprocess.  See experiment_runner."""
    return ER.run_step(label, cmd, runs_root)


def _ensure_harvest(args, runs_root: Path) -> int:
    """The recorded design points, checked and rebuilt if absent.

    Every replay stage reads a harvest recorded by running PROCESS once per
    deck with a recording hook.  It is 35 MB a deck and is not tracked, so in a
    worktree it is usually reached through a symlink into the main checkout's
    untracked run tree.

    **It is a cache to be verified, not a dependency to be trusted.**  If any
    deck's harvest is missing this rebuilds it, which is the expensive part of
    a from-scratch run.  Skipping the stage instead would leave a later stage
    reporting a table over a population nobody chose.
    """
    a18 = runs_root / "a18"
    # **A worktree usually reaches the recording through a symlink into the
    # main checkout's untracked run tree**, because it is 35 MB a deck and is
    # not duplicated.  Rebuilding through that symlink would silently
    # overwrite the shared recording every other task in the project replays.
    # Refused, with the exact fix, rather than done.
    if a18.is_symlink() and not str(a18.resolve()).startswith(str(TREE)):
        st0 = ER.harvest_status(runs_root, args.scenarios)
        if not st0["summary"]["complete"]:
            print(
                f"\nCANNOT REBUILD: {a18} is a symlink to "
                f"{a18.resolve()},\n  which is outside this tree.  Rebuilding "
                f"the recording there would overwrite\n  the shared one every "
                f"other task replays.\n\nTHE FIX:\n    "
                f"python {Path(sys.argv[0]).name} --runs-root "
                f"{runs_root.parent}/runs_fresh ...\n", flush=True)
            return 2
    st = ER.harvest_status(runs_root, args.scenarios)
    print("\nrecorded design points (the replay stages' input)")
    print(f"  location        {st['root']}"
          + (f"  ->  {st['resolves_to']}" if st["is_symlink"] else ""))
    for s, v in st["per_scenario"].items():
        print(f"  {s:<24}"
              + (f"present, {v['harvest_bytes'] / 2**20:.0f} MB"
                 if v["harvest_present"] else "ABSENT -- will be rebuilt"))
    if st["summary"]["complete"]:
        return 0
    print("  rebuilding the missing harvest(s).  This runs PROCESS once per "
          "deck with\n  a recording hook and is the slow part of a "
          "from-scratch run.", flush=True)
    return _run(
        "record the design points a real optimisation visits",
        [sys.executable, str(FIXEDPOINT / "run_phase_a.py"), "harvest",
         "--runs", str(runs_root / "a18"),
         "--scenarios", *args.scenarios],
        runs_root)


def stage_phase_a(args, runs_root: Path) -> int:
    """The four arrangements, the tolerance ladder, and the gates.

    Runs PROCESS once per test case with a recording hook to collect the design
    points, checks that the hook changes nothing, calibrates the tolerance, then
    replays all four arrangements over every recorded point -- twice, so the
    counts can be shown to reproduce exactly -- and once more with the
    feed-forward models lifted out of the loop.
    """
    a18 = runs_root / "a18"
    if a18.is_symlink() and not str(a18.resolve()).startswith(str(TREE)):
        print(f"\nCANNOT RUN phase_a: {a18} is a symlink to "
              f"{a18.resolve()},\n  outside this tree.  This stage RECORDS "
              f"design points and would overwrite the\n  shared recording "
              f"every other task replays.\n\nTHE FIX:\n    python "
              f"{Path(sys.argv[0]).name} --runs-root "
              f"{runs_root.parent}/runs_fresh ...\n", flush=True)
        return 2
    cmd = [sys.executable, str(FIXEDPOINT / "run_phase_a.py"), "all",
           "--runs", str(a18),
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
    rc = _ensure_harvest(args, runs_root)
    if rc:
        return rc
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
    rc = _ensure_harvest(args, runs_root)
    if rc:
        return rc
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


def stage_method_gate(args, runs_root: Path) -> int:
    """A26's reproduction gate: the instrument is inert where it must be.

    A26 changed code every previously merged arm runs through --- the
    subset-aware coupling-state read, the restructured residual, the routing
    rule for hoisted nodes.  This replays at A18's settings and compares
    against A18's recorded artifacts **bit for bit, with no tolerance**, then
    perturbs the comparison to show it can fail.  It is also the licence for
    reusing A18's harvest at all: the argument that licensed it before ---
    that the model sub-trees are hash-identical to the recording commit --- no
    longer holds, and an empirical reproduction replaces it.
    """
    rc = _ensure_harvest(args, runs_root)
    if rc:
        return rc
    # **Not truncated even in --quick.**  This gate compares the fresh replay
    # against the recorded one point for point, so a truncated population is
    # not a cheaper version of it -- it is a different comparison, and the gate
    # correctly refuses with "point sets differ".  A smoke mode that turned a
    # refusal into a failure would teach the reader to ignore the gate.
    return _run("A26 method gate: reproduce A18 bit for bit",
                [sys.executable, str(FIXEDPOINT / "run_a26.py"), "gate",
                 "--a18-runs", str(runs_root / "a18"),
                 "--runs", str(runs_root / "a26"),
                 "--scenarios", *args.scenarios],
                runs_root)


def stage_accuracy(args, runs_root: Path) -> int:
    """Cost against **achieved** accuracy, for both arms, per test case.

    The blocked arrangement was run with its inner blocks over-converged, so
    its cost figures were upper bounds rather than a comparison.  This runs
    both arrangements across ladders of tolerance, records what each actually
    delivered, and reads cost off at equal delivered accuracy.
    """
    rc = _ensure_harvest(args, runs_root)
    if rc:
        return rc
    rc = _run("A26: cost-versus-accuracy ladders",
              [sys.executable, str(FIXEDPOINT / "run_a26.py"), "ladder",
               "--a18-runs", str(runs_root / "a18"),
               "--runs", str(runs_root / "a26"),
               "--scenarios", *args.scenarios]
              + (["--max-points", "12", "--flat-taus", "0.0001", "1e-06",
                  "--joint-taus", "0.0001", "1e-06", "--inner-taus", "0.01"]
                 if args.quick else []),
              runs_root)
    if rc:
        return rc
    return _run("A26: cost at matched achieved accuracy",
                [sys.executable, str(FIXEDPOINT / "accuracy.py"),
                 "--runs", str(runs_root / "a26"),
                 "--scenarios", *args.scenarios,
                 "--out", str(runs_root / "a26" / "matched_accuracy.json")],
                runs_root)


def stage_pulse_gate(args, runs_root: Path) -> int:
    """`pulse` leaves the model loop once the burn time is a design variable.

    Runs PROCESS's own driver two ways on the lifted deck --- `pulse` on every
    pass, and `pulse` once per optimiser evaluation before the stopping test is
    evaluated --- and compares the stopping test's inputs as exact bits.
    """
    return _run("A26: pulse pre-predicate placement, in PROCESS's own driver",
                [sys.executable, str(PROBE / "run_a26_pulse.py")],
                runs_root)


STAGE_FN = {
    "phase_a": stage_phase_a,
    "method_gate": stage_method_gate,
    "accuracy": stage_accuracy,
    "pulse_gate": stage_pulse_gate,
    "census": stage_census,
    "permutation": stage_permutation,
    "driver_hoist": stage_driver_hoist,
    "driver_reorder": stage_driver_reorder,
    "tables": stage_tables,
}

#: What each stage costs on this machine, so the estimate printed before the
#: run is an estimate and not a shrug.  Measured, at four parallel jobs where
#: the stage runs in parallel and serially where trap T8 requires it.
#: Minutes and megabytes, **measured on this machine** on 2026-09-02, not
#: estimated.  ``phase_a``'s figure is for a from-scratch run that records the
#: design points; with the recording already present it is about a quarter of
#: that.  ``--quick`` figures are one test case, measured the same day.
STAGE_TABLE = [
    ER.Stage("phase_a", stage_phase_a,
             "record the design points, check the hook, calibrate the "
             "tolerance, replay four arrangements", 60, 7, 5000),
    ER.Stage("method_gate", stage_method_gate,
             "reproduce the recorded results bit for bit", 4, 1, 90),
    ER.Stage("accuracy", stage_accuracy,
             "tolerance ladders and cost at matched achieved accuracy",
             22, 1, 90),
    ER.Stage("pulse_gate", stage_pulse_gate,
             "the burn-time model out of the loop, in PROCESS's own driver",
             6, 3, 200),
    ER.Stage("census", stage_census,
             "which quantity forces a second pass", 6, 1, 300),
    ER.Stage("permutation", stage_permutation,
             "grouping versus node ordering", 6, 1, 300),
    ER.Stage("driver_hoist", stage_driver_hoist,
             "the feed-forward hoist, in PROCESS's own driver", 8, 3, 400,
             optional_reason="no --parent-tree, so there is nothing to "
                             "compare against"),
    ER.Stage("driver_reorder", stage_driver_reorder,
             "the build/physics reorder, in PROCESS's own driver", 8, 3, 400,
             optional_reason="no --parent-tree, so there is nothing to "
                             "compare against"),
    ER.Stage("tables", stage_tables, "print the tables the report quotes",
             1, 1, 1),
]

#: The published numbers this run can be checked against.  A disagreement is a
#: FINDING to surface, not an error to swallow.
PUBLISHED_PATH = TREE / "arch_surgery" / "docs" / "data" / "a21_published.json"


def stage_verify(args, runs_root: Path) -> int:
    """Compare this run's numbers with the published ones, per deck."""
    if not PUBLISHED_PATH.exists():
        print(f"no published numbers at {PUBLISHED_PATH}; nothing to verify "
              f"against.")
        return 2
    pub = json.loads(PUBLISHED_PATH.read_text())
    records = []
    rep = runs_root / "phase_a_report.json"
    if rep.exists():
        d = json.loads(rep.read_text())
        reps = d.get("replays") or {}
        for arm in ("A0", "A0f", "A1"):
            meas = {}
            for key, rec in reps.items():
                deck, _, label = key.partition("/")
                if label != "replay_tau1e-06_hoist0":
                    continue
                pair = (rec.get("paired") or {}).get(f"R->{arm}") or {}
                tot = (pair.get("total_node_calls") or {}).get(arm)
                if tot is not None:
                    meas[deck] = tot
            if meas:
                records.append(ER.verify_table(
                    f"in-loop model evaluations at tau = 1e-6, arm {arm}",
                    pub.get(f"node_calls_{arm}", {}), meas))
        meas = {}
        for key, rec in reps.items():
            deck, _, label = key.partition("/")
            if label != "replay_tau1e-06_hoist0":
                continue
            pair = (rec.get("paired") or {}).get("R->A1") or {}
            tot = (pair.get("total_node_calls") or {}).get("R")
            if tot is not None:
                meas[deck] = tot
        if meas:
            records.append(ER.verify_table(
                "in-loop model evaluations at tau = 1e-6, arm R",
                pub.get("node_calls_R", {}), meas))
    acc = runs_root / "a26" / "matched_accuracy.json"
    # A29 (replication-verify) found the original extraction here read a
    # key (``at_the_calibration_point``) that ``accuracy.py`` has never
    # written, swallowed the KeyError per deck, and silently dropped the
    # whole matched-accuracy table from the verification -- so "every
    # compared table agrees" was printed over 4 of the 5 published
    # tables.  The calibration point is the flat arm's rung at the
    # experiment's shared tolerance (tau = 1e-6), so the ratio is read
    # from that row.  A deck where the row cannot be found is now
    # reported as MISSING in the table rather than dropped without a
    # word.  And when the artifact itself is absent (issue I-14: a
    # worktree retirement destroyed exactly this file once), the table is
    # still emitted, all decks MISSING, with the command that rebuilds it
    # -- absence must be loud, for the same reason the wrong key had to
    # be: a verification that quietly narrows its own population is the
    # shape this project's trap T11 names.
    meas = {}
    if acc.exists():
        d = json.loads(acc.read_text())
        for s, rec in (d.get("per_scenario") or d).items():
            rows = ((rec.get("matched_accuracy") or {}).get("rows")
                    if isinstance(rec, dict) else None) or []
            for row in rows:
                if row.get("flat_label") == "acc_flat_tau1e-06":
                    meas[s] = row.get("ratio_block_over_flat")
                    break
            else:
                meas[s] = None
    else:
        print(f"NOTE: {acc} is absent, so the matched-accuracy table below "
              f"is all MISSING.\n      Rebuild it with:  python "
              f"{Path(sys.argv[0]).name} --stages accuracy")
    records.append(ER.verify_table(
        "A1/A0 at the calibration point, matched achieved accuracy",
        pub.get("matched_accuracy_ratio", {}), meas,
        exact=False, rtol=1e-3))
    if not records:
        print("nothing to verify: no analysis artifacts found under "
              f"{runs_root}.  Run the experiment first.")
        return 2
    (runs_root / "_verification_phase_a.json").write_text(
        json.dumps(records, indent=2, default=str))
    return ER.print_verification(records)


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
    ap.add_argument("--quick", action="store_true",
                    help="smoke mode: one deck, a short ladder and a single "
                         "repetition.  Exercises every stage in minutes.  Its "
                         "counts are its own and must not be compared with "
                         "the report's")
    ap.add_argument("--verify", action="store_true",
                    help="run nothing; compare a finished run's numbers with "
                         "the published ones, per deck, with denominators")
    ap.add_argument("--analyse-only", action="store_true",
                    help="run nothing; print the tables from artifacts that "
                         "already exist")
    ap.add_argument("--runs-root", default=str(RUNS_ROOT),
                    help="where the artifacts live (default: this tree's "
                         "arch_surgery/idf_probe/runs, which is untracked)")
    args = ap.parse_args()

    if args.quick:
        args.scenarios = args.scenarios[:1]
        args.reps = 1

    runs_root = Path(args.runs_root).resolve()

    if args.verify:
        ER.print_provenance()
        return stage_verify(args, runs_root)

    if args.analyse_only:
        ER.print_provenance()
        runs_root.mkdir(parents=True, exist_ok=True)
        (runs_root / "_mplconfig").mkdir(exist_ok=True)
        return stage_tables(args, runs_root)

    ER.check_prerequisites(
        args.scenarios,
        need_artifacts=("ystate_{scenario}.json", "dsm_node_map.json"),
        runs_root=runs_root,
    )

    if args.stages:
        unknown = [s for s in args.stages if s not in STAGES]
        if unknown:
            print(f"unknown stage(s): {unknown}; known: {list(STAGES)}")
            return 2
        chosen = [s for s in STAGES if s in args.stages]
    else:
        chosen = list(STAGES)

    stages = [x for x in STAGE_TABLE if x.name in chosen]
    skipped = []
    if not args.parent_tree:
        skipped = [x for x in stages if x.name in NEEDS_PARENT_TREE]
        stages = [x for x in stages if x.name not in NEEDS_PARENT_TREE]
        print("NOTE: no --parent-tree given, so the neutrality check (this "
              "tree against an\n      untouched copy of the base commit) is "
              "skipped inside the phase_a stage\n      as well as the two "
              "driver-side stages below.")

    ER.print_provenance()
    ER.print_plan("MDA partition experiment, Phase A (the optimiser is absent)",
                  stages, quick=args.quick, scenarios=args.scenarios,
                  runs_root=runs_root, skipped=skipped)
    runs_root.mkdir(parents=True, exist_ok=True)
    (runs_root / "_mplconfig").mkdir(exist_ok=True)

    results: dict[str, int] = {}
    for x in stages:
        results[x.name] = STAGE_FN[x.name](args, runs_root)
        if results[x.name] != 0:
            # A failed stage stops the run rather than letting later stages
            # report tables built on a partial result.
            print(f"\nSTOPPING: stage '{x.name}' exited {results[x.name]}.",
                  flush=True)
            break

    print("\n=== summary")
    for name in STAGES:
        if name in results:
            v = results[name]
            print(f"  {name:16s} {'ok' if v == 0 else f'FAILED ({v})'}")
        elif any(x.name == name for x in skipped):
            print(f"  {name:16s} skipped (no --parent-tree)")
        else:
            print(f"  {name:16s} not run")
    return 0 if all(v == 0 for v in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
