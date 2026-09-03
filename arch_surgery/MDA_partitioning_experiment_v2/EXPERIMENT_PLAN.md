# MDA Partitioning Experiment V2 — Experiment Plan

> **Document status (2026-09-03).** **DRAFT for user review — not authorised for execution.**
> Supersedes the user's `Provisional_experiment_plan.txt` (same directory) by incorporating the
> design discussion of 2026-09-03; draws its licensing measurements from
> [`../docs/plans/MDA_PARTITION_V2_REVISION_LIST.md`](../docs/plans/MDA_PARTITION_V2_REVISION_LIST.md)
> (R1–R11), A22/A28/A30/A31/A32, and the V-register. Execution begins only when the user
> approves this document; any later deviation is a dated amendment here, never a silent change.

## 1. Objective and claim structure

**Goal: an existence proof that optimisation architecture matters in PROCESS.** The intervention
is one clean architectural change, with every physics and engineering model byte-identical to
upstream at `c0ae5b28` (D2, D5):

> **The intervention (one unit, not three):** partition the overarching MDA into three block
> MDAs run in feed-forward order; lift the single cross-block feedback (the burn-time coupling;
> k = 1 on the pulsed decks, k = 0 on `st_regression`) to the optimiser with its consistency
> constraint (constraint 93); feed-forward nodes execute once, outside any loop (hoisting is
> definitional to the partition, not measured separately).

**Claim decomposition (R11).** Total cost = optimiser iterations × calls per iteration ×
per-call MDA cost. The experiment splits along that product:

- **Phase A** (no optimiser) measures the **per-call factor**: the cost of one MDA evaluation
  under each architecture, with the lifted coupling **pinned** — which is exactly the lifted
  architecture's per-call structure, since the optimiser holds the lifted variable fixed within
  any single evaluation. Phase A's number is the **best case / upper bound**: the case where
  consistency costs zero.
- **Phase B** (full optimisation) is **the headline**: it measures the multiplier (does the
  optimiser need more iterations? does robustness degrade?) and the end-to-end deployment
  number under the real call mix. If warm-started optimiser calls shrink the architecture's
  impact relative to Phase A's bound, the shrunken number is the honest result — no correction
  is applied or wanted.

**Preconditions (both already closed):** the coupling-state spec generation is a26-mode
everywhere (A31 found the A18-mode exact-equality-on-constants artifact; A32 confirmed
end-to-end on `st_regression` A1′ that the recurring 3+-pass tail collapses 2,802/54,480 →
25/49,920 — exactly one cold first call per run — and the moved-constant counter goes to 0);
the driver's spec loader is mode-aware (A32's B1 fix, gated bit-exact against A28's record).

## 2. Experimental variables and controls

- **Independent variable:** the driver architecture only — `process/core/caller.py`,
  `process/core/solver/`. The physics is frozen; no `process/models/` edit without user
  approval (D11); base commit `c0ae5b28` is the coordinate system.
- **Scenarios (D17):** `large_tokamak_nof`, `low_aspect_ratio_DEMO` (pulsed, k = 1),
  `st_regression` (steady-state, k = 0 — the clean partition-only case).
  `large_tokamak_eval` stays dropped (D17: 0 solver iterations).
- **Spec generation:** every arm, every audit, every gate runs on the **a26-mode** ystate
  artifacts, with a26-generation write sets for all three decks (generator:
  `a25_writeset.py --spec-variant a26`; `st_regression`'s exists and is validated; the two
  pulsed decks' are Appendix A work).
- **Perturbation size:** δ = 0.10 (D15's calibrated value), one perturbation stream,
  seed-paired across all arms of a phase. N = 25 starts per deck per arm (start000–start024,
  A28's enumeration) unless the review changes it (Appendix B).
- **Isolation:** every PROCESS run is a fresh subprocess in its own working directory, tree
  asserted in-process; first run discarded for any timing context (JIT).

## 3. Phase A — per-call MDA cost (no optimiser)

**Arms: two.**

| arm | architecture |
|---|---|
| FLAT | one MDA over all models; convergence predicate on the full coupling state at τ |
| BLOCKS | three block MDAs in feed-forward order, one shared inner τ, **no outer loop**; feed-forward tail nodes execute once |

**Coupling handling.** On `st_regression` there is nothing to lift; BLOCKS is pure
feed-forward. On the pulsed decks the burn-time coupling is live at MDA level (A22: pass-≥2
movement at 149/149 and 297/297 harvested points — all of it the burn time), so BLOCKS runs
with the coupling **pinned** (A22's pin-arm instrument). The ±10 % scan over coupling initial
guesses doubles as the **pin-value insensitivity check** (R11 condition 2): per-call cost as a
function of pin value is a published curve, not an assumption.

**Equivalence gate (per deck, teeth per §12 of the protocol):** one BLOCKS run pinned **at the
FLAT arm's converged coupling value** must reproduce the FLAT fixed point within the audit's
resolution. This replaces the draft's "converged to the same point" check, which would fire on
every pulsed run by construction (pinned ≠ converged is the design, not an error). The gate is
shown able to fail before its pass is counted.

**Accuracy rule (pre-declared).** Both arms run at the same τ (single knob each). The
**uncharged** exit audit (a26-mode spec, identical instrument, outside the cost accounting)
measures delivered accuracy per run. Pre-declared similarity criterion: **per deck, the two
arms' median audited max-scaled-residuals lie within a factor F = 10 of one another, and both
below the anchor accuracy (what stock PROCESS delivers at its shipped predicate).** The lifted
coupling's inconsistency is reported separately as the **lift residual** and excluded from this
criterion (it is the pin, not an error). If the criterion fails, the fallback is the matched
**measured** accuracy machinery (A26 fix 1 / A28's envelope), both constructions published —
the rationale for same-τ-first is R10: with no outer loop in either arm there is no overshoot
mechanism, and error ≈ δ·ρ/(1−ρ) differences are expected to be τ-grade; that expectation is
checked, not assumed.

**Metrics (counts only; acceptance never on a timing):**
- **per-node model-evaluation counts** (primary; recorded for every run, enabling
  weighting-invariance bounds later without re-running — the I-10 insurance);
- per-block totals (M1/M2/M3/FF) and predicate-evaluation counts;
- per-call cost binned by **entry distance** (from the entry census) — the warmth diagnostic
  for §5's transfer argument; purely attributional, no correction applied anywhere;
- failure taxonomy per start: crashed / refused / unconverged / infeasible-at-audit, with
  denominators (A30's lesson); failures count to robustness, completions to cost statistics.

**Declared expectation:** blocks converge at their own rates (fewer sweeps for
fast-contracting blocks), FF nodes execute once; the per-call saving is positive on all three
decks; its magnitude is the number being measured (prior context: A28 measured the receipted
variant at −1.63 %/−6.18 %/inconclusive with the ~38 %-of-solve-phase verification pass still
charged; V2's arm does not carry that pass).

## 4. Phase B — optimisation comparison (the headline)

**Arms: four.**

| arm | architecture | isolates (vs previous) |
|---|---|---|
| R | PROCESS as shipped (its idempotence loop) | anchor |
| A0 | proper flat fixed-point MDA, predicate-matched | stopping rule (R→A0) |
| A1 | flat MDA + burn-time coupling lifted to optimiser (constraint 93) | the lift (A0→A1) |
| A2 | partitioned block MDAs, feed-forward, lifted coupling, **no overarching MDA** | the partition (A1→A2) |

There is no "partitioned with outer loop" bridge arm: no-outer-loop is inherent to feed-forward
partitioning, not a separable factor — partitioned-with-receipt is not a candidate
architecture. **A0→A2 is the headline comparison; R→A2 is the user-facing figure; A0→A1 shows
what the lift alone does.** On `st_regression` (k = 0) A1 degenerates to A0 and is skipped.

**Settings.** Optimiser settings default (comparability with reference). Same τ across arms,
with the Phase-A similarity criterion re-applied at accepted optima.

**Initial guesses (pre-declared rule).** One perturbation stream, seed-paired across all four
arms: ±10 % (δ = 0.10) on all iteration-variable initial guesses. In A1/A2 the lifted
variable's initial guess is **the same perturbed value the coupling would start from in
R/A0** — the lift adds a variable, never a different starting state. (n vs n+1 iteration
variables is part of the intervention, including its finite-difference gradient cost.)

**Checks, each testable and pre-declared (never on iteration variables — D6):**
1. **Same optimum:** per-start paired |Δ norm_objf| plus the post-solve feasibility audit;
   accepted as "same" when the difference is smaller than each arm's own audited
   distance-to-fixed-point. The full paired distribution is published either way.
2. **Iteration multiplier:** paired per-start ratio of optimiser iterations (and of function
   evaluations), median and q1–q3 per deck. Acceptance: median paired iteration ratio
   ≤ 1.05 (A28 precedent: 1.000/1.000 on two decks — the bar is strict because it can be met).
3. **Lift actually closed:** constraint-93 residual at every accepted optimum, reported per
   start.
4. **Robustness:** paired multi-start with the A30 taxonomy (crashed / refused / unconverged /
   infeasible-at-audit, denominators named), identical-success-set cost comparisons, and
   refusal attribution by arm (the D18 lesson: two-thirds of V1's refusal deficit was the
   predicate, not the architecture).

**Per-deck outcome rules, fixed now:** decks are never pooled. If check 2 fails on a deck, the
A→B transfer is declared broken there and only end-to-end numbers are quoted for that deck
(the `low_aspect_ratio_DEMO` clause). A failed gate or check is a result, reported with its
numbers — never tuned around.

## 5. The transfer argument (how A and B combine)

If Phase B's checks 1–4 pass: net saving ≈ Phase A's per-call saving × (unchanged multiplier),
with the warm-call regime read from Phase A's entry-distance bins if attribution is wanted.
If Phase B's realized saving lands below Phase A's bound, the bins diagnose whether warmth
explains the gap; **no correction is applied in either direction** — Phase B's number stands
as the deployment result, Phase A's as the mechanism and upper bound.

## 6. Correctness, gates, and reporting (binding rules)

- **Instrumentation neutrality is a gate, not an argument** (no grandfathering by historical
  checks): at the V2 driver commit, one reproduction run per deck must match its recorded
  reference bit-for-bit on count fields and objective hex, teeth shown. Precedent: A32's
  "provably neutral" one-line loader fix was still gated, and the gate is what makes its
  numbers citable.
- **Acceptance quantities are counts and bit-comparisons.** Timings appear as context only,
  with median, interval, repetition count, and run-sequence position (D17).
- **Every published number comes from executing a committed script** (§15): one commit per
  campaign, `--verify` regenerates every published table, failure paths reachable from the
  same entry points. Bulk run artifacts stay untracked; summaries and verdicts are committed.
- **Everything in this document is fixed before the first run.** Amendments are dated edits.

## 7. Scope honesty (what this experiment does not show)

One code (PROCESS), three decks, one partitioning choice, one lift. No claim transfers to
other partitionings, other couplings, or other systems codes; the existence proof is exactly
that — architecture changed performance measurably, physics untouched.

---

## Appendix A — Harness changes required (implementation specifics)

1. **a26-generation write sets for the pulsed decks** — `a25_writeset.py --spec-variant a26`
   against each deck's committed a26 ystate artifact, control-checked the A32 way (default
   invocation must regenerate the committed A18 artifact byte-stable but `tree_git_head`).
   `st_regression`'s is committed and validated (A32).
2. **Pin instrument for Phase A pulsed decks** — revive A22's pin arm under the V2 runner:
   env-switched pin value (`PROCESS_ARCH_PIN_*`), value sourced from the perturbation stream;
   no-op when unset (switch-neutrality gated).
3. **A2 trust-mode driver path** — partitioned `module_solve` without the outer verification
   loop; env-switched; the constraint-93 lift wiring exists (A25/A28). Driver scope only
   (`process/core/solver/`, `caller.py`).
4. **Per-node counts in campaign metrics** — enable the node census fields in every campaign
   run's `metrics.json` (machinery exists; currently off in campaign mode).
5. **Entry-distance binning** — analysis-side only; the entry census is already recorded.
6. **Run-button scripts** — new directory `arch_surgery/MDA_partitioning_experiment_v2/`:
   `phase_a.py`, `phase_b.py`, `run_experiment.py` (runs both phases plus gates), each with
   `main()` under `if __name__ == "__main__"` and **no required CLI arguments** — F5 in VSCode
   runs it end to end; optional stage argument for reruns; configuration constants at the top;
   shared runner imported from `arch_surgery/idf_probe/` (never duplicated); every PROCESS run
   a fresh subprocess; `--verify` mode regenerating all published tables from run records.
7. **Neutrality gates** — reproduction gate per deck at the V2 driver commit (item 3 changes
   the driver, so the gate re-runs after it), teeth included.

## Appendix B — Open questions for the user's review

1. **N starts:** 25 per deck per arm (Phase B: 4 arms × 3 decks × 25 ≈ 275 optimisations
   after the k = 0 degeneracy; order 6–10 h serial wall time by A28 experience). Acceptable,
   or resize?
2. **Similarity factor F = 10** on the audit medians — confirm or tighten.
3. **Iteration-ratio acceptance ≤ 1.05** on the median — confirm.
4. **Phase A deck coverage:** all three decks (recommended: the pin scan is the pulsed decks'
   pin-value insensitivity evidence, needed by §5), or `st_regression` + one pulsed deck?
5. **Anchor accuracy:** measured from R at its shipped predicate per deck (recommended), or
   fixed numerically in advance?
6. **A32 merge** precedes execution (its driver fix is what loads the a26 specs) — assess and
   merge per protocol §5 first. Confirm.
