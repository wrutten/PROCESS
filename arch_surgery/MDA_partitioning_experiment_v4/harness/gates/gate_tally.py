#!/usr/bin/env python
"""The tally's own gate: what a table may not be, and the cells it must land on.

The tally itself has nothing to pass — it publishes what the experiment plan
asks for by name — so it runs under ``--measure``.  What *is* a gate is the set
of things the tally **refuses**, and the one number it can be checked against:
the previous revision's published cells.

**The criterion**, in four parts, each with its own denominator:

1. **The previous revision's published cells reproduce.**  For each of the
   twenty reference runs the previous revision published a row of numbers; this
   computes the same cells from this revision's records — through this
   revision's own constructions where there is one, and through the field-name
   map where a record field has been renamed — and compares them without
   tolerance.  Three of the cells are *constructed* rather than read
   (``stats.iterations_final_attempt``, ``stats.iterations_summed_over_attempts``,
   ``stats.n_attempts``), which is what makes this a stronger statement than the
   reproduction gate's field-for-field comparison: a construction landing on the
   previous revision's published number says the rule is the same rule.
2. **Every table the tally emits carries a caption and a denominator**, and the
   denominator is a count rather than a letter.
3. **No acceptance table carries a timing column.**
4. **The record contract holds over the population the tally read** — no record
   missing a declared field, no record carrying one ruler and not both, no
   record whose per-attempt costs do not sum to the run total.

**Ten teeth**, one per way a tally can go wrong quietly.  Each constructs the
break and requires the refusal; a tooth that does not trip fails the gate.

Written by task **A53 (harness-tally)**.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable, Mapping

from harness.core import records as records_mod
from harness.gates import reference as reference_mod
from harness.measurement import stats as stats_mod
from harness.measurement import tables as tables_mod
from harness.measurement import tally as tally_mod
from harness.measurement import tally_evaluation as tally_a
from harness.measurement import tally_optimisation as tally_b
from harness.core.config import Campaign
from harness.core.framework import Gate, Tooth
from harness.measurement.tables import Caption, Column, Table

__all__ = ["gate"]


# --------------------------------------------------------------------------
# a table that is fine, to break in several different ways
# --------------------------------------------------------------------------


def _sound_caption() -> Caption:
    return Caption(
        units="counts",
        row_is="one arm",
        column_is="one counter",
        population="the tooth's own two rows",
        construction="written here, for the tooth",
    )


def _sound_table(**overrides: Any) -> Table:
    kwargs: dict[str, Any] = {
        "name": "a sound table",
        "caption": _sound_caption(),
        "columns": (Column("arm", "arm"), Column("calls", "node calls")),
        "rows": ({"arm": "B0", "calls": 10}, {"arm": "B3", "calls": 5}),
        "denominator": 2,
        "denominator_is": "runs",
    }
    kwargs.update(overrides)
    return Table(**kwargs)


def _refuses(call: Callable[[], Any], *, what: str) -> tuple[bool, str]:
    """Run *call* and require a refusal.  Anything else is a tooth that failed."""
    try:
        call()
    except (tables_mod.TableError, stats_mod.StatsError, records_mod.RecordError) as exc:
        return True, f"{what}: refused — {str(exc).splitlines()[0]}"
    except Exception as exc:  # noqa: BLE001 - a different exception is not the refusal
        return False, (
            f"{what}: raised {type(exc).__name__} rather than the declared "
            f"refusal — {exc}"
        )
    return False, f"{what}: was accepted.  It must not be."


# --------------------------------------------------------------------------
# the criterion
# --------------------------------------------------------------------------


def body(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    """The four parts, each with its denominator."""
    cells = tally_mod.reference_cells(campaign)
    detail: list[str] = []
    n_compared = 0
    n_mismatched = 0

    # --- part 1: the previous revision's published cells -------------------
    detail.append(
        f"the previous revision's published cells: "
        f"{cells['n_cells_matched']}/{cells['n_cells_compared']} over "
        f"{cells['n_runs']} reference run(s); "
        f"{cells['n_runs_reproduced']} run(s) reproduced whole"
    )
    if cells.get("cells_by_construction"):
        detail.append(
            "cells computed by one of this revision's own constructions "
            "rather than read from a field: "
            + ", ".join(cells["cells_by_construction"])
        )
    for row in cells["rows"]:
        for cell in row["cells"]:
            if not cell["matched"]:
                detail.append(
                    f"MOVED: {row['key']} {cell['cell']} — expected "
                    f"{cell.get('expected')!r}, found {cell.get('found')!r}"
                )

    # --- parts 2 and 3: every emitted table --------------------------------
    emitted: list[Mapping[str, Any]] = []
    tally_errors: list[str] = []
    for name, stage in (
        ("evaluation", tally_a.tally),
        ("optimisation", tally_b.tally),
    ):
        try:
            block = stage(campaign, resume=resume)
        except (tally_mod.TallyError, stats_mod.StatsError) as exc:
            tally_errors.append(f"the {name} tally refused: {exc}")
            continue
        emitted.extend(block.get("tables") or [])
        for line in block.get("record_contract_refusals") or []:
            tally_errors.append(f"the {name} tally's population: {line}")
    for table in emitted:
        n_compared += 3
        if not table.get("caption"):
            n_mismatched += 1
            detail.append(f"{table['table']}: no caption")
        denominator = table.get("denominator")
        if not isinstance(denominator, int) or isinstance(denominator, bool):
            n_mismatched += 1
            detail.append(f"{table['table']}: denominator {denominator!r}")
        if not str(table.get("denominator_is") or "").strip():
            n_mismatched += 1
            detail.append(f"{table['table']}: the denominator says nothing")
    detail.append(
        f"{len(emitted)} table(s) emitted, each checked for a caption, a "
        f"denominator that is a count, and a sentence saying what the "
        f"denominator counts: {n_compared} checks"
    )
    acceptance = [t for t in emitted if t.get("acceptance")]
    detail.append(
        f"{len(acceptance)} of them are acceptance tables and carry no timing "
        f"column, which the table module enforces at construction"
    )
    mixed = [
        t["table"] for t in emitted if len(t.get("audit_positions") or []) > 1
    ]
    detail.append(
        "audit positions across the emitted tables: "
        + json.dumps(
            sorted({p for t in emitted for p in (t.get("audit_positions") or [])})
        )
        + (
            f"; {len(mixed)} table(s) carry more than one and each labels it "
            f"per row"
            if mixed
            else "; no table carries more than one"
        )
    )

    # --- part 4: the record contract ---------------------------------------
    for line in tally_errors:
        n_mismatched += 1
        detail.append(line)

    passed = (
        cells["passed"]
        and n_mismatched == 0
        and not tally_errors
        and bool(emitted)
    )
    if not emitted:
        detail.append(
            "REFUSED: the tally emitted no table at all, so there is nothing "
            "to check.  A gate over an empty set is not a gate."
        )
    return {
        "passed": bool(passed),
        "population": (
            f"{cells['population']}; and {len(emitted)} table(s) emitted by "
            f"the two tally stages over the gate records on disk"
        ),
        "n_reference_values_compared": cells["n_cells_compared"],
        "n_reference_values_differing": cells["n_cells_differing"],
        "n_compared": n_compared,
        "n_mismatched": n_mismatched,
        "n_tables": len(emitted),
        "n_acceptance_tables": len(acceptance),
        "reference_cells": cells,
        "tables": [
            {
                "table": t["table"],
                "denominator": t["denominator"],
                "denominator_is": t["denominator_is"],
                "acceptance": t["acceptance"],
                "audit_positions": t["audit_positions"],
                "n_rows": len(t["rows"]),
            }
            for t in emitted
        ],
        "detail": detail,
    }


# --------------------------------------------------------------------------
# the teeth
# --------------------------------------------------------------------------


def _tooth_no_caption() -> tuple[bool, str]:
    return _refuses(
        lambda: _sound_table(caption=None),
        what="a table built with no caption",
    )


def _tooth_no_denominator() -> tuple[bool, str]:
    return _refuses(
        lambda: _sound_table(denominator=None),
        what="a table built with no denominator",
    )


def _tooth_placeholder_denominator() -> tuple[bool, str]:
    return _refuses(
        lambda: _sound_table(denominator="n"),
        what="a table carrying the experiment plan's placeholder denominator "
        "'n'",
    )


def _tooth_timing_column() -> tuple[bool, str]:
    return _refuses(
        lambda: _sound_table(
            columns=(
                Column("arm", "arm"),
                Column("wall_s", "wall clock, s"),
            ),
            rows=({"arm": "B0", "wall_s": 12.0},),
            denominator=1,
            acceptance=True,
        ),
        what="an acceptance table carrying a wall-clock column",
    )


def _tooth_pooled_predicates() -> tuple[bool, str]:
    return _refuses(
        lambda: _sound_table(
            columns=(
                Column("arm", "arm"),
                Column(
                    "tests",
                    "convergence tests (both predicates)",
                    predicate="pooled",
                ),
            ),
            rows=({"arm": "B3", "tests": 900},),
            denominator=1,
        ),
        what="a table carrying one column that adds the two predicates' counts",
    )


def _tooth_audit_position_mix() -> tuple[bool, str]:
    return _refuses(
        lambda: _sound_table(
            columns=(Column("arm", "arm"), Column("residual", "residual")),
            rows=(
                {
                    "arm": "B0",
                    "residual": 1e-7,
                    "audit_position": "entry_to_write_output_files",
                },
                {"arm": "BR", "residual": 7e-3, "audit_position": "after_run"},
            ),
            denominator=2,
        ),
        what="a residual table whose rows were audited at two different "
        "positions with no column saying so",
    )


def _tooth_forced_budget() -> tuple[bool, str]:
    """A demonstration record must not reach a population that summarises."""
    demonstration = {
        "campaign_phase": "B",
        "campaign_arm": "BR",
        "campaign_configuration": "st_regression",
        "campaign_seed": 0,
        stats_mod.FORCED_BUDGET_STAMP: 2,
    }
    plain = {
        "campaign_phase": "B",
        "campaign_arm": "B0",
        "campaign_configuration": "st_regression",
        "campaign_seed": 0,
    }
    population = stats_mod.Population.of(
        [plain, demonstration], what="the tooth's own two records"
    )
    if len(population) != 1 or len(population.excluded) != 1:
        return False, (
            f"the population kept {len(population)} record(s) and excluded "
            f"{len(population.excluded)}: the budget-capped demonstration was "
            f"not separated out"
        )
    return _refuses(
        population.assert_no_forced_budget,
        what=(
            "a population handed a record stamped "
            f"{stats_mod.FORCED_BUDGET_STAMP} "
            f"(excluded by name: {population.excluded[0][0]})"
        ),
    )


def _tooth_check_two_constructions() -> tuple[bool, str]:
    """Doctor one attempt's iteration count and require the two to disagree."""
    record = {
        "campaign_phase": "B",
        "attempts": [
            {"attempt": 0, "n_iterations": 11},
            {"attempt": 1, "n_iterations": 7},
        ],
    }
    final = stats_mod.iterations_final_attempt(record)
    summed = stats_mod.iterations_summed_over_attempts(record)
    if final != 7 or summed != 18:
        return False, (
            f"the two constructions read {final} and {summed} on a record "
            f"whose attempts are 11 then 7; they must read 7 and 18"
        )
    doctored = copy.deepcopy(record)
    doctored["attempts"][0]["n_iterations"] = 12
    moved_final = stats_mod.iterations_final_attempt(doctored)
    moved_summed = stats_mod.iterations_summed_over_attempts(doctored)
    caught = moved_final == final and moved_summed == summed + 1
    return caught, (
        f"a failed attempt's iteration count moved by one: the final-attempt "
        f"construction reads {moved_final} (unchanged, correctly — the move "
        f"was not in the final attempt) and the summed construction reads "
        f"{moved_summed} rather than {summed}.  The two constructions "
        f"disagree by exactly the doctored amount, which is what publishing "
        f"both is for"
        if caught
        else f"the doctored record read {moved_final} and {moved_summed}; the "
        f"two constructions did not separate"
    )


def _tooth_summation_broken() -> tuple[bool, str]:
    """Break the attempt summation by one and require both refusals."""
    record = {
        "campaign_phase": "B",
        "status": "ok",
        "attempts": [
            {"attempt": 0, "n_iterations": 3, "node_calls_solve_phase": 100, "sweeps": 10},
            {"attempt": 1, "n_iterations": 4, "node_calls_solve_phase": 50, "sweeps": 5},
        ],
        "node_calls_solve_phase": 150,
        "dispatch_sweeps_solve_phase": 15,
    }
    sound = stats_mod.attempt_summation(record)
    if not sound.get("decomposes"):
        return False, (
            f"the identity did not hold on a record built to satisfy it: "
            f"{sound}"
        )
    doctored = copy.deepcopy(record)
    doctored["node_calls_solve_phase"] = 151
    broken = stats_mod.attempt_summation(doctored)
    residual = (broken.get("parts") or {}).get("node_calls_solve_phase", {}).get(
        "residual"
    )
    if broken.get("decomposes") or residual != 1:
        return False, (
            f"the tally's own identity did not catch a run total moved by "
            f"one: decomposes={broken.get('decomposes')}, residual={residual}"
        )
    return _refuses(
        lambda: records_mod.assert_attempt_summation(doctored, where="the tooth"),
        what=(
            f"a run total moved by one against its attempts "
            f"(the tally's identity reports residual {residual}, and the "
            f"record contract)"
        ),
    )


def _tooth_reference_cell_moved(campaign: Campaign) -> Callable[[], tuple[bool, str]]:
    """Move one published cell of the committed reference by one."""

    def look() -> tuple[bool, str]:
        document = copy.deepcopy(reference_mod.load())
        moved: str | None = None
        for entry in document["entries"]:
            for path, value in entry["fields"].items():
                if isinstance(value, int) and not isinstance(value, bool):
                    entry["fields"][path] = value + 1
                    moved = (
                        f"{entry['arm']}/{entry['configuration']}/"
                        f"seed{entry['seed']:03d} {path}: {value} → {value + 1}"
                    )
                    break
            if moved:
                break
        if moved is None:
            return False, "the committed reference carries no integer cell to move"
        # Against the **undoctored** comparison, not against zero: the tooth
        # must show that moving one cell adds exactly one differing cell,
        # whatever the criterion's own state is.  A tooth that only trips when
        # everything else already passes is a tooth that cannot be run until
        # the gate passes, which is the wrong way round.
        before = tally_mod.reference_cells(campaign)
        after = tally_mod.reference_cells(campaign, document=document)
        caught = (
            after["n_cells_differing"] == before["n_cells_differing"] + 1
            and not after["passed"]
        )
        return caught, (
            f"one published cell moved by one ({moved}): the comparison goes "
            f"from {before['n_cells_differing']} to "
            f"{after['n_cells_differing']} differing cell(s) of "
            f"{after['n_cells_compared']}, and does not pass"
            if caught
            else f"the moved cell was not caught: "
            f"{before['n_cells_differing']} differing before, "
            f"{after['n_cells_differing']} after, passed={after['passed']}"
        )

    return look


def gate(campaign: Campaign) -> Gate:
    """The tally's gate, with its eight teeth."""
    return Gate(
        name="tally_contracts",
        binds="every table the tally emits, and the cells it reproduces",
        what_it_proves=(
            "that the tally reproduces the previous revision's published cells "
            "on the twenty runs where a previous number exists, that every "
            "table it emits carries a caption and a real denominator, that no "
            "acceptance table carries a timing, and that each of the seven "
            "things a table may not be is a refusal at construction rather "
            "than a review comment"
        ),
        body=lambda *, resume=False: body(campaign, resume=resume),
        needs_runs=False,
        runs_under=("reproduction", "predicate_mode", "output_path"),
        reads_from=("reproduction",),
        teeth=(
            Tooth(
                name="no caption",
                what="a table built with no caption at all",
                must="REFUSE",
                check=_tooth_no_caption,
            ),
            Tooth(
                name="no denominator",
                what="a table built with no denominator",
                must="REFUSE",
                check=_tooth_no_denominator,
            ),
            Tooth(
                name="placeholder denominator",
                what="a table carrying the plan's placeholder 'n' where a "
                "count belongs",
                must="REFUSE",
                check=_tooth_placeholder_denominator,
            ),
            Tooth(
                name="timing column in an acceptance table",
                what="a wall-clock column added to a table an acceptance "
                "verdict is read from",
                must="REFUSE",
                check=_tooth_timing_column,
            ),
            Tooth(
                name="pooled predicates",
                what="one column adding the coupling-state test's count to "
                "upstream's objective/constraint test's",
                must="REFUSE",
                check=_tooth_pooled_predicates,
            ),
            Tooth(
                name="audit-position mix",
                what="two residuals audited at two positions in one table "
                "with no column saying so",
                must="REFUSE",
                check=_tooth_audit_position_mix,
            ),
            Tooth(
                name="a demonstration record in a population",
                what="a record stamped force_maxcal offered to a population "
                "that summarises",
                must="REFUSE",
                check=_tooth_forced_budget,
            ),
            Tooth(
                name="check 2's two constructions disagree",
                what="a failed attempt's iteration count moved by one",
                must="SEPARATE THE TWO CONSTRUCTIONS",
                check=_tooth_check_two_constructions,
            ),
            Tooth(
                name="the summation identity broken by one",
                what="a run's solve-phase total moved by one against the sum "
                "of its attempts",
                must="REFUSE",
                check=_tooth_summation_broken,
            ),
            Tooth(
                name="a reference cell moved by one",
                what="one published cell of the committed reference "
                "incremented",
                must="TRIP",
                check=_tooth_reference_cell_moved(campaign),
            ),
        ),
    )


def print_verdict(verdict: Mapping[str, Any]) -> None:
    """The gate's own numbers, printed rather than left in the record."""
    print(
        f"  reference cells : "
        f"{verdict.get('n_reference_values_compared', 0) - verdict.get('n_reference_values_differing', 0)}"
        f"/{verdict.get('n_reference_values_compared')} reproduced"
    )
    print(
        f"  table contracts : {verdict.get('n_compared')} checks over "
        f"{verdict.get('n_tables')} table(s), "
        f"{verdict.get('n_mismatched')} failed"
    )
    for line in verdict.get("detail") or []:
        print(f"  . {line}")
