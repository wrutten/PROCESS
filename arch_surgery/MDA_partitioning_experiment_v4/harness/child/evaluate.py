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
        --tree <tree> --configuration <name> --arm A1 --seed 1 \\
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
    parser.add_argument("--pending-allowed", default="")
    parser.add_argument("--reproduction-overrides", default="{}",
                        help="JSON of what the reproduction gate set "
                             "differently from the campaign, stamped into the "
                             "record; empty for every other run")
    parser.add_argument("--switches-asked", default="{}")
    parser.add_argument("--node-census", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:  # noqa: PLR0912, PLR0915
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
        pending_switches_allowed=[
            t for t in args.pending_allowed.split(",") if t
        ],
        switches_asked=json.loads(args.switches_asked),
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
    child.stamp_capabilities_absent(record, phase="A")

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
    # Gate G8's detector, and a no-op with its variable unset: it watches every
    # predicate evaluation on both rulers so the gate does not have to infer
    # "no decisive pass" from "the two runs agree", which is the thing the gate
    # is checking.  It returns the run's own residual unchanged; the driver
    # loads the same cached spec object this call returned, which is why
    # installing it here reaches every evaluation the run makes.
    ruler_observer = child.install_ruler_observer(
        module_solve_mod, spec, outdir, run_kind=args.run_kind
    )
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
    (outdir / "y_entry.json").write_text(
        json.dumps(
            predicate_mod.snapshot_record(
                spec,
                y_entry,
                # The preamble names the ruler this run's loops will stop on.
                # An entry state is compared across arms bit for bit, and a
                # state carried between two runs on different rulers has to say
                # so on the file rather than in whoever's memory copied it.
                predicate_mode=getattr(
                    module_solve_mod, "PREDICATE_MODE", "frozen"
                ),
            )
        )
    )
    record["entry_state_recorded_to"] = "y_entry.json"

    # ------------------------------------------------------------------
    # 3. The census, then EXACTLY ONE evaluation.
    # ------------------------------------------------------------------
    node_census = (
        child.install_node_census(caller_mod) if args.node_census else None
    )
    nodes_before = caller_mod.NODE_CALLS[0]
    prime_cell = getattr(caller_mod, "ARRANGEMENT_METHOD_CALLS", None)
    prime_before = prime_cell[0] if prime_cell is not None else None

    objf = conf = None
    the_caller = None
    raised: BaseException | None = None
    try:
        # Caller construction is inside the try: the driver's refusals — a
        # constant owning a variable the model still solves for, an input file
        # naming that variable twice — fire there, and a refusal is a recorded
        # taxonomy row, not an unhandled crash.
        the_caller = caller_mod.Caller(single_run.models, data)
        objf, conf = the_caller.call_models(x, m)
        record["status"] = "ok"
    except BaseException as exc:  # noqa: BLE001 - classified, then recorded
        raised = exc
        record["status"] = "crashed"
        record["traceback"] = traceback.format_exc()
    child.stamp_resources(record, usage_before, started)
    record["failure_class"] = failure_mod.classify(raised, status=record["status"])

    # ------------------------------------------------------------------
    # 4. That evaluation's counts, frozen before the audit runs.
    # ------------------------------------------------------------------
    record["node_calls_single_eval"] = caller_mod.NODE_CALLS[0] - nodes_before
    record["n_model_calls_sweeps"] = int(numerics.n_model_calls)
    record["n_arrangement_method_calls"] = (
        prime_cell[0] - prime_before if prime_cell is not None else None
    )
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

    record["completeness"] = _completeness(record)
    # The observation goes to its own file, never into the record: the record
    # is what the switch-neutrality gate compares value for value, and a
    # gate-only instrument's output has no place in it.
    child.write_ruler_observation(ruler_observer, outdir)
    child.write_record(outdir, record)
    child.print_brief(
        record,
        drop=("exact", "traceback", "env_architecture", "resolved_switches",
              "coupling_state_provenance"),
    )
    return 0 if record["status"] == "ok" else 1


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
