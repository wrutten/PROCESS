#!/usr/bin/env python
"""The report's results tables, rendered from the stage records.

``EXPERIMENT_REPORT.md`` §4 carried a template — every cell a *format*,
``0.xxx`` where a ratio belongs and ``n`` where a count belongs — so that the
shape could be reviewed before anything was measured.  This module renders the
tables the measurement stages actually emitted, **by reading their records**
(``runs/gates/<stage>/measurements.json``) and writing them out.  No cell
passes through a person's hands (protocol §15), and nothing here computes a
number: every table, caption and denominator is the stage's own.

**Where the tables go (task A79 (report-captions), the user's rulings of
2026-09-15; task A83 (headline-tables-in-text), the user's of the same day).**
The report's main text §4 states conclusions in prose, and **the three
headline tables stand in §4 beside the paragraphs that read them** — node
calls per block in §4.2, node calls per module and the optimiser's path in
§4.3 — each rendered between a :data:`MAIN_START` / :data:`MAIN_END` marker
pair carrying the layout's name, and numbered ``Table n`` after §3's
:data:`MAIN_TABLES_BEFORE` hand-written ones.  Everything else is **Appendix
D — Results tables**, rendered between :data:`SECTION_START` (the appendix
heading) and :data:`SECTION_END` (an explicit end marker), so ``--plan-tables
write | check`` guards exactly the rendered blocks and nothing a person
wrote.

**One construction, one table** (the user, 2026-09-15: *"[the tables] seem
expanded over a bunch of different tables with one row, which makes no sense
at all"*).  The tally emits a table per *(configuration, source)*, which put
82 tables for 17 constructions into Appendix D, 21 of them with a single row,
and 162 into the companion file with every table twice.  A declared
:class:`Layout` per construction now says how those tables become **one**:
stacked with the configurations and regimes as row groups, or merged on a
join column where one construction's one-row table is a fact about another's
rows (the seed set into per-arm success; the entry reference's three
constructions into one).  This is a **rendering** change: the tally's
emission, the stage records and the gates over cells (``recomputation``,
``tally_contracts``) are untouched, and every cell of a combined grid is a
cell one stage table already held, rendered by that table's own columns.

Appendix D holds **summarising tables only** — per arm or arm pair and
configuration — each numbered ``Table D.n`` in emission order and carrying
**one caption of a few lines**.  Every construction's full declaration
(units, row, column, construction, clauses, how to read) is printed **once
per construction** in D.0.  A table whose rows are runs, seeds, pairs of runs
or predicate evaluations — a full result matrix — is rendered into the
**companion file** :data:`COMPANION_NAME` beside the report, numbered ``Table
F.n``, together with the full versions of tables whose per-seed columns the
report omits; the companion is generated whole and guarded by the same
``check``.  The second implementation's tables (:data:`UNRENDERED_STAGE`) are
**not rendered anywhere**: gate ``recomputation``'s row of D.1 — tables
compared, cells compared, cells mismatched — is that check, and the gate's
record holds the cells.

What is rendered, and from which stage's record:

=========================  ==================================================
``gate_table``             D.1, one row per registered gate
``tally_evaluation``       §4's Table 7; D.2 (the evaluation phase); → F
``tally_optimisation``     §4's Tables 8 and 9; D.3 (the optimisation phase); → F
``recomputed_tables``      nothing: gate ``recomputation``'s row of D.1 is it
=========================  ==================================================

**What the cells are over, said once.** The tally stages are over **one
population**, the one the tally publishes (``tally.published_sources``): the
**campaign population** — the campaign plan's own records under
``runs/campaign/``, twenty-five seeds per arm — once a campaign record exists,
and the **gate population** — the runs the verification gates made, one or two
seeds per arm — while none does.  A median over one run and a median over
twenty-five are different quantities with the same name (trap T11), so the
appendix's opening names the population and the commit its records were made
at, and every caption states its own denominator.  D.1 is the gates' own table
and stays over each gate's own population: gates are gates.

**D.1 is rendered from the ``gate_table`` stage record, not from the verdicts
themselves**, so a gate re-run after that stage would be reproduced here as it
was, not as it is.  The renderer therefore refuses a stage record whose own
account of the verdicts it read disagrees with the verdicts on disk, naming the
gate, both commits and both times (issue I-22 (a); the mechanism is the
framework's ``assert_records_read_are_current``).

**Table numbers are positional.** ``Table D.n`` and ``Table F.n`` are assigned
in emission order and change when a table is added or removed; the hand-written
text cites them, so ``check`` also resolves every ``Table D.n`` / ``Table F.n``
reference in the report against the numbers this rendering assigns and reports
any that point past the end.  Cells are keyed by the table's *construction
name* (``table``) everywhere a number must be traced, never by its number.

Written by task **A55 (harness-smoke)**; the freshness refusal and the
comparison mode by task **A63 (stage-provenance)**; the appendix, the companion
file, the numbering and the caption rule by task **A79 (report-captions)**;
the layouts, the main-text headline tables and the withdrawal of the
recomputed copies by task **A83 (headline-tables-in-text)**; the previous
revision's cell forms (``merges``, ``select``, ``blocks``, ``bold``,
``blank_repeats``) by task **A85 (v3-table-formats)** and (``omit``,
``fraction``, the reduced block heading line) by task **A86
(v3-tables-remainder)**.

**Task A87 (v3-grid-polish)** finished the grids: a ratio pair and its verdict
in **one** cell (``Merged`` join ``"verdict"``, ``0.76, 5.64 → PASS``); a
**reduced sub-heading row** — the group's configuration, its regime where a
table holds more than one, and its own n, with what that n counts moved into
the caption and the tally's table name left to the construction line under the
grid; a declared ``column_order``; and two layouts that **share** their stage
tables by naming each other (``shares_tables_with``), so per-arm success is the
main text's grid in the previous revision's §5.1 form *and* a constituent of
the appendix's merged reliability table.  A cell may appear in more than one
table; it may never be lost or changed.
"""

from __future__ import annotations

import datetime as _dt
import difflib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from ..core import framework
from ..core.config import EXECUTION_APPROVED, Campaign

__all__ = [
    "PlanTablesError",
    "render",
    "check",
    "write",
    "SECTIONS",
    "GROUPS",
    "LAYOUTS",
    "Layout",
    "SECTION_START",
    "SECTION_END",
    "MAIN_START",
    "MAIN_END",
    "MAIN_TABLES_BEFORE",
    "COMPANION_NAME",
    "UNRENDERED_STAGE",
]


class PlanTablesError(RuntimeError):
    """A refusal to render.  Never a section with a hole in it."""


#: Where the rendered block starts and stops in the report.  Both are matched
#: on the whole line, so a heading that has been reworded is a refusal rather
#: than a silent rewrite of the wrong part of the document.  The end marker is
#: explicit because Appendix D is the document's last section.
SECTION_START = "## Appendix D — Results tables"
SECTION_END = "<!-- plan_tables: end of the rendered results tables -->"

#: The companion file beside the report: every full result matrix, generated
#: whole by :func:`write` and compared whole by :func:`check`.
COMPANION_NAME = "RESULTS_TABLES_FULL.md"

#: The two documents' table-number prefixes.
REPORT_PREFIX = "D"
COMPANION_PREFIX = "F"


@dataclass(frozen=True)
class Section:
    """One stage record the appendix is rendered from, and its heading."""

    number: str
    heading: str
    stage: str
    what: str
    #: Whether this stage's record must say **which records it read**, and be
    #: refused when they have moved since.  True where the stage summarises
    #: other records rather than runs: D.1 is one row per gate *verdict*, and
    #: a gate re-run after the stage leaves this section reproducing the older
    #: verdict byte for byte with nothing to mark it — which is what happened
    #: (issue I-22 (a)).  A stage over **run** records is not checked here: its
    #: provenance is ``runs_provenance``, which the analysis compares against
    #: its own survey of the same runs.
    records_read_required: bool = False


SECTIONS: tuple[Section, ...] = (
    Section(
        number="D.1",
        heading="Gates",
        stage="gate_table",
        records_read_required=True,
        what=(
            "one row per registered gate, read from the verdict records: what "
            "it binds, its population, its denominator, its mismatches and its "
            "teeth"
        ),
    ),
    Section(
        number="D.3",
        heading="The evaluation phase",
        stage="tally_evaluation",
        what=(
            "cost per call, matched accuracy on both rulers, the fixed-point "
            "distance between arms (reported, not accepted on), the ownership "
            "rung, the failure taxonomy and the per-block headline table; the "
            "per-run tables and the predicate trial go to the companion file"
        ),
    ),
    Section(
        number="D.4",
        heading="The optimisation phase",
        stage="tally_optimisation",
        what=(
            "the seed set, the same-optimum check, both iteration "
            "constructions, the cost with and without the retried seeds, the "
            "achieved accuracy, the lift's residual, the failure taxonomy and "
            "the two headline tables; the failure table, the attempt-summation "
            "identity and the per-run overhead go to the companion file"
        ),
    ),
    Section(
        number="F",
        heading="The same cells, computed a second time",
        stage="recomputed_tables",
        what=(
            "every cell of the tally's tables recomputed by an implementation "
            "that shares no construction with the tally; the verdict on "
            "whether the two agree is gate `recomputation`'s, in D.1"
        ),
    ),
)

#: The tally stages whose tables carry a ``kind`` and are grouped by it.
TALLY_STAGES: tuple[str, ...] = ("tally_evaluation", "tally_optimisation")


@dataclass(frozen=True)
class Merged:
    """**Several of a constituent's columns as one cell**, the V3 report's form.

    The previous revision's tables put a mean and its seed bracket in *one*
    cell — ``1978 [1758, 2280]`` — and a median and its p90 in one —
    ``5.04e-10 / 2.96e-9``.  The user asked for those forms back on
    2026-09-15 (*"How I want them formatted is based on v3 report section 4
    and 5"*), and a sixteen-column grid of alternating ``mean`` /
    ``[min, max]`` columns is what made that necessary.

    This is a **rendering** declaration and no cell is lost: the merged cell
    is the constituents' own rendered cells joined, and
    ``report_cells_preserved.py`` reads the same declaration to prove that
    every part is still present, in the same row, with the same value.

    ``join``:

    ``"bracket"``
        ``mean [min, max]``, and — the previous revision's own rule — the
        **bare value** where the bracket is degenerate and equals the mean,
        so a column every run agreed on reads ``4`` and not ``4 [4, 4]``.
    ``"slash"``
        ``median / p90``: two order statistics of one distribution.  Two
        missing values read ``— / —`` and are **not** collapsed to one dash:
        the same-optimum table's yardstick rows already print that pair, and
        a rendering change may move a cell, never rewrite one (task A86
        (v3-tables-remainder)).

    ``"fraction"``
        ``k/n``: a count and the denominator it is out of, which the previous
        revision printed in **one** cell (``0/22``) and this rendering had as
        two columns.  An empty or absent denominator leaves the count alone,
        so a row that carries no pair count still prints its count.

    ``"verdict"``
        ``med, p90 -> **PASS**``: a ratio at two quantiles and the verdict it
        was read against, which the previous revision printed in **one** cell
        (``0.76, 5.64 -> PASS``, its §4 check-1 grid) and this rendering had
        as three columns.  The verdict is emboldened by the join, because the
        previous revision bolded the word and not the ratios; a verdict
        already bold — which is what an earlier rendering of the same cell
        printed — is left as it is, so the join is the same on a stage
        record's raw cell and on a published one.  A triple whose parts are
        all missing reads ``—``: nothing was ever published for that pair, as
        against the ``— / —`` of a pair that exists and has no value (task
        A86 (v3-tables-remainder)'s deviation xi).
    """

    #: The merged column's key and heading.
    key: str
    heading: str
    #: The constituent column keys it consumes, in order.
    parts: tuple[str, ...]
    join: str = "bracket"


def _merge_cells(parts: Sequence[str], join: str) -> str:
    """Two rendered cells as one, under :class:`Merged`'s join."""
    values = [str(p).strip() for p in parts]
    if join == "bracket":
        head, bracket = (values + ["", ""])[:2]
        if not head and not bracket:
            return ""
        if head in ("", "—") and bracket in ("", "—"):
            return head or bracket or ""
        if bracket in ("", "—"):
            return head
        ends = [e.strip() for e in bracket.strip("[]").split(",")]
        if len(ends) == 2 and ends[0] == ends[1]:
            try:
                same = float(head) == float(ends[0])
            except ValueError:
                same = False
            if same:
                return ends[0]
        return f"{head} {bracket}"
    if join == "slash":
        if not any(values):
            # every part empty: a group heading row, not a missing value.
            return ""
        return " / ".join(values)
    if join == "fraction":
        count, denominator = (values + ["", ""])[:2]
        if not count and not denominator:
            return ""
        if denominator in ("", "—"):
            return count
        return f"{count}/{denominator}"
    if join == "verdict":
        head, tail, verdict = (values + ["", "", ""])[:3]
        if not any(values):
            # every part empty: a group heading row, not a missing value.
            return ""
        if not any(v not in ("", "—") for v in (head, tail, verdict)):
            # the pair does not exist on this row — the previous revision
            # left such a cell blank and this rendering prints one dash.
            return "—"
        if verdict and verdict != "—" and not verdict.startswith("**"):
            verdict = f"**{verdict}**"
        return f"{head or '—'}, {tail or '—'} → {verdict or '—'}"
    raise PlanTablesError(
        f"no cell join {join!r}: it is 'bracket', 'slash', 'fraction' or "
        f"'verdict'"
    )


#: The arm set a table states in its caption where the grid does not carry
#: an *arms* column — the previous revision's grids never did, and the four
#: one-quantity tables of the optimiser's path drop theirs into the caption
#: (``Layout.omit``, task A86 (v3-tables-remainder)).
ARM_SET = (
    " The arms are `BR`, `B0`, `B1` and `B2`; `B1` is inactive on "
    "`st_regression` and its column reads — there."
)

#: Each phase's whole ladder, by the stage that emits it.  A block heading
#: line names its arm set only where the block does not carry all of it —
#: the previous revision's `st` block, whose heading said *"no B1"* (task
#: A86 (v3-tables-remainder)).
LADDERS: dict[str, tuple[str, ...]] = {
    "tally_evaluation": ("AR", "A0", "A1", "A2"),
    "tally_optimisation": ("BR", "B0", "B1", "B2"),
}

#: How a configuration is written in a block heading line and in a row group
#: label: the report's own short names (§4), not the previous revision's.
SHORT_NAMES: dict[str, str] = {
    "large_tokamak_nof": "nof",
    "low_aspect_ratio_DEMO": "lad",
    "st_regression": "st",
}


@dataclass(frozen=True)
class Layout:
    """**How one construction becomes one table.**

    The tally emits a table per *(configuration, source)* because that is how
    it computes them: ``cost per call — large_tokamak_nof —
    campaign_displaced`` is one of twelve.  Rendering them one per grid put
    **82 tables for 17 constructions** into Appendix D, twenty-one of them
    with a single row, and a reader met the same grid nine or twelve times
    with a different name over it (the user, 2026-09-15: *"these seem expanded
    over a bunch of different tables with one row, which makes no sense at
    all"*).

    A layout is the declaration that fixes that: **one construction, one
    table**.  It names the tables it takes, where the combined table goes, and
    how the constituents are laid out inside it.  It is *data* — the tally's
    emission, the stage records and the gates over cells (``recomputation``,
    ``tally_contracts``) are untouched, and every cell of the combined grid is
    a cell one constituent's record already carried, copied as that
    constituent's own columns rendered it.

    ``mode``:

    ``"single"``
        One constituent, rendered as it is today (its own caption, its own
        grid).  For a construction the tally already emits whole — the
        optimiser's path over the configurations, the predicate trial.

    ``"stack"``
        The constituents one after another in one grid, each under a **bold
        sub-heading row** naming its configuration, its source and its own
        ``n``.  Columns are the union of the constituents' columns, keyed by
        column key; a cell of a column the constituent does not have is
        empty (as against ``—``, which is a constituent's own missing value).
        This is where the *source regime* becomes a row key: it is one where
        the construction's statistic is too wide to make a column group of
        without dropping columns.

    ``"merge"``
        The constituents of one configuration **aligned on one column**
        (``join``) into single rows: the seed set and the optimisation
        phase's failure taxonomy become columns of per-arm success, the
        entry reference's three constructions become one row per arm and
        ruler.  A constituent with no ``join`` column, or with one row where
        the group has several, is broadcast across the group's rows — which
        is what "stated once per configuration" means in a table whose rows
        are arms.

    ``where`` is ``"main"`` (the report's §4, between this module's markers,
    numbered ``Table n`` after §3's six), ``"report"`` (Appendix D,
    ``Table D.n``) or ``"companion"`` (``RESULTS_TABLES_FULL.md``,
    ``Table F.n``).  A combined report table whose constituents omit per-seed
    columns is rendered a second time in the companion with every column, as
    before.

    ``headings`` is consulted **only** where the constituents disagree on a
    column's heading — ``vs A0 pooled`` against ``vs A1 pooled``, ``paired at
    seeds`` against ``paired at columns``.  Disagreement with no declared
    heading is a refusal: a combined column labelled with one constituent's
    heading would say the wrong thing about the others.
    """

    #: The layout's own name — the marker name for a main-text table, and the
    #: key the census and the cell-preservation check report by.
    name: str
    #: The construction name printed under the grid.
    title: str
    stage: str
    #: The kinds it takes.  More than one only where a construction absorbs
    #: another (per-arm success; the reference entries).
    kinds: tuple[str, ...]
    where: str
    mode: str
    #: The few lines the combined table's caption prints.  Hand-written, like
    #: the group context paragraphs, and true of the construction as a whole;
    #: what varies by constituent is in the sub-heading rows.
    caption: str
    #: Why this layout and not another — the entry's docstring.
    why: str
    #: Source families it takes; empty means every source the kinds appear in.
    sources: tuple[str, ...] = ()
    #: ``True`` to take the kinds' **detail** tables (the companion's).
    detail: bool = False
    #: The column the constituents of one group are aligned on, in ``merge``.
    join: str | None = None
    #: Column key → heading, where the constituents disagree.
    headings: tuple[tuple[str, str], ...] = ()
    # ---------------- the V3 forms (task A85 (v3-table-formats)) -----------
    #: Cells the V3 report put in one cell and this rendering does too.
    merges: tuple[Merged, ...] = ()
    #: ``(column key, accepted cell values)``: the rows this table keeps.  A
    #: construction the previous revision published as **several tables of
    #: one shape** — the iteration multiplier, the evaluation count and the
    #: node-call rate are three tables, each one quantity — is one tally
    #: table here, and each layout takes its own rows.  Two layouts may claim
    #: one stage table only when each declares a selection, and the
    #: selections must not overlap: a row rendered twice is a cell published
    #: twice under two numbers.
    select: tuple[tuple[str, tuple[str, ...]], ...] = ()
    #: Columns printed in bold: the result column and the verdict, as the
    #: previous revision printed them.
    bold: tuple[str, ...] = ()
    #: ``True`` to print one **grid per constituent** under a bold heading
    #: line (``**`nof`** (n = 22)``) instead of one grid with sub-heading
    #: rows — the previous revision's per-module form, which the user's three
    #: images are.
    blocks: bool = False
    #: Columns whose repeated consecutive value is blanked, so a
    #: cross-configuration table names its configuration once and leaves the
    #: continuation rows empty, as the previous revision's §4.4, §5.1, §5.2
    #: and §5.5 tables did.
    blank_repeats: tuple[str, ...] = ()
    #: **Columns this rendering drops into the caption** — a column whose cell
    #: is the same label on every row the grid keeps, which the previous
    #: revision's grid did not have because the label was its caption's
    #: (the quantity of a one-quantity table, the arm set of a block).  A
    #: rendering declaration like ``merges``: the cells are not changed, they
    #: are stated once above the grid instead of once per row, and
    #: ``report_cells_preserved.py`` reads the same declaration so the check
    #: still proves every remaining cell present.  A column named here that
    #: the tables do not have is a refusal; **the caption must carry what the
    #: column carried**, which is the entry's own job to write (task A86
    #: (v3-tables-remainder)).
    omit: tuple[str, ...] = ()
    #: **The order this grid's columns print in**, by column key; the
    #: columns not named keep the order the constituents gave them, after the
    #: named ones.  A combined grid's columns are otherwise the order the
    #: constituents happen to carry them in, which is the order the *first*
    #: configuration to exhibit an outcome class put it in — so a class only
    #: `low_aspect_ratio_DEMO` has lands after a column that belongs to the
    #: right of every class.  A key named here that the tables do not have is
    #: a refusal (task A87 (v3-grid-polish)).
    column_order: tuple[str, ...] = ()
    #: **The other layouts this one deliberately shares its stage tables
    #: with**, by name, each of which must name this one back.  Normally a
    #: stage table is rendered by exactly one layout, and two claims are a
    #: declaration that has fallen behind the tally; the exception is a
    #: construction the report prints twice on purpose — per-arm success is
    #: the main text's grid in the previous revision's §5.1 form *and* a
    #: constituent of the appendix's merged reliability table.  **A cell may
    #: appear in more than one table; it may never be lost or changed**, and
    #: ``report_cells_preserved.py`` looks for an old row in every grid that
    #: names its stage table, so a shared table is found in either (task A87
    #: (v3-grid-polish)).
    shares_tables_with: tuple[str, ...] = ()
    #: The layout whose companion **full version** already prints this one's
    #: per-seed columns.  A table that leaves a per-seed column out is
    #: rendered again in the companion with every column; where two layouts
    #: are built from the same stage tables, the second would be a strict
    #: copy of the first's full version, so it names that one instead and its
    #: caption points the reader at that table (task A87 (v3-grid-polish)).
    per_seed_columns_in: str = ""


#: The source families, in the order their tables print, with the label the
#: sub-heading rows use.  A source in a record carries the arm set after a
#: ``·`` (``campaign_optimisation · BR·B0·B1·B2``); the family is the part
#: before it.
SOURCE_ORDER: tuple[str, ...] = (
    "campaign_entry_references",
    "campaign_displaced",
    "campaign_stencil_forward",
    "campaign_stencil_backward",
    "campaign_optimisation",
    "paired_entries",
    "gate_entries",
)

_STENCILS = ("campaign_stencil_forward", "campaign_stencil_backward")
_EVALUATION_REGIMES = ("campaign_displaced", *_STENCILS)


LAYOUTS: tuple[Layout, ...] = (
    # ---------------- the main text: the previous revision's §4 and §5 shapes ----
    Layout(
        name="matched_accuracy_headline",
        title="check 1, matched accuracy",
        stage="tally_evaluation",
        kinds=("matched_accuracy_headline",),
        sources=("campaign_displaced",),
        where="main",
        mode="single",
        merges=(
            Merged(key="AR", heading="AR", parts=("AR_median", "AR_p90"), join="slash"),
            Merged(key="A0", heading="A0", parts=("A0_median", "A0_p90"), join="slash"),
            Merged(key="A1", heading="A1", parts=("A1_median", "A1_p90"), join="slash"),
            Merged(key="A2", heading="A2", parts=("A2_median", "A2_p90"), join="slash"),
            Merged(
                key="A2_over_A1",
                heading="A2/A1 med, p90 → verdict",
                parts=(
                    "A2_over_A1_median",
                    "A2_over_A1_p90",
                    "A2_over_A1_verdict",
                ),
                join="verdict",
            ),
            Merged(
                key="A2_over_A0",
                heading="A2/A0 med, p90 → verdict",
                parts=(
                    "A2_over_A0_median",
                    "A2_over_A0_p90",
                    "A2_over_A0_verdict",
                ),
                join="verdict",
            ),
        ),
        omit=("note",),
        caption=(
            "**Check 1 — matched accuracy**, the headline evaluation-phase "
            "check: the restricted audit maximum as `median / p90` per arm, "
            "one row per configuration, over that configuration's 25 "
            "displaced-entry runs per arm on the frozen ruler. The declared "
            "pair is `A2/A1` on a pulsed configuration and `A2/A0` on "
            "`st_regression` — the *reference* column names it — and the rule "
            "is within F = 10 at median **and** p90; the other pair is "
            "published beside and is not the acceptance. A ratio cell reads "
            "`med, p90 → verdict`, and `—` where the pair has no ratio to "
            "report. The dropped *verdict note* column said which pair is the "
            "declared one, which the *reference* column says, and carried one "
            "note of its own: on `low_aspect_ratio_DEMO` both quantiles of "
            "both pairs are exactly 0, so the ratios read `—` and the pair "
            "passes under the **trivially-similar clause**, not on a measured "
            "ratio. The mixed ruler's distributions are in Appendix D."
        ),
        why=(
            "**The previous revision's §4 check-1 table, reproduced** (the "
            "user's ruling of 2026-09-15).  Its grid is one row per "
            "configuration and one column per arm as `median / p90`, with "
            "the ratio pair and the verdict beside — **in one cell**, "
            "`0.76, 5.64 → PASS`, which this rendering had spread over a "
            "`med` / `p90` / `verdict` triple and a note column (task A87 "
            "(v3-grid-polish)); the stencil regimes it never had are the "
            "companion file's, in the same form."
        ),
    ),
    Layout(
        name="per_call_cost_headline",
        title="per-call cost",
        stage="tally_evaluation",
        kinds=("cost_per_call_headline",),
        sources=("campaign_displaced",),
        where="main",
        mode="single",
        merges=(
            Merged(key="AR", heading="AR", parts=("AR_mean", "AR_bracket")),
            Merged(key="A0", heading="A0", parts=("A0_mean", "A0_bracket")),
            Merged(key="A1", heading="A1", parts=("A1_mean", "A1_bracket")),
            Merged(key="A2", heading="A2", parts=("A2_mean", "A2_bracket")),
        ),
        bold=("A1_to_A2", "A0_to_A2"),
        caption=(
            "**Per-call cost**: mean model-node executions per `call_models` "
            "evaluation with the `[min, max]` seed bracket in one cell, one "
            "row per configuration over its 25 displaced-entry runs per arm, "
            "then the ladder's rungs as pooled ratios — `AR→A0` the stopping "
            "rule, `A0→A1` the ownership of the burn time, `A1→A2` the "
            "partition, with `A0→A2` standing in where the ownership rung "
            "does not exist. The partitioned arm's prime calls per evaluation "
            "are the last column and are in **no** node-call cell (D19)."
        ),
        why=(
            "**The previous revision's check-3 table, reproduced**, in the "
            "per-run form its own §4.5 rewrite moved to: it summed node "
            "calls over 25 seeds, and the sums hid both the denominator and "
            "the run-to-run spread.  One rung per column, because V4's "
            "ladder has three where the previous revision's had one."
        ),
    ),
    Layout(
        name="module_sweeps_evaluation",
        title="module sweeps per run, the evaluation phase",
        stage="tally_evaluation",
        kinds=("module_sweeps",),
        sources=("campaign_displaced",),
        where="main",
        mode="stack",
        blocks=True,
        shares_tables_with=("module_sweeps_functions_evaluation",),
        merges=(
            Merged(key="AR", heading="AR", parts=("AR_mean", "AR_bracket")),
            Merged(key="A0", heading="A0", parts=("A0_mean", "A0_bracket")),
            Merged(key="A1", heading="A1", parts=("A1_mean", "A1_bracket")),
            Merged(key="A2", heading="A2", parts=("A2_mean", "A2_bracket")),
        ),
        bold=("ratio",),
        caption=(
            "**Module sweeps per run**: how often each node group was swept "
            "in one `call_models` evaluation, one block per configuration "
            "over its own 25 displaced-entry runs, as the mean with its "
            "[min, max] seed bracket — a bare integer where every run agreed "
            "exactly. `models` is the group's collapsed-DSM row count, so "
            "total calls = Σ sweeps × models. **The ratio column is the "
            "result**, and it is unit-free: within a group every model node "
            "runs once per sweep (the construction refuses the run if they "
            "did not), so a ratio of sweeps does not depend on whether one "
            "counts model calls or DSM rows. The total does, and its ratio "
            "cell is the `[v = 1, v = 0]` interval over the two defensible "
            "attributions of the once-per-run nodes' rows (trap T9); the "
            "per-arm total cells are the v = 1 case. Reported, not accepted "
            "on."
        ),
        why=(
            "**The previous revision's §4.5 table, reproduced** — one of the "
            "three the user gave as images on 2026-09-15 (*\"How I want them "
            "formatted is based on v3 report section 4 and 5\"*).  Per-"
            "configuration **blocks** under a bold heading line rather than "
            "one grid with sub-heading rows, because that is the form of the "
            "image: three short grids of the same six rows read down, and a "
            "single grid of eighteen rows does not.  The other three regimes "
            "are the same three blocks in the companion file."
        ),
    ),
    Layout(
        name="per_arm_success",
        title="per-arm success",
        stage="tally_optimisation",
        kinds=("per_arm_success",),
        where="main",
        mode="stack",
        shares_tables_with=("reliability_and_taxonomy",),
        per_seed_columns_in="reliability_and_taxonomy",
        column_order=(
            "arm",
            "offered",
            "accepted",
            "finished, ifail = 5",
            "crashed (RuntimeError)",
            "coupling-loop cap (ModuleSolveFailure)",
            "lost_another_arm_accepted",
            "seed_set",
        ),
        blank_repeats=("seed_set",),
        caption=(
            "**Reliability per arm**, the configurations stacked: of the 25 "
            "starts offered to each arm, the **accepted optima** (status ok "
            "and the output file's `ifail == 1`), then every other start by "
            "its outcome class — finished with the optimiser's own exit code "
            "`ifail = 5` after its four attempts; crashed inside PROCESS "
            "(`RuntimeError`); refused by the coupling-state loop's 20-sweep "
            "cap (`ModuleSolveFailure`) — and last the starts **lost**, which "
            "this arm did not accept and another did. A class column is empty "
            "where the configuration has no start of that class. The **seed "
            "set** is the last column, stated once at the head of each "
            "configuration's arm rows and blank below it: the seeds on which "
            "*every* arm reached an accepted optimum, which is the n of every "
            "other optimisation table. The seeds behind each class, the "
            "configuration-invalid seeds, the retried seeds and the failure "
            "taxonomy's tracebacks are the merged table in Appendix D, and "
            "per seed in the companion file. Reported, not accepted on (D29, "
            "2026-09-15)."
        ),
        why=(
            "**The previous revision's §5.1 grid, reproduced** — "
            "`config | invalid seeds | arm | ok | converged | not-converged` "
            "— with V4's finer outcome classes in place of its two (task A87 "
            "(v3-grid-polish)).  The main text carries this construction "
            "alone: merged with the failure taxonomy and the seed set it is "
            "twenty-three columns, three of them one label repeated down a "
            "configuration's rows, which is a bookkeeping table and not a "
            "grid a paragraph reads.  The merged table keeps every one of "
            "those cells, in Appendix D; a cell may appear in more than one "
            "table, it may never be lost."
        ),
    ),
    Layout(
        name="same_optimum",
        title="same optimum (check 1)",
        stage="tally_optimisation",
        kinds=("same_optimum",),
        where="main",
        mode="stack",
        merges=(
            Merged(
                key="r_median",
                heading="relative Δ objf, median / p90",
                parts=("r_median", "r_p90"),
                join="slash",
            ),
            Merged(
                key="threshold_median",
                heading="threshold median / p90",
                parts=("threshold_median", "threshold_p90"),
                join="slash",
            ),
        ),
        bold=("verdict",),
        caption=(
            "Check 1 by configuration and arm pair: the paired relative "
            "objective difference at median and p90 against the pair's own "
            "threshold, with the verdict, the count of seeds whose optima sit "
            "in different objective clusters (*hops*) and the count below "
            "cluster resolution. The yardstick pair `BR → B0` is published "
            "beside and never accepted on."
        ),
        why="Three tables of two or three rows, one per configuration.",
    ),
    Layout(
        name="iteration_multiplier_headline",
        title="the iteration multiplier",
        stage="tally_optimisation",
        kinds=("optimiser_path",),
        where="main",
        mode="single",
        select=(("quantity", ("iterations (summed over attempts)",)),),
        merges=(
            Merged(
                key="ratio_median",
                heading="B2/B0 median [min, max]",
                parts=("ratio_median", "ratio_bracket"),
            ),
        ),
        bold=("ratio_median",),
        omit=("quantity", "arms"),
        caption=(
            "**Optimiser iterations per run**, summed over the optimiser's retry attempts, one row per configuration over its own seed set: the mean per arm, then `B2` against `B0` as the ratio of those means — equal to the ratio of the sums over the same seeds, the campaign-cost statistic — as the mean of the per-seed ratios, as their median with the observed [min, max] seed bracket (the check-2 acceptance quantity, bound ≤ 1.05) and as the count of seeds on which `B2` took strictly more iterations." + ARM_SET
        ),
        why=(
            "The previous revision's §5.3 table, reproduced (task A85 (v3-table-formats), the user's ruling of 2026-09-15).  Its shape holds **one quantity per table**, so the optimiser's path — which the tally emits as four quantities stacked — is rendered as four tables of that shape, each taking its own rows by a declared selection.  This is the first, and it is the one check 2 is read from."
        ),
    ),
    Layout(
        name="evaluation_count",
        title="the evaluation count ε",
        stage="tally_optimisation",
        kinds=("optimiser_path",),
        where="main",
        mode="single",
        select=(("quantity", ("evaluations of the model set, ε",)),),
        merges=(
            Merged(
                key="ratio_median",
                heading="B2/B0 median [min, max]",
                parts=("ratio_median", "ratio_bracket"),
            ),
        ),
        bold=("ratio_median",),
        omit=("quantity", "arms"),
        caption=(
            "**Evaluations of the model set per run**, ε (`sweeps_per_eval.n_evaluations`, the field issue I-26 named as the correct one), one row per configuration over its own seed set: the mean per arm, then `B2` against `B0` read the same four ways — the ratio of the means, the mean of the per-seed ratios, their median with the bracket, and the count above 1. This is the ε of R = ρ × ε and it is a count of optimiser probes, not a cost." + ARM_SET
        ),
        why=(
            "The same shape as the iteration multiplier, one quantity over: the previous revision's §5.3 form holds one quantity per table, and ε and ρ were rows of task A79's Table 9.  Selected from the same stage table."
        ),
    ),
    Layout(
        name="node_calls_per_evaluation",
        title="node calls per evaluation ρ",
        stage="tally_optimisation",
        kinds=("optimiser_path",),
        where="main",
        mode="single",
        select=(("quantity", ("node calls per evaluation, ρ",)),),
        merges=(
            Merged(
                key="ratio_median",
                heading="B2/B0 median [min, max]",
                parts=("ratio_median", "ratio_bracket"),
            ),
        ),
        bold=("ratio_median",),
        omit=("quantity", "arms"),
        caption=(
            "**Model-node executions per evaluation of the model set**, ρ, one row per configuration over its own seed set: the mean per arm, then `B2` against `B0` read the same four ways. This is the ρ of R = ρ × ε — the per-call term the partition acts on, and the stable one." + ARM_SET
        ),
        why=(
            "The third quantity of the optimiser's path, in the previous revision's one-quantity-per-table shape."
        ),
    ),
    Layout(
        name="node_calls_per_run",
        title="node calls per run R",
        stage="tally_optimisation",
        kinds=("optimiser_path",),
        where="main",
        mode="single",
        select=(("quantity", ("node calls per run, R = ρ × ε",)),),
        merges=(
            Merged(
                key="ratio_median",
                heading="B2/B0 median [min, max]",
                parts=("ratio_median", "ratio_bracket"),
            ),
        ),
        bold=("ratio_median",),
        omit=("quantity", "arms"),
        caption=(
            "**Model-node executions per run**, R, one row per configuration over its own seed set: the mean per arm, then `B2` against `B0` read the same four ways. R = ρ × ε per seed, so this table reproduces check 4's cost ratio by another road; check 4's own table sums the solve phase over the set instead." + ARM_SET
        ),
        why=(
            "The fourth quantity of the optimiser's path, in the previous revision's one-quantity-per-table shape; read against check 4's cost table, which sums the solve phase alone."
        ),
    ),
    Layout(
        name="cost_sums",
        title="cost as sums (check 4)",
        stage="tally_optimisation",
        kinds=("cost_sums",),
        where="main",
        mode="single",
        bold=("ratio",),
        blank_repeats=("configuration",),
        caption=(
            "**Check 4 — the cost**: solve-phase model-node executions "
            "**summed** over each configuration's seed set, one column per "
            "arm, with the partitioned arm's ratio to the flat control. Two "
            "sets per configuration: the seeds on which every arm reached an "
            "accepted optimum, and the same set less the seeds on which any "
            "arm retried. Sums, so the claim is about total work over the "
            "set and not about every run — the per-run reading is Table 17's "
            "last columns. Prime calls are not model nodes and are in no "
            "column here (D19)."
        ),
        why=(
            "**The previous revision's §5.5 table, reproduced**: rows "
            "configuration × set, arms as columns, summed solve-phase node "
            "calls.  The per-arm cost table (Appendix D) has the same "
            "quantity with the arms as *rows* and a per-run mean in the cell; "
            "this is the campaign-cost reading, which is what a deployment "
            "question asks and what the report's headline ratio is."
        ),
    ),
    Layout(
        name="module_sweeps_optimisation",
        title="module sweeps per run, the optimisation phase",
        stage="tally_optimisation",
        kinds=("module_sweeps",),
        where="main",
        mode="stack",
        blocks=True,
        shares_tables_with=("module_sweeps_functions_optimisation",),
        merges=(
            Merged(key="BR", heading="BR", parts=("BR_mean", "BR_bracket")),
            Merged(key="B0", heading="B0", parts=("B0_mean", "B0_bracket")),
            Merged(key="B1", heading="B1", parts=("B1_mean", "B1_bracket")),
            Merged(key="B2", heading="B2", parts=("B2_mean", "B2_bracket")),
            Merged(
                key="median",
                heading="B2/B0 per-run median [min, max]",
                parts=("median", "bracket"),
            ),
            Merged(
                key="n_above_one",
                heading="runs B2 > B0",
                parts=("n_above_one", "n_pairs"),
                join="fraction",
            ),
        ),
        bold=("pooled",),
        caption=(
            "**Module sweeps per run**: how often each node group was swept "
            "in one whole optimisation, one block per configuration over its "
            "own seed set, as the mean with its [min, max] seed bracket. "
            "`models` is the group's collapsed-DSM row count, so total calls "
            "= Σ sweeps × models, bracketed `[v = 1, v = 0]` over the "
            "once-per-run nodes' unknown rows (trap T9). **The per-module "
            "ratio column is the result** and is unit-free; the last two "
            "columns give that ratio's per-run distribution, which the pooled "
            "figure does not show. " "These are whole-run census counts: they include the output path — two MDA_Output sweeps of every node in `BR` and `B0`, none in `B1`, one execution of each once-per-run node in `B2` — and the exit audit's one sweep of every node in every arm, which is the harness's accuracy instrument and no arm's architecture. Neither cancels from a ratio: the audit's sweep moves a ratio by under 0.2 % in every row but the once-per-run one, where it is half of `B2`'s count, and the output path differs by arm; check 4's cost table sums the solve phase alone. " "`B1` is inactive on `st_regression`. Reported, not accepted on."
        ),
        why=(
            "**The previous revision's §5.5.1 table, reproduced** — the "
            "second of the user's three images.  Blocks for the same reason "
            "as the evaluation phase's, and beside it so the two phases' "
            "per-module results are read in one shape."
        ),
    ),
    # ---------------- Appendix D: the evaluation phase ---------------------
    # ---------------- Appendix D: the evaluation phase ---------------------
    Layout(
        name="module_scope",
        title="module scope",
        stage="tally_evaluation",
        kinds=("module_scope",),
        where="report",
        mode="single",
        caption=(
            "What the partition **is** on each configuration: each node "
            "group's collapsed-DSM row count and whether the committed map "
            "places it inside the iterated loop, then how many of its model "
            "nodes execute on each configuration and which. Static — derived "
            "from the committed node map and each configuration's per-run "
            "artifact, with no cell read from a run's statistics. The "
            "once-per-run group is the configuration's deferred nodes "
            "whatever module the map assigns them, which is why it carries no "
            "row count of its own (trap T9)."
        ),
        why=(
            "**The previous revision's §4.5 module-scope table, reproduced.** "
            "It is the table every per-module grid is read against: `models` "
            "in those grids is this table's *DSM rows* column, and the "
            "executing-node columns are what a sweep of that group actually "
            "runs."
        ),
    ),
    Layout(
        name="node_calls_per_block",
        title="node calls per block",
        stage="tally_evaluation",
        kinds=("node_calls_per_block",),
        sources=("campaign_entry_references", *_EVALUATION_REGIMES),
        where="report",
        mode="stack",
        bold=("ratio",),
        blank_repeats=("configuration",),
        caption=(
            "Mean node calls per evaluation by block and arm, configurations "
            "stacked, in all four evaluation-phase regimes as row groups: the "
            "entry reference, the **displaced entries** (δ = 0.10, the "
            "acceptance regime), and the forward and backward stencil "
            "points. The ratio is `A2` pooled against the configuration's "
            "declared reference (the *reference* column: `A1` on a pulsed "
            "configuration, `A0` on `st_regression`); the configuration is "
            "named once per group and blank on its continuation rows. The "
            "once-per-run row is the deferred nodes; prime calls are not "
            "model nodes and are in no row. The entry reference carries one "
            "`A0` run per configuration and so no pair and no ratio. The "
            "displaced regime's per-block ratios are the per-module ratios "
            "of the main text's module sweeps table, cell for cell, and its "
            "TOTAL row's ratio is the per-call cost table's partitioning rung."
        ),
        why=(
            "**One construction, one table** (harness plan amendment 29).  "
            "Until task A88 (function-weighted-sweeps) the displaced regime "
            "was the main text's Table 9 and the other three regimes were "
            "this table; the user asked (2026-09-17) for the per-node tables "
            "to leave the main text — the per-module sweep tables carry the "
            "same ratios in a unit-free form — so the reason for two tables "
            "went with it and the construction is rendered whole, the "
            "acceptance regime as one row group among four.  Stacked by "
            "source rather than folded into ratio columns per regime: a "
            "ratio-column rendering would have dropped the four per-arm mean "
            "columns and the pair count for those regimes out of the report "
            "altogether, which is a loss of cells, not a change of layout."
        ),
    ),
    Layout(
        name="reference_entries",
        title="the reference entries",
        stage="tally_evaluation",
        kinds=("cost_per_call", "matched_accuracy", "failure_taxonomy"),
        sources=("campaign_entry_references",),
        where="report",
        mode="merge",
        join="arm",
        caption=(
            "The entry reference, one row per configuration and ruler: what "
            "one flat `A0` evaluation from the input file's own design point "
            "cost, what it left at exit on both rulers, and whether it "
            "finished. This is the once-per-run cold-start term of plan "
            "§3.4, reported beside the displaced and stencil regimes and "
            "never pooled with them; it carries one run per configuration, so "
            "there is no pair, no ratio and no bracket. The cost and outcome "
            "cells are per configuration and repeat down its two ruler rows."
        ),
        why=(
            "Nine tables here, six of them with a single row, for three runs. "
            "The three constructions state different things about the same "
            "one run per configuration, so they are columns of one row, not "
            "three tables — the rule's *a one-row table is a row of some "
            "other table*.  Merged on the arm rather than stacked so the "
            "reader sees one line per run."
        ),
    ),
    Layout(
        name="cost_per_call",
        title="cost per call",
        stage="tally_evaluation",
        kinds=("cost_per_call",),
        sources=_EVALUATION_REGIMES,
        where="report",
        mode="stack",
        merges=(
            Merged(
                key="calls_per_eval",
                heading="node calls per evaluation [min, max]",
                parts=("calls_per_eval", "calls_bracket"),
            ),
        ),
        bold=("pooled",),
        caption=(
            "Node calls per `call_models` evaluation by arm, configuration "
            "and regime, with the ratio against the declared reference read "
            "three ways: pooled, as the per-run median, and as the count of "
            "runs on which the arm cost more. The reference is `A1` on a "
            "pulsed configuration and `A0` on `st_regression`; each "
            "sub-heading row names its regime and its own n. Prime "
            "(arrangement-method) calls stand beside the node calls and are "
            "never in them."
        ),
        why=(
            "Twelve tables of one to four rows for one construction.  The "
            "regime is a **row key** here, not a column group: three regime "
            "groups of seven columns would be a twenty-two-column grid, and "
            "the spec's fallback — a displaced table and a stencil table — "
            "would still be two tables for one construction."
        ),
        headings=(
            ("paired_seeds", "paired with the reference at"),
            ("pooled", "vs reference pooled"),
            ("median", "vs reference median"),
        ),
    ),
    Layout(
        name="matched_accuracy",
        title="matched accuracy",
        stage="tally_evaluation",
        kinds=("matched_accuracy",),
        sources=_EVALUATION_REGIMES,
        where="report",
        mode="stack",
        merges=(
            Merged(
                key="restricted_median",
                heading="restricted median / p90",
                parts=("restricted_median", "restricted_p90"),
                join="slash",
            ),
            Merged(
                key="whole_median",
                heading="whole-state median / p90",
                parts=("whole_median", "whole_p90"),
                join="slash",
            ),
        ),
        blank_repeats=("arm",),
        caption=(
            "Exit accuracy by arm, configuration and regime on both rulers: "
            "the restricted maximum scaled residual (median, p90), its argmax "
            "component, and the whole-state maximum beside it. The "
            "whole-state columns are large for `A2` by design — they hold the "
            "components the once-per-run deferred nodes write, stale at the "
            "audit — and are published so the exclusion can be seen, not "
            "judged. The audit position is a column of its own."
        ),
        why=(
            "Twelve tables of two to eight rows for one construction, "
            "identical in shape.  Stacked with the regime as a row key for "
            "the same reason as cost per call: a regime column group would "
            "drop the argmax, the whole-state pair and the exclusion count "
            "out of the report."
        ),
    ),
    Layout(
        name="full_distributions",
        title="full distributions",
        stage="tally_evaluation",
        kinds=("full_distributions",),
        sources=_EVALUATION_REGIMES,
        where="report",
        mode="stack",
        blank_repeats=("configuration",),
        caption=(
            "The full restricted-audit distributions by configuration, arm "
            "and regime: minimum, median and maximum on the frozen ruler, "
            "the components left above τ = 1e-6 summed over the arm's runs "
            "and in its worst single run, the mixed ruler's median and p90 "
            "beside, and the per-evaluation sweeps and node calls as observed "
            "ranges. The count column needs no ruler and says whether "
            "anything at all was left unconverged; compare an arm's minimum "
            "with another's maximum to see whether the two populations "
            "overlap at all."
        ),
        why=(
            "**The previous revision's §4.4 table, reproduced** — the full "
            "picture behind §4's medians, which is what it was added for.  "
            "The regime is a row key here for the same reason as in the cost "
            "and accuracy tables: a regime column group would drop the count "
            "and range columns out of the report."
        ),
    ),
    Layout(
        name="excluded_namespaces",
        title="the excluded namespaces",
        stage="tally_evaluation",
        kinds=("excluded_namespaces",),
        sources=_EVALUATION_REGIMES,
        where="report",
        mode="stack",
        bold=("restricted",),
        blank_repeats=("configuration",),
        caption=(
            "**What the exclusion set is load-bearing for**: the p90 across "
            "runs of the per-run maximum scaled residual, for the restricted "
            "set and for each namespace the restriction removes, by "
            "configuration, arm and regime, from every run's own residual "
            "vector. Had a namespace been wrongly excluded, the restricted "
            "column would read that namespace's number instead of its own — "
            "which is the size of what the headline rests on."
        ),
        why=(
            "**The previous revision's second §4.5 table, reproduced.**  Its "
            "point is that the headline's exclusion is load-bearing rather "
            "than cosmetic, and the only way to show that is to print what "
            "the excluded components hold."
        ),
    ),
    Layout(
        name="fixed_point_distance",
        title="fixed-point distance",
        stage="tally_evaluation",
        kinds=("fixed_point_distance",),
        where="report",
        mode="stack",
        merges=(
            Merged(
                key="restricted_median",
                heading="restricted median / p90",
                parts=("restricted_median", "restricted_p90"),
                join="slash",
            ),
            Merged(
                key="whole_median",
                heading="whole-state median / p90",
                parts=("whole_median", "whole_p90"),
                join="slash",
            ),
        ),
        caption=(
            "The distance between two arms' exit states on the restricted "
            "component set, by configuration, regime and pair: median, p90, "
            "worst, the worst pair's key, the argmax component, and the "
            "counts of pairs holding a component at or above τ = 1e-6 or "
            "categorically unclean. Reported, never accepted on: the "
            "acceptance quantity is the matched-accuracy table's residual."
        ),
        why=(
            "Nine tables of two or four rows.  The regime is a row key "
            "rather than a column group of median · p90 · above τ, because "
            "the column group form drops nine of the fifteen columns for the "
            "stencil regimes — the worst pair, the argmax, the unclean count "
            "and the whole-state pair — out of the report."
        ),
        headings=(
            ("n", "n (shared)"),
            ("worst_pair", "worst"),
        ),
    ),
    Layout(
        name="ownership_rung",
        title="the ownership rung A0 → A1",
        stage="tally_evaluation",
        kinds=("ownership_rung",),
        where="report",
        mode="stack",
        merges=(
            Merged(
                key="residual_s_median",
                heading="burn-time residual, s: median [min, max]",
                parts=("residual_s_median", "residual_s_bracket"),
            ),
        ),
        bold=("pooled",),
        caption=(
            "What pinning the burn time to a constant costs per call, and the "
            "inconsistency it leaves: six rows, one per pulsed configuration "
            "and regime. `st_regression` is steady-state and has no burn-time "
            "coupling, so the rung does not exist there."
        ),
        why=(
            "Six tables of one row each for one construction — the clearest "
            "case in the appendix of the rule *a one-row table is a row of "
            "some other table*; here the other table is the construction's "
            "own."
        ),
        headings=(("paired_seeds", "paired at"),),
    ),
    Layout(
        name="failure_taxonomy_evaluation",
        title="failure taxonomy, the evaluation phase",
        stage="tally_evaluation",
        kinds=("failure_taxonomy",),
        sources=_EVALUATION_REGIMES,
        where="report",
        mode="stack",
        caption=(
            "Every scheduled evaluation by arm, configuration and regime: how "
            "many were scheduled, how many finished, and each other outcome "
            "class by the last line of its traceback. The *rows sum* column "
            "is the all-or-none check that the classes account for the "
            "denominator. The entry reference's rows are in the "
            "reference-entries table."
        ),
        why=(
            "Twelve tables of one to four rows.  Stacked whole rather than "
            "reduced to a caption line: the classes are a column set the "
            "table states per arm, and a reader checking that every "
            "evaluation finished should be able to see the denominators it "
            "finished against."
        ),
    ),
    # ---------------- Appendix D: the optimisation phase --------------------
    # ---------------- Appendix D: the optimisation phase --------------------
    Layout(
        name="reliability_and_taxonomy",
        title="per-arm success, the seed set and the failure taxonomy",
        stage="tally_optimisation",
        kinds=("per_arm_success", "failure_taxonomy", "seed_set"),
        where="report",
        mode="merge",
        join="arm",
        shares_tables_with=("per_arm_success",),
        caption=(
            "Reliability read both ways, configurations stacked — **the whole "
            "of it**, of which the main text's per-arm success grid is the "
            "first seven columns. Per arm, of the 25 starts offered: accepted "
            "optima (status ok and the output file's `ifail == 1`), the other "
            "starts by outcome class, and the starts lost that another arm "
            "accepted. Beside them, the failure taxonomy over every "
            "optimisation-phase run of the configuration — scheduled, "
            "crashed, ok, the all-or-none *rows sum* check and the last line "
            "of each traceback with its count — and, per configuration and "
            "repeated down its arm rows, the **seed set**: the seeds on which "
            "*every* arm reached an accepted optimum, which every other "
            "optimisation table's n is, with the configuration-invalid seeds "
            "and the retried seeds per arm. The three constructions have "
            "three different denominators and each sub-heading row states "
            "them. Reported, not accepted on (D29, 2026-09-15)."
        ),
        why=(
            "Three constructions × three configurations = nine tables, three "
            "of them a single row, all about one question: which starts each "
            "arm accepted, and which seeds survive into every other table's "
            "denominator.  Per-arm success is the host; the failure taxonomy "
            "aligns on the arm; the seed set has no arm and is broadcast "
            "across the configuration's rows, which is what *stated once per "
            "configuration* means here.  **It is the appendix's** (task A87 "
            "(v3-grid-polish)): twenty-three columns of bookkeeping is not a "
            "grid the main text's paragraphs read, and the main text carries "
            "per-arm success alone in the previous revision's §5.1 form.  No "
            "cell is lost by the move — every one of them is here."
        ),
    ),
    Layout(
        name="problem_definition",
        title="the problem each configuration poses",
        stage="tally_optimisation",
        kinds=("problem_definition",),
        where="report",
        mode="single",
        caption=(
            "**The three configurations do not optimise the same thing.** "
            "From the runs' own stamps: the figure of merit and its name and "
            "sense (read from the frozen tree's `FiguresOfMerit`; a negative "
            "figure of merit means *maximise*), the iteration variables and "
            "the constraints as total (equality / inequality) as the unlifted "
            "arms solve them, the same after the burn-time lift, and whether "
            "the configuration is pulsed. Every cross-configuration "
            "comparison in this report is three answers to three questions, "
            "never one sample of three."
        ),
        why=(
            "**The previous revision's §5.6 table, reproduced**, with the "
            "problem *after* the lift beside the configuration's own: the "
            "lift adds an iteration variable and a constraint, which is a "
            "change of problem and not only of architecture (I-20 (b)), and "
            "the previous revision's single `vars` column could not show it."
        ),
    ),
    Layout(
        name="node_calls_per_module",
        title="node calls per module",
        stage="tally_optimisation",
        kinds=("node_calls_per_module",),
        where="report",
        mode="stack",
        merges=(
            Merged(
                key="BR",
                heading="BR",
                parts=("BR_mean", "BR_bracket"),
            ),
            Merged(
                key="B0",
                heading="B0",
                parts=("B0_mean", "B0_bracket"),
            ),
            Merged(
                key="B1",
                heading="B1",
                parts=("B1_mean", "B1_bracket"),
            ),
            Merged(
                key="B2",
                heading="B2",
                parts=("B2_mean", "B2_bracket"),
            ),
        ),
        bold=("pooled",),
        caption=(
            "Node calls per run by node group and arm, the three "
            "configurations stacked, each over its own seed set (mean, "
            "[min, max]); `B2` against `B0` pooled, as the per-run median "
            "with its bracket and as runs on which `B2` cost more. These are "
            "whole-run census counts: a group's last row is the part outside "
            "the solve phase, so the row above it less that row is check 4's "
            "solve-phase total. `B1` is inactive on `st_regression`."
        ),
        why=(
            "The per-module construction in **node-call** units, which check "
            "4's solve-phase total is read from (its last row is the part "
            "outside the solve phase).  Task **A85 (v3-table-formats)** moved "
            "it out of the main text: the previous revision's per-module "
            "headline — the one the user asked for — states module **sweeps** "
            "per run, and that table is now §4.3's.  Kept here whole, because "
            "the solve-phase decomposition is a cell set the sweeps table "
            "does not carry.  Each arm's mean and bracket are one cell, as "
            "the previous revision printed them."
        ),
    ),
    Layout(
        name="location_diagnostic",
        title="the location diagnostic",
        stage="tally_optimisation",
        kinds=("location_diagnostic",),
        where="report",
        mode="single",
        blank_repeats=("configuration",),
        caption=(
            "Where each pair of arms landed, by configuration: check 1's "
            "objective difference repeated for direct comparison, then the "
            "maximum relative difference over the **iteration variables** the "
            "two runs share by name, as median, p90 and maximum, with the "
            "variable it sat on most often and any variable one side alone "
            "carries. **A diagnostic. D6 forbids gating on it, and nothing in "
            "this report's verdicts rests on it** — some iteration variables "
            "are not identified by the problem and differ at an unchanged "
            "optimum. The yardstick pair is a change of stopping rule and "
            "nothing else."
        ),
        why=(
            "**The previous revision's §5.2.2 table, reproduced.**  It is the "
            "answer to the easiest available misreading of this campaign — "
            "that *same optimum* means *same machine* — and it is published "
            "precisely because D6 refuses to gate on it."
        ),
    ),
    Layout(
        name="identity",
        title="the identity B1 → B2",
        stage="tally_optimisation",
        kinds=("identity",),
        where="report",
        mode="single",
        bold=("objf_identical",),
        caption=(
            "**The partition at an unchanged trajectory**: over the pairs on "
            "which both `B1` and `B2` reached an accepted optimum, how many "
            "agree exactly on evaluations of the model set, on optimiser "
            "iterations summed over the attempts, and on a **bit-identical** "
            "`norm_objf` — compared as the hex float the record stamps, so "
            "identity is exact and not agreement to a printed precision. "
            "`B1` is inactive on `st_regression`, which therefore has no row."
        ),
        why=(
            "**The previous revision's identity table, one rung over.**  Its "
            "proved that removing the outer verification loop left the "
            "optimiser's path unchanged; this proves the **partition** does, "
            "which is the claim this experiment is about."
        ),
    ),
    Layout(
        name="iteration_multiplier",
        title="iteration multiplier (check 2)",
        stage="tally_optimisation",
        kinds=("iteration_multiplier",),
        where="report",
        mode="stack",
        bold=("summed_median", "acceptance"),
        caption=(
            "Check 2 by configuration and arm pair: the iteration ratio "
            "summed over the optimiser's attempts (the acceptance "
            "construction) as median and as a ratio of sums, the "
            "final-attempt construction beside it, the evaluation-count ratio "
            "ε from `sweeps_per_eval.n_evaluations` with the seeds on which "
            "it is exactly 1, and the dispatch-sweep ratio — a mechanism, not "
            "a cost."
        ),
        why=(
            "Three tables of two to four rows.  Kept as its own table rather "
            "than folded into the optimiser's path (headline shape 2): shape "
            "2's rows are quantities per configuration over four arms, this "
            "one's are arm *pairs* with verdicts and two constructions of the "
            "same ratio; the columns do not coincide."
        ),
    ),
    Layout(
        name="cost",
        title="cost (check 4)",
        stage="tally_optimisation",
        kinds=("cost",),
        where="report",
        mode="stack",
        merges=(
            Merged(
                key="node_calls_mean",
                heading="node calls per run [min, max]",
                parts=("node_calls_mean", "bracket"),
            ),
        ),
        bold=("with_pooled",),
        caption=(
            "Check 4 by configuration and arm: solve-phase model-node "
            "executions per run over the seed set with the observed bracket, "
            "the arrangement-method calls beside them, and the ratio against "
            "`B0` with and without the seeds on which either side retried. "
            "The output path and the exit audit are excluded alike in every "
            "arm."
        ),
        why="Three tables of three or four rows, one per configuration.",
    ),
    Layout(
        name="cost_anchors",
        title="cost against both anchors",
        stage="tally_optimisation",
        kinds=("cost_anchors",),
        where="report",
        mode="single",
        bold=("partition_to_reference",),
        blank_repeats=("configuration",),
        caption=(
            "The partitioned arm's cost ratio against **both** anchors, by "
            "configuration and set, from the same sums as check 4's cost "
            "table: `BR→B0` is the stopping-rule change alone, `B2/B0` "
            "isolates the architecture at a matched stopping rule and is the "
            "ladder's number, and `B2/BR` is the end-to-end change a user "
            "switching from PROCESS as shipped would see. Neither of the last "
            "two is more correct; they answer different questions, and the "
            "gap between them is exactly what the stopping rule is worth."
        ),
        why=(
            "**The previous revision's second §5.5 table, reproduced.**  "
            "*Cheaper than the predicate-matched flat baseline* and *cheaper "
            "than the code as shipped* are different claims, and a "
            "deployment question wants the second."
        ),
    ),
    Layout(
        name="sweeps_and_prime_calls",
        title="sweeps and prime calls",
        stage="tally_optimisation",
        kinds=("sweeps_and_prime_calls",),
        where="report",
        mode="single",
        blank_repeats=("configuration",),
        caption=(
            "The accounting that explains how node calls fall while dispatch "
            "sweeps rise, by configuration and arm over the seed set: summed "
            "solve-phase node calls, summed dispatch sweeps (`n_model_calls`, "
            "the field issue I-26 named as the sweep count), summed prime "
            "calls, and the two rates. `prime/sweep` is the prime's contract "
            "— one `set_fw_geometry()` per sweep — read as a check; "
            "`prime/node` is the quantity D19 excludes from every cost ratio "
            "in this report, named here so the exclusion has a size (trap "
            "T11). Both are **counts**, never costs."
        ),
        why=(
            "**The previous revision's third §5.5 table, reproduced.**  The "
            "cost tables state that node calls fall; this states what rose "
            "instead, and it is where the excluded prime calls are counted."
        ),
    ),
    Layout(
        name="achieved_accuracy",
        title="achieved accuracy at the accepted optimum",
        stage="tally_optimisation",
        kinds=("achieved_accuracy",),
        where="report",
        mode="stack",
        merges=(
            Merged(
                key="restricted_median",
                heading="restricted median / max",
                parts=("restricted_median", "restricted_max"),
                join="slash",
            ),
        ),
        blank_repeats=("arm",),
        caption=(
            "What each arm left at its accepted optimum, by configuration, "
            "arm and ruler: the restricted maximum scaled residual as median "
            "and maximum, its argmax component, and the whole-state median "
            "beside it. Matched accuracy is the condition the cost ratios are "
            "read under; this table is where it is met or not."
        ),
        why="Three tables of six or eight rows, one per configuration.",
    ),
    Layout(
        name="lift_closed",
        title="the lift closed (check 3)",
        stage="tally_optimisation",
        kinds=("lift_closed",),
        where="report",
        mode="stack",
        merges=(
            Merged(
                key="residual_s_median",
                heading="residual, s: median [min, max]",
                parts=("residual_s_median", "bracket"),
            ),
        ),
        caption=(
            "Check 3 on the two pulsed configurations: constraint 93's "
            "residual at every accepted optimum of the arms that carry the "
            "lifted design variable, absolute and relative, and whether the "
            "constraint sits in the equality block. `st_regression` has no "
            "burn-time coupling and no lift."
        ),
        why="Two tables of two rows.",
    ),
    # ---------------- Appendix D: the aggregate under three weightings ------
    Layout(
        name="module_sweeps_functions_evaluation",
        title="module sweeps per run, function-weighted, the evaluation phase",
        stage="tally_evaluation",
        kinds=("module_sweeps_functions", "module_sweeps"),
        sources=("campaign_displaced",),
        where="report",
        mode="merge",
        join="module",
        blocks=True,
        shares_tables_with=("module_sweeps_evaluation",),
        merges=(
            Merged(key="AR", heading="AR", parts=("AR_mean", "AR_bracket")),
            Merged(key="A0", heading="A0", parts=("A0_mean", "A0_bracket")),
            Merged(key="A1", heading="A1", parts=("A1_mean", "A1_bracket")),
            Merged(key="A2", heading="A2", parts=("A2_mean", "A2_bracket")),
        ),
        bold=("ratio",),
        omit=("models",),
        caption=(
            "**The main text's module sweeps table, weighted per function.** "
            "The same grid as the evaluation phase's module sweeps table — "
            "the sweep cells and the per-module ratios are that table's own, "
            "republished here, never recomputed — with `models` replaced by "
            "**`functions`**: the number of individual callables in the "
            "group, a model's callable submodels from the dependency "
            "analysis's decomposition at pin `PROCESS_at_36ac820e` (a model "
            "with no submodel counts as one function, its entry method). "
            "The counts are per configuration and differ per block where the "
            "exports do (the TF-coil model `i_tf_turn_type` selects, the "
            "electron-cyclotron model `st_regression` alone runs; M1 is 24 "
            "collapsed-DSM rows on the two pulsed configurations and 25 on "
            "`st_regression`). The total row is Σ sweeps × functions per arm "
            "and its ratio the `[v = 1, v = 0]` bracket over the once-per-run "
            "nodes' own functions, the same attribution unknown as the "
            "DSM-row total's (trap T9). **Reported, not accepted on.** For "
            "each configuration the three totals side by side are: node "
            "calls (the headline, the per-call cost table's `A1→A2` / "
            "`A0→A2`), DSM rows (the module sweeps table's total) and "
            "functions (this table's total) — the context paragraph above "
            "reads them."
        ),
        why=(
            "The user (2026-09-17): *\"add to the appendix table 10 and 18 "
            "but then with a per function weight. I want to see how this "
            "skews the headline average.\"*  The twin is a **merge** of the "
            "sweep table with a construction that carries only the new cells "
            "(rule xviii, `shares_tables_with`): a cell may appear in two "
            "tables, never be lost or changed, and the per-module cells are "
            "not computed a second time in the records.  Blocks, as the "
            "sweep table it twins.  `models` is dropped because the twin "
            "replaces it and the sweep table prints it; both columns side by "
            "side is the reversal."
        ),
    ),
    Layout(
        name="module_sweeps_functions_optimisation",
        title="module sweeps per run, function-weighted, the optimisation phase",
        stage="tally_optimisation",
        kinds=("module_sweeps_functions", "module_sweeps"),
        where="report",
        mode="merge",
        join="module",
        blocks=True,
        shares_tables_with=("module_sweeps_optimisation",),
        merges=(
            Merged(key="BR", heading="BR", parts=("BR_mean", "BR_bracket")),
            Merged(key="B0", heading="B0", parts=("B0_mean", "B0_bracket")),
            Merged(key="B1", heading="B1", parts=("B1_mean", "B1_bracket")),
            Merged(key="B2", heading="B2", parts=("B2_mean", "B2_bracket")),
            Merged(
                key="median",
                heading="B2/B0 per-run median [min, max]",
                parts=("median", "bracket"),
            ),
            Merged(
                key="n_above_one",
                heading="runs B2 > B0",
                parts=("n_above_one", "n_pairs"),
                join="fraction",
            ),
        ),
        bold=("pooled",),
        omit=("models",),
        caption=(
            "**The main text's optimisation-phase module sweeps table, "
            "weighted per function.** The same grid — the sweep cells, the "
            "per-module ratios and their per-run distributions are that "
            "table's own, republished, never recomputed — with `models` "
            "replaced by **`functions`**, the number of individual callables "
            "in the group from the dependency analysis's decomposition at pin "
            "`PROCESS_at_36ac820e` (a model with no submodel counts as one). "
            "The counts are per configuration and differ per block where the "
            "exports do. The total row is Σ sweeps × functions per arm over "
            "the whole run, its pooled ratio the `[v = 1, v = 0]` bracket over "
            "the once-per-run nodes' own functions (trap T9), and its per-run "
            "median and count above 1 are the v = 1 case. Whole-run census "
            "counts, as in the table it twins; `B1` is inactive on "
            "`st_regression`. **Reported, not accepted on.** For each "
            "configuration the three totals side by side are: node calls "
            "(the headline, check 4's `B2/B0`), DSM rows (the module sweeps "
            "table's total) and functions (this table's total) — the context "
            "paragraph above reads them."
        ),
        why=(
            "As the evaluation phase's twin, for the optimisation phase's "
            "module sweeps table; the two sit together under one context "
            "paragraph that states the aggregate under the three weightings "
            "for both phases, which is what the user asked to see."
        ),
    ),
    # ---------------- the companion file ------------------------------------
    # ---------------- the companion file ------------------------------------
    Layout(
        name="matched_accuracy_headline_other_regimes",
        title="check 1, matched accuracy, the stencil regimes",
        stage="tally_evaluation",
        kinds=("matched_accuracy_headline",),
        sources=_STENCILS,
        where="companion",
        mode="stack",
        merges=(
            Merged(key="AR", heading="AR", parts=("AR_median", "AR_p90"), join="slash"),
            Merged(key="A0", heading="A0", parts=("A0_median", "A0_p90"), join="slash"),
            Merged(key="A1", heading="A1", parts=("A1_median", "A1_p90"), join="slash"),
            Merged(key="A2", heading="A2", parts=("A2_median", "A2_p90"), join="slash"),
        ),
        bold=("A2_over_A1_verdict", "A2_over_A0_verdict"),
        caption=(
            "Check 1's grid at the two **stencil** entry points — the "
            "optimiser's own finite-difference points, one per design-vector "
            "column, paired across arms by column — in the report's form. "
            "These are not the acceptance regime: the displaced entries are, "
            "and their table is in §4.2. A stencil point is a far smaller "
            "displacement, so a ratio there is over two very small numbers "
            "and swings widely; the verdict column is printed for "
            "completeness and the regime is not one the plan accepts on."
        ),
        why=(
            "The acceptance regime's grid is the report's; these confirm it "
            "and belong beside the other per-regime detail, in the same form "
            "so the two are read the same way — as the per-module blocks are."
        ),
    ),
    Layout(
        name="per_call_cost_headline_other_regimes",
        title="per-call cost, the stencil regimes",
        stage="tally_evaluation",
        kinds=("cost_per_call_headline",),
        sources=_STENCILS,
        where="companion",
        mode="stack",
        merges=(
            Merged(key="AR", heading="AR", parts=("AR_mean", "AR_bracket")),
            Merged(key="A0", heading="A0", parts=("A0_mean", "A0_bracket")),
            Merged(key="A1", heading="A1", parts=("A1_mean", "A1_bracket")),
            Merged(key="A2", heading="A2", parts=("A2_mean", "A2_bracket")),
        ),
        bold=("A1_to_A2", "A0_to_A2"),
        caption=(
            "Per-call cost at the two **stencil** entry points, in the "
            "report's form: mean node calls per evaluation with the observed "
            "bracket, the ladder's rungs as pooled ratios, and the "
            "partitioned arm's prime calls per evaluation. Pairs are keyed by "
            "design-vector column here, not by seed."
        ),
        why=(
            "The displaced regime's grid is §4.2's; these are the same "
            "construction at the other two entry points."
        ),
    ),
    Layout(
        name="module_sweeps_other_regimes",
        title="module sweeps per run, the other three regimes",
        stage="tally_evaluation",
        kinds=("module_sweeps",),
        sources=("campaign_entry_references", *_STENCILS),
        where="companion",
        mode="stack",
        blocks=True,
        merges=(
            Merged(key="AR", heading="AR", parts=("AR_mean", "AR_bracket")),
            Merged(key="A0", heading="A0", parts=("A0_mean", "A0_bracket")),
            Merged(key="A1", heading="A1", parts=("A1_mean", "A1_bracket")),
            Merged(key="A2", heading="A2", parts=("A2_mean", "A2_bracket")),
        ),
        bold=("ratio",),
        caption=(
            "**Module sweeps per run** in the three regimes the report's "
            "table does not show — the entry reference and the forward and "
            "backward stencil points — one block per configuration and "
            "regime, in the same form: the mean with its [min, max] bracket, "
            "a bare integer where every run agreed, `models` the group's "
            "collapsed-DSM row count, the total Σ sweeps × models with its "
            "`[v = 1, v = 0]` interval. The entry reference carries one `A0` "
            "run per configuration and so no pair and no ratio."
        ),
        why=(
            "The acceptance regime's blocks are the report's; these confirm "
            "them and belong beside the other per-regime detail, in the same "
            "form so the two are read the same way."
        ),
    ),
    Layout(
        name="per_sweep_overhead_evaluation",
        title="per-sweep overhead, the evaluation phase",
        stage="tally_evaluation",
        kinds=("per_sweep_overhead",),
        where="companion",
        mode="stack",
        detail=True,
        caption=(
            "What each finished evaluation-phase run's convergence test cost, "
            "one row per run, configurations and regimes stacked: sweeps, and "
            "for the test the arm stops on its evaluations, components "
            "compared and mean width. The two predicates are never summed."
        ),
        why="Twelve per-run tables of one construction.",
    ),
    Layout(
        name="predicate_trial",
        title="the predicate trial",
        stage="tally_evaluation",
        kinds=("predicate_trial",),
        where="companion",
        mode="single",
        detail=True,
        caption="",
        why="The tally emits it whole, one row per pair of runs.",
    ),
    Layout(
        name="per_arm_success_by_seed",
        title="per-arm success by seed",
        stage="tally_optimisation",
        kinds=("per_arm_success_by_seed",),
        where="companion",
        mode="stack",
        detail=True,
        caption=(
            "Every start offered, configurations stacked: each arm's outcome "
            "class at that seed, how many arms accepted it, whether it is in "
            "the seed set, and which arms lost it where another accepted."
        ),
        why="Three per-seed tables of one construction.",
    ),
    Layout(
        name="failure_table",
        title="the failure table",
        stage="tally_optimisation",
        kinds=("failure_table",),
        where="companion",
        mode="stack",
        detail=True,
        caption=(
            "Every seed outside the seed set, configurations stacked: which "
            "arms failed there, what `ifail` and how many attempts, what the "
            "failed arm and the other arms cost at that start, and whether "
            "the seed is configuration-invalid (no arm accepted it)."
        ),
        why="Three per-seed tables of one construction.",
    ),
    Layout(
        name="attempt_summation",
        title="the attempt-summation identity",
        stage="tally_optimisation",
        kinds=("attempt_summation",),
        where="companion",
        mode="stack",
        detail=True,
        caption=(
            "The identity that licenses summing an optimisation's cost over "
            "the optimiser's attempts, one row per run, configurations "
            "stacked: the per-attempt costs, their sum, the solve-phase total "
            "and the residual between them. A run that did not finish with "
            "status ok has no solve-phase total by construction and reads NO "
            "with no residual."
        ),
        why="Three per-run tables of one construction.",
    ),
    Layout(
        name="per_sweep_overhead_optimisation",
        title="per-sweep overhead, the optimisation phase",
        stage="tally_optimisation",
        kinds=("per_sweep_overhead",),
        where="companion",
        mode="stack",
        detail=True,
        caption=(
            "What each optimisation run's convergence test cost, one row per "
            "run, configurations stacked: dispatch sweeps and the solve-phase "
            "part of them, the output-time loop's sweeps, and for the test "
            "the arm stops on its evaluations, components compared and mean "
            "width. The two predicates are never summed."
        ),
        why="Three per-run tables of one construction.",
    ),
)

#: The stage whose tables are **not rendered as tables anywhere** (the user's
#: reassessment, 2026-09-15: *"the recomputed copies are not rendered as
#: tables"*).  The second implementation's agreement with the tally is a
#: verdict, not a table set: gate ``recomputation``'s row of the gate table
#: states it — tables compared, cells compared, cells mismatched — and the
#: gate's own record holds the cells.  Rendering 107 further grids of the same
#: numbers under different column headings doubled the companion file and
#: added nothing a reader could act on.
UNRENDERED_STAGE = "recomputed_tables"

#: The report's main text carries six hand-written tables (§3's matrix, rungs,
#: choices, gates and settings, and §1.3's vocabulary), so the rendered
#: headline tables continue the sequence from here.
MAIN_TABLES_BEFORE = 6

#: The markers a main-text table is rendered between.  Both carry the
#: layout's name, so a table cannot be written into another's place, and both
#: are matched on the whole line.
MAIN_START = "<!-- plan_tables: main-text table {name} -->"
MAIN_END = "<!-- plan_tables: end of main-text table {name} -->"


@dataclass(frozen=True)
class Group:
    """One group of Appendix D: a heading, a hand-written context paragraph
    said once, and the layouts it holds, in the order they print.  A report
    layout absent from every group is a refusal, not a guess."""

    number: str
    title: str
    context: str
    layouts: tuple[str, ...]


GROUPS: tuple[Group, ...] = (
    Group(
        number="D.1",
        title="Gates",
        context=(
            "The gate table is the appendix's licence: every table below is "
            "read only if every row here is PASS with its teeth tripped. A "
            "**tooth** is a deliberate break the gate must catch, so a gate "
            "whose tooth did not trip is not accepted whatever its verdict. "
            "The row `recomputation` is the second implementation's summary "
            "— every cell of the tally's tables recomputed from the run "
            "records by code sharing no construction with the tally, "
            "compared without tolerance; its *compared* / *mismatched* pair "
            "is the whole of that check, and **is the only place the "
            "recomputed tables appear**: the copies themselves are not "
            "rendered, in this appendix or in the companion file, because a "
            "second grid of the same numbers under the record's own column "
            "keys is not something a reader can act on. The row "
            "`tally_contracts` covers the captions, denominators and record "
            "contract of every table emitted."
        ),
        layouts=(),
    ),
    Group(
        number="D.2",
        title="The evaluation phase",
        context=(
            "One `call_models` evaluation per run, no optimiser. Four "
            "sources, never pooled: the **entry reference** (one flat `A0` "
            "evaluation per configuration from the input file's own point), "
            "the **displaced entries** (δ = 0.10, seeds 1–25 — the acceptance "
            "regime), and the **forward** and **backward stencil points** "
            "(one per design-vector column, paired across arms by column). "
            "**One construction, one table**: each table below combines the "
            "tally's per-configuration and per-source tables of one "
            "construction into one grid, the configurations and regimes as "
            "row groups under a bold sub-heading row that names the group's "
            "configuration, its regime where a table holds more than one, "
            "and its own n; what that n counts is in the caption. Node calls "
            "per block is rendered whole here — the acceptance regime (the "
            "displaced entries) as one row group among the four regimes of "
            "Table D.3 — since the main text carries the per-module result in "
            "sweeps, whose ratios are the same cells (the user, 2026-09-17: "
            "*\"move the per node tables to the appendix\"*). Absolute cost cells are per-run "
            "means with the seed bracket; a ratio against the reference is "
            "read three ways — pooled (Σ arm / Σ reference), per-run median, "
            "and the count of runs on which the arm cost more. The reference "
            "is `A1` on a pulsed configuration and `A0` on a steady-state "
            "one. The accuracy tables are on both rulers and carry the audit "
            "position as a column; their whole-state columns are large for "
            "`A2` by design and are not judged. Denominators are runs of the "
            "configuration in the source (25 per arm in the displaced regime; "
            "one per design-vector column per arm in a stencil source), and "
            "every sub-heading row states its own. The per-run overhead "
            "tables and the predicate trial are in the companion file."
        ),
        layouts=(
            "module_scope",
            "node_calls_per_block",
            "reference_entries",
            "cost_per_call",
            "matched_accuracy",
            "full_distributions",
            "excluded_namespaces",
            "fixed_point_distance",
            "ownership_rung",
            "failure_taxonomy_evaluation",
        ),
    ),
    Group(
        number="D.3",
        title="The optimisation phase",
        context=(
            "One full optimisation per start, 25 starts per arm per "
            "configuration (seed 0 unperturbed, seeds 1–24 displaced at "
            "δ = 0.10). Every check is over **the seed set** — the seeds on "
            "which every arm reached an accepted optimum (status ok and the "
            "output file's `ifail == 1`) — whose size the per-arm success "
            "grid in §4.3 (Table 10) states once per configuration and every "
            "other table repeats as its n; the seeds outside it are the failure table's, in the "
            "companion file, so the filter cannot flatter an arm that fails "
            "on expensive seeds. Every ratio is against the flat control "
            "`B0`; `BR → B0` is published beside as the yardstick, never "
            "accepted on. Cost is solve-phase model-node executions summed "
            "over the optimiser's attempts (the output path and the exit "
            "audit excluded alike in every arm), published with and without "
            "the seeds on which either side retried; the attempt-summation "
            "identity that licenses this is printed per run in the companion "
            "file. **One construction, one table**: the three configurations "
            "are row groups of each table, under a sub-heading row naming the "
            "configuration and stating its own n; `B1` is inactive on "
            "`st_regression`, so its rows are absent from that group and its "
            "columns empty there. The phase's headline tables are in §4.3 "
            "and are not repeated here — per-arm success (Table 10), whose "
            "merged whole with the failure taxonomy and the seed set is "
            "Table D.12 below, the same optimum (Table 11), the optimiser's "
            "path (Tables 12–15), check 4's cost sums (Table 16) and module "
            "sweeps per run (Table 17), whose function-weighted twin is "
            "Table D.24 in D.4."
        ),
        layouts=(
            "reliability_and_taxonomy",
            "problem_definition",
            "node_calls_per_module",
            "location_diagnostic",
            "identity",
            "iteration_multiplier",
            "cost",
            "cost_anchors",
            "sweeps_and_prime_calls",
            "achieved_accuracy",
            "lift_closed",
        ),
    ),
    Group(
        number="D.4",
        title="The aggregate under three weightings",
        context=(
            "**How the weight per module skews the headline average** (the "
            "user, 2026-09-17). The per-module sweep ratios of Tables 9 and "
            "17 are unit-free; only the aggregate depends on the weight per "
            "module, and the two tables here weight the same sweep counts "
            "per **function** — the dependency analysis's callable submodels "
            "behind each module's collapsed-DSM rows, a model with none "
            "counting as one — beside the report's two other weights. Three "
            "weightings of one set of sweep counts, each configuration "
            "nof / lad / st. In the **evaluation phase** (one `call_models` "
            "evaluation from a displaced entry, `A2` against its reference) "
            "the aggregate reads **0.5625 / 0.5772 / 0.5016** in **node "
            "calls** (Table 8's partitioning rung — the acceptance quantity), "
            "**[0.724, 0.767] / [0.742, 0.786] / [0.655, 0.709]** in **DSM "
            "rows** (Table 9's total) and **[0.695, 0.794] / [0.709, 0.811] / "
            "[0.626, 0.720]** in **functions** (Table D.23's total). In the "
            "**optimisation phase** (`B2` against `B0` over the seed set) it "
            "reads **0.6395 / 0.4504 / 0.5331** in node calls (Table 16, "
            "check 4), **[0.690, 0.736] / [0.476, 0.508] / [0.599, 0.653]** in "
            "DSM rows (Table 17's total) and **[0.650, 0.746] / [0.448, "
            "0.514] / [0.565, 0.653]** in functions (Table D.24's total). A "
            "bracket is the `[v = 1, v = 0]` attribution interval of the "
            "once-per-run nodes' rows or functions (trap T9). **What does not "
            "depend on the weighting:** under any non-negative weighting the "
            "aggregate is a weighted mean of the per-module ratios and so lies "
            "between the smallest and the largest of them, and every "
            "per-module ratio in Tables 9 and 17 is at or below 1 except one "
            "— M2 on `large_tokamak_nof` in the evaluation phase, at "
            "**1.0078**; the largest in the optimisation phase is M2 on the "
            "same configuration at **0.8691**. So the **direction** of the "
            "saving is weighting-independent (only a weighting that put "
            "essentially all its weight on that one module could read "
            "otherwise) and its **magnitude** is not: across the three "
            "weightings the evaluation-phase aggregate spans 0.50–0.81 and "
            "the optimisation-phase aggregate 0.45–0.75. Node calls weight "
            "the aggregate toward the groups with many executing nodes — M3's "
            "twelve and the once-per-run set — where the partition saves "
            "most; DSM rows and functions weight it toward M1 (24 of the 47 "
            "rows the four modules hold, 178 of their 344 functions on "
            "`large_tokamak_nof`), where it saves less. Node calls remain the "
            "acceptance unit (D19, D29); these tables are reported, not "
            "accepted on."
        ),
        layouts=(
            "module_sweeps_functions_evaluation",
            "module_sweeps_functions_optimisation",
        ),
    ),
)

#: The companion file's groups, each naming the layouts it prints.  The
#: ``"omitted"`` group is not a layout list: it is every **report** table of
#: this rendering that leaves a per-seed column out, printed again with every
#: column.
COMPANION_GROUPS: tuple[dict[str, Any], ...] = (
    {
        "number": "F.1",
        "title": "The evaluation phase — one row per run",
        "context": (
            "The per-run tables of the evaluation phase, one construction per "
            "table with the configurations and regimes as row groups: what "
            "each finished run's convergence test cost (one row per run; the "
            "two predicates in columns of their own, never summed) and the "
            "predicate trial (one row per pair of runs under the two rulers). "
            "Populations and constructions are as declared in Appendix D.0 of "
            "the report."
        ),
        "layouts": (
            "matched_accuracy_headline_other_regimes",
            "per_call_cost_headline_other_regimes",
            "module_sweeps_other_regimes",
            "per_sweep_overhead_evaluation",
            "predicate_trial",
        ),
    },
    {
        "number": "F.2",
        "title": "The optimisation phase — one row per seed or per run",
        "context": (
            "The per-seed and per-run tables of the optimisation phase, one "
            "construction per table with the configurations as row groups: "
            "per-arm success by seed (every start offered, each arm's outcome "
            "class there), the failure table (every seed outside the seed "
            "set, with what failed there and what the other arms cost at the "
            "same start), the attempt-summation identity (every run's "
            "per-attempt costs against its solve-phase total) and the per-run "
            "overhead."
        ),
        "layouts": (
            "per_arm_success_by_seed",
            "failure_table",
            "attempt_summation",
            "per_sweep_overhead_optimisation",
        ),
    },
    {
        "number": "F.3",
        "title": "Appendix D's tables with their per-seed columns",
        "context": (
            "The full versions of the report's tables whose columns listing a "
            "value per seed inside one cell (the paired seeds, the seeds of "
            "the set, the attempts per seed, the components above τ per run) "
            "the report omits. Every other cell is identical to the report's."
        ),
        "layouts": "omitted",
    },
)


#: The report's conventions paragraph, printed once at the appendix's opening
#: (formerly the §4 preamble's).
CONVENTIONS = (
    "**Conventions that hold in every table (D21 (c)).** Absolute cost cells "
    "are per-run means with the seed bracket. A ratio against the reference is "
    "given three ways: pooled (sum over the set / sum over the set), per-run "
    "median with `[min, max]`, and the count of seeds on which the arm cost "
    "more. Configurations appear in the fixed order nof / lad / st and are "
    "never pooled (D21 (b)). Prime calls appear beside node calls, never inside "
    "them (D19). Node-call ratios are the acceptance quantities; timings are "
    "context and no conclusion rests on one (I-10). Arm names are `AR / A0 / "
    "A1 / A2` and `BR / B0 / B1 / B2` (2026-09-15); the records carry the "
    "names of their day and are translated at read (trap T16)."
)


# --------------------------------------------------------------------------
# the stage records
# --------------------------------------------------------------------------


def stage_record(records_dir: Path, stage: str) -> dict[str, Any]:
    """One stage's own record, or a refusal naming the stage that makes it."""
    path = Path(records_dir) / stage / "measurements.json"
    if not path.exists():
        raise PlanTablesError(
            f"stage {stage!r} has written no record at {path}.  The appendix's "
            f"{stage} tables are that stage's own output and are never typed "
            f"by hand: run `experiment_runner.py --measure {stage}` (or "
            f"`--measure all`) first."
        )
    try:
        return json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001
        raise PlanTablesError(f"{path} is not readable JSON: {exc}") from exc


def assert_stage_read_what_is_there(
    record: Mapping[str, Any], records_dir: Path, section: Section
) -> str:
    """Refuse to render a section from a stage record its sources have outrun.

    D.1 is not rendered from the verdict records: it is rendered from the
    ``gate_table`` **stage** record, which was made from the verdicts at the
    moment that stage ran.  Re-run a gate afterwards and this renderer would
    reproduce the older verdict — the same table, the same numbers, the same
    PASS or FAIL — with nothing anywhere to say the file on disk now says
    something else.  That is not a hypothetical: it happened, and the first
    re-render of a fixed gate reproduced its failing row byte for byte.

    The check is the framework's, not this module's, so that it is one
    mechanism: the stage declares what it reads, the framework stamps it, and
    every consumer refuses the same way.
    """
    try:
        return framework.assert_records_read_are_current(
            record,
            records_dir,
            stage=section.stage,
            remedy=(
                f"Re-run `experiment_runner.py --measure {section.stage}` and "
                f"render again: {section.number} is that stage's output, and "
                f"a section rendered from a record older than the verdicts it "
                f"summarises publishes the older verdict without saying so."
            ),
        )
    except framework.StaleRecordError as exc:
        raise PlanTablesError(str(exc)) from exc


def _survey(paths: Sequence[Path]) -> dict[str, Any]:
    """Commit, run kind, audit position, ruler and instrument over *paths*."""
    heads: dict[str, int] = {}
    kinds: dict[str, int] = {}
    positions: set[str] = set()
    rulers: set[str] = set()
    instruments: set[str] = set()
    total = 0
    for path in paths:
        try:
            record = json.loads(Path(path).read_text())
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
        "n_run_records": total,
        "records_by_commit": dict(sorted(heads.items())),
        "records_by_run_kind": dict(sorted(kinds.items())),
        "audit_positions": sorted(positions),
        "predicate_modes": sorted(rulers),
        "exit_audit_instrument": sorted(instruments),
    }


def population_marker(campaign: Campaign, records_dir: Path) -> dict[str, Any]:
    """What every tally cell is over, measured from the records themselves.

    The commit, the record count, the audit position, the convergence ruler and
    the exit-audit instrument version, all read from the run records rather
    than written down here — a marker that says which instrument produced a
    residual, and is itself hand-maintained, is a marker that will one day name
    the wrong instrument.

    **Which records:** the tally's published sources' (``tally.published_sources``
    — the campaign family once a campaign record exists, the gate family
    otherwise), so the marker describes the population the tables were
    computed over and no other.  The gate runs under *records_dir* are
    surveyed too, as the population D.1 is over and — with the campaign
    present — as the tables' earlier fill, named as excluded.
    """
    from harness.measurement import tally as tally_mod  # noqa: PLC0415

    present = tally_mod.campaign_present(campaign)
    published = tally_mod.published_sources(campaign)
    by_source: dict[str, int] = {}
    paths: list[Path] = []
    seen: set[str] = set()
    for source in published:
        n = 0
        for directory in tally_mod.source_directories(campaign, source):
            path = Path(directory) / "metrics.json"
            if path.exists():
                n += 1
                if str(path) not in seen:
                    seen.add(str(path))
                    paths.append(path)
        by_source[source.name] = n
    root = Path(records_dir)
    gates = _survey(sorted(root.rglob("metrics.json")))
    return {
        "verdict_commit": framework.git_head(),
        "campaign_present": present,
        "population_family": "campaign" if present else "gate",
        "published_sources": by_source,
        **_survey(paths),
        "gate_runs": gates,
        "execution_approved": EXECUTION_APPROVED,
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
    }


def _commits(block: Mapping[str, Any]) -> str:
    return ", ".join(f"`{h[:8]}`" for h in block["records_by_commit"]) or "—"


def _marker_sentence(marker: Mapping[str, Any]) -> str:
    """The full population statement, made once at the appendix's opening."""
    audit = (
        f"The exit audit was taken at position(s) "
        f"{', '.join(f'`{p}`' for p in marker['audit_positions'])} with the "
        f"convergence ruler(s) "
        f"{', '.join(f'`{r}`' for r in marker['predicate_modes'])} and the "
        f"exit-audit instrument "
        f"{', '.join(f'`{i}`' for i in marker['exit_audit_instrument'])}."
    )
    if marker["campaign_present"]:
        gates = marker["gate_runs"]
        sources = ", ".join(
            f"`{name}` {n}" for name, n in marker["published_sources"].items()
        )
        return (
            f"**Population: the campaign, not the gate runs.** "
            f"`EXECUTION_APPROVED` is {marker['execution_approved']} and the "
            f"campaign has run: every cell of this appendix, of §4's headline "
            f"tables and of the companion file is over the "
            f"{marker['n_run_records']} campaign run "
            f"record(s) made at commit(s) {_commits(marker)}, by run kind "
            f"{marker['records_by_run_kind']}, by source {sources}. The "
            f"{gates['n_run_records']} gate run record(s) at {_commits(gates)} "
            f"(by run kind {gates['records_by_run_kind']}) were these tables' "
            f"earlier fill, before execution approval; they are excluded from "
            f"every published cell **by kind** (gate `run_kind_separation`) and "
            f"appear only in D.1, which is the gates' own table. {audit}"
        )
    return (
        f"**Population: the gate runs, not the campaign.** "
        f"`EXECUTION_APPROVED` is {marker['execution_approved']}, so no "
        f"campaign record exists: every cell of this appendix and of §4's "
        f"headline tables is over the "
        f"{marker['n_run_records']} run record(s) the verification gates made "
        f"— one or two seeds per arm — at commit(s) {_commits(marker)}, by "
        f"run kind {marker['records_by_run_kind']}. {audit} The "
        f"campaign fills these tables again, over its own twenty-five seeds "
        f"per arm, after the user approves execution."
    )


# --------------------------------------------------------------------------
# one table on the page
# --------------------------------------------------------------------------


def _column_key(column: Any) -> str:
    return str(column["key"]) if isinstance(column, Mapping) else str(column)


def _column_heading(column: Any) -> str:
    if isinstance(column, Mapping):
        return str(column.get("heading") or column.get("key"))
    return str(column)


def _grid_lines(table: Mapping[str, Any], *, omit: Sequence[str] = ()) -> list[str]:
    """The table's grid, from the record's rendered cells where it has them.

    A record made since task A79 carries ``cells`` (the columns' own
    rendering, row by row) and the grid is built from them so that a column
    can be left out; an older record, a recomputed table or a self-check
    fixture carries only ``markdown``, and the grid is its ``|`` lines —
    which is also what strips the caption an older record's ``markdown``
    still carries, the cause of the doubled captions before A79.
    """
    columns = table.get("columns") or []
    cells = table.get("cells")
    if cells is not None and columns:
        keep = [i for i, c in enumerate(columns) if _column_key(c) not in set(omit)]
        headings = [_column_heading(columns[i]) for i in keep]
        lines = ["| " + " | ".join(headings) + " |", "|" + "|".join("---" for _ in keep) + "|"]
        for row in cells:
            lines.append("| " + " | ".join(str(row[i]) for i in keep) + " |")
        return lines
    if omit:
        raise PlanTablesError(
            f"table {table.get('table')!r} asks the report to omit columns "
            f"{list(omit)} but its record carries no rendered cells; re-run "
            f"the stage that emits it"
        )
    return [
        line
        for line in str(table.get("markdown") or "").splitlines()
        if line.startswith("|")
    ]


def _caption_text(table: Mapping[str, Any]) -> str:
    """The few lines the report prints: the summary, or the full caption
    where a stage has not written one (an older record, a recomputed table)."""
    summary = str(table.get("caption_summary") or "").strip()
    if summary:
        return summary
    return str(table.get("caption") or "").strip()


def _table_block(
    table: Mapping[str, Any],
    number: str,
    *,
    omit: Sequence[str] = (),
    full_version: str | None = None,
) -> list[str]:
    """One table as the documents print it: a numbered caption, the grid, the
    construction name.  ``full_version`` names the companion table that holds
    the omitted columns, when any are.

    A **combined** table prints, under the grid, the construction it is an
    instance of *and* every stage table it was built from, by name.  A table
    number is a position and shifts (trap T17); those names do not, and they
    are what traces a cell in this grid back to the stage record that holds
    it — which is also what the cell-preservation check keys on.
    """
    caption = _caption_text(table)
    denominator = f"n = {table['denominator']} ({table['denominator_is']})."
    omitted = ""
    if omit:
        headings = [
            _column_heading(c)
            for c in table.get("columns") or []
            if _column_key(c) in set(omit)
        ]
        omitted = (
            f" Per-seed column(s) {', '.join(f'*{h}*' for h in headings)}: "
            f"{full_version}."
        )
    lines = [f"**Table {number}.** *{caption} {denominator}{omitted}*", ""]
    blocks = table.get("blocks")
    if blocks:
        # One grid per block, each under its own bold heading line — the
        # previous revision's per-configuration form (task A85
        # (v3-table-formats)).  The caption above is the table's, stated once.
        columns = table.get("columns") or []
        keep = [
            i for i, c in enumerate(columns) if _column_key(c) not in set(omit)
        ]
        header = [
            "| " + " | ".join(_column_heading(columns[i]) for i in keep) + " |",
            "|" + "|".join("---" for _ in keep) + "|",
        ]
        for block in blocks:
            lines.append(str(block["label"]))
            lines.append("")
            lines.extend(header)
            for row in block["cells"]:
                lines.append("| " + " | ".join(str(row[i]) for i in keep) + " |")
            lines.append("")
    else:
        lines.extend(_grid_lines(table, omit=omit))
        lines.append("")
    lines.append(f"<sub>`{table['table']}`</sub>")
    combines = table.get("combines") or []
    if combines:
        lines.append("")
        lines.append(
            "<sub>combining "
            + f"{len(combines)} stage table(s): "
            + "; ".join(f"`{name}`" for name in combines)
            + "</sub>"
        )
    lines.append("")
    return lines


def _gate_table_block(block: Mapping[str, Any], number: str) -> list[str]:
    """D.1: the gate table, which is a measurement stage and not a Table."""
    lines = [
        f"**Table {number}.** *{block['caption']} Population: "
        f"{block['population']}.*",
        "",
    ]
    lines.extend(
        line
        for line in str(block.get("markdown") or "").splitlines()
        if line.startswith("|")
    )
    lines.append("")
    lines.append(
        f"**{block['n_pass']} PASS, {block['n_fail']} FAIL, "
        f"{block['n_not_run']} not run; {block['n_teeth_tripped']} of "
        f"{block['n_teeth']} teeth tripped.**"
    )
    lines.append("")
    lines.append("<sub>`gate table`</sub>")
    lines.append("")
    return lines


# --------------------------------------------------------------------------
# sorting the tables into the two documents
# --------------------------------------------------------------------------


@dataclass
class Placed:
    """One table the tally emitted, with what it is of and where it goes."""

    stage: str
    kind: str
    table: Mapping[str, Any]
    emitted_index: int
    #: What the table's name says it is of: the construction, the
    #: configuration (``None`` where the construction is already over the
    #: configurations) and the source family.
    construction: str = ""
    configuration: str | None = None
    source: str | None = None
    source_family: str | None = None
    #: The layout(s) that render it — several only where each takes a
    #: declared, disjoint selection of its rows — or ``None`` for a stage
    #: rendered nowhere.
    layouts: tuple[Layout, ...] = ()

    @property
    def layout(self) -> Layout | None:
        """The first layout that renders it, for the callers that want one."""
        return self.layouts[0] if self.layouts else None


def _identify(name: str) -> tuple[str, str | None, str | None]:
    """A table's construction, configuration and source, from its own name.

    Every tally table is named ``<construction> — <configuration> —
    <source>``, or ``<construction> — <source>`` where the construction is
    already over the configurations (the block table, the optimiser's path).
    The separator is an em dash with spaces, which no configuration or source
    name contains.  Reading the name rather than adding a field to the record
    keeps this a **rendering** change: the stage records are the ones the
    gates over cells already compared.
    """
    parts = [part.strip() for part in str(name).split(" — ")]
    if len(parts) >= 3:
        return parts[0], parts[1], " — ".join(parts[2:])
    if len(parts) == 2:
        return parts[0], None, parts[1]
    return parts[0], None, None


def _family(source: str | None) -> str | None:
    """A source's family: the part before the arm set it was taken over."""
    if source is None:
        return None
    return source.split(" · ")[0].strip()


def _layout_for(placed: Placed) -> list[Layout] | None:
    """The layout(s) that render *placed*, or a refusal naming the choice.

    Normally one.  Several only where each declares a disjoint selection of
    the table's rows — how a construction the previous revision published as
    several tables of one shape is rendered from the one table the tally
    emits.  None claiming it is a declaration that has fallen behind the
    tally: the appendix's shape is declared and never guessed at.
    """
    matches = [
        layout
        for layout in LAYOUTS
        if layout.stage == placed.stage
        and placed.kind in layout.kinds
        and bool(layout.detail) == bool(placed.table.get("detail"))
        and (not layout.sources or placed.source_family in layout.sources)
    ]
    if len(matches) > 1:
        # Or when each names the others as a table it **shares**: a
        # construction the report prints twice on purpose — per-arm success,
        # which is the main text's grid in the previous revision's §5.1 form
        # and a constituent of the appendix's merged reliability table.  A
        # cell may appear in more than one table; it may never be lost or
        # changed, and the naming must be mutual so one layout cannot take a
        # share of another's table without that other saying so.
        names = {m.name for m in matches}
        if all(names - {m.name} <= set(m.shares_tables_with) for m in matches):
            return matches
        # Several layouts may claim one stage table when each takes a
        # declared, disjoint set of its rows: the previous revision published
        # the iteration multiplier, the evaluation count and the node-call
        # rate as three tables of one shape, and this rendering does too.
        # Undeclared or overlapping claims are still a declaration that has
        # fallen behind the tally.
        undeclared = [m.name for m in matches if not m.select]
        if undeclared:
            raise PlanTablesError(
                f"table {placed.table.get('table')!r} is claimed by "
                f"{[m.name for m in matches]}, of which {undeclared} select "
                f"no rows; two layouts may share a table only when each "
                f"declares which of its rows it takes"
            )
        seen: dict[tuple[str, str], str] = {}
        for layout in matches:
            for key, values in layout.select:
                for value in values:
                    other = seen.get((key, value))
                    if other is not None:
                        raise PlanTablesError(
                            f"table {placed.table.get('table')!r}: layouts "
                            f"{other!r} and {layout.name!r} both select "
                            f"{key}={value!r}; a row rendered twice is a cell "
                            f"published twice under two table numbers"
                        )
                    seen[(key, value)] = layout.name
    return matches if matches else None


def _place(records: Mapping[str, Mapping[str, Any]]) -> list[Placed]:
    """Every table of every stage, identified and given its layout.

    Refuses a tally table no layout declares: which construction a table
    belongs to, and how that construction is laid out, is a declaration made
    by whoever adds the table.
    """
    placed: list[Placed] = []
    for stage in TALLY_STAGES:
        for index, table in enumerate(records[stage].get("tables") or []):
            kind = str(table.get("kind") or "")
            if not kind:
                raise PlanTablesError(
                    f"stage {stage!r} emitted table {table.get('table')!r} "
                    f"without a kind; the appendix groups tables by kind and "
                    f"does not guess one"
                )
            construction, configuration, source = _identify(table.get("table") or "")
            row = Placed(
                stage=stage,
                kind=kind,
                table=table,
                emitted_index=index,
                construction=construction,
                configuration=configuration,
                source=source,
                source_family=_family(source),
            )
            found = _layout_for(row)
            row.layouts = tuple(found or ())
            if not row.layouts:
                raise PlanTablesError(
                    f"stage {stage!r} emitted {table.get('table')!r} (kind "
                    f"{kind!r}, source {row.source_family!r}, detail="
                    f"{bool(table.get('detail'))}) that no layout of "
                    f"plan_tables.LAYOUTS declares.  A construction's layout "
                    f"— which table it is combined into, and where that table "
                    f"goes — is declared, never guessed: place it before "
                    f"rendering."
                )
            placed.append(row)
    for index, table in enumerate(records[UNRENDERED_STAGE].get("tables") or []):
        construction, configuration, source = _identify(table.get("table") or "")
        placed.append(
            Placed(
                stage=UNRENDERED_STAGE,
                kind=str(table.get("kind") or "recomputed"),
                table=table,
                emitted_index=index,
                construction=construction,
                configuration=configuration,
                source=source,
                source_family=_family(source),
            )
        )
    return placed


# --------------------------------------------------------------------------
# one construction, one table
# --------------------------------------------------------------------------


@dataclass
class Combined:
    """One rendered table: its layout, the tables it is built from, its grid."""

    layout: Layout
    constituents: list[Placed]
    table: Mapping[str, Any]
    #: ``Table 7`` / ``Table D.4`` / ``Table F.2`` — assigned at render.
    number: str | None = None
    #: Where it prints: the layout's ``where``, or ``"companion"`` for the
    #: full version of a report table whose per-seed columns the report omits.
    where: str = "report"
    #: The companion number of this table's full version, where it has one.
    full_version: str | None = None


def _headings_of(placed: Placed, overrides: Mapping[str, str]) -> list[tuple[str, str]]:
    return [
        (_column_key(column), overrides.get(_column_key(column), _column_heading(column)))
        for column in placed.table.get("columns") or []
    ]


def _union_columns(
    constituents: Sequence[Placed], overrides: Mapping[str, str], layout: Layout
) -> list[dict[str, str]]:
    """The combined table's columns: the constituents' own, in order, once.

    Keyed by ``(key, heading)``, so a column two constituents spell the same
    way is one column and a column they spell differently is a refusal unless
    the layout declares what the combined heading says.  A heading taken from
    whichever constituent happened to be first would say ``vs A1 pooled``
    over a column whose `st_regression` rows are against `A0`.
    """
    columns: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    by_key: dict[tuple[str, str], set[str]] = {}
    for placed in constituents:
        for key, heading in _headings_of(placed, overrides):
            # Disagreement is asked **within a construction**.  Across
            # constructions the same key legitimately names different things —
            # cost per call's `ok` is runs that finished per run scheduled,
            # the failure taxonomy's `ok` is a count of runs — and those are
            # two columns of the merged table, not a contradiction.
            by_key.setdefault((placed.kind, key), set()).add(heading)
            if (key, heading) not in seen:
                seen.add((key, heading))
                columns.append({"key": key, "heading": heading})
    disagreed = {k[1]: sorted(v) for k, v in by_key.items() if len(v) > 1}
    if disagreed:
        raise PlanTablesError(
            f"layout {layout.name!r} combines tables of one construction "
            f"whose columns disagree on a heading: {disagreed}.  Declare the "
            f"combined heading in the layout's `headings`; a combined column "
            f"labelled with one constituent's heading states the wrong thing "
            f"about the others."
        )
    if layout.column_order:
        keys = [c["key"] for c in columns]
        missing = [k for k in layout.column_order if k not in keys]
        if missing:
            raise PlanTablesError(
                f"layout {layout.name!r} orders column(s) {missing}, which "
                f"its tables do not have (they have {keys})"
            )
        named = list(layout.column_order)
        columns = [
            c for key in named for c in columns if c["key"] == key
        ] + [c for c in columns if c["key"] not in set(named)]
    return columns


def _arm_set_note(placed: Placed) -> str | None:
    """``arms BR·B0·B2`` where this group does not carry the phase's whole
    ladder — the previous revision's `st` block, whose heading said *"no
    B1"*.  ``None`` where it does, because naming a set that is the whole of
    the ladder distinguishes nothing."""
    source = str(placed.source or "")
    if " · " not in source:
        return None
    arms = source.split(" · ", 1)[1].split("·")
    ladder = LADDERS.get(str(placed.stage))
    if ladder and len(arms) != len(ladder):
        return "arms " + "·".join(arms)
    return None


def _group_label(placed: Placed, *, with_regime: bool) -> str:
    """The bold sub-heading row over one constituent's rows.

    **The configuration and its own n, and nothing more** — the previous
    revision's grids put the configuration in the first column and its ``n``
    in the bold line over the block, and said what that ``n`` counts in the
    caption.  This row used to carry the tally's whole table name and the
    population sentence with it
    (``large_tokamak_nof · campaign_optimisation · BR·B0·B1·B2 — n = 22
    (seeds on which every arm of large_tokamak_nof converged)``); the table
    name is under the grid, where the renderer names every stage table it
    combines, and the population sentence is in the caption, where the
    denominator sentence names what a group's n counts (task A87
    (v3-grid-polish), as task A86 (v3-tables-remainder) did for the block
    heading lines).

    *with_regime* is true where one table combines more than one **source
    regime**, and the regime is then named beside the configuration because
    it is the other half of what a row group is over.  The arm set is named
    only where the group does not carry the phase's whole ladder, exactly as
    a block heading line names it.
    """
    name = str(placed.configuration or "")
    family = str(placed.source_family or "")
    if with_regime and name and family:
        name = f"{name} · {family}"
    elif not name:
        name = family or placed.construction
    parts = [f"n = {placed.table.get('denominator')}"]
    arms = _arm_set_note(placed)
    if arms:
        parts.append(arms)
    return f"**{name} ({'; '.join(parts)})**"


def _population_sentences(constituents: Sequence[Placed]) -> list[str]:
    """What each group's ``n`` counts, once per distinct sentence.

    The constituents' own ``denominator_is`` strings, with the configuration
    named in them replaced by *that configuration* so that three sentences
    differing only in a configuration name are one sentence.  Nothing is
    rewritten in a record: this is the caption's half of the sub-heading
    reduction, and it is the constituents' own words.
    """
    out: list[str] = []
    for placed in constituents:
        text = str(placed.table.get("denominator_is") or "").strip()
        configuration = str(placed.configuration or "")
        if configuration:
            text = text.replace(configuration, "that configuration")
        if text and text not in out:
            out.append(text)
    return out


def _cells_by_key(placed: Placed, overrides: Mapping[str, str]) -> list[dict[tuple[str, str], str]]:
    """One constituent's rows as ``{(column key, heading): cell}``.

    The cells are the ones the constituent's **own** columns rendered — not
    re-derived here — so a combined grid holds the same strings the
    per-configuration grids held.
    """
    headings = _headings_of(placed, overrides)
    cells = placed.table.get("cells")
    if cells is None:
        raise PlanTablesError(
            f"table {placed.table.get('table')!r} carries no rendered cells, "
            f"so it cannot be combined with another; re-run the stage that "
            f"emits it"
        )
    return [
        {headings[i]: str(row[i]) for i in range(min(len(headings), len(row)))}
        for row in cells
    ]


def _stack(constituents: Sequence[Placed], columns, overrides) -> list[list[str]]:
    """The constituents one after another, each under its sub-heading row."""
    keys = [(c["key"], c["heading"]) for c in columns]
    with_regime = len({p.source_family for p in constituents}) > 1
    grid: list[list[str]] = []
    for placed in constituents:
        grid.append(
            [_group_label(placed, with_regime=with_regime)] + [""] * (len(keys) - 1)
        )
        for row in _cells_by_key(placed, overrides):
            grid.append([row.get(key, "") for key in keys])
    return grid


def _merge_group(
    members: Sequence[Placed], keys: Sequence[tuple[str, str]], overrides, layout: Layout
) -> list[list[str]]:
    """One configuration's constituents aligned on ``layout.join``: the rows,
    without a heading row.

    The constituents are taken in the layout's ``kinds`` order and the first
    to carry a cell for a column keeps it — **unless the cell is empty**.  An
    empty cell is a column the row does not have (the appendix's convention;
    ``—`` is a value that is missing), so it never claims the column and a
    later constituent's cell fills it.  That is what lets a construction
    carrying only the *new* cells of a grid — the function-weighted total's
    `functions` column and total row — sit first in the order, so its total
    row wins, while its module rows leave every other cell to the sweep table
    they are republished from (task A88 (function-weighted-sweeps)).
    """
    join = layout.join or ""
    join_key = next((key for key in keys if key[0] == join), None)
    members = sorted(members, key=lambda p: layout.kinds.index(p.kind))
    rows_by_member = [(p, _cells_by_key(p, overrides)) for p in members]
    # The spine is the join values the constituents that *have* the join
    # column carry, in the order they first appear.  A constituent
    # without that column contributes no row of its own — it is the
    # per-configuration fact broadcast across the ones that do.
    order: list[str] = []
    for _p, rows in rows_by_member:
        for row in rows:
            if join_key is None or join_key not in row:
                continue
            if row[join_key] not in order:
                order.append(row[join_key])
    spine: list[tuple[str, int]] = []
    for value in order:
        depth = max(
            sum(1 for row in rows if row.get(join_key) == value)
            for _p, rows in rows_by_member
        )
        spine.extend((value, i) for i in range(max(depth, 1)))
    if not spine:
        spine = [("", 0)]
    grid: list[list[str]] = []
    for value, index in spine:
        out: dict[tuple[str, str], str] = {}
        for _p, rows in rows_by_member:
            matching = [
                row
                for row in rows
                if join_key is not None and row.get(join_key) == value
            ]
            if not matching:
                # no join column of its own, or nothing at this value:
                # broadcast a single row, else leave the cells empty.
                matching = rows if len(rows) == 1 else []
            if not matching:
                continue
            chosen = matching[index] if index < len(matching) else matching[-1]
            for key, cell in chosen.items():
                if cell == "":
                    continue
                out.setdefault(key, cell)
        grid.append([out.get(key, "") for key in keys])
    return grid


def _merge(
    constituents: Sequence[Placed], columns, overrides, layout: Layout
) -> list[list[str]]:
    """The constituents of one configuration aligned on ``layout.join``.

    A constituent with no join column at all, or with one row where the group
    has several, is **broadcast** across the group's rows: that is what a fact
    stated once per configuration — the seed set, the entry reference's cost
    — looks like in a table whose rows are arms.
    """
    keys = [(c["key"], c["heading"]) for c in columns]
    grid: list[list[str]] = []
    groups: dict[str, list[Placed]] = {}
    for placed in constituents:
        groups.setdefault(str(placed.configuration), []).append(placed)
    for configuration, members in groups.items():
        members = sorted(
            members, key=lambda p: layout.kinds.index(p.kind)
        )
        grid.append(
            [
                f"**{configuration} — {len(members)} construction(s): "
                + "; ".join(f"`{p.construction}` n = {p.table.get('denominator')}" for p in members)
                + "**"
            ]
            + [""] * (len(keys) - 1)
        )
        grid.extend(_merge_group(members, keys, overrides, layout))
    return grid


def _block_label(placed: Placed, layout: Layout) -> str:
    """The bold heading **line** over one block of a per-configuration table.

    The previous revision's form, which the user's three images are:
    ``**`nof`** (n = 22)``, with the arm set named where it is not the
    configuration's full ladder.  The configuration is written short — the
    report's own ``nof / lad / st`` (§4), not the previous revision's ``tok``,
    because the report names that configuration ``nof`` throughout and a
    table that renamed it would be a table the prose cannot cite.
    """
    name = SHORT_NAMES.get(str(placed.configuration), str(placed.configuration or ""))
    block = placed.table.get("block_denominator")
    if block:
        parts = [f"n = {block[0]} {block[1]}"]
    else:
        parts = [f"n = {placed.table.get('denominator')}"]
    # The arm set only where the block does not carry the phase's whole
    # ladder — the previous revision's `st` block, whose heading said "no B1".
    arms = _arm_set_note(placed)
    if arms:
        parts.append(arms)
    return f"**`{name}`** ({'; '.join(parts)})"


def _apply_select(
    layout: Layout, columns: Sequence[Mapping[str, str]], grid: Sequence[Sequence[str]]
) -> list[list[str]]:
    """The rows this layout takes, of a stage table several layouts share."""
    if not layout.select:
        return [list(row) for row in grid]
    keys = [c["key"] for c in columns]
    kept: list[list[str]] = []
    for row in grid:
        take = True
        for key, values in layout.select:
            if key not in keys:
                raise PlanTablesError(
                    f"layout {layout.name!r} selects on column {key!r}, which "
                    f"its tables do not have (they have {keys})"
                )
            if str(row[keys.index(key)]).strip() not in values:
                take = False
                break
        if take:
            kept.append(list(row))
    if not kept:
        raise PlanTablesError(
            f"layout {layout.name!r} selected no row at all ({layout.select}); "
            f"a table with no row is a section with a hole in it (trap T11)"
        )
    return kept


def _apply_merges(
    layout: Layout, columns: Sequence[Mapping[str, str]], grid: Sequence[Sequence[str]]
) -> tuple[list[dict[str, str]], list[list[str]]]:
    """The declared columns joined into one cell each, in place."""
    if not layout.merges:
        return [dict(c) for c in columns], [list(row) for row in grid]
    keys = [c["key"] for c in columns]
    consumed: dict[str, Merged] = {}
    for merged in layout.merges:
        for part in merged.parts:
            if part not in keys:
                raise PlanTablesError(
                    f"layout {layout.name!r} merges column {part!r}, which its "
                    f"tables do not have (they have {keys})"
                )
            if part in consumed:
                raise PlanTablesError(
                    f"layout {layout.name!r} merges column {part!r} into both "
                    f"{consumed[part].key!r} and {merged.key!r}; a cell may be "
                    f"rendered once"
                )
            consumed[part] = merged
    out_columns: list[dict[str, str]] = []
    plan: list[tuple[str, Any]] = []
    for column in columns:
        key = column["key"]
        merged = consumed.get(key)
        if merged is None:
            out_columns.append(dict(column))
            plan.append(("copy", keys.index(key)))
        elif key == merged.parts[0]:
            out_columns.append({"key": merged.key, "heading": merged.heading})
            plan.append(("merge", merged))
    out_grid: list[list[str]] = []
    for row in grid:
        cells: list[str] = []
        for what, argument in plan:
            if what == "copy":
                cells.append(str(row[argument]))
            else:
                cells.append(
                    _merge_cells(
                        [str(row[keys.index(part)]) for part in argument.parts],
                        argument.join,
                    )
                )
        out_grid.append(cells)
    return out_columns, out_grid


def _apply_bold(
    layout: Layout, columns: Sequence[Mapping[str, str]], grid: Sequence[Sequence[str]]
) -> list[list[str]]:
    """The result column and the verdict in bold, as the previous revision
    printed them.  A cell already bold, empty or a dash is left alone — a
    group heading row is not a result."""
    if not layout.bold:
        return [list(row) for row in grid]
    keys = [c["key"] for c in columns]
    positions = [keys.index(k) for k in layout.bold if k in keys]
    missing = [k for k in layout.bold if k not in keys]
    if missing:
        raise PlanTablesError(
            f"layout {layout.name!r} bolds column(s) {missing}, which its "
            f"tables do not have (they have {keys})"
        )
    out: list[list[str]] = []
    for row in grid:
        cells = [str(c) for c in row]
        if cells and cells[0].startswith("**"):
            out.append(cells)
            continue
        for index in positions:
            value = cells[index].strip()
            if value and value != "—" and not value.startswith("**"):
                cells[index] = f"**{value}**"
        out.append(cells)
    return out


def _apply_blank_repeats(
    layout: Layout, columns: Sequence[Mapping[str, str]], grid: Sequence[Sequence[str]]
) -> list[list[str]]:
    """A repeated key cell blanked on continuation rows — the previous
    revision's cross-configuration form, where the configuration is named
    once and its further rows leave the cell empty."""
    if not layout.blank_repeats:
        return [list(row) for row in grid]
    keys = [c["key"] for c in columns]
    positions = [keys.index(k) for k in layout.blank_repeats if k in keys]
    missing = [k for k in layout.blank_repeats if k not in keys]
    if missing:
        raise PlanTablesError(
            f"layout {layout.name!r} blanks repeats of {missing}, which its "
            f"tables do not have (they have {keys})"
        )
    out: list[list[str]] = []
    previous: list[str] | None = None
    for row in grid:
        cells = [str(c) for c in row]
        if cells and cells[0].startswith("**"):
            previous = None
            out.append(cells)
            continue
        if previous is not None:
            # Hierarchical: a cell is blanked only while every blanked column
            # to its left also repeats, so a new configuration re-states its
            # name and everything under it.
            for depth, index in enumerate(positions):
                if all(
                    cells[positions[j]] == previous[positions[j]]
                    for j in range(depth + 1)
                ):
                    cells[index] = ""
                else:
                    break
        previous = [str(c) for c in row]
        out.append(cells)
    return out


def _apply_omit(
    layout: Layout, columns: Sequence[Mapping[str, str]], grid: Sequence[Sequence[str]]
) -> tuple[list[dict[str, str]], list[list[str]]]:
    """The declared columns dropped, their content stated in the caption.

    The previous revision's grids carry no column for a label that is the
    same on every row — the quantity of a one-quantity table, the arm set of
    a block — because that label is the caption's.  Declaring the drop here
    keeps it a rendering: the layout's own caption says what the column said,
    and the preservation check applies the same declaration before looking
    for an old row.
    """
    if not layout.omit:
        return [dict(c) for c in columns], [list(row) for row in grid]
    keys = [c["key"] for c in columns]
    missing = [k for k in layout.omit if k not in keys]
    if missing:
        raise PlanTablesError(
            f"layout {layout.name!r} omits column(s) {missing}, which its "
            f"tables do not have (they have {keys})"
        )
    keep = [i for i, key in enumerate(keys) if key not in set(layout.omit)]
    if not keep:
        raise PlanTablesError(
            f"layout {layout.name!r} omits every column it has; a grid with "
            f"no column is a section with a hole in it"
        )
    return (
        [dict(columns[i]) for i in keep],
        [[str(row[i]) for i in keep] for row in grid],
    )


def _transform(
    layout: Layout,
    columns: Sequence[Mapping[str, str]],
    grid: Sequence[Sequence[str]],
) -> tuple[list[dict[str, str]], list[list[str]]]:
    """The V3 forms, in one order: rows selected, cells merged, declared
    columns dropped into the caption, results bolded, repeated keys blanked.
    Every step is a **rendering** of cells a stage record already carries."""
    rows = _apply_select(layout, columns, grid)
    out_columns, rows = _apply_merges(layout, columns, rows)
    out_columns, rows = _apply_omit(layout, out_columns, rows)
    rows = _apply_bold(layout, out_columns, rows)
    rows = _apply_blank_repeats(layout, out_columns, rows)
    return out_columns, rows


def _denominator_is(layout: Layout, constituents: Sequence[Placed]) -> str:
    """What the combined table's own ``n`` counts, for its caption.

    A combined table has no single denominator: its ``n`` is the number of
    groups, and each group carries its own.  The **sub-heading row** carries
    the configuration, the regime where there is more than one, and the
    group's ``n``; what that ``n`` counts is said here, once, instead of once
    per group — which is the caption's half of the heading reduction (task
    A87 (v3-grid-polish)).
    """
    if layout.blocks:
        return (
            "block(s) of this table, each over its own population with its "
            "own n in its heading line; never pooled"
        )
    if layout.mode == "merge":
        return (
            "row group(s) of this table, each over its own population with "
            "its own n in its sub-heading row; never pooled"
        )
    with_regime = len({p.source_family for p in constituents}) > 1
    names = "its configuration" + (" and source regime" if with_regime else "")
    sentences = _population_sentences(constituents)
    counts = "; ".join(sentences)
    return (
        f"row group(s) of this table, each over its own population and never "
        f"pooled; a group's sub-heading row names {names} and its own n, and "
        f"that n counts {counts}"
    )


def _combine(layout: Layout, constituents: Sequence[Placed]) -> Combined:
    """One construction's tables as one table, under the layout's mode."""
    constituents = list(constituents)
    overrides = dict(layout.headings)
    single = layout.mode == "single" or (
        len(constituents) == 1 and not layout.blocks
    )
    if single:
        source = constituents[0].table
        columns = [
            {"key": _column_key(c), "heading": overrides.get(_column_key(c), _column_heading(c))}
            for c in source.get("columns") or []
        ]
        grid = [[str(cell) for cell in row] for row in (source.get("cells") or [])]
        columns, grid = _transform(layout, columns, grid)
        table = dict(source)
        table["columns"] = columns
        table["cells"] = grid
        if layout.caption:
            table["caption_summary"] = layout.caption
        # A single-constituent table names itself by its **layout** and says
        # which stage table it was built from, exactly as a combined one
        # does.  Without that a layout that selects rows or merges cells
        # would print the stage table's name over a grid that is not the
        # whole of it, and a cell could not be traced to the declaration
        # that rendered it (trap T17; task A85 (v3-table-formats)).
        table["table"] = layout.title
        table["combines"] = [source.get("table")]
        return Combined(
            layout=layout,
            constituents=constituents,
            table=table,
            where=layout.where,
        )
    columns = _union_columns(constituents, overrides, layout)
    blocks: list[dict[str, Any]] | None = None
    if layout.blocks and layout.mode == "merge":
        # One block per configuration, each the **merge** of that
        # configuration's constituents on the join column — the per-module
        # form of a grid whose cells come from two constructions (the sweep
        # table and its function-weighted total; task A88
        # (function-weighted-sweeps)).  The heading line is read from the
        # constituent that declares a block denominator, else the first.
        blocks = []
        grid = []
        keys = [(c["key"], c["heading"]) for c in columns]
        by_configuration: dict[str, list[Placed]] = {}
        for placed in constituents:
            by_configuration.setdefault(str(placed.configuration), []).append(placed)
        for members in by_configuration.values():
            rows = _merge_group(members, keys, overrides, layout)
            block_columns, rows = _transform(layout, columns, rows)
            host = next(
                (p for p in members if p.table.get("block_denominator")), members[0]
            )
            blocks.append({"label": _block_label(host, layout), "cells": rows})
            grid.extend(rows)
        columns = block_columns
    elif layout.blocks:
        blocks = []
        grid = []
        for placed in constituents:
            rows = [
                [row.get((c["key"], c["heading"]), "") for c in columns]
                for row in _cells_by_key(placed, overrides)
            ]
            block_columns, rows = _transform(layout, columns, rows)
            blocks.append({"label": _block_label(placed, layout), "cells": rows})
            grid.extend(rows)
        columns = block_columns
    elif layout.mode == "stack":
        columns, grid = _transform(layout, columns, _stack(constituents, columns, overrides))
    elif layout.mode == "merge":
        columns, grid = _transform(
            layout, columns, _merge(constituents, columns, overrides, layout)
        )
    else:
        raise PlanTablesError(f"layout {layout.name!r} has no mode {layout.mode!r}")
    omits = sorted({
        key
        for placed in constituents
        for key in (placed.table.get("report_omits") or [])
    })
    merged_away = {part for m in layout.merges for part in m.parts}
    # A column the layout has merged into another, or dropped into its
    # caption, is not a per-seed column held back for the companion: it is
    # not in this grid at all, and the caption already says where it went.
    omits = [
        key
        for key in omits
        if key not in merged_away and key not in set(layout.omit)
    ]
    audit_positions = sorted({
        position
        for placed in constituents
        for position in (placed.table.get("audit_positions") or [])
    })
    table = {
        "table": layout.title,
        "kind": layout.name,
        "detail": bool(layout.detail),
        "report_omits": omits,
        "caption_summary": layout.caption,
        "caption": layout.caption,
        "denominator": len(constituents),
        "denominator_is": _denominator_is(layout, constituents),
        "acceptance": any(p.table.get("acceptance") for p in constituents),
        "audit_positions": audit_positions,
        "columns": columns,
        "rows": [],
        "cells": grid,
        "combines": [p.table.get("table") for p in constituents],
    }
    if blocks is not None:
        table["blocks"] = blocks
    return Combined(
        layout=layout,
        constituents=constituents,
        table=table,
        where=layout.where,
    )


def _all_combined(placed: Sequence[Placed]) -> list[Combined]:
    """Every combined table, in the layouts' declared order."""
    out: list[Combined] = []
    for layout in LAYOUTS:
        constituents = [p for p in placed if layout in p.layouts]
        if not constituents:
            continue
        if layout.mode == "merge":
            # Configuration-major, then the layout's declared order of
            # constructions: the host first, so its columns lead the grid.
            configurations = list(
                dict.fromkeys(str(p.configuration) for p in constituents)
            )
            constituents.sort(
                key=lambda p: (
                    configurations.index(str(p.configuration)),
                    layout.kinds.index(p.kind),
                )
            )
        else:
            # Source-major, then the tally's own emission order, which runs
            # the configurations nof / lad / st inside each source.
            constituents.sort(
                key=lambda p: (
                    SOURCE_ORDER.index(p.source_family)
                    if p.source_family in SOURCE_ORDER
                    else len(SOURCE_ORDER),
                    p.emitted_index,
                )
            )
        out.append(_combine(layout, constituents))
    return out


def _number_of(text: str | None) -> int:
    if not text:
        return 0
    tail = text.split(".")[-1]
    return int(tail) if tail.isdigit() else 0


# --------------------------------------------------------------------------
# D.0 — constructions and populations, once
# --------------------------------------------------------------------------


KIND_TITLES: dict[str, str] = {
    "gate_table": "the gate table",
    "node_calls_per_module": "node calls per module (headline shape 1)",
    "optimiser_path": "the optimiser's path (headline shape 2)",
    "node_calls_per_block": "node calls per block (headline shape 3)",
    "cost_per_call": "cost per call",
    "matched_accuracy": "matched accuracy",
    "fixed_point_distance": "fixed-point distance",
    "ownership_rung": "the ownership rung",
    "failure_taxonomy": "failure taxonomy",
    "per_sweep_overhead": "per-sweep overhead",
    "predicate_trial": "the predicate trial",
    "seed_set": "the seed set",
    "per_arm_success": "per-arm success",
    "per_arm_success_by_seed": "per-arm success by seed",
    "failure_table": "the failure table",
    "same_optimum": "same optimum (check 1)",
    "iteration_multiplier": "iteration multiplier (check 2)",
    "cost": "cost (check 4)",
    "attempt_summation": "the attempt-summation identity",
    "achieved_accuracy": "achieved accuracy at the accepted optimum",
    "lift_closed": "the lift closed (check 3)",
}


def _declaration_lines(
    kind_title: str,
    placed: Sequence[Placed],
    numbers: Mapping[str, str],
) -> list[str]:
    """One kind's declaration, printed once, with where its cells now print.

    *numbers* maps a layout name to the number of the table its cells were
    combined into.  Since one construction is now one table, a kind names one
    or two numbers here where it used to name a run of twelve.
    """
    variants: dict[str, list[Placed]] = {}
    for p in placed:
        declaration = p.table.get("declaration")
        key = json.dumps(declaration, sort_keys=True) if declaration else json.dumps(
            {"caption": p.table.get("caption")}
        )
        variants.setdefault(key, []).append(p)
    where: list[str] = []
    for name in dict.fromkeys(
        layout.name for p in placed for layout in p.layouts
    ):
        number = numbers.get(name)
        if number:
            where.append(f"Table {number}")
    lines = [
        f"**{kind_title}** (`{placed[0].kind}`, stage `{placed[0].stage}`; "
        f"{'; '.join(where) or 'not rendered'}; {len(placed)} stage table(s) "
        f"combined).",
        "",
    ]
    for key, group in variants.items():
        declaration = json.loads(key)
        if len(variants) > 1:
            applies = ", ".join(
                f"`{p.table.get('table')}`" for p in group
            )
            lines.append(f"*Applies to {applies}.*")
            lines.append("")
        if "caption" in declaration and "units" not in declaration:
            lines.append(str(declaration["caption"]))
            lines.append("")
            continue
        lines.append(f"- *Units:* {declaration['units']}.")
        lines.append(f"- *A row is* {declaration['row_is']}.")
        lines.append(f"- *A column is* {declaration['column_is']}.")
        lines.append(f"- *Construction:* {declaration['construction']}.")
        for clause in declaration.get("clauses") or []:
            lines.append(f"- {clause}.")
        if declaration.get("how_to_read"):
            lines.append(f"- *How to read:* {declaration['how_to_read']}.")
        lines.append("")
    return lines


def _populations_sentence(records: Mapping[str, Mapping[str, Any]]) -> str:
    parts: list[str] = []
    seen: set[str] = set()
    for stage in TALLY_STAGES:
        for source in records[stage].get("sources") or []:
            name = str(source.get("source"))
            if name in seen:
                continue
            seen.add(name)
            parts.append(
                f"`{name}` — {source.get('n_records')} record(s): {source.get('what')}"
            )
    if not parts:
        return "no tally source published a record."
    return "One population family, the sources named in every caption: " + "; ".join(parts) + "."


def _constructions(
    placed: Sequence[Placed],
    records: Mapping[str, Mapping[str, Any]],
    gate_block: Mapping[str, Any],
    numbers: Mapping[str, str],
) -> list[str]:
    lines = [
        "### D.0 Constructions and populations",
        "",
        "Every table of this appendix, of the companion file and of the "
        "headline tables in §4 is an instance of one **construction**, "
        "declared once here — its units, what a row and a column are, how the "
        "cells are built (the function in `harness/measurement/stats.py` whose "
        "docstring is the declaration), the clauses that bind its reading — "
        "and printed under no table. A table's own caption carries only what "
        "varies by table: what it shows, its population and denominator, the "
        "one thing not to infer. The declarations are rendered from the "
        "stages' records, so a construction that changes here changed in the "
        "code.",
        "",
        "**One construction, one table.** The tally computes a table per "
        "*(configuration, source)* because that is how it computes them; the "
        "renderer combines the tables of one construction into one grid under "
        "a declared layout (`plan_tables.LAYOUTS`), with the configurations "
        "and source regimes as row groups under a bold sub-heading row that "
        "names the group and states its own n — never a pooled one; what that n "
        "counts is in the table's caption, said once for the grid rather than "
        "once per group. Every "
        "cell of a combined grid is a cell one of those stage tables already "
        "held, rendered by that table's own columns; the stage tables it "
        "combines are named under the grid, and are the stable citation "
        "(a table number is a position, trap T17). An **empty** cell is a "
        "column the row's group does not have; `—` is a group's own missing "
        "value.",
        "",
        "**Populations.** " + _populations_sentence(records),
        "",
        f"**{KIND_TITLES['gate_table']}** (`gate_table`; Table {REPORT_PREFIX}.1; 1 table).",
        "",
        str(gate_block.get("declaration") or gate_block.get("caption") or ""),
        "",
    ]
    order = {layout.name: index for index, layout in enumerate(LAYOUTS)}
    by_kind: dict[tuple[str, str], list[Placed]] = {}
    for p in placed:
        if p.stage == UNRENDERED_STAGE or p.layout is None:
            continue
        by_kind.setdefault((p.stage, p.kind), []).append(p)
    keys = sorted(
        by_kind,
        key=lambda k: (
            min(
                order.get(p.layout.name, len(LAYOUTS))
                for p in by_kind[k]
                if p.layout is not None
            ),
            k[0],
            k[1],
        ),
    )
    for key in keys:
        title = KIND_TITLES.get(key[1], key[1])
        lines.extend(_declaration_lines(title, by_kind[key], numbers))
    return lines


# --------------------------------------------------------------------------
# the two documents
# --------------------------------------------------------------------------


def _captions_status(combined: Sequence[Combined]) -> dict[str, Any]:
    """How long the report's captions are, for the renderer's own report."""
    lengths = [
        len(_caption_text(c.table))
        for c in combined
        if c.where in ("report", "main")
    ]
    return {
        "n_report_tables": len(lengths),
        "caption_chars_max": max(lengths) if lengths else 0,
        "caption_chars_median": sorted(lengths)[len(lengths) // 2] if lengths else 0,
    }


def render(campaign: Campaign, records_dir: Path | None = None) -> dict[str, Any]:
    """The report's main-text headline tables, Appendix D and the companion
    file, as markdown, with the record of where every table came from and
    which number it got."""
    records_dir = Path(
        records_dir or (Path(campaign.runs_dir) / framework.GATES_SUBPATH)
    )
    marker = population_marker(campaign, records_dir)
    records: dict[str, dict[str, Any]] = {}
    freshness: list[str] = []
    for section in SECTIONS:
        records[section.stage] = stage_record(records_dir, section.stage)
        if section.records_read_required:
            freshness.append(
                assert_stage_read_what_is_there(records[section.stage], records_dir, section)
            )
    for stage in TALLY_STAGES:
        if not records[stage].get("tables"):
            raise PlanTablesError(
                f"stage {stage!r} emitted no table, so its part of the appendix "
                f"would be an empty section presented as a result.  A section "
                f"with no population is not a section (trap T11)."
            )
    placed = _place(records)
    combined = _all_combined(placed)
    by_name = {c.layout.name: c for c in combined}

    # --- numbering.  The main text continues §3's hand-written six; the
    #     appendix starts at D.1, the gate table; the companion at F.1.
    main_tables = [c for c in combined if c.where == "main"]
    for index, c in enumerate(main_tables):
        c.number = str(MAIN_TABLES_BEFORE + index + 1)
    report_tables = [
        by_name[name]
        for group in GROUPS
        for name in group.layouts
        if name in by_name
    ]
    undeclared = sorted(
        c.layout.name
        for c in combined
        if c.where == "report" and c not in report_tables
    )
    if undeclared:
        raise PlanTablesError(
            f"layout(s) {undeclared} render into the report but no group of "
            f"plan_tables.GROUPS holds them; the appendix's grouping is a "
            f"declaration, not a guess"
        )
    for index, c in enumerate(report_tables):
        c.number = f"{REPORT_PREFIX}.{index + 2}"  # D.1 is the gate table
    # **Every** table that leaves a per-seed column out gets its full version
    # in the companion, the main text's as well as the appendix's: a table
    # moved into §4 must not take its omitted columns out of the documents
    # altogether (task A86 (v3-tables-remainder), which moved two).
    omitting = [
        c
        for c in [*main_tables, *report_tables]
        if c.table.get("report_omits") and not c.layout.per_seed_columns_in
    ]
    full_versions = [
        Combined(
            layout=c.layout,
            constituents=c.constituents,
            table=c.table,
            where="companion",
        )
        for c in omitting
    ]
    companion_groups: list[tuple[Mapping[str, Any], list[Combined]]] = []
    for group in COMPANION_GROUPS:
        if group["layouts"] == "omitted":
            chosen = list(full_versions)
        else:
            chosen = [by_name[name] for name in group["layouts"] if name in by_name]
        companion_groups.append((group, chosen))
    m = 0
    for _group, chosen in companion_groups:
        for c in chosen:
            m += 1
            c.number = f"{COMPANION_PREFIX}.{m}"
    for omitted_from, full in zip(omitting, full_versions):
        omitted_from.full_version = full.number
    # A layout whose per-seed columns another layout's full version already
    # prints names that table rather than adding a second copy of the same
    # cells to the companion (``per_seed_columns_in``).
    numbers_of_full = {c.layout.name: c.full_version for c in omitting}
    for c in [*main_tables, *report_tables]:
        wanted = c.layout.per_seed_columns_in
        if not wanted:
            continue
        if wanted not in numbers_of_full:
            raise PlanTablesError(
                f"layout {c.layout.name!r} says its per-seed columns are "
                f"printed in full by {wanted!r}, which renders no full "
                f"version in the companion; a column left out of both "
                f"documents is a cell lost"
            )
        c.full_version = numbers_of_full[wanted]
    numbers_by_layout = {
        c.layout.name: c.number for c in combined if c.number
    }
    numbers_by_layout.update(
        {
            c.layout.name: c.number
            for c in main_tables
            if c.number
        }
    )

    # --- the main text's headline tables, one rendered block per marker pair
    main_blocks: dict[str, str] = {}
    for c in main_tables:
        omit = tuple(c.table.get("report_omits") or ())
        main_blocks[c.layout.name] = "\n".join(
            _table_block(
                c.table,
                c.number or "?",
                omit=omit,
                full_version=(
                    f"companion Table {c.full_version}" if omit and c.full_version else None
                ),
            )
        ).rstrip() + "\n"

    # --- Appendix D
    heading_note = (
        f"*(rendered by `harness/measurement/plan_tables.py` from the stage "
        f"records; the **{marker['population_family']}** population — "
        f"{marker['n_run_records']} run records at {_commits(marker)})*"
    )
    main_list = ", ".join(
        f"Table {c.number} ({c.layout.title})" for c in main_tables
    )
    lines: list[str] = [
        f"{SECTION_START} {heading_note}",
        "",
        "**What this appendix is.** Every table of the experiment's results, "
        "numbered `Table D.n` in the order printed, each an output of a "
        "measurement stage of `experiment_runner.py` read from its record "
        "under `runs/gates/<stage>/measurements.json`; no cell is typed by "
        "hand (protocol §15) and nothing here computes a number. **One "
        "construction, one table**: the tally's per-configuration and "
        "per-source tables of a construction are combined into one grid, the "
        "configurations and regimes as row groups (D.0 says how). §4 of the "
        "main text states the conclusions and points at these tables by "
        f"number; the **headline tables are in §4 itself** — {main_list} — "
        "and are not repeated here. **Only summarising tables are here** — "
        "per arm or arm pair and configuration. Every table with a row per "
        "run, seed, pair of runs or predicate evaluation, and the full "
        "versions of the tables whose per-seed columns are omitted here, are "
        f"in the companion file [`{COMPANION_NAME}`]({COMPANION_NAME}) "
        "(numbered `Table F.n`, generated by the same renderer and guarded by "
        "the same check), which this appendix points at once, here. The "
        "second implementation's recomputed copies are **not rendered as "
        "tables**: gate `recomputation`'s row of Table D.1 — tables compared, "
        "cells compared, cells mismatched — is that check, and the gate's "
        "record holds the cells. Table numbers are positional and change when "
        "a table is added; a cell is traced by the construction names printed "
        "under each grid, never by its number.",
        "",
        _marker_sentence(marker),
        "",
        CONVENTIONS,
        "",
    ]
    gate_block = records["gate_table"]
    lines.extend(_constructions(placed, records, gate_block, numbers_by_layout))
    for group in GROUPS:
        lines.append(f"### {group.number} {group.title}")
        lines.append("")
        lines.append(group.context)
        lines.append("")
        if not group.layouts:
            lines.extend(_gate_table_block(gate_block, f"{REPORT_PREFIX}.1"))
            continue
        for name in group.layouts:
            c = by_name.get(name)
            if c is None:
                continue
            omit = tuple(c.table.get("report_omits") or ())
            lines.extend(
                _table_block(
                    c.table,
                    c.number or "?",
                    omit=omit,
                    full_version=(
                        f"companion Table {c.full_version}"
                        if omit and c.full_version
                        else None
                    ),
                )
            )
        if group.number == "D.3":
            not_produced = records["tally_optimisation"].get("tables_not_produced") or []
            if not_produced:
                lines.append(
                    f"*Not produced by the stage, each with its reason: "
                    f"{_not_produced_text(not_produced)}*"
                )
                lines.append("")
    lines.append(SECTION_END)
    markdown = "\n".join(lines).rstrip() + "\n"

    # --- the companion file
    companion_lines: list[str] = [
        "# Results tables — the full result matrices",
        "",
        "> **Document status** — **GENERATED, never hand-edited.** Written whole "
        "by `harness/measurement/plan_tables.py` (`experiment_runner.py "
        "--plan-tables write`) from the same stage records as the report's "
        "Appendix D, and compared whole by `--plan-tables check`. It holds "
        "every table with a row per run, seed, pair of runs or predicate "
        "evaluation, and the full versions of the report's tables whose "
        "per-seed columns the report omits — **one construction, one table**, "
        "with the configurations and source regimes as row groups under a "
        "bold sub-heading row naming the group and stating its own n. The "
        "second "
        "implementation's recomputed copies are not rendered here: gate "
        "`recomputation`'s row of the report's Table D.1 is that check, and "
        "the gate's record holds the cells. Tables are numbered `Table F.n` "
        "in the order printed; the report cites them by that number and "
        "traces a cell by the construction names printed under each grid. "
        "Populations, constructions and conventions are the report's Appendix "
        "D.0's, not repeated here. Arm names are today's (`AR/A0/A1/A2`, "
        "`BR/B0/B1/B2`); the records carry the names of their day (trap T16).",
        "",
        f"*Rendered from the **{marker['population_family']}** population — "
        f"{marker['n_run_records']} run records at {_commits(marker)}.*",
        "",
    ]
    for group, chosen in companion_groups:
        companion_lines.append(f"## {group['number']} {group['title']}")
        companion_lines.append("")
        companion_lines.append(group["context"])
        companion_lines.append("")
        if not chosen:
            companion_lines.append("*No table of this group was emitted.*")
            companion_lines.append("")
        for c in chosen:
            companion_lines.extend(_table_block(c.table, c.number or "?"))
    not_produced = records[UNRENDERED_STAGE].get("tables_not_produced") or []
    companion_lines.append(
        f"*The second implementation emitted "
        f"{len(records[UNRENDERED_STAGE].get('tables') or [])} table(s); none "
        f"is rendered here. Whether they agree with the tally's, table by "
        f"table, row by row and cell by cell without tolerance, is gate "
        f"`recomputation`'s verdict — one row of the report's Table D.1 — and "
        f"the gate's own record holds every compared cell.*"
        + (
            f" *Not produced by that stage, each with its reason: "
            f"{_not_produced_text(not_produced)}*"
            if not_produced
            else ""
        )
    )
    companion_lines.append("")
    companion_markdown = "\n".join(companion_lines).rstrip() + "\n"

    numbers = {
        f"{p.stage}::{p.table['table']}": {
            "stage": p.stage,
            "kind": p.kind,
            "configuration": p.configuration,
            "source": p.source,
            "layout": p.layout.name if p.layout else None,
            "table": (
                numbers_by_layout.get(p.layout.name) if p.layout else None
            ),
        }
        for p in placed
    }
    census = {
        "n_main_text_tables": len(main_tables),
        "n_appendix_tables": 1 + len(report_tables),
        "n_companion_tables": m,
        "n_stage_tables_combined": sum(1 for p in placed if p.layout is not None),
        "n_stage_tables_not_rendered": sum(1 for p in placed if p.layout is None),
        "n_one_row_tables": sum(
            1
            for c in [*main_tables, *report_tables, *(t for _g, ts in companion_groups for t in ts)]
            if len(c.table.get("cells") or c.table.get("rows") or []) == 1
        ),
        "by_layout": [
            {
                "layout": c.layout.name,
                "where": c.where,
                "number": c.number,
                "mode": c.layout.mode,
                "n_stage_tables": len(c.constituents),
                "n_rows": len(c.table.get("cells") or c.table.get("rows") or []),
                "n_columns": len(c.table.get("columns") or []),
            }
            for c in [*main_tables, *report_tables, *(t for _g, ts in companion_groups for t in ts)]
        ],
    }
    return {
        "markdown": markdown,
        "companion_markdown": companion_markdown,
        "main_blocks": main_blocks,
        "marker": marker,
        "records_dir": str(records_dir),
        "stage_records_are_current": freshness,
        "n_tables": 1 + len(report_tables),
        "n_report_tables": 1 + len(report_tables),
        "n_main_tables": len(main_tables),
        "n_companion_tables": m,
        "n_cells": sum(
            len(p.table.get("rows") or []) * len(p.table.get("columns") or [])
            for p in placed
        ) + len(gate_block.get("rows") or []),
        "numbers": numbers,
        "census": census,
        "captions": _captions_status([*main_tables, *report_tables]),
        "sections": [
            {
                "stage": stage,
                "n_tables": (
                    len(records[stage].get("tables") or []) if stage != "gate_table" else 1
                ),
                "n_in_report": (
                    1 if stage == "gate_table"
                    else sum(
                        1
                        for c in report_tables
                        if any(p.stage == stage for p in c.constituents)
                    )
                ),
                "n_in_companion": sum(
                    1
                    for _g, ts in companion_groups
                    for c in ts
                    if any(p.stage == stage for p in c.constituents)
                ),
                "population": records[stage].get("population"),
                "runs_provenance": records[stage].get("runs_provenance"),
            }
            for stage in ("gate_table", *TALLY_STAGES, UNRENDERED_STAGE)
        ],
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


# --------------------------------------------------------------------------
# the documents on disk
# --------------------------------------------------------------------------


def plan_path(campaign: Campaign) -> Path:
    """The experiment report the appendix belongs to."""
    return Path(campaign.runs_dir).parent / "EXPERIMENT_REPORT.md"


def companion_path(campaign: Campaign) -> Path:
    """The companion file beside the report."""
    return Path(campaign.runs_dir).parent / COMPANION_NAME


def section_span(document: Path, lines: Sequence[str]) -> tuple[int, int]:
    """Where the rendered block starts and stops in *lines*, or a refusal.

    Both markers are matched on the whole line and both must occur exactly
    once: a renderer that writes into — or compares against — the wrong part
    of a shared document is worse than one that does nothing.  The span
    **includes** the end marker, which the renderer writes.
    """
    starts = [i for i, line in enumerate(lines) if line.startswith(SECTION_START)]
    ends = [i for i, line in enumerate(lines) if line.strip() == SECTION_END]
    if len(starts) != 1 or len(ends) != 1 or ends[0] <= starts[0]:
        raise PlanTablesError(
            f"{document} does not hold exactly one section starting "
            f"{SECTION_START!r} followed by one line {SECTION_END!r} "
            f"(found {len(starts)} and {len(ends)}).  The renderer replaces "
            f"that span and nothing else, and refuses rather than guessing "
            f"which part of a shared document it was asked to rewrite."
        )
    return starts[0], ends[0] + 1


def main_span(document: Path, lines: Sequence[str], name: str) -> tuple[int, int]:
    """Where one main-text table's rendered block sits, or a refusal.

    Both markers carry the layout's name and are matched on the whole line,
    and both must occur exactly once: §4's headline tables are rendered into
    a document a person also writes, and a renderer that writes into — or
    compares against — the wrong paragraph of it is worse than one that does
    nothing.  The span is the lines **between** the markers; the markers
    themselves stay where the author put them.
    """
    start_marker = MAIN_START.format(name=name)
    end_marker = MAIN_END.format(name=name)
    starts = [i for i, line in enumerate(lines) if line.strip() == start_marker]
    ends = [i for i, line in enumerate(lines) if line.strip() == end_marker]
    if len(starts) != 1 or len(ends) != 1 or ends[0] <= starts[0]:
        raise PlanTablesError(
            f"{document} does not hold exactly one line {start_marker!r} "
            f"followed by one line {end_marker!r} (found {len(starts)} and "
            f"{len(ends)}).  §4's headline table {name!r} is rendered between "
            f"them, and the renderer refuses rather than guessing which part "
            f"of a shared document it was asked to rewrite."
        )
    return starts[0] + 1, ends[0]


def _main_spans(
    document: Path, lines: Sequence[str], rendered: Mapping[str, Any]
) -> list[tuple[str, int, int]]:
    """Every main-text table's span, in the order they sit in the document."""
    spans = [
        (name, *main_span(document, lines, name))
        for name in (rendered.get("main_blocks") or {})
    ]
    return sorted(spans, key=lambda s: s[1])


#: A reference in the hand-written text: ``Table D.12``, ``Tables D.3–D.5``,
#: ``Tables F.1 and F.2``.
_REFERENCE = re.compile(
    r"\bTables?\s+([DF])\.(\d+)(?:\s*(?:–|-|—|and|,)\s*(?:[DF]\.)?(\d+))?"
)

#: A reference to a **main-text** table: ``Table 7``, ``Tables 8 and 9``.
#: It cannot match ``Table D.7``, which carries the prefix before the digits.
_MAIN_REFERENCE = re.compile(
    r"\bTables?\s+(\d+)(?:\s*(?:–|-|—|and|,)\s*(\d+))?"
)


#: The heading of the report's change log.  Its entries state the table set
#: of their own day, so a number in one is a **record**, not a citation
#: (trap T17's second addition, task A86 (v3-tables-remainder)): the change
#: log is held out of the citation sweep and, since task A88
#: (function-weighted-sweeps), out of the dangling-reference scan too — an
#: entry written when the main text had eighteen tables still says so after a
#: table left it, and that is what a change log is for.
CHANGE_LOG_HEADING = "## Appendix C — Change log"


def _outside_the_change_log(lines: Sequence[str]) -> tuple[list[str], int]:
    """*lines* with the change log's span removed, and how many lines it held.

    The span runs from the change log's heading to the next heading of its
    level; the line numbers reported for a dangling reference are the
    positions in *lines*, which the removal shifts, so the reference scan
    replaces the held-out lines by blanks rather than dropping them."""
    out = list(lines)
    held = 0
    inside = False
    for i, line in enumerate(lines):
        if line.startswith(CHANGE_LOG_HEADING):
            inside = True
        elif inside and line.startswith("## "):
            inside = False
        if inside:
            out[i] = ""
            held += 1
    return out, held


def _references(lines: Sequence[str], counts: Mapping[str, int]) -> dict[str, Any]:
    """Every ``Table n`` / ``Table D.n`` / ``Table F.n`` reference in *lines*,
    resolved against the numbers this rendering assigns.

    The main text's own numbers are resolved too: §3's six tables are
    hand-written and §4's headline tables are rendered, so a citation of
    ``Table 9`` after a headline table is dropped would otherwise point at
    nothing and say nothing about it.  The change log's lines are held out
    (:func:`_outside_the_change_log`): its numbers are records of their day.
    """
    found: dict[str, int] = {"D": 0, "F": 0, "": 0}
    dangling: list[str] = []
    lines, held_out = _outside_the_change_log(lines)
    for i, line in enumerate(lines):
        for match in _REFERENCE.finditer(line):
            prefix = match.group(1)
            numbers = [int(match.group(2))]
            if match.group(3):
                numbers.append(int(match.group(3)))
            for number in numbers:
                found[prefix] += 1
                if number < 1 or number > counts.get(prefix, 0):
                    dangling.append(f"line {i + 1}: Table {prefix}.{number}")
        for match in _MAIN_REFERENCE.finditer(line):
            numbers = [int(match.group(1))]
            if match.group(2):
                numbers.append(int(match.group(2)))
            for number in numbers:
                found[""] += 1
                if number < 1 or number > counts.get("", 0):
                    dangling.append(f"line {i + 1}: Table {number}")
    return {
        "n_references_to_the_main_text": found[""],
        "n_references_to_the_appendix": found["D"],
        "n_references_to_the_companion": found["F"],
        "n_change_log_lines_held_out": held_out,
        "n_dangling": len(dangling),
        "dangling": dangling[:20],
    }


def _diff(committed: list[str], fresh: list[str]) -> dict[str, Any]:
    # Blank lines at either end are the document's spacing around a rendered
    # block, not content: the renderer writes one either side of a main-text
    # table so the markers do not sit against the prose, and comparing them
    # would report a difference in whitespace as a difference in the table.
    for side in (committed, fresh):
        while side and not side[-1].strip():
            side.pop()
        while side and not side[0].strip():
            side.pop(0)
    # A **diff**, not a line-for-line comparison against position: one row
    # added shifts everything below it, and a positional comparator would
    # report seventeen hundred differences where there is one insertion —
    # a count over a population nobody would recognise (trap T11).
    matcher = difflib.SequenceMatcher(a=committed, b=fresh, autojunk=False)
    common = added = removed = 0
    hunks: list[dict[str, Any]] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            common += i2 - i1
            continue
        removed += i2 - i1
        added += j2 - j1
        hunks.append(
            {
                "how": tag,
                "at_line_in_document": i1 + 1,
                "n_lines_in_document": i2 - i1,
                "n_lines_from_the_records": j2 - j1,
                "in_document": [line[:160] for line in committed[i1:i2][:3]],
                "from_the_records": [line[:160] for line in fresh[j1:j2][:3]],
            }
        )
    return {
        "n_lines_in_document": len(committed),
        "n_lines_from_the_records": len(fresh),
        "n_lines_identical": common,
        "n_lines_only_in_the_document": removed,
        "n_lines_only_from_the_records": added,
        "n_hunks": len(hunks),
        "identical": not hunks,
        "hunks": hunks[:10],
        "n_hunks_not_listed": max(0, len(hunks) - 10),
    }


def _reference_counts(rendered: Mapping[str, Any]) -> dict[str, int]:
    return {
        "": MAIN_TABLES_BEFORE + int(rendered["n_main_tables"]),
        "D": int(rendered["n_report_tables"]),
        "F": int(rendered["n_companion_tables"]),
    }


def check(
    campaign: Campaign, records_dir: Path | None = None, *, path: Path | None = None
) -> dict[str, Any]:
    """Render every block and compare it with what is committed, writing nothing.

    The same rendering as :func:`write`, and **no write**: what comes back is
    whether the committed §4 headline tables, Appendix D and companion file
    are the ones these records produce, the lines where they are not, and
    whether every table reference in the hand-written text resolves.  It
    exists so that a task whose job is the records can report the state of a
    shared document without editing it, and so that "the report is up to
    date" is a comparison rather than a claim.
    """
    document = Path(path) if path is not None else plan_path(campaign)
    companion = (
        document.parent / COMPANION_NAME if path is not None else companion_path(campaign)
    )
    lines = document.read_text().splitlines()
    start, end = section_span(document, lines)
    rendered = render(campaign, records_dir)
    spans = _main_spans(document, lines, rendered)
    compared_main: list[dict[str, Any]] = []
    hand_written = list(lines[:start]) + list(lines[end:])
    for name, first, last in spans:
        block = _diff(
            list(lines[first:last]),
            rendered["main_blocks"][name].splitlines(),
        )
        block["table"] = name
        block["what_this_is"] = (
            f"§4's headline table {name!r} in the document against the one "
            f"these stage records produce now"
        )
        compared_main.append(block)
    # the hand-written text is everything outside the rendered blocks
    rendered_lines: set[int] = set(range(start, end))
    for _name, first, last in spans:
        rendered_lines.update(range(first, last))
    hand_written = [line for i, line in enumerate(lines) if i not in rendered_lines]
    compared = _diff(lines[start:end], rendered["markdown"].splitlines())
    compared["what_this_is"] = (
        "the document's Appendix D against the appendix these stage records "
        "produce now, as a diff, with nothing written"
    )
    if companion.exists():
        compared_companion = _diff(
            companion.read_text().splitlines(),
            rendered["companion_markdown"].splitlines(),
        )
    else:
        fresh = rendered["companion_markdown"].splitlines()
        compared_companion = {
            "identical": False,
            "missing": True,
            "n_hunks": 1,
            "hunks": [],
            "n_hunks_not_listed": 0,
            "n_lines_in_document": 0,
            "n_lines_from_the_records": len(fresh),
            "n_lines_identical": 0,
            "n_lines_only_in_the_document": 0,
            "n_lines_only_from_the_records": len(fresh),
        }
    compared_companion["what_this_is"] = (
        f"the committed {COMPANION_NAME} against the one these stage records "
        f"produce now, whole, as a diff"
    )
    references = _references(hand_written, _reference_counts(rendered))
    rendered.update(
        {
            "document": str(document),
            "companion": str(companion),
            "compared": compared,
            "compared_main": compared_main,
            "compared_companion": compared_companion,
            "references": references,
            "identical": bool(
                compared["identical"]
                and compared_companion["identical"]
                and all(block["identical"] for block in compared_main)
                and references["n_dangling"] == 0
            ),
        }
    )
    return rendered


def write(
    campaign: Campaign, records_dir: Path | None = None, *, path: Path | None = None
) -> dict[str, Any]:
    """Replace §4's headline tables and Appendix D in the report, and the
    companion file, in place.

    Only the rendered blocks are touched in the report: each is found by its
    own pair of markers, and a document where a marker has moved or been
    reworded is a **refusal**, never a best-effort edit.  The companion file
    is the renderer's alone and is written whole.  The report's blocks are
    replaced from the bottom up so that one replacement does not move the
    next one's line numbers.
    """
    document = Path(path) if path is not None else plan_path(campaign)
    companion = (
        document.parent / COMPANION_NAME if path is not None else companion_path(campaign)
    )
    text = document.read_text()
    lines = text.splitlines()
    start, end = section_span(document, lines)
    rendered = render(campaign, records_dir)
    spans = _main_spans(document, lines, rendered)
    body = rendered["markdown"].splitlines()
    replacements: list[tuple[int, int, list[str]]] = [(start, end, body)]
    for name, first, last in spans:
        replacements.append(
            (first, last, ["", *rendered["main_blocks"][name].splitlines(), ""])
        )
    replaced = list(lines)
    n_main_lines = 0
    for first, last, block in sorted(replacements, key=lambda r: r[0], reverse=True):
        replaced[first:last] = block
        if (first, last) != (start, end):
            n_main_lines += len(block)
    document.write_text("\n".join(replaced).rstrip() + "\n")
    companion.write_text(rendered["companion_markdown"])
    rendered["document"] = str(document)
    rendered["companion"] = str(companion)
    rendered["n_lines_replaced"] = end - start
    rendered["n_lines_written"] = len(body)
    rendered["n_main_lines_written"] = n_main_lines
    rendered["n_companion_lines_written"] = len(rendered["companion_markdown"].splitlines())
    written = document.read_text().splitlines()
    new_start, new_end = section_span(document, written)
    new_spans = _main_spans(document, written, rendered)
    rendered_lines = set(range(new_start, new_end))
    for _name, first, last in new_spans:
        rendered_lines.update(range(first, last))
    rendered["references"] = _references(
        [line for i, line in enumerate(written) if i not in rendered_lines],
        _reference_counts(rendered),
    )
    return rendered


def report(result: Mapping[str, Any]) -> None:
    """What was rendered, and over what, on the terminal."""
    marker = result["marker"]
    print(f"  records   : {result['records_dir']}")
    for sentence in result.get("stage_records_are_current") or ():
        print(f"  freshness : {sentence}")
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
            f"  {block['stage']:<20} {block['n_tables']:>3} table(s): "
            f"{block['n_in_report']} in the report, {block['n_in_companion']} "
            f"in the companion file"
        )
        provenance = block.get("runs_provenance") or {}
        if provenance:
            print(
                f"            runs read: {provenance.get('n_records')} "
                f"record(s) at {provenance.get('heads')}"
            )
    captions = result.get("captions") or {}
    census = result.get("census") or {}
    print(
        f"  {result.get('n_main_tables')} headline table(s) in §4, "
        f"{result['n_report_tables']} table(s) in Appendix D, "
        f"{result['n_companion_tables']} in {COMPANION_NAME}, "
        f"{result['n_cells']} cell(s); report captions up to "
        f"{captions.get('caption_chars_max')} characters (median "
        f"{captions.get('caption_chars_median')})"
    )
    if census:
        print(
            f"  census    : {census['n_stage_tables_combined']} stage table(s) "
            f"combined into {census['n_main_text_tables']} + "
            f"{census['n_appendix_tables']} + {census['n_companion_tables']} "
            f"rendered table(s); {census['n_one_row_tables']} with one row; "
            f"{census['n_stage_tables_not_rendered']} stage table(s) rendered "
            f"nowhere (the second implementation's)"
        )
        for row in census["by_layout"]:
            print(
                f"    {str(row['number']):>5}  {row['layout']:<34} "
                f"{row['where']:<9} {row['mode']:<6} "
                f"{row['n_stage_tables']:>3} stage table(s) → "
                f"{row['n_rows']:>4} row(s) × {row['n_columns']:>2} column(s)"
            )
    for block in result.get("compared_main") or ():
        print(
            f"  compared  : §4 Table {block['table']} — "
            f"{block['n_lines_in_document']} line(s) in the document against "
            f"{block['n_lines_from_the_records']} from the records, in "
            f"{block['n_hunks']} hunk(s); "
            + ("IDENTICAL" if block["identical"] else "NOT IDENTICAL")
        )
    for name, compared in (
        ("Appendix D", result.get("compared")),
        (COMPANION_NAME, result.get("compared_companion")),
    ):
        if not compared:
            continue
        if compared.get("missing"):
            print(f"  compared  : {name} — the committed file does not exist; NOT IDENTICAL")
            continue
        print(
            f"  compared  : {name} — "
            f"{compared['n_lines_in_document']} line(s) in the document "
            f"against {compared['n_lines_from_the_records']} from the "
            f"records: {compared['n_lines_identical']} identical, "
            f"{compared['n_lines_only_in_the_document']} only in the "
            f"document, {compared['n_lines_only_from_the_records']} only from "
            f"the records, in {compared['n_hunks']} hunk(s); "
            + ("IDENTICAL" if compared["identical"] else "NOT IDENTICAL")
        )
        for hunk in compared["hunks"]:
            print(
                f"    {hunk['how']} at line {hunk['at_line_in_document']}: "
                f"{hunk['n_lines_in_document']} line(s) in the document, "
                f"{hunk['n_lines_from_the_records']} from the records"
            )
            for line in hunk["in_document"]:
                print(f"      - {line[:120]}")
            for line in hunk["from_the_records"]:
                print(f"      + {line[:120]}")
        if compared["n_hunks_not_listed"]:
            print(
                f"    and {compared['n_hunks_not_listed']} further hunk(s) "
                f"not listed"
            )
    references = result.get("references")
    if references:
        print(
            f"  references: "
            f"{references.get('n_references_to_the_main_text', 0)} to §3/§4's "
            f"numbered tables, "
            f"{references['n_references_to_the_appendix']} to "
            f"Appendix D and {references['n_references_to_the_companion']} to "
            f"the companion file in the hand-written text "
            f"(the change log's {references.get('n_change_log_lines_held_out', 0)} "
            f"line(s) held out: its numbers are records of their day); "
            f"{references['n_dangling']} dangling"
        )
        for line in references["dangling"]:
            print(f"    DANGLING {line}")
    if result.get("compared"):
        print("  nothing was written: this is the comparison mode")
    elif result.get("document"):
        print(
            f"  written   : {result['document']} — {result['n_lines_written']} "
            f"line(s) replacing {result['n_lines_replaced']}; "
            f"{result['companion']} — {result['n_companion_lines_written']} line(s), whole"
        )
