# A85 (v3-table-formats) — the report's tables in the V3 report's forms

> **Document status** — **OPEN**, task **A85 (v3-table-formats)**, branch `A85-v3-table-formats`
> (worktree `.claude/worktrees/A85-v3-table-formats`), base `4b902124`, tip `3aa1ffb8`.
> Specification: [`../plans/REPORT_TABLE_FORMATS.md`](../plans/REPORT_TABLE_FORMATS.md) (RULING,
> 2026-09-15). **Zero PROCESS runs**; `EXECUTION_APPROVED` untouched; no file under
> `MDA_partitioning_experiment_v4/PROCESS/`, `harness/child/` or the root `process/` changed.
> Arm names are today's (`AR/A0/A1/A2`, `BR/B0/B1/B2`); the records stamp the names of their day
> and `records.read` translates (trap T16).

---

## 1. Verdict

**The previous revision's cell formats are now the report's, everywhere, and its two per-module
tables and its iteration table are built and in the main text.** The user's instruction was
*"these headline tables are not what I gave you as images. How I want them formatted is based on
v3 report section 4 and 5. Start by reproducing these kinds of tables, considering the name change
of the arms. If you deviate, justify it."* Of the eighteen tables the specification maps, **seven
are delivered** — the three the user gave as images among them — and **eleven are not built**.
That is the headline of this report and §7 says exactly what each of the eleven needs.

What is delivered:

1. **Two new constructions, `module sweeps per run`**, one per phase — the previous revision's
   §4.5 and §5.5.1 tables, which are two of the user's three images. Fifteen new stage tables,
   **1 154 new cells**, each computed in the tally, re-derived by the second implementation and
   compared cell by cell under gate `recomputation` (**122 tables, 16 276 cells, 0 mismatched**).
2. **The optimiser's path split into four tables of one quantity each** — the previous revision's
   §5.3 shape, which is the third image — by a declared row selection. No new cell.
3. **The V3 cell formats across every rendered table**: a mean with its seed bracket in one cell
   (`1978 [1758, 2280]`, a bare value where every run agreed), a median with its p90 in one
   (`5.042e-10 / 2.963e-09`), the result column and the verdict in bold, per-configuration blocks
   under a bold heading line, a repeated key blanked on continuation rows.
4. **Two teeth** for `tally_contracts`, and **four stale citations** the previous re-pointing left
   behind, repaired.

### 1.1 The census

| | before (`4b902124`) | after (`3aa1ffb8`) |
|---|---|---|
| tables in §4 (main text) | 3 | **7** |
| tables in Appendix D | 14 | **15** |
| tables in the companion file | 12 | **13** |
| markdown grids in the report | 17 | **26** |
| markdown grids in the companion | 12 | **21** |
| tables with one row | **0** | **0** |
| stage tables the tally emits | 107 | **122** |
| cells the two implementations compare | 15 122 | **16 276** |

*A blocks-mode table prints one grid per configuration under one caption and one number, which is
why the grid counts rise faster than the table counts: Table 12, Table 13 and companion Table F.1
are three tables and nine grids.* The one-row count is 0 before and after — A83's rule holds.

### 1.2 The V3 → V4 table map

| V3 table | V4 table | state |
|---|---|---|
| **T4.1** check 1, matched accuracy (§4) | — | **not built** (§7 a) |
| **T4.2** cost of the prime → per-call cost (§4) | — | **not built** (§7 b) |
| **T4.3** full distributions per configuration and arm (§4.4) | — | **not built** (§7 c) |
| **T4.4** module scope (§4.5, static) | — | **not built** (§7 d) |
| **T4.5** per-module sweeps per run (§4.5) | **Table 12**, §4.2 | **built** — the user's first image |
| **T4.6** the exclusion set's namespaces (§4.5) | — | **not built** (§7 e) |
| fixed-point distance (V4 only, A76) | **Table D.6** | re-rendered in V3's cell formats |
| **T5.1** robustness and taxonomy (§5.1) | **Table D.10** | re-rendered; not moved to the main text (§7 i) |
| **T5.2** same optimum, check 1 (§5.2.1) | **Table D.11** | re-rendered; not moved to the main text (§7 i) |
| **T5.3** location diagnostic (§5.2.2) | — | **not built** (§7 f) |
| **T5.4** iteration multiplier, check 2 (§5.3) | **Table 8**, §4.3 | **built** — the user's third image |
| — the ε table of the same shape | **Table 9**, §4.3 | **built** |
| — the ρ table of the same shape | **Table 10**, §4.3 | **built** |
| — the R = ρ × ε table of the same shape | **Table 11**, §4.3 | **built** |
| **T5.5** identity table (V3's `B2`/`B3`) | — | **not built** (§7 g) |
| **T5.6** lift closure, check 3 (§5.4) | **Table D.15** | re-rendered in V3's cell formats |
| **T5.7** cost, check 4 (§5.5) | **Table D.13** | re-rendered; the V3 shape not built (§7 h) |
| **T5.8** both anchors (§5.5) | — | **not built** (§7 h) |
| **T5.9** sweeps and prime calls (§5.5) | — | **not built** (§7 h) |
| **T5.10** per-module breakdown (§5.5.1) | **Table 13**, §4.3 | **built** — the user's second image |
| **T5.11** problem definition (§5.6) | — | **not built** (§7 j) |

V4's own tables with no V3 counterpart keep their places, re-rendered in the V3 formats: node
calls per block (Table 7 and D.2), the reference entries (D.3), cost per call (D.4), matched
accuracy (D.5), the ownership rung (D.7), the evaluation phase's failure taxonomy (D.8), node
calls per module (D.9 — moved out of the main text, see §4), achieved accuracy (D.14).

### 1.3 The three tables the user gave as images, as rendered

**Table 12 — module sweeps per run, the evaluation phase (V3's §4.5).** One block per
configuration; `nof` shown:

| module | models | AR | A0 | A1 | A2 | reference | A2 / reference | pairs |
|---|---|---|---|---|---|---|---|---|
| M1 | 24 | 4.96 [4, 5] | 5.52 [5, 6] | 5.12 [4, 6] | 4 | A1 | **0.7812** | 25 |
| M2 | 10 | 4.96 [4, 5] | 5.52 [5, 6] | 5.12 [4, 6] | 5.16 [5, 6] | A1 | **1.0078** | 25 |
| M3 | 11 | 4.96 [4, 5] | 5.52 [5, 6] | 5.12 [4, 6] | 3 | A1 | **0.5859** | 25 |
| PULSE | 1 | 4.96 [4, 5] | 5.52 [5, 6] | 5.12 [4, 6] | 1 | A1 | **0.1953** | 25 |
| once per run | 3 | 4.96 [4, 5] | 5.52 [5, 6] | 5.12 [4, 6] | 0 | A1 | **0.0000** | 25 |
| total calls | 49 | 243 | 270.5 | 250.9 | 181.6 | A1 | **[0.724, 0.767]** | 25 |

**Table 13 — module sweeps per run, the optimisation phase (V3's §5.5.1).** `nof` shown:

| module | models | BR | B0 | B1 | B2 | B2/B0 pooled | B2/B0 per-run median [min, max] | runs B2 > B0 | of n |
|---|---|---|---|---|---|---|---|---|---|
| M1 | 24 | 1978 [1758, 2280] | 2028 [1793, 2396] | 2041 [1821, 2381] | 1389 [1241, 1624] | **0.6851** | 0.6909 [0.598, 0.799] | 0 | 22 |
| M2 | 10 | 1978 [1758, 2280] | 2028 [1793, 2396] | 2041 [1821, 2381] | 1762 [1573, 2058] | **0.8691** | 0.8765 [0.761, 1.013] | 1 | 22 |
| M3 | 11 | 1978 [1758, 2280] | 2028 [1793, 2396] | 2041 [1821, 2381] | 1542 [1378, 1805] | **0.7603** | 0.7670 [0.657, 0.887] | 0 | 22 |
| PULSE | 1 | 1978 [1758, 2280] | 2028 [1793, 2396] | 2041 [1821, 2381] | 641 [573, 749] | **0.3161** | 0.3189 [0.276, 0.369] | 0 | 22 |
| once per run | 3 | 1978 [1758, 2280] | 2028 [1793, 2396] | 2041 [1821, 2381] | 2 | **0.0010** | 0.001 | 0 | 22 |
| total calls | 49 | 96933 | 99350 | 100013 | 68566 | **[0.690, 0.736]** | 0.6959 [0.602, 0.805] | 0 | 22 |

**Table 8 — the iteration multiplier (V3's §5.3).** One row per configuration:

| quantity | configuration | arms | n | BR | B0 | B1 | B2 | B2/B0 mean | B2/B0 median [min, max] | seeds B2/B0 > 1 |
|---|---|---|---|---|---|---|---|---|---|---|
| iterations (summed over attempts) | large_tokamak_nof | BR · B0 · B1 · B2 | 22 | 7.818 | 7.818 | 7.773 | 7.773 | 0.9964 | **1.0000 [0.875, 1.143]** | 2 |
|  | low_aspect_ratio_DEMO | BR · B0 · B1 · B2 | 11 | 29.82 | 29.82 | 20.91 | 20.91 | 1.3842 | **0.8125 [0.129, 5.909]** | 3 |
|  | st_regression | BR · B0 · B2 | 22 | 31.18 | 25.14 | — | 23.95 | 0.9828 | **1.0000 [0.246, 1.356]** | 5 |

**A confirmation worth naming.** The two per-module tables were written from the V4 records with
no V3 number in front of them, and they reproduce the previous revision's own cells where the two
campaigns are comparable: the previous revision's `tok` block reads M1 `5.52 [5,6]` for the flat
arm and `4` for the partitioned one, M2 `5.16 [5,6]`, M3 `3`, PULSE `1`, and a `lad` total of
`178.8` — every one of those is a cell of Table 12. The previous revision's `st` M2 ratio of
`1.000` — the partition buying that module nothing — reproduces exactly. That is a construction
check the recomputation gate cannot give, because both implementations here are V4's.

---

## 2. The new constructions, and their re-derivation

Three declarations in `harness/measurement/stats.py`, each with an independently written twin in
`harness/measurement/analysis.py` (which may import nothing from `stats`, `tables` or either
`tally` module — gate `recomputation`'s import tooth):

| construction | what it is | the premise it checks rather than assumes |
|---|---|---|
| `stats.module_sweeps` | **module sweeps in one run** — the census count every node of a group shares | refuses the run where the group's nodes did **not** execute equally often, naming the group and the counts |
| `stats.dsm_rows_by_group` | `models` per group under the two attributions of the once-per-run nodes' collapsed-DSM rows (`v = 1`, `v = 0`) | refuses where the committed node map states no row count for a module — `models` is never guessed (trap T9) |
| `stats.weighted_total` | `Σ sweeps × models` under one attribution | returns nothing rather than a sum over a population smaller than the table's rows |

**Why sweeps and not node calls.** Within a group every model node runs once per sweep, so the
cell is a sweep count and **its ratio does not depend on whether one counts model calls or DSM
rows**. The total does, which is why it is published as an interval and demoted to reconciliation
— exactly the previous revision's reasoning, and exactly its `[v = 1, v = 0]` bracket.

**Agreement.** Gate `recomputation`, `--resume`, at `d6e8c229`: **122 tables compared, 16 276
cells, 0 mismatched**, over 949 campaign run records made at `57dc0c14`. Before the task: 107
tables, 15 122 cells. The 1 154 new cells are the fifteen `module sweeps per run` tables (three
configurations × four evaluation-phase sources, plus three optimisation-phase tables). Nine teeth
tripped, including the import tooth and the doctored-cell tooth.

**Two new teeth** on `tally_contracts` (`--resume`, at `548082b2`; **PASS, 622 compared, 0
mismatched, 13 of 13 teeth tripped**, 161 → 163 teeth in the gate table):

| tooth | what is offered | it must |
|---|---|---|
| *a module executed unequally* | a group whose two nodes ran 4 and 5 times | REFUSE — tripped |
| *a DSM row count the map does not state* | a node map with no row count for M3 | REFUSE — tripped |

---

## 3. Deviations

Every place a V4 table is not the V3 table, one line each. The specification names the first
block; the second block is this task's own.

### 3.1 Named in the specification

| V3 | V4 | what differs | why |
|---|---|---|---|
| T4.5, T5.10 columns `A0 / A1u / A1`, `R / B0 / B1 / B2 / B3` | `AR / A0 / A1 / A2`, `BR / B0 / B1 / B2` | `A1u` and V3's `B2` dropped, `AR` and `A1` added | `A1u` is not run in V4 (the prime is inside the intervention); V3's `B2` was removed by D22; `AR` and `A1` are V4's reference and ownership rungs. The specification's §0 translation, applied |
| T4.5 ratio against `A0` | ratio against `A1` on a pulsed configuration, `A0` on st | the declared reference arm changed | V4 declares the reference per configuration (`tally_evaluation.reference_arm`); the *reference* column names it in every row |
| T5.10 `st` block without `B1` | the same | — | not a deviation; the heading line names the arm set |

### 3.2 Introduced by this task

| # | V3 | V4 | what differs | why |
|---|---|---|---|---|
| 1 | T4.5 / T5.10 rows `M1, M2, M3 live, \`vacuum\`, PULSE, FF` | `M1, M2, M3, PULSE, once per run` | V4 groups **the configuration's own deferred nodes** (`costs`, `vacuum`, `water_use`, and `pulse` on st) into one *once per run* row instead of splitting `vacuum` out of M3 and leaving `costs`/`water_use` in FF | The grouping is V4's existing, derived one (`stats.node_groups` from the committed node map and the configuration's per-run artifact), already used by Tables 7 and D.9 and already gated. Re-splitting it for one table would put two groupings in one report |
| 2 | T4.5 / T5.10 `models` total 52 | 49 | three collapsed-DSM rows are attributed to no group | Those are FF's rows whose nodes execute on no configuration of this experiment. The previous revision named the same limit and did not resolve it; the caption of each table now states the map's 52 and the configuration's 49, so the gap is visible rather than implied |
| 3 | T4.5 / T5.10 total ratio a bracket over `v = 0/1` for `vacuum`'s row | the same bracket over the **whole once-per-run group's** rows | the unknown is three or four rows, not one | Follows deviation 1: the group is the thing whose row ownership is unknown. The construction is unchanged and the caption says which nodes |
| 4 | configurations abbreviated `tok / lad / st` | `nof / lad / st` | the first configuration's short name | The V4 report writes `nof` for `large_tokamak_nof` throughout §4–§6 (A79). A table that renamed it `tok` would be a table the report's own prose cannot cite |
| 5 | numbers spaced (`102 868`) | unspaced (`96933`) | no thousands separator | The existing V4 cells carry none, and a separator inside a cell makes the committed cell-preservation comparison string-sensitive to presentation |
| 6 | T5.4 columns `n, R, B0, B3, ratios` | the same plus a constant `quantity` column | one column names the quantity, stated once and blank after | The four tables are selections of one stage table; keeping the selector visible means no cell of that table is dropped, and `blank_repeats` states it once |
| 7 | cross-configuration tables put the configuration in the first column, blank on continuation rows | the appendix's stacked tables keep A83's **bold sub-heading row** per configuration | the configuration is a row group, not a first column | The sub-heading row carries the configuration **and** the source regime **and** that group's own `n` with what it counts (trap T11); a blank first column can carry only the first of those. Applied where a key really repeats down consecutive rows: the two accuracy tables (arm × ruler) and Table 7 |
| 8 | V3 §5.2.1 has `within-cluster med / p90 / would accept` columns | V4's same-optimum table has `below resolution` | a different companion construction | V4 never built the within-cluster construction; `below_resolution` is what it has. Not introduced here — recorded because the map would otherwise imply a like-for-like reproduction |
| 9 | node calls per module was §4.3's Table 8 | Appendix D.9 | the node-call per-module table left the main text | Its sweeps twin (Table 13) is the previous revision's headline and is the table the user asked for; keeping both in §4 would be the same grid twice in two units. D.9 is kept whole because its *of which outside the solve phase* row is what check 4's solve-phase total is read from, and the sweeps table has no such row |

---

## 4. Placement and the re-pointed citations

**Main text.** §4.2 now carries Table 7 (node calls per block) with the RQ1 paragraph, then
**Table 12** with a new paragraph that reads it — the flat arm's single repeated number, the
partitioned arm's exact constants, M2's `1.0078 / 0.9919 / 1.0000`, M3's 2.52 / 2.00 / 2.84 fewer
sweeps, and the total as an interval. §4.3 carries **Table 13** with a new paragraph on the three
readings of the ratio (per-run universality, the flat arms' free consistency check, where the
partition does real work), then **Tables 8–11** — iterations, ε, ρ and R = ρ × ε — each under the
prose that reads it.

**Citations.** `report_citations_repoint.py` was rewritten for this move and executed (protocol
§15); it applies the number shifts **highest first** and then the phrases, and prints what it
could not find:

- Appendix D: `D.9`–`D.14` each moved up one (node calls per module entered at D.9) — **29
  citations** moved.
- The companion: `F.1`–`F.12` each moved up one (module sweeps in the other three regimes entered
  at F.1) — **20 citations** moved.
- Ten phrases naming a table by name, including the four **stale citations the previous
  re-pointing left behind**: `(Table 9 and D.34–D.36)` — a number that had not existed since A83 —
  and three further `Table 9` citations in §4.2 and §5.1 that named the optimiser's path where
  matched accuracy was meant. These are corrected to `Tables D.5 and D.6` / `Table D.5`.
- `--plan-tables check`: **0 dangling** references, 33 to §3/§4's numbered tables, 71 to
  Appendix D, 20 to the companion.

---

## 5. Verification

Worktree root, everything committed, nothing running, seeded with the A83 records tree.
**Zero PROCESS runs.**

| check | result |
|---|---|
| `--measure tally_evaluation --resume` | 80 tables (68 before); 0 runs made |
| `--measure tally_optimisation --resume` | 42 tables (39 before); 0 runs made |
| `--gate recomputation --resume` | **PASS** — 122 tables, **16 276 compared, 0 mismatched**, 9/9 teeth |
| `--gate tally_contracts --resume` | **PASS** — **622 compared (366 + 256), 0 mismatched**, **13/13 teeth**, both new teeth tripped |
| `--gate run_kind_separation --resume` | **PASS** — 3 000 compared, 0 mismatched, 9/9 teeth |
| `--gate self_containment --resume` | **PASS** — 52 files compared, 0 mismatched, 1/1 tooth |
| `--measure gate_table --resume` | **30 PASS, 0 FAIL, 163 of 163 teeth tripped** (161 before) |
| `--plan-tables write` then `--plan-tables check` | **IDENTICAL** for all seven §4 blocks, for Appendix D (879 of 879 lines) and for the companion (1 671 of 1 671); **0 dangling** references |
| `report_cells_preserved.py --base 4b902124` | **1 761 of 1 761 rows and 19 426 of 19 426 cells preserved** (14 689 of them carrying a number); **0 missing**; **2 differing**, both rows of the gate table |
| `run_stamp_survey.py`, before and after | **1 102 records**, the same nine commits, 949 at `57dc0c14`; **0 re-made, 0 new** |
| `--selfcheck` | **PASS** (after the fixture fix of §6) |
| `report_counts_check.py` | runs; **4 lines differ**, the same four that differed at the base — down from 6, the two teeth lines now agreeing |

**The two differing rows, with their denominators.** Both are rows of Table D.1, and both are the
gates' own cells rather than a rendering:

| row | cell | before | after | why |
|---|---|---|---|---|
| `tally_contracts` | population | 107 tables | **122** | the tally emits fifteen more |
| | compared | 577 (321 + 256) | **622 (366 + 256)** | 45 more table checks for the fifteen new tables |
| | teeth | 11/11 | **13/13** | the two new teeth |
| `recomputation` | population | 107 tables | **122** | as above |
| | compared | 15 122 | **16 276** | the 1 154 new cells |

Every other cell of both documents — 19 426 of them — is present with the same value, keyed by
construction, configuration, source, row and column. The four figures above are restated in §4.1
and §4.4 of the report, each with its previous value beside it.

**What the preservation check now proves, and how.** A merged cell would have defeated a
whole-row containment: the old row's `BR mean` and `BR [min, max]` no longer exist as columns.
The check therefore puts each old row **through the same declarations the renderer used** — the
layout's `merges` (using the renderer's own `_merge_cells`), its `bold`, and its `blank_repeats` —
and then looks for the result. A merge that dropped a part, swapped two parts or changed a value
would not reproduce the cell, so the parts are still proved present, in the same row, with the
same values. Three further defects in the check were found and fixed on the way: it indexed new
grids only by the stage tables they combine (so a document that already printed combined grids
matched nothing — 1 690 rows read as "missing"); it could not find the construction line under a
table printed as several blocks; and it resolved a column key only through the stage records'
headings, not through a heading a layout had already renamed.

---

## 6. Autonomous decisions, each with its reversal

| # | decision | reversal |
|---|---|---|
| 1 | The V3 shapes that need cells the tally does not emit (T4.1, T4.2, T4.3, T4.6, T5.3, T5.5, T5.7 in V3's form, T5.8, T5.9, T5.11, T4.4) were **not built**; the effort went to the three tables the user gave as images and to the cell formats across every table | Each is specified in §7; building one is a tally construction, an analysis twin and a layout, and adds cells the recomputation gate covers automatically |
| 2 | `node calls per module` moved from §4 to Appendix D.9 rather than being deleted or kept beside the sweeps table | Move its layout's `where` back to `"main"` and restore the marker pair; the prose already cites both |
| 3 | The configuration is a **bold sub-heading row** in the stacked appendix tables, not a blanked first column (deviation 7) | `blank_repeats` exists and takes a column key; a layout that wants the V3 form declares it |
| 4 | `nof`, not `tok`, in the block heading lines (deviation 4) | One entry in `plan_tables.SHORT_NAMES` |
| 5 | A single-mode layout now names itself by its **layout title** and prints a `combining 1 stage table(s)` line, because a layout that selects rows or merges cells would otherwise print the stage table's name over a grid that is not the whole of it | Revert the two lines in `_combine`; the preservation check indexes by both names and would keep working |
| 6 | The self-check's scratch tally tables were given the columns their layout declares, rather than relaxing the renderer's refusal for an absent merge part | Relax `_apply_merges` instead — but then a layout that has fallen behind the tally renders silently, which is what the refusal exists to prevent |
| 7 | `tables.sweep_cell` fixes one spelling for a sweep count (four significant figures, never scientific, the nearest integer above 1 000) rather than each table choosing | One function, in `tables.py` beside `CELL_SEPARATOR`, for the reason that module already gives |

---

## 7. What is not built, and what each needs

Eleven of the specification's tables. Each is one tally construction, one independently written
analysis twin, one `Layout`, and a caption; none needs a PROCESS run, and gate `recomputation`
covers the new cells the moment both sides emit them.

| | table | what it needs |
|---|---|---|
| a | **T4.1** check 1, matched accuracy | A new construction with rows the three configurations and columns `AR / A0 / A1 / A2` as `median / p90`, plus ratio-and-verdict columns. The verdicts exist — `tally_evaluation`'s record carries `similarity_verdicts` per pair and ruler — but they are **not in any table**, so they are new cells. Not a reshaping of D.5, which is rows × (arm, ruler) and carries six columns D.5 alone has |
| b | **T4.2** per-call cost | Rows the configurations, columns the arms as **mean node calls per evaluation with the bracket in one cell**, ratio columns `AR→A0`, `A0→A1`, `A1→A2`, and prime calls per evaluation. Every value is in D.4; the shape is a new construction because D.4's rows are arms |
| c | **T4.3** full distributions | D.5's min/median/max plus two cells the tally does not compute: **`Σ components > τ`** summed over the runs and the **worst run**, both from each run's `audit_residual.json` (`rulers.<ruler>.n_above` is there per run), and the sweeps and node-call **ranges** |
| d | **T4.4** module scope | Static: the committed node map's modules, their DSM rows, whether iterated, and which nodes execute per configuration. Every input is in `harness/data/dsm_node_map.json` and the per-run artifacts; no run record is read for the row counts |
| e | **T4.6** the excluded namespaces | The p90 across runs of the per-run maximum scaled residual **per excluded namespace**, from each run's `audit_residual.json` (`scaled` is keyed by `namespace.field`, `excluded_keys` names the excluded ones). Rows configuration × arm, columns `restricted` then one per namespace |
| f | **T5.3** location diagnostic | **Feasible**: the records carry the accepted design vector (`mfile.itvars`) and `itvar_names`, so the max relative difference over iteration variables matched **by name** is computable, with the argmax named and the shared/extra variable counts. D6's sentence goes in the caption verbatim: *a diagnostic, never an acceptance* |
| g | **T5.5** identity, `B1 → B2` | Evaluations identical, iterations identical, `norm_objf` bit-identical, over both-accepted pairs. The counts partly exist as D.12's *ε = 1 on* column; the bit-identity of `norm_objf` is a new cell and needs the hex, which the records carry |
| h | **T5.7 / T5.8 / T5.9** cost sums, both anchors, sweeps and prime calls | T5.7 and T5.8 are rows configuration × set with the **arms as columns** and summed solve-phase node calls — D.13 has every value with arms as rows. T5.9 needs `n_model_calls` (the sweep count, I-26) and `n_arrangement_method_calls` per arm, with `prime/sweep` and `prime/node`; both fields are in every optimisation record |
| i | **T5.1 / T5.2 into the main text** | The specification places the taxonomy and the same-optimum table in §4.3 beside their discussion. They are built (D.10, D.11) and correctly formatted; only the placement and the prose re-cut remain |
| j | **T5.11** problem definition | `i_figure_merit`, objective, sense, `nvar`, `n_constraints` (eq / ineq) and pulsed, all stamped on every optimisation record; the objective name comes from the `FiguresOfMerit` enum in the frozen tree |

---

## 8. Limits

1. **The per-module total's `models` is 49, not the map's 52.** Three collapsed-DSM rows belong to
   nodes that execute on no configuration of this experiment. The caption of every per-module table
   states both numbers. Resolving it needs the per-node DSM row attribution trap T9 forbids reading
   live; nothing here is affected but the total, which is already an interval.
2. **The `[v = 1, v = 0]` interval is a bracket over an unknown, not an uncertainty.** It brackets
   two defensible attributions; the true attribution is one of them or neither. No per-module ratio
   depends on it, and no acceptance quantity is read from any cell of these two tables — both
   captions say *reported, not accepted on*.
3. **The evaluation-phase block heading reads `n = 100`**, the finished runs of that configuration
   across all four arms in the source, not the previous revision's `n = 25` per arm. The per-arm
   denominator of the ratio is the `pairs` column (25). This is the table's own denominator with
   what it counts beside it (trap T11); a bare `25` would be a count over a population the table is
   not over.
4. **The cell-preservation check compares rendered strings.** Two cells that render identically and
   differ in the eleventh digit would pass it. The check against a changed *value* is gate
   `recomputation`, which compares raw numbers without tolerance; the two together are the proof.
5. **The four remaining lines of `report_counts_check.py` still differ** — the crash-class split,
   the stencil budget of the plan, and the second nonzero-mismatched PASS row. All four differed at
   the base and are the bookkeeping notes A80 recorded; none is a cell of a table.

---

## 9. What should change elsewhere (proposals; the queue and TRAPS are not this task's to edit)

**Harness plan, Appendix A, amendment 30 — proposed text.**

> **30. The report's tables are the V3 report's tables (task A85 (v3-table-formats), the user's
> ruling of 2026-09-15, [`docs/plans/REPORT_TABLE_FORMATS.md`](../../docs/plans/REPORT_TABLE_FORMATS.md)).**
> A `Layout` declares not only which stage tables become one table and where it goes, but **how a
> cell is spelled**: `merges` puts a mean and its seed bracket in one cell and a median and its p90
> in one, collapsing to the bare value where every run agreed; `select` takes a declared, disjoint
> set of a stage table's rows, so a construction the previous revision published as several tables
> of one quantity renders as several tables; `blocks` prints one grid per configuration under a
> bold heading line; `bold` marks the result column and the verdict; `blank_repeats` blanks a
> repeated key on continuation rows. **Rule xvi:** a layout that names a column its tables do not
> have is a refusal, never a skipped declaration; and a rendering change is proved by
> `report_cells_preserved.py`, which puts each old row through the same declarations before
> looking for it — so a merge that dropped or swapped a part does not pass.

**`harness/README.md`** — done on the branch (§0's `plan_tables` paragraph states the five V3
forms and the preservation argument; the Appendix D row of §13's table no longer says "the three
headline tables").

**TRAPS — proposed addition to T17** (the orchestrator's to make): *a citation that names a table
by number and by construction survives a renumbering; one that names only a number does not, and
three such citations survived two re-pointings in this report before A85 found them by re-reading
every one. When the table set changes, re-read every numbered citation and ask what the sentence
is about, not only whether the number resolves — `--plan-tables check` reports a dangling number,
never a plausible wrong one.*

**For the queue (a proposal, not a minting).** The eleven tables of §7 are one further task's work
— `A86 (v3-tables-remainder)` would be the obvious keyword — and it is mechanical: each is a tally
construction, an analysis twin, a layout and a caption, with zero PROCESS runs and the same five
verification presses.

---

## 10. Change log

| commit | what |
|---|---|
| `d6e8c229` | `stats.module_sweeps`, `stats.dsm_rows_by_group`, `stats.weighted_total`; `tables.sweep_cell`; the `module sweeps per run` table in both tally phases and both analysis twins |
| `548082b2` | two teeth for `tally_contracts` |
| `a5e180be` | the renderer's V3 forms (`Merged`, `select`, `blocks`, `bold`, `blank_repeats`) and the layouts that declare them; `report_cells_preserved.py` made transform-aware |
| `10970557` | the main text's markers and the two new discussion paragraphs; `report_citations_repoint.py` rewritten and executed |
| `94206ffa` | §4.1 and §4.4's gate counts and `report_counts_check.py`'s constants |
| `ca2d0033` | the self-check's scratch tally tables given their layout's columns |
| `3aa1ffb8` | `harness/README.md` §0 |
