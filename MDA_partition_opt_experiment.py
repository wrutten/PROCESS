#!/usr/bin/env python
"""Run the MDA partition experiment, Phase B, end to end.

WHAT THE EXPERIMENT ASKS
------------------------
PROCESS designs a fusion power plant by wrapping an optimiser around a loop
that runs about twenty-six physics and engineering models over and over until
their outputs stop changing.  This experiment asks whether the *arrangement* of
that machinery -- how many loops there are, what they iterate on, which models
sit inside them, and which quantities the optimiser owns rather than the loop
-- changes how much work a solve costs, with not one line of any physics model
altered.

Freezing the models is the point.  A faster program with rewritten models
proves nothing about architecture, because afterwards the rewrite and the
rearrangement cannot be told apart.

Phase A (its companion file, ``MDA_partition_experiment.py``) removed the
optimiser entirely and replayed arrangements over recorded design points.
**Phase B puts the optimiser back.**  Every run here is a whole optimisation,
from a starting design vector to a converged plant design, in PROCESS's own
driver -- which is the only way to ask the question that matters: does the
optimiser react to the rearrangement?  A loop that is cheaper per solve is
worth nothing if the optimiser then takes more solves, or fails to converge at
all from starting points the current arrangement handles.

WHAT IT COMPARES
----------------
Three arrangements of the same frozen models, and it takes three because two
cannot separate the two things that changed:

  R    PROCESS as it ships.  Its loop stops when two summary numbers -- the
       objective and the constraint vector -- stop changing between passes.
       The reference point, and the reason any of this is relevant to a real
       user.

  A0'  the same flat loop, stopping instead when the *plant state itself* has
       stopped changing: about 840 measured quantities, each to a tolerance.
       Nothing else differs from R.  This is the control, and it exists
       because R and the proposal below stop on different tests, so comparing
       them directly measures the rearrangement and the change of stopping
       rule added together -- and the second can be as large as the first.

  A1'  the proposal: the models split into three groups (plasma physics,
       coils, balance of plant), each solved to completion before the next
       runs; the plant's burn time handed to the optimiser as a design
       variable with a consistency constraint instead of being solved for
       inside the loop; and the models that feed nothing back run once after
       the loop instead of on every pass.

So ``A0' -> A1'`` is the arrangement on its own and is the headline;
``R -> A1'`` is what a user would actually see and is reported beside it;
``R -> A0'`` is what the change of stopping rule costs by itself.

**The result of A0' -> A1' is called "the proposed architecture", never "the
partition's benefit."**  Three things change at once and only one of them is
the partition.  A fourth arrangement, A1' without the last of the three, is run
so that its share is measured rather than guessed.

HOW IT MEASURES
---------------
Cost is a **count of model evaluations**, never a time.  Identical work has
been observed to vary by up to 35 % in processor time on this machine and the
cause is not known, so every conclusion here rests on counts and exact
comparisons of numbers, which reproduce bit for bit.  Timings are printed with
a median, an interval and a repetition count, and are labelled as context.

Because one run is one sample from a distribution of paths, each arrangement is
run from twenty-odd *perturbed* starting points, the same ones for every
arrangement, and the distributions are compared rather than single numbers.
The size of the perturbation is calibrated on the reference arrangement first
rather than chosen.

**Robustness outranks cost.**  How many starting points each arrangement solves
is a first-class result.  An arrangement that is cheaper on the ones it solves
and fails on more of them has not won.

Before any of that, an equivalence gate: each arrangement must reach the same
optimum as the reference, satisfy every constraint at the point it returns,
and -- for the arrangement that hands the burn time to the optimiser -- satisfy
that consistency constraint too.  **If the gate fails the run stops and says
so.**  Nothing is tuned, retried at another setting, or narrowed until it
passes.

HOW TO RUN IT
-------------
    python MDA_partition_opt_experiment.py

Try the smoke mode first.  It exercises every stage on one deck in a few
minutes so you can confirm the machinery works before committing hours::

    python MDA_partition_opt_experiment.py --quick

Add an unmodified checkout of the base commit to include the check that this
tree behaves identically to it when every switch is off::

    git archive c0ae5b28 | tar -x -C /some/dir/pristine_c0ae5b28
    python MDA_partition_opt_experiment.py --parent-tree /some/dir/pristine_c0ae5b28

To compare a finished run against the published numbers, running nothing::

    python MDA_partition_opt_experiment.py --verify

Output lands under ``arch_surgery/idf_probe/runs/a28/``, which is not tracked
by git.  Nothing is written to the tracked tree.

WHAT THIS FILE IS AND IS NOT
----------------------------
It is a wrapper.  Every measurement is made by code that was written, reviewed
and gated as its own task -- ``arch_surgery/idf_probe/run_a28.py`` (the arms
and the runs), ``a28_analysis.py`` (the declarations, the gates and the
analysis), ``a25_variant_deck.py`` (the derived decks), ``run_a24.py`` and
``gates.py`` (the switch-neutrality check), and
``arch_surgery/fixedpoint/manifest.py`` and ``accuracy.py`` (the comparison
declarations and the matched-accuracy curves).  Nothing is reimplemented here,
so running the whole experiment from one file and running the stages
separately are two paths to the same numbers rather than two implementations of
them.  If they ever disagree, that disagreement is a finding.

It shares its runner with Phase A's entry point
(``arch_surgery/experiment_runner.py``): the two files differ in which phase
they drive, not in how they drive it.

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

PROBE = TREE / "arch_surgery" / "idf_probe"
FIXEDPOINT = TREE / "arch_surgery" / "fixedpoint"
RUNS_ROOT = PROBE / "runs"
A28 = "a28"

#: **Three decks, from 2026-09-02 (D17).**  ``large_tokamak_eval`` is dropped:
#: it runs 0 solver iterations, so it cannot inform a study about how an
#: architecture behaves when the optimiser reacts; its inequality constraints
#: are never enforced, so its "solution" is not a feasible optimum; and the
#: evidence behind its coupling-state artifact rests on ten design points.
#: Merged four-deck tables stand as the record of what was run.
DROPPED_2026_09_02 = ("large_tokamak_eval",)

SCENARIOS = ["large_tokamak_nof", "low_aspect_ratio_DEMO", "st_regression"]

CORE_ARMS = ["R", "A0p", "A1p"]
ALL_ARMS = ["R", "A0p", "A1p", "A0p_reordered", "A1p_nohoist"]


def _a28(args, runs_root: Path) -> Path:
    return runs_root / A28


def _py():
    return sys.executable


# ---------------------------------------------------------------------------
# stages
# ---------------------------------------------------------------------------


def stage_decks(args, runs_root: Path) -> int:
    """Derive the deck in which the burn time is a design variable.

    The frozen input decks are never edited.  A derived copy is written into
    the run directory with three lines added -- the extra design variable, the
    consistency constraint, and the variable's starting value -- and carries
    its provenance in a header comment and a JSON sidecar.  The starting value
    is measured, not chosen: it is the burn time the reference arrangement's
    own loop settles on at this deck's own starting design vector, which is the
    only value at which the two arrangements start from the same design point.
    """
    return ER.run_step(
        "derive the lifted decks (frozen scenarios untouched)",
        [_py(), PROBE / "run_a28.py", "decks",
         "--runs", _a28(args, runs_root), "--scenarios", *args.scenarios],
        runs_root)


def stage_neutrality(args, runs_root: Path) -> int:
    """With every switch off, is this tree still the base commit, bit for bit?

    The three arrangements are selected by environment variables, and the code
    that reads them sits on the path every run takes.  So "off means upstream"
    is a claim about this tree and is gated rather than asserted: every number
    in the output file, on every deck, against an unmodified checkout of the
    base commit -- and then the comparison is deliberately broken, to show it
    can fail.
    """
    rc = ER.run_step(
        "switch neutrality: this tree with everything off, against the base "
        "commit",
        [_py(), PROBE / "run_a24.py",
         "--parent-tree", args.parent_tree,
         "--runs", _a28(args, runs_root) / "neutrality",
         "--scenarios", *args.scenarios,
         "--jobs", str(args.jobs)],
        runs_root)
    if rc:
        return rc
    rc = ER.run_step(
        "switch neutrality: the comparison",
        [_py(), PROBE / "gates.py", "gate",
         "--runs", _a28(args, runs_root) / "neutrality",
         "--scenarios", *args.scenarios],
        runs_root)
    if rc:
        return rc
    return ER.run_step(
        "switch neutrality: the comparison shown capable of failing",
        [_py(), PROBE / "gates.py", "sensitivity",
         "--runs", _a28(args, runs_root) / "neutrality",
         "--scenarios", *args.scenarios],
        runs_root)


def stage_gate(args, runs_root: Path) -> int:
    """Each arrangement at each deck's own starting point, then the gates.

    Four checks, in this order, and the first is the one most experiments skip:

    1. **What does each comparison vary?**  Every pair of arrangements that was
       run carries a written declaration of exactly what differs between them,
       checked against the arrangements as they were actually built.  A
       difference nobody declared is a refusal, not a warning.  This exists
       because an earlier comparison in this study varied two things and
       nothing in its design was capable of noticing.
    2. **Do the arrangements run the same models?**  A block schedule that
       fails to name a model silently stops running it.  The call sites are
       read out of the driver's source and checked against what each
       arrangement resolved.  The cost unit is checked the same way rather
       than asserted.
    3. **The equivalence gate.**  Same optimum, feasible at the point
       returned, and the lifted arrangement on its own consistency manifold.
    4. **Every gate shown capable of failing**, on deliberately corrupted
       inputs, before any of its zeros are accepted.
    """
    rc = ER.run_step(
        "gate runs: every arrangement at each deck's own point",
        [_py(), PROBE / "run_a28.py", "gate",
         "--runs", _a28(args, runs_root),
         "--scenarios", *args.scenarios, "--arms", *args.arms,
         "--jobs", str(args.jobs)],
        runs_root)
    if rc:
        return rc
    for cmd, label in (
        ("manifests", "what each comparison declares it varies"),
        ("manifest_sensitivity",
         "the declaration check shown capable of refusing"),
        ("model_set", "do the arrangements run the same models, and does the "
                      "cost unit count what it claims"),
        ("gate", "the equivalence gate"),
        ("gate_sensitivity", "the equivalence gate shown capable of failing"),
    ):
        rc = ER.run_step(
            f"gate analysis: {label}",
            [_py(), PROBE / "a28_analysis.py", cmd,
             "--runs", _a28(args, runs_root),
             "--scenarios", *args.scenarios, "--arms", *args.arms],
            runs_root)
        if rc:
            return rc
    # THE STOP RULE.  Not negotiable, and not a formality: if the arrangements
    # do not reach the same optimum, a cost comparison between them is a
    # comparison of two different problems.
    g = json.loads(
        (_a28(args, runs_root) / "_gate_a28.json").read_text()
    )
    if g["overall"] != "PASS":
        print("\n" + "=" * 72)
        print("EQUIVALENCE GATE FAILED.  STOPPING.")
        print("  Per deck, per arm:")
        for s, byarm in g["status_by_scenario"].items():
            for a, st in byarm.items():
                print(f"    {s:24s} {a:14s} {st}")
        print("  The multi-start campaign is NOT run on a failing gate.")
        print("  A failed gate is a result, not an obstacle: it is reported "
              "with its\n  numbers and nothing is tuned, retried or narrowed "
              "to make it pass.")
        print("=" * 72, flush=True)
        return 3
    return 0


def stage_calibrate(args, runs_root: Path) -> int:
    """How large a perturbation the reference arrangement still survives.

    The multi-start campaign perturbs the starting design vector, and how far
    is a parameter that must not be chosen after seeing a result.  It is
    measured on the **reference arrangement alone**, at 1 %, 5 % and 10 %, and
    the largest size that still solves most starts is taken.  The whole table
    is reported, not just the choice.
    """
    rc = ER.run_step(
        "perturbation calibration, on the reference arrangement only",
        [_py(), PROBE / "run_a28.py", "calibrate",
         "--runs", _a28(args, runs_root),
         "--scenarios", *args.scenarios,
         "--starts", str(args.calibration_starts),
         "--deltas", *[repr(d) for d in args.deltas],
         "--jobs", str(args.jobs)],
        runs_root)
    if rc:
        return rc
    return ER.run_step(
        "perturbation calibration: the table",
        [_py(), PROBE / "a28_analysis.py", "calibration",
         "--runs", _a28(args, runs_root),
         "--scenarios", *args.scenarios,
         "--deltas", *[repr(d) for d in args.deltas]],
        runs_root)


def stage_ladder(args, runs_root: Path) -> int:
    """Cost at matched **achieved** accuracy, not at matched settings.

    Two arrangements asked for the same tolerance do not deliver the same
    accuracy: one that solves each group to completion against inputs that are
    about to change ends up far more converged than one that does not, and only
    the extra work shows up in a cost ratio.  So both are run across a ladder
    of tolerances, each run's *achieved* accuracy is measured by taking one
    further full pass past termination, and cost is read off at equal achieved
    accuracy.

    Reading the ladder in tolerance order instead is the wrong construction and
    reversed the sign of this study's Phase A result once.  What is read is the
    lower envelope: the cheapest setting that delivers at least the accuracy
    asked for.
    """
    cal = _a28(args, runs_root) / "_calibration_a28.json"
    delta = args.delta
    if delta is None and cal.exists():
        delta = json.loads(cal.read_text())["campaign_delta"]
    cmd = [_py(), PROBE / "run_a28.py", "ladder",
           "--runs", _a28(args, runs_root),
           "--scenarios", *args.scenarios,
           "--ladder-starts", str(args.ladder_starts),
           "--jobs", str(args.jobs)]
    if delta is not None:
        cmd += ["--delta", repr(delta)]
    if args.quick:
        cmd += ["--flat-taus", "0.0001", "1e-06",
                "--joint-taus", "0.0001", "1e-06",
                "--inner-taus", "0.01"]
    rc = ER.run_step("tolerance ladders, both arrangements", cmd, runs_root)
    if rc:
        return rc
    return ER.run_step(
        "cost at matched achieved accuracy",
        [_py(), PROBE / "a28_analysis.py", "ladder",
         "--runs", _a28(args, runs_root), "--scenarios", *args.scenarios],
        runs_root)


def stage_campaign(args, runs_root: Path) -> int:
    """The paired multi-start campaign: robustness first, then cost.

    Every arrangement solves the same perturbed starting points, so the
    comparison is paired.  Reported in a fixed order that is not a style
    choice: which starts each arrangement solves, then which starts leave the
    cost comparison and why, and only then any ratio.  A ratio over a quietly
    smaller population is the error this project has published three times.
    """
    cal = _a28(args, runs_root) / "_calibration_a28.json"
    delta = args.delta
    if delta is None:
        if not cal.exists():
            print("the campaign needs a perturbation size, and it comes from "
                  "the calibration stage.  Run --stages calibrate first, or "
                  "pass --delta.", flush=True)
            return 2
        delta = json.loads(cal.read_text())["campaign_delta"]
        print(f"perturbation size from the calibration: {delta}", flush=True)
    rc = ER.run_step(
        "multi-start campaign, every arrangement on the same starts",
        [_py(), PROBE / "run_a28.py", "campaign",
         "--runs", _a28(args, runs_root),
         "--scenarios", *args.scenarios, "--arms", *args.arms,
         "--starts", str(args.starts), "--delta", repr(delta),
         "--jobs", str(args.jobs)],
        runs_root)
    if rc:
        return rc
    rc = ER.run_step(
        "campaign analysis: robustness, drop census, then cost",
        [_py(), PROBE / "a28_analysis.py", "h5",
         "--runs", _a28(args, runs_root),
         "--scenarios", *args.scenarios, "--arms", *args.arms],
        runs_root)
    if rc:
        return rc
    return ER.run_step(
        "timings, as context and never as evidence",
        [_py(), PROBE / "a28_analysis.py", "timings",
         "--runs", _a28(args, runs_root),
         "--scenarios", *args.scenarios, "--arms", *args.arms],
        runs_root)


def stage_tables(args, runs_root: Path) -> int:
    """Turn the recorded results into the tables the report quotes."""
    return ER.run_step(
        "tables",
        [_py(), PROBE / "a28_tables.py",
         "--runs", _a28(args, runs_root), "--scenarios", *args.scenarios],
        runs_root)


STAGES = [
    ER.Stage("decks", stage_decks,
             "derive the deck with the burn time lifted", 1, 1, 1),
    ER.Stage("neutrality", stage_neutrality,
             "every switch off must equal the base commit, bit for bit",
             6, 3, 400,
             optional_reason="no --parent-tree, so there is nothing to "
                             "compare against"),
    ER.Stage("gate", stage_gate,
             "the arrangements at each deck's own point, and every gate",
             9, 2, 350),
    ER.Stage("calibrate", stage_calibrate,
             "how large a perturbation the reference survives", 55, 4, 1500),
    ER.Stage("campaign", stage_campaign,
             "the paired multi-start campaign, then robustness and cost",
             130, 6, 4500),
    ER.Stage("ladder", stage_ladder,
             "tolerance ladders and cost at matched achieved accuracy",
             35, 4, 1200),
    ER.Stage("tables", stage_tables, "print the tables the report quotes",
             1, 1, 1),
]

NEEDS_PARENT_TREE = ("neutrality",)


# ---------------------------------------------------------------------------
# verification
# ---------------------------------------------------------------------------

#: The published numbers, so a re-run can be checked against them rather than
#: merely produced.  **These are the report's, and a disagreement is a finding
#: to surface, not an error to swallow.**  Counts are compared exactly; the
#: paired ratios are compared to a stated relative tolerance, because a ratio
#: over a distribution of starts moves if any start's verdict moves.
PUBLISHED: dict = {}
PUBLISHED_PATH = TREE / "arch_surgery" / "docs" / "data" / "a28_published.json"


def load_published() -> dict:
    if PUBLISHED_PATH.exists():
        return json.loads(PUBLISHED_PATH.read_text())
    return PUBLISHED


def stage_verify(args, runs_root: Path) -> int:
    """Compare this run's numbers with the published ones, per deck."""
    pub = load_published()
    if not pub:
        print(f"no published numbers at {PUBLISHED_PATH}; nothing to verify "
              f"against.  This file is written when the study's results are "
              f"committed.")
        return 2
    a28 = _a28(args, runs_root)
    records = []

    def _read(name):
        p = a28 / name
        return json.loads(p.read_text()) if p.exists() else None

    g = _read("_gate_a28.json")
    if g:
        meas = {
            s: all(v == "PASS" for v in byarm.values())
            for s, byarm in g["status_by_scenario"].items()
        }
        records.append(ER.verify_table(
            "equivalence gate passes, per deck",
            pub.get("gate_passes", {}), meas))
    h = _read("_h5_a28.json")
    if h:
        for key, pubkey in (("A0p_vs_A1p", "paired_median_A0p_to_A1p"),
                            ("R_vs_A1p", "paired_median_R_to_A1p"),
                            ("R_vs_A0p", "paired_median_R_to_A0p")):
            meas = {}
            for s, comps in h["comparisons"].items():
                c = comps.get(key)
                if c and c.get("paired_ratio_variant_over_reference"):
                    meas[s] = c["paired_ratio_variant_over_reference"]["median"]
            records.append(ER.verify_table(
                f"paired median cost ratio, {key}",
                pub.get(pubkey, {}), meas, exact=False, rtol=1e-3))
        meas = {}
        for s, comps in h["comparisons"].items():
            c = comps.get("A0p_vs_A1p")
            if c:
                meas[s] = c["paired_robustness"]["n_both_solve"]
        records.append(ER.verify_table(
            "starts both A0' and A1' solve", pub.get("n_both_solve", {}), meas))
    if not records:
        print("nothing to verify: no analysis artifacts found under "
              f"{a28}.  Run the experiment first.")
        return 2
    (a28 / "_verification_a28.json").write_text(
        json.dumps(records, indent=2, default=str))
    return ER.print_verification(records)


# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__.split("HOW TO RUN IT")[0].strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS,
                    help="which input decks to run; results are always "
                         "reported per deck and never pooled")
    ap.add_argument("--arms", nargs="*", default=ALL_ARMS,
                    help="which arrangements to run")
    ap.add_argument("--stages", nargs="*", default=None,
                    help="run only these stages, in order: "
                         + ", ".join(s.name for s in STAGES))
    ap.add_argument("--quick", action="store_true",
                    help="smoke mode: one deck, three arrangements, a few "
                         "starts and a short ladder.  Exercises every stage "
                         "in minutes.  Its counts are its own and must not be "
                         "compared with the report's")
    ap.add_argument("--verify", action="store_true",
                    help="run nothing; compare a finished run's numbers with "
                         "the published ones, per deck, with denominators")
    ap.add_argument("--parent-tree", default=None,
                    help="an unmodified checkout of the base commit.  Enables "
                         "the switch-neutrality check; without it that stage "
                         "is skipped and said to be skipped")
    ap.add_argument("--starts", type=int, default=24,
                    help="perturbed starting points per arrangement per deck")
    ap.add_argument("--calibration-starts", type=int, default=12)
    ap.add_argument("--ladder-starts", type=int, default=1)
    ap.add_argument("--delta", type=float, default=None,
                    help="perturbation size; default is whatever the "
                         "calibration stage measured")
    ap.add_argument("--deltas", nargs="*", type=float,
                    default=[0.01, 0.05, 0.10])
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--runs-root", default=str(RUNS_ROOT),
                    help="where the artifacts live (default: this tree's "
                         "arch_surgery/idf_probe/runs, which is untracked)")
    args = ap.parse_args()

    if args.quick:
        args.scenarios = args.scenarios[:1]
        args.arms = [a for a in args.arms if a in CORE_ARMS]
        args.starts = 3
        args.calibration_starts = 2
        args.deltas = [0.10]
        args.ladder_starts = 1
        args.jobs = min(args.jobs, 3)

    runs_root = Path(args.runs_root).resolve()

    if args.verify:
        ER.print_provenance()
        return stage_verify(args, runs_root)

    ER.check_prerequisites(
        args.scenarios,
        need_artifacts=("ystate_{scenario}.json", "writeset_{scenario}.json"),
        runs_root=runs_root,
    )

    stages = STAGES
    if args.stages:
        unknown = [s for s in args.stages
                   if s not in {x.name for x in STAGES}]
        if unknown:
            print(f"unknown stage(s): {unknown}; known: "
                  f"{[s.name for s in STAGES]}")
            return 2
        stages = [s for s in STAGES if s.name in args.stages]
    skipped = []
    if not args.parent_tree:
        skipped = [s for s in stages if s.name in NEEDS_PARENT_TREE]
        stages = [s for s in stages if s.name not in NEEDS_PARENT_TREE]

    ER.print_provenance()
    ER.print_plan("MDA partition experiment, Phase B (the optimiser is present)",
                  stages, quick=args.quick, scenarios=args.scenarios,
                  runs_root=runs_root / A28, skipped=skipped)
    (runs_root / A28).mkdir(parents=True, exist_ok=True)
    (runs_root / "_mplconfig").mkdir(parents=True, exist_ok=True)

    results = {}
    for s in stages:
        results[s.name] = s.fn(args, runs_root)
        if results[s.name] != 0:
            print(f"\nSTOPPING: stage '{s.name}' exited {results[s.name]}.",
                  flush=True)
            break
    print("\n=== summary")
    for s in STAGES:
        if s.name in results:
            v = results[s.name]
            print(f"  {s.name:<14}{'ok' if v == 0 else f'FAILED ({v})'}")
        elif s in skipped:
            print(f"  {s.name:<14}skipped (no --parent-tree)")
        else:
            print(f"  {s.name:<14}not run")
    return 0 if all(v == 0 for v in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
