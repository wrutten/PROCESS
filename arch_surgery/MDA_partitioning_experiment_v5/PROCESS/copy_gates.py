"""Gates that prove this PROCESS copy is exactly what ``PROVENANCE.json`` claims.

V4 runs its own copy of the PROCESS package (decision D20 in the master
queue's decision register): the repository-root ``process/`` stays as the tree
V3's records were made against, and every V4 driver change is made here
instead.  A duplicated tree nobody checks is how a frozen model quietly stops
being frozen, so the copy comes with two gates, both implemented here and both
runnable at any later commit.

``copy-identity``
    Every file under ``PROCESS/process/`` is byte-identical to the same path at
    the **source commit** named in ``PROVENANCE.json``, except the permitted
    edits recorded there -- whose post-edit sha256 and whose exact hunks must
    match.  The file *set* is compared as well as the file contents, because a
    per-file hash loop that never compares the set passes on a removed and on
    an added file.

``frozen-physics`` (gate G0' of the harness implementation plan)
    Every file under ``PROCESS/process/models/`` has the sha256 it is supposed
    to have, where "supposed to" means: the byte content at the frozen base
    commit ``c0ae5b28`` (D5, the physics freeze), except for the model files
    the experiment has explicitly approved a structural edit to -- today
    exactly one, ``process/models/pulse.py`` under D14(b), whose expected
    content is pinned by sha256 as well, so a *further* edit to it fails too.

Both comparisons are made against the **commit**, read with ``git cat-file``,
never against a working tree: an uncommitted edit in the repository-root
``process/`` must not be able to ride along unnoticed, and a root-tree edit
must not be able to mask a copy-tree edit or the reverse.

Teeth (queue protocol section 12: a gate must be shown capable of failing
before its zeros are accepted).  Each gate is re-run against perturbed
*temporary copies* of the tree -- a one-byte change, a removed file, an added
file, and a change made to a file that is allowed to differ but in the wrong
place -- and each must FAIL.  The real tree is never modified.

New in A46 (process-copy); it derives from no earlier file.  A48
(harness-data) generalised the permitted-edit model from constant markers to
recorded hunks, so an edit that is not a constant is describable.  A56
(driver-renames) added three more permitted-edit files and taught the
edit-behaviour gate to name the per-run deferral switch and entry point per
side, because the rename means the two trees spell them differently.  A60
(driver-attempts) added the sixth, ``solver_handler.py``, where the optimiser's
retry ladder lives.  Stdlib
only, no PROCESS run, runs in seconds.

**Where the verdicts live.**  The three criteria here are registered in the
harness's gate registry (``harness/gates/registry.py``) as ``g0prime``,
``copy_identity`` and ``edit_behaviour``, each loading this module by path;
``experiment_runner.py --gate <name>`` runs them with the framework's commit
stamp, ordering and teeth, and writes the verdict under ``runs/gates/<name>/``.
This module's own command line is a second, thin entry to the same functions
for a reader who wants the copy checked from inside ``PROCESS/``: it prints and
exits, and **writes no record** -- the harness's verdict is the record.
(``edit-behaviour`` gained a tooth with that registration: the permitted edit
doctored in a throwaway copy must make the gate FAIL, ``run_edit_behaviour_tooth``.)

Usage
-----
    python copy_gates.py all                # every check below, with teeth
    python copy_gates.py copy-identity
    python copy_gates.py frozen-physics
    python copy_gates.py smoke-import       # PYTHONPATH selects the copy (trap T6)
    python copy_gates.py edit-behaviour     # the one non-comment edit, exercised
    python copy_gates.py provenance --force # regenerate PROVENANCE.json

Exit status: 0 every gate passed, 1 a gate or a tooth failed, 2 setup error.
"""

from __future__ import annotations

import argparse
import copy
import datetime as _dt
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
COPY_ROOT = HERE  # holds process/ and PROVENANCE.json
PROVENANCE = HERE / "PROVENANCE.json"
SOURCE_PREFIX = "process"
MODELS_PREFIX = "process/models"

@dataclass(frozen=True)
class PermittedEdit:
    """One recorded change the copy is permitted to carry.

    A46 (process-copy) recorded permitted edits as **constant markers**: a file
    was allowed to differ, and the record named the constants it re-pointed.
    That model has no place for an edit that is not a constant -- the existence
    check and the comments A48 (harness-data) adds are neither -- so the model
    is the **recorded hunk**: every permitted edit is described here, and
    ``PROVENANCE.json`` records the file's exact hunks and post-edit sha256
    whatever kind of edit produced them.  The gate compares those, so the
    description below is documentation and the hunks are the check.
    """

    #: What kind of change it is: ``path constant``, ``existence check`` or
    #: ``comment``.
    kind: str
    #: The constant, function or subject the edit is about.
    name: str
    #: What it does and why, in one sentence a reviewer can check against the
    #: hunk.
    description: str
    #: The task that made it, so the record says who as well as what.
    task: str
    #: For a path constant: what it resolved to before and after.
    was: str = ""
    now: str = ""

    def as_dict(self) -> dict:
        record = {
            "kind": self.kind,
            "name": self.name,
            "description": self.description,
            "task": self.task,
        }
        if self.was or self.now:
            record["was"] = self.was
            record["now"] = self.now
        return record


#: The complete set of files the copy is permitted to differ from its source
#: commit in, and every edit each of them carries.  Adding a row here is not
#: enough to make an edit legal -- ``PROVENANCE.json`` must be regenerated so
#: the expected hunks and post-edit sha256 are recorded and reviewable, and its
#: guard refuses unless the files that actually differ are exactly these.
PERMITTED_EDIT_FILES: dict[str, list[PermittedEdit]] = {
    "process/core/solver/__init__.py": [
        PermittedEdit(
            kind="new definition",
            name="ArchitectureRefusal",
            description=(
                "the typed refusal every driver-side refusal of an "
                "architecture setting raises, so a measurement harness can "
                "tell a refused run from a crashed one by the exception's "
                "type instead of by matching the text of its message"
            ),
            task="A56 (driver-renames)",
        ),
        PermittedEdit(
            kind="new definition",
            name="RETIRED_SWITCHES / assert_no_retired_switches",
            description=(
                "the eleven switch names the rename retired, each with the "
                "switch that replaced it, checked at the import of this "
                "package: a stale name that is merely ignored runs a "
                "different arrangement under the right name"
            ),
            task="A56 (driver-renames)",
        ),
    ],
    "process/core/solver/module_solve.py": [
        PermittedEdit(
            kind="path constant",
            name="YSTATE_MODULE_PATH",
            description=(
                "the coupling-state predicate is loaded by path; the copy "
                "loads the harness's own module instead of the repository's "
                "research tree"
            ),
            task="A46 (process-copy)",
            was='Path(__file__).resolve().parents[3] / "arch_surgery" / "fixedpoint" / "ystate.py"',
            now='Path(__file__).resolve().parents[4] / "harness" / "child" / "ystate.py"',
        ),
        PermittedEdit(
            kind="comment",
            name="the coupling-state artifact's name",
            description=(
                "the module docstring named the artifact by its path in the "
                "repository's shared data directory; it names the file the "
                "copy actually reads, and the constant's comment says the "
                "target exists and where its provenance is recorded"
            ),
            task="A48 (harness-data)",
        ),
        PermittedEdit(
            kind="switch rename",
            name="PROCESS_ARCH_MDA",
            description=(
                "the shape of the analysis loop takes its intended name and "
                "its intended values; the schedule, the predicate and the "
                "artifact loading are unchanged"
            ),
            task="A56 (driver-renames)",
            was="PROCESS_ARCH_MODULE_SOLVE=off | per_module | flat_state",
            now="PROCESS_ARCH_MDA=flat | partitioned (unset for upstream's own loop)",
        ),
        PermittedEdit(
            kind="switch retired",
            name="PROCESS_ARCH_OUTER",
            description=(
                "the schedule runs once, which is what the partitioned value "
                "now means, so the switch that chose between running it once "
                "and repeating it is gone, along with its mode table, its "
                "two composition refusals and the pass cap"
            ),
            task="A56 (driver-renames)",
        ),
        PermittedEdit(
            kind="switch retired",
            name="PROCESS_ARCH_INNER_TAU",
            description=(
                "one tolerance for every converger (decision D23), so the "
                "second one and the refusal that guarded its misuse are gone"
            ),
            task="A56 (driver-renames)",
        ),
        PermittedEdit(
            kind="switch rename",
            name="PROCESS_ARCH_COUPLING_STATE / PROCESS_ARCH_WRITE_SETS",
            description=(
                "the two committed artifacts a block loop reads take their "
                "intended names; the files, their validation and their "
                "cross-check are unchanged"
            ),
            task="A56 (driver-renames)",
            was="PROCESS_ARCH_YSTATE, PROCESS_ARCH_WRITESET",
            now="PROCESS_ARCH_COUPLING_STATE, PROCESS_ARCH_WRITE_SETS",
        ),
        PermittedEdit(
            kind="typed refusal",
            name="ArchitectureRefusal",
            description=(
                "every refusal of an architecture setting in this file raises "
                "the typed refusal instead of a bare RuntimeError"
            ),
            task="A56 (driver-renames)",
        ),
        PermittedEdit(
            kind="switch added",
            name="PROCESS_ARCH_PREDICATE",
            description=(
                "which denominator the coupling-state convergence test scales "
                "a step by becomes a driver choice: 'frozen', the measured "
                "scale alone and every earlier revision's ruler, or 'mixed', "
                "the conventional scaled step with that scale kept as a floor "
                "under the current magnitude.  Resolved once at import, "
                "guarded against a misspelling with a typed refusal, read "
                "back as PREDICATE_MODE, stamped into the loaded spec's "
                "provenance beside the tolerance -- the two together are what "
                "'converged' means -- and checked against the list the "
                "coupling-state module itself implements the first time that "
                "module is loaded.  Unset is 'frozen', which is upstream of "
                "this change line for line"
            ),
            task="A59 (driver-predicate-mode)",
            was="one ruler, not selectable and not named in any record",
            now="PROCESS_ARCH_PREDICATE=frozen | mixed (unset for frozen)",
        ),
        PermittedEdit(
            kind="switch added",
            name="PROCESS_ARCH_BLOCK_TRACE",
            description=(
                "an observation-only per-evaluation block trace: the switch, "
                "resolved once at import and refused with the analysis loop "
                "unset; the evaluation kind the optimiser's evaluator sets "
                "before each call; a helper that splits one sweep's residual "
                "by module (its maximum scaled step and whether the module's "
                "own components would still fail the test); and the JSONL "
                "writer.  Unset, nothing here runs and no float the run "
                "computes with is read or written"
            ),
            task="A90 (m2-phasea-vs-phaseb)",
            was="no per-evaluation, per-block record",
            now="PROCESS_ARCH_BLOCK_TRACE=<file> (unset for no trace)",
        ),
    ],
    "process/core/solver/subsolve.py": [
        PermittedEdit(
            kind="switch rename",
            name="PROCESS_ARCH_BURN_TIME_OWNER",
            description=(
                "the two settings that took the burn time out of the model "
                "and named its new holder are folded into one switch whose "
                "value says who owns it; the seam, the value returned and the "
                "tripwire are unchanged, and the refusal of a constant "
                "without the site taken out of the loop is gone because that "
                "combination can no longer be written down"
            ),
            task="A56 (driver-renames)",
            was="PROCESS_ARCH_LIFT=<site list> plus PROCESS_ARCH_PIN_BURN_TIME=<float>",
            now="PROCESS_ARCH_BURN_TIME_OWNER=loop | optimiser | constant:<hex float>",
        ),
    ],
    "process/core/solver/constraints.py": [
        PermittedEdit(
            kind="comment",
            name="constraint 93's docstring",
            description=(
                "the burn-time consistency constraint's docstring named the "
                "retired switch that used to take the burn time out of the "
                "model; it names the switch that does now.  Nothing the "
                "constraint computes changes"
            ),
            task="A56 (driver-renames)",
            was="PROCESS_ARCH_LIFT=burn_time",
            now="PROCESS_ARCH_BURN_TIME_OWNER=optimiser",
        ),
    ],
    "process/core/caller.py": [
        PermittedEdit(
            kind="path constant",
            name="NODE_WRITESET_PATH",
            description=(
                "the committed per-node write sets are read by path; the copy "
                "reads the harness's own copy of them"
            ),
            task="A46 (process-copy)",
            was='Path(__file__).resolve().parents[2] / "arch_surgery" / "docs" / "data" / "node_writesets.json"',
            now='Path(__file__).resolve().parents[3] / "harness" / "data" / "node_writesets.json"',
        ),
        PermittedEdit(
            kind="path constant",
            name="NODE_MAP_PATH",
            description=(
                "the committed node map is read by path; the copy reads the "
                "harness's own copy of it"
            ),
            task="A46 (process-copy)",
            was='Path(__file__).resolve().parents[2] / "arch_surgery" / "docs" / "data" / "dsm_node_map.json"',
            now='Path(__file__).resolve().parents[3] / "harness" / "data" / "dsm_node_map.json"',
        ),
        PermittedEdit(
            kind="existence check",
            name="_defer_per_run_nodes, step (4)",
            description=(
                "the per-run deferral path read NODE_WRITESET_PATH with no "
                "existence check and raised a bare FileNotFoundError; it now "
                "raises a typed refusal naming the artifact and its "
                "provenance file, mirroring the check the per-call path "
                "already had.  No behaviour change on any path where the file "
                "exists"
            ),
            task="A48 (harness-data)",
        ),
        PermittedEdit(
            kind="comment",
            name="the artifacts' origin",
            description=(
                "the per-call refusal named a generator script in the "
                "repository's research tree as the way to obtain the write "
                "sets, and a comment named the per-run deferral artifact by "
                "its path in the shared data directory; both name the "
                "committed copy in harness/data/ and its provenance file, and "
                "the two constants' comments say the target exists"
            ),
            task="A48 (harness-data)",
        ),
        PermittedEdit(
            kind="switch rename",
            name="every architecture switch this file reads",
            description=(
                "the four switches resolved here take their intended names, "
                "and so do the module-level readbacks a harness reads them "
                "back through; every branch, table and derivation is "
                "unchanged"
            ),
            task="A56 (driver-renames)",
            was="PROCESS_ARCH_SEQUENCE, _PRIME, _HOIST, _POST_SOLVE",
            now="PROCESS_ARCH_ARRANGEMENT_NODE, _ARRANGEMENT_METHOD, _DEFER_PER_CALL, _DEFER_PER_RUN",
        ),
        PermittedEdit(
            kind="removal",
            name="the repeated schedule",
            description=(
                "the block schedule runs exactly once, so the loop over "
                "schedule passes, the joint residual evaluation that decided "
                "whether to repeat it, that evaluation's trace hook and the "
                "pass-cap refusal are removed from "
                "Caller._call_models_partitioned.  Every arm this experiment "
                "runs already took the single-pass path, which gate GR is "
                "what proves"
            ),
            task="A56 (driver-renames)",
        ),
        PermittedEdit(
            kind="typed refusal",
            name="ArchitectureRefusal",
            description=(
                "every refusal of an architecture setting in this file raises "
                "the typed refusal instead of a bare RuntimeError; upstream's "
                "own ten-pass raise is left as it is, because it is a finding "
                "about the shipped code rather than a refused setting"
            ),
            task="A56 (driver-renames)",
        ),
        PermittedEdit(
            kind="switch added",
            name="PROCESS_ARCH_OUTPUT_LOOP",
            description=(
                "the output path becomes a driver choice.  Upstream re-solves "
                "the accepted state through a second flat idempotence loop "
                "before writing the output files; 'none' calls finalise once "
                "on the accepted state and runs no output-time sweep.  Two "
                "integer counters travel with it -- the sweeps that loop "
                "actually ran, and the entries to write_output_files -- so "
                "what the second loop costs is a measured column and not a "
                "term nobody counted.  Unset is upstream's own behaviour, "
                "line for line"
            ),
            task="A57 (driver-output-path)",
            was="one output path: upstream's output-time loop, uncounted",
            now="PROCESS_ARCH_OUTPUT_LOOP=upstream | none (unset for upstream)",
        ),
        PermittedEdit(
            kind="instrument hook",
            name="EXIT_SNAPSHOT_HOOK / EXIT_SNAPSHOTS",
            description=(
                "a callable slot the measurement subprocess installs, called "
                "at two named positions on the output path: the entry to "
                "write_output_files -- the state the solve handed over, "
                "before the per-run deferred nodes and before any output-time "
                "sweep -- and immediately before the single finalise that "
                "writes the real files.  It is what lets the exit audit be "
                "taken where the experiment plan declares it: the audit's own "
                "sweep mutates the state it measures, so the state is "
                "snapshotted there and the residual computed after the run "
                "from the restored snapshot.  With the hook uninstalled -- "
                "every run of PROCESS that is not being measured -- the "
                "mechanism is two 'is None' tests per run, and a hook that "
                "raises is recorded rather than allowed to change the run's "
                "outcome"
            ),
            task="A57 (driver-output-path)",
        ),
        PermittedEdit(
            kind="counters",
            name=(
                "PREDICATE_EVALUATIONS / COMPONENTS_COMPARED / "
                "BLOCK_VISITS / EMPTY_BLOCK_VISITS / "
                "EMPTY_BLOCK_SWEEPS / "
                "UPSTREAM_PREDICATE_EVALUATIONS / "
                "UPSTREAM_COMPONENTS_COMPARED"
            ),
            description=(
                "what the convergence test costs, counted rather than timed.  "
                "The coupling-state predicate is counted per evaluation and "
                "by the number of components each evaluation walked -- the "
                "block's own write set, or the whole coupling state where the "
                "block has none -- with both also kept per block label; the "
                "schedule's visits to each block are counted, and the subset "
                "of those that executed no model node -- measured on the node "
                "counter, not on the block's membership, because the routing "
                "rule moves a node out of the loop at the call site and not "
                "out of the block, which is issue I-20(a)'s PULSE block -- "
                "with the sweeps those empty visits spent kept separately, "
                "since a block emptied of members costs no sweep and a block "
                "whose members are skipped costs a full walk of the dispatch "
                "body.  Counted and disclaimed rather than repaired (decision "
                "D21); and upstream's own stopping test on "
                "the objective and the constraint vector is counted "
                "separately, exactly, so the reference arms carry a measured "
                "predicate cost rather than a zero.  Plain integer "
                "increments: no float is touched and no branch a result "
                "depends on changes, which gate G1 is what proves"
            ),
            task="A58 (driver-predicate-counters)",
            was="nothing counted the convergence test",
            now=(
                "six counters, solve phase only; the output-time loop's own "
                "check_agreement calls are counted by neither predicate"
            ),
        ),
        PermittedEdit(
            kind="rename",
            name="DISPATCH_SWEEPS",
            description=(
                "the per-run count of sweeps of the dispatch body loses its "
                "leading underscore.  It existed only to be differenced "
                "across call_models for the per-evaluation histogram; the "
                "per-sweep-overhead question needs the run total, and it "
                "cannot be asked of a counter a harness has to reach into a "
                "module's private names to read.  Same cell, same increment, "
                "same value"
            ),
            task="A58 (driver-predicate-counters)",
            was="_SWEEP_CALLS",
            now="DISPATCH_SWEEPS",
        ),
        PermittedEdit(
            kind="switch added",
            name="PROCESS_ARCH_PREDICATE, at the predicate's call site",
            description=(
                "the one place this file evaluates the coupling-state "
                "convergence test passes the ruler the run asked for.  The "
                "call site serves both arrangements -- the flat one's single "
                "block and each block loop of the partitioned one -- so there "
                "is exactly one place the choice is made and no path where a "
                "loop can stop on a ruler the record does not name.  The test "
                "itself is not reimplemented here: it lives in the harness's "
                "coupling-state module, which is the one implementation this "
                "revision of the experiment has"
            ),
            task="A59 (driver-predicate-mode)",
            was="spec.residual(y_prev, y, subset=subset)",
            now="the same call, with ruler=module_solve.PREDICATE_MODE",
        ),
        PermittedEdit(
            kind="counters",
            name="ATTEMPT_LADDERS / ATTEMPT_STAMPS / open_ladder / attempt",
            description=(
                "what each attempt of the optimiser's retry ladder cost.  The "
                "ladder runs the optimiser again on a failed exit code -- with "
                "a larger finite-difference step, then a smaller one, then "
                "from a reset second-derivative matrix -- and every attempt "
                "evaluates the model set, so the run's node-call total carries "
                "attempts whose iterations and exit code the record did not "
                "publish.  A context manager reads the cost counters at the "
                "entry to and the exit from every attempt and appends them to "
                "a list the measurement harness differences; the exit stamp is "
                "taken in a finally, so an attempt that raises is still "
                "bounded.  DISPATCH_SWEEPS_AT_OUTPUT is frozen by the same "
                "statement that freezes NODE_CALLS_AT_OUTPUT, so the "
                "per-attempt sweep counts have a solve-phase whole to add up "
                "to.  Four integer reads and two dict copies per boundary, at "
                "most eight boundaries in a run: no float is touched and no "
                "branch a result depends on changes"
            ),
            task="A60 (driver-attempts)",
            was="node calls and sweeps were run totals; attempts had none",
            now=(
                "a boundary stamp per attempt entry and exit, summing to the "
                "solve-phase totals"
            ),
        ),
        PermittedEdit(
            kind="instrument hook",
            name="the block trace in the block schedule's call_models",
            description=(
                "with PROCESS_ARCH_BLOCK_TRACE set, each block loop's sweep "
                "residual is split by module and kept, and one line per "
                "evaluation is written at both of the schedule's exits (the "
                "converged return and the block-cap refusal) by a new method, "
                "_block_trace_line.  Every statement is guarded by the switch; "
                "the residual it reads is the one the loop already computed, "
                "and no branch a result depends on changes"
            ),
            task="A90 (m2-phasea-vs-phaseb)",
            was="per-evaluation block counts rolled into run totals only",
            now="the same totals, plus a per-evaluation trace when asked for",
        ),
        PermittedEdit(
            kind="memoisation",
            name="resolve_schedule / SCHEDULE_RESOLUTION",
            description=(
                "the block schedule and the per-call deferral sets are "
                "resolved once per run instead of on every call_models: one "
                "resolver, keyed on the figure of merit, does the ast walk of "
                "the predicate sources, the read of the write census and the "
                "block membership on its first call and hands the same "
                "objects back on every later one; module_schedule and "
                "resolved_defer_per_call_tails delegate to it and keep their "
                "signatures.  A stamp records what was resolved, the digests "
                "of what it read and how many times it ran; the per-call "
                "deferred_tail entry of the block stats goes.  With every "
                "switch unset the resolver is never reached (gate G1); no "
                "count changes and every exit state is bit-identical (gate "
                "GC); no float the run computes with is touched"
            ),
            task="A99 (v5-schedule-and-prime)",
            was=(
                "the deferral sets and the schedule re-derived on every "
                "evaluation (issue I-30: 8-11 ms per evaluation of a "
                "deferring arm)"
            ),
            now=(
                "resolved once per run, keyed on i_figure_merit, stamped in "
                "SCHEDULE_RESOLUTION"
            ),
        ),
        PermittedEdit(
            kind="hook moved",
            name="the arrangement-method (prime) hook",
            description=(
                "the first-wall geometry prime moves from the head of every "
                "sweep (_call_models_once) to the head of every evaluation "
                "(_call_models_inner), before the first block of the schedule "
                "or the first sweep of the flat loop: pre-processing of the "
                "sequenced schedule, once per call_models.  The same two "
                "statements under the same guard; the output path and the "
                "exit audit, which call _call_models_once directly, no longer "
                "prime.  ARRANGEMENT_METHOD_CALLS becomes the evaluation "
                "count.  With the switch unset one boolean read moves (gate "
                "G1); with it on every exit state is bit-identical to the "
                "per-sweep form's and no other count changes (gates G2, GC)"
            ),
            task="A99 (v5-schedule-and-prime)",
            was="the prime at the head of every sweep, about 9-15 stamped calls per evaluation",
            now="the prime once per evaluation, before M1; n_prime_calls = evaluations",
        ),
    ],
    "process/core/solver/solver_handler.py": [
        PermittedEdit(
            kind="counters",
            name="LADDER_STAGES, and the four attempts bracketed",
            description=(
                "the retry ladder's rungs are named beside the branches that "
                "implement them -- initial, the finite-difference step times "
                "ten, times a tenth, and the reset second-derivative matrix -- "
                "and each of the four calls to the optimiser is wrapped in the "
                "cost-stamp context manager.  The names are here rather than "
                "in the harness so that a ladder which gains a rung cannot "
                "keep the old vocabulary silently.  Nothing about the ladder "
                "changes: which attempts run, in which order, under which "
                "settings, is exactly what it was, and the only new statements "
                "are the stamps"
            ),
            task="A60 (driver-attempts)",
            was="four bare calls to the solver, indistinguishable in the counters",
            now="the same four calls, each bracketed by a boundary stamp",
        ),
    ],
    "process/core/solver/evaluators.py": [
        PermittedEdit(
            kind="instrument hook",
            name="EVALUATION_KIND before each call_models",
            description=(
                "with PROCESS_ARCH_BLOCK_TRACE set, the evaluator labels each "
                "of its calls to call_models for the block trace -- the "
                "function evaluation, the gradient column and sign, the "
                "reconcile call -- so the kind of an evaluation is read from "
                "the optimiser's own call site rather than inferred from its "
                "position in the sequence.  Guarded by the switch; the calls "
                "themselves are unchanged"
            ),
            task="A90 (m2-phasea-vs-phaseb)",
            was="unlabelled calls",
            now="the same calls, labelled when the block trace is on",
        ),
    ],
    "process/core/_idf_probe_modules.py": [
        PermittedEdit(
            kind="instrument report",
            name="reads_by_node",
            description=(
                "the census instrument's summary reports each node's read "
                "set by name, beside the write set it already reported.  It "
                "reported the *count* of a node's reads and not the names, so "
                "the harness had to reach into the instrument's module-level "
                "state to get them; now it reads the report.  One line, the "
                "same expression the writes half uses, in a probe that is a "
                "no-op with PROCESS_IDF_PROBE unset"
            ),
            task="A58 (driver-predicate-counters); task A51 "
            "(harness-artifacts)'s handover",
        ),
    ],
}

#: Model files the experiment has approved a structural edit to, with the
#: decision that approved each.  Anything else differing from the base commit
#: is a finding, not something this gate absorbs.
APPROVED_MODEL_EDITS: dict[str, str] = {
    "process/models/pulse.py": (
        "D14(b), 2026-09-01 -- the burn-time residual extracted into a "
        "driver-solvable form (burn_time_root / burn_time_residual), the "
        "arithmetic verbatim; structural only, D11's approval rule satisfied"
    ),
}


# ---------------------------------------------------------------------------
# git access -- always the commit, never a working tree
# ---------------------------------------------------------------------------


def _git(*args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(HERE), *args],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout


def blobs_at(commit: str, prefix: str) -> dict[str, bytes]:
    """``{path: bytes}`` for every blob under ``prefix`` at ``commit``.

    Read with ``git cat-file``, so no checkout filter and no working tree can
    stand between the commit and the bytes compared.
    """
    listing = _git("ls-tree", "-r", "-z", "--full-tree", commit, prefix)
    entries: list[tuple[str, str]] = []  # (oid, path)
    for chunk in listing.split(b"\0"):
        if not chunk:
            continue
        meta, path = chunk.split(b"\t", 1)
        mode, kind, oid = meta.split()
        if kind != b"blob":
            raise SystemExit(
                f"{prefix} at {commit} contains a non-blob entry "
                f"({kind.decode()} at {path.decode()}); this gate handles "
                "regular files only."
            )
        if mode != b"100644":
            raise SystemExit(
                f"{path.decode()} at {commit} has mode {mode.decode()}, not "
                "100644; the copy's file modes are not covered by this gate."
            )
        entries.append((oid.decode(), path.decode()))

    proc = subprocess.run(
        ["git", "-C", str(HERE), "cat-file", "--batch"],
        input="".join(oid + "\n" for oid, _ in entries).encode(),
        check=True,
        stdout=subprocess.PIPE,
    )
    out, pos, result = proc.stdout, 0, {}
    for _oid, path in entries:
        nl = out.index(b"\n", pos)
        size = int(out[pos:nl].split()[2])
        start = nl + 1
        result[path] = out[start : start + size]
        pos = start + size + 1
    return result


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def on_disk(root: Path, prefix: str) -> dict[str, bytes]:
    """``{path: bytes}`` for every file under ``root / prefix``.

    ``__pycache__`` is excluded: it is generated, ignored by git, and never
    part of what the copy claims to be.
    """
    base = root / prefix
    files: dict[str, bytes] = {}
    for p in sorted(base.rglob("*")):
        if p.is_dir() or "__pycache__" in p.parts:
            continue
        files[str(p.relative_to(root))] = p.read_bytes()
    return files


def expected_hunks(source: bytes, copy: bytes, path: str) -> list[str]:
    """The unified diff of one permitted edit, zero context, as a line list.

    Zero context so the record shows the changed lines and their positions and
    nothing else; hunk headers are kept, so an edit that moved would not match
    a recorded one silently.
    """
    return [
        line.rstrip("\n")
        for line in difflib.unified_diff(
            source.decode().splitlines(keepends=True),
            copy.decode().splitlines(keepends=True),
            fromfile=f"source commit:{path}",
            tofile=f"copy:{path}",
            n=0,
        )
    ]


# ---------------------------------------------------------------------------
# gate results
# ---------------------------------------------------------------------------


@dataclass
class GateResult:
    """One gate's verdict and the numbers behind it."""

    gate: str
    label: str
    passed: bool = True
    compared: int = 0
    identical: int = 0
    detail: dict = field(default_factory=dict)
    failures: list[str] = field(default_factory=list)

    def fail(self, message: str) -> None:
        self.passed = False
        self.failures.append(message)

    def as_dict(self) -> dict:
        return {
            "gate": self.gate,
            "label": self.label,
            "verdict": "PASS" if self.passed else "FAIL",
            "files_compared": self.compared,
            "files_identical": self.identical,
            "failures": self.failures,
            **self.detail,
        }


# ---------------------------------------------------------------------------
# gate 1 -- copy-identity
# ---------------------------------------------------------------------------


def check_copy_identity(prov: dict, root: Path) -> GateResult:
    """Every copied file is the source commit's, bar the permitted edits."""
    res = GateResult("copy-identity", "the copy is the source commit's process/")
    commit = prov["source"]["commit_full"]
    source = blobs_at(commit, SOURCE_PREFIX)
    copy = on_disk(root, SOURCE_PREFIX)
    permitted = prov["permitted_edits"]["files"]

    # A90 (m2-phasea-vs-phaseb): the recorded list must be the committed one.
    # Without this, an edit blessed in PROVENANCE.json alone -- a file entry
    # added there with its post-edit digest and hunks, and no row in
    # PERMITTED_EDIT_FILES -- would pass every comparison below.
    if sorted(permitted) != sorted(PERMITTED_EDIT_FILES):
        res.fail(
            "the permitted-edit files recorded in PROVENANCE.json "
            f"({sorted(permitted)}) are not the committed PERMITTED_EDIT_FILES "
            f"({sorted(PERMITTED_EDIT_FILES)})"
        )

    missing = sorted(set(source) - set(copy))
    extra = sorted(set(copy) - set(source))
    for p in missing:
        res.fail(f"file missing from the copy: {p}")
    for p in extra:
        res.fail(f"file present in the copy but not at the source commit: {p}")

    unexplained: list[str] = []
    for path in sorted(set(source) & set(copy)):
        res.compared += 1
        if source[path] == copy[path]:
            res.identical += 1
            if path in permitted:
                res.fail(
                    f"{path} is recorded as a permitted edit but is identical "
                    "to the source commit; the edit has been lost."
                )
            continue
        if path not in permitted:
            unexplained.append(path)
            res.fail(f"unexplained difference from the source commit: {path}")
            continue
        spec = permitted[path]
        got = sha256(copy[path])
        if got != spec["sha256_expected_in_copy"]:
            res.fail(
                f"{path} differs from the source commit AND from the expected "
                f"post-edit content (sha256 {got}, expected "
                f"{spec['sha256_expected_in_copy']}); something other than the "
                "recorded edits has been changed in it."
            )
        got_hunks = expected_hunks(source[path], copy[path], path)
        if got_hunks != spec["expected_hunks"]:
            res.fail(
                f"{path}'s hunks do not match the ones recorded in "
                "PROVENANCE.json."
            )

    res.detail = {
        "source_commit": prov["source"]["commit"],
        "source_commit_full": commit,
        "files_at_source_commit": len(source),
        "files_in_copy": len(copy),
        "files_missing_from_copy": missing,
        "files_added_to_copy": extra,
        "permitted_edit_files": sorted(permitted),
        "unexplained_differences": unexplained,
    }
    return res


# ---------------------------------------------------------------------------
# gate 2 -- frozen-physics (G0')
# ---------------------------------------------------------------------------


def check_frozen_physics(prov: dict, root: Path) -> GateResult:
    """The copy's models/ is the frozen base commit's, bar approved edits."""
    res = GateResult("frozen-physics", "G0' -- the physics stays frozen in the copy")
    base = prov["frozen_physics"]["base_commit_full"]
    approved = {a["path"]: a for a in prov["frozen_physics"]["approved_differences"]}
    at_base = blobs_at(base, MODELS_PREFIX)
    copy = on_disk(root, MODELS_PREFIX)

    missing = sorted(set(at_base) - set(copy))
    extra = sorted(set(copy) - set(at_base))
    for p in missing:
        res.fail(f"model file missing from the copy: {p}")
    for p in extra:
        res.fail(f"model file present in the copy but not at {base[:8]}: {p}")

    differing: list[str] = []
    unapproved: list[str] = []
    for path in sorted(set(at_base) & set(copy)):
        res.compared += 1
        same = at_base[path] == copy[path]
        if same:
            res.identical += 1
        else:
            differing.append(path)
        if path in approved:
            got = sha256(copy[path])
            if got != approved[path]["sha256_expected_in_copy"]:
                res.fail(
                    f"{path} carries an approved edit ({approved[path]['decision']}) "
                    f"but its content is not the approved one (sha256 {got}, "
                    f"expected {approved[path]['sha256_expected_in_copy']})."
                )
        elif not same:
            unapproved.append(path)
            res.fail(
                f"{path} differs from the frozen base commit and no decision "
                "approves it; this is a finding, not something to absorb."
            )

    for path in approved:
        if path not in copy:
            res.fail(f"approved model edit {path} is not in the copy at all.")

    res.detail = {
        "base_commit": prov["frozen_physics"]["base_commit"],
        "base_commit_full": base,
        "model_files_at_base_commit": len(at_base),
        "model_files_in_copy": len(copy),
        "model_files_missing_from_copy": missing,
        "model_files_added_to_copy": extra,
        "model_files_differing_from_base": differing,
        "approved_differences": {p: a["decision"] for p, a in approved.items()},
        "unapproved_differences": unapproved,
    }
    return res


# ---------------------------------------------------------------------------
# teeth -- each perturbation must make the gate FAIL
# ---------------------------------------------------------------------------


def _staged(root: Path, tmp: Path) -> Path:
    """A throwaway copy of the tree.  The real tree is never perturbed."""
    dest = tmp / "process"
    shutil.copytree(root / "process", dest, ignore=shutil.ignore_patterns("__pycache__"))
    return tmp


def _flip_one_byte(path: Path) -> str:
    """Change exactly one byte, in place, without changing the file's length."""
    data = bytearray(path.read_bytes())
    for i, b in enumerate(data):
        if 0x61 <= b <= 0x7A:  # first lowercase ASCII letter
            data[i] = b - 0x20
            path.write_bytes(bytes(data))
            return f"byte {i} of {path.name}: {chr(b)!r} -> {chr(b - 0x20)!r}"
    raise SystemExit(f"no byte to flip in {path}")


def run_teeth(prov: dict, root: Path, gate: str) -> list[dict]:
    """Perturb, re-run the gate, and require FAIL each time."""
    check = check_copy_identity if gate == "copy-identity" else check_frozen_physics
    sub = "process/models" if gate == "frozen-physics" else "process/core"
    victim = (
        "process/models/vacuum.py"
        if gate == "frozen-physics"
        else "process/core/constants.py"
    )
    teeth: list[tuple[str, str]] = [
        ("one_byte_changed", victim),
        ("file_removed", victim),
        ("file_added", f"{sub}/_tooth_added.py"),
    ]
    # A fourth tooth per gate: a change to a file that IS allowed to differ,
    # made somewhere other than the approved place.  Without it, "the permitted
    # edit list" would be a blanket pardon for those files.
    # A90 (m2-phasea-vs-phaseb): one such tooth per permitted file, derived
    # from the committed list, so a file added to it is covered the moment it
    # is added; and a tooth that blesses an edit in PROVENANCE.json alone.
    if gate == "copy-identity":
        for path in sorted(PERMITTED_EDIT_FILES):
            teeth.append(("permitted_file_changed_elsewhere", path))
        teeth.append(("edit_blessed_in_provenance_only", victim))
    else:
        teeth.append(("approved_file_changed_further", "process/models/pulse.py"))

    results = []
    for kind, target in teeth:
        with tempfile.TemporaryDirectory() as td:
            staged = _staged(root, Path(td))
            p = staged / target
            if kind == "file_removed":
                p.unlink()
                what = f"removed {target}"
            elif kind == "file_added":
                p.write_text("# a file the source commit does not have\n")
                what = f"added {target}"
            elif kind == "edit_blessed_in_provenance_only":
                before = p.read_bytes()
                flipped = _flip_one_byte(p)
                doctored = copy.deepcopy(prov)
                doctored["permitted_edits"]["files"][target] = {
                    "edits": [],
                    "sha256_at_source_commit": sha256(before),
                    "sha256_expected_in_copy": sha256(p.read_bytes()),
                    "expected_hunks": expected_hunks(before, p.read_bytes(), target),
                }
                what = f"{flipped}, and {target} recorded as permitted in PROVENANCE.json only"
                res = check(doctored, staged)
                results.append(
                    {
                        "tooth": kind,
                        "target": target,
                        "perturbation": what,
                        "gate_verdict": "PASS" if res.passed else "FAIL",
                        "tooth_result": "TRIPPED" if not res.passed else "DID NOT TRIP",
                        "first_failure": res.failures[0] if res.failures else None,
                    }
                )
                continue
            else:
                what = _flip_one_byte(p)
            res = check(prov, staged)
            results.append(
                {
                    "tooth": kind,
                    "target": target,
                    "perturbation": what,
                    "gate_verdict": "PASS" if res.passed else "FAIL",
                    "tooth_result": "TRIPPED" if not res.passed else "DID NOT TRIP",
                    "first_failure": res.failures[0] if res.failures else None,
                }
            )
    return results


# ---------------------------------------------------------------------------
# smoke import -- the copy is the tree that would actually run
# ---------------------------------------------------------------------------


def smoke_import() -> dict:
    """``import process`` in a fresh subprocess must resolve under the copy.

    Trap T6: a git worktree does not redirect the editable install, and the
    editable install in this environment points at the repository-root
    package.  Setting PYTHONPATH to the copy's directory is what selects the
    copy, and ``process.__file__`` -- the path, never ``__version__``, which
    trap T10 shows can report a different commit than the tree holds -- is what
    proves it.  Run from a directory that is neither tree, so cwd cannot be
    what resolves the import.

    The tooth is the same subprocess without PYTHONPATH: it must resolve
    somewhere other than the copy, or PYTHONPATH was not what selected it.
    """
    # __version__ is recorded, never asserted on: trap T10 -- a frozen archive
    # reports the version string of whatever tree wrote its _version.py, so a
    # passing __version__ check on the wrong tree is worse than no check.  The
    # copy has no _version.py at all (it is untracked by design), so its
    # __version__ comes from the installed distribution's metadata, which is
    # the repository-root editable install's.  Recording both makes that
    # visible instead of tempting.
    code = "import process; print(process.__file__); print(process.__version__)"
    neutral = tempfile.mkdtemp()
    results = {}
    for name, env_extra in (("with_pythonpath", str(COPY_ROOT)), ("tooth_without_pythonpath", None)):
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        if env_extra:
            env["PYTHONPATH"] = env_extra
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=neutral,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        lines = proc.stdout.strip().splitlines()
        results[name] = {
            "returncode": proc.returncode,
            "process_file": lines[0] if lines else "",
            "process_version_recorded_not_asserted": lines[1] if len(lines) > 1 else "",
            "stderr": proc.stderr.strip()[-400:],
        }
    shutil.rmtree(neutral, ignore_errors=True)

    under_copy = results["with_pythonpath"]["process_file"].startswith(
        str(COPY_ROOT / "process") + "/"
    )
    tooth_elsewhere = not results["tooth_without_pythonpath"][
        "process_file"
    ].startswith(str(COPY_ROOT / "process") + "/")
    results["python"] = sys.executable
    results["cwd_used"] = neutral
    results["verdict"] = "PASS" if under_copy and tooth_elsewhere else "FAIL"
    results["tooth_result"] = "TRIPPED" if tooth_elsewhere else "DID NOT TRIP"
    return results


# ---------------------------------------------------------------------------
# edit-behaviour -- the one edit that is not a comment, exercised
# ---------------------------------------------------------------------------

#: Driven in a child process so that neither tree is imported into this one.
#: It reaches the per-run deferral path with a stub in place of the run's data
#: object -- the function reads ``data.numerics`` and nothing else -- and stops
#: at the step that reads the per-node write sets.  No PROCESS run: nothing is
#: solved, no model is called, no output file is opened.
_BEHAVIOUR_SOURCE = r"""
import json, os, sys
from pathlib import Path

import process.core.caller as caller

artifact_present = sys.argv[1] == "present"
missing = Path(sys.argv[2])
node_map = Path(sys.argv[3])
write_sets = Path(sys.argv[4])
# The two trees spell the per-run deferral switch and its entry point
# differently -- that rename is itself one of the permitted edits -- so the
# caller passes the name each tree uses and this probe reaches the same code on
# both sides.  Without it the arm run against the source commit would fail on
# the name rather than on the behaviour, and the comparison would say nothing.
variable = sys.argv[5]
entry_point = sys.argv[6]
record = json.loads(Path(os.environ[variable]).read_text())

# Both trees are given the same two artifacts by hand, so that the only thing
# that differs between the arms is the tree's own code.  Without this the tree
# extracted from the source commit stops one step earlier, on a node map that
# is simply not beside it, and the arms would not be comparable.
caller.NODE_MAP_PATH = node_map
caller.NODE_WRITESET_PATH = write_sets


class _Numerics:
    def __init__(self, record):
        icc = record["deck"]["icc_expected_at_runtime"]
        self.i_figure_merit = record["deck"]["i_figure_merit_expected"]
        self.n_equality_constraints = len(icc)
        self.n_inequality_constraints = 0
        self.icc = list(icc)


class _Data:
    def __init__(self, record):
        self.numerics = _Numerics(record)


if not artifact_present:
    caller.NODE_WRITESET_PATH = missing
try:
    getattr(caller, entry_point)(_Data(record))
    out = {"raised": None, "message": ""}
except BaseException as exc:
    out = {"raised": type(exc).__name__, "message": str(exc)[:400]}
print("@@B@@" + json.dumps(out) + "@@B@@")
"""


#: How each side of the edit-behaviour gate names the per-run deferral: the
#: switch it reads and the function that validates the artifact.  The copy's
#: names are A56 (driver-renames)'; the source commit's are what it was written
#: with.  Naming both is what keeps the two arms a comparison of *behaviour*.
_PER_RUN_NAMES = {
    "copy": ("PROCESS_ARCH_DEFER_PER_RUN", "_defer_per_run_nodes"),
    "source": ("PROCESS_ARCH_POST_SOLVE", "_post_solve_nodes"),
}


def _behaviour_child(
    tree: Path, artifact: Path, present: bool, *, side: str = "copy"
) -> dict:
    """Run the probe above against *tree*, and report what it raised."""
    missing = Path(tempfile.gettempdir()) / "a_write_set_file_that_is_not_there.json"
    variable, entry_point = _PER_RUN_NAMES[side]
    env = {k: v for k, v in os.environ.items() if not k.startswith("PROCESS_ARCH")}
    env["PYTHONPATH"] = str(tree)
    env[variable] = str(artifact)
    neutral = tempfile.mkdtemp()
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            _BEHAVIOUR_SOURCE,
            "present" if present else "absent",
            str(missing),
            str(artifact.parent / "dsm_node_map.json"),
            str(artifact.parent / "node_writesets.json"),
            variable,
            entry_point,
        ],
        cwd=neutral,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    shutil.rmtree(neutral, ignore_errors=True)
    body = proc.stdout.split("@@B@@")
    if len(body) < 3:
        return {
            "raised": "probe failed",
            "message": (proc.stderr or proc.stdout).strip()[-400:],
        }
    return json.loads(body[1])


def check_edit_behaviour(prov: dict, root: Path | None = None) -> tuple[bool, dict]:
    """The added existence check refuses by name, and changes nothing else.

    *root* is the directory holding the copy's ``process/`` -- the real copy by
    default; the tooth hands it a throwaway staging whose edit has been
    doctored.  The committed artifacts are always the real tree's.

    The per-node write sets are read on two paths.  The per-call deferral path
    always checked the file was there and raised a ``RuntimeError`` naming it;
    the per-run deferral path did not, and raised a bare ``FileNotFoundError``
    from inside ``json.loads``.  A48 (harness-data) added the missing check.
    Three arms, one gate:

    * **the copy, artifact absent** -- must raise ``ArchitectureRefusal``
      naming the artifact and ``harness/data/PROVENANCE.json``;
    * **the source commit, artifact absent** -- must raise
      ``FileNotFoundError``, which is the defect the edit repairs and is what
      makes the first arm a change rather than a restatement;
    * **the copy, artifact present** (the tooth) -- must *not* refuse, so the
      check is shown to be a guard on absence and not a new refusal on the
      path every run takes.
    """
    root = COPY_ROOT if root is None else Path(root)
    data_dir = COPY_ROOT.parent / "harness" / "data"
    artifact = data_dir / "defer_per_run_large_tokamak_nof.json"
    result: dict = {
        "gate": "edit-behaviour",
        "copy_root": str(root),
        "label": "the added existence check refuses by name, and only on absence",
        "artifact_used": str(artifact),
    }
    if not artifact.exists() or not (data_dir / "node_writesets.json").exists():
        result["verdict"] = "FAIL"
        result["failures"] = [
            f"the committed artifacts are not in {data_dir}; this gate needs "
            "them, and falling back to another copy of them would be checking "
            "a file nobody asked about."
        ]
        return False, result

    with tempfile.TemporaryDirectory() as td:
        source_tree = Path(td)
        # From the repository's top level: ``git archive``'s pathspec is
        # relative to the current directory, and this directory does not exist
        # at the source commit.
        top = _git("rev-parse", "--show-toplevel").decode().strip()
        archive = subprocess.run(
            [
                "git",
                "-C",
                top,
                "archive",
                prov["source"]["commit_full"],
                SOURCE_PREFIX,
            ],
            check=True,
            stdout=subprocess.PIPE,
        ).stdout
        subprocess.run(["tar", "-x", "-C", str(source_tree)], input=archive, check=True)
        at_source = _behaviour_child(
            source_tree, artifact, present=False, side="source"
        )
    in_copy = _behaviour_child(root, artifact, present=False)
    tooth = _behaviour_child(root, artifact, present=True)

    failures = []
    if (
        in_copy["raised"] != "ArchitectureRefusal"
        or "PROVENANCE.json" not in in_copy["message"]
    ):
        failures.append(
            f"the copy raised {in_copy['raised']} ({in_copy['message']!r}); "
            "expected an ArchitectureRefusal naming harness/data/PROVENANCE.json"
        )
    if at_source["raised"] != "FileNotFoundError":
        failures.append(
            f"the source commit raised {at_source['raised']} "
            f"({at_source['message']!r}); expected the bare FileNotFoundError "
            "this edit repairs, so the edit is a change and not a restatement"
        )
    tooth_tripped = tooth["raised"] is None
    if not tooth_tripped:
        failures.append(
            f"with the artifact present the copy still refused "
            f"({tooth['raised']}: {tooth['message']!r}); the check would be a "
            "new refusal on the path every run takes, not a guard on absence"
        )
    result.update(
        {
            "verdict": "PASS" if not failures else "FAIL",
            "copy_artifact_absent": in_copy,
            "source_commit_artifact_absent": at_source,
            "tooth_copy_artifact_present": {
                **tooth,
                "tooth_result": "TRIPPED" if tooth_tripped else "DID NOT TRIP",
            },
            "failures": failures,
        }
    )
    return not failures, result


#: The permitted edit the edit-behaviour gate exercises, as it stands in the
#: copy's ``process/core/caller.py``, anchored on its own refusal message so
#: that the per-call path's identical ``if`` line one function up is not the
#: one doctored; and what the tooth turns the ``if`` line into.  The doctored
#: line keeps the file's length in lines and its syntax, and makes the
#: existence check unreachable -- so with the artifact absent the doctored copy
#: falls through to ``json.loads`` and raises the bare ``FileNotFoundError`` the
#: source commit raises.  A copy whose permitted edit no longer does what the
#: gate says it does must FAIL the gate; this tooth is what shows it would.
EDIT_BEHAVIOUR_TOOTH_FILE = "process/core/caller.py"
EDIT_BEHAVIOUR_TOOTH_LINE = (
    "    if not NODE_WRITESET_PATH.exists():\n"
    "        raise ArchitectureRefusal(\n"
    '            f"PROCESS_ARCH_DEFER_PER_RUN needs the committed per-node write "\n'
)
EDIT_BEHAVIOUR_TOOTH_DOCTORED = (
    "    if False:  # doctored by the edit-behaviour tooth\n"
    "        raise ArchitectureRefusal(\n"
    '            f"PROCESS_ARCH_DEFER_PER_RUN needs the committed per-node write "\n'
)


def run_edit_behaviour_tooth(prov: dict, root: Path) -> dict:
    """Doctor the permitted edit in a throwaway staging and require FAIL.

    The gate's criterion is a comparison of behaviour -- the copy refuses by
    name where the source commit raised a bare ``FileNotFoundError`` -- so its
    tooth is a copy whose behaviour has been made the source commit's again.
    The real tree is never modified.
    """
    with tempfile.TemporaryDirectory() as td:
        staged = _staged(root, Path(td))
        victim = staged / EDIT_BEHAVIOUR_TOOTH_FILE
        source = victim.read_text()
        if source.count(EDIT_BEHAVIOUR_TOOTH_LINE) != 1:
            return {
                "tooth": "permitted_edit_doctored",
                "perturbation": (
                    f"could not doctor {EDIT_BEHAVIOUR_TOOTH_FILE}: the anchor "
                    f"{EDIT_BEHAVIOUR_TOOTH_LINE.splitlines()[0].strip()!r} occurs "
                    f"{source.count(EDIT_BEHAVIOUR_TOOTH_LINE)} time(s), not once"
                ),
                "gate_verdict": None,
                "tooth_result": "DID NOT TRIP",
                "first_failure": None,
            }
        victim.write_text(
            source.replace(EDIT_BEHAVIOUR_TOOTH_LINE, EDIT_BEHAVIOUR_TOOTH_DOCTORED)
        )
        passed, result = check_edit_behaviour(prov, root=staged)
    return {
        "tooth": "permitted_edit_doctored",
        "perturbation": (
            f"{EDIT_BEHAVIOUR_TOOTH_FILE}: "
            f"{EDIT_BEHAVIOUR_TOOTH_LINE.splitlines()[0].strip()!r} -> "
            f"{EDIT_BEHAVIOUR_TOOTH_DOCTORED.splitlines()[0].strip()!r} in a "
            f"throwaway copy of the tree, so the per-run path's existence check "
            f"is unreachable"
        ),
        "gate_verdict": result["verdict"],
        "tooth_result": "TRIPPED" if not passed else "DID NOT TRIP",
        "first_failure": (result.get("failures") or [None])[0],
        "copy_artifact_absent_raised": (result.get("copy_artifact_absent") or {}).get(
            "raised"
        ),
    }


# ---------------------------------------------------------------------------
# PROVENANCE.json
# ---------------------------------------------------------------------------


def build_provenance(commit: str, base: str, root: Path) -> dict:
    """Assemble the provenance record from the commits and the copy on disk."""
    full = _git("rev-parse", commit).decode().strip()
    base_full = _git("rev-parse", base).decode().strip()
    source = blobs_at(full, SOURCE_PREFIX)
    copy = on_disk(root, SOURCE_PREFIX)

    differing = sorted(p for p in source if p in copy and source[p] != copy[p])
    if differing != sorted(PERMITTED_EDIT_FILES):
        raise SystemExit(
            "refusing to write PROVENANCE.json: the files differing from the "
            f"source commit are {differing}, but the permitted-edit list names "
            f"{sorted(PERMITTED_EDIT_FILES)}.  Regenerating provenance must "
            "never be the way an unapproved edit becomes approved."
        )

    at_base = blobs_at(base_full, MODELS_PREFIX)
    approved = []
    for path, decision in sorted(APPROVED_MODEL_EDITS.items()):
        approved.append(
            {
                "path": path,
                "decision": decision,
                "sha256_at_base_commit": sha256(at_base[path]),
                "sha256_expected_in_copy": sha256(copy[path]),
            }
        )
    model_diff = sorted(p for p in at_base if at_base[p] != copy.get(p))
    if model_diff != sorted(APPROVED_MODEL_EDITS):
        raise SystemExit(
            "refusing to write PROVENANCE.json: models/ differs from "
            f"{base} in {model_diff}, the approved set is "
            f"{sorted(APPROVED_MODEL_EDITS)}."
        )

    return {
        "what": (
            "Provenance of V4's own copy of the PROCESS package.  The copy was "
            "extracted from the source commit below, not from a working tree, "
            "and receives exactly the permitted edits listed here.  Gates "
            "copy-identity and frozen-physics (G0') in copy_gates.py check "
            "both claims and are runnable at any later commit."
        ),
        "task": "A46 (process-copy)",
        "decision": (
            "D20, 2026-09-10 -- V4 runs its own copy of PROCESS and owes V3 no "
            "backward compatibility"
        ),
        "generated_by": "PROCESS/copy_gates.py provenance",
        "copy_date": _dt.date.today().isoformat(),
        "source": {
            "repository": "PROCESS_surgery (this repository), branch architecture_surgery",
            "path": "process/  -- the PROCESS package at the repository root",
            "commit": full[:8],
            "commit_full": full,
            "tree_sha1": _git("rev-parse", f"{full}:{SOURCE_PREFIX}").decode().strip(),
            "file_count": len(source),
            "total_bytes": sum(len(b) for b in source.values()),
            "extracted_with": f"git archive {full[:8]} process | tar -x -C PROCESS/",
        },
        "frozen_physics": {
            "what": (
                "D5 freezes the physics and engineering models at the base "
                "commit; D11 permits minimal structural edits under "
                "process/models/ with the user's approval.  Gate G0' checks "
                "the copy's models/ against the base commit and refuses any "
                "difference outside the approved list."
            ),
            "base_commit": base_full[:8],
            "base_commit_full": base_full,
            "scope": f"{MODELS_PREFIX}/",
            "model_file_count": len(at_base),
            "approved_differences": approved,
        },
        "permitted_edits": {
            "what": (
                "The complete set of changes the copy receives (harness "
                "implementation plan section 3.3 as amended by section 11).  "
                "Three path constants are re-pointed from the repository-root "
                "research tree at the V4 harness beside the copy; one "
                "existence check is added where the driver read one of those "
                "artifacts without one; and the comments that named the "
                "artifacts by their old paths name the copies.  Nothing else "
                "in the copied tree differs from the source commit.  The "
                "permitted edits are recorded as **hunks**, not as constant "
                "names: expected_hunks below is the zero-context diff of each "
                "file against the source commit and is what the gate "
                "compares, so an edit of any kind is reviewable and no file "
                "is blanket-pardoned by appearing in this list."
            ),
            "files": {
                path: {
                    "edits": [
                        edit.as_dict() for edit in PERMITTED_EDIT_FILES[path]
                    ],
                    "sha256_at_source_commit": sha256(source[path]),
                    "sha256_expected_in_copy": sha256(copy[path]),
                    "expected_hunks": expected_hunks(source[path], copy[path], path),
                }
                for path in sorted(PERMITTED_EDIT_FILES)
            },
        },
        "files": {
            "what": (
                "sha256 of every copied file as it stands at the source "
                "commit.  The two permitted-edit files differ in the copy; "
                "their expected post-edit sha256 is above."
            ),
            "sha256_at_source_commit": {p: sha256(b) for p, b in sorted(source.items())},
        },
    }


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------


def load_provenance() -> dict:
    if not PROVENANCE.exists():
        raise SystemExit(
            f"{PROVENANCE} is not present; the copy has no provenance and no "
            "gate can be run against it."
        )
    return json.loads(PROVENANCE.read_text())


def report(res: GateResult, teeth: list[dict] | None) -> None:
    print(f"\n=== gate {res.gate} -- {res.label}")
    print(f"    verdict           : {'PASS' if res.passed else 'FAIL'}")
    print(f"    files compared    : {res.compared}")
    print(f"    files identical   : {res.identical}")
    for key in (
        "files_missing_from_copy",
        "files_added_to_copy",
        "unexplained_differences",
        "model_files_missing_from_copy",
        "model_files_added_to_copy",
        "model_files_differing_from_base",
        "unapproved_differences",
    ):
        if key in res.detail:
            value = res.detail[key]
            print(f"    {key:<34}: {value if value else '(none)'}")
    for f in res.failures:
        print(f"    FAILURE: {f}")
    if teeth is not None:
        for t in teeth:
            print(
                f"    tooth {t['tooth']:<34} {t['tooth_result']:<13} "
                f"({t['perturbation']})"
            )


def carry_history(old: dict, new: dict, task: str, copy_date: str | None) -> dict:
    """Keep the copy's date and the regeneration history across a regeneration.

    ``copy_date`` is the day the copy was extracted, and a regeneration does
    not change it.  Until A90 (m2-phasea-vs-phaseb) the generator stamped
    today's date there, so each regeneration moved it (2026-09-10 at A46,
    2026-09-11 at A60, 2026-09-14 at A73, 2026-09-29 at A90's first
    regeneration).  Now the old value is kept, ``--copy-date`` restores it
    with the correction recorded, and every regeneration that changes the
    permitted edits appends one entry to ``permitted_edits_updated``: the
    date, the task, and which permitted-edit files were added, removed or
    changed in digest.
    """
    old_files = (old.get("permitted_edits") or {}).get("files") or {}
    new_files = new["permitted_edits"]["files"]
    history = list(old.get("permitted_edits_updated") or [])
    entry = {
        "date": _dt.date.today().isoformat(),
        "task": task,
        "files_added": sorted(set(new_files) - set(old_files)),
        "files_removed": sorted(set(old_files) - set(new_files)),
        "files_changed": sorted(
            p for p in set(new_files) & set(old_files)
            if new_files[p]["sha256_expected_in_copy"]
            != old_files[p]["sha256_expected_in_copy"]
        ),
    }
    kept = old.get("copy_date", new["copy_date"])
    if copy_date and copy_date != kept:
        entry["copy_date_corrected"] = {"from": kept, "to": copy_date}
        kept = copy_date
    if entry["files_added"] or entry["files_removed"] or entry["files_changed"] \
            or "copy_date_corrected" in entry:
        history.append(entry)
    out = dict(new)
    out["copy_date"] = kept
    out["permitted_edits_updated"] = history
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "command",
        choices=[
            "all",
            "copy-identity",
            "frozen-physics",
            "smoke-import",
            "edit-behaviour",
            "provenance",
        ],
    )
    ap.add_argument("--no-teeth", action="store_true", help="skip the teeth")
    ap.add_argument("--force", action="store_true", help="provenance: overwrite")
    ap.add_argument(
        "--source-commit",
        default=None,
        help="provenance: the commit the copy was taken from (defaults to the "
        "one already recorded, which never changes for a given copy)",
    )
    ap.add_argument("--base-commit", default="c0ae5b28", help="provenance: base")
    ap.add_argument(
        "--task",
        default=None,
        help="provenance: the task regenerating it, recorded in "
        "permitted_edits_updated (required when PROVENANCE.json exists)",
    )
    ap.add_argument(
        "--copy-date",
        default=None,
        help="provenance: correct copy_date to this date (the copy's own date "
        "never changes on a regeneration; this is for restoring it, and the "
        "correction is recorded)",
    )
    args = ap.parse_args(argv)

    if args.command == "provenance":
        if PROVENANCE.exists() and not args.force:
            raise SystemExit(
                f"{PROVENANCE} already exists.  Regenerating it re-blesses "
                "whatever the tree currently holds, so it needs --force and a "
                "reviewer who reads the resulting diff."
            )
        source = args.source_commit
        if source is None:
            if not PROVENANCE.exists():
                raise SystemExit(
                    "no PROVENANCE.json to take the source commit from; pass "
                    "--source-commit explicitly."
                )
            source = json.loads(PROVENANCE.read_text())["source"]["commit_full"]
        prov = build_provenance(source, args.base_commit, COPY_ROOT)
        if PROVENANCE.exists():
            if not args.task:
                raise SystemExit(
                    "regenerating an existing PROVENANCE.json needs --task: "
                    "every regeneration is recorded by who made it"
                )
            prov = carry_history(json.loads(PROVENANCE.read_text()), prov, args.task, args.copy_date)
        PROVENANCE.write_text(json.dumps(prov, indent=2) + "\n")
        print(f"wrote {PROVENANCE}")
        print(f"  source commit {prov['source']['commit_full']}")
        print(f"  {prov['source']['file_count']} files, "
              f"{prov['source']['total_bytes']} bytes")
        return 0

    prov = load_provenance()

    if args.command in ("all", "smoke-import"):
        s = smoke_import()
        print("\n=== smoke import -- the copy is the tree that would run")
        print(f"    python            : {s['python']}")
        print(f"    verdict           : {s['verdict']}")
        print(f"    with PYTHONPATH   : {s['with_pythonpath']['process_file']}")
        print(
            f"    tooth (no PYTHONPATH, must differ): "
            f"{s['tooth_without_pythonpath']['process_file']}  "
            f"[{s['tooth_result']}]"
        )
        print(
            "    __version__ (recorded, never asserted -- trap T10): "
            f"copy {s['with_pythonpath']['process_version_recorded_not_asserted']} "
            f"/ root {s['tooth_without_pythonpath']['process_version_recorded_not_asserted']}"
        )
        if args.command == "smoke-import":
            return 0 if s["verdict"] == "PASS" else 1
        if s["verdict"] != "PASS":
            print("\nGATE FAILURE")
            return 1

    if args.command in ("all", "edit-behaviour"):
        ok_behaviour, behaviour = check_edit_behaviour(prov)
        print("\n=== gate edit-behaviour -- the added existence check")
        print(f"    verdict           : {behaviour['verdict']}")
        for key, label in (
            ("copy_artifact_absent", "copy, artifact absent    "),
            ("source_commit_artifact_absent", "source, artifact absent  "),
        ):
            arm = behaviour.get(key, {})
            print(f"    {label}: {arm.get('raised')}")
        tooth = behaviour.get("tooth_copy_artifact_present", {})
        print(
            f"    tooth (artifact present, must not refuse): "
            f"{tooth.get('raised')}  [{tooth.get('tooth_result')}]"
        )
        for failure in behaviour.get("failures", []):
            print(f"    FAILURE: {failure}")
        if not args.no_teeth:
            doctored = run_edit_behaviour_tooth(prov, COPY_ROOT)
            print(
                f"    tooth {doctored['tooth']:<34} {doctored['tooth_result']:<13} "
                f"({doctored['perturbation']})"
            )
            if doctored["tooth_result"] != "TRIPPED":
                ok_behaviour = False
                print(f"    TEETH FAILED: ['{doctored['tooth']}']")
        if args.command == "edit-behaviour":
            return 0 if ok_behaviour else 1
        if not ok_behaviour:
            print("\nGATE FAILURE")
            return 1

    gates = (
        ["copy-identity", "frozen-physics"] if args.command == "all" else [args.command]
    )
    ok = True
    for gate in gates:
        check = check_copy_identity if gate == "copy-identity" else check_frozen_physics
        res = check(prov, COPY_ROOT)
        teeth = None if args.no_teeth else run_teeth(prov, COPY_ROOT, gate)
        report(res, teeth)
        blunt = [t for t in (teeth or []) if t["tooth_result"] != "TRIPPED"]
        if blunt:
            ok = False
            print(f"    TEETH FAILED: {[t['tooth'] for t in blunt]}")
        ok = ok and res.passed

    print(f"\n{'ALL GATES PASS' if ok else 'GATE FAILURE'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
