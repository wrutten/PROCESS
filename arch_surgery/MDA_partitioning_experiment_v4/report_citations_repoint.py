"""Re-point every table citation in the report at the table set A85 renders.

**A table number is a position, not a name** (trap T17).  Task **A85
(v3-table-formats)** put the previous revision's §4 and §5 forms back, which
added two per-module tables to the main text, split the optimiser's path into
the four one-quantity tables the previous revision's §5.3 shape holds, and
moved the node-call per-module table into Appendix D.  Every number after
those moves shifted, and the hand-written text cites them.

This script is that re-pointing, committed and executed (protocol §15) rather
than done by hand: it names each move, applies the shifts **from the highest
number down** so a shifted number is never shifted twice, and prints what it
changed and what it could not find.  A phrase it cannot find is reported, not
skipped silently — the previous revision of this script left three citations
behind (``Table 9 and D.34–D.36`` among them), which this run also repairs.

Run from the V4 folder, after ``--plan-tables write``:

    python report_citations_repoint.py
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT = HERE / "EXPERIMENT_REPORT.md"

#: Citations naming a table by an old number, longest first.  Applied before
#: the numeric shifts, because each names a table the shifts would move.
PHRASES: list[tuple[str, str]] = [
    # --- citations left behind by the previous re-pointing (stale) ---------
    ("(Table 9 and D.34–D.36)", "(Tables D.5 and D.6)"),
    ("(Table 9, frozen ruler; the mixed ruler reads the same or lower on every row)",
     "(Table D.5, frozen ruler; the mixed ruler reads the same or lower on every row)"),
    ("(median 2.435 / 0.1816 / 0.2575, Table 9)",
     "(median 2.435 / 0.1816 / 0.2575, Table D.5)"),
    ("Table D.4 the stencil regime; Table 9 matched accuracy",
     "Table D.4 the stencil regime; Table D.5 matched accuracy"),
    # --- the optimiser's path, now four tables of one quantity each --------
    ("headline Tables 8 and 9", "headline Tables 11 and 13"),
    ("**The optimiser's path decomposes that ratio (Table 9).**",
     "**The optimiser's path decomposes that ratio (Tables 8–11).**"),
    ("the same numbers as Table 9's ε row", "the same numbers as Table 9"),
    ("the per-run\nmean over Table 9's ε", "the per-run\nmean over Table 9"),
    # --- node calls per module, now Appendix D -----------------------------
    ("Per module (Table 8, the whole run's census)",
     "Per module (Table 13 in sweeps, Table D.9 in node calls — the whole run's "
     "census)"),
    # A stale citation the previous re-pointing left: the sentence is about
    # the optimisation's evaluation counts, which are check 2's table, not
    # the evaluation phase's matched accuracy.
    ("(three took more evaluations, Table\nD.5)",
     "(three took more evaluations, Table\nD.12)"),
    # The solve-phase decomposition is the node-call per-module table's, now
    # in the appendix.
    ("The census total less its\nlast row",
     "The node-call census total of Table D.9 less its\nlast row"),
    # --- the placeholders this task's own new prose left ------------------
    ("MODULE_EVAL_REF", "Table 12"),
]

#: ``prefix`` → the lowest old number that moved, and by how much.  Applied
#: from the highest number down.
SHIFTS: list[tuple[str, int, int]] = [
    # Appendix D gained `node calls per module` at D.9, so D.9 and up move up
    # one; the companion gained `module sweeps, the other three regimes` at
    # F.1, so every F number moves up one.
    ("D", 9, 1),
    ("F", 1, 1),
]

#: The highest number of each prefix before the move, so the descending sweep
#: covers every one of them.
CEILING = {"D": 14, "F": 12}


def apply_phrases(text: str) -> tuple[str, list[str], list[str]]:
    done: list[str] = []
    missing: list[str] = []
    for old, new in PHRASES:
        if old in text:
            text = text.replace(old, new)
            done.append(f"{old!r} → {new!r}")
        else:
            missing.append(repr(old))
    return text, done, missing


def apply_shifts(text: str) -> tuple[str, list[str]]:
    done: list[str] = []
    for prefix, lowest, by in SHIFTS:
        for number in range(CEILING[prefix], lowest - 1, -1):
            old = f"{prefix}.{number}"
            new = f"{prefix}.{number + by}"
            # A number is a citation only where a table is named: `Table D.9`,
            # `Tables D.9 and D.10`, `companion Table F.4`.  Bare `D.9` also
            # names the appendix's own sub-section headings, which move with
            # their tables and must not be rewritten here, so the pattern
            # requires the number to follow `Table`, `Tables`, `and` or a
            # comma inside a citation.
            pattern = re.compile(
                rf"(?<![A-Za-z0-9.])(?<!### ){re.escape(old)}(?![0-9])"
            )
            hits = len(pattern.findall(text))
            if hits:
                text = pattern.sub(new, text)
                done.append(f"{old} → {new} ({hits})")
    return text, done


def main() -> int:
    text = REPORT.read_text(encoding="utf-8")
    # The rendered blocks are the renderer's and are rewritten by it; the
    # shifts must not touch them, so they are lifted out and put back.
    held: list[str] = []

    def hold(match: re.Match[str]) -> str:
        held.append(match.group(0))
        return f"\x00HELD{len(held) - 1}\x00"

    block = re.compile(
        r"<!-- plan_tables: main-text table (\w+) -->.*?"
        r"<!-- plan_tables: end of main-text table \1 -->",
        re.S,
    )
    text = block.sub(hold, text)
    appendix = re.compile(
        r"## Appendix D — Results tables.*?"
        r"<!-- plan_tables: end of the rendered results tables -->",
        re.S,
    )
    text = appendix.sub(hold, text)

    # The shifts run **first**, so a phrase's replacement may name the final
    # number and will not itself be shifted afterwards.
    text, shifts = apply_shifts(text)
    text, phrases, missing = apply_phrases(text)

    for index, kept in enumerate(held):
        text = text.replace(f"\x00HELD{index}\x00", kept)
    REPORT.write_text(text, encoding="utf-8")

    print(f"re-pointed {REPORT.name}")
    print(f"  phrases applied : {len(phrases)}")
    for line in phrases:
        print(f"    {line}")
    print(f"  phrases not found: {len(missing)}")
    for line in missing:
        print(f"    {line}")
    print(f"  number shifts   : {len(shifts)}")
    for line in shifts:
        print(f"    {line}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
