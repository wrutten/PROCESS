# V2 experiment report — MDA partitioning: per-call cost and optimisation behaviour of the flat, lifted, partitioned and trust architectures on three decks

> **Document status** — **CURRENT · EXPERIMENT REPORT.** Written 2026-09-04 by the
> orchestrating session after the approved full execution of
> [`EXPERIMENT_PLAN.md`](../../MDA_partitioning_experiment_v2/EXPERIMENT_PLAN.md) (revision 3,
> approved and `EXECUTION_APPROVED` flipped at `59e91b62`). Campaign machinery at `ba69c05d`
> (Phase A `large_tokamak_nof` records at `6d9ff4b9`, see §2); analysis-time checks from
> [`v2_report_analysis.py`](../../MDA_partitioning_experiment_v2/v2_report_analysis.py) at
> `0e272595`. Experiment base commit `c0ae5b28`; physics untouched throughout.

| | |
|---|---|
| **Task** | Execute the V2 experiment end-to-end: Phase A (per-call MDA cost, no optimiser: A0 flat vs A1 blocked-trust, warm entries, N = 25, δ = 0.10) and Phase B (optimisation: R / B0 / B1 / B2 / B3, seed-paired N = 25 per arm), per the approved plan, from the one-button `run_experiment.py` entry point |
| **Headline** | **Per-call cost (Phase A):** A1/A0 model-call ratio **0.522 / 0.568 / 0.502** (nof / lad / st), positive saving on every deck; weighting-invariance brackets [0, 0.935] / [0, 0.976] / [0, 1.0]. **Optimisation (Phase B):** iteration bound (≤ 1.05) **PASS on `large_tokamak_nof` and `st_regression` (median 1.000)**, **FAIL on `low_aspect_ratio_DEMO` B0→B3 (median 1.27)** — the declared per-deck clause fires: the A→B transfer is broken on lad and only end-to-end numbers are quoted there, which still favour the partition: **identical-success-set node calls B3/B0 = 0.640 / 0.758 / 0.675**. Same-optimum: formally FAIL under the declared yardstick on all decks (§5.2's construction critique); substantively, all five arms land on the same optimum to ≤ 1.3e-10 on nof, within ≤ 1.5e-4 on lad's converged seeds, and st shows deck-native attractor hops that the stopping-rule change R→B0 itself exhibits |
| **Plan** | `EXPERIMENT_PLAN.md` revision 3; pre-campaign amendment (2026-09-03) fixed the Phase A similarity interpretation before any campaign run (R9 capability-difference clause) |
| **Scripts** | `run_experiment.py` (F5 entry, `__main__`), `phase_a.py`, `phase_b.py`, `v2_runner.py`, `v2_config.py` — campaign + tally, at `ba69c05d`; `v2_report_analysis.py` — the analysis-time checks and the independent tally recomputation, committed at `aa6c8b89` and refined at `94e4d9b6` / `645411da` / `0e272595` **before** the numbers each refinement publishes |
| **Runs** | Phase A: 150 seeded single-eval runs (2 arms × 3 decks × 25 seeds) + 3 references + 6 gates, **150/150 ok**. Phase B: 350 requested optimisation runs (5 arms × 25 × 2 pulsed decks + 4 arms × 25 on st) + R-neutrality and arm gates + smoke; taxonomy in §5.1 (9 crashed on nof, 14/21 crash/unconverged-heavy lad, 0 crashed st). Serial context-timing block: 3 reps × 14 deck/arm cells |
| **Environment** | `PROCESS_surgery_env`; fresh subprocess and own working directory per run; `process.__file__` asserted in-process; W = 3 workers (memory-bound); every record stamps tree, commit, and dirty flag |
| **Date** | 2026-09-04 (campaign overnight 2026-09-03/04) |

---

## 1. What ran

Five Phase B arms per pulsed deck (R stock; B0 flat predicate-matched; B1 flat + burn-time
lift; B2 partitioned + outer verification loop; B3 partitioned trust — the designed
architecture), four on `st_regression` (k = 0: B1 degenerates to B0 and is skipped per plan).
Phase A ran A0 (flat single eval) vs A1 (B3's per-call structure: resequenced `per_module`
blocks, trust mode, post-solve exclusion, lift + pin on the pulsed decks) from seed-paired
±δ-perturbed warm entries around each deck's converged flat snapshot. One perturbation stream,
seed-paired across arms; τ = 1e-6 everywhere; δ = 0.10; N = 25.

## 2. Launch history and resume integrity (the hiccups, in full)

Four launch attempts; the three failed ones are preserved as
`runs/experiment_main_attempt{1,2,3_partial}.log`:

1. **Attempt 1** — the post-solve loader's wrong-deck refusal fired on Phase A's pin arm
   (which runs the ORIGINAL deck: its `icc` differs by exactly {93} from the lifted deck the
   artifact was sealed for). Fixed by generating `nolift` post-solve artifacts from the
   committed generator (`6d9ff4b9`). The refusal was the loader working as designed.
2. **Attempt 2** — `low_aspect_ratio_DEMO`'s entry-gate tooth demanded a nonzero doctored
   audit on a zero-residual deck, where a doctored run legitimately re-converges to exactly 0
   (the work tooth *did* fire). Tooth semantics widened to OR (`ba69c05d`); a broken loader
   still fails both teeth. `large_tokamak_nof`'s Phase A campaign had already completed and
   its records (stamped `6d9ff4b9`, clean) were kept.
3. **Attempt 3** — killed externally by a session restart (orphaned background task); 301
   complete records existed at that point.
4. **Attempt 4** — resumed and completed everything: campaign remainder, both tallies, and
   the context-timing block, exit 0.

**Resume semantics and their audit.** Resume is keyed on complete records
(`status: ok` + matching deck/arm/seed); 150 Phase A and 301 total records were carried
across attempts, and every gate and reference **re-ran fresh on each attempt and reproduced
bit-exactly**: R-neutrality (start000 per deck vs A28's recorded runs) three times, the B3
armgate (post-solve ON vs OFF bit-identity, suppressed-call counts 2910 / 4340 / 6354) three
times. Provenance stamps across all campaign records: Phase A nof at `6d9ff4b9`, Phase A
lad/st and all of Phase B at `ba69c05d` and `6dd66d6a` — every one clean. The two Phase B
stamps differ by a docs-only commit (`6dd66d6a` touches `MASTER_TODO.md` alone); the
`6d9ff4b9`→`ba69c05d` diff touches the entry-gate tooth logic and the nolift generator only,
not the run machinery, and the affected gates re-ran at `ba69c05d`.

## 3. Gates

All gates carried teeth (a deliberately broken input must fail), and all passed:

- **Phase A per deck:** entry gate (restore → bit-exact readback → minimal work;
  doctored-snapshot and work teeth) and warm equivalence gate (A1 from the unperturbed
  reference snapshot audits categorically clean; teeth) — PASS ×3 decks.
- **Phase B:** R-neutrality (new driver, all switches off, start000 bit-exact vs A28's
  recorded stock runs) PASS ×3 decks ×3 attempts; B3 armgate (post-solve ON vs OFF
  bit-identical `norm_objf`, suppressed-call counts reproducing) PASS ×3 decks ×3 attempts.

## 4. Phase A results (per-call cost; counts only)

*Caption: one row per deck; all quantities over the 25 paired-ok seeds. "Cold-start term" =
model-node calls / flat sweeps of the once-per-run A0 reference convergence at the cold deck
point (dimensionless counts). "A1/A0 call ratio" = summed single-eval model-node calls of A1
over A0 (the parenthesis gives the two sums). "Bracket" = [min, max] of the per-node A1/A0
count ratios — any positive per-node cost weighting lands inside it. "Audit" columns =
median / nearest-rank-p90 over seeds of each run's uncharged exit-audit max scaled residual
(dimensionless, per-component |Δ|/scale, the a26 ruler).*

| deck | cold-start term (calls / sweeps) | A1/A0 call ratio (paired-ok N=25) | bracket [min, max] per-node ratio | A0 audit med / p90 | A1 audit med / p90 |
|---|---|---|---|---|---|
| `large_tokamak_nof` | 126 / 6 | **0.522** (2898→1512) | [0.0, 0.935] | 6.3e-10 / 8.0e-9 | 2.44 / 9.86 |
| `low_aspect_ratio_DEMO` | 105 / 5 | **0.568** (2625→1491) | [0.0, 0.976] | 0.0 / 0.0 (25 exact zeros) | 0.182 / 0.288 |
| `st_regression` | 147 / 7 | **0.502** (3066→1538) | [0.0, 1.0] | 5.4e-9 / 2.0e-8 | 0.258 / 0.337 |

- Pairing: 25/25 seeds bit-identical entry states across arms on every deck. Failure
  taxonomy: 150/150 ok (denominator 25 per arm per deck).
- **The declared per-call saving is positive on every deck** (expectation confirmed). The
  bracket's upper end is the iterating-block ratio (`build`/coils nodes); on st it reaches
  1.0 — a weighting concentrated entirely on those nodes sees no saving there.
- **Similarity check: FAIL, exactly as pre-declared.** The F = 10 criterion fails on every
  deck (on lad any nonzero A1 value is an infinite factor against A0's 25 exact zeros). Per
  the pre-campaign amendment this is reported under R9 as a **capability difference**: A1 has
  no accuracy dial (one pass, no predicate), so each arm's delivered accuracy is published at
  its cost and no matched-accuracy read is fabricated.
- **The failure decomposes (A35 §6 item 2, now measured):** the argmax ownership census over
  all 75 A1 runs shows **75/75 audit argmaxes owned by post-solve-excluded structures**
  (`costs` 25/25 nof; `costs` 23 + `water_use` 2 lad; `costs` 15 + `water_use` 10 st). The
  dominant term of the A1 audit is the *suppression accounting artifact* — δ-perturbed
  components of nodes A1 deliberately never executes, which the whole-state audit still
  measures — not cross-block error. The genuine cross-block term is A35's carrier image,
  ~5.4e-4 scaled at δ = 0.10 (coefficient-exact, displacement-linear, depth-1).
- Lift residual (pin inconsistency), reported separately per plan: A1 medians O(10–100 s) raw
  on the pulsed decks against a 7200 s burn time; A0 exactly 0 everywhere; excluded from the
  similarity statistic by declaration.

## 5. Phase B results (the declared checks, per deck — decks never pooled)

### 5.1 Robustness / taxonomy (check 4, denominators of 25)

*Caption: per deck and arm, counts out of the 25 requested starts: runs with `status: ok`
(the subprocess completed and produced records) / runs **converged** (`ifail = 1`, an
accepted optimum) / runs crashed (no usable record). ok − conv = completions where VMCON
stopped without convergence (`ifail = 5`).*

| deck | R | B0 | B1 | B2 | B3 |
|---|---|---|---|---|---|
| nof | 22 ok / **22 conv** / 3 crash | 22 / 22 / 3 | 22 / 22 / 3 | 22 / 22 / 3 | 22 / 22 / 3 |
| lad | 23 ok / **12 conv** / 2 crash | 21 / 12 / 4 | 20 / 11 / 5 | 20 / 11 / 5 | 20 / 11 / 5 |
| st | 25 ok / **24 conv** / 0 crash | 25 / 23 / 0 | — | 25 / 23 / 0 | 25 / 24 / 0 |

"conv" = accepted optimum (`ifail = 1`); ok-but-`ifail = 5` runs are the A30 taxonomy's
**unconverged** class. The V2 tally pooled these under "ok" — the split here is from the
analysis script and is load-bearing on lad, where the failures are **paired** (the same 9
seeds are unconverged in every arm, B0 included): deck/seed hardness, not architecture.
Crash attribution likewise shows no arm effect (nof: the same 3 seeds crash in all five
arms; lad: 2 seeds crash everywhere, B1/B2/B3 add 4-vs-2 on two further seeds).

**Why lad fails so often — what the records show.** Its unconverged runs all die *early and
the same way*: 538–554 model calls (converged runs spend 2 810–31 216), `sqsumsq` stuck at
0.15–0.64 (converged exits: ≤ 1e-13), on the same seeds in every arm including stock R. So
these are not iteration-cap timeouts but early aborts: the ±10 % perturbed start lands
outside the region from which VMCON's restart ladder can restore feasibility at all, and it
gives up after a few hundred evaluations with the constraints grossly violated. The deck's
feasible basin is simply narrow relative to δ = 0.10 — roughly half the perturbed starts
fall outside it for *every* architecture. (Whether a smaller, basin-sized δ or per-deck
amplitudes is the right design response is a v3 question; deeper attribution — which
constraints are violated at the aborts — needs exit-state forensics the current records do
not carry, also a v3 item.)

### 5.2 Same optimum (check 1) — paired |Δ norm_objf| at accepted optima

The declared yardstick is measured inside the campaign: the R→B0 spread, with acceptance at
median AND p90 ≤ F × yardstick (F = 10). Converged-only pairs (the plan's "accepted
optima"); the all-ok construction is published beside it in `report_analysis.json`.

*Caption: per deck, the distribution of |Δ norm_objf| (dimensionless — the normalised figure
of merit, O(1) to O(17) on these decks) over seed-paired runs where BOTH sides converged
(`ifail = 1`); median / nearest-rank p90 / max over those pairs (n in the row label).
Acceptance (declared): a B0→Bx column's median AND p90 must be ≤ F = 10 × the R→B0 column's.
Bold marks the entries discussed in the text.*

| deck | R→B0 (yardstick) med / p90 / max | B0→B1 | B0→B2 | B0→B3 | B2→B3 |
|---|---|---|---|---|---|
| nof (n=22) | 3.3e-15 / 1.1e-12 / 1.5e-10 | 4.3e-11 / 7.3e-11 / 1.3e-10 | identical to B1 | 2.8e-11 / 7.1e-11 / 8.9e-11 | 1.8e-12 / 1.6e-11 / 1.3e-10 |
| lad (n=11–12) | 9.9e-15 / 1.3e-12 / 8.3e-11 | 1.7e-7 / 8.7e-7 / **1.3e-4** | identical to B1 | 1.3e-9 / **1.5e-4** / 1.5e-4 | 1.5e-9 / 1.5e-4 / 1.5e-4 |
| st (n=23) | 2.6e-12 / 9.9e-8 / **0.22** | — | 2.2e-12 / **0.21** / 0.22 | 1.7e-10 / **0.022** / 0.22 | 1.6e-10 / 4.2e-9 / 0.21 |

**Formal verdict: FAIL on every deck** (a failed check is a result; nothing was tuned). The
substantive per-deck reading, from the full distributions:

- **nof:** zero converged pairs above 1e-6 in *any* comparison — all five arms reach the
  same optimum to ≤ 1.3e-10 on all 22 seeds. The formal failure is a yardstick artifact: R
  and B0 agree to machine noise (3.3e-15), so *any* nonzero architecture footprint exceeds
  10× it. The declared construction did not anticipate a near-zero yardstick.
- **lad:** among converged pairs, B0→B1/B2 move exactly one seed (seed 1, 1.28e-4) and the
  trust step B0→B3 moves five seeds by ~1.3–1.5e-4 — a small but real, structured objective
  footprint of the trust step on this deck.
- **st:** medians are τ-grade (B0→B2 at 2.2e-12), but 2–3 of 23 seeds hop to a different
  attractor under *any* change — including the stopping rule itself (R→B0: seeds 12 at 0.22
  and 24 at 0.022). **These are not unconverged runs slipping through**: every side of every
  hop pair has `ifail = 1` and `sqsumsq ≤ 2e-11` — genuinely accepted, feasible optima. The
  deck supports at least four distinct nearby optima, all observed at accepted exits:
  `norm_objf` = −16.8089 (the common one), −16.8309, −16.5966, −16.5886. Seed 24 alone lands
  on three of them across the four arms (R −16.8309, B0/B3 −16.8089, B2 −16.5966). Deck-native
  multi-modality, not an architecture defect; B2→B3 agree with each other at p90 4.2e-9.

### 5.3 Iteration multiplier (check 2, bound ≤ 1.05 on the median paired ratio)

*Caption: per deck, the median over converged seed-pairs of the paired ratio of optimiser
(VMCON) iterations, arm-b over arm-a (dimensionless; 1.0 = same iteration count; pair counts
in the row label). ✓/✗ against the declared bound: median ≤ 1.05. B2→B3 and B0→R are
reported beside the three declared comparisons, outside the acceptance rule.*

| deck | B0→B1 | B0→B2 | B0→B3 | B2→B3 (beside) | B0→R |
|---|---|---|---|---|---|
| nof (22 pairs) | **1.000 ✓** | **1.000 ✓** | **1.000 ✓** | 1.000 | 1.000 |
| lad (11 pairs) | **0.833 ✓** | **0.833 ✓** | **1.273 ✗** | 1.33 / 1.40 † | 1.000 |
| st (24 pairs) | — | **1.000 ✓** | **1.000 ✓** | 1.000 | 1.000 |

*† Correction (2026-09-04, from an independent read of the records): the lad B2→B3 cell has
an even pair count (10) whose two middle ratios differ (1.267, 1.400), so the two median
constructions the committed analysis publishes disagree there and only there —
`statistics.median` (mean of the two middles) gives **1.33**, the tally's nearest-rank
(upper-middle) convention gives **1.40**. The report originally printed 1.33 without naming
its construction. Both now shown; every other cell is identical under both constructions,
and no verdict involves this cell (B2→B3 sits outside the acceptance rule). Pair counts
vary by column (lad B2→B3: 10; lad B0→R: 12); exact counts per pair are in
`report_analysis.json` (`check2_iters`). V3 pre-declares a single construction
(nearest-rank) so a cited median is always reproducible to the digit.*

The tally's pair counts (silently dropping pairs with no recorded iterations) turn out to be
exactly the converged pairs — iterations are recorded only at `ifail = 1` — so its medians
coincide with the converged-only construction; the analysis names every dropped pair
(all paired `ifail = 5`, plus st seed 17).

- **The lad failure fires the declared per-deck clause:** the A→B transfer is broken on
  `low_aspect_ratio_DEMO`; only end-to-end numbers are quoted there (§5.5). "Transfer
  broken" means specifically: the experiment's argument structure multiplies Phase A's
  per-call saving by an unchanged iteration count to claim an end-to-end saving (plan §5).
  That multiplication is only valid where the iteration multiplier is ~1; at 1.27 the
  per-call figure no longer predicts the total, so on lad we do not *derive* the saving —
  we quote the measured end-to-end totals directly, which happen to still favour the
  partition (§5.5).
- **Why lad is also the deck where iterations FALL (B0→B1/B2 = 0.833):** current data
  localises it precisely but does not explain it mechanistically. B0→B1 isolates the
  burn-time lift (same flat architecture, one added optimiser variable + explicit
  constraint 93): on lad's converged seeds that alone buys the 17 % iteration reduction,
  and B2 (which keeps the lift) inherits it exactly (0.833, same pairs). The nof pairs show
  1.000 for the same lift — so this is a lad-specific interaction: on this deck, and not on
  nof, giving VMCON the coupling as an explicit degree of freedom with its own constraint
  row helps it converge where solving the same coupling as an inner fixed point does not.
  The trust step then gives most of it back (B2→B3 = 1.33 / 1.40, † in §5.3). *Why lad specifically responds
  is not measured*: no per-deck stiffness/contraction measurement of the burn-time coupling
  exists in these records, so "the coupling is stiffer on lad" is a hypothesis consistent
  with — not demonstrated by — these numbers; the gradient-quality instrumentation that
  could attribute it is a v3 item.
- **The declared st expectation ("B3 may inflate, context 10→20") is REFUTED:** median
  1.000, q1–q3 [0.85, 1.18]. The single-trajectory context was not representative.
- "B3 ≈ B2 on the pulsed decks" is confirmed on nof (B2→B3 = 1.000) and refuted on lad
  (1.33 / 1.40, † in §5.3).

### 5.4 Lift closed (check 3) and post-solve suppression

Constraint-93 residual at **accepted optima**: nof max 1.6e-3 s, lad max 6.6e-5 s on a
7200 s burn time (relative ≤ 2.2e-7) — **the lift closes** in every lifted arm. The large
residuals (up to 6135 s) exist only at lad's unconverged exits, which are not optima; they
are published beside, not pooled. st: nothing lifted (k = 0), field absent as designed.

**Post-solve suppression, spelled out.** A33 identified, per deck, the model nodes whose
outputs never reach the objective or any active constraint — pure "reporting" models
(`costs`, `vacuum`, `water_use`; plus `pulse` on st). The flat arms execute these on **every**
`call_models` even though the optimiser can never see their output; B2/B3 remove them from
the per-call loop and execute them **once per run** at the accepted optimum, before output.
The "suppression share" quantifies what that removal saves: of all the node calls the solve
phase *would have made* without the hoist (executed calls + suppressed call sites), the
fraction that was suppressed. Measured on B2: **8.34 % / 8.35 % / 11.44 %**, against A33's
baseline predictions 8.3 / 8.4 / 11.3 % from its static census — confirmed to the precision
the baselines carry. B3 shows 9.40 / 9.39 / 11.78 %: the *same* suppressed nodes, a higher
share only because the trust arm executes fewer in-loop calls (a smaller denominator).

### 5.5 Cost (check 4): identical-success-set node-call sums (solve phase)

*Caption: per deck, each arm's summed solve-phase model-node calls over the identical
success set (the seeds where every arm of that deck is ok / converged — n in the row label),
expressed as a ratio to B0 (B0's absolute call count in parentheses; dimensionless counts,
exact and bit-reproducible). Lower = cheaper.*

| deck (n seeds) | R | B0 | B1 | B2 | B3 |
|---|---|---|---|---|---|
| nof (22) | 0.976 | 1.000 (935 340) | 1.008 | 0.894 | **0.640** |
| lad (19 ok / 10 conv) | 1.027 / 1.029 | 1.000 (1 729 812 / 1 627 395) | 0.718 / 0.701 | 0.648 / 0.634 | **0.758 / 0.766** |
| st (25 ok / 23 conv) | 1.155 / 1.177 | 1.000 (3 184 377 / 2 507 568) | — | 0.885 / 0.845 | **0.675 / 0.711** |

End-to-end, the designed architecture B3 spends **0.64 / 0.76 / 0.68** of B0's model-node
calls for the campaign — on lad *despite* the 1.27 iteration multiplier (the per-call saving
outweighs the extra iterations; B2, whose iterations are 0.83×, is the cheapest lad arm at
0.65). On st the stock driver R costs 15–18 % *more* node calls than the flat control B0.

**Per-block split of the same sums** (user-requested; computed by the analysis script from
each run's per-node census, mapped through the deck's executed block schedule):

*Caption: summed model-node calls over the identical-ok-set (n as in the table above), split
by owning block: M1 = plasma physics (physics, plasma_geom); M2 = build + coils; M3 =
in-vessel components, power and plant engineering; PULSE = the lifted `pulse` node (executes
in-loop, outside any iterating block; absent on st, k = 0); post-solve = the hoisted
reporting nodes (`costs`, `vacuum`, `water_use`; + `pulse` on st) — per-call in R/B0/B1,
once-per-run in B2/B3. TOTAL is the census total; it exceeds §5.5's solve-phase totals by
~0.1 % (the once-per-run and exit-audit calls the census also counts). Dimensionless counts.*

| deck / arm | M1 | M2 | M3 | PULSE | post-solve | TOTAL |
|---|---|---|---|---|---|---|
| **nof** R | 87 042 | 130 563 | 522 252 | 43 521 | 130 563 | 913 941 |
| B0 | 89 212 | 133 818 | 535 272 | 44 606 | 133 818 | 936 726 |
| B1 | 89 896 | 134 844 | 539 376 | 44 948 | 134 844 | 943 908 |
| B2 | 89 116 | 158 493 | 575 484 | 14 146 | 264 | 837 503 |
| B3 | 61 212 | 116 463 | 407 520 | 14 146 | 264 | 599 605 |
| **lad** R | 169 314 | 253 971 | 1 015 884 | 84 657 | 253 971 | 1 777 797 |
| B0 | 164 858 | 247 287 | 989 148 | 82 429 | 247 287 | 1 731 009 |
| B1 | 118 398 | 177 597 | 710 388 | 59 199 | 177 597 | 1 243 179 |
| B2 | 116 836 | 207 801 | 778 932 | 18 705 | 228 | 1 122 502 |
| B3 | 129 692 | 247 218 | 905 412 | 30 297 | 228 | 1 312 847 |
| **st** R | 350 386 | 525 579 | 2 102 316 | — | 700 772 | 3 679 053 |
| B0 | 303 424 | 455 136 | 1 820 544 | — | 606 848 | 3 185 952 |
| B2 | 327 668 | 506 274 | 1 986 360 | — | 400 | 2 820 702 |
| B3 | 246 780 | 390 645 | 1 514 316 | — | 408 | 2 152 149 |

Three structural reads: (1) the post-solve column is where the hoist lives — six-figure
per-call cost in every flat arm collapsing to a few hundred once-per-run calls in B2/B3;
(2) on nof, trust (B2→B3) cuts every iterating block by ~30 % (M1 89k→61k, M3 575k→408k) at
identical optimiser iterations — the outer verification passes were the cost; (3) on lad,
B3's M2/M3 *grow* back over B2 (208k→247k, 779k→905k) — the extra optimiser iterations
(§5.3) spend their calls in the engineering blocks, eating most of the trust saving.

## 6. Timing (context only — never evidence)

*Caption: wall-clock seconds per full optimisation run at the baseline start, median
[min – max] over 3 serial repetitions, each a fresh process with numba JIT included
identically in every rep (so JIT is a constant offset, not a discard); machine otherwise
idle. From `runs/phase_b/timing/timing.json` (the committed timing stage). Context only —
no acceptance quantity rests on any entry (I-10).*

| deck / arm | R | B0 | B1 | B2 | B3 |
|---|---|---|---|---|---|
| nof | 16.4 [15.9–17.3] | 25.7 [25.3–27.5] | 24.7 [23.9–26.4] | 39.5 [39.1–42.0] | 28.6 [26.7–32.3] |
| lad | 31.5 [31.5–32.9] | 49.7 [49.3–50.6] | 40.3 [39.4–40.8] | 65.9 [64.5–66.7] | 40.3 [40.2–42.0] |
| st | 15.0 [14.9–15.1] | 28.3 [26.3–30.5] | — | 38.1 [35.9–38.5] | 48.6 [48.0–49.8] |

**Uncertainty:** with n = 3 the ranges are the honest uncertainty statement — they span
~1 % (st R) to ~20 % (nof B3, 26.7–32.3 s), so differences below ~10 % between cells are
unresolved at this repetition count; the wall-clock *ordering* R < B0 and B2 > B3 (nof) is
outside the ranges and stable. **A per-block wall-clock split does not exist in the
records** — no per-block timers were instrumented (counts were the declared acceptance
quantity) — so the per-block table of §5.5 has no timing counterpart; added to the v3
method list as a context-only instrument.

Two context observations: the new driver carries instrumentation overhead over stock (R vs
B0) that counts do not see; and on st, B3's *wall clock* exceeds B0's while its node calls
are 0.68× — per-call machinery overhead of the block solver (three `module_solve`
invocations per call replacing one flat sweep loop, at st's small per-node cost). Both are
why acceptance rests on counts (I-10); the timing block completed after the tallies,
stamped clean.

## 7. Critical assessment

**What the experiment establishes.** On the deck family it was designed around
(`large_tokamak_nof`), the answer is unambiguous: the designed architecture B3 delivers the
same optimum (≤ 8.9e-11 paired objective difference, 22/22 seeds), the same iteration count
(median ratio exactly 1.000), the same robustness (identical crash set), and **64 % of the
flat architecture's model-evaluation cost** — with the lift closed and the post-solve share
matching its A33 prediction. The architecture change, not the physics, produced the saving:
that is the existence proof V2 was designed to be, on one deck, with the caveats below.

**Where the declared checks failed and what that means.** (1) The same-optimum yardstick
construction is the weakest declaration in the plan: R→B0 measured at machine noise, so the
check cannot pass for any arm that changes *anything* — on nof the "failure" coexists with
1e-10-grade agreement. The declared rule was applied as written and reported as FAIL; a
future revision should declare a floor for the yardstick before the campaign, not after.
(2) The lad B0→B3 iteration failure is a genuine adverse result for the trust step on that
deck (B2→B3 = 1.33 / 1.40 isolates it to the outer-loop removal, not the partition), and the
declared clause quarantines lad's transfer argument accordingly. Note lad's fragility
baseline: only 12/25 seeds converge in *any* arm, including stock. **To pre-empt a
misreading: this report does not conclude that the architecture costs robustness.** The
mass of lad's failures (13/25 unconverged-or-crashed) is seed-paired across every arm
including R — deck hardness under δ = 0.10, not an arm effect. What the data does carry is
a small unresolved hint: crash counts rise 2 (R) → 4 (B0) → 5 (B1/B2/B3) on lad, a 1–3-seed
effect that N = 25 cannot distinguish from noise; it is recorded for v3's
robustness-powered design, neither claimed nor dismissed. (3) The Phase A
similarity failure was pre-declared with its interpretation fixed before the campaign (R9);
§4 shows it decomposes into the suppression accounting artifact (75/75 argmaxes) plus the
bounded carrier term.

**Tally defects found by the independent recomputation** (the tally's own numbers all
reproduced under its operationalization): the iteration pairing silently dropped
unconverged pairs — harmless in effect (it equals the correct converged-only construction)
but undeclared (trap T11); the taxonomy pooled `ifail = 5` completions under "ok", which the
A30 taxonomy requires splitting. Both are published corrected in `report_analysis.json`;
neither changes a verdict.

**Expected impact of the A35 findings** *(user-requested paragraph)*. A35 (merged
2026-09-04, `b20b6112`) names the displaced-entry transient's carrier: the value-frozen
back edge `FirstWall → build.dr_fw_inboard/outboard → Build`, transmitting exactly the
entry displacement, once, under any one-pass schedule (register V15: "value-frozen ≠
displacement-inert"). For **this experiment's numbers** the expected impact is bounded and
mostly already visible. A regime disclosure first (surfaced by the parallel methodology
assessment, verified here): Phase A's multiplicative δ-stream displaces two classes of
state that **no optimiser-driven call displaces after call 1** — run-constants (the
`dr_fw` pair; `vpfskv`) and post-solve-owned outputs — so the warm δ-regime is
deliberately more hostile than any state B3 visits inside an optimisation, and the 75/75
census and the carrier term are the two symptoms of exactly that mismatch. In Phase A, the
carrier contributes only the ~5.4e-4-scaled
displacement image inside A1's audits — the measured 0.18–2.44 medians are 75/75
post-solve-owned accounting (§4), so removing the carrier would *not* rescue the F = 10
check; a similarity audit restricted to in-loop-writeset components would isolate the true
carrier-grade deficit and is the natural methodology control. In **Phase B** the carrier is
essentially inert after each run's first call: `dr_fw_*` derive from two pure deck inputs
that are not iteration variables, so optimiser steps and finite-difference stencils never
displace them — the carrier costs B2 at most the documented once-per-run extra outer pass
and B3 a one-shot first-call deficit that the optimiser's own iteration washes out; it
therefore cannot explain the lad B0→B3 iteration inflation (A34's
interior-accuracy-feeds-gradients observation remains the live hypothesis there, and lad
was outside A35's traced scope). Consequently: accepted-optima agreement (§5.2) is
unaffected by the carrier; the Phase A capability-difference verdict stands but its
magnitude is dominated by an accounting choice, not by cross-block physics; and a D11-gated
one-line fix (seeding `dr_fw_*` at initialisation) would dissolve the carrier entirely —
a user decision, recorded in A35 §6, not taken here.

## 8. Scope honesty

Three decks, one machine, one environment, N = 25 seeds at a single perturbation amplitude
δ = 0.10; `low_aspect_ratio_DEMO`'s conclusions rest on 11–12 converged pairs. The
existence proof is per-deck: nof carries it cleanly; st carries the cost and iteration
result with a deck-native multi-attractor caveat on the objective tail; lad's transfer is
declared broken and only its end-to-end numbers are claimed. Nothing here measures
gradient-quality mechanisms (why lad's trust arm iterates more) — that question is open and
now has a named non-candidate (the A35 carrier). Timings are context. All raw records are
untracked under `runs/`; summaries and this report are the committed record.

## 9. Provenance and reproduction

Every run: fresh subprocess, own working directory, tree asserted in-process, record stamped
with commit + dirty flag (all clean). Gates and references reproduced bit-exactly across
three independent executions (attempts 2–4). Seeded perturbation streams are deterministic
and bit-identical across arms (25/25 pairing per deck). The one-button path
(`run_experiment.py` as `__main__`) re-executes preflights → Phase A campaign + tally →
Phase B campaign + tally → timing; resume semantics skip complete records and re-run every
gate. Analysis: `v2_report_analysis.py` at `0e272595` → `runs/report_analysis.json`
(untracked; regenerated deterministically from the records).
