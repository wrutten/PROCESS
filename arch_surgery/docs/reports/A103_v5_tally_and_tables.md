# A103 (v5-tally-and-tables) — rule B1's attribution, the retired iteration multiplier, the matrix's stopping-rule cell, two captions, I-37, and the V5 harness README

> **Document status** — **OPEN task report** (branch `A103-v5-tally-and-tables`, from
> `architecture_surgery` at `b84892e8`). Analysis and rendering over the V5 campaign's existing records
> (A102 (v5-campaign)); **no PROCESS run was made and no driver file changed**. Every number below comes
> from `experiment_runner.py` or `paper_cells_recount.py` at the commit named beside it. The V5 experiment
> report (`EXPERIMENT_REPORT.md`) is not written here (it waits on the user's decision about which `st`
> result the main table carries).

## 1. Verdict

All six items are built, each its own commit, and pressed read-only over the campaign's 553 records.

- **Gates after: 29 registered, 29 PASS, 0 FAIL, 0 not run; 167 of 167 teeth tripped**
  (`--measure gate_table --resume` at `c2295511`; Table 7.1). 28 gates were re-pressed at `c2295511`;
  `record_completeness` (G7) was not re-pressed and its verdict stands from `75b9e9d4` (decision 1: its tooth
  makes one PROCESS run by design). `tally_contracts` now compares 302 table-contract checks (94 tables × 3,
  plus 20 new directory comparisons for I-37) and 236 reference cells, 0 mismatched, 18/18 teeth (A102: 506,
  17/17).
- **Item 4, rule B1 with its attribution** (§2): the tally reproduces A102's reading from the records.
  **`tok` PASS** (0 hops of 22; every `B0 → B2` difference is a relocation along a flat direction that enters
  at the lift, `B1 → B2` within the floor on 22/22 with the same path on 22/22). **`lad` FAIL at p90**
  (objective p90 3.1e-04 against 1.0e-06): 4 hops of 12 (seeds 1*, 10*, 11, 13; 2 across objective clusters),
  **every one entering at the lift `B0 → B1`**; the partition `B1 → B2` reads objective median 8.9e-15, p90
  2.3e-14, 0 hops, the same path on 12 of 12. **`st` FAIL at p90** on `B0 → B2` (p90 1.3e-03): 3 hops of 20
  (seeds 5*, 12*, 24*, all retried), entering at `B0 → B2` — the partition under the census set at τ = 1e-8,
  `st` having no `B1`; **the yardstick `BR → B0` hops on 2 of those 3 seeds too** (12 and 24). The
  verification table's B1 row reads **PASS tok · FAIL lad, st** with that attribution, from the stage record.
- **Item 1's leftover** (§3): the iteration multiplier's verdict and its 1.05 threshold are gone
  (`Campaign.iteration_ratio_max` removed); every number stays; the plan's label is printed beside ε: `tok`
  **trajectory-neutral** (ε = 1.0411), `lad` **trajectory changed by ε = 1.4410**, `st` **trajectory changed by
  ε = 2.4432** (`B0 → B2`, ratio of the summed evaluations) — A102's §1 labels, now printed by the tally.
- **The matrix's stopping-rule cell** (§4) reads the campaign's test set and τ: `feedback couplings @ τ = 1e-08`
  (flat) and `… per block` (partitioned), where it read V4's `y @ τ`.
- **Two captions** (§5): phase B's wall-clock caption states the first evaluation's cache load (0.26–0.44 s per
  run, 0.6–3.3 % of module time, from the `cache_load` record); the optimisation tally's achieved-accuracy
  caption states why `B2`'s whole-state statistic reads large, and the code shows no phase B rule reads it.
- **I-37 fixed** (§6): the reproduction gate's jobs resolve with every instrument switch cleared; a new part and
  tooth in `tally_contracts`; the gate **PASSes both ways** without a campaign press — the chain's reading
  stages pressed alone under the campaign press's own composition (timers on) and under the plain one, each
  236/236 reference cells, 0 of 302, 18/18 teeth. **I-37 can close.**
- **The harness README** (§7) is rewritten to V5's text (1 992 → 422 lines).
- **`paper_tables.md`**: `--paper-tables write` then `check` IDENTICAL; cross-check 0 mismatched of 178, tooth
  bites; `paper_cells_recount.py` 44 cell rows, 0 mismatched. **The diff against `b84892e8` touches only the
  matrix row, the phase B caption and the verification table** (its B1 row, its records-read line and the six
  gate rows' commit, re-stamped at `c2295511`); **no count cell of the phase A, iterations or phase B module
  tables moved** (§8).

## 2. Item 4 — rule B1 with its attribution (plan §5 B1; V5 list item 4 as reduced)

**What was built** (`harness/measurement/tally_optimisation.py`, commit `613a0e4e`). The statistic table is
kept and renamed `same optimum (B1)` (48 of 48 existing stage tables' rows identical to A102's record). Its
verdict is factored into `judge_pair` (median and p90 of `|Δ norm_objf| / max(|a|, |b|)` against
`max(F × yardstick, floor)`, F = 10, floor = 1e-6, yardstick `BR → B0`), which the new tables share, so the
verdict is computed once. Two new tables:

- **`same optimum per seed and rung — <configuration>`** (one per configuration, a detail table): per seed of
  the seed set, for the yardstick, each ladder step (`B0 → B1` the lift, `B1 → B2` the partition; on `st`,
  where `B1` is inactive, one step `B0 → B2`) and each judged pair: the objective's relative difference, the
  design point's (the largest relative difference over the iteration variables the two sides share by name —
  a diagnostic, D6), the **kind** — **hop** where the objective differs by more than the floor (marked *across
  clusters* where the two optima sit in different objective clusters at 10 × floor, V4's hop), **relocation**
  where the objective is within the floor and the point moved by more than the floor, **within the floor**
  otherwise — whether the optimiser took the same path (equal evaluations and equal iterations summed over
  attempts), the retried arms, and the step the headline pair's (`B0 → B2`) difference **enters at** (the first
  spanned step whose own difference is of the same kind).
- **`same optimum by rung`** (one per source): one row per configuration and pair — the yardstick and the ladder
  steps beside, the judged pairs with the verdict, which order statistic fails, the counts by kind, the same-path
  count, where the hops and the relocations enter, the hop seeds (`*` = a retried arm) and how many of them the
  yardstick hops on too. The paper's verification row reads this table (`paper_tables._same_optimum_verdict`).

The supplementary tally gains the same two tables over its own population (no `BR`, so no yardstick and no
verdict there, as before). The tables verbatim are Appendix A.

**The reading per configuration.**

- **`tok` (n = 22): PASS.** No seed hops on any pair. Every `B0 → B1` and `B0 → B2` difference is a
  relocation (objective within the floor, the point moved by 1e-2 to 4e-1 — `t_plant_pulse_burn` is lifted into
  the optimiser and other variables move along the flat direction), and all 22 enter at the lift. `B1 → B2`:
  objective 0 on the median and p90, point within the floor, the same path on 22 of 22 — the partition changes
  nothing about where the optimiser lands.
- **`lad` (n = 12): FAIL at p90** on both `B0 → B1` and `B0 → B2` (identical cells). Four seeds hop: 1 and 10 across
  clusters (3.1e-4, 3.9e-4; seed 1 retried in `BR`/`B0`, seed 10 in `B1`/`B2`), 11 and 13 below cluster resolution
  (1.3e-6, 2.1e-6). **All four enter at the lift**; the other eight are relocations entering at the lift. The
  partition step reads objective median 8.9e-15, p90 2.3e-14, 0 hops, the same path on 12 of 12. The yardstick hops
  on none of the four seeds. This is V4's attribution, reproduced: the difference is the lift's, not the
  partition's.
- **`st` (n = 20): FAIL at p90** on `B0 → B2`. Three seeds hop, all across clusters and all with a retried arm:
  5 (1.3e-3; `B2` retried), 12 (1.3e-2; `BR` and `B2` retried), 24 (1.3e-2; `BR` and `B2` retried). They enter at
  `B0 → B2`, the only step — the partitioned arm under the census set at τ = 1e-8, the pre-declared non-neutral
  trajectory term (plan §3, A96). **On seeds 12 and 24 the yardstick hops too**: at seed 12 `BR` and `B2` agree and
  `B0` is the odd one (`BR → B0` and `B0 → B2` both 1.311e-2); at seed 24 all three differ. So one of the three hops
  is the flat control's own landing, not the partition's. The other 17 seeds are relocations with a point moved
  by up to 0.96 (A102's location diagnostic: `dr_tf_nose_case`, `dr_bore`), 2 of 20 on the same path.
- **Supplementary `st` at τ = 1e-12 (n = 24), beside:** 1 hop (seed 5*, across clusters), 8 relocations, 15 within
  the floor, the same path on 16 of 24 — the path returns at the tighter tolerance, as A102 §7 read.

## 3. Item 1's leftover — the iteration multiplier's verdict retired (plan §5 B3)

**Before** (A102 Appendix B, `iteration multiplier (check 2)`): columns `summed median (acceptance)` and a
`verdict` column reading PASS / FAIL against `iteration_ratio_max = 1.05` on `B0 → B1` and `B0 → B2`, "beside" on
`B0 → BR` and `B1 → B2`; `tok` PASS, `lad` PASS (median 0.8333), `st` FAIL (2.2143).

**Now** (`iterations and ε (B3)`, commit `59c85283`): no verdict column, no acceptance pairs, no threshold
(`ACCEPTANCE_PAIRS` and `Campaign.iteration_ratio_max` removed; the table is no longer an acceptance table).
Every number kept: the summed and final-attempt iteration medians and sum ratios, ε's median, `ε = 1 on`, the
sweep ratio, the attempts per seed, `constructions disagree` — each shared cell identical to A102's record on all
ten rows. Added: **ε's ratio of the summed evaluations** (the ε of `R = ρ × ε`) and the plan's **label** beside it
(`trajectory_label`, band `Campaign.trajectory_neutral_band = 1.05`, a label and never a verdict):

| configuration | pair | ε median | ε sum ratio | label |
|---|---|---|---|---|
| `tok` | `B0 → B1`, `B0 → B2` | 1.0476 | 1.0411 | trajectory-neutral |
| `tok` | `B1 → B2` | 1.0000 | 1.0000 | trajectory-neutral |
| `lad` | `B0 → B1`, `B0 → B2` | 0.8674 | 1.4410 | trajectory changed by ε = 1.4410 |
| `lad` | `B1 → B2` | 1.0000 | 1.0000 | trajectory-neutral |
| `st` | `B0 → BR` | 1.0000 | 1.4370 | trajectory changed by ε = 1.4370 |
| `st` | `B0 → B2` | 2.2593 | 2.4432 | trajectory changed by ε = 2.4432 |
| `st` supplementary (1e-12) | `B0 → B2` | 1.0000 | 1.0475 | trajectory-neutral |

(Excerpted from Appendix A's four tables; `B0 → BR` on `tok` and `lad` reads 1.0000, neutral.) The paper's
iterations table is unchanged (its cells are the optimiser's path table's, read by the cross-check). **The
contracts gate's expectation**: its tooth "check 2's two constructions disagree" is renamed **"the two iteration
constructions disagree"** — it still guards what the table publishes (the final-attempt and summed constructions
side by side), not V4's retired check 2; no other expectation of the gate named the table. Dead code removed:
`ACCEPTANCE_PAIRS`, the verdict branch, `iteration_ratio_max`; docstrings in `stats.py`, `registry.py`,
`paper_tables.py` re-worded.

## 4. The switch matrix's stopping-rule cell

`Arm.stopping_rule` is now a **form** — `test set @ τ` on the flat arms, `test set @ τ per block` on the
partitioned ones (the plan's Table 1 has `c @ τ per block`), `objf/conf` on the references — and
`arms.matrix(campaign)` fills it from `config.TEST_SET_WORDS[campaign.test_set]` and `campaign.tau`
(`stopping_rule_text`; commit `4af3c73d`). `PLAN_MATRIX` transcribes the form; the `rungs` self-check reads 98
compared, 0 mismatched, 3/3 teeth.

| | before (`b84892e8`) | after |
|---|---|---|
| `A0`, `A1`, `B0`, `B1` | `y @ τ` | `feedback couplings @ τ = 1e-08` |
| `A2`, `B2` | `y @ τ` | `feedback couplings @ τ = 1e-08 per block` |
| under `--test-set write_set` | `y @ τ` | `whole write set @ τ = 1e-06` (… `per block`) |
| LaTeX | `y @ $\tau$` | `feedback couplings @ $\tau$ = 1e-08` |

## 5. The two captions (commit `4a01e6e3`; no computation changed)

**(a) Phase B wall-clock caption** (`paper_tables._cache_load_sentence`, reading
`runs/timing/cache_load/measurements.json` through `timing.cache_load_record` / `cache_load_summary`; refuses
where the stage was never pressed). The stage record was re-pressed at `c2295511` (`--timing cache-load`, read
only): A102's was made at `24c6573c`, before the `st` phase B re-make, and only its three `st` phase B rows moved.
The sentence as rendered:

> **The module rows include one numba cache load per run**: a phase B run's first evaluation is not warmed (the
> fixed per-run term ends at its start), so its module rows carry the per-process cache load the warmed phase A
> records measure as warm-up less measured model time — a median of 0.26–0.44 s per run over the 11 configuration
> and arm rows, 0.6–3.3 % of the median module time per run of the arm's phase B twin, the same order in every arm
> (`--timing cache-load`, record at `c2295511`).

**(b) Phase B's whole-state statistic** — printed only in the optimisation tally's `achieved accuracy at the
accepted optimum` table (the paper does not print it). New clause, and the summary's closing sentence replaced:

> the whole-state statistic on the deferring arm (B2) is taken at an audit snapshot that precedes the deferred
> nodes' one execution on the output path (A102 (v5-campaign) §13): the driver copy takes the snapshot at the entry
> to write_output_files and executes the per-run nodes immediately after it (caller.py, write_output_files), so at
> the snapshot their components still hold the values of an earlier state and the whole-state maximum reads large
> on them; the restricted statistic excludes them. No phase B acceptance rule reads the whole-state column: rule
> B1 reads exact.norm_objf, B2 and B3 counts, B4 constraint 93's residual, B5 the exit status; D36's whole-state
> rule is phase A's (A1), where the deferred set is executed before the audit.

**Confirmed by reading the code**: the order is `_take_exit_snapshot(models, data, "entry_to_write_output_files")`
then `caller._sweep_block(x, ps)` over the per-run set (`PROCESS/process/core/caller.py`, `write_output_files`).
The whole-state statistic's readers (`stats.whole_state_statistic` / `whole_state_population`) are, in phase B,
only `tally_optimisation.achieved_accuracy`'s `whole_median` column; `gate_count_neutrality` reports the
whole-state maximum on both sides and does not compare it; the paper's A1 row reads the evaluation tally's tables
alone; B1 (`same_optimum`, `same_optimum_by_*`), B2/B3 (`cost`, `iterations`, `optimiser_path`), B4
(`lift_closed`) and B5 (`per_arm_success`) never read it.

## 6. I-37 — `tally_contracts` inside the campaign press

**Reproduced first, read-only** (inspection at `b84892e8`'s code): `tally.reference_cells` under the campaign
with the timers on matched 0 of 236 cells, and 236 of 236 with them off.

**The fix** (commit `470f7a41`): `reproduction.v4_criterion` — applied to every job GR composes (its twenty
planned runs, the entry-reference prerequisites, the substitutes, the composition tooth) — now sets every
`switches.INSTRUMENT_SWITCHES` field of the job to `False` (and refuses if a switch has no Job field). GR's records
are untimed by construction, and an instrument switch must never change which record a comparison reads. With it,
the timed campaign resolves 236 of 236. `tally.reference_cells` also names a caught prerequisite error
(`prerequisite_error`, and `why_not`) instead of reporting 236 `no_record` cells as ordinary mismatches.

**The tooth that would have caught it.** `tally_contracts` part **1b** (`gate_tally.instrument_invariance`):
GR's twenty planned runs resolved with each instrument switch on in a copy of the campaign, each directory
compared with the one resolved with every switch off; a composition that refuses counts every run as a mismatch.
Without the fix this part reads **20 of 20 mismatched** (checked by inspection with the old `v4_criterion` put back
in a scratch process; not a published figure) — the gate would have failed at every press, not only inside the
campaign press. New tooth **"an instrument switch reaches a reference job"**: one planned job composed with the
campaign's switch on (I-37's defect on one job) must move the count — 0 → 1 of 20, tripped. The 20 comparisons are
folded into the gate's table-contract count (282 → 302).

**Pressed both ways without a campaign press.** The chain's reading stages (`tally_evaluation`,
`tally_optimisation`, `tally_contracts`) are factored into `chain.run_reading_stages`, which `chain.run` calls
after its run stages; the runner's new `--reading-stages {campaign-press,plain}` presses them alone over the
records on disk — `campaign-press` under `campaign_press_composition` (the function `--campaign` now calls: the
timers on), `plain` as `--gate` does — with no run stage and no PROCESS run, verdicts to `--outdir`:

| press (at `cbdad977`) | timers | `tally_contracts` | compared | reference cells | teeth | log |
|---|---|---|---|---|---|---|
| `--reading-stages campaign-press --resume --outdir runs/reading_stages/campaign_press` | on | **PASS** | 302, 0 mismatched | 236 / 236 | 18/18 | `A103_press03_…` |
| `--reading-stages plain --resume --outdir runs/reading_stages/plain` | off | **PASS** | 302, 0 mismatched | 236 / 236 | 18/18 | `A103_press04_…` |

Both read 94 tables over the campaign family (3 + 275 + 275 records). (Presses 01/02 at `470f7a41` read the same
verdicts; their detail line mis-stated the table-check count, fixed in `cbdad977`.) What remains unpressed: a real
`--campaign` press through `chain.run` — by construction it now calls the same `run_reading_stages` with the same
composed campaign. **I-37 can be closed.**

## 7. The harness README, and the gate table after

`harness/README.md` rewritten to V5's text (commit `c2295511`; 1 992 → 422 lines). Outline: status header;
1 what this folder is (the copy, the harness, the button, the paper's document; isolation); 2 the package;
3 the switch matrix (with the stopping-rule form), the rungs, the switch kinds (architecture, campaign settings,
instruments); 4 one run end to end; 5 the test set and its census (DR11; GT); 6 the schedule and the prime (DR9,
DR10; GC, G2); 7 phase A's once-execution (item 5; D35, D36) and phase B's audit snapshot; 8 the warmed evaluation
child; 9 the timers and the six timing stages (D38, D41, D42); 10 the chain with the reading stages, the
supplementary stage, the tally's rules A1–B5 with B1's attribution and B3's label, the paper's document and the
recount; 11 the 29 gates; 12 where records live and what a record is; 13 pressing each stage; change log. Removed:
V4's sections on the second implementation, the report renderer and companion file, G8 and the `mixed` ruler, the
cold chain, the stencil regime, the function-weighted tables, and A101/A102's appended §§17–19 (folded in). Two code
comments that cited "README §3" now cite V4's README.

**Table 7.1 — the gate table after** (`--measure gate_table --resume` at `c2295511`,
`A103_press09_gate_table.log`; record `runs/gates/gate_table/measurements.json`): 29 PASS, 0 FAIL, 0 not run;
167 of 167 teeth. Verbatim in Appendix B. Changed against A102's Table 12.2: `tally_contracts` 506 (270 + 236),
17/17 → **538 (302 + 236), 18/18**; every row but `record_completeness` at `c2295511`.

## 8. The diff of `paper_tables.md` (`b84892e8` → `65dd0044`)

11 lines changed, 11 inserted (`--paper-tables write` at `c2295511`, `A103_press13`; `check` IDENTICAL at
`65dd0044`, `A103_press14`; recount 44 rows, 0 mismatched, `A103_press15`). The changed lines, in order:

1. the switch matrix's `stopping rule` row, Markdown and LaTeX (§4);
2. the phase B wall-clock caption: the cache-load sentence appended (§5 (a));
3. the verification table's records-read line: the `gate_table` stage record now read 30 records at
   `0353c524`, `75b9e9d4` and `c2295511`;
4. the verification rows G0, G1, G6, G5, G9, GT: their gate's commit `75b9e9d4` → `c2295511` (the same verdicts,
   compared counts, mismatches and teeth);
5. the B1 row: **see detail** with "V5's attribution rule is item 4's, pending" → **PASS tok · FAIL lad, st** with
   the attribution (§2).

No cell of the configurations, phase A, iterations, phase B module, wall-clock or per-arm success tables moved; the
generator's cross-check compared 178 of them with the stage records, 0 mismatched. The full diff is Appendix C.

## 9. Decisions taken alone (each with its reversal)

1. **`--gate all --resume` was pressed as its 28 gates one at a time, `record_completeness` skipped**, because G7's
   tooth "a stale run is re-made without --resume" re-makes one smoke evaluation on every press and the brief
   forbids PROCESS runs. Its verdict stands at `75b9e9d4`; nothing it reads changed. Records under `runs/` before and
   after the press: 1 168 `metrics.json`, identical paths and modification times. Reversal: `--gate
   record_completeness --resume` (one smoke run), then `--measure gate_table --resume`.
2. **`--timing cache-load` re-pressed** at `c2295511` so the caption reads a record made over the current `st`
   records (the old one predated the `st` re-make). Reversal: restore A102's record from
   `idf_probe/runs/A102_runs/v5_campaign/timing/cache_load/`.
3. **Hop = objective difference above the floor; relocation = within the floor with the design point moved by more
   than the same floor (1e-6)**; the cluster-based hop is kept as *across clusters*. The point threshold is mine.
   Reversal: `difference_kind`'s second comparison.
4. **ε's label is read on the ratio of the summed evaluations** (the ε of `R = ρ × ε`), with the median beside; on
   these records the two constructions give the same label on every judged pair and on `B1 → B2`, and differ on one
   row beside: `st` `B0 → BR` (median 1.0000, neutral; ratio of the sums 1.4370, changed — three retried seeds carry
   the sums). Reversal: `trajectory_label` on
   `evaluations_median`.
5. **`iterations and ε (B3)` is no longer an acceptance table** (no verdict reads it); `same optimum by rung` is one.
   Reversal: the `acceptance=` flags.
6. **The statistic table is renamed `same optimum (B1)`** (was `(check 1)`), and the iterations table
   `iterations and ε (B3)`. Reversal: the two names; nothing reads them by name except the paper's verification row,
   which reads `same optimum by rung`.
7. **The verification row's verdict is mixed** (`PASS tok · FAIL lad, st`) rather than one word. Reversal:
   `_same_optimum_verdict`'s return.
8. **The fix for I-37 is at `v4_criterion`** (every GR job) rather than only in `reference_cells`; and a runner flag
   `--reading-stages` was added to show the gate under the press's composition. Reversal: revert `470f7a41`.

## 10. Limits

- **G7 not re-pressed** (decision 1); the gate table carries it at `75b9e9d4`.
- **The phase B cache load is estimated from phase A records** (warm-up less measured), not measured on phase B
  records, as in A102 §6; the caption's share is against the phase B twin's median module time over its finished
  runs, not the seed set.
- **The design-point column is a diagnostic** (D6): a relocation says the point moved, not that the optimum is the
  same in any other sense; `st`'s relocations move up to 96 % on `dr_tf_nose_case` / `dr_bore`, which A102's location
  diagnostic already named.
- **`st`'s attribution cannot separate the partition from the census set at τ**: with no `B1` rung the one step
  changes both; the supplementary stage at 1e-12 (1 hop of 24, beside) is the evidence that the tolerance carries it.
- **I-37's fix is shown by the reading stages under the press's composition, not by a whole `--campaign` press.**
- **I-36 still stands**: `--jobs all` (and `--jobs reproduction`) refuse on this tree (five directories hold GR's
  `AR` substitute's digest); A103's per-gate `--jobs` listings were used instead (`A103_press05_jobs_all.log`).
- The tally stages were pressed with `--resume` over records at `6221af70` and `f4a75f8e`; every stage says so in its
  straddle note.

## 11. Records

Presses in `runs/_press_logs/A103_press01…15_*.log` (reading stages ×4, `--jobs`, `--selfcheck` 7/7 PASS,
`--timing cache-load`, the 28 gates, `gate_table`, the three tallies, `--paper-tables write` / `check`, the recount).
The whole `runs/` is relocated to **`arch_surgery/idf_probe/runs/v5_tally_and_tables/`** (moved on one filesystem;
record counts before and after in the change log).

## Appendix — change log (append-only)

- 2026-09-30 — commits `613a0e4e` (item 4), `59c85283` (item 1's leftover), `4af3c73d` (the matrix cell),
  `4a01e6e3` (captions), `470f7a41` and `cbdad977` (I-37), `c2295511` (README), `65dd0044` (`paper_tables.md`);
  presses 01–15 as listed in §11; this report.
- 2026-09-30 — `runs/` moved whole by `mv` (one filesystem) to `arch_surgery/idf_probe/runs/v5_tally_and_tables/`:
  1 168 `metrics.json` and 17 529 files before, 1 168 and 17 529 after; the V5 folder holds no `runs/` now.

## Appendix A — the new and changed tally tables, verbatim (stage records `runs/gates/tally_optimisation/measurements.json`, `tally_supplementary/measurements.json` at `c2295511`)

#### same optimum per seed and rung — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2

| seed | retried arms | BR → B0 objf | BR → B0 point | BR → B0 kind | BR → B0 same path | B0 → B1 objf | B0 → B1 point | B0 → B1 kind | B0 → B1 same path | B1 → B2 objf | B1 → B2 point | B1 → B2 kind | B1 → B2 same path | B0 → B2 objf | B0 → B2 point | B0 → B2 kind | B0 → B2 same path | B0 → B2 enters at |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | — | 1.388e-16 | 1.845e-06 | relocation | yes | 7.984e-11 | 4.243e-02 | relocation | no | 0 | 5.747e-12 | within the floor | yes | 7.984e-11 | 4.243e-02 | relocation | no | B0 → B1 |
| 1 | — | 8.327e-16 | 6.128e-07 | within the floor | yes | 7.749e-12 | 4.179e-02 | relocation | no | 0 | 6.775e-12 | within the floor | yes | 7.749e-12 | 4.179e-02 | relocation | no | B0 → B1 |
| 2 | — | 1.388e-16 | 2.550e-06 | relocation | yes | 1.484e-11 | 4.408e-01 | relocation | no | 0 | 5.554e-12 | within the floor | yes | 1.484e-11 | 4.408e-01 | relocation | no | B0 → B1 |
| 3 | — | 2.220e-15 | 7.171e-07 | within the floor | yes | 2.597e-11 | 1.214e-02 | relocation | no | 0 | 1.021e-12 | within the floor | yes | 2.597e-11 | 1.214e-02 | relocation | no | B0 → B1 |
| 4 | — | 2.914e-15 | 2.214e-09 | within the floor | yes | 3.786e-11 | 7.247e-02 | relocation | no | 0 | 1.227e-11 | within the floor | yes | 3.786e-11 | 7.247e-02 | relocation | no | B0 → B1 |
| 6 | — | 2.776e-16 | 9.423e-07 | within the floor | yes | 5.136e-12 | 2.881e-02 | relocation | no | 0 | 5.357e-12 | within the floor | yes | 5.136e-12 | 2.881e-02 | relocation | no | B0 → B1 |
| 7 | — | 5.002e-13 | 1.017e-06 | relocation | yes | 2.823e-11 | 2.283e-02 | relocation | no | 0 | 8.665e-12 | within the floor | yes | 2.823e-11 | 2.283e-02 | relocation | no | B0 → B1 |
| 8 | — | 1.110e-15 | 1.216e-06 | relocation | yes | 3.487e-11 | 3.006e-02 | relocation | no | 0 | 8.209e-12 | within the floor | yes | 3.487e-11 | 3.006e-02 | relocation | no | B0 → B1 |
| 9 | — | 1.110e-15 | 6.623e-07 | within the floor | yes | 2.913e-11 | 2.983e-02 | relocation | no | 0 | 1.967e-11 | within the floor | yes | 2.913e-11 | 2.983e-02 | relocation | no | B0 → B1 |
| 10 | — | 5.025e-13 | 4.802e-09 | within the floor | yes | 8.882e-12 | 2.690e-02 | relocation | no | 0 | 1.681e-11 | within the floor | yes | 8.882e-12 | 2.690e-02 | relocation | no | B0 → B1 |
| 11 | — | 2.290e-14 | 8.876e-07 | within the floor | yes | 3.429e-11 | 1.884e-01 | relocation | no | 0 | 1.667e-11 | within the floor | yes | 3.429e-11 | 1.884e-01 | relocation | no | B0 → B1 |
| 12 | — | 2.914e-15 | 3.921e-07 | within the floor | yes | 8.831e-12 | 4.944e-02 | relocation | no | 0 | 6.229e-12 | within the floor | yes | 8.831e-12 | 4.944e-02 | relocation | no | B0 → B1 |
| 13 | — | 7.494e-15 | 6.864e-07 | within the floor | yes | 9.368e-12 | 5.593e-02 | relocation | no | 0 | 1.038e-10 | within the floor | yes | 9.368e-12 | 5.593e-02 | relocation | no | B0 → B1 |
| 14 | — | 9.315e-11 | 1.632e-04 | relocation | yes | 4.570e-11 | 1.870e-01 | relocation | no | 0 | 1.628e-11 | within the floor | yes | 4.570e-11 | 1.870e-01 | relocation | no | B0 → B1 |
| 15 | — | 1.110e-15 | 1.060e-06 | relocation | yes | 5.474e-11 | 4.564e-02 | relocation | no | 0 | 1.048e-12 | within the floor | yes | 5.474e-11 | 4.564e-02 | relocation | no | B0 → B1 |
| 16 | — | 2.776e-16 | 3.007e-07 | within the floor | yes | 4.030e-11 | 4.752e-02 | relocation | no | 0 | 4.148e-11 | within the floor | yes | 4.030e-11 | 4.752e-02 | relocation | no | B0 → B1 |
| 17 | — | 3.594e-14 | 8.352e-05 | relocation | yes | 3.220e-11 | 1.146e-01 | relocation | no | 0 | 1.044e-11 | within the floor | yes | 3.220e-11 | 1.146e-01 | relocation | no | B0 → B1 |
| 18 | — | 0 | 8.345e-08 | within the floor | yes | 5.647e-12 | 2.838e-02 | relocation | no | 2.776e-16 | 2.253e-11 | within the floor | yes | 5.647e-12 | 2.838e-02 | relocation | no | B0 → B1 |
| 19 | — | 2.483e-13 | 2.902e-07 | within the floor | yes | 9.071e-12 | 4.783e-02 | relocation | no | 0 | 1.477e-11 | within the floor | yes | 9.071e-12 | 4.783e-02 | relocation | no | B0 → B1 |
| 22 | — | 2.082e-15 | 2.482e-07 | within the floor | yes | 3.157e-11 | 9.349e-02 | relocation | no | 0 | 5.545e-10 | within the floor | yes | 3.157e-11 | 9.349e-02 | relocation | no | B0 → B1 |
| 23 | — | 6.893e-13 | 1.306e-06 | relocation | yes | 4.114e-12 | 3.241e-02 | relocation | no | 0 | 1.120e-11 | within the floor | yes | 4.114e-12 | 3.241e-02 | relocation | no | B0 → B1 |
| 24 | — | 3.386e-14 | 5.546e-07 | within the floor | yes | 1.041e-11 | 3.483e-02 | relocation | no | 0 | 1.513e-11 | within the floor | yes | 1.041e-11 | 3.483e-02 | relocation | no | B0 → B1 |

*n = 22 (seeds on which every arm of large_tokamak_nof converged).*

#### iterations and ε (B3) — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2

| pair | n | summed median | summed sum ratio | final-attempt median | final-attempt sum ratio | ε median (evaluations) | ε sum ratio | ε label | ε = 1 on | sweeps median | attempts per seed (base/arm) | constructions disagree |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 → BR | 22 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | trajectory-neutral | 22 | 0.9359 | 0:1/1, 1:1/1, 2:1/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 10:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 17:1/1, 18:1/1, 19:1/1, 22:1/1, 23:1/1, 24:1/1 | 0 |
| B0 → B1 | 22 | 1.0000 | 0.9942 | 1.0000 | 0.9942 | 1.0476 | 1.0411 | trajectory-neutral | 0 | 0.9782 | 0:1/1, 1:1/1, 2:1/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 10:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 17:1/1, 18:1/1, 19:1/1, 22:1/1, 23:1/1, 24:1/1 | 0 |
| B0 → B2 | 22 | 1.0000 | 0.9942 | 1.0000 | 0.9942 | 1.0476 | 1.0411 | trajectory-neutral | 0 | 2.2822 | 0:1/1, 1:1/1, 2:1/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 10:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 17:1/1, 18:1/1, 19:1/1, 22:1/1, 23:1/1, 24:1/1 | 0 |
| B1 → B2 | 22 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | trajectory-neutral | 22 | 2.3338 | 0:1/1, 1:1/1, 2:1/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 10:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 17:1/1, 18:1/1, 19:1/1, 22:1/1, 23:1/1, 24:1/1 | 0 |

*n = 22 (seeds on which every arm of large_tokamak_nof converged).*

#### same optimum per seed and rung — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2

| seed | retried arms | BR → B0 objf | BR → B0 point | BR → B0 kind | BR → B0 same path | B0 → B1 objf | B0 → B1 point | B0 → B1 kind | B0 → B1 same path | B1 → B2 objf | B1 → B2 point | B1 → B2 kind | B1 → B2 same path | B0 → B2 objf | B0 → B2 point | B0 → B2 kind | B0 → B2 same path | B0 → B2 enters at |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | — | 5.602e-15 | 2.552e-11 | within the floor | yes | 6.849e-07 | 5.828e-06 | relocation | no | 2.842e-14 | 6.338e-12 | within the floor | yes | 6.849e-07 | 5.828e-06 | relocation | no | B0 → B1 |
| 1 | BR; B0 | 0 | 0 | within the floor | yes | 3.148e-04 | 7.038e-03 | hop (across clusters) | no | 8.888e-15 | 1.724e-12 | within the floor | yes | 3.148e-04 | 7.038e-03 | hop (across clusters) | no | B0 → B1 |
| 5 | — | 0 | 0 | within the floor | yes | 6.421e-11 | 4.084e-06 | relocation | no | 1.641e-15 | 2.741e-12 | within the floor | yes | 6.420e-11 | 4.084e-06 | relocation | no | B0 → B1 |
| 6 | — | 6.422e-15 | 4.681e-12 | within the floor | yes | 4.101e-07 | 3.935e-06 | relocation | no | 2.036e-14 | 1.951e-12 | within the floor | yes | 4.101e-07 | 3.935e-06 | relocation | no | B0 → B1 |
| 9 | — | 0 | 0 | within the floor | yes | 2.327e-09 | 5.348e-06 | relocation | no | 5.468e-16 | 1.459e-11 | within the floor | yes | 2.327e-09 | 5.348e-06 | relocation | no | B0 → B1 |
| 10 | B1; B2 | 3.131e-12 | 4.299e-10 | within the floor | yes | 3.894e-04 | 1.100e-03 | hop (across clusters) | no | 2.057e-15 | 3.706e-10 | within the floor | yes | 3.894e-04 | 1.100e-03 | hop (across clusters) | no | B0 → B1 |
| 11 | — | 0 | 0 | within the floor | yes | 1.261e-06 | 5.983e-06 | hop | no | 4.099e-16 | 1.449e-10 | within the floor | yes | 1.261e-06 | 5.983e-06 | hop | no | B0 → B1 |
| 12 | — | 0 | 0 | within the floor | yes | 1.911e-09 | 4.231e-06 | relocation | no | 2.272e-14 | 8.502e-12 | within the floor | yes | 1.911e-09 | 4.231e-06 | relocation | no | B0 → B1 |
| 13 | — | 0 | 0 | within the floor | yes | 2.148e-06 | 9.541e-06 | hop | no | 1.571e-14 | 2.428e-12 | within the floor | yes | 2.148e-06 | 9.541e-06 | hop | no | B0 → B1 |
| 15 | — | 2.053e-10 | 3.472e-07 | within the floor | yes | 5.829e-07 | 2.756e-06 | relocation | no | 6.012e-15 | 1.286e-11 | within the floor | yes | 5.829e-07 | 2.756e-06 | relocation | no | B0 → B1 |
| 18 | — | 5.377e-14 | 1.674e-10 | within the floor | yes | 4.165e-10 | 3.515e-06 | relocation | no | 8.251e-15 | 3.451e-12 | within the floor | yes | 4.165e-10 | 3.515e-06 | relocation | no | B0 → B1 |
| 19 | — | 1.970e-13 | 8.959e-10 | within the floor | yes | 4.042e-09 | 1.011e-05 | relocation | no | 1.959e-14 | 1.308e-11 | within the floor | yes | 4.042e-09 | 1.011e-05 | relocation | no | B0 → B1 |

*n = 12 (seeds on which every arm of low_aspect_ratio_DEMO converged).*

#### iterations and ε (B3) — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2

| pair | n | summed median | summed sum ratio | final-attempt median | final-attempt sum ratio | ε median (evaluations) | ε sum ratio | ε label | ε = 1 on | sweeps median | attempts per seed (base/arm) | constructions disagree |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 → BR | 12 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | trajectory-neutral | 12 | 1.0047 | 0:1/1, 1:2/2, 5:1/1, 6:1/1, 9:1/1, 10:1/1, 11:1/1, 12:1/1, 13:1/1, 15:1/1, 18:1/1, 19:1/1 | 1 |
| B0 → B1 | 12 | 0.8333 | 1.3658 | 0.9000 | 1.1004 | 0.8674 | 1.4410 | trajectory changed by ε = 1.4410 | 0 | 0.8017 | 0:1/1, 1:2/1, 5:1/1, 6:1/1, 9:1/1, 10:1/3, 11:1/1, 12:1/1, 13:1/1, 15:1/1, 18:1/1, 19:1/1 | 2 |
| B0 → B2 | 12 | 0.8333 | 1.3658 | 0.9000 | 1.1004 | 0.8674 | 1.4410 | trajectory changed by ε = 1.4410 | 0 | 1.8786 | 0:1/1, 1:2/1, 5:1/1, 6:1/1, 9:1/1, 10:1/3, 11:1/1, 12:1/1, 13:1/1, 15:1/1, 18:1/1, 19:1/1 | 2 |
| B1 → B2 | 12 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | trajectory-neutral | 12 | 2.3434 | 0:1/1, 1:1/1, 5:1/1, 6:1/1, 9:1/1, 10:3/3, 11:1/1, 12:1/1, 13:1/1, 15:1/1, 18:1/1, 19:1/1 | 1 |

*n = 12 (seeds on which every arm of low_aspect_ratio_DEMO converged).*

#### same optimum per seed and rung — st_regression — campaign_optimisation · BR·B0·B2

| seed | retried arms | BR → B0 objf | BR → B0 point | BR → B0 kind | BR → B0 same path | B0 → B2 objf | B0 → B2 point | B0 → B2 kind | B0 → B2 same path | B0 → B2 enters at |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | — | 4.453e-13 | 1.277e-05 | relocation | yes | 1.472e-11 | 9.606e-01 | relocation | no | B0 → B2 |
| 2 | BR | 2.101e-11 | 2.538e-01 | relocation | no | 6.825e-12 | 9.386e-01 | relocation | no | B0 → B2 |
| 3 | — | 4.060e-12 | 6.326e-05 | relocation | yes | 2.540e-11 | 9.398e-01 | relocation | no | B0 → B2 |
| 4 | — | 7.844e-12 | 8.310e-02 | relocation | no | 5.609e-12 | 9.459e-01 | relocation | no | B0 → B2 |
| 5 | B2 | 7.970e-11 | 3.231e-06 | relocation | no | 1.305e-03 | 1.059e-01 | hop (across clusters) | no | B0 → B2 |
| 6 | — | 8.374e-14 | 5.708e-05 | relocation | yes | 6.098e-12 | 8.318e-03 | relocation | no | B0 → B2 |
| 7 | — | 1.375e-13 | 2.797e-05 | relocation | yes | 1.580e-11 | 1.186e-01 | relocation | no | B0 → B2 |
| 8 | — | 7.085e-13 | 1.925e-05 | relocation | yes | 2.131e-11 | 9.586e-01 | relocation | no | B0 → B2 |
| 11 | — | 1.649e-14 | 4.335e-05 | relocation | yes | 1.992e-14 | 4.938e-04 | relocation | yes | B0 → B2 |
| 12 | BR; B2 | 1.311e-02 | 1.000e+00 | hop (across clusters) | no | 1.311e-02 | 1.000e+00 | hop (across clusters) | no | B0 → B2 |
| 13 | — | 5.054e-14 | 3.821e-05 | relocation | yes | 3.553e-12 | 9.529e-01 | relocation | no | B0 → B2 |
| 14 | — | 1.146e-12 | 1.087e-05 | relocation | yes | 5.965e-12 | 9.582e-03 | relocation | no | B0 → B2 |
| 16 | — | 5.675e-14 | 1.531e-04 | relocation | no | 4.099e-12 | 9.554e-01 | relocation | no | B0 → B2 |
| 18 | — | 1.137e-13 | 7.700e-05 | relocation | yes | 1.192e-11 | 5.882e-02 | relocation | no | B0 → B2 |
| 19 | — | 4.838e-13 | 1.228e-05 | relocation | no | 3.384e-12 | 9.556e-01 | relocation | no | B0 → B2 |
| 20 | — | 4.557e-13 | 3.078e-05 | relocation | yes | 5.733e-13 | 9.332e-01 | relocation | no | B0 → B2 |
| 21 | — | 1.178e-14 | 9.256e-06 | relocation | yes | 6.211e-12 | 9.587e-01 | relocation | no | B0 → B2 |
| 22 | — | 2.501e-13 | 3.849e-05 | relocation | yes | 4.463e-13 | 6.545e-01 | relocation | no | B0 → B2 |
| 23 | — | 4.731e-13 | 4.016e-05 | relocation | yes | 9.059e-14 | 3.699e-04 | relocation | yes | B0 → B2 |
| 24 | BR; B2 | 1.305e-03 | 1.704e-01 | hop (across clusters) | no | 1.263e-02 | 8.246e-02 | hop (across clusters) | no | B0 → B2 |

*n = 20 (seeds on which every arm of st_regression converged).*

#### iterations and ε (B3) — st_regression — campaign_optimisation · BR·B0·B2

| pair | n | summed median | summed sum ratio | final-attempt median | final-attempt sum ratio | ε median (evaluations) | ε sum ratio | ε label | ε = 1 on | sweeps median | attempts per seed (base/arm) | constructions disagree |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 → BR | 20 | 1.0000 | 1.4217 | 1.0000 | 0.9373 | 1.0000 | 1.4370 | trajectory changed by ε = 1.4370 | 13 | 1.0246 | 0:1/1, 2:1/2, 3:1/1, 4:1/1, 5:1/1, 6:1/1, 7:1/1, 8:1/1, 11:1/1, 12:1/2, 13:1/1, 14:1/1, 16:1/1, 18:1/1, 19:1/1, 20:1/1, 21:1/1, 22:1/1, 23:1/1, 24:1/3 | 3 |
| B0 → B2 | 20 | 2.2143 | 2.4048 | 2.1667 | 1.5687 | 2.2593 | 2.4432 | trajectory changed by ε = 2.4432 | 2 | 5.8667 | 0:1/1, 2:1/1, 3:1/1, 4:1/1, 5:1/3, 6:1/1, 7:1/1, 8:1/1, 11:1/1, 12:1/2, 13:1/1, 14:1/1, 16:1/1, 18:1/1, 19:1/1, 20:1/1, 21:1/1, 22:1/1, 23:1/1, 24:1/2 | 3 |

*n = 20 (seeds on which every arm of st_regression converged).*

#### same optimum by rung — campaign_optimisation

| configuration | pair | role | n | objf median | objf p90 | threshold p90 | verdict | fails at | hops | across clusters | relocations | within the floor | same path | hops enter at | relocations enter at | hop seeds | yardstick hops too |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | BR → B0 | yardstick | 22 | 2.914e-15 | 5.025e-13 | — | — | — | 0 | 0 | 8 | 14 | 22 | — | — | — | — |
| large_tokamak_nof | B0 → B1 (the lift) | judged | 22 | 2.823e-11 | 4.570e-11 | 1.000e-06 | PASS | — | 0 | 0 | 22 | 0 | 0 | — | B0 → B1 (the lift) 22 of 22 | — | — |
| large_tokamak_nof | B1 → B2 (the partition) | step | 22 | 0 | 0 | — | — | — | 0 | 0 | 0 | 22 | 22 | — | — | — | — |
| large_tokamak_nof | B0 → B2 | judged | 22 | 2.823e-11 | 4.570e-11 | 1.000e-06 | PASS | — | 0 | 0 | 22 | 0 | 0 | — | B0 → B1 (the lift) 22 of 22 | — | — |
| low_aspect_ratio_DEMO | BR → B0 | yardstick | 12 | 5.602e-15 | 3.131e-12 | — | — | — | 0 | 0 | 0 | 12 | 12 | — | — | — | — |
| low_aspect_ratio_DEMO | B0 → B1 (the lift) | judged | 12 | 5.829e-07 | 3.148e-04 | 1.000e-06 | FAIL | p90 | 4 | 2 | 8 | 0 | 0 | B0 → B1 (the lift) 4 of 4 | B0 → B1 (the lift) 8 of 8 | 1*, 10*, 11, 13 | 0 of 4 |
| low_aspect_ratio_DEMO | B1 → B2 (the partition) | step | 12 | 8.888e-15 | 2.272e-14 | — | — | — | 0 | 0 | 0 | 12 | 12 | — | — | — | — |
| low_aspect_ratio_DEMO | B0 → B2 | judged | 12 | 5.829e-07 | 3.148e-04 | 1.000e-06 | FAIL | p90 | 4 | 2 | 8 | 0 | 0 | B0 → B1 (the lift) 4 of 4 | B0 → B1 (the lift) 8 of 8 | 1*, 10*, 11, 13 | 0 of 4 |
| st_regression | BR → B0 | yardstick | 20 | 4.731e-13 | 7.970e-11 | — | — | — | 2 | 2 | 18 | 0 | 13 | — | — | 12*, 24* | — |
| st_regression | B0 → B2 (the partition, its block loops on the feedback couplings at τ = 1e-08; no B1 on this configuration) | judged | 20 | 6.211e-12 | 1.305e-03 | 1.000e-06 | FAIL | p90 | 3 | 3 | 17 | 0 | 2 | B0 → B2 3 of 3 | B0 → B2 17 of 17 | 5*, 12*, 24* | 2 of 3 |

*n = 88 (seed pairs judged, summed over the judged rows).*

#### same optimum per seed and rung — st_regression — supplementary st_census_exact · B0·B2 · census/1e-12

| seed | retried arms | B0 → B2 objf | B0 → B2 point | B0 → B2 kind | B0 → B2 same path | B0 → B2 enters at |
|---|---|---|---|---|---|---|
| 0 | — | 0 | 1.649e-09 | within the floor | yes | — |
| 1 | — | 5.753e-11 | 2.888e-07 | within the floor | no | — |
| 2 | — | 3.558e-12 | 4.282e-05 | relocation | yes | B0 → B2 |
| 3 | — | 2.142e-16 | 3.170e-11 | within the floor | yes | — |
| 4 | — | 2.598e-13 | 4.091e-03 | relocation | yes | B0 → B2 |
| 5 | B2 | 1.263e-02 | 2.158e-02 | hop (across clusters) | no | B0 → B2 |
| 6 | — | 1.456e-14 | 6.058e-06 | relocation | yes | B0 → B2 |
| 7 | — | 1.071e-15 | 3.256e-10 | within the floor | yes | — |
| 8 | — | 1.810e-13 | 1.739e-08 | within the floor | yes | — |
| 9 | — | 1.110e-11 | 2.555e-06 | relocation | no | B0 → B2 |
| 10 | — | 2.556e-10 | 9.189e-04 | relocation | no | B0 → B2 |
| 11 | — | 0 | 9.961e-11 | within the floor | yes | — |
| 12 | — | 4.725e-10 | 1.047e-01 | relocation | no | B0 → B2 |
| 13 | — | 6.626e-13 | 1.963e-08 | within the floor | yes | — |
| 14 | — | 5.761e-13 | 2.752e-05 | relocation | yes | B0 → B2 |
| 15 | — | 1.908e-10 | 1.705e-07 | within the floor | no | — |
| 16 | — | 5.590e-14 | 2.464e-05 | relocation | no | B0 → B2 |
| 18 | — | 1.499e-15 | 3.167e-10 | within the floor | yes | — |
| 19 | — | 6.361e-14 | 1.989e-08 | within the floor | yes | — |
| 20 | — | 1.103e-13 | 6.304e-10 | within the floor | yes | — |
| 21 | — | 1.071e-15 | 4.576e-10 | within the floor | yes | — |
| 22 | — | 8.802e-14 | 1.295e-09 | within the floor | yes | — |
| 23 | — | 6.425e-16 | 5.429e-11 | within the floor | yes | — |
| 24 | B0; B2 | 2.281e-12 | 5.137e-08 | within the floor | no | — |

*n = 24 (seeds on which every arm of st_regression converged).*

#### iterations and ε (B3) — st_regression — supplementary st_census_exact · B0·B2 · census/1e-12

| pair | n | summed median | summed sum ratio | final-attempt median | final-attempt sum ratio | ε median (evaluations) | ε sum ratio | ε label | ε = 1 on | sweeps median | attempts per seed (base/arm) | constructions disagree |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 → B2 | 24 | 1.0000 | 1.0460 | 1.0000 | 0.9709 | 1.0000 | 1.0475 | trajectory-neutral | 16 | 2.1945 | 0:1/1, 1:1/1, 2:1/1, 3:1/1, 4:1/1, 5:1/2, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 10:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 18:1/1, 19:1/1, 20:1/1, 21:1/1, 22:1/1, 23:1/1, 24:2/2 | 2 |

*n = 24 (seeds on which every arm of st_regression converged).*

#### same optimum by rung — supplementary st_census_exact

| configuration | pair | role | n | objf median | objf p90 | threshold p90 | verdict | fails at | hops | across clusters | relocations | within the floor | same path | hops enter at | relocations enter at | hop seeds | yardstick hops too |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| st_regression | B0 → B2 (the partition, its block loops on the feedback couplings at τ = 1e-12; no B1 on this configuration) | judged | 24 | 1.810e-13 | 2.556e-10 | — | — | — | 1 | 1 | 8 | 15 | 16 | B0 → B2 1 of 1 | B0 → B2 8 of 8 | 5* | — |

*n = 24 (seed pairs judged, summed over the judged rows).*


## Appendix B — the gate table after (`--measure gate_table --resume` at `c2295511`)

| gate | plan | binds | verdict | population | compared | mismatched | teeth | record |
|---|---|---|---|---|---|---|---|---|
| `g0prime` | G0 / G0' | every V4 commit, every arm, both phases | **PASS** | 77 files under PROCESS/process/models/ compared byte for byte against c0ae5b28 (git cat-file, never a working tree), plus the file set | 77 | 1 | 4/4 | `runs/gates/g0prime/gate.json` |
| `copy_identity` | — | every V4 commit that touches the experiment's copy of PROCESS | **PASS** | 224 files under PROCESS/process/ compared byte for byte against the source commit f2dc9243 (git cat-file, never a working tree), plus the file set;… | 224 | 8 | 12/12 | `runs/gates/copy_identity/gate.json` |
| `edit_behaviour` | — | the one permitted edit in the copy that is not a rename or a comment | **PASS** | three arms of one probe, no PROCESS run: the copy with the per-run write-set artifact absent, the source commit f2dc9243 (git archive) with it abse… | 3 | 0 | 1/1 | `runs/gates/edit_behaviour/gate.json` |
| `self_containment` | — | the user's requirement in the harness plan §6: nothing in this package is imported from, o | **PASS** | 57 Python file(s): every module under harness/ and experiment_runner.py beside it; 45 line(s) naming either directory, 13 of them executable | 57 | 0 | 1/1 | `runs/gates/self_containment/gate.json` |
| `composition` | — | the harness itself, before any PROCESS run | **PASS** | 8 arms x 3 configurations = 24 pairs | 42 | 0 | 7/7 | `runs/gates/composition/gate.json` |
| `rungs` | — | the harness itself, before any PROCESS run | **PASS** | 11 matrix rows x 8 arms = 88 cells; 6 rung steps | 98 | 0 | 3/3 | `runs/gates/rungs/gate.json` |
| `provenance` | — | the harness itself, before any PROCESS run | **PASS** | one scratch repository, three states | 4 | 0 | 4/4 | `runs/gates/provenance/gate.json` |
| `data` | — | the harness itself, before any PROCESS run | **PASS** | 21 committed file(s) in harness/data/ + the moved predicate module = 22 comparisons; and 9 declared counts (3 configurations x coupling-state compo… | 22 | 0 | 6/6 | `runs/gates/data/gate.json` |
| `run_path` | — | the harness itself, before any PROCESS run | **PASS** | 2 phases x the declared field list; 2 displacement streams; 5 refusals | 12 | 0 | 12/12 | `runs/gates/run_path/gate.json` |
| `resume_identity` | — | every --resume decision and every directory of the shared run pool | **PASS** | 25 Job field(s); 12 by-design pair(s) (9 must differ, 3 must agree); 3 recorded-name row(s); 1168 record(s) under runs/ read by arm name | 1208 | 0 | 11/11 | `runs/gates/resume_identity/gate.json` |
| `capability` | — | the harness itself, before any PROCESS run | **PASS** | every arm/configuration pair whose arms are active | 61 | 0 | 5/5 | `runs/gates/capability/gate.json` |
| `artifacts_check` | — | every committed artifact of every configuration | **PASS** | 22 artifact row(s) over 3 configuration(s) (large_tokamak_nof, low_aspect_ratio_DEMO, st_regression); 119 individual check(s) | 119 | 0 | 3/3 | `runs/gates/artifacts_check/gate.json` |
| `artifacts_derive_inputs` | — | the lifted input file of each pulsed configuration | **PASS** | 3 configuration(s) (large_tokamak_nof, low_aspect_ratio_DEMO, st_regression); the digest gate applies to the 2 pulsed one(s) | 2 | 0 | 4/4 | `runs/gates/artifacts_derive_inputs/gate.json` |
| `artifacts_census` | — | the committed run-time write census, per configuration | **PASS** | 3 configuration(s) (large_tokamak_nof, low_aspect_ratio_DEMO, st_regression); one optimisation census each, taken with the read half of the instrum… | 81 | 0 | 5/5 | `runs/gates/artifacts_census/gate.json` |
| `artifacts_per_run` | — | each configuration's per-run deferral set | **PASS** | 5 (configuration, input file) pair(s) over 3 configuration(s) (large_tokamak_nof, low_aspect_ratio_DEMO, st_regression); the write census is measur… | 16 | 0 | 2/2 | `runs/gates/artifacts_per_run/gate.json` |
| `evaluation_warmup` | — | the warmed evaluation child (V5 plan §6): a harness change, not a driver change | **PASS** | 11 evaluation pair(s) (the gate job set's evaluation half: every arm active on each configuration at seed 1, δ = 0.1, census/1e-08, timers on); 142… | 19876 (1426 + 18450) | 0 | 2/2 | `runs/gates/evaluation_warmup/gate.json` |
| `record_completeness` | G7 | the declared pairing and the failure forensics, in both phases | **PASS** | 2 runs on st_regression (the configuration with the fewest iteration variables, derived); 95 declared field(s) in the optimisation phase and 90 in … | 185 | 0 | 12/12 | `runs/gates/record_completeness/gate.json` |
| `count_neutrality` | GC | each count-neutral driver change (DR9, DR10): every arm the matrix composes, both phases,  | **PASS** | straddles 'item5' at ['cfa0d3ff'] -> 'DR12' at ['24b78e2d', 'd08e8ab4']: a count-neutrality result.  22 run pair(s) = 11 evaluation(s) + 11 optimis… | 50114 (3989 + 46125) | 0 | 4/4 | `runs/gates/count_neutrality/gate.json` |
| `prime_map` | G2 | the arrangement's method-level move in its once-per-evaluation form: inert once the first- | **PASS** | (i) 6 arrangement/configuration pair(s); 12 evaluations; 5026 components compared, 0 differing.  (ii) 6 primed pair(s) of GC's DR9/DR10 straddle; 1… | 17591 (5026 + 12565) | 0 | 3/3 | `runs/gates/prime_map/gate.json` |
| `entry_and_warm` | G6 | the evaluation phase, on every configuration | **PASS** | 8 entry pair(s) at seed 1; 5 warm run(s); 16 evaluations | 6717 | 0 | 3/3 | `runs/gates/entry_and_warm/gate.json` |
| `test_set` | GT | the census test set every block loop stops on (V5 plan §3; item 6, D32; driver change DR11 | **PASS** | 8 full-set run(s) over 3 configuration(s) and arms ['A0', 'A1', 'A2'] at seed 1; 8 binding drop(s): 3 bite, 5 not individually binding; 8 control(s… | 13424 | 794 | 4/4 | `runs/gates/test_set/gate.json` |
| `switch_composition` | G5 | B2, on every configuration where it is active | **PASS** | 3 configuration(s) where B2 is active; 6 optimisations; 42 switch names and 10 run values per configuration | 156 | 0 | 4/4 | `runs/gates/switch_composition/gate.json` |
| `switch_neutrality` | G1 | each driver change, run per change and never batched | **PASS** | one capture names no commit, so what this run straddles cannot be stated:  6 run pair(s) = 3 configuration(s) x 2 reference arm(s); 3669 determinis… | 54988 (3669 + 51319) | 0 | 9/9 | `runs/gates/switch_neutrality/gate.json` |
| `reproduction` | GR | the harness rewrite and the experiment's copy of PROCESS, once, at the copy commit before  | **PASS** | 20 runs (14 optimisations + 6 evaluations) over 3 configurations; 270 values in the committed reference, 14 of them excluded by name with their rea… | 256 | 0 | 8/8 | `runs/gates/reproduction/gate.json` |
| `output_path` | G9 | the removal of the output-time loop from the arms whose matrix cell turns it off, on every | **PASS** | 11 run(s) at seed 0 = every optimisation-phase arm on every configuration where it is active, each composed from the experiment's matrix; 3825 coup… | 3879 (3825 + 54) | 0 | 4/4 | `runs/gates/output_path/gate.json` |
| `written_file_gap` | — | the written-file gap on the one-call output path: BR, B1 and B2 at seed 0 on the pulsed co | **PASS** | 6 run(s) at seed 0, unperturbed = 3 arm(s) (BR, B1, B2) x 2 pulsed configuration(s), each composed from the experiment's matrix with no override bu… | 42 | 0 | 4/4 | `runs/gates/written_file_gap/gate.json` |
| `tally_contracts` | — | every table the tally emits, and the cells it reproduces | **PASS** | 20 reference run(s) (14 optimisations + 6 evaluations) over 3 configurations; 236 published cells, no tolerance on any of them; and 94 table(s) emi… | 538 (302 + 236) | 0 | 18/18 | `runs/gates/tally_contracts/gate.json` |
| `run_kind_separation` | — | every record this package makes, and every population the tally builds | **PASS** | 1168 run record(s) under runs/, of which 553 are covered by the tally's 3 published source(s) (the campaign family) and 31 by its 2 unpublished; ru… | 2274 | 0 | 7/7 | `runs/gates/run_kind_separation/gate.json` |
| `stage_provenance` | — | the harness itself, before any PROCESS run | **PASS** | a scratch records directory this check writes itself — 3 verdict record(s) and 3 stage record(s) — broken 4 ways; a scratch census record, stamped … | 13 | 0 | 5/5 | `runs/gates/stage_provenance/gate.json` |
29 PASS, 0 FAIL, 0 not run; 167 of 167 teeth tripped.

## Appendix C — `git diff b84892e8 65dd0044 -- paper_tables.md`

```diff
diff --git a/arch_surgery/MDA_partitioning_experiment_v5/paper_tables.md b/arch_surgery/MDA_partitioning_experiment_v5/paper_tables.md
index c8045413..41751cd8 100644
--- a/arch_surgery/MDA_partitioning_experiment_v5/paper_tables.md
+++ b/arch_surgery/MDA_partitioning_experiment_v5/paper_tables.md
@@ -23,7 +23,7 @@ One column per arm, one row per switch, from `harness/experiment/arms.py`'s matr
 | | **AR** | **A0** | **A1** | **A2** | **BR** | **B0** | **B1** | **B2** |
 |---|---|---|---|---|---|---|---|---|
 | MDA solve | upstream | flat | flat | partitioned | upstream | flat | flat | partitioned |
-| stopping rule | objf/conf | y @ τ | y @ τ | y @ τ | objf/conf | y @ τ | y @ τ | y @ τ |
+| stopping rule | objf/conf | feedback couplings @ τ = 1e-08 | feedback couplings @ τ = 1e-08 | feedback couplings @ τ = 1e-08 per block | objf/conf | feedback couplings @ τ = 1e-08 | feedback couplings @ τ = 1e-08 | feedback couplings @ τ = 1e-08 per block |
 | block schedule | — | (one block) | (one block) | one pass | — | (one block) | (one block) | one pass |
 | arrangement · node (build after physics) | — | — | — | ✓ | — | — | — | ✓ |
 | arrangement · method (prime) | — | — | — | ✓ | — | — | — | ✓ |
@@ -40,7 +40,7 @@ One column per arm, one row per switch, from `harness/experiment/arms.py`'s matr
  & AR & A0 & A1 & A2 & BR & B0 & B1 & B2 \\
 \hline
 MDA solve & upstream & flat & flat & partitioned & upstream & flat & flat & partitioned \\
-stopping rule & objf/conf & y @ $\tau$ & y @ $\tau$ & y @ $\tau$ & objf/conf & y @ $\tau$ & y @ $\tau$ & y @ $\tau$ \\
+stopping rule & objf/conf & feedback couplings @ $\tau$ = 1e-08 & feedback couplings @ $\tau$ = 1e-08 & feedback couplings @ $\tau$ = 1e-08 per block & objf/conf & feedback couplings @ $\tau$ = 1e-08 & feedback couplings @ $\tau$ = 1e-08 & feedback couplings @ $\tau$ = 1e-08 per block \\
 block schedule & -- & (one block) & (one block) & one pass & -- & (one block) & (one block) & one pass \\
 arrangement · node (build after physics) & -- & -- & -- & $\checkmark$ & -- & -- & -- & $\checkmark$ \\
 arrangement · method (prime) & -- & -- & -- & $\checkmark$ & -- & -- & -- & $\checkmark$ \\
@@ -267,7 +267,7 @@ Post-processing & 5734 & 3895 & -- & 1 & 0.00 & 0.00 [0.00, 0.00] \\
 
 **phase A in wall clock, ms per evaluation** — Per configuration, arms as columns, ms per `call_models` evaluation: each module's own model time, the block loops' convergence test (read plus residual) and dispatch (the sweep body less its nodes and its test), the objective-and-constraints layer, the unattributed residual, and the evaluation's measured wall as Total; ratio of means and per-run median with [min, max] as the count tables. Harness-only costs — the exit-audit sweep, the state snapshots, the census hooks, the record assembly — are excluded from every cell (plan §6). Context, never evidence (D33).
 
-**phase B in wall clock, s per optimisation** — As the phase A table, per whole optimisation in seconds, with the optimiser's own time (solve-phase wall less every evaluation) and the fixed per-run term (process start, imports, numba cache load, input parse, output writing, the once-per-run schedule derivation); Total is the run's wall less the harness-only costs (plan §6).
+**phase B in wall clock, s per optimisation** — As the phase A table, per whole optimisation in seconds, with the optimiser's own time (solve-phase wall less every evaluation) and the fixed per-run term (process start, imports, numba cache load, input parse, output writing, the once-per-run schedule derivation); Total is the run's wall less the harness-only costs (plan §6). **The module rows include one numba cache load per run**: a phase B run's first evaluation is not warmed (the fixed per-run term ends at its start), so its module rows carry the per-process cache load the warmed phase A records measure as warm-up less measured model time — a median of 0.26–0.44 s per run over the 11 configuration and arm rows, 0.6–3.3 % of the median module time per run of the arm's phase B twin, the same order in every arm (`--timing cache-load`, record at `c2295511`).
 
 **cost breakdown, phase B** — Per configuration and arm: seconds per optimisation and ms per evaluation with the share of the total. Whether the architecture changes the overhead is read off the B0 and B2 columns of the per-sweep rows, normalised per evaluation (plan §6).
 
@@ -434,17 +434,17 @@ Per configuration and arm: the starts offered, the accepted optima (`status == o
 
 One row per check of plan §8, in its order. A gate's verdict is read from its record through the `gate_table` stage record, which this generator refuses when the verdict records have been re-made, removed or added to since the stage ran; `not pressed` is a gate with no verdict record (a declared placeholder that refuses, or one never pressed) or a rule that is not yet a construction. A verdict is PASS only with every tooth tripped.
 
-*the gate_table stage record read 30 record(s) at ['0353c52471c95adbc903274ef93e82da351a200d', '75b9e9d4e1f6658d13558d7a909a1bd139cfbe09'], and every one of them is byte-identical to what is on disk now*
+*the gate_table stage record read 30 record(s) at ['0353c52471c95adbc903274ef93e82da351a200d', '75b9e9d4e1f6658d13558d7a909a1bd139cfbe09', 'c2295511298249638e0c2e9a1bb3620dfc1bbe11'], and every one of them is byte-identical to what is on disk now*
 
 | check | plan | verdict | detail |
 |---|---|---|---|
-| physics frozen | G0 | **PASS** | `g0prime` at `75b9e9d4`: 1 of 77 mismatched; 4/4 teeth |
-| switch neutrality | G1 | **PASS** | `switch_neutrality` at `75b9e9d4`: 0 of 54988 mismatched; 9/9 teeth |
+| physics frozen | G0 | **PASS** | `g0prime` at `c2295511`: 1 of 77 mismatched; 4/4 teeth |
+| switch neutrality | G1 | **PASS** | `switch_neutrality` at `c2295511`: 0 of 54988 mismatched; 9/9 teeth |
 | matched accuracy — whole-state audit at 0 components above τ | A1 | **PASS** | `tok` A2/A1: similarity PASS, runs with a component ≥ τ A1 0 / A2 0 → **PASS**; `lad` A2/A1: similarity PASS, runs with a component ≥ τ A1 0 / A2 0 → **PASS**; `st` A2/A0: similarity PASS, runs with a component ≥ τ A0 0 / A2 0 → **PASS** (whole-state statistic, D36; the second half of the rule is the count column) |
 | fixed-point distance between arms | A2 | **reported, no rule** | the tally's fixed-point distance table (plan §5 A2) |
-| same optimum, attributed where it fails | B1 | **see detail** | `tok` B0 → B1: PASS; `tok` B0 → B2: PASS; `lad` B0 → B1: FAIL; `lad` B0 → B2: FAIL; `st` B0 → B2: FAIL (V4's check 1 construction; V5's attribution rule is item 4's, pending) |
-| entry pairing | G6 | **PASS** | `entry_and_warm` at `75b9e9d4`: 0 of 6717 mismatched; 3/3 teeth |
-| arm composition | G5 | **PASS** | `switch_composition` at `75b9e9d4`: 0 of 156 mismatched; 4/4 teeth |
-| output-path equivalence | G9 | **PASS** | `output_path` at `75b9e9d4`: 0 of 3879 mismatched; 4/4 teeth |
-| the test set's teeth | GT | **PASS** | `test_set` at `75b9e9d4`: 794 of 13424 mismatched; 4/4 teeth |
+| same optimum, attributed where it fails | B1 | **PASS tok · FAIL lad, st** | `tok` B0 → B1 PASS, B0 → B2 PASS (objf p90 4.6e-11 ≤ 1.0e-06; 0 hops of 22); `lad` B0 → B1 FAIL, B0 → B2 FAIL at p90 (objf p90 3.1e-04 > 1.0e-06): 4 hops of 12 (2 across clusters; seeds 1*, 10*, 11, 13), entering at B0 → B1 (the lift) 4 of 4; B1 → B2 (the partition) adds none: objf median 8.9e-15, p90 2.3e-14, same path on 12 of 12; the yardstick BR → B0 also hops on 0 of 4 of these seeds; `st` B0 → B2 FAIL at p90 (objf p90 1.3e-03 > 1.0e-06): 3 hops of 20 (3 across clusters; seeds 5*, 12*, 24*), entering at B0 → B2 3 of 3 — the partition, its block loops on the feedback couplings at τ = 1e-08; no B1 on this configuration; the yardstick BR → B0 also hops on 2 of 3 of these seeds (hop: objective difference above the floor; * = a retried arm; the tally's `same optimum by rung` table, plan §5 B1) |
+| entry pairing | G6 | **PASS** | `entry_and_warm` at `c2295511`: 0 of 6717 mismatched; 3/3 teeth |
+| arm composition | G5 | **PASS** | `switch_composition` at `c2295511`: 0 of 156 mismatched; 4/4 teeth |
+| output-path equivalence | G9 | **PASS** | `output_path` at `c2295511`: 0 of 3879 mismatched; 4/4 teeth |
+| the test set's teeth | GT | **PASS** | `test_set` at `c2295511`: 794 of 13424 mismatched; 4/4 teeth |
 
```

---

## Orchestrator's critical assessment (protocol §5) — verdict: merge

*Written 2026-09-30 by the orchestrating session, the user present. Checked differently from the agent.*

**Checked.** (1) `git diff --name-only b84892e8..fca03a32`: 17 files — tally, generator, one gate, the
matrix, the runner, the README, `paper_tables.md`, this report; **0 paths under the V5 driver copy
`PROCESS/`, 0 under `process/models/`, 0 under `_v4/`**; worktree clean; `merge-tree`: no conflict.
(2) `compileall` clean and `--gates` constructs the registry at the tip. (3) The diff of `paper_tables.md`
read line by line: the switch matrix's stopping-rule row, the phase B wall-clock caption, the verification
table's B1 row, the records-read line and the gate rows' stamps — **no count cell and no wall-clock cell
moved**, which is the brief's condition. (4) The gate-table record on disk: 29 PASS; 28 verdicts at
`c2295511` on a clean tree and `record_completeness` kept at `75b9e9d4` (the agent's declared deviation: its
tooth re-makes one smoke evaluation, and the brief said no PROCESS run — the right call); 553 campaign
records present and untouched.

**Read against the rulings.** Item 4 as the list reduced it: the statistic kept, the attribution per seed and
rung beside it — `lad`'s failures enter at the lift and none at the partition, `st`'s at the test set at
1e-8, with the yardstick itself hopping on two of the three st seeds, which is st's own fragility (A96).
Item 1: the verdict and its threshold are gone, every number kept, ε labelled by the plan's rule; the paper's
iterations table is untouched (the user, 2026-09-30, confirmed the table stays). The matrix cell is read
from the campaign's settings. I-37: fixed with a tooth and shown PASS composed both ways over the existing
records; a whole `--campaign` press through the new function is unpressed and costs nothing to leave so —
**I-37 closed on that evidence**. The hop count on `lad` reads 4 of 12 here against "2/12" in A102's
clustering column: two definitions (objective difference above the floor, against the clustering
statistic); the attribution table's is the plan's.

**Queue consequences at merge.** A103 merged; I-37 closed; V5 list items 1 and 4 done; the README rewrite
(plan §8) done; what remains for V5 is the experiment report, after the user's decision on st.
