"""The driver's switch vocabulary as data, and the capability probe.

Derived from ``arch_surgery/idf_probe/run_a28.py::_ARCH_VARS`` and
``arch_surgery/MDA_partitioning_experiment_v3/v3_runner.py::_ALL_ARCH_VARS``
at ``f2dc9243`` (task A47), and from the driver's own module-level switch
definitions in ``process/core/caller.py``,
``process/core/solver/module_solve.py`` and ``process/core/solver/subsolve.py``
read at the same commit.

Three things live here and nowhere else.

**The vocabulary.**  One :class:`Switch` per thing the driver can be told to
do: the term V4 uses for it, the environment variable the tree *currently*
implements, the name it is intended to carry once the rename lands, its legal
values, whether an arm composes it or the harness only clears it, and how to
read back what the driver actually resolved.  When the rename happens this
file is the only one that changes.

**The clearing discipline.**  Every known variable is removed before an arm is
composed (V3's ``_ALL_ARCH_VARS``), so an inherited value can never change
what is measured without saying so.

**The capability probe.**  A child process imports the driver under a given
environment and reports what it resolved.  It replaces V3's hand-edited
``INSTRUMENTATION`` ledger of booleans, which said what a human believed the
tree could do and was consulted on one code path and not the other.  A switch
the tree does not implement is *ignored* by the driver: the run succeeds, and
measures a different arm under the right name.  That is the failure this
module exists to make impossible — the same shape as trap T6 (a worktree does
not redirect the editable install) and trap T10 (a version string agreeing
with the wrong answer).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping, MutableMapping

CALLER = "process.core.caller"
MODULE_SOLVE = "process.core.solver.module_solve"
SUBSOLVE = "process.core.solver.subsolve"
#: The solver package itself, which carries the typed refusal and the list of
#: switch names this revision retired.
SOLVER = "process.core.solver"
#: The solver handler, which is where the optimiser's retry ladder lives.
SOLVER_HANDLER = "process.core.solver.solver_handler"


# --------------------------------------------------------------------------
# the record
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Switch:
    """One thing the driver can be told to do."""

    #: V4's term for it (V4 README §3; this README §3's switch table), used as the key everywhere in the harness.
    term: str
    #: Environment variable the tree implements *today*, or None when the
    #: capability does not exist yet and an approved driver change will add it.
    driver_name: str | None
    #: The name it is intended to carry.  None when the switch is intended to
    #: disappear rather than be renamed.
    intended_name: str | None
    #: "enum" | "path" | "number" | "hexfloat" | "csv"
    value_kind: str
    #: Legal values for an enum switch; empty otherwise.  The driver's own
    #: default (the variable unset) is not listed.
    values: tuple[str, ...]
    #: True when an arm composes it; False when the harness only clears it.
    composed: bool
    #: ``(module, attribute)`` pairs a child process reads back to say what the
    #: driver resolved.
    readbacks: tuple[tuple[str, str], ...]
    #: ``(resolved, requested) -> bool``: did the driver resolve as asked?
    resolved_as_asked: Callable[[Mapping[str, object], str], bool] = field(
        compare=False, repr=False, default=lambda resolved, value: True
    )
    #: Names that must never appear in a composed environment, each with the
    #: reason it was retired.  A stale caller setting a retired name would run
    #: the wrong arm under the right name; this is the guard against that, and
    #: the driver carries the same list so that the refusal happens there too.
    retired_names: Mapping[str, str] = field(default_factory=dict)
    #: The driver change that will supply or rename it, for the refusal message.
    pending_change: str = ""
    note: str = ""

    @property
    def implemented(self) -> bool:
        """Whether any tree can be asked for this at all today."""
        return self.driver_name is not None


def _resolved(resolved: Mapping[str, object], module: str, attribute: str):
    return resolved.get(f"{module}.{attribute}", _MISSING)


class _Missing:
    def __repr__(self) -> str:  # pragma: no cover - display only
        return "<not implemented by this tree>"


_MISSING = _Missing()


# --------------------------------------------------------------------------
# the registry
# --------------------------------------------------------------------------
#
# Row order is the order of EXPERIMENT_REPORT.md §3.2's switch list, then the
# switches an arm never composes.  Every legal value below was read from the
# driver's own guard tables, not from a document: an unrecognised value is an
# import-time error in the driver, so a wrong spelling here is refused rather
# than run.

REGISTRY: dict[str, Switch] = {
    "mda": Switch(
        term="mda",
        driver_name="PROCESS_ARCH_MDA",
        intended_name="PROCESS_ARCH_MDA",
        value_kind="enum",
        values=("flat", "partitioned"),
        composed=True,
        readbacks=(
            (MODULE_SOLVE, "MDA_MODE"),
            (MODULE_SOLVE, "ENABLED"),
            (MODULE_SOLVE, "FLAT"),
        ),
        resolved_as_asked=lambda r, v: _resolved(r, MODULE_SOLVE, "MDA_MODE") == v,
        retired_names={
            "PROCESS_ARCH_MODULE_SOLVE": (
                "renamed: the shape of the analysis loop is PROCESS_ARCH_MDA, "
                "and its values are flat and partitioned rather than "
                "flat_state and per_module"
            ),
            "PROCESS_ARCH_OUTER": (
                "folded: the partitioned loop runs its block schedule once, "
                "which is what PROCESS_ARCH_MDA=partitioned now means.  The "
                "repeated schedule left with the arm that used it (D22), after "
                "its verification pass was measured triggering a further pass "
                "0 times in 91 888 evaluations"
            ),
        },
        note=(
            "Shape of the analysis loop: one block over every in-loop node "
            "(flat) or three block solves in feed-forward order "
            "(partitioned).  Unset is upstream's own loop, which is what the "
            "reference arms run.  Choosing 'partitioned' *is* choosing to run "
            "the block schedule once; there is no separate switch for that any "
            "more and setting the old one raises."
        ),
    ),
    "tolerance": Switch(
        term="tolerance",
        driver_name="PROCESS_ARCH_TAU",
        intended_name="PROCESS_ARCH_TAU",
        value_kind="number",
        values=(),
        composed=True,
        readbacks=((MODULE_SOLVE, "TAU"),),
        resolved_as_asked=lambda r, v: _resolved(r, MODULE_SOLVE, "TAU") == float(v),
        retired_names={
            "PROCESS_ARCH_INNER_TAU": (
                "D23 (user, 2026-09-10): one tolerance for every converger, so "
                "a second one cannot be set.  A run carrying it would report a "
                "block accuracy the campaign never declared"
            ),
        },
        note=(
            "The one tolerance of every converger (D23, the user's ruling of "
            "2026-09-10): the flat loop and each block loop alike, both "
            "phases, every arm."
        ),
    ),
    "coupling_state": Switch(
        term="coupling_state",
        driver_name="PROCESS_ARCH_COUPLING_STATE",
        intended_name="PROCESS_ARCH_COUPLING_STATE",
        value_kind="path",
        values=(),
        composed=True,
        readbacks=((MODULE_SOLVE, "COUPLING_STATE_PATH"),),
        resolved_as_asked=lambda r, v: _resolved(r, MODULE_SOLVE, "COUPLING_STATE_PATH") == v,
        retired_names={"PROCESS_ARCH_YSTATE": "renamed to PROCESS_ARCH_COUPLING_STATE"},
        note=(
            "The committed artifact naming the fields that make up the "
            "coupling state and the measured scale of each.  No default: "
            "another configuration's components would silently test the wrong "
            "thing."
        ),
    ),
    "write_sets": Switch(
        term="write_sets",
        driver_name="PROCESS_ARCH_WRITE_SETS",
        intended_name="PROCESS_ARCH_WRITE_SETS",
        value_kind="path",
        values=(),
        composed=True,
        readbacks=((MODULE_SOLVE, "WRITE_SETS_PATH"),),
        resolved_as_asked=lambda r, v: _resolved(r, MODULE_SOLVE, "WRITE_SETS_PATH") == v,
        retired_names={"PROCESS_ARCH_WRITESET": "renamed to PROCESS_ARCH_WRITE_SETS"},
        note=(
            "The committed artifact naming which coupling-state components "
            "each block writes.  Since DR11 a block loop tests this subset "
            "under the fallback test set only; the block trace and the exit "
            "audit read it under both."
        ),
    ),
    "test_set": Switch(
        term="test_set",
        driver_name="PROCESS_ARCH_TEST_SET",
        intended_name="PROCESS_ARCH_TEST_SET",
        value_kind="enum",
        values=("census", "write_set"),
        composed=True,
        readbacks=((MODULE_SOLVE, "TEST_SET"),),
        resolved_as_asked=lambda r, v: _resolved(r, MODULE_SOLVE, "TEST_SET") == v,
        note=(
            "Which components every block loop tests (driver change DR11, "
            "task A100 (v5-test-set)): 'census', the read-before-write set "
            "measured at run time per loop and block (decision D32, the V5 "
            "default), or 'write_set', the block's whole write set -- exactly "
            "V4's predicate, kept as the fallback (decision D39).  A "
            "campaign-level value composed into every arm the loop runs in; "
            "never a matrix cell, never mixed within a campaign; the "
            "tolerance follows it (config.TAU_BY_TEST_SET) unless overridden.  "
            "Required by the driver whenever the loop is on, so no run relies "
            "on a default."
        ),
    ),
    "test_sets": Switch(
        term="test_sets",
        driver_name="PROCESS_ARCH_TEST_SETS",
        intended_name="PROCESS_ARCH_TEST_SETS",
        value_kind="path",
        values=(),
        composed=True,
        readbacks=((MODULE_SOLVE, "TEST_SETS_PATH"),),
        resolved_as_asked=lambda r, v: _resolved(r, MODULE_SOLVE, "TEST_SETS_PATH") == v,
        note=(
            "The committed census test-set artifact of the configuration "
            "(harness/data/test_sets_<configuration>.json), keyed by loop "
            "('<mda>/<burn-time owner>').  Composed with test_set=census only; "
            "the driver refuses it with the fallback and refuses the census "
            "value without it."
        ),
    ),
    "arrangement_node": Switch(
        term="arrangement_node",
        driver_name="PROCESS_ARCH_ARRANGEMENT_NODE",
        intended_name="PROCESS_ARCH_ARRANGEMENT_NODE",
        value_kind="enum",
        values=("build_after_physics",),
        composed=True,
        readbacks=(
            (CALLER, "ARRANGEMENT_NODE_NAME"),
            (CALLER, "ARRANGEMENT_NODE_HEAD"),
        ),
        resolved_as_asked=lambda r, v: _resolved(r, CALLER, "ARRANGEMENT_NODE_NAME") == v,
        retired_names={"PROCESS_ARCH_SEQUENCE": "renamed to PROCESS_ARCH_ARRANGEMENT_NODE"},
        note=(
            "When a node runs: 'build' moved after 'physics' so the physics "
            "block is contiguous in the call order.  A permutation of three "
            "existing calls; no model changes."
        ),
    ),
    "arrangement_method": Switch(
        term="arrangement_method",
        driver_name="PROCESS_ARCH_ARRANGEMENT_METHOD",
        intended_name="PROCESS_ARCH_ARRANGEMENT_METHOD",
        value_kind="enum",
        values=("fw_geometry",),
        composed=True,
        readbacks=(
            (CALLER, "ARRANGEMENT_METHOD_NAME"),
            (CALLER, "ARRANGEMENT_METHOD_FW_GEOMETRY"),
        ),
        resolved_as_asked=lambda r, v: _resolved(r, CALLER, "ARRANGEMENT_METHOD_NAME") == v,
        retired_names={"PROCESS_ARCH_PRIME": "renamed to PROCESS_ARCH_ARRANGEMENT_METHOD"},
        note=(
            "When a method runs: the run-constant first-wall geometry method "
            "executed at the head of every sweep, so 'build' reads this "
            "pass's thickness instead of the previous pass's."
        ),
    ),
    "defer_per_call": Switch(
        term="defer_per_call",
        driver_name="PROCESS_ARCH_DEFER_PER_CALL",
        intended_name="PROCESS_ARCH_DEFER_PER_CALL",
        value_kind="enum",
        values=("feedforward", "feedforward_lifted"),
        composed=True,
        readbacks=(
            (CALLER, "DEFER_PER_CALL_NAME"),
            (CALLER, "DEFER_PER_CALL_ENABLED"),
            (CALLER, "DEFER_PER_CALL_NODES"),
        ),
        resolved_as_asked=lambda r, v: _resolved(r, CALLER, "DEFER_PER_CALL_NAME") == v,
        retired_names={"PROCESS_ARCH_HOIST": "renamed to PROCESS_ARCH_DEFER_PER_CALL"},
        note=(
            "How often a node runs: once per evaluation of the model set "
            "instead of once per sweep.  'feedforward_lifted' additionally "
            "defers the burn-time node, which is only correct once the burn "
            "time has left the loop — the driver refuses the combination "
            "otherwise.  The two value names are the driver's own and the "
            "terminology table names no replacements for them, so they stay."
        ),
    ),
    "defer_per_run": Switch(
        term="defer_per_run",
        driver_name="PROCESS_ARCH_DEFER_PER_RUN",
        intended_name="PROCESS_ARCH_DEFER_PER_RUN",
        value_kind="path",
        values=(),
        composed=True,
        readbacks=((CALLER, "DEFER_PER_RUN_PATH"), (CALLER, "DEFER_PER_RUN_ENABLED")),
        resolved_as_asked=lambda r, v: _resolved(r, CALLER, "DEFER_PER_RUN_PATH") == v,
        retired_names={"PROCESS_ARCH_POST_SOLVE": "renamed to PROCESS_ARCH_DEFER_PER_RUN"},
        note=(
            "How often a node runs: once in total, at the accepted optimum.  "
            "The value is the committed artifact naming that node set; there "
            "is no default, because a run asked to defer nodes must refuse "
            "rather than quietly run all of them."
        ),
    ),
    "defer_per_run_execution": Switch(
        term="defer_per_run_execution",
        driver_name="PROCESS_ARCH_DEFER_PER_RUN_EXECUTION",
        intended_name="PROCESS_ARCH_DEFER_PER_RUN_EXECUTION",
        value_kind="enum",
        values=("output_path", "evaluation_exit"),
        composed=True,
        readbacks=(
            (CALLER, "DEFER_PER_RUN_EXECUTION"),
            (CALLER, "DEFER_PER_RUN_AT_EVALUATION_EXIT"),
        ),
        resolved_as_asked=lambda r, v: _resolved(r, CALLER, "DEFER_PER_RUN_EXECUTION") == v,
        note=(
            "WHERE the per-run deferred set is executed once (V5 list item 5, "
            "task A101 (v5-timers-and-once); decision D35): 'output_path' "
            "(unset), at the entry to write_output_files after the optimiser "
            "has accepted -- the optimisation phase's place, unchanged -- or "
            "'evaluation_exit', at the exit of every call_models on the "
            "converged state, so that an evaluation-phase run (one "
            "call_models, no output path) executes the set exactly once and "
            "its exit state carries what a flat evaluation's carries.  "
            "Composed by the evaluation phase's deferring arm only; the "
            "execution is one sweep of the dispatch body, counted like any "
            "other node call and sweep (measured, not charged; gate GC "
            "declares the counts it moves).  Not a matrix row: it follows "
            "from the phase and the per-run deferral."
        ),
    ),
    "burn_time_owner": Switch(
        term="burn_time_owner",
        driver_name="PROCESS_ARCH_BURN_TIME_OWNER",
        intended_name="PROCESS_ARCH_BURN_TIME_OWNER",
        value_kind="owner",
        values=("loop", "optimiser", "constant:<hex float>"),
        composed=True,
        readbacks=(
            (SUBSOLVE, "BURN_TIME_OWNER"),
            (SUBSOLVE, "BURN_TIME_CONSTANT"),
            (SUBSOLVE, "BURN_TIME_OUT_OF_LOOP"),
            (SUBSOLVE, "SITES"),
        ),
        resolved_as_asked=lambda r, v: _owner_resolved_as_asked(r, v),
        retired_names={
            "PROCESS_ARCH_LIFT": (
                "folded: taking the burn time out of the model is now said by "
                "naming its new owner — PROCESS_ARCH_BURN_TIME_OWNER=optimiser "
                "or =constant:<hex float>"
            ),
            "PROCESS_ARCH_PIN_BURN_TIME": (
                "folded: PROCESS_ARCH_BURN_TIME_OWNER=constant:<hex float> "
                "names the constant and takes the quantity out of the model in "
                "one setting, so the pair that could disagree no longer exists"
            ),
        },
        note=(
            "Who owns the burn time: the model's own loop (the default, and "
            "upstream's behaviour), the optimiser (a design variable), or a "
            "named constant, for the phase that has no optimiser to own it.  "
            "The constant is passed as a C99 hex float so a measured value "
            "survives the round trip exactly.  The driver refuses an input "
            "file that also names the burn time as an optimiser variable — two "
            "owners is a refusal, not a race."
        ),
    ),
    "output_loop": Switch(
        term="output_loop",
        driver_name="PROCESS_ARCH_OUTPUT_LOOP",
        intended_name="PROCESS_ARCH_OUTPUT_LOOP",
        value_kind="enum",
        values=("upstream", "none"),
        composed=True,
        readbacks=(
            (CALLER, "OUTPUT_LOOP_NAME"),
            (CALLER, "OUTPUT_PATH_NAME"),
        ),
        resolved_as_asked=lambda r, v: _resolved(r, CALLER, "OUTPUT_LOOP_NAME") == v,
        note=(
            "Upstream writes its output files through a second loop that "
            "re-solves the accepted state until the output stops changing.  "
            "The arms whose solve already handed over a state converged at "
            "the shared tolerance do not run it: 'none' calls the file-writing "
            "step once on the accepted state.  ``upstream`` is also the "
            "driver's behaviour with the variable unset, and is listed as a "
            "value because the reproduction gate sets it **explicitly** — an "
            "override that has to be read back is an override that can be "
            "checked, and one that relies on a default is not."
        ),
    ),
    "predicate_mode": Switch(
        term="predicate_mode",
        # **Retired** (task A98 (v5-reporting-trim), 2026-09-29; V5 list item
        # 10, D30's "or drop it").  No arm composes it: the frozen ruler is
        # what the variable unset means, and the 'mixed' trial (driver change
        # DR5, V4's gate G8) is dropped.  The name stays in the registry so
        # that it is **cleared** before every arm and **refused** if present
        # (``retired_names``); the driver's own ``RETIRED_SWITCHES`` entry
        # rides on DR11 (``RETIRED_PENDING_IN_DRIVER`` below).
        driver_name=None,
        intended_name=None,
        value_kind="enum",
        values=(),
        composed=False,
        readbacks=(),
        retired_names={
            "PROCESS_ARCH_PREDICATE": "dropped, D30 / item 10 (the 'mixed' ruler trial)",
        },
        note=(
            "Which denominator the convergence test scaled a step by: "
            "'frozen', the measured scale alone -- the driver's behaviour with "
            "the variable unset -- or 'mixed', the scale kept as a floor under "
            "the current magnitude.  V5 composes neither: the switch is "
            "retired and the frozen ruler is the one every arm runs under."
        ),
    ),
    "pass_trace": Switch(
        term="pass_trace",
        driver_name="PROCESS_ARCH_PASS_TRACE",
        intended_name="PROCESS_ARCH_PASS_TRACE",
        value_kind="path",
        values=(),
        composed=False,
        readbacks=((MODULE_SOLVE, "PASS_TRACE_PATH"), (MODULE_SOLVE, "TRACE_ENABLED")),
        note=(
            "A per-pass residual trace.  A debugging instrument the "
            "experiment publishes nothing from: cleared before every arm so "
            "an inherited value cannot add work, never composed."
        ),
    ),
    "pass_trace_full_from": Switch(
        term="pass_trace_full_from",
        driver_name="PROCESS_ARCH_PASS_TRACE_FULL_FROM",
        intended_name="PROCESS_ARCH_PASS_TRACE_FULL_FROM",
        value_kind="number",
        values=(),
        composed=False,
        readbacks=((MODULE_SOLVE, "TRACE_FULL_FROM"),),
        note="Companion of the trace above; same treatment.",
    ),
    "timers": Switch(
        term="timers",
        driver_name="PROCESS_ARCH_TIMERS",
        intended_name="PROCESS_ARCH_TIMERS",
        value_kind="enum",
        values=("on",),
        composed=True,
        readbacks=((CALLER, "TIMERS_ENABLED"), (CALLER, "TIMERS_NAME")),
        resolved_as_asked=lambda r, v: _resolved(r, CALLER, "TIMERS_NAME") == v,
        note=(
            "The observation-only wall-clock timers (driver change DR12, task "
            "A101 (v5-timers-and-once); V5 list item 9; decisions D33, D38): "
            "with 'on' the driver accumulates per run the wall of every node "
            "call, every sweep, the convergence tests, the objective layer, "
            "every evaluation, the once-per-run set-up, the solve phase and "
            "the output path, with the epochs a launcher needs; the harness "
            "harvests them into the record's 'timers' block before its own "
            "audit sweep.  An INSTRUMENT, not an architecture switch: composed "
            "into every arm of a campaign that asks for it, the reference arms "
            "included (INSTRUMENT_SWITCHES); unset, every hook is one 'is None' "
            "test (gate G1); on, no count and no exit state moves (gate GC).  "
            "Context, never evidence."
        ),
    ),
    "block_trace": Switch(
        term="block_trace",
        driver_name="PROCESS_ARCH_BLOCK_TRACE",
        intended_name="PROCESS_ARCH_BLOCK_TRACE",
        value_kind="path",
        values=(),
        composed=False,
        readbacks=(
            (MODULE_SOLVE, "BLOCK_TRACE_PATH"),
            (MODULE_SOLVE, "BLOCK_TRACE_ENABLED"),
        ),
        note=(
            "A per-evaluation block trace (task A90 (m2-phasea-vs-phaseb)): per "
            "call_models, the evaluation kind the optimiser asked for, the "
            "design vector, and each block's sweeps with every sweep's "
            "residual split by module.  Observation only: cleared before "
            "every arm, never composed; a run that wants it passes it as a "
            "job's override_env, which makes it a different job identity "
            "from any campaign run.  Since driver change DR13 (A115 "
            "(v5-sweep-residual-trace)) every sweep is also scored on the "
            "block's census and non-census components, each part's worst "
            "component named, and the line carries the objective and the "
            "constraints as hex floats."
        ),
    ),
    "block_trace_census_sets": Switch(
        term="block_trace_census_sets",
        driver_name="PROCESS_ARCH_BLOCK_TRACE_CENSUS_SETS",
        intended_name="PROCESS_ARCH_BLOCK_TRACE_CENSUS_SETS",
        value_kind="path",
        values=(),
        composed=False,
        readbacks=((MODULE_SOLVE, "BLOCK_TRACE_CENSUS_PATH"),),
        note=(
            "Driver change DR13 (A115 (v5-sweep-residual-trace)): the census "
            "test-set artifact the block trace splits a write-set loop's "
            "score by.  Observation only, read by the trace alone; refused "
            "without the block trace and under the census test set.  Cleared "
            "before every arm, never composed; the traced-run stage "
            "(harness/traced_runs.py) passes it in a job's override_env."
        ),
    ),
}


def _owner_resolved_as_asked(resolved: Mapping[str, object], value: str) -> bool:
    """Did the driver resolve the burn time's owner exactly as asked?

    ``constant:<hex>`` is checked on the **value** as well as the owner: a
    driver that took the owner and dropped the number would otherwise pass.
    """
    owner = _resolved(resolved, SUBSOLVE, "BURN_TIME_OWNER")
    if value.startswith("constant:"):
        constant = _resolved(resolved, SUBSOLVE, "BURN_TIME_CONSTANT")
        try:
            wanted = float.fromhex(value.split(":", 1)[1])
        except ValueError:
            return False
        return owner == "constant" and isinstance(constant, float) and constant == wanted
    return owner == value


#: Switches that are **instruments, not architecture**: composed into an arm
#: without making it a different arrangement, the reference arms included,
#: and left out of every check that reads "which architecture switches are
#: set" (the reference arm composes to every architecture switch cleared).
INSTRUMENT_SWITCHES: tuple[str, ...] = ("timers",)


#: Module-level names the driver exposes that are **counters, not switches**:
#: nothing sets them, an arm never composes them, and they carry no environment
#: variable.  They are listed here, beside the switch registry, for one reason:
#: :func:`default_readbacks` feeds the capability probe, and a tree that does
#: not expose a counter the harness is about to record should say so in the
#: probe's report rather than have the harness discover a ``None`` in a record
#: afterwards.  ``Switch`` is the wrong shape for them — a Switch with no
#: driver name is a capability the tree *lacks*, which is refused, and these
#: are capabilities it *has*.
#:
#: Every entry is a ``(module, attribute)`` pair, in the same shape as a
#: switch's readbacks.  Added by task A58 (driver-predicate-counters): before
#: it, ``OUTPUT_LOOP_SWEEPS`` and the sweep counter were read by name in
#: ``child.py`` and named nowhere else, so nothing checked that the tree under
#: test had them.
DIAGNOSTIC_READBACKS: tuple[tuple[str, str], ...] = (
    (CALLER, "NODE_CALLS"),
    (CALLER, "NODE_CALLS_AT_OUTPUT"),
    (CALLER, "ARRANGEMENT_METHOD_CALLS"),
    # DR9 (A99 (v5-schedule-and-prime)): the once-per-run schedule stamp the
    # record carries as ``schedule_resolution``; probed so a tree lacking it
    # is reported before a record is found with a null in it (A99's proposal
    # 3, applied by A100 (v5-test-set)).
    (CALLER, "SCHEDULE_RESOLUTION"),
    # DR11 (A100 (v5-test-set)): the once-per-run stamp of what the block
    # loops tested, carried into the record as ``loop_test_sets``.
    (MODULE_SOLVE, "LOOP_TEST_SETS"),
    # DR12 (A101 (v5-timers-and-once)): the timers' accumulators, None with
    # the switch unset; probed so a tree lacking the instrument is reported
    # before a record is found with the block missing.
    (CALLER, "TIMERS"),
    (CALLER, "DISPATCH_SWEEPS"),
    (CALLER, "SWEEPS_PER_EVAL_HIST"),
    (CALLER, "OUTPUT_LOOP_SWEEPS"),
    (CALLER, "OUTPUT_PATH_ENTRIES"),
    (CALLER, "PREDICATE_EVALUATIONS"),
    (CALLER, "COMPONENTS_COMPARED"),
    (CALLER, "PREDICATE_EVALUATIONS_BY_BLOCK"),
    (CALLER, "COMPONENTS_COMPARED_BY_BLOCK"),
    (CALLER, "BLOCK_VISITS"),
    (CALLER, "EMPTY_BLOCK_VISITS"),
    (CALLER, "EMPTY_BLOCK_SWEEPS"),
    (CALLER, "UPSTREAM_PREDICATE_EVALUATIONS"),
    (CALLER, "UPSTREAM_COMPONENTS_COMPARED"),
    # Added by task A60 (driver-attempts): the retry ladder's boundary stamps,
    # the solve-phase sweep total they add up to, and the ladder's own names
    # for its rungs.  The last is not a counter but it is read back for the
    # same reason — a tree whose ladder has gained a rung the harness does not
    # know about should say so in the probe's report, not in a table nobody
    # can explain afterwards.
    (CALLER, "ATTEMPT_STAMPS"),
    (CALLER, "ATTEMPT_LADDERS"),
    (CALLER, "DISPATCH_SWEEPS_AT_OUTPUT"),
    (SOLVER_HANDLER, "LADDER_STAGES"),
)


#: Instrumentation variables that are not architecture switches: they select
#: and tune the in-driver probe.  Cleared before every arm for the same reason
#: the switches are — an inherited one changes what a run does — and never
#: composed by an arm.  Read from ``process/core/_idf_probe*.py``.
PROBE_VARIABLES: tuple[str, ...] = (
    "PROCESS_IDF_PROBE",
    "PROCESS_IDF_PROBE_OUT",
    "PROCESS_IDF_PROBE_READ_BUDGET",
    "PROCESS_IDF_PROBE_READ_STRIDE",
    "PROCESS_IDF_PROBE_FROZEN_GRAD_STRIDE",
    "PROCESS_IDF_PROBE_FROZEN_OTHER_STRIDE",
    "PROCESS_IDF_PROBE_FROZEN_MAX_SUBSWEEPS",
    "PROCESS_IDF_PROBE_FROZEN_NOINJECT",
    "PROCESS_IDF_PROBE_FROZEN_TRACE",
    "PROCESS_IDF_PROBE_HARVEST_OUT",
    "PROCESS_IDF_PROBE_HARVEST_GRAD_STRIDE",
    "PROCESS_IDF_PROBE_HARVEST_MAX_POINTS",
    "PROCESS_IDF_PROBE_HARVEST_ALL_POINTS",
)


#: Arms the earlier revision (V3) ran under different names: V3's name -> V4's.
#: A lookup that misses raises: a reference a gate cannot find must refuse,
#: never pass over an empty comparison (trap T11).  The keys are **V3's**
#: spellings: since the renaming of 2026-09-15 (``records.RECORDED_ARM_NAMES``)
#: V4's partitioned evaluation arm is ``A2`` (V3 called it ``A1``) and its
#: partitioned optimisation arm is ``B2`` (V3 called it ``B3``); V4's ``A1``
#: is the flat arm with a constant owning the burn time, which V3 never ran
#: (``reference.ARMS_WITHOUT_PREVIOUS_RECORDS``).
PREVIOUS_ARM_NAMES: dict[str, str] = {"R": "BR", "A1": "A2", "B3": "B2"}

#: Arms the earlier revision (V3) ran that V4 does not, **in V3's spellings**:
#: ``A1u`` was the prime-free counterfactual, retired with the prime's own
#: gate; V3's ``B2`` — the joint-test arm, which repeated the block schedule —
#: measured nothing the exit audit does not (D22) and was removed.  V4's own
#: ``B2`` is a different arm (the partitioned optimisation arm, V3's ``B3``)
#: and shares nothing with it but the spelling; the self-check compares by
#: what each V4 arm was called in V3, never by the bare string.
RETIRED_ARM_NAMES: tuple[str, ...] = ("A1u", "B2")


def all_names() -> tuple[str, ...]:
    """Every environment variable the harness knows about, current and future.

    Cleared before composing an arm: current names because they change what
    the driver does, intended names because a tree that already implements one
    would pick up an inherited value, retired names because a stale one would
    run the wrong arm under the right name.
    """
    names: list[str] = []
    for sw in REGISTRY.values():
        names.extend(
            n
            for n in (sw.driver_name, sw.intended_name, *sw.retired_names)
            if n is not None
        )
    names.extend(PROBE_VARIABLES)
    return tuple(dict.fromkeys(names))


def retired_names() -> dict[str, str]:
    """Names that must never appear in a composed environment, and why.

    The driver carries the same list (``process.core.solver.RETIRED_SWITCHES``)
    and refuses on it too.  The two are checked against each other by the
    capability probe rather than assumed equal: a harness that cleared a name
    the driver still honoured, or refused one the driver had never heard of,
    would be describing a tree it is not running.  The one licensed
    difference is :data:`RETIRED_PENDING_IN_DRIVER`.
    """
    return {
        name: because
        for sw in REGISTRY.values()
        for name, because in sw.retired_names.items()
    }


#: Names the **harness** has retired that the **driver** has not yet: each
#: with the driver change that carries its retirement.  The interim is
#: declared here so that the capability self-check can tolerate it by name
#: and nothing else: the check requires the driver's ``RETIRED_SWITCHES`` to
#: equal the registry's list **minus** these, and requires every name here to
#: be **absent** from the driver's list — so the day the driver change lands,
#: this table must be emptied in the same commit or the check fails, and the
#: interim cannot outlive the change silently.  While a name is here the
#: driver still honours it; the harness clears it before every arm
#: (``all_names``) and refuses it if present (``assert_no_retired``), so no run
#: made through the harness can carry it.
#:
#: **Empty since DR11** (task A100 (v5-test-set)): ``PROCESS_ARCH_PREDICATE``
#: was the one entry (retired on the harness side by A98 (v5-reporting-trim))
#: and the driver retired it in the same commit that removed the ``mixed``
#: ruler (V5 plan §11, the DR11 addition; §12 Q5).  The mechanism stays for
#: the next two-task retirement.
RETIRED_PENDING_IN_DRIVER: dict[str, str] = {}


#: How the previous revision spelled each switch: its variable name -> V4's
#: term for the same **role**.  Used only where a V4 environment has to be
#: compared with one the previous revision composed (the self-check's
#: composition comparison).  A name missing from this map is a name the
#: previous revision did not have.
PREVIOUS_SWITCH_NAMES: dict[str, str] = {
    "PROCESS_ARCH_MODULE_SOLVE": "mda",
    "PROCESS_ARCH_OUTER": "schedule_passes",
    "PROCESS_ARCH_TAU": "tolerance",
    "PROCESS_ARCH_INNER_TAU": "inner_tolerance",
    "PROCESS_ARCH_YSTATE": "coupling_state",
    "PROCESS_ARCH_WRITESET": "write_sets",
    "PROCESS_ARCH_SEQUENCE": "arrangement_node",
    "PROCESS_ARCH_PRIME": "arrangement_method",
    "PROCESS_ARCH_HOIST": "defer_per_call",
    "PROCESS_ARCH_POST_SOLVE": "defer_per_run",
    "PROCESS_ARCH_LIFT": "burn_time_lift",
    "PROCESS_ARCH_PIN_BURN_TIME": "burn_time_constant",
    "PROCESS_ARCH_PASS_TRACE": "pass_trace",
    "PROCESS_ARCH_PASS_TRACE_FULL_FROM": "pass_trace_full_from",
}

#: Values the previous revision spelled differently for the same role.
PREVIOUS_VALUES: dict[str, dict[str, str]] = {
    "mda": {"flat_state": "flat", "per_module": "partitioned"},
}


class RoleError(RuntimeError):
    """An environment that cannot be read as a set of roles.  Never ignored."""


def canonical_roles(
    env: Mapping[str, str], *, revision: str = "current"
) -> dict[str, str]:
    """*env* as ``role -> value``, in the vocabulary of the current revision.

    This is what makes two revisions' compositions comparable **by what they
    ask the driver to do** rather than by how they spell it.  Equality of the
    two results means the same role carries the same value on both sides, which
    is the claim a rename has to support: ``OUTER=trust`` with
    ``MODULE_SOLVE=per_module`` on the previous revision's side and
    ``MDA=partitioned`` on ours are the *same request*, and comparing the raw
    variable names would call them different.

    Two foldings happen here, and both can fail rather than paper over a
    difference:

    * the previous revision's ``OUTER`` is dropped **only** where its value is
      the one the partitioned loop now implies; any other combination becomes
      an explicit ``schedule_passes`` role, so the comparison fails and says
      why;
    * its two burn-time settings become one ``burn_time_owner`` value, and a
      pin without the lift -- which that revision refused at import -- is a
      refusal here too rather than a silently different owner.
    """
    if revision not in ("current", "previous"):
        raise RoleError(f"{revision!r} is neither 'current' nor 'previous'")
    if revision == "current":
        roles = {}
        for term, sw in REGISTRY.items():
            if sw.driver_name and sw.driver_name in env:
                roles[term] = env[sw.driver_name]
            elif sw.intended_name and sw.intended_name in env:
                roles[term] = env[sw.intended_name]
        return roles

    roles: dict[str, str] = {}
    for name, value in env.items():
        term = PREVIOUS_SWITCH_NAMES.get(name)
        if term is None:
            continue
        roles[term] = PREVIOUS_VALUES.get(term, {}).get(value, value)

    # the burn time's owner, from the two settings that used to say it
    lifted = roles.pop("burn_time_lift", None)
    constant = roles.pop("burn_time_constant", None)
    if constant is not None:
        if lifted is None:
            raise RoleError(
                "the previous revision's environment names a constant burn "
                "time without lifting the site, which that revision refused at "
                "import; it has no reading as a burn-time owner"
            )
        roles["burn_time_owner"] = f"constant:{constant}"
    elif lifted is not None:
        roles["burn_time_owner"] = "optimiser"

    # the schedule passes, which the partitioned loop now implies
    passes = roles.pop("schedule_passes", None)
    if passes is not None and not (
        passes == "trust" and roles.get("mda") == "partitioned"
    ):
        roles["schedule_passes"] = passes
    return roles


def previous_revision_roles() -> frozenset[str]:
    """Every role the previous revision's environment could express.

    **Measured from the composer, not listed.**  An environment setting every
    name that revision had is put through :func:`canonical_roles`, and what
    comes out is what it could say.  That matters because the map from a name
    to a role is not one to one: two of its names fold into one role of ours
    (the burn time's owner), and one of them folds away entirely (how often the
    block schedule runs), so the map's *values* are not the roles.

    The caller is the composition check, which compares this revision's request
    with the previous one's role by role.  A role that is **not** in this set is
    a capability the driver has gained since -- the output path is one -- and
    comparing it against a side that could not express it would report a
    capability as a disagreement.  A role that *is* in this set can never be
    set aside, which is what keeps that exception from becoming a place to hide
    a real difference.
    """
    probe = {name: "probe" for name in PREVIOUS_SWITCH_NAMES}
    # A consistent pair for the fold: that revision refused a constant burn
    # time without the site taken out of the loop, and so does the fold.
    probe["PROCESS_ARCH_LIFT"] = "burn_time"
    probe["PROCESS_ARCH_PIN_BURN_TIME"] = "0x1.0p+0"
    # The schedule value the partitioned loop now implies, so the fold that
    # drops it is exercised rather than stepped around.
    probe["PROCESS_ARCH_MODULE_SOLVE"] = "per_module"
    probe["PROCESS_ARCH_OUTER"] = "trust"
    return frozenset(canonical_roles(probe, revision="previous"))


def clear_all(env: MutableMapping[str, str]) -> MutableMapping[str, str]:
    """Remove every known variable from *env*, in place, and return it."""
    for name in all_names():
        env.pop(name, None)
    return env


def assert_no_retired(env: Mapping[str, str]) -> None:
    """Raise if *env* carries a name V4 has retired."""
    retired = retired_names()
    present = sorted(name for name in retired if name in env)
    if present:
        raise SwitchError(
            "the composed environment carries retired "
            + ", ".join(f"{n} ({retired[n]})" for n in present)
        )


class SwitchError(RuntimeError):
    """A composition or capability refusal.  Never degraded into a warning."""


# --------------------------------------------------------------------------
# the capability probe
# --------------------------------------------------------------------------

#: The child program.  It imports the driver under the environment it inherits
#: and prints what the driver resolved.  Module-level names only: nothing is
#: run, no model is called, no output file is opened.  ``process.__file__`` is
#: reported so the caller can assert the exact tree (trap T6) — and the
#: version string is never consulted (trap T10: a frozen archive's version
#: agrees with the wrong commit).
_PROBE_SOURCE = r"""
import importlib, json, sys

SENTINEL = "@@HARNESS-PROBE@@"
spec = json.loads(sys.stdin.read())


def coerce(v):
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    if isinstance(v, (set, frozenset)):
        return sorted(str(x) for x in v)
    if isinstance(v, (list, tuple)):
        return [coerce(x) for x in v]
    if isinstance(v, dict):
        return {str(k): coerce(x) for k, x in v.items()}
    return repr(v)


out = {"resolved": {}, "missing": [], "ok": True, "error": None}
try:
    import process

    out["process_file"] = process.__file__
    for module, attrs in spec.items():
        m = importlib.import_module(module)
        for attr in attrs:
            key = module + "." + attr
            if hasattr(m, attr):
                out["resolved"][key] = coerce(getattr(m, attr))
            else:
                out["missing"].append(key)
except BaseException as exc:
    out["ok"] = False
    out["error"] = type(exc).__name__ + ": " + str(exc)

sys.stdout.write(SENTINEL + json.dumps(out) + SENTINEL)
"""

_SENTINEL = "@@HARNESS-PROBE@@"


@dataclass(frozen=True)
class Capability:
    """What one child process reported about one environment."""

    ok: bool
    resolved: Mapping[str, object]
    missing: tuple[str, ...]
    process_file: str | None
    error: str | None

    def value(self, module: str, attribute: str):
        return _resolved(self.resolved, module, attribute)


def probe(
    tree: Path,
    env: Mapping[str, str],
    *,
    readbacks: tuple[tuple[str, str], ...] | None = None,
    timeout: int = 300,
) -> Capability:
    """Import the driver from *tree* under *env* and report what it resolved.

    A fresh child process, because every switch is read once at import: the
    only way to ask "what would this environment do" is to be that process.
    """
    spec: dict[str, list[str]] = {}
    pairs = readbacks if readbacks is not None else default_readbacks()
    for module, attr in pairs:
        spec.setdefault(module, []).append(attr)
    child_env = dict(env)
    child_env["PYTHONPATH"] = str(tree)
    # **The current working directory must not be able to shadow PYTHONPATH.**
    # With ``-c``, Python puts the cwd at the head of ``sys.path``, ahead of
    # everything PYTHONPATH names -- so pressing the button from the repository
    # root made the probe import the *repository's* ``process/`` package while
    # the environment named the experiment's copy, and the check failed
    # honestly with a verdict that depended on where it was pressed.  Found by
    # the orchestrator at review.
    #
    # ``-P`` (Python 3.11+) is the fix: it stops the cwd being prepended and
    # leaves PYTHONPATH alone.  It used to travel with ``PYTHONSAFEPATH=1`` in
    # the environment, which says the same thing a second way; one is kept,
    # and the capability check's decoy tooth is what proves it holds.  ``-I``
    # would be wrong: it isolates the interpreter and drops PYTHONPATH, which
    # is the one thing this child needs.
    proc = subprocess.run(
        [sys.executable, "-P", "-c", _PROBE_SOURCE],
        input=json.dumps(spec),
        env=child_env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    body = proc.stdout.split(_SENTINEL)
    if len(body) < 3:
        return Capability(
            ok=False,
            resolved={},
            missing=(),
            process_file=None,
            error=(
                f"probe child produced no report (rc={proc.returncode}): "
                f"{(proc.stderr or proc.stdout or '').strip()[-600:]}"
            ),
        )
    raw = json.loads(body[1])
    return Capability(
        ok=bool(raw["ok"]),
        resolved=raw["resolved"],
        missing=tuple(raw["missing"]),
        process_file=raw.get("process_file"),
        error=raw.get("error"),
    )


def default_readbacks() -> tuple[tuple[str, str], ...]:
    """Every readback the registry names, deduplicated.

    Switches only.  :data:`DIAGNOSTIC_READBACKS` is deliberately **not** folded
    in here: this is what a run record's ``resolved_switches`` block is built
    from, and a counter's value is not a thing the driver *resolved* — putting
    one there would both duplicate it and hide it, since the neutrality gate
    excludes that whole block by name.  The counters are probed by
    :func:`counter_readbacks`, whose caller is the self-check.
    """
    pairs: list[tuple[str, str]] = []
    for sw in REGISTRY.values():
        pairs.extend(sw.readbacks)
    return tuple(dict.fromkeys(pairs))


def counter_readbacks() -> tuple[tuple[str, str], ...]:
    """The switch readbacks and the counters, for a probe that checks both."""
    return tuple(dict.fromkeys((*default_readbacks(), *DIAGNOSTIC_READBACKS)))


def unimplemented(terms: Mapping[str, str]) -> tuple[str, ...]:
    """Which of the composed *terms* no tree implements yet."""
    return tuple(
        term for term in terms if term in REGISTRY and not REGISTRY[term].implemented
    )


def assert_capable(
    tree: Path,
    terms: Mapping[str, str],
    env: Mapping[str, str],
    *,
    label: str = "",
    timeout: int = 300,
) -> Capability:
    """Refuse unless *tree* resolved every composed switch exactly as asked.

    *terms* maps the V4 term to the value the arm asked for.  Refusal, never
    degradation: a tree that does not implement a switch ignores it silently,
    runs to completion, and reports a different arm under the right name.
    """
    where = f" for {label}" if label else ""
    pending = unimplemented(terms)
    if pending:
        raise SwitchError(
            f"refusing{where}: this tree implements no switch for "
            + "; ".join(
                f"{t} (needs {REGISTRY[t].pending_change or 'a driver change'})"
                for t in pending
            )
        )
    assert_no_retired(env)
    cap = probe(tree, env, timeout=timeout)
    if not cap.ok:
        raise SwitchError(
            f"refusing{where}: the driver refused this environment at import "
            f"— {cap.error}"
        )
    for term, value in terms.items():
        sw = REGISTRY[term]
        for module, attr in sw.readbacks:
            if f"{module}.{attr}" not in cap.resolved:
                raise SwitchError(
                    f"refusing{where}: the tree at {tree} has no "
                    f"{module}.{attr}, so it cannot implement {term} "
                    f"({sw.driver_name}={value!r}).  A tree that ignores a "
                    f"switch runs a different arm under this arm's name."
                )
        if not sw.resolved_as_asked(cap.resolved, value):
            raise SwitchError(
                f"refusing{where}: asked for {sw.driver_name}={value!r} "
                f"({term}) but the driver resolved "
                + ", ".join(
                    f"{a}={cap.value(m, a)!r}" for m, a in sw.readbacks
                )
            )
    return cap


def base_environment(tree: Path, *, cache_dir: Path | None = None) -> dict[str, str]:
    """A copy of this process's environment with every known switch cleared.

    Nothing is assumed absent: V3's discipline, kept.  ``PYTHONPATH`` names
    the tree under test because the editable install points at the main
    checkout and a worktree does not redirect it (trap T6).  *cache_dir* is
    where the children's caches go: the top level of ``runs/``, shared by
    every run ID (``config.SHARED_CACHES``; ``Campaign.cache_dir``).
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = str(tree)
    if cache_dir is not None:
        env["MPLCONFIGDIR"] = str(Path(cache_dir) / "_mplconfig")
        # Issue I-31: without a cache directory numba writes its compiled
        # cache beside the imported modules, under the copied driver's
        # ``__pycache__`` directories — 122 gitignored files in a worktree
        # that only *read* the copy.  A harness **default**, beside the
        # matplotlib one: a caller that sets its own keeps it.
        env.setdefault("NUMBA_CACHE_DIR", str(Path(cache_dir) / "_numba_cache"))
    # Decision D38: every child is pinned to one thread, so a parallel pool
    # never oversubscribes the machine and no run's floating point depends on
    # how many threads numba or a BLAS happened to take.  Defaults beside the
    # cache directory: a caller that sets its own keeps it.
    env.setdefault("NUMBA_NUM_THREADS", "1")
    env.setdefault("OMP_NUM_THREADS", "1")
    clear_all(env)
    return env
