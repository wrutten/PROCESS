# The V4 report's headline tables — the shapes the user wants

> **Document status** — **RULING, 2026-09-15.** The user showed three tables from the V3 report
> and said: *"These should be the main tables to show the headline results (with exp arm names
> adjusted ofc). There can be previous tables to elucidate which statistics end up in these tables.
> But I think this is all I need to make my conclusions."* This file transcribes the three shapes
> for task **A79 (report-captions)**; the numbers below are V3's, shown only to fix the shape, and
> must not appear in the V4 report. Arm names are V4's after A78 (arm-renames):
> `AR/A0/A1/A2` and `BR/B0/B1/B2`.

## Shape 1 — optimisation phase: node calls per module, per configuration

One table per configuration, headed `<configuration> (n = <seed set size>)`. One row per node
group of the partition (M1, M2, M3, the once-per-run nodes, the pulse node, the feed-forward /
post-solve nodes), then a **total calls** row. Columns: `module`, `models` (nodes in the group),
one column per optimisation arm with **per-run mean `[min, max]`** node calls, the pooled ratio
of the partitioned arm to the flat arm (`B2/B0`), the **per-run median `[min, max]`** of that
ratio, and **`runs B2 > B0`** as a count over n. The total row gives summed calls and the pooled
ratio's bracket.

| module | models | BR | B0 | B1 | B2 | B2/B0 | per-run med [min, max] | runs B2 > B0 |
|---|---|---|---|---|---|---|---|---|
| M1 | 24 | 1978 [1758, 2280] | 2028 [1793, 2396] | 2043 [1823, 2383] | 1391 [1243, 1626] | **0.686** | 0.692 [0.598, 0.800] | 0/22 |
| M2 | 10 | … | … | … | 1764 [1575, 2060] | **0.870** | 0.877 [0.762, **1.014**] | **1/22** |
| M3 live | 11 | … | … | … | 1544 [1380, 1807] | **0.761** | 0.768 [0.658, 0.888] | 0/22 |
| `vacuum` (once per run) | 1 | … | … | … | 4 | **0.002** | 0.002 [0.002, 0.002] | 0/22 |
| PULSE | 1 | … | … | … | 643 [575, 751] | **0.317** | 0.320 [0.277, 0.370] | 0/22 |
| FF | 5 | … | … | … | 4 | **0.002** | 0.002 [0.002, 0.002] | 0/22 |
| **total calls** | 52 | 102 868 | 105 432 | 106 241 | 68 676 | **[0.651, 0.666]** | 0.657 [0.568, 0.760] | 0/22 |

*(V3's `tok` table; V4 has four optimisation arms, so BR gets a column as shown.)*

## Shape 2 — optimisation phase: the optimiser's path, all configurations in one table

One row per configuration. Columns: `config`, `n`, per-arm **mean optimiser iterations** (or the
declared construction: summed over attempts), the ratio's mean, the ratio's **median `[min, max]`**,
and the count of seeds with ratio `> 1` over n.

| config | n | BR | B0 | B2 | B2/B0 mean | B2/B0 median [min, max] | B2/B0 > 1 |
|---|---|---|---|---|---|---|---|
| nof | 22 | 7.82 | 7.82 | 7.77 | 0.994 | 1.000 [0.875, 1.143] | 2/22 |
| lad | 11 | 20.73 | 20.73 | 20.91 | 1.009 | 0.833 [0.250, 5.909] | 3/11 |
| st | 22 | 22.05 | 23.91 | 23.95 | 1.002 | 1.000 [0.246, 1.857] | 6/22 |

The same shape serves the **evaluation-count ratio ε** (from `sweeps_per_eval.n_evaluations`,
issue I-26) and the **per-evaluation cost ratio ρ**, so that R = ρ × ε can be read across three
rows per configuration.

## Shape 3 — evaluation phase: node calls per block, all configurations stacked

One table, a sub-heading row per configuration. One row per block (with its node count on the
first configuration), then post-solve / feed-forward, then **TOTAL**. Columns: one per evaluation
arm with **mean node calls per evaluation**, then the ratio of the partitioned arm to its declared
reference (`A2/A1` on the pulsed configurations, `A2/A0` on st — the caption says which; V3 showed
`A1/A0`).

| block (nodes) | A0 | A1 | A2 | A2/A1 |
|---|---|---|---|---|
| **large_tokamak_nof** | | | | |
| M1 (2 nodes) | 276 | 200 | 200 | 0.725 |
| M2 (3 nodes) | 414 | 387 | 387 | **0.935** |
| M3 (12 nodes) | 1656 | 900 | 900 | 0.543 |
| PULSE (1 node) | 138 | 25 | 25 | 0.181 |
| **post-solve (3 nodes, feedforward)** | 414 | 0 | 0 | **0.000** |
| TOTAL | 2898 | 1512 | 1512 | **0.522** |
| **low_aspect_ratio_DEMO** | … | | | |
| **st_regression** | … | | | |

*(V3's columns were `A0 / A1u / A1`; V4's are `AR / A0 / A1 / A2`, with the matched-accuracy
statement made in the text beside, not in the table.)*

## What the rest of the report does with these

- These are the tables §4 (main text) is written from and points at; they live in the results
  appendix with the summarising tables that feed them (matched accuracy, same-optimum check,
  fixed-point distance, failure taxonomy — each summarised per arm and configuration, never per
  seed).
- Every cell is still a stage's output rendered by `plan_tables.py` and covered by
  `recomputation` and `tally_contracts`; the shapes above are rendering groupings of cells the
  tally already computes (per-module and per-block node calls, per-run brackets, pooled ratios,
  counts over n). Where a cell is not yet computed (e.g. per-module brackets on the optimisation
  phase), the tally and the analysis both gain it under the gate — zero PROCESS runs.
- Captions: a few lines, academic style; construction detail in the appendix's context
  paragraph, said once.

---

## The orchestrator's reassessment of the report's table formatting (2026-09-15) — binding on A83 (headline-tables-in-text)

*The user, on reading Appendix D after A82: "these seem expanded over a bunch of different tables with one row, which makes no sense at all. Critically reassess the report formatting yourself, and improve the reporting." The census below is from the report at `d483c768`, by a script over the rendered headings and grids.*

### What is wrong

Appendix D holds **82 tables for 17 constructions**. The renderer emits one table per *(construction, configuration, source)* because that is how the tally emits them, so a reader meets the same grid three, six, nine or twelve times with a different name over it:

| construction | tables | rows each | what a reader needs |
|---|---|---|---|
| cost per call | 12 | 1, 3, 4 | one |
| matched accuracy | 12 | 2, 6, 8 | one or two |
| fixed-point distance | 9 | 2, 4 | one |
| failure taxonomy (evaluation phase) | 15 | 1, 3, 4 | one |
| ownership rung | 6 | **1** | one, six rows |
| the seed set | 3 | **1** | none — a column of the per-arm success table |
| per-arm success, same optimum, iteration multiplier, cost (check 4), achieved accuracy | 3 each | 2–8 | one each |
| the lift closed | 2 | 2 | one |
| node calls per module (headline) | 3 | 6–7 | one, stacked |
| node calls per block (headline) | 4 | 17 | one in the text, one in the appendix |

**Twenty-one tables have a single row.** The *entry-references* source (one run per configuration) alone produces nine one-row tables. The companion file repeats the pattern at 162 tables, and doubles it: it carries the full version of every report table *and* the recomputed copy of each, so a construction appears there up to twenty-four times.

### The rule

**One construction, one table.** Configurations are row groups under a sub-heading row (as the block table, shape 3, already does) or a `configuration` column; arms are rows within the group; the source regime is a column group where the statistic is short (median · p90 · above τ per regime) and a row key where it is not. A table is never split by configuration. A one-row table is a row of some other table. Something stated once per configuration and not per arm (the seed set, the reference entry) is a column or a row of the table it qualifies, not a table.

### The layout, table by table

**Main text** (numbered `Table n`, continuing §3's; rendered by the renderer between markers; each followed by its discussion paragraph, moved from the present §4 prose):

- §4.2: **shape 3 on the displaced regime** — node calls per block, configurations stacked, `AR/A0/A1/A2` and `A2/reference`; the discussion of RQ1 beside it.
- §4.3: **shape 1** — node calls per module, the three configurations stacked under sub-heading rows (`large_tokamak_nof (n = 22)` …), `BR/B0/B1/B2` mean `[min, max]`, `B2/B0` pooled, median `[min, max]`, `runs B2 > B0`; then **shape 2** — the optimiser's path, ε, ρ, R over the configurations (today's D.5); the discussion of RQ2, RQ3 and the trajectory beside them.

**Appendix D** — target about fifteen tables:

1. Gates (today's D.1) — unchanged.
2. Node calls per block, the other three regimes — one table: rows configuration × block (the block table's row set), columns `A2/reference` pooled for entry-reference, stencil forward, stencil backward, with the displaced ratio repeated in the first column for reading across.
3. Reference entries — one table, one row per configuration: the entry-reference run's cost per call and its audit residual per arm (today's nine one-row tables of the `campaign_entry_references` source across cost per call, matched accuracy and failure taxonomy).
4. Cost per call — one table: rows configuration × arm, one column group per regime (displaced; stencil forward; stencil backward) holding node calls mean `[min, max]`, prime calls, sweeps; if wider than about twelve columns, two tables: displaced, and stencil with a direction column.
5. Matched accuracy — one table: rows configuration × arm × ruler, displaced regime; the stencil regimes as a second table with a direction column (the restricted median, p90, argmax, whole-state, excluded).
6. Fixed-point distance — one table: rows configuration × pair (10 rows), column groups per regime (median · p90 · above τ), plus the argmax and whole-state median for the displaced regime.
7. Ownership rung `A0 → A1` — one table, six rows (configuration × regime).
8. Failure taxonomy, evaluation phase — one table: rows configuration × arm, columns the outcome classes, regimes as column groups only if any regime has a non-zero off-`ok` count; otherwise one line in the caption says every evaluation finished.
9. Per-arm success (optimisation phase) — one table, configurations stacked (today's D.67–D.69); it absorbs the seed set (D.64–D.66) and the optimisation-phase failure taxonomy (D.61–D.63), which are not repeated.
10. Same optimum (check 1) — one table, configurations stacked.
11. Iteration multiplier (check 2) with ε and the sweeps ratio — one table, configurations stacked (or folded into shape 2 if the columns coincide; say which).
12. Cost (check 4) — one table, configurations stacked.
13. Achieved accuracy at the accepted optimum — one table, configurations stacked, rows arm × ruler.
14. The lift closed (check 3) — one table, the two pulsed configurations stacked.
15. Per-sweep overhead — one table per phase at most, configurations stacked, if it is kept in the report at all; otherwise the companion.

**Companion file** — the same rule: one construction, one table, seeds as rows, configurations stacked; the recomputed copies are not rendered as tables (the `recomputation` gate's row in Table D.1 is the statement; the gate's record holds the cells).

### How, without touching a cell

This is a **rendering** change: the renderer combines the tally's per-(configuration, source) tables of one construction into one rendered table under a declared layout per construction kind (stack by configuration with sub-heading rows; regime as column group; one-row tables absorbed into a named host table). The tally's emission, the stage records, and the gates over cells (`recomputation`, `tally_contracts`) are unchanged — every cell is still a cell of a stage record, still recomputed, still compared. `--plan-tables check` guards the combined rendering as it guards today's; the cell-preservation proof (every old cell present with the same value, keyed by construction, configuration, source, row, column — not by table number) is run once as a committed check and its result stated in the report. Zero PROCESS runs.
