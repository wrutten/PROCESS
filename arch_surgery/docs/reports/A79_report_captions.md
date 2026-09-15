# A79 (report-captions) — the V4 report's tables as an academic paper handles them

> **Document status** — **OPEN, 2026-09-15.** Task report of **A79 (report-captions)**, branch
> `A79-report-captions` off `architecture_surgery` at `4dac585e` (after A78 (arm-renames)). Zero
> PROCESS runs; every number below comes from a committed script named beside it, run in the
> worktree at the commit named. The user's rulings of 2026-09-15 this task implements are quoted in
> the queue's A79 row and in `docs/plans/REPORT_HEADLINE_TABLES.md`.

## 1. Verdict

**Done; nothing needs the user's ruling to merge, one decision is offered (§8).** The report's
rendered tables moved from §4 into **Appendix D — Results tables** (80 summarising tables,
`Table D.1`–`D.80`, one caption of a few lines each — median 368 characters, at most 485 — with
every construction declared once in D.0), the full result matrices into a generated companion file
**`RESULTS_TABLES_FULL.md`** (150 tables, `Table F.1`–`F.150`), §4 rewritten as conclusions that
point at tables by number, the three headline shapes the user showed built as tally constructions
and re-derived independently, the doubled-caption defect fixed at its cause, §3's tables numbered
with short captions, §5 and §6 re-pointed. **No number changed**: every one of the **33 467** cells
of the old §4 is a cell of the new documents with the same value (0 absent, 0 differing;
`results_cells_unchanged.py --base 4dac585e` at `4cfd1b11`). **0 of 1 102 run records re-made**
(`run_stamp_survey.py`, before at `4dac585e`, after at `297709f4`). Gates pressed once each on kept
records: `recomputation` PASS 14 394 / 0 over 101 tables, `tally_contracts` PASS (303 table checks
+ 256 reference cells = 559 in the gate table) / 0, `run_kind_separation` PASS 3 000 / 0,
`self_containment` PASS 52 / 0; `--selfcheck` PASS; `--plan-tables check` IDENTICAL for both
documents with 86 + 21 table references resolved and 0 dangling.

## 2. What went where

| before (`4dac585e`) | after (`4cfd1b11`) | count |
|---|---|---|
| §4 rendered: 187 tables (gate table; 64 evaluation-phase; 29 optimisation-phase; 93 recomputed), 4 965 lines, 373 `*Caption:` lines + 187 `*How to read:` lines | **§4 hand-written conclusions** (4.1 gates, 4.2 evaluation phase, 4.3 optimisation phase, 4.4 the second computation in one paragraph), ~170 lines, 55 + 9 table references | — |
| — | **Appendix D — Results tables**, rendered between `## Appendix D — Results tables` and `<!-- plan_tables: end of the rendered results tables -->`: D.0 constructions and populations; D.1 gates (1); D.2 headline tables (8: node calls per module ×3, the optimiser's path ×1, node calls per block ×4 sources); D.3 evaluation phase (51: cost per call 12, matched accuracy 12, fixed-point distance 9, ownership rung 6, failure taxonomy 12); D.4 optimisation phase (20: failure taxonomy 3, seed set 3, same optimum 3, iteration multiplier 3, cost 3, achieved accuracy 3, lift closed 2); 1 198 lines | **80 tables**, 80 caption lines (1.00 per table) |
| — | **`RESULTS_TABLES_FULL.md`** (generated whole, status header says so): F.1 evaluation per-run tables (12 per-sweep overhead + the predicate trial = 13); F.2 optimisation per-seed/per-run tables (3 failure tables, 3 attempt-summation identities, 3 per-sweep overheads = 9); F.3 the full versions of the 27 report tables whose per-seed columns the report omits (cost per call 12, ownership rung 6, seed set 3, iteration multiplier 3, achieved accuracy 3); F.4 the 101 recomputed tables; 3 949 lines | **150 tables**, 150 caption lines |
| 7 hand-written `*Caption:` paragraphs (§3.2 ×2, §3.7, §3.9, §3.10, App. A, App. B; median 208, max 681 characters) | 8 numbered hand-written tables — `Table 1` (§1.3 terms, previously uncaptioned) to `Table 6` (§3.10), `Table A.1`, `Table B.1` — captions median 144, max 246 characters; the moved sentences are in the paragraph before each table | — |

*(`caption_census.py --base 4dac585e`; the census's line estimate at 100 characters per line: the
old §4 captions were median 14, max 33 lines; Appendix D's are median 4, max 5.)*

The kinds that left the report and why: **per-sweep overhead** (one row per run, both phases),
**the attempt-summation identity** (one row per run), **the failure table** (one row per seed
outside the set), **the predicate trial** (one row per pair of runs), and every **recomputed**
table (§4.4's "same cells computed a second time" — a gate's business; its summary is the
`recomputation` row of Table D.1). Five kinds stay in the report without their per-seed *columns*
(the paired seeds, the seeds of the set, the attempts per seed, the components above τ per run),
which the companion's full versions keep; each report caption names the companion table.

## 3. The three headline tables, as rendered

Shape 1 (Table D.2, `large_tokamak_nof`; D.3 and D.4 are lad and st):

| module | nodes | which | BR mean | BR [min, max] | B0 mean | B0 [min, max] | B1 mean | B1 [min, max] | B2 mean | B2 [min, max] | B2/B0 pooled | B2/B0 per-run median | [min, max] | runs B2 > B0 | of n |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 | 2 | physics, plasma_geom | 3956.5 | [3516, 4560] | 4055.1 | [3586, 4792] | 4082.2 | [3642, 4762] | 2778.3 | [2482, 3248] | 0.6851 | 0.6909 | [0.598, 0.799] | 0 | 22 |
| M2 | 3 | build, cicc_sctfcoil, pfcoil | 5934.7 | [5274, 6840] | 6082.6 | [5379, 7188] | 6123.3 | [5463, 7143] | 5286.5 | [4719, 6174] | 0.8691 | 0.8765 | [0.761, 1.013] | 1 | 22 |
| M3 | 12 | Plant: 12 nodes (the committed node map's members) | 23738.7 | [21096, 27360] | 24330.5 | [21516, 28752] | 24493.1 | [21852, 28572] | 18499.6 | [16536, 21660] | 0.7603 | 0.7670 | [0.657, 0.887] | 0 | 22 |
| PULSE | 1 | pulse | 1978.2 | [1758, 2280] | 2027.5 | [1793, 2396] | 2041.1 | [1821, 2381] | 641.0 | [573, 749] | 0.3161 | 0.3189 | [0.276, 0.369] | 0 | 22 |
| once per run | 3 | costs, vacuum, water_use | 5934.7 | [5274, 6840] | 6082.6 | [5379, 7188] | 6123.3 | [5463, 7143] | 6.0 | [6, 6] | 0.0010 | 0.0010 | [0.001, 0.001] | 0 | 22 |
| all counted nodes | 21 | every node above | 41542.8 | [36918, 47880] | 42578.5 | [37653, 50316] | 42862.9 | [38241, 50001] | 27211.5 | [24320, 31837] | 0.6391 | 0.6447 | [0.555, 0.746] | 0 | 22 |
| of which outside the solve phase | — | the output path and the exit audit's sweep | 63.0 | [63, 63] | 63.0 | [63, 63] | 21.0 | [21, 21] | 24.0 | [24, 24] | 0.3810 | 0.3810 | [0.381, 0.381] | 0 | 22 |

Shape 2 (Table D.5):

| quantity | configuration | arms | n | BR | B0 | B1 | B2 | B2/B0 mean | B2/B0 median | [min, max] | seeds B2/B0 > 1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| iterations (summed over attempts) | large_tokamak_nof | BR · B0 · B1 · B2 | 22 | 7.818 | 7.818 | 7.773 | 7.773 | 0.9964 | 1.0000 | [0.875, 1.143] | 2 |
| evaluations of the model set, ε | large_tokamak_nof | BR · B0 · B1 · B2 | 22 | 614.7 | 614.7 | 640 | 640 | 1.0437 | 1.0476 | [0.908, 1.209] | 19 |
| node calls per evaluation, ρ | large_tokamak_nof | BR · B0 · B1 · B2 | 22 | 67.49 | 69.15 | 66.94 | 42.48 | 0.6144 | 0.6159 | [0.600, 0.618] | 0 |
| node calls per run, R = ρ × ε | large_tokamak_nof | BR · B0 · B1 · B2 | 22 | 41480 | 42515 | 42842 | 27187 | 0.6414 | 0.6452 | [0.555, 0.746] | 0 |
| iterations (summed over attempts) | low_aspect_ratio_DEMO | BR · B0 · B1 · B2 | 11 | 29.82 | 29.82 | 20.91 | 20.91 | 1.3842 | 0.8125 | [0.129, 5.909] | 3 |
| evaluations of the model set, ε | low_aspect_ratio_DEMO | BR · B0 · B1 · B2 | 11 | 2345 | 2345 | 1714 | 1714 | 1.4816 | 0.8468 | [0.132, 6.450] | 3 |
| node calls per evaluation, ρ | low_aspect_ratio_DEMO | BR · B0 · B1 · B2 | 11 | 72.49 | 70.14 | 66.63 | 43.37 | 0.6183 | 0.6192 | [0.611, 0.620] | 0 |
| node calls per run, R = ρ × ε | low_aspect_ratio_DEMO | BR · B0 · B1 · B2 | 11 | 169943 | 164997 | 114154 | 74312 | 0.9156 | 0.5237 | [0.081, 3.980] | 2 |
| iterations (summed over attempts) | st_regression | BR · B0 · B2 | 22 | 31.18 | 25.14 | — | 23.95 | 0.9828 | 1.0000 | [0.246, 1.356] | 5 |
| evaluations of the model set, ε | st_regression | BR · B0 · B2 | 22 | 1846 | 1480 | — | 1407 | 0.9821 | 1.0000 | [0.241, 1.360] | 5 |
| node calls per evaluation, ρ | st_regression | BR · B0 · B2 | 22 | 69.01 | 71.2 | — | 40.69 | 0.5722 | 0.5858 | [0.534, 0.596] | 0 |
| node calls per run, R = ρ × ε | st_regression | BR · B0 · B2 | 22 | 126868 | 106007 | — | 56507 | 0.5616 | 0.5911 | [0.136, 0.753] | 0 |

Shape 3 (Table D.7, the displaced entries; D.6, D.8, D.9 are the entry reference and the two
stencil sources):

| configuration | block | nodes | which | AR | A0 | A1 | A2 | reference | A2 / reference (pooled) | pairs |
|---|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | M1 | 2 | physics, plasma_geom | 9.9 | 11.0 | 10.2 | 8.0 | A1 | 0.7812 | 25 |
| large_tokamak_nof | M2 | 3 | build, cicc_sctfcoil, pfcoil | 14.9 | 16.6 | 15.4 | 15.5 | A1 | 1.0078 | 25 |
| large_tokamak_nof | M3 | 12 | Plant: 12 nodes (the committed node map's members) | 59.5 | 66.2 | 61.4 | 36.0 | A1 | 0.5859 | 25 |
| large_tokamak_nof | PULSE | 1 | pulse | 5.0 | 5.5 | 5.1 | 1.0 | A1 | 0.1953 | 25 |
| large_tokamak_nof | once per run | 3 | costs, vacuum, water_use | 14.9 | 16.6 | 15.4 | 0.0 | A1 | 0.0000 | 25 |
| large_tokamak_nof | TOTAL | 21 | all counted nodes | 104.2 | 115.9 | 107.5 | 60.5 | A1 | 0.5625 | 25 |
| low_aspect_ratio_DEMO | M1 | 2 | physics, plasma_geom | 10.0 | 10.0 | 9.8 | 8.0 | A1 | 0.8130 | 25 |
| low_aspect_ratio_DEMO | M2 | 3 | build, cicc_sctfcoil, pfcoil | 15.0 | 15.0 | 14.8 | 14.6 | A1 | 0.9919 | 25 |
| low_aspect_ratio_DEMO | M3 | 12 | Plant: 12 nodes (the committed node map's members) | 60.0 | 60.0 | 59.0 | 36.0 | A1 | 0.6098 | 25 |
| low_aspect_ratio_DEMO | PULSE | 1 | pulse | 5.0 | 5.0 | 4.9 | 1.0 | A1 | 0.2033 | 25 |
| low_aspect_ratio_DEMO | once per run | 3 | costs, vacuum, water_use | 15.0 | 15.0 | 14.8 | 0.0 | A1 | 0.0000 | 25 |
| low_aspect_ratio_DEMO | TOTAL | 21 | all counted nodes | 105.0 | 105.0 | 103.3 | 59.6 | A1 | 0.5772 | 25 |
| st_regression | M1 | 2 | physics, plasma_geom | 9.8 | 11.7 | — | 8.0 | A0 | 0.6849 | 25 |
| st_regression | M2 | 3 | build, croco_sctfcoil, pfcoil | 14.8 | 17.5 | — | 17.5 | A0 | 1.0000 | 25 |
| st_regression | M3 | 12 | Plant: 12 nodes (the committed node map's members) | 59.0 | 70.1 | — | 36.0 | A0 | 0.5137 | 25 |
| st_regression | once per run | 4 | costs, pulse, vacuum, water_use | 19.7 | 23.4 | — | 0.0 | A0 | 0.0000 | 25 |
| st_regression | TOTAL | 21 | all counted nodes | 103.3 | 122.6 | — | 61.5 | A0 | 0.5016 | 25 |

**How they are built, and checked.** Each is a construction in `stats.py` — `node_groups` (the
grouping, from `dsm_node_map.json`'s `nodes[<node>].module` and the configuration's per-run
artifact's `post_solve_nodes`, checked against what each record's exit audit stamped as excluded;
never a hand list), `per_node_census` (the evaluation phase's `node_census.counted`, the measured
evaluation alone; the optimisation phase's `node_census.per_node_counted`, the whole run, refused
unless it reconciles with the driver's counter), `census_by_group`, `n_evaluations`
(`sweeps_per_eval.n_evaluations`, I-26's field) and `per_seed_ratio_summary` — built in
`tally_evaluation.node_calls_per_block`, `tally_optimisation.node_calls_per_module` and
`tally_optimisation.optimiser_path`, and re-derived in `analysis.py` (`_node_calls_per_block`,
`_node_calls_per_module`, `_optimiser_path`) importing none of them. The analysis reads ε by
**summing `attempts[].sweeps_per_eval.n_evaluations`** where the tally reads the run-level field;
the two roads met on every cell (the recomputation's 14 394 / 0 include the 1 220 cells of the 8
new tables). Two things the shapes did not say and the tables state: the optimisation-phase
census counts the **whole run**, so a row *of which outside the solve phase* (63 / 63 / 21 / 24
calls per run: the output path's two sweeps in `BR`/`B0`, one call per deferred node in `B1`/`B2`,
the audit's sweep in all) reconciles *all counted nodes* with check 4's solve-phase total by
subtraction rather than apportioning it; and the TOTAL row of shape 3 reproduces the
cost-per-call table's mean and pooled ratio through the census (the census sums to
`node_calls_single_eval` on every record).

**What the path table shows that check 2 could not.** On `large_tokamak_nof` `B2` takes
**1.0476 ×** `B0`'s evaluations in the median (19 of 22 seeds above 1; 640 against 614.7 per run)
at identical iterations (median 1.0000): the lifted formulation's extra design variable adds a
stencil column, and `B1` shows the same 640. The pre-declared ε = 1 holds in iterations and not in
evaluations on nof; the report's §4.3 says so. Check 2's existing *evaluations median* column
(`n_model_calls`, 2.65 on nof) is not ε and is left for A80 (report-accuracy-audit), as the brief
instructed; the report's caption of Tables D.70–D.72 and the D.0 declaration name I-26.

## 4. The caption rule, and one example

**Rule applied.** Every table still declares units, row, column, population and construction
(`tables.Caption`, protocol §16, mechanically enforced) — that declaration is printed **once per
table kind** in Appendix D.0, rendered from the stages' records, and under no table. Under each
table the report prints one caption, `**Table D.n.** *…*`: what the table shows, over which
population (a short source phrase), the one thing not to infer (the reference arm and whether it is
a fallback; the audit position; that the whole-state column is not judged; where a companion table
holds the omitted columns), then `n = … (…)`. Text that varies per table lives in that caption
(`Caption.summary`); the declaration is the same for every table of a kind, and where two variants
remained the renderer prints each with the tables it applies to (two kinds: cost per call and the
fixed-point distance differ by *pairs keyed by seed* / *by design-vector column* — the pairing
column's heading says which). The construction name is printed under each grid in `<sub>` so a cell
is traced by name, never by number.

**Before** (`4dac585e`, `cost per call — large_tokamak_nof — campaign_displaced`, 1 443 characters,
printed twice):

> *Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model
> sequence; ratios are dimensionless. a row is one arm of the evaluation phase on this
> configuration. a column is a per-run mean over that arm's finished runs, with the observed
> bracket, or one of the three readings of the ratio against the declared reference arm.
> population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry
> regime at δ = 0.10 — every arm active on the configuration entered from the same seeded
> displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the
> acceptance regime; 100 run(s) of large_tokamak_nof, of which 100 finished. construction:
> stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank
> upper-middle of the per-run ratios; worse = runs on which the arm cost more. The reference arm is
> A1 — pulsed: the declared reference, because it and the partitioned arm sit on the same reduced
> map. the arrangement-method calls are stamped beside the node calls and are never pooled into
> them. the empty block visits are included in every sweep count and are disclaimed in the
> per-sweep-overhead table, which states their sweep share. these are campaign runs: the population
> named above and no other. pairs are keyed by seeds. n = 100 (evaluation-phase campaign runs of
> large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption,
> twenty-five seeds per arm — **not** the gate runs, which filled this section before execution
> approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the
> instrument.*

**After** (Table D.13, 425 characters, printed once):

> **Table D.13.** *Node calls per evaluation by arm on large_tokamak_nof, the displaced entries
> (δ = 0.10), with the ratio against A1 pooled, as the per-run median and as runs on which the arm
> cost more. A1 is the declared reference (the same reduced map as A2). Prime calls stand beside
> the node calls, not in them. n = 100 (evaluation-phase campaign runs of large_tokamak_nof).
> Per-seed column(s) *paired with A1 at seeds*: companion Table F.26.*

**The doubled-caption defect, at its cause.** `tables.Table.as_record()` stored `markdown()` —
caption, grid, `n = …` line and *How to read* — and `plan_tables._table_block` printed the caption
and the *How to read* again around it: 373 `*Caption:` and 187 `*How to read:` lines for 187
tables. The record's `markdown` is now the grid alone (`Table.grid()`; `Recomputed.markdown()`
likewise), the record also carries the rendered `cells` so the renderer can leave a column out,
and the renderer takes only `|` lines from any older record's `markdown` — so the defect cannot
return from a stale record either. The pooled `n = 100` line under per-row tables is gone with it.

## 5. Numbers unchanged — the proof (`results_cells_unchanged.py --base 4dac585e`)

Every cell of the old §4 is keyed `(implementation, construction name, row index, column heading)`
— the name printed under the table, never its number or caption — and looked up in the union of
Appendix D and the companion file:

| | count |
|---|---|
| old §4 cells (tally 93 tables + recomputed 93; the gate table apart) | **33 467** (25 978 with a digit) |
| … absent from the new documents | **0** |
| … present with a different value | **0** |
| new documents' cells (Appendix D 3 743 in 79 tables; companion 32 882 in 150; union) | 35 891 in 202 tables |
| cells printed in both documents (the 27 tables with omitted columns) | 734, disagreeing between them 0 |
| tables new since `4dac585e` | 16 = the 8 headline tables (3 + 1 + 4) × 2 implementations |
| tables gone | 0 |
| gate table (270 cells, compared beside): cells moved | 6 — `tally_contracts` population and compared (535 → 559: 101 tables × 3 checks + 256 reference cells, was 93 × 3 + 256), `recomputation` population and compared (13 174 → 14 394), `run_kind_separation` population and compared (1 099 → 1 102 records under `runs/`; 2 997 → 3 000) |

The `run_kind_separation` movement is not this task's: the worktree was seeded with A78's records
tree, which holds 1 102 run records (3 from A76 at `47be2b0d`, 3 from A78 at `61473c1d`) against
the 1 099 the campaign-time verdict read; the stamp survey below shows the same 1 102 before and
after this task. The other two moved because the table set grew by the headline tables.

## 6. Verification, in the brief's order (worktree root, everything committed, nothing running)

| step | command (`$PY` = `PROCESS_surgery_env`'s python) | result |
|---|---|---|
| (a) | `experiment_runner.py --selfcheck` at `87a7f298`, and again at `4cfd1b11` | **PASS** both times (the `stage_provenance` fixture carries table kinds; every self-check passes on this tree) |
| (b) | `--measure all --resume` at `297709f4`: `exclusion_review`, `gate_table`, `recomputed_tables`, `tally_evaluation`, `tally_optimisation` — 949 records read at `57dc0c14`, no PROCESS run; then `--plan-tables write`, `--plan-tables check` | **IDENTICAL** for both: Appendix D 1 198 lines / 1 198, companion 3 949 / 3 949, 0 hunks; references 86 to D and 21 to F, 0 dangling |
| (c) | `--gate recomputation --resume` (code changed: `analysis.py`) | PASS, 14 394 / 0 over 101 tables, 9/9 teeth; runs read 949 at `57dc0c14`; verdict at `9b424b50` |
| (c) | `--gate tally_contracts --resume` (population changed: 101 tables) | PASS, 303 table checks / 0 + 256/256 reference cells (gate table 559 / 0), 11/11 teeth; runs read 969 = 949 at `57dc0c14` + 20 at `0677a9b3`; verdict at `9b424b50` |
| (c) | `--gate run_kind_separation --resume` | PASS, 3 000 / 0, 9/9 teeth; 949 at `57dc0c14`; verdict at `9b424b50` |
| (c) | `--gate self_containment --resume` (files changed) | PASS, 52 files / 0, 1/1 tooth; verdict at `9b424b50` |
| (c) | `--measure gate_table --resume`, `--plan-tables write` | 30 PASS, 0 FAIL, 161/161 teeth; the two moved rows committed at `297709f4` |
| (d) | `results_cells_unchanged.py --base 4dac585e` | old ⊆ new, 33 467 cells, 0 absent, 0 differing (§5) |
| (e) | `run_stamp_survey.py --json runs/A79_stamps_before.json` (at `4dac585e`, before any change) and `… --json runs/A79_stamps_after.json --against runs/A79_stamps_before.json` (at `297709f4`) | 1 102 records then and now; commit changed 0, disappeared 0, new 0 — **0 runs re-made** |
| (f) | `merged_names_check.py` | 24 (arm, configuration) pairs identical; 44 400 pin evaluations identical over 185 reference hex values |
| (f) | `harness_survey.py` | 30 gates, 161 teeth, 5 measurement stages; `plan_tables.py` 1 448 lines (was 705), `analysis.py` 4 568, `stats.py` 1 468, `tally_evaluation.py` 1 828, `tally_optimisation.py` 1 984 |
| (g) | `caption_census.py --base 4dac585e` | §2's count table: 187 → 80 report tables + 150 companion; caption lines per table 1.99 → 1.00; caption characters median 1 318 / max 3 290 → 368 / 485 (lines at 100 characters: 14 / 33 → 4 / 5) |

The gates not pressed: none of their code or populations changed (the tally records they read are
regenerated over the same 949 records; `stage_provenance` is a self-check and passed in (a)).

## 7. Autonomous decisions, each with its reversal

1. **The rendered block's end is an explicit HTML comment**, `<!-- plan_tables: end of the rendered
   results tables -->`, because Appendix D is the document's last section and no next heading
   exists. *Reversal:* move Appendix D before Appendix C and set `SECTION_END` to `## Appendix C`.
2. **The optimisation-phase per-module counts are the whole run's census** (the only per-node count
   the records carry), with an explicit *of which outside the solve phase* row reconciling to check
   4 by subtraction, rather than apportioning the output path and audit to modules. *Reversal:*
   a per-node counter frozen at the solve-phase boundary is a driver change (a `NODE_CALLS`
   per-node freeze at each attempt boundary) — out of this task's scope and a G1-gated edit.
3. **Shape 3 is emitted for every evaluation-phase source** (4 tables), not only the displaced
   regime; §4 points at the displaced one. *Reversal:* restrict `node_calls_per_block` to
   `campaign_displaced` in `tally_evaluation.tally()` and `analysis.recompute()`.
4. **Shape 2 carries four rows per configuration** — iterations, ε, ρ **and R** — so the identity
   R = ρ × ε reads down the rows and the R row reproduces check 4; the brief asked for iterations,
   ε and ρ. *Reversal:* drop `("node calls per run, R = ρ × ε", "calls_per_run")` from
   `PATH_QUANTITIES` and `PATH_ROWS`.
5. **Five kinds stay in the report without their per-seed columns** (`report_omits`: the paired
   seeds, the seeds of the set, the attempts per seed, the components above τ per run) and the
   companion carries the full versions, so the report holds no per-seed list in any cell and the
   cell set is a superset. *Reversal:* clear `report_omits` on those tables; the companion group
   F.3 then empties and the census shows it.
6. **Node groups larger than four print the node map's label and count** ("Plant: 12 nodes")
   rather than twelve names in every row. *Reversal:* set `MEMBERS_LISTED_UP_TO` (tally) and
   `MEMBERS_NAMED_UP_TO` (analysis) to 21.
7. **`check` fails on a dangling `Table D.n` / `Table F.n` reference** in the hand-written text,
   since numbers are positional. *Reversal:* drop `references["n_dangling"] == 0` from
   `check()`'s `identical`.
8. **The gate table's row for `recomputation` is the report's whole statement of the second
   computation**; §4.4 is one paragraph pointing at it and at companion Tables F.50–F.150.
9. **§5's prime-call sentence was re-pointed and not corrected.** §5.8 reads "117 281 / 157 504 /
   280 776 per optimisation in `B2`"; the cell (Tables D.73–D.75, *arrangement·method calls*) is a
   **sum over the arm's runs in the seed set** (22 / 11 / 22), not a per-optimisation figure. §4.3
   states the cell correctly; the §5 sentence is a finding for A80 (report-accuracy-audit), whose
   scope it is, and is recorded here rather than rewritten in a merged section's prose.

## 8. Limits, and one decision offered

- **Table numbers are positional.** Adding or removing a table renumbers everything after it and
  every hand-written reference in §4–§6 must follow; `--plan-tables check` now fails on a reference
  past the end but cannot tell a *shifted* reference from a right one. Whoever adds a table re-reads
  §4–§6's references (`grep -n "Table D\."`). *Offered for the user's decision:* whether a stable
  per-table anchor (the construction name, already printed under each grid) should be what the prose
  cites instead of the number — academic style says number; this project's traceability says name.
- **A reader of §5/§6 or of an older report** meets "§4.2 'cost per call'"-style names in the
  archived task reports (A75–A78) and in the queue: those name the *kind* (still the construction
  name under each table), not a section that exists now. The A78 proof script
  `renamed_section_diff.py` reads the pre-A79 markers (`## 4. Results` … `## 5. Discussion`) and
  works only against reports up to `4dac585e`; left as the record of that task.
- **The companion's recomputed tables keep the analysis's own long captions** (median 806
  characters): they are the second implementation's declarations and were not shortened, since the
  companion is a traceability file and not the report.
- **`tally_contracts`' *compared* column** read 535 at `4dac585e` and 559 now; the gate itself
  reports 303 (3 checks × 101 tables) and the gate table adds its `n_reference_values_compared` 256
  — two counts the row sums and names (`denominators summed`). Not a change of this task's making
  beyond the table count.
- **Zero PROCESS runs** — the brief's requirement; nothing here needed one.

## 9. What should change elsewhere (proposals; the README is done)

- **Harness plan, Appendix A — amendment 28 (proposed):** the renderer's block is Appendix D between
  the appendix heading and an explicit end marker; the companion file `RESULTS_TABLES_FULL.md`;
  every table carries `kind`, `summary`, `detail`, `report_omits`; protocol §16's caption is
  satisfied by the declaration printed once in D.0 plus a per-table summary; `check` covers both
  documents and the table references. Rule (ix)'s text ("§4 is rendered from the `gate_table` stage
  record") should read "Appendix D".
- **Queue:** the A79 row to MERGED at merge with this report archived; protocol §16's wording
  ("Every table carries a concise caption: units, what a row and a column are, the population, the
  construction") could add "— the declaration once per kind, a few lines under the table".
- **TRAPS (proposed T17):** *a table number is a position, not a name* — `Table D.n` moves when a
  table is added; a cell is traced by the construction name under its grid, and prose that cites a
  number is re-read whenever the table set changes.
- **A80 (report-accuracy-audit):** three findings for it — §5.8's prime-call sentence (§7.9 above);
  check 2's *evaluations median* column is `n_model_calls` (I-26, known; Table D.5's ε row is the
  declared field); `tally_contracts`' gate-table count is two counts summed (§8).
- **The improvement list (V5):** the per-module optimisation-phase split (Tables D.2–D.4) shows
  where the saving is *not* — M2 at 0.87 / 0.59 / 0.67 pooled, M2's per-run median 0.8765 on nof
  with one run above 1 — which is a design input for V5's partition and belongs on its list.

## 10. Commits (branch `A79-report-captions`, off `4dac585e`)

| commit | what |
|---|---|
| `1022d93e` | the three headline constructions in `stats`/`tally_*`, re-derived in `analysis`; every table carries `kind`, `summary`, `detail`, `report_omits`; declarations kind-invariant; the record's `markdown` is the grid alone |
| `87a7f298` | the renderer: Appendix D, the companion file, numbering, D.0, `check` over both documents and the references; the gate table's caption split; the self-check fixture |
| `9b424b50` | §4 rewritten; Appendix D and the companion rendered; §3 and appendix tables numbered; §5–§6 re-pointed; header and Appendix C; `results_cells_unchanged.py`, `caption_census.py` |
| `297709f4` | the gate table re-rendered after the four gate presses |
| `4cfd1b11` | harness README; the census joins wrapped hand-written captions |
| *(this report)* | `docs/reports/A79_report_captions.md` |

## 11. Change log

- 2026-09-15 — task opened at `4dac585e`; the work above; report written at `4cfd1b11`.
