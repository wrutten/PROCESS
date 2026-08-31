# Sequencing comparison — plan (OUT OF SCOPE)

**Status:** **OUT OF SCOPE for this repository** (user, 2026-08-31). Not started, not queued.
Retained for its assessment, which stands.

**Verdict.** The comparison as originally proposed — count fixed-point iterations in PROCESS
against `functional_PROCESS` and infer runtime from the un-iterated source fraction — would not
have supported its conclusion: outer iteration counts hide the nested Newton/Picard work inside
`functional_PROCESS`'s scheduled blocks, asymmetrically favouring the sequenced arm, and
sequencing was perfectly confounded with the rewrite.

**Why it left this repository rather than being fixed.** §3.4 established that the only clean
control — unstructured versus scheduled, same models, same back-end, same precision — lives
*inside* `functional_PROCESS`. Once that is true, PROCESS is no longer the counterpart but a
third, external reference arm. The user's conclusion follows directly and goes one step further:
**if the experiment has to be built inside `functional_PROCESS` anyway, then architectures should
simply be implemented there directly**, rather than staged as a cross-implementation comparison.

So the question is live; its home is the `functional_PROCESS` programme, not this one. It was
also always outside decision D5's model freeze, which is a second reason it does not belong here.

**What to carry across if it is ever picked up there:** count model-node evaluations rather than
outer iterations (§3.2); weight by measured per-model cost, never by source size (§3.5); sample
`x` including finite-difference-perturbed points, since 94–96 % of PROCESS's sweeps are
perturbations and those converge less readily (§3.6); and state the boundary between an
MDA-convergence result and a full-optimisation runtime claim (§3.7).

---

## 1. The proposal

> PROCESS's dependency graph is not accurate enough to re-sequence its call order safely — doing
> so would mean chasing bugs and rewriting models. But `functional_PROCESS` **is** sequenced and
> produces validated-equivalent results. Full optimisation runtime is incomparable because of the
> JAX back-end. So: implement a fixed-point iterator to converge `call_models` once in PROCESS,
> implement the same iterator over an equivalent model set in `functional_PROCESS`, use no JAX
> gradients, and compare **iteration counts**. Expect far fewer for the sequenced case, then infer
> a runtime comparison from the fraction of the source not iterated over in the sequenced case.

---

## 2. What `functional_PROCESS` actually is — and why it changes the design

The proposal assumes `functional_PROCESS` is a *sequence* that a fixed-point iterator can be
wrapped around. It is not. From `functional_process/mda.py` and `core/solver/drivers.py`:

- `indat.GRAPH` is decomposed by `cottax.blocking.Blocking` into **strongly connected
  components**, then run under a `Schedule`.
- Most SCCs already declare their own problem (`FixedPointFunction`/`ImplicitFunction` self-loop
  pairs, the coil island's `Intersect`). Raw cross-node cycles that declare no problem are **cut**
  into declared `FixedPoint` problems via `FixedPointCut`, using `Graph.closing_readers` plus an
  empirical check that the cut set actually breaks the cycle.
- **Every block then gets its own driver by problem type** — `NewtonDriver` for `RootFind`,
  `PicardDriver` for `FixedPoint`, `VmconDriver` for the single `Optimise`.

So `functional_PROCESS` is **a schedule of many small solvers**, not a sequence. There is no
single outer loop whose iterations you could count. "Number of iterations to converge" is not
well-defined for it without saying *which* loop, and any outer count would exclude all the
nested Newton and Picard work inside the blocks.

Two other facts, both favourable:

- **JAX x64 is enabled** (`jax.config.update("jax_enable_x64", True)`, with an explicit note that
  PROCESS is float64 throughout). The float32 precision trap is already closed.
- `mda.py` imports **`Undrive`**, so drivers can be removed from blocks. §3.4 turns on this.

---

## 3. Critical assessment

### 3.1 What is right about the idea

**Rejecting wall clock is correct.** Comparing a Python/numba implementation against a JIT-compiled
JAX one on time would measure the back-ends, not the architecture. Choosing a structural unit is
the right instinct and it is what makes any comparison possible.

**Using `functional_PROCESS` as the sequenced arm is the real insight.** The objection to
re-sequencing PROCESS directly is well founded — the DSM is a static approximation, `F4` records
that the code itself admits ordering changes results, and A1 has already shown how an archived
artifact goes stale against the tree. Borrowing an implementation where the sequencing has already
been *derived and validated* buys the sequenced arm without paying for it in bug-chasing.

**Excluding JAX gradients is right.** Including them would confound sequencing with automatic
differentiation, which is a separate and much larger effect.

### 3.2 As stated, the comparison is not fair — iteration count is not a common unit

This is the flaw that would invalidate the conclusion.

One PROCESS "iteration" is one sweep: **every model evaluated once**. One `functional_PROCESS`
outer step is a pass over the schedule — but each block inside it runs its own Newton or Picard
loop to convergence. **Counting outer steps moves work out of the count and into the blocks**, and
it does so asymmetrically: only the sequenced arm gets to hide work that way. The sequenced arm
would look better by construction, whatever the truth.

This is the same failure mode PROCESS's own `nviter` has — it under-reports evaluations, which is
why A1's probe counts sweeps instead. Repeating it across implementations would be worse, because
there is no cross-check.

**Fix: count model-node evaluations, not iterations.** Instrument both arms to count how many
times each individual model function is invoked to reach the fixed point, inner solves included.
That is a genuine common unit, it is exact rather than timed, and it is what the runtime inference
needs anyway. Iteration counts can still be reported as a mechanism diagnostic; they cannot carry
the conclusion.

### 3.3 Sequencing and the rewrite are perfectly confounded

Any difference between the two arms could come from the sequencing — or from the rewrite. Different
intermediate expressions, different residual formulations, reassociated arithmetic (the port's own
`_harness/tolerance.py` discusses "float64 round-off from a reassociated expression"), different
starting guesses (`SUPPLIED_STARTS`). Nothing in the proposed design separates these.

Validated equivalence does **not** rescue this. Equivalence says the two arms land in the same
place; it says nothing about how many evaluations each takes to get there, which is exactly the
dependent variable.

### 3.4 The fix, and it makes this a much better experiment

**Run the control inside `functional_PROCESS`.** `mda.py` already imports `Undrive`. Assemble two
arms from the *same* code:

- **Arm U (unstructured):** undrive the blocks and wrap the whole graph in a single global
  `FixedPoint` with `PicardDriver` — one flat Gauss-Seidel over everything, the structural analogue
  of PROCESS's `call_models`.
- **Arm S (scheduled):** the port as it stands — SCC blocking, cuts, per-block drivers.

Same models, same back-end, same precision, same tolerance, same starting guesses. **The only
difference is structure.** That comparison isolates sequencing cleanly, and it does not depend on
the equivalence argument at all.

PROCESS then becomes a **third, external reference arm** rather than the counterpart: the question
it answers is *"does PROCESS's global loop behave like Arm U?"* If it does, Arm S versus Arm U
transfers to PROCESS. If it does not, that discrepancy is itself the finding — and it would say
the rewrite, not the sequencing, is doing the work.

This is a strictly stronger design than the two-arm version and costs one extra assembly.

### 3.5 "Fraction of source code not iterated over" will not support the inference

Lines of code are a poor proxy for runtime. One CoolProp call, one `scipy` root-find or one
quadrature dominates thousands of lines of arithmetic; A1's own measurements show cost is
concentrated in ways source size does not predict.

**Fix:** measure per-model cost once on the PROCESS side — wall time per model evaluation, profiled
directly — then weight the evaluation counts from §3.2 by it. That turns the inference from a
hand-wave into arithmetic, and the weights are reusable by every other experiment here.

### 3.6 Converging at one point is not representative

A1 measured that **94–96 % of PROCESS's sweeps are finite-difference gradient perturbations**, and
that perturbed points are systematically harder to reconcile than the points VMCON visits — 47–53 %
of `fn` calls finish at the two-sweep floor against only 12–20 % of `grad` calls.

So a comparison performed at the initial point measures the easy case, and the ratio there need not
hold where nearly all the work is. **Sample `x` across a representative set — the initial point, a
near-optimal point, and perturbed points at the FD step — and report a distribution, not a single
ratio.**

### 3.7 What conclusion this can actually license

If §3.2's counting and §3.4's control are in place, the defensible claim is:

> *At these design points, the scheduled formulation reaches the same fixed point in **k×** fewer
> cost-weighted model evaluations than the unstructured one, over the same models and back-end.*

That is a real result and it is the cleanest available isolation of sequencing as a variable —
precisely **because** stripping out the back-end and the gradients is what makes the arms
comparable.

What it does **not** license is a runtime claim for the full optimisation. Converging one MDA at
fixed `x` is not the optimisation: the optimiser's own iteration count may differ between
formulations, gradient quality differs, FD cost scales with `n`, and the JAX back-end is excluded
by construction. **State that boundary explicitly in the write-up**, because "sequencing gives k×"
will otherwise be read as a runtime claim, and a reviewer will hold you to the reading you did not
intend.

There is also a scope limit worth stating plainly: this measures **one particular sequencing** —
the cuts `functional_PROCESS` chose, which its own docstrings say were *measured, not chosen*. It
is evidence about that decomposition, not about sequencing in general.

### 3.8 The equivalence claim needs a stated margin

"Validated equivalent" must be pinned down: to what tolerance, on which scenarios, on which
outputs. If equivalence holds at ~1e-6 and the fixed-point convergence test is also 1e-6, the two
are at the same scale and the comparison sits inside its own noise. **The equivalence margin must
be tighter than the convergence tolerance**, or the gap must be reported as an error bar on `k`.

---

## 4. Experiment design

### Stage Q0 — Common counting instrument

Add a model-node evaluation counter to both arms: PROCESS (extend the A1 probe) and
`functional_PROCESS` (count invocations per graph node, inner driver iterations included). Verify
on a case with a known answer that the two counters mean the same thing.

**Gate.** On a single non-iterated model, both counters report exactly 1. Without this, nothing
downstream is comparable.

### Stage Q1 — Per-model cost weights

Profile per-model wall time on the PROCESS side, warm, repeated per the timing protocol (I-8).
Produces the weight vector §3.5 needs.

**Gate.** Weights stable across repetitions; report the spread. A weight with an interval wider
than the differences it is meant to resolve is not usable.

### Stage Q2 — Arm U versus Arm S, inside `functional_PROCESS`

The core measurement, and the one that does not depend on cross-implementation equivalence.
Assemble the undriven global-fixed-point arm and the scheduled arm; converge both to the same
tolerance from the same starts; count weighted model evaluations at a sampled set of `x` (§3.6).

**Gate.** Both arms reach the same fixed point to a stated tolerance — otherwise they are not
solving the same problem and the counts are meaningless.

### Stage Q3 — PROCESS as external reference

Converge PROCESS's `call_models` at the same `x` with the same tolerance, counting the same way.

**Question answered:** does PROCESS's global loop behave like Arm U? Agreement transfers Q2's
result to PROCESS. Disagreement is the finding — it locates the difference in the rewrite rather
than the structure, which is worth knowing and is not currently known.

### Stage Q4 — Report

The bounded claim of §3.7, with its distribution over `x`, its cost weights, its equivalence
margin, and its scope limits stated in the same breath as the number.

---

## 5. Threats to validity

| Threat | Handling |
|---|---|
| Outer iteration counts hide nested solver work | Count model-node evaluations, inner iterations included (§3.2) |
| Sequencing confounded with the rewrite | Arm U vs Arm S inside one codebase (§3.4); PROCESS as external reference only |
| LOC as a cost proxy | Measured per-model weights (Q1) |
| Single design point unrepresentative | Sample `x`, including FD-perturbed points; report a distribution (§3.6) |
| Equivalence margin at the same scale as the convergence tolerance | Margin stated and required tighter, else reported as an error bar (§3.8) |
| Result read as a full-optimisation runtime claim | Boundary stated explicitly in §3.7 and repeated in the write-up |
| Conclusion generalised beyond one decomposition | Scope limited to `functional_PROCESS`'s measured cuts |
| Different starting guesses between arms | `SUPPLIED_STARTS` held identical across arms, or the difference reported as a factor |

---

## 6. Open questions

1. Can the whole graph actually be assembled as one global `FixedPoint` with every block undriven,
   or do some SCCs refuse to run without their declared problem? `Drive.__check_init__` rejects a
   block that "declares no problem", so Arm U may need every block wrapped rather than merely
   undriven. **This determines whether §3.4's control is available**, and it is the first thing to
   check.
2. Does Arm U converge at all? An unstructured Picard over the full graph may diverge where
   PROCESS's hand-ordered sweep converges — which would itself be a strong result about the value
   of the ordering, but it would end the counting comparison.
3. Is `functional_PROCESS`'s model set identical in scope to PROCESS's `_call_models_once`, or does
   it cover a subset? Any difference must be reported as a coverage caveat on `k`.
4. What is the actual equivalence margin, on which scenarios (§3.8)?
