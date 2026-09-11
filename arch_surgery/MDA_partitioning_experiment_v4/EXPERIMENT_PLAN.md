# MDA Partitioning Experiment V4 — Experiment Plan

> **Document status** — **DRAFT · NOT APPROVED.** Written 2026-09-10 by the orchestrating
> session at the user's instruction, from
> [`../docs/plans/V4_IMPROVEMENT_LIST.md`](../docs/plans/V4_IMPROVEMENT_LIST.md) (the candidate
> list this plan selects from), the V3 plan and report in
> [`../MDA_partitioning_experiment_v3/`](../MDA_partitioning_experiment_v3/), and the arm matrix
> settled with the user on 2026-09-10. **V2's and V3's directories are frozen as the record of
> what ran; nothing in them is edited by V4.** Base commit `c0ae5b28` throughout; the physics is
> frozen — V4 contains no change under `process/models/`.
>
> **This document describes the methodology only.** How the measurement harness is built is a
> separate plan ([`../docs/plans/V4_HARNESS_IMPLEMENTATION_PLAN.md`](../docs/plans/V4_HARNESS_IMPLEMENTATION_PLAN.md),
> task A45, pending the user's approval); §3.5 here says *what* the implementation must provide,
> not how.
>
> **Every §3.7 choice is ruled** (user, 2026-09-10; D20–D22) — the rulings are recorded in §3.7;
> §4's table format awaits the user's review. Execution is blocked until
> the user approves this plan by a dated edit of this header and flips the harness's
> `EXECUTION_APPROVED` flag in the same commit, as V3 did.
>
> **Both investigations that fed this plan have reported and are merged.** A44 (transfer-gap):
> the Phase A → Phase B gap is the entry regime (per-evaluation term, uniform) times an
> evaluation-count term (lift stencil column, retries, trajectory) — absorbed in §3.4/§3.5. A43
> (st-trust-gap): the outer verification loop never fired in the whole V3 campaign; the `B2`/`B3`
> difference is inner-solve slack below τ, not a missed coupling; `st_regression` stays (D22's
> conditional answered *no*) — absorbed in §3.2/§3.3/§3.7 (e)/(g).

---

## 1. Introduction

### 1.1 The system under study

PROCESS is a fusion power-plant systems code. It solves a constrained optimisation problem
over a design vector of 14–20 iteration variables with the sequential quadratic programming
optimiser VMCON, using central finite differences (step `epsfcn = 0.001`) for its gradients.
Every objective and constraint evaluation the optimiser requests — including each of the
`2n` finite-difference perturbations per optimiser iteration — calls `call_models`, which runs
the plant's physics and engineering models in a fixed sequence and repeats the sequence until
the objective and the constraint vector stop changing between passes. That repeated sequence is
a **multidisciplinary analysis (MDA)**: a fixed-point iteration over the *coupling state*, the
set of quantities the models write for one another. Upstream's stopping test looks at ~27
output scalars with `np.allclose(rtol = 1e-6)` (which carries a hidden `atol = 1e-8`) and a
minimum of two passes; it does not look at the coupling state itself.

The **architecture** of this solve — how the MDA is organised, where its convergence is tested,
which quantities the optimiser owns, and which models run how often — is a driver choice.
The models are not. This experiment changes only the driver (`process/core/caller.py`,
`process/core/solver/`) and keeps every model byte-identical to upstream at the frozen base
commit `c0ae5b28`, so that any measured difference is the architecture's alone.

### 1.2 Research question

> **Does the arrangement of solvers and optimisers alone — every physics and engineering model
> frozen — measurably change the cost of solving PROCESS, at unchanged quality of the optimum,
> and does the per-call saving measured without the optimiser transfer to the optimisation?**

Decomposed into the questions V4 answers, each with its own arm pair and acceptance rule (§3):

- **RQ1 — per-call cost.** At matched final accuracy on the coupling state, how many
  model-node evaluations does one MDA solve cost under the partitioned architecture against
  the flat one? *(Phase A, `A0 → A1`, with the ownership rung `A0 → A0p → A1`.)*
- **RQ2 — end-to-end cost and correctness.** Inside a full optimisation, how many model-node
  evaluations does the partitioned architecture cost against the flat baseline, at the same
  optimum, with the optimiser's iteration count bounded? *(Phase B, `B0 → B3` per rung.)*
- **RQ3 — transfer.** Does Phase A's per-call ratio predict Phase B's realised ratio, and if
  not, which factor — the per-evaluation cost, the evaluation count, the entry regime, or the
  ownership of the coupling variable — carries the difference? *(§3.4; issue I-17.)*
- **RQ4 — the stopping rule.** What does replacing upstream's objective/constraint stopping
  test with a coupling-state test cost, and where does upstream's test actually leave the
  coupling state? *(`AR → A0`, `BR → B0`.)*
- **RQ5 — the trust step.** After the partition, is the outer verification loop still doing
  work — i.e. is the block decomposition complete — on every configuration? *(answered by A43
  (st-trust-gap) on V3's records: the decomposition is complete on every configuration — the
  verification pass never fired, and one schedule pass reaches the flat fixed point bit for bit once
  the blocks are solved exactly. No V4 arm measures it; `B2` is removed, §3.2.)*

### 1.3 Terms used throughout

| term | meaning here |
|---|---|
| **node** | one model call site in `call_models` (e.g. `physics`, `build`, `costs`); the unit of cost. A **node call** is one execution of one node |
| **sweep** | one pass over a node sequence — the whole loop (flat) or one block's nodes (partitioned) |
| **coupling state `y`** | the measured set of state fields written by in-loop models (840 / 846 / 827 components on the three configurations); the fixed-point iteration converges this |
| **τ** | the convergence tolerance on `y`, per component, scaled: `max_i |Δy_i| / s_i < τ`, τ = 1e-6, `s_i` a measured scale (§3.6 says which) |
| **flat MDA** | one loop over every in-loop node, stopping on `y` at τ (arms `A0`, `B0`) |
| **partitioned MDA** | three block solves — M1 physics, M2 coils, M3 plant — each iterated to its own fixed point at τ, run in feed-forward order; the block membership comes from a validated dependency-structure matrix (DSM) of the code |
| **block loop** | in the partitioned MDA, each block is iterated to its own fixed point at τ. V3 also offered a *joint test* over all blocks that repeated the whole schedule if anything still moved (its arm `B2`, and the words "outer"/"inner" loop); V4's partitioned arms run the schedule **once**, so there is one kind of loop and **one tolerance for every converger** (D23) |
| **burn-time coupling** | the one cross-block feedback on pulsed configurations (`k = 1`): the `pulse` model computes `times.t_plant_pulse_burn`, which the physics block reads. `st_regression` is steady-state (`k = 0`): it has no such coupling |
| **lift** | taking the burn time out of the loop; its **owner** becomes either a *constant* (Phase A: pinned at the entry value) or *the optimiser* (Phase B: iteration variable 178 with consistency constraint 93) |
| **arrangement** | *when* things run: at node granularity (`build` after `physics`) and at method granularity (the **prime** — the run-constant first-wall geometry method executed at the head of every sweep so that `build` reads this pass's value) |
| **deferral** | how often a node runs: **`per_sweep`** (in the loop), **`per_call`** (once per `call_models`, after convergence, before or after the predicate depending on what the predicate reads), **`per_run`** (once per optimisation, at the accepted optimum). Membership is derived from measured read/write sets, never listed by hand |
| **configuration** | one optimisation problem — plant, objective, constraint set — named by its input file's stem (`large_tokamak_nof`, `low_aspect_ratio_DEMO`, `st_regression`); the word replaces V3's "deck" and "scenario" |
| **input file** | the configuration's committed `<name>.IN.DAT` (never edited, D9) or its **lifted** derived copy (§3.3); "frozen" is reserved for the physics freeze and the predicate mode |
| **seed-pairing** | every arm sees bit-identical perturbed entries for the same seed index, so comparisons are paired |
| **teeth** | a gate's demonstrated ability to fail: a deliberately broken input that must trip it before its zeros are accepted |

---

## 2. Background

### 2.1 What the earlier revisions established

**V2 (2026-09-02).** The existence proof: on `large_tokamak_nof`, architecture alone changed the
cost of solving PROCESS measurably. Its two lasting corrections to method were that Phase A's
cost must be compared *at matched achieved accuracy* (a comparison at matched tolerance settings
reversed sign on two configurations) and that a *reference arm* running PROCESS as shipped is
needed beside the predicate-matched control, because the flat control and upstream stop on
different predicates and their ratio bundles architecture with stopping rule.

**V3 (2026-09-07).** Added the prime to the intervention and corrected the apparatus. Results
that V4 inherits as prior context (V3 report, §4–§8; all at `c0ae5b28`, campaign commit
`362c0b47`):

- **The prime closes the `FirstWall → Build` carrier.** Phase A's similarity check failed for
  the prime-free block arm by five to six orders and passed for the primed one on all three
  configurations, at zero additional node calls (`A1u → A1` ratio exactly 1.0000). From V4 the
  prime is part of the intervention, not a separate question (improvement-list item 0).
- **End-to-end, the partitioned architecture executes 36–55 % fewer model-node evaluations**:
  `B3/B0 = 0.639 / 0.450 / 0.533` (nof / lad / st) over the identical-converged seed sets,
  with the optimiser's iteration bound (median paired ratio ≤ 1.05) passing on every
  configuration and every accepted pair.
- **The stopping rule is not free.** `R → B0` costs 0.976 / 1.028 / 1.155 in node calls.
- **Same optimum: passes on nof; fails on lad at the p90 by a factor 1.26 and localises to the
  lift rung `B0 → B1`; on st fails all-pairs and passes within cluster** on a four-attractor
  configuration. Check 1 measures optimality, not location — objectives agree to 11–13 digits
  while design points differ by up to 44 % / 100 %, and upstream's own stopping-rule change
  relocates the point as much.
- **The node-call win does not reach wall clock**: B3 is 0–15 % slower despite far fewer node
  evaluations, and a non-node-proportional cost term must exist (V3 §7–§8). Timings are
  never evidence in this project; the term is to be *counted* (item 3).
- **The trust step is free on the pulsed configurations and not on st**: `B2 → B3` iteration
  counts are identical seed for seed on nof and lad; on `st_regression` 7 of 23 both-converged
  seeds differ, B3 worse on 6 (summed 501 → 587). The outer loop still does work there that
  the prime does not account for — investigation A43.
- **The Phase A → Phase B transfer is not systematic.** V2's uniform over-prediction became
  +22.6 % / −20.7 % / +6.3 % in V3 (converged sets); lad reversed sign. Candidate mechanisms
  named in V3: the entry regime (Phase A enters 100× further from the fixed point than any
  finite-difference call), and the ownership of the burn time (Phase A pins it to a constant
  displaced from consistency by 155 s / 526 s at the median; Phase B lifts it into the
  optimiser, and on lad that quantity *is* the objective) — investigation A44.

### 2.2 What V3's own assessment found wrong with its design

Read from the V3 report §8 and the improvement list; each becomes a method change in §3:

1. Phase A had **no reference arm** and **no rung for burn-time ownership** — `A0 → A1` varied
   the owner together with the partition, so its similarity statistic had to *exclude* the
   burn-time residual by declaration, and no Phase A step matched any Phase B step.
2. The intervention arms ran upstream's **output-time idempotence loop (`MDA_Output`)**, a
   second flat convergence loop that is a property of the incumbent, not of the architecture
   (item 1b); it also masked the only place the block arm's handed-over state was re-tested.
3. On st an **empty block** was swept 570–1131 times per run executing nothing (I-20a), and
   the **per-sweep overhead** hypothesised to explain the wall-clock gap was never counted.
4. The **objective is perfectly confounded with the structural variable** across the three
   configurations (item 4): st is at once the only `k = 0`, the only un-lifted, the only
   Q-objective and the only post-solve-`pulse` configuration.
5. Phase B statistics used **five different seed filters**; check 1's clusters were **ten
   times coarser than its floor**; a declared construction reached only one of two
   implementations (I-19).
6. The convergence predicate's **frozen denominator** is unconventional and demonstrably
   over-tight on some components (I-12); a conventional scaled step test was proposed for
   trial (item 5a).
7. **Names did not say what mechanisms do**: `HOIST` vs `POST_SOLVE` are two levels of one
   deferral ladder; the prime is arrangement at method granularity (item 1d).

### 2.3 What does not change

The frozen base commit `c0ae5b28` (D2); the models (D5/D11); correctness gated on `norm_objf`
plus a feasibility audit, never on iteration variables (D6); the module partition derived from
the collapsed DSM (D8); the three configurations (D17); the baseline is PROCESS as shipped
(D14c) with a predicate-matched control beside it (D18); the prime inside the intervention
(D19). Every acceptance quantity is a count or a bit-comparison; no conclusion rests on a
timing (I-10).

---

## 3. Method

### 3.1 Design in one sentence

Two phases on three configurations, seed-paired, every arm composed from the same set of
driver switches: **Phase A** runs one `call_models` evaluation per arm at perturbed warm
entries and measures per-call cost and final accuracy without an optimiser; **Phase B** runs
the full optimisation per arm from perturbed starts and measures end-to-end cost, optimum
quality and the optimiser's trajectory; the arms form a **ladder** in which adjacent rungs
differ by one named thing.

### 3.2 The switch matrix — the centrepiece

Every arm is an assignment of the driver's environment switches. The matrix is the experiment:
the harness composes each arm's environment *from this table and nothing else* (every switch
cleared first, then set), and records the composed environment in every run record.

*Caption: one column per arm, one row per switch. Phase A arms (`A*`) run one evaluation; Phase
B arms (`B*`) run an optimisation. "Committed" is the configuration's committed input file, never
edited; "lifted" is a derived copy of it differing in exactly three lines (§3.3). The Phase A arms
never reach the output path, so the output-time-loop row is not applicable (`n/a`) to them. Rows marked ⁺ apply on the
pulsed configurations only; on `st_regression` (`k = 0`) they are inactive, `A0p` composes to
`A0` and is skipped and recorded as skipped, and `B1` composes to `B0` and is skipped likewise.
Nodes not deferred run `per_sweep`. `AR`/`BR` have every switch unset: PROCESS as shipped.*

| | **AR** | **A0** | **A0p** | **A1** | **BR** | **B0** | **B1** | **B3** |
|---|---|---|---|---|---|---|---|---|
| MDA solve | upstream | flat | flat | **partitioned** | upstream | flat | flat | partitioned |
| stopping rule | objf/conf | `y` @ τ | `y` @ τ | `y` @ τ | objf/conf | `y` @ τ | `y` @ τ | `y` @ τ |
| block schedule | — | *(one block)* | *(one block)* | one pass | — | *(one block)* | *(one block)* | one pass |
| arrangement · node (`build` after `physics`) | — | — | — | ✓ | — | — | — | ✓ |
| arrangement · method (prime) | — | — | — | ✓ | — | — | — | ✓ |
| deferral `per_call` | — | — | — | ✓ | — | — | — | ✓ |
| deferral `per_run` | — | — | — | ✓ | — | — | — | ✓ |
| burn time out of the loop ⁺ | — | — | **✓** | ✓ | — | — | ✓ | ✓ |
| **burn-time owner** ⁺ | loop | loop | **constant** | constant | loop | loop | **optimiser** | optimiser |
| input file ⁺ | committed | committed | committed | committed | committed | committed | **lifted** | lifted |
| output-time loop (`MDA_Output`) | n/a | n/a | n/a | n/a | upstream | upstream | **none** | none |

**`B2` — the partitioned arm with the outer loop in verify mode — is removed** (user ruling
2026-09-10). V3 measured its verification pass triggering a third pass **zero** times in 91 888
calls across the three configurations (A43 (st-trust-gap), records stage), so as an arm it
measures nothing the uncharged exit audit does not; its only remaining role — detecting an
incomplete decomposition on `st_regression` — is A43's, on V3's records. **A43 (st-trust-gap) has since answered the question the removal left open:** on st a single
schedule pass reaches the flat fixed point *bit for bit* once the blocks are solved exactly (0 of 805
components differ at inner τ = 1e-14, on every traced seed); the `B2`/`B3` difference was the blocks'
own inner-solve slack below τ (max 3.3e-9, in M2 and M3, none in M1), and 0 of its 40 movers has a
loop-carried cross-block edge in the dependency export. **`st_regression` stays in V4.** What the
verification pass bought was sub-τ accuracy, and the inner tolerance buys it instead — decision (g).

*The switches, for the record — the names the copy reads since DR1 (A56 (driver-renames), 2026-09-10; harness plan §11.2), the V3 name in parentheses; every retired name raises if set:* `PROCESS_ARCH_MDA = flat | partitioned` (was `MODULE_SOLVE = flat_state | per_module`; `OUTER` retired — `partitioned` runs its block schedule once); `PROCESS_ARCH_ARRANGEMENT_NODE = build_after_physics` (was `SEQUENCE`); `PROCESS_ARCH_ARRANGEMENT_METHOD = fw_geometry` (was `PRIME`); `PROCESS_ARCH_DEFER_PER_CALL = feedforward | feedforward_lifted` (was `HOIST`); `PROCESS_ARCH_DEFER_PER_RUN = <artifact>` (was `POST_SOLVE`); `PROCESS_ARCH_BURN_TIME_OWNER = loop | constant:<hex> | optimiser` (was `LIFT = burn_time` and `PIN_BURN_TIME = <hex>`); `PROCESS_ARCH_TAU` (`INNER_TAU` retired, D23); `PROCESS_ARCH_COUPLING_STATE` and `PROCESS_ARCH_WRITE_SETS` (were `YSTATE`, `WRITESET`) — the two committed per-configuration artifacts that define `y` and the per-block write sets. `PROCESS_ARCH_OUTPUT_LOOP = upstream | none` landed with A57 (driver-output-path), 2026-09-10. Pending, refused until its driver change lands: `PROCESS_ARCH_PREDICATE = frozen | mixed` (A59).

**The rungs, and what each isolates.** Adjacent arms differ by one named thing; the ladder is
declared, and the harness refuses an arm pair whose declared difference does not match its
composed environments.

*Caption: one row per rung; the Phase A and Phase B steps in a row are the same set of switch
changes — with one declared exception, the output-time loop on the ownership rung, which exists in
Phase B only — so a Phase A ratio may be read against its Phase B twin. Every Phase A arm has a
Phase B twin and every Phase B arm a Phase A one.*

| Phase A step | Phase B step | isolates | acceptance / role |
|---|---|---|---|
| `AR → A0` | `BR → B0` | **the stopping rule** — upstream's objective/constraint test at its two-pass floor vs the coupling-state test at τ | reported, never accepted on (a comparison at unmatched accuracy by construction — §3.6) |
| `A0 → A0p` | `B0 → B1` | **burn-time ownership** — the loop vs a constant (A) / the optimiser (B); *the one rung where the phases differ in kind* — and, in Phase B only, **the output-time loop** (`upstream → none`), placed on this rung deliberately: it is the rung already declared to differ in kind between the phases, so the headline rung `B1 → B3` keeps a switch set identical to `A0p → A1`. *(Wording completed 2026-09-10 after A47 (harness-skeleton) found the row named only ownership; the matrix is unchanged. The output-time loop's sweeps are counted per run and published as their own column, so neither rung's attribution carries them silently.)* | Phase A: cost and audit at matched map; Phase B: checks 1–3 |
| `A0p → A1` | `B1 → B3` | **the partitioning intervention** — block solves + arrangement (node and method) + both deferrals + one pass over the block schedule | Phase A headline (RQ1); Phase B headline via `B0 → B3` (RQ2); `ε = 1` pre-declared on the pulsed configurations |

`B0 → B3` is the designed-architecture comparison and the Phase B headline; `BR → B3` is the
user-facing figure and is published beside it, never instead of it.

### 3.3 Arms and what composes them

**Configurations (D17), in the order used in every table: nof / lad / st.**
`large_tokamak_nof` (pulsed, `k = 1`, 20 variables, 26 constraints, minimises major radius),
`low_aspect_ratio_DEMO` (pulsed, `k = 1`, 19 / 25, maximises the burn time — *the lifted
variable itself*), `st_regression` (steady-state, `k = 0`, 14 / 18, maximises fusion gain).
The objective/structure confound this creates is item 4 and §3.7 decision (b).

**Reference arms `AR` / `BR`** (item 1). PROCESS as shipped: every architecture switch unset.
`BR` is V3's `R`, renamed so that the two phases' references carry distinct names. `AR` is
new to Phase A and answers RQ4's second half: it reports *where upstream's stopping rule
leaves the coupling state*, measured by the same exit audit every other arm gets. Three
outcomes, all results: audit residual ≫ τ (upstream under-converges the MDA and its cheapness
is bought with accuracy), ≈ τ (the two rules are accidentally equivalent and `BR → B0`'s cost
is pure overhead), ≪ τ (upstream over-solves). **Binding:** `AR → A0`'s cost ratio may never
be published without both arms' audit residuals in the same table. Upstream's loop raises
after ten passes; a Phase A entry at δ = 0.10 may hit that cap, which is recorded as its own
taxonomy row `unconverged-at-cap`, distinct from `crashed`, never dropped.

**Flat control `A0` / `B0`.** One block containing every in-loop node, stopping on `y` at τ;
no deferral (the flat architecture as shipped keeps those nodes in its loop); upstream node
order; no prime (the flat loop self-repairs the first-wall lag within one sweep, so priming it
would change nothing measurable and move the reference's first call — V3 decision O4).

**Ownership rung `A0p` / `B1`** (item 1c; V3's `B1`). Flat solve plus the burn time taken out
of the loop, nothing else. In Phase A the owner is a **constant**: `A0p` pins the burn time at
the seed's perturbed value — the same hex value `A1` receives — so `A0p` and `A1` solve the
same reduced map and their exit states are comparable without exclusion. In Phase B the owner
is **the optimiser**: the lifted input file adds iteration variable 178 and equality constraint 93.
With deferral off the `pulse` node still executes in `A0p` (it just stops computing the burn
time), so `A0 → A0p` changes the owner without changing the node set.

**Partitioned arms `A1` / `B3`.** Three block solves M1 → M2 → M3 in feed-forward
order, each iterated to its own fixed point at τ (inner cap 20 sweeps; reaching it is a
refusal, not a budget); `build` resequenced after `physics`; the prime at every sweep head;
`per_call` and `per_run` deferral by the measured routing rule; the burn time lifted. Both run
**one pass over the block schedule** — what V3 called the outer loop in trust mode; the switch that chose it (`PROCESS_ARCH_OUTER`) is retired and the verified-schedule code removed (DR1, A56 (driver-renames), 2026-09-10). There are no prime-free
twins (item 0; V3 decision O5) and no verified-outer-loop twin (§3.2). **Their certificate of
convergence is the block solves' inner tolerance plus the uncharged exit audit at the handover
point** — there is no outer verification pass, so the inner tolerance is what sets the handover
accuracy, and it is **the same τ every converger uses (D23)**: the flat loop converges the whole coupling
vector to τ, each block loop converges its block to τ, and there is no second tolerance. A43
(st-trust-gap) measured the exchange rate should τ ever be tightened: at a single evaluation `B3`
with block loops at 1e-8 reproduces the removed two-pass `B2` at 1e-6 to every digit of achieved
accuracy, and at 1e-6 its handover is ~30× looser *below* τ — a sub-τ difference the exit audit
records per run and the matched-accuracy rule (§3.6) governs. Not required for V4.

**The lifted input file** differs from the committed one in exactly three lines: the burn time becomes
iteration variable 178; its consistency residual becomes equality constraint 93, inserted
inside the input file's equality block with the count raised in the same edit; and the variable's
initial value is set to the burn time the baseline's own loop settles on at the configuration's starting
design vector, so that the lifted arm's entry consistency residual is exactly 0.0. It is derived
by a committed stage, never hand-edited, and never used in Phase A: the pin refuses any input file
naming iteration variable 178 ("two owners is a refusal, not a race").

**`MDA_Output`** (item 1b). Upstream writes its output files through a second, flat
idempotence loop (up to ten sweeps, MFILEs compared float by float at `rtol = 1e-6`). `BR` and
`B0` keep it: they are the incumbent and its predicate-matched shadow. The Phase A arms never
reach the output path, so the row is not applicable to them and they carry no switch for it
(`A1` therefore runs before driver change DR2 lands; only `B1` and `B3` wait on it). `B1` and
`B3` **do not run it**: their solve phase hands over a state it has already verified at τ, and
re-solving that state with a different loop before writing it out is a property of the
incumbent, not of the architecture. *(Keep-list corrected 2026-09-10 after A47 (harness-skeleton)
found the matrix and this sentence disagreeing on `A1`.)* Consequences, all binding: the replacement output
path calls `finalise` once on the accepted state (a driver change, §3.5); the rung table above
declares the difference; the exit audit is taken at the same position in every arm — at the
entry to `write_output_files`, before any output-time sweep — and the audit position is
recorded per run; and the one signal `MDA_Output` found by accident in V3 (three st `B3` runs
whose handed-over state was not MFILE-idempotent after two flat passes) is looked for on
purpose: the exit audit at the accepted point, per run, with the count of components above τ. *Implementation note, 2026-09-10 (orchestrator, at A50 (harness-run)'s merge):* the audit sweep mutates the state it measures, so it cannot run *at* that entry without handing the output path an audited state; the position is reached by a **snapshot** of the coupling state taken at the entry to `write_output_files`, with the residual computed after the run from the restored snapshot. The snapshot hook landed with A57 (driver-output-path), 2026-09-10: every campaign record carries `audit_position == audit_position_declared == entry_to_write_output_files`, the restore is proven bit-exact before the audit is taken, and the after-the-run position survives for the reproduction gate alone, whose compared values include a residual the previous revision measured there. First measurement at the declared position (seed 0, gate G9): on both pulsed configurations, in `B1` and `B3` alike, exactly one restricted component sits above τ — `tfcoil.insstrain`, ~7e-3 scaled — and none on `st_regression` (improvement list item 11). *Diagnosed 2026-09-11 (A61 (insstrain-diagnosis), `fd480aff`):* that residual is an artefact of the instrument, not of convergence — PROCESS's output path raises `tfcoil.n_rad_per_layer` 100 → 500 before the snapshot and the coupling-state restore does not put it back, so the audit swept a different mesh than the loop; 0 of 840/846/827 components differ between the loop's exit and the audited state, and restoring that one field gives exactly `0x0.0p+0`. **Ruling D25:** the snapshot and restore cover the whole data structure (a derived set, fields that cannot be restored counted and named), landing with A62 (exit-audit-restore) before the campaign; GR's compared set loses the inherited audit residual with its reason. The "one component above τ" reading is withdrawn: `B0` and `B3` converged to τ on every evaluation.

**Empty blocks and empty nodes are left as they are** *(user ruling 2026-09-10 on item 2)*. On
`st_regression` the `PULSE` block survives in the schedule after its only member has left it and is
swept 570–1131 times per run executing nothing (I-20a). *Measured by the copy's own counters (A58 (driver-predicate-counters), 2026-09-10, gate GR's runs): 570 empty sweeps at seed 0 and 3 510 at seed 1 on `B3`, **10.84 % / 11.30 %** of the run's block sweeps. The empty `PULSE` visit occurs on **all three** configurations (40 % of block visits everywhere, `FF` and `PULSE`), but costs a sweep only on `st_regression`: on the pulsed configurations the per-call deferral has emptied the block of members and the visit is free. Every disclaimer therefore quotes the **sweep share** (0 / 0 / 10.84–11.30 %), never the visit share.* V4 does **not** repair this: it is one of
PROCESS's oddities this experiment does not exist to fix, and it costs no model-node evaluation.
It is **disclaimed** wherever it bears: the per-sweep-overhead table (§3.5 check 5) states the
count of empty visits per run beside the dispatch-sweep count, and every caption that weights
sweeps says that node weights differ between sweeps and that empty sweeps are included.

### 3.4 Phase A — per-call cost and accuracy without an optimiser

**Entries.** Per configuration, the **reference** is the converged flat state at the
configuration's design point (one `A0` evaluation from the cold entry of the input file; its cost is the once-per-run cold-start
term, reported beside, never pooled). Campaign entries are multiplicative `1 ± δ·u`
perturbations of that snapshot over the coupling state, `u` uniform in `[−1, 1)` per component
from a hash of (seed, component), seeds 1–25, seed-paired across arms and verified
bit-identical per configuration; each is evaluated by one `call_models` under each arm.

**Two entry regimes** *(amended 2026-09-10 on A44's measurement; A44 pending review)*.
**δ = 0.10**, the V2/V3 regime, deliberately hostile — it displaces run-constants and post-solve
outputs that no optimiser-driven call displaces after call 1, which is what makes the prime's carrier
measurable; **acceptance stays here** (comparability with V2, V3, A35, A38; the prime's
detectability). And **the stencil regime**, the representative one: for each arm and configuration,
the `nvar` **forward** stencil points — design variable `i` at `x_i (1 + epsfcn)`, every other
variable at the configuration's design point, coupling state at the reference fixed point — and the `nvar`
**backward** points `x_i (1 − epsfcn)`, each entered from its forward point's exit, which is
exactly the sequence `fcnvmc2` executes (`evaluators.py:136-143`); plus the lifted column on the
pinned arms. Deterministic, no seeds, `2(nvar + 1)` single evaluations per arm per configuration.
The transfer (§3.5) is stated on this regime, with the forward and backward sets as the published
bracket.

**Why not a smaller δ.** The improvement list proposed δ = 0.001, matched to `epsfcn`, as the
representative regime. A44 measured it (`E2`, ten seeds, three configurations): at δ = 0.001 the
flat arm still takes 5.0 sweeps on nof and lad against the 3.3 an in-loop evaluation takes, the
ratio moves the *wrong* way on two configurations (0.522 → 0.538; 0.568 → 0.524) and is
non-monotone in δ. Sweep counts are roughly logarithmic in amplitude; what governs them is *which*
components are displaced, and a δ-stream displaces every coupling component at once — a different
object from a design-variable step at any amplitude. At the stencil regime every arm's cost per
evaluation, sweep count and per-block composition land within 1–7 % of in-loop, and `A1/A0` at the
backward points is within 0.003 of the in-loop ratio on every configuration. Item 1a's "do not
reduce δ" half stands; its second-amplitude half is replaced.

**Checks, each with its acceptance rule pre-declared.**

1. **Similarity at matched accuracy (the Phase A headline).** Per configuration and pair, the
   distributions of each arm's audited maximum scaled residual over the components **not owned
   by the configuration's `per_run` node set** (membership derived nodes → measured write sets
   → spec keys; never a prefix rule), with the whole-state audit published beside.
   **Acceptance: `A0p/A1` (pulsed) and `A0/A1` (st) within F = 10 at both median and p90.**
   A configuration where every arm reads exactly 0 counts as trivially similar and the report
   says so. The exit audit is one further full sweep of the complete node set — the same ruler
   for every arm — taken at termination and uncharged. On the pulsed configurations the pinned
   pair `A0p → A1` is the declared headline pair because both arms sit on the same reduced map;
   `A0 → A1` is published beside it with the burn-time residual reported separately (V3's
   construction), so V3's numbers remain comparable.
2. **The ownership rung.** `A0 → A0p`: node calls and the exit audit. The pin holds the burn
   time off consistency by the seed's factor; the resulting inconsistency (`burn_time_residual`
   at exit, seconds and relative) is published per run as the rung's own statistic.
3. **Cost.** Per-node model-evaluation counts (primary), per-block totals, the unweighted
   `A1/A0p` (pulsed) and `A1/A0` (st) ratios with the weighting-invariance bracket, and the
   `AR → A0` ratio **only** in the table that carries both arms' audit residuals. Prior context
   (V2, reproduced by A38; not acceptance): `A1/A0 = 0.522 / 0.568 / 0.502`.
4. **Bookkeeping.** The cold-start term beside, never pooled; the failure taxonomy —
   `crashed` / `refused` / `unconverged` / `unconverged-at-cap` (AR) / `infeasible-at-audit` —
   with denominators of 25 per arm per configuration per amplitude; skipped arms (st `A0p`)
   recorded as skipped with the reason.

**Prime accounting (D19, unchanged).** The prime is stamped, not counted: `n_prime_calls`
appears beside every node-call table and is never pooled into it (trap T11).

### 3.5 Phase B — the optimisation, and the transfer

**Starts.** `start000` unperturbed plus 24 perturbed at δ = 0.10 on the iteration variables'
initial values (`1 + δ·u`, `u` uniform in `[−1, 1)` keyed on the variable *number* so shared
variables get bit-identical factors across arms even though the lifted design vector is one
longer), bounds-clamped; N = 25 per configuration per arm; same τ everywhere. Jobs are never
retried; a crashed run is a taxonomy row.

**One seed set per configuration, and failures on the page** (item 5b, §3.7 decision (c)).
Every Phase B table — checks 1–4, cost, per-block split, sweeps per evaluation — is computed
over **the seeds on which every arm converged** (`status == ok` and MFILE `ifail == 1`), one
`n` per configuration, pre-declared. Beside it, per configuration, **the failure table**: every
seed outside that set, which arm failed, its `ifail`, its node calls, and the other arms' node
calls on the same seed — so an arm that fails on expensive seeds cannot be flattered by the
filter. The identical-ok pooled ratio is published once beside, not in every table.

**One format.** Absolute cells as per-run means with the seed bracket; the ratio against `B0`
as the pooled value (sum / sum — the campaign's cost), the per-run median with `[min, max]`
(the typical run), and the count of runs where the arm is worse. Sums retire. `B0` is the
reference everywhere; `B3/BR` is published once on the same set. Prime calls are a column of
the same table (trap T11 in-table). Solve-phase node calls are the denominator throughout; the
output-time and audit sweeps are excluded symmetrically and every caption that uses the
per-node census says so.

**Retries are a term, not a footnote** *(added 2026-09-10 from A44's preliminary finding on V3's
records: lad's published `B3/B0 = 0.450` carries one seed on which the flat arms failed their
first VMCON attempt and converged on the `epsfcn × 10` retry; both attempts' evaluations were
charged to `B0`, and over the ten retry-free seeds the ratio is 0.659 — pending A44's review)*.
A run's node calls are recorded **per VMCON attempt**; the cost table publishes, per arm, the
count of seeds that retried and the ratio **with and without** retried seeds, side by side.
Both readings are defensible and both are published: a retry the other arm did not need is
real cost the architecture avoided at that start, *and* it is a robustness event, not a
per-evaluation cost — pooling it into a cost ratio without saying so is what made V3's lad
headline unreadable. The failure table carries the retried seeds with each arm's attempt count,
`ifail` per attempt and iterations per attempt.

**Median construction, declared once:** nearest-rank, upper-middle — the element at index
`n // 2` of the sorted values — for every Phase B check.

**Checks, each with its acceptance rule pre-declared (never on iteration variables — D6).**

1. **Same optimum.** Per configuration, paired relative `|Δ norm_objf| / max(|a|, |b|)` at
   accepted optima, for `B0 → B1`, `B0 → B3`; yardstick = the `BR → B0` relative
   spread measured inside the campaign. **Acceptance at both median and p90:
   `r ≤ max(F × yardstick, floor)`**, F = 10, floor = 1e-6 relative (the D6/A25 correctness
   tolerance). **1a — clusters.** Accepted optima are clustered by `norm_objf` with a relative
   gap of 10 × floor = 1e-5; hop rates per arm pair are reported with `BR → B0`'s as the
   comparator; within-cluster agreement is published beside all-pairs, **implemented in both
   the tally and the independent analysis** (item 6). **1b — resolution, declared** (item 5):
   two optima closer than the cluster gap but further than the floor are *distinct optima
   below cluster resolution*, a named category with its count per configuration; the smallest
   inter-optimum gap observed is published per configuration so the reader can see whether the
   configuration's optima are denser than the cluster gap can resolve.
2. **Iteration multiplier.** Paired ratio of optimiser iterations over the seed set;
   **acceptance: nearest-rank median ≤ 1.05** for `B0 → B1`, `B0 → B3`; summed
   iterations over the same pairs published beside every median with the sum ratio, since a
   median and a sum can disagree in direction. *Amended 2026-09-10 (user directive, relayed by
   session `process-surgery-bd`, explained and **confirmed by the user in the orchestrating session**):* the iteration
   count is published in **two constructions** — the **final attempt's** (V3's, kept for
   comparability) and **summed over every VMCON attempt, failed attempts included**
   (`n_solver_iterations_summed_over_attempts`, present in every V3 record and never read by V3's
   tally) — with the per-seed attempt count and ladder stage in the table. The trajectory term
   check 2 controls is the whole optimiser path, and a failed attempt is part of it. Both sit
   beside the evaluation count over all attempts, which is the multiplier the transfer needs:
   iterations, even summed, miss the lift's stencil column and the line-search evaluations that
   vary at equal iteration count. **The acceptance statistic is declared as the summed-over-attempts
   median** ( A43 (st-trust-gap) P2 — the same 23 st pairs read 1.17,
   0.91 and 1.07 under three constructions, and a check whose sign depends on an undeclared choice
   is not a check); the final-attempt median is published beside it for comparability with V3. `B1 → B3` and `B0 → BR` reported beside,
   outside the acceptance rule. **Pre-declared expectation:** on the pulsed configurations
   `B1 → B3` leaves the evaluation count unchanged (`ε = 1` exactly; V3: 33/33 converged seeds).
   RQ5 is not measured by a V4 arm (§3.2); A43 (st-trust-gap)'s verdict decides st's place.
3. **Lift closed.** Constraint-93 residual at every accepted optimum, seconds and relative to
   the burn time; residuals at unconverged exits beside, never pooled.
4. **Cost and robustness reporting (no robustness claim).** Solve-phase node calls on the
   one seed set in the one format; the per-block split as a first-class artifact; the failure
   taxonomy with denominators of 25; the configuration-invalid-seed statistic (a seed failing in every
   arm is configuration hardness, counted separately). **Pre-declared expectations (context,
   not acceptance), from V3:** `B3/B0 ≈ 0.64 / 0.45 / 0.53`; `BR → B0 ≈ 0.98 / 1.03 / 1.16`.
5. **The per-sweep overhead, counted** (item 3). Two new driver counters, exact and
   concurrency-invariant like `NODE_CALLS`: predicate evaluations and components compared,
   per run per arm. Published beside the node-call table with the dispatch-sweep count. This
   settles on counts alone whether a non-node-proportional term of the hypothesised size
   exists; wall-clock context (3 serial repetitions, median and range) is reported in its own
   section and is never evidence.

**The transfer (RQ3; I-17), restated** *(amended 2026-09-10 on A44; pending review)*. No V4
number is derived through the transfer; Phase B's realised ratio stands as the deployment result.
The gap is an identity, `R = (N_B3/C_B3)/(N_B0/C_B0) × C_B3/C_B0 = ρ_B × ε`, with `N` solve-phase
node calls and `C` `call_models` evaluations over the one seed set, `per_run` executions and the
reference arms' output-time sweeps carried as separate terms. A44 established on V3's records that
the per-evaluation term `ρ_B/ρ_A` is uniform across configurations and is the entry regime
(§3.4), and that the evaluation-count term `ε` carries all the configuration dependence:
**(i)** the lift's stencil column, exact — every VMCON problem-call costs `2(nvar + 1)`
evaluations, so the lifted arms pay `(nvar + 2)/(nvar + 1)` per problem-call; **(ii)** retries,
whose evaluations are in `N` and whose iterations are not in check 2; **(iii)** trajectory change
at the lift (lad, every seed) and, on st, at the partition. V4 therefore states the transfer as

    B3/B0  ≈  ρ_A(stencil)  ×  (nvar_B3 + 1)/(nvar_B0 + 1)  ×  (problem-call ratio)

with `ρ_A(stencil)` the ratio of per-evaluation means at the stencil regime, the forward and
backward sets as the published bracket, and the problem-call ratio a Phase B measurement the
transfer carries and cannot predict. **Pre-declared expectations:** on the pulsed configurations
`B1 → B3` leaves the evaluation count unchanged (`ε = 1` exactly; V3: 33/33 converged seeds) —
any departure is a finding, not noise; the residual after the restatement is ≤ 5 % (A44 measured
≤ 1 % at the backward points, ≤ 5 % at the forward ones). Check 2 is therefore published **in
evaluations beside iterations**, with per-attempt node calls and both retry readings (§3.5 above).
What Phase A still cannot predict, and the report must say so: the optimiser's response to the
lift and, on st, to the partition.

### 3.6 The convergence predicate, and its trial

**The declared predicate** is a max-norm on the coupling state: a continuous component passes
when `max |Δy_i| / s_i < τ`; discrete components must be exactly equal; a NaN never
converges; a component no model has yet written scores `inf`. **`s_i` is the point of the
trial.** V2/V3 froze `s_i` at the median magnitude over the configuration's harvest, with
`s_i = 1.0` where no magnitude was observed — the **`frozen`** mode — which I-12 showed to be
~10¹⁸ times tighter than intended on `costs.coe` at a divergent design point. The conventional
form (Dennis & Schnabel's scaled step; what MINPACK's `diag`, KINSOL's scaling and OpenMDAO's
`ref` reduce to) keeps the measured scale as a floor and adds the current value:
`max_i |Δy_i| / max(|y_i|, s_i) < τ` — the **`mixed`** mode. Wherever `|y_i| ≤ s_i` it is
bit-identical to `frozen`; it is never tighter, so no count can go up.

**The trial, pre-declared** (item 5a). One implementation, selected by a spec-level mode
recorded in every artifact preamble and every run record, default `frozen` so every V2/V3
record reproduces. A pass is *decisive* when some component is at or above τ on `frozen` and
below it on `mixed`. Gates: (1) neutrality — default mode reproduces V3's Phase A records bit
for bit; (2) the identity with teeth — under `mixed`, every run with no decisive pass is
bit-identical to `frozen`; a run where it is not is an implementation defect; (3) the binding
set named — per configuration and arm, the decisive passes, the components, `|y_i| / s_i`
there, whether the component held the pass under `frozen`; plus a doctored-component tooth
(a component at `100 s_i` with `Δy = 50 τ s_i` fails `frozen` and passes `mixed`; the same
`Δy` at `y = s_i` fails both). **Measurement:** Phase A (`A0`, `A0p`, `A1`; 25 seeds; three
configurations; δ = 0.10) under both modes — counts, ratios with seed bracket, and the exit
audit **on both rulers** (a mixed audit beside a frozen one alone would report an accuracy
gain that is a change of ruler — both columns or neither). Phase B (`B0`, `B3`) under `mixed`
only if Phase A shows a decisive pass on an in-loop component. **Adoption rule:** gates 1–3
pass and the measurement is either neutral (adopted as the easier-to-defend equivalent) or
non-neutral on a named set (adopted, with the moved ratios re-stated as metric-dependent).
Only a gate failure blocks adoption. Adoption makes `mixed` V4's predicate and audit ruler,
with `frozen` selectable for cross-study comparison; V3's numbers are not retro-edited.

**Matched accuracy is verified per run, never assumed from a shared τ.** The exit audit is the
same full sweep on the same ruler for every arm; a pair whose audit residuals differ beyond the
similarity factor is reported as not comparable in cost, whatever its tolerance setting.

### 3.7 Decisions: rulings so far, and what is still open

*Caption: one row per choice of the original §3.7 list; "ruling" is the user's decision of
2026-09-10 (D21) or the plan's recommendation where the decision is still open; the last column is
where the ruling is applied.*

| # | choice | ruling | applied in |
|---|---|---|---|
| **(a)** | second Phase A entry regime | **adopted** — the stencil regime (A44 (transfer-gap)'s measurement), not δ = 0.001; the extra Phase A cost is accepted | §3.4, §3.5, §3.10 |
| **(b)** | objective/structure confound | **no fourth configuration in V4.** Three case studies; the confound is disclosed in every cross-configuration caption and no synthesis is claimed. A separate experiment follows only if V4's results stay inconclusive | §3.3, §3.11, §4 captions |
| **(c)** | Phase B seed set and format | **accepted**: one every-arm-converged set, the failure table, one format, retries as an explicit term. §4 carries placeholder tables in that format for review before any run | §3.5, §4 |
| **(d)** | driver changes | **accepted:** `MDA_Output` removed from the intervention arms (1b); switch renames (1d); predicate mode `frozen \| mixed` (5a), implemented cleanly. **Rejected:** empty-block / empty-node skipping (2) — left as is and disclaimed. Predicate-evaluation counters (3) — **accepted** (2026-09-10, after the explanation in §3.5 check 5). All changes are made in **V4's own copy of PROCESS** (D20), which owes V3 no backward compatibility | §3.3, §3.5, §3.8 |
| **(e)** | `B2`'s fate | **removed** (user, 2026-09-10; D22). **A43 (st-trust-gap) answered D22's conditional: `B3` is not unreliable on st** — 0 components above τ at every inner tolerance, its single pass reaching `B2`'s two-pass state bit for bit once the blocks are solved exactly — so **`st_regression` stays** | §3.2, §3.3 |
| **(g)** | the tolerance of the partitioned arms' block loops, now that `B2` is gone (A43 P1) | **ruled (user, 2026-09-10; D23): one tolerance, τ = 1e-6, for every MDA converger in every arm, both phases** — there is no separate "inner" tolerance to set. Tightening is not required: the exit audit records achieved accuracy per run and comparisons are at matched accuracy. A43's exchange rate (block loops at 1e-8 ≡ the removed `B2`) is recorded should τ ever be tightened — everywhere at once | §1.3, §3.3, §3.10 |
| **(f)** | wait for A43/A44 before approving | **do not wait**; both land as dated amendments (A44's already has) | header |

**All ruled (2026-09-10)**, (g) last, after A43 (st-trust-gap)'s verdict opened it the same day. The V3 report receives **no errata**: A44 (transfer-gap)'s retry finding
lives in its own report and is carried into V4's method (§3.5), not written back into V3. The
PROCESS copy is taken at the current `architecture_surgery` tip, the commit recorded (§3.8 (i)).
The §4 table format awaits the user's review.

### 3.8 Implementation overview

What the implementation must provide for the method above; *how* is the harness plan's
business (A45). Three layers.

**(i) PROCESS driver changes — the instrument.** All in `process/core/caller.py` and
`process/core/solver/`; nothing under `process/models/`; every switch unset ⇒ byte-identical to
upstream, gated (G1-style) with teeth. Existing from V2/V3: the coupling-state MDA (`flat_state`
/ `per_module`), the outer-loop mode, the sequence, the prime, the two deferrals with predicate
routing derived by AST walk of the objective and constraint layers, the lift site in `pulse`
with its driver-owned solution, the pin, the per-pass trace, the counters `NODE_CALLS`,
`SWEEPS_PER_EVAL_HIST`, `n_prime_calls`. **New in V4** (decision (d), D21): the switch renames; the
`MDA_Output`-free output path for the intervention arms; the predicate mode (`frozen | mixed`);
per-attempt node-call stamps at the retry-ladder boundaries (the accounting A44 (transfer-gap)
showed V3 lacked); and the predicate-evaluation and components-compared counters (accepted
2026-09-10). Empty-block skipping is **not** made
(§3.3). Each is a separate, neutrality-gated change with the user's approval before merge.

**V4 runs its own copy of PROCESS (D20).** The root `process/` package stays as the tree V3's
records were made against and is not modified for V4. The whole package is copied to
`arch_surgery/MDA_partitioning_experiment_v4/PROCESS/process/` **at the `architecture_surgery`
commit current when the copy is made, recorded in `PROCESS/PROVENANCE.json` and checked
byte-for-byte against `git show <commit>:process/`** (user: "ensure it is the same commit"), and
every V4 driver change is made in the copy, with no backward compatibility owed to V3's switch names,
record fields or harness. The V4 harness imports the copy (`PYTHONPATH` set to the copy's parent,
`process.__file__` asserted against it in every subprocess); the editable install keeps pointing
at the root package and is never relied on. Two gates bind the copy: its `process/models/` is
byte-identical to `c0ae5b28`'s (the frozen physics, D5) and stays so at every V4 commit; and, at
the copy commit, the copy reproduces V3's records bit-exactly through the rewritten harness (gate
GR, §3.9) — the one place the V3→V4 name map is needed. Because each experiment version now has
exactly one implementation of everything it runs, the convergence-predicate module and the
per-configuration artifacts live inside the V4 folder — **`harness/ystate.py` and
`harness/data/`** (user preference: do not modify the copied tree beyond necessity) — and the
copied driver is re-pointed at them by one path constant each, the only edits the copy needs for
them. The drift objection D14(c) raised against copies does not apply: the copy is the version,
not a fork.

**(ii) Measurement harness — `arch_surgery/MDA_partitioning_experiment_v4/`.** Mirrors V2/V3 at
the top: this plan, the report, `experiment_runner.py` (the one-button entry point, no required
arguments; a draft mode runs preflight, gates and smoke only; refuses the campaign while
`EXECUTION_APPROVED` is `False`), `phase_a.py`, `phase_b.py`, `runs/` (untracked bulk
artifacts). Everything else in a self-contained `harness/` package — nothing imported from
`idf_probe/` or `fixedpoint/`. It must provide: derivation of the per-configuration artifacts
(coupling-state spec, write sets, `per_run` sets by class-level classification with a committed
runtime read census — item 6a, lifted input files) as committed stages; arm composition **from the
switch matrix as data**, every switch cleared first, the composed environment recorded per run;
one isolated fresh subprocess per PROCESS run in its own directory with `process.__file__`
asserted against the tree; the W = 3 pool, deterministic job lists, no retries; run records
stamping tree, commit, dirty flag, full arch environment, `n_solver_iterations`, `ifail`,
ladder stage, constraint residual vector, active set, exit audit (position recorded), per-node
census, per-block split, sweeps per evaluation, the new counters — the same provenance fields
in both phases (item 6a-b); gates as first-class objects with teeth; tallies in the declared
constructions; a name mapping to V3's records for G0, with a gate that cannot find its
reference **refusing**, never passing over an empty comparison.

**(iii) Analysis.** An independent recomputation of every published table from the records
(`--verify` against the tally cell by cell, `--teeth` doctoring the records to show each
comparison can fail), producing every table in this plan's §4 in the one format with its
caption. Nothing is published that this script does not regenerate. The DSM overlay of
improvement-list item 8 is dropped with `B2`: no V4 arm exercises the outer verification loop.

### 3.9 Gates, each with teeth, run before any campaign number is cited

*Caption: one row per gate: what it binds, the criterion, the tooth. All criteria are counts or
bit-comparisons; a failed gate stops the dependent stage and is a result; nothing is retried
with different settings. Component counts by configuration: 840 / 846 / 827.*

| gate | binds | criterion | teeth |
|---|---|---|---|
| **GR** the rewrite reproduces V3 | the harness rewrite and the PROCESS copy, once, at the copy commit before any driver change | twenty V3 records (`R`/`B0`/`B3 start000`, `B3 start001`, `B1 start001` on the pulsed configurations, `A0`/`A1 start001`) reproduced bit-exactly on every count field and hex float through the rewritten harness against the copy; the only use of the V3→V4 name map | +1 on a count, 1 ULP on a hex, a missing reference record, a missing key, a bad name map — each must refuse, never skip |
| **G0** the copy's physics is frozen | every V4 commit | `PROCESS/process/models/` byte-identical to `c0ae5b28`'s | a 1-byte change to one model file is caught |
| **G1** every new switch off ⇒ byte identity | all V4 driver changes (decision (d)) | MFILE hex floats identical to a run at the pre-change commit, 3 configurations, both stamps recorded | a 1-ULP change to one float is caught |
| **G2** prime on, fixed-point map | the prime's inertness after call 1 | from each reference exit snapshot, one flat and one partitioned call, prime on vs off, exit states bit-identical on N/N components | a doctored snapshot component trips |
| **G3 / G3c** prime on, cold chain; lad carrier census | "no cut edge carries anything" | as V3, **re-run at the campaign commit** (item 7) | prime-off chain reproduces A35's counts — 244 (`large_tokamak_nof`) / 124 (`st_regression`) for G3, 240 cold / 218 displaced (`low_aspect_ratio_DEMO`) for G3c — and every residual maximum to the bit; the "3 outer passes → 2" half has nothing to count since DR1 removed the repeated schedule (A52) |
| **G4** audit restriction | the similarity statistic | a doctored `per_run`-owned component trips the whole-state audit and not the restricted one; a doctored in-loop component trips both; **one doctored component from each excluded namespace** (`costs`, `water_use`, `vacuum`, …) | both directions, every namespace |
| **G5** combined-switch equivalence | `B3` | the arm composed from the matrix equals the arm composed switch by switch: `norm_objf` hex, `ifail`, iterations, outer-pass histogram, exit audit hex | `norm_objf` hex and `n_call_models` teeth |
| **G6** Phase A entry and warm equivalence | Phase A | seed-paired entries bit-identical across arms per configuration; each block arm from the reference snapshot, pinned at the reference's converged burn time, reproduces the reference fixed point below τ with the pinned component bit-identical | as V3 |
| **G7** record completeness | the declared pairing and forensics | a forced-unconverged smoke run carries every declared field; a record with a field missing is refused by the tally | 5/5 field teeth |
| **G8** predicate trial (§3.6 gates 1–3) | the `mixed` mode | neutrality of `frozen`; the identity; the binding set | the doctored-component tooth |
| **G9** output-path equivalence | `MDA_Output` removal | on the intervention arms, the accepted state written by the new path is bit-identical to the state at the entry to `write_output_files`; on `BR`/`B0` nothing changes | a 1-ULP perturbation before `finalise` is caught |

### 3.10 Declared settings

*Caption: one row per knob: symbol, value, what it controls, provenance. None may change after
approval except by dated amendment.*

| setting | value | controls | provenance |
|---|---|---|---|
| N | 25 per configuration per arm, both phases | sample size | V3 (O2) |
| Phase A entry regimes | **δ = 0.10** (acceptance) and the **stencil regime** (`x_i (1 ± epsfcn)`, representative) | entry displacement | D15; item 1a as amended by A44 (2026-09-10) |
| δ (Phase B) | 0.10 | start displacement | D15 |
| τ | **1e-6 — the one tolerance of every MDA converger**: the flat loop and each block loop alike, every arm, both phases (D23) | convergence, and thereby the partitioned arms' handover accuracy | V2; user 2026-09-10; A43 (st-trust-gap) §6.1 gives the exchange rate should it ever be tightened |
| predicate mode | `frozen` (default) and `mixed` (trial) | the denominator of the scaled step | item 5a |
| F | 10 | similarity (A) and same-optimum (B) factor, median and p90 | V2 App. B |
| floor | 1e-6 relative on `norm_objf` | same-optimum yardstick floor | V3 (O3) |
| cluster gap | 10 × floor = 1e-5, with the resolution category declared | check 1a/1b | V3; item 5 |
| iteration bound | median paired ratio ≤ 1.05 | check 2 | V2 App. B |
| median | nearest-rank, upper-middle (`sorted[n // 2]`) | every Phase B check | V3 |
| inner cap | 20 sweeps per block; a cap hit is a refusal | partitioned arms | V2 |
| upstream cap | 10 passes (raises) → `unconverged-at-cap` | `AR`/`BR` | upstream; item 1 |
| W | 3 | worker pool | V2 |

**Run budget (context).** Phase A: `AR` 75 + `A0` 75 + `A0p` 50 + `A1` 75 = 275 single
evaluations at δ = 0.10, plus the stencil regime — `2(nvar+1)` per arm per configuration:
42 × 4 (nof) + 40 × 4 (lad) + 30 × 3 (st) = 418 — plus 150 under the `mixed` mode, plus gates;
V3's 225 took ≈ 1.5 h at W = 3. Phase B: 4 arms × 25 × 2 pulsed + 3 arms × 25 on st = 275 optimisations (V3: 350; `B2`
removed; ≈ 2.5–3 h at W = 3), plus `B0`/`B3` under `mixed` (≤ 150) only if Phase A licenses it.

### 3.11 Scope honesty, declared in advance

One code at one commit, three configurations (three case studies unless decision (b) adds a
fourth), tokamak only, one partitioning, one lift, one optimiser, one perturbation stream at two
amplitudes. Per-configuration conclusions; configurations are never pooled, and the
cross-configuration spread in any cost result is not physics — the three optimisation problems
differ in objective, variable count and constraint count. No robustness claim (the powered
campaign stays deferred). No claim that the arms reach the same design point (D6 gates
optimality, not location; the location diagnostic is published beside). The prime's full-run
neutrality is not claimed. No timing is evidence.

---

## 4. Results *(placeholder — format for review; every cell is a placeholder, nothing is measured)*

**How to read this section before the campaign.** Each table below is the exact shape the
committed analysis emits. Cells show the *format* of the value that will appear — `0.xxx` a ratio to
three decimals, `n` an integer count, `[lo, hi]` the seed bracket (minimum and maximum over the
seeds in the table's population), `[hex]` a hex-float, `s` seconds — never a number. Every table
carries a caption stating units, what a row and a column are, the population the cells summarise
and the construction that produced them, followed by a short *how to read* note. Configurations
appear in the fixed order **nof / lad / st** and are never pooled (D21 (b)): a table with three
configuration blocks is three tables sharing one header, and no row spans them.

**Conventions that hold in every table (D21 (c)).** Absolute cost cells are **per-run means with
the seed bracket**. A ratio against the reference is given three ways: **pooled** (sum over the
set / sum over the set — the campaign's cost), **per-run median** with `[min, max]` (the typical
run), and **worse** (the count of seeds on which the arm cost more than the reference). Every Phase
B table is over **one seed set per configuration** — the seeds on which *every* arm converged
(`status == ok` and MFILE `ifail == 1`) — with its `n` in the header; the seeds outside it are in
the failure table (4.3.1), never dropped silently. **Retries are a term:** a run's node calls are
recorded per VMCON attempt, retried seeds are counted per arm, and every ratio that could contain a
retry is published *with* and *without* retried seeds. Prime calls appear as a column beside node
calls, never inside them (D19). Node-call ratios are the acceptance quantities; timings are context.

### 4.1 Gates

*Caption: one row per registered gate, emitted by `experiment_runner.py --measure gate_table` from the verdict
records of one from-scratch press of `--gate all --census-entry evaluation` from the repository root at commit
`eb38c34a` (A52 (harness-gates); records under `runs/gates/`, untracked, relocated to `arch_surgery/idf_probe/runs/A52_runs/gates/` at the task's
retirement). "Plan" is the §3.9 label, empty for the harness's own checks promoted into the same framework. "Verdict"
is PASS on the criterion **and** on every tooth. "Compared" is the denominator and "mismatched" the count that
differed; where a gate compares more than one kind of thing the record names each part. The frozen-physics row reads
1 mismatched and PASS: the one model file the user approved under D11, by name. G1's row states what it straddles; a
same-commit G1 says so and is not a neutrality result. Every verdict also records the commit of every run record it
read — all at one commit here. Re-taken by the button at every later commit; this is the state at A52's merge.*

| gate | plan | binds | verdict | population | compared | mismatched | teeth | record |
|---|---|---|---|---|---|---|---|---|
| `g0prime` | G0 / G0' | every V4 commit, every arm, both phases | **PASS** | 77 files under PROCESS/process/models/ compared byte for byte against c0ae5b28 (git cat-file, never a working tree), plus the file set | 77 | 1 | 4/4 | `runs/gates/g0prime/gate.json` |
| `composition` | — | the harness itself, before any PROCESS run | **PASS** | 8 arms x 3 configurations = 24 pairs | 42 | 0 | 7/7 | `runs/gates/composition/gate.json` |
| `rungs` | — | the harness itself, before any PROCESS run | **PASS** | 11 matrix rows x 8 arms = 88 cells; 6 rung steps | 98 | 0 | 3/3 | `runs/gates/rungs/gate.json` |
| `provenance` | — | the harness itself, before any PROCESS run | **PASS** | one scratch repository, three states | 4 | 0 | 4/4 | `runs/gates/provenance/gate.json` |
| `data` | — | the harness itself, before any PROCESS run | **PASS** | 16 committed file(s) in harness/data/ + the moved predicate module = 17 comparisons; and 9 declared counts (3 configurations x coupling-state compo… | 17 | 0 | 6/6 | `runs/gates/data/gate.json` |
| `run_path` | — | the harness itself, before any PROCESS run | **PASS** | 2 phases x the declared field list; 2 displacement streams; 4 refusals | 9 | 0 | 12/12 | `runs/gates/run_path/gate.json` |
| `capability` | — | the harness itself, before any PROCESS run | **PASS** | every arm/configuration pair whose arms are active | 55 | 0 | 15/15 | `runs/gates/capability/gate.json` |
| `artifacts_check` | — | every committed artifact of every configuration | **PASS** | 19 artifact row(s) over 3 configuration(s) (large_tokamak_nof, low_aspect_ratio_DEMO, st_regression); 95 individual check(s) | 95 | 0 | 3/3 | `runs/gates/artifacts_check/gate.json` |
| `artifacts_derive_inputs` | — | the lifted input file of each pulsed configuration | **PASS** | 3 configuration(s) (large_tokamak_nof, low_aspect_ratio_DEMO, st_regression); the digest gate applies to the 2 pulsed one(s) | 2 | 0 | 4/4 | `runs/gates/artifacts_derive_inputs/gate.json` |
| `artifacts_census` | — | the committed run-time write census, per configuration | **PASS** | 3 configuration(s) (large_tokamak_nof, low_aspect_ratio_DEMO, st_regression); one evaluation census each, taken with the read half of the instrumen… | 81 | 0 | 2/2 | `runs/gates/artifacts_census/gate.json` |
| `artifacts_per_run` | — | each configuration's per-run deferral set | **PASS** | 5 (configuration, input file) pair(s) over 3 configuration(s) (large_tokamak_nof, low_aspect_ratio_DEMO, st_regression); the write census is measur… | 16 | 0 | 2/2 | `runs/gates/artifacts_per_run/gate.json` |
| `record_completeness` | G7 | the declared pairing and the failure forensics, in both phases | **PASS** | 2 runs on st_regression (the configuration with the fewest iteration variables, derived); 85 declared field(s) in the optimisation phase and 78 in … | 163 | 0 | 9/9 | `runs/gates/record_completeness/gate.json` |
| `prime_map` | G2 | the claim that the arrangement's method-level move changes nothing once the first-wall mod | **PASS** | 6 arrangement/configuration pair(s); 12 evaluations; 5026 components compared | 5026 | 0 | 2/2 | `runs/gates/prime_map/gate.json` |
| `cold_chain` | G3 / G3c | the claim that with the method-level move in place no cut edge carries a stale value into  | **PASS** | 8 chain/composition pair(s) over 4 chain(s); 16 evaluations | 60 | 0 | 4/4 | `runs/gates/cold_chain/gate.json` |
| `audit_restriction` | G4 | the similarity statistic, on every configuration | **PASS** | 13 doctored run(s) over 3 configuration(s), each against that configuration's undoctored run; namespaces derived per configuration | 12 | 0 | 5/5 | `runs/gates/audit_restriction/gate.json` |
| `entry_and_warm` | G6 | the evaluation phase, on every configuration | **PASS** | 5 entry pair(s) at seed 1; 5 warm run(s); 13 evaluations | 4204 | 0 | 3/3 | `runs/gates/entry_and_warm/gate.json` |
| `switch_composition` | G5 | B3, on every configuration where it is active | **PASS** | 3 configuration(s) where B3 is active; 6 optimisations; 37 switch names and 10 run values per configuration | 141 | 0 | 3/3 | `runs/gates/switch_composition/gate.json` |
| `switch_neutrality` | G1 | each driver change, run per change and never batched | **PASS** | straddles 5e64ce0e -> eb38c34a: a neutrality result.  6 run pair(s) = 3 configuration(s) x 2 reference arm(s); 3164 deterministic record values and… | 54483 | 0 | 6/6 | `runs/gates/switch_neutrality/gate.json` |
| `reproduction` | GR | the harness rewrite and the experiment's copy of PROCESS, once, at the copy commit before  | **PASS** | 20 runs (14 optimisations + 6 evaluations) over 3 configurations; 270 compared values, no tolerance on any of them | 270 | 0 | 7/7 | `runs/gates/reproduction/gate.json` |
| `output_path` | G9 | the removal of the output-time loop from the arms whose matrix cell turns it off, on every | **PASS** | 11 run(s) at seed 0 = every optimisation-phase arm on every configuration where it is active, each composed from the experiment's matrix; 3825 coup… | 3879 | 0 | 4/4 | `runs/gates/output_path/gate.json` |
| `predicate_mode` | G8 | the convergence predicate's second ruler, on the evaluation-phase arms of every configurat | **PASS** | 12 pair(s) = 3 configuration(s) x the evaluation-phase arms active on each (A0, A1) x 2 seed(s), each run under both rulers = 24 runs at delta = 0.… | 7684 | 0 | 4/4 | `runs/gates/predicate_mode/gate.json` |

**21 PASS, 0 FAIL, 0 not run; 109 of 109 teeth tripped** (at `eb38c34a`).

*How to read: no number in §4.2–§4.4 is cited unless every row here is PASS with its tooth tripped;
a FAIL is a result and the dependent tables are marked "not produced — gate X failed".*

### 4.2 Phase A

#### 4.2.1 Cost per call, δ = 0.10 regime

*Caption: per configuration and arm, model-node executions per `call_models` evaluation (the cost
unit), dispatch sweeps per evaluation, sweeps per block for the partitioned arm, and prime calls per
evaluation, as per-run means with the seed bracket over the arm's `ok` runs out of 25; ratios are
pooled (sum/sum) over the seeds on which both arms are `ok`, with the per-run median `[min, max]`
and the count of seeds where the arm cost more. `A0p` is the declared reference for `A1` on the
pulsed configurations (same reduced map); `A0` on st, where `A0p` is skipped. `AR`'s ratio appears
only in 4.2.2, beside its audit residual.*

| config | arm | ok/25 | node calls / eval | sweeps / eval | M1 / M2 / M3 sweeps | prime calls / eval | vs `A0` pooled · median [min, max] · worse | vs `A0p` pooled · median · worse |
|---|---|---|---|---|---|---|---|---|
| nof | `AR` | n | nn.n [nn, nn] | n.nn | — | 0 | *(4.2.2 only)* | — |
| nof | `A0` | n | nn.n [nn, nn] | n.nn | — | 0 | 1 | — |
| nof | `A0p` | n | nn.n [nn, nn] | n.nn | — | 0 | 0.xxx · 0.xxx [0.xxx, 0.xxx] · n | 1 |
| nof | `A1` | n | nn.n [nn, nn] | n.nn | n.nn / n.nn / n.nn | n.n | 0.xxx · 0.xxx [0.xxx, 0.xxx] · n | **0.xxx** · 0.xxx [0.xxx, 0.xxx] · n |
| lad | … | | | | | | | |
| st | `A0p` | skipped (k = 0) | — | — | — | — | — | — |
| st | `A1` | n | nn.n [nn, nn] | n.nn | n.nn / n.nn / n.nn | n.n | **0.xxx** · 0.xxx [0.xxx, 0.xxx] · n | — |

*How to read: the bold cell is the Phase A cost headline per configuration (RQ1). A pooled ratio
below 1 with "worse = 0" means the partitioned arm was cheaper on every seed; a median far from the
pooled value means a few seeds carry the campaign cost — look at the bracket. Prime calls are the
work D19 excludes from node calls; a reader who wants them charged adds the column.*

#### 4.2.2 Matched accuracy, and where upstream's stopping rule leaves the coupling state

*Caption: per configuration and arm, the exit-audit maximum scaled residual (dimensionless, on the
declared ruler, §3.6) over the components **not owned** by the configuration's `per_run` node set
(restricted) and over all components (whole state), median and p90 over `ok` runs; the similarity
verdict for the declared pair at F = 10 (both median and p90 within a factor 10); and `AR`'s
node-call ratio against `A0`, which may appear **only** here, beside both arms' audit residuals
(§3.3). "0" is an exact zero.*

| config | arm | restricted median · p90 | whole-state median · p90 | pair | similar at F = 10 (median · p90) | `AR/A0` node calls |
|---|---|---|---|---|---|---|
| nof | `AR` | x.xe−x · x.xe−x | x.xe−x · x.xe−x | — | — | 0.xxx |
| nof | `A0` | x.xe−x · x.xe−x | x.xe−x · x.xe−x | — | — | 1 |
| nof | `A0p` | x.xe−x · x.xe−x | x.xe−x · x.xe−x | `A0p/A0` | yes/no · yes/no | — |
| nof | `A1` | x.xe−x · x.xe−x | x.xe−x · x.xe−x | **`A1/A0p`** | **yes/no · yes/no** | — |
| lad | … | | | | | |
| st | `A1` | x.xe−x · x.xe−x | x.xe−x · x.xe−x | **`A1/A0`** | **yes/no · yes/no** | — |

*How to read: the restricted column is the declared statistic; the whole-state column will be
large for the partitioned arms by design (their `per_run` nodes run once, so those outputs are
stale at audit) and is published to show the exclusion's size, not judged. `AR`'s row answers RQ4:
a restricted residual ≫ τ means upstream's rule leaves the MDA under-converged and its cheaper
`AR/A0` is bought with accuracy; ≈ τ means the two rules are accidentally equivalent; ≪ τ means
upstream over-solves. The ratio and the residual are read together or not at all.*

#### 4.2.3 The ownership rung, `A0 → A0p` (pulsed configurations)

*Caption: per configuration, the cost and accuracy of taking the burn time out of the flat loop and
holding it constant at the seed's perturbed value. Node-call ratio pooled and per-run median over
seeds where both arms are `ok`; `burn_time_residual` is constraint 93's function at exit — how far
the pinned value sits from the value the coupling would have produced — in seconds and relative to
the burn time, median `[min, max]` over `A0p` runs (it is 0 by construction in `A0`).*

| config | n | `A0p/A0` pooled · median [min, max] · worse | `A0p` restricted audit median · p90 | burn-time residual s median [min, max] | relative |
|---|---|---|---|---|---|
| nof | n | 0.xxx · 0.xxx [0.xxx, 0.xxx] · n | x.xe−x · x.xe−x | nnn [nn, nnn] | x.xe−x |
| lad | n | … | … | … | … |

*How to read: this rung is the one where Phase A and Phase B differ in kind (a constant here, the
optimiser there). Its node-call ratio is the loop's cost of converging the burn time; its residual
is the price of the pin. Neither is a claim about the partition.*

#### 4.2.4 Two entry regimes

*Caption: per configuration and regime — δ = 0.10 (acceptance) and the stencil regime's forward
(`E3`) and backward (`E3b`) sets — the per-evaluation means of node calls for each arm and the
per-evaluation-mean ratios, beside the in-loop values measured in Phase B over the one seed set
(`ρ_B = B3/B0`, and `B3/B1`). n is the number of entries per arm (25 seeds; `nvar` or `nvar + 1`
stencil points).*

| config | regime | n | `A0` calls/eval | `A0p` calls/eval | `A1` calls/eval | `A1/A0` | `A1/A0p` | in-loop `ρ_B` | in-loop `B3/B1` |
|---|---|---|---|---|---|---|---|---|---|
| nof | δ = 0.10 | 25 | nnn.n | nnn.n | nn.n | 0.xxx | 0.xxx | 0.xxx | 0.xxx |
| nof | stencil fwd | nn | nn.n | nn.n | nn.n | 0.xxx | 0.xxx | ″ | ″ |
| nof | stencil bwd | nn | nn.n | nn.n | nn.n | **0.xxx** | **0.xxx** | ″ | ″ |
| lad | … | | | | | | | | |
| st | … | | | — | | | — | | — |

*How to read: the δ = 0.10 rows are the acceptance regime and the carrier detector; the stencil
rows are the representative regime, and the bold cells are what the transfer (4.4) uses. The test
of RQ3's regime hypothesis is whether the stencil-row ratio lands within the in-loop value's
per-seed spread (given in 4.4) while the δ = 0.10 ratio does not.*

#### 4.2.5 The predicate trial (`frozen` vs `mixed`)

*Caption rule added 2026-09-11 (A59 (driver-predicate-mode)): "decisive passes" is published as **two counts** — evaluations at which some component crossed τ between the rulers, and evaluations whose **verdict changed** (the crossing component was the one holding the evaluation open). Only the second can make two runs differ; G8 binds on it. A59's 24 gate runs: 13 crossings, 0 verdicts changed, 48 distinct components, `|y|/s` up to 54.6.*

*Caption: per configuration and arm at δ = 0.10, the runs under each predicate mode: decisive
passes (a component at or above τ on `frozen` and below it on `mixed`) as a count over runs; the
components that made passes decisive, with `|y_i| / s_i` there; node calls per evaluation under each
mode and their ratio; the exit audit **on both rulers**. The adoption outcome per §3.6 is stated
below the table.*

| config | arm | runs | decisive passes (runs) | components (`\|y\|/s`) | calls/eval frozen · mixed · ratio | audit frozen median · mixed median |
|---|---|---|---|---|---|---|
| nof | `A0` | 25 | n / 25 | `ns.field` (nn), … | nnn.n · nnn.n · 0.xxx | x.xe−x · x.xe−x |
| nof | `A0p` | 25 | n / 25 | … | … | … |
| nof | `A1` | 25 | n / 25 | … | … | … |
| lad · st | … | | | | | |

**Adoption outcome:** *neutral / non-neutral on the named set / blocked by gate G8 — one sentence,
with the moved ratios re-stated as metric-dependent if non-neutral.*

*How to read: a run with no decisive pass is bit-identical under both modes (G8's identity), so
every difference in this table is attributable to the named components. Both audit columns must be
read together: the mixed ruler reads lower wherever the term binds — a change of ruler, not an
accuracy gain.*

#### 4.2.6 Failure taxonomy

*Caption: per configuration, regime and arm, the disposition of every scheduled run with its
denominator: `ok`; `crashed` (machinery, with the error class); `refused` (a preflight or
composition refusal, by name); `unconverged` (inner or outer cap); `unconverged-at-cap` (`AR` only:
upstream's ten-pass loop raised); `infeasible-at-audit`; `skipped` (arm inactive on the
configuration, by reason). Rows sum to the denominator.*

| config | regime | arm | denominator | ok | crashed | refused | unconverged | unconverged-at-cap | infeasible-at-audit | skipped (reason) |
|---|---|---|---|---|---|---|---|---|---|---|
| nof | δ = 0.10 | `AR` | 25 | n | n | n | n | n | n | 0 |
| nof | δ = 0.10 | `A0p` | 25 | n | … | | | — | | 0 |
| st | δ = 0.10 | `A0p` | 25 | 0 | 0 | 0 | 0 | — | 0 | 25 (k = 0, composes to `A0`) |
| … | | | | | | | | | | |

*How to read: `unconverged-at-cap` on `AR` is a finding about the shipped code, not a machinery
failure; a nonzero `crashed` column is a machinery result that must be explained before any ratio in
this configuration is cited.*

### 4.3 Phase B

#### 4.3.1 The seed set, and the failure table

*Caption (seed set): per configuration, the number of seeds on which every arm converged — the one
population for every Phase B table — and, per arm, the count of those seeds on which the arm
retried a VMCON attempt.*

| config | arms | n (every arm converged) | retried seeds: `BR` · `B0` · `B1` · `B3` |
|---|---|---|---|
| nof | 4 | nn / 25 | n · n · n · n |
| lad | 4 | nn / 25 | … |
| st | 3 (`B1` skipped) | nn / 25 | n · n · — · n |

*Caption (failure table): per configuration, every seed **outside** the set: which arm(s) failed,
each failed arm's `ifail`, attempts and solve-phase node calls, and the other arms' node calls on the
same seed, so a failure's cost is visible beside what the other arms paid at the same start. A seed
failing in every arm is marked configuration-invalid (configuration hardness, not an arm effect).*

| config | seed | failed arm(s) | `ifail` | attempts | failed arm node calls | other arms' node calls (`BR` / `B0` / `B1` / `B3`) | configuration-invalid |
|---|---|---|---|---|---|---|---|
| lad | k | `B0`, `BR` | 5, 5 | 1, 1 | nn nnn, nn nnn | — / — / nnn nnn / nnn nnn | no |
| lad | k | all | 5 ×4 | 1 ×4 | … | … | **yes** |
| st | k | `B3` | 5 | 2 | nnn nnn | nnn nnn / nnn nnn / — / — | no |

*How to read: the converged set is the fairer cost population, but it can flatter an arm that fails
on expensive seeds — this table is what keeps it honest. A `B3`-only failure that cost several
times a converged run is a robustness event and is reported as one.*

#### 4.3.2 Same optimum (check 1)

*Caption: per configuration and arm pair over the seed set, the paired relative objective difference
`r = |Δ norm_objf| / max(|a|, |b|)` at accepted optima — median and p90 (nearest-rank) — against the
threshold `max(F × yardstick, floor)` with the yardstick the `BR → B0` spread measured in the same
campaign, F = 10, floor = 1e-6; the verdict; hops (seeds whose two sides land in different
`norm_objf` clusters, gap 1e-5) and the hop rate; the within-cluster statistics; and the count of
pairs that are distinct optima below cluster resolution (1e-6 < r < 1e-5).*

| config | pair | n | r median · p90 | threshold median · p90 | **verdict** | hops (rate) | within-cluster median · p90 | below-resolution | retried seeds in pair |
|---|---|---|---|---|---|---|---|---|---|
| nof | `BR → B0` (yardstick) | nn | x.xe−xx · x.xe−xx | — | — | n (0.xx) | … | n | n |
| nof | `B0 → B1` | nn | x.xe−x · x.xe−x | x.xe−x · x.xe−x | PASS/FAIL | n (0.xx) | x.xe−x · x.xe−x | n | n |
| nof | `B0 → B3` | nn | … | … | **PASS/FAIL** | … | … | n | n |
| lad · st | … | | | | | | | | | |

*How to read: the pre-declared expectation is that the error at the stencil regime is within ±5 %
(A44 (transfer-gap) measured ≤ 1 % at the backward points on V3's records) while δ = 0.10 leaves
6–23 %; a `ρ_B` bracket that is wide (st in V3) means the per-evaluation ratio depends on the
optimiser's path and the agreement is "inside the spread", not "at the value". What the transfer
cannot predict is the problem-call ratio — a Phase B result about the optimiser's response to the
lift and, on st, to the partition.*

---

## 5. Discussion *(placeholder)*

To be written from §4 only, under the following pre-declared headings so that the discussion
cannot drift toward what was hoped for: (i) what each rung measured, per configuration, against
its pre-declared expectation, with refuted expectations named as such; (ii) the transfer — which
factor carried the gap, and what that says about Phase A as a predictor; (iii) the stopping
rule — where upstream's test leaves the coupling state, and what the predicate-matched control
therefore is a control *for*; (iv) the trust step — what `B2 → B3` says about completeness of
the decomposition after A43; (v) the per-sweep overhead — whether the counted term is of the
size the wall-clock gap requires; (vi) the predicate trial's outcome and what it changes;
(vii) threats to validity that survived the design: the objective/structure confound under
decision (b), small denominators where a configuration is hostile, location non-identification,
the prime's excluded cost.

## 6. Conclusion *(placeholder)*

One paragraph per research question RQ1–RQ5, each answered per configuration with its number,
its denominator and its acceptance verdict, followed by the single sentence the experiment
licenses about the research question in §1.2 — and the sentence it does not.

---

## Appendix A — Directory and run discipline

New directory `arch_surgery/MDA_partitioning_experiment_v4/`, mirroring V2/V3 at the top level.
**V2's and V3's directories are not edited.** Every published number is produced by executing a
committed script (protocol §15); the script is committed before its numbers are published, and
the report names the script and the commit per figure. Every table carries a caption (§16).
Every PROCESS run is a fresh subprocess in its own directory under `PROCESS_surgery_env`, with
`process.__file__` asserted against the tree. Bulk run artifacts stay untracked; tallies and
verdicts are committed. Failure paths — dropped seeds, refused arms, failed gates — are
reachable from the same entry point as the successes.

*Caption: one row per top-level file: name and role; the `harness/` package's internals are the
implementation plan's.*

| file | role |
|---|---|
| `EXPERIMENT_PLAN.md` | this document (no version token in file names inside the versioned folder — user, 2026-09-10); every later change a dated amendment |
| `EXPERIMENT_REPORT.md` | the report, written from the committed analysis only |
| `experiment_runner.py` | one-button entry point; draft mode; refuses the campaign until approved |
| `phase_a.py` | preflight / artifacts / reference / gates / campaign (`AR`, `A0`, `A0p`, `A1`; two amplitudes; predicate trial) / tally |
| `phase_b.py` | preflight / gates / campaign (`BR`, `B0`, `B1`, `B3`) / tally / timing context |
| `PROCESS/` | V4's own copy of the PROCESS package (D20); every V4 driver change lives here; `models/` frozen at `c0ae5b28`, gated. `PROCESS/PROVENANCE.json` names the source commit (`f2dc9243`) and every file's sha256; `PROCESS/copy_gates.py` is the copy-identity gate, G0′ and the smoke import, nine teeth (A46 (process-copy), merged 2026-09-10) |
| `PROCESS_diff.py` | shows every change the experiment made to PROCESS: a `git diff` of `PROCESS/process/` against the copy's source commit, grouped by file with a plain-language overview (user, 2026-09-10) |
| `harness/` | the self-contained package (per the implementation plan); every verification gate is implemented here |
| `runs/` | untracked bulk artifacts |
| `.gitignore` | `runs/` untracked; the copy's `.dat` files re-included against the repository-root `*.dat` pattern (added at A46's merge) |

## Appendix B — Traceability to the improvement list

*Caption: one row per improvement-list item: where this plan absorbs it, or why not.*

| item | absorbed in | status |
|---|---|---|
| 0 prime inside the intervention; `A1u` retired | §3.2, §3.3 | decided (user) |
| 1 `AR`/`BR`; `unconverged-at-cap`; G0 refusal | §3.3, §3.4 check 4, §3.9 | decided (user) |
| 1a second amplitude | §3.4, §3.10 | recommendation (a) |
| 1b `MDA_Output` out of the intervention arms | §3.3, §3.9 G9 | decided (user); driver change (d) |
| 1c `A0p` | §3.2, §3.3, §3.4 | decided (user) |
| 1d naming | §3.2 | decided (user; `per_call`) |
| 2 empty blocks / nodes | §3.3 | driver change (d) |
| 3 per-sweep counters | §3.5 check 5 | driver change (d) |
| 4 objective/structure confound | §3.7 (b) | open |
| 5 clusters vs floor | §3.5 check 1b | declared resolution category |
| 5a predicate trial | §3.6, §3.9 G8 | pre-declared; driver change (d) |
| 5b one seed set, one format | §3.5, §3.7 (c) | recommendation (c) |
| 6 within-cluster in both implementations | §3.5 check 1a | absorbed |
| 6a class-level classification; read census; Phase A provenance; G4 per namespace | §3.8 (ii), §3.9 G4 | absorbed |
| 7 G1–G3c at the campaign commit | §3.9 | absorbed |
| 8 `B2` in the DSM overlay | — | **dropped** with `B2` (user, 2026-09-10) |

## Appendix C — Change log

- 2026-09-10 — written by the orchestrating session at the user's instruction; status
  **DRAFT · NOT APPROVED**; decisions (a)–(f) open; A43 and A44 running, to be absorbed as
  dated amendments.
- 2026-09-10 — §3.5: retry attempts made an explicit term of the Phase B cost format, on
  A44's preliminary finding (committed on its branch, not yet reviewed) that lad's V3
  headline is dominated by one retried seed.
- 2026-09-10 — §3.4, §3.5, §3.7(a), §3.10, §4: the second Phase A entry regime is the
  **stencil regime**, not δ = 0.001, and the transfer is restated as `ρ_A(stencil) × stencil-column
  factor × problem-call ratio` with `ε = 1` pre-declared on `B1 → B2 → B3` (pulsed) — on A44's
  completed probe (472/472 ok, gates with teeth; report at `b01fccec`, assessment sent, task still
  provisional pending the user).
- 2026-09-10 — user rulings (D20, D21) recorded in §3.3, §3.7, §3.8, §3.9, Appendix A; §4 rewritten as
  placeholder tables in the accepted format (one seed set, failure table, three-way ratios, retries as
  a term, captions and how-to-read notes) for the user's review before any run; the PROCESS copy
  described in §3.8 (i) and gated (GR, G0).
- 2026-09-10 — user: the harness refactor is **approved** with three notes (no task numbers or
  version tokens in file/method names, heritage in docstrings; a `PROCESS_diff.py` overview of every
  change to PROCESS; a plain-language README with the terminology) — applied to the harness plan
  §11 and to this file's name (`V4_EXPERIMENT_PLAN.md` → `EXPERIMENT_PLAN.md`). Decision (g) ruled
  (D23: one tolerance for every converger, τ = 1e-6). Check 2's directive explained; stands.
- 2026-09-10 — A43 (st-trust-gap) merged and absorbed: `st_regression` stays (D22's conditional
  answered *no*); the intervention arms' certificate stated (§3.3); decision (g) opened — the inner
  tolerance of `A1`/`B3`, recommended 1e-8 (§3.7, §3.10); check 2's acceptance construction declared
  (P2); a retried-seeds column added to check 1's table (P3); header updated.
- 2026-09-10 — check 2's summed-over-attempts acceptance construction **confirmed by the user**
  ("check-2 accepted indeed"); decision (g) closed by D23 the same day.
- 2026-09-10 — check 2 (§3.5, §4.3.3): iterations published in two constructions, final attempt
  and summed over all VMCON attempts, with per-seed attempt counts — user directive relayed by
  session `process-surgery-bd`, marked for confirmation in the orchestrating session.
- 2026-09-10 — user rulings of the second round (D22): `B2` removed from the matrix (§3.2, §3.3,
  §3.5, §3.10, §4, App. B) with the pre-declared rule on `st_regression`; predicate counters
  accepted; no errata to the V3 report; the PROCESS copy taken at the current tip and checked
  against `git show`; predicate and artifacts under `harness/` (§3.8 (i)).
- 2026-09-10 — **A46 (process-copy) merged** (`38057e27`): the PROCESS copy of §3.8 (i) exists at
  `f2dc9243` and is gated (`copy-identity`, G0′; nine teeth); `PROCESS_diff.py` in place. Appendix A:
  `PROCESS/` row extended, `.gitignore` row added, `phase_b.py` row corrected (`B2` was removed by D22
  and had survived in the row). Two facts for the run path: without `PYTHONPATH` the import lands in
  the main checkout, and `process.__version__` is identical for both trees (traps T6/T10) — every
  child asserts `process.__file__` for equality against the copy.
- 2026-09-10 — **terminology and two rung corrections at A47 (harness-skeleton)'s assessment**
  (orchestrator, applying harness plan §11.2): "deck" removed — the file is the **input file**,
  *committed* or *lifted*; "frozen" is reserved for the physics freeze and the predicate mode;
  the matrix row reads `input file ⁺ | committed | … | lifted`; "deck-invalid" seeds are
  "configuration-invalid". The output-time-loop row is `n/a` for the four Phase A arms (an
  evaluation never reaches the output path; `A1` no longer waits on DR2), and §3.3's keep-list
  is `BR`, `B0`. The `B0 → B1` rung's *isolates* wording now names the output-time loop, Phase B
  only, with the reason it sits on that rung (the alternative — moving the change to `B3` —
  would put a Phase-B-only field on the headline rung and break its twin with `A0p → A1`).
- 2026-09-10 — **A47 (harness-skeleton) merged**; the two rulings of the previous entry **approved by
  the user (D24)**, who also delegated the remainder of the rebuild to the orchestrator (tasks
  A48–A60 minted; the campaign still waits for `EXECUTION_APPROVED`). The harness regenerates this
  plan's §3.2 matrix cell for cell from its arm records and refuses a rung whose computed difference
  is not the declared one.
- 2026-09-10 — **A50 (harness-run) merged; gate GR PASSES**: the rewritten harness reproduces V3's
  twenty reference runs on 270/270 compared values with no tolerance, against the untouched PROCESS
  copy, re-run independently by the orchestrator; seven teeth trip, the `A0p` and `AR` substitutes
  pass. §3.3: the audit position's implementation stated (snapshot at the declared entry, residual
  after the run; hook with A57). The composition tooth measured that `PROCESS_ARCH_OUTER` is still
  load-bearing for the partitioned arms until A56 folds it into `partitioned`.
- 2026-09-10 — **A56 (driver-renames) merged — DR1**: the copy's switches carry the §11.2 names; `PROCESS_ARCH_OUTER`
  removed (the partitioned loop runs its schedule once, the verified-schedule code deleted), `INNER_TAU` retired, the
  lift and pin folded into the burn-time owner; a typed refusal. Gates G0′, G1 (0 differences over 2 383 values and
  51 319 output lines) and GR after the rename (270/270) all PASS, re-run by the orchestrator. §3.2: the matrix row
  "outer loop" is now "block schedule" (`one pass`), the rung wording and the switch list follow.
- 2026-09-10 — **A57 (driver-output-path) merged — DR2**: `PROCESS_ARCH_OUTPUT_LOOP = upstream | none` in the copy;
  the exit audit at the declared position via a bit-exact snapshot; G0′, G1 (failed once on its own exclusion set,
  fixed, reported), G9 (0/3 825 components) and GR after DR2 (270/270) all PASS, re-run by the orchestrator. §3.2's
  switch list and §3.3's audit note updated; the `tfcoil.insstrain` signal recorded in §3.3 and on the improvement
  list. `B1`/`B3` are now runnable in the campaign composition; GR keeps a recorded `upstream` override for them.
- 2026-09-10 — **A58 (driver-predicate-counters) merged — DR4**: predicate evaluations, components compared, block visits,
  empty visits and the sweeps they cost, and dispatch sweeps counted in the copy and recorded in both phases; G0′, G1 and
  GR after DR4 PASS, re-run by the orchestrator. Improvement item 3's hypothesis closed in the negative on counts: the
  partitioned arm compares 33–47 % fewer components than the flat control, tracking its node calls to within 0.02 — the
  convergence test is not the per-sweep overhead; what that overhead is stays open (§3.5 check 5 will report the
  remaining candidates). §3.3's empty-blocks paragraph gains the measured shares; I-20(a) extended in the register.
- 2026-09-11 — **A59 (driver-predicate-mode) merged — DR5**: the `frozen | mixed` rulers of §3.6 in the harness's predicate module,
  selected in the copy by `PROCESS_ARCH_PREDICATE` (campaign default `frozen`); the exit audit on both rulers, never one; gate G8
  built and passing (12/12 pairs bit-identical with an independent detector; doctored-component tooth); G0′, G1 and GR after DR5
  PASS, all re-run by the orchestrator. §4.2.5 gains the two-counts caption rule. Adoption of `mixed` is the campaign's decision
  by the adoption rule, not made here.
- 2026-09-11 — **A60 (driver-attempts) merged — DR7; the driver chain is closed.** Every optimisation record carries the
  cost of each retry-ladder attempt with the summation identity enforced (§3.5 check 2's two constructions and the
  with/without-retried-seeds ratios are now computable from the record); G0′, G1 and GR after DR7 PASS, re-run by the
  orchestrator. The five driver changes of §3.8 have all landed in the copy; from here only the harness changes.
- 2026-09-11 — **A52 (harness-gates) merged — H5; every gate inside the harness, on one button** (`d13a54c7`). G2–G7 built, GR/G1/G8/G9 registered, the self-checks and artifact stages promoted; `--gate all` 21 PASS,
  109/109 teeth, from the repository root and from the experiment directory, every run re-made at one commit; GR 270/270;
  G1 run as a genuine two-tree straddle `5e64ce0e → eb38c34a` (0 of 3 164 values, 0 of 51 319 lines; 70-name exclusion
  set reviewed). §4.1 filled from the verdict records; §3.9's G3 tooth cell corrected (244 nof / 124 st; 240 / 218 lad).
  Six defects found at the orchestrator's review and fixed on the branch, among them `--resume` not reaching the gates'
  runs (verdicts now name the commits of the runs they read) and the capability probe's working-directory dependence.
  Rule: no commit while measurement runs execute. Finding: `tfcoil.insstrain` above τ at the accepted point on the
  reference arm too (item 11); **A61 (insstrain-diagnosis)**, dispatched in parallel, classifies it as an artefact of the
  exit-audit instrument — the output path raises `tfcoil.n_rad_per_layer` from 100 to 500 before the snapshot and the
  snapshot does not restore it — to be verified at A61's merge; if it holds, §3.3's audit restores the whole data
  structure and the "one component above τ" statements of A57/A52 are withdrawn as convergence statements.
- 2026-09-11 — **A61 (insstrain-diagnosis) merged** (`fd480aff`): item 11 diagnosed before the campaign. The exit-audit
  residual on `tfcoil.insstrain` is an artefact of the audit instrument (the output path's TF-coil stress mesh, 100 → 500,
  not restored by the coupling-state snapshot), not of convergence; `B0`/`B3` converged to τ. §3.3's implementation note
  amended; **D25** rules that the audit restores the whole data structure (A62 (exit-audit-restore), dispatched); §7.1's GR
  compared set will lose the inherited audit residual with its reason (A62 states the count). The A57/A52 "one component
  above τ" statements are withdrawn as convergence statements. PROCESS findings (the mesh change; the MFILE `insstrain`
  0.70–0.72 % off the solved value in every arm as shipped; the `None` latch) filed in `PROCESS_code_analysis` at the
  user's instruction. Open: I-21, what else the output pass leaves inconsistent in the written file.
