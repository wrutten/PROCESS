# MDA Partitioning Experiment V4 — Experiment Report

> **Document status (V5 copy)** — **V4's TEXT, PENDING V5's REWRITE.** This file is the V4 report
> copied whole into `MDA_partitioning_experiment_v5/` by task A94 (v5-copy) and is **not** V5's
> report: every number, table and conclusion below is V4's, measured on V4's records at V4's commits,
> and nothing in it has been re-rendered or re-run in this folder. V5's report is the four-part
> document of the V5 plan §8 (method; the paper tables included verbatim from the one generator,
> `harness/measurement/paper_tables.py`; one short findings section per rung; the change log — under
> 600 lines), to be written when V5's campaign has run. The machinery this text cites as rendering it
> — `harness/measurement/plan_tables.py`, the companion file `RESULTS_TABLES_FULL.md`,
> `--plan-tables`, the second implementation and gate `recomputation` — was removed from this copy
> under V5 list item 10 by task A98 (v5-reporting-trim), 2026-09-29; the citations below are history.
> Read V4's own header, which follows, as V4's.

> **Document status** — **EXECUTED AND REPORTED, 2026-09-14.** One document carries the whole
> experiment: §1–§3 are the **plan as approved** — hypothesis, background and pre-registered method,
> written 2026-09-10 and changed only by the dated amendments the text and Appendix C record
> (D24–D27); §4 is the **results as conclusions**, hand-written from the numbered tables of
> **Appendix D**, which is rendered from the campaign's records by
> `harness/measurement/plan_tables.py` and never typed by hand (since 2026-09-15, task A79
> (report-captions): the tables moved from §4 to the appendix, every table numbered `Table D.n`
> with one caption of a few lines, the full result matrices in the generated companion file
> [`RESULTS_TABLES_FULL.md`](RESULTS_TABLES_FULL.md) as `Table F.n`); §5 and §6 are the
> **discussion and conclusion**, written from the rendered tables alone; **audited sentence by
> sentence against the tables on 2026-09-15 by task A80 (report-accuracy-audit)**, whose corrections
> are one dated Appendix C entry and which closed issue I-26 (the check-2 evaluation column). The file was
> `EXPERIMENT_PLAN.md` until 2026-09-15, when the user had it renamed to what it had become (*"rename
> the PLAN file to REPORT"*); the superseded draft header is readable at `3abea2c6` and is summarised
> in Appendix C.
>
> **Arm names (2026-09-15).** The arms are `AR / A0 / A1 / A2` (one evaluation) and `BR / B0 / B1 /
> B2` (one optimisation), so that the two phases read rung for rung — reference, flat control,
> burn-time ownership, partition — at the user's ruling (*"rename A0p and A1 to A1 and A2, and B3 to
> B2 … so the naming of the rungs reflects the parallelism in the switch matrix"*; task A78
> (arm-renames)). The names were changed throughout this document, §4 by re-rendering; no number
> changed. **The campaign's records were not re-made and carry the names of their day** — the table
> `harness/core/records.py::RECORDED_ARM_NAMES` is the one place that says which is which, applied
> where a record is read. V3's `B2` was a different arm (its joint-test arm, removed in V4, §3.2) and
> is always written "V3's `B2`" here; Appendix C's entries before this date keep their day's names.
>
> **Approval record:** **APPROVED FOR EXECUTION, 2026-09-14** (the user: *"You can run the
> experiment"*), after the D27 rerun of every gate on the final harness — 30 PASS, 152/152 teeth,
> GR 256/256, G1 byte-neutral, at `03f72479`; `EXECUTION_APPROVED` flipped at the approval commit
> `57dc0c14`. The campaign was pressed from the button (`experiment_runner.py --campaign`) at that
> commit: **949 records** (921 ok, 28 not ok — 20 crashed in PROCESS's own Newton solve and 8 whose
> coupling-state loop hit its 20-sweep cap, both stamped `crashed` by the harness and split by Tables
> D.61–D.63; "28 crashed" until A80's audit, 2026-09-15), stamped `campaign`, kept untracked at
> `arch_surgery/idf_probe/runs/campaign_57dc0c14/`.
>
> **Scope.** Base commit `c0ae5b28` throughout; the physics is frozen — V4 contains no change under
> `process/models/`. How the measurement harness is built is the implementation plan's subject
> ([`../docs/plans/V4_HARNESS_IMPLEMENTATION_PLAN.md`](../docs/plans/V4_HARNESS_IMPLEMENTATION_PLAN.md));
> §3.5 says *what* the harness must provide, not how. The candidate list this design selected from is
> [`../docs/plans/V4_IMPROVEMENT_LIST.md`](../docs/plans/V4_IMPROVEMENT_LIST.md); the V3 plan and report
> are in [`../MDA_partitioning_experiment_v3/`](../MDA_partitioning_experiment_v3/). **V2's and V3's
> directories are frozen as the record of what ran; nothing in them is edited by V4.**
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
  the flat one? *(Phase A, `A1 → A2`, with the ownership rung `A0 → A1 → A2`.)*
- **RQ2 — end-to-end cost and correctness.** Inside a full optimisation, how many model-node
  evaluations does the partitioned architecture cost against the flat baseline, at the same
  optimum, with the optimiser's iteration count bounded? *(Phase B, `B0 → B2` per rung.)*
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
  the blocks are solved exactly. No V4 arm measures it; V3's joint-test arm — V3's `B2`, not today's — is removed, §3.2.)*

### 1.3 Terms used throughout

**Table 1.** *The vocabulary of this document, one row per term; the harness README §3 is the
fuller table.*

| term | meaning here |
|---|---|
| **node** | one model call site in `call_models` (e.g. `physics`, `build`, `costs`); the unit of cost. A **node call** is one execution of one node |
| **sweep** | one pass over a node sequence — the whole loop (flat) or one block's nodes (partitioned) |
| **coupling state `y`** | the measured set of state fields written by in-loop models (840 / 846 / 827 components on the three configurations); the fixed-point iteration converges this |
| **τ** | the convergence tolerance on `y`, per component, scaled: `max_i |Δy_i| / s_i < τ`, τ = 1e-6, `s_i` a measured scale (§3.6 says which) |
| **flat MDA** | one loop over every in-loop node, stopping on `y` at τ (arms `A0`, `B0`) |
| **partitioned MDA** | three block solves — M1 physics, M2 coils, M3 plant — each iterated to its own fixed point at τ, run in feed-forward order; the block membership comes from a validated dependency-structure matrix (DSM) of the code |
| **block loop** | in the partitioned MDA, each block is iterated to its own fixed point at τ. V3 also offered a *joint test* over all blocks that repeated the whole schedule if anything still moved (V3's arm `B2` — removed in V4; today's `B2` is a different arm, §3.2 — and the words "outer"/"inner" loop); V4's partitioned arms run the schedule **once**, so there is one kind of loop and **one tolerance for every converger** (D23) |
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

**V3 (2026-09-07).** Added the prime to the intervention and corrected the apparatus. *(This subsection quotes V3's results under **V3's arm names**: V3's `A1` and `B3` are today's `A2` and `B2`, V3's `B2` is the removed joint-test arm, V3's `R` is today's `BR` — §3.2 and Appendix C, 2026-09-15.)* Results
that V4 inherits as prior context (V3 report, §4–§8; all at `c0ae5b28`, campaign commit
`362c0b47`):

- **The prime closes the `FirstWall → Build` carrier.** Phase A's similarity check failed for
  the prime-free block arm by five to six orders and passed for the primed one on all three
  configurations, at zero additional node calls (V3's `A1u → A1` ratio exactly 1.0000). From V4 the
  prime is part of the intervention, not a separate question (improvement-list item 0).
- **End-to-end, the partitioned architecture executes 36–55 % fewer model-node evaluations**:
  V3's `B3/B0 = 0.639 / 0.450 / 0.533` (nof / lad / st) over the identical-converged seed sets,
  with the optimiser's iteration bound (median paired ratio ≤ 1.05) passing on every
  configuration and every accepted pair.
- **The stopping rule is not free.** `R → B0` costs 0.976 / 1.028 / 1.155 in node calls.
- **Same optimum: passes on nof; fails on lad at the p90 by a factor 1.26 and localises to the
  lift rung `B0 → B1`; on st fails all-pairs and passes within cluster** on a four-attractor
  configuration. Check 1 measures optimality, not location — objectives agree to 11–13 digits
  while design points differ by up to 44 % / 100 %, and upstream's own stopping-rule change
  relocates the point as much.
- **The node-call win does not reach wall clock**: V3's `B3` is 0–15 % slower despite far fewer node
  evaluations, and a non-node-proportional cost term must exist (V3 §7–§8). Timings are
  never evidence in this project; the term is to be *counted* (item 3). *(As built, 2026-09-15: the
  counting is §5.5 and that is where this line ends — **the non-node cost term and wall clock are out
  of scope for V4** by ruling D29 (2); the study is an existence proof in node calls, for applications
  dominated by node-call runtime, not a claim about run time.)*
- **The trust step is free on the pulsed configurations and not on st**: V3's `B2 → B3` (its joint-test arm to its partitioned arm) iteration
  counts are identical seed for seed on nof and lad; on `st_regression` 7 of 23 both-converged
  seeds differ, V3's `B3` worse on 6 (summed 501 → 587). The outer loop still does work there that
  the prime does not account for — investigation A43.
- **The Phase A → Phase B transfer is not systematic.** V2's uniform over-prediction became
  +22.6 % / −20.7 % / +6.3 % in V3 (converged sets); lad reversed sign. Candidate mechanisms
  named in V3: the entry regime (Phase A enters 100× further from the fixed point than any
  finite-difference call), and the ownership of the burn time (Phase A pins it to a constant
  displaced from consistency by 155 s / 526 s at the median; Phase B lifts it into the
  optimiser, and on lad that quantity *is* the objective) — investigation A44.

### 2.2 What V3's own assessment found wrong with its design

Read from the V3 report §8 and the improvement list; each becomes a method change in §3:

1. Phase A had **no reference arm** and **no rung for burn-time ownership** — V3's `A0 → A1` (today's `A0 → A2`) varied
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
cleared first, then set), and records the composed environment in every run record. In the
matrix, "committed" is the configuration's committed input file, never edited, and "lifted" a
derived copy of it differing in exactly three lines (§3.3); nodes not deferred run `per_sweep`; the
Phase A arms never reach the output path, so the output-time-loop row does not apply to them
(`n/a`). On `st_regression` (`k = 0`) the rows marked ⁺ are inactive: `A1` composes to `A0` and
`B1` to `B0`, and both are skipped and recorded as skipped.

**Table 2.** *The switch matrix: one column per arm, one row per switch. Phase A arms (`A*`) run
one evaluation, Phase B arms (`B*`) an optimisation; rows marked ⁺ apply on the pulsed
configurations only; `AR`/`BR` have every switch unset — PROCESS as shipped.*

| | **AR** | **A0** | **A1** | **A2** | **BR** | **B0** | **B1** | **B2** |
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

**V3's `B2` — the partitioned arm with the outer loop in verify mode, V3's joint-test arm — is removed and is not today's `B2`** (today's `B2` is the partitioned optimisation arm, V3's `B3`; the names were changed 2026-09-15, Appendix C) (user ruling
2026-09-10). V3 measured its verification pass triggering a third pass **zero** times in 91 888
calls across the three configurations (A43 (st-trust-gap), records stage), so as an arm it
measures nothing the uncharged exit audit does not; its only remaining role — detecting an
incomplete decomposition on `st_regression` — is A43's, on V3's records. **A43 (st-trust-gap) has since answered the question the removal left open:** on st a single
schedule pass reaches the flat fixed point *bit for bit* once the blocks are solved exactly (0 of 805
components differ at inner τ = 1e-14, on every traced seed); the difference between V3's `B2` and V3's `B3` was the blocks'
own inner-solve slack below τ (max 3.3e-9, in M2 and M3, none in M1), and 0 of its 40 movers has a
loop-carried cross-block edge in the dependency export. **`st_regression` stays in V4.** What the
verification pass bought was sub-τ accuracy, and the inner tolerance buys it instead — decision (g).

*The switches, for the record — the names the copy reads since DR1 (A56 (driver-renames), 2026-09-10; harness plan §11.2), the V3 name in parentheses; every retired name raises if set:* `PROCESS_ARCH_MDA = flat | partitioned` (was `MODULE_SOLVE = flat_state | per_module`; `OUTER` retired — `partitioned` runs its block schedule once); `PROCESS_ARCH_ARRANGEMENT_NODE = build_after_physics` (was `SEQUENCE`); `PROCESS_ARCH_ARRANGEMENT_METHOD = fw_geometry` (was `PRIME`); `PROCESS_ARCH_DEFER_PER_CALL = feedforward | feedforward_lifted` (was `HOIST`); `PROCESS_ARCH_DEFER_PER_RUN = <artifact>` (was `POST_SOLVE`); `PROCESS_ARCH_BURN_TIME_OWNER = loop | constant:<hex> | optimiser` (was `LIFT = burn_time` and `PIN_BURN_TIME = <hex>`); `PROCESS_ARCH_TAU` (`INNER_TAU` retired, D23); `PROCESS_ARCH_COUPLING_STATE` and `PROCESS_ARCH_WRITE_SETS` (were `YSTATE`, `WRITESET`) — the two committed per-configuration artifacts that define `y` and the per-block write sets. `PROCESS_ARCH_OUTPUT_LOOP = upstream | none` landed with A57 (driver-output-path), 2026-09-10; `PROCESS_ARCH_PREDICATE = frozen | mixed` with A59 (driver-predicate-mode), 2026-09-11 — the pending list is empty, and the self-check says so in its own words (*"0 registry entries with no driver name"*).

**The rungs, and what each isolates.** Adjacent arms differ by one named thing; the ladder is
declared, and the harness refuses an arm pair whose declared difference does not match its
composed environments. Every Phase A arm has a Phase B twin and every Phase B arm a Phase A one,
so a Phase A ratio may be read against its Phase B twin.

**Table 3.** *The rungs: one row per rung; the Phase A and Phase B steps of a row are the same
switch changes, with one declared exception — the output-time loop on the ownership rung, which
exists in Phase B only.*

| Phase A step | Phase B step | isolates | acceptance / role |
|---|---|---|---|
| `AR → A0` | `BR → B0` | **the stopping rule** — upstream's objective/constraint test at its two-pass floor vs the coupling-state test at τ | reported, never accepted on (a comparison at unmatched accuracy by construction — §3.6) |
| `A0 → A1` | `B0 → B1` | **burn-time ownership** — the loop vs a constant (A) / the optimiser (B); *the one rung where the phases differ in kind* — and, in Phase B only, **the output-time loop** (`upstream → none`), placed on this rung deliberately: it is the rung already declared to differ in kind between the phases, so the headline rung `B1 → B2` keeps a switch set identical to `A1 → A2`. *(Wording completed 2026-09-10 after A47 (harness-skeleton) found the row named only ownership; the matrix is unchanged. The output-time loop's sweeps are counted per run and published as their own column, so neither rung's attribution carries them silently.)* | Phase A: cost and audit at matched map; Phase B: checks 1–3 |
| `A1 → A2` | `B1 → B2` | **the partitioning intervention** — block solves + arrangement (node and method) + both deferrals + one pass over the block schedule | Phase A headline (RQ1); Phase B headline via `B0 → B2` (RQ2); `ε = 1` pre-declared on the pulsed configurations |

`B0 → B2` is the designed-architecture comparison and the Phase B headline; `BR → B2` is the
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

**Ownership rung `A1` / `B1`** (item 1c; V3's `B1`). Flat solve plus the burn time taken out
of the loop, nothing else. In Phase A the owner is a **constant**: `A1` pins the burn time at
the seed's perturbed value — the same hex value `A2` receives — so `A1` and `A2` solve the
same reduced map and their exit states are comparable without exclusion. In Phase B the owner
is **the optimiser**: the lifted input file adds iteration variable 178 and equality constraint 93.
With deferral off the `pulse` node still executes in `A1` (it just stops computing the burn
time), so `A0 → A1` changes the owner without changing the node set.

**Partitioned arms `A2` / `B2`.** Three block solves M1 → M2 → M3 in feed-forward
order, each iterated to its own fixed point at τ (inner cap 20 sweeps; reaching it is a
refusal, not a budget); `build` resequenced after `physics`; the prime at every sweep head;
`per_call` and `per_run` deferral by the measured routing rule; the burn time lifted. Both run
**one pass over the block schedule** — what V3 called the outer loop in trust mode; the switch that chose it (`PROCESS_ARCH_OUTER`) is retired and the verified-schedule code removed (DR1, A56 (driver-renames), 2026-09-10). There are no prime-free
twins (item 0; V3 decision O5) and no verified-outer-loop twin (§3.2). **Their certificate of
convergence is the block solves' inner tolerance plus the uncharged exit audit at the handover
point** — there is no outer verification pass, so the inner tolerance is what sets the handover
accuracy, and it is **the same τ every converger uses (D23)**: the flat loop converges the whole coupling
vector to τ, each block loop converges its block to τ, and there is no second tolerance. A43
(st-trust-gap) measured the exchange rate should τ ever be tightened: at a single evaluation `B2`
with block loops at 1e-8 reproduces V3's removed two-pass joint-test arm (V3's `B2`) at 1e-6 to every digit of achieved
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
(`A2` therefore runs before driver change DR2 lands; only `B1` and `B2` wait on it). `B1` and
`B2` **do not run it**: their solve phase hands over a state it has already verified at τ, and
re-solving that state with a different loop before writing it out is a property of the
incumbent, not of the architecture. *(Keep-list corrected 2026-09-10 after A47 (harness-skeleton)
found the matrix and this sentence disagreeing on `A2`.)* Consequences, all binding: the replacement output
path calls `finalise` once on the accepted state (a driver change, §3.5); the rung table above
declares the difference; the exit audit is taken at the same position in every arm — at the
entry to `write_output_files`, before any output-time sweep — and the audit position is
recorded per run; and the one signal `MDA_Output` found by accident in V3 (three st `B2` runs
whose handed-over state was not MFILE-idempotent after two flat passes) is looked for on
purpose: the exit audit at the accepted point, per run, with the count of components above τ. *Implementation note, 2026-09-10 (orchestrator, at A50 (harness-run)'s merge):* the audit sweep mutates the state it measures, so it cannot run *at* that entry without handing the output path an audited state; the position is reached by a **snapshot** of the coupling state taken at the entry to `write_output_files`, with the residual computed after the run from the restored snapshot. The snapshot hook landed with A57 (driver-output-path), 2026-09-10: every campaign record carries `audit_position == audit_position_declared == entry_to_write_output_files`, the restore is proven bit-exact before the audit is taken, and the after-the-run position survives for the reproduction gate alone, whose compared values include a residual the previous revision measured there. First measurement at the declared position (seed 0, gate G9): on both pulsed configurations, in `B1` and `B2` alike, exactly one restricted component sits above τ — `tfcoil.insstrain`, ~7e-3 scaled — and none on `st_regression` (improvement list item 11). *Diagnosed 2026-09-11 (A61 (insstrain-diagnosis), `fd480aff`):* that residual is an artefact of the instrument, not of convergence — PROCESS's output path raises `tfcoil.n_rad_per_layer` 100 → 500 before the snapshot and the coupling-state restore does not put it back, so the audit swept a different mesh than the loop; 0 of 840/846/827 components differ between the loop's exit and the audited state, and restoring that one field gives exactly `0x0.0p+0`. **Ruling D25:** the snapshot and restore cover the whole data structure (a derived set, fields that cannot be restored counted and named), landing with A62 (exit-audit-restore) before the campaign; GR's compared set loses the inherited audit residual with its reason. The "one component above τ" reading is withdrawn: `B0` and `B2` converged to τ on every evaluation. *Landed 2026-09-11 with A62 (exit-audit-restore), `a3407d5d`:* the audit snapshots the whole data structure at both of the driver's positions and restores a derived set before its sweep, at both audit positions; one namespace (`numerics`, the optimiser's own accounting) is held back by a named rule and what it holds back is named per run; every record stamps the instrument. Measured at the declared position: 0 of 31 records have a component above τ, and `tfcoil.insstrain` sits at exactly `0x0.0p+0` in every arm on both pulsed configurations (new maximum 1.15e-11 on `large_tokamak_nof`, exactly 0 on `low_aspect_ratio_DEMO`). GR's compared set is 270 → 256 by name (§7.1 of the harness plan). The `after_run` residual on the reference arm now reads 6.99e-03 / 7.02e-03 — the distance between the written file and a fixed point of the solve's own map (I-21).

*Measured 2026-09-14 (A67 (written-file-gap), gate `written_file_gap`, `f8d67eb4`):* the one-call output path writes the **same** ~0.7 % `tfcoil.insstrain` gap as the loop path — the written file carries the post-write value in every Phase B arm, `BR` and `B0` through the loop, `B1` and `B2` through the single `finalise` — and no second component moves. No acceptance quantity of this experiment is written by a model's `output()`. The gap is PROCESS's, reported per run, never accepted on (D25, confirmed by the user 2026-09-14).

**Empty blocks and empty nodes are left as they are** *(user ruling 2026-09-10 on item 2)*. On
`st_regression` the `PULSE` block survives in the schedule after its only member has left it and is
swept 570–1131 times per run executing nothing (I-20a). *Measured by the copy's own counters (A58 (driver-predicate-counters), 2026-09-10, gate GR's runs): 570 empty sweeps at seed 0 and 3 510 at seed 1 on `B2`, **10.84 % / 11.30 %** of the run's block sweeps. The empty `PULSE` visit occurs on **all three** configurations (40 % of block visits everywhere, `FF` and `PULSE`), but costs a sweep only on `st_regression`: on the pulsed configurations the per-call deferral has emptied the block of members and the visit is free. Every disclaimer therefore quotes the **sweep share** (0 / 0 / 10.84–11.30 %), never the visit share.* V4 does **not** repair this: it is one of
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
bracket. *(As built, 2026-09-15 (A80): every Phase A arm reads the committed input file — the pin is a
constant, not an iteration variable — so no arm has a lifted column and each has `nvar` points per
sign: 20 / 19 / 14 per arm, 396 stencil evaluations in all, not 418 (Table D.11; the chain derives
the column set from the input file each arm reads, `chain.stencil_column_set`).)*

**Why not a smaller δ.** The improvement list proposed δ = 0.001, matched to `epsfcn`, as the
representative regime. A44 measured it (`E2`, ten seeds, three configurations): at δ = 0.001 the
flat arm still takes 5.0 sweeps on nof and lad against the 3.3 an in-loop evaluation takes, the
ratio moves the *wrong* way on two configurations (0.522 → 0.538; 0.568 → 0.524) and is
non-monotone in δ. Sweep counts are roughly logarithmic in amplitude; what governs them is *which*
components are displaced, and a δ-stream displaces every coupling component at once — a different
object from a design-variable step at any amplitude. At the stencil regime every arm's cost per
evaluation, sweep count and per-block composition land within 1–7 % of in-loop, and `A2/A0` at the
backward points is within 0.003 of the in-loop ratio on every configuration. Item 1a's "do not
reduce δ" half stands; its second-amplitude half is replaced.

**Checks, each with its acceptance rule pre-declared.**

1. **Similarity at matched accuracy (the Phase A headline).** Per configuration and pair, the
   distributions of each arm's audited maximum scaled residual over the components **not owned
   by the configuration's `per_run` node set** (membership derived nodes → measured write sets
   → spec keys; never a prefix rule), with the whole-state audit published beside.
   **Acceptance: `A1/A2` (pulsed) and `A0/A2` (st) within F = 10 at both median and p90.**
   A configuration where every arm reads exactly 0 counts as trivially similar and the report
   says so. The exit audit is one further full sweep of the complete node set — the same ruler
   for every arm — taken at termination and uncharged. On the pulsed configurations the pinned
   pair `A1 → A2` is the declared headline pair because both arms sit on the same reduced map;
   `A0 → A2` is published beside it with the burn-time residual reported separately (V3's
   construction), so V3's numbers remain comparable.
2. **The ownership rung.** `A0 → A1`: node calls and the exit audit. The pin holds the burn
   time off consistency by the seed's factor; the resulting inconsistency (`burn_time_residual`
   at exit, seconds and relative) is published per run as the rung's own statistic.
3. **Cost.** Per-node model-evaluation counts (primary), per-block totals, the unweighted
   `A2/A1` (pulsed) and `A2/A0` (st) ratios with the weighting-invariance bracket, and the
   `AR → A0` ratio **only** in the table that carries both arms' audit residuals. Prior context
   (V2, reproduced by A38; not acceptance): `A2/A0 = 0.522 / 0.568 / 0.502`.
4. **Bookkeeping.** The cold-start term beside, never pooled; the failure taxonomy —
   `crashed` / `refused` / `unconverged` / `unconverged-at-cap` (AR) / `infeasible-at-audit` —
   with denominators of 25 per arm per configuration per amplitude; skipped arms (st `A1`)
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
reference everywhere; `B2/BR` is published once on the same set. Prime calls are a column of
the same table (trap T11 in-table). Solve-phase node calls are the denominator throughout; the
output-time and audit sweeps are excluded symmetrically and every caption that uses the
per-node census says so.

**Retries are a term, not a footnote** *(added 2026-09-10 from A44's preliminary finding on V3's
records: lad's published `B2/B0 = 0.450` carries one seed on which the flat arms failed their
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
   accepted optima, for `B0 → B1`, `B0 → B2`; yardstick = the `BR → B0` relative
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
   **acceptance: nearest-rank median ≤ 1.05** for `B0 → B1`, `B0 → B2`; summed
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
   is not a check); the final-attempt median is published beside it for comparability with V3. `B1 → B2` and `B0 → BR` reported beside,
   outside the acceptance rule. **Pre-declared expectation:** on the pulsed configurations
   `B1 → B2` leaves the evaluation count unchanged (`ε = 1` exactly; V3: 33/33 converged seeds).
   RQ5 is not measured by a V4 arm (§3.2); A43 (st-trust-gap)'s verdict decides st's place.
3. **Lift closed.** Constraint-93 residual at every accepted optimum, seconds and relative to
   the burn time; residuals at unconverged exits beside, never pooled.
4. **Cost and robustness reporting (no robustness claim).** Solve-phase node calls on the
   one seed set in the one format; the per-block split as a first-class artifact; the failure
   taxonomy with denominators of 25; the configuration-invalid-seed statistic (a seed failing in every
   arm is configuration hardness, counted separately). **Pre-declared expectations (context,
   not acceptance), from V3:** `B2/B0 ≈ 0.64 / 0.45 / 0.53`; `BR → B0 ≈ 0.98 / 1.03 / 1.16`.
5. **The per-sweep overhead, counted** (item 3). Two new driver counters, exact and
   concurrency-invariant like `NODE_CALLS`: predicate evaluations and components compared,
   per run per arm. Published beside the node-call table with the dispatch-sweep count. This
   settles on counts alone whether a non-node-proportional term of the hypothesised size
   exists; wall-clock context (3 serial repetitions, median and range) is reported in its own
   section and is never evidence. *(As built, 2026-09-15: **that section is not written and the
   promise is withdrawn**, ruling D29 (2) — the user: "the non-node cost term is not relevant, as is
   the wall-clock time. Because this is an existance proof, not a claim that we really improved
   process this much … the impact on node calls is enough, as it is reasonable to see the impact for
   applications dominated by node call runtime". The counted per-sweep overhead is §5.5 and no
   timing is published; the plan text above is not rewritten.)*

**The transfer (RQ3; I-17), restated** *(amended 2026-09-10 on A44; pending review)*. No V4
number is derived through the transfer; Phase B's realised ratio stands as the deployment result.
The gap is an identity, `R = (N_B2/C_B2)/(N_B0/C_B0) × C_B2/C_B0 = ρ_B × ε`, with `N` solve-phase
node calls and `C` `call_models` evaluations over the one seed set, `per_run` executions and the
reference arms' output-time sweeps carried as separate terms. A44 established on V3's records that
the per-evaluation term `ρ_B/ρ_A` is uniform across configurations and is the entry regime
(§3.4), and that the evaluation-count term `ε` carries all the configuration dependence:
**(i)** the lift's stencil column, exact — every VMCON problem-call costs `2(nvar + 1)`
evaluations, so the lifted arms pay `(nvar + 2)/(nvar + 1)` per problem-call; **(ii)** retries,
whose evaluations are in `N` and whose iterations are not in check 2; **(iii)** trajectory change
at the lift (lad, every seed) and, on st, at the partition. V4 therefore states the transfer as

    B2/B0  ≈  ρ_A(stencil)  ×  (nvar_B2 + 1)/(nvar_B0 + 1)  ×  (problem-call ratio)

with `ρ_A(stencil)` the ratio of per-evaluation means at the stencil regime, the forward and
backward sets as the published bracket, and the problem-call ratio a Phase B measurement the
transfer carries and cannot predict. **Pre-declared expectations:** on the pulsed configurations
`B1 → B2` leaves the evaluation count unchanged (`ε = 1` exactly; V3: 33/33 converged seeds) —
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
`Δy` at `y = s_i` fails both). **Measurement:** Phase A (`A0`, `A1`, `A2`; 25 seeds; three
configurations; δ = 0.10) under both modes *(as built, 2026-09-15 (A80): the trial ran as gate G8 on
`A0` and `A2` at seeds 1–2 on the three configurations — 12 pairs, 24 runs — not as 150 campaign runs;
Table D.1 and companion Table F.5)* — counts, ratios with seed bracket, and the exit
audit **on both rulers** (a mixed audit beside a frozen one alone would report an accuracy
gain that is a change of ruler — both columns or neither). Phase B (`B0`, `B2`) under `mixed`
only if Phase A shows a decisive pass on an in-loop component. **Adoption rule:** gates 1–3
pass and the measurement is either neutral (adopted as the easier-to-defend equivalent) or
non-neutral on a named set (adopted, with the moved ratios re-stated as metric-dependent).
Only a gate failure blocks adoption. Adoption makes `mixed` V4's predicate and audit ruler,
with `frozen` selectable for cross-study comparison; V3's numbers are not retro-edited. *(As
built, 2026-09-15 (A80): gates 1–3 passed and the 12 pairs were neutral, which under this rule adopts
`mixed`; the campaign nevertheless ran and is reported on `frozen`, and the rule was not applied —
§5.6 records the departure for the user's ruling rather than adopting retroactively — ruled D30,
2026-09-15: the departure stands.)*

**Matched accuracy is verified per run, never assumed from a shared τ.** The exit audit is the
same full sweep on the same ruler for every arm; a pair whose audit residuals differ beyond the
similarity factor is reported as not comparable in cost, whatever its tolerance setting.

### 3.7 Decisions: rulings so far, and what is still open

**Table 4.** *The design choices: one row per choice of the original §3.7 list; "ruling" is the
user's decision of 2026-09-10 (D21) or the plan's recommendation where still open; the last column
is where it is applied.*

| # | choice | ruling | applied in |
|---|---|---|---|
| **(a)** | second Phase A entry regime | **adopted** — the stencil regime (A44 (transfer-gap)'s measurement), not δ = 0.001; the extra Phase A cost is accepted | §3.4, §3.5, §3.10 |
| **(b)** | objective/structure confound | **no fourth configuration in V4.** Three case studies; the confound is disclosed in every cross-configuration caption and no synthesis is claimed. A separate experiment follows only if V4's results stay inconclusive | §3.3, §3.11, §4 captions |
| **(c)** | Phase B seed set and format | **accepted**: one every-arm-converged set, the failure table, one format, retries as an explicit term. §4 carries placeholder tables in that format for review before any run | §3.5, §4 |
| **(d)** | driver changes | **accepted:** `MDA_Output` removed from the intervention arms (1b); switch renames (1d); predicate mode `frozen \| mixed` (5a), implemented cleanly. **Rejected:** empty-block / empty-node skipping (2) — left as is and disclaimed. Predicate-evaluation counters (3) — **accepted** (2026-09-10, after the explanation in §3.5 check 5). All changes are made in **V4's own copy of PROCESS** (D20), which owes V3 no backward compatibility | §3.3, §3.5, §3.8 |
| **(e)** | the fate of V3's joint-test arm (V3's `B2`; not today's `B2`) | **removed** (user, 2026-09-10; D22). **A43 (st-trust-gap) answered D22's conditional: the partitioned arm (`B2` today, V3's `B3`) is not unreliable on st** — 0 components above τ at every inner tolerance, its single pass reaching the joint-test arm's two-pass state bit for bit once the blocks are solved exactly — so **`st_regression` stays** | §3.2, §3.3 |
| **(g)** | the tolerance of the partitioned arms' block loops, now that V3's joint-test arm is gone (A43 P1) | **ruled (user, 2026-09-10; D23): one tolerance, τ = 1e-6, for every MDA converger in every arm, both phases** — there is no separate "inner" tolerance to set. Tightening is not required: the exit audit records achieved accuracy per run and comparisons are at matched accuracy. A43's exchange rate (block loops at 1e-8 ≡ the removed `B2`) is recorded should τ ever be tightened — everywhere at once | §1.3, §3.3, §3.10 |
| **(f)** | wait for A43/A44 before approving | **do not wait**; both land as dated amendments (A44's already has) | header |

**All ruled (2026-09-10)**, (g) last, after A43 (st-trust-gap)'s verdict opened it the same day. The V3 report receives **no errata**: A44 (transfer-gap)'s retry finding
lives in its own report and is carried into V4's method (§3.5), not written back into V3. The
PROCESS copy is taken at the current `architecture_surgery` tip, the commit recorded (§3.8 (i)).
The §4 table format awaits the user's review *(reviewed and accepted 2026-09-10, D21 (c); the tables
are Appendix D and the companion file since 2026-09-15, A79)*.

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
the top: this document, `experiment_runner.py` (the one-button entry point, no required
arguments; a draft mode runs preflight, gates and smoke only; refuses the campaign while
`EXECUTION_APPROVED` is `False`), `phase_a.py`, `phase_b.py`, `runs/` (untracked bulk
artifacts) *(as built there are no `phase_a.py`/`phase_b.py`: both phases are plans of the harness's
`chain.py`, pressed by the one button — Appendix C, 2026-09-15)*. Everything else in a self-contained `harness/` package — nothing imported from
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
comparison can fail), producing every table in §4 in the one format with its
caption *(as built: the tables are Appendix D and `RESULTS_TABLES_FULL.md` since A79, 2026-09-15; §4
states the conclusions)*. Nothing is published that this script does not regenerate. The DSM overlay of
improvement-list item 8 is dropped with V3's joint-test arm (V3's `B2`): no V4 arm exercises the outer verification loop.

### 3.9 Gates, each with teeth, run before any campaign number is cited

A failed gate stops the dependent stage and is a result; nothing is retried with different
settings. The coupling-state component counts the criteria refer to are 840 / 846 / 827 by
configuration (nof / lad / st).

**Table 5.** *The plan's gates: one row per gate — what it binds, the criterion, the tooth. All
criteria are counts or bit-comparisons.*

| gate | binds | criterion | teeth |
|---|---|---|---|
| **GR** the rewrite reproduces V3 | the harness rewrite and the PROCESS copy, once, at the copy commit before any driver change | twenty V3 records (in V3's names: `R`/`B0`/`B3 start000`, `B3 start001`, `B1 start001` on the pulsed configurations, `A0`/`A1 start001`) reproduced bit-exactly on every count field and hex float through the rewritten harness against the copy; the only use of the V3→V4 name map | +1 on a count, 1 ULP on a hex, a missing reference record, a missing key, a bad name map — each must refuse, never skip |
| **G0** the copy's physics is frozen | every V4 commit | `PROCESS/process/models/` byte-identical to `c0ae5b28`'s | a 1-byte change to one model file is caught |
| **G1** every new switch off ⇒ byte identity | all V4 driver changes (decision (d)) | MFILE hex floats identical to a run at the pre-change commit, 3 configurations, both stamps recorded | a 1-ULP change to one float is caught |
| **G2** prime on, fixed-point map | the prime's inertness after call 1 | from each reference exit snapshot, one flat and one partitioned call, prime on vs off, exit states bit-identical on N/N components | a doctored snapshot component trips |
| **G3 / G3c** prime on, cold chain; lad carrier census | "no cut edge carries anything" | as V3, **re-run at the campaign commit** (item 7) | prime-off chain reproduces A35's counts — 244 (`large_tokamak_nof`) / 124 (`st_regression`) for G3, 240 cold / 218 displaced (`low_aspect_ratio_DEMO`) for G3c — and every residual maximum to the bit; the "3 outer passes → 2" half has nothing to count since DR1 removed the repeated schedule (A52) |
| **G4** audit restriction | the similarity statistic | a doctored `per_run`-owned component trips the whole-state audit and not the restricted one; a doctored in-loop component trips both; **one doctored component from each excluded namespace** (`costs`, `water_use`, `vacuum`, …) | both directions, every namespace |
| **G5** combined-switch equivalence | `B2` | the arm composed from the matrix equals the arm composed switch by switch: `norm_objf` hex, `ifail`, iterations, outer-pass histogram, exit audit hex *(as built: 37 switch names and 10 run values per configuration, 141 compared, Table D.1; the outer-pass histogram has nothing to count since DR1)* | `norm_objf` hex and `n_call_models` teeth *(as built 4/4)* |
| **G6** Phase A entry and warm equivalence | Phase A | seed-paired entries bit-identical across arms per configuration; each block arm from the reference snapshot, pinned at the reference's converged burn time, reproduces the reference fixed point below τ with the pinned component bit-identical | as V3 |
| **G7** record completeness | the declared pairing and forensics | a forced-unconverged smoke run carries every declared field; a record with a field missing is refused by the tally | 5/5 field teeth *(as built 9/9, Table D.1)* |
| **G8** predicate trial (§3.6 gates 1–3) | the `mixed` mode | neutrality of `frozen`; the identity; the binding set | the doctored-component tooth |
| **G9** output-path equivalence | `MDA_Output` removal | on the intervention arms, the accepted state written by the new path is bit-identical to the state at the entry to `write_output_files`; on `BR`/`B0` nothing changes | a 1-ULP perturbation before `finalise` is caught |

### 3.10 Declared settings

**Table 6.** *The declared settings: one row per knob — symbol, value, what it controls,
provenance. None may change after approval except by dated amendment.*

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
| inner cap | 20 sweeps per block; a cap hit is a refusal | partitioned arms *(as built: the flat control's one block too — `B0`/`B1` on `low_aspect_ratio_DEMO` refused with `block FLAT did not converge in 20 sweeps` on 2 / 3 starts, Table 10; the message is Table D.12's)* | V2 |
| upstream cap | 10 passes (raises) → `unconverged-at-cap` | `AR`/`BR` | upstream; item 1 |
| W | 3 | worker pool | V2 |

**Run budget (context).** Phase A: `AR` 75 + `A0` 75 + `A1` 50 + `A2` 75 = 275 single
evaluations at δ = 0.10, plus the stencil regime — `2(nvar+1)` per arm per configuration:
42 × 4 (nof) + 40 × 4 (lad) + 30 × 3 (st) = 418 *(as built 40 × 4 + 38 × 4 + 28 × 3 = 396, §3.4)* — plus 150 under the `mixed` mode *(as built: 24 gate runs, G8; §3.6)*, plus gates;
V3's 225 took ≈ 1.5 h at W = 3. Phase B: 4 arms × 25 × 2 pulsed + 3 arms × 25 on st = 275 optimisations (V3: 350; V3's joint-test arm
removed; ≈ 2.5–3 h at W = 3), plus `B0`/`B2` under `mixed` (≤ 150) only if Phase A licenses it *(not
licensed: 0 verdict changes, §5.6; not run)*.

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

## 4. Results

*Written 2026-09-15 by task A79 (report-captions) from Appendix D alone, and audited the same day by
A80 (report-accuracy-audit), whose corrections are marked in Appendix C. Every number below is a
cell of a table there or in the companion file [`RESULTS_TABLES_FULL.md`](RESULTS_TABLES_FULL.md),
and the table is named beside it; nothing in this section is computed by hand. The population is
the **campaign** — 949 run records made at `57dc0c14` (921 ok; 28 stamped `crashed`, of which 20 are
PROCESS's own `RuntimeError` and 8 the coupling-state loop's 20-sweep cap, Table 10), 25 seeds
per arm per configuration — read through the arm-name translation of 2026-09-15 (`AR / A0 / A1 / A2`,
`BR / B0 / B1 / B2`; Appendix C). Configurations are written nof / lad / st for
`large_tokamak_nof` / `low_aspect_ratio_DEMO` / `st_regression`, in that order, and are never
pooled. Denominators: in the evaluation phase 25 runs per arm in the displaced regime, one per
design-vector column per arm at the stencil points (20 / 19 / 14) and one `A0` run per configuration
in the entry reference (Tables D.4 and D.11); in the
optimisation phase the seed set on which every arm reached an accepted optimum — **22 / 11 / 22**
of 25 (Table 10). The appendix's own conventions (D.0) hold: a ratio is read pooled
(Σ arm / Σ reference), as the per-run median with its bracket, and as the count of runs on which
the arm cost more.*

### 4.1 Gates

Every table below is read under a passed gate table: **30 gates PASS, 0 FAIL, 168 of 168 teeth
tripped** (Table D.1). *(A88 (function-weighted-sweeps), 2026-09-17: 167 before it; `tally_contracts`
gained one — a function-count file stating no count for a module, or giving a once-per-run node no
DSM row of its own, is refused rather than weighted by a guess. A86 (v3-tables-remainder): 163 before it; `tally_contracts` gained four,
one per construction added — a design vector with a value in a slot the name map does not name is
refused, a variable one side alone carries is named and never compared, an audit residual file
with no exclusion list of its own and a ruler it does not carry are both refused, and a figure of
merit the frozen tree's enum does not carry is refused rather than printed as an integer. A85
(v3-table-formats) had added the first two, 161 → 163.)* The rows that license the numbers directly: the reproduction gate GR
reproduces the previous revision's twenty records on 256 of 256 compared values; the neutrality
gate G1 finds 0 of 54 144 compared values changed across the driver commits it straddles (2 825
record values and 51 319 output-file lines, the two counts its cell now shows); the recomputation
row states that a second implementation sharing no construction with the tally reproduced every
published cell — **141 tables, 17 554 cells compared, 0 mismatched**; `tally_contracts` reproduces
the 256 reference cells and finds every emitted table captioned with a counted denominator (its 679
compared are 423 table checks + 256 cells, two counts the cell shows since A80);
*(A86 (v3-tables-remainder): 122 tables and 16 276 cells before it — the 1 278 new cells are the
nineteen tables the previous revision's remaining §4 and §5 shapes needed. A85
(v3-table-formats): 107 and 15 122 before that.)*
`run_kind_separation` shows the 949 campaign records and no gate or smoke record in every published
population. Two PASS rows carry a nonzero *mismatched*: the frozen-physics gate `g0prime`, which
counts the single model file the user approved as differing, by name (1 of 77), and `copy_identity`,
which counts the seven driver files the experiment's permitted edits touched, by name and digest (7 of
224; the record lists them). *(A80: the sentence named only the first.)*

### 4.2 The evaluation phase

<!-- plan_tables: main-text table matched_accuracy_headline -->

**Table 7.** ***Check 1 — matched accuracy**, the headline evaluation-phase check: the restricted audit maximum as `median / p90` per arm, one row per configuration, over that configuration's 25 displaced-entry runs per arm on the frozen ruler. The declared pair is `A2/A1` on a pulsed configuration and `A2/A0` on `st_regression` — the *reference* column names it — and the rule is within F = 10 at median **and** p90; the other pair is published beside and is not the acceptance. A ratio cell reads `med, p90 → verdict`, and `—` where the pair has no ratio to report. The dropped *verdict note* column said which pair is the declared one, which the *reference* column says, and carried one note of its own: on `low_aspect_ratio_DEMO` both quantiles of both pairs are exactly 0, so the ratios read `—` and the pair passes under the **trivially-similar clause**, not on a measured ratio. The mixed ruler's distributions are in Appendix D. n = 275 (finished evaluation-phase campaign runs over every configuration in this source).*

| configuration | n (runs) | AR | A0 | A1 | A2 | reference | A2/A1 med, p90 → verdict | A2/A0 med, p90 → verdict |
|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | 100 | 2.624e-08 / 1.542e-07 | 5.042e-10 / 2.963e-09 | 3.833e-10 / 1.671e-08 | 3.833e-10 / 1.671e-08 | A1 | 1.0000, 1.0000 → **PASS** | 1.3154, 5.6408 → **PASS** |
| low_aspect_ratio_DEMO | 100 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | A1 | —, — → **PASS** | —, — → **PASS** |
| st_regression | 75 | 1.539e-07 / 2.793e-07 | 5.372e-09 / 2.023e-08 | — / — | 5.372e-09 / 2.023e-08 | A0 | — | 1.0000, 1.0000 → **PASS** |

<sub>`check 1, matched accuracy`</sub>

<sub>combining 1 stage table(s): `matched accuracy by configuration — campaign_displaced`</sub>

<!-- plan_tables: end of main-text table matched_accuracy_headline -->

**The same fixed point, not merely an equally converged one (Table 7; Tables D.6 and D.9).**
The restricted maximum scaled residual at exit is **identical** for `A1` and `A2` on both pulsed
configurations — median 3.833e-10, p90 1.671e-08 on nof; exactly 0 on every run of lad — and for
`A0` and `A2` on st (5.372e-09, p90 2.023e-08), so the F = 10 similarity rule of §3.4 is met with a
factor of 1 (Table D.6, frozen ruler; the mixed ruler reads the same or lower on every row).
The distance between the two arms' exit states themselves, on the same restricted set and the same
ruler, is **5.094e-12 / 0 / 1.227e-11** median (p90 1.838e-10 / 0 / 4.620e-11; worst pair
2.709e-10 / 0 / 6.565e-11) for the headline pairs `A2/A1`, `A2/A1`, `A2/A0`, with **0 of 25**
pairs holding any restricted component at or above τ = 1e-6 and 0 pairs categorically unclean on
every configuration (Table D.9). The whole-state columns of both tables are large for `A2`
(median 2.435 / 0.1816 / 0.2575, Table D.6): those are the components the once-per-run
deferred nodes write, stale by construction at the audit, excluded from the restricted statistic
by the derived membership rule and published so the exclusion can be seen — they are not judged.

<!-- plan_tables: main-text table per_call_cost_headline -->

**Table 8.** ***Per-call cost**: mean model-node executions per `call_models` evaluation with the `[min, max]` seed bracket in one cell, one row per configuration over its 25 displaced-entry runs per arm, then the ladder's rungs as pooled ratios — `AR→A0` the stopping rule, `A0→A1` the ownership of the burn time, `A1→A2` the partition, with `A0→A2` standing in where the ownership rung does not exist. The partitioned arm's prime calls per evaluation are the last column and are in **no** node-call cell (D19). n = 275 (finished evaluation-phase campaign runs over every configuration in this source).*

| configuration | n (runs) | AR | A0 | A1 | A2 | AR→A0 | A0→A1 | A1→A2 | A0→A2 | reference | A2 prime calls / eval | pairs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | 100 | 104.2 [84, 105] | 115.9 [105, 126] | 107.5 [84, 126] | 60.5 [60, 63] | 1.1129 | 0.9275 | **0.5625** | — | A1 | 13.2 | 25 |
| low_aspect_ratio_DEMO | 100 | 105 | 105 | 103.3 [84, 105] | 59.6 [57, 60] | 1.0000 | 0.9840 | **0.5772** | — | A1 | 12.9 | 25 |
| st_regression | 75 | 103.3 [84, 105] | 122.6 [105, 126] | — | 61.5 [59, 62] | 1.1870 | — | — | **0.5016** | A0 | 14.8 | 25 |

<sub>`per-call cost`</sub>

<sub>combining 1 stage table(s): `per-call cost by configuration — campaign_displaced`</sub>

<!-- plan_tables: end of main-text table per_call_cost_headline -->

**RQ4 — the stopping rule `AR → A0` (Tables D.5 and D.6).** Upstream's
objective/constraint test at its two-pass floor is cheaper per call than the coupling-state test
at τ on two configurations — `AR` costs **0.9688** of `A1` on nof where `A0` costs 1.0781 of it,
and **0.8425** of `A0` on st; on lad `AR` and `A0` both cost exactly 105.0 calls on every seed —
and it stops **further from the fixed point**: `AR`'s restricted residual is 2.624e-08 / 0 /
1.539e-07 median against `A0`'s 5.042e-10 / 0 / 5.372e-09 (p90 1.542e-07 / 0 / 2.793e-07 against
2.963e-09 / 0 / 2.023e-08). That is what the predicate-matched control is a control *for*.

**The ownership rung `A0 → A1` (Table 8, displaced entries).** Pinning the burn time to a
constant costs nothing measurable per call — **0.9275 / 0.9840** pooled, median 1.0000, `A1` worse
on 0 of 25 seeds — and leaves the declared inconsistency: a burn-time residual at exit of
**154.6 s / 525.8 s** median (relative 6.298e-02 / 5.275e-02). Seen on the coupling state rather
than on the burn time alone, the rung moves the plant block's fixed point by 9.665e-02 / 7.026e-02
of its scale with **25 of 25** pairs above τ (`A1/A0`, Table D.9) — which is why the
previous revision's pair `A2/A0`, published beside, reads the same 9.665e-02 / 7.026e-02: it
compared two different fixed points.

**RQ1 — the partitioning rung `A1 → A2` (`A0 → A2` on st), one evaluation, displaced entries
(Table D.5, headline Table 8).** At matched achieved accuracy the partitioned arm costs
**0.5625 / 0.5772 / 0.5016** of the reference arm's model-node executions per `call_models`
evaluation, pooled over 25 paired seeds per configuration (per-run medians 0.5714 / 0.5714 /
0.4921; `A2` cost more on **0 of 25** seeds on every configuration). In absolute terms 60.5 / 59.6 /
61.5 node calls per evaluation against 107.5 / 103.3 / 122.6 for the reference (Table 8's per-arm
cells). Where the saving sits (Table 9, the pooled ratio of `A2` to its reference module by
module — the same ratios in node calls per block, with the per-block absolute counts, are the
displaced-entry row group of Table D.3): the once-per-run
deferred nodes fall to **0** (they run after the solve in `A2` and on every sweep in the flat
arms), the pulse node to **0.1953 / 0.2033** (st has it deferred), the plant block M3 to **0.5859 /
0.6098 / 0.5137**, the physics block M1 to **0.7812 / 0.8130 / 0.6849**, while the coils block M2
is solved about as often as the flat arm sweeps it — **1.0078 / 0.9919 / 1.0000**. The
arrangement-method (prime) calls the partitioned arm adds are 13.2 / 12.9 / 14.8 per evaluation,
stamped beside the node calls and never in them (Table D.5).

<!-- plan_tables: main-text table module_sweeps_evaluation -->

**Table 9.** ***Module sweeps per run**: how often each node group was swept in one `call_models` evaluation, one block per configuration over its own 25 displaced-entry runs, as the mean with its [min, max] seed bracket — a bare integer where every run agreed exactly. `models` is the group's collapsed-DSM row count, so total calls = Σ sweeps × models. **The ratio column is the result**, and it is unit-free: within a group every model node runs once per sweep (the construction refuses the run if they did not), so a ratio of sweeps does not depend on whether one counts model calls or DSM rows. The total does, and its ratio cell is the `[v = 1, v = 0]` interval over the two defensible attributions of the once-per-run nodes' rows (trap T9); the per-arm total cells are the v = 1 case. Reported, not accepted on. n = 3 (block(s) of this table, each over its own population with its own n in its heading line; never pooled).*

**`nof`** (n = 25 per arm)

| module | models | AR | A0 | A1 | A2 | reference | A2 / reference | pairs |
|---|---|---|---|---|---|---|---|---|
| M1 | 24 | 4.96 [4, 5] | 5.52 [5, 6] | 5.12 [4, 6] | 4 | A1 | **0.7812** | 25 |
| M2 | 10 | 4.96 [4, 5] | 5.52 [5, 6] | 5.12 [4, 6] | 5.16 [5, 6] | A1 | **1.0078** | 25 |
| M3 | 11 | 4.96 [4, 5] | 5.52 [5, 6] | 5.12 [4, 6] | 3 | A1 | **0.5859** | 25 |
| PULSE | 1 | 4.96 [4, 5] | 5.52 [5, 6] | 5.12 [4, 6] | 1 | A1 | **0.1953** | 25 |
| once per run | 3 | 4.96 [4, 5] | 5.52 [5, 6] | 5.12 [4, 6] | 0 | A1 | **0.0000** | 25 |
| total calls | 49 | 243 | 270.5 | 250.9 | 181.6 | A1 | **[0.724, 0.767]** | 25 |

**`lad`** (n = 25 per arm)

| module | models | AR | A0 | A1 | A2 | reference | A2 / reference | pairs |
|---|---|---|---|---|---|---|---|---|
| M1 | 24 | 5 | 5 | 4.92 [4, 5] | 4 | A1 | **0.8130** | 25 |
| M2 | 10 | 5 | 5 | 4.92 [4, 5] | 4.88 [4, 5] | A1 | **0.9919** | 25 |
| M3 | 11 | 5 | 5 | 4.92 [4, 5] | 3 | A1 | **0.6098** | 25 |
| PULSE | 1 | 5 | 5 | 4.92 [4, 5] | 1 | A1 | **0.2033** | 25 |
| once per run | 3 | 5 | 5 | 4.92 [4, 5] | 0 | A1 | **0.0000** | 25 |
| total calls | 49 | 245 | 245 | 241.1 | 178.8 | A1 | **[0.742, 0.786]** | 25 |

**`st`** (n = 25 per arm)

| module | models | AR | A0 | A1 | A2 | reference | A2 / reference | pairs |
|---|---|---|---|---|---|---|---|---|
| M1 | 24 | 4.92 [4, 5] | 5.84 [5, 6] | — | 4 | A0 | **0.6849** | 25 |
| M2 | 10 | 4.92 [4, 5] | 5.84 [5, 6] | — | 5.84 [5, 6] | A0 | **1.0000** | 25 |
| M3 | 11 | 4.92 [4, 5] | 5.84 [5, 6] | — | 3 | A0 | **0.5137** | 25 |
| once per run | 4 | 4.92 [4, 5] | 5.84 [5, 6] | — | 0 | A0 | **0.0000** | 25 |
| total calls | 49 | 241.1 | 286.2 | — | 187.4 | A0 | **[0.655, 0.709]** | 25 |

<sub>`module sweeps per run, the evaluation phase`</sub>

<sub>combining 3 stage table(s): `module sweeps per run — large_tokamak_nof — campaign_displaced`; `module sweeps per run — low_aspect_ratio_DEMO — campaign_displaced`; `module sweeps per run — st_regression — campaign_displaced`</sub>

<!-- plan_tables: end of main-text table module_sweeps_evaluation -->

**The same result in sweeps, per module — where the partition does its work (Table 9).**
A node group is *swept* when the schedule walks it, and every model node inside it runs once per
sweep, so the cell of Table 9 is a **sweep count** and its ratio does not depend on
whether one counts model calls or collapsed-DSM rows — which the node-call total does. Read down
the ratio column: the flat arm's own column is **one repeated number** on every configuration
(5.52 / 5 / 5.84 sweeps of every group — a flat sweep executes everything equally often), and the
partitioned arm's cells are **exact constants across all 25 runs** wherever it does not iterate a
module: 4 sweeps of M1, 3 of M3, 1 of the pulse node and 0 of the once-per-run set, with no
spread whatever. All of the seed dispersion in the partitioned arm sits in M2 and never exceeds
one sweep. M2's ratio is the reading that matters: **1.0078 / 0.9919 / 1.0000** — on st the
partitioned arm runs 5.84 M2 sweeps against the flat arm's 5.84, seed for seed, so the partition
buys that module nothing at all, while M3 falls by 2.52 / 2.00 / 2.84 sweeps per evaluation
across the most models of any live group. The total row is for reconciliation only and is an
**interval**, not a number: `models` per module is committed but `models` per *node* is not (trap
T9), so how many collapsed-DSM rows the once-per-run nodes own is unknown, and the two defensible
attributions bracket the ratio at **[0.724, 0.767] / [0.742, 0.786] / [0.655, 0.709]**. The per-module ratios are unaffected by that choice.

**What the partition is, before what it cost (Table D.2).** The three modules hold 2, 3 and 12
executing model nodes on every configuration — the TF-coil family contributes exactly one member
by conductor choice (`cicc_sctfcoil` on the two pulsed configurations, `croco_sctfcoil` on
`st_regression`) — against collapsed-DSM row counts of 24, 10 and 12. **M1 is two model nodes and
twenty-four DSM rows; M3 is twelve nodes and twelve rows.** That is why the per-module ratios are
the result and the weighted total is an interval: counting model calls weights a total toward M3,
counting DSM rows weights it toward M1, and the unit is a modelling choice. The pulse node is one
row and executes on the two pulsed configurations; on `st_regression` it is deferred, which is why
that configuration's once-per-run group holds four nodes and the others' three.

**The distributions do not overlap, and the count statistic needs no ruler (Table D.7).** Over the
displaced entries the reference arm's restricted maximum runs 0 – 2.265e-07 on the large tokamak
and 2.755e-08 – 5.938e-07 on the spherical one, while the flat control's runs 0 – 4.352e-09 and
1.632e-09 – 2.875e-08: the stopping rule's populations are separated by an order of magnitude at
both ends, not by a summary statistic. The partitioned arm's distribution is **identical to its
reference's at all three order statistics** on every configuration (0 / 3.833e-10 / 1.870e-08 on
nof against `A1`'s; exactly 0 throughout on lad; 1.632e-09 / 5.372e-09 / 2.875e-08 on st against
`A0`'s). And the statistic that needs no ruler agrees: **`Σ components > τ` is 0 in every arm on
every configuration in the displaced regime and at the forward stencil points**, and the worst
single run leaves 0 — the arms do not merely shrink the residual, they leave nothing above
tolerance. **One row of the thirty-three is not 0**, and it is the reference arm's: at the backward
stencil points `AR` on the large tokamak leaves **2** components above τ, both in one run (max
2.645e-06 — the same value the fixed-point table reports for the `A0/AR` pair at column 19). That
is upstream's own stopping rule at its two-pass floor, and it is not a statement about the
partition. The mixed
ruler's median and p90 stand beside the frozen ruler's in the same rows and are never larger
(D30).

**The exclusion set is load-bearing, and by how much (Table D.8).** The restricted statistic
excludes the components the once-per-run deferred nodes write, and the report's headline rests
entirely on that set being right. In the partitioned arm every excluded namespace is far from
converged at the audit — p90 of the per-run maximum 9.860 (`costs`), 0.1349 (`fwbs`), 0.09859
(`water_use`), 0.06787 (`vacuum`) and 0.05270 (`physics`) on the large tokamak, and 0.2878 /
0.08439 / 0.1289 / 0.09657 / 0.08508 on the low-aspect-ratio machine — against a restricted
headline of 1.671e-08 and 0. **Had `vacuum` alone been wrongly excluded the headline would read
6.8e-02 / 9.7e-02 / 9.1e-02 instead of 1.7e-08 / 0 / 2.0e-08**, six to seven orders, and the
`A2`-passes verdict would not survive. The flat control's excluded set is at machine noise or
exactly zero in the same rows, because it runs those nodes on every sweep. The membership of all
five namespaces is therefore load-bearing rather than cosmetic, and it is gated in both directions
by G4.

**The stencil regime confirms the displaced one at a smaller saving (Table D.5 and companion Table F.2).** From the forward stencil points `A2` costs **0.6214 / 0.6399 / 0.5767** of its
reference pooled (medians 0.6071 / 0.6071 / 0.5714), from the backward points **0.6405 / 0.6609 /
0.5583** (0.6071 / 0.7143 / 0.5238), worse on 0 of 20 / 19 / 14 columns in every case; the
one-variable displacement from a fixed point leaves the flat arm less to iterate. The headline
pairs' restricted distance is 2.579e-12 / 0 / 1.116e-10 median forward and 0 / 0 / 5.339e-11
backward, with 0 pairs at or above τ (Table D.9). One rung row reads otherwise: on nof's
backward points the stopping-rule pair `A0/AR` has **1 of 20** pairs with a component at or above
τ (worst 2.645e-06, column 19; Table D.9) — a statement about where upstream's test stops, not
about the partition.

**Machinery.** Every scheduled evaluation finished: 25 of 25 per arm in the displaced regime, 20 / 19 /
14 of 20 / 19 / 14 per arm at the forward and at the backward stencil points, 1 of 1 entry reference per
configuration (Tables D.4 and D.11). The predicate trial's runs are bit-identical under the two rulers
with 0 verdict changes on every pair (gate `predicate_mode`, 8 152 compared / 0 mismatched, Table
D.1; the per-pair table is companion Table F.5). The per-run convergence-test costs are companion Table F.4.

### 4.3 The optimisation phase

<!-- plan_tables: main-text table per_arm_success -->

**Table 10.** ***Reliability per arm**, the configurations stacked: of the 25 starts offered to each arm, the **accepted optima** (status ok and the output file's `ifail == 1`), then every other start by its outcome class — finished with the optimiser's own exit code `ifail = 5` after its four attempts; crashed inside PROCESS (`RuntimeError`); refused by the coupling-state loop's 20-sweep cap (`ModuleSolveFailure`) — and last the starts **lost**, which this arm did not accept and another did. A class column is empty where the configuration has no start of that class. The **seed set** is the last column, stated once at the head of each configuration's arm rows and blank below it: the seeds on which *every* arm reached an accepted optimum, which is the n of every other optimisation table. The seeds behind each class, the configuration-invalid seeds, the retried seeds and the failure taxonomy's tracebacks are the merged table in Appendix D, and per seed in the companion file. Reported, not accepted on (D29, 2026-09-15). n = 3 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and its own n, and that n counts starts offered per arm on that configuration). Per-seed column(s) *seeds not accepted, by class*, *seeds lost that another arm accepted*: companion Table F.13.*

| arm | starts offered | accepted optima | finished, ifail = 5 | crashed (RuntimeError) | coupling-loop cap (ModuleSolveFailure) | lost, another arm accepted | seed set (every arm accepted) |
|---|---|---|---|---|---|---|---|
| **large_tokamak_nof (n = 25)** |  |  |  |  |  |  |  |
| BR | 25 | 22 |  | 3 |  | 0 | 22 |
| B0 | 25 | 22 |  | 3 |  | 0 |  |
| B1 | 25 | 22 |  | 3 |  | 0 |  |
| B2 | 25 | 22 |  | 3 |  | 0 |  |
| **low_aspect_ratio_DEMO (n = 25)** |  |  |  |  |  |  |  |
| BR | 25 | 12 | 11 | 2 | 0 | 0 | 11 |
| B0 | 25 | 12 | 9 | 2 | 2 | 0 |  |
| B1 | 25 | 11 | 9 | 2 | 3 | 1 |  |
| B2 | 25 | 11 | 9 | 2 | 3 | 1 |  |
| **st_regression (n = 25; arms BR·B0·B2)** |  |  |  |  |  |  |  |
| BR | 25 | 24 | 1 |  |  | 0 | 22 |
| B0 | 25 | 23 | 2 |  |  | 1 |  |
| B2 | 25 | 23 | 2 |  |  | 1 |  |

<sub>`per-arm success`</sub>

<sub>combining 3 stage table(s): `per-arm success — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`; `per-arm success — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`; `per-arm success — st_regression — campaign_optimisation · BR·B0·B2`</sub>

<!-- plan_tables: end of main-text table per_arm_success -->

**The population (Tables 10 and D.12).** On nof seeds 5, 20 and 21 crash in all four arms with
PROCESS's own `RuntimeError: Failed to converge after 50 iterations, value is nan`, leaving a seed
set of **22**; no arm retried on any of them. On lad 14 seeds are outside the set and 13 of them are
configuration-invalid — no arm reached an accepted optimum there: on 2 every arm crashes, on 9 every arm
exhausts VMCON's four-attempt retry ladder and finishes with `ifail = 5` (a finished run, counted *ok*
in Table D.12 and *failed* in companion Table F.7), and on 2 `BR` exhausts the ladder while `B0`, `B1`
and `B2` are refused by their coupling-state loop's 20-sweep cap (`ModuleSolveFailure`, block `FLAT` /
`M1`, `current_drive.eta_cd_dimensionless_hcd_primary` at `inf`; `B0` 2, `B1` 3, `B2` 3 such exits in
all). The fourteenth, seed 10, is the one start lost to the intervention arms alone: `BR` and `B0`
accepted, `B1` and `B2` hit the cap. That leaves **11**, with accepted optima on 12 / 12 / 11 / 11 seeds
per arm and 12 / 10 / 10 / 10 retried seeds per arm across the 25 offered (Tables 10 and D.12; companion Table F.7; `report_counts_check.py` §3). On st every start finished (25 of 25 per arm); one seed is
configuration-invalid (every arm `ifail = 5` after four attempts) and two more are lost to one arm's
`ifail = 5` each (`B2` on seed 5, `B0` on seed 10), so the set is **22**; 5 / 3 / 2 seeds retried in
`BR` / `B0` / `B2`. Every ratio below is over these sets and says so. **Per arm, of the 25 starts
offered, accepted optima are 22 / 22 / 22 / 22 on nof, 12 / 12 / 11 / 11 on lad and 24 / 23 / — / 23
on st for `BR` / `B0` / `B1` / `B2`** — 88 %, 48 % / 44 % and 96 % / 92 % — with every other start
named by outcome class in Table 10 (per-arm success) and per seed in companion Table F.6; the table is reported, not accepted on (D29, 2026-09-15). *(A80 corrected this paragraph:
it had described the 13 as "2 crash in every arm and the rest fail to converge in at least one".)*
*(A82 added the per-arm sentence and its table, 2026-09-15.)*

**The three configurations do not optimise the same thing (Table D.13).** `large_tokamak_nof`
minimises the plasma major radius (`i_figure_merit` 1) over 20 iteration variables and 26
constraints (3 equality); `low_aspect_ratio_DEMO` **maximises the pulse length** (−14) over 19 and
25 (4 equality); `st_regression` maximises the fusion gain (−5) over 14 and 18 (3 equality) and is
steady state. The consequence that matters is the second one: **on `low_aspect_ratio_DEMO` the
lifted quantity *is* the objective**, so `B0` computes the burn time through the coupling loop and
reports it, while `B1` and `B2` let the optimiser choose it and enforce consistency through
constraint 93 — 20 variables and 26 constraints after the lift, against 19 and 25 before. Those
are not the same optimisation problem (I-20 (b)), which is why `B0` is the odd arm out on that
configuration and why every cross-configuration statement below is three answers to three
questions rather than one sample of three. On the large tokamak the same switch is a pure
architectural change (21 variables and 27 constraints after the lift, the burn time being a
constraint-side quantity) and on the spherical tokamak it is absent entirely.

<!-- plan_tables: main-text table same_optimum -->

**Table 11.** *Check 1 by configuration and arm pair: the paired relative objective difference at median and p90 against the pair's own threshold, with the verdict, the count of seeds whose optima sit in different objective clusters (*hops*) and the count below cluster resolution. The yardstick pair `BR → B0` is published beside and never accepted on. n = 3 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and its own n, and that n counts seeds on which every arm of that configuration converged).*

| pair | n | relative Δ objf, median / p90 | threshold median / p90 | verdict | hops | below resolution | retried seeds in pair |
|---|---|---|---|---|---|---|---|
| **large_tokamak_nof (n = 22)** |  |  |  |  |  |  |  |
| BR → B0 (yardstick) | 22 | 2.082e-15 / 6.893e-13 | — / — | — | 0/22 (0.00) | 0 | 0 |
| B0 → B1 | 22 | 2.823e-11 / 4.570e-11 | 1.000e-06 / 1.000e-06 | **PASS** | 0/22 (0.00) | 0 | 0 |
| B0 → B2 | 22 | 2.823e-11 / 4.570e-11 | 1.000e-06 / 1.000e-06 | **PASS** | 0/22 (0.00) | 0 | 0 |
| **low_aspect_ratio_DEMO (n = 11)** |  |  |  |  |  |  |  |
| BR → B0 (yardstick) | 11 | 1.982e-14 / 1.976e-13 | — / — | — | 0/11 (0.00) | 0 | 1 |
| B0 → B1 | 11 | 4.101e-07 / 2.148e-06 | 1.000e-06 / 1.000e-06 | **FAIL** | 1/11 (0.09) | 2 | 1 |
| B0 → B2 | 11 | 4.101e-07 / 2.148e-06 | 1.000e-06 / 1.000e-06 | **FAIL** | 1/11 (0.09) | 2 | 1 |
| **st_regression (n = 22; arms BR·B0·B2)** |  |  |  |  |  |  |  |
| BR → B0 (yardstick) | 22 | 1.553e-13 / 5.908e-09 | — / — | — | 2/22 (0.09) | 0 | 3 |
| B0 → B2 | 22 | 3.467e-13 / 3.510e-09 | 1.000e-06 / 1.000e-06 | **PASS** | 1/22 (0.05) | 0 | 1 |

<sub>`same optimum (check 1)`</sub>

<sub>combining 3 stage table(s): `same optimum (check 1) — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`; `same optimum (check 1) — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`; `same optimum (check 1) — st_regression — campaign_optimisation · BR·B0·B2`</sub>

<!-- plan_tables: end of main-text table same_optimum -->

**The same optimum — check 1 (Table 11).** The paired relative objective difference
`B0 → B2` is **2.823e-11 / 4.101e-07 / 3.467e-13** median and **4.570e-11 / 2.148e-06 /
3.510e-09** at p90 against a threshold of 1.000e-06 on every configuration (the F × yardstick term
never exceeds the floor: the `BR → B0` yardstick reads 2.082e-15 / 1.982e-14 / 1.553e-13 median).
**PASS on nof and st; FAIL on lad**, where the p90 exceeds the floor with **1 hop of 11** between
objective clusters and 2 pairs below cluster resolution. `B0 → B1` reads the same values to every
digit on lad (4.101e-07 / 2.148e-06, FAIL), so the difference sits on the ownership rung and not on
the partition. On st the yardstick pair itself hops on 2 of 22 seeds and `B0 → B2` on 1 of 22.

**Same optimum does not mean same machine (Table D.15) — a diagnostic, never an acceptance
(D6).** Over exactly check 1's pairs, the maximum relative difference across the iteration
variables the two runs share **by name** tells a different story from the objective. `B0 → B2`
agrees on the objective to 2.8e-11 on the large tokamak while its design point moves by
**4.6e-02** at the median and **4.4e-01** at the worst, on composition fractions
(`f_nd_alpha_thermal_electron` on 12 of 22 pairs, `f_nd_impurity_electrons(13)` on 5). On the
spherical tokamak the objectives agree to 3.5e-13 and some pairs' points differ by **1.000** — a
100 % difference in `dr_shld_inboard` (14 of 22) or `dr_tf_nose_case` (6 of 22). The configuration
that **fails** check 1 has the tightest point agreement of the three (5.3e-06 median on lad).
And the control settles what that indicts: **`BR → B0`, a change of stopping rule and nothing
else, moves st's point by p90 1.7e-01 and max 1.000**, as far as any architectural rung does.
Non-identification is a property of the configuration and its constraint set, not of the
partition — which is why D6 forbids gating on iteration variables, and this table is the
measurement that justifies the rule rather than merely asserting it. On the pulsed configurations
the relocation enters at `B0 → B1`, the rung that *adds* `t_plant_pulse_burn` to the design vector
(the *extra vars* column), and `B1 → B2` — the partition alone — moves the point by 0 at the
median and at most 6.7e-11 and 3.2e-11.

**The partition leaves the optimiser's path untouched (Table D.16).** Over the pairs on which both
`B1` and `B2` reached an accepted optimum, the two arms take the **identical** number of
evaluations of the model set on 22 of 22 and 11 of 11, the identical number of optimiser
iterations on 22 of 22 and 11 of 11, and reach a **bit-identical** `norm_objf` — the stamped hex
float, not agreement to a printed precision — on **22 of 22** and 8 of 11. These are integers and
a bit comparison, so *identical* is exact: the partition changed nothing about the path the
optimiser took, only what each step cost. On three of the eleven low-aspect-ratio pairs the two
arms end on a different bit pattern while taking the same evaluations and the same iterations;
what the table states is the counts, and why those three differ in the last bits is not measured
here. `B1` is inactive on `st_regression`, which therefore has no row.

<!-- plan_tables: main-text table iteration_multiplier_headline -->

**Table 12.** ***Optimiser iterations per run**, summed over the optimiser's retry attempts, one row per configuration over its own seed set: the mean per arm, then `B2` against `B0` as the ratio of those means — equal to the ratio of the sums over the same seeds, the campaign-cost statistic — as the mean of the per-seed ratios, as their median with the observed [min, max] seed bracket (the check-2 acceptance quantity, bound ≤ 1.05) and as the count of seeds on which `B2` took strictly more iterations. The arms are `BR`, `B0`, `B1` and `B2`; `B1` is inactive on `st_regression` and its column reads — there. n = 3 (configurations stacked, each over its own seed set — the n column: large_tokamak_nof 22 / low_aspect_ratio_DEMO 11 / st_regression 22 seeds on which every arm converged; never pooled).*

| configuration | n | BR | B0 | B1 | B2 | B2/B0 mean | B2/B0 mean of per-seed ratios | B2/B0 median [min, max] | seeds B2/B0 > 1 |
|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | 22 | 7.818 | 7.818 | 7.773 | 7.773 | 0.9942 | 0.9964 | **1.0000 [0.875, 1.143]** | 2 |
| low_aspect_ratio_DEMO | 11 | 29.82 | 29.82 | 20.91 | 20.91 | 0.7012 | 1.3842 | **0.8125 [0.129, 5.909]** | 3 |
| st_regression | 22 | 31.18 | 25.14 | — | 23.95 | 0.9530 | 0.9828 | **1.0000 [0.246, 1.356]** | 5 |

<sub>`the iteration multiplier`</sub>

<sub>combining 1 stage table(s): `the optimiser's path over the configurations — campaign_optimisation`</sub>

<!-- plan_tables: end of main-text table iteration_multiplier_headline -->

<!-- plan_tables: main-text table evaluation_count -->

**Table 13.** ***Evaluations of the model set per run**, ε (`sweeps_per_eval.n_evaluations`, the field issue I-26 named as the correct one), one row per configuration over its own seed set: the mean per arm, then `B2` against `B0` read the same four ways — the ratio of the means, the mean of the per-seed ratios, their median with the bracket, and the count above 1. This is the ε of R = ρ × ε and it is a count of optimiser probes, not a cost. The arms are `BR`, `B0`, `B1` and `B2`; `B1` is inactive on `st_regression` and its column reads — there. n = 3 (configurations stacked, each over its own seed set — the n column: large_tokamak_nof 22 / low_aspect_ratio_DEMO 11 / st_regression 22 seeds on which every arm converged; never pooled).*

| configuration | n | BR | B0 | B1 | B2 | B2/B0 mean | B2/B0 mean of per-seed ratios | B2/B0 median [min, max] | seeds B2/B0 > 1 |
|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | 22 | 614.7 | 614.7 | 640 | 640 | 1.0411 | 1.0437 | **1.0476 [0.908, 1.209]** | 19 |
| low_aspect_ratio_DEMO | 11 | 2345 | 2345 | 1714 | 1714 | 0.7309 | 1.4816 | **0.8468 [0.132, 6.450]** | 3 |
| st_regression | 22 | 1846 | 1480 | — | 1407 | 0.9512 | 0.9821 | **1.0000 [0.241, 1.360]** | 5 |

<sub>`the evaluation count ε`</sub>

<sub>combining 1 stage table(s): `the optimiser's path over the configurations — campaign_optimisation`</sub>

<!-- plan_tables: end of main-text table evaluation_count -->

<!-- plan_tables: main-text table node_calls_per_evaluation -->

**Table 14.** ***Model-node executions per evaluation of the model set**, ρ, one row per configuration over its own seed set: the mean per arm, then `B2` against `B0` read the same four ways. This is the ρ of R = ρ × ε — the per-call term the partition acts on, and the stable one. The arms are `BR`, `B0`, `B1` and `B2`; `B1` is inactive on `st_regression` and its column reads — there. n = 3 (configurations stacked, each over its own seed set — the n column: large_tokamak_nof 22 / low_aspect_ratio_DEMO 11 / st_regression 22 seeds on which every arm converged; never pooled).*

| configuration | n | BR | B0 | B1 | B2 | B2/B0 mean | B2/B0 mean of per-seed ratios | B2/B0 median [min, max] | seeds B2/B0 > 1 |
|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | 22 | 67.49 | 69.15 | 66.94 | 42.48 | 0.6144 | 0.6144 | **0.6159 [0.600, 0.618]** | 0 |
| low_aspect_ratio_DEMO | 11 | 72.49 | 70.14 | 66.63 | 43.37 | 0.6183 | 0.6183 | **0.6192 [0.611, 0.620]** | 0 |
| st_regression | 22 | 69.01 | 71.2 | — | 40.69 | 0.5716 | 0.5722 | **0.5858 [0.534, 0.596]** | 0 |

<sub>`node calls per evaluation ρ`</sub>

<sub>combining 1 stage table(s): `the optimiser's path over the configurations — campaign_optimisation`</sub>

<!-- plan_tables: end of main-text table node_calls_per_evaluation -->

<!-- plan_tables: main-text table node_calls_per_run -->

**Table 15.** ***Model-node executions per run**, R, one row per configuration over its own seed set: the mean per arm, then `B2` against `B0` read the same four ways. R = ρ × ε per seed, so this table reproduces check 4's cost ratio by another road; check 4's own table sums the solve phase over the set instead. The arms are `BR`, `B0`, `B1` and `B2`; `B1` is inactive on `st_regression` and its column reads — there. n = 3 (configurations stacked, each over its own seed set — the n column: large_tokamak_nof 22 / low_aspect_ratio_DEMO 11 / st_regression 22 seeds on which every arm converged; never pooled).*

| configuration | n | BR | B0 | B1 | B2 | B2/B0 mean | B2/B0 mean of per-seed ratios | B2/B0 median [min, max] | seeds B2/B0 > 1 |
|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | 22 | 41480 | 42515 | 42842 | 27187 | 0.6395 | 0.6414 | **0.6452 [0.555, 0.746]** | 0 |
| low_aspect_ratio_DEMO | 11 | 169943 | 164997 | 114154 | 74312 | 0.4504 | 0.9156 | **0.5237 [0.081, 3.980]** | 2 |
| st_regression | 22 | 126868 | 106007 | — | 56507 | 0.5331 | 0.5616 | **0.5911 [0.136, 0.753]** | 0 |

<sub>`node calls per run R`</sub>

<sub>combining 1 stage table(s): `the optimiser's path over the configurations — campaign_optimisation`</sub>

<!-- plan_tables: end of main-text table node_calls_per_run -->

**The optimiser's path decomposes that ratio (Tables 12–15).** Per seed R = ρ × ε, where ε is the
count of evaluations of the model set (`sweeps_per_eval.n_evaluations`) and ρ the node calls per
evaluation. The per-evaluation term is the stable one: ρ for `B2/B0` reads **0.6159 / 0.6192 /
0.5858** median with brackets [0.600, 0.618] / [0.611, 0.620] / [0.534, 0.596] and 0 seeds above
1. The evaluation count is not 1 on every configuration: on nof `B2` takes **1.0476** times `B0`'s
evaluations in the median (mean 1.0437, 19 of 22 seeds above 1; 640 against 614.7 per run) while
its iterations are the same (median 1.0000) — the lifted formulation's extra design variable adds
a stencil column, and `B1` shows the same 640; on lad the median is 0.8468 (3 of 11 seeds above 1,
the largest 6.450, which is why the mean reads 1.4816); on st 1.0000 (5 of 22 above 1). The R rows
reproduce check 4 (medians 0.6452 / 0.5237 / 0.5911). **The ε = 1 expectation of §3.5 was pre-declared
on `B1 → B2`, and there it holds exactly**: `B1` and `B2` take the same number of evaluations on 22 of 22
and 11 of 11 seeds (Table D.17, the `B1 → B2` row's *ε = 1 on* column, added by A80). The 1.0476
above is `B0 → B2`, and it is the ownership rung's formulation — one design variable more, one stencil
column more, (nvar + 2)/(nvar + 1) = 22/21 = 1.0476 on nof exactly — not the partition, that adds it; on
lad the same rung reads 0.8468 because the lift shortens the optimiser's path (0.8125 iterations) by more
than the column adds. *(A80: this paragraph had read the expectation against `B0 → B2` and called it
refuted in evaluations.)*

**The path — check 2 (Table D.17).** The summed-over-attempts iteration median of `B0 → B2`
is **1.0000 / 0.8125 / 1.0000**, PASS against ≤ 1.05 on every configuration; the ratio of sums
0.9942 / 0.7012 / 0.9530. `B0 → B1` reads identically on the pulsed configurations (1.0000 /
0.8125), so the partition adds no iteration; the final-attempt construction agrees on nof (0
disagreeing seeds) and differs on lad and st where seeds retried (1 / 1 pairs). The tables' ε column
reads `sweeps_per_eval.n_evaluations` since A80 closed issue I-26 — until then it read `n_model_calls`,
the driver's count of dispatch-body sweeps, under a heading that said evaluations — and gives
**1.0476 / 0.8468 / 1.0000** for `B0 → B2`, the same numbers as Table 13, with ε exactly 1 on
0 / 0 / 14 seeds; the sweep ratio it used to show is now its own column, **2.6524 / 2.1169 / 2.7767**,
a mechanism (block sweeps over a third of the map) and not a cost.

<!-- plan_tables: main-text table cost_sums -->

**Table 16.** ***Check 4 — the cost**: solve-phase model-node executions **summed** over each configuration's seed set, one column per arm, with the partitioned arm's ratio to the flat control. Two sets per configuration: the seeds on which every arm reached an accepted optimum, and the same set less the seeds on which any arm retried. Sums, so the claim is about total work over the set and not about every run — the per-run reading is Table 17's last columns. Prime calls are not model nodes and are in no column here (D19). n = 6 (configuration × set rows, each over its own seeds — the n column).*

| configuration | set | n | BR | B0 | B1 | B2 | B2/B0 |
|---|---|---|---|---|---|---|---|
| large_tokamak_nof | every arm accepted | 22 | 912555 | 935340 | 942522 | 598124 | **0.6395** |
|  | without retried seeds | 22 | 912555 | 935340 | 942522 | 598124 | **0.6395** |
| low_aspect_ratio_DEMO | every arm accepted | 11 | 1869378 | 1814967 | 1255695 | 817436 | **0.4504** |
|  | without retried seeds | 10 | 1200171 | 1159494 | 1174467 | 764602 | **0.6594** |
| st_regression | every arm accepted | 22 | 2791089 | 2332155 | — | 1243161 | **0.5331** |
|  | without retried seeds | 19 | 1462230 | 1624917 | — | 999298 | **0.6150** |

<sub>`cost as sums (check 4)`</sub>

<sub>combining 1 stage table(s): `cost sums (check 4) — campaign_optimisation`</sub>

<!-- plan_tables: end of main-text table cost_sums -->

**RQ2 — the partitioning inside the optimisation, `B0 → B2` (Table 16; per arm Table D.18; headline Tables 15 and 17).** `B2` costs **0.6395 / 0.4504 / 0.5331** of `B0`'s solve-phase model-node executions
pooled (medians 0.6452 / 0.5237 / 0.5911; `B2` cost more on **0 / 2 / 0** seeds), against V3's
pre-declared context 0.64 / 0.45 / 0.53. Without the seeds on which either side retried the lad
ratio is 0.6594 pooled (0.5371 median, n = 10); nof has no retried seed and st's ratio moves to
0.5439 (n = 21). Per module (Table 17 in sweeps, Table D.14 in node calls — the whole run's census): the once-per-run nodes cost
0.0010 / 0.0003 / 0.0004 of the flat arm's, the pulse node 0.3161 / 0.2182 (pooled; deferred on
st), M3 0.7603 / 0.5438 / 0.6583, M1 0.6851 / 0.4671 / 0.6437, and M2 0.8691 / 0.5930 / 0.6680 —
on nof the per-run median for M2 is 0.8765 with one run of 22 above 1 (bracket [0.761, 1.013]),
and on lad the two seeds on which `B2` cost more in node calls (three took more evaluations, Table
D.17) show as 2 of 11 runs above 1 in each of the M1, M2, M3 and pulse rows. The node-call census total of Table D.14 less its
last row (the 63 / 63 / 21 / 24 calls per run outside the solve phase — 25 for `B2` on st, whose
once-per-run set has four nodes: the output path and the audit's sweep) is check 4's solve-phase total.

**The other rungs.** `BR → B0`, the stopping rule inside the optimisation, reads **0.9756 / 1.0300
/ 1.1968** pooled (Table D.18); `B0 → B1`, ownership plus the removal of the output-time
loop, reads **1.0077 / 0.6919** pooled (medians 1.0151 / 0.8049; `B1` worse on 18 of 22 seeds on
nof) — no saving on nof, a third off on lad, where it also shortens the path (0.8125 median
iterations). The lift closes: constraint 93's residual at every accepted optimum of `B1` and `B2`
is **1.659e-05 s / 5.480e-06 s** median (relative 2.304e-09 / 6.744e-10), in the equality block
(Table D.22).

**Against both anchors, and what rose while node calls fell (Tables D.19 and D.20).** `B2/B0`
isolates the architecture at a matched stopping rule and is the ladder's number; the end-to-end
change a user switching from PROCESS as shipped would see is `B2/BR` = **0.6554 / 0.4373 /
0.4454** over the seed sets, against `B2/B0` = 0.6395 / 0.4504 / 0.5331. The gap is the
stopping-rule change `BR → B0` itself — 1.0250 / 0.9709 / 0.8356 — and on the spherical tokamak it
is nine percentage points, so measuring against `B0` **understates** what a user would gain there;
on the large tokamak it goes the other way by 1.6 points. Neither ratio is more correct and the
report's headline uses `B0`, because that is the anchor the ladder decomposes against. What rose
instead of node calls is the dispatch: `B2` walks the dispatch body 117 303 / 157 515 / 280 798
times against `B0`'s 44 606 / 86 460 / 111 121, 2.6 / 1.8 / 2.5 times as often, each walk over a
third of the map. The prime's contract holds exactly — **0.9998 / 0.9999 / 0.9999 prime calls per
dispatch sweep**, one `set_fw_geometry()` per sweep to four decimals — and the cost D19 excludes
from every ratio above has a size: **0.1961 / 0.1927 / 0.2259 prime calls per counted node call**.
Both are counts; whether one prime call is cheap against one average model node is a timing, and
no conclusion here rests on one (I-10).

<!-- plan_tables: main-text table module_sweeps_optimisation -->

**Table 17.** ***Module sweeps per run**: how often each node group was swept in one whole optimisation, one block per configuration over its own seed set, as the mean with its [min, max] seed bracket. `models` is the group's collapsed-DSM row count, so total calls = Σ sweeps × models, bracketed `[v = 1, v = 0]` over the once-per-run nodes' unknown rows (trap T9). **The per-module ratio column is the result** and is unit-free; the last two columns give that ratio's per-run distribution, which the pooled figure does not show. These are whole-run census counts: they include the output path — two MDA_Output sweeps of every node in `BR` and `B0`, none in `B1`, one execution of each once-per-run node in `B2` — and the exit audit's one sweep of every node in every arm, which is the harness's accuracy instrument and no arm's architecture. Neither cancels from a ratio: the audit's sweep moves a ratio by under 0.2 % in every row but the once-per-run one, where it is half of `B2`'s count, and the output path differs by arm; check 4's cost table sums the solve phase alone. `B1` is inactive on `st_regression`. Reported, not accepted on. n = 3 (block(s) of this table, each over its own population with its own n in its heading line; never pooled).*

**`nof`** (n = 22)

| module | models | BR | B0 | B1 | B2 | B2/B0 pooled | B2/B0 per-run median [min, max] | runs B2 > B0 |
|---|---|---|---|---|---|---|---|---|
| M1 | 24 | 1978 [1758, 2280] | 2028 [1793, 2396] | 2041 [1821, 2381] | 1389 [1241, 1624] | **0.6851** | 0.6909 [0.598, 0.799] | 0/22 |
| M2 | 10 | 1978 [1758, 2280] | 2028 [1793, 2396] | 2041 [1821, 2381] | 1762 [1573, 2058] | **0.8691** | 0.8765 [0.761, 1.013] | 1/22 |
| M3 | 11 | 1978 [1758, 2280] | 2028 [1793, 2396] | 2041 [1821, 2381] | 1542 [1378, 1805] | **0.7603** | 0.7670 [0.657, 0.887] | 0/22 |
| PULSE | 1 | 1978 [1758, 2280] | 2028 [1793, 2396] | 2041 [1821, 2381] | 641 [573, 749] | **0.3161** | 0.3189 [0.276, 0.369] | 0/22 |
| once per run | 3 | 1978 [1758, 2280] | 2028 [1793, 2396] | 2041 [1821, 2381] | 2 | **0.0010** | 0.001 | 0/22 |
| total calls | 49 | 96933 | 99350 | 100013 | 68566 | **[0.690, 0.736]** | 0.6959 [0.602, 0.805] | 0/22 |

**`lad`** (n = 11)

| module | models | BR | B0 | B1 | B2 | B2/B0 pooled | B2/B0 per-run median [min, max] | runs B2 > B0 |
|---|---|---|---|---|---|---|---|---|
| M1 | 24 | 8096 [2904, 31870] | 7860 [2810, 31216] | 5437 [2535, 17172] | 3671 [1709, 11595] | **0.4671** | 0.5420 [0.084, 4.126] | 2/11 |
| M2 | 10 | 8096 [2904, 31870] | 7860 [2810, 31216] | 5437 [2535, 17172] | 4661 [2175, 14723] | **0.5930** | 0.6891 [0.106, 5.240] | 2/11 |
| M3 | 11 | 8096 [2904, 31870] | 7860 [2810, 31216] | 5437 [2535, 17172] | 4274 [1992, 13488] | **0.5438** | 0.6324 [0.097, 4.800] | 2/11 |
| PULSE | 1 | 8096 [2904, 31870] | 7860 [2810, 31216] | 5437 [2535, 17172] | 1715 [799, 5419] | **0.2182** | 0.2539 [0.039, 1.928] | 2/11 |
| once per run | 3 | 8096 [2904, 31870] | 7860 [2810, 31216] | 5437 [2535, 17172] | 2 | **0.0003** | 0.0005 [0.000, 0.001] | 0/11 |
| total calls | 49 | 396682 | 385140 | 266409 | 183454 | **[0.476, 0.508]** | 0.5533 [0.085, 4.207] | 2/11 |

**`st`** (n = 22; arms BR·B0·B2)

| module | models | BR | B0 | B1 | B2 | B2/B0 pooled | B2/B0 per-run median [min, max] | runs B2 > B0 |
|---|---|---|---|---|---|---|---|---|
| M1 | 24 | 6044 [1890, 39952] | 5051 [1895, 14084] | — | 3251 [1363, 9635] | **0.6437** | 0.7156 [0.165, 0.894] | 0/22 |
| M2 | 10 | 6044 [1890, 39952] | 5051 [1895, 14084] | — | 3374 [1368, 10319] | **0.6680** | 0.7235 [0.169, 0.955] | 0/22 |
| M3 | 11 | 6044 [1890, 39952] | 5051 [1895, 14084] | — | 3325 [1389, 9929] | **0.6583** | 0.7314 [0.168, 0.929] | 0/22 |
| once per run | 4 | 6044 [1890, 39952] | 5051 [1895, 14084] | — | 2 | **0.0004** | 0.0007 [0.000, 0.001] | 0/22 |
| total calls | 49 | 296172 | 247497 | — | 148348 | **[0.599, 0.653]** | 0.6644 [0.153, 0.841] | 0/22 |

<sub>`module sweeps per run, the optimisation phase`</sub>

<sub>combining 3 stage table(s): `module sweeps per run — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`; `module sweeps per run — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`; `module sweeps per run — st_regression — campaign_optimisation · BR·B0·B2`</sub>

<!-- plan_tables: end of main-text table module_sweeps_optimisation -->

**Read the per-module ratios; the total is for reconciliation only (Table 17).** Three things
the pooled ratio of check 4 does not show, and the sweep form does. **The improvement is not
per-run universal.** On lad **2 of 11 runs** have `B2` sweeping *more* than `B0` — up to 4.1× in
M1, 5.2× in M2 and 4.8× in M3 — and the per-run medians sit well above the pooled figures there
(0.5420 / 0.6891 / 0.6324 against 0.4671 / 0.5930 / 0.5438), because the pooled ratio is a
total-work statistic dominated by a few very long runs (`B0` sweeps per run: mean 7 860, max
31 216). Even on nof, uniform on the total, **one run of 22 comes out at 1.013 in M2**. Both
readings are legitimate and they answer different questions; publishing only the pooled one would
assert a uniformity the runs do not have. **The flat arms' columns are one repeated number.**
`BR`, `B0` and `B1` read the *same* sweep count in every module row of every block — a flat sweep
executes everything once — which is a free consistency check on the module accounting, and it
holds exactly. **M3 is where the partition does real work and M2 is where it does least**
(0.7603 / 0.5438 / 0.6583 against 0.8691 / 0.5930 / 0.6680), while the once-per-run set falls from
every sweep to **2** per optimisation, a factor of about a thousand — most of the headline saving
in fractional terms and none of it in difficulty, since nothing live reads those nodes. The total
row is again an interval, `[0.690, 0.736] / [0.476, 0.508] / [0.599, 0.653]`, over the same
unknown row attribution; no per-module ratio depends on it.

**Accuracy at exit (Table D.21).** Over the arm group's finished runs the restricted maximum
residual of `B2` is 0 / 0 / 7.497e-12 median and **7.257e-16 / 5.315e-15 / 3.587e-11** at its
maximum on the frozen ruler — every value far below τ = 1e-6 — against `B0`'s 1.150e-11 / 0 /
4.894e-14 median. `BR`'s maximum on lad is `inf` on `current_drive.eta_cd_dimensionless_hcd_primary`
(the per-run components-above-τ column, companion Table F.15, reads 1 on two of its 23 runs;
§5.7). The per-run components-above-τ columns are companion Table F.15.

**Cost beside the node calls.** The arrangement-method (prime) calls `B2` adds are one per sweep of
the dispatch body — **5 331.0 / 14 318.5 / 12 762.5 per run** on average, 117 281 / 157 504 / 280 776
summed over its 22 / 11 / 22 runs in the seed set (Table D.18, two columns of their own, never
pooled into the node calls; `report_counts_check.py` §6 finds the per-run count equal to the run's
dispatch sweeps on every one of the 55 runs). Per evaluation that is about 8.3 / 8.4 / 9.1 (the per-run
mean over Table 13), the optimisation's sweeps per evaluation — **not** the 13.2 / 12.9 / 14.8 of
the displaced single evaluations (Table D.5), whose entries sit 100× further from the fixed
point. *(A80: the sentence had carried the evaluation phase's figure over.)* The output-time loop costs exactly two sweeps per run in `BR` and `B0` and none in `B1`
and `B2`; the attempt-summation identity holds with residual 0 on every run that finished with
status ok, while a crashed or unconverged start carries no solve-phase total and reads NO with no
residual — both are per-run tables and are companion Table F.8 (the identity) and companion Table F.9 (the per-run overhead).

### 4.4 The same cells, computed a second time

Every cell of Tables 7–17 and Tables D.2–D.24 and of the companion's tally tables was recomputed from the run
records by `harness/measurement/analysis.py`, which imports none of the tally's constructions, and
compared without tolerance: **141 tables, 17 554 cells, 0 mismatched** (gate `recomputation`, one
row of Table D.1). Of those, **17 454 are cells of the tables** — 1 486 rows, 13 010 from a
construction and 4 444 composed as a string — and 99 are the published values that stand beside
them (48 similarity verdicts and 3 seed sets); the recomputed copies themselves are not rendered —
that row is the check, and the gate's record holds the cells.

## 5. Discussion

*Written 2026-09-14 by the orchestrating session from the rendered results only — the campaign
population, 949 records at `57dc0c14`, rendered by `--plan-tables` from the stage records at
`004eb06b` after A75 (campaign-tally-source); the table references were re-pointed at Appendix D's
numbered tables by A79 (report-captions) on 2026-09-15, the numbers unchanged; audited against the
tables by A80 (report-accuracy-audit) the same day — every sentence it changed says so in place. Every number below
is a cell of Appendix D or of the companion file; the table it comes from is named. Denominators:
25 seeds offered per arm per configuration; Phase A tables are over 25 runs per arm in the displaced
regime and 20 / 19 / 14 per arm at the stencil points (every evaluation finished), Phase B tables over
the seed set on which every arm converged — 22 on
`large_tokamak_nof`, **11** on `low_aspect_ratio_DEMO`, 22 on `st_regression` (Table 10).
The pre-declared expectations are §3.4 and §3.5's; where a measurement refutes one it is named so.*

### 5.1 What each rung measured, per configuration

**`A1 → A2` / `A0 → A2` — the partitioning, one evaluation (RQ1; Table D.5, the
displaced regime; Table D.5 the stencil regime; Table D.6 matched accuracy).** The partitioned architecture costs **0.56 / 0.58 / 0.50** of the flat arm's
model-node evaluations per call (pooled; medians 0.571 / 0.571 / 0.492) on the large tokamak, the
low-aspect-ratio machine and the spherical tokamak, worse on 0 of 25 seeds each. V2's context
figures were 0.522 / 0.568 / 0.502: reproduced to within a few hundredths, on a different entry
construction. In the stencil regime the saving is smaller — **0.62 / 0.64 / 0.58** forward,
0.64 / 0.66 / 0.56 backward — because a one-variable displacement from a fixed point leaves the flat
arm little to iterate; the plan's transfer statement (§3.4–§3.5) uses both regimes and both are on the
page. Matched accuracy holds and is not a near thing: at the audit position the restricted maximum
scaled residual is **identical** for `A1` and `A2` on both pulsed configurations (median 3.8e-10,
p90 1.7e-8 on the large tokamak; exactly 0 on every run of the low-aspect-ratio machine) and for
`A0` and `A2` on the spherical tokamak (5.4e-9 / 2.0e-8), so the F = 10 similarity rule of §3.4
check 1 is met with a factor of 1. The whole-state audit beside it is large for `A2` (median 2.4,
0.18, 0.26): those are the components the configuration's once-per-run deferred nodes write, which a
single evaluation of the reduced map does not update, excluded from the restricted statistic by the
derived membership rule and published so the exclusion can be seen.

**The same fixed point, not merely an equally converged one (Table D.9, added after the
campaign by A76 (fixed-point-distance); reported, not accepted on).** The matched-accuracy
table says how far each arm's exit state is from *a* fixed point; the table beside it says how far
the two arms' exit states are from *each other*, on the same restricted set and the same ruler,
computed from the exit states the runs wrote and no model run. On the headline pair the distance is
**5.1e-12 / 0 / 1.2e-11** median (p90 1.8e-10 / 0 / 4.6e-11; worst seed 2.7e-10 / 0 / 6.6e-11) for
`A2/A1` on the large tokamak and the low-aspect-ratio machine and `A2/A0` on the spherical tokamak,
with **0 of 25** pairs holding any restricted component at or above τ = 1e-6 on every configuration,
and no discrete component or constant differing on any pair. The low-aspect-ratio machine's
partitioned and flat exit states are *bit-identical* over every restricted component on all 25
seeds (restricted worst exactly 0). The stencil regime reads the same: `A2/A1` 2.6e-12 / 0 forward and 0 / 0 backward on the
pulsed configurations, `A2/A0` 1.1e-10 / 5.3e-11 on the spherical tokamak, 0 pairs above τ. So the
partition reaches the flat arrangement's fixed point, not a neighbouring one, on every entry of every
configuration — the assumption the per-call ratio above rests on, now a measured cell. The two other
rungs are on the page for what they show: `A0/AR` reads 2.6e-8 / 0 / 1.5e-7 median, which is the
distance upstream's stopping rule leaves (the same numbers as `AR`'s own audit residual), and
`A1/A0` reads **9.7e-2 / 7.0e-2** median on the pulsed configurations with 25 of 25 pairs above τ,
argmax `power.qac` / `power.e_plant_net_electric_pulse_*` — pinning the burn time moves the plant
block's fixed point by a tenth of its scale, which is the ownership rung's inconsistency seen on the
coupling state rather than on the burn time alone, and is why the previous revision's pair `A2/A0`,
published beside, reads the same 9.7e-2 / 7.0e-2: that pair compared two different fixed points.

**`A0 → A1` — ownership of the burn time (Table 8).** Pinning the burn time to a
constant costs nothing measurable per call (pooled 0.93 / 0.98, median 1.00, worse on 0 seeds) and
leaves the declared inconsistency: a burn-time residual at exit of 155 s / 526 s median (6.3 % /
5.3 % relative), the rung's own statistic, published per run and never pooled into a cost.

**`AR → A0` — the stopping rule (RQ4; Tables D.5 and D.6).** Upstream's
objective/constraint test at its two-pass floor is cheaper per call than the coupling-state test at
τ on two configurations (0.90 and 0.84 pooled against `A0` — on the large tokamak Table D.5's
ratios are against `A1`, 0.9688 for `AR` and 1.0781 for `A0`, whose quotient is the 0.8986; 0.8425
directly on the spherical tokamak; equal on the low-aspect-ratio machine, where both stop after
exactly five sweeps on every seed) — and it stops **further from the fixed point**: `AR`'s
restricted residual is 2.6e-8 / 1.5e-7 median against `A0`'s 5.0e-10 / 5.4e-9 on the large and
spherical tokamaks, a factor of 52 and 29, and 0 against 0 on the low-aspect-ratio machine. *(A80:
the sentence had read "0.97 and 0.84 against `A0`" — the 0.97 is against `A1` — and "30–50".)*
That is what the predicate-matched control is a control *for*: `B0` is `BR` with a stopping rule
that reaches a stated accuracy, so that every rung above it compares arms at matched accuracy.

**`B0 → B1` — ownership in the optimisation, and the output-time loop (Table D.18).** Lifting the burn time to the optimiser and dropping upstream's
output-time loop costs **1.008 / 0.692** pooled (medians 1.015 / 0.805) on the two pulsed
configurations — no saving on the large tokamak, a third off on the low-aspect-ratio machine, where
it also shortens the optimiser's path (summed iterations 0.81 median, 0.70 sum ratio). The output
loop's own cost is exactly two sweeps per run in `BR` and `B0` and zero in `B1`/`B2` (the
per-run overhead tables, companion Table F.9), so it is not what moves the ratio. The lift closes: constraint 93's residual
at every accepted optimum is 1.7e-5 s / 5.5e-6 s median (2.3e-9 / 6.7e-10 relative), in the
equality block.

**`B1 → B2` and `B0 → B2` — the partitioning inside the optimisation (RQ2; Tables 16 and D.18;
per module Table 17; the path Tables 12–15).** The
headline: `B2` costs **0.640 / 0.450 / 0.533** of `B0`'s solve-phase model-node evaluations pooled
(medians 0.645 / 0.524 / 0.591; worse on 0 / 2 / 0 seeds), against V3's pre-declared context
0.64 / 0.45 / 0.53 — the same numbers to two decimals, from a rebuilt harness, a different entry
construction and 25 seeds. Without the retried seeds the low-aspect-ratio ratio is 0.66 pooled
(0.54 median), the reading §3.5 asked for beside the pooled one. `BR → B0` reads 0.976 / 1.030 /
1.197 pooled against the expected 0.98 / 1.03 / 1.16. The `ε = 1` expectation holds where it was
pre-declared and in the quantity it was declared in: `B1` and `B2` take exactly the same number of
evaluations on every seed of the set — 22 of 22 and 11 of 11 (Table D.17, the `B1 → B2` row) —
and the same summed iterations (1.000 and 0.8125 against `B0` for both), so the partition changes what
an evaluation costs and not how many the optimiser takes. The dispatch runs 2.7 / 2.1 / 2.8 times as
many sweeps per run in `B2` (the *sweeps median* column of Table D.17, 2.6524 / 2.1169 / 2.7767:
block sweeps, each over a third of the map), which is the mechanism, not a cost.

**Refuted or qualified expectations, named.** (a) **Same optimum (check 1) FAILs on the
low-aspect-ratio machine**: `B0 → B1` and `B0 → B2` both read a paired relative objective difference
of 4.1e-7 median (passes) and **2.15e-6 p90 (fails the 1e-6 floor)**, with 1 hop of 11 and 2 pairs
below cluster resolution; `BR → B0`'s yardstick is 2.0e-13. Since `B1` and `B2` read the same `r`
to every digit, the difference sits on the ownership rung `B0 → B1` — the lifted formulation lands
on a different optimum on 3 of 11 seeds: the 2 pairs below cluster resolution (1.26e-6 and 2.15e-6
relative) and the 1 hop between objective clusters, 3.1e-4 relative, on the one seed of the set on
which `B0` retried (`report_counts_check.py` §11; Table 11's *hops*, *below resolution* and *retried*
columns) — and not on the partition. On the large tokamak
(2.8e-11 / 4.6e-11) and the spherical tokamak (3.5e-13 / 3.5e-9) check 1 PASSes with margin.
(b) **The low-aspect-ratio seed set is 11 of 25.** Fourteen seeds are outside the set, 13 of them
configuration-invalid — no arm reached an accepted optimum there: 2 crashed in every arm (§5.7), 9
exhausted VMCON's four-attempt retry ladder with `ifail = 5` in every arm, and on 2 the incumbent
exhausted the ladder while the three coupling-state arms hit their loop's 20-sweep cap. The fourteenth
(seed 10) is the one start lost to the intervention arms alone (§4.3). The 10–12 retried seeds per arm
are mostly those ladder exhaustions. Every low-aspect-ratio ratio above is over n = 11 and says so.

### 5.2 The transfer (RQ3)

Phase A's per-call ratio against the realised Phase B ratio, pooled: 0.56 → 0.64 (large tokamak),
0.58 → 0.45 (low aspect ratio), 0.50 → 0.53 (spherical). The transfer factor is 1.14, 0.78 and 1.06:
Phase A under-predicts the saving on one configuration and over-predicts on two, by up to 22 %.
The factor decomposition that §3.5 declares — per-evaluation cost × evaluation count × the entry
regime × ownership — is on the page (the stencil-regime per-call ratios 0.62–0.66 sit closer to the
realised 0.64 on the large tokamak than the displaced-regime 0.56 does; the iteration multiplier is 1
on two configurations and 0.81 on the third), but attributing the residual to one factor is issue
**I-17**, which the user has reserved. What the campaign settles is that the transfer is not
systematic in sign, exactly as V3's assessment (§2.2) said, and that Phase A's displaced-regime ratio
is a predictor good to within 22 % here (the transfer factors are quotients of the pooled cells of
Table 8's `A1→A2` / `A0→A2` cells and Table D.18, not cells themselves).

### 5.3 The stopping rule (RQ4)

Covered in §5.1 (`AR → A0`): upstream's test stops 52× and 29× further from the coupling-state fixed
point on two configurations and at the same place on the third, for a per-call saving of 10 % and
16 % (0 on the third; `report_counts_check.py` §8, from Tables D.5 and D.6).
`BR → B0` in the optimisation reads 0.98 / 1.03 / 1.20 — the coupling-state test costs up to a fifth
more on the spherical tokamak, where `BR` also retries more seeds (5 against 3). The control is
therefore a control for *accuracy*, bought at that price, and the headline ratios are stated against
it, never against `BR` (user, 2026-09-11).

### 5.4 The trust step (RQ5)

No V4 arm measures it (V3's joint-test arm — V3's `B2`, not today's `B2` — was removed, §3.2). A43 (st-trust-gap) answered it on V3's records: a single
schedule pass reaches the flat fixed point bit for bit once the blocks are solved exactly. The
campaign's `B2` (the partitioned arm) exit audit is consistent with that: 0 components above τ at the accepted point on
every converged run on every configuration (Table D.21; the per-run column is companion Table F.15), with the spherical tokamak's
`B2` restricted median 7.5e-12 against `B0`'s 4.9e-14 — a factor 150, two orders, both far under
τ = 1e-6.

### 5.5 The per-sweep overhead

Counted, not timed (the per-run overhead tables, companion Table F.9; the
numbers here are companion Table F.9's seed-0 rows). `B2` evaluates the convergence predicate about 2.3×
as often as `B0` per run (4 839 against 2 069 tests on the large tokamak at seed 0) over widths of
239 against 840 components, so the components compared per run are **fewer** (1.16 M against 1.74 M).
The counted overhead cannot be the source of a wall-clock gap; on the spherical tokamak 10.8 % of
`B2`'s sweeps visit the empty `PULSE` block (I-20a), disclaimed where it bears and costing no model
evaluation.

### 5.6 The predicate trial

`frozen` against `mixed` (companion Table F.5; the gate row is in Table D.1): on every pair tried
the two rulers' runs are
bit-identical and no decisive pass changed its verdict (0 verdicts changed over 8–16 predicate
evaluations per run). The `mixed` ruler reads the same run's exit residual smaller (by up to 5.4× on the
large tokamak's `A2`, seed 1: `0x1.f5b2a3ea40bd7p-1` against `0x1.774db44e2d2b1p-3`;
`report_counts_check.py` §9 over the 9 pairs whose residual is not 0), so a threshold stated on it would
be a looser threshold; the experiment's τ is stated on `frozen` and nothing in §4 depends on the choice.
**The pre-declared adoption rule of §3.6 was not applied.** It reads: gates 1–3 pass and the
measurement is neutral → `mixed` is adopted as V4's predicate and audit ruler. Gate G8 passed with its
teeth and the 12 pairs it measured were neutral, so the rule as written adopts `mixed`; the campaign
was pressed and is reported on `frozen`, and the trial's measurement was also smaller than §3.6
declared (`A0`/`A2` at 2 seeds as a gate, not `A0`/`A1`/`A2` at 25 seeds in the campaign). The
departure is recorded here (A80, 2026-09-15) rather than repaired. **Ruled (D30, the user,
2026-09-15: "I am fine with recording the departure, please do"): V4 stands on the `frozen` ruler
and the departure is recorded, not repaired.** V4's numbers are therefore frozen-ruler numbers: the
rule was met (G8, 12 of 12 pairs bit-identical) and not applied because the campaign was pressed
before the rule was re-read. Nothing acceptance-bearing depends on it — the exit audit is printed on
both rulers, and every cost quantity is a count of model-node executions of runs that were made under
`frozen`; since `mixed` is never tighter than `frozen`, a change of ruler could only have stopped some
runs earlier, which cannot be applied to runs already made, only to their reporting. Keeping `frozen`
also keeps V4 on V3's ruler, so the V3 context numbers (0.64 / 0.45 / 0.53) stay comparable. V5
applies the adoption rule before its campaign or drops it; a future revision adopting `mixed` must
restate τ.

### 5.7 Robustness events, reported without a robustness claim

Twenty-eight of 275 optimisations did not finish (Table 10; the failure tables are companion Table F.7): 20 crashed with PROCESS's own
`RuntimeError: Failed to converge after 50 iterations, value is nan` from a model-internal Newton
solve at a displaced start, and 8 — on the low-aspect-ratio machine only — were refused by their
coupling-state loop's 20-sweep cap (the harness stamps both `crashed`; the taxonomy tables split them;
*A80: the sentence had read "crashed … all with PROCESS's own RuntimeError"*). On the large tokamak seeds 5, 20 and 21 crash in **all four arms** —
configuration hardness, dropped paired. On the low-aspect-ratio machine `BR` crashes on 2 seeds,
`B0` on 2 plus 2 unconverged, `B1` and `B2` on 2 plus 3 unconverged; the unconverged ones are the
block solver's own exit (`ModuleSolveFailure: block FLAT / M1 did not converge in 20 sweeps`,
`current_drive.eta_cd_dimensionless_hcd_primary` at `inf`), and on the same variable `BR` reaches
the audit with an infinite residual on 2 runs. The spherical tokamak loses no seed to a crash. The
intervention arms therefore do not finish on 5 low-aspect-ratio starts against `B0`'s 4 and `BR`'s 2,
on a variable the incumbent also cannot hold finite; counted in accepted optima the difference is one
start — 11 for `B1` and `B2` against 12 for `BR` and `B0` (seed 10, §4.3) — because on the other lost
seeds no arm reached one: 9 of them are VMCON exhausting its retry ladder (`ifail = 5` after four
attempts) in every arm, a failure the taxonomy tables count as finished (`report_counts_check.py` §3).
**Stated per arm over the 25 starts offered rather than through the seed-set filter** (Table 10, added 2026-09-15 under D29): the rates are 22 / 22 / 22 / 22 on the large tokamak,
12 / 12 / 11 / 11 on the low-aspect-ratio machine — the intervention arms lose one start (seed 10)
that the flat arms solve — and 24 / 23 / — / 23 on the spherical tokamak, where the two asymmetric
failures cancel in count and not in cost: `B2` gives up on seed 5 after 479 630 node calls where
`B0` accepts at 175 413, and `B0` gives up on seed 10 after 667 989 where `B2` accepts at 129 012
(companion Table F.7). The seed set drops both starts and neither cost enters a ratio.
The plan makes no robustness claim and this report makes none.

### 5.8 Threats to validity that survived the design

- **The objective/structure confound (decision (b))** stands: `B1`/`B2` optimise the lifted
  formulation, `B0`/`BR` the original. §5.1(a) shows it bites on the low-aspect-ratio machine at p90.
- **Small denominators where a configuration is hostile:** n = 11 on the low-aspect-ratio machine.
  Its ratios are the least certain in this report and its same-optimum check is the one that fails.
- **Location non-identification:** correctness is gated on `norm_objf` and the feasibility audit
  (D6), never on iteration variables; two optima closer than 1e-5 relative are "below resolution",
  and 2 such pairs are counted on the low-aspect-ratio machine.
- **The prime's excluded cost:** `n_arrangement_method_calls` is 13.2 / 12.9 / 14.8 per evaluation in
  `A2` (Table D.5) and 5 331 / 14 319 / 12 763 per optimisation on average in `B2` — one per
  dispatch sweep; 117 281 / 157 504 / 280 776 summed over the 22 / 11 / 22 runs of the seed set (Table D.18, columns *arrangement·method calls / run* and *Σ over the set*; *A80: the sentence had
  called the sum "per optimisation"*), stamped beside every node-call table and never pooled into it
  (D19). A reader who
  weights the prime as a model node must add it; it is not a model node.
- **The written file** carries a post-write value of `tfcoil.insstrain` 0.7 % off the accepted
  state in every Phase B arm (A67, I-21); no acceptance quantity reads it.

## 6. Conclusion

*Each research question of §1.2, per configuration (large tokamak / low aspect ratio / spherical
tokamak), with its number, denominator and pre-declared verdict — three configurations, so this is a
case study and not a benchmark set, and the conclusion it licenses is an existence proof that the
architecture alone changes the cost in model-node evaluations (D29, 2026-09-15).*

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
floor; 3 of 11 pairs above the floor, 1 of them a hop between objective clusters at 3.1e-4), where the
difference sits on the ownership rung and not on the partition.

*Added 2026-09-17 at the user's instruction (task A88 (function-weighted-sweeps)):* the
**direction** of the saving does not depend on how the modules are weighted and its **magnitude**
does — the aggregate of the same per-module sweep ratios reads 0.50–0.58 in node calls, 0.66–0.79
in collapsed-DSM rows and 0.63–0.81 in functions for one evaluation, and 0.45–0.64, 0.48–0.74 and
0.45–0.75 inside the optimisation, every per-module ratio at or below 1 except M2 on the large
tokamak's evaluations at 1.0078 (Appendix D.4, Tables D.23 and D.24); node calls remain the
acceptance unit.

**RQ3 — transfer.** Phase A's displaced-regime per-call ratio predicts the realised optimisation
ratio to within 1.14 / 0.78 / 1.06; the transfer is not systematic in sign. The attribution to one
factor is I-17, reserved by the user; the terms it needs are on the page.

**RQ4 — the stopping rule.** Upstream's objective/constraint test saves 10 % and 16 % of model-node
evaluations per call against the coupling-state test at τ = 1e-6 and stops 52× and 29× further from the
fixed point on those two configurations (0 % and identical on the third); in the optimisation the coupling-state
control costs 0.98 / 1.03 / 1.20 of the incumbent. The control buys stated accuracy at that price.

**RQ5 — the trust step.** Not measured by a V4 arm; A43's answer on V3's records stands and the
campaign's `B2` exit audits (0 components above τ on every converged run) are consistent with it.

**The sentence the experiment licenses about §1.2:** *with every physics and engineering model
byte-identical to upstream, rearranging the driver alone — solving the models in three blocks with
the burn time owned by the optimiser — reaches the same accepted optimum on two of three
configurations at 0.53–0.64 of the model evaluations, and on the third, at 0.45, the same optimum on
8 of 11 seeds and a different one on 3 (2.15e-6 relative at the p90; 3.1e-4 on the one seed that
changes objective cluster); the per-call saving of roughly half measured without the optimiser
transfers to the optimisation to within 22 %.*

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

**Table A.1.** *The folder's top-level files: one row per file, its name and role; the `harness/`
package's internals are the implementation plan's.*

| file | role |
|---|---|
| `EXPERIMENT_REPORT.md` | this document — plan (§1–§3), results (§4), discussion and conclusion (§5–§6) in one file; no version token in file names inside the versioned folder (user, 2026-09-10); every change after approval a dated entry in Appendix C. Named `EXPERIMENT_PLAN.md` until 2026-09-15 |
| `experiment_runner.py` | one-button entry point: `--selfcheck`, `--gate`, `--measure`, `--plan-tables write\|check`, `--smoke`, `--campaign`, `--jobs`; refused the campaign until approved |
| `RESULTS_TABLES_FULL.md` | the companion file of Appendix D: every full result matrix (per-run, per-seed and per-pair tables, the full versions of tables whose per-seed columns the report omits, the second implementation's tables), numbered `Table F.n`, generated whole by `--plan-tables write` and guarded by `--plan-tables check`; never hand-edited (A79 (report-captions), 2026-09-15) |
| `run_stamp_survey.py` | the survey behind "this press re-made no run": `tree_git_head` read out of every run record before and after a press (trap T13) |
| `report_counts_check.py` | every count the report states — the 949 / 921 / 28, the 25 per arm, the seed sets 22 / 11 / 22 with every seed outside them by arm and disposition, the crash taxonomy by seed, the retried seeds, the prime-calls-per-sweep identity, ε on `B1 → B2` per seed, `AR/A0`, the predicate trial's ruler ratio, the 30 gates / 163 teeth — re-derived from the records through the harness and printed beside the report's figure (A80 (report-accuracy-audit), 2026-09-15) |
| `PROCESS/` | V4's own copy of the PROCESS package (D20); every V4 driver change lives here; `models/` frozen at `c0ae5b28`, gated. `PROCESS/PROVENANCE.json` names the source commit (`f2dc9243`) and every file's sha256; `PROCESS/copy_gates.py` is the copy-identity gate, G0′ and the smoke import, nine teeth (A46 (process-copy), merged 2026-09-10) |
| `PROCESS_diff.py` | shows every change the experiment made to PROCESS: a `git diff` of `PROCESS/process/` against the copy's source commit, grouped by file with a plain-language overview (user, 2026-09-10) |
| `harness/` | the self-contained package (per the implementation plan): `core/`, `experiment/`, `child/`, `gates/`, `measurement/`, `data/` (the committed per-configuration artifacts and input files), `reference/` (the committed reproduction reference), `chain.py`; every verification gate and every measurement stage is implemented here (its own `README.md` is the map) |
| `runs/` | untracked bulk artifacts |
| `.gitignore` | `runs/` untracked; the copy's `.dat` files re-included against the repository-root `*.dat` pattern (added at A46's merge) |

## Appendix B — Traceability to the improvement list

**Table B.1.** *Traceability: one row per improvement-list item — where the method (§3) absorbs
it, or why not.*

| item | absorbed in | status |
|---|---|---|
| 0 prime inside the intervention; `A1u` retired | §3.2, §3.3 | decided (user) |
| 1 `AR`/`BR`; `unconverged-at-cap`; G0 refusal | §3.3, §3.4 check 4, §3.9 | decided (user) |
| 1a second amplitude | §3.4, §3.10 | ruled (a): the stencil regime, not δ = 0.001 (D21, 2026-09-10); as built 2·nvar points per arm and sign (§3.4) |
| 1b `MDA_Output` out of the intervention arms | §3.3, §3.9 G9 | decided (user); driver change (d) |
| 1c the pinned flat arm, `A1` (the list names it as of 2026-09-10; Appendix C, 2026-09-15) | §3.2, §3.3, §3.4 | decided (user) |
| 1d naming | §3.2 | decided (user; `per_call`) |
| 2 empty blocks / nodes | §3.3 | **rejected** under (d): left as is and disclaimed (D21, 2026-09-10); the sweep share is 0 / 0 / 10.84–11.30 % |
| 3 per-sweep counters | §3.5 check 5 | accepted under (d); built (A58 (driver-predicate-counters), 2026-09-10); the hypothesis it tested is **closed in the negative** on counts — the list's heading says so |
| 4 objective/structure confound | §3.7 (b) | ruled: no fourth configuration in V4, disclosed in every cross-configuration caption (D21 (b), 2026-09-10); it bites on lad at p90 (§5.1 (a)) |
| 5 clusters vs floor | §3.5 check 1b | declared resolution category |
| 5a predicate trial | §3.6, §3.9 G8 | built (A59 (driver-predicate-mode), 2026-09-11); ran as gate G8 on 12 pairs: neutral, 0 verdict changes; **the adoption rule was not applied** — §5.6, awaiting the user's ruling |
| 5b one seed set, one format | §3.5, §3.7 (c) | accepted (D21 (c), 2026-09-10); as built in every optimisation-phase table |
| 6 within-cluster in both implementations | §3.5 check 1a | absorbed |
| 6a class-level classification; read census; Phase A provenance; G4 per namespace | §3.8 (ii), §3.9 G4 | absorbed |
| 7 G1–G3c at the campaign commit | §3.9 | absorbed |
| 8 V3's joint-test arm (V3's `B2`, not today's) in the DSM overlay | — | **dropped** with that arm (user, 2026-09-10) |
| 9, 10 (A43's candidates: sub-tolerance injection; permutation control) | — | not in V4's method; open on the list |
| 6b the trace instrument's argmax on a zero residual (A43) | — | not in V4's method; open on the list |
| 11 `tfcoil.insstrain` above τ at the accepted point | §3.3 | diagnosed as an instrument artefact (A61, `fd480aff`) and, in the written file, as PROCESS's own 0.7 % gap (A67, I-21); no acceptance quantity reads it |
| 12 G4's doctored runs bypass `--resume` | — | discharged (A71, `24e5fe2f`) |
| 13 G1's `--resume` press rewrites the manifest's commit | — | discharged (A73, `4ca8cff5`) |
| 14 δ at seed 0 composed two ways; 15 a never-bound name found only by a press | — | filed 2026-09-14 (A72, A73); open on the list |
*(Rows 9–15 and the statuses of 1a, 2, 3, 4, 5a and 5b brought to the list's current state by A80 (report-accuracy-audit), 2026-09-15; the list is the authority on each item's state.)*

## Appendix C — Change log

*Entries before the renaming entry of 2026-09-15 (including A76's, dated the same day but written before the rename) use the arm names of their day and are not rewritten: `A0p` is
today's `A1`, `A1` is today's `A2`, `B3` is today's `B2`; a `B2` in those entries is V3's removed
joint-test arm, not today's partitioned optimisation arm (the renaming entry of 2026-09-15, below).*

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
| 2026-09-14 | **Execution approved by the user** (*"You can run the experiment"*), approval commit `57dc0c14` (header dated, `EXECUTION_APPROVED = True`; `--campaign` added to the button at `e247e48d`). **The campaign pressed** from a detached worktree at `57dc0c14`, 3 workers: 949 runs, 921 ok, 28 crashed optimisations (PROCESS's own Newton solve, `nan` from displaced starts); a first press attempt was killed with the orchestrator's shell before any record was written and left nothing. The chain stopped at the tally (no campaign source, I-24); A75 (campaign-tally-source, `004eb06b`) added the source family and re-rendered §4 as the campaign population (169 tables). **§5–§6 written from §4**; header EXECUTED AND REPORTED. |
| 2026-09-15 | **Renamed `EXPERIMENT_PLAN.md` → `EXPERIMENT_REPORT.md`** at the user's instruction (*"rename the PLAN file to REPORT"*, *"clean up the framing of the document accordingly"*), with `git mv`. Framing: title; the status header rewritten as a report's — the document's three parts named, the approval record and the campaign's facts kept, the superseded 2026-09-10 draft header removed (it said: draft, not approved; methodology only; every §3.7 choice ruled by D20–D22; A43 and A44 absorbed — all of it recorded in the entries above and readable at `3abea2c6`); Appendix A's file table brought to the folder as it is (`phase_a.py`/`phase_b.py` never built, the surveys and the harness's subpackages added; the separate `EXPERIMENT_REPORT.md` row folded into this one); §3.5 (ii) gains an as-built bracket. No §4 cell, no §3 rule and no §5/§6 sentence changed. Every live reference re-pointed: `plan_tables.plan_path`, `harness_survey`, the runner's messages and docstrings, `config`, `failure`, `records`, `arms`, `switches`, `chain`, the harness README, the queue v2 and the implementation plan. Left as written: V2/V3, the PROCESS copy, `PROVENANCE.json`, archived reports and the archived queue (D17). |
| 2026-09-15 | **A76 (fixed-point-distance): the between-arm distance of the evaluation phase's fixed points, added to the analysis from the campaign's exit states** (the user, 2026-09-15: *"add the between-arm distance of phase A as an additional analysis to the analysis scripts, and add the results to the report"*). §4.2 gains a *fixed-point distance* table beside each matched-accuracy table — the predicate's own residual evaluated between two arms' `y_exit.json` at the same entry, restricted to the components the once-per-run nodes do not write (the audit's own exclusion, re-derived and checked against the digest the audit stamped), one row per rung of the ladder with the headline pair marked; `stats.fixed_point_distance` is the declaration, `tally_evaluation.fixed_point_distance` computes it through `harness/child/predicate.py`, `analysis._fixed_point_distance` re-derives it from the artifacts and the hex literals importing no line of the predicate. **Reported, not accepted on**: no acceptance rule was pre-declared. Zero PROCESS runs; 0 of 1 096 run records re-made. Gates re-pressed with `--resume`: `recomputation` 13 174 compared / 0 mismatched over 93 tables (from 12 715 / 84 — the 459 new cells are the nine distance tables), `tally_contracts` 279 / 0 with an eleventh tooth (one exit state doctored in a scratch copy: a kept component moved by 1e-3 of its scale raises the restricted distance to 1.000e-3 and counts the pair above τ; an excluded one moved past the whole-state maximum leaves the restricted distance at 1.523e-10 and carries the whole-state column), `run_kind_separation` 2 994 / 0, `self_containment` 52 / 0; §4.1 reads 30 PASS, 156 of 156 teeth; self-check PASS. §5.1 gains one paragraph under the `A0p → A1` rung, from §4 cells only. Not renamed here: the arms keep their current names (A78 (arm-renames) follows). |
| 2026-09-15 | **A78 (arm-renames): the arms renamed so the rungs read rung for rung — `A0p → A1`, `A1 → A2`, `B3 → B2`; `AR/A0/A1/A2` against `BR/B0/B1/B2`** (the user, 2026-09-15: *"In the v4 report, rename A0p and A1 to A1 and A2, and B3 to B2. That makes the naming of the rungs reflect the parallelism in the switch matrix … it should be applied consistently throughout the v4 folder"*). A rename, not a method change: no number changed. Applied in place in §1–§3, §5–§6 and Appendices A–B; §4 re-rendered by `--plan-tables write` after the tally stages were re-run over the same 949 campaign records (`check` IDENTICAL); every mention of V3's removed joint-test arm now reads "V3's `B2`" so today's `B2` cannot be read as it; §2.1 quotes V3's results under V3's names and says so; this appendix's earlier entries keep their day's names (the line at its head). Harness: the matrix, the registry's V3 name map (`switches.PREVIOUS_ARM_NAMES = {R: BR, A1: A2, B3: B2}`), every gate, both tallies, the analysis, the README, `PROCESS/CHANGES.md` (no `.py` under `PROCESS/` changed: `copy_identity` and `g0prime` PASS). **The records were not re-made.** The 949 campaign records and the 139 seeded gate records stamp the old names; one declared table, `records.RECORDED_ARM_NAMES`, is applied in `records.read` — the one reader — so every consumer sees today's names; a record made after the renaming stamps `arm_naming` (by the pool) and is read as written; a translated record's `job_digest` is re-derived over the translated identity, the stamped one kept in the in-memory trace `arm_name_translation`; the pool resolves a job's directory by that digest (`pool.directory_for`) where a record exists and refuses to remove another job's record; a record naming an arm nobody declared is refused by name. Gate `resume_identity` surveys every record by how its name was read — 1099 records: 458 translated (`A0p → A1` 132, `A1 → A2` 233, `B3 → B2` 93), 641 unchanged or stamped, 0 refused — and has four new teeth (160 teeth in all). `--jobs all`: 1075 distinct jobs, `--resume` would keep 1044 before and after the renaming (the 31 not kept are the 28 crashed campaign optimisations and G5's three hand-composed jobs, both as at the base). The reproduction reference's `arm` fields regenerated names-only (`reference.py --rename-arms`; 9 fields, 3 provenance keys) and GR pressed once: 256 / 0. **The press in this worktree (`--gate all --resume`, then the gates the stopped chain did not reach, one press each): 30 PASS, 0 FAIL, 161 of 161 teeth** — after one fix on the branch: at the first press `switch_composition` (G5) FAILed 3 of 141, its kept from-the-matrix records (`0677a9b3`, made in the A73 worktree) against its hand-composed records re-made here differing only in `resolved_switches`' absolute artifact paths under the two worktrees, every physics value equal; the gate now compares those paths relative to the experiment directory of the record that carries them (its own `tree` stamp), with a tooth (a resolved value flipped disagrees; the paths re-rooted under another worktree agree), and the pool renders path-valued `override_env` identity entries tree-relative so the hand-composed job's identity — the reason `--jobs all` at the base listed those three jobs "no record on disk" in every worktree but A73's — is portable (digest changed for those 3 jobs only; `--jobs all` keeps 1044 of 1075 before and after, 1047 once their records exist). G5 pressed once after: 141 / 0. Runs made: 7 (G7's tooth evaluation, re-made by design every press; G5's three hand-composed `B2` optimisations twice — once under the old identity, once under the portable one, ~29–52 s each); every other record kept, 1096 → 1102. §4 against the base with the names reversed (`renamed_section_diff.py`): 1439 tokens reversed, 13 of 4966 line positions differ, all of them the §4.1 gate table and marker re-made by this press (the new records and their commits, `resume_identity`'s new population, the census entry pressed as `optimisation`, G8's excluded-value count 240 → 294 from the translation trace) — 0 in a measurement cell. |
| 2026-09-15 | **A79 (report-captions): the report's presentation brought to an academic paper's** (the user, 2026-09-15: *"Captions in the report should be much more concise a few lines at most. the rest should be clear from the main text"*; *"the report should mimic academic paper style in terms of how the captions are handled"*; *"move the big tables to an appendix (with some explanation/context there), report only the conclusions in the main text"*; *"there should simply not be any tables listing results per seed. I don't want full result matrices, but summarizing tables"*; the three headline shapes of `docs/plans/REPORT_HEADLINE_TABLES.md`). **§4 is now hand-written conclusions** — per research question and rung, the numbers that carry a verdict, each pointing at its table by number — and **the rendered tables are Appendix D — Results tables**: 80 summarising tables numbered `Table D.1`–`D.80` (the gate table; the three headline shapes as Tables D.2–D.10 of that day of that day — node calls per module per configuration with per-run brackets, pooled `B2/B0`, per-run median and the runs `B2 > B0`; the optimiser's path over the configurations as iterations, ε from `sweeps_per_eval.n_evaluations` (issue I-26's field), ρ and R = ρ × ε; node calls per block, configurations stacked, per evaluation-phase source; then cost per call, matched accuracy, fixed-point distance, the ownership rung, the failure taxonomies, the seed sets, checks 1–4 and the accepted-optimum accuracy), each under **one caption of a few lines** (median 368 characters, at most 485 — `caption_census.py`), with every construction's declaration printed once in D.0 from the stages' own records and a hand-written context paragraph per group. **No table with a row per run, seed, pair of runs or predicate evaluation is in the report**: the per-sweep overhead (both phases), the attempt-summation identity, the failure table and the predicate trial, the full versions of the five table kinds whose per-seed columns the report omits, and the second implementation's 101 tables are rendered, unchanged in content, into the generated companion file [`RESULTS_TABLES_FULL.md`](RESULTS_TABLES_FULL.md) as `Table F.2`–`F.150`, guarded by the same `--plan-tables check`, which now compares both documents and resolves every `Table D.n` / `Table F.n` reference in the hand-written text. The doubled-caption defect (373 `*Caption:` lines for 187 tables at `4dac585e`: the record's `markdown` carried the caption and the renderer printed it again) is fixed at its cause — the record carries the grid alone. The pooled `n = 100` line under per-row tables is gone. §3's tables are `Table 1`–`Table 6`, Appendix A's and B's `Table A.1` / `B.1`, with captions of a few lines. §5's and §6's table references re-pointed at the numbered tables; no number in them changed. **No number changed:** `results_cells_unchanged.py --base 4dac585e` — every one of the 33 467 cells of the old §4 is a cell of Appendix D or the companion file with the same value (0 absent, 0 differing); the 16 new tables (8 tally + 8 recomputed) are the headline shapes; the gate table's `recomputation` row moved from 93 tables / 13 174 cells to 101 / 14 394 because the table set grew, and `tally_contracts` correspondingly. Records translate arm names at read; the tally stages were re-run over the same 949 records at `57dc0c14`, **0 PROCESS runs**. |
| 2026-09-15 | **A80 (report-accuracy-audit): the report audited sentence by sentence against Appendix D and the companion file** (the user: *"critically reassess the accuracy of the experiment_report v4"*); the findings table is `docs/reports/A80_report_accuracy_audit.md`. **Corrected in place** (each corrected sentence says so): the population — 28 records stamped `crashed` are 20 PROCESS `RuntimeError` crashes and 8 refusals by the coupling-state loop's 20-sweep cap, not "28 crashed … all with PROCESS's own RuntimeError" (header, §4, §5.7); the low-aspect-ratio seed set — 14 seeds outside, 13 configuration-invalid, of which 9 are VMCON exhausting its retry ladder with `ifail = 5` in every arm and 2 the incumbent's ladder exhaustion beside the coupling-state arms' cap, and one seed (10) lost to the intervention arms alone; accepted optima 12 / 12 / 11 / 11 per arm (§4.3, §5.1 (b), §5.7); **the pre-declared `ε = 1` expectation is on `B1 → B2` and holds exactly on 22 of 22 and 11 of 11 seeds** — §4.3 had read it against `B0 → B2` and called it refuted in evaluations, §5.1 had substituted iterations for evaluations (the `B1 → B2` row the plan's §3.5 declared "reported beside" is now in Table D.11, with an *ε = 1 on* column); `AR → A0`'s per-call saving is 10 % / 0 / 16 % and its residual factor 52× / — / 29×, not "3–16 %" and "30–50×" (§5.1, §5.3, §6 RQ4; §5.1's "0.97 against `A0`" was against `A1`); check 1 on lad differs on 3 of 11 seeds with the worst pair 3.1e-4 on the one retried seed, not "2 of 11" and not "within 2.2e-6" (§5.1 (a), §6); the transfer factor 0.78 is 22 % off, not "a fifth" / "±20 %" (§5.2, §6); `B2`'s st exit residual is two orders above `B0`'s, not three (§5.4); the predicate trial ran 8–16 evaluations per run and the rulers differ by up to 5.4×, not 9–15 and 8× (§5.6); the prime calls of Table D.12 are a sum over the seed set, 5 331 / 14 319 / 12 763 per optimisation on average and 8.3 / 8.4 / 9.1 per evaluation, not "per optimisation" and not the evaluation phase's 13.2 / 12.9 / 14.8 (§4.3, §5.8); `copy_identity` is the second PASS row with a nonzero mismatched count (7 permitted-edit files; §4.1); G1's 54 144 are 2 825 record values + 51 319 output-file lines and `tally_contracts`' 559 are 303 + 256, now shown in the cell (§4.1, D.1); the evaluation-phase denominators are 25 per arm in the displaced regime only — 20 / 19 / 14 at the stencil points, 1 in the entry reference (§4 intro, §4.2, §5 intro); "63 / 63 / 21 / 24" outside the solve phase is 25 for `B2` on st; the 2 lad seeds above 1 in Table 8 are node calls, 3 took more evaluations (§4.3). **As-built brackets in the plan (§3, text unchanged):** the stencil regime is 2·nvar points per arm — no lifted column exists in Phase A — 396 evaluations, not 418 (§3.4, §3.10); the predicate trial ran as gate G8 on 12 pairs, not 150 campaign runs, and **its pre-declared adoption rule was not applied** — neutral on a passed gate adopts `mixed`, the campaign ran on `frozen`; recorded in §5.6 for the user's ruling (§3.6, §3.10, App. B item 5a); G7's teeth 9/9 not 5/5 and G5's compared set as built (Table 5); the 20-sweep cap binds the flat control's one block too (Table 6); §3.5's transfer identity still spelled `B3` — renamed `B2`; the format-review and "every table in §4" sentences bracketed (§3.7, §3.8 (iii)). **Appendix D and the companion, through the renderer only:** issue **I-26 closed** — check 2's evaluation column reads `sweeps_per_eval.n_evaluations` (ε) in `tally_optimisation.py` and `analysis.py`, the old `n_model_calls` ratio kept beside as *sweeps median*, the plan's `B1 → B2` row added, the `n_model_calls` schema sentence in `records.py` corrected (the driver's sweep count, not evaluations); check 4 gains *arrangement·method calls / run* beside the sum; Table 9's caption states n per configuration, never summed (D21 (b)); the gate table shows a summed *compared* count's parts and names both nonzero-mismatched PASS rows; the predicate-trial declaration's dangling "§4.2.5" re-pointed. Gates re-pressed with `--resume` at `86430cb6` and `1f378e58`: `recomputation` 14 445 compared / 0 mismatched over 101 tables (from 14 394; the 51 new cells are the new columns and rows), `tally_contracts` 559 / 0 (303 + 256), `run_kind_separation` 3 000 / 0, `self_containment` 52 / 0; `--measure gate_table --resume` 30 PASS, 0 FAIL, 161 of 161 teeth; `--plan-tables write`, `check` IDENTICAL, 80 tables in Appendix D before and after (no number shifted, T17), 150 in the companion; stamp survey before and after: 1 102 records, 0 whose commit changed, 0 new — **0 PROCESS runs**. Every count the report states re-derived from the records by `report_counts_check.py` (committed) and printed beside the report's figure; the two `y_exit.json` files under the campaign tree that are not campaign records are the lifted-input derivation's baseline evaluations (`input_files/<configuration>/baseline_evaluation/`), so 921 under `campaign/` = 674 + 247 exactly. Appendix A gains `report_counts_check.py` and the `harness/data/`, `harness/reference/` folders; Appendix B's item statuses brought to the improvement list's current state, rows 9–15 added. Not changed: the merged reports and this appendix's earlier entries (their "28 crashed" stands as the record of its day, D17). |
| 2026-09-15 | **A82 (per-arm-success): reliability stated per arm, the case study named, the wall-clock section withdrawn** (rulings **D29** and **D30**, the user, 2026-09-15). D29 (1) (*"I follow your advice here"*, on A81 (benchmarking-practices)'s finding F1): a **per-arm success table** — one declared construction `stats.per_arm_success`, computed in `tally_optimisation.py`, re-derived independently in `analysis.py` under `recomputation` — states, per configuration and optimisation arm, the 25 starts offered, the accepted optima (status ok and `ifail == 1`), every other start by outcome class (finished with the optimiser's exit code; crashed in PROCESS's own code; refused at the coupling-state loop's 20-sweep cap) and the starts lost that another arm accepted, with the seed set beside; **Table D.10**, the seeds named in companion Table F.11 and per seed in companion Table F.4. Accepted optima of 25: nof 22 / 22 / 22 / 22, lad 12 / 12 / 11 / 11, st 24 / 23 / — / 23. Reported, not accepted on — no pre-declared rule reads it and no verdict changes. §4.3 and §5.7 gain one sentence each. D29 (2) (*"the non-node cost term is not relevant, as is the wall-clock time. Because this is an existance proof …"*): §3.5 check 5's promised wall-clock section and §1's non-node-cost-term line carry a dated as-built bracket **withdrawing the promise**; no timing is published and the plan text is not rewritten. D29 (3) (*"yes, this is a case study, not a full benchmark indeed"*): §6's preamble gains one clause — three configurations, a case study, the conclusion an existence proof in node calls. **D30** (*"I am fine with recording the departure, please do"*): §5.6 states the ruling — V4 stands on the `frozen` ruler, the predicate trial's adoption rule was met (G8, 12 of 12 pairs bit-identical) and not applied, nothing acceptance-bearing depends on it, V5 applies the rule before its campaign or drops it — and §3.6's as-built bracket says the departure stands. Appendix D grew 80 → 83 tables and the companion file 150 → 162, so every `Table D.n` ≥ D.67 moved by 3 and the companion's F.14 onward moved; **30 citations were re-pointed** in §4.3, §4.4, §5.1, §5.3, §5.5, §5.6, §5.7 and §5.8 (trap T17). The entries above keep the numbers of their day. `recomputation` 15 122 / 0 over 107 tables; `tally_contracts` 577 / 0; `run_kind_separation` 3 000 / 0; `self_containment` 52 / 0; 30 PASS / 0 FAIL, 161 of 161 teeth; 0 PROCESS runs and 0 of 1 102 run records re-made. |
| 2026-09-15 | **A83 (headline-tables-in-text): one construction, one table; the headline tables back in §4** (the user, 2026-09-15: *"keep the headline tables, with their discussion, in the main text"*; *"[the tables] seem expanded over a bunch of different tables with one row, which makes no sense at all"*; the orchestrator's layout in `docs/plans/REPORT_HEADLINE_TABLES.md`). The renderer gained a declared `Layout` per construction (`stack`, `merge`, `single`) and combines the tally's per-(configuration, source) tables: Appendix D 83 → 14 tables, the companion 162 → 12, one-row tables 48 → 0; Tables 7–9 (node calls per block, displaced; node calls per module, configurations stacked; the optimiser's path) rendered inside §4.2/§4.3 between marker pairs, each followed by its discussion, and not repeated in Appendix D; the second implementation's copies no longer rendered (gate `recomputation`'s row is the statement). Every old cell present with the same value (`report_cells_preserved.py`: 38 451 cells compared, 0 differing; the 1 663 rows absent are the recomputed copies); 92 citations re-pointed; `check` IDENTICAL for the five rendered blocks; gates unchanged (`recomputation` 15 122 / 0). Regime kept as a row key on the block, distance, cost-per-call and accuracy tables (agent's decision (b), reversible). **At the merge (orchestrator):** §4.1's gate-table prose brought to Table D.1's cells — `recomputation` 107 tables / 15 122 cells (was 101 / 14 394), `tally_contracts` 577 = 321 + 256 (was 559 = 303 + 256), stale since A82 grew the table set. |
| 2026-09-15 | **A85 (v3-table-formats): the tables in the V3 report's forms** (the user: *"How I want them formatted is based on v3 report section 4 and 5 … If you deviate, justify it"*). A new construction, *module sweeps per run*, in both tally phases and both analysis twins (1 154 new cells under `recomputation`, 122 tables / 16 276 cells compared, 0 mismatched; two teeth added to `tally_contracts`, 13/13); the renderer grows V3's cell forms (`mean [min, max]` in one cell, `median / p90` in one, bold result column and verdicts, per-configuration blocks under a bold heading line, repeated keys blanked). §4.2 gains Table 12 (module sweeps per run, evaluation phase — V3 §4.5's table), §4.3 Tables 8–11 (the optimiser's path as four tables of one quantity — V3 §5.3's shape) and Table 13 (module sweeps per run, optimisation phase — V3 §5.5.1's table); node calls per module moved to Appendix D.9; Appendix D 14 → 15, companion 12 → 13. Every pre-existing cell present unchanged (19 426/19 426 by `report_cells_preserved.py`); four stale citations re-pointed (T17). Deviations from V3 are listed in the task report (`nof` for `tok`; one `once per run` row for V3's `vacuum` and FF rows; `models` total 49 of the map's 52). Eleven mapped V3 tables are not yet built and follow in A86. Zero PROCESS runs. Entry written by the orchestrator at merge; the task wrote none. |
| 2026-09-15 | **A86 (v3-tables-remainder): the rest of the previous revision's §4 and §5 tables, and the main text in reading order** (the user, 2026-09-15: *"How I want them formatted is based on v3 report section 4 and 5. Start by reproducing these kinds of tables … If you deviate, justify it"* — the half A85 (v3-table-formats) left). **The eleven tables it had not built now exist**, each a construction in the tally with an independently written twin in `analysis.py`: check 1's matched accuracy by configuration with the similarity **verdicts as cells** (Table 7), the per-call cost with the ladder's rungs `AR→A0`, `A0→A1`, `A1→A2` and the prime calls per evaluation (Table 8), the full restricted-audit distributions with `Σ components > τ`, the worst run and both rulers (D.7), module scope (D.2, static), the excluded namespaces' p90s from every run's own residual vector (D.8), the problem each configuration poses before and after the lift (D.12), the location diagnostic matched **by name** with D6's sentence in its caption (D.14), the identity `B1 → B2` in evaluations, iterations and a bit-identical `norm_objf` (D.15), check 4's cost as sums with the arms as columns (Table 17), both anchors (D.18) and the sweeps-and-prime-calls accounting (D.19); the taxonomy and the same-optimum table moved into §4.3 as Tables 11 and 12. Four new constructions in `stats.py` — `iteration_variables`, `point_difference`, `namespace_residuals`, `figure_of_merit` — each with a tooth on `tally_contracts` (13 → 17 teeth, 163 → 167 in the gate table). **The residual departures from the previous revision's grids, closed**: `B2/B0 mean` on the optimiser's path is now the **ratio of the means** under that heading — the campaign-cost statistic the previous revision published there — and the mean of the per-seed ratios is renamed beside it (`report_cells_preserved.py` carries the rename as a declaration); `runs B2 > B0` is one cell `k/n`; the block heading lines read `**`nof`** (n = 22)` with the population sentence in the caption and Table 12's `n = 25 per arm`; the `quantity` and `arms` columns of the path's four tables are stated in their captions (`Layout.omit`, 24 label cells, declared and counted). **The main text is in reading order**: §4.2 Tables 7–10, §4.3 Tables 11–18, each followed by the prose that reads it. **No number changed**: 1 846 rows and 19 771 cells preserved, 0 missing and 0 differing (`report_cells_preserved.py --base ab3d339a`); the 1 278 new cells are the nineteen new stage tables, computed twice and compared with **0 mismatched** (`recomputation`: 141 tables, 17 554 compared). Every citation re-pointed by `report_citations_repoint.py`, rewritten for a move map rather than a shift: five citations that had not existed since A79 and five that would have survived as a **plausible wrong table** (trap T17's addition) repaired, the change log held out of the sweep because its entries state the table set of their own day. `check` IDENTICAL for all twelve §4 blocks, Appendix D and the companion; 0 dangling. Zero PROCESS runs; 0 of 1 102 run records re-made. |
| 2026-09-15 | **A87 (v3-grid-polish): the three grids that were still not the previous revision's** (the user, 2026-09-15: *"How I want them formatted is based on v3 report section 4 and 5 … If you deviate, justify it"*, the residue A86 (v3-tables-remainder)'s assessment listed). **(1) The reliability table's merged whole left the main text.** §4.3's Table 11 was per-arm success merged with the failure taxonomy and the seed set — twenty-three columns, twenty of them printed, three of those one label repeated down a configuration's rows. The merge is now **Table D.12**, first of Appendix D's optimisation-phase group, and §4.3 carries the per-arm success construction **alone**, in the previous revision's §5.1 form: `arm`, `starts offered`, `accepted optima`, the three outcome classes (`finished, ifail = 5`, `crashed (RuntimeError)`, `coupling-loop cap (ModuleSolveFailure)`), `lost, another arm accepted` and the seed set stated once at the head of each configuration's arm rows — eight columns, the configurations stacked. **No cell moved out of the documents**: Table 11's 11 rows and 88 cells are all cells of Table D.12, which keeps the taxonomy's tracebacks, the configuration-invalid seeds and the retried seeds; a cell may appear in more than one table (declared, `Layout.shares_tables_with`, and counted by `report_cells_preserved.py`), it may never be lost or changed. **(2) The stacked tables' sub-heading rows** read `**large_tokamak_nof (n = 22)**` — the configuration, its source regime where one table holds more than one, its own n, and the arm set only where the block is not the phase's whole ladder — instead of `large_tokamak_nof · campaign_optimisation · BR·B0·B1·B2 — n = 22 (seeds on which every arm of large_tokamak_nof converged)`. The tally's table name is the construction line under the grid, where the renderer already names every stage table it combines; the population sentence is in the caption, generated from the constituents' own `denominator_is` and said once for the grid. This is the reduction A86 made for the block heading lines, applied to the row groups; report and companion alike. **(3) Check 1's ratio triples are one cell**: Table 7 reads `1.0000, 1.0000 → **PASS**` where it read `med` | `p90` | `verdict`, by a declared `verdict` cell join, `—` where the pair has no ratio; its `verdict note` column (3 cells, no number among them) is stated in the caption, the *reference* column already naming the declared pair. Table 7 goes from 14 columns to 9 — the previous revision's 7 plus `n (runs)` and `reference`, which V4 needs because it declares the acceptance pair per configuration. **The widest grid in §4 goes from 20 columns to 13.** Rendering only, in `plan_tables.py`'s declarations: no construction, no stage record and no cell changed — 1 958 rows and 20 917 cells preserved, **0 missing and 0 differing** (`report_cells_preserved.py --base f1848d63`), §4 12 tables, Appendix D 21 → 22, the companion 15, 0 tables with one row. Appendix D from D.12 on moved by one and the companion's full versions re-ordered, so **22 numbers and 5 phrases were re-pointed** by the committed script and every citation re-read (trap T17): three sentences cited Table 11 for the taxonomy's *ok* column, its tracebacks and the seed-set table's retried seeds, which Table 11 no longer carries. `recomputation` 17 554 / 0 over 141 tables; `tally_contracts` 679 (423 + 256) / 0, 17/17 teeth; `run_kind_separation` 3 000 / 0; `self_containment` 52 / 0; 30 PASS / 0 FAIL, 167 of 167 teeth; 0 PROCESS runs and 0 of 1 102 run records re-made. The entries above keep the numbers of their day. |

| 2026-09-17 | **A88 (function-weighted-sweeps): the per-node table leaves the main text; the per-module sweep tables gain function-weighted twins in the appendix; the skew of the aggregate under three weightings stated** (the user, 2026-09-17: *"move the per node tables to the appendix. Only keep per module in the main text. Also, add to the appendix table 10 and 18 but then with a per function weight. I want to see how this skews the headline average. You can find the nr of functions per module from the DSM decomposition … each model has a set of submodels (individual functions) defined with the parent-child relations in the DSM."*). **(1)** §4.2's Table 9 of that day — node calls per block on the displaced entries — is no longer rendered in the main text: the construction is rendered **whole** as Appendix D's Table D.3, the acceptance regime one row group among its four (one construction, one table, amendment 29; the reason for two tables went with the main text's), so the main-text tables numbered 10 to 18 on that day are numbered 9 to 17 on this one; §4.2's RQ1 paragraph reads the headline ratio and the absolute totals from Table 8 and the per-module ratios from Table 9 (the sweep table — the same numbers), and §5.2's transfer inputs from Table 8's rung cells; the main text's only per-module breakdowns are the two sweep tables. **(2)** Appendix D gains group **D.4** with the function-weighted twins of Tables 9 and 17 (Tables **D.23**, **D.24**): the same grid with `models` replaced by **`functions`** — the number of individual callables in the module, a model's callable submodels from the dependency analysis's decomposition at pin `PROCESS_at_36ac820e`, a model with no submodel counting as one (its entry method) — the total row Σ sweeps × functions per arm and its ratio the `[v = 1, v = 0]` bracket over the once-per-run nodes' own functions. The sweep cells and per-module ratios are the sweep tables' own, **republished, never recomputed**: each twin is a merge (rule xviii, `shares_tables_with`) of the sweep table with a new construction carrying only the new cells (`module sweeps per run, function-weighted total`; `stats.functions_by_group` beside `dsm_rows_by_group`, `stats.weighted_total` reused; a twin in `analysis.py`; one tooth on `tally_contracts`, 18/18). The counts come by the node map's own route (trap T9): `arch_surgery/fixedpoint/gen_function_counts.py` read the sibling's three per-configuration exports once — the row → model mapping taken from the sibling's own `figures.driver_order`, run read-only in its environment and cross-checked against the export's `process_line_order` — and committed `dsm_function_counts.json` with provenance (sibling HEAD, pin read from its `config.py`, export digests); the copy in `harness/data/` is entered by `data_provenance.py add` with its own source commit (17 files + the predicate module, 18/18 identical). Found and named, not placed: the sibling's tokamak export has since split D8's `Constraints` row in two (its M125), and on `st_regression` the export's rows shift (`ElectronCyclotron` at row 21, `CsFatigue` absent) so M1 holds 25 collapsed-DSM rows there, not the node map's 24 — the `models` column is the node map's and is unchanged. **(3)** D.4's context paragraph states the aggregate under the three weightings for both phases and three configurations (nof / lad / st, evaluation: node calls 0.5625 / 0.5772 / 0.5016, DSM rows [0.724, 0.767] / [0.742, 0.786] / [0.655, 0.709], functions [0.695, 0.794] / [0.709, 0.811] / [0.626, 0.720]; optimisation: 0.6395 / 0.4504 / 0.5331, [0.690, 0.736] / [0.476, 0.508] / [0.599, 0.653], [0.650, 0.746] / [0.448, 0.514] / [0.565, 0.653]) and what does not depend on the weight — the aggregate is a weighted mean of the per-module ratios, every one at or below 1 except M2 on `large_tokamak_nof` in the evaluation phase at 1.0078; §6 gains one marked sentence. **No cell lost or changed**: `report_cells_preserved.py --base c04c93bb` finds every old row whole (20 990 of 20 990 cells) but the gate table's own three, whose populations grew (`recomputation`, `tally_contracts`, `self_containment`), and counts 80 new cells; `--plan-tables check` IDENTICAL; gates re-pressed with `--resume`; stamp survey 1 102 records, 0 re-made — **zero PROCESS runs**. Census: §4 12 → 11 tables, Appendix D 22 → 24, companion 15 → 15, one-row tables 0. Report: `docs/reports/A88_function_weighted_sweeps.md`. |
| 2026-09-28 | **A correction: what the optimisation phase's whole-run census adds outside the solve** (the user, 2026-09-28, *"Please fix the report sentence directly"*). Table 17's caption, the module-sweeps declaration in D.0 and the three function-weighted captions said the output pass runs every node once, adds exactly one sweep to every row in every arm and cancels from every ratio. The records say otherwise, and Table D.14's own last row already showed it (63 / 63 / 21 / 24 calls per run outside the solve phase on the large tokamak): the output path is **two MDA_Output sweeps of every node in `BR` and `B0`, none in `B1`, one execution of each once-per-run node in `B2`**, and the remaining 21 calls are the exit audit's one sweep of every node in every arm — the harness's accuracy instrument, not an architecture. Neither cancels from a ratio. The sentence is corrected in the report and in its generators (`plan_tables.py`'s Table 17 caption; `tally_optimisation.py`'s clause, summary and docstring). **No number changes**: every cell is the same census, and the audit's sweep moves a module ratio by under 0.2 % except in the once-per-run row. The D.0 and appendix captions are read from the `tally_optimisation` stage record, which still holds the old wording, so `--plan-tables check` shows those lines as differing until that stage is re-measured. Found while building the paper's tables (`harness/measurement/paper_tables.py`), which leave the exit audit out of the phase B census. |

## Appendix D — Results tables *(rendered by `harness/measurement/plan_tables.py` from the stage records; the **campaign** population — 949 run records at `57dc0c14`)*

**What this appendix is.** Every table of the experiment's results, numbered `Table D.n` in the order printed, each an output of a measurement stage of `experiment_runner.py` read from its record under `runs/gates/<stage>/measurements.json`; no cell is typed by hand (protocol §15) and nothing here computes a number. **One construction, one table**: the tally's per-configuration and per-source tables of a construction are combined into one grid, the configurations and regimes as row groups (D.0 says how). §4 of the main text states the conclusions and points at these tables by number; the **headline tables are in §4 itself** — Table 7 (check 1, matched accuracy), Table 8 (per-call cost), Table 9 (module sweeps per run, the evaluation phase), Table 10 (per-arm success), Table 11 (same optimum (check 1)), Table 12 (the iteration multiplier), Table 13 (the evaluation count ε), Table 14 (node calls per evaluation ρ), Table 15 (node calls per run R), Table 16 (cost as sums (check 4)), Table 17 (module sweeps per run, the optimisation phase) — and are not repeated here. **Only summarising tables are here** — per arm or arm pair and configuration. Every table with a row per run, seed, pair of runs or predicate evaluation, and the full versions of the tables whose per-seed columns are omitted here, are in the companion file [`RESULTS_TABLES_FULL.md`](RESULTS_TABLES_FULL.md) (numbered `Table F.n`, generated by the same renderer and guarded by the same check), which this appendix points at once, here. The second implementation's recomputed copies are **not rendered as tables**: gate `recomputation`'s row of Table D.1 — tables compared, cells compared, cells mismatched — is that check, and the gate's record holds the cells. Table numbers are positional and change when a table is added; a cell is traced by the construction names printed under each grid, never by its number.

**Population: the campaign, not the gate runs.** `EXECUTION_APPROVED` is True and the campaign has run: every cell of this appendix, of §4's headline tables and of the companion file is over the 949 campaign run record(s) made at commit(s) `57dc0c14`, by run kind {'campaign': 949}, by source `campaign_entry_references` 3, `campaign_displaced` 275, `campaign_stencil_forward` 198, `campaign_stencil_backward` 198, `campaign_optimisation` 275. The 145 gate run record(s) at `0677a9b3`, `3983fb0c`, `4ca8cff5`, `50a35de1`, `6f5ba612`, `8996b843`, `d6c48c88` (by run kind {'gate': 143, 'smoke': 2}) were these tables' earlier fill, before execution approval; they are excluded from every published cell **by kind** (gate `run_kind_separation`) and appear only in D.1, which is the gates' own table. The exit audit was taken at position(s) `after_single_evaluation`, `entry_to_write_output_files` with the convergence ruler(s) `frozen` and the exit-audit instrument `whole_data_structure_derived_set`.

**Conventions that hold in every table (D21 (c)).** Absolute cost cells are per-run means with the seed bracket. A ratio against the reference is given three ways: pooled (sum over the set / sum over the set), per-run median with `[min, max]`, and the count of seeds on which the arm cost more. Configurations appear in the fixed order nof / lad / st and are never pooled (D21 (b)). Prime calls appear beside node calls, never inside them (D19). Node-call ratios are the acceptance quantities; timings are context and no conclusion rests on one (I-10). Arm names are `AR / A0 / A1 / A2` and `BR / B0 / B1 / B2` (2026-09-15); the records carry the names of their day and are translated at read (trap T16).

### D.0 Constructions and populations

Every table of this appendix, of the companion file and of the headline tables in §4 is an instance of one **construction**, declared once here — its units, what a row and a column are, how the cells are built (the function in `harness/measurement/stats.py` whose docstring is the declaration), the clauses that bind its reading — and printed under no table. A table's own caption carries only what varies by table: what it shows, its population and denominator, the one thing not to infer. The declarations are rendered from the stages' records, so a construction that changes here changed in the code.

**One construction, one table.** The tally computes a table per *(configuration, source)* because that is how it computes them; the renderer combines the tables of one construction into one grid under a declared layout (`plan_tables.LAYOUTS`), with the configurations and source regimes as row groups under a bold sub-heading row that names the group and states its own n — never a pooled one; what that n counts is in the table's caption, said once for the grid rather than once per group. Every cell of a combined grid is a cell one of those stage tables already held, rendered by that table's own columns; the stage tables it combines are named under the grid, and are the stable citation (a table number is a position, trap T17). An **empty** cell is a column the row's group does not have; `—` is a group's own missing value.

**Populations.** One population family, the sources named in every caption: `campaign_entry_references` — 3 record(s): the campaign population: the entry references — one flat A0 evaluation per configuration from the input file's own design point, the once-per-run cold-start term (plan §3.4), reported beside and never pooled with the displaced or stencil entries; `campaign_displaced` — 275 record(s): the campaign population: the evaluation phase's displaced-entry regime at δ = 0.10 — every arm active on the configuration entered from the same seeded displacement of the reference fixed point, seeds 1–25, one call_models each (plan §3.4); the acceptance regime; `campaign_stencil_forward` — 198 record(s): the campaign population: the evaluation phase's stencil regime, the **forward** points x_i (1 + epsfcn) entered from the reference fixed point, one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; `campaign_stencil_backward` — 198 record(s): the campaign population: the evaluation phase's stencil regime, the **backward** points x_i (1 − epsfcn) each entered from its own forward point's exit — the sequence the optimiser's evaluator executes — one per design-vector column per arm (plan §3.4); paired across arms by column, not seed; `campaign_optimisation` — 275 record(s): the campaign population: the optimisation phase — every arm active on the configuration, one full optimisation per start, seed000 unperturbed and seeds 1–24 displaced at δ = 0.10 on the iteration variables' initial values (plan §3.5); a crashed start is a taxonomy row, never a cost.

**the gate table** (`gate_table`; Table D.1; 1 table).

'plan' is the label the experiment plan's §3.9 table uses, empty where the gate is one of the harness's own checks rather than one of the plan's. 'verdict' is PASS/FAIL on the gate's criterion **and** on every tooth tripping. 'population' is what the gate compared, in its own words; 'compared' is the denominator and 'mismatched' the count of things that differed — both are the gate's own headline pair, and a gate whose criterion is not a count of compared values leaves them empty and states its population in words instead. Where a gate compares more than one kind of thing — coupling-state components, record values, output-file lines — the denominator is their sum and the row's 'denominators summed' names each. 'teeth' is tripped / declared. A gate whose tooth did not trip is not accepted whatever its verdict.

**matched_accuracy_headline** (`matched_accuracy_headline`, stage `tally_evaluation`; Table 7; Table F.1; 3 stage table(s) combined).

- *Units:* dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination; ratios are dimensionless.
- *A row is* one configuration.
- *A column is* one arm's restricted audit maximum as median and p90 over that arm's finished runs, or one reading of a declared pair's similarity ratio, or that pair's verdict.
- *Construction:* stats.accuracy_population and stats.restricted_statistic on the frozen ruler; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the ratio and the verdict are stats.similarity — the larger statistic over the smaller, similar when it is within F = 10 at median **and** p90, with two exact zeros similar by the trivially-similar clause.
- **one ruler**: these cells are the frozen ruler's, V4's declared one (D30); the mixed ruler is published beside in the full-distributions table and the two are never mixed into one column.
- the declared pair is A2/A1 on a pulsed configuration and A2/A0 on a steady-state one — the *reference* column names it; the other pair is published beside and is not the declared acceptance.
- the restricted maximum excludes the components the configuration's once-per-run deferred nodes write; the whole-state maximum is in the matched-accuracy table and is large for A2 by design.
- **n counts runs** over every arm of the configuration in this source, never values (stats.accuracy_population).
- *How to read:* read the verdict against the ratio pair beside it: the rule is within F at median **and** p90, so a PASS needs both.

**cost_per_call_headline** (`cost_per_call_headline`, stage `tally_evaluation`; Table 8; Table F.2; 3 stage table(s) combined).

- *Units:* model-node executions per `call_models` evaluation; arrangement-method (prime) calls are counted in a column of their own; ratios are dimensionless.
- *A row is* one configuration.
- *A column is* one arm's mean node calls per evaluation over its finished runs with the observed [min, max] seed bracket, or one rung of the ladder as a pooled ratio, or the partitioned arm's prime calls per evaluation.
- *Construction:* the arithmetic mean of node_calls_single_eval over the arm's finished runs, with stats.seed_bracket; each rung's ratio is Σ right / Σ left over the runs both sides finished, keyed by seed in a displaced source and by design-vector column in a stencil source.
- **the ladder's rungs, not one comparison**: AR→A0 is the stopping rule alone, A0→A1 the ownership of the burn time, A1→A2 the partition; on a steady-state configuration the ownership rung does not exist and A0→A2 stands in its place.
- the prime calls are stamped beside the node calls and never pooled into them (D19), so the cost ratios above exclude them by declaration and the column names what is excluded (trap T11).
- per-run means with the bracket rather than the previous revision's 25-seed sums: a sum hides both the denominator and the run-to-run spread.
- *How to read:* read the three rung columns across: each is one named change, and their product is the end-to-end ratio AR→A2.

**module_sweeps** (`module_sweeps`, stage `tally_evaluation`; Table F.3; Table 9; Table D.23; 12 stage table(s) combined).

*Applies to `module sweeps per run — large_tokamak_nof — campaign_entry_references`, `module sweeps per run — low_aspect_ratio_DEMO — campaign_entry_references`.*

- *Units:* sweeps of a node group per `call_models` evaluation; `models` is a count of collapsed-DSM rows; the total row is Σ sweeps × models, a count of DSM-row executions; ratios are dimensionless.
- *A row is* one node group of this configuration — the three modules, the pulse node, the feed-forward tail and the once-per-run deferred nodes as the committed node map and the configuration's per-run artifact place them — then the total over those rows.
- *A column is* the group's collapsed-DSM row count, or one arm's mean sweeps of that group per evaluation over its finished runs with the observed [min, max] seed bracket, or the pooled ratio of A2 to the declared reference arm over the runs both sides finished.
- *Construction:* stats.module_sweeps — the census count every node of the group shares, the construction refusing the run if the group's nodes did not execute equally often; the mean is the arithmetic mean over the arm's finished runs; the ratio is Σ A2 / Σ reference over the paired runs; the total row is stats.weighted_total (Σ sweeps × models) with models from stats.dsm_rows_by_group.
- a cell is a **sweep** count, not a node-call count: within a group every model node runs once per sweep, so the ratio does not depend on whether one counts model calls or DSM rows.
- the total does depend on it, and its ratio cell is the interval over the two defensible attributions of the once-per-run nodes' DSM rows — `[v = 1, v = 0]`, v = 1 giving each of them a row of its own and v = 0 leaving the rows with the module the map assigns them (trap T9: per-node DSM rows are not readable here); the per-arm total cells are the v = 1 case.
- the committed node map states 52 DSM rows execute in a sweep and this configuration attributes 49 of them; the remainder are rows of nodes that execute on no configuration of this experiment and are in no row.
- reported, not accepted on: the acceptance quantities are the cost-per-call and matched-accuracy tables'.
- the reference arm is A0 (pulsed, but this population carries no A1 run, so the ratio falls back to the plain flat control — the previous revision's construction, in which the burn-time residual is reported separately rather than being part of the arm.  This is a FALLBACK and not the declared pair).
- *How to read:* read the ratio column down the modules: it is the result, and it is unit-free; the total row is for reconciliation and is an interval.

*Applies to `module sweeps per run — st_regression — campaign_entry_references`, `module sweeps per run — st_regression — campaign_displaced`, `module sweeps per run — st_regression — campaign_stencil_forward`, `module sweeps per run — st_regression — campaign_stencil_backward`.*

- *Units:* sweeps of a node group per `call_models` evaluation; `models` is a count of collapsed-DSM rows; the total row is Σ sweeps × models, a count of DSM-row executions; ratios are dimensionless.
- *A row is* one node group of this configuration — the three modules, the pulse node, the feed-forward tail and the once-per-run deferred nodes as the committed node map and the configuration's per-run artifact place them — then the total over those rows.
- *A column is* the group's collapsed-DSM row count, or one arm's mean sweeps of that group per evaluation over its finished runs with the observed [min, max] seed bracket, or the pooled ratio of A2 to the declared reference arm over the runs both sides finished.
- *Construction:* stats.module_sweeps — the census count every node of the group shares, the construction refusing the run if the group's nodes did not execute equally often; the mean is the arithmetic mean over the arm's finished runs; the ratio is Σ A2 / Σ reference over the paired runs; the total row is stats.weighted_total (Σ sweeps × models) with models from stats.dsm_rows_by_group.
- a cell is a **sweep** count, not a node-call count: within a group every model node runs once per sweep, so the ratio does not depend on whether one counts model calls or DSM rows.
- the total does depend on it, and its ratio cell is the interval over the two defensible attributions of the once-per-run nodes' DSM rows — `[v = 1, v = 0]`, v = 1 giving each of them a row of its own and v = 0 leaving the rows with the module the map assigns them (trap T9: per-node DSM rows are not readable here); the per-arm total cells are the v = 1 case.
- the committed node map states 52 DSM rows execute in a sweep and this configuration attributes 49 of them; the remainder are rows of nodes that execute on no configuration of this experiment and are in no row.
- reported, not accepted on: the acceptance quantities are the cost-per-call and matched-accuracy tables'.
- the reference arm is A0 (steady state: there is no burn-time coupling, the pinned flat control degenerates onto the plain one and is skipped).
- *How to read:* read the ratio column down the modules: it is the result, and it is unit-free; the total row is for reconciliation and is an interval.

*Applies to `module sweeps per run — large_tokamak_nof — campaign_displaced`, `module sweeps per run — low_aspect_ratio_DEMO — campaign_displaced`, `module sweeps per run — large_tokamak_nof — campaign_stencil_forward`, `module sweeps per run — low_aspect_ratio_DEMO — campaign_stencil_forward`, `module sweeps per run — large_tokamak_nof — campaign_stencil_backward`, `module sweeps per run — low_aspect_ratio_DEMO — campaign_stencil_backward`.*

- *Units:* sweeps of a node group per `call_models` evaluation; `models` is a count of collapsed-DSM rows; the total row is Σ sweeps × models, a count of DSM-row executions; ratios are dimensionless.
- *A row is* one node group of this configuration — the three modules, the pulse node, the feed-forward tail and the once-per-run deferred nodes as the committed node map and the configuration's per-run artifact place them — then the total over those rows.
- *A column is* the group's collapsed-DSM row count, or one arm's mean sweeps of that group per evaluation over its finished runs with the observed [min, max] seed bracket, or the pooled ratio of A2 to the declared reference arm over the runs both sides finished.
- *Construction:* stats.module_sweeps — the census count every node of the group shares, the construction refusing the run if the group's nodes did not execute equally often; the mean is the arithmetic mean over the arm's finished runs; the ratio is Σ A2 / Σ reference over the paired runs; the total row is stats.weighted_total (Σ sweeps × models) with models from stats.dsm_rows_by_group.
- a cell is a **sweep** count, not a node-call count: within a group every model node runs once per sweep, so the ratio does not depend on whether one counts model calls or DSM rows.
- the total does depend on it, and its ratio cell is the interval over the two defensible attributions of the once-per-run nodes' DSM rows — `[v = 1, v = 0]`, v = 1 giving each of them a row of its own and v = 0 leaving the rows with the module the map assigns them (trap T9: per-node DSM rows are not readable here); the per-arm total cells are the v = 1 case.
- the committed node map states 52 DSM rows execute in a sweep and this configuration attributes 49 of them; the remainder are rows of nodes that execute on no configuration of this experiment and are in no row.
- reported, not accepted on: the acceptance quantities are the cost-per-call and matched-accuracy tables'.
- the reference arm is A1 (pulsed: the declared reference, because it and the partitioned arm sit on the same reduced map).
- *How to read:* read the ratio column down the modules: it is the result, and it is unit-free; the total row is for reconciliation and is an interval.

**per-arm success** (`per_arm_success`, stage `tally_optimisation`; Table 10; Table D.12; 3 stage table(s) combined).

- *Units:* counts of starts.
- *A row is* one optimisation arm on this configuration.
- *A column is* the starts offered, the accepted optima, every other start by its outcome class, the starts lost that another arm accepted, and the seed set beside.
- *Construction:* stats.per_arm_success — accepted is stats.accepted_optimum (status ok AND the output file's ifail == 1); every other start carries one stats.outcome_class (finished with the optimiser's exit code; crashed in PROCESS's own code, the exception named; refused by the coupling-state loop's sweep cap, ModuleSolveFailure); a start is lost when this arm did not accept and another arm did; the seed set is stats.every_arm_converged.
- **reported, not accepted on**: no pre-declared rule of the plan reads a per-arm rate; the cost tables stay over the seed set and this table states what that filter leaves out (decision D29, 2026-09-15, on A81 (benchmarking-practices)'s finding F1).
- the classes partition the offered starts: accepted plus the class columns sum to the starts offered in every row.
- a seed no arm accepted is configuration hardness (the seed-set table's configuration-invalid column) and is not a lost start of any arm; the lost starts are the asymmetric failures.
- the harness stamps a coupling-loop refusal and a PROCESS exception both as status crashed; the failure class and the traceback separate them here, as in the taxonomy table.
- *How to read:* read accepted over offered as the arm's success rate with its denominator; the lost column is what the seed-set filter hides from a cost ratio.

**same optimum (check 1)** (`same_optimum`, stage `tally_optimisation`; Table 11; 3 stage table(s) combined).

- *Units:* dimensionless: a relative difference of the normalised objective.
- *A row is* one arm pair over the seed set.
- *A column is* the paired relative objective difference's median and p90, the threshold they are judged against, and the clustering statistics.
- *Construction:* stats.relative_objective_difference — |Δ norm_objf| / max(|a|, |b|) per pair, from the hex floats; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); stats.acceptance_threshold = max(F × yardstick, floor) with F = 10 and floor = 1e-06, the yardstick being the BR → B0 spread measured in this same population; stats.clusters at a relative gap of 1e-05.
- the yardstick row carries no threshold and no verdict: it *is* the threshold's calibration.
- *below resolution* counts pairs further apart than the correctness floor and closer than the cluster gap — distinct optima below cluster resolution, a named category and not a rounding remark.
- the retried column is computed from attempts[], never from a stored flag, so a pair containing a retry is visible here as well as in the cost table.
- *How to read:* a verdict is read only where a threshold exists; a hop is a seed whose two sides landed in different objective clusters, and the yardstick pair's own hop rate is the comparator.

**the optimiser's path (headline shape 2)** (`optimiser_path`, stage `tally_optimisation`; Table 12; Table 13; Table 14; Table 15; 1 stage table(s) combined).

- *Units:* counts per optimisation run (iterations, evaluations, model-node executions) and their ratios, dimensionless.
- *A row is* one quantity of the optimiser's path on one configuration (and arm group): iterations summed over attempts, the evaluation count ε, the node calls per evaluation ρ, the node calls per run R.
- *A column is* per arm, the mean over the seed set; for B2 against B0, the ratio of those means, the mean of the per-seed ratios, their median with [min, max], and the count of seeds on which the ratio exceeds 1.
- *Construction:* stats.iterations_summed_over_attempts (check 2's declared statistic); stats.n_evaluations (sweeps_per_eval.n_evaluations, the field issue I-26 names — the driver's histogram summed over the attempts, output path excluded); R = solve-phase node calls summed over attempts[] (check 4's unit); ρ = R / ε per run.  Means are arithmetic over the arm's runs in the seed set; the B2/B0 columns are stats.per_seed_ratio_summary (mean and nearest-rank upper-middle median of the per-seed ratios, their [min, max], the count above 1) — whose **pooled** reading is Σ B2 / Σ B0 over the same seeds, the ratio of the two mean columns beside it and the campaign-cost statistic, and whose **mean** reading is the mean of the per-seed ratios, the typical seed's.
- R = ρ × ε holds per seed by construction, so a configuration's four rows decompose check 4's cost ratio into how many evaluations the optimiser took and what each cost.
- **two statistics, two headings**: `B2/B0 mean` is the ratio of the two arms' means — equal to the ratio of the sums over the same seeds, which is what the campaign cost; `B2/B0 mean of per-seed ratios` is the mean of the ratios a seed at a time, which is what a typical start saw.  They differ by a lot where a few long runs dominate the sums, and publishing one under the other's name would state the wrong quantity (task A86 (v3-tables-remainder)).
- the iteration row is the same construction as check 2's acceptance column, and the ε row the same field as check 2's ε column (issue I-26, closed by task A80 (report-accuracy-audit): until then that column read n_model_calls, the driver's sweep count).
- B1 is absent on a steady-state configuration and reads —.
- *How to read:* an ε row near 1 with an R row well below 1 says the partition changed what an evaluation costs and not how many the optimiser needed; a median far from the mean names a few seeds carrying the difference.

**cost_sums** (`cost_sums`, stage `tally_optimisation`; Table 16; 1 stage table(s) combined).

- *Units:* model-node executions during the solve, summed over the set; the ratio is dimensionless.
- *A row is* one configuration under one published seed set.
- *A column is* one arm's summed solve-phase node calls over that set, or the partitioned arm's ratio to the flat control.
- *Construction:* solve-phase node calls **summed over attempts[]** per run (the attempt-summation identity is printed per run in the companion file), then summed over the set's seeds; the ratio is Σ B2 / Σ B0 over the same seeds.
- **these are sums, so the claim is about total work over the set** and not about every run: the per-run distribution is the per-module table's last columns, which show where the sign reverses.
- the two sets are V4's own — the seeds on which every arm reached an accepted optimum, and the same set less the seeds on which any arm retried — not the previous revision's ok / converged pair, because V4 has one acceptance set and publishes the retry exclusion beside it.
- the output path and the exit audit are excluded from this unit symmetrically in every arm.
- prime calls are not model nodes and are in no column here (D19); they are the sweeps-and-prime-calls table's.
- *How to read:* read the ratio column down the two sets of one configuration: where they agree, nothing in the result depended on a retry.

**module_sweeps** (`module_sweeps`, stage `tally_optimisation`; Table 17; Table D.24; 3 stage table(s) combined).

- *Units:* sweeps of a node group per optimisation run; `models` is a count of collapsed-DSM rows; the total row is Σ sweeps × models, a count of DSM-row executions; ratios are dimensionless.
- *A row is* one node group of this configuration — the three modules, the pulse node, the feed-forward tail and the once-per-run deferred nodes as the committed node map and the configuration's per-run artifact place them — then the total over those rows.
- *A column is* the group's collapsed-DSM row count, or one arm's mean sweeps of that group per run over the seed set with the observed [min, max] bracket, or one of the three readings of B2 against B0: pooled, the per-run median with its bracket, and the count of runs on which B2 swept the group more.
- *Construction:* stats.module_sweeps — the census count every node of the group shares (node_census.per_node_counted, the whole run), the construction refusing the run if the group's nodes did not execute together; stats.per_seed_ratio_summary for the three readings of the ratio; the total row is stats.weighted_total (Σ sweeps × models) with models from stats.dsm_rows_by_group.
- a cell is a **sweep** count, not a node-call count: within a group every model node runs once per sweep, so a per-module ratio does not depend on whether one counts model calls or DSM rows.
- the total does depend on it, and its ratio cell is the interval over the two defensible attributions of the once-per-run nodes' DSM rows — `[v = 1, v = 0]` (trap T9: per-node DSM rows are not readable in this repository); the per-arm total cells and the per-run distribution are the v = 1 case.
- these are whole-run census counts: the output pass runs every node once, so it adds exactly **one sweep to every row in every arm**; it is symmetric across arms and cancels from every ratio it appears in, while check 4's cost table sums the solve phase alone.
- the committed node map states 52 DSM rows execute in a sweep and this configuration attributes 49 of them; the remainder are rows of nodes that execute on no configuration of this experiment and are in no row.
- reported, not accepted on: the acceptance quantity is check 4's solve-phase cost table.
- *How to read:* read the ratio column down the modules — it is the result, and it is unit-free; then read the last two columns, which say whether the pooled ratio holds run by run.

**module_scope** (`module_scope`, stage `tally_evaluation`; Table D.2; 1 stage table(s) combined).

- *Units:* counts of collapsed-DSM rows and of model nodes.
- *A row is* one node group of the partition.
- *A column is* the group's collapsed-DSM row count, whether the map places it inside the iterated loop, or how many of its nodes execute on one configuration and which.
- *Construction:* harness/data/dsm_node_map.json for the row counts and the loop membership; tally_evaluation.node_grouping for the executing nodes — derived from that map and the configuration's per-run artifact, and refused where a record's own exit audit excluded a different node set.
- **no cell here is a statistic**: this table says what the partition *is* on each configuration, and the tables that follow say what it cost.
- the once-per-run group is the configuration's deferred nodes whatever module the map assigns them, which is why it carries no DSM row count of its own (trap T9: per-node rows are not readable in this repository).
- a node absent from a configuration's column does not execute there — the TF-coil family contributes one member per configuration by conductor choice.
- *How to read:* read the per-configuration columns across one row to see where a module is larger or smaller than on its neighbours.

**node calls per block (headline shape 3)** (`node_calls_per_block`, stage `tally_evaluation`; Table D.3; 4 stage table(s) combined).

- *Units:* model-node executions per `call_models` evaluation, per block; the ratio is dimensionless.
- *A row is* one node group of one configuration (the three modules, the pulse node, the feed-forward tail and the once-per-run deferred nodes, each as the committed node map and the configuration's per-run artifact place them), then that configuration's TOTAL over every counted node.
- *A column is* one evaluation-phase arm's mean node calls per evaluation over its finished runs, or the pooled ratio of A2 to the configuration's declared reference over the pairs both sides finished.
- *Construction:* stats.per_node_census (node_census.counted — the measured evaluation alone, frozen before the exit audit's sweep) summed over each group of stats.node_groups; the group's mean is the arithmetic mean over the arm's finished runs; the ratio is Σ A2 / Σ reference over the paired runs (stats.per_seed_ratio_summary's pooled reading), the reference being A1 on a pulsed configuration and A0 on a steady-state one (tally_evaluation.reference_arm).
- the once-per-run group holds the configuration's deferred nodes whatever module the map assigns them: the partitioned arm runs them once, after the solve, so their calls are not a module's loop cost.
- a group absent from a configuration's rows means no such node ran there, not that it cost nothing.
- the TOTAL row is the cost-per-call table's per-run mean and pooled ratio reached through the census, which sums to node_calls_single_eval on every record.
- the arrangement-method (prime) calls are not model nodes and are not in any row.
- *How to read:* read down a configuration's block rows to see where the partition's saving sits; a ratio near 1 on a block means the block is solved about as often as the flat arm sweeps it.

**cost per call** (`cost_per_call`, stage `tally_evaluation`; Table D.4; Table D.5; 12 stage table(s) combined).

- *Units:* model-node executions per `call_models` evaluation; sweeps are walks of the model sequence; ratios are dimensionless.
- *A row is* one arm of the evaluation phase on this configuration.
- *A column is* a per-run mean over that arm's finished runs, with the observed bracket, or one of the three readings of the ratio against the declared reference arm.
- *Construction:* stats.ratio_triple — pooled = Σ arm / Σ reference over the paired runs; median = nearest-rank upper-middle of the per-run ratios; worse = runs on which the arm cost more.  The reference arm is the declared one (tally_evaluation.reference_arm): A1 on a pulsed configuration, A0 on a steady-state one, and A0 as a stated fallback where the population carries no A1 run — the caption says which.
- the arrangement-method calls are stamped beside the node calls and are never pooled into them.
- the empty block visits are included in every sweep count and are disclaimed in the per-sweep-overhead table, which states their sweep share.
- these are campaign runs: the population named above and no other.
- pairs are keyed by seed in a displaced or reference source and by design-vector column in a stencil source; the pairing column's heading says which.
- *How to read:* a pooled ratio below 1 with worse = 0 means the arm was cheaper on every run of this population; a median far from the pooled value means a few runs carry the cost.

**failure taxonomy** (`failure_taxonomy`, stage `tally_evaluation`; Table D.4; Table D.11; 12 stage table(s) combined).

- *Units:* counts of runs; the detail column is text.
- *A row is* one arm on this configuration.
- *A column is* one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.
- *Construction:* stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.
- the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.
- an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.
- *How to read:* a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited.

**matched accuracy** (`matched_accuracy`, stage `tally_evaluation`; Table D.4; Table D.6; 12 stage table(s) combined).

- *Units:* dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.
- *A row is* one arm on one ruler.
- *A column is* the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.
- *Construction:* stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys, never by a prefix rule.
- **the audit position is a column**: a residual taken at the entry to the output path and one taken after the run are different quantities and never share an unlabelled table.
- **the audit instrument's version is read from the record** (stats.audit_instrument), never assumed: task A61 (insstrain-diagnosis) classified the largest residual seen at this commit as an artefact of the instrument — an output-path setting the snapshot does not restore — and task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns.  The instrument column is what tells two otherwise identical tables apart, and the argmax component is read from the record rather than written into this table.
- **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction, so a table showing one column alone reports a change of ruler as a change of accuracy.
- the two rulers' exclusion counts are listed per row and are never pooled; a run whose restricted block is null carries no count at all and reads —.
- **n counts runs, not values** (stats.accuracy_population): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11; the caption says whether every run of the population carried it.
- *How to read:* the restricted column is the declared statistic; the whole-state column is large for the partitioned arms by design — their once-per-run nodes run at the end, so those outputs are stale at the audit — and is published to show the exclusion's size, not judged.

**full_distributions** (`full_distributions`, stage `tally_evaluation`; Table D.7; 3 stage table(s) combined).

- *Units:* dimensionless for the residual columns; counts for the components, sweeps and node calls.
- *A row is* one arm of one configuration.
- *A column is* an order statistic of that arm's restricted audit maxima, a count of components left above τ, or the observed range of a per-evaluation count.
- *Construction:* stats.accuracy_population on both rulers; min and max are stats.seed_bracket's ends, median nearest-rank upper-middle, p90 nearest-rank ceil(0.9 n); `Σ components > τ` sums each run's restricted n_above and `worst run` is the largest of them; the range columns are the observed [min, max] of the run's own per-evaluation counts.
- **the count statistic needs no ruler**: `Σ components > τ` is an integer and says whether anything at all was left unconverged, which the magnitude columns cannot.
- **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, so its two columns stand beside the frozen ruler's rather than replacing them (D30).
- the sweeps and node calls are per **evaluation** and are the same quantity the per-call cost table means; here they are ranges rather than means, to show that the arms' distributions do not overlap.
- *How to read:* compare an arm's minimum with another arm's maximum: where they do not overlap the verdict is not a close call decided by a summary statistic.

**excluded_namespaces** (`excluded_namespaces`, stage `tally_evaluation`; Table D.8; 3 stage table(s) combined).

- *Units:* dimensionless: a scaled coupling-state residual.
- *A row is* one arm of one configuration.
- *A column is* the p90 across that arm's runs of the per-run maximum scaled residual — over the restricted set, or over the components of one excluded namespace.
- *Construction:* stats.namespace_residuals — each run's own audit_residual.json, the components its `excluded_keys` names, on the frozen ruler, reduced to the maximum per namespace; the cell is stats.p90 (nearest-rank ceil(0.9 n)) of those per-run maxima.
- **this is the size of what the headline excludes**: had a namespace been wrongly excluded, the restricted column would read that namespace's number instead of its own.
- the flat control's excluded set is at machine noise or exactly zero, because it runs every node on every sweep; the partitioned arm's is not, because it runs them once after the solve.
- the namespaces are the runs' own excluded keys, not a list typed into this table.
- *How to read:* read the restricted column against the namespace columns beside it on the same row: the gap between them is what the exclusion is worth.

**fixed-point distance** (`fixed_point_distance`, stage `tally_evaluation`; Table D.9; 9 stage table(s) combined).

- *Units:* dimensionless: the largest scaled difference between two arms' exit coupling states at the same entry, in the units τ is stated in.
- *A row is* one pair of arms: each rung of the evaluation phase's ladder (adjacent arms, differing by one named thing) and, marked headline, the partitioned arm against the declared reference (A1 on a pulsed configuration, A0 on a steady-state one); on a pulsed configuration A2/A0 is published beside, the previous revision's pair.
- *A column is* the pairs the two arms share (by seed, or by design-vector column in a stencil source), how many of them were compared and why the rest were not, the restricted distance's median, p90 and worst pair, the components the maximum sat on, the pairs with any restricted component at or above τ, the pairs where a discrete component differs or a constant moved, and the whole-state distance beside.
- *Construction:* stats.fixed_point_distance: the predicate's own scaled residual (harness/child/ystate.py, frozen ruler: max_i |y_arm,i − y_base,i| / s_i) evaluated between the two exit states the runs wrote (y_exit.json), restricted to the components the configuration's once-per-run deferred nodes do not write — the exit audit's own exclusion, re-derived from the artifacts and checked against the digest the audit stamped; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n) over the compared pairs.
- **reported, not accepted on**: no acceptance rule was pre-declared for this quantity; it was added after the campaign by task A76 (fixed-point-distance) from the exit states already on disk, and no model ran to produce it.
- **what it adds to the matched-accuracy table beside it**: that table says how far each arm is from *a* fixed point; this one says how far the two arms' points are from *each other*.  Both are on the frozen ruler; the mixed ruler is not offered here because its denominator reads a current value and a distance between two states has no current side.
- **the exit states are the ones the audit read**: taken at the audit position the caption names, before the audit's own sweep, so a state moved by the instrument cannot enter this table.
- **n counts the pairs the two arms share**, and n_compared the ones on which both exit states exist and both audits carry the restriction; the shortfall is named by reason in the column beside, never dropped (trap T11).
- the whole-state distance is large for the partitioned arm by design — its once-per-run nodes run at the end, so their outputs are stale at exit — and is published to show the exclusion's size, not judged.
- *How to read:* a restricted median far below τ with 0 pairs above τ means the two arms stopped at the same fixed point to within the tolerance they were asked for; a pair above τ names an entry on which they did not, and the worst-pair column says which.

**the ownership rung** (`ownership_rung`, stage `tally_evaluation`; Table D.10; 6 stage table(s) combined).

- *Units:* node-call ratio dimensionless; the burn-time residual in seconds and relative to the burn time.
- *A row is* this configuration's rung.
- *A column is* the cost of taking the burn time out of the flat loop, and the inconsistency the constant leaves behind.
- *Construction:* stats.ratio_triple on node calls of the single evaluation; the residual is constraint 93's own function at exit, |value|, median = nearest-rank upper-middle.
- the residual is 0 by construction in the flat control, which converges the burn time, and is the price of the constant in the pinned arm.
- neither column is a claim about the partition: this rung moves one thing only.
- *How to read:* the ratio is the loop's cost of converging the burn time; the residual is what holding it constant costs in accuracy.

**failure taxonomy** (`failure_taxonomy`, stage `tally_optimisation`; Table D.12; 3 stage table(s) combined).

- *Units:* counts of runs; the detail column is text.
- *A row is* one arm on this configuration.
- *A column is* one disposition of the taxonomy, and the detail: the last line of each unfinished run's traceback, distinct, with its count.
- *Construction:* stats.failure_taxonomy — every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped; stats.crash_detail for the detail.
- the rows sum to the denominator, and the table says so per arm rather than leaving it to be added up.
- an arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.
- a crashed start is counted here and in the failure table, and reaches no cost cell: the cost tables are over the every-arm-converged seed set (plan §3.5).
- *How to read:* a nonzero crashed column is a machinery result that must be explained before any ratio on this configuration is cited; the detail says whether one failure mode or several.

**the seed set** (`seed_set`, stage `tally_optimisation`; Table D.12; 3 stage table(s) combined).

- *Units:* counts of seeds.
- *A row is* this configuration.
- *A column is* the size of the one population every optimisation-phase table on this configuration is over, or a per-arm count of the seeds on which the optimiser was called more than once.
- *Construction:* stats.every_arm_converged — a seed is in the set when every arm present reached an accepted optimum (status ok AND the output file's ifail == 1); stats.retried, which counts attempts[] and never a stored flag.
- **this is one arm group of the source.**  The plan's construction assumes what a campaign guarantees — every arm at every seed — and a gate's runs do not: the source is therefore split by which arms have a run at a seed, and each group is a population the construction applies to.  The group is named in this table's title and in every other table of the same group.
- the seeds outside the set are not dropped: they are the failure table, published beside this one, so an arm that fails on expensive seeds cannot be flattered by the filter.
- a seed on which **no** arm converged is configuration hardness, counted in its own column and not against any arm.
- *How to read:* this n is the denominator of every other optimisation-phase table on this configuration.

**problem_definition** (`problem_definition`, stage `tally_optimisation`; Table D.13; 1 stage table(s) combined).

- *Units:* counts of iteration variables and constraints; the objective is a name.
- *A row is* one configuration.
- *A column is* one part of the optimisation problem that configuration poses.
- *Construction:* the stamps `i_figure_merit`, `nvar`, `n_constraints`, `n_equality_constraints` and `n_inequality_constraints` of every finished run of BR and B0 (the configuration's own problem) and of B1 and B2 beside (the problem after the lift), each refused where its runs disagree; the objective's name and sense are stats.figure_of_merit — the description of the matching member of `FiguresOfMerit` in the **frozen tree's** `process/data_structure/numerics.py`, parsed from the file and never imported, a negative figure of merit meaning *maximise*.
- **the three configurations do not optimise the same thing**, so every cross-configuration comparison in this report is three answers to three questions and never one sample of three.
- on a configuration whose objective **is** the lifted quantity, the ownership rung promotes that objective into the design vector: the arms either side of it are not solving the same optimisation problem (I-20 (b)).
- the counts are the run's own stamps, not the input file read again.
- **the lift changes the problem**, so its `nvar` and constraint counts are columns of their own rather than folded into the configuration's: the unlifted arms state what the configuration poses and the lifted arms what the intervention poses.
- *How to read:* read the objective column against the report's ladder: a rung that touches the objective is a change of problem, not only a change of architecture.

**node calls per module (headline shape 1)** (`node_calls_per_module`, stage `tally_optimisation`; Table D.14; 3 stage table(s) combined).

- *Units:* model-node executions per optimisation run, per node group; ratios dimensionless.
- *A row is* one node group of the configuration (the three modules, the pulse node, the feed-forward tail and the once-per-run deferred nodes, as the committed node map and the per-run artifact place them), then every counted node, then the part of that total outside the solve phase.
- *A column is* per arm, the per-run mean and [min, max] over the seed set; for B2 against B0, the pooled ratio, the per-run median with its [min, max], and the count of runs on which B2 cost more.
- *Construction:* stats.per_node_census (node_census.per_node_counted — the whole run: every attempt, the output path and the exit audit's one sweep) summed over each group of stats.node_groups; means and stats.seed_bracket over the arm's runs in the seed set; the B2/B0 columns are stats.per_seed_ratio_summary over the paired runs (pooled = Σ B2 / Σ B0; median = nearest-rank upper-middle of the per-run ratios; runs B2 > B0 = ratio above 1).  The *outside the solve phase* row is the census total less the solve-phase node calls summed over attempts[] — check 4's unit — so the two tables reconcile by subtraction.
- the census counts the whole run, so a module's calls include its share of the output path (two sweeps in BR and B0, one call per deferred node in B1 and B2) and of the audit's one sweep; the last row states that share and it is not apportioned to the modules.
- the once-per-run group holds the configuration's deferred nodes whatever module the map assigns them: B2 runs them once per run, the flat arms every sweep.
- the arrangement-method (prime) calls are not model nodes and are in no row; check 4's table carries them beside.
- *How to read:* read the B2/B0 column down the modules: a module near 1 is solved about as often as the flat arm sweeps it; the once-per-run row is the deferral's whole saving.

**location_diagnostic** (`location_diagnostic`, stage `tally_optimisation`; Table D.15; 1 stage table(s) combined).

- *Units:* dimensionless: relative differences of the normalised objective and of an iteration variable.
- *A row is* one arm pair of one configuration over its seed set.
- *A column is* an order statistic of the pair's objective difference or of its design-point difference, the variable the point difference sat on most often, or the variables the two sides do not share.
- *Construction:* stats.iteration_variables joins the output file's itvars to its itvar_names **on the solver's slot** and refuses a record with a value in a slot the name map does not carry; stats.point_difference is the maximum over the shared names of |Δx| / max(|x_a|, |x_b|) on the unscaled vector, with the argmax named; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the objective columns are stats.relative_objective_difference, check 1's own.
- **This is a diagnostic. D6 forbids gating on it, and nothing in this report's verdicts rests on it** — some iteration variables are not identified by the problem and differ at an unchanged optimum.
- variables are matched **by name**, never by index: the lift adds `t_plant_pulse_burn`, so a lifted arm carries one more iteration variable than a flat one on a pulsed configuration; the unshared variable is named in its own column and never compared.
- the yardstick pair is a change of **stopping rule** and nothing else; where it moves the point as far as an architectural rung does, non-identification is a property of the configuration and not of the partition.
- the objective columns are check 1's, repeated here so the two questions — how good, and where — are read side by side.
- *How to read:* read the objective columns against the point columns on one row: agreement to thirteen digits on the first with a per-cent difference on the second is a weakly identified direction, not a disagreement about the optimum.

**identity** (`identity`, stage `tally_optimisation`; Table D.16; 1 stage table(s) combined).

- *Units:* counts of seeds.
- *A row is* one configuration.
- *A column is* how many of the configuration's both-accepted pairs agree exactly on one quantity.
- *Construction:* stats.n_evaluations (sweeps_per_eval.n_evaluations) and stats.iterations_summed_over_attempts compared as integers; the objective compared as the **hex float** the record stamps (`exact.norm_objf`), so identity is bit identity and not agreement to a printed precision.
- a pair counts only where both sides reached an accepted optimum; the seeds outside that set are the failure table's.
- integers are compared exactly, so *identical* here is exact and never 'within noise'.
- this is the **partition** at an unchanged trajectory: the two arms differ by the partition alone, both carrying the lift and the prime.
- *How to read:* a count equal to the pair count says the partition changed nothing about the path the optimiser took, only what each step cost.

**iteration multiplier (check 2)** (`iteration_multiplier`, stage `tally_optimisation`; Table D.17; 3 stage table(s) combined).

- *Units:* dimensionless ratios of counts.
- *A row is* one arm against the flat control over the seed set, and the B1 → B2 step beside where both arms are present.
- *A column is* one of check 2's two iteration constructions, its sum ratio, the evaluation-count ratio ε beside them, the seeds on which ε is exactly 1, and the sweep ratio.
- *Construction:* stats.iterations_summed_over_attempts (the **declared acceptance statistic**, nearest-rank upper-middle median against 1.05) and stats.iterations_final_attempt (the previous revision's construction, published beside for comparability).  Both are read from attempts[], so a disagreement between them is a disagreement about that list and not about which field was read.
- the sum ratio is published beside every median because a median of per-seed ratios and the ratio of the sums can point in opposite directions.
- the evaluation-count ratio ε is beside both: iterations, even summed, miss the lifted arm's extra stencil column and the line-search evaluations that vary at equal iteration count.  It reads stats.n_evaluations (sweeps_per_eval.n_evaluations, call_models evaluations summed over the attempts) — issue I-26, closed by task A80 (report-accuracy-audit): until then this column read n_model_calls, the driver's count of sweeps of the dispatch body, under a heading that said evaluations.
- the sweep ratio (n_model_calls, sweeps of the dispatch body over the whole run) is its own column: a block sweep runs one module, not all of them, so it is a mechanism, not a cost, and is never read as ε.
- *ε = 1 on* counts the seeds on which the two arms took exactly the same number of evaluations; on the B1 → B2 row it is the plan's §3.5 pre-declared expectation, per seed.
- *constructions disagree* counts the seeds on which the final attempt's pair and the summed pair are not the same numbers — 0 means no run in this population retried.
- *How to read:* read the acceptance column against the summed median; a final-attempt median that differs from it names the retried seeds, which the attempts column lists.

**cost (check 4)** (`cost`, stage `tally_optimisation`; Table D.18; 3 stage table(s) combined).

- *Units:* model executions during the solve; ratios dimensionless.
- *A row is* one arm over the seed set.
- *A column is* an absolute per-run mean with its bracket, or one reading of the ratio against the flat control.
- *Construction:* stats.with_and_without_retried — solve-phase node calls **summed over attempts[]** per run, so the ratio is over the quantity the attempts decompose (the identity is in the attempt-summation table); pooled = Σ arm / Σ base, median = nearest-rank upper-middle of the per-seed ratios, worse = seeds on which the arm cost more.
- **retries are a term, not a footnote**: the ratio is published *with* and *without* the retried seeds because both readings are defensible — a retry the other arm did not need is real cost the architecture avoided at that start, *and* it is a robustness event rather than a per-evaluation cost.
- a seed counts as retried when **either** side of the pair retried: the pair is what the ratio is over.
- the arrangement-method (prime) calls are two columns of their own — the per-run mean, in the unit of the node-call column beside it, and the sum over the arm's runs in the seed set — and are never pooled into the node calls; on the partitioned arm there is one such call per sweep of the dispatch body.
- the output-time and audit sweeps are excluded from this unit symmetrically in every arm.
- *How to read:* where *retried* is 0 the with- and without- columns are the same number, and the pair of columns is the statement that nothing in this population depended on a retry.

**cost_anchors** (`cost_anchors`, stage `tally_optimisation`; Table D.19; 1 stage table(s) combined).

- *Units:* dimensionless ratios of summed solve-phase node calls.
- *A row is* one configuration under one published seed set.
- *A column is* one of the three anchored ratios.
- *Construction:* the same sums as the cost-sums table, ratioed: BR → B0 is Σ B0 / Σ BR, B2/B0 is Σ B2 / Σ B0 and B2/BR is Σ B2 / Σ BR, each over the set's own seeds.
- **B2/B0 isolates the architecture at a matched stopping rule** and is the ladder's number; **B2/BR is the end-to-end change** a user switching from PROCESS as shipped would see, and conflates the architecture with the stopping-rule change.
- BR → B0 is that stopping-rule change alone, and it is not free: where it exceeds 1 the matched baseline is already cheaper than the code as shipped, so measuring against B0 understates what a user would gain.
- neither ratio is more correct; the report's headline uses B0 because that is the anchor the ladder decomposes against.
- *How to read:* the gap between the last two columns is exactly what the stopping rule is worth on that configuration.

**sweeps_and_prime_calls** (`sweeps_and_prime_calls`, stage `tally_optimisation`; Table D.20; 1 stage table(s) combined).

- *Units:* counts: model-node executions, dispatch sweeps and arrangement-method calls, summed over the seed set; the two rates are dimensionless.
- *A row is* one arm of one configuration over its seed set.
- *A column is* one summed count, or one of the two rates.
- *Construction:* solve-phase node calls summed over attempts[] and then over the set; `n_model_calls` is the **dispatch sweep** count (issue I-26: it counts walks of the dispatch body, not evaluations of the model set) and `n_arrangement_method_calls` the prime calls, each summed over the same runs; the rates are those sums divided.
- **both rates are counts, never costs**: whether a prime call is cheap against an average model node is a timing, and no conclusion in this report rests on one (I-10).
- `prime/sweep` is the prime's contract — one `set_fw_geometry()` per sweep of the dispatch body — and is read as a check, not as a result.
- `prime/node` is the quantity decision D19 excludes from every cost ratio in this report, named here so the exclusion has a size (trap T11).
- a flat arm runs no prime and its rate columns read —.
- *How to read:* node calls fall while sweeps rise: the partitioned arm walks the dispatch body far more often and executes far fewer nodes each time.

**achieved accuracy at the accepted optimum** (`achieved_accuracy`, stage `tally_optimisation`; Table D.21; 3 stage table(s) combined).

- *Units:* dimensionless: the largest scaled coupling-state residual found by one further full sweep past termination.
- *A row is* one arm on one ruler.
- *A column is* the restricted or whole-state audit maximum over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.
- *Construction:* stats.restricted_statistic and stats.whole_state_statistic; median = nearest-rank upper-middle.  The restricted maximum excludes the components the configuration's once-per-run deferred nodes write, derived node → write sets → spec keys.
- **the audit position is a column**: `entry_to_write_output_files` is the declared position — the state the solve handed over — and `after_run` is the reproduction gate's, where the previous revision measured.  The two are different quantities and share this table only because the position is a column of its own.
- **the audit instrument's version is read from the record** (stats.audit_instrument).  Task A61 (insstrain-diagnosis) showed that the largest residual at the accepted point on the pulsed configurations is an artefact of this instrument — the output path permanently changes a model setting the snapshot does not restore, so the audit's sweep is not the loop's map — and task A62 (exit-audit-restore) widens the snapshot under decision D25, which moves every value in these columns.  The argmax is read from the record and is not written into this table.
- **both rulers or neither**: the mixed ruler reads lower wherever its denominator binds, by construction.
- the two rulers' exclusion counts are listed per row and never pooled; a run whose restricted block is null carries no count and reads —.
- **n counts runs, not values** (stats.accuracy_population, the same construction the evaluation phase's table uses): a run whose audit carries no restricted block is counted in n and shows in the column beside it, rather than vanishing from the denominator of a median, which is trap T11; the caption says whether every run of the population carried it.
- *How to read:* read the argmax beside the maximum: a residual above the tolerance whose argmax is the component A61 named is a statement about the audit instrument, not about the arm.

**the lift closed (check 3)** (`lift_closed`, stage `tally_optimisation`; Table D.22; 2 stage table(s) combined).

- *Units:* seconds for the residual; the relative column is dimensionless (residual / burn time).
- *A row is* one arm whose runs name the burn-time consistency constraint.
- *A column is* the residual of that constraint at the accepted optima.
- *Construction:* the model's own extracted burn-time consistency relation, evaluated on the returned state — never read back from an output table; |value|, median = nearest-rank upper-middle.
- an arm whose input file does not name the constraint is absent from this table rather than reading 0.
- residuals at unconverged exits are not here: they belong beside the failure table and are never pooled with these.
- *How to read:* an optimiser that owns the burn time must still satisfy the relation the model used to assign it, or it has returned a point that is not on the same manifold.

**module_sweeps_functions** (`module_sweeps_functions`, stage `tally_evaluation`; Table D.23; 3 stage table(s) combined).

*Applies to `module sweeps per run, function-weighted total — large_tokamak_nof — campaign_displaced`.*

- *Units:* `functions` is a count of functions — the dependency analysis's submodels, one callable of a model each, a model with no submodel counting as one (its entry method) — behind the group's collapsed-DSM rows; the total row is Σ sweeps × functions, a count of function executions; the ratio is dimensionless.
- *A row is* one node group of this configuration, carrying its function count and nothing else (its sweep cells are the module sweeps table's own and are republished beside it, never recomputed), then the function-weighted total over those rows.
- *A column is* the group's function count, or — on the total row alone — one arm's mean Σ sweeps × functions per evaluation over its finished runs, or the pooled ratio of A2 to the declared reference arm over the runs both sides finished.
- *Construction:* stats.functions_by_group — the functions behind each group's rows from the committed harness/data/dsm_function_counts.json, under the two attributions of the once-per-run nodes' own functions; stats.weighted_total (Σ sweeps × functions) with stats.module_sweeps for the sweeps, the same census counts the module sweeps table is built from.
- the function counts are per configuration, read from the committed harness/data/dsm_function_counts.json and nothing else — a file generated once (its generated_by field and the data provenance record name the generator) from the dependency analysis's per-configuration exports at pin PROCESS_at_36ac820e; they differ per block where the exports do (the TF-coil model selected by i_tf_turn_type; the electron-cyclotron model st_regression alone runs), and the module-level counts this block reads are M1 178, M2 90, M3 73, PULSE 3, FF 51.
- the total's ratio cell is the `[v = 1, v = 0]` interval over the two attributions of the once-per-run nodes' own functions — v = 1 taking each node's functions out of the module the map assigns it, v = 0 leaving them there — the same unknown the DSM-row total brackets (trap T9); the per-arm total cells are the v = 1 case.
- no per-module ratio reads the weight: a ratio of sweeps is unit-free, and the weight moves the aggregate alone.
- reported, not accepted on: the acceptance quantities are node calls (the cost-per-call table); this table shows how the aggregate moves with the weight.
- the reference arm is A1 (pulsed: the declared reference, because it and the partitioned arm sit on the same reduced map).
- *How to read:* read the total row's ratio against the module sweeps table's and the per-call cost table's for the same configuration: three weightings of one set of sweep counts.

*Applies to `module sweeps per run, function-weighted total — low_aspect_ratio_DEMO — campaign_displaced`.*

- *Units:* `functions` is a count of functions — the dependency analysis's submodels, one callable of a model each, a model with no submodel counting as one (its entry method) — behind the group's collapsed-DSM rows; the total row is Σ sweeps × functions, a count of function executions; the ratio is dimensionless.
- *A row is* one node group of this configuration, carrying its function count and nothing else (its sweep cells are the module sweeps table's own and are republished beside it, never recomputed), then the function-weighted total over those rows.
- *A column is* the group's function count, or — on the total row alone — one arm's mean Σ sweeps × functions per evaluation over its finished runs, or the pooled ratio of A2 to the declared reference arm over the runs both sides finished.
- *Construction:* stats.functions_by_group — the functions behind each group's rows from the committed harness/data/dsm_function_counts.json, under the two attributions of the once-per-run nodes' own functions; stats.weighted_total (Σ sweeps × functions) with stats.module_sweeps for the sweeps, the same census counts the module sweeps table is built from.
- the function counts are per configuration, read from the committed harness/data/dsm_function_counts.json and nothing else — a file generated once (its generated_by field and the data provenance record name the generator) from the dependency analysis's per-configuration exports at pin PROCESS_at_36ac820e; they differ per block where the exports do (the TF-coil model selected by i_tf_turn_type; the electron-cyclotron model st_regression alone runs), and the module-level counts this block reads are M1 177, M2 90, M3 73, PULSE 3, FF 62.
- the total's ratio cell is the `[v = 1, v = 0]` interval over the two attributions of the once-per-run nodes' own functions — v = 1 taking each node's functions out of the module the map assigns it, v = 0 leaving them there — the same unknown the DSM-row total brackets (trap T9); the per-arm total cells are the v = 1 case.
- no per-module ratio reads the weight: a ratio of sweeps is unit-free, and the weight moves the aggregate alone.
- reported, not accepted on: the acceptance quantities are node calls (the cost-per-call table); this table shows how the aggregate moves with the weight.
- the reference arm is A1 (pulsed: the declared reference, because it and the partitioned arm sit on the same reduced map).
- *How to read:* read the total row's ratio against the module sweeps table's and the per-call cost table's for the same configuration: three weightings of one set of sweep counts.

*Applies to `module sweeps per run, function-weighted total — st_regression — campaign_displaced`.*

- *Units:* `functions` is a count of functions — the dependency analysis's submodels, one callable of a model each, a model with no submodel counting as one (its entry method) — behind the group's collapsed-DSM rows; the total row is Σ sweeps × functions, a count of function executions; the ratio is dimensionless.
- *A row is* one node group of this configuration, carrying its function count and nothing else (its sweep cells are the module sweeps table's own and are republished beside it, never recomputed), then the function-weighted total over those rows.
- *A column is* the group's function count, or — on the total row alone — one arm's mean Σ sweeps × functions per evaluation over its finished runs, or the pooled ratio of A2 to the declared reference arm over the runs both sides finished.
- *Construction:* stats.functions_by_group — the functions behind each group's rows from the committed harness/data/dsm_function_counts.json, under the two attributions of the once-per-run nodes' own functions; stats.weighted_total (Σ sweeps × functions) with stats.module_sweeps for the sweeps, the same census counts the module sweeps table is built from.
- the function counts are per configuration, read from the committed harness/data/dsm_function_counts.json and nothing else — a file generated once (its generated_by field and the data provenance record name the generator) from the dependency analysis's per-configuration exports at pin PROCESS_at_36ac820e; they differ per block where the exports do (the TF-coil model selected by i_tf_turn_type; the electron-cyclotron model st_regression alone runs), and the module-level counts this block reads are M1 178, M2 79, M3 77, PULSE 1, FF 55.
- the total's ratio cell is the `[v = 1, v = 0]` interval over the two attributions of the once-per-run nodes' own functions — v = 1 taking each node's functions out of the module the map assigns it, v = 0 leaving them there — the same unknown the DSM-row total brackets (trap T9); the per-arm total cells are the v = 1 case.
- no per-module ratio reads the weight: a ratio of sweeps is unit-free, and the weight moves the aggregate alone.
- reported, not accepted on: the acceptance quantities are node calls (the cost-per-call table); this table shows how the aggregate moves with the weight.
- the reference arm is A0 (steady state: there is no burn-time coupling, the pinned flat control degenerates onto the plain one and is skipped).
- *How to read:* read the total row's ratio against the module sweeps table's and the per-call cost table's for the same configuration: three weightings of one set of sweep counts.

**module_sweeps_functions** (`module_sweeps_functions`, stage `tally_optimisation`; Table D.24; 3 stage table(s) combined).

*Applies to `module sweeps per run, function-weighted total — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`.*

- *Units:* `functions` is a count of functions — the dependency analysis's submodels, one callable of a model each, a model with no submodel counting as one (its entry method) — behind the group's collapsed-DSM rows; the total row is Σ sweeps × functions over the whole run, a count of function executions; ratios are dimensionless.
- *A row is* one node group of this configuration, carrying its function count and nothing else (its sweep cells are the module sweeps table's own and are republished beside it, never recomputed), then the function-weighted total over those rows.
- *A column is* the group's function count, or — on the total row alone — one arm's mean Σ sweeps × functions per run over the seed set, or one of the three readings of B2 against B0 on that total: pooled as the [v = 1, v = 0] interval, the per-run median with its bracket, and the count of runs on which B2's weighted total was the larger.
- *Construction:* stats.functions_by_group — the functions behind each group's rows from the committed harness/data/dsm_function_counts.json, under the two attributions of the once-per-run nodes' own functions; stats.weighted_total (Σ sweeps × functions) with stats.module_sweeps for the sweeps (node_census.per_node_counted, the whole run); stats.per_seed_ratio_summary for the three readings of the ratio.
- the function counts are per configuration, read from the committed harness/data/dsm_function_counts.json and nothing else — a file generated once (its generated_by field and the data provenance record name the generator) from the dependency analysis's per-configuration exports at pin PROCESS_at_36ac820e; they differ per block where the exports do, and the module-level counts this block reads are M1 178, M2 90, M3 73, PULSE 3, FF 51.
- the total's pooled ratio is the `[v = 1, v = 0]` interval over the two attributions of the once-per-run nodes' own functions (trap T9); the per-arm total cells and the per-run distribution are the v = 1 case.
- whole-run census counts: the output pass adds one sweep to every row in every arm and cancels from every ratio here.
- no per-module ratio reads the weight: a ratio of sweeps is unit-free, and the weight moves the aggregate alone.
- reported, not accepted on: the acceptance quantity is check 4's solve-phase cost table; this table shows how the aggregate moves with the weight.
- *How to read:* read the total row's pooled ratio against the module sweeps table's and check 4's for the same configuration: three weightings of one set of sweep counts.

*Applies to `module sweeps per run, function-weighted total — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`.*

- *Units:* `functions` is a count of functions — the dependency analysis's submodels, one callable of a model each, a model with no submodel counting as one (its entry method) — behind the group's collapsed-DSM rows; the total row is Σ sweeps × functions over the whole run, a count of function executions; ratios are dimensionless.
- *A row is* one node group of this configuration, carrying its function count and nothing else (its sweep cells are the module sweeps table's own and are republished beside it, never recomputed), then the function-weighted total over those rows.
- *A column is* the group's function count, or — on the total row alone — one arm's mean Σ sweeps × functions per run over the seed set, or one of the three readings of B2 against B0 on that total: pooled as the [v = 1, v = 0] interval, the per-run median with its bracket, and the count of runs on which B2's weighted total was the larger.
- *Construction:* stats.functions_by_group — the functions behind each group's rows from the committed harness/data/dsm_function_counts.json, under the two attributions of the once-per-run nodes' own functions; stats.weighted_total (Σ sweeps × functions) with stats.module_sweeps for the sweeps (node_census.per_node_counted, the whole run); stats.per_seed_ratio_summary for the three readings of the ratio.
- the function counts are per configuration, read from the committed harness/data/dsm_function_counts.json and nothing else — a file generated once (its generated_by field and the data provenance record name the generator) from the dependency analysis's per-configuration exports at pin PROCESS_at_36ac820e; they differ per block where the exports do, and the module-level counts this block reads are M1 177, M2 90, M3 73, PULSE 3, FF 62.
- the total's pooled ratio is the `[v = 1, v = 0]` interval over the two attributions of the once-per-run nodes' own functions (trap T9); the per-arm total cells and the per-run distribution are the v = 1 case.
- whole-run census counts: the output pass adds one sweep to every row in every arm and cancels from every ratio here.
- no per-module ratio reads the weight: a ratio of sweeps is unit-free, and the weight moves the aggregate alone.
- reported, not accepted on: the acceptance quantity is check 4's solve-phase cost table; this table shows how the aggregate moves with the weight.
- *How to read:* read the total row's pooled ratio against the module sweeps table's and check 4's for the same configuration: three weightings of one set of sweep counts.

*Applies to `module sweeps per run, function-weighted total — st_regression — campaign_optimisation · BR·B0·B2`.*

- *Units:* `functions` is a count of functions — the dependency analysis's submodels, one callable of a model each, a model with no submodel counting as one (its entry method) — behind the group's collapsed-DSM rows; the total row is Σ sweeps × functions over the whole run, a count of function executions; ratios are dimensionless.
- *A row is* one node group of this configuration, carrying its function count and nothing else (its sweep cells are the module sweeps table's own and are republished beside it, never recomputed), then the function-weighted total over those rows.
- *A column is* the group's function count, or — on the total row alone — one arm's mean Σ sweeps × functions per run over the seed set, or one of the three readings of B2 against B0 on that total: pooled as the [v = 1, v = 0] interval, the per-run median with its bracket, and the count of runs on which B2's weighted total was the larger.
- *Construction:* stats.functions_by_group — the functions behind each group's rows from the committed harness/data/dsm_function_counts.json, under the two attributions of the once-per-run nodes' own functions; stats.weighted_total (Σ sweeps × functions) with stats.module_sweeps for the sweeps (node_census.per_node_counted, the whole run); stats.per_seed_ratio_summary for the three readings of the ratio.
- the function counts are per configuration, read from the committed harness/data/dsm_function_counts.json and nothing else — a file generated once (its generated_by field and the data provenance record name the generator) from the dependency analysis's per-configuration exports at pin PROCESS_at_36ac820e; they differ per block where the exports do, and the module-level counts this block reads are M1 178, M2 79, M3 77, PULSE 1, FF 55.
- the total's pooled ratio is the `[v = 1, v = 0]` interval over the two attributions of the once-per-run nodes' own functions (trap T9); the per-arm total cells and the per-run distribution are the v = 1 case.
- whole-run census counts: the output pass adds one sweep to every row in every arm and cancels from every ratio here.
- no per-module ratio reads the weight: a ratio of sweeps is unit-free, and the weight moves the aggregate alone.
- reported, not accepted on: the acceptance quantity is check 4's solve-phase cost table; this table shows how the aggregate moves with the weight.
- *How to read:* read the total row's pooled ratio against the module sweeps table's and check 4's for the same configuration: three weightings of one set of sweep counts.

**per-sweep overhead** (`per_sweep_overhead`, stage `tally_evaluation`; Table F.4; 12 stage table(s) combined).

- *Units:* counts: evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.
- *A row is* one run of one arm.
- *A column is* a counter of one **named** convergence test, or the sweep total the run's dispatch body walked.
- *Construction:* stats.predicate_widths and stats.empty_visit_shares, read from the driver's own counters — exact and concurrency-invariant, like the node counter.
- **the two predicates are never pooled**: the coupling-state test and upstream's objective/constraint test are not the same test, an arm stops on exactly one of them, and their widths differ by nearly two orders of magnitude.  Their sum is a number belonging to neither and the table module refuses a column carrying one.
- **the empty block visits are counted and disclaimed, never repaired**: a block whose members are skipped at the call site is still visited and still costs a full walk of the model sequence.  The share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — stated per population in the caption.  The *visit* share is a different and larger number and is never quoted: a block visited with no members costs no sweep at all.
- no conclusion rests on a timing: this table answers the per-sweep-overhead question in counts alone.
- *How to read:* read the width column of the test the arm actually stops on; the other test's columns are 0 or blank for that arm, which is the point of keeping them apart.

**the predicate trial** (`predicate_trial`, stage `tally_evaluation`; Table F.5; 1 stage table(s) combined).

- *Units:* counts of predicate evaluations; the audit columns are hex floats of the largest scaled residual.
- *A row is* one pair of runs — the same arm, configuration and seed under each ruler.
- *A column is* a count of the trial, or one run's exit audit read on one named ruler.
- *Construction:* the trial gate's observer, which watches each predicate evaluation of the frozen run and reads it again on the mixed ruler; the record comparison is bit-for-bit with no tolerance.
- **decisive passes are published as two counts** (the two-counts caption rule recorded in the report's Appendix C at A59's merge, 2026-09-11, in what was then its §4.2.5): *crossings* — evaluations at which some component crossed the tolerance between the rulers — and *verdict changes* — evaluations whose verdict changed because the crossing component was the one holding the evaluation open.  Only the second can make two runs differ, and the gate binds on it.
- **the exit audit is on both rulers, never one**: each run is audited on the frozen and the mixed ruler, so a difference between the audit columns of one row is a change of ruler and a difference down a column is a change of run.
- the size of |y|/s on the components that made a pass decisive, or the absence of any such component, is stated per population in the caption.
- *How to read:* a pair with no verdict change must be bit-identical, which is the gate's identity; every difference in this table is attributable to the named components.

**per-arm success by seed** (`per_arm_success_by_seed`, stage `tally_optimisation`; Table F.6; 3 stage table(s) combined).

- *Units:* outcome classes (text) and counts of arms.
- *A row is* one seed offered to every arm of the group.
- *A column is* each arm's outcome class at that seed, how many arms accepted, whether the seed is in the seed set, and which arms lost it while another accepted.
- *Construction:* stats.per_arm_success (per-seed part) — stats.outcome_class per record; in the seed set when every arm accepted (stats.every_arm_converged); lost by an arm when it did not accept and another did.
- the per-seed detail behind the per-arm success table: the report carries the counts, this table the seeds.
- a seed no arm accepted is configuration-invalid and reads 0 arms accepted with no arm losing it.
- *How to read:* read down an arm's column for its failures; read the lost-by column for the asymmetric ones.

**the failure table** (`failure_table`, stage `tally_optimisation`; Table F.7; 3 stage table(s) combined).

- *Units:* counts: model executions for the cost columns, optimiser exit codes for ifail.
- *A row is* one seed outside the converged set.
- *A column is* which arm failed there, how it failed, what it cost, and what the other arms cost at the same start.
- *Construction:* stats.accepted_optimum for membership; the cost column is node_calls_solve_phase, the same unit the cost table uses.
- an arm the gate did not run at a seed reads *not run* rather than *failed*: an absent record and a failed run are different results.
- a seed on which every arm failed or was absent is marked configuration-invalid.
- *How to read:* the converged set is the fairer cost population but can flatter an arm that fails on expensive seeds; this table is what keeps it honest.

**the attempt-summation identity** (`attempt_summation`, stage `tally_optimisation`; Table F.8; 3 stage table(s) combined).

- *Units:* counts: model executions and sweeps of the model sequence.
- *A row is* one optimisation run.
- *A column is* the per-attempt costs, the run's solve-phase total they decompose, and the residual between them.
- *Construction:* stats.attempt_summation — Σ over attempts[] against node_calls_solve_phase and dispatch_sweeps_solve_phase.
- this identity is why the with- and without-retried-seeds cost ratios may be published: they are computed over quantities that visibly decompose the published total, and a residual that is not 0 would make them ratios of something else.
- the record contract already refuses a record whose parts do not add up; this table is the same identity stated as a number a reader can see.
- *How to read:* every residual column reads 0, or the run is refused before it reaches any other table here.

**per-sweep overhead** (`per_sweep_overhead`, stage `tally_optimisation`; Table F.9; 3 stage table(s) combined).

- *Units:* counts: evaluations of a convergence test, components compared summed over them, and sweeps of the model sequence.
- *A row is* one optimisation run.
- *A column is* a counter of one **named** convergence test, or a sweep total.
- *Construction:* stats.predicate_widths and stats.empty_visit_shares, from the driver's own counters — exact and concurrency-invariant.
- **the two predicates are never pooled**: an arm stops on exactly one of them and their widths differ by nearly two orders of magnitude, so their sum belongs to neither.  The table module refuses a column carrying one.
- **the empty block visits are counted and disclaimed, never repaired**, and the share quoted is the **sweep** share — the fraction of the run's dispatch sweeps those visits cost — stated per population in the caption.  The visit share is larger and is never quoted.
- no conclusion rests on a timing: the question is asked in counts alone.
- *How to read:* read the width column of the test the arm actually stops on; the other test's columns are 0 for that arm, which is why they are kept apart.

### D.1 Gates

The gate table is the appendix's licence: every table below is read only if every row here is PASS with its teeth tripped. A **tooth** is a deliberate break the gate must catch, so a gate whose tooth did not trip is not accepted whatever its verdict. The row `recomputation` is the second implementation's summary — every cell of the tally's tables recomputed from the run records by code sharing no construction with the tally, compared without tolerance; its *compared* / *mismatched* pair is the whole of that check, and **is the only place the recomputed tables appear**: the copies themselves are not rendered, in this appendix or in the companion file, because a second grid of the same numbers under the record's own column keys is not something a reader can act on. The row `tally_contracts` covers the captions, denominators and record contract of every table emitted.

**Table D.1.** *Every registered gate from its verdict record: the verdict on the criterion and every tooth, what it compared (the denominator) and how many differed, teeth tripped / declared. No number in this appendix is cited unless every row is PASS with its teeth tripped; the two PASS rows with a nonzero mismatched count are the frozen-physics gate (1: the one approved model file, by name) and the copy-identity gate (8: the recorded permitted driver-edit files, by name and digest). A compared count that sums more than one kind of thing shows its parts in brackets. Population: 30 registered gate(s): 11 of the experiment plan's §3.9 table and 19 of the harness's own checks, promoted.*

| gate | plan | binds | verdict | population | compared | mismatched | teeth | record |
|---|---|---|---|---|---|---|---|---|
| `g0prime` | G0 / G0' | every V4 commit, every arm, both phases | **PASS** | 77 files under PROCESS/process/models/ compared byte for byte against c0ae5b28 (git cat-file, never a working tree), plus the file set | 77 | 1 | 4/4 | `runs/gates/g0prime/gate.json` |
| `copy_identity` | — | every V4 commit that touches the experiment's copy of PROCESS | **PASS** | 224 files under PROCESS/process/ compared byte for byte against the source commit f2dc9243 (git cat-file, never a working tree), plus the file set;… | 224 | 8 | 12/12 | `runs/gates/copy_identity/gate.json` |
| `edit_behaviour` | — | the one permitted edit in the copy that is not a rename or a comment | **PASS** | three arms of one probe, no PROCESS run: the copy with the per-run write-set artifact absent, the source commit f2dc9243 (git archive) with it abse… | 3 | 0 | 1/1 | `runs/gates/edit_behaviour/gate.json` |
| `self_containment` | — | the user's requirement in the harness plan §6: nothing in this package is imported from, o | **PASS** | 52 Python file(s): every module under harness/ and experiment_runner.py beside it; 49 line(s) naming either directory, 14 of them executable | 52 | 0 | 1/1 | `runs/gates/self_containment/gate.json` |
| `composition` | — | the harness itself, before any PROCESS run | **PASS** | 8 arms x 3 configurations = 24 pairs | 42 | 0 | 7/7 | `runs/gates/composition/gate.json` |
| `rungs` | — | the harness itself, before any PROCESS run | **PASS** | 11 matrix rows x 8 arms = 88 cells; 6 rung steps | 98 | 0 | 3/3 | `runs/gates/rungs/gate.json` |
| `provenance` | — | the harness itself, before any PROCESS run | **PASS** | one scratch repository, three states | 4 | 0 | 4/4 | `runs/gates/provenance/gate.json` |
| `data` | — | the harness itself, before any PROCESS run | **PASS** | 16 committed file(s) in harness/data/ + the moved predicate module = 17 comparisons; and 9 declared counts (3 configurations x coupling-state compo… | 17 | 0 | 6/6 | `runs/gates/data/gate.json` |
| `run_path` | — | the harness itself, before any PROCESS run | **PASS** | 2 phases x the declared field list; 2 displacement streams; 5 refusals | 12 | 0 | 12/12 | `runs/gates/run_path/gate.json` |
| `resume_identity` | — | every --resume decision and every directory of the shared run pool | **PASS** | 22 Job field(s); 13 by-design pair(s) (10 must differ, 3 must agree); 3 recorded-name row(s); 1102 record(s) under runs/ read by arm name | 1140 | 0 | 9/9 | `runs/gates/resume_identity/gate.json` |
| `capability` | — | the harness itself, before any PROCESS run | **PASS** | every arm/configuration pair whose arms are active | 55 | 0 | 5/5 | `runs/gates/capability/gate.json` |
| `artifacts_check` | — | every committed artifact of every configuration | **PASS** | 19 artifact row(s) over 3 configuration(s) (large_tokamak_nof, low_aspect_ratio_DEMO, st_regression); 95 individual check(s) | 95 | 0 | 3/3 | `runs/gates/artifacts_check/gate.json` |
| `artifacts_derive_inputs` | — | the lifted input file of each pulsed configuration | **PASS** | 3 configuration(s) (large_tokamak_nof, low_aspect_ratio_DEMO, st_regression); the digest gate applies to the 2 pulsed one(s) | 2 | 0 | 4/4 | `runs/gates/artifacts_derive_inputs/gate.json` |
| `artifacts_census` | — | the committed run-time write census, per configuration | **PASS** | 3 configuration(s) (large_tokamak_nof, low_aspect_ratio_DEMO, st_regression); one optimisation census each, taken with the read half of the instrum… | 81 | 0 | 5/5 | `runs/gates/artifacts_census/gate.json` |
| `artifacts_per_run` | — | each configuration's per-run deferral set | **PASS** | 5 (configuration, input file) pair(s) over 3 configuration(s) (large_tokamak_nof, low_aspect_ratio_DEMO, st_regression); the write census is measur… | 16 | 0 | 2/2 | `runs/gates/artifacts_per_run/gate.json` |
| `record_completeness` | G7 | the declared pairing and the failure forensics, in both phases | **PASS** | 2 runs on st_regression (the configuration with the fewest iteration variables, derived); 90 declared field(s) in the optimisation phase and 83 in … | 173 | 0 | 9/9 | `runs/gates/record_completeness/gate.json` |
| `prime_map` | G2 | the claim that the arrangement's method-level move changes nothing once the first-wall mod | **PASS** | 6 arrangement/configuration pair(s); 12 evaluations; 5026 components compared | 5026 | 0 | 2/2 | `runs/gates/prime_map/gate.json` |
| `cold_chain` | G3 / G3c | the claim that with the method-level move in place no cut edge carries a stale value into  | **PASS** | 8 chain/composition pair(s) over 4 chain(s); 16 evaluations | 60 | 0 | 4/4 | `runs/gates/cold_chain/gate.json` |
| `audit_restriction` | G4 | the similarity statistic, on every configuration | **PASS** | 13 doctored run(s) over 3 configuration(s), each against that configuration's undoctored run; namespaces derived per configuration | 12 | 0 | 6/6 | `runs/gates/audit_restriction/gate.json` |
| `entry_and_warm` | G6 | the evaluation phase, on every configuration | **PASS** | 8 entry pair(s) at seed 1; 5 warm run(s); 16 evaluations | 6717 | 0 | 3/3 | `runs/gates/entry_and_warm/gate.json` |
| `switch_composition` | G5 | B2, on every configuration where it is active | **PASS** | 3 configuration(s) where B2 is active; 6 optimisations; 37 switch names and 10 run values per configuration | 141 | 0 | 4/4 | `runs/gates/switch_composition/gate.json` |
| `switch_neutrality` | G1 | each driver change, run per change and never batched | **PASS** | straddles d6c48c88 -> 3983fb0c: a neutrality result.  6 run pair(s) = 3 configuration(s) x 2 reference arm(s); 3980 deterministic record values and… | 55299 (3980 + 51319) | 0 | 9/9 | `runs/gates/switch_neutrality/gate.json` |
| `reproduction` | GR | the harness rewrite and the experiment's copy of PROCESS, once, at the copy commit before  | **PASS** | 20 runs (14 optimisations + 6 evaluations) over 3 configurations; 270 values in the committed reference, 14 of them excluded by name with their rea… | 256 | 0 | 8/8 | `runs/gates/reproduction/gate.json` |
| `output_path` | G9 | the removal of the output-time loop from the arms whose matrix cell turns it off, on every | **PASS** | 11 run(s) at seed 0 = every optimisation-phase arm on every configuration where it is active, each composed from the experiment's matrix; 3825 coup… | 3879 (3825 + 54) | 0 | 4/4 | `runs/gates/output_path/gate.json` |
| `written_file_gap` | — | the written-file gap on the one-call output path: BR, B1 and B2 at seed 0 on the pulsed co | **PASS** | 6 run(s) at seed 0, unperturbed = 3 arm(s) (BR, B1, B2) x 2 pulsed configuration(s), each composed from the experiment's matrix with no override bu… | 42 | 0 | 4/4 | `runs/gates/written_file_gap/gate.json` |
| `predicate_mode` | G8 | the convergence predicate's second ruler, on the evaluation-phase arms of every configurat | **PASS** | 12 pair(s) = 3 configuration(s) x the evaluation-phase arms active on each (A0, A2) x 2 seed(s), each run under both rulers = 24 runs at delta = 0.… | 8152 (8068 + 84) | 0 | 4/4 | `runs/gates/predicate_mode/gate.json` |
| `tally_contracts` | — | every table the tally emits, and the cells it reproduces | **PASS** | 20 reference run(s) (14 optimisations + 6 evaluations) over 3 configurations; 256 published cells, no tolerance on any of them; and 147 table(s) em… | 697 (441 + 256) | 0 | 18/18 | `runs/gates/tally_contracts/gate.json` |
| `recomputation` | — | every cell the tally publishes, recomputed from the run records by a second implementation | **PASS** | 147 table(s) emitted by the two tally stages, recomputed cell by cell from 949 run record(s) under the 5 published source(s) of the campaign popula… | 18036 | 0 | 9/9 | `runs/gates/recomputation/gate.json` |
| `run_kind_separation` | — | every record this package makes, and every population the tally and the analysis build | **PASS** | 1102 run record(s) under runs/, of which 949 are covered by the tally's 5 published source(s) (the campaign family) and 31 by its 2 unpublished; ru… | 3000 | 0 | 9/9 | `runs/gates/run_kind_separation/gate.json` |
| `stage_provenance` | — | the harness itself, before any PROCESS run | **PASS** | a scratch records directory this check writes itself — 3 verdict record(s) and 4 stage record(s) — broken 4 ways; a scratch census record, stamped … | 17 | 0 | 5/5 | `runs/gates/stage_provenance/gate.json` |

**30 PASS, 0 FAIL, 0 not run; 176 of 176 teeth tripped.**

<sub>`gate table`</sub>

### D.2 The evaluation phase

One `call_models` evaluation per run, no optimiser. Four sources, never pooled: the **entry reference** (one flat `A0` evaluation per configuration from the input file's own point), the **displaced entries** (δ = 0.10, seeds 1–25 — the acceptance regime), and the **forward** and **backward stencil points** (one per design-vector column, paired across arms by column). **One construction, one table**: each table below combines the tally's per-configuration and per-source tables of one construction into one grid, the configurations and regimes as row groups under a bold sub-heading row that names the group's configuration, its regime where a table holds more than one, and its own n; what that n counts is in the caption. Node calls per block is rendered whole here — the acceptance regime (the displaced entries) as one row group among the four regimes of Table D.3 — since the main text carries the per-module result in sweeps, whose ratios are the same cells (the user, 2026-09-17: *"move the per node tables to the appendix"*). Absolute cost cells are per-run means with the seed bracket; a ratio against the reference is read three ways — pooled (Σ arm / Σ reference), per-run median, and the count of runs on which the arm cost more. The reference is `A1` on a pulsed configuration and `A0` on a steady-state one. The accuracy tables are on both rulers and carry the audit position as a column; their whole-state columns are large for `A2` by design and are not judged. Denominators are runs of the configuration in the source (25 per arm in the displaced regime; one per design-vector column per arm in a stencil source), and every sub-heading row states its own. The per-run overhead tables and the predicate trial are in the companion file.

**Table D.2.** *What the partition **is** on each configuration: each node group's collapsed-DSM row count and whether the committed map places it inside the iterated loop, then how many of its model nodes execute on each configuration and which. Static — derived from the committed node map and each configuration's per-run artifact, with no cell read from a run's statistics. The once-per-run group is the configuration's deferred nodes whatever module the map assigns them, which is why it carries no row count of its own (trap T9). n = 3 (configurations whose grouping this table states).*

| DSM module | what | DSM rows | iterated | large_tokamak_nof: executing | large_tokamak_nof: nodes | low_aspect_ratio_DEMO: executing | low_aspect_ratio_DEMO: nodes | st_regression: executing | st_regression: nodes |
|---|---|---|---|---|---|---|---|---|---|
| M1 | Physics | 24 | yes | 2 | physics; plasma_geom | 2 | physics; plasma_geom | 2 | physics; plasma_geom |
| M2 | Coils | 10 | yes | 3 | build; cicc_sctfcoil; pfcoil | 3 | build; cicc_sctfcoil; pfcoil | 3 | build; croco_sctfcoil; pfcoil |
| M3 | Plant | 12 | yes | 12 | availability; buildings; ccfe_hcpb; cryostat; divertor; fw; power; power.acpow; power.plant_electric_production; shield; structure; vacuum_vessel | 12 | availability; buildings; ccfe_hcpb; cryostat; divertor; fw; power; power.acpow; power.plant_electric_production; shield; structure; vacuum_vessel | 12 | availability; buildings; ccfe_hcpb; cryostat; divertor; fw; power; power.acpow; power.plant_electric_production; shield; structure; vacuum_vessel |
| PULSE | Pulse -- the articulation point, belonging to no module | 1 | yes | 1 | pulse | 1 | pulse | 0 | — |
| once per run | once per run | — | — | 3 | costs; vacuum; water_use | 3 | costs; vacuum; water_use | 4 | costs; pulse; vacuum; water_use |

<sub>`module scope`</sub>

<sub>combining 1 stage table(s): `module scope`</sub>

**Table D.3.** *Mean node calls per evaluation by block and arm, configurations stacked, in all four evaluation-phase regimes as row groups: the entry reference, the **displaced entries** (δ = 0.10, the acceptance regime), and the forward and backward stencil points. The ratio is `A2` pooled against the configuration's declared reference (the *reference* column: `A1` on a pulsed configuration, `A0` on `st_regression`); the configuration is named once per group and blank on its continuation rows. The once-per-run row is the deferred nodes; prime calls are not model nodes and are in no row. The entry reference carries one `A0` run per configuration and so no pair and no ratio. The displaced regime's per-block ratios are the per-module ratios of the main text's module sweeps table, cell for cell, and its TOTAL row's ratio is the per-call cost table's partitioning rung. n = 4 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and source regime and its own n, and that n counts finished evaluation-phase campaign runs of every configuration in this source).*

| configuration | block | nodes | which | AR | A0 | A1 | A2 | reference | A2 / reference (pooled) | pairs |
|---|---|---|---|---|---|---|---|---|---|---|
| **campaign_entry_references (n = 3)** |  |  |  |  |  |  |  |  |  |  |
| large_tokamak_nof | M1 | 2 | physics, plasma_geom | — | 12.0 | — | — | A0 | — | 0 |
|  | M2 | 3 | build, cicc_sctfcoil, pfcoil | — | 18.0 | — | — | A0 | — | 0 |
|  | M3 | 12 | Plant: 12 nodes (the committed node map's members) | — | 72.0 | — | — | A0 | — | 0 |
|  | PULSE | 1 | pulse | — | 6.0 | — | — | A0 | — | 0 |
|  | once per run | 3 | costs, vacuum, water_use | — | 18.0 | — | — | A0 | — | 0 |
|  | TOTAL | 21 | all counted nodes | — | 126.0 | — | — | A0 | — | 0 |
| low_aspect_ratio_DEMO | M1 | 2 | physics, plasma_geom | — | 10.0 | — | — | A0 | — | 0 |
|  | M2 | 3 | build, cicc_sctfcoil, pfcoil | — | 15.0 | — | — | A0 | — | 0 |
|  | M3 | 12 | Plant: 12 nodes (the committed node map's members) | — | 60.0 | — | — | A0 | — | 0 |
|  | PULSE | 1 | pulse | — | 5.0 | — | — | A0 | — | 0 |
|  | once per run | 3 | costs, vacuum, water_use | — | 15.0 | — | — | A0 | — | 0 |
|  | TOTAL | 21 | all counted nodes | — | 105.0 | — | — | A0 | — | 0 |
| st_regression | M1 | 2 | physics, plasma_geom | — | 14.0 | — | — | A0 | — | 0 |
|  | M2 | 3 | build, croco_sctfcoil, pfcoil | — | 21.0 | — | — | A0 | — | 0 |
|  | M3 | 12 | Plant: 12 nodes (the committed node map's members) | — | 84.0 | — | — | A0 | — | 0 |
|  | once per run | 4 | costs, pulse, vacuum, water_use | — | 28.0 | — | — | A0 | — | 0 |
|  | TOTAL | 21 | all counted nodes | — | 147.0 | — | — | A0 | — | 0 |
| **campaign_displaced (n = 275)** |  |  |  |  |  |  |  |  |  |  |
| large_tokamak_nof | M1 | 2 | physics, plasma_geom | 9.9 | 11.0 | 10.2 | 8.0 | A1 | **0.7812** | 25 |
|  | M2 | 3 | build, cicc_sctfcoil, pfcoil | 14.9 | 16.6 | 15.4 | 15.5 | A1 | **1.0078** | 25 |
|  | M3 | 12 | Plant: 12 nodes (the committed node map's members) | 59.5 | 66.2 | 61.4 | 36.0 | A1 | **0.5859** | 25 |
|  | PULSE | 1 | pulse | 5.0 | 5.5 | 5.1 | 1.0 | A1 | **0.1953** | 25 |
|  | once per run | 3 | costs, vacuum, water_use | 14.9 | 16.6 | 15.4 | 0.0 | A1 | **0.0000** | 25 |
|  | TOTAL | 21 | all counted nodes | 104.2 | 115.9 | 107.5 | 60.5 | A1 | **0.5625** | 25 |
| low_aspect_ratio_DEMO | M1 | 2 | physics, plasma_geom | 10.0 | 10.0 | 9.8 | 8.0 | A1 | **0.8130** | 25 |
|  | M2 | 3 | build, cicc_sctfcoil, pfcoil | 15.0 | 15.0 | 14.8 | 14.6 | A1 | **0.9919** | 25 |
|  | M3 | 12 | Plant: 12 nodes (the committed node map's members) | 60.0 | 60.0 | 59.0 | 36.0 | A1 | **0.6098** | 25 |
|  | PULSE | 1 | pulse | 5.0 | 5.0 | 4.9 | 1.0 | A1 | **0.2033** | 25 |
|  | once per run | 3 | costs, vacuum, water_use | 15.0 | 15.0 | 14.8 | 0.0 | A1 | **0.0000** | 25 |
|  | TOTAL | 21 | all counted nodes | 105.0 | 105.0 | 103.3 | 59.6 | A1 | **0.5772** | 25 |
| st_regression | M1 | 2 | physics, plasma_geom | 9.8 | 11.7 | — | 8.0 | A0 | **0.6849** | 25 |
|  | M2 | 3 | build, croco_sctfcoil, pfcoil | 14.8 | 17.5 | — | 17.5 | A0 | **1.0000** | 25 |
|  | M3 | 12 | Plant: 12 nodes (the committed node map's members) | 59.0 | 70.1 | — | 36.0 | A0 | **0.5137** | 25 |
|  | once per run | 4 | costs, pulse, vacuum, water_use | 19.7 | 23.4 | — | 0.0 | A0 | **0.0000** | 25 |
|  | TOTAL | 21 | all counted nodes | 103.3 | 122.6 | — | 61.5 | A0 | **0.5016** | 25 |
| **campaign_stencil_forward (n = 198)** |  |  |  |  |  |  |  |  |  |  |
| large_tokamak_nof | M1 | 2 | physics, plasma_geom | 5.9 | 6.3 | 6.0 | 3.8 | A1 | **0.6333** | 20 |
|  | M2 | 3 | build, cicc_sctfcoil, pfcoil | 8.8 | 9.4 | 9.0 | 7.3 | A1 | **0.8167** | 20 |
|  | M3 | 12 | Plant: 12 nodes (the committed node map's members) | 35.4 | 37.8 | 36.0 | 27.0 | A1 | **0.7500** | 20 |
|  | PULSE | 1 | pulse | 3.0 | 3.1 | 3.0 | 1.0 | A1 | **0.3333** | 20 |
|  | once per run | 3 | costs, vacuum, water_use | 8.8 | 9.4 | 9.0 | 0.0 | A1 | **0.0000** | 20 |
|  | TOTAL | 21 | all counted nodes | 62.0 | 66.2 | 63.0 | 39.1 | A1 | **0.6214** | 20 |
| low_aspect_ratio_DEMO | M1 | 2 | physics, plasma_geom | 6.4 | 6.3 | 6.0 | 3.8 | A1 | **0.6316** | 19 |
|  | M2 | 3 | build, cicc_sctfcoil, pfcoil | 9.6 | 9.5 | 9.0 | 7.1 | A1 | **0.7895** | 19 |
|  | M3 | 12 | Plant: 12 nodes (the committed node map's members) | 38.5 | 37.9 | 36.0 | 28.4 | A1 | **0.7895** | 19 |
|  | PULSE | 1 | pulse | 3.2 | 3.2 | 3.0 | 1.0 | A1 | **0.3333** | 19 |
|  | once per run | 3 | costs, vacuum, water_use | 9.6 | 9.5 | 9.0 | 0.0 | A1 | **0.0000** | 19 |
|  | TOTAL | 21 | all counted nodes | 67.4 | 66.3 | 63.0 | 40.3 | A1 | **0.6399** | 19 |
| st_regression | M1 | 2 | physics, plasma_geom | 6.0 | 6.4 | — | 4.4 | A0 | **0.6889** | 14 |
|  | M2 | 3 | build, croco_sctfcoil, pfcoil | 9.0 | 9.6 | — | 6.2 | A0 | **0.6444** | 14 |
|  | M3 | 12 | Plant: 12 nodes (the committed node map's members) | 36.0 | 38.6 | — | 28.3 | A0 | **0.7333** | 14 |
|  | once per run | 4 | costs, pulse, vacuum, water_use | 12.0 | 12.9 | — | 0.0 | A0 | **0.0000** | 14 |
|  | TOTAL | 21 | all counted nodes | 63.0 | 67.5 | — | 38.9 | A0 | **0.5767** | 14 |
| **campaign_stencil_backward (n = 198)** |  |  |  |  |  |  |  |  |  |  |
| large_tokamak_nof | M1 | 2 | physics, plasma_geom | 5.8 | 6.3 | 6.0 | 3.8 | A1 | **0.6333** | 20 |
|  | M2 | 3 | build, cicc_sctfcoil, pfcoil | 8.7 | 9.4 | 9.0 | 7.3 | A1 | **0.8167** | 20 |
|  | M3 | 12 | Plant: 12 nodes (the committed node map's members) | 34.8 | 37.8 | 36.0 | 28.2 | A1 | **0.7833** | 20 |
|  | PULSE | 1 | pulse | 2.9 | 3.1 | 3.0 | 1.0 | A1 | **0.3333** | 20 |
|  | once per run | 3 | costs, vacuum, water_use | 8.7 | 9.4 | 9.0 | 0.0 | A1 | **0.0000** | 20 |
|  | TOTAL | 21 | all counted nodes | 60.9 | 66.2 | 63.0 | 40.4 | A1 | **0.6405** | 20 |
| low_aspect_ratio_DEMO | M1 | 2 | physics, plasma_geom | 6.4 | 6.5 | 6.1 | 3.8 | A1 | **0.6207** | 19 |
|  | M2 | 3 | build, cicc_sctfcoil, pfcoil | 9.6 | 9.8 | 9.2 | 7.3 | A1 | **0.7931** | 19 |
|  | M3 | 12 | Plant: 12 nodes (the committed node map's members) | 38.5 | 39.2 | 36.6 | 30.3 | A1 | **0.8276** | 19 |
|  | PULSE | 1 | pulse | 3.2 | 3.3 | 3.1 | 1.0 | A1 | **0.3276** | 19 |
|  | once per run | 3 | costs, vacuum, water_use | 9.6 | 9.8 | 9.2 | 0.0 | A1 | **0.0000** | 19 |
|  | TOTAL | 21 | all counted nodes | 67.4 | 68.5 | 64.1 | 42.4 | A1 | **0.6609** | 19 |
| st_regression | M1 | 2 | physics, plasma_geom | 6.3 | 6.7 | — | 4.4 | A0 | **0.6596** | 14 |
|  | M2 | 3 | build, croco_sctfcoil, pfcoil | 9.4 | 10.1 | — | 6.6 | A0 | **0.6596** | 14 |
|  | M3 | 12 | Plant: 12 nodes (the committed node map's members) | 37.7 | 40.3 | — | 28.3 | A0 | **0.7021** | 14 |
|  | once per run | 4 | costs, pulse, vacuum, water_use | 12.6 | 13.4 | — | 0.0 | A0 | **0.0000** | 14 |
|  | TOTAL | 21 | all counted nodes | 66.0 | 70.5 | — | 39.4 | A0 | **0.5583** | 14 |

<sub>`node calls per block`</sub>

<sub>combining 4 stage table(s): `node calls per block — campaign_entry_references`; `node calls per block — campaign_displaced`; `node calls per block — campaign_stencil_forward`; `node calls per block — campaign_stencil_backward`</sub>

**Table D.4.** *The entry reference, one row per configuration and ruler: what one flat `A0` evaluation from the input file's own design point cost, what it left at exit on both rulers, and whether it finished. This is the once-per-run cold-start term of plan §3.4, reported beside the displaced and stencil regimes and never pooled with them; it carries one run per configuration, so there is no pair, no ratio and no bracket. The cost and outcome cells are per configuration and repeat down its two ruler rows. n = 9 (row group(s) of this table, each over its own population with its own n in its sub-heading row; never pooled). Per-seed column(s) *paired with A0 at seeds*: companion Table F.10.*

| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | vs A0 pooled | vs A0 median | worse | ruler | n (runs) | with a restricted statistic | restricted median | restricted p90 | restricted argmax | whole-state median | whole-state p90 | components excluded | audit position | audit instrument (snapshot positions taken) | scheduled | ok | rows sum | detail (traceback's last line × count) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **large_tokamak_nof — 3 construction(s): `cost per call` n = 1; `matched accuracy` n = 1; `failure taxonomy` n = 1** |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| A0 | 1/1 | 126.0 | [126, 126] | 6.00 | FLAT 6 | 0.0 | — | — | — | frozen | 1 | 1 | 8.092e-09 | 8.092e-09 | power.qac | 1.465e-08 | 1.465e-08 | 122 | after_single_evaluation | no snapshot recorded on this record | 1 | 1 | yes | — |
| A0 | 1/1 | 126.0 | [126, 126] | 6.00 | FLAT 6 | 0.0 | — | — | — | mixed | 1 | 1 | 4.529e-09 | 4.529e-09 | power.qac | 4.529e-09 | 4.529e-09 | 122 | after_single_evaluation | no snapshot recorded on this record | 1 | 1 | yes | — |
| **low_aspect_ratio_DEMO — 3 construction(s): `cost per call` n = 1; `matched accuracy` n = 1; `failure taxonomy` n = 1** |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| A0 | 1/1 | 105.0 | [105, 105] | 5.00 | FLAT 5 | 0.0 | — | — | — | frozen | 1 | 1 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record | 1 | 1 | yes | — |
| A0 | 1/1 | 105.0 | [105, 105] | 5.00 | FLAT 5 | 0.0 | — | — | — | mixed | 1 | 1 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record | 1 | 1 | yes | — |
| **st_regression — 3 construction(s): `cost per call` n = 1; `matched accuracy` n = 1; `failure taxonomy` n = 1** |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| A0 | 1/1 | 147.0 | [147, 147] | 7.00 | FLAT 7 | 0.0 | — | — | — | frozen | 1 | 1 | 3.276e-09 | 3.276e-09 | superconducting_tfcoil.a_tf_plasma_case | 3.276e-09 | 3.276e-09 | 123 | after_single_evaluation | no snapshot recorded on this record | 1 | 1 | yes | — |
| A0 | 1/1 | 147.0 | [147, 147] | 7.00 | FLAT 7 | 0.0 | — | — | — | mixed | 1 | 1 | 2.286e-09 | 2.286e-09 | superconducting_tfcoil.a_tf_plasma_case | 2.286e-09 | 2.286e-09 | 123 | after_single_evaluation | no snapshot recorded on this record | 1 | 1 | yes | — |

<sub>`the reference entries`</sub>

<sub>combining 9 stage table(s): `cost per call — large_tokamak_nof — campaign_entry_references`; `matched accuracy — large_tokamak_nof — campaign_entry_references`; `failure taxonomy — large_tokamak_nof — campaign_entry_references`; `cost per call — low_aspect_ratio_DEMO — campaign_entry_references`; `matched accuracy — low_aspect_ratio_DEMO — campaign_entry_references`; `failure taxonomy — low_aspect_ratio_DEMO — campaign_entry_references`; `cost per call — st_regression — campaign_entry_references`; `matched accuracy — st_regression — campaign_entry_references`; `failure taxonomy — st_regression — campaign_entry_references`</sub>

**Table D.5.** *Node calls per `call_models` evaluation by arm, configuration and regime, with the ratio against the declared reference read three ways: pooled, as the per-run median, and as the count of runs on which the arm cost more. The reference is `A1` on a pulsed configuration and `A0` on `st_regression`; each sub-heading row names its regime and its own n. Prime (arrangement-method) calls stand beside the node calls and are never in them. n = 9 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and source regime and its own n, and that n counts evaluation-phase campaign runs of that configuration). Per-seed column(s) *paired with the reference at*: companion Table F.11.*

| arm | ok/run | node calls per evaluation [min, max] | sweeps / eval | sweeps by block | arrangement·method calls | vs reference pooled | vs reference median | worse |
|---|---|---|---|---|---|---|---|---|
| **large_tokamak_nof · campaign_displaced (n = 100)** |  |  |  |  |  |  |  |  |
| AR | 25/25 | 104.2 [84, 105] | 4.96 | — | 0.0 | **0.9688** | 1.0000 | 0 |
| A0 | 25/25 | 115.9 [105, 126] | 5.52 | FLAT 138 | 0.0 | **1.0781** | 1.0000 | 10 |
| A1 | 25/25 | 107.5 [84, 126] | 5.12 | FLAT 128 | 0.0 | — | — | — |
| A2 | 25/25 | 60.5 [60, 63] | 13.16 | FF 0, M1 100, M2 129, M3 75, PULSE 0 | 13.2 | **0.5625** | 0.5714 | 0 |
| **low_aspect_ratio_DEMO · campaign_displaced (n = 100)** |  |  |  |  |  |  |  |  |
| AR | 25/25 | 105 | 5.00 | — | 0.0 | **1.0163** | 1.0000 | 2 |
| A0 | 25/25 | 105 | 5.00 | FLAT 125 | 0.0 | **1.0163** | 1.0000 | 2 |
| A1 | 25/25 | 103.3 [84, 105] | 4.92 | FLAT 123 | 0.0 | — | — | — |
| A2 | 25/25 | 59.6 [57, 60] | 12.88 | FF 0, M1 100, M2 122, M3 75, PULSE 0 | 12.9 | **0.5772** | 0.5714 | 0 |
| **st_regression · campaign_displaced (n = 75)** |  |  |  |  |  |  |  |  |
| AR | 25/25 | 103.3 [84, 105] | 4.92 | — | 0.0 | **0.8425** | 0.8333 | 0 |
| A0 | 25/25 | 122.6 [105, 126] | 5.84 | FLAT 146 | 0.0 | — | — | — |
| A2 | 25/25 | 61.5 [59, 62] | 14.84 | FF 0, M1 100, M2 146, M3 75, PULSE 25 | 14.8 | **0.5016** | 0.4921 | 0 |
| **large_tokamak_nof · campaign_stencil_forward (n = 80)** |  |  |  |  |  |  |  |  |
| AR | 20/20 | 62.0 [42, 84] | 2.95 | — | 0.0 | **0.9833** | 1.0000 | 0 |
| A0 | 20/20 | 66.2 [42, 105] | 3.15 | FLAT 63 | 0.0 | **1.0500** | 1.0000 | 3 |
| A1 | 20/20 | 63.0 [42, 105] | 3.00 | FLAT 60 | 0.0 | — | — | — |
| A2 | 20/20 | 39.1 [20, 55] | 7.60 | FF 0, M1 38, M2 49, M3 45, PULSE 0 | 7.6 | **0.6214** | 0.6071 | 0 |
| **low_aspect_ratio_DEMO · campaign_stencil_forward (n = 76)** |  |  |  |  |  |  |  |  |
| AR | 19/19 | 67.4 [42, 105] | 3.21 | — | 0.0 | **1.0702** | 1.0000 | 4 |
| A0 | 19/19 | 66.3 [42, 105] | 3.16 | FLAT 60 | 0.0 | **1.0526** | 1.0000 | 3 |
| A1 | 19/19 | 63.0 [42, 84] | 3.00 | FLAT 57 | 0.0 | — | — | — |
| A2 | 19/19 | 40.3 [33, 55] | 7.63 | FF 0, M1 36, M2 45, M3 45, PULSE 0 | 7.6 | **0.6399** | 0.6071 | 0 |
| **st_regression · campaign_stencil_forward (n = 42)** |  |  |  |  |  |  |  |  |
| AR | 14/14 | 63.0 [42, 84] | 3.00 | — | 0.0 | **0.9333** | 1.0000 | 0 |
| A0 | 14/14 | 67.5 [42, 84] | 3.21 | FLAT 45 | 0.0 | — | — | — |
| A2 | 14/14 | 38.9 [19, 50] | 8.64 | FF 0, M1 31, M2 29, M3 33, PULSE 14 | 8.6 | **0.5767** | 0.5714 | 0 |
| **large_tokamak_nof · campaign_stencil_backward (n = 80)** |  |  |  |  |  |  |  |  |
| AR | 20/20 | 60.9 [42, 84] | 2.90 | — | 0.0 | **0.9667** | 1.0000 | 0 |
| A0 | 20/20 | 66.2 [42, 105] | 3.15 | FLAT 63 | 0.0 | **1.0500** | 1.0000 | 3 |
| A1 | 20/20 | 63.0 [42, 105] | 3.00 | FLAT 60 | 0.0 | — | — | — |
| A2 | 20/20 | 40.4 [20, 55] | 7.70 | FF 0, M1 38, M2 49, M3 47, PULSE 0 | 7.7 | **0.6405** | 0.6071 | 0 |
| **low_aspect_ratio_DEMO · campaign_stencil_backward (n = 76)** |  |  |  |  |  |  |  |  |
| AR | 19/19 | 67.4 [42, 105] | 3.21 | — | 0.0 | **1.0517** | 1.0000 | 4 |
| A0 | 19/19 | 68.5 [42, 105] | 3.26 | FLAT 62 | 0.0 | **1.0690** | 1.0000 | 4 |
| A1 | 19/19 | 64.1 [42, 84] | 3.05 | FLAT 58 | 0.0 | — | — | — |
| A2 | 19/19 | 42.4 [33, 55] | 7.84 | FF 0, M1 36, M2 46, M3 48, PULSE 0 | 7.8 | **0.6609** | 0.7143 | 0 |
| **st_regression · campaign_stencil_backward (n = 42)** |  |  |  |  |  |  |  |  |
| AR | 14/14 | 66.0 [42, 84] | 3.14 | — | 0.0 | **0.9362** | 1.0000 | 0 |
| A0 | 14/14 | 70.5 [42, 105] | 3.36 | FLAT 47 | 0.0 | — | — | — |
| A2 | 14/14 | 39.4 [19, 53] | 8.79 | FF 0, M1 31, M2 31, M3 33, PULSE 14 | 8.8 | **0.5583** | 0.5238 | 0 |

<sub>`cost per call`</sub>

<sub>combining 9 stage table(s): `cost per call — large_tokamak_nof — campaign_displaced`; `cost per call — low_aspect_ratio_DEMO — campaign_displaced`; `cost per call — st_regression — campaign_displaced`; `cost per call — large_tokamak_nof — campaign_stencil_forward`; `cost per call — low_aspect_ratio_DEMO — campaign_stencil_forward`; `cost per call — st_regression — campaign_stencil_forward`; `cost per call — large_tokamak_nof — campaign_stencil_backward`; `cost per call — low_aspect_ratio_DEMO — campaign_stencil_backward`; `cost per call — st_regression — campaign_stencil_backward`</sub>

**Table D.6.** *Exit accuracy by arm, configuration and regime on both rulers: the restricted maximum scaled residual (median, p90), its argmax component, and the whole-state maximum beside it. The whole-state columns are large for `A2` by design — they hold the components the once-per-run deferred nodes write, stale at the audit — and are published so the exclusion can be seen, not judged. The audit position is a column of its own. n = 9 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and source regime and its own n, and that n counts evaluation-phase campaign runs of that configuration).*

| arm | ruler | n (runs) | with a restricted statistic | restricted median / p90 | restricted argmax | whole-state median / p90 | components excluded | audit position | audit instrument (snapshot positions taken) |
|---|---|---|---|---|---|---|---|---|---|
| **large_tokamak_nof · campaign_displaced (n = 100)** |  |  |  |  |  |  |  |  |  |
| AR | frozen | 25 | 25 | 2.624e-08 / 1.542e-07 | blanket.deg_blkt_inboard_poloidal_plasma, heat_transport.tlvpmw, power.qac | 3.255e-08 / 4.142e-07 | 122 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 25 | 25 | 1.501e-08 / 8.372e-08 | blanket.deg_blkt_inboard_poloidal_plasma, heat_transport.tlvpmw, power.qac | 1.501e-08 / 8.372e-08 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 25 | 25 | 5.042e-10 / 2.963e-09 | blanket.deg_blkt_inboard_poloidal_plasma, power.qac | 6.254e-10 / 7.959e-09 | 122 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 25 | 25 | 2.883e-10 / 1.609e-09 | blanket.deg_blkt_inboard_poloidal_plasma, power.qac | 2.883e-10 / 1.609e-09 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 25 | 25 | 3.833e-10 / 1.671e-08 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.stress_z_cs_self_midplane_profile | 3.833e-10 / 1.671e-08 | 122 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 25 | 25 | 3.833e-10 / 1.671e-08 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.stress_z_cs_self_midplane_profile | 3.833e-10 / 1.671e-08 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A2 | frozen | 25 | 25 | 3.833e-10 / 1.671e-08 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.stress_z_cs_self_midplane_profile | 2.435e+00 / 9.860e+00 | 122 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 25 | 25 | 3.833e-10 / 1.671e-08 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.stress_z_cs_self_midplane_profile | 3.977e-01 / 6.170e-01 | 122 | after_single_evaluation | no snapshot recorded on this record |
| **low_aspect_ratio_DEMO · campaign_displaced (n = 100)** |  |  |  |  |  |  |  |  |  |
| AR | frozen | 25 | 25 | 0 / 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 / 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 25 | 25 | 0 / 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 / 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 25 | 25 | 0 / 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 / 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 25 | 25 | 0 / 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 / 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 25 | 25 | 0 / 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 / 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 25 | 25 | 0 / 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 / 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A2 | frozen | 25 | 25 | 0 / 0 | blanket.deg_blkt_inboard_poloidal_plasma | 1.816e-01 / 2.878e-01 | 123 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 25 | 25 | 0 / 0 | blanket.deg_blkt_inboard_poloidal_plasma | 1.687e-01 / 2.420e-01 | 123 | after_single_evaluation | no snapshot recorded on this record |
| **st_regression · campaign_displaced (n = 75)** |  |  |  |  |  |  |  |  |  |
| AR | frozen | 25 | 25 | 1.539e-07 / 2.793e-07 | superconducting_tfcoil.a_tf_plasma_case | 1.539e-07 / 2.793e-07 | 123 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 25 | 25 | 1.074e-07 / 1.949e-07 | superconducting_tfcoil.a_tf_plasma_case | 1.074e-07 / 1.949e-07 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 25 | 25 | 5.372e-09 / 2.023e-08 | superconducting_tfcoil.a_tf_plasma_case | 5.372e-09 / 2.023e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 25 | 25 | 3.749e-09 / 1.412e-08 | superconducting_tfcoil.a_tf_plasma_case | 3.749e-09 / 1.412e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A2 | frozen | 25 | 25 | 5.372e-09 / 2.023e-08 | superconducting_tfcoil.a_tf_plasma_case | 2.575e-01 / 3.374e-01 | 123 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 25 | 25 | 3.749e-09 / 1.412e-08 | superconducting_tfcoil.a_tf_plasma_case | 1.343e-01 / 1.810e-01 | 123 | after_single_evaluation | no snapshot recorded on this record |
| **large_tokamak_nof · campaign_stencil_forward (n = 80)** |  |  |  |  |  |  |  |  |  |
| AR | frozen | 20 | 20 | 2.974e-12 / 1.869e-08 | power.qac | 5.344e-12 / 3.385e-08 | 122 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 20 | 20 | 1.664e-12 / 1.046e-08 | power.qac | 1.664e-12 / 1.046e-08 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 20 | 20 | 2.974e-12 / 3.592e-10 | power.qac | 5.344e-12 / 6.504e-10 | 122 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 20 | 20 | 1.664e-12 / 2.010e-10 | power.qac | 1.664e-12 / 2.010e-10 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 20 | 20 | 4.523e-13 / 2.783e-09 | pf_coil.f_j_cs_start_end_flat_top, pf_coil.stress_z_cs_self_midplane_profile | 4.523e-13 / 2.783e-09 | 122 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 20 | 20 | 4.523e-13 / 2.783e-09 | pf_coil.f_j_cs_start_end_flat_top, pf_coil.stress_z_cs_self_midplane_profile | 4.523e-13 / 2.783e-09 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A2 | frozen | 20 | 20 | 2.363e-11 / 2.783e-09 | pf_coil.f_j_cs_start_end_flat_top, pf_coil.stress_z_cs_self_midplane_profile | 2.016e-03 / 7.115e-02 | 122 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 20 | 20 | 2.363e-11 / 2.783e-09 | pf_coil.f_j_cs_start_end_flat_top, pf_coil.stress_z_cs_self_midplane_profile | 1.827e-03 / 1.078e-02 | 122 | after_single_evaluation | no snapshot recorded on this record |
| **low_aspect_ratio_DEMO · campaign_stencil_forward (n = 76)** |  |  |  |  |  |  |  |  |  |
| AR | frozen | 19 | 19 | 0 / 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 / 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 19 | 19 | 0 / 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 / 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 19 | 19 | 0 / 0 | blanket.deg_blkt_inboard_poloidal_plasma, heat_transport.tlvpmw | 0 / 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 19 | 19 | 0 / 0 | blanket.deg_blkt_inboard_poloidal_plasma, heat_transport.tlvpmw | 0 / 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 19 | 19 | 0 / 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 / 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 19 | 19 | 0 / 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 / 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A2 | frozen | 19 | 19 | 0 / 0 | blanket.deg_blkt_inboard_poloidal_plasma | 1.504e-03 / 7.584e-03 | 123 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 19 | 19 | 0 / 0 | blanket.deg_blkt_inboard_poloidal_plasma | 1.471e-03 / 7.584e-03 | 123 | after_single_evaluation | no snapshot recorded on this record |
| **st_regression · campaign_stencil_forward (n = 42)** |  |  |  |  |  |  |  |  |  |
| AR | frozen | 14 | 14 | 3.779e-11 / 3.920e-07 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 3.779e-11 / 3.920e-07 | 123 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 14 | 14 | 1.434e-11 / 2.735e-07 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 1.434e-11 / 2.735e-07 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 14 | 14 | 3.779e-11 / 2.137e-08 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 3.779e-11 / 2.137e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 14 | 14 | 1.434e-11 / 1.491e-08 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 1.434e-11 / 1.491e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A2 | frozen | 14 | 14 | 1.116e-10 / 2.137e-08 | fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 1.761e-03 / 5.969e-03 | 123 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 14 | 14 | 7.789e-11 / 1.491e-08 | fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 1.021e-03 / 2.569e-03 | 123 | after_single_evaluation | no snapshot recorded on this record |
| **large_tokamak_nof · campaign_stencil_backward (n = 80)** |  |  |  |  |  |  |  |  |  |
| AR | frozen | 20 | 20 | 5.339e-15 / 1.730e-10 | blanket.deg_blkt_inboard_poloidal_plasma, heat_transport.tlvpmw, power.qac | 5.339e-15 / 1.730e-10 | 122 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 20 | 20 | 2.988e-15 / 1.730e-10 | blanket.deg_blkt_inboard_poloidal_plasma, heat_transport.tlvpmw, power.qac | 2.988e-15 / 1.730e-10 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 20 | 20 | 0 / 5.339e-15 | blanket.deg_blkt_inboard_poloidal_plasma, power.qac | 0 / 1.144e-14 | 122 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 20 | 20 | 0 / 2.988e-15 | blanket.deg_blkt_inboard_poloidal_plasma, power.qac | 0 / 2.988e-15 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 20 | 20 | 0 / 8.309e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top, pf_coil.stress_z_cs_self_midplane_profile | 0 / 8.309e-16 | 122 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 20 | 20 | 0 / 8.309e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.bpf2, pf_coil.stress_z_cs_self_midplane_profile | 0 / 8.309e-16 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A2 | frozen | 20 | 20 | 8.309e-16 / 4.523e-13 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top, pf_coil.stress_z_cs_self_midplane_profile | 2.016e-03 / 6.975e-02 | 122 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 20 | 20 | 8.309e-16 / 4.523e-13 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.bpf2, pf_coil.stress_z_cs_self_midplane_profile | 1.826e-03 / 1.079e-02 | 122 | after_single_evaluation | no snapshot recorded on this record |
| **low_aspect_ratio_DEMO · campaign_stencil_backward (n = 76)** |  |  |  |  |  |  |  |  |  |
| AR | frozen | 19 | 19 | 0 / 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 / 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 19 | 19 | 0 / 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 / 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 19 | 19 | 0 / 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 / 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 19 | 19 | 0 / 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 / 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 19 | 19 | 0 / 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 / 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 19 | 19 | 0 / 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 / 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A2 | frozen | 19 | 19 | 0 / 0 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.stress_z_cs_self_midplane_profile | 1.509e-03 / 8.370e-03 | 123 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 19 | 19 | 0 / 0 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.stress_z_cs_self_midplane_profile | 1.468e-03 / 8.370e-03 | 123 | after_single_evaluation | no snapshot recorded on this record |
| **st_regression · campaign_stencil_backward (n = 42)** |  |  |  |  |  |  |  |  |  |
| AR | frozen | 14 | 14 | 6.459e-14 / 4.272e-08 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 6.459e-14 / 4.272e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 14 | 14 | 6.459e-14 / 2.983e-08 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 6.459e-14 / 2.983e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 14 | 14 | 0 / 2.670e-08 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.radius_beam_tangency_max, superconducting_tfcoil.a_tf_plasma_case | 0 / 2.670e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 14 | 14 | 0 / 1.864e-08 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.radius_beam_tangency_max, superconducting_tfcoil.a_tf_plasma_case | 0 / 1.864e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A2 | frozen | 14 | 14 | 1.560e-11 / 2.670e-08 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 1.760e-03 / 5.988e-03 | 123 | after_single_evaluation | no snapshot recorded on this record |
|  | mixed | 14 | 14 | 5.919e-12 / 1.864e-08 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 1.022e-03 / 2.579e-03 | 123 | after_single_evaluation | no snapshot recorded on this record |

<sub>`matched accuracy`</sub>

<sub>combining 9 stage table(s): `matched accuracy — large_tokamak_nof — campaign_displaced`; `matched accuracy — low_aspect_ratio_DEMO — campaign_displaced`; `matched accuracy — st_regression — campaign_displaced`; `matched accuracy — large_tokamak_nof — campaign_stencil_forward`; `matched accuracy — low_aspect_ratio_DEMO — campaign_stencil_forward`; `matched accuracy — st_regression — campaign_stencil_forward`; `matched accuracy — large_tokamak_nof — campaign_stencil_backward`; `matched accuracy — low_aspect_ratio_DEMO — campaign_stencil_backward`; `matched accuracy — st_regression — campaign_stencil_backward`</sub>

**Table D.7.** *The full restricted-audit distributions by configuration, arm and regime: minimum, median and maximum on the frozen ruler, the components left above τ = 1e-6 summed over the arm's runs and in its worst single run, the mixed ruler's median and p90 beside, and the per-evaluation sweeps and node calls as observed ranges. The count column needs no ruler and says whether anything at all was left unconverged; compare an arm's minimum with another's maximum to see whether the two populations overlap at all. n = 3 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and source regime and its own n, and that n counts finished evaluation-phase campaign runs over every configuration in this source).*

| configuration | arm | n (runs) | min | median | max | Σ components > τ | worst run | mixed median | mixed p90 | sweeps | node calls |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **campaign_displaced (n = 275)** |  |  |  |  |  |  |  |  |  |  |  |
| large_tokamak_nof | AR | 25 | 0 | 2.624e-08 | 2.265e-07 | 0 | 0 | 1.501e-08 | 8.372e-08 | 4–5 | 84–105 |
|  | A0 | 25 | 0 | 5.042e-10 | 4.352e-09 | 0 | 0 | 2.883e-10 | 1.609e-09 | 5–6 | 105–126 |
|  | A1 | 25 | 0 | 3.833e-10 | 1.870e-08 | 0 | 0 | 3.833e-10 | 1.671e-08 | 4–6 | 84–126 |
|  | A2 | 25 | 0 | 3.833e-10 | 1.870e-08 | 0 | 0 | 3.833e-10 | 1.671e-08 | 13–14 | 60–63 |
| low_aspect_ratio_DEMO | AR | 25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 5 | 105 |
|  | A0 | 25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 5 | 105 |
|  | A1 | 25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4–5 | 84–105 |
|  | A2 | 25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 12–13 | 57–60 |
| st_regression | AR | 25 | 2.755e-08 | 1.539e-07 | 5.938e-07 | 0 | 0 | 1.074e-07 | 1.949e-07 | 4–5 | 84–105 |
|  | A0 | 25 | 1.632e-09 | 5.372e-09 | 2.875e-08 | 0 | 0 | 3.749e-09 | 1.412e-08 | 5–6 | 105–126 |
|  | A2 | 25 | 1.632e-09 | 5.372e-09 | 2.875e-08 | 0 | 0 | 3.749e-09 | 1.412e-08 | 14–15 | 59–62 |
| **campaign_stencil_forward (n = 198)** |  |  |  |  |  |  |  |  |  |  |  |
| large_tokamak_nof | AR | 20 | 1.686e-15 | 2.974e-12 | 7.190e-08 | 0 | 0 | 1.664e-12 | 1.046e-08 | 2–4 | 42–84 |
|  | A0 | 20 | 1.686e-15 | 2.974e-12 | 1.381e-09 | 0 | 0 | 1.664e-12 | 2.010e-10 | 2–5 | 42–105 |
|  | A1 | 20 | 2.608e-16 | 4.523e-13 | 2.840e-09 | 0 | 0 | 4.523e-13 | 2.783e-09 | 2–5 | 42–105 |
|  | A2 | 20 | 2.608e-16 | 2.363e-11 | 2.840e-09 | 0 | 0 | 2.363e-11 | 2.783e-09 | 5–11 | 20–55 |
| low_aspect_ratio_DEMO | AR | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2–5 | 42–105 |
|  | A0 | 19 | 0 | 0 | 1.976e-11 | 0 | 0 | 0 | 0 | 2–5 | 42–105 |
|  | A1 | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2–4 | 42–84 |
|  | A2 | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6–11 | 33–55 |
| st_regression | AR | 14 | 6.459e-14 | 3.779e-11 | 4.704e-07 | 0 | 0 | 1.434e-11 | 2.735e-07 | 2–4 | 42–84 |
|  | A0 | 14 | 6.459e-14 | 3.779e-11 | 3.206e-08 | 0 | 0 | 1.434e-11 | 1.491e-08 | 2–4 | 42–84 |
|  | A2 | 14 | 1.560e-11 | 1.116e-10 | 3.206e-08 | 0 | 0 | 7.789e-11 | 1.491e-08 | 6–10 | 19–50 |
| **campaign_stencil_backward (n = 198)** |  |  |  |  |  |  |  |  |  |  |  |
| large_tokamak_nof | AR | 20 | 0 | 5.339e-15 | 2.645e-06 | 2 | 2 | 2.988e-15 | 1.730e-10 | 2–4 | 42–84 |
|  | A0 | 20 | 0 | 0 | 5.339e-15 | 0 | 0 | 0 | 2.988e-15 | 2–5 | 42–105 |
|  | A1 | 20 | 0 | 0 | 1.156e-15 | 0 | 0 | 0 | 8.309e-16 | 2–5 | 42–105 |
|  | A2 | 20 | 0 | 8.309e-16 | 4.523e-13 | 0 | 0 | 8.309e-16 | 4.523e-13 | 5–11 | 20–55 |
| low_aspect_ratio_DEMO | AR | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2–5 | 42–105 |
|  | A0 | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2–5 | 42–105 |
|  | A1 | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2–4 | 42–84 |
|  | A2 | 19 | 0 | 0 | 6.864e-19 | 0 | 0 | 0 | 0 | 6–11 | 33–55 |
| st_regression | AR | 14 | 0 | 6.459e-14 | 6.407e-08 | 0 | 0 | 6.459e-14 | 2.983e-08 | 2–4 | 42–84 |
|  | A0 | 14 | 0 | 0 | 3.204e-08 | 0 | 0 | 0 | 1.864e-08 | 2–5 | 42–105 |
|  | A2 | 14 | 6.459e-14 | 1.560e-11 | 3.204e-08 | 0 | 0 | 5.919e-12 | 1.864e-08 | 6–11 | 19–53 |

<sub>`full distributions`</sub>

<sub>combining 3 stage table(s): `full distributions — campaign_displaced`; `full distributions — campaign_stencil_forward`; `full distributions — campaign_stencil_backward`</sub>

**Table D.8.** ***What the exclusion set is load-bearing for**: the p90 across runs of the per-run maximum scaled residual, for the restricted set and for each namespace the restriction removes, by configuration, arm and regime, from every run's own residual vector. Had a namespace been wrongly excluded, the restricted column would read that namespace's number instead of its own — which is the size of what the headline rests on. n = 3 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and source regime and its own n, and that n counts finished evaluation-phase campaign runs over every configuration in this source, arms A0, A2).*

| configuration | arm | n (runs) | restricted (headline) | `costs` | `fwbs` | `physics` | `vacuum` | `water_use` |
|---|---|---|---|---|---|---|---|---|
| **campaign_displaced (n = 150)** |  |  |  |  |  |  |  |  |
| large_tokamak_nof | A0 | 25 | **2.963e-09** | 7.959e-09 | 0 | 0 | 1.151e-12 | 2.861e-16 |
|  | A2 | 25 | **1.671e-08** | 9.860e+00 | 1.349e-01 | 5.270e-02 | 6.787e-02 | 9.859e-02 |
| low_aspect_ratio_DEMO | A0 | 25 | **0** | 0 | 0 | 0 | 0 | 0 |
|  | A2 | 25 | **0** | 2.878e-01 | 8.439e-02 | 8.508e-02 | 9.657e-02 | 1.289e-01 |
| st_regression | A0 | 25 | **2.023e-08** | 1.583e-09 | 0 | 0 | 8.914e-11 | 1.360e-11 |
|  | A2 | 25 | **2.023e-08** | 3.336e-01 | 3.668e-02 | 1.972e-01 | 9.125e-02 | 3.188e-01 |
| **campaign_stencil_forward (n = 106)** |  |  |  |  |  |  |  |  |
| large_tokamak_nof | A0 | 20 | **3.592e-10** | 6.504e-10 | 0 | 0 | 1.409e-13 | 0 |
|  | A2 | 20 | **2.783e-09** | 7.115e-02 | 2.750e-03 | 1.133e-03 | 8.100e-04 | 1.030e-03 |
| low_aspect_ratio_DEMO | A0 | 19 | **0** | 0 | 0 | 0 | 0 | 0 |
|  | A2 | 19 | **0** | 7.584e-03 | 2.795e-03 | 2.979e-03 | 1.559e-03 | 2.804e-03 |
| st_regression | A0 | 14 | **2.137e-08** | 1.672e-09 | 0 | 0 | 9.413e-11 | 1.354e-11 |
|  | A2 | 14 | **2.137e-08** | 5.969e-03 | 5.894e-04 | 3.341e-03 | 7.229e-05 | 3.132e-03 |
| **campaign_stencil_backward (n = 106)** |  |  |  |  |  |  |  |  |
| large_tokamak_nof | A0 | 20 | **5.339e-15** | 1.144e-14 | 0 | 0 | 0 | 0 |
|  | A2 | 20 | **4.523e-13** | 6.975e-02 | 2.761e-03 | 1.133e-03 | 8.104e-04 | 1.030e-03 |
| low_aspect_ratio_DEMO | A0 | 19 | **0** | 0 | 0 | 0 | 0 | 0 |
|  | A2 | 19 | **0** | 8.370e-03 | 2.807e-03 | 2.975e-03 | 1.559e-03 | 2.800e-03 |
| st_regression | A0 | 14 | **2.670e-08** | 2.089e-09 | 0 | 0 | 1.177e-10 | 1.467e-11 |
|  | A2 | 14 | **2.670e-08** | 5.988e-03 | 5.881e-04 | 3.343e-03 | 7.229e-05 | 3.134e-03 |

<sub>`the excluded namespaces`</sub>

<sub>combining 3 stage table(s): `excluded namespaces — campaign_displaced`; `excluded namespaces — campaign_stencil_forward`; `excluded namespaces — campaign_stencil_backward`</sub>

**Table D.9.** *The distance between two arms' exit states on the restricted component set, by configuration, regime and pair: median, p90, worst, the worst pair's key, the argmax component, and the counts of pairs holding a component at or above τ = 1e-6 or categorically unclean. Reported, never accepted on: the acceptance quantity is the matched-accuracy table's residual. n = 9 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and source regime and its own n, and that n counts evaluation-phase pairs of that configuration over the ladder's rungs).*

| pair | role | n (shared) | compared | not compared (reason: count) | restricted median / p90 | restricted worst | worst | restricted argmax | pairs with a component ≥ τ | pairs categorically unclean | whole-state median / p90 | components excluded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **large_tokamak_nof · campaign_displaced (n = 100)** |  |  |  |  |  |  |  |  |  |  |  |  |
| A0/AR | rung | 25 | 25 | — | 2.624e-08 / 1.542e-07 | 2.265e-07 | 20 | blanket.deg_blkt_inboard_poloidal_plasma; heat_transport.tlvpmw; power.qac | 0 | 0 | 3.255e-08 / 4.142e-07 | 122 |
| A1/A0 | rung | 25 | 25 | — | 9.665e-02 / 1.985e-01 | 2.563e-01 | 15 | power.qac | 25 | 0 | 2.919e-01 / 8.333e-01 | 122 |
| A2/A1 | headline | 25 | 25 | — | 5.094e-12 / 1.838e-10 | 2.709e-10 | 15 | blanket.deg_blkt_inboard_poloidal_plasma; heat_transport.tlvpmw; pf_coil.stress_z_cs_self_midplane_profile | 0 | 0 | 2.435e+00 / 9.860e+00 | 122 |
| A2/A0 | beside | 25 | 25 | — | 9.665e-02 / 1.985e-01 | 2.563e-01 | 15 | power.qac | 25 | 0 | 2.818e+00 / 1.029e+01 | 122 |
| **low_aspect_ratio_DEMO · campaign_displaced (n = 100)** |  |  |  |  |  |  |  |  |  |  |  |  |
| A0/AR | rung | 25 | 25 | — | 0 / 0 | 0 | — | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 0 / 0 | 123 |
| A1/A0 | rung | 25 | 25 | — | 7.026e-02 / 1.585e-01 | 2.047e-01 | 15 | power.e_plant_net_electric_pulse_kwh; power.e_plant_net_electric_pulse_mj; times.t_burn_0 | 25 | 0 | 7.026e-02 / 1.585e-01 | 123 |
| A2/A1 | headline | 25 | 25 | — | 0 / 0 | 0 | — | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 1.816e-01 / 2.878e-01 | 123 |
| A2/A0 | beside | 25 | 25 | — | 7.026e-02 / 1.585e-01 | 2.047e-01 | 15 | power.e_plant_net_electric_pulse_kwh; power.e_plant_net_electric_pulse_mj; times.t_burn_0 | 25 | 0 | 1.839e-01 / 2.864e-01 | 123 |
| **st_regression · campaign_displaced (n = 50)** |  |  |  |  |  |  |  |  |  |  |  |  |
| A0/AR | rung | 25 | 25 | — | 1.539e-07 / 2.793e-07 | 5.938e-07 | 21 | blanket.deg_blkt_inboard_poloidal_plasma; superconducting_tfcoil.a_tf_plasma_case | 0 | 0 | 1.539e-07 / 2.793e-07 | 123 |
| A2/A0 | headline | 25 | 25 | — | 1.227e-11 / 4.620e-11 | 6.565e-11 | 22 | heat_transport.tlvpmw | 0 | 0 | 2.575e-01 / 3.374e-01 | 123 |
| **large_tokamak_nof · campaign_stencil_forward (n = 80)** |  |  |  |  |  |  |  |  |  |  |  |  |
| A0/AR | rung | 20 | 20 | — | 0 / 1.869e-08 | 7.190e-08 | 8 | blanket.deg_blkt_inboard_poloidal_plasma; power.qac | 0 | 0 | 0 / 3.385e-08 | 122 |
| A1/A0 | rung | 20 | 20 | — | 7.108e-04 / 5.313e-03 | 7.937e-03 | 8 | power.qac | 14 | 0 | 1.727e-03 / 1.291e-02 | 122 |
| A2/A1 | headline | 20 | 20 | — | 2.579e-12 / 3.409e-11 | 3.462e-11 | 12 | blanket.deg_blkt_inboard_poloidal_plasma; heat_transport.tlvpmw; pf_coil.stress_z_cs_self_midplane_profile | 0 | 0 | 2.016e-03 / 7.115e-02 | 122 |
| A2/A0 | beside | 20 | 20 | — | 7.108e-04 / 5.313e-03 | 7.937e-03 | 8 | power.qac | 14 | 0 | 9.974e-03 / 8.381e-02 | 122 |
| **low_aspect_ratio_DEMO · campaign_stencil_forward (n = 76)** |  |  |  |  |  |  |  |  |  |  |  |  |
| A0/AR | rung | 19 | 19 | — | 0 / 0 | 1.976e-11 | 13 | blanket.deg_blkt_inboard_poloidal_plasma; heat_transport.tlvpmw | 0 | 0 | 0 / 0 | 123 |
| A1/A0 | rung | 19 | 19 | — | 5.536e-04 / 3.810e-03 | 4.508e-03 | 8 | blanket.deg_blkt_inboard_poloidal_plasma; power.e_plant_net_electric_pulse_kwh; power.e_plant_net_electric_pulse_mj | 14 | 0 | 5.536e-04 / 3.810e-03 | 123 |
| A2/A1 | headline | 19 | 19 | — | 0 / 0 | 0 | — | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 1.504e-03 / 7.584e-03 | 123 |
| A2/A0 | beside | 19 | 19 | — | 5.536e-04 / 3.810e-03 | 4.508e-03 | 8 | blanket.deg_blkt_inboard_poloidal_plasma; power.e_plant_net_electric_pulse_kwh; power.e_plant_net_electric_pulse_mj | 14 | 0 | 3.127e-03 / 7.584e-03 | 123 |
| **st_regression · campaign_stencil_forward (n = 28)** |  |  |  |  |  |  |  |  |  |  |  |  |
| A0/AR | rung | 14 | 14 | — | 0 / 3.920e-07 | 4.704e-07 | 6 | blanket.deg_blkt_inboard_poloidal_plasma; fwbs.p_cp_shield_nuclear_heat_mw; superconducting_tfcoil.a_tf_plasma_case | 0 | 0 | 0 / 3.920e-07 | 123 |
| A2/A0 | headline | 14 | 14 | — | 1.116e-10 / 1.154e-10 | 1.155e-10 | 0 | fwbs.p_cp_shield_nuclear_heat_mw; heat_transport.tlvpmw; superconducting_tfcoil.a_tf_plasma_case | 0 | 0 | 1.761e-03 / 5.969e-03 | 123 |
| **large_tokamak_nof · campaign_stencil_backward (n = 80)** |  |  |  |  |  |  |  |  |  |  |  |  |
| A0/AR | rung | 20 | 20 | — | 0 / 1.730e-10 | 2.645e-06 | 19 | blanket.deg_blkt_inboard_poloidal_plasma; heat_transport.tlvpmw; power.qac | 1 | 0 | 0 / 1.730e-10 | 122 |
| A1/A0 | rung | 20 | 20 | — | 7.127e-04 / 5.252e-03 | 7.984e-03 | 8 | power.qac | 14 | 0 | 1.795e-03 / 1.322e-02 | 122 |
| A2/A1 | headline | 20 | 20 | — | 0 / 4.613e-13 | 4.622e-13 | 5 | blanket.deg_blkt_inboard_poloidal_plasma; heat_transport.tlvpmw; pf_coil.stress_z_cs_self_midplane_profile | 0 | 0 | 2.016e-03 / 6.975e-02 | 122 |
| A2/A0 | beside | 20 | 20 | — | 7.127e-04 / 5.252e-03 | 7.984e-03 | 8 | power.qac | 14 | 0 | 1.003e-02 / 8.367e-02 | 122 |
| **low_aspect_ratio_DEMO · campaign_stencil_backward (n = 76)** |  |  |  |  |  |  |  |  |  |  |  |  |
| A0/AR | rung | 19 | 19 | — | 0 / 0 | 0 | — | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 0 / 0 | 123 |
| A1/A0 | rung | 19 | 19 | — | 5.482e-04 / 3.780e-03 | 4.505e-03 | 8 | blanket.deg_blkt_inboard_poloidal_plasma; power.e_plant_net_electric_pulse_kwh; power.e_plant_net_electric_pulse_mj | 14 | 0 | 5.482e-04 / 3.780e-03 | 123 |
| A2/A1 | headline | 19 | 19 | — | 0 / 0 | 6.864e-19 | 3 | blanket.deg_blkt_inboard_poloidal_plasma; pf_coil.stress_z_cs_self_midplane_profile | 0 | 0 | 1.509e-03 / 8.370e-03 | 123 |
| A2/A0 | beside | 19 | 19 | — | 5.482e-04 / 3.780e-03 | 4.505e-03 | 8 | blanket.deg_blkt_inboard_poloidal_plasma; power.e_plant_net_electric_pulse_kwh; power.e_plant_net_electric_pulse_mj | 14 | 0 | 3.124e-03 / 8.370e-03 | 123 |
| **st_regression · campaign_stencil_backward (n = 28)** |  |  |  |  |  |  |  |  |  |  |  |  |
| A0/AR | rung | 14 | 14 | — | 0 / 4.272e-08 | 6.407e-08 | 11 | blanket.deg_blkt_inboard_poloidal_plasma; fwbs.p_cp_shield_nuclear_heat_mw; superconducting_tfcoil.a_tf_plasma_case | 0 | 0 | 0 / 4.272e-08 | 123 |
| A2/A0 | headline | 14 | 14 | — | 5.339e-11 / 6.099e-11 | 7.318e-11 | 6 | blanket.deg_blkt_inboard_poloidal_plasma; current_drive.radius_beam_tangency_max; fwbs.p_cp_shield_nuclear_heat_mw; heat_transport.tlvpmw | 0 | 0 | 1.760e-03 / 5.988e-03 | 123 |

<sub>`fixed-point distance`</sub>

<sub>combining 9 stage table(s): `fixed-point distance — large_tokamak_nof — campaign_displaced`; `fixed-point distance — low_aspect_ratio_DEMO — campaign_displaced`; `fixed-point distance — st_regression — campaign_displaced`; `fixed-point distance — large_tokamak_nof — campaign_stencil_forward`; `fixed-point distance — low_aspect_ratio_DEMO — campaign_stencil_forward`; `fixed-point distance — st_regression — campaign_stencil_forward`; `fixed-point distance — large_tokamak_nof — campaign_stencil_backward`; `fixed-point distance — low_aspect_ratio_DEMO — campaign_stencil_backward`; `fixed-point distance — st_regression — campaign_stencil_backward`</sub>

**Table D.10.** *What pinning the burn time to a constant costs per call, and the inconsistency it leaves: six rows, one per pulsed configuration and regime. `st_regression` is steady-state and has no burn-time coupling, so the rung does not exist there. n = 6 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and source regime and its own n, and that n counts A0 and A1 campaign runs of that configuration). Per-seed column(s) *paired at*: companion Table F.12.*

| n | A1/A0 pooled | median | worse | burn-time residual, s: median [min, max] | relative (median) |
|---|---|---|---|---|---|
| **large_tokamak_nof · campaign_displaced (n = 50)** |  |  |  |  |  |
| 25 | **0.9275** | 1.0000 | 0 | 1.546e+02 [12.8111, 406.884] | 6.298e-02 |
| **low_aspect_ratio_DEMO · campaign_displaced (n = 50)** |  |  |  |  |  |
| 25 | **0.9840** | 1.0000 | 0 | 5.258e+02 [1.64882, 1436.26] | 5.275e-02 |
| **large_tokamak_nof · campaign_stencil_forward (n = 40)** |  |  |  |  |  |
| 20 | **0.9524** | 1.0000 | 0 | 1.173e+00 [2.61319e-07, 13.1365] | 4.566e-04 |
| **low_aspect_ratio_DEMO · campaign_stencil_forward (n = 38)** |  |  |  |  |  |
| 19 | **0.9500** | 1.0000 | 0 | 4.176e+00 [0, 34.2015] | 4.016e-04 |
| **large_tokamak_nof · campaign_stencil_backward (n = 40)** |  |  |  |  |  |
| 20 | **0.9524** | 1.0000 | 0 | 1.175e+00 [2.61418e-07, 13.1158] | 4.574e-04 |
| **low_aspect_ratio_DEMO · campaign_stencil_backward (n = 38)** |  |  |  |  |  |
| 19 | **0.9355** | 1.0000 | 0 | 4.184e+00 [0, 34.1746] | 4.024e-04 |

<sub>`the ownership rung A0 → A1`</sub>

<sub>combining 6 stage table(s): `ownership rung A0 → A1 — large_tokamak_nof — campaign_displaced`; `ownership rung A0 → A1 — low_aspect_ratio_DEMO — campaign_displaced`; `ownership rung A0 → A1 — large_tokamak_nof — campaign_stencil_forward`; `ownership rung A0 → A1 — low_aspect_ratio_DEMO — campaign_stencil_forward`; `ownership rung A0 → A1 — large_tokamak_nof — campaign_stencil_backward`; `ownership rung A0 → A1 — low_aspect_ratio_DEMO — campaign_stencil_backward`</sub>

**Table D.11.** *Every scheduled evaluation by arm, configuration and regime: how many were scheduled, how many finished, and each other outcome class by the last line of its traceback. The *rows sum* column is the all-or-none check that the classes account for the denominator. The entry reference's rows are in the reference-entries table. n = 9 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and source regime and its own n, and that n counts evaluation-phase campaign runs of that configuration).*

| arm | scheduled | ok | rows sum | detail (traceback's last line × count) |
|---|---|---|---|---|
| **large_tokamak_nof · campaign_displaced (n = 100)** |  |  |  |  |
| AR | 25 | 25 | yes | — |
| A0 | 25 | 25 | yes | — |
| A1 | 25 | 25 | yes | — |
| A2 | 25 | 25 | yes | — |
| **low_aspect_ratio_DEMO · campaign_displaced (n = 100)** |  |  |  |  |
| AR | 25 | 25 | yes | — |
| A0 | 25 | 25 | yes | — |
| A1 | 25 | 25 | yes | — |
| A2 | 25 | 25 | yes | — |
| **st_regression · campaign_displaced (n = 75)** |  |  |  |  |
| AR | 25 | 25 | yes | — |
| A0 | 25 | 25 | yes | — |
| A2 | 25 | 25 | yes | — |
| **large_tokamak_nof · campaign_stencil_forward (n = 80)** |  |  |  |  |
| AR | 20 | 20 | yes | — |
| A0 | 20 | 20 | yes | — |
| A1 | 20 | 20 | yes | — |
| A2 | 20 | 20 | yes | — |
| **low_aspect_ratio_DEMO · campaign_stencil_forward (n = 76)** |  |  |  |  |
| AR | 19 | 19 | yes | — |
| A0 | 19 | 19 | yes | — |
| A1 | 19 | 19 | yes | — |
| A2 | 19 | 19 | yes | — |
| **st_regression · campaign_stencil_forward (n = 42)** |  |  |  |  |
| AR | 14 | 14 | yes | — |
| A0 | 14 | 14 | yes | — |
| A2 | 14 | 14 | yes | — |
| **large_tokamak_nof · campaign_stencil_backward (n = 80)** |  |  |  |  |
| AR | 20 | 20 | yes | — |
| A0 | 20 | 20 | yes | — |
| A1 | 20 | 20 | yes | — |
| A2 | 20 | 20 | yes | — |
| **low_aspect_ratio_DEMO · campaign_stencil_backward (n = 76)** |  |  |  |  |
| AR | 19 | 19 | yes | — |
| A0 | 19 | 19 | yes | — |
| A1 | 19 | 19 | yes | — |
| A2 | 19 | 19 | yes | — |
| **st_regression · campaign_stencil_backward (n = 42)** |  |  |  |  |
| AR | 14 | 14 | yes | — |
| A0 | 14 | 14 | yes | — |
| A2 | 14 | 14 | yes | — |

<sub>`failure taxonomy, the evaluation phase`</sub>

<sub>combining 9 stage table(s): `failure taxonomy — large_tokamak_nof — campaign_displaced`; `failure taxonomy — low_aspect_ratio_DEMO — campaign_displaced`; `failure taxonomy — st_regression — campaign_displaced`; `failure taxonomy — large_tokamak_nof — campaign_stencil_forward`; `failure taxonomy — low_aspect_ratio_DEMO — campaign_stencil_forward`; `failure taxonomy — st_regression — campaign_stencil_forward`; `failure taxonomy — large_tokamak_nof — campaign_stencil_backward`; `failure taxonomy — low_aspect_ratio_DEMO — campaign_stencil_backward`; `failure taxonomy — st_regression — campaign_stencil_backward`</sub>

### D.3 The optimisation phase

One full optimisation per start, 25 starts per arm per configuration (seed 0 unperturbed, seeds 1–24 displaced at δ = 0.10). Every check is over **the seed set** — the seeds on which every arm reached an accepted optimum (status ok and the output file's `ifail == 1`) — whose size the per-arm success grid in §4.3 (Table 10) states once per configuration and every other table repeats as its n; the seeds outside it are the failure table's, in the companion file, so the filter cannot flatter an arm that fails on expensive seeds. Every ratio is against the flat control `B0`; `BR → B0` is published beside as the yardstick, never accepted on. Cost is solve-phase model-node executions summed over the optimiser's attempts (the output path and the exit audit excluded alike in every arm), published with and without the seeds on which either side retried; the attempt-summation identity that licenses this is printed per run in the companion file. **One construction, one table**: the three configurations are row groups of each table, under a sub-heading row naming the configuration and stating its own n; `B1` is inactive on `st_regression`, so its rows are absent from that group and its columns empty there. The phase's headline tables are in §4.3 and are not repeated here — per-arm success (Table 10), whose merged whole with the failure taxonomy and the seed set is Table D.12 below, the same optimum (Table 11), the optimiser's path (Tables 12–15), check 4's cost sums (Table 16) and module sweeps per run (Table 17), whose function-weighted twin is Table D.24 in D.4.

**Table D.12.** *Reliability read both ways, configurations stacked — **the whole of it**, of which the main text's per-arm success grid is the first seven columns. Per arm, of the 25 starts offered: accepted optima (status ok and the output file's `ifail == 1`), the other starts by outcome class, and the starts lost that another arm accepted. Beside them, the failure taxonomy over every optimisation-phase run of the configuration — scheduled, crashed, ok, the all-or-none *rows sum* check and the last line of each traceback with its count — and, per configuration and repeated down its arm rows, the **seed set**: the seeds on which *every* arm reached an accepted optimum, which every other optimisation table's n is, with the configuration-invalid seeds and the retried seeds per arm. The three constructions have three different denominators and each sub-heading row states them. Reported, not accepted on (D29, 2026-09-15). n = 9 (row group(s) of this table, each over its own population with its own n in its sub-heading row; never pooled). Per-seed column(s) *seeds not accepted, by class*, *seeds lost that another arm accepted*, *seeds in the set*: companion Table F.13.*

| arm | starts offered | accepted optima | crashed (RuntimeError) | lost, another arm accepted | seed set (every arm accepted) | scheduled | crashed | ok | rows sum | detail (traceback's last line × count) | arms | which | seeds offered | n (every arm converged) | configuration-invalid seeds | retried seeds per arm | finished, ifail = 5 | coupling-loop cap (ModuleSolveFailure) | unconverged |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **large_tokamak_nof — 3 construction(s): `per-arm success` n = 25; `failure taxonomy` n = 100; `the seed set` n = 25** |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| BR | 25 | 22 | 3 | 0 | 22 | 25 | 3 | 22 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×3 | 4 | BR · B0 · B1 · B2 | 25 | 22 | 3 | BR 0 · B0 0 · B1 0 · B2 0 |  |  |  |
| B0 | 25 | 22 | 3 | 0 | 22 | 25 | 3 | 22 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×3 | 4 | BR · B0 · B1 · B2 | 25 | 22 | 3 | BR 0 · B0 0 · B1 0 · B2 0 |  |  |  |
| B1 | 25 | 22 | 3 | 0 | 22 | 25 | 3 | 22 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×3 | 4 | BR · B0 · B1 · B2 | 25 | 22 | 3 | BR 0 · B0 0 · B1 0 · B2 0 |  |  |  |
| B2 | 25 | 22 | 3 | 0 | 22 | 25 | 3 | 22 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×3 | 4 | BR · B0 · B1 · B2 | 25 | 22 | 3 | BR 0 · B0 0 · B1 0 · B2 0 |  |  |  |
| **low_aspect_ratio_DEMO — 3 construction(s): `per-arm success` n = 25; `failure taxonomy` n = 100; `the seed set` n = 25** |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| BR | 25 | 12 | 2 | 0 | 11 | 25 | 2 | 23 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×2 | 4 | BR · B0 · B1 · B2 | 25 | 11 | 13 | BR 12 · B0 10 · B1 10 · B2 10 | 11 | 0 | 0 |
| B0 | 25 | 12 | 2 | 0 | 11 | 25 | 2 | 21 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×2; process.core.solver.module_solve.ModuleSolveFailure: block FLAT did not converge in 20 sweeps at tau=1e-06; max scaled residual inf on current_drive.eta_cd_dimensionless_hcd_primary, 1 components above tau ×2 | 4 | BR · B0 · B1 · B2 | 25 | 11 | 13 | BR 12 · B0 10 · B1 10 · B2 10 | 9 | 2 | 2 |
| B1 | 25 | 11 | 2 | 1 | 11 | 25 | 2 | 20 | yes | process.core.solver.module_solve.ModuleSolveFailure: block FLAT did not converge in 20 sweeps at tau=1e-06; max scaled residual inf on current_drive.eta_cd_dimensionless_hcd_primary, 1 components above tau ×3; RuntimeError: Failed to converge after 50 iterations, value is nan. ×2 | 4 | BR · B0 · B1 · B2 | 25 | 11 | 13 | BR 12 · B0 10 · B1 10 · B2 10 | 9 | 3 | 3 |
| B2 | 25 | 11 | 2 | 1 | 11 | 25 | 2 | 20 | yes | process.core.solver.module_solve.ModuleSolveFailure: block M1 did not converge in 20 sweeps at tau=1e-06; max scaled residual inf on current_drive.eta_cd_dimensionless_hcd_primary, 1 components above tau ×3; RuntimeError: Failed to converge after 50 iterations, value is nan. ×2 | 4 | BR · B0 · B1 · B2 | 25 | 11 | 13 | BR 12 · B0 10 · B1 10 · B2 10 | 9 | 3 | 3 |
| **st_regression — 3 construction(s): `per-arm success` n = 25; `failure taxonomy` n = 75; `the seed set` n = 25** |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| BR | 25 | 24 |  | 0 | 22 | 25 |  | 25 | yes | — | 3 | BR · B0 · B2 | 25 | 22 | 1 | BR 5 · B0 3 · B2 2 | 1 |  |  |
| B0 | 25 | 23 |  | 1 | 22 | 25 |  | 25 | yes | — | 3 | BR · B0 · B2 | 25 | 22 | 1 | BR 5 · B0 3 · B2 2 | 2 |  |  |
| B2 | 25 | 23 |  | 1 | 22 | 25 |  | 25 | yes | — | 3 | BR · B0 · B2 | 25 | 22 | 1 | BR 5 · B0 3 · B2 2 | 2 |  |  |

<sub>`per-arm success, the seed set and the failure taxonomy`</sub>

<sub>combining 9 stage table(s): `per-arm success — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`; `failure taxonomy — large_tokamak_nof — campaign_optimisation`; `the seed set — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`; `per-arm success — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`; `failure taxonomy — low_aspect_ratio_DEMO — campaign_optimisation`; `the seed set — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`; `per-arm success — st_regression — campaign_optimisation · BR·B0·B2`; `failure taxonomy — st_regression — campaign_optimisation`; `the seed set — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table D.13.** ***The three configurations do not optimise the same thing.** From the runs' own stamps: the figure of merit and its name and sense (read from the frozen tree's `FiguresOfMerit`; a negative figure of merit means *maximise*), the iteration variables and the constraints as total (equality / inequality) as the unlifted arms solve them, the same after the burn-time lift, and whether the configuration is pulsed. Every cross-configuration comparison in this report is three answers to three questions, never one sample of three. n = 3 (configurations whose problem this table states).*

| configuration | n (runs) | `i_figure_merit` | objective | sense | vars | constraints (eq / ineq) | vars after the lift | constraints after the lift | pulsed |
|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | 44 | 1 | Plasma major radius (R₀) | minimise | 20 | 26 (3 / 23) | 21 | 27 (4 / 23) | yes |
| low_aspect_ratio_DEMO | 22 | -14 | Pulse length | maximise | 19 | 25 (4 / 21) | 20 | 26 (5 / 21) | yes |
| st_regression | 44 | -5 | Fusion gain (Qₚₗₐₛₘₐ) | maximise | 14 | 18 (3 / 15) | 14 | 18 (3 / 15) | no (k = 0) |

<sub>`the problem each configuration poses`</sub>

<sub>combining 1 stage table(s): `problem definition — campaign_optimisation`</sub>

**Table D.14.** *Node calls per run by node group and arm, the three configurations stacked, each over its own seed set (mean, [min, max]); `B2` against `B0` pooled, as the per-run median with its bracket and as runs on which `B2` cost more. These are whole-run census counts: a group's last row is the part outside the solve phase, so the row above it less that row is check 4's solve-phase total. `B1` is inactive on `st_regression`. n = 3 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and its own n, and that n counts seeds on which every arm of that configuration converged).*

| module | nodes | which | BR | B0 | B1 | B2 | B2/B0 pooled | B2/B0 per-run median | [min, max] | runs B2 > B0 | of n |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **large_tokamak_nof (n = 22)** |  |  |  |  |  |  |  |  |  |  |  |
| M1 | 2 | physics, plasma_geom | 3956.5 [3516, 4560] | 4055.1 [3586, 4792] | 4082.2 [3642, 4762] | 2778.3 [2482, 3248] | **0.6851** | 0.6909 | [0.598, 0.799] | 0 | 22 |
| M2 | 3 | build, cicc_sctfcoil, pfcoil | 5934.7 [5274, 6840] | 6082.6 [5379, 7188] | 6123.3 [5463, 7143] | 5286.5 [4719, 6174] | **0.8691** | 0.8765 | [0.761, 1.013] | 1 | 22 |
| M3 | 12 | Plant: 12 nodes (the committed node map's members) | 23738.7 [21096, 27360] | 24330.5 [21516, 28752] | 24493.1 [21852, 28572] | 18499.6 [16536, 21660] | **0.7603** | 0.7670 | [0.657, 0.887] | 0 | 22 |
| PULSE | 1 | pulse | 1978.2 [1758, 2280] | 2027.5 [1793, 2396] | 2041.1 [1821, 2381] | 641.0 [573, 749] | **0.3161** | 0.3189 | [0.276, 0.369] | 0 | 22 |
| once per run | 3 | costs, vacuum, water_use | 5934.7 [5274, 6840] | 6082.6 [5379, 7188] | 6123.3 [5463, 7143] | 6 | **0.0010** | 0.0010 | [0.001, 0.001] | 0 | 22 |
| all counted nodes | 21 | every node above | 41542.8 [36918, 47880] | 42578.5 [37653, 50316] | 42862.9 [38241, 50001] | 27211.5 [24320, 31837] | **0.6391** | 0.6447 | [0.555, 0.746] | 0 | 22 |
| of which outside the solve phase | — | the output path and the exit audit's sweep | 63 | 63 | 21 | 24 | **0.3810** | 0.3810 | [0.381, 0.381] | 0 | 22 |
| **low_aspect_ratio_DEMO (n = 11)** |  |  |  |  |  |  |  |  |  |  |  |
| M1 | 2 | physics, plasma_geom | 16191.1 [5808, 63740] | 15720.0 [5620, 62432] | 10873.8 [5070, 34344] | 7342.4 [3418, 23190] | **0.4671** | 0.5420 | [0.084, 4.126] | 2 | 11 |
| M2 | 3 | build, cicc_sctfcoil, pfcoil | 24286.6 [8712, 95610] | 23580.0 [8430, 93648] | 16310.7 [7605, 51516] | 13982.5 [6525, 44169] | **0.5930** | 0.6891 | [0.106, 5.240] | 2 | 11 |
| M3 | 12 | Plant: 12 nodes (the committed node map's members) | 97146.5 [34848, 382440] | 94320.0 [33720, 374592] | 65242.9 [30420, 206064] | 51290.2 [23904, 161856] | **0.5438** | 0.6324 | [0.097, 4.800] | 2 | 11 |
| PULSE | 1 | pulse | 8095.5 [2904, 31870] | 7860.0 [2810, 31216] | 5436.9 [2535, 17172] | 1715.4 [799, 5419] | **0.2182** | 0.2539 | [0.039, 1.928] | 2 | 11 |
| once per run | 3 | costs, vacuum, water_use | 24286.6 [8712, 95610] | 23580.0 [8430, 93648] | 16310.7 [7605, 51516] | 6 | **0.0003** | 0.0005 | [0.000, 0.001] | 0 | 11 |
| all counted nodes | 21 | every node above | 170006.5 [60984, 669270] | 165060.0 [59010, 655536] | 114175.1 [53235, 360612] | 74336.4 [34652, 234640] | **0.4504** | 0.5236 | [0.081, 3.976] | 2 | 11 |
| of which outside the solve phase | — | the output path and the exit audit's sweep | 63 | 63 | 21 | 24 | **0.3810** | 0.3810 | [0.381, 0.381] | 0 | 11 |
| **st_regression (n = 22; arms BR·B0·B2)** |  |  |  |  |  |  |  |  |  |  |  |
| M1 | 2 | physics, plasma_geom | 12088.6 [3780, 79904] | 10101.9 [3790, 28168] | — | 6502.2 [2726, 19270] | **0.6437** | 0.7156 | [0.165, 0.894] | 0 | 22 |
| M2 | 3 | build, croco_sctfcoil, pfcoil | 18133.0 [5670, 119856] | 15152.9 [5685, 42252] | — | 10121.6 [4104, 30957] | **0.6680** | 0.7235 | [0.169, 0.955] | 0 | 22 |
| M3 | 12 | Plant: 12 nodes (the committed node map's members) | 72531.8 [22680, 479424] | 60611.5 [22740, 169008] | — | 39900.5 [16668, 119148] | **0.6583** | 0.7314 | [0.168, 0.929] | 0 | 22 |
| once per run | 4 | costs, pulse, vacuum, water_use | 24177.3 [7560, 159808] | 20203.8 [7580, 56336] | — | 8 | **0.0004** | 0.0007 | [0.000, 0.001] | 0 | 22 |
| all counted nodes | 21 | every node above | 126930.7 [39690, 838992] | 106070.0 [39795, 295764] | — | 56532.3 [23509, 169383] | **0.5330** | 0.5908 | [0.136, 0.753] | 0 | 22 |
| of which outside the solve phase | — | the output path and the exit audit's sweep | 63 | 63 | — | 25 | **0.3968** | 0.3968 | [0.397, 0.397] | 0 | 22 |

<sub>`node calls per module`</sub>

<sub>combining 3 stage table(s): `node calls per module — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`; `node calls per module — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`; `node calls per module — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table D.15.** *Where each pair of arms landed, by configuration: check 1's objective difference repeated for direct comparison, then the maximum relative difference over the **iteration variables** the two runs share by name, as median, p90 and maximum, with the variable it sat on most often and any variable one side alone carries. **A diagnostic. D6 forbids gating on it, and nothing in this report's verdicts rests on it** — some iteration variables are not identified by the problem and differ at an unchanged optimum. The yardstick pair is a change of stopping rule and nothing else. n = 176 (arm-pair comparisons over the configurations' seed sets).*

| configuration | pair | n | objf med | objf p90 | point med | point p90 | point max | shared vars | extra vars | argmax census |
|---|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | BR → B0 (yardstick) | 22 | 2.082e-15 | 6.893e-13 | 7.170e-07 | 2.549e-06 | 1.632e-04 | 20 | — | t_tf_superconductor_quench (7/22); f_nd_impurity_electrons(13) (6/22); dr_cs (3/22) |
|  | B0 → B1 | 22 | 2.823e-11 | 4.570e-11 | 4.564e-02 | 1.870e-01 | 4.408e-01 | 20 | t_plant_pulse_burn | f_nd_alpha_thermal_electron (12/22); f_nd_impurity_electrons(13) (5/22); t_tf_superconductor_quench (2/22) |
|  | B0 → B2 | 22 | 2.823e-11 | 4.570e-11 | 4.564e-02 | 1.870e-01 | 4.408e-01 | 20 | t_plant_pulse_burn | f_nd_alpha_thermal_electron (12/22); f_nd_impurity_electrons(13) (5/22); t_tf_superconductor_quench (2/22) |
|  | B1 → B2 | 22 | 0 | 0 | 0 | 1.012e-11 | 6.721e-11 | 21 | — | b_plasma_toroidal_on_axis (18/22); dr_tf_nose_case (2/22); f_nd_alpha_thermal_electron (2/22) |
| low_aspect_ratio_DEMO | BR → B0 (yardstick) | 11 | 1.982e-14 | 1.976e-13 | 5.625e-12 | 8.975e-10 | 3.467e-07 | 19 | — | dr_cs (9/11); f_j_cs_start_pulse_end_flat_top (2/11) |
|  | B0 → B1 | 11 | 4.101e-07 | 2.148e-06 | 5.348e-06 | 1.011e-05 | 7.038e-03 | 19 | t_plant_pulse_burn | j_cs_flat_top_end (7/11); dr_cs (2/11); f_j_cs_start_pulse_end_flat_top (2/11) |
|  | B0 → B2 | 11 | 4.101e-07 | 2.148e-06 | 5.348e-06 | 1.011e-05 | 7.038e-03 | 19 | t_plant_pulse_burn | j_cs_flat_top_end (7/11); dr_cs (2/11); f_j_cs_start_pulse_end_flat_top (2/11) |
|  | B1 → B2 | 11 | 0 | 2.665e-14 | 0 | 1.074e-11 | 3.248e-11 | 20 | — | b_plasma_toroidal_on_axis (8/11); f_j_cs_start_pulse_end_flat_top (2/11); dr_cs (1/11) |
| st_regression | BR → B0 (yardstick) | 22 | 1.553e-13 | 5.908e-09 | 4.459e-05 | 1.704e-01 | 1.000e+00 | 14 | — | dr_tf_nose_case (9/22); dr_shld_inboard (7/22); dr_bore (5/22) |
|  | B0 → B2 | 22 | 3.467e-13 | 3.510e-09 | 4.528e-06 | 2.068e-01 | 1.000e+00 | 14 | — | dr_shld_inboard (14/22); dr_tf_nose_case (6/22); dr_bore (1/22) |

<sub>`the location diagnostic`</sub>

<sub>combining 1 stage table(s): `location diagnostic — campaign_optimisation`</sub>

**Table D.16.** ***The partition at an unchanged trajectory**: over the pairs on which both `B1` and `B2` reached an accepted optimum, how many agree exactly on evaluations of the model set, on optimiser iterations summed over the attempts, and on a **bit-identical** `norm_objf` — compared as the hex float the record stamps, so identity is exact and not agreement to a printed precision. `B1` is inactive on `st_regression`, which therefore has no row. n = 33 (pairs on which both arms of B1 → B2 reached an accepted optimum).*

| configuration | pair | pairs | evaluations identical | iterations identical | objf bit-identical |
|---|---|---|---|---|---|
| large_tokamak_nof | B1 → B2 | 22 | 22 | 22 | **22** |
| low_aspect_ratio_DEMO | B1 → B2 | 11 | 11 | 11 | **8** |

<sub>`the identity B1 → B2`</sub>

<sub>combining 1 stage table(s): `the identity B1 → B2 — campaign_optimisation`</sub>

**Table D.17.** *Check 2 by configuration and arm pair: the iteration ratio summed over the optimiser's attempts (the acceptance construction) as median and as a ratio of sums, the final-attempt construction beside it, the evaluation-count ratio ε from `sweeps_per_eval.n_evaluations` with the seeds on which it is exactly 1, and the dispatch-sweep ratio — a mechanism, not a cost. n = 3 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and its own n, and that n counts seeds on which every arm of that configuration converged). Per-seed column(s) *attempts per seed (base/arm)*: companion Table F.14.*

| pair | n | summed median (acceptance) | summed sum ratio | verdict | final-attempt median | final-attempt sum ratio | ε median (evaluations) | ε = 1 on | sweeps median | constructions disagree |
|---|---|---|---|---|---|---|---|---|---|---|
| **large_tokamak_nof (n = 22)** |  |  |  |  |  |  |  |  |  |  |
| B0 → BR (beside) | 22 | **1.0000** | 1.0000 | **beside** | 1.0000 | 1.0000 | 1.0000 | 22 | 0.9795 | 0 |
| B0 → B1 | 22 | **1.0000** | 0.9942 | **PASS** | 1.0000 | 0.9942 | 1.0476 | 0 | 1.0139 | 0 |
| B0 → B2 | 22 | **1.0000** | 0.9942 | **PASS** | 1.0000 | 0.9942 | 1.0476 | 0 | 2.6524 | 0 |
| B1 → B2 (beside) | 22 | **1.0000** | 1.0000 | **beside** | 1.0000 | 1.0000 | 1.0000 | 22 | 2.6158 | 0 |
| **low_aspect_ratio_DEMO (n = 11)** |  |  |  |  |  |  |  |  |  |  |
| B0 → BR (beside) | 11 | **1.0000** | 1.0000 | **beside** | 1.0000 | 1.0000 | 1.0000 | 11 | 1.0352 | 1 |
| B0 → B1 | 11 | **0.8125** | 0.7012 | **PASS** | 0.8333 | 1.0088 | 0.8468 | 0 | 0.8046 | 1 |
| B0 → B2 | 11 | **0.8125** | 0.7012 | **PASS** | 0.8333 | 1.0088 | 0.8468 | 0 | 2.1169 | 1 |
| B1 → B2 (beside) | 11 | **1.0000** | 1.0000 | **beside** | 1.0000 | 1.0000 | 1.0000 | 11 | 2.6335 | 0 |
| **st_regression (n = 22; arms BR·B0·B2)** |  |  |  |  |  |  |  |  |  |  |
| B0 → BR (beside) | 22 | **1.0000** | 1.2405 | **beside** | 1.0000 | 0.9221 | 1.0000 | 15 | 0.9906 | 3 |
| B0 → B2 | 22 | **1.0000** | 0.9530 | **PASS** | 1.0000 | 1.0019 | 1.0000 | 14 | 2.7767 | 1 |

<sub>`iteration multiplier (check 2)`</sub>

<sub>combining 3 stage table(s): `iteration multiplier (check 2) — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`; `iteration multiplier (check 2) — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`; `iteration multiplier (check 2) — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table D.18.** *Check 4 by configuration and arm: solve-phase model-node executions per run over the seed set with the observed bracket, the arrangement-method calls beside them, and the ratio against `B0` with and without the seeds on which either side retried. The output path and the exit audit are excluded alike in every arm. n = 3 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and its own n, and that n counts seeds on which every arm of that configuration converged).*

| arm | n | node calls per run [min, max] | arrangement·method calls / run | arrangement·method calls, Σ over the set | with retried: pooled | with retried: median | worse | retried seeds | without retried: pooled | without retried: median | n without |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **large_tokamak_nof (n = 22)** |  |  |  |  |  |  |  |  |  |  |  |
| BR | 22 | 41479.8 [36855, 47817] | 0.0 | 0 | **0.9756** | 0.9794 | 0 | 0 | 0.9756 | 0.9794 | 22 |
| B0 | 22 | 42515.5 [37590, 50253] | 0.0 | 0 | **1.0000** | 1.0000 | 0 | 0 | 1.0000 | 1.0000 | 22 |
| B1 | 22 | 42841.9 [38220, 49980] | 0.0 | 0 | **1.0077** | 1.0151 | 18 | 0 | 1.0077 | 1.0151 | 22 |
| B2 | 22 | 27187.5 [24296, 31813] | 5331.0 | 117281 | **0.6395** | 0.6452 | 0 | 0 | 0.6395 | 0.6452 | 22 |
| **low_aspect_ratio_DEMO (n = 11)** |  |  |  |  |  |  |  |  |  |  |  |
| BR | 11 | 169943.5 [60921, 669207] | 0.0 | 0 | **1.0300** | 1.0352 | 11 | 1 | 1.0351 | 1.0352 | 10 |
| B0 | 11 | 164997.0 [58947, 655473] | 0.0 | 0 | **1.0000** | 1.0000 | 0 | 1 | 1.0000 | 1.0000 | 10 |
| B1 | 11 | 114154.1 [53214, 360591] | 0.0 | 0 | **0.6919** | 0.8049 | 3 | 1 | 1.0129 | 0.8257 | 10 |
| B2 | 11 | 74312.4 [34628, 234616] | 14318.5 | 157504 | **0.4504** | 0.5237 | 2 | 1 | 0.6594 | 0.5371 | 10 |
| **st_regression (n = 22; arms BR·B0·B2)** |  |  |  |  |  |  |  |  |  |  |  |
| BR | 22 | 126867.7 [39627, 838929] | 0.0 | 0 | **1.1968** | 0.9906 | 3 | 3 | 0.8999 | 0.9906 | 19 |
| B0 | 22 | 106007.0 [39732, 295701] | 0.0 | 0 | **1.0000** | 1.0000 | 0 | 1 | 1.0000 | 1.0000 | 21 |
| B2 | 22 | 56507.3 [23484, 169358] | 12762.5 | 280776 | **0.5331** | 0.5911 | 0 | 1 | 0.5439 | 0.5911 | 21 |

<sub>`cost (check 4)`</sub>

<sub>combining 3 stage table(s): `cost (check 4) — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`; `cost (check 4) — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`; `cost (check 4) — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table D.19.** *The partitioned arm's cost ratio against **both** anchors, by configuration and set, from the same sums as check 4's cost table: `BR→B0` is the stopping-rule change alone, `B2/B0` isolates the architecture at a matched stopping rule and is the ladder's number, and `B2/BR` is the end-to-end change a user switching from PROCESS as shipped would see. Neither of the last two is more correct; they answer different questions, and the gap between them is exactly what the stopping rule is worth. n = 6 (configuration × set rows, each over its own seeds — the n column).*

| configuration | set | n | BR→B0 | B2/B0 | B2/BR |
|---|---|---|---|---|---|
| large_tokamak_nof | every arm accepted | 22 | 1.0250 | 0.6395 | **0.6554** |
|  | without retried seeds | 22 | 1.0250 | 0.6395 | **0.6554** |
| low_aspect_ratio_DEMO | every arm accepted | 11 | 0.9709 | 0.4504 | **0.4373** |
|  | without retried seeds | 10 | 0.9661 | 0.6594 | **0.6371** |
| st_regression | every arm accepted | 22 | 0.8356 | 0.5331 | **0.4454** |
|  | without retried seeds | 19 | 1.1113 | 0.6150 | **0.6834** |

<sub>`cost against both anchors`</sub>

<sub>combining 1 stage table(s): `cost against both anchors — campaign_optimisation`</sub>

**Table D.20.** *The accounting that explains how node calls fall while dispatch sweeps rise, by configuration and arm over the seed set: summed solve-phase node calls, summed dispatch sweeps (`n_model_calls`, the field issue I-26 named as the sweep count), summed prime calls, and the two rates. `prime/sweep` is the prime's contract — one `set_fw_geometry()` per sweep — read as a check; `prime/node` is the quantity D19 excludes from every cost ratio in this report, named here so the exclusion has a size (trap T11). Both are **counts**, never costs. n = 11 (arm rows over the configurations' seed sets — the n column).*

| configuration | arm | n | node calls | dispatch sweeps | prime calls | prime/sweep | prime/node |
|---|---|---|---|---|---|---|---|
| large_tokamak_nof | BR | 22 | 912555 | 43521 | 0 | — | — |
|  | B0 | 22 | 935340 | 44606 | 0 | — | — |
|  | B1 | 22 | 942522 | 44904 | 0 | — | — |
|  | B2 | 22 | 598124 | 117303 | 117281 | 0.9998 | 0.1961 |
| low_aspect_ratio_DEMO | BR | 11 | 1869378 | 89051 | 0 | — | — |
|  | B0 | 11 | 1814967 | 86460 | 0 | — | — |
|  | B1 | 11 | 1255695 | 59806 | 0 | — | — |
|  | B2 | 11 | 817436 | 157515 | 157504 | 0.9999 | 0.1927 |
| st_regression | BR | 22 | 2791089 | 132975 | 0 | — | — |
|  | B0 | 22 | 2332155 | 111121 | 0 | — | — |
|  | B2 | 22 | 1243161 | 280798 | 280776 | 0.9999 | 0.2259 |

<sub>`sweeps and prime calls`</sub>

<sub>combining 1 stage table(s): `sweeps and prime calls — campaign_optimisation`</sub>

**Table D.21.** *What each arm left at its accepted optimum, by configuration, arm and ruler: the restricted maximum scaled residual as median and maximum, its argmax component, and the whole-state median beside it. Matched accuracy is the condition the cost ratios are read under; this table is where it is met or not. n = 3 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and its own n, and that n counts optimisation-phase runs of that configuration in this arm group). Per-seed column(s) *components above τ*: companion Table F.15.*

| arm | ruler | n (runs) | with a restricted statistic | restricted median / max | restricted argmax | whole-state median | components excluded | audit position | audit instrument |
|---|---|---|---|---|---|---|---|---|---|
| **large_tokamak_nof (n = 100)** |  |  |  |  |  |  |  |  |  |
| BR | frozen | 22 | 22 | 1.150e-11 / 1.332e-11 | heat_transport.tlvpmw | 1.150e-11 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
|  | mixed | 22 | 22 | 1.150e-11 / 1.253e-11 | heat_transport.tlvpmw | 1.150e-11 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | frozen | 22 | 22 | 1.150e-11 / 1.332e-11 | heat_transport.tlvpmw | 1.150e-11 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
|  | mixed | 22 | 22 | 1.150e-11 / 1.253e-11 | heat_transport.tlvpmw | 1.150e-11 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B1 | frozen | 22 | 22 | 0 / 7.257e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.c_pf_cs_coil_flat_top_ma | 0 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
|  | mixed | 22 | 22 | 0 / 6.928e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.c_pf_cs_coil_flat_top_ma | 0 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B2 | frozen | 22 | 22 | 0 / 7.257e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.c_pf_cs_coil_flat_top_ma | 1.066e+00 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
|  | mixed | 22 | 22 | 0 / 6.928e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.c_pf_cs_coil_flat_top_ma | 1.000e+00 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| **low_aspect_ratio_DEMO (n = 100)** |  |  |  |  |  |  |  |  |  |
| BR | frozen | 23 | 23 | 0 / inf | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.eta_cd_dimensionless_hcd_primary, pf_coil.f_j_cs_start_end_flat_top | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
|  | mixed | 23 | 23 | 0 / inf | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.eta_cd_dimensionless_hcd_primary, pf_coil.f_j_cs_start_end_flat_top | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | frozen | 21 | 21 | 0 / 5.315e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
|  | mixed | 21 | 21 | 0 / 3.995e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B1 | frozen | 20 | 20 | 0 / 5.315e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
|  | mixed | 20 | 20 | 0 / 4.365e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B2 | frozen | 20 | 20 | 0 / 5.315e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 1.007e+00 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
|  | mixed | 20 | 20 | 0 / 3.995e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 1.000e+00 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| **st_regression (n = 75; arms BR·B0·B2)** |  |  |  |  |  |  |  |  |  |
| BR | frozen | 25 | 25 | 4.875e-14 / 5.040e-14 | blanket.deg_blkt_inboard_poloidal_plasma, physics.f_beta_alpha_beam_thermal | 4.875e-14 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
|  | mixed | 25 | 25 | 4.871e-14 / 5.035e-14 | blanket.deg_blkt_inboard_poloidal_plasma, physics.f_beta_alpha_beam_thermal | 4.871e-14 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | frozen | 25 | 25 | 4.894e-14 / 4.967e-14 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.big_q_plasma, physics.f_beta_alpha_beam_thermal | 4.894e-14 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
|  | mixed | 25 | 25 | 4.889e-14 / 4.962e-14 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.big_q_plasma, physics.f_beta_alpha_beam_thermal | 4.889e-14 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B2 | frozen | 25 | 25 | 7.497e-12 / 3.587e-11 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, heat_transport.tlvpmw, physics.f_beta_alpha_beam_thermal, superconducting_tfcoil.a_tf_plasma_case | 1.598e+00 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
|  | mixed | 25 | 25 | 6.643e-12 / 3.585e-11 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, heat_transport.tlvpmw, physics.f_beta_alpha_beam_thermal, superconducting_tfcoil.a_tf_plasma_case | 1.000e+00 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |

<sub>`achieved accuracy at the accepted optimum`</sub>

<sub>combining 3 stage table(s): `achieved accuracy at the accepted optimum — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`; `achieved accuracy at the accepted optimum — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`; `achieved accuracy at the accepted optimum — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table D.22.** *Check 3 on the two pulsed configurations: constraint 93's residual at every accepted optimum of the arms that carry the lifted design variable, absolute and relative, and whether the constraint sits in the equality block. `st_regression` has no burn-time coupling and no lift. n = 2 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and its own n, and that n counts optimisation-phase campaign runs of that configuration).*

| arm | n accepted | residual, s: median [min, max] | relative (median) | in the equality block |
|---|---|---|---|---|
| **large_tokamak_nof (n = 100)** |  |  |  |  |
| B1 | 22 | 1.659e-05 [2.600e-06, 1.600e-03] | 2.304e-09 | True |
| B2 | 22 | 1.659e-05 [2.600e-06, 1.600e-03] | 2.304e-09 | True |
| **low_aspect_ratio_DEMO (n = 100)** |  |  |  |  |
| B1 | 11 | 5.480e-06 [1.692e-07, 4.756e-05] | 6.744e-10 | True |
| B2 | 11 | 5.480e-06 [1.692e-07, 4.756e-05] | 6.744e-10 | True |

<sub>`the lift closed (check 3)`</sub>

<sub>combining 2 stage table(s): `the lift closed (check 3) — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`; `the lift closed (check 3) — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`</sub>

### D.4 The aggregate under three weightings

**How the weight per module skews the headline average** (the user, 2026-09-17). The per-module sweep ratios of Tables 9 and 17 are unit-free; only the aggregate depends on the weight per module, and the two tables here weight the same sweep counts per **function** — the dependency analysis's callable submodels behind each module's collapsed-DSM rows, a model with none counting as one — beside the report's two other weights. Three weightings of one set of sweep counts, each configuration nof / lad / st. In the **evaluation phase** (one `call_models` evaluation from a displaced entry, `A2` against its reference) the aggregate reads **0.5625 / 0.5772 / 0.5016** in **node calls** (Table 8's partitioning rung — the acceptance quantity), **[0.724, 0.767] / [0.742, 0.786] / [0.655, 0.709]** in **DSM rows** (Table 9's total) and **[0.695, 0.794] / [0.709, 0.811] / [0.626, 0.720]** in **functions** (Table D.23's total). In the **optimisation phase** (`B2` against `B0` over the seed set) it reads **0.6395 / 0.4504 / 0.5331** in node calls (Table 16, check 4), **[0.690, 0.736] / [0.476, 0.508] / [0.599, 0.653]** in DSM rows (Table 17's total) and **[0.650, 0.746] / [0.448, 0.514] / [0.565, 0.653]** in functions (Table D.24's total). A bracket is the `[v = 1, v = 0]` attribution interval of the once-per-run nodes' rows or functions (trap T9). **What does not depend on the weighting:** under any non-negative weighting the aggregate is a weighted mean of the per-module ratios and so lies between the smallest and the largest of them, and every per-module ratio in Tables 9 and 17 is at or below 1 except one — M2 on `large_tokamak_nof` in the evaluation phase, at **1.0078**; the largest in the optimisation phase is M2 on the same configuration at **0.8691**. So the **direction** of the saving is weighting-independent (only a weighting that put essentially all its weight on that one module could read otherwise) and its **magnitude** is not: across the three weightings the evaluation-phase aggregate spans 0.50–0.81 and the optimisation-phase aggregate 0.45–0.75. Node calls weight the aggregate toward the groups with many executing nodes — M3's twelve and the once-per-run set — where the partition saves most; DSM rows and functions weight it toward M1 (24 of the 47 rows the four modules hold, 178 of their 344 functions on `large_tokamak_nof`), where it saves less. Node calls remain the acceptance unit (D19, D29); these tables are reported, not accepted on.

**Table D.23.** ***The main text's module sweeps table, weighted per function.** The same grid as the evaluation phase's module sweeps table — the sweep cells and the per-module ratios are that table's own, republished here, never recomputed — with `models` replaced by **`functions`**: the number of individual callables in the group, a model's callable submodels from the dependency analysis's decomposition at pin `PROCESS_at_36ac820e` (a model with no submodel counts as one function, its entry method). The counts are per configuration and differ per block where the exports do (the TF-coil model `i_tf_turn_type` selects, the electron-cyclotron model `st_regression` alone runs; M1 is 24 collapsed-DSM rows on the two pulsed configurations and 25 on `st_regression`). The total row is Σ sweeps × functions per arm and its ratio the `[v = 1, v = 0]` bracket over the once-per-run nodes' own functions, the same attribution unknown as the DSM-row total's (trap T9). **Reported, not accepted on.** For each configuration the three totals side by side are: node calls (the headline, the per-call cost table's `A1→A2` / `A0→A2`), DSM rows (the module sweeps table's total) and functions (this table's total) — the context paragraph above reads them. n = 6 (block(s) of this table, each over its own population with its own n in its heading line; never pooled).*

**`nof`** (n = 25 per arm)

| module | functions | AR | A0 | A1 | A2 | reference | A2 / reference | pairs |
|---|---|---|---|---|---|---|---|---|
| M1 | 178 | 4.96 [4, 5] | 5.52 [5, 6] | 5.12 [4, 6] | 4 | A1 | **0.7812** | 25 |
| M2 | 90 | 4.96 [4, 5] | 5.52 [5, 6] | 5.12 [4, 6] | 5.16 [5, 6] | A1 | **1.0078** | 25 |
| M3 | 68 | 4.96 [4, 5] | 5.52 [5, 6] | 5.12 [4, 6] | 3 | A1 | **0.5859** | 25 |
| PULSE | 3 | 4.96 [4, 5] | 5.52 [5, 6] | 5.12 [4, 6] | 1 | A1 | **0.1953** | 25 |
| once per run | 50 | 4.96 [4, 5] | 5.52 [5, 6] | 5.12 [4, 6] | 0 | A1 | **0.0000** | 25 |
| total calls | 389 | 1929 | 2147 | 1992 | 1383 | A1 | **[0.695, 0.794]** | 25 |

**`lad`** (n = 25 per arm)

| module | functions | AR | A0 | A1 | A2 | reference | A2 / reference | pairs |
|---|---|---|---|---|---|---|---|---|
| M1 | 177 | 5 | 5 | 4.92 [4, 5] | 4 | A1 | **0.8130** | 25 |
| M2 | 90 | 5 | 5 | 4.92 [4, 5] | 4.88 [4, 5] | A1 | **0.9919** | 25 |
| M3 | 68 | 5 | 5 | 4.92 [4, 5] | 3 | A1 | **0.6098** | 25 |
| PULSE | 3 | 5 | 5 | 4.92 [4, 5] | 1 | A1 | **0.2033** | 25 |
| once per run | 50 | 5 | 5 | 4.92 [4, 5] | 0 | A1 | **0.0000** | 25 |
| total calls | 388 | 1940 | 1940 | 1909 | 1354 | A1 | **[0.709, 0.811]** | 25 |

**`st`** (n = 25 per arm)

| module | functions | AR | A0 | A1 | A2 | reference | A2 / reference | pairs |
|---|---|---|---|---|---|---|---|---|
| M1 | 178 | 4.92 [4, 5] | 5.84 [5, 6] | — | 4 | A0 | **0.6849** | 25 |
| M2 | 79 | 4.92 [4, 5] | 5.84 [5, 6] | — | 5.84 [5, 6] | A0 | **1.0000** | 25 |
| M3 | 72 | 4.92 [4, 5] | 5.84 [5, 6] | — | 3 | A0 | **0.5137** | 25 |
| once per run | 51 | 4.92 [4, 5] | 5.84 [5, 6] | — | 0 | A0 | **0.0000** | 25 |
| total calls | 380 | 1870 | 2219 | — | 1389 | A0 | **[0.626, 0.720]** | 25 |

<sub>`module sweeps per run, function-weighted, the evaluation phase`</sub>

<sub>combining 6 stage table(s): `module sweeps per run, function-weighted total — large_tokamak_nof — campaign_displaced`; `module sweeps per run — large_tokamak_nof — campaign_displaced`; `module sweeps per run, function-weighted total — low_aspect_ratio_DEMO — campaign_displaced`; `module sweeps per run — low_aspect_ratio_DEMO — campaign_displaced`; `module sweeps per run, function-weighted total — st_regression — campaign_displaced`; `module sweeps per run — st_regression — campaign_displaced`</sub>

**Table D.24.** ***The main text's optimisation-phase module sweeps table, weighted per function.** The same grid — the sweep cells, the per-module ratios and their per-run distributions are that table's own, republished, never recomputed — with `models` replaced by **`functions`**, the number of individual callables in the group from the dependency analysis's decomposition at pin `PROCESS_at_36ac820e` (a model with no submodel counts as one). The counts are per configuration and differ per block where the exports do. The total row is Σ sweeps × functions per arm over the whole run, its pooled ratio the `[v = 1, v = 0]` bracket over the once-per-run nodes' own functions (trap T9), and its per-run median and count above 1 are the v = 1 case. Whole-run census counts, as in the table it twins; `B1` is inactive on `st_regression`. **Reported, not accepted on.** For each configuration the three totals side by side are: node calls (the headline, check 4's `B2/B0`), DSM rows (the module sweeps table's total) and functions (this table's total) — the context paragraph above reads them. n = 6 (block(s) of this table, each over its own population with its own n in its heading line; never pooled).*

**`nof`** (n = 22)

| module | functions | BR | B0 | B1 | B2 | B2/B0 pooled | B2/B0 per-run median [min, max] | runs B2 > B0 |
|---|---|---|---|---|---|---|---|---|
| M1 | 178 | 1978 [1758, 2280] | 2028 [1793, 2396] | 2041 [1821, 2381] | 1389 [1241, 1624] | **0.6851** | 0.6909 [0.598, 0.799] | 0/22 |
| M2 | 90 | 1978 [1758, 2280] | 2028 [1793, 2396] | 2041 [1821, 2381] | 1762 [1573, 2058] | **0.8691** | 0.8765 [0.761, 1.013] | 1/22 |
| M3 | 68 | 1978 [1758, 2280] | 2028 [1793, 2396] | 2041 [1821, 2381] | 1542 [1378, 1805] | **0.7603** | 0.7670 [0.657, 0.887] | 0/22 |
| PULSE | 3 | 1978 [1758, 2280] | 2028 [1793, 2396] | 2041 [1821, 2381] | 641 [573, 749] | **0.3161** | 0.3189 [0.276, 0.369] | 0/22 |
| once per run | 50 | 1978 [1758, 2280] | 2028 [1793, 2396] | 2041 [1821, 2381] | 2 | **0.0010** | 0.001 | 0/22 |
| total calls | 389 | 769530 | 788715 | 793984 | 512717 | **[0.650, 0.746]** | 0.6556 [0.567, 0.758] | 0/22 |

**`lad`** (n = 11)

| module | functions | BR | B0 | B1 | B2 | B2/B0 pooled | B2/B0 per-run median [min, max] | runs B2 > B0 |
|---|---|---|---|---|---|---|---|---|
| M1 | 177 | 8096 [2904, 31870] | 7860 [2810, 31216] | 5437 [2535, 17172] | 3671 [1709, 11595] | **0.4671** | 0.5420 [0.084, 4.126] | 2/11 |
| M2 | 90 | 8096 [2904, 31870] | 7860 [2810, 31216] | 5437 [2535, 17172] | 4661 [2175, 14723] | **0.5930** | 0.6891 [0.106, 5.240] | 2/11 |
| M3 | 68 | 8096 [2904, 31870] | 7860 [2810, 31216] | 5437 [2535, 17172] | 4274 [1992, 13488] | **0.5438** | 0.6324 [0.097, 4.800] | 2/11 |
| PULSE | 3 | 8096 [2904, 31870] | 7860 [2810, 31216] | 5437 [2535, 17172] | 1715 [799, 5419] | **0.2182** | 0.2539 [0.039, 1.928] | 2/11 |
| once per run | 50 | 8096 [2904, 31870] | 7860 [2810, 31216] | 5437 [2535, 17172] | 2 | **0.0003** | 0.0005 [0.000, 0.001] | 0/11 |
| total calls | 388 | 3141072 | 3049680 | 2109521 | 1365163 | **[0.448, 0.514]** | 0.5200 [0.080, 3.954] | 2/11 |

**`st`** (n = 22; arms BR·B0·B2)

| module | functions | BR | B0 | B1 | B2 | B2/B0 pooled | B2/B0 per-run median [min, max] | runs B2 > B0 |
|---|---|---|---|---|---|---|---|---|
| M1 | 178 | 6044 [1890, 39952] | 5051 [1895, 14084] | — | 3251 [1363, 9635] | **0.6437** | 0.7156 [0.165, 0.894] | 0/22 |
| M2 | 79 | 6044 [1890, 39952] | 5051 [1895, 14084] | — | 3374 [1368, 10319] | **0.6680** | 0.7235 [0.169, 0.955] | 0/22 |
| M3 | 72 | 6044 [1890, 39952] | 5051 [1895, 14084] | — | 3325 [1389, 9929] | **0.6583** | 0.7314 [0.168, 0.929] | 0/22 |
| once per run | 51 | 6044 [1890, 39952] | 5051 [1895, 14084] | — | 2 | **0.0004** | 0.0007 [0.000, 0.001] | 0/22 |
| total calls | 380 | 2296841 | 1919363 | — | 1084735 | **[0.565, 0.653]** | 0.6260 [0.144, 0.793] | 0/22 |

<sub>`module sweeps per run, function-weighted, the optimisation phase`</sub>

<sub>combining 6 stage table(s): `module sweeps per run, function-weighted total — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`; `module sweeps per run — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`; `module sweeps per run, function-weighted total — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`; `module sweeps per run — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`; `module sweeps per run, function-weighted total — st_regression — campaign_optimisation · BR·B0·B2`; `module sweeps per run — st_regression — campaign_optimisation · BR·B0·B2`</sub>

<!-- plan_tables: end of the rendered results tables -->
