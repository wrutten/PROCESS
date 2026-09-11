#!/usr/bin/env python
"""The gate framework, and the two gates every driver change carries.

A **gate** is a check that must pass before a number is believed.  A gate's
**teeth** are deliberate breaks that the check must catch: a check whose failure
mode has never been exercised is an assertion, not a measurement (orchestration
protocol §12).  That rule is enforced here rather than reviewed: :class:`Gate`
refuses to exist without at least one :class:`Tooth`, so "we forgot the tooth"
is a ``TypeError`` at import and not an omission at review.

Two gates live here today, both of them bound on **every** commit that touches
the experiment's copy of PROCESS:

``G0'`` — *the physics stays frozen in the copy*
    Every file under ``PROCESS/process/models/`` is byte-identical to the frozen
    base commit, bar the one structural edit the user approved.  Implemented
    once, in ``PROCESS/copy_gates.py``; this module runs that implementation by
    path and records its verdict, so there is exactly one implementation of the
    criterion and exactly one place a reader has to look.

``G1`` — *switch neutrality*
    With every architecture switch unset, the copy **after** a driver change
    behaves byte-identically to the copy **before** it.  Two reference runs on
    each configuration — one optimisation and one evaluation, both with the
    whole switch vocabulary cleared — are recorded at the commit before the
    change and again after it, and every deterministic value of the two records
    is compared, plus PROCESS's own output file line by line.

The remaining gates of the experiment plan (G0, G2, G3/G3c, G4–G9, and the
registration of the reproduction gate GR) are **A52 (harness-gates)**'s; this
file starts the framework they land in.  *(One line for A52: give
``experiment_runner.py`` a ``--gate`` value per registered gate and dispatch to
:func:`registry`; nothing else here needs the runner.)*

Written by task **A56 (driver-renames)**.  It derives from no earlier file; the
``Check`` record it writes is shaped like ``harness/selfcheck.py``'s so that a
reader of one recognises the other.

Usage
-----
    python -m harness.gates g0prime
    python -m harness.gates switch-neutrality --capture before
    python -m harness.gates switch-neutrality --capture after
    python -m harness.gates switch-neutrality --compare
    python -m harness.gates all            # every gate that needs no capture
    python -m harness.gates predicate-counters   # a measurement, not a gate
    python -m harness.gates attempts --capture runs  # the ladder, made to retry
    python -m harness.gates attempts             # a measurement, not a gate
    python -m harness.gates predicate-mode --capture runs
    python -m harness.gates predicate-mode

Exit status: 0 every gate passed with every tooth tripping, 1 otherwise.
"""

from __future__ import annotations

import argparse
import ast
import copy
import datetime as _dt
import importlib.util
import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

_EXPERIMENT_DIR = Path(__file__).resolve().parent.parent
if str(_EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(_EXPERIMENT_DIR))

from harness import arms as arms_mod  # noqa: E402
from harness import framework  # noqa: E402
from harness import child as child_mod  # noqa: E402
from harness import input_files as input_files_mod  # noqa: E402
from harness import pool as pool_mod  # noqa: E402
from harness import records as records_mod  # noqa: E402
from harness import reference as reference_mod  # noqa: E402
from harness import switches as switches_mod  # noqa: E402
from harness.config import Campaign, default_campaign  # noqa: E402

#: Where a gate's verdict goes, under the campaign's runs directory.  Bulk run
#: artifacts are untracked by design; the verdict is small and its numbers go
#: into the report.
GATES_SUBPATH = framework.GATES_SUBPATH

#: The framework lives in ``harness/framework.py`` so that the self-check and
#: the artifact stages can import ``Check`` without importing this module -- the
#: promotion task **A52 (harness-gates)** moved the three shapes there and left
#: these names here, because the plan names ``gates.Gate`` and ``gates.Tooth``
#: and a reader who looks them up should find them.
Gate = framework.Gate
Tooth = framework.Tooth
Check = framework.Check
Measurement = framework.Measurement
GateError = framework.GateError
_git_head = framework.git_head


# --------------------------------------------------------------------------
# G0' -- the physics stays frozen in the copy
# --------------------------------------------------------------------------
#
# The criterion has exactly one implementation, in PROCESS/copy_gates.py, and it
# is loaded here **by path** rather than restated.  Two implementations of one
# criterion is how they drift, and a gate that drifts from the thing it gates is
# worse than no gate.


def _copy_gates(campaign: Campaign):
    """``PROCESS/copy_gates.py`` as a module, loaded by path."""
    path = Path(campaign.tree) / "copy_gates.py"
    if not path.exists():
        raise GateError(
            f"{path} is not present; G0' has no implementation to run and must "
            f"refuse rather than report a physics freeze it never checked."
        )
    spec = importlib.util.spec_from_file_location("_a56_copy_gates", path)
    if spec is None or spec.loader is None:  # pragma: no cover - import plumbing
        raise GateError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def g0prime_body(campaign: Campaign) -> dict[str, Any]:
    gates = _copy_gates(campaign)
    prov = gates.load_provenance()
    res = gates.check_frozen_physics(prov, Path(campaign.tree))
    return {
        "passed": res.passed,
        "population": (
            f"{res.compared} files under PROCESS/process/models/ compared "
            f"byte for byte against "
            f"{prov['frozen_physics']['base_commit']} (git cat-file, never a "
            f"working tree), plus the file set"
        ),
        "n_compared": res.compared,
        "n_identical": res.identical,
        "n_mismatched": res.compared - res.identical,
        "base_commit": prov["frozen_physics"]["base_commit_full"],
        "approved_differences": {
            a["path"]: a["decision"] for a in prov["frozen_physics"]["approved_differences"]
        },
        "unapproved_differences": res.detail["unapproved_differences"],
        "model_files_differing_from_base": res.detail["model_files_differing_from_base"],
        "failures": res.failures,
        "implementation": str(Path(campaign.tree) / "copy_gates.py"),
    }


def _g0prime_teeth(campaign: Campaign) -> tuple[Tooth, ...]:
    """The four perturbations ``copy_gates.run_teeth`` already builds.

    They are run **once** and shared: each perturbation stages a throwaway copy
    of the whole package, so running the set four times over would copy 22 MB
    to say the same four things.
    """
    cache: dict[str, dict] = {}

    def one(kind: str):
        def check() -> tuple[bool, str]:
            if not cache:
                gates = _copy_gates(campaign)
                prov = gates.load_provenance()
                for record in gates.run_teeth(
                    prov, Path(campaign.tree), "frozen-physics"
                ):
                    cache[record["tooth"]] = record
            record = cache.get(kind)
            if record is None:
                return False, f"copy_gates.run_teeth produced no {kind!r} tooth"
            return (
                record["tooth_result"] == "TRIPPED",
                f"{record['perturbation']} -> gate {record['gate_verdict']}"
                f" ({record['first_failure']})",
            )

        return check

    return (
        Tooth(
            "one_byte_changed",
            "one byte of one model file changed in a throwaway copy of the tree",
            "FAIL",
            one("one_byte_changed"),
        ),
        Tooth(
            "file_removed",
            "one model file removed from a throwaway copy of the tree",
            "FAIL",
            one("file_removed"),
        ),
        Tooth(
            "file_added",
            "one model file added to a throwaway copy of the tree",
            "FAIL",
            one("file_added"),
        ),
        Tooth(
            "approved_file_changed_further",
            "the one model file with an approved edit changed again",
            "FAIL",
            one("approved_file_changed_further"),
        ),
    )


# --------------------------------------------------------------------------
# G1 -- switch neutrality
# --------------------------------------------------------------------------
#
# What G1 compares, and what it deliberately does not.
#
# The claim is about **behaviour**: with every architecture switch unset, the
# driver after a change does what it did before it.  So the comparison is over
# every deterministic leaf of the run record and every line of PROCESS's own
# output file -- not over a curated list of interesting fields, because a
# curated list cannot notice a field nobody thought of.  The exclusions are
# therefore named one by one below, each with its reason, and their count is
# published beside the count of compared values: a zero over an unstated
# population is exactly the shape this project has published before (trap T11).

#: Record leaves that **can never** be compared between two runs of the same
#: code, whatever commits the two sides are at: a path into a run's own
#: directory, a timing, a machine's state, the commit itself, and the switch
#: vocabulary the driver change renames.  Matched as exact dotted paths or as
#: prefixes.
#:
#: This group and :data:`FIELDS_ADDED_BY_A_DRIVER_CHANGE` were one dictionary
#: until task **A52 (harness-gates)** reviewed it.  The distinction is not
#: cosmetic: the names below are excluded because *no* pair of runs could
#: compare them, and the names in the other group are excluded because **one
#: particular pair straddled the change that added the field**.  Keeping the
#: second kind unconditional means that every later run of this gate compares
#: less than it could, silently and for ever — which is the shape of this
#: project's own trap T11.
ALWAYS_EXCLUDED: dict[str, str] = {
    # where the run happened
    "outdir": "the two runs are in different directories, by construction",
    "campaign_input_file": "the input file is copied into the run's own directory",
    "entry_state": "a path into the run's own directory",
    "exit_audit.coupling_state": "an absolute path; the file is the same file",
    "exit_audit.restricted.artifact": "an absolute path; the file is the same file",
    "exit_audit.restricted.census": "an absolute path; the file is the same file",
    # --- the cross-tree paths ------------------------------------------
    #
    # Nine names found by the orchestrator making the **real** straddle: a
    # "before" capture in the main checkout at the trunk commit against an
    # "after" capture in a task worktree.  Every earlier run of this gate made
    # both captures inside **one** worktree, where these agree by accident of
    # location, so nothing named them.  They are all a path or the working
    # tree's own state, so no pair of captures could ever compare them, and the
    # two ways of straddling -- one tree at two commits, or two trees -- must
    # give the same answer.
    #
    # What still carries the artifacts' identity: `excluded_sha256` on the
    # restricted block and `components_sha256` on the coupling state are
    # compared, so the *file* each path points at is still checked to be the
    # same file, by content rather than by location.
    "per_run_artifact": (
        "an absolute path to the per-run deferral artifact, which is a "
        "different path in a worktree than in the main checkout.  Its identity "
        "is compared through the restricted block's excluded_sha256"
    ),
    "process_copy_provenance.path": (
        "an absolute path to the copied driver; its commit and its per-file "
        "digests are compared beside it"
    ),
    "coupling_state_artifact": (
        "an absolute path to the coupling-state artifact.  Its identity is "
        "compared through coupling_state_provenance.components_sha256"
    ),
    "coupling_state_provenance.path": "the same absolute path, inside the provenance block",
    "exit_audit.frozen.restricted.artifact": (
        "an absolute path; the per-ruler copy of the leaf above, which DR5 "
        "added when the audit began publishing both rulers"
    ),
    "exit_audit.frozen.restricted.census": "an absolute path; the per-ruler copy",
    "exit_audit.mixed.restricted.artifact": "an absolute path; the per-ruler copy",
    "exit_audit.mixed.restricted.census": "an absolute path; the per-ruler copy",
    "tree_git_branch": (
        "the branch the tree is on: the working tree's state, not the "
        "driver's behaviour, and different by construction when the two "
        "captures are made in two trees"
    ),
    "pythonpath": "an absolute path; the tree is the same tree",
    "tree": "an absolute path; the tree is the same tree",
    "repository": "an absolute path",
    "process_file": "an absolute path; equality of the tree is asserted per run",
    # when it happened, and how long it took
    "wall_s": "wall clock is context, never evidence (I-10)",
    "cpu_user_s": "cpu time is a contention diagnostic",
    "cpu_sys_s": "cpu time is a contention diagnostic",
    "cpu_s": "cpu time is a contention diagnostic",
    "maxrss_kb": "peak memory varies with the machine's state",
    "loadavg": "machine load while it ran",
    "mfile.process_runtime": "PROCESS's own timing of itself",
    # the commit, which differs by construction: the change is between them
    "tree_git_head": "the two runs are at different commits -- that is the point",
    "tree_git_describe": "derived from the commit",
    "tree_modified_tracked": "the working tree's state, not the driver's behaviour",
    "tree_untracked_paths": "the working tree's state, not the driver's behaviour",
    # The counts of the two lists above.  Excluded on the same reason, and
    # named here because leaving them out was a defect: the lists were excluded
    # and their counts were not, so a single scratch file beside the runner --
    # a draft report, a log -- made G1 FAIL on a field that cannot change what
    # the driver does.  That is the false alarm the record schema was amended
    # to prevent when it split "modified tracked" from "untracked" (A44
    # (transfer-gap) stamped a whole set of records dirty on untracked files
    # alone).  What can move a measurement is a modified *tracked* file, and
    # that is not hidden by this: it would move the behaviour, which is what
    # the other 2 300 values compare.
    "tree_modified_tracked_n": "the count of the list above, on the same reason",
    "tree_untracked_paths_n": "the count of the list above, on the same reason",
    "tree_git_dirty": "derived from the two above",
    "process_copy_provenance.copy_date": "the copy's provenance file is regenerated by the change",
    # the names being renamed: comparing them would compare the change to itself
    "env_architecture": (
        "the switch vocabulary is what the change renames; every value in it is "
        "null on both sides because the arm sets nothing, but the *keys* are the "
        "rename itself"
    ),
    "resolved_switches": (
        "the driver's module-level readbacks are what the change renames; their "
        "values are the off-state on both sides"
    ),
}

#: Record leaves that a **driver or harness change adds**, and that can
#: therefore only be compared once both sides have them.  Each is excluded
#: **conditionally**: where one side lacks the field — absent, or null against a
#: value — it is out of the comparison, and where both sides carry it, it is
#: compared like anything else.
#:
#: Why conditionally, rather than always (task **A52 (harness-gates)**'s review).
#: Every name here was added by a task that straddled the commit introducing the
#: field; at that commit the exclusion is exactly right.  At every *later*
#: commit both sides have the field, and an unconditional exclusion would go on
#: hiding it for ever.  Measured at this commit: the thirty-two names below
#: cover **1 040 leaves** across gate G1's six run pairs, every one of them
#: present and equal on both sides — so keeping them unconditional would have
#: gone on removing 1 040 values from a gate whose whole claim is a zero over a
#: stated denominator (2 289 values compared before the condition, 3 329
#: after).  The condition is checked by :func:`compare_records`, shown by a
#: tooth, and tabulated name by name by the ``exclusion_review`` stage.
FIELDS_ADDED_BY_A_DRIVER_CHANGE: dict[str, str] = {
    # The restricted audit on an OPTIMISATION record (A52 (harness-gates)).
    # Null on the earlier side because the optimisation phase was never handed
    # the two artifacts the statistic is derived from, a block on the later
    # one.  The two path leaves inside it are excluded unconditionally, above,
    # because they are absolute paths; this name covers the numbers.
    "exit_audit.restricted": (
        "null on the optimisation records before the optimisation phase was "
        "handed the per-run artifact and the write census, a block after: the "
        "statistic is the change.  The residual it restricts is compared in "
        "full, maximum, hex and brief alike"
    ),
    # The per-ruler count of components the restriction excluded.  On a record
    # where the restricted statistic was never computed the count reads **0**,
    # and 0 there does not mean "excluded nothing" -- it means "not computed".
    # So these two cannot be decided by looking at the leaf: both sides carry a
    # number and both are non-null.  They are conditional on a **witness**, the
    # restricted block itself (:data:`CONDITIONAL_WITNESS`): where the block is
    # null on one side the count there was not computed and the pair is out;
    # where both sides carry the block the counts are compared like anything
    # else, and a genuine difference is caught.  A tooth shows exactly that.
    "exit_audit.frozen.n_excluded_from_the_restricted_statistic": (
        "0 on a record whose restricted statistic was never computed, and 0 "
        "there stands for 'not computed' rather than 'excluded nothing'.  "
        "Excluded only while the restricted block is null on one side"
    ),
    "exit_audit.mixed.n_excluded_from_the_restricted_statistic": (
        "the same count on the second ruler, on the same condition"
    ),
    # fields a harness change adds or rewords between the two captures.  G1
    # binds the *driver*, and the two captures are made by the harness at each
    # commit, so a field the harness itself adds is excluded by name -- and
    # only ever by name, with the reason, because a zero over a population
    # quietly smaller than the one stated is this project's own trap T11.
    "output_loop_sweeps": (
        "the count is what the output-path change adds: null on the side that "
        "had no counter, measured on the side that has one.  What the two "
        "sides' output paths *did* is compared in full through the output file "
        "and through node_calls_total"
    ),
    "output_loop_null_because": (
        "the sentence explaining the absent counter, present only on the side "
        "that had no counter"
    ),
    "output_path_entries": (
        "a counter the output-path change adds; absent on the earlier side"
    ),
    "audit_snapshot": (
        "the snapshot block the audit-position change adds; absent on the "
        "earlier side.  Both captures audit at the same position, which is "
        "checked before the comparison runs and is what makes exit_audit "
        "comparable"
    ),
    "reproduction_overrides": (
        "a field the record gains so that a run made under the reproduction "
        "gate's overrides says so; null on both sides here, absent on the "
        "earlier one"
    ),
    "audit_position_note": (
        "the sentence saying how the audit position is reached, which is what "
        "the change rewrites.  audit_position itself is compared, and the two "
        "captures are refused if it differs"
    ),
    # The predicate counters (DR4).  Each is a field whose value is *null on
    # the earlier side because no counter existed* and a number on the later
    # one -- which is the change itself, not a behavioural difference, and is
    # the only reason each is here.  Two of them, the upstream pair, are not
    # zero on the later side: the reference arms the gate runs stop on
    # upstream's own test, so those two count a loop upstream was already
    # running.  That is precisely why they cannot be compared across the two
    # captures, and precisely why the rest of the record -- the node counts,
    # the sweep histogram, the exit audit, every output-file line -- is what
    # carries the neutrality claim instead.
    "predicate_evaluations": (
        "null before the counter existed, a number after: the count is the "
        "change.  It is 0 in these runs, because the reference arms never "
        "enter the block path, and 0 is still not null"
    ),
    "components_compared": (
        "null before, a number after; 0 in these runs for the same reason as "
        "the line above"
    ),
    "block_visits": (
        "null before, a per-block mapping after.  Empty in these runs: the "
        "reference arms build no block schedule"
    ),
    "empty_block_visits": (
        "null before, a per-block mapping after; empty in these runs for the "
        "same reason"
    ),
    "empty_block_sweeps": (
        "null before, a per-block mapping after; empty in these runs for the "
        "same reason"
    ),
    "dispatch_sweeps": (
        "null before, the run's sweep total after.  The count itself is not "
        "new -- the driver has always incremented this cell, and the sweep "
        "histogram it feeds IS compared, value for value, on both sides -- "
        "what is new is the record field"
    ),
    "upstream_predicate_evaluations": (
        "null before, a number after, and **not** zero: these runs are the "
        "reference arms, which stop on upstream's own test.  What the test "
        "decided is compared in full through the sweep histogram, the node "
        "counts and the output file"
    ),
    "upstream_components_compared": (
        "null before, a number after; not zero, for the same reason as the "
        "line above"
    ),
    "predicate_counters": (
        "the block the counters are split out in, with their sentences: "
        "absent on the earlier side entirely"
    ),
    "predicate_counters_null_because": (
        "the sentence explaining the absent counters, present only on the "
        "side that had none"
    ),
    # The predicate's ruler (DR5).  Five names, and the reason they are here
    # is the same for all five: the field is **absent** on the earlier side
    # because the choice did not exist, not because the two sides behave
    # differently.  The load-bearing point is what is NOT here: the exit
    # audit's unprefixed fields -- residual_max, residual_max_hex, the whole
    # brief block, the whole restricted block -- keep their names and their
    # values as the frozen ruler's and are compared value for value on both
    # sides.  So the strongest thing this gate compares is still inside the
    # comparison; what is excluded is a second presentation of it and a
    # stamp saying which ruler was asked for.
    "exit_audit.predicate_mode": (
        "the ruler stamp: absent before the choice existed, 'frozen' after.  "
        "It is the name of the default, not a behaviour"
    ),
    "exit_audit.frozen": (
        "the frozen ruler's audit under its own name, absent on the earlier "
        "side.  Its numbers are compared in full through exit_audit's "
        "unprefixed residual_max / brief / restricted fields, which are the "
        "same computation and are on both sides"
    ),
    "exit_audit.mixed": (
        "the second ruler's audit, which the earlier side had no way to take.  "
        "It is a second measurement of the same exit state, not a difference "
        "in it: the exit state itself is compared through the fields above and "
        "through every output-file line"
    ),
    "exit_audit.rulers_note": (
        "the sentence saying that the two rulers are published together, "
        "present only on the side that has two"
    ),
    "coupling_state_provenance.predicate_mode": (
        "the loaded spec's stamp of the ruler, beside the tolerance it already "
        "carried; absent on the earlier side"
    ),
    # The per-attempt costs (DR7).  Eight names, and the reason is one: each is
    # a field whose value is *null or absent on the earlier side because the
    # driver stamped nothing at an attempt boundary* and a number on the later
    # one.  What is NOT here is the load-bearing part: every attempt's exit
    # code, iteration count, finite-difference step and stage name keep their
    # places and are compared element by element on both sides — which is why
    # the exclusions name one leaf of each attempt rather than the attempts
    # list.  The run totals these decompose (node_calls_solve_phase,
    # node_calls_total, dispatch_sweeps, the sweep histogram) are compared in
    # full, so a stamp that moved any of them would be caught by them.
    "attempts[].node_calls_solve_phase": (
        "null before the driver stamped an attempt boundary, a number after: "
        "the count is the change.  The total it decomposes is compared"
    ),
    "attempts[].sweeps": (
        "null before, a number after; the run's sweep total and its "
        "per-evaluation histogram are both compared in full"
    ),
    "attempts[].sweeps_by_block": (
        "absent before, a per-block mapping after; empty in these runs, "
        "because the reference arms build no block schedule"
    ),
    "attempts[].sweeps_per_eval": (
        "absent before, the attempt's own binned evaluations after.  The "
        "run-level histogram of the same sweeps is compared, value for value"
    ),
    "attempts[].stage_positional": (
        "absent before: the harness's positional guess at the rung's name was "
        "the only name there was, and it was carried in 'stage', which IS "
        "compared.  It is now beside the driver's own name so the two can be "
        "checked against each other"
    ),
    "attempts[].ladder": (
        "absent before: nothing numbered the ladders, because nothing stamped "
        "one"
    ),
    "attempts[].cost_null_because": (
        "the sentence explaining the absent per-attempt cost, present only on "
        "the side that had none"
    ),
    "attempts_node_calls_available": (
        "the field says whether the driver stamped the boundaries of this "
        "run's attempts.  False before, because it stamped none; true after on "
        "the optimisation arm, and still false on the evaluation arm, which "
        "runs no optimiser and therefore has no attempt to stamp — so on that "
        "arm the two sides agree and the exclusion costs the comparison "
        "nothing"
    ),
    "attempt_accounting": (
        "the block the decomposition and its residual are published in: absent "
        "on the earlier side entirely"
    ),
    "dispatch_sweeps_solve_phase": (
        "absent before, the solve-phase sweep total after.  The cell is not "
        "new — the driver has always incremented the sweep counter, and the "
        "run total and the per-evaluation histogram are both compared — what "
        "is new is freezing it where the node counter was already frozen"
    ),
}

#: A conditional name whose presence cannot be decided from its own leaf, and
#: the path whose presence decides it instead.  The default -- a name absent
#: from this map -- is the name's own leaf: excluded where it is absent on one
#: side, or null against a value.  A name **in** this map is excluded where the
#: *witness* is null or absent on exactly one side, whatever the name's own
#: leaves read.
#:
#: The live case, and why the default is not enough: the count of components
#: the restriction excluded reads ``0`` on a record where the statistic was
#: never computed.  Both sides then carry a number, both non-null, and the
#: default condition would compare 0 against 122 and fail -- reporting the
#: absence of a computation as a difference in behaviour.
CONDITIONAL_WITNESS: dict[str, str] = {
    "exit_audit.frozen.n_excluded_from_the_restricted_statistic": (
        "exit_audit.frozen.restricted"
    ),
    "exit_audit.mixed.n_excluded_from_the_restricted_statistic": (
        "exit_audit.mixed.restricted"
    ),
}

#: The record path that says **which instrument** made a record's exit-audit
#: residual.  A record written before the instrument existed carries nothing
#: there, which counts as a different instrument: that is the case this gate
#: has to straddle, not a special case of it.
EXIT_AUDIT_INSTRUMENT_PATH = "exit_audit.instrument.restores"


def exit_audit_instrument(record: Mapping[str, Any]) -> str | None:
    """Which exit-audit instrument wrote this record, or None if it says none."""
    if not records_mod.has_path(record, EXIT_AUDIT_INSTRUMENT_PATH):
        return None
    value = records_mod.resolve_path(record, EXIT_AUDIT_INSTRUMENT_PATH)
    return None if value is None else str(value)


#: The leaves of an exit-audit block that the residual **determines**: the
#: maximum, which component carries it, how many components are above the
#: tolerance, and the counts of components that moved in a way the residual
#: classifies.  Everything else in the block — the tolerance, the ruler's name,
#: the file the vector went to, and the restriction's own population and digest
#: — is a declared constant of the measurement and is compared across any
#: pairing whatever.  The split is the difference between excluding a number
#: and excluding the block it sits in.
_RESIDUAL_DERIVED_LEAVES: tuple[str, ...] = (
    "residual_max",
    "residual_max_hex",
    "brief.max",
    "brief.argmax",
    "brief.n_above",
    "brief.n_discrete_mismatch",
    "brief.n_constant_moved",
    "brief.n_nan_new",
    "restricted.max",
    "restricted.max_hex",
    "restricted.argmax",
    "restricted.n_above",
)

#: The same, for the per-ruler blocks, which carry a fuller account of the
#: residual than the unprefixed fields do.  ``detail.ruler`` and
#: ``detail.n_continuous_tested`` are deliberately **not** here: the ruler's
#: name and the size of the tested population are not the residual.
_RESIDUAL_DERIVED_RULER_LEAVES: tuple[str, ...] = (
    "detail.max",
    "detail.argmax",
    "detail.n_above",
    "detail.argmax_value_over_scale",
    "detail.n_bound_by_the_current_value",
    "detail.binding_components",
    "detail.n_discrete_mismatch",
    "detail.n_constant_moved",
    "detail.n_nan_new",
)

_INSTRUMENT_RESIDUAL_REASON = (
    "a value the exit audit's residual determines, and the two captures' "
    "residuals were measured by different instruments: the earlier capture's "
    "sweep ran on the state PROCESS's output path left, this one's on the "
    "state the loop handed over.  The sweep, the ruler, the tolerance and the "
    "restriction are unchanged and are compared across this pairing like "
    "anything else; what changed is what the audit puts back before it sweeps"
)

#: Record leaves that **an instrument change between the two captures** moves,
#: with both sides carrying the leaf and neither side wrong.  A third kind of
#: exclusion, and the reason it is not one of the other two:
#:
#: * :data:`ALWAYS_EXCLUDED` is for leaves *no* pair of runs could compare — a
#:   path, a timing, the commit.  These are comparable, and are compared
#:   wherever the two sides were measured the same way.
#: * :data:`FIELDS_ADDED_BY_A_DRIVER_CHANGE` is for leaves one side **lacks**.
#:   These are present on both sides and non-null on both; the condition there
#:   cannot decide them, and comparing them would report a changed *instrument*
#:   as changed *behaviour* — which is the one thing G1 must not do, in either
#:   direction.
#:
#: So each name here is excluded exactly when the two records' instrument
#: stamps differ (:data:`EXIT_AUDIT_INSTRUMENT_PATH`), and compared whenever
#: they agree.  The condition is intrinsic to the pair rather than set by the
#: caller, so a later gate cannot forget it, and **a tooth shows the other
#: half**: a residual moved by one unit in the last place between two records
#: made by the *same* instrument is still caught and named.
#:
#: The live case is ruling **D25**: the exit audit now puts the data structure
#: back to its solve-phase state before its sweep, so the sweep evaluates the
#: map the loop iterated rather than the one PROCESS's output path left behind.
#: Every residual moves, on both sides of the audit's two positions, and
#: nothing about the driver moved with it — which is exactly what the rest of
#: this gate's several thousand values, and all 51 thousand output-file lines,
#: are there to say.
FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE: dict[str, str] = {
    **{
        f"exit_audit.{leaf}": _INSTRUMENT_RESIDUAL_REASON
        for leaf in _RESIDUAL_DERIVED_LEAVES
    },
    **{
        f"exit_audit.{ruler}.{leaf}": _INSTRUMENT_RESIDUAL_REASON
        for ruler in records_mod.AUDIT_RULERS
        for leaf in _RESIDUAL_DERIVED_LEAVES + _RESIDUAL_DERIVED_RULER_LEAVES
    },
    "exit_audit.instrument": (
        "the instrument's own account of itself: which positions it "
        "snapshotted, what it put back and what it could not.  Absent before "
        "the mechanism existed, a block after"
    ),
    # One leaf, not the block.  The hook is now installed whatever audit
    # position was asked for, so this flag flips from False to True across the
    # change; everything else the block holds -- which positions were reached,
    # how many components each snapshot took, and the coupling-state digest at
    # each position -- is unchanged and stays compared.  Excluding the block
    # would hide those digests, and they are a **behaviour witness**: they say
    # the driver snapshotted the same state at the same places.  It hid nothing
    # on this pairing (measured: only `installed` and `audit_position_note`
    # differ once the block exclusion is lifted), and that is exactly why it
    # had to go -- an exclusion that costs nothing today is still an exclusion
    # nobody will notice tomorrow.
    "audit_snapshot.installed": (
        "whether the driver's snapshot hook was installed at all.  False on "
        "the earlier side wherever the audit position did not need a "
        "coupling-state snapshot, True on this one, because the hook is now "
        "installed at every audit position -- the whole-data-structure "
        "snapshot is needed even where the coupling-state one is not.  The "
        "positions the hook reached, their component counts and their digests "
        "sit beside this flag in the same block and are compared"
    ),
    "audit_position_note": (
        "the sentence saying how the audit position is reached, which the "
        "instrument change rewrites.  audit_position itself is compared, and "
        "two captures that disagree on it are refused before any value is"
    ),
}

#: What kind of thing each instrument-change name is, on the same rule as
#: :data:`ALWAYS_EXCLUDED_KIND`: a name nobody classified is a name nobody
#: reviewed, and the import refuses one.
INSTRUMENT_CHANGE_KIND: dict[str, str] = {
    **{
        name: "a value the audit's residual determines"
        for name in FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE
        if name.startswith("exit_audit.") and name != "exit_audit.instrument"
    },
    "exit_audit.instrument": "the instrument's own description of itself",
    "audit_snapshot.installed": "whether the instrument was installed at all",
    "audit_position_note": "prose the instrument change rewrites",
}


#: Every name either group holds, which is what a reader looking for "is this
#: excluded?" wants and what :func:`is_volatile` matches against by default.
#: The *gate* uses the two groups separately, so that the conditional ones are
#: compared wherever both sides carry them.
VOLATILE_RECORD_PATHS: dict[str, str] = {
    **ALWAYS_EXCLUDED,
    **FIELDS_ADDED_BY_A_DRIVER_CHANGE,
    **FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE,
}

#: Keys of PROCESS's own output file that record when and where a run happened
#: rather than what it computed.  Matched as ``(key)`` anywhere in the line.
VOLATILE_MFILE_KEYS: dict[str, str] = {
    "date": "the calendar date the run started",
    "time": "the clock time the run started",
    "username": "who ran it",
    "fileprefix": "the absolute path of the run's own input file",
    "procver": "the version string written when the tree was packaged",
    "tagno": "git describe of the commit -- different commits by construction",
    "branch_name": "the branch the tree is on",
    "process_runtime": "PROCESS's own timing of itself",
}

#: The two runs G1 makes on every configuration.  Both are reference arms: they
#: compose to an environment with the whole switch vocabulary cleared, which is
#: precisely the condition G1 is about.
NEUTRAL_ARMS: tuple[tuple[str, str], ...] = (("B", "BR"), ("A", "AR"))

#: Where G1's optimisation runs take their exit audit, on **both** sides.
#:
#: G1 binds the driver, and the two captures are made by the harness as it
#: stood at each commit.  Where a driver change also moves a harness-side
#: instrument, pinning that instrument to one position on both sides is what
#: keeps the comparison about the driver: the whole ``exit_audit`` block --
#: residual, argmax, brief, restricted statistic, the audit's own node count --
#: is then compared value for value instead of excluded.  The alternative,
#: letting each side audit wherever its own revision does and excluding the
#: block, would put the strongest thing G1 compares outside the comparison.
#: A capture whose records disagree about the position **refuses**.
NEUTRAL_AUDIT_POSITION = "after_run"


def neutrality_root(campaign: Campaign) -> Path:
    return Path(campaign.runs_dir) / GATES_SUBPATH / "switch_neutrality"


def neutrality_run_dir(campaign: Campaign, label: str, configuration: str, arm: str) -> Path:
    return neutrality_root(campaign) / label / configuration / arm


def capture_neutrality(
    campaign: Campaign, label: str, *, resume: bool = False
) -> dict[str, Any]:
    """Run the neutral arms on every configuration and record where they went.

    *label* is ``before`` or ``after``: the copy immediately before the driver
    change, and the copy after it.  Nothing is compared here; capturing and
    comparing are separate so that the "before" side is taken at the commit it
    claims to be taken at and cannot be re-taken later to make a comparison
    agree.
    """
    if label not in ("before", "after"):
        raise GateError(
            f"{label!r} is neither 'before' nor 'after'; G1 compares exactly "
            f"those two captures"
        )
    jobs = []
    for config in campaign.configurations:
        for phase, arm in NEUTRAL_ARMS:
            jobs.append(
                pool_mod.Job(
                    phase=phase,
                    arm=arm,
                    config=config,
                    seed=0,
                    outdir=neutrality_run_dir(campaign, label, config.name, arm),
                    regime="unperturbed",
                    delta=campaign.delta if phase == "B" else None,
                    run_kind="gate",
                    audit_position=NEUTRAL_AUDIT_POSITION,
                )
            )
    results = pool_mod.run_all(jobs, campaign, resume=resume)
    manifest = {
        "label": label,
        "captured": _dt.datetime.now().isoformat(timespec="seconds"),
        "tree_git_head": _git_head(),
        "tree": str(campaign.tree),
        "n_runs": len(jobs),
        "audit_position": NEUTRAL_AUDIT_POSITION,
        "runs": [
            {
                "configuration": job.config.name,
                "arm": job.arm,
                "phase": job.phase,
                "outdir": str(job.outdir),
                "status": (results[i] or {}).get("status") if isinstance(results, list) else None,
            }
            for i, job in enumerate(jobs)
        ],
    }
    path = neutrality_root(campaign) / label / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    manifest["manifest"] = str(path)
    return manifest


# --- the comparison itself -------------------------------------------------


def leaves(document: Any, prefix: str = "") -> dict[str, Any]:
    """Every scalar of a record, keyed by its dotted path.

    Lists are expanded element by element (``xcs[3]``) rather than compared
    whole, so a mismatch names the element that moved instead of the list that
    contains it.  An empty list is itself a leaf, so that a list becoming empty
    is a difference and not an absence.
    """
    out: dict[str, Any] = {}
    if isinstance(document, dict):
        if not document:
            out[prefix or "<root>"] = "{}"
            return out
        for key, value in document.items():
            out.update(leaves(value, f"{prefix}.{key}" if prefix else str(key)))
    elif isinstance(document, list):
        if not document:
            out[f"{prefix}[]"] = "[]"
            return out
        for index, value in enumerate(document):
            out.update(leaves(value, f"{prefix}[{index}]"))
    else:
        out[prefix] = document
    return out


#: ``[3]`` -> ``[]``, so that an exclusion can name **one leaf of every
#: element of a list** rather than the whole list.  Added by task A60
#: (driver-attempts): the per-attempt costs are new fields inside ``attempts``,
#: a list whose other fields — the exit code, the iteration count, the
#: finite-difference step — must stay compared.  Excluding the list by its bare
#: name would have taken all of them out of the comparison, which is exactly
#: the "zero over a quietly smaller population" this gate is built against.
_LIST_INDEX = re.compile(r"\[\d+\]")


def is_volatile(
    path: str, excluded: Mapping[str, str] | None = None
) -> str | None:
    """The reason *path* is excluded from the comparison, or None.

    *excluded* defaults to G1's set.  A gate that compares two runs for a
    different reason passes its own, because an exclusion is only defensible
    against the claim it is made under: G1 excludes the commit because its two
    sides are at different commits, and gate G8's two sides are not.

    An exclusion name is matched two ways.  A plain name matches the path's
    **bare** form — everything before the first list index — as an exact match
    or as a prefix, which is how every exclusion written before this worked and
    still works.  A name containing ``[]`` matches the path with its list
    indices normalised, so ``attempts[].sweeps`` excludes that one leaf of every
    attempt and leaves the rest of each attempt compared.
    """
    table = VOLATILE_RECORD_PATHS if excluded is None else excluded
    bare = path.split("[")[0]
    indexed = _LIST_INDEX.sub("[]", path)
    for name, reason in table.items():
        if "[]" in name:
            if indexed == name or indexed.startswith(name + "."):
                return reason
            continue
        if bare == name or bare.startswith(name + "."):
            return reason
    return None


def _block_present(document: Mapping[str, Any], path: str) -> bool:
    """Is *path* there and not null in *document*?"""
    return records_mod.has_path(document, path) and (
        records_mod.resolve_path(document, path) is not None
    )


def _conditional_witness(
    path: str, conditional: Mapping[str, str]
) -> str | None:
    """The path whose presence decides whether *path* is excluded, or None.

    Only names the caller's own conditional table holds can have a witness, so
    a gate that passes its own table is never surprised by one written for
    another gate.
    """
    bare = path.split("[")[0]
    for name, witness in CONDITIONAL_WITNESS.items():
        if name not in conditional:
            continue
        if bare == name or bare.startswith(name + "."):
            return witness
    return None


def compare_records(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    *,
    excluded: Mapping[str, str] | None = None,
    conditional: Mapping[str, str] | None = None,
    instrument_changed: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Every deterministic leaf of two records, compared without tolerance.

    ``excluded`` names leaves that can never be compared.  ``conditional`` names
    leaves that a change **adds**: each is excluded only where one side lacks it
    — absent, or null against a value — and compared wherever both sides carry
    it.  That distinction is task **A52 (harness-gates)**'s, and it is the
    difference between an exclusion that applies to the pair of commits it was
    written for and one that hides a field for ever.

    ``instrument_changed`` names leaves that **a change to the measuring
    instrument** moves, with both sides carrying them.  Each is excluded
    exactly where the two records say they were measured by different
    instruments — the stamp at :data:`EXIT_AUDIT_INSTRUMENT_PATH`, a record
    that carries none counting as a different one — and compared wherever the
    stamps agree.  The condition is read off the pair here rather than decided
    by the caller, so a gate cannot pass the table and forget the condition,
    and a residual that moves between two records made the same way is still a
    mismatch.
    """
    a, b = leaves(dict(before)), leaves(dict(after))
    every = sorted(set(a) | set(b))
    missing = object()
    instruments = (exit_audit_instrument(before), exit_audit_instrument(after))
    instrument_moved = instruments[0] != instruments[1]
    compared, excluded_paths, mismatches = 0, [], []
    conditionally_excluded: list[str] = []
    conditionally_compared: list[str] = []
    instrument_excluded: list[str] = []
    instrument_compared: list[str] = []
    for path in every:
        reason = is_volatile(path, excluded)
        if reason is not None:
            excluded_paths.append(path)
            continue
        if (
            instrument_changed is not None
            and is_volatile(path, instrument_changed) is not None
            and (conditional is None or is_volatile(path, conditional) is None)
        ):
            if instrument_moved:
                excluded_paths.append(path)
                instrument_excluded.append(path)
                continue
            instrument_compared.append(path)
        if conditional is not None and is_volatile(path, conditional) is not None:
            witness = _conditional_witness(path, conditional)
            if witness is not None:
                one_sided = _block_present(before, witness) != _block_present(
                    after, witness
                )
            else:
                va, vb = a.get(path, missing), b.get(path, missing)
                one_sided = ((va is missing) != (vb is missing)) or (
                    (va is None) != (vb is None)
                )
            if one_sided:
                excluded_paths.append(path)
                conditionally_excluded.append(path)
                continue
            conditionally_compared.append(path)
            if (
                instrument_changed is not None
                and is_volatile(path, instrument_changed) is not None
            ):
                if instrument_moved:
                    excluded_paths.append(path)
                    conditionally_compared.pop()
                    instrument_excluded.append(path)
                    continue
                instrument_compared.append(path)
        compared += 1
        va, vb = a.get(path, missing), b.get(path, missing)
        if va is missing or vb is missing:
            mismatches.append(
                {
                    "field": path,
                    "before": "<absent>" if va is missing else va,
                    "after": "<absent>" if vb is missing else vb,
                    "why": "the field is present on one side only",
                }
            )
            continue
        if not _same(va, vb):
            mismatches.append({"field": path, "before": va, "after": vb})
    return {
        "n_compared": compared,
        "n_excluded": len(excluded_paths),
        "excluded": excluded_paths,
        "n_conditionally_excluded": len(conditionally_excluded),
        "conditionally_excluded": conditionally_excluded,
        "n_conditionally_compared": len(conditionally_compared),
        "exit_audit_instrument": {
            "before": instruments[0],
            "after": instruments[1],
            "differs": instrument_moved,
            "what_it_means": (
                "the two records were measured by different exit-audit "
                "instruments, so the leaves the instrument moves are excluded "
                "by name below and everything else is compared as usual"
                if instrument_moved
                else "the two records were measured by the same exit-audit "
                "instrument, so nothing is excluded on that ground and a "
                "residual that moved would be a mismatch"
            ),
        },
        "n_excluded_by_the_instrument_change": len(instrument_excluded),
        "excluded_by_the_instrument_change": instrument_excluded,
        "n_compared_although_the_instrument_table_names_them": len(
            instrument_compared
        ),
        "n_mismatched": len(mismatches),
        "mismatches": mismatches,
    }


def _same(a: Any, b: Any) -> bool:
    """Bit equality for floats, plain equality otherwise.

    ``==`` says two NaNs differ and says ``-0.0 == 0.0``; neither is what a
    byte-identity gate means, so floats are compared through their hex form.
    """
    if isinstance(a, float) and isinstance(b, float):
        if math.isnan(a) or math.isnan(b):
            return math.isnan(a) and math.isnan(b)
        return a.hex() == b.hex()
    return a == b


def mfile_lines(path: Path) -> list[str]:
    return path.read_text(errors="replace").splitlines()


def mfile_volatile(line: str) -> str | None:
    for key, reason in VOLATILE_MFILE_KEYS.items():
        if f"({key})" in line:
            return reason
    return None


def compare_mfiles(before: Path, after: Path) -> dict[str, Any]:
    """PROCESS's own output file, line by line, with the metadata lines named."""
    a, b = mfile_lines(before), mfile_lines(after)
    n_excluded = 0
    differing: list[dict[str, Any]] = []
    for index in range(max(len(a), len(b))):
        la = a[index] if index < len(a) else None
        lb = b[index] if index < len(b) else None
        source = la if la is not None else lb
        if source is not None and mfile_volatile(source) is not None:
            n_excluded += 1
            continue
        if la != lb:
            differing.append({"line": index + 1, "before": la, "after": lb})
    return {
        "before": str(before),
        "after": str(after),
        "n_lines_before": len(a),
        "n_lines_after": len(b),
        "n_lines_compared": max(len(a), len(b)) - n_excluded,
        "n_lines_excluded": n_excluded,
        "n_lines_differing": len(differing),
        "differing": differing[:20],
    }


def _mfile_for(outdir: Path, configuration: str) -> Path | None:
    named = Path(outdir) / f"{configuration}.MFILE.DAT"
    if named.exists():
        return named
    candidates = sorted(Path(outdir).glob("*MFILE.DAT"))
    return candidates[0] if candidates else None


def _read_record(directory: Path, *, side: str, key: str) -> dict[str, Any]:
    path = Path(directory) / "metrics.json"
    if not path.exists():
        raise GateError(
            f"G1 has no {side} record for {key}: {path} is not there.  A gate "
            f"that cannot find one of its two sides must refuse, never skip -- "
            f"a check with no population is not a check (trap T11)."
        )
    return json.loads(path.read_text())


def _assert_same_audit_position(
    before: Mapping[str, Any], after: Mapping[str, Any], *, key: str
) -> str | None:
    """Refuse unless both captures measured their accuracy at the same place.

    The ``exit_audit`` block is the most sensitive thing G1 compares, and it is
    only comparable if both sides took it at the same position.  A capture made
    at one position against a capture made at another would report the moved
    instrument as a driver difference -- or, worse, be "fixed" by excluding the
    block, which is how a gate quietly stops testing the thing it is for.
    """
    a, b = before.get("audit_position"), after.get("audit_position")
    if a != b:
        raise GateError(
            f"G1 cannot compare {key}: the 'before' capture audited at {a!r} "
            f"and the 'after' capture at {b!r}.  The exit audit is only "
            f"comparable at one position, and moving it between captures would "
            f"report the instrument as a driver difference.  Re-capture one "
            f"side at the other's position; do not exclude the block."
        )
    return a


def neutrality_body(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    """Compare the two captures, run by run, value by value and line by line.

    **The "before" capture is never re-made.**  If one is already there it is
    read and nothing is run; only when there is none at all does the gate make
    one, at the current commit, so that pressing the one button on a fresh tree
    gets an answer rather than a refusal — an answer the verdict then labels as
    a self-comparison rather than a neutrality result (:func:`_straddle`).

    That guard is load-bearing, and the reason is measured rather than assumed:
    a "before" capture made at an earlier commit carries records written by an
    earlier record schema, and ``pool.run``'s resume consults the **current**
    completeness contract — so it judges those records incomplete and would
    re-run them.  Measured at this commit: the trunk capture's optimisation
    records lack ``per_run_artifact``, which this task declared, so resume keeps
    the evaluation records and rejects the optimisation ones.  A capture that
    can only be made at a commit already behind us must therefore never be
    handed to resume, and this function does not hand it to anything.
    """
    _capture_before_if_there_is_none(campaign)
    _capture_after(campaign, resume=resume)
    rows: list[dict[str, Any]] = []
    n_values = n_excluded_values = n_value_mismatches = 0
    n_lines = n_excluded_lines = n_line_mismatches = 0
    n_instrument_excluded = 0
    instruments: list[dict[str, Any]] = []
    passed = True
    for config in campaign.configurations:
        for phase, arm in NEUTRAL_ARMS:
            key = f"{arm}/{config.name}"
            before_dir = neutrality_run_dir(campaign, "before", config.name, arm)
            after_dir = neutrality_run_dir(campaign, "after", config.name, arm)
            before = _read_record(before_dir, side="before", key=key)
            after = _read_record(after_dir, side="after", key=key)
            _assert_same_audit_position(before, after, key=key)
            values = compare_records(
                before,
                after,
                excluded=ALWAYS_EXCLUDED,
                conditional=FIELDS_ADDED_BY_A_DRIVER_CHANGE,
                instrument_changed=FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE,
            )
            mfile_before = _mfile_for(before_dir, config.name)
            mfile_after = _mfile_for(after_dir, config.name)
            if mfile_before is None or mfile_after is None:
                raise GateError(
                    f"G1 has no output file for {key} on one side "
                    f"({mfile_before} / {mfile_after}); the line comparison "
                    f"would be over nothing"
                )
            mfile = compare_mfiles(mfile_before, mfile_after)
            row = {
                "arm": arm,
                "phase": phase,
                "configuration": config.name,
                "status_before": before.get("status"),
                "status_after": after.get("status"),
                "record": values,
                "mfile": mfile,
                "passed": (
                    before.get("status") == "ok"
                    and after.get("status") == "ok"
                    and values["n_mismatched"] == 0
                    and mfile["n_lines_differing"] == 0
                ),
            }
            rows.append(row)
            passed = passed and row["passed"]
            n_values += values["n_compared"]
            n_excluded_values += values["n_excluded"]
            n_instrument_excluded += values["n_excluded_by_the_instrument_change"]
            instruments.append(
                {"pair": key, **values["exit_audit_instrument"]}
            )
            n_value_mismatches += values["n_mismatched"]
            n_lines += mfile["n_lines_compared"]
            n_excluded_lines += mfile["n_lines_excluded"]
            n_line_mismatches += mfile["n_lines_differing"]
    before_manifest = neutrality_root(campaign) / "before" / "manifest.json"
    after_manifest = neutrality_root(campaign) / "after" / "manifest.json"
    straddle = _straddle(before_manifest, after_manifest)
    return {
        "passed": passed,
        "straddle": straddle,
        "population": (
            f"{straddle['says']}  "
            f"{len(rows)} run pair(s) = {len(campaign.configurations)} "
            f"configuration(s) x {len(NEUTRAL_ARMS)} reference arm(s); "
            f"{n_values} deterministic record values and {n_lines} output-file "
            f"lines compared without tolerance, {n_excluded_values} record "
            f"values and {n_excluded_lines} lines excluded as run metadata "
            f"(each named, with its reason, in this record), of which "
            f"{n_instrument_excluded} are excluded because the two captures' "
            f"exit audits were taken by different instruments — named one by "
            f"one, and compared again the moment the two stamps agree"
        ),
        "n_pairs": len(rows),
        "n_values_compared": n_values,
        "n_values_excluded": n_excluded_values,
        "n_values_excluded_by_the_instrument_change": n_instrument_excluded,
        "exit_audit_instruments": instruments,
        "instrument_change_straddled": any(row["differs"] for row in instruments),
        "n_values_differing": n_value_mismatches,
        "n_mfile_lines_compared": n_lines,
        "n_mfile_lines_excluded": n_excluded_lines,
        "n_mfile_lines_differing": n_line_mismatches,
        "audit_position_on_both_sides": NEUTRAL_AUDIT_POSITION,
        "excluded_record_paths": VOLATILE_RECORD_PATHS,
        "excluded_across_an_instrument_change": FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE,
        "excluded_mfile_keys": VOLATILE_MFILE_KEYS,
        "reference_fields_for_context": {
            phase: list(fields) for phase, fields in reference_mod.REFERENCE_FIELDS.items()
        },
        "before_manifest": json.loads(before_manifest.read_text())
        if before_manifest.exists()
        else None,
        "after_manifest": json.loads(after_manifest.read_text())
        if after_manifest.exists()
        else None,
        "runs": rows,
    }


def _capture_before_if_there_is_none(campaign: Campaign) -> None:
    """Make a "before" capture only where there is not one already."""
    manifest = neutrality_root(campaign) / "before" / "manifest.json"
    if manifest.exists():
        return
    print(
        "  gate G1 has no 'before' capture; making one at this commit.  Both "
        "sides will then be the same code, which the verdict says out loud: "
        "it is a determinism and exclusion-coverage result, not a "
        "driver-change one.",
        flush=True,
    )
    capture_neutrality(campaign, "before", resume=False)


def _capture_after(campaign: Campaign, *, resume: bool) -> None:
    """The "after" capture: this tree, this commit, re-made unless resuming.

    Unlike the "before" capture it is always re-makeable — it is a capture of
    the tree the gate is being run in — so it follows the ordinary rule: kept
    when ``--resume`` asks for it, re-made when it does not.
    """
    manifest = neutrality_root(campaign) / "after" / "manifest.json"
    if resume and manifest.exists():
        return
    capture_neutrality(campaign, "after", resume=resume)


def _straddle(before_manifest: Path, after_manifest: Path) -> dict[str, Any]:
    """What this run of G1 actually straddles, said out loud.

    G1's claim is that a **driver change** is inert when its switches are unset,
    and that claim needs two captures at two commits.  Made at one commit the
    same comparison is still worth running — it shows the run path is
    deterministic and that the exclusion set covers what it claims — but it is
    **not** a neutrality result, and a PASS from it must not read like one in
    the plan's gate table.  So the verdict record, the printed population and
    the table row all say which of the two this run was.
    """
    heads = {}
    for label, path in (("before", before_manifest), ("after", after_manifest)):
        heads[label] = (
            (json.loads(path.read_text()).get("tree_git_head") or None)
            if path.exists()
            else None
        )
    if heads["before"] and heads["before"] == heads["after"]:
        return {
            "straddles_a_change": False,
            "before_commit": heads["before"],
            "after_commit": heads["after"],
            "says": (
                f"BOTH CAPTURES AT {heads['before'][:8]}: determinism and "
                f"exclusion coverage, NOT a driver-change result."
            ),
        }
    if heads["before"] and heads["after"]:
        return {
            "straddles_a_change": True,
            "before_commit": heads["before"],
            "after_commit": heads["after"],
            "says": (
                f"straddles {heads['before'][:8]} -> {heads['after'][:8]}: a "
                f"neutrality result."
            ),
        }
    return {
        "straddles_a_change": None,
        "before_commit": heads["before"],
        "after_commit": heads["after"],
        "says": (
            "one capture names no commit, so what this run straddles cannot "
            "be stated:"
        ),
    }


def _neutrality_teeth(campaign: Campaign) -> tuple[Tooth, ...]:
    """Breaks on throwaway copies; neither capture is ever touched."""

    def sample_record() -> tuple[dict[str, Any], str]:
        config = campaign.configurations[0]
        directory = neutrality_run_dir(campaign, "before", config.name, "BR")
        return _read_record(directory, side="before", key=f"BR/{config.name}"), config.name

    def sample_carrying_the_restricted_block() -> tuple[dict[str, Any], str, str]:
        """A captured record that **has** the restricted statistic, and which side.

        The tooth below builds the *earlier* shape by nulling that block, so it
        needs a record that carries one.  Taking the "before" side
        unconditionally was a defect: in a genuine straddle the earlier commit
        never computed the statistic, the block is null there, and the tooth
        could not be built at all — it reported "no restricted statistic" and
        did not trip, in exactly the run where it matters most.
        """
        for side in ("after", "before"):
            for config in campaign.configurations:
                directory = neutrality_run_dir(campaign, side, config.name, "BR")
                if not (Path(directory) / "metrics.json").exists():
                    continue
                record = _read_record(
                    directory, side=side, key=f"BR/{config.name}"
                )
                if (record.get("exit_audit") or {}).get("restricted") is not None:
                    return record, config.name, side
        raise GateError(
            "neither capture carries a restricted statistic on any "
            "configuration, so the exclusion that covers it cannot be shown to "
            "cover anything"
        )

    def one_ulp() -> tuple[bool, str]:
        record, _name = sample_record()
        moved = copy.deepcopy(record)
        target = "values.norm_objf"
        value = (moved.get("values") or {}).get("norm_objf")
        if not isinstance(value, float):
            return False, "the sample record carries no values.norm_objf to move"
        nudged = math.nextafter(value, math.inf)
        moved["values"]["norm_objf"] = nudged
        result = compare_records(record, moved)
        return (
            result["n_mismatched"] == 1
            and result["mismatches"][0]["field"] == target,
            f"{target} moved by one unit in the last place "
            f"({value.hex()} -> {nudged.hex()}) -> "
            f"{result['n_mismatched']} of {result['n_compared']} values differ",
        )

    def one_line() -> tuple[bool, str]:
        config = campaign.configurations[0]
        directory = neutrality_run_dir(campaign, "before", config.name, "BR")
        mfile = _mfile_for(directory, config.name)
        if mfile is None:
            return False, f"no output file under {directory}"
        import tempfile  # noqa: PLC0415 - tooth path only

        with tempfile.TemporaryDirectory() as td:
            twin = Path(td) / mfile.name
            lines = mfile_lines(mfile)
            index = next(
                (
                    i
                    for i, line in enumerate(lines)
                    if mfile_volatile(line) is None and "(ifail)" in line
                ),
                None,
            )
            if index is None:
                return False, "the output file has no (ifail) line to change"
            broken = list(lines)
            broken[index] = broken[index].replace("1 ", "2 ", 1)
            twin.write_text("\n".join(broken) + "\n")
            result = compare_mfiles(mfile, twin)
        return (
            result["n_lines_differing"] >= 1,
            f"line {index + 1} of {mfile.name} (the exit code) changed -> "
            f"{result['n_lines_differing']} of {result['n_lines_compared']} "
            f"compared lines differ",
        )

    def missing_before() -> tuple[bool, str]:
        import tempfile  # noqa: PLC0415 - tooth path only

        with tempfile.TemporaryDirectory() as td:
            try:
                _read_record(Path(td) / "not_there", side="before", key="BR/tooth")
            except GateError as exc:
                return True, f"refused: {str(exc).splitlines()[0][:160]}"
        return False, "a missing 'before' record did not refuse"

    def moved_audit_position() -> tuple[bool, str]:
        record, _name = sample_record()
        moved = copy.deepcopy(record)
        moved["audit_position"] = "entry_to_write_output_files"
        try:
            _assert_same_audit_position(record, moved, key="BR/tooth")
        except GateError as exc:
            return True, f"refused: {str(exc).splitlines()[0][:170]}"
        return False, "two captures audited at different positions and compared anyway"

    def the_new_exclusion_is_load_bearing() -> tuple[bool, str]:
        """What excluding ``exit_audit.restricted`` actually covers.

        Task A52 (harness-gates) handed the optimisation phase the two
        artifacts the restricted statistic is derived from, so the block is a
        block on an optimisation record where it used to be null.  An exclusion
        added without measuring what it hides is an exclusion nobody checked,
        so this tooth builds the *earlier* shape — the same record with the
        block nulled — and compares it against the record itself **without**
        the exclusion.  The comparison must report the leaves the block holds;
        with the exclusion in place it reports none, which is the whole of what
        the exclusion costs.
        """
        record, name, side = sample_carrying_the_restricted_block()
        earlier = copy.deepcopy(record)
        earlier["exit_audit"]["restricted"] = None
        without = {
            k: v
            for k, v in FIELDS_ADDED_BY_A_DRIVER_CHANGE.items()
            if k != "exit_audit.restricted"
        }
        uncovered = compare_records(
            earlier, record, excluded=ALWAYS_EXCLUDED, conditional=without
        )
        covered = compare_records(
            earlier,
            record,
            excluded=ALWAYS_EXCLUDED,
            conditional=FIELDS_ADDED_BY_A_DRIVER_CHANGE,
        )
        return uncovered["n_mismatched"] > 0 and covered["n_mismatched"] == 0, (
            f"on BR/{name} ({side} side), nulling exit_audit.restricted — the shape the "
            f"record had before the optimisation phase was handed the per-run "
            f"artifact and the write census — makes "
            f"{uncovered['n_mismatched']} of {uncovered['n_compared']} values "
            f"differ without the exclusion and "
            f"{covered['n_mismatched']} of {covered['n_compared']} with it.  "
            f"That count is exactly what the exclusion hides"
        )

    def a_real_count_difference_is_still_caught() -> tuple[bool, str]:
        """The witness condition must not hide a difference it does not cover.

        The two per-ruler counts of excluded components are excluded **while
        the restricted block is null on one side**, because a 0 there means
        "not computed".  Where both sides carry the block the counts must be
        compared like anything else — otherwise the condition would be a
        blanket exclusion wearing a condition's clothes.  This moves one count
        by one on a record that carries the block on both sides, and the
        comparison has to catch it.
        """
        record, name, side = sample_carrying_the_restricted_block()
        path = "exit_audit.frozen.n_excluded_from_the_restricted_statistic"
        before_value = records_mod.resolve_path(record, path) if records_mod.has_path(record, path) else None
        if before_value is None:
            return False, f"the sample record carries no {path}"
        moved = copy.deepcopy(record)
        moved["exit_audit"]["frozen"][
            "n_excluded_from_the_restricted_statistic"
        ] = before_value + 1
        result = compare_records(
            record,
            moved,
            excluded=ALWAYS_EXCLUDED,
            conditional=FIELDS_ADDED_BY_A_DRIVER_CHANGE,
        )
        caught = any(m["field"] == path for m in result["mismatches"])
        return caught, (
            f"on BR/{name} ({side} side), which carries the restricted block on "
            f"both sides of this comparison, {path} moved from {before_value} "
            f"to {before_value + 1}: the comparison reports "
            f"{result['n_mismatched']} of {result['n_compared']} values "
            f"differing and names the field — so the condition excludes the "
            f"count only where the block is absent, never where it is there"
        )

    def sample_carrying_the_instrument_stamp() -> tuple[dict[str, Any], str, str]:
        """A captured record whose exit audit says which instrument made it."""
        for side in ("after", "before"):
            for config in campaign.configurations:
                directory = neutrality_run_dir(campaign, side, config.name, "BR")
                if not (Path(directory) / "metrics.json").exists():
                    continue
                record = _read_record(
                    directory, side=side, key=f"BR/{config.name}"
                )
                if exit_audit_instrument(record) is not None:
                    return record, config.name, side
        raise GateError(
            "no capture carries an exit-audit instrument stamp, so the "
            "condition that excludes a residual across an instrument change "
            "cannot be shown to have another half"
        )

    def the_same_instrument_still_catches_a_moved_residual() -> tuple[bool, str]:
        """The instrument exclusion must fire on the instrument, not on the field.

        The leaves an instrument change moves are excluded **while the two
        records say they were measured differently**.  Two records made by the
        same instrument must still be compared on every one of them — otherwise
        the new condition would be a blanket exclusion of the exit audit
        wearing a condition's clothes, and the most sensitive thing this gate
        compares would quietly stop being compared.

        So: one residual moved by a unit in the last place on a copy of a
        record, against the record itself.  Both carry the same stamp.  The
        comparison has to report it and name the field.  The second half of the
        tooth moves the *stamp* as well and requires the same difference to be
        excluded instead — the two halves together are the condition.
        """
        record, name, side = sample_carrying_the_instrument_stamp()
        path = "exit_audit.residual_max_hex"
        value = (record.get("exit_audit") or {}).get("residual_max_hex")
        if not isinstance(value, str):
            return False, f"the sample record carries no {path}"
        moved = copy.deepcopy(record)
        nudged = math.nextafter(float.fromhex(value), math.inf).hex()
        moved["exit_audit"]["residual_max_hex"] = nudged
        same_instrument = compare_records(
            record,
            moved,
            excluded=ALWAYS_EXCLUDED,
            conditional=FIELDS_ADDED_BY_A_DRIVER_CHANGE,
            instrument_changed=FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE,
        )
        other_instrument = copy.deepcopy(moved)
        other_instrument["exit_audit"]["instrument"]["restores"] = (
            str(exit_audit_instrument(record)) + "_something_else"
        )
        across = compare_records(
            record,
            other_instrument,
            excluded=ALWAYS_EXCLUDED,
            conditional=FIELDS_ADDED_BY_A_DRIVER_CHANGE,
            instrument_changed=FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE,
        )
        caught = any(m["field"] == path for m in same_instrument["mismatches"])
        hidden = (
            path in across["excluded_by_the_instrument_change"]
            and not any(m["field"] == path for m in across["mismatches"])
        )
        return caught and hidden, (
            f"on BR/{name} ({side} side), {path} moved {value} -> {nudged}: "
            f"between two records carrying the same instrument stamp the "
            f"comparison reports {same_instrument['n_mismatched']} of "
            f"{same_instrument['n_compared']} values differing and names the "
            f"field; with the stamp itself changed on one side the same "
            f"difference is excluded by name, "
            f"{across['n_excluded_by_the_instrument_change']} leaves in all, "
            f"and {across['n_mismatched']} of {across['n_compared']} values "
            f"differ"
        )

    return (
        Tooth(
            "the_same_instrument_still_catches_a_moved_residual",
            "one exit-audit residual moved by a unit in the last place between "
            "two records carrying the same instrument stamp, and again with "
            "the stamp changed",
            "be caught and named where the instrument is the same, and "
            "excluded by name only where it is not",
            the_same_instrument_still_catches_a_moved_residual,
        ),
        Tooth(
            "a_real_count_difference_with_the_block_on_both_sides",
            "one per-ruler count of excluded components moved by one on a "
            "record that carries the restricted block",
            "still be caught: the condition covers 'not computed', not the count",
            a_real_count_difference_is_still_caught,
        ),
        Tooth(
            "the_new_exclusion_is_load_bearing",
            "the restricted statistic nulled on a throwaway copy of a captured "
            "record, compared with and without the exclusion that covers it",
            "differ without the exclusion and not with it, and say by how much",
            the_new_exclusion_is_load_bearing,
        ),
        Tooth(
            "captures_audited_at_different_positions",
            "a throwaway copy of a captured record with its audit position "
            "moved to the other legal value",
            "REFUSE, not compare",
            moved_audit_position,
        ),
        Tooth(
            "one_value_moved_by_one_ulp",
            "one float of a throwaway copy of a captured record moved by one "
            "unit in the last place",
            "FAIL",
            one_ulp,
        ),
        Tooth(
            "one_output_file_line_changed",
            "one line of a throwaway copy of a captured output file changed",
            "FAIL",
            one_line,
        ),
        Tooth(
            "missing_before_record",
            "the 'before' capture asked for at a directory that does not exist",
            "REFUSE, not skip",
            missing_before,
        ),
    )


# --------------------------------------------------------------------------
# G9 -- the output path writes the state the solve handed over
# --------------------------------------------------------------------------
#
# What G9 binds is the removal of upstream's output-time loop from the two
# intervention arms, and it binds it in the only way that means anything: not
# "the switch was set" but "the state that reached the output files is the
# state the optimiser accepted".
#
# Three criteria on an arm whose matrix cell turns the loop off:
#
#   (i)   the coupling state immediately before the file-writing call is
#         **bit-identical**, component by component in hex, to the snapshot
#         taken at the entry to the output path -- on every component the
#         per-run deferred nodes do not own.  Those nodes run between the two
#         snapshots by design (that is what "once per run, at the accepted
#         optimum" means), their write set is derived from the same two
#         committed artifacts the restricted audit derives it from, never
#         listed, and the components they move are reported by name rather
#         than waved past;
#   (ii)  the output-time loop ran **0** sweeps;
#   (iii) the objective in PROCESS's own output file is the accepted objective,
#         to the bit.
#
# And on the reference arms, which keep the loop: every field that describes
# the solve equals the reproduction gate's record for the same run.  "Nothing
# changes on BR/B0" is a comparison against a record made before this change,
# not an assertion.  The audit residual is deliberately **not** among those
# fields -- the audit moved to the declared position for every arm, which is
# the other half of this task -- and that exclusion is stated here rather than
# left to be noticed.

#: Fields that describe the solve and must be untouched by an output-path
#: change, compared against the reproduction gate's record run for run.
#: ``exit_audit.residual_max_hex`` is deliberately absent: the audit position
#: moved for every arm in this same change, so the residual is expected to
#: differ and comparing it would test the audit, not the output path.
UNCHANGED_ON_REFERENCE_ARMS: tuple[str, ...] = (
    "node_calls_solve_phase",
    "node_calls_total",
    "n_model_calls",
    "n_arrangement_method_calls",
    "exact.norm_objf",
    "n_solver_iterations",
    "mfile.ifail",
    "exit_forensics.n_attempts",
    "exit_forensics.n_solver_iterations_summed_over_attempts",
)


def output_path_root(campaign: Campaign) -> Path:
    return Path(campaign.runs_dir) / GATES_SUBPATH / "output_path"


def output_path_jobs(campaign: Campaign) -> list[pool_mod.Job]:
    """Every Phase B arm at seed 0 on every configuration where it is active.

    The intervention arms carry the criteria; the reference arms carry the
    "nothing changes" half.  A skipped arm is skipped **by the configuration's
    own recorded reason**, never by a condition written here.
    """
    root = output_path_root(campaign)
    jobs: list[pool_mod.Job] = []
    for config in campaign.configurations:
        for arm in arms_mod.active_arms(config, "B"):
            jobs.append(
                pool_mod.Job(
                    phase="B",
                    arm=arm,
                    config=config,
                    seed=0,
                    outdir=root / "runs" / config.name / arm,
                    regime="unperturbed",
                    delta=campaign.delta,
                    run_kind="gate",
                )
            )
    return jobs


def capture_output_path(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    """Run G9's runs and record where they went.  Nothing is compared here."""
    jobs = output_path_jobs(campaign)
    # The two arms whose matrix cell turns the loop off read the lifted input
    # file.  Checked here, before anything starts, so that "the derived input
    # file is not there" is a refusal at the gate's front door rather than a
    # failed run three jobs in.
    lifted = {}
    for config in campaign.configurations:
        if config.pulsed:
            lifted[config.name] = input_files_mod.assert_lifted(config, campaign)
    results = pool_mod.run_all(jobs, campaign, resume=resume)
    manifest = {
        "captured": _dt.datetime.now().isoformat(timespec="seconds"),
        "tree_git_head": _git_head(),
        "n_runs": len(jobs),
        "lifted_input_files": lifted,
        "runs": [
            {
                "configuration": job.config.name,
                "arm": job.arm,
                "outdir": str(job.outdir),
                "status": (results[i] or {}).get("status")
                if isinstance(results, list)
                else None,
            }
            for i, job in enumerate(jobs)
        ],
        "skipped": {
            config.name: dict(arms_mod.skipped_arms(config))
            for config in campaign.configurations
        },
    }
    path = output_path_root(campaign) / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    manifest["manifest"] = str(path)
    return manifest


def _snapshot(directory: Path, where: str, *, key: str) -> dict[str, Any]:
    path = Path(directory) / f"y_{where}.json"
    if not path.exists():
        raise GateError(
            f"G9 has no {where!r} snapshot for {key}: {path} is not there.  A "
            f"gate that cannot find one of the two states it compares must "
            f"refuse, never pass over an empty comparison (trap T11)."
        )
    return json.loads(path.read_text())


def compare_snapshots(
    entry: Mapping[str, Any],
    written: Mapping[str, Any],
    *,
    excluded: set[str],
) -> dict[str, Any]:
    """Two snapshots of the coupling state, component by component, exactly.

    Floats travel as hex literals in a snapshot, so equality here is bit
    equality and no tolerance is applied or available.  ``excluded`` names the
    components the per-run deferred nodes own; they are compared too, and
    reported separately, so that "the difference is confined to the nodes that
    are *supposed* to run there" is a measurement rather than a premise.
    """
    if entry["components_sha256"] != written["components_sha256"]:
        raise GateError(
            "G9's two snapshots were taken against different component specs "
            f"({entry['components_sha256']} vs {written['components_sha256']}); "
            "comparing them would compare components nobody paired"
        )
    a, b = entry["state"], written["state"]
    names = sorted(set(a) | set(b))
    differing_kept, differing_excluded = [], []
    for name in names:
        if a.get(name) == b.get(name):
            continue
        (differing_excluded if name in excluded else differing_kept).append(name)
    return {
        "n_components": len(names),
        "n_excluded_as_per_run_owned": len(excluded & set(names)),
        "n_compared": len(names) - len(excluded & set(names)),
        "n_differing_outside_the_per_run_write_sets": len(differing_kept),
        "differing_outside_the_per_run_write_sets": differing_kept[:20],
        "n_differing_inside_the_per_run_write_sets": len(differing_excluded),
        "differing_inside_the_per_run_write_sets": differing_excluded[:20],
    }


def per_run_owned_components(
    campaign: Campaign, arm: str, config
) -> tuple[set[str], dict[str, Any]]:
    """Components the per-run deferred nodes write, derived from the artifacts.

    The same derivation the restricted audit uses -- the per-run artifact names
    nodes, the committed run-time write census maps each node to what it writes
    on this configuration -- so the two statistics cannot drift apart.  An arm
    that defers nothing owns nothing, and the whole state is compared.
    """
    entry = arms_mod.ARMS[arm]
    if not entry.defer_per_run:
        return set(), {"defers_per_run": False, "artifact": None}
    artifact = config.per_run_artifact(lifted_input_file=entry.input_file == "lifted")
    nodes = list(json.loads(Path(artifact).read_text())["post_solve_nodes"])
    census = json.loads(
        (Path(campaign.data_dir) / "node_writesets.json").read_text()
    )["per_scenario"]
    if config.name not in census:
        raise GateError(
            f"G9 has no write census for {config.name}; the per-run-owned set "
            f"would be guessed, so it is refused"
        )
    writes = census[config.name]["writes_by_node"]
    owned: set[str] = set()
    for node in nodes:
        owned |= set(writes.get(node, ()))
    return owned, {
        "defers_per_run": True,
        "artifact": str(artifact),
        "per_run_nodes": nodes,
        "n_owned_fields": len(owned),
    }


def output_path_body(campaign: Campaign) -> dict[str, Any]:
    """Compare each run against its criteria, and each reference against GR."""
    root = output_path_root(campaign)
    reference_root = Path(campaign.runs_dir) / "gates" / "reproduction" / "runs"
    rows: list[dict[str, Any]] = []
    passed = True
    n_components = n_component_diffs = 0
    n_reference_values = n_reference_diffs = 0
    for config in campaign.configurations:
        for arm in arms_mod.active_arms(config, "B"):
            key = f"{arm}/{config.name}"
            directory = root / "runs" / config.name / arm
            record = _read_record(directory, side="G9", key=key)
            entry = arms_mod.ARMS[arm]
            row: dict[str, Any] = {
                "arm": arm,
                "configuration": config.name,
                "matrix_cell": arms_mod.matrix_cell(entry, "output-time loop (MDA_Output)"),
                "status": record.get("status"),
                "output_path": record.get("output_path"),
                "output_loop_sweeps": record.get("output_loop_sweeps"),
                "output_path_entries": record.get("output_path_entries"),
                "audit_position": record.get("audit_position"),
                "audit_position_declared": record.get("audit_position_declared"),
                "exit_audit_residual_max_hex": (record.get("exit_audit") or {}).get(
                    "residual_max_hex"
                ),
                "exit_audit_n_above_tau": (
                    (record.get("exit_audit") or {}).get("restricted") or {}
                ).get("n_above"),
                "outdir": str(directory),
            }
            checks: list[dict[str, Any]] = []
            checks.append(
                {
                    "check": "the audit was taken where the plan declares",
                    "passed": record.get("audit_position")
                    == record.get("audit_position_declared")
                    == "entry_to_write_output_files",
                    "detail": f"{record.get('audit_position')!r}",
                }
            )
            if entry.output_loop == "none":
                row["expected_output_path"] = "finalise_once"
                owned, derivation = per_run_owned_components(campaign, arm, config)
                row["per_run_derivation"] = derivation
                comparison = compare_snapshots(
                    _snapshot(directory, "entry_to_write_output_files", key=key),
                    _snapshot(directory, "before_finalise", key=key),
                    excluded=owned,
                )
                row["state_written_vs_handed_over"] = comparison
                n_components += comparison["n_compared"]
                n_component_diffs += comparison[
                    "n_differing_outside_the_per_run_write_sets"
                ]
                checks += [
                    {
                        "check": (
                            "(i) the state written out is the state the solve "
                            "handed over, component by component in hex, "
                            "outside the per-run deferred nodes' own writes"
                        ),
                        "passed": comparison[
                            "n_differing_outside_the_per_run_write_sets"
                        ]
                        == 0,
                        "detail": (
                            f"{comparison['n_differing_outside_the_per_run_write_sets']}"
                            f" of {comparison['n_compared']} components differ"
                        ),
                    },
                    {
                        "check": "(ii) the output-time loop ran no sweep",
                        "passed": record.get("output_loop_sweeps") == 0,
                        "detail": f"output_loop_sweeps = {record.get('output_loop_sweeps')}",
                    },
                    {
                        "check": "(iii) the output file's objective is the accepted objective, to the bit",
                        "passed": _same_hex(
                            (record.get("mfile") or {}).get("norm_objf"),
                            (record.get("exact") or {}).get("norm_objf"),
                        ),
                        "detail": _hex_detail(
                            (record.get("mfile") or {}).get("norm_objf"),
                            (record.get("exact") or {}).get("norm_objf"),
                        ),
                    },
                    {
                        "check": "the driver resolved the finalise-once path",
                        "passed": record.get("output_path") == "finalise_once",
                        "detail": f"{record.get('output_path')!r}",
                    },
                ]
            else:
                row["expected_output_path"] = "mda_output"
                reference = reference_root / config.name / arm / pool_mod.seed_directory(0)
                previous = _read_record(
                    reference, side="reproduction gate", key=key
                )
                diffs = []
                for path in UNCHANGED_ON_REFERENCE_ARMS:
                    left = records_mod.resolve_path(previous, path)
                    right = records_mod.resolve_path(record, path)
                    n_reference_values += 1
                    if not _same(left, right):
                        diffs.append({"field": path, "gate_GR": left, "here": right})
                n_reference_diffs += len(diffs)
                row["unchanged_against_the_reproduction_gate"] = {
                    "reference_record": str(reference / "metrics.json"),
                    "n_compared": len(UNCHANGED_ON_REFERENCE_ARMS),
                    "n_differing": len(diffs),
                    "differing": diffs,
                    "fields": list(UNCHANGED_ON_REFERENCE_ARMS),
                    "audit_residual_excluded_because": (
                        "the audit position moved to the declared one for every "
                        "arm in this same change, so the residual is expected "
                        "to differ; the audit is gated by its own criterion "
                        "above and the two residuals are published side by side"
                    ),
                    "audit_residual_here": row["exit_audit_residual_max_hex"],
                    "audit_residual_at_the_previous_position": (
                        previous.get("exit_audit") or {}
                    ).get("residual_max_hex"),
                }
                checks += [
                    {
                        "check": "nothing about the solve changed on the reference arm",
                        "passed": not diffs,
                        "detail": (
                            f"{len(diffs)} of {len(UNCHANGED_ON_REFERENCE_ARMS)} "
                            f"fields differ from the reproduction gate's record"
                        ),
                    },
                    {
                        "check": "the driver resolved upstream's output path",
                        "passed": record.get("output_path") == "mda_output",
                        "detail": f"{record.get('output_path')!r}",
                    },
                    {
                        "check": "the output-time loop actually ran",
                        "passed": (record.get("output_loop_sweeps") or 0) >= 1,
                        "detail": f"output_loop_sweeps = {record.get('output_loop_sweeps')}",
                    },
                ]
            row["checks"] = checks
            row["passed"] = record.get("status") == "ok" and all(
                c["passed"] for c in checks
            )
            passed = passed and row["passed"]
            rows.append(row)
    return {
        "passed": passed,
        "population": (
            f"{len(rows)} run(s) at seed 0 = every optimisation-phase arm on "
            f"every configuration where it is active, each composed from the "
            f"experiment's matrix; {n_components} coupling-state components "
            f"compared in hex on the arms whose matrix cell turns the "
            f"output-time loop off, and {n_reference_values} solve-describing "
            f"values compared against the reproduction gate's records on the "
            f"arms that keep it.  No tolerance is applied to any of them"
        ),
        "n_runs": len(rows),
        "n_components_compared": n_components,
        "n_components_differing": n_component_diffs,
        "n_reference_values_compared": n_reference_values,
        "n_reference_values_differing": n_reference_diffs,
        "unchanged_fields": list(UNCHANGED_ON_REFERENCE_ARMS),
        "runs": rows,
    }


def _same_hex(mfile_value, accepted_hex) -> bool:
    if mfile_value is None or accepted_hex is None:
        return False
    try:
        return float(mfile_value).hex() == accepted_hex
    except (TypeError, ValueError):
        return False


def _hex_detail(mfile_value, accepted_hex) -> str:
    try:
        got = float(mfile_value).hex()
    except (TypeError, ValueError):
        got = repr(mfile_value)
    return f"output file {got}, accepted {accepted_hex}"


def _output_path_teeth(campaign: Campaign) -> tuple[Tooth, ...]:
    """Four breaks, every one on a throwaway copy; no run is ever touched."""

    def an_intervention_run() -> tuple[Path, str, Any]:
        for config in campaign.configurations:
            for arm in arms_mod.active_arms(config, "B"):
                if arms_mod.ARMS[arm].output_loop == "none":
                    directory = output_path_root(campaign) / "runs" / config.name / arm
                    if (directory / "metrics.json").exists():
                        return directory, f"{arm}/{config.name}", config
        raise GateError("G9 has no intervention run to bite on")

    def one_ulp_before_finalise() -> tuple[bool, str]:
        directory, key, config = an_intervention_run()
        entry = _snapshot(directory, "entry_to_write_output_files", key=key)
        written = copy.deepcopy(entry)
        arm = key.split("/")[0]
        owned, _ = per_run_owned_components(campaign, arm, config)
        target = next(
            (
                name
                for name, value in sorted(written["state"].items())
                if value.get("k") == "f" and name not in owned
            ),
            None,
        )
        if target is None:
            return False, "the snapshot carries no float component outside the per-run write sets"
        before = float.fromhex(written["state"][target]["hex"])
        after = math.nextafter(before, math.inf)
        written["state"][target]["hex"] = after.hex()
        result = compare_snapshots(entry, written, excluded=owned)
        return (
            result["n_differing_outside_the_per_run_write_sets"] == 1
            and result["differing_outside_the_per_run_write_sets"] == [target],
            f"{target} moved by one unit in the last place between the snapshot "
            f"and the file-writing call ({before.hex()} -> {after.hex()}) -> "
            f"{result['n_differing_outside_the_per_run_write_sets']} of "
            f"{result['n_compared']} components differ",
        )

    def missing_snapshot() -> tuple[bool, str]:
        import tempfile  # noqa: PLC0415 - tooth path only

        with tempfile.TemporaryDirectory() as td:
            try:
                _snapshot(Path(td), "before_finalise", key="B3/tooth")
            except GateError as exc:
                return True, f"refused: {str(exc).splitlines()[0][:160]}"
        return False, "a missing snapshot did not refuse"

    def a_sweep_that_should_not_be() -> tuple[bool, str]:
        directory, key, _config = an_intervention_run()
        record = copy.deepcopy(_read_record(directory, side="G9", key=key))
        record["output_loop_sweeps"] = 1
        return (
            record["output_loop_sweeps"] != 0,
            f"a throwaway copy of {key}'s record with output_loop_sweeps = 1 "
            f"fails criterion (ii), which reads the field the driver stamped "
            f"(the run itself recorded 0)",
        )

    def a_moved_objective() -> tuple[bool, str]:
        directory, key, _config = an_intervention_run()
        record = _read_record(directory, side="G9", key=key)
        accepted = (record.get("exact") or {}).get("norm_objf")
        written = (record.get("mfile") or {}).get("norm_objf")
        if accepted is None or written is None:
            return False, f"{key} carries no objective to move"
        nudged = math.nextafter(float(written), math.inf)
        return (
            _same_hex(written, accepted) and not _same_hex(nudged, accepted),
            f"the output file's objective moved by one unit in the last place "
            f"({float(written).hex()} -> {nudged.hex()}) no longer equals the "
            f"accepted {accepted}",
        )

    return (
        Tooth(
            "one_component_moved_by_one_ulp_before_finalise",
            "one float of a throwaway copy of the entry snapshot moved by one "
            "unit in the last place, standing in for the state being touched "
            "between the snapshot and the file-writing call",
            "FAIL, naming the component",
            one_ulp_before_finalise,
        ),
        Tooth(
            "missing_snapshot",
            "one of the two snapshots asked for at a directory that has none",
            "REFUSE, not skip",
            missing_snapshot,
        ),
        Tooth(
            "an_output_time_sweep_under_the_finalise_once_path",
            "a throwaway copy of an intervention run's record with "
            "output_loop_sweeps = 1",
            "FAIL",
            a_sweep_that_should_not_be,
        ),
        Tooth(
            "the_written_objective_moved",
            "the output file's objective moved by one unit in the last place",
            "FAIL",
            a_moved_objective,
        ),
    )


# --------------------------------------------------------------------------
# the output path, measured -- not a gate
# --------------------------------------------------------------------------
#
# Two quantities the experiment plan asks for by name, published as
# measurements with their populations and never as acceptance criteria.
#
# **What the output-time loop costs.**  Section 3.3 of the plan commits the
# sweep count of that loop, per run, by arm and configuration.  It is read from
# the driver's own counter on the reproduction gate's runs -- the only set of
# runs in which every arm, including the two whose matrix cell turns the loop
# off, executes it (that gate runs them with it on, because the records it
# reproduces were made that way).
#
# **What the accepted state's residual is, at the declared position.**  The
# same section says the one signal the output-time loop found by accident in
# the previous revision -- a handed-over state that was not output-idempotent
# -- is to be "looked for on purpose": the exit audit at the accepted point,
# per run, with the count of components above the tolerance.  That count is
# read from the gate's own runs at the declared position.
#
# It is published **twice**, and the reason is not caution.  The audit sweep
# runs every node, including the ones an arm defers to once per run; measured
# from the handed-over state -- which is *before* those nodes have run -- their
# own outputs necessarily move, and a whole-state count on such an arm would
# report that as non-convergence.  The restricted count excludes exactly the
# components those nodes write, derived here from the same two committed
# artifacts the audit's own restricted statistic derives from: the per-run
# deferral artifact names the nodes, the run-time write census says what each
# writes on this configuration.  One excluded set per configuration, from the
# committed input file's artifact, so that the count is on the same ruler in
# every arm of that configuration.
#
# (The restricted count is computed here, from the run's own committed residual
# vector, rather than carried in the record: wiring it into the optimisation
# record belongs with gate G4, which is task A52 (harness-gates)'s.  Both
# constructions are stated in the table's caption.)


def _residual_vector(directory: Path, *, key: str) -> dict[str, Any]:
    path = Path(directory) / "audit_residual.json"
    if not path.exists():
        raise GateError(
            f"no residual vector for {key}: {path} is not there.  A count of "
            f"components above the tolerance with no vector behind it is a "
            f"number over an unstated population (trap T11)."
        )
    return json.loads(path.read_text())


def excluded_by_the_per_run_nodes(campaign: Campaign, config) -> tuple[set[str], dict]:
    """Components the per-run deferrable nodes write on this configuration.

    One set per configuration, from the **committed** input file's artifact, so
    that every arm of that configuration is restricted by the same set — which
    is the whole point of a restricted statistic.  The derivation is the audit's
    own: the artifact names nodes, the census maps each node to what it writes.
    """
    artifact = config.per_run_artifact(lifted_input_file=False)
    nodes = list(json.loads(Path(artifact).read_text())["post_solve_nodes"])
    census = json.loads(
        (Path(campaign.data_dir) / "node_writesets.json").read_text()
    )["per_scenario"]
    if config.name not in census:
        raise GateError(
            f"no write census for {config.name}; the excluded set would be "
            f"guessed, so it is refused"
        )
    writes = census[config.name]["writes_by_node"]
    owned: set[str] = set()
    for node in nodes:
        owned |= set(writes.get(node, ()))
    return owned, {
        "artifact": str(artifact),
        "per_run_nodes": nodes,
        "census": str(Path(campaign.data_dir) / "node_writesets.json"),
        "n_fields_named": len(owned),
    }


#: The two runs the contrast makes on each configuration: the reference arm,
#: identical in everything, written out through each of the two output paths.
CONTRAST_LABELS: dict[str, str | None] = {"with_loop": None, "without_loop": "none"}


def contrast_root(campaign: Campaign) -> Path:
    return output_path_root(campaign) / "contrast"


def contrast_jobs(campaign: Campaign) -> list[pool_mod.Job]:
    """The reference arm, run twice per configuration, once down each path.

    Deliberately **not** a matrix composition: no arm of the experiment writes
    upstream's own solve out through the one-call path.  That is the point —
    holding the solve fixed and varying only the output path is the only way to
    say what the output-time loop does to the numbers a reader of the output
    file gets, and the arm whose numbers a reader actually gets is the reference
    one.  It runs as a gate, never as a campaign record, and the environment
    override is stamped in each record.
    """
    jobs: list[pool_mod.Job] = []
    for config in campaign.configurations:
        for label, value in CONTRAST_LABELS.items():
            jobs.append(
                pool_mod.Job(
                    phase="B",
                    arm="BR",
                    config=config,
                    seed=0,
                    outdir=contrast_root(campaign) / config.name / label,
                    regime="unperturbed",
                    delta=campaign.delta,
                    run_kind="gate",
                    override_env=(
                        {}
                        if value is None
                        else {switches_mod.REGISTRY["output_loop"].driver_name: value}
                    ),
                )
            )
    return jobs


def capture_contrast(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    """Run the contrast's two runs per configuration.  Nothing is compared here."""
    jobs = contrast_jobs(campaign)
    results = pool_mod.run_all(jobs, campaign, resume=resume)
    manifest = {
        "captured": _dt.datetime.now().isoformat(timespec="seconds"),
        "tree_git_head": _git_head(),
        "n_runs": len(jobs),
        "runs": [
            {
                "configuration": job.config.name,
                "label": sorted(CONTRAST_LABELS)[i % len(CONTRAST_LABELS)],
                "override_env": dict(job.override_env),
                "outdir": str(job.outdir),
                "status": (results[i] or {}).get("status")
                if isinstance(results, list)
                else None,
            }
            for i, job in enumerate(jobs)
        ],
    }
    path = contrast_root(campaign) / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    manifest["manifest"] = str(path)
    return manifest


def contrast_rows(campaign: Campaign) -> list[dict[str, Any]]:
    """What the output-time loop moves, per configuration, in the output file.

    The solve is held fixed and is checked to be fixed: the accepted objective
    and the solve-phase node count must be identical on the two sides, and a
    row where they are not says so rather than attributing a solve difference
    to the output path.  What is then counted is output-file lines differing,
    with the same metadata keys excluded that gate G1 excludes -- date, time,
    user, paths, version strings and PROCESS's own timing of itself.
    """
    rows: list[dict[str, Any]] = []
    for config in campaign.configurations:
        key = f"BR/{config.name}"
        directory = {
            label: contrast_root(campaign) / config.name / label
            for label in CONTRAST_LABELS
        }
        record = {
            label: _read_record(d, side=f"contrast:{label}", key=key)
            for label, d in directory.items()
        }
        mfile = {}
        for label, d in directory.items():
            found = _mfile_for(d, config.name)
            if found is None:
                raise GateError(
                    f"the contrast has no output file for {key} on the "
                    f"{label!r} side ({d}); the line comparison would be over "
                    f"nothing"
                )
            mfile[label] = found
        lines = compare_mfiles(mfile["with_loop"], mfile["without_loop"])
        solve_identical = (
            record["with_loop"].get("node_calls_solve_phase")
            == record["without_loop"].get("node_calls_solve_phase")
            and (record["with_loop"].get("exact") or {}).get("norm_objf")
            == (record["without_loop"].get("exact") or {}).get("norm_objf")
        )
        rows.append(
            {
                "configuration": config.name,
                "arm": "BR",
                "solve_identical": solve_identical,
                "node_calls_solve_phase": record["with_loop"].get(
                    "node_calls_solve_phase"
                ),
                "node_calls_total_with_loop": record["with_loop"].get(
                    "node_calls_total"
                ),
                "node_calls_total_without_loop": record["without_loop"].get(
                    "node_calls_total"
                ),
                "accepted_objf_hex": (record["with_loop"].get("exact") or {}).get(
                    "norm_objf"
                ),
                "output_loop_sweeps_with_loop": record["with_loop"].get(
                    "output_loop_sweeps"
                ),
                "output_loop_sweeps_without_loop": record["without_loop"].get(
                    "output_loop_sweeps"
                ),
                "mfile_ifail_with_loop": (record["with_loop"].get("mfile") or {}).get(
                    "ifail"
                ),
                "mfile_ifail_without_loop": (
                    record["without_loop"].get("mfile") or {}
                ).get("ifail"),
                "n_lines_compared": lines["n_lines_compared"],
                "n_lines_excluded": lines["n_lines_excluded"],
                "n_lines_differing": lines["n_lines_differing"],
                "differing_first": [
                    row["before"].split()[0][:70] for row in lines["differing"][:12]
                ],
            }
        )
    return rows


def output_path_measurements(campaign: Campaign) -> dict[str, Any]:
    """The two measurements, over the run sets each is defined on."""
    reproduction_root = Path(campaign.runs_dir) / "gates" / "reproduction" / "runs"
    sweeps: list[dict[str, Any]] = []
    for run in reference_mod.reference_set(campaign):
        if run.phase != "B":
            continue
        key = f"{run.arm}/{run.configuration}/seed{run.seed:03d}"
        directory = (
            reproduction_root
            / run.configuration
            / run.arm
            / pool_mod.seed_directory(run.seed)
        )
        record = _read_record(directory, side="the reproduction gate", key=key)
        total = record.get("node_calls_total")
        solve = record.get("node_calls_solve_phase")
        sweeps.append(
            {
                "arm": run.arm,
                "configuration": run.configuration,
                "seed": run.seed,
                "output_path": record.get("output_path"),
                "output_loop_sweeps": record.get("output_loop_sweeps"),
                "output_path_entries": record.get("output_path_entries"),
                "reproduction_overrides": record.get("reproduction_overrides"),
                "node_calls_solve_phase": solve,
                "node_calls_total": total,
                "node_calls_after_the_solve": (
                    None if total is None or solve is None else total - solve
                ),
            }
        )

    above: list[dict[str, Any]] = []
    excluded_by_config: dict[str, dict] = {}
    for config in campaign.configurations:
        owned, derivation = excluded_by_the_per_run_nodes(campaign, config)
        excluded_by_config[config.name] = derivation
        for arm in arms_mod.active_arms(config, "B"):
            if arms_mod.ARMS[arm].output_loop != "none":
                continue
            key = f"{arm}/{config.name}"
            directory = output_path_root(campaign) / "runs" / config.name / arm
            record = _read_record(directory, side="G9", key=key)
            vector = _residual_vector(directory, key=key)
            tau = float(vector["tau"])
            scaled = vector["scaled"]
            kept = {k: v for k, v in scaled.items() if k not in owned}
            above.append(
                {
                    "arm": arm,
                    "configuration": config.name,
                    "audit_position": record.get("audit_position"),
                    "tau": tau,
                    "residual_max_hex": (record.get("exit_audit") or {}).get(
                        "residual_max_hex"
                    ),
                    "n_tested_whole_state": len(scaled),
                    "n_above_tau_whole_state": sum(
                        1 for v in scaled.values() if v >= tau
                    ),
                    "n_tested_restricted": len(kept),
                    "n_above_tau_restricted": sum(
                        1 for v in kept.values() if v >= tau
                    ),
                    "n_excluded_as_per_run_owned": len(scaled) - len(kept),
                    "residual_max_restricted": max(kept.values()) if kept else 0.0,
                    "residual_max_restricted_hex": float(
                        max(kept.values()) if kept else 0.0
                    ).hex(),
                    "residual_argmax_restricted": (
                        max(kept, key=kept.get) if kept else None
                    ),
                    "above_tau_restricted": sorted(
                        k for k, v in kept.items() if v >= tau
                    )[:20],
                }
            )
    contrast = contrast_rows(campaign)
    return {
        "what_the_output_time_loop_moves": {
            "population": (
                f"{len(contrast) * 2} run(s) = the reference arm at seed 0 on "
                f"each of {len(contrast)} configuration(s), written out once "
                f"through each output path with everything else identical.  "
                f"Not a matrix composition: no arm of the experiment writes "
                f"upstream's own solve through the one-call path, and holding "
                f"the solve fixed while varying only the output path is what "
                f"isolates the loop's effect on the numbers a reader gets"
            ),
            "rows": contrast,
        },
        "output_time_loop_sweeps": {
            "population": (
                f"{len(sweeps)} optimisation run(s) of the reproduction gate = "
                f"its whole optimisation-phase reference set.  Every one runs "
                f"upstream's output-time loop: the two arms whose matrix cell "
                f"turns it off carry the gate's recorded override, because the "
                f"records they reproduce were made before the switch existed"
            ),
            "rows": sweeps,
        },
        "above_tau_at_the_declared_position": {
            "population": (
                f"{len(above)} run(s) at seed 0 = the arms whose matrix cell "
                f"turns the output-time loop off, on every configuration where "
                f"they are active, from gate G9's own runs; the audit is taken "
                f"at the entry to the output path in every one"
            ),
            "excluded_set_per_configuration": excluded_by_config,
            "rows": above,
        },
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "tree_git_head": _git_head(),
    }


def print_measurements(block: Mapping[str, Any]) -> None:
    """The three tables, with their captions, as the report prints them."""
    contrast = block["what_the_output_time_loop_moves"]
    print()
    print(
        "*Caption: one row per configuration.  The reference arm is run at "
        "seed 0 and written out twice — once through upstream's output-time "
        "loop and once through the one-call path — with everything else "
        "identical.  The solve is held fixed and checked to be fixed: "
        '"solve identical" is the accepted objective hex and the solve-phase '
        "node count agreeing on the two sides, and a row where they do not "
        "agree is not a statement about the output path.  Lines differing are "
        "lines of PROCESS's own output file, with the same metadata keys "
        "excluded that the switch-neutrality gate excludes (date, time, user, "
        "paths, version strings and PROCESS's own timing of itself).  Counts, "
        "not timings.  Population: " + contrast["population"] + ".*"
    )
    print()
    print(
        "| configuration | solve identical | accepted objective (hex) | "
        "solve-phase node calls | total node calls, loop on / off | sweeps, "
        "on / off | output-file lines differing / compared |"
    )
    print("|---|---|---|---:|---:|---:|---:|")
    for row in contrast["rows"]:
        print(
            f"| `{row['configuration']}` | "
            f"{'yes' if row['solve_identical'] else '**NO**'} | "
            f"`{row['accepted_objf_hex']}` | {row['node_calls_solve_phase']} | "
            f"{row['node_calls_total_with_loop']} / "
            f"{row['node_calls_total_without_loop']} | "
            f"{row['output_loop_sweeps_with_loop']} / "
            f"{row['output_loop_sweeps_without_loop']} | "
            f"**{row['n_lines_differing']}** / {row['n_lines_compared']} |"
        )
    print()
    for row in contrast["rows"]:
        if row["differing_first"]:
            print(f"  {row['configuration']}: {', '.join(row['differing_first'])}")
    sweeps = block["output_time_loop_sweeps"]
    print()
    print(
        "*Caption: one row per optimisation run of the reproduction gate.  "
        '"Sweeps" is how many times upstream\'s output-time loop evaluated the '
        "whole model set before writing the output files, read from the "
        'driver\'s own counter; "entries" is how many times the output path '
        'was entered (one per scan point).  "After the solve" is model node '
        "calls made after the solve-phase counter was frozen: the per-run "
        "deferred nodes where an arm has them, plus the output-time loop's own "
        "sweeps.  Counts, not timings.  Population: "
        + sweeps["population"]
        + ".*"
    )
    print()
    print("| arm | configuration | seed | path | sweeps | entries | solve-phase node calls | node calls after the solve |")
    print("|---|---|---:|---|---:|---:|---:|---:|")
    for row in sweeps["rows"]:
        print(
            f"| `{row['arm']}` | `{row['configuration']}` | {row['seed']} | "
            f"`{row['output_path']}` | {row['output_loop_sweeps']} | "
            f"{row['output_path_entries']} | {row['node_calls_solve_phase']} | "
            f"{row['node_calls_after_the_solve']} |"
        )
    above = block["above_tau_at_the_declared_position"]
    print()
    print(
        "*Caption: one row per run of gate G9 on an arm whose matrix cell "
        "turns the output-time loop off.  The exit audit is one further sweep "
        "of the whole model set from the state the solve handed over, and the "
        "columns count how many coupling-state components moved by at least "
        "the tolerance under it.  **Whole state** counts every tested "
        "component; **restricted** excludes the components the per-run "
        "deferrable nodes write, derived from the committed per-run artifact "
        "and the committed run-time write census, one set per configuration so "
        "every arm is on the same ruler.  The two differ because the audit "
        "sweep runs those nodes and the handed-over state is from before they "
        "ran, so their own outputs move by construction — which is why the "
        "whole-state maximum is not published here at all: on an arm that "
        "defers, it is a per-run node's own output and says nothing about "
        "convergence.  Population: "
        + above["population"]
        + ".*"
    )
    print()
    print(
        "| arm | configuration | tau | tested | above tau, whole state | "
        "tested, restricted | above tau, restricted | restricted max | "
        "restricted argmax |"
    )
    print("|---|---|---:|---:|---:|---:|---:|---:|---|")
    for row in above["rows"]:
        print(
            f"| `{row['arm']}` | `{row['configuration']}` | {row['tau']:g} | "
            f"{row['n_tested_whole_state']} | "
            f"{row['n_above_tau_whole_state']} | {row['n_tested_restricted']} | "
            f"{row['n_above_tau_restricted']} | "
            f"{row['residual_max_restricted']:.3g} | "
            f"`{row['residual_argmax_restricted']}` |"
        )
    print()
    for name, derivation in above["excluded_set_per_configuration"].items():
        print(
            f"  {name}: per-run nodes {derivation['per_run_nodes']} write "
            f"{derivation['n_fields_named']} field(s); artifact "
            f"{Path(derivation['artifact']).name}"
        )


# --------------------------------------------------------------------------
# The per-sweep overhead, counted -- a measurement, not a gate
# --------------------------------------------------------------------------
#
# EXPERIMENT_PLAN.md section 3.5, check 5, and improvement-list item 3.  The
# partitioned arrangement runs far more sweeps of the model sequence than the
# flat one while executing far fewer model nodes, and the previous revision
# measured it no faster.  Something a sweep costs is therefore not proportional
# to the nodes it runs, and the convergence test is the obvious suspect: a flat
# loop compares the whole coupling state on every sweep while a block loop
# compares only its own block's write set.
#
# Nothing here is evidence about speed.  These are counts, which reproduce bit
# for bit; no conclusion in this experiment rests on a clock (issue I-10).  What
# the counts settle is whether a non-node-proportional term of the hypothesised
# *size* exists at all.
#
# The population is the reproduction gate's own runs, because they already
# exist at this commit, they cover every arm the gate covers on all three
# configurations, and they are made by the committed run path.  They are one
# seed each -- seed 0 for most rows -- so no row here is a campaign statistic
# and none is quoted as one.

#: The order rows are printed in, so a reader can compare configurations down a
#: column.  Arms follow the experiment plan's matrix order.
MEASUREMENT_ARM_ORDER = arms_mod.MATRIX_ORDER


def predicate_counter_rows(campaign: Campaign, root: Path | None = None) -> list[dict[str, Any]]:
    """One row per run of the reproduction gate, with its counters.

    Reads records; runs nothing.  A run directory with no record is a row that
    says so, never a row silently dropped: a table over a population quietly
    smaller than the one named is this project's trap T11.
    """
    from harness import reproduction as reproduction_mod  # noqa: PLC0415

    base = Path(root or (Path(campaign.runs_dir) / reproduction_mod.RUNS_SUBPATH))
    rows: list[dict[str, Any]] = []
    for run in reference_mod.reference_set(campaign):
        directory = (
            base / "runs" / run.configuration / run.arm
            / pool_mod.seed_directory(run.seed)
        )
        record = records_mod.read(directory)
        rows.append(_counter_row(run.arm, run.configuration, run.seed, run.phase, record))
    rows.sort(
        key=lambda r: (
            r["configuration"],
            MEASUREMENT_ARM_ORDER.index(r["arm"])
            if r["arm"] in MEASUREMENT_ARM_ORDER
            else len(MEASUREMENT_ARM_ORDER),
            r["seed"],
        )
    )
    return rows


def _counter_row(
    arm: str, configuration: str, seed: int, phase: str, record: Mapping[str, Any]
) -> dict[str, Any]:
    """One run's counters, with the reconciliation of its sweep total."""
    block_visits = record.get("block_visits") or {}
    empty_visits = record.get("empty_block_visits") or {}
    empty_sweeps = record.get("empty_block_sweeps") or {}
    totals = record.get("block_loop_totals") or {}
    evaluations = record.get("predicate_evaluations")
    components = record.get("components_compared")
    upstream_evaluations = record.get("upstream_predicate_evaluations")
    upstream_components = record.get("upstream_components_compared")
    counters = record.get("predicate_counters") or {}
    coupling = counters.get("coupling_state_predicate") or {}
    row: dict[str, Any] = {
        "configuration": configuration,
        "arm": arm,
        "seed": seed,
        "phase": phase,
        "status": record.get("status"),
        "stops_on": (
            "coupling state"
            if evaluations
            else ("upstream's objective/constraint test" if upstream_evaluations else "—")
        ),
        "dispatch_sweeps": record.get("dispatch_sweeps"),
        "block_sweeps": totals.get("block_sweeps"),
        "output_loop_sweeps": record.get("output_loop_sweeps"),
        "predicate_evaluations": evaluations,
        "components_compared": components,
        "mean_test_width": coupling.get("mean_test_width"),
        "mean_test_width_by_block": coupling.get("mean_test_width_by_block") or {},
        "evaluations_by_block": coupling.get("evaluations_by_block") or {},
        "upstream_predicate_evaluations": upstream_evaluations,
        "upstream_components_compared": upstream_components,
        "upstream_mean_test_width": (
            (counters.get("upstream_predicate") or {}).get("mean_test_width")
        ),
        "block_visits": dict(sorted(block_visits.items())) if block_visits else {},
        "n_block_visits": sum(block_visits.values()) if block_visits else 0,
        "empty_block_visits": dict(sorted(empty_visits.items())) if empty_visits else {},
        "n_empty_block_visits": sum(empty_visits.values()) if empty_visits else 0,
        "empty_block_sweeps": dict(sorted(empty_sweeps.items())) if empty_sweeps else {},
        "n_empty_block_sweeps": sum(empty_sweeps.values()) if empty_sweeps else 0,
        "node_calls_solve_phase": record.get("node_calls_solve_phase"),
        "node_calls_single_eval": record.get("node_calls_single_eval"),
        "n_call_models": totals.get("n_call_models"),
    }
    row["empty_share_of_block_visits"] = (
        (row["n_empty_block_visits"] / row["n_block_visits"])
        if row["n_block_visits"]
        else None
    )
    row["reconciliation"] = _reconcile_sweeps(record, row)
    return row


def _reconcile_sweeps(record: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, Any]:
    """Does the run's sweep total decompose into the parts that claim it?

    The identity, for an arm that runs a block schedule::

        dispatch_sweeps = block_sweeps + output_loop_sweeps + per_run_sweep

    ``per_run_sweep`` is one sweep, spent in ``write_output_files`` running the
    nodes deferred to once per run; it is 1 when that set is non-empty and 0
    otherwise.  For an arm with no block schedule the first term is instead the
    sweeps the analysis loop took, which the per-evaluation histogram sums.

    A residual that is not 0 is reported, never absorbed: a sweep total nobody
    can decompose is a total nobody can attribute.
    """
    total = row["dispatch_sweeps"]
    if total is None:
        return {"checked": False, "why": "the record carries no sweep total"}
    per_run = record.get("defer_per_run_totals") or {}
    per_run_sweep = 1 if (per_run.get("executed_once") or []) else 0
    output = row["output_loop_sweeps"] or 0
    if row["block_sweeps"]:
        loop = row["block_sweeps"]
        loop_is = "block_sweeps (the block schedule's own charged sweeps)"
    else:
        loop = ((record.get("sweeps_per_eval") or {}).get("n_sweeps")) or 0
        loop_is = "sweeps_per_eval.n_sweeps (the analysis loop's own sweeps)"
    residual = total - (loop + output + per_run_sweep)
    return {
        "checked": True,
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


def predicate_counter_measurements(
    campaign: Campaign, root: Path | None = None
) -> dict[str, Any]:
    """The per-sweep-overhead block the report publishes, with its population."""
    rows = predicate_counter_rows(campaign, root=root)
    finished = [r for r in rows if r["status"] == "ok"]
    undecomposed = [
        f"{r['arm']}/{r['configuration']}"
        for r in finished
        if r["reconciliation"].get("checked") and not r["reconciliation"]["decomposes"]
    ]
    empty_rows = [r for r in finished if r["n_empty_block_visits"]]
    return {
        "what": (
            "what each arm's convergence test cost, in counts.  Two predicates "
            "are reported and never pooled: an arm stops on exactly one of "
            "them.  'mean test width' is components compared divided by "
            "evaluations — the average number of components one test walked"
        ),
        "population": (
            f"{len(rows)} run(s) of the reproduction gate at this commit, "
            f"{len(finished)} of them finished; one seed per row (seed 0 "
            f"except where the row says otherwise), so no figure here is a "
            f"campaign statistic and none is quoted as one"
        ),
        "empty_visits_disclaimer": (
            "empty block visits are INCLUDED in every visit and sweep count "
            "here.  On st_regression the PULSE block is visited once per "
            "evaluation of the model set with its member skipped at the call "
            "site: a full sweep of the model sequence that executes no model.  "
            "The user ruled that this stays and is disclaimed rather than "
            "repaired (issue I-20a), because dropping the block would change "
            "the node weights the comparison rests on.  A block the per-call "
            "deferral has emptied of members is also an empty visit but costs "
            "no sweep at all, which is why the two are counted separately"
        ),
        "timing_note": (
            "no timing appears here and none is implied: these are counts, "
            "which reproduce bit for bit"
        ),
        "n_rows": len(rows),
        "n_finished": len(finished),
        "rows": rows,
        "sweep_decomposition": {
            "identity": (
                "dispatch_sweeps = loop sweeps + output-time loop sweeps + the "
                "one sweep the per-run deferral spends at the output path"
            ),
            "n_checked": len([r for r in finished if r["reconciliation"].get("checked")]),
            "n_that_do_not_decompose": len(undecomposed),
            "which": undecomposed,
        },
        "flat_against_partitioned": {
            "what": (
                "the flat control against the partitioned arm at the same "
                "configuration and the same seed: how much more often the "
                "convergence test is evaluated, how much narrower each "
                "evaluation is, and what the two multiply to.  A ratio below "
                "1 in the components column means the partitioned arm does "
                "LESS component comparison than the flat one, which is what "
                "decides the per-sweep-overhead hypothesis on counts"
            ),
            "population": (
                "one run against one run per cell, never a campaign mean, and "
                "only where both arms have a run at the same seed"
            ),
            "rows": predicate_pair_rows(rows),
        },
        "empty_visits": {
            "n_runs_with_any": len(empty_rows),
            "by_run": [
                {
                    "configuration": r["configuration"],
                    "arm": r["arm"],
                    "seed": r["seed"],
                    "visits": r["n_block_visits"],
                    "empty_visits": r["n_empty_block_visits"],
                    "empty_visits_that_cost_a_sweep": r["n_empty_block_sweeps"],
                    "share_of_visits": r["empty_share_of_block_visits"],
                    # The share that is actually a cost.  A visit to a block
                    # with no members costs nothing, so the visit share is not
                    # a cost share and must never be quoted as one; this is,
                    # and it is the figure the earlier finding was filed as.
                    "block_sweeps": r["block_sweeps"],
                    "share_of_block_sweeps": (
                        (r["n_empty_block_sweeps"] / r["block_sweeps"])
                        if r["block_sweeps"]
                        else None
                    ),
                    "by_block": r["empty_block_visits"],
                    "sweeps_by_block": r["empty_block_sweeps"],
                }
                for r in empty_rows
            ],
        },
    }


#: The pairs check 5 is about: the flat control against the partitioned arm, at
#: the same configuration and the same seed.  ``B1`` is the flat arm carrying
#: the lift, so it is the one whose design vector matches ``B3``'s; ``B0`` is
#: the flat control the cost ratio is quoted against.  A pair is formed only
#: where both runs exist at the same seed — never across seeds, because the two
#: would then be different problems.
PREDICATE_PAIRS: tuple[tuple[str, str], ...] = (("B0", "B3"), ("B1", "B3"))


def predicate_pair_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Flat against partitioned, at matched configuration and seed.

    The hypothesis check 5 exists to settle is that the partitioned arm pays a
    per-sweep cost the flat one does not, with the convergence test the prime
    suspect: the flat loop compares the whole coupling state on every sweep and
    a block loop compares only its own block's write set.  The suspect predicts
    that the partitioned arm does **more** component comparison in total, since
    it runs far more sweeps.  These ratios are what decides that, and they
    decide it on counts alone.

    Each cell is a ratio of two single runs, not of two campaign means; the
    caption says so and nothing here is a campaign statistic.
    """
    by_key = {(r["configuration"], r["arm"], r["seed"]): r for r in rows}
    out: list[dict[str, Any]] = []
    for (configuration, arm, seed), row in sorted(by_key.items()):
        for flat, partitioned in PREDICATE_PAIRS:
            if arm != partitioned:
                continue
            control = by_key.get((configuration, flat, seed))
            if control is None or control["status"] != "ok" or row["status"] != "ok":
                continue
            out.append(
                {
                    "configuration": configuration,
                    "seed": seed,
                    "flat_arm": flat,
                    "partitioned_arm": partitioned,
                    "flat_evaluations": control["predicate_evaluations"],
                    "partitioned_evaluations": row["predicate_evaluations"],
                    "evaluations_ratio": _ratio(
                        row["predicate_evaluations"], control["predicate_evaluations"]
                    ),
                    "flat_width": control["mean_test_width"],
                    "partitioned_width": row["mean_test_width"],
                    "width_ratio": _ratio(
                        row["mean_test_width"], control["mean_test_width"]
                    ),
                    "flat_components": control["components_compared"],
                    "partitioned_components": row["components_compared"],
                    "components_ratio": _ratio(
                        row["components_compared"], control["components_compared"]
                    ),
                    "flat_sweeps": control["dispatch_sweeps"],
                    "partitioned_sweeps": row["dispatch_sweeps"],
                    "sweeps_ratio": _ratio(
                        row["dispatch_sweeps"], control["dispatch_sweeps"]
                    ),
                    "flat_node_calls": control["node_calls_solve_phase"],
                    "partitioned_node_calls": row["node_calls_solve_phase"],
                    "node_calls_ratio": _ratio(
                        row["node_calls_solve_phase"],
                        control["node_calls_solve_phase"],
                    ),
                }
            )
    return out


def _ratio(a, b):
    if a is None or not b:
        return None
    return a / b


def _n(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:,.1f}"
    return f"{value:,}"


def print_predicate_counters(block: Mapping[str, Any]) -> None:
    """The measurement, as the report prints it."""
    print("\n=== the per-sweep overhead, counted (experiment plan §3.5 check 5)")
    print(f"    {block['what']}")
    print(f"    population : {block['population']}")
    print(f"    empty visits: {block['empty_visits_disclaimer']}")
    print()
    head = (
        f"    {'configuration':<22} {'arm':<4} {'seed':>4} {'stops on':<34} "
        f"{'sweeps':>8} {'pred.ev':>8} {'comps':>12} {'width':>8} "
        f"{'visits':>7} {'empty':>7} {'e.sweeps':>9}"
    )
    print(head)
    print("    " + "-" * (len(head) - 4))
    for row in block["rows"]:
        if row["status"] != "ok":
            print(
                f"    {row['configuration']:<22} {row['arm']:<4} "
                f"{row['seed']:>4} NO RECORD ({row['status']})"
            )
            continue
        evaluations = row["predicate_evaluations"] or row["upstream_predicate_evaluations"]
        components = row["components_compared"] or row["upstream_components_compared"]
        width = row["mean_test_width"] or row["upstream_mean_test_width"]
        print(
            f"    {row['configuration']:<22} {row['arm']:<4} {row['seed']:>4} "
            f"{row['stops_on']:<34} "
            f"{_n(row['dispatch_sweeps']):>8} {_n(evaluations):>8} "
            f"{_n(components):>12} {_n(width):>8} "
            f"{_n(row['n_block_visits']):>7} {_n(row['n_empty_block_visits']):>7} "
            f"{_n(row['n_empty_block_sweeps']):>9}"
        )
    print()
    print("    per-block mean test width, one row per run:")
    for row in block["rows"]:
        if not row["mean_test_width_by_block"]:
            continue
        widths = ", ".join(
            f"{label} {width:.0f} ({row['evaluations_by_block'].get(label, 0):,} tests)"
            for label, width in row["mean_test_width_by_block"].items()
        )
        print(
            f"      {row['configuration']:<22} {row['arm']:<4} "
            f"{row['seed']:>4} {widths}"
        )
    print()
    pairs = block["flat_against_partitioned"]
    print("    flat against partitioned, matched configuration and seed:")
    print(f"      {pairs['what']}")
    print(f"      population : {pairs['population']}")
    pair_head = (
        f"      {'configuration':<22} {'pair':<9} {'seed':>4} "
        f"{'evals x':>9} {'width x':>9} {'comps x':>9} {'sweeps x':>9} "
        f"{'nodes x':>9}"
    )
    print(pair_head)
    print("      " + "-" * (len(pair_head) - 6))
    for pair in pairs["rows"]:
        def _r(value):
            return f"{value:.3f}" if value is not None else "—"
        print(
            f"      {pair['configuration']:<22} "
            f"{pair['flat_arm'] + '→' + pair['partitioned_arm']:<9} "
            f"{pair['seed']:>4} {_r(pair['evaluations_ratio']):>9} "
            f"{_r(pair['width_ratio']):>9} {_r(pair['components_ratio']):>9} "
            f"{_r(pair['sweeps_ratio']):>9} {_r(pair['node_calls_ratio']):>9}"
        )
    print()
    print("    empty block visits, and the share of them that is a cost:")
    print(
        "      a visit to a block with no members costs no sweep, so the visit "
        "share is not a cost share; the sweep share is"
    )
    empty_head = (
        f"      {'configuration':<22} {'arm':<4} {'seed':>4} {'visits':>7} "
        f"{'empty':>7} {'% visits':>9} {'e.sweeps':>9} {'% sweeps':>9}  blocks"
    )
    print(empty_head)
    print("      " + "-" * (len(empty_head) - 6))
    for entry in block["empty_visits"]["by_run"]:
        share_v = entry["share_of_visits"]
        share_s = entry["share_of_block_sweeps"]
        print(
            f"      {entry['configuration']:<22} {entry['arm']:<4} "
            f"{entry['seed']:>4} {_n(entry['visits']):>7} "
            f"{_n(entry['empty_visits']):>7} "
            f"{(f'{share_v * 100:.2f}' if share_v is not None else '—'):>9} "
            f"{_n(entry['empty_visits_that_cost_a_sweep']):>9} "
            f"{(f'{share_s * 100:.2f}' if share_s is not None else '—'):>9}  "
            f"empty {sorted(entry['by_block'])}, costing a sweep "
            f"{sorted(k for k, v in entry['sweeps_by_block'].items() if v)}"
        )
    print()
    decomposition = block["sweep_decomposition"]
    print(f"    sweep decomposition: {decomposition['identity']}")
    print(
        f"      {decomposition['n_checked']} run(s) checked, "
        f"{decomposition['n_that_do_not_decompose']} that do not decompose"
        + (f": {decomposition['which']}" if decomposition["which"] else "")
    )
    print(f"    {block['timing_note']}")




# --------------------------------------------------------------------------
# The retry ladder, per attempt -- a measurement, not a gate
# --------------------------------------------------------------------------
#
# EXPERIMENT_PLAN.md section 3.5 ("retries are a term, not a footnote") and
# driver change DR7.  The optimiser is tried up to four times in one run and
# every attempt evaluates the model set, so a run total charges a retry's
# evaluations to the arm while publishing the iterations and the exit code of
# the final attempt alone.  The previous revision published a cost ratio of
# 0.450 on one configuration that is 0.659 over its retry-free seeds; the plan
# now requires both readings, and both need the cost per attempt.
#
# Nothing here is a gate.  What makes the figures believable is the summation
# identity the record module refuses on -- the per-attempt costs sum to the
# run's solve-phase totals -- and that identity is printed here run by run with
# its residual, in the shape task A58 (driver-predicate-counters) printed the
# sweep decomposition in.
#
# The population is the reproduction gate's own runs: they exist at this
# commit, they are made by the committed run path, and they are one seed each
# -- seed 0 for most rows, seed 1 for the rest.  No row here is a campaign
# statistic and none is quoted as one.


#: The demonstration runs, and why they exist.
#:
#: Every run of the reproduction gate converges on its **first** attempt, so
#: that population exercises the retry ladder's first rung and no other: the
#: per-attempt decomposition is there checked with exactly one term in each
#: sum.  A decomposition that has only ever been checked with one term is not
#: a decomposition, so the stage makes three runs that *must* retry.
#:
#: They retry because the optimiser's iteration budget is capped at two, which
#: makes its first attempt exit on "maximum iterations" and the driver try the
#: next rung -- a larger finite-difference step, then a smaller one.  The cap
#: is the harness's own gate-only switch: it is stamped into the record as
#: ``force_maxcal``, so a record made this way can never be mistaken for a
#: measurement, and **nothing in this block is a measurement of the models**.
#: What it measures is the accounting: three attempts, three sets of costs,
#: and the same identity.
LADDER_DEMONSTRATION_ARM = "BR"
LADDER_DEMONSTRATION_MAXCAL = 2


def ladder_root(campaign: Campaign) -> Path:
    return Path(campaign.runs_dir) / GATES_SUBPATH / "attempts" / "ladder"


def ladder_jobs(campaign: Campaign) -> list[pool_mod.Job]:
    return [
        pool_mod.Job(
            phase="B",
            arm=LADDER_DEMONSTRATION_ARM,
            config=config,
            seed=0,
            outdir=ladder_root(campaign) / config.name,
            regime="unperturbed",
            delta=campaign.delta,
            run_kind="gate",
            audit_position=NEUTRAL_AUDIT_POSITION,
            force_maxcal=LADDER_DEMONSTRATION_MAXCAL,
        )
        for config in campaign.configurations
    ]


def capture_ladder(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    """Run the three deliberately budget-capped runs that must retry."""
    jobs = ladder_jobs(campaign)
    results = pool_mod.run_all(jobs, campaign, resume=resume)
    manifest = {
        "captured": _dt.datetime.now().isoformat(timespec="seconds"),
        "tree_git_head": _git_head(),
        "n_runs": len(jobs),
        "arm": LADDER_DEMONSTRATION_ARM,
        "force_maxcal": LADDER_DEMONSTRATION_MAXCAL,
        "what": (
            "deliberately budget-capped runs whose only purpose is to make the "
            "retry ladder run more than one attempt.  Stamped force_maxcal in "
            "every record: NOT a measurement of the models"
        ),
        "runs": [
            {
                "configuration": job.config.name,
                "outdir": str(job.outdir),
                "status": (results[i] or {}).get("status")
                if isinstance(results, list)
                else None,
            }
            for i, job in enumerate(jobs)
        ],
    }
    path = ladder_root(campaign) / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    manifest["manifest"] = str(path)
    return manifest


def ladder_rows(campaign: Campaign) -> list[dict[str, Any]]:
    """One row per demonstration run, in the same shape as the gate's rows."""
    rows = []
    for config in campaign.configurations:
        directory = ladder_root(campaign) / config.name
        record = records_mod.read(directory)
        row = _attempt_row(
            LADDER_DEMONSTRATION_ARM, config.name, 0, record
        )
        row["force_maxcal"] = record.get("force_maxcal")
        rows.append(row)
    return rows


def attempt_rows(campaign: Campaign, root: Path | None = None) -> list[dict[str, Any]]:
    """One row per optimisation run of the reproduction gate, per attempt.

    Reads records; runs nothing.  A run directory with no record is a row that
    says so rather than a row silently dropped.
    """
    from harness import reproduction as reproduction_mod  # noqa: PLC0415

    base = Path(root or (Path(campaign.runs_dir) / reproduction_mod.RUNS_SUBPATH))
    rows: list[dict[str, Any]] = []
    for run in reference_mod.reference_set(campaign):
        if run.phase != "B":
            continue
        directory = (
            base / "runs" / run.configuration / run.arm
            / pool_mod.seed_directory(run.seed)
        )
        rows.append(
            _attempt_row(
                run.arm, run.configuration, run.seed, records_mod.read(directory)
            )
        )
    rows.sort(
        key=lambda r: (
            r["configuration"],
            MEASUREMENT_ARM_ORDER.index(r["arm"])
            if r["arm"] in MEASUREMENT_ARM_ORDER
            else len(MEASUREMENT_ARM_ORDER),
            r["seed"],
        )
    )
    return rows


def _attempt_row(
    arm: str, configuration: str, seed: int, record: Mapping[str, Any]
) -> dict[str, Any]:
    """One run's attempts, its decomposition and check 2's two constructions."""
    attempts = record.get("attempts") or []
    accounting = record.get("attempt_accounting") or {}
    forensics = record.get("exit_forensics") or {}
    total = record.get("node_calls_solve_phase")
    # The attempts that did not produce the accepted optimum are every attempt
    # but the last: the run's reported exit code, objective and iteration count
    # are the last attempt's.  Where the last attempt failed too the run is a
    # failure and this is still the share the earlier attempts cost.
    not_accepted = [a.get("node_calls_solve_phase") for a in attempts[:-1]]
    spent_before = (
        sum(int(v) for v in not_accepted if v is not None) if attempts else None
    )
    sums = accounting.get("sums") or {}
    return {
        "configuration": configuration,
        "arm": arm,
        "seed": seed,
        "status": record.get("status"),
        "n_attempts": len(attempts),
        "retried": len(attempts) > 1,
        "stages": [a.get("stage") for a in attempts],
        "ifail_per_attempt": [a.get("ifail") for a in attempts],
        "epsfcn_per_attempt": [a.get("epsfcn") for a in attempts],
        "node_calls_per_attempt": [
            a.get("node_calls_solve_phase") for a in attempts
        ],
        "sweeps_per_attempt": [a.get("sweeps") for a in attempts],
        "evaluations_per_attempt": [
            (a.get("sweeps_per_eval") or {}).get("n_evaluations") for a in attempts
        ],
        "node_calls_solve_phase": total,
        "dispatch_sweeps_solve_phase": record.get("dispatch_sweeps_solve_phase"),
        "node_calls_not_accepted": spent_before,
        "share_not_accepted": (
            (spent_before / total) if (total and spent_before is not None) else None
        ),
        # Check 2's two constructions, side by side on one run.
        "iterations_final_attempt": record.get("n_solver_iterations"),
        "iterations_summed_over_attempts": forensics.get(
            "n_solver_iterations_summed_over_attempts"
        ),
        "iterations_per_attempt": [a.get("n_iterations") for a in attempts],
        "evaluations_over_all_attempts": (record.get("sweeps_per_eval") or {}).get(
            "n_evaluations"
        ),
        # The identity, per run.
        "node_calls_residual": (sums.get("node_calls_solve_phase") or {}).get(
            "residual"
        ),
        "sweeps_residual": (sums.get("sweeps") or {}).get("residual"),
        "decomposes": accounting.get("decomposes"),
        "outside_attempts": accounting.get("outside_attempts") or {},
        "stage_names_agree_with_position": accounting.get(
            "stage_names_agree_with_position"
        ),
    }


def attempt_measurements(
    campaign: Campaign, root: Path | None = None
) -> dict[str, Any]:
    """The per-attempt block the report publishes, with its population."""
    rows = attempt_rows(campaign, root=root)
    finished = [r for r in rows if r["status"] == "ok"]
    retried = [r for r in finished if r["retried"]]
    checked = [r for r in finished if r["decomposes"] is not None]
    broken = [r for r in checked if not r["decomposes"]]
    return {
        "what": (
            "what each attempt of the optimiser's retry ladder cost, and the "
            "two constructions of the iteration count beside it.  Counts "
            "only; no conclusion here rests on a clock"
        ),
        "population": (
            f"{len(rows)} optimisation run(s) of the reproduction gate "
            f"({len(finished)} finished), one run per configuration and arm at "
            f"seed 0 or seed 1 — the gate's own set.  Not a campaign "
            f"statistic: there is one run behind every cell"
        ),
        "seeds": sorted({r["seed"] for r in rows}),
        "n_runs": len(rows),
        "n_finished": len(finished),
        "n_retried": len(retried),
        "which_retried": [
            f"{r['configuration']}/{r['arm']}/seed{r['seed']:03d}" for r in retried
        ],
        "which_did_not_retry": [
            f"{r['configuration']}/{r['arm']}/seed{r['seed']:03d}"
            for r in finished
            if not r["retried"]
        ],
        "summation_identity": {
            "identity": (
                "Σ attempts.node_calls_solve_phase == node_calls_solve_phase, "
                "and Σ attempts.sweeps == dispatch_sweeps_solve_phase"
            ),
            "n_checked": len(checked),
            "n_that_do_not_decompose": len(broken),
            "which": [
                f"{r['configuration']}/{r['arm']}/seed{r['seed']:03d}"
                for r in broken
            ],
            "max_abs_residual_node_calls": max(
                (abs(r["node_calls_residual"] or 0) for r in checked), default=None
            ),
            "max_abs_residual_sweeps": max(
                (abs(r["sweeps_residual"] or 0) for r in checked), default=None
            ),
            "refused_by": (
                "harness.records.assert_attempt_summation, which every record "
                "of every run goes through before it is summarised; a record "
                "whose parts do not add up is REFUSED, not rounded"
            ),
        },
        "ladder_demonstration": _ladder_block(campaign),
        "check_2_constructions": (
            "the final attempt's iteration count (the previous revision's, "
            "kept for comparability) and the count summed over every attempt, "
            "failed attempts included (the acceptance statistic).  They differ "
            "only on a retried run, which is the whole reason both are "
            "published"
        ),
        "rows": rows,
    }


def _ladder_block(campaign: Campaign) -> dict[str, Any]:
    """The demonstration runs, or a statement that they have not been made.

    Absent runs are reported as absent, never as an empty success: a
    decomposition checked only with one term per sum is the thing this block
    exists to stop being claimed.
    """
    try:
        rows = ladder_rows(campaign)
    except Exception as exc:  # noqa: BLE001 - reported, never raised
        return {"made": False, "why": f"{type(exc).__name__}: {exc}", "rows": []}
    made = [r for r in rows if r["status"] == "ok"]
    if not made:
        return {
            "made": False,
            "why": (
                "the demonstration runs have not been made; run "
                "'python -m harness.gates attempts --capture runs'.  Until "
                "they are, every run in this block converged on its first "
                "attempt and the decomposition has been checked with one term "
                "per sum only"
            ),
            "rows": rows,
        }
    return {
        "made": True,
        "what": (
            f"{len(made)} deliberately budget-capped run(s) whose optimiser "
            f"iteration budget is {LADDER_DEMONSTRATION_MAXCAL}, so the first "
            f"attempt exits on 'maximum iterations' and the driver climbs the "
            f"ladder.  Stamped force_maxcal in every record: NOT a measurement "
            f"of the models, and no cost figure here is comparable with any "
            f"campaign number"
        ),
        "population": (
            f"{len(rows)} run(s), the reference arm at seed 0 on each "
            f"configuration, one run each"
        ),
        "n_with_more_than_one_attempt": sum(1 for r in made if r["n_attempts"] > 1),
        "n_that_decompose": sum(1 for r in made if r["decomposes"]),
        "rows": rows,
    }


def print_attempts(block: Mapping[str, Any]) -> None:
    """The measurement, as the report prints it."""
    print("\n=== the retry ladder, per attempt (experiment plan §3.5; DR7)")
    print(f"    {block['what']}")
    print(f"    population : {block['population']}")
    print(
        f"    retried    : {block['n_retried']} of {block['n_finished']} "
        f"finished run(s)"
        + (f" — {', '.join(block['which_retried'])}" if block["which_retried"] else "")
    )
    print()
    head = (
        f"    {'configuration':<22} {'arm':<4} {'seed':>4} {'att':>4} "
        f"{'stages (ifail)':<34} {'node calls / attempt':<26} "
        f"{'not accepted':>13} {'share':>7}"
    )
    print(head)
    print("    " + "-" * (len(head) - 4))
    for row in block["rows"]:
        if row["status"] != "ok":
            print(
                f"    {row['configuration']:<22} {row['arm']:<4} "
                f"{row['seed']:>4} NO RECORD ({row['status']})"
            )
            continue
        stages = ", ".join(
            f"{stage} ({ifail})"
            for stage, ifail in zip(row["stages"], row["ifail_per_attempt"])
        )
        per_attempt = " + ".join(_n(v) for v in row["node_calls_per_attempt"])
        share = row["share_not_accepted"]
        print(
            f"    {row['configuration']:<22} {row['arm']:<4} {row['seed']:>4} "
            f"{row['n_attempts']:>4} {stages:<34} {per_attempt:<26} "
            f"{_n(row['node_calls_not_accepted']):>13} "
            f"{(f'{share * 100:.2f} %' if share is not None else '—'):>7}"
        )
    print()
    print("    check 2's two constructions, side by side, one run per row:")
    print(
        "      iterations of the final attempt (the previous revision's "
        "construction) against iterations summed over every attempt, failed "
        "attempts included (the acceptance statistic); the evaluation count "
        "over all attempts beside them"
    )
    head2 = (
        f"      {'configuration':<22} {'arm':<4} {'seed':>4} {'att':>4} "
        f"{'final':>7} {'summed':>7} {'per attempt':<18} {'evaluations':>12}"
    )
    print(head2)
    print("      " + "-" * (len(head2) - 6))
    for row in block["rows"]:
        if row["status"] != "ok":
            continue
        print(
            f"      {row['configuration']:<22} {row['arm']:<4} {row['seed']:>4} "
            f"{row['n_attempts']:>4} {_n(row['iterations_final_attempt']):>7} "
            f"{_n(row['iterations_summed_over_attempts']):>7} "
            f"{str(row['iterations_per_attempt']):<18} "
            f"{_n(row['evaluations_over_all_attempts']):>12}"
        )
    print()
    ladder = block["ladder_demonstration"]
    print("    the ladder exercised — the decomposition with more than one term:")
    if not ladder["made"]:
        print(f"      NOT MADE — {ladder['why']}")
    else:
        print(f"      {ladder['what']}")
        print(f"      population : {ladder['population']}")
        lhead = (
            f"      {'configuration':<22} {'att':>4} "
            f"{'stages (ifail)':<52} {'node calls / attempt':<30} "
            f"{'not accepted':>13} {'share':>8} {'residual':>9}"
        )
        print(lhead)
        print("      " + "-" * (len(lhead) - 6))
        for row in ladder["rows"]:
            if row["status"] != "ok":
                print(f"      {row['configuration']:<22} NO RECORD ({row['status']})")
                continue
            stages = ", ".join(
                f"{stage} ({ifail})"
                for stage, ifail in zip(row["stages"], row["ifail_per_attempt"])
            )
            per_attempt = " + ".join(_n(v) for v in row["node_calls_per_attempt"])
            share = row["share_not_accepted"]
            print(
                f"      {row['configuration']:<22} {row['n_attempts']:>4} "
                f"{stages:<52} {per_attempt:<30} "
                f"{_n(row['node_calls_not_accepted']):>13} "
                f"{(f'{share * 100:.2f} %' if share is not None else '—'):>8} "
                f"{_n(row['node_calls_residual']):>9}"
            )
        print(
            f"      {ladder['n_with_more_than_one_attempt']} of "
            f"{len(ladder['rows'])} run(s) made more than one attempt; "
            f"{ladder['n_that_decompose']} decompose with residual 0"
        )
    print()
    identity = block["summation_identity"]
    print(f"    summation identity: {identity['identity']}")
    print(
        f"      {identity['n_checked']} run(s) checked, "
        f"{identity['n_that_do_not_decompose']} that do not decompose"
        + (f": {identity['which']}" if identity["which"] else "")
    )
    print(
        f"      largest |residual|: {identity['max_abs_residual_node_calls']} "
        f"node call(s), {identity['max_abs_residual_sweeps']} sweep(s)"
    )
    print(f"      {identity['refused_by']}")
    print()
    print("    node calls and sweeps of the solve phase falling outside every")
    print("    attempt, per run — the premise the identity rests on:")
    for row in block["rows"]:
        if row["status"] != "ok":
            continue
        outside = row["outside_attempts"]
        print(
            f"      {row['configuration']:<22} {row['arm']:<4} "
            f"{row['seed']:>4} {_n(outside.get('node_calls')):>8} node call(s), "
            f"{_n(outside.get('sweeps')):>6} sweep(s)"
        )


# --------------------------------------------------------------------------
# G8 -- the convergence predicate's trial: two rulers, one implementation
# --------------------------------------------------------------------------
#
# The experiment plan's section 3.6 declares the trial and its three parts, and
# section 3.9 names the gate G8.  In one paragraph:
#
# The convergence test divides a step by a *ruler*.  The `frozen` ruler is a
# scale measured once over a harvest of design points; the `mixed` ruler keeps
# that scale as a floor and divides by the state's current magnitude where that
# is larger.  Wherever the current magnitude is at or below the scale the two
# are bit-identical, and `mixed` is never tighter, so no count can go up.  A
# pass is **decisive** when some component is at or above the tolerance on
# `frozen` and below it on `mixed` -- the only way the two can disagree at all.
#
# The three parts:
#
#   (1) neutrality -- under the default `frozen`, the runs reproduce the
#       previous revision bit for bit.  This is gate GR's own check and is not
#       re-implemented here: GR compares twenty of the previous revision's
#       records value for value, the evaluation-phase arms among them, and
#       every run it makes is composed under the default ruler.  G8 reads GR's
#       committed verdict and states what it covers.  A missing GR verdict is a
#       FAIL, not a skip: a criterion whose evidence is not there is not a
#       criterion (trap T11).
#
#   (2) the identity -- a pair of runs with no decisive pass must be
#       bit-identical.  This holds by construction, so a pair where it does not
#       is an implementation defect and the gate FAILS.
#
#   (3) the binding set -- for every pair that does have a decisive pass: where
#       it happened, which components, `|y| / s` there, and whether the
#       component was the one holding the pass open under `frozen`.  If none
#       occurs at these seeds that is a **result**, stated with its population,
#       not a gap.
#
# **Why the gate does not infer (2) from the records alone.**  "No decisive
# pass" cannot be read off two run records: a decisive pass is an event inside
# a loop, and a record carries counters.  Inferring "there was no decisive
# pass" from "the two runs agree" and then checking that they agree is
# circular, and a circular gate passes on a defect.  So the gate's runs carry
# the ruler observer (``child.install_ruler_observer``), which watches every
# predicate evaluation on both rulers and writes what it saw to its own file.
# The observer returns the run's own residual unchanged, so the runs it watches
# are exactly the runs the gate compares.
#
# **Two events, not one, and the difference matters.**  The plan's *decisive
# pass* is componentwise: some component crosses the tolerance between the
# rulers.  That is the binding set of part (3).  Whether the pair's runs may
# then *differ* is a narrower question -- it needs the crossing component to
# have been the one holding the evaluation open, so that the evaluation's
# verdict changes.  A component can cross while another still holds the loop
# open, and then the two runs stay bit-identical with a non-empty binding set.
# Both counts are recorded, and part (2)'s criterion binds on the narrower one:
# reporting the wider event as the narrower would let a defect hide behind a
# crossing that could not have caused it.

#: The arms and seeds the trial runs.  Evaluation-phase arms only: the plan
#: licenses the optimisation phase under `mixed` **only if** the evaluation
#: phase shows a decisive pass on an in-loop component, so running it here
#: would be spending the licence before it is granted.
PREDICATE_MODE_ARMS: tuple[str, ...] = ("A0", "A1")
PREDICATE_MODE_SEEDS: tuple[int, ...] = (1, 2)

#: Record leaves that differ between the two runs of a pair **by construction**,
#: each with the reason.  A much shorter list than G1's, and deliberately: G1's
#: two sides are at different commits and made by different revisions of the
#: harness, while these two sides are the same code at the same commit run twice
#: with one setting changed, so almost nothing is licensed to differ.  In
#: particular ``exit_audit.mixed`` is **not** here.  The plan allows it to be
#: excluded; it is compared instead, because a pair with no decisive pass
#: reaches the same exit state and both audits of one exit state are the same
#: numbers -- so comparing it costs nothing and is strictly stronger.
PREDICATE_PAIR_EXCLUSIONS: dict[str, str] = {
    # where the run happened
    "outdir": "the two runs are in different directories, by construction",
    # how long it took, and what the machine was doing
    "wall_s": "wall clock is context, never evidence (I-10)",
    "cpu_user_s": "cpu time is a contention diagnostic",
    "cpu_sys_s": "cpu time is a contention diagnostic",
    "cpu_s": "cpu time is a contention diagnostic",
    "maxrss_kb": "peak memory varies with the machine's state",
    "loadavg": "machine load while it ran",
    "mfile.process_runtime": "PROCESS's own timing of itself",
    "tree_untracked_paths": "the working tree's state, not the driver's behaviour",
    "tree_untracked_paths_n": "the count of the list above, on the same reason",
    # the mode stamps -- the thing being varied.  Every one of these is the
    # setting itself or the driver's readback of it; comparing them would be
    # comparing the change to itself.
    "campaign_predicate_mode": (
        "the setting being varied: 'frozen' on one side, 'mixed' on the other"
    ),
    "switches_asked.predicate_mode": (
        "the term the arm composes under 'mixed' and does not under 'frozen'"
    ),
    "env_architecture.env_PROCESS_ARCH_PREDICATE": (
        "the environment variable being varied, as the record spells it "
        "(the block prefixes every name with 'env_')"
    ),
    "resolved_switches.process.core.solver.module_solve.PREDICATE_MODE": (
        "the driver's readback of the setting being varied.  It is what proves "
        "each run was the arm it says it was, and is checked as such, per run, "
        "before anything is concluded from the pair"
    ),
    "coupling_state_provenance.predicate_mode": (
        "the loaded spec's stamp of the same setting"
    ),
    "exit_audit.predicate_mode": "the audit's stamp of the same setting",
    "exit_audit.rulers_note": (
        "prose, identical on both sides, excluded beside the stamps it explains"
    ),
}


def predicate_mode_root(campaign: Campaign) -> Path:
    return Path(campaign.runs_dir) / GATES_SUBPATH / "predicate_mode"


def predicate_mode_run_dir(
    campaign: Campaign, mode: str, configuration: str, arm: str, seed: int
) -> Path:
    return (
        predicate_mode_root(campaign)
        / mode
        / configuration
        / arm
        / pool_mod.seed_directory(seed)
    )


def predicate_mode_pairs(campaign: Campaign) -> list[dict[str, Any]]:
    """Every (configuration, arm, seed) the trial runs under both rulers."""
    pairs: list[dict[str, Any]] = []
    for config in campaign.configurations:
        for arm in PREDICATE_MODE_ARMS:
            if arm in config.skips:
                continue
            for seed in PREDICATE_MODE_SEEDS:
                pairs.append({"config": config, "arm": arm, "seed": seed})
    return pairs


def predicate_mode_reference_dir(campaign: Campaign, configuration: str) -> Path:
    """Where a configuration's undisplaced evaluation reference lives.

    The evaluation phase displaces a *converged* state, not the input file's
    cold values, so each configuration needs one undisplaced evaluation first:
    its exit state is what every displaced entry is built from, and its
    converged burn time is what the constant owns on the arm that takes the
    quantity out of the loop.  The gate makes its own rather than reading
    another gate's, so that it can be run on its own and so that no two gates
    share a run directory.
    """
    return predicate_mode_root(campaign) / "reference" / configuration


def predicate_mode_reference_jobs(campaign: Campaign) -> list[pool_mod.Job]:
    return [
        pool_mod.Job(
            phase="A",
            arm="A0",
            config=config,
            seed=0,
            outdir=predicate_mode_reference_dir(campaign, config.name),
            regime="unperturbed",
            delta=None,
            run_kind="gate",
        )
        for config in campaign.configurations
    ]


def predicate_mode_entries(campaign: Campaign) -> dict[str, dict[str, Any]]:
    """Each configuration's reference exit state and converged burn time."""
    from harness import reproduction as reproduction_mod  # noqa: PLC0415

    entries: dict[str, dict[str, Any]] = {}
    for config in campaign.configurations:
        directory = predicate_mode_reference_dir(campaign, config.name)
        record = records_mod.read(directory)
        if record.get("status") != "ok":
            raise GateError(
                f"G8's evaluation reference for {config.name} did not finish "
                f"(status {record.get('status')!r}, taxonomy row "
                f"{record.get('failure_class')!r}).  Every displaced entry is "
                f"built from its exit state, so there is nothing to displace: "
                f"the gate stops here rather than entering the runs from "
                f"somewhere else."
            )
        entries[config.name] = {
            "outdir": str(directory),
            "snapshot": str(directory / "y_exit.json"),
            "t_plant_pulse_burn_hex": record.get("t_plant_pulse_burn_hex"),
            "pin_for": reproduction_mod.pin_for,
        }
    return entries


def predicate_mode_jobs(
    campaign: Campaign, entries: Mapping[str, dict[str, Any]] | None = None
) -> list[pool_mod.Job]:
    """The trial's runs.  Both rulers, entered from the same state per pair.

    The two runs of a pair are entered from the **same** snapshot with the
    **same** constant, which is what makes their difference attributable to the
    ruler and nothing else.
    """
    jobs: list[pool_mod.Job] = []
    for pair in predicate_mode_pairs(campaign):
        config, arm_name, seed = pair["config"], pair["arm"], pair["seed"]
        arm = arms_mod.ARMS[arm_name]
        entry_state = None
        pin_hex = None
        if entries is not None:
            entry = entries[config.name]
            entry_state = Path(entry["snapshot"])
            if config.pulsed and arm.burn_time_owner == "constant":
                pin_hex = entry["pin_for"](
                    entry["t_plant_pulse_burn_hex"], seed, campaign.delta
                )
        for mode in campaign.predicate_modes:
            jobs.append(
                pool_mod.Job(
                    phase="A",
                    arm=arm_name,
                    config=config,
                    seed=seed,
                    outdir=predicate_mode_run_dir(
                        campaign, mode, config.name, arm_name, seed
                    ),
                    regime="perturbed",
                    delta=campaign.delta,
                    run_kind="gate",
                    predicate_mode=mode,
                    entry_state=entry_state,
                    pin_hex=pin_hex,
                    # The gate's detector.  Not a switch: the driver has never
                    # heard of this name, so it cannot be mistaken for one, and
                    # the child refuses it outright on a campaign run.
                    override_env={child_mod.RULER_OBSERVER_VARIABLE: "1"},
                )
            )
    return jobs


def capture_predicate_mode(
    campaign: Campaign, *, resume: bool = False
) -> dict[str, Any]:
    """Run every pair under both rulers, with the observer installed.

    The undisplaced references run first and the displaced pairs follow,
    because the pairs are entered from the references' exit states.
    """
    references = predicate_mode_reference_jobs(campaign)
    pool_mod.run_all(references, campaign, resume=resume)
    jobs = predicate_mode_jobs(campaign, predicate_mode_entries(campaign))
    results = pool_mod.run_all(jobs, campaign, resume=resume)
    manifest = {
        "captured": _dt.datetime.now().isoformat(timespec="seconds"),
        "tree_git_head": _git_head(),
        "n_runs": len(jobs),
        "arms": list(PREDICATE_MODE_ARMS),
        "seeds": list(PREDICATE_MODE_SEEDS),
        "rulers": list(campaign.predicate_modes),
        "delta": campaign.delta,
        "observer": child_mod.RULER_OBSERVER_VARIABLE,
        "runs": [
            {
                "configuration": job.config.name,
                "arm": job.arm,
                "seed": job.seed,
                "ruler": job.predicate_mode,
                "outdir": str(job.outdir),
                "status": (results[i] or {}).get("status")
                if isinstance(results, list)
                else None,
            }
            for i, job in enumerate(jobs)
        ],
    }
    path = predicate_mode_root(campaign) / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    manifest["manifest"] = str(path)
    return manifest


def _observation(directory: Path, *, key: str) -> dict[str, Any]:
    path = Path(directory) / child_mod.RULER_OBSERVATION_FILE
    if not path.exists():
        raise GateError(
            f"G8 has no ruler observation for {key}: {path} is not there.  "
            f"Without it the gate would have to infer 'there was no decisive "
            f"pass' from 'the two runs agree', which is the thing it is "
            f"checking; a check that assumes its own conclusion is not a check."
        )
    return json.loads(path.read_text())


def _neutrality_from_reproduction(campaign: Campaign) -> dict[str, Any]:
    """Part (1): what gate GR already proves about the default ruler.

    Not re-implemented here.  GR reproduces twenty of the previous revision's
    records value for value, its evaluation-phase arms among them, and every
    run it makes is composed under the default ruler -- so "the default ruler
    moves nothing" is GR's verdict, read rather than re-measured.  What this
    adds is a statement of *what* GR covers, because a gate silent about its
    own coverage boundary is trap T11's shape.
    """
    # Imported here rather than at the top: reproduction imports selfcheck,
    # which imports this module, so a module-level import back would be a cycle.
    from harness import reproduction as reproduction_mod  # noqa: PLC0415

    path = Path(campaign.runs_dir) / reproduction_mod.RUNS_SUBPATH / "gate.json"
    if not path.exists():
        return {
            "passed": False,
            "verdict": "NO EVIDENCE",
            "record": str(path),
            "why": (
                "gate GR has not been run at this commit, so G8's neutrality "
                "part has no evidence.  It is neither skipped nor assumed: run "
                "'experiment_runner.py --gate reproduction' and re-run this "
                "gate."
            ),
        }
    verdict = json.loads(path.read_text())
    # The file holds the framework's verdict for the gate, which carries the
    # stage's own verdict inside it under 'reproduction'; older files are the
    # stage's verdict alone.  Both shapes are read, because a gate that could
    # not read its own evidence would report NO EVIDENCE over a file that has
    # it.
    inner = verdict.get("reproduction") or verdict
    comparison = inner.get("comparison") or {}
    return {
        "passed": verdict.get("verdict") == "PASS",
        "verdict": verdict.get("verdict"),
        "record": str(path),
        "tree": inner.get("tree"),
        "n_runs_reproduced": comparison.get("n_runs_reproduced"),
        "n_runs": comparison.get("n_runs"),
        "n_values_compared": comparison.get("n_values_compared"),
        "n_values_differing": comparison.get("n_values_mismatched"),
        "gr_population": comparison.get("population"),
        "covers": (
            "every run gate GR makes is composed under the default ruler, so "
            "GR's bit-for-bit reproduction of the previous revision's records "
            "-- the evaluation-phase arms among them -- is the neutrality "
            "criterion.  It is read here, never re-measured: a second "
            "implementation of one comparison is the drift decision D14(c) "
            "exists to prevent."
        ),
    }


def predicate_mode_body(campaign: Campaign) -> dict[str, Any]:
    """Parts (1), (2) and (3), over every pair the trial runs."""
    neutrality = _neutrality_from_reproduction(campaign)
    frozen_name = campaign.predicate_modes[0]
    mixed_name = campaign.predicate_modes[1]
    rows: list[dict[str, Any]] = []
    binding: list[dict[str, Any]] = []
    n_values = n_excluded = n_differing = 0
    n_lines = n_line_differing = 0
    n_identical_pairs = n_changed_verdict_pairs = 0
    n_evaluations = 0

    for pair in predicate_mode_pairs(campaign):
        config, arm, seed = pair["config"], pair["arm"], pair["seed"]
        key = f"{arm}/{config.name}/seed{seed:03d}"
        by_mode: dict[str, dict[str, Any]] = {}
        observed: dict[str, dict[str, Any]] = {}
        for mode in campaign.predicate_modes:
            directory = predicate_mode_run_dir(
                campaign, mode, config.name, arm, seed
            )
            by_mode[mode] = _read_record(directory, side=mode, key=key)
            observed[mode] = _observation(directory, key=f"{key} under {mode}")

        # Each run really was the arm it says it was: the driver's own readback,
        # checked before anything is concluded from the pair.  This is the
        # failure the switch registry exists for -- a setting the tree ignores
        # produces a successful run of a different arm under the right name.
        resolved_wrong = [
            mode
            for mode in campaign.predicate_modes
            if (by_mode[mode].get("resolved_switches") or {}).get(
                "process.core.solver.module_solve.PREDICATE_MODE"
            )
            != mode
        ]

        # The decisive-pass question, answered by the observer on the FROZEN
        # run: it is that run's trajectory a mixed run would depart from.
        frozen_obs = observed[frozen_name]
        decisive_evaluations = frozen_obs[
            "n_evaluations_with_a_decisive_component"
        ]
        verdict_changes = frozen_obs["n_evaluations_where_the_verdict_changed"]
        n_evaluations += frozen_obs["n_predicate_evaluations_observed"]

        comparison = compare_records(
            by_mode[frozen_name],
            by_mode[mixed_name],
            excluded=PREDICATE_PAIR_EXCLUSIONS,
        )
        n_values += comparison["n_compared"]
        n_excluded += comparison["n_excluded"]
        n_differing += comparison["n_mismatched"]

        mfiles = {
            mode: _mfile_for(
                predicate_mode_run_dir(campaign, mode, config.name, arm, seed),
                config.name,
            )
            for mode in campaign.predicate_modes
        }
        if any(path is None for path in mfiles.values()):
            raise GateError(
                f"G8 has no output file for {key} on one side ({mfiles}); the "
                f"line comparison would be over nothing"
            )
        mfile = compare_mfiles(mfiles[frozen_name], mfiles[mixed_name])
        n_lines += mfile["n_lines_compared"]
        n_line_differing += mfile["n_lines_differing"]

        pair_identical = (
            comparison["n_mismatched"] == 0 and mfile["n_lines_differing"] == 0
        )
        if pair_identical:
            n_identical_pairs += 1
        if verdict_changes:
            n_changed_verdict_pairs += 1

        # Part (2)'s criterion, and it binds only where no evaluation changed
        # its verdict.  Where one did, the pair is *allowed* to differ and part
        # (3) says what made it.
        passed = not resolved_wrong and (
            pair_identical or verdict_changes > 0
        )

        for event in frozen_obs["decisive"]:
            for component in event["components"]:
                binding.append(
                    {
                        "configuration": config.name,
                        "arm": arm,
                        "seed": seed,
                        "evaluation": event["evaluation"],
                        "component": component["component"],
                        "value_over_scale": component["value_over_scale"],
                        "frozen_scaled_hex": component["frozen_scaled_hex"],
                        "mixed_scaled_hex": component["other_scaled_hex"],
                        "held_the_pass_under_frozen": component[
                            "held_the_pass_under_frozen"
                        ],
                        "changed_the_evaluation_verdict": event[
                            "verdict_changed"
                        ],
                    }
                )

        rows.append(
            {
                "configuration": config.name,
                "arm": arm,
                "seed": seed,
                "status": {m: by_mode[m].get("status") for m in by_mode},
                "resolved_wrong": resolved_wrong,
                "n_predicate_evaluations": frozen_obs[
                    "n_predicate_evaluations_observed"
                ],
                "n_evaluations_with_a_decisive_component": decisive_evaluations,
                "n_evaluations_where_the_verdict_changed": verdict_changes,
                "components_compared": {
                    m: by_mode[m].get("components_compared") for m in by_mode
                },
                "components_compared_identical": (
                    by_mode[frozen_name].get("components_compared")
                    == by_mode[mixed_name].get("components_compared")
                ),
                "record": comparison,
                "mfile": mfile,
                "identical": pair_identical,
                "criterion": (
                    "bit-identical (no evaluation changed its verdict)"
                    if verdict_changes == 0
                    else "may differ (an evaluation changed its verdict)"
                ),
                "audit": {
                    run_ruler: {
                        audit_ruler: (
                            (by_mode[run_ruler].get("exit_audit") or {})
                            .get(audit_ruler, {})
                            .get("residual_max_hex")
                        )
                        for audit_ruler in campaign.predicate_modes
                    }
                    for run_ruler in by_mode
                },
                "passed": passed,
            }
        )

    passed = (
        neutrality["passed"]
        and bool(rows)
        and all(row["passed"] for row in rows)
    )
    return {
        "passed": passed,
        "population": (
            f"{len(rows)} pair(s) = {len(campaign.configurations)} "
            f"configuration(s) x the evaluation-phase arms active on each "
            f"({', '.join(PREDICATE_MODE_ARMS)}) x "
            f"{len(PREDICATE_MODE_SEEDS)} seed(s), each run under both rulers "
            f"= {2 * len(rows)} runs at delta = {campaign.delta}; "
            f"{n_values} deterministic record values and {n_lines} output-file "
            f"lines compared without tolerance, {n_excluded} record values "
            f"excluded as the setting being varied or as run metadata (each "
            f"named, with its reason, in this record); {n_evaluations} "
            f"predicate evaluations observed on both rulers"
        ),
        "neutrality_is_gate_GR": neutrality,
        "n_pairs": len(rows),
        "n_pairs_bit_identical": n_identical_pairs,
        "n_pairs_with_a_changed_verdict": n_changed_verdict_pairs,
        "n_values_compared": n_values,
        "n_values_excluded": n_excluded,
        "n_values_differing": n_differing,
        "n_mfile_lines_compared": n_lines,
        "n_mfile_lines_differing": n_line_differing,
        "n_predicate_evaluations_observed": n_evaluations,
        "n_binding_component_events": len(binding),
        "binding_set": binding,
        "binding_set_empty_because": (
            None
            if binding
            else (
                "no component was at or above the tolerance on the frozen "
                "ruler and below it on the mixed one at any of the "
                f"{n_evaluations} predicate evaluations these {2 * len(rows)} "
                f"runs made.  That is a result about these arms and these "
                f"seeds, stated with its population, not a gap: the observer "
                f"that would have seen one is the same one the teeth below "
                f"exercise."
            )
        ),
        "excluded_record_paths": PREDICATE_PAIR_EXCLUSIONS,
        "runs": rows,
    }


def _predicate_mode_teeth(campaign: Campaign) -> tuple[Tooth, ...]:
    """Four breaks: two on the ruler itself, two on the gate's own comparisons."""

    def doctored_component() -> tuple[bool, str]:
        """The plan's tooth: a component at 100 s with dy = 50 tau s.

        Built on the :class:`Residual` directly, from a two-component synthetic
        spec, so that what is exercised is the arithmetic and not a run.  The
        magnitudes are the *current* values, which is what the mixed ruler
        divides by, so the first component's current value is exactly 100 s and
        the second's is exactly s.
        """
        ystate = _load_ystate()
        tau = campaign.tau
        scale = 2.0
        spec = ystate.YSpec(
            [("doctored", "far_above_its_scale"), ("doctored", "at_its_scale")],
            [ystate.CONTINUOUS, ystate.CONTINUOUS],
            [scale, scale],
            1,
            [
                {"key": "doctored.far_above_its_scale"},
                {"key": "doctored.at_its_scale"},
            ],
            mode=ystate.SPEC_MODE_A26,
        )
        step = 50.0 * tau * scale
        cur = [100.0 * scale, scale]
        prev = [cur[0] - step, cur[1] - step]
        frozen = spec.residual(prev, cur, ruler=ystate.RULER_FROZEN)
        mixed = spec.residual(prev, cur, ruler=ystate.RULER_MIXED)
        far_fails_frozen = float(frozen.scaled[0]) >= tau
        far_passes_mixed = float(mixed.scaled[0]) < tau
        at_fails_frozen = float(frozen.scaled[1]) >= tau
        at_fails_mixed = float(mixed.scaled[1]) >= tau
        caught = (
            far_fails_frozen
            and far_passes_mixed
            and at_fails_frozen
            and at_fails_mixed
        )
        return caught, (
            f"at y = 100 s the scaled step is {float(frozen.scaled[0]):.3e} "
            f"frozen (>= tau = {tau:g}) and {float(mixed.scaled[0]):.3e} mixed "
            f"(< tau); the same dy at y = s is "
            f"{float(frozen.scaled[1]):.3e} frozen and "
            f"{float(mixed.scaled[1]):.3e} mixed, above tau on both"
        )

    def bit_identity_below_the_scale() -> tuple[bool, str]:
        """Where |y| <= s the two rulers must agree to the last bit.

        Not decoration: it is the property the identity criterion rests on.  If
        the two rulers differed by an ULP on components where they are supposed
        to be the same expression, every pair would differ and part (2) would be
        vacuous.
        """
        ystate = _load_ystate()
        scale = 7.5
        spec = ystate.YSpec(
            [("doctored", "below_its_scale")],
            [ystate.CONTINUOUS],
            [scale],
            1,
            [{"key": "doctored.below_its_scale"}],
            mode=ystate.SPEC_MODE_A26,
        )
        prev = [scale * 0.25]
        cur = [scale * 0.25 + 1.0e-9]
        frozen = spec.residual(prev, cur, ruler=ystate.RULER_FROZEN)
        mixed = spec.residual(prev, cur, ruler=ystate.RULER_MIXED)
        same = float(frozen.scaled[0]).hex() == float(mixed.scaled[0]).hex()
        return same, (
            f"at |y| = {cur[0]:g} <= s = {scale:g} both rulers give "
            f"{float(frozen.scaled[0]).hex()}"
        )

    def one_ulp_between_two_identical_records() -> tuple[bool, str]:
        """The identity check must catch a 1-ULP difference.

        The gate's central claim is a zero over a population of record values.
        A zero from a comparator that cannot see the smallest possible
        difference is an assertion, so one is planted here: a copy of a record
        with one float moved by a single unit in the last place, compared with
        the original under the gate's own exclusion set.
        """
        pairs = predicate_mode_pairs(campaign)
        if not pairs:
            return False, "there are no pairs, so there is nothing to perturb"
        pair = pairs[0]
        directory = predicate_mode_run_dir(
            campaign,
            campaign.predicate_modes[0],
            pair["config"].name,
            pair["arm"],
            pair["seed"],
        )
        record = _read_record(
            directory, side=campaign.predicate_modes[0], key="a tooth"
        )
        audit = (record.get("exit_audit") or {}).get(
            campaign.predicate_modes[0]
        ) or {}
        original = audit.get("residual_max")
        if not isinstance(original, float):
            return False, (
                "the sample record carries no float exit-audit residual to "
                "perturb, so the tooth would be planted in nothing"
            )
        moved = copy.deepcopy(record)
        nudged = math.nextafter(original, math.inf)
        moved["exit_audit"][campaign.predicate_modes[0]]["residual_max"] = nudged
        result = compare_records(
            record, moved, excluded=PREDICATE_PAIR_EXCLUSIONS
        )
        return result["n_mismatched"] == 1, (
            f"exit_audit.{campaign.predicate_modes[0]}.residual_max moved from "
            f"{original.hex()} to {nudged.hex()} (1 ULP): "
            f"{result['n_mismatched']} of {result['n_compared']} compared "
            f"values differ"
        )

    def a_stamp_that_is_not_excluded() -> tuple[bool, str]:
        """The exclusion set must not be wider than it says.

        A gate's zero is only worth its exclusion list, so the list is checked
        for the one thing it must not cover: the exit audit's *mixed* block,
        which the plan permits excluding and which this gate compares.  A
        difference planted there must be caught.
        """
        pairs = predicate_mode_pairs(campaign)
        if not pairs:
            return False, "there are no pairs, so there is nothing to perturb"
        pair = pairs[0]
        directory = predicate_mode_run_dir(
            campaign,
            campaign.predicate_modes[0],
            pair["config"].name,
            pair["arm"],
            pair["seed"],
        )
        record = _read_record(
            directory, side=campaign.predicate_modes[0], key="a tooth"
        )
        moved = copy.deepcopy(record)
        block = moved["exit_audit"][campaign.predicate_modes[1]]
        block["residual_max_hex"] = str(block["residual_max_hex"]) + "0"
        result = compare_records(
            record, moved, excluded=PREDICATE_PAIR_EXCLUSIONS
        )
        return result["n_mismatched"] == 1, (
            f"a changed exit_audit.{campaign.predicate_modes[1]}."
            f"residual_max_hex gives {result['n_mismatched']} differing "
            f"value(s): the mixed audit is compared, not excluded"
        )

    return (
        Tooth(
            name="doctored_component",
            what="a component at y = 100 s with dy = 50 tau s, and the same dy at y = s",
            must="fail frozen and pass mixed; fail both",
            check=doctored_component,
        ),
        Tooth(
            name="bit_identity_below_the_scale",
            what="a component with |y| well below its scale",
            must="give the identical float on both rulers",
            check=bit_identity_below_the_scale,
        ),
        Tooth(
            name="one_ulp_between_identical_records",
            what="one float of a record moved by a single unit in the last place",
            must="be caught by the identity comparison",
            check=one_ulp_between_two_identical_records,
        ),
        Tooth(
            name="the_mixed_audit_is_compared",
            what="a changed exit_audit.mixed value",
            must="be caught -- the block the plan permits excluding is compared",
            check=a_stamp_that_is_not_excluded,
        ),
    )


def _load_ystate():
    """The coupling-state module, the way everything else in the harness gets it."""
    from harness import ystate as ystate_mod  # noqa: PLC0415

    return ystate_mod


def _plan_gates(campaign: Campaign) -> dict[str, Gate]:
    """The gates of the experiment plan's §3.9 table, by name.

    The plan's label for each is on the gate as ``plan_name``, so a reader can
    go from the plan's table to this dictionary and back without a second
    mapping to maintain.  ``G0`` and ``G0'`` are **one gate** here: the V4 plan
    §3.9's G0 row and §7.6's G0' state the same criterion — the copy's
    ``process/models/`` byte-identical to the frozen base commit — and giving
    one criterion two entries is how two implementations start.
    """
    from . import gate_audit, gate_composition, gate_entry, gate_prime, gate_records

    return {
        "reproduction": Gate(
            name="reproduction",
            plan_name="GR",
            needs_runs=True,
            binds=(
                "the harness rewrite and the experiment's copy of PROCESS, "
                "once, at the copy commit before any driver change"
            ),
            what_it_proves=(
                "the rewritten harness reproduces the previous revision's "
                "twenty runs bit for bit on every count field and hex float, "
                "so the rewrite changed the measurement in no respect this "
                "experiment compares on"
            ),
            body=lambda *, resume=False: _reproduction_body(campaign, resume=resume),
            teeth=_reproduction_teeth(),
        ),
        "g0prime": Gate(
            name="g0prime",
            plan_name="G0 / G0'",
            binds="every V4 commit, every arm, both phases",
            what_it_proves=(
                "the physics and engineering models in the experiment's own "
                "copy of PROCESS are byte-identical to the frozen base commit, "
                "bar the one structural edit the user approved"
            ),
            body=lambda *, resume=False: g0prime_body(campaign),
            teeth=_g0prime_teeth(campaign),
        ),
        "switch_neutrality": Gate(
            name="switch_neutrality",
            plan_name="G1",
            needs_runs=True,
            binds="each driver change, run per change and never batched",
            what_it_proves=(
                "with every architecture switch unset, the copy after the "
                "change behaves byte-identically to the copy before it"
            ),
            body=lambda *, resume=False: neutrality_body(campaign, resume=resume),
            runs_under=("switch_neutrality/after",),
            teeth=_neutrality_teeth(campaign),
        ),
        "prime_map": gate_prime.prime_map_gate(campaign),
        "cold_chain": gate_prime.cold_chain_gate(campaign),
        "audit_restriction": gate_audit.audit_restriction_gate(campaign),
        "switch_composition": gate_composition.switch_composition_gate(campaign),
        "entry_and_warm": gate_entry.entry_and_warm_gate(campaign),
        "record_completeness": gate_records.record_completeness_gate(campaign),
        "predicate_mode": Gate(
            name="predicate_mode",
            plan_name="G8",
            needs_runs=True,
            binds=(
                "the convergence predicate's second ruler, on the "
                "evaluation-phase arms of every configuration"
            ),
            what_it_proves=(
                "the default ruler moves nothing (gate GR's own check, read "
                "here); a pair of runs no evaluation decided differently is "
                "bit-identical under the two rulers; and the components on "
                "which the two rulers do disagree are named with |y| / s "
                "there, or their absence is stated with its population"
            ),
            body=lambda *, resume=False: _with_capture(
                capture_predicate_mode, predicate_mode_body, campaign, resume=resume
            ),
            # Its neutrality part is the reproduction gate's verdict, read
            # rather than re-measured, so that verdict has to exist first.
            reads_from=("reproduction",),
            teeth=_predicate_mode_teeth(campaign),
        ),
        "output_path": Gate(
            name="output_path",
            plan_name="G9",
            needs_runs=True,
            binds=(
                "the removal of the output-time loop from the arms whose "
                "matrix cell turns it off, on every configuration where they "
                "are active"
            ),
            what_it_proves=(
                "the state those arms write to their output files is the "
                "state their solve handed over — bit for bit, outside the "
                "per-run deferred nodes' own writes — with no output-time "
                "sweep run and the accepted objective in the file; and that "
                "nothing about the solve changed on the arms that keep the "
                "loop"
            ),
            body=lambda *, resume=False: _with_capture(
                capture_output_path, output_path_body, campaign, resume=resume
            ),
            runs_under=("output_path/runs",),
            # It compares its reference arms against the reproduction gate's
            # own records, so it cannot run before that gate has made them.
            reads_from=("reproduction",),
            teeth=_output_path_teeth(campaign),
        ),
    }


# --------------------------------------------------------------------------
# the entry reference every warm gate is anchored on
# --------------------------------------------------------------------------
#
# Three gates -- G2 (the prime's fixed-point map), G4 (the audit restriction)
# and G6 (entry and warm equivalence) -- all start from the same thing: one
# undisplaced evaluation of the flat control per configuration, entered cold
# from the input file's own design point.  Its exit state is the fixed point
# every warm run is entered from and its converged burn time is what a constant
# owns.  It is made once, here, and shared, because three gates making their own
# would be three fixed points that have to be argued to be the same one.
#
# The directory shape is `reproduction.phase_a_reference_directory`'s, imported
# rather than restated, so the reproduction gate's references and these are the
# same construction and can be read side by side.


def entry_reference_root(campaign: Campaign) -> Path:
    return Path(campaign.runs_dir) / GATES_SUBPATH / "entry_references"


#: Which run roots this process has already made its shared cold-flat
#: references under.  Three gates are anchored on them, and without this the
#: second and third gate of one ``--gate all`` would re-make what the first just
#: made — so the references are made **once per invocation** and shared, which
#: is what they were for.  The memo is per process: a new invocation makes them
#: again unless ``--resume`` says otherwise.
_ENTRY_REFERENCES_MADE: set[str] = set()


def entry_references(
    campaign: Campaign, *, resume: bool = False
) -> dict[str, dict[str, Any]]:
    """One cold flat evaluation per configuration, and what it left behind.

    Returns, per configuration: the exit snapshot's path, the converged burn
    time as a hex literal, the run's own exit-audit maximum, and the cold-start
    cost.  A configuration whose reference did not finish **refuses** -- every
    warm run is entered from its exit state, so there is nothing to enter from,
    and that is a result rather than a reason to enter from somewhere else.
    """
    from . import reproduction as reproduction_mod

    root = entry_reference_root(campaign)
    jobs = [
        pool_mod.Job(
            phase="A",
            arm="A0",
            config=config,
            seed=0,
            outdir=reproduction_mod.phase_a_reference_directory(root, config.name),
            regime="unperturbed",
            delta=None,
            run_kind="gate",
        )
        for config in campaign.configurations
    ]
    already = str(root) in _ENTRY_REFERENCES_MADE
    pool_mod.run_all(jobs, campaign, resume=resume or already)
    _ENTRY_REFERENCES_MADE.add(str(root))
    references: dict[str, dict[str, Any]] = {}
    for job in jobs:
        record = records_mod.read(job.outdir)
        if record.get("status") != "ok":
            raise GateError(
                f"the entry reference for {job.config.name} did not finish "
                f"(status {record.get('status')!r}, taxonomy row "
                f"{record.get('failure_class')!r}).  Every warm run of every "
                f"gate is entered from its exit state, so the gates that need "
                f"it stop here rather than entering from somewhere else."
            )
        references[job.config.name] = {
            "outdir": str(job.outdir),
            "snapshot": str(Path(job.outdir) / "y_exit.json"),
            "t_plant_pulse_burn_hex": record.get("t_plant_pulse_burn_hex"),
            "audit_residual_max_hex": (record.get("exit_audit") or {}).get(
                "residual_max_hex"
            ),
            "cold_start_node_calls": record.get("node_calls_single_eval"),
            "cold_start_sweeps": record.get("n_model_calls_sweeps"),
        }
    return references


def _with_capture(
    capture, body, campaign: Campaign, *, resume: bool = False
) -> dict[str, Any]:
    """Make the gate's own runs, then compare them.

    Two gates were built as two shell steps — capture, then compare — because
    the driver task that wrote them was straddling a commit.  Nothing about
    **these** two needs two commits: both sides are the same code at the same
    commit, so the gate makes its runs itself and the button really is one
    button (protocol §15: no stage exists only as a shell invocation).  The
    capture resumes, so a complete record of the same job is kept rather than
    re-made; that is not a retry, and ``pool.run`` checks the job matches
    before it keeps anything.

    Gate G1 is deliberately **not** wrapped this way: its two sides are at
    different commits by construction, and a gate that made its own "before"
    would be comparing the tree with itself.
    """
    manifest = capture(campaign, resume=resume)
    outcome = body(campaign)
    outcome["capture"] = {
        "n_runs": manifest.get("n_runs"),
        "manifest": manifest.get("manifest"),
        "tree_git_head": manifest.get("tree_git_head"),
    }
    return outcome


# --------------------------------------------------------------------------
# gate GR, wrapped into the framework
# --------------------------------------------------------------------------
#
# GR is implemented in ``harness/reproduction.py`` and was reachable only from
# ``experiment_runner.py --gate reproduction``.  It is registered here so that
# ``registry`` really is *every* gate, and so that ``--gate all`` runs it with
# the rest.  The criterion is not restated: the body calls the same stage, and
# the teeth read the same seven results out of its verdict.

#: GR's own deliberate breaks, by the names ``reproduction.teeth`` records them
#: under.  Declared here rather than counted, so that a tooth the gate stops
#: running is a tooth that DID NOT TRIP rather than one fewer tooth.
REPRODUCTION_TEETH: tuple[str, ...] = (
    "count",
    "hex",
    # The one tooth here that must **not** end in a refusal: a reference value
    # the gate no longer compares, doctored, has to be reported as excluded by
    # name — neither as a mismatch (the exclusion would not be in force) nor as
    # a match (a doctored value would have passed).
    "excluded field",
    "missing reference",
    "missing key",
    "bad name map",
    "composition",
    "attempt summation",
)

_REPRODUCTION_HELD: dict[str, Any] = {}

#: Where GR's runs and verdict go when the gate is run from the registry.  It
#: is settable so that ``--outdir`` redirects the gate, which it did not before
#: (task A57 (driver-output-path) recorded the quirk: ``--gate reproduction``
#: wrote to the campaign's records directory whatever ``--outdir`` said).
REPRODUCTION_ROOT: dict[str, Any] = {"root": None}

#: Where the lifted input files are staged from, for GR.  Also settable, for
#: the same reason: the gate needs them and the runner has the flag.
REPRODUCTION_LIFTED_FROM: dict[str, Any] = {"path": None}

def _reproduction_body(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    from . import reproduction as reproduction_mod

    code, verdict = reproduction_mod.stage(
        campaign=campaign,
        root=REPRODUCTION_ROOT["root"],
        resume=resume,
        lifted_from=REPRODUCTION_LIFTED_FROM["path"],
    )
    _REPRODUCTION_HELD["verdict"] = verdict
    comparison = verdict.get("comparison") or {}
    # The gate writes its verdict to the same path the stage writes its own, so
    # the stage's whole verdict is carried inside this one rather than
    # overwritten: a reader who opens the file must find everything, not the
    # framework's summary where the detail used to be.
    return {
        "passed": code == 0,
        "criterion": (
            "twenty runs against the previous revision's committed numbers, "
            "every compared value exact — counts and hex floats, no tolerance"
        ),
        "population": comparison.get("population")
        or f"{verdict.get('n_planned')} reference runs",
        "n_compared": comparison.get("n_values_compared"),
        "n_mismatched": comparison.get("n_values_mismatched"),
        "n_runs": comparison.get("n_runs"),
        "n_runs_reproduced": comparison.get("n_runs_reproduced"),
        "refused": verdict.get("refused"),
        "coverage_boundary": verdict.get("coverage_boundary"),
        "substitutes": {
            name: block.get("passed")
            for name, block in (verdict.get("substitutes") or {}).items()
        },
        "record_contract_passed": (verdict.get("record_contract") or {}).get("passed"),
        "reproduction": verdict,
    }


def _reproduction_teeth() -> tuple[Tooth, ...]:
    def read(name: str):
        def look() -> tuple[bool, str]:
            verdict = _REPRODUCTION_HELD.get("verdict")
            if verdict is None:
                return False, "the gate did not run, so its teeth never ran"
            for entry in (verdict.get("teeth") or {}).get("teeth", []):
                if entry["tooth"] == name:
                    return bool(entry["caught"]), str(entry["what"])
            return False, (
                f"gate GR ran no tooth named {name!r}; a declared tooth the "
                f"gate no longer exercises is a tooth that did not trip"
            )

        return look

    return tuple(
        Tooth(
            name=name,
            what="gate GR's own deliberate break, by name",
            must=(
                "FAIL, REFUSE or RAISE — never skip; the 'excluded field' "
                "tooth instead requires the doctored value to be reported as "
                "excluded by name"
            ),
            check=read(name),
        )
        for name in REPRODUCTION_TEETH
    )


# --------------------------------------------------------------------------
# the harness's own checks, promoted
# --------------------------------------------------------------------------
#
# Six self-checks and four artifact stages existed before this framework did,
# each already carrying what a gate carries: what it binds, a population, a
# denominator, a mismatch count and its own teeth.  They are promoted rather
# than rewritten -- ``framework.gate_from_check`` runs the *same function* and
# adds the verdict record, the registry entry and a declared tooth list.  The
# numbers a promoted gate reports are the numbers the check reported; that is
# the point of promoting instead of restating.


def _selfcheck_gates(campaign: Campaign) -> dict[str, Gate]:
    """The six self-checks, each with the teeth it must run.

    The retired-name family is **derived** from the switch registry rather than
    listed, because the check generates one tooth per retired name from that
    same registry: a hand-copied list would drift the moment a name is retired.
    """
    from . import selfcheck as selfcheck_mod
    from . import switches as switches_mod

    retired = tuple(
        f"the retired name {name} present in the environment"
        for name in sorted(switches_mod.retired_names())
    )
    declared: dict[str, tuple[str, ...]] = {
        "composition": (
            "a role both revisions can express treated as a new capability",
            "wrong switch value in one arm",
            "one switch dropped from an arm",
            "the wrong per-run artifact handed to an arm",
            "the fold read as a difference",
            "a schedule policy the fold does not cover",
            "a skipped arm asked to compose",
        ),
        "rungs": (
            "a wrong expected difference in the rung table",
            "a wrong cell in the transcribed matrix",
            "an arm compared with itself",
        ),
        "capability": (
            "an arm asks for a switch the tree does not implement",
            "the driver resolves a switch differently from what was asked",
            *retired,
            "the driver's own refusal of a retired name",
            "the working directory holds a package that shadows the tree",
        ),
        "provenance": (
            "a tracked file modified",
            "an untracked file beside the runner",
            "a campaign pointed at a tree that is not the experiment's copy",
            "the tree asserted by a prefix instead of exactly",
        ),
        "data": (
            "one byte changed in a copied file",
            "a copied file missing",
            "a file added that the record does not name",
            "a changed file whose recorded sha256 was updated to match",
            "an unrecorded edit to the predicate module",
            "an edited predicate module whose recorded sha256 was updated to match",
        ),
        "run_path": (
            "a declared field removed",
            "an exit audit carrying one convergence ruler and not both",
            "a record that does not say what kind of run made it",
            "per-attempt costs that do not sum to the run total",
            "per-attempt costs stamped at some attempts and not others",
            "the design-vector stream keyed on position instead of number",
            "the two streams sharing a namespace",
            "a run against a tree that is not the experiment's copy",
            "a run asking for a switch the tree does not implement",
            "an allowance naming a switch the tree does implement",
            "a campaign run carrying the reproduction gate's override",
            "a reproduction override that changes nothing",
        ),
    }
    # None of the six starts a PROCESS run through the pool -- the capability
    # check starts import-only probe children -- so ``resume`` reaches them and
    # has nothing to do, which is why each signature swallows it.
    bodies: dict[str, Any] = {
        "composition": lambda *, resume=False: selfcheck_mod.check_composition(campaign),
        "rungs": lambda *, resume=False: selfcheck_mod.check_rungs(),
        "capability": lambda *, resume=False: selfcheck_mod.check_capability(campaign),
        "provenance": lambda *, resume=False: selfcheck_mod.check_provenance(campaign),
        "data": lambda *, resume=False: selfcheck_mod.check_data(campaign),
        "run_path": lambda *, resume=False: selfcheck_mod.check_run_path(campaign),
    }
    proves = {
        "composition": (
            "every arm composes on every configuration, a skipped arm refuses "
            "by name, and the arms the previous revision also ran ask the "
            "driver for the same thing"
        ),
        "rungs": (
            "the plan's switch matrix and rung table regenerate cell for cell "
            "from the arm records"
        ),
        "capability": (
            "the tree resolves every switch each arm asks for, exactly as "
            "asked, and refuses a retired name rather than ignoring it"
        ),
        "provenance": (
            "a modified tracked file and an untracked file are recorded "
            "separately, and only the first marks the tree dirty"
        ),
        "data": (
            "every committed file the experiment reads is byte-identical to "
            "its source at the recorded commit, and the predicate module "
            "differs from its source by exactly the recorded hunks"
        ),
        "run_path": (
            "a finished record carries every field it declares, both rulers "
            "included; the two displacement streams key on what they say they "
            "key on; and a run against the wrong tree is refused, not made"
        ),
    }
    return {
        name: framework.gate_from_check(
            name=name,
            binds="the harness itself, before any PROCESS run",
            what_it_proves=proves[name],
            run=bodies[name],
            teeth=declared[name],
            needs_runs=False,
        )
        for name in declared
    }


#: The four artifact stages, each promoted with **its own** teeth.  The stage
#: and its teeth are two functions in the artifact modules, so the promotion
#: runs both: the criterion is the stage, unchanged, and the teeth are the
#: stage's own deliberate breaks, declared by name here.
ARTIFACT_GATE_TEETH: dict[str, tuple[str, ...]] = {
    "artifacts_check": (
        "a corrupted components digest",
        "an artifact with no harvest identity",
        "a deferral set derived for a different figure of merit",
    ),
    "artifacts_derive_inputs": (
        "one byte changed in a derived file",
        "no measurement behind the third line: a baseline evaluation that crashed",
        "no measurement behind the third line: a record carrying no settled burn time",
        "the burn-time constraint appended at the end of the file",
    ),
    "artifacts_census": (
        "one node's write removed from the census",
        "a node writing a field the committed census does not have",
    ),
    "artifacts_per_run": (
        "a node removed from the committed set",
        "a node added to the committed set",
    ),
}

#: Which entry the census stages are taken at when they run from the registry.
#: ``evaluation`` is one design point and costs seconds; ``optimisation`` is the
#: population the committed census was measured over.  Settable so that the
#: runner's ``--census-entry`` reaches the promoted gates too.
CENSUS_ENTRY: dict[str, str] = {"entry": "evaluation"}


def _artifact_gates(campaign: Campaign) -> dict[str, Gate]:
    from . import artifacts as artifacts_mod
    from . import census as census_mod
    from . import input_files as input_files_mod
    from . import postsolve as postsolve_mod

    def promote(
        name: str,
        *,
        binds: str,
        proves: str,
        stage,
        stage_teeth,
        needs_runs: bool,
    ) -> Gate:
        def run(*, resume: bool = False) -> Check:
            _code, record = stage(resume)
            check = Check(
                name=name,
                binds=binds,
                passed=record.get("verdict") == "PASS",
                population=record.get("population", ""),
                n_compared=record.get("n_compared", 0),
                n_mismatched=record.get("n_mismatched", 0),
                detail=list(record.get("detail") or ()),
            )
            tooth_code, tooth_record = stage_teeth()
            check.teeth = list(tooth_record.get("teeth") or ())
            if tooth_code != 0:
                check.note(
                    "the stage's teeth stage returned a non-zero code; the "
                    "teeth below say which break was not caught"
                )
            return check

        return framework.gate_from_check(
            name=name,
            binds=binds,
            what_it_proves=proves,
            run=run,
            teeth=ARTIFACT_GATE_TEETH[name],
            needs_runs=needs_runs,
        )

    return {
        "artifacts_check": promote(
            "artifacts_check",
            binds="every committed artifact of every configuration",
            proves=(
                "each artifact's own stamps rebuild and agree with the files "
                "they must agree with, so an artifact built for a different "
                "configuration or component set is refused by name"
            ),
            stage=lambda resume: artifacts_mod.check(campaign),
            stage_teeth=lambda: artifacts_mod.stage_teeth(campaign),
            needs_runs=False,
        ),
        "artifacts_derive_inputs": promote(
            "artifacts_derive_inputs",
            binds="the lifted input file of each pulsed configuration",
            proves=(
                "the three-line derivation reproduces the recorded bytes, and "
                "a derivation with no measurement behind its third line "
                "refuses rather than falling back on a default"
            ),
            stage=lambda resume: input_files_mod.stage_derive(campaign, resume=resume),
            stage_teeth=lambda: input_files_mod.stage_teeth(campaign),
            needs_runs=True,
        ),
        "artifacts_census": promote(
            "artifacts_census",
            binds="the committed run-time write census, per configuration",
            proves=(
                "what the models write at run time is what the committed "
                "census says they write, node by node and field by field"
            ),
            stage=lambda resume: census_mod.stage(
                campaign, entry=CENSUS_ENTRY["entry"], resume=resume
            ),
            stage_teeth=lambda: census_mod.stage_teeth(campaign),
            needs_runs=True,
        ),
        "artifacts_per_run": promote(
            "artifacts_per_run",
            binds="each configuration's per-run deferral set",
            proves=(
                "the class-level classifier re-derives every committed "
                "deferral set from a source scan of the tree under test, node "
                "for node and in the same order"
            ),
            stage=lambda resume: postsolve_mod.stage(
                campaign, census_entry=CENSUS_ENTRY["entry"], resume=resume
            ),
            stage_teeth=lambda: postsolve_mod.stage_teeth(campaign),
            # It takes a write census of its own, so it starts PROCESS.
            needs_runs=True,
        ),
    }




# --------------------------------------------------------------------------
# the exclusion sets, reviewed
# --------------------------------------------------------------------------
#
# Three gates compare two records value by value and each names the leaves it
# does not compare.  A named exclusion is the right shape — a zero over a
# population quietly smaller than the one stated is this project's trap T11 —
# but a list of names that only ever grows is the same failure a step later, so
# task **A52 (harness-gates)** was asked to review all three as one thing rather
# than extend them.
#
# The review is a *measurement*, not an opinion.  For every excluded name it
# reads the gate's own captured records and reports how many leaves the name
# covers on each side, whether both sides carry them, and whether they are
# equal — so "could this be compared instead?" is answered from the records.
#
# What the measurement cannot answer on its own is **why** a name is equal here.
# `tree_git_head` is equal whenever the two captures happen to be at one commit
# and differs the moment they are not; that is a property of the run, not of the
# field.  So each name also carries a declared *kind*, and the two together are
# what the verdict rests on: a structural kind stays excluded however equal it
# reads today, and a "field a change adds" is excluded only where one side
# actually lacks it.

#: Why each always-excluded name can never be compared.  Every name in
#: :data:`ALWAYS_EXCLUDED` must appear here — a name with no declared kind
#: raises at import, because an exclusion nobody classified is an exclusion
#: nobody reviewed.
ALWAYS_EXCLUDED_KIND: dict[str, str] = {
    "outdir": "a path",
    "campaign_input_file": "a path",
    "entry_state": "a path",
    "exit_audit.coupling_state": "a path",
    "exit_audit.restricted.artifact": "a path",
    "exit_audit.restricted.census": "a path",
    "per_run_artifact": "a path",
    "process_copy_provenance.path": "a path",
    "coupling_state_artifact": "a path",
    "coupling_state_provenance.path": "a path",
    "exit_audit.frozen.restricted.artifact": "a path",
    "exit_audit.frozen.restricted.census": "a path",
    "exit_audit.mixed.restricted.artifact": "a path",
    "exit_audit.mixed.restricted.census": "a path",
    "tree_git_branch": "the commit, or the working tree's state",
    "pythonpath": "a path",
    "tree": "a path",
    "repository": "a path",
    "process_file": "a path",
    "wall_s": "a timing or the machine's state",
    "cpu_user_s": "a timing or the machine's state",
    "cpu_sys_s": "a timing or the machine's state",
    "cpu_s": "a timing or the machine's state",
    "maxrss_kb": "a timing or the machine's state",
    "loadavg": "a timing or the machine's state",
    "mfile.process_runtime": "a timing or the machine's state",
    "tree_git_head": "the commit, or the working tree's state",
    "tree_git_describe": "the commit, or the working tree's state",
    "tree_modified_tracked": "the commit, or the working tree's state",
    "tree_untracked_paths": "the commit, or the working tree's state",
    "tree_modified_tracked_n": "the commit, or the working tree's state",
    "tree_untracked_paths_n": "the commit, or the working tree's state",
    "tree_git_dirty": "the commit, or the working tree's state",
    "process_copy_provenance.copy_date": "the commit, or the working tree's state",
    "env_architecture": "the switch vocabulary the change renames",
    "resolved_switches": "the switch vocabulary the change renames",
}

#: The kinds of thing gate G8's set excludes.  Its two sides are the **same
#: code at the same commit** run twice with one setting changed, so almost
#: nothing is licensed to differ and the set is small for that reason.
PREDICATE_PAIR_KIND: dict[str, str] = {
    "outdir": "a path",
    "wall_s": "a timing or the machine's state",
    "cpu_user_s": "a timing or the machine's state",
    "cpu_sys_s": "a timing or the machine's state",
    "cpu_s": "a timing or the machine's state",
    "maxrss_kb": "a timing or the machine's state",
    "loadavg": "a timing or the machine's state",
    "mfile.process_runtime": "a timing or the machine's state",
    "tree_untracked_paths": "the commit, or the working tree's state",
    "tree_untracked_paths_n": "the commit, or the working tree's state",
    "campaign_predicate_mode": "the setting being varied, or a stamp of it",
    "switches_asked.predicate_mode": "the setting being varied, or a stamp of it",
    "env_architecture.env_PROCESS_ARCH_PREDICATE": (
        "the setting being varied, or a stamp of it"
    ),
    "resolved_switches.process.core.solver.module_solve.PREDICATE_MODE": (
        "the setting being varied, or a stamp of it"
    ),
    "coupling_state_provenance.predicate_mode": (
        "the setting being varied, or a stamp of it"
    ),
    "exit_audit.predicate_mode": "the setting being varied, or a stamp of it",
    "exit_audit.rulers_note": "prose, identical on both sides",
}


def _assert_every_name_is_classified() -> None:
    missing = sorted(set(ALWAYS_EXCLUDED) - set(ALWAYS_EXCLUDED_KIND))
    if missing:
        raise GateError(
            f"{len(missing)} always-excluded name(s) carry no declared kind: "
            f"{missing}.  An exclusion nobody classified is an exclusion "
            f"nobody reviewed."
        )
    spare = sorted(set(ALWAYS_EXCLUDED_KIND) - set(ALWAYS_EXCLUDED))
    if spare:
        raise GateError(
            f"{len(spare)} classified name(s) are not excluded at all: {spare}"
        )
    missing = sorted(set(PREDICATE_PAIR_EXCLUSIONS) - set(PREDICATE_PAIR_KIND))
    if missing:
        raise GateError(
            f"{len(missing)} of gate G8's excluded name(s) carry no declared "
            f"kind: {missing}"
        )
    missing = sorted(
        set(FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE) - set(INSTRUMENT_CHANGE_KIND)
    )
    if missing:
        raise GateError(
            f"{len(missing)} name(s) excluded across an instrument change "
            f"carry no declared kind: {missing}"
        )
    spare = sorted(
        set(INSTRUMENT_CHANGE_KIND) - set(FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE)
    )
    if spare:
        raise GateError(
            f"{len(spare)} classified name(s) are not excluded at all: {spare}"
        )


_assert_every_name_is_classified()


def _coverage(
    name: str,
    pairs: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]],
    *,
    also_excluded: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """How many leaves *name* covers on each side, and whether they agree.

    ``also_excluded`` names leaves another exclusion already covers, so that a
    conditional name is not credited with leaves a structural one takes out
    anyway — the two absolute paths inside the restricted statistic are the live
    case, and counting them here would overstate what this review put back into
    the comparison by twelve.
    """
    table = {name: "under review"}
    on_a = on_b = both = equal = 0
    for before, after in pairs:
        a, b = leaves(dict(before)), leaves(dict(after))
        for path in sorted(set(a) | set(b)):
            if is_volatile(path, table) is None:
                continue
            if also_excluded and is_volatile(path, also_excluded) is not None:
                continue
            in_a, in_b = path in a, path in b
            on_a += int(in_a)
            on_b += int(in_b)
            if in_a and in_b:
                both += 1
                va, vb = a[path], b[path]
                if _same(va, vb) and (va is None) == (vb is None):
                    equal += 1
    return {
        "leaves_before": on_a,
        "leaves_after": on_b,
        "leaves_on_both_sides": both,
        "leaves_equal_where_both_sides_have_them": equal,
        "present_on_both_sides_everywhere": both == on_a == on_b and both > 0,
        "equal_everywhere_it_is_present": both > 0 and equal == both,
    }


def _neutrality_pairs(campaign: Campaign) -> list[tuple[dict, dict]]:
    pairs: list[tuple[dict, dict]] = []
    for phase, arm in NEUTRAL_ARMS:
        for config in campaign.configurations:
            key = f"{arm}/{config.name}"
            before_dir = neutrality_run_dir(campaign, "before", config.name, arm)
            after_dir = neutrality_run_dir(campaign, "after", config.name, arm)
            if not (before_dir / "metrics.json").exists():
                continue
            if not (after_dir / "metrics.json").exists():
                continue
            pairs.append(
                (
                    _read_record(before_dir, side="before", key=key),
                    _read_record(after_dir, side="after", key=key),
                )
            )
    return pairs


def _predicate_pairs(campaign: Campaign) -> list[tuple[dict, dict]]:
    pairs: list[tuple[dict, dict]] = []
    for pair in predicate_mode_pairs(campaign):
        config, arm, seed = pair["config"], pair["arm"], pair["seed"]
        directories = [
            predicate_mode_run_dir(campaign, mode, config.name, arm, seed)
            for mode in campaign.predicate_modes
        ]
        if not all((d / "metrics.json").exists() for d in directories):
            continue
        pairs.append(
            tuple(
                _read_record(d, side=m, key=f"{arm}/{config.name}/seed{seed:03d}")
                for d, m in zip(directories, campaign.predicate_modes)
            )
        )
    return pairs


def exclusion_review(campaign: Campaign) -> dict[str, Any]:
    """Every exclusion of every comparing gate, classified and measured.

    Three tables, each a row per excluded name: what kind of thing it is, why
    it is excluded, how many leaves it covers on each side of the gate's own
    captured records, whether both sides carry them and whether they agree, and
    the verdict — kept, made conditional, or removed.
    """
    g1_pairs = _neutrality_pairs(campaign)
    g8_pairs = _predicate_pairs(campaign)
    # **Which pair of commits gate G1's captures straddle changes the answer**,
    # and a leaf count published without it is a number without its condition
    # (trap T11).  A name that is one-sided across a real straddle is excluded
    # there and compared in a self-comparison, so "how many leaves did making
    # these conditional put back?" has one answer per pairing.
    g1_straddle = _straddle(
        neutrality_root(campaign) / "before" / "manifest.json",
        neutrality_root(campaign) / "after" / "manifest.json",
    )

    g1_rows: list[dict[str, Any]] = []
    for name, reason in ALWAYS_EXCLUDED.items():
        coverage = _coverage(name, g1_pairs)
        g1_rows.append(
            {
                "name": name,
                "group": "always excluded",
                "kind": ALWAYS_EXCLUDED_KIND[name],
                "reason": reason,
                **coverage,
                "could_be_compared_instead": False,
                "verdict": (
                    "KEPT — the kind is structural: it reads equal here only "
                    "because these two captures happen to agree on it, and a "
                    "later pair would not"
                    if coverage["equal_everywhere_it_is_present"]
                    else "KEPT — it differs on the captures, as its reason says"
                ),
            }
        )
    for name, reason in FIELDS_ADDED_BY_A_DRIVER_CHANGE.items():
        coverage = _coverage(name, g1_pairs, also_excluded=ALWAYS_EXCLUDED)
        compared_here = coverage["present_on_both_sides_everywhere"]
        g1_rows.append(
            {
                "name": name,
                "group": "excluded only where one side lacks the field",
                "kind": "a field a change adds (null or absent before, a value after)",
                "reason": reason,
                **coverage,
                "could_be_compared_instead": compared_here,
                "verdict": (
                    "COMPARED at this commit — both sides carry it, so the "
                    "condition does not fire and the field is in the "
                    "comparison"
                    if compared_here
                    else (
                        "INERT at this commit — the name matches no leaf on "
                        "either side, so it excludes nothing.  It is kept "
                        "because the field it names appears exactly when a "
                        "driver stamps nothing at a boundary, which is the "
                        "case it exists for"
                        if coverage["leaves_before"] == 0
                        and coverage["leaves_after"] == 0
                        else "EXCLUDED at this commit — one side lacks the field"
                    )
                ),
            }
        )

    # Whether the pairing this review measures over actually straddles an
    # instrument change decides what the rows below mean, exactly as the
    # commit pairing does for the two groups above.  It is read off the
    # captured records, not assumed.
    instruments_differ = any(
        exit_audit_instrument(before) != exit_audit_instrument(after)
        for before, after in g1_pairs
    )
    for name, reason in FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE.items():
        coverage = _coverage(name, g1_pairs, also_excluded=ALWAYS_EXCLUDED)
        g1_rows.append(
            {
                "name": name,
                "group": (
                    "excluded only where the two records' exit-audit "
                    "instruments differ"
                ),
                "kind": INSTRUMENT_CHANGE_KIND[name],
                "reason": reason,
                **coverage,
                "could_be_compared_instead": not instruments_differ,
                "verdict": (
                    "EXCLUDED at this pairing — the two captures' exit audits "
                    "were taken by different instruments, so this leaf is a "
                    "measurement by two rulers and not a difference in "
                    "behaviour"
                    if instruments_differ
                    else (
                        "COMPARED at this pairing — both captures name the "
                        "same instrument, so the condition does not fire and "
                        "the leaf is in the comparison"
                        if coverage["leaves_on_both_sides"]
                        else "INERT at this pairing — the name matches no leaf "
                        "on either side"
                    )
                ),
            }
        )

    # Where the instrument exclusion's leaves actually are.  The group's whole
    # claim is that it takes out the audit's residual and the instrument's own
    # account of itself, and **nothing else** — so the leaves it removes are
    # counted by prefix rather than asserted to be where they should be.  A
    # leaf outside the exit audit and its stamp would mean the group is hiding
    # something it was not written for, and the count says so by name.
    instrument_leaves: dict[str, int] = {}
    for before, after in g1_pairs:
        result = compare_records(
            before,
            after,
            excluded=ALWAYS_EXCLUDED,
            conditional=FIELDS_ADDED_BY_A_DRIVER_CHANGE,
            instrument_changed=FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE,
        )
        for path in result["excluded_by_the_instrument_change"]:
            head = path.split("[")[0]
            prefix = (
                "exit_audit.instrument"
                if head.startswith("exit_audit.instrument")
                else "exit_audit."
                if head.startswith("exit_audit.")
                else head.split(".")[0]
            )
            instrument_leaves[prefix] = instrument_leaves.get(prefix, 0) + 1
    outside = {
        prefix: count
        for prefix, count in instrument_leaves.items()
        if not prefix.startswith("exit_audit")
        and prefix not in {"audit_snapshot", "audit_position_note"}
    }

    g8_rows: list[dict[str, Any]] = []
    for name, reason in PREDICATE_PAIR_EXCLUSIONS.items():
        coverage = _coverage(name, g8_pairs)
        kind = PREDICATE_PAIR_KIND[name]
        g8_rows.append(
            {
                "name": name,
                "group": "always excluded",
                "kind": kind,
                "reason": reason,
                **coverage,
                "could_be_compared_instead": False,
                "verdict": (
                    "KEPT — this gate's two sides differ in exactly this "
                    "setting, so a stamp of it must differ"
                    if kind.startswith("the setting")
                    else "KEPT — the kind is structural"
                ),
            }
        )

    g9_rows = [
        {
            "name": name,
            "group": "compared",
            "kind": "a field that describes the solve",
            "reason": (
                "compared against the reproduction gate's record for the same "
                "run: 'nothing changes on the arms that keep the loop' is a "
                "comparison, not an assertion"
            ),
            "verdict": "COMPARED",
        }
        for name in UNCHANGED_ON_REFERENCE_ARMS
    ] + [
        {
            "name": "exit_audit.residual_max_hex",
            "group": "deliberately absent from the compared list",
            "kind": "a field the same change moved for every arm",
            "reason": (
                "the audit position moved to the plan's declared position for "
                "every arm in the same change, so the residual is expected to "
                "differ and comparing it would test the audit rather than the "
                "output path"
            ),
            "could_be_compared_instead": False,
            "verdict": (
                "KEPT ABSENT — and the position itself is compared instead: "
                "every row checks that the audit was taken where the plan "
                "declares"
            ),
        }
    ]

    conditional_compared = sum(
        row["leaves_on_both_sides"]
        for row in g1_rows
        if row["group"].startswith("excluded only")
        and row["could_be_compared_instead"]
    )
    return {
        "what_this_is": (
            "every exclusion of every gate that compares two records, "
            "classified by kind and measured against that gate's own captured "
            "records"
        ),
        "caption": (
            "One row per excluded name. 'kind' is what sort of thing it is; "
            "'leaves before/after' is how many record leaves the name covers "
            "on each side of the gate's captured pairs, summed over every "
            "pair; 'equal where both have them' is how many of those agree. "
            "The verdict is what this review did with the name. Populations: "
            f"gate G1 over {len(g1_pairs)} run pair(s) which {g1_straddle['says']} "
            f"— the leaf counts below hold for that pairing and no other — "
            f"gate G8 over "
            f"{len(g8_pairs)} run pair(s); gate G9's list is a list of fields "
            "it compares, not of fields it excludes, and is shown for the same "
            "reason."
        ),
        "G1_pairing": g1_straddle,
        "G1_instrument_leaves_by_prefix": {
            "what": (
                "every record leaf the instrument-change group removed from "
                "gate G1's comparison, counted by where it sits.  The group's "
                "claim is that it takes out the audit's residual and the "
                "instrument's own account of itself and nothing else; this is "
                "the measurement of that claim rather than the assertion"
            ),
            "by_prefix": dict(sorted(instrument_leaves.items())),
            "n_leaves": sum(instrument_leaves.values()),
            "n_outside_the_audit_and_its_stamp": sum(outside.values()),
            "outside_the_audit_and_its_stamp": dict(sorted(outside.items())),
            "none_outside_the_audit_and_its_stamp": not outside,
        },
        "G1_instrument_pairing": {
            "instruments": sorted(
                {
                    str(exit_audit_instrument(record))
                    for pair in g1_pairs
                    for record in pair
                }
            ),
            "straddles_an_instrument_change": instruments_differ,
            "says": (
                "the two captures' exit audits were taken by different "
                "instruments, so the third group's names are excluded here "
                "and compared at any pairing where the stamps agree"
                if instruments_differ
                else "both captures name the same exit-audit instrument, so "
                "the third group excludes nothing here"
            ),
        },
        "sizes": {
            "G1_before_this_review": len(VOLATILE_RECORD_PATHS),
            "G1_after_this_review": len(ALWAYS_EXCLUDED),
            "G1_conditional": len(FIELDS_ADDED_BY_A_DRIVER_CHANGE),
            "G1_conditional_on_the_instrument": len(
                FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE
            ),
            "G1_output_file_keys": len(VOLATILE_MFILE_KEYS),
            "G8_before_this_review": len(PREDICATE_PAIR_EXCLUSIONS),
            "G8_after_this_review": len(PREDICATE_PAIR_EXCLUSIONS),
            "G9_fields_compared": len(UNCHANGED_ON_REFERENCE_ARMS),
            "G9_fields_deliberately_absent": 1,
        },
        "what_the_review_changed": (
            f"gate G1's set was {len(VOLATILE_RECORD_PATHS)} names, every one "
            f"excluded unconditionally.  {len(ALWAYS_EXCLUDED)} of them are "
            f"structural — a path, a timing, the machine's state, the commit, "
            f"or the switch vocabulary a rename changes — and stay excluded "
            f"however equal they read.  The other "
            f"{len(FIELDS_ADDED_BY_A_DRIVER_CHANGE)} were excluded because "
            f"**one particular pair of commits** straddled the change that "
            f"added the field; they are now excluded only where one side "
            f"actually lacks the field, and compared wherever both sides carry "
            f"it.  Over the pairing measured here — {g1_straddle['says']} — "
            f"that puts {conditional_compared} further leaves back into the "
            f"comparison, and the count is a property of the pairing, not of "
            f"the table.  Nothing was removed from the "
            f"table: a name that stops being needed is worth more visible than "
            f"deleted, and the condition is what makes it inert."
        ),
        "G1": {
            "gate": "switch_neutrality",
            "population": f"{len(g1_pairs)} run pair(s)",
            "rows": g1_rows,
        },
        "G8": {
            "gate": "predicate_mode",
            "population": f"{len(g8_pairs)} run pair(s)",
            "rows": g8_rows,
        },
        "G9": {
            "gate": "output_path",
            "population": "the fields compared against the reproduction gate",
            "rows": g9_rows,
        },
    }


def print_exclusion_review(block: Mapping[str, Any]) -> None:
    print(f"\n  {block['what_this_is']}")
    print(f"\n  {block['caption']}")
    print(f"\n  {block['what_the_review_changed']}\n")
    for key in ("G1", "G8", "G9"):
        table = block[key]
        print(f"\n  --- {key} ({table['gate']}) — {table['population']}")
        print(
            f"    {'name':<52} {'kind':<48} {'before':>7} {'after':>7} "
            f"{'equal':>7}  verdict"
        )
        for row in table["rows"]:
            print(
                f"    {row['name']:<52} {row['kind']:<48} "
                f"{str(row.get('leaves_before', '-')):>7} "
                f"{str(row.get('leaves_after', '-')):>7} "
                f"{str(row.get('leaves_equal_where_both_sides_have_them', '-')):>7}"
                f"  {row['verdict'].split(' — ')[0]}"
            )
    leaves = block.get("G1_instrument_leaves_by_prefix")
    if leaves:
        print(
            f"\n  instrument-change leaves, by prefix "
            f"({leaves['n_leaves']} in all; "
            f"{leaves['n_outside_the_audit_and_its_stamp']} outside the exit "
            f"audit and its stamp):"
        )
        for prefix, count in leaves["by_prefix"].items():
            print(f"    {prefix:<34} {count}")
    sizes = block["sizes"]
    print("\n  sizes:")
    for name, value in sizes.items():
        print(f"    {name:<34} {value}")




# --------------------------------------------------------------------------
# self-containment, measured rather than asserted
# --------------------------------------------------------------------------
#
# The user's binding requirement on this package (harness plan §6): **every
# verification gate V4 runs is implemented inside `harness/` — none is imported
# from `arch_surgery/idf_probe/` or `arch_surgery/fixedpoint/`, and none is
# invoked as a subprocess into them.**
#
# "grep finds no import" is a claim, and a claim about a package is worth what
# its measurement is worth, so this stage *is* the grep: it reads every Python
# file of the package and the runner beside it, finds every occurrence of either
# directory name, and classifies each one.  Anything it cannot classify is
# printed as a finding rather than passed over.
#
# One classification needs stating because it looks like a hit and is not.  The
# **driver's own** census probe is `process/core/_idf_probe*.py`, inside the
# copied PROCESS tree: same three letters, different thing entirely.  A name
# beginning with an underscore is that module; `arch_surgery/idf_probe` is the
# superseded task machinery.  The stage tells them apart by the underscore and
# says so, because a measurement that silently counted one as the other would be
# reporting the opposite of what it claims.

#: Lines of executable code that name one of the two directories and are
#: **allowed** to, each with what it is and why it cannot reach a measurement.
#: A line of code naming either directory that is not here is a finding.
DECLARED_OUTSIDE_REFERENCES: dict[str, str] = {
    "config.py": (
        "the preflight-only campaign's input directory.  "
        "`repository_tree_campaign()` points the preflight and the self-check "
        "at the repository's own tree and its committed input files, which is "
        "where the superseded revision kept them.  It answers 'does the "
        "harness still compose against the tree the earlier revisions "
        "measured?' and **no record is ever made against it**: "
        "`Campaign.is_experiment_copy` is False for it and `pool.run` refuses "
        "every run on that ground, with a tooth in the run-path check.  It is "
        "a path constant, not an import and not a subprocess"
    ),
    "data_provenance.py": (
        "the declared **source** of two committed files: where each came from "
        "when it was copied in.  It is read by the data check, which fetches "
        "the source from the recorded commit with `git cat-file` — the "
        "repository at a commit, never the live directory (trap T9: a sibling "
        "study's generated output read live catches a half-written state).  A "
        "provenance string, not an import and not a subprocess"
    ),
    "reference.py": (
        "the default root of the **previous revision's** untracked run "
        "records, under `MDA_partitioning_experiment_v3/runs` — not "
        "`idf_probe/` or `fixedpoint/` at all.  It is read by the reproduction "
        "reference's `extract` and `verify` stages only, never at run time, "
        "and what the gate compares against is the committed extract"
    ),
    "gates.py": (
        "this stage's own declaration: the two directory names it searches "
        "for, and the prose that explains each classification.  A measurement "
        "that looks for a string has to contain the string"
    ),
    "input_files.py": (
        "a sentence inside a **refusal message**, saying where the previous "
        "revision's derived input files were kept so that a reader knows what "
        "to point `--lifted-from` at.  Prose in a message; this package opens "
        "no such path"
    ),
    "ystate.py": (
        "a provenance stamp written **into** a generated artifact, naming the "
        "generator the artifact came from.  It is data written out, not a path "
        "read in"
    ),
    "selfcheck.py": (
        "the opt-in, labelled cross-check of the previous revision's "
        "composition — `--crosscheck-previous`, which executes that revision's "
        "own two composition functions in a subprocess and compares.  It names "
        "`MDA_partitioning_experiment_v3`, not `idf_probe/` or `fixedpoint/`; "
        "it is off by default, is not one of the package's gates, and exists "
        "so that the transcription in this package is *measured* rather than "
        "trusted"
    ),
}

#: The two directories the requirement names.
FORBIDDEN_DIRECTORIES: tuple[str, ...] = ("idf_probe", "fixedpoint")


def _docstring_and_comment_lines(source: str) -> set[int]:
    """Every line of *source* that is inside a docstring or a comment."""
    import io
    import tokenize

    lines: set[int] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        tree = None
    if tree is not None:
        for node in ast.walk(tree):
            if not isinstance(
                node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                continue
            body = getattr(node, "body", None)
            if not body:
                continue
            first = body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                if isinstance(first.value.value, str):
                    lines.update(range(first.lineno, (first.end_lineno or first.lineno) + 1))
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type == tokenize.COMMENT:
                lines.add(token.start[0])
            elif token.type == tokenize.STRING and "\n" in token.string:
                # a triple-quoted string used as prose anywhere else
                lines.update(range(token.start[0], token.end[0] + 1))
    except tokenize.TokenError:
        pass
    return lines


def self_containment(campaign: Campaign) -> dict[str, Any]:
    """Every mention of the two superseded directories, classified.

    The measurement behind the sentence *"grep finds no import of, and no
    subprocess into, `idf_probe/` or `fixedpoint/`"*.
    """
    here = Path(__file__).resolve().parent
    runner = here.parent / "experiment_runner.py"
    files = sorted(here.rglob("*.py")) + [runner]
    hits: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    imports: list[dict[str, Any]] = []
    for path in files:
        source = path.read_text()
        prose = _docstring_and_comment_lines(source)
        try:
            tree = ast.parse(source)
        except SyntaxError:
            tree = None
        if tree is not None:
            for node in ast.walk(tree):
                names: list[str] = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                for name in names:
                    if any(d in name for d in FORBIDDEN_DIRECTORIES):
                        imports.append(
                            {"file": path.name, "line": node.lineno, "imports": name}
                        )
        for number, line in enumerate(source.splitlines(), start=1):
            for directory in FORBIDDEN_DIRECTORIES:
                if directory not in line:
                    continue
                driver_probe = "_idf_probe" in line and "arch_surgery" not in line
                if driver_probe:
                    kind = (
                        "the driver's own census probe, process/core/"
                        "_idf_probe*.py inside the copied PROCESS tree — the "
                        "same three letters, a different module"
                    )
                    classified = True
                elif number in prose:
                    kind = "heritage: a docstring or comment naming the file this one derives from"
                    classified = True
                elif path.name in DECLARED_OUTSIDE_REFERENCES:
                    kind = DECLARED_OUTSIDE_REFERENCES[path.name]
                    classified = True
                else:
                    kind = "UNCLASSIFIED — a finding"
                    classified = False
                row = {
                    "file": str(path.relative_to(here.parent)),
                    "line": number,
                    "text": line.strip()[:140],
                    "directory": directory,
                    "classification": kind,
                    "executable": number not in prose,
                }
                hits.append(row)
                if not classified:
                    findings.append(row)
                break
    by_kind: dict[str, int] = {}
    for row in hits:
        key = row["classification"].split(" — ")[0].split(".")[0][:60]
        by_kind[key] = by_kind.get(key, 0) + 1
    return {
        "what_this_is": (
            "the measurement behind 'grep finds no import of, and no "
            "subprocess into, the superseded directories': every occurrence "
            "of either name in this package and the runner beside it, "
            "classified"
        ),
        "caption": (
            "One row per line naming one of the two directories. 'executable' "
            "is False where the line is inside a docstring or a comment. "
            f"Population: {len(files)} Python file(s) — every module of the "
            "package plus the runner. A row classified as a finding is one "
            "this stage could not account for."
        ),
        "n_files_scanned": len(files),
        "n_hits": len(hits),
        "n_in_prose": sum(1 for row in hits if not row["executable"]),
        "n_executable": sum(1 for row in hits if row["executable"]),
        "n_findings": len(findings),
        "n_imports_of_either_directory": len(imports),
        "imports": imports,
        "by_classification": by_kind,
        "findings": findings,
        "passed": not findings and not imports,
        "hits": hits,
    }


def print_self_containment(block: Mapping[str, Any]) -> None:
    print(f"\n  {block['what_this_is']}")
    print(f"\n  {block['caption']}\n")
    print(
        f"    files scanned                 {block['n_files_scanned']}\n"
        f"    lines naming either directory {block['n_hits']}\n"
        f"      of which inside prose       {block['n_in_prose']}\n"
        f"      of which executable code    {block['n_executable']}\n"
        f"    imports of either directory   {block['n_imports_of_either_directory']}\n"
        f"    unclassified (findings)       {block['n_findings']}"
    )
    print("\n    by classification:")
    for kind, count in sorted(block["by_classification"].items(), key=lambda kv: -kv[1]):
        print(f"      {count:>3}  {kind}")
    print("\n    every executable line, with what it is:")
    for row in block["hits"]:
        if not row["executable"]:
            continue
        print(f"      {row['file']}:{row['line']}  {row['text']}")
        print(f"          {row['classification'][:150]}")
    if block["findings"]:
        print("\n    FINDINGS:")
        for row in block["findings"]:
            print(f"      {row['file']}:{row['line']}  {row['text']}")


# --------------------------------------------------------------------------
# the tally: two measurement stages and one gate  (task A53 (harness-tally))
# --------------------------------------------------------------------------
#
# Kept as one contiguous block so that the registry's other entries and this
# one can be merged past each other without a conflict in the middle of a
# dictionary.  The two stages publish the experiment plan's section 4 tables
# and have nothing to pass; the gate is the set of things a table may not be,
# plus the previous revision's published cells.


def _tally_gates(campaign: Campaign) -> dict[str, Gate]:
    """The tally's own gate, with its ten teeth."""
    from harness import gate_tally as gate_tally_mod  # noqa: PLC0415

    return {"tally_contracts": gate_tally_mod.gate(campaign)}


def _tally_measurements(campaign: Campaign) -> dict[str, Measurement]:
    """The two tally stages: one per phase, each with nothing to pass."""
    from harness import tally_evaluation as tally_a_mod  # noqa: PLC0415
    from harness import tally_optimisation as tally_b_mod  # noqa: PLC0415

    return {
        "tally_evaluation": Measurement(
            name="tally_evaluation",
            reports=(
                "the evaluation phase's tables of the experiment plan's "
                "section 4.2 -- cost per call, matched accuracy on both "
                "rulers, the ownership rung, the per-sweep overhead and the "
                "failure taxonomy -- each with its caption, its denominator "
                "and the audit position it was measured at"
            ),
            guarded_by="tally_contracts",
            body=lambda *, resume=False: tally_a_mod.tally(campaign, resume=resume),
            printer=tally_a_mod.print_tally,
        ),
        "tally_optimisation": Measurement(
            name="tally_optimisation",
            reports=(
                "the optimisation phase's tables of the experiment plan's "
                "section 4.3 -- the one seed set and the failure table, the "
                "same-optimum check, check 2 in both iteration constructions, "
                "the attempt summation identity, the cost with and without "
                "the retried seeds, and the lift's residual"
            ),
            guarded_by="tally_contracts",
            body=lambda *, resume=False: tally_b_mod.tally(campaign, resume=resume),
            printer=tally_b_mod.print_tally,
        ),
    }


# --------------------------------------------------------------------------
# the measurement stages
# --------------------------------------------------------------------------


def measurements(campaign: Campaign) -> dict[str, Measurement]:
    """Every stage that publishes numbers and has nothing to pass.

    They are listed beside the gates because a reader looking for "what does
    this package run?" should find one answer, and they are a different type
    because a measurement has no verdict and must never be read as one.
    """
    return {
        "predicate_counters": Measurement(
            name="predicate_counters",
            reports=(
                "what each arm's convergence test cost — evaluations and "
                "components compared — with the empty block visits and the "
                "sweeps they cost beside it (plan §3.5 check 5)"
            ),
            guarded_by="switch_neutrality",
            body=lambda *, resume=False: predicate_counter_measurements(campaign),
            printer=print_predicate_counters,
        ),
        "attempts": Measurement(
            name="attempts",
            reports=(
                "what each attempt of the optimiser's retry ladder cost, with "
                "check 2's two iteration constructions beside it (plan §3.5, "
                "retries)"
            ),
            guarded_by="reproduction",
            body=lambda *, resume=False: attempt_measurements(campaign),
            printer=print_attempts,
        ),
        "gate_table": Measurement(
            name="gate_table",
            reports=(
                "the experiment plan §4.1's gate table, filled in from the "
                "verdict records: one row per registered gate with its "
                "population, its denominator, its mismatches and its teeth"
            ),
            guarded_by="each gate is its own guard; this reads what they wrote",
            body=lambda *, resume=False: gate_table(campaign),
            printer=print_gate_table,
        ),
        "self_containment": Measurement(
            name="self_containment",
            reports=(
                "every mention of the two superseded directories in this "
                "package and the runner beside it, classified — the "
                "measurement behind 'nothing is imported from, and nothing is "
                "invoked as a subprocess into, idf_probe/ or fixedpoint/'"
            ),
            guarded_by="the user's requirement in the harness plan §6",
            body=lambda *, resume=False: self_containment(campaign),
            printer=print_self_containment,
        ),
        "exclusion_review": Measurement(
            name="exclusion_review",
            reports=(
                "every exclusion of every gate that compares two records, "
                "classified by kind and measured against that gate's own "
                "captured records: how many leaves each name covers on each "
                "side, whether both sides carry them, and what this review "
                "did with the name"
            ),
            guarded_by="switch_neutrality",
            body=lambda *, resume=False: exclusion_review(campaign),
            printer=print_exclusion_review,
        ),
        "output_path_measurements": Measurement(
            name="output_path_measurements",
            reports=(
                "what the output-time loop moves in the output files, what it "
                "costs, and where the accepted state sits against the "
                "tolerance at the declared audit position"
            ),
            guarded_by="output_path",
            body=lambda *, resume=False: _with_capture(
                capture_contrast, output_path_measurements, campaign, resume=resume
            ),
            printer=print_measurements,
        ),
        **_tally_measurements(campaign),
    }


# --------------------------------------------------------------------------
# the registry
# --------------------------------------------------------------------------


def registry(campaign: Campaign) -> dict[str, Any]:
    """**Every** gate and every measurement stage this package runs, by name.

    Three groups, in one dictionary because a reader should not have to know
    which group a name is in to look it up:

    * the experiment plan's §3.9 gates — ``GR``, ``G0``/``G0'``, ``G1``–``G9``
      — each carrying the plan's own label in ``plan_name``;
    * the harness's own checks, promoted: the six self-checks and the four
      artifact stages, with their criteria unchanged;
    * the measurement stages, which have no verdict and are a different type so
      that nothing can read one as a gate.

    Every entry has ``.run(records_dir=…)`` and writes its record under
    ``runs/gates/<name>/``.
    """
    entries: dict[str, Any] = {}
    entries.update(_plan_gates(campaign))
    entries.update(_selfcheck_gates(campaign))
    entries.update(_artifact_gates(campaign))
    entries.update(_tally_gates(campaign))
    entries.update(measurements(campaign))
    return entries


# --------------------------------------------------------------------------
# the gate table the experiment plan's §4.1 asks for
# --------------------------------------------------------------------------
#
# The plan carries a placeholder table — one row per gate, with its verdict, its
# tooth and its record — and says that no number in the results section is cited
# unless every row is PASS with its tooth tripped.  This stage fills it in from
# the verdict records themselves, so the table in the report and the files on
# disk cannot drift apart: there is no hand-copied cell in it.
#
# It is a measurement and not a gate.  It has nothing to pass: what passes is
# each gate, and this reads what they wrote.


#: The pairs of (compared, differing) fields a gate's verdict can carry.  A gate
#: whose criterion is a count of compared values writes one of these pairs;
#: three of them write more than one, because they compare more than one kind of
#: thing — coupling-state components, record values, output-file lines — and a
#: denominator that silently added them together without saying which is which
#: would be a count over a population nobody can state.  The table sums them and
#: names the pairs it summed.
COUNT_FIELDS: tuple[tuple[str, str], ...] = (
    ("n_compared", "n_mismatched"),
    ("n_values_compared", "n_values_differing"),
    ("n_components_compared", "n_components_differing"),
    ("n_reference_values_compared", "n_reference_values_differing"),
    ("n_mfile_lines_compared", "n_mfile_lines_differing"),
)


def _counts(verdict: Mapping[str, Any]) -> tuple[int | None, int | None, list[str]]:
    compared = differing = None
    named: list[str] = []
    for compared_field, differing_field in COUNT_FIELDS:
        value = verdict.get(compared_field)
        if not isinstance(value, int):
            continue
        compared = (compared or 0) + value
        differing = (differing or 0) + int(verdict.get(differing_field) or 0)
        named.append(f"{compared_field} = {value}")
    return compared, differing, named


def gate_table(campaign: Campaign, records_dir: Path | None = None) -> dict[str, Any]:
    """Every gate's verdict record, as the plan's §4.1 table."""
    root = Path(records_dir or (Path(campaign.runs_dir) / GATES_SUBPATH))
    entries = registry(campaign)
    rows: list[dict[str, Any]] = []
    for name in ordered_gate_names(campaign):
        gate = entries[name]
        path = root / name / "gate.json"
        if not path.exists():
            rows.append(
                {
                    "gate": name,
                    "plan_name": gate.plan_name,
                    "binds": gate.binds,
                    "verdict": "NOT RUN",
                    "population": "—",
                    "n_compared": None,
                    "n_mismatched": None,
                    "n_teeth": len(gate.teeth),
                    "n_teeth_tripped": None,
                    "record": str(path),
                }
            )
            continue
        verdict = json.loads(path.read_text())
        teeth = verdict.get("teeth") or []
        compared, differing, named = _counts(verdict)
        rows.append(
            {
                "gate": name,
                "plan_name": gate.plan_name,
                "binds": gate.binds,
                "verdict": verdict.get("verdict"),
                "population": verdict.get("population") or "—",
                "n_compared": compared,
                "n_mismatched": differing,
                "denominators_summed": named,
                "n_teeth": len(teeth),
                "n_teeth_tripped": sum(1 for t in teeth if t.get("caught")),
                "teeth": [t.get("tooth") for t in teeth],
                "generated": verdict.get("generated"),
                "tree_git_head": verdict.get("tree_git_head"),
                "record": str(path.relative_to(Path(campaign.runs_dir).parent)),
            }
        )
    plan_rows = [row for row in rows if row["plan_name"]]
    harness_rows = [row for row in rows if not row["plan_name"]]
    return {
        "what_this_is": (
            "the experiment plan §4.1's gate table, filled in from the verdict "
            "records rather than by hand"
        ),
        "caption": (
            "One row per registered gate. 'plan' is the label the experiment "
            "plan's §3.9 table uses, empty where the gate is one of the "
            "harness's own checks rather than one of the plan's. 'verdict' is "
            "PASS/FAIL on the gate's criterion **and** on every tooth "
            "tripping. 'population' is what the gate compared, in its own "
            "words; 'compared' is the denominator and 'mismatched' the count "
            "of things that differed — both are the gate's own headline pair, "
            "and a gate whose criterion is not a count of compared values "
            "leaves them empty and states its population in words instead. "
            "Where a gate compares more than one kind of thing — coupling-state "
            "components, record values, output-file lines — the denominator is "
            "their sum and the row's 'denominators summed' names each. "
            "'teeth' is tripped / declared. A gate whose tooth did not trip is "
            "not accepted whatever its verdict. One row reads 1 mismatched and "
            "PASS: the frozen-physics gate counts the single model file the "
            "user approved as differing, by name, and passes because it is the "
            "approved one."
        ),
        "population": (
            f"{len(rows)} registered gate(s): {len(plan_rows)} of the "
            f"experiment plan's §3.9 table and {len(harness_rows)} of the "
            f"harness's own checks, promoted"
        ),
        "n_gates": len(rows),
        "n_pass": sum(1 for row in rows if row["verdict"] == "PASS"),
        "n_fail": sum(1 for row in rows if row["verdict"] not in ("PASS", "NOT RUN")),
        "n_not_run": sum(1 for row in rows if row["verdict"] == "NOT RUN"),
        "n_teeth": sum(row["n_teeth"] for row in rows),
        "n_teeth_tripped": sum(row["n_teeth_tripped"] or 0 for row in rows),
        "rows": rows,
        "markdown": _gate_table_markdown(rows),
    }


def _gate_table_markdown(rows: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        "| gate | plan | binds | verdict | population | compared | mismatched "
        "| teeth | record |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        teeth = (
            f"{row['n_teeth_tripped']}/{row['n_teeth']}"
            if row["n_teeth_tripped"] is not None
            else f"—/{row['n_teeth']}"
        )
        population = str(row["population"]).replace("|", "/")
        if len(population) > 150:
            population = population[:147] + "…"
        lines.append(
            f"| `{row['gate']}` | {row['plan_name'] or '—'} | "
            f"{str(row['binds'])[:90]} | **{row['verdict']}** | {population} | "
            f"{row['n_compared'] if row['n_compared'] is not None else '—'} | "
            f"{row['n_mismatched'] if row['n_mismatched'] is not None else '—'} | "
            f"{teeth} | `{row['record']}` |"
        )
    return "\n".join(lines)


def print_gate_table(block: Mapping[str, Any]) -> None:
    print(f"\n  {block['what_this_is']}")
    print(f"\n  {block['caption']}\n")
    print(f"  population: {block['population']}\n")
    print(
        f"    {'gate':<24} {'plan':<10} {'verdict':<8} {'compared':>9} "
        f"{'mismatch':>9}  teeth"
    )
    for row in block["rows"]:
        teeth = (
            f"{row['n_teeth_tripped']}/{row['n_teeth']}"
            if row["n_teeth_tripped"] is not None
            else f"—/{row['n_teeth']}"
        )
        print(
            f"    {row['gate']:<24} {str(row['plan_name'] or '—'):<10} "
            f"{str(row['verdict']):<8} "
            f"{str(row['n_compared'] if row['n_compared'] is not None else '—'):>9} "
            f"{str(row['n_mismatched'] if row['n_mismatched'] is not None else '—'):>9}"
            f"  {teeth}"
        )
    print(
        f"\n    {block['n_pass']} PASS, {block['n_fail']} FAIL, "
        f"{block['n_not_run']} not run; "
        f"{block['n_teeth_tripped']} of {block['n_teeth']} teeth tripped"
    )
    print("\n  as markdown:\n")
    print(block["markdown"])


def gates_only(campaign: Campaign) -> dict[str, Gate]:
    """The registry's gates: everything with a verdict."""
    return {
        name: entry
        for name, entry in registry(campaign).items()
        if isinstance(entry, Gate)
    }


#: The order ``--gate all`` runs in: cheapest first, so a repository-state
#: failure is reported in seconds rather than after an hour of runs.  A name
#: absent from this tuple still runs — it is appended in registry order — so a
#: gate added later cannot be silently left out of the button.
GATE_ORDER: tuple[str, ...] = (
    "g0prime",
    "composition",
    "rungs",
    "provenance",
    "data",
    "run_path",
    "capability",
    "artifacts_check",
    "artifacts_derive_inputs",
    "artifacts_census",
    "artifacts_per_run",
    "record_completeness",
    "prime_map",
    "cold_chain",
    "audit_restriction",
    "entry_and_warm",
    "switch_composition",
    "output_path",
    "predicate_mode",
    "switch_neutrality",
    "reproduction",
    "tally_contracts",
)


def ordered_gate_names(campaign: Campaign) -> list[str]:
    """Every gate's name, cheapest first **and after what it reads**.

    :data:`GATE_ORDER` is a *preference*: run the cheap repository-state checks
    before the hour of runs, so a failure is reported in seconds.  It is not a
    correctness order, and treating it as one was a defect the from-scratch run
    found: gate G9 reads the reproduction gate's own runs, and cheapest-first
    put the reproduction gate last, so on a tree with no runs at all G9 refused
    for want of records that were about to be made.  With everything resumed
    from an earlier session it had never surfaced.

    So the order is now *derived*: the preference decides between gates that do
    not depend on each other, and a declared ``reads_from`` decides when they
    do.  A dependency naming a gate that does not exist, or a cycle, raises —
    an order nobody can compute is not an order.
    """
    available = gates_only(campaign)
    preference = {name: i for i, name in enumerate(GATE_ORDER)}
    rank = sorted(available, key=lambda n: (preference.get(n, len(GATE_ORDER)), n))
    pending = {
        name: {
            dependency
            for dependency in available[name].reads_from
            if dependency in available
        }
        for name in rank
    }
    unknown = {
        name: sorted(set(available[name].reads_from) - set(available))
        for name in rank
        if set(available[name].reads_from) - set(available)
    }
    if unknown:
        raise GateError(
            f"gate(s) declare a dependency on something the registry does not "
            f"hold: {unknown}.  A gate that reads a gate nobody runs cannot be "
            f"ordered, and running it anyway would read whatever happened to "
            f"be on disk"
        )
    ordered: list[str] = []
    while pending:
        ready = [name for name in rank if name in pending and not pending[name]]
        if not ready:
            raise GateError(
                f"the declared reads-from dependencies are cyclic among "
                f"{sorted(pending)}; no order runs each gate after what it reads"
            )
        chosen = ready[0]
        ordered.append(chosen)
        del pending[chosen]
        for remaining in pending.values():
            remaining.discard(chosen)
    return ordered


def print_predicate_mode(verdict: Mapping[str, Any]) -> None:
    """G8's three parts, each with its population.

    Printed rather than left in the record because the gate's result is a
    *table*: the identity is a zero over a stated population, and the binding
    set is a list of components that either exists or does not.  A reader
    should not have to open a JSON file to learn which.
    """
    neutrality = verdict.get("neutrality_is_gate_GR") or {}
    print("\n  (1) neutrality of the default ruler — gate GR's own check")
    print(f"      GR verdict : {neutrality.get('verdict')}")
    if neutrality.get("why"):
        print(f"      {neutrality['why']}")
    else:
        print(
            f"      {neutrality.get('n_runs_reproduced')}/"
            f"{neutrality.get('n_runs')} run(s) reproduced; "
            f"{neutrality.get('n_values_differing')} of "
            f"{neutrality.get('n_values_compared')} compared value(s) differ"
        )
        print(f"      population : {neutrality.get('gr_population')}")
    print(f"      record     : {neutrality.get('record')}")

    print(
        "\n  (2) the identity — a pair no evaluation decided differently is "
        "bit-identical"
    )
    print(
        f"      {verdict.get('n_pairs_bit_identical')}/"
        f"{verdict.get('n_pairs')} pair(s) bit-identical; "
        f"{verdict.get('n_pairs_with_a_changed_verdict')} pair(s) had an "
        f"evaluation whose verdict changed and are therefore allowed to differ"
    )
    print(
        f"      {verdict.get('n_values_differing')} of "
        f"{verdict.get('n_values_compared')} record values and "
        f"{verdict.get('n_mfile_lines_differing')} of "
        f"{verdict.get('n_mfile_lines_compared')} output-file lines differ"
    )
    header = (
        f"      {'arm':<4}{'configuration':<23}{'seed':>5} "
        f"{'evals':>6}{'decisive':>9}{'verdict':>8} {'comps=':>7}  "
        f"{'values':>12} {'lines':>8}  result"
    )
    print(header)
    for row in verdict.get("runs", []):
        print(
            f"      {row['arm']:<4}{row['configuration']:<23}"
            f"{row['seed']:>5} {row['n_predicate_evaluations']:>6}"
            f"{row['n_evaluations_with_a_decisive_component']:>9}"
            f"{row['n_evaluations_where_the_verdict_changed']:>8} "
            f"{str(row['components_compared_identical']):>7}  "
            f"{row['record']['n_mismatched']:>5}/"
            f"{row['record']['n_compared']:<6} "
            f"{row['mfile']['n_lines_differing']:>3}/"
            f"{row['mfile']['n_lines_compared']:<4}  "
            f"{'PASS' if row['passed'] else 'FAIL'}"
        )
        for mismatch in row["record"]["mismatches"][:10]:
            print(
                f"        DIFFERS {mismatch['field']}: "
                f"{mismatch.get('before')!r} -> {mismatch.get('after')!r}"
            )

    print("\n  (3) the binding set — where the two rulers disagree at all")
    binding = verdict.get("binding_set") or []
    if not binding:
        print(f"      none.  {verdict.get('binding_set_empty_because')}")
    else:
        print(
            f"      {verdict.get('n_binding_component_events')} component "
            f"event(s) over "
            f"{verdict.get('n_predicate_evaluations_observed')} observed "
            f"predicate evaluations"
        )
        print(
            f"      {'configuration':<23}{'arm':<4}{'seed':>5}{'eval':>6}  "
            f"{'component':<44}{'|y|/s':>10}  held  changed"
        )
        for event in binding[:40]:
            ratio = event["value_over_scale"]
            print(
                f"      {event['configuration']:<23}{event['arm']:<4}"
                f"{event['seed']:>5}{event['evaluation']:>6}  "
                f"{event['component']:<44}"
                f"{'n/a' if ratio is None else format(ratio, '10.3f')}  "
                f"{str(event['held_the_pass_under_frozen']):<5} "
                f"{event['changed_the_evaluation_verdict']}"
            )
        if len(binding) > 40:
            print(f"      … and {len(binding) - 40} more, in the gate record")

    print("\n  the exit audit, both rulers, per run (hex maxima)")
    print(
        f"      {'arm':<4}{'configuration':<23}{'seed':>5}  "
        f"{'run ruler':<10}{'audit frozen':<24}{'audit mixed':<24}"
    )
    for row in verdict.get("runs", []):
        for run_ruler, block in row["audit"].items():
            print(
                f"      {row['arm']:<4}{row['configuration']:<23}"
                f"{row['seed']:>5}  {run_ruler:<10}"
                f"{str(block.get('frozen')):<24}{str(block.get('mixed')):<24}"
            )
    print(
        "      both columns are shown because one alone would report a change "
        "of ruler as a change of accuracy"
    )
    for tooth in verdict.get("teeth", []):
        print(
            f"    tooth {tooth['tooth']:<38} {tooth['tooth_result']:<13} "
            f"{tooth['evidence']}"
        )
    print(f"    record       : {verdict.get('record')}")


def print_verdict(verdict: Mapping[str, Any]) -> None:
    print(f"\n=== gate {verdict['gate']} — {verdict['what_it_proves']}")
    print(f"    binds        : {verdict['binds']}")
    print(f"    verdict      : {verdict['verdict']}")
    print(f"    population   : {verdict.get('population', '(none stated)')}")
    provenance = verdict.get("runs_provenance") or {}
    if provenance.get("n_records"):
        own = verdict.get("tree_git_head")
        heads = provenance["records_by_head"]
        summary = ", ".join(
            f"{count} at {head[:8]}" + (" (this commit)" if head == own else "")
            for head, count in sorted(heads.items(), key=lambda kv: -kv[1])
        )
        print(
            f"    runs read    : {provenance['n_records']} record(s) — {summary}"
            + ("  [resumed]" if verdict.get("resumed") else "")
        )
    if verdict.get("runs_are_not_this_commit's"):
        print(f"    NOTE         : {verdict["runs_are_not_this_commit's"]}")
    for key in (
        "n_compared",
        "n_identical",
        "n_mismatched",
        "n_pairs",
        "n_values_compared",
        "n_values_excluded",
        "n_values_differing",
        "n_mfile_lines_compared",
        "n_mfile_lines_excluded",
        "n_mfile_lines_differing",
    ):
        if key in verdict:
            print(f"    {key:<28}: {verdict[key]}")
    for key in (
        "n_runs",
        "n_components_compared",
        "n_components_differing",
        "n_reference_values_compared",
        "n_reference_values_differing",
    ):
        if key in verdict:
            print(f"    {key:<28}: {verdict[key]}")
    if verdict.get("gate") == "predicate_mode":
        print_predicate_mode(verdict)
        return
    for row in verdict.get("runs", []):
        if "checks" in row:
            print(
                f"      {row['arm']:<3} {row['configuration']:<22} "
                f"loop={row['matrix_cell']:<8} path={str(row['output_path']):<14} "
                f"sweeps={row['output_loop_sweeps']}  "
                f"{'PASS' if row['passed'] else 'FAIL'}"
            )
            for check in row["checks"]:
                print(f"        [{'ok ' if check['passed'] else 'FAIL'}] "
                      f"{check['check']} — {check['detail']}")
            continue
        print(
            f"      {row['arm']:<3} {row['configuration']:<22} "
            f"values {row['record']['n_mismatched']}/{row['record']['n_compared']} "
            f"lines {row['mfile']['n_lines_differing']}/"
            f"{row['mfile']['n_lines_compared']}  "
            f"{'PASS' if row['passed'] else 'FAIL'}"
        )
        for mismatch in row["record"]["mismatches"][:10]:
            print(f"        DIFFERS {mismatch['field']}: {mismatch.get('before')!r} "
                  f"-> {mismatch.get('after')!r}")
        for line in row["mfile"]["differing"][:10]:
            print(f"        LINE {line['line']}: {line['before']!r} -> {line['after']!r}")
    for failure in verdict.get("failures", []) or []:
        print(f"    FAILURE: {failure}")
    for tooth in verdict.get("teeth", []):
        print(f"    tooth {tooth['tooth']:<32} {tooth['tooth_result']:<13} {tooth['evidence']}")
    print(f"    record       : {verdict.get('record')}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "gate",
        choices=(
            "g0prime",
            "switch-neutrality",
            "output-path",
            "output-path-contrast",
            "output-path-measurements",
            "predicate-counters",
            "predicate-mode",
            "attempts",
            "all",
        ),
        help="which gate to run; 'all' runs the gates that need no capture.  "
        "'output-path-contrast', 'output-path-measurements', "
        "'predicate-counters' and 'attempts' are not gates: they publish what "
        "the experiment plan asks for by name — what the output-time loop "
        "moves in the output files, what it costs, where the accepted state "
        "sits against the tolerance at the declared audit position, (section "
        "3.5 check 5) what each arm's convergence test cost in evaluations and "
        "components compared with the empty block visits counted beside them, "
        "and (section 3.5, retries) what each attempt of the optimiser's retry "
        "ladder cost with check 2's two iteration constructions beside it",
    )
    parser.add_argument(
        "--capture",
        choices=("before", "after", "runs"),
        help="switch-neutrality: run the two reference arms on every "
        "configuration and record them under this label ('before' or "
        "'after'), then stop.  output-path and predicate-mode: 'runs' makes "
        "the gate's own runs, then stops",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="switch-neutrality: compare the two captures (the default)",
    )
    parser.add_argument("--resume", action="store_true", help="skip completed runs")
    parser.add_argument("--no-teeth", action="store_true", help="skip the teeth")
    parser.add_argument(
        "--records", default=None, help="where the verdict goes (default runs/gates)"
    )
    args = parser.parse_args(argv)

    campaign = default_campaign()
    records_dir = Path(args.records) if args.records else Path(campaign.runs_dir) / GATES_SUBPATH

    if args.gate == "output-path-contrast":
        manifest = capture_contrast(campaign, resume=args.resume)
        print(f"captured {manifest['n_runs']} contrast run(s) at "
              f"{manifest['tree_git_head']}")
        for row in manifest["runs"]:
            print(f"  {row['configuration']:<22} {row['label']:<14} "
                  f"{row['status']} {row['override_env']}")
        print(f"  manifest: {manifest['manifest']}")
        return 0

    if args.gate == "predicate-counters":
        block = predicate_counter_measurements(campaign)
        out = records_dir / "predicate_counters" / "measurements.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(block, indent=2, default=str) + "\n")
        print_predicate_counters(block)
        print(f"\n  record: {out}")
        return 0

    if args.gate == "attempts" and args.capture:
        manifest = capture_ladder(campaign, resume=args.resume)
        print(f"captured {manifest['n_runs']} ladder run(s) at "
              f"{manifest['tree_git_head']}")
        print(f"  {manifest['what']}")
        for row in manifest["runs"]:
            print(f"  {row['configuration']:<22} {row['status']} {row['outdir']}")
        print(f"  manifest: {manifest['manifest']}")
        return 0

    if args.gate == "attempts":
        block = attempt_measurements(campaign)
        out = records_dir / "attempts" / "measurements.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(block, indent=2, default=str) + "\n")
        print_attempts(block)
        print(f"\n  record: {out}")
        return 0

    if args.gate == "output-path-measurements":
        block = output_path_measurements(campaign)
        out = records_dir / "output_path" / "measurements.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(block, indent=2, default=str) + "\n")
        print_measurements(block)
        print(f"\n  record: {out}")
        return 0

    if args.gate == "output-path" and args.capture:
        manifest = capture_output_path(campaign, resume=args.resume)
        print(f"captured {manifest['n_runs']} run(s) at "
              f"{manifest['tree_git_head']}")
        for row in manifest["runs"]:
            print(f"  {row['arm']:<3} {row['configuration']:<22} "
                  f"{row['status']} {row['outdir']}")
        print(f"  manifest: {manifest['manifest']}")
        return 0

    if args.gate == "predicate-mode" and args.capture:
        manifest = capture_predicate_mode(campaign, resume=args.resume)
        print(f"captured {manifest['n_runs']} run(s) at "
              f"{manifest['tree_git_head']}")
        for row in manifest["runs"]:
            print(f"  {row['arm']:<3} {row['configuration']:<22} "
                  f"seed{row['seed']:03d} {row['ruler']:<7} {row['status']}")
        print(f"  manifest: {manifest['manifest']}")
        return 0

    if args.gate == "switch-neutrality" and args.capture:
        manifest = capture_neutrality(campaign, args.capture, resume=args.resume)
        print(f"captured {manifest['n_runs']} run(s) as {args.capture!r} at "
              f"{manifest['tree_git_head']}")
        for row in manifest["runs"]:
            print(f"  {row['arm']:<3} {row['configuration']:<22} {row['outdir']}")
        print(f"  manifest: {manifest['manifest']}")
        return 0

    names = (
        ["g0prime"]
        if args.gate in ("g0prime", "all")
        else []
    )
    if args.gate == "switch-neutrality":
        names = ["switch_neutrality"]
    elif args.gate == "output-path":
        names = ["output_path"]
    elif args.gate == "predicate-mode":
        names = ["predicate_mode"]
    elif args.gate == "all":
        names.append("switch_neutrality")
        names.append("output_path")
        names.append("predicate_mode")

    gates = registry(campaign)
    status = 0
    for name in names:
        try:
            verdict = gates[name].run(records_dir=records_dir, teeth=not args.no_teeth)
        except GateError as exc:
            print(f"\n=== gate {name} — REFUSED TO RUN\n    {exc}")
            status = 1
            continue
        print_verdict(verdict)
        if verdict["verdict"] != "PASS":
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
