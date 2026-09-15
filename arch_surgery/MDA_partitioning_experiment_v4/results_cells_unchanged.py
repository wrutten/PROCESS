#!/usr/bin/env python
"""Every cell of the old results section is a cell of the new documents, unchanged.

Task **A79 (report-captions)** moved the report's rendered tables from §4 into
Appendix D and a companion file, shortened every caption, omitted the per-seed
columns from the report's copies and added three headline tables.  It was
allowed to change **how** a cell is presented and never a cell.  This script
is the proof: it takes the report at a base commit (``git show``, never a
working tree), cuts every rendered table out of its §4 — the gate table, the
two tally sections and the recomputed section — and does the same for the
working tree's Appendix D and ``RESULTS_TABLES_FULL.md``; every cell becomes
``(implementation, table construction name, row index, column heading) →
value``, keyed by the construction name printed under each table and **never
by a table number or a caption**; and it reports whether the old set is a
subset of the new set with 0 value differences, listing every cell present
before and absent now.  Expected: none absent, 0 differences, and a new set
larger than the old by exactly the headline tables' cells.

The gate table is compared beside, not inside, the subset: its *compared* and
*mismatched* columns are gate populations, and two of them (``recomputation``,
``tally_contracts``) count the tables emitted, which this task increased.
Their movement is printed so that a reader sees it rather than infers it.

Usage::

    python results_cells_unchanged.py --base 4dac585e
    python results_cells_unchanged.py --base 4dac585e --show 30

No PROCESS run.  Exit status 0 when the old cells are a subset with 0
differences, 3 otherwise.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT = HERE / "EXPERIMENT_REPORT.md"
COMPANION = HERE / "RESULTS_TABLES_FULL.md"

Cell = tuple[str, str, int, str]

_OLD_TITLE = re.compile(r"^\*\*`(.+)`\*\*$")
_NEW_NAME = re.compile(r"^<sub>`(.+)`</sub>$")


def _repo_root() -> Path:
    return Path(
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(HERE), check=True, capture_output=True, text=True,
        ).stdout.strip()
    )


def report_at(commit: str) -> str:
    relative = REPORT.relative_to(_repo_root())
    return subprocess.run(
        ["git", "show", f"{commit}:{relative.as_posix()}"],
        cwd=str(_repo_root()), check=True, capture_output=True, text=True,
    ).stdout


def _split_row(line: str) -> list[str]:
    inner = line.strip()
    assert inner.startswith("|") and inner.endswith("|"), line
    return [c.strip() for c in inner[1:-1].split(" | ")]


def _grid_cells(
    grid: list[str], implementation: str, name: str
) -> dict[Cell, str]:
    """``{(implementation, name, row index, column heading): value}`` of one grid."""
    if len(grid) < 2:
        return {}
    header = _split_row(grid[0])
    cells: dict[Cell, str] = {}
    for r, line in enumerate(grid[2:]):
        values = _split_row(line)
        if len(values) != len(header):
            raise SystemExit(
                f"{implementation} {name!r}: row {r} has {len(values)} cells "
                f"against {len(header)} headings — the grid is malformed"
            )
        for heading, value in zip(header, values):
            cells[(implementation, name, r, heading)] = value
    return cells


def old_cells(text: str) -> tuple[dict[Cell, str], dict[Cell, str], Counter]:
    """The rendered tables of the report's §4 at the base commit.

    A table is a ``**`name`**`` title followed by its grid; the section it
    sits in says which implementation made it (4.2/4.3 the tally, 4.4 the
    analysis).  The gate table (4.1) has no title and is returned apart.
    """
    lines = text.split("\n")
    start = next(i for i, l in enumerate(lines) if l.startswith("## 4. Results"))
    end = next(i for i, l in enumerate(lines) if l.startswith("## 5. Discussion"))
    implementation = "?"
    name: str | None = None
    grid: list[str] = []
    cells: dict[Cell, str] = {}
    gate: dict[Cell, str] = {}
    counts: Counter = Counter()

    def flush() -> None:
        """Emit a finished grid under the title that preceded it.  The title
        arrives lines before its grid (the caption sits between), so the
        pending name survives until a grid has been emitted under it."""
        nonlocal grid, name
        if grid:
            table = "gate table" if implementation == "gate" else (name or "?")
            block = _grid_cells(grid, implementation, table)
            (gate if implementation == "gate" else cells).update(block)
            counts[implementation] += 1
            grid, name = [], None

    for line in lines[start:end]:
        if line.startswith("|"):
            grid.append(line)
            continue
        flush()
        if line.startswith("### 4.1"):
            implementation = "gate"
        elif line.startswith("### 4.2") or line.startswith("### 4.3"):
            implementation = "tally"
        elif line.startswith("### 4.4"):
            implementation = "recomputed"
        title = _OLD_TITLE.match(line.strip())
        if title:
            name = title.group(1)
    flush()
    return cells, gate, counts


def new_cells(text: str, *, default_implementation: str) -> tuple[dict[Cell, str], dict[Cell, str], Counter]:
    """The rendered tables of Appendix D or of the companion file.

    A table is a grid followed by ``<sub>`name`</sub>``; in the companion the
    ``## F.4`` heading switches the implementation to the analysis.
    """
    lines = text.split("\n")
    implementation = default_implementation
    grid: list[str] = []
    cells: dict[Cell, str] = {}
    gate: dict[Cell, str] = {}
    counts: Counter = Counter()
    for line in lines:
        if line.startswith("## F.4"):
            implementation = "recomputed"
        elif line.startswith("## F.") or line.startswith("### D."):
            implementation = default_implementation
        if line.startswith("|"):
            grid.append(line)
            continue
        named = _NEW_NAME.match(line.strip())
        if named and grid:
            name = named.group(1)
            if name == "gate table":
                gate.update(_grid_cells(grid, "gate", name))
                counts["gate"] += 1
            else:
                cells.update(_grid_cells(grid, implementation, name))
                counts[implementation] += 1
            grid = []
    return cells, gate, counts


def appendix_d(text: str) -> str:
    lines = text.split("\n")
    start = next(i for i, l in enumerate(lines) if l.startswith("## Appendix D — Results tables"))
    return "\n".join(lines[start:])


def has_digit(value: str) -> bool:
    return any(ch.isdigit() for ch in value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--base", required=True, help="the commit whose §4 is the 'before'")
    parser.add_argument("--show", type=int, default=20, help="how many absent or differing cells to print")
    args = parser.parse_args(argv)

    before, gate_before, counts_before = old_cells(report_at(args.base))
    d_cells, gate_after, counts_d = new_cells(appendix_d(REPORT.read_text()), default_implementation="tally")
    f_cells, _gate_f, counts_f = new_cells(COMPANION.read_text(), default_implementation="tally")
    after = dict(f_cells)
    after.update(d_cells)  # the report's copy wins where a table is in both; the cells agree by construction

    # The same cell printed in both documents must read the same.
    both = set(d_cells) & set(f_cells)
    disagree_between_documents = [k for k in both if d_cells[k] != f_cells[k]]

    absent = [k for k in before if k not in after]
    differing = [k for k in before if k in after and before[k] != after[k]]
    numeric_before = sum(1 for v in before.values() if has_digit(v))
    numeric_after = sum(1 for v in after.values() if has_digit(v))
    tables_before = {(k[0], k[1]) for k in before}
    tables_after = {(k[0], k[1]) for k in after}
    new_tables = sorted(tables_after - tables_before)
    gone_tables = sorted(tables_before - tables_after)

    print(f"before: §4 at {args.base} — {len(before)} cells ({numeric_before} with a digit) in "
          f"{len(tables_before)} tables (tally {counts_before['tally']}, recomputed {counts_before['recomputed']}), "
          f"plus the gate table ({len(gate_before)} cells)")
    print(f"after : Appendix D — {len(d_cells)} cells in {counts_d['tally']} tables; {COMPANION.name} — "
          f"{len(f_cells)} cells in {counts_f['tally'] + counts_f['recomputed']} tables "
          f"(tally {counts_f['tally']}, recomputed {counts_f['recomputed']}); union {len(after)} cells "
          f"({numeric_after} with a digit) in {len(tables_after)} tables; the gate table {len(gate_after)} cells")
    print(f"cells printed in both documents: {len(both)}; disagreeing between them: {len(disagree_between_documents)}")
    print(f"old cells absent now : {len(absent)} of {len(before)}")
    print(f"old cells differing  : {len(differing)} of {len(before) - len(absent)} compared")
    print(f"tables new since {args.base}: {len(new_tables)}; tables gone: {len(gone_tables)}")
    for implementation, name in new_tables[:args.show]:
        n = sum(1 for k in after if (k[0], k[1]) == (implementation, name))
        print(f"  NEW   [{implementation}] {name}  ({n} cells)")
    for implementation, name in gone_tables[:args.show]:
        print(f"  GONE  [{implementation}] {name}")
    for key in absent[:args.show]:
        print(f"  ABSENT  {key} = {before[key]!r}")
    for key in differing[:args.show]:
        print(f"  DIFFERS {key}: {before[key]!r} -> {after[key]!r}")
    for key in disagree_between_documents[:args.show]:
        print(f"  D≠F     {key}: {d_cells[key]!r} vs {f_cells[key]!r}")

    # The gate table, beside: which cells moved, by gate and column.
    moved = [k for k in gate_before if k in gate_after and gate_before[k] != gate_after[k]]
    gate_absent = [k for k in gate_before if k not in gate_after]
    print(f"gate table: {len(gate_before)} cells before, {len(gate_after)} after; "
          f"{len(moved)} moved, {len(gate_absent)} absent (compared beside the subset, not inside it)")
    rows_before = {k[2]: v for k, v in gate_before.items() if k[3] == "gate"}
    for key in moved[:args.show]:
        print(f"  MOVED   {rows_before.get(key[2], '?')} · {key[3]}: {gate_before[key]!r} -> {gate_after[key]!r}")

    ok = not absent and not differing and not disagree_between_documents
    print("VERDICT:", "the old cells are a subset of the new, 0 value differences" if ok else "NOT a clean subset")
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
