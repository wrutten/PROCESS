#!/usr/bin/env python
"""The reproduction reference: the previous revision's numbers, committed.

Gate **GR** asks one question — *did rewriting the harness change the
measurement?*  It answers it by running twenty runs against the experiment's
own copy of PROCESS, at the commit where that copy is taken and **before any
driver change**, and comparing them with the same twenty runs made by the
previous revision of this experiment.  At that moment the copied driver is
byte-identical to the tree the previous revision measured, so any difference
is the harness's, which is exactly and only what GR is for
(harness plan §7.2).

This module owns the *reference half* of that comparison.  The previous
revision's records live in an untracked bulk directory, and this project has
destroyed untracked run records three times (issues I-14, I-15, I-16 of the
queue; a retired working tree took the evidence behind a headline correction
with it).  A gate anchored on files that can vanish is a gate that will one
day pass over nothing, which is trap **T11**'s shape.  So the compared
fields are extracted once into
``harness/reference/reproduction_reference.json`` and **committed**; the live
records are then used only to *re-derive* that file and check it byte for
byte.

The file was extracted **once** from those records, verified byte for byte
against them, and committed (task A49 (harness-reference)); the extraction,
verification and teeth stages that did it were retired by the simplification
survey's item B7, because the reference is not regenerated (D25) and the
records they read are the previous revision's untracked bulk.  What remains is
the committed bytes, the reader (:func:`load`, :func:`lookup`), the compared
field list and its translation (:data:`FIELD_NAME_MAP`), and the two printers
(``--reference show`` / ``--reference tables``).  The file's provenance block
names the extraction's source root, commit and date.

The entry schema
----------------

The committed file is ``{"format", "provenance", "entries"}``.  Each entry
is::

    {
      "arm":            V4's name for the arm            ("BR"; since the
                        renaming of 2026-09-15 the partitioned arms are
                        "A2" and "B2" — records.RECORDED_ARM_NAMES)
      "previous_arm":   the previous revision's name      ("R", "A1", "B3")
      "configuration":  the configuration's name          ("st_regression")
      "phase":          "A" (one evaluation) or "B" (one optimisation)
      "seed":           0 for the unperturbed start, 1 for the first
                        perturbed one.  The previous revision spelled these
                        "start000" / "start001"; the word here is "seed".
      "source_path":    the record's path relative to the runs root
      "source_sha256":  sha256 of the record file's bytes
      "tree_git_head":  the commit the record was made at
      "fields":         {compared field -> its value}, the field list being
                        REFERENCE_FIELDS[phase]
    }

:func:`lookup` returns one entry by ``(arm, configuration, seed)``; a lookup
that misses raises.  :data:`REFERENCE_FIELDS` is the compared-field list per
phase, exported as data so that the run path's GR comparator (task A50
(harness-run)) reads the same list this file was written from rather than a
second copy of it.

Heritage: the reference set, the compared fields and the teeth are the V4
harness implementation plan's §7.1, §7.3 and §7.4; the file is named for what
it holds rather than for the revision it came from (§11.1), and the source
revision is named in the JSON's provenance, where naming it is the point.
Written by task **A49 (harness-reference)**.  No PROCESS run happens here.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

_EXPERIMENT_DIR = Path(__file__).resolve().parents[2]
if str(_EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(_EXPERIMENT_DIR))

from harness.experiment import arms as arms_mod  # noqa: E402
from harness.experiment import switches as sw  # noqa: E402
from harness.core import records as records_mod  # noqa: E402
from harness.core.config import Campaign, default_campaign  # noqa: E402

#: This file's directory.
HERE = Path(__file__).resolve().parent.parent

#: Where the committed reference lives.  The name says what the file is, not
#: which revision produced it (harness plan §11.1).
REFERENCE_PATH = HERE / "reference" / "reproduction_reference.json"

#: Schema tag, so a later change to the entry shape is visible rather than
#: silently absorbed by a reader that expected the old one.
FORMAT = "reproduction-reference-1"

class ReferenceError(RuntimeError):
    """A refusal.  Never downgraded to a warning and never to a skip."""


# --------------------------------------------------------------------------
# the compared fields (harness plan §7.1)
# --------------------------------------------------------------------------
#
# Dotted paths into a record.  ``attempts[]`` means "map over that list and
# take the named key from each element", which is how the per-attempt
# iteration counts of the plan's check 2 are compared without pulling the
# rest of the forensics block into the reference.
#
# The two lists differ because the two phases record different things: an
# evaluation has no optimiser, so it has no objective under the optimiser's
# name, no exit code and no iteration count.  Which fields each phase's
# records actually carry was **enumerated from the records**, not assumed;
# the enumeration is in the file's provenance block and in A49's report.

#: Compared fields, per phase.  Exported as data: the run path's comparator
#: reads this rather than keeping a second copy of the list.
REFERENCE_FIELDS: dict[str, tuple[str, ...]] = {
    "B": (
        "node_calls_solve_phase",
        "node_calls_total",
        "n_model_calls",
        "n_prime_calls",
        "exact.norm_objf",
        "exit_audit.residual_max_hex",
        "module_solve_totals.n_call_models",
        "module_solve_totals.block_sweeps",
        "module_solve_totals.outer_pass_hist",
        "module_solve_totals.inner_sweeps_by_block",
        "n_solver_iterations",
        "mfile.ifail",
        "exit_forensics.n_solver_iterations_summed_over_attempts",
        "exit_forensics.n_attempts",
        "exit_forensics.attempts[].n_solver_iterations",
    ),
    "A": (
        "node_calls_single_eval",
        "n_model_calls_sweeps",
        "n_prime_calls",
        "exact.objf",
        "exit_audit.residual_max_hex",
        "module_solve_totals.n_call_models",
        "module_solve_totals.block_sweeps",
        "module_solve_totals.outer_pass_hist",
        "module_solve_totals.inner_sweeps_by_block",
        "exit_forensics.n_attempts",
    ),
}

# --------------------------------------------------------------------------
# the field-name map (orchestrator ruling at A56 (driver-renames)'s merge)
# --------------------------------------------------------------------------
#
# The driver change that renamed the switches to the harness plan's §11.2
# vocabulary renamed the *driver's* own counters with them — the prime became
# ``ARRANGEMENT_METHOD_CALLS``, the post-solve deferral became
# ``DEFER_PER_RUN_TOTALS`` — but the **record fields** carrying those counters
# kept the previous revision's mechanism words.  The ruling at that merge: the
# record fields are renamed by this task, through a map here, and the committed
# reference is **never regenerated** — its bytes are the previous revision's
# numbers, and a comparison that rewrote them would be a comparison with
# itself.
#
# So :data:`REFERENCE_FIELDS` above stays in the previous revision's spelling,
# because that is what the previous revision's records carry and what the
# committed file's keys are; every reader of that file that then reaches into a
# **this-revision** record goes through :func:`field_name_map`.

#: Previous-revision record path → this revision's path, for the fields whose
#: names carried a mechanism word the vocabulary retired.  A path absent from
#: this map is spelt the same in both revisions.
#:
#: *Why each*:
#:
#: ``module_solve_totals``
#:     named the driver module that produced it.  What it counts is the **block
#:     loop**, the vocabulary's word for V3's "inner loop / outer loop".
#: ``…outer_pass_hist``
#:     "outer pass" is the retired arm's word.  The matrix row is **block
#:     schedule**, and since that rename the schedule runs once, so what the
#:     histogram records is the schedule's passes per evaluation.
#: ``…inner_sweeps_by_block`` / ``…inner_solves_by_block``
#:     the sibling keys of the same dictionary, carrying the other half of the
#:     retired inner/outer pair.  Renamed with it rather than left behind,
#:     which would have made one dictionary half-translated.  *(This task's own
#:     decision; the ruling names ``outer_pass_hist`` alone.)*
#: ``post_solve_totals``
#:     "post-solve" is the mechanism; the vocabulary's term is the deferral's
#:     **frequency**, ``defer_per_run``.
#: ``n_prime_calls``
#:     "the prime" is the mechanism name for a method-level reorder; the matrix
#:     row is **arrangement · method**, and the driver's own counter has been
#:     called ``ARRANGEMENT_METHOD_CALLS`` since that change.
#: ``pin_intact_at_exit``
#:     "pin" survives only as a mechanism word in docstrings; the matrix row is
#:     the **burn-time owner**, and this field reports whether the constant
#:     that owns it was still that constant at exit.
FIELD_NAME_MAP: dict[str, str] = {
    "module_solve_totals": "block_loop_totals",
    "module_solve_totals.n_call_models": "block_loop_totals.n_call_models",
    "module_solve_totals.block_sweeps": "block_loop_totals.block_sweeps",
    "module_solve_totals.outer_pass_hist": (
        "block_loop_totals.schedule_passes_per_evaluation"
    ),
    "module_solve_totals.inner_sweeps_by_block": (
        "block_loop_totals.sweeps_by_block"
    ),
    "module_solve_totals.inner_solves_by_block": (
        "block_loop_totals.solves_by_block"
    ),
    "post_solve_totals": "defer_per_run_totals",
    "n_prime_calls": "n_arrangement_method_calls",
    "pin_intact_at_exit": "burn_time_constant_intact_at_exit",
}


def field_name_map() -> dict[str, str]:
    """Previous-revision record path → this revision's path.

    A function rather than a bare dict so that every caller is visible in one
    grep, and so that a path the map does not carry is answered the same way
    everywhere: unchanged.  Callers write ``field_name_map().get(path, path)``.
    """
    return dict(FIELD_NAME_MAP)


def this_revisions_path(previous_path: str) -> str:
    """Where a previous-revision path lives in a record of this revision."""
    return FIELD_NAME_MAP.get(previous_path, previous_path)


#: Why each field is compared, in one line.  Kept beside the list so that a
#: reader of the committed file does not have to open the plan to know what
#: a cell means.
FIELD_NOTES: dict[str, str] = {
    "node_calls_solve_phase": (
        "model executions during the solve, the cost unit of every Phase B "
        "table; excludes the output-time and audit sweeps"
    ),
    "node_calls_total": "model executions including the output-time and audit sweeps",
    "n_model_calls": (
        "sweeps of the dispatch body over the whole run (numerics.n_model_calls); "
        "the committed file's own note for this field still reads 'call_models "
        "evaluations the optimiser asked for' — its bytes are never regenerated "
        "(D25) — and that reading is wrong: the evaluations are "
        "sweeps_per_eval.n_evaluations (issue I-26, task A80 (report-accuracy-audit))"
    ),
    "n_prime_calls": (
        "executions of the run-constant first-wall geometry method at the head "
        "of a sweep (the arrangement-by-method change); 0 where it is off"
    ),
    "exact.norm_objf": "the normalised objective at the optimum, as a hex float",
    "exact.objf": (
        "the objective at the evaluation's exit, as a hex float; the "
        "evaluation phase's records spell it 'objf', the optimisation "
        "phase's 'norm_objf'"
    ),
    "exit_audit.residual_max_hex": (
        "the largest scaled coupling-state residual found by one further full "
        "sweep past termination, as a hex float; the accuracy ruler, taken "
        "identically in every arm"
    ),
    "module_solve_totals.n_call_models": (
        "call_models evaluations the block solver saw; 0 on the reference arm, "
        "which never enters it"
    ),
    "module_solve_totals.block_sweeps": "sweeps summed over every block",
    "module_solve_totals.outer_pass_hist": (
        "how many times the block schedule was repeated per evaluation; one "
        "pass everywhere in V4, kept because it is what the removed repeated-"
        "schedule arm would have changed"
    ),
    "module_solve_totals.inner_sweeps_by_block": (
        "sweeps per block: the three blocks by name on a partitioned arm, the "
        "single block 'FLAT' on a flat arm, and nothing at all on the "
        "reference arm"
    ),
    "n_solver_iterations": "the optimiser's iteration count on its final attempt",
    "mfile.ifail": "the optimiser's exit code as PROCESS's own output file reports it",
    "exit_forensics.n_solver_iterations_summed_over_attempts": (
        "iterations summed over every optimiser attempt, failed attempts "
        "included: the second of check 2's two constructions"
    ),
    "exit_forensics.n_attempts": (
        "optimiser attempts; a retry is a robustness event and a cost, and the "
        "plan publishes the cost ratio with and without retried seeds.  0 in "
        "the evaluation phase, where no optimiser runs"
    ),
    "exit_forensics.attempts[].n_solver_iterations": (
        "iterations of each attempt in order, so the summed construction can "
        "be checked against its parts rather than trusted"
    ),
}

#: Fields compared here that the harness plan's §7.1 list does not name
#: literally **for that phase**, with the reason.  Keyed by phase, because
#: the same field can be the plan's for one phase and this module's addition
#: for the other.  Recorded rather than absorbed: a gate that quietly
#: compares more than it declares is as hard to read as one that quietly
#: compares less.
FIELDS_BEYOND_THE_PLAN: dict[str, dict[str, str]] = {
    "B": {},
    "A": {
        "exact.objf": (
            "§7.1 names exact.norm_objf, which no evaluation-phase record "
            "carries — that phase spells the same quantity 'objf'.  Without "
            "it the evaluation phase would reproduce on counts alone, with no "
            "bit-comparison of the objective at all"
        ),
        "exit_forensics.n_attempts": (
            "§7.1 names it for the optimisation phase only.  Every "
            "evaluation-phase record carries it as 0, and comparing it states "
            "as a value what would otherwise be an assumption: that the "
            "evaluation entry point starts no optimiser"
        ),
    },
}


#: Fields the committed reference **holds** and the gate no longer **compares**,
#: with the reason, keyed by phase.  The committed file is never regenerated —
#: it is the previous revision's own numbers and re-extracting it would be
#: re-writing the thing being reproduced — so a field leaves the comparison by
#: being named here, and the name, the reason and the resulting count all
#: travel in the gate's verdict.
#:
#: The live entry is ruling **D25**.  The exit audit now restores the data
#: structure to its solve-phase state before its sweep, so the sweep evaluates
#: the map the loop iterated; the previous revision's audit did not, and on the
#: optimisation phase its sweep ran on the mesh PROCESS's output path had
#: already changed (task A61 (insstrain-diagnosis) measured that mesh: the
#: TF-coil stress discretisation, raised 100 → 500 and never put back).  The
#: two numbers are therefore made by two instruments.  This gate reproduces a
#: measurement; it cannot reproduce an instrument it has deliberately replaced,
#: and pretending otherwise would mean either keeping the defect or tuning the
#: gate — so the field is named out, with its reason, and the count says so.
#:
#: **The evaluation phase keeps it**, and that is a measurement rather than an
#: oversight: that phase evaluates the model set once and never enters the
#: output path, so there is nothing for the restore to put back and the two
#: instruments produce the same number.  Its six residuals reproduce bit for
#: bit after the change.  Dropping them too would remove a comparison that
#: works, on the strength of a reason that does not apply to them.
FIELDS_NOT_COMPARED: dict[str, dict[str, str]] = {
    "B": {
        "exit_audit.residual_max_hex": (
            "an instrument value, not a measurement this experiment compares "
            "on.  The previous revision's optimisation-phase audit swept from "
            "the state PROCESS's output path left, on the discretisation that "
            "path had already changed; this revision's puts the data "
            "structure back to its solve-phase state first, so its sweep is "
            "the loop's own map.  The residual is published per run on both "
            "rulers and is compared between arms and between rulers wherever "
            "one instrument made both sides — here it would compare two "
            "instruments"
        ),
    },
    "A": {},
}


def compared_fields(phase: str) -> tuple[str, ...]:
    """The fields gate GR compares for *phase*: what the reference holds, less
    what :data:`FIELDS_NOT_COMPARED` names."""
    dropped = FIELDS_NOT_COMPARED.get(phase, {})
    return tuple(f for f in REFERENCE_FIELDS[phase] if f not in dropped)


# --------------------------------------------------------------------------
# the reference set (harness plan §7.1)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ReferenceRun:
    """One run of the reference set: which arm, which configuration, which seed."""

    arm: str
    configuration: str
    seed: int
    phase: str
    #: Which row of the plan's reference table this run belongs to.
    group: str

    @property
    def key(self) -> str:
        """A short, stable name for this run, used in messages and records."""
        return f"{self.arm}/{self.configuration}/seed{self.seed:03d}"

    @property
    def previous_arm(self) -> str:
        """What the previous revision called this arm."""
        return previous_arm_name(self.arm)


#: The reference table of harness plan §7.1, as data.  One tuple per row:
#: (phase, arm, seed, whether the row is restricted to pulsed configurations,
#: the row's label).  The configurations themselves come from the campaign,
#: never from a list written here — every population in this experiment
#: re-derives from :attr:`Campaign.population` (trap T11).
_REFERENCE_TABLE: tuple[tuple[str, str, int, bool, str], ...] = (
    ("B", "BR", 0, False, "optimisation, unperturbed seed, reference arm"),
    ("B", "B0", 0, False, "optimisation, unperturbed seed, flat control"),
    ("B", "B2", 0, False, "optimisation, unperturbed seed, partitioned arm"),
    ("A", "A0", 1, False, "evaluation, first perturbed seed, flat control"),
    ("A", "A2", 1, False, "evaluation, first perturbed seed, partitioned arm"),
    ("B", "B2", 1, False, "optimisation, first perturbed seed, partitioned arm"),
    (
        "B",
        "B1",
        1,
        True,
        "optimisation, first perturbed seed, lifted design vector "
        "(pulsed configurations only)",
    ),
)


def reference_set(campaign: Campaign | None = None) -> tuple[ReferenceRun, ...]:
    """The twenty reference runs, in the plan's order.

    The last row is restricted to the pulsed configurations because the arm
    whose design vector the optimiser owns degenerates onto the flat control
    where there is no burn-time coupling, and the previous revision did not
    run it there.  That restriction is read from the configuration's own
    recorded skip, not written here a second time.
    """
    campaign = campaign or default_campaign()
    runs: list[ReferenceRun] = []
    for phase, arm, seed, pulsed_only, group in _REFERENCE_TABLE:
        for config in campaign.configurations:
            if pulsed_only and not config.pulsed:
                continue
            runs.append(ReferenceRun(arm, config.name, seed, phase, group))
    return tuple(runs)


def absent_from_the_reference_set(campaign: Campaign | None = None) -> dict[str, str]:
    """Arm/configuration pairs of the plan's table that are deliberately absent.

    Stated rather than inferred from a smaller count: an absence nobody wrote
    down reads as an omission.
    """
    campaign = campaign or default_campaign()
    absent: dict[str, str] = {}
    for phase, arm, seed, pulsed_only, _group in _REFERENCE_TABLE:
        if not pulsed_only:
            continue
        for config in campaign.configurations:
            if config.pulsed:
                continue
            absent[f"{arm}/{config.name}/seed{seed:03d}"] = config.skips.get(
                arm,
                "the configuration has no burn-time coupling, so the arm "
                "composes onto its predecessor",
            ) + "; the previous revision did not run it"
    return absent


# --------------------------------------------------------------------------
# the name map (harness plan §7.3, tooth "bad name map")
# --------------------------------------------------------------------------

#: V4 arm -> the previous revision's name for it.  The registry holds the map
#: the other way round; it is inverted here rather than written twice.  Since
#: the renaming of 2026-09-15 it reads ``{"BR": "R", "A2": "A1", "B2": "B3"}``:
#: the right-hand sides are V3's spellings.
PREVIOUS_NAME_BY_ARM: dict[str, str] = {
    v4: previous for previous, v4 in sw.PREVIOUS_ARM_NAMES.items()
}

#: V4 arms the previous revision never ran, and the gate that covers each
#: instead (harness plan §7.5).  Asking for one of these by name is a
#: refusal, not an empty result: GR's coverage boundary is stated, never
#: inferred from an arm's absence.
ARMS_WITHOUT_PREVIOUS_RECORDS: dict[str, str] = {
    "AR": (
        "the previous revision had no evaluation-phase reference arm.  "
        "Covered instead by a G1-shape check: one evaluation with every "
        "architecture switch cleared must reproduce the first call_models of "
        "BR at seed 0 on that call's node calls, sweeps and objective hex"
    ),
    "A1": (
        "the previous revision never ran the flat arm with the burn time "
        "owned by a constant.  Covered instead by the warm-equivalence gate "
        "G6: pinned at the reference's converged burn time it must reproduce "
        "the reference fixed point, cross-state residual below the tolerance "
        "and the pinned component bit-identical"
    ),
}


def previous_arm_names() -> frozenset[str]:
    """Every arm name the previous revision's run directories can carry.

    Derived, not listed: the arms V4 kept under the same name, the arms it
    renamed, and the arms it retired.  A V4-only arm is not in here, which is
    what makes asking for one a refusal rather than a missing directory.
    """
    kept = {
        name
        for name in arms_mod.ARMS
        if name not in PREVIOUS_NAME_BY_ARM
        and name not in ARMS_WITHOUT_PREVIOUS_RECORDS
    }
    return frozenset(kept | set(sw.PREVIOUS_ARM_NAMES) | set(sw.RETIRED_ARM_NAMES))


def previous_arm_name(arm: str) -> str:
    """The previous revision's name for V4 arm *arm*.

    Raises rather than returning the name unchanged when the previous
    revision had no such arm.  A lookup that misses must raise: a reference a
    gate cannot find has to refuse, never pass over an empty comparison
    (trap T11).
    """
    if arm in PREVIOUS_NAME_BY_ARM:
        return PREVIOUS_NAME_BY_ARM[arm]
    if arm in ARMS_WITHOUT_PREVIOUS_RECORDS:
        raise ReferenceError(
            f"{arm!r} has no record in the previous revision: "
            f"{ARMS_WITHOUT_PREVIOUS_RECORDS[arm]}"
        )
    if arm in sw.RETIRED_ARM_NAMES:
        raise ReferenceError(
            f"{arm!r} is an arm the previous revision ran and V4 has retired; "
            f"it is not part of any V4 comparison.  Retired: "
            f"{', '.join(sw.RETIRED_ARM_NAMES)}"
        )
    if arm in arms_mod.ARMS:
        return arm
    raise ReferenceError(
        f"{arm!r} is not an arm of this experiment; the arms are "
        f"{', '.join(arms_mod.MATRIX_ORDER)}"
    )


def assert_previous_arm_name(name: str) -> str:
    """Refuse *name* unless the previous revision's records can carry it.

    *name* is read in the **previous revision's** namespace: ``"B2"`` here is
    V3's retired joint-test arm, not V4's partitioned optimisation arm, which
    V3 spelled ``"B3"``.  Go through :func:`previous_arm_name` to translate a
    V4 name first.

    This is the guard the reference extraction goes through, and it is what
    makes the renamed reference arm's V4 name illegal here: the previous
    revision's directories are named ``R``, and reaching for ``BR`` without
    the map would build a path to a directory that never existed and then
    report "missing record" for a name error.
    """
    if name in previous_arm_names():
        return name
    hint = ""
    if name in PREVIOUS_NAME_BY_ARM:
        hint = (
            f"  {name!r} is this revision's name for it; the previous "
            f"revision called it {PREVIOUS_NAME_BY_ARM[name]!r}.  Go through "
            f"previous_arm_name()."
        )
    elif name in ARMS_WITHOUT_PREVIOUS_RECORDS:
        hint = f"  {ARMS_WITHOUT_PREVIOUS_RECORDS[name]}"
    raise ReferenceError(
        f"{name!r} is not a name the previous revision's records carry; those "
        f"are {', '.join(sorted(previous_arm_names()))}.{hint}"
    )


# --------------------------------------------------------------------------
# reading the committed file
# --------------------------------------------------------------------------


def load(path: Path | None = None) -> dict[str, Any]:
    """The committed reference.  An absent file raises; it is never an empty set."""
    path = Path(path or REFERENCE_PATH)
    if not path.exists():
        raise ReferenceError(
            f"the reproduction reference is not committed at {path}.  It was "
            f"extracted once from the previous revision's records and "
            f"committed (its provenance block says from where and when); the "
            f"gate reads the committed file and nothing regenerates it (D25)."
        )
    document = json.loads(path.read_text())
    if document.get("format") != FORMAT:
        raise ReferenceError(
            f"{path} is in format {document.get('format')!r}, not {FORMAT!r}"
        )
    naming = (document.get("provenance") or {}).get(records_mod.ARM_NAMING_FIELD)
    if naming != records_mod.ARM_NAMING:
        raise ReferenceError(
            f"{path} writes its V4 arm names in naming scheme {naming!r}, not "
            f"{records_mod.ARM_NAMING!r}: its 'arm' fields would not match the "
            f"arms the gate composes today (records.RECORDED_ARM_NAMES).  "
            f"Bring the committed file to today's names with "
            f"`reference.py --rename-arms` and press the gate once; the file is "
            f"not read under a guess."
        )
    return document


def rename_arms(path: Path | None = None) -> dict[str, Any]:
    """Rewrite the committed file's ``arm`` fields into today's names.

    The **names-only** regeneration for the arm renaming of 2026-09-15
    (``records.RECORDED_ARM_NAMES``): each entry's ``arm`` — V4's name — goes
    through the table; ``previous_arm``, ``source_path``, ``source_sha256``,
    ``tree_git_head`` and every compared value are V3's and are not touched.
    Provenance blocks keyed by V4 arm name (per-arm prose) are re-keyed; the
    provenance block gains the naming stamp :func:`load` requires and a
    dated note.  Refuses a file already in today's scheme, so it cannot be
    applied twice and translate ``A1`` a second time.  Returns what changed.
    """
    path = Path(path or REFERENCE_PATH)
    document = json.loads(path.read_text())
    if document.get("format") != FORMAT:
        raise ReferenceError(
            f"{path} is in format {document.get('format')!r}, not {FORMAT!r}"
        )
    provenance = document.setdefault("provenance", {})
    if provenance.get(records_mod.ARM_NAMING_FIELD) == records_mod.ARM_NAMING:
        raise ReferenceError(
            f"{path} already writes its arm names in {records_mod.ARM_NAMING!r}; "
            f"applying the table again would rename today's arms a second time"
        )
    changed: dict[str, int] = {}
    for entry in document["entries"]:
        old = entry["arm"]
        new = records_mod.RECORDED_ARM_NAMES.get(old, old)
        if new != old:
            entry["arm"] = new
            changed[f"{old} -> {new}"] = changed.get(f"{old} -> {new}", 0) + 1
    absent = provenance.get("absent_from_the_set")
    if isinstance(absent, Mapping):
        renamed_absent: dict[str, Any] = {}
        for key, why in absent.items():
            arm, rest = key.split("/", 1)
            renamed_absent[f"{records_mod.RECORDED_ARM_NAMES.get(arm, arm)}/{rest}"] = why
        provenance["absent_from_the_set"] = renamed_absent
    # Provenance blocks keyed by V4 arm name -- prose per arm, such as
    # ``block_solver_field_applicability`` and ``not_covered_by_this_reference``.
    # A block whose every key is an arm name (today's or a recorded one) is
    # re-keyed; the prose is not touched.
    arm_names = set(records_mod.RECORDED_ARM_NAMES) | set(arms_mod.ARMS)
    for name, block in list(provenance.items()):
        if (
            isinstance(block, Mapping)
            and block
            and all(isinstance(k, str) and k in arm_names for k in block)
        ):
            rekeyed = {
                records_mod.RECORDED_ARM_NAMES.get(k, k): v for k, v in block.items()
            }
            if list(rekeyed) != list(block):
                provenance[name] = rekeyed
                changed[f"provenance.{name} keys"] = sum(
                    1 for k in block if records_mod.RECORDED_ARM_NAMES.get(k, k) != k
                )
    provenance[records_mod.ARM_NAMING_FIELD] = records_mod.ARM_NAMING
    provenance["arm_names_note"] = (
        "the 'arm' fields were rewritten into the matrix's names of 2026-09-15 "
        "by reference.py --rename-arms (task A78 (arm-renames)) through "
        "records.RECORDED_ARM_NAMES; 'previous_arm', 'source_path' and every "
        "compared value are the previous revision's and were not touched"
    )
    path.write_text(json.dumps(document, indent=2) + "\n")
    return {"path": str(path), "entries": len(document["entries"]), "changed": changed}


def lookup(
    arm: str,
    configuration: str,
    seed: int,
    *,
    document: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """The reference entry for one run; raises if the set does not hold it.

    This is what the run path's GR comparator calls: it hands over the arm as
    **V4** names it, and the entry carries both names, the compared field
    values and the source record's identity.
    """
    previous_arm_name(arm)  # refuses a retired or record-less arm by name
    document = document or load()
    for entry in document["entries"]:
        if (
            entry["arm"] == arm
            and entry["configuration"] == configuration
            and entry["seed"] == seed
        ):
            return entry
    absent = absent_from_the_reference_set()
    key = f"{arm}/{configuration}/seed{seed:03d}"
    raise ReferenceError(
        f"the reproduction reference has no entry for {key}."
        + (f"  {absent[key]}" if key in absent else "")
        + f"  It holds {len(document['entries'])} entries: "
        + ", ".join(
            sorted(
                {f"{e['arm']}/seed{e['seed']:03d}" for e in document["entries"]}
            )
        )
    )


# --------------------------------------------------------------------------
# reporting and entry point
# --------------------------------------------------------------------------


def summary(document: Mapping[str, Any]) -> list[str]:
    """The lines the runner prints about the committed reference."""
    provenance = document["provenance"]
    source = provenance["source_revision"]
    lines = [
        f"  {len(document['entries'])} entries, "
        f"{sum(len(e['fields']) for e in document['entries'])} compared field "
        f"values",
        f"  source     {source['name']} at {source['campaign_commit'][:12]}",
        f"  extracted  {provenance['extracted_on']} from {source['runs_root']}",
        f"  population {provenance['population']}",
    ]
    for key, why in provenance.get("absent_from_the_set", {}).items():
        lines.append(f"  absent     {key} — {why}")
    for arm, why in provenance.get("not_covered_by_this_reference", {}).items():
        lines.append(f"  not covered {arm} — {why.splitlines()[0]}")
    return lines


def tables(document: Mapping[str, Any]) -> str:
    """The report's tables, emitted by the same script that made the numbers.

    A table is never written by hand from a JSON read at a shell prompt: the
    figures a report cites come out of a committed script, and so does the
    caption that says what population they are over (protocol §15 and §16).
    """
    provenance = document["provenance"]
    source = provenance["source_revision"]
    out: list[str] = []

    out.append(
        f"*Caption: the {len(document['entries'])} entries of the committed "
        f"reproduction reference — one row per reference run of harness plan "
        f"§7.1. \"Arm\" is this revision's name and \"previous\" the name the "
        f"record directory carries; \"seed\" 0 is the unperturbed start and 1 "
        f"the first perturbed one. \"sha256\" is the first 12 characters of "
        f"the source record file's digest. The two value columns are examples "
        f"of the compared fields, not the whole set: the committed file holds "
        f"{len(REFERENCE_FIELDS['B'])} fields per optimisation record and "
        f"{len(REFERENCE_FIELDS['A'])} per evaluation record, of which the "
        f"gate compares {len(compared_fields('B'))} and "
        f"{len(compared_fields('A'))} — the difference is named, with its "
        f"reason, in FIELDS_NOT_COMPARED. Node calls are model executions "
        f"during the solve "
        f"(optimisation phase) or in the one evaluation (evaluation phase); "
        f"the objective is a hex float, exact. Population: "
        f"{provenance['population']}, every record at {source['name']} commit "
        f"`{source['campaign_commit'][:8]}`.*"
    )
    out.append("")
    out.append(
        "| arm | previous | configuration | phase | seed | sha256 | node calls "
        "| objective (hex) |"
    )
    out.append("|---|---|---|---|---|---|---:|---|")
    for entry in document["entries"]:
        fields = entry["fields"]
        if entry["phase"] == "B":
            calls = fields["node_calls_solve_phase"]
            objective = fields["exact.norm_objf"]
        else:
            calls = fields["node_calls_single_eval"]
            objective = fields["exact.objf"]
        out.append(
            f"| `{entry['arm']}` | `{entry['previous_arm']}` | "
            f"{entry['configuration']} | {entry['phase']} | {entry['seed']} | "
            f"`{entry['source_sha256'][:12]}` | {calls} | `{objective}` |"
        )

    out.append("")
    out.append(
        "*Caption: the compared fields, per phase, with the number of records "
        "carrying each. Every field was enumerated from the records rather "
        "than assumed; a field the plan names for a phase that a record does "
        "not carry is a refusal naming the record and the field, so every "
        "denominator below is also the check. \"beyond the plan\" marks a "
        "field harness plan §7.1 does not name literally.*"
    )
    out.append("")
    out.append("| phase | field | carried by | beyond the plan |")
    out.append("|---|---|---:|---|")
    for phase, block in provenance["field_population"].items():
        label = "B (optimisation)" if phase == "B" else "A (evaluation)"
        beyond_here = provenance["compared_fields_beyond_the_plan"].get(phase, {})
        for name, carried in block["carried_by"].items():
            beyond = "yes" if name in beyond_here else ""
            out.append(
                f"| {label} | `{name}` | {carried} / {block['n_records']} | "
                f"{beyond} |"
            )
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    stage = parser.add_mutually_exclusive_group(required=True)
    stage.add_argument(
        "--show",
        action="store_true",
        help="print what the committed reference holds and what it does not "
        "cover",
    )
    stage.add_argument(
        "--tables",
        action="store_true",
        help="emit the report's two tables, with their captions, from the "
        "committed reference",
    )
    stage.add_argument(
        "--rename-arms",
        action="store_true",
        help="rewrite the committed file's V4 'arm' fields into today's names "
        "through records.RECORDED_ARM_NAMES and stamp the naming scheme; "
        "names only, refused if already done.  The gate that reads the file "
        "is then pressed once",
    )
    parser.add_argument(
        "--path",
        type=Path,
        help=f"read this file instead of the committed one ({REFERENCE_PATH})",
    )
    args = parser.parse_args(argv)
    if args.rename_arms:
        try:
            outcome = rename_arms(args.path)
        except ReferenceError as exc:
            print(f"[FAIL] {exc}")
            return 3
        print(
            f"{outcome['path']}: {outcome['entries']} entries; arm fields "
            f"renamed {outcome['changed'] or 'none'}; stamped "
            f"{records_mod.ARM_NAMING_FIELD}={records_mod.ARM_NAMING!r}"
        )
        return 0
    try:
        document = load(args.path)
    except ReferenceError as exc:
        print(f"[FAIL] {exc}")
        return 3
    if args.tables:
        print(tables(document))
        return 0
    print("=" * 74)
    print("reproduction reference — what is committed")
    print("=" * 74)
    for line in summary(document):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
