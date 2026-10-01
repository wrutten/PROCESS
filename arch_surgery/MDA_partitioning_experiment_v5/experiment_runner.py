#!/usr/bin/env python
"""The button: run the experiment, or say exactly why it cannot be run yet.

Derived from ``arch_surgery/MDA_partitioning_experiment_v3/run_experiment.py``
at ``f2dc9243`` (task A47).  Press Run: no arguments are needed.

The **preflight** refuses to start under an interpreter that cannot import
PROCESS, names the tree it will measure and the commit it is at, resolves every
configuration and every artifact, asks the tree itself which switches it
implements, prints the switch matrix and the rung table with the check that they
agree with the plan, and lists the chain one press runs — the smoke's and the
campaign's, which are the same chain.  Every campaign stage refuses while the
plan is not approved, and the refusal is reachable from this same entry point —
a failure path that can only be reached by retyping a command line is not
reproducible.

Everything else is here too, each as a stage of this one script: the gates
(``--gate``), the measurement stages (``--measure``), the artifact stages
(``--artifacts``), the reproduction reference (``--reference``), one run
(``--run``), the harness's own checks (``--selfcheck``), the paper's one
generated document (``--paper-tables``), and **the chain**
— ``--smoke`` runs it once on one seed and the cheapest configuration with every
record stamped ``smoke``; the campaign runs the same stages over every
configuration and the plan's seed count, and is refused until the user approves
execution.

Exit codes: 0 ready · 2 refused to start · 3 not ready.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from harness.experiment import arms as arms_mod  # noqa: E402
from harness.experiment import artifacts as artifacts_mod  # noqa: E402
from harness.child import census as census_mod  # noqa: E402
from harness.experiment import test_sets as test_sets_mod  # noqa: E402
from harness.measurement import test_set_smoke as test_set_smoke_mod  # noqa: E402
from harness.measurement import timing as timing_mod  # noqa: E402
from harness import chain as chain_mod  # noqa: E402
from harness.gates import gate_neutrality as neutrality_mod  # noqa: E402
from harness.gates import gates as gates_mod  # noqa: E402
from harness.gates import registry as registry_mod  # noqa: E402
from harness.experiment import input_files as input_files_mod  # noqa: E402
from harness.child import postsolve as postsolve_mod  # noqa: E402
from harness.core import provenance as prov  # noqa: E402
from harness.measurement import paper_tables as paper_tables_mod  # noqa: E402
from harness.core import framework as framework_mod  # noqa: E402
from harness.core import pool as pool_mod  # noqa: E402
from harness.core import records as records_mod  # noqa: E402
from harness.core import run_layout  # noqa: E402
from harness.gates import archived_records as archived_records_mod  # noqa: E402
from harness import run_isolation as run_isolation_mod  # noqa: E402
from harness.gates import reference as reference_mod  # noqa: E402
from harness.gates import selfcheck as selfcheck_mod  # noqa: E402
from harness.core.config import (  # noqa: E402
    CAMPAIGN_TIMERS,
    DEFAULT_RUN_ID,
    EXECUTION_APPROVED,
    TAU_BY_TEST_SET,
    TAU_RULES,
    TEST_SETS,
    Campaign,
    default_campaign,
)

WIDTH = 74
_PIN_PLACEHOLDER = float(1234.5).hex()


def _rule(title: str) -> None:
    print(f"\n--- {title} " + "-" * max(3, WIDTH - len(title) - 5))


# --------------------------------------------------------------------------
# preflight stages
# --------------------------------------------------------------------------


def stage_interpreter(campaign: Campaign) -> tuple[int, dict[str, Any]]:
    """Refuse before anything else if this interpreter cannot run PROCESS."""
    _rule("interpreter")
    try:
        process_file = prov.assert_interpreter(campaign.tree)
    except prov.ProvenanceError as exc:
        print(str(exc))
        return 2, {"ok": False, "error": str(exc)}
    print(f"  {sys.executable}")
    print(f"  imports PROCESS from {process_file}")
    same = Path(process_file).resolve().parent.parent == Path(campaign.tree).resolve()
    if not same:
        print(
            "  note: that is not the tree under test.  The editable install "
            "points at the main checkout and a worktree does not redirect it, "
            "so every measurement subprocess sets PYTHONPATH to the tree "
            "under test and asserts it for equality (trap T6).  This stage "
            "only asks whether the interpreter can run PROCESS at all."
        )
    return 0, {
        "ok": True,
        "python": sys.executable,
        "process_file": process_file,
        "is_tree_under_test": same,
    }


def stage_tree(campaign: Campaign) -> tuple[int, dict[str, Any]]:
    """Name the tree that will be measured, and stamp its commit."""
    _rule("tree and commit")
    present = (campaign.tree / "process" / "__init__.py").exists()
    record: dict[str, Any] = {"tree": str(campaign.tree)}
    if present:
        record = prov.git_stamp(campaign.tree)
        print(prov.banner(record))
    record["process_package_present"] = present
    if not present:
        print(f"  tree       {campaign.tree}")
        print(
            f"  MISSING    no PROCESS package at {campaign.tree}.  The "
            f"experiment runs its own copy; it is created by the task that "
            f"owns it.  Nothing falls back to another tree — a fallback "
            f"would measure code nobody asked for."
        )
        return 3, record
    return 0, record


def stage_configurations(campaign: Campaign) -> tuple[int, dict[str, Any]]:
    """Resolve every configuration, then *check* every artifact it reads.

    The check is ``artifacts.check``, which **replaces** the existence-and-count
    test this stage used to make.  The reason is worth stating: a file can
    exist, carry the declared component count, and still have been built for a
    different configuration, against a different component set, or from a
    generation of the scales nobody can identify.  Each of those has a stamp,
    and each stamp is now rebuilt and compared rather than assumed.  What is
    kept from the old stage is the human summary — what each configuration is
    and which arms it skips — because that is orientation, not verification.
    """
    _rule("configurations and artifacts")
    records = []
    for config in campaign.configurations:
        kind = "pulsed" if config.pulsed else "steady state"
        print(
            f"  {config.name:24s} {kind:12s} "
            f"objective {config.figure_of_merit:>3d} "
            f"({config.figure_of_merit_name})"
        )
        print(
            f"    {config.n_iteration_variables} variables, "
            f"{config.n_constraints} constraints, "
            f"{config.n_coupling_components} coupling-state components"
        )
        for arm, why in config.skips.items():
            print(f"    skipped: {arm} — {why}")
        records.append(
            {
                "configuration": config.name,
                "pulsed": config.pulsed,
                "declared_n_components": config.n_coupling_components,
                "skips": dict(config.skips),
            }
        )
    for removal in campaign.removed_configurations:
        print(
            f"  removed: {removal.configuration} — {removal.decision}, "
            f"{removal.date}: {removal.reason}"
        )
    code, checked = artifacts_mod.check(campaign)
    print()
    for line in artifacts_mod.ledger_table(checked):
        print(line)
    print()
    for line in artifacts_mod.report(checked):
        print(line)
    print(
        f"\n  {len(campaign.configurations)} configuration(s) in the "
        f"population; {checked['n_compared']} artifact check(s) made, "
        f"{checked['n_mismatched']} failed"
    )
    return code, {"configurations": records, "artifacts": checked}


def stage_matrix(campaign: Campaign) -> tuple[int, dict[str, Any]]:
    """Print the switch matrix and the rung table, and check both."""
    _rule("switch matrix and rungs")
    order = arms_mod.MATRIX_ORDER
    print("  " + " " * 42 + "".join(f"{n:>13s}" for n in order))
    for row, cells in arms_mod.matrix().items():
        print(f"  {row:<42s}" + "".join(f"{c:>13s}" for c in cells))
    print("\n  rungs (what each step changes, computed from the arms):")
    for rung_row in arms_mod.RUNGS:
        for step in (rung_row.phase_a, rung_row.phase_b):
            changed = arms_mod.rung(*step)
            body = ", ".join(
                f"{f}: {a} -> {b}" for f, (a, b) in changed.items()
            )
            print(f"    {step[0]:>4s} -> {step[1]:<4s}  {body}")
        print(f"        isolates: {rung_row.isolates}")
    check = selfcheck_mod.check_rungs()
    print(
        f"\n  {'PASS' if check.passed else 'FAIL'}: "
        f"{check.n_compared} comparisons, {check.n_mismatched} mismatched "
        f"({check.population})"
    )
    for line in check.detail:
        print(f"  . {line}")
    return (0 if check.passed else 3), check.as_record()


def stage_capability(campaign: Campaign, *, probe: bool = True) -> tuple[int, dict]:
    """Ask the tree which switches it implements, arm by arm."""
    _rule("capability of the tree")
    if not probe:
        print("  skipped (--no-capability)")
        return 0, {"skipped": True}
    check = selfcheck_mod.check_capability(campaign)
    print(
        f"  {'PASS' if check.passed else 'FAIL'}: {check.n_compared} "
        f"arm/configuration pair(s) examined, {check.n_mismatched} refused "
        f"unexpectedly"
    )
    for line in check.detail:
        print(f"  . {line}")
    for tooth in check.teeth:
        mark = "tripped" if tooth["caught"] else "DID NOT TRIP"
        print(f"  tooth {mark}: {tooth['tooth']}")
    return (0 if check.passed else 3), check.as_record()


def stage_reference(campaign: Campaign) -> tuple[int, dict[str, Any]]:
    """The committed reproduction reference: what the rewrite must reproduce.

    The reference holds the compared fields of the previous revision's twenty
    reference runs, so that the reproduction gate reads a committed file
    rather than untracked run records that a retired working tree can delete
    — which has happened to this project three times.  This stage reports
    what is committed; the file is not regenerated (D25) and its provenance
    block names the records it was extracted from.
    """
    _rule("reproduction reference")
    try:
        document = reference_mod.load()
    except reference_mod.ReferenceError as exc:
        print(f"  MISSING    {exc}")
        return 3, {"present": False, "error": str(exc)}
    for line in reference_mod.summary(document):
        print(line)
    provenance = document["provenance"]
    return 0, {
        "present": True,
        "path": str(reference_mod.REFERENCE_PATH),
        "n_entries": len(document["entries"]),
        "source_revision": provenance["source_revision"],
        "population": provenance["population"],
        "compared_fields": provenance["compared_fields"],
        "not_covered": provenance["not_covered_by_this_reference"],
    }


def stage_campaign(campaign: Campaign) -> tuple[int, dict[str, Any]]:
    """The campaign: the chain it runs, what it would cost, and why it refuses.

    The campaign and the smoke are **one chain with two parameterisations**
    (``harness/chain.py``), so this stage prints the stage list the smoke also
    runs rather than describing a second thing.  What separates them is the
    plan: the campaign's asks for every configuration, the plan's seed count
    and records stamped ``campaign``, and it is refused unless the user has
    approved execution and the tree is the experiment's own copy.

    Reachable from the button so that the refusal is as reproducible as a
    result would be (protocol §15).
    """
    _rule("campaign")
    plan = chain_mod.campaign_plan(campaign)
    reasons = chain_mod.refusals(plan, campaign)
    for reason in reasons:
        print(f"  REFUSED — {reason}")
    print("\n  the chain one press runs, in order:")
    for stage in chain_mod.stage_names(plan):
        skipped = stage.get("skipped")
        mark = f"  — SKIPPED: {skipped}" if skipped else ""
        print(f"    {stage['stage']:<24} [{stage['kind']:<11}] "
              f"{stage['what']}{mark}")
    try:
        registry_check = chain_mod.assert_stages_exist(campaign)
        print(
            f"\n  every one of the {registry_check['n_reading_stages']} stages "
            f"that read the records is in the registry"
        )
    except chain_mod.ChainError as exc:
        print(f"\n  REFUSED — {exc}")
        reasons.append(str(exc))
        registry_check = {"missing": str(exc)}
    budget = plan.budget(campaign)
    print(
        f"\n  would run: {budget['entry_references']} entry reference(s) + "
        f"{budget['evaluation_displaced']} displaced-entry evaluations + "
        f"{budget['optimisation']} optimisations = {budget['total']} runs"
    )
    smoke = chain_mod.smoke_plan(campaign)
    smoke_budget = smoke.budget(campaign)
    print(
        f"\n  the smoke is the same chain, available now: "
        f"--smoke runs {smoke_budget['total']} run(s) on "
        f"{smoke.configurations[0].name}, records stamped "
        f"{smoke.run_kind!r}, then the tally and its contract gate"
    )
    return 3, {
        "refused": reasons,
        "budget": budget,
        "stages": chain_mod.stage_names(plan),
        "registry": registry_check,
        "smoke": {
            "configuration": smoke.configurations[0].name,
            "budget": smoke_budget,
            "run_kind": smoke.run_kind,
        },
    }


def stage_smoke(args: argparse.Namespace, campaign: Campaign) -> int:
    """The one-seed pass: the whole chain, from this entry point, once.

    It runs the **campaign's** stages — the same functions, with one seed, one
    configuration and records stamped ``smoke`` — then the two tally stages
    and the tally's contract gate.  Nothing here is a measurement: the tally
    refuses to summarise a smoke record, and gate ``run_kind_separation`` has a
    tooth for each direction of that refusal.
    """
    _rule("smoke — the campaign's chain, one seed")
    chosen = chain_mod.cheapest_configuration(campaign)
    print(f"  cheapest configuration, chosen from {chosen['basis']}:")
    print(
        f"    {'configuration':24}{'runs':>6}{'node calls':>12}"
        f"{'wall s':>9}  route"
    )
    for row in chosen["rows"]:
        print(
            f"    {row['configuration']:24}{row['n_runs_in_the_smoke']:>6}"
            f"{row['node_calls']:>12}{row['wall_s']:>9}  {row['route']}"
            + (
                f"  (no record for {row['arms_without_a_record']})"
                if row["arms_without_a_record"]
                else ""
            )
        )
    print(
        f"    chosen: {chosen['chosen']['configuration']}.  Node-call counts "
        f"are exact; the wall clock beside them is progress information and "
        f"chooses nothing (I-10)"
    )
    try:
        plan = chain_mod.plan_for(
            "smoke", campaign, configuration=args.configuration or None
        )
    except chain_mod.ChainError as exc:
        print(f"  REFUSED — {exc}")
        return 3
    gates_mod.CENSUS_ENTRY["entry"] = args.census_entry
    # DR12 (V5 plan §9; D33): the campaign runs with the timers on.
    campaign = dataclasses.replace(campaign, timers=CAMPAIGN_TIMERS)
    print(f"  wall-clock timers: {'on' if campaign.timers else 'off'} (config.CAMPAIGN_TIMERS)")
    press = chain_mod.run(
        campaign,
        plan,
        resume=args.resume,
        records_dir=_gate_records_dir(args, campaign),
        teeth=not args.no_teeth,
    )
    chain_mod.print_press(press)
    out = args.json or (chain_mod.chain_root(campaign, plan) / "press.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(press, indent=2, default=str) + "\n")
    print(f"\n  record: {out}")
    return 3 if press.get("refused") else 0


def campaign_press_composition(campaign: Campaign) -> Campaign:
    """The campaign as the campaign press composes it, and as nothing else does.

    DR12 (V5 plan §9; D33): the campaign runs with the wall-clock timers on.
    Composed here as the smoke composes them (A101 wired the smoke and reported
    the campaign press as wired too; it was not -- found by A102 (v5-campaign)
    before its campaign press, from the code).  One function, so that
    ``--reading-stages campaign-press`` reads the records under the press's own
    composition rather than a retyped one (issue I-37).
    """
    return dataclasses.replace(campaign, timers=CAMPAIGN_TIMERS)


#: The two compositions ``--reading-stages`` presses the chain's reading
#: stages under: the campaign press's, and the plain campaign every ``--gate``
#: and ``--measure`` press uses.
READING_STAGE_COMPOSITIONS = ("campaign-press", "plain")


def stage_reading_stages(args: argparse.Namespace, campaign: Campaign) -> int:
    """The chain's reading stages alone, over the records on disk: the two
    tallies and the tally's contract gate, under the composition named —
    ``campaign-press`` (:func:`campaign_press_composition`, the timers on) or
    ``plain`` — with no run stage and no PROCESS run.

    Issue I-37: ``tally_contracts`` failed inside the campaign press and passed
    pressed alone, and only a whole campaign press could reach it under the
    press's composition.  This presses exactly the stages the press runs after
    its runs (``chain.run_reading_stages``, the function the press calls),
    under the press's composition, read-only.  Verdicts and stage records go
    where ``--outdir`` says, or to the campaign's records directory.
    """
    composed = (
        campaign_press_composition(campaign)
        if args.reading_stages == "campaign-press"
        else campaign
    )
    records_dir = _gate_records_dir(args, campaign)
    _rule(
        f"the chain's reading stages, composed as {args.reading_stages!r} "
        f"(wall-clock timers {'on' if composed.timers else 'off'})"
    )
    print(f"  records to: {records_dir}")
    stages, refused = chain_mod.run_reading_stages(
        composed, records_dir=records_dir, resume=args.resume, teeth=not args.no_teeth
    )
    for block in stages:
        if block["kind"] == "gate":
            print(
                f"  {block['stage']:<20} {block['verdict']}: {block['n_mismatched']} of "
                f"{block['n_compared']} mismatched; teeth {block['n_teeth_tripped']}/{block['n_teeth']}"
            )
        else:
            print(f"  {block['stage']:<20} {block['n_tables']} table(s); {block['population']}")
    if refused:
        print(f"  REFUSED — {refused}")
    out = args.json or (records_dir / "reading_stages" / f"{args.reading_stages}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "composition": args.reading_stages,
                "run": run_layout.stamp(campaign),
                "timers": bool(composed.timers),
                "resumed": bool(args.resume),
                "tree_git_head": framework_mod.git_head(),
                "stages": stages,
                "refused": refused,
            },
            indent=2,
            default=str,
        )
        + "\n"
    )
    print(f"\n  record: {out}")
    return 3 if refused else 0


def stage_campaign_press(args: argparse.Namespace, campaign: Campaign) -> int:
    """The campaign: the whole chain, every configuration, the plan's seeds.

    The same functions the smoke runs (``chain.run`` on ``plan_for``), with the
    campaign plan: every configuration, ``campaign.n_seeds`` seeds, records
    stamped ``campaign``.  ``chain.plan_for`` refuses it until the user has
    approved execution (``EXECUTION_APPROVED`` flipped in the same commit as the
    dated approval in ``EXPERIMENT_REPORT.md``) and the tree is the experiment's
    own copy; the refusal is printed and the exit code is 3, so pressing this
    before approval is a reproducible refusal, not a crash (protocol §15).
    Added 2026-09-14 when the user approved execution: until then the preflight
    printed the budget and nothing on the button could ask for the campaign.
    """
    _rule("campaign — the chain, every configuration, the plan's seeds")
    print("=" * WIDTH)
    print("MDA partitioning experiment — report: EXPERIMENT_REPORT.md")
    print(f"execution approved: {EXECUTION_APPROVED}")
    print("=" * WIDTH)
    try:
        plan = chain_mod.plan_for("campaign", campaign)
    except chain_mod.ChainError as exc:
        print(f"  REFUSED — {exc}")
        return 3
    budget = plan.budget(campaign)
    campaign = campaign_press_composition(campaign)
    print(
        f"  will run: {budget['entry_references']} entry reference(s) + "
        f"{budget['evaluation_displaced']} displaced-entry evaluations + "
        f"{budget['optimisation']} optimisations = {budget['total']} runs, "
        f"records stamped {plan.run_kind!r}, {pool_mod.workers(campaign)} worker(s) "
        f"(HARNESS_WORKERS or the campaign's {campaign.workers}), wall-clock timers "
        f"{'on' if campaign.timers else 'off'} (config.CAMPAIGN_TIMERS)"
    )
    gates_mod.CENSUS_ENTRY["entry"] = args.census_entry
    press = chain_mod.run(
        campaign,
        plan,
        resume=args.resume,
        records_dir=_gate_records_dir(args, campaign),
        teeth=not args.no_teeth,
    )
    chain_mod.print_press(press)
    out = args.json or (chain_mod.chain_root(campaign, plan) / "press.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(press, indent=2, default=str) + "\n")
    print(f"\n  record: {out}")
    return 3 if press.get("refused") else 0


def stage_single_run(args: argparse.Namespace, campaign: Campaign) -> int:
    """One run, from the button: one arm, one configuration, one seed, one phase.

    Not a campaign: the run kind is ``gate`` or ``smoke``, never ``campaign``,
    and the record says so.  This is how a single arm is looked at without
    inventing a command line for it — every stage of the experiment, successes
    and refusals alike, is reachable from this entry point (protocol §15).
    """
    _rule("one run")
    try:
        config = campaign.configuration(args.configuration)
    except KeyError as exc:
        print(f"  REFUSED — {exc}")
        return 3
    arm = arms_mod.ARMS.get(args.arm)
    if arm is None:
        print(
            f"  REFUSED — {args.arm!r} is not an arm of this experiment; the "
            f"arms are {', '.join(arms_mod.MATRIX_ORDER)}"
        )
        return 3
    phase = arm.phase
    # The test set and the tolerance are in the directory name (DR11): a
    # run under the census set and one under the fallback of the same arm
    # and seed are two records, and a named directory is the job's.
    outdir = Path(args.outdir) if args.outdir else (
        campaign.runs_dir
        / "single"
        / config.name
        / arm.name
        / (
            f"{campaign.test_set}_tau{campaign.tau_for(config)!r}"
            + (f"_rule_{campaign.tau_rule}" if campaign.tau_rule is not None else "")
        )
        / pool_mod.seed_directory(args.seed)
    )
    job = pool_mod.Job(
        phase=phase,
        arm=arm.name,
        config=config,
        seed=args.seed,
        outdir=outdir,
        regime=args.regime,
        delta=(None if args.delta is None else float(args.delta)),
        pin_hex=args.pin_hex,
        entry_state=(Path(args.entry_state) if args.entry_state else None),
        stencil_column=args.stencil_column,
        stencil_sign=args.stencil_sign,
        run_kind=(args.run_kind or "smoke"),
        timers=(True if args.timers else None),
    )
    print(
        f"  {arm.name} on {config.name}, seed {args.seed}, phase {phase}, "
        f"regime {args.regime}, kind {args.run_kind or 'smoke'}, test set "
        f"{campaign.test_set}, tau {campaign.tau_for(config)!r}"
        + (
            f" (rule {campaign.tau_rule})"
            if campaign.tau_rule is not None
            else (" (overridden)" if campaign.tau_overridden else " (the test set's declared value)")
        )
    )
    try:
        result = pool_mod.run(job, campaign, resume=args.resume)
    except (pool_mod.PoolError, Exception) as exc:  # noqa: BLE001
        print(f"  REFUSED — {exc}")
        return 3
    record = records_mod.read(outdir)
    print(f"  status {result['status']!r}  taxonomy {result['failure_class']!r}")
    print(
        f"  stamped: test set {record.get('campaign_test_set')!r}, tau "
        f"{record.get('campaign_tau')!r}, tolerance rule {record.get('campaign_tau_rule')!r}"
        + (
            f" (derivation: {record['tau_rule_derivation'].get('formula')}, epsvmc "
            f"{record['tau_rule_derivation'].get('epsvmc')!r} from "
            f"{record['tau_rule_derivation'].get('epsvmc_from')})"
            if isinstance(record.get("tau_rule_derivation"), dict)
            else ""
        )
    )
    if phase == "B":
        print(
            f"  counts: ifail {(record.get('mfile') or {}).get('ifail')!r}, solver "
            f"iterations {record.get('n_solver_iterations')!r}, evaluations "
            f"{(record.get('sweeps_per_eval') or {}).get('n_evaluations')!r}, solve-phase "
            f"node calls {record.get('node_calls_solve_phase')!r}, attempts "
            f"{(record.get('exit_forensics') or {}).get('n_attempts')!r} — plumbing "
            f"evidence of one smoke run, never a result"
        )
    print(f"  record {outdir / 'metrics.json'}")
    completeness = record.get("completeness") or {}
    print(
        "  record contract: "
        + ("complete" if completeness.get("complete") else
           f"INCOMPLETE — {completeness.get('refusal')}")
    )
    return 0 if result["status"] == "ok" else 1


def _gate_records_dir(args: argparse.Namespace, campaign: Campaign) -> Path:
    """Where a gate's verdict goes.

    ``--outdir`` redirects it.  It did not before: ``--gate reproduction``
    wrote to the campaign's records directory whatever ``--outdir`` said, which
    task A57 (driver-output-path) recorded as a quirk worth one line.  This is
    that line, and it applies to every gate rather than to one.
    """
    if args.outdir:
        # A verdict sent into another run ID's folder would be read there as
        # that run ID's (task A107 (v5-campaign-settings-keys)); refused.
        return pool_mod.refuse_another_runs_folder(Path(args.outdir), campaign)
    return Path(campaign.runs_dir) / gates_mod.GATES_SUBPATH


def stage_gate(args: argparse.Namespace, campaign: Campaign) -> int:
    """One gate, or every gate, from the button.

    Every gate returns a verdict and writes its record; a failed gate stops the
    chain and is **reported**, never retried with different settings (protocol
    §6).  ``--gate all`` runs them cheapest first, so a repository-state failure
    is reported in seconds rather than after an hour of runs.
    """
    records_dir = _gate_records_dir(args, campaign)
    # `--outdir` moves the **verdicts**, not the gates' runs.  The output-path
    # gate reads the reproduction gate's own runs at their declared place to
    # show that nothing about the solve changed on the arms that keep the loop,
    # so moving those runs would break a cross-reference between two gates in
    # order to relocate a small JSON file.
    gates_mod.CENSUS_ENTRY["entry"] = args.census_entry
    if not args.resume:
        print(
            "  --resume was not asked for, so every gate re-makes its own "
            "runs.  Gate G1's 'before' capture is the one exception and says "
            "why; the shared cold-flat references are made once per invocation "
            "and shared by the gates anchored on them."
        )

    if args.capture:
        if args.gate != "switch_neutrality":
            print(
                f"  REFUSED — --capture is gate switch_neutrality's; "
                f"{args.gate!r} makes its own runs.  Two steps exist there "
                f"because its two sides are at two commits, which is a "
                f"property of that gate and of no other."
            )
            return 3
        manifest = neutrality_mod.capture_neutrality(
            campaign, args.capture, resume=args.resume
        )
        print(
            f"  captured {manifest['n_runs']} run(s) as {args.capture!r}; records "
            f"at {manifest['tree_git_head'] or manifest['records_git_heads']}, "
            f"pressed at {manifest['pressed_at_git_head']}"
        )
        for row in manifest["runs"]:
            print(f"    {row['arm']:<3} {row['configuration']:<22} {row['outdir']}")
        print(f"    manifest: {manifest['manifest']}")
        return 0

    available = registry_mod.gates_only(campaign)
    names = (
        registry_mod.ordered_gate_names(campaign)
        if args.gate == "all"
        else [args.gate]
    )
    unknown = [n for n in names if n not in available]
    if unknown:
        print(
            f"  REFUSED — {unknown} is not a registered gate.  The registry "
            f"holds {sorted(available)}; a measurement stage runs under "
            f"--measure, not --gate, because it has no verdict."
        )
        return 3
    stages = registry_mod.measurements(campaign)
    made: set[str] = set()
    status = 0
    for name in names:
        gate = available[name]
        # A gate may declare that it reads a **measurement stage's output**, not
        # only another gate's runs.  Such a stage is run here, immediately
        # before the gate and with the same --resume, so the gate is never
        # compared against a stage record nobody made — and, once made in this
        # press, not re-made for a second gate that declares it.
        for dependency in registry_mod.measurement_dependencies(campaign, name):
            if dependency in made:
                continue
            _rule(f"measurement {dependency} — declared by gate {name}")
            print(f"  {stages[dependency].reports}")
            try:
                stages[dependency].run(
                    records_dir=records_dir, resume=args.resume
                )
            except (gates_mod.GateError, FileNotFoundError, KeyError) as exc:
                print(f"  REFUSED TO RUN — {exc}")
                return 3
            made.add(dependency)
        _rule(f"gate {name}" + (f" ({gate.plan_name})" if gate.plan_name else ""))
        try:
            verdict = gate.run(
                records_dir=records_dir,
                teeth=not args.no_teeth,
                resume=args.resume,
            )
        except gates_mod.GateError as exc:
            print(f"  REFUSED TO RUN — {exc}")
            status = 3
            if args.gate == "all":
                print(
                    "\n  the chain stops here.  A refused gate is a result, "
                    "not an obstacle: nothing below is run with different "
                    "settings."
                )
                break
            continue
        registry_mod.print_verdict(verdict)
        if verdict["verdict"] != "PASS":
            status = 1
            if args.gate == "all":
                print(
                    f"\n  gate {name!r} did not pass; the chain stops here.  "
                    f"A failed gate is a result, not an obstacle."
                )
                break
    return status


def stage_measure(args: argparse.Namespace, campaign: Campaign) -> int:
    """One measurement stage, or every one, from the button.

    A measurement has no verdict: it publishes what the experiment plan asks
    for by name.  It is a separate option from ``--gate`` so that nothing can
    be read as a gate that is not one.
    """
    records_dir = _gate_records_dir(args, campaign)
    available = registry_mod.measurements(campaign)
    names = sorted(available) if args.measure == "all" else [args.measure]
    unknown = [n for n in names if n not in available]
    if unknown:
        print(
            f"  REFUSED — {unknown} is not a registered measurement stage.  "
            f"The registry holds {sorted(available)}; a gate runs under "
            f"--gate."
        )
        return 3
    status = 0
    for name in names:
        stage = available[name]
        _rule(f"measurement {name}")
        print(f"  reports: {stage.reports}")
        print(f"  guarded by gate: {stage.guarded_by}")
        try:
            stage.run(records_dir=records_dir, resume=args.resume)
        except (gates_mod.GateError, FileNotFoundError, KeyError) as exc:
            print(f"  REFUSED — {type(exc).__name__}: {exc}")
            status = 3
    return status


def stage_paper_tables(args: argparse.Namespace, campaign: Campaign) -> int:
    """The paper's one document, computed from the campaign's run records.

    ``show`` prints ``paper_tables.md``, ``write`` writes it, ``check``
    compares it without writing and refuses when the rendered file and the
    records disagree (V5 list item 10).  The numbers are computed with the
    tally's own constructions over the tally's own population; every cell the
    stage records also hold is compared with them exactly first, and a
    mismatch refuses the write.  ``--paper-tables-runs`` reads the records
    from another runs root — a relocated tree's, for a check against test
    data — and writes nothing there.
    """
    _rule("the paper's results tables")
    campaign = paper_tables_mod.with_runs(campaign, args.paper_tables_runs)
    records_dir = (
        Path(args.outdir)
        if args.outdir
        else Path(campaign.runs_dir) / gates_mod.GATES_SUBPATH
    )
    # A render from another runs root — test data — must not become the
    # committed document: ``--paper-tables-out`` names the file instead.
    out = Path(args.paper_tables_out) if args.paper_tables_out else None
    if args.paper_tables_runs is not None and out is None and args.paper_tables != "show":
        print(
            "  REFUSED — --paper-tables-runs reads another tree's records; a "
            "write or check against them needs --paper-tables-out so that the "
            "rendering lands beside those records and not as this folder's "
            "paper_tables.md"
        )
        return 3
    try:
        if args.paper_tables == "write":
            result = paper_tables_mod.write(campaign, records_dir, path=out)
        elif args.paper_tables == "check":
            result = paper_tables_mod.check(campaign, records_dir, path=out)
        else:
            result = paper_tables_mod.render(campaign, records_dir)
    except paper_tables_mod.PaperTablesError as exc:
        print(f"  REFUSED — {exc}")
        return 3
    paper_tables_mod.report(result)
    if args.paper_tables == "show":
        print()
        print(result["markdown"])
    if result["cross_check"]["mismatched"] or not result["tooth"]:
        return 3
    return 0


def stage_jobs(args: argparse.Namespace, campaign: Campaign) -> int:
    """One gate's job set, by identity, and what ``--resume`` would do with each.

    Nothing runs.  The gate's ``jobs`` declaration is composed from the records
    on disk — a dependent job carries its reference's exit state, so a gate
    whose references are not made yet says so by name — and each job is
    printed with its key, its digest, the shared pool's directory and
    ``records.why_not_complete_for``'s sentence, or KEPT where a complete
    record of exactly that job is there.  That sentence is the whole of the
    resume decision (rule (vii)); this shows it without pressing anything.
    With ``all``, the union over every gate, and which gates share each job.
    """
    if args.jobs == CAMPAIGN_JOBS:
        return stage_campaign_jobs(args, campaign)
    _rule(f"jobs of gate {args.jobs}")
    available = registry_mod.gates_only(campaign)
    names = registry_mod.ordered_gate_names(campaign) if args.jobs == "all" else [args.jobs]
    unknown = [n for n in names if n not in available]
    if unknown:
        print(f"  REFUSED — {unknown} is not a registered gate")
        return 3
    by_digest: dict[str, dict[str, Any]] = {}
    readers: dict[str, list[str]] = {}
    refused: list[str] = []
    for name in names:
        gate = available[name]
        if gate.jobs is None:
            if args.jobs != "all":
                print(
                    f"  gate {name} declares no job set"
                    + (f"; it reads run records under {list(gate.runs_under)}" if gate.runs_under else "")
                )
            continue
        try:
            rows = list(gate.jobs())
        except gates_mod.GateError as exc:
            print(f"  gate {name}: not composable yet — {exc}")
            continue
        except pool_mod.PoolError as exc:
            print(f"  gate {name}: REFUSED by the pool — {exc}")
            refused.append(name)
            continue
        except Exception as exc:  # noqa: BLE001 - the reproduction gate's own refusal
            if type(exc).__name__ != "ReproductionError":
                raise
            print(f"  gate {name}: not composable yet — {exc}")
            continue
        for row in rows:
            by_digest.setdefault(row["job_digest"], row)
            readers.setdefault(row["job_digest"], []).append(name)
        if args.jobs != "all":
            kept = sum(1 for r in rows if r["why_not_complete"] is None)
            print(f"  {len(rows)} distinct job(s); --resume would keep {kept}\n")
            for row in rows:
                state = "KEPT" if row["why_not_complete"] is None else f"RUN — {row['why_not_complete']}"
                relative = framework_mod._relative(Path(row["path"]), Path(campaign.runs_dir) / gates_mod.GATES_SUBPATH)
                print(f"    {row['key']}")
                print(f"      digest {row['job_digest'][:16]}  {relative}")
                print(f"      {state}")
    if args.jobs == "all":
        shared = {d: g for d, g in readers.items() if len(g) > 1}
        kept = sum(1 for r in by_digest.values() if r["why_not_complete"] is None)
        print(
            f"  {len(by_digest)} distinct job(s) over {len(names)} gate(s); "
            f"{sum(len(g) for g in readers.values())} gate-job declarations; "
            f"{len(shared)} job(s) read by more than one gate; --resume would "
            f"keep {kept}\n"
        )
        for digest, gates in sorted(shared.items(), key=lambda kv: by_digest[kv[0]]["key"]):
            print(f"    {by_digest[digest]['key']}  <- {', '.join(gates)}")
    if refused:
        print(f"\n  REFUSED by the pool: {refused}")
        return 3
    return 0


#: The name ``--jobs`` takes for the campaign press's own job set rather than
#: a gate's.  No gate may be registered under it.
CAMPAIGN_JOBS = "campaign"


def stage_campaign_jobs(args: argparse.Namespace, campaign: Campaign) -> int:
    """The campaign press's job set, by identity, and what ``--resume`` would
    do with each.  Nothing runs.

    The same jobs the press composes — ``chain.campaign_jobs`` per run stage,
    under the press's own composition (:func:`campaign_press_composition`,
    the timers on) — each resolved by the pool and put through
    ``pool.why_not_kept``, the decision ``pool.run`` takes under ``--resume``.
    So "a resumed campaign press would re-make these" is read off the records
    without pressing anything (task A105 (v5-resume-fixes-and-tau-rule),
    issue I-38).  The dependent stage (the displaced evaluations) is composed
    from the entry references' records; where one is absent the stage says
    so and lists nothing.  ``--json`` writes the rows.
    """
    if CAMPAIGN_JOBS in registry_mod.gates_only(campaign):
        print(f"  REFUSED — a gate is registered as {CAMPAIGN_JOBS!r}, the name --jobs reserves for the campaign")
        return 3
    composed = campaign_press_composition(campaign)
    _rule(
        f"jobs of the campaign press (test set {composed.test_set}, "
        f"{_tolerance_words(composed)}, wall-clock timers "
        f"{'on' if composed.timers else 'off'})"
    )
    stages: dict[str, list[dict[str, Any]]] = {}
    for stage in chain_mod.RUN_STAGES:
        try:
            jobs = chain_mod.campaign_jobs(composed, stage)
        except chain_mod.ChainError as exc:
            print(f"  {stage}: not composable yet — {exc}")
            stages[stage] = []
            continue
        stages[stage] = pool_mod.job_listing(jobs, composed)
    n_jobs = sum(len(rows) for rows in stages.values())
    n_kept = sum(1 for rows in stages.values() for r in rows if r["why_not_complete"] is None)
    for stage, rows in stages.items():
        kept = sum(1 for r in rows if r["why_not_complete"] is None)
        print(f"  {stage:<22} {len(rows):>4} distinct job(s); --resume would keep {kept}, run {len(rows) - kept}")
    print(f"  {'all run stages':<22} {n_jobs:>4} distinct job(s); --resume would keep {n_kept}, run {n_jobs - n_kept}\n")
    for stage, rows in stages.items():
        for row in rows:
            if row["why_not_complete"] is None:
                continue
            relative = framework_mod._relative(Path(row["path"]), Path(composed.runs_dir))
            print(f"    RUN  {row['key']}")
            print(f"         {relative}: {row['why_not_complete']}")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(
                {
                    "tree_git_head": framework_mod.git_head(),
                    "run": run_layout.stamp(composed),
                    "test_set": composed.test_set,
                    "tolerance": _tolerance_words(composed),
                    "timers": bool(composed.timers),
                    "n_jobs": n_jobs,
                    "n_kept": n_kept,
                    "stages": {
                        stage: [
                            {k: r[k] for k in ("key", "job_digest", "path", "why_not_complete")}
                            for r in rows
                        ]
                        for stage, rows in stages.items()
                    },
                },
                indent=2,
            )
            + "\n"
        )
        print(f"\n  record: {args.json}")
    return 0


def _tolerance_words(campaign: Campaign) -> str:
    """The campaign's tolerance as a listing prints it."""
    if campaign.tau_rule is not None:
        return f"tau by rule {campaign.tau_rule} (" + ", ".join(
            f"{config.name} {campaign.tau_for(config)!r}" for config in campaign.configurations
        ) + ")"
    return f"tau {campaign.tau!r}" + (" (overridden)" if campaign.tau_overridden else "")


def stage_gate_catalogue(campaign: Campaign) -> int:
    """Every registered gate and measurement stage, with what it binds."""
    _rule("the gate registry")
    entries = registry_mod.registry(campaign)
    gates = registry_mod.ordered_gate_names(campaign)
    print(
        f"  {len(gates)} gate(s) and "
        f"{len(entries) - len(gates)} measurement stage(s)\n"
    )
    print("  gates, in the order --gate all runs them:")
    for name in gates:
        gate = entries[name]
        runs = "runs PROCESS" if gate.needs_runs else "no PROCESS run"
        label = f"[{gate.plan_name}]" if gate.plan_name else "[harness]"
        print(f"    {name:<24} {label:<12} {len(gate.teeth):>2} teeth   {runs}")
        print(f"      binds: {gate.binds}")
    print("\n  measurement stages (--measure), which have no verdict:")
    for name, stage in sorted(registry_mod.measurements(campaign).items()):
        print(f"    {name:<24} guarded by {stage.guarded_by}")
        print(f"      reports: {stage.reports}")
    return 0


# --------------------------------------------------------------------------
# the artifact stages
# --------------------------------------------------------------------------

#: What each artifact stage does, in one line each, for the help text and for
#: the record.  ``check`` is also the preflight's artifact half.
ARTIFACT_STAGES = {
    "check": (
        "resolve and validate every committed artifact of every configuration: "
        "rebuild each stamp and compare it with the files it must agree with"
    ),
    "derive-inputs": (
        "derive each pulsed configuration's lifted input file from its "
        "committed one and gate the bytes on the recorded digest"
    ),
    "census": (
        "take a runtime write and read census and compare it with the "
        "committed per-node census and per-block subsets"
    ),
    "per-run": (
        "derive each per-run deferral set with the class-level classifier and "
        "compare it with the committed artifact"
    ),
    "teeth": "the deliberate breaks of all four, each of which must be caught",
    "all": "every stage above, in order, stopping at the first failure",
}


def _write_stage_record(
    name: str, record: dict[str, Any], args: argparse.Namespace, campaign: Campaign
) -> None:
    record = {**record, "run": run_layout.stamp(campaign)}
    out = args.json or (
        campaign.runs_dir / "artifacts" / f"{name.replace('-', '_')}.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2, default=str))
    print(f"  record: {out}")


def stage_artifacts(args: argparse.Namespace, campaign: Campaign) -> int:
    """One artifact stage, or all of them, from the button.

    Every stage returns a code and writes its record; a failure stops the chain
    rather than escaping as an exception, so a failed gate is a *result* that
    the entry point reports (protocol §15: the failure paths are reachable from
    the same button as the successes).
    """
    wanted = (
        [k for k in ARTIFACT_STAGES if k not in ("all",)]
        if args.artifacts == "all"
        else [args.artifacts]
    )
    configurations = (
        [args.configuration] if args.configuration else None
    )
    codes: list[int] = []
    for name in wanted:
        _rule(f"artifacts — {name}")
        print(f"  {ARTIFACT_STAGES[name]}")
        if name == "check":
            code, record = artifacts_mod.check(campaign)
            for line in artifacts_mod.ledger_table(record):
                print(line)
            print()
            for line in artifacts_mod.report(record):
                print(line)
        elif name == "derive-inputs":
            code, record = input_files_mod.stage_derive(
                campaign, configurations=configurations, resume=args.resume
            )
            for line in artifacts_mod.report(record):
                print(line)
        elif name == "census":
            code, record = census_mod.stage(
                campaign,
                configurations=configurations,
                entry=args.census_entry,
                read_census=not args.no_read_census,
                resume=args.resume,
            )
            for line in artifacts_mod.report(record):
                print(line)
        elif name == "per-run":
            code, record = postsolve_mod.stage(
                campaign,
                configurations=configurations,
                census_entry=args.census_entry,
                resume=True,
            )
            for line in artifacts_mod.report(record):
                print(line)
        else:
            code, record = _artifact_teeth(campaign)
        _write_stage_record(name, record, args, campaign)
        codes.append(code)
        if code != 0 and args.artifacts == "all":
            print(
                f"\n  stage {name!r} did not pass; the chain stops here.  A "
                f"failed gate is a result, not an obstacle: nothing below is "
                f"re-run with different settings."
            )
            break
    return 0 if all(code == 0 for code in codes) else 3


def _artifact_teeth(campaign: Campaign) -> tuple[int, dict[str, Any]]:
    """Every artifact stage's deliberate breaks, in one place."""
    parts = []
    codes = []
    for label, run in (
        ("artifacts", lambda: artifacts_mod.stage_teeth(campaign)),
        ("input files", lambda: input_files_mod.stage_teeth(campaign)),
        ("census", lambda: census_mod.stage_teeth(campaign)),
        ("per-run deferral sets", lambda: postsolve_mod.stage_teeth(campaign)),
        ("census test sets", lambda: test_sets_mod.stage_teeth(campaign)),
    ):
        code, record = run()
        codes.append(code)
        parts.append(record)
        for line in artifacts_mod.report(record):
            print(line)
        print()
    n_teeth = sum(len(part["teeth"]) for part in parts)
    n_tripped = sum(
        1 for part in parts for tooth in part["teeth"] if tooth["caught"]
    )
    print(f"  {n_tripped}/{n_teeth} tooth/teeth tripped")
    return (0 if all(code == 0 for code in codes) else 3), {
        "check": "artifact stages — teeth",
        "binds": "the five artifact stages' own ability to fail",
        "verdict": "PASS" if all(code == 0 for code in codes) else "FAIL",
        "population": f"{n_teeth} deliberate breaks over 5 stages",
        "n_compared": n_teeth,
        "n_mismatched": n_teeth - n_tripped,
        "detail": [f"{n_tripped}/{n_teeth} tripped"],
        "teeth": [tooth for part in parts for tooth in part["teeth"]],
        "stages": parts,
    }


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------


def stage_census(args: argparse.Namespace, campaign: Campaign) -> int:
    """The census test sets, from the button (DR11; V5 plan §3).

    ``take`` runs the census job set under the fallback predicate, checks
    every censused run reproduces its uncensused twin, derives the sets,
    compares them with the two priors and writes the artifacts under
    ``runs/census_test_sets/``; ``write`` does the same and copies the
    artifacts into ``harness/data/``, where they are committed and the
    ``artifacts`` check validates them.
    """
    _rule(f"census test sets — {args.census}")
    configurations = [args.configuration] if args.configuration else None
    try:
        code, record = test_sets_mod.stage(
            campaign,
            resume=args.resume,
            write_data=(args.census == "write"),
            configurations=configurations,
        )
    except (test_sets_mod.TestSetError, pool_mod.PoolError) as exc:
        print(f"  REFUSED — {exc}")
        return 3
    for line in artifacts_mod.report(record):
        print(line)
    for name, block in (record.get("artifacts") or {}).items():
        print(f"  {name}: widths {block['n_by_block']}")
        for where, path in block["written"].items():
            print(f"    {where}: {path}")
    _write_stage_record("census-test-sets", record, args, campaign)
    return code


def stage_smoke_test_set(args: argparse.Namespace, campaign: Campaign) -> int:
    """The test-set smoke pairs, from the button (task A100 (v5-test-set))."""
    _rule("smoke — the test-set pairs")
    try:
        code, record = test_set_smoke_mod.stage(
            campaign,
            resume=args.resume,
            ladder_record=(Path(args.ladder_record) if args.ladder_record else None),
        )
    except (pool_mod.PoolError, framework_mod.GateError) as exc:
        print(f"  REFUSED — {exc}")
        return 3
    for line in test_set_smoke_mod.report(record):
        print(line)
    _write_stage_record("smoke-test-set", record, args, campaign)
    return code


def stage_timing(args: argparse.Namespace, campaign: Campaign) -> int:
    """The wall-clock instrument's stages, from the button (V5 plan §6; D33, D38;
    task A101 (v5-timers-and-once)): repeatability (the gate job set three
    times at W = 1, timers on), timers-off (once, timers unset: the
    instrument's own cost), validity (D38's check against the campaign's
    timing of the same seeds) and tables (the three appendix tables over the
    repeatability records, as test data).  Context, never evidence."""
    _rule(f"timing — {args.timing}")
    try:
        code, record = timing_mod.stage(campaign, args.timing, resume=args.resume)
    except (pool_mod.PoolError, framework_mod.GateError, chain_mod.ChainError) as exc:
        print(f"  REFUSED — {exc}")
        return 3
    for line in timing_mod.report(record):
        print(line)
    out = args.json or (timing_mod.timing_root(campaign, record["stage"]) / "measurements.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    record = {**record, "run": run_layout.stamp(campaign)}
    out.write_text(json.dumps(record, indent=2, default=str))
    print(f"  record: {out}")
    return code


def stage_supplementary(args: argparse.Namespace, campaign: Campaign) -> int:
    """A declared supplementary stage, from the button (V5 plan §3; A96).

    Composes the stage's optimisation jobs at the stage's own test set and
    tolerance — admitted by the pool because the stage is declared — and
    runs them, records stamped with the stage's run kind (``supplementary``)
    unless ``--run-kind smoke`` asks for a smoke record.  ``--arm``, ``--seed``
    and ``--configuration`` narrow the job set.
    """
    _rule(f"supplementary stage — {args.supplementary}")
    stage = next((s for s in campaign.supplementary if s.name == args.supplementary), None)
    if stage is None:
        print(
            f"  REFUSED — {args.supplementary!r} is not a declared supplementary "
            f"stage; the declared ones are {[s.name for s in campaign.supplementary]}"
        )
        return 3
    seeds = [args.seed] if args.seed_given else None
    try:
        jobs = chain_mod.supplementary_jobs(
            campaign,
            stage,
            run_kind=args.run_kind if args.run_kind == "smoke" else stage.run_kind,
            configurations=[args.configuration] if args.configuration else None,
            arms=[args.arm] if args.arm else None,
            seeds=seeds,
        )
    except chain_mod.ChainError as exc:
        print(f"  REFUSED — {exc}")
        return 3
    print(
        f"  {stage.name}: {stage.why}\n  {len(jobs)} job(s) at test set "
        f"{stage.test_set}, tau {stage.tau!r}, run kind "
        f"{jobs[0].run_kind if jobs else stage.run_kind}"
    )
    try:
        results = pool_mod.run_all(jobs, campaign, resume=args.resume)
    except pool_mod.PoolError as exc:
        print(f"  REFUSED — {exc}")
        return 3
    for result in results:
        print(f"    {result['key']}: {result['status']} -> {result['outdir']}")
    record = {
        "stage": stage.name,
        "test_set": stage.test_set,
        "tau": stage.tau,
        "why": stage.why,
        "n_jobs": len(jobs),
        "results": results,
        "tree_git_head": framework_mod.git_head(),
    }
    _write_stage_record(f"supplementary-{stage.name}", record, args, campaign)
    return 0 if all(r["status"] == "ok" for r in results) else 1


def _run_reference_stage(args: argparse.Namespace, campaign: Campaign) -> int:
    """The committed reproduction reference, shown or tabled, from the button.

    Reachable here rather than by retyping a module invocation (protocol §15).
    The ``show`` record goes under ``runs/reference/``, which is untracked.
    """
    if args.reference == "tables":
        return reference_mod.main(["--tables"])
    code, record = stage_reference(campaign)
    out = args.json or (campaign.runs_dir / "reference" / "show.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2, default=str))
    print(f"record: {out}")
    return code


# --------------------------------------------------------------------------
# the run IDs: one folder of records per campaign settings (task A107)
# --------------------------------------------------------------------------


def stage_runs(args: argparse.Namespace, campaign: Campaign) -> int:
    """The run IDs on disk, each with its settings, its campaign records by
    phase and status, the commits they were made at, and whether its gate
    table, tallies and tables document exist.  Nothing is compared between
    run IDs: the folders are the comparison's input, not this listing's."""
    _rule("the run IDs under runs/")
    block = run_layout.listing(campaign.runs_root or campaign.runs_dir)
    run_layout.print_listing(block)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(block, indent=2, default=str) + "\n")
        print(f"\n  record: {args.json}")
    return 0


def stage_adopt_records_layout(args: argparse.Namespace, campaign: Campaign) -> int:
    """Re-lay a ``runs/`` in the layout before run IDs under the run ID its
    campaign records were made under: a listing unless ``--apply``.  One
    rename per top-level entry on the same filesystem; no file's bytes or
    modification time change (``run_layout.adopt``)."""
    _rule("adopt the records layout: runs/<entry> -> runs/<run ID>/<entry>" + ("" if args.apply else " (dry run)"))
    root = campaign.runs_root or campaign.runs_dir
    try:
        plan = run_layout.adopt(root, fallback=campaign, apply=args.apply)
    except (OSError, run_layout.RunLayoutError) as exc:
        print(f"  REFUSED — {type(exc).__name__}: {exc}")
        return 3
    print(f"  runs/ = {plan['root']}: {plan['n_records']} run record(s) in {len(plan['legacy_entries'])} entr(ies) in the old layout")
    print("  campaign records by settings (these decide the run ID):")
    for row in plan["campaign_records_by_settings"] or [{"n": 0}]:
        if row["n"]:
            print(f"    {row['n']:>5}  test set {row['test_set']}, tau {row['tau']!r}, rule {row['tau_rule']!r}  (e.g. {row['example']})")
        else:
            print("    none")
    print("  other records by run kind and settings (carried along; they do not decide):")
    for row in plan["other_records_by_kind_and_settings"]:
        print(f"    {row['n']:>5}  {row['run_kind']:<13} test set {row['test_set']}, tau {row['tau']!r}, rule {row['tau_rule']!r}")
    if plan["refused"]:
        print(f"  REFUSED — {plan['refused']}")
        return 3
    print(f"  run ID: {plan['run_id']} ({plan['decided_by']})")
    print(f"  stays shared at the top level: {', '.join(plan['shared_caches_staying']) or '(none)'}")
    for move in plan["moves"]:
        print(f"    runs/{move['from']}  ->  runs/{move['to']}")
    if plan["applied"]:
        print(
            f"  APPLIED: {len(plan['moves'])} rename(s); run records under runs/ {plan['n_records_before']} before, "
            f"{plan['n_records_after']} after, {plan['n_records_in_folder']} in runs/{plan['run_id']}/"
        )
        m = plan["manifest_comparison"]
        print(
            f"  manifest of the moved entries before and after, by path relative to the entry: "
            f"{m['n_files_compared']} file(s) by size and modification time, {m['n_run_records_digested']} "
            f"run record(s) by SHA-256; {m['n_differing']} differing"
        )
    else:
        print("  dry run: nothing moved (--apply moves)")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(plan, indent=2, default=str) + "\n")
        print(f"  record: {args.json}")
    return 0


def stage_copy_archived_records(args: argparse.Namespace, campaign: Campaign) -> int:
    """Copy the read-only records every run ID reads (the reproduction gate's
    verdict and pool records, the neutrality gates' archives, the derived
    input files) from another run ID's folder into this one: a listing unless
    ``--apply`` (``harness/gates/archived_records.py``)."""
    source_id = args.copy_archived_records
    _rule(f"archived records: runs/{source_id}/ -> runs/{campaign.run_id}/" + ("" if args.apply else " (dry run)"))
    root = Path(campaign.runs_root or campaign.runs_dir)
    settings = run_layout.read_settings(root / source_id)
    if settings is None:
        print(f"  REFUSED — runs/{source_id}/ is not a run ID's folder; the run IDs on disk are {[f.name for f in run_layout.run_folders(root)]}")
        return 3
    source = default_campaign(
        test_set=settings["test_set"],
        tau=None if settings.get("tau_rule") else settings.get("tau"),
        tau_rule=settings.get("tau_rule"),
    )
    if source.run_id != source_id:
        print(f"  REFUSED — runs/{source_id}/'s settings name the run ID {source.run_id!r}, not its folder's name")
        return 3
    try:
        block = archived_records_mod.copy(source, campaign, apply=args.apply)
    except (archived_records_mod.ArchiveError, pool_mod.PoolError) as exc:
        print(f"  REFUSED — {exc}")
        return 3
    resolved = archived_records_mod.resolution(campaign) if block.get("applied") else None
    for line in archived_records_mod.report(block, resolved):
        print(line)
    return 0


def stage_run_isolation(args: argparse.Namespace, campaign: Campaign) -> int:
    """The run-ID layout's acceptance check around a smoke press under this
    run ID (``harness/run_isolation.py``): (a) written inside its folder, (b)
    every other run ID's folder unchanged, (c) the reproduction gate not
    pressed and its verdict read from this folder, (d) the listing."""
    _rule(f"run isolation — the smoke chain under run ID {campaign.run_id}, and nothing else touched")
    try:
        record = run_isolation_mod.check(campaign, press=lambda: stage_smoke(args, campaign))
    except framework_mod.GateError as exc:
        print(f"  REFUSED — {exc}")
        return 3
    _rule("run isolation — the check")
    for line in run_isolation_mod.report(record):
        print(line)
    return 0 if record["verdict"] == "PASS" else 1


#: The stages that only read: they never create a run ID's folder.
def _reads_only(args: argparse.Namespace) -> bool:
    pressing = (
        args.selfcheck or args.reference or args.artifacts or args.census or args.timing
        or args.smoke_test_set or args.supplementary or args.smoke or args.campaign
        or args.reading_stages or args.gate or args.measure or args.run
        or (args.copy_archived_records and args.apply) or args.run_isolation
        or args.paper_tables == "write"
    )
    return not pressing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--draft",
        action="store_true",
        help="preflight and gates only, even once execution is approved",
    )
    parser.add_argument(
        "--campaign",
        action="store_true",
        help="run the campaign: the same chain as --smoke on every configuration "
        "at the plan's seed count, records stamped 'campaign'.  Refused, with "
        "the reasons printed, until EXECUTION_APPROVED is True in the commit that "
        "records the user's dated approval in EXPERIMENT_REPORT.md",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="run the campaign's own chain once, end to end, on one seed and "
        "the cheapest configuration, with every record stamped 'smoke': both "
        "phases, every arm of the matrix active on it, then the two tally "
        "stages and the tally's contract gate.  Needs no approval and makes "
        "no campaign record",
    )
    parser.add_argument(
        "--reading-stages",
        choices=READING_STAGE_COMPOSITIONS,
        default=None,
        help="the chain's reading stages alone (the two tallies, then the "
        "tally's contract gate) over the records on disk, and stop: no run "
        "stage, no PROCESS run.  'campaign-press' composes the campaign as the "
        "campaign press does (the wall-clock timers on); 'plain' as --gate and "
        "--measure do.  Records go where --outdir says (issue I-37)",
    )
    parser.add_argument(
        "--paper-tables",
        choices=("show", "check", "write"),
        help="compute the paper's one document (Structuring-fusion-MDAO-with-"
        "DSMs, section 3, Case 2: the main-text tables and the appendix "
        "tables) from the campaign's run records and print it ('show'), "
        "compare it with paper_tables.md ('check', exits 3 on a difference or "
        "a cross-check mismatch) or write that file ('write'); every cell the "
        "stage records also hold is compared with them exactly first",
    )
    parser.add_argument(
        "--paper-tables-runs",
        type=Path,
        default=None,
        help="for --paper-tables: the runs root to read (campaign/ and gates/ "
        "under it) in place of the experiment's own runs/ — a relocated "
        "records tree, read only; nothing is written there",
    )
    parser.add_argument(
        "--paper-tables-out",
        type=Path,
        default=None,
        help="for --paper-tables write/check: the file to write or compare "
        "instead of this folder's paper_tables.md; required with "
        "--paper-tables-runs, so a rendering from test data never becomes "
        "the committed document",
    )
    parser.add_argument(
        "--selfcheck",
        action="store_true",
        help="run the harness's own gates with their teeth, and stop",
    )
    parser.add_argument(
        "--no-capability",
        action="store_true",
        help="skip the capability probe (it starts a child process per arm "
        "and configuration)",
    )
    parser.add_argument(
        "--reference",
        choices=("show", "tables"),
        help="the committed reproduction reference, and stop: show what is "
        "committed and what it does not cover, or emit the report's tables "
        "from it.  The file is not regenerated (D25)",
    )
    parser.add_argument(
        "--artifacts",
        choices=tuple(ARTIFACT_STAGES),
        help="run one artifact stage and stop: "
        + "; ".join(f"{k} = {v}" for k, v in ARTIFACT_STAGES.items()),
    )
    parser.add_argument(
        "--census-entry",
        default="optimisation",
        choices=tuple(census_mod.ENTRIES),
        help="for --artifacts census / per-run: what the census is taken over "
        "— one full optimisation (the population the committed census was "
        "measured over) or one evaluation of the model set (cheaper, one "
        "design point)",
    )
    parser.add_argument(
        "--no-read-census",
        action="store_true",
        help="for --artifacts census: take the write half only.  The read half "
        "overrides attribute access on every data-structure object and is the "
        "expensive half",
    )
    parser.add_argument(
        "--jobs",
        metavar="NAME",
        help="list one gate's job set by identity — key, digest, shared-pool "
        "directory, and whether --resume would keep the record there, with "
        "the reason where it would not — and stop.  Nothing runs.  'all' "
        "lists the union and which gates share each job; 'campaign' lists the "
        "campaign press's own job set, composed as the press composes it",
    )
    parser.add_argument(
        "--gate",
        metavar="NAME",
        help="run one gate and stop, or 'all' for every registered gate "
        "cheapest first.  '--gates' lists them.  Only gates run here; a "
        "measurement stage has no verdict and runs under --measure",
    )
    parser.add_argument(
        "--gates",
        action="store_true",
        help="list every registered gate and measurement stage, with what "
        "each binds, how many teeth it has and whether it starts PROCESS",
    )
    parser.add_argument(
        "--measure",
        metavar="NAME",
        help="run one measurement stage and stop, or 'all'.  A measurement "
        "publishes numbers and has nothing to pass; the gate that guards the "
        "same records is named beside it",
    )
    parser.add_argument(
        "--capture",
        choices=("before", "after"),
        help="for --gate switch_neutrality: make that gate's two reference "
        "runs on every configuration and record them under this label, then "
        "stop.  That gate alone has two steps, because its two sides are at "
        "two commits by construction; every other gate makes its own runs",
    )
    parser.add_argument(
        "--no-teeth",
        action="store_true",
        help="for --gate: skip the teeth.  The verdict then says so, and a "
        "gate whose teeth were not run is not an accepted gate (protocol §12)",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="run ONE run and stop: one arm, one configuration, one seed.  "
        "Needs --arm and --configuration; the run kind is gate or smoke, "
        "never campaign",
    )
    parser.add_argument("--arm", help="which arm, for --run")
    parser.add_argument("--configuration", help="which configuration, for --run")
    parser.add_argument("--seed", type=int, default=0, help="which start, for --run")
    parser.add_argument("--delta", type=float, default=None,
                        help="displacement size, for --run")
    parser.add_argument("--regime", default="unperturbed",
                        choices=records_mod.REGIMES, help="for --run")
    # No default here (A102 (v5-campaign)): the default was "smoke", so
    # --supplementary without --run-kind made smoke records although the stage
    # promises its own run kind "unless --run-kind smoke asks for a smoke
    # record".  --run resolves None to "smoke" (its default, unchanged);
    # --supplementary to the stage's declared kind.
    parser.add_argument("--run-kind", default=None,
                        choices=("gate", "smoke"),
                        help="for --run (default smoke) and --supplementary (default the "
                        "stage's own kind); a campaign record is never made here")
    parser.add_argument("--pin-hex", default=None, help="for --run")
    parser.add_argument("--timers", action="store_true",
                        help="for --run: compose the wall-clock timers (DR12)")
    parser.add_argument("--entry-state", default=None, help="for --run")
    parser.add_argument("--stencil-column", type=int, default=None, help="for --run")
    parser.add_argument("--stencil-sign", type=int, default=1, choices=(1, -1),
                        help="for --run")
    parser.add_argument("--outdir", default=None,
                        help="for --run: where the run goes.  For --gate and "
                             "--measure: where the verdicts and the gates' own "
                             "runs go, instead of the campaign's records "
                             "directory")
    parser.add_argument("--resume", action="store_true",
                        help="keep a run whose directory already holds a "
                        "complete record of the same job.  It reaches the "
                        "gates' own runs as well as --run: without it every "
                        "gate re-makes the runs it reads, so a verdict is "
                        "never computed over records made before the change "
                        "it is checking")
    parser.add_argument("--skip-runs", action="store_true",
                        help="for --gate reproduction: compare and run the "
                        "cost-free teeth against records that already exist")
    parser.add_argument(
        "--test-set",
        choices=TEST_SETS,
        default=None,
        help="the campaign-level test set every block loop stops on (driver "
        "change DR11): 'census' (the measured set, D32; the default) or "
        "'write_set' (the block's whole write set, V4's predicate, the fallback "
        "of D39).  One value for every arm and both phases; the tolerance "
        "follows it (" + ", ".join(f"{k}: {v:g}" for k, v in TAU_BY_TEST_SET.items()) + ")",
    )
    parser.add_argument(
        "--tau",
        type=float,
        default=None,
        help="override the tolerance the test set is declared at (stamped as an "
        "override in every record; in the job identity, so records at another "
        "tolerance never resolve into the campaign's)",
    )
    parser.add_argument(
        "--tau-rule",
        choices=tuple(rule.name for rule in TAU_RULES),
        default=None,
        help="a named tolerance rule instead of one tau: each configuration's "
        "tau computed from its committed input file ("
        + "; ".join(f"{rule.name}: {rule.why}" for rule in TAU_RULES)
        + ").  Refused with --tau.  The rule's name and each tau are in the "
        "job identity and stamped on every record; none by default",
    )
    parser.add_argument(
        "--census",
        choices=("take", "write"),
        help="the census test sets, and stop: take = run the census job set "
        "under the fallback predicate, check it is observation-only, derive "
        "the sets, compare them with the priors and write the artifacts under "
        "runs/; write = the same, and copy the artifacts into harness/data/",
    )
    parser.add_argument(
        "--smoke-test-set",
        action="store_true",
        help="the test-set smoke pairs, and stop: B0 and B2 on the cheapest "
        "pulsed configuration at seed 0 under the census set and under the "
        "fallback, and the supplementary stage's B2 on st_regression, each "
        "compared with the seeded reproduction records or a ladder record",
    )
    parser.add_argument(
        "--timing",
        choices=timing_mod.STAGES,
        default=None,
        help="the wall-clock instrument's stages, and stop (V5 plan §6; D33, "
        "D38): 'repeatability' runs the gate job set three times at W = 1 with "
        "PROCESS_ARCH_TIMERS=on and reports per row the median and [min, max] "
        "(a job whose repetitions differ in counts is refused); 'timers-off' "
        "runs the set once with the timers unset (the instrument's own cost); "
        "'validity' checks the campaign's timing of the same seeds against "
        "the repetitions' range; 'tables' renders the three appendix tables "
        "over the repeatability records as test data.  Records stamped "
        "'timing' under runs/timing/, never pooled.  Context, never evidence",
    )
    parser.add_argument(
        "--ladder-record",
        default=None,
        help="for --smoke-test-set: a record of the supplementary stage's B2 "
        "st_regression seed-0 run made elsewhere, to compare with",
    )
    parser.add_argument(
        "--supplementary",
        default=None,
        help="run one declared supplementary stage by name and stop (its own "
        "test set and tolerance, records stamped 'supplementary'; --arm, "
        "--seed and --configuration narrow it, --run-kind smoke makes a smoke "
        "record)",
    )
    parser.add_argument(
        "--evaluation-warmup",
        choices=("check",),
        default=None,
        help="the warmed evaluation child's neutrality check, and stop (V5 plan "
        "§6; A102 (v5-campaign)): gate 'evaluation_warmup' -- A101's cold-child "
        "records of the gate job set's evaluation half (archived on the first "
        "press) against the same jobs made by the warmed child, every count and "
        "every exit-state component identical, each warmed record's own "
        "determinism check re-derived; two teeth.  The same as --gate "
        "evaluation_warmup",
    )
    parser.add_argument(
        "--runs",
        action="store_true",
        help="list the run IDs on disk (one folder per campaign settings under "
        "runs/): each one's settings, its campaign records by phase and status, "
        "the commits they were made at, and whether its gate table, tallies and "
        "tables document exist; and stop.  No comparison between run IDs",
    )
    parser.add_argument(
        "--adopt-records-layout",
        action="store_true",
        help="re-lay a runs/ in the layout before run IDs under the run ID its "
        "campaign records were made under (runs/<entry> -> runs/<run ID>/<entry>, "
        "one rename per entry, no file changed), and stop.  A dry run with the "
        "listing unless --apply; a tree whose campaign records carry more than "
        "one setting is refused with the list",
    )
    parser.add_argument(
        "--copy-archived-records",
        metavar="FROM_RUN_ID",
        default=None,
        help="copy the read-only records every run ID reads and none re-makes "
        "(the reproduction gate's verdict and pool records, gates GC's and G1's "
        "archived straddles, the warm-up gate's cold-child records, the derived "
        "input files) from that run ID's folder into the folder of the run ID "
        "the settings name, and stop.  A dry run unless --apply",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="for --adopt-records-layout and --copy-archived-records: do it",
    )
    parser.add_argument(
        "--run-isolation",
        choices=("smoke",),
        default=None,
        help="the run-ID layout's acceptance check: press the smoke chain under "
        "the run ID the settings name and show that everything it wrote is in "
        "that run ID's folder, that no other run ID's folder changed (path, size, "
        "modification time, run-record SHA-256), that the reproduction gate was "
        "not pressed and its verdict reads from this folder, and that the "
        "listing shows every run ID; two teeth",
    )
    parser.add_argument("--json", type=Path, help="write the preflight record here")
    args = parser.parse_args(argv)
    if args.evaluation_warmup:
        args.gate = "evaluation_warmup"
    args.seed_given = any(a == "--seed" or a.startswith("--seed=") for a in (argv if argv is not None else sys.argv[1:]))

    # The experiment's own copy of PROCESS is the only tree a record is ever
    # made against; there is no flag to point the button anywhere else.  The
    # test set and the tolerance are the two campaign-level settings the
    # button takes (DR11, D39): one value each, reaching every job.
    if args.tau_rule is not None and args.tau is not None:
        print("  REFUSED — --tau-rule and --tau both given; a campaign takes its tolerance one way")
        return 3
    campaign = default_campaign(test_set=args.test_set, tau=args.tau, tau_rule=args.tau_rule)

    # The run ID (task A107 (v5-campaign-settings-keys)): every record this
    # press makes or reads is under runs/<run ID>/.  The listing and the
    # adoption look at the whole of runs/ and pass no guard; every other stage
    # refuses a runs/ in the old layout and a folder of other settings.
    if args.runs:
        return stage_runs(args, campaign)
    if args.adopt_records_layout:
        return stage_adopt_records_layout(args, campaign)
    print(f"{run_layout.header(campaign)}")
    try:
        run_layout.open_run(campaign, create=not _reads_only(args))
    except run_layout.RunLayoutError as exc:
        print(f"  REFUSED — {exc}")
        return 3
    try:
        return _dispatch(args, campaign)
    except (pool_mod.PoolError, run_layout.RunLayoutError) as exc:
        print(f"  REFUSED — {type(exc).__name__}: {exc}")
        return 3


def _dispatch(args: argparse.Namespace, campaign: Campaign) -> int:
    """Every stage but the listing and the adoption, after the run-ID guard."""
    if args.copy_archived_records:
        return stage_copy_archived_records(args, campaign)

    if args.run_isolation:
        return stage_run_isolation(args, campaign)

    if args.selfcheck:
        checks = selfcheck_mod.run_all(
            campaign, include_capability=not args.no_capability
        )
        return selfcheck_mod.report(checks)

    if args.reference:
        return _run_reference_stage(args, campaign)

    if args.artifacts:
        return stage_artifacts(args, campaign)

    if args.census:
        return stage_census(args, campaign)

    if args.timing:
        return stage_timing(args, campaign)

    if args.smoke_test_set:
        return stage_smoke_test_set(args, campaign)

    if args.supplementary:
        return stage_supplementary(args, campaign)

    if args.smoke:
        return stage_smoke(args, campaign)

    if args.campaign:
        return stage_campaign_press(args, campaign)

    if args.reading_stages:
        return stage_reading_stages(args, campaign)

    if args.paper_tables:
        return stage_paper_tables(args, campaign)

    if args.gates:
        return stage_gate_catalogue(campaign)

    if args.jobs:
        return stage_jobs(args, campaign)

    if args.gate:
        return stage_gate(args, campaign)

    if args.measure:
        return stage_measure(args, campaign)

    if args.run:
        if not (args.arm and args.configuration):
            print("--run needs --arm and --configuration")
            return 2
        return stage_single_run(args, campaign)

    print("=" * WIDTH)
    print("MDA partitioning experiment — report: EXPERIMENT_REPORT.md")
    print(f"execution approved: {EXECUTION_APPROVED}   draft mode: "
          f"{args.draft or not EXECUTION_APPROVED}")
    print("=" * WIDTH)

    record: dict[str, Any] = {"tree": str(campaign.tree)}
    rc, record["interpreter"] = stage_interpreter(campaign)
    if rc == 2:
        return 2
    codes = [rc]
    rc, record["tree_stamp"] = stage_tree(campaign)
    codes.append(rc)
    tree_present = record["tree_stamp"].get("process_package_present", False)
    rc, record["configurations"] = stage_configurations(campaign)
    codes.append(rc)
    rc, record["matrix"] = stage_matrix(campaign)
    codes.append(rc)
    rc, record["capability"] = stage_capability(
        campaign, probe=tree_present and not args.no_capability
    )
    codes.append(rc)
    rc, record["reference"] = stage_reference(campaign)
    codes.append(rc)
    rc, record["campaign"] = stage_campaign(campaign)
    codes.append(rc)

    ready = all(code == 0 for code in codes[:-1])
    print("\n" + "=" * WIDTH)
    print("preflight: " + ("READY" if ready else "NOT READY"))
    if not ready:
        print(
            "  what is missing is listed above, with the stage or task that "
            "produces it."
        )
    print("=" * WIDTH)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(record, indent=2, default=str))
        print(f"record: {args.json}")
    return 0 if ready else 3


if __name__ == "__main__":
    raise SystemExit(main())
