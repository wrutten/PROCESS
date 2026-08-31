# Architecture experiment candidates — portfolio and interference

**Status:** proposal · **Base commit:** `c0ae5b28`

Candidates for further architecture experiments, subject to three filters:

1. **Inferable from the DSM.** The change is motivated by the dependency structure, not by
   numerical taste.
2. **Architecture, not settings.** Changing `epsfcn`, `epsvmc`, an FD step floor or a retry
   ladder is tuning; changing *what iterates, in what order, converging on what* is
   architecture.
3. **Minimally invasive.** Ideally confined to `process/core/caller.py` and
   `process/core/solver/` — no edits under `process/models/`, so decision D5's model freeze
   holds without needing a ruling.

Sources: [`../reports/PROCESS_architecture_evaluation.md`](../reports/PROCESS_architecture_evaluation.md)
(findings F1–F14, C1) and the collapsed and sequenced DSMs.

---

## 1. Ranked candidates

### E1 — Hoist the feed-forward tail out of the MDA · *strongly recommended*

**DSM basis.** Nodes in no strongly connected component do not feed back, yet the idempotence
loop re-runs them on every sweep. From the collapsed DSM: `CsFatigue` (38) and rows 52–55
(`WaterUse`, `Costs`, `Objective`, `Constraints`), plus whatever else the SCC decomposition
finds outside the cycles — the plant accounting tail is the obvious candidate.

**Change.** In `call_models`, run the feed-forward nodes **once, after** the fixed point is
reached, rather than inside the loop. Pure `caller.py`.

**Why it is attractive.** This is the `|all|` term of the partition experiment's speedup
mechanism, available **without partitioning anything**. If the loop averages `S` sweeps, hoisting
`h` feed-forward nodes saves `(S−1)·h` model evaluations per `call_models` for a change of a few
lines and no new design variables — no dimension penalty at all. It is the cheapest
performance experiment in the portfolio.

**Risk.** Small but real: a node believed feed-forward that in fact writes something an upstream
model reads would silently change results. The gate is exact agreement with baseline on
`norm_objf` and the full MFILE, which catches it.

**Interaction.** Overlaps the partition experiment's mechanism (it is the same saving), so the
two must not be measured together — see §2. It also overlaps E2 below: hoisting `Objective` and
`Constraints` out of the loop is only possible once the loop stops converging *on* them.

### E2 — Converge the coupling variables, not the objective and constraints · *high value, higher risk*

**DSM basis.** Finding **F3**. `call_models` converges on `objf` and `conf`
([caller.py:73–137](../../../process/core/caller.py#L73)) — the functionals — rather than on the
coupling variables `y` that the DSM's feedback edges identify. Coupling variables that do not
move `f` or `c` by `rtol` are declared converged, but the finite-difference stencil differences
exactly `f` and `c`, so residual variation in `y` invisible to the test is **precisely** what
pollutes the gradient.

**Change.** Replace the convergence predicate with agreement on the coupling-variable set, and
move objective and constraint evaluation out of the loop to after it. Pure `caller.py` plus
whatever names the coupling set — which task A2 (module-convergence) produces as a by-product.

**Why it is attractive.** The architecture evaluation calls this Tier 3, and it is the one Tier-3
item that needs **no model changes and no new design variables**. It fixes the convergence
variable and the F/C-inside-the-MDA problem in a single change, and it is squarely "architecture,
not settings".

**Risk.** The convergence criterion changes meaning, so sweep counts are not comparable to
baseline without care — converging `y` to `1e-6` is a *different and generally stricter*
standard than converging `f` and `c` to `1e-6`. Expect more sweeps, and judge on gradient
quality and robustness rather than on sweep count. This is the standing "matched final accuracy"
rule in its sharpest form.

**Prerequisite.** A2 (module-convergence) must have produced the coupling-variable set.

### E3 — Re-sequence the call order from the sequenced DSM · *cheap, and it subsumes A3*

**DSM basis.** The instrument already emits `dsm_collapsed_sequenced.html` — a sequencing that
minimises feedback. The executed order in `_call_models_once` is a hand-written sequence that
does not match it, which is how `Build` (DSM row 5, Module 2) comes to run at position 4 inside
Module 1's span.

**Change.** Reorder the `self.models.X.run()` calls to the sequenced DSM's order. Pure
`caller.py`, pure reordering, no logic touched.

**Note.** **A3 (build-reorder) is the single-node special case of this.** If E3 is adopted, A3
should be folded into it rather than run separately — otherwise two tasks reorder the same
sequence and neither result is attributable.

**Why it is attractive.** It tests finding **F4** directly. The code carries a comment admitting
ordering matters — *"These two methods need to be run after vacuum/buildings otherwise output
changes quite a lot"* — which is an architectural defect stated in a `TODO`. Sequencing is the
classic DSM intervention and this is the cleanest instance of it in the codebase.

**Risk.** Unlike A3's single move, a full re-sequence is **not** expected to be result-neutral —
the F4 comment says as much. So the gate cannot be bit-identity; it has to be `norm_objf`
agreement plus a feasibility audit, and any changed result must be explained by a named edge.
That makes it a more demanding task than it first looks.

### E4 — Convergence-predicate audit · *read-only, do it early*

**DSM basis.** Finding **F12**. `MDA_Idempotence` converges on objective and constraints;
`MDA_Output` converges on successive MFILEs, variable by variable. Same word, two predicates,
same system, both capped at 10 iterations at `rtol = 1e-6`. **A run can satisfy one and not the
other, and only the second is reported to the user.**

**Change.** None. Instrument both predicates and measure how often they disagree, and by how
much, across the four scenarios.

**Why it is attractive.** Zero invasion, robustness-relevant, and it either produces a finding or
retires a suspicion. It also directly informs E2: if the two predicates routinely disagree, the
choice of convergence variable is demonstrably load-bearing rather than theoretical.

### E5 — Fixed-count inner iterations in the tokamak path · *read-only scan*

**DSM basis.** Finding **F11** — unrolled iteration with a fixed count and no convergence test,
nested inside a converged loop. The evaluation found this in the stellarator path, which is out
of scope. **Whether the tokamak path contains the same pattern is unchecked.**

**Change.** None — a scan for repeated calls to the same model within one sweep, or loops with a
literal trip count where a convergence test would be expected.

**Why it is attractive.** Cheap, and it either extends the subdriver-lift candidate list or
bounds it. Naturally folded into A9 (subdriver-count).

---

## 2. Do the two planned experiments conflict?

**Yes — in four places, three of which are avoidable with a convention, and one of which is a
genuine open design question.**

### 2.1 Shared registries — the concrete collision

Both experiments mint new optimiser entities in the same two files:

- `process/core/solver/iteration_variables.py` — `ITERATION_VARIABLES`, a number-keyed dict;
  `N_ITERATION_VARIABLES_MAX` is derived from `max(keys)`.
- `process/core/solver/constraints.py` — 82 constraints registered as
  `@ConstraintManager.register_constraint(<n>, …)`.

The MDA partition needs **1** of each (`t_plant_pulse_burn`); the subdriver lift needs **up to
4** of each. Developed on separate branches, both will take the next free numbers, collide at
merge, and — worse — produce **different numberings on each branch**, so an `IN.DAT` written for
one is silently misinterpreted by the other. That is a data-corruption-shaped failure, not a
merge conflict.

**Fix:** reserve disjoint ranges in the queue before either starts, the same way `A<n>`, `D<n>`
and `I-<n>` are administered. Recorded in `MASTER_TODO.md`.

### 2.2 Confounded dimension penalties

Both raise `n`. Gradient cost scales as `n + k + 1` at `n = 14–20`, so both pay a penalty from
the same budget. Measured together, neither is attributable. **Fix:** strict sequencing, and each
experiment reports its own `k` and its own penalty separately (already the reporting rule in
both plans).

### 2.3 Baseline drift

If the partition merges first, the subdriver experiment's baseline is no longer Stage 0. **Fix:**
every result names its baseline commit explicitly. Cheap, but it has to be a habit from the
start.

### 2.4 The real conflict: where does a lifted residual go?

This one is not administrative.

The subdriver sites lie **inside** the partition's modules — S2 (`pfcoil`) and S3/S4 (TF coil)
are in Module 2; S1 (`vacuum`) is in Module 3. The subdriver plan was written against the
current monolithic MDA, where there is exactly one place to lift a residual to: the global
optimiser.

**After the partition there are two**, and they are different architectures:

- **Lift to the module's own solver.** The residual is local to Module 2, so Module 2's solver
  drives it. `n` is unchanged — no dimension penalty at all — and the coupling stays local.
- **Lift to the global optimiser.** `n` rises by `k`, VMCON sees the constraint, and the residual
  is satisfied only at the optimum rather than at every module solve.

These have different robustness properties (a module solver failing is still a local failure;
the global optimiser reports it) and different costs (the first is free in dimension, the second
is not). **The subdriver plan currently assumes the second without arguing for it**, because when
it was written the first did not exist.

**This is not a blocker — it is a dependency.** If the partition succeeds, the subdriver
experiment gains a second arm and becomes a *comparison* (local solver versus global constraint),
which is a better experiment than the one currently planned. If the partition is stopped at its
Stage 1 gate, the question never arises and the current plan stands.

**Therefore: the partition experiment resolves first.** Not merely for sequencing hygiene — its
outcome changes what the subdriver experiment is.

### 2.5 What does *not* conflict

`caller.py` is touched only by the partition experiment (and by E1–E3); the subdriver lift does
not go near it. The `process/models/` edits are touched only by the subdriver lift. So the file
surfaces are largely disjoint; the collisions are in the two solver registries and in the
measurement design, not in the bulk of the code.

---

## 3. Recommended order

| Order | Work | Why here |
|---|---|---|
| 1 | **A1 (stage0-rebaseline)** | Everything needs the baseline |
| 2 | **E4 (convergence-predicate audit)**, **E5 (fixed-count scan)** | Read-only, no branch contention, informs E2 and A9 |
| 3 | **A2 (module-convergence)** | Gating measurement; also produces the coupling set E2 needs |
| 4 | **E1 (feed-forward hoist)** | Cheapest performance result in the portfolio; no dimension penalty |
| 5 | **A3/E3 (sequencing)** — fold A3 into E3 | One reordering, one attributable result |
| 6 | **A4–A5 (partition)** *or* stop at A2's gate | Resolves §2.4 either way |
| 7 | **E2 (converge y)** | Needs A2's coupling set; large change, wants a settled baseline |
| 8 | **A9–A11 (subdriver lift)** | Framing depends on §2.4's resolution |
| — | **A12 (subdriver-failure-policy)** | Independent; runnable at any time |

Note that E1, E4 and E5 need **no ruling on D5** — they touch no model code — so they are
available immediately while A9–A11 remain blocked.

---

## 4. Explicitly excluded

The architecture evaluation's **Tier 2** items — raise `epsfcn`, loosen `epsvmc`, add an FD step
floor, record the successful FD step — are **settings, not architecture**, and are out of scope
by filter (2). They are worth doing and probably cheaper than anything here, but they belong in a
tuning study where they cannot be confused with an architectural result. The **retry ladder**
(F5, F7) is the same category.

**Analytic or AD derivatives** (Tier 3) is the change that would actually remove F2, and the
evaluation's own summary is that *"derivatives are the bottleneck, not the architecture"* — but
it requires touching every model and is squarely outside D5.
