# A83 (headline-tables-in-text) — the headline tables back in §4, and one construction, one table

> **Document status** — **OPEN task report.** Task **A83 (headline-tables-in-text)**, branch
> `A83-headline-tables-in-text` off `architecture_surgery` at **`c45cac1c`**. Base commit of the
> experiment: `c0ae5b28` (frozen). Written 2026-09-15. Archive to
> `docs/reports/deprecated/` at merge; folder position records lifecycle, not validity (trap T3).
> **Zero PROCESS runs.** `EXECUTION_APPROVED` untouched. No number in the report changed: this is a
> rendering task, and the proof is §4 below.

## 1. The verdict

The user, on reading the report after A82: *"The previous task moved ALL tables to the appendix.
Please keep the headline tables, with their discussion, in the main text of the v4 report."* and
*"[the tables] seem expanded over a bunch of different tables with one row, which makes no sense at
all. Critically reassess the report formatting yourself, and improve the reporting."*

Both are done, and both are done **in the renderer**, as declarations, not by hand.

**The census** (`report_cells_preserved.py --base c45cac1c`, committed, run at `8f07328a`; and
`experiment_runner.py --plan-tables check`):

| | at `c45cac1c` | now |
|---|---|---|
| rendered tables in the report's **§4** | **0** | **3** (Tables 7, 8, 9) |
| tables in **Appendix D** | **83** (the gate table + 82) | **14** (the gate table + 13) |
| grids in `EXPERIMENT_REPORT.md` as a whole | 83 | 17 |
| tables in the **companion** `RESULTS_TABLES_FULL.md` | **162** | **12** |
| **tables with a single row** (both documents) | **48** (15 of them in the report) | **0** |
| stage tables the two tally stages emit | 107 | 107 (unchanged) |
| stage tables of the second implementation, rendered | 107 | **0** |

The three tables the user asked to see in the main text, as rendered:

- **§4.2, Table 7** — *node calls per block*, the displaced entries, configurations stacked,
  `AR / A0 / A1 / A2` and `A2 / reference` pooled (headline shape 3); the RQ1 paragraph follows it.
- **§4.3, Table 8** — *node calls per module*, the **three configurations stacked in one grid**
  (headline shape 1), `BR / B0 / B1 / B2` mean `[min, max]`, `B2/B0` pooled, the per-run median with
  its bracket and `runs B2 > B0`; the RQ2 paragraph follows it.
- **§4.3, Table 9** — *the optimiser's path* over the configurations (headline shape 2): iterations,
  ε, ρ and R = ρ × ε; its paragraph follows it.

They are numbered in the main sequence after §3's six hand-written tables, are rendered between
explicit markers that `--plan-tables write | check` guards, and do **not** also appear in Appendix D.

## 2. The layout table — kind → layout → host

`plan_tables.LAYOUTS` is the declaration. Each entry carries a `why` docstring; the table below is
what the renderer printed (`--plan-tables check`, census block).

| # | layout | mode | where | stage tables → | shape |
|---|---|---|---|---|---|
| `Table 7` | `node_calls_per_block` (displaced) | single | **§4.2** | 1 | 17 × 11 |
| `Table 8` | `node_calls_per_module` | stack | **§4.3** | 3 | 23 × 16 |
| `Table 9` | `optimiser_path` | single | **§4.3** | 1 | 12 × 12 |
| `D.1` | the gate table | — | D.1 | 1 | unchanged |
| `D.2` | `node_calls_per_block_other_regimes` | stack | D.2 | 3 | 54 × 11 |
| `D.3` | `reference_entries` | **merge** (`arm`) | D.2 | **9** | 9 × 26 |
| `D.4` | `cost_per_call` | stack | D.2 | 9 | 42 × 11 |
| `D.5` | `matched_accuracy` | stack | D.2 | 9 | 75 × 12 |
| `D.6` | `fixed_point_distance` | stack | D.2 | 9 | 39 × 15 |
| `D.7` | `ownership_rung` | stack | D.2 | 6 | 12 × 8 |
| `D.8` | `failure_taxonomy_evaluation` | stack | D.2 | 9 | 42 × 5 |
| `D.9` | `per_arm_success` (+ the seed set + the optimisation failure taxonomy) | **merge** (`arm`) | D.3 | **9** | 14 × 23 |
| `D.10` | `same_optimum` | stack | D.3 | 3 | 11 × 10 |
| `D.11` | `iteration_multiplier` | stack | D.3 | 3 | 13 × 12 |
| `D.12` | `cost` | stack | D.3 | 3 | 14 × 13 |
| `D.13` | `achieved_accuracy` | stack | D.3 | 3 | 25 × 12 |
| `D.14` | `lift_closed` | stack | D.3 | 2 | 6 × 6 |
| `F.1` | `per_sweep_overhead_evaluation` | stack | companion | 12 | 686 × 12 |
| `F.2` | `predicate_trial` | single | companion | 1 | 12 × 11 |
| `F.3` | `per_arm_success_by_seed` | stack | companion | 3 | 78 × 8 |
| `F.4` | `failure_table` | stack | companion | 3 | 23 × 8 |
| `F.5` | `attempt_summation` | stack | companion | 3 | 278 × 11 |
| `F.6` | `per_sweep_overhead_optimisation` | stack | companion | 3 | 250 × 14 |
| `F.7`–`F.12` | the full versions of `D.3`, `D.4`, `D.7`, `D.9`, `D.11`, `D.13` | as above | companion | 39 | as above |
| — | the second implementation's tables | **not rendered** | nowhere | 107 | — |

**The three modes.**

- **`stack`** — the constituents one after another in one grid, each under a bold sub-heading row
  `**<configuration> · <source> — n = <its own n> (<what it counts>)**`. Columns are the union of the
  constituents' columns keyed by column key; an **empty** cell is a column the row's group does not
  have, `—` is a group's own missing value. This is where the source regime becomes a *row key*.
- **`merge`** — the constituents of one configuration aligned on a join column. A constituent with no
  join column (the seed set, whose row is per configuration and not per arm), or with one row where
  the group has several (the entry reference's cost, against its two ruler rows), is **broadcast**
  across the group's rows. That is what *stated once per configuration* means in a table whose rows
  are arms.
- **`single`** — a construction the tally already emits whole, rendered as it is with its own caption.

**Heading refusal.** A layout combining tables of one construction whose columns disagree on a
heading (`vs A0 pooled` against `vs A1 pooled`) is **refused** unless the layout declares the combined
heading. Three constructions needed one; they are listed in §4 below. A heading taken from whichever
constituent happened to be first would have said `vs A1 pooled` over a column whose `st_regression`
rows are against `A0`.

**Nothing in the tally moved.** The emission (`tally_evaluation.py`, `tally_optimisation.py`,
`tables.py`), the stage records and the gates over cells (`recomputation`, `tally_contracts`) are
untouched. The renderer reads each table's *configuration* and *source* from the name the stage
already gives it (`<construction> — <configuration> — <source>`), so no record field was added.

## 3. What §4 now reads like

§4.2 opens with Table 7 — the block table on the acceptance regime, the three configurations stacked
— and the RQ1 paragraph reads it line by line beside it: `A2` at 0.5625 / 0.5772 / 0.5016 of its
reference, the once-per-run row at 0, the pulse node at 0.1953 / 0.2033, M2 at ~1. §4.3 states the
population, then puts Table 8 (node calls per module, the three configurations in one grid) above the
RQ2 paragraph and Table 9 (the optimiser's path) above the paragraph that decomposes R = ρ × ε. Every
other sentence of §4 still points at Appendix D, by a number that now names one table per
construction rather than one of twelve: `Table D.4` for cost per call, `Table D.5` for matched
accuracy, `Table D.9` for reliability. The prose itself is A79's and A80's, unchanged except for the
citations.

## 4. Verification

Worktree `/home/wrutten/projects/PROCESS_surgery_worktrees/A83-headline-tables-in-text`, everything
committed, nothing running, seeded with the A82 records tree. **Zero PROCESS runs.**

### 4.1 The presses

| step | result |
|---|---|
| `--measure all --resume` | every stage re-made from the same 949 campaign records at `57dc0c14`; 107 tally tables; 0 PROCESS runs |
| `--plan-tables write` | §4's three blocks + Appendix D (793 lines) + the companion (1 567 lines) |
| `--plan-tables check` | **IDENTICAL** for all five blocks: §4 Table 7 (23/23 lines, 0 hunks), Table 8 (31/31, 0), Table 9 (18/18, 0), Appendix D (793 = 793 identical, 0 hunks), `RESULTS_TABLES_FULL.md` (1 567 = 1 567 identical, 0 hunks); references **31 + 63 + 20 = 114 resolved, 0 dangling** |
| `--gate recomputation --resume` | **PASS**, 15 122 compared / 0 mismatched over 107 tables — the same pair as at the A82 merge |
| `--gate tally_contracts --resume` | **PASS**, 577 (321 + 256) / 0, 11/11 teeth |
| `--gate run_kind_separation --resume` | **PASS**, 3 000 / 0, 9/9 teeth |
| `--gate self_containment --resume` | **PASS**, 52 / 0, 1/1 tooth |
| `--measure gate_table --resume` | **30 PASS, 0 FAIL, 0 not run; 161 of 161 teeth tripped** |
| re-render after the gate table | `--plan-tables write` then `check`: IDENTICAL, 0 dangling; working tree clean |
| `--selfcheck` | **PASS** (all checks; `stage provenance` 17 compared / 0, its four teeth tripped through the renderer) |
| stamp survey before / after (`run_stamp_survey.py`) | **1 102 records, byte-identical listing, 0 re-made, 0 new** |

**Does `tally_contracts` read rendered captions?** No. It reads the `caption`, `denominator` and
`denominator_is` fields of each **stage record** table (`gate_tally.py`, the loop over `emitted`),
never the rendered documents, and it reproduces 256 reference cells from the reproduction reference.
Combining is downstream of everything it reads, which is why its counts are unchanged and it still
PASSes: 577 (321 table checks + 256 cells) / 0, exactly the pair the committed Table D.1 carried at
`c45cac1c`.

### 4.2 The cell-preservation check

`report_cells_preserved.py --base c45cac1c` (committed at `55da17b4`, census added at `8f07328a`).
It parses the two documents at `c45cac1c` and the two in the tree, keys every cell by
**(construction, configuration, source, row, column)** — read from the construction name printed
under each grid, **never by table number** (trap T17) — and requires **every row of every old grid to
appear whole inside a row of the grid that now names it as one of the tables it combines**. Whole,
because a per-column multiset of values would not catch a cell that moved to the wrong row.

```
grids     : 245 before (of which 107 the second implementation's), 29 now
census    : the report's grids 83 → 17, the companion's 162 → 12;
            grids with a single row 48 → 0 (15 → 0 of them in the report)
compared  : 3444 row(s), 38451 cell(s), of which 29262 carry a number
preserved : 1781 row(s), 19048 cell(s), of which 14458 carry a number —
            each found whole inside a row of the table that now combines it
missing   : 1663 row(s), of which 0 are not the second implementation's
differing : 0 row(s)
VERDICT   : every cell preserved; 1663 row(s) withdrawn by construction
```

**0 missing that are not expected, 0 differing, of 3 444 rows and 38 451 cells (29 262 numeric).**

**The rows rendered fewer times than before**, by kind — all of them the second implementation's
copies, withdrawn by the decision in §5(a):

| rows | construction (the second implementation's copy of) |
|---|---|
| 921 | per-sweep overhead |
| 275 | the attempt summation identity |
| 75 | per-arm success by seed |
| 72 | matched accuracy |
| 68 | node calls per block |
| 47 | failure taxonomy |
| 36 | cost per call |
| 30 | fixed-point distance |
| 22 | achieved accuracy at the accepted optimum |
| 20 | node calls per module; 20 the failure table |
| 12 | the optimiser's path; 12 the predicate trial |
| 11 | cost (check 4); 11 per-arm success |
| 10 | iteration multiplier (check 2) |
| 8 | same optimum (check 1) |
| 6 | ownership rung A0 → A1 |
| 4 | the lift closed (check 3) |
| 3 | the seed set |
| **1 663** | **total; 0 rows of any other kind** |

**Headings translated before comparing** (the renderer's own declarations, imported, not restated):

| construction | column key | the combined table's heading |
|---|---|---|
| cost per call | `paired_seeds` | *paired with the reference at* |
| cost per call | `pooled` | *vs reference pooled* |
| cost per call | `median` | *vs reference median* |
| fixed-point distance | `n` | *n (shared)* |
| fixed-point distance | `worst_pair` | *worst* |
| the ownership rung A0 → A1 | `paired_seeds` | *paired at* |

These six are the only headings that changed anywhere. The `reference_entries` merge declares none —
its constituents are all of one source, so they never disagreed.

### 4.3 The re-pointed citations

`report_citations_repoint.py EXPERIMENT_REPORT.md` (committed at `3e1956ca`), a declared list of
phrase → phrase with the count it applied, run in two passes: **92 citations re-pointed**
(88 + 4, the second pass being the four split across a line break or whose first half the first pass
had already moved). The mapping:

| old | now | old | now |
|---|---|---|---|
| `D.2`–`D.4` | **Table 8** | `D.49`–`D.51` | `D.3` |
| `D.5` | **Table 9** | `D.52`–`D.60` | `D.8` |
| `D.6`, `D.8`, `D.9` | `D.2` | `D.61`–`D.69` | `D.9` |
| `D.7` | **Table 7** | `D.70`–`D.72` | `D.10` |
| `D.10`–`D.12`, `D.22`–`D.24` | `D.3` | `D.73`–`D.75` | `D.11` |
| `D.13`–`D.21` | `D.4` | `D.76`–`D.78` | `D.12` |
| `D.25`–`D.33` | `D.5` | `D.79`–`D.81` | `D.13` |
| `D.34`–`D.42` | `D.6` | `D.82`–`D.83` | `D.14` |
| `D.43`–`D.48` | `D.7` | `D.1` | `D.1` (unchanged) |
| `F.1`–`F.12` | `F.1` | `F.26`–`F.28` | `F.7` |
| `F.13` | `F.2` | `F.29`–`F.37` | `F.8` |
| `F.14`, `F.18`, `F.22` | `F.3` | `F.38`–`F.43` | `F.9` |
| `F.15`, `F.19`, `F.23` | `F.4` | `F.44`–`F.49` | `F.10` |
| `F.16`, `F.20`, `F.24` | `F.5` | `F.50`–`F.52` | `F.11` |
| `F.17`, `F.21`, `F.25` | `F.6` | `F.53`–`F.55` | `F.12` |
| `F.56`–`F.162` | *withdrawn* — the sentence now says the recomputed copies are not rendered and that the gate's row is the check | | |

After the two passes the renderer resolves **114** references (31 to §3/§4's numbered tables, 63 to
Appendix D, 20 to the companion) with **0 dangling**. `check` now also resolves the plain
`Table n` form, which it could not before: a citation of `Table 9` after a headline table were
dropped would otherwise point at nothing and say nothing about it.

Appendix C's change-log rows were re-pointed by the same pass, so their citations still reach the
table they describe; the A79 row's *"the three headline shapes as Tables D.2–D.9"* gained *"of that
day"* rather than being renumbered, because it is a statement about what that task did (D17).

## 5. Autonomous decisions, each with its reversal

**(a) The second implementation's 107 tables are not rendered anywhere.** The spec says the
recomputed copies are not rendered and that *"the `recomputation` row of the gate table is the
statement"*; I applied it to the companion **and** left them out of the report, and wrote the reason
into the appendix's opening and the companion's header. It halved the companion (162 → 12 grids) and
is 1 663 of the 1 663 withdrawn rows. *Reversal:* add a `Layout` for
`UNRENDERED_STAGE` in `plan_tables.py` and a companion group for it; the tables are still in
`runs/gates/recomputed_tables/measurements.json` and the gate's own record, and nothing else has to
change.

**(b) The regime is a row key everywhere, never a column group.** The spec's table-by-table list asks
for regime **column groups** on the block table's other regimes (item 2) and on fixed-point distance
(item 6), and for a displaced table plus a stencil table on cost per call (item 4) and matched
accuracy (item 5). I used `stack` with the regime as a row key for all four. **Why:** a regime column
group of *median · p90 · above τ* drops nine of fixed-point distance's fifteen columns — the worst
pair, the argmax, the unclean count and the whole-state pair — out of the report for the stencil
regimes, and the block table's ratio-column form drops its four per-arm mean columns and its pair
count. That is a loss of cells, not a change of layout, and this task's own check would have had to
report it. The row-key form keeps every cell **and** gives one table per construction rather than
two. *Reversal:* the spec's shape is a fourth mode on `Layout` (`regime_columns`, with the column
keys it takes per regime); the cells it would drop are all still in the companion's full versions and
in the stage records.

**(c) A combined table's caption is the layout's, not its constituents'.** A combined grid cannot
carry twelve `caption_summary` texts, so each layout declares a caption of a few lines that is true
of the whole construction and states what varies (the reference arm per configuration, the fallback,
what the last row is), while the population and n live in each group's sub-heading row and the
constituent stage tables are named under the grid. The per-constituent summaries are still in the
stage records and are what `tally_contracts` reads. Report captions are now up to **534** characters,
median **364** (A79's rule: a few lines; it was max 485, median 368). *Reversal:* print the distinct
constituent summaries under the grid, as `_declaration_lines` already does for declarations.

**(d) A combined table's denominator is its number of row groups.** `n = 9 (row group(s) of this
table, each over its own population with its own n in its sub-heading row; never pooled)`. Summing
the constituents' n would be a count over a population nobody asked for (trap T11); D21 (b) forbids
pooling configurations. *Reversal:* one line in `_combine`.

**(e) Heading disagreement is asked within a construction, not across one.** In `reference_entries`
the key `ok` means *runs finished per run scheduled* in cost per call and *a count of runs* in the
failure taxonomy; those are two columns of the merged table, not a contradiction. Across
constituents of **one** construction, disagreement is still a refusal. *Reversal:* one predicate in
`_union_columns`.

**(f) Appendix D's groups are now three, not four.** D.0 (constructions), D.1 (gates), D.2 (the
evaluation phase), D.3 (the optimisation phase). The old D.2 *Headline tables* group has no tables
left — they are in §4 — so it is gone rather than empty. *Reversal:* a `Group` entry.

**(g) The self-check's scratch tables were renamed.** `a_scratch_table_of_tally_evaluation` →
`cost per call — a_scratch_configuration — campaign_displaced`, because the renderer now reads the
configuration and the source from the name. The fixture is still "the least content the renderer
accepts" and `stage provenance` still trips all four of its teeth through `render`. *Reversal:* trivial.

## 6. Limits

- **The check is a containment, not a bijection.** It proves every old row survives; it does not
  prove no *new* cell appeared. Nothing computes a number in the renderer, `recomputation` is
  unchanged at 15 122 / 0 over the same 107 tables, and `--plan-tables check` is IDENTICAL, so a new
  cell would have to come from a stage record — which the gates already cover — but the check itself
  does not say so.
- **`reference_entries` and `per_arm_success` are wide** (26 and 23 columns) because a merge keeps
  every constituent column. They are 9 and 14 rows against the 9 tables each replaced, and a reader
  meets the construction once; but they are the two widest grids in the appendix.
- **The one-row census differs from the spec's.** The spec's reassessment counted 21 one-row tables
  at `d483c768`; `report_cells_preserved.py` counts **15** in the report at `c45cac1c` (6 ownership
  rung + 3 seed set + 3 entry-reference cost per call + 3 entry-reference failure taxonomy) and 48
  across both documents. The difference is the counting rule, not the tree; both are 0 now.
- **The cell-preservation check reads the two documents, not the records.** That is what was asked
  (the old *documents* at `c45cac1c`), and it is the right population for a rendering change, but it
  means a cell that was already absent from both documents before is invisible to it.
- **No timing anywhere.** Nothing in this task rests on one (I-10).

## 7. What should change elsewhere

### (a) A defect found, **not fixed** — §4.1 and §4.4 carry stale gate counts

The brief forbids number changes, so these are reported rather than corrected. §4.1 says
*"`tally_contracts` … its 559 compared are 303 table checks + 256 cells"* and §4.4 says
*"101 tables, 14 394 cells, 0 mismatched"*. The committed Table D.1 at `c45cac1c` already read
**577 (321 + 256)** and **15 122** over **107 tables** — the prose is A79's and A80's, stale since
the table set grew at A82, and it was stale before this task began. The fix is three numbers in two
sentences: 559 → **577**, 303 → **321**, and "101 tables, 14 394 cells" → "**107 tables, 15 122
cells**". **This needs the user's or the orchestrator's ruling**, because it is a number change.

### (b) Harness plan amendment 29, proposed text

> **Amendment 29 (2026-09-15, A83 (headline-tables-in-text)) — one construction, one table; the
> headline tables in §4.** At the user's rulings (*"keep the headline tables, with their discussion,
> in the main text"*; *"[the tables] seem expanded over a bunch of different tables with one row,
> which makes no sense at all"*) the renderer gained a declared **`Layout` per construction**. The
> tally emits a table per *(configuration, source)* — 82 tables for 17 constructions in Appendix D,
> 21 of them one row, 162 in the companion with every table twice — and the renderer now combines
> them: `stack` (configurations and regimes as row groups under a sub-heading row stating each
> group's own n), `merge` (constituents of one configuration aligned on a join column, a
> per-configuration fact broadcast across the arm rows), `single` (a construction the tally emits
> whole). The three headline tables are rendered into **§4 itself**, between `MAIN_START` /
> `MAIN_END` marker pairs carrying the layout's name and numbered `Table n` after §3's six; `write`
> replaces the blocks bottom-up so one replacement does not move the next one's lines, and `check`
> compares each block and resolves `Table n` as well as `Table D.n` / `F.n`. The second
> implementation's tables are rendered **nowhere**: gate `recomputation`'s row of Table D.1 is that
> check. **Rule (xv): a construction's layout is a declaration.** A tally table whose kind, source
> or detail flag no layout claims is refused, as is one claimed by two; a combined column whose
> constituents of one construction spell the heading differently is refused unless the layout
> declares the combined heading. Amendment 28's numbering and caption rules stand; its
> "Appendix D and the companion file are rendered" reads "§4's headline tables, Appendix D and the
> companion file are rendered". **A rendering change moves cells and never changes them**: the
> proof is a committed check keyed by construction, configuration, source, row and column and never
> by table number (`report_cells_preserved.py`) — 3 444 rows / 38 451 cells compared, 1 781 rows /
> 19 048 cells preserved whole, 0 differing, 1 663 rows withdrawn and every one of them the second
> implementation's. Census 83 → 17 report grids, 162 → 12 companion, 48 → 0 one-row. Gates
> re-pressed with `--resume`: `recomputation` 15 122 / 0, `tally_contracts` 577 / 0,
> `run_kind_separation` 3 000 / 0, `self_containment` 52 / 0, gate table 30 PASS / 161 of 161 teeth;
> stamp survey 1 102 records, 0 re-made — **0 PROCESS runs**.

### (c) `harness/README.md` — **done** (committed at `d96ce438`)

§0 layer 4, §0 *How a number reaches the plan*, and §5's `--plan-tables` block now describe the
layouts, the three modes, the main-text markers, the per-group denominators and the withdrawn
recomputed copies.

### (d) TRAPS — no new trap proposed

T17 (*a table number is a position, not a name*) is exactly what this task lived through: every one
of the 92 citations moved. Its remedy — cite by the construction name under the grid, re-read every
numbered citation when the table set changes — is what was done, and the combined grids now print
*every* constituent construction name under themselves, which makes the remedy cheaper rather than
different. Nothing to add. (If the orchestrator wants one, the candidate is *"a caption that varies
by constituent cannot survive a combination"* — decision (c) above — but it is a consequence of the
layout rule, not an independent way of being misled.)

### (e) Nothing proposed for the queue or the decisions register

D-rows are the user's to mint. Items (a) and (b) above are proposals, not entries.

## 8. Commits

| commit | what |
|---|---|
| `60ae0074` | the renderer combines: `Layout`, `LAYOUTS`, `stack` / `merge` / `single`, the main-text markers and numbering, the withdrawn recomputed stage; the self-check's scratch table names |
| `3e1956ca` | §4 carries Tables 7–9 between the markers; 92 citations re-pointed by the committed `report_citations_repoint.py`; Appendix D and the companion re-rendered |
| `55da17b4` | `report_cells_preserved.py` — the cell-preservation check |
| `d96ce438` | `harness/README.md` §0 and §5 |
| `8f07328a` | the census printed by the cell-preservation check |

Nothing under `arch_surgery/MDA_partitioning_experiment_v4/PROCESS/`, `harness/child/` or the root
`process/` changed. `EXECUTION_APPROVED` untouched. Nothing pushed.

## Orchestrator's critical assessment (protocol §5)

*Written 2026-09-15 at `ee307296` by the orchestrating session, by checks that differ from the agent's; gates the merge.*

**Checks.** (1) **Census by my own script** over the rendered headings and grids of the branch's report: 17 tables — Tables 7–9 in §4, D.1–D.14 in Appendix D — and **0 with a single row** (data rows counted after the sub-heading rows); the widest is D.3 at 25 columns (the entry reference's three constructions merged, 6 rows), the longest D.5 at 66 rows (matched accuracy, all regimes and rulers stacked). Against the spec's target of about fifteen: met. (2) **The headline cells against their pre-A83 values**: Table 7's TOTAL rows read 0.5625 / 0.5772 / 0.5016 and Table 8's `all counted nodes` 0.6391 / 0.4504 / 0.5330, the same digits as D.7 and D.2–D.4 before; Table 9 is D.5 unchanged. (3) **Gate records** in the worktree: `recomputation` 15 122 / 0, `tally_contracts` 321 / 0, `run_kind_separation` 3 000 / 0, `self_containment` 52 / 0, all stamped `55da17b4` — the last commit that touched code (the three after it are README, the check's census and the report). (4) **Scope by diff**: eight files, nothing under `PROCESS/`, `harness/child/` or the root `process/`. (5) The agent's decision (b) — the regime as a *row key* on the block, distance, cost-per-call and accuracy tables rather than the spec's column groups — is right: the column-group form would have dropped cells from the report, which the spec's own rule (no cell lost) outranks; the reversal is declared.

**Fixed in this commit, not deferred.** The stale §4.1 prose the agent found and was forbidden to touch (three numbers: `recomputation` 101 tables / 14 394 → 107 / 15 122; `tally_contracts` 559 = 303 + 256 → 577 = 321 + 256, stale since A82 grew the table set) is brought to Table D.1's cells here, with the correction named in A83's Appendix C entry.

**Findings for the record, none blocking.** Tables 7–9 now carry the right rows in the right place, but two presentation points remain against the user's own mock-up: the mean and its `[min, max]` are separate columns (Table 8 runs to 16), where one cell `3 957 [3 516, 4 560]` reads better; and the sub-heading rows carry the tally's full table name (`large_tokamak_nof · campaign_optimisation · BR·B0·B1·B2 — n = 22 (seeds on which every arm … converged)`) where `large_tokamak_nof (n = 22)` would do. Both are a rendering pass over the `Layout` declarations, no cell touched — a small follow-up if the user wants it.

**Verdict: merge.** The rule *one construction, one table* is met (82 → 14 in the appendix, 162 → 12 in the companion, 0 one-row tables), the headline tables sit in §4 with their discussion, every old cell is present with the same value by the agent's committed check and the headline cells by my reading, gates PASS at the code commit, zero PROCESS runs.
