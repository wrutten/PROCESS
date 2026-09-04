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

### 5.2 Same optimum (check 1) — paired |Δ norm_objf| at accepted optima

The declared yardstick is measured inside the campaign: the R→B0 spread, with acceptance at
median AND p90 ≤ F × yardstick (F = 10). Converged-only pairs (the plan's "accepted
optima"); the all-ok construction is published beside it in `report_analysis.json`.

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
  and 24 at 0.022). Deck-native multi-modality, not an architecture defect; B2→B3 agree with
  each other at p90 4.2e-9.

### 5.3 Iteration multiplier (check 2, bound ≤ 1.05 on the median paired ratio)

| deck | B0→B1 | B0→B2 | B0→B3 | B2→B3 (beside) | B0→R |
|---|---|---|---|---|---|
| nof (22 pairs) | **1.000 ✓** | **1.000 ✓** | **1.000 ✓** | 1.000 | 1.000 |
| lad (11 pairs) | **0.833 ✓** | **0.833 ✓** | **1.273 ✗** | 1.33 | 1.000 |
| st (24 pairs) | — | **1.000 ✓** | **1.000 ✓** | 1.000 | 1.000 |

The tally's pair counts (silently dropping pairs with no recorded iterations) turn out to be
exactly the converged pairs — iterations are recorded only at `ifail = 1` — so its medians
coincide with the converged-only construction; the analysis names every dropped pair
(all paired `ifail = 5`, plus st seed 17).

- **The lad failure fires the declared per-deck clause:** the A→B transfer is broken on
  `low_aspect_ratio_DEMO`; only end-to-end numbers are quoted there (§5.5).
- **The declared st expectation ("B3 may inflate, context 10→20") is REFUTED:** median
  1.000, q1–q3 [0.85, 1.18]. The single-trajectory context was not representative.
- "B3 ≈ B2 on the pulsed decks" is confirmed on nof (B2→B3 = 1.000) and refuted on lad
  (1.33).

### 5.4 Lift closed (check 3) and post-solve suppression

Constraint-93 residual at **accepted optima**: nof max 1.6e-3 s, lad max 6.6e-5 s on a
7200 s burn time (relative ≤ 2.2e-7) — **the lift closes** in every lifted arm. The large
residuals (up to 6135 s) exist only at lad's unconverged exits, which are not optima; they
are published beside, not pooled. st: nothing lifted (k = 0), field absent as designed.

Post-solve suppression share of would-be solve-phase calls (B2): **8.34 % / 8.35 % /
11.44 %** against A33's declared baselines 8.3 / 8.4 / 11.3 — confirmed to the precision the
baselines carry. B3: 9.40 / 9.39 / 11.78 % (higher share purely because the trust arm
executes fewer in-loop calls).

### 5.5 Cost (check 4): identical-success-set node-call sums (solve phase)

| deck (n seeds) | R | B0 | B1 | B2 | B3 |
|---|---|---|---|---|---|
| nof (22) | 0.976 | 1.000 (935 340) | 1.008 | 0.894 | **0.640** |
| lad (19 ok / 10 conv) | 1.027 / 1.029 | 1.000 (1 729 812 / 1 627 395) | 0.718 / 0.701 | 0.648 / 0.634 | **0.758 / 0.766** |
| st (25 ok / 23 conv) | 1.155 / 1.177 | 1.000 (3 184 377 / 2 507 568) | — | 0.885 / 0.845 | **0.675 / 0.711** |

End-to-end, the designed architecture B3 spends **0.64 / 0.76 / 0.68** of B0's model-node
calls for the campaign — on lad *despite* the 1.27 iteration multiplier (the per-call saving
outweighs the extra iterations; B2, whose iterations are 0.83×, is the cheapest lad arm at
0.65). On st the stock driver R costs 15–18 % *more* node calls than the flat control B0.

## 6. Timing (context only — never evidence; 3 serial reps, first run discarded)

Median wall-clock per run (ranges in the log): nof R 16.4 s, B0 25.7 s, B1 24.7 s, B2
39.5 s, B3 28.6 s; lad R 31.5, B0 49.7, B1 40.3, B2 65.9, B3 40.3; st R 15.0, B0 28.3, B2
38.1, B3 48.6. Two context observations: the new driver carries instrumentation overhead
over stock (R vs B0) that counts do not see; and on st, B3's *wall clock* exceeds B0's while
its node calls are 0.68× — per-call machinery overhead of the block solver. Both are why
acceptance rests on counts (I-10); the timing block completed after the tallies, stamped
clean.

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
deck (B2→B3 = 1.33 isolates it to the outer-loop removal, not the partition), and the
declared clause quarantines lad's transfer argument accordingly. Note lad's fragility
baseline: only 12/25 seeds converge in *any* arm, including stock. (3) The Phase A
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
