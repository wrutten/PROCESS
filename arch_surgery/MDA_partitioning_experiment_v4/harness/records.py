"""The run record: its schema, its completeness contract, and its refusals.

Derived from the record ``arch_surgery/idf_probe/run_one.py`` and
``arch_surgery/idf_probe/v2_eval_one.py`` write, and from the completeness
check of ``arch_surgery/MDA_partitioning_experiment_v3/phase_b.py`` (the
previous revision's gate G7), all read at ``9a8defa6``; task **A50
(harness-run)**.  The harness implementation plan's §4.4 is the change list
against that record and §11.1 fixes the names.

Why a schema module at all
--------------------------
The previous revision's two run drivers each built a dict of about ninety keys
inline, and the check that a finished run carried what the summary needed lived
in a third file.  A field could therefore be dropped from one driver and not the
other, and the omission would surface as a missing column in a table months
later.  Here the field list is **data**, both entry points fill it, and one
function refuses a record that does not carry what it declares.

Three refusals live here, and none of them is a warning:

``assert_complete``
    a finished record missing a declared field.  A summary computed over
    records that are missing different fields is a summary over a population
    nobody can state (trap T11).

``assert_attempt_summation``
    per-attempt costs that do not add up to the run total they decompose.  The
    optimiser retries, and the published cost ratio is quoted **with and
    without** retried seeds; if the parts do not sum to the whole, that ratio is
    computed over quantities that do not decompose the published one, which is
    worse than having no per-attempt figures at all.  The driver does not
    supply per-attempt node calls yet — that is approved driver change DR7,
    task **A60 (driver-attempts)** — so today the check refuses only when the
    numbers are **present**, and its tooth is a synthetic record that carries
    them and gets them wrong.

``assert_run_kind``
    a record that does not say what kind of run made it.  A gate run and a
    campaign run look identical afterwards, and one of them is not a
    measurement.

Vocabulary, once: a **configuration** is one optimisation problem; an **arm** is
one setting of the driver's switches; a **seed** selects which displaced
starting point is used, and seed 0 is the undisplaced one; a **regime** says how
the starting point is displaced; the **coupling state** is the set of state
fields the in-loop models write, and the **audit** is one further full sweep
past termination that measures how far it still moves.  A **predicate** is the
convergence test a loop stops on, and there are two of them in this experiment:
the coupling-state one the flat and partitioned arrangements use, and upstream's
own test on the objective and the constraint vector.  A record counts both,
separately, because an arm runs exactly one of them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

#: Schema tag.  Bumped when a field is added, renamed or dropped, so a reader
#: that expected the old shape says so instead of finding ``None``.
FORMAT = "run-record-1"

#: What kind of run made this record.  ``campaign`` is a measurement; the other
#: three are not, and nothing may pool them with one.
RUN_KINDS: tuple[str, ...] = ("campaign", "gate", "smoke", "reference")

#: How a run ended.  ``unconverged-at-cap`` is separate from ``unconverged``
#: on purpose: upstream's own analysis loop raises after ten passes, and a
#: displaced entry may reach that cap.  That is a **finding about the shipped
#: code**, not a broken run — and ``machinery`` is the row for a broken one,
#: separate again, because the two were confused once and a machinery failure
#: was published as "the reference arm did not converge".
FAILURE_CLASSES: tuple[str, ...] = (
    "ok",
    "crashed",
    "refused",
    "unconverged",
    "unconverged-at-cap",
    "infeasible-at-audit",
    "machinery",
    "timeout",
    "no_record",
)

#: How the starting point of one run is displaced.
REGIMES: tuple[str, ...] = ("unperturbed", "perturbed", "stencil")

#: Where the exit audit's sweep is taken.  It is recorded per run because a
#: residual table whose arms were audited at different points, without saying
#: so, is the thing that must not happen (EXPERIMENT_PLAN.md §3.3).
#:
#: ``after_single_evaluation`` is the evaluation phase's position: that phase
#: runs one evaluation and never reaches the output path, so its audit is taken
#: at the state the evaluation terminated in.
#:
#: ``entry_to_write_output_files`` is the optimisation phase's position and the
#: one the plan declares: the state the solve handed over, before the per-run
#: deferred nodes and before any output-time sweep.  It is reached by a
#: **snapshot** — see :data:`AUDIT_POSITION_HOW`.
#:
#: ``after_run`` is where the previous revision audited: after the run has
#: finished, which is after the output path.  It survives for exactly one
#: caller — see :data:`AUDIT_POSITION_AFTER_RUN_WHY`.
AUDIT_POSITIONS: tuple[str, ...] = (
    "after_single_evaluation",
    "after_run",
    "entry_to_write_output_files",
)

#: Positions an optimisation run may audit at.  The declared one is the
#: default; the other is the reproduction gate's, and nothing else may ask for
#: it.
OPTIMISATION_AUDIT_POSITIONS: tuple[str, ...] = (
    "entry_to_write_output_files",
    "after_run",
)

#: How the declared position is reached, quoted into every record that uses it.
#: The audit sweep mutates the state it measures, so it cannot be *run* at the
#: entry to the output path without handing that path a state the optimiser
#: never accepted — the output files, the exit code and the total node count
#: would all be of the audited state.  The driver therefore **snapshots** the
#: coupling state there (task A57 (driver-output-path); experiment plan §3.3)
#: and the residual is computed after the run, from the restored snapshot, by
#: the same one-sweep instrument every arm gets.
AUDIT_POSITION_HOW = (
    "the driver snapshots the coupling state at the entry to "
    "write_output_files — before the per-run deferred nodes and before any "
    "output-time sweep — and this run computed the residual afterwards, from "
    "that snapshot restored into the data structure, with the same one-sweep "
    "instrument every arm gets.  The restore is proved bit-exact component by "
    "component before the sweep runs; a restore that is not bit-exact refuses "
    "the audit rather than reporting a residual of a state nobody chose.  The "
    "audit's own model calls are counted and never charged to the arm, and the "
    "per-run deferred nodes' own components stay excluded from the restricted "
    "statistic exactly as before."
)

#: Why ``after_run`` still exists, and the only thing that may ask for it.
#: The reproduction gate reproduces the **previous revision**, which audited
#: after the run; its recorded ``exit_audit.residual_max_hex`` values are among
#: the values that gate compares, so reproducing them means auditing where they
#: were audited.  Every campaign record uses the declared position.
AUDIT_POSITION_AFTER_RUN_WHY = (
    "the reproduction gate reproduces the previous revision's records, and "
    "that revision audited after the run — its residual is one of the values "
    "the gate compares bit for bit, so reproducing it means taking the audit "
    "where it was taken.  This position is refused outside that gate: it is "
    "recorded per run and stamped in the gate's own record as a reproduction "
    "override."
)


class RecordError(RuntimeError):
    """A refused record.  Never downgraded into a warning."""


# --------------------------------------------------------------------------
# resolving a dotted field path
# --------------------------------------------------------------------------


def resolve_path(record: Mapping[str, Any], path: str) -> Any:
    """The value at dotted *path*, or :class:`KeyError` naming what is missing.

    ``attempts[].n_solver_iterations`` maps over a list and takes the named key
    from each element, so a per-attempt column is one field rather than a
    variable number of them.  This is the one implementation: the reproduction
    reference reads its records through it too, so a path that resolves for the
    gate resolves identically for the reference it is compared against.
    """
    cursor: Any = record
    walked: list[str] = []
    for step in path.split("."):
        if step.endswith("[]"):
            name = step[:-2]
            if not isinstance(cursor, Mapping) or name not in cursor:
                raise KeyError(".".join([*walked, name]))
            cursor = cursor[name]
            if not isinstance(cursor, list):
                raise KeyError(".".join([*walked, name]) + " (not a list)")
            walked.append(step)
            continue
        if walked and walked[-1].endswith("[]"):
            values = []
            for index, element in enumerate(cursor):
                if not isinstance(element, Mapping) or step not in element:
                    raise KeyError(".".join([*walked, f"[{index}]", step]))
                values.append(element[step])
            walked.append(step)
            cursor = values
            continue
        if not isinstance(cursor, Mapping) or step not in cursor:
            raise KeyError(".".join([*walked, step]))
        cursor = cursor[step]
        walked.append(step)
    return cursor


def has_path(record: Mapping[str, Any], path: str) -> bool:
    """Whether *path* resolves at all.  Present-but-null counts as present."""
    try:
        resolve_path(record, path)
    except KeyError:
        return False
    return True


# --------------------------------------------------------------------------
# the declared field list
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Field:
    """One declared field of the record."""

    #: Dotted path into the record.
    name: str
    #: Phases that must carry it: "A" (one evaluation), "B" (one optimisation).
    phases: tuple[str, ...]
    #: "always" — every record, whatever happened; "finished" — only a record
    #: whose status is ok, because the quantity does not exist otherwise.
    when: str
    #: One line: what the field is, for a reader who has not read the plan.
    why: str


def _f(name: str, phases: str, when: str, why: str) -> Field:
    return Field(name, tuple(phases), when, why)


#: The schema.  Order is the order a reader wants it in: what was run, where it
#: ran, what the driver resolved, how it ended, what it cost, what it achieved.
SCHEMA: tuple[Field, ...] = (
    # --- what was run --------------------------------------------------
    _f("record_format", "AB", "always", "schema tag of this record"),
    _f("harness_version", "AB", "always", "which harness wrote it"),
    _f("runner", "AB", "always", "which entry point wrote it"),
    _f("campaign_phase", "AB", "always", "A: one evaluation; B: one optimisation"),
    _f("campaign_arm", "AB", "always", "the arm: one setting of the switches"),
    _f("campaign_configuration", "AB", "always", "the optimisation problem"),
    _f("campaign_seed", "AB", "always", "which displaced start; 0 is undisplaced"),
    _f("campaign_delta", "AB", "always", "displacement size, null at a stencil point"),
    _f("campaign_tau", "AB", "always", "the one tolerance every converger uses"),
    _f("campaign_run_kind", "AB", "always", "campaign | gate | smoke | reference"),
    _f("campaign_predicate_mode", "AB", "always", "which denominator the test scales by"),
    _f("campaign_input_file", "AB", "always", "the input file actually read"),
    _f("campaign_input_file_kind", "AB", "always", "committed or lifted"),
    _f("campaign_pin_hex", "AB", "always", "the constant that owns the burn time, or null"),
    _f("regime", "AB", "always", "unperturbed | perturbed | stencil"),
    # --- where it ran ---------------------------------------------------
    _f("tree", "AB", "always", "the tree whose driver ran"),
    _f("tree_git_head", "AB", "always", "its commit"),
    _f("tree_git_branch", "AB", "always", "its branch"),
    _f("tree_git_describe", "AB", "always", "git describe of that commit"),
    _f("tree_modified_tracked", "AB", "always", "tracked modifications: the kind that can move a measurement"),
    _f("tree_modified_tracked_n", "AB", "always", "how many of them"),
    _f("tree_untracked_paths", "AB", "always", "untracked paths: context, and no dirt"),
    _f("tree_untracked_paths_n", "AB", "always", "how many of them"),
    _f("tree_git_dirty", "AB", "always", "derived from the tracked half only"),
    _f("tree_contains_base_commit", "AB", "always", "whether the tree descends from the base commit"),
    _f("base_commit", "AB", "always", "the experiment's base commit"),
    _f("process_file", "AB", "always", "the imported package's own file: the exact-tree evidence"),
    _f("python", "AB", "always", "the interpreter"),
    _f("python_version", "AB", "always", "its version"),
    _f("pythonpath", "AB", "always", "what made the tree importable"),
    _f("process_copy_provenance", "AB", "always", "the identity of the copied driver"),
    # --- what the driver resolved ---------------------------------------
    _f("env_architecture", "AB", "always", "every known switch variable and its value, or null"),
    _f("switches_asked", "AB", "always", "what the arm asked for, term by term"),
    _f("resolved_switches", "AB", "always", "what the driver resolved, read back from the imported modules"),
    _f("pending_switches_allowed", "AB", "always", "switches this tree does not implement that this run was allowed to omit"),
    # --- how it ended -----------------------------------------------------
    _f("status", "AB", "always", "the run's own word for how it ended"),
    _f("failure_class", "AB", "always", "the taxonomy row"),
    _f("wall_s", "AB", "always", "wall clock: context, never evidence"),
    _f("cpu_s", "AB", "always", "cpu time: a contention diagnostic"),
    _f("maxrss_kb", "AB", "always", "peak resident memory"),
    _f("loadavg", "AB", "always", "machine load while it ran"),
    # --- the audit --------------------------------------------------------
    _f("audit_position", "AB", "always", "where the audit sweep was taken"),
    _f("audit_position_declared", "AB", "always", "where the plan declares it should be taken"),
    _f("audit_snapshot", "B", "always", "the driver's snapshots of the coupling state on the output path, or why there are none"),
    _f("exit_audit", "AB", "always", "the achieved accuracy: one further full sweep, uncharged"),
    # --- counters common to both phases -----------------------------------
    _f("node_calls_total", "AB", "always", "model executions, the whole run"),
    _f("n_prime_calls", "AB", "always", "executions of the run-constant geometry method; stamped, never pooled"),
    _f("module_solve_totals", "AB", "finished", "the block solver's own totals"),
    _f("post_solve_totals", "AB", "always", "the per-run deferral's own counts, or null when it is off"),
    _f("node_census", "AB", "always", "model executions per node name"),
    _f("exit_forensics", "AB", "always", "the five fields recorded at every exit"),
    _f("attempts", "AB", "always", "one entry per optimiser attempt, in order"),
    _f("attempts_node_calls_available", "AB", "always", "whether the driver supplies per-attempt node calls yet"),
    # --- the output path --------------------------------------------------
    _f("output_path", "B", "always", "which output path ran: mda_output | finalise_once"),
    _f("output_loop_sweeps", "B", "always", "sweeps the output-time loop ran; 0 under the finalise-once path"),
    _f("output_path_entries", "B", "always", "entries to the output path: one per scan point"),
    # --- how this run differed from the campaign, if it did ---------------
    _f("reproduction_overrides", "AB", "always", "what the reproduction gate set differently, or null for a run that is not that gate's"),
    # --- what the convergence tests cost -----------------------------------
    _f("predicate_evaluations", "AB", "always", "evaluations of the coupling-state convergence test in the solve phase"),
    _f("components_compared", "AB", "always", "components those evaluations walked, summed"),
    _f("block_visits", "AB", "always", "visits the block schedule made to each block, per block"),
    _f("empty_block_visits", "AB", "always", "of those, the visits that executed no node: counted and disclaimed, never repaired"),
    _f("empty_block_sweeps", "AB", "always", "sweeps of the model sequence spent inside those empty visits: what they actually cost"),
    _f("dispatch_sweeps", "AB", "always", "sweeps of the dispatch body over the whole run, every path included"),
    _f("upstream_predicate_evaluations", "AB", "always", "evaluations of upstream's own stopping test in the solve phase"),
    _f("upstream_components_compared", "AB", "always", "values those tests actually compared, summed: the pair short-circuits"),
    _f("predicate_counters", "AB", "always", "the two predicates' counts split out, with the mean test width and the empty-visit share"),
    # --- the optimisation phase ------------------------------------------
    _f("node_calls_solve_phase", "B", "finished", "model executions during the solve: the cost unit"),
    _f("n_model_calls", "B", "finished", "evaluations of the model set the optimiser asked for"),
    _f("n_solver_iterations", "B", "finished", "the optimiser's iterations on its final attempt"),
    _f("sweeps_per_eval", "B", "finished", "sweeps per evaluation, binned"),
    _f("first_call_models", "B", "finished", "the first evaluation's own counts and objective"),
    _f("nvar", "B", "finished", "design-vector length"),
    _f("n_constraints", "B", "finished", "constraints"),
    _f("epsfcn_final", "B", "finished", "the finite-difference step at exit"),
    _f("i_figure_merit", "B", "finished", "the figure of merit the input file names"),
    _f("values", "B", "finished", "the optimum, as decimals"),
    _f("exact", "B", "finished", "the optimum, as hex floats: what a bit-comparison compares"),
    _f("mfile", "B", "finished", "PROCESS's own output file, the independent cross-check"),
    _f("constraint_93", "B", "finished", "the burn-time consistency residual, or null where the input file does not name it"),
    # --- the evaluation phase ---------------------------------------------
    _f("node_calls_single_eval", "A", "finished", "model executions of the one measured evaluation"),
    _f("n_model_calls_sweeps", "A", "finished", "sweeps the one evaluation took"),
    _f("epsfcn", "A", "always", "the input file's own finite-difference step"),
    _f("x_fd", "A", "always", "the stencil point entered, or null in the displacement regime"),
    _f("entry_state", "A", "always", "the snapshot this evaluation was entered from, or null"),
    _f("perturbation", "A", "always", "the displacement applied, or its recorded absence"),
    _f("spec_keys_owned_by_x", "A", "always", "components the design vector rewrites at every sweep head"),
    _f("t_plant_pulse_burn", "A", "finished", "the burn time at exit"),
    _f("t_plant_pulse_burn_hex", "A", "finished", "the same, as a hex float"),
    _f("lift_residual", "A", "finished", "the lifted component's inconsistency at exit"),
    _f("exact", "A", "finished", "the objective at exit, as a hex float"),
)


#: The completeness contract the previous revision's gate G7 bound on: a
#: finished record missing any of these makes a summary refuse.  They are named
#: separately from the schema because they are the ones whose absence made a
#: whole class of failed runs vanish from a tally silently.
CONTRACT: dict[str, tuple[str, ...]] = {
    "B": (
        "n_solver_iterations",
        "mfile.ifail",
        "exit_forensics.ladder_stage",
        "exit_forensics.constraint_residual_vector",
        "exit_forensics.active_set",
        "exit_forensics.n_attempts",
    ),
    "A": (
        "exit_forensics.constraint_residual_vector",
        "exit_forensics.active_set",
        "exit_forensics.n_attempts",
    ),
}


def fields_for(phase: str, *, finished: bool) -> tuple[Field, ...]:
    """The fields a record of this phase must carry."""
    return tuple(
        field
        for field in SCHEMA
        if phase in field.phases and (finished or field.when == "always")
    )


# --------------------------------------------------------------------------
# the refusals
# --------------------------------------------------------------------------


def assert_run_kind(record: Mapping[str, Any]) -> None:
    """Refuse a record that does not say what kind of run made it."""
    kind = record.get("campaign_run_kind")
    if kind not in RUN_KINDS:
        raise RecordError(
            f"campaign_run_kind is {kind!r}, not one of {RUN_KINDS}.  A gate "
            f"run and a campaign run are indistinguishable afterwards, and "
            f"one of them is not a measurement."
        )
    failure = record.get("failure_class")
    if failure not in FAILURE_CLASSES:
        raise RecordError(
            f"failure_class is {failure!r}, not one of {FAILURE_CLASSES}"
        )


def missing_fields(record: Mapping[str, Any]) -> list[str]:
    """Declared fields this record does not carry.  Null counts as carried."""
    phase = record.get("campaign_phase")
    if phase not in ("A", "B"):
        raise RecordError(
            f"campaign_phase is {phase!r}: the record does not say which phase "
            f"it belongs to, so there is no field list to check it against"
        )
    finished = record.get("status") == "ok"
    absent = [
        field.name
        for field in fields_for(phase, finished=finished)
        if not has_path(record, field.name)
    ]
    if finished:
        absent += [
            path
            for path in CONTRACT[phase]
            if path not in absent and not has_path(record, path)
        ]
    return absent


def assert_complete(record: Mapping[str, Any], *, where: str = "") -> None:
    """Refuse a record missing a declared field.

    A field that is *present and null* is complete: "the optimiser did not run,
    and here is the null that says so" is information, and "the key is not
    there" is not.
    """
    assert_run_kind(record)
    absent = missing_fields(record)
    if absent:
        raise RecordError(
            f"incomplete record{' for ' + where if where else ''}: "
            f"{len(absent)} declared field(s) missing — {', '.join(absent)}.  "
            f"A summary computed over records missing different fields is a "
            f"summary over a population nobody can state."
        )


def assert_attempt_summation(record: Mapping[str, Any], *, where: str = "") -> None:
    """Refuse per-attempt costs that do not sum to the run total.

    The driver does not stamp node calls per attempt yet (approved driver
    change DR7, task A60 (driver-attempts)), so every attempt carries
    ``node_calls_solve_phase: null`` and this check has nothing to add up.  The
    moment it does, the sum must equal ``node_calls_solve_phase`` — per-attempt
    accounting whose parts do not add up to the whole it decomposes is worse
    than none, because the cost ratio published *with and without* retried
    seeds would then be computed over quantities that do not decompose the
    published one.
    """
    attempts = record.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        return
    per_attempt = [a.get("node_calls_solve_phase") for a in attempts]
    if any(value is None for value in per_attempt):
        if all(value is None for value in per_attempt):
            return
        raise RecordError(
            f"partial per-attempt node calls{' for ' + where if where else ''}: "
            f"{sum(1 for v in per_attempt if v is not None)} of "
            f"{len(per_attempt)} attempts carry a count.  Either the driver "
            f"stamps them at every attempt boundary or at none; a partial "
            f"decomposition cannot be summed."
        )
    total = record.get("node_calls_solve_phase")
    if total is None:
        raise RecordError(
            f"per-attempt node calls without a run total"
            f"{' for ' + where if where else ''}: there is nothing for them to "
            f"decompose."
        )
    summed = sum(int(v) for v in per_attempt)
    if summed != int(total):
        raise RecordError(
            f"per-attempt node calls do not sum to the run total"
            f"{' for ' + where if where else ''}: "
            f"{' + '.join(str(int(v)) for v in per_attempt)} = {summed}, "
            f"node_calls_solve_phase = {int(total)}.  REFUSED: the cost ratio "
            f"published with and without retried seeds would be computed over "
            f"quantities that do not decompose the published one."
        )


def assert_usable(record: Mapping[str, Any], *, where: str = "") -> None:
    """Every refusal, in one call.  What a reader of records goes through."""
    assert_complete(record, where=where)
    assert_attempt_summation(record, where=where)


# --------------------------------------------------------------------------
# building and reading
# --------------------------------------------------------------------------


def attempts_from_forensics(
    forensics: Mapping[str, Any], *, node_calls_solve_phase: int | None
) -> list[dict[str, Any]]:
    """The per-attempt list of harness plan §4.4, from what the driver gives.

    The solver-owned half — the ladder stage, the finite-difference step, the
    iteration count and the exit code — is recorded by the harness's own wrap of
    every solver's ``solve``.  The cost half is the driver's and does not exist
    yet: ``node_calls_solve_phase`` and ``sweeps`` are explicit nulls naming the
    change that will supply them, never absent keys.
    """
    out: list[dict[str, Any]] = []
    for attempt in forensics.get("attempts") or []:
        out.append(
            {
                "attempt": attempt.get("attempt"),
                "stage": attempt.get("ladder_stage_positional"),
                "epsfcn": attempt.get("epsfcn_at_entry"),
                "n_iterations": attempt.get("n_solver_iterations"),
                "ifail": attempt.get("ifail"),
                "raised": attempt.get("raised"),
                "node_calls_solve_phase": None,
                "sweeps": None,
                "cost_null_because": (
                    "the driver stamps node calls and the sweep histogram at "
                    "the end of the run, not at each retry boundary; approved "
                    "driver change DR7, task A60 (driver-attempts)"
                ),
            }
        )
    _ = node_calls_solve_phase  # kept in the signature: A60 fills it in here
    return out


def read(outdir: Path | str) -> dict[str, Any]:
    """One record from a run directory.  An absent one is a record, not a gap.

    A directory with no record is reported as ``no_record`` rather than raising:
    a crashed subprocess that wrote nothing is a taxonomy row, and turning it
    into an exception is how a whole class of failures once left a tally
    silently.
    """
    path = Path(outdir) / "metrics.json"
    if not path.exists():
        return {
            "status": "no_record",
            "failure_class": "machinery",
            "record_path": str(path),
            "why": "the run wrote no record; the subprocess did not reach the write",
        }
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return {
            "status": "no_record",
            "failure_class": "machinery",
            "record_path": str(path),
            "why": f"the record is not readable JSON: {exc}",
        }


def is_complete_for(
    record: Mapping[str, Any],
    *,
    arm: str,
    configuration: str,
    seed: int,
    phase: str,
    regime: str,
) -> bool:
    """Whether *record* is a finished record of exactly this job.

    What ``resume`` consults.  A directory is never evidence of a completed
    run: an interrupted one leaves a directory behind, and re-using it would
    put a half-written record into a population.
    """
    if record.get("status") != "ok":
        return False
    for key, value in (
        ("campaign_arm", arm),
        ("campaign_configuration", configuration),
        ("campaign_seed", seed),
        ("campaign_phase", phase),
        ("regime", regime),
    ):
        if record.get(key) != value:
            return False
    return not missing_fields(record)


def summarise(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Counts by taxonomy row, with the denominator beside them."""
    by_class: dict[str, int] = {}
    for record in records:
        row = record.get("failure_class") or "unknown"
        by_class[row] = by_class.get(row, 0) + 1
    return {
        "n_records": len(records),
        "by_failure_class": dict(sorted(by_class.items())),
        "population": f"{len(records)} record(s)",
    }


def declared_field_names(phase: str) -> tuple[str, ...]:
    """Every field name declared for a phase, finished or not."""
    return tuple(field.name for field in SCHEMA if phase in field.phases)


def schema_table() -> Iterable[tuple[str, str, str, str]]:
    """The schema as rows, for the README and the report."""
    for field in SCHEMA:
        yield field.name, "".join(field.phases), field.when, field.why
