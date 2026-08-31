# Subdriver-lift experiment — plan

**Status:** draft, not started, **blocked on a decision** (§3.4) · **Base commit:** `c0ae5b28`
· **Branch:** task branches off `architecture_surgery`

**Relationship to the other experiment.** This is a *second, separate* architecture change,
independent of [`MDA_PARTITION_EXPERIMENT.md`](../MDA_PARTITION_EXPERIMENT.md). Both alter the
driver, so they must be **sequenced, never run in parallel** — see §3.5.

---

## 1. The hypothesis

> PROCESS contains various subdrivers — root-finders nested inside model evaluations. Lifting
> their residuals to the optimiser, focusing on those that call another function (easiest to
> extract), should improve runtime, because nested loops should be avoided.

Testable claims:

| | Claim | Status |
|---|---|---|
| **H1** | There are subdrivers nested inside the MDA that take a callback residual | **Supported** — four confirmed, one rejected (§2) |
| **H2** | Their residuals can be lifted to the optimiser as design variables plus equality constraints | Plausible; §3.4 raises a scope conflict first |
| **H3** | Lifting reduces runtime | **Doubtful as the primary claim** (§3.1) |
| **H4** | Lifting improves finite-difference gradient quality | **Untested, and the stronger claim** (§3.2) |
| **H5** | Lifting improves robustness and makes failure auditable | **Partly established already** by inspection (§3.3) |

---

## 2. The subdrivers, as found

Enumerated by inspection at `c0ae5b28`. Each is a root-find taking a callback, nested inside a
model evaluation, therefore inside the outer finite-difference stencil.

| # | Site | Method | Unknown | Residual | Tolerance | On failure |
|---|---|---|---|---|---|---|
| **S1** | [`vacuum.py:460`](../../../process/models/vacuum.py#L460) `_newton_method_duct_diameter` | hand-rolled Newton, `for _ in range(100)`, inside an outer `while True` that rescales `ceff *= 0.9` | duct diameter | `_newton_function` | **`dd <= 0.01`** — 1 % relative | logs an error and **continues with the unconverged value** |
| **S2** | [`pfcoil.py:4909`](../../../process/models/pfcoil.py#L4909) | `optimize.newton` (secant, `x1` given), `maxiter=50` | temperature at zero margin | `superconductors.superconductor_current_density_margin` | `tol=1e-6`, `rtol=1e-6` | **`disp=False`** — returns silently unconverged |
| **S3** | [`tfcoil/superconducting.py:1267`](../../../process/models/tfcoil/superconducting.py#L1267) | `optimize.newton` (secant), `maxiter=50` | temperature at zero margin | **the same function as S2** | `tol=1e-6`, `rtol=1e-6` | **`disp=True`** — raises |
| **S4** | [`superconductors.py:282`](../../../process/models/superconductors.py#L282) `current_sharing_rebco` | `optimize.newton` (secant), `maxiter=50` | current-sharing temperature | `jcrit_rebco(T,B) − j` | `tol=1e-6`, `rtol=1e-6` | `disp=True` — raises |

### 2.1 A candidate rejected — read this before adding others

[`confinement_time.py:1160`](../../../process/models/physics/confinement_time.py#L1160) looks
like the *best* candidate in the codebase:

```python
return root_scalar(fhz, bracket=(0.01, 150), xtol=0.001).root
```

A bracketed Brent solve on the H-factor, over a bracket spanning four orders of magnitude, at
an absolute tolerance of `1e-3`, whose residual `fhz(hfact)` re-runs the entire
`calculate_confinement_time` scaling with ~20 arguments. Loose tolerance, expensive residual,
and it sits in Module 1 of the partition analysis.

**It is not in the MDA.** Its only caller is `find_other_h_factors`, whose only caller is
`output_confinement_comparison` — a reporting method that iterates over confinement scalings
and writes a comparison table to the output file, once, after the solve. It never enters the
finite-difference stencil and lifting it would change nothing.

This is the second time this exact trap has been hit (issue **I-4**, raised when
`physics.b_plasma_vertical_required` looked like a feedback edge and turned out to be read in
`PlasmaFields.output()`). **Every candidate must be confirmed to lie on a `run()` path before
it is counted.** Stage 1 does this by measurement, not by reading.

---

## 3. Critical assessment

### 3.1 The runtime claim is the weakest part of the hypothesis

"Nested loops should be avoided to improve runtime" is a reasonable prior in general, but the
arithmetic here is unfavourable, for a reason specific to this codebase.

**What lifting removes** is a handful of evaluations of a *scalar* residual — `jcrit_rebco`,
a current-density margin, a duct-diameter update. A secant iteration converges in roughly 5–15
evaluations of a cheap function.

**What lifting costs** is `k` design variables and `k` equality constraints. Gradient cost
scales as `n + k + 1`, and `n` is only **14–20** in these scenarios. Lifting four residuals is
therefore roughly a **+20–29 % increase in gradient cost**, paid on every optimiser iteration.

Contrast the partition experiment, where lifting **one** variable eliminates whole sweeps of a
56-node sequence: there, `k = 1` buys a large structural saving. Here, `k = 4` buys the removal
of some scalar iterations. **The break-even condition is that the nested solvers currently
consume more than ~25 % of wall clock.** That is measurable before any refactor is written —
just time them — and it is the first thing this experiment should do. My expectation is that
they do not, and that H3 is false.

There is a second-order effect that could rescue it: `S2`/`S3`/`S4` are called **per coil and
per conductor**, so their aggregate count may be much larger than "one solve per model call".
Stage 1 must count, not assume. But the burden of proof sits with H3.

### 3.2 The strong argument is gradient quality, and the hypothesis omits it

A root-find with a finite exit tolerance makes the enclosing model a **piecewise** function of
its inputs. Perturb an input by the finite-difference step, and the inner solver may take a
different number of iterations and land on a different side of its tolerance — so the model
output jumps by roughly the inner tolerance, discontinuously, for an arbitrarily small input
change. That jump enters the outer finite-difference quotient divided by the FD step, and
appears as **noise in the constraint Jacobian**.

This is finding **F14** in the architecture evaluation ("root-finders inside the FD stencil"),
and it is where the payoff actually is:

- **S1's tolerance is 1 % relative.** Against a relative FD step of order `1e-3`, a 1 % jump in
  the duct diameter is not a perturbation of the derivative — it is larger than the signal.
- S2–S4 are at `1e-6`, so their contribution should be small — **which is itself a testable
  prediction**: if lifting only S2–S4 changes the Jacobian materially, something other than the
  exit tolerance is going on.

Lifting converts the model into an exact algebraic function of (inputs, lifted unknown), and
the finite-difference derivative becomes exact in that direction. **Reframe the experiment
around this.** Runtime becomes a secondary measurement that may well be negative, and the
result is still publishable: *"lifting nested solves buys gradient accuracy at a quantified
cost in problem dimension"* is a real architectural finding. A runtime-only framing risks
producing a null result and calling it a failure.

### 3.3 Three defects are already visible, and they are a deliverable

Found by inspection, before any measurement:

1. **The same residual is solved with two different failure policies.** `pfcoil.py:4909` passes
   `disp=False` — on non-convergence `optimize.newton` **returns the unconverged iterate
   silently**. `tfcoil/superconducting.py:1267` calls the *same function*
   (`superconductor_current_density_margin`) with the same tolerances and `disp=True`, which
   raises. One of these is wrong; nothing in the code says which.
2. **`vacuum.py` continues on non-convergence.** The `for … else` logs an error and then
   proceeds with whatever `d[i]` the loop left behind — the outer `while True` carries on using
   it.
3. **The tolerances span four orders of magnitude with no stated rationale** — `1e-2` relative
   (S1), `1e-6` (S2–S4) — and the rejected candidate in §2.1 uses `1e-3` absolute on a quantity
   whose bracket spans `0.01–150`.

Lifting replaces all three with something auditable: an equality constraint the optimiser must
satisfy, whose residual is reported in the output and whose violation is visible rather than
silent. That is an architectural argument that does not depend on any timing result.

### 3.4 This conflicts with the model freeze — a decision is required first

**Decision D5 states that the models are frozen and only the driver changes.** That is what
separates this study from `functional_PROCESS`. Lifting a subdriver requires editing files
under `process/models/` — `vacuum.py`, `pfcoil.py`, `superconducting.py`, `superconductors.py`
— to expose the residual and accept the previously-solved unknown as a parameter.

Two readings, and the user must choose:

- **Narrow (current D5):** any edit under `process/models/` is a model change, so this
  experiment is out of scope as written. It would have to wait for the `functional_PROCESS`
  back-end, where the residuals are already explicit.
- **Refined:** the *residual expressions* are frozen — the physics is untouched — while the
  *method by which a residual is driven to zero* is architecture, and moving it from an inner
  Newton to an outer constraint is exactly the independent variable this project studies.

The refined reading is defensible and, I think, correct: `jcrit_rebco(T,B) − j = 0` is the same
equation whoever solves it. But it materially widens what "only the driver changes" licenses,
and a reviewer will press on it, so it should be an explicit recorded decision rather than an
assumption. **This plan cannot start until that is settled.**

A mitigation that keeps the narrow reading nearly intact: make each lift a **pure refactor plus
a switch** — extract the residual into a function, leave the inner solve as the default path,
and lift only when an environment switch is set. Then the frozen configuration is provably
byte-identical to upstream (the same switch-neutrality gate the probe uses), and the diff
under `process/models/` is mechanical.

### 3.5 Sequencing against the partition experiment

The two experiments overlap on surface and on subject. S2 sits in `pfcoil` (Module 2); S3 and
S4 sit in the TF-coil models (Module 2); S1 sits in `vacuum` (Module 3). Running both at once
changes two independent variables and makes neither attributable.

**Sequence:** the partition experiment completes through its Stage 3 (or is stopped at its
Stage 1 gate) before this one starts. This experiment then measures against whatever the
partition left as the new baseline, and says so explicitly. If the partition is abandoned at
its gate, this experiment measures against the Stage-0 baseline instead.

There is one genuine interaction worth stating in advance: **if the partition succeeds, the
inner solvers are called fewer times** (fewer sweeps), which *reduces* the runtime prize here
further while leaving the gradient-quality prize untouched — another reason to lead with §3.2.

---

## 4. Experiment design

### Stage L0 — Confirm and count (read-only, no refactor)

Extend the Stage-0 probe to instrument every candidate site.

1. **Confirm each site is on a `run()` path**, by counting invocations during an optimisation
   run rather than by reading call graphs (§2.1, I-4).
2. **Count and time**: invocations per `call_models`, iterations per invocation, wall clock
   attributable to the nested solves, as a fraction of total.
3. **Record non-convergence**: how often `maxiter` is hit; how often `pfcoil.py`'s
   `disp=False` path returns unconverged; how often `vacuum.py` logs and continues.
4. **Sweep the candidate list** for any site missed by inspection.

**Gate.** This decides the framing, and is cheap enough to be worth doing even if the
experiment stops here.
- Nested solves are **> 25 %** of wall clock → H3 is live; keep runtime as a primary claim.
- **5–25 %** → runtime is secondary; lead with gradient quality (§3.2).
- **< 5 %** → **H3 is refuted.** Report it as a measured negative and continue only on the
  gradient-quality and robustness case, with the plan rewritten accordingly.

Any non-convergence observed in (3) is a **finding reportable immediately**, independent of
everything downstream.

### Stage L1 — Extract residuals behind a switch

For each confirmed site: extract the residual into a named function taking `(unknown,
inputs)`; leave the existing inner solve as the default path; add an env-switched branch that
instead reads the unknown from the lifted design vector.

**Gate.** With the switch unset, results **bit-identical** to Stage L0. This is the mechanism
that keeps §3.4's narrow reading nearly intact, and it is non-negotiable.

### Stage L2 — Lift one residual

Start with the site with the **loosest tolerance and the highest call count** from L0 — on
current evidence that is **S1 (`vacuum`, 1 % relative)**, but L0's counts decide.

Add one design variable and one equality consistency constraint. Measure:
- **Gradient quality** — the primary result. Compare the constraint Jacobian against a
  high-accuracy reference (Richardson-extrapolated or complex-step where the code permits) at a
  fixed point away from the optimum and at the optimum. This is where §3.2 predicts a win.
- **Runtime** at matched final accuracy, reporting the `n → n+1` dimension cost separately from
  the saving, so the two are not netted into an uninterpretable single number.
- **Correctness** — `norm_objf` agreement plus a post-solve feasibility audit (D6). Never
  iteration variables.
- **Robustness** — `ifail`, retries, and whether previously-silent non-convergence now shows up
  as constraint violation.

**Gate.** Measurable Jacobian improvement, correctness held, no robustness regression. A
runtime regression is **acceptable here** if the gradient result is positive — but it must be
stated, not buried.

### Stage L3 — Lift the remainder, incrementally

Add S2, S3, S4 one at a time, re-measuring after each. `k` rises one at a time so the
dimension penalty is attributable per lift rather than in aggregate.

**Stop rule.** Stop at the `k` where the marginal Jacobian improvement no longer justifies the
marginal dimension cost, and report that `k` as the result. "How far is it worth lifting" is a
more useful finding than "lift everything".

### Stage L4 — Resolve the failure-policy inconsistency

Independent of the lift: determine whether `disp=False` at `pfcoil.py:4909` is deliberate.
Report as a PROCESS finding — architecture critique here, implementation defect to
`PROCESS_code_analysis/docs/bug_reports/` if it turns out to be a plain bug.

---

## 5. Measurement protocol

Inherits the standing protocol: fresh subprocess and working directory per run; discard the
first run for timing; compare at matched final accuracy; gate correctness on `norm_objf` plus
feasibility, never on iteration variables (D6).

**Additional for this experiment — the Jacobian reference.** The primary result is gradient
accuracy, so it needs a trustworthy reference derivative. Establish it once, at L0, and state
its own error bound; a "gradient improvement" measured against an equally noisy reference is
not a result.

---

## 6. Threats to validity

| Threat | Handling |
|---|---|
| Runtime saving is smaller than the dimension penalty | Predicted (§3.1); L0's gate decides the framing before any refactor |
| Candidate is on an `output()` path, not in the MDA | L0 confirms by invocation counting, not by reading (§2.1, I-4) |
| The lift is really a model change (D5) | Blocking decision (§3.4); switch-gated extraction keeps the frozen path byte-identical |
| Confounding with the partition experiment | Strict sequencing (§3.5); baseline named explicitly in every result |
| Jacobian reference is itself noisy | Reference established and error-bounded at L0 |
| Equality constraints make the problem harder to start | Measured as robustness; `ifail` and retries reported per stage |
| Lifted unknowns need bounds the inner solver supplied implicitly | Brackets/initial estimates in the current code (`0.01–150`, `x0`, `x1 = 2·x0`) are the starting point for bounds |

---

## 7. Open questions

1. **Does the refined reading of D5 hold?** Blocking — §3.4.
2. What fraction of wall clock do the nested solves actually consume? L0 answers it and it
   determines whether H3 survives.
3. Is `disp=False` at `pfcoil.py:4909` deliberate, given the identical call at
   `superconducting.py:1267` uses `disp=True`?
4. Are S2/S3/S4 called per coil, per conductor, or once — i.e. is the aggregate count large
   enough to matter?
5. Does `vacuum.py`'s unconverged-continue path ever trigger in the four scenarios?
