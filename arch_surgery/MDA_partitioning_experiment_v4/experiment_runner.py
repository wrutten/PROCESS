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
from harness import provenance as prov  # noqa: E402
from harness import pool as pool_mod  # noqa: E402
from harness import records as records_mod  # noqa: E402
from harness import reference as reference_mod  # noqa: E402
from harness import reproduction as reproduction_mod  # noqa: E402
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
    """Resolve every configuration and its committed artifacts.

    A missing artifact is reported, not fatal: some are produced by stages
    that do not exist yet.  What *is* fatal is a configuration whose arms
    cannot be composed, because that is a defect in the experiment's
    description of itself rather than a file that has not been made.
    """
    _rule("configurations and artifacts")
    missing: list[str] = []
    records = []
    for config in campaign.configurations:
        entries = {
            "input": config.input_path,
            "coupling_state": config.coupling_state_path,
            "write_sets": config.write_sets_path,
            "defer_per_run": config.defer_per_run_path,
            "defer_per_run_lifted": config.defer_per_run_lifted_path,
            "node_write_sets": campaign.data_dir / "node_writesets.json",
            "node_map": campaign.data_dir / "dsm_node_map.json",
        }
        found = {k: v.exists() for k, v in entries.items()}
        absent = sorted(k for k, ok in found.items() if not ok)
        missing.extend(f"{config.name}/{k}" for k in absent)
        components = None
        if found["coupling_state"]:
            try:
                components = json.loads(config.coupling_state_path.read_text()).get(
                    "n_components"
                )
            except Exception as exc:  # noqa: BLE001 - reported, not raised
                components = f"unreadable: {exc}"
        agrees = (not found["coupling_state"]) or (
            components == config.n_coupling_components
        )
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
            + ("" if agrees else f"  [artifact says {components}]")
        )
        for arm, why in config.skips.items():
            print(f"    skipped: {arm} — {why}")
        if absent:
            print(f"    MISSING: {', '.join(absent)}")
        records.append(
            {
                "configuration": config.name,
                "pulsed": config.pulsed,
                "missing": absent,
                "artifact_n_components": components,
                "declared_n_components": config.n_coupling_components,
                "components_agree": agrees,
                "skips": dict(config.skips),
            }
        )
    for removal in campaign.removed_configurations:
        print(
            f"  removed: {removal.configuration} — {removal.decision}, "
            f"{removal.date}: {removal.reason}"
        )
    print(
        f"\n  {len(campaign.configurations)} configuration(s) in the "
        f"population; {len(missing)} artifact(s) missing"
    )
    return (0 if not missing else 3), {"configurations": records, "missing": missing}


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


def stage_reproduction_gate(args: argparse.Namespace, campaign: Campaign) -> int:
    """Gate GR: twenty runs against the previous revision's committed numbers."""
    _rule("gate GR — reproduction")
    code, verdict = reproduction_mod.stage(
        campaign=campaign,
        resume=args.resume,
        lifted_from=args.lifted_from,
        skip_runs=args.skip_runs,
    )
    for line in reproduction_mod.summary(verdict):
        print(line)
    print(f"\n  verdict: {verdict.get('verdict', 'REFUSED')}")
    out = args.json or (campaign.runs_dir / reproduction_mod.RUNS_SUBPATH / "gate.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(verdict, indent=2, default=str))
    print(f"  record: {out}")
    return code


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
        "--gate",
        choices=("reproduction",),
        help="run one gate and stop.  'reproduction' is gate GR: the twenty "
        "reference runs against the previous revision's committed numbers, "
        "the seven teeth, and the two substitutes for the arms the reference "
        "cannot cover",
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
    parser.add_argument("--outdir", default=None, help="for --run")
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

    if args.gate:
        return stage_reproduction_gate(args, campaign)

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
