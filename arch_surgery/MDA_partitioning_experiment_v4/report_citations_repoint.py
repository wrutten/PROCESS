"""Re-point every table citation in the report at the table set A86 renders.

**A table number is a position, not a name** (trap T17).  Task **A86
(v3-tables-remainder)** built the eleven tables of the previous revision's §4
and §5 that A85 had not, moved the taxonomy, the same-optimum table and the
cost sums into the main text, and put the main text's tables into **reading
order** — so every number in both documents moved, and the hand-written text
cites them.

This script is that re-pointing, committed and executed (protocol §15) rather
than done by hand.  It works from a **map of layout → old number → new
number** rather than from a shift, because the moves are not a shift: the
per-module evaluation table went from 12 to 10 while the iteration multiplier
went from 8 to 13, and two appendix tables became main-text ones.  A citation
is rewritten to a placeholder first and then to its new number, so a number
that is both an old and a new one is never rewritten twice.

Every phrase it cannot find is reported, not skipped silently — the previous
revision of this script left three citations behind before A85 found them by
re-reading every one, which is the addition trap T17 now carries.

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
    # --- the main text.  §3's Tables 1-6 are hand-written and do not move.
    "": {
        7: "9",    # node calls per block
        8: "13",   # the iteration multiplier
        9: "14",   # the evaluation count ε
        10: "15",  # node calls per evaluation ρ
        11: "16",  # node calls per run R
        12: "10",  # module sweeps per run, the evaluation phase
        13: "18",  # module sweeps per run, the optimisation phase
    },
    # --- Appendix D.  D.1 (the gate table) does not move; D.10 and D.11
    #     became main-text Tables 11 and 12.
    "D.": {
        2: "D.3",    # node calls per block, the other three regimes
        3: "D.4",    # the reference entries
        4: "D.5",    # cost per call
        5: "D.6",    # matched accuracy
        6: "D.9",    # fixed-point distance
        7: "D.10",   # the ownership rung
        8: "D.11",   # failure taxonomy, the evaluation phase
        9: "D.13",   # node calls per module
        10: "11",    # per-arm success — now a main-text table
        11: "12",    # same optimum (check 1) — now a main-text table
        12: "D.16",  # iteration multiplier (check 2)
        13: "D.17",  # cost (check 4)
        14: "D.20",  # achieved accuracy
        15: "D.21",  # the lift closed (check 3)
    },
    # --- the companion file.
    "F.": {
        1: "F.3",    # module sweeps, the other three regimes
        2: "F.4",    # per-sweep overhead, the evaluation phase
        3: "F.5",    # the predicate trial
        4: "F.6",    # per-arm success by seed
        5: "F.7",    # the failure table
        6: "F.8",    # the attempt-summation identity
        7: "F.9",    # per-sweep overhead, the optimisation phase
        8: "F.11",   # the reference entries, full
        9: "F.12",   # cost per call, full
        10: "F.13",  # the ownership rung, full
        11: "F.10",  # per-arm success, full
        12: "F.14",  # iteration multiplier, full
        13: "F.15",  # achieved accuracy, full
    },
}

#: Citations a number map cannot carry: a **range** that no longer spans one
#: run of tables, and four numbers that have not existed since task A79
#: combined the per-configuration tables and which two re-pointings left
#: behind (the addition trap **T17** carries).  Each is replaced by a
#: placeholder **before** the number map runs and restored after it, so the
#: numbers inside its replacement are final and are never swept twice.
PHRASES: list[tuple[str, str]] = [
    # --- the range of every rendered table, in §4.4 and §6 ----------------
    ("Tables 7–9 and Tables D.2–D.15",
     "Tables 7–18 and Tables D.2–D.21"),
    # --- four numbers that no longer exist (stale since A79) --------------
    # The stencil regimes are rows of the cost-per-call table and blocks of
    # the companion's stencil grids, not tables of their own.
    ("(Table D.4 and\nD.37–D.42)", "(Table D.5 and companion Table F.2)"),
    # The per-configuration cost tables are row groups of check 4's table.
    ("(Table D.13,\nD.73–D.75, D.82–D.83)", "(Table D.17)"),
    # Per-arm success is now a main-text table.
    ("(Tables\nD.67–D.69, added 2026-09-15 under D29)",
     "(Table 11, added 2026-09-15 under D29)"),
    ("(Tables\n  D.76–D.78, columns", "(Table D.17, columns"),
    # --- citations that would survive the map as a **plausible wrong one**
    #     (trap T17's addition): the number resolves, and the table it now
    #     names is not what the sentence is about.  Each was found by
    #     re-reading every citation after the map, not by the checker.
    # The ownership rung's per-call ratio is the per-call cost table's own
    # `A0→A1` column, not the per-block table's.
    ("**The ownership rung `A0 → A1` (Table 7, displaced entries).**",
     "**The ownership rung `A0 → A1` (Table 8, displaced entries).**"),
    ("**`A0 → A1` — ownership of the burn time (Table 7).**",
     "**`A0 → A1` — ownership of the burn time (Table 8).**"),
    # The paragraph now sits under check 1's own table, which carries the
    # verdicts it reads.
    ("**The same fixed point, not merely an equally converged one (Tables D.5 and D.6).**",
     "**The same fixed point, not merely an equally converged one (Table 7; "
     "Tables D.6 and D.9).**"),
    # Check 4's headline is the cost-sums table in §4.3; the per-arm table is
    # the appendix's.
    ("**RQ2 — the partitioning inside the optimisation, `B0 → B2` (Table D.13, headline Tables 11 and 13).**",
     "**RQ2 — the partitioning inside the optimisation, `B0 → B2` (Table 17; "
     "per arm Table D.17; headline Tables 16 and 18).**"),
    # `per module Table 8` named the iteration multiplier and `the path
    # Table 9` named one of the path's four tables: two citations A85's
    # re-pointing left pointing at a plausible wrong table.
    ("(RQ2; Table D.13;\nper module Table 8; the path Table 9)",
     "(RQ2; Tables 17 and D.17;\nper module Table 18; the path Tables 13–16)"),
    # A doubled word the previous re-pointing left behind, three times.
    ("are companion\ncompanion Table F.2.", "are companion Table F.4."),
    ("companion\ncompanion Table F.5;", "companion Table F.7;"),
    ("companion companion Table F.6 (the identity) and companion Table F.7",
     "companion Table F.8 (the identity) and companion Table F.9"),
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
