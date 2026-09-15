"""Section 4 of the report before and after the arm renaming: names only?

The arm renaming of 2026-09-15 (``harness.core.records.RECORDED_ARM_NAMES``)
changed no number.  Section 4 of ``EXPERIMENT_REPORT.md`` is rendered from the
measurement stages' records and never typed by hand, so after the tally
stages are re-run over the same 949 campaign records and the section is
re-rendered, every difference between the old section and the new one must be
a name.  This script is the proof: it takes the report at a base commit and
the report in the working tree, cuts section 4 out of each by the renderer's
own markers, applies the **reverse** of the recorded-name table to the new
section — today's names back to the names the old section was rendered under
— and diffs the result against the old section line for line.  0 differing
lines means names only; anything else is printed and is a finding.

The reverse translation is applied in the order that makes it a bijection on
the tokens: the table renames one arm onto another's old name (today's ``A1``
was ``A0p``; today's ``A2`` was ``A1``), so the token that is a *value* of the
table and also a *key* of it is translated first.

Usage::

    python renamed_section_diff.py --base abcd15e0
    python renamed_section_diff.py --base abcd15e0 --show 20

No PROCESS run.  Exit status 0 on names only, 3 otherwise.
"""

from __future__ import annotations

import argparse
import difflib
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from harness.core import records as records_mod  # noqa: E402
from harness.measurement import plan_tables  # noqa: E402

REPORT = HERE / "EXPERIMENT_REPORT.md"


def section_4(text: str) -> list[str]:
    """The lines of section 4, by the renderer's own start and end markers."""
    lines = text.split("\n")
    start, end = plan_tables.section_span(REPORT, lines)
    return lines[start:end]


def reverse_translation_order() -> list[tuple[str, str]]:
    """``(today, recorded)`` pairs, values that are also keys first."""
    table = records_mod.RECORDED_ARM_NAMES
    pairs = [(today, recorded) for recorded, today in table.items()]
    pairs.sort(key=lambda p: (p[0] not in table, p[0]))
    return pairs


def reverse_translate(lines: list[str]) -> list[str]:
    """Today's arm names back to the recorded ones, whole tokens only.

    A single pass with one alternation, so that a token translated by one
    pair is never re-translated by the next.
    """
    pairs = dict(reverse_translation_order())
    pattern = re.compile(r"\b(" + "|".join(re.escape(t) for t in pairs) + r")\b")
    return [pattern.sub(lambda m: pairs[m.group(1)], line) for line in lines]


def report_at(commit: str) -> str:
    relative = REPORT.relative_to(_repo_root())
    return subprocess.run(
        ["git", "show", f"{commit}:{relative.as_posix()}"],
        cwd=str(_repo_root()),
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _repo_root() -> Path:
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=str(HERE),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return Path(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", required=True, help="the commit whose report is the old section")
    parser.add_argument("--show", type=int, default=40, help="how many differing lines to print")
    args = parser.parse_args(argv)

    old = section_4(report_at(args.base))
    new = section_4(REPORT.read_text())
    reversed_new = reverse_translate(new)

    pairs = reverse_translation_order()
    token = re.compile(r"\b(" + "|".join(re.escape(t) for t, _ in pairs) + r")\b")
    n_tokens_translated = sum(len(token.findall(line)) for line in new)
    raw_differing = sum(1 for a, b in zip(old, new) if a != b) + abs(len(old) - len(new))

    diff = list(
        difflib.unified_diff(old, reversed_new, "section 4 at " + args.base, "section 4 now, names reversed", lineterm="", n=0)
    )
    differing = [line for line in diff[2:] if line[:1] in "+-" and not line.startswith(("+++", "---"))]

    print(f"section 4 at {args.base}: {len(old)} lines; now: {len(new)} lines")
    print(f"reverse translation applied: {' , '.join(f'{t} -> {r}' for t, r in pairs)}; {n_tokens_translated} token(s) reversed")
    print(f"lines differing before the reverse translation: {raw_differing} of {max(len(old), len(new))}")
    positions = sum(1 for a, b in zip(old, reversed_new) if a != b) + abs(len(old) - len(new))
    print(
        f"lines differing after the reverse translation: {positions} of "
        f"{max(len(old), len(new))} line position(s) ({len(differing)} unified-diff lines)"
    )
    if len(old) == len(new):
        # Which subsection each residual difference falls in, so that a reader
        # can see whether the measurement tables (§4.2-§4.4) moved or only the
        # gate table (§4.1), whose rows are re-made by every press.
        by_subsection: dict[str, int] = {}
        current = "(before the first subsection)"
        for a, b in zip(old, reversed_new):
            if a.startswith("### "):
                current = a.split(" ")[1]
            if a != b:
                by_subsection[current] = by_subsection.get(current, 0) + 1
        print("residual differing lines by subsection: " + ", ".join(f"{k}: {v}" for k, v in by_subsection.items()) if by_subsection else "residual differing lines by subsection: none")
    if differing:
        for line in differing[: args.show]:
            print("  " + line[:200])
        if len(differing) > args.show:
            print(f"  … {len(differing) - args.show} more")
        print("VERDICT: NOT names only")
        return 3
    print("VERDICT: names only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
