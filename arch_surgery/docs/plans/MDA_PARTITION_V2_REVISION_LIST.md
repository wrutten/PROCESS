# MDA partition experiment, V2 — revision list

> **Document status (2026-09-03).** Planning list only — **not authorised for execution**
> (user, 2026-09-03: *"I don't want to execute this now. But add it to a plan list to revise
> the experiment. I want to build a new experiment from scratch."*). Items here are design
> decisions and open questions for a from-scratch successor to
> [`MDA_PARTITION_EXPERIMENT.md`](MDA_PARTITION_EXPERIMENT.md); nothing here amends the
> published Phase A/B results, which stand as measured.

## The central design change (user, 2026-09-03)

**R1 — the variant loses its outer loop.** The lifted, partitioned architecture is a pure
feed-forward chain of internally-converged block solves: consistency of the lifted variable is
the optimiser's equality (constraint 93), feed-forward needs no convergence by construction,
and the outer predicate pass in A28's A1′ is a *verification receipt*, not architecture. The
receipt is expensive: **~38 % of the solve phase** (one sweep of the ~25-node loop set out of
~65 node calls per MDA evaluation, estimated on all three decks' unperturbed runs). The
architecture comparison must measure the architecture as designed, with correctness guaranteed
by instruments that are **not charged to the arm**:
- the equivalence gate exactly as A28 built it (`norm_objf` + post-solve feasibility audit
  against R, per deck, teeth shown);
- one exit audit **per optimisation at the accepted optimum** (a single further sweep,
  outside the cost accounting), replacing per-call verification.

**R1a — the 3.2 % must be explained first (open question, artifact-first).** A28's campaign is
itself the wholesale verification of the partition: over 67 completed A1′ runs, 88 930 MDA
calls, **95.1 % take exactly 2 outer passes** (solve, then a verify pass that finds nothing).
But **2 844 calls (3.198 %) needed a 3rd–7th pass** — the verify pass caught real movement —
every run has at least one such call, and a heavy tail of hostile starts has hundreds (858,
621, 452, 215, 202, 177, 124 in single runs). Two candidate mechanisms with opposite
consequences:
1. **slow intra-block modes** creeping past the inner step-size test → trust-mode merely
   delivers slightly less accuracy on those calls, priced by the audit; benign;
2. **state-dependent cross-block coupling** waking at states far from the harvest → trust-mode
   is structurally wrong on those calls.
**Localised from artifacts; mechanism narrowed to two candidates (orchestrator, 2026-09-03);
one confirming run pending.** The recurring drift is **contained to `st_regression`**: 2 802 of
54 480 A1′ calls (5.14 %) need a 3rd–7th outer pass there, against exactly **one call per run**
on each pulsed deck (22/14 080 and 20/20 370 — the cold first call, maximal staleness, benign).
The slow mode is the TF-coil chain: `superconducting_tfcoil.a_tf_plasma_case` (computed in `tfcoil/superconducting.py`
~line 1878; `st_regression` has `i_tf_sup = 1` — superconducting TF, corrected 2026-09-03) is the argmax exit residual on 22/28
ladder audits **in both arms**, decaying ~30× per rung — a property of the coupling structure,
not of blocking. The downstream cascade is ~147 fields across 17 modules; it is **transient**
(bit-exact 0 at every accepted optimum) and dormant at the harvest, which is why A2/A22
correctly measured zero cross-module movement there. **A first source scan eliminated the
obvious explanations**: the `physics ← pf_coil.p_pf_electric_supplies_mw` read is in
`outplas()` (output path, physics.py:2601 at `c0ae5b28`), `dr_fw_plasma_gap_*` is written by
`plasma_geometry` itself, and `b_plasma_*_toroidal` is physics-internal (though
physics.py:387/395 holds a one-sweep **stale read** of `b_plasma_inboard_toroidal` — an
intra-module lag the inner loop resolves). Two candidates remain: **(i)** a computational
cross-block read our grep missed — handed to `PROCESS_code_analysis`, whose pinned dependency
instrument can enumerate readsets authoritatively (see the outgoing report of 2026-09-03);
**(ii)** a **non-idempotent model** in the coils block — an internal solve whose output carries
its own state between executions, so the block re-emits above-τ dust at hostile states: a class
no DSM edge can represent. Consequences for R1: on the pulsed decks the evidence supports
one-pass trust-mode (staleness fires once, at the cold first call — "verify the first call,
trust thereafter" captures it); on `st_regression` the verify pass is NOT vacuous and the V2
options are keep-it, resolve mechanism (i)/(ii) first, or a declared audited accuracy
concession. Confirming run (blocked on the heavy slot): one instrumented `st_regression`
`start010` recording per-call, per-pass argmax components — and it must record **which deck
switches the moving chain needs**, because the sibling study's graph exports are built for the
large-tokamak config and `st_regression` differs from it on ten-plus switches (register V6) though NOT on the
TF family (`i_tf_sup = 1` in both), so branch-liveness must be checked switch by switch (DSM register V14
addendum; their D77/I-44).

## Design items carried from the V1 lessons

**R2 — no instrument cost charged to any arm.** The exit audit runs per-run, not per-call
(A28 §5.1 already moved it out of the run being costed); YSpec state copies and any probe
work are accounted outside the arm's cost or made identical across arms.

**R3 — the predicate asymmetry dissolves, and matched measured accuracy becomes the *only*
comparison basis.** A trust-mode variant has no outer τ at all — only inner tolerances — so
matched-tolerance comparison is not even definable. The exit-audit + lower-envelope machinery
(A26 fix 1, A28's `matched_accuracy.json`) is the entire basis; **declare the constructions in
advance**: all-settings and matched-count both computed, the bracket published, the headline
row rule fixed before any run (A30 checks (b)/(c)).

**R4 — factor identification designed in, not patched on** (A30 F2). The V1 arms never varied
the lift alone. V2's arm lattice should include at minimum: R, flat control (predicate-matched),
**flat + lift** (lift alone), partitioned + lift with outer loop (V1's A1′, as the bridge),
partitioned + lift trust-mode (R1). Hoist on/off stays a separable diagnostic. Any factor not
isolated is *declared* not isolated in the abstract.

**R5 — robustness at the deployment setting.** V1 costed the loose-inner (warm-start)
configurations on the ladder but ran the 25-start robustness campaign only at inner = 1e-6.
V2 pre-declares the deployment setting (chosen for a stated mechanism, before results) and
runs the full multi-start campaign there. Note the risk direction: a looser/absent outer test
consults the NaN-refusing predicate less often; refusals may convert to silent completions —
the gate and drop census must be sharp enough to see it.

**R6 — Phase A's role shrinks to a decomposition control.** The unlifted partitioned arm
*cannot* drop its outer loop — the burn-time feedback is live without the lift — so R1's
saving belongs to the **lift**, not the partition. V1's Phase A bracket (all-settings vs
matched-count) already says the partition alone is worth ≈ nothing resolvable; V2 keeps a
small Phase-A-shaped control to re-establish that, and the headline is lift + trust-mode
against the flat control.

**R7 — everything pre-declared** (the A26/A28/A30 lessons as one item): outcome rules per
deck, acceptance rule, accuracy statistic (with the p50-degeneracy check), envelope
constructions and headline-row rule, drop-census columns labelled by what they count, entry
census (I-12) beside every cost figure, provenance = one commit per campaign (protocol §15,
single entry point, `--verify` covering **every** published table — A29's finding).

**R8 — carry-overs otherwise unchanged:** frozen models and base commit; three decks (D17);
δ calibration (D15); isolation per run; counts-not-timings; §12 teeth on every gate; one
committed entry point from clean (§15).

## What this does and does not touch

- **Published V1 results are untouched.** Phase A's bracket and Phase B's per-deck verdicts
  measured predicate-bearing architectures, both arms carrying their receipts; they stand.
- The V2 headline question becomes: *what does the lifted, partitioned, trust-mode
  architecture cost or save against PROCESS's flat loop at matched measured accuracy, and
  what does it do to robustness?* — with the ~38 % receipt no longer charged to the variant.

## R9 — the V2 comparison design (user question, 2026-09-03): one overarching MDA vs feed-forward block MDAs

**The structural fact:** the feed-forward arm has **no dial controlling final accuracy** — delivered
accuracy is what one chain pass produces. Matched tolerance is undefined, not merely unfair; the
comparison basis is matched **measured** accuracy, full stop.

**Tolerances:** one knob per arm, same ladder grid — flat arm's τ vs **one shared inner τ across
all blocks**. Per-block tolerances only as a separately-labelled tuning study. Equal rung counts by
construction (kills the envelope sampling bias at the source). Exit audit (uncharged, identical
instrument) measures accuracy per rung; cost read off cost-vs-achieved curves; **no extrapolation**
— an accuracy one arm cannot reach is a reported capability difference; the headline read at an
externally anchored accuracy (what stock PROCESS delivers at its shipped predicate).

**Arm lattice:** R (anchor) → A0 (flat, matched predicate: the stopping-rule step) → B1 (blocked
with outer loop: the partitioning step, lift inseparable on pulsed decks and declared so) → B2
(feed-forward, no outer loop: **the trust step, B1→B2 is the headline**). Grouping and order
identical across B1/B2. B2's correctness lives outside the run: equivalence gate with teeth +
per-run exit audit; on `st_regression` B2's validity is conditional on A31's verdict.

**Performance:** net model evaluations in the solve phase at matched measured accuracy, per deck,
never pooled; cost decomposed into **optimiser iterations × per-iteration loop work** with the
paired iteration ratio reported (a ratio ≠ 1.000 flags search-path contamination — the
`low_aspect_ratio_DEMO` lesson); paired multi-start robustness with drop census at matched
measured accuracy; audits at a pre-declared sample of interior calls (first + accepted), since B2's
risk is interior accuracy feeding gradients; timings as context only; every rule pre-declared.

## R10 — Phase A V2 (MDA solve only, no optimiser): the simplified two-arm design (user, 2026-09-03)

**Correction to R9's accuracy story, Phase A scope:** the measured bit-exact overshoot belongs to
the **nested** arm and is produced by its verification pass (a full extra pass of block solves
polishing already-tiny dust to the exact fixed point). A **pure feed-forward** chain has no second
visit: each block's dust freezes at its own ~τ exit, and the audit sees ~ρᵢ·δᵢ per block — the
same order as the flat arm's exit. **Expectation, declared in advance: flat and feed-forward at
one shared τ deliver similar, τ-grade accuracy.** Consequence: matched τ is an acceptable setting
for THIS pair, with the (uncharged) exit audit as the per-point check; the envelope machinery is
the fallback only if the audit refutes the expectation.

**Arms: two.** Flat (one loop, predicate on the full state at τ) vs feed-forward blocks (three
chained block MDAs, one shared inner τ, no outer loop). **No nested arm**: at Phase A's evaluation
states the drift is measured dormant (A22: zero above-τ movement on pass ≥ 2 at every harvested
point) and the audit covers exceptions for free — an outer loop would be pure receipt. The nested
arm's remaining role is Phase-B-only (hostile states), parked.

**Performance: per-node evaluation counts, with weighting-invariance bounds.** Publish n_i per
node per arm; for any nonnegative per-node cost weighting the weighted ratio lies in
[min_i n_B/n_F, max_i n_B/n_F] — so the count table plus that min/max pair bounds the architecture
effect under EVERY per-node cost model, timing-free. A tight bracket proves the unweighted count
representative; a wide one is reported with the extremal nodes named. Timings at most one
contextual weighting inside the bracket. Evaluation points: the harvested design points, per deck,
never pooled; audit at every point; drop census; all rules pre-declared.

## R10a — correction to R10 (user pushback, 2026-09-03): feed-forward is only valid where k = 0

**R10's "no nested arm, all decks" was wrong, and the user caught it.** Phase A's nested MDA was
not defensive structure: without the lift — which requires an optimiser to own the lifted variable,
and Phase A has none — **the outer loop is what converges the burn-time coupling** (`Pulse` writes
late, M1 reads early). A22's numbers say so directly: pass-≥2 movement at **149/149 and 297/297**
harvested points on the pulsed decks, all of it the burn time. (R10's "drift dormant at harvested
states" is true only of `st_regression`; the orchestrator conflated the two phenomena.)

Corrected Phase A V2 scope:
- **`st_regression` (k = 0): the clean comparison.** Flat vs pure feed-forward, one shared τ,
  **matched-tolerance comparison with a pre-declared a-posteriori similarity check on the audit**
  (criterion fixed before the run — e.g. both audit residuals below the anchor accuracy or within
  a stated factor). Envelope machinery is the fallback only if the audit refutes similarity. This
  is the R3 simplification, adopted with its scope stated.
- **Pulsed decks (k = 1): pure feed-forward is structurally invalid without the lift** — no
  setting converges the burn time. Either compare flat vs **nested** there (the V1 question;
  note its final pass still polishes, so partial overshoot and the accuracy-matching concern
  return), or **defer those decks' feed-forward question to the optimiser round**, where the lift
  exists. Deferral is the cleaner headline.

Standing note for the orchestrator: this is the second design simplification the user had to
push back on (the first: trust-mode "delete the pass" before the 3.2 % was explained). Check
proposed simplifications against the recorded measurements (A22's censuses, the V-register)
before adopting them into the plan.

## R11 — the A→B decomposition argument (user, 2026-09-03), with its transfer conditions

**The V2 argument structure:** total cost = (optimiser iterations × calls per iteration) ×
(per-call MDA cost). Phase A measures the per-call factor **with the coupling pinned — which IS
the lifted variant's per-call structure**, since the optimiser holds the lifted variable fixed
within any call (A22's pin arm is the instrument). Phase B then verifies only the multiplier:
iterations ≈ unchanged (A28 measured paired ratios of exactly 1.000/1.000/1.000 on two decks — the
check can pass cleanly, and fails loudly where it fails), robustness not degraded, plus the
deterministic +1/n gradient arithmetic. If the multiplier holds, Phase A's per-call saving
transfers by multiplication; if it does not (the `low_aspect_ratio_DEMO` case), the transfer is
declared broken and only end-to-end numbers are quoted for that deck.

**Transfer conditions, each with its precedent:**
1. **Call-mix weighting** — §4.1a's failure: the optimiser's calls are ~2n warm FD evaluations per
   iteration (1–2 sweeps each); Phase A must weight per-call cost by that mix (replay recorded
   optimiser state sequences), not by cold entries, or the fractional saving is inflated.
2. **Pin-value insensitivity** — pin at ±δ around the consistent value and show the per-call cost
   does not care (the lift mid-optimisation pins at inconsistent values).
3. **The multiplier check is Phase B's whole job** — iterations and robustness at matched measured
   accuracy; nothing else needs re-measuring there if 1–2 hold.

**Phase A's role under this logic:** mechanism and attribution (per-node counts, weighting bounds,
warmth scaling, the predicted Phase B number), cheap and optimiser-noise-free; Phase B confirms
the multiplier and the prediction. A confirming Phase B is deliberately small.
