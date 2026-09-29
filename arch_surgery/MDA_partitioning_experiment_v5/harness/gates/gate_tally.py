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

**Twelve teeth**, one per way a tally can go wrong quietly.  Each constructs the
break and requires the refusal; a tooth that does not trip fails the gate.

Written by task **A53 (harness-tally)**.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable, Mapping

from harness.core import pool as pool_mod
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
        "rows": ({"arm": "B0", "calls": 10}, {"arm": "B2", "calls": 5}),
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
    families: set[str] = set()
    source_counts: list[str] = []
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
        families.add(str(block.get("population_family")))
        source_counts.extend(
            f"{s['source']}: {s['n_records']}" for s in block.get("sources") or []
        )
        for line in block.get("record_contract_refusals") or []:
            tally_errors.append(f"the {name} tally's population: {line}")
    if len(families) > 1:
        tally_errors.append(
            f"the two tally stages published different population families: "
            f"{sorted(families)}.  A table is over one population."
        )
    family = next(iter(families)) if len(families) == 1 else "?"
    detail.append(
        f"the tables are over the {family} population — "
        + (", ".join(source_counts) or "no source")
        + " record(s); the reference cells above are the reproduction gate's "
        "twenty runs whatever the published family"
    )
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
            f"the two tally stages over the {family} population "
            f"({', '.join(source_counts) or 'no source'} record(s))"
        ),
        "population_family": family,
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
            rows=({"arm": "B2", "tests": 900},),
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


def _tooth_unequal_module_execution() -> tuple[bool, str]:
    """Move one node of a group by one call and require the sweep count to be
    refused rather than averaged.

    The per-module tables state **module sweeps per run**, which is only a
    quantity because every model node of a group runs once per sweep.  A
    group whose members did not execute together has no sweep count, and a
    mean over them would be a number with no unit printed under a heading
    that claims one.  Task **A85 (v3-table-formats)**.
    """
    groups = [{"group": "M1", "nodes": ["physics", "plasma_geom"]}]
    counted = {"physics": 4, "plasma_geom": 4}
    sound = stats_mod.module_sweeps(counted, groups)
    if sound != {"M1": 4.0}:
        return False, (
            f"an equally-executed group read {sound}; it must read 4 sweeps"
        )
    doctored = dict(counted, plasma_geom=5)
    return _refuses(
        lambda: stats_mod.module_sweeps(doctored, groups),
        what="a group whose two nodes executed 4 and 5 times",
    )


def _tooth_row_attribution_not_guessed() -> tuple[bool, str]:
    """Withhold a module's DSM row count and require the total to be refused.

    ``models`` is what makes ``Σ sweeps × models`` a number; a map that does
    not state it would otherwise be silently filled in with a guess, which is
    exactly the reading of another repository's exports trap T9 forbids.
    Task **A85 (v3-table-formats)**.
    """
    node_map = {
        "module_order": {"M1": 0, "M2": 1, "M3": 2, "PULSE": 3, "FF": 4},
        "units": {"dsm_rows": {"M1": 24, "M2": 10, "M3": 12, "PULSE": 1, "FF": 5}},
        "nodes": {"vacuum": {"module": "M3"}},
    }
    groups = [
        {"group": "M3", "nodes": ["fw", "shield"]},
        {"group": "once per run", "nodes": ["vacuum"]},
    ]
    sound = stats_mod.dsm_rows_by_group(node_map, groups)
    if sound["M3"] != {"v1": 11, "v0": 12} or sound["once per run"] != {"v1": 1, "v0": 0}:
        return False, (
            f"the two attributions read {sound}; M3 must read 11 rows under "
            f"v = 1 and 12 under v = 0, and the once-per-run group 1 and 0"
        )
    short = copy.deepcopy(node_map)
    del short["units"]["dsm_rows"]["M3"]
    return _refuses(
        lambda: stats_mod.dsm_rows_by_group(short, groups),
        what="a node map stating no DSM row count for M3",
    )


def _tooth_function_count_not_guessed() -> tuple[bool, str]:
    """Withhold a module's function count, then a once-per-run node's own
    row, and require the function-weighted total to be refused both times.

    ``functions`` is what makes ``Σ sweeps × functions`` a number; a committed
    file that does not state it for a module, or that cannot give a
    once-per-run node one DSM row of its own for the ``v = 1`` attribution,
    would otherwise be filled in with a guess — the same reading of another
    repository's exports trap T9 forbids, one weight over.  Task **A88
    (function-weighted-sweeps)**.
    """
    node_map = {"nodes": {"vacuum": {"module": "M3"}}}
    counts = {
        "modules": {
            "M1": {"functions": 178}, "M2": {"functions": 90}, "M3": {"functions": 73},
            "PULSE": {"functions": 3}, "FF": {"functions": 51},
        },
        "nodes": {"vacuum": {"functions": 5, "one_row": True, "models": ["Vacuum"]}},
    }
    groups = [
        {"group": "M3", "nodes": ["fw", "shield"]},
        {"group": "once per run", "nodes": ["vacuum"]},
    ]
    sound = stats_mod.functions_by_group(counts, node_map, groups)
    if sound["M3"] != {"v1": 68, "v0": 73} or sound["once per run"] != {"v1": 5, "v0": 0}:
        return False, (
            f"the two attributions read {sound}; M3 must read 68 functions under "
            f"v = 1 and 73 under v = 0, and the once-per-run group 5 and 0"
        )
    short = copy.deepcopy(counts)
    del short["modules"]["M3"]["functions"]
    tripped, why = _refuses(
        lambda: stats_mod.functions_by_group(short, node_map, groups),
        what="a function-count file stating no count for M3",
    )
    if not tripped:
        return False, why
    no_row = copy.deepcopy(counts)
    no_row["nodes"]["vacuum"] = {"functions": 5, "one_row": False, "models": []}
    tripped_row, why_row = _refuses(
        lambda: stats_mod.functions_by_group(no_row, node_map, groups),
        what="a once-per-run node the file resolves to no single DSM row",
    )
    if not tripped_row:
        return False, why_row
    return True, f"{why}; and {why_row}"


def _tooth_design_vector_by_position() -> tuple[bool, str]:
    """Offer a design vector with a value in a slot the name map does not name.

    The location diagnostic matches iteration variables **by name**: the lift
    adds one, so two arms' vectors are of different lengths, and a join by
    position would compare two different variables and publish the result as
    a design-point difference.  The construction joins on the solver's slot
    and refuses a record that has a value where there is no name.  Task
    **A86 (v3-tables-remainder)**.
    """
    record = {
        "campaign_phase": "B",
        "mfile": {
            "itvars": {"itvar001": 1.0, "itvar002": 2.0},
            "itvar_names": {"itvar001": "rmajor", "itvar002": "dr_cs"},
        },
    }
    sound = stats_mod.iteration_variables(record)
    if sound != {"rmajor": 1.0, "dr_cs": 2.0}:
        return False, f"a named vector read {sound}; it must be keyed by name"
    doctored = copy.deepcopy(record)
    doctored["mfile"]["itvars"]["itvar003"] = 3.0
    return _refuses(
        lambda: stats_mod.iteration_variables(doctored),
        what="a design vector with a third value and only two names",
    )


def _tooth_unshared_variable_not_compared() -> tuple[bool, str]:
    """Add a variable to one side only and require it to be **named, not
    compared**.

    A variable one arm carries and the other does not has no difference; the
    previous revision's §5.2.2 named it and never compared it.  The
    construction must report it in ``extra`` and must not let it move the
    maximum.  Task **A86 (v3-tables-remainder)**.
    """
    left = {"rmajor": 8.0, "dr_cs": 0.5}
    right = {"rmajor": 8.8, "dr_cs": 0.5}
    sound = stats_mod.point_difference(left, right)
    if sound["argmax"] != "rmajor" or abs(sound["max"] - 0.8 / 8.8) > 1e-15:
        return False, f"the shared maximum read {sound}; it must be rmajor"
    lifted = dict(right, t_plant_pulse_burn=1.0e4)
    after = stats_mod.point_difference(left, lifted)
    if after["max"] != sound["max"] or after["argmax"] != "rmajor":
        return False, (
            f"a variable on one side only moved the maximum: {after}; it must "
            f"be named and never compared"
        )
    if after["extra"] != ["t_plant_pulse_burn"] or after["n_shared"] != 2:
        return False, (
            f"the unshared variable was not named: {after}; extra must hold "
            f"it and n_shared must stay 2"
        )
    return True, (
        "a variable added to one side alone is named in `extra` and does not "
        "move the maximum, which stays on rmajor"
    )


def _tooth_excluded_namespaces_not_guessed() -> tuple[bool, str]:
    """Withhold the run's own exclusion list and require the per-namespace
    maxima to be refused.

    The excluded namespaces are the run's own ``excluded_keys``; a list typed
    into the table would be a list of what somebody expected the exclusion to
    hold, which is the shape of trap T11.  A ruler the file does not carry is
    refused for the same reason: a maximum on another ruler is a different
    quantity under the same heading.  Task **A86 (v3-tables-remainder)**.
    """
    audit = {
        "excluded_keys": ["costs.coecap", "costs.c21", "vacuum.vacdshm"],
        "rulers": {
            "frozen": {
                "scaled_hex": {
                    "costs.coecap": "0x1.0p+0",
                    "costs.c21": "0x1.0p-1",
                    "vacuum.vacdshm": "0x1.0p-2",
                }
            }
        },
    }
    sound = stats_mod.namespace_residuals(audit, ruler="frozen")
    if sound != {"costs": 1.0, "vacuum": 0.25}:
        return False, (
            f"the per-namespace maxima read {sound}; costs must be 1.0 (the "
            f"larger of its two components) and vacuum 0.25"
        )
    blind = {k: v for k, v in audit.items() if k != "excluded_keys"}
    refused, why = _refuses(
        lambda: stats_mod.namespace_residuals(blind, ruler="frozen"),
        what="an audit residual file naming no excluded_keys",
    )
    if not refused:
        return refused, why
    return _refuses(
        lambda: stats_mod.namespace_residuals(audit, ruler="mixed"),
        what="a ruler the audit residual file does not carry",
    )


def _tooth_objective_name_not_an_integer() -> tuple[bool, str]:
    """Offer a figure of merit the frozen tree's enum does not carry.

    A problem-definition row that printed the integer where the objective's
    name belongs is a row whose reader cannot tell which problem was solved,
    so the construction refuses rather than falling back to the number.  The
    sense is read from the sign, which the sound case checks in both
    directions.  Task **A86 (v3-tables-remainder)**.
    """
    source = (
        'class FiguresOfMerit(IntEnum):\n'
        '    MAJOR_RADIUS = (1, "Plasma major radius")\n'
        '    PULSE_LENGTH = (14, "Pulse length")\n'
    )
    least = stats_mod.figure_of_merit(source, 1)
    most = stats_mod.figure_of_merit(source, -14)
    if least["objective"] != "Plasma major radius" or least["sense"] != "minimise":
        return False, f"a positive figure of merit read {least}"
    if most["objective"] != "Pulse length" or most["sense"] != "maximise":
        return False, f"a negative figure of merit read {most}"
    return _refuses(
        lambda: stats_mod.figure_of_merit(source, 6),
        what="a figure of merit the frozen tree's enum does not carry",
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


def _tooth_fixed_point_distance_restriction(
    campaign: Campaign,
) -> Callable[[], tuple[bool, str]]:
    """Doctor one exit state in a scratch copy: a kept component moved by
    1e-3 of its scale must raise the restricted distance to at least that
    and count the pair above τ; an excluded component moved past the
    whole-state maximum must leave the restricted distance exactly where it
    was and carry the whole-state one.  Both halves, on one real pair of the
    published population, or the tooth is not tripped."""

    def look() -> tuple[bool, str]:
        import shutil  # noqa: PLC0415
        import tempfile  # noqa: PLC0415

        from harness.child import predicate as predicate_mod  # noqa: PLC0415

        # One real pair: the first configuration and published evaluation
        # source that carries the headline pair with both exit states.
        for source in tally_mod.published_sources(campaign):
            if tally_a.PHASE not in source.phases:
                continue
            rows, _ = tally_mod.source_rows(campaign, source)
            where = {
                str(r.record.get("job_digest")): Path(r.path).parent
                for r in rows
                if r.record.get("job_digest")
            }
            population = tally_mod.population_for(
                rows, phase=tally_a.PHASE, what="tooth",
                campaign_present=tally_mod.campaign_present(campaign),
            )
            for config in campaign.configurations:
                indexed = tally_a._by_arm_and_seed(population, config.name)
                base, _why = tally_a.reference_arm(config.pulsed, set(indexed))
                pairs = [
                    (b, a) for b, a, role in tally_a.ladder_pairs(list(indexed), base)
                    if role == "headline"
                ]
                if not pairs:
                    continue
                b_arm, a_arm = pairs[0]
                for key in sorted(set(indexed[b_arm]) & set(indexed[a_arm])):
                    left, right = indexed[b_arm][key], indexed[a_arm][key]
                    if not (stats_mod.finished(left) and stats_mod.finished(right)):
                        continue
                    d_left = where.get(str(left.get("job_digest")))
                    d_right = where.get(str(right.get("job_digest")))
                    if d_left is None or d_right is None:
                        continue
                    if not ((d_left / "y_exit.json").exists() and (d_right / "y_exit.json").exists()):
                        continue
                    return _doctor_and_look(
                        campaign, config, population, source.name,
                        left, right, d_left, d_right, key,
                        predicate_mod, shutil, tempfile,
                    )
        return False, "no published evaluation pair with both exit states on disk"

    return look


def _doctor_and_look(
    campaign, config, population, source_name, left, right, d_left, d_right,
    key, predicate_mod, shutil, tempfile,
) -> tuple[bool, str]:
    spec = predicate_mod.load_spec(config.coupling_state_path)
    spec_keys = [spec.name(i) for i in range(len(spec.keys))]
    tested = [spec.name(i) for i in sorted(set(spec.idx_continuous) | set(spec.idx_nonfinite))]
    written, _excluded, why = tally_a._excluded_by_the_per_run_nodes(
        campaign, config.name, right, spec_keys, tested
    )
    if written is None:
        return False, f"the pair carries no restriction to test: {why}"
    state = json.loads((d_right / "y_exit.json").read_text())["state"]
    scalars = {
        spec.name(i): i for i in spec.idx_continuous
        if state.get(spec.name(i), {}).get("k") == "f"
    }
    kept_name = next((n for n in scalars if n not in written), None)
    excluded_name = next((n for n in scalars if n in written), None)
    if kept_name is None or excluded_name is None:
        return False, "no scalar continuous component on both sides of the restriction"
    two = {str(left.get("job_digest")): d_left}

    def distance_with(doctored_name: str | None, *, scaled_step: float = 1e-3) -> Mapping[str, Any]:
        scratch = Path(tempfile.mkdtemp(prefix="tooth_fixed_point_"))
        try:
            copy_dir = scratch / "arm"
            shutil.copytree(d_right, copy_dir)
            if doctored_name is not None:
                doc = json.loads((copy_dir / "y_exit.json").read_text())
                value = float.fromhex(doc["state"][doctored_name]["hex"])
                step = scaled_step * float(spec.scale[scalars[doctored_name]])
                doc["state"][doctored_name]["hex"] = float(value + step).hex()
                (copy_dir / "y_exit.json").write_text(json.dumps(doc))
            where = {**two, str(right.get("job_digest")): copy_dir}
            pop = stats_mod.Population.of(
                [left, right], what="tooth: one pair",
                campaign_present=tally_mod.campaign_present(campaign),
            )
            table = tally_a.fixed_point_distance(
                campaign, pop, config.name, source_name, where
            )
            row = next(r for r in table.rows if r["role"] == "headline")
            return dict(row)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)

    plain = distance_with(None)
    kept = distance_with(kept_name)
    # The excluded component is moved past the whole-state maximum, so that
    # the whole-state column must follow it while the restricted one holds.
    big = 2.0 * (float(plain["whole_median"] or 0.0) + 1.0)
    excluded = distance_with(excluded_name, scaled_step=big)
    kept_caught = (
        kept["restricted_max"] is not None
        and kept["restricted_max"] >= 1e-3 - 1e-12
        and kept["n_pairs_above_tau"] == 1
        and kept["argmax"] == kept_name
    )
    excluded_caught = (
        excluded["restricted_max"] == plain["restricted_max"]
        and excluded["n_pairs_above_tau"] == plain["n_pairs_above_tau"]
        and excluded["whole_median"] is not None
        and excluded["whole_median"] >= big - 1e-9
    )
    caught = bool(kept_caught and excluded_caught)
    return caught, (
        f"{config.name} {plain['pair']} at key {key}: undoctored restricted "
        f"worst {plain['restricted_max']:.3e}; kept component {kept_name} "
        f"moved by 1e-3 of its scale → restricted worst "
        f"{kept['restricted_max']:.3e}, argmax {kept['argmax']}, pairs above "
        f"τ {kept['n_pairs_above_tau']}; excluded component {excluded_name} "
        f"moved by {big:.3g} of its scale → restricted worst "
        f"{excluded['restricted_max']:.3e} (unchanged), whole-state median "
        f"{plain['whole_median']:.3e} → {excluded['whole_median']:.3e}"
        + ("" if caught else " — NOT CAUGHT")
    )


def pool_tally_jobs(campaign: Campaign) -> list[dict[str, Any]]:
    """The jobs this gate reads: the published sources' and the reproduction gate's."""
    jobs = [
        job
        for source in tally_mod.published_sources(campaign)
        for job in tally_mod.source_jobs(campaign, source)
    ]
    reference = next(s for s in tally_mod.GATE_SOURCES if s.name == "reference_runs")
    jobs += tally_mod.source_jobs(campaign, reference)
    return pool_mod.job_listing(jobs, campaign)


def gate(campaign: Campaign) -> Gate:
    """The tally's gate, with its eighteen teeth."""
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
        # The runs it reads are the tally's **published** sources' job sets —
        # the campaign plan's once a campaign record exists, GR's planned runs
        # and G6's pairing runs otherwise — plus GR's runs whatever the family,
        # since part 1 reproduces the previous revision's cells on them.
        # Resolved by the pool; never a retyped directory (trap T12).
        jobs=lambda: pool_tally_jobs(campaign),
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
                name="a module executed unequally",
                what="a node group whose members ran 4 and 5 times, offered "
                "to the construction that states module sweeps per run",
                must="REFUSE",
                check=_tooth_unequal_module_execution,
            ),
            Tooth(
                name="a DSM row count the map does not state",
                what="a node map with no row count for M3, offered to the "
                "construction that weights the per-module total",
                must="REFUSE",
                check=_tooth_row_attribution_not_guessed,
            ),
            Tooth(
                name="a function count the file does not state",
                what="a function-count file with no count for M3, then one "
                "giving a once-per-run node no DSM row of its own, offered to "
                "the construction that weights the per-module total per function",
                must="REFUSE",
                check=_tooth_function_count_not_guessed,
            ),
            Tooth(
                name="a design vector joined by position",
                what="an output file with a third iteration-variable value "
                "and only two names, offered to the construction the "
                "location diagnostic matches by name",
                must="REFUSE",
                check=_tooth_design_vector_by_position,
            ),
            Tooth(
                name="a variable one side alone carries",
                what="the lifted arm's extra iteration variable added to one "
                "of two design vectors",
                must="BE NAMED AND NEVER COMPARED",
                check=_tooth_unshared_variable_not_compared,
            ),
            Tooth(
                name="an exclusion list the run did not state",
                what="an audit residual file with its excluded_keys removed, "
                "and then a ruler it does not carry",
                must="REFUSE",
                check=_tooth_excluded_namespaces_not_guessed,
            ),
            Tooth(
                name="a figure of merit the enum does not carry",
                what="i_figure_merit = 6 offered to the construction that "
                "names the objective",
                must="REFUSE",
                check=_tooth_objective_name_not_an_integer,
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
            Tooth(
                name="the fixed-point distance's restriction",
                what="one exit state doctored in a scratch copy: a kept "
                "component moved by 1e-3 of its scale, then an excluded one",
                must="MOVE ON THE KEPT COMPONENT, HOLD ON THE EXCLUDED ONE",
                check=_tooth_fixed_point_distance_restriction(campaign),
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
