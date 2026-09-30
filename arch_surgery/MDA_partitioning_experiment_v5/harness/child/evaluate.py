#!/usr/bin/env python
"""One evaluation of the model set, with no optimiser anywhere.  Phase A's child.

Derived from ``arch_surgery/idf_probe/v2_eval_one.py`` and its one-option
extension ``arch_surgery/idf_probe/a44_eval_one.py`` (which added the stencil
entry), both read at ``9a8defa6``; task **A50 (harness-run)**.  Everything shared
with the optimisation phase now lives in :mod:`harness.child.child`.

What this measures, and what it deliberately does not
-----------------------------------------------------
The per-evaluation cost of an architecture: what one evaluation of the whole
model set costs and how converged it leaves the coupling state.  There is **no
optimiser in this process** — no VMCON object is built, no gradient is taken, no
retry ladder exists — so a failed evaluation is a recorded taxonomy row and
never a retry.

What it does, in order:

1. initialise the input file exactly as a real run does, and stop where a real
   run hands over to the optimiser: nothing more runs before a real run's first
   evaluation, and nothing more runs here;
2. optionally enter from a previous run's exact exit state — floats as hex
   literals, checked bit for bit after the write;
3. optionally displace the coupling state, keyed on component **name** so every
   arm displaces identically whatever its switches;
4. execute **exactly one** evaluation under whatever the environment selected;
5. record that evaluation's counts;
6. take the uncharged exit audit — one further full sweep, the same instrument
   every arm gets — and stop, because the audit sweep mutates the state.

The two entry regimes
---------------------
**Displacement**: the coupling state multiplied by ``1 ± δ·u`` per component.
Deliberately hostile, and where acceptance lives.

**Stencil**: the point the optimiser's own gradient stencil visits — one scaled
design variable multiplied by ``(1 ± epsfcn)``, built on a **copy** of the
design vector, which is exactly how the optimiser's evaluator builds its forward
and backward vectors.  A column outside the design vector is **refused**, never
clamped.  The backward points are entered from their forward point's exit, which
is the sequence the evaluator itself executes.

Usage::

    PYTHONPATH=<tree> python harness/child/evaluate.py \\
        --tree <tree> --configuration <name> --arm A2 --seed 1 \\
        --input <input file> --coupling-state <artifact> --outdir <dir> \\
        [--delta 0.10] [--entry-state <y_exit.json>] \\
        [--stencil-column 7 --stencil-sign +1]
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

import numpy as np

_HERE = Path(__file__).resolve().parent
_EXPERIMENT_DIR = _HERE.parent.parent
if sys.path and Path(sys.path[0] or ".").resolve() == _HERE:
    sys.path[0] = str(_EXPERIMENT_DIR)
elif str(_EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(_EXPERIMENT_DIR))

from harness.child import child  # noqa: E402
from harness.core import failure as failure_mod  # noqa: E402
from harness.child import perturb  # noqa: E402
from harness.child import predicate as predicate_mod  # noqa: E402
from harness.core import records as records_mod  # noqa: E402

#: This phase evaluates the model set once and never reaches the output path,
#: so its audit is taken at the state that evaluation terminated in — which is
#: the position the plan declares, before any output-time sweep, reached here by
#: there being no output path rather than by a hook.
AUDIT_POSITION = "after_single_evaluation"

#: The component a constant owns when the burn time is taken out of the loop.
PINNED_COMPONENT = "times.t_plant_pulse_burn"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tree", required=True)
    parser.add_argument("--configuration", required=True)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--input-kind", default="committed",
                        choices=("committed", "lifted"))
    parser.add_argument("--coupling-state", required=True,
                        help="the committed artifact whose component names key "
                             "the displacement and which the audit is measured "
                             "with; loaded and validated even for an "
                             "undisplaced run, so a wrong path fails loudly "
                             "rather than on the first displaced start")
    parser.add_argument("--per-run-artifact", default=None,
                        help="the committed per-run deferral artifact; when "
                             "given the audit ALSO reports the statistic "
                             "restricted to the components the in-loop nodes "
                             "write.  The whole-state statistic is unchanged")
    parser.add_argument("--node-write-sets", default=None,
                        help="the committed run-time write census the "
                             "restricted statistic derives membership from")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--delta", type=float, default=None)
    parser.add_argument("--tau", type=float, required=True)
    parser.add_argument("--run-kind", default="campaign",
                        choices=records_mod.RUN_KINDS)
    parser.add_argument("--regime", default="unperturbed",
                        choices=records_mod.REGIMES)
    parser.add_argument("--predicate-mode", default="frozen")
    parser.add_argument("--test-set", required=True,
                        help="which components every block loop tests (DR11): "
                             "census or write_set; stamped as campaign_test_set")
    parser.add_argument("--timers", default="off", choices=("on", "off"),
                        help="whether the wall-clock timers were composed "
                             "(DR12); stamped as campaign_timers")
    parser.add_argument("--pin-hex", default=None)
    parser.add_argument("--entry-state", default=None,
                        help="a previous run's exit snapshot, written into the "
                             "data structure at initialisation BEFORE any "
                             "displacement, so a displacement acts around the "
                             "entered state")
    parser.add_argument("--stencil-column", type=int, default=None,
                        help="enter at the optimiser's own stencil point: "
                             "scaled design variable at this 0-based position "
                             "multiplied by (1 + sign * epsfcn), on a copy of "
                             "the design vector")
    parser.add_argument("--stencil-sign", type=int, default=1, choices=(1, -1),
                        help="+1 the forward point, -1 the backward point")
    parser.add_argument("--reproduction-overrides", default="{}",
                        help="JSON of what the reproduction gate set "
                             "differently from the campaign, stamped into the "
                             "record; empty for every other run")
    parser.add_argument("--switches-asked", default="{}")
    parser.add_argument("--node-census", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:  # noqa: PLR0912, PLR0915
    epochs: dict[str, Any] = {"main_entry_at": time.time()}
    args = build_parser().parse_args(argv)

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    source = Path(args.input)
    local_input = outdir / f"{args.configuration}.IN.DAT"
    shutil.copy(source, local_input)

    # A single evaluation is never a probe run; an inherited probe switch would
    # change what is measured without saying so.
    os.environ.pop("PROCESS_IDF_PROBE", None)

    record = child.open_record(
        runner="evaluate",
        phase="A",
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
        switches_asked=json.loads(args.switches_asked),
        test_set=args.test_set,
        timers=(args.timers == "on"),
    )
    record["outdir"] = str(outdir)
    record["reproduction_overrides"] = json.loads(args.reproduction_overrides) or None
    record["coupling_state_artifact"] = str(args.coupling_state)
    record["per_run_artifact"] = args.per_run_artifact
    record["entry_state_argument"] = args.entry_state
    record["audit_position"] = AUDIT_POSITION
    record["audit_position_declared"] = AUDIT_POSITION
    record["audit_position_note"] = (
        "this phase never reaches the output path, so the audit is taken at "
        "the state the evaluation terminated in — the declared position, "
        "reached by there being no output path rather than by a hook"
    )
    child.stamp_driver_counters_null(record, phase="A")

    # DR12: the run starts here for the fixed per-run term -- the tree
    # assertion below imports PROCESS (numba, scipy, the models), and that
    # import, the numba cache load and the input parse are the run's own
    # start-up (V5 plan §6), not the harness's; what precedes this line
    # (the record's identity half) is the harness's set-up, excluded by name.
    epochs["run_started_at"] = time.time()

    process_file = child.assert_tree(Path(args.tree))
    child.stamp_tree(record, Path(args.tree), process_file)
    child.banner(record)

    from process.core import caller as caller_mod
    from process.core.solver import module_solve as module_solve_mod
    from process.core.solver.iteration_variables import (
        load_iteration_variables,
        load_scaled_bounds,
    )
    from process.main import SingleRun

    usage_before = resource.getrusage(resource.RUSAGE_SELF)
    started = time.perf_counter()

    # ------------------------------------------------------------------
    # 1. Initialise exactly as a real run does, and stop where it hands over.
    # ------------------------------------------------------------------
    single_run = SingleRun(str(local_input), solver="vmcon", update_obsolete=True)
    data = single_run.data
    load_iteration_variables(data)
    load_scaled_bounds(data)
    numerics = data.numerics
    n = int(numerics.n_iteration_variables)
    m = int(numerics.n_equality_constraints) + int(
        numerics.n_inequality_constraints
    )
    x = numerics.xcm[:n]
    record["nvar"] = n
    record["n_constraints"] = m
    record["i_figure_merit"] = int(numerics.i_figure_merit)
    record["epsfcn"] = float(numerics.epsfcn)
    record["x_fd"] = None
    if args.stencil_column is not None:
        record["x_fd"], x = _stencil_point(numerics, args, n)

    # ------------------------------------------------------------------
    # 2. The entered state, then the displacement around it.  The order is
    #    fixed: a displacement of a state that has not been entered yet would
    #    be a displacement of the input file's cold values instead.
    # ------------------------------------------------------------------
    spec, spec_provenance = module_solve_mod.load_spec(str(args.coupling_state))
    record["coupling_state_provenance"] = spec_provenance
    record["spec_keys_owned_by_x"] = _keys_owned_by_x(numerics, spec, n)

    record["entry_state"] = None
    if args.entry_state:
        snapshot = json.loads(Path(args.entry_state).read_text())
        written = predicate_mod.write_entry_state(spec, data, snapshot)
        record["entry_state"] = {
            "path": str(Path(args.entry_state).resolve()),
            "components_sha256": snapshot["components_sha256"],
            **written,
        }

    if perturb.is_perturbed(args.seed, args.delta):
        displacement = _displace(spec, data, args.delta, args.seed)
        (outdir / "perturbation.json").write_text(
            json.dumps(displacement, indent=2)
        )
        summary = {k: v for k, v in displacement.items() if k != "per_component"}
        summary["per_component_written_to"] = "perturbation.json"
        owned = record.get("spec_keys_owned_by_x")
        moved = {r["key"] for r in displacement["per_component"] if r["moved"]}
        summary["displaced_keys_rewritten_from_x"] = (
            sorted(set(owned) & moved) if owned is not None else None
        )
        record["perturbation"] = summary
    else:
        record["perturbation"] = {
            "applied": False,
            "why": (
                "the undisplaced point: no displacement size, or seed 0 (the "
                "house convention — the input file's own point, or the "
                "snapshot's when one was entered)"
            ),
        }

    # The exact state this evaluation is entered with, before any caller
    # exists: what the cross-arm pairing check compares bit for bit.
    y_entry = spec.read(spec.bind(data))
    y_entry_record = predicate_mod.snapshot_record(
        spec,
        y_entry,
        # The preamble names the ruler this run's loops will stop on.
        # An entry state is compared across arms bit for bit, and a
        # state carried between two runs on different rulers has to say
        # so on the file rather than in whoever's memory copied it.
        predicate_mode=getattr(module_solve_mod, "PREDICATE_MODE", "frozen"),
    )
    (outdir / "y_entry.json").write_text(json.dumps(y_entry_record))
    record["entry_state_recorded_to"] = "y_entry.json"

    # ------------------------------------------------------------------
    # 3. The census, then the WARMED evaluation: a discarded warm-up on this
    #    entry, the entry re-entered bit-exact, every driver counter and the
    #    timers reset, a fresh Caller, and EXACTLY ONE measured evaluation.
    # ------------------------------------------------------------------
    node_census = (
        child.install_node_census(caller_mod) if args.node_census else None
    )
    warmed = _WarmedEvaluation(
        caller_mod=caller_mod,
        module_solve_mod=module_solve_mod,
        models=single_run.models,
        data=data,
        numerics=numerics,
        spec=spec,
        x=x,
        m=m,
        entry_snapshot=y_entry_record,
        node_census=node_census,
    )
    epochs["warmup_started_at"] = time.time()
    warmed.warm_up()
    epochs["warmup_ended_at"] = time.time()
    if warmed.warmup["status"] == "ok":
        warmed.re_enter()
    epochs["measured_started_at"] = time.time()
    warmed.measure()
    the_caller = warmed.the_caller
    objf, conf = warmed.objf, warmed.conf
    raised = warmed.raised
    record["status"] = warmed.status
    if warmed.traceback is not None:
        record["traceback"] = warmed.traceback
    if warmed.refused is not None:
        record["refused"] = warmed.refused
    epochs["run_returned_at"] = time.time()
    child.stamp_resources(record, usage_before, started)
    record["failure_class"] = failure_mod.classify(raised, status=record["status"])
    # DR12: the driver's timers, read before the audit as the counters are --
    # the MEASURED evaluation's (the warm-up's are kept apart, below).
    timers_before_audit = child.harvest_timers(caller_mod)

    # ------------------------------------------------------------------
    # 4. The measured evaluation's counts, frozen before the audit runs.
    # ------------------------------------------------------------------
    record["node_calls_single_eval"] = caller_mod.NODE_CALLS[0] - warmed.nodes_before
    record["n_model_calls_sweeps"] = int(numerics.n_model_calls)
    record["n_arrangement_method_calls"] = warmed.prime_calls()
    shared = child.harvest_counters(caller_mod, module_solve=module_solve_mod)
    # The shared harvest reports the prime over the whole process and the cost
    # frozen at the output path; this phase wants the measured call's own
    # counts, which were taken above, and never reaches an output path.
    shared.pop("n_arrangement_method_calls", None)
    shared.pop("node_calls_solve_phase", None)
    record.update(shared)
    record.update(child.harvest_predicate_counters(caller_mod))
    record["module_solve_stats"] = (
        the_caller.module_solve_stats if the_caller is not None else None
    )
    record["evaluation_warmup"] = warmed.block()
    record["arch_block_schedule"] = (
        [
            [label, sorted(nodes), bool(iterated)]
            for label, nodes, iterated in caller_mod.module_schedule(
                numerics.i_figure_merit
            )[0]
        ]
        if getattr(caller_mod, "MDA_ENABLED", False)
        else None
    )
    if objf is not None:
        record["values"] = {
            "objf": float(objf),
            "conf_l2": float(np.sqrt(np.sum(np.square(conf)))),
        }
        record["exact"] = {"objf": child.hexf(objf), "conf": child.hexes(conf)}
    record["t_plant_pulse_burn"] = float(data.times.t_plant_pulse_burn)
    record["t_plant_pulse_burn_hex"] = child.hexf(data.times.t_plant_pulse_burn)
    pinned = record["resolved_switches"].get(
        "process.core.solver.subsolve.CONSTANT_OWNS_BURN_TIME"
    )
    record["burn_time_constant_intact_at_exit"] = (
        (
            float(data.times.t_plant_pulse_burn)
            == float(
                record["resolved_switches"].get(
                    "process.core.solver.subsolve.BURN_TIME_CONSTANT"
                )
            )
        )
        if pinned
        else None
    )
    record["lift_residual"] = _lift_residual(data, spec, record)

    record["node_census"] = (
        {
            "counted": dict(sorted(node_census["counted"].items())),
            "flat_tail": dict(sorted(node_census["flat_tail"].items())),
            "note": (
                "the measured evaluation only; frozen here, before the "
                "uncharged exit audit runs"
            ),
        }
        if node_census is not None
        else None
    )
    measured_census = dict((node_census or {}).get("counted") or {})

    # ------------------------------------------------------------------
    # 5. The uncharged exit audit, then stop.
    # ------------------------------------------------------------------
    epochs["audit_started_at"] = time.time()
    audit_t0 = time.perf_counter()
    if record["status"] == "ok":
        record["exit_audit"] = child.take_exit_audit(
            caller_mod,
            module_solve_mod,
            models=single_run.models,
            data=data,
            x=x,
            coupling_state_path=Path(args.coupling_state),
            outdir=outdir,
            position=AUDIT_POSITION,
            write_state=True,
            per_run_artifact=(
                Path(args.per_run_artifact) if args.per_run_artifact else None
            ),
            node_write_sets_path=(
                Path(args.node_write_sets) if args.node_write_sets else None
            ),
            configuration=args.configuration,
        )
        record["exit_state_written_to"] = (record["exit_audit"] or {}).get(
            "exit_state_written_to"
        )
        if node_census is not None:
            record["exit_audit"]["node_census_audit_extra"] = {
                name: count - measured_census.get(name, 0)
                for name, count in node_census["counted"].items()
                if count - measured_census.get(name, 0)
            }
    else:
        record["exit_audit"] = {
            "skipped": f"status {record['status']!r}: there is no exit state",
            "audit_position": AUDIT_POSITION,
        }
        record["exit_state_written_to"] = None
    audit_wall_s = time.perf_counter() - audit_t0
    epochs["audit_ended_at"] = time.time()

    # ------------------------------------------------------------------
    # 6. The forensics block, in the same shape the other phase writes it.
    # ------------------------------------------------------------------
    record["exit_forensics"] = child.assemble_forensics(
        {"attempts": [], "data": data},
        fallback_data=data,
        conf=(None if conf is None else [float(v) for v in conf]),
        runner=(
            "evaluate: one evaluation of the model set, no optimiser in this "
            "process — no retry ladder, and the solver-owned fields are "
            "structurally inapplicable"
        ),
    )
    # No optimiser runs in this process, so there is no retry ladder and no
    # attempt.  Said in the record rather than left to be inferred from an
    # empty list: a reader of two records must be able to tell "this phase has
    # no optimiser" from "this run stopped before it had one".
    record["attempts"] = []
    record["attempts_node_calls_available"] = False
    record["attempt_accounting"] = records_mod.attempt_accounting(
        [], None,
        node_calls_solve_phase=None,
        dispatch_sweeps_solve_phase=None,
        phase="A",
    )

    # DR12: the timers block -- the driver's accumulators before the audit,
    # the harness-only costs measured apart, the epochs.
    epochs["record_written_at"] = time.time()
    # The warm-up's own epochs beside the run's: the fixed per-run term is
    # timed from process start to the WARM-UP's first evaluation (the numba
    # cache load lands there), and the record says so.
    epochs["warmup_first_call_models_at"] = (warmed.warmup_timers or {}).get(
        "first_call_models_at"
    )
    child.stamp_timers(
        record,
        driver_before_audit=timers_before_audit,
        driver_after_audit=child.harvest_timers(caller_mod),
        epochs=epochs,
        excluded={
            "exit_audit_wall_s": audit_wall_s,
            # the whole-structure snapshots of the warm-up's restore (D25's
            # mechanism, applied to re-enter the entry): harness-only
            "state_snapshots_s": warmed.restore_wall_s,
            "warmup_evaluation_s": warmed.warmup_wall_s,
            "record_assembly_s": epochs["record_written_at"] - epochs["audit_ended_at"],
            "harness_before_run_s": epochs["run_started_at"] - epochs["main_entry_at"],
            "census_hooks_s": None,
        },
        warmup=warmed.warmup_timers,
    )
    record["completeness"] = _completeness(record)
    child.write_record(outdir, record)
    child.print_brief(
        record,
        drop=("exact", "traceback", "env_architecture", "resolved_switches",
              "coupling_state_provenance", "timers", "evaluation_warmup"),
    )
    return 0 if record["status"] == "ok" else 1


# --------------------------------------------------------------------------
# the warmed evaluation (V5 plan §6; ruled by the orchestrator under D37 at
# A101's merge, built by A102 (v5-campaign))
# --------------------------------------------------------------------------

#: What the warmed form is, quoted into every record.
EVALUATION_WARMUP_FORM = (
    "A91's warmed form: one discarded WARM-UP evaluation on this entry (numba's "
    "per-process cache load lands in its nodes' first calls), then the whole "
    "data structure put back to the entry snapshot field by derived field and "
    "the coupling state re-entered bit-exact (ruling D25's restore mechanism), "
    "every driver counter and the timers reset, a fresh Caller, and the one "
    "MEASURED evaluation whose counts, exit state and audit the record carries.  "
    "Both evaluations' counts and exit-state digests are stamped and the record "
    "is REFUSED when they differ: the warm-up is a per-record determinism check.  "
    "The fixed per-run term is timed from process start to the warm-up's first "
    "evaluation (timers.epochs.warmup_first_call_models_at)"
)

#: The driver's module-level counters the warm-up resets, by name: the
#: integer cells (``[0]``) and the dictionaries, put back to their import-time
#: values in place (the driver's functions look them up by global name, so
#: the objects must stay the same objects).  ``DEFER_PER_RUN_TOTALS`` and
#: ``SCHEDULE_RESOLUTION`` are handled apart: the once-per-run set-up they
#: carry (the validated node set, the memoised resolution -- DR9) is kept, as
#: an optimisation's warmed evaluations keep it, and only their per-evaluation
#: counts go back.
COUNTER_CELLS: tuple[str, ...] = (
    "NODE_CALLS",
    "DISPATCH_SWEEPS",
    "ARRANGEMENT_METHOD_CALLS",
    "PREDICATE_EVALUATIONS",
    "COMPONENTS_COMPARED",
    "UPSTREAM_PREDICATE_EVALUATIONS",
    "UPSTREAM_COMPONENTS_COMPARED",
    "OUTPUT_LOOP_SWEEPS",
    "OUTPUT_PATH_ENTRIES",
    "ATTEMPT_LADDERS",
    "NODE_CALLS_AT_OUTPUT",
    "DISPATCH_SWEEPS_AT_OUTPUT",
)
COUNTER_DICTS: tuple[str, ...] = (
    "SWEEPS_PER_EVAL_HIST",
    "PREDICATE_EVALUATIONS_BY_BLOCK",
    "COMPONENTS_COMPARED_BY_BLOCK",
    "BLOCK_VISITS",
    "EMPTY_BLOCK_VISITS",
    "EMPTY_BLOCK_SWEEPS",
    "MDA_TOTALS",
    "EXIT_SNAPSHOTS",
    "EXIT_SNAPSHOT_ERRORS",
)
COUNTER_LISTS: tuple[str, ...] = ("ATTEMPT_STAMPS",)
#: The per-evaluation keys of ``DEFER_PER_RUN_TOTALS`` and their reset values;
#: ``executed_once_at_node_calls`` exists only once the set has run and is
#: removed, so the measured execution stamps it as a cold run would.
DEFER_PER_RUN_RESET: dict = {
    "n_call_sites_suppressed": 0,
    "suppressed_by_node": {},
    "executed_once": None,
    "n_executions": 0,
}
DEFER_PER_RUN_REMOVED: tuple[str, ...] = ("executed_once_at_node_calls",)


def _leaves(document, prefix: str = "") -> dict:
    """Every leaf of a nested document, keyed by its dotted path (lists by index)."""
    out: dict = {}
    if isinstance(document, dict):
        for key in sorted(document):
            out.update(_leaves(document[key], f"{prefix}.{key}" if prefix else str(key)))
        return out
    if isinstance(document, list):
        for index, value in enumerate(document):
            out.update(_leaves(value, f"{prefix}[{index}]"))
        return out
    out[prefix] = document
    return out


def _sha256_of_json(document) -> str:
    import hashlib  # noqa: PLC0415

    return hashlib.sha256(
        json.dumps(document, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


class _WarmedEvaluation:
    """The warm-up, the re-entry and the measured evaluation, in that order.

    One object so that what the two evaluations share (the models, the data,
    the design vector, the spec, the census dictionaries) is handed over once
    and what they must not share (the Caller, the counters, the timers) is
    made fresh between them, visibly, in :meth:`re_enter`.
    """

    def __init__(
        self,
        *,
        caller_mod,
        module_solve_mod,
        models,
        data,
        numerics,
        spec,
        x,
        m: int,
        entry_snapshot: dict,
        node_census: dict | None,
    ) -> None:
        from harness.child import data_structure as structure_mod  # noqa: PLC0415

        self.caller_mod = caller_mod
        self.module_solve_mod = module_solve_mod
        self.structure_mod = structure_mod
        self.models = models
        self.data = data
        self.numerics = numerics
        self.spec = spec
        self.x = x
        self.m = m
        self.entry_snapshot = entry_snapshot
        self.node_census = node_census
        # The import-time values of the counters, deep-copied before anything
        # runs; the reset puts them back in place.
        self.pristine: dict = {}
        for name in COUNTER_CELLS:
            cell = getattr(caller_mod, name, None)
            if isinstance(cell, list):
                self.pristine[name] = list(cell)
        for name in COUNTER_DICTS + COUNTER_LISTS:
            value = getattr(caller_mod, name, None)
            if isinstance(value, (dict, list)):
                self.pristine[name] = json.loads(json.dumps(value, default=list))
        # The entry: the whole data structure as it stands, before any Caller.
        t0 = time.perf_counter()
        self.structure_at_entry = structure_mod.snapshot(data)
        self.restore_wall_s = time.perf_counter() - t0
        self.the_caller = None
        self.objf = self.conf = None
        self.raised: BaseException | None = None
        self.traceback: str | None = None
        self.status = "crashed"
        self.refused: str | None = None
        self.warmup: dict = {"status": None}
        self.measured: dict | None = None
        self.restore: dict | None = None
        self.warmup_timers: dict | None = None
        self.warmup_wall_s: float | None = None
        self.nodes_before = caller_mod.NODE_CALLS[0]
        self._prime_before = self._prime_cell_value()
        self.agrees: bool | None = None
        self.n_compared = 0
        self.differing: list = []

    # --- one evaluation ------------------------------------------------

    def _prime_cell_value(self):
        cell = getattr(self.caller_mod, "ARRANGEMENT_METHOD_CALLS", None)
        return cell[0] if cell is not None else None

    def prime_calls(self):
        now = self._prime_cell_value()
        return None if now is None else now - self._prime_before

    def _run_one(self) -> tuple[dict, BaseException | None, str | None]:
        """Construct a fresh Caller and evaluate once; the counts, or the crash."""
        nodes_before = self.caller_mod.NODE_CALLS[0]
        prime_before = self._prime_cell_value()
        caller = objf = conf = None
        raised = tb = None
        t0 = time.perf_counter()
        try:
            # Caller construction inside the try: the driver's refusals fire
            # there, and a refusal is a recorded taxonomy row, not a crash.
            caller = self.caller_mod.Caller(self.models, self.data)
            objf, conf = caller.call_models(self.x, self.m)
        except BaseException as exc:  # noqa: BLE001 - classified, then recorded
            raised = exc
            tb = traceback.format_exc()
        wall = time.perf_counter() - t0
        counts = self._counts(caller, objf, conf, nodes_before, prime_before)
        return (
            {
                "status": "ok" if raised is None else "crashed",
                "wall_s": wall,
                "node_calls": self.caller_mod.NODE_CALLS[0] - nodes_before,
                "sweeps": int(self.numerics.n_model_calls),
                "objf_hex": child.hexf(objf) if objf is not None else None,
                "exit_state_sha256": self._exit_digest() if raised is None else None,
                "counts": counts,
                "counts_sha256": _sha256_of_json(counts),
                "n_count_leaves": len(counts),
                "caller": caller,
                "objf": objf,
                "conf": conf,
            },
            raised,
            tb,
        )

    def _counts(self, caller, objf, conf, nodes_before, prime_before) -> dict:
        """Every count of one evaluation, flattened: what the two must agree on."""
        prime_now = self._prime_cell_value()
        document = {
            "node_calls_single_eval": self.caller_mod.NODE_CALLS[0] - nodes_before,
            "n_model_calls_sweeps": int(self.numerics.n_model_calls),
            "n_arrangement_method_calls": (
                None if prime_now is None else prime_now - prime_before
            ),
            **child.harvest_counters(self.caller_mod, module_solve=self.module_solve_mod),
            **child.harvest_predicate_counters(self.caller_mod),
            "module_solve_stats": (
                caller.module_solve_stats if caller is not None else None
            ),
            "node_census": (
                {
                    "counted": dict(sorted(self.node_census["counted"].items())),
                    "flat_tail": dict(sorted(self.node_census["flat_tail"].items())),
                }
                if self.node_census is not None
                else None
            ),
            "exact": (
                {"objf": child.hexf(objf), "conf": child.hexes(conf)}
                if objf is not None
                else None
            ),
            "t_plant_pulse_burn_hex": child.hexf(self.data.times.t_plant_pulse_burn),
        }
        # The prime's whole-process count and the output-path stamps are not
        # this evaluation's (the record drops them too); the once-per-run
        # resolution stamp is kept -- it must read the same on both sides.
        document.pop("node_calls_solve_phase", None)
        return _leaves(json.loads(json.dumps(document, default=str)))

    def _exit_digest(self) -> str:
        state = predicate_mod.snapshot_record(
            self.spec, self.spec.read(self.spec.bind(self.data))
        )["state"]
        return _sha256_of_json(state)

    # --- the three steps -----------------------------------------------

    def warm_up(self) -> None:
        outcome, raised, tb = self._run_one()
        self.warmup_wall_s = outcome["wall_s"]
        self.warmup_timers = child.harvest_timers(self.caller_mod)
        self.warmup = {k: v for k, v in outcome.items() if k not in ("caller", "objf", "conf")}
        if raised is not None:
            # The warm-up crashed: a cold evaluation of this entry crashes the
            # same way, so this IS the run's outcome, recorded as such; the
            # measured evaluation is not attempted.
            self.the_caller = outcome["caller"]
            self.raised, self.traceback = raised, tb
            self.status = "crashed"

    def re_enter(self) -> None:
        """Put the entry back (D25's mechanism) and reset every counter."""
        structure_mod = self.structure_mod
        t0 = time.perf_counter()
        after = structure_mod.snapshot(self.data)
        moved = structure_mod.differences(self.structure_at_entry, after)
        put_back = structure_mod.restore(
            self.data, self.structure_at_entry, only=moved["differ"]
        )
        entry = predicate_mod.write_entry_state(self.spec, self.data, self.entry_snapshot)
        still = structure_mod.differences(
            self.structure_at_entry, structure_mod.snapshot(self.data)
        )
        self.restore_wall_s += time.perf_counter() - t0
        self.restore = {
            "n_fields_in_the_entry_snapshot": self.structure_at_entry["n_fields"],
            "n_fields_moved_by_the_warmup": moved["n_differ"],
            "moved_by_the_warmup": moved["differ"][:60],
            "n_asked": put_back["n_asked"],
            "n_restored": put_back["n_restored"],
            "n_not_restorable": put_back["n_not_restorable"],
            "not_restorable": put_back["not_restorable"],
            "entry_state": entry,
            "n_still_differing_from_the_entry": still["n_differ"],
            "still_differing": still["differ"][:40],
            "only_before": still["only_before"][:20],
            "only_after": still["only_after"][:20],
            "restored_bitexact": (
                put_back["readback_bitexact"]
                and entry["readback_bitexact"]
                and still["n_differ"] == 0
                and not still["only_before"]
                and not still["only_after"]
            ),
        }
        if not self.restore["restored_bitexact"]:
            self.refused = (
                f"the entry did not restore bit for bit after the warm-up "
                f"({still['n_differ']} of {still['n_compared']} data-structure "
                f"fields still differ, first {still['differ'][:5]}; "
                f"{put_back['n_not_restorable']} not restorable; the coupling "
                f"state read back bit-exact: {entry['readback_bitexact']}).  A "
                f"measured evaluation from a state nobody chose is refused."
            )
            self.status = "refused"
            return
        self._reset_counters()
        self.nodes_before = self.caller_mod.NODE_CALLS[0]
        self._prime_before = self._prime_cell_value()

    def _reset_counters(self) -> None:
        caller_mod = self.caller_mod
        for name, values in self.pristine.items():
            live = getattr(caller_mod, name)
            if isinstance(live, list):
                live[:] = json.loads(json.dumps(values))
            else:
                live.clear()
                live.update(json.loads(json.dumps(values)))
        totals = getattr(caller_mod, "DEFER_PER_RUN_TOTALS", None)
        if isinstance(totals, dict):
            for key, value in DEFER_PER_RUN_RESET.items():
                totals[key] = json.loads(json.dumps(value))
            for key in DEFER_PER_RUN_REMOVED:
                totals.pop(key, None)
        # MDA_TOTALS keeps a set; the JSON round trip made it a list.
        mda = getattr(caller_mod, "MDA_TOTALS", None)
        if isinstance(mda, dict) and isinstance(mda.get("moved_constants"), list):
            mda["moved_constants"] = set(mda["moved_constants"])
        timers = getattr(caller_mod, "TIMERS", None)
        if isinstance(timers, dict):
            timers.clear()
            timers.update(caller_mod._new_timers())
        if self.node_census is not None:
            self.node_census["counted"].clear()
            self.node_census["flat_tail"].clear()

    def measure(self) -> None:
        if self.status == "refused" or self.warmup.get("status") != "ok":
            return
        outcome, raised, tb = self._run_one()
        self.the_caller = outcome["caller"]
        self.objf, self.conf = outcome["objf"], outcome["conf"]
        self.raised, self.traceback = raised, tb
        self.measured = {k: v for k, v in outcome.items() if k not in ("caller", "objf", "conf")}
        if raised is not None:
            self.status = "crashed"
            self.agrees = False
            return
        a, b = self.warmup["counts"], self.measured["counts"]
        every = sorted(set(a) | set(b))
        self.n_compared = len(every)
        self.differing = [
            {"leaf": k, "warmup": a.get(k, "<absent>"), "measured": b.get(k, "<absent>")}
            for k in every
            if k not in a or k not in b or a[k] != b[k]
        ]
        same_state = self.warmup["exit_state_sha256"] == self.measured["exit_state_sha256"]
        self.agrees = not self.differing and same_state
        if self.agrees:
            self.status = "ok"
            return
        self.status = "refused"
        self.refused = (
            f"the warm-up and the measured evaluation differ: "
            f"{len(self.differing)} of {self.n_compared} count leaves "
            f"(first {[d['leaf'] for d in self.differing[:5]]}), exit states "
            f"{'identical' if same_state else 'DIFFERENT'}.  The warm-up is a "
            f"per-record determinism check and the record is refused."
        )

    def block(self) -> dict:
        strip = ("counts",)
        return {
            "form": EVALUATION_WARMUP_FORM,
            "warmup": {
                **{k: v for k, v in self.warmup.items() if k not in strip},
                "counts": self.warmup.get("counts"),
                "timers_driver": self.warmup_timers,
            },
            "measured": (
                None
                if self.measured is None
                else {
                    **{k: v for k, v in self.measured.items() if k not in strip},
                    "counts": self.measured.get("counts"),
                }
            ),
            "restore": self.restore,
            "counters_reset": sorted(self.pristine)
            + ["DEFER_PER_RUN_TOTALS (per-evaluation keys)", "TIMERS", "node census"],
            "counters_kept": ["SCHEDULE_RESOLUTION", "DEFER_PER_RUN_TOTALS (the validated set)", "the memoised schedule and artifact caches (DR9)"],
            "agrees": self.agrees,
            "n_compared": self.n_compared,
            "n_differing": len(self.differing),
            "differing": self.differing[:40],
            "refused": self.refused,
            "restore_wall_s": self.restore_wall_s,
            "warmup_wall_s": self.warmup_wall_s,
        }


# --------------------------------------------------------------------------
# the two entry regimes
# --------------------------------------------------------------------------


def _stencil_point(numerics, args, n: int):
    """The optimiser's own stencil point, built the way the optimiser builds it.

    Returns ``(block, vector)``: what the record says about the point, and the
    design vector to evaluate at.  The vector is a **copy** of the scaled design
    vector with one column multiplied by ``(1 + sign * epsfcn)`` — the same
    multiplicative step, on a copy, one column at a time, which is exactly how
    the optimiser's evaluator builds its forward and backward vectors.  A column
    outside the vector is **refused rather than clamped**: a clamped column
    would silently evaluate a different point.
    """
    column = int(args.stencil_column)
    if not 0 <= column < n:
        raise SystemExit(
            f"--stencil-column {column} is outside the design vector "
            f"(nvar = {n}); refused, never clamped"
        )
    step = float(numerics.epsfcn)
    sign = int(args.stencil_sign)
    vector = numerics.xcm[:n].copy()
    base_hex = float(vector[column]).hex()
    vector[column] = vector[column] * (1.0 + sign * step)
    try:
        from process.core.solver.iteration_variables import ITERATION_VARIABLES

        variable = ITERATION_VARIABLES[int(numerics.ixc[column])]
        name = f"{variable.module}.{variable.target_name or variable.name}"
    except Exception:  # noqa: BLE001 - a name is context, never a result
        name = None
    return (
        {
            "column": column,
            "sign": sign,
            "epsfcn": step,
            "ixc": int(numerics.ixc[column]),
            "name": name,
            "xcm_base_hex": base_hex,
            "xcm_hex": float(vector[column]).hex(),
            "what": (
                "one evaluation at the gradient stencil point xcm[column] * "
                "(1 + sign * epsfcn), every other design variable at the input "
                "file's own point, the coupling state as entered"
            ),
        },
        vector,
    )


def _displace(spec, data, delta: float, seed: int) -> dict:
    """Multiply every continuous component by its seeded factor, in place.

    Components whose category is not continuous are never touched — a displaced
    discrete switch is a different problem, not a displaced start — and a
    component that is identically zero is unmoved by a multiplicative factor and
    is counted as ineffective rather than pretended displaced.
    """
    bound = spec.bind(data)
    rows = []
    n_moved = 0
    n_zero = 0
    skipped: dict[str, int] = {}
    for i, (namespace, field) in enumerate(bound):
        category = spec.category[i]
        key = spec.name(i)
        if category != "continuous":
            skipped[category] = skipped.get(category, 0) + 1
            continue
        f = perturb.coupling_state_factor(seed, key, delta)
        value = object.__getattribute__(namespace, field)
        if isinstance(value, (float, np.floating)):
            before = float(value)
            after = before * f
            setattr(namespace, field, after)
            moved = after != before
        elif isinstance(value, np.ndarray) and value.dtype.kind == "f":
            before_array = value.copy()
            value *= f  # in place: dtype, shape and object identity preserved
            moved = bool(np.any(value != before_array))
            j = int(np.argmax(np.abs(value - before_array))) if value.size else 0
            before = float(before_array.ravel()[j]) if value.size else 0.0
            after = float(value.ravel()[j]) if value.size else 0.0
        elif isinstance(value, list):
            try:
                array = np.asarray(value)
            except Exception:  # noqa: BLE001
                skipped["continuous_unviewable"] = (
                    skipped.get("continuous_unviewable", 0) + 1
                )
                continue
            if array.dtype.kind != "f":
                skipped["continuous_unviewable"] = (
                    skipped.get("continuous_unviewable", 0) + 1
                )
                continue
            new = [float(v) * f for v in value]
            setattr(namespace, field, new)
            moved = new != value
            before = float(value[0]) if value else 0.0
            after = float(new[0]) if new else 0.0
        else:
            skipped["continuous_unviewable"] = (
                skipped.get("continuous_unviewable", 0) + 1
            )
            continue
        n_moved += moved
        if not moved:
            n_zero += 1
        rows.append(
            {
                "key": key,
                "factor": f,
                "factor_hex": float(f).hex(),
                "moved": bool(moved),
                "elem_before_hex": float(before).hex(),
                "elem_after_hex": float(after).hex(),
            }
        )
    return {
        "delta": delta,
        "seed": seed,
        "keyed_on": "the component NAME, so every arm displaces identically",
        "n_components_in_spec": len(spec.keys),
        "n_continuous_eligible": len(rows),
        "n_moved": n_moved,
        "n_unmoved_multiplicative_zero": n_zero,
        "n_skipped_by_category": skipped,
        "per_component": rows,
    }


# --------------------------------------------------------------------------
# small readings taken before the audit mutates the state
# --------------------------------------------------------------------------


def _keys_owned_by_x(numerics, spec, n: int) -> list[str] | None:
    """Coupling components the design vector rewrites at every sweep head.

    Recorded unconditionally: a check that hand-displaces a snapshot has to
    know which components the injection would silently reset.
    """
    try:
        from process.core.solver.iteration_variables import ITERATION_VARIABLES

        owned = set()
        for i in range(n):
            variable = ITERATION_VARIABLES[int(numerics.ixc[i])]
            owned.add(f"{variable.module}.{variable.target_name or variable.name}")
        names = {spec.name(i) for i in range(len(spec.keys))}
        return sorted(owned & names)
    except Exception:  # noqa: BLE001 - recorded as unknown, never raised
        return None


def _lift_residual(data, spec, record) -> dict | None:
    """The lifted component's inconsistency at exit, by the model's own relation.

    Measured with the same function the consistency constraint evaluates — a
    pure function: nothing runs and nothing mutates — and read **before** the
    audit sweep moves the state.  Reported separately and excluded from the
    similarity statistic: in a pinned arm it is the price of the pin, not an
    error.
    """
    if record.get("status") != "ok":
        return None
    try:
        if int(data.pulse.i_pulsed_plant) != 1:
            return {
                "inactive": (
                    "the plant is not pulsed: the model writes no burn time, "
                    "so nothing is taken out of the loop here"
                )
            }
        from process.models.pulse import burn_time_residual

        raw = burn_time_residual(
            float(data.times.t_plant_pulse_burn),
            float(data.pf_coil.vs_cs_pf_total_burn),
            float(data.physics.v_plasma_loop_burn),
            float(data.times.t_plant_pulse_fusion_ramp),
        )
        index = predicate_mod.component_index(spec, PINNED_COMPONENT)
        scale = None if index is None else float(spec.scale[index])
        return {
            "component": PINNED_COMPONENT,
            "raw_s": raw,
            "raw_hex": child.hexf(raw),
            "scale": scale,
            "scaled_abs": (abs(raw) / scale) if scale else None,
            "pinned": bool(record.get("campaign_pin_hex")),
            "note": (
                "the burn-time consistency residual at the exit state, "
                "excluded from the similarity statistic"
            ),
        }
    except Exception:  # noqa: BLE001 - recorded, never raised
        return {"error": traceback.format_exc()}


def _completeness(record: dict) -> dict:
    try:
        records_mod.assert_usable(record, where="this run")
        return {"complete": True, "missing": []}
    except records_mod.RecordError as exc:
        return {
            "complete": False,
            "missing": records_mod.missing_fields(record),
            "refusal": str(exc),
        }


if __name__ == "__main__":
    raise SystemExit(main())
