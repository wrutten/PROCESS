"""Everything that runs *inside* a measurement subprocess, shared by both phases.

Derived from ``arch_surgery/idf_probe/run_one.py`` (the optimisation phase's run
driver, one 1 000-line ``main()``) and ``arch_surgery/idf_probe/v2_eval_one.py``
/ ``a44_eval_one.py`` (the evaluation phase's), all read at ``9a8defa6``; task
**A50 (harness-run)**.  Those two files carried parallel copies of the same six
instruments, and the harness implementation plan's §4.2 calls collapsing them
the highest-value and highest-risk change in the rewrite.  Gate **GR** is what
makes it safe: the twenty reference runs must reproduce the previous revision's
numbers bit for bit before this module is believed.

Why the run driver lives *inside* the subprocess
------------------------------------------------
The driver stamps its counters as module-level globals.  A harness reads them by
importing the driver **in the same process as the run** and reading them
afterwards, so the code that starts a run and the code that records it cannot be
separated.  And a run must be its own process: PROCESS holds its output-file
handles as *class* attributes and its initialisation mutates a global, so two
runs in one interpreter contaminate each other.

The instruments, and what each is for
-------------------------------------
Every one of them is **harness-side, additive and identical in every arm**: it
reads counters and appends to lists, mutates nothing the models see, and takes no
branch a result depends on.

``resolved_switches``
    what the driver *resolved*, read back from the imported modules — never the
    environment echoed back.  A tree that does not implement a switch ignores
    it silently and runs a different arm under the right name; this is the only
    thing that catches that.
``node census``
    model executions per node name.  The cost unit checked rather than
    asserted: the per-name counts must sum to the reported total.
``entry census``
    net electric power at the state each evaluation is entered with.  PROCESS's
    cost model diverges where that is not positive, which makes a
    median-scaled relative test arbitrarily tight there, and displaced starts
    visit such states by design.
``first evaluation``
    the counts and objective of the run's **first** evaluation of the model
    set.  New here: it is what the evaluation-phase reference arm is checked
    against, since the previous revision had no such arm to compare with.
``exit forensics``
    the five fields recorded at *every* exit, including a crashed one — the
    optimiser's attempts, its exit code, the ladder stage, the constraint
    residual vector and the active set.  Without it an unconverged exit carries
    none of them and a summary drops it silently.
``exit audit``
    one further full sweep of the complete model set past termination, the same
    instrument for every arm, whose own model calls are counted and **never
    charged** to the arm.  This is what "compare at matched achieved accuracy"
    is measured with.
"""

from __future__ import annotations

import importlib
import json
import math
import os
import resource
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Mapping

from ..core import provenance as prov
from ..core import records as records_mod
from ..experiment import switches as switches_mod


# --------------------------------------------------------------------------
# small conversions
# --------------------------------------------------------------------------


def hexf(value) -> str | None:
    """One float as a C99 hex literal: an exact representation of the double."""
    if value is None:
        return None
    return float(value).hex()


def hexes(values) -> list[str]:
    return [float(v).hex() for v in values]


def _plain(value):
    """Anything the driver hands back, in a form JSON can carry."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (set, frozenset)):
        return sorted(str(x) for x in value)
    if isinstance(value, (list, tuple)):
        return [_plain(x) for x in value]
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    return repr(value)


# --------------------------------------------------------------------------
# the tree, and what the driver resolved
# --------------------------------------------------------------------------


def assert_tree(expected: Path) -> str:
    """Refuse unless the imported PROCESS is *exactly* the expected tree.

    Equality of the directory holding the package, never a prefix: the editable
    install points at the main checkout, so a prefix test passes on the main
    tree even when the run is meant to measure a copy.  ``__version__`` is never
    consulted — it is written when a tree is archived and frozen with it, so it
    can agree with a plausible wrong answer, which is worse than no check.
    """
    return str(prov.assert_tree(Path(expected)))


def copy_provenance(tree: Path) -> dict[str, Any]:
    """The identity of the copied driver, from the copy's own provenance file.

    A record names the code that produced it without depending on the working
    tree's git state, which a task worktree can make say anything.
    """
    path = Path(tree) / "PROVENANCE.json"
    if not path.exists():
        return {"present": False, "path": str(path)}
    try:
        record = json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001 - recorded, never raised
        return {"present": False, "path": str(path), "error": str(exc)}
    source = record.get("source") or {}
    frozen = record.get("frozen_physics") or {}
    return {
        "present": True,
        "path": str(path),
        "task": record.get("task"),
        "copy_date": record.get("copy_date"),
        "source_commit": source.get("commit_full") or source.get("commit"),
        "source_tree_sha1": source.get("tree_sha1"),
        "source_file_count": source.get("file_count"),
        "frozen_physics_base_commit": frozen.get("base_commit_full")
        or frozen.get("base_commit"),
    }


def architecture_environment() -> dict[str, str | None]:
    """Every switch variable the harness knows about, and this run's value.

    Recorded in **both** phases.  The previous revision's evaluation-phase
    records carried only a handful of them, so a per-block table could not be
    read from the run's own record; this is the whole list, present with a null
    where the variable is unset.
    """
    return {
        f"env_{name}": os.environ.get(name)
        for name in switches_mod.all_names()
    }


def resolved_switches() -> dict[str, Any]:
    """What the driver resolved, read back from the imported modules.

    The registry says, per switch, which module attributes report it.  A switch
    the tree does not implement shows as ``<not implemented by this tree>``
    rather than as the value the harness asked for, which is the difference
    between "the tree did what I asked" and "the tree ignored me".
    """
    out: dict[str, Any] = {}
    for module, attribute in switches_mod.default_readbacks():
        key = f"{module}.{attribute}"
        try:
            imported = importlib.import_module(module)
        except Exception as exc:  # noqa: BLE001 - recorded, never raised
            out[key] = f"<module not importable: {type(exc).__name__}>"
            continue
        if hasattr(imported, attribute):
            out[key] = _plain(getattr(imported, attribute))
        else:
            out[key] = "<not implemented by this tree>"
    return out


# --------------------------------------------------------------------------
# the instruments
# --------------------------------------------------------------------------


def install_node_census(caller) -> dict[str, dict[str, int]]:
    """Count model executions per node name, harness-side.

    A node is counted only when the driver's own counter moved, so a suppressed
    or deferred node is not miscounted.  ``_run_deferred_tail`` calls each model
    directly and does *not* go through the counted path, so it is counted
    separately: a cost figure quoted as net model evaluations must have nothing
    hiding in that column.
    """
    counted: dict[str, int] = {}
    tail: dict[str, int] = {}
    original_node = caller.Caller._node

    def censused(self, name, run):
        before = caller.NODE_CALLS[0]
        original_node(self, name, run)
        if caller.NODE_CALLS[0] != before:
            counted[name] = counted.get(name, 0) + 1

    caller.Caller._node = censused

    original_tail = caller.Caller._run_deferred_tail

    def tail_censused(self, pending):
        for name, _run in pending:
            tail[name] = tail.get(name, 0) + 1
        return original_tail(self, pending)

    caller.Caller._run_deferred_tail = tail_censused
    return {"counted": counted, "flat_tail": tail}


def install_call_models_census(caller) -> dict[str, Any]:
    """Record, per evaluation of the model set, what it was entered with.

    Two things at once, from one wrap, because they are two reads of the same
    boundary:

    * the **entry census** — net electric power at the state each evaluation is
      entered with.  Where that is not positive, PROCESS's cost model diverges
      and a median-scaled relative test becomes arbitrarily tight; displaced
      starts reach such states by design, so it is measured rather than hoped
      against;
    * the **first evaluation's own counts** — its model executions, its sweeps
      and the objective it returned.  The evaluation-phase reference arm has no
      record in the previous revision to be checked against, so it is checked
      against the first evaluation of the optimisation-phase reference arm
      instead, and that call's numbers have to be recorded for the comparison
      to exist at all.
    """
    census: dict[str, Any] = {
        "p_plant_electric_net_mw_at_entry": [],
        "first_call_models": None,
    }
    original = caller.Caller.call_models
    sweeps_cell = getattr(caller, "DISPATCH_SWEEPS", None)

    def censused(self, xc, m):
        try:
            census["p_plant_electric_net_mw_at_entry"].append(
                float(self.data.heat_transport.p_plant_electric_net_mw)
            )
        except Exception:  # noqa: BLE001 - a census must never break a run
            census["p_plant_electric_net_mw_at_entry"].append(None)
        first = census["first_call_models"] is None
        if not first:
            return original(self, xc, m)
        nodes_before = caller.NODE_CALLS[0]
        sweeps_before = sweeps_cell[0] if sweeps_cell is not None else None
        prime_cell = getattr(caller, "ARRANGEMENT_METHOD_CALLS", None)
        prime_before = prime_cell[0] if prime_cell is not None else None
        census["first_call_models"] = {"in_progress": True}
        objf, conf = original(self, xc, m)
        census["first_call_models"] = {
            "what": (
                "the run's first evaluation of the model set: what it cost and "
                "what it returned, frozen before anything else ran"
            ),
            "node_calls": caller.NODE_CALLS[0] - nodes_before,
            "sweeps": (
                None
                if sweeps_cell is None
                else sweeps_cell[0] - sweeps_before
            ),
            "n_arrangement_method_calls": (
                None if prime_cell is None else prime_cell[0] - prime_before
            ),
            "objf_hex": hexf(objf),
            "conf_l2_hex": hexf(
                sum(float(v) * float(v) for v in conf) ** 0.5
            ),
        }
        return objf, conf

    caller.Caller.call_models = censused
    return census


def summarise_entry_census(values: list) -> dict[str, Any]:
    """The entry census, with its denominator and its one exclusion stated.

    The **first** entry is not a physical state: the very first evaluation of a
    run is entered before any model has run, with net electric power at its
    declared default of zero.  Counting it would report a degenerate start on
    every run of every arm — a zero denominator dressed as a finding — so it is
    reported separately rather than silently dropped.
    """
    finite = [v for v in values if v is not None]
    rest = finite[1:]
    non_positive = [v for v in rest if v <= 0.0]
    return {
        "n_call_models_entries_recorded": len(values),
        "n_recorded_as_float": len(finite),
        "first_entry_p_net_mw": finite[0] if finite else None,
        "first_entry_excluded_because": (
            "entered before any model has run; the field is at its declared "
            "default and is not a state the loop reached"
        ),
        "denominator_entries_after_the_first": len(rest),
        "n_non_positive_entries": len(non_positive),
        "min_entry_p_net_mw": min(rest) if rest else None,
        "max_entry_p_net_mw": max(rest) if rest else None,
        "start_is_degenerate": bool(non_positive),
        "why": (
            "PROCESS's cost model diverges where net electric power is not "
            "positive, so a median-scaled relative convergence test becomes "
            "arbitrarily tight there.  Reported with its denominator beside "
            "every cost figure."
        ),
    }


#: The retry ladder, positionally.  The driver tries the optimiser, then the
#: same problem with a larger finite-difference step, then a smaller one, then a
#: reset Hessian.  The label is checked against the step size recorded beside
#: it, so the positional guess is evidence rather than an assumption.
LADDER: tuple[str, ...] = (
    "initial",
    "epsfcn_x10",
    "epsfcn_x0.1",
    "hessian_reset_b2",
)


def install_exit_forensics(solver_module) -> dict[str, Any]:
    """Record every optimiser attempt, including one that raised.

    A class-level wrap of each solver's ``solve``: it reads state and appends to
    a list.  Without it a crashed or unconverged exit carries none of the five
    fields — the object that held them is discarded on the way out — and a
    summary drops the run rather than classifying it.
    """
    state: dict[str, Any] = {"attempts": [], "data": None}

    def wrap(cls):
        original = cls.solve

        def solved(self):
            numerics = self.data.numerics
            index = len(state["attempts"])
            entry = {
                "attempt": index + 1,
                "ladder_stage_positional": (
                    LADDER[index]
                    if index < len(LADDER)
                    else f"attempt_{index + 1}_beyond_known_ladder"
                ),
                "solver_class": type(self).__name__,
                "epsfcn_at_entry": float(numerics.epsfcn),
                "hessian_b": (
                    None
                    if getattr(self, "b", None) is None
                    else float(self.b)
                ),
            }
            state["data"] = self.data
            try:
                info = original(self)
            except Exception as exc:  # recorded, then re-raised
                entry["raised"] = type(exc).__name__
                state["attempts"].append(entry)
                raise
            entry["ifail"] = int(info)
            try:
                entry["n_solver_iterations"] = int(numerics.n_solver_iterations)
            except Exception:  # noqa: BLE001
                entry["n_solver_iterations"] = None
            conf = getattr(self, "conf", None)
            entry["conf_hex"] = None if conf is None else hexes(conf)
            state["attempts"].append(entry)
            return info

        cls.solve = solved

    wrap(solver_module.Vmcon)
    wrap(solver_module.FSolve)
    return state


def assemble_forensics(
    state: Mapping[str, Any], *, fallback_data=None, conf=None, runner: str = ""
) -> dict[str, Any]:
    """The five fields, from whatever the run left behind.

    The **active set** is operationalised from the solver's own inequality
    convention — a negative normalised residual means violated, and the solver
    tests against its own tolerance — so an inequality is active when its exit
    residual is at or below that tolerance, binding or violated.  Equalities are
    always enforced and are reported as the equality block rather than listed.
    """
    attempts = list(state.get("attempts") or [])
    last = attempts[-1] if attempts else None
    forensics: dict[str, Any] = {
        "recorded_at": "every exit",
        "runner": runner,
        "n_attempts": len(attempts),
        "attempts": attempts,
        "ladder_stage": (last or {}).get("ladder_stage_positional"),
        "ifail": (last or {}).get("ifail"),
        "n_solver_iterations": (last or {}).get("n_solver_iterations"),
        "n_solver_iterations_summed_over_attempts": (
            sum(a.get("n_solver_iterations") or 0 for a in attempts)
            if attempts
            else None
        ),
        "constraint_residual_vector": None,
        "active_set": None,
    }
    if not attempts:
        forensics["solver_fields_null_because"] = (
            "no optimiser attempt was made in this process; these fields are "
            "structurally inapplicable and are recorded as explicit nulls"
        )
    try:
        data = state.get("data") if state.get("data") is not None else fallback_data
        vector = conf
        if vector is None and last and last.get("conf_hex"):
            vector = [float.fromhex(h) for h in last["conf_hex"]]
        if data is not None and vector is not None:
            numerics = data.numerics
            n_equality = int(numerics.n_equality_constraints)
            n_all = n_equality + int(numerics.n_inequality_constraints)
            icc = [int(v) for v in numerics.icc[:n_all]]
            values = [float(v) for v in vector]
            forensics["constraint_residual_vector"] = {
                "icc": icc,
                "n_equality": n_equality,
                "n_inequality": n_all - n_equality,
                "conf": values,
                "conf_hex": hexes(values),
                "what": (
                    "the normalised constraint residual vector at the exit "
                    "this record describes, equality block first"
                ),
            }
            tolerance = float(numerics.force_vmcon_inequality_tolerance)
            inequalities = values[n_equality:]
            forensics["active_set"] = {
                "definition": (
                    "inequality constraints whose normalised exit residual is "
                    "at or below force_vmcon_inequality_tolerance (binding or "
                    "violated; the solver's own convention: negative means "
                    "violated).  Equalities are always enforced and are not "
                    "listed."
                ),
                "tolerance": tolerance,
                "binding_or_violated_icc": [
                    icc[n_equality + j]
                    for j, v in enumerate(inequalities)
                    if v <= tolerance
                ],
                "violated_icc": [
                    icc[n_equality + j]
                    for j, v in enumerate(inequalities)
                    if v < -tolerance
                ],
            }
        elif vector is None:
            forensics["vector_null_because"] = (
                "the run returned no constraint vector; recorded, not papered "
                "over"
            )
    except Exception:  # noqa: BLE001 - recorded, never raised
        forensics["assembly_error"] = traceback.format_exc()
    return forensics


def install_design_vector_perturbation(
    solver_handler, *, seed: int, delta: float, factor
) -> dict[str, Any]:
    """Displace the *initial design vector*, identically in every arm.

    The hook wraps the loading of the scaled bounds rather than the loading of
    the variables, because it must run after both: the scaled bounds are what a
    displaced start is clamped into, and a start outside its own box is not a
    start, it is a different problem.  Nothing under the driver is touched.
    """
    original = solver_handler.load_scaled_bounds
    record: dict[str, Any] = {}

    def perturbed(data):
        original(data)
        numerics = data.numerics
        n = int(numerics.n_iteration_variables)
        rows = []
        n_clamped = 0
        for i in range(n):
            number = int(numerics.ixc[i])
            f = factor(seed, number, delta)
            before = float(numerics.xcm[i])
            wanted = before * f
            low = float(numerics.itv_scaled_lower_bounds[i])
            high = float(numerics.itv_scaled_upper_bounds[i])
            got = min(max(wanted, low), high)
            if got != wanted:
                n_clamped += 1
            numerics.xcm[i] = got
            rows.append(
                {
                    "ixc": number,
                    "factor": f,
                    "scaled_before": before,
                    "scaled_after": got,
                    "clamped": got != wanted,
                }
            )
        record["per_variable"] = rows
        record["n_variables"] = n
        record["n_clamped_to_bounds"] = n_clamped

    solver_handler.load_scaled_bounds = perturbed
    return record


# --------------------------------------------------------------------------
# harvesting the driver's counters
# --------------------------------------------------------------------------


#: The block loop's own totals reach the record under the vocabulary's names.
#: The driver's dictionary still spells three of its keys with the retired
#: inner/outer pair, and that dictionary belongs to the copied tree, which this
#: task does not touch: the translation therefore happens **here**, at the one
#: place the driver's counters become a record field.  The map back to the
#: previous revision's spelling is ``reference.FIELD_NAME_MAP``, which is what
#: lets the committed reproduction reference keep its bytes.
#: (Orchestrator ruling at A56 (driver-renames)'s merge; task A53
#: (harness-tally).)
BLOCK_LOOP_KEYS: dict[str, str] = {
    "outer_pass_hist": "schedule_passes_per_evaluation",
    "inner_sweeps_by_block": "sweeps_by_block",
    "inner_solves_by_block": "solves_by_block",
}


def harvest_counters(caller, *, module_solve=None) -> dict[str, Any]:
    """The driver's own counters, read from the imported modules.

    Read **before** the exit audit runs: the audit's sweep goes through the same
    counted path as any other, and charging the measurement to the thing
    measured is the accounting error this study has already made once.
    """
    out: dict[str, Any] = {
        "node_calls_total": getattr(caller, "NODE_CALLS", [None])[0],
        "node_calls_solve_phase": getattr(
            caller, "NODE_CALLS_AT_OUTPUT", [None]
        )[0],
        "dispatch_sweeps_solve_phase": getattr(
            caller, "DISPATCH_SWEEPS_AT_OUTPUT", [None]
        )[0],
        "n_arrangement_method_calls": getattr(caller, "ARRANGEMENT_METHOD_CALLS", [None])[0],
    }
    histogram = getattr(caller, "SWEEPS_PER_EVAL_HIST", None)
    if histogram is not None:
        ordered = {k: histogram[k] for k in sorted(histogram, key=int)}
        n_evaluations = sum(ordered.values())
        n_sweeps = sum(int(k) * v for k, v in ordered.items())
        out["sweeps_per_eval"] = {
            "hist": ordered,
            "n_evaluations": n_evaluations,
            "n_sweeps": n_sweeps,
            "mean": (n_sweeps / n_evaluations) if n_evaluations else None,
            "what": (
                "sweeps of the node sequence per evaluation of the model set; "
                "the output path is excluded because it does not go through "
                "that entry point"
            ),
        }
    else:
        out["sweeps_per_eval"] = None
    totals = getattr(caller, "MDA_TOTALS", None)
    if totals is not None:
        totals = {BLOCK_LOOP_KEYS.get(k, k): v for k, v in dict(totals).items()}
        totals["moved_constants"] = sorted(totals.get("moved_constants", ()))
        out["block_loop_totals"] = totals
    else:
        out["block_loop_totals"] = None
    per_run = getattr(caller, "DEFER_PER_RUN_TOTALS", None)
    out["defer_per_run_totals"] = (
        dict(per_run)
        if (per_run is not None and getattr(caller, "DEFER_PER_RUN_ENABLED", False))
        else None
    )
    # DR9 (A99 (v5-schedule-and-prime)): the block schedule and the deferral
    # sets, resolved once per run and stamped once -- what was resolved, the
    # digests of what the resolution read, and how many times the resolver
    # ran.  Rendered through JSON so the record holds a copy, never the
    # driver's live dictionary.
    resolution = getattr(caller, "SCHEDULE_RESOLUTION", None)
    out["schedule_resolution"] = (
        json.loads(json.dumps(resolution, default=str))
        if resolution is not None
        else None
    )
    # DR11 (A100 (v5-test-set)): what the block loops tested -- the test set,
    # the loop key it was selected by, the artifact's digests and the width
    # per block -- stamped once by the driver when the sets are first loaded.
    # Null with every switch unset (no block loop runs, the stamp is never
    # filled) and on a tree without the name.
    loop_tests = getattr(module_solve, "LOOP_TEST_SETS", None) if module_solve is not None else None
    out["loop_test_sets"] = (
        json.loads(json.dumps(loop_tests, default=str))
        if isinstance(loop_tests, dict) and loop_tests.get("loaded")
        else None
    )
    return out


#: What each predicate counter is, in one sentence, quoted into every record so
#: a reader does not need the plan open beside it.
PREDICATE_COUNTER_NOTES: dict[str, str] = {
    "predicate_evaluations": (
        "evaluations of the coupling-state convergence test during the solve "
        "phase: one per block-loop sweep that reached its test.  0 in the "
        "reference arms, which stop on upstream's own test instead"
    ),
    "components_compared": (
        "summed over those evaluations, the number of coupling-state "
        "components each one walked — the block's own write set, or the whole "
        "coupling state where the block has none, which is the flat "
        "arrangement's single block"
    ),
    "block_visits": (
        "how many times the block schedule visited each block, whether or not "
        "the visit executed anything"
    ),
    "empty_block_visits": (
        "of those visits, how many executed no model node at all — measured on "
        "the node counter across the visit, not on the block's membership.  On "
        "st_regression the PULSE block still has its member in the schedule "
        "and that member is skipped at the call site, so the block is visited, "
        "a sweep of the model sequence is charged for it, and nothing runs.  "
        "The user ruled that these visits stay and are disclaimed rather than "
        "repaired, because dropping the block would change the node weights "
        "the comparison rests on.  Every table that weights sweeps must say "
        "they are included"
    ),
    "empty_block_sweeps": (
        "sweeps of the model sequence spent inside those empty visits.  A "
        "block visited with no members costs no sweep; a block whose members "
        "are all skipped at the call site costs a full walk of the sequence "
        "executing nothing.  This is what the empty visits actually cost, and "
        "the visit count alone would overstate it"
    ),
    "dispatch_sweeps": (
        "sweeps of the dispatch body over the whole run, on every path that "
        "walks the model sequence: the analysis loop, every block sweep, the "
        "output-time loop and the exit audit"
    ),
    "upstream_predicate_evaluations": (
        "evaluations of upstream's own stopping test — the objective and the "
        "constraint vector against the previous sweep's — during the solve "
        "phase.  0 in the arms that stop on the coupling state"
    ),
    "upstream_components_compared": (
        "summed over those tests, the values each actually compared: the "
        "objective, plus the constraint vector when the objective agreed.  "
        "The pair short-circuits, so this is the width compared and not the "
        "width declared"
    ),
}


def harvest_predicate_counters(caller) -> dict[str, Any]:
    """What the run's convergence tests cost, from the driver's own counters.

    Read at the same moment as the other counters and for the same reason:
    **before** the exit audit, whose own sweep goes through the same counted
    path as any other, so that the measurement is not charged to the thing it
    measures.

    Two predicates are reported separately, never pooled: an arm stops on
    exactly one of them, and they are not the same test.  A run's average test
    width is the ratio of the two counts and is computed here so that every
    reader of a record computes it the same way; it is ``None`` where the count
    is zero, because a width over no evaluations is not a small number, it is
    an absent one.
    """
    evaluations = getattr(caller, "PREDICATE_EVALUATIONS", [None])[0]
    components = getattr(caller, "COMPONENTS_COMPARED", [None])[0]
    upstream_evaluations = getattr(
        caller, "UPSTREAM_PREDICATE_EVALUATIONS", [None]
    )[0]
    upstream_components = getattr(
        caller, "UPSTREAM_COMPONENTS_COMPARED", [None]
    )[0]
    by_block = dict(getattr(caller, "PREDICATE_EVALUATIONS_BY_BLOCK", {}) or {})
    width_by_block = dict(
        getattr(caller, "COMPONENTS_COMPARED_BY_BLOCK", {}) or {}
    )
    visits = dict(getattr(caller, "BLOCK_VISITS", {}) or {})
    empty = dict(getattr(caller, "EMPTY_BLOCK_VISITS", {}) or {})
    empty_sweeps = dict(getattr(caller, "EMPTY_BLOCK_SWEEPS", {}) or {})
    n_visits = sum(visits.values())
    n_empty = sum(empty.values())
    n_empty_sweeps = sum(empty_sweeps.values())
    return {
        "predicate_evaluations": evaluations,
        "components_compared": components,
        "block_visits": dict(sorted(visits.items())),
        "empty_block_visits": dict(sorted(empty.items())),
        "empty_block_sweeps": dict(sorted(empty_sweeps.items())),
        "dispatch_sweeps": getattr(caller, "DISPATCH_SWEEPS", [None])[0],
        "predicate_counters": {
            "what": (
                "what the run's convergence tests cost, in counts.  No "
                "conclusion in this experiment rests on a timing, so the "
                "per-sweep-overhead question is asked in evaluations and "
                "components compared"
            ),
            "coupling_state_predicate": {
                "evaluations": evaluations,
                "components_compared": components,
                "mean_test_width": (
                    (components / evaluations)
                    if (evaluations and components is not None)
                    else None
                ),
                "evaluations_by_block": dict(sorted(by_block.items())),
                "components_compared_by_block": dict(
                    sorted(width_by_block.items())
                ),
                "mean_test_width_by_block": {
                    label: (width_by_block.get(label, 0) / n)
                    for label, n in sorted(by_block.items())
                    if n
                },
            },
            "upstream_predicate": {
                "evaluations": upstream_evaluations,
                "components_compared": upstream_components,
                "mean_test_width": (
                    (upstream_components / upstream_evaluations)
                    if (upstream_evaluations and upstream_components is not None)
                    else None
                ),
                "what": PREDICATE_COUNTER_NOTES["upstream_components_compared"],
            },
            "block_schedule": {
                "visits": n_visits,
                "empty_visits": n_empty,
                "empty_share_of_visits": (
                    (n_empty / n_visits) if n_visits else None
                ),
                "empty_visits_that_cost_a_sweep": n_empty_sweeps,
                "empty_blocks": sorted(k for k, v in empty.items() if v),
                "empty_blocks_costing_a_sweep": sorted(
                    k for k, v in empty_sweeps.items() if v
                ),
                "disclaimed": (
                    "the empty visits are counted and disclaimed, never "
                    "repaired (issue I-20a; the user's ruling): dropping a "
                    "block whose membership is empty would change the node "
                    "weights the comparison rests on"
                ),
            },
            "notes": PREDICATE_COUNTER_NOTES,
        },
        "upstream_predicate_evaluations": upstream_evaluations,
        "upstream_components_compared": upstream_components,
    }


def harvest_output_path(caller) -> dict[str, Any]:
    """Which output path ran, and what it cost.

    Read from the driver's own module-level names, never from the environment
    the harness composed: a tree that ignored the switch would otherwise report
    the arm the harness *asked* for.  ``output_loop_sweeps`` is 0 under the
    finalise-once path by construction rather than by assertion, and
    ``output_path_entries`` is 1 for a single problem — a record showing more
    is a scan, and says so instead of quietly describing its first point.
    """
    return {
        "output_path": getattr(caller, "OUTPUT_PATH_NAME", None),
        "output_loop_sweeps": getattr(caller, "OUTPUT_LOOP_SWEEPS", [None])[0],
        "output_path_entries": getattr(caller, "OUTPUT_PATH_ENTRIES", [None])[0],
    }


#: What the per-attempt accounting is, in one sentence each, quoted into every
#: record so a reader does not need the plan open beside it.
ATTEMPT_NOTES: dict[str, str] = {
    "node_calls_solve_phase": (
        "model executions inside this attempt: the driver's node counter at "
        "the attempt's exit less its value at the previous attempt's exit.  "
        "Summed over the attempts these are the run's solve-phase total, which "
        "is checked rather than assumed"
    ),
    "sweeps": (
        "sweeps of the model sequence inside this attempt, on the same "
        "difference; the output-time loop and the exit audit are in neither, "
        "because they are outside every attempt"
    ),
    "sweeps_by_block": (
        "those sweeps per block of the schedule, where the arm runs one; an "
        "empty mapping where it does not"
    ),
    "sweeps_per_eval": (
        "the attempt's own evaluations of the model set and the sweeps they "
        "took, binned — the evaluation count the transfer needs per attempt, "
        "which an iteration count cannot give because a line search and the "
        "gradient stencil both vary at equal iteration count"
    ),
    "outside_attempts": (
        "model executions and sweeps of the solve phase that fall outside "
        "every attempt: before the first attempt is entered, or after the last "
        "one exits and before the output path is reached.  Expected to be 0 — "
        "the only thing that evaluates the model set during the solve is the "
        "optimiser — and published rather than assumed, because it is what the "
        "summation identity rests on"
    ),
}


def _difference(before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, int]:
    """``after - before``, key by key, keeping only what moved."""
    out: dict[str, int] = {}
    for key in sorted(set(before) | set(after)):
        moved = int(after.get(key, 0)) - int(before.get(key, 0))
        if moved:
            out[key] = moved
    return out


def _sweeps_per_eval(histogram: Mapping[str, int]) -> dict[str, Any]:
    """One binned histogram, with the two totals it implies."""
    ordered = {k: histogram[k] for k in sorted(histogram, key=int)}
    n_evaluations = sum(ordered.values())
    n_sweeps = sum(int(k) * v for k, v in ordered.items())
    return {
        "hist": ordered,
        "n_evaluations": n_evaluations,
        "n_sweeps": n_sweeps,
    }


def harvest_attempt_stamps(caller) -> dict[str, Any]:
    """The retry ladder's boundary stamps, differenced into per-attempt costs.

    The driver stamps its cost counters at the entry to and the exit from every
    attempt of the optimiser's retry ladder (driver change DR7).  An attempt's
    own cost is the difference between consecutive **exit** stamps, with the
    first attempt measured from its own entry stamp — so the arithmetic here is
    a subtraction and nothing is attributed to an attempt that did not happen
    inside it.

    Read for the same reason as the other counters and at the same moment:
    **before** the exit audit takes its extra sweep.  The stamps themselves are
    frozen at the boundaries, so the audit could not move them; reading them
    here keeps every cost figure in one place in the record's construction.
    """
    stamps = list(getattr(caller, "ATTEMPT_STAMPS", []) or [])
    ladders = (getattr(caller, "ATTEMPT_LADDERS", [None]) or [None])[0]
    if not stamps:
        return {
            "available": False,
            "costs": [],
            "n_ladders": ladders,
            "why": (
                "the driver recorded no attempt boundary: nothing in this "
                "process entered the optimiser's retry ladder"
            ),
        }
    entries = [s for s in stamps if s.get("boundary") == "entry"]
    exits = [s for s in stamps if s.get("boundary") == "exit"]
    costs: list[dict[str, Any]] = []
    previous = entries[0]
    for index, stamp in enumerate(exits):
        costs.append(
            {
                "attempt": stamp.get("attempt"),
                "ladder": stamp.get("ladder"),
                "stage": stamp.get("stage"),
                "node_calls_solve_phase": (
                    int(stamp["node_calls"]) - int(previous["node_calls"])
                ),
                "sweeps": (
                    int(stamp["dispatch_sweeps"])
                    - int(previous["dispatch_sweeps"])
                ),
                "sweeps_by_block": _difference(
                    previous.get("sweeps_by_block") or {},
                    stamp.get("sweeps_by_block") or {},
                ),
                "sweeps_per_eval": _sweeps_per_eval(
                    _difference(
                        previous.get("sweeps_per_eval_hist") or {},
                        stamp.get("sweeps_per_eval_hist") or {},
                    )
                ),
                "node_calls_at_exit": int(stamp["node_calls"]),
                "sweeps_at_exit": int(stamp["dispatch_sweeps"]),
            }
        )
        previous = stamp
        _ = index
    return {
        "available": True,
        "costs": costs,
        "n_ladders": ladders,
        "n_boundaries": len(stamps),
        "n_entries": len(entries),
        "n_exits": len(exits),
        "node_calls_at_first_entry": int(entries[0]["node_calls"]),
        "sweeps_at_first_entry": int(entries[0]["dispatch_sweeps"]),
        "node_calls_at_last_exit": int(exits[-1]["node_calls"]),
        "sweeps_at_last_exit": int(exits[-1]["dispatch_sweeps"]),
        "stages": [s.get("stage") for s in exits],
        "notes": ATTEMPT_NOTES,
    }


# --------------------------------------------------------------------------
# the snapshot the exit audit is taken from
# --------------------------------------------------------------------------


def install_exit_snapshot(caller, module_solve, *, coupling_state_path: Path):
    """Install the driver's snapshot hook, and report what it took.

    The plan declares one audit position for every arm: the entry to the output
    path, before any output-time sweep — the state the solve handed over.  The
    audit's sweep mutates the state it measures, so it cannot run there; the
    driver instead calls this hook at that entry (and again immediately before
    the file-writing step), and the residual is computed after the run from the
    restored snapshot.

    **Two snapshots are taken at each position, not one** (ruling D25).  The
    coupling state is what the residual is measured over and what the declared
    position restores bit for bit.  The **whole data structure** is what makes
    the audit's sweep the loop's own map: PROCESS's output path changes model
    settings that are not coupling-state components and never puts them back,
    so a sweep taken after it, from a coupling state alone, evaluates a
    different map (task A61 (insstrain-diagnosis) measured one such setting;
    the point of snapshotting everything is not to depend on which).  The
    structure snapshots are kept in memory under ``structures`` and are
    **never** written into the run record: two thousand fields per position is
    a file a gate would walk value by value, and what the record carries is
    the derived restore's own counts and names.

    The driver owns the *position*; the shape of a snapshot belongs to the
    harness, so what is installed is this function.  It never raises into the
    run: the driver records an exception rather than letting an instrument
    change a measurement's outcome, and the state below carries whatever went
    wrong so the audit can refuse instead of reporting a residual of a state
    nobody chose.
    """
    from . import data_structure as structure_mod
    from . import predicate as predicate_mod

    state: dict[str, Any] = {
        "installed": True,
        "coupling_state": str(coupling_state_path),
        "spec_error": None,
        "positions": {},
        "structures": {},
        "structure_errors": {},
    }
    holder: dict[str, Any] = {}

    def hook(models, data, where):  # noqa: ARG001 - the driver's signature
        t0 = time.perf_counter()
        try:
            return _hook(models, data, where)
        finally:
            state["wall_s"] = state.get("wall_s", 0.0) + (time.perf_counter() - t0)

    def _hook(models, data, where):  # noqa: ARG001 - the driver's signature
        if "spec" not in holder:
            spec, provenance = module_solve.load_spec(str(coupling_state_path))
            holder["spec"] = spec
            holder["provenance"] = provenance
        spec = holder["spec"]
        record = predicate_mod.snapshot_record(
            spec,
            spec.read(spec.bind(data)),
            predicate_mode=getattr(module_solve, "PREDICATE_MODE", "frozen"),
        )
        state["positions"][where] = {
            "components_sha256": record["components_sha256"],
            "n_components": record["n_components"],
        }
        try:
            state["structures"][where] = structure_mod.snapshot(data)
        except Exception:  # noqa: BLE001 - recorded, never raised
            state["structure_errors"][where] = traceback.format_exc()
        return record

    caller.EXIT_SNAPSHOT_HOOK[0] = hook
    return state


def collect_exit_snapshots(caller, state: dict[str, Any], outdir: Path) -> dict[str, Any]:
    """Write the driver's snapshots out, and say which positions it reached.

    Called after the run.  A position the driver never reached — a run that
    crashed before the output path — is reported as absent by name, never as an
    empty comparison (trap T11).

    The whole-data-structure snapshots the hook also takes stay out of the
    block this returns: what goes in the record is how many fields each one
    holds and over how many namespaces, and the restore's own counts and names
    go in the exit audit beside the residual they made possible.
    """
    structures = dict(state.get("structures") or {})
    snapshots = dict(getattr(caller, "EXIT_SNAPSHOTS", {}) or {})
    errors = dict(getattr(caller, "EXIT_SNAPSHOT_ERRORS", {}) or {})
    written: dict[str, str] = {}
    for where, record in snapshots.items():
        name = f"y_{where}.json"
        (Path(outdir) / name).write_text(json.dumps(record))
        written[where] = name
    state = dict(state)
    state.update(
        {
            "positions_offered": list(
                getattr(caller, "EXIT_SNAPSHOT_POSITIONS", ())
            ),
            "positions_taken": sorted(snapshots),
            "positions_that_raised": errors,
            "written_to": written,
            "n_components": {
                where: record["n_components"] for where, record in snapshots.items()
            },
            "components_sha256": {
                where: record["components_sha256"]
                for where, record in snapshots.items()
            },
            "data_structure_positions": {
                where: {
                    "n_fields": snapshot["n_fields"],
                    "n_namespaces": snapshot["n_namespaces"],
                    "skipped_namespaces": snapshot["skipped_namespaces"],
                }
                for where, snapshot in sorted(structures.items())
            },
            "data_structure_positions_that_raised": dict(
                state.get("structure_errors") or {}
            ),
        }
    )
    state.pop("structures", None)
    state.pop("structure_errors", None)
    return state


def summarise_node_census(
    census: Mapping[str, Any],
    *,
    node_calls_total: int | None,
    node_calls_solve_phase: int | None,
    audit_node_calls: int | None,
) -> dict[str, Any]:
    """The per-node counts, with the identity that checks them.

    ``node_calls_total`` is read at the end of the run, **before** the exit
    audit takes its extra sweep, and that sweep goes through the counted path
    like any other — so the per-name counts see it and the reported total does
    not.  The identity below is therefore stronger than equality would be: it
    says both that nothing is uncounted *and* that the audit's cost is exactly
    what the audit reports and is excluded from the arm's.
    """
    counted = dict(sorted((census.get("counted") or {}).items()))
    tail = dict(sorted((census.get("flat_tail") or {}).items()))
    counted_total = sum(counted.values())
    return {
        "per_node_counted": counted,
        "per_node_run_through_flat_deferred_tail_uncounted": tail,
        "sum_counted": counted_total,
        "sum_flat_tail_uncounted": sum(tail.values()),
        "node_calls_total_reported": node_calls_total,
        "node_calls_solve_phase_reported": node_calls_solve_phase,
        "audit_node_calls": audit_node_calls,
        "counted_matches_node_calls_total": (
            counted_total == (node_calls_total or 0) + int(audit_node_calls or 0)
        ),
        "why": (
            "the cost unit checked rather than asserted.  The counted path "
            "increments the driver's counter; the flat deferred tail calls "
            "each model directly and does not, which is the accounting error "
            "that once published a difference whose composition could not be "
            "stated.  sum_flat_tail_uncounted must be 0 for any arm whose cost "
            "is quoted as net model evaluations."
        ),
    }


# --------------------------------------------------------------------------
# the exit audit
# --------------------------------------------------------------------------


def _finite(value) -> bool:
    """Whether *value* is a real number worth writing into a record."""
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _ystate_namespace(spec) -> Mapping[str, Any]:
    """The module globals of whatever coupling-state module *spec* came from.

    Taken from the class's own function globals rather than from
    ``sys.modules``: the driver loads the predicate module by path, with
    ``importlib.util.spec_from_file_location`` and ``exec_module``, and never
    registers it in ``sys.modules`` -- so a lookup by module name finds nothing
    and would silently fall back to a default, which is the shape of failure
    this whole switch exists to prevent.
    """
    return type(spec).residual.__globals__


def ystate_rulers(spec) -> tuple[str, ...]:
    """The rulers the loaded coupling-state module implements, in its order.

    Read from the module the spec came from rather than listed here: there is
    one implementation of the predicate in this revision of the experiment
    (decision D14(c)), and a harness carrying its own list of that module's
    rulers would be a second, differently-maintained copy of the same decision.
    """
    rulers = _ystate_namespace(spec).get("RULERS")
    if not rulers:
        raise RuntimeError(
            "the loaded coupling-state module names no RULERS; the exit audit "
            "cannot say which ruler it was taken on"
        )
    return tuple(rulers)


def ystate_frozen(spec) -> str:
    """The name of the ruler every earlier revision measured on."""
    frozen = _ystate_namespace(spec).get("RULER_FROZEN")
    if not frozen:
        raise RuntimeError(
            "the loaded coupling-state module names no RULER_FROZEN, so the "
            "audit's unprefixed fields could not be said to be any particular "
            "ruler's"
        )
    return frozen


def restricted_audit(
    per_run_artifact: Path,
    configuration: str,
    node_write_sets_path: Path,
    keys: list[str],
    values: list[float],
    tau: float,
) -> tuple[dict[str, Any], set[str]]:
    """The audit maximum over the components the in-loop nodes write.

    Membership is **derived, never listed**: the per-run deferral artifact names
    nodes; the committed run-time write census maps each node to the fields it
    writes for this configuration; the intersection with the audit spec's tested
    keys is the excluded set.  A prefix rule is deliberately not used — one
    configuration's node list contains a node that writes nothing there, and a
    prefix would either miss it or over-match.
    """
    artifact = json.loads(Path(per_run_artifact).read_text())
    nodes = list(artifact["post_solve_nodes"])
    census = json.loads(Path(node_write_sets_path).read_text())["per_scenario"]
    if configuration not in census:
        raise RuntimeError(
            f"{node_write_sets_path} carries no write census for "
            f"{configuration!r}; the restricted audit would be guessed, so it "
            f"is refused"
        )
    writes_by_node = census[configuration]["writes_by_node"]
    known = set(census[configuration].get("node_module") or ()) | set(
        writes_by_node
    )
    excluded: set[str] = set()
    empty: list[str] = []
    for node in nodes:
        if node not in known:
            raise RuntimeError(
                f"per-run node {node!r} is unknown to the {configuration} write "
                f"census {node_write_sets_path}; refusing to derive the "
                f"excluded set"
            )
        if node not in writes_by_node:
            empty.append(node)
            continue
        excluded |= set(writes_by_node[node])
    excluded_keys = excluded & set(keys)
    kept = [(k, v) for k, v in zip(keys, values) if k not in excluded_keys]
    if kept:
        argmax, maximum = max(kept, key=lambda kv: kv[1])
    else:
        argmax, maximum = None, 0.0
    import hashlib

    return (
        {
            "artifact": str(per_run_artifact),
            "per_run_nodes": nodes,
            "nodes_with_empty_write_set": empty,
            "census": str(node_write_sets_path),
            "n_excluded": len(excluded_keys),
            "n_kept": len(kept),
            "excluded_sha256": hashlib.sha256(
                "\n".join(sorted(excluded_keys)).encode()
            ).hexdigest(),
            "max": maximum,
            "max_hex": hexf(maximum),
            "argmax": argmax,
            "n_above": sum(1 for _, v in kept if v >= tau),
            "tau": tau,
        },
        excluded_keys,
    )


#: What the exit audit puts back before its sweep, stamped in every record it
#: writes.  It is the **instrument's version**, and it is in the record so that
#: two residuals can be told apart by the instrument that made them: a gate
#: comparing records across a change to this mechanism must exclude the
#: residual by name, and a gate comparing two records made by the same
#: instrument must not.  The string names the mechanism, never the task or the
#: revision that wrote it.
EXIT_AUDIT_RESTORE = "whole_data_structure_derived_set"

#: Namespaces of the data structure the audit does **not** put back, and why.
#: A rule about one namespace, not a list of fields: whatever it holds back is
#: named per run in the record, so the rule can never quietly grow.
#:
#: ``numerics`` is the optimiser's own account of the run — the design vector,
#: the constraint residuals, the iteration and call counters, the
#: finite-difference step.  The run record reads it **after** the audit, and the
#: models reach none of it except through the design vector, which the audit
#: injects explicitly.  Putting it back would mean the instrument rewinding the
#: run's own counters and the record then publishing the instrument's
#: bookkeeping as the run's cost.
#:
#: This is not a guess.  The switch-neutrality gate caught it: with the
#: namespace restored, ``n_model_calls`` — one of the values the reproduction
#: gate compares — read two lower on the reference arm, because PROCESS's
#: output-time loop had incremented it twice between the snapshot and the audit
#: and the restore wound it back.  The answer to a gate catching an instrument
#: contaminating a measurement is to fix the instrument, not to exclude the
#: measurement.
NAMESPACES_THE_AUDIT_DOES_NOT_RESTORE: dict[str, str] = {
    "numerics": (
        "the optimiser's own account of the run: the design vector, the "
        "constraint residuals, the iteration and call counters, the "
        "finite-difference step.  The record reads it after the audit and the "
        "models reach it only through the design vector, which the audit "
        "injects; restoring it would rewind the run's own counters"
    ),
}


def _restore_the_solve_phase_structure(
    data,
    *,
    structure_mod,
    structure_snapshots: Mapping[str, Any] | None,
    restore_from_position: str | None,
    coupling_names: set[str],
    audit_position: str,
    coupling_state_is_restored: bool,
) -> dict[str, Any]:
    """Put the data structure back to the snapshot, field by derived field.

    Returns the instrument block the record publishes.  Three things are always
    in it, whatever happened: which positions were snapshotted, how many fields
    were restored, and how many could not be **and which**.

    The restored set is derived — the fields that differ between the snapshot
    and the state this sweep would otherwise start from — with the coupling
    state's own components left out of it.  Those are governed by the audit
    position: at the declared position they are restored from the coupling
    snapshot immediately after this, bit for bit or the audit refuses; at the
    position after the run they are *deliberately* the state the run ended in,
    which is what that position means.  Mixing the two would quietly turn one
    position into the other.
    """
    instrument: dict[str, Any] = {
        "restores": EXIT_AUDIT_RESTORE,
        "what": (
            "before the sweep, the data structure is put back to the snapshot "
            "taken at the audit's snapshot position for every field that has "
            "changed since — a derived set, never a list — so that the sweep "
            "evaluates the map the loop iterated and not the one PROCESS's "
            "output path left behind.  The coupling state's own components are "
            "not in that set: at the declared position they are restored from "
            "the coupling snapshot, bit for bit; after the run they are the "
            "state the run ended in, which is what that position is"
        ),
        "audit_position": audit_position,
        "positions_snapshotted": sorted(structure_snapshots or {}),
        "snapshot_position": restore_from_position,
        "coupling_state_restored_from_a_snapshot": bool(coupling_state_is_restored),
    }
    snapshot = (structure_snapshots or {}).get(restore_from_position or "")
    if snapshot is None:
        instrument.update(
            {
                "restored": False,
                "why": (
                    "this audit names no snapshot position: the phase "
                    "evaluates the model set once and never enters the output "
                    "path, so nothing the output path changes can be in the "
                    "state the sweep starts from, and there is nothing to put "
                    "back"
                    if restore_from_position is None
                    else (
                        f"no whole-data-structure snapshot was taken at "
                        f"{restore_from_position!r} — the run never reached "
                        f"that position — so the fields the output path "
                        f"changed are not known and none was put back"
                    )
                ),
                "n_fields_in_the_snapshot": 0,
                "n_derived": 0,
                "derived": [],
                "n_restored": 0,
                "n_not_restorable": 0,
                "not_restorable": [],
                # The census of what could never be put back is a property of
                # the data structure and of the serialiser, not of the run, so
                # it is taken here too — from the live structure — and every
                # record names those fields whether or not this audit had
                # anything to restore.  A record that said only "0 restored,
                # 0 not restorable" would be true and would still leave a
                # reader thinking the mechanism is total.
                "round_trip_census": structure_mod.round_trip_census(
                    structure_mod.snapshot(data)
                ),
            }
        )
        return instrument
    difference = structure_mod.differences(snapshot, structure_mod.snapshot(data))
    outside = [n for n in difference["differ"] if n not in coupling_names]
    inside = [n for n in difference["differ"] if n in coupling_names]
    held_back = [
        n
        for n in outside
        if n.partition(".")[0] in NAMESPACES_THE_AUDIT_DOES_NOT_RESTORE
    ]
    derived = [n for n in outside if n not in set(held_back)]
    put_back = structure_mod.restore(data, snapshot, only=derived)
    instrument.update(
        {
            "restored": True,
            "n_fields_in_the_snapshot": snapshot["n_fields"],
            "n_namespaces_in_the_snapshot": snapshot["n_namespaces"],
            "n_fields_compared": difference["n_compared"],
            "n_fields_differing": difference["n_differ"],
            "n_differing_outside_the_coupling_state": len(outside),
            "n_derived": len(derived),
            "derived": derived,
            "n_held_back_by_rule": len(held_back),
            "held_back_by_rule": held_back,
            "namespaces_not_restored": dict(NAMESPACES_THE_AUDIT_DOES_NOT_RESTORE),
            "n_differing_inside_the_coupling_state": len(inside),
            "differing_inside_the_coupling_state": inside[:200],
            "n_restored": put_back["n_restored"],
            "n_not_restorable": put_back["n_not_restorable"],
            "not_restorable": put_back["not_restorable"],
            "restore": put_back,
            "round_trip_census": structure_mod.round_trip_census(snapshot),
        }
    )
    return instrument


def _census_the_state_the_sweep_starts_from(
    instrument: dict[str, Any],
    data,
    *,
    structure_mod,
    structure_snapshots: Mapping[str, Any] | None,
    restore_from_position: str | None,
    coupling_names: set[str],
) -> None:
    """How far the state the sweep is about to take is from the snapshot.

    Taken after both restores, over the **whole** snapshot rather than over the
    set that was put back, which is the difference between "everything I tried
    to restore worked" and "the state I am about to sweep is the state I said
    it was".  The second is the claim the residual rests on, so it is the one
    the record carries.  Its split — inside the coupling state, outside it — is
    what makes the two audit positions legible: at the declared position both
    halves are 0, and after the run the inside half is the output path's own
    work on the coupling state, which that position exists to keep.
    """
    snapshot = (structure_snapshots or {}).get(restore_from_position or "")
    if snapshot is None:
        instrument["state_the_sweep_starts_from"] = {
            "compared": False,
            "why": instrument.get("why", "no snapshot to compare against"),
        }
        return
    difference = structure_mod.differences(snapshot, structure_mod.snapshot(data))
    still = difference["differ"]
    outside = [n for n in still if n not in coupling_names]
    inside = [n for n in still if n in coupling_names]
    held_back = [
        n
        for n in outside
        if n.partition(".")[0] in NAMESPACES_THE_AUDIT_DOES_NOT_RESTORE
    ]
    instrument["state_the_sweep_starts_from"] = {
        "compared": True,
        "n_fields_compared": difference["n_compared"],
        "n_still_differing_from_the_snapshot": len(still),
        "n_outside_the_coupling_state": len(outside),
        "outside_the_coupling_state": outside,
        "n_of_those_held_back_by_rule": len(held_back),
        "held_back_by_rule": held_back,
        "n_of_those_the_restore_asked_for_and_missed": len(
            [n for n in outside if n not in set(held_back)]
        ),
        "the_restore_asked_for_and_missed": [
            n for n in outside if n not in set(held_back)
        ],
        "n_inside_the_coupling_state": len(inside),
        "inside_the_coupling_state": inside[:200],
    }


def take_exit_audit(
    caller,
    module_solve,
    *,
    models,
    data,
    x,
    coupling_state_path: Path,
    outdir: Path,
    position: str,
    write_state: bool,
    per_run_artifact: Path | None = None,
    node_write_sets_path: Path | None = None,
    configuration: str = "",
    from_snapshot: Mapping[str, Any] | None = None,
    structure_snapshots: Mapping[str, Any] | None = None,
    restore_from_position: str | None = None,
) -> dict[str, Any]:
    """One further full sweep past termination, and how far the state moved.

    The same instrument in every arm — a fresh caller with nothing deferred and
    no block filter — which is what makes "compare at matched achieved accuracy"
    mean anything.  Its own model calls are recorded and **never charged** to
    the arm.  The sweep mutates the state, so the exit state is written out
    first and nothing may run after it.

    ``from_snapshot`` moves the audit to a position the run has already passed:
    the state the driver captured there is written back into the data structure
    and the sweep is taken from *that*, which is how the plan's declared
    position — the entry to the output path — is reached without handing the
    output path an audited state.  The restore is proved bit-exact before the
    sweep runs, and an audit whose restore is not bit-exact is **refused**: a
    residual measured from a state nobody chose is worse than no residual.

    **The sweep must be the loop's own map, not the output path's** (ruling
    D25).  The coupling state is not the whole of what a model reads: PROCESS's
    output path permanently changes settings that are not coupling-state
    components and never puts them back, and a sweep taken afterwards then
    evaluates a different function of the same state.  So ``structure_snapshots``
    carries the whole data structure as it stood at the driver's positions, and
    before the sweep this function puts back a **derived** set — the fields that
    differ between the snapshot and the state the sweep would otherwise start
    from, outside the coupling state, whose own restore is governed by the audit
    position.  Derived, never listed: the one field known to latch today is not
    what the mechanism knows about.  What could not be put back is counted and
    named in the record; nothing here reports "all".
    """
    record: dict[str, Any] = {"audit_position": position}
    try:
        from . import data_structure as structure_mod
        from . import predicate as predicate_mod

        spec, provenance = module_solve.load_spec(str(coupling_state_path))
        coupling_names = {spec.name(i) for i in range(len(spec.keys))}
        record["instrument"] = _restore_the_solve_phase_structure(
            data,
            structure_mod=structure_mod,
            structure_snapshots=structure_snapshots,
            restore_from_position=restore_from_position,
            coupling_names=coupling_names,
            audit_position=position,
            coupling_state_is_restored=from_snapshot is not None,
        )
        if from_snapshot is not None:
            restored = predicate_mod.write_entry_state(spec, data, from_snapshot)
            record["restored_from_snapshot"] = restored
            if not restored["readback_bitexact"]:
                record["refused"] = (
                    f"the snapshot taken at {position} did not restore bit for "
                    f"bit ({restored['n_readback_mismatch']} of "
                    f"{restored['n_components']} components differ, first: "
                    f"{restored['readback_mismatch_first'][:3]}); auditing the "
                    f"state that is actually in the data structure would "
                    f"report a residual of a state nobody chose"
                )
                return record
        _census_the_state_the_sweep_starts_from(
            record["instrument"],
            data,
            structure_mod=structure_mod,
            structure_snapshots=structure_snapshots,
            restore_from_position=restore_from_position,
            coupling_names=coupling_names,
        )
        bound = spec.bind(data)
        y_before = spec.read(bound)
        predicate_mode = getattr(module_solve, "PREDICATE_MODE", "frozen")
        if write_state:
            (Path(outdir) / "y_exit.json").write_text(
                json.dumps(
                    predicate_mod.snapshot_record(
                        spec, y_before, predicate_mode=predicate_mode
                    )
                )
            )
            record["exit_state_written_to"] = "y_exit.json"
        nodes_before = caller.NODE_CALLS[0]
        caller.Caller(models, data)._call_models_once(x)
        y_after = spec.read(bound)
        tau = getattr(module_solve, "TAU", 1e-6)

        # --- every declared ruler, as a named block -------------------------
        #
        # The audit is where an arm's achieved accuracy is read.  V4 took it
        # on two rulers, always both, because the mixed one read lower
        # wherever its denominator bound and a half-present pair would report
        # a change of ruler as a gain in accuracy (improvement item 5a's trap
        # (ii)); DR11 removed the second ruler, and the loop below reads the
        # one the coupling-state module declares.  No model call, no sweep.
        rulers: dict[str, Any] = {}
        vectors: dict[str, Any] = {}
        for ruler in ystate_rulers(spec):
            residual_r = spec.residual(y_before, y_after, ruler=ruler)
            keys_r = [spec.name(int(i)) for i in residual_r.idx_c]
            values_r = [float(v) for v in residual_r.scaled]
            restricted_r = None
            excluded_r: set[str] = set()
            if per_run_artifact is not None and node_write_sets_path is not None:
                restricted_r, excluded_r = restricted_audit(
                    per_run_artifact,
                    configuration,
                    node_write_sets_path,
                    keys_r,
                    values_r,
                    tau,
                )
            ratios = residual_r.value_over_scale()
            vectors[ruler] = {
                "scaled_hex": {k: hexf(v) for k, v in zip(keys_r, values_r)},
                "value_over_scale": {
                    k: (None if not _finite(r) else float(r))
                    for k, r in zip(keys_r, ratios)
                },
            }
            # The **summary** goes in the record; the per-component vectors go
            # in audit_residual.json beside it.  Both rulers' vectors together
            # are some 3 400 further leaves per record, which is a file a tally
            # reads and a gate walks value by value -- and the vector is already
            # written, exactly, to its own file.  Which ruler the run's own
            # loops stopped on is stamped ONCE, at exit_audit.predicate_mode;
            # the block's key says which ruler the block is.  It was briefly
            # stamped inside each block as well, and gate G8 caught that as two
            # differing values per pair, which is what a stamp of the setting
            # being varied looks like when it is written twice.
            rulers[ruler] = {
                "ruler": ruler,
                "tau": tau,
                "residual_max": residual_r.max,
                "residual_max_hex": hexf(residual_r.max),
                "brief": residual_r.brief(tau),
                "detail": residual_r.ruler_detail(tau),
                "restricted": restricted_r,
                "n_excluded_from_the_restricted_statistic": len(excluded_r),
                "vector_written_to": "audit_residual.json",
            }

        # The unprefixed fields below are the **frozen** ruler's, unchanged in
        # name, shape and value from every record made before DR5, because a
        # gate compares them value for value and a reproduction gate reads one
        # of them by path.  They are taken from the frozen block above rather
        # than computed a second time, so there is one computation and two
        # presentations of it.
        frozen = rulers[ystate_frozen(spec)]
        residual = spec.residual(y_before, y_after, ruler=ystate_frozen(spec))
        keys = [spec.name(int(i)) for i in residual.idx_c]
        values = [float(v) for v in residual.scaled]
        vector = {
            "components_sha256": provenance.get("components_sha256"),
            "n_components": provenance.get("n_components"),
            "n_continuous_tested": len(keys),
            "tau": tau,
            # The preamble of an artifact this run writes: which ruler the
            # run's own loops stopped on, and which ruler the unprefixed
            # vector below is taken on.  They can differ -- the audit is always
            # published on both -- and a vector that named neither could not be
            # told apart from the other afterwards (item 5a trap (i)).
            "predicate_mode": predicate_mode,
            "vector_ruler": ystate_frozen(spec),
            "rulers": {
                name: {
                    "residual_max_hex": rulers[name]["residual_max_hex"],
                    "n_above": rulers[name]["brief"]["n_above"],
                    "argmax": rulers[name]["brief"]["argmax"],
                    **vectors[name],
                }
                for name in rulers
            },
            "scaled": dict(zip(keys, values)),
            "scaled_hex": {k: hexf(v) for k, v in zip(keys, values)},
            "discrete_mismatch": [
                spec.name(i) for i in residual.mismatch_discrete
            ],
            "moved_constant": [spec.name(i) for i in residual.moved_constant],
            "nan_new": [spec.name(i) for i in residual.nan_new],
        }
        restricted = frozen["restricted"]
        if per_run_artifact is not None and node_write_sets_path is not None:
            _r, excluded_keys = restricted_audit(
                per_run_artifact,
                configuration,
                node_write_sets_path,
                keys,
                values,
                tau,
            )
            vector["excluded_keys"] = sorted(excluded_keys)
        (Path(outdir) / "audit_residual.json").write_text(json.dumps(vector))
        record.update(
            {
                "coupling_state": str(coupling_state_path),
                "components_sha256": provenance.get("components_sha256"),
                "n_components": provenance.get("n_components"),
                "tau_for_the_brief": tau,
                "residual_max": residual.max,
                "residual_max_hex": hexf(residual.max),
                "brief": residual.brief(tau),
                "residual_vector_written_to": "audit_residual.json",
                "restricted": restricted,
                "audit_node_calls": caller.NODE_CALLS[0] - nodes_before,
                "charged_to_the_arm": False,
                "note": (
                    "one further full sweep of the complete model set past "
                    "termination; the identical instrument in every arm; its "
                    "node calls are excluded from the arm's cost, which was "
                    "frozen before it ran"
                ),
            }
        )
        # Both rulers, as named blocks, beside the unprefixed frozen fields
        # above.  The pair is what a residual table reads; a table that shows
        # one column alone is reporting a change of ruler as a change of
        # accuracy.
        record.update(rulers)
        record["predicate_mode"] = predicate_mode
        record["rulers_note"] = (
            "one ruler since DR11: 'frozen' (max|dy_i| / s_i, the measured "
            "scale alone).  The unprefixed residual_max / brief / restricted "
            "fields are the frozen ruler's, kept under their original names "
            "because earlier records carry them there; the per-ruler block "
            "is published under its name so a second ruler, were one ever "
            "declared again, would be all-or-nothing beside it."
        )
    except Exception:  # noqa: BLE001 - recorded, never raised
        record["error"] = traceback.format_exc()
    return record


# --------------------------------------------------------------------------
# PROCESS's own output file
# --------------------------------------------------------------------------

#: Scalar keys the output file carries that a record wants.  Read from a file
#: this tree produced, not from a document.
MFILE_SCALARS: tuple[str, ...] = (
    "ifail",
    "norm_objf",
    "sqsumsq",
    "n_iteration_variables",
    "n_solver_iterations",
    "process_runtime",
    "p_plant_electric_net_mw",
)


def read_mfile(path: Path) -> dict[str, Any]:
    """PROCESS's own output file, parsed: the independent cross-check.

    It is the only source of the optimiser's exit code that does not come from
    the harness's own instrumentation, which is why it is compared as its own
    field.  The **raw ASCII** value is kept beside the parsed float for the
    quantities a bit-comparison uses, so a comparison never passes or fails
    because of a float re-parse.

    Reimplemented here from ``arch_surgery/idf_probe/metrics.py`` at
    ``9a8defa6``: every check this experiment runs is implemented inside this
    package, and nothing is imported from the earlier revisions' machinery.
    """
    from process.core.io.mfile import MFile

    mfile = MFile(str(path))

    def scalar(key):
        try:
            return mfile.data[key].get_scan(-1)
        except Exception:  # noqa: BLE001
            return None

    out: dict[str, Any] = {key: scalar(key) for key in MFILE_SCALARS}
    itvars: dict[str, float] = {}
    names: dict[str, str] = {}
    for i in range(1, 200):
        key = f"itvar{i:03d}"
        if key not in mfile.data:
            break
        itvars[key] = mfile.data[key].get_scan(-1)
        names[key] = getattr(mfile.data[key], "var_description", "")
    out["itvars"] = itvars
    out["itvar_names"] = names
    out["raw"] = _raw_mfile_fields(
        path, ("norm_objf", "sqsumsq", "ifail", *itvars)
    )
    return out


def _raw_mfile_fields(path: Path, keys) -> dict[str, str]:
    """The raw ASCII value field of each ``(key)``-tagged line."""
    wanted = {f"({key})": key for key in keys}
    found: dict[str, str] = {}
    for line in Path(path).read_text(errors="replace").splitlines():
        for tag, key in wanted.items():
            if tag + "_" in line or line.rstrip().endswith(tag):
                index = line.find(tag)
                if index == -1:
                    continue
                rest = line[index + len(tag):].lstrip("_").strip()
                if rest.endswith(" OP"):  # marks an output-only variable
                    rest = rest[:-3].strip()
                found[key] = rest
    return found


def find_mfile(outdir: Path, configuration: str) -> Path | None:
    """The output file this run wrote, by name and then by pattern."""
    named = Path(outdir) / f"{configuration}MFILE.DAT"
    if named.exists():
        return named
    candidates = sorted(Path(outdir).glob("*MFILE.DAT"))
    return candidates[0] if candidates else None


# --------------------------------------------------------------------------
# the record
# --------------------------------------------------------------------------


def open_record(
    *,
    runner: str,
    phase: str,
    arm: str,
    configuration: str,
    seed: int,
    delta: float | None,
    tau: float,
    run_kind: str,
    regime: str,
    predicate_mode: str,
    input_file: Path,
    input_file_kind: str,
    pin_hex: str | None,
    switches_asked: Mapping[str, str],
    test_set: str,
    timers: bool = False,
) -> dict[str, Any]:
    """The identity half of a record, filled before anything runs.

    Filled first so that a run which crashes before it reaches the driver still
    produces a record saying what it was trying to be.  ``test_set`` is the
    campaign-level test set the loops were asked to test (DR11), stamped as
    ``campaign_test_set`` beside the tolerance it was composed with.
    """
    from .. import __version__ as harness_version

    return {
        "record_format": records_mod.FORMAT,
        "harness_version": harness_version,
        "runner": runner,
        "campaign_phase": phase,
        "campaign_arm": arm,
        "campaign_configuration": configuration,
        "campaign_seed": seed,
        "campaign_delta": delta,
        "campaign_tau": tau,
        "campaign_test_set": test_set,
        "campaign_timers": bool(timers),
        "campaign_run_kind": run_kind,
        "campaign_predicate_mode": predicate_mode,
        "campaign_input_file": str(input_file),
        "campaign_input_file_kind": input_file_kind,
        "campaign_pin_hex": pin_hex,
        "regime": regime,
        "switches_asked": dict(switches_asked),
        "python": sys.executable,
        "python_version": sys.version.split()[0],
        "pythonpath": os.environ.get("PYTHONPATH"),
        "env_architecture": architecture_environment(),
    }


def stamp_tree(record: dict[str, Any], tree: Path, process_file: str) -> None:
    """The provenance half: which tree, which commit, and how dirty."""
    record.update(prov.git_stamp(Path(tree)))
    record["tree"] = str(tree)
    record["process_file"] = process_file
    record["process_copy_provenance"] = copy_provenance(Path(tree))
    record["resolved_switches"] = resolved_switches()


def stamp_resources(record: dict[str, Any], usage_before, started: float) -> None:
    """Wall clock and cpu time.  Context, never evidence.

    No conclusion of this experiment rests on a timing: a wall-clock-derived
    weight has been measured moving by half its own size across runs of
    identical code.  They are recorded because a run that takes ten times as
    long as its neighbours is worth looking at, not because anything is decided
    by them.
    """
    usage_after = resource.getrusage(resource.RUSAGE_SELF)
    record["wall_s"] = time.perf_counter() - started
    record["cpu_user_s"] = usage_after.ru_utime - usage_before.ru_utime
    record["cpu_sys_s"] = usage_after.ru_stime - usage_before.ru_stime
    record["cpu_s"] = record["cpu_user_s"] + record["cpu_sys_s"]
    record["maxrss_kb"] = usage_after.ru_maxrss
    try:
        record["loadavg"] = os.getloadavg()
    except OSError:
        record["loadavg"] = None
    record["timing_is_context_not_evidence"] = True


def harvest_timers(caller) -> dict[str, Any] | None:
    """The driver's wall-clock accumulators (DR12), copied, or None when off.

    Read **before** the exit audit runs, as the counters are: the audit's
    sweep goes through the same timed path, and its share is measured
    afterwards as an excluded cost (:func:`stamp_timers`), never charged.
    """
    timers = getattr(caller, "TIMERS", None)
    if not isinstance(timers, dict):
        return None
    copy = json.loads(json.dumps(timers, default=str))
    copy.pop("_solve_t0", None)
    return copy


def stamp_timers(
    record: dict[str, Any],
    *,
    driver_before_audit: dict[str, Any] | None,
    driver_after_audit: dict[str, Any] | None,
    epochs: Mapping[str, Any],
    excluded: Mapping[str, Any],
) -> None:
    """The record's ``timers`` block: the driver's accumulators as they stood
    before the audit, the harness-only costs measured apart (the audit's own
    wall and its share of the driver's timers, the snapshots, the record
    assembly, the set-up before the run), and the epochs.  Null when the
    timers were off.  Context, never evidence (D33)."""
    if driver_before_audit is None:
        record["timers"] = None
        return
    audit_driver = {}
    if driver_after_audit is not None:
        for key in ("sweep_s", "n_sweeps"):
            audit_driver[key] = driver_after_audit.get(key, 0) - driver_before_audit.get(key, 0)
        audit_driver["node_s"] = sum(driver_after_audit.get("node_s", {}).values()) - sum(
            driver_before_audit.get("node_s", {}).values()
        )
    record["timers"] = {
        "enabled": True,
        "driver": driver_before_audit,
        "excluded": {
            **dict(excluded),
            "exit_audit_driver_sweep_s": audit_driver.get("sweep_s"),
            "exit_audit_driver_node_s": audit_driver.get("node_s"),
            "exit_audit_driver_n_sweeps": audit_driver.get("n_sweeps"),
        },
        "epochs": dict(epochs),
        "what": (
            "DR12 (A101): 'driver' is process.core.caller.TIMERS as it stood "
            "when the counters were harvested, before the audit; 'excluded' "
            "names the harness-only costs measured apart (the exit-audit "
            "sweep's wall and its share of the driver's timers, the state "
            "snapshots, the record assembly, the harness's set-up before the "
            "run; the census hooks are not timed and read null); 'epochs' are "
            "time.time() stamps the launcher's spawn time is compared with.  "
            "Context, never evidence (D33)"
        ),
    }


def stamp_driver_counters_null(record: dict[str, Any], *, phase: str) -> None:
    """The driver-counter fields, present with an explicit null before the run.

    Never absent: a reader of a record must be able to tell "this run did not
    get far enough to have one" from "the harness forgot to write it down".
    Every field here is filled after the run from the driver's own counters
    (:func:`harvest_attempt_stamps`, :func:`harvest_predicate_counters`,
    :func:`harvest_output_path`); a record that still carries the null is a
    record of a run that crashed or was refused before the driver produced one.
    The next driver counter the plan asks for is stamped here in the same way.

    *Was ``stamp_capabilities_absent``*: named when some of these counters were
    driver capabilities the tree did not yet supply (before A57, A58 and A60),
    and kept under that name with the allowance for a *pending* switch until
    A72 retired the allowance (survey item B4).  Renamed for what it does by
    A73, the child-side remainder of that retirement.
    """
    # Filled from the driver's own attempt-boundary stamps after the run
    # (:func:`harvest_attempt_stamps`).  Present here with a null so that a
    # record of a run that never reached the driver still carries the key.
    record["attempt_accounting"] = None
    # Filled from the driver's own counters after the run
    # (:func:`harvest_predicate_counters`).  Present here with a null so that a
    # record of a run that never reached the driver still carries the key.
    record["predicate_evaluations"] = None
    record["components_compared"] = None
    record["block_visits"] = None
    record["empty_block_visits"] = None
    record["empty_block_sweeps"] = None
    record["dispatch_sweeps"] = None
    record["upstream_predicate_evaluations"] = None
    record["upstream_components_compared"] = None
    record["predicate_counters"] = None
    # Filled from the driver's own stamp after the run (:func:`harvest_counters`,
    # DR11).  Null here and null after a run with every switch unset.
    record["loop_test_sets"] = None
    if phase == "B":
        # Filled from the driver's own counters after the run
        # (:func:`harvest_output_path`).  Present here with a null so that a
        # record of a run that never reached the driver still carries the key.
        record["output_path"] = None
        record["output_loop_sweeps"] = None
        record["output_path_entries"] = None


def write_record(outdir: Path, record: Mapping[str, Any]) -> Path:
    """The record, written where the pool will read it."""
    path = Path(outdir) / "metrics.json"
    path.write_text(json.dumps(record, indent=2, default=str))
    return path


def print_brief(record: Mapping[str, Any], *, drop: tuple[str, ...]) -> None:
    """A short form on stdout, so a live run is readable in the log."""
    brief = {k: v for k, v in record.items() if k not in drop}
    print(json.dumps(brief, indent=2, default=str))


def banner(record: Mapping[str, Any]) -> None:
    """Print the provenance, so a wrong tree is visible immediately."""
    print("-" * 68)
    print(prov.banner(record))
    print("-" * 68, flush=True)
