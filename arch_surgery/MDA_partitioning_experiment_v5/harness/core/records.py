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

Six refusals live here, and none of them is a warning:

``assert_complete``
    a finished record missing a declared field.  A summary computed over
    records that are missing different fields is a summary over a population
    nobody can state (trap T11).

``assert_attempt_summation``
    per-attempt costs that do not add up to the run total they decompose.  The
    optimiser retries, and the published cost ratio is quoted **with and
    without** retried seeds; if the parts do not sum to the whole, that ratio is
    computed over quantities that do not decompose the published one, which is
    worse than having no per-attempt figures at all.  The driver stamps its
    cost counters at every attempt boundary of the retry ladder (driver change
    DR7, task **A60 (driver-attempts)**), so the check runs against real
    numbers on every optimisation record — node calls and sweeps alike — and
    its tooth is a synthetic record whose parts are made not to add up.

``assert_sweep_decomposition``
    a finished record whose sweep total does not decompose into the parts that
    claim it: ``dispatch_sweeps = loop sweeps + output-time loop sweeps + the
    one sweep the per-run deferral spends at the output path``.  A sweep total
    nobody can decompose is a total nobody can attribute.  The identity was
    the ``predicate_counters`` measurement stage's one unique construction
    (task **A58 (driver-predicate-counters)**); when that stage was retired the
    identity moved here, beside the attempt summation it is the same shape as,
    so that it is asserted by the contract rather than printed by a stage.

``assert_run_kind``
    a record that does not say what kind of run made it.  A gate run and a
    campaign run look identical afterwards, and one of them is not a
    measurement.

``translate_recorded_arm_names`` (inside :func:`read`)
    a record naming an arm neither the matrix nor the recorded-name table
    knows.  The arms were renamed on 2026-09-15 and the records were not
    re-made, so a record's arm name is the name at the time of the run; the
    one table :data:`RECORDED_ARM_NAMES` is applied where the record is read,
    and a name nobody declared is refused there rather than kept under a
    guess or dropped from a population without a word.

``assert_audit_ruler``
    a finished record whose exit audit names no convergence ruler, or not
    every declared one.  While the audit was taken on two rulers (V4, driver
    change DR5, task A59 (driver-predicate-mode)) the pair was all-or-nothing,
    because the ``mixed`` one reads lower wherever its denominator binds and a
    table built from half-present pairs would show a change of ruler as a
    change of accuracy; since driver change DR11 (A100 (v5-test-set)) there
    is one ruler and the check keeps its shape.

Vocabulary, once: a **configuration** is one optimisation problem; an **arm** is
one setting of the driver's switches; a **seed** selects which displaced
starting point is used, and seed 0 is the undisplaced one; a **regime** says how
the starting point is displaced; the **coupling state** is the set of state
fields the in-loop models write, and the **audit** is one further full sweep
past termination that measures how far it still moves.  A **predicate** is the
convergence test a loop stops on, and there are two of them in this experiment:
the coupling-state one the flat and partitioned arrangements use, and upstream's
own test on the objective and the constraint vector.  A record counts both,
separately, because an arm runs exactly one of them.  A **ruler** is what the
coupling-state predicate divides a step by before comparing it with the
tolerance: ``frozen``, a scale measured once over a harvest of design points, or
``mixed``, that scale kept as a floor under the state's current magnitude ---
removed by DR11, so that since then there is one ruler.  A record says which
ruler its run stopped on and reports the exit audit on every declared one.
A **test set** is which components of the coupling state a block loop tests
(DR11): the block's whole write set (V4's predicate, the fallback of D39) or
the census set measured at run time (D32); a record says which, and stamps
the width the loops bound.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

#: Schema tag.  Bumped when a field is added, renamed or dropped, so a reader
#: that expected the old shape says so instead of finding ``None``.
FORMAT = "run-record-1"

#: What kind of run made this record.  ``campaign`` is a measurement; the
#: others are not, and nothing may pool them with one.  ``supplementary`` is
#: the kind of a declared supplementary stage (``config.SupplementaryStage``;
#: V5 plan §3, A96 (st-trajectory-ladder)): a measurement reported **beside**
#: the campaign's cell under its own test set and tolerance, never pooled
#: with it and never a campaign record.
RUN_KINDS: tuple[str, ...] = ("campaign", "gate", "smoke", "reference", "supplementary", "timing")

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
#: so, is the thing that must not happen (EXPERIMENT_REPORT.md §3.3).
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
#: finished, which is after the output path.  It is a position with **declared
#: callers** — the stages named in :data:`AUDIT_POSITION_AFTER_RUN_CALLERS`,
#: and no other; see :data:`AUDIT_POSITION_AFTER_RUN_WHY`.  Its sweep is the
#: loop's own map there too: the data structure is put back to the snapshot
#: taken at the entry to the output path for every field that changed outside
#: the coupling state, and the coupling state itself is left as the run ended
#: it — as PROCESS wrote it out — which is what distinguishes the position from
#: the declared one, and what makes its residual the distance between the
#: written file and a fixed point of the solve's own map.
AUDIT_POSITIONS: tuple[str, ...] = (
    "after_single_evaluation",
    "after_run",
    "entry_to_write_output_files",
)

#: Positions an optimisation run may audit at.  The declared one is the
#: default; the other may be asked for only by a declared caller
#: (:data:`AUDIT_POSITION_AFTER_RUN_CALLERS`), never by a campaign run.
OPTIMISATION_AUDIT_POSITIONS: tuple[str, ...] = (
    "entry_to_write_output_files",
    "after_run",
)

#: The optimisation phase's declared position, and the one position beside it.
AUDIT_POSITION_DECLARED = "entry_to_write_output_files"
AUDIT_POSITION_AFTER_RUN = "after_run"

#: The evaluation phase's one position: that phase runs one evaluation and
#: never reaches the output path, so the child audits where it terminated and
#: the pool composes no position for it (``child/evaluate.py`` stamps this
#: constant).  Named here so that the job identity can render an evaluation
#: job's position as what the run will actually stamp.
AUDIT_POSITION_EVALUATION = "after_single_evaluation"


def effective_audit_position(phase: str, asked: str) -> str | None:
    """The position a run of *phase* audits at, given what the job asked.

    An optimisation run audits where the job asked (the pool passes it to the
    child); an evaluation run audits at :data:`AUDIT_POSITION_EVALUATION`
    whatever the job's default says, because the pool passes no position and
    the child has one; a census run audits nowhere.
    """
    if phase == "B":
        return asked
    if phase == "A":
        return AUDIT_POSITION_EVALUATION
    return None

#: The stages that may ask an optimisation run to audit at ``after_run``, by
#: their registry name, each with the reason.  **Declared, never inferred**:
#: the run pool refuses the position for any caller not named here and for
#: every campaign run (:func:`assert_audit_position_allowed`), and each caller
#: stamps the override in its own record.  Adding a caller is adding a row
#: here with its reason — a gate that needs the position and is not named is
#: refused, which is the point.
#:
#: Until task **A67 (written-file-gap)** the prose here said the position had
#: "exactly one caller", the reproduction gate; it had three (the switch-
#: neutrality gate pins both of its captures to it, and the retry-ladder
#: demonstration runs of the ``attempts`` stage audited there), none of them
#: refused, because nothing enforced the sentence.  The table replaces the
#: sentence and the pool enforces the table.  The ``attempts`` stage was
#: retired with the simplification survey's item A2 (its columns are the
#: tally's) and its row left this table with it; a caller by that name is
#: refused like any other undeclared one.
AUDIT_POSITION_AFTER_RUN_CALLERS: dict[str, str] = {
    "reproduction": (
        "gate GR reproduces the previous revision's records, and that "
        "revision audited after the run; reproducing them means auditing "
        "where they were audited"
    ),
    "switch_neutrality": (
        "gate G1 pins both of its captures to one position so that the whole "
        "exit_audit block is compared value for value across a driver change "
        "rather than excluded"
    ),
    "written_file_gap": (
        "the gate that measures, per run, the distance between the state "
        "PROCESS wrote to its output files and a fixed point of the solve's "
        "own map (issue I-21) — which is what this position, and only this "
        "position, reads"
    ),
}

#: How the declared position is reached, quoted into every record that uses it.
#: The audit sweep mutates the state it measures, so it cannot be *run* at the
#: entry to the output path without handing that path a state the optimiser
#: never accepted — the output files, the exit code and the total node count
#: would all be of the audited state.  The driver therefore **snapshots** the
#: coupling state there (task A57 (driver-output-path); experiment plan §3.3)
#: and the residual is computed after the run, from the restored snapshot, by
#: the same one-sweep instrument every arm gets.
AUDIT_POSITION_HOW = (
    "the driver snapshots the coupling state and the whole data structure at "
    "the entry to write_output_files — before the per-run deferred nodes and before any "
    "output-time sweep — and this run computed the residual afterwards, from "
    "that snapshot restored into the data structure, with the same one-sweep "
    "instrument every arm gets.  The restore is proved bit-exact component by "
    "component before the sweep runs; a restore that is not bit-exact refuses "
    "the audit rather than reporting a residual of a state nobody chose.  The "
    "audit's own model calls are counted and never charged to the arm, and the "
    "per-run deferred nodes' own components stay excluded from the restricted "
    "statistic exactly as before.  Everything outside the coupling state that "
    "the output path changed before the snapshot is put back too — a derived "
    "set, counted and named per run — so the sweep evaluates the map the loop "
    "iterated rather than the one the output path left behind."
)

#: Why ``after_run`` still exists, what its residual means, and who may ask
#: for it.  Quoted into every record that audits there as
#: ``audit_position_note``.  Every campaign record uses the declared position.
AUDIT_POSITION_AFTER_RUN_WHY = (
    "this run audits after the whole run, which is after the output path: the "
    "same one-sweep instrument every arm gets, with the solve-phase data "
    "structure put back for every field outside the coupling state, on the "
    "coupling state as PROCESS wrote it out.  Its residual is therefore the "
    "distance between the written state and a fixed point of the solve's own "
    "map — not a convergence statement about the arm.  The position is where "
    "the previous revision audited, which is why the reproduction gate uses "
    "it; it may be asked for only by the stages "
    "records.AUDIT_POSITION_AFTER_RUN_CALLERS declares by name, each of which "
    "stamps the override in its own record, and the run pool refuses any "
    "other caller and every campaign run."
)


def assert_audit_position_allowed(
    position: str,
    *,
    phase: str,
    run_kind: str,
    caller: str | None,
    where: str = "",
) -> None:
    """Refuse an audit position nobody declared, or a campaign run off the declared one.

    The evaluation phase has one position and takes no argument; this is about
    the optimisation phase, where the plan declares one position for every arm
    and a second one exists for the callers named in
    :data:`AUDIT_POSITION_AFTER_RUN_CALLERS`.  Three refusals, none a warning:
    a position the record vocabulary does not know; a **campaign** run at any
    position but the declared one — the campaign audits where the plan says,
    whoever asks; and the second position asked for by a caller the table does
    not name, or by no caller at all.
    """
    at = f" for {where}" if where else ""
    if phase != "B":
        return
    if position not in OPTIMISATION_AUDIT_POSITIONS:
        raise RecordError(
            f"audit position {position!r}{at} is not one an optimisation run "
            f"may audit at ({OPTIMISATION_AUDIT_POSITIONS})"
        )
    if position == AUDIT_POSITION_DECLARED:
        return
    if run_kind == "campaign":
        raise RecordError(
            f"a campaign run{at} may not audit at {position!r}: every campaign "
            f"record audits at the declared position "
            f"{AUDIT_POSITION_DECLARED!r}, whoever asks"
        )
    if caller not in AUDIT_POSITION_AFTER_RUN_CALLERS:
        raise RecordError(
            f"audit position {position!r}{at} was asked for by "
            f"{caller!r}, which is not a declared caller of it.  The declared "
            f"callers are {sorted(AUDIT_POSITION_AFTER_RUN_CALLERS)}; a stage "
            f"that needs the position is added to "
            f"records.AUDIT_POSITION_AFTER_RUN_CALLERS with its reason, and "
            f"stamps the override in its own record"
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
    _f("campaign_tau", "AB", "always", "the one tolerance every converger uses; follows the test set's declared value (config.TAU_BY_TEST_SET) unless overridden"),
    _f("campaign_test_set", "AB", "always", "which components every block loop tests: 'census' (the measured test set, D32) or 'write_set' (the block's whole write set, V4's predicate, the fallback of D39); one value per campaign, DR11"),
    _f("campaign_run_kind", "AB", "always", "campaign | gate | smoke | reference | supplementary | timing"),
    # DR12 (A101 (v5-timers-and-once)): the three timing fields are required
    # only on a record made with the timers on (``when == "timers"``): a
    # record made before the instrument existed, or with it off, is complete
    # without them, so no seeded record is re-made by the contract alone.
    _f("campaign_timers", "AB", "timers", "whether the wall-clock timers were composed (PROCESS_ARCH_TIMERS=on); context, never evidence"),
    _f("timers", "AB", "timers", "the driver's wall-clock accumulators harvested before the audit, the harness's excluded costs and the epochs (DR12); context, never evidence"),
    _f("launcher", "AB", "timers", "the pool's independent wall of the subprocess, its spawn and return epochs and the load average at both (DR12); context, never evidence"),
    _f("campaign_predicate_mode", "AB", "always", "which denominator the test scales by: 'frozen', the one ruler since DR11"),
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
    # --- which job this is: the pool's stamp, after the child returns ------
    _f("job_identity", "AB", "always", "every field the pool composed into this run, rendered once (pool.JOB_IDENTITY_FIELDS): what --resume compares"),
    _f("job_digest", "AB", "always", "sha256 over the canonical JSON of job_identity; the shared pool's directory carries its first sixteen digits"),
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
    _f("audit_snapshot", "B", "always", "the driver's snapshots on the output path — the coupling state and the whole data structure, per position — or why there are none"),
    _f("exit_audit", "AB", "always", "the achieved accuracy: one further full sweep, uncharged"),
    _f("exit_audit.instrument", "AB", "finished", "what the audit put back before its sweep: the positions snapshotted, the derived restored set, and what could not be restored, by name"),
    _f("exit_audit.instrument.restores", "AB", "finished", "the instrument's own version: which mechanism made this residual"),
    _f("exit_audit.instrument.n_restored", "AB", "finished", "fields put back and read back equal before the sweep"),
    _f("exit_audit.instrument.n_not_restorable", "AB", "finished", "fields the restore asked for and could not put back; their names are beside the count"),
    _f("exit_audit.predicate_mode", "AB", "finished", "which ruler the run's own loops stopped on: 'frozen', the one ruler"),
    _f("exit_audit.frozen", "AB", "finished", "the audit on the measured-scale ruler (the second ruler's block, exit_audit.mixed, went with the mixed ruler: DR11, D30)"),
    # --- counters common to both phases -----------------------------------
    _f("node_calls_total", "AB", "always", "model executions, the whole run"),
    _f("n_arrangement_method_calls", "AB", "always", "executions of the run-constant geometry method; stamped, never pooled"),
    _f("block_loop_totals", "AB", "finished", "the block solver's own totals"),
    _f("defer_per_run_totals", "AB", "always", "the per-run deferral's own counts, or null when it is off"),
    _f("schedule_resolution", "AB", "always", "the block schedule and the deferral sets resolved once per run (DR9): what was resolved, keyed on the figure of merit, the digests of the files the resolution read, and how many times the resolver ran — 1 in every run of this experiment that composes a block schedule or a deferral, 0 with every switch unset"),
    _f("loop_test_sets", "AB", "always", "what the block loops tested (DR11): the test set, the loop key it was selected by, the artifact and its digests, the width per block; null with every switch unset, when no block loop runs"),
    _f("node_census", "AB", "always", "model executions per node name"),
    _f("exit_forensics", "AB", "always", "the five fields recorded at every exit"),
    _f("attempts", "AB", "always", "one entry per optimiser attempt, in order"),
    _f("attempts_node_calls_available", "AB", "always", "whether the driver stamped the cost counters at every attempt boundary of this run"),
    _f("attempt_accounting", "AB", "always", "how the per-attempt costs decompose the run's solve-phase totals, with what falls outside every attempt"),
    # --- the output path --------------------------------------------------
    _f("output_path", "B", "always", "which output path ran: mda_output | finalise_once"),
    _f("output_loop_sweeps", "B", "always", "sweeps the output-time loop ran; 0 under the finalise-once path"),
    _f("output_path_entries", "B", "always", "entries to the output path: one per scan point"),
    # --- how this run differed from the campaign, if it did ---------------
    _f("reproduction_overrides", "AB", "always", "what the reproduction gate set differently, or null for a run that is not that gate's"),
    _f("per_run_artifact", "AB", "always", "the per-run deferral artifact the exit audit's restricted statistic derived its excluded set from, or null where none was handed to it"),
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
    _f("dispatch_sweeps_solve_phase", "B", "finished", "sweeps of the dispatch body during the solve: the whole the per-attempt sweeps decompose"),
    _f("n_model_calls", "B", "finished", "sweeps of the dispatch body over the whole run (numerics.n_model_calls, incremented once per _call_models_once) — not evaluations: a block sweep runs one module, so it is not comparable between a flat loop and a block schedule; the evaluations of the model set are sweeps_per_eval.n_evaluations (issue I-26, task A80 (report-accuracy-audit))"),
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
#: The exit audit's rulers: **one** since driver change DR11 (A100
#: (v5-test-set); decision D30, V5 plan §12 Q5).  V4 audited on two —
#: ``frozen`` and ``mixed`` — and the contract required both or neither,
#: because the mixed ruler reads lower wherever its denominator binds and a
#: table built from half-present pairs would report a change of ruler as a
#: change of accuracy (improvement item 5a's trap (ii)).  With one ruler the
#: contract is that a finished record names it; the tuple stays so that every
#: consumer that iterates the rulers reads one and not a literal.
AUDIT_RULERS: tuple[str, ...] = ("frozen",)

CONTRACT: dict[str, tuple[str, ...]] = {
    "B": (
        "n_solver_iterations",
        "mfile.ifail",
        "exit_forensics.ladder_stage",
        "exit_forensics.constraint_residual_vector",
        "exit_forensics.active_set",
        "exit_forensics.n_attempts",
        *(f"exit_audit.{ruler}.residual_max_hex" for ruler in AUDIT_RULERS),
    ),
    "A": (
        "exit_forensics.constraint_residual_vector",
        "exit_forensics.active_set",
        "exit_forensics.n_attempts",
        *(f"exit_audit.{ruler}.residual_max_hex" for ruler in AUDIT_RULERS),
    ),
}


def fields_for(phase: str, *, finished: bool, timers_on: bool = False) -> tuple[Field, ...]:
    """The fields a record of this phase must carry.

    ``when == "timers"`` fields are owed only by a record made with the
    wall-clock timers on (DR12); the other two values are as before.
    """
    return tuple(
        field
        for field in SCHEMA
        if phase in field.phases
        and (
            field.when == "always"
            or (field.when == "finished" and finished)
            or (field.when == "timers" and timers_on)
        )
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
    timers_on = bool(record.get("campaign_timers"))
    absent = [
        field.name
        for field in fields_for(phase, finished=finished, timers_on=timers_on)
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
    assert_audit_ruler(record, where=where)
    absent = missing_fields(record)
    if absent:
        raise RecordError(
            f"incomplete record{' for ' + where if where else ''}: "
            f"{len(absent)} declared field(s) missing — {', '.join(absent)}.  "
            f"A summary computed over records missing different fields is a "
            f"summary over a population nobody can state."
        )


def assert_audit_ruler(record: Mapping[str, Any], *, where: str = "") -> None:
    """Refuse a finished record whose exit audit names no ruler, or not every one.

    *Was ``assert_both_rulers``* while the audit was taken on two rulers (V4,
    driver change DR5): the pair was all-or-nothing because the mixed ruler
    reads lower wherever its denominator binds and a table built from
    half-present pairs would report a change of ruler as a change of accuracy
    (improvement item 5a's trap (ii)).  Since DR11 there is one ruler
    (:data:`AUDIT_RULERS`); the check keeps its shape — every ruler the
    contract names must be present as a block, and a finished run's audit
    that names none is refused — so that a second ruler, should one ever be
    added again, is all-or-nothing from the day it is declared.

    A record that did not finish carries no audit at all, and that is not this
    check's business: :func:`assert_complete` says which fields a finished
    record owes.
    """
    if record.get("status") != "ok":
        return
    audit = record.get("exit_audit") or {}
    if audit.get("skipped") or audit.get("refused") or audit.get("error"):
        return
    present = [r for r in AUDIT_RULERS if isinstance(audit.get(r), Mapping)]
    if present and len(present) != len(AUDIT_RULERS):
        raise RecordError(
            f"the exit audit{' of ' + where if where else ''} carries "
            f"{present} and not {list(AUDIT_RULERS)}.  Every declared ruler or "
            f"none: a table built from records with one column here and two "
            f"there reports a change of ruler as a change of accuracy."
        )
    if not present:
        raise RecordError(
            f"the exit audit{' of ' + where if where else ''} of a finished "
            f"run names no ruler at all.  An achieved-accuracy figure whose "
            f"denominator is not recorded cannot be compared with one whose is."
        )


#: The two quantities a run's attempts decompose, and the run total each must
#: add up to.  Both are solve-phase totals: the output-time loop and the exit
#: audit are outside every attempt and are in neither.
ATTEMPT_SUMS: tuple[tuple[str, str], ...] = (
    ("node_calls_solve_phase", "node_calls_solve_phase"),
    ("sweeps", "dispatch_sweeps_solve_phase"),
)


def assert_attempt_summation(record: Mapping[str, Any], *, where: str = "") -> None:
    """Refuse per-attempt costs that do not sum to the run total.

    The driver stamps its cost counters at the entry to and the exit from every
    attempt of the optimiser's retry ladder (driver change DR7, task A60
    (driver-attempts)), so every attempt of a finished optimisation carries its
    own node calls and its own sweeps.  Each of those must sum, over the
    attempts, to the run's solve-phase total for that quantity: per-attempt
    accounting whose parts do not add up to the whole it decomposes is worse
    than none, because the cost ratio published *with and without* retried
    seeds would then be computed over quantities that do not decompose the
    published one.

    A record whose attempts carry **no** cost at all is passed over rather than
    refused — an evaluation-phase record has no attempts, and a run that
    crashed before the driver stamped anything has nothing to check — but a
    record carrying a cost for some attempts and not others is refused, because
    a partial decomposition cannot be summed.

    **A record that did not finish has no run total to decompose**, so for it
    only the all-or-none rule above is checked and the summation is not: the
    driver stamps each attempt's cost at the attempt boundary (DR7) but the
    run total is written at a finished exit, and a crashed optimisation
    therefore carries per-attempt costs and no ``node_calls_solve_phase``.
    That is the record's shape, not a defect in it — the crash is a taxonomy
    row and its cost is never summarised (plan §3.5) — and refusing it would
    refuse every crash out of the taxonomy.  *(A75 (campaign-tally-source):
    at the first campaign press all 28 crashed optimisations, and 0 of the
    921 finished records, were refused by this rule as it stood; the sibling
    :func:`assert_sweep_decomposition` already passed unfinished records over.)*
    """
    attempts = record.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        return
    # Unfinished means the record *says* it did not finish; a record with no
    # status at all (a synthetic one in a tooth) is held to the full rule.
    status = record.get("status")
    finished = status is None or status == "ok"
    for field, total_field in ATTEMPT_SUMS:
        per_attempt = [a.get(field) for a in attempts]
        if all(value is None for value in per_attempt):
            continue
        if any(value is None for value in per_attempt):
            raise RecordError(
                f"partial per-attempt {field}"
                f"{' for ' + where if where else ''}: "
                f"{sum(1 for v in per_attempt if v is not None)} of "
                f"{len(per_attempt)} attempts carry a count.  Either the driver "
                f"stamps them at every attempt boundary or at none; a partial "
                f"decomposition cannot be summed."
            )
        if not finished:
            continue
        total = record.get(total_field)
        if total is None:
            raise RecordError(
                f"per-attempt {field} without a run total"
                f"{' for ' + where if where else ''}: {total_field} is absent, "
                f"so there is nothing for them to decompose."
            )
        summed = sum(int(v) for v in per_attempt)
        if summed != int(total):
            raise RecordError(
                f"per-attempt {field} does not sum to the run total"
                f"{' for ' + where if where else ''}: "
                f"{' + '.join(str(int(v)) for v in per_attempt)} = {summed}, "
                f"{total_field} = {int(total)}.  REFUSED: the cost ratio "
                f"published with and without retried seeds would be computed "
                f"over quantities that do not decompose the published one."
            )


#: The identity a finished run's sweep total decomposes by.  ``per_run_sweep``
#: is one sweep, spent in ``write_output_files`` running the nodes deferred to
#: once per run; it is 1 when that set is non-empty and 0 otherwise.  For an arm
#: with no block schedule the loop term is the sweeps the analysis loop took,
#: which the per-evaluation histogram sums.  The exit audit's own sweep is not in
#: the total: the counters are read before the audit runs, so the measurement is
#: not charged to the thing it measures.
SWEEP_DECOMPOSITION_IDENTITY = (
    "dispatch_sweeps = loop sweeps + output-time loop sweeps + the one sweep "
    "the per-run deferral spends at the output path"
)


def sweep_decomposition(record: Mapping[str, Any]) -> dict[str, Any]:
    """Does the run's sweep total decompose into the parts that claim it?

    The identity, for an arm that runs a block schedule::

        dispatch_sweeps = block_sweeps + output_loop_sweeps + per_run_sweep

    For an arm with no block schedule the first term is instead
    ``sweeps_per_eval.n_sweeps``.  Returns the reconciliation as a block --
    ``checked``, each term, ``residual`` and ``decomposes`` -- so a stage that
    prints it and the refusal that acts on it read one construction.  A record
    that carries no sweep total is ``checked: False`` with the reason.

    Moved verbatim from the retired ``predicate_counters`` stage's
    ``_reconcile_sweeps`` (task A58 (driver-predicate-counters)); the row it
    used to read its terms from is read from the record here instead.
    """
    total = record.get("dispatch_sweeps")
    if total is None:
        return {"checked": False, "why": "the record carries no sweep total"}
    per_run = record.get("defer_per_run_totals") or {}
    per_run_sweep = 1 if (per_run.get("executed_once") or []) else 0
    output = record.get("output_loop_sweeps") or 0
    totals = record.get("block_loop_totals") or {}
    if totals.get("block_sweeps"):
        loop = totals["block_sweeps"]
        loop_is = "block_sweeps (the block schedule's own charged sweeps)"
    else:
        loop = ((record.get("sweeps_per_eval") or {}).get("n_sweeps")) or 0
        loop_is = "sweeps_per_eval.n_sweeps (the analysis loop's own sweeps)"
    residual = int(total) - (int(loop) + int(output) + per_run_sweep)
    return {
        "checked": True,
        "identity": SWEEP_DECOMPOSITION_IDENTITY,
        "dispatch_sweeps": total,
        "loop_sweeps": loop,
        "loop_sweeps_is": loop_is,
        "output_loop_sweeps": output,
        "per_run_deferral_sweep": per_run_sweep,
        "residual": residual,
        "decomposes": residual == 0,
        "why": (
            "the exit audit's own sweep is not in this total: the counters are "
            "read before the audit runs, so the measurement is not charged to "
            "the thing it measures"
        ),
    }


def assert_sweep_decomposition(record: Mapping[str, Any], *, where: str = "") -> None:
    """Refuse a finished record whose sweep total does not decompose.

    A residual that is not 0 is refused, never absorbed: a sweep total nobody
    can decompose is a total nobody can attribute, and the per-sweep overhead
    tables are built from exactly these terms.  A record that did not finish,
    or carries no sweep total, is passed over -- there is no total to
    decompose, and :func:`assert_complete` says what a finished record owes.
    """
    if record.get("status") != "ok":
        return
    block = sweep_decomposition(record)
    if not block["checked"] or block["decomposes"]:
        return
    raise RecordError(
        f"the sweep total does not decompose"
        f"{' for ' + where if where else ''}: dispatch_sweeps = "
        f"{block['dispatch_sweeps']}, but {block['loop_sweeps_is']} = "
        f"{block['loop_sweeps']} + output_loop_sweeps = "
        f"{block['output_loop_sweeps']} + per-run deferral sweep = "
        f"{block['per_run_deferral_sweep']} leaves a residual of "
        f"{block['residual']}.  REFUSED: a sweep total nobody can decompose is "
        f"a total nobody can attribute ({SWEEP_DECOMPOSITION_IDENTITY})."
    )


def assert_usable(record: Mapping[str, Any], *, where: str = "") -> None:
    """Every refusal, in one call.  What a reader of records goes through."""
    assert_complete(record, where=where)
    assert_attempt_summation(record, where=where)
    assert_sweep_decomposition(record, where=where)


# --------------------------------------------------------------------------
# building and reading
# --------------------------------------------------------------------------


#: Why an evaluation-phase record's ``attempts`` list is empty.  Written into
#: the record rather than left to be inferred from an absent key: a reader of
#: two records, one with attempts and one without, must be able to tell "this
#: phase has no optimiser" from "this run stopped before it had one".
ATTEMPTS_NOT_APPLICABLE = (
    "this phase runs one evaluation of the model set with no optimiser in the "
    "process, so there is no retry ladder, no attempt, and nothing for a "
    "per-attempt cost to decompose.  The run's node calls and sweeps are the "
    "single evaluation's own and are recorded as such."
)


def attempts_from_forensics(
    forensics: Mapping[str, Any],
    *,
    costs: Sequence[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """The per-attempt list of harness plan §4.4, from what the driver gives.

    Two halves meet here.  The **solver-owned** half — the finite-difference
    step the attempt entered with, its iteration count, its exit code, whether
    it raised — is recorded by the harness's own wrap of every solver's
    ``solve``.  The **cost** half — model executions, sweeps, sweeps per block
    and the evaluations they came in — is the driver's, stamped at the attempt
    boundaries inside the retry ladder itself (driver change DR7).

    The ladder stage is taken from the **driver's own** name for the rung, not
    from the harness's positional guess at it; the guess is kept beside it under
    ``stage_positional`` so the two can be compared rather than assumed equal,
    which is what :func:`attempt_accounting` does.
    """
    by_attempt = {c.get("attempt"): c for c in (costs or [])}
    out: list[dict[str, Any]] = []
    for attempt in forensics.get("attempts") or []:
        index = attempt.get("attempt")
        cost = by_attempt.get(index) or {}
        out.append(
            {
                "attempt": index,
                "stage": cost.get("stage", attempt.get("ladder_stage_positional")),
                "stage_positional": attempt.get("ladder_stage_positional"),
                "ladder": cost.get("ladder"),
                "epsfcn": attempt.get("epsfcn_at_entry"),
                "n_iterations": attempt.get("n_solver_iterations"),
                "ifail": attempt.get("ifail"),
                "raised": attempt.get("raised"),
                "node_calls_solve_phase": cost.get("node_calls_solve_phase"),
                "sweeps": cost.get("sweeps"),
                "sweeps_by_block": cost.get("sweeps_by_block"),
                "sweeps_per_eval": cost.get("sweeps_per_eval"),
            }
        )
    return out


def attempt_accounting(
    attempts: Sequence[Mapping[str, Any]],
    stamps: Mapping[str, Any] | None,
    *,
    node_calls_solve_phase: int | None,
    dispatch_sweeps_solve_phase: int | None,
    phase: str,
) -> dict[str, Any]:
    """How the per-attempt costs decompose the run's solve-phase totals.

    Published beside the attempts, never instead of them, and stated as an
    identity with its residual rather than as a claim: the summation the record
    module refuses on is ``Σ attempts == the run total``, and that holds only
    because nothing evaluates the model set during the solve except the
    optimiser.  That premise is a measurement here — the node calls and sweeps
    falling **outside** every attempt — not an assumption, so a driver change
    that put work between the ladder and the output path would show up as a
    non-zero residual instead of silently unbalancing the sum.
    """
    if phase == "A":
        return {
            "applicable": False,
            "why": ATTEMPTS_NOT_APPLICABLE,
            "n_attempts": 0,
            "retried": False,
        }
    block: dict[str, Any] = {
        "applicable": True,
        "n_attempts": len(attempts),
        "retried": len(attempts) > 1,
        "retried_is": (
            "a seed is 'retried' when the optimiser was called more than once "
            "on it; the experiment plan publishes every cost ratio with and "
            "without the retried seeds"
        ),
        "stages": [a.get("stage") for a in attempts],
        "ifail_per_attempt": [a.get("ifail") for a in attempts],
        "iterations_per_attempt": [a.get("n_iterations") for a in attempts],
    }
    if not stamps or not stamps.get("available"):
        block["decomposes"] = None
        block["why_not_checked"] = (
            (stamps or {}).get("why")
            or "the driver recorded no attempt boundary in this process"
        )
        return block
    block["n_ladders"] = stamps.get("n_ladders")
    block["stage_names_agree_with_position"] = all(
        a.get("stage") == a.get("stage_positional") for a in attempts
    )
    mismatched = [
        {"attempt": a.get("attempt"), "driver": a.get("stage"),
         "positional": a.get("stage_positional")}
        for a in attempts
        if a.get("stage") != a.get("stage_positional")
    ]
    block["stage_name_disagreements"] = mismatched
    sums: dict[str, Any] = {}
    for field, total_field, first, last in (
        (
            "node_calls_solve_phase",
            "node_calls_solve_phase",
            "node_calls_at_first_entry",
            "node_calls_at_last_exit",
        ),
        (
            "sweeps",
            "dispatch_sweeps_solve_phase",
            "sweeps_at_first_entry",
            "sweeps_at_last_exit",
        ),
    ):
        total = (
            node_calls_solve_phase
            if total_field == "node_calls_solve_phase"
            else dispatch_sweeps_solve_phase
        )
        per_attempt = [a.get(field) for a in attempts]
        summed = (
            sum(int(v) for v in per_attempt)
            if per_attempt and all(v is not None for v in per_attempt)
            else None
        )
        before = stamps.get(first)
        after = stamps.get(last)
        sums[field] = {
            "per_attempt": per_attempt,
            "summed": summed,
            "run_total_field": total_field,
            "run_total": total,
            "residual": (
                None if (summed is None or total is None) else int(total) - summed
            ),
            "before_the_first_attempt": before,
            "after_the_last_attempt": (
                None if (after is None or total is None) else int(total) - int(after)
            ),
        }
    block["sums"] = sums
    block["decomposes"] = all(
        entry["residual"] == 0 for entry in sums.values()
    )
    block["outside_attempts"] = {
        "node_calls": (
            None
            if sums["node_calls_solve_phase"]["before_the_first_attempt"] is None
            else sums["node_calls_solve_phase"]["before_the_first_attempt"]
            + (sums["node_calls_solve_phase"]["after_the_last_attempt"] or 0)
        ),
        "sweeps": (
            None
            if sums["sweeps"]["before_the_first_attempt"] is None
            else sums["sweeps"]["before_the_first_attempt"]
            + (sums["sweeps"]["after_the_last_attempt"] or 0)
        ),
        "what": (stamps.get("notes") or {}).get("outside_attempts"),
    }
    block["sweeps_agree_with_the_evaluation_histogram"] = all(
        (a.get("sweeps_per_eval") or {}).get("n_sweeps") == a.get("sweeps")
        for a in attempts
    )
    block["notes"] = stamps.get("notes")
    return block


# --------------------------------------------------------------------------
# arm names: what the matrix calls an arm today, and what a record calls it
# --------------------------------------------------------------------------

#: The arm renaming of **2026-09-15**, as a translation from the name a record
#: made before it carries to the name the matrix uses today.  The user's
#: ruling: *"In the v4 report, rename A0p and A1 to A1 and A2, and B3 to B2.
#: That makes the naming of the rungs reflect the parallelism in the switch
#: matrix … it should be applied consistently throughout the v4 folder."*  The
#: rungs then read ``AR/A0/A1/A2`` against ``BR/B0/B1/B2`` — stopping rule,
#: burn-time ownership, partitioning — one letter apart per rung (task **A78
#: (arm-renames)**).
#:
#: **The records were not re-made.**  The campaign's 949 records and every gate
#: record made before that date stamp ``campaign_arm`` and ``job_identity.arm``
#: with the old names, and a record's name is the name at the time of the run.
#: This table is applied in **one** place, :func:`read`, so that every reader
#: of a record — the pool's resume comparison, the tallies, the gates, the
#: population marker, the stamp surveys — sees today's names, and a record made
#: today, which stamps :data:`ARM_NAMING` (see :func:`translate_recorded_arm_names`),
#: passes through untouched.  Directory names on disk keep the names they were
#: made under: the record is the truth and the path is where the pool found
#: it (``pool.directory_for`` resolves a job's directory by its digest).
#:
#: Reversal: empty this table and the read returns every record as written.
RECORDED_ARM_NAMES: dict[str, str] = {"A0p": "A1", "A1": "A2", "B3": "B2"}

#: The field a record made **after** the renaming carries, and its value: the
#: name of the naming scheme its arm fields are written in.  Stamped by the
#: pool beside ``job_identity`` (``pool.stamp_identity``), never by hand.  A
#: record without it was made under the scheme before the renaming and is
#: translated through :data:`RECORDED_ARM_NAMES`; a record with it is not.
#: This is what lets today's ``A1`` (the flat arm with a constant owning the
#: burn time) be told from a pre-renaming record's ``A1`` (today's ``A2``):
#: the two spell the same and mean different arms, and nothing but a stamp
#: can separate them.  Deliberately **not** a field of :data:`SCHEMA`: a schema
#: field is required of every record, and requiring this one of the 949
#: campaign records would make ``--resume`` cross the renaming as though it
#: were a schema change (harness plan amendment 17), which it is not — no
#: quantity in any record changed.
ARM_NAMING_FIELD = "arm_naming"
ARM_NAMING = "rungs-2026-09-15"

#: The field a translated record carries **in memory** beside the translated
#: names: what the record said on disk, so that a reader can always get back to
#: the bytes.  Never written to disk — the record on disk stays as the run
#: wrote it.
ARM_NAME_TRANSLATION_FIELD = "arm_name_translation"


def _matrix_arm_names() -> frozenset[str]:
    """The arm names the matrix knows today.  Imported lazily: ``arms`` does
    not import this module, but keeping the schema module free of experiment
    imports at load time is what lets the child import it alone."""
    from ..experiment import arms as arms_mod  # noqa: PLC0415

    return frozenset(arms_mod.ARMS)


def translate_recorded_arm_names(
    record: Mapping[str, Any], *, where: str = ""
) -> dict[str, Any]:
    """*record* with its arm fields in today's names, or a refusal by name.

    The one application of :data:`RECORDED_ARM_NAMES`.  Three cases:

    * the record carries :data:`ARM_NAMING_FIELD` = :data:`ARM_NAMING` — made
      after the renaming, already in today's names; returned unchanged after
      its arm is checked against the matrix;
    * the record carries no naming stamp — made before the renaming; its
      ``campaign_arm`` and ``job_identity.arm`` go through the table, and
      where the arm's name changed its ``job_digest`` is **re-derived** over
      the translated identity, the stamped digest kept in the record's
      :data:`ARM_NAME_TRANSLATION_FIELD` block as ``job_digest_as_stamped``
      (that block is the whole in-memory trace of the translation, one field,
      so that a gate comparing two records value for value has one name to
      set aside).  The digest is a pure function of the
      identity and the identity is now spelled in today's names, so the
      stamped digest — a digest of the old spelling — identifies nothing the
      pool composes today; the re-derived one is what the pool's job computes,
      which is what lets ``--resume`` keep the record.  The re-derivation
      happens only where the stamped digest re-derives from the stamped
      identity in the first place; a record whose digest never matched its
      identity keeps its mismatch and is refused downstream as before;
    * the record names an arm that neither the table nor the matrix knows —
      **refused**, naming the arm and the record.  Never kept under a name
      nobody declared, never dropped from a population without a word.

    A record with no ``campaign_arm`` at all (the ``no_record`` row for a
    directory without a record; a census record from before arms were stamped)
    is returned as it is.
    """
    out = dict(record)
    recorded = out.get("campaign_arm")
    if recorded is None:
        return out
    known = _matrix_arm_names()
    tag = f" ({where})" if where else ""
    scheme = out.get(ARM_NAMING_FIELD)
    if scheme is not None:
        if scheme != ARM_NAMING:
            raise RecordError(
                f"record{tag} stamps {ARM_NAMING_FIELD}={scheme!r}, a naming "
                f"scheme this harness does not know (it knows {ARM_NAMING!r} "
                f"and, unstamped, the scheme before 2026-09-15).  Refused "
                f"rather than read under a guess at what its arm names mean."
            )
        if recorded not in known:
            raise RecordError(
                f"record{tag} names arm {recorded!r}, which the matrix does "
                f"not know (arms: {', '.join(sorted(known))}).  Refused by "
                f"name rather than kept under one nobody declared."
            )
        return out
    if recorded not in RECORDED_ARM_NAMES and recorded not in known:
        raise RecordError(
            f"record{tag} names arm {recorded!r}, which neither "
            f"records.RECORDED_ARM_NAMES ({', '.join(RECORDED_ARM_NAMES)}) nor "
            f"the matrix ({', '.join(sorted(known))}) knows.  Refused by name "
            f"rather than kept under one nobody declared or dropped without "
            f"a word."
        )
    today = RECORDED_ARM_NAMES.get(recorded, recorded)
    out["campaign_arm"] = today
    translation: dict[str, Any] = {
        "recorded_campaign_arm": recorded,
        "campaign_arm": today,
        "table": "harness.core.records.RECORDED_ARM_NAMES",
        "scheme_of_the_record": "the arm names before 2026-09-15 (unstamped)",
    }
    identity = out.get("job_identity")
    if isinstance(identity, Mapping):
        identity = dict(identity)
        recorded_identity_arm = identity.get("arm")
        if isinstance(recorded_identity_arm, str):
            if (
                recorded_identity_arm not in RECORDED_ARM_NAMES
                and recorded_identity_arm not in known
            ):
                raise RecordError(
                    f"record{tag} stamps job_identity.arm={recorded_identity_arm!r}, "
                    f"which neither records.RECORDED_ARM_NAMES nor the matrix "
                    f"knows.  Refused by name."
                )
            identity_arm = RECORDED_ARM_NAMES.get(
                recorded_identity_arm, recorded_identity_arm
            )
            translation["recorded_job_identity_arm"] = recorded_identity_arm
            translation["job_identity_arm"] = identity_arm
            stamped_digest = out.get("job_digest")
            if identity_arm != recorded_identity_arm:
                identity["arm"] = identity_arm
                if isinstance(stamped_digest, str) and job_digest(
                    record["job_identity"]
                ) == stamped_digest:
                    out["job_digest"] = job_digest(identity)
                    translation["job_digest_as_stamped"] = stamped_digest
                    translation["job_digest"] = out["job_digest"]
                    translation["job_digest_note"] = (
                        "re-derived over the translated job_identity; the "
                        "stamped digest is of the old spelling and identifies "
                        "no job the pool composes today"
                    )
                else:
                    translation["job_digest_note"] = (
                        "left as stamped: it did not re-derive from the stamped "
                        "job_identity, so the record keeps its mismatch"
                    )
            out["job_identity"] = identity
    # The record in memory differs from the bytes on disk in the translated
    # names and, where a name changed, in this one trace field -- nothing
    # else.  The naming stamp itself is not added in memory: a gate comparing
    # two records value for value would otherwise see a field neither run
    # wrote, and what the reader adds is kept to one name.
    if today != recorded or translation.get("job_identity_arm") != translation.get(
        "recorded_job_identity_arm"
    ):
        out[ARM_NAME_TRANSLATION_FIELD] = translation
    return out


def stamped_as_today(record: Mapping[str, Any]) -> dict[str, Any]:
    """*record*, as read, made safe to write to disk again.

    A record that came through :func:`read` carries today's arm names and no
    naming stamp (the stamp is the pool's, on disk).  Written back as it is —
    a tooth's doctored copy, a scratch record — it would be read a second time
    through :data:`RECORDED_ARM_NAMES`, and an arm whose today's name is also a
    key of the table (``A1``) would come back as another arm.  So a copy that
    goes to disk gets the stamp and loses the in-memory trace.  The one rule:
    **a record read through** :func:`read` **and written again goes through
    here.**
    """
    out = dict(record)
    out.pop(ARM_NAME_TRANSLATION_FIELD, None)
    if out.get("campaign_arm") is not None:
        out[ARM_NAMING_FIELD] = ARM_NAMING
    return out


def read(outdir: Path | str) -> dict[str, Any]:
    """One record from a run directory.  An absent one is a record, not a gap.

    A directory with no record is reported as ``no_record`` rather than raising:
    a crashed subprocess that wrote nothing is a taxonomy row, and turning it
    into an exception is how a whole class of failures once left a tally
    silently.

    **The one place a record's arm names are translated** into today's names
    (:func:`translate_recorded_arm_names`, :data:`RECORDED_ARM_NAMES`); every
    reader of a run record goes through here so that all of them see the same
    names, and a record naming an arm nobody declared is refused here, by
    name.  A reader that needs the bytes as written — the pool's own
    ``stamp_identity``, a tooth that stales a record on disk and writes it
    back — reads the JSON itself and says so.
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
        record = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return {
            "status": "no_record",
            "failure_class": "machinery",
            "record_path": str(path),
            "why": f"the record is not readable JSON: {exc}",
        }
    if not isinstance(record, Mapping):
        return {
            "status": "no_record",
            "failure_class": "machinery",
            "record_path": str(path),
            "why": f"the record is JSON but not an object ({type(record).__name__})",
        }
    return translate_recorded_arm_names(record, where=str(path))


def job_digest(identity: Mapping[str, Any]) -> str:
    """The digest of one job identity: sha256 over its canonical JSON.

    Canonical means sorted keys, no whitespace, ASCII escapes — so two renders
    of the same identity are the same bytes whatever produced them.  Lives here
    rather than in the pool so that a reader of a record can re-derive the
    digest from the stamped ``job_identity`` without importing the pool, which
    is what :func:`is_complete_for` does.
    """
    canonical = json.dumps(
        identity, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


#: Identity fields the **child** also stamps, under its own names.  Compared by
#: :func:`is_complete_for` beside the pool's stamp, so a record whose digest
#: matches but whose child-stamped δ (or mode, or pin, or position) differs is
#: refused: the two stamps have to agree with each other and with the job.
IDENTITY_FIELDS_STAMPED_BY_THE_CHILD: dict[str, str] = {
    "phase": "campaign_phase",
    "arm": "campaign_arm",
    "configuration": "campaign_configuration",
    "seed": "campaign_seed",
    "regime": "regime",
    "run_kind": "campaign_run_kind",
    "delta": "campaign_delta",
    "pin_hex": "campaign_pin_hex",
    "predicate_mode": "campaign_predicate_mode",
    "audit_position": "audit_position",
    "test_set": "campaign_test_set",
    "tau": "campaign_tau",
    "timers": "campaign_timers",
}

#: The value an identity field **means when it is absent** from the rendered
#: identity: V4's.  Driver change DR11 (A100 (v5-test-set)) made the test set
#: and the tolerance job-identity fields; the fallback of decision D39 — the
#: block's whole write set at 1e-6 — is **exactly V4's predicate**, and every
#: record made before DR11 was made under it, so a job under the fallback
#: carries V4's identity (and V4's digest) and the seeded records are the
#: fallback's records.  A job under the census set, or at any other
#: tolerance, renders both fields and has a digest no earlier record has.
#: ``why_not_complete_for`` compares the child's stamp against the identity's
#: value **or this default**, so a V4 record at ``campaign_tau = 1e-6`` is
#: the same job as a fallback job that renders no ``tau``.  The values are
#: ``config.V4_TEST_SET`` and ``config.TAU_BY_TEST_SET[V4_TEST_SET]``,
#: repeated here as literals because this module never imports the config.
IDENTITY_DEFAULTS_WHEN_ABSENT: dict[str, Any] = {
    "test_set": "write_set",
    "tau": 1e-6,
    # DR12: the timers off -- every record made before the instrument, and
    # every gate record since, is a record made without it.
    "timers": False,
}

#: The six fields the comparison consisted of before task A72
#: (resume-identity-and-shared-pool): the readable half, kept as the first
#: thing checked so that a refusal on them reads as "not this arm" rather than
#: as a digest mismatch.
READABLE_IDENTITY_FIELDS: tuple[str, ...] = (
    "arm", "configuration", "seed", "phase", "regime", "run_kind",
)


def why_not_complete_for(
    record: Mapping[str, Any], *, identity: Mapping[str, Any], digest: str
) -> str | None:
    """Why *record* is not a finished record of exactly this job, or None.

    What ``resume`` consults, spelled out.  A directory is never evidence of a
    completed run: an interrupted one leaves a directory behind, and re-using
    it would put a half-written record into a population.  Four comparisons,
    in order:

    1. the record finished (``status == "ok"``);
    2. the **readable half** — arm, configuration, seed, phase, regime, run
       kind — against the child's own stamps;
    3. every identity field the child also stamps
       (:data:`IDENTITY_FIELDS_STAMPED_BY_THE_CHILD`) against the job, and the
       pool's stamped ``job_identity`` field by field against the job's — so a
       record whose digest was copied but whose δ was not is refused by name;
    4. the stamped ``job_digest`` equals the job's **and** re-derives from the
       stamped ``job_identity``; a record with no digest is incomplete, which
       is what makes every record made before this field existed re-run
       (harness plan amendment 17: ``--resume`` cannot cross a schema change);

    and then the completeness contract itself (:func:`missing_fields`).
    """
    if record.get("status") != "ok":
        return f"status is {record.get('status')!r}, not 'ok'"
    for name in READABLE_IDENTITY_FIELDS:
        stamped = record.get(IDENTITY_FIELDS_STAMPED_BY_THE_CHILD[name])
        if stamped != identity.get(name):
            return (
                f"{IDENTITY_FIELDS_STAMPED_BY_THE_CHILD[name]} is {stamped!r}, "
                f"the job's {name} is {identity.get(name)!r}"
            )
    for name, child_name in IDENTITY_FIELDS_STAMPED_BY_THE_CHILD.items():
        wanted = identity.get(name, IDENTITY_DEFAULTS_WHEN_ABSENT.get(name))
        # A child stamp that is absent from the record means the default
        # (the record was made before the stamp existed): the same rule as
        # the identity's own absence, applied to the child's half.
        stamped = (
            record.get(child_name)
            if child_name in record
            else IDENTITY_DEFAULTS_WHEN_ABSENT.get(name)
        )
        if stamped != wanted:
            return (
                f"the child stamped {child_name}={record.get(child_name)!r} "
                f"and the job's {name} is {wanted!r}"
            )
    stamped_identity = record.get("job_identity")
    if not isinstance(stamped_identity, Mapping):
        return "the record carries no job_identity (made before the field existed)"
    for name in identity:
        if stamped_identity.get(name) != identity[name]:
            return (
                f"job_identity.{name} is {stamped_identity.get(name)!r} in the "
                f"record and {identity[name]!r} in the job"
            )
    extra = sorted(set(stamped_identity) - set(identity))
    if extra:
        return f"job_identity carries fields the job does not: {extra}"
    stamped_digest = record.get("job_digest")
    if not isinstance(stamped_digest, str):
        return "the record carries no job_digest (made before the field existed)"
    if stamped_digest != digest:
        return f"job_digest is {stamped_digest[:12]}…, the job's is {digest[:12]}…"
    rederived = job_digest(stamped_identity)
    if rederived != stamped_digest:
        return (
            f"job_digest {stamped_digest[:12]}… does not re-derive from the "
            f"stamped job_identity ({rederived[:12]}…)"
        )
    absent = missing_fields(record)
    if absent:
        return f"{len(absent)} declared field(s) missing: {', '.join(absent[:6])}"
    return None


def is_complete_for(
    record: Mapping[str, Any], *, identity: Mapping[str, Any], digest: str
) -> bool:
    """Whether *record* is a finished record of exactly this job.

    The predicate ``pool.run`` consults under ``--resume``; the reasons are in
    :func:`why_not_complete_for`.  *identity* is ``Job.identity(runs_dir)`` and
    *digest* is :func:`job_digest` of it — both the pool's construction, handed
    in rather than recomputed here so that this module never imports the pool.
    """
    return why_not_complete_for(record, identity=identity, digest=digest) is None


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
