# MDA Partitioning Experiment V2 — Experiment Plan

> **Document status (2026-09-03, revision 2).** **DRAFT for user review — not authorised for
> execution.** Revision 2 folds in the user's first review round (all seven assessment points
> accepted; the post-solve hoist of optimiser-irrelevant feed-forward nodes added to the
> intervention in both phases; parallelisation strategy declared; A32 merged).
> Supersedes the user's `Provisional_experiment_plan.txt` (same directory) by incorporating the
> design discussion of 2026-09-03; draws its licensing measurements from
> [`../docs/plans/MDA_PARTITION_V2_REVISION_LIST.md`](../docs/plans/MDA_PARTITION_V2_REVISION_LIST.md)
> (R1–R11), A22/A28/A30/A31/A32, and the V-register. Execution begins only when the user
> approves this document; any later deviation is a dated amendment here, never a silent change.

## 1. Objective and claim structure

**Goal: an existence proof that optimisation architecture matters in PROCESS.** The intervention
is one clean architectural change, with every physics and engineering model byte-identical to
upstream at `c0ae5b28` (D2, D5):

> **The intervention (one unit, not four):** partition the overarching MDA into three block
> MDAs run in feed-forward order; lift the single cross-block feedback (the burn-time coupling;
> k = 1 on the pulsed decks, k = 0 on `st_regression`) to the optimiser with its consistency
> constraint (constraint 93); feed-forward nodes execute once, outside any loop (hoisting is
> definitional to the partition, not measured separately); and feed-forward nodes whose outputs
> the optimiser never consumes — no objective read, no active-constraint read, no reader inside
> the solve — leave the per-call path entirely, executing **once per run at the accepted
> optimum** (the post-solve hoist; user decision 2026-09-03). The per-deck post-solve set is a
> committed artifact derived by crawling the collapsed DSM backwards from the deck's objective
> and constraint readsets, confirmed in source and by the §6 bit-comparison gate — first-cut:
> `costs` and `water_use` leave on all three decks (none of the three objectives reads a cost
> output, and the two constraint equations touching `data.costs.*` read fields the costs node
> does not write); `pulse` stays per-call on the pulsed decks (fom −14 reads
> `times.t_plant_pulse_burn`, `objectives.py:81`, and icc 13 reads the burn time).

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

**Preconditions (closed — A32 merged `637a6bb6`, 2026-09-03):** the coupling-state spec
generation is a26-mode everywhere (A31 found the A18-mode exact-equality-on-constants
artifact; A32 confirmed end-to-end on `st_regression` A1′ that the recurring 3+-pass tail
collapses 2,802/54,480 → 25/49,920 — exactly one cold first call per run, verified by call
index — and the moved-constant counter goes to 0 in both arms); the driver's spec loader is
mode-aware (A32's B1 fix, gated bit-exact against A28's record, teeth shown).

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
- **Execution and parallelism:** a fixed worker pool of **W = 3** concurrent runs
  (memory-bound, not core-bound: measured per-run peak RSS 0.65 GB against 7 GB total RAM
  on 16 cores). Every acceptance quantity is a count or bit-comparison and is
  **concurrency-invariant**; the one contextual timing weighting comes from a small
  **serial** repetition block run after the campaign, never from the parallel runs (each
  record stamps loadavg and sequence position regardless — D17). The job list is
  deterministic (deck × arm × start), jobs never retried — a crashed run is a taxonomy row,
  not a rerun — and the tally reads only the on-disk records.

## 3. Phase A — per-call MDA cost (no optimiser)

**Arms: two.**

| arm | architecture |
|---|---|
| FLAT | one MDA over all models; convergence predicate on the full coupling state at τ. The post-solve-eligible nodes stay **inside** its loop — that is the flat architecture as shipped (measured: A28's `A0'` hoists nothing; `costs`/`pulse`/`water_use` run every sweep) |
| BLOCKS | three block MDAs in feed-forward order, one shared inner τ, **no outer loop**; per-call feed-forward nodes execute once per call; **post-solve nodes do not run in the measured call at all** — they execute once at the end of the run (uncharged to the per-call cost, present for the audit) |

**Attribution (declared).** The FLAT→BLOCKS delta measures **the intervention as one unit**
(partition + pinned/lifted coupling + both hoists). Only `st_regression` (k = 0, nothing
pinned) separates the partition-and-hoist effect from the coupling term; no per-factor claim
is made from the pulsed decks' Phase A numbers.

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
arms' audited max-scaled-residual distributions lie within a factor F = 10 of one another at
BOTH the median and the p90 — the p50-degeneracy check (R7): a median may pass while a tail
diverges — and both arms sit below the anchor accuracy (what stock PROCESS delivers at its
shipped predicate). Full distributions are published either way.** The lifted
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
| A2 | partitioned block MDAs, feed-forward, lifted coupling, **no overarching MDA**, and the deck's post-solve set executed once per run at the accepted optimum instead of once per call | the partition + post-solve hoist (A1→A2) |

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
1. **Same optimum:** per-start paired |Δ norm_objf| plus the post-solve feasibility audit.
   The yardstick for a "harmless" difference is **measured inside the same campaign**: the
   R→A0 paired |Δ norm_objf| spread — the stopping-rule change's own footprint — rather than
   an assumed state-to-objective sensitivity. Acceptance: the A0→A1 and A0→A2 paired spreads
   are not larger than the R→A0 spread by more than the declared factor (F, §3's). The full
   paired distributions are published either way.
2. **Iteration multiplier:** paired per-start ratio of optimiser iterations (and of function
   evaluations), median and q1–q3 per deck. Acceptance: median paired iteration ratio
   ≤ 1.05. *Licensing measurement:* A28 measured paired ratios of exactly 1.000/1.000 on two
   decks **with the lift in place** — the bar is strict because it has been met under the
   same lift.
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
3a. **Post-solve hoist instrument (task A33)** — two pieces. *(i) The classification:* per
   deck, a committed `postsolve_<scenario>.json` artifact from a backward crawl of the
   collapsed DSM (sibling repo's export, read-only) seeded by the objective's and the active
   constraints' read-variables (assembled per `icc` from `process/core/solver/constraints.py`
   and per `minmax` from `objectives.py`), confirmed in source; V6 config-specificity checked
   per deck. *(ii) The driver capability:* env-switched (`PROCESS_ARCH_POST_SOLVE`) exclusion
   of the listed nodes from solve-phase `_call_models_once`, with one execution at the
   accepted optimum before output; byte-neutral when unset (gated). *Correctness gate:* at
   fixed x on sampled starts, the constraint vector and objective must be **bit-identical**
   with and without the exclusion — per deck, teeth shown. First-cut classification and its
   evidence: §1.
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

## Appendix B — Review decisions (user, 2026-09-03) and the one open question

1. **N starts: 25 per deck per arm — CONFIRMED.** Declared companion rule: robustness is a
   count of 25, so **a robustness difference of ≤ 2 starts is reported as "not resolved at
   N = 25"**, never as a verdict (A28 precedent: one deck's verdict turned on a single
   start and was flagged, not claimed); the affected deck may be extended (e.g. to 50) as a
   dated amendment if a 1–2-start difference matters for the conclusion.
2. **Similarity factor F = 10 — CONFIRMED**, for both phases, at median and p90. What it
   bounds: the ratio of the two arms' *delivered accuracies* (each arm's own audited
   distance-to-fixed-point), not a distance between their answers. Licensing measurement:
   A28's at-call audits put the pathology this must catch (the receipted arm's overshoot)
   at a **30–90×** gap, and the benign contraction-factor scale at O(1–10) — 10 separates
   the two measured regimes. Clause: a deck where the audit reads 0.0 for every arm (as
   `low_aspect_ratio_DEMO`'s call-1 audit did in A28) counts as trivially similar, and the
   report says so.
3. **Iteration-ratio median ≤ 1.05 — CONFIRMED.** Licensing measurements: A28 measured
   paired medians of exactly 1.000/1.000 with the lift in place; and the A28-vs-A32
   comparison (identical code, spec change only, same 25 starts) measured the noise floor —
   **median 1.000, 16/25 pairs bit-identical, individual pairs 0.59–1.81** — so per-start
   iteration counts are last-bit-dust-sensitive by ±80 % and the bound applies to the
   median ONLY; extremes are published, never judged.
4. **Phase A deck coverage: all three decks — CONFIRMED** (the pulsed decks carry the
   pin-value-insensitivity evidence the §5 transfer argument needs).
5. **Anchor accuracy — OPEN.** Options: **(a)** measured from R per deck in the same
   campaign (same instrument/starts/spec generation; the headline "at least stock
   accuracy" becomes measured; expected magnitudes from A28's call-1 audits: 5.1e-07 /
   9.3e-08 / 0.0) — recommended; **(b)** a number fixed now (rigid, but detached from what
   R actually delivers under the V2 audit protocol and the a26 generation). The choice
   changes the strength of the headline sentence, not the runs.
6. ~~A32 merge precedes execution~~ **Resolved 2026-09-03:** A32 assessed and merged
   (`637a6bb6`) — tail confirmed dissolved, driver fix gated switch-neutral.
7. **Post-solve hoist** is part of the intervention in both phases (user decision
   2026-09-03); the classification artifact and driver capability are task A33's
   deliverables and precede execution.
