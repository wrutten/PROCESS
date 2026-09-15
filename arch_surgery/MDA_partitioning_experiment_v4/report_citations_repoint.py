"""Re-point every table citation in the report at the table set A87 renders.

**A table number is a position, not a name** (trap T17).  Task **A87
(v3-grid-polish)** took the reliability table out of the main text — the
twenty-three-column merge of per-arm success, the failure taxonomy and the
seed set — and put the per-arm success construction alone in its place, in the
previous revision's §5.1 form; the merged whole went to Appendix D, first of
the optimisation phase's group.  So **no main-text number moves** (the new
grid takes the old one's slot, Table 11), every appendix number from D.12 on
moves by one, and the companion's full versions re-order because the main
text's table no longer has one of its own.

This script is that re-pointing, committed and executed (protocol §15) rather
than done by hand.  It works from a **map of layout → old number → new
number** rather than from a shift, because a shift is not what a move is: the
companion's per-arm-success full version went from F.10 to F.13 while the
three below it each rose by one.  A citation is rewritten to a placeholder
first and then to its new number, so a number that is both an old and a new
one is never rewritten twice.

**A number that still resolves can still be the wrong table** (trap T17's
addition).  Table 11 is still called *per-arm success* and is still in §4.3,
but it no longer carries the failure taxonomy's *ok* column, its tracebacks or
the seed-set table's *retried seeds per arm* — three sentences cited it for
exactly those, and each is re-pointed by a phrase below after re-reading every
citation in the document and asking what its sentence is about.

Every phrase it cannot find is reported, not skipped silently.

Run from the V4 folder, after ``--plan-tables write``:

    python report_citations_repoint.py
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT = HERE / "EXPERIMENT_REPORT.md"

#: ``old citation → new citation``, by prefix.  The layout each names is in
#: the comment, because a number is a position and the layout is the name.
MOVES: dict[str, dict[int, str]] = {
    # --- the main text.  Nothing moves: the per-arm success grid takes the
    #     merged table's slot (Table 11) and §3's Tables 1-6 are hand-written.
    "": {},
    # --- Appendix D.  D.1-D.11 do not move; D.12 is the merged reliability
    #     table, arriving at the head of the optimisation phase's group.
    "D.": {
        12: "D.13",  # the problem each configuration poses
        13: "D.14",  # node calls per module
        14: "D.15",  # the location diagnostic
        15: "D.16",  # the identity B1 -> B2
        16: "D.17",  # iteration multiplier (check 2)
        17: "D.18",  # cost (check 4)
        18: "D.19",  # cost against both anchors
        19: "D.20",  # sweeps and prime calls
        20: "D.21",  # achieved accuracy
        21: "D.22",  # the lift closed (check 3)
    },
    # --- the companion file.  F.1-F.9 do not move.  The full versions
    #     re-order: the main text's per-arm success grid no longer renders
    #     one of its own (it names the merged table's, `per_seed_columns_in`),
    #     so the three that followed rise by one and it falls to F.13.
    "F.": {
        10: "F.13",  # per-arm success, full -> the merged table's full version
        11: "F.10",  # the reference entries, full
        12: "F.11",  # cost per call, full
        13: "F.12",  # the ownership rung, full
    },
}

#: Citations a number map cannot carry: a **range** that no longer spans one
#: run of tables, and four numbers that have not existed since task A79
#: combined the per-configuration tables and which two re-pointings left
#: behind (the addition trap **T17** carries).  Each is replaced by a
#: placeholder **before** the number map runs and restored after it, so the
#: numbers inside its replacement are final and are never swept twice.
PHRASES: list[tuple[str, str]] = [
    # --- the range of every rendered table, in §4.4 ------------------------
    ("Tables 7–18 and Tables D.2–D.21",
     "Tables 7–18 and Tables D.2–D.22"),
    # --- citations that would survive the map as a **plausible wrong one**
    #     (trap T17's addition).  Table 11 kept its number and its name and
    #     lost three column sets to Appendix D's merged table; each sentence
    #     below was reading one of them.
    # The traceback text is the failure taxonomy's `detail` column.
    ("`block FLAT did not converge in 20 sweeps` on 2 / 3 starts, Table 11)*",
     "`block FLAT did not converge in 20 sweeps` on 2 / 3 starts, Table 11; "
     "the message is Table D.12's)*"),
    # The paragraph reads the per-arm grid **and** the taxonomy's tracebacks
    # and the seed-set table's invalid and retried seeds.
    ("**The population (Table 11).**", "**The population (Tables 11 and D.12).**"),
    # *ok* is the failure taxonomy's column, not a column of Table 11.
    ("counted *ok*\nin Table 11 and *failed* in companion Table F.7",
     "counted *ok*\nin Table D.12 and *failed* in companion Table F.7"),
    # The retried seeds per arm are the seed-set table's column.
    ("retried seeds per arm across the 25 offered (Table 11; companion Table F.7;",
     "retried seeds per arm across the 25 offered (Tables 11 and D.12; "
     "companion Table F.7;"),
]

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
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
