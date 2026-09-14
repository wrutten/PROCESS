#!/usr/bin/env python
"""A table, and the four things it cannot be emitted without.

The orchestration protocol's §16 says every table carries a concise caption:
units, what a row is, what a column is, what population the numbers summarise,
and which construction produced them.  That has been a review rule, and review
rules are remembered unevenly.  Here it is a **type error**: a
:class:`Table` cannot be constructed without a :class:`Caption`, and a caption
cannot be constructed without each of its parts.

Four refusals, each of which exists because of a specific way this project has
already been misled:

**No caption** — a table whose meaning requires the surrounding prose to decode
is incomplete (protocol §16).

**No denominator** — a count published over a population quietly smaller than
the one named is trap **T11**, this project's recurring error.  The denominator
is an integer and a sentence saying what it counts; a *placeholder* — the
literal ``n``, ``nn``, ``N``, ``?``, ``TBD``, ``—`` that the experiment plan's
own placeholder tables carry — is refused by name, so that a table copied out
of the plan's §4 template and filled in half way cannot be emitted.

**A timing column in an acceptance table** — no conclusion in this experiment
rests on a clock (issue I-10: a wall-clock-derived weight moved 6.4 % → 4.4 %
across runs of identical code, and it had already reached the arithmetic behind
a gate decision).  Timings are context, reported in their own section with
their repetition count.  A table marked ``acceptance=True`` refuses a column
whose name names a clock.

**A pooled-predicates column** — the two convergence tests this experiment
counts are not the same test and their widths differ by nearly two orders of
magnitude.  A column that adds them is a number belonging to neither, so a
:class:`Column` declares which predicate it belongs to and ``"pooled"`` is
refused.

And one more that is about *reading* rather than about emitting:

**An audit-position mix** — a residual measured at the entry to the output path
and one measured after the run are two different quantities.  A table whose
rows carry both positions must label the position per row; one that does not is
refused.

Written by task **A53 (harness-tally)**.  The caption vocabulary is the
experiment plan's §4 preamble; the refusals are the queue's A53 row.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

__all__ = [
    "TableError",
    "Caption",
    "Column",
    "Table",
    "PLACEHOLDER_DENOMINATORS",
    "TIMING_WORDS",
    "CELL_SEPARATOR",
    "cell_list",
]


class TableError(RuntimeError):
    """A refused table.  Never downgraded into a warning."""


#: Denominator spellings the experiment plan's placeholder tables use.  A table
#: reaching emission with one of these has been copied from the template and
#: not filled in, and is refused by name rather than printed with a letter
#: where a count belongs.
PLACEHOLDER_DENOMINATORS: frozenset[str] = frozenset(
    {"n", "nn", "nnn", "N", "k", "?", "-", "—", "–", "tbd", "TBD", "x", "xx", ""}
)

#: Words that name a clock.  A column whose name contains one of these as a
#: whole word may not appear in a table marked as an acceptance table.  The
#: list is words rather than substrings on purpose: the burn-time residual is
#: published in **seconds** and is not a timing, so "seconds" is not here and
#: "time" is not here either — what is refused is wall clock, CPU time and
#: their spellings.
TIMING_WORDS: frozenset[str] = frozenset(
    {
        "wall",
        "wall_s",
        "walltime",
        "clock",
        "cpu",
        "cpu_s",
        "elapsed",
        "runtime",
        "timing",
        "timings",
        "ms",
        "µs",
        "us",
        "loadavg",
        "maxrss",
        "s/run",
        "throughput",
    }
)

#: How a cell that carries several values joins them.  **One separator, in one
#: place**: the two accuracy tables joined their audit-instrument column with
#: two different spellings of the same idea (``";"`` and ``"; "``), which task
#: **A54 (harness-analysis)** found by having to reproduce both.  A separator
#: that lives beside each cell is a separator that drifts.
CELL_SEPARATOR = "; "


def cell_list(
    values: Sequence[Any], *, separator: str = CELL_SEPARATOR, empty: str = "—"
) -> str:
    """Several values in one cell, joined one way.

    ``empty`` is what an empty list reads as, and it is a dash rather than an
    empty string so that a cell with nothing in it is visibly a cell with
    nothing in it.
    """
    return separator.join(str(value) for value in values) if values else empty


_WORD = re.compile(r"[a-zA-Z_µ/]+")


def _words(text: str) -> set[str]:
    return {w.lower() for w in _WORD.findall(text)}


# --------------------------------------------------------------------------
# the caption
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Caption:
    """What a reader needs before the first cell means anything.

    Every field is required and none may be empty.  ``units`` may be the word
    "dimensionless" or "counts" — what it may not be is absent, because a
    number whose unit is left to inference is a number whose unit is guessed.
    """

    #: What the cells are measured in: "model executions", "dimensionless",
    #: "counts", "seconds", …
    units: str
    #: What one row is.
    row_is: str
    #: What one column is.
    column_is: str
    #: The population the cells summarise, in one clause.
    population: str
    #: Which construction produced them — the name of the function in
    #: ``harness/measurement/stats.py``, or the sentence its docstring declares.
    construction: str
    #: Clauses the plan requires in *this* caption: the audit position, the
    #: empty-visit disclaimer with its sweep share, the configuration confound.
    #: Each is a sentence; they are printed in order after the five above.
    clauses: tuple[str, ...] = ()
    #: One short note telling a reader how to read the table.
    how_to_read: str = ""

    def __post_init__(self) -> None:
        missing = [
            name
            for name in ("units", "row_is", "column_is", "population", "construction")
            if not str(getattr(self, name)).strip()
        ]
        if missing:
            raise TableError(
                f"a caption missing {missing}.  A table whose meaning requires "
                f"the surrounding prose to decode is incomplete (protocol §16)."
            )

    def text(self) -> str:
        parts = [
            f"units: {self.units}",
            f"a row is {self.row_is}",
            f"a column is {self.column_is}",
            f"population: {self.population}",
            f"construction: {self.construction}",
        ]
        return ".  ".join(parts + list(self.clauses)) + "."


# --------------------------------------------------------------------------
# a column
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Column:
    """One column: the key its cells are read from, and what it is.

    ``predicate`` says which convergence test a counter column belongs to.  It
    is ``None`` for a column that is not about a predicate at all, one of the
    names in ``stats.PREDICATES`` for a column that is, and ``"pooled"`` for a
    column built by adding the two — which is the thing the table refuses.
    """

    key: str
    heading: str
    #: ``None`` | "coupling_state" | "upstream" | "pooled"
    predicate: str | None = None
    #: How a cell is rendered.  A callable taking the raw value.
    fmt: Any = None

    def render(self, value: Any) -> str:
        if self.fmt is not None:
            return self.fmt(value)
        if value is None:
            return "—"
        if isinstance(value, float):
            return f"{value:.6g}"
        return str(value)


# --------------------------------------------------------------------------
# the table
# --------------------------------------------------------------------------


@dataclass
class Table:
    """One emitted table: a name, a caption, a denominator, columns and rows.

    Construction is where the refusals happen, so a table that exists is a
    table that may be printed.

    ``acceptance`` marks a table one of the plan's acceptance verdicts is read
    from.  Such a table refuses a timing column.  A context table — the
    wall-clock section — is built with ``acceptance=False`` and may carry one,
    which is exactly where a timing belongs.

    ``audit_position_labelled`` says the table carries the audit position as a
    column of its own.  Without it, rows that name more than one position are
    refused: a residual taken at the entry to the output path and one taken
    after the run are two different quantities, and pooling them unlabelled is
    the thing the experiment plan's §3.3 says must not happen.
    """

    name: str
    caption: Caption
    columns: tuple[Column, ...]
    rows: tuple[Mapping[str, Any], ...]
    denominator: int
    denominator_is: str
    acceptance: bool = False
    audit_position_labelled: bool = False
    #: Set by :meth:`__post_init__`: the audit positions the rows name.
    audit_positions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.caption, Caption):
            raise TableError(
                f"table {self.name!r} was built without a caption.  A table "
                f"whose meaning requires the surrounding prose to decode is "
                f"incomplete (protocol §16)."
            )
        self._check_denominator()
        self._check_timing()
        self._check_predicates()
        self._check_audit_position()

    # --- the four refusals -------------------------------------------------

    def _check_denominator(self) -> None:
        value = self.denominator
        if isinstance(value, str):
            if value.strip() in PLACEHOLDER_DENOMINATORS:
                raise TableError(
                    f"table {self.name!r} carries the placeholder denominator "
                    f"{value!r}.  The experiment plan's §4 tables print a "
                    f"letter where a count belongs, deliberately, because "
                    f"nothing is measured there yet; a table emitted with one "
                    f"is a table copied from the template and not filled in."
                )
            raise TableError(
                f"table {self.name!r} has a denominator of {value!r}, which is "
                f"not a count.  Every count carries the denominator of the "
                f"things actually compared (protocol §12)."
            )
        if value is None or not isinstance(value, int) or isinstance(value, bool):
            raise TableError(
                f"table {self.name!r} has no denominator.  A count published "
                f"over a population quietly smaller than the one named is this "
                f"project's trap T11."
            )
        if value < 0:
            raise TableError(
                f"table {self.name!r} has a denominator of {value}, which is "
                f"not a number of things."
            )
        if not str(self.denominator_is).strip():
            raise TableError(
                f"table {self.name!r} states a denominator of {value} without "
                f"saying what it counts.  '{value}' of what?"
            )

    def _check_timing(self) -> None:
        if not self.acceptance:
            return
        offending = [
            column.heading
            for column in self.columns
            if _words(column.heading) & TIMING_WORDS or _words(column.key) & TIMING_WORDS
        ]
        if offending:
            raise TableError(
                f"acceptance table {self.name!r} carries the timing "
                f"column(s) {offending}.  No conclusion in this experiment "
                f"rests on a timing (issue I-10): the acceptance quantities "
                f"are counts and bit-comparisons, which reproduce exactly, and "
                f"wall clock is reported as context in its own section with "
                f"its repetition count."
            )

    def _check_predicates(self) -> None:
        pooled = [c.heading for c in self.columns if c.predicate == "pooled"]
        if pooled:
            raise TableError(
                f"table {self.name!r} carries the pooled-predicate "
                f"column(s) {pooled}.  The objective/constraint test and the "
                f"coupling-state test are not the same test — an arm stops on "
                f"exactly one of them and their widths differ by nearly two "
                f"orders of magnitude — so their sum is a number belonging to "
                f"neither.  Publish one column per predicate."
            )

    def _check_audit_position(self) -> None:
        positions = sorted(
            {
                str(row["audit_position"])
                for row in self.rows
                if row.get("audit_position") is not None
            }
        )
        object.__setattr__(self, "audit_positions", tuple(positions))
        if len(positions) > 1 and not self.audit_position_labelled:
            raise TableError(
                f"table {self.name!r} mixes exit audits taken at "
                f"{positions} without labelling the position.  A residual "
                f"measured at the entry to the output path and one measured "
                f"after the run are two different quantities; the two may "
                f"share a table only with the position in a column of its own."
            )

    # --- emission ----------------------------------------------------------

    def header(self) -> list[str]:
        return [column.heading for column in self.columns]

    def body(self) -> list[list[str]]:
        return [
            [column.render(row.get(column.key)) for column in self.columns]
            for row in self.rows
        ]

    def markdown(self) -> str:
        """The table as markdown, caption first, how-to-read last."""
        lines = [f"*Caption: {self.caption.text()}*", ""]
        headings = self.header()
        lines.append("| " + " | ".join(headings) + " |")
        lines.append("|" + "|".join("---" for _ in headings) + "|")
        for row in self.body():
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")
        lines.append(
            f"*n = {self.denominator} ({self.denominator_is}).*"
        )
        if self.caption.how_to_read:
            lines.append("")
            lines.append(f"*How to read: {self.caption.how_to_read}*")
        return "\n".join(lines)

    def text(self, *, width: int = 2) -> str:
        """The table as aligned plain text, for the terminal."""
        headings = self.header()
        body = self.body()
        widths = [
            max(len(headings[i]), *(len(row[i]) for row in body)) if body
            else len(headings[i])
            for i in range(len(headings))
        ]
        pad = " " * width
        lines = [pad.join(h.ljust(w) for h, w in zip(headings, widths))]
        lines.append(pad.join("-" * w for w in widths))
        for row in body:
            lines.append(pad.join(cell.ljust(w) for cell, w in zip(row, widths)))
        return "\n".join(lines)

    def as_record(self) -> dict[str, Any]:
        """The table as data, for the stage's own JSON record."""
        return {
            "table": self.name,
            "caption": self.caption.text(),
            "how_to_read": self.caption.how_to_read,
            "denominator": self.denominator,
            "denominator_is": self.denominator_is,
            "acceptance": self.acceptance,
            "audit_positions": list(self.audit_positions),
            "columns": [
                {"key": c.key, "heading": c.heading, "predicate": c.predicate}
                for c in self.columns
            ],
            "rows": [dict(row) for row in self.rows],
            "markdown": self.markdown(),
        }
