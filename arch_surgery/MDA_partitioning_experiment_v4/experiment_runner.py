#!/usr/bin/env python
"""The button: run the experiment, or say exactly why it cannot be run yet.

Derived from ``arch_surgery/MDA_partitioning_experiment_v3/run_experiment.py``
at ``f2dc9243`` (task A47).  Press Run: no arguments are needed.

Only the preflight exists at this point.  It refuses to start under an
interpreter that cannot import PROCESS, names the tree it will measure and
the commit it is at, resolves every configuration and every artifact, asks
the tree itself which switches it implements, and prints the switch matrix
and the rung table with the check that they agree with the plan.  Every
campaign stage refuses while the plan is not approved, and the refusal is
reachable from this same entry point — a failure path that can only be
reached by retyping a command line is not reproducible.

Exit codes: 0 ready · 2 refused to start · 3 not ready.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from harness import arms as arms_mod  # noqa: E402
from harness import artifacts as artifacts_mod  # noqa: E402
from harness import census as census_mod  # noqa: E402
from harness import gates as gates_mod  # noqa: E402
from harness import input_files as input_files_mod  # noqa: E402
from harness import postsolve as postsolve_mod  # noqa: E402
from harness import provenance as prov  # noqa: E402
from harness import pool as pool_mod  # noqa: E402
from harness import records as records_mod  # noqa: E402
from harness import reference as reference_mod  # noqa: E402
from harness import selfcheck as selfcheck_mod  # noqa: E402
from harness.config import (  # noqa: E402
    EXECUTION_APPROVED,
    Campaign,
    default_campaign,
    repository_tree_campaign,
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
    what is committed; ``--reference verify`` re-derives it from the live
    records and requires byte-for-byte equality, and ``--reference teeth``
    shows the four ways it refuses.
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
    print(
        "  re-derive  experiment_runner.py --reference verify "
        "--previous-runs <root>"
    )
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
    """Every campaign stage, and why it refuses.

    Reachable from the button so that the refusal is as reproducible as a
    result would be.
    """
    _rule("campaign")
    reasons = []
    if not campaign.is_experiment_copy:
        reasons.append(
            f"the tree is not the experiment's copy ({campaign.tree}); records "
            f"are only ever made against "
            f"{Path(__file__).resolve().parent / 'PROCESS'}.  Pointing the "
            f"campaign elsewhere is for preflight and the self-check"
        )
    if not EXECUTION_APPROVED:
        reasons.append(
            "the plan's execution is not approved: the user flips "
            "EXECUTION_APPROVED in harness/config.py in the same commit that "
            "records the dated approval in EXPERIMENT_PLAN.md"
        )
    reasons.append(
        "the stages that summarise the records into the experiment's tables "
        "are separate tasks; the run path itself is built and is reachable "
        "from --run (one run) and --gate reproduction (the reproduction gate)"
    )
    for reason in reasons:
        print(f"  REFUSED — {reason}")
    budget = {
        "phase_a_delta_regime": sum(
            len(arms_mod.active_arms(c, "A")) * campaign.n_seeds
            for c in campaign.configurations
        ),
        "phase_a_stencil_regime": sum(
            len(arms_mod.active_arms(c, "A")) * campaign.stencil_runs(c)
            for c in campaign.configurations
        ),
        "phase_b": sum(
            len(arms_mod.active_arms(c, "B")) * campaign.n_seeds
            for c in campaign.configurations
        ),
    }
    print(
        f"  would run: {budget['phase_a_delta_regime']} displaced-entry "
        f"evaluations + {budget['phase_a_stencil_regime']} stencil-point "
        f"evaluations + {budget['phase_b']} optimisations"
    )
    return 3, {"refused": reasons, "budget": budget}


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
    outdir = Path(args.outdir) if args.outdir else (
        campaign.runs_dir
        / "single"
        / config.name
        / arm.name
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
        run_kind=args.run_kind,
        allow_pending=tuple(t for t in (args.allow_pending or "").split(",") if t),
    )
    print(
        f"  {arm.name} on {config.name}, seed {args.seed}, phase {phase}, "
        f"regime {args.regime}, kind {args.run_kind}"
    )
    try:
        result = pool_mod.run(job, campaign, resume=args.resume)
    except (pool_mod.PoolError, Exception) as exc:  # noqa: BLE001
        print(f"  REFUSED — {exc}")
        return 3
    record = records_mod.read(outdir)
    print(f"  status {result['status']!r}  taxonomy {result['failure_class']!r}")
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
        return Path(args.outdir)
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
    gates_mod.REPRODUCTION_LIFTED_FROM["path"] = args.lifted_from
    gates_mod.REPRODUCTION_RESUME["resume"] = args.resume
    gates_mod.CENSUS_ENTRY["entry"] = args.census_entry

    available = gates_mod.gates_only(campaign)
    names = (
        gates_mod.ordered_gate_names(campaign)
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
    status = 0
    for name in names:
        gate = available[name]
        _rule(f"gate {name}" + (f" ({gate.plan_name})" if gate.plan_name else ""))
        try:
            verdict = gate.run(records_dir=records_dir, teeth=not args.no_teeth)
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
        gates_mod.print_verdict(verdict)
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
    available = gates_mod.measurements(campaign)
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
            stage.run(records_dir=records_dir)
        except (gates_mod.GateError, FileNotFoundError, KeyError) as exc:
            print(f"  REFUSED — {type(exc).__name__}: {exc}")
            status = 3
    return status


def stage_gate_catalogue(campaign: Campaign) -> int:
    """Every registered gate and measurement stage, with what it binds."""
    _rule("the gate registry")
    entries = gates_mod.registry(campaign)
    gates = gates_mod.ordered_gate_names(campaign)
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
    for name, stage in sorted(gates_mod.measurements(campaign).items()):
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
        "binds": "the four artifact stages' own ability to fail",
        "verdict": "PASS" if all(code == 0 for code in codes) else "FAIL",
        "population": f"{n_teeth} deliberate breaks over 4 stages",
        "n_compared": n_teeth,
        "n_mismatched": n_teeth - n_tripped,
        "detail": [f"{n_tripped}/{n_teeth} tripped"],
        "teeth": [tooth for part in parts for tooth in part["teeth"]],
        "stages": parts,
    }


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------


def _run_reference_stage(args: argparse.Namespace, campaign: Campaign) -> int:
    """One reproduction-reference stage, from the button rather than by hand.

    Every stage of the experiment is reachable from this entry point,
    successes and refusals alike: a run that can only be started by retyping a
    module invocation with flags is not reproducible (protocol §15).  The
    stage's own record goes under ``runs/reference/``, which is untracked.
    """
    if args.reference == "tables":
        return reference_mod.main(["--tables"])
    if args.reference == "show":
        code, record = stage_reference(campaign)
        name = "show"
    elif args.reference == "extract":
        code, record = stage_extract_reference(args.previous_runs, campaign)
        name = "extract"
    elif args.reference == "verify":
        code, record = reference_mod.stage_verify(
            runs_root=args.previous_runs, campaign=campaign
        )
        name = "verify"
    else:
        code, record = reference_mod.stage_teeth(
            runs_root=args.previous_runs, campaign=campaign
        )
        name = "teeth"
    if name != "show":
        reference_mod.report(name, code, record)
    out = args.json or (campaign.runs_dir / "reference" / f"{name}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2, default=str))
    print(f"record: {out}")
    return code


def stage_extract_reference(
    previous_runs: Path | None, campaign: Campaign
) -> tuple[int, dict[str, Any]]:
    """Rebuild the committed reference from the previous revision's records."""
    return reference_mod.stage_extract(runs_root=previous_runs, campaign=campaign)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--tree",
        choices=("copy", "repository"),
        default="copy",
        help="which tree to run against: the experiment's own copy of "
        "PROCESS (the default, and the only tree a record is ever made "
        "against), or the repository's, which is for preflight and the "
        "self-check only and refuses every campaign stage",
    )
    parser.add_argument(
        "--draft",
        action="store_true",
        help="preflight and gates only, even once execution is approved",
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
        choices=("show", "tables", "extract", "verify", "teeth"),
        help="run one stage of the reproduction reference and stop: show what "
        "is committed, emit the report's tables from it, extract it from the "
        "previous revision's records, verify that it re-derives from them "
        "byte for byte, or run its four teeth.  'extract', 'verify' and "
        "'teeth' need --previous-runs",
    )
    parser.add_argument(
        "--previous-runs",
        type=Path,
        help="root of the previous revision's untracked run records, for the "
        "reference stages; they live in the main checkout, so a task worktree "
        "must be pointed at it",
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
    parser.add_argument("--run-kind", default="smoke",
                        choices=("gate", "smoke"),
                        help="for --run; a campaign record is never made here")
    parser.add_argument("--pin-hex", default=None, help="for --run")
    parser.add_argument("--entry-state", default=None, help="for --run")
    parser.add_argument("--stencil-column", type=int, default=None, help="for --run")
    parser.add_argument("--stencil-sign", type=int, default=1, choices=(1, -1),
                        help="for --run")
    parser.add_argument("--allow-pending", default="",
                        help="for --run: switch terms this tree does not "
                        "implement that this run may omit, named explicitly "
                        "and recorded.  Never available to a campaign stage")
    parser.add_argument("--outdir", default=None,
                        help="for --run: where the run goes.  For --gate and "
                             "--measure: where the verdicts and the gates' own "
                             "runs go, instead of the campaign's records "
                             "directory")
    parser.add_argument("--resume", action="store_true",
                        help="keep a run whose directory already holds a "
                        "complete record of the same job")
    parser.add_argument("--lifted-from", type=Path, default=None,
                        help="for --gate reproduction: a directory holding the "
                        "derived lifted input files, staged after their bytes "
                        "are checked against the recorded digests")
    parser.add_argument("--skip-runs", action="store_true",
                        help="for --gate reproduction: compare and run the "
                        "cost-free teeth against records that already exist")
    parser.add_argument("--json", type=Path, help="write the preflight record here")
    args = parser.parse_args(argv)

    campaign = (
        default_campaign() if args.tree == "copy" else repository_tree_campaign()
    )

    if args.selfcheck:
        checks = selfcheck_mod.run_all(
            campaign, include_capability=not args.no_capability
        )
        return selfcheck_mod.report(checks)

    if args.reference:
        return _run_reference_stage(args, campaign)

    if args.artifacts:
        return stage_artifacts(args, campaign)

    if args.gates:
        return stage_gate_catalogue(campaign)

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
    print("MDA partitioning experiment — plan: EXPERIMENT_PLAN.md")
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
