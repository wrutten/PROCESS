# A87 (v3-grid-polish) — the three grids that were still not the previous revision's

> **Document status** — **OPEN.** Task **A87 (v3-grid-polish)**, branch `A87-v3-grid-polish`
> (worktree `.claude/worktrees/A87-v3-grid-polish`), base `f1848d63`, tip **`91098b8c`** —
> **which is the last commit that touches code or a generated document, and is where every gate
> verdict this report cites was pressed** (rule xiii); the only commit after it is this document.
> Work list: A86 (v3-tables-remainder)'s orchestrator assessment, paragraph *"Two grids still not
> V3's"*. Specification: [`../plans/REPORT_TABLE_FORMATS.md`](../plans/REPORT_TABLE_FORMATS.md)
> (RULING, 2026-09-15). **Zero PROCESS runs**; `EXECUTION_APPROVED` untouched; no file under
> `MDA_partitioning_experiment_v4/PROCESS/`, `harness/child/` or the root `process/` changed.
> Arm names are today's (`AR/A0/A1/A2`, `BR/B0/B1/B2`); the records stamp the names of their day
> and `records.read` translates (trap T16).

---

## 1. Verdict

**The three grids are the previous revision's, and no cell moved out of the documents.** This is a
rendering task and it changed nothing else: not a construction, not a stage record, not a number.
**1 958 rows and 20 917 cells preserved, 0 missing and 0 differing** against `f1848d63`.

| | the grid before | the grid now |
|---|---|---|
| **Table 11**, §4.3 | per-arm success **merged** with the failure taxonomy and the seed set — 23 columns, 20 printed, three of them one label repeated down a configuration's rows | **per-arm success alone, 8 columns**, the configurations stacked, in the previous revision's §5.1 form. The merge is **Table D.12**, first of Appendix D's optimisation-phase group, whole |
| **the stacked tables' sub-heading rows** | `large_tokamak_nof · campaign_optimisation · BR·B0·B1·B2 — n = 22 (seeds on which every arm of large_tokamak_nof converged)` | `**large_tokamak_nof (n = 22)**`. The tally's table name is the construction line under the grid; the population sentence is in the caption |
| **Table 7**, §4.2 | `A2/A1 med` \| `A2/A1 p90` \| `A2/A1 verdict` \| … \| `verdict note` — 14 columns | `A2/A1 med, p90 → verdict` as **one cell**, `1.0000, 1.0000 → **PASS**`; the note in the caption — **9 columns** |

**The widest grid in §4 goes from 20 columns to 13** — and the 13 is Table 8, the per-call cost
ladder, not a bookkeeping table.

### 1.1 The census

Every line below is printed by `report_cells_preserved.py --base f1848d63` (protocol §15),
executed at `91098b8c`.

| | before (`f1848d63`) | after (`91098b8c`) |
|---|---|---|
| tables in §4 (main text) | 12 | **12** |
| tables in Appendix D | 21 | **22** |
| tables in the companion file | 15 | **15** |
| markdown grids in the report | 37 | **38** |
| grids in §4 | 16 | **16** |
| grids in Appendix D | 21 | **22** |
| markdown grids in the companion | 23 | **23** |
| **tables with one row** | **0** | **0** |
| **widest grid in §4**, in columns | **20** | **13** |
| widest grid in Appendix D, in columns | 25 | **25** |
| widest grid in the companion, in columns | 26 | **26** |
| stage tables the tally emits | 141 | **141** |
| cells the two implementations compare | 17 554 | **17 554** |
| teeth in the gate table | 167 | **167** |

*The grid counts exceed the table counts because a blocks-mode table prints one grid per
configuration under one caption and one number. The one-row count is 0 before and after: A83's
rule holds.*

**Nothing new was computed.** The tally emits the same 141 tables over the same 949 campaign run
records made at `57dc0c14`; gate `recomputation` compares the same 17 554 cells. The task added no
construction, no cell and no tooth.

### 1.2 The cells that now appear in two tables, and why the check accepts them

The main text's Table 11 and the appendix's Table D.12 are built from the **same three stage
tables** (`per-arm success — <configuration> — campaign_optimisation`). That is a deliberate
republication and it is declared: `Layout.shares_tables_with` names the other layout, mutually, and
`_layout_for` refuses two claims on one stage table unless each names the other. The preservation
check counts it and prints it:

```
stage table(s) rendered into more than one grid (declared; a cell may appear twice, it may
never be lost or changed):
  'per-arm success' (§4.3): 3 stage table(s) it shares with ['reliability_and_taxonomy'],
      11 row(s), 88 cell(s) of which 66 carry a value
  'per-arm success, the seed set and the failure taxonomy' (§D.3): 9 stage table(s) it shares
      with ['per_arm_success'], 11 row(s), 220 cell(s) of which 196 carry a value
```

**Why the check accepts it.** `report_cells_preserved.py` keys a cell by *(construction,
configuration, source, row, column)* and looks for each old row inside **every** new grid that
names its stage table — `where[name]` is a list, not a single host — so a stage table hosted twice
is found in either. The rule it enforces is not *every cell exactly once*; it is **no cell lost and
no cell changed**. Publishing a cell twice breaks neither. What it would break is a cell that
differs between the two renderings, and that cannot happen here: both grids copy the constituent's
own rendered cells, and the 88 cells of Table 11 are 88 of Table D.12's 220.

**The cost of the duplication is one grid of 11 rows** in the main text, in exchange for the
argument's paragraph reading an 8-column grid instead of a 20-column one.

---

## 2. What was done, item by item

### 2.1 Table 11 — the merged whole leaves the main text

The construction `per_arm_success` is now claimed by **two** layouts:

| layout | where | mode | what it renders |
|---|---|---|---|
| `per_arm_success` | §4.3, **Table 11** | `stack` | the per-arm success stage tables **alone**, configurations as row groups |
| `reliability_and_taxonomy` | Appendix D, **Table D.12** | `merge` | the same three, merged with the failure taxonomy and the seed set — the table that used to be Table 11, unchanged |

The appendix layout keeps the **title** the old main-text table printed (`per-arm success, the seed
set and the failure taxonomy`), so the preservation check finds the old grid by name without a
translation; only the layout's `name` changed, which is the marker key, and the marker in the
report is still `per_arm_success` — so no marker moved.

**The main text's grid, and how it maps onto V3 §5.1.**

| V3 §5.1 | Table 11 |
|---|---|
| `config` | the bold sub-heading row (`**large_tokamak_nof (n = 25)**`) — the stage tables have no `configuration` column, and a stack's row group is where the renderer puts a configuration |
| `invalid seeds` | Table D.12's *configuration-invalid seeds*, and the seeds themselves in companion Table F.6 |
| `arm` | `arm` |
| `ok` | `accepted optima` (status ok **and** `ifail == 1` — V4's finer definition) |
| `converged (ifail = 1)` | folded into *accepted optima*; the starts that finished without one are `finished, ifail = 5` |
| `not-converged among ok` | `finished, ifail = 5` and `coupling-loop cap (ModuleSolveFailure)`, which V4 distinguishes and V3 did not |
| — | `starts offered`, `crashed (RuntimeError)`, `lost, another arm accepted`, `seed set` — V4's own |

The seed set is the last column, **stated once at the head of each configuration's arm rows and
blank below** (`blank_repeats`), which is the previous revision's own convention for a value that
repeats down consecutive rows (`REPORT_TABLE_FORMATS.md` §0). See decision 3 below for why it is
not in the caption.

**The prose.** §4.3's *"The population"* paragraph reads the grid it always read and stays where it
is; it also reads the taxonomy's tracebacks, the configuration-invalid seeds and the retried seeds,
which are now Table D.12's, so its citation names both tables. Three further sentences were citing
Table 11 for columns it no longer carries (§4.4 below).

### 2.2 The stacked tables' sub-heading rows

`_group_label` now prints **the group and its own n, and nothing more**:

- `**large_tokamak_nof (n = 22)**` where one table holds one source regime;
- `**large_tokamak_nof · campaign_displaced (n = 100)**` where it holds more than one (Appendix D's
  cost per call, matched accuracy, fixed-point distance, the ownership rung, the evaluation
  phase's taxonomy);
- `**campaign_stencil_forward (n = 198)**` where the construction is already over the
  configurations;
- `; arms BR·B0·B2` appended **only** where the group is not the phase's whole ladder — the
  previous revision's `st` block, whose heading said *"no B1"*. That rule and its helper are now
  shared with `_block_label`, so a block heading and a sub-heading row say the same thing the same
  way.

**Where the two halves went.** The tally's table name (`campaign_optimisation · BR·B0·B1·B2`) is
already under the grid, on the `combining N stage table(s)` line the renderer prints for every
combined table — the stable citation (trap T17). The population sentence is now **generated into
the caption**: `_denominator_is` collects the constituents' own `denominator_is` strings, replaces
the configuration named inside each with *that configuration*, and prints the distinct ones once:

> n = 3 (row group(s) of this table, each over its own population and never pooled; a group's
> sub-heading row names its configuration and its own n, and that n counts seeds on which every arm
> of that configuration converged).

Nothing is typed by hand and nothing is rewritten in a record. **A85's deviation 7** argued the long
row carries three things a blank first column cannot; the answer, as for the block headings at A86,
is that two of the three belong above and below the grid rather than inside it.

Applied to **twenty** stacked tables across the report and the companion.

### 2.3 Table 7 — the ratio triples as one cell

A new declared cell join, `Merged(join="verdict")`, prints `med, p90 → **verdict**`:

| | Table 7's `A2/A1` cell |
|---|---|
| `large_tokamak_nof` | `1.0000, 1.0000 → **PASS**` |
| `low_aspect_ratio_DEMO` | `—, — → **PASS**` |
| `st_regression` | `—` |

The join emboldens the verdict and nothing else, which is how V3 printed it (`0.76, 5.64 →
**PASS**`); a verdict **already** bold is left alone, so the join gives the same string on a stage
record's raw cell and on a cell an earlier rendering already published — which is what lets the
preservation check put the old row through it and find the new one. A triple whose parts are all
missing reads a single `—`; a triple with a verdict and no ratio reads `—, — → **PASS**` (see
deviation A87-2). The `bold` declaration on the two verdict columns was removed, because those
columns no longer exist after the merge.

The `verdict note` column is dropped into the caption (`omit`): 3 cells, **none of which carries a
number**. Two of the three said *declared pair A2/A1* and *declared pair A2/A0*, which the
`reference` column already says in every row; the third is the trivially-similar clause on
`low_aspect_ratio_DEMO`, and the caption now states it in full.

**Table 7 ends at 9 columns**: `configuration | n (runs) | AR | A0 | A1 | A2 | reference |
A2/A1 med, p90 → verdict | A2/A0 med, p90 → verdict`. V3's is 7. The two extra are kept, one line
each:

- **`reference`** — V4 declares the acceptance pair **per configuration** (`A2/A1` on a pulsed
  configuration, `A2/A0` on `st_regression`), so a grid with two ratio columns must say which of
  them is the acceptance on each row; V3 had one ratio pair and needed no such column.
- **`n (runs)`** — kept, and listed in §5 as *noticed and not done*: its cells are three different
  numbers (100 / 100 / 75), and `omit` states a column in the **caption**, which is hand-written —
  moving a measured number there would be a published number not produced by a script (§15).

### 2.4 The declarations this needed

Four additions to `plan_tables.py`, all data, all rendering:

| declaration | what it says | its refusal |
|---|---|---|
| `Merged(join="verdict")` | a ratio at two quantiles and the verdict read against it, in one cell | an unknown join is named and refused |
| `Layout.column_order` | the order a combined grid's columns print in, by key | a key the constituents do not have |
| `Layout.shares_tables_with` | the other layouts this one deliberately shares its stage tables with, **mutually** | a second claim on a stage table that is not mutual falls back to the `select` rule and is refused |
| `Layout.per_seed_columns_in` | the layout whose companion full version already prints this one's per-seed columns | a name that renders no full version — *"a column left out of both documents is a cell lost"* |

`column_order` earns its place: the union of the three per-arm-success stage tables' columns puts
`crashed (RuntimeError)` (which `large_tokamak_nof` has) before `lost, another arm accepted` and the
two classes only `low_aspect_ratio_DEMO` and `st_regression` have *after* it — the outcome classes
split around a column that belongs to the right of all of them. The order is now declared, not an
accident of which configuration exhibits which class first.

`per_seed_columns_in` earns its place too: without it the main text's Table 11 would have rendered
a **second** companion full version, a strict column-subset of Table F.13. It names F.13 instead,
and the companion's grid count is unchanged at 23.

---

## 3. Deviations from the V3 grids, all of them in one place

Every place a V4 table is not the V3 table, one line each. **A85's and A86's are carried forward**
so the merged report's deviations are listed here and nowhere else.

### 3.1 Named in the specification (A85's §3.1, unchanged)

| V3 | V4 | what differs | why |
|---|---|---|---|
| T4.5, T5.10 columns `A0 / A1u / A1`, `R / B0 / B1 / B2 / B3` | `AR / A0 / A1 / A2`, `BR / B0 / B1 / B2` | `A1u` and V3's `B2` dropped, `AR` and `A1` added | `A1u` is not run in V4 (the prime is inside the intervention); V3's `B2` was removed by D22; `AR` and `A1` are V4's reference and ownership rungs. The specification's §0 translation, applied |
| T4.5 ratio against `A0` | ratio against `A1` on a pulsed configuration, `A0` on st | the declared reference arm changed | V4 declares the reference per configuration (`tally_evaluation.reference_arm`); the *reference* column names it in every row |

### 3.2 Introduced at A85 (v3-table-formats), carried forward

| # | V3 | V4 | what differs | why |
|---|---|---|---|---|
| 1 | T4.5 / T5.10 rows `M1, M2, M3 live, vacuum, PULSE, FF` | `M1, M2, M3, PULSE, once per run` | V4 groups the configuration's own deferred nodes into one *once per run* row | V4's existing derived grouping (`stats.node_groups`), already used and already gated; the caption names the row's nodes |
| 2 | `models` total 52 | 49 | three collapsed-DSM rows are attributed to no group | Those are FF's rows whose nodes execute on no configuration; each caption states the map's 52 and the configuration's 49 |
| 3 | total ratio bracketed over `vacuum`'s row | bracketed over the whole once-per-run group's rows | the unknown is three or four rows, not one | Follows deviation 1 |
| 4 | configurations abbreviated `tok / lad / st` | `nof / lad / st` | the first configuration's short name | The V4 report writes `nof` throughout §4–§6; a table renaming it would be one the prose cannot cite |
| 5 | numbers spaced (`102 868`) | unspaced (`96933`) | no thousands separator | The existing V4 cells carry none, and a separator inside a cell makes the committed cell-preservation comparison presentation-sensitive |
| 6 | T5.4 columns `n, R, B0, B3, ratios` | closed at A86 | — | the constant `quantity` column is in the caption (`omit`) |
| 7 | cross-configuration tables blank the configuration on continuation rows | **closed here** — see A87-1 | the sub-heading row carried three things | The tally's table name went to the construction line and the population sentence to the caption, as A86 did for the block headings; what is left is the configuration and its n |
| 8 | V3 §5.2.1 has `within-cluster med / p90 / would accept` | V4's same-optimum table has `below resolution` | a different companion construction | V4 never built the within-cluster construction; `below_resolution` is what it has |
| 9 | node calls per module was §4.3's table | Appendix D.14 | the node-call per-module table left the main text | Its sweeps twin (Table 18) is the previous revision's headline; keeping both in §4 would be the same grid twice in two units |

### 3.3 Introduced or closed by A86 (v3-tables-remainder), carried forward

| # | V3 | V4 | what differs, and why |
|---|---|---|---|
| i | T5.4 `B2/B0 mean` — the ratio of the means | **closed.** `B2/B0 mean` is the ratio of the means; the mean of the per-seed ratios is renamed beside it, carried as a declaration (`RENAMED_HEADINGS`) | A V3-shaped table with a V3 heading over a different statistic |
| ii | T5.10 `runs B3 > B0` as one cell `0/22` | **closed.** One cell `k/n` by a `fraction` join | It was two columns |
| iii | block heading `tok` (n = 25) | **closed.** `**\`nof\`** (n = 22)`, the population sentence in the caption, the per-arm count declared (`Table.block_denominator`) | The evaluation table's own denominator is over four arms |
| iv | T5.4 has no `quantity` and no `arms` column | **closed.** Both in the caption (`Layout.omit`, 24 label cells) | They are labels, not numbers |
| v | `vacuum` and `FF` rows | one `once per run` row, its nodes named in the caption | A85's deviation 1 accepted at assessment with this addition |
| vi | `M3 live` | `M3` | V4's `M3` group is already the live one; the name is the committed node map's key |
| vii | `tok` | `nof` | as deviation 4 |
| viii | V3's §4 check-1 grid has no stencil rows | Tables 7 and 8 carry the displaced regime only; the stencil regimes are companion Tables F.1 and F.2 | Reproducing *that grid* means the acceptance regime alone. **A deviation from the specification, not from V3** |
| ix | V3 §5.2.2 repeats check 1's verdict column | Table D.15 repeats the median and p90 and **not** the verdict | Repeating a verdict in two tables is two places for it to go stale |
| x | V3 §5.1 is six columns | Table 11 was twenty-three | **closed here** — see A87-1 |
| xi | — | a merged `median / p90` both of whose parts are missing reads `— / —`, not `—` | A collapse that rewrites an already-published string was withdrawn at A86; a rendering change may move a cell, never rewrite one |
| xii | V3 §5.5 publishes **ok** and **converged** seed sets | Table 17 publishes *every arm accepted* and *without retried seeds* | V4 has one acceptance set; the caption says which |

### 3.4 Introduced or closed by this task

| # | V3 | V4 | what differs, and why |
|---|---|---|---|
| **A87-1** | §5.1 is `config \| invalid seeds \| arm \| ok \| converged \| not-converged`, six columns; cross-configuration tables blank the configuration on continuation rows | **closed.** §4.3's Table 11 is per-arm success alone in that form, eight columns, the configurations as **row groups** under `**large_tokamak_nof (n = 25)**`; the merge with the taxonomy and the seed set is Table D.12. Sub-heading rows everywhere carry the group and its n and nothing more | A82's per-arm success **is** V3's grid with V4's finer classes; what made Table 11 unreadable was the merge, and that is a placement question, not a width one (A86's Limit 1 called it width). The configuration is a row group rather than a blanked first column because the stage tables have no `configuration` column — the renderer's `stack` is where a configuration goes — and A85's deviation 7 is closed the same way A86 closed the block headings: the tally's table name below the grid, the population sentence above it |
| **A87-2** | T4.1 prints `both exactly 0 → **PASS**` where the ratio is 0/0 | `—, — → **PASS**` | V3 wrote a phrase into the cell; V4's `A2/A1 med` and `p90` cells **already read `—`** on that row and a rendering change may move a cell, never rewrite one (A86's deviation xi, the same rule that withdrew `— / —` → `—`). The caption carries V3's sentence: *"on `low_aspect_ratio_DEMO` both quantiles of both pairs are exactly 0, so the ratios read `—` and the pair passes under the trivially-similar clause, not on a measured ratio"* |
| **A87-3** | T4.1 has no `verdict note` column | dropped into the caption (`omit`, 3 cells, no number among them) | The *reference* column says which pair is declared, which is two of the three notes; the third is the trivially-similar clause and the caption states it |
| **A87-4** | T5.1 collapses arms with identical counts into one row (`R / B0 / B1 / B2 / B3 · 22 each`) | four rows on `large_tokamak_nof`, each reading `22` | **Not done, deliberately.** Collapsing four rows into one and writing *22 each* rewrites cells; the preservation rule forbids it (§5, item 1) |
| **A87-5** | T5.1's `invalid seeds` carries the seed numbers (`3 (5, 20, 21)`) | the count is Table D.12's *configuration-invalid seeds*; the seeds are companion Table F.6 | Putting the seed numbers back into the main grid puts the merged table back |

---

## 4. Verification

The sequence, worktree root, tree clean and committed at **`91098b8c`** at every step, nothing else
running. **Zero PROCESS runs.**

| # | step | result |
|---|---|---|
| 1 | `--measure all --resume` | five stages re-pressed (`tally_evaluation` **93** tables, `tally_optimisation` **48**, `recomputed_tables` **141**, `gate_table`, `exclusion_review`); **0 runs made** |
| 2 | `--plan-tables write` | both documents written; **12 + 22 + 15** tables, 43 632 cells |
| 3 | `--plan-tables check` | **IDENTICAL** for all twelve §4 blocks, Appendix D (1 152/1 152 lines) and the companion (1 705/1 705); **0 dangling** references |
| 4 | `--gate recomputation --resume` | **PASS** at `91098b8c` — 141 tables, **17 554 compared, 0 mismatched**, 9/9 teeth |
| 5 | `--gate tally_contracts --resume` | **PASS** at `91098b8c` — **679 compared (423 table checks + 256 reference cells), 0 mismatched**, **17/17 teeth** |
| 6 | `--gate run_kind_separation --resume` | **PASS** at `91098b8c` — **3 000 compared, 0 mismatched**, 9/9 teeth |
| 7 | `--gate self_containment --resume` | **PASS** at `91098b8c` — **52 files, 0 mismatched**, 1/1 tooth |
| 8 | `--measure gate_table --resume` | **30 PASS, 0 FAIL, 167 of 167 teeth tripped** |
| 9 | `--plan-tables write`, then `check` again | **IDENTICAL** everywhere, **0 dangling**; nothing re-rendered, `git status` empty |
| 10 | `--selfcheck` | **PASS** |

### 4.1 The stamps

| verdict | `tree_git_head` | is that the tip's code? |
|---|---|---|
| `recomputation` | **`91098b8c`** | yes — the tip |
| `tally_contracts` | **`91098b8c`** | yes — the tip |
| `run_kind_separation` | **`91098b8c`** | yes — the tip |
| `self_containment` | **`91098b8c`** | yes — the tip |

`91098b8c` is **the last commit that touches code or a generated document**: the only commit after
it is this report. One earlier press is superseded and this report cites none of it — the four
gates were pressed at `10af6a16`, before the report's Appendix C entry and the preservation check's
census additions, with identical numbers; every verdict was pressed again at the tip.

The `gate_table` stage record's `records_read` names the commit of each of the thirty verdicts it
read: **4 at `91098b8c`** (the four above — the only gates this task's change alters what they
read) and 26 at the commits they were pressed at in the seeded records tree — `8996b843` 23,
`6f5ba612` 2, `350a58c4` 1 — which is the records-reuse rule.

The two tally stage records and `recomputed_tables` carry no commit of their own by design: a stage
over **run** records is provenanced by `runs_provenance`. All three were re-pressed at `91098b8c`
in steps 1 and 4–5.

### 4.2 The standing checks

| check | result |
|---|---|
| `report_cells_preserved.py --base f1848d63` | **1 958 of 1 958 rows and 20 917 of 20 917 cells preserved** (15 785 carrying a number); **0 missing**; **0 differing** |
| | **3 cells** (the *verdict note* column, none of them a number) stated in a caption instead of once per row, declared (`Layout.omit`) and counted by name in the output |
| | **11 rows / 88 cells** (66 carrying a value) republished, declared (`Layout.shares_tables_with`) and printed |
| `run_stamp_survey.py`, before and after the whole press | **1 102 records**, the same nine commits, 949 at `57dc0c14`; byte-identical output — **0 re-made, 0 new** |
| `report_counts_check.py` | runs; **4 lines differ**, the same four that differed at the base (A86's Limit 7) |

**0 differing rows, and none expected.** A86 had two — the gate table's own, whose populations
grew. This task adds no table and no tooth to the tally, so the gate table's cells are the same
cells.

### 4.3 The citations, re-pointed and re-read

`report_citations_repoint.py` was rewritten for this move and executed (protocol §15). It works
from a **map of layout → old number → new number**: Appendix D from D.12 on rose by one, and the
companion's full versions re-ordered because the main text's table no longer renders one of its own
(F.10 → F.13, F.11 → F.10, F.12 → F.11, F.13 → F.12). **No main-text number moved** — the new grid
took the merged table's slot.

- **22 numbers moved**, all in Appendix D citations.
- **Five phrases**, four of them the T17 addition — *a number that still resolves can still be the
  wrong table*. Table 11 is still called *per-arm success* and is still in §4.3, and three
  sentences were citing it for columns it no longer carries:

  | where | was | is |
  |---|---|---|
  | §3's *inner cap* row | the `ModuleSolveFailure` **message**, Table 11 | *"Table 11; the message is Table D.12's"* — the traceback is the taxonomy's `detail` column |
  | §4.3's *"The population"* heading | Table 11 | *Tables 11 and D.12* — the paragraph reads the tracebacks and the configuration-invalid seeds too |
  | §4.3, the `ifail = 5` sentence | *"counted **ok** in Table 11"* | *"counted **ok** in Table D.12"* — `ok` is the failure taxonomy's column and was never a column of per-arm success |
  | §4.3, the retried-seed sentence | Table 11 | *Tables 11 and D.12* — *retried seeds per arm* is the seed-set table's column |
  | §4.4 | *"Tables D.2–D.21"* | *"Tables D.2–D.22"* |

- **Every numbered citation in the document was then re-read**, one by one, against the table it
  now names — 68 to §3/§4, 72 to Appendix D, 21 to the companion. `--plan-tables check` reports
  **0 dangling**, which is the weaker check and is not what found the four above.
- **Appendix C is held out of the sweep** (A86's decision 8, trap T17's second addition): its
  entries state the table set of their own day. This task's entry, written by the task, states
  today's.

**Three stale citations were also found inside the renderer's own generated text** — held out of
the citation sweep because they sit in a rendered block, and therefore never swept:

| where | was | is |
|---|---|---|
| Appendix D.2's context paragraph | *"node calls per block … is **Table 7** in §4.2"* | **Table 9** — it has been Table 9 since A86 reordered the main text |
| Appendix D.3's context paragraph | *"the phase's two headline tables … are **Tables 8 and 9** in §4.3"* | the five headline tables named by their numbers (11, 12, 13–16, 17, 18) |
| `report_counts_check.py` §9 | *"companion **Table F.13**'s hex columns"* | **Table F.5** — the exit-audit-on-both-rulers columns are the predicate trial's |

Two further labels in `report_counts_check.py` were corrected (§2's *Table D.5: nvar per arm* →
*Table D.13: vars per configuration*; §7's *Table D.19's cell* → *Table D.20's*).

---

## 5. Not V3's grid, noticed and **not** done

The brief's instruction. Each of these is a departure from the previous revision's grids that this
task saw and left alone, with the reason.

1. **Table 11 does not collapse arms with identical counts.** V3 §5.1 printed
   `R / B0 / B1 / B2 / B3 | 22 each` as one row; Table 11 prints four rows of `22` on
   `large_tokamak_nof`. Collapsing them rewrites four cells into one and invents the word *each* —
   a rendering change may move a cell, never rewrite one (deviation xi's rule). It would also make
   the grid's rows disagree with Table D.12's, which must keep them because the taxonomy's
   tracebacks differ per arm.
2. **Table 7 keeps `n (runs)`** (100 / 100 / 75). V3's grid had no `n` column because every row was
   over the same 25 seeds and its caption said so once. V4's rows are over different populations, so
   the column carries three different **numbers** — and `omit` states a column in a hand-written
   caption, where a measured number does not belong (§15).
3. **Table 8 is 13 columns against V3's 7**, and is now the widest grid in §4. V4's ladder has three
   rungs where V3's had one (`AR→A0`, `A0→A1`, `A1→A2`, with `A0→A2` standing in on st) and carries
   the prime calls per evaluation as a cell where V3 named them in prose. Narrowing it means
   dropping a rung.
4. **The merge-mode sub-heading rows are not reduced.** Tables D.4 (the reference entries) and D.12
   still read `**large_tokamak_nof — 3 construction(s): \`per-arm success\` n = 25;
   \`failure taxonomy\` n = 100; \`the seed set\` n = 25**`. A merge group has three constructions
   with **three different denominators**, so there is no single `n` to put in `(n = …)`; moving them
   to the caption means nine numbers there, hand-written. Both tables are now the appendix's
   bookkeeping tables, which is the reason the main text's grid was separated from them.
5. **Appendix D.4 is 25 columns**, the widest grid in the report — the reference entries merged from
   three constructions. The same shape as Table 11's problem and the same answer would apply
   (per-arm grid in the text, merge in the appendix), but it is already in the appendix and no
   paragraph reads it as a grid.
6. **Several appendix tables keep an `n` column whose value is also in the sub-heading row.**
   Dropping it is a cell removal, not a rendering.
7. **Numbers are unspaced** (`96933`, not `96 933`) — A85's deviation 5, unchanged: a separator
   inside a cell makes the committed cell-preservation comparison presentation-sensitive.
8. **V3's `within-cluster med / p90 / would accept`** columns of §5.2.1 do not exist in V4 — the
   construction was never built (deviation 8).

---

## 6. Autonomous decisions, each with its reversal

| # | decision | reversal |
|---|---|---|
| 1 | **Two layouts share the per-arm-success stage tables** (`shares_tables_with`), rather than rendering the main text's grid from a `select` of rows or from a new tally table | Delete the main-text layout; Table 11 becomes the merged table again and the appendix loses D.12. Or: drop `shares_tables_with` and give the main text a `select` — which cannot work here, because the two grids take the same rows and different columns |
| 2 | **The appendix's merged table keeps the old title** and only its layout `name` changed (`per_arm_success` → `reliability_and_taxonomy`), so the preservation check finds the old grid by name and the report's marker does not move | Rename the title; `report_cells_preserved.py` then needs a title translation of its own, which it does not have |
| 3 | **The seed set is `blank_repeats`, not `omit`.** The brief offered "the caption or a sub-heading"; the caption is hand-written and the three values (22 / 11 / 22) are measured numbers (§15), and a sub-heading row carries the group's `denominator` (25 starts offered per arm), which is a different quantity. Blanking on continuation rows is the previous revision's own convention for a repeated value and states it once per configuration | Add `seed_set` to `omit` and write the three numbers into the caption; or declare a per-group second denominator in the tally (`Table.block_denominator`'s shape), which is a stage-record change and not a rendering |
| 4 | **The reduced sub-heading applies to `stack` mode only**, not to `merge` (§5, item 4) | Reduce `_merge`'s group label the same way and generate the nine per-construction n into the caption |
| 5 | **The population sentence in the caption is generated**, by normalising each constituent's own `denominator_is` (the configuration name → *that configuration*) and printing the distinct ones | Print them per constituent instead, which is the same text at nine times the length on the widest tables |
| 6 | **`Layout.per_seed_columns_in`**: the main text's Table 11 names Table D.12's companion full version rather than rendering a second, strictly narrower copy of it | Remove the field; the companion gains a sixteenth table that is a column-subset of F.13 |
| 7 | **`Layout.column_order`** is declared rather than left to the union order of the constituents | Remove it; the outcome classes split around *lost, another arm accepted* |
| 8 | **The three stale citations inside the renderer's generated text were fixed** (§4.3), although they predate this task | Revert those three strings; the appendix then points a reader at Table 7 for node calls per block |

---

## 7. Limits

1. **The same 88 cells are printed twice**, in Table 11 and in Table D.12. That is the price of the
   main text reading an 8-column grid, it is declared and counted, and the preservation rule it must
   not break — no cell lost, no cell changed — is not broken. A reader who counts cells across the
   two documents will count those 88 twice.
2. **`—, — → **PASS**` is an odd cell to read** (deviation A87-2). It is truthful — the ratio of two
   zeros has no value and the pair passes under a clause, not on a number — and the caption says so,
   but V3's `both exactly 0 → PASS` reads better. Fixing it means rewriting two published cells.
3. **The cell-preservation check compares rendered strings.** Two cells that render identically and
   differ in the eleventh digit would pass it. The check against a changed *value* is gate
   `recomputation`, which compares raw numbers without tolerance; the two together are the proof.
   Unchanged from A86's Limit 4.
4. **The widest grid in the report is still 25 columns** (Table D.4) and the widest in the companion
   26. Both are the appendix's and the companion's, where a wide grid is a reference rather than an
   argument.
5. **`report_counts_check.py` still differs on four lines** — the crash-class split, the plan's
   stencil budget, and the second nonzero-mismatched PASS row. All four differed at the base and are
   the bookkeeping notes A80 recorded; none is a cell of a table.
6. **A87-1's row-group choice is not literally V3's first column.** V3 wrote the configuration into
   column 1 and blanked it on continuation rows; this renderer hoists it into a bold group row.
   The information is the same and the renderer has no `configuration` column to blank — the stage
   tables do not carry one — but a reader comparing the two documents side by side will see a
   different first column.
7. **Three of the eleven `B1 → B2` pairs on `low_aspect_ratio_DEMO` still differ in the last bits of
   `norm_objf`** (issue **I-27**, opened at A86's merge). Not this task's; nothing here touches it.

---

## 8. What should change elsewhere (proposals; the queue and TRAPS are not this task's to edit)

**Harness plan, Appendix A, amendment 32 — proposed text.**

> **32. A grid is the previous revision's grid, and a cell may appear in more than one of them
> (task A87 (v3-grid-polish), the user's ruling of 2026-09-15,
> [`docs/plans/REPORT_TABLE_FORMATS.md`](../../docs/plans/REPORT_TABLE_FORMATS.md)).** A `Merged`
> may join a ratio pair and the verdict read against it into one cell (`verdict`,
> `0.76, 5.64 → **PASS**`, the verdict emboldened and a verdict already bold left alone so the join
> is the same on a raw cell and a published one); a `Layout` may declare the order its columns print
> in (`column_order`). **A sub-heading row carries the group and its own n, and nothing more** — the
> configuration, its source regime where one table holds more than one, the arm set only where the
> group is not the phase's whole ladder: the tally's table name is the construction line under the
> grid and the population sentence is **generated into the caption** from the constituents' own
> `denominator_is`, never typed. **Rule xviii:** two layouts may render one stage table when each
> names the other in `shares_tables_with` — a construction the report prints twice on purpose, a
> grid in the main text and a merge in the appendix. **A cell may appear in more than one table; it
> may never be lost or changed**, `report_cells_preserved.py` looks for an old row in every grid
> that names its stage table and counts the republication, and a layout whose per-seed columns
> another's companion full version already prints names that table (`per_seed_columns_in`) rather
> than rendering a second copy. A column dropped into a caption (`omit`) may carry a **label**; a
> measured number belongs in a grid, because a caption is hand-written and protocol §15 binds every
> published number to a script.

**`harness/README.md`** — done on the branch: §0's `plan_tables` paragraph states the reduced
sub-heading row, the `verdict` join, `column_order`, `shares_tables_with` and
`per_seed_columns_in`, and the rule that a cell may appear twice but never be lost or changed.

**TRAPS — proposed addition to T17** (the orchestrator's to make): *a citation sweep reaches only
the hand-written text. The renderer's own generated context paragraphs cite table numbers too —
Appendix D.2's and D.3's group contexts named Tables 7, 8 and 9 for tables that have been 9, 18 and
13–16 since A86 — and they sit inside the rendered block that every sweep holds out of its scope, so
no re-pointing has ever touched them and `--plan-tables check` does not resolve a bare `Table n`.
The rule: when the table set changes, grep the renderer's source for table numbers as well as the
documents.*

**For the queue (a proposal, not a minting).** Nothing of the specification remains, and nothing of
A86's assessment. Two items surfaced and are not this task's: the merge-mode sub-heading rows and
Appendix D.4's 25 columns (§5, items 4 and 5), which are the appendix's bookkeeping tables and would
be a small rendering task if the user wants them narrowed.

---

## 9. Change log

| commit | what |
|---|---|
| `10af6a16` | the `verdict` join, `Layout.column_order`, `shares_tables_with`, `per_seed_columns_in`; the reduced sub-heading row and the generated population sentence; the two per-arm-success layouts and Appendix D.3's new first table; Table 7's merges and `omit`; the renderer's three stale generated citations; `report_citations_repoint.py` rewritten and executed; `report_counts_check.py`'s five citations; `harness/README.md` §0; both documents re-rendered |
| `91098b8c` | the report's Appendix C entry; `report_cells_preserved.py`'s census by section, widest grid and declared republications — **the tip, and where every verdict this report cites was pressed** |
| *(this file)* | this report |

---

## Orchestrator's critical assessment (protocol §5)

*Written 2026-09-15 at `1cf9a230` by the orchestrating session, by checks that differ from the agent's; gates the merge.*

**Checks.** (1) **Stamps read from the four `gate.json` files**: each carries one `tree_git_head`, `91098b8c`, all PASS; `git diff --stat 91098b8c..1cf9a230` is this report alone. Rule xiii met at the first press. (2) **`--plan-tables check` re-run by me**: fourteen IDENTICAL comparisons, 68 + 72 + 21 references, 0 dangling. (3) **`report_cells_preserved.py --base f1848d63` re-run by me**: 1 958 rows, 20 917 cells, 0 missing, 0 differing, 3 label cells declared into the caption, Table 11's cells republished from D.12 — the check's rule *never lost, never changed* is the right one; *once* was never the rule. (4) **Census by my own counts**: 18 `Table n` (6 + 12), 22 `Table D.n`, 15 `Table F.n`, 0 one-row grids; the widest grid in §4 is now 13 columns by my own `awk` over the section (was 23). (5) **The three grids against V3's**: Table 11 is V3 §5.1's form with V4's finer classes (`arm | starts offered | accepted optima | finished, ifail = 5 | crashed | coupling-loop cap | lost | seed set`) under **`large_tokamak_nof (n = 25)`**; Table 12's sub-heading rows read **`large_tokamak_nof (n = 22)`**; Table 7 reads `1.0000, 1.0000 → **PASS**` in one cell, nine columns. The counts in Table 11 are A80's and A82's (nof 22/22/22/22, 3 crashed each). (6) **Scope**: 8 files, nothing under `PROCESS/`, `harness/child/` or the root `process/`; stamp survey 1 102 records, 0 re-made — zero PROCESS runs. (7) Appendix C entry written by the task.

**Decisions I accept.** Decision 1 (`shares_tables_with`, mutual): the alternative — a second tally table for the same cells — would put one construction's numbers into the records twice. Decision 3 (`blank_repeats` for the seed set): the brief offered the caption, and the agent is right that a measured number does not go into hand-written text (§15). Decision 8 (the three stale citations inside the renderer's generated context paragraphs, fixed): that is the third kind of T17 miss in as many tasks — hand-written numbers, the change log, and now generated prose — and goes into TRAPS.

**Residuals, for the record.** Table 11 prints a **blank** where a class has no member (`finished, ifail = 5` on `nof`) rather than `0`; it is the tally's absent cell and rewriting it is forbidden by the same rule that protects every other cell, but a reader may take the blank for *not measured*. The caption should say a blank is zero — one sentence, hand-written, no number. The merge-mode sub-heading rows (D.4, D.12) keep the long form; the agent's reason (three constructions, three denominators) holds and both are appendix bookkeeping tables. The other six items of §5 are V4's ladder being taller than V3's or cells that cannot be removed without loss; none is a formatting fault.

**The programme.** A85, A86 and A87 together executed the user's ruling of 2026-09-15: every table V3 §4 and §5 carried is in V4's report in V3's form with the arm translation, every deviation is listed in one place (A87 §3, carried forward), no cell changed across the three tasks (19 426, 19 771, 20 917 preserved), the gates re-pressed at each committed tip, and no PROCESS run was made. What remains is the user's reading.

**Verdict: merge.**
