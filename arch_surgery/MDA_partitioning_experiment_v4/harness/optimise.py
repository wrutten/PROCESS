#!/usr/bin/env python
"""One full optimisation, in a fresh interpreter.  The optimisation phase's child.

Derived from ``arch_surgery/idf_probe/run_one.py`` at ``9a8defa6`` — a single
1 000-line ``main()`` — split so that everything shared with the evaluation
phase lives in :mod:`harness.child` and only what is particular to running an
optimisation lives here; task **A50 (harness-run)**.  Four capabilities of the
original are gone because the campaign never used them: the four in-driver probe
modes, the alternative model sequences reached through them, the call-indexed
audit, and the ``--mode`` argument that selected them.

Isolation is not a nicety.  PROCESS holds its output-file handles as *class*
attributes and its initialisation mutates a global, so two runs in one
interpreter contaminate each other: one run per process, each in its own working
directory, with ``PYTHONPATH`` naming the tree under test and that **exact**
tree asserted in-process before any work is done.

This module is never imported by the pool that starts it — it is executed.

Usage::

    PYTHONPATH=<tree> python harness/optimise.py \\
        --tree <tree> --configuration <name> --arm B3 --seed 1 \\
        --input <input file> --coupling-state <artifact> --outdir <dir>
"""

from __future__ import annotations

import argparse
import json
import os
import resource
import shutil
import sys
import time
import traceback
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_EXPERIMENT_DIR = _HERE.parent
if sys.path and Path(sys.path[0] or ".").resolve() == _HERE:
    sys.path[0] = str(_EXPERIMENT_DIR)
elif str(_EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(_EXPERIMENT_DIR))

from harness import child  # noqa: E402
from harness import failure as failure_mod  # noqa: E402
from harness import perturb  # noqa: E402
from harness import records as records_mod  # noqa: E402

#: Where the plan says this phase's audit sweep must be taken, in every arm:
#: the entry to the output path, before any output-time sweep — the state the
#: solve handed over.  It is reached by a snapshot the driver takes there, with
#: the residual computed afterwards from the restored snapshot; see
#: :data:`harness.records.AUDIT_POSITION_HOW`.
#:
#: A run may be asked for ``after_run`` instead, which is where the previous
#: revision audited.  Exactly one caller may ask — the reproduction gate, whose
#: whole purpose is to reproduce that revision's recorded residuals — and the
#: run record says so; see :data:`harness.records.AUDIT_POSITION_AFTER_RUN_WHY`.
AUDIT_POSITION_DECLARED = "entry_to_write_output_files"
AUDIT_POSITION = AUDIT_POSITION_DECLARED


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tree", required=True,
                        help="the tree whose driver must be imported, asserted "
                             "for equality in this process (never a prefix)")
    parser.add_argument("--configuration", required=True)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--input", required=True,
                        help="the input file this arm reads: the committed one "
                             "or its lifted derived copy")
    parser.add_argument("--input-kind", default="committed",
                        choices=("committed", "lifted"))
    parser.add_argument("--coupling-state", required=True,
                        help="the committed artifact the exit audit is "
                             "measured with")
    parser.add_argument("--seed", type=int, default=0,
                        help="which displaced start; 0 leaves the input file's "
                             "own point undisplaced even when a size is given")
    parser.add_argument("--delta", type=float, default=None,
                        help="displacement size on the initial design vector")
    parser.add_argument("--tau", type=float, required=True,
                        help="the one tolerance every converger uses; recorded, "
                             "not set here — the arm's environment sets it")
    parser.add_argument("--run-kind", default="campaign",
                        choices=records_mod.RUN_KINDS)
    parser.add_argument("--regime", default="unperturbed",
                        choices=records_mod.REGIMES)
    parser.add_argument("--predicate-mode", default="frozen")
    parser.add_argument("--pin-hex", default=None)
    parser.add_argument("--pending-allowed", default="",
                        help="comma-separated switch terms this tree does not "
                             "implement and this run was allowed to omit; "
                             "recorded in the record, never silent")
    parser.add_argument("--switches-asked", default="{}",
                        help="JSON of term -> value the arm asked for")
    parser.add_argument("--audit-position",
                        default=AUDIT_POSITION_DECLARED,
                        choices=records_mod.OPTIMISATION_AUDIT_POSITIONS,
                        help="where the exit audit is taken.  The default is "
                             "the position the plan declares, reached by the "
                             "driver's snapshot; 'after_run' is the previous "
                             "revision's position and is the reproduction "
                             "gate's alone")
    parser.add_argument("--reproduction-overrides", default="{}",
                        help="JSON of what the reproduction gate set "
                             "differently from the campaign, stamped into the "
                             "record; empty for every other run")
    parser.add_argument("--node-census", action="store_true",
                        help="count model executions per node name")
    parser.add_argument("--force-maxcal", type=int, default=None,
                        help="cap the optimiser's iteration budget to force a "
                             "deliberately unconverged exit.  GATE RUNS ONLY; "
                             "stamped into the record so one carrying it can "
                             "never be mistaken for a measurement")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    source = Path(args.input)
    local_input = outdir / f"{args.configuration}.IN.DAT"
    shutil.copy(source, local_input)

    # An optimisation run is never a probe run; an inherited probe switch would
    # change what is measured without saying so.
    os.environ.pop("PROCESS_IDF_PROBE", None)

    record = child.open_record(
        runner="optimise",
        phase="B",
        arm=args.arm,
        configuration=args.configuration,
        seed=args.seed,
        delta=args.delta,
        tau=args.tau,
        run_kind=args.run_kind,
        regime=args.regime,
        predicate_mode=args.predicate_mode,
        input_file=source.resolve(),
        input_file_kind=args.input_kind,
        pin_hex=args.pin_hex,
        pending_switches_allowed=[
            t for t in args.pending_allowed.split(",") if t
        ],
        switches_asked=json.loads(args.switches_asked),
    )
    record["outdir"] = str(outdir)
    record["force_maxcal"] = args.force_maxcal
    overrides = json.loads(args.reproduction_overrides)
    record["reproduction_overrides"] = overrides or None
    record["audit_position"] = args.audit_position
    record["audit_position_declared"] = AUDIT_POSITION_DECLARED
    record["audit_position_note"] = (
        records_mod.AUDIT_POSITION_HOW
        if args.audit_position == AUDIT_POSITION_DECLARED
        else records_mod.AUDIT_POSITION_AFTER_RUN_WHY
    )
    child.stamp_capabilities_absent(record, phase="B")

    # ------------------------------------------------------------------
    # The tree, before anything else.  A sibling environment on this machine
    # imports a *different* copy of PROCESS without any error at all.
    # ------------------------------------------------------------------
    process_file = child.assert_tree(Path(args.tree))
    child.stamp_tree(record, Path(args.tree), process_file)
    child.banner(record)

    from process.core import caller as caller_mod
    from process.core.solver import module_solve as module_solve_mod

    # ------------------------------------------------------------------
    # The instruments.  All harness-side, all additive, all identical in every
    # arm: they read counters and append to lists.
    # ------------------------------------------------------------------
    record["perturbation"] = None
    if perturb.is_perturbed(args.seed, args.delta):
        from process.core.solver import solver_handler as solver_handler_mod

        record["perturbation"] = child.install_design_vector_perturbation(
            solver_handler_mod,
            seed=args.seed,
            delta=args.delta,
            factor=perturb.design_vector_factor,
        )
    else:
        record["perturbation"] = {
            "applied": False,
            "why": (
                "the input file's own point: no displacement size, or seed 0 "
                "(the house convention — the campaign's first start is the "
                "input file's own point)"
            ),
        }

    node_census = (
        child.install_node_census(caller_mod) if args.node_census else None
    )
    call_census = child.install_call_models_census(caller_mod)

    # The coupling-state snapshot the audit is taken from, when the audit is
    # taken where the plan declares.  Installed before the run, because the
    # position it is taken at is inside the run.
    if args.audit_position == AUDIT_POSITION_DECLARED:
        snapshot_state = child.install_exit_snapshot(
            caller_mod,
            module_solve_mod,
            coupling_state_path=Path(args.coupling_state),
        )
    else:
        snapshot_state = {
            "installed": False,
            "why": records_mod.AUDIT_POSITION_AFTER_RUN_WHY,
        }

    try:
        from process.core.solver import solver as solver_mod

        forensics_state = child.install_exit_forensics(solver_mod)
        record["exit_forensics_hook"] = "installed"
    except Exception:  # noqa: BLE001 - recorded, never raised
        forensics_state = {"attempts": [], "data": None}
        record["exit_forensics_hook"] = traceback.format_exc()

    # ------------------------------------------------------------------
    # The run.
    # ------------------------------------------------------------------
    from process.main import SingleRun

    usage_before = resource.getrusage(resource.RUSAGE_SELF)
    started = time.perf_counter()
    single_run = None
    raised: BaseException | None = None
    try:
        single_run = SingleRun(
            str(local_input), solver="vmcon", update_obsolete=True
        )
        if args.force_maxcal is not None:
            single_run.data.globals.maxcal = int(args.force_maxcal)
        single_run.run()
        record["status"] = "ok"
    except BaseException as exc:  # noqa: BLE001 - classified, then recorded
        raised = exc
        single_run = None
        record["status"] = "crashed"
        record["traceback"] = traceback.format_exc()
    child.stamp_resources(record, usage_before, started)
    record["failure_class"] = failure_mod.classify(raised, status=record["status"])

    # ------------------------------------------------------------------
    # The counters, read BEFORE the audit takes its extra sweep.
    # ------------------------------------------------------------------
    record.update(child.harvest_counters(caller_mod, module_solve=module_solve_mod))
    record.update(child.harvest_output_path(caller_mod))
    record.update(child.harvest_predicate_counters(caller_mod))
    attempt_stamps = child.harvest_attempt_stamps(caller_mod)
    record["first_call_models"] = call_census["first_call_models"]
    record["audit_snapshot"] = (
        child.collect_exit_snapshots(caller_mod, snapshot_state, outdir)
        if snapshot_state.get("installed")
        else snapshot_state
    )

    # ------------------------------------------------------------------
    # The audit: the accuracy the arm achieved, on the same ruler in every arm,
    # at the same position in every arm.
    # ------------------------------------------------------------------
    from_snapshot = None
    if args.audit_position == AUDIT_POSITION_DECLARED:
        from_snapshot = (getattr(caller_mod, "EXIT_SNAPSHOTS", {}) or {}).get(
            AUDIT_POSITION_DECLARED
        )
    if single_run is not None and (
        args.audit_position != AUDIT_POSITION_DECLARED or from_snapshot is not None
    ):
        n = int(single_run.data.numerics.n_iteration_variables)
        record["exit_audit"] = child.take_exit_audit(
            caller_mod,
            module_solve_mod,
            models=single_run.models,
            data=single_run.data,
            x=single_run.data.numerics.xcm[:n],
            coupling_state_path=Path(args.coupling_state),
            outdir=outdir,
            position=args.audit_position,
            write_state=True,
            from_snapshot=from_snapshot,
        )
    elif single_run is not None:
        record["exit_audit"] = {
            "skipped": (
                "the run reached no snapshot at "
                f"{AUDIT_POSITION_DECLARED}: it never entered the output path, "
                "so there is no handed-over state to audit"
            ),
            "audit_position": args.audit_position,
            "positions_that_raised": dict(
                getattr(caller_mod, "EXIT_SNAPSHOT_ERRORS", {}) or {}
            ),
        }
    else:
        record["exit_audit"] = {
            "skipped": f"status {record['status']!r}: there is no exit state",
            "audit_position": args.audit_position,
        }

    # ------------------------------------------------------------------
    # What the optimiser returned.
    # ------------------------------------------------------------------
    if single_run is not None:
        numerics = single_run.data.numerics
        n = int(numerics.n_iteration_variables)
        n_equality = int(numerics.n_equality_constraints)
        n_inequality = int(numerics.n_inequality_constraints)
        m = n_equality + n_inequality
        residuals = list(numerics.rcm[:m])
        record.update(
            {
                "solver_name": single_run.solver,
                "nvar": n,
                "n_equality_constraints": n_equality,
                "n_inequality_constraints": n_inequality,
                "n_constraints": m,
                "n_solver_iterations": int(numerics.n_solver_iterations),
                "n_model_calls": int(numerics.n_model_calls),
                "epsfcn_final": float(numerics.epsfcn),
                "i_process_run_mode": int(numerics.i_process_run_mode),
                "i_figure_merit": int(numerics.i_figure_merit),
                "itvar_names": [
                    str(numerics.lablxc[int(numerics.ixc[i]) - 1]).strip()
                    for i in range(n)
                ],
            }
        )
        norm_objf = numerics.norm_objf
        record["values"] = {
            "norm_objf": None if norm_objf is None else float(norm_objf),
            "sqsumsq": float(numerics.sqsumsq),
            "xcs": [float(v) for v in numerics.xcs[:n]],
            "xcm": [float(v) for v in numerics.xcm[:n]],
            "rcm": [float(v) for v in residuals],
            "conf_l2": float(sum(r * r for r in residuals) ** 0.5),
        }
        record["exact"] = {
            "norm_objf": child.hexf(norm_objf),
            "sqsumsq": child.hexf(numerics.sqsumsq),
            "xcs": child.hexes(numerics.xcs[:n]),
            "xcm": child.hexes(numerics.xcm[:n]),
            "rcm": child.hexes(residuals),
            "conf_l2": child.hexf(sum(r * r for r in residuals) ** 0.5),
        }
        record["constraint_93"] = _burn_time_consistency(single_run)
        mfile_path = child.find_mfile(outdir, args.configuration)
        try:
            record["mfile"] = (
                child.read_mfile(mfile_path)
                if mfile_path is not None
                else {"error": "no output file"}
            )
        except Exception:  # noqa: BLE001 - recorded, never raised
            record["mfile"] = {"error": traceback.format_exc()}

    # ------------------------------------------------------------------
    # The censuses, summarised, and the forensics, assembled.
    # ------------------------------------------------------------------
    record["node_census"] = (
        child.summarise_node_census(
            node_census,
            node_calls_total=record.get("node_calls_total"),
            node_calls_solve_phase=record.get("node_calls_solve_phase"),
            audit_node_calls=(record.get("exit_audit") or {}).get(
                "audit_node_calls"
            ),
        )
        if node_census is not None
        else None
    )
    series = call_census["p_plant_electric_net_mw_at_entry"]
    record["entry_census"] = child.summarise_entry_census(series)
    (outdir / "entry_census_series.json").write_text(json.dumps(series))

    record["exit_forensics"] = child.assemble_forensics(
        forensics_state,
        fallback_data=(single_run.data if single_run is not None else None),
        runner="optimise: one full optimisation",
    )
    record["attempts"] = records_mod.attempts_from_forensics(
        record["exit_forensics"],
        costs=attempt_stamps["costs"],
    )
    record["attempts_node_calls_available"] = bool(attempt_stamps["available"])
    record["attempt_accounting"] = records_mod.attempt_accounting(
        record["attempts"],
        attempt_stamps,
        node_calls_solve_phase=record.get("node_calls_solve_phase"),
        dispatch_sweeps_solve_phase=record.get("dispatch_sweeps_solve_phase"),
        phase="B",
    )

    if record["perturbation"] is not None and "per_variable" in record["perturbation"]:
        (outdir / "perturbation.json").write_text(
            json.dumps(record["perturbation"], indent=2)
        )
        record["perturbation"] = {
            k: v
            for k, v in record["perturbation"].items()
            if k != "per_variable"
        }
        record["perturbation"]["per_variable_written_to"] = "perturbation.json"
        record["perturbation"]["keyed_on"] = (
            "the iteration variable's NUMBER, so a design vector one element "
            "longer still gives bit-identical factors to every variable it "
            "shares with the shorter one"
        )
        record["perturbation"]["delta"] = args.delta
        record["perturbation"]["seed"] = args.seed

    # ------------------------------------------------------------------
    # The record's own contract, before it is written.
    # ------------------------------------------------------------------
    record["completeness"] = _completeness(record)
    child.write_record(outdir, record)
    child.print_brief(
        record,
        drop=("mfile", "values", "exact", "traceback", "itvar_names",
              "env_architecture", "resolved_switches"),
    )
    return 0 if record["status"] == "ok" else 1


def _completeness(record: dict) -> dict:
    """Whether this record satisfies its own declared contract, and why not.

    Recorded rather than raised: a record that fails its contract is more
    useful written down than lost, and the summary refuses on it later.
    """
    try:
        records_mod.assert_usable(record, where="this run")
        return {"complete": True, "missing": []}
    except records_mod.RecordError as exc:
        return {
            "complete": False,
            "missing": records_mod.missing_fields(record),
            "refusal": str(exc),
        }


def _burn_time_consistency(single_run) -> dict | None:
    """The lifted variable's own residual, where the input file names it.

    The arm whose optimiser owns the burn time must satisfy the same
    consistency relation the model used to assign it, or it has "won" by
    returning a point that is not on that manifold at all — which is not a
    solution to the same problem.  Computed from the returned state through the
    model's own extracted relation, never read back from a table, and recorded
    as null where the input file does not name the constraint, so an input file
    that does not carry it says so rather than passing silently.
    """
    try:
        numerics = single_run.data.numerics
        n_all = int(numerics.n_equality_constraints) + int(
            numerics.n_inequality_constraints
        )
        icc = [int(v) for v in numerics.icc[:n_all]]
        if 93 not in icc:
            return None
        from process.models.pulse import burn_time_residual

        burn = float(single_run.data.times.t_plant_pulse_burn)
        residual = float(
            burn_time_residual(
                burn,
                single_run.data.pf_coil.vs_cs_pf_total_burn,
                single_run.data.physics.v_plasma_loop_burn,
                single_run.data.times.t_plant_pulse_fusion_ramp,
            )
        )
        position = icc.index(93)
        return {
            "position_in_icc": position,
            "is_in_equality_block": position
            < int(numerics.n_equality_constraints),
            "n_equality_constraints": int(numerics.n_equality_constraints),
            "t_plant_pulse_burn_s": burn,
            "residual_s": residual,
            "residual_relative_to_burn_time": (
                abs(residual) / abs(burn) if burn else None
            ),
            "normalised_residual_rcm": float(numerics.rcm[position]),
        }
    except Exception:  # noqa: BLE001 - recorded, never raised
        return {"error": traceback.format_exc()}


if __name__ == "__main__":
    raise SystemExit(main())
