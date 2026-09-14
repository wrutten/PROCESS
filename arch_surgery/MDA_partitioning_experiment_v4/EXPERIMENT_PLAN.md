# MDA Partitioning Experiment V4 — Experiment Plan

> **Document status** — **EXECUTED AND REPORTED, 2026-09-14** — §4 is the campaign population (949 records at `57dc0c14`), §5 and §6 are written from it. Approval record: **APPROVED FOR EXECUTION, 2026-09-14** (the user: *"You can run the experiment"*, after the D27 rerun of every gate on the
> final harness — 30 PASS, 152/152 teeth, GR 256/256, G1 byte-neutral, at `03f72479`; `EXECUTION_APPROVED` flipped in this commit). The campaign is
> pressed from the button (`experiment_runner.py --campaign`) at this commit; its records are stamped `campaign` and §4 is re-rendered from them.
> Methodology unchanged since the 2026-09-10 draft except by the dated amendments in the text (D24–D27). *Superseded header follows for the record:*
> DRAFT · NOT APPROVED. Written 2026-09-10 by the orchestrating
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

*The switches, for the record — the names the copy reads since DR1 (A56 (driver-renames), 2026-09-10; harness plan §11.2), the V3 name in parentheses; every retired name raises if set:* `PROCESS_ARCH_MDA = flat | partitioned` (was `MODULE_SOLVE = flat_state | per_module`; `OUTER` retired — `partitioned` runs its block schedule once); `PROCESS_ARCH_ARRANGEMENT_NODE = build_after_physics` (was `SEQUENCE`); `PROCESS_ARCH_ARRANGEMENT_METHOD = fw_geometry` (was `PRIME`); `PROCESS_ARCH_DEFER_PER_CALL = feedforward | feedforward_lifted` (was `HOIST`); `PROCESS_ARCH_DEFER_PER_RUN = <artifact>` (was `POST_SOLVE`); `PROCESS_ARCH_BURN_TIME_OWNER = loop | constant:<hex> | optimiser` (was `LIFT = burn_time` and `PIN_BURN_TIME = <hex>`); `PROCESS_ARCH_TAU` (`INNER_TAU` retired, D23); `PROCESS_ARCH_COUPLING_STATE` and `PROCESS_ARCH_WRITE_SETS` (were `YSTATE`, `WRITESET`) — the two committed per-configuration artifacts that define `y` and the per-block write sets. `PROCESS_ARCH_OUTPUT_LOOP = upstream | none` landed with A57 (driver-output-path), 2026-09-10; `PROCESS_ARCH_PREDICATE = frozen | mixed` with A59 (driver-predicate-mode), 2026-09-11 — the pending list is empty, and the self-check says so in its own words (*"0 registry entries with no driver name"*).

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
purpose: the exit audit at the accepted point, per run, with the count of components above τ. *Implementation note, 2026-09-10 (orchestrator, at A50 (harness-run)'s merge):* the audit sweep mutates the state it measures, so it cannot run *at* that entry without handing the output path an audited state; the position is reached by a **snapshot** of the coupling state taken at the entry to `write_output_files`, with the residual computed after the run from the restored snapshot. The snapshot hook landed with A57 (driver-output-path), 2026-09-10: every campaign record carries `audit_position == audit_position_declared == entry_to_write_output_files`, the restore is proven bit-exact before the audit is taken, and the after-the-run position survives for the reproduction gate alone, whose compared values include a residual the previous revision measured there. First measurement at the declared position (seed 0, gate G9): on both pulsed configurations, in `B1` and `B3` alike, exactly one restricted component sits above τ — `tfcoil.insstrain`, ~7e-3 scaled — and none on `st_regression` (improvement list item 11). *Diagnosed 2026-09-11 (A61 (insstrain-diagnosis), `fd480aff`):* that residual is an artefact of the instrument, not of convergence — PROCESS's output path raises `tfcoil.n_rad_per_layer` 100 → 500 before the snapshot and the coupling-state restore does not put it back, so the audit swept a different mesh than the loop; 0 of 840/846/827 components differ between the loop's exit and the audited state, and restoring that one field gives exactly `0x0.0p+0`. **Ruling D25:** the snapshot and restore cover the whole data structure (a derived set, fields that cannot be restored counted and named), landing with A62 (exit-audit-restore) before the campaign; GR's compared set loses the inherited audit residual with its reason. The "one component above τ" reading is withdrawn: `B0` and `B3` converged to τ on every evaluation. *Landed 2026-09-11 with A62 (exit-audit-restore), `a3407d5d`:* the audit snapshots the whole data structure at both of the driver's positions and restores a derived set before its sweep, at both audit positions; one namespace (`numerics`, the optimiser's own accounting) is held back by a named rule and what it holds back is named per run; every record stamps the instrument. Measured at the declared position: 0 of 31 records have a component above τ, and `tfcoil.insstrain` sits at exactly `0x0.0p+0` in every arm on both pulsed configurations (new maximum 1.15e-11 on `large_tokamak_nof`, exactly 0 on `low_aspect_ratio_DEMO`). GR's compared set is 270 → 256 by name (§7.1 of the harness plan). The `after_run` residual on the reference arm now reads 6.99e-03 / 7.02e-03 — the distance between the written file and a fixed point of the solve's own map (I-21).

*Measured 2026-09-14 (A67 (written-file-gap), gate `written_file_gap`, `f8d67eb4`):* the one-call output path writes the **same** ~0.7 % `tfcoil.insstrain` gap as the loop path — the written file carries the post-write value in every Phase B arm, `BR` and `B0` through the loop, `B1` and `B3` through the single `finalise` — and no second component moves. No acceptance quantity of this experiment is written by a model's `output()`. The gap is PROCESS's, reported per run, never accepted on (D25, confirmed by the user 2026-09-14).

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
bit-identical per configuration; each is evaluated by one `call_models` under each arm. **Every Phase A arm, the reference arm `AR` included, is entered from the same displaced snapshot at the same seed** (decision D26, ruled by the user 2026-09-14: *"here we compare just the stopping rule"*); "PROCESS as shipped" names `AR`'s switches, not its starting point, and the cost of starting from the input file's own point is the cold-start term above. Gate G6 checks the pairing for `AR` too since A64 (entry-pairing-reference).

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
per-configuration artifacts live inside the V4 folder — **`harness/child/ystate.py` (at `harness/ystate.py` until A66) and
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

## 4. Results *(the **campaign** population — 949 records at `57dc0c14` — rendered from the campaign's records; the gate population at `0677a9b3`, `4ca8cff5`, `fd480aff` was the section's earlier fill, before execution approval, and is excluded by kind)*

**Where these cells come from.** Every table below is emitted by a measurement stage of `experiment_runner.py` and rendered into this document by `harness/measurement/plan_tables.py`, which reads the stages' own records under `runs/gates/<stage>/measurements.json`. No cell is typed by hand (protocol §15), and nothing in this section is computed here: each caption, denominator and grid is the stage's.

**Population: the campaign, not the gate runs.** `EXECUTION_APPROVED` is True and the campaign has run: every cell in §4.2–§4.4 is over the 949 campaign run record(s) made at commit(s) `57dc0c14`, by run kind {'campaign': 949}, by source `campaign_entry_references` 3, `campaign_displaced` 275, `campaign_stencil_forward` 198, `campaign_stencil_backward` 198, `campaign_optimisation` 275. The 139 gate run record(s) at `0677a9b3`, `4ca8cff5`, `fd480aff` (by run kind {'gate': 137, 'smoke': 2}) were this section's earlier fill, before execution approval; they are excluded from every published cell **by kind** (gate `run_kind_separation`) and appear only in §4.1, which is the gates' own table. The exit audit was taken at position(s) `after_single_evaluation`, `entry_to_write_output_files` with the convergence ruler(s) `frozen` and the exit-audit instrument `whole_data_structure_derived_set`.

**Conventions that hold in every table (D21 (c)).** Absolute cost cells are per-run means with the seed bracket. A ratio against the reference is given three ways: pooled (sum over the set / sum over the set), per-run median with `[min, max]`, and the count of seeds on which the arm cost more. Configurations appear in the fixed order nof / lad / st and are never pooled (D21 (b)). Prime calls appear beside node calls, never inside them (D19). Node-call ratios are the acceptance quantities; timings are context and no conclusion rests on one (I-10).

### 4.1 Gates

*Emitted by `experiment_runner.py --measure gate_table`; one row per registered gate, read from the verdict records: what it binds, its population, its denominator, its mismatches and its teeth.*

*Caption: One row per registered gate. 'plan' is the label the experiment plan's §3.9 table uses, empty where the gate is one of the harness's own checks rather than one of the plan's. 'verdict' is PASS/FAIL on the gate's criterion **and** on every tooth tripping. 'population' is what the gate compared, in its own words; 'compared' is the denominator and 'mismatched' the count of things that differed — both are the gate's own headline pair, and a gate whose criterion is not a count of compared values leaves them empty and states its population in words instead. Where a gate compares more than one kind of thing — coupling-state components, record values, output-file lines — the denominator is their sum and the row's 'denominators summed' names each. 'teeth' is tripped / declared. A gate whose tooth did not trip is not accepted whatever its verdict. One row reads 1 mismatched and PASS: the frozen-physics gate counts the single model file the user approved as differing, by name, and passes because it is the approved one. Population: 30 registered gate(s): 11 of the experiment plan's §3.9 table and 19 of the harness's own checks, promoted. Population: each gate's own, stated in its row — the gate population (139 run record(s) at `0677a9b3`, `4ca8cff5`, `fd480aff`), never the campaign's; gates are gates.  §4.2–§4.4 are over the campaign population.*

| gate | plan | binds | verdict | population | compared | mismatched | teeth | record |
|---|---|---|---|---|---|---|---|---|
| `g0prime` | G0 / G0' | every V4 commit, every arm, both phases | **PASS** | 77 files under PROCESS/process/models/ compared byte for byte against c0ae5b28 (git cat-file, never a working tree), plus the file set | 77 | 1 | 4/4 | `runs/gates/g0prime/gate.json` |
| `copy_identity` | — | every V4 commit that touches the experiment's copy of PROCESS | **PASS** | 224 files under PROCESS/process/ compared byte for byte against the source commit f2dc9243 (git cat-file, never a working tree), plus the file set;… | 224 | 7 | 4/4 | `runs/gates/copy_identity/gate.json` |
| `edit_behaviour` | — | the one permitted edit in the copy that is not a rename or a comment | **PASS** | three arms of one probe, no PROCESS run: the copy with the per-run write-set artifact absent, the source commit f2dc9243 (git archive) with it abse… | 3 | 0 | 1/1 | `runs/gates/edit_behaviour/gate.json` |
| `self_containment` | — | the user's requirement in the harness plan §6: nothing in this package is imported from, o | **PASS** | 52 Python file(s): every module under harness/ and experiment_runner.py beside it; 46 line(s) naming either directory, 13 of them executable | 52 | 0 | 1/1 | `runs/gates/self_containment/gate.json` |
| `composition` | — | the harness itself, before any PROCESS run | **PASS** | 8 arms x 3 configurations = 24 pairs | 42 | 0 | 7/7 | `runs/gates/composition/gate.json` |
| `rungs` | — | the harness itself, before any PROCESS run | **PASS** | 11 matrix rows x 8 arms = 88 cells; 6 rung steps | 98 | 0 | 3/3 | `runs/gates/rungs/gate.json` |
| `provenance` | — | the harness itself, before any PROCESS run | **PASS** | one scratch repository, three states | 4 | 0 | 4/4 | `runs/gates/provenance/gate.json` |
| `data` | — | the harness itself, before any PROCESS run | **PASS** | 16 committed file(s) in harness/data/ + the moved predicate module = 17 comparisons; and 9 declared counts (3 configurations x coupling-state compo… | 17 | 0 | 6/6 | `runs/gates/data/gate.json` |
| `run_path` | — | the harness itself, before any PROCESS run | **PASS** | 2 phases x the declared field list; 2 displacement streams; 5 refusals | 12 | 0 | 12/12 | `runs/gates/run_path/gate.json` |
| `resume_identity` | — | every --resume decision and every directory of the shared run pool | **PASS** | 22 Job field(s); 13 by-design pair(s) (10 must differ, 3 must agree) | 35 | 0 | 5/5 | `runs/gates/resume_identity/gate.json` |
| `capability` | — | the harness itself, before any PROCESS run | **PASS** | every arm/configuration pair whose arms are active | 55 | 0 | 5/5 | `runs/gates/capability/gate.json` |
| `artifacts_check` | — | every committed artifact of every configuration | **PASS** | 19 artifact row(s) over 3 configuration(s) (large_tokamak_nof, low_aspect_ratio_DEMO, st_regression); 95 individual check(s) | 95 | 0 | 3/3 | `runs/gates/artifacts_check/gate.json` |
| `artifacts_derive_inputs` | — | the lifted input file of each pulsed configuration | **PASS** | 3 configuration(s) (large_tokamak_nof, low_aspect_ratio_DEMO, st_regression); the digest gate applies to the 2 pulsed one(s) | 2 | 0 | 4/4 | `runs/gates/artifacts_derive_inputs/gate.json` |
| `artifacts_census` | — | the committed run-time write census, per configuration | **PASS** | 3 configuration(s) (large_tokamak_nof, low_aspect_ratio_DEMO, st_regression); one evaluation census each, taken with the read half of the instrumen… | 81 | 0 | 5/5 | `runs/gates/artifacts_census/gate.json` |
| `artifacts_per_run` | — | each configuration's per-run deferral set | **PASS** | 5 (configuration, input file) pair(s) over 3 configuration(s) (large_tokamak_nof, low_aspect_ratio_DEMO, st_regression); the write census is measur… | 16 | 0 | 2/2 | `runs/gates/artifacts_per_run/gate.json` |
| `record_completeness` | G7 | the declared pairing and the failure forensics, in both phases | **PASS** | 2 runs on st_regression (the configuration with the fewest iteration variables, derived); 90 declared field(s) in the optimisation phase and 83 in … | 173 | 0 | 9/9 | `runs/gates/record_completeness/gate.json` |
| `prime_map` | G2 | the claim that the arrangement's method-level move changes nothing once the first-wall mod | **PASS** | 6 arrangement/configuration pair(s); 12 evaluations; 5026 components compared | 5026 | 0 | 2/2 | `runs/gates/prime_map/gate.json` |
| `cold_chain` | G3 / G3c | the claim that with the method-level move in place no cut edge carries a stale value into  | **PASS** | 8 chain/composition pair(s) over 4 chain(s); 16 evaluations | 60 | 0 | 4/4 | `runs/gates/cold_chain/gate.json` |
| `audit_restriction` | G4 | the similarity statistic, on every configuration | **PASS** | 13 doctored run(s) over 3 configuration(s), each against that configuration's undoctored run; namespaces derived per configuration | 12 | 0 | 6/6 | `runs/gates/audit_restriction/gate.json` |
| `entry_and_warm` | G6 | the evaluation phase, on every configuration | **PASS** | 8 entry pair(s) at seed 1; 5 warm run(s); 16 evaluations | 6717 | 0 | 3/3 | `runs/gates/entry_and_warm/gate.json` |
| `switch_composition` | G5 | B3, on every configuration where it is active | **PASS** | 3 configuration(s) where B3 is active; 6 optimisations; 37 switch names and 10 run values per configuration | 141 | 0 | 3/3 | `runs/gates/switch_composition/gate.json` |
| `switch_neutrality` | G1 | each driver change, run per change and never batched | **PASS** | straddles fd480aff -> 0677a9b3: a neutrality result.  6 run pair(s) = 3 configuration(s) x 2 reference arm(s); 2825 deterministic record values and… | 54144 | 0 | 9/9 | `runs/gates/switch_neutrality/gate.json` |
| `reproduction` | GR | the harness rewrite and the experiment's copy of PROCESS, once, at the copy commit before  | **PASS** | 20 runs (14 optimisations + 6 evaluations) over 3 configurations; 270 values in the committed reference, 14 of them excluded by name with their rea… | 256 | 0 | 8/8 | `runs/gates/reproduction/gate.json` |
| `output_path` | G9 | the removal of the output-time loop from the arms whose matrix cell turns it off, on every | **PASS** | 11 run(s) at seed 0 = every optimisation-phase arm on every configuration where it is active, each composed from the experiment's matrix; 3825 coup… | 3879 | 0 | 4/4 | `runs/gates/output_path/gate.json` |
| `written_file_gap` | — | the written-file gap on the one-call output path: BR, B1 and B3 at seed 0 on the pulsed co | **PASS** | 6 run(s) at seed 0, unperturbed = 3 arm(s) (BR, B1, B3) x 2 pulsed configuration(s), each composed from the experiment's matrix with no override bu… | 42 | 0 | 4/4 | `runs/gates/written_file_gap/gate.json` |
| `predicate_mode` | G8 | the convergence predicate's second ruler, on the evaluation-phase arms of every configurat | **PASS** | 12 pair(s) = 3 configuration(s) x the evaluation-phase arms active on each (A0, A1) x 2 seed(s), each run under both rulers = 24 runs at delta = 0.… | 8152 | 0 | 4/4 | `runs/gates/predicate_mode/gate.json` |
| `tally_contracts` | — | every table the tally emits, and the cells it reproduces | **PASS** | 20 reference run(s) (14 optimisations + 6 evaluations) over 3 configurations; 256 published cells, no tolerance on any of them; and 84 table(s) emi… | 508 | 0 | 10/10 | `runs/gates/tally_contracts/gate.json` |
| `recomputation` | — | every cell the tally publishes, recomputed from the run records by a second implementation | **PASS** | 84 table(s) emitted by the two tally stages, recomputed cell by cell from 949 run record(s) under the 5 published source(s) of the campaign populat… | 12715 | 0 | 9/9 | `runs/gates/recomputation/gate.json` |
| `run_kind_separation` | — | every record this package makes, and every population the tally and the analysis build | **PASS** | 1096 run record(s) under runs/, of which 949 are covered by the tally's 5 published source(s) (the campaign family) and 31 by its 2 unpublished; ru… | 2994 | 0 | 9/9 | `runs/gates/run_kind_separation/gate.json` |
| `stage_provenance` | — | the harness itself, before any PROCESS run | **PASS** | a scratch records directory this check writes itself — 3 verdict record(s) and 4 stage record(s) — broken 4 ways; a scratch census record, stamped … | 16 | 0 | 5/5 | `runs/gates/stage_provenance/gate.json` |

**30 PASS, 0 FAIL, 0 not run; 155 of 155 teeth tripped.**

*How to read: no number in §4.2–§4.4 is cited unless every row here is PASS with its tooth tripped; a FAIL is a result and the dependent tables are marked "not produced — gate X failed".*

### 4.2 The evaluation phase

*Emitted by `experiment_runner.py --measure tally_evaluation`; cost per call, matched accuracy on both rulers, the ownership rung, the per-sweep overhead, the failure taxonomy and the predicate trial.*

**`cost per call — large_tokamak_nof — campaign_entry_references`**

*Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.  a row is one arm of the evaluation phase on this configuration.  a column is a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.  population: campaign_entry_references — the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; 1 run(s) of large_tokamak_nof, of which 1 finished.  construction: stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is A0 — pulsed, but this population carries no A0p run, so the ratio falls back to the plain flat control — the previous revision's construction, in which the burn-time residual is reported separately rather than being part of the arm.  This is a FALLBACK and not the declared pair.  the arrangement-method calls are stamped beside the node calls and are never pooled into them.  the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.  these are campaign runs: the population named above and no other.  pairs are keyed by seeds. n = 1 (evaluation-phase campaign runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.  a row is one arm of the evaluation phase on this configuration.  a column is a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.  population: campaign_entry_references — the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; 1 run(s) of large_tokamak_nof, of which 1 finished.  construction: stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is A0 — pulsed, but this population carries no A0p run, so the ratio falls back to the plain flat control — the previous revision's construction, in which the burn-time residual is reported separately rather than being part of the arm.  This is a FALLBACK and not the declared pair.  the arrangement-method calls are stamped beside the node calls and are never pooled into them.  the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.  these are campaign runs: the population named above and no other.  pairs are keyed by seeds.*
| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A0 at seeds | vs A0 pooled | vs A0 median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 1/1 | 126.0 | [126, 126] | 6.00 | FLAT 6 | 0.0 | — | — | — | — |
*n = 1 (evaluation-phase campaign runs of large_tokamak_nof).*
*How to read: a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost*

*How to read: a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost*

**`matched accuracy — large_tokamak_nof — campaign_entry_references`**

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_entry_references — the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; 1 run(s) of large_tokamak_nof.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.  **audit position**: after_single_evaluation.  A residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.  **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.  the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.  **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic. Audit position: `after_single_evaluation`. n = 1 (evaluation-phase campaign runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_entry_references — the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; 1 run(s) of large_tokamak_nof.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.  **audit position**: after_single_evaluation.  A residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.  **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.  the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.  **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic.*
| arm | ruler | n (runs) | with a restricted statistic | restricted median | restricted p90 | restricted argmax | whole-state median | whole-state p90 | components excluded | audit position | audit instrument (snapshot positions taken) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | frozen | 1 | 1 | 8.092e-09 | 8.092e-09 | power.qac | 1.465e-08 | 1.465e-08 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 1 | 1 | 4.529e-09 | 4.529e-09 | power.qac | 4.529e-09 | 4.529e-09 | 122 | after_single_evaluation | no snapshot recorded on this record |
*n = 1 (evaluation-phase campaign runs of large_tokamak_nof).*
*How to read: the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged*

*How to read: the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged*

**`per-sweep overhead — large_tokamak_nof — campaign_entry_references`**

*Caption: units: counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  a row is one run of one arm.  a column is a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.  population: campaign_entry_references — the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; the finished evaluation-phase campaign runs of large_tokamak_nof.  construction: stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.  **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — and over this population it is 0 %.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.  no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone. n = 1 (finished evaluation-phase campaign runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  a row is one run of one arm.  a column is a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.  population: campaign_entry_references — the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; the finished evaluation-phase campaign runs of large_tokamak_nof.  construction: stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.  **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — and over this population it is 0 %.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.  no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone.*
| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 0 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
*n = 1 (finished evaluation-phase campaign runs of large_tokamak_nof).*
*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart*

*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart*

**`failure taxonomy — large_tokamak_nof — campaign_entry_references`**

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_entry_references — the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; every campaign run of large_tokamak_nof.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results. n = 1 (evaluation-phase campaign runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_entry_references — the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; every campaign run of large_tokamak_nof.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.*
| arm | scheduled | ok | rows sum | detail (traceback's last line × count) |
|---|---|---|---|---|
| A0 | 1 | 1 | yes | — |
*n = 1 (evaluation-phase campaign runs of large_tokamak_nof).*
*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited*

*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited*

**`cost per call — low_aspect_ratio_DEMO — campaign_entry_references`**

*Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.  a row is one arm of the evaluation phase on this configuration.  a column is a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.  population: campaign_entry_references — the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; 1 run(s) of low_aspect_ratio_DEMO, of which 1 finished.  construction: stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is A0 — pulsed, but this population carries no A0p run, so the ratio falls back to the plain flat control — the previous revision's construction, in which the burn-time residual is reported separately rather than being part of the arm.  This is a FALLBACK and not the declared pair.  the arrangement-method calls are stamped beside the node calls and are never pooled into them.  the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.  these are campaign runs: the population named above and no other.  pairs are keyed by seeds. n = 1 (evaluation-phase campaign runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.  a row is one arm of the evaluation phase on this configuration.  a column is a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.  population: campaign_entry_references — the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; 1 run(s) of low_aspect_ratio_DEMO, of which 1 finished.  construction: stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is A0 — pulsed, but this population carries no A0p run, so the ratio falls back to the plain flat control — the previous revision's construction, in which the burn-time residual is reported separately rather than being part of the arm.  This is a FALLBACK and not the declared pair.  the arrangement-method calls are stamped beside the node calls and are never pooled into them.  the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.  these are campaign runs: the population named above and no other.  pairs are keyed by seeds.*
| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A0 at seeds | vs A0 pooled | vs A0 median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 1/1 | 105.0 | [105, 105] | 5.00 | FLAT 5 | 0.0 | — | — | — | — |
*n = 1 (evaluation-phase campaign runs of low_aspect_ratio_DEMO).*
*How to read: a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost*

*How to read: a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost*

**`matched accuracy — low_aspect_ratio_DEMO — campaign_entry_references`**

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_entry_references — the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; 1 run(s) of low_aspect_ratio_DEMO.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.  **audit position**: after_single_evaluation.  A residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.  **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.  the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.  **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic. Audit position: `after_single_evaluation`. n = 1 (evaluation-phase campaign runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_entry_references — the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; 1 run(s) of low_aspect_ratio_DEMO.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.  **audit position**: after_single_evaluation.  A residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.  **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.  the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.  **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic.*
| arm | ruler | n (runs) | with a restricted statistic | restricted median | restricted p90 | restricted argmax | whole-state median | whole-state p90 | components excluded | audit position | audit instrument (snapshot positions taken) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | frozen | 1 | 1 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 1 | 1 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
*n = 1 (evaluation-phase campaign runs of low_aspect_ratio_DEMO).*
*How to read: the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged*

*How to read: the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged*

**`per-sweep overhead — low_aspect_ratio_DEMO — campaign_entry_references`**

*Caption: units: counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  a row is one run of one arm.  a column is a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.  population: campaign_entry_references — the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; the finished evaluation-phase campaign runs of low_aspect_ratio_DEMO.  construction: stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.  **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — and over this population it is 0 %.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.  no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone. n = 1 (finished evaluation-phase campaign runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  a row is one run of one arm.  a column is a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.  population: campaign_entry_references — the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; the finished evaluation-phase campaign runs of low_aspect_ratio_DEMO.  construction: stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.  **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — and over this population it is 0 %.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.  no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone.*
| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
*n = 1 (finished evaluation-phase campaign runs of low_aspect_ratio_DEMO).*
*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart*

*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart*

**`failure taxonomy — low_aspect_ratio_DEMO — campaign_entry_references`**

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_entry_references — the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; every campaign run of low_aspect_ratio_DEMO.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results. n = 1 (evaluation-phase campaign runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_entry_references — the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; every campaign run of low_aspect_ratio_DEMO.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.*
| arm | scheduled | ok | rows sum | detail (traceback's last line × count) |
|---|---|---|---|---|
| A0 | 1 | 1 | yes | — |
*n = 1 (evaluation-phase campaign runs of low_aspect_ratio_DEMO).*
*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited*

*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited*

**`cost per call — st_regression — campaign_entry_references`**

*Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.  a row is one arm of the evaluation phase on this configuration.  a column is a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.  population: campaign_entry_references — the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; 1 run(s) of st_regression, of which 1 finished.  construction: stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is A0 — steady state: there is no burn-time coupling, the pinned flat control degenerates onto the plain one and is skipped.  the arrangement-method calls are stamped beside the node calls and are never pooled into them.  the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.  these are campaign runs: the population named above and no other.  pairs are keyed by seeds. n = 1 (evaluation-phase campaign runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.  a row is one arm of the evaluation phase on this configuration.  a column is a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.  population: campaign_entry_references — the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; 1 run(s) of st_regression, of which 1 finished.  construction: stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is A0 — steady state: there is no burn-time coupling, the pinned flat control degenerates onto the plain one and is skipped.  the arrangement-method calls are stamped beside the node calls and are never pooled into them.  the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.  these are campaign runs: the population named above and no other.  pairs are keyed by seeds.*
| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A0 at seeds | vs A0 pooled | vs A0 median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 1/1 | 147.0 | [147, 147] | 7.00 | FLAT 7 | 0.0 | — | — | — | — |
*n = 1 (evaluation-phase campaign runs of st_regression).*
*How to read: a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost*

*How to read: a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost*

**`matched accuracy — st_regression — campaign_entry_references`**

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_entry_references — the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; 1 run(s) of st_regression.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.  **audit position**: after_single_evaluation.  A residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.  **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.  the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.  **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic. Audit position: `after_single_evaluation`. n = 1 (evaluation-phase campaign runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_entry_references — the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; 1 run(s) of st_regression.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.  **audit position**: after_single_evaluation.  A residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.  **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.  the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.  **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic.*
| arm | ruler | n (runs) | with a restricted statistic | restricted median | restricted p90 | restricted argmax | whole-state median | whole-state p90 | components excluded | audit position | audit instrument (snapshot positions taken) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | frozen | 1 | 1 | 3.276e-09 | 3.276e-09 | superconducting_tfcoil.a_tf_plasma_case | 3.276e-09 | 3.276e-09 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 1 | 1 | 2.286e-09 | 2.286e-09 | superconducting_tfcoil.a_tf_plasma_case | 2.286e-09 | 2.286e-09 | 123 | after_single_evaluation | no snapshot recorded on this record |
*n = 1 (evaluation-phase campaign runs of st_regression).*
*How to read: the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged*

*How to read: the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged*

**`per-sweep overhead — st_regression — campaign_entry_references`**

*Caption: units: counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  a row is one run of one arm.  a column is a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.  population: campaign_entry_references — the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; the finished evaluation-phase campaign runs of st_regression.  construction: stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.  **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — and over this population it is 0 %.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.  no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone. n = 1 (finished evaluation-phase campaign runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  a row is one run of one arm.  a column is a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.  population: campaign_entry_references — the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; the finished evaluation-phase campaign runs of st_regression.  construction: stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.  **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — and over this population it is 0 %.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.  no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone.*
| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 0 | coupling_state | 7 | 7 | 5789 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
*n = 1 (finished evaluation-phase campaign runs of st_regression).*
*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart*

*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart*

**`failure taxonomy — st_regression — campaign_entry_references`**

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_entry_references — the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; every campaign run of st_regression.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results. n = 1 (evaluation-phase campaign runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_entry_references — the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; every campaign run of st_regression.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.*
| arm | scheduled | ok | rows sum | detail (traceback's last line × count) |
|---|---|---|---|---|
| A0 | 1 | 1 | yes | — |
*n = 1 (evaluation-phase campaign runs of st_regression).*
*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited*

*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited*

**`cost per call — large_tokamak_nof — campaign_displaced`**

*Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.  a row is one arm of the evaluation phase on this configuration.  a column is a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; 100 run(s) of large_tokamak_nof, of which 100 finished.  construction: stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is A0p — pulsed: the declared reference, because it and the partitioned arm sit on the same reduced map.  the arrangement-method calls are stamped beside the node calls and are never pooled into them.  the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.  these are campaign runs: the population named above and no other.  pairs are keyed by seeds. n = 100 (evaluation-phase campaign runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.  a row is one arm of the evaluation phase on this configuration.  a column is a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; 100 run(s) of large_tokamak_nof, of which 100 finished.  construction: stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is A0p — pulsed: the declared reference, because it and the partitioned arm sit on the same reduced map.  the arrangement-method calls are stamped beside the node calls and are never pooled into them.  the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.  these are campaign runs: the population named above and no other.  pairs are keyed by seeds.*
| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A0p at seeds | vs A0p pooled | vs A0p median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 25/25 | 104.2 | [84, 105] | 4.96 | — | 0.0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.9688 | 1.0000 | 0 |
| A0 | 25/25 | 115.9 | [105, 126] | 5.52 | FLAT 138 | 0.0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 1.0781 | 1.0000 | 10 |
| A0p | 25/25 | 107.5 | [84, 126] | 5.12 | FLAT 128 | 0.0 | — | — | — | — |
| A1 | 25/25 | 60.5 | [60, 63] | 13.16 | FF 0, M1 100, M2 129, M3 75, PULSE 0 | 13.2 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.5625 | 0.5714 | 0 |
*n = 100 (evaluation-phase campaign runs of large_tokamak_nof).*
*How to read: a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost*

*How to read: a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost*

**`matched accuracy — large_tokamak_nof — campaign_displaced`**

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; 100 run(s) of large_tokamak_nof.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.  **audit position**: after_single_evaluation.  A residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.  **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.  the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.  **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic. Audit position: `after_single_evaluation`. n = 100 (evaluation-phase campaign runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; 100 run(s) of large_tokamak_nof.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.  **audit position**: after_single_evaluation.  A residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.  **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.  the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.  **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic.*
| arm | ruler | n (runs) | with a restricted statistic | restricted median | restricted p90 | restricted argmax | whole-state median | whole-state p90 | components excluded | audit position | audit instrument (snapshot positions taken) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 25 | 25 | 2.624e-08 | 1.542e-07 | blanket.deg_blkt_inboard_poloidal_plasma, heat_transport.tlvpmw, power.qac | 3.255e-08 | 4.142e-07 | 122 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 25 | 25 | 1.501e-08 | 8.372e-08 | blanket.deg_blkt_inboard_poloidal_plasma, heat_transport.tlvpmw, power.qac | 1.501e-08 | 8.372e-08 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 25 | 25 | 5.042e-10 | 2.963e-09 | blanket.deg_blkt_inboard_poloidal_plasma, power.qac | 6.254e-10 | 7.959e-09 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 25 | 25 | 2.883e-10 | 1.609e-09 | blanket.deg_blkt_inboard_poloidal_plasma, power.qac | 2.883e-10 | 1.609e-09 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0p | frozen | 25 | 25 | 3.833e-10 | 1.671e-08 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.stress_z_cs_self_midplane_profile | 3.833e-10 | 1.671e-08 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0p | mixed | 25 | 25 | 3.833e-10 | 1.671e-08 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.stress_z_cs_self_midplane_profile | 3.833e-10 | 1.671e-08 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 25 | 25 | 3.833e-10 | 1.671e-08 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.stress_z_cs_self_midplane_profile | 2.435e+00 | 9.860e+00 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A1 | mixed | 25 | 25 | 3.833e-10 | 1.671e-08 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.stress_z_cs_self_midplane_profile | 3.977e-01 | 6.170e-01 | 122 | after_single_evaluation | no snapshot recorded on this record |
*n = 100 (evaluation-phase campaign runs of large_tokamak_nof).*
*How to read: the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged*

*How to read: the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged*

**`ownership rung A0 → A0p — large_tokamak_nof — campaign_displaced`**

*Caption: units: node-call ratio dimensionless; the burn-time residual in seconds and relative to the burn time.  a row is this configuration's rung.  a column is the cost of taking the burn time out of the flat loop, and the inconsistency the constant leaves behind.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; 25 flat-control and 25 pinned run(s) of large_tokamak_nof.  construction: stats.ratio_triple on node calls of the single evaluation; the residual is constraint 93's own function at exit, |value|, median = nearest-rank upper-middle.  the residual is 0 by construction in the flat control, which converges the burn time, and is the price of the constant in the pinned arm.  neither column is a claim about the partition: this rung moves one thing only. n = 50 (A0 and A0p campaign runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: node-call ratio dimensionless; the burn-time residual in seconds and relative to the burn time.  a row is this configuration's rung.  a column is the cost of taking the burn time out of the flat loop, and the inconsistency the constant leaves behind.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; 25 flat-control and 25 pinned run(s) of large_tokamak_nof.  construction: stats.ratio_triple on node calls of the single evaluation; the residual is constraint 93's own function at exit, |value|, median = nearest-rank upper-middle.  the residual is 0 by construction in the flat control, which converges the burn time, and is the price of the constant in the pinned arm.  neither column is a claim about the partition: this rung moves one thing only.*
| n | paired at seeds | A0p/A0 pooled | median | worse | burn-time residual, s (median) | bracket, s | relative (median) |
|---|---|---|---|---|---|---|---|
| 25 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.9275 | 1.0000 | 0 | 1.546e+02 | [12.8111, 406.884] | 6.298e-02 |
*n = 50 (A0 and A0p campaign runs of large_tokamak_nof).*
*How to read: the ratio is the loop's cost of converging the burn time; the residual is what holding it constant costs in accuracy*

*How to read: the ratio is the loop's cost of converging the burn time; the residual is what holding it constant costs in accuracy*

**`per-sweep overhead — large_tokamak_nof — campaign_displaced`**

*Caption: units: counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  a row is one run of one arm.  a column is a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; the finished evaluation-phase campaign runs of large_tokamak_nof.  construction: stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.  **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — and over this population it is 0 %.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.  no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone. n = 100 (finished evaluation-phase campaign runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  a row is one run of one arm.  a column is a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; the finished evaluation-phase campaign runs of large_tokamak_nof.  construction: stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.  **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — and over this population it is 0 %.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.  no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone.*
| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 1 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 2 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 3 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 4 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 5 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 6 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 7 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 8 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 9 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 10 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 11 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 12 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 13 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 14 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 15 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 16 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27.0 | 0.00 % |
| AR | 17 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 18 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 19 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 20 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 21 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 22 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 23 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 24 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 25 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| A0 | 1 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 2 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 3 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 4 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 5 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 6 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 7 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 8 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 9 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 10 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 11 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 12 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 13 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 14 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 15 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 16 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 17 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 18 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 19 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 20 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 21 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 22 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 23 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 24 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 25 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 1 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 2 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 3 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 4 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 5 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 6 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 7 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 8 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 9 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 10 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 11 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 12 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 13 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 14 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 15 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 16 | coupling_state | 4 | 4 | 3360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 17 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 18 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 19 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 20 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 21 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 22 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 23 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 24 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 25 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 1 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 2 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 3 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 4 | coupling_state | 14 | 13 | 3135 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 5 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 6 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 7 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 8 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 9 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 10 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 11 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 12 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 13 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 14 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 15 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 16 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 17 | coupling_state | 14 | 13 | 3135 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 18 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 19 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 20 | coupling_state | 14 | 13 | 3135 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 21 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 22 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 23 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 24 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 25 | coupling_state | 14 | 13 | 3135 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
*n = 100 (finished evaluation-phase campaign runs of large_tokamak_nof).*
*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart*

*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart*

**`failure taxonomy — large_tokamak_nof — campaign_displaced`**

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; every campaign run of large_tokamak_nof.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results. n = 100 (evaluation-phase campaign runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; every campaign run of large_tokamak_nof.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.*
| arm | scheduled | ok | rows sum | detail (traceback's last line × count) |
|---|---|---|---|---|
| AR | 25 | 25 | yes | — |
| A0 | 25 | 25 | yes | — |
| A0p | 25 | 25 | yes | — |
| A1 | 25 | 25 | yes | — |
*n = 100 (evaluation-phase campaign runs of large_tokamak_nof).*
*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited*

*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited*

**`cost per call — low_aspect_ratio_DEMO — campaign_displaced`**

*Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.  a row is one arm of the evaluation phase on this configuration.  a column is a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; 100 run(s) of low_aspect_ratio_DEMO, of which 100 finished.  construction: stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is A0p — pulsed: the declared reference, because it and the partitioned arm sit on the same reduced map.  the arrangement-method calls are stamped beside the node calls and are never pooled into them.  the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.  these are campaign runs: the population named above and no other.  pairs are keyed by seeds. n = 100 (evaluation-phase campaign runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.  a row is one arm of the evaluation phase on this configuration.  a column is a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; 100 run(s) of low_aspect_ratio_DEMO, of which 100 finished.  construction: stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is A0p — pulsed: the declared reference, because it and the partitioned arm sit on the same reduced map.  the arrangement-method calls are stamped beside the node calls and are never pooled into them.  the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.  these are campaign runs: the population named above and no other.  pairs are keyed by seeds.*
| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A0p at seeds | vs A0p pooled | vs A0p median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 25/25 | 105.0 | [105, 105] | 5.00 | — | 0.0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 1.0163 | 1.0000 | 2 |
| A0 | 25/25 | 105.0 | [105, 105] | 5.00 | FLAT 125 | 0.0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 1.0163 | 1.0000 | 2 |
| A0p | 25/25 | 103.3 | [84, 105] | 4.92 | FLAT 123 | 0.0 | — | — | — | — |
| A1 | 25/25 | 59.6 | [57, 60] | 12.88 | FF 0, M1 100, M2 122, M3 75, PULSE 0 | 12.9 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.5772 | 0.5714 | 0 |
*n = 100 (evaluation-phase campaign runs of low_aspect_ratio_DEMO).*
*How to read: a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost*

*How to read: a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost*

**`matched accuracy — low_aspect_ratio_DEMO — campaign_displaced`**

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; 100 run(s) of low_aspect_ratio_DEMO.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.  **audit position**: after_single_evaluation.  A residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.  **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.  the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.  **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic. Audit position: `after_single_evaluation`. n = 100 (evaluation-phase campaign runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; 100 run(s) of low_aspect_ratio_DEMO.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.  **audit position**: after_single_evaluation.  A residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.  **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.  the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.  **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic.*
| arm | ruler | n (runs) | with a restricted statistic | restricted median | restricted p90 | restricted argmax | whole-state median | whole-state p90 | components excluded | audit position | audit instrument (snapshot positions taken) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 25 | 25 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 25 | 25 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 25 | 25 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 25 | 25 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0p | frozen | 25 | 25 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0p | mixed | 25 | 25 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 25 | 25 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 1.816e-01 | 2.878e-01 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | mixed | 25 | 25 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 1.687e-01 | 2.420e-01 | 123 | after_single_evaluation | no snapshot recorded on this record |
*n = 100 (evaluation-phase campaign runs of low_aspect_ratio_DEMO).*
*How to read: the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged*

*How to read: the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged*

**`ownership rung A0 → A0p — low_aspect_ratio_DEMO — campaign_displaced`**

*Caption: units: node-call ratio dimensionless; the burn-time residual in seconds and relative to the burn time.  a row is this configuration's rung.  a column is the cost of taking the burn time out of the flat loop, and the inconsistency the constant leaves behind.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; 25 flat-control and 25 pinned run(s) of low_aspect_ratio_DEMO.  construction: stats.ratio_triple on node calls of the single evaluation; the residual is constraint 93's own function at exit, |value|, median = nearest-rank upper-middle.  the residual is 0 by construction in the flat control, which converges the burn time, and is the price of the constant in the pinned arm.  neither column is a claim about the partition: this rung moves one thing only. n = 50 (A0 and A0p campaign runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: node-call ratio dimensionless; the burn-time residual in seconds and relative to the burn time.  a row is this configuration's rung.  a column is the cost of taking the burn time out of the flat loop, and the inconsistency the constant leaves behind.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; 25 flat-control and 25 pinned run(s) of low_aspect_ratio_DEMO.  construction: stats.ratio_triple on node calls of the single evaluation; the residual is constraint 93's own function at exit, |value|, median = nearest-rank upper-middle.  the residual is 0 by construction in the flat control, which converges the burn time, and is the price of the constant in the pinned arm.  neither column is a claim about the partition: this rung moves one thing only.*
| n | paired at seeds | A0p/A0 pooled | median | worse | burn-time residual, s (median) | bracket, s | relative (median) |
|---|---|---|---|---|---|---|---|
| 25 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.9840 | 1.0000 | 0 | 5.258e+02 | [1.64882, 1436.26] | 5.275e-02 |
*n = 50 (A0 and A0p campaign runs of low_aspect_ratio_DEMO).*
*How to read: the ratio is the loop's cost of converging the burn time; the residual is what holding it constant costs in accuracy*

*How to read: the ratio is the loop's cost of converging the burn time; the residual is what holding it constant costs in accuracy*

**`per-sweep overhead — low_aspect_ratio_DEMO — campaign_displaced`**

*Caption: units: counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  a row is one run of one arm.  a column is a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; the finished evaluation-phase campaign runs of low_aspect_ratio_DEMO.  construction: stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.  **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — and over this population it is 0 %.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.  no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone. n = 100 (finished evaluation-phase campaign runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  a row is one run of one arm.  a column is a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; the finished evaluation-phase campaign runs of low_aspect_ratio_DEMO.  construction: stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.  **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — and over this population it is 0 %.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.  no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone.*
| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 1 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 2 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 3 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 4 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 5 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 6 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 7 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 8 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 9 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 10 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 11 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 12 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 13 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 14 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 15 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 16 | upstream | 5 | 0 | 0 | — | — | 4 | 79 | 19.8 | 0.00 % |
| AR | 17 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 18 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 19 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 20 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 21 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 22 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 23 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 24 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 25 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| A0 | 1 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 2 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 3 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 4 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 5 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 6 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 7 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 8 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 9 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 10 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 11 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 12 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 13 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 14 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 15 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 16 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 17 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 18 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 19 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 20 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 21 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 22 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 23 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 24 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 25 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 1 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 2 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 3 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 4 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 5 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 6 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 7 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 8 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 9 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 10 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 11 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 12 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 13 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 14 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 15 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 16 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 17 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 18 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 19 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 20 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 21 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 22 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 23 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 24 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 25 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 1 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 2 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 3 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 4 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 5 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 6 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 7 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 8 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 9 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 10 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 11 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 12 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 13 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 14 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 15 | coupling_state | 12 | 11 | 2675 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 16 | coupling_state | 12 | 11 | 2675 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 17 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 18 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 19 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 20 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 21 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 22 | coupling_state | 12 | 11 | 2675 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 23 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 24 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 25 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
*n = 100 (finished evaluation-phase campaign runs of low_aspect_ratio_DEMO).*
*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart*

*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart*

**`failure taxonomy — low_aspect_ratio_DEMO — campaign_displaced`**

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; every campaign run of low_aspect_ratio_DEMO.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results. n = 100 (evaluation-phase campaign runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; every campaign run of low_aspect_ratio_DEMO.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.*
| arm | scheduled | ok | rows sum | detail (traceback's last line × count) |
|---|---|---|---|---|
| AR | 25 | 25 | yes | — |
| A0 | 25 | 25 | yes | — |
| A0p | 25 | 25 | yes | — |
| A1 | 25 | 25 | yes | — |
*n = 100 (evaluation-phase campaign runs of low_aspect_ratio_DEMO).*
*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited*

*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited*

**`cost per call — st_regression — campaign_displaced`**

*Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.  a row is one arm of the evaluation phase on this configuration.  a column is a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; 75 run(s) of st_regression, of which 75 finished.  construction: stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is A0 — steady state: there is no burn-time coupling, the pinned flat control degenerates onto the plain one and is skipped.  the arrangement-method calls are stamped beside the node calls and are never pooled into them.  the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.  these are campaign runs: the population named above and no other.  pairs are keyed by seeds. n = 75 (evaluation-phase campaign runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.  a row is one arm of the evaluation phase on this configuration.  a column is a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; 75 run(s) of st_regression, of which 75 finished.  construction: stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is A0 — steady state: there is no burn-time coupling, the pinned flat control degenerates onto the plain one and is skipped.  the arrangement-method calls are stamped beside the node calls and are never pooled into them.  the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.  these are campaign runs: the population named above and no other.  pairs are keyed by seeds.*
| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A0 at seeds | vs A0 pooled | vs A0 median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 25/25 | 103.3 | [84, 105] | 4.92 | — | 0.0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.8425 | 0.8333 | 0 |
| A0 | 25/25 | 122.6 | [105, 126] | 5.84 | FLAT 146 | 0.0 | — | — | — | — |
| A1 | 25/25 | 61.5 | [59, 62] | 14.84 | FF 0, M1 100, M2 146, M3 75, PULSE 25 | 14.8 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.5016 | 0.4921 | 0 |
*n = 75 (evaluation-phase campaign runs of st_regression).*
*How to read: a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost*

*How to read: a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost*

**`matched accuracy — st_regression — campaign_displaced`**

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; 75 run(s) of st_regression.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.  **audit position**: after_single_evaluation.  A residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.  **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.  the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.  **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic. Audit position: `after_single_evaluation`. n = 75 (evaluation-phase campaign runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; 75 run(s) of st_regression.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.  **audit position**: after_single_evaluation.  A residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.  **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.  the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.  **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic.*
| arm | ruler | n (runs) | with a restricted statistic | restricted median | restricted p90 | restricted argmax | whole-state median | whole-state p90 | components excluded | audit position | audit instrument (snapshot positions taken) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 25 | 25 | 1.539e-07 | 2.793e-07 | superconducting_tfcoil.a_tf_plasma_case | 1.539e-07 | 2.793e-07 | 123 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 25 | 25 | 1.074e-07 | 1.949e-07 | superconducting_tfcoil.a_tf_plasma_case | 1.074e-07 | 1.949e-07 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 25 | 25 | 5.372e-09 | 2.023e-08 | superconducting_tfcoil.a_tf_plasma_case | 5.372e-09 | 2.023e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 25 | 25 | 3.749e-09 | 1.412e-08 | superconducting_tfcoil.a_tf_plasma_case | 3.749e-09 | 1.412e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 25 | 25 | 5.372e-09 | 2.023e-08 | superconducting_tfcoil.a_tf_plasma_case | 2.575e-01 | 3.374e-01 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | mixed | 25 | 25 | 3.749e-09 | 1.412e-08 | superconducting_tfcoil.a_tf_plasma_case | 1.343e-01 | 1.810e-01 | 123 | after_single_evaluation | no snapshot recorded on this record |
*n = 75 (evaluation-phase campaign runs of st_regression).*
*How to read: the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged*

*How to read: the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged*

**`per-sweep overhead — st_regression — campaign_displaced`**

*Caption: units: counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  a row is one run of one arm.  a column is a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; the finished evaluation-phase campaign runs of st_regression.  construction: stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.  **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — and over this population it is 0 %, 6.67 %, 7.14 %.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.  no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone. n = 75 (finished evaluation-phase campaign runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  a row is one run of one arm.  a column is a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; the finished evaluation-phase campaign runs of st_regression.  construction: stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.  **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — and over this population it is 0 %, 6.67 %, 7.14 %.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.  no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone.*
| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 1 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 2 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 3 | upstream | 4 | 0 | 0 | — | — | 3 | 21 | 7.0 | 0.00 % |
| AR | 4 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 5 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 6 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 7 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 8 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 9 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 10 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 11 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 12 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 13 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 14 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 15 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 16 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 17 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 18 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 19 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 20 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 21 | upstream | 4 | 0 | 0 | — | — | 3 | 21 | 7.0 | 0.00 % |
| AR | 22 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 23 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 24 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 25 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| A0 | 1 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 2 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 3 | coupling_state | 5 | 5 | 4135 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 4 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 5 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 6 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 7 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 8 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 9 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 10 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 11 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 12 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 13 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 14 | coupling_state | 5 | 5 | 4135 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 15 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 16 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 17 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 18 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 19 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 20 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 21 | coupling_state | 5 | 5 | 4135 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 22 | coupling_state | 5 | 5 | 4135 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 23 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 24 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 25 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A1 | 1 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A1 | 2 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A1 | 3 | coupling_state | 14 | 12 | 2821 | 235.1 | M1 268, M2 216, M3 223 | 0 | 0 | — | 7.14 % |
| A1 | 4 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A1 | 5 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A1 | 6 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A1 | 7 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A1 | 8 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A1 | 9 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A1 | 10 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A1 | 11 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A1 | 12 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A1 | 13 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A1 | 14 | coupling_state | 14 | 12 | 2821 | 235.1 | M1 268, M2 216, M3 223 | 0 | 0 | — | 7.14 % |
| A1 | 15 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A1 | 16 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A1 | 17 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A1 | 18 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A1 | 19 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A1 | 20 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A1 | 21 | coupling_state | 14 | 12 | 2821 | 235.1 | M1 268, M2 216, M3 223 | 0 | 0 | — | 7.14 % |
| A1 | 22 | coupling_state | 14 | 12 | 2821 | 235.1 | M1 268, M2 216, M3 223 | 0 | 0 | — | 7.14 % |
| A1 | 23 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A1 | 24 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A1 | 25 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
*n = 75 (finished evaluation-phase campaign runs of st_regression).*
*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart*

*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart*

**`failure taxonomy — st_regression — campaign_displaced`**

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; every campaign run of st_regression.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results. n = 75 (evaluation-phase campaign runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_displaced — the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; every campaign run of st_regression.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.*
| arm | scheduled | ok | rows sum | detail (traceback's last line × count) |
|---|---|---|---|---|
| AR | 25 | 25 | yes | — |
| A0 | 25 | 25 | yes | — |
| A1 | 25 | 25 | yes | — |
*n = 75 (evaluation-phase campaign runs of st_regression).*
*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited*

*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited*

**`cost per call — large_tokamak_nof — campaign_stencil_forward`**

*Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.  a row is one arm of the evaluation phase on this configuration.  a column is a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 80 run(s) of large_tokamak_nof, of which 80 finished.  construction: stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is A0p — pulsed: the declared reference, because it and the partitioned arm sit on the same reduced map.  the arrangement-method calls are stamped beside the node calls and are never pooled into them.  the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.  these are campaign runs: the population named above and no other.  pairs are keyed by columns. n = 80 (evaluation-phase campaign runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.  a row is one arm of the evaluation phase on this configuration.  a column is a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 80 run(s) of large_tokamak_nof, of which 80 finished.  construction: stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is A0p — pulsed: the declared reference, because it and the partitioned arm sit on the same reduced map.  the arrangement-method calls are stamped beside the node calls and are never pooled into them.  the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.  these are campaign runs: the population named above and no other.  pairs are keyed by columns.*
| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A0p at columns | vs A0p pooled | vs A0p median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 20/20 | 62.0 | [42, 84] | 2.95 | — | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 0.9833 | 1.0000 | 0 |
| A0 | 20/20 | 66.2 | [42, 105] | 3.15 | FLAT 63 | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 1.0500 | 1.0000 | 3 |
| A0p | 20/20 | 63.0 | [42, 105] | 3.00 | FLAT 60 | 0.0 | — | — | — | — |
| A1 | 20/20 | 39.1 | [20, 55] | 7.60 | FF 0, M1 38, M2 49, M3 45, PULSE 0 | 7.6 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 0.6214 | 0.6071 | 0 |
*n = 80 (evaluation-phase campaign runs of large_tokamak_nof).*
*How to read: a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost*

*How to read: a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost*

**`matched accuracy — large_tokamak_nof — campaign_stencil_forward`**

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 80 run(s) of large_tokamak_nof.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.  **audit position**: after_single_evaluation.  A residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.  **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.  the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.  **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic. Audit position: `after_single_evaluation`. n = 80 (evaluation-phase campaign runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 80 run(s) of large_tokamak_nof.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.  **audit position**: after_single_evaluation.  A residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.  **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.  the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.  **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic.*
| arm | ruler | n (runs) | with a restricted statistic | restricted median | restricted p90 | restricted argmax | whole-state median | whole-state p90 | components excluded | audit position | audit instrument (snapshot positions taken) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 20 | 20 | 2.974e-12 | 1.869e-08 | power.qac | 5.344e-12 | 3.385e-08 | 122 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 20 | 20 | 1.664e-12 | 1.046e-08 | power.qac | 1.664e-12 | 1.046e-08 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 20 | 20 | 2.974e-12 | 3.592e-10 | power.qac | 5.344e-12 | 6.504e-10 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 20 | 20 | 1.664e-12 | 2.010e-10 | power.qac | 1.664e-12 | 2.010e-10 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0p | frozen | 20 | 20 | 4.523e-13 | 2.783e-09 | pf_coil.f_j_cs_start_end_flat_top, pf_coil.stress_z_cs_self_midplane_profile | 4.523e-13 | 2.783e-09 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0p | mixed | 20 | 20 | 4.523e-13 | 2.783e-09 | pf_coil.f_j_cs_start_end_flat_top, pf_coil.stress_z_cs_self_midplane_profile | 4.523e-13 | 2.783e-09 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 20 | 20 | 2.363e-11 | 2.783e-09 | pf_coil.f_j_cs_start_end_flat_top, pf_coil.stress_z_cs_self_midplane_profile | 2.016e-03 | 7.115e-02 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A1 | mixed | 20 | 20 | 2.363e-11 | 2.783e-09 | pf_coil.f_j_cs_start_end_flat_top, pf_coil.stress_z_cs_self_midplane_profile | 1.827e-03 | 1.078e-02 | 122 | after_single_evaluation | no snapshot recorded on this record |
*n = 80 (evaluation-phase campaign runs of large_tokamak_nof).*
*How to read: the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged*

*How to read: the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged*

**`ownership rung A0 → A0p — large_tokamak_nof — campaign_stencil_forward`**

*Caption: units: node-call ratio dimensionless; the burn-time residual in seconds and relative to the burn time.  a row is this configuration's rung.  a column is the cost of taking the burn time out of the flat loop, and the inconsistency the constant leaves behind.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 20 flat-control and 20 pinned run(s) of large_tokamak_nof.  construction: stats.ratio_triple on node calls of the single evaluation; the residual is constraint 93's own function at exit, |value|, median = nearest-rank upper-middle.  the residual is 0 by construction in the flat control, which converges the burn time, and is the price of the constant in the pinned arm.  neither column is a claim about the partition: this rung moves one thing only. n = 40 (A0 and A0p campaign runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: node-call ratio dimensionless; the burn-time residual in seconds and relative to the burn time.  a row is this configuration's rung.  a column is the cost of taking the burn time out of the flat loop, and the inconsistency the constant leaves behind.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 20 flat-control and 20 pinned run(s) of large_tokamak_nof.  construction: stats.ratio_triple on node calls of the single evaluation; the residual is constraint 93's own function at exit, |value|, median = nearest-rank upper-middle.  the residual is 0 by construction in the flat control, which converges the burn time, and is the price of the constant in the pinned arm.  neither column is a claim about the partition: this rung moves one thing only.*
| n | paired at columns | A0p/A0 pooled | median | worse | burn-time residual, s (median) | bracket, s | relative (median) |
|---|---|---|---|---|---|---|---|
| 20 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 0.9524 | 1.0000 | 0 | 1.173e+00 | [2.61319e-07, 13.1365] | 4.566e-04 |
*n = 40 (A0 and A0p campaign runs of large_tokamak_nof).*
*How to read: the ratio is the loop's cost of converging the burn time; the residual is what holding it constant costs in accuracy*

*How to read: the ratio is the loop's cost of converging the burn time; the residual is what holding it constant costs in accuracy*

**`per-sweep overhead — large_tokamak_nof — campaign_stencil_forward`**

*Caption: units: counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  a row is one run of one arm.  a column is a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; the finished evaluation-phase campaign runs of large_tokamak_nof.  construction: stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.  **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — and over this population it is 0 %.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.  no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone. n = 80 (finished evaluation-phase campaign runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  a row is one run of one arm.  a column is a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; the finished evaluation-phase campaign runs of large_tokamak_nof.  construction: stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.  **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — and over this population it is 0 %.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.  no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone.*
| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27.0 | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 4 | 4 | 3360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 4 | 4 | 3360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 4 | 4 | 3360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 4 | 4 | 3360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 10 | 9 | 2157 | 239.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 11 | 10 | 2397 | 239.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1456 | 242.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 8 | 7 | 1678 | 239.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1456 | 242.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 5 | 4 | 977 | 244.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 9 | 8 | 1881 | 235.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 9 | 8 | 1936 | 242.0 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 10 | 9 | 2121 | 235.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1420 | 236.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1456 | 242.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 6 | 5 | 1180 | 236.0 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 9 | 8 | 1881 | 235.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 6 | 5 | 1180 | 236.0 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 6 | 5 | 1180 | 236.0 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 6 | 5 | 1180 | 236.0 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1456 | 242.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 6 | 5 | 1180 | 236.0 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1456 | 242.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 9 | 8 | 1881 | 235.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
*n = 80 (finished evaluation-phase campaign runs of large_tokamak_nof).*
*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart*

*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart*

**`failure taxonomy — large_tokamak_nof — campaign_stencil_forward`**

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; every campaign run of large_tokamak_nof.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results. n = 80 (evaluation-phase campaign runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; every campaign run of large_tokamak_nof.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.*
| arm | scheduled | ok | rows sum | detail (traceback's last line × count) |
|---|---|---|---|---|
| AR | 20 | 20 | yes | — |
| A0 | 20 | 20 | yes | — |
| A0p | 20 | 20 | yes | — |
| A1 | 20 | 20 | yes | — |
*n = 80 (evaluation-phase campaign runs of large_tokamak_nof).*
*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited*

*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited*

**`cost per call — low_aspect_ratio_DEMO — campaign_stencil_forward`**

*Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.  a row is one arm of the evaluation phase on this configuration.  a column is a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 76 run(s) of low_aspect_ratio_DEMO, of which 76 finished.  construction: stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is A0p — pulsed: the declared reference, because it and the partitioned arm sit on the same reduced map.  the arrangement-method calls are stamped beside the node calls and are never pooled into them.  the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.  these are campaign runs: the population named above and no other.  pairs are keyed by columns. n = 76 (evaluation-phase campaign runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.  a row is one arm of the evaluation phase on this configuration.  a column is a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 76 run(s) of low_aspect_ratio_DEMO, of which 76 finished.  construction: stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is A0p — pulsed: the declared reference, because it and the partitioned arm sit on the same reduced map.  the arrangement-method calls are stamped beside the node calls and are never pooled into them.  the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.  these are campaign runs: the population named above and no other.  pairs are keyed by columns.*
| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A0p at columns | vs A0p pooled | vs A0p median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 19/19 | 67.4 | [42, 105] | 3.21 | — | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 1.0702 | 1.0000 | 4 |
| A0 | 19/19 | 66.3 | [42, 105] | 3.16 | FLAT 60 | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 1.0526 | 1.0000 | 3 |
| A0p | 19/19 | 63.0 | [42, 84] | 3.00 | FLAT 57 | 0.0 | — | — | — | — |
| A1 | 19/19 | 40.3 | [33, 55] | 7.63 | FF 0, M1 36, M2 45, M3 45, PULSE 0 | 7.6 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 0.6399 | 0.6071 | 0 |
*n = 76 (evaluation-phase campaign runs of low_aspect_ratio_DEMO).*
*How to read: a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost*

*How to read: a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost*

**`matched accuracy — low_aspect_ratio_DEMO — campaign_stencil_forward`**

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 76 run(s) of low_aspect_ratio_DEMO.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.  **audit position**: after_single_evaluation.  A residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.  **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.  the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.  **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic. Audit position: `after_single_evaluation`. n = 76 (evaluation-phase campaign runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 76 run(s) of low_aspect_ratio_DEMO.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.  **audit position**: after_single_evaluation.  A residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.  **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.  the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.  **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic.*
| arm | ruler | n (runs) | with a restricted statistic | restricted median | restricted p90 | restricted argmax | whole-state median | whole-state p90 | components excluded | audit position | audit instrument (snapshot positions taken) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma, heat_transport.tlvpmw | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma, heat_transport.tlvpmw | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0p | frozen | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0p | mixed | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 1.504e-03 | 7.584e-03 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | mixed | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 1.471e-03 | 7.584e-03 | 123 | after_single_evaluation | no snapshot recorded on this record |
*n = 76 (evaluation-phase campaign runs of low_aspect_ratio_DEMO).*
*How to read: the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged*

*How to read: the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged*

**`ownership rung A0 → A0p — low_aspect_ratio_DEMO — campaign_stencil_forward`**

*Caption: units: node-call ratio dimensionless; the burn-time residual in seconds and relative to the burn time.  a row is this configuration's rung.  a column is the cost of taking the burn time out of the flat loop, and the inconsistency the constant leaves behind.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 19 flat-control and 19 pinned run(s) of low_aspect_ratio_DEMO.  construction: stats.ratio_triple on node calls of the single evaluation; the residual is constraint 93's own function at exit, |value|, median = nearest-rank upper-middle.  the residual is 0 by construction in the flat control, which converges the burn time, and is the price of the constant in the pinned arm.  neither column is a claim about the partition: this rung moves one thing only. n = 38 (A0 and A0p campaign runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: node-call ratio dimensionless; the burn-time residual in seconds and relative to the burn time.  a row is this configuration's rung.  a column is the cost of taking the burn time out of the flat loop, and the inconsistency the constant leaves behind.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 19 flat-control and 19 pinned run(s) of low_aspect_ratio_DEMO.  construction: stats.ratio_triple on node calls of the single evaluation; the residual is constraint 93's own function at exit, |value|, median = nearest-rank upper-middle.  the residual is 0 by construction in the flat control, which converges the burn time, and is the price of the constant in the pinned arm.  neither column is a claim about the partition: this rung moves one thing only.*
| n | paired at columns | A0p/A0 pooled | median | worse | burn-time residual, s (median) | bracket, s | relative (median) |
|---|---|---|---|---|---|---|---|
| 19 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 0.9500 | 1.0000 | 0 | 4.176e+00 | [0, 34.2015] | 4.016e-04 |
*n = 38 (A0 and A0p campaign runs of low_aspect_ratio_DEMO).*
*How to read: the ratio is the loop's cost of converging the burn time; the residual is what holding it constant costs in accuracy*

*How to read: the ratio is the loop's cost of converging the burn time; the residual is what holding it constant costs in accuracy*

**`per-sweep overhead — low_aspect_ratio_DEMO — campaign_stencil_forward`**

*Caption: units: counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  a row is one run of one arm.  a column is a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; the finished evaluation-phase campaign runs of low_aspect_ratio_DEMO.  construction: stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.  **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — and over this population it is 0 %.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.  no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone. n = 76 (finished evaluation-phase campaign runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  a row is one run of one arm.  a column is a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; the finished evaluation-phase campaign runs of low_aspect_ratio_DEMO.  construction: stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.  **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — and over this population it is 0 %.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.  no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone.*
| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 53 | 17.7 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 53 | 17.7 | 0.00 % |
| AR | 0 | upstream | 5 | 0 | 0 | — | — | 4 | 104 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26.0 | 0.00 % |
| AR | 0 | upstream | 5 | 0 | 0 | — | — | 4 | 104 | 26.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 10 | 9 | 2172 | 241.3 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 11 | 10 | 2416 | 241.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1463 | 243.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 8 | 7 | 1669 | 238.4 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1463 | 243.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 8 | 7 | 1654 | 236.3 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 9 | 8 | 1898 | 237.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 9 | 8 | 1928 | 241.0 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 9 | 8 | 1898 | 237.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1433 | 238.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1433 | 238.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1463 | 243.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 8 | 7 | 1677 | 239.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1463 | 243.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1463 | 243.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
*n = 76 (finished evaluation-phase campaign runs of low_aspect_ratio_DEMO).*
*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart*

*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart*

**`failure taxonomy — low_aspect_ratio_DEMO — campaign_stencil_forward`**

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; every campaign run of low_aspect_ratio_DEMO.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results. n = 76 (evaluation-phase campaign runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; every campaign run of low_aspect_ratio_DEMO.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.*
| arm | scheduled | ok | rows sum | detail (traceback's last line × count) |
|---|---|---|---|---|
| AR | 19 | 19 | yes | — |
| A0 | 19 | 19 | yes | — |
| A0p | 19 | 19 | yes | — |
| A1 | 19 | 19 | yes | — |
*n = 76 (evaluation-phase campaign runs of low_aspect_ratio_DEMO).*
*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited*

*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited*

**`cost per call — st_regression — campaign_stencil_forward`**

*Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.  a row is one arm of the evaluation phase on this configuration.  a column is a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 42 run(s) of st_regression, of which 42 finished.  construction: stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is A0 — steady state: there is no burn-time coupling, the pinned flat control degenerates onto the plain one and is skipped.  the arrangement-method calls are stamped beside the node calls and are never pooled into them.  the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.  these are campaign runs: the population named above and no other.  pairs are keyed by columns. n = 42 (evaluation-phase campaign runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.  a row is one arm of the evaluation phase on this configuration.  a column is a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 42 run(s) of st_regression, of which 42 finished.  construction: stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is A0 — steady state: there is no burn-time coupling, the pinned flat control degenerates onto the plain one and is skipped.  the arrangement-method calls are stamped beside the node calls and are never pooled into them.  the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.  these are campaign runs: the population named above and no other.  pairs are keyed by columns.*
| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A0 at columns | vs A0 pooled | vs A0 median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 14/14 | 63.0 | [42, 84] | 3.00 | — | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | 0.9333 | 1.0000 | 0 |
| A0 | 14/14 | 67.5 | [42, 84] | 3.21 | FLAT 45 | 0.0 | — | — | — | — |
| A1 | 14/14 | 38.9 | [19, 50] | 8.64 | FF 0, M1 31, M2 29, M3 33, PULSE 14 | 8.6 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | 0.5767 | 0.5714 | 0 |
*n = 42 (evaluation-phase campaign runs of st_regression).*
*How to read: a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost*

*How to read: a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost*

**`matched accuracy — st_regression — campaign_stencil_forward`**

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 42 run(s) of st_regression.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.  **audit position**: after_single_evaluation.  A residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.  **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.  the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.  **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic. Audit position: `after_single_evaluation`. n = 42 (evaluation-phase campaign runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 42 run(s) of st_regression.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.  **audit position**: after_single_evaluation.  A residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.  **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.  the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.  **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic.*
| arm | ruler | n (runs) | with a restricted statistic | restricted median | restricted p90 | restricted argmax | whole-state median | whole-state p90 | components excluded | audit position | audit instrument (snapshot positions taken) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 14 | 14 | 3.779e-11 | 3.920e-07 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 3.779e-11 | 3.920e-07 | 123 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 14 | 14 | 1.434e-11 | 2.735e-07 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 1.434e-11 | 2.735e-07 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 14 | 14 | 3.779e-11 | 2.137e-08 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 3.779e-11 | 2.137e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 14 | 14 | 1.434e-11 | 1.491e-08 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 1.434e-11 | 1.491e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 14 | 14 | 1.116e-10 | 2.137e-08 | fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 1.761e-03 | 5.969e-03 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | mixed | 14 | 14 | 7.789e-11 | 1.491e-08 | fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 1.021e-03 | 2.569e-03 | 123 | after_single_evaluation | no snapshot recorded on this record |
*n = 42 (evaluation-phase campaign runs of st_regression).*
*How to read: the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged*

*How to read: the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged*

**`per-sweep overhead — st_regression — campaign_stencil_forward`**

*Caption: units: counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  a row is one run of one arm.  a column is a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; the finished evaluation-phase campaign runs of st_regression.  construction: stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.  **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — and over this population it is 0 %, 10 %, 11.11 %, 12.5 %, 16.67 %.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.  no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone. n = 42 (finished evaluation-phase campaign runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  a row is one run of one arm.  a column is a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; the finished evaluation-phase campaign runs of st_regression.  construction: stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.  **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — and over this population it is 0 %, 10 %, 11.11 %, 12.5 %, 16.67 %.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.  no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone.*
| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 21 | 7.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 19 | 19.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 19 | 19.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 38 | 19.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 38 | 19.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 57 | 19.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 19 | 19.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 57 | 19.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10.0 | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1654 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1654 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 10 | 8 | 1957 | 244.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.00 % |
| A1 | 0 | coupling_state | 8 | 6 | 1414 | 235.7 | M1 268, M2 216, M3 223 | 0 | 0 | — | 12.50 % |
| A1 | 0 | coupling_state | 9 | 7 | 1689 | 241.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.11 % |
| A1 | 0 | coupling_state | 6 | 4 | 975 | 243.8 | M1 268, M2 216, M3 223 | 0 | 0 | — | 16.67 % |
| A1 | 0 | coupling_state | 9 | 7 | 1578 | 225.4 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.11 % |
| A1 | 0 | coupling_state | 9 | 7 | 1682 | 240.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.11 % |
| A1 | 0 | coupling_state | 9 | 7 | 1578 | 225.4 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.11 % |
| A1 | 0 | coupling_state | 10 | 8 | 1801 | 225.1 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.00 % |
| A1 | 0 | coupling_state | 8 | 6 | 1369 | 228.2 | M1 268, M2 216, M3 223 | 0 | 0 | — | 12.50 % |
| A1 | 0 | coupling_state | 9 | 7 | 1689 | 241.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.11 % |
| A1 | 0 | coupling_state | 8 | 6 | 1466 | 244.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 12.50 % |
| A1 | 0 | coupling_state | 10 | 8 | 1801 | 225.1 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.00 % |
| A1 | 0 | coupling_state | 8 | 6 | 1466 | 244.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 12.50 % |
| A1 | 0 | coupling_state | 8 | 6 | 1466 | 244.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 12.50 % |
*n = 42 (finished evaluation-phase campaign runs of st_regression).*
*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart*

*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart*

**`failure taxonomy — st_regression — campaign_stencil_forward`**

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; every campaign run of st_regression.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results. n = 42 (evaluation-phase campaign runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_stencil_forward — the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; every campaign run of st_regression.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.*
| arm | scheduled | ok | rows sum | detail (traceback's last line × count) |
|---|---|---|---|---|
| AR | 14 | 14 | yes | — |
| A0 | 14 | 14 | yes | — |
| A1 | 14 | 14 | yes | — |
*n = 42 (evaluation-phase campaign runs of st_regression).*
*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited*

*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited*

**`cost per call — large_tokamak_nof — campaign_stencil_backward`**

*Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.  a row is one arm of the evaluation phase on this configuration.  a column is a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 80 run(s) of large_tokamak_nof, of which 80 finished.  construction: stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is A0p — pulsed: the declared reference, because it and the partitioned arm sit on the same reduced map.  the arrangement-method calls are stamped beside the node calls and are never pooled into them.  the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.  these are campaign runs: the population named above and no other.  pairs are keyed by columns. n = 80 (evaluation-phase campaign runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.  a row is one arm of the evaluation phase on this configuration.  a column is a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 80 run(s) of large_tokamak_nof, of which 80 finished.  construction: stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is A0p — pulsed: the declared reference, because it and the partitioned arm sit on the same reduced map.  the arrangement-method calls are stamped beside the node calls and are never pooled into them.  the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.  these are campaign runs: the population named above and no other.  pairs are keyed by columns.*
| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A0p at columns | vs A0p pooled | vs A0p median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 20/20 | 60.9 | [42, 84] | 2.90 | — | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 0.9667 | 1.0000 | 0 |
| A0 | 20/20 | 66.2 | [42, 105] | 3.15 | FLAT 63 | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 1.0500 | 1.0000 | 3 |
| A0p | 20/20 | 63.0 | [42, 105] | 3.00 | FLAT 60 | 0.0 | — | — | — | — |
| A1 | 20/20 | 40.4 | [20, 55] | 7.70 | FF 0, M1 38, M2 49, M3 47, PULSE 0 | 7.7 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 0.6405 | 0.6071 | 0 |
*n = 80 (evaluation-phase campaign runs of large_tokamak_nof).*
*How to read: a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost*

*How to read: a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost*

**`matched accuracy — large_tokamak_nof — campaign_stencil_backward`**

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 80 run(s) of large_tokamak_nof.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.  **audit position**: after_single_evaluation.  A residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.  **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.  the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.  **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic. Audit position: `after_single_evaluation`. n = 80 (evaluation-phase campaign runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 80 run(s) of large_tokamak_nof.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.  **audit position**: after_single_evaluation.  A residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.  **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.  the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.  **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic.*
| arm | ruler | n (runs) | with a restricted statistic | restricted median | restricted p90 | restricted argmax | whole-state median | whole-state p90 | components excluded | audit position | audit instrument (snapshot positions taken) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 20 | 20 | 5.339e-15 | 1.730e-10 | blanket.deg_blkt_inboard_poloidal_plasma, heat_transport.tlvpmw, power.qac | 5.339e-15 | 1.730e-10 | 122 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 20 | 20 | 2.988e-15 | 1.730e-10 | blanket.deg_blkt_inboard_poloidal_plasma, heat_transport.tlvpmw, power.qac | 2.988e-15 | 1.730e-10 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 20 | 20 | 0 | 5.339e-15 | blanket.deg_blkt_inboard_poloidal_plasma, power.qac | 0 | 1.144e-14 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 20 | 20 | 0 | 2.988e-15 | blanket.deg_blkt_inboard_poloidal_plasma, power.qac | 0 | 2.988e-15 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0p | frozen | 20 | 20 | 0 | 8.309e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top, pf_coil.stress_z_cs_self_midplane_profile | 0 | 8.309e-16 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0p | mixed | 20 | 20 | 0 | 8.309e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.bpf2, pf_coil.stress_z_cs_self_midplane_profile | 0 | 8.309e-16 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 20 | 20 | 8.309e-16 | 4.523e-13 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top, pf_coil.stress_z_cs_self_midplane_profile | 2.016e-03 | 6.975e-02 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A1 | mixed | 20 | 20 | 8.309e-16 | 4.523e-13 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.bpf2, pf_coil.stress_z_cs_self_midplane_profile | 1.826e-03 | 1.079e-02 | 122 | after_single_evaluation | no snapshot recorded on this record |
*n = 80 (evaluation-phase campaign runs of large_tokamak_nof).*
*How to read: the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged*

*How to read: the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged*

**`ownership rung A0 → A0p — large_tokamak_nof — campaign_stencil_backward`**

*Caption: units: node-call ratio dimensionless; the burn-time residual in seconds and relative to the burn time.  a row is this configuration's rung.  a column is the cost of taking the burn time out of the flat loop, and the inconsistency the constant leaves behind.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 20 flat-control and 20 pinned run(s) of large_tokamak_nof.  construction: stats.ratio_triple on node calls of the single evaluation; the residual is constraint 93's own function at exit, |value|, median = nearest-rank upper-middle.  the residual is 0 by construction in the flat control, which converges the burn time, and is the price of the constant in the pinned arm.  neither column is a claim about the partition: this rung moves one thing only. n = 40 (A0 and A0p campaign runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: node-call ratio dimensionless; the burn-time residual in seconds and relative to the burn time.  a row is this configuration's rung.  a column is the cost of taking the burn time out of the flat loop, and the inconsistency the constant leaves behind.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 20 flat-control and 20 pinned run(s) of large_tokamak_nof.  construction: stats.ratio_triple on node calls of the single evaluation; the residual is constraint 93's own function at exit, |value|, median = nearest-rank upper-middle.  the residual is 0 by construction in the flat control, which converges the burn time, and is the price of the constant in the pinned arm.  neither column is a claim about the partition: this rung moves one thing only.*
| n | paired at columns | A0p/A0 pooled | median | worse | burn-time residual, s (median) | bracket, s | relative (median) |
|---|---|---|---|---|---|---|---|
| 20 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 0.9524 | 1.0000 | 0 | 1.175e+00 | [2.61418e-07, 13.1158] | 4.574e-04 |
*n = 40 (A0 and A0p campaign runs of large_tokamak_nof).*
*How to read: the ratio is the loop's cost of converging the burn time; the residual is what holding it constant costs in accuracy*

*How to read: the ratio is the loop's cost of converging the burn time; the residual is what holding it constant costs in accuracy*

**`per-sweep overhead — large_tokamak_nof — campaign_stencil_backward`**

*Caption: units: counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  a row is one run of one arm.  a column is a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; the finished evaluation-phase campaign runs of large_tokamak_nof.  construction: stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.  **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — and over this population it is 0 %.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.  no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone. n = 80 (finished evaluation-phase campaign runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  a row is one run of one arm.  a column is a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; the finished evaluation-phase campaign runs of large_tokamak_nof.  construction: stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.  **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — and over this population it is 0 %.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.  no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone.*
| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 4 | 4 | 3360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 4 | 4 | 3360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 4 | 4 | 3360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 4 | 4 | 3360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 10 | 9 | 2157 | 239.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 11 | 10 | 2397 | 239.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1456 | 242.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 9 | 8 | 1899 | 237.4 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1456 | 242.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 5 | 4 | 977 | 244.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 9 | 8 | 1881 | 235.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 10 | 9 | 2157 | 239.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 10 | 9 | 2121 | 235.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1420 | 236.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1456 | 242.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 6 | 5 | 1180 | 236.0 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 9 | 8 | 1881 | 235.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 6 | 5 | 1180 | 236.0 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 6 | 5 | 1180 | 236.0 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 6 | 5 | 1180 | 236.0 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1456 | 242.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 6 | 5 | 1180 | 236.0 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1456 | 242.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 9 | 8 | 1881 | 235.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
*n = 80 (finished evaluation-phase campaign runs of large_tokamak_nof).*
*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart*

*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart*

**`failure taxonomy — large_tokamak_nof — campaign_stencil_backward`**

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; every campaign run of large_tokamak_nof.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results. n = 80 (evaluation-phase campaign runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; every campaign run of large_tokamak_nof.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.*
| arm | scheduled | ok | rows sum | detail (traceback's last line × count) |
|---|---|---|---|---|
| AR | 20 | 20 | yes | — |
| A0 | 20 | 20 | yes | — |
| A0p | 20 | 20 | yes | — |
| A1 | 20 | 20 | yes | — |
*n = 80 (evaluation-phase campaign runs of large_tokamak_nof).*
*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited*

*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited*

**`cost per call — low_aspect_ratio_DEMO — campaign_stencil_backward`**

*Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.  a row is one arm of the evaluation phase on this configuration.  a column is a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 76 run(s) of low_aspect_ratio_DEMO, of which 76 finished.  construction: stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is A0p — pulsed: the declared reference, because it and the partitioned arm sit on the same reduced map.  the arrangement-method calls are stamped beside the node calls and are never pooled into them.  the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.  these are campaign runs: the population named above and no other.  pairs are keyed by columns. n = 76 (evaluation-phase campaign runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.  a row is one arm of the evaluation phase on this configuration.  a column is a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 76 run(s) of low_aspect_ratio_DEMO, of which 76 finished.  construction: stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is A0p — pulsed: the declared reference, because it and the partitioned arm sit on the same reduced map.  the arrangement-method calls are stamped beside the node calls and are never pooled into them.  the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.  these are campaign runs: the population named above and no other.  pairs are keyed by columns.*
| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A0p at columns | vs A0p pooled | vs A0p median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 19/19 | 67.4 | [42, 105] | 3.21 | — | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 1.0517 | 1.0000 | 4 |
| A0 | 19/19 | 68.5 | [42, 105] | 3.26 | FLAT 62 | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 1.0690 | 1.0000 | 4 |
| A0p | 19/19 | 64.1 | [42, 84] | 3.05 | FLAT 58 | 0.0 | — | — | — | — |
| A1 | 19/19 | 42.4 | [33, 55] | 7.84 | FF 0, M1 36, M2 46, M3 48, PULSE 0 | 7.8 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 0.6609 | 0.7143 | 0 |
*n = 76 (evaluation-phase campaign runs of low_aspect_ratio_DEMO).*
*How to read: a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost*

*How to read: a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost*

**`matched accuracy — low_aspect_ratio_DEMO — campaign_stencil_backward`**

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 76 run(s) of low_aspect_ratio_DEMO.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.  **audit position**: after_single_evaluation.  A residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.  **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.  the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.  **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic. Audit position: `after_single_evaluation`. n = 76 (evaluation-phase campaign runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 76 run(s) of low_aspect_ratio_DEMO.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.  **audit position**: after_single_evaluation.  A residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.  **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.  the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.  **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic.*
| arm | ruler | n (runs) | with a restricted statistic | restricted median | restricted p90 | restricted argmax | whole-state median | whole-state p90 | components excluded | audit position | audit instrument (snapshot positions taken) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0p | frozen | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0p | mixed | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.stress_z_cs_self_midplane_profile | 1.509e-03 | 8.370e-03 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | mixed | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.stress_z_cs_self_midplane_profile | 1.468e-03 | 8.370e-03 | 123 | after_single_evaluation | no snapshot recorded on this record |
*n = 76 (evaluation-phase campaign runs of low_aspect_ratio_DEMO).*
*How to read: the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged*

*How to read: the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged*

**`ownership rung A0 → A0p — low_aspect_ratio_DEMO — campaign_stencil_backward`**

*Caption: units: node-call ratio dimensionless; the burn-time residual in seconds and relative to the burn time.  a row is this configuration's rung.  a column is the cost of taking the burn time out of the flat loop, and the inconsistency the constant leaves behind.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 19 flat-control and 19 pinned run(s) of low_aspect_ratio_DEMO.  construction: stats.ratio_triple on node calls of the single evaluation; the residual is constraint 93's own function at exit, |value|, median = nearest-rank upper-middle.  the residual is 0 by construction in the flat control, which converges the burn time, and is the price of the constant in the pinned arm.  neither column is a claim about the partition: this rung moves one thing only. n = 38 (A0 and A0p campaign runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: node-call ratio dimensionless; the burn-time residual in seconds and relative to the burn time.  a row is this configuration's rung.  a column is the cost of taking the burn time out of the flat loop, and the inconsistency the constant leaves behind.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 19 flat-control and 19 pinned run(s) of low_aspect_ratio_DEMO.  construction: stats.ratio_triple on node calls of the single evaluation; the residual is constraint 93's own function at exit, |value|, median = nearest-rank upper-middle.  the residual is 0 by construction in the flat control, which converges the burn time, and is the price of the constant in the pinned arm.  neither column is a claim about the partition: this rung moves one thing only.*
| n | paired at columns | A0p/A0 pooled | median | worse | burn-time residual, s (median) | bracket, s | relative (median) |
|---|---|---|---|---|---|---|---|
| 19 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 0.9355 | 1.0000 | 0 | 4.184e+00 | [0, 34.1746] | 4.024e-04 |
*n = 38 (A0 and A0p campaign runs of low_aspect_ratio_DEMO).*
*How to read: the ratio is the loop's cost of converging the burn time; the residual is what holding it constant costs in accuracy*

*How to read: the ratio is the loop's cost of converging the burn time; the residual is what holding it constant costs in accuracy*

**`per-sweep overhead — low_aspect_ratio_DEMO — campaign_stencil_backward`**

*Caption: units: counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  a row is one run of one arm.  a column is a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; the finished evaluation-phase campaign runs of low_aspect_ratio_DEMO.  construction: stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.  **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — and over this population it is 0 %.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.  no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone. n = 76 (finished evaluation-phase campaign runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  a row is one run of one arm.  a column is a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; the finished evaluation-phase campaign runs of low_aspect_ratio_DEMO.  construction: stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.  **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — and over this population it is 0 %.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.  no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone.*
| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 53 | 17.7 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 53 | 17.7 | 0.00 % |
| AR | 0 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26.0 | 0.00 % |
| AR | 0 | upstream | 5 | 0 | 0 | — | — | 4 | 104 | 26.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 10 | 9 | 2172 | 241.3 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 11 | 10 | 2416 | 241.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1463 | 243.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 8 | 7 | 1669 | 238.4 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1463 | 243.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 8 | 7 | 1654 | 236.3 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 9 | 8 | 1898 | 237.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 10 | 9 | 2172 | 241.3 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 9 | 8 | 1898 | 237.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 8 | 7 | 1654 | 236.3 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 8 | 7 | 1654 | 236.3 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1463 | 243.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1410 | 235.0 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 8 | 7 | 1677 | 239.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1463 | 243.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 7 | 6 | 1463 | 243.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
*n = 76 (finished evaluation-phase campaign runs of low_aspect_ratio_DEMO).*
*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart*

*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart*

**`failure taxonomy — low_aspect_ratio_DEMO — campaign_stencil_backward`**

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; every campaign run of low_aspect_ratio_DEMO.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results. n = 76 (evaluation-phase campaign runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; every campaign run of low_aspect_ratio_DEMO.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.*
| arm | scheduled | ok | rows sum | detail (traceback's last line × count) |
|---|---|---|---|---|
| AR | 19 | 19 | yes | — |
| A0 | 19 | 19 | yes | — |
| A0p | 19 | 19 | yes | — |
| A1 | 19 | 19 | yes | — |
*n = 76 (evaluation-phase campaign runs of low_aspect_ratio_DEMO).*
*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited*

*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited*

**`cost per call — st_regression — campaign_stencil_backward`**

*Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.  a row is one arm of the evaluation phase on this configuration.  a column is a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 42 run(s) of st_regression, of which 42 finished.  construction: stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is A0 — steady state: there is no burn-time coupling, the pinned flat control degenerates onto the plain one and is skipped.  the arrangement-method calls are stamped beside the node calls and are never pooled into them.  the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.  these are campaign runs: the population named above and no other.  pairs are keyed by columns. n = 42 (evaluation-phase campaign runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.  a row is one arm of the evaluation phase on this configuration.  a column is a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 42 run(s) of st_regression, of which 42 finished.  construction: stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is A0 — steady state: there is no burn-time coupling, the pinned flat control degenerates onto the plain one and is skipped.  the arrangement-method calls are stamped beside the node calls and are never pooled into them.  the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.  these are campaign runs: the population named above and no other.  pairs are keyed by columns.*
| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A0 at columns | vs A0 pooled | vs A0 median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 14/14 | 66.0 | [42, 84] | 3.14 | — | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | 0.9362 | 1.0000 | 0 |
| A0 | 14/14 | 70.5 | [42, 105] | 3.36 | FLAT 47 | 0.0 | — | — | — | — |
| A1 | 14/14 | 39.4 | [19, 53] | 8.79 | FF 0, M1 31, M2 31, M3 33, PULSE 14 | 8.8 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | 0.5583 | 0.5238 | 0 |
*n = 42 (evaluation-phase campaign runs of st_regression).*
*How to read: a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost*

*How to read: a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost*

**`matched accuracy — st_regression — campaign_stencil_backward`**

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 42 run(s) of st_regression.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.  **audit position**: after_single_evaluation.  A residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.  **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.  the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.  **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic. Audit position: `after_single_evaluation`. n = 42 (evaluation-phase campaign runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; 42 run(s) of st_regression.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.  **audit position**: after_single_evaluation.  A residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.  **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.  the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.  **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic.*
| arm | ruler | n (runs) | with a restricted statistic | restricted median | restricted p90 | restricted argmax | whole-state median | whole-state p90 | components excluded | audit position | audit instrument (snapshot positions taken) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 14 | 14 | 6.459e-14 | 4.272e-08 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 6.459e-14 | 4.272e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 14 | 14 | 6.459e-14 | 2.983e-08 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 6.459e-14 | 2.983e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 14 | 14 | 0 | 2.670e-08 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.radius_beam_tangency_max, superconducting_tfcoil.a_tf_plasma_case | 0 | 2.670e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 14 | 14 | 0 | 1.864e-08 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.radius_beam_tangency_max, superconducting_tfcoil.a_tf_plasma_case | 0 | 1.864e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 14 | 14 | 1.560e-11 | 2.670e-08 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 1.760e-03 | 5.988e-03 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | mixed | 14 | 14 | 5.919e-12 | 1.864e-08 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 1.022e-03 | 2.579e-03 | 123 | after_single_evaluation | no snapshot recorded on this record |
*n = 42 (evaluation-phase campaign runs of st_regression).*
*How to read: the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged*

*How to read: the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged*

**`per-sweep overhead — st_regression — campaign_stencil_backward`**

*Caption: units: counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  a row is one run of one arm.  a column is a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; the finished evaluation-phase campaign runs of st_regression.  construction: stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.  **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — and over this population it is 0 %, 9.09 %, 10 %, 11.11 %, 12.5 %, 16.67 %.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.  no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone. n = 42 (finished evaluation-phase campaign runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  a row is one run of one arm.  a column is a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; the finished evaluation-phase campaign runs of st_regression.  construction: stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.  **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — and over this population it is 0 %, 9.09 %, 10 %, 11.11 %, 12.5 %, 16.67 %.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.  no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone.*
| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 21 | 7.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 19 | 19.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 19 | 19.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 57 | 19.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 57 | 19.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 57 | 19.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 19 | 19.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 57 | 19.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10.0 | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1654 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1654 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4135 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4135 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 10 | 8 | 1957 | 244.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.00 % |
| A1 | 0 | coupling_state | 8 | 6 | 1414 | 235.7 | M1 268, M2 216, M3 223 | 0 | 0 | — | 12.50 % |
| A1 | 0 | coupling_state | 9 | 7 | 1689 | 241.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.11 % |
| A1 | 0 | coupling_state | 6 | 4 | 975 | 243.8 | M1 268, M2 216, M3 223 | 0 | 0 | — | 16.67 % |
| A1 | 0 | coupling_state | 9 | 7 | 1578 | 225.4 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.11 % |
| A1 | 0 | coupling_state | 9 | 7 | 1682 | 240.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.11 % |
| A1 | 0 | coupling_state | 9 | 7 | 1578 | 225.4 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.11 % |
| A1 | 0 | coupling_state | 11 | 9 | 2017 | 224.1 | M1 268, M2 216, M3 223 | 0 | 0 | — | 9.09 % |
| A1 | 0 | coupling_state | 8 | 6 | 1369 | 228.2 | M1 268, M2 216, M3 223 | 0 | 0 | — | 12.50 % |
| A1 | 0 | coupling_state | 9 | 7 | 1689 | 241.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.11 % |
| A1 | 0 | coupling_state | 8 | 6 | 1466 | 244.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 12.50 % |
| A1 | 0 | coupling_state | 11 | 9 | 2017 | 224.1 | M1 268, M2 216, M3 223 | 0 | 0 | — | 9.09 % |
| A1 | 0 | coupling_state | 8 | 6 | 1466 | 244.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 12.50 % |
| A1 | 0 | coupling_state | 8 | 6 | 1466 | 244.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 12.50 % |
*n = 42 (finished evaluation-phase campaign runs of st_regression).*
*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart*

*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart*

**`failure taxonomy — st_regression — campaign_stencil_backward`**

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; every campaign run of st_regression.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results. n = 42 (evaluation-phase campaign runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_stencil_backward — the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; every campaign run of st_regression.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.*
| arm | scheduled | ok | rows sum | detail (traceback's last line × count) |
|---|---|---|---|---|
| AR | 14 | 14 | yes | — |
| A0 | 14 | 14 | yes | — |
| A1 | 14 | 14 | yes | — |
*n = 42 (evaluation-phase campaign runs of st_regression).*
*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited*

*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited*

**`the predicate trial — frozen against mixed`**

*Caption: units: counts of predicate evaluations; the audit columns are hex floats of the largest scaled residual.  a row is one pair of runs — the same arm, configuration and seed under each ruler.  a column is a count of the trial, or one run's exit audit read on one named ruler.  population: 12 pair(s) = 3 configuration(s) x the evaluation-phase arms active on each (A0, A1) x 2 seed(s), each run under both rulers = 24 runs at delta = 0.1; 8068 deterministic record values and 84 output-file lines compared without tolerance, 240 record values excluded as the setting being varied or as run metadata (each named, with its reason, in this record); 143 predicate evaluations observed on both rulers.  construction: the trial gate's observer, which watches each predicate evaluation of the frozen run and reads it again on the mixed ruler; the record comparison is bit-for-bit with no tolerance.  **decisive passes are published as two counts** (the plan's §4.2.5 caption rule): *crossings* — evaluations at which some component crossed the tolerance between the rulers — and *verdict changes* — evaluations whose verdict changed because the crossing component was the one holding the evaluation open.  Only the second can make two runs differ, and the gate binds on it.  **the exit audit is on both rulers, never one**: each run is audited on the frozen and the mixed ruler, so a difference between the audit columns of one row is a change of ruler and a difference down a column is a change of run.  the components that made a pass decisive carry |y|/s up to 54.59 over this population. n = 12 (pairs of runs, one per ruler). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of predicate evaluations; the audit columns are hex floats of the largest scaled residual.  a row is one pair of runs — the same arm, configuration and seed under each ruler.  a column is a count of the trial, or one run's exit audit read on one named ruler.  population: 12 pair(s) = 3 configuration(s) x the evaluation-phase arms active on each (A0, A1) x 2 seed(s), each run under both rulers = 24 runs at delta = 0.1; 8068 deterministic record values and 84 output-file lines compared without tolerance, 240 record values excluded as the setting being varied or as run metadata (each named, with its reason, in this record); 143 predicate evaluations observed on both rulers.  construction: the trial gate's observer, which watches each predicate evaluation of the frozen run and reads it again on the mixed ruler; the record comparison is bit-for-bit with no tolerance.  **decisive passes are published as two counts** (the plan's §4.2.5 caption rule): *crossings* — evaluations at which some component crossed the tolerance between the rulers — and *verdict changes* — evaluations whose verdict changed because the crossing component was the one holding the evaluation open.  Only the second can make two runs differ, and the gate binds on it.  **the exit audit is on both rulers, never one**: each run is audited on the frozen and the mixed ruler, so a difference between the audit columns of one row is a change of ruler and a difference down a column is a change of run.  the components that made a pass decisive carry |y|/s up to 54.59 over this population.*
| configuration | arm | seed | predicate evaluations | decisive passes: crossings | decisive passes: verdicts changed | pair bit-identical | frozen run · frozen ruler | frozen run · mixed ruler | mixed run · frozen ruler | mixed run · mixed ruler |
|---|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | A0 | 1 | 9 | 3 | 0 | yes | 0x1.5fe433222bb97p-29 | 0x1.f8c2a9ec36d62p-31 | 0x1.5fe433222bb97p-29 | 0x1.f8c2a9ec36d62p-31 |
| large_tokamak_nof | A0 | 2 | 8 | 1 | 0 | yes | 0x0.0p+0 | 0x0.0p+0 | 0x0.0p+0 | 0x0.0p+0 |
| large_tokamak_nof | A1 | 1 | 15 | 2 | 0 | yes | 0x1.f5b2a3ea40bd7p-1 | 0x1.774db44e2d2b1p-3 | 0x1.f5b2a3ea40bd7p-1 | 0x1.774db44e2d2b1p-3 |
| large_tokamak_nof | A1 | 2 | 15 | 1 | 0 | yes | 0x1.c4dcc35b240c9p+0 | 0x1.656469d523e7ep-2 | 0x1.c4dcc35b240c9p+0 | 0x1.656469d523e7ep-2 |
| low_aspect_ratio_DEMO | A0 | 1 | 8 | 0 | 0 | yes | 0x0.0p+0 | 0x0.0p+0 | 0x0.0p+0 | 0x0.0p+0 |
| low_aspect_ratio_DEMO | A0 | 2 | 8 | 1 | 0 | yes | 0x0.0p+0 | 0x0.0p+0 | 0x0.0p+0 | 0x0.0p+0 |
| low_aspect_ratio_DEMO | A1 | 1 | 15 | 0 | 0 | yes | 0x1.ad17b67239f49p-4 | 0x1.a621cc5cabcc8p-4 | 0x1.ad17b67239f49p-4 | 0x1.a621cc5cabcc8p-4 |
| low_aspect_ratio_DEMO | A1 | 2 | 15 | 0 | 0 | yes | 0x1.2cdce94f65769p-3 | 0x1.24c92dd10e577p-3 | 0x1.2cdce94f65769p-3 | 0x1.24c92dd10e577p-3 |
| st_regression | A0 | 1 | 9 | 2 | 0 | yes | 0x1.9e44b1da8552dp-29 | 0x1.211b7a2189fc0p-29 | 0x1.9e44b1da8552dp-29 | 0x1.211b7a2189fc0p-29 |
| st_regression | A0 | 2 | 9 | 1 | 0 | yes | 0x1.05028b3bcc6bfp-27 | 0x1.6c4dec4c0f592p-28 | 0x1.05028b3bcc6bfp-27 | 0x1.6c4dec4c0f592p-28 |
| st_regression | A1 | 1 | 16 | 1 | 0 | yes | 0x1.fabf584472547p-3 | 0x1.3cec1f486b6d0p-3 | 0x1.fabf584472547p-3 | 0x1.3cec1f486b6d0p-3 |
| st_regression | A1 | 2 | 16 | 1 | 0 | yes | 0x1.e15dc1afec083p-3 | 0x1.ccd4e2d6e3fcap-4 | 0x1.e15dc1afec083p-3 | 0x1.ccd4e2d6e3fcap-4 |
*n = 12 (pairs of runs, one per ruler).*
*How to read: a pair with no verdict change must be bit-identical, which is the gate's identity; every difference in this table is attributable to the named components*

*How to read: a pair with no verdict change must be bit-identical, which is the gate's identity; every difference in this table is attributable to the named components*

### 4.3 The optimisation phase

*Emitted by `experiment_runner.py --measure tally_optimisation`; the seed set and the failure table, the same-optimum check, both iteration constructions, the attempt-summation identity, the cost with and without the retried seeds, and the lift's residual.*

**`failure taxonomy — large_tokamak_nof — campaign_optimisation`**

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; every campaign run of large_tokamak_nof, every start.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped; stats.crash_detail for the detail.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  a crashed start is counted here and in the failure table, and reaches no cost cell: the cost tables are over the every-arm-converged seed set (plan §3.5). n = 100 (optimisation-phase campaign runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; every campaign run of large_tokamak_nof, every start.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped; stats.crash_detail for the detail.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  a crashed start is counted here and in the failure table, and reaches no cost cell: the cost tables are over the every-arm-converged seed set (plan §3.5).*
| arm | scheduled | crashed | ok | rows sum | detail (traceback's last line × count) |
|---|---|---|---|---|---|
| BR | 25 | 3 | 22 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×3 |
| B0 | 25 | 3 | 22 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×3 |
| B1 | 25 | 3 | 22 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×3 |
| B3 | 25 | 3 | 22 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×3 |
*n = 100 (optimisation-phase campaign runs of large_tokamak_nof).*
*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited; the detail says whether one failure mode or several*

*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited; the detail says whether one failure mode or several*

**`the seed set — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: counts of seeds.  a row is this configuration.  a column is the size of the one population every optimisation-phase table on this configuration is over, or a per-arm count of the seeds on which the optimiser was called more than once.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; the arms present here are BR, B0, B1, B3 at seeds 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24.  construction: stats.every_arm_converged — a seed is in the set when every arm present reached an accepted optimum (status ok AND the output file's ifail == 1); stats.retried, which counts attempts[] and never a stored flag.  **this is one arm group of the source.**  The plan's construction assumes what a campaign guarantees — every arm at every seed — and a gate's runs do not: the source is therefore split by which arms have a run at a seed, and each group is a population the construction applies to.  The group is named in this table's title and in every other table of the same group.  the seeds outside the set are not dropped: they are the failure table, published beside this one, so an arm that fails on expensive seeds cannot be flattered by the filter.  a seed on which **no** arm converged is configuration hardness, counted in its own column and not against any arm. n = 25 (distinct seeds run on large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of seeds.  a row is this configuration.  a column is the size of the one population every optimisation-phase table on this configuration is over, or a per-arm count of the seeds on which the optimiser was called more than once.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; the arms present here are BR, B0, B1, B3 at seeds 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24.  construction: stats.every_arm_converged — a seed is in the set when every arm present reached an accepted optimum (status ok AND the output file's ifail == 1); stats.retried, which counts attempts[] and never a stored flag.  **this is one arm group of the source.**  The plan's construction assumes what a campaign guarantees — every arm at every seed — and a gate's runs do not: the source is therefore split by which arms have a run at a seed, and each group is a population the construction applies to.  The group is named in this table's title and in every other table of the same group.  the seeds outside the set are not dropped: they are the failure table, published beside this one, so an arm that fails on expensive seeds cannot be flattered by the filter.  a seed on which **no** arm converged is configuration hardness, counted in its own column and not against any arm.*
| arms | which | seeds offered | n (every arm converged) | seeds in the set | configuration-invalid seeds | retried seeds per arm |
|---|---|---|---|---|---|---|
| 4 | BR · B0 · B1 · B3 | 25 | 22 | 0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 22, 23, 24 | 3 | BR 0 · B0 0 · B1 0 · B3 0 |
*n = 25 (distinct seeds run on large_tokamak_nof).*
*How to read: this n is the denominator of every other optimisation-phase table on this configuration*

*How to read: this n is the denominator of every other optimisation-phase table on this configuration*

**`the failure table — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: counts: model executions for the cost columns, optimiser exit codes for ifail.  a row is one seed outside the converged set.  a column is which arm failed there, how it failed, what it cost, and what the other arms cost at the same start.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 3 of 25 seed(s) on large_tokamak_nof lie outside the every-arm-converged set.  construction: stats.accepted_optimum for membership; the cost column is node_calls_solve_phase, the same unit the cost table uses.  an arm the gate did not run at a seed reads *not run* rather than *failed*: an absent record and a failed run are different results.  a seed on which every arm failed or was absent is marked configuration-invalid. n = 25 (distinct seeds run on large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts: model executions for the cost columns, optimiser exit codes for ifail.  a row is one seed outside the converged set.  a column is which arm failed there, how it failed, what it cost, and what the other arms cost at the same start.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 3 of 25 seed(s) on large_tokamak_nof lie outside the every-arm-converged set.  construction: stats.accepted_optimum for membership; the cost column is node_calls_solve_phase, the same unit the cost table uses.  an arm the gate did not run at a seed reads *not run* rather than *failed*: an absent record and a failed run are different results.  a seed on which every arm failed or was absent is marked configuration-invalid.*
| seed | failed arm(s) | not run | ifail | attempts | failed arm node calls | other arms' node calls | configuration-invalid |
|---|---|---|---|---|---|---|---|
| 5 | BR, B0, B1, B3 | — | None, None, None, None | 1, 1, 1, 1 | None, None, None, None | BR — / B0 — / B1 — / B3 — | yes |
| 20 | BR, B0, B1, B3 | — | None, None, None, None | 1, 1, 1, 1 | None, None, None, None | BR — / B0 — / B1 — / B3 — | yes |
| 21 | BR, B0, B1, B3 | — | None, None, None, None | 1, 1, 1, 1 | None, None, None, None | BR — / B0 — / B1 — / B3 — | yes |
*n = 25 (distinct seeds run on large_tokamak_nof).*
*How to read: the converged set is the fairer cost population but can flatter an arm that fails on expensive seeds; this table is what keeps it honest*

*How to read: the converged set is the fairer cost population but can flatter an arm that fails on expensive seeds; this table is what keeps it honest*

**`same optimum (check 1) — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: dimensionless: a relative difference of the normalised objective.  a row is one arm pair over the seed set.  a column is the paired relative objective difference's median and p90, the threshold they are judged against, and the clustering statistics.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 22 seed(s) on which every arm of large_tokamak_nof reached an accepted optimum.  construction: stats.relative_objective_difference — |Δ norm_objf| / max(|a|, |b|) per pair, from the hex floats; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); stats.acceptance_threshold = max(F × yardstick, floor) with F = 10 and floor = 1e-06, the yardstick being the BR → B0 spread measured in this same population; stats.clusters at a relative gap of 1e-05.  the yardstick row carries no threshold and no verdict: it *is* the threshold's calibration.  *below resolution* counts pairs further apart than the correctness floor and closer than the cluster gap — distinct optima below cluster resolution, a named category and not a rounding remark.  the retried column is computed from attempts[], never from a stored flag, so a pair containing a retry is visible here as well as in the cost table. n = 22 (seeds on which every arm of large_tokamak_nof converged). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless: a relative difference of the normalised objective.  a row is one arm pair over the seed set.  a column is the paired relative objective difference's median and p90, the threshold they are judged against, and the clustering statistics.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 22 seed(s) on which every arm of large_tokamak_nof reached an accepted optimum.  construction: stats.relative_objective_difference — |Δ norm_objf| / max(|a|, |b|) per pair, from the hex floats; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); stats.acceptance_threshold = max(F × yardstick, floor) with F = 10 and floor = 1e-06, the yardstick being the BR → B0 spread measured in this same population; stats.clusters at a relative gap of 1e-05.  the yardstick row carries no threshold and no verdict: it *is* the threshold's calibration.  *below resolution* counts pairs further apart than the correctness floor and closer than the cluster gap — distinct optima below cluster resolution, a named category and not a rounding remark.  the retried column is computed from attempts[], never from a stored flag, so a pair containing a retry is visible here as well as in the cost table.*
| pair | n | r median | r p90 | threshold median | threshold p90 | verdict | hops | below resolution | retried seeds in pair |
|---|---|---|---|---|---|---|---|---|---|
| BR → B0 (yardstick) | 22 | 2.082e-15 | 6.893e-13 | — | — | — | 0/22 (0.00) | 0 | 0 |
| B0 → B1 | 22 | 2.823e-11 | 4.570e-11 | 1.000e-06 | 1.000e-06 | PASS | 0/22 (0.00) | 0 | 0 |
| B0 → B3 | 22 | 2.823e-11 | 4.570e-11 | 1.000e-06 | 1.000e-06 | PASS | 0/22 (0.00) | 0 | 0 |
*n = 22 (seeds on which every arm of large_tokamak_nof converged).*
*How to read: a verdict is read only where a threshold exists; a hop is a seed whose two sides landed in different objective clusters, and the yardstick pair's own hop rate is the comparator*

*How to read: a verdict is read only where a threshold exists; a hop is a seed whose two sides landed in different objective clusters, and the yardstick pair's own hop rate is the comparator*

**`iteration multiplier (check 2) — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: dimensionless ratios of counts.  a row is one arm against the flat control over the seed set.  a column is one of check 2's two iteration constructions, its sum ratio, or the evaluation-count ratio beside them.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 22 seed(s) on which every arm of large_tokamak_nof reached an accepted optimum.  construction: stats.iterations_summed_over_attempts (the **declared acceptance statistic**, nearest-rank upper-middle median against 1.05) and stats.iterations_final_attempt (the previous revision's construction, published beside for comparability).  Both are read from attempts[], so a disagreement between them is a disagreement about that list and not about which field was read.  the sum ratio is published beside every median because a median of per-seed ratios and the ratio of the sums can point in opposite directions.  the evaluation-count ratio is beside both: iterations, even summed, miss the lifted arm's extra stencil column and the line-search evaluations that vary at equal iteration count.  *constructions disagree* counts the seeds on which the final attempt's pair and the summed pair are not the same numbers — 0 means no run in this population retried. n = 22 (seeds on which every arm of large_tokamak_nof converged). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless ratios of counts.  a row is one arm against the flat control over the seed set.  a column is one of check 2's two iteration constructions, its sum ratio, or the evaluation-count ratio beside them.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 22 seed(s) on which every arm of large_tokamak_nof reached an accepted optimum.  construction: stats.iterations_summed_over_attempts (the **declared acceptance statistic**, nearest-rank upper-middle median against 1.05) and stats.iterations_final_attempt (the previous revision's construction, published beside for comparability).  Both are read from attempts[], so a disagreement between them is a disagreement about that list and not about which field was read.  the sum ratio is published beside every median because a median of per-seed ratios and the ratio of the sums can point in opposite directions.  the evaluation-count ratio is beside both: iterations, even summed, miss the lifted arm's extra stencil column and the line-search evaluations that vary at equal iteration count.  *constructions disagree* counts the seeds on which the final attempt's pair and the summed pair are not the same numbers — 0 means no run in this population retried.*
| pair | n | summed median (acceptance) | summed sum ratio | verdict | final-attempt median | final-attempt sum ratio | evaluations median | attempts per seed (base/arm) | constructions disagree |
|---|---|---|---|---|---|---|---|---|---|
| B0 → BR (beside) | 22 | 1.0000 | 1.0000 | beside | 1.0000 | 1.0000 | 0.9795 | 0:1/1, 1:1/1, 2:1/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 10:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 17:1/1, 18:1/1, 19:1/1, 22:1/1, 23:1/1, 24:1/1 | 0 |
| B0 → B1 | 22 | 1.0000 | 0.9942 | PASS | 1.0000 | 0.9942 | 1.0139 | 0:1/1, 1:1/1, 2:1/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 10:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 17:1/1, 18:1/1, 19:1/1, 22:1/1, 23:1/1, 24:1/1 | 0 |
| B0 → B3 | 22 | 1.0000 | 0.9942 | PASS | 1.0000 | 0.9942 | 2.6524 | 0:1/1, 1:1/1, 2:1/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 10:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 17:1/1, 18:1/1, 19:1/1, 22:1/1, 23:1/1, 24:1/1 | 0 |
*n = 22 (seeds on which every arm of large_tokamak_nof converged).*
*How to read: read the acceptance column against the summed median; a final-attempt median that differs from it names the retried seeds, which the attempts column lists*

*How to read: read the acceptance column against the summed median; a final-attempt median that differs from it names the retried seeds, which the attempts column lists*

**`cost (check 4) — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: model executions during the solve; ratios dimensionless.  a row is one arm over the seed set.  a column is an absolute per-run mean with its bracket, or one reading of the ratio against the flat control.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 22 seed(s) on which every arm of large_tokamak_nof reached an accepted optimum.  construction: stats.with_and_without_retried — solve-phase node calls **summed over attempts[]** per run, so the ratio is over the quantity the attempts decompose (the identity is in the attempt-summation table); pooled = Σ arm / Σ base, median = nearest-rank upper-middle of the per-seed ratios, worse = seeds on which the arm cost more.  **retries are a term, not a footnote**: the ratio is published *with* and *without* the retried seeds because both readings are defensible — a retry the other arm did not need is real cost the architecture avoided at that start, *and* it is a robustness event rather than a per-evaluation cost.  a seed counts as retried when **either** side of the pair retried: the pair is what the ratio is over.  the arrangement-method calls are a column of their own and are never pooled into the node calls.  the output-time and audit sweeps are excluded from this unit symmetrically in every arm. n = 22 (seeds on which every arm of large_tokamak_nof converged). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model executions during the solve; ratios dimensionless.  a row is one arm over the seed set.  a column is an absolute per-run mean with its bracket, or one reading of the ratio against the flat control.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 22 seed(s) on which every arm of large_tokamak_nof reached an accepted optimum.  construction: stats.with_and_without_retried — solve-phase node calls **summed over attempts[]** per run, so the ratio is over the quantity the attempts decompose (the identity is in the attempt-summation table); pooled = Σ arm / Σ base, median = nearest-rank upper-middle of the per-seed ratios, worse = seeds on which the arm cost more.  **retries are a term, not a footnote**: the ratio is published *with* and *without* the retried seeds because both readings are defensible — a retry the other arm did not need is real cost the architecture avoided at that start, *and* it is a robustness event rather than a per-evaluation cost.  a seed counts as retried when **either** side of the pair retried: the pair is what the ratio is over.  the arrangement-method calls are a column of their own and are never pooled into the node calls.  the output-time and audit sweeps are excluded from this unit symmetrically in every arm.*
| arm | n | node calls / run | bracket | arrangement·method calls | with retried: pooled | with retried: median | worse | retried seeds | without retried: pooled | without retried: median | n without |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | 22 | 41479.8 | [36855, 47817] | 0 | 0.9756 | 0.9794 | 0 | 0 | 0.9756 | 0.9794 | 22 |
| B0 | 22 | 42515.5 | [37590, 50253] | 0 | 1.0000 | 1.0000 | 0 | 0 | 1.0000 | 1.0000 | 22 |
| B1 | 22 | 42841.9 | [38220, 49980] | 0 | 1.0077 | 1.0151 | 18 | 0 | 1.0077 | 1.0151 | 22 |
| B3 | 22 | 27187.5 | [24296, 31813] | 117281 | 0.6395 | 0.6452 | 0 | 0 | 0.6395 | 0.6452 | 22 |
*n = 22 (seeds on which every arm of large_tokamak_nof converged).*
*How to read: where *retried* is 0 the with- and without- columns are the same number, and the pair of columns is the statement that nothing in this population depended on a retry*

*How to read: where *retried* is 0 the with- and without- columns are the same number, and the pair of columns is the statement that nothing in this population depended on a retry*

**`the attempt summation identity — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: counts: model executions and sweeps of the model sequence.  a row is one optimisation run.  a column is the per-attempt costs, the run's solve-phase total they decompose, and the residual between them.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 100 optimisation run(s) of large_tokamak_nof, of which 100 carry a per-attempt cost the identity can be checked on.  construction: stats.attempt_summation — Σ over attempts[] against node_calls_solve_phase and dispatch_sweeps_solve_phase.  this identity is why the with- and without-retried-seeds cost ratios may be published: they are computed over quantities that visibly decompose the published total, and a residual that is not 0 would make them ratios of something else.  the record contract already refuses a record whose parts do not add up; this table is the same identity stated as a number a reader can see. n = 100 (optimisation-phase campaign runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts: model executions and sweeps of the model sequence.  a row is one optimisation run.  a column is the per-attempt costs, the run's solve-phase total they decompose, and the residual between them.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 100 optimisation run(s) of large_tokamak_nof, of which 100 carry a per-attempt cost the identity can be checked on.  construction: stats.attempt_summation — Σ over attempts[] against node_calls_solve_phase and dispatch_sweeps_solve_phase.  this identity is why the with- and without-retried-seeds cost ratios may be published: they are computed over quantities that visibly decompose the published total, and a residual that is not 0 would make them ratios of something else.  the record contract already refuses a record whose parts do not add up; this table is the same identity stated as a number a reader can see.*
| arm | seed | attempts | retried | node calls per attempt | = solve-phase total | residual | sweeps per attempt | = solve-phase total | residual | decomposes |
|---|---|---|---|---|---|---|---|---|---|---|
| BR | 0 | 1 | no | 42567 | 42567 | 0 | 2027 | 2027 | 0 | yes |
| BR | 1 | 1 | no | 42399 | 42399 | 0 | 2019 | 2019 | 0 | yes |
| BR | 2 | 1 | no | 47817 | 47817 | 0 | 2277 | 2277 | 0 | yes |
| BR | 3 | 1 | no | 36897 | 36897 | 0 | 1757 | 1757 | 0 | yes |
| BR | 4 | 1 | no | 36939 | 36939 | 0 | 1759 | 1759 | 0 | yes |
| BR | 5 | 1 | no | — | — | — | — | — | — | NO |
| BR | 6 | 1 | no | 42714 | 42714 | 0 | 2034 | 2034 | 0 | yes |
| BR | 7 | 1 | no | 42630 | 42630 | 0 | 2030 | 2030 | 0 | yes |
| BR | 8 | 1 | no | 42672 | 42672 | 0 | 2032 | 2032 | 0 | yes |
| BR | 9 | 1 | no | 42504 | 42504 | 0 | 2024 | 2024 | 0 | yes |
| BR | 10 | 1 | no | 37044 | 37044 | 0 | 1764 | 1764 | 0 | yes |
| BR | 11 | 1 | no | 42063 | 42063 | 0 | 2003 | 2003 | 0 | yes |
| BR | 12 | 1 | no | 42567 | 42567 | 0 | 2027 | 2027 | 0 | yes |
| BR | 13 | 1 | no | 42399 | 42399 | 0 | 2019 | 2019 | 0 | yes |
| BR | 14 | 1 | no | 47817 | 47817 | 0 | 2277 | 2277 | 0 | yes |
| BR | 15 | 1 | no | 36876 | 36876 | 0 | 1756 | 1756 | 0 | yes |
| BR | 16 | 1 | no | 36855 | 36855 | 0 | 1755 | 1755 | 0 | yes |
| BR | 17 | 1 | no | 42525 | 42525 | 0 | 2025 | 2025 | 0 | yes |
| BR | 18 | 1 | no | 42525 | 42525 | 0 | 2025 | 2025 | 0 | yes |
| BR | 19 | 1 | no | 42588 | 42588 | 0 | 2028 | 2028 | 0 | yes |
| BR | 20 | 1 | no | — | — | — | — | — | — | NO |
| BR | 21 | 1 | no | — | — | — | — | — | — | NO |
| BR | 22 | 1 | no | 36981 | 36981 | 0 | 1761 | 1761 | 0 | yes |
| BR | 23 | 1 | no | 42630 | 42630 | 0 | 2030 | 2030 | 0 | yes |
| BR | 24 | 1 | no | 42546 | 42546 | 0 | 2026 | 2026 | 0 | yes |
| B0 | 0 | 1 | no | 43449 | 43449 | 0 | 2069 | 2069 | 0 | yes |
| B0 | 1 | 1 | no | 43491 | 43491 | 0 | 2071 | 2071 | 0 | yes |
| B0 | 2 | 1 | no | 49623 | 49623 | 0 | 2363 | 2363 | 0 | yes |
| B0 | 3 | 1 | no | 37695 | 37695 | 0 | 1795 | 1795 | 0 | yes |
| B0 | 4 | 1 | no | 37590 | 37590 | 0 | 1790 | 1790 | 0 | yes |
| B0 | 5 | 1 | no | — | — | — | — | — | — | NO |
| B0 | 6 | 1 | no | 43449 | 43449 | 0 | 2069 | 2069 | 0 | yes |
| B0 | 7 | 1 | no | 43428 | 43428 | 0 | 2068 | 2068 | 0 | yes |
| B0 | 8 | 1 | no | 43428 | 43428 | 0 | 2068 | 2068 | 0 | yes |
| B0 | 9 | 1 | no | 43470 | 43470 | 0 | 2070 | 2070 | 0 | yes |
| B0 | 10 | 1 | no | 37590 | 37590 | 0 | 1790 | 1790 | 0 | yes |
| B0 | 11 | 1 | no | 44583 | 44583 | 0 | 2123 | 2123 | 0 | yes |
| B0 | 12 | 1 | no | 43428 | 43428 | 0 | 2068 | 2068 | 0 | yes |
| B0 | 13 | 1 | no | 43533 | 43533 | 0 | 2073 | 2073 | 0 | yes |
| B0 | 14 | 1 | no | 50253 | 50253 | 0 | 2393 | 2393 | 0 | yes |
| B0 | 15 | 1 | no | 37737 | 37737 | 0 | 1797 | 1797 | 0 | yes |
| B0 | 16 | 1 | no | 37674 | 37674 | 0 | 1794 | 1794 | 0 | yes |
| B0 | 17 | 1 | no | 43470 | 43470 | 0 | 2070 | 2070 | 0 | yes |
| B0 | 18 | 1 | no | 43323 | 43323 | 0 | 2063 | 2063 | 0 | yes |
| B0 | 19 | 1 | no | 43407 | 43407 | 0 | 2067 | 2067 | 0 | yes |
| B0 | 20 | 1 | no | — | — | — | — | — | — | NO |
| B0 | 21 | 1 | no | — | — | — | — | — | — | NO |
| B0 | 22 | 1 | no | 37758 | 37758 | 0 | 1798 | 1798 | 0 | yes |
| B0 | 23 | 1 | no | 43386 | 43386 | 0 | 2066 | 2066 | 0 | yes |
| B0 | 24 | 1 | no | 43575 | 43575 | 0 | 2075 | 2075 | 0 | yes |
| B1 | 0 | 1 | no | 44142 | 44142 | 0 | 2102 | 2102 | 0 | yes |
| B1 | 1 | 1 | no | 44100 | 44100 | 0 | 2100 | 2100 | 0 | yes |
| B1 | 2 | 1 | no | 44142 | 44142 | 0 | 2102 | 2102 | 0 | yes |
| B1 | 3 | 1 | no | 38304 | 38304 | 0 | 1824 | 1824 | 0 | yes |
| B1 | 4 | 1 | no | 38220 | 38220 | 0 | 1820 | 1820 | 0 | yes |
| B1 | 5 | 1 | no | — | — | — | — | — | — | NO |
| B1 | 6 | 1 | no | 44037 | 44037 | 0 | 2097 | 2097 | 0 | yes |
| B1 | 7 | 1 | no | 44037 | 44037 | 0 | 2097 | 2097 | 0 | yes |
| B1 | 8 | 1 | no | 44121 | 44121 | 0 | 2101 | 2101 | 0 | yes |
| B1 | 9 | 1 | no | 44163 | 44163 | 0 | 2103 | 2103 | 0 | yes |
| B1 | 10 | 1 | no | 44100 | 44100 | 0 | 2100 | 2100 | 0 | yes |
| B1 | 11 | 1 | no | 44478 | 44478 | 0 | 2118 | 2118 | 0 | yes |
| B1 | 12 | 1 | no | 44163 | 44163 | 0 | 2103 | 2103 | 0 | yes |
| B1 | 13 | 1 | no | 44142 | 44142 | 0 | 2102 | 2102 | 0 | yes |
| B1 | 14 | 1 | no | 44961 | 44961 | 0 | 2141 | 2141 | 0 | yes |
| B1 | 15 | 1 | no | 38262 | 38262 | 0 | 1822 | 1822 | 0 | yes |
| B1 | 16 | 1 | no | 38241 | 38241 | 0 | 1821 | 1821 | 0 | yes |
| B1 | 17 | 1 | no | 44184 | 44184 | 0 | 2104 | 2104 | 0 | yes |
| B1 | 18 | 1 | no | 38241 | 38241 | 0 | 1821 | 1821 | 0 | yes |
| B1 | 19 | 1 | no | 49980 | 49980 | 0 | 2380 | 2380 | 0 | yes |
| B1 | 20 | 1 | no | — | — | — | — | — | — | NO |
| B1 | 21 | 1 | no | — | — | — | — | — | — | NO |
| B1 | 22 | 1 | no | 38304 | 38304 | 0 | 1824 | 1824 | 0 | yes |
| B1 | 23 | 1 | no | 44184 | 44184 | 0 | 2104 | 2104 | 0 | yes |
| B1 | 24 | 1 | no | 44016 | 44016 | 0 | 2096 | 2096 | 0 | yes |
| B3 | 0 | 1 | no | 28055 | 28055 | 0 | 5499 | 5499 | 0 | yes |
| B3 | 1 | 1 | no | 28037 | 28037 | 0 | 5496 | 5496 | 0 | yes |
| B3 | 2 | 1 | no | 28055 | 28055 | 0 | 5499 | 5499 | 0 | yes |
| B3 | 3 | 1 | no | 24319 | 24319 | 0 | 4767 | 4767 | 0 | yes |
| B3 | 4 | 1 | no | 24307 | 24307 | 0 | 4763 | 4763 | 0 | yes |
| B3 | 5 | 1 | no | — | — | — | — | — | — | NO |
| B3 | 6 | 1 | no | 28024 | 28024 | 0 | 5491 | 5491 | 0 | yes |
| B3 | 7 | 1 | no | 28038 | 28038 | 0 | 5493 | 5493 | 0 | yes |
| B3 | 8 | 1 | no | 28040 | 28040 | 0 | 5497 | 5497 | 0 | yes |
| B3 | 9 | 1 | no | 28046 | 28046 | 0 | 5499 | 5499 | 0 | yes |
| B3 | 10 | 1 | no | 28049 | 28049 | 0 | 5497 | 5497 | 0 | yes |
| B3 | 11 | 1 | no | 28007 | 28007 | 0 | 5486 | 5486 | 0 | yes |
| B3 | 12 | 1 | no | 28066 | 28066 | 0 | 5499 | 5499 | 0 | yes |
| B3 | 13 | 1 | no | 28041 | 28041 | 0 | 5497 | 5497 | 0 | yes |
| B3 | 14 | 1 | no | 27888 | 27888 | 0 | 5494 | 5494 | 0 | yes |
| B3 | 15 | 1 | no | 24315 | 24315 | 0 | 4766 | 4766 | 0 | yes |
| B3 | 16 | 1 | no | 24324 | 24324 | 0 | 4766 | 4766 | 0 | yes |
| B3 | 17 | 1 | no | 27987 | 27987 | 0 | 5494 | 5494 | 0 | yes |
| B3 | 18 | 1 | no | 24296 | 24296 | 0 | 4763 | 4763 | 0 | yes |
| B3 | 19 | 1 | no | 31813 | 31813 | 0 | 6232 | 6232 | 0 | yes |
| B3 | 20 | 1 | no | — | — | — | — | — | — | NO |
| B3 | 21 | 1 | no | — | — | — | — | — | — | NO |
| B3 | 22 | 1 | no | 24321 | 24321 | 0 | 4768 | 4768 | 0 | yes |
| B3 | 23 | 1 | no | 28061 | 28061 | 0 | 5501 | 5501 | 0 | yes |
| B3 | 24 | 1 | no | 28035 | 28035 | 0 | 5492 | 5492 | 0 | yes |
*n = 100 (optimisation-phase campaign runs of large_tokamak_nof).*
*How to read: every residual column reads 0, or the run is refused before it reaches any other table here*

*How to read: every residual column reads 0, or the run is refused before it reaches any other table here*

**`achieved accuracy at the accepted optimum — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state audit maximum over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; the finished optimisation-phase runs of large_tokamak_nof in this arm group.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle.  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys.  **audit position**: entry_to_write_output_files.  `entry_to_write_output_files` is the declared position — the state the solve handed over — and `after_run` is the reproduction gate's, where the previous revision measured.  The two are different quantities and share this table only because the position is a column of its own.  **the audit instrument's version is read from the record** (stats.audit_instrument).  Task A61 (insstrain-diagnosis) showed that the largest residual at the accepted point on the pulsed configurations is an artefact of this instrument — the output path permanently changes a model setting the snapshot does not restore, so the audit's sweep is not the loop's map — and task A62 (exit-audit-restore) widens the snapshot under decision D25, which moves every value in these columns.  The argmax is read from the record and is not written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction.  the two rulers' exclusion counts are listed per row and never pooled; a run whose restricted block is null carries no count and reads —.  **n counts runs, not values** (stats.accuracy_population, the same construction the evaluation phase's table uses): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic. Audit position: `entry_to_write_output_files`. n = 100 (optimisation-phase runs of large_tokamak_nof in this arm group). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state audit maximum over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; the finished optimisation-phase runs of large_tokamak_nof in this arm group.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle.  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys.  **audit position**: entry_to_write_output_files.  `entry_to_write_output_files` is the declared position — the state the solve handed over — and `after_run` is the reproduction gate's, where the previous revision measured.  The two are different quantities and share this table only because the position is a column of its own.  **the audit instrument's version is read from the record** (stats.audit_instrument).  Task A61 (insstrain-diagnosis) showed that the largest residual at the accepted point on the pulsed configurations is an artefact of this instrument — the output path permanently changes a model setting the snapshot does not restore, so the audit's sweep is not the loop's map — and task A62 (exit-audit-restore) widens the snapshot under decision D25, which moves every value in these columns.  The argmax is read from the record and is not written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction.  the two rulers' exclusion counts are listed per row and never pooled; a run whose restricted block is null carries no count and reads —.  **n counts runs, not values** (stats.accuracy_population, the same construction the evaluation phase's table uses): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic.*
| arm | ruler | n (runs) | with a restricted statistic | restricted median | restricted max | restricted argmax | components above τ | whole-state median | components excluded | audit position | audit instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | frozen | 22 | 22 | 1.150e-11 | 1.332e-11 | heat_transport.tlvpmw | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.150e-11 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| BR | mixed | 22 | 22 | 1.150e-11 | 1.253e-11 | heat_transport.tlvpmw | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.150e-11 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | frozen | 22 | 22 | 1.150e-11 | 1.332e-11 | heat_transport.tlvpmw | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.150e-11 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | mixed | 22 | 22 | 1.150e-11 | 1.253e-11 | heat_transport.tlvpmw | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.150e-11 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B1 | frozen | 22 | 22 | 0 | 7.257e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.c_pf_cs_coil_flat_top_ma | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B1 | mixed | 22 | 22 | 0 | 6.928e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.c_pf_cs_coil_flat_top_ma | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B3 | frozen | 22 | 22 | 0 | 7.257e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.c_pf_cs_coil_flat_top_ma | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.066e+00 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B3 | mixed | 22 | 22 | 0 | 6.928e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.c_pf_cs_coil_flat_top_ma | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.000e+00 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
*n = 100 (optimisation-phase runs of large_tokamak_nof in this arm group).*
*How to read: read the argmax beside the maximum: a residual above the tolerance whose argmax is the component A61 named is a statement about the audit instrument, not about the arm*

*How to read: read the argmax beside the maximum: a residual above the tolerance whose argmax is the component A61 named is a statement about the audit instrument, not about the arm*

**`the lift closed (check 3) — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: seconds for the residual; the relative column is dimensionless (residual / burn time).  a row is one arm whose runs name the burn-time consistency constraint.  a column is the residual of that constraint at the accepted optima.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; the accepted optima of large_tokamak_nof whose input file names constraint 93.  construction: the model's own extracted burn-time consistency relation, evaluated on the returned state — never read back from an output table; |value|, median = nearest-rank upper-middle.  an arm whose input file does not name the constraint is absent from this table rather than reading 0.  residuals at unconverged exits are not here: they belong beside the failure table and are never pooled with these. n = 100 (optimisation-phase campaign runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: seconds for the residual; the relative column is dimensionless (residual / burn time).  a row is one arm whose runs name the burn-time consistency constraint.  a column is the residual of that constraint at the accepted optima.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; the accepted optima of large_tokamak_nof whose input file names constraint 93.  construction: the model's own extracted burn-time consistency relation, evaluated on the returned state — never read back from an output table; |value|, median = nearest-rank upper-middle.  an arm whose input file does not name the constraint is absent from this table rather than reading 0.  residuals at unconverged exits are not here: they belong beside the failure table and are never pooled with these.*
| arm | n accepted | residual, s (median) | bracket, s | relative (median) | in the equality block |
|---|---|---|---|---|---|
| B1 | 22 | 1.659e-05 | [2.600e-06, 1.600e-03] | 2.304e-09 | True |
| B3 | 22 | 1.659e-05 | [2.600e-06, 1.600e-03] | 2.304e-09 | True |
*n = 100 (optimisation-phase campaign runs of large_tokamak_nof).*
*How to read: an optimiser that owns the burn time must still satisfy the relation the model used to assign it, or it has returned a point that is not on the same manifold*

*How to read: an optimiser that owns the burn time must still satisfy the relation the model used to assign it, or it has returned a point that is not on the same manifold*

**`per-sweep overhead — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: counts: evaluations of a convergence test, components compared summed over them, and sweeps of the model sequence.  a row is one optimisation run.  a column is a counter of one **named** convergence test, or a sweep total.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; the finished optimisation-phase campaign runs of large_tokamak_nof.  construction: stats.predicate_widths and stats.empty_visit_shares, from the driver's own counters — exact and concurrency-invariant.  **the two predicates are never pooled**: an arm stops on exactly one of them and their widths differ by nearly two orders of magnitude, so their sum belongs to neither.  The table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**, and the share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — which over this population is 0 %.  The visit share is larger and is never quoted.  no conclusion rests on a timing: the question is asked in counts alone. n = 88 (finished optimisation-phase campaign runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts: evaluations of a convergence test, components compared summed over them, and sweeps of the model sequence.  a row is one optimisation run.  a column is a counter of one **named** convergence test, or a sweep total.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; the finished optimisation-phase campaign runs of large_tokamak_nof.  construction: stats.predicate_widths and stats.empty_visit_shares, from the driver's own counters — exact and concurrency-invariant.  **the two predicates are never pooled**: an arm stops on exactly one of them and their widths differ by nearly two orders of magnitude, so their sum belongs to neither.  The table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**, and the share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — which over this population is 0 %.  The visit share is larger and is never quoted.  no conclusion rests on a timing: the question is asked in counts alone.*
| arm | seed | stops on | dispatch sweeps | of which solve phase | output-time loop | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | 0 | upstream | 2029 | 2027 | 2 | 0 | 0 | — | — | 1397 | 37719 | 27.0 | 0.00 % |
| BR | 1 | upstream | 2021 | 2019 | 2 | 0 | 0 | — | — | 1389 | 37503 | 27.0 | 0.00 % |
| BR | 2 | upstream | 2279 | 2277 | 2 | 0 | 0 | — | — | 1563 | 42201 | 27.0 | 0.00 % |
| BR | 3 | upstream | 1759 | 1757 | 2 | 0 | 0 | — | — | 1211 | 32697 | 27.0 | 0.00 % |
| BR | 4 | upstream | 1761 | 1759 | 2 | 0 | 0 | — | — | 1213 | 32751 | 27.0 | 0.00 % |
| BR | 6 | upstream | 2036 | 2034 | 2 | 0 | 0 | — | — | 1404 | 37908 | 27.0 | 0.00 % |
| BR | 7 | upstream | 2032 | 2030 | 2 | 0 | 0 | — | — | 1400 | 37800 | 27.0 | 0.00 % |
| BR | 8 | upstream | 2034 | 2032 | 2 | 0 | 0 | — | — | 1402 | 37854 | 27.0 | 0.00 % |
| BR | 9 | upstream | 2026 | 2024 | 2 | 0 | 0 | — | — | 1394 | 37638 | 27.0 | 0.00 % |
| BR | 10 | upstream | 1766 | 1764 | 2 | 0 | 0 | — | — | 1218 | 32886 | 27.0 | 0.00 % |
| BR | 11 | upstream | 2005 | 2003 | 2 | 0 | 0 | — | — | 1373 | 37071 | 27.0 | 0.00 % |
| BR | 12 | upstream | 2029 | 2027 | 2 | 0 | 0 | — | — | 1397 | 37719 | 27.0 | 0.00 % |
| BR | 13 | upstream | 2021 | 2019 | 2 | 0 | 0 | — | — | 1389 | 37503 | 27.0 | 0.00 % |
| BR | 14 | upstream | 2279 | 2277 | 2 | 0 | 0 | — | — | 1563 | 42201 | 27.0 | 0.00 % |
| BR | 15 | upstream | 1758 | 1756 | 2 | 0 | 0 | — | — | 1210 | 32670 | 27.0 | 0.00 % |
| BR | 16 | upstream | 1757 | 1755 | 2 | 0 | 0 | — | — | 1209 | 32643 | 27.0 | 0.00 % |
| BR | 17 | upstream | 2027 | 2025 | 2 | 0 | 0 | — | — | 1395 | 37665 | 27.0 | 0.00 % |
| BR | 18 | upstream | 2027 | 2025 | 2 | 0 | 0 | — | — | 1395 | 37665 | 27.0 | 0.00 % |
| BR | 19 | upstream | 2030 | 2028 | 2 | 0 | 0 | — | — | 1398 | 37746 | 27.0 | 0.00 % |
| BR | 22 | upstream | 1763 | 1761 | 2 | 0 | 0 | — | — | 1215 | 32805 | 27.0 | 0.00 % |
| BR | 23 | upstream | 2032 | 2030 | 2 | 0 | 0 | — | — | 1400 | 37800 | 27.0 | 0.00 % |
| BR | 24 | upstream | 2028 | 2026 | 2 | 0 | 0 | — | — | 1396 | 37692 | 27.0 | 0.00 % |
| B0 | 0 | coupling_state | 2071 | 2069 | 2 | 2069 | 1737960 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 1 | coupling_state | 2073 | 2071 | 2 | 2071 | 1739640 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 2 | coupling_state | 2365 | 2363 | 2 | 2363 | 1984920 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 3 | coupling_state | 1797 | 1795 | 2 | 1795 | 1507800 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 4 | coupling_state | 1792 | 1790 | 2 | 1790 | 1503600 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 6 | coupling_state | 2071 | 2069 | 2 | 2069 | 1737960 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 7 | coupling_state | 2070 | 2068 | 2 | 2068 | 1737120 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 8 | coupling_state | 2070 | 2068 | 2 | 2068 | 1737120 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 9 | coupling_state | 2072 | 2070 | 2 | 2070 | 1738800 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 10 | coupling_state | 1792 | 1790 | 2 | 1790 | 1503600 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 11 | coupling_state | 2125 | 2123 | 2 | 2123 | 1783320 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 12 | coupling_state | 2070 | 2068 | 2 | 2068 | 1737120 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 13 | coupling_state | 2075 | 2073 | 2 | 2073 | 1741320 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 14 | coupling_state | 2395 | 2393 | 2 | 2393 | 2010120 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 15 | coupling_state | 1799 | 1797 | 2 | 1797 | 1509480 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 16 | coupling_state | 1796 | 1794 | 2 | 1794 | 1506960 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 17 | coupling_state | 2072 | 2070 | 2 | 2070 | 1738800 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 18 | coupling_state | 2065 | 2063 | 2 | 2063 | 1732920 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 19 | coupling_state | 2069 | 2067 | 2 | 2067 | 1736280 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 22 | coupling_state | 1800 | 1798 | 2 | 1798 | 1510320 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 23 | coupling_state | 2068 | 2066 | 2 | 2066 | 1735440 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 24 | coupling_state | 2077 | 2075 | 2 | 2075 | 1743000 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 0 | coupling_state | 2102 | 2102 | 0 | 2102 | 1765680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 1 | coupling_state | 2100 | 2100 | 0 | 2100 | 1764000 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 2 | coupling_state | 2102 | 2102 | 0 | 2102 | 1765680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 3 | coupling_state | 1824 | 1824 | 0 | 1824 | 1532160 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 4 | coupling_state | 1820 | 1820 | 0 | 1820 | 1528800 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 6 | coupling_state | 2097 | 2097 | 0 | 2097 | 1761480 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 7 | coupling_state | 2097 | 2097 | 0 | 2097 | 1761480 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 8 | coupling_state | 2101 | 2101 | 0 | 2101 | 1764840 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 9 | coupling_state | 2103 | 2103 | 0 | 2103 | 1766520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 10 | coupling_state | 2100 | 2100 | 0 | 2100 | 1764000 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 11 | coupling_state | 2118 | 2118 | 0 | 2118 | 1779120 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 12 | coupling_state | 2103 | 2103 | 0 | 2103 | 1766520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 13 | coupling_state | 2102 | 2102 | 0 | 2102 | 1765680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 14 | coupling_state | 2141 | 2141 | 0 | 2141 | 1798440 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 15 | coupling_state | 1822 | 1822 | 0 | 1822 | 1530480 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 16 | coupling_state | 1821 | 1821 | 0 | 1821 | 1529640 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 17 | coupling_state | 2104 | 2104 | 0 | 2104 | 1767360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 18 | coupling_state | 1821 | 1821 | 0 | 1821 | 1529640 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 19 | coupling_state | 2380 | 2380 | 0 | 2380 | 1999200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 22 | coupling_state | 1824 | 1824 | 0 | 1824 | 1532160 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 23 | coupling_state | 2104 | 2104 | 0 | 2104 | 1767360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 24 | coupling_state | 2096 | 2096 | 0 | 2096 | 1760640 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B3 | 0 | coupling_state | 5500 | 5499 | 0 | 4839 | 1156926 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 1 | coupling_state | 5497 | 5496 | 0 | 4836 | 1156225 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 2 | coupling_state | 5500 | 5499 | 0 | 4839 | 1156926 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 3 | coupling_state | 4768 | 4767 | 0 | 4195 | 1002938 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 4 | coupling_state | 4764 | 4763 | 0 | 4191 | 1001978 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 6 | coupling_state | 5492 | 5491 | 0 | 4831 | 1154989 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 7 | coupling_state | 5494 | 5493 | 0 | 4833 | 1155468 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 8 | coupling_state | 5498 | 5497 | 0 | 4837 | 1156465 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 9 | coupling_state | 5500 | 5499 | 0 | 4839 | 1156945 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 10 | coupling_state | 5498 | 5497 | 0 | 4837 | 1156446 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 11 | coupling_state | 5487 | 5486 | 0 | 4826 | 1153825 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 12 | coupling_state | 5500 | 5499 | 0 | 4839 | 1156871 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 13 | coupling_state | 5498 | 5497 | 0 | 4837 | 1156447 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 14 | coupling_state | 5495 | 5494 | 0 | 4834 | 1156031 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 15 | coupling_state | 4767 | 4766 | 0 | 4194 | 1002716 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 16 | coupling_state | 4767 | 4766 | 0 | 4194 | 1002697 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 17 | coupling_state | 5495 | 5494 | 0 | 4834 | 1155822 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 18 | coupling_state | 4764 | 4763 | 0 | 4191 | 1002033 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 19 | coupling_state | 6233 | 6232 | 0 | 5484 | 1311098 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 22 | coupling_state | 4769 | 4768 | 0 | 4196 | 1003196 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 23 | coupling_state | 5502 | 5501 | 0 | 4841 | 1157406 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 24 | coupling_state | 5493 | 5492 | 0 | 4832 | 1155228 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
*n = 88 (finished optimisation-phase campaign runs of large_tokamak_nof).*
*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 for that arm, which is why they are kept apart*

*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 for that arm, which is why they are kept apart*

**`failure taxonomy — low_aspect_ratio_DEMO — campaign_optimisation`**

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; every campaign run of low_aspect_ratio_DEMO, every start.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped; stats.crash_detail for the detail.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  a crashed start is counted here and in the failure table, and reaches no cost cell: the cost tables are over the every-arm-converged seed set (plan §3.5). n = 100 (optimisation-phase campaign runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; every campaign run of low_aspect_ratio_DEMO, every start.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped; stats.crash_detail for the detail.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  a crashed start is counted here and in the failure table, and reaches no cost cell: the cost tables are over the every-arm-converged seed set (plan §3.5).*
| arm | scheduled | crashed | ok | unconverged | rows sum | detail (traceback's last line × count) |
|---|---|---|---|---|---|---|
| BR | 25 | 2 | 23 | 0 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×2 |
| B0 | 25 | 2 | 21 | 2 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×2; process.core.solver.module_solve.ModuleSolveFailure: block FLAT did not converge in 20 sweeps at tau=1e-06; max scaled residual inf on current_drive.eta_cd_dimensionless_hcd_primary, 1 components above tau ×2 |
| B1 | 25 | 2 | 20 | 3 | yes | process.core.solver.module_solve.ModuleSolveFailure: block FLAT did not converge in 20 sweeps at tau=1e-06; max scaled residual inf on current_drive.eta_cd_dimensionless_hcd_primary, 1 components above tau ×3; RuntimeError: Failed to converge after 50 iterations, value is nan. ×2 |
| B3 | 25 | 2 | 20 | 3 | yes | process.core.solver.module_solve.ModuleSolveFailure: block M1 did not converge in 20 sweeps at tau=1e-06; max scaled residual inf on current_drive.eta_cd_dimensionless_hcd_primary, 1 components above tau ×3; RuntimeError: Failed to converge after 50 iterations, value is nan. ×2 |
*n = 100 (optimisation-phase campaign runs of low_aspect_ratio_DEMO).*
*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited; the detail says whether one failure mode or several*

*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited; the detail says whether one failure mode or several*

**`the seed set — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: counts of seeds.  a row is this configuration.  a column is the size of the one population every optimisation-phase table on this configuration is over, or a per-arm count of the seeds on which the optimiser was called more than once.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; the arms present here are BR, B0, B1, B3 at seeds 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24.  construction: stats.every_arm_converged — a seed is in the set when every arm present reached an accepted optimum (status ok AND the output file's ifail == 1); stats.retried, which counts attempts[] and never a stored flag.  **this is one arm group of the source.**  The plan's construction assumes what a campaign guarantees — every arm at every seed — and a gate's runs do not: the source is therefore split by which arms have a run at a seed, and each group is a population the construction applies to.  The group is named in this table's title and in every other table of the same group.  the seeds outside the set are not dropped: they are the failure table, published beside this one, so an arm that fails on expensive seeds cannot be flattered by the filter.  a seed on which **no** arm converged is configuration hardness, counted in its own column and not against any arm. n = 25 (distinct seeds run on low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of seeds.  a row is this configuration.  a column is the size of the one population every optimisation-phase table on this configuration is over, or a per-arm count of the seeds on which the optimiser was called more than once.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; the arms present here are BR, B0, B1, B3 at seeds 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24.  construction: stats.every_arm_converged — a seed is in the set when every arm present reached an accepted optimum (status ok AND the output file's ifail == 1); stats.retried, which counts attempts[] and never a stored flag.  **this is one arm group of the source.**  The plan's construction assumes what a campaign guarantees — every arm at every seed — and a gate's runs do not: the source is therefore split by which arms have a run at a seed, and each group is a population the construction applies to.  The group is named in this table's title and in every other table of the same group.  the seeds outside the set are not dropped: they are the failure table, published beside this one, so an arm that fails on expensive seeds cannot be flattered by the filter.  a seed on which **no** arm converged is configuration hardness, counted in its own column and not against any arm.*
| arms | which | seeds offered | n (every arm converged) | seeds in the set | configuration-invalid seeds | retried seeds per arm |
|---|---|---|---|---|---|---|
| 4 | BR · B0 · B1 · B3 | 25 | 11 | 0, 1, 5, 6, 9, 11, 12, 13, 15, 18, 19 | 13 | BR 12 · B0 10 · B1 10 · B3 10 |
*n = 25 (distinct seeds run on low_aspect_ratio_DEMO).*
*How to read: this n is the denominator of every other optimisation-phase table on this configuration*

*How to read: this n is the denominator of every other optimisation-phase table on this configuration*

**`the failure table — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: counts: model executions for the cost columns, optimiser exit codes for ifail.  a row is one seed outside the converged set.  a column is which arm failed there, how it failed, what it cost, and what the other arms cost at the same start.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 14 of 25 seed(s) on low_aspect_ratio_DEMO lie outside the every-arm-converged set.  construction: stats.accepted_optimum for membership; the cost column is node_calls_solve_phase, the same unit the cost table uses.  an arm the gate did not run at a seed reads *not run* rather than *failed*: an absent record and a failed run are different results.  a seed on which every arm failed or was absent is marked configuration-invalid. n = 25 (distinct seeds run on low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts: model executions for the cost columns, optimiser exit codes for ifail.  a row is one seed outside the converged set.  a column is which arm failed there, how it failed, what it cost, and what the other arms cost at the same start.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 14 of 25 seed(s) on low_aspect_ratio_DEMO lie outside the every-arm-converged set.  construction: stats.accepted_optimum for membership; the cost column is node_calls_solve_phase, the same unit the cost table uses.  an arm the gate did not run at a seed reads *not run* rather than *failed*: an absent record and a failed run are different results.  a seed on which every arm failed or was absent is marked configuration-invalid.*
| seed | failed arm(s) | not run | ifail | attempts | failed arm node calls | other arms' node calls | configuration-invalid |
|---|---|---|---|---|---|---|---|
| 2 | BR, B0, B1, B3 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11466, 11571, 11298, 7092 | BR — / B0 — / B1 — / B3 — | yes |
| 3 | BR, B0, B1, B3 | — | None, None, None, None | 1, 1, 1, 1 | None, None, None, None | BR — / B0 — / B1 — / B3 — | yes |
| 4 | BR, B0, B1, B3 | — | 5.0, None, None, None | 4, 1, 1, 1 | 10773, None, None, None | BR — / B0 — / B1 — / B3 — | yes |
| 7 | BR, B0, B1, B3 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11298, 11340, 10983, 7126 | BR — / B0 — / B1 — / B3 — | yes |
| 8 | BR, B0, B1, B3 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11025, 11298, 10983, 7066 | BR — / B0 — / B1 — / B3 — | yes |
| 10 | B1, B3 | — | None, None | 2, 2 | None, None | BR 60816 / B0 58947 / B1 — / B3 — | no |
| 14 | BR, B0, B1, B3 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11130, 11529, 11193, 7190 | BR — / B0 — / B1 — / B3 — | yes |
| 16 | BR, B0, B1, B3 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11319, 11235, 11277, 7146 | BR — / B0 — / B1 — / B3 — | yes |
| 17 | BR, B0, B1, B3 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11340, 11277, 11298, 7208 | BR — / B0 — / B1 — / B3 — | yes |
| 20 | BR, B0, B1, B3 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11214, 11403, 11361, 7186 | BR — / B0 — / B1 — / B3 — | yes |
| 21 | BR, B0, B1, B3 | — | None, None, None, None | 1, 1, 1, 1 | None, None, None, None | BR — / B0 — / B1 — / B3 — | yes |
| 22 | BR, B0, B1, B3 | — | 5.0, None, None, None | 4, 1, 1, 1 | 11130, None, None, None | BR — / B0 — / B1 — / B3 — | yes |
| 23 | BR, B0, B1, B3 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11340, 11319, 11319, 7212 | BR — / B0 — / B1 — / B3 — | yes |
| 24 | BR, B0, B1, B3 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11403, 11445, 11130, 7152 | BR — / B0 — / B1 — / B3 — | yes |
*n = 25 (distinct seeds run on low_aspect_ratio_DEMO).*
*How to read: the converged set is the fairer cost population but can flatter an arm that fails on expensive seeds; this table is what keeps it honest*

*How to read: the converged set is the fairer cost population but can flatter an arm that fails on expensive seeds; this table is what keeps it honest*

**`same optimum (check 1) — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: dimensionless: a relative difference of the normalised objective.  a row is one arm pair over the seed set.  a column is the paired relative objective difference's median and p90, the threshold they are judged against, and the clustering statistics.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 11 seed(s) on which every arm of low_aspect_ratio_DEMO reached an accepted optimum.  construction: stats.relative_objective_difference — |Δ norm_objf| / max(|a|, |b|) per pair, from the hex floats; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); stats.acceptance_threshold = max(F × yardstick, floor) with F = 10 and floor = 1e-06, the yardstick being the BR → B0 spread measured in this same population; stats.clusters at a relative gap of 1e-05.  the yardstick row carries no threshold and no verdict: it *is* the threshold's calibration.  *below resolution* counts pairs further apart than the correctness floor and closer than the cluster gap — distinct optima below cluster resolution, a named category and not a rounding remark.  the retried column is computed from attempts[], never from a stored flag, so a pair containing a retry is visible here as well as in the cost table. n = 11 (seeds on which every arm of low_aspect_ratio_DEMO converged). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless: a relative difference of the normalised objective.  a row is one arm pair over the seed set.  a column is the paired relative objective difference's median and p90, the threshold they are judged against, and the clustering statistics.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 11 seed(s) on which every arm of low_aspect_ratio_DEMO reached an accepted optimum.  construction: stats.relative_objective_difference — |Δ norm_objf| / max(|a|, |b|) per pair, from the hex floats; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); stats.acceptance_threshold = max(F × yardstick, floor) with F = 10 and floor = 1e-06, the yardstick being the BR → B0 spread measured in this same population; stats.clusters at a relative gap of 1e-05.  the yardstick row carries no threshold and no verdict: it *is* the threshold's calibration.  *below resolution* counts pairs further apart than the correctness floor and closer than the cluster gap — distinct optima below cluster resolution, a named category and not a rounding remark.  the retried column is computed from attempts[], never from a stored flag, so a pair containing a retry is visible here as well as in the cost table.*
| pair | n | r median | r p90 | threshold median | threshold p90 | verdict | hops | below resolution | retried seeds in pair |
|---|---|---|---|---|---|---|---|---|---|
| BR → B0 (yardstick) | 11 | 1.982e-14 | 1.976e-13 | — | — | — | 0/11 (0.00) | 0 | 1 |
| B0 → B1 | 11 | 4.101e-07 | 2.148e-06 | 1.000e-06 | 1.000e-06 | FAIL | 1/11 (0.09) | 2 | 1 |
| B0 → B3 | 11 | 4.101e-07 | 2.148e-06 | 1.000e-06 | 1.000e-06 | FAIL | 1/11 (0.09) | 2 | 1 |
*n = 11 (seeds on which every arm of low_aspect_ratio_DEMO converged).*
*How to read: a verdict is read only where a threshold exists; a hop is a seed whose two sides landed in different objective clusters, and the yardstick pair's own hop rate is the comparator*

*How to read: a verdict is read only where a threshold exists; a hop is a seed whose two sides landed in different objective clusters, and the yardstick pair's own hop rate is the comparator*

**`iteration multiplier (check 2) — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: dimensionless ratios of counts.  a row is one arm against the flat control over the seed set.  a column is one of check 2's two iteration constructions, its sum ratio, or the evaluation-count ratio beside them.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 11 seed(s) on which every arm of low_aspect_ratio_DEMO reached an accepted optimum.  construction: stats.iterations_summed_over_attempts (the **declared acceptance statistic**, nearest-rank upper-middle median against 1.05) and stats.iterations_final_attempt (the previous revision's construction, published beside for comparability).  Both are read from attempts[], so a disagreement between them is a disagreement about that list and not about which field was read.  the sum ratio is published beside every median because a median of per-seed ratios and the ratio of the sums can point in opposite directions.  the evaluation-count ratio is beside both: iterations, even summed, miss the lifted arm's extra stencil column and the line-search evaluations that vary at equal iteration count.  *constructions disagree* counts the seeds on which the final attempt's pair and the summed pair are not the same numbers — 0 means no run in this population retried. n = 11 (seeds on which every arm of low_aspect_ratio_DEMO converged). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless ratios of counts.  a row is one arm against the flat control over the seed set.  a column is one of check 2's two iteration constructions, its sum ratio, or the evaluation-count ratio beside them.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 11 seed(s) on which every arm of low_aspect_ratio_DEMO reached an accepted optimum.  construction: stats.iterations_summed_over_attempts (the **declared acceptance statistic**, nearest-rank upper-middle median against 1.05) and stats.iterations_final_attempt (the previous revision's construction, published beside for comparability).  Both are read from attempts[], so a disagreement between them is a disagreement about that list and not about which field was read.  the sum ratio is published beside every median because a median of per-seed ratios and the ratio of the sums can point in opposite directions.  the evaluation-count ratio is beside both: iterations, even summed, miss the lifted arm's extra stencil column and the line-search evaluations that vary at equal iteration count.  *constructions disagree* counts the seeds on which the final attempt's pair and the summed pair are not the same numbers — 0 means no run in this population retried.*
| pair | n | summed median (acceptance) | summed sum ratio | verdict | final-attempt median | final-attempt sum ratio | evaluations median | attempts per seed (base/arm) | constructions disagree |
|---|---|---|---|---|---|---|---|---|---|
| B0 → BR (beside) | 11 | 1.0000 | 1.0000 | beside | 1.0000 | 1.0000 | 1.0352 | 0:1/1, 1:2/2, 5:1/1, 6:1/1, 9:1/1, 11:1/1, 12:1/1, 13:1/1, 15:1/1, 18:1/1, 19:1/1 | 1 |
| B0 → B1 | 11 | 0.8125 | 0.7012 | PASS | 0.8333 | 1.0088 | 0.8046 | 0:1/1, 1:2/1, 5:1/1, 6:1/1, 9:1/1, 11:1/1, 12:1/1, 13:1/1, 15:1/1, 18:1/1, 19:1/1 | 1 |
| B0 → B3 | 11 | 0.8125 | 0.7012 | PASS | 0.8333 | 1.0088 | 2.1169 | 0:1/1, 1:2/1, 5:1/1, 6:1/1, 9:1/1, 11:1/1, 12:1/1, 13:1/1, 15:1/1, 18:1/1, 19:1/1 | 1 |
*n = 11 (seeds on which every arm of low_aspect_ratio_DEMO converged).*
*How to read: read the acceptance column against the summed median; a final-attempt median that differs from it names the retried seeds, which the attempts column lists*

*How to read: read the acceptance column against the summed median; a final-attempt median that differs from it names the retried seeds, which the attempts column lists*

**`cost (check 4) — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: model executions during the solve; ratios dimensionless.  a row is one arm over the seed set.  a column is an absolute per-run mean with its bracket, or one reading of the ratio against the flat control.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 11 seed(s) on which every arm of low_aspect_ratio_DEMO reached an accepted optimum.  construction: stats.with_and_without_retried — solve-phase node calls **summed over attempts[]** per run, so the ratio is over the quantity the attempts decompose (the identity is in the attempt-summation table); pooled = Σ arm / Σ base, median = nearest-rank upper-middle of the per-seed ratios, worse = seeds on which the arm cost more.  **retries are a term, not a footnote**: the ratio is published *with* and *without* the retried seeds because both readings are defensible — a retry the other arm did not need is real cost the architecture avoided at that start, *and* it is a robustness event rather than a per-evaluation cost.  a seed counts as retried when **either** side of the pair retried: the pair is what the ratio is over.  the arrangement-method calls are a column of their own and are never pooled into the node calls.  the output-time and audit sweeps are excluded from this unit symmetrically in every arm. n = 11 (seeds on which every arm of low_aspect_ratio_DEMO converged). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model executions during the solve; ratios dimensionless.  a row is one arm over the seed set.  a column is an absolute per-run mean with its bracket, or one reading of the ratio against the flat control.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 11 seed(s) on which every arm of low_aspect_ratio_DEMO reached an accepted optimum.  construction: stats.with_and_without_retried — solve-phase node calls **summed over attempts[]** per run, so the ratio is over the quantity the attempts decompose (the identity is in the attempt-summation table); pooled = Σ arm / Σ base, median = nearest-rank upper-middle of the per-seed ratios, worse = seeds on which the arm cost more.  **retries are a term, not a footnote**: the ratio is published *with* and *without* the retried seeds because both readings are defensible — a retry the other arm did not need is real cost the architecture avoided at that start, *and* it is a robustness event rather than a per-evaluation cost.  a seed counts as retried when **either** side of the pair retried: the pair is what the ratio is over.  the arrangement-method calls are a column of their own and are never pooled into the node calls.  the output-time and audit sweeps are excluded from this unit symmetrically in every arm.*
| arm | n | node calls / run | bracket | arrangement·method calls | with retried: pooled | with retried: median | worse | retried seeds | without retried: pooled | without retried: median | n without |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | 11 | 169943.5 | [60921, 669207] | 0 | 1.0300 | 1.0352 | 11 | 1 | 1.0351 | 1.0352 | 10 |
| B0 | 11 | 164997.0 | [58947, 655473] | 0 | 1.0000 | 1.0000 | 0 | 1 | 1.0000 | 1.0000 | 10 |
| B1 | 11 | 114154.1 | [53214, 360591] | 0 | 0.6919 | 0.8049 | 3 | 1 | 1.0129 | 0.8257 | 10 |
| B3 | 11 | 74312.4 | [34628, 234616] | 157504 | 0.4504 | 0.5237 | 2 | 1 | 0.6594 | 0.5371 | 10 |
*n = 11 (seeds on which every arm of low_aspect_ratio_DEMO converged).*
*How to read: where *retried* is 0 the with- and without- columns are the same number, and the pair of columns is the statement that nothing in this population depended on a retry*

*How to read: where *retried* is 0 the with- and without- columns are the same number, and the pair of columns is the statement that nothing in this population depended on a retry*

**`the attempt summation identity — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: counts: model executions and sweeps of the model sequence.  a row is one optimisation run.  a column is the per-attempt costs, the run's solve-phase total they decompose, and the residual between them.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 100 optimisation run(s) of low_aspect_ratio_DEMO, of which 100 carry a per-attempt cost the identity can be checked on.  construction: stats.attempt_summation — Σ over attempts[] against node_calls_solve_phase and dispatch_sweeps_solve_phase.  this identity is why the with- and without-retried-seeds cost ratios may be published: they are computed over quantities that visibly decompose the published total, and a residual that is not 0 would make them ratios of something else.  the record contract already refuses a record whose parts do not add up; this table is the same identity stated as a number a reader can see. n = 100 (optimisation-phase campaign runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts: model executions and sweeps of the model sequence.  a row is one optimisation run.  a column is the per-attempt costs, the run's solve-phase total they decompose, and the residual between them.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 100 optimisation run(s) of low_aspect_ratio_DEMO, of which 100 carry a per-attempt cost the identity can be checked on.  construction: stats.attempt_summation — Σ over attempts[] against node_calls_solve_phase and dispatch_sweeps_solve_phase.  this identity is why the with- and without-retried-seeds cost ratios may be published: they are computed over quantities that visibly decompose the published total, and a residual that is not 0 would make them ratios of something else.  the record contract already refuses a record whose parts do not add up; this table is the same identity stated as a number a reader can see.*
| arm | seed | attempts | retried | node calls per attempt | = solve-phase total | residual | sweeps per attempt | = solve-phase total | residual | decomposes |
|---|---|---|---|---|---|---|---|---|---|---|
| BR | 0 | 1 | no | 89964 | 89964 | 0 | 4284 | 4284 | 0 | yes |
| BR | 1 | 2 | yes | 579369 + 89838 | 669207 | 0 | 27589 + 4278 | 31867 | 0 | yes |
| BR | 2 | 4 | yes | 2940 + 2877 + 2772 + 2877 | 11466 | 0 | 140 + 137 + 132 + 137 | 546 | 0 | yes |
| BR | 3 | 1 | no | — | — | — | — | — | — | NO |
| BR | 4 | 4 | yes | 2751 + 2877 + 2457 + 2688 | 10773 | 0 | 131 + 137 + 117 + 128 | 513 | 0 | yes |
| BR | 5 | 1 | no | 60921 | 60921 | 0 | 2901 | 2901 | 0 | yes |
| BR | 6 | 1 | no | 194313 | 194313 | 0 | 9253 | 9253 | 0 | yes |
| BR | 7 | 4 | yes | 2940 + 2877 + 2604 + 2877 | 11298 | 0 | 140 + 137 + 124 + 137 | 538 | 0 | yes |
| BR | 8 | 4 | yes | 2856 + 2877 + 2499 + 2793 | 11025 | 0 | 136 + 137 + 119 + 133 | 525 | 0 | yes |
| BR | 9 | 1 | no | 72513 | 72513 | 0 | 3453 | 3453 | 0 | yes |
| BR | 10 | 1 | no | 60816 | 60816 | 0 | 2896 | 2896 | 0 | yes |
| BR | 11 | 1 | no | 60984 | 60984 | 0 | 2904 | 2904 | 0 | yes |
| BR | 12 | 1 | no | 89985 | 89985 | 0 | 4285 | 4285 | 0 | yes |
| BR | 13 | 1 | no | 113106 | 113106 | 0 | 5386 | 5386 | 0 | yes |
| BR | 14 | 4 | yes | 2898 + 2877 + 2520 + 2835 | 11130 | 0 | 138 + 137 + 120 + 135 | 530 | 0 | yes |
| BR | 15 | 1 | no | 367773 | 367773 | 0 | 17513 | 17513 | 0 | yes |
| BR | 16 | 4 | yes | 2940 + 2877 + 2625 + 2877 | 11319 | 0 | 140 + 137 + 125 + 137 | 539 | 0 | yes |
| BR | 17 | 4 | yes | 2940 + 2877 + 2646 + 2877 | 11340 | 0 | 140 + 137 + 126 + 137 | 540 | 0 | yes |
| BR | 18 | 1 | no | 84042 | 84042 | 0 | 4002 | 4002 | 0 | yes |
| BR | 19 | 1 | no | 66570 | 66570 | 0 | 3170 | 3170 | 0 | yes |
| BR | 20 | 4 | yes | 2940 + 2877 + 2520 + 2877 | 11214 | 0 | 140 + 137 + 120 + 137 | 534 | 0 | yes |
| BR | 21 | 1 | no | — | — | — | — | — | — | NO |
| BR | 22 | 4 | yes | 2898 + 2877 + 2520 + 2835 | 11130 | 0 | 138 + 137 + 120 + 135 | 530 | 0 | yes |
| BR | 23 | 4 | yes | 2940 + 2877 + 2646 + 2877 | 11340 | 0 | 140 + 137 + 126 + 137 | 540 | 0 | yes |
| BR | 24 | 4 | yes | 2940 + 2877 + 2709 + 2877 | 11403 | 0 | 140 + 137 + 129 + 137 | 543 | 0 | yes |
| B0 | 0 | 1 | no | 86877 | 86877 | 0 | 4137 | 4137 | 0 | yes |
| B0 | 1 | 2 | yes | 558999 + 96474 | 655473 | 0 | 26619 + 4594 | 31213 | 0 | yes |
| B0 | 2 | 4 | yes | 2940 + 3087 + 2688 + 2856 | 11571 | 0 | 140 + 147 + 128 + 136 | 551 | 0 | yes |
| B0 | 3 | 1 | no | — | — | — | — | — | — | NO |
| B0 | 4 | 1 | no | — | — | — | — | — | — | NO |
| B0 | 5 | 1 | no | 58947 | 58947 | 0 | 2807 | 2807 | 0 | yes |
| B0 | 6 | 1 | no | 187572 | 187572 | 0 | 8932 | 8932 | 0 | yes |
| B0 | 7 | 4 | yes | 2877 + 3003 + 2667 + 2793 | 11340 | 0 | 137 + 143 + 127 + 133 | 540 | 0 | yes |
| B0 | 8 | 4 | yes | 2877 + 3003 + 2625 + 2793 | 11298 | 0 | 137 + 143 + 125 + 133 | 538 | 0 | yes |
| B0 | 9 | 1 | no | 70077 | 70077 | 0 | 3337 | 3337 | 0 | yes |
| B0 | 10 | 1 | no | 58947 | 58947 | 0 | 2807 | 2807 | 0 | yes |
| B0 | 11 | 1 | no | 58947 | 58947 | 0 | 2807 | 2807 | 0 | yes |
| B0 | 12 | 1 | no | 86919 | 86919 | 0 | 4139 | 4139 | 0 | yes |
| B0 | 13 | 1 | no | 109221 | 109221 | 0 | 5201 | 5201 | 0 | yes |
| B0 | 14 | 4 | yes | 2919 + 3087 + 2688 + 2835 | 11529 | 0 | 139 + 147 + 128 + 135 | 549 | 0 | yes |
| B0 | 15 | 1 | no | 355278 | 355278 | 0 | 16918 | 16918 | 0 | yes |
| B0 | 16 | 4 | yes | 2877 + 2982 + 2583 + 2793 | 11235 | 0 | 137 + 142 + 123 + 133 | 535 | 0 | yes |
| B0 | 17 | 4 | yes | 2877 + 2982 + 2625 + 2793 | 11277 | 0 | 137 + 142 + 125 + 133 | 537 | 0 | yes |
| B0 | 18 | 1 | no | 81186 | 81186 | 0 | 3866 | 3866 | 0 | yes |
| B0 | 19 | 1 | no | 64470 | 64470 | 0 | 3070 | 3070 | 0 | yes |
| B0 | 20 | 4 | yes | 2898 + 3024 + 2667 + 2814 | 11403 | 0 | 138 + 144 + 127 + 134 | 543 | 0 | yes |
| B0 | 21 | 1 | no | — | — | — | — | — | — | NO |
| B0 | 22 | 1 | no | — | — | — | — | — | — | NO |
| B0 | 23 | 4 | yes | 2877 + 3024 + 2625 + 2793 | 11319 | 0 | 137 + 144 + 125 + 133 | 539 | 0 | yes |
| B0 | 24 | 4 | yes | 2898 + 3045 + 2688 + 2814 | 11445 | 0 | 138 + 145 + 128 + 134 | 545 | 0 | yes |
| B1 | 0 | 1 | no | 69930 | 69930 | 0 | 3330 | 3330 | 0 | yes |
| B1 | 1 | 1 | no | 81228 | 81228 | 0 | 3868 | 3868 | 0 | yes |
| B1 | 2 | 4 | yes | 2856 + 2982 + 2688 + 2772 | 11298 | 0 | 136 + 142 + 128 + 132 | 538 | 0 | yes |
| B1 | 3 | 1 | no | — | — | — | — | — | — | NO |
| B1 | 4 | 1 | no | — | — | — | — | — | — | NO |
| B1 | 5 | 1 | no | 198240 | 198240 | 0 | 9440 | 9440 | 0 | yes |
| B1 | 6 | 1 | no | 114555 | 114555 | 0 | 5455 | 5455 | 0 | yes |
| B1 | 7 | 4 | yes | 2793 + 2835 + 2646 + 2709 | 10983 | 0 | 133 + 135 + 126 + 129 | 523 | 0 | yes |
| B1 | 8 | 4 | yes | 2793 + 2835 + 2646 + 2709 | 10983 | 0 | 133 + 135 + 126 + 129 | 523 | 0 | yes |
| B1 | 9 | 1 | no | 75600 | 75600 | 0 | 3600 | 3600 | 0 | yes |
| B1 | 10 | 2 | yes | — | — | — | — | — | — | NO |
| B1 | 11 | 1 | no | 360591 | 360591 | 0 | 17171 | 17171 | 0 | yes |
| B1 | 12 | 1 | no | 53214 | 53214 | 0 | 2534 | 2534 | 0 | yes |
| B1 | 13 | 1 | no | 97881 | 97881 | 0 | 4661 | 4661 | 0 | yes |
| B1 | 14 | 4 | yes | 2856 + 2898 + 2667 + 2772 | 11193 | 0 | 136 + 138 + 127 + 132 | 533 | 0 | yes |
| B1 | 15 | 1 | no | 86604 | 86604 | 0 | 4124 | 4124 | 0 | yes |
| B1 | 16 | 4 | yes | 2856 + 3024 + 2625 + 2772 | 11277 | 0 | 136 + 144 + 125 + 132 | 537 | 0 | yes |
| B1 | 17 | 4 | yes | 2856 + 3003 + 2667 + 2772 | 11298 | 0 | 136 + 143 + 127 + 132 | 538 | 0 | yes |
| B1 | 18 | 1 | no | 64617 | 64617 | 0 | 3077 | 3077 | 0 | yes |
| B1 | 19 | 1 | no | 53235 | 53235 | 0 | 2535 | 2535 | 0 | yes |
| B1 | 20 | 4 | yes | 2856 + 3003 + 2730 + 2772 | 11361 | 0 | 136 + 143 + 130 + 132 | 541 | 0 | yes |
| B1 | 21 | 1 | no | — | — | — | — | — | — | NO |
| B1 | 22 | 1 | no | — | — | — | — | — | — | NO |
| B1 | 23 | 4 | yes | 2856 + 3024 + 2667 + 2772 | 11319 | 0 | 136 + 144 + 127 + 132 | 539 | 0 | yes |
| B1 | 24 | 4 | yes | 2835 + 2877 + 2667 + 2751 | 11130 | 0 | 135 + 137 + 127 + 131 | 530 | 0 | yes |
| B3 | 0 | 1 | no | 45496 | 45496 | 0 | 8762 | 8762 | 0 | yes |
| B3 | 1 | 1 | no | 52834 | 52834 | 0 | 10182 | 10182 | 0 | yes |
| B3 | 2 | 4 | yes | 1792 + 1896 + 1654 + 1750 | 7092 | 0 | 353 + 363 + 332 + 344 | 1392 | 0 | yes |
| B3 | 3 | 1 | no | — | — | — | — | — | — | NO |
| B3 | 4 | 1 | no | — | — | — | — | — | — | NO |
| B3 | 5 | 1 | no | 129215 | 129215 | 0 | 24883 | 24883 | 0 | yes |
| B3 | 6 | 1 | no | 74687 | 74687 | 0 | 14382 | 14382 | 0 | yes |
| B3 | 7 | 4 | yes | 1819 + 1876 + 1654 + 1777 | 7126 | 0 | 353 + 357 + 330 + 344 | 1384 | 0 | yes |
| B3 | 8 | 4 | yes | 1795 + 1876 + 1642 + 1753 | 7066 | 0 | 351 + 357 + 329 + 342 | 1379 | 0 | yes |
| B3 | 9 | 1 | no | 49194 | 49194 | 0 | 9480 | 9480 | 0 | yes |
| B3 | 10 | 2 | yes | — | — | — | — | — | — | NO |
| B3 | 11 | 1 | no | 234616 | 234616 | 0 | 45221 | 45221 | 0 | yes |
| B3 | 12 | 1 | no | 34646 | 34646 | 0 | 6675 | 6675 | 0 | yes |
| B3 | 13 | 1 | no | 63761 | 63761 | 0 | 12282 | 12282 | 0 | yes |
| B3 | 14 | 4 | yes | 1837 + 1895 + 1663 + 1795 | 7190 | 0 | 356 + 360 + 332 + 347 | 1395 | 0 | yes |
| B3 | 15 | 1 | no | 56439 | 56439 | 0 | 10868 | 10868 | 0 | yes |
| B3 | 16 | 4 | yes | 1816 + 1912 + 1644 + 1774 | 7146 | 0 | 355 + 366 + 329 + 346 | 1396 | 0 | yes |
| B3 | 17 | 4 | yes | 1840 + 1908 + 1662 + 1798 | 7208 | 0 | 357 + 364 + 332 + 348 | 1401 | 0 | yes |
| B3 | 18 | 1 | no | 41920 | 41920 | 0 | 8087 | 8087 | 0 | yes |
| B3 | 19 | 1 | no | 34628 | 34628 | 0 | 6671 | 6671 | 0 | yes |
| B3 | 20 | 4 | yes | 1828 + 1900 + 1672 + 1786 | 7186 | 0 | 356 + 365 + 336 + 347 | 1404 | 0 | yes |
| B3 | 21 | 1 | no | — | — | — | — | — | — | NO |
| B3 | 22 | 1 | no | — | — | — | — | — | — | NO |
| B3 | 23 | 4 | yes | 1840 + 1912 + 1662 + 1798 | 7212 | 0 | 357 + 366 + 332 + 348 | 1403 | 0 | yes |
| B3 | 24 | 4 | yes | 1825 + 1881 + 1663 + 1783 | 7152 | 0 | 355 + 358 + 332 + 346 | 1391 | 0 | yes |
*n = 100 (optimisation-phase campaign runs of low_aspect_ratio_DEMO).*
*How to read: every residual column reads 0, or the run is refused before it reaches any other table here*

*How to read: every residual column reads 0, or the run is refused before it reaches any other table here*

**`achieved accuracy at the accepted optimum — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state audit maximum over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; the finished optimisation-phase runs of low_aspect_ratio_DEMO in this arm group.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle.  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys.  **audit position**: entry_to_write_output_files.  `entry_to_write_output_files` is the declared position — the state the solve handed over — and `after_run` is the reproduction gate's, where the previous revision measured.  The two are different quantities and share this table only because the position is a column of its own.  **the audit instrument's version is read from the record** (stats.audit_instrument).  Task A61 (insstrain-diagnosis) showed that the largest residual at the accepted point on the pulsed configurations is an artefact of this instrument — the output path permanently changes a model setting the snapshot does not restore, so the audit's sweep is not the loop's map — and task A62 (exit-audit-restore) widens the snapshot under decision D25, which moves every value in these columns.  The argmax is read from the record and is not written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction.  the two rulers' exclusion counts are listed per row and never pooled; a run whose restricted block is null carries no count and reads —.  **n counts runs, not values** (stats.accuracy_population, the same construction the evaluation phase's table uses): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic. Audit position: `entry_to_write_output_files`. n = 100 (optimisation-phase runs of low_aspect_ratio_DEMO in this arm group). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state audit maximum over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; the finished optimisation-phase runs of low_aspect_ratio_DEMO in this arm group.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle.  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys.  **audit position**: entry_to_write_output_files.  `entry_to_write_output_files` is the declared position — the state the solve handed over — and `after_run` is the reproduction gate's, where the previous revision measured.  The two are different quantities and share this table only because the position is a column of its own.  **the audit instrument's version is read from the record** (stats.audit_instrument).  Task A61 (insstrain-diagnosis) showed that the largest residual at the accepted point on the pulsed configurations is an artefact of this instrument — the output path permanently changes a model setting the snapshot does not restore, so the audit's sweep is not the loop's map — and task A62 (exit-audit-restore) widens the snapshot under decision D25, which moves every value in these columns.  The argmax is read from the record and is not written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction.  the two rulers' exclusion counts are listed per row and never pooled; a run whose restricted block is null carries no count and reads —.  **n counts runs, not values** (stats.accuracy_population, the same construction the evaluation phase's table uses): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic.*
| arm | ruler | n (runs) | with a restricted statistic | restricted median | restricted max | restricted argmax | components above τ | whole-state median | components excluded | audit position | audit instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | frozen | 23 | 23 | 0 | inf | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.eta_cd_dimensionless_hcd_primary, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| BR | mixed | 23 | 23 | 0 | inf | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.eta_cd_dimensionless_hcd_primary, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | frozen | 21 | 21 | 0 | 5.315e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | mixed | 21 | 21 | 0 | 3.995e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B1 | frozen | 20 | 20 | 0 | 5.315e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B1 | mixed | 20 | 20 | 0 | 4.365e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B3 | frozen | 20 | 20 | 0 | 5.315e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.007e+00 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B3 | mixed | 20 | 20 | 0 | 3.995e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.000e+00 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
*n = 100 (optimisation-phase runs of low_aspect_ratio_DEMO in this arm group).*
*How to read: read the argmax beside the maximum: a residual above the tolerance whose argmax is the component A61 named is a statement about the audit instrument, not about the arm*

*How to read: read the argmax beside the maximum: a residual above the tolerance whose argmax is the component A61 named is a statement about the audit instrument, not about the arm*

**`the lift closed (check 3) — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: seconds for the residual; the relative column is dimensionless (residual / burn time).  a row is one arm whose runs name the burn-time consistency constraint.  a column is the residual of that constraint at the accepted optima.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; the accepted optima of low_aspect_ratio_DEMO whose input file names constraint 93.  construction: the model's own extracted burn-time consistency relation, evaluated on the returned state — never read back from an output table; |value|, median = nearest-rank upper-middle.  an arm whose input file does not name the constraint is absent from this table rather than reading 0.  residuals at unconverged exits are not here: they belong beside the failure table and are never pooled with these. n = 100 (optimisation-phase campaign runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: seconds for the residual; the relative column is dimensionless (residual / burn time).  a row is one arm whose runs name the burn-time consistency constraint.  a column is the residual of that constraint at the accepted optima.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; the accepted optima of low_aspect_ratio_DEMO whose input file names constraint 93.  construction: the model's own extracted burn-time consistency relation, evaluated on the returned state — never read back from an output table; |value|, median = nearest-rank upper-middle.  an arm whose input file does not name the constraint is absent from this table rather than reading 0.  residuals at unconverged exits are not here: they belong beside the failure table and are never pooled with these.*
| arm | n accepted | residual, s (median) | bracket, s | relative (median) | in the equality block |
|---|---|---|---|---|---|
| B1 | 11 | 5.480e-06 | [1.692e-07, 4.756e-05] | 6.744e-10 | True |
| B3 | 11 | 5.480e-06 | [1.692e-07, 4.756e-05] | 6.744e-10 | True |
*n = 100 (optimisation-phase campaign runs of low_aspect_ratio_DEMO).*
*How to read: an optimiser that owns the burn time must still satisfy the relation the model used to assign it, or it has returned a point that is not on the same manifold*

*How to read: an optimiser that owns the burn time must still satisfy the relation the model used to assign it, or it has returned a point that is not on the same manifold*

**`per-sweep overhead — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: counts: evaluations of a convergence test, components compared summed over them, and sweeps of the model sequence.  a row is one optimisation run.  a column is a counter of one **named** convergence test, or a sweep total.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; the finished optimisation-phase campaign runs of low_aspect_ratio_DEMO.  construction: stats.predicate_widths and stats.empty_visit_shares, from the driver's own counters — exact and concurrency-invariant.  **the two predicates are never pooled**: an arm stops on exactly one of them and their widths differ by nearly two orders of magnitude, so their sum belongs to neither.  The table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**, and the share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — which over this population is 0 %.  The visit share is larger and is never quoted.  no conclusion rests on a timing: the question is asked in counts alone. n = 84 (finished optimisation-phase campaign runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts: evaluations of a convergence test, components compared summed over them, and sweeps of the model sequence.  a row is one optimisation run.  a column is a counter of one **named** convergence test, or a sweep total.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; the finished optimisation-phase campaign runs of low_aspect_ratio_DEMO.  construction: stats.predicate_widths and stats.empty_visit_shares, from the driver's own counters — exact and concurrency-invariant.  **the two predicates are never pooled**: an arm stops on exactly one of them and their widths differ by nearly two orders of magnitude, so their sum belongs to neither.  The table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**, and the share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — which over this population is 0 %.  The visit share is larger and is never quoted.  no conclusion rests on a timing: the question is asked in counts alone.*
| arm | seed | stops on | dispatch sweeps | of which solve phase | output-time loop | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | 0 | upstream | 4286 | 4284 | 2 | 0 | 0 | — | — | 3044 | 68069 | 22.4 | 0.00 % |
| BR | 1 | upstream | 31869 | 31867 | 2 | 0 | 0 | — | — | 22627 | 499852 | 22.1 | 0.00 % |
| BR | 2 | upstream | 548 | 546 | 2 | 0 | 0 | — | — | 386 | 8311 | 21.5 | 0.00 % |
| BR | 4 | upstream | 515 | 513 | 2 | 0 | 0 | — | — | 353 | 7703 | 21.8 | 0.00 % |
| BR | 5 | upstream | 2903 | 2901 | 2 | 0 | 0 | — | — | 2061 | 45911 | 22.3 | 0.00 % |
| BR | 6 | upstream | 9255 | 9253 | 2 | 0 | 0 | — | — | 6573 | 146973 | 22.4 | 0.00 % |
| BR | 7 | upstream | 540 | 538 | 2 | 0 | 0 | — | — | 378 | 8353 | 22.1 | 0.00 % |
| BR | 8 | upstream | 527 | 525 | 2 | 0 | 0 | — | — | 365 | 8015 | 22.0 | 0.00 % |
| BR | 9 | upstream | 3455 | 3453 | 2 | 0 | 0 | — | — | 2453 | 54753 | 22.3 | 0.00 % |
| BR | 10 | upstream | 2898 | 2896 | 2 | 0 | 0 | — | — | 2056 | 45856 | 22.3 | 0.00 % |
| BR | 11 | upstream | 2906 | 2904 | 2 | 0 | 0 | — | — | 2064 | 45939 | 22.3 | 0.00 % |
| BR | 12 | upstream | 4287 | 4285 | 2 | 0 | 0 | — | — | 3045 | 68020 | 22.3 | 0.00 % |
| BR | 13 | upstream | 5388 | 5386 | 2 | 0 | 0 | — | — | 3826 | 85501 | 22.3 | 0.00 % |
| BR | 14 | upstream | 532 | 530 | 2 | 0 | 0 | — | — | 370 | 8095 | 21.9 | 0.00 % |
| BR | 15 | upstream | 17515 | 17513 | 2 | 0 | 0 | — | — | 12433 | 278158 | 22.4 | 0.00 % |
| BR | 16 | upstream | 541 | 539 | 2 | 0 | 0 | — | — | 379 | 8379 | 22.1 | 0.00 % |
| BR | 17 | upstream | 542 | 540 | 2 | 0 | 0 | — | — | 380 | 8405 | 22.1 | 0.00 % |
| BR | 18 | upstream | 4004 | 4002 | 2 | 0 | 0 | — | — | 2842 | 63492 | 22.3 | 0.00 % |
| BR | 19 | upstream | 3172 | 3170 | 2 | 0 | 0 | — | — | 2250 | 50250 | 22.3 | 0.00 % |
| BR | 20 | upstream | 536 | 534 | 2 | 0 | 0 | — | — | 374 | 8099 | 21.7 | 0.00 % |
| BR | 22 | upstream | 532 | 530 | 2 | 0 | 0 | — | — | 370 | 8145 | 22.0 | 0.00 % |
| BR | 23 | upstream | 542 | 540 | 2 | 0 | 0 | — | — | 380 | 8405 | 22.1 | 0.00 % |
| BR | 24 | upstream | 545 | 543 | 2 | 0 | 0 | — | — | 383 | 8483 | 22.1 | 0.00 % |
| B0 | 0 | coupling_state | 4139 | 4137 | 2 | 4137 | 3499902 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 1 | coupling_state | 31215 | 31213 | 2 | 31213 | 26406198 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 2 | coupling_state | 553 | 551 | 2 | 551 | 466146 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 5 | coupling_state | 2809 | 2807 | 2 | 2807 | 2374722 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 6 | coupling_state | 8934 | 8932 | 2 | 8932 | 7556472 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 7 | coupling_state | 542 | 540 | 2 | 540 | 456840 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 8 | coupling_state | 540 | 538 | 2 | 538 | 455148 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 9 | coupling_state | 3339 | 3337 | 2 | 3337 | 2823102 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 10 | coupling_state | 2809 | 2807 | 2 | 2807 | 2374722 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 11 | coupling_state | 2809 | 2807 | 2 | 2807 | 2374722 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 12 | coupling_state | 4141 | 4139 | 2 | 4139 | 3501594 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 13 | coupling_state | 5203 | 5201 | 2 | 5201 | 4400046 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 14 | coupling_state | 551 | 549 | 2 | 549 | 464454 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 15 | coupling_state | 16920 | 16918 | 2 | 16918 | 14312628 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 16 | coupling_state | 537 | 535 | 2 | 535 | 452610 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 17 | coupling_state | 539 | 537 | 2 | 537 | 454302 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 18 | coupling_state | 3868 | 3866 | 2 | 3866 | 3270636 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 19 | coupling_state | 3072 | 3070 | 2 | 3070 | 2597220 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 20 | coupling_state | 545 | 543 | 2 | 543 | 459378 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 23 | coupling_state | 541 | 539 | 2 | 539 | 455994 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 24 | coupling_state | 547 | 545 | 2 | 545 | 461070 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 0 | coupling_state | 3330 | 3330 | 0 | 3330 | 2817180 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 1 | coupling_state | 3868 | 3868 | 0 | 3868 | 3272328 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 2 | coupling_state | 538 | 538 | 0 | 538 | 455148 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 5 | coupling_state | 9440 | 9440 | 0 | 9440 | 7986240 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 6 | coupling_state | 5455 | 5455 | 0 | 5455 | 4614930 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 7 | coupling_state | 523 | 523 | 0 | 523 | 442458 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 8 | coupling_state | 523 | 523 | 0 | 523 | 442458 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 9 | coupling_state | 3600 | 3600 | 0 | 3600 | 3045600 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 11 | coupling_state | 17171 | 17171 | 0 | 17171 | 14526666 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 12 | coupling_state | 2534 | 2534 | 0 | 2534 | 2143764 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 13 | coupling_state | 4661 | 4661 | 0 | 4661 | 3943206 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 14 | coupling_state | 533 | 533 | 0 | 533 | 450918 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 15 | coupling_state | 4124 | 4124 | 0 | 4124 | 3488904 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 16 | coupling_state | 537 | 537 | 0 | 537 | 454302 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 17 | coupling_state | 538 | 538 | 0 | 538 | 455148 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 18 | coupling_state | 3077 | 3077 | 0 | 3077 | 2603142 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 19 | coupling_state | 2535 | 2535 | 0 | 2535 | 2144610 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 20 | coupling_state | 541 | 541 | 0 | 541 | 457686 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 23 | coupling_state | 539 | 539 | 0 | 539 | 455994 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 24 | coupling_state | 530 | 530 | 0 | 530 | 448380 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B3 | 0 | coupling_state | 8763 | 8762 | 0 | 7712 | 1855182 | 240.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 1 | coupling_state | 10183 | 10182 | 0 | 8964 | 2156500 | 240.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 2 | coupling_state | 1393 | 1392 | 0 | 1224 | 294788 | 240.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 5 | coupling_state | 24884 | 24883 | 0 | 21901 | 5268614 | 240.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 6 | coupling_state | 14383 | 14382 | 0 | 12660 | 3045529 | 240.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 7 | coupling_state | 1385 | 1384 | 0 | 1216 | 292750 | 240.7 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 8 | coupling_state | 1380 | 1379 | 0 | 1211 | 291645 | 240.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 9 | coupling_state | 9481 | 9480 | 0 | 8346 | 2007830 | 240.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 11 | coupling_state | 45222 | 45221 | 0 | 39803 | 9575641 | 240.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 12 | coupling_state | 6676 | 6675 | 0 | 5877 | 1413837 | 240.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 13 | coupling_state | 12283 | 12282 | 0 | 10812 | 2601007 | 240.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 14 | coupling_state | 1396 | 1395 | 0 | 1227 | 295305 | 240.7 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 15 | coupling_state | 10869 | 10868 | 0 | 9566 | 2301183 | 240.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 16 | coupling_state | 1397 | 1396 | 0 | 1228 | 295694 | 240.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 17 | coupling_state | 1402 | 1401 | 0 | 1233 | 296769 | 240.7 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 18 | coupling_state | 8088 | 8087 | 0 | 7121 | 1713243 | 240.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 19 | coupling_state | 6672 | 6671 | 0 | 5873 | 1412839 | 240.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 20 | coupling_state | 1405 | 1404 | 0 | 1236 | 297630 | 240.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 23 | coupling_state | 1404 | 1403 | 0 | 1235 | 297287 | 240.7 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B3 | 24 | coupling_state | 1392 | 1391 | 0 | 1223 | 294383 | 240.7 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
*n = 84 (finished optimisation-phase campaign runs of low_aspect_ratio_DEMO).*
*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 for that arm, which is why they are kept apart*

*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 for that arm, which is why they are kept apart*

**`failure taxonomy — st_regression — campaign_optimisation`**

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; every campaign run of st_regression, every start.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped; stats.crash_detail for the detail.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  a crashed start is counted here and in the failure table, and reaches no cost cell: the cost tables are over the every-arm-converged seed set (plan §3.5). n = 75 (optimisation-phase campaign runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  a row is one arm on this configuration.  a column is one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; every campaign run of st_regression, every start.  construction: stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped; stats.crash_detail for the detail.  the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.  an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  a crashed start is counted here and in the failure table, and reaches no cost cell: the cost tables are over the every-arm-converged seed set (plan §3.5).*
| arm | scheduled | ok | rows sum | detail (traceback's last line × count) |
|---|---|---|---|---|
| BR | 25 | 25 | yes | — |
| B0 | 25 | 25 | yes | — |
| B3 | 25 | 25 | yes | — |
*n = 75 (optimisation-phase campaign runs of st_regression).*
*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited; the detail says whether one failure mode or several*

*How to read: a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited; the detail says whether one failure mode or several*

**`the seed set — st_regression — campaign_optimisation · BR·B0·B3`**

*Caption: units: counts of seeds.  a row is this configuration.  a column is the size of the one population every optimisation-phase table on this configuration is over, or a per-arm count of the seeds on which the optimiser was called more than once.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; the arms present here are BR, B0, B3 at seeds 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24.  construction: stats.every_arm_converged — a seed is in the set when every arm present reached an accepted optimum (status ok AND the output file's ifail == 1); stats.retried, which counts attempts[] and never a stored flag.  **this is one arm group of the source.**  The plan's construction assumes what a campaign guarantees — every arm at every seed — and a gate's runs do not: the source is therefore split by which arms have a run at a seed, and each group is a population the construction applies to.  The group is named in this table's title and in every other table of the same group.  the seeds outside the set are not dropped: they are the failure table, published beside this one, so an arm that fails on expensive seeds cannot be flattered by the filter.  a seed on which **no** arm converged is configuration hardness, counted in its own column and not against any arm. n = 25 (distinct seeds run on st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of seeds.  a row is this configuration.  a column is the size of the one population every optimisation-phase table on this configuration is over, or a per-arm count of the seeds on which the optimiser was called more than once.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; the arms present here are BR, B0, B3 at seeds 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24.  construction: stats.every_arm_converged — a seed is in the set when every arm present reached an accepted optimum (status ok AND the output file's ifail == 1); stats.retried, which counts attempts[] and never a stored flag.  **this is one arm group of the source.**  The plan's construction assumes what a campaign guarantees — every arm at every seed — and a gate's runs do not: the source is therefore split by which arms have a run at a seed, and each group is a population the construction applies to.  The group is named in this table's title and in every other table of the same group.  the seeds outside the set are not dropped: they are the failure table, published beside this one, so an arm that fails on expensive seeds cannot be flattered by the filter.  a seed on which **no** arm converged is configuration hardness, counted in its own column and not against any arm.*
| arms | which | seeds offered | n (every arm converged) | seeds in the set | configuration-invalid seeds | retried seeds per arm |
|---|---|---|---|---|---|---|
| 3 | BR · B0 · B3 | 25 | 22 | 0, 1, 2, 3, 4, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 18, 19, 20, 21, 22, 23, 24 | 1 | BR 5 · B0 3 · B3 2 |
*n = 25 (distinct seeds run on st_regression).*
*How to read: this n is the denominator of every other optimisation-phase table on this configuration*

*How to read: this n is the denominator of every other optimisation-phase table on this configuration*

**`the failure table — st_regression — campaign_optimisation · BR·B0·B3`**

*Caption: units: counts: model executions for the cost columns, optimiser exit codes for ifail.  a row is one seed outside the converged set.  a column is which arm failed there, how it failed, what it cost, and what the other arms cost at the same start.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 3 of 25 seed(s) on st_regression lie outside the every-arm-converged set.  construction: stats.accepted_optimum for membership; the cost column is node_calls_solve_phase, the same unit the cost table uses.  an arm the gate did not run at a seed reads *not run* rather than *failed*: an absent record and a failed run are different results.  a seed on which every arm failed or was absent is marked configuration-invalid. n = 25 (distinct seeds run on st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts: model executions for the cost columns, optimiser exit codes for ifail.  a row is one seed outside the converged set.  a column is which arm failed there, how it failed, what it cost, and what the other arms cost at the same start.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 3 of 25 seed(s) on st_regression lie outside the every-arm-converged set.  construction: stats.accepted_optimum for membership; the cost column is node_calls_solve_phase, the same unit the cost table uses.  an arm the gate did not run at a seed reads *not run* rather than *failed*: an absent record and a failed run are different results.  a seed on which every arm failed or was absent is marked configuration-invalid.*
| seed | failed arm(s) | not run | ifail | attempts | failed arm node calls | other arms' node calls | configuration-invalid |
|---|---|---|---|---|---|---|---|
| 5 | B3 | — | 5.0 | 3 | 479630 | BR 160335 / B0 175413 / B3 — | no |
| 10 | B0 | — | 5.0 | 3 | 667989 | BR 717990 / B0 — / B3 129012 | no |
| 17 | BR, B0, B3 | — | 5.0, 5.0, 5.0 | 4, 4, 4 | 8064, 8820, 4921 | BR — / B0 — / B3 — | yes |
*n = 25 (distinct seeds run on st_regression).*
*How to read: the converged set is the fairer cost population but can flatter an arm that fails on expensive seeds; this table is what keeps it honest*

*How to read: the converged set is the fairer cost population but can flatter an arm that fails on expensive seeds; this table is what keeps it honest*

**`same optimum (check 1) — st_regression — campaign_optimisation · BR·B0·B3`**

*Caption: units: dimensionless: a relative difference of the normalised objective.  a row is one arm pair over the seed set.  a column is the paired relative objective difference's median and p90, the threshold they are judged against, and the clustering statistics.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 22 seed(s) on which every arm of st_regression reached an accepted optimum.  construction: stats.relative_objective_difference — |Δ norm_objf| / max(|a|, |b|) per pair, from the hex floats; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); stats.acceptance_threshold = max(F × yardstick, floor) with F = 10 and floor = 1e-06, the yardstick being the BR → B0 spread measured in this same population; stats.clusters at a relative gap of 1e-05.  the yardstick row carries no threshold and no verdict: it *is* the threshold's calibration.  *below resolution* counts pairs further apart than the correctness floor and closer than the cluster gap — distinct optima below cluster resolution, a named category and not a rounding remark.  the retried column is computed from attempts[], never from a stored flag, so a pair containing a retry is visible here as well as in the cost table. n = 22 (seeds on which every arm of st_regression converged). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless: a relative difference of the normalised objective.  a row is one arm pair over the seed set.  a column is the paired relative objective difference's median and p90, the threshold they are judged against, and the clustering statistics.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 22 seed(s) on which every arm of st_regression reached an accepted optimum.  construction: stats.relative_objective_difference — |Δ norm_objf| / max(|a|, |b|) per pair, from the hex floats; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); stats.acceptance_threshold = max(F × yardstick, floor) with F = 10 and floor = 1e-06, the yardstick being the BR → B0 spread measured in this same population; stats.clusters at a relative gap of 1e-05.  the yardstick row carries no threshold and no verdict: it *is* the threshold's calibration.  *below resolution* counts pairs further apart than the correctness floor and closer than the cluster gap — distinct optima below cluster resolution, a named category and not a rounding remark.  the retried column is computed from attempts[], never from a stored flag, so a pair containing a retry is visible here as well as in the cost table.*
| pair | n | r median | r p90 | threshold median | threshold p90 | verdict | hops | below resolution | retried seeds in pair |
|---|---|---|---|---|---|---|---|---|---|
| BR → B0 (yardstick) | 22 | 1.553e-13 | 5.908e-09 | — | — | — | 2/22 (0.09) | 0 | 3 |
| B0 → B3 | 22 | 3.467e-13 | 3.510e-09 | 1.000e-06 | 1.000e-06 | PASS | 1/22 (0.05) | 0 | 1 |
*n = 22 (seeds on which every arm of st_regression converged).*
*How to read: a verdict is read only where a threshold exists; a hop is a seed whose two sides landed in different objective clusters, and the yardstick pair's own hop rate is the comparator*

*How to read: a verdict is read only where a threshold exists; a hop is a seed whose two sides landed in different objective clusters, and the yardstick pair's own hop rate is the comparator*

**`iteration multiplier (check 2) — st_regression — campaign_optimisation · BR·B0·B3`**

*Caption: units: dimensionless ratios of counts.  a row is one arm against the flat control over the seed set.  a column is one of check 2's two iteration constructions, its sum ratio, or the evaluation-count ratio beside them.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 22 seed(s) on which every arm of st_regression reached an accepted optimum.  construction: stats.iterations_summed_over_attempts (the **declared acceptance statistic**, nearest-rank upper-middle median against 1.05) and stats.iterations_final_attempt (the previous revision's construction, published beside for comparability).  Both are read from attempts[], so a disagreement between them is a disagreement about that list and not about which field was read.  the sum ratio is published beside every median because a median of per-seed ratios and the ratio of the sums can point in opposite directions.  the evaluation-count ratio is beside both: iterations, even summed, miss the lifted arm's extra stencil column and the line-search evaluations that vary at equal iteration count.  *constructions disagree* counts the seeds on which the final attempt's pair and the summed pair are not the same numbers — 0 means no run in this population retried. n = 22 (seeds on which every arm of st_regression converged). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless ratios of counts.  a row is one arm against the flat control over the seed set.  a column is one of check 2's two iteration constructions, its sum ratio, or the evaluation-count ratio beside them.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 22 seed(s) on which every arm of st_regression reached an accepted optimum.  construction: stats.iterations_summed_over_attempts (the **declared acceptance statistic**, nearest-rank upper-middle median against 1.05) and stats.iterations_final_attempt (the previous revision's construction, published beside for comparability).  Both are read from attempts[], so a disagreement between them is a disagreement about that list and not about which field was read.  the sum ratio is published beside every median because a median of per-seed ratios and the ratio of the sums can point in opposite directions.  the evaluation-count ratio is beside both: iterations, even summed, miss the lifted arm's extra stencil column and the line-search evaluations that vary at equal iteration count.  *constructions disagree* counts the seeds on which the final attempt's pair and the summed pair are not the same numbers — 0 means no run in this population retried.*
| pair | n | summed median (acceptance) | summed sum ratio | verdict | final-attempt median | final-attempt sum ratio | evaluations median | attempts per seed (base/arm) | constructions disagree |
|---|---|---|---|---|---|---|---|---|---|
| B0 → BR (beside) | 22 | 1.0000 | 1.2405 | beside | 1.0000 | 0.9221 | 0.9906 | 0:1/1, 1:1/1, 2:2/2, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 11:1/1, 12:1/2, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 18:1/1, 19:1/1, 20:1/1, 21:1/1, 22:1/1, 23:1/1, 24:1/3 | 3 |
| B0 → B3 | 22 | 1.0000 | 0.9530 | PASS | 1.0000 | 1.0019 | 2.7767 | 0:1/1, 1:1/1, 2:2/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 18:1/1, 19:1/1, 20:1/1, 21:1/1, 22:1/1, 23:1/1, 24:1/1 | 1 |
*n = 22 (seeds on which every arm of st_regression converged).*
*How to read: read the acceptance column against the summed median; a final-attempt median that differs from it names the retried seeds, which the attempts column lists*

*How to read: read the acceptance column against the summed median; a final-attempt median that differs from it names the retried seeds, which the attempts column lists*

**`cost (check 4) — st_regression — campaign_optimisation · BR·B0·B3`**

*Caption: units: model executions during the solve; ratios dimensionless.  a row is one arm over the seed set.  a column is an absolute per-run mean with its bracket, or one reading of the ratio against the flat control.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 22 seed(s) on which every arm of st_regression reached an accepted optimum.  construction: stats.with_and_without_retried — solve-phase node calls **summed over attempts[]** per run, so the ratio is over the quantity the attempts decompose (the identity is in the attempt-summation table); pooled = Σ arm / Σ base, median = nearest-rank upper-middle of the per-seed ratios, worse = seeds on which the arm cost more.  **retries are a term, not a footnote**: the ratio is published *with* and *without* the retried seeds because both readings are defensible — a retry the other arm did not need is real cost the architecture avoided at that start, *and* it is a robustness event rather than a per-evaluation cost.  a seed counts as retried when **either** side of the pair retried: the pair is what the ratio is over.  the arrangement-method calls are a column of their own and are never pooled into the node calls.  the output-time and audit sweeps are excluded from this unit symmetrically in every arm. n = 22 (seeds on which every arm of st_regression converged). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model executions during the solve; ratios dimensionless.  a row is one arm over the seed set.  a column is an absolute per-run mean with its bracket, or one reading of the ratio against the flat control.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 22 seed(s) on which every arm of st_regression reached an accepted optimum.  construction: stats.with_and_without_retried — solve-phase node calls **summed over attempts[]** per run, so the ratio is over the quantity the attempts decompose (the identity is in the attempt-summation table); pooled = Σ arm / Σ base, median = nearest-rank upper-middle of the per-seed ratios, worse = seeds on which the arm cost more.  **retries are a term, not a footnote**: the ratio is published *with* and *without* the retried seeds because both readings are defensible — a retry the other arm did not need is real cost the architecture avoided at that start, *and* it is a robustness event rather than a per-evaluation cost.  a seed counts as retried when **either** side of the pair retried: the pair is what the ratio is over.  the arrangement-method calls are a column of their own and are never pooled into the node calls.  the output-time and audit sweeps are excluded from this unit symmetrically in every arm.*
| arm | n | node calls / run | bracket | arrangement·method calls | with retried: pooled | with retried: median | worse | retried seeds | without retried: pooled | without retried: median | n without |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | 22 | 126867.7 | [39627, 838929] | 0 | 1.1968 | 0.9906 | 3 | 3 | 0.8999 | 0.9906 | 19 |
| B0 | 22 | 106007.0 | [39732, 295701] | 0 | 1.0000 | 1.0000 | 0 | 1 | 1.0000 | 1.0000 | 21 |
| B3 | 22 | 56507.3 | [23484, 169358] | 280776 | 0.5331 | 0.5911 | 0 | 1 | 0.5439 | 0.5911 | 21 |
*n = 22 (seeds on which every arm of st_regression converged).*
*How to read: where *retried* is 0 the with- and without- columns are the same number, and the pair of columns is the statement that nothing in this population depended on a retry*

*How to read: where *retried* is 0 the with- and without- columns are the same number, and the pair of columns is the statement that nothing in this population depended on a retry*

**`the attempt summation identity — st_regression — campaign_optimisation · BR·B0·B3`**

*Caption: units: counts: model executions and sweeps of the model sequence.  a row is one optimisation run.  a column is the per-attempt costs, the run's solve-phase total they decompose, and the residual between them.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 75 optimisation run(s) of st_regression, of which 75 carry a per-attempt cost the identity can be checked on.  construction: stats.attempt_summation — Σ over attempts[] against node_calls_solve_phase and dispatch_sweeps_solve_phase.  this identity is why the with- and without-retried-seeds cost ratios may be published: they are computed over quantities that visibly decompose the published total, and a residual that is not 0 would make them ratios of something else.  the record contract already refuses a record whose parts do not add up; this table is the same identity stated as a number a reader can see. n = 75 (optimisation-phase campaign runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts: model executions and sweeps of the model sequence.  a row is one optimisation run.  a column is the per-attempt costs, the run's solve-phase total they decompose, and the residual between them.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; 75 optimisation run(s) of st_regression, of which 75 carry a per-attempt cost the identity can be checked on.  construction: stats.attempt_summation — Σ over attempts[] against node_calls_solve_phase and dispatch_sweeps_solve_phase.  this identity is why the with- and without-retried-seeds cost ratios may be published: they are computed over quantities that visibly decompose the published total, and a residual that is not 0 would make them ratios of something else.  the record contract already refuses a record whose parts do not add up; this table is the same identity stated as a number a reader can see.*
| arm | seed | attempts | retried | node calls per attempt | = solve-phase total | residual | sweeps per attempt | = solve-phase total | residual | decomposes |
|---|---|---|---|---|---|---|---|---|---|---|
| BR | 0 | 1 | no | 39669 | 39669 | 0 | 1889 | 1889 | 0 | yes |
| BR | 1 | 1 | no | 176379 | 176379 | 0 | 8399 | 8399 | 0 | yes |
| BR | 2 | 2 | yes | 113442 + 96726 | 210168 | 0 | 5402 + 4606 | 10008 | 0 | yes |
| BR | 3 | 1 | no | 72408 | 72408 | 0 | 3448 | 3448 | 0 | yes |
| BR | 4 | 1 | no | 79905 | 79905 | 0 | 3805 | 3805 | 0 | yes |
| BR | 5 | 1 | no | 160335 | 160335 | 0 | 7635 | 7635 | 0 | yes |
| BR | 6 | 1 | no | 71799 | 71799 | 0 | 3419 | 3419 | 0 | yes |
| BR | 7 | 1 | no | 39774 | 39774 | 0 | 1894 | 1894 | 0 | yes |
| BR | 8 | 1 | no | 47565 | 47565 | 0 | 2265 | 2265 | 0 | yes |
| BR | 9 | 1 | no | 243810 | 243810 | 0 | 11610 | 11610 | 0 | yes |
| BR | 10 | 3 | yes | 226149 + 272601 + 219240 | 717990 | 0 | 10769 + 12981 + 10440 | 34190 | 0 | yes |
| BR | 11 | 1 | no | 43869 | 43869 | 0 | 2089 | 2089 | 0 | yes |
| BR | 12 | 2 | yes | 211659 + 68103 | 279762 | 0 | 10079 + 3243 | 13322 | 0 | yes |
| BR | 13 | 1 | no | 55776 | 55776 | 0 | 2656 | 2656 | 0 | yes |
| BR | 14 | 1 | no | 88683 | 88683 | 0 | 4223 | 4223 | 0 | yes |
| BR | 15 | 1 | no | 123795 | 123795 | 0 | 5895 | 5895 | 0 | yes |
| BR | 16 | 1 | no | 96852 | 96852 | 0 | 4612 | 4612 | 0 | yes |
| BR | 17 | 4 | yes | 2121 + 2121 + 1785 + 2037 | 8064 | 0 | 101 + 101 + 85 + 97 | 384 | 0 | yes |
| BR | 18 | 1 | no | 51618 | 51618 | 0 | 2458 | 2458 | 0 | yes |
| BR | 19 | 1 | no | 43575 | 43575 | 0 | 2075 | 2075 | 0 | yes |
| BR | 20 | 1 | no | 56049 | 56049 | 0 | 2669 | 2669 | 0 | yes |
| BR | 21 | 1 | no | 39627 | 39627 | 0 | 1887 | 1887 | 0 | yes |
| BR | 22 | 1 | no | 47439 | 47439 | 0 | 2259 | 2259 | 0 | yes |
| BR | 23 | 1 | no | 43638 | 43638 | 0 | 2078 | 2078 | 0 | yes |
| BR | 24 | 3 | yes | 249102 + 283311 + 306516 | 838929 | 0 | 11862 + 13491 + 14596 | 39949 | 0 | yes |
| B0 | 0 | 1 | no | 42756 | 42756 | 0 | 2036 | 2036 | 0 | yes |
| B0 | 1 | 1 | no | 226002 | 226002 | 0 | 10762 | 10762 | 0 | yes |
| B0 | 2 | 2 | yes | 117789 + 101031 | 218820 | 0 | 5609 + 4811 | 10420 | 0 | yes |
| B0 | 3 | 1 | no | 76461 | 76461 | 0 | 3641 | 3641 | 0 | yes |
| B0 | 4 | 1 | no | 80661 | 80661 | 0 | 3841 | 3841 | 0 | yes |
| B0 | 5 | 1 | no | 175413 | 175413 | 0 | 8353 | 8353 | 0 | yes |
| B0 | 6 | 1 | no | 72450 | 72450 | 0 | 3450 | 3450 | 0 | yes |
| B0 | 7 | 1 | no | 39732 | 39732 | 0 | 1892 | 1892 | 0 | yes |
| B0 | 8 | 1 | no | 47901 | 47901 | 0 | 2281 | 2281 | 0 | yes |
| B0 | 9 | 1 | no | 190512 | 190512 | 0 | 9072 | 9072 | 0 | yes |
| B0 | 10 | 3 | yes | 263676 + 239421 + 164892 | 667989 | 0 | 12556 + 11401 + 7852 | 31809 | 0 | yes |
| B0 | 11 | 1 | no | 44037 | 44037 | 0 | 2097 | 2097 | 0 | yes |
| B0 | 12 | 1 | no | 295701 | 295701 | 0 | 14081 | 14081 | 0 | yes |
| B0 | 13 | 1 | no | 56070 | 56070 | 0 | 2670 | 2670 | 0 | yes |
| B0 | 14 | 1 | no | 88998 | 88998 | 0 | 4238 | 4238 | 0 | yes |
| B0 | 15 | 1 | no | 251958 | 251958 | 0 | 11998 | 11998 | 0 | yes |
| B0 | 16 | 1 | no | 104454 | 104454 | 0 | 4974 | 4974 | 0 | yes |
| B0 | 17 | 4 | yes | 2289 + 2352 + 2016 + 2163 | 8820 | 0 | 109 + 112 + 96 + 103 | 420 | 0 | yes |
| B0 | 18 | 1 | no | 51975 | 51975 | 0 | 2475 | 2475 | 0 | yes |
| B0 | 19 | 1 | no | 55965 | 55965 | 0 | 2665 | 2665 | 0 | yes |
| B0 | 20 | 1 | no | 59619 | 59619 | 0 | 2839 | 2839 | 0 | yes |
| B0 | 21 | 1 | no | 39732 | 39732 | 0 | 1892 | 1892 | 0 | yes |
| B0 | 22 | 1 | no | 48657 | 48657 | 0 | 2317 | 2317 | 0 | yes |
| B0 | 23 | 1 | no | 46977 | 46977 | 0 | 2237 | 2237 | 0 | yes |
| B0 | 24 | 1 | no | 192717 | 192717 | 0 | 9177 | 9177 | 0 | yes |
| B3 | 0 | 1 | no | 23505 | 23505 | 0 | 5259 | 5259 | 0 | yes |
| B3 | 1 | 1 | no | 134560 | 134560 | 0 | 31071 | 31071 | 0 | yes |
| B3 | 2 | 1 | no | 93767 | 93767 | 0 | 21153 | 21153 | 0 | yes |
| B3 | 3 | 1 | no | 43204 | 43204 | 0 | 9694 | 9694 | 0 | yes |
| B3 | 4 | 1 | no | 47985 | 47985 | 0 | 10721 | 10721 | 0 | yes |
| B3 | 5 | 3 | yes | 175996 + 137488 + 166146 | 479630 | 0 | 39645 + 29681 + 41059 | 110385 | 0 | yes |
| B3 | 6 | 1 | no | 43103 | 43103 | 0 | 9632 | 9632 | 0 | yes |
| B3 | 7 | 1 | no | 23484 | 23484 | 0 | 5258 | 5258 | 0 | yes |
| B3 | 8 | 1 | no | 28385 | 28385 | 0 | 6352 | 6352 | 0 | yes |
| B3 | 9 | 1 | no | 143424 | 143424 | 0 | 32469 | 32469 | 0 | yes |
| B3 | 10 | 1 | no | 129012 | 129012 | 0 | 30849 | 30849 | 0 | yes |
| B3 | 11 | 1 | no | 25988 | 25988 | 0 | 5821 | 5821 | 0 | yes |
| B3 | 12 | 1 | no | 40163 | 40163 | 0 | 9050 | 9050 | 0 | yes |
| B3 | 13 | 1 | no | 32983 | 32983 | 0 | 7420 | 7420 | 0 | yes |
| B3 | 14 | 1 | no | 52965 | 52965 | 0 | 11830 | 11830 | 0 | yes |
| B3 | 15 | 1 | no | 169358 | 169358 | 0 | 38460 | 38460 | 0 | yes |
| B3 | 16 | 1 | no | 62796 | 62796 | 0 | 14014 | 14014 | 0 | yes |
| B3 | 17 | 4 | yes | 1288 + 1360 + 1045 + 1228 | 4921 | 0 | 290 + 295 + 258 + 278 | 1121 | 0 | yes |
| B3 | 18 | 1 | no | 30852 | 30852 | 0 | 6897 | 6897 | 0 | yes |
| B3 | 19 | 1 | no | 25952 | 25952 | 0 | 5807 | 5807 | 0 | yes |
| B3 | 20 | 1 | no | 32958 | 32958 | 0 | 7432 | 7432 | 0 | yes |
| B3 | 21 | 1 | no | 23520 | 23520 | 0 | 5261 | 5261 | 0 | yes |
| B3 | 22 | 1 | no | 28505 | 28505 | 0 | 6389 | 6389 | 0 | yes |
| B3 | 23 | 1 | no | 25771 | 25771 | 0 | 5799 | 5799 | 0 | yes |
| B3 | 24 | 1 | no | 109933 | 109933 | 0 | 24965 | 24965 | 0 | yes |
*n = 75 (optimisation-phase campaign runs of st_regression).*
*How to read: every residual column reads 0, or the run is refused before it reaches any other table here*

*How to read: every residual column reads 0, or the run is refused before it reaches any other table here*

**`achieved accuracy at the accepted optimum — st_regression — campaign_optimisation · BR·B0·B3`**

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state audit maximum over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; the finished optimisation-phase runs of st_regression in this arm group.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle.  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys.  **audit position**: entry_to_write_output_files.  `entry_to_write_output_files` is the declared position — the state the solve handed over — and `after_run` is the reproduction gate's, where the previous revision measured.  The two are different quantities and share this table only because the position is a column of its own.  **the audit instrument's version is read from the record** (stats.audit_instrument).  Task A61 (insstrain-diagnosis) showed that the largest residual at the accepted point on the pulsed configurations is an artefact of this instrument — the output path permanently changes a model setting the snapshot does not restore, so the audit's sweep is not the loop's map — and task A62 (exit-audit-restore) widens the snapshot under decision D25, which moves every value in these columns.  The argmax is read from the record and is not written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction.  the two rulers' exclusion counts are listed per row and never pooled; a run whose restricted block is null carries no count and reads —.  **n counts runs, not values** (stats.accuracy_population, the same construction the evaluation phase's table uses): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic. Audit position: `entry_to_write_output_files`. n = 75 (optimisation-phase runs of st_regression in this arm group). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.  a row is one arm on one ruler.  a column is the restricted or whole-state audit maximum over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; the finished optimisation-phase runs of st_regression in this arm group.  construction: stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle.  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys.  **audit position**: entry_to_write_output_files.  `entry_to_write_output_files` is the declared position — the state the solve handed over — and `after_run` is the reproduction gate's, where the previous revision measured.  The two are different quantities and share this table only because the position is a column of its own.  **the audit instrument's version is read from the record** (stats.audit_instrument).  Task A61 (insstrain-diagnosis) showed that the largest residual at the accepted point on the pulsed configurations is an artefact of this instrument — the output path permanently changes a model setting the snapshot does not restore, so the audit's sweep is not the loop's map — and task A62 (exit-audit-restore) widens the snapshot under decision D25, which moves every value in these columns.  The argmax is read from the record and is not written into this table.  **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction.  the two rulers' exclusion counts are listed per row and never pooled; a run whose restricted block is null carries no count and reads —.  **n counts runs, not values** (stats.accuracy_population, the same construction the evaluation phase's table uses): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11.  Over this population every run carried the statistic.*
| arm | ruler | n (runs) | with a restricted statistic | restricted median | restricted max | restricted argmax | components above τ | whole-state median | components excluded | audit position | audit instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | frozen | 25 | 25 | 4.875e-14 | 5.040e-14 | blanket.deg_blkt_inboard_poloidal_plasma, physics.f_beta_alpha_beam_thermal | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 4.875e-14 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| BR | mixed | 25 | 25 | 4.871e-14 | 5.035e-14 | blanket.deg_blkt_inboard_poloidal_plasma, physics.f_beta_alpha_beam_thermal | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 4.871e-14 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | frozen | 25 | 25 | 4.894e-14 | 4.967e-14 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.big_q_plasma, physics.f_beta_alpha_beam_thermal | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 4.894e-14 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | mixed | 25 | 25 | 4.889e-14 | 4.962e-14 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.big_q_plasma, physics.f_beta_alpha_beam_thermal | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 4.889e-14 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B3 | frozen | 25 | 25 | 7.497e-12 | 3.587e-11 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, heat_transport.tlvpmw, physics.f_beta_alpha_beam_thermal, superconducting_tfcoil.a_tf_plasma_case | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.598e+00 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B3 | mixed | 25 | 25 | 6.643e-12 | 3.585e-11 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, heat_transport.tlvpmw, physics.f_beta_alpha_beam_thermal, superconducting_tfcoil.a_tf_plasma_case | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.000e+00 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
*n = 75 (optimisation-phase runs of st_regression in this arm group).*
*How to read: read the argmax beside the maximum: a residual above the tolerance whose argmax is the component A61 named is a statement about the audit instrument, not about the arm*

*How to read: read the argmax beside the maximum: a residual above the tolerance whose argmax is the component A61 named is a statement about the audit instrument, not about the arm*

**`per-sweep overhead — st_regression — campaign_optimisation · BR·B0·B3`**

*Caption: units: counts: evaluations of a convergence test, components compared summed over them, and sweeps of the model sequence.  a row is one optimisation run.  a column is a counter of one **named** convergence test, or a sweep total.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; the finished optimisation-phase campaign runs of st_regression.  construction: stats.predicate_widths and stats.empty_visit_shares, from the driver's own counters — exact and concurrency-invariant.  **the two predicates are never pooled**: an arm stops on exactly one of them and their widths differ by nearly two orders of magnitude, so their sum belongs to neither.  The table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**, and the share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — which over this population is 0 %, 10.7 %, 10.8 %, 10.82 %, 10.83 %, 10.84 %, 10.85 %, 10.86 %, 10.87 %, 10.9 %, 10.91 %, 10.92 %, 10.94 %, 11.15 %, 11.18 %, 11.22 %, 11.3 %, 11.57 %.  The visit share is larger and is never quoted.  no conclusion rests on a timing: the question is asked in counts alone. n = 75 (finished optimisation-phase campaign runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts: evaluations of a convergence test, components compared summed over them, and sweeps of the model sequence.  a row is one optimisation run.  a column is a counter of one **named** convergence test, or a sweep total.  population: campaign_optimisation — the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost; the finished optimisation-phase campaign runs of st_regression.  construction: stats.predicate_widths and stats.empty_visit_shares, from the driver's own counters — exact and concurrency-invariant.  **the two predicates are never pooled**: an arm stops on exactly one of them and their widths differ by nearly two orders of magnitude, so their sum belongs to neither.  The table module refuses a column carrying one.  **the empty block visits are counted and disclaimed, never repaired**, and the share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — which over this population is 0 %, 10.7 %, 10.8 %, 10.82 %, 10.83 %, 10.84 %, 10.85 %, 10.86 %, 10.87 %, 10.9 %, 10.91 %, 10.92 %, 10.94 %, 11.15 %, 11.18 %, 11.22 %, 11.3 %, 11.57 %.  The visit share is larger and is never quoted.  no conclusion rests on a timing: the question is asked in counts alone.*
| arm | seed | stops on | dispatch sweeps | of which solve phase | output-time loop | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | 0 | upstream | 1891 | 1889 | 2 | 0 | 0 | — | — | 1319 | 18491 | 14.0 | 0.00 % |
| BR | 1 | upstream | 8401 | 8399 | 2 | 0 | 0 | — | — | 5789 | 84431 | 14.6 | 0.00 % |
| BR | 2 | upstream | 10010 | 10008 | 2 | 0 | 0 | — | — | 7128 | 100674 | 14.1 | 0.00 % |
| BR | 3 | upstream | 3450 | 3448 | 2 | 0 | 0 | — | — | 2398 | 33646 | 14.0 | 0.00 % |
| BR | 4 | upstream | 3807 | 3805 | 2 | 0 | 0 | — | — | 2635 | 37357 | 14.2 | 0.00 % |
| BR | 5 | upstream | 7637 | 7635 | 2 | 0 | 0 | — | — | 5265 | 77049 | 14.6 | 0.00 % |
| BR | 6 | upstream | 3421 | 3419 | 2 | 0 | 0 | — | — | 2369 | 33527 | 14.2 | 0.00 % |
| BR | 7 | upstream | 1896 | 1894 | 2 | 0 | 0 | — | — | 1324 | 18586 | 14.0 | 0.00 % |
| BR | 8 | upstream | 2267 | 2265 | 2 | 0 | 0 | — | — | 1575 | 22113 | 14.0 | 0.00 % |
| BR | 9 | upstream | 11612 | 11610 | 2 | 0 | 0 | — | — | 7980 | 117618 | 14.7 | 0.00 % |
| BR | 10 | upstream | 34192 | 34190 | 2 | 0 | 0 | — | — | 23600 | 343622 | 14.6 | 0.00 % |
| BR | 11 | upstream | 2091 | 2089 | 2 | 0 | 0 | — | — | 1459 | 20431 | 14.0 | 0.00 % |
| BR | 12 | upstream | 13324 | 13322 | 2 | 0 | 0 | — | — | 9362 | 132572 | 14.2 | 0.00 % |
| BR | 13 | upstream | 2658 | 2656 | 2 | 0 | 0 | — | — | 1846 | 25948 | 14.1 | 0.00 % |
| BR | 14 | upstream | 4225 | 4223 | 2 | 0 | 0 | — | — | 2933 | 41669 | 14.2 | 0.00 % |
| BR | 15 | upstream | 5897 | 5895 | 2 | 0 | 0 | — | — | 4065 | 59235 | 14.6 | 0.00 % |
| BR | 16 | upstream | 4614 | 4612 | 2 | 0 | 0 | — | — | 3202 | 45700 | 14.3 | 0.00 % |
| BR | 17 | upstream | 386 | 384 | 2 | 0 | 0 | — | — | 264 | 3468 | 13.1 | 0.00 % |
| BR | 18 | upstream | 2460 | 2458 | 2 | 0 | 0 | — | — | 1708 | 24136 | 14.1 | 0.00 % |
| BR | 19 | upstream | 2077 | 2075 | 2 | 0 | 0 | — | — | 1445 | 20255 | 14.0 | 0.00 % |
| BR | 20 | upstream | 2671 | 2669 | 2 | 0 | 0 | — | — | 1859 | 26069 | 14.0 | 0.00 % |
| BR | 21 | upstream | 1889 | 1887 | 2 | 0 | 0 | — | — | 1317 | 18471 | 14.0 | 0.00 % |
| BR | 22 | upstream | 2261 | 2259 | 2 | 0 | 0 | — | — | 1569 | 21999 | 14.0 | 0.00 % |
| BR | 23 | upstream | 2080 | 2078 | 2 | 0 | 0 | — | — | 1448 | 20222 | 14.0 | 0.00 % |
| BR | 24 | upstream | 39951 | 39949 | 2 | 0 | 0 | — | — | 27559 | 401527 | 14.6 | 0.00 % |
| B0 | 0 | coupling_state | 2038 | 2036 | 2 | 2036 | 1683772 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 1 | coupling_state | 10764 | 10762 | 2 | 10762 | 8900174 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 2 | coupling_state | 10422 | 10420 | 2 | 10420 | 8617340 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 3 | coupling_state | 3643 | 3641 | 2 | 3641 | 3011107 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 4 | coupling_state | 3843 | 3841 | 2 | 3841 | 3176507 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 5 | coupling_state | 8355 | 8353 | 2 | 8353 | 6907931 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 6 | coupling_state | 3452 | 3450 | 2 | 3450 | 2853150 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 7 | coupling_state | 1894 | 1892 | 2 | 1892 | 1564684 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 8 | coupling_state | 2283 | 2281 | 2 | 2281 | 1886387 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 9 | coupling_state | 9074 | 9072 | 2 | 9072 | 7502544 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 10 | coupling_state | 31811 | 31809 | 2 | 31809 | 26306043 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 11 | coupling_state | 2099 | 2097 | 2 | 2097 | 1734219 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 12 | coupling_state | 14083 | 14081 | 2 | 14081 | 11644987 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 13 | coupling_state | 2672 | 2670 | 2 | 2670 | 2208090 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 14 | coupling_state | 4240 | 4238 | 2 | 4238 | 3504826 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 15 | coupling_state | 12000 | 11998 | 2 | 11998 | 9922346 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 16 | coupling_state | 4976 | 4974 | 2 | 4974 | 4113498 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 17 | coupling_state | 422 | 420 | 2 | 420 | 347340 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 18 | coupling_state | 2477 | 2475 | 2 | 2475 | 2046825 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 19 | coupling_state | 2667 | 2665 | 2 | 2665 | 2203955 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 20 | coupling_state | 2841 | 2839 | 2 | 2839 | 2347853 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 21 | coupling_state | 1894 | 1892 | 2 | 1892 | 1564684 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 22 | coupling_state | 2319 | 2317 | 2 | 2317 | 1916159 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 23 | coupling_state | 2239 | 2237 | 2 | 2237 | 1849999 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 24 | coupling_state | 9179 | 9177 | 2 | 9177 | 7589379 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B3 | 0 | coupling_state | 5260 | 5259 | 0 | 4119 | 970258 | 235.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.84 % |
| B3 | 1 | coupling_state | 31072 | 31071 | 0 | 24051 | 5659602 | 235.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.30 % |
| B3 | 2 | coupling_state | 21154 | 21153 | 0 | 16533 | 3892592 | 235.4 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.92 % |
| B3 | 3 | coupling_state | 9695 | 9694 | 0 | 7594 | 1788185 | 235.5 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.83 % |
| B3 | 4 | coupling_state | 10722 | 10721 | 0 | 8381 | 1972937 | 235.4 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.91 % |
| B3 | 5 | coupling_state | 110386 | 110385 | 0 | 85605 | 20138750 | 235.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.22 % |
| B3 | 6 | coupling_state | 9633 | 9632 | 0 | 7532 | 1773223 | 235.4 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.90 % |
| B3 | 7 | coupling_state | 5259 | 5258 | 0 | 4118 | 970028 | 235.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.84 % |
| B3 | 8 | coupling_state | 6353 | 6352 | 0 | 4972 | 1171089 | 235.5 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.86 % |
| B3 | 9 | coupling_state | 32470 | 32469 | 0 | 25209 | 5925850 | 235.1 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.18 % |
| B3 | 10 | coupling_state | 30850 | 30849 | 0 | 23709 | 5588124 | 235.7 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.57 % |
| B3 | 11 | coupling_state | 5822 | 5821 | 0 | 4561 | 1074441 | 235.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.82 % |
| B3 | 12 | coupling_state | 9051 | 9050 | 0 | 7070 | 1664464 | 235.4 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.94 % |
| B3 | 13 | coupling_state | 7421 | 7420 | 0 | 5800 | 1366359 | 235.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.91 % |
| B3 | 14 | coupling_state | 11831 | 11830 | 0 | 9250 | 2177370 | 235.4 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.90 % |
| B3 | 15 | coupling_state | 38461 | 38460 | 0 | 29880 | 7024544 | 235.1 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.15 % |
| B3 | 16 | coupling_state | 14015 | 14014 | 0 | 10954 | 2577921 | 235.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.92 % |
| B3 | 17 | coupling_state | 1122 | 1121 | 0 | 881 | 207690 | 235.7 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.70 % |
| B3 | 18 | coupling_state | 6898 | 6897 | 0 | 5397 | 1270730 | 235.5 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.87 % |
| B3 | 19 | coupling_state | 5808 | 5807 | 0 | 4547 | 1071105 | 235.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.85 % |
| B3 | 20 | coupling_state | 7433 | 7432 | 0 | 5812 | 1369273 | 235.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.90 % |
| B3 | 21 | coupling_state | 5262 | 5261 | 0 | 4121 | 970697 | 235.5 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.83 % |
| B3 | 22 | coupling_state | 6390 | 6389 | 0 | 5009 | 1179088 | 235.4 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.80 % |
| B3 | 23 | coupling_state | 5800 | 5799 | 0 | 4539 | 1069466 | 235.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.86 % |
| B3 | 24 | coupling_state | 24966 | 24965 | 0 | 19385 | 4558929 | 235.2 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.18 % |
*n = 75 (finished optimisation-phase campaign runs of st_regression).*
*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 for that arm, which is why they are kept apart*

*How to read: read the width column of the test the arm actually stops on; the other test's columns are 0 for that arm, which is why they are kept apart*

### 4.4 The same cells, computed a second time

*Emitted by `experiment_runner.py --measure recomputed_tables`; every cell of §4.2 and §4.3 recomputed by an implementation that shares no construction with the tally; the verdict on whether the two agree is gate `recomputation`'s, in §4.1.*

**`achieved accuracy at the accepted optimum — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state audit maximum over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the finished optimisation-phase runs of large_tokamak_nof in this arm group.  Construction: median nearest-rank upper-middle; the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: entry_to_write_output_files.  The audit instrument's version is **read from the record**: task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns, and this column is what tells two otherwise identical tables apart.  Both rulers or neither. n = 100 (optimisation-phase runs of large_tokamak_nof in this arm group). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state audit maximum over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the finished optimisation-phase runs of large_tokamak_nof in this arm group.  Construction: median nearest-rank upper-middle; the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: entry_to_write_output_files.  The audit instrument's version is **read from the record**: task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns, and this column is what tells two otherwise identical tables apart.  Both rulers or neither.*
| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_max | argmax | n_above_tau | whole_median | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | frozen | 22 | 22 | 1.14998e-11 | 1.33158e-11 | heat_transport.tlvpmw | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.14998e-11 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| BR | mixed | 22 | 22 | 1.14998e-11 | 1.25276e-11 | heat_transport.tlvpmw | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.14998e-11 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | frozen | 22 | 22 | 1.14994e-11 | 1.33159e-11 | heat_transport.tlvpmw | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.14994e-11 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | mixed | 22 | 22 | 1.14994e-11 | 1.25278e-11 | heat_transport.tlvpmw | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.14994e-11 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B1 | frozen | 22 | 22 | 0 | 7.25732e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.c_pf_cs_coil_flat_top_ma | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B1 | mixed | 22 | 22 | 0 | 6.92805e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.c_pf_cs_coil_flat_top_ma | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B3 | frozen | 22 | 22 | 0 | 7.25732e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.c_pf_cs_coil_flat_top_ma | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.066 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B3 | mixed | 22 | 22 | 0 | 6.92805e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.c_pf_cs_coil_flat_top_ma | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
*n = 100 (optimisation-phase runs of large_tokamak_nof in this arm group).*

**`achieved accuracy at the accepted optimum — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state audit maximum over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the finished optimisation-phase runs of low_aspect_ratio_DEMO in this arm group.  Construction: median nearest-rank upper-middle; the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: entry_to_write_output_files.  The audit instrument's version is **read from the record**: task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns, and this column is what tells two otherwise identical tables apart.  Both rulers or neither. n = 100 (optimisation-phase runs of low_aspect_ratio_DEMO in this arm group). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state audit maximum over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the finished optimisation-phase runs of low_aspect_ratio_DEMO in this arm group.  Construction: median nearest-rank upper-middle; the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: entry_to_write_output_files.  The audit instrument's version is **read from the record**: task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns, and this column is what tells two otherwise identical tables apart.  Both rulers or neither.*
| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_max | argmax | n_above_tau | whole_median | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | frozen | 23 | 23 | 0 | inf | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.eta_cd_dimensionless_hcd_primary, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| BR | mixed | 23 | 23 | 0 | inf | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.eta_cd_dimensionless_hcd_primary, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | frozen | 21 | 21 | 0 | 5.31457e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | mixed | 21 | 21 | 0 | 3.99521e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B1 | frozen | 20 | 20 | 0 | 5.31457e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B1 | mixed | 20 | 20 | 0 | 4.36506e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B3 | frozen | 20 | 20 | 0 | 5.31457e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.00722 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B3 | mixed | 20 | 20 | 0 | 3.99521e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
*n = 100 (optimisation-phase runs of low_aspect_ratio_DEMO in this arm group).*

**`achieved accuracy at the accepted optimum — st_regression — campaign_optimisation · BR·B0·B3`**

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state audit maximum over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the finished optimisation-phase runs of st_regression in this arm group.  Construction: median nearest-rank upper-middle; the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: entry_to_write_output_files.  The audit instrument's version is **read from the record**: task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns, and this column is what tells two otherwise identical tables apart.  Both rulers or neither. n = 75 (optimisation-phase runs of st_regression in this arm group). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state audit maximum over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the finished optimisation-phase runs of st_regression in this arm group.  Construction: median nearest-rank upper-middle; the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: entry_to_write_output_files.  The audit instrument's version is **read from the record**: task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns, and this column is what tells two otherwise identical tables apart.  Both rulers or neither.*
| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_max | argmax | n_above_tau | whole_median | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | frozen | 25 | 25 | 4.8754e-14 | 5.04035e-14 | blanket.deg_blkt_inboard_poloidal_plasma, physics.f_beta_alpha_beam_thermal | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 4.8754e-14 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| BR | mixed | 25 | 25 | 4.87066e-14 | 5.03546e-14 | blanket.deg_blkt_inboard_poloidal_plasma, physics.f_beta_alpha_beam_thermal | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 4.87066e-14 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | frozen | 25 | 25 | 4.89373e-14 | 4.96704e-14 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.big_q_plasma, physics.f_beta_alpha_beam_thermal | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 4.89373e-14 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | mixed | 25 | 25 | 4.88897e-14 | 4.96221e-14 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.big_q_plasma, physics.f_beta_alpha_beam_thermal | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 4.88897e-14 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B3 | frozen | 25 | 25 | 7.49746e-12 | 3.58709e-11 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, heat_transport.tlvpmw, physics.f_beta_alpha_beam_thermal, superconducting_tfcoil.a_tf_plasma_case | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.5975 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B3 | mixed | 25 | 25 | 6.64269e-12 | 3.58474e-11 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, heat_transport.tlvpmw, physics.f_beta_alpha_beam_thermal, superconducting_tfcoil.a_tf_plasma_case | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
*n = 75 (optimisation-phase runs of st_regression in this arm group).*

**`cost (check 4) — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: model executions during the solve; ratios dimensionless.  A row is one arm over the seed set.  A column is an absolute per-run mean with its bracket, or one reading of the ratio against the flat control.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 22 seed(s) on which every arm of large_tokamak_nof reached an accepted optimum.  Construction: solve-phase node calls **summed over attempts[]** per run, so the ratio is over the quantity the attempts decompose; pooled = Σ arm / Σ base, median nearest-rank upper-middle of the per-seed ratios, worse = seeds on which the arm cost more.  Retries are a term, not a footnote: the ratio is published with and without the retried seeds, and a seed counts as retried when **either** side of the pair retried.  The arrangement-method calls are a column of their own and are never pooled into the node calls. n = 22 (seeds on which every arm of large_tokamak_nof converged). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model executions during the solve; ratios dimensionless.  A row is one arm over the seed set.  A column is an absolute per-run mean with its bracket, or one reading of the ratio against the flat control.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 22 seed(s) on which every arm of large_tokamak_nof reached an accepted optimum.  Construction: solve-phase node calls **summed over attempts[]** per run, so the ratio is over the quantity the attempts decompose; pooled = Σ arm / Σ base, median nearest-rank upper-middle of the per-seed ratios, worse = seeds on which the arm cost more.  Retries are a term, not a footnote: the ratio is published with and without the retried seeds, and a seed counts as retried when **either** side of the pair retried.  The arrangement-method calls are a column of their own and are never pooled into the node calls.*
| arm | n | node_calls_mean | bracket | arrangement_method_calls | with_pooled | with_median | with_worse | n_retried | without_pooled | without_median | without_n |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | 22 | 41479.8 | [36855, 47817] | 0 | 0.97564 | 0.979422 | 0 | 0 | 0.97564 | 0.979422 | 22 |
| B0 | 22 | 42515.5 | [37590, 50253] | 0 | 1 | 1 | 0 | 0 | 1 | 1 | 22 |
| B1 | 22 | 42841.9 | [38220, 49980] | 0 | 1.00768 | 1.01505 | 18 | 0 | 1.00768 | 1.01505 | 22 |
| B3 | 22 | 27187.5 | [24296, 31813] | 117281 | 0.639472 | 0.645152 | 0 | 0 | 0.639472 | 0.645152 | 22 |
*n = 22 (seeds on which every arm of large_tokamak_nof converged).*

**`cost (check 4) — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: model executions during the solve; ratios dimensionless.  A row is one arm over the seed set.  A column is an absolute per-run mean with its bracket, or one reading of the ratio against the flat control.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 11 seed(s) on which every arm of low_aspect_ratio_DEMO reached an accepted optimum.  Construction: solve-phase node calls **summed over attempts[]** per run, so the ratio is over the quantity the attempts decompose; pooled = Σ arm / Σ base, median nearest-rank upper-middle of the per-seed ratios, worse = seeds on which the arm cost more.  Retries are a term, not a footnote: the ratio is published with and without the retried seeds, and a seed counts as retried when **either** side of the pair retried.  The arrangement-method calls are a column of their own and are never pooled into the node calls. n = 11 (seeds on which every arm of low_aspect_ratio_DEMO converged). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model executions during the solve; ratios dimensionless.  A row is one arm over the seed set.  A column is an absolute per-run mean with its bracket, or one reading of the ratio against the flat control.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 11 seed(s) on which every arm of low_aspect_ratio_DEMO reached an accepted optimum.  Construction: solve-phase node calls **summed over attempts[]** per run, so the ratio is over the quantity the attempts decompose; pooled = Σ arm / Σ base, median nearest-rank upper-middle of the per-seed ratios, worse = seeds on which the arm cost more.  Retries are a term, not a footnote: the ratio is published with and without the retried seeds, and a seed counts as retried when **either** side of the pair retried.  The arrangement-method calls are a column of their own and are never pooled into the node calls.*
| arm | n | node_calls_mean | bracket | arrangement_method_calls | with_pooled | with_median | with_worse | n_retried | without_pooled | without_median | without_n |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | 11 | 169943 | [60921, 669207] | 0 | 1.02998 | 1.03517 | 11 | 1 | 1.03508 | 1.03518 | 10 |
| B0 | 11 | 164997 | [58947, 655473] | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 10 |
| B1 | 11 | 114154 | [53214, 360591] | 0 | 0.691856 | 0.804931 | 3 | 1 | 1.01291 | 0.825733 | 10 |
| B3 | 11 | 74312.4 | [34628, 234616] | 157504 | 0.450386 | 0.523683 | 2 | 1 | 0.659427 | 0.537118 | 10 |
*n = 11 (seeds on which every arm of low_aspect_ratio_DEMO converged).*

**`cost (check 4) — st_regression — campaign_optimisation · BR·B0·B3`**

*Caption: units: model executions during the solve; ratios dimensionless.  A row is one arm over the seed set.  A column is an absolute per-run mean with its bracket, or one reading of the ratio against the flat control.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 22 seed(s) on which every arm of st_regression reached an accepted optimum.  Construction: solve-phase node calls **summed over attempts[]** per run, so the ratio is over the quantity the attempts decompose; pooled = Σ arm / Σ base, median nearest-rank upper-middle of the per-seed ratios, worse = seeds on which the arm cost more.  Retries are a term, not a footnote: the ratio is published with and without the retried seeds, and a seed counts as retried when **either** side of the pair retried.  The arrangement-method calls are a column of their own and are never pooled into the node calls. n = 22 (seeds on which every arm of st_regression converged). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model executions during the solve; ratios dimensionless.  A row is one arm over the seed set.  A column is an absolute per-run mean with its bracket, or one reading of the ratio against the flat control.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 22 seed(s) on which every arm of st_regression reached an accepted optimum.  Construction: solve-phase node calls **summed over attempts[]** per run, so the ratio is over the quantity the attempts decompose; pooled = Σ arm / Σ base, median nearest-rank upper-middle of the per-seed ratios, worse = seeds on which the arm cost more.  Retries are a term, not a footnote: the ratio is published with and without the retried seeds, and a seed counts as retried when **either** side of the pair retried.  The arrangement-method calls are a column of their own and are never pooled into the node calls.*
| arm | n | node_calls_mean | bracket | arrangement_method_calls | with_pooled | with_median | with_worse | n_retried | without_pooled | without_median | without_n |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | 22 | 126868 | [39627, 838929] | 0 | 1.19679 | 0.990627 | 3 | 3 | 0.89988 | 0.990627 | 19 |
| B0 | 22 | 106007 | [39732, 295701] | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 21 |
| B3 | 22 | 56507.3 | [23484, 169358] | 280776 | 0.533052 | 0.59106 | 0 | 1 | 0.543877 | 0.59106 | 21 |
*n = 22 (seeds on which every arm of st_regression converged).*

**`cost per call — large_tokamak_nof — campaign_displaced`**

*Caption: units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0p.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 100 run(s) of large_tokamak_nof.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other. n = 100 (evaluation-phase runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0p.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 100 run(s) of large_tokamak_nof.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other.*
| arm | ok | calls_per_eval | calls_bracket | sweeps_per_eval | sweeps_by_block | arrangement_method_calls | paired_seeds | pooled | median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 25/25 | 104.16 | [84, 105] | 4.96 | — | 0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.96875 | 1 | 0 |
| A0 | 25/25 | 115.92 | [105, 126] | 5.52 | FLAT 138 | 0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 1.07812 | 1 | 10 |
| A0p | 25/25 | 107.52 | [84, 126] | 5.12 | FLAT 128 | 0 | — | — | — | — |
| A1 | 25/25 | 60.48 | [60, 63] | 13.16 | FF 0, M1 100, M2 129, M3 75, PULSE 0 | 13.16 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.5625 | 0.571429 | 0 |
*n = 100 (evaluation-phase runs of large_tokamak_nof).*

**`cost per call — large_tokamak_nof — campaign_entry_references`**

*Caption: units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; 1 run(s) of large_tokamak_nof.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other. n = 1 (evaluation-phase runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; 1 run(s) of large_tokamak_nof.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other.*
| arm | ok | calls_per_eval | calls_bracket | sweeps_per_eval | sweeps_by_block | arrangement_method_calls | paired_seeds | pooled | median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 1/1 | 126 | [126, 126] | 6 | FLAT 6 | 0 | — | — | — | — |
*n = 1 (evaluation-phase runs of large_tokamak_nof).*

**`cost per call — large_tokamak_nof — campaign_stencil_backward`**

*Caption: units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0p.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 80 run(s) of large_tokamak_nof.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other. n = 80 (evaluation-phase runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0p.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 80 run(s) of large_tokamak_nof.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other.*
| arm | ok | calls_per_eval | calls_bracket | sweeps_per_eval | sweeps_by_block | arrangement_method_calls | paired_seeds | pooled | median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 20/20 | 60.9 | [42, 84] | 2.9 | — | 0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 0.966667 | 1 | 0 |
| A0 | 20/20 | 66.15 | [42, 105] | 3.15 | FLAT 63 | 0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 1.05 | 1 | 3 |
| A0p | 20/20 | 63 | [42, 105] | 3 | FLAT 60 | 0 | — | — | — | — |
| A1 | 20/20 | 40.35 | [20, 55] | 7.7 | FF 0, M1 38, M2 49, M3 47, PULSE 0 | 7.7 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 0.640476 | 0.607143 | 0 |
*n = 80 (evaluation-phase runs of large_tokamak_nof).*

**`cost per call — large_tokamak_nof — campaign_stencil_forward`**

*Caption: units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0p.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 80 run(s) of large_tokamak_nof.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other. n = 80 (evaluation-phase runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0p.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 80 run(s) of large_tokamak_nof.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other.*
| arm | ok | calls_per_eval | calls_bracket | sweeps_per_eval | sweeps_by_block | arrangement_method_calls | paired_seeds | pooled | median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 20/20 | 61.95 | [42, 84] | 2.95 | — | 0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 0.983333 | 1 | 0 |
| A0 | 20/20 | 66.15 | [42, 105] | 3.15 | FLAT 63 | 0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 1.05 | 1 | 3 |
| A0p | 20/20 | 63 | [42, 105] | 3 | FLAT 60 | 0 | — | — | — | — |
| A1 | 20/20 | 39.15 | [20, 55] | 7.6 | FF 0, M1 38, M2 49, M3 45, PULSE 0 | 7.6 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 0.621429 | 0.607143 | 0 |
*n = 80 (evaluation-phase runs of large_tokamak_nof).*

**`cost per call — low_aspect_ratio_DEMO — campaign_displaced`**

*Caption: units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0p.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 100 run(s) of low_aspect_ratio_DEMO.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other. n = 100 (evaluation-phase runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0p.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 100 run(s) of low_aspect_ratio_DEMO.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other.*
| arm | ok | calls_per_eval | calls_bracket | sweeps_per_eval | sweeps_by_block | arrangement_method_calls | paired_seeds | pooled | median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 25/25 | 105 | [105, 105] | 5 | — | 0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 1.01626 | 1 | 2 |
| A0 | 25/25 | 105 | [105, 105] | 5 | FLAT 125 | 0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 1.01626 | 1 | 2 |
| A0p | 25/25 | 103.32 | [84, 105] | 4.92 | FLAT 123 | 0 | — | — | — | — |
| A1 | 25/25 | 59.64 | [57, 60] | 12.88 | FF 0, M1 100, M2 122, M3 75, PULSE 0 | 12.88 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.577236 | 0.571429 | 0 |
*n = 100 (evaluation-phase runs of low_aspect_ratio_DEMO).*

**`cost per call — low_aspect_ratio_DEMO — campaign_entry_references`**

*Caption: units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; 1 run(s) of low_aspect_ratio_DEMO.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other. n = 1 (evaluation-phase runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; 1 run(s) of low_aspect_ratio_DEMO.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other.*
| arm | ok | calls_per_eval | calls_bracket | sweeps_per_eval | sweeps_by_block | arrangement_method_calls | paired_seeds | pooled | median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 1/1 | 105 | [105, 105] | 5 | FLAT 5 | 0 | — | — | — | — |
*n = 1 (evaluation-phase runs of low_aspect_ratio_DEMO).*

**`cost per call — low_aspect_ratio_DEMO — campaign_stencil_backward`**

*Caption: units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0p.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 76 run(s) of low_aspect_ratio_DEMO.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other. n = 76 (evaluation-phase runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0p.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 76 run(s) of low_aspect_ratio_DEMO.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other.*
| arm | ok | calls_per_eval | calls_bracket | sweeps_per_eval | sweeps_by_block | arrangement_method_calls | paired_seeds | pooled | median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 19/19 | 67.4211 | [42, 105] | 3.21053 | — | 0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 1.05172 | 1 | 4 |
| A0 | 19/19 | 68.5263 | [42, 105] | 3.26316 | FLAT 62 | 0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 1.06897 | 1 | 4 |
| A0p | 19/19 | 64.1053 | [42, 84] | 3.05263 | FLAT 58 | 0 | — | — | — | — |
| A1 | 19/19 | 42.3684 | [33, 55] | 7.84211 | FF 0, M1 36, M2 46, M3 48, PULSE 0 | 7.84211 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 0.66092 | 0.714286 | 0 |
*n = 76 (evaluation-phase runs of low_aspect_ratio_DEMO).*

**`cost per call — low_aspect_ratio_DEMO — campaign_stencil_forward`**

*Caption: units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0p.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 76 run(s) of low_aspect_ratio_DEMO.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other. n = 76 (evaluation-phase runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0p.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 76 run(s) of low_aspect_ratio_DEMO.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other.*
| arm | ok | calls_per_eval | calls_bracket | sweeps_per_eval | sweeps_by_block | arrangement_method_calls | paired_seeds | pooled | median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 19/19 | 67.4211 | [42, 105] | 3.21053 | — | 0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 1.07018 | 1 | 4 |
| A0 | 19/19 | 66.3158 | [42, 105] | 3.15789 | FLAT 60 | 0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 1.05263 | 1 | 3 |
| A0p | 19/19 | 63 | [42, 84] | 3 | FLAT 57 | 0 | — | — | — | — |
| A1 | 19/19 | 40.3158 | [33, 55] | 7.63158 | FF 0, M1 36, M2 45, M3 45, PULSE 0 | 7.63158 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 0.639933 | 0.607143 | 0 |
*n = 76 (evaluation-phase runs of low_aspect_ratio_DEMO).*

**`cost per call — st_regression — campaign_displaced`**

*Caption: units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 75 run(s) of st_regression.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other. n = 75 (evaluation-phase runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 75 run(s) of st_regression.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other.*
| arm | ok | calls_per_eval | calls_bracket | sweeps_per_eval | sweeps_by_block | arrangement_method_calls | paired_seeds | pooled | median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 25/25 | 103.32 | [84, 105] | 4.92 | — | 0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.842466 | 0.833333 | 0 |
| A0 | 25/25 | 122.64 | [105, 126] | 5.84 | FLAT 146 | 0 | — | — | — | — |
| A1 | 25/25 | 61.52 | [59, 62] | 14.84 | FF 0, M1 100, M2 146, M3 75, PULSE 25 | 14.84 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.501631 | 0.492063 | 0 |
*n = 75 (evaluation-phase runs of st_regression).*

**`cost per call — st_regression — campaign_entry_references`**

*Caption: units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; 1 run(s) of st_regression.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other. n = 1 (evaluation-phase runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; 1 run(s) of st_regression.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other.*
| arm | ok | calls_per_eval | calls_bracket | sweeps_per_eval | sweeps_by_block | arrangement_method_calls | paired_seeds | pooled | median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 1/1 | 147 | [147, 147] | 7 | FLAT 7 | 0 | — | — | — | — |
*n = 1 (evaluation-phase runs of st_regression).*

**`cost per call — st_regression — campaign_stencil_backward`**

*Caption: units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 42 run(s) of st_regression.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other. n = 42 (evaluation-phase runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 42 run(s) of st_regression.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other.*
| arm | ok | calls_per_eval | calls_bracket | sweeps_per_eval | sweeps_by_block | arrangement_method_calls | paired_seeds | pooled | median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 14/14 | 66 | [42, 84] | 3.14286 | — | 0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | 0.93617 | 1 | 0 |
| A0 | 14/14 | 70.5 | [42, 105] | 3.35714 | FLAT 47 | 0 | — | — | — | — |
| A1 | 14/14 | 39.3571 | [19, 53] | 8.78571 | FF 0, M1 31, M2 31, M3 33, PULSE 14 | 8.78571 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | 0.558257 | 0.52381 | 0 |
*n = 42 (evaluation-phase runs of st_regression).*

**`cost per call — st_regression — campaign_stencil_forward`**

*Caption: units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 42 run(s) of st_regression.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other. n = 42 (evaluation-phase runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 42 run(s) of st_regression.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other.*
| arm | ok | calls_per_eval | calls_bracket | sweeps_per_eval | sweeps_by_block | arrangement_method_calls | paired_seeds | pooled | median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 14/14 | 63 | [42, 84] | 3 | — | 0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | 0.933333 | 1 | 0 |
| A0 | 14/14 | 67.5 | [42, 84] | 3.21429 | FLAT 45 | 0 | — | — | — | — |
| A1 | 14/14 | 38.9286 | [19, 50] | 8.64286 | FF 0, M1 31, M2 29, M3 33, PULSE 14 | 8.64286 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | 0.57672 | 0.571429 | 0 |
*n = 42 (evaluation-phase runs of st_regression).*

**`failure taxonomy — large_tokamak_nof — campaign_displaced`**

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; every run of large_tokamak_nof.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 100 (evaluation-phase runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; every run of large_tokamak_nof.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell.*
| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| AR | 25 | 25 | yes | — |
| A0 | 25 | 25 | yes | — |
| A0p | 25 | 25 | yes | — |
| A1 | 25 | 25 | yes | — |
*n = 100 (evaluation-phase runs of large_tokamak_nof).*

**`failure taxonomy — large_tokamak_nof — campaign_entry_references`**

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; every run of large_tokamak_nof.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 1 (evaluation-phase runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; every run of large_tokamak_nof.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell.*
| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| A0 | 1 | 1 | yes | — |
*n = 1 (evaluation-phase runs of large_tokamak_nof).*

**`failure taxonomy — large_tokamak_nof — campaign_optimisation`**

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; every run of large_tokamak_nof.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 100 (optimisation-phase runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; every run of large_tokamak_nof.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell.*
| arm | denominator | crashed | ok | sums | detail |
|---|---|---|---|---|---|
| BR | 25 | 3 | 22 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×3 |
| B0 | 25 | 3 | 22 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×3 |
| B1 | 25 | 3 | 22 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×3 |
| B3 | 25 | 3 | 22 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×3 |
*n = 100 (optimisation-phase runs of large_tokamak_nof).*

**`failure taxonomy — large_tokamak_nof — campaign_stencil_backward`**

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; every run of large_tokamak_nof.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 80 (evaluation-phase runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; every run of large_tokamak_nof.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell.*
| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| AR | 20 | 20 | yes | — |
| A0 | 20 | 20 | yes | — |
| A0p | 20 | 20 | yes | — |
| A1 | 20 | 20 | yes | — |
*n = 80 (evaluation-phase runs of large_tokamak_nof).*

**`failure taxonomy — large_tokamak_nof — campaign_stencil_forward`**

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; every run of large_tokamak_nof.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 80 (evaluation-phase runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; every run of large_tokamak_nof.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell.*
| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| AR | 20 | 20 | yes | — |
| A0 | 20 | 20 | yes | — |
| A0p | 20 | 20 | yes | — |
| A1 | 20 | 20 | yes | — |
*n = 80 (evaluation-phase runs of large_tokamak_nof).*

**`failure taxonomy — low_aspect_ratio_DEMO — campaign_displaced`**

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; every run of low_aspect_ratio_DEMO.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 100 (evaluation-phase runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; every run of low_aspect_ratio_DEMO.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell.*
| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| AR | 25 | 25 | yes | — |
| A0 | 25 | 25 | yes | — |
| A0p | 25 | 25 | yes | — |
| A1 | 25 | 25 | yes | — |
*n = 100 (evaluation-phase runs of low_aspect_ratio_DEMO).*

**`failure taxonomy — low_aspect_ratio_DEMO — campaign_entry_references`**

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; every run of low_aspect_ratio_DEMO.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 1 (evaluation-phase runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; every run of low_aspect_ratio_DEMO.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell.*
| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| A0 | 1 | 1 | yes | — |
*n = 1 (evaluation-phase runs of low_aspect_ratio_DEMO).*

**`failure taxonomy — low_aspect_ratio_DEMO — campaign_optimisation`**

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; every run of low_aspect_ratio_DEMO.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 100 (optimisation-phase runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; every run of low_aspect_ratio_DEMO.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell.*
| arm | denominator | crashed | ok | unconverged | sums | detail |
|---|---|---|---|---|---|---|
| BR | 25 | 2 | 23 | 0 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×2 |
| B0 | 25 | 2 | 21 | 2 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×2; process.core.solver.module_solve.ModuleSolveFailure: block FLAT did not converge in 20 sweeps at tau=1e-06; max scaled residual inf on current_drive.eta_cd_dimensionless_hcd_primary, 1 components above tau ×2 |
| B1 | 25 | 2 | 20 | 3 | yes | process.core.solver.module_solve.ModuleSolveFailure: block FLAT did not converge in 20 sweeps at tau=1e-06; max scaled residual inf on current_drive.eta_cd_dimensionless_hcd_primary, 1 components above tau ×3; RuntimeError: Failed to converge after 50 iterations, value is nan. ×2 |
| B3 | 25 | 2 | 20 | 3 | yes | process.core.solver.module_solve.ModuleSolveFailure: block M1 did not converge in 20 sweeps at tau=1e-06; max scaled residual inf on current_drive.eta_cd_dimensionless_hcd_primary, 1 components above tau ×3; RuntimeError: Failed to converge after 50 iterations, value is nan. ×2 |
*n = 100 (optimisation-phase runs of low_aspect_ratio_DEMO).*

**`failure taxonomy — low_aspect_ratio_DEMO — campaign_stencil_backward`**

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; every run of low_aspect_ratio_DEMO.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 76 (evaluation-phase runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; every run of low_aspect_ratio_DEMO.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell.*
| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| AR | 19 | 19 | yes | — |
| A0 | 19 | 19 | yes | — |
| A0p | 19 | 19 | yes | — |
| A1 | 19 | 19 | yes | — |
*n = 76 (evaluation-phase runs of low_aspect_ratio_DEMO).*

**`failure taxonomy — low_aspect_ratio_DEMO — campaign_stencil_forward`**

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; every run of low_aspect_ratio_DEMO.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 76 (evaluation-phase runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; every run of low_aspect_ratio_DEMO.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell.*
| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| AR | 19 | 19 | yes | — |
| A0 | 19 | 19 | yes | — |
| A0p | 19 | 19 | yes | — |
| A1 | 19 | 19 | yes | — |
*n = 76 (evaluation-phase runs of low_aspect_ratio_DEMO).*

**`failure taxonomy — st_regression — campaign_displaced`**

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; every run of st_regression.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 75 (evaluation-phase runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; every run of st_regression.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell.*
| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| AR | 25 | 25 | yes | — |
| A0 | 25 | 25 | yes | — |
| A1 | 25 | 25 | yes | — |
*n = 75 (evaluation-phase runs of st_regression).*

**`failure taxonomy — st_regression — campaign_entry_references`**

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; every run of st_regression.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 1 (evaluation-phase runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; every run of st_regression.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell.*
| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| A0 | 1 | 1 | yes | — |
*n = 1 (evaluation-phase runs of st_regression).*

**`failure taxonomy — st_regression — campaign_optimisation`**

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; every run of st_regression.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 75 (optimisation-phase runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; every run of st_regression.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell.*
| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| BR | 25 | 25 | yes | — |
| B0 | 25 | 25 | yes | — |
| B3 | 25 | 25 | yes | — |
*n = 75 (optimisation-phase runs of st_regression).*

**`failure taxonomy — st_regression — campaign_stencil_backward`**

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; every run of st_regression.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 42 (evaluation-phase runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; every run of st_regression.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell.*
| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| AR | 14 | 14 | yes | — |
| A0 | 14 | 14 | yes | — |
| A1 | 14 | 14 | yes | — |
*n = 42 (evaluation-phase runs of st_regression).*

**`failure taxonomy — st_regression — campaign_stencil_forward`**

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; every run of st_regression.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 42 (evaluation-phase runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; every run of st_regression.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell.*
| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| AR | 14 | 14 | yes | — |
| A0 | 14 | 14 | yes | — |
| A1 | 14 | 14 | yes | — |
*n = 42 (evaluation-phase runs of st_regression).*

**`iteration multiplier (check 2) — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: dimensionless ratios of counts.  A row is one arm against the flat control over the seed set.  A column is one of check 2's two iteration constructions, its sum ratio, or the evaluation-count ratio beside them.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 22 seed(s) on which every arm of large_tokamak_nof reached an accepted optimum.  Construction: iterations summed over attempts[] is the declared acceptance statistic, nearest-rank upper-middle median against 1.05; the final attempt's count is the previous revision's construction, published beside.  Both are read from attempts[], so a disagreement between them is a disagreement about that list.  The sum ratio is beside every median because the two can point in opposite directions. n = 22 (seeds on which every arm of large_tokamak_nof converged). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless ratios of counts.  A row is one arm against the flat control over the seed set.  A column is one of check 2's two iteration constructions, its sum ratio, or the evaluation-count ratio beside them.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 22 seed(s) on which every arm of large_tokamak_nof reached an accepted optimum.  Construction: iterations summed over attempts[] is the declared acceptance statistic, nearest-rank upper-middle median against 1.05; the final attempt's count is the previous revision's construction, published beside.  Both are read from attempts[], so a disagreement between them is a disagreement about that list.  The sum ratio is beside every median because the two can point in opposite directions.*
| pair | n | summed_median | summed_sum_ratio | acceptance | final_median | final_sum_ratio | evaluations_median | attempts | constructions_disagree |
|---|---|---|---|---|---|---|---|---|---|
| B0 → BR (beside) | 22 | 1 | 1 | beside | 1 | 1 | 0.979456 | 0:1/1, 1:1/1, 2:1/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 10:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 17:1/1, 18:1/1, 19:1/1, 22:1/1, 23:1/1, 24:1/1 | 0 |
| B0 → B1 | 22 | 1 | 0.994186 | PASS | 1 | 0.994186 | 1.01391 | 0:1/1, 1:1/1, 2:1/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 10:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 17:1/1, 18:1/1, 19:1/1, 22:1/1, 23:1/1, 24:1/1 | 0 |
| B0 → B3 | 22 | 1 | 0.994186 | PASS | 1 | 0.994186 | 2.65239 | 0:1/1, 1:1/1, 2:1/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 10:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 17:1/1, 18:1/1, 19:1/1, 22:1/1, 23:1/1, 24:1/1 | 0 |
*n = 22 (seeds on which every arm of large_tokamak_nof converged).*

**`iteration multiplier (check 2) — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: dimensionless ratios of counts.  A row is one arm against the flat control over the seed set.  A column is one of check 2's two iteration constructions, its sum ratio, or the evaluation-count ratio beside them.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 11 seed(s) on which every arm of low_aspect_ratio_DEMO reached an accepted optimum.  Construction: iterations summed over attempts[] is the declared acceptance statistic, nearest-rank upper-middle median against 1.05; the final attempt's count is the previous revision's construction, published beside.  Both are read from attempts[], so a disagreement between them is a disagreement about that list.  The sum ratio is beside every median because the two can point in opposite directions. n = 11 (seeds on which every arm of low_aspect_ratio_DEMO converged). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless ratios of counts.  A row is one arm against the flat control over the seed set.  A column is one of check 2's two iteration constructions, its sum ratio, or the evaluation-count ratio beside them.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 11 seed(s) on which every arm of low_aspect_ratio_DEMO reached an accepted optimum.  Construction: iterations summed over attempts[] is the declared acceptance statistic, nearest-rank upper-middle median against 1.05; the final attempt's count is the previous revision's construction, published beside.  Both are read from attempts[], so a disagreement between them is a disagreement about that list.  The sum ratio is beside every median because the two can point in opposite directions.*
| pair | n | summed_median | summed_sum_ratio | acceptance | final_median | final_sum_ratio | evaluations_median | attempts | constructions_disagree |
|---|---|---|---|---|---|---|---|---|---|
| B0 → BR (beside) | 11 | 1 | 1 | beside | 1 | 1 | 1.03515 | 0:1/1, 1:2/2, 5:1/1, 6:1/1, 9:1/1, 11:1/1, 12:1/1, 13:1/1, 15:1/1, 18:1/1, 19:1/1 | 1 |
| B0 → B1 | 11 | 0.8125 | 0.70122 | PASS | 0.833333 | 1.00877 | 0.804589 | 0:1/1, 1:2/1, 5:1/1, 6:1/1, 9:1/1, 11:1/1, 12:1/1, 13:1/1, 15:1/1, 18:1/1, 19:1/1 | 1 |
| B0 → B3 | 11 | 0.8125 | 0.70122 | PASS | 0.833333 | 1.00877 | 2.11691 | 0:1/1, 1:2/1, 5:1/1, 6:1/1, 9:1/1, 11:1/1, 12:1/1, 13:1/1, 15:1/1, 18:1/1, 19:1/1 | 1 |
*n = 11 (seeds on which every arm of low_aspect_ratio_DEMO converged).*

**`iteration multiplier (check 2) — st_regression — campaign_optimisation · BR·B0·B3`**

*Caption: units: dimensionless ratios of counts.  A row is one arm against the flat control over the seed set.  A column is one of check 2's two iteration constructions, its sum ratio, or the evaluation-count ratio beside them.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 22 seed(s) on which every arm of st_regression reached an accepted optimum.  Construction: iterations summed over attempts[] is the declared acceptance statistic, nearest-rank upper-middle median against 1.05; the final attempt's count is the previous revision's construction, published beside.  Both are read from attempts[], so a disagreement between them is a disagreement about that list.  The sum ratio is beside every median because the two can point in opposite directions. n = 22 (seeds on which every arm of st_regression converged). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless ratios of counts.  A row is one arm against the flat control over the seed set.  A column is one of check 2's two iteration constructions, its sum ratio, or the evaluation-count ratio beside them.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 22 seed(s) on which every arm of st_regression reached an accepted optimum.  Construction: iterations summed over attempts[] is the declared acceptance statistic, nearest-rank upper-middle median against 1.05; the final attempt's count is the previous revision's construction, published beside.  Both are read from attempts[], so a disagreement between them is a disagreement about that list.  The sum ratio is beside every median because the two can point in opposite directions.*
| pair | n | summed_median | summed_sum_ratio | acceptance | final_median | final_sum_ratio | evaluations_median | attempts | constructions_disagree |
|---|---|---|---|---|---|---|---|---|---|
| B0 → BR (beside) | 22 | 1 | 1.24051 | beside | 1 | 0.922053 | 0.990635 | 0:1/1, 1:1/1, 2:2/2, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 11:1/1, 12:1/2, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 18:1/1, 19:1/1, 20:1/1, 21:1/1, 22:1/1, 23:1/1, 24:1/3 | 3 |
| B0 → B3 | 22 | 1 | 0.952984 | PASS | 1 | 1.0019 | 2.77666 | 0:1/1, 1:1/1, 2:2/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 18:1/1, 19:1/1, 20:1/1, 21:1/1, 22:1/1, 23:1/1, 24:1/1 | 1 |
*n = 22 (seeds on which every arm of st_regression converged).*

**`matched accuracy — large_tokamak_nof — campaign_displaced`**

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 100 run(s) of large_tokamak_nof.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither. n = 100 (evaluation-phase runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 100 run(s) of large_tokamak_nof.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither.*
| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_p90 | argmax | whole_median | whole_p90 | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 25 | 25 | 2.62424e-08 | 1.542e-07 | blanket.deg_blkt_inboard_poloidal_plasma, heat_transport.tlvpmw, power.qac | 3.25488e-08 | 4.14213e-07 | 122 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 25 | 25 | 1.50054e-08 | 8.37157e-08 | blanket.deg_blkt_inboard_poloidal_plasma, heat_transport.tlvpmw, power.qac | 1.50054e-08 | 8.37157e-08 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 25 | 25 | 5.04239e-10 | 2.9629e-09 | blanket.deg_blkt_inboard_poloidal_plasma, power.qac | 6.25411e-10 | 7.95902e-09 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 25 | 25 | 2.88323e-10 | 1.60857e-09 | blanket.deg_blkt_inboard_poloidal_plasma, power.qac | 2.88323e-10 | 1.60857e-09 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0p | frozen | 25 | 25 | 3.83344e-10 | 1.67131e-08 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.stress_z_cs_self_midplane_profile | 3.83344e-10 | 1.67131e-08 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0p | mixed | 25 | 25 | 3.83344e-10 | 1.67131e-08 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.stress_z_cs_self_midplane_profile | 3.83344e-10 | 1.67131e-08 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 25 | 25 | 3.83344e-10 | 1.67131e-08 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.stress_z_cs_self_midplane_profile | 2.43528 | 9.85963 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A1 | mixed | 25 | 25 | 3.83344e-10 | 1.67131e-08 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.stress_z_cs_self_midplane_profile | 0.39768 | 0.616996 | 122 | after_single_evaluation | no snapshot recorded on this record |
*n = 100 (evaluation-phase runs of large_tokamak_nof).*

**`matched accuracy — large_tokamak_nof — campaign_entry_references`**

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; 1 run(s) of large_tokamak_nof.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither. n = 1 (evaluation-phase runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; 1 run(s) of large_tokamak_nof.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither.*
| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_p90 | argmax | whole_median | whole_p90 | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | frozen | 1 | 1 | 8.09171e-09 | 8.09171e-09 | power.qac | 1.46505e-08 | 1.46505e-08 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 1 | 1 | 4.52872e-09 | 4.52872e-09 | power.qac | 4.52872e-09 | 4.52872e-09 | 122 | after_single_evaluation | no snapshot recorded on this record |
*n = 1 (evaluation-phase runs of large_tokamak_nof).*

**`matched accuracy — large_tokamak_nof — campaign_stencil_backward`**

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 80 run(s) of large_tokamak_nof.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither. n = 80 (evaluation-phase runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 80 run(s) of large_tokamak_nof.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither.*
| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_p90 | argmax | whole_median | whole_p90 | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 20 | 20 | 5.33878e-15 | 1.72982e-10 | blanket.deg_blkt_inboard_poloidal_plasma, heat_transport.tlvpmw, power.qac | 5.33878e-15 | 1.72982e-10 | 122 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 20 | 20 | 2.98798e-15 | 1.72982e-10 | blanket.deg_blkt_inboard_poloidal_plasma, heat_transport.tlvpmw, power.qac | 2.98798e-15 | 1.72982e-10 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 20 | 20 | 0 | 5.33878e-15 | blanket.deg_blkt_inboard_poloidal_plasma, power.qac | 0 | 1.14372e-14 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 20 | 20 | 0 | 2.98798e-15 | blanket.deg_blkt_inboard_poloidal_plasma, power.qac | 0 | 2.98798e-15 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0p | frozen | 20 | 20 | 0 | 8.30864e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top, pf_coil.stress_z_cs_self_midplane_profile | 0 | 8.30864e-16 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0p | mixed | 20 | 20 | 0 | 8.30864e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.bpf2, pf_coil.stress_z_cs_self_midplane_profile | 0 | 8.30864e-16 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 20 | 20 | 8.30864e-16 | 4.52263e-13 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top, pf_coil.stress_z_cs_self_midplane_profile | 0.00201638 | 0.0697524 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A1 | mixed | 20 | 20 | 8.30864e-16 | 4.52263e-13 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.bpf2, pf_coil.stress_z_cs_self_midplane_profile | 0.00182634 | 0.0107935 | 122 | after_single_evaluation | no snapshot recorded on this record |
*n = 80 (evaluation-phase runs of large_tokamak_nof).*

**`matched accuracy — large_tokamak_nof — campaign_stencil_forward`**

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 80 run(s) of large_tokamak_nof.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither. n = 80 (evaluation-phase runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 80 run(s) of large_tokamak_nof.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither.*
| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_p90 | argmax | whole_median | whole_p90 | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 20 | 20 | 2.97398e-12 | 1.86926e-08 | power.qac | 5.34367e-12 | 3.38483e-08 | 122 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 20 | 20 | 1.66446e-12 | 1.04618e-08 | power.qac | 1.66446e-12 | 1.04618e-08 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 20 | 20 | 2.97398e-12 | 3.59169e-10 | power.qac | 5.34367e-12 | 6.50359e-10 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 20 | 20 | 1.66446e-12 | 2.01018e-10 | power.qac | 1.66446e-12 | 2.01018e-10 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0p | frozen | 20 | 20 | 4.52263e-13 | 2.78324e-09 | pf_coil.f_j_cs_start_end_flat_top, pf_coil.stress_z_cs_self_midplane_profile | 4.52263e-13 | 2.78324e-09 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0p | mixed | 20 | 20 | 4.52263e-13 | 2.78324e-09 | pf_coil.f_j_cs_start_end_flat_top, pf_coil.stress_z_cs_self_midplane_profile | 4.52263e-13 | 2.78324e-09 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 20 | 20 | 2.36272e-11 | 2.78324e-09 | pf_coil.f_j_cs_start_end_flat_top, pf_coil.stress_z_cs_self_midplane_profile | 0.00201638 | 0.0711547 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A1 | mixed | 20 | 20 | 2.36272e-11 | 2.78324e-09 | pf_coil.f_j_cs_start_end_flat_top, pf_coil.stress_z_cs_self_midplane_profile | 0.00182707 | 0.0107756 | 122 | after_single_evaluation | no snapshot recorded on this record |
*n = 80 (evaluation-phase runs of large_tokamak_nof).*

**`matched accuracy — low_aspect_ratio_DEMO — campaign_displaced`**

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 100 run(s) of low_aspect_ratio_DEMO.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither. n = 100 (evaluation-phase runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 100 run(s) of low_aspect_ratio_DEMO.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither.*
| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_p90 | argmax | whole_median | whole_p90 | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 25 | 25 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 25 | 25 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 25 | 25 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 25 | 25 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0p | frozen | 25 | 25 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0p | mixed | 25 | 25 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 25 | 25 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0.181599 | 0.287845 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | mixed | 25 | 25 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0.168677 | 0.242 | 123 | after_single_evaluation | no snapshot recorded on this record |
*n = 100 (evaluation-phase runs of low_aspect_ratio_DEMO).*

**`matched accuracy — low_aspect_ratio_DEMO — campaign_entry_references`**

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; 1 run(s) of low_aspect_ratio_DEMO.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither. n = 1 (evaluation-phase runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; 1 run(s) of low_aspect_ratio_DEMO.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither.*
| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_p90 | argmax | whole_median | whole_p90 | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | frozen | 1 | 1 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 1 | 1 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
*n = 1 (evaluation-phase runs of low_aspect_ratio_DEMO).*

**`matched accuracy — low_aspect_ratio_DEMO — campaign_stencil_backward`**

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 76 run(s) of low_aspect_ratio_DEMO.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither. n = 76 (evaluation-phase runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 76 run(s) of low_aspect_ratio_DEMO.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither.*
| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_p90 | argmax | whole_median | whole_p90 | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0p | frozen | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0p | mixed | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.stress_z_cs_self_midplane_profile | 0.00150908 | 0.00837004 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | mixed | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.stress_z_cs_self_midplane_profile | 0.00146758 | 0.00837004 | 123 | after_single_evaluation | no snapshot recorded on this record |
*n = 76 (evaluation-phase runs of low_aspect_ratio_DEMO).*

**`matched accuracy — low_aspect_ratio_DEMO — campaign_stencil_forward`**

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 76 run(s) of low_aspect_ratio_DEMO.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither. n = 76 (evaluation-phase runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 76 run(s) of low_aspect_ratio_DEMO.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither.*
| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_p90 | argmax | whole_median | whole_p90 | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma, heat_transport.tlvpmw | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma, heat_transport.tlvpmw | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0p | frozen | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0p | mixed | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0.00150362 | 0.00758377 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | mixed | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0.00147063 | 0.00758377 | 123 | after_single_evaluation | no snapshot recorded on this record |
*n = 76 (evaluation-phase runs of low_aspect_ratio_DEMO).*

**`matched accuracy — st_regression — campaign_displaced`**

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 75 run(s) of st_regression.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither. n = 75 (evaluation-phase runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 75 run(s) of st_regression.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither.*
| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_p90 | argmax | whole_median | whole_p90 | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 25 | 25 | 1.53939e-07 | 2.79264e-07 | superconducting_tfcoil.a_tf_plasma_case | 1.53939e-07 | 2.79264e-07 | 123 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 25 | 25 | 1.0743e-07 | 1.94891e-07 | superconducting_tfcoil.a_tf_plasma_case | 1.0743e-07 | 1.94891e-07 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 25 | 25 | 5.37197e-09 | 2.02343e-08 | superconducting_tfcoil.a_tf_plasma_case | 5.37197e-09 | 2.02343e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 25 | 25 | 3.74896e-09 | 1.4121e-08 | superconducting_tfcoil.a_tf_plasma_case | 3.74896e-09 | 1.4121e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 25 | 25 | 5.37197e-09 | 2.02343e-08 | superconducting_tfcoil.a_tf_plasma_case | 0.257542 | 0.337422 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | mixed | 25 | 25 | 3.74896e-09 | 1.4121e-08 | superconducting_tfcoil.a_tf_plasma_case | 0.134306 | 0.181027 | 123 | after_single_evaluation | no snapshot recorded on this record |
*n = 75 (evaluation-phase runs of st_regression).*

**`matched accuracy — st_regression — campaign_entry_references`**

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; 1 run(s) of st_regression.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither. n = 1 (evaluation-phase runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; 1 run(s) of st_regression.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither.*
| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_p90 | argmax | whole_median | whole_p90 | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | frozen | 1 | 1 | 3.27554e-09 | 3.27554e-09 | superconducting_tfcoil.a_tf_plasma_case | 3.27554e-09 | 3.27554e-09 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 1 | 1 | 2.28591e-09 | 2.28591e-09 | superconducting_tfcoil.a_tf_plasma_case | 2.28591e-09 | 2.28591e-09 | 123 | after_single_evaluation | no snapshot recorded on this record |
*n = 1 (evaluation-phase runs of st_regression).*

**`matched accuracy — st_regression — campaign_stencil_backward`**

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 42 run(s) of st_regression.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither. n = 42 (evaluation-phase runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 42 run(s) of st_regression.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither.*
| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_p90 | argmax | whole_median | whole_p90 | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 14 | 14 | 6.45896e-14 | 4.27221e-08 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 6.45896e-14 | 4.27221e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 14 | 14 | 6.45896e-14 | 2.98301e-08 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 6.45896e-14 | 2.98301e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 14 | 14 | 0 | 2.67039e-08 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.radius_beam_tangency_max, superconducting_tfcoil.a_tf_plasma_case | 0 | 2.67039e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 14 | 14 | 0 | 1.8642e-08 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.radius_beam_tangency_max, superconducting_tfcoil.a_tf_plasma_case | 0 | 1.8642e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 14 | 14 | 1.55986e-11 | 2.67039e-08 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 0.00175996 | 0.00598788 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | mixed | 14 | 14 | 5.91923e-12 | 1.8642e-08 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 0.00102212 | 0.00257926 | 123 | after_single_evaluation | no snapshot recorded on this record |
*n = 42 (evaluation-phase runs of st_regression).*

**`matched accuracy — st_regression — campaign_stencil_forward`**

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 42 run(s) of st_regression.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither. n = 42 (evaluation-phase runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 42 run(s) of st_regression.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither.*
| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_p90 | argmax | whole_median | whole_p90 | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 14 | 14 | 3.77932e-11 | 3.91977e-07 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 3.77932e-11 | 3.91977e-07 | 123 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 14 | 14 | 1.4342e-11 | 2.73462e-07 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 1.4342e-11 | 2.73462e-07 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 14 | 14 | 3.77932e-11 | 2.13721e-08 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 3.77932e-11 | 2.13721e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 14 | 14 | 1.4342e-11 | 1.49073e-08 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 1.4342e-11 | 1.49073e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 14 | 14 | 1.11615e-10 | 2.13721e-08 | fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 0.00176096 | 0.00596933 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | mixed | 14 | 14 | 7.78935e-11 | 1.49073e-08 | fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 0.00102062 | 0.00256932 | 123 | after_single_evaluation | no snapshot recorded on this record |
*n = 42 (evaluation-phase runs of st_regression).*

**`ownership rung A0 → A0p — large_tokamak_nof — campaign_displaced`**

*Caption: units: the node-call ratio is dimensionless; the burn-time residual is in seconds and relative to the burn time.  A row is this configuration's rung.  A column is the cost of taking the burn time out of the flat loop, or the inconsistency the constant leaves behind.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 25 flat-control and 25 pinned run(s) of large_tokamak_nof.  Construction: the ratio triple on node calls of the single evaluation; the residual is the lifted component's own inconsistency at exit, |value|, median nearest-rank upper-middle.  Neither column is a claim about the partition: this rung moves one thing only. n = 50 (A0 and A0p runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: the node-call ratio is dimensionless; the burn-time residual is in seconds and relative to the burn time.  A row is this configuration's rung.  A column is the cost of taking the burn time out of the flat loop, or the inconsistency the constant leaves behind.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 25 flat-control and 25 pinned run(s) of large_tokamak_nof.  Construction: the ratio triple on node calls of the single evaluation; the residual is the lifted component's own inconsistency at exit, |value|, median nearest-rank upper-middle.  Neither column is a claim about the partition: this rung moves one thing only.*
| n | paired_seeds | pooled | median | worse | residual_s_median | residual_s_bracket | relative_median |
|---|---|---|---|---|---|---|---|
| 25 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.927536 | 1 | 0 | 154.633 | [12.8111, 406.884] | 0.062979 |
*n = 50 (A0 and A0p runs of large_tokamak_nof).*

**`ownership rung A0 → A0p — large_tokamak_nof — campaign_stencil_backward`**

*Caption: units: the node-call ratio is dimensionless; the burn-time residual is in seconds and relative to the burn time.  A row is this configuration's rung.  A column is the cost of taking the burn time out of the flat loop, or the inconsistency the constant leaves behind.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 20 flat-control and 20 pinned run(s) of large_tokamak_nof.  Construction: the ratio triple on node calls of the single evaluation; the residual is the lifted component's own inconsistency at exit, |value|, median nearest-rank upper-middle.  Neither column is a claim about the partition: this rung moves one thing only. n = 40 (A0 and A0p runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: the node-call ratio is dimensionless; the burn-time residual is in seconds and relative to the burn time.  A row is this configuration's rung.  A column is the cost of taking the burn time out of the flat loop, or the inconsistency the constant leaves behind.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 20 flat-control and 20 pinned run(s) of large_tokamak_nof.  Construction: the ratio triple on node calls of the single evaluation; the residual is the lifted component's own inconsistency at exit, |value|, median nearest-rank upper-middle.  Neither column is a claim about the partition: this rung moves one thing only.*
| n | paired_seeds | pooled | median | worse | residual_s_median | residual_s_bracket | relative_median |
|---|---|---|---|---|---|---|---|
| 20 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 0.952381 | 1 | 0 | 1.17471 | [2.61418e-07, 13.1158] | 0.000457418 |
*n = 40 (A0 and A0p runs of large_tokamak_nof).*

**`ownership rung A0 → A0p — large_tokamak_nof — campaign_stencil_forward`**

*Caption: units: the node-call ratio is dimensionless; the burn-time residual is in seconds and relative to the burn time.  A row is this configuration's rung.  A column is the cost of taking the burn time out of the flat loop, or the inconsistency the constant leaves behind.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 20 flat-control and 20 pinned run(s) of large_tokamak_nof.  Construction: the ratio triple on node calls of the single evaluation; the residual is the lifted component's own inconsistency at exit, |value|, median nearest-rank upper-middle.  Neither column is a claim about the partition: this rung moves one thing only. n = 40 (A0 and A0p runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: the node-call ratio is dimensionless; the burn-time residual is in seconds and relative to the burn time.  A row is this configuration's rung.  A column is the cost of taking the burn time out of the flat loop, or the inconsistency the constant leaves behind.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 20 flat-control and 20 pinned run(s) of large_tokamak_nof.  Construction: the ratio triple on node calls of the single evaluation; the residual is the lifted component's own inconsistency at exit, |value|, median nearest-rank upper-middle.  Neither column is a claim about the partition: this rung moves one thing only.*
| n | paired_seeds | pooled | median | worse | residual_s_median | residual_s_bracket | relative_median |
|---|---|---|---|---|---|---|---|
| 20 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 0.952381 | 1 | 0 | 1.17254 | [2.61319e-07, 13.1365] | 0.000456574 |
*n = 40 (A0 and A0p runs of large_tokamak_nof).*

**`ownership rung A0 → A0p — low_aspect_ratio_DEMO — campaign_displaced`**

*Caption: units: the node-call ratio is dimensionless; the burn-time residual is in seconds and relative to the burn time.  A row is this configuration's rung.  A column is the cost of taking the burn time out of the flat loop, or the inconsistency the constant leaves behind.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 25 flat-control and 25 pinned run(s) of low_aspect_ratio_DEMO.  Construction: the ratio triple on node calls of the single evaluation; the residual is the lifted component's own inconsistency at exit, |value|, median nearest-rank upper-middle.  Neither column is a claim about the partition: this rung moves one thing only. n = 50 (A0 and A0p runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: the node-call ratio is dimensionless; the burn-time residual is in seconds and relative to the burn time.  A row is this configuration's rung.  A column is the cost of taking the burn time out of the flat loop, or the inconsistency the constant leaves behind.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 25 flat-control and 25 pinned run(s) of low_aspect_ratio_DEMO.  Construction: the ratio triple on node calls of the single evaluation; the residual is the lifted component's own inconsistency at exit, |value|, median nearest-rank upper-middle.  Neither column is a claim about the partition: this rung moves one thing only.*
| n | paired_seeds | pooled | median | worse | residual_s_median | residual_s_bracket | relative_median |
|---|---|---|---|---|---|---|---|
| 25 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.984 | 1 | 0 | 525.842 | [1.64882, 1436.26] | 0.0527537 |
*n = 50 (A0 and A0p runs of low_aspect_ratio_DEMO).*

**`ownership rung A0 → A0p — low_aspect_ratio_DEMO — campaign_stencil_backward`**

*Caption: units: the node-call ratio is dimensionless; the burn-time residual is in seconds and relative to the burn time.  A row is this configuration's rung.  A column is the cost of taking the burn time out of the flat loop, or the inconsistency the constant leaves behind.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 19 flat-control and 19 pinned run(s) of low_aspect_ratio_DEMO.  Construction: the ratio triple on node calls of the single evaluation; the residual is the lifted component's own inconsistency at exit, |value|, median nearest-rank upper-middle.  Neither column is a claim about the partition: this rung moves one thing only. n = 38 (A0 and A0p runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: the node-call ratio is dimensionless; the burn-time residual is in seconds and relative to the burn time.  A row is this configuration's rung.  A column is the cost of taking the burn time out of the flat loop, or the inconsistency the constant leaves behind.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 19 flat-control and 19 pinned run(s) of low_aspect_ratio_DEMO.  Construction: the ratio triple on node calls of the single evaluation; the residual is the lifted component's own inconsistency at exit, |value|, median nearest-rank upper-middle.  Neither column is a claim about the partition: this rung moves one thing only.*
| n | paired_seeds | pooled | median | worse | residual_s_median | residual_s_bracket | relative_median |
|---|---|---|---|---|---|---|---|
| 19 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 0.935484 | 1 | 0 | 4.18366 | [0, 34.1746] | 0.000402376 |
*n = 38 (A0 and A0p runs of low_aspect_ratio_DEMO).*

**`ownership rung A0 → A0p — low_aspect_ratio_DEMO — campaign_stencil_forward`**

*Caption: units: the node-call ratio is dimensionless; the burn-time residual is in seconds and relative to the burn time.  A row is this configuration's rung.  A column is the cost of taking the burn time out of the flat loop, or the inconsistency the constant leaves behind.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 19 flat-control and 19 pinned run(s) of low_aspect_ratio_DEMO.  Construction: the ratio triple on node calls of the single evaluation; the residual is the lifted component's own inconsistency at exit, |value|, median nearest-rank upper-middle.  Neither column is a claim about the partition: this rung moves one thing only. n = 38 (A0 and A0p runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: the node-call ratio is dimensionless; the burn-time residual is in seconds and relative to the burn time.  A row is this configuration's rung.  A column is the cost of taking the burn time out of the flat loop, or the inconsistency the constant leaves behind.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 19 flat-control and 19 pinned run(s) of low_aspect_ratio_DEMO.  Construction: the ratio triple on node calls of the single evaluation; the residual is the lifted component's own inconsistency at exit, |value|, median nearest-rank upper-middle.  Neither column is a claim about the partition: this rung moves one thing only.*
| n | paired_seeds | pooled | median | worse | residual_s_median | residual_s_bracket | relative_median |
|---|---|---|---|---|---|---|---|
| 19 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 0.95 | 1 | 0 | 4.17586 | [0, 34.2015] | 0.000401626 |
*n = 38 (A0 and A0p runs of low_aspect_ratio_DEMO).*

**`per-sweep overhead — large_tokamak_nof — campaign_displaced`**

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; the finished evaluation-phase gate runs of large_tokamak_nof.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 100 (finished evaluation-phase runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; the finished evaluation-phase gate runs of large_tokamak_nof.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone.*
| arm | seed | stops_on | dispatch_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 1 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 2 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 3 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 4 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 5 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 6 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 7 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 8 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 9 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 10 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 11 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 12 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 13 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 14 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 15 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 16 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27 | 0 |
| AR | 17 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 18 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 19 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 20 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 21 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 22 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 23 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 24 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 25 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| A0 | 1 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 2 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 3 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 4 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 5 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 6 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 7 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 8 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 9 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 10 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 11 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 12 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 13 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 14 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 15 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 16 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 17 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 18 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 19 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 20 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 21 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 22 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 23 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 24 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 25 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 1 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 2 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 3 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 4 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 5 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 6 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 7 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 8 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 9 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 10 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 11 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 12 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 13 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 14 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 15 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 16 | coupling_state | 4 | 4 | 3360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 17 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 18 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 19 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 20 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 21 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 22 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 23 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 24 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 25 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 1 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 2 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 3 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 4 | coupling_state | 14 | 13 | 3135 | 241.154 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 5 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 6 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 7 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 8 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 9 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 10 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 11 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 12 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 13 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 14 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 15 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 16 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 17 | coupling_state | 14 | 13 | 3135 | 241.154 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 18 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 19 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 20 | coupling_state | 14 | 13 | 3135 | 241.154 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 21 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 22 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 23 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 24 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 25 | coupling_state | 14 | 13 | 3135 | 241.154 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
*n = 100 (finished evaluation-phase runs of large_tokamak_nof).*

**`per-sweep overhead — large_tokamak_nof — campaign_entry_references`**

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; the finished evaluation-phase gate runs of large_tokamak_nof.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 1 (finished evaluation-phase runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; the finished evaluation-phase gate runs of large_tokamak_nof.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone.*
| arm | seed | stops_on | dispatch_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 0 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
*n = 1 (finished evaluation-phase runs of large_tokamak_nof).*

**`per-sweep overhead — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished optimisation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the finished optimisation-phase gate runs of large_tokamak_nof.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 88 (finished optimisation-phase runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished optimisation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the finished optimisation-phase gate runs of large_tokamak_nof.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone.*
| arm | seed | stops_on | dispatch_sweeps | solve_sweeps | output_loop_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | 0 | upstream | 2029 | 2027 | 2 | 0 | 0 | — | — | 1397 | 37719 | 27 | 0 |
| BR | 1 | upstream | 2021 | 2019 | 2 | 0 | 0 | — | — | 1389 | 37503 | 27 | 0 |
| BR | 2 | upstream | 2279 | 2277 | 2 | 0 | 0 | — | — | 1563 | 42201 | 27 | 0 |
| BR | 3 | upstream | 1759 | 1757 | 2 | 0 | 0 | — | — | 1211 | 32697 | 27 | 0 |
| BR | 4 | upstream | 1761 | 1759 | 2 | 0 | 0 | — | — | 1213 | 32751 | 27 | 0 |
| BR | 6 | upstream | 2036 | 2034 | 2 | 0 | 0 | — | — | 1404 | 37908 | 27 | 0 |
| BR | 7 | upstream | 2032 | 2030 | 2 | 0 | 0 | — | — | 1400 | 37800 | 27 | 0 |
| BR | 8 | upstream | 2034 | 2032 | 2 | 0 | 0 | — | — | 1402 | 37854 | 27 | 0 |
| BR | 9 | upstream | 2026 | 2024 | 2 | 0 | 0 | — | — | 1394 | 37638 | 27 | 0 |
| BR | 10 | upstream | 1766 | 1764 | 2 | 0 | 0 | — | — | 1218 | 32886 | 27 | 0 |
| BR | 11 | upstream | 2005 | 2003 | 2 | 0 | 0 | — | — | 1373 | 37071 | 27 | 0 |
| BR | 12 | upstream | 2029 | 2027 | 2 | 0 | 0 | — | — | 1397 | 37719 | 27 | 0 |
| BR | 13 | upstream | 2021 | 2019 | 2 | 0 | 0 | — | — | 1389 | 37503 | 27 | 0 |
| BR | 14 | upstream | 2279 | 2277 | 2 | 0 | 0 | — | — | 1563 | 42201 | 27 | 0 |
| BR | 15 | upstream | 1758 | 1756 | 2 | 0 | 0 | — | — | 1210 | 32670 | 27 | 0 |
| BR | 16 | upstream | 1757 | 1755 | 2 | 0 | 0 | — | — | 1209 | 32643 | 27 | 0 |
| BR | 17 | upstream | 2027 | 2025 | 2 | 0 | 0 | — | — | 1395 | 37665 | 27 | 0 |
| BR | 18 | upstream | 2027 | 2025 | 2 | 0 | 0 | — | — | 1395 | 37665 | 27 | 0 |
| BR | 19 | upstream | 2030 | 2028 | 2 | 0 | 0 | — | — | 1398 | 37746 | 27 | 0 |
| BR | 22 | upstream | 1763 | 1761 | 2 | 0 | 0 | — | — | 1215 | 32805 | 27 | 0 |
| BR | 23 | upstream | 2032 | 2030 | 2 | 0 | 0 | — | — | 1400 | 37800 | 27 | 0 |
| BR | 24 | upstream | 2028 | 2026 | 2 | 0 | 0 | — | — | 1396 | 37692 | 27 | 0 |
| B0 | 0 | coupling_state | 2071 | 2069 | 2 | 2069 | 1737960 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 1 | coupling_state | 2073 | 2071 | 2 | 2071 | 1739640 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 2 | coupling_state | 2365 | 2363 | 2 | 2363 | 1984920 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 3 | coupling_state | 1797 | 1795 | 2 | 1795 | 1507800 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 4 | coupling_state | 1792 | 1790 | 2 | 1790 | 1503600 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 6 | coupling_state | 2071 | 2069 | 2 | 2069 | 1737960 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 7 | coupling_state | 2070 | 2068 | 2 | 2068 | 1737120 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 8 | coupling_state | 2070 | 2068 | 2 | 2068 | 1737120 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 9 | coupling_state | 2072 | 2070 | 2 | 2070 | 1738800 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 10 | coupling_state | 1792 | 1790 | 2 | 1790 | 1503600 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 11 | coupling_state | 2125 | 2123 | 2 | 2123 | 1783320 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 12 | coupling_state | 2070 | 2068 | 2 | 2068 | 1737120 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 13 | coupling_state | 2075 | 2073 | 2 | 2073 | 1741320 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 14 | coupling_state | 2395 | 2393 | 2 | 2393 | 2010120 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 15 | coupling_state | 1799 | 1797 | 2 | 1797 | 1509480 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 16 | coupling_state | 1796 | 1794 | 2 | 1794 | 1506960 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 17 | coupling_state | 2072 | 2070 | 2 | 2070 | 1738800 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 18 | coupling_state | 2065 | 2063 | 2 | 2063 | 1732920 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 19 | coupling_state | 2069 | 2067 | 2 | 2067 | 1736280 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 22 | coupling_state | 1800 | 1798 | 2 | 1798 | 1510320 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 23 | coupling_state | 2068 | 2066 | 2 | 2066 | 1735440 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 24 | coupling_state | 2077 | 2075 | 2 | 2075 | 1743000 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 0 | coupling_state | 2102 | 2102 | 0 | 2102 | 1765680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 1 | coupling_state | 2100 | 2100 | 0 | 2100 | 1764000 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 2 | coupling_state | 2102 | 2102 | 0 | 2102 | 1765680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 3 | coupling_state | 1824 | 1824 | 0 | 1824 | 1532160 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 4 | coupling_state | 1820 | 1820 | 0 | 1820 | 1528800 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 6 | coupling_state | 2097 | 2097 | 0 | 2097 | 1761480 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 7 | coupling_state | 2097 | 2097 | 0 | 2097 | 1761480 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 8 | coupling_state | 2101 | 2101 | 0 | 2101 | 1764840 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 9 | coupling_state | 2103 | 2103 | 0 | 2103 | 1766520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 10 | coupling_state | 2100 | 2100 | 0 | 2100 | 1764000 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 11 | coupling_state | 2118 | 2118 | 0 | 2118 | 1779120 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 12 | coupling_state | 2103 | 2103 | 0 | 2103 | 1766520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 13 | coupling_state | 2102 | 2102 | 0 | 2102 | 1765680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 14 | coupling_state | 2141 | 2141 | 0 | 2141 | 1798440 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 15 | coupling_state | 1822 | 1822 | 0 | 1822 | 1530480 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 16 | coupling_state | 1821 | 1821 | 0 | 1821 | 1529640 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 17 | coupling_state | 2104 | 2104 | 0 | 2104 | 1767360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 18 | coupling_state | 1821 | 1821 | 0 | 1821 | 1529640 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 19 | coupling_state | 2380 | 2380 | 0 | 2380 | 1999200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 22 | coupling_state | 1824 | 1824 | 0 | 1824 | 1532160 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 23 | coupling_state | 2104 | 2104 | 0 | 2104 | 1767360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 24 | coupling_state | 2096 | 2096 | 0 | 2096 | 1760640 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B3 | 0 | coupling_state | 5500 | 5499 | 0 | 4839 | 1156926 | 239.084 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B3 | 1 | coupling_state | 5497 | 5496 | 0 | 4836 | 1156225 | 239.087 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B3 | 2 | coupling_state | 5500 | 5499 | 0 | 4839 | 1156926 | 239.084 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B3 | 3 | coupling_state | 4768 | 4767 | 0 | 4195 | 1002938 | 239.079 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B3 | 4 | coupling_state | 4764 | 4763 | 0 | 4191 | 1001978 | 239.079 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B3 | 6 | coupling_state | 5492 | 5491 | 0 | 4831 | 1154989 | 239.079 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B3 | 7 | coupling_state | 5494 | 5493 | 0 | 4833 | 1155468 | 239.079 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B3 | 8 | coupling_state | 5498 | 5497 | 0 | 4837 | 1156465 | 239.087 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B3 | 9 | coupling_state | 5500 | 5499 | 0 | 4839 | 1156945 | 239.088 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B3 | 10 | coupling_state | 5498 | 5497 | 0 | 4837 | 1156446 | 239.083 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B3 | 11 | coupling_state | 5487 | 5486 | 0 | 4826 | 1153825 | 239.085 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B3 | 12 | coupling_state | 5500 | 5499 | 0 | 4839 | 1156871 | 239.072 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B3 | 13 | coupling_state | 5498 | 5497 | 0 | 4837 | 1156447 | 239.084 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B3 | 14 | coupling_state | 5495 | 5494 | 0 | 4834 | 1156031 | 239.146 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B3 | 15 | coupling_state | 4767 | 4766 | 0 | 4194 | 1002716 | 239.083 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B3 | 16 | coupling_state | 4767 | 4766 | 0 | 4194 | 1002697 | 239.079 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B3 | 17 | coupling_state | 5495 | 5494 | 0 | 4834 | 1155822 | 239.103 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B3 | 18 | coupling_state | 4764 | 4763 | 0 | 4191 | 1002033 | 239.092 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B3 | 19 | coupling_state | 6233 | 6232 | 0 | 5484 | 1311098 | 239.077 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B3 | 22 | coupling_state | 4769 | 4768 | 0 | 4196 | 1003196 | 239.084 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B3 | 23 | coupling_state | 5502 | 5501 | 0 | 4841 | 1157406 | 239.084 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B3 | 24 | coupling_state | 5493 | 5492 | 0 | 4832 | 1155228 | 239.079 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
*n = 88 (finished optimisation-phase runs of large_tokamak_nof).*

**`per-sweep overhead — large_tokamak_nof — campaign_stencil_backward`**

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; the finished evaluation-phase gate runs of large_tokamak_nof.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 80 (finished evaluation-phase runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; the finished evaluation-phase gate runs of large_tokamak_nof.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone.*
| arm | seed | stops_on | dispatch_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 4 | 4 | 3360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 4 | 4 | 3360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 4 | 4 | 3360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 4 | 4 | 3360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 10 | 9 | 2157 | 239.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 11 | 10 | 2397 | 239.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1456 | 242.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 9 | 8 | 1899 | 237.375 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1456 | 242.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 5 | 4 | 977 | 244.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 9 | 8 | 1881 | 235.125 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 10 | 9 | 2157 | 239.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 10 | 9 | 2121 | 235.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1420 | 236.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1456 | 242.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 6 | 5 | 1180 | 236 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 9 | 8 | 1881 | 235.125 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 6 | 5 | 1180 | 236 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 6 | 5 | 1180 | 236 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 6 | 5 | 1180 | 236 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1456 | 242.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 6 | 5 | 1180 | 236 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1456 | 242.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 9 | 8 | 1881 | 235.125 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
*n = 80 (finished evaluation-phase runs of large_tokamak_nof).*

**`per-sweep overhead — large_tokamak_nof — campaign_stencil_forward`**

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; the finished evaluation-phase gate runs of large_tokamak_nof.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 80 (finished evaluation-phase runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; the finished evaluation-phase gate runs of large_tokamak_nof.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone.*
| arm | seed | stops_on | dispatch_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27 | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 4 | 4 | 3360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 4 | 4 | 3360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 4 | 4 | 3360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 4 | 4 | 3360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 10 | 9 | 2157 | 239.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 11 | 10 | 2397 | 239.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1456 | 242.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 8 | 7 | 1678 | 239.714 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1456 | 242.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 5 | 4 | 977 | 244.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 9 | 8 | 1881 | 235.125 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 9 | 8 | 1936 | 242 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 10 | 9 | 2121 | 235.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1420 | 236.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1456 | 242.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 6 | 5 | 1180 | 236 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 9 | 8 | 1881 | 235.125 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 6 | 5 | 1180 | 236 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 6 | 5 | 1180 | 236 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 6 | 5 | 1180 | 236 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1456 | 242.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 6 | 5 | 1180 | 236 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1456 | 242.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 9 | 8 | 1881 | 235.125 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
*n = 80 (finished evaluation-phase runs of large_tokamak_nof).*

**`per-sweep overhead — low_aspect_ratio_DEMO — campaign_displaced`**

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; the finished evaluation-phase gate runs of low_aspect_ratio_DEMO.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 100 (finished evaluation-phase runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; the finished evaluation-phase gate runs of low_aspect_ratio_DEMO.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone.*
| arm | seed | stops_on | dispatch_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 1 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 2 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 3 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 4 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 5 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 6 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 7 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 8 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 9 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 10 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 11 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 12 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 13 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 14 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 15 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 16 | upstream | 5 | 0 | 0 | — | — | 4 | 79 | 19.75 | 0 |
| AR | 17 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 18 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 19 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 20 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 21 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 22 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 23 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 24 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 25 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| A0 | 1 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 2 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 3 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 4 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 5 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 6 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 7 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 8 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 9 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 10 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 11 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 12 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 13 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 14 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 15 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 16 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 17 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 18 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 19 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 20 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 21 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 22 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 23 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 24 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 25 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 1 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 2 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 3 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 4 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 5 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 6 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 7 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 8 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 9 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 10 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 11 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 12 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 13 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 14 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 15 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 16 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 17 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 18 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 19 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 20 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 21 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 22 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 23 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 24 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 25 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 1 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 2 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 3 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 4 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 5 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 6 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 7 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 8 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 9 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 10 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 11 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 12 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 13 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 14 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 15 | coupling_state | 12 | 11 | 2675 | 243.182 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 16 | coupling_state | 12 | 11 | 2675 | 243.182 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 17 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 18 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 19 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 20 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 21 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 22 | coupling_state | 12 | 11 | 2675 | 243.182 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 23 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 24 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 25 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
*n = 100 (finished evaluation-phase runs of low_aspect_ratio_DEMO).*

**`per-sweep overhead — low_aspect_ratio_DEMO — campaign_entry_references`**

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; the finished evaluation-phase gate runs of low_aspect_ratio_DEMO.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 1 (finished evaluation-phase runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; the finished evaluation-phase gate runs of low_aspect_ratio_DEMO.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone.*
| arm | seed | stops_on | dispatch_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
*n = 1 (finished evaluation-phase runs of low_aspect_ratio_DEMO).*

**`per-sweep overhead — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished optimisation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the finished optimisation-phase gate runs of low_aspect_ratio_DEMO.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 84 (finished optimisation-phase runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished optimisation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the finished optimisation-phase gate runs of low_aspect_ratio_DEMO.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone.*
| arm | seed | stops_on | dispatch_sweeps | solve_sweeps | output_loop_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | 0 | upstream | 4286 | 4284 | 2 | 0 | 0 | — | — | 3044 | 68069 | 22.3617 | 0 |
| BR | 1 | upstream | 31869 | 31867 | 2 | 0 | 0 | — | — | 22627 | 499852 | 22.091 | 0 |
| BR | 2 | upstream | 548 | 546 | 2 | 0 | 0 | — | — | 386 | 8311 | 21.5311 | 0 |
| BR | 4 | upstream | 515 | 513 | 2 | 0 | 0 | — | — | 353 | 7703 | 21.8215 | 0 |
| BR | 5 | upstream | 2903 | 2901 | 2 | 0 | 0 | — | — | 2061 | 45911 | 22.2761 | 0 |
| BR | 6 | upstream | 9255 | 9253 | 2 | 0 | 0 | — | — | 6573 | 146973 | 22.3601 | 0 |
| BR | 7 | upstream | 540 | 538 | 2 | 0 | 0 | — | — | 378 | 8353 | 22.0979 | 0 |
| BR | 8 | upstream | 527 | 525 | 2 | 0 | 0 | — | — | 365 | 8015 | 21.9589 | 0 |
| BR | 9 | upstream | 3455 | 3453 | 2 | 0 | 0 | — | — | 2453 | 54753 | 22.3208 | 0 |
| BR | 10 | upstream | 2898 | 2896 | 2 | 0 | 0 | — | — | 2056 | 45856 | 22.3035 | 0 |
| BR | 11 | upstream | 2906 | 2904 | 2 | 0 | 0 | — | — | 2064 | 45939 | 22.2573 | 0 |
| BR | 12 | upstream | 4287 | 4285 | 2 | 0 | 0 | — | — | 3045 | 68020 | 22.3383 | 0 |
| BR | 13 | upstream | 5388 | 5386 | 2 | 0 | 0 | — | — | 3826 | 85501 | 22.3474 | 0 |
| BR | 14 | upstream | 532 | 530 | 2 | 0 | 0 | — | — | 370 | 8095 | 21.8784 | 0 |
| BR | 15 | upstream | 17515 | 17513 | 2 | 0 | 0 | — | — | 12433 | 278158 | 22.3726 | 0 |
| BR | 16 | upstream | 541 | 539 | 2 | 0 | 0 | — | — | 379 | 8379 | 22.1082 | 0 |
| BR | 17 | upstream | 542 | 540 | 2 | 0 | 0 | — | — | 380 | 8405 | 22.1184 | 0 |
| BR | 18 | upstream | 4004 | 4002 | 2 | 0 | 0 | — | — | 2842 | 63492 | 22.3406 | 0 |
| BR | 19 | upstream | 3172 | 3170 | 2 | 0 | 0 | — | — | 2250 | 50250 | 22.3333 | 0 |
| BR | 20 | upstream | 536 | 534 | 2 | 0 | 0 | — | — | 374 | 8099 | 21.6551 | 0 |
| BR | 22 | upstream | 532 | 530 | 2 | 0 | 0 | — | — | 370 | 8145 | 22.0135 | 0 |
| BR | 23 | upstream | 542 | 540 | 2 | 0 | 0 | — | — | 380 | 8405 | 22.1184 | 0 |
| BR | 24 | upstream | 545 | 543 | 2 | 0 | 0 | — | — | 383 | 8483 | 22.1488 | 0 |
| B0 | 0 | coupling_state | 4139 | 4137 | 2 | 4137 | 3499902 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 1 | coupling_state | 31215 | 31213 | 2 | 31213 | 26406198 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 2 | coupling_state | 553 | 551 | 2 | 551 | 466146 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 5 | coupling_state | 2809 | 2807 | 2 | 2807 | 2374722 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 6 | coupling_state | 8934 | 8932 | 2 | 8932 | 7556472 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 7 | coupling_state | 542 | 540 | 2 | 540 | 456840 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 8 | coupling_state | 540 | 538 | 2 | 538 | 455148 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 9 | coupling_state | 3339 | 3337 | 2 | 3337 | 2823102 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 10 | coupling_state | 2809 | 2807 | 2 | 2807 | 2374722 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 11 | coupling_state | 2809 | 2807 | 2 | 2807 | 2374722 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 12 | coupling_state | 4141 | 4139 | 2 | 4139 | 3501594 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 13 | coupling_state | 5203 | 5201 | 2 | 5201 | 4400046 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 14 | coupling_state | 551 | 549 | 2 | 549 | 464454 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 15 | coupling_state | 16920 | 16918 | 2 | 16918 | 14312628 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 16 | coupling_state | 537 | 535 | 2 | 535 | 452610 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 17 | coupling_state | 539 | 537 | 2 | 537 | 454302 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 18 | coupling_state | 3868 | 3866 | 2 | 3866 | 3270636 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 19 | coupling_state | 3072 | 3070 | 2 | 3070 | 2597220 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 20 | coupling_state | 545 | 543 | 2 | 543 | 459378 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 23 | coupling_state | 541 | 539 | 2 | 539 | 455994 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 24 | coupling_state | 547 | 545 | 2 | 545 | 461070 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 0 | coupling_state | 3330 | 3330 | 0 | 3330 | 2817180 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 1 | coupling_state | 3868 | 3868 | 0 | 3868 | 3272328 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 2 | coupling_state | 538 | 538 | 0 | 538 | 455148 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 5 | coupling_state | 9440 | 9440 | 0 | 9440 | 7986240 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 6 | coupling_state | 5455 | 5455 | 0 | 5455 | 4614930 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 7 | coupling_state | 523 | 523 | 0 | 523 | 442458 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 8 | coupling_state | 523 | 523 | 0 | 523 | 442458 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 9 | coupling_state | 3600 | 3600 | 0 | 3600 | 3045600 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 11 | coupling_state | 17171 | 17171 | 0 | 17171 | 14526666 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 12 | coupling_state | 2534 | 2534 | 0 | 2534 | 2143764 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 13 | coupling_state | 4661 | 4661 | 0 | 4661 | 3943206 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 14 | coupling_state | 533 | 533 | 0 | 533 | 450918 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 15 | coupling_state | 4124 | 4124 | 0 | 4124 | 3488904 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 16 | coupling_state | 537 | 537 | 0 | 537 | 454302 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 17 | coupling_state | 538 | 538 | 0 | 538 | 455148 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 18 | coupling_state | 3077 | 3077 | 0 | 3077 | 2603142 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 19 | coupling_state | 2535 | 2535 | 0 | 2535 | 2144610 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 20 | coupling_state | 541 | 541 | 0 | 541 | 457686 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 23 | coupling_state | 539 | 539 | 0 | 539 | 455994 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 24 | coupling_state | 530 | 530 | 0 | 530 | 448380 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B3 | 0 | coupling_state | 8763 | 8762 | 0 | 7712 | 1855182 | 240.558 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B3 | 1 | coupling_state | 10183 | 10182 | 0 | 8964 | 2156500 | 240.573 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B3 | 2 | coupling_state | 1393 | 1392 | 0 | 1224 | 294788 | 240.84 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B3 | 5 | coupling_state | 24884 | 24883 | 0 | 21901 | 5268614 | 240.565 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B3 | 6 | coupling_state | 14383 | 14382 | 0 | 12660 | 3045529 | 240.563 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B3 | 7 | coupling_state | 1385 | 1384 | 0 | 1216 | 292750 | 240.748 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B3 | 8 | coupling_state | 1380 | 1379 | 0 | 1211 | 291645 | 240.83 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B3 | 9 | coupling_state | 9481 | 9480 | 0 | 8346 | 2007830 | 240.574 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B3 | 11 | coupling_state | 45222 | 45221 | 0 | 39803 | 9575641 | 240.576 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B3 | 12 | coupling_state | 6676 | 6675 | 0 | 5877 | 1413837 | 240.571 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B3 | 13 | coupling_state | 12283 | 12282 | 0 | 10812 | 2601007 | 240.567 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B3 | 14 | coupling_state | 1396 | 1395 | 0 | 1227 | 295305 | 240.672 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B3 | 15 | coupling_state | 10869 | 10868 | 0 | 9566 | 2301183 | 240.559 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B3 | 16 | coupling_state | 1397 | 1396 | 0 | 1228 | 295694 | 240.793 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B3 | 17 | coupling_state | 1402 | 1401 | 0 | 1233 | 296769 | 240.689 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B3 | 18 | coupling_state | 8088 | 8087 | 0 | 7121 | 1713243 | 240.59 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B3 | 19 | coupling_state | 6672 | 6671 | 0 | 5873 | 1412839 | 240.565 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B3 | 20 | coupling_state | 1405 | 1404 | 0 | 1236 | 297630 | 240.801 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B3 | 23 | coupling_state | 1404 | 1403 | 0 | 1235 | 297287 | 240.718 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B3 | 24 | coupling_state | 1392 | 1391 | 0 | 1223 | 294383 | 240.706 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
*n = 84 (finished optimisation-phase runs of low_aspect_ratio_DEMO).*

**`per-sweep overhead — low_aspect_ratio_DEMO — campaign_stencil_backward`**

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; the finished evaluation-phase gate runs of low_aspect_ratio_DEMO.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 76 (finished evaluation-phase runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; the finished evaluation-phase gate runs of low_aspect_ratio_DEMO.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone.*
| arm | seed | stops_on | dispatch_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 53 | 17.6667 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 53 | 17.6667 | 0 |
| AR | 0 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26 | 0 |
| AR | 0 | upstream | 5 | 0 | 0 | — | — | 4 | 104 | 26 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 10 | 9 | 2172 | 241.333 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 11 | 10 | 2416 | 241.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1463 | 243.833 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 8 | 7 | 1669 | 238.429 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1463 | 243.833 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 8 | 7 | 1654 | 236.286 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 9 | 8 | 1898 | 237.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 10 | 9 | 2172 | 241.333 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 9 | 8 | 1898 | 237.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 8 | 7 | 1654 | 236.286 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 8 | 7 | 1654 | 236.286 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1463 | 243.833 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1410 | 235 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 8 | 7 | 1677 | 239.571 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1463 | 243.833 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1463 | 243.833 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
*n = 76 (finished evaluation-phase runs of low_aspect_ratio_DEMO).*

**`per-sweep overhead — low_aspect_ratio_DEMO — campaign_stencil_forward`**

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; the finished evaluation-phase gate runs of low_aspect_ratio_DEMO.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 76 (finished evaluation-phase runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; the finished evaluation-phase gate runs of low_aspect_ratio_DEMO.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone.*
| arm | seed | stops_on | dispatch_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 53 | 17.6667 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 53 | 17.6667 | 0 |
| AR | 0 | upstream | 5 | 0 | 0 | — | — | 4 | 104 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26 | 0 |
| AR | 0 | upstream | 5 | 0 | 0 | — | — | 4 | 104 | 26 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0p | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 10 | 9 | 2172 | 241.333 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 11 | 10 | 2416 | 241.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1463 | 243.833 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 8 | 7 | 1669 | 238.429 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1463 | 243.833 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 8 | 7 | 1654 | 236.286 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 9 | 8 | 1898 | 237.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 9 | 8 | 1928 | 241 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 9 | 8 | 1898 | 237.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1433 | 238.833 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1433 | 238.833 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1463 | 243.833 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 8 | 7 | 1677 | 239.571 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1463 | 243.833 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 7 | 6 | 1463 | 243.833 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
*n = 76 (finished evaluation-phase runs of low_aspect_ratio_DEMO).*

**`per-sweep overhead — st_regression — campaign_displaced`**

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; the finished evaluation-phase gate runs of st_regression.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %, 6.67 %, 7.14 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 75 (finished evaluation-phase runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; the finished evaluation-phase gate runs of st_regression.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %, 6.67 %, 7.14 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone.*
| arm | seed | stops_on | dispatch_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 1 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 2 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 3 | upstream | 4 | 0 | 0 | — | — | 3 | 21 | 7 | 0 |
| AR | 4 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 5 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 6 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 7 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 8 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 9 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 10 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 11 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 12 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 13 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 14 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 15 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 16 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 17 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 18 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 19 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 20 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 21 | upstream | 4 | 0 | 0 | — | — | 3 | 21 | 7 | 0 |
| AR | 22 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 23 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 24 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 25 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| A0 | 1 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 2 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 3 | coupling_state | 5 | 5 | 4135 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 4 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 5 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 6 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 7 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 8 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 9 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 10 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 11 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 12 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 13 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 14 | coupling_state | 5 | 5 | 4135 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 15 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 16 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 17 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 18 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 19 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 20 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 21 | coupling_state | 5 | 5 | 4135 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 22 | coupling_state | 5 | 5 | 4135 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 23 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 24 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 25 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A1 | 1 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A1 | 2 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A1 | 3 | coupling_state | 14 | 12 | 2821 | 235.083 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0714286 |
| A1 | 4 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A1 | 5 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A1 | 6 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A1 | 7 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A1 | 8 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A1 | 9 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A1 | 10 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A1 | 11 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A1 | 12 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A1 | 13 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A1 | 14 | coupling_state | 14 | 12 | 2821 | 235.083 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0714286 |
| A1 | 15 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A1 | 16 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A1 | 17 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A1 | 18 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A1 | 19 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A1 | 20 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A1 | 21 | coupling_state | 14 | 12 | 2821 | 235.083 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0714286 |
| A1 | 22 | coupling_state | 14 | 12 | 2821 | 235.083 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0714286 |
| A1 | 23 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A1 | 24 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A1 | 25 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
*n = 75 (finished evaluation-phase runs of st_regression).*

**`per-sweep overhead — st_regression — campaign_entry_references`**

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; the finished evaluation-phase gate runs of st_regression.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 1 (finished evaluation-phase runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; the finished evaluation-phase gate runs of st_regression.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone.*
| arm | seed | stops_on | dispatch_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 0 | coupling_state | 7 | 7 | 5789 | 827 | FLAT 827 | 0 | 0 | — | 0 |
*n = 1 (finished evaluation-phase runs of st_regression).*

**`per-sweep overhead — st_regression — campaign_optimisation · BR·B0·B3`**

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished optimisation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the finished optimisation-phase gate runs of st_regression.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %, 10.7 %, 10.8 %, 10.82 %, 10.83 %, 10.84 %, 10.85 %, 10.86 %, 10.87 %, 10.9 %, 10.91 %, 10.92 %, 10.94 %, 11.15 %, 11.18 %, 11.22 %, 11.3 %, 11.57 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 75 (finished optimisation-phase runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished optimisation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the finished optimisation-phase gate runs of st_regression.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %, 10.7 %, 10.8 %, 10.82 %, 10.83 %, 10.84 %, 10.85 %, 10.86 %, 10.87 %, 10.9 %, 10.91 %, 10.92 %, 10.94 %, 11.15 %, 11.18 %, 11.22 %, 11.3 %, 11.57 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone.*
| arm | seed | stops_on | dispatch_sweeps | solve_sweeps | output_loop_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | 0 | upstream | 1891 | 1889 | 2 | 0 | 0 | — | — | 1319 | 18491 | 14.019 | 0 |
| BR | 1 | upstream | 8401 | 8399 | 2 | 0 | 0 | — | — | 5789 | 84431 | 14.5847 | 0 |
| BR | 2 | upstream | 10010 | 10008 | 2 | 0 | 0 | — | — | 7128 | 100674 | 14.1237 | 0 |
| BR | 3 | upstream | 3450 | 3448 | 2 | 0 | 0 | — | — | 2398 | 33646 | 14.0309 | 0 |
| BR | 4 | upstream | 3807 | 3805 | 2 | 0 | 0 | — | — | 2635 | 37357 | 14.1772 | 0 |
| BR | 5 | upstream | 7637 | 7635 | 2 | 0 | 0 | — | — | 5265 | 77049 | 14.6342 | 0 |
| BR | 6 | upstream | 3421 | 3419 | 2 | 0 | 0 | — | — | 2369 | 33527 | 14.1524 | 0 |
| BR | 7 | upstream | 1896 | 1894 | 2 | 0 | 0 | — | — | 1324 | 18586 | 14.0378 | 0 |
| BR | 8 | upstream | 2267 | 2265 | 2 | 0 | 0 | — | — | 1575 | 22113 | 14.04 | 0 |
| BR | 9 | upstream | 11612 | 11610 | 2 | 0 | 0 | — | — | 7980 | 117618 | 14.7391 | 0 |
| BR | 10 | upstream | 34192 | 34190 | 2 | 0 | 0 | — | — | 23600 | 343622 | 14.5603 | 0 |
| BR | 11 | upstream | 2091 | 2089 | 2 | 0 | 0 | — | — | 1459 | 20431 | 14.0034 | 0 |
| BR | 12 | upstream | 13324 | 13322 | 2 | 0 | 0 | — | — | 9362 | 132572 | 14.1606 | 0 |
| BR | 13 | upstream | 2658 | 2656 | 2 | 0 | 0 | — | — | 1846 | 25948 | 14.0563 | 0 |
| BR | 14 | upstream | 4225 | 4223 | 2 | 0 | 0 | — | — | 2933 | 41669 | 14.207 | 0 |
| BR | 15 | upstream | 5897 | 5895 | 2 | 0 | 0 | — | — | 4065 | 59235 | 14.572 | 0 |
| BR | 16 | upstream | 4614 | 4612 | 2 | 0 | 0 | — | — | 3202 | 45700 | 14.2723 | 0 |
| BR | 17 | upstream | 386 | 384 | 2 | 0 | 0 | — | — | 264 | 3468 | 13.1364 | 0 |
| BR | 18 | upstream | 2460 | 2458 | 2 | 0 | 0 | — | — | 1708 | 24136 | 14.1311 | 0 |
| BR | 19 | upstream | 2077 | 2075 | 2 | 0 | 0 | — | — | 1445 | 20255 | 14.0173 | 0 |
| BR | 20 | upstream | 2671 | 2669 | 2 | 0 | 0 | — | — | 1859 | 26069 | 14.0231 | 0 |
| BR | 21 | upstream | 1889 | 1887 | 2 | 0 | 0 | — | — | 1317 | 18471 | 14.0251 | 0 |
| BR | 22 | upstream | 2261 | 2259 | 2 | 0 | 0 | — | — | 1569 | 21999 | 14.021 | 0 |
| BR | 23 | upstream | 2080 | 2078 | 2 | 0 | 0 | — | — | 1448 | 20222 | 13.9655 | 0 |
| BR | 24 | upstream | 39951 | 39949 | 2 | 0 | 0 | — | — | 27559 | 401527 | 14.5697 | 0 |
| B0 | 0 | coupling_state | 2038 | 2036 | 2 | 2036 | 1683772 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 1 | coupling_state | 10764 | 10762 | 2 | 10762 | 8900174 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 2 | coupling_state | 10422 | 10420 | 2 | 10420 | 8617340 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 3 | coupling_state | 3643 | 3641 | 2 | 3641 | 3011107 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 4 | coupling_state | 3843 | 3841 | 2 | 3841 | 3176507 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 5 | coupling_state | 8355 | 8353 | 2 | 8353 | 6907931 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 6 | coupling_state | 3452 | 3450 | 2 | 3450 | 2853150 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 7 | coupling_state | 1894 | 1892 | 2 | 1892 | 1564684 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 8 | coupling_state | 2283 | 2281 | 2 | 2281 | 1886387 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 9 | coupling_state | 9074 | 9072 | 2 | 9072 | 7502544 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 10 | coupling_state | 31811 | 31809 | 2 | 31809 | 26306043 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 11 | coupling_state | 2099 | 2097 | 2 | 2097 | 1734219 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 12 | coupling_state | 14083 | 14081 | 2 | 14081 | 11644987 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 13 | coupling_state | 2672 | 2670 | 2 | 2670 | 2208090 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 14 | coupling_state | 4240 | 4238 | 2 | 4238 | 3504826 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 15 | coupling_state | 12000 | 11998 | 2 | 11998 | 9922346 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 16 | coupling_state | 4976 | 4974 | 2 | 4974 | 4113498 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 17 | coupling_state | 422 | 420 | 2 | 420 | 347340 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 18 | coupling_state | 2477 | 2475 | 2 | 2475 | 2046825 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 19 | coupling_state | 2667 | 2665 | 2 | 2665 | 2203955 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 20 | coupling_state | 2841 | 2839 | 2 | 2839 | 2347853 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 21 | coupling_state | 1894 | 1892 | 2 | 1892 | 1564684 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 22 | coupling_state | 2319 | 2317 | 2 | 2317 | 1916159 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 23 | coupling_state | 2239 | 2237 | 2 | 2237 | 1849999 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 24 | coupling_state | 9179 | 9177 | 2 | 9177 | 7589379 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B3 | 0 | coupling_state | 5260 | 5259 | 0 | 4119 | 970258 | 235.557 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.108365 |
| B3 | 1 | coupling_state | 31072 | 31071 | 0 | 24051 | 5659602 | 235.317 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.112963 |
| B3 | 2 | coupling_state | 21154 | 21153 | 0 | 16533 | 3892592 | 235.444 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.109199 |
| B3 | 3 | coupling_state | 9695 | 9694 | 0 | 7594 | 1788185 | 235.473 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.108303 |
| B3 | 4 | coupling_state | 10722 | 10721 | 0 | 8381 | 1972937 | 235.406 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.109121 |
| B3 | 5 | coupling_state | 110386 | 110385 | 0 | 85605 | 20138750 | 235.252 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.112242 |
| B3 | 6 | coupling_state | 9633 | 9632 | 0 | 7532 | 1773223 | 235.425 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.109 |
| B3 | 7 | coupling_state | 5259 | 5258 | 0 | 4118 | 970028 | 235.558 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.108386 |
| B3 | 8 | coupling_state | 6353 | 6352 | 0 | 4972 | 1171089 | 235.537 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.10861 |
| B3 | 9 | coupling_state | 32470 | 32469 | 0 | 25209 | 5925850 | 235.069 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111796 |
| B3 | 10 | coupling_state | 30850 | 30849 | 0 | 23709 | 5588124 | 235.696 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.115721 |
| B3 | 11 | coupling_state | 5822 | 5821 | 0 | 4561 | 1074441 | 235.571 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.10821 |
| B3 | 12 | coupling_state | 9051 | 9050 | 0 | 7070 | 1664464 | 235.426 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.10938 |
| B3 | 13 | coupling_state | 7421 | 7420 | 0 | 5800 | 1366359 | 235.579 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.10915 |
| B3 | 14 | coupling_state | 11831 | 11830 | 0 | 9250 | 2177370 | 235.391 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.109036 |
| B3 | 15 | coupling_state | 38461 | 38460 | 0 | 29880 | 7024544 | 235.092 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111542 |
| B3 | 16 | coupling_state | 14015 | 14014 | 0 | 10954 | 2577921 | 235.341 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.109169 |
| B3 | 17 | coupling_state | 1122 | 1121 | 0 | 881 | 207690 | 235.743 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.106952 |
| B3 | 18 | coupling_state | 6898 | 6897 | 0 | 5397 | 1270730 | 235.451 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.108727 |
| B3 | 19 | coupling_state | 5808 | 5807 | 0 | 4547 | 1071105 | 235.563 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.108471 |
| B3 | 20 | coupling_state | 7433 | 7432 | 0 | 5812 | 1369273 | 235.594 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.108973 |
| B3 | 21 | coupling_state | 5262 | 5261 | 0 | 4121 | 970697 | 235.549 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.108324 |
| B3 | 22 | coupling_state | 6390 | 6389 | 0 | 5009 | 1179088 | 235.394 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.107981 |
| B3 | 23 | coupling_state | 5800 | 5799 | 0 | 4539 | 1069466 | 235.617 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.108621 |
| B3 | 24 | coupling_state | 24966 | 24965 | 0 | 19385 | 4558929 | 235.178 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111752 |
*n = 75 (finished optimisation-phase runs of st_regression).*

**`per-sweep overhead — st_regression — campaign_stencil_backward`**

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; the finished evaluation-phase gate runs of st_regression.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %, 9.09 %, 10 %, 11.11 %, 12.5 %, 16.67 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 42 (finished evaluation-phase runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; the finished evaluation-phase gate runs of st_regression.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %, 9.09 %, 10 %, 11.11 %, 12.5 %, 16.67 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone.*
| arm | seed | stops_on | dispatch_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 21 | 7 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 19 | 19 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 19 | 19 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 57 | 19 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 57 | 19 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 57 | 19 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 19 | 19 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 57 | 19 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10 | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1654 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1654 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4135 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4135 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 10 | 8 | 1957 | 244.625 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.1 |
| A1 | 0 | coupling_state | 8 | 6 | 1414 | 235.667 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.125 |
| A1 | 0 | coupling_state | 9 | 7 | 1689 | 241.286 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111111 |
| A1 | 0 | coupling_state | 6 | 4 | 975 | 243.75 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.166667 |
| A1 | 0 | coupling_state | 9 | 7 | 1578 | 225.429 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111111 |
| A1 | 0 | coupling_state | 9 | 7 | 1682 | 240.286 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111111 |
| A1 | 0 | coupling_state | 9 | 7 | 1578 | 225.429 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111111 |
| A1 | 0 | coupling_state | 11 | 9 | 2017 | 224.111 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0909091 |
| A1 | 0 | coupling_state | 8 | 6 | 1369 | 228.167 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.125 |
| A1 | 0 | coupling_state | 9 | 7 | 1689 | 241.286 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111111 |
| A1 | 0 | coupling_state | 8 | 6 | 1466 | 244.333 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.125 |
| A1 | 0 | coupling_state | 11 | 9 | 2017 | 224.111 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0909091 |
| A1 | 0 | coupling_state | 8 | 6 | 1466 | 244.333 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.125 |
| A1 | 0 | coupling_state | 8 | 6 | 1466 | 244.333 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.125 |
*n = 42 (finished evaluation-phase runs of st_regression).*

**`per-sweep overhead — st_regression — campaign_stencil_forward`**

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; the finished evaluation-phase gate runs of st_regression.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %, 10 %, 11.11 %, 12.5 %, 16.67 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 42 (finished evaluation-phase runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; the finished evaluation-phase gate runs of st_regression.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %, 10 %, 11.11 %, 12.5 %, 16.67 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone.*
| arm | seed | stops_on | dispatch_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 21 | 7 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 19 | 19 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 19 | 19 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 38 | 19 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 38 | 19 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 57 | 19 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 19 | 19 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 57 | 19 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10 | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1654 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1654 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 10 | 8 | 1957 | 244.625 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.1 |
| A1 | 0 | coupling_state | 8 | 6 | 1414 | 235.667 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.125 |
| A1 | 0 | coupling_state | 9 | 7 | 1689 | 241.286 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111111 |
| A1 | 0 | coupling_state | 6 | 4 | 975 | 243.75 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.166667 |
| A1 | 0 | coupling_state | 9 | 7 | 1578 | 225.429 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111111 |
| A1 | 0 | coupling_state | 9 | 7 | 1682 | 240.286 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111111 |
| A1 | 0 | coupling_state | 9 | 7 | 1578 | 225.429 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111111 |
| A1 | 0 | coupling_state | 10 | 8 | 1801 | 225.125 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.1 |
| A1 | 0 | coupling_state | 8 | 6 | 1369 | 228.167 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.125 |
| A1 | 0 | coupling_state | 9 | 7 | 1689 | 241.286 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111111 |
| A1 | 0 | coupling_state | 8 | 6 | 1466 | 244.333 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.125 |
| A1 | 0 | coupling_state | 10 | 8 | 1801 | 225.125 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.1 |
| A1 | 0 | coupling_state | 8 | 6 | 1466 | 244.333 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.125 |
| A1 | 0 | coupling_state | 8 | 6 | 1466 | 244.333 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.125 |
*n = 42 (finished evaluation-phase runs of st_regression).*

**`same optimum (check 1) — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: dimensionless — a relative difference of the normalised objective.  A row is one arm pair over the seed set.  A column is the paired relative objective difference's median and p90, the threshold they are judged against, and the clustering statistics.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 22 seed(s) on which every arm of large_tokamak_nof reached an accepted optimum.  Construction: |Δ norm_objf| / max(|a|, |b|) per pair from the hex floats; median nearest-rank upper-middle, p90 nearest-rank ceil(0.9 n); threshold = max(F × yardstick, floor) with F = 10 and floor = 1e-06, the yardstick being the BR → B0 spread in this same population; clusters at a relative gap of 1e-05.  The yardstick row carries no threshold and no verdict: it *is* the calibration.  *Below resolution* is a named category — distinct optima closer than the cluster gap and further apart than the correctness floor.  The retried column is computed from attempts[], never from a stored flag. n = 22 (seeds on which every arm of large_tokamak_nof converged). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless — a relative difference of the normalised objective.  A row is one arm pair over the seed set.  A column is the paired relative objective difference's median and p90, the threshold they are judged against, and the clustering statistics.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 22 seed(s) on which every arm of large_tokamak_nof reached an accepted optimum.  Construction: |Δ norm_objf| / max(|a|, |b|) per pair from the hex floats; median nearest-rank upper-middle, p90 nearest-rank ceil(0.9 n); threshold = max(F × yardstick, floor) with F = 10 and floor = 1e-06, the yardstick being the BR → B0 spread in this same population; clusters at a relative gap of 1e-05.  The yardstick row carries no threshold and no verdict: it *is* the calibration.  *Below resolution* is a named category — distinct optima closer than the cluster gap and further apart than the correctness floor.  The retried column is computed from attempts[], never from a stored flag.*
| pair | n | r_median | r_p90 | threshold_median | threshold_p90 | verdict | hops | below_resolution | retried_in_pair |
|---|---|---|---|---|---|---|---|---|---|
| BR → B0 (yardstick) | 22 | 2.08167e-15 | 6.8931e-13 | — | — | — | 0/22 (0.00) | 0 | 0 |
| B0 → B1 | 22 | 2.82345e-11 | 4.56971e-11 | 1e-06 | 1e-06 | PASS | 0/22 (0.00) | 0 | 0 |
| B0 → B3 | 22 | 2.82345e-11 | 4.56971e-11 | 1e-06 | 1e-06 | PASS | 0/22 (0.00) | 0 | 0 |
*n = 22 (seeds on which every arm of large_tokamak_nof converged).*

**`same optimum (check 1) — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: dimensionless — a relative difference of the normalised objective.  A row is one arm pair over the seed set.  A column is the paired relative objective difference's median and p90, the threshold they are judged against, and the clustering statistics.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 11 seed(s) on which every arm of low_aspect_ratio_DEMO reached an accepted optimum.  Construction: |Δ norm_objf| / max(|a|, |b|) per pair from the hex floats; median nearest-rank upper-middle, p90 nearest-rank ceil(0.9 n); threshold = max(F × yardstick, floor) with F = 10 and floor = 1e-06, the yardstick being the BR → B0 spread in this same population; clusters at a relative gap of 1e-05.  The yardstick row carries no threshold and no verdict: it *is* the calibration.  *Below resolution* is a named category — distinct optima closer than the cluster gap and further apart than the correctness floor.  The retried column is computed from attempts[], never from a stored flag. n = 11 (seeds on which every arm of low_aspect_ratio_DEMO converged). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless — a relative difference of the normalised objective.  A row is one arm pair over the seed set.  A column is the paired relative objective difference's median and p90, the threshold they are judged against, and the clustering statistics.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 11 seed(s) on which every arm of low_aspect_ratio_DEMO reached an accepted optimum.  Construction: |Δ norm_objf| / max(|a|, |b|) per pair from the hex floats; median nearest-rank upper-middle, p90 nearest-rank ceil(0.9 n); threshold = max(F × yardstick, floor) with F = 10 and floor = 1e-06, the yardstick being the BR → B0 spread in this same population; clusters at a relative gap of 1e-05.  The yardstick row carries no threshold and no verdict: it *is* the calibration.  *Below resolution* is a named category — distinct optima closer than the cluster gap and further apart than the correctness floor.  The retried column is computed from attempts[], never from a stored flag.*
| pair | n | r_median | r_p90 | threshold_median | threshold_p90 | verdict | hops | below_resolution | retried_in_pair |
|---|---|---|---|---|---|---|---|---|---|
| BR → B0 (yardstick) | 11 | 1.98217e-14 | 1.97589e-13 | — | — | — | 0/11 (0.00) | 0 | 1 |
| B0 → B1 | 11 | 4.10089e-07 | 2.14765e-06 | 1e-06 | 1e-06 | FAIL | 1/11 (0.09) | 2 | 1 |
| B0 → B3 | 11 | 4.10089e-07 | 2.14765e-06 | 1e-06 | 1e-06 | FAIL | 1/11 (0.09) | 2 | 1 |
*n = 11 (seeds on which every arm of low_aspect_ratio_DEMO converged).*

**`same optimum (check 1) — st_regression — campaign_optimisation · BR·B0·B3`**

*Caption: units: dimensionless — a relative difference of the normalised objective.  A row is one arm pair over the seed set.  A column is the paired relative objective difference's median and p90, the threshold they are judged against, and the clustering statistics.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 22 seed(s) on which every arm of st_regression reached an accepted optimum.  Construction: |Δ norm_objf| / max(|a|, |b|) per pair from the hex floats; median nearest-rank upper-middle, p90 nearest-rank ceil(0.9 n); threshold = max(F × yardstick, floor) with F = 10 and floor = 1e-06, the yardstick being the BR → B0 spread in this same population; clusters at a relative gap of 1e-05.  The yardstick row carries no threshold and no verdict: it *is* the calibration.  *Below resolution* is a named category — distinct optima closer than the cluster gap and further apart than the correctness floor.  The retried column is computed from attempts[], never from a stored flag. n = 22 (seeds on which every arm of st_regression converged). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: dimensionless — a relative difference of the normalised objective.  A row is one arm pair over the seed set.  A column is the paired relative objective difference's median and p90, the threshold they are judged against, and the clustering statistics.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 22 seed(s) on which every arm of st_regression reached an accepted optimum.  Construction: |Δ norm_objf| / max(|a|, |b|) per pair from the hex floats; median nearest-rank upper-middle, p90 nearest-rank ceil(0.9 n); threshold = max(F × yardstick, floor) with F = 10 and floor = 1e-06, the yardstick being the BR → B0 spread in this same population; clusters at a relative gap of 1e-05.  The yardstick row carries no threshold and no verdict: it *is* the calibration.  *Below resolution* is a named category — distinct optima closer than the cluster gap and further apart than the correctness floor.  The retried column is computed from attempts[], never from a stored flag.*
| pair | n | r_median | r_p90 | threshold_median | threshold_p90 | verdict | hops | below_resolution | retried_in_pair |
|---|---|---|---|---|---|---|---|---|---|
| BR → B0 (yardstick) | 22 | 1.55271e-13 | 5.90757e-09 | — | — | — | 2/22 (0.09) | 0 | 3 |
| B0 → B3 | 22 | 3.46735e-13 | 3.51e-09 | 1e-06 | 1e-06 | PASS | 1/22 (0.05) | 0 | 1 |
*n = 22 (seeds on which every arm of st_regression converged).*

**`the attempt summation identity — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: counts — model executions and sweeps of the model sequence.  A row is one optimisation run.  A column is the per-attempt costs, the run's solve-phase total they decompose, and the residual between them.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 100 optimisation run(s) of large_tokamak_nof, of which 100 carry a per-attempt cost the identity can be checked on.  Construction: Σ over attempts[] against node_calls_solve_phase and dispatch_sweeps_solve_phase.  This identity is why the with- and without-retried-seeds cost ratios may be published: they are over quantities that visibly decompose the published total. n = 100 (optimisation-phase runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts — model executions and sweeps of the model sequence.  A row is one optimisation run.  A column is the per-attempt costs, the run's solve-phase total they decompose, and the residual between them.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 100 optimisation run(s) of large_tokamak_nof, of which 100 carry a per-attempt cost the identity can be checked on.  Construction: Σ over attempts[] against node_calls_solve_phase and dispatch_sweeps_solve_phase.  This identity is why the with- and without-retried-seeds cost ratios may be published: they are over quantities that visibly decompose the published total.*
| arm | seed | attempts | retried | node_per_attempt | node_total | node_residual | sweeps_per_attempt | sweeps_total | sweeps_residual | decomposes |
|---|---|---|---|---|---|---|---|---|---|---|
| BR | 0 | 1 | no | 42567 | 42567 | 0 | 2027 | 2027 | 0 | yes |
| BR | 1 | 1 | no | 42399 | 42399 | 0 | 2019 | 2019 | 0 | yes |
| BR | 2 | 1 | no | 47817 | 47817 | 0 | 2277 | 2277 | 0 | yes |
| BR | 3 | 1 | no | 36897 | 36897 | 0 | 1757 | 1757 | 0 | yes |
| BR | 4 | 1 | no | 36939 | 36939 | 0 | 1759 | 1759 | 0 | yes |
| BR | 5 | 1 | no | — | — | — | — | — | — | NO |
| BR | 6 | 1 | no | 42714 | 42714 | 0 | 2034 | 2034 | 0 | yes |
| BR | 7 | 1 | no | 42630 | 42630 | 0 | 2030 | 2030 | 0 | yes |
| BR | 8 | 1 | no | 42672 | 42672 | 0 | 2032 | 2032 | 0 | yes |
| BR | 9 | 1 | no | 42504 | 42504 | 0 | 2024 | 2024 | 0 | yes |
| BR | 10 | 1 | no | 37044 | 37044 | 0 | 1764 | 1764 | 0 | yes |
| BR | 11 | 1 | no | 42063 | 42063 | 0 | 2003 | 2003 | 0 | yes |
| BR | 12 | 1 | no | 42567 | 42567 | 0 | 2027 | 2027 | 0 | yes |
| BR | 13 | 1 | no | 42399 | 42399 | 0 | 2019 | 2019 | 0 | yes |
| BR | 14 | 1 | no | 47817 | 47817 | 0 | 2277 | 2277 | 0 | yes |
| BR | 15 | 1 | no | 36876 | 36876 | 0 | 1756 | 1756 | 0 | yes |
| BR | 16 | 1 | no | 36855 | 36855 | 0 | 1755 | 1755 | 0 | yes |
| BR | 17 | 1 | no | 42525 | 42525 | 0 | 2025 | 2025 | 0 | yes |
| BR | 18 | 1 | no | 42525 | 42525 | 0 | 2025 | 2025 | 0 | yes |
| BR | 19 | 1 | no | 42588 | 42588 | 0 | 2028 | 2028 | 0 | yes |
| BR | 20 | 1 | no | — | — | — | — | — | — | NO |
| BR | 21 | 1 | no | — | — | — | — | — | — | NO |
| BR | 22 | 1 | no | 36981 | 36981 | 0 | 1761 | 1761 | 0 | yes |
| BR | 23 | 1 | no | 42630 | 42630 | 0 | 2030 | 2030 | 0 | yes |
| BR | 24 | 1 | no | 42546 | 42546 | 0 | 2026 | 2026 | 0 | yes |
| B0 | 0 | 1 | no | 43449 | 43449 | 0 | 2069 | 2069 | 0 | yes |
| B0 | 1 | 1 | no | 43491 | 43491 | 0 | 2071 | 2071 | 0 | yes |
| B0 | 2 | 1 | no | 49623 | 49623 | 0 | 2363 | 2363 | 0 | yes |
| B0 | 3 | 1 | no | 37695 | 37695 | 0 | 1795 | 1795 | 0 | yes |
| B0 | 4 | 1 | no | 37590 | 37590 | 0 | 1790 | 1790 | 0 | yes |
| B0 | 5 | 1 | no | — | — | — | — | — | — | NO |
| B0 | 6 | 1 | no | 43449 | 43449 | 0 | 2069 | 2069 | 0 | yes |
| B0 | 7 | 1 | no | 43428 | 43428 | 0 | 2068 | 2068 | 0 | yes |
| B0 | 8 | 1 | no | 43428 | 43428 | 0 | 2068 | 2068 | 0 | yes |
| B0 | 9 | 1 | no | 43470 | 43470 | 0 | 2070 | 2070 | 0 | yes |
| B0 | 10 | 1 | no | 37590 | 37590 | 0 | 1790 | 1790 | 0 | yes |
| B0 | 11 | 1 | no | 44583 | 44583 | 0 | 2123 | 2123 | 0 | yes |
| B0 | 12 | 1 | no | 43428 | 43428 | 0 | 2068 | 2068 | 0 | yes |
| B0 | 13 | 1 | no | 43533 | 43533 | 0 | 2073 | 2073 | 0 | yes |
| B0 | 14 | 1 | no | 50253 | 50253 | 0 | 2393 | 2393 | 0 | yes |
| B0 | 15 | 1 | no | 37737 | 37737 | 0 | 1797 | 1797 | 0 | yes |
| B0 | 16 | 1 | no | 37674 | 37674 | 0 | 1794 | 1794 | 0 | yes |
| B0 | 17 | 1 | no | 43470 | 43470 | 0 | 2070 | 2070 | 0 | yes |
| B0 | 18 | 1 | no | 43323 | 43323 | 0 | 2063 | 2063 | 0 | yes |
| B0 | 19 | 1 | no | 43407 | 43407 | 0 | 2067 | 2067 | 0 | yes |
| B0 | 20 | 1 | no | — | — | — | — | — | — | NO |
| B0 | 21 | 1 | no | — | — | — | — | — | — | NO |
| B0 | 22 | 1 | no | 37758 | 37758 | 0 | 1798 | 1798 | 0 | yes |
| B0 | 23 | 1 | no | 43386 | 43386 | 0 | 2066 | 2066 | 0 | yes |
| B0 | 24 | 1 | no | 43575 | 43575 | 0 | 2075 | 2075 | 0 | yes |
| B1 | 0 | 1 | no | 44142 | 44142 | 0 | 2102 | 2102 | 0 | yes |
| B1 | 1 | 1 | no | 44100 | 44100 | 0 | 2100 | 2100 | 0 | yes |
| B1 | 2 | 1 | no | 44142 | 44142 | 0 | 2102 | 2102 | 0 | yes |
| B1 | 3 | 1 | no | 38304 | 38304 | 0 | 1824 | 1824 | 0 | yes |
| B1 | 4 | 1 | no | 38220 | 38220 | 0 | 1820 | 1820 | 0 | yes |
| B1 | 5 | 1 | no | — | — | — | — | — | — | NO |
| B1 | 6 | 1 | no | 44037 | 44037 | 0 | 2097 | 2097 | 0 | yes |
| B1 | 7 | 1 | no | 44037 | 44037 | 0 | 2097 | 2097 | 0 | yes |
| B1 | 8 | 1 | no | 44121 | 44121 | 0 | 2101 | 2101 | 0 | yes |
| B1 | 9 | 1 | no | 44163 | 44163 | 0 | 2103 | 2103 | 0 | yes |
| B1 | 10 | 1 | no | 44100 | 44100 | 0 | 2100 | 2100 | 0 | yes |
| B1 | 11 | 1 | no | 44478 | 44478 | 0 | 2118 | 2118 | 0 | yes |
| B1 | 12 | 1 | no | 44163 | 44163 | 0 | 2103 | 2103 | 0 | yes |
| B1 | 13 | 1 | no | 44142 | 44142 | 0 | 2102 | 2102 | 0 | yes |
| B1 | 14 | 1 | no | 44961 | 44961 | 0 | 2141 | 2141 | 0 | yes |
| B1 | 15 | 1 | no | 38262 | 38262 | 0 | 1822 | 1822 | 0 | yes |
| B1 | 16 | 1 | no | 38241 | 38241 | 0 | 1821 | 1821 | 0 | yes |
| B1 | 17 | 1 | no | 44184 | 44184 | 0 | 2104 | 2104 | 0 | yes |
| B1 | 18 | 1 | no | 38241 | 38241 | 0 | 1821 | 1821 | 0 | yes |
| B1 | 19 | 1 | no | 49980 | 49980 | 0 | 2380 | 2380 | 0 | yes |
| B1 | 20 | 1 | no | — | — | — | — | — | — | NO |
| B1 | 21 | 1 | no | — | — | — | — | — | — | NO |
| B1 | 22 | 1 | no | 38304 | 38304 | 0 | 1824 | 1824 | 0 | yes |
| B1 | 23 | 1 | no | 44184 | 44184 | 0 | 2104 | 2104 | 0 | yes |
| B1 | 24 | 1 | no | 44016 | 44016 | 0 | 2096 | 2096 | 0 | yes |
| B3 | 0 | 1 | no | 28055 | 28055 | 0 | 5499 | 5499 | 0 | yes |
| B3 | 1 | 1 | no | 28037 | 28037 | 0 | 5496 | 5496 | 0 | yes |
| B3 | 2 | 1 | no | 28055 | 28055 | 0 | 5499 | 5499 | 0 | yes |
| B3 | 3 | 1 | no | 24319 | 24319 | 0 | 4767 | 4767 | 0 | yes |
| B3 | 4 | 1 | no | 24307 | 24307 | 0 | 4763 | 4763 | 0 | yes |
| B3 | 5 | 1 | no | — | — | — | — | — | — | NO |
| B3 | 6 | 1 | no | 28024 | 28024 | 0 | 5491 | 5491 | 0 | yes |
| B3 | 7 | 1 | no | 28038 | 28038 | 0 | 5493 | 5493 | 0 | yes |
| B3 | 8 | 1 | no | 28040 | 28040 | 0 | 5497 | 5497 | 0 | yes |
| B3 | 9 | 1 | no | 28046 | 28046 | 0 | 5499 | 5499 | 0 | yes |
| B3 | 10 | 1 | no | 28049 | 28049 | 0 | 5497 | 5497 | 0 | yes |
| B3 | 11 | 1 | no | 28007 | 28007 | 0 | 5486 | 5486 | 0 | yes |
| B3 | 12 | 1 | no | 28066 | 28066 | 0 | 5499 | 5499 | 0 | yes |
| B3 | 13 | 1 | no | 28041 | 28041 | 0 | 5497 | 5497 | 0 | yes |
| B3 | 14 | 1 | no | 27888 | 27888 | 0 | 5494 | 5494 | 0 | yes |
| B3 | 15 | 1 | no | 24315 | 24315 | 0 | 4766 | 4766 | 0 | yes |
| B3 | 16 | 1 | no | 24324 | 24324 | 0 | 4766 | 4766 | 0 | yes |
| B3 | 17 | 1 | no | 27987 | 27987 | 0 | 5494 | 5494 | 0 | yes |
| B3 | 18 | 1 | no | 24296 | 24296 | 0 | 4763 | 4763 | 0 | yes |
| B3 | 19 | 1 | no | 31813 | 31813 | 0 | 6232 | 6232 | 0 | yes |
| B3 | 20 | 1 | no | — | — | — | — | — | — | NO |
| B3 | 21 | 1 | no | — | — | — | — | — | — | NO |
| B3 | 22 | 1 | no | 24321 | 24321 | 0 | 4768 | 4768 | 0 | yes |
| B3 | 23 | 1 | no | 28061 | 28061 | 0 | 5501 | 5501 | 0 | yes |
| B3 | 24 | 1 | no | 28035 | 28035 | 0 | 5492 | 5492 | 0 | yes |
*n = 100 (optimisation-phase runs of large_tokamak_nof).*

**`the attempt summation identity — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: counts — model executions and sweeps of the model sequence.  A row is one optimisation run.  A column is the per-attempt costs, the run's solve-phase total they decompose, and the residual between them.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 100 optimisation run(s) of low_aspect_ratio_DEMO, of which 100 carry a per-attempt cost the identity can be checked on.  Construction: Σ over attempts[] against node_calls_solve_phase and dispatch_sweeps_solve_phase.  This identity is why the with- and without-retried-seeds cost ratios may be published: they are over quantities that visibly decompose the published total. n = 100 (optimisation-phase runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts — model executions and sweeps of the model sequence.  A row is one optimisation run.  A column is the per-attempt costs, the run's solve-phase total they decompose, and the residual between them.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 100 optimisation run(s) of low_aspect_ratio_DEMO, of which 100 carry a per-attempt cost the identity can be checked on.  Construction: Σ over attempts[] against node_calls_solve_phase and dispatch_sweeps_solve_phase.  This identity is why the with- and without-retried-seeds cost ratios may be published: they are over quantities that visibly decompose the published total.*
| arm | seed | attempts | retried | node_per_attempt | node_total | node_residual | sweeps_per_attempt | sweeps_total | sweeps_residual | decomposes |
|---|---|---|---|---|---|---|---|---|---|---|
| BR | 0 | 1 | no | 89964 | 89964 | 0 | 4284 | 4284 | 0 | yes |
| BR | 1 | 2 | yes | 579369 + 89838 | 669207 | 0 | 27589 + 4278 | 31867 | 0 | yes |
| BR | 2 | 4 | yes | 2940 + 2877 + 2772 + 2877 | 11466 | 0 | 140 + 137 + 132 + 137 | 546 | 0 | yes |
| BR | 3 | 1 | no | — | — | — | — | — | — | NO |
| BR | 4 | 4 | yes | 2751 + 2877 + 2457 + 2688 | 10773 | 0 | 131 + 137 + 117 + 128 | 513 | 0 | yes |
| BR | 5 | 1 | no | 60921 | 60921 | 0 | 2901 | 2901 | 0 | yes |
| BR | 6 | 1 | no | 194313 | 194313 | 0 | 9253 | 9253 | 0 | yes |
| BR | 7 | 4 | yes | 2940 + 2877 + 2604 + 2877 | 11298 | 0 | 140 + 137 + 124 + 137 | 538 | 0 | yes |
| BR | 8 | 4 | yes | 2856 + 2877 + 2499 + 2793 | 11025 | 0 | 136 + 137 + 119 + 133 | 525 | 0 | yes |
| BR | 9 | 1 | no | 72513 | 72513 | 0 | 3453 | 3453 | 0 | yes |
| BR | 10 | 1 | no | 60816 | 60816 | 0 | 2896 | 2896 | 0 | yes |
| BR | 11 | 1 | no | 60984 | 60984 | 0 | 2904 | 2904 | 0 | yes |
| BR | 12 | 1 | no | 89985 | 89985 | 0 | 4285 | 4285 | 0 | yes |
| BR | 13 | 1 | no | 113106 | 113106 | 0 | 5386 | 5386 | 0 | yes |
| BR | 14 | 4 | yes | 2898 + 2877 + 2520 + 2835 | 11130 | 0 | 138 + 137 + 120 + 135 | 530 | 0 | yes |
| BR | 15 | 1 | no | 367773 | 367773 | 0 | 17513 | 17513 | 0 | yes |
| BR | 16 | 4 | yes | 2940 + 2877 + 2625 + 2877 | 11319 | 0 | 140 + 137 + 125 + 137 | 539 | 0 | yes |
| BR | 17 | 4 | yes | 2940 + 2877 + 2646 + 2877 | 11340 | 0 | 140 + 137 + 126 + 137 | 540 | 0 | yes |
| BR | 18 | 1 | no | 84042 | 84042 | 0 | 4002 | 4002 | 0 | yes |
| BR | 19 | 1 | no | 66570 | 66570 | 0 | 3170 | 3170 | 0 | yes |
| BR | 20 | 4 | yes | 2940 + 2877 + 2520 + 2877 | 11214 | 0 | 140 + 137 + 120 + 137 | 534 | 0 | yes |
| BR | 21 | 1 | no | — | — | — | — | — | — | NO |
| BR | 22 | 4 | yes | 2898 + 2877 + 2520 + 2835 | 11130 | 0 | 138 + 137 + 120 + 135 | 530 | 0 | yes |
| BR | 23 | 4 | yes | 2940 + 2877 + 2646 + 2877 | 11340 | 0 | 140 + 137 + 126 + 137 | 540 | 0 | yes |
| BR | 24 | 4 | yes | 2940 + 2877 + 2709 + 2877 | 11403 | 0 | 140 + 137 + 129 + 137 | 543 | 0 | yes |
| B0 | 0 | 1 | no | 86877 | 86877 | 0 | 4137 | 4137 | 0 | yes |
| B0 | 1 | 2 | yes | 558999 + 96474 | 655473 | 0 | 26619 + 4594 | 31213 | 0 | yes |
| B0 | 2 | 4 | yes | 2940 + 3087 + 2688 + 2856 | 11571 | 0 | 140 + 147 + 128 + 136 | 551 | 0 | yes |
| B0 | 3 | 1 | no | — | — | — | — | — | — | NO |
| B0 | 4 | 1 | no | — | — | — | — | — | — | NO |
| B0 | 5 | 1 | no | 58947 | 58947 | 0 | 2807 | 2807 | 0 | yes |
| B0 | 6 | 1 | no | 187572 | 187572 | 0 | 8932 | 8932 | 0 | yes |
| B0 | 7 | 4 | yes | 2877 + 3003 + 2667 + 2793 | 11340 | 0 | 137 + 143 + 127 + 133 | 540 | 0 | yes |
| B0 | 8 | 4 | yes | 2877 + 3003 + 2625 + 2793 | 11298 | 0 | 137 + 143 + 125 + 133 | 538 | 0 | yes |
| B0 | 9 | 1 | no | 70077 | 70077 | 0 | 3337 | 3337 | 0 | yes |
| B0 | 10 | 1 | no | 58947 | 58947 | 0 | 2807 | 2807 | 0 | yes |
| B0 | 11 | 1 | no | 58947 | 58947 | 0 | 2807 | 2807 | 0 | yes |
| B0 | 12 | 1 | no | 86919 | 86919 | 0 | 4139 | 4139 | 0 | yes |
| B0 | 13 | 1 | no | 109221 | 109221 | 0 | 5201 | 5201 | 0 | yes |
| B0 | 14 | 4 | yes | 2919 + 3087 + 2688 + 2835 | 11529 | 0 | 139 + 147 + 128 + 135 | 549 | 0 | yes |
| B0 | 15 | 1 | no | 355278 | 355278 | 0 | 16918 | 16918 | 0 | yes |
| B0 | 16 | 4 | yes | 2877 + 2982 + 2583 + 2793 | 11235 | 0 | 137 + 142 + 123 + 133 | 535 | 0 | yes |
| B0 | 17 | 4 | yes | 2877 + 2982 + 2625 + 2793 | 11277 | 0 | 137 + 142 + 125 + 133 | 537 | 0 | yes |
| B0 | 18 | 1 | no | 81186 | 81186 | 0 | 3866 | 3866 | 0 | yes |
| B0 | 19 | 1 | no | 64470 | 64470 | 0 | 3070 | 3070 | 0 | yes |
| B0 | 20 | 4 | yes | 2898 + 3024 + 2667 + 2814 | 11403 | 0 | 138 + 144 + 127 + 134 | 543 | 0 | yes |
| B0 | 21 | 1 | no | — | — | — | — | — | — | NO |
| B0 | 22 | 1 | no | — | — | — | — | — | — | NO |
| B0 | 23 | 4 | yes | 2877 + 3024 + 2625 + 2793 | 11319 | 0 | 137 + 144 + 125 + 133 | 539 | 0 | yes |
| B0 | 24 | 4 | yes | 2898 + 3045 + 2688 + 2814 | 11445 | 0 | 138 + 145 + 128 + 134 | 545 | 0 | yes |
| B1 | 0 | 1 | no | 69930 | 69930 | 0 | 3330 | 3330 | 0 | yes |
| B1 | 1 | 1 | no | 81228 | 81228 | 0 | 3868 | 3868 | 0 | yes |
| B1 | 2 | 4 | yes | 2856 + 2982 + 2688 + 2772 | 11298 | 0 | 136 + 142 + 128 + 132 | 538 | 0 | yes |
| B1 | 3 | 1 | no | — | — | — | — | — | — | NO |
| B1 | 4 | 1 | no | — | — | — | — | — | — | NO |
| B1 | 5 | 1 | no | 198240 | 198240 | 0 | 9440 | 9440 | 0 | yes |
| B1 | 6 | 1 | no | 114555 | 114555 | 0 | 5455 | 5455 | 0 | yes |
| B1 | 7 | 4 | yes | 2793 + 2835 + 2646 + 2709 | 10983 | 0 | 133 + 135 + 126 + 129 | 523 | 0 | yes |
| B1 | 8 | 4 | yes | 2793 + 2835 + 2646 + 2709 | 10983 | 0 | 133 + 135 + 126 + 129 | 523 | 0 | yes |
| B1 | 9 | 1 | no | 75600 | 75600 | 0 | 3600 | 3600 | 0 | yes |
| B1 | 10 | 2 | yes | — | — | — | — | — | — | NO |
| B1 | 11 | 1 | no | 360591 | 360591 | 0 | 17171 | 17171 | 0 | yes |
| B1 | 12 | 1 | no | 53214 | 53214 | 0 | 2534 | 2534 | 0 | yes |
| B1 | 13 | 1 | no | 97881 | 97881 | 0 | 4661 | 4661 | 0 | yes |
| B1 | 14 | 4 | yes | 2856 + 2898 + 2667 + 2772 | 11193 | 0 | 136 + 138 + 127 + 132 | 533 | 0 | yes |
| B1 | 15 | 1 | no | 86604 | 86604 | 0 | 4124 | 4124 | 0 | yes |
| B1 | 16 | 4 | yes | 2856 + 3024 + 2625 + 2772 | 11277 | 0 | 136 + 144 + 125 + 132 | 537 | 0 | yes |
| B1 | 17 | 4 | yes | 2856 + 3003 + 2667 + 2772 | 11298 | 0 | 136 + 143 + 127 + 132 | 538 | 0 | yes |
| B1 | 18 | 1 | no | 64617 | 64617 | 0 | 3077 | 3077 | 0 | yes |
| B1 | 19 | 1 | no | 53235 | 53235 | 0 | 2535 | 2535 | 0 | yes |
| B1 | 20 | 4 | yes | 2856 + 3003 + 2730 + 2772 | 11361 | 0 | 136 + 143 + 130 + 132 | 541 | 0 | yes |
| B1 | 21 | 1 | no | — | — | — | — | — | — | NO |
| B1 | 22 | 1 | no | — | — | — | — | — | — | NO |
| B1 | 23 | 4 | yes | 2856 + 3024 + 2667 + 2772 | 11319 | 0 | 136 + 144 + 127 + 132 | 539 | 0 | yes |
| B1 | 24 | 4 | yes | 2835 + 2877 + 2667 + 2751 | 11130 | 0 | 135 + 137 + 127 + 131 | 530 | 0 | yes |
| B3 | 0 | 1 | no | 45496 | 45496 | 0 | 8762 | 8762 | 0 | yes |
| B3 | 1 | 1 | no | 52834 | 52834 | 0 | 10182 | 10182 | 0 | yes |
| B3 | 2 | 4 | yes | 1792 + 1896 + 1654 + 1750 | 7092 | 0 | 353 + 363 + 332 + 344 | 1392 | 0 | yes |
| B3 | 3 | 1 | no | — | — | — | — | — | — | NO |
| B3 | 4 | 1 | no | — | — | — | — | — | — | NO |
| B3 | 5 | 1 | no | 129215 | 129215 | 0 | 24883 | 24883 | 0 | yes |
| B3 | 6 | 1 | no | 74687 | 74687 | 0 | 14382 | 14382 | 0 | yes |
| B3 | 7 | 4 | yes | 1819 + 1876 + 1654 + 1777 | 7126 | 0 | 353 + 357 + 330 + 344 | 1384 | 0 | yes |
| B3 | 8 | 4 | yes | 1795 + 1876 + 1642 + 1753 | 7066 | 0 | 351 + 357 + 329 + 342 | 1379 | 0 | yes |
| B3 | 9 | 1 | no | 49194 | 49194 | 0 | 9480 | 9480 | 0 | yes |
| B3 | 10 | 2 | yes | — | — | — | — | — | — | NO |
| B3 | 11 | 1 | no | 234616 | 234616 | 0 | 45221 | 45221 | 0 | yes |
| B3 | 12 | 1 | no | 34646 | 34646 | 0 | 6675 | 6675 | 0 | yes |
| B3 | 13 | 1 | no | 63761 | 63761 | 0 | 12282 | 12282 | 0 | yes |
| B3 | 14 | 4 | yes | 1837 + 1895 + 1663 + 1795 | 7190 | 0 | 356 + 360 + 332 + 347 | 1395 | 0 | yes |
| B3 | 15 | 1 | no | 56439 | 56439 | 0 | 10868 | 10868 | 0 | yes |
| B3 | 16 | 4 | yes | 1816 + 1912 + 1644 + 1774 | 7146 | 0 | 355 + 366 + 329 + 346 | 1396 | 0 | yes |
| B3 | 17 | 4 | yes | 1840 + 1908 + 1662 + 1798 | 7208 | 0 | 357 + 364 + 332 + 348 | 1401 | 0 | yes |
| B3 | 18 | 1 | no | 41920 | 41920 | 0 | 8087 | 8087 | 0 | yes |
| B3 | 19 | 1 | no | 34628 | 34628 | 0 | 6671 | 6671 | 0 | yes |
| B3 | 20 | 4 | yes | 1828 + 1900 + 1672 + 1786 | 7186 | 0 | 356 + 365 + 336 + 347 | 1404 | 0 | yes |
| B3 | 21 | 1 | no | — | — | — | — | — | — | NO |
| B3 | 22 | 1 | no | — | — | — | — | — | — | NO |
| B3 | 23 | 4 | yes | 1840 + 1912 + 1662 + 1798 | 7212 | 0 | 357 + 366 + 332 + 348 | 1403 | 0 | yes |
| B3 | 24 | 4 | yes | 1825 + 1881 + 1663 + 1783 | 7152 | 0 | 355 + 358 + 332 + 346 | 1391 | 0 | yes |
*n = 100 (optimisation-phase runs of low_aspect_ratio_DEMO).*

**`the attempt summation identity — st_regression — campaign_optimisation · BR·B0·B3`**

*Caption: units: counts — model executions and sweeps of the model sequence.  A row is one optimisation run.  A column is the per-attempt costs, the run's solve-phase total they decompose, and the residual between them.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 75 optimisation run(s) of st_regression, of which 75 carry a per-attempt cost the identity can be checked on.  Construction: Σ over attempts[] against node_calls_solve_phase and dispatch_sweeps_solve_phase.  This identity is why the with- and without-retried-seeds cost ratios may be published: they are over quantities that visibly decompose the published total. n = 75 (optimisation-phase runs of st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts — model executions and sweeps of the model sequence.  A row is one optimisation run.  A column is the per-attempt costs, the run's solve-phase total they decompose, and the residual between them.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 75 optimisation run(s) of st_regression, of which 75 carry a per-attempt cost the identity can be checked on.  Construction: Σ over attempts[] against node_calls_solve_phase and dispatch_sweeps_solve_phase.  This identity is why the with- and without-retried-seeds cost ratios may be published: they are over quantities that visibly decompose the published total.*
| arm | seed | attempts | retried | node_per_attempt | node_total | node_residual | sweeps_per_attempt | sweeps_total | sweeps_residual | decomposes |
|---|---|---|---|---|---|---|---|---|---|---|
| BR | 0 | 1 | no | 39669 | 39669 | 0 | 1889 | 1889 | 0 | yes |
| BR | 1 | 1 | no | 176379 | 176379 | 0 | 8399 | 8399 | 0 | yes |
| BR | 2 | 2 | yes | 113442 + 96726 | 210168 | 0 | 5402 + 4606 | 10008 | 0 | yes |
| BR | 3 | 1 | no | 72408 | 72408 | 0 | 3448 | 3448 | 0 | yes |
| BR | 4 | 1 | no | 79905 | 79905 | 0 | 3805 | 3805 | 0 | yes |
| BR | 5 | 1 | no | 160335 | 160335 | 0 | 7635 | 7635 | 0 | yes |
| BR | 6 | 1 | no | 71799 | 71799 | 0 | 3419 | 3419 | 0 | yes |
| BR | 7 | 1 | no | 39774 | 39774 | 0 | 1894 | 1894 | 0 | yes |
| BR | 8 | 1 | no | 47565 | 47565 | 0 | 2265 | 2265 | 0 | yes |
| BR | 9 | 1 | no | 243810 | 243810 | 0 | 11610 | 11610 | 0 | yes |
| BR | 10 | 3 | yes | 226149 + 272601 + 219240 | 717990 | 0 | 10769 + 12981 + 10440 | 34190 | 0 | yes |
| BR | 11 | 1 | no | 43869 | 43869 | 0 | 2089 | 2089 | 0 | yes |
| BR | 12 | 2 | yes | 211659 + 68103 | 279762 | 0 | 10079 + 3243 | 13322 | 0 | yes |
| BR | 13 | 1 | no | 55776 | 55776 | 0 | 2656 | 2656 | 0 | yes |
| BR | 14 | 1 | no | 88683 | 88683 | 0 | 4223 | 4223 | 0 | yes |
| BR | 15 | 1 | no | 123795 | 123795 | 0 | 5895 | 5895 | 0 | yes |
| BR | 16 | 1 | no | 96852 | 96852 | 0 | 4612 | 4612 | 0 | yes |
| BR | 17 | 4 | yes | 2121 + 2121 + 1785 + 2037 | 8064 | 0 | 101 + 101 + 85 + 97 | 384 | 0 | yes |
| BR | 18 | 1 | no | 51618 | 51618 | 0 | 2458 | 2458 | 0 | yes |
| BR | 19 | 1 | no | 43575 | 43575 | 0 | 2075 | 2075 | 0 | yes |
| BR | 20 | 1 | no | 56049 | 56049 | 0 | 2669 | 2669 | 0 | yes |
| BR | 21 | 1 | no | 39627 | 39627 | 0 | 1887 | 1887 | 0 | yes |
| BR | 22 | 1 | no | 47439 | 47439 | 0 | 2259 | 2259 | 0 | yes |
| BR | 23 | 1 | no | 43638 | 43638 | 0 | 2078 | 2078 | 0 | yes |
| BR | 24 | 3 | yes | 249102 + 283311 + 306516 | 838929 | 0 | 11862 + 13491 + 14596 | 39949 | 0 | yes |
| B0 | 0 | 1 | no | 42756 | 42756 | 0 | 2036 | 2036 | 0 | yes |
| B0 | 1 | 1 | no | 226002 | 226002 | 0 | 10762 | 10762 | 0 | yes |
| B0 | 2 | 2 | yes | 117789 + 101031 | 218820 | 0 | 5609 + 4811 | 10420 | 0 | yes |
| B0 | 3 | 1 | no | 76461 | 76461 | 0 | 3641 | 3641 | 0 | yes |
| B0 | 4 | 1 | no | 80661 | 80661 | 0 | 3841 | 3841 | 0 | yes |
| B0 | 5 | 1 | no | 175413 | 175413 | 0 | 8353 | 8353 | 0 | yes |
| B0 | 6 | 1 | no | 72450 | 72450 | 0 | 3450 | 3450 | 0 | yes |
| B0 | 7 | 1 | no | 39732 | 39732 | 0 | 1892 | 1892 | 0 | yes |
| B0 | 8 | 1 | no | 47901 | 47901 | 0 | 2281 | 2281 | 0 | yes |
| B0 | 9 | 1 | no | 190512 | 190512 | 0 | 9072 | 9072 | 0 | yes |
| B0 | 10 | 3 | yes | 263676 + 239421 + 164892 | 667989 | 0 | 12556 + 11401 + 7852 | 31809 | 0 | yes |
| B0 | 11 | 1 | no | 44037 | 44037 | 0 | 2097 | 2097 | 0 | yes |
| B0 | 12 | 1 | no | 295701 | 295701 | 0 | 14081 | 14081 | 0 | yes |
| B0 | 13 | 1 | no | 56070 | 56070 | 0 | 2670 | 2670 | 0 | yes |
| B0 | 14 | 1 | no | 88998 | 88998 | 0 | 4238 | 4238 | 0 | yes |
| B0 | 15 | 1 | no | 251958 | 251958 | 0 | 11998 | 11998 | 0 | yes |
| B0 | 16 | 1 | no | 104454 | 104454 | 0 | 4974 | 4974 | 0 | yes |
| B0 | 17 | 4 | yes | 2289 + 2352 + 2016 + 2163 | 8820 | 0 | 109 + 112 + 96 + 103 | 420 | 0 | yes |
| B0 | 18 | 1 | no | 51975 | 51975 | 0 | 2475 | 2475 | 0 | yes |
| B0 | 19 | 1 | no | 55965 | 55965 | 0 | 2665 | 2665 | 0 | yes |
| B0 | 20 | 1 | no | 59619 | 59619 | 0 | 2839 | 2839 | 0 | yes |
| B0 | 21 | 1 | no | 39732 | 39732 | 0 | 1892 | 1892 | 0 | yes |
| B0 | 22 | 1 | no | 48657 | 48657 | 0 | 2317 | 2317 | 0 | yes |
| B0 | 23 | 1 | no | 46977 | 46977 | 0 | 2237 | 2237 | 0 | yes |
| B0 | 24 | 1 | no | 192717 | 192717 | 0 | 9177 | 9177 | 0 | yes |
| B3 | 0 | 1 | no | 23505 | 23505 | 0 | 5259 | 5259 | 0 | yes |
| B3 | 1 | 1 | no | 134560 | 134560 | 0 | 31071 | 31071 | 0 | yes |
| B3 | 2 | 1 | no | 93767 | 93767 | 0 | 21153 | 21153 | 0 | yes |
| B3 | 3 | 1 | no | 43204 | 43204 | 0 | 9694 | 9694 | 0 | yes |
| B3 | 4 | 1 | no | 47985 | 47985 | 0 | 10721 | 10721 | 0 | yes |
| B3 | 5 | 3 | yes | 175996 + 137488 + 166146 | 479630 | 0 | 39645 + 29681 + 41059 | 110385 | 0 | yes |
| B3 | 6 | 1 | no | 43103 | 43103 | 0 | 9632 | 9632 | 0 | yes |
| B3 | 7 | 1 | no | 23484 | 23484 | 0 | 5258 | 5258 | 0 | yes |
| B3 | 8 | 1 | no | 28385 | 28385 | 0 | 6352 | 6352 | 0 | yes |
| B3 | 9 | 1 | no | 143424 | 143424 | 0 | 32469 | 32469 | 0 | yes |
| B3 | 10 | 1 | no | 129012 | 129012 | 0 | 30849 | 30849 | 0 | yes |
| B3 | 11 | 1 | no | 25988 | 25988 | 0 | 5821 | 5821 | 0 | yes |
| B3 | 12 | 1 | no | 40163 | 40163 | 0 | 9050 | 9050 | 0 | yes |
| B3 | 13 | 1 | no | 32983 | 32983 | 0 | 7420 | 7420 | 0 | yes |
| B3 | 14 | 1 | no | 52965 | 52965 | 0 | 11830 | 11830 | 0 | yes |
| B3 | 15 | 1 | no | 169358 | 169358 | 0 | 38460 | 38460 | 0 | yes |
| B3 | 16 | 1 | no | 62796 | 62796 | 0 | 14014 | 14014 | 0 | yes |
| B3 | 17 | 4 | yes | 1288 + 1360 + 1045 + 1228 | 4921 | 0 | 290 + 295 + 258 + 278 | 1121 | 0 | yes |
| B3 | 18 | 1 | no | 30852 | 30852 | 0 | 6897 | 6897 | 0 | yes |
| B3 | 19 | 1 | no | 25952 | 25952 | 0 | 5807 | 5807 | 0 | yes |
| B3 | 20 | 1 | no | 32958 | 32958 | 0 | 7432 | 7432 | 0 | yes |
| B3 | 21 | 1 | no | 23520 | 23520 | 0 | 5261 | 5261 | 0 | yes |
| B3 | 22 | 1 | no | 28505 | 28505 | 0 | 6389 | 6389 | 0 | yes |
| B3 | 23 | 1 | no | 25771 | 25771 | 0 | 5799 | 5799 | 0 | yes |
| B3 | 24 | 1 | no | 109933 | 109933 | 0 | 24965 | 24965 | 0 | yes |
*n = 75 (optimisation-phase runs of st_regression).*

**`the failure table — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: counts — model executions for the cost columns, optimiser exit codes for ifail.  A row is one seed outside the converged set.  A column is which arm failed there, how it failed, what it cost, and what the other arms cost at the same start.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 3 of 25 seed(s) on large_tokamak_nof lie outside the every-arm-converged set.  Construction: membership by accepted optimum; the cost column is node_calls_solve_phase, the same unit the cost table uses.  An arm the gate did not run at a seed reads *not run* rather than *failed*. n = 25 (distinct seeds run on large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts — model executions for the cost columns, optimiser exit codes for ifail.  A row is one seed outside the converged set.  A column is which arm failed there, how it failed, what it cost, and what the other arms cost at the same start.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 3 of 25 seed(s) on large_tokamak_nof lie outside the every-arm-converged set.  Construction: membership by accepted optimum; the cost column is node_calls_solve_phase, the same unit the cost table uses.  An arm the gate did not run at a seed reads *not run* rather than *failed*.*
| seed | failed | not_run | ifail | attempts | failed_cost | other_cost | configuration_invalid |
|---|---|---|---|---|---|---|---|
| 5 | BR, B0, B1, B3 | — | None, None, None, None | 1, 1, 1, 1 | None, None, None, None | BR — / B0 — / B1 — / B3 — | yes |
| 20 | BR, B0, B1, B3 | — | None, None, None, None | 1, 1, 1, 1 | None, None, None, None | BR — / B0 — / B1 — / B3 — | yes |
| 21 | BR, B0, B1, B3 | — | None, None, None, None | 1, 1, 1, 1 | None, None, None, None | BR — / B0 — / B1 — / B3 — | yes |
*n = 25 (distinct seeds run on large_tokamak_nof).*

**`the failure table — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: counts — model executions for the cost columns, optimiser exit codes for ifail.  A row is one seed outside the converged set.  A column is which arm failed there, how it failed, what it cost, and what the other arms cost at the same start.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 14 of 25 seed(s) on low_aspect_ratio_DEMO lie outside the every-arm-converged set.  Construction: membership by accepted optimum; the cost column is node_calls_solve_phase, the same unit the cost table uses.  An arm the gate did not run at a seed reads *not run* rather than *failed*. n = 25 (distinct seeds run on low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts — model executions for the cost columns, optimiser exit codes for ifail.  A row is one seed outside the converged set.  A column is which arm failed there, how it failed, what it cost, and what the other arms cost at the same start.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 14 of 25 seed(s) on low_aspect_ratio_DEMO lie outside the every-arm-converged set.  Construction: membership by accepted optimum; the cost column is node_calls_solve_phase, the same unit the cost table uses.  An arm the gate did not run at a seed reads *not run* rather than *failed*.*
| seed | failed | not_run | ifail | attempts | failed_cost | other_cost | configuration_invalid |
|---|---|---|---|---|---|---|---|
| 2 | BR, B0, B1, B3 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11466, 11571, 11298, 7092 | BR — / B0 — / B1 — / B3 — | yes |
| 3 | BR, B0, B1, B3 | — | None, None, None, None | 1, 1, 1, 1 | None, None, None, None | BR — / B0 — / B1 — / B3 — | yes |
| 4 | BR, B0, B1, B3 | — | 5.0, None, None, None | 4, 1, 1, 1 | 10773, None, None, None | BR — / B0 — / B1 — / B3 — | yes |
| 7 | BR, B0, B1, B3 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11298, 11340, 10983, 7126 | BR — / B0 — / B1 — / B3 — | yes |
| 8 | BR, B0, B1, B3 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11025, 11298, 10983, 7066 | BR — / B0 — / B1 — / B3 — | yes |
| 10 | B1, B3 | — | None, None | 2, 2 | None, None | BR 60816 / B0 58947 / B1 — / B3 — | no |
| 14 | BR, B0, B1, B3 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11130, 11529, 11193, 7190 | BR — / B0 — / B1 — / B3 — | yes |
| 16 | BR, B0, B1, B3 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11319, 11235, 11277, 7146 | BR — / B0 — / B1 — / B3 — | yes |
| 17 | BR, B0, B1, B3 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11340, 11277, 11298, 7208 | BR — / B0 — / B1 — / B3 — | yes |
| 20 | BR, B0, B1, B3 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11214, 11403, 11361, 7186 | BR — / B0 — / B1 — / B3 — | yes |
| 21 | BR, B0, B1, B3 | — | None, None, None, None | 1, 1, 1, 1 | None, None, None, None | BR — / B0 — / B1 — / B3 — | yes |
| 22 | BR, B0, B1, B3 | — | 5.0, None, None, None | 4, 1, 1, 1 | 11130, None, None, None | BR — / B0 — / B1 — / B3 — | yes |
| 23 | BR, B0, B1, B3 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11340, 11319, 11319, 7212 | BR — / B0 — / B1 — / B3 — | yes |
| 24 | BR, B0, B1, B3 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11403, 11445, 11130, 7152 | BR — / B0 — / B1 — / B3 — | yes |
*n = 25 (distinct seeds run on low_aspect_ratio_DEMO).*

**`the failure table — st_regression — campaign_optimisation · BR·B0·B3`**

*Caption: units: counts — model executions for the cost columns, optimiser exit codes for ifail.  A row is one seed outside the converged set.  A column is which arm failed there, how it failed, what it cost, and what the other arms cost at the same start.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 3 of 25 seed(s) on st_regression lie outside the every-arm-converged set.  Construction: membership by accepted optimum; the cost column is node_calls_solve_phase, the same unit the cost table uses.  An arm the gate did not run at a seed reads *not run* rather than *failed*. n = 25 (distinct seeds run on st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts — model executions for the cost columns, optimiser exit codes for ifail.  A row is one seed outside the converged set.  A column is which arm failed there, how it failed, what it cost, and what the other arms cost at the same start.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 3 of 25 seed(s) on st_regression lie outside the every-arm-converged set.  Construction: membership by accepted optimum; the cost column is node_calls_solve_phase, the same unit the cost table uses.  An arm the gate did not run at a seed reads *not run* rather than *failed*.*
| seed | failed | not_run | ifail | attempts | failed_cost | other_cost | configuration_invalid |
|---|---|---|---|---|---|---|---|
| 5 | B3 | — | 5.0 | 3 | 479630 | BR 160335 / B0 175413 / B3 — | no |
| 10 | B0 | — | 5.0 | 3 | 667989 | BR 717990 / B0 — / B3 129012 | no |
| 17 | BR, B0, B3 | — | 5.0, 5.0, 5.0 | 4, 4, 4 | 8064, 8820, 4921 | BR — / B0 — / B3 — | yes |
*n = 25 (distinct seeds run on st_regression).*

**`the lift closed (check 3) — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: seconds for the residual; the relative column is dimensionless (residual / burn time).  A row is one arm whose runs name the burn-time consistency constraint.  A column is the residual of that constraint at the accepted optima.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the accepted optima of large_tokamak_nof whose input file names the constraint.  Construction: the model's own extracted consistency relation evaluated on the returned state, |value|, median nearest-rank upper-middle.  An arm whose input file does not name the constraint is absent from this table rather than reading 0; residuals at unconverged exits are never pooled with these. n = 100 (optimisation-phase runs of large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: seconds for the residual; the relative column is dimensionless (residual / burn time).  A row is one arm whose runs name the burn-time consistency constraint.  A column is the residual of that constraint at the accepted optima.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the accepted optima of large_tokamak_nof whose input file names the constraint.  Construction: the model's own extracted consistency relation evaluated on the returned state, |value|, median nearest-rank upper-middle.  An arm whose input file does not name the constraint is absent from this table rather than reading 0; residuals at unconverged exits are never pooled with these.*
| arm | n | residual_s_median | bracket | relative_median | in_equality_block |
|---|---|---|---|---|---|
| B1 | 22 | 1.65911e-05 | [2.600e-06, 1.600e-03] | 2.30429e-09 | True |
| B3 | 22 | 1.65911e-05 | [2.600e-06, 1.600e-03] | 2.30429e-09 | True |
*n = 100 (optimisation-phase runs of large_tokamak_nof).*

**`the lift closed (check 3) — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: seconds for the residual; the relative column is dimensionless (residual / burn time).  A row is one arm whose runs name the burn-time consistency constraint.  A column is the residual of that constraint at the accepted optima.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the accepted optima of low_aspect_ratio_DEMO whose input file names the constraint.  Construction: the model's own extracted consistency relation evaluated on the returned state, |value|, median nearest-rank upper-middle.  An arm whose input file does not name the constraint is absent from this table rather than reading 0; residuals at unconverged exits are never pooled with these. n = 100 (optimisation-phase runs of low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: seconds for the residual; the relative column is dimensionless (residual / burn time).  A row is one arm whose runs name the burn-time consistency constraint.  A column is the residual of that constraint at the accepted optima.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the accepted optima of low_aspect_ratio_DEMO whose input file names the constraint.  Construction: the model's own extracted consistency relation evaluated on the returned state, |value|, median nearest-rank upper-middle.  An arm whose input file does not name the constraint is absent from this table rather than reading 0; residuals at unconverged exits are never pooled with these.*
| arm | n | residual_s_median | bracket | relative_median | in_equality_block |
|---|---|---|---|---|---|
| B1 | 11 | 5.47958e-06 | [1.692e-07, 4.756e-05] | 6.74426e-10 | True |
| B3 | 11 | 5.47958e-06 | [1.692e-07, 4.756e-05] | 6.74426e-10 | True |
*n = 100 (optimisation-phase runs of low_aspect_ratio_DEMO).*

**`the predicate trial — frozen against mixed`**

*Caption: units: counts of predicate evaluations; the audit columns are hex floats of the largest scaled residual.  A row is one pair of runs — the same arm, configuration and seed under each ruler.  A column is a count of the trial, or one run's exit audit read on one named ruler.  Population: 12 pair(s) = 3 configuration(s) x the evaluation-phase arms active on each (A0, A1) x 2 seed(s), each run under both rulers = 24 runs at delta = 0.1; 8068 deterministic record values and 84 output-file lines compared without tolerance, 240 record values excluded as the setting being varied or as run metadata (each named, with its reason, in this record); 143 predicate evaluations observed on both rulers.  Construction: **read from the trial gate's verdict, not from run records** — the decisive-pass counts come from an observer that watches the run's own predicate evaluations and cannot be reconstructed from a record afterwards, so this recomputation checks the table's shaping and not the measurement.  Decisive passes are two counts, never one: crossings, and the verdict changes that alone can make two runs differ. n = 12 (pairs of runs, one per ruler). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of predicate evaluations; the audit columns are hex floats of the largest scaled residual.  A row is one pair of runs — the same arm, configuration and seed under each ruler.  A column is a count of the trial, or one run's exit audit read on one named ruler.  Population: 12 pair(s) = 3 configuration(s) x the evaluation-phase arms active on each (A0, A1) x 2 seed(s), each run under both rulers = 24 runs at delta = 0.1; 8068 deterministic record values and 84 output-file lines compared without tolerance, 240 record values excluded as the setting being varied or as run metadata (each named, with its reason, in this record); 143 predicate evaluations observed on both rulers.  Construction: **read from the trial gate's verdict, not from run records** — the decisive-pass counts come from an observer that watches the run's own predicate evaluations and cannot be reconstructed from a record afterwards, so this recomputation checks the table's shaping and not the measurement.  Decisive passes are two counts, never one: crossings, and the verdict changes that alone can make two runs differ.*
| configuration | arm | seed | evaluations | crossings | verdict_changes | identical | audit_frozen_run_frozen_ruler | audit_frozen_run_mixed_ruler | audit_mixed_run_frozen_ruler | audit_mixed_run_mixed_ruler |
|---|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | A0 | 1 | 9 | 3 | 0 | yes | 0x1.5fe433222bb97p-29 | 0x1.f8c2a9ec36d62p-31 | 0x1.5fe433222bb97p-29 | 0x1.f8c2a9ec36d62p-31 |
| large_tokamak_nof | A0 | 2 | 8 | 1 | 0 | yes | 0x0.0p+0 | 0x0.0p+0 | 0x0.0p+0 | 0x0.0p+0 |
| large_tokamak_nof | A1 | 1 | 15 | 2 | 0 | yes | 0x1.f5b2a3ea40bd7p-1 | 0x1.774db44e2d2b1p-3 | 0x1.f5b2a3ea40bd7p-1 | 0x1.774db44e2d2b1p-3 |
| large_tokamak_nof | A1 | 2 | 15 | 1 | 0 | yes | 0x1.c4dcc35b240c9p+0 | 0x1.656469d523e7ep-2 | 0x1.c4dcc35b240c9p+0 | 0x1.656469d523e7ep-2 |
| low_aspect_ratio_DEMO | A0 | 1 | 8 | 0 | 0 | yes | 0x0.0p+0 | 0x0.0p+0 | 0x0.0p+0 | 0x0.0p+0 |
| low_aspect_ratio_DEMO | A0 | 2 | 8 | 1 | 0 | yes | 0x0.0p+0 | 0x0.0p+0 | 0x0.0p+0 | 0x0.0p+0 |
| low_aspect_ratio_DEMO | A1 | 1 | 15 | 0 | 0 | yes | 0x1.ad17b67239f49p-4 | 0x1.a621cc5cabcc8p-4 | 0x1.ad17b67239f49p-4 | 0x1.a621cc5cabcc8p-4 |
| low_aspect_ratio_DEMO | A1 | 2 | 15 | 0 | 0 | yes | 0x1.2cdce94f65769p-3 | 0x1.24c92dd10e577p-3 | 0x1.2cdce94f65769p-3 | 0x1.24c92dd10e577p-3 |
| st_regression | A0 | 1 | 9 | 2 | 0 | yes | 0x1.9e44b1da8552dp-29 | 0x1.211b7a2189fc0p-29 | 0x1.9e44b1da8552dp-29 | 0x1.211b7a2189fc0p-29 |
| st_regression | A0 | 2 | 9 | 1 | 0 | yes | 0x1.05028b3bcc6bfp-27 | 0x1.6c4dec4c0f592p-28 | 0x1.05028b3bcc6bfp-27 | 0x1.6c4dec4c0f592p-28 |
| st_regression | A1 | 1 | 16 | 1 | 0 | yes | 0x1.fabf584472547p-3 | 0x1.3cec1f486b6d0p-3 | 0x1.fabf584472547p-3 | 0x1.3cec1f486b6d0p-3 |
| st_regression | A1 | 2 | 16 | 1 | 0 | yes | 0x1.e15dc1afec083p-3 | 0x1.ccd4e2d6e3fcap-4 | 0x1.e15dc1afec083p-3 | 0x1.ccd4e2d6e3fcap-4 |
*n = 12 (pairs of runs, one per ruler).*

**`the seed set — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: counts of seeds.  A row is this configuration.  A column is the size of the one population every optimisation-phase table on this configuration is over, or a per-arm count of the seeds on which the optimiser was called more than once.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the arms here are BR, B0, B1, B3 at seeds 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24.  Construction: a seed is in the set when every arm present reached an accepted optimum (status ok AND the output file's ifail == 1); the retried count is computed from attempts[] and never from a stored flag.  This is one seed-complete arm group of the source — the plan's construction assumes every arm at every seed, which a gate's runs do not guarantee.  The seeds outside the set are the failure table, published beside. n = 25 (distinct seeds run on large_tokamak_nof). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of seeds.  A row is this configuration.  A column is the size of the one population every optimisation-phase table on this configuration is over, or a per-arm count of the seeds on which the optimiser was called more than once.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the arms here are BR, B0, B1, B3 at seeds 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24.  Construction: a seed is in the set when every arm present reached an accepted optimum (status ok AND the output file's ifail == 1); the retried count is computed from attempts[] and never from a stored flag.  This is one seed-complete arm group of the source — the plan's construction assumes every arm at every seed, which a gate's runs do not guarantee.  The seeds outside the set are the failure table, published beside.*
| arms | arm_names | seeds_offered | n | seeds | configuration_invalid | retried |
|---|---|---|---|---|---|---|
| 4 | BR · B0 · B1 · B3 | 25 | 22 | 0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 22, 23, 24 | 3 | BR 0 · B0 0 · B1 0 · B3 0 |
*n = 25 (distinct seeds run on large_tokamak_nof).*

**`the seed set — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B3`**

*Caption: units: counts of seeds.  A row is this configuration.  A column is the size of the one population every optimisation-phase table on this configuration is over, or a per-arm count of the seeds on which the optimiser was called more than once.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the arms here are BR, B0, B1, B3 at seeds 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24.  Construction: a seed is in the set when every arm present reached an accepted optimum (status ok AND the output file's ifail == 1); the retried count is computed from attempts[] and never from a stored flag.  This is one seed-complete arm group of the source — the plan's construction assumes every arm at every seed, which a gate's runs do not guarantee.  The seeds outside the set are the failure table, published beside. n = 25 (distinct seeds run on low_aspect_ratio_DEMO). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of seeds.  A row is this configuration.  A column is the size of the one population every optimisation-phase table on this configuration is over, or a per-arm count of the seeds on which the optimiser was called more than once.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the arms here are BR, B0, B1, B3 at seeds 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24.  Construction: a seed is in the set when every arm present reached an accepted optimum (status ok AND the output file's ifail == 1); the retried count is computed from attempts[] and never from a stored flag.  This is one seed-complete arm group of the source — the plan's construction assumes every arm at every seed, which a gate's runs do not guarantee.  The seeds outside the set are the failure table, published beside.*
| arms | arm_names | seeds_offered | n | seeds | configuration_invalid | retried |
|---|---|---|---|---|---|---|
| 4 | BR · B0 · B1 · B3 | 25 | 11 | 0, 1, 5, 6, 9, 11, 12, 13, 15, 18, 19 | 13 | BR 12 · B0 10 · B1 10 · B3 10 |
*n = 25 (distinct seeds run on low_aspect_ratio_DEMO).*

**`the seed set — st_regression — campaign_optimisation · BR·B0·B3`**

*Caption: units: counts of seeds.  A row is this configuration.  A column is the size of the one population every optimisation-phase table on this configuration is over, or a per-arm count of the seeds on which the optimiser was called more than once.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the arms here are BR, B0, B3 at seeds 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24.  Construction: a seed is in the set when every arm present reached an accepted optimum (status ok AND the output file's ifail == 1); the retried count is computed from attempts[] and never from a stored flag.  This is one seed-complete arm group of the source — the plan's construction assumes every arm at every seed, which a gate's runs do not guarantee.  The seeds outside the set are the failure table, published beside. n = 25 (distinct seeds run on st_regression). Population: the campaign runs at `57dc0c14` — the source named in the caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before execution approval and are excluded by kind; see the §4 heading for the audit position, the ruler and the instrument.*

*Caption: units: counts of seeds.  A row is this configuration.  A column is the size of the one population every optimisation-phase table on this configuration is over, or a per-arm count of the seeds on which the optimiser was called more than once.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the arms here are BR, B0, B3 at seeds 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24.  Construction: a seed is in the set when every arm present reached an accepted optimum (status ok AND the output file's ifail == 1); the retried count is computed from attempts[] and never from a stored flag.  This is one seed-complete arm group of the source — the plan's construction assumes every arm at every seed, which a gate's runs do not guarantee.  The seeds outside the set are the failure table, published beside.*
| arms | arm_names | seeds_offered | n | seeds | configuration_invalid | retried |
|---|---|---|---|---|---|---|
| 3 | BR · B0 · B3 | 25 | 22 | 0, 1, 2, 3, 4, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 18, 19, 20, 21, 22, 23, 24 | 1 | BR 5 · B0 3 · B3 2 |
*n = 25 (distinct seeds run on st_regression).*

## 5. Discussion

*Written 2026-09-14 by the orchestrating session from §4 only — the campaign population, 949
records at `57dc0c14`, rendered by `--plan-tables` from the stage records at `004eb06b` after
A75 (campaign-tally-source). Every number below is a cell of §4; the table it comes from is named.
Denominators: 25 seeds offered per arm per configuration; Phase A tables are over 25 runs per arm
(every evaluation finished), Phase B tables over the seed set on which every arm converged — 22 on
`large_tokamak_nof`, **11** on `low_aspect_ratio_DEMO`, 22 on `st_regression` (§4.3 "the seed set").
The pre-declared expectations are §3.4 and §3.5's; where a measurement refutes one it is named so.*

### 5.1 What each rung measured, per configuration

**`A0p → A1` / `A0 → A1` — the partitioning, one evaluation (RQ1; §4.2 "cost per call",
displaced regime).** The partitioned architecture costs **0.56 / 0.58 / 0.50** of the flat arm's
model-node evaluations per call (pooled; medians 0.571 / 0.571 / 0.492) on the large tokamak, the
low-aspect-ratio machine and the spherical tokamak, worse on 0 of 25 seeds each. V2's context
figures were 0.522 / 0.568 / 0.502: reproduced to within a few hundredths, on a different entry
construction. In the stencil regime the saving is smaller — **0.62 / 0.64 / 0.58** forward,
0.64 / 0.66 / 0.56 backward — because a one-variable displacement from a fixed point leaves the flat
arm little to iterate; the plan's transfer statement (§3.4) uses both regimes and both are on the
page. Matched accuracy holds and is not a near thing: at the audit position the restricted maximum
scaled residual is **identical** for `A0p` and `A1` on both pulsed configurations (median 3.8e-10,
p90 1.7e-8 on the large tokamak; exactly 0 on every run of the low-aspect-ratio machine) and for
`A0` and `A1` on the spherical tokamak (5.4e-9 / 2.0e-8), so the F = 10 similarity rule of §3.4
check 1 is met with a factor of 1. The whole-state audit beside it is large for `A1` (median 2.4,
0.18, 0.26): those are the components the configuration's once-per-run deferred nodes write, which a
single evaluation of the reduced map does not update, excluded from the restricted statistic by the
derived membership rule and published so the exclusion can be seen.

**`A0 → A0p` — ownership of the burn time (§4.2 "ownership rung").** Pinning the burn time to a
constant costs nothing measurable per call (pooled 0.93 / 0.98, median 1.00, worse on 0 seeds) and
leaves the declared inconsistency: a burn-time residual at exit of 155 s / 526 s median (6.3 % /
5.3 % relative), the rung's own statistic, published per run and never pooled into a cost.

**`AR → A0` — the stopping rule (RQ4; §4.2 "cost per call" and "matched accuracy").** Upstream's
objective/constraint test at its two-pass floor is cheaper per call than the coupling-state test at
τ on two configurations (0.97 and 0.84 pooled against `A0`; equal on the low-aspect-ratio machine,
where both stop after exactly five sweeps on every seed) — and it stops **further from the fixed
point**: `AR`'s restricted residual is 2.6e-8 / 1.5e-7 median against `A0`'s 5.0e-10 / 5.4e-9 on the
large and spherical tokamaks, a factor of 30–50, and 0 against 0 on the low-aspect-ratio machine.
That is what the predicate-matched control is a control *for*: `B0` is `BR` with a stopping rule
that reaches a stated accuracy, so that every rung above it compares arms at matched accuracy.

**`B0 → B1` — ownership in the optimisation, and the output-time loop (§4.3 "cost", "iteration
multiplier", "the lift closed").** Lifting the burn time to the optimiser and dropping upstream's
output-time loop costs **1.008 / 0.692** pooled (medians 1.015 / 0.805) on the two pulsed
configurations — no saving on the large tokamak, a third off on the low-aspect-ratio machine, where
it also shortens the optimiser's path (summed iterations 0.81 median, 0.70 sum ratio). The output
loop's own cost is exactly two sweeps per run in `BR` and `B0` and zero in `B1`/`B3` (§4.3
"per-sweep overhead"), so it is not what moves the ratio. The lift closes: constraint 93's residual
at every accepted optimum is 1.7e-5 s / 5.5e-6 s median (2.3e-9 / 6.7e-10 relative), in the
equality block.

**`B1 → B3` and `B0 → B3` — the partitioning inside the optimisation (RQ2; §4.3 "cost").** The
headline: `B3` costs **0.640 / 0.450 / 0.533** of `B0`'s solve-phase model-node evaluations pooled
(medians 0.645 / 0.524 / 0.591; worse on 0 / 2 / 0 seeds), against V3's pre-declared context
0.64 / 0.45 / 0.53 — the same numbers to two decimals, from a rebuilt harness, a different entry
construction and 25 seeds. Without the retried seeds the low-aspect-ratio ratio is 0.66 pooled
(0.54 median), the reading §3.5 asked for beside the pooled one. `BR → B0` reads 0.976 / 1.030 /
1.197 pooled against the expected 0.98 / 1.03 / 1.16. The `ε = 1` expectation holds where it was
pre-declared: the summed-over-attempts iteration median is identical for `B1` and `B3` on both pulsed
configurations (1.000 and 0.8125), so the partition changes what an evaluation costs and not how many
the optimiser takes. The dispatch runs 2.7 / 2.1 / 2.8 times as many sweeps per run in `B3` (block
sweeps, each over a third of the map), which is the mechanism, not a cost.

**Refuted or qualified expectations, named.** (a) **Same optimum (check 1) FAILs on the
low-aspect-ratio machine**: `B0 → B1` and `B0 → B3` both read a paired relative objective difference
of 4.1e-7 median (passes) and **2.15e-6 p90 (fails the 1e-6 floor)**, with 1 hop of 11 and 2 pairs
below cluster resolution; `BR → B0`'s yardstick is 2.0e-13. Since `B1` and `B3` read the same `r`
to every digit, the difference sits on the ownership rung `B0 → B1` — the lifted formulation lands
on a slightly different optimum on 2 of 11 seeds — and not on the partition. On the large tokamak
(2.8e-11 / 4.6e-11) and the spherical tokamak (3.5e-13 / 3.5e-9) check 1 PASSes with margin.
(b) **The low-aspect-ratio seed set is 11 of 25.** Thirteen seeds are configuration-invalid: 2
crashed in every arm (§5.7), and the rest failed to converge in at least one arm, with 10–12 retried
seeds per arm. Every low-aspect-ratio ratio above is over n = 11 and says so.

### 5.2 The transfer (RQ3)

Phase A's per-call ratio against the realised Phase B ratio, pooled: 0.56 → 0.64 (large tokamak),
0.58 → 0.45 (low aspect ratio), 0.50 → 0.53 (spherical). The transfer factor is 1.14, 0.78 and 1.06:
Phase A under-predicts the saving on one configuration and over-predicts on two, by up to a fifth.
The factor decomposition that §3.4 declares — per-evaluation cost × evaluation count × the entry
regime × ownership — is on the page (the stencil-regime per-call ratios 0.62–0.66 sit closer to the
realised 0.64 on the large tokamak than the displaced-regime 0.56 does; the iteration multiplier is 1
on two configurations and 0.81 on the third), but attributing the residual to one factor is issue
**I-17**, which the user has reserved. What the campaign settles is that the transfer is not
systematic in sign, exactly as V3's assessment (§2.2) said, and that Phase A's displaced-regime ratio
is a predictor good to ±20 % here.

### 5.3 The stopping rule (RQ4)

Covered in §5.1 (`AR → A0`): upstream's test stops 30–50× further from the coupling-state fixed
point on two configurations and at the same place on the third, for a per-call saving of 3–16 %.
`BR → B0` in the optimisation reads 0.98 / 1.03 / 1.20 — the coupling-state test costs up to a fifth
more on the spherical tokamak, where `BR` also retries more seeds (5 against 3). The control is
therefore a control for *accuracy*, bought at that price, and the headline ratios are stated against
it, never against `BR` (user, 2026-09-11).

### 5.4 The trust step (RQ5)

Not an arm of V4 (`B2` removed, §3.2). A43 (st-trust-gap) answered it on V3's records: a single
schedule pass reaches the flat fixed point bit for bit once the blocks are solved exactly. The
campaign's `B3` exit audit is consistent with that: 0 components above τ at the accepted point on
every converged run on every configuration (§4.3 "achieved accuracy"), with the spherical tokamak's
`B3` restricted median 7.5e-12 against `B0`'s 4.9e-14 — three orders larger, both far under
τ = 1e-6.

### 5.5 The per-sweep overhead

Counted, not timed (§4.3 "per-sweep overhead"). `B3` evaluates the convergence predicate about 2.3×
as often as `B0` per run (4 839 against 2 069 tests on the large tokamak at seed 0) over widths of
239 against 840 components, so the components compared per run are **fewer** (1.16 M against 1.74 M).
The counted overhead cannot be the source of a wall-clock gap; on the spherical tokamak 10.8 % of
`B3`'s sweeps visit the empty `PULSE` block (I-20a), disclaimed where it bears and costing no model
evaluation.

### 5.6 The predicate trial

`frozen` against `mixed` (§4.2 "the predicate trial"): on every pair tried the two rulers' runs are
bit-identical and no decisive pass changed its verdict (0 verdicts changed over 9–15 predicate
evaluations per run). The `mixed` ruler reads the same run's residual smaller (by up to 8× on the
large tokamak's `A1`), so a threshold stated on it would be a looser threshold; the experiment's
τ is stated on `frozen` and nothing in §4 depends on the choice. The trial changes nothing here and
records that a future revision adopting `mixed` must restate τ.

### 5.7 Robustness events, reported without a robustness claim

Twenty-eight of 275 optimisations crashed (§4.3 "failure taxonomy"), all with PROCESS's own
`RuntimeError: Failed to converge after 50 iterations, value is nan` from a model-internal Newton
solve at a displaced start. On the large tokamak seeds 5, 20 and 21 crash in **all four arms** —
configuration hardness, dropped paired. On the low-aspect-ratio machine `BR` crashes on 2 seeds,
`B0` on 2 plus 2 unconverged, `B1` and `B3` on 2 plus 3 unconverged; the unconverged ones are the
block solver's own exit (`ModuleSolveFailure: block FLAT / M1 did not converge in 20 sweeps`,
`current_drive.eta_cd_dimensionless_hcd_primary` at `inf`), and on the same variable `BR` reaches
the audit with an infinite residual on 2 runs. The spherical tokamak loses no seed to a crash. The
intervention arms therefore fail on 1–3 more low-aspect-ratio starts than the incumbent, on a
variable the incumbent also cannot hold finite; the plan makes no robustness claim and this report
makes none.

### 5.8 Threats to validity that survived the design

- **The objective/structure confound (decision (b))** stands: `B1`/`B3` optimise the lifted
  formulation, `B0`/`BR` the original. §5.1(a) shows it bites on the low-aspect-ratio machine at p90.
- **Small denominators where a configuration is hostile:** n = 11 on the low-aspect-ratio machine.
  Its ratios are the least certain in this report and its same-optimum check is the one that fails.
- **Location non-identification:** correctness is gated on `norm_objf` and the feasibility audit
  (D6), never on iteration variables; two optima closer than 1e-5 relative are "below resolution",
  and 2 such pairs are counted on the low-aspect-ratio machine.
- **The prime's excluded cost:** `n_arrangement_method_calls` is 13 per evaluation in `A1` and
  117 281 / 157 504 / 280 776 per optimisation in `B3` (§4.3 "cost", column "arrangement·method
  calls"), stamped beside every node-call table and never pooled into it (D19). A reader who
  weights the prime as a model node must add it; it is not a model node.
- **The written file** carries a post-write value of `tfcoil.insstrain` 0.7 % off the accepted
  state in every Phase B arm (A67, I-21); no acceptance quantity reads it.

## 6. Conclusion

*Each research question of §1.2, per configuration (large tokamak / low aspect ratio / spherical
tokamak), with its number, denominator and pre-declared verdict.*

**RQ1 — per-call cost.** At matched achieved accuracy (identical restricted residuals, factor 1
against the F = 10 rule), one MDA solve under the partitioned architecture costs **0.56 / 0.58 /
0.50** of the flat arm's model-node evaluations from a displaced entry (n = 25 per arm, worse on
0 seeds) and 0.62 / 0.64 / 0.58 from a stencil point. **Accepted.**

**RQ2 — end-to-end cost and correctness.** Inside a full optimisation the partitioned architecture
costs **0.640 / 0.450 / 0.533** of the control's solve-phase model-node evaluations (pooled; n = 22 /
11 / 22 converged seeds), with the optimiser's summed iteration count unchanged (median ratio 1.00 /
0.81 / 1.00 — **accepted** against ≤ 1.05) and the lifted constraint closed. **Same optimum:
accepted** on the large and spherical tokamaks (paired relative objective difference ≤ 4.6e-11 /
3.5e-9 at p90), **not accepted** on the low-aspect-ratio machine (2.15e-6 at p90 against the 1e-6
floor, 1 hop of 11), where the difference sits on the ownership rung and not on the partition.

**RQ3 — transfer.** Phase A's displaced-regime per-call ratio predicts the realised optimisation
ratio to within 1.14 / 0.78 / 1.06; the transfer is not systematic in sign. The attribution to one
factor is I-17, reserved by the user; the terms it needs are on the page.

**RQ4 — the stopping rule.** Upstream's objective/constraint test saves 3–16 % of model-node
evaluations per call against the coupling-state test at τ = 1e-6 and stops 30–50× further from the
fixed point on two configurations (identical on the third); in the optimisation the coupling-state
control costs 0.98 / 1.03 / 1.20 of the incumbent. The control buys stated accuracy at that price.

**RQ5 — the trust step.** Not measured by a V4 arm; A43's answer on V3's records stands and the
campaign's `B3` exit audits (0 components above τ on every converged run) are consistent with it.

**The sentence the experiment licenses about §1.2:** *with every physics and engineering model
byte-identical to upstream, rearranging the driver alone — solving the models in three blocks with
the burn time owned by the optimiser — reaches the same accepted optimum on two of three
configurations at 0.53–0.64 of the model evaluations, and a different optimum within 2.2e-6 relative
on the third at 0.45; the per-call saving of roughly half measured without the optimiser transfers
to the optimisation to within a fifth.*

**The sentence it does not license:** that the partitioned architecture is more robust, or that it
would save wall-clock time — no conclusion here rests on a timing, and on the hostile configuration
the intervention arms fail on more displaced starts than the incumbent.

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
- 2026-09-11 — **A53 (harness-tally) merged — H6** (`d98f602a`): every declared construction of §3.4–§3.6 is one documented
  function; no table without a caption and a denominator; the tally reproduces the previous revision's 270 published cells
  over the twenty reference runs; the record fields carrying retired mechanism words renamed (the committed reference keeps
  its bytes). §4's placeholder tables are fillable by `--measure tally_evaluation` / `--measure tally_optimisation` and are
  filled once at the final tip. The empty-visit sweep share on the gate population is 0 / 0 / 6.67 %; disclaimers quote the
  share measured on their own population. At `after_run` the restricted audit maximum is exactly 0 on all 14 reference
  records against ~7e-3 at the declared position — the A61 instrument artefact seen from the other side.
| 2026-09-11 | **A62 (exit-audit-restore) merged (`a3407d5d`; D25 discharged).** §3.3's implementation note gains the landing: whole-structure snapshot and derived restore at both audit positions, `numerics` held back by rule, the instrument stamped per record; 0 of 31 declared-position records above τ, `insstrain` exactly `0x0.0p+0`. Every published exit-audit residual changes with the instrument; a residual table must name the instrument beside the audit position and the ruler (A53's caption rule, extended). GR compares 256 of the 270 reference values. §4's tables stay placeholders until the smoke fills them at the final tip. |
| 2026-09-11 | **A54 (harness-analysis) merged (`72c343d1`).** Every §4 cell now has a second, independent implementation behind gate `recomputation` (1 901 compared, 0 mismatched over the gate population). The two accuracy tables gain a column, *with a restricted statistic*, beside `n (runs)`: `n` counts the runs a row is over and a run whose audit carries no restricted block is counted and named, never dropped from the denominator. §4's tables are still filled once, at the final tip, by the smoke. |
| 2026-09-11 | **A55 (harness-smoke) merged (`bfaee7ce`); the implementation is complete.** §4 is rendered by `harness/plan_tables.py` from the stage records at the commits the marker names: the **gate population**, 24 PASS / 0 FAIL / 139 of 139 teeth, 131 tables, 3 620 cells; the campaign fills it again after execution approval. `--smoke` runs the campaign's own chain at one seed on `st_regression`. Open before the campaign: **D26** (how `AR` is entered in Phase A — awaiting the user), I-21, I-22. This header stays DRAFT · NOT APPROVED until the user's dated approval edit and the `EXECUTION_APPROVED` flip in one commit. |
| 2026-09-11 | **A63 (stage-provenance) merged (`52264b53`).** §4.1 gains the `stage_provenance` row and reads 25 PASS / 0 FAIL / 147 of 147 teeth; `artifacts_check` reads 93 with its two lifted-input rows pending in that worktree. §4 is now guarded: `--plan-tables` refuses to render from a stage record the verdicts have outrun, and `--plan-tables check` compares this section with the records without writing. |
