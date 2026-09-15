#!/usr/bin/env python
"""How many tables the report carries and how long their captions are, before and after.

The count table task **A79 (report-captions)** publishes: for the report at a
base commit (``git show``) and for the working tree's report and companion
file — the number of rendered tables, the number of caption lines each carries
(the old renderer printed ``*Caption:`` twice per table; the new one prints one
``**Table X.n.**`` line), and the caption lengths in characters and in lines
at a stated width.  Every number is over a stated population and the script
is what produced it (protocol §15).

A **rendered table** is a markdown grid (``|`` lines) under a title: at the
base commit a ``**`name`**`` line, in the new documents a ``**Table D.n.**`` /
``**Table F.n.**`` line.  A **caption line** is a ``*Caption:`` line, a
``*How to read:`` line or a ``**Table X.n.**`` line — the lines a reader must
read before the grid means anything, whichever renderer wrote them.  The
hand-written tables of §1–§3 and the appendices are counted apart, as the
lines starting ``*Caption:`` outside the rendered block (before) or the
``**Table n.**`` lines (after).

Usage::

    python caption_census.py --base 4dac585e [--width 100]

No PROCESS run.
"""

from __future__ import annotations

import argparse
import math
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT = HERE / "EXPERIMENT_REPORT.md"
COMPANION = HERE / "RESULTS_TABLES_FULL.md"

_OLD_TITLE = re.compile(r"^\*\*`.+`\*\*$")
_NEW_TITLE = re.compile(r"^\*\*Table ([DF])\.\d+\.\*\* \*(.*)\*$")
_HAND_TITLE = re.compile(r"^\*\*Table (\d+|[A-C]\.\d+)\.\*\* \*(.*)\*$")
_OLD_CAPTION = re.compile(r"^\*Caption: (.*)\*$")


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


def _lines_at(chars: int, width: int) -> int:
    return max(1, math.ceil(chars / width))


def _stats(values: list[int]) -> str:
    if not values:
        return "—"
    ordered = sorted(values)
    return f"median {ordered[len(ordered) // 2]}, max {ordered[-1]}"


def census_old(text: str, width: int) -> dict[str, object]:
    """The report before: §4's rendered tables and their ``*Caption:`` lines."""
    lines = text.split("\n")
    start = next(i for i, l in enumerate(lines) if l.startswith("## 4. Results"))
    end = next(i for i, l in enumerate(lines) if l.startswith("## 5. Discussion"))
    section = lines[start:end]
    n_tables = sum(1 for l in section if _OLD_TITLE.match(l.strip()))
    # the gate table has no title line but has a caption; count it as a table
    n_tables += 1
    caption_lines = [l for l in section if l.startswith("*Caption:")]
    how_to_read = [l for l in section if l.startswith("*How to read:")]
    per_table_caption_lines = len(caption_lines) / n_tables if n_tables else 0
    chars = [len(_OLD_CAPTION.match(l).group(1)) if _OLD_CAPTION.match(l) else len(l) for l in caption_lines]
    hand = [l for i, l in enumerate(lines) if l.startswith("*Caption:") and not (start <= i < end)]
    return {
        "document": "EXPERIMENT_REPORT.md §4 (before)",
        "n_tables": n_tables,
        "n_caption_lines": len(caption_lines),
        "n_how_to_read_lines": len(how_to_read),
        "caption_lines_per_table": per_table_caption_lines,
        "caption_chars": _stats(chars),
        "caption_lines_at_width": _stats([_lines_at(c, width) for c in chars]),
        "n_hand_written_captions_outside": len(hand),
        "hand_written_caption_chars": _stats([len(l) for l in hand]),
    }


def census_new(text: str, name: str, width: int, *, block_only: bool) -> dict[str, object]:
    """A new document: ``**Table X.n.**`` titles, one per table."""
    lines = text.split("\n")
    if block_only:
        start = next(i for i, l in enumerate(lines) if l.startswith("## Appendix D — Results tables"))
        section = lines[start:]
        outside = lines[:start]
    else:
        section, outside = lines, []
    titles = [m for l in section if (m := _NEW_TITLE.match(l.strip()))]
    stray = [l for l in section if l.startswith("*Caption:") or l.startswith("*How to read:")]
    grids = 0
    in_grid = False
    for l in section:
        if l.startswith("|"):
            if not in_grid:
                grids += 1
            in_grid = True
        else:
            in_grid = False
    chars = [len(m.group(2)) for m in titles]
    hand = [m for l in outside if (m := _HAND_TITLE.match(l.strip()))]
    return {
        "document": name,
        "n_tables": len(titles),
        "n_grids": grids,
        "n_caption_lines": len(titles) + len(stray),
        "n_stray_old_style_caption_lines": len(stray),
        "caption_lines_per_table": (len(titles) + len(stray)) / len(titles) if titles else 0,
        "caption_chars": _stats(chars),
        "caption_lines_at_width": _stats([_lines_at(c, width) for c in chars]),
        "n_hand_written_captions_outside": len(hand),
        "hand_written_caption_chars": _stats([len(m.group(2)) for m in hand]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--base", required=True)
    parser.add_argument("--width", type=int, default=100, help="characters per line for the line estimate")
    args = parser.parse_args(argv)
    rows = [
        census_old(report_at(args.base), args.width),
        census_new(REPORT.read_text(), "EXPERIMENT_REPORT.md Appendix D (after)", args.width, block_only=True),
        census_new(COMPANION.read_text(), "RESULTS_TABLES_FULL.md (after)", args.width, block_only=False),
    ]
    keys = [
        "n_tables", "n_grids", "n_caption_lines", "n_how_to_read_lines",
        "n_stray_old_style_caption_lines", "caption_lines_per_table",
        "caption_chars", "caption_lines_at_width",
        "n_hand_written_captions_outside", "hand_written_caption_chars",
    ]
    print(f"| measure | " + " | ".join(str(r["document"]) for r in rows) + " |")
    print("|---|" + "---|" * len(rows))
    for key in keys:
        values = []
        for r in rows:
            v = r.get(key, "—")
            values.append(f"{v:.2f}" if isinstance(v, float) else str(v))
        print(f"| {key} | " + " | ".join(values) + " |")
    print(f"\n(line estimate at {args.width} characters per line; a caption's characters exclude the title and the markup)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
