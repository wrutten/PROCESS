# V3 improvement list — method changes for a third experiment revision

> **Document status** — **CURRENT · PLANNING INPUT.** Opened 2026-09-04 from the user's
> review of [`V2_EXPERIMENT_REPORT.md`](../reports/V2_EXPERIMENT_REPORT.md), folding in the
> methodology findings of A35 and the parallel assessment session. This is a list of
> candidate design changes, not a plan: nothing here is decided, and a V3 experiment plan
> would restate its selections with pre-declared acceptance rules. Items marked **[data
> gap]** name instrumentation V2 lacked; the rest are design/analysis changes on data that
> already exists.

## Acceptance-rule fixes

1. **Same-optimum yardstick floor** *(the §5.2 artifact — user, 2026-09-04)*. V2's declared
   yardstick (the measured R→B0 paired |Δ norm_objf| spread) landed at machine noise
   (3.3e-15 on nof), so any nonzero architecture footprint formally failed while agreeing to
   1e-10. V3 declares, before the campaign, an accuracy-equivalence **floor** and accepts at
   `spread ≤ max(F × yardstick, floor)` — candidate floor constructions: the objective dust
   of re-running R itself from identical starts (measured), or a τ-propagated bound through
   the objective's scaling. The yardstick construction itself is kept (it is the right
   *relative* object); only its degenerate-zero regime is repaired.
2. **Iteration pairing and taxonomy declared, not accidental.** V2's tally dropped
   iteration pairs silently where `n_solver_iterations` was unrecorded — which happened to
   equal the converged-only construction, and pooled `ifail = 5` completions under "ok". V3
   declares: pairing on both-converged; the A30 taxonomy split (`crashed / refused /
   unconverged / infeasible-at-audit`) computed in the tally itself with denominators, per
   arm per deck. **[data gap]** record `n_solver_iterations` (and ladder stage) at
   *unconverged* exits too — V2 stores 0/absent there.
3. **Multi-attractor decks handled by declaration** *(st's 0.22 tail)*. Where a deck
   supports multiple accepted optima (st: ≥ 4 observed, §5.2), per-pair |Δ| statistics mix
   within-attractor agreement with between-attractor hops. V3 declares up front: cluster
   accepted optima by `norm_objf`; report (a) within-attractor agreement and (b) the hop
   *rate* per arm pair, with the R→B0 hop rate as the comparator. A hop is then a counted
   event, not an outlier corrupting a spread.

## Phase A similarity — regime and accounting

4. **Audit restricted to the in-loop writeset** *(A35 §6.2, confirmed by the 75/75 argmax
   census)*. V2's whole-state audit charges A1 for δ-perturbed components of post-solve
   nodes it deliberately never executes — the dominant term of its F-failure. V3's
   similarity statistic excludes post-solve-owned components (published beside the
   whole-state audit, both declared); expected residual: the carrier-class terms (~1e5 ×
   A0's level at δ = 0.10 — pre-declared, from the parallel assessment).
5. **Carrier-class controls** *(A35; known-cut set)*. Either exclude the known-cut
   constants (`build.dr_fw_inboard/outboard`, `pf_power.vpfskv`) from the perturbation
   stream, or run a control arm with them held at their run-constants — pre-declared
   expected outcome: the similarity residual drops to inner-τ dust or a **new carrier is
   named**. This is the cheap falsifiable follow-up A35's coefficient closure licenses.
   (A source fix — seeding the pair at initialisation — is a separate, D11-gated user
   decision, with its own attainable-gates list from the 2026-09-04 assessment; a fix would
   make this control moot.)
6. **Perturbation-regime alignment disclosed and optionally matched.** V2's multiplicative
   δ-stream displaces run-constants and post-solve outputs — state no optimiser-driven call
   displaces after call 1, making Phase A's regime deliberately more hostile than B3's
   in-optimisation regime. V3 either (a) keeps the hostile regime and carries V2's
   disclosure, or (b) adds a matched-regime variant (perturb only optimiser-reachable
   state), both published. **[data gap — closed cheaply]** record each run's entry
   displacement of the known-cut constants so carrier terms are computable without
   re-tracing.

## Robustness and hard decks

7. **Failure forensics at every non-converged exit.** **[data gap]** V2 records only
   `ifail`, `sqsumsq` and call counts at unconverged exits — enough to show lad's aborts
   are early and paired (538–554 calls, `sqsumsq` 0.15–0.64), not enough to say *which*
   constraints are violated or where the ladder gave up. V3 records the constraint-residual
   vector, active set and ladder stage at every unconverged/crashed exit.
8. **Robustness-powered design for arm attribution.** V2's N = 25 cannot resolve 1–3-seed
   crash-count differences (lad: 2 → 4 → 5 across arms). V3 either sizes N for a declared
   minimal detectable robustness effect, or declares robustness out of scope per deck; the
   V2 hint is recorded, neither claimed nor dismissed.
9. **Per-deck perturbation amplitude.** lad's feasible basin is narrow relative to
   δ = 0.10 (13/25 starts unrecoverable in every arm — §5.1). V3 decides, per deck and
   before the campaign: keep the shared δ (comparability across decks) or declare
   basin-sized per-deck amplitudes (usable-pair yield); the V2 result quantifies the
   trade-off.

## Mechanism instrumentation

10. **Gradient-quality diagnostics for the iteration multipliers.** The two unexplained
    iteration effects — lad's lift *gain* (B0→B1 = 0.83) and lad's trust *loss*
    (B2→B3 = 1.33) — both plausibly live in the finite-difference gradients. **[data
    gap]** V3 instruments FD-stencil audits (per-gradient-point exit residuals, stencil
    condition) so iteration multipliers can be attributed rather than only localised.
11. **Per-block wall-clock context timers.** **[data gap]** V2 has per-block call counts
    but no per-block timing, so §5.5's structure table has no wall-clock counterpart.
    V3 adds per-block timers inside `module_solve` — context only, never acceptance
    (I-10 stands).
12. **Per-block cost split as a tally output.** V2 computed the §5.5 per-block table at
    analysis time from per-run censuses; V3 makes it a first-class tally artifact
    (the data already exists per run — no new instrumentation, just tally scope).

## Reporting admin

13. **Table captions** *(adopted immediately as protocol §16, 2026-09-04)*: every table
    carries a concise caption stating units, entry semantics, the population summarised and
    the construction that produced it. Applied retroactively to the V2 report.
