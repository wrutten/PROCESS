#!/usr/bin/env python
"""Every cell the report and the companion carried before, still carried now.

A **rendering** change is one that moves cells, never one that changes them.
Task A83 (headline-tables-in-text) combined the tally's per-(configuration,
source) tables of one construction into one grid and moved three of them into
the main text; ``--plan-tables check`` proves the documents are the ones the
records produce *now*, and says nothing about whether the cells are the ones
they produced *before*.  This script is that half.

**How a cell is keyed.**  Not by table number — a table number is a position
and every one of them moved (trap T17) — but by

    (construction, configuration, source, row, column)

where *construction*, *configuration* and *source* come from the construction
name printed under each grid (``<sub>`cost per call — large_tokamak_nof —
campaign_displaced`</sub>``), *row* is the whole row as
``{column heading: cell}``, and *column* is the heading.  The old documents
print one grid per construction name; the new ones print one grid per
**layout**, naming under it every stage table it combines.  So the test is a
containment:

    every row of every old grid appears, whole, inside some row of the new
    grid that names that old grid as one of the tables it combines

Whole, because a row-for-row containment catches a cell that moved to the
wrong row, which a multiset of values per column would not.  Where a layout
declares a combined heading for a column its constituents spelled differently
(``vs A0 pooled`` against ``vs A1 pooled``), the declaration — the same one
the renderer used — translates the old heading before the comparison; it is
named in the output, so a heading silently renamed is a heading a reader can
see was renamed.

**What a missing row means.** The second implementation's 107 recomputed
tables are, by the same task's decision, no longer rendered anywhere: gate
``recomputation``'s row of the gate table is that check.  Their rows are
reported as *withdrawn by construction*, listed by kind and counted, and are
the only missing rows this script expects.  Anything else is a defect.

Run from the V4 folder:

    python report_cells_preserved.py --base c45cac1c

Reads the two documents at *base* through ``git show`` and the two in the
working tree; starts no PROCESS run and reads no run record.
"""

from __future__ import annotations

import argparse
import collections
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
REPORT = "EXPERIMENT_REPORT.md"
COMPANION = "RESULTS_TABLES_FULL.md"

#: The construction name a grid prints under itself.
_SUB = re.compile(r"^<sub>`(.+)`</sub>$")
#: The line a combined grid prints beside it, naming what it combines.
_COMBINES = re.compile(r"^<sub>combining \d+ stage table\(s\): (.+)</sub>$")
#: A cell carries a number if it holds a digit; the headline count is over
#: these, so that "yes", "—" and an arm name do not inflate it.
_HAS_DIGIT = re.compile(r"\d")


class Grid:
    """One rendered table: its construction name(s), headings and rows."""

    def __init__(self, name: str, headings: list[str], rows: list[list[str]]):
        self.name = name
        self.section = ""
        self.combines: list[str] = []
        self.headings = headings
        self.rows = [
            {headings[i]: cell for i, cell in enumerate(row) if i < len(headings)}
            for row in rows
        ]

    @property
    def names(self) -> list[str]:
        return self.combines or [self.name]


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_rule(line: str) -> bool:
    return bool(re.fullmatch(r"\|[\s:|-]+\|", line.strip()))


def grids(text: str) -> list[Grid]:
    """Every markdown grid in *text*, with the construction line under it."""
    lines = text.splitlines()
    out: list[Grid] = []
    section = ""
    i = 0
    while i < len(lines):
        if lines[i].startswith("#"):
            section = lines[i].lstrip("# ").strip()
        if not lines[i].startswith("|"):
            i += 1
            continue
        block = []
        while i < len(lines) and lines[i].startswith("|"):
            block.append(lines[i])
            i += 1
        if len(block) < 2 or not _is_rule(block[1]):
            continue
        headings = _cells(block[0])
        body = [_cells(line) for line in block[2:]]
        name = ""
        combines: list[str] = []
        for look in lines[i : i + 6]:
            found = _SUB.match(look.strip())
            if found and not name:
                name = found.group(1)
            more = _COMBINES.match(look.strip())
            if more:
                combines = [
                    part.strip().strip("`") for part in more.group(1).split(";")
                ]
        if not name:
            continue
        grid = Grid(name, headings, body)
        grid.combines = combines
        grid.section = section
        out.append(grid)
    return out


def _group_row(row: dict[str, str]) -> bool:
    """A sub-heading row: one bold label and nothing else."""
    values = [v for v in row.values() if v]
    return len(values) == 1 and values[0].startswith("**")


def layouts_by_title() -> dict[str, Any]:
    """``the construction name a combined grid prints`` → its layout.

    The layouts are the renderer's own — imported, never restated — so the
    heading a combined column carries is read here exactly as the renderer
    wrote it.  A ``single`` table prints its constituent's own name and
    renames nothing, so it is absent from this map and translates nothing.
    """
    sys.path.insert(0, str(HERE))
    from harness.measurement import plan_tables  # noqa: PLC0415

    return {layout.title: layout for layout in plan_tables.LAYOUTS}


def _construction_key(name: str) -> str:
    """The construction a stage table's name starts with."""
    return str(name).split(" — ")[0].strip()


def _kind_of(name: str, kinds: dict[str, str]) -> str:
    return kinds.get(_construction_key(name), "")


def _translate(
    row: dict[str, str],
    name: str,
    host: Grid,
    layouts: dict[str, Any],
    kinds: dict[str, str],
    keys_by_heading: dict[tuple[str, str], str],
) -> dict[str, str]:
    """One old row with its headings read as *host* spells them."""
    layout = layouts.get(host.name)
    overrides = dict(getattr(layout, "headings", ()) or ())
    if not overrides:
        return dict(row)
    kind = _kind_of(name, kinds)
    out: dict[str, str] = {}
    for heading, cell in row.items():
        key = keys_by_heading.get((kind, heading))
        out[overrides.get(key, heading) if key else heading] = cell
    return out


def keys_by_heading() -> tuple[dict[tuple[str, str], str], dict[str, str]]:
    """``(kind, heading) → column key`` and ``construction → kind``, read from
    the stage records: the same records both renderings were made from."""
    import json  # noqa: PLC0415

    out: dict[tuple[str, str], str] = {}
    kinds: dict[str, str] = {}
    for stage in ("tally_evaluation", "tally_optimisation", "recomputed_tables"):
        path = HERE / "runs" / "gates" / stage / "measurements.json"
        if not path.exists():
            continue
        for table in json.loads(path.read_text()).get("tables") or []:
            kind = str(table.get("kind") or "")
            # The second implementation's tables carry no kind and share the
            # tally's construction names; a kind already read from a tally
            # table is never overwritten by the empty one beside it.
            construction = _construction_key(table.get("table") or "")
            if kind or construction not in kinds:
                kinds[construction] = kind
            for column in table.get("columns") or []:
                if isinstance(column, dict):
                    out[(kind, str(column.get("heading")))] = str(column.get("key"))
    return out, kinds


def at(base: str, name: str) -> str:
    rel = f"arch_surgery/MDA_partitioning_experiment_v4/{name}"
    return subprocess.run(
        ["git", "show", f"{base}:{rel}"],
        cwd=HERE,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def compare(base: str) -> dict[str, Any]:
    layouts = layouts_by_title()
    by_heading, kinds = keys_by_heading()

    old = grids(at(base, REPORT)) + grids(at(base, COMPANION))
    new = grids((HERE / REPORT).read_text()) + grids((HERE / COMPANION).read_text())

    where: dict[str, list[Grid]] = collections.defaultdict(list)
    for grid in new:
        for name in grid.names:
            where[name].append(grid)

    n_rows = n_cells = n_numeric = 0
    kept_rows = kept_cells = kept_numeric = 0
    n_recomputed_grids = 0
    missing_rows = 0
    missing_not_recomputed = 0
    differing: list[dict[str, Any]] = []
    fewer: collections.Counter[str] = collections.Counter()
    withdrawn: collections.Counter[str] = collections.Counter()
    for grid in old:
        # The second implementation's copies sat in the companion's own
        # group and carry the tally's construction names; they are told
        # apart by where they sat, not by what they are called.
        recomputed = "computed a second time" in grid.section
        if recomputed:
            n_recomputed_grids += 1
        hosts = [] if recomputed else where.get(grid.name, [])
        for row in grid.rows:
            if _group_row(row):
                continue
            n_rows += 1
            n_cells += len(row)
            numeric = sum(1 for cell in row.values() if _HAS_DIGIT.search(cell))
            n_numeric += numeric
            if hosts:
                kept_rows += 1
                kept_cells += len(row)
                kept_numeric += numeric
            if not hosts:
                if not recomputed:
                    missing_not_recomputed += 1
                kind = _kind_of(grid.name, kinds) or "(no kind: recomputed)"
                label = (
                    f"the second implementation's copies of "
                    f"`{_construction_key(grid.name)}`"
                    if recomputed
                    else f"NOT the second implementation's: {kind} — "
                    f"`{grid.name}`"
                )
                withdrawn[label] += 1
                fewer[grid.name] += 1
                missing_rows += 1
                continue
            hit = False
            best = 0
            worst: dict[str, str] = {}
            for host in hosts:
                wanted = _translate(row, grid.name, host, layouts, kinds, by_heading)
                for candidate in host.rows:
                    if _group_row(candidate):
                        continue
                    agree = sum(
                        1
                        for heading, cell in wanted.items()
                        if candidate.get(heading) == cell
                    )
                    if agree == len(wanted):
                        hit = True
                        break
                    if agree > best:
                        best, worst = agree, wanted
                if hit:
                    break
            if not hit:
                differing.append(
                    {
                        "construction": grid.name,
                        "row": dict(list((worst or row).items())[:8]),
                        "cells_matched_at_best": best,
                        "cells_in_the_row": len(row),
                        "hosts": [host.name for host in hosts],
                    }
                )
    return {
        "base": base,
        "n_old_grids": len(old),
        "n_old_grids_recomputed": n_recomputed_grids,
        "n_new_grids": len(new),
        "n_old_rows_compared": n_rows,
        "n_old_cells_compared": n_cells,
        "n_old_numeric_cells_compared": n_numeric,
        "n_rows_kept": kept_rows,
        "n_cells_kept": kept_cells,
        "n_numeric_cells_kept": kept_numeric,
        "n_rows_missing": missing_rows,
        "n_rows_missing_not_the_second_implementation": missing_not_recomputed,
        "n_rows_differing": len(differing),
        "differing": differing[:20],
        "withdrawn_by_kind": dict(sorted(withdrawn.items())),
        "constructions_rendered_fewer_times": dict(sorted(fewer.items())),
        "heading_translations": {
            f"{title}.{key}": heading
            for title, layout in sorted(layouts.items())
            for key, heading in (getattr(layout, "headings", ()) or ())
        },
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="c45cac1c")
    args = parser.parse_args(list(argv) if argv is not None else None)
    result = compare(args.base)
    print(f"cell preservation against {result['base']}")
    print(
        f"  grids     : {result['n_old_grids']} before "
        f"(of which {result['n_old_grids_recomputed']} the second "
        f"implementation's), {result['n_new_grids']} now"
    )
    print(
        f"  compared  : {result['n_old_rows_compared']} row(s), "
        f"{result['n_old_cells_compared']} cell(s), of which "
        f"{result['n_old_numeric_cells_compared']} carry a number"
    )
    print(
        f"  preserved : {result['n_rows_kept']} row(s), "
        f"{result['n_cells_kept']} cell(s), of which "
        f"{result['n_numeric_cells_kept']} carry a number — each found whole "
        f"inside a row of the table that now combines it"
    )
    print(
        f"  missing   : {result['n_rows_missing']} row(s), of which "
        f"{result['n_rows_missing_not_the_second_implementation']} are not "
        f"the second implementation's"
    )
    print(f"  differing : {result['n_rows_differing']} row(s)")
    for row in result["differing"]:
        print(
            f"    DIFFERING {row['construction']} (in {row['hosts']}): "
            f"{row['cells_matched_at_best']} of {row['cells_in_the_row']} "
            f"cell(s) matched at best — {row['row']}"
        )
    if result["heading_translations"]:
        print("  headings the layouts rename, translated before comparing:")
        for key, heading in result["heading_translations"].items():
            print(f"    {key} → {heading!r}")
    if result["withdrawn_by_kind"]:
        print("  rendered fewer times than before, by kind (expected):")
        for kind, n in result["withdrawn_by_kind"].items():
            print(f"    {n:>5} row(s)  {kind}")
    print(
        "  VERDICT   : "
        + (
            "every cell preserved"
            if not result["n_rows_differing"]
            else "CELLS DIFFER"
        )
        + (
            f"; {result['n_rows_missing']} row(s) withdrawn by construction"
            if result["n_rows_missing"]
            else "; nothing withdrawn"
        )
    )
    return (
        1
        if result["n_rows_differing"]
        or result["n_rows_missing_not_the_second_implementation"]
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
