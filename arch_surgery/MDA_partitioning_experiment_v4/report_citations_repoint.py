"""Re-point every table citation in the report at the table set A88 renders.

**A table number is a position, not a name** (trap T17).  Task **A88
(function-weighted-sweeps)** took the per-node table out of the main text at
the user's instruction (2026-09-17: *"move the per node tables to the
appendix. Only keep per module in the main text"*): §4.2's Table 9 — node
calls per block on the displaced entries — is now one row group of Appendix
D's Table D.3, the construction rendered whole over its four regimes, and
its rendered block leaves the document.  So **every main-text number from 10
on falls by one** (Tables 10–18 → 9–17); Appendix D.1–D.22 do not move and
the two new function-weighted tables are D.23 and D.24 in the new group D.4;
the companion does not move.

This script is that re-pointing, committed and executed (protocol §15) rather
than done by hand.  It (1) removes the orphaned rendered block — the renderer
rewrites the blocks whose layouts exist and leaves one whose layout is gone
where it stands — (2) applies the phrases below, which re-point by **meaning**
rather than by number, and (3) applies the number map to every citation span
outside the rendered blocks and Appendix C.  A citation is rewritten to a
placeholder first and then to its new number, so a number that is both an old
and a new one is never rewritten twice.

**A number that still resolves can still be the wrong table** (trap T17's
addition).  Two sentences cited Table 9 for what it carried — the headline
ratio and the absolute per-evaluation totals, which are Table 8's cells too,
and the per-module ratios, which are the module sweeps table's cells (the
same numbers in sweeps: a ratio of sweeps is a ratio of node calls within a
group) — and one in §5.2 cited "Table 9's TOTAL rows" for the transfer
factors' inputs, which are Table 8's `A1→A2` / `A0→A2` cells.  Each is
re-pointed by a phrase after re-reading every citation and asking what the
sentence is about; the map would have sent all three to Table D.3, which
resolves and is the wrong table for two of them.

Every phrase it cannot find is reported, not skipped silently.

Run from the V4 folder, before ``--plan-tables write``:

    python report_citations_repoint.py
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT = HERE / "EXPERIMENT_REPORT.md"

#: Rendered main-text blocks whose layout no longer exists: removed whole,
#: markers included, with the one blank line that followed.  The renderer
#: never removes a block, so this is the committed record of the removal.
REMOVED_BLOCKS: tuple[str, ...] = ("node_calls_per_block",)

#: ``old citation → new citation``, by prefix.  The layout each names is in
#: the comment, because a number is a position and the layout is the name.
MOVES: dict[str, dict[int, str]] = {
    # --- the main text.  Table 9 (node calls per block, displaced) leaves;
    #     everything after it falls by one.  A bare "Table 9" that no phrase
    #     below has claimed is the per-node grid and goes to D.3.
    "": {
        9: "D.3",   # node calls per block, displaced -> one row group of D.3
        10: "9",    # module sweeps per run, the evaluation phase
        11: "10",   # per-arm success
        12: "11",   # same optimum (check 1)
        13: "12",   # optimiser iterations per run
        14: "13",   # evaluations of the model set per run
        15: "14",   # model-node executions per evaluation
        16: "15",   # model-node executions per run
        17: "16",   # check 4 -- the cost
        18: "17",   # module sweeps per run, the optimisation phase
    },
    # --- Appendix D.  Nothing moves: D.3 absorbs the displaced regime as a
    #     row group and the two new tables are D.23 and D.24 at the end.
    "D.": {},
    # --- the companion file.  Nothing moves.
    "F.": {},
}

#: Citations a number map cannot carry.  Each is replaced by a placeholder
#: **before** the number map runs and restored after it, so the numbers
#: inside its replacement are final and are never swept twice.
PHRASES: list[tuple[str, str]] = [
    # --- the range of every rendered table, in §4.4 ------------------------
    ("Tables 7–18 and Tables D.2–D.22",
     "Tables 7–17 and Tables D.2–D.24"),
    # --- the three citations that would survive the map as a **plausible
    #     wrong one** (trap T17's addition): Table 9 cited for cells that
    #     are Table 8's or the module sweeps table's.
    # The headline ratio 0.5625 / 0.5772 / 0.5016 is Table 8's `A1->A2` /
    # `A0->A2` cell.
    ("(Table D.5, headline Table 9).** At matched achieved accuracy",
     "(Table D.5, headline Table 8).** At matched achieved accuracy"),
    # The absolute per-evaluation totals are Table 8's per-arm cells; the
    # per-module ratios are the sweep table's own cells (identical numbers),
    # and the node-call form with the per-block absolute counts is D.3's
    # displaced row group.
    ("0.4921; `A2` cost more on **0 of 25** seeds on every configuration). In absolute terms 60.5 / 59.6 /\n"
     "61.5 node calls per evaluation against 107.5 / 103.3 / 122.6 for the reference. Where the saving\n"
     "sits (Table 9, the pooled ratio of `A2` to its reference block by block): the once-per-run",
     "0.4921; `A2` cost more on **0 of 25** seeds on every configuration). In absolute terms 60.5 / 59.6 /\n"
     "61.5 node calls per evaluation against 107.5 / 103.3 / 122.6 for the reference (Table 8's per-arm\n"
     "cells). Where the saving sits (Table 9, the pooled ratio of `A2` to its reference module by\n"
     "module — the same ratios in node calls per block, with the per-block absolute counts, are the\n"
     "displaced-entry row group of Table D.3): the once-per-run"),
    # §5.2: the transfer factors' Phase A inputs are the headline ratios,
    # which are Table 8's rung cells; "Table 9's TOTAL rows" carried the same
    # numbers and is now a row group of D.3.
    ("Table 9's TOTAL rows and Table D.18, not cells themselves).",
     "Table 8's `A1→A2` / `A0→A2` cells and Table D.18, not cells themselves)."),
]


def remove_blocks(text: str) -> tuple[str, list[str]]:
    """The orphaned rendered blocks taken out whole, and which were found."""
    removed: list[str] = []
    for name in REMOVED_BLOCKS:
        start = f"<!-- plan_tables: main-text table {name} -->"
        end = f"<!-- plan_tables: end of main-text table {name} -->"
        if start not in text or end not in text:
            continue
        i = text.index(start)
        j = text.index(end) + len(end)
        tail = text[j:]
        # the blank line the renderer wrote after the block goes with it
        if tail.startswith("\n\n"):
            tail = tail[2:]
        text = text[:i] + tail
        removed.append(name)
    return text, removed


def hold_rendered(text: str) -> tuple[str, list[str]]:
    """Lift out the parts a citation sweep must not touch.

    The rendered blocks are the renderer's and are rewritten by it.  **The
    change log is history**: each of its entries states the table set of its
    own day (task A82's entry says so in as many words), so a number in it is
    a record and not a citation.
    """
    held: list[str] = []

    def keep(match: re.Match[str]) -> str:
        held.append(match.group(0))
        return f"\x00HELD{len(held) - 1}\x00"

    text = re.compile(
        r"<!-- plan_tables: main-text table (\w+) -->.*?"
        r"<!-- plan_tables: end of main-text table \1 -->",
        re.S,
    ).sub(keep, text)
    text = re.compile(
        r"## Appendix C — Change log.*?(?=## Appendix D — Results tables)", re.S
    ).sub(keep, text)
    text = re.compile(
        r"## Appendix D — Results tables.*?"
        r"<!-- plan_tables: end of the rendered results tables -->",
        re.S,
    ).sub(keep, text)
    return text, held


#: What a citation looks like: ``Table 9``, ``Tables D.2–D.21``, ``Tables 13,
#: 14 and 15``, ``companion Table F.7`` — the word, then one or more numbers
#: joined by a dash, a comma, ``and`` or a semicolon.  **Only numbers inside
#: such a span are rewritten**, so ``F = 10``, ``§3.7`` and ``0.7812`` are not
#: citations and are left alone.
CITATION = re.compile(
    r"(?:companion\s+)?Tables?\s+"
    r"(?:[DF]\.)?\d+"
    r"(?:\s*(?:–|—|-|,|;|\band\b|\bto\b)\s*(?:companion\s+)?"
    r"(?:Tables?\s+)?(?:[DF]\.)?\d+)*",
    re.S,
)

#: One number inside a citation span.
NUMBER = re.compile(r"(?<![A-Za-z0-9.])(?:[DF]\.)?\d+")


def apply_moves(text: str) -> tuple[str, list[str]]:
    """Every number inside a citation span rewritten, once."""
    done: list[str] = []

    def rewrite_span(span: re.Match[str]) -> str:
        def rewrite(one: re.Match[str]) -> str:
            spelling = one.group(0)
            prefix, number = ("", spelling)
            if spelling[:2] in ("D.", "F."):
                prefix, number = spelling[:2], spelling[2:]
            new = MOVES.get(prefix, {}).get(int(number))
            if new is None:
                return spelling
            done.append(f"{spelling} → {new}")
            return new

        return NUMBER.sub(rewrite, span.group(0))

    return CITATION.sub(rewrite_span, text), done


def main() -> int:
    text = REPORT.read_text(encoding="utf-8")
    text, removed = remove_blocks(text)
    text, held = hold_rendered(text)
    # The phrases go behind placeholders first: their replacements already
    # name the final numbers, and the map must not sweep them again.
    applied: list[str] = []
    missing: list[str] = []
    stand_ins: list[str] = []
    for old, new in PHRASES:
        if old in text:
            text = text.replace(old, f"\x02{len(stand_ins)}\x02")
            stand_ins.append(new)
            applied.append(f"{old!r} → {new!r}")
        else:
            missing.append(repr(old))
    text, moves = apply_moves(text)
    for index, new in enumerate(stand_ins):
        text = text.replace(f"\x02{index}\x02", new)
    for index, kept in enumerate(held):
        text = text.replace(f"\x00HELD{index}\x00", kept)
    REPORT.write_text(text, encoding="utf-8")

    print(f"re-pointed {REPORT.name}")
    print(f"  rendered blocks removed: {removed} (declared: {list(REMOVED_BLOCKS)})")
    print(f"  phrases applied  : {len(applied)}")
    for line in applied:
        print(f"    {line}")
    print(f"  phrases not found: {len(missing)}")
    for line in missing:
        print(f"    {line}")
    print(f"  number moves     : {len(moves)}")
    for line in moves:
        print(f"    {line}")
    print(
        "  held out of the sweep: the rendered blocks and Appendix C, whose "
        "entries state the table set of their own day"
    )
    not_removed = [n for n in REMOVED_BLOCKS if n not in removed]
    if not_removed:
        print(f"  blocks declared removed and not found: {not_removed}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
