"""Gate G1 -- switch neutrality -- and the record/output-file comparison it rests on.

With every architecture switch unset, the copy **after** a driver change behaves
byte-identically to the copy **before** it.  Two reference runs on each
configuration -- one optimisation and one evaluation, both with the whole switch
vocabulary cleared -- are recorded at the commit before the change and again
after it, and every deterministic value of the two records is compared, plus
PROCESS's own output file line by line.

The exclusion tables (:data:`ALWAYS_EXCLUDED`,
:data:`FIELDS_ADDED_BY_A_DRIVER_CHANGE`,
:data:`FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE` and the volatile sets) live here,
whole, beside the gate that reads them; ``exclusion_review`` reads them from
here.  The comparison machinery (:func:`leaves`, :func:`compare_records`,
:func:`compare_mfiles`) is shared with gates G8 and G9 and the diagnosis
instrument, which import it from this module.

Moved verbatim out of ``harness/gates/gates.py`` (its ``G1`` and ``the earlier
capture's vocabulary`` sections) by the code-move task of the simplification
survey; written by task **A56 (driver-renames)** and reviewed by **A52
(harness-gates)**.  Gate name, ``runs_under``, record path and teeth are
unchanged; the gate is constructed by :func:`gate` and registered in
``harness/gates/registry.py``.
"""

from __future__ import annotations

import copy
import datetime as _dt
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Mapping

_EXPERIMENT_DIR = Path(__file__).resolve().parents[2]
if str(_EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(_EXPERIMENT_DIR))

from harness.core import framework  # noqa: E402
from harness.core import pool as pool_mod  # noqa: E402
from harness.core import records as records_mod  # noqa: E402
from harness.gates import reference as reference_mod  # noqa: E402
from harness.core.config import Campaign  # noqa: E402

GATES_SUBPATH = framework.GATES_SUBPATH
Gate = framework.Gate
Tooth = framework.Tooth
GateError = framework.GateError
_git_head = framework.git_head


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
    # A110 (v5-warmup-verdict-once): the same absolute path again, inside the
    # snapshot block (child.install_exit_snapshot_hook's state), added after
    # the group above was written.  It agreed only while both captures were
    # made in one tree; A109's write-set press of G1, the first with its two
    # captures in two trees (A101's and A109's), failed on it alone (3 of 3 651
    # values, 0 of 51 319 output lines; trap T20).  The hook loads the file
    # with the same load_spec as the exit audit, and in every optimisation
    # record this leaf equals exit_audit.coupling_state, whose file's identity
    # is compared through exit_audit.components_sha256 (the rebuilt spec's
    # digest, refused at load unless it equals the artifact's own); measured
    # by the exclusion review (exclusion_review.PATH_CONTENT_WITNESS).
    "audit_snapshot.coupling_state": (
        "the same absolute path, inside the snapshot block.  The file is the "
        "one exit_audit.coupling_state names in the same record, and its "
        "identity is compared through exit_audit.components_sha256"
    ),
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
    # --- the harness's own stamps of itself and of the campaign (A100 (v5-test-set)) --
    #
    # Found by the first press of the DR11 straddle (b1bb1594 -> 60434c52):
    # 27 differing leaves, every one a harness stamp and none a driver value,
    # with every output-file line identical.  Each is a thing the harness
    # writes about itself or about the campaign it was pressed from, not a
    # thing the driver did; the driver's own resolved values are compared in
    # full through resolved_switches.
    "harness_version": (
        "which harness wrote the record: a version stamp, bumped when the "
        "record schema changes (0.2.0 -> 0.3.0 at DR11), not a behaviour"
    ),
    "campaign_tau": (
        "the campaign's declared tolerance, a harness stamp: DR11 made it "
        "follow the test set (1e-6 under the fallback, 1e-8 under the census "
        "set), and the reference arms compose no tolerance at all.  The "
        "tolerance the driver resolved is compared through "
        "resolved_switches (process.core.solver.module_solve.TAU)"
    ),
    "campaign_test_set": (
        "the campaign's declared test set, a harness stamp (DR11); the "
        "reference arms compose no test set and the driver's resolved value "
        "is compared through resolved_switches (…module_solve.TEST_SET)"
    ),
    "exit_audit.rulers_note": (
        "a sentence of prose the exit audit writes beside its blocks, reworded "
        "by DR11 when the second ruler went; not a value"
    ),
    # when it happened, and how long it took
    "launcher": "the pool's wall of the subprocess and the load average (DR12): context, never evidence",
    # A102 (v5-campaign): the warmed evaluation child's own timings.  The
    # block's counts and digests stay compared (FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE
    # names the block); these leaves are wall clock.
    "evaluation_warmup.warmup.wall_s": "the discarded warm-up evaluation's wall: context, never evidence",
    "evaluation_warmup.measured.wall_s": "the measured evaluation's wall: context, never evidence",
    "evaluation_warmup.warmup.timers_driver": "the warm-up's own timer accumulators (DR12): context, never evidence",
    "evaluation_warmup.restore_wall_s": "the whole-structure restore's wall: context, never evidence",
    "evaluation_warmup.warmup_wall_s": "the warm-up's wall: context, never evidence",
    "wall_s": "wall clock is context, never evidence (I-10)",
    # A116 (v5-gate-criterion-keys; issue I-45): the snapshot hook's own
    # stopwatch (child.install_exit_snapshot: time.perf_counter() summed over
    # the hook's calls).  Compared, and differing on every BR pair, from the
    # first straddle whose two sides both carry the snapshot block
    # (3211f50e -> d1e94dc8, A115: 3 of 4 614 values, 0 of 51 319 output-file
    # lines).  The exclusion review measured it before it was listed: the
    # only compared leaf named as a timing that differs, a non-negative float
    # on every side, with the other compared leaves of its block equal (72
    # over the three pairs, at 2c5e281a under census_tau1e-08) --
    # the stopwatch moved and the snapshots it timed did not.
    "audit_snapshot.wall_s": (
        "the exit-snapshot hook's wall: context, never evidence.  The "
        "positions it reached, their component counts and digests sit beside "
        "it in the same block and are compared"
    ),
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
    # Prose the harness quotes into the record from a constant.  It names no
    # driver behaviour -- it is the sentence records.AUDIT_POSITION_HOW or
    # records.AUDIT_POSITION_AFTER_RUN_WHY held when the run was made -- so
    # two captures can differ on it whenever the harness rewords the sentence,
    # with or without an instrument change.  It sat in the two conditional
    # groups above (compared whenever both sides carried it and the instrument
    # stamps agreed), which made a harness prose correction a G1 mismatch on
    # the next straddle; task A67 (written-file-gap) corrected the after_run
    # sentence and moved the leaf here.  What the leaf could witness is
    # compared elsewhere: `audit_position` itself is compared, and two
    # captures that disagree on it are refused before any value is.
    "audit_position_note": (
        "prose quoted from a harness constant into the record; it names no "
        "driver behaviour.  audit_position itself is compared, and two "
        "captures that disagree on it are refused before any value is"
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
    "schedule_resolution": (
        "the once-per-run schedule stamp driver change DR9 adds (A99 "
        "(v5-schedule-and-prime)): absent on a side captured before it, a "
        "block after.  With every switch unset the resolver is never reached "
        "and the block reads n_resolutions = 0 with an empty list; compared "
        "wherever both sides carry it"
    ),
    "loop_test_sets": (
        "the once-per-run stamp of what the block loops tested that driver "
        "change DR11 adds (A100 (v5-test-set)): absent on a side captured "
        "before it, null after with every switch unset (no block loop runs, "
        "so the stamp is never filled); compared wherever both sides carry it"
    ),
    "campaign_timers": (
        "the harness's stamp of whether the wall-clock timers were composed "
        "(driver change DR12, A101 (v5-timers-and-once)): absent on a side "
        "captured before it, False after with every switch unset; compared "
        "wherever both sides carry it"
    ),
    "timers": (
        "the timers block DR12 adds: absent on a side captured before it, "
        "null after with every switch unset (the driver's TIMERS is None and "
        "the harness stamps null); compared wherever both sides carry it"
    ),
    "coupling_state_provenance.test_set": (
        "the loaded spec's stamp of the test set (DR11), beside the tolerance "
        "and the ruler it already carried: absent on the earlier side, null "
        "on the reference arms after (they compose no test set)"
    ),
    "audit_snapshot": (
        "the snapshot block the audit-position change adds; absent on the "
        "earlier side.  Both captures audit at the same position, which is "
        "checked before the comparison runs and is what makes exit_audit "
        "comparable"
    ),
    # A102 (v5-campaign; V5 plan §6): the warmed evaluation child's block --
    # a harness change to the child, not a driver change, but the same shape
    # as the timer fields above: absent on a side captured before the child
    # warmed, a block after; its counts and exit-state digests are compared
    # wherever both sides carry it (its wall-clock leaves are excluded by
    # name, ALWAYS_EXCLUDED).  First placed in the instrument-change table,
    # which applies only where the audit instrument's stamp differs; the
    # after capture re-made by the warmed child at d08e8ab4 then read every
    # leaf of the block as present on one side only (933 values, 0 output-file
    # lines) -- moved here at that press.
    "evaluation_warmup": (
        "the warmed evaluation's own account of itself (A102 (v5-campaign)): "
        "the discarded warm-up's counts and digest, the entry's restore, the "
        "measured evaluation's counts and digest.  Absent on a side captured "
        "by the cold child, a block after; compared wherever both sides carry it"
    ),
    "reproduction_overrides": (
        "a field the record gains so that a run made under the reproduction "
        "gate's overrides says so; null on both sides here, absent on the "
        "earlier one"
    ),
    # The job identity (task A72 (resume-identity-and-shared-pool), I-23).
    # Stamped by the pool after the child returns; absent on a capture made
    # before the field existed.  Where both sides carry it, it is compared:
    # the two captures are the **same job** at two commits, so every identity
    # field must agree, and a difference there is a capture of another job
    # under this gate's name.  The digest is a function of the identity.
    "job_identity": (
        "the pool's rendering of every field it composed into the run; absent "
        "on a capture made before A72.  Where both sides carry it the two "
        "captures must be the same job, field for field"
    ),
    "job_digest": (
        "sha256 of the identity above; absent on a capture made before A72, "
        "equal where both sides carry it"
    ),
    # The allowance mechanism's record field, retired from the schema by A72
    # (survey item B4) and from the child by A73 (the child-side remainder):
    # present (an empty list) on every capture made before A73, absent on
    # every capture made since, which is the shape this table exists for.
    # Compared, and equal, wherever both sides carry it.
    "pending_switches_allowed": (
        "the retired allowance's stamp: an empty list on every record made "
        "between A59 and A73, absent since the child stopped writing it.  "
        "Excluded only while one side lacks it"
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
        "the second ruler's audit: absent on a side captured before DR5 added "
        "it and absent again on a side captured after DR11 (A100 "
        "(v5-test-set)) removed the mixed ruler.  It is a second measurement "
        "of the same exit state, not a difference in it: the exit state itself "
        "is compared through the fields above and through every output-file "
        "line"
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

#: A conditional name that is a **digest of a block**, and that block: the
#: name is compared only where both sides computed it over the same field set
#: -- the same top-level keys of the block -- and excluded where they did not
#: (one side lacks the block, or the two blocks render different fields).
#:
#: The live case is the job digest, sha256 over the canonical JSON of the job
#: identity (``records.job_digest``).  DR11 (A100 (v5-test-set)) added two
#: identity fields, the test set and the tolerance, each rendered **only where
#: it differs from V4's value** -- so the same job's digest moves across the
#: DR11 commit although every field both sides carry agrees, and two captures
#: under one test set at two tolerances render different field sets.  The
#: identity's own leaves are compared one by one under the conditional name
#: ``job_identity``; the digest adds a comparison only where its inputs are the
#: same fields.  Until A116 (v5-gate-criterion-keys; issue I-43) the witness
#: was one field, ``job_identity.test_set``, present on exactly one side; under
#: ``census_tau1e-06`` the test set is on both sides while the tolerance is
#: rendered on one, so two digests over two field sets were compared and
#: differed on 6 of 6 pairs, 0 of 51 319 output-file lines differing (A114).
#: A tooth shows the other half: a digest that differs over the same field set
#: still FAILs.
FIELD_SET_WITNESS: dict[str, str] = {
    "job_digest": "job_identity",
}


def _field_set(document: Mapping[str, Any], path: str) -> frozenset[str] | None:
    """The top-level keys of the block at *path*, or None where it is absent,
    null or not a mapping."""
    if not records_mod.has_path(document, path):
        return None
    block = records_mod.resolve_path(document, path)
    return frozenset(block) if isinstance(block, Mapping) else None


def _field_set_witness(path: str, conditional: Mapping[str, str]) -> str | None:
    """The block whose field set decides whether *path* is compared, or None.
    Only names the caller's own conditional table holds can have one."""
    bare = path.split("[")[0]
    for name, block in FIELD_SET_WITNESS.items():
        if name not in conditional:
            continue
        if bare == name or bare.startswith(name + "."):
            return block
    return None

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
#:
#: This gate is one of the position's declared callers
#: (:data:`records.AUDIT_POSITION_AFTER_RUN_CALLERS`) and names itself on
#: every job it makes; the run pool refuses the position for a caller that
#: does not.
NEUTRAL_AUDIT_POSITION = records_mod.AUDIT_POSITION_AFTER_RUN
NEUTRAL_GATE_NAME = "switch_neutrality"


def neutrality_root(campaign: Campaign) -> Path:
    """Where G1's two captures live — **not** the shared pool.

    The before and after captures are one job identity at two commits; the
    pool's one-directory-per-identity would put the second on top of the first,
    and the "before" side is never re-made by this gate (harness plan amendment
    13, rule (ii)).  So each capture names its directory explicitly, by label,
    and the gate declares ``runs_under`` rather than a job set.  Nothing shares
    with these runs anyway: their audit position and caller are in the
    identity.
    """
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
                    audit_position_caller=NEUTRAL_GATE_NAME,
                )
            )
    results = pool_mod.run_all(jobs, campaign, resume=resume)
    # The manifest carries the commit of the **records it indexes**, read from
    # the records themselves, and names the pressing commit apart.  Under
    # ``--resume`` the two differ whenever every record was kept -- the press
    # is at a later commit than the runs -- and a manifest that stamped the
    # pressing commit as ``tree_git_head`` misplaced its own records
    # (improvement list item 13, found by A67 (written-file-gap)).  The
    # straddle is between the records, so it is the records' commit that
    # decides it; a capture whose records sit at two commits states both and
    # names none as its own.
    record_heads = sorted(
        head
        for head in {
            records_mod.read(job.outdir).get("tree_git_head") for job in jobs
        }
        if head
    )
    manifest = {
        "label": label,
        "captured": _dt.datetime.now().isoformat(timespec="seconds"),
        "tree_git_head": record_heads[0] if len(record_heads) == 1 else None,
        "records_git_heads": record_heads,
        "pressed_at_git_head": _git_head(),
        "tree": str(campaign.tree),
        "n_runs": len(jobs),
        "audit_position": NEUTRAL_AUDIT_POSITION,
        "audit_position_caller": NEUTRAL_GATE_NAME,
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


# --------------------------------------------------------------------------
# the earlier capture's vocabulary
# --------------------------------------------------------------------------
#
# G1 is about **behaviour**: with every architecture switch unset, does the copy
# after a change do what it did before?  A record-field **rename** is a change
# of the record's vocabulary and not of its behaviour, so a straddle that
# contains one must not report the rename as a difference — and must not stop
# comparing the renamed fields either, which is what excluding them by name
# would do.  The earlier capture's leaf paths are therefore **translated** into
# this revision's vocabulary through the one map the project keeps for it,
# ``reference.FIELD_NAME_MAP``, and the translated leaves are then compared as
# values like any other.
#
# Found by task **A55 (harness-smoke)**: the first press in which G1's two
# captures genuinely straddled task A53's record-field rename reported **144 of
# 2 903** values differing, every one of them "present on one side only" and
# every one a name that rename changed.


def _segments(path: str) -> list[str]:
    """A dotted leaf path as segments, each keeping its own list index."""
    return path.split(".")


def _bare(segment: str) -> str:
    """A segment without its list index: ``moved_constants[2]`` -> the name."""
    return segment.split("[", 1)[0]


def _index(segment: str) -> str:
    """A segment's list index, ``[2]`` or ``[]``, or the empty string."""
    name = _bare(segment)
    return segment[len(name):]


def translate_path(path: str, name_map: Mapping[str, str]) -> str:
    """*path* with one run of whole segments renamed through *name_map*.

    **Segment-aware, not prefix-aware.**  A map entry names a dotted run of
    segments, and the run is matched anywhere in the path, not only at its
    head: ``n_prime_calls -> n_arrangement_method_calls`` has to reach
    ``first_call_models.n_prime_calls`` as well as the bare field, and
    ``module_solve_totals -> block_loop_totals`` has to carry every leaf under
    the block with it.  A run is matched on the segments' **bare** names and the
    list index of the last segment replaced is kept, so
    ``module_solve_totals.moved_constants[2]`` translates and stays element 2.

    Longest run first, so ``module_solve_totals.outer_pass_hist`` is renamed by
    the entry that names both segments rather than by the entry that names the
    block; at most one run is replaced, at the leftmost match, so the result
    does not depend on the order two entries happen to be written in.
    """
    segments = _segments(path)
    bare = [_bare(segment) for segment in segments]
    for old in sorted(name_map, key=lambda name: (-len(_segments(name)), name)):
        wanted = _segments(old)
        width = len(wanted)
        for start in range(len(segments) - width + 1):
            if bare[start:start + width] != wanted:
                continue
            replacement = _segments(name_map[old])
            replacement[-1] += _index(segments[start + width - 1])
            return ".".join(
                segments[:start] + replacement + segments[start + width:]
            )
    return path


def translate_leaves(
    earlier: Mapping[str, Any], name_map: Mapping[str, str]
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """The earlier capture's leaves in this revision's vocabulary.

    Returns the translated leaves and the renamings that were applied, so the
    verdict can say how many leaves it renamed and which — a translation nobody
    counts is indistinguishable from an exclusion nobody declared.

    Two paths translating onto one is a **refusal**: it would silently drop one
    of them, which is the shape of every quiet population shrink this project
    has published (trap T11).
    """
    translated: dict[str, Any] = {}
    renamed: list[dict[str, str]] = []
    for path, value in earlier.items():
        new = translate_path(path, name_map)
        if new in translated:
            raise GateError(
                f"two leaves of the earlier capture translate onto {new!r} "
                f"through the record-field name map; keeping one would drop "
                f"the other silently.  The map is reference.FIELD_NAME_MAP."
            )
        translated[new] = value
        if new != path:
            renamed.append({"from": path, "to": new})
    return translated, renamed


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
    name_map: Mapping[str, str] | None = None,
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

    ``name_map`` translates the **earlier** record's leaf paths into this
    revision's vocabulary before anything is compared
    (:func:`translate_leaves`).  A record-field rename is a change of the
    record's vocabulary and not of the copy's behaviour, so the renamed leaves
    are **compared as values** under their new names and are never excluded.  A
    leaf present on one side only that the map does not cover is still a
    mismatch, which is what keeps the translation from becoming an exclusion
    under a friendlier name.
    """
    a = leaves(dict(before))
    renamed: list[dict[str, str]] = []
    if name_map:
        a, renamed = translate_leaves(a, name_map)
    renamed_paths = {row["to"] for row in renamed}
    b = leaves(dict(after))
    every = sorted(set(a) | set(b))
    missing = object()
    instruments = (exit_audit_instrument(before), exit_audit_instrument(after))
    instrument_moved = instruments[0] != instruments[1]
    compared, excluded_paths, mismatches = 0, [], []
    renamed_compared: list[str] = []
    renamed_differing: list[str] = []
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
            field_block = _field_set_witness(path, conditional)
            fields_a = _field_set(before, field_block) if field_block else None
            fields_b = _field_set(after, field_block) if field_block else None
            if field_block is not None and (fields_a is not None or fields_b is not None):
                # A digest of a block: compared only over the same field set
                # (FIELD_SET_WITNESS; A116, issue I-43).
                one_sided = fields_a != fields_b
            elif witness is not None and (
                _block_present(before, witness) or _block_present(after, witness)
            ):
                one_sided = _block_present(before, witness) != _block_present(
                    after, witness
                )
            else:
                # No witness declared, or the witness absent on both sides
                # (two captures made before the witnessed field existed):
                # the name's own leaf decides.
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
        if path in renamed_paths:
            renamed_compared.append(path)
        va, vb = a.get(path, missing), b.get(path, missing)
        if va is missing or vb is missing:
            mismatches.append(
                {
                    "field": path,
                    "before": "<absent>" if va is missing else va,
                    "after": "<absent>" if vb is missing else vb,
                    "why": "the field is present on one side only",
                    "renamed_from_the_earlier_vocabulary": path in renamed_paths,
                }
            )
            if path in renamed_paths:
                renamed_differing.append(path)
            continue
        if not _same(va, vb):
            mismatches.append(
                {
                    "field": path,
                    "before": va,
                    "after": vb,
                    "renamed_from_the_earlier_vocabulary": path in renamed_paths,
                }
            )
            if path in renamed_paths:
                renamed_differing.append(path)
    return {
        "n_compared": compared,
        "n_leaves_renamed_from_the_earlier_vocabulary": len(renamed),
        "renamed_from_the_earlier_vocabulary": renamed,
        "n_renamed_leaves_compared": len(renamed_compared),
        "n_renamed_leaves_differing": len(renamed_differing),
        "renamed_leaves_differing": renamed_differing,
        "name_map_used": (
            "harness.gates.reference.FIELD_NAME_MAP"
            if name_map
            else "none: the two captures share one record vocabulary"
        ),
        "n_entries_in_the_name_map": len(name_map or {}),
        "what_the_translation_means": (
            "the earlier capture's leaf paths were renamed into this "
            "revision's vocabulary and then compared as values, never "
            "excluded: a record-field rename is a change of the record's "
            "vocabulary and not of the copy's behaviour, and a leaf the map "
            "does not cover that is present on one side only is still a "
            "mismatch"
        ),
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
    return records_mod.read(directory)


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
    n_renamed = n_renamed_compared = n_renamed_differing = 0
    renamed_differing: list[str] = []
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
                # The earlier capture may have been made before a record-field
                # rename.  Translate its vocabulary rather than excluding the
                # renamed fields: the rename is a change of what the record
                # calls a quantity, not of what the copy did, so the quantity
                # stays compared.
                name_map=reference_mod.FIELD_NAME_MAP,
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
            n_renamed += values["n_leaves_renamed_from_the_earlier_vocabulary"]
            n_renamed_compared += values["n_renamed_leaves_compared"]
            n_renamed_differing += values["n_renamed_leaves_differing"]
            renamed_differing.extend(
                f"{key}: {path}" for path in values["renamed_leaves_differing"]
            )
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
            f"one, and compared again the moment the two stamps agree.  "
            f"{n_renamed} leaf/leaves of the earlier capture were **renamed** "
            f"into this revision's vocabulary through "
            f"harness.gates.reference.FIELD_NAME_MAP "
            f"({len(reference_mod.FIELD_NAME_MAP)} entries) and then compared "
            f"as values, never excluded: {n_renamed_compared} compared, "
            f"{n_renamed_differing} differing"
        ),
        "n_pairs": len(rows),
        "n_leaves_renamed_from_the_earlier_vocabulary": n_renamed,
        "n_renamed_leaves_compared": n_renamed_compared,
        "n_renamed_leaves_differing": n_renamed_differing,
        "renamed_leaves_differing": renamed_differing,
        "record_field_name_map": dict(reference_mod.FIELD_NAME_MAP),
        "what_the_translation_means": (
            "gate G1 is about behaviour.  A record-field rename changes what "
            "the record calls a quantity and not what the copy did with it, so "
            "the earlier capture's leaf paths are translated into this "
            "revision's vocabulary and the renamed leaves are compared as "
            "values under their new names.  They are never excluded, and a "
            "leaf present on one side only that the map does not cover is "
            "still a mismatch"
        ),
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
        "audit_position_override": {
            "position": NEUTRAL_AUDIT_POSITION,
            "caller": NEUTRAL_GATE_NAME,
            "why": records_mod.AUDIT_POSITION_AFTER_RUN_CALLERS[NEUTRAL_GATE_NAME],
            "declared_callers": sorted(records_mod.AUDIT_POSITION_AFTER_RUN_CALLERS),
        },
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
    the tree the gate is being run in — so it follows the ordinary rule, and
    the ordinary rule is ``pool.run``'s, not this function's: a run is kept
    only where its directory holds a **complete record of the same job**, and
    re-made otherwise.

    It used to return early whenever ``--resume`` was given and a manifest
    existed, which made the *manifest's existence* the evidence — precisely
    what ``pool.run`` says a directory may never be.  Task **A55
    (harness-smoke)** found it: under the merged schema every record of the
    previous capture is incomplete, and the gate kept all six anyway, so a
    press that should have re-made them reported a straddle ending at a commit
    it had not measured.  Handing the whole capture to the pool puts the
    completeness contract back in the path, which is the standing property of
    harness plan amendment 17 — ``--resume`` cannot cross a schema change, and
    that is not to be weakened for a cheaper press.
    """
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

    def _earlier_vocabulary(record: Mapping[str, Any]) -> tuple[dict, str, Any]:
        """A copy of *record* rewritten into the earlier capture's vocabulary.

        The map runs forwards everywhere else, so here it is inverted: a block
        the rename gave a new name is put back under the old one, which is what
        an earlier capture actually holds.  Returns the copy, the old path of a
        renamed scalar leaf, and that leaf's value.
        """
        earlier = copy.deepcopy(dict(record))
        renamed_leaf = renamed_value = None
        for old, new in reference_mod.FIELD_NAME_MAP.items():
            if "." in old or "." in new:
                continue
            if new in earlier:
                earlier[old] = earlier.pop(new)
                if isinstance(earlier[old], int) and renamed_leaf is None:
                    renamed_leaf, renamed_value = old, earlier[old]
        return earlier, renamed_leaf, renamed_value

    def a_renamed_field_moved_by_one() -> tuple[bool, str]:
        """A genuine difference in a renamed field must still be caught.

        The translation exists so that a rename does not read as a difference.
        It must not also stop a *difference* in a renamed field from reading as
        one — otherwise it would be the exclusion it was chosen instead of,
        with a friendlier name.  So: a record rewritten into the earlier
        vocabulary, one renamed integer moved by one under its **old** name,
        compared against the record itself.  The comparison has to report it
        and name it under its **new** name.
        """
        record, name, side = sample_carrying_the_instrument_stamp()
        earlier, old_path, value = _earlier_vocabulary(record)
        if old_path is None:
            return False, (
                "no renamed scalar leaf is present on the sample record, so "
                "the tooth could not be built"
            )
        new_path = reference_mod.FIELD_NAME_MAP[old_path]
        clean = compare_records(
            earlier,
            record,
            excluded=ALWAYS_EXCLUDED,
            conditional=FIELDS_ADDED_BY_A_DRIVER_CHANGE,
            instrument_changed=FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE,
            name_map=reference_mod.FIELD_NAME_MAP,
        )
        broken = copy.deepcopy(earlier)
        broken[old_path] = value + 1
        result = compare_records(
            broken,
            record,
            excluded=ALWAYS_EXCLUDED,
            conditional=FIELDS_ADDED_BY_A_DRIVER_CHANGE,
            instrument_changed=FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE,
            name_map=reference_mod.FIELD_NAME_MAP,
        )
        named = [m for m in result["mismatches"] if m["field"] == new_path]
        return (
            clean["n_mismatched"] == 0
            and len(named) == 1
            and bool(named[0].get("renamed_from_the_earlier_vocabulary"))
        ), (
            f"on BR/{name} ({side} side) rewritten into the earlier "
            f"vocabulary, {old_path} moved {value} -> {value + 1}: untouched "
            f"the translated comparison reports "
            f"{clean['n_mismatched']} of {clean['n_compared']} differing with "
            f"{clean['n_leaves_renamed_from_the_earlier_vocabulary']} leaves "
            f"renamed, and with the one value moved it reports "
            f"{result['n_mismatched']} and names it under its new name "
            f"{new_path!r} — so the translation renames the field and still "
            f"compares its value"
        )

    def a_one_sided_leaf_the_map_does_not_cover() -> tuple[bool, str]:
        """The translation must not swallow a field the map does not name.

        A leaf present on one side only is a mismatch unless something declared
        covers it.  The name map covers renames and nothing else, so a field
        that simply appears on one side has to keep failing — which is what
        stops "translate the vocabulary" from becoming "excuse any absence".
        """
        record, name, side = sample_carrying_the_instrument_stamp()
        earlier = copy.deepcopy(dict(record))
        invented = "a_field_the_name_map_does_not_name"
        earlier[invented] = 1
        result = compare_records(
            earlier,
            record,
            excluded=ALWAYS_EXCLUDED,
            conditional=FIELDS_ADDED_BY_A_DRIVER_CHANGE,
            instrument_changed=FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE,
            name_map=reference_mod.FIELD_NAME_MAP,
        )
        named = [m for m in result["mismatches"] if m["field"] == invented]
        return len(named) == 1 and not named[0].get(
            "renamed_from_the_earlier_vocabulary"
        ), (
            f"on BR/{name} ({side} side), {invented!r} added to the earlier "
            f"side alone: the translated comparison reports "
            f"{result['n_mismatched']} of {result['n_compared']} values "
            f"differing and names it as present on one side only, not as a "
            f"rename — the map covers renames and nothing else"
        )

    def a_digest_moved_over_the_same_field_set() -> tuple[bool, str]:
        """The job digest is compared wherever both sides computed it over the
        same field set, and only there (A116 (v5-gate-criterion-keys); issue
        I-43).

        Part 1: one hex digit of ``job_digest`` changed on a copy of a captured
        record, compared with the record itself -- the same identity, the same
        field set -- must be the one mismatch, named.  Part 2: the same moved
        digest with the identity's ``tau`` field rendered on one side only (the
        shape of a census capture at 1e-8 against one at 1e-6, where τ is
        rendered only when it differs from V4's) must be excluded, with nothing
        differing.  Witnessed by the test set alone, as before A116, part 2
        compares the two digests and the tooth does not trip.
        """
        for side in ("after", "before"):
            for config in campaign.configurations:
                directory = neutrality_run_dir(campaign, side, config.name, "BR")
                if not (Path(directory) / "metrics.json").exists():
                    continue
                record = _read_record(directory, side=side, key=f"BR/{config.name}")
                if isinstance(record.get("job_digest"), str) and isinstance(
                    record.get("job_identity"), Mapping
                ):
                    break
            else:
                continue
            break
        else:
            return False, "no capture carries a job identity and its digest"
        tables = dict(
            excluded=ALWAYS_EXCLUDED,
            conditional=FIELDS_ADDED_BY_A_DRIVER_CHANGE,
            instrument_changed=FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE,
        )
        digest = record["job_digest"]
        moved = copy.deepcopy(record)
        moved["job_digest"] = digest[:-1] + ("0" if digest[-1] != "0" else "1")
        same_fields = compare_records(record, moved, **tables)
        caught = same_fields["n_mismatched"] == 1 and same_fields["mismatches"][0]["field"] == "job_digest"
        other = copy.deepcopy(moved)
        if "tau" in other["job_identity"]:
            del other["job_identity"]["tau"]
            shape = "tau removed from one side's identity"
        else:
            other["job_identity"]["tau"] = 1e-08
            shape = "tau added to one side's identity"
        other_fields = compare_records(record, other, **tables)
        excluded = (
            "job_digest" in other_fields["conditionally_excluded"]
            and other_fields["n_mismatched"] == 0
        )
        return caught and excluded, (
            f"on BR/{config.name} ({side} side), job_digest {digest[-6:]} -> "
            f"{moved['job_digest'][-6:]}: over the same field set "
            f"{same_fields['n_mismatched']} of {same_fields['n_compared']} values "
            f"differ ({[m['field'] for m in same_fields['mismatches']]}); with "
            f"{shape} the digest is "
            f"{'excluded' if 'job_digest' in other_fields['conditionally_excluded'] else 'COMPARED'} "
            f"and {other_fields['n_mismatched']} of {other_fields['n_compared']} differ"
        )

    return (
        Tooth(
            "a_digest_moved_over_the_same_field_set",
            "one hex digit of job_digest changed on a copy of a captured record, "
            "compared over the same identity field set, and again with tau "
            "rendered in one side's identity only",
            "be caught and named over the same field set, and excluded only "
            "where the field sets differ",
            a_digest_moved_over_the_same_field_set,
        ),
        Tooth(
            "a_renamed_field_moved_by_one",
            "one renamed integer moved by one on a record rewritten into the "
            "earlier capture's vocabulary",
            "still be caught, and be named under its NEW name",
            a_renamed_field_moved_by_one,
        ),
        Tooth(
            "a_one_sided_leaf_the_name_map_does_not_cover",
            "a field the name map does not name, added to the earlier side "
            "alone",
            "still be a mismatch: the translation covers renames and nothing else",
            a_one_sided_leaf_the_map_does_not_cover,
        ),
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




def gate(campaign: Campaign) -> Gate:
    """G1, as the registry holds it.  The literal is the one ``_plan_gates`` held."""
    return Gate(
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
    )
