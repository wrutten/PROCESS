# V3 development plan — MDA partitioning experiment, third revision

> **Document status** — **CURRENT · DEVELOPMENT PLAN, §0 fully resolved 2026-09-04; execution started** (tasks A39–A41 dispatched; A42 blocked on their merges + the user's dated execution approval).
> Written 2026-09-04 by the investigative-orchestrator session (`process-surgery-bf`) at the
> user's instruction, from the committed record at `architecture_surgery` HEAD (`59bc0db0`):
> [`V3_IMPROVEMENT_LIST.md`](V3_IMPROVEMENT_LIST.md) (the candidate list this plan selects
> from), [`../reports/V2_EXPERIMENT_REPORT.md`](../reports/V2_EXPERIMENT_REPORT.md),
> [`../reports/deprecated/A35_cold_census.md`](../reports/deprecated/A35_cold_census.md),
> register entry V15, and the V2 run records under
> `arch_surgery/MDA_partitioning_experiment_v2/runs/`. Untracked until the orchestrating
> session commits it on `architecture_surgery` (protocol §10: one actor per working tree).
> Base commit `c0ae5b28` (D2) throughout. **V2's plan and directory are frozen as the record
> of what ran; nothing in them is edited by V3.** This document plans the *development* of
> V3; the experiment plan V3 will run under is deliverable T1 (§8) and restates every
> selection here with its pre-declared acceptance rule.

| | |
|---|---|
| **What V3 is** | V2's intervention plus one method-level fix folded into it (the `FirstWall → Build` first-wall-thickness **prime**, A35's carrier: one run-constant method hoisted to the sweep head — **not** a reorder of the `FirstWall` node), measured under a corrected accuracy audit and declared tally constructions, on the V2 arm lattice, with the V2 entry regime retained |
| **What V3 is not** | a harvested-entry redesign of Phase A; a cold-start comparison row; a powered robustness campaign (deferred, user 2026-09-04); gradient-quality instrumentation inside the campaign (O1 resolved: excluded; lad's trust-step inflation stays "mechanism unknown", investigated after the campaign if it persists) |
| **Decisions this plan rests on** | user, 2026-09-04, in session `process-surgery-bf`: the prime is part of the V3 intervention; the synthetic warm δ-stream stays (no harvest, no cold row); the audit correction is a harness fix separate from the intervention; the "dead needs two qualifiers" register convention is adopted. Improvement-list items 4/5/6/8/11(a)/13 are user-decided there or in the orchestrating session; items 1 (direction), 2, 3, 7, 9, 10, 12 are orchestrator proposals assessed in §1 |
| **Numbering** | tasks and decisions were proposed here with placeholders; minted 2026-09-04 under the user's start instruction: **T1 → A39 (v3-plan), T2 → A40 (v3-prime), T3 → A41 (v3-harness), T4 → A42 (v3-campaign, blocked on A39–A41 + the user's dated execution approval); the prime decision → D19.** T5 is deliberately not minted (O1: post-campaign, contingent) |

---

## 0. Open items for the user — resolve before this plan is committed

Each item below is either a deviation from the improvement list or a construction this plan
chose where the list left a choice. The plan is written under the recommendation; an
override changes the marked section only.

| # | item | recommendation in this plan | alternative | where |
|---|---|---|---|---|
| **O1** | Improvement-list item 10, gradient-quality diagnostics (per-gradient-point exit audits) | **RESOLVED 2026-09-04: recommendation accepted** (user: *"keep it as mechanism unknown. See if it changes now. We investigate the root causes for strange behaviour after the new experiment"*) — so T5 is deferred until after the campaign, contingent on the adverse result persisting. **Not in the V3 campaign.** A per-call uncharged audit inside an optimisation is a new driver instrument with its own neutrality gate and a runtime cost on every call; it serves an adverse result on one deck, not the existence proof. V3 declares "mechanism unknown" for lad's trust-step inflation as the honest baseline, and closes A35's declared scope gap cheaply instead: the traced verified chain on lad (A35's `trace` and `restarts` stages, ~7 single evaluations) as pre-campaign gate G3c. A separate diagnostic task after the campaign, on lad only, is proposed as optional T5 | include the instrument in T2 and run it on B2/B3 lad pairs inside the campaign (adds a driver hook, a gate, and ~20–30 % wall time on those runs) | §1 item 10, §5 G3c, §8 T5 |
| **O2** | lad sample size | **RESOLVED 2026-09-04: N = 25 everywhere** (user: *"don't change to 50 now"*). lad's B2→B3 verdict stays on ~10 converged pairs and is published with that denominator. (Recommendation was N = 50 on lad; V2's Appendix B still allows extending by dated amendment later if a 1–2-start difference matters) | — | §3.2 |
| **O3** | Improvement-list item 1, the yardstick floor construction | **RESOLVED 2026-09-04: option A accepted — floor = 1e-6 relative on `norm_objf`**, the tolerance the correctness gate has used since A25 (its provenance is PROCESS's own `check_agreement` rtol, not a choice made here); acceptance `spread ≤ max(F × yardstick, floor)`. The list's candidate (a), re-running R from identical starts, measures **zero** on this instrument (V2 §9: references reproduced bit-exactly across three executions), so it cannot serve as a floor | a measured dust floor: R from each deck's baseline start with a 1e-12-relative kick on every design variable, 3 reps per deck, the resulting `|Δ norm_objf|` spread as the floor (9 runs, context-grade) | §4.2 check 1 |
| **O4** | where the prime is switched on | **RESOLVED 2026-09-04: recommendation accepted — A1, B2 and B3 only** — the same placement as the `build_after_physics` reorder, so the B1→B2 step reads "the partition, including the reorder and the prime it requires". R stays PROCESS as shipped; B0/B1 keep upstream order. The flat arms self-repair the lag at a cost of at most one sweep on call 1, so priming them would change nothing measurable and would move the reference arm's first call | seed on in every arm except R (then R→B0 carries the prime's ≤ 1-sweep first-call effect as well as the stopping rule) | §2, §3 |
| **O5** | prime-free Phase B counterparts | **RESOLVED 2026-09-04: none** (user: the prime's individual Phase B impact is not needed — the whole intervention's effect on optimiser convergence is measured by the arm ladder; the prime rides inside the B1→B2 step and is not separately attributed there). The prime's Phase B inertness after call 1 is established by gate G2 (fixed-point map bit-identical) and disclosed; paired B2u/B3u arms would cost ~150 optimisations to show a difference the dust floor cannot resolve. Phase A *does* carry the prime-free block arm (A1u) because there the prime's effect is the measurement | add B3u on one deck as a spot check (25 runs) | §3 |

Everything else in this plan is either user-decided or an orchestrator proposal this
assessment endorses as written (§1).

---

## 1. Critical assessment of the improvement list, item by item

| item | status at HEAD | assessment | folded in as |
|---|---|---|---|
| 1 yardstick floor | user-decided in direction | Right diagnosis: the R→B0 spread landed at machine noise (3.3e-15 on nof), so any nonzero footprint failed while agreeing to 1e-10. Candidate floor (a) is measurable and equals zero on this instrument; candidate (b) needs a sensitivity the records do not hold. The project already owns a tolerance with provenance: D6/A25's 1e-6 relative | §4.2 check 1, construction per **O3** |
| 2 declared pairing and taxonomy; iterations at unconverged exits | proposed | Endorsed. The V2 tally's silent drop happened to equal the correct construction; V3 declares it. The data gap is real: `run_one.py` reads `n_solver_iterations` from the data structure but the record carries it only at `ifail = 1` | §4.2 check 2; §6 harness H3 |
| 3 multi-attractor decks | proposed | Endorsed. st shows ≥ 4 accepted optima; a hop is a counted event, not an outlier. Declared rule in §4.2 | §4.2 check 1a |
| 4 audit restricted to the in-loop write set | user-decided | Endorsed and load-bearing: 75/75 A1 audit argmaxes are post-solve-owned. The exclusion set is the deck's committed post-solve node list mapped to components through the a26 write-set subsets, **not** a prefix list (on st the set also contains `pulse`, which writes nothing there). V2's published 75/75 census is unaffected — every argmax was `costs` or `water_use`, captured either way — but the write-set mapping is the construction V3 declares. Both audits published. Re-run, not re-tally: the records hold `y_exit.json` (162/162) but not the post-audit state | §3.1 (arm A1u), §4.1, §5 G4, §6 H4 |
| 5 carrier controls / the prime | user-decided: prime folded in | The prime makes the perturbation-stream control moot; the counterfactual is A1u → A1 under the corrected audit, on the same entries. Attainable gates replace bit-identity (§5 G1–G3) | §2, §3, §5 |
| 6 regime disclosure; known-cut displacement field | user-decided (a); add-on pending | Disclosure carries verbatim from the V2 report. **The add-on is not a data gap**: every Phase A run's `perturbation.json` already records the factor and before/after hex of `build.dr_fw_inboard`, `build.dr_fw_outboard` and `pf_power.vpfskv` (checked on `st_regression/A1/start001`). V3 makes the tally read it and compute the A35-predicted carrier term per run | §4.1 closure check; §6 tally T-e (no harness change) |
| 7 failure forensics at non-converged exits | proposed | Endorsed; the lad failures are direction-driven, so the killing constraint family is the only lever left. Record the constraint residual vector, the active set, `ifail` and the ladder stage at every non-`ifail = 1` exit | §6 H3 |
| 8 powered robustness campaign | **deferred** (user) | Deferred as decided. What survives: the deck-invalid-seed statistic in the tally (a seed failing in every arm is excluded from per-arm rates and counted separately) | §4.2 check 4 |
| 9 per-deck amplitude; interior vs shell | proposed | **Not adopted.** Shared δ = 0.10 keeps the three decks comparable and the measured null says amplitude is not the failure lever; interior sampling is declared. The yield problem on lad is addressed by N, not δ (**O2**) | §3.2 declaration |
| 10 gradient-quality diagnostics | proposed | **Deviation — see O1.** The cheap, independent step is the lad carrier census the A35 report declared as its scope gap | O1; §5 G3c; §8 T5 |
| 11 per-block wall clock, route (a) | user-decided | Endorsed as context only (I-10 stands): one profiled run per deck, per-node unit times with n = 3 ranges, per-block time reconstructed from the recorded counts; both caveats (state-independence, driver overhead outside node time) published with it | §6 A-b |
| 12 per-block split as tally output | proposed | Endorsed; the analysis already computes it from per-run censuses | §6 tally T-d |
| 13 captions | in force (§16) | Binding on every V3 table | §7 |

Two items the list does not carry, added here: the register-convention amendment the user
agreed to (§6 D-b), and the pre-declared lad prediction the prime makes testable at zero
cost (§4.2).

---

## 2. The intervention, restated with the prime

V2 defined the intervention as one unit: partition the MDA into three block MDAs in
feed-forward order; lift the burn-time coupling to the optimiser with constraint 93;
feed-forward nodes execute once per call; post-solve nodes execute once per run. V3 adds
one element to the same unit:

> **The prime.** The first-wall thicknesses `build.dr_fw_inboard` and
> `build.dr_fw_outboard` are a run-constant of two deck inputs, computed by `FirstWall`
> (block M3, `fw.py:347-352` at `c0ae5b28`) and read by `Build` (block M2, `build.py:826-842`,
> `:1862-1889`, `:1940-1947`), which the schedule runs first. Under an iterating driver the
> lag costs at most one sweep; under a one-pass schedule it transmits exactly the entry
> displacement of the pair, once (A35, V15). V3 primes the pair at the head of every sweep of
> the block arms, so `Build` reads this pass's value. It is a driver choice about *when* an
> existing model method runs — the same family as the `build_after_physics` reorder but
> finer-grained (a method, not a node); no file under `process/models/` changes.
>
> This is **not an ordering fix at the collapsed-model level** (user, 2026-09-04): the
> `FirstWall` *node* stays exactly where the schedule has it. Moving the node wholly ahead
> of `Build` would carry its physics-dependent reads upstream of their writers and create
> new backward edges; what moves is the one run-constant method, the only part of
> `FirstWall` whose inputs are pure deck inputs.

**Implementation shape** (deliverable T2; the only `process/` change in V3):

```python
# process/core/caller.py, module level, beside the sequence variant point
_PRIME = {"off": False, "fw_geometry": True}
PRIME_NAME: str = os.environ.get("PROCESS_ARCH_PRIME", "").strip() or "off"
if PRIME_NAME not in _PRIME:
    raise RuntimeError(...)          # an unrecognised value raises, never defaults
PRIME_FW_GEOMETRY: bool = _PRIME[PRIME_NAME]

# Caller._call_models_once, after the stellarator/IFE early returns,
# before the SEQUENCE_HEAD loop
if PRIME_FW_GEOMETRY:
    self.models.fw.set_fw_geometry()   # not a node, not counted, idempotent
```

Not routed through `Caller._node`, so it adds no counted node call and every count
comparison stays commensurable with V2. **Stamped, not counted** (user question,
2026-09-04): the runner records `n_prime_calls` in every run's metrics and the tally
publishes it as a footnote beside the node-call tables, never pooled into them (trap T11 —
no silent work). Nothing is removed from `FirstWall`, whose own execution and cost are
unchanged — the prime *duplicates* a run-constant of two floating-point operations at the
sweep head — so neglecting it in the cost ratios is a disclosed, bounded statement, not an
assumption. **Coverage requirement** (T1 states it, T2 verifies
it): the block schedule's `Caller._sweep_block` runs a block by calling `_call_models_once`
with the node filter set (VP4), so the site above is on every block sweep's path as well as
the flat loop's; T2 confirms it by counting the prime's executions in a traced verified
chain, which must equal that run's block-sweep count. Its two inputs are loader-written and outside the
coupling-state spec, so the perturbation stream never touches them. It runs at the head of
every block sweep (two floating-point operations, identical bits each time) and in the
output-phase and audit callers (harmless, idempotent). It also cures `FirstWall`'s own stale
self-read of the pair (`fw.py:54-55` before `:110`, the sibling's owed row M117).

**What the intervention may then claim, pre-declared.** A35's census gives the backward-edge
set the trust schedule cuts as exactly the pair on `st_regression`, and on the pulsed decks
the pair plus `pf_power.vpfskv` (a literal, whose only computational reader is the CS emf term of the ramp-time
calculation, `pulse.py:224` at `c0ae5b28` — line 326 in the working tree at HEAD after A24's residual
extraction, which is why line numbers here are always the base commit's — feeding constraint 41 — inactive on all three
decks per A26, and carried commented-out with an inline justification in the `st_regression`
deck) plus the burn time (lifted). With the prime, **no cut edge on the
three decks carries a displaced value into a one-pass exit**; gate G3 tests exactly this and
names any residual mover.

**Register and decision bookkeeping.** The user's decision to fold the prime into the
intervention is to be recorded as a decision row (placeholder **D19**) by the orchestrating
session. The prime's defect note goes to the sibling's M117 row with A35's magnitudes and the
initialisation-time fix shape (§6 D-a); no new handoff.

---

## 3. Arms

### 3.1 Phase A — per-call MDA cost, no optimiser (three arms)

| arm | architecture | role |
|---|---|---|
| **A0** | flat coupling-state MDA at τ; post-solve nodes inside its loop | control, as V2 |
| **A1u** | V2's A1 exactly: resequenced blocks, trust mode, post-solve exclusion, lift + pin on the pulsed decks, **no prime** | the corrected-audit re-run of V2 (list item 4) and the prime's counterfactual |
| **A1** | A1u plus the prime | the V3 intervention's per-call structure |

Entries: V2's design unchanged (user decision) — per deck one A0 cold reference at the deck
point, whose cost is the once-per-run cold-start term; campaign entries are seed-paired
multiplicative ±δ perturbations of that snapshot, seeds 1–25, δ = 0.10, τ = 1e-6, a26
artifacts, pin on the pulsed decks from the same stream. Pairing check across all three
arms per seed (bit-identical entry states). The regime disclosure from the V2 report carries
verbatim: the stream displaces run-constants and post-solve outputs that no optimiser-driven
call displaces after call 1, so this regime is deliberately more hostile than B3's.

A1u is already measured: task **A38** (merged 2026-09-04, `e9e7e965`) ran exactly this arm
under the corrected audit at the mint commit — restricted medians 6.4e-4 / 9.8e-4 / 1.15e-3
against A0's 5.0e-10 / 0 / 5.4e-9, FAIL at F = 10 on all decks as §4.1 pre-declares, with
the composition per deck in its report (`deprecated/A38_audit_rerun.md`): nof and st 25/25
linear images of the pair; **lad's argmax in 21/25 is `tfcoil.m_tf_coil_superconductor`,
not one linear image of the pair — G3c's open term**. T4 reuses A38's numbers if G1 holds
at the V3 driver commit (prime unset ⇒ byte-identical behaviour), else re-runs the arm;
either way the report states which.

### 3.2 Phase B — optimisation, the headline (five arms, as V2)

| arm | architecture | isolates |
|---|---|---|
| R | PROCESS as shipped | anchor |
| B0 | flat coupling-state MDA, predicate-matched | stopping rule (R→B0) |
| B1 | B0 + burn-time lift (constraint 93) | the lift (B0→B1) |
| B2 | partitioned blocks with the outer verification loop, lift, post-solve, **prime** | the partition including its ordering fixes (B1→B2) |
| B3 | B2 without the outer loop (trust), **prime** | the trust step (B2→B3) |

`st_regression` skips B1 (k = 0). Starts: start000 unperturbed plus 24 perturbed at
δ = 0.10, seed-paired across arms, interior sampling declared (u uniform in [−1, 1) per
component, bounds-clamped); N = 25 per deck (O2 resolved 2026-09-04: no lad extension now —
the B2→B3 lad verdict stays on ~10 converged pairs and is published with that denominator).
Same τ everywhere; the lifted variable's initial guess is the value the coupling would
start from in R/B0.

---

## 4. Pre-declared checks and expectations

### 4.1 Phase A

- **Similarity, corrected.** Per deck, the audited max-scaled residual distributions over
  components **not owned by the post-solve set**, arm pairs A0/A1u and A0/A1, within F = 10
  at median and p90. The whole-state audit is published beside it. Expected, from A35's
  coefficients: A0/A1u **fails** on the carrier term alone (A1u ≈ 5e-4 against A0 ≈ 5e-9 on
  the traced decks); A0/A1 **passes**, or a residual mover is named as a new carrier — either
  is a result.
- **Carrier closure per run** (list item 6 add-on, tally-side). From each A1u run's recorded
  entry displacement of the pair, the predicted A35 image (0.5·(Δin + Δout) on nof's top
  mover; −Δout on st's) is compared with the measured restricted-audit maximum; relative
  difference published per run. `low_aspect_ratio_DEMO` has no coefficient yet; G3c
  supplies it.
- **Cost.** Per-node counts, per-block totals, the unweighted A1/A0 ratio and the
  weighting-invariance bracket as V2; A1u/A1 counts expected equal to within one M2 inner
  sweep (the prime changes what `Build` reads, not how often it runs). Prior context, V2:
  0.522 / 0.568 / 0.502.
- Lift residual reported separately; cold-start term beside, never pooled; failure taxonomy
  with denominators.

### 4.2 Phase B

1. **Same optimum.** Paired `|Δ norm_objf|` at accepted optima; yardstick = the R→B0 spread;
   acceptance `spread ≤ max(F × yardstick, floor)`, floor = 1e-6 relative on `norm_objf`
   (**O3**, resolved 2026-09-04). **1a,
   multi-attractor decks**: accepted optima clustered by `norm_objf` with a declared gap
   (relative gap > 10 × floor separates clusters); within-cluster agreement and the hop
   rate per arm pair reported, R→B0's hop rate as comparator.
2. **Iteration multiplier.** Paired ratio over both-converged pairs (declared), median
   ≤ 1.05 for B0→B1, B0→B2, B0→B3; B2→B3 and B0→R beside. **Pre-declared lad prediction
   the prime makes testable at zero cost:** B2→B3 on lad stays elevated at ≈ 1.33–1.40
   (the two committed median constructions over V2's 10 pairs disagree in that one cell —
   V2 report §5.3 correction note, 2026-09-04; **V3 declares nearest-rank as its single
   median construction for every Phase B check**, under which the anchor is 1.40) within
   the dust floor, because the carrier is inert after call 1. If it falls to ≈ 1.0, the
   first-call deficit *was* the mechanism on lad and A35's inertness reasoning is refuted
   there; both outcomes are results.
3. **Lift closed.** Constraint-93 residual at every accepted optimum, per start.
4. **Robustness reporting and cost.** The A30 taxonomy computed in the tally with
   denominators; the **deck-invalid-seed statistic** (a seed failing in every arm is
   excluded from per-arm rates and counted separately); identical-success-set cost sums per
   arm; the per-block split as a tally artifact. No robustness *claim* is made (item 8
   deferred).

Expectations per deck (prior context from V2, not acceptance): nof B0→B3 ≈ 0.64 in node
calls at median iteration ratio 1.000; st ≈ 0.68 at 1.000; lad end-to-end ≈ 0.76 with the
transfer clause applied as in V2 unless check 2 passes there. Decks are never pooled.

---

## 5. Gates, each with teeth (protocol §12), run before any campaign number is cited

| gate | binds | criterion | teeth |
|---|---|---|---|
| **G0** V3 driver neutrality | every arm | R × 3 decks at the V3 driver commit reproduces V2's recorded R start000 bit-exactly on count fields and objective hex | +1 on a count, 1 ULP on the hex, each must trip |
| **G1** prime off, byte identity | R, B0, B1 | `PROCESS_ARCH_PRIME` unset ⇒ MFILE hex floats identical to a run at the pre-T2 commit, 3 decks (A3's comparator); both runs fresh at their respective commits with identical environment sets, both stamps recorded in the gate record | a 1-ULP change to one float is caught |
| **G2** prime on, fixed-point map | the claim that the prime changes nothing after the first-wall model has run | from each deck's reference exit snapshot: one `flat_state` call and one `per_module` call, prime on vs off, exit states bit-identical on N/N components (nof 840, lad 846, st 827 — labelled 2026-09-04, A39's finding: the earlier unlabelled "(827 / 840 / 846)" was out of the document's deck order) | a doctored snapshot component trips the comparison |
| **G3** prime on, cold chain (A35's stages) | the "no cut edge carries anything" claim | verified block chain from the cold deck entry: outer passes 3 → **2** on nof and st; trust chain exit vs the flat fixed point, **in-run `exit_audit` operationalization: 0 above τ** (A35 in-run: 244 / 124; the A35 report's snapshot-pair construction reads 243 on nof — the ±1 near-τ spread is documented in A35 §9, and the gate names its construction so a reproduced 243 is not misread); any residual mover named | the prime-off run must reproduce A35's 3 passes and 244 / 124 |
| **G3c** lad carrier census | A35's declared scope gap; the O1 alternative | A35's `trace` + `restarts` stages on `low_aspect_ratio_DEMO`, prime off then on: the carrier coefficient on that deck, and the residual mover set with the prime | as G3 |
| **G4** audit restriction | the corrected similarity statistic | a doctored post-solve-owned component in an exit snapshot trips the whole-state audit and **not** the restricted one; a doctored in-loop component trips both | both directions shown |
| **G5** B3 combined-switch equivalence | B3 | as V2's `armgate`, re-run with the prime in the switch set | as V2 |
| **G6** Phase A entry-state and warm equivalence | Phase A | as V2 (A36), re-run at the V3 commit for all three arms | as V2 |
| **G7** record completeness | items 2 and 7 | a deliberately unconverged smoke run carries `n_solver_iterations`, the constraint residual vector, the active set and the ladder stage | a run with a field missing is refused by the tally |

A failed gate stops the dependent stage and is reported with its numbers; nothing is retried
with different settings. Full-run neutrality of the prime (objective within the D6 tolerance,
iteration medians within the dust floor) is not a gate but a published context table from
the campaign itself: bit-identity across an optimisation is unattainable for any change to
sweep 1 of call 1, and is not claimed.

---

## 6. Harness, driver, tally and documentation changes

**Driver (H1, task T2, the only `process/` change):** the `PROCESS_ARCH_PRIME` variant
point of §2; the variable added to every cleared-switch list (`run_a28._ARCH_VARS` consumers,
the V3 runner) and stamped into every run record (`env_PROCESS_ARCH_PRIME`,
`arch_prime_name`, `n_prime_calls` — the invocation count published as a footnote,
never pooled into node calls; §2).

**Runner and records (H2–H3, task T3):**
- H2 — the V3 runner composes arms from nothing with every switch cleared, as V2's did; A1
  and B2/B3 add the prime.
- H3 — `run_one.py` and `v2_eval_one.py` record at **every** exit: `n_solver_iterations`,
  `ifail`, the ladder stage, the constraint residual vector and the active set (items 2, 7).
  A field missing at an unconverged exit is a tally refusal (G7).

**Tally (T-a … T-e, task T3):**
- T-a — similarity over the restricted component set (post-solve nodes → components via the
  a26 write-set subsets), whole-state audit beside (H4 in the runner: the audit records the
  per-component residual vector, so a re-tally is possible next time).
- T-b — declared pairing (both-converged) and the A30 taxonomy with denominators; the
  deck-invalid-seed statistic.
- T-c — check 1 with floor and the multi-attractor clustering and hop rates.
- T-d — the per-block node-call split as a first-class artifact.
- T-e — the per-run carrier closure from `perturbation.json` (no new field needed).

**Analysis, context only (A-a, A-b, task T4):** timing block as V2 (3 serial reps, ranges);
per-node unit wall time from one profiled run per deck and the per-block reconstruction, with
its caveats (item 11a).

**Documentation (D-a, D-b, task T1):**
- D-a — the prime's defect note for the sibling's owed M117 row: the read-before-write pair,
  A35's displaced-state magnitudes, the initialisation-time fix shape (compute the pair in
  `init.check_process` beside the double-null geometry derivation; delete the model's write;
  the same treatment for the `vpfskv` literal), per the sibling's bug-report structure.
- D-b — `DSM_VALIDATION.md` convention amendment: a liveness verdict states both
  value-liveness and displacement-liveness (V15); user agreed 2026-09-04, orchestrator to
  confirm at execution.

---

## 7. Directory and run discipline

New directory `arch_surgery/MDA_partitioning_experiment_v3/`, mirroring V2:

| file | role |
|---|---|
| `EXPERIMENT_PLAN.md` | the V3 experiment plan (deliverable T1): objective, arms, checks, gates, approval status header; every later change a dated amendment |
| `v3_config.py` | every declared setting in one place; `EXECUTION_APPROVED = False` until the user approves the plan in the same commit; `INSTRUMENTATION` ledger with `prime` (T2) and `exit_forensics` (T3) entries that make campaign stages refuse while False |
| `v3_runner.py` | thin layer over `arch_surgery/idf_probe/` (never a duplicate of it): arm environments from nothing, isolated fresh-subprocess runs, the W = 3 pool, resume semantics, clean-tree stamps |
| `phase_a.py` | preflight / reference / gates G4 G6 / campaign (A0, A1u, A1) / tally |
| `phase_b.py` | preflight / gates G0 G5 / campaign (R, B0, B1, B2, B3) / tally / timing |
| `run_experiment.py` | one-button entry point; draft mode runs preflights, gates and smoke only |
| `v3_report_analysis.py` | independent recomputation of every published table from the records; `--verify` |
| `runs/` | untracked bulk artifacts; summaries and verdicts committed |

V2's directory is not edited. **Reuse from V2 is the default, explicitly** (user directive,
2026-09-04): T3's **first commit is a verbatim copy of the V2 harness** into the v3
directory — unchanged content, provenance (source path + commit) in each copied file's
docstring — so every subsequent modification is legible in history as a diff against V2.
Thin layers still import `arch_surgery/idf_probe/` rather than duplicating it; a copy that
diverges is a new file in v3, never a patch to the V2 record. Every published number comes from a committed script (§15); every table carries a
caption (§16); bulk artifacts stay untracked; the machine's one heavy slot is respected.

---

## 8. Proposed task decomposition (the user mints numbers and keywords)

| placeholder | keyword | scope | touches | prerequisites |
|---|---|---|---|---|
| **T1** | `v3-plan` | write `MDA_partitioning_experiment_v3/EXPERIMENT_PLAN.md` from this document with pre-declared acceptance rules; D-a and D-b | docs only | O1–O5 resolved |
| **T2** | `v3-prime` | the `PROCESS_ARCH_PRIME` variant point; gates G1, G2, G3, G3c with teeth; committed gate script | `caller.py`; record stamping in the two runners | — |
| **T3** | `v3-harness` | the v3 directory: **first commit = verbatim copy of the V2 harness (§7)**, then the config/runner/skeleton modifications as separate commits; H3 exit forensics; the tally constructions T-a … T-e; G4, G7; `--verify` | `arch_surgery/` only | — |
| **T4** | `v3-campaign` | G0, G5, G6; Phase A (3 arms); Phase B (5 arms, N = 25 per O2); tallies; timing; unit-time reconstruction; the V3 report | `arch_surgery/` only | T1, T2, T3 merged; user approval flips `EXECUTION_APPROVED` |
| **T5** (optional, O1) | `lad-gradient-diagnostic` | per-call uncharged exit audits on seed-paired B2/B3 lad runs, hypothesis pre-declared | driver hook + gate | T4 reported |

T1, T2 and T3 are independent and may run in parallel (T2 is the only heavy-slot user among
them, for its gate runs). T4 is the single heavy campaign. Bundling T2 into T3 is not
recommended: T2 is the only `process/` change and deserves its own neutrality gate and merge.

**Cost, context only, from V2's timings.** Phase A: 3 arms × 25 seeds × 3 decks plus
references and gates, roughly 1.5 h at W = 3. Phase B: 350 optimisations at N = 25,
roughly 3–4 h at W = 3. Gates: under an hour.

---

## 9. External watches and scope

- The sibling study's **M120** (process-line runtime validation, transferred from our
  cancelled A37) — **resolved 2026-09-04, nothing routed back**: the tokamak process line
  is runtime-validated (338/338 canonical solve calls in identical relative order); the one
  HIGH defect is stellarator-only, the `call_index` defect has zero cross-model tokamak
  occurrences. The ordering V3's partition and prime are grounded in is now
  trace-confirmed, not only statically derived.
- The sibling's owed **M117** row is the home of the defect note (D-a).
- Scope as V2: three decks, tokamak only, one commit, one perturbation stream, one
  optimiser; per-deck conclusions, decks never pooled.

---

## 10. Change log

- 2026-09-04 — drafted by the investigative-orchestrator session from HEAD `59bc0db0`;
  untracked; open items O1–O5 put to the user; handed to the orchestrating session for
  review and commit once resolved.
- 2026-09-04 — orchestrating session's review: endorsed as drafted, O1–O5 recommended
  unchanged; its four non-blocking notes folded in (hook-site coverage requirement in §2;
  G3's operationalization named; G1's cross-commit stamping; T-a's write-set mapping with
  the V2 census unaffected).
- 2026-09-04 — re-review: the `vpfskv` reader citation queried as 326; verified 224 at
  `c0ae5b28` (326 is the working tree after A24, `0a2e64f3`); cross-reference added, number kept.
- 2026-09-04 — user resolutions applied by the orchestrating session: **O2 resolved** (N = 25
  everywhere), **O4 resolved** (accepted). Terminology: the FirstWall fix renamed **prime**
  throughout, ending the collision with the perturbation seeds; §2 states it is a
  method-level hoist, not a collapsed-model node reorder (the user's framing: moving
  `FirstWall` wholly would create new back edges). The prime invocation is stamped
  (`n_prime_calls`), never pooled into node counts (user question on call accounting).
  §7/T3: T3's first commit is a verbatim copy of the V2 harness (user directive, diff
  legibility). §3.1: A38 (dispatched today) measures A1u at the current commit; reuse
  licensed by G1. **O1, O3, O5 remain open.**
- 2026-09-04 (later) — §3.1 note updated to A38's merged result (`e9e7e965`); the fix
  renamed **prime** (user: "preseed" confusing; 64 sites, including `PROCESS_ARCH_PRIME`,
  `n_prime_calls`, gate names, T2's keyword `v3-prime`); **O3 resolved** (option A, floor
  1e-6 relative); **O5 resolved** (none — the user's rationale recorded in the row; per-deck
  differences read from the results, taken from there). **O1 remains the only open item.**
- 2026-09-04 (execution start) — **O1 resolved** (recommendation accepted: mechanism unknown
  as baseline, G3c in the gates, T5 post-campaign and contingent); §0 fully resolved; the
  user instructed the readiness check and start. Committed by the orchestrating session;
  tasks minted A39/A40/A41 (T1/T2/T3, parallel) and A42 (T4, blocked on their merges + the
  user's dated execution approval per §7's `EXECUTION_APPROVED` rule); D19 minted for the
  prime decision. A38's merged instruments noted as reusable: `v2_eval_one.py` already
  carries the restricted audit and `audit_residual.json`, and its G4-style teeth are the
  template for T3's.
