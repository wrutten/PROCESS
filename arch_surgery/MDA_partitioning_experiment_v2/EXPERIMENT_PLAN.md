# MDA Partitioning Experiment V2 — Experiment Plan

> **Document status (2026-09-03, revision 3).** Revision 3 (evening review round): the
> **warm-entry Phase A design** (§3), the **five-arm Phase B lattice** R/B0/B1/B2/B3 with the
> re-admitted partitioned-with-outer-loop arm B2 (§4, user decision after the trust-vs-verified
> single-trajectory context — declared before any campaign run), per-deck expectations declared
> (§4), campaign ≈ 350 optimisations, A35 (cold-entry runtime census) minted as a separate,
> non-blocking investigation, A36 building the Phase A machinery. Approval status: see the
> foot of this header. Revision 2 folded in the user's first review round (all seven assessment points
> accepted; the post-solve hoist of optimiser-irrelevant feed-forward nodes added to the
> intervention in both phases; parallelisation strategy declared; A32 merged).
> **Arm naming (user, 2026-09-03):** Phase A arms are **A0** (flat) / **A1** (feed-forward
> blocks); Phase B arms are **R / B0 / B1 / B2**.  These are V2 names: A28/V1's primed
> arms A0'/A1' are different objects (B1 carries no blocks; V1's A1' carried the outer
> loop that B2 does not).
> Supersedes the user's `Provisional_experiment_plan.txt` (same directory) by incorporating the
> design discussion of 2026-09-03; draws its licensing measurements from
> [`../docs/plans/MDA_PARTITION_V2_REVISION_LIST.md`](../docs/plans/MDA_PARTITION_V2_REVISION_LIST.md)
> (R1–R11), A22/A28/A30/A31/A32, and the V-register. Execution begins only when the user
> approves this document; any later deviation is a dated amendment here, never a silent change.
>
> **APPROVED FOR EXECUTION — 2026-09-03 (evening).** The user authorised autonomous
> execution ("update the plan and update the experiment framework machinery... If you find
> no further issues, you are cleared to press run on the full experiment execution. Run the
> run_experiment.py script as main"), with review the following morning.
> `v2_config.EXECUTION_APPROVED` flipped to True in this same commit. All gates green at
> launch: driver neutrality (R×3 bit-exact vs A28), B3 combined-switch equivalence (×3),
> Phase A entry-state + warm equivalence gates (A36). Run log:
> `runs/experiment_main.log`.

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
| A0 (flat) | one MDA over all models; convergence predicate on the full coupling state at τ. The post-solve-eligible nodes stay **inside** its loop — that is the flat architecture as shipped (measured: A28's `A0'` hoists nothing; `costs`/`pulse`/`water_use` run every sweep) |
| A1 (blocks) | three block MDAs in feed-forward order, one shared inner τ, **no outer loop**; per-call feed-forward nodes execute once per call; **post-solve nodes do not run in the measured call at all** — they execute once at the end of the run (uncharged to the per-call cost, present for the audit) |

**Attribution (declared).** The FLAT→BLOCKS delta measures **the intervention as one unit**
(partition + pinned/lifted coupling + both hoists). Only `st_regression` (k = 0, nothing
pinned) separates the partition-and-hoist effect from the coupling term; no per-factor claim
is made from the pulsed decks' Phase A numbers.

**Entry states (warm-entry design; user decision 2026-09-03, evening).** Per deck, the
**reference** is the converged flat state at the deck point, obtained by one A0-arm single
evaluation from the cold deck entry (one `call_models` under `flat_state` is the full flat MDA
solve); its cost is reported separately as the **once-per-run cold-start term**, never mixed
into the per-call statistics. Campaign entries are **multiplicative ±δ perturbations of the
reference snapshot** (seed-paired: bit-identical perturbed entries across arms, verified per
deck), evaluated by one `call_models` under each arm. Rationale, with its licensing
measurements: this is the regime Phase B's B3 actually visits — every call after the first is
warm (A28: ~95 % two-pass structure; A32: exactly one cold call per run, verified by call
index) — and it is the regime where feed-forwardness is dynamically verified (A22). A34
measured the cold regime to be a different question: a one-pass chain from a cold entry sits
1.46e-2 from the fixed point while the verified control repairs it in ~2 extra cross-block
propagations — a transient whose carrier is task **A35's** separate, non-blocking
investigation. At the warm reference the components are non-zero, so the multiplicative stream
is well-posed (the 767/799-zeros problem was a cold-init artifact).

**Coupling handling.** On `st_regression` there is nothing to lift; A1 is pure feed-forward.
On the pulsed decks the burn-time coupling is live at MDA level (A22: pass-≥2 movement at
149/149 and 297/297 harvested points — all of it the burn time), so A1 runs with the coupling
**pinned** (A34's instrument), the pin value being **the perturbed burn-time component from
the same seeded stream** — so the ±δ scan is exactly the **pin-value insensitivity check**
(R11 condition 2) around the consistent value: per-call cost as a function of pin value is a
published curve, not an assumption.

**Equivalence gates (per deck, teeth per §12 of the protocol):**
1. *Entry-state instrument gate:* an A0-arm evaluation launched from its **own** unperturbed
   exit snapshot must audit ≈ 0 (the state is already the fixed point) — the loader shown
   faithful before anything rests on it.
2. *Warm equivalence gate:* one A1 run from the reference snapshot, unperturbed, pinned at
   the reference's burn-time value, must reproduce the reference within the audit's
   resolution (categorically clean AND cross-state max < τ). This supersedes A34's
   cold-entry pin gate, whose FAIL-as-bound is recorded context about the cold transient,
   not a Phase A defect. A warm-gate failure STOPS the Phase A campaign and is the result.
Both replace the draft's "converged to the same point" check, which would fire on every
pulsed run by construction (pinned ≠ converged is the design, not an error).

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

> **Amendment (2026-09-03, pre-campaign, from A36's machinery smoke):** at δ = 0.10 warm
> entries the A1 one-pass delivered accuracy measured ≈ 0.24 scaled against A0's ≈ 5e-9
> (N = 2, `st_regression`) — the cross-block transient at perturbation amplitude. The F = 10
> similarity check is therefore expected to FAIL at N = 25; that failure is a result, and the
> interpretation rule is fixed now: the dial-less one-pass arm's delivered accuracy is a
> **reported capability difference** (R9) — each arm's accuracy is published at its cost, no
> extrapolated matched read is fabricated, and the per-node count table plus the
> weighting-invariance bracket remain the cost evidence. Nothing was tuned in response.

**Metrics (counts only; acceptance never on a timing):**
- **per-node model-evaluation counts** (primary; recorded for every run, enabling
  weighting-invariance bounds later without re-running — the I-10 insurance);
- per-block totals (M1/M2/M3/FF) and predicate-evaluation counts;
- the exact entry state of every run (snapshot + perturbation record), so the evaluated
  regime is itself part of the record; the cold-start term reported beside, never mixed in;
- failure taxonomy per start: crashed / refused / unconverged / infeasible-at-audit, with
  denominators (A30's lesson); failures count to robustness, completions to cost statistics.

**Declared expectation:** blocks converge at their own rates (fewer sweeps for
fast-contracting blocks), FF nodes execute once; the per-call saving is positive on all three
decks; its magnitude is the number being measured (prior context: A28 measured the receipted
variant at −1.63 %/−6.18 %/inconclusive with the ~38 %-of-solve-phase verification pass still
charged; V2's arm does not carry that pass).

## 4. Phase B — optimisation comparison (the headline)

**Arms: five.**

| arm | architecture | isolates (vs previous) |
|---|---|---|
| R | PROCESS as shipped (its idempotence loop) | anchor |
| B0 | proper flat fixed-point MDA, predicate-matched | stopping rule (R→B0) |
| B1 | flat MDA + burn-time coupling lifted to optimiser (constraint 93) | the lift (B0→B1) |
| B2 | partitioned block MDAs **with the outer verification loop**, lifted coupling, post-solve set executed once per run | the partition (B1→B2) |
| B3 | as B2 but **no outer loop** (trust mode): one chain pass per call | the outer-loop removal / trust step (B2→B3) |

The partitioned-with-outer-loop arm B2 was dropped in revision 1 as "never a candidate
architecture" and **re-admitted by the user (2026-09-03, evening) before any campaign run**,
on measured cause: the trust-vs-verified single-trajectory context (iterations 8→8 / 13→12 /
10→20 across the decks) showed the outer pass may buy optimiser-consumed interior accuracy, so
whether its per-call cost is repaid in iterations is now a declared question, answered by
B2→B3 with everything else identical (same post-solve set, same inner τ). **B0→B3 is the
headline comparison (the designed architecture); R→B3 the user-facing figure; B0→B1 the lift;
B1→B2 the partition; B2→B3 the trust step.** On `st_regression` (k = 0) B1 degenerates to B0
and is skipped.

**Settings.** Optimiser settings default (comparability with reference). Same τ across arms,
with the Phase-A similarity criterion re-applied at accepted optima.

**Initial guesses (pre-declared rule).** One perturbation stream, seed-paired across all five
arms: ±10 % (δ = 0.10) on all iteration-variable initial guesses. In B1/B2/B3 the lifted
variable's initial guess is **the same perturbed value the coupling would start from in
R/B0** — the lift adds a variable, never a different starting state. (n vs n+1 iteration
variables is part of the intervention, including its finite-difference gradient cost.)

**Checks, each testable and pre-declared (never on iteration variables — D6):**
1. **Same optimum:** per-start paired |Δ norm_objf| plus the post-solve feasibility audit.
   The yardstick for a "harmless" difference is **measured inside the same campaign**: the
   R→B0 paired |Δ norm_objf| spread — the stopping-rule change's own footprint — rather than
   an assumed state-to-objective sensitivity. Acceptance: the B0→B1, B0→B2 and B0→B3 paired
   spreads are not larger than the R→B0 spread by more than the declared factor (F, §3's).
   The full paired distributions are published either way.
2. **Iteration multiplier:** paired per-start ratio of optimiser iterations (and of function
   evaluations) for B0→B1, B0→B2 and B0→B3, median and q1–q3 per deck; B2→B3 reported beside
   them (the trust step's own multiplier). Acceptance per arm: median paired iteration ratio
   ≤ 1.05. *Licensing measurement:* A28 measured paired ratios of exactly 1.000/1.000 on two
   decks **with the lift in place** — the bar is strict because it has been met under the
   same lift.
3. **Lift actually closed:** constraint-93 residual at every accepted optimum, reported per
   start.
4. **Robustness:** paired multi-start with the A30 taxonomy (crashed / refused / unconverged /
   infeasible-at-audit, denominators named), identical-success-set cost comparisons, and
   refusal attribution by arm (the D18 lesson: two-thirds of V1's refusal deficit was the
   predicate, not the architecture).

**Declared per-deck expectations (hypotheses, written before the first campaign run):**
B2 ≈ B0 in iterations everywhere (licensing: A28's 1.000/1.000 with the lift). B3 ≈ B2 in
iterations on the pulsed decks and **may inflate on `st_regression`** (single-trajectory
context: 10→20; mechanism hypothesis: one-pass interior states carry ~30×-per-pass more
sub-τ dust into the finite differences via the cross-block transient — A35's subject).
Post-solve suppression ≈ 8.3/8.4/11.3 % of solve-phase node calls (A33's measured
baselines). Phase A per-call saving positive on all three decks. Each expectation can fail;
a failure is a per-deck result.

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
3. **B2 trust-mode driver path** — partitioned `module_solve` without the outer verification
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
5. **Anchor accuracy — RESOLVED (user, 2026-09-03): option (a).** The anchor is
   **measured from R per deck in the same campaign** (same instrument, same starts, same
   spec generation), with a declared sanity check afterwards: the measured anchors are
   compared against A28's call-1 magnitudes (5.1e-07 / 9.3e-08 / 0.0) and an anchor that
   looks wrong (orders away, or degenerate where A28 was not) is investigated before any
   conclusion cites it.
6. ~~A32 merge precedes execution~~ **Resolved 2026-09-03:** A32 assessed and merged
   (`637a6bb6`) — tail confirmed dissolved, driver fix gated switch-neutral.
7. **Post-solve hoist** is part of the intervention in both phases (user decision
   2026-09-03); the classification artifact and driver capability are task A33's
   deliverables and precede execution.
