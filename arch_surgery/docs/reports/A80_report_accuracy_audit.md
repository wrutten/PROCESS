# A80 (report-accuracy-audit) — the V4 report, sentence by sentence against its tables

> **Document status** — **OPEN.** Task report of **A80 (report-accuracy-audit)**, branch
> `A80-report-accuracy-audit` off `architecture_surgery` at `589138ef` (after A79 (report-captions)).
> The user's instruction (2026-09-15): *"critically reassess the accuracy of the experiment_report
> v4."* The auditor is not the author of §5/§6. **Zero PROCESS runs**; every number below is a cell of
> `EXPERIMENT_REPORT.md` / `RESULTS_TABLES_FULL.md` at `0d407ca7`, a line of
> `report_counts_check.py`'s output at that commit, or a gate verdict record named with the commit it
> ran at. Arm names are today's (`AR/A0/A1/A2`, `BR/B0/B1/B2`); the records stamp their day's and were
> read through `records.read` (trap T16).

## 1. Verdict

**147 findings rows across §4, §5, §6, §1–§3 (as built), the pre-declared expectations, the
cross-references, Appendices A–C and the denominators: 89 hold, 53 corrected (45 distinct
corrections — passes 4, 5 and 7 re-list eight of the earlier passes' under their own heading), 1
withdrawn, 4 cannot be verified from this folder's records.** A row is one sentence or one group of
numbers read against one cell; a row that holds in part and is corrected in part counts as corrected.
No headline number
moved: every cost ratio, every matched-accuracy residual, every check-1/check-2 verdict and every
gate count in §4–§6 is the cell it cites. What was wrong sits one layer down — in the sentences that
*interpret* a cell (a pre-declared expectation read against the wrong arm pair; a sum called a
per-run figure; a range that excludes both values it summarises) and in the population description
of the one hostile configuration. Three findings change what a reader takes away:

1. **The pre-declared `ε = 1` expectation was reported as refuted; it holds exactly.** §3.5 declared
   it on `B1 → B2`. §4.3 read Table D.5's `B0 → B2` ε (1.0476 on nof) against it and wrote "does not
   hold in evaluations on nof"; §5.1 defended it with *iterations*, a different quantity. The records
   say `B1` and `B2` take the same number of evaluations on **22 of 22 and 11 of 11** seeds. The
   `B1 → B2` row the plan said would be "reported beside" was never in the check-2 table; it is now
   (Tables D.70–D.72, column *ε = 1 on*). Both sentences are corrected in place.
2. **"28 crashed, all with PROCESS's own RuntimeError" is 20 + 8.** Eight of the 28 records the
   harness stamps `crashed` are the coupling-state loop refusing at its 20-sweep cap
   (`ModuleSolveFailure`, block `FLAT` in `B0`/`B1`, `M1` in `B2`), on the low-aspect-ratio machine
   only. Tables D.61–D.63 always split them; the header, §4 and §5.7 did not.
3. **The low-aspect-ratio seed set's 14 lost seeds were mis-described.** "13 configuration-invalid —
   2 crash in every arm and the rest fail to converge in at least one" conflates two definitions.
   Configuration-invalid means *no* arm reached an accepted optimum: 2 crash everywhere, **9 exhaust
   VMCON's four-attempt retry ladder with `ifail = 5` in every arm** (finished runs, counted *ok* in
   Table D.62), 2 have `BR` exhausting the ladder while the three coupling-state arms hit their cap.
   The fourteenth seed (10) is the **one** start lost to the intervention arms alone; accepted optima
   are 12 / 12 / 11 / 11 per arm. §5.7's "the intervention arms fail on 1–3 more starts than the
   incumbent" is restated in both counts.

**Known defects fixed (brief pass 2):** issue **I-26** closed — check 2's evaluation column reads
`sweeps_per_eval.n_evaluations` in both implementations, the old `n_model_calls` ratio kept beside as
*sweeps median*, the schema sentence corrected (`n_model_calls` is the driver's count of dispatch-body
sweeps); §5.8's "per optimisation" sum corrected and the cost table given a per-run column; Table
D.5's summed `n = 55` gone (n per configuration); `tally_contracts`' two-count cell shows its parts
(and so do G1's, G9's and G8's). A76/A78/A79 left nothing else for this task.

**One thing needs the user's ruling (§9): the predicate trial's pre-declared adoption rule was not
applied.** §3.6 says gates 1–3 passing plus a neutral measurement *adopts* `mixed`; G8 passed and its
12 pairs were neutral; the campaign ran and is reported on `frozen`. §5.6 now says so and defers to
the user rather than adopting retroactively. Nothing in the acceptance tables depends on the ruler.

**Gates at the end:** `recomputation` 14 445 / 0 over 101 tables (from 14 394; the 51 new cells are
the new columns and rows), `tally_contracts` 559 / 0 (303 + 256), `run_kind_separation` 3 000 / 0,
`self_containment` 52 / 0, `--measure gate_table --resume` 30 PASS / 0 FAIL / 161 of 161 teeth;
`--plan-tables check` IDENTICAL for both documents with 0 dangling references; 80 tables in Appendix D
before and after (no number shifted, T17); stamp survey 1 102 records, **0 whose commit changed, 0
new**; `merged_names_check.py`, `harness_survey.py`, `--selfcheck` PASS. **0 PROCESS runs.**

## 2. The findings table

Verdicts: *holds* (cell named, digits equal, rounding stated); *corrected* (edited in place, marked
"A80" in the sentence, listed in Appendix C); *withdrawn* (no cell can carry it); *cannot verify*
(the records do not hold the quantity). "counts §n" = `report_counts_check.py`'s section.

### 2.1 Pass 1 — §4, §5, §6 against Appendix D and the companion file

| # | location | claim | evidence | verdict |
|---|---|---|---|---|
| 1 | header, §4 intro | 949 records, 921 ok, 28 crashed | counts §1: 949 = 3 + 275 + 198 + 198 + 275; 921 `status ok`; 28 `status crashed` — of which `failure_class` crashed 20, unconverged 8 | **corrected**: "28 not ok — 20 crashed, 8 the loop's 20-sweep cap" |
| 2 | §4 intro, §5 intro | denominators: 25 runs per arm in every evaluation-phase source | Tables D.55–D.60: 20 / 19 / 14 per arm; D.49–D.51: 1 | **corrected**: 25 in the displaced regime, 20/19/14 at the stencil points, 1 entry reference |
| 3 | §4 intro | seed sets 22 / 11 / 22 of 25 (D.64–D.66) | D.64–D.66 n column; counts §3 | holds |
| 4 | §4.1 | 30 PASS, 0 FAIL, 161/161 teeth (D.1) | D.1 footer; counts §10 | holds |
| 5 | §4.1 | GR 256 of 256; G1 0 of 54 144 "values" | D.1 rows; G1's 54 144 = 2 825 record values + 51 319 output-file lines | holds (GR); **corrected** (G1: the two counts named) |
| 6 | §4.1 | recomputation 101 tables, 14 394 cells, 0 mismatched | D.1 at `589138ef`; now 14 445 after the I-26 columns | holds at its commit; §4.4 and §4.1 read the re-rendered cell |
| 7 | §4.1 | `tally_contracts` reproduces the 256 reference cells | D.1 population text; its 559 = 303 + 256 | holds; **corrected** to name the two counts |
| 8 | §4.1 | "The one row reading 1 mismatched and PASS is `g0prime`" | D.1: `copy_identity` PASS with 7 mismatched (its 7 permitted-edit files, listed in `runs/gates/copy_identity/gate.json`) | **corrected**: two such rows, both named |
| 9 | §4.2 RQ1 | 0.5625 / 0.5772 / 0.5016 pooled; medians 0.5714 / 0.5714 / 0.4921; worse on 0 of 25 | D.13–D.15 `A2` rows | holds |
| 10 | §4.2 | 60.5 / 59.6 / 61.5 against 107.5 / 103.3 / 122.6 | D.13–D.15 node calls / eval | holds |
| 11 | §4.2 | block ratios 0 / 0.1953–0.2033 / 0.5859–0.6098–0.5137 / 0.7812–0.8130–0.6849 / 1.0078–0.9919–1.0000 | D.7 | holds |
| 12 | §4.2 | prime 13.2 / 12.9 / 14.8 per evaluation | D.13–D.15 arrangement·method calls | holds |
| 13 | §4.2 | restricted residual identical `A1`/`A2`: 3.833e-10, p90 1.671e-08; 0 on lad; `A0`/`A2` on st 5.372e-09 / 2.023e-08; mixed ruler same or lower on every row | D.25–D.27 | holds |
| 14 | §4.2 | distance 5.094e-12 / 0 / 1.227e-11 median, p90 1.838e-10 / 0 / 4.620e-11, worst 2.709e-10 / 0 / 6.565e-11; 0 of 25 pairs ≥ τ; 0 unclean | D.34–D.36 headline rows | holds |
| 15 | §4.2 | whole-state `A2` median 2.435 / 0.1816 / 0.2575 | D.25–D.27 | holds |
| 16 | §4.2 | stencil 0.6214 / 0.6399 / 0.5767 (0.6071 / 0.6071 / 0.5714); 0.6405 / 0.6609 / 0.5583 (0.6071 / 0.7143 / 0.5238); worse 0 of 20 / 19 / 14 | D.16–D.21 | holds |
| 17 | §4.2 | stencil distance 2.579e-12 / 0 / 1.116e-10 forward, 0 / 0 / 5.339e-11 backward; 0 pairs ≥ τ | D.37–D.42 | holds |
| 18 | §4.2 | nof backward `A0/AR` 1 of 20 ≥ τ, worst 2.645e-06, column 19 | D.40 | holds |
| 19 | §4.2 | ownership rung 0.9275 / 0.9840 pooled, median 1.0000, worse 0; residual 154.6 s / 525.8 s, 6.298e-02 / 5.275e-02 | D.43–D.44 | holds |
| 20 | §4.2 | `A1/A0` 9.665e-02 / 7.026e-02, 25 of 25 ≥ τ; `A2/A0` same | D.34–D.35 | holds |
| 21 | §4.2 RQ4 | `AR` 0.9688 of `A1`, `A0` 1.0781 of it; 0.8425 of `A0` on st; 105.0 on every lad seed | D.13–D.15 (brackets [105, 105]) | holds |
| 22 | §4.2 | `AR` residual 2.624e-08 / 0 / 1.539e-07 vs `A0` 5.042e-10 / 0 / 5.372e-09; p90s | D.25–D.27 | holds |
| 23 | §4.2 machinery | "25 of 25 per arm in every source and configuration" | D.55–D.60 read 20 / 19 / 14 | **corrected** |
| 24 | §4.2 | predicate trial 8 152 / 0, 0 verdict changes | D.1 `predicate_mode` (8 068 + 84); F.13 | holds |
| 25 | §4.3 population | nof: seeds 5, 20, 21 crash in all four arms; 22; no retry | D.61, D.64; counts §3–§4 | holds |
| 26 | §4.3 | lad: "13 configuration-invalid — 2 crash in every arm and the rest fail to converge in at least one (`B0` 2, `B1` 3, `B2` 3 unconverged)" | counts §3: 14 outside the set; invalid 13 = 2 crashed + 9 `ifail = 5` in every arm after 4 attempts + 2 (`BR` ladder / others capped); seed 10 lost to `B1`/`B2` alone; accepted 12 / 12 / 11 / 11; F.17 | **corrected** |
| 27 | §4.3 | lad retried 12 / 10 / 10 / 10 across 25 | D.65; counts §3 | holds |
| 28 | §4.3 | st: every start finished, 1 configuration-invalid, set 22, retried 5 / 3 / 2 | D.63, D.66; counts §3 (two more seeds lost to one arm's `ifail = 5` each — added) | holds; completed |
| 29 | §4.3 RQ2 | 0.6395 / 0.4504 / 0.5331; medians 0.6452 / 0.5237 / 0.5911; worse 0 / 2 / 0 | D.73–D.75 | holds |
| 30 | §4.3 | without retried: lad 0.6594 (0.5371, n = 10); st 0.5439 (n = 21); nof none | D.73–D.75 | holds |
| 31 | §4.3 | per-module pooled ratios and the nof M2 median 0.8765, 1 of 22 above 1, [0.761, 1.013] | D.2–D.4 | holds |
| 32 | §4.3 | "the two seeds on which `B2` took more evaluations show as 2 of 11" | D.5: 3 seeds took more evaluations, 2 more node calls | **corrected** |
| 33 | §4.3 | 63 / 63 / 21 / 24 calls outside the solve phase | D.4: `B2` on st reads 25 | **corrected** (25 for `B2` on st) |
| 34 | §4.3 D.5 | ρ 0.6159 / 0.6192 / 0.5858, brackets, 0 above 1; ε nof 1.0476 (mean 1.0437, 19 of 22, 640 vs 614.7); iterations 1.0000; `B1` 640; lad 0.8468 (3 of 11, 6.450, mean 1.4816); st 1.0000 (5 of 22); R medians | D.5 | holds |
| 35 | §4.3 D.5 | "The ε = 1 expectation of §3.5 therefore holds in iterations and does not hold in evaluations on nof" | §3.5 declares ε = 1 on `B1 → B2`; counts §7: ε(B1) = ε(B2) on 22/22 and 11/11 seeds; Tables D.70–D.71 `B1 → B2` row *ε = 1 on* 22 / 11 | **corrected**: holds exactly; the 1.0476 is `B0 → B2`, the stencil column 22/21 |
| 36 | §4.3 check 1 | medians 2.823e-11 / 4.101e-07 / 3.467e-13; p90 4.570e-11 / 2.148e-06 / 3.510e-09; yardstick medians; PASS/FAIL/PASS; 1 hop of 11, 2 below resolution; st hops 2 of 22 and 1 of 22; `B0 → B1` identical on lad | D.67–D.69 | holds |
| 37 | §4.3 check 2 | 1.0000 / 0.8125 / 1.0000 PASS; sums 0.9942 / 0.7012 / 0.9530; final-attempt agrees on nof, differs 1 / 1 | D.70–D.72 | holds |
| 38 | §4.3 check 2 | "*evaluations median* column reads `n_model_calls` and is not ε (I-26)" | I-26 closed: the column is ε, 1.0476 / 0.8468 / 1.0000, sweeps beside 2.6524 / 2.1169 / 2.7767 | **corrected** (the defect fixed, the sentence rewritten) |
| 39 | §4.3 other rungs | `BR → B0` 0.9756 / 1.0300 / 1.1968; `B0 → B1` 1.0077 / 0.6919, medians 1.0151 / 0.8049, 18 of 22 worse; lift 1.659e-05 / 5.480e-06 s, 2.304e-09 / 6.744e-10 | D.73–D.75, D.79–D.80 | holds |
| 40 | §4.3 accuracy | `B2` 0 / 0 / 7.497e-12 median, max 7.257e-16 / 5.315e-15 / 3.587e-11; `B0` 1.150e-11 / 0 / 4.894e-14; `BR` inf on lad, 1 on two of 23 runs | D.76–D.78; F.48 | holds |
| 41 | §4.3 cost beside | prime calls 117 281 / 157 504 / 280 776 "summed over its 22 / 11 / 22 runs" | D.73–D.75; counts §6 (Σ equal) | holds |
| 42 | §4.3 cost beside | "per evaluation they are the 13.2 / 12.9 / 14.8 of Tables D.13–D.15" | counts §6: one prime call per dispatch sweep on all 55 `B2` runs; per run 5 331.0 / 14 318.5 / 12 762.5; per evaluation 8.33 / 8.35 / 9.07 | **corrected** |
| 43 | §4.3 | output loop exactly two sweeps in `BR`/`B0`, none in `B1`/`B2`; attempt identity residual 0 | F.16/F.19/F.22, F.15/F.18/F.21 | holds |
| 44 | §4.4 | 101 tables, 14 394 cells, 0 mismatched | D.1 at `589138ef`; 14 445 now — §4.4's number is D.1's cell and reads with it | holds (the cell moved with the fix) |
| 45 | §5.1 `A1 → A2` | 0.56 / 0.58 / 0.50 (0.571 / 0.571 / 0.492); V2 context 0.522 / 0.568 / 0.502; stencil 0.62 / 0.64 / 0.58, 0.64 / 0.66 / 0.56 | D.13–D.21; §3.4 | holds (rounded) |
| 46 | §5.1 | "the plan's transfer statement (§3.4)" | the statement is §3.5 | **corrected** to §3.4–§3.5 |
| 47 | §5.1 | matched accuracy 3.8e-10 / 1.7e-8; 0; 5.4e-9 / 2.0e-8; whole-state 2.4 / 0.18 / 0.26 | D.25–D.27 | holds (rounded) |
| 48 | §5.1 fixed point | 5.1e-12 / 0 / 1.2e-11 etc.; lad bit-identical over every restricted component | D.34–D.36; A76's assessment checked the hex | holds |
| 49 | §5.1 | `A0/AR` 2.6e-8 / 0 / 1.5e-7; `A1/A0` 9.7e-2 / 7.0e-2, argmax `power.qac` / `power.e_plant_net_electric_pulse_*` | D.34–D.35 | holds |
| 50 | §5.1 `A0 → A1` | 0.93 / 0.98, 1.00, 0; 155 s / 526 s, 6.3 % / 5.3 % | D.43–D.44 | holds (rounded) |
| 51 | §5.1 `AR → A0` | "0.97 and 0.84 pooled against `A0`" | D.13: 0.9688 is against `A1`; `AR/A0` = 0.8986 (counts §8); st 0.8425 | **corrected** |
| 52 | §5.1 | "a factor of 30–50" | counts §8: 52.0 and 28.7 — the range excludes both | **corrected** to 52 and 29 |
| 53 | §5.1 | both stop after exactly five sweeps on every lad seed | D.14: 5.00 sweeps, [105, 105] | holds |
| 54 | §5.1 `B0 → B1` | 1.008 / 0.692, 1.015 / 0.805; 0.81 / 0.70; two sweeps; lift 1.7e-5 / 5.5e-6 s | D.73–D.74, D.71, F.16/F.19, D.79–D.80 | holds |
| 55 | §5.1 `B1 → B2` | 0.640 / 0.450 / 0.533 etc.; `BR → B0` 0.976 / 1.030 / 1.197 vs 0.98 / 1.03 / 1.16 | D.73–D.75 | holds |
| 56 | §5.1 | "The ε = 1 expectation holds where it was pre-declared: the summed-over-attempts iteration median is identical for `B1` and `B2`" | the expectation is in evaluations; D.70–D.71 `B1 → B2` row: ε = 1 on 22 / 11 | **corrected**: stated in evaluations, per seed |
| 57 | §5.1 | dispatch 2.7 / 2.1 / 2.8× sweeps in `B2` | new *sweeps median* column 2.6524 / 2.1169 / 2.7767 (had no cell) | holds; given its cell |
| 58 | §5.1 (a) | 4.1e-7 / 2.15e-6 FAIL, 1 hop of 11, 2 below resolution, yardstick 2.0e-13; nof 2.8e-11 / 4.6e-11; st 3.5e-13 / 3.5e-9 | D.67–D.69 | holds |
| 59 | §5.1 (a) | "a slightly different optimum on 2 of 11 seeds" | counts §11: 3 of 11 pairs above the floor (1.26e-6, 2.15e-6, 3.15e-4); the hop is on the retried seed | **corrected** |
| 60 | §5.1 (b) | "Thirteen seeds are configuration-invalid: 2 crashed in every arm, and the rest failed to converge in at least one arm" | as #26 | **corrected** |
| 61 | §5.2 | 0.56 → 0.64, 0.58 → 0.45, 0.50 → 0.53; factors 1.14 / 0.78 / 1.06 | quotients of D.7 and D.73–D.75 cells (0.6395/0.5625 = 1.137, 0.4504/0.5772 = 0.780, 0.5331/0.5016 = 1.063) | holds (derived; now said so) |
| 62 | §5.2 | "by up to a fifth"; "good to ±20 %" | 0.78 is 22 % off | **corrected** to 22 % |
| 63 | §5.2 | "The factor decomposition that §3.4 declares" | §3.5 | **corrected** |
| 64 | §5.2 | under-predicts on one, over-predicts on two; iteration multiplier 1 / 0.81 / 1 | D.7, D.73–D.75, D.70–D.72 | holds |
| 65 | §5.3 | "30–50× further … for a per-call saving of 3–16 %" | counts §8: 52× / 29×; savings 10.1 % / 0 / 15.8 % | **corrected** |
| 66 | §5.3 | `BR → B0` 0.98 / 1.03 / 1.20; `BR` retries 5 against 3 | D.73–D.75, D.66 | holds |
| 67 | §5.4 | 0 components above τ on every converged run; st `B2` 7.5e-12 vs `B0` 4.9e-14 "three orders larger" | D.76–D.78, F.47–F.49; 7.497e-12 / 4.894e-14 = 153 | holds; **corrected** to two orders |
| 68 | §5.5 | 4 839 vs 2 069 tests, 239 vs 840 wide, 1.16 M vs 1.74 M; 10.8 % empty sweeps on st | F.16 seed-0 rows; §3.3's A58 share (the campaign's F.22 caption states its own) | holds |
| 69 | §5.6 | "0 verdicts changed over 9–15 predicate evaluations per run" | F.13: 8–16 | **corrected** |
| 70 | §5.6 | "by up to 8× on the large tokamak's `A2`" | counts §9 over F.13's hex pairs: largest 5.35× (nof `A2` seed 1) | **corrected** |
| 71 | §5.6 | "The trial changes nothing here" | §3.6's adoption rule adopts `mixed` on a neutral passed gate; not applied | **corrected**: the departure stated, ruling deferred (§9) |
| 72 | §5.7 | "Twenty-eight of 275 optimisations crashed … all with PROCESS's own RuntimeError" | counts §1/§4: 20 RuntimeError, 8 `ModuleSolveFailure` | **corrected** |
| 73 | §5.7 | nof 5, 20, 21 in all four arms; lad `BR` 2, `B0` 2 + 2, `B1`/`B2` 2 + 3; `BR` inf on 2 runs; st none | D.61–D.63, F.48; counts §4 | holds |
| 74 | §5.7 | "fail on 1–3 more low-aspect-ratio starts than the incumbent" | not-finished 5 vs 4 (`B0`) vs 2 (`BR`); accepted optima 11 vs 12 vs 12 — one start (seed 10) | **corrected**: both counts stated |
| 75 | §5.8 | "117 281 / 157 504 / 280 776 per optimisation" | the cell is Σ over 22 / 11 / 22 runs (A79 §7.9); per run 5 331 / 14 319 / 12 763 (new column) | **corrected** |
| 76 | §5.8 | "13 per evaluation in `A2`" | D.13–D.15: 13.2 / 12.9 / 14.8 | holds; written out |
| 77 | §5.8 | n = 11; 2 pairs below resolution; written-file 0.7 % (A67) | D.65, D.68; §3.3 | holds |
| 78 | §6 RQ1 | 0.56 / 0.58 / 0.50 (n = 25, worse on 0); 0.62 / 0.64 / 0.58 | D.13–D.18 | holds |
| 79 | §6 RQ2 | 0.640 / 0.450 / 0.533; iterations 1.00 / 0.81 / 1.00 ≤ 1.05; ≤ 4.6e-11 / 3.5e-9; 2.15e-6, 1 hop of 11 | D.73–D.75, D.70–D.72, D.67–D.69 | holds; extended with "3 of 11 pairs above the floor, one at 3.1e-4" |
| 80 | §6 RQ3 | 1.14 / 0.78 / 1.06 | as #61 | holds |
| 81 | §6 RQ4 | "saves 3–16 % … 30–50×"; 0.98 / 1.03 / 1.20 | as #65 | **corrected**; the `BR → B0` numbers hold |
| 82 | §6 RQ5 | 0 components above τ on every converged run | D.76–D.78, F.47–F.49 | holds |
| 83 | §6 sentence | "a different optimum within 2.2e-6 relative on the third" | 2.148e-6 is the p90; the worst pair is 3.1e-4 (counts §11) | **corrected** |
| 84 | §6 sentence | "transfers … to within a fifth" | 22 % | **corrected** |

### 2.2 Pass 3 — §1–§3 (the plan as approved) against the harness as built

| # | location | claim | as built | verdict |
|---|---|---|---|---|
| 85 | §1.1, §3.3 | 14–20 iteration variables; 20/26, 19/25, 14/18; 840 / 846 / 827 components | `config.py` `default_configurations`; records' `nvar` | holds |
| 86 | §3.2 | every switch cleared then set; `AR`/`BR` all unset; ⁺ rows inactive on st, `A1`/`B1` skipped | gates `composition`, `rungs` PASS; D.15, D.63 carry three arms | holds |
| 87 | §3.4 | seeds 1–25, seed-paired, bit-identical (G6) | D.0 populations; `entry_and_warm` 6 717 / 0 | holds |
| 88 | §3.4 | stencil "2(nvar + 1) per arm … plus the lifted column on the pinned arms" | `chain.stencil_column_set`: the column exists only for an arm reading the lifted file; no Phase A arm does; 20 / 19 / 14 per arm (counts §2) | **corrected** (as-built bracket; never buildable as written) |
| 89 | §3.5 | starts: seed 0 unperturbed + 24; N = 25; no retries by the harness | D.0, D.61–D.63 | holds |
| 90 | §3.5 | seed set = every arm `status ok` and `ifail == 1` | `stats.accepted_optimum`, `every_arm_converged` | holds |
| 91 | §3.5 | "`B1 → B2` and `B0 → BR` reported beside" (check 2) | the table had `B0 → BR` only | **corrected**: the `B1 → B2` row added |
| 92 | §3.5 | transfer identity written with `N_B3`, `nvar_B3` | the arms are `B2` since A78 | **corrected** (a missed rename) |
| 93 | §3.6 | trial measured on `A0`, `A1`, `A2`, 25 seeds, both modes | G8: `A0`, `A2` × 2 seeds × 3 configurations = 12 pairs | **corrected** (as-built bracket) |
| 94 | §3.6 | adoption rule | not applied (§9) | **corrected** (as-built bracket; ruling deferred) |
| 95 | §3.7 | "The §4 table format awaits the user's review" | reviewed 2026-09-10 (D21 (c)) | **corrected** (bracket) |
| 96 | §3.8 (i) | V4 driver changes all in the copy's `core/`; `models/` byte-identical | `g0prime` 77 files, 1 approved; `copy_identity` 224, 7 permitted edits | holds |
| 97 | §3.8 (ii) | `phase_a.py`/`phase_b.py`; W = 3; `PYTHONPATH` to the copy | already bracketed (A79); 3 workers in `press.json`; `process_file` stamped | holds |
| 98 | §3.8 (iii) | "every table in §4" | Appendix D and the companion since A79 | **corrected** (bracket) |
| 99 | §3.9 Table 5 | GR: twenty V3 records, 14 + 6 | D.1 `reproduction` population | holds |
| 100 | §3.9 Table 5 | G3/G3c tooth counts 244 / 124, 240 / 218 | `cold_chain` PASS 60 / 0 (the counts are in its record, not re-derived here) | cannot verify from the tables; the gate's verdict stands |
| 101 | §3.9 Table 5 | G5 compares "outer-pass histogram" | DR1 removed the outer loop; as built 37 switch names + 10 run values | **corrected** (bracket) |
| 102 | §3.9 Table 5 | G7 "5/5 field teeth" | D.1: 9/9 | **corrected** (bracket) |
| 103 | §3.9 | G1, G2, G4, G6, G8, G9 as declared | D.1 rows PASS with teeth | holds |
| 104 | §3.10 Table 6 | τ, δ, F, floor, cluster gap, iteration bound, median, upstream cap, W | D.0 declarations (`max(F × yardstick, floor)`, gap 1e-05, nearest-rank), captions | holds |
| 105 | §3.10 Table 6 | "inner cap 20 sweeps per block — partitioned arms" | `B0`/`B1` refused at "block FLAT … 20 sweeps" (D.62) — the flat control's one block is under the same cap | **corrected** (bracket) |
| 106 | §3.10 | budget 275 + 418 + 150 (mixed) + 275 | 275 + 396 + 0 + 275 = 946 + 3 entry references = 949 | **corrected** (bracket) |
| 107 | §3.3 | `AR` may hit upstream's ten-pass cap → `unconverged-at-cap` | none did: 25 / 25 ok in every source | holds (outcome: the row is empty) |
| 108 | §3.4 | prime stamped beside, never pooled | every cost table carries it as its own column | holds |
| 109 | §1.2 RQ5, §3.2 | A43's answer on V3's records | outside this report's records | cannot verify here (cited, not re-derived) |
| 110 | §2.1 | V3's numbers under V3's names | the V3 report, outside this folder | cannot verify here (declared as prior context) |

### 2.3 Pass 4 — pre-declared expectations against outcomes

| # | expectation (where declared) | outcome cell | verdict as the report states it | wording |
|---|---|---|---|---|
| 111 | `ε = 1` on `B1 → B2`, pulsed (§3.5 twice) | D.70–D.71 `B1 → B2` row: ε median 1.0000, ε = 1 on 22 / 11 of 22 / 11 | PASS — **the report said FAIL in evaluations** (§4.3) and PASS in the wrong quantity (§5.1) | **corrected** in both places |
| 112 | the lift's stencil column `(nvar + 2)/(nvar + 1)` (§3.5) | D.70 `B0 → B1` ε 1.0476 = 22/21 on nof (counts §7); lad 0.8468 (the path shortens, 0.8125 iterations) | stated in §4.3 | holds; the lad reading now explained |
| 113 | transfer `ρ_A(stencil) × stencil factor × problem-call ratio`, residual ≤ 5 % (§3.5) | the problem-call ratio is not a table; §5.2 states the factors 1.14 / 0.78 / 1.06 and defers the attribution to I-17 | not evaluated as a number | **cannot verify** from the tables — the report says so (I-17 reserved); noted as a limit |
| 114 | same optimum, F = 10, floor 1e-6 (§3.5 check 1) | D.67–D.69: PASS / **FAIL** / PASS | FAIL stated as FAIL at §4.3, §5.1 (a), §6 RQ2 and §6's sentence | holds; §6's sentence softened it ("within 2.2e-6") — **corrected** to the p90 and the 3.1e-4 hop |
| 115 | iteration multiplier ≤ 1.05 (§3.5 check 2) | D.70–D.72: 1.0000 / 0.8125 / 1.0000 PASS | PASS | holds |
| 116 | `B2/B0 ≈ 0.64 / 0.45 / 0.53`; `BR → B0 ≈ 0.98 / 1.03 / 1.16` (context) | 0.6395 / 0.4504 / 0.5331; 0.9756 / 1.0300 / 1.1968 | stated with the departure on st (1.20 vs 1.16) | holds |
| 117 | similarity F = 10 (§3.4 check 1) | D.25–D.27: identical residuals, factor 1 | PASS | holds |
| 118 | `AR`'s residual ≫ / ≈ / ≪ τ (§3.3, three outcomes) | 2.6e-8 / 0 / 1.5e-7 — all ≪ τ, and 29–52× `A0`'s | §5.1 states the factor; the ≪ τ reading (upstream over-solves *relative to τ* while under-converging relative to `A0`) is not named | holds; **noted** — the plan's three-outcome frame is not closed in §5.3 (a wording gap, not a number) |
| 119 | predicate trial adoption rule (§3.6) | G8 PASS, 0 verdict changes | rule not applied | **corrected**: stated in §5.6, deferred to the user |

### 2.4 Pass 5 — cross-references

| # | what | result |
|---|---|---|
| 120 | every `Table D.n` / `F.n` in the hand-written text (120 + 24 after the edits) | `--plan-tables check`: 0 dangling; each cited number read against the construction name under its grid — all point at the construction the sentence describes (rows 9–83) | holds |
| 121 | §4.3 "companion Tables F.15–F.22" for two table kinds; §5.5/§5.1 F.16/F.19/F.22; §5.7 F.14/F.17/F.20 | D.0's companion ranges: failure F.14/17/20, attempts F.15/18/21, overhead F.16/19/22 | holds |
| 122 | §4.4 "F.50–F.150" = 101 recomputed tables | 150 − 50 + 1 = 101 | holds |
| 123 | § references | §3.4 ↔ §3.5 for the transfer (rows 46, 63) | **corrected** |
| 124 | file names | `EXPERIMENT_REPORT.md`, `RESULTS_TABLES_FULL.md`, `harness/measurement/plan_tables.py`, `harness/child/ystate.py`, `harness/core/records.py::RECORDED_ARM_NAMES` — all exist; Appendix C's `harness/plan_tables.py` (A55 entry) is its day's | holds |
| 125 | arm names in §1–§6 | `B3` twice in §3.5's identity (row 92); §2.1 and Appendix C declared as their day's | **corrected** |
| 126 | Appendix C translation line | reads "entries before the renaming entry" (A78's assessment fix) | holds |
| 127 | D.0's "the plan's §4.2.5 caption rule" | a section that no longer exists | **corrected** in the tally clause, re-rendered |

### 2.5 Pass 6 — Appendices A, B, C

| # | what | result |
|---|---|---|
| 128 | Table A.1 against `ls -A` | every listed file exists; `report_counts_check.py` (new) added; `harness/` row lacked `data/` and `reference/` | **corrected** |
| 129 | Table B.1 against `V4_IMPROVEMENT_LIST.md` headings | 1a "recommendation" → ruled; 2 "driver change" → rejected; 3 → built, closed in the negative; 4 "open" → ruled; 5a → built, ran as G8, adoption rule unapplied; 5b "recommendation" → accepted; items 9–15 absent | **corrected** (six statuses, seven rows) |
| 130 | Appendix C hashes, 24 checked by `git log -1` | `38057e27 d13a54c7 fd480aff d98f602a a3407d5d 72c343d1 bfaee7ce 52264b53 57dc0c14 e247e48d 004eb06b 3abea2c6 f2dc9243 0677a9b3 b01fccec 362c0b47 24e5fe2f 4ca8cff5 f276fbb5 abff00a2 d9e7c2a5 df9831f5 4dac585e 03f72479` — all resolve to the commits described | holds |
| 131 | header: 152/152 teeth and GR 256/256 at approval | `git show 57dc0c14:…/EXPERIMENT_PLAN.md`: "30 PASS, 0 FAIL; 152 of 152 teeth"; GR 256 / 0 | holds |
| 132 | Appendix C 2026-09-14 entry: "921 ok, 28 crashed optimisations (PROCESS's own Newton solve …)" | its day's wording; the new entry records the split | withdrawn as a current statement; **not rewritten** (history) |

### 2.6 Pass 7 — the denominators (`report_counts_check.py` at `0d407ca7`; `--canonical …/idf_probe/runs/campaign_57dc0c14`)

| # | count | records | report | verdict |
|---|---|---|---|---|
| 133 | records per source 3 / 275 / 198 / 198 / 275 = 949 | same | same | holds |
| 134 | status ok 921; status crashed 28 | same | same | holds |
| 135 | failure_class: crashed 20, unconverged 8 | 20 / 8 | 28 / — | **corrected** (rows 1, 72) |
| 136 | finished, not accepted (`ifail ≠ 1`): lad 38 runs, st 5 | — | unstated | added (§4.3) |
| 137 | 25 per arm per configuration, displaced; 25 ok | same | same | holds |
| 138 | stencil points per arm 20 / 19 / 14 per sign; 396 in all | same as D.55–D.60 | plan text 418 | **corrected** (bracket) |
| 139 | seed sets 22 / 11 / 22; configuration-invalid 3 / 13 / 1 | same | same | holds |
| 140 | seeds outside the set by arm and disposition (printed per seed) | lad: 14 seeds, mechanisms as row 26; st: 5, 10, 17 | — | the basis of rows 26, 60, 74 |
| 141 | retried per arm over 25: 0 / 0 / 0 / 0; 12 / 10 / 10 / 10; 5 / 3 / 2 | same | same | holds |
| 142 | crashed seeds: nof {5, 20, 21} × 4; lad {3, 21} × 4; unconverged lad `B0` {4, 22}, `B1`/`B2` {4, 10, 22} | — | counts only | holds; the seeds now named |
| 143 | `y_exit.json`: 921 under `campaign/` in this tree and in the canonical tree (923 in all there) | the two extra are `input_files/<configuration>/baseline_evaluation/` — the lifted-input derivation's baseline evaluations, not campaign records | — | resolved: 921 = 674 + 247 |
| 144 | prime calls = dispatch sweeps on every `B2` run of the seed set (55 / 55, difference 0); Σ 117 281 / 157 504 / 280 776 | same | same | holds; the "one per sweep" sentence now checked |
| 145 | ε(B1) = ε(B2) on 22 / 22 and 11 / 11 seeds | — | — | row 111 |
| 146 | gates 30 / PASS 30 / teeth 161 / 161 | same | same | holds |
| 147 | nonzero-mismatched PASS rows: `g0prime` 1, `copy_identity` 7 | two | one named | **corrected** (row 8) |

**Tally, by pass (rows; counted from the tables above by verdict cell).** Pass 1 (§4–§6): 84 rows —
53 hold, 31 corrected. Pass 3 (§1–§3 as built): 26 rows — 12 hold, 11 corrected, 3 cannot verify. Pass
4 (expectations): 9 rows — 5 hold, 3 corrected, 1 cannot verify. Pass 5 (cross-references): 8 rows —
5 hold, 3 corrected. Pass 6 (appendices): 5 rows — 2 hold, 2 corrected, 1 withdrawn. Pass 7
(denominators): 15 rows — 12 hold, 3 corrected. In all 147 rows: **89 hold, 53 corrected, 1 withdrawn,
4 cannot verify**; the 53 are 45 distinct corrections, since rows 111, 114, 119, 123, 125, 135, 138 and
147 restate earlier rows under the pass that asked for them. No corrected row moved a cost ratio, a
residual, a check-1 or check-2 verdict or a gate count; every one was a sentence *about* a cell, or the
plan's text against the harness as built.

## 3. The I-26 fix — the new columns beside the old

Check 2's *evaluations median* column was `n_model_calls`, the driver's count of `_call_models_once`
sweeps over the whole run (`caller.py:693` says so in a comment: "counts *sweeps* … not comparable
between a flat loop and a block schedule"); `records.py` described the field as "evaluations of the
model set the optimiser asked for". Fixed in `tally_optimisation.iterations`, `analysis` (its own
`_evaluations`, summed over `attempts[]`), `records.py`, `stats.n_evaluations`'s docstring and
`reference.FIELD_NOTES` (the committed reference file keeps its bytes, D25; its note is wrong and the
code says so).

| pair | old column (`n_model_calls` ratio, now *sweeps median*) | ε median (`sweeps_per_eval.n_evaluations`) | ε = 1 on / n |
|---|---|---|---|
| nof `B0 → BR` | 0.9795 | 1.0000 | 22 / 22 |
| nof `B0 → B1` | 1.0139 | **1.0476** | 0 / 22 |
| nof `B0 → B2` | 2.6524 | **1.0476** | 0 / 22 |
| nof `B1 → B2` (new row) | 2.6158 | **1.0000** | **22 / 22** |
| lad `B0 → BR` | 1.0352 | 1.0000 | 11 / 11 |
| lad `B0 → B1` | 0.8046 | **0.8468** | 0 / 11 |
| lad `B0 → B2` | 2.1169 | **0.8468** | 0 / 11 |
| lad `B1 → B2` (new row) | 2.6335 | **1.0000** | **11 / 11** |
| st `B0 → BR` | 0.9906 | 1.0000 | 15 / 22 |
| st `B0 → B2` | 2.7767 | **1.0000** | 14 / 22 |

The ε column agrees with Table D.5's ε row to every printed digit (1.0476 / 0.8468 / 1.0000 for
`B0 → B2`); the recomputation gate compares both implementations cell by cell (14 445 / 0). Why both
columns: §5.1 reads the sweep ratio as the *mechanism* ("2.7× as many sweeps, each over a third of the
map"), and a reader of check 2 wants the evaluation multiplier and the sweep multiplier side by side
to see that the partition changes the second and not the first.

## 4. Gate results and presses (worktree root, everything committed)

| press | commit | result |
|---|---|---|
| `run_stamp_survey.py --json before` | `589138ef` | 1 102 records; 949 at `57dc0c14`, 153 gate/smoke at six commits |
| `--measure tally_optimisation --resume` | `86430cb6` | 33 tables; runs read 949 at `57dc0c14` |
| `--gate recomputation --resume` | `86430cb6` | PASS 14 445 / 0 (101 tables), 9/9 teeth |
| `--gate tally_contracts --resume` | `86430cb6` | PASS 559 / 0 (303 + 256), 11/11 |
| `--gate run_kind_separation --resume` | `86430cb6` | PASS 3 000 / 0, 9/9 |
| `--gate self_containment --resume` | `86430cb6` | PASS 52 / 0, 1/1 |
| `--measure gate_table --resume`; `--plan-tables write`; `check` | `86430cb6` → `bd16c8a2` | 30 PASS, 161/161; 80 tables in D before and after; IDENTICAL |
| `--measure tally_evaluation --resume`, the four gates again, `gate_table`, `write`, `check` | `1f378e58` → `f4dab209` | all PASS with the same counts; IDENTICAL; 1 D.0 line changed |
| `run_stamp_survey.py --against before` (after each press) | | **0 records whose commit changed, 0 gone, 0 new** |
| `--plan-tables check` after the prose edits | `0d407ca7` | IDENTICAL both documents; 120 + 24 references, 0 dangling |
| `merged_names_check.py`; `harness_survey.py`; `--selfcheck` | `0d407ca7` | exit 0; exit 0; `verdict: PASS` |
| `report_counts_check.py --canonical …` | `0d407ca7` | 45 lines same, 4 DIFFERS — the four are the report's *pre-A80* figures the script keeps as its "report" column (20/8 not 28; 396 not 418; two nonzero-mismatched rows not one) |

The scratch stamp-survey files were lost with the session's temporary directory between the two
presses; the second press's before/after pair (`stamps_before_second_press.json`,
`stamps_after_second_press.json`) is in the scratchpad and both read 1 102 records with 0 moved.

## 5. Autonomous decisions, each with its reversal

1. **Both columns, not a relabel** (the brief's "if instead … do both"): ε from the right field
   *and* the sweep ratio kept. *Reversal:* drop `sweeps_median` / `sweeps_ratios` from `iterations()`
   and `_iteration_multiplier()` and the column from both column lists.
2. **The `B1 → B2` row added to check 2**, because §3.5 pre-declared it ("reported beside") and the
   ε = 1 expectation has no cell without it. *Reversal:* remove the `ACCEPTANCE_PAIRS` append in both
   implementations.
3. **An *ε = 1 on* column**, the per-seed count behind the expectation. *Reversal:* drop
   `evaluations_equal` from both.
4. **Check 4 gains a per-run prime-call column** beside the sum (D21 (c): absolute cells are per-run
   means), the sum's heading saying it is a sum. *Reversal:* drop `arrangement_method_calls_per_run`
   and restore the heading.
5. **Table D.5's denominator is the number of configurations stacked** (3) with the three seed-set
   sizes in `denominator_is`, since `Table.denominator` must be an int and configurations are never
   pooled. *Reversal:* `denominator=n_total` with the old sentence.
6. **The gate table's *compared* cell shows its parts** for the four rows that sum two counts, and
   the caption names both nonzero-mismatched PASS rows. *Reversal:* the two hunks in `registry.py`.
7. **Corrected sentences carry an "(A80: …)" bracket** naming what they said before, rather than a
   silent rewrite; the plan's §1–§3 text is never rewritten, only bracketed *(as built, 2026-09-15
   (A80))* — except the two `B3` tokens in §3.5's identity, a missed rename corrected in place as
   A78 did throughout §3. *Reversal:* strip the brackets; the Appendix C entry keeps the list.
8. **`report_counts_check.py` keeps the pre-A80 figures as its "report" column**, so its four DIFFERS
   lines are the audit's record and it exits 3 by design. *Reversal:* update the four expected values
   to the corrected ones (then 49 same, exit 0).
9. **The adoption rule's non-application is recorded, not repaired.** Adopting `mixed` retroactively
   would restate τ across a finished campaign; refusing to record it would hide a departure from a
   pre-declared rule. *Reversal:* the user's ruling either way (§9).
10. **Appendix C's earlier entries and the merged reports are untouched** (D17); the 2026-09-14
    entry's "28 crashed" stands as its day's wording and the new entry says so.

## 6. Limits

- **A number with no cell.** Four §5/§6 numbers are quotients of cells (the transfer factors, the
  `AR/A0` pooled ratio on nof, the prime calls per evaluation in `B2`, the 150× of §5.4). Each now
  names the cells it is computed from; none was promoted to a table.
- **The count script re-derives counts, not statistics.** It does not recompute medians, p90s or
  pooled ratios — the recomputation gate does that with a second implementation — except check 1's
  per-seed `r` on lad (§11), which it prints because no table carries the worst pair.
- **"Cannot verify" is three claims** about V3 records and A43's result, cited as prior context and
  outside this folder; and the transfer's problem-call ratio, which no V4 table computes (I-17).
- **The predicate-trial ratio** (5.35×) is over the 9 of 12 pairs whose frozen residual is nonzero;
  on the 3 lad `A0` pairs both rulers read exactly 0.
- **I did not re-read the harness plan's amendments 20–28 against the code beyond what the report
  cites**; the brief named them as reading, and rule (ix)'s "§4 is rendered" → "Appendix D" wording
  (A79 §9) is that document's business.
- **The gate presses ran at `86430cb6` and `1f378e58`**, the commits of the code they tested; the
  rendered appendix was committed one commit later each time (`bd16c8a2`, `f4dab209`), so the
  verdicts' `tree_git_head` is one behind the document's commit by construction.

## 7. What should change elsewhere (proposals; nothing outside the report edited here)

- **Queue v2:** I-26 → CLOSED at merge, pointer to this report and Appendix C's A80 entry; the A80
  row → §4.2 with the merge commit and the records path the retire script prints.
- **A ruling on the predicate trial's adoption rule (D-row, the user's):** either (a) `frozen` stands
  as V4's ruler by ruling, the §3.6 rule discharged as not applied because the trial ran as a gate of
  12 pairs and nothing acceptance-bearing depends on the ruler; or (b) `mixed` is adopted as the rule
  says and V5 states τ on it. Proposed wording for either is in §5.6.
- **TRAPS (proposed T18): *a pre-declared expectation is read against the pair it was declared
  on.*** §3.5's `ε = 1` was declared on `B1 → B2`; the only ε cell published was `B0 → B2`; the
  report read the expectation against the cell it had and called it refuted, then defended it in a
  different quantity. The shape: a declaration names an arm pair and a quantity; a table offers a
  neighbouring pair or a neighbouring quantity; the sentence closes the gap by substitution. How to
  avoid it: the table that judges an expectation carries the declared pair and the declared quantity
  as a row and column of their own, or the expectation is marked *not measured*.
- **TRAPS (candidate, or a §12 corollary): *the harness's status word is not the taxonomy.*** 28
  records stamp `status = crashed`; 8 of them are the driver's own refusal at a cap, which the
  taxonomy table splits by `failure_class`. Prose that quotes the status count as a crash count is
  wrong by construction. Perhaps a line in T11 rather than a new trap.
- **The V5 list:** (i) publish the failure taxonomy with `ifail = 5` exhaustions as their own
  disposition — on lad 9 of the 13 configuration-invalid seeds are VMCON's, not the architecture's,
  and the *ok* column of Table D.62 hides them; (ii) the transfer's problem-call ratio as a table, so
  §3.5's restated transfer can be evaluated rather than deferred; (iii) the stencil regime's lifted
  column (§3.4's wording) either built for a pinned arm or struck from the method.
- **Harness plan Appendix A:** amendment (proposed) recording I-26's closure — the ε field, the sweep
  column, the `B1 → B2` row — and the gate table's parts-in-brackets rendering.

## 8. Commits (branch `A80-report-accuracy-audit`, off `589138ef`)

| commit | what |
|---|---|
| `86430cb6` | I-26 closed in tally and analysis; check 4's per-run prime column; D.5's denominator per configuration; the gate table's parts and caption; `records.py` / `stats.py` / `reference.py` sentences; `report_counts_check.py` |
| `bd16c8a2` | Appendix D and the companion re-rendered after the presses named in §4 |
| `1f378e58` | `report_counts_check.py` §11 (check 1 per seed on lad) and labels; the predicate-trial declaration's "§4.2.5" re-pointed |
| `f4dab209` | D.0 re-rendered after that fix (the four gates and the gate table pressed again) |
| `0d407ca7` | the prose corrections, the §3 as-built brackets, Appendices A–C |
| *(this report)* | `docs/reports/A80_report_accuracy_audit.md` |

## 9. Decision offered

**The predicate trial's adoption rule (§3.6) was pre-declared and not applied.** Gate G8 passed with
its teeth (12 pairs bit-identical, 0 verdict changes) — the rule's condition for adopting `mixed` as
V4's predicate and audit ruler — and the campaign was pressed on `frozen`. Nothing acceptance-bearing
depends on the choice (the exit-audit columns are printed on both rulers), so no number moves either
way; but a pre-declared rule that is not applied needs a dated ruling, and §5.6 now says the choice is
the user's. The two wordings are in §7.

## 10. Change log

- 2026-09-15 — task opened at `589138ef`; the work above; report written at `0d407ca7`.
