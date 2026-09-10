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

Two stages, both reachable from ``experiment_runner.py`` so that their
failure paths are as reproducible as their successes (protocol §15):

``extract``
    Read the twenty records under a ``--previous-runs`` root and write the
    committed file.  A missing record is a **refusal**, never a skip.  A
    record that does not carry a field the harness plan names for its phase
    is a refusal that names the record and the field.  A record made at any
    commit other than the previous revision's campaign commit is a refusal.

``verify``
    Re-derive the file from the live records and require **byte-for-byte**
    equality with the committed one.  A missing record is a FAIL, not a skip;
    an absent committed file is a FAIL, not a skip.

And ``--teeth``: four deliberate breaks, each of which must make one of those
two stages refuse.  A check that has never been shown to fail is an
assertion, not a measurement (protocol §12).

The entry schema
----------------

The committed file is ``{"format", "provenance", "entries"}``.  Each entry
is::

    {
      "arm":            V4's name for the arm            ("BR")
      "previous_arm":   the previous revision's name      ("R")
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
import hashlib
import json
import shutil
import sys
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Sequence

_EXPERIMENT_DIR = Path(__file__).resolve().parent.parent
if str(_EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(_EXPERIMENT_DIR))

from harness import arms as arms_mod  # noqa: E402
from harness import switches as sw  # noqa: E402
from harness.config import REPO_ROOT, Campaign, default_campaign  # noqa: E402
from harness.selfcheck import Check  # noqa: E402

#: This file's directory.
HERE = Path(__file__).resolve().parent

#: Where the committed reference lives.  The name says what the file is, not
#: which revision produced it (harness plan §11.1).
REFERENCE_PATH = HERE / "reference" / "reproduction_reference.json"

#: Schema tag, so a later change to the entry shape is visible rather than
#: silently absorbed by a reader that expected the old one.
FORMAT = "reproduction-reference-1"

#: Where the previous revision's records sit, relative to a repository root.
#: They are untracked bulk: present in the main checkout, absent from a task
#: worktree.  The extraction is therefore pointed at a root explicitly, and
#: the root it used is recorded in the file.
PREVIOUS_RUNS_SUBPATH = (
    Path("arch_surgery") / "MDA_partitioning_experiment_v3" / "runs"
)

#: The commit the previous revision's campaign ran at.  Every one of the
#: twenty records must carry it; a record made anywhere else is not part of
#: that campaign and is refused rather than quietly averaged in.
PREVIOUS_CAMPAIGN_COMMIT = "362c0b47dffcbfb8747338134a82d11985761d46"

#: How the previous revision named a seed's run directory.  Its Phase B
#: "start000" is seed 0 and its Phase A "start001" is seed 1; the word in V4
#: is **seed**, in both phases (harness plan §11.2).
_SEED_DIRECTORY = "start{seed:03d}"

#: The previous revision's phase directories.
_PHASE_DIRECTORY = {"A": "phase_a", "B": "phase_b"}


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

#: Why each field is compared, in one line.  Kept beside the list so that a
#: reader of the committed file does not have to open the plan to know what
#: a cell means.
FIELD_NOTES: dict[str, str] = {
    "node_calls_solve_phase": (
        "model executions during the solve, the cost unit of every Phase B "
        "table; excludes the output-time and audit sweeps"
    ),
    "node_calls_total": "model executions including the output-time and audit sweeps",
    "n_model_calls": "call_models evaluations the optimiser asked for",
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

    @property
    def source_path(self) -> Path:
        """The record's path, relative to a runs root."""
        return (
            Path(_PHASE_DIRECTORY[self.phase])
            / "campaign"
            / self.configuration
            / self.previous_arm
            / _SEED_DIRECTORY.format(seed=self.seed)
            / "metrics.json"
        )


#: The reference table of harness plan §7.1, as data.  One tuple per row:
#: (phase, arm, seed, whether the row is restricted to pulsed configurations,
#: the row's label).  The configurations themselves come from the campaign,
#: never from a list written here — every population in this experiment
#: re-derives from :attr:`Campaign.population` (trap T11).
_REFERENCE_TABLE: tuple[tuple[str, str, int, bool, str], ...] = (
    ("B", "BR", 0, False, "optimisation, unperturbed seed, reference arm"),
    ("B", "B0", 0, False, "optimisation, unperturbed seed, flat control"),
    ("B", "B3", 0, False, "optimisation, unperturbed seed, partitioned arm"),
    ("A", "A0", 1, False, "evaluation, first perturbed seed, flat control"),
    ("A", "A1", 1, False, "evaluation, first perturbed seed, partitioned arm"),
    ("B", "B3", 1, False, "optimisation, first perturbed seed, partitioned arm"),
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
#: the other way round; it is inverted here rather than written twice.
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
    "A0p": (
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
# reading one record
# --------------------------------------------------------------------------


def _resolve(record: Mapping[str, Any], path: str) -> Any:
    """The value at dotted *path*, or raise :class:`KeyError` naming what is missing.

    ``attempts[].n_solver_iterations`` maps over a list and takes the named
    key from each element, so a per-attempt column is one field rather than a
    variable number of them.
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


def sha256_of(path: Path) -> str:
    """The sha256 of a file's bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_entry(run: ReferenceRun, runs_root: Path) -> dict[str, Any]:
    """One entry of the committed reference, read from one live record.

    Three refusals, each of which would otherwise become a silent hole in the
    gate: the record is not there; the record was made at a different commit
    from the rest of the campaign; the record does not carry a field the plan
    names for its phase.
    """
    assert_previous_arm_name(run.previous_arm)
    path = Path(runs_root) / run.source_path
    if not path.exists():
        raise ReferenceError(
            f"missing record for {run.key}: {path} does not exist.  A missing "
            f"record is a refusal, not a skip — a gate computed over a "
            f"population smaller than the one it names is how a zero gets "
            f"published over nothing (trap T11)."
        )
    digest = sha256_of(path)
    try:
        record = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ReferenceError(f"unreadable record for {run.key}: {path}: {exc}") from exc

    head = record.get("tree_git_head")
    if head != PREVIOUS_CAMPAIGN_COMMIT:
        raise ReferenceError(
            f"{run.key}: the record at {path} was made at commit {head!r}, not "
            f"at the previous revision's campaign commit "
            f"{PREVIOUS_CAMPAIGN_COMMIT}.  A record from another commit is "
            f"not part of that campaign and is refused rather than mixed in."
        )

    fields: dict[str, Any] = {}
    for name in REFERENCE_FIELDS[run.phase]:
        try:
            fields[name] = _resolve(record, name)
        except KeyError as exc:
            raise ReferenceError(
                f"{run.key}: the record at {path} does not carry the compared "
                f"field {name!r} (missing at {exc.args[0]}).  A missing field "
                f"is a refusal, not a skip: the gate would otherwise compare "
                f"fewer things than it says it does."
            ) from exc

    return {
        "arm": run.arm,
        "previous_arm": run.previous_arm,
        "configuration": run.configuration,
        "phase": run.phase,
        "seed": run.seed,
        "group": run.group,
        "source_path": run.source_path.as_posix(),
        "source_sha256": digest,
        "tree_git_head": head,
        "fields": fields,
    }


# --------------------------------------------------------------------------
# building the whole document
# --------------------------------------------------------------------------


def _field_population(entries: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Per phase, how many records carry each compared field.

    Every count in this experiment carries the number of things it was taken
    over (protocol §12).  Here that number is also the check: a field present
    on fewer records than the phase has is a refusal upstream of this
    function, so every entry below reads ``n / n``.
    """
    population: dict[str, Any] = {}
    for phase, names in REFERENCE_FIELDS.items():
        of_phase = [e for e in entries if e["phase"] == phase]
        population[phase] = {
            "n_records": len(of_phase),
            "n_fields": len(names),
            "carried_by": {
                name: sum(1 for e in of_phase if name in e["fields"]) for name in names
            },
        }
    return population


def _applicability(entries: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    """What the block-solver fields mean on arms that never enter a block solver.

    The reference arm runs upstream's own loop, so its block-solver totals are
    present in the record and empty: no evaluations, no sweeps, no
    histograms.  That is recorded here as the *value it has*, and compared
    like any other value — never omitted, because an omitted field and a zero
    field are the two things a reader must be able to tell apart.
    """
    notes: dict[str, str] = {}
    for entry in entries:
        arm = entry["arm"]
        if arm in notes:
            continue
        blocks = entry["fields"].get("module_solve_totals.inner_sweeps_by_block")
        calls = entry["fields"].get("module_solve_totals.n_call_models")
        if not blocks:
            notes[arm] = (
                "the block solver is never entered on this arm (upstream's own "
                f"loop runs instead), so module_solve_totals is present and "
                f"empty: n_call_models = {calls}, no per-block histogram.  "
                "Compared as the value it has, not omitted"
            )
        elif list(blocks) == ["FLAT"]:
            notes[arm] = (
                "one block over every in-loop node, so the per-block histogram "
                "has the single entry 'FLAT'.  This is the flat arm's shape, "
                "not a missing partition"
            )
        else:
            notes[arm] = (
                "the partitioned arm: one entry per block in the schedule "
                f"({', '.join(blocks)})"
            )
    return notes


def build(
    runs_root: Path,
    *,
    extracted_on: str,
    campaign: Campaign | None = None,
) -> dict[str, Any]:
    """The whole committed document, derived from the live records.

    *extracted_on* is a parameter rather than today's date so that
    re-derivation is a pure function of the records: ``verify`` re-derives
    with the date the committed file already carries, and the byte comparison
    then measures the records and nothing else.
    """
    campaign = campaign or default_campaign()
    runs_root = Path(runs_root)
    runs = reference_set(campaign)
    entries = [extract_entry(run, runs_root) for run in runs]

    n_optimisations = sum(1 for e in entries if e["phase"] == "B")
    n_evaluations = sum(1 for e in entries if e["phase"] == "A")

    return {
        "format": FORMAT,
        "provenance": {
            "what": (
                "the compared fields of the previous revision's twenty "
                "reference runs, committed so that gate GR does not depend on "
                "untracked run records"
            ),
            "gate": "GR (harness plan §7): the rewritten harness, driving the "
            "experiment's own copy of PROCESS before any driver change, must "
            "reproduce these values bit for bit",
            "written_by": "harness/reference.py (task A49 (harness-reference))",
            "extracted_on": extracted_on,
            "source_revision": {
                "name": "MDA_partitioning_experiment_v3",
                "campaign_commit": PREVIOUS_CAMPAIGN_COMMIT,
                "runs_root": str(runs_root),
                "why_absolute": (
                    "the records are untracked bulk and live only in the main "
                    "checkout; naming the directory the numbers were read from "
                    "is the point of recording it"
                ),
            },
            "population": (
                f"{len(entries)} records = {n_optimisations} optimisations + "
                f"{n_evaluations} evaluations, over the "
                f"{len(campaign.configurations)} configurations "
                f"{', '.join(campaign.population)}; "
                "seed 0 is the unperturbed start and seed 1 the first "
                "perturbed one"
            ),
            "configurations": list(campaign.population),
            "absent_from_the_set": absent_from_the_reference_set(campaign),
            "compared_fields": {
                phase: list(names) for phase, names in REFERENCE_FIELDS.items()
            },
            "compared_fields_why": FIELD_NOTES,
            "compared_fields_beyond_the_plan": FIELDS_BEYOND_THE_PLAN,
            "field_population": _field_population(entries),
            "block_solver_field_applicability": _applicability(entries),
            "not_covered_by_this_reference": ARMS_WITHOUT_PREVIOUS_RECORDS,
            "how_to_re_derive": (
                "python harness/reference.py --extract --previous-runs "
                "<repo>/arch_surgery/MDA_partitioning_experiment_v3/runs; "
                "python harness/reference.py --verify re-derives it and "
                "requires byte-for-byte equality"
            ),
        },
        "entries": entries,
    }


def serialise(document: Mapping[str, Any]) -> str:
    """The document's committed text.  One spelling, so bytes can be compared."""
    return json.dumps(document, indent=2, ensure_ascii=True) + "\n"


# --------------------------------------------------------------------------
# reading the committed file
# --------------------------------------------------------------------------


def load(path: Path | None = None) -> dict[str, Any]:
    """The committed reference.  An absent file raises; it is never an empty set."""
    path = Path(path or REFERENCE_PATH)
    if not path.exists():
        raise ReferenceError(
            f"the reproduction reference is not committed at {path}.  It is "
            f"produced by 'harness/reference.py --extract --previous-runs "
            f"<root>' and committed; the gate reads the committed file, never "
            f"the untracked records directly."
        )
    document = json.loads(path.read_text())
    if document.get("format") != FORMAT:
        raise ReferenceError(
            f"{path} is in format {document.get('format')!r}, not {FORMAT!r}"
        )
    return document


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
# stage: extract
# --------------------------------------------------------------------------


def default_previous_runs_root() -> Path:
    """Where this checkout would look for the previous revision's records.

    A task worktree has no such directory — the records are untracked bulk
    and exist only in the main checkout — so the default is the path that
    *would* hold them and the refusal names it.  Guessing at another checkout
    would read numbers nobody asked for.
    """
    return REPO_ROOT / PREVIOUS_RUNS_SUBPATH


def stage_extract(
    *,
    runs_root: Path | None = None,
    out_path: Path | None = None,
    extracted_on: str | None = None,
    campaign: Campaign | None = None,
) -> tuple[int, dict[str, Any]]:
    """Write the committed reference from the live records.  0 written, 3 refused."""
    runs_root = Path(runs_root or default_previous_runs_root())
    out_path = Path(out_path or REFERENCE_PATH)
    extracted_on = extracted_on or date.today().isoformat()
    check = Check(
        name="reference extraction",
        binds="the twenty reference runs of harness plan §7.1, at the previous "
        "revision's campaign commit",
        population=f"records under {runs_root}",
    )
    if not runs_root.exists():
        check.fail(
            f"no such runs root: {runs_root}.  The previous revision's records "
            f"are untracked bulk and live in the main checkout; point "
            f"--previous-runs at it."
        )
        return 3, check.as_record()
    try:
        document = build(runs_root, extracted_on=extracted_on, campaign=campaign)
    except ReferenceError as exc:
        check.fail(str(exc))
        return 3, check.as_record()
    text = serialise(document)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text)
    check.n_compared = len(document["entries"])
    check.note(f"wrote {out_path} ({len(text)} bytes)")
    check.note(document["provenance"]["population"])
    record = check.as_record()
    record["path"] = str(out_path)
    record["bytes"] = len(text)
    record["sha256"] = hashlib.sha256(text.encode()).hexdigest()
    record["provenance"] = document["provenance"]
    return 0, record


# --------------------------------------------------------------------------
# stage: verify
# --------------------------------------------------------------------------


def _first_difference(a: str, b: str) -> str:
    """Where two texts first differ, with a little context on both sides."""
    limit = min(len(a), len(b))
    index = next((i for i in range(limit) if a[i] != b[i]), limit)
    lo, hi = max(0, index - 60), index + 60
    return (
        f"first difference at byte {index} of {len(a)} (committed) / "
        f"{len(b)} (re-derived)\n"
        f"    committed  : ...{a[lo:hi]!r}...\n"
        f"    re-derived : ...{b[lo:hi]!r}..."
    )


def _field_differences(
    committed: Mapping[str, Any], rederived: Mapping[str, Any]
) -> list[str]:
    """A readable account of what moved, entry by entry and field by field."""
    def index(document: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
        return {
            f"{e['arm']}/{e['configuration']}/seed{e['seed']:03d}": e
            for e in document.get("entries", [])
        }

    left, right = index(committed), index(rederived)
    lines: list[str] = []
    for key in sorted(set(left) - set(right)):
        lines.append(f"{key}: in the committed file, absent from the re-derivation")
    for key in sorted(set(right) - set(left)):
        lines.append(f"{key}: re-derived, absent from the committed file")
    for key in sorted(set(left) & set(right)):
        a, b = left[key], right[key]
        for name in ("source_sha256", "source_path", "tree_git_head"):
            if a.get(name) != b.get(name):
                lines.append(f"{key}: {name} {a.get(name)!r} -> {b.get(name)!r}")
        for name in sorted(set(a["fields"]) | set(b["fields"])):
            if a["fields"].get(name, "<absent>") != b["fields"].get(name, "<absent>"):
                lines.append(
                    f"{key}: {name} {a['fields'].get(name, '<absent>')!r} -> "
                    f"{b['fields'].get(name, '<absent>')!r}"
                )
    if committed.get("provenance") != rederived.get("provenance"):
        lines.append("the provenance block differs (see the byte difference above)")
    return lines


def stage_verify(
    *,
    runs_root: Path | None = None,
    reference_path: Path | None = None,
    campaign: Campaign | None = None,
) -> tuple[int, dict[str, Any]]:
    """Re-derive the committed reference and require byte-for-byte equality.

    Returns 0 on PASS and 3 on FAIL.  Every way of not being able to compare
    — the committed file absent, the records absent, a record missing, a
    field missing — is a FAIL and never a skip.
    """
    reference_path = Path(reference_path or REFERENCE_PATH)
    check = Check(
        name="reference verification",
        binds="the committed reproduction reference re-derives byte for byte "
        "from the previous revision's live records",
    )
    try:
        committed_text = reference_path.read_text()
        committed = load(reference_path)
    except (ReferenceError, OSError, json.JSONDecodeError) as exc:
        check.fail(str(exc))
        check.population = f"the committed file at {reference_path}"
        return 3, check.as_record()

    recorded_root = committed["provenance"]["source_revision"]["runs_root"]
    runs_root = Path(runs_root or recorded_root)
    check.population = (
        f"{len(committed['entries'])} entries re-derived from {runs_root}"
    )
    if not runs_root.exists():
        check.fail(
            f"no such runs root: {runs_root}.  Verification needs the live "
            f"records; not having them is a FAIL, not a skip — a gate that "
            f"passes when its input is absent has no population."
        )
        return 3, check.as_record()

    try:
        rederived = build(
            runs_root,
            extracted_on=committed["provenance"]["extracted_on"],
            campaign=campaign,
        )
    except ReferenceError as exc:
        check.fail(str(exc))
        return 3, check.as_record()

    rederived_text = serialise(rederived)
    check.n_compared = len(committed["entries"])
    if rederived_text == committed_text:
        check.note(
            f"{len(committed_text)} bytes identical; "
            f"{check.n_compared} entries, "
            f"{sum(len(e['fields']) for e in committed['entries'])} compared "
            f"field values"
        )
        check.note(
            "the extraction date is taken from the committed file, so the "
            "comparison measures the records and nothing else"
        )
        record = check.as_record()
        record["sha256"] = hashlib.sha256(committed_text.encode()).hexdigest()
        return 0, record

    check.fail(_first_difference(committed_text, rederived_text))
    for line in _field_differences(committed, rederived)[:40]:
        check.fail(line)
    return 3, check.as_record()


# --------------------------------------------------------------------------
# teeth (harness plan §7.3; protocol §12)
# --------------------------------------------------------------------------


def _shadow_root(runs_root: Path, destination: Path, campaign=None) -> Path:
    """A throwaway copy holding only the twenty record files.

    The real runs directory is gigabytes of PROCESS output; the teeth need
    only the records, so they are copied at their own relative paths into a
    temporary tree that can be broken freely.  Nothing under the real
    directory is ever written to — it belongs to the main checkout.
    """
    for run in reference_set(campaign):
        source = Path(runs_root) / run.source_path
        target = Path(destination) / run.source_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return Path(destination)


def stage_teeth(
    *, runs_root: Path | None = None, campaign: Campaign | None = None
) -> tuple[int, dict[str, Any]]:
    """Four deliberate breaks, each of which must make a stage refuse.

    A gate whose failure mode has never been exercised is an assertion, not a
    measurement.  Two of these need the live records, so a teeth run without
    them is reported as a FAIL rather than as a pass over three teeth.
    """
    runs_root = Path(runs_root or default_previous_runs_root())
    check = Check(
        name="reference teeth",
        binds="each deliberate break makes the extraction or the verification "
        "refuse",
        population="four teeth: a missing record, a missing compared field, "
        "the name map bypassed, one changed value in the committed file",
    )

    # ---- tooth 3 first: it needs no records at all -----------------------
    refusals: list[str] = []
    for name, what in (
        ("BR", "this revision's name for the renamed reference arm"),
        ("A1u", "an arm the previous revision ran and V4 retired"),
        ("B2", "an arm the previous revision ran and V4 retired"),
    ):
        try:
            if name == "BR":
                assert_previous_arm_name(name)
            else:
                previous_arm_name(name)
        except ReferenceError as exc:
            refusals.append(f"{name} ({what}): {str(exc).splitlines()[0]}")
        else:
            refusals.append(f"{name}: DID NOT RAISE")
    caught = all("DID NOT RAISE" not in line for line in refusals)
    check.tooth(
        "name map bypassed",
        caught,
        "asking the previous revision's records for BR, A1u or B2 by name: "
        + " | ".join(refusals),
    )

    if not runs_root.exists():
        check.fail(
            f"no such runs root: {runs_root}.  Three of the four teeth need "
            f"the live records; a teeth run that cannot construct its breaks "
            f"is a FAIL, not a pass over the teeth it could run."
        )
        return 3, check.as_record()

    with tempfile.TemporaryDirectory(prefix="reference-teeth-") as tmp:
        tmp_path = Path(tmp)

        # ---- tooth 1: a missing record ------------------------------------
        root_missing = _shadow_root(runs_root, tmp_path / "missing", campaign)
        victim = reference_set(campaign)[-1]
        (root_missing / victim.source_path).unlink()
        caught, message = _must_refuse(
            lambda: build(root_missing, extracted_on="1970-01-01", campaign=campaign)
        )
        check.tooth(
            "missing record",
            caught and "missing record" in message,
            f"{victim.key}'s record removed from a throwaway copy -> {message}",
        )

        # ---- tooth 2: a compared field deleted ----------------------------
        root_field = _shadow_root(runs_root, tmp_path / "field", campaign)
        target = reference_set(campaign)[0]
        dropped = REFERENCE_FIELDS[target.phase][0]
        record_path = root_field / target.source_path
        record = json.loads(record_path.read_text())
        record.pop(dropped)
        record_path.write_text(json.dumps(record))
        caught, message = _must_refuse(
            lambda: build(root_field, extracted_on="1970-01-01", campaign=campaign)
        )
        check.tooth(
            "missing compared field",
            caught and dropped in message,
            f"{dropped!r} deleted from {target.key}'s record -> {message}",
        )

        # ---- tooth 4: one value changed in the committed file -------------
        broken = tmp_path / "reproduction_reference.json"
        try:
            document = load()
        except ReferenceError as exc:
            check.fail(f"cannot construct the fourth tooth: {exc}")
            return 3, check.as_record()
        first = document["entries"][0]
        moved = REFERENCE_FIELDS[first["phase"]][0]
        was = first["fields"][moved]
        first["fields"][moved] = (was + 1) if isinstance(was, int) else f"{was}0"
        broken.write_text(serialise(document))
        code, record = stage_verify(
            runs_root=runs_root, reference_path=broken, campaign=campaign
        )
        check.tooth(
            "one value changed in the committed file",
            code != 0,
            f"{first['arm']}/{first['configuration']}: {moved} "
            f"{was!r} -> {first['fields'][moved]!r} in a throwaway copy -> "
            f"verification {record['verdict']}",
        )

    check.n_compared = len(check.teeth)
    return (0 if check.passed else 3), check.as_record()


def _must_refuse(call) -> tuple[bool, str]:
    """Run *call*; report whether it refused, and with what first line."""
    try:
        call()
    except ReferenceError as exc:
        return True, str(exc).splitlines()[0]
    return False, "DID NOT REFUSE"


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
        f"of the compared fields, not the whole set: the optimisation phase "
        f"compares {len(REFERENCE_FIELDS['B'])} fields per record and the "
        f"evaluation phase {len(REFERENCE_FIELDS['A'])}, all of them in the "
        f"committed file. Node calls are model executions during the solve "
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


def report(name: str, code: int, record: Mapping[str, Any]) -> int:
    """Print one stage's verdict in the same shape as the harness's own checks."""
    width = 74
    print("=" * width)
    print(f"reproduction reference — {name}")
    print("=" * width)
    print(f"\n[{record['verdict']}] {record['check']} — {record['binds']}")
    print(f"  population : {record['population']}")
    print(f"  compared   : {record['n_compared']}   mismatched: "
          f"{record['n_mismatched']}")
    for line in record["detail"]:
        print(f"  . {line}")
    for tooth in record["teeth"]:
        mark = "tripped" if tooth["caught"] else "DID NOT TRIP"
        print(f"  tooth {mark}: {tooth['tooth']} — {tooth['what']}")
    print("\n" + "=" * width)
    print(f"verdict: {record['verdict']}")
    print("=" * width)
    return code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    stage = parser.add_mutually_exclusive_group(required=True)
    stage.add_argument(
        "--extract",
        action="store_true",
        help="read the twenty records and write the committed reference",
    )
    stage.add_argument(
        "--verify",
        action="store_true",
        help="re-derive the committed reference and require byte-for-byte "
        "equality with it",
    )
    stage.add_argument(
        "--teeth",
        action="store_true",
        help="the four deliberate breaks, each of which must make a stage "
        "refuse",
    )
    stage.add_argument(
        "--show",
        action="store_true",
        help="print what the committed reference holds and what it does not "
        "cover, without touching the live records",
    )
    stage.add_argument(
        "--tables",
        action="store_true",
        help="emit the report's two tables, with their captions, from the "
        "committed reference",
    )
    parser.add_argument(
        "--previous-runs",
        type=Path,
        help="root of the previous revision's untracked run records "
        "(default for --extract: this checkout's own, which a task worktree "
        "does not have; default for --verify: the root the committed file "
        "names)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help=f"where to write the reference (default {REFERENCE_PATH})",
    )
    parser.add_argument(
        "--extraction-date",
        help="stamp this date instead of today's, so an extraction can be "
        "reproduced exactly",
    )
    parser.add_argument("--json", type=Path, help="write the stage's record here")
    args = parser.parse_args(argv)

    if args.show or args.tables:
        try:
            document = load(args.out)
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

    if args.extract:
        code, record = stage_extract(
            runs_root=args.previous_runs,
            out_path=args.out,
            extracted_on=args.extraction_date,
        )
        name = "extract"
    elif args.verify:
        code, record = stage_verify(
            runs_root=args.previous_runs, reference_path=args.out
        )
        name = "verify"
    else:
        code, record = stage_teeth(runs_root=args.previous_runs)
        name = "teeth"

    report(name, code, record)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(record, indent=2, default=str))
        print(f"record: {args.json}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
