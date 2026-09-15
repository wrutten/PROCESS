# A86 (v3-tables-remainder) — the rest of the previous revision's §4 and §5 tables

> **Document status** — **MERGED 2026-09-15** at `150c7ed3` (`--no-ff`); archived here at merge — folder position records lifecycle, not validity (trap T3). Records: `arch_surgery/idf_probe/runs/A86_runs/` (latest resume-compatible). Orchestrator's assessment at the end; its two residual grids are task A87 (v3-grid-polish), its finding issue I-27. Task **A86 (v3-tables-remainder)**, branch
> `A86-v3-tables-remainder` (worktree `.claude/worktrees/A86-v3-tables-remainder`, retired), base
> `ab3d339a`, tip `52a77127` — **which is the last commit that touches code or a generated
> document, and is where every gate verdict this report cites was pressed** (rule xiii); the
> only commit after it is this document. Specification:
> [`../plans/REPORT_TABLE_FORMATS.md`](../plans/REPORT_TABLE_FORMATS.md) (RULING, 2026-09-15) and
> A85 (v3-table-formats)'s report §7 and the orchestrator's assessment appended to it.
> **Zero PROCESS runs**; `EXECUTION_APPROVED` untouched; no file under
> `MDA_partitioning_experiment_v4/PROCESS/`, `harness/child/` or the root `process/` changed.
> Arm names are today's (`AR/A0/A1/A2`, `BR/B0/B1/B2`); the records stamp the names of their day
> and `records.read` translates (trap T16).

---

## 1. Verdict

**All eighteen tables the specification maps are built, and the main text's tables are in reading
order.** A85 (v3-table-formats) delivered seven of them and the V3 cell formats; this task builds
the remaining eleven, closes the six residual departures from the V3 grids that the orchestrator's
assessment listed, and re-cuts §4.2 and §4.3 so that each table is followed by the prose that
reads it.

Nineteen new stage tables, **1 278 new cells**, each computed in the tally and re-derived by an
independently written twin in `analysis.py`, compared cell by cell without tolerance under gate
`recomputation`: **141 tables, 17 554 compared, 0 mismatched**. Four new constructions in
`stats.py`, each with a tooth on `tally_contracts` that trips (13 → 17 teeth). **No pre-existing
cell changed**: 1 846 rows and 19 771 cells preserved, **0 missing and 0 differing** except the
gate table's own two rows, whose populations grew.

### 1.1 The census

| | before (`ab3d339a`) | after (`52a77127`) |
|---|---|---|
| tables in §4 (main text) | 7 | **12** |
| tables in Appendix D | 15 | **21** |
| tables in the companion file | 13 | **15** |
| markdown grids in the report | 26 | **37** |
| markdown grids in the companion | 21 | **23** |
| **tables with one row** | **0** | **0** |
| stage tables the tally emits | 122 | **141** |
| cells the two implementations compare | 16 276 | **17 554** |
| teeth in the gate table | 163 | **167** |

*A blocks-mode table prints one grid per configuration under one caption and one number, which is
why the grid counts exceed the table counts: Tables 10 and 18 and companion Table F.3 are three
tables and fifteen grids.* The one-row count is 0 before and after: A83's rule holds.

### 1.2 The V3 → V4 table map, complete

Every table of [`V3_EXPERIMENT_REPORT.md`](../../MDA_partitioning_experiment_v3/V3_EXPERIMENT_REPORT.md)
§4 and §5 that the specification maps, with the V4 table that reproduces it and its number.

| V3 table | V4 table | state |
|---|---|---|
| **T4.1** check 1, matched accuracy (§4) | **Table 7**, §4.2 | **built here** |
| **T4.2** cost of the prime → per-call cost (§4) | **Table 8**, §4.2 | **built here** |
| **T4.3** full distributions per configuration and arm (§4.4) | **Table D.7** | **built here** |
| **T4.4** module scope (§4.5, static) | **Table D.2** | **built here** |
| **T4.5** per-module sweeps per run (§4.5) | **Table 10**, §4.2 | built at A85 (v3-table-formats) |
| **T4.6** the exclusion set's namespaces (§4.5) | **Table D.8** | **built here** |
| fixed-point distance (V4 only, A76) | **Table D.9** | V4's own, in the V3 cell formats |
| **T5.1** robustness and taxonomy (§5.1) | **Table 11**, §4.3 | **moved into the main text here** |
| **T5.2** same optimum, check 1 (§5.2.1) | **Table 12**, §4.3 | **moved into the main text here** |
| **T5.3** location diagnostic (§5.2.2) | **Table D.14** | **built here** |
| **T5.4** iteration multiplier, check 2 (§5.3) | **Table 13**, §4.3 | built at A85 |
| — the ε table of the same shape | **Table 14**, §4.3 | built at A85 |
| — the ρ table of the same shape | **Table 15**, §4.3 | built at A85 |
| — the R = ρ × ε table of the same shape | **Table 16**, §4.3 | built at A85 |
| **T5.5** identity (V3's `B2`/`B3`, here `B1 → B2`) | **Table D.15** | **built here** |
| **T5.6** lift closure, check 3 (§5.4) | **Table D.21** | re-rendered at A85 |
| **T5.7** cost, check 4 (§5.5) | **Table 17**, §4.3 | **built here** |
| **T5.8** both anchors (§5.5) | **Table D.18** | **built here** |
| **T5.9** sweeps and prime calls (§5.5) | **Table D.19** | **built here** |
| **T5.10** per-module breakdown (§5.5.1) | **Table 18**, §4.3 | built at A85 |
| **T5.11** problem definition (§5.6) | **Table D.12** | **built here** |

**Eighteen of eighteen built; none omitted.** No table appears twice: a construction the main text
carries is not repeated in the appendix, and the two tables whose per-seed columns the report omits
(per-arm success, the reference entries and four others) have their full version in the companion
and nowhere else.

V4's own tables with no V3 counterpart keep their places, in the V3 cell formats: node calls per
block (Table 9 and D.3), the reference entries (D.4), cost per call per arm (D.5), matched accuracy
per arm and ruler (D.6), the ownership rung (D.10), the evaluation phase's failure taxonomy (D.11),
node calls per module (D.13), check 2's two constructions (D.16), check 4 per arm (D.17), achieved
accuracy (D.20).

### 1.3 The main text, in reading order

Twelve tables, each followed by the prose that reads it. A85 left the numbers out of reading order
(Table 12 printed before Table 8); this task reorders `LAYOUTS` so the number rises down the page.

| § | table | what |
|---|---|---|
| 4.2 | **7** | check 1, matched accuracy — the headline evaluation-phase check, with the verdicts as cells |
| 4.2 | **8** | per-call cost — the ladder's rungs `AR→A0`, `A0→A1`, `A1→A2`, and the prime calls |
| 4.2 | **9** | node calls per block (V4's own) |
| 4.2 | **10** | module sweeps per run, the evaluation phase (V3 §4.5) |
| 4.3 | **11** | per-arm success, the seed set and the failure taxonomy (V3 §5.1) |
| 4.3 | **12** | same optimum, check 1 (V3 §5.2.1) |
| 4.3 | **13–16** | the optimiser's path as four tables of one quantity (V3 §5.3's shape) |
| 4.3 | **17** | check 4's cost as sums, arms as columns (V3 §5.5) |
| 4.3 | **18** | module sweeps per run, the optimisation phase (V3 §5.5.1) |

---

## 2. The new constructions, and their re-derivation

Four declarations in `harness/measurement/stats.py`, each with an independently written twin in
`harness/measurement/analysis.py` (which may import nothing from `stats`, `tables` or either
`tally` module — gate `recomputation`'s import tooth), and each with a tooth on
`tally_contracts` offering the premise broken:

| construction | what it is | the premise it checks rather than assumes | its tooth |
|---|---|---|---|
| `stats.iteration_variables` | the accepted design vector keyed **by name**, joining `mfile.itvars` to `mfile.itvar_names` **on the solver's slot** | refuses a record with a value in a slot the name map does not name | *a design vector joined by position* — a third value and two names: REFUSED |
| `stats.point_difference` | the largest relative difference over the variables two vectors **share by name**, with the argmax, the shared count and the unshared names | a variable one side alone carries has no difference: it is named and never compared | *a variable one side alone carries* — `t_plant_pulse_burn` added to one side does not move the maximum and is named in `extra` |
| `stats.namespace_residuals` | each excluded namespace's maximum scaled residual in one run, from that run's own `audit_residual.json` | refuses a file naming no `excluded_keys` (the namespaces would be a list typed by hand) and a ruler the file does not carry | *an exclusion list the run did not state* — both REFUSED |
| `stats.figure_of_merit` | the objective's name and sense, parsed from the **frozen tree's** `FiguresOfMerit` and never imported | refuses a figure of merit the enum does not carry, rather than printing the integer | *a figure of merit the enum does not carry* — `i_figure_merit = 6`: REFUSED |

**Agreement.** Gate `recomputation`, `--resume`, at `52a77127`: **141 tables, 17 554 compared,
0 mismatched**, over 949 campaign run records made at `57dc0c14`. Of those, **17 454 are cells of
the tables** (1 486 rows; 13 010 from a construction, 4 444 composed as a string) and 99 are the
published values beside them (48 similarity verdicts, 3 seed sets). Before the task: 122 tables,
16 276 compared. The 1 278 new cells are the nineteen new stage tables.

**The nineteen new stage tables**, by construction: `matched accuracy by configuration` (3 — one
per evaluation-phase source with the partitioned arm), `per-call cost by configuration` (3),
`full distributions` (3), `excluded namespaces` (3), `module scope` (1, emitted once), and one each
of `location diagnostic`, `the identity B1 → B2`, `cost sums (check 4)`, `cost against both
anchors`, `sweeps and prime calls` and `problem definition`. One further **cell** is not a new
table: the optimiser's path gains `ratio_pooled`, the ratio of the means (deviation (i) below).

**Gate `tally_contracts`** (`--resume`, at `52a77127`): **PASS, 679 compared (423 table checks +
256 reference cells), 0 mismatched, 17 of 17 teeth tripped**, the four new ones among them
(163 → 167 teeth in the gate table).

**A confirmation worth naming.** Three of the new tables reproduce the previous revision's own
published cells where the two campaigns are comparable, written from the V4 records with no V3
number in front of them. Check 4's cost sums (Table 17) read `912 555 / 935 340 / 942 522 /
598 124` on `nof` — the previous revision printed `912 555 / 935 340 / 942 522 / … / 598 124` for
`R / B0 / B1 / … / B3` — and the ratio `0.6395` against its `0.639`. The location diagnostic's
argmax census reproduces `f_nd_alpha_thermal_electron (12/22)` and
`f_nd_impurity_electrons(13) (5/22)` on `nof` and `dr_shld_inboard (14/22)` and
`dr_tf_nose_case (6/22)` on `st`, cell for cell. The excluded namespaces reproduce its §4.5 second
table's order of magnitude on every namespace. That is a construction check no gate can give,
because both implementations here are V4's.

---

## 3. Deviations from the V3 grids, all of them in one place

Every place a V4 table is not the V3 table, one line each. **A85's are carried forward** so the
merged report's deviations are listed here and nowhere else.

### 3.1 Named in the specification (A85's §3.1, unchanged)

| V3 | V4 | what differs | why |
|---|---|---|---|
| T4.5, T5.10 columns `A0 / A1u / A1`, `R / B0 / B1 / B2 / B3` | `AR / A0 / A1 / A2`, `BR / B0 / B1 / B2` | `A1u` and V3's `B2` dropped, `AR` and `A1` added | `A1u` is not run in V4 (the prime is inside the intervention); V3's `B2` was removed by D22; `AR` and `A1` are V4's reference and ownership rungs. The specification's §0 translation, applied |
| T4.5 ratio against `A0` | ratio against `A1` on a pulsed configuration, `A0` on st | the declared reference arm changed | V4 declares the reference per configuration (`tally_evaluation.reference_arm`); the *reference* column names it in every row |

### 3.2 Introduced at A85 (v3-table-formats), carried forward

| # | V3 | V4 | what differs | why |
|---|---|---|---|---|
| 1 | T4.5 / T5.10 rows `M1, M2, M3 live, \`vacuum\`, PULSE, FF` | `M1, M2, M3, PULSE, once per run` | V4 groups the configuration's own deferred nodes into one *once per run* row | V4's existing derived grouping (`stats.node_groups`), already used by Tables 9 and D.13 and already gated; re-splitting it for one table would put two groupings in one report. **Accepted at A85's assessment**, with the caption now naming the row's nodes (§3.3 (v)) |
| 2 | `models` total 52 | 49 | three collapsed-DSM rows are attributed to no group | Those are FF's rows whose nodes execute on no configuration of this experiment; each caption states the map's 52 and the configuration's 49 |
| 3 | total ratio bracketed over `vacuum`'s row | bracketed over the whole once-per-run group's rows | the unknown is three or four rows, not one | Follows deviation 1 |
| 4 | configurations abbreviated `tok / lad / st` | `nof / lad / st` | the first configuration's short name | The V4 report writes `nof` throughout §4–§6 (A79); a table renaming it would be one the prose cannot cite. **Accepted at A85's assessment** |
| 5 | numbers spaced (`102 868`) | unspaced (`96933`) | no thousands separator | The existing V4 cells carry none, and a separator inside a cell makes the committed cell-preservation comparison presentation-sensitive |
| 6 | T5.4 columns `n, R, B0, B3, ratios` | the same plus a constant `quantity` column | one column named the quantity | **Closed here** — see §3.3 (iv): the column is dropped into the caption |
| 7 | cross-configuration tables blank the configuration on continuation rows | the appendix's stacked tables keep a bold sub-heading row per group | the configuration is a row group, not a first column | The sub-heading row carries the configuration **and** the source regime **and** that group's own n with what it counts (trap T11); a blank first column can carry only the first. Where a key really repeats down consecutive rows the blanking is applied, and this task adds it to five more tables |
| 8 | V3 §5.2.1 has `within-cluster med / p90 / would accept` | V4's same-optimum table has `below resolution` | a different companion construction | V4 never built the within-cluster construction; `below_resolution` is what it has |
| 9 | node calls per module was §4.3's table | Appendix D.13 | the node-call per-module table left the main text | Its sweeps twin (Table 18) is the previous revision's headline; keeping both in §4 would be the same grid twice in two units. D.13 is kept whole because check 4's solve-phase total is read from its *outside the solve phase* row |

### 3.3 Introduced or closed by this task

| # | V3 | V4 | what differs, and why |
|---|---|---|---|
| i | T5.4 column **`B2/B0 mean`** — the ratio of the means, *"equal to the ratio of the sums over the same seeds — the campaign-cost statistic"* (V3 §5.3) | **closed.** `B2/B0 mean` is now the ratio of the means, computed in the tally and in the analysis (`stats.per_seed_ratio_summary`'s `pooled` reading, a new **cell** under V3's heading); the statistic that used to sit there — the mean of the per-seed ratios — is **renamed** `B2/B0 mean of per-seed ratios` and stands beside it | Neither number was wrong; a V3-shaped table with a V3 heading over a different statistic was. The two differ by a lot where a few long runs dominate the sums: on `lad` V3's statistic reads **0.7012** and the mean of ratios **1.3842**. `report_cells_preserved.py` carries the rename as a **declaration** (`RENAMED_HEADINGS`) printed with every run, so the old cell is still proved present under its new heading |
| ii | T5.10 `runs B3 > B0` as one cell `0/22` | **closed.** One cell `k/n` on Table 18, by a new `fraction` cell join | It was two columns (`runs B2 > B0` \| `of n`). Both parts are still present and the preservation check puts the old row through the same join before looking for it |
| iii | block heading **`tok`** (n = 25) / (n = 22) | **closed.** `**\`nof\`** (n = 22)` on Table 18 and `**\`nof\`** (n = 25 per arm)` on Table 10; the population sentence moved to the caption | The evaluation table's own denominator is 100 (four arms × 25), so the per-arm count is declared as a count with the sentence that says what it counts (`Table.block_denominator`) rather than derived by dividing. The arm set is named only where the block does not carry the phase's whole ladder — V3's `st` block, whose heading said *"no B1"* |
| iv | T5.4 has no `quantity` and no `arms` column | **closed.** Both dropped from Tables 13–16 and stated in each caption, by a declared `Layout.omit` | 24 label cells, named and counted in the preservation check's output. They are labels, not numbers: every numeric cell is untouched |
| v | `vacuum` and `FF` rows | one `once per run` row, **its nodes now named in the caption** (`costs`, `vacuum`, `water_use`; `pulse` as well on `st_regression`) | A85's deviation 1 was accepted at assessment with this addition; the row's membership is now readable without opening the node map. It is also Table D.2's own cell set |
| vi | `M3 live` | **`M3`** | V4's `M3` group is already the live one: the non-live nodes are in the *once per run* row by construction, so the word *live* would distinguish nothing. The group's name is the committed node map's key and is the same name Tables 9, D.2 and D.13 use; renaming it in one table would give the report two names for one group |
| vii | `tok` | `nof` | accepted at A85's assessment (deviation 4 above), restated here so the list is complete |
| viii | V3's §4 check-1 grid is one row per configuration and carries **no stencil rows** | Table 7 and Table 8 carry the **displaced regime only**; the same grids at the two stencil entry points are companion Tables F.1 and F.2 | The specification asked for the stencil regimes "as two further rows per configuration"; V3's own grid has no such rows, and reproducing *that grid* means the acceptance regime alone. The other regimes keep the same form, one grid per regime, as A85 did for the per-module blocks. **This is a deviation from the specification, not from V3** |
| ix | V3 §5.2.2 repeats check 1's **verdict** column | Table D.14 repeats check 1's median and p90 and **not** its verdict | The verdict is a cell of Table 12, three pages earlier; repeating a verdict in two tables is two places for it to go stale. The objective columns are repeated because the whole point of the table is reading them side by side with the point columns |
| x | V3 §5.1 is six columns | Table 11 is twenty-three | Not introduced here: it is A82's per-arm success table merged with the failure taxonomy and the seed set, which V4 distinguishes and V3 did not. Recorded because the map would otherwise imply a like-for-like reproduction |
| xi | — | a merged `median / p90` column both of whose parts are missing reads `— / —`, not `—` | The collapse was written and **withdrawn**: it rewrote three already-published cells of the same-optimum table's yardstick rows, which the preservation check caught. A rendering change may move a cell, never rewrite one |
| xii | V3 §5.5 publishes **ok** and **converged** seed sets | Table 17 publishes *every arm accepted* and *without retried seeds* | V4 has one acceptance set and publishes the retry exclusion beside it (the specification names this deviation; the caption says which) |

---

## 4. Placement, and the citations

**Main text.** §4.2 and §4.3 were re-cut so that every table is followed by its discussion, in
reading order (§1.3). Five paragraphs were written for the tables that had none — module scope,
the full distributions, the excluded namespaces, the problem each configuration poses, the location
diagnostic with the identity, and both anchors with the prime accounting — each reading cells of
the rendered grid.

**Citations.** `report_citations_repoint.py` was rewritten for this move and executed (protocol
§15). It works from a **map of layout → old number → new number**, not from a shift: the moves are
not a shift (the per-module evaluation table went 12 → 10 while the iteration multiplier went
8 → 13, and two appendix tables became main-text ones). Numbers are rewritten only **inside a
citation span** (`Table …`, `Tables … and …`, `companion Table …`), so `F = 10` and `0.7812` are
not citations; each is put behind a placeholder so no number moves twice.

- **74 numbers moved** across the two documents' hand-written text.
- **Five citations that have not existed since A79** repaired: `D.37–D.42`, `D.73–D.75`,
  `D.82–D.83`, `D.67–D.69`, `D.76–D.78`.
- **Five citations that would have survived the map as a plausible wrong table** (trap T17's
  addition), found by re-reading every one after the map and asking what the sentence is about:
  the ownership rung's per-call ratio cited the per-block table in §4.2 and §5.1 (it is the
  per-call cost table's own `A0→A1` column); §4.2's fixed-point paragraph cited the appendix where
  it now sits under check 1's own table; §4.3's RQ2 paragraph cited the per-arm cost table as the
  headline where check 4's sums are; and §5.1's *"per module Table 8; the path Table 9"* named the
  iteration multiplier and one quarter of the path — two citations A85's re-pointing left behind.
- **Three doubled `companion companion Table F.n`** repaired.
- **The change log is held out of the sweep.** Appendix C's entries state the table set of their
  own day — A82's entry says so in as many words — so a number in one is a record, not a citation.
  A85's re-pointing rewrote them; this task's does not, and the entries are restored to the numbers
  they were written with.
- `--plan-tables check`: **0 dangling** references, 63 to §3/§4's numbered tables, 68 to Appendix D
  and 21 to the companion.

---

## 5. Verification

The sequence, worktree root, tree clean and committed at **`52a77127`** at every step, nothing else
running. **Zero PROCESS runs.**

| # | step | result |
|---|---|---|
| 1 | `--measure all --resume` | five stages re-pressed: `tally_evaluation` **93** tables, `tally_optimisation` **48**, `recomputed_tables` **141**, `gate_table`, `exclusion_review`; **0 runs made** |
| 2 | `--plan-tables write` | both documents written; 12 + 21 + 15 tables |
| 3 | `--plan-tables check` | **IDENTICAL** for all twelve §4 blocks, Appendix D (1 129/1 129 lines) and the companion (1 705/1 705); **0 dangling** references |
| 4 | `--gate recomputation --resume` | **PASS** at `52a77127` — 141 tables, **17 554 compared, 0 mismatched**, 9/9 teeth |
| 5 | `--gate tally_contracts --resume` | **PASS** at `52a77127` — **679 compared (423 + 256), 0 mismatched**, **17/17 teeth**, the four new ones tripped |
| 6 | `--gate run_kind_separation --resume` | **PASS** at `52a77127` — 3 000 compared, 0 mismatched, 9/9 teeth |
| 7 | `--gate self_containment --resume` | **PASS** at `52a77127` — 52 files, 0 mismatched, 1/1 tooth |
| 8 | `--measure gate_table --resume` | **30 PASS, 0 FAIL, 167 of 167 teeth tripped** |
| 9 | `--plan-tables write`, then `check` again | **IDENTICAL** everywhere, **0 dangling**; nothing re-rendered, tree clean |
| 10 | `--selfcheck` | **PASS** |

### 5.1 The stamps

| verdict | `tree_git_head` | is that the tip's code? |
|---|---|---|
| `recomputation` | **`52a77127`** | yes — the tip |
| `tally_contracts` | **`52a77127`** | yes — the tip |
| `run_kind_separation` | **`52a77127`** | yes — the tip |
| `self_containment` | **`52a77127`** | yes — the tip |

`52a77127` is **the last commit that touches code or a generated document**: the only commit after
it is this report. Two earlier presses are superseded and this report cites neither — one at
`8b7d38a5`, before the slash-merge collapse was withdrawn (deviation xi, a code change), and one at
`9631dd7e`, before §4.3's opening paragraphs were put in table order. Every verdict was pressed
again at the tip each time.
The `gate_table` stage record's `records_read` names the commit of each of the thirty verdicts it
read: **4 at `52a77127`** (the four above, the only gates this task's change alters what they read)
and 26 at the commits they were pressed at in the seeded records tree — `8996b843` 23,
`6f5ba612` 2, `350a58c4` 1 — which is the records-reuse rule.

The two tally stage records and `recomputed_tables` carry no commit of their own by design: a stage
over **run** records is provenanced by `runs_provenance`, which the analysis compares against its
own survey of the same runs. All three were re-pressed at `52a77127` in steps 1 and 4–5.

### 5.2 The standing checks

| check | result |
|---|---|
| `report_cells_preserved.py --base ab3d339a` | **1 846 of 1 846 rows and 19 771 of 19 771 cells preserved** (14 879 carrying a number); **0 missing**; **2 differing**, both rows of the gate table |
| | **24 label cells** stated in a caption instead of once per row, declared (`Layout.omit`) and counted by name in the output |
| `run_stamp_survey.py`, before and after the whole press | **1 102 records**, the same nine commits, 949 at `57dc0c14`; byte-identical output — **0 re-made, 0 new** |
| `report_counts_check.py` | runs; **4 lines differ**, the same four that differed at the base (A85's Limit 5) |

**The two differing rows, with their denominators.** Both are rows of Table D.1 and both are the
gates' own cells rather than a rendering:

| row | cell | before | after | why |
|---|---|---|---|---|
| `tally_contracts` | population | 122 tables | **141** | the tally emits nineteen more |
| | compared | 622 (366 + 256) | **679 (423 + 256)** | 57 more table checks for the nineteen new tables |
| | teeth | 13/13 | **17/17** | the four new teeth |
| `recomputation` | population | 122 tables | **141** | as above |
| | compared | 16 276 | **17 554** | the 1 278 new cells |

Every other cell of both documents — 19 771 of them — is present with the same value, keyed by
construction, configuration, source, row and column, and put through the same `merges`, `omit`,
`bold` and `blank_repeats` declarations the renderer used before being looked for.

---

## 6. Autonomous decisions, each with its reversal

| # | decision | reversal |
|---|---|---|
| 1 | The check-1 and per-call-cost grids in §4.2 carry the **displaced regime only**, with the stencil regimes as the same grids in the companion, rather than as extra rows per configuration (deviation viii) | The two companion layouts' `where` becomes `"main"`, or `sources` is widened and the layouts merged into one `stack` |
| 2 | `Layout.omit` was added as a **declared** transform and taught to the preservation check, rather than dropping the `quantity` and `arms` columns at the tally (which would have removed them from the record too) | Remove `omit` from the four layouts; the columns return with no change to any stage record |
| 3 | The `B2/B0 mean` rename is carried by a committed `RENAMED_HEADINGS` map in the preservation check, rather than letting the check report ten differing rows | Delete the entry: the check then reports the rename as ten differing rows, which is also a true statement |
| 4 | `M3`, not V3's `M3 live` (deviation vi) | One entry in the node map's `modules.M3.label`, or a per-layout row rename |
| 5 | `Table.block_denominator` declares the per-arm count for the evaluation phase's block heading, rather than the renderer dividing the table's denominator by the number of arms | Remove the field; the heading returns to the table's own denominator (`n = 100`) |
| 6 | `problem_definition` states the configuration's problem from the **unlifted** arms and the problem after the lift beside it, rather than refusing a configuration whose arms disagree on `nvar` | Restrict to one arm set and drop the two *after the lift* columns; the refusal is then the whole behaviour |
| 7 | The location diagnostic does **not** repeat check 1's verdict column (deviation ix) | Recompute the threshold from the yardstick in the same construction and add the column |
| 8 | Appendix C is held out of the citation sweep | Remove the hold from `report_citations_repoint.py`; its entries' numbers then move with the tables |

---

## 7. Limits

1. **Table 11 is twenty-three columns wide in the main text.** It is V3's §5.1 table merged with
   V4's failure taxonomy and its seed set — the specification asked for the extra columns — and
   three of its columns are the same label repeated down a configuration's rows. Narrowing it means
   either dropping cells (which the preservation rule forbids) or a second grouping of the same
   construction.
2. **`Σ components > τ` is 0 in thirty-two of the thirty-three rows of Table D.7 and not in the
   thirty-third**: the reference arm `AR` on `large_tokamak_nof`'s backward stencil points leaves 2
   components above τ, both in one run. The report states it; a reader who took "0 everywhere" from
   the displaced regime would be wrong at one point in the appendix (trap T11).
3. **The per-module total's `models` is 49, not the map's 52**, and the `[v = 1, v = 0]` interval
   is a bracket over an unknown rather than an uncertainty. Unchanged from A85; Table D.2 now makes
   the attribution visible, but it does not resolve it — per-node DSM rows are what trap T9 forbids
   reading live.
4. **The cell-preservation check compares rendered strings.** Two cells that render identically and
   differ in the eleventh digit would pass it. The check against a changed *value* is gate
   `recomputation`, which compares raw numbers without tolerance; the two together are the proof.
5. **The identity table has no `st_regression` row**, because `B1` is inactive there. V3's identity
   table had one, for a pair V4 does not run. The caption says so.
6. **Three of the eleven `B1 → B2` pairs on `low_aspect_ratio_DEMO` reach a different `norm_objf`
   bit pattern** at identical evaluation and iteration counts. The table states the counts; why
   those three differ in the last bits is not measured here and the report does not guess.
7. **The four differing lines of `report_counts_check.py` still differ** — the crash-class split,
   the plan's stencil budget, and the second nonzero-mismatched PASS row. All four differed at the
   base and are the bookkeeping notes A80 recorded; none is a cell of a table.

---

## 8. What should change elsewhere (proposals; the queue and TRAPS are not this task's to edit)

**Harness plan, Appendix A, amendment 31 — proposed text.**

> **31. The report's table set is the V3 report's, whole (task A86 (v3-tables-remainder), the
> user's ruling of 2026-09-15, [`docs/plans/REPORT_TABLE_FORMATS.md`](../../docs/plans/REPORT_TABLE_FORMATS.md)).**
> All eighteen mapped tables are built; the main text carries twelve in reading order, each
> followed by the prose that reads it, and the appendix twenty-one. A `Layout` may also **drop a
> column into its caption** (`omit`) where the cell is the same label on every row it keeps — the
> V3 grids carried no such column — and a `Merged` may join a count to its denominator
> (`fraction`, `0/22`). A block heading line states the previous revision's `n` and nothing more;
> where the table's own denominator is over a wider population than the block's rows, the block's
> count is **declared** (`Table.block_denominator`) with the sentence that says what it counts,
> never derived by dividing. **Rule xvii:** a heading reused for a different statistic is a
> declaration, not an edit — it is named in `report_cells_preserved.py`'s `RENAMED_HEADINGS` with
> the column key it now means, printed on every run, and the old cell is then proved present under
> its new heading; and a rendering change may move a cell but never rewrite one, so a collapse that
> alters an already-published string (`— / —` → `—`) is withdrawn rather than published.

**`harness/README.md`** — done on the branch: §0's `plan_tables` paragraph states `omit`, the
`fraction` join, the reduced block heading line and the `RENAMED_HEADINGS` declaration, and the
companion's row of §13's table names what it now holds.

**TRAPS — proposed addition to T17** (the orchestrator's to make): *a re-pointing must hold the
change log out of its sweep. Appendix C's entries state the table set of the day they were written
— one of them says so in as many words — so a number in one is a record, not a citation; A85's
re-pointing rewrote five of them and A86 restored them. The rule: a citation sweep names the parts
of the document it may touch, and the historical ones are not among them.*

**For the queue (a proposal, not a minting).** Nothing of the specification remains. Two small
items surfaced and are not this task's: Table 11's width (Limit 1), and the three
`low_aspect_ratio_DEMO` pairs whose `norm_objf` differs in its last bits at an identical trajectory
(Limit 6), which is a one-paragraph investigation over records already on disk.

---

## 9. Change log

| commit | what |
|---|---|
| `c1a07caa` | the four constructions in `stats.py`; eleven new tables in the two tally modules; the optimiser's path's ratio-of-means column; every twin in `analysis.py` |
| `b9b8c79e` | the renderer's `fraction` join, `Layout.omit`, `Table.block_denominator` and the reduced block heading line; the layouts for the eleven tables and the main text's reading order; `report_cells_preserved.py` taught the omission and the rename |
| `dde92401` | §4.2 and §4.3 re-cut; `report_citations_repoint.py` rewritten and executed; the five new discussion paragraphs |
| `654ff0b1` | four teeth for the new constructions' premises; `report_counts_check.py`'s constants and its stale table numbers |
| `d553a132` | §4.1's and §4.4's gate counts; `harness/README.md` §0; the report's Appendix C entry |
| `8b7d38a5` | the evaluation phase's block heading line at `n = 25 per arm`; both documents re-rendered |
| `9631dd7e` | the slash-merge collapse withdrawn (deviation xi) |
| `52a77127` | §4.3's opening paragraphs in table order — **the tip, and where every verdict this report cites was pressed** |
| *(this file)* | this report |

---

## Orchestrator's critical assessment (protocol §5)

*Written 2026-09-15 at `2a18c274` by the orchestrating session, by checks that differ from the agent's; gates the merge.*

**Checks.** (1) **Stamps read from the four `gate.json` files**: `recomputation`, `tally_contracts`, `run_kind_separation`, `self_containment` each carry one `tree_git_head`, `52a77127`, all PASS; `git diff --stat 52a77127..2a18c274` touches only this report. Rule xiii met at the first press this time. (2) **`--plan-tables check` re-run by me** on the clean worktree: fourteen IDENTICAL comparisons (12 §4 blocks, Appendix D, companion), 63 + 68 + 21 references, 0 dangling. (3) **`report_cells_preserved.py --base ab3d339a` re-run by me**: 1 846 rows, 19 771 cells, 0 missing, 2 differing — the gate table's own rows, populations grown (122 → 141 tables, 16 276 → 17 554, 622 → 679, 13 → 17 teeth). (4) **Census by my own counts** of caption lines: 18 `Table n` (6 in §3, 12 in §4), 21 `Table D.n`, 15 `Table F.n`, 0 grids with a single data row. (5) **Cells against known values**: Table 8's `A1→A2` 0.5625 / 0.5772 / `A0→A2` 0.5016 are the headline per-call ratios; Table 17's `B2/B0` 0.6395 / 0.4504 / 0.5331 are check 4's; Table 13's new `B2/B0 mean` is the ratio of the printed means to the last digit (7.773 / 7.818 = 0.9942; 20.91 / 29.82 = 0.7012; 23.95 / 25.14 = 0.9527 against 0.9530 from the unrounded means), and the renamed mean-of-ratios column is unchanged (0.9964 / 1.3842 / 0.9828). Table 18's `nof` block is A85's Table 13 cell for cell with `0/22` in one cell and **`nof`** (n = 22) over it. (6) **Scope by diff**: nothing under `PROCESS/`, `harness/child/` or the root `process/`; stamp survey 1 102 records, 0 re-made — zero PROCESS runs. (7) The Appendix C entry is written by the task, as the brief required.

**Decisions I accept.** Decision 1 (stencil regimes to the companion; V3's §4 grid had no stencil rows, and the user ruled that V3's grid wins over my spec); decision 3 (`RENAMED_HEADINGS` as a printed declaration — the alternative, ten differing rows, would make the check cry wolf on every run); decision 8 (Appendix C held out of the citation sweep — its numbers are history, and A85's sweep had rewritten five of them). Deviation xi, the withdrawn `— / —` collapse, is the preservation check doing exactly its job.

**Two grids still not V3's, for the record and for A87.** (a) **Table 11 is twenty-three columns in the main text.** V3 §5.1 was six: `config | invalid seeds | arm | ok | converged (ifail = 1) | not-converged among ok`. A82's per-arm success table alone is that grid with V4's finer classes; what makes Table 11 unreadable is the merge with the failure taxonomy's bookkeeping columns (`scheduled`, `rows sum`, `detail (traceback's last line × count)`, `arms`, `which`) and the seed-set columns repeated down every arm row. The main text should carry the per-arm success grid in V3's form; the merged table belongs in Appendix D, where no cell is lost. The agent's Limit 1 treats this as a width problem; it is a placement one. (b) **The stacked tables' sub-heading rows** still carry the tally's whole table name (`large_tokamak_nof · campaign_optimisation · BR·B0·B1·B2 — n = 22 (seeds on which every arm of large_tokamak_nof converged)`, Table 12): the heading reduction of deviation iii was applied to `blocks` tables only. V3's grids put `config` in the first column; A85's deviation 7 argued the sub-heading row carries more, but the same argument was answered for the block tables by moving the sentence into the caption. (c) Smaller: Table 7 spreads V3's one cell `0.76, 5.64 → PASS` over `med | p90 | verdict` and adds a `verdict note` column (14 columns against V3's 7); a `merges` declaration closes it.

**A finding to register, not a verdict change.** Table D.15: on `low_aspect_ratio_DEMO`, all 11 `B1 → B2` pairs agree exactly on evaluations and iterations but only **8 of 11** on the `norm_objf` bit pattern; on `nof` 22/22 agree. The ε = 1 expectation (evaluations) holds as A80 stated; the objective's bit identity was never an acceptance quantity. Why three pairs differ in the last bits at an identical trajectory is one paragraph over records on disk — issue **I-27**, proposed to the user.

**Verdict: merge.** All eighteen mapped tables exist, the ratio-of-means statistic sits under V3's heading with the other renamed beside it, the residual grid departures A85's assessment listed are closed except the two above, 1 278 new cells are computed twice with 0 mismatched, every old cell is present unchanged by the committed check and by my re-run, the four verdicts name the committed code they were pressed on, zero PROCESS runs.
