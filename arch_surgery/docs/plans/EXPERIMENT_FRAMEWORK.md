# Experiment framework — implementation master plan

> **Document status** — CURRENT · design for the shared harness · last revised 2026-08-31.

**Status:** design, not built — proposed as **A18 (experiment-framework)**. A1
(stage0-rebaseline) has already delivered the parts marked *(built, A1)* below: the probe module,
its four measurement hooks, the run harness and the first three gates. · **Base commit:**
`c0ae5b28` · **Owns:** the shared code both architecture experiments run on

This document specifies the code to build **before** running either experiment. It is not an
experiment plan — [`MDA_PARTITION_EXPERIMENT.md`](MDA_PARTITION_EXPERIMENT.md),
[`SUBDRIVER_LIFT_EXPERIMENT.md`](SUBDRIVER_LIFT_EXPERIMENT.md) and
[`ARCHITECTURE_EXPERIMENT_CANDIDATES.md`](ARCHITECTURE_EXPERIMENT_CANDIDATES.md) are those. This
is the harness they share.

---

## 1. The organising idea: variant points, not code edits

Every experiment in the portfolio is a **different value at one of five variant points** in the
driver. Once that is true, an experiment stops being a patch to `caller.py` and becomes a
configuration — which is what makes arms composable, neutrality provable, and results
attributable.

| VP | Where | Baseline behaviour | Variants (task) |
|---|---|---|---|
| **VP1 — sequence** | `_call_models_once` | the hand-written call order | `Build` moved (A3); DSM-sequenced order (A15, *deferred*) |
| **VP2 — loop membership** | `call_models` | every node runs every sweep | feed-forward tail hoisted out — **live**, folded into the partition as its Stage 1b (D12) |
| **VP3 — convergence predicate** | `call_models` | agreement on objective + constraints | agreement on coupling variables (A14, *deferred*) |
| **VP4 — loop topology** | `call_models` | one global fixed-point loop | per-module solvers over M1/M2/M3 (A5) |
| **VP5 — lifted unknowns** | models + solver | inner root-find | unknown from the design vector, residual as a constraint (A4, A9–A11) |

Two things fall out of this table that were not obvious when the experiments were planned
separately:

- **A4 (burn-time lift) and A9–A11 (subdriver lift) are the same mechanism.** Both are VP5: expose
  a residual, take the unknown from the design vector, add an equality constraint. They differ
  only in *which* residual. One implementation serves both, and the subdriver experiment stops
  being a separate build.
- **The two experiments are separable in code even though they interact in measurement.** The
  partition is VP1–VP4; the subdriver lift is VP5. Disjoint surfaces, one shared registry.

**Design rule.** A variant point is a branch on configuration, evaluated once per run, never a
per-call `if` in a hot path. Baseline must cost nothing — see §3.

---

## 2. Components to build

### C1 — `process/core/_experiment.py` (extends A1's `_idf_probe.py`)

The single module holding arm configuration and all hook state. A1 built this as a probe; it
generalises to the harness.

Responsibilities: parse the active arm set from the environment once at import; expose
`ENABLED` and per-variant-point selections as module-level constants; hold the measurement
counters; provide the hook functions. No PROCESS imports beyond data structures, so it can be
imported from anywhere in `process/core/` without a cycle.

**Arm selection.** One environment variable, a comma-separated set, so arms compose:

```
PROCESS_ARCH=baseline                       # instrumented, no behaviour change
PROCESS_ARCH=seq:dsm,hoist                  # VP1 + VP2 together
PROCESS_ARCH=partition,lift:t_plant_pulse_burn
```

Unset ⇒ every hook is a no-op and behaviour is byte-identical to upstream. Every arm's identity,
resolved value and the tree's git HEAD go into each run's `metrics.json` — a result that cannot
say which arms produced it is not a result.

### C2 — Hook points

A fixed, minimal set. Adding a hook is a framework change and needs its own neutrality check;
experiments must not add hooks ad hoc.

| Hook | Site | Serves |
|---|---|---|
| `call_models_begin/end` | `caller.py` | measurement (built, A1) |
| `sweep_begin/end` | `caller.py` | measurement (built, A1) |
| `phase(...)` | `solver/evaluators.py` | fn / grad / grad_reconcile attribution (built, A1) |
| `note_retry()` | `solver/solver_handler.py` | retry census (built, A1 — **never fired**, so verified by inspection only) |
| `model_sequence()` | `_call_models_once` | VP1 |
| `in_loop(node)` | `call_models` | VP2 |
| `converged(state_prev, state)` | `call_models` | VP3 |
| `solve_blocks(...)` | `call_models` | VP4 |
| `subsolve(residual, x0, …)` | each VP5 site | VP5 |
| `note_subsolve(site, iters, converged)` | each VP5 site | robustness census (A9) |

`note_subsolve` is **read-only and independent of VP5** — it is how A9 (subdriver-count) measures
failure incidence without extracting anything, and it should land first.

### C2a — The feed-forward set is dynamic, not a constant

**`in_loop(node)` must be a function of the active arm set.** `Pulse` (DSM row 39) is inside the
fixed-point loop while `times.t_plant_pulse_burn` is unlifted, and becomes a pure feed-forward
node once VP5 lifts it — A2 §6.2 and the partition plan §2.3a establish this from its two state
writes. So a hoist arm that hard-codes the feed-forward node list would be **wrong in exactly one
configuration**: VP2 combined with VP5.

The framework must therefore derive the set from `(DSM node map, active arms)` at run time and
record the resolved set in `metrics.json`. A hard-coded list is a latent defect that only fires
when two arms compose, which is the hardest kind to notice.

### C3 — The VP5 pattern

One pattern, applied identically at every lifted residual, so the diff under `process/models/` is
mechanical and reviewable:

1. Extract the residual into a module-level function `f(unknown, *inputs) -> float`. **Pure
   refactor** — the expression is unchanged, satisfying D5's reading that the physics is frozen.
2. Replace the inline solve with `_experiment.subsolve(f, x0, args, site="...")`, which by default
   performs *exactly* the original call with the original tolerances and failure policy.
3. When the site is lifted, `subsolve` instead returns the value from the design vector and
   records the residual for the constraint layer.

**Measured consequence (A19):** the burn-time lift is **not separable** — `max Sᵢ` is unchanged to
four decimals when the coupler is pinned, so lifting alone buys nothing without VP4. VP5 must be
measured *with* the partition, never as a standalone arm claiming a saving. The feed-forward hoist
is the opposite and is separable; do not generalise from one to the other.

Step 2 must be **provably inert**: `subsolve`'s default path is the original call, so the frozen
arm is byte-identical. That is what keeps the model freeze intact and is the reason the
extraction is worth doing even if nothing is ever lifted.

### C4 — Registry allocation (D10)

New iteration variables and constraints are **appended, never fitted into gaps**.
`N_ITERATION_VARIABLES_MAX` is derived (`max(ITERATION_VARIABLES.keys())`), so appending key 178
raises it automatically and every array sized by it grows; `lablxc` self-populates from the
registry. There are 94 gaps in 1–177 and reusing one would silently reinterpret an existing
`IN.DAT`.

`arch_surgery/docs/plans/REGISTRY_ALLOCATIONS.md` is the single allocation table — every task
takes its numbers from there, in one place, so two branches cannot both claim 178.

**Consequence to state in the write-up:** once `ixc = 178` validates here and not upstream, the
fork's input language has diverged. Inherent to lifting anything; not a blocker.

### C5 — Run harness (extends A1's `run_stage0.py` / `run_one.py`)

Scenario × arm × repetition matrix. Fresh subprocess and working directory per run — mandatory,
because `OutputFileManager` holds file handles as class attributes and initialisation mutates a
global data structure. Each subprocess re-asserts the imported tree and aborts if it is wrong
(A1 built this; keep it even now that the environment is fixed).

Writes `runs/<scenario>/<arm>/<rep>/metrics.json`. `runs/` stays untracked.

### C6 — Gate library

Five reusable gates, so no task hand-rolls one:

| Gate | Predicate |
|---|---|
| **Neutrality** | arm-off vs a pristine `git archive` of `c0ae5b28`, on hex float literals plus whole-MFILE identity |
| **Determinism** | two runs of one arm agree bit-for-bit and sweep-for-sweep |
| **Solves** | `ifail = 1` on every scenario |
| **Correctness** | `norm_objf` agreement to a stated tolerance **plus** a post-solve feasibility audit — never iteration variables (D6) |
| **Robustness** | `ifail`, retries, sub-solve non-convergence census, starting-point sensitivity |

A1's `compare.py` already implements the first three at the required strength; correctness and
robustness are new.

### C7 — Timing protocol (closes I-8)

**A1 measured a worst within-arm wall-clock spread of 19.6 % at `n = 5`, while the partition plan
gates on 25 % and stops below 10 %.** Single-run timings are not measurements, and at that spread
a 10 % effect is not resolvable at all.

**Most of this is probably contention, not the code.** The machine has 16 cores but **7 GB of
RAM**, no thread-pinning variables are set (so every process defaults OpenBLAS to all 16 cores),
and other sessions run concurrently. Two mechanisms fit: BLAS oversubscription when processes
overlap, and page-cache eviction under memory pressure perturbing numba cache loads. Supporting
evidence: A1's 2 SE band on the *difference* between arms was 3–9 % against a 19.6 % marginal
spread, which is the signature of **common-mode** noise.

The protocol therefore attacks the difference, not the absolute:

1. **Interleave the arms and take paired differences.** Run `A,B,A,B,…` rather than all-A then
   all-B, and difference within each pair. Blocked ordering lets a slow period bias one arm
   entirely; interleaving turns drift into common-mode noise that cancels. **This is the single
   highest-value change** — the gates care about the ratio between arms, not absolute time.
2. **Pin threads, identically across arms** — `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`,
   `MKL_NUM_THREADS=1`, `NUMBA_NUM_THREADS=1` — **but test before adopting.** This is *not* a free
   knob. The Stage-0 baseline was cut under the current unpinned defaults, and every gate here is
   **bit-identity**; multi-threaded BLAS can change the reduction order of a dot product or QP
   solve, and a different summation order is a different last bit. PROCESS's solver path runs
   through `scipy.optimize.fsolve` and pyvmcon's QP, so LAPACK/BLAS is plausibly in it.
   **Precondition:** run one scenario pinned and unpinned and compare hex floats. Bit-identical ⇒
   pinning is free, take it. Different ⇒ the baseline must be re-cut under the pinned
   configuration and every existing figure carries a footnote. Cheap to test, expensive to
   assume — and the answer is needed *before* the timing protocol depends on it.
   *(Raised by the `PROCESS_code_analysis` orchestrator, 2026-08-31, declining to move the same
   lever under its own regression baseline. The argument transfers.)*
3. **Record CPU time alongside wall clock** (`resource.getrusage`). This is a **diagnostic, not
   just a mitigation**: process CPU time is far less sensitive to other processes' scheduling, so
   if the CPU-time spread is much narrower than the wall-clock spread, contention is confirmed as
   the cause. If both are equally wide, the variance is in the code and the machine is exonerated.
   **Run this diagnostic before investing in the rest of the protocol** — it decides whether the
   problem is worth solving this way.
4. **Record load average and available memory in every `metrics.json`**, so a contaminated run can
   be flagged or excluded after the fact rather than silently averaged in.
4b. **Record a content hash and the run's position in its sequence.** Timings are only comparable
   across *identical* content, and the confound is easy to miss: a sibling project's three
   descending quiet samples looked like a settling trend until it emerged that the third ran on a
   branch with ~100 files of prose deleted — lighter import work, not a faster machine. Without a
   content hash in the record, that error is invisible after the fact.
5. Choose `n` from a target minimum detectable effect, not by habit; variance is not uniform
   across scenarios, so a per-scenario `n` is cheaper than a uniform one. Discard the first run in
   a fresh environment (numba JIT).
6. Refuse to emit a timing comparison whose intervals overlap — report "indistinguishable".

Sweep and model-evaluation counts stay the primary mechanism diagnostic: they are exact and
reproduce bit-for-bit, so they carry the mechanism while wall clock carries the headline with its
interval attached.

### C8 — DSM node map

A checked-in mapping from PROCESS model attribute → DSM row → module, generated from the
dependency analysis at `PROCESS_at_36ac820e` and committed as data. VP1, VP2 and VP4 all need it,
and it must not be three hand-written lists that drift apart.

**It must be validated at run time**, not trusted: A1's `st_regression` failure is the standing
example of an archived artifact silently going stale against the tree.

---

## 3. Two invariants the framework must enforce

**Baseline costs nothing.** With `PROCESS_ARCH` unset, no hook allocates, branches in a hot path,
or touches a float. A1 established the current probe satisfies this by whole-MFILE identity;
every new hook must clear the same bar before its task proceeds. A framework that perturbs the
baseline invalidates every experiment simultaneously.

**Every arm is neutral until selected.** Adding VP5's `subsolve` wrapper to a model must not
change results with the site unlifted. This is what allows model-touching work to proceed under
D5's freeze, and it is checked by the neutrality gate on every arm, not argued once.

---

## 4. Build order

| Step | Work | Why here | Blocks |
|---|---|---|---|
| **F1** | Rename/extend `_idf_probe.py` → `_experiment.py`; arm parsing; arm identity into `metrics.json` | Everything keys off arm selection | all |
| **F2** | C4 registry allocation table + append 178 as the first entry (proves the mechanism) | Cheap; unblocks every lifting task | A4, A9–A11 |
| **F3** | C7 timing protocol into the harness | I-8 makes current timings unreportable | every timing claim |
| **F4** | C8 DSM node map, with run-time validation | VP1/VP2/VP4 all need it | A2, A13, A15 |
| **F5** | `note_subsolve` census hook (read-only) | Lets A9 measure failure incidence with no extraction | A9 |
| **F6** | C6 correctness + robustness gates | Needed before any behaviour-changing arm | A3 onward |
| **F7a** | VP1 hook (`model_sequence`) | Needed by A3 (build-reorder), Stage 2 of the partition | A3 |
| **F7b** | VP2 hook (`in_loop`) — **arm-dependent, not a constant set** | The partition's Stage 1b needs it; the node set changes with the arms (see below) | partition Stage 1b |
| ~~F8~~ | ~~VP3 hook (`converged`)~~ | Consumer A14 deferred | *(deferred)* |
| **F9** | VP5 pattern + constraint layer | The largest piece; serves A4 and A9–A11 together | A4, A9–A11 |
| **F10** | VP4 (`solve_blocks`) | Largest architectural change; wants everything else settled | A5 |

F1–F6 are framework-only: no behaviour changes, so they merge under the neutrality and
determinism gates alone. **F1–F3 are the minimum before any further experiment runs**, because
without them arms are unidentifiable and timings unreportable.

**Scope note (revised 2026-08-31, D12).** The partition experiment is authorised to proceed and
the feed-forward hoist is folded into it, so the live path is **F1–F6, F7a, F7b, F9, F10**.
E2–E5 remain deferred; only E1 has been absorbed. VP2 and VP3 remain in the variant-point
model because they are what makes it a complete account of the driver's degrees of freedom, but
their hooks are built with their consumers, not now. Building an unused hook would mean carrying
a neutrality obligation for a variant nobody is testing.

---

## 5. What this framework deliberately does not do

- **No settings knobs.** `epsfcn`, `epsvmc`, FD step floors and the retry ladder are tuning, not
  architecture, and are out of scope (portfolio §4). Exposing them here would invite an
  architectural claim built on a tuning change.
- **No stellarator or IFE arms.** Both take an early return in `_call_models_once`; the whole
  portfolio is tokamak-only.
- **No automatic arm composition testing.** Arms compose mechanically, but any *combination* used
  in a result must be gated explicitly. Composability is a convenience, not a licence to report
  an untested combination.

---

## 6. Open questions

1. **VP4 and VP5 interact, and the framework must not pre-empt the answer.** Post-partition a
   lifted residual has two possible hosts — the module's own solver or the global optimiser
   (portfolio §2.4). `subsolve` must be able to target either, so the choice stays an experimental
   variable rather than being hard-coded now.
2. Does `note_subsolve` need to distinguish per-coil from per-conductor invocations, or is a
   per-site count enough for A9's gate?
3. A1's retry hooks have **never executed** in any run. They are verified by inspection only —
   does the framework need a fault-injection arm to exercise them, or is that over-building?
