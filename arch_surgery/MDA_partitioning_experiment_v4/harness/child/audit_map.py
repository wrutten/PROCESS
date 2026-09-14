"""What the exit audit's sweep evaluates, and whether it is the loop's own map.

The exit audit is *one further full sweep of the model set*, taken from the
state the solve handed over, and its residual is read as "how far from
converged the accepted point still is".  That reading has a premise: the sweep
the audit takes must be the **same map** the loop iterated.  If anything the
models read has changed between the loop's last sweep and the audit's sweep —
anything that is not part of the coupling state, and so is neither snapshotted
nor restored — then the audit measures ``|F'(y*) - y*|`` for some other map
``F'``, and a component may sit above the tolerance with nothing about
convergence to say.

This module measures that premise rather than assuming it.  It is a **gate
instrument**: installed by an environment variable, refused on a campaign run,
and writing to its own file so that nothing it produces can reach a record a
gate compares value for value.

What it does
------------
While the run happens, it keeps

* the **coupling state after the last sweep of the model set** before the
  output path is entered — the loop's own exit state;
* the **coupling state at the last evaluation of the model set** — one step
  later, after the objective and constraint layer has run;
* a **whole-data-structure snapshot** at each position the driver offers
  (the entry to the output path, and immediately before the files are
  written), and at the moment the diagnosis sweeps begin.

Afterwards it takes a declared series of sweeps, each from a fully specified
state: a chosen data-structure base, a chosen coupling-state snapshot written
over it, and a chosen set of fields put back to the value they held at the
entry to the output path.  Every sweep reports the same residual summary the
exit audit reports, so a number here is comparable with a number there.

Nothing here is hand-picked.  The set of fields the output path changed is
**derived** by comparing two whole-data-structure snapshots, and the set is
published with its denominator.

Heritage: task **A61 (insstrain-diagnosis)**, after the exit audit at the
plan's declared position showed exactly one restricted coupling-state component
above the tolerance on both pulsed configurations, in every arm.  The
observer's shape follows ``child.install_ruler_observer`` (task A59
(driver-predicate-mode)): an environment variable, a refusal on a campaign run,
a file of its own.
"""

from __future__ import annotations

import json
import os
import traceback
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from . import data_structure as structure_mod
from . import predicate as predicate_mod

#: Environment variable that installs the trace.  **Not** a ``PROCESS_ARCH_``
#: name: the driver has never heard of it, so it cannot be mistaken for a
#: switch, cannot be cleared as one, and cannot change what any arm is.
TRACE_VARIABLE = "HARNESS_AUDIT_MAP_TRACE"

#: Where the observation goes.  Its own file, never the run record: the record
#: is what the switch-neutrality gate compares value for value, and a gate-only
#: instrument's output has no business in it.
OBSERVATION_FILE = "audit_map_observation.json"

#: The field the attribution sweeps single out.  It is a **hypothesis under
#: test**, not a conclusion: the radial-discretisation setting of the TF-coil
#: stress calculation, which the model's own ``output`` branch raises from its
#: default to its maximum and never puts back.  Two sweeps decide it — one that
#: puts back this field alone, one that puts back every other changed field and
#: not this one — so the attribution is a leave-one-out pair rather than an
#: argument from plausibility.  If the pair ever disagrees with the whole-set
#: sweep, the pair is what is reported.
CANDIDATE_FIELD = "tfcoil.n_rad_per_layer"

#: Components whose before-and-after value every sweep reports, whatever their
#: place in the residual ordering.  The head below reports the largest movers,
#: which is exactly the wrong population for a component one is asking about
#: *because* it sometimes does not move: a row that reads "absent" because the
#: component fell out of the top ten is a gap, not a measurement.
TRACKED_COMPONENTS: tuple[str, ...] = ("tfcoil.insstrain",)

#: How many components of a sweep's residual are reported with their before and
#: after values.  The summary carries the maximum and the count above the
#: tolerance for all of them; this is the head of the ordered list.
N_COMPONENTS_REPORTED = 10


class AuditMapError(RuntimeError):
    """A refusal.  Never downgraded into a warning."""


# --------------------------------------------------------------------------
# whole-data-structure snapshots
# --------------------------------------------------------------------------
#
# The three functions this section used to define — snapshot the whole data
# structure, compare two snapshots, write one back — now live in
# ``harness/data_structure.py``, because ruling **D25** makes the same
# mechanism part of the exit audit, which runs on every run.  This module is a
# gate instrument refused on campaign runs; a definition both need cannot live
# in it.  The names below are this module's own spelling of that module's
# functions, kept so that the diagnosis stage reads as it did.

snapshot_data_structure = structure_mod.snapshot
data_structure_differences = structure_mod.differences
restore_data_structure = structure_mod.restore


# --------------------------------------------------------------------------
# the trace, installed for the run
# --------------------------------------------------------------------------


def install(
    caller_mod, module_solve_mod, *, coupling_state_path: Path, run_kind: str
) -> dict[str, Any] | None:
    """Watch the positions the audit's premise depends on.  Observation only.

    Returns the trace state, or ``None`` when the variable is unset — in which
    case nothing is wrapped and the run is identical to one made without this
    module in the tree at all.

    Three wraps, each of which returns exactly what the unwrapped call returns:

    * ``Caller._call_models_once`` — the coupling state after **every** sweep of
      the model set, kept only as the latest, and frozen the moment the output
      path is entered.  That latest one is the loop's own exit state: the
      predicate reads ``y`` immediately after the sweep and stops there;
    * ``Caller.call_models`` — the same, one step later, after the objective and
      constraint layer has run, so that what that layer writes into the
      coupling state is visible as a difference rather than assumed to be
      nothing;
    * the driver's own exit-snapshot hook — which the harness installed before
      this — so that a whole-data-structure snapshot is taken at each position
      the driver offers, beside the coupling-state snapshot the driver takes
      there.

    Keeping only the latest is what makes the per-sweep wrap affordable: one
    further read of the coupling state per sweep, which is the same read the
    predicate makes, and no serialisation until the run is over.
    """
    if not os.environ.get(TRACE_VARIABLE, "").strip():
        return None
    if run_kind == "campaign":
        raise AuditMapError(
            f"{TRACE_VARIABLE} is set on a campaign run.  This trace reads the "
            f"coupling state once more per sweep and snapshots the whole data "
            f"structure at the output path's entry; a campaign carrying it "
            f"would publish per-sweep costs measured with an instrument in the "
            f"loop.  It is a gate instrument, refused here rather than allowed "
            f"to contaminate a measurement."
        )
    state: dict[str, Any] = {
        "installed": True,
        "coupling_state": str(coupling_state_path),
        "what": (
            "the positions the exit audit's premise depends on: the coupling "
            "state at the loop's own exit, the coupling state one step later "
            "at the evaluation's exit, and the whole data structure at the "
            "entry to the output path and at the moment the diagnosis sweeps "
            "begin"
        ),
        "n_sweeps_seen": 0,
        "n_evaluations_seen": 0,
        "frozen_at_output_entry": False,
        "positions_seen": [],
        "errors": {},
    }
    holder: dict[str, Any] = {}

    def spec_of():
        if "spec" not in holder:
            spec, provenance = module_solve_mod.load_spec(str(coupling_state_path))
            holder["spec"] = spec
            holder["provenance"] = provenance
        return holder["spec"]

    original_once = caller_mod.Caller._call_models_once
    original_call = caller_mod.Caller.call_models

    def traced_once(self, xc):
        result = original_once(self, xc)
        if not state["frozen_at_output_entry"]:
            state["n_sweeps_seen"] += 1
            try:
                spec = spec_of()
                holder["last_sweep_y"] = spec.read(spec.bind(self.data))
                holder["last_sweep_x"] = [float(v) for v in np.asarray(xc).ravel()]
            except Exception:  # noqa: BLE001 - recorded, never raised
                state["errors"]["last_sweep"] = traceback.format_exc()
        return result

    def traced_call(self, xc, m):
        result = original_call(self, xc, m)
        if not state["frozen_at_output_entry"]:
            state["n_evaluations_seen"] += 1
            try:
                spec = spec_of()
                holder["last_evaluation_y"] = spec.read(spec.bind(self.data))
                holder["last_evaluation_x"] = [
                    float(v) for v in np.asarray(xc).ravel()
                ]
            except Exception:  # noqa: BLE001 - recorded, never raised
                state["errors"]["last_evaluation"] = traceback.format_exc()
        return result

    caller_mod.Caller._call_models_once = traced_once
    caller_mod.Caller.call_models = traced_call

    inner_hook = caller_mod.EXIT_SNAPSHOT_HOOK[0]
    if inner_hook is None:
        state["errors"]["hook"] = (
            "the driver's exit-snapshot hook was not installed before this "
            "trace, so the whole-data-structure snapshots at the driver's own "
            "positions could not be taken"
        )
    else:

        def traced_hook(models, data, where):
            record = inner_hook(models, data, where)
            try:
                holder.setdefault("data_structure", {})[where] = (
                    snapshot_data_structure(data)
                )
                state["positions_seen"].append(where)
            except Exception:  # noqa: BLE001 - recorded, never raised
                state["errors"][f"hook:{where}"] = traceback.format_exc()
            if where == "entry_to_write_output_files":
                state["frozen_at_output_entry"] = True
            return record

        caller_mod.EXIT_SNAPSHOT_HOOK[0] = traced_hook

    holder["state"] = state
    state["_holder_id"] = id(holder)
    _HOLDERS[id(state)] = holder
    return state


#: The trace's working store, keyed by the state object handed back to the
#: caller.  Kept out of the state itself so that the state stays JSON-writable
#: at every moment, including when a run crashes between install and observe.
_HOLDERS: dict[int, dict[str, Any]] = {}


def mark(state: dict[str, Any] | None, data, where: str) -> None:
    """Take a whole-data-structure snapshot at a position the harness names.

    Used for the one position the driver does not offer: the moment just before
    the run record's own exit audit, which is the state the audit's sweep is
    actually evaluated in.
    """
    if state is None:
        return
    holder = _HOLDERS.get(id(state))
    if holder is None:
        return
    try:
        holder.setdefault("data_structure", {})[where] = snapshot_data_structure(data)
        state["positions_seen"].append(where)
    except Exception:  # noqa: BLE001 - recorded, never raised
        state["errors"][f"mark:{where}"] = traceback.format_exc()


# --------------------------------------------------------------------------
# the sweeps, taken after the run
# --------------------------------------------------------------------------

#: The declared series.  One row per sweep: the name it is published under, the
#: coupling-state snapshot it starts from, whether the data structure is put
#: back to the state the diagnosis found or to the state at the entry to the
#: output path for the fields that differ, and whether it continues from the
#: previous sweep's result instead of restoring anything.
SWEEP_SERIES: tuple[dict[str, Any], ...] = (
    {
        "name": "output_entry_as_found",
        "from": "entry_to_write_output_files",
        "restore": "none",
        "what": (
            "the run record's own exit audit, re-taken: the state the solve "
            "handed over, swept in the data structure the run was left in.  "
            "Its residual must reproduce the record's exit audit exactly, "
            "which is what makes every other row here comparable with a "
            "published number"
        ),
    },
    {
        "name": "output_entry_as_found_second_sweep",
        "from": "continue",
        "restore": "none",
        "what": (
            "a second sweep from where the first one landed.  A residual as "
            "large as the first's is a cycle; one at zero is a one-off "
            "recomputation"
        ),
    },
    {
        "name": "output_entry_with_the_solve_phase_settings",
        "from": "entry_to_write_output_files",
        "restore": "differing",
        "what": (
            "the same state, swept with every data-structure field the output "
            "path changed put back to the value it held at the entry to the "
            "output path — the map the loop iterated, on the state the loop "
            "handed over"
        ),
    },
    {
        "name": "output_entry_with_the_solve_phase_settings_second_sweep",
        "from": "continue",
        "restore": "none",
        "what": "a second sweep of the loop's own map, for the same question",
    },
    {
        "name": "output_entry_with_only_the_candidate_put_back",
        "from": "entry_to_write_output_files",
        "restore": "candidate",
        "what": (
            "the same state, swept with ONE field put back to its value at "
            "the entry to the output path: the candidate named in "
            "CANDIDATE_FIELD.  Half of the leave-one-out attribution"
        ),
    },
    {
        "name": "output_entry_without_the_candidate_put_back",
        "from": "entry_to_write_output_files",
        "restore": "differing_except_the_candidate",
        "what": (
            "the same state, swept with every other changed field put back "
            "and the candidate left as the output path set it.  The other "
            "half: if this row keeps the residual and the row above removes "
            "it, the attribution is exact"
        ),
    },
    *(
        {
            "name": f"output_entry_with_the_candidate_at_{value}",
            "from": "entry_to_write_output_files",
            "restore": "set_candidate",
            "value": value,
            "what": (
                f"the same state, swept with the candidate field set to "
                f"{value}.  The series is a dose response: if the residual is "
                f"a function of this one setting, the attribution is not an "
                f"argument but a curve"
            ),
        }
        for value in (100, 200, 300, 400, 500)
    ),
    {
        "name": "loop_exit_as_found",
        "from": "last_sweep",
        "restore": "none",
        "what": (
            "the coupling state after the loop's own last sweep, swept in the "
            "data structure the run was left in"
        ),
    },
    {
        "name": "loop_exit_with_the_solve_phase_settings",
        "from": "last_sweep",
        "restore": "differing",
        "what": "the same, with the loop's own map",
    },
)


def observe(
    state: dict[str, Any] | None,
    caller_mod,
    module_solve_mod,
    *,
    single_run,
    outdir: Path,
) -> dict[str, Any] | None:
    """Take the declared series of sweeps and write the observation out.

    Called **after** the run record's own exit audit, so that nothing here can
    change the number the record publishes.  Returns the observation, or
    ``None`` when the trace was never installed.
    """
    if state is None:
        return None
    holder = _HOLDERS.get(id(state), {})
    observation: dict[str, Any] = dict(state)
    observation.pop("_holder_id", None)
    try:
        _observe(observation, holder, caller_mod, module_solve_mod, single_run)
    except Exception:  # noqa: BLE001 - recorded, never raised
        observation["failed"] = traceback.format_exc()
    path = Path(outdir) / OBSERVATION_FILE
    path.write_text(json.dumps(observation, indent=2, default=str) + "\n")
    observation["written_to"] = str(path)
    return observation


def _observe(observation, holder, caller_mod, module_solve_mod, single_run) -> None:
    data = single_run.data
    spec, provenance = module_solve_mod.load_spec(observation["coupling_state"])
    tau = float(getattr(module_solve_mod, "TAU", 1e-6))
    predicate_mode = getattr(module_solve_mod, "PREDICATE_MODE", "frozen")
    from .. import ystate as ystate_mod

    rulers = ystate_mod.RULERS
    frozen_ruler = ystate_mod.RULER_FROZEN

    observation["provenance"] = provenance
    observation["tau"] = tau
    observation["predicate_mode_the_run_stopped_on"] = predicate_mode

    # -- the states, serialised now that the run is over ------------------
    snapshots: dict[str, Any] = {}
    for key, name in (
        ("last_sweep_y", "last_sweep"),
        ("last_evaluation_y", "last_evaluation"),
    ):
        if key in holder:
            snapshots[name] = predicate_mod.snapshot_record(
                spec, holder[key], predicate_mode=predicate_mode
            )
    driver_snapshots = dict(getattr(caller_mod, "EXIT_SNAPSHOTS", {}) or {})
    for where, record in driver_snapshots.items():
        snapshots[where] = record

    observation["coupling_state_snapshots"] = {
        name: {
            "n_components": record["n_components"],
            "components_sha256": record["components_sha256"],
        }
        for name, record in snapshots.items()
    }
    observation["design_vectors"] = {
        "last_sweep": _hexes(holder.get("last_sweep_x")),
        "last_evaluation": _hexes(holder.get("last_evaluation_x")),
        "audit_x_xcm": _hexes(
            [
                float(v)
                for v in single_run.data.numerics.xcm[
                    : int(single_run.data.numerics.n_iteration_variables)
                ]
            ]
        ),
    }

    # -- is the audited state the loop's exit state? ----------------------
    observation["state_comparisons"] = {}
    pairs = (
        ("last_sweep", "last_evaluation"),
        ("last_evaluation", "entry_to_write_output_files"),
        ("last_sweep", "entry_to_write_output_files"),
        ("entry_to_write_output_files", "before_finalise"),
    )
    for left, right in pairs:
        if left not in snapshots or right not in snapshots:
            observation["state_comparisons"][f"{left}__vs__{right}"] = {
                "compared": False,
                "why": f"{left if left not in snapshots else right} was not taken",
            }
            continue
        y_left = predicate_mod.restore_snapshot(spec, snapshots[left])
        y_right = predicate_mod.restore_snapshot(spec, snapshots[right])
        summary = predicate_mod.cross_residual(
            spec, y_left, y_right, tau, ruler=frozen_ruler
        )
        bitwise = [
            spec.name(i)
            for i in range(len(spec.keys))
            if predicate_mod.snap_value(y_left[i])
            != predicate_mod.snap_value(y_right[i])
        ]
        summary["compared"] = True
        summary["n_components"] = len(spec.keys)
        summary["n_not_bit_identical"] = len(bitwise)
        summary["not_bit_identical"] = bitwise[:200]
        summary["not_bit_identical_listed"] = min(len(bitwise), 200)
        observation["state_comparisons"][f"{left}__vs__{right}"] = summary

    # -- what the output path changed outside the coupling state ----------
    structures = holder.get("data_structure", {})
    observation["data_structure_positions"] = {
        where: {
            "n_fields": snapshot["n_fields"],
            "n_namespaces": snapshot["n_namespaces"],
            "skipped_namespaces": snapshot["skipped_namespaces"],
        }
        for where, snapshot in structures.items()
    }
    coupling_names = {spec.name(i) for i in range(len(spec.keys))}
    differing: list[str] = []
    observation["data_structure_comparisons"] = {}
    for left, right in (
        ("entry_to_write_output_files", "before_finalise"),
        ("entry_to_write_output_files", "before_the_record_audit"),
    ):
        if left not in structures or right not in structures:
            observation["data_structure_comparisons"][f"{left}__vs__{right}"] = {
                "compared": False,
                "why": (
                    f"{left if left not in structures else right} was not taken"
                ),
            }
            continue
        difference = data_structure_differences(structures[left], structures[right])
        outside = [n for n in difference["differ"] if n not in coupling_names]
        inside = [n for n in difference["differ"] if n in coupling_names]
        difference["n_outside_the_coupling_state"] = len(outside)
        difference["outside_the_coupling_state"] = outside
        difference["n_inside_the_coupling_state"] = len(inside)
        difference["detail"] = {
            name: difference["detail"][name] for name in outside
        }
        difference["compared"] = True
        observation["data_structure_comparisons"][f"{left}__vs__{right}"] = difference
        if right == "before_the_record_audit":
            differing = outside
    observation["fields_put_back_for_the_solve_phase_map"] = differing
    observation["n_fields_put_back_for_the_solve_phase_map"] = len(differing)

    # -- the sweeps -------------------------------------------------------
    base = structures.get("before_the_record_audit")
    entry_structure = structures.get("entry_to_write_output_files")
    n = int(single_run.data.numerics.n_iteration_variables)
    x = np.array(single_run.data.numerics.xcm[:n], dtype=float)
    observation["sweeps"] = []
    for row in SWEEP_SERIES:
        observation["sweeps"].append(
            _one_sweep(
                row,
                spec=spec,
                data=data,
                models=single_run.models,
                caller_mod=caller_mod,
                snapshots=snapshots,
                base=base,
                entry_structure=entry_structure,
                differing=differing,
                x=x,
                tau=tau,
                rulers=rulers,
                frozen_ruler=frozen_ruler,
            )
        )


def _one_sweep(
    row,
    *,
    spec,
    data,
    models,
    caller_mod,
    snapshots,
    base,
    entry_structure,
    differing,
    x,
    tau,
    rulers,
    frozen_ruler,
) -> dict[str, Any]:
    """One sweep of the declared series, from a fully specified state."""
    result: dict[str, Any] = {
        "name": row["name"],
        "from": row["from"],
        "restore": row["restore"],
        "what": row["what"],
    }
    try:
        if row["from"] != "continue":
            if row["from"] not in snapshots:
                result["skipped"] = (
                    f"no coupling-state snapshot was taken at {row['from']!r}"
                )
                return result
            if base is None:
                result["skipped"] = (
                    "no whole-data-structure snapshot was taken before the "
                    "record's audit, so a sweep from a specified state could "
                    "not be set up"
                )
                return result
            result["data_structure_restore"] = restore_data_structure(data, base)
            result["coupling_state_restore"] = predicate_mod.write_entry_state(
                spec, data, snapshots[row["from"]]
            )
            if not result["coupling_state_restore"]["readback_bitexact"]:
                result["refused"] = (
                    "the coupling-state snapshot did not restore bit for bit; "
                    "a residual measured from a state nobody chose is worse "
                    "than no residual"
                )
                return result
            put_back = None
            if row["restore"] == "differing":
                put_back = list(differing)
            elif row["restore"] == "candidate":
                put_back = [n for n in differing if n == CANDIDATE_FIELD]
            elif row["restore"] == "differing_except_the_candidate":
                put_back = [n for n in differing if n != CANDIDATE_FIELD]
            elif row["restore"] == "set_candidate":
                namespace_name, _, field = CANDIDATE_FIELD.partition(".")
                setattr(getattr(data, namespace_name), field, row["value"])
                result["candidate_set_to"] = getattr(
                    getattr(data, namespace_name), field
                )
            if put_back is not None:
                if entry_structure is None:
                    result["skipped"] = (
                        "no whole-data-structure snapshot was taken at the "
                        "entry to the output path, so the solve-phase values "
                        "of the changed fields are not known"
                    )
                    return result
                result["n_fields_put_back"] = len(put_back)
                result["fields_put_back"] = put_back[:20]
                result["candidate_among_the_changed_fields"] = (
                    CANDIDATE_FIELD in differing
                )
                result["settings_restore"] = restore_data_structure(
                    data, entry_structure, only=put_back
                )
        bound = spec.bind(data)
        y_before = spec.read(bound)
        nodes_before = caller_mod.NODE_CALLS[0]
        caller_mod.Caller(models, data)._call_models_once(x)
        y_after = spec.read(bound)
        result["node_calls"] = caller_mod.NODE_CALLS[0] - nodes_before
        result["charged_to_the_arm"] = False
        result["rulers"] = {}
        for ruler in rulers:
            residual = spec.residual(y_before, y_after, ruler=ruler)
            result["rulers"][ruler] = {
                "residual_max": float(residual.max),
                "residual_max_hex": float(residual.max).hex(),
                "argmax": (
                    None if residual.argmax is None else spec.name(residual.argmax)
                ),
                "n_above_tau": residual.n_above(tau),
            }
        residual = spec.residual(y_before, y_after, ruler=frozen_ruler)
        order = sorted(
            range(len(residual.idx_c)),
            key=lambda p: -float(residual.scaled[p]),
        )[:N_COMPONENTS_REPORTED]
        scaled_by_index = {
            int(residual.idx_c[p]): float(residual.scaled[p])
            for p in range(len(residual.idx_c))
        }
        result["tracked"] = {}
        for name in TRACKED_COMPONENTS:
            index = predicate_mod.component_index(spec, name)
            result["tracked"][name] = (
                {"present_in_the_spec": False}
                if index is None
                else {
                    "present_in_the_spec": True,
                    "before_hex": _hex_of(y_before[index]),
                    "after_hex": _hex_of(y_after[index]),
                    "scaled_hex": (
                        None
                        if index not in scaled_by_index
                        else float(scaled_by_index[index]).hex()
                    ),
                    "tested_as_continuous": index in scaled_by_index,
                }
            )
        result["head"] = [
            {
                "component": spec.name(int(residual.idx_c[p])),
                "scaled_hex": float(residual.scaled[p]).hex(),
                "before_hex": _hex_of(y_before[int(residual.idx_c[p])]),
                "after_hex": _hex_of(y_after[int(residual.idx_c[p])]),
            }
            for p in order
        ]
    except Exception:  # noqa: BLE001 - recorded, never raised
        result["failed"] = traceback.format_exc()
    return result


def _hex_of(value) -> str | None:
    try:
        return float(value).hex()
    except Exception:  # noqa: BLE001
        return None


def _hexes(values) -> list[str] | None:
    if values is None:
        return None
    return [float(v).hex() for v in values]
