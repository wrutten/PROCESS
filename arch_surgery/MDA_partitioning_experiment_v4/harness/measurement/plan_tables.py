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
recomputed copies by task **A83 (headline-tables-in-text)**.
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
    # ---------------- the main text: the three headline shapes -------------
    Layout(
        name="node_calls_per_block",
        title="node calls per block",
        stage="tally_evaluation",
        kinds=("node_calls_per_block",),
        sources=("campaign_displaced",),
        where="main",
        mode="single",
        caption="",
        why=(
            "Headline shape 3 on the acceptance regime, in §4.2 where RQ1 is "
            "answered.  The tally emits it already stacked over the "
            "configurations, so there is nothing to combine: the layout's "
            "work is to place it in the main text and keep it out of the "
            "appendix, where it would be the same grid twice."
        ),
    ),
    Layout(
        name="node_calls_per_module",
        title="node calls per module",
        stage="tally_optimisation",
        kinds=("node_calls_per_module",),
        where="main",
        mode="stack",
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
            "Headline shape 1, in §4.3 where RQ2 is answered.  Three tables "
            "of six or seven rows, one per configuration, differing only in "
            "the population — the case the *one construction, one table* rule "
            "is written for.  Stacked, because the statistic is sixteen "
            "columns wide and a configuration column group would be forty-"
            "eight."
        ),
    ),
    Layout(
        name="optimiser_path",
        title="the optimiser's path",
        stage="tally_optimisation",
        kinds=("optimiser_path",),
        where="main",
        mode="single",
        caption="",
        why=(
            "Headline shape 2, in §4.3 beside shape 1: R = ρ × ε read down "
            "each configuration's four rows.  The tally emits it over the "
            "configurations already."
        ),
    ),
    # ---------------- Appendix D: the evaluation phase ---------------------
    Layout(
        name="node_calls_per_block_other_regimes",
        title="node calls per block, the other three regimes",
        stage="tally_evaluation",
        kinds=("node_calls_per_block",),
        sources=("campaign_entry_references", *_STENCILS),
        where="report",
        mode="stack",
        caption=(
            "Mean node calls per evaluation by block and arm, configurations "
            "stacked, in the three regimes the main text's table does not "
            "show: the entry reference, and the forward and backward stencil "
            "points. The ratio is `A2` pooled against the configuration's "
            "declared reference (the *reference* column: `A1` on a pulsed "
            "configuration, `A0` on `st_regression`). The once-per-run row is "
            "the deferred nodes; prime calls are not model nodes and are in "
            "no row. The entry reference carries one `A0` run per "
            "configuration and so no pair and no ratio."
        ),
        why=(
            "The displaced regime is the main text's Table 7; the other three "
            "confirm it and belong in the appendix.  Stacked by source rather "
            "than folded into ratio columns per regime: a ratio-column "
            "rendering would have dropped the four per-arm mean columns and "
            "the pair count for those regimes out of the report altogether, "
            "which is a loss of cells, not a change of layout."
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
        name="fixed_point_distance",
        title="fixed-point distance",
        stage="tally_evaluation",
        kinds=("fixed_point_distance",),
        where="report",
        mode="stack",
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
    Layout(
        name="per_arm_success",
        title="per-arm success, the seed set and the failure taxonomy",
        stage="tally_optimisation",
        kinds=("per_arm_success", "failure_taxonomy", "seed_set"),
        where="report",
        mode="merge",
        join="arm",
        caption=(
            "Reliability read both ways, configurations stacked. Per arm, of "
            "the 25 starts offered: accepted optima (status ok and the output "
            "file's `ifail == 1`), the other starts by outcome class, and the "
            "starts lost that another arm accepted. Beside them, per "
            "configuration and repeated down its arm rows: the **seed set** — "
            "the seeds on which *every* arm reached an accepted optimum, "
            "which every other optimisation table's n is — with the "
            "configuration-invalid seeds and the retried seeds per arm. "
            "Reported, not accepted on (D29, 2026-09-15)."
        ),
        why=(
            "Three constructions × three configurations = nine tables, three "
            "of them a single row, all about one question: which starts each "
            "arm accepted, and which seeds survive into every other table's "
            "denominator.  Per-arm success is the host; the failure taxonomy "
            "aligns on the arm; the seed set has no arm and is broadcast "
            "across the configuration's rows, which is what *stated once per "
            "configuration* means here."
        ),
    ),
    Layout(
        name="same_optimum",
        title="same optimum (check 1)",
        stage="tally_optimisation",
        kinds=("same_optimum",),
        where="report",
        mode="stack",
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
        name="iteration_multiplier",
        title="iteration multiplier (check 2)",
        stage="tally_optimisation",
        kinds=("iteration_multiplier",),
        where="report",
        mode="stack",
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
        name="achieved_accuracy",
        title="achieved accuracy at the accepted optimum",
        stage="tally_optimisation",
        kinds=("achieved_accuracy",),
        where="report",
        mode="stack",
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
        caption=(
            "Check 3 on the two pulsed configurations: constraint 93's "
            "residual at every accepted optimum of the arms that carry the "
            "lifted design variable, absolute and relative, and whether the "
            "constraint sits in the equality block. `st_regression` has no "
            "burn-time coupling and no lift."
        ),
        why="Two tables of two rows.",
    ),
    # ---------------- the companion file ------------------------------------
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
            "row groups under a bold sub-heading row that names each group's "
            "own population and n. The acceptance regime's headline table — "
            "node calls per block on the displaced entries — is Table 7 in "
            "§4.2 and is not repeated here. Absolute cost cells are per-run "
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
            "node_calls_per_block_other_regimes",
            "reference_entries",
            "cost_per_call",
            "matched_accuracy",
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
            "table states per configuration and every other table repeats as "
            "its n; the seeds outside it are the failure table's, in the "
            "companion file, so the filter cannot flatter an arm that fails "
            "on expensive seeds. Every ratio is against the flat control "
            "`B0`; `BR → B0` is published beside as the yardstick, never "
            "accepted on. Cost is solve-phase model-node executions summed "
            "over the optimiser's attempts (the output path and the exit "
            "audit excluded alike in every arm), published with and without "
            "the seeds on which either side retried; the attempt-summation "
            "identity that licenses this is printed per run in the companion "
            "file. **One construction, one table**: the three configurations "
            "are row groups of each table, under a sub-heading row stating "
            "the group's own n; `B1` is inactive on `st_regression`, so its "
            "rows are absent from that group and its columns empty there. The "
            "phase's two headline tables — node calls per module and the "
            "optimiser's path — are Tables 8 and 9 in §4.3 and are not "
            "repeated here."
        ),
        layouts=(
            "per_arm_success",
            "same_optimum",
            "iteration_multiplier",
            "cost",
            "achieved_accuracy",
            "lift_closed",
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
        "layouts": ("per_sweep_overhead_evaluation", "predicate_trial"),
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
    #: The layout that renders it, or ``None`` for a stage rendered nowhere.
    layout: Layout | None = None


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


def _layout_for(placed: Placed) -> Layout | None:
    """The one layout that renders *placed*, or a refusal naming the choice.

    Two layouts claiming one table, or none claiming it, are both
    declarations that have fallen behind the tally: the appendix's shape is a
    declaration and is never guessed at.
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
        raise PlanTablesError(
            f"table {placed.table.get('table')!r} is claimed by "
            f"{[m.name for m in matches]}; a table belongs to exactly one "
            f"layout, and two claiming it is a declaration that has fallen "
            f"behind the tally"
        )
    return matches[0] if matches else None


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
            row.layout = _layout_for(row)
            if row.layout is None:
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
    return columns


def _group_label(placed: Placed) -> str:
    """The bold sub-heading row over one constituent's rows.

    It carries what the reader needs to know the rows are over — the
    configuration, the source, and **this group's own n with what it counts**
    — because a combined table has no single denominator and a pooled one
    would be a count over a population nobody asked for (trap T11).
    """
    where = " · ".join(
        part for part in (placed.configuration, placed.source) if part
    )
    return (
        f"**{where or placed.construction} — n = {placed.table.get('denominator')} "
        f"({placed.table.get('denominator_is')})**"
    )


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
    grid: list[list[str]] = []
    for placed in constituents:
        grid.append([_group_label(placed)] + [""] * (len(keys) - 1))
        for row in _cells_by_key(placed, overrides):
            grid.append([row.get(key, "") for key in keys])
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
    join = layout.join or ""
    join_key = next((key for key in keys if key[0] == join), None)
    grid: list[list[str]] = []
    groups: dict[str, list[Placed]] = {}
    for placed in constituents:
        groups.setdefault(str(placed.configuration), []).append(placed)
    for configuration, members in groups.items():
        members = sorted(
            members, key=lambda p: layout.kinds.index(p.kind)
        )
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
        grid.append(
            [
                f"**{configuration} — {len(members)} construction(s): "
                + "; ".join(f"`{p.construction}` n = {p.table.get('denominator')}" for p in members)
                + "**"
            ]
            + [""] * (len(keys) - 1)
        )
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
                    out.setdefault(key, cell)
            grid.append([out.get(key, "") for key in keys])
    return grid


def _combine(layout: Layout, constituents: Sequence[Placed]) -> Combined:
    """One construction's tables as one table, under the layout's mode."""
    constituents = list(constituents)
    if layout.mode == "single" or len(constituents) == 1:
        # Nothing to combine: the table is rendered as the stage emitted it,
        # with its own caption and its own denominator.
        return Combined(
            layout=layout,
            constituents=constituents,
            table=constituents[0].table,
            where=layout.where,
        )
    overrides = dict(layout.headings)
    columns = _union_columns(constituents, overrides, layout)
    if layout.mode == "stack":
        grid = _stack(constituents, columns, overrides)
    elif layout.mode == "merge":
        grid = _merge(constituents, columns, overrides, layout)
    else:
        raise PlanTablesError(f"layout {layout.name!r} has no mode {layout.mode!r}")
    omits = sorted({
        key
        for placed in constituents
        for key in (placed.table.get("report_omits") or [])
    })
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
        "denominator_is": (
            "row group(s) of this table, each over its own population with "
            "its own n in its sub-heading row; never pooled"
        ),
        "acceptance": any(p.table.get("acceptance") for p in constituents),
        "audit_positions": audit_positions,
        "columns": columns,
        "rows": [],
        "cells": grid,
        "combines": [p.table.get("table") for p in constituents],
    }
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
        constituents = [p for p in placed if p.layout is layout]
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
        p.layout.name for p in placed if p.layout is not None
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
        "states each group's own population and n — never a pooled one. Every "
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
    full_versions = [
        Combined(
            layout=c.layout,
            constituents=c.constituents,
            table=c.table,
            where="companion",
        )
        for c in report_tables
        if c.table.get("report_omits")
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
    for report_table, full in zip(
        [c for c in report_tables if c.table.get("report_omits")], full_versions
    ):
        report_table.full_version = full.number
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
        "bold sub-heading row stating each group's own n. The second "
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


def _references(lines: Sequence[str], counts: Mapping[str, int]) -> dict[str, Any]:
    """Every ``Table n`` / ``Table D.n`` / ``Table F.n`` reference in *lines*,
    resolved against the numbers this rendering assigns.

    The main text's own numbers are resolved too: §3's six tables are
    hand-written and §4's headline tables are rendered, so a citation of
    ``Table 9`` after a headline table is dropped would otherwise point at
    nothing and say nothing about it.
    """
    found: dict[str, int] = {"D": 0, "F": 0, "": 0}
    dangling: list[str] = []
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
            f"the companion file in the hand-written text; "
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
