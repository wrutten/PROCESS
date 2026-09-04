# MDA Partitioning Experiment V3 — Experiment Plan

> **Document status** — **APPROVED FOR EXECUTION — 2026-09-04, by the user.**
> The user approved this plan and flipped `v3_config.EXECUTION_APPROVED` to `True` in their
> own commit `a164c6cd` ("V3 experiment approved", 2026-09-04 15:23). This header is the
> paired record of that approval, written by the orchestrating session immediately after and
> transcribing the user's decision — it does not itself grant anything. Campaign task A42
> (v3-campaign) is unblocked.
>
> **Amendments made before execution, all dated in place:** §4.2 check 1's per-pair relative
> statistic and the nearest-rank median construction; §4.2 check 2's summed-iteration
> publication and the both-ok/both-converged pairing rule; §5's transfer amendment (I-17 —
> the transfer is an upper bound, not a prediction, with the measured per-deck
> over-prediction published and the `sweeps_per_eval` hypothesis pre-declared). Every later
> change is a dated amendment, never a silent edit.
>
> Written 2026-09-04 by task A39 (v3-plan) from
> [`../docs/plans/V3_DEVELOPMENT_PLAN.md`](../docs/plans/V3_DEVELOPMENT_PLAN.md) (the
> development plan, §0 fully resolved 2026-09-04 — every selection below is either a user
> decision recorded there or an orchestrator proposal its assessment endorsed), on the
> structural template of
> [`../MDA_partitioning_experiment_v2/EXPERIMENT_PLAN.md`](../MDA_partitioning_experiment_v2/EXPERIMENT_PLAN.md).
> **V2's plan and directory are frozen as the record of what ran; nothing in them is edited
> by V3.** Base commit `c0ae5b28` (D2) throughout; physics untouched (D5/D11 — V3 contains
> **no** `process/models/` change). Every later change to this document is a dated
> amendment, never a silent edit.

## 1. Objective and claim structure

**Goal: the existence proof of V2, completed.** V2 established on `large_tokamak_nof` that
optimisation architecture alone — every physics and engineering model byte-identical to
upstream at `c0ae5b28` — changes the cost of solving PROCESS measurably. V3 re-runs the
same design with **one element added to the intervention** and **the measurement apparatus
corrected where V2's own report found it defective**: the accuracy audit restricted to what
the solve phase actually writes (V2's whole-state audit charged the block arm for outputs of
nodes it deliberately never executes — 75/75 of its audit maxima), the same-optimum
yardstick given a floor (V2's yardstick landed at machine noise, so the check could not pass
for any arm that changed anything), and every tally construction declared before the first
run (V2's tally had two undeclared constructions its independent recomputation had to
reverse-engineer).

**The intervention (one unit, restated from the development plan §2).** As V2: partition
the overarching MDA into three block MDAs run in feed-forward order; lift the single
cross-block feedback (the burn-time coupling; k = 1 on the pulsed decks, k = 0 on
`st_regression`) to the optimiser with constraint 93; feed-forward nodes execute once per
call; post-solve nodes execute once per run. V3 adds one element to the same unit:

> **The prime.** The first-wall thicknesses `build.dr_fw_inboard` and `build.dr_fw_outboard`
> are a run-constant of two pure deck inputs, computed by `FirstWall` (block M3,
> `fw.py:347-352` at `c0ae5b28`) and read by `Build` (block M2, `build.py:826-842`,
> `:1862-1889`, `:1940-1947`), which the schedule runs first. Under an iterating driver the
> lag costs at most one sweep; under a one-pass schedule it transmits exactly the entry
> displacement of the pair, once (A35, register V15). V3 primes the pair at the head of
> every sweep of the block arms — the driver executes the existing model method
> `fw.set_fw_geometry()` — so `Build` reads this pass's value. It is a driver choice about
> *when* an existing model method runs — the same family as the `build_after_physics`
> reorder but finer-grained (**a method, not a node**); no file under `process/models/`
> changes.
>
> This is **not an ordering fix at the collapsed-model level** (user, 2026-09-04): the
> `FirstWall` *node* stays exactly where the schedule has it. Moving the node wholly ahead
> of `Build` would carry its physics-dependent reads upstream of their writers and create
> new backward edges; what moves is the one run-constant method, the only part of
> `FirstWall` whose inputs are pure deck inputs.

**Prime accounting (declared).** The prime is env-switched (`PROCESS_ARCH_PRIME`; an
unrecognised value raises, never defaults; unset ⇒ byte-identical behaviour, gate G1). It
is **not** routed through `Caller._node`, so it adds no counted node call and every count
comparison stays commensurable with V2. It is **stamped, not counted**: the runner records
`n_prime_calls` in every run's metrics and the tally publishes it as a footnote beside the
node-call tables, **never pooled into them** (trap T11 — no silent work). Nothing is
removed from `FirstWall`, whose own execution and cost are unchanged — the prime
*duplicates* a run-constant of two floating-point operations at the sweep head — so
neglecting it in the cost ratios is a disclosed, bounded statement, not an assumption.
**Coverage requirement** (verified by A40, task T2): the block schedule's
`Caller._sweep_block` runs a block by calling `_call_models_once` with the node filter set,
so the prime site is on every block sweep's path as well as the flat loop's; A40 confirms
it by counting the prime's executions in a traced verified chain, which must equal that
run's block-sweep count. The prime's two inputs (`fwbs.radius_fw_channel`,
`fwbs.dr_fw_wall`) are loader-written and outside the coupling-state spec, so the
perturbation stream never touches them. The prime also runs in the output-phase and audit
callers (harmless, idempotent), and cures `FirstWall`'s own stale self-read of the pair
(`fw.py:54-55` before `:110`).

**What the intervention may then claim, pre-declared.** A35's census gives the
backward-edge set the trust schedule cuts as exactly the pair on `st_regression`, and on
the pulsed decks the pair plus `pf_power.vpfskv` (a literal whose only computational reader
feeds constraint 41 — inactive on all three decks per A26) plus the burn time (lifted).
With the prime, **no cut edge on the three decks carries a displaced value into a one-pass
exit**; gate G3 tests exactly this and names any residual mover.

**Claim decomposition (as V2).** Total cost = optimiser iterations × calls per iteration ×
per-call MDA cost. Phase A (no optimiser) measures the per-call factor — the best case /
upper bound. Phase B (full optimisation) is the headline: the iteration multiplier,
robustness, and the end-to-end number under the real call mix. If Phase B's realised saving
lands below Phase A's bound, the shrunken number is the honest result; no correction is
applied in either direction.

**What V3 is not** (development plan, user decisions 2026-09-04): not a harvested-entry
redesign of Phase A; not a cold-start comparison row; not a powered robustness campaign
(deferred — **no robustness claim is made in V3**); not gradient-quality instrumentation
inside the campaign (lad's trust-step iteration inflation stays **"mechanism unknown"** as
the declared baseline; it is investigated after the campaign, and only if it persists —
the contingent post-campaign task T5).

## 2. Experimental variables and controls

- **Independent variable:** the driver architecture only — `process/core/caller.py`,
  `process/core/solver/`. The prime is a driver choice about when an existing model method
  runs; **no `process/models/` file changes in V3.** Base commit `c0ae5b28` is the
  coordinate system.
- **Scenarios (D17):** `large_tokamak_nof`, `low_aspect_ratio_DEMO` (pulsed, k = 1),
  `st_regression` (steady-state, k = 0 — the clean partition-only case). Deck order in
  every table of this plan and its report: **nof / lad / st.**
- **Spec generation:** a26-mode ystate artifacts everywhere, as V2 (A32's precondition,
  closed).
- **Isolation:** every PROCESS run is a fresh subprocess in its own working directory,
  exact tree asserted in-process (traps T6/T10); first run discarded for any timing
  context (JIT).
- **Execution and parallelism:** a fixed worker pool of W = 3 concurrent runs
  (memory-bound). Every acceptance quantity is a count or bit-comparison and is
  concurrency-invariant; the contextual timing block is serial, after the campaign. The
  job list is deterministic (deck × arm × start), jobs are never retried — a crashed run
  is a taxonomy row, not a rerun — and the tally reads only the on-disk records.

*Caption: the declared numeric settings, one row per knob: symbol, value, what it
controls, and where it was fixed. All dimensionless. None may change after approval except
by dated amendment.*

| setting | value | controls | provenance |
|---|---|---|---|
| N | **25** starts per deck per arm, both phases | sample size | O2 resolved 2026-09-04 (user: no lad extension now); V2 Appendix B's dated-amendment clause for a later extension stands |
| δ | **0.10** | perturbation amplitude, one shared stream, seed-paired across arms | D15 calibration; item 9 of the improvement list **not adopted** (shared δ keeps decks comparable; the measured null says amplitude is not the failure lever) |
| τ | **1e-6** | convergence tolerance, same in every arm | V2 |
| F | **10** | similarity factor (Phase A) and same-optimum factor (Phase B), at median and p90 | V2 Appendix B item 2 |
| floor | **1e-6 relative on `norm_objf`** | the same-optimum yardstick floor (§4 check 1) | O3 resolved 2026-09-04, option A — the D6/A25 correctness tolerance, whose provenance is PROCESS's own `check_agreement` rtol, not a choice made here |
| iteration bound | median paired ratio **≤ 1.05**, median only | §4 check 2 | V2 Appendix B item 3 (extremes published, never judged; per-start counts are dust-sensitive by ±80 %) |
| median construction | **nearest-rank, upper-middle** — the element at index n//2 (0-based) of the sorted values — for **every** Phase B check | §4.2's medians (checks 1 and 2) | declared here because V2's lad B2→B3 iteration cell is construction-dependent: over the same 10 pairs the mean-of-middles median reads 1.33 and the nearest-rank reads 1.40 — the only cell where the two disagree (V2 report §5.3, dated note; trunk commit `0a8f5af2`). Matches the nearest-rank p90 convention already in use |
| W | **3** | worker pool | V2 |

## 3. Phase A — per-call MDA cost (no optimiser)

### 3.1 Arms: three

*Caption: the Phase A arm lattice; one row per arm: its architecture and the role it plays
in the comparison. All arms run the same seed-paired entries (§3.2).*

| arm | architecture | role |
|---|---|---|
| **A0** | flat coupling-state MDA at τ; post-solve nodes inside its loop (the flat architecture as shipped) | control, as V2 |
| **A1u** | V2's A1 exactly: resequenced blocks, trust mode, post-solve exclusion, lift + pin on the pulsed decks, **no prime** | the corrected-audit re-run of V2 and **the prime's counterfactual** |
| **A1** | A1u plus the prime | the V3 intervention's per-call structure |

**Attribution (declared).** A0→A1 measures the intervention as one unit; A1u→A1 isolates
the prime on identical entries. Only `st_regression` (k = 0, nothing pinned) separates the
partition-and-hoist effect from the coupling term; no per-factor claim is made from the
pulsed decks' Phase A numbers.

### 3.2 Entry states — the V2 regime, unchanged (user decision), with its disclosure

Per deck, the **reference** is the converged flat state at the deck point, obtained by one
A0-arm single evaluation from the cold deck entry; its cost is the **once-per-run
cold-start term**, reported beside, never mixed into the per-call statistics. Campaign
entries are multiplicative ±δ perturbations of that snapshot, seeds 1–25, seed-paired
(bit-identical entry states across all three arms, verified per deck), evaluated by one
`call_models` under each arm. On the pulsed decks A1u and A1 run with the burn-time
coupling **pinned**, the pin value being the perturbed burn-time component from the same
stream (the ±δ scan is the pin-value insensitivity check, as V2).

The regime disclosure from the V2 experiment report §7 carries **verbatim**:

> Phase A's multiplicative δ-stream displaces two classes of state that **no
> optimiser-driven call displaces after call 1** — run-constants (the `dr_fw` pair;
> `vpfskv`) and post-solve-owned outputs — so the warm δ-regime is deliberately more
> hostile than any state B3 visits inside an optimisation, and the 75/75 census and the
> carrier term are the two symptoms of exactly that mismatch.

This regime is retained deliberately (user decision, development plan): it is the harder
test, and A1u→A1 under it is exactly the prime's counterfactual measurement.

### 3.3 The A38-reuse clause

Arm A1u is **already measured**: task A38 (audit-rerun, merged 2026-09-04, `e9e7e965`) ran
exactly this arm under the corrected audit, campaign executed at commit `9fcedc92` on the
`a4446bed` mint lineage, with 150/150 seed runs reproducing V2's records bit for bit.
**Reuse rule, pre-declared:** if gate G1 holds at the V3 driver commit (prime unset ⇒
byte-identical behaviour, MFILE hex floats, three decks), A38's A1u records are reused as
V3's A1u arm; otherwise the arm is re-run at the V3 driver commit. **The V3 report states
which path was taken.**

A38's measured baseline, which the prime must close (from
[`../docs/reports/deprecated/A38_audit_rerun.md`](../docs/reports/deprecated/A38_audit_rerun.md);
archived at merge per trap T3 — the authoritative record of a merged task):

*Caption: per deck (nof / lad / st), the median over 25 paired-ok seeds of each arm's
audited maximum scaled residual (dimensionless, a26 ruler), restricted to components not
owned by the deck's post-solve node set; and the composition of the restricted argmax over
the 25 A1u runs. A0 = flat control, A1u = the prime-free block arm.*

| deck | A0 restricted median | A1u restricted median | restricted argmax composition (of 25) |
|---|---|---|---|
| `large_tokamak_nof` | 5.0e-10 | **6.4e-4** | 25/25 are A35's two closed linear images of the `dr_fw` pair |
| `low_aspect_ratio_DEMO` | 0 (25 exact zeros) | **9.8e-4** | pair images present and coefficient-exact 25/25, but the argmax in **21/25 is `tfcoil.m_tf_coil_superconductor` — not one linear image of the pair** (fit residual median 0.067, max 0.92): the one open term, owned by gate G3c |
| `st_regression` | 5.4e-9 | **1.15e-3** | 25/25 linear images of the pair (17 A35's image; 8 `blanket.vol_shld_inboard` at measured gain 47.0) |

### 3.4 Checks, each with its acceptance rule pre-declared

1. **Similarity, corrected (the headline Phase A check).** Per deck, the audited
   max-scaled-residual distributions over components **not owned by the deck's post-solve
   node set** (membership derived nodes → write census → spec keys, A38's construction —
   never a prefix rule), for arm pairs A0/A1u and A0/A1. **Acceptance: within F = 10 at
   BOTH median and p90.** The whole-state audit is published beside it (both statistics,
   every run). A deck where the audit reads exactly 0 for every arm counts as trivially
   similar and the report says so (V2 Appendix B item 2's clause).
   **Pre-declared expectations:** A0/A1u **fails** on the carrier term alone (§3.3's
   measured baseline: restricted medians 6.4e-4 / 9.8e-4 / 1.15e-3 against A0's
   5.0e-10 / 0 / 5.4e-9 — five to six orders over F = 10); A0/A1 **passes, or a residual
   mover is named as a new carrier — either is a result.** On `low_aspect_ratio_DEMO` the
   baseline's argmax is the open term above, so the expected outcome there is exactly the
   naming case: the pair's images vanish and whatever `tfcoil.m_tf_coil_superconductor`
   carries beyond them remains and is named.
2. **Carrier closure per run** (tally-side; no new field — every Phase A run's
   `perturbation.json` already records the factor and before/after hex of
   `build.dr_fw_inboard`, `build.dr_fw_outboard` and `pf_power.vpfskv`). From each A1u
   run's recorded entry displacement of the pair, the predicted A35 image
   (0.5·(Δin + Δout) on nof's top mover; −Δout on st's) is compared with the measured
   restricted-audit maximum; the relative difference is published per run.
   `low_aspect_ratio_DEMO` has no traced coefficient yet; gate G3c supplies it.
3. **Cost.** Per-node model-evaluation counts (primary; the I-10 insurance), per-block
   totals, the unweighted A1/A0 ratio and the weighting-invariance bracket, as V2.
   **Pre-declared expectation:** A1u/A1 counts equal to within one M2 inner sweep (the
   prime changes what `Build` reads, not how often it runs). Prior context, V2 (not
   acceptance): A1/A0 = 0.522 / 0.568 / 0.502 (nof / lad / st), reproduced by A38 as
   0.5217 / 0.5680 / 0.5016.
4. **Bookkeeping rules.** The lift residual (pin inconsistency) is reported separately and
   excluded from the similarity statistic by declaration; the cold-start term is reported
   beside, never pooled; the failure taxonomy (crashed / refused / unconverged /
   infeasible-at-audit) carries denominators of 25 per arm per deck.

## 4. Phase B — optimisation comparison (the headline)

### 4.1 Arms: five

*Caption: the Phase B arm lattice; one row per arm: its architecture and which step of the
ladder it isolates against the previous arm. The prime is ON in B2 and B3 only (O4/D19);
R, B0 and B1 keep upstream order and no prime — the flat arms self-repair the lag at a
cost of at most one sweep on call 1, so priming them would change nothing measurable and
would move the reference arm's first call. `st_regression` (k = 0) skips B1, which
degenerates to B0 there. There are no prime-free Phase B twin arms (O5): the ladder
measures the whole intervention; the prime rides inside the B1→B2 step and is not
separately attributed there — its Phase B inertness after call 1 is established by gate G2
and disclosed.*

| arm | architecture | isolates (vs previous) |
|---|---|---|
| **R** | PROCESS as shipped | anchor |
| **B0** | flat coupling-state MDA, predicate-matched | stopping rule (R→B0) |
| **B1** | B0 + burn-time lift (constraint 93) | the lift (B0→B1) |
| **B2** | partitioned blocks with the outer verification loop, lift, post-solve hoist, **prime** | the partition, including the reorder and the prime it requires (B1→B2) |
| **B3** | B2 without the outer loop (trust), **prime** | the trust step (B2→B3) |

**B0→B3 is the headline comparison (the designed architecture); R→B3 the user-facing
figure.**

**Starts (pre-declared rule).** start000 unperturbed plus 24 perturbed at δ = 0.10,
seed-paired across arms; **interior sampling declared**: u uniform in [−1, 1) per
component, bounds-clamped. N = 25 per deck per arm (O2: no lad extension now — **lad's
B2→B3 verdict rests on ~10 both-converged pairs and is published with that denominator**).
Same τ everywhere; in the lifted arms the lifted variable's initial guess is the value the
coupling would start from in R/B0 — the lift adds a variable, never a different starting
state.

### 4.2 Checks, each with its acceptance rule pre-declared (never on iteration variables — D6)

**Median construction, declared once for every Phase B check (§2's table):**
**nearest-rank, upper-middle** — the element at index n//2 (0-based) of the sorted values
(`ratios[n // 2]` on the sorted list), matching the nearest-rank p90 convention already in
use. Declared before any run because V2's lad B2→B3 iteration cell is
construction-dependent: over the same 10 pairs the mean-of-middles (`statistics.median`)
construction reads 1.33 and the nearest-rank construction reads 1.40 — the only cell where
the two disagree (V2 report §5.3, dated note; trunk commit `0a8f5af2`). Every median below
is the nearest-rank one.

**Amendment, 2026-09-04 (pre-campaign, pre-approval) — totals are published beside every
iteration median.** A second independent read of V2's records found that lad's B0→B1
iteration median (0.833, "a 17 % reduction") **reverses on summed iterations**: over the
same 11 pairs, B0 = 228 against B1 = 230, a sum ratio of 1.009, because two seeds blow up
(11 → 36, 11 → 65) and repay what the other eight save (V2 report §5.3 correction; the
absolute counts are emitted by the committed analysis at `6f05f819`). A median of ratios
answers "what happens to a typical seed"; it does not answer "what does the campaign cost".
V3 therefore **publishes, for every arm pair and deck: the declared nearest-rank median of
per-pair ratios, both arms' summed iterations over exactly the ratio-contributing pairs,
and their sum ratio**, with the pair count and the contributing seed set named. **The
acceptance rule is unchanged** — it remains the median, declared in §2 — but a median and a
sum ratio that disagree in *direction* must both appear, and the report must say which
question each answers. Corollary, also declared: a B0 column is only comparable within one
arm pair, because converged pair sets differ between pairs (on V2's lad, B0 totals 228
against B1 and 205 against B3 — different seed sets); totals are never carried across
columns.

1. **Same optimum.** Per deck, paired |Δ `norm_objf`| at accepted optima (`ifail = 1` on
   both sides — the declared pairing), expressed **relative** per pair:
   r = |Δ `norm_objf`| / max(|`norm_objf`|ₐ, |`norm_objf`|ᵦ) (the per-pair denominator is
   fixed now as the larger magnitude of the two sides — a construction the development
   plan left unstated, declared here before any run). The yardstick is measured inside the
   same campaign: the R→B0 relative spread. **Acceptance, per deck at BOTH median and
   p90:** for each of B0→B1, B0→B2, B0→B3,
   **r_quantile ≤ max(F × yardstick_quantile, floor)** with F = 10 and
   **floor = 1e-6** (relative on `norm_objf`, O3 — the D6/A25 correctness tolerance).
   The floor is what V2's construction lacked: its R→B0 yardstick landed at machine noise
   (3.3e-15 on nof), so any nonzero footprint failed while agreeing to 1e-10. The full
   paired distributions are published either way; the all-ok construction beside.
   **1a — multi-attractor decks (declared reporting rule, no acceptance threshold).**
   Per deck, accepted optima are clustered by `norm_objf`: values sorted, and a relative
   gap > 10 × floor (= 1e-5) between consecutive values separates clusters. A **hop** for
   an arm pair is a seed whose two accepted sides land in different clusters; the **hop
   rate** (hops / both-converged pairs) is reported per arm pair with **R→B0's hop rate as
   the comparator** (V2 measured the stopping-rule change itself hopping on st — a hop is
   a counted event, not an outlier). Within-cluster agreement (check 1's statistics over
   same-cluster pairs) is published beside the all-pairs construction.
2. **Iteration multiplier.** Per deck, the paired ratio of optimiser iterations over
   **both-converged pairs (the declared pairing** — V2's tally reached this construction
   only by a silent drop that happened to coincide with it; V3 declares it, and H3's
   records make the unconverged-exit iteration counts available beside).
   **Amendment, 2026-09-04 (pre-campaign): "both-ok" is not "both-converged", and the
   tally must test `ifail`, not merely the presence of an iteration count.** A second
   independent read of V2's records found that an `ifail = 5` run *can* record a nonzero
   iteration count — st seed 10 ends `ifail = 5` after 44 iterations — so V2's st check-2
   rows are over 24 both-*ok* pairs including one unconverged baseline, and its summed
   B0→B3 iterations reverse direction between the two constructions (1.021 both-ok
   against 0.972 converged-only; V2 report §5.3 pairing correction). V3 therefore
   **computes both constructions and names each in a `pair_construction` field**, accepts
   on the declared both-converged one, and publishes the both-ok one beside. `_conv()`
   tests `status == ok` **and** MFILE `ifail == 1`; a pair kept on the presence of an
   iteration count alone is a defect, not a construction.
   **Acceptance: median ≤ 1.05 for B0→B1, B0→B2, B0→B3; the median only** (per-start
   counts are dust-sensitive by ±80 %; extremes are published, never judged). B2→B3 and
   B0→R are reported beside, outside the acceptance rule.
   **Pre-declared lad prediction (the prime makes it testable at zero cost):** B2→B3 on
   `low_aspect_ratio_DEMO` **stays elevated at ≈ 1.40 under the declared nearest-rank
   construction** (1.33 under mean-of-middles — both cited here once; the declared
   construction is used everywhere in this plan) — within the dust floor (A28-vs-A32
   noise measurement: median 1.000, individual pairs 0.59–1.81) — because the carrier is
   inert after call 1 (gate G2). If it instead falls to ≈ 1.0, the first-call deficit
   *was* the mechanism on lad and A35's inertness reasoning is refuted there. **Both
   outcomes are results.** Beyond this prediction, lad's trust-step inflation carries the declared
   baseline **"mechanism unknown"** (O1): no gradient-quality instrument runs inside the
   campaign, and the question is investigated after it only if the adverse result
   persists (contingent task T5).
3. **Lift closed.** Constraint-93 residual at every accepted optimum, per start, reported
   in raw seconds and relative to the burn time. Residuals at unconverged exits are
   published beside, never pooled (they are not optima).
4. **Robustness reporting and cost (no robustness claim).** The A30 taxonomy computed in
   the tally with denominators of 25, `ifail = 5` completions split from "ok" (the V2
   tally defect, corrected by declaration); the **deck-invalid-seed statistic**: a seed
   failing in **every** arm of a deck is excluded from the per-arm rates and counted
   separately as deck-invalid (deck hardness under δ, not an arm effect — V2's lad
   showed 9 such seeds). Identical-success-set node-call sums per arm; the per-block
   split as a first-class tally artifact. **The powered robustness campaign is deferred
   (user, 2026-09-04): V3 makes no robustness claim**; the 1–3-seed crash-count hint V2
   recorded on lad stays recorded, neither claimed nor dismissed.

### 4.3 Declared per-deck expectations (prior context from V2 — hypotheses, not acceptance)

nof: B0→B3 ≈ 0.64 in identical-success-set node calls at median iteration ratio 1.000.
st: ≈ 0.68 at 1.000. lad: end-to-end ≈ 0.76 with the transfer clause applied as in V2
unless check 2 passes there this time. Decks are never pooled; if check 2 fails on a deck,
the A→B transfer is declared broken there and only end-to-end numbers are quoted for that
deck. A failed check is a per-deck result, reported with its numbers — never tuned around.

## 5. The transfer argument (how A and B combine)

As V2: if Phase B's checks pass, net saving ≈ Phase A's per-call saving × (unchanged
multiplier). If Phase B's realised saving lands below Phase A's bound, Phase B's number
stands as the deployment result and Phase A's as the mechanism and upper bound; no
correction is applied in either direction.

**Amendment, 2026-09-04 (pre-campaign, I-17): the transfer is an UPPER BOUND, not a
prediction, and V3 says so before it runs.** Measured on V2's own records, the transfer
**over-predicts the saving on all three decks**: nof 0.522 × 1.000 = 0.522 predicted
against 0.640 measured (**+22.6 %**), lad 0.568 × 1.273 = 0.723 against 0.766
(**+6.0 %**), st 0.502 × 1.000 = 0.502 against 0.711 (**+41.8 %**). The sign is uniform
across every construction (identical-ok and identical-converged cost sets, both iteration
constructions), so it is systematic. Note what this does to V2's declared failure
condition: the transfer was declared broken on **lad only**, on iteration-multiplier
grounds — yet lad is where it is most nearly right, and **st, which passes every gate at
an iteration ratio of exactly 1.000, is the worst deck**. *The declared condition does not
select the decks where the transfer fails.* Consequences, binding on this campaign:
(i) **no V3 number is derived through the transfer** — every end-to-end figure is the
measured node-call ratio, as in V2; (ii) the per-call ratio is reported as the mechanism
and an upper bound, never as an expected end-to-end gain; (iii) the per-deck
over-prediction is republished beside V3's own end-to-end numbers.

**Hypothesis under test in this campaign, pre-declared (not a mechanism).** A Phase A
evaluation may not be the same object as an in-loop one: Phase A enters from a δ = 0.10
perturbed point and takes ≈ 5.5 sweeps (5.53 / 5.00 / 5.84 by deck), while a
gradient-stencil evaluation enters from a point displaced by a tiny finite-difference step
and should sit nearer the two-sweep floor; if the partition's per-call saving is
proportionally smaller on a short evaluation, the transfer over-predicts exactly as
observed. **V2 could not test this — nothing recorded the in-loop sweep distribution.**
V3 records it: `sweeps_per_eval` (histogram, mean, and totals) in every run record, the
same unit on both arms, from the driver instrument committed at `0c4ce5c8` (neutrality
13 493 MFILE hex floats vs the pre-instrument tree, 0 mismatches; the block arm's binned
total equals the driver's own `block_sweeps` counter exactly). **Pre-declared reading:**
if in-loop evaluations are systematically shorter than Phase A's and the block arm's
per-sweep advantage shrinks with evaluation length, the hypothesis is supported; if the
distributions are comparable and the gap persists, it is refuted and the cause is
elsewhere. Both outcomes are results. This is a *reporting* question, not an acceptance
one: no gate depends on it.

## 6. Gates, each with teeth (protocol §12), run before any campaign number is cited

Carried from the development plan §5, verbatim in criteria and teeth. Where component
counts appear they are labelled by deck: 840 (`large_tokamak_nof`) / 846
(`low_aspect_ratio_DEMO`) / 827 (`st_regression`).

*Caption: one row per gate: what it binds, its pass criterion, and its tooth — the
deliberately broken input that must fail before the gate's zeros are accepted (protocol
§12). All criteria are counts or bit-comparisons; a failed gate stops the dependent stage
and is reported with its numbers; nothing is retried with different settings.*

| gate | binds | criterion | teeth |
|---|---|---|---|
| **G0** V3 driver neutrality | every arm | R × 3 decks at the V3 driver commit reproduces V2's recorded R start000 bit-exactly on count fields and objective hex | +1 on a count, 1 ULP on the hex, each must trip |
| **G1** prime off, byte identity | R, B0, B1; the A38-reuse clause (§3.3) | `PROCESS_ARCH_PRIME` unset ⇒ MFILE hex floats identical to a run at the pre-A40 commit, 3 decks (A3's comparator); both runs fresh at their respective commits with identical environment sets, both stamps recorded in the gate record | a 1-ULP change to one float is caught |
| **G2** prime on, fixed-point map | the claim that the prime changes nothing after the first-wall model has run (the Phase B inertness disclosure, §4.1) | from each deck's reference exit snapshot: one `flat_state` call and one `per_module` call, prime on vs off, exit states bit-identical on N/N components — 840 (nof) / 846 (lad) / 827 (st) | a doctored snapshot component trips the comparison |
| **G3** prime on, cold chain (A35's stages) | the "no cut edge carries anything" claim (§1) | verified block chain from the cold deck entry: outer passes 3 → **2** on nof and st; trust chain exit vs the flat fixed point, **in-run `exit_audit` operationalization: 0 above τ** (A35 in-run: 244 / 124; the A35 report's snapshot-pair construction reads 243 on nof — the ±1 near-τ spread is documented in A35 §9, and the gate names its construction so a reproduced 243 is not misread); any residual mover named | the prime-off run must reproduce A35's 3 passes and 244 / 124 |
| **G3c** lad carrier census | A35's declared scope gap; the O1 alternative; §3.3's open term | A35's `trace` + `restarts` stages on `low_aspect_ratio_DEMO`, prime off then on: the carrier coefficient on that deck, and the residual mover set with the prime — names whether A38's open term `tfcoil.m_tf_coil_superconductor` closes or survives | as G3 |
| **G4** audit restriction | the corrected similarity statistic (§3.4 check 1) | a doctored post-solve-owned component in an exit snapshot trips the whole-state audit and **not** the restricted one; a doctored in-loop component trips both | both directions shown |
| **G5** B3 combined-switch equivalence | B3 | as V2's `armgate`, re-run with the prime in the switch set | as V2 |
| **G6** Phase A entry-state and warm equivalence | Phase A | as V2 (A36), re-run at the V3 commit for all three arms | as V2 |
| **G7** record completeness | the declared pairing and the failure forensics (§4.2 checks 2 and 4) | a deliberately unconverged smoke run carries `n_solver_iterations`, the constraint residual vector, the active set and the ladder stage | a run with a field missing is refused by the tally |

**Full-run neutrality of the prime is not a gate** but a published context table from the
campaign itself (objective within the D6 tolerance, iteration medians within the dust
floor): bit-identity across an optimisation is unattainable for any change to sweep 1 of
call 1, and is not claimed.

## 7. Correctness, records and reporting (binding rules)

- **Acceptance quantities are counts and bit-comparisons.** Timings appear as context
  only — the serial repetition block (3 reps, median and range) and one profiled run per
  deck for the per-node unit-time reconstruction, both with their caveats published
  (state-independence; driver overhead outside node time). No conclusion rests on a
  timing (I-10, trap T5).
- **Exit forensics at every exit** (harness H3, task A41): `n_solver_iterations`,
  `ifail`, the ladder stage, the constraint residual vector and the active set are
  recorded at **every** exit, converged or not; a field missing at an unconverged exit is
  a tally refusal (G7).
- **Declared tally constructions** (task A41, T-a…T-e): restricted similarity via the
  node→write-census→spec mapping with the whole-state audit beside; declared
  both-converged pairing, the A30 taxonomy with denominators and the deck-invalid-seed
  statistic; the same-optimum floor, clustering and hop rates; the per-block node-call
  split as a first-class artifact; the per-run carrier closure from `perturbation.json`.
  The audit records the per-component residual vector in every run
  (`audit_residual.json`, A38's instrument), so any future restriction is a re-tally,
  not a re-run.
- **Every published number comes from executing a committed script** (protocol §15);
  `v3_report_analysis.py --verify` regenerates every published table from the records;
  failure paths are reachable from the same entry points. **Every table carries a concise
  caption** stating units and cell semantics (protocol §16).
- **Everything in this document is fixed before the first campaign run.** Amendments are
  dated edits.

## 8. Scope honesty (what this experiment does not show)

As V2, per the development plan §9: one code (PROCESS) at one commit (`c0ae5b28`), three
decks, tokamak only, one partitioning choice, one lift, one perturbation stream at one
amplitude, one optimiser (VMCON). Per-deck conclusions; decks are never pooled. No claim
transfers to other partitionings, other couplings, or other systems codes. **No robustness
claim** (the powered campaign is deferred). `low_aspect_ratio_DEMO`'s B2→B3 verdict rests
on ~10 both-converged pairs and is published with that denominator; its trust-step
iteration inflation carries the declared baseline **"mechanism unknown"** — the
gradient-quality question is deliberately outside this campaign and is taken up afterwards
only if the adverse result persists. The existence proof is exactly that: architecture
changed performance measurably, physics untouched.

---

## Appendix A — Directory and run discipline

New directory `arch_surgery/MDA_partitioning_experiment_v3/`, mirroring V2. **V2's
directory is not edited.** Reuse from V2 is the default, explicitly (user directive,
2026-09-04): A41's first commit is a **verbatim copy of the V2 harness** into this
directory — unchanged content, provenance (source path + commit) in each copied file's
docstring — so every subsequent modification is legible in history as a diff against V2.
Thin layers import `arch_surgery/idf_probe/` rather than duplicating it; a copy that
diverges is a new file here, never a patch to the V2 record.

*Caption: one row per file of this directory: its name and its role. All committed except
`runs/`, which stays untracked (bulk artifacts); summaries and verdicts are committed.*

| file | role |
|---|---|
| `EXPERIMENT_PLAN.md` | this document; every later change a dated amendment |
| `v3_config.py` | every declared setting in one place; **`EXECUTION_APPROVED = False` until the user approves this plan, flipped in the same commit as the dated approval here**; `INSTRUMENTATION` ledger with `prime` (A40) and `exit_forensics` (A41) entries that make campaign stages refuse while `False` |
| `v3_runner.py` | thin layer over `arch_surgery/idf_probe/` (never a duplicate): arm environments composed from nothing with every switch cleared (A1 and B2/B3 add the prime), isolated fresh-subprocess runs, the W = 3 pool, resume semantics, clean-tree stamps |
| `phase_a.py` | preflight / reference / gates G4 G6 / campaign (A0, A1u, A1) / tally |
| `phase_b.py` | preflight / gates G0 G5 / campaign (R, B0, B1, B2, B3) / tally / timing |
| `run_experiment.py` | one-button entry point (`__main__`, no required CLI arguments); draft mode runs preflights, gates and smoke only |
| `v3_report_analysis.py` | independent recomputation of every published table from the records; `--verify` |
| `runs/` | untracked bulk artifacts |

Gates G1/G2/G3/G3c and the prime variant point are task A40's (the only `process/` change
in V3, driver scope, with its own neutrality gate and merge). The heavy slot is A40's
among the parallel tasks; the campaign (A42) is the single heavy user afterwards. Cost,
context only, from V2's timings: Phase A roughly 1.5 h at W = 3; Phase B ~350
optimisations, roughly 3–4 h at W = 3; gates under an hour.

## Appendix B — Change log

- 2026-09-04 — written by task A39 (v3-plan) from `V3_DEVELOPMENT_PLAN.md` (§0 fully
  resolved) on V2's structural template; status **NOT YET APPROVED**; A42 blocked on the
  user's dated execution approval.
- 2026-09-04 — orchestrator mid-task correction folded in before the first commit (trunk
  commit `0a8f5af2`, which landed after this worktree's branch point): V2's lad B2→B3
  iteration multiplier is construction-dependent (mean-of-middles 1.33 vs nearest-rank
  1.40 over the same 10 pairs); the **nearest-rank (upper-middle) median is pre-declared
  as the single construction for every Phase B check** (§2, §4.2), and the lad prediction
  anchor is restated as ≈ 1.40 under the declared construction (§4.2 check 2). The
  development plan's §4.2 wrote the anchor as ≈ 1.33 before the construction dependence
  was known; this plan's declaration supersedes it.
