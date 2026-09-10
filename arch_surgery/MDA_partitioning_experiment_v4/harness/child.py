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
import os
import resource
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Mapping

from . import provenance as prov
from . import records as records_mod
from . import switches as switches_mod


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
    sweeps_cell = getattr(caller, "_SWEEP_CALLS", None)

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
            "n_prime_calls": (
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
        "n_prime_calls": getattr(caller, "ARRANGEMENT_METHOD_CALLS", [None])[0],
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
        totals = dict(totals)
        totals["moved_constants"] = sorted(totals.get("moved_constants", ()))
        out["module_solve_totals"] = totals
    else:
        out["module_solve_totals"] = None
    per_run = getattr(caller, "DEFER_PER_RUN_TOTALS", None)
    out["post_solve_totals"] = (
        dict(per_run)
        if (per_run is not None and getattr(caller, "DEFER_PER_RUN_ENABLED", False))
        else None
    )
    _ = module_solve
    return out


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
) -> dict[str, Any]:
    """One further full sweep past termination, and how far the state moved.

    The same instrument in every arm — a fresh caller with nothing deferred and
    no block filter — which is what makes "compare at matched achieved accuracy"
    mean anything.  Its own model calls are recorded and **never charged** to
    the arm.  The sweep mutates the state, so the exit state is written out
    first and nothing may run after it.
    """
    record: dict[str, Any] = {"audit_position": position}
    try:
        from . import predicate as predicate_mod

        spec, provenance = module_solve.load_spec(str(coupling_state_path))
        bound = spec.bind(data)
        y_before = spec.read(bound)
        if write_state:
            (Path(outdir) / "y_exit.json").write_text(
                json.dumps(predicate_mod.snapshot_record(spec, y_before))
            )
            record["exit_state_written_to"] = "y_exit.json"
        nodes_before = caller.NODE_CALLS[0]
        caller.Caller(models, data)._call_models_once(x)
        y_after = spec.read(bound)
        residual = spec.residual(y_before, y_after)
        tau = getattr(module_solve, "TAU", 1e-6)
        keys = [spec.name(int(i)) for i in residual.idx_c]
        values = [float(v) for v in residual.scaled]
        vector = {
            "components_sha256": provenance.get("components_sha256"),
            "n_components": provenance.get("n_components"),
            "n_continuous_tested": len(keys),
            "tau": tau,
            "scaled": dict(zip(keys, values)),
            "scaled_hex": {k: hexf(v) for k, v in zip(keys, values)},
            "discrete_mismatch": [
                spec.name(i) for i in residual.mismatch_discrete
            ],
            "moved_constant": [spec.name(i) for i in residual.moved_constant],
            "nan_new": [spec.name(i) for i in residual.nan_new],
        }
        restricted = None
        if per_run_artifact is not None and node_write_sets_path is not None:
            restricted, excluded_keys = restricted_audit(
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
    pending_switches_allowed: list[str],
    switches_asked: Mapping[str, str],
) -> dict[str, Any]:
    """The identity half of a record, filled before anything runs.

    Filled first so that a run which crashes before it reaches the driver still
    produces a record saying what it was trying to be.
    """
    from . import __version__ as harness_version

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
        "campaign_run_kind": run_kind,
        "campaign_predicate_mode": predicate_mode,
        "campaign_input_file": str(input_file),
        "campaign_input_file_kind": input_file_kind,
        "campaign_pin_hex": pin_hex,
        "regime": regime,
        "pending_switches_allowed": list(pending_switches_allowed),
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


def stamp_capabilities_absent(record: dict[str, Any], *, phase: str) -> None:
    """The fields the plan declares that this tree cannot yet supply.

    Present with an explicit null and the reason, never absent: a reader of a
    record must be able to tell "the driver does not count this yet" from "the
    harness forgot to write it down".  Each names the approved driver change
    that will fill it in.
    """
    record["predicate_evaluations"] = None
    record["components_compared"] = None
    record["predicate_counters_null_because"] = (
        "the driver does not count predicate evaluations or components "
        "compared; approved driver change DR4, task A58 "
        "(driver-predicate-counters)"
    )
    if phase == "B":
        record["output_path"] = "mda_output"
        record["output_loop_sweeps"] = None
        record["output_loop_null_because"] = (
            "this tree has one output path — upstream's own output-time loop — "
            "and does not count its sweeps separately; the switch that selects "
            "the other path and the counter are approved driver change DR2, "
            "task A57 (driver-output-path)"
        )


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
