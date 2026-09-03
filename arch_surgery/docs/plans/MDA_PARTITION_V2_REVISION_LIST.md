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
**Identified from artifacts (orchestrator, 2026-09-03), one confirming run pending.** The
heavy tail is entirely `st_regression`, and the mechanism is (2) in a dormant form: a genuine
**M2 → M1 back edge** — `physics` reads TF-coil-derived fields (`b_plasma_*_toroidal` via
`tfcoil.ripple_b_tf_plasma_edge`, `build.r_tf_outboard_mid`) but is scheduled first, so at
states far from self-consistency its pass-1 output is computed against stale coil values and
pass 2 moves > τ, cascading through the coils block (`superconducting_tfcoil.a_tf_plasma_case`
is the argmax slow mode, 22/28 ladder audits, in BOTH arms) into the ~100-field blanket/fwbs
geometry census. At harvested states the edge carries nothing — which is why A2/A22 correctly
measured zero cross-module movement there ("k = 1, confirmed at the harvest" meeting its
predicted failure mode). The drift is transient (bit-exact 0 at every accepted optimum) and
the outer loop resolves it in 1–5 extra passes on 3.2 % of calls. Consequences for R1:
trust-mode's one-pass design is unsafe where this edge is live; the V2 options are (a) keep
the verify pass on decks where it fires — on `st_regression` it is NOT vacuous — (b) treat
the TF-field coupling as a second lift candidate (k = 2), or (c) price the staleness as a
declared accuracy concession, audited per run. Confirming run (blocked on the heavy slot,
A29): one instrumented `st_regression` `start010` recording per-call, per-pass argmax
components and pass counts, to tie the 3+-pass calls to this edge beyond aggregates.

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
