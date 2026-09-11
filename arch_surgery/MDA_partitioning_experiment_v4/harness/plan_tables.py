#!/usr/bin/env python
"""The experiment plan's results section, rendered from the stage records.

``EXPERIMENT_PLAN.md`` §4 carried a template: every cell a *format*, ``0.xxx``
where a ratio belongs and ``n`` where a count belongs, so that the shape could
be reviewed before anything was measured.  This module replaces that template
with the tables the measurement stages actually emitted, **by reading their
records** — ``runs/gates/<stage>/measurements.json`` — and writing the section
out.  No cell passes through a person's hands (protocol §15), and nothing here
computes a number: every table, caption and denominator is the stage's own.

What is rendered, and from which stage's record:

=========================  ==================================================
``gate_table``             §4.1, one row per registered gate
``tally_evaluation``       §4.2, the evaluation phase's tables
``tally_optimisation``     §4.3, the optimisation phase's tables
``recomputed_tables``      §4.4, the same cells from the second implementation
=========================  ==================================================

**What the cells are over, said once and in every caption.** While
``EXECUTION_APPROVED`` is False there is no campaign, so every cell in §4 is
over the **gate population** — the runs the verification gates made, one or two
seeds per arm — and not over the experiment's twenty-five.  A median over one
run and a median over twenty-five are different quantities with the same name,
which is trap T11's shape, so the section's heading marker says so, each
rendered caption is prefixed with it, and the campaign fills the section again
once the user approves execution.

Written by task **A55 (harness-smoke)**.
"""

from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from . import framework
from .config import EXECUTION_APPROVED, Campaign

__all__ = ["PlanTablesError", "render", "write", "SECTIONS"]


class PlanTablesError(RuntimeError):
    """A refusal to render.  Never a section with a hole in it."""


#: Where §4 starts and stops in the plan.  Both are matched on the whole line,
#: so a heading that has been reworded is a refusal rather than a silent
#: rewrite of the wrong part of the document.
SECTION_START = "## 4. Results"
SECTION_END = "## 5. Discussion"


@dataclass(frozen=True)
class Section:
    """One subsection of §4: which stage record fills it, and its heading."""

    number: str
    heading: str
    stage: str
    what: str


SECTIONS: tuple[Section, ...] = (
    Section(
        number="4.1",
        heading="Gates",
        stage="gate_table",
        what=(
            "one row per registered gate, read from the verdict records: what "
            "it binds, its population, its denominator, its mismatches and its "
            "teeth"
        ),
    ),
    Section(
        number="4.2",
        heading="The evaluation phase",
        stage="tally_evaluation",
        what=(
            "cost per call, matched accuracy on both rulers, the ownership "
            "rung, the per-sweep overhead, the failure taxonomy and the "
            "predicate trial"
        ),
    ),
    Section(
        number="4.3",
        heading="The optimisation phase",
        stage="tally_optimisation",
        what=(
            "the seed set and the failure table, the same-optimum check, both "
            "iteration constructions, the attempt-summation identity, the cost "
            "with and without the retried seeds, and the lift's residual"
        ),
    ),
    Section(
        number="4.4",
        heading="The same cells, computed a second time",
        stage="recomputed_tables",
        what=(
            "every cell of §4.2 and §4.3 recomputed by an implementation that "
            "shares no construction with the tally; the verdict on whether the "
            "two agree is gate `recomputation`'s, in §4.1"
        ),
    ),
)


def stage_record(records_dir: Path, stage: str) -> dict[str, Any]:
    """One stage's own record, or a refusal naming the stage that makes it."""
    path = Path(records_dir) / stage / "measurements.json"
    if not path.exists():
        raise PlanTablesError(
            f"stage {stage!r} has written no record at {path}.  §4's "
            f"{stage} tables are that stage's own output and are never typed "
            f"by hand: run `experiment_runner.py --measure {stage}` (or "
            f"`--measure all`) first."
        )
    try:
        return json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001
        raise PlanTablesError(f"{path} is not readable JSON: {exc}") from exc


def population_marker(campaign: Campaign, records_dir: Path) -> dict[str, Any]:
    """What every cell in §4 is over, measured from the records themselves.

    The commit, the record count, the audit position, the convergence ruler and
    the exit-audit instrument version, all read from the run records rather
    than written down here — a marker that says which instrument produced a
    residual, and is itself hand-maintained, is a marker that will one day name
    the wrong instrument.
    """
    root = Path(campaign.runs_dir) / framework.GATES_SUBPATH
    heads: dict[str, int] = {}
    kinds: dict[str, int] = {}
    positions: set[str] = set()
    rulers: set[str] = set()
    instruments: set[str] = set()
    total = 0
    for path in sorted(root.rglob("metrics.json")):
        try:
            record = json.loads(path.read_text())
        except Exception:  # noqa: BLE001 - a half-written record is not a row
            continue
        total += 1
        heads[str(record.get("tree_git_head"))] = (
            heads.get(str(record.get("tree_git_head")), 0) + 1
        )
        kinds[str(record.get("campaign_run_kind"))] = (
            kinds.get(str(record.get("campaign_run_kind")), 0) + 1
        )
        if record.get("audit_position"):
            positions.add(str(record["audit_position"]))
        if record.get("campaign_predicate_mode"):
            rulers.add(str(record["campaign_predicate_mode"]))
        instrument = (record.get("exit_audit") or {}).get("instrument") or {}
        if instrument.get("restores"):
            instruments.add(str(instrument["restores"]))
    return {
        "verdict_commit": framework.git_head(),
        "n_run_records": total,
        "records_by_commit": dict(sorted(heads.items())),
        "records_by_run_kind": dict(sorted(kinds.items())),
        "audit_positions": sorted(positions),
        "predicate_modes": sorted(rulers),
        "exit_audit_instrument": sorted(instruments),
        "execution_approved": EXECUTION_APPROVED,
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
    }


def _marker_sentence(marker: Mapping[str, Any]) -> str:
    """The one clause every caption in this section is prefixed with."""
    return (
        f"**Population: the gate runs, not the campaign.** "
        f"`EXECUTION_APPROVED` is {marker['execution_approved']}, so no "
        f"campaign record exists: every cell below is over the "
        f"{marker['n_run_records']} run record(s) the verification gates made "
        f"— one or two seeds per arm — at commit(s) "
        f"{', '.join(f'`{h[:8]}`' for h in marker['records_by_commit'])}, by "
        f"run kind {marker['records_by_run_kind']}. The exit audit was taken "
        f"at position(s) {', '.join(f'`{p}`' for p in marker['audit_positions'])} "
        f"with the convergence ruler(s) "
        f"{', '.join(f'`{r}`' for r in marker['predicate_modes'])} and the "
        f"exit-audit instrument "
        f"{', '.join(f'`{i}`' for i in marker['exit_audit_instrument'])}. The "
        f"campaign fills these tables again, over its own twenty-five seeds "
        f"per arm, after the user approves execution."
    )


def _table_block(table: Mapping[str, Any], marker_sentence: str) -> list[str]:
    """One emitted table as the plan prints it: caption, grid, denominator."""
    lines = [f"**`{table['table']}`**", ""]
    caption = str(table.get("caption") or "").strip()
    audit = table.get("audit_positions") or []
    audit_clause = (
        f" Audit position: {', '.join(f'`{p}`' for p in audit)}." if audit else ""
    )
    lines.append(
        f"*Caption: {caption}{audit_clause} "
        f"n = {table['denominator']} ({table['denominator_is']}). "
        f"{marker_sentence}*"
    )
    lines.append("")
    lines.extend(
        line for line in str(table.get("markdown") or "").splitlines() if line.strip()
    )
    lines.append("")
    if table.get("how_to_read"):
        lines.append(f"*How to read: {table['how_to_read']}*")
        lines.append("")
    return lines


def _gate_table_block(block: Mapping[str, Any], marker_sentence: str) -> list[str]:
    """§4.1: the gate table, which is a measurement stage and not a Table."""
    lines = [
        f"*Caption: {block['caption']} "
        f"Population: {block['population']}. {marker_sentence}*",
        "",
    ]
    lines.extend(
        line for line in str(block.get("markdown") or "").splitlines() if line.strip()
    )
    lines.append("")
    lines.append(
        f"**{block['n_pass']} PASS, {block['n_fail']} FAIL, "
        f"{block['n_not_run']} not run; {block['n_teeth_tripped']} of "
        f"{block['n_teeth']} teeth tripped.**"
    )
    lines.append("")
    lines.append(
        "*How to read: no number in §4.2–§4.4 is cited unless every row here "
        "is PASS with its tooth tripped; a FAIL is a result and the dependent "
        "tables are marked \"not produced — gate X failed\".*"
    )
    lines.append("")
    return lines


def render(campaign: Campaign, records_dir: Path | None = None) -> dict[str, Any]:
    """§4 of the plan, as markdown, with the record that says where it came from."""
    records_dir = Path(
        records_dir or (Path(campaign.runs_dir) / framework.GATES_SUBPATH)
    )
    marker = population_marker(campaign, records_dir)
    marker_sentence = _marker_sentence(marker)
    head = marker["verdict_commit"] or "unknown"
    lines: list[str] = [
        f"{SECTION_START} *(the gate population at `{head[:8]}` — **not** the "
        f"campaign; every cell is from gate runs, and the campaign fills the "
        f"section again after execution approval)*",
        "",
        "**Where these cells come from.** Every table below is emitted by a "
        "measurement stage of `experiment_runner.py` and rendered into this "
        "document by `harness/plan_tables.py`, which reads the stages' own "
        "records under `runs/gates/<stage>/measurements.json`. No cell is "
        "typed by hand (protocol §15), and nothing in this section is "
        "computed here: each caption, denominator and grid is the stage's.",
        "",
        marker_sentence,
        "",
        "**Conventions that hold in every table (D21 (c)).** Absolute cost "
        "cells are per-run means with the seed bracket. A ratio against the "
        "reference is given three ways: pooled (sum over the set / sum over "
        "the set), per-run median with `[min, max]`, and the count of seeds on "
        "which the arm cost more. Configurations appear in the fixed order "
        "nof / lad / st and are never pooled (D21 (b)). Prime calls appear "
        "beside node calls, never inside them (D19). Node-call ratios are the "
        "acceptance quantities; timings are context and no conclusion rests on "
        "one (I-10).",
        "",
    ]
    blocks: list[dict[str, Any]] = []
    n_tables = 0
    n_cells = 0
    for section in SECTIONS:
        record = stage_record(records_dir, section.stage)
        lines.append(f"### {section.number} {section.heading}")
        lines.append("")
        lines.append(
            f"*Emitted by `experiment_runner.py --measure {section.stage}`; "
            f"{section.what}.*"
        )
        lines.append("")
        if section.stage == "gate_table":
            lines.extend(_gate_table_block(record, marker_sentence))
            n_tables += 1
            n_cells += len(record.get("rows") or [])
            blocks.append(
                {
                    "section": section.number,
                    "stage": section.stage,
                    "n_tables": 1,
                    "n_rows": len(record.get("rows") or []),
                }
            )
            continue
        tables = record.get("tables") or []
        if not tables:
            raise PlanTablesError(
                f"stage {section.stage!r} emitted no table, so §{section.number} "
                f"would be an empty section presented as a result.  A section "
                f"with no population is not a section (trap T11)."
            )
        not_produced = record.get("tables_not_produced") or []
        for table in tables:
            lines.extend(_table_block(table, marker_sentence))
            n_tables += 1
            n_cells += len(table.get("rows") or []) * len(
                table.get("columns") or []
            )
        if not_produced:
            lines.append(
                f"*Not produced by this stage, each with its reason: "
                f"{_not_produced_text(not_produced)}*"
            )
            lines.append("")
        blocks.append(
            {
                "section": section.number,
                "stage": section.stage,
                "n_tables": len(tables),
                "n_not_produced": len(not_produced),
                "population": record.get("population"),
                "runs_provenance": record.get("runs_provenance"),
            }
        )
    markdown = "\n".join(lines).rstrip() + "\n"
    return {
        "markdown": markdown,
        "marker": marker,
        "sections": blocks,
        "n_tables": n_tables,
        "n_cells": n_cells,
        "records_dir": str(records_dir),
    }


def _not_produced_text(rows: Sequence[Any]) -> str:
    parts: list[str] = []
    for row in rows:
        if isinstance(row, Mapping):
            name = row.get("table") or row.get("name") or "?"
            why = row.get("why") or row.get("reason") or row
            parts.append(f"`{name}` — {why}")
        else:
            parts.append(str(row))
    return "; ".join(parts)


def plan_path(campaign: Campaign) -> Path:
    """The experiment plan this section belongs to."""
    return Path(campaign.runs_dir).parent / "EXPERIMENT_PLAN.md"


def write(
    campaign: Campaign, records_dir: Path | None = None, *, path: Path | None = None
) -> dict[str, Any]:
    """Replace §4 of the plan with the rendered section, in place.

    Only §4 is touched: the section is found by its own heading and the next
    one, and a document where either heading has moved or been reworded is a
    **refusal**, never a best-effort edit — a renderer that writes into the
    wrong part of a shared document is worse than one that does nothing.
    """
    document = Path(path) if path is not None else plan_path(campaign)
    text = document.read_text()
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith(SECTION_START)]
    ends = [i for i, line in enumerate(lines) if line.startswith(SECTION_END)]
    if len(starts) != 1 or len(ends) != 1 or ends[0] <= starts[0]:
        raise PlanTablesError(
            f"{document} does not hold exactly one section starting "
            f"{SECTION_START!r} followed by one starting {SECTION_END!r} "
            f"(found {len(starts)} and {len(ends)}).  The renderer replaces "
            f"that span and nothing else, and refuses rather than guessing "
            f"which part of a shared document it was asked to rewrite."
        )
    rendered = render(campaign, records_dir)
    body = rendered["markdown"].splitlines()
    replaced = lines[: starts[0]] + body + [""] + lines[ends[0] :]
    document.write_text("\n".join(replaced).rstrip() + "\n")
    rendered["document"] = str(document)
    rendered["n_lines_replaced"] = ends[0] - starts[0]
    rendered["n_lines_written"] = len(body)
    return rendered


def report(result: Mapping[str, Any]) -> None:
    """What was rendered, and over what, on the terminal."""
    marker = result["marker"]
    print(f"  records   : {result['records_dir']}")
    print(
        f"  population: {marker['n_run_records']} run record(s) at "
        f"{marker['records_by_commit']}, by run kind "
        f"{marker['records_by_run_kind']}"
    )
    print(f"  audit     : {marker['audit_positions']}")
    print(f"  rulers    : {marker['predicate_modes']}")
    print(f"  instrument: {marker['exit_audit_instrument']}")
    for block in result["sections"]:
        print(
            f"  §{block['section']:<5} {block['stage']:<20} "
            f"{block['n_tables']:>3} table(s)"
            + (
                f", {block['n_not_produced']} not produced"
                if block.get("n_not_produced")
                else ""
            )
        )
        provenance = block.get("runs_provenance") or {}
        if provenance:
            print(
                f"            runs read: {provenance.get('n_records')} "
                f"record(s) at {provenance.get('heads')}"
            )
    print(f"  {result['n_tables']} table(s), {result['n_cells']} cell(s)")
    if result.get("document"):
        print(
            f"  written   : {result['document']} — {result['n_lines_written']} "
            f"line(s) replacing {result['n_lines_replaced']}"
        )
