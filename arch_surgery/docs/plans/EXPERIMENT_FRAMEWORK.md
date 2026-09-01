# Experiment framework — implementation master plan

> **Document status** — CURRENT · design for the shared harness · rewritten 2026-09-01 against
> D13 (two-phase partition design).

**Status:** proposed as **A18 (experiment-framework)**. A1 (stage0-rebaseline) has already
delivered the parts marked *(built, A1)*. · **Base commit:** `c0ae5b28` · **Owns:** the shared
code every architecture experiment runs on.

**Governing principle — the framework is minimal, and stays minimal.** Build a component when a
*queued* task needs it, never because a variant point exists in the model below. Every hook carries
a permanent neutrality obligation, and an unused hook is that obligation with no result behind it.
Where this document describes a component that no queued task consumes, it is a **specification
held in reserve**, not work to schedule. §5.1 audits what is currently over-built.

This document specifies the code to build **before** running an experiment. The experiments
themselves are [`MDA_PARTITION_EXPERIMENT.md`](MDA_PARTITION_EXPERIMENT.md),
[`SUBDRIVER_LIFT_EXPERIMENT.md`](SUBDRIVER_LIFT_EXPERIMENT.md) and the deferred register
[`ARCHITECTURE_EXPERIMENT_CANDIDATES.md`](ARCHITECTURE_EXPERIMENT_CANDIDATES.md).

---

## 1. Problem context

### 1.1 Why a framework rather than a series of patches

Each experiment in the portfolio changes the driver in a different place. Built as independent
patches to `caller.py` they would collide in the same three files, produce different registry
numberings on different branches — which silently reinterprets any `IN.DAT` written against the
other — and leave no way to say which combination of changes produced a given result.

The organising idea is that **every experiment is a different value at one of five variant points**
in the driver. Once that is true, an experiment stops being a patch and becomes a *configuration*,
which is what makes arms composable, neutrality provable, and results attributable.

| VP | Where | Baseline behaviour | Variants (task) |
|---|---|---|---|
| **VP1 — sequence** | `_call_models_once` | the hand-written call order | `Build` moved (A3); DSM-sequenced order (A15, *deferred*) |
| **VP2 — loop membership** | the loop | every node runs every sweep | feed-forward tail hoisted out — **live** |
| **VP3 — convergence predicate** | the loop | agreement on objective + constraints | **agreement on coupling variables — live (A14, un-deferred by D13)** |
| **VP4 — loop topology** | the loop | one global fixed-point loop | per-module solves over M1/M2/M3 (A5) |
| **VP5 — lifted unknowns** | models + solver | inner root-find | unknown from the design vector, residual as a constraint (A4, A9-A11) |

Two consequences that were not obvious when the experiments were planned separately:

- **A4 (burn-time lift) and A9-A11 (subdriver lift) are the same mechanism.** Both are VP5: expose
  a residual, take the unknown from the design vector, add an equality constraint. One
  implementation serves both, and the subdriver experiment stops being a separate build.
- **The experiments are separable in code even though they interact in measurement.** The partition
  is VP1-VP4; the subdriver lift is VP5. Disjoint surfaces, one shared registry.

### 1.2 What D13 changed

The partition experiment now runs in two phases: **Phase A** compares fixed-point architectures
with the optimiser absent, **Phase B** reintroduces VMCON. That splits this framework in two, and
the split is the most important structural fact in this document.

| | Phase A half | Phase B half |
|---|---|---|
| Lives in | `arch_surgery/` only | `process/core/`, `process/models/` |
| Touches PROCESS | **no** | yes |
| Neutrality obligation | trivial — the production path is unchanged | per-hook, gated |
| D11 model-edit approval | not required | **required before merging** |
| Primary metric | counts (exact, bit-reproducible) | counts; wall clock as context only |

**Build the Phase A half first.** It is smaller, it carries no approval burden, it cannot perturb
the baseline it measures, and it produces a result on its own.

### 1.3 What A1 already built

The probe module `process/core/_idf_probe.py`, four measurement hooks
(`call_models_begin/end`, `sweep_begin/end`, `phase(...)`, `note_retry()`), the isolated run
harness (`run_one.py`, `run_stage0.py`) and the first three gates (neutrality, determinism,
solves) at the strength this framework needs — neutrality verified against a pristine
`git archive` of `c0ae5b28` on hex float literals plus whole-MFILE identity.

`note_retry()` has **never fired** in any run, so it is verified by inspection only.

### 1.4 PROCESS is not pristine, and what to do about it

`architecture_surgery` carries **1 632 lines of change to `process/` since `c0ae5b28`**:

| File | Lines | Kind |
|---|---|---|
| `process/core/_idf_probe.py` | +296 | new — A1's probe |
| `process/core/_idf_probe_modules.py` | +688 | new — A2's module instrument |
| `process/core/_idf_probe_frozen.py` | +610 | new — A19's replay instrument |
| `process/core/caller.py` | +14 | 6 guarded hook calls, 1 import |
| `process/core/solver/evaluators.py` | +10 | 3 guarded hook calls, 1 import |
| `process/core/solver/solver_handler.py` | +8 | 3 guarded hook calls, 1 import |

**Every edit to an existing file is additive.** The complete diff to the three PROCESS files is
three import lines plus twelve `if _idf_probe.ENABLED:` guards. **No original line of logic is
changed, reordered or deleted.** And it is not merely asserted: A1 gated switch-neutrality against
a pristine `git archive` of `c0ae5b28` — probe-off runs byte-identical on hex float literals and
whole-MFILE identity, four scenarios, eleven arms.

**So a fresh branch is not needed for correctness.** What *is* wrong is the shape: three
task-specific probe modules accreted one per task, inside `process/core/`, where a fourth would
otherwise follow. That is what **F1** exists to fix — consolidate to one `_experiment.py` with arm
parsing, and re-gate neutrality on the consolidated module.

**Phase A needs no new hook site at all.** The existing `sweep(models, data)` call
(`caller.py:273`) already receives both the model registry and the data structure, so the
harvest of `(x, y0)` is a new *mode* inside the probe module rather than a new call site in
PROCESS. Phase A therefore adds **zero** lines to `caller.py`.

**Recommendation.** Build F1 as a consolidation task on `architecture_surgery`, not a fresh branch
from `c0ae5b28`. A fresh branch would discard A1's neutrality verification, A2's module instrument
and A19's replay harness — the last of which is the Phase A instrument — and would have to
re-derive all three under the same gates to get back to where the tree already is. The clean-tree
property that matters is *provable neutrality*, and that already holds.

---

## 2. Proposed approach

### 2.1 C1 — `_experiment.py` (generalises A1's `_idf_probe.py`)

The single module holding arm configuration and hook state. Parses the active arm set from the
environment **once at import**; exposes `ENABLED` and per-variant-point selections as module-level
constants; holds the counters; provides the hooks. No PROCESS imports beyond data structures, so
it can be imported anywhere in `process/core/` without a cycle.

```
PROCESS_ARCH=baseline                       # instrumented, no behaviour change
PROCESS_ARCH=seq:dsm,hoist                  # VP1 + VP2 together
PROCESS_ARCH=partition,lift:t_plant_pulse_burn
```

Unset means every hook is a no-op and behaviour is byte-identical to upstream. Every arm's
identity, its resolved value and the tree's git HEAD go into each run's `metrics.json` — **a
result that cannot say which arms produced it is not a result.**

**Design rule.** A variant point is a branch on configuration, evaluated once per run, never a
per-call `if` in a hot path.

### 2.2 C2 — Hook points

Fixed and minimal. Adding a hook is a framework change needing its own neutrality check;
experiments must not add hooks ad hoc.

| Hook | Site | Serves |
|---|---|---|
| `call_models_begin/end` | `caller.py` | measurement (built, A1) |
| `sweep_begin/end` | `caller.py` | measurement (built, A1) |
| `phase(...)` | `solver/evaluators.py` | fn / grad / grad_reconcile attribution (built, A1) |
| `note_retry()` | `solver/solver_handler.py` | retry census (built, A1 — never fired) |
| `harvest(x, state)` | `caller.py` | **Phase A** — saves design points |
| `model_sequence()` | `_call_models_once` | VP1 |
| `in_loop(node)` | the loop | VP2 |
| `converged(y_prev, y)` | the loop | VP3 |
| `solve_blocks(...)` | the loop | VP4 |
| `subsolve(residual, x0, …)` | each VP5 site | VP5 |
| `note_subsolve(site, iters, converged)` | each VP5 site | robustness census (A9) |

`note_subsolve` is **read-only and independent of VP5** — it is how A9 measures failure incidence
without extracting anything, and it should land early.

### 2.3 C2a — The feed-forward set is dynamic, not a constant

**`in_loop(node)` must be a function of the active arm set.** `Pulse` (DSM row 39) is inside the
loop while `times.t_plant_pulse_burn` is unlifted and becomes a pure feed-forward node once VP5
lifts it. So a hoist arm with a hard-coded feed-forward list would be **wrong in exactly one
configuration: VP2 combined with VP5** — a latent defect that fires only when two arms compose,
which is the hardest kind to notice.

Derive the set from `(DSM node map, active arms)` at run time and record the resolved set in
`metrics.json`.

### 2.4 C9 — The fixed-point engine · *new, and the Phase A deliverable*

Plain **Gauss-Seidel (Picard) iteration** on a declared coupling-variable vector. It does **not**
reproduce the idempotence loop; it replaces it with a correct implementation.

```
y_{m+1} = G(y_m)          G = one pass over the in-loop node sequence
stop when  max_i |y_{m+1,i} - y_{m,i}| / (|y_{m,i}| + atol_i)  <  rtol
```

| Parameter | Value | Rationale |
|---|---|---|
| Floor | **1 sweep** | The entry state *is* `y0`. Today's floor of 2 exists only because `objf`/`conf` do not exist at entry, so the loop must evaluate once to manufacture a comparand |
| `y` set | **(b)** all state written by in-loop models, from the probe | Independent of the DSM's completeness |
| Cross-check set | **(a)** DSM feedback-edge variables, evaluated in parallel | Disagreement is a DSM validation result (C10) |
| `rtol` | `1e-6` per component | The *nominal* value today. **Do not describe it as "the same as today's"** — see the row below |
| `atol_i` | **chosen deliberately, per component, and recorded** | Today's predicate is `np.allclose(rtol=1e-6)`, whose hidden `atol=1e-8` dominates for `\|y\|<1e-2`. Measured at `c0ae5b28`: **18.0 % of nonzero MFILE quantities fall below that crossover** and 203 are small enough that *any* change passes. Inheriting numpy's default would silently reproduce that hole; leaving `atol_i = 0` makes near-zero components unconvergeable. Both failure modes are real, so the choice is stated per component, not defaulted (architecture evaluation F1 addendum) |
| Exclusions | accumulating fields only, **each measured and justified** | Counters never converge; an unjustified exclusion is a silent, arm-wide false convergence |
| NaN | **never converged** | Today's `equal_nan=True` reports a NaN state as converged; not reproduced |
| Acceleration | **none** | Aitken/Anderson is a separate variant point and would confound the topology change |
| Caps | inner **20**, outer **20**, global **200 module-sweeps per design point** | Reaching any marks the point **invalid** — never a budget |

**Design point.** The pair `(x, y0)` — design vector *and* entry state — restored bit-identically
for every arm. Not `x` alone: the entry state is what makes the comparison paired.

**Exit audit.** On termination every arm gets one further full sweep and the **same global
residual** is evaluated and recorded. This is how "matched final accuracy" is enforced —
per point, verified, rather than assumed from a shared tolerance setting.

**Pairwise drop.** A point enters the comparison only if every arm converged it. The drop census
is reported **before** any ratio.

**Arms.** `R` (today's loop, reference — not a competitor), `A0` (flat, control), `A1` (block).
The feed-forward hoist is a toggle, applied to both A0 and A1 in first results so it cancels.

### 2.5 C3 — The VP5 pattern

One pattern at every lifted residual, so the diff under `process/models/` is mechanical and
reviewable:

1. Extract the residual into a module-level `f(unknown, *inputs) -> float`. **Pure refactor** —
   the expression is unchanged, which is what satisfies D5/D11.
2. Replace the inline solve with `_experiment.subsolve(f, x0, args, site=...)`, whose default path
   performs *exactly* the original call with the original tolerances and failure policy.
3. When the site is lifted, `subsolve` returns the design-vector value and records the residual
   for the constraint layer.

Step 2 must be **provably inert**, so the frozen arm is byte-identical. That is what keeps the
model freeze intact and makes the extraction worth doing even if nothing is ever lifted.

**Measured constraint (A19):** the burn-time lift is **not separable** — `max Si` is unchanged to
four decimals when the coupler is pinned, so lifting alone buys nothing without VP4. VP5 must be
measured *with* the partition, never as a standalone arm claiming a saving. The feed-forward hoist
is the opposite. Do not generalise from one to the other.

### 2.6 C4 — Registry allocation (D10)

New iteration variables and constraints are **appended, never fitted into gaps**.
`N_ITERATION_VARIABLES_MAX` is derived as `max(ITERATION_VARIABLES.keys())`, so appending key 178
raises it automatically and every array sized by it grows. There are 94 gaps in 1-177 and reusing
one would silently reinterpret an existing `IN.DAT`. Constraints append from 93 with `lablcc`
extended in step.

[`REGISTRY_ALLOCATIONS.md`](REGISTRY_ALLOCATIONS.md) is the single allocation table, so two
branches cannot both claim 178.

**State in the write-up:** once `ixc = 178` validates here and not upstream, the fork's input
language has diverged. Inherent to lifting anything; not a blocker.

### 2.7 C5 — Run harness

Scenario x arm x repetition matrix. **Fresh subprocess and working directory per run** — mandatory,
because `OutputFileManager` holds file handles as class attributes and initialisation mutates a
global data structure. Each subprocess re-asserts the imported tree and aborts if it is wrong.

Phase A adds a **cached harvest**: one instrumented baseline run per scenario saves `(x, y0)` at
every `call_models` to disk, so the harvest is paid once rather than per arm, and a **1-in-5
subsample of `grad` points** (all `fn` and `grad_reconcile` kept). 94.5 % of points are gradient
perturbations and A19 §5.2 established they behave no differently.

Writes `runs/<scenario>/<arm>/<rep>/metrics.json`. `runs/` stays untracked.

**Trap T7:** ten models call `run()` from `output()`. The replay must call the *unwrapped* bound
methods captured before instrumentation.

### 2.8 C6 — Gate library

| Gate | Predicate |
|---|---|
| **Neutrality** | arm-off vs a pristine `git archive` of `c0ae5b28`, on hex float literals plus whole-MFILE identity |
| **Determinism** | two runs of one arm agree bit-for-bit and sweep-for-sweep |
| **Solves** | `ifail = 1` on every scenario |
| **Correctness** | `norm_objf` to a stated tolerance **plus** a post-solve feasibility audit — never iteration variables (D6) |
| **Matched accuracy** | *new* — the C9 exit audit: all arms terminate at a comparable global residual, verified per design point |
| **Robustness** | `ifail`, retries, sub-solve non-convergence census, drop census, starting-point sensitivity |

A1's `compare.py` implements the first three at the required strength.

### 2.9 C8 — DSM node map

A checked-in mapping model attribute -> DSM row -> module, generated from the dependency analysis
at `PROCESS_at_36ac820e` and committed as data. VP1, VP2, VP4 and C9 all need it, and it must not
be four hand-written lists that drift apart.

**The map is stable, so the check is small.** It is generated from the same pin the tree descends
from, and it maps *model attribute -> row -> module* — a mapping VP1 does not disturb, because
reordering the call sequence does not change which module a node belongs to. So this needs a
three-line assertion, not a validation subsystem.

**The assertion is `observed nodes are a subset of mapped nodes`, not equality.** Per V6 the map is
**configuration-specific**: a map generated for the tokamak deck names nodes that do not execute in
every scenario — `Pulse` writes nothing under `i_pulsed_plant = 0`, and `models.tfcoil.run()` is
reached in none of the four decks. An equality check would fail on correct runs. A node observed
that the map does not name is the real error, and that is what to raise on.

### 2.10 C10 — DSM validation reporting · *new*

The framework computes the coupling set two ways (C9): from the probe, and from the DSM. **Any
disagreement is a finding about the DSM, not a nuisance**, and the project has already accumulated
three T1 false positives plus two dead back edges that a naive reading would have counted.

Every such finding gets an entry in
[`../reports/DSM_VALIDATION.md`](../reports/DSM_VALIDATION.md) — the edge, the evidence, whether
the DSM is wrong or the instrument is, and the consequence. That report is **not** archived at
merge; it accumulates across tasks and is a deliverable to the dependency-analysis study.

---

## 3. Implementation impact

### 3.1 Build order

| Step | Work | Half | Status |
|---|---|---|---|
| **F11** | **C9 fixed-point engine** + `harvest` probe mode + cached harvest and subsample | **Phase A** | **build now** — the whole comparison |
| **F4** | C8 node map + subset assertion | Phase A | **build now** — small |
| **F12** | C10 DSM validation register | Phase A | **open** (`reports/DSM_VALIDATION.md`) |
| F1 | consolidate three probe modules to one `_experiment.py`, pure file-merge | shared | approved, **after** Phase A — not a blocker |
| F2 | C4 registry table + append 178 | Phase B | when a lift is run |
| F6 | correctness + robustness gates | Phase B | needs a solve |
| F7a / F7b | VP1 / VP2 hooks in `caller.py` | Phase B | with their consumers |
| F8 / F10 | VP3 / VP4 hooks in `caller.py` | Phase B | **only if** Phase A's findings are carried into production (open question 4) |
| F5 / F9 | `note_subsolve`; VP5 pattern + constraint layer | Phase B | **unqueued** — specified, not scheduled |
| F3 | C7 timing protocol | context | metadata fields only; the rest is a recipe |

**F11 + F4 is the minimum before Phase A runs**, with F12 as a reporting obligation rather than
code. Everything else waits for a task that consumes it.

### 3.2 Where the code lives

| Path | Content | PROCESS touched |
|---|---|---|
| `arch_surgery/fixedpoint/engine.py` | C9: Gauss-Seidel, predicate, caps, exit audit | no |
| `arch_surgery/fixedpoint/arms.py` | R / A0 / A1 construction from the node map | no |
| `arch_surgery/fixedpoint/ystate.py` | `y` extraction, norm, exclusion list | no |
| `arch_surgery/docs/data/dsm_node_map.json` | C8 | no |
| `process/core/_idf_probe.py` | one new `harvest` mode — **no new hook site** (§1.4) | yes — mode-gated, existing file |
| `process/core/_experiment.py` | F1 consolidation of the three probe modules — *after* Phase A | yes — bit-identity gate |
| `process/core/caller.py` | VP1-VP4 hook sites | yes — neutrality-gated |
| `process/core/solver/{iteration_variables,constraints}.py` | C4 appends | yes |
| `process/models/*.py` | VP5 residual extraction | yes — **D11 approval before merging** |

### 3.3 Two invariants the framework must enforce

**Baseline costs nothing.** With `PROCESS_ARCH` unset, no hook allocates, branches in a hot path,
or touches a float. A1 established the current probe satisfies this by whole-MFILE identity; every
new hook clears the same bar before its task proceeds. A framework that perturbs the baseline
invalidates every experiment simultaneously.

**Every arm is neutral until selected.** Adding VP5's `subsolve` wrapper to a model must not change
results with the site unlifted. This is what allows model-touching work to proceed under D11, and
it is checked by the neutrality gate on every arm, not argued once.

---

## 4. Expected results

The framework produces no experimental result of its own. What each step unlocks:

| Step | Capability delivered | Without it |
|---|---|---|
| F1 | arms are identifiable in every artifact | results cannot be attributed to a configuration |
| F4 | one authoritative node -> row -> module map | four lists drift apart silently |
| **F11** | **the entire Phase A comparison** | the partition cannot be measured without editing PROCESS |
| F12 | DSM errors accumulate as findings | each is rediscovered, as T1 already was three times |
| F6 | matched-accuracy verification | sweep-count comparisons are unsound |
| F2 | lifting is possible at all | I-7 blocks every lifting task |
| F7a/F7b/F8 | VP1/VP2/VP3 in production | Phase A's findings cannot be carried into the running code |
| F9 | one implementation serves A4 and A9-A11 | two separate builds, two registry claims |
| F10 | VP4 in production | Phase B has no partition arm |

**The cheapest useful milestone is F1 + F4 + F11.** It yields the reference-arm result — how much
of today's sweep count is the two-sweep artefact, and how often the incumbent loop stops with the
state still moving — with no `process/` edits and no approval gate.

---

## 5. Critical assessment

### 5.1 Over-building audit — what to cut, and what Phase A actually needs

The variant-point model is a good *description* of the driver's degrees of freedom. It is a bad
*build list*, and reading it as one is how this document reached ten hooks and twelve build steps
for a portfolio with one live experiment. The audit:

**Phase A needs three things. Not twelve.**

| Needed | Why |
|---|---|
| **One new probe mode** (`harvest`) | saves `(x, y0)` per `call_models` |
| **C9, the fixed-point engine** | the entire comparison, in `arch_surgery/` |
| **C8, the node map** | the block arm's module boundaries |

Everything else in §2 is Phase B or unqueued. Specifically:

**Cut now — `PROCESS_ARCH` arm composition (part of C1).** The comma-separated arm parser exists to
let two behaviour-changing arms run together. Exactly one composition is known to be needed —
VP2 with VP5, the C2a case — and it is in Phase B. **Phase A selects its arms in the harness, not
in PROCESS**, because R / A0 / A1 all live in `arch_surgery/`. The existing single-mode switch
(`PROCESS_IDF_PROBE=<mode>`, which A1, A2 and A19 each extended) already covers everything Phase A
does. Build the parser when the first real composition is run.

**Defer entirely — C3 / F9, the VP5 pattern.** It is the largest single piece in the document and
**no queued task consumes it**. A4 is Phase B; A9-A11 belong to the subdriver experiment, which is
not queued. It also carries the only `process/models/` edits in the portfolio, hence the only D11
approval burden. Nothing is lost by leaving it specified and unbuilt.

**Defer — VP3, VP4 and `note_subsolve` hooks in production (F8, F10, F5).** VP3 and VP4 in
`caller.py` are only needed **if** Phase A's findings are carried into the running code, which is
open question 4 and not yet decided. Building them first is building for a hypothesis. Phase A
exercises both concepts entirely outside PROCESS.

**Shrink — C6, the "gate library".** A1's `compare.py` already does neutrality, determinism and
solves. Of the three additions: **matched-accuracy is not a gate, it is the engine's exit audit**
and belongs inside C9; correctness (`norm_objf` + feasibility) and robustness need a *solve*, so
they are Phase B. There is no library to build for Phase A.

**Shrink — C7, the timing protocol.** Already demoted. With counts primary the only parts earning
their place are the metadata fields, which cost nothing to record, and the rule refusing to quote a
comparison whose intervals overlap. Interleaved-arm scheduling and the thread-pinning precondition
are real work that **no live gate depends on**. Keep them as a recipe for the day a timing matters.

**Optional, and not a blocker — F1, the probe consolidation.** Three task-specific probe modules
(A1's, A2's, A19's, 1 594 lines) have accreted in `process/core/`, and merging them to one
`_experiment.py` is approved (user, 2026-09-01) on condition it is bit-identical in output with
negligible runtime cost. But **the harvest mode does not require it** — it can be a fourth mode in
the existing module. Scope F1 as a **pure file-merge with a bit-identity gate**, not as
"generalise to arm parsing", and run it *after* Phase A rather than before, so a working instrument
set is not refactored on the critical path.

**What remains a genuine risk after all that**

- **The `y` exclusion list** is the most dangerous artifact in the design: a hand-maintained list
  that can make every arm declare a convergence that has not happened, with no symptom. Mitigation
  is not architectural — it is that each exclusion is measured and justified in the report, and the
  DSM-derived cross-check set runs in parallel to catch a coupling variable wrongly excluded.
- **Composed arms are untested combinations.** C2a is the worked example of a defect visible in
  only one composition. Any combination used in a result is gated explicitly. This is a reporting
  rule, and costs nothing until Phase B.

### 5.2 What this framework deliberately does not do

- **No settings knobs.** `epsfcn`, `epsvmc`, FD step floors and the retry ladder are tuning, not
  architecture. Exposing them here would invite an architectural claim built on a tuning change.
- **No acceleration.** Aitken/Anderson on the fixed point is architecture by this project's own
  filter and would be a legitimate variant point — but it is not in Phase A, because it would
  confound with the topology change.
- **No stellarator or IFE arms.** Both take an early return in `_call_models_once`.
- **No automatic composition testing.** Composability is a convenience, not a licence to report an
  untested combination.

### 5.3 The timing protocol is demoted, and that is the right call

Under D13 the primary metric is a **count**. Timings are context, reported with their interval and
repetition count, never evidence. So C7 is no longer on the critical path — F3 sits at the bottom
of the build order.

What survives from it, because it costs nothing: interleave arms and take paired differences rather
than running all-A then all-B; record CPU time, load, available memory, a **content hash** and the
run's position in its sequence in every `metrics.json`; discard the first run in a fresh
environment for JIT; refuse to emit a timing comparison whose intervals overlap.

**Thread pinning is not adopted and must not be adopted casually.** Every gate here is bit-identity,
and multi-threaded BLAS can change the reduction order of a dot product or a QP solve — a different
summation order is a different last bit. The Stage-0 baseline was cut unpinned. **Precondition:**
run one scenario pinned and unpinned and compare hex floats. Bit-identical means pinning is free;
different means the baseline must be re-cut and every existing figure carries a footnote.

**I-10 remains open.** Identical work varies up to 35 % in CPU-seconds on this machine. Scheduling
contention is retired (both this project and the sibling run at ~1 core on 16); memory pressure is
now also retired (our peak RSS is 423 MB, the sibling's heaviest 0.47 GB, against a 7 GB ceiling).
Remaining candidates: frequency scaling, cache/memory-bandwidth effects, the WSL2 layer. **A
mechanism has been eliminated, not identified** — which is exactly why counts lead.

---

## 6. Open questions

1. **VP4 and VP5 interact, and the framework must not pre-empt the answer.** Post-partition a
   lifted residual has two possible hosts — the module's own solver or the global optimiser. In
   Phase A a third exists: an outer fixed-point loop. `subsolve` must be able to target any of
   them, so the choice stays an experimental variable.
2. **Does `note_subsolve` need to distinguish per-coil from per-conductor invocations**, or is a
   per-site count enough for A9's gate?
3. **A1's retry hooks have never executed.** Verified by inspection only — does the framework need
   a fault-injection arm to exercise them, or is that over-building?
4. **Does Phase A's predicate get carried into production at all** (F8), or does it stay a
   measurement instrument? That depends on what Phase A finds about the strict predicate's cost.
