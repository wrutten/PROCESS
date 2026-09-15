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
