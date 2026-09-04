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
   *Status note (relayed 2026-09-04 from session process-surgery-bf; user decisions made
   there, to be confirmed on execution):* elevated to **the load-bearing harness fix**,
   separate from any intervention change — the same campaign design re-run unchanged with
   the corrected audit (a re-run is required: V2's Phase A records carry only the audit
   brief, not the per-component residual vector or an exit snapshot, so the restricted
   statistic cannot be recomputed offline). Expected outcome, pre-declared there: F still
   fails, on the carrier term alone.
5. **Carrier-class controls** *(A35; known-cut set)*. Either exclude the known-cut
   constants (`build.dr_fw_inboard/outboard`, `pf_power.vpfskv`) from the perturbation
   stream, or run a control arm with them held at their run-constants — pre-declared
   expected outcome: the similarity residual drops to inner-τ dust or a **new carrier is
   named**. This is the cheap falsifiable follow-up A35's coefficient closure licenses.
   (A source fix — seeding the pair at initialisation — is a separate, D11-gated user
   decision, with its own attainable-gates list from the 2026-09-04 assessment; a fix would
   make this control moot.)
   *Status note (relayed 2026-09-04 from session process-surgery-bf):* seed approval is
   **still open with the user**; if approved, its counterfactual runs on the
   corrected-audit campaign of item 4, in that order. The user has also agreed there to a
   **"dead needs two qualifiers" register-convention amendment** (a liveness verdict must
   state both value-liveness and displacement-liveness, per V15) — not yet written into
   `DSM_VALIDATION.md`'s conventions; whichever session executes it should confirm with
   the user first.
6. **Perturbation-regime alignment disclosed and optionally matched.** V2's multiplicative
   δ-stream displaces run-constants and post-solve outputs — state no optimiser-driven call
   displaces after call 1, making Phase A's regime deliberately more hostile than B3's
   in-optimisation regime. V3 either (a) keeps the hostile regime and carries V2's
   disclosure, or (b) adds a matched-regime variant (perturb only optimiser-reachable
   state), both published. **[data gap — closed cheaply]** record each run's entry
   displacement of the known-cut constants so carrier terms are computable without
   re-tracing.
   *Status note (relayed 2026-09-04 from session process-surgery-bf; user decisions made
   there):* **option (a) is decided** — no harvested-entry redesign of Phase A, no
   cold-start row for both arms, the synthetic warm δ-stream stays (ground: closely
   related to Phase B). The disclosure carries; option (b) is off the table.

## Robustness and hard decks

7. **Failure forensics at every non-converged exit.** **[data gap]** V2 records only
   `ifail`, `sqsumsq` and call counts at unconverged exits — enough to show lad's aborts
   are early and paired (538–554 calls, `sqsumsq` 0.15–0.64), not enough to say *which*
   constraints are violated or where the ladder gave up. V3 records the constraint-residual
   vector, active set and ladder stage at every unconverged/crashed exit.
8. **[DEFERRED — user decision 2026-09-04: "I want to defer the robustness test. I'm not
   sure I need/want to make claims about it."]** The powered robustness campaign (the
   two-tier B0-vs-B3 design and its N sizing below) is **not** part of v3 unless the user
   re-opens it; the design arithmetic is kept here so re-opening costs nothing. What
   survives independently of the deferral: the **reporting statistic** (deck-invalid-seed
   separation, next paragraph) applies to whatever taxonomy v3 publishes, and V2's stance
   stands — the 1–3-seed hint is recorded, neither claimed nor dismissed.
   **Robustness-powered design for arm attribution, with seed-driven failures separated
   out** *(user directive, 2026-09-04: "robustness comparison statistics should separate
   out these seed-driven failures. If all arms fail, it should be excluded from the failure
   rates per arm, as we presume the models are simply invalid for the seed")*. V3's
   declared robustness statistic: a seed that fails in **every** arm (crash or unconverged)
   is a **deck-invalid seed** — excluded from the per-arm failure rates and reported as its
   own count; per-arm rates are computed over the remaining seeds only, so they carry
   arm-attributable failures alone. Under this statistic V2's lad numbers become: 12
   deck-invalid seeds (9 unconverged + crashes common to all arms), per-arm attributable
   failures 0 (R) … 1–3 (B0…B3) of the ~13 attributable seeds — which is the effect N must
   be sized to resolve. V3 either sizes N for a declared minimal detectable arm effect or
   declares robustness out of scope per deck.
   **Design recommendation (orchestrator, 2026-09-04, from the V2 timing/taxonomy data;
   scripted with v3's design work if promoted into a plan):** state the robustness claim
   as an **equivalence bound** ("arm X adds ≤ E attributable failures vs B0, 95 %"), not
   effect detection — then N follows from E by the discordant-pair arithmetic (≈ 3/N upper
   bound at zero discordant events; ≈ 8/p usable seeds to *detect* a discordance rate p).
   N = 50 full-lattice resolves only ≥ ~15 % effects (screening grade); the V2 hint
   (1–3 of ~13 usable lad seeds) needs ~100–150 *usable* seeds. Efficient shape:
   **two tiers** — the 5-arm lattice stays at N = 25 for cost/optimum; robustness runs the
   headline pair **B0 vs B3 only**, N_drawn ≈ 300 on lad (≈ 140 usable after deck-invalid
   exclusion → ~2 % bound) and ≈ 150 on nof/st — roughly 4–5 h at W = 3 (failed runs abort
   early and cost little), one overnight with margin. Percent-level bounds would need
   N ~ 10³ (the "orders of magnitude" regime); the question actually on the table (a
   5–10 % effect) does not.
   **Measured input to this design:** reconstructing the seed streams shows lad's
   all-arms failures are NOT the large-|u| draws (converged and failing seeds' RMS|u|
   distributions overlap almost completely; the smallest draw fails, larger ones
   converge) — failure is direction-dominated. Consequently raw N is not the only lever:
   item 7's exit forensics may identify the killing constraint family and let v3 raise
   usable-seed yield by construction instead of brute force.
9. **Per-deck perturbation amplitude, and interior-vs-shell sampling declared.** lad's
   feasible basin is narrow relative to δ = 0.10 (13/25 starts unrecoverable in every arm —
   §5.1). V3 decides, per deck and before the campaign: keep the shared δ (comparability)
   or declare basin-sized per-deck amplitudes (usable-pair yield). Related declaration
   (user question, 2026-09-04): the V2 stream samples the **interior** of the δ-ball
   (per-component u uniform in [−1, 1), so per-seed displacement varies); the alternative
   — fixed |u| = 1, sign-only random — samples the **shell**, which is strictly stronger
   than every current draw (max observed RMS|u| = 0.66 of the shell's 1.0) and would fail
   *more* often on narrow-basin decks, not less. The measured null above (failures are
   direction-, not magnitude-driven) says the interior/shell choice is second-order for
   failure statistics; either is fine **declared**, shell only in combination with a
   smaller δ.

## Mechanism instrumentation

10. **Gradient-quality diagnostics for the iteration multipliers.** The two unexplained
    iteration effects — lad's lift *gain* (B0→B1 = 0.83) and lad's trust *loss*
    (B2→B3 = 1.33) — both plausibly live in the finite-difference gradients. **[data
    gap]** V3 instruments FD-stencil audits (per-gradient-point exit residuals, stencil
    condition) so iteration multipliers can be attributed rather than only localised.
11. **Per-block wall-clock context, two constructions** *(user, 2026-09-04)*. **[data
    gap]** V2 has per-block call counts but no per-block timing, so §5.5's structure table
    has no wall-clock counterpart. Two routes, both context-only (I-10 stands):
    (a) **reconstruction** — measure per-node unit wall-clock once per deck (one profiled
    run), then per-block time ≈ Σ_node (recorded calls × unit time). Cheap, applies
    retroactively to V2's recorded counts; caveats to publish with it: unit times assumed
    state-independent (A19 §5.2 licenses this approximately), and driver overhead
    (module_solve machinery, predicate evaluations) is outside node time — the st B3
    wall-vs-counts gap shows that overhead is not negligible, so the reconstruction
    estimates *model* time, not run time. (b) **direct per-block timers** inside
    `module_solve` — captures overhead too, needs instrumentation. V3 does (a) at minimum;
    (b) if the overhead split itself becomes a question.
12. **Per-block cost split as a tally output.** V2 computed the §5.5 per-block table at
    analysis time from per-run censuses; V3 makes it a first-class tally artifact
    (the data already exists per run — no new instrumentation, just tally scope).

## Reporting admin

13. **Table captions** *(adopted immediately as protocol §16, 2026-09-04)*: every table
    carries a concise caption stating units, entry semantics, the population summarised and
    the construction that produced it. Applied retroactively to the V2 report.
