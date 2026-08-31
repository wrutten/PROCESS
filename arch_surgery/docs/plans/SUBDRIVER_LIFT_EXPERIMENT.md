# Subdriver-lift experiment — plan

> **Document status** — CURRENT · plan for a live but blocked experiment · last revised
> 2026-08-31.

**Status:** not started, **no longer blocked**. **D11 (2026-08-31) rules** that minimal structural
edits under `process/models/` are permitted — extracting a residual is licensed, changing what a
model computes is not — **with every change requiring the user's approval before merging**. §3.4's
open question is resolved in favour of the refined reading; the switch-gated extraction it
recommends remains the right mechanism, now as good practice rather than as a workaround. **Not** blocked by I-7, which
was downgraded once the iteration-variable cap turned out to be derived rather than hand-set;
numbers are allocated append-only from
[`REGISTRY_ALLOCATIONS.md`](REGISTRY_ALLOCATIONS.md) (D10). · **Base commit:** `c0ae5b28`

**Relationship to the other experiment.** This is a *second, separate* architecture change,
independent of [`MDA_PARTITION_EXPERIMENT.md`](../MDA_PARTITION_EXPERIMENT.md). Both alter the
driver, so they must be **sequenced, never run in parallel** — see §3.5.

---

## 1. The hypothesis

> PROCESS contains various subdrivers — root-finders nested inside model evaluations. Lifting
> their residuals to the optimiser, focusing on those that call another function (easiest to
> extract), should make the code **more robust**: a nested solve that fails does so silently and
> locally, whereas a lifted residual becomes an equality constraint the optimiser must satisfy
> and the user can audit. Runtime is a secondary question and the dimension penalty is expected
> to be real.

Testable claims, primary first:

| | Claim | Status |
|---|---|---|
| **H1** | Nested solves fail — hit `maxiter`, return unconverged, or raise — during ordinary runs, and those failures are currently invisible | **Partly established by inspection** (§3.1); incidence unmeasured |
| **H2** | Lifting converts a silent local failure into a visible constraint violation, so failure becomes attributable | **Untested — the primary result** |
| **H3** | Lifting removes a discontinuity from the finite-difference stencil, improving Jacobian quality | **Untested — the secondary result** (§3.2) |
| **H4** | The dimension penalty (`n → n+k`) is affordable | **Must be measured, expected adverse** (§3.3) |
| **H5** | Net runtime improves | **Doubtful** (§3.3); measured and reported, but not the reason to do this |

**Framing.** This experiment is about **robustness first**, gradient quality second, and runtime
third. A result of "more robust, more auditable, and 15 % slower" is a success. A runtime-led
framing would have to call that a failure, which is why it is not the framing.

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

### 3.1 The robustness case is already half-made, before any measurement

Three defects are visible by inspection:

1. **The same residual is solved with two different failure policies.** `pfcoil.py:4909` passes
   `disp=False` — on non-convergence `optimize.newton` **returns the unconverged iterate
   silently**, and the caller uses it as though it were a root. `tfcoil/superconducting.py:1267`
   calls the *same function* (`superconductors.superconductor_current_density_margin`) with the
   *same tolerances* and `disp=True`, which raises. One of these is wrong; nothing in the code
   says which, and the two produce opposite behaviour on the same numerical failure.
2. **`vacuum.py` continues on non-convergence.** The `for … else` logs an error and then the
   enclosing `while True` proceeds with whatever `d[i]` the loop left behind. A logged error is
   not a gate; the run completes and reports a number.
3. **Tolerances span four orders of magnitude with no stated rationale** — `1e-2` relative (S1),
   `1e-6` (S2–S4) — and the candidate rejected in §2.1 uses `1e-3` absolute on a quantity whose
   bracket spans `0.01–150`.

What is *not* yet known is how often any of this fires in practice. That is Stage L0, it is
read-only, and it is the first deliverable.

**Why lifting helps.** A lifted residual becomes an equality constraint. Non-convergence stops
being a local event inside a model — invisible, policy-dependent, sometimes silent — and becomes
a **constraint violation the optimiser reports and the user can see in the output**. That is a
genuine architectural improvement and it does not depend on any timing result. It also removes
the `disp=True`/`disp=False` divergence by construction: there is one policy, and it is the
optimiser's.

**The honest counter-argument.** Lifting does not make a badly-conditioned residual well
conditioned. If `superconductor_current_density_margin` is hard to solve, it is hard whether the
secant method or VMCON drives it — and VMCON must now satisfy it *simultaneously* with 82
other constraints, from a starting point that may be far from its root. It is possible that
lifting converts a rare silent local failure into a frequent visible global one. **That would
still be a result** — it would say the nested solves are load-bearing — but it must be measured
rather than assumed away, and it is the reason Stage L2 lifts exactly one residual first.

### 3.2 Gradient quality — the secondary case

A root-find with a finite exit tolerance makes the enclosing model a **piecewise** function of
its inputs. Perturb an input by the finite-difference step and the inner solver may take a
different number of iterations, landing on a different side of its tolerance, so the model
output jumps by roughly the inner tolerance for an arbitrarily small input change. That jump
enters the outer difference quotient divided by the FD step, and appears as noise in the
constraint Jacobian. This is finding **F14** of the architecture evaluation.

- **S1's tolerance is 1 % relative.** Against a relative FD step of order `1e-3`, the jump is
  larger than the signal.
- S2–S4 are at `1e-6`, so their contribution should be small — **a testable prediction**: if
  lifting only S2–S4 moves the Jacobian materially, something other than the exit tolerance is
  at work.

### 3.3 The performance penalty is real and must be measured, not hidden

Lifting costs `k` design variables and `k` equality constraints. Gradient cost scales as
`n + k + 1`, and `n` is only **14–20** in these scenarios, so lifting four residuals is roughly
a **+20–29 % increase in gradient cost**, paid every optimiser iteration.

What lifting saves is a handful of evaluations of a *scalar* residual — a secant iteration
converges in roughly 5–15 cheap evaluations. Break-even needs the nested solves to be consuming
more than ~25 % of wall clock, which Stage L0 measures directly.

Two further pressures on the runtime side, both worth stating in advance so a negative result is
not a surprise:

- **The partition experiment shrinks this prize.** If the MDA partition succeeds, the inner
  solvers are called fewer times, so there is less nested-solve time to reclaim — while the
  robustness and gradient prizes are untouched.
- **`k` may be larger than 4.** S2–S4 may be invoked per coil and per conductor; if the lift has
  to be per-invocation rather than per-site, `k` grows and the penalty with it. Stage L0 counts.

**Reporting rule.** The dimension penalty and the nested-solve saving are reported as two
separate numbers, never netted into one. A single "net runtime" figure hides which mechanism did
what, and the two move independently as `k` changes.

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

**Gate — on failure incidence, not on time.**
- **Any** non-convergence observed in ordinary runs → the robustness case is live; proceed, and
  report the incidence immediately as a standalone finding.
- **Zero** non-convergence across all four scenarios → widen the search before proceeding: scan
  starting points and scenario variants, since a defect that never fires in four decks may still
  fire in a user's. If it still never fires, the robustness case rests on *auditability* alone
  (silent-by-construction versus visible-by-construction) and the plan should say so plainly
  rather than implying a failure rate it has not measured.

Wall-clock share is recorded at the same time, and sets expectations for §3.3's penalty
reporting — but it does not gate this experiment.

### Stage L1 — Extract residuals behind a switch

For each confirmed site: extract the residual into a named function taking `(unknown,
inputs)`; leave the existing inner solve as the default path; add an env-switched branch that
instead reads the unknown from the lifted design vector.

**Gate.** With the switch unset, results **bit-identical** to Stage L0. This is the mechanism
that keeps §3.4's narrow reading nearly intact, and it is non-negotiable.

### Stage L2 — Lift one residual

Start with the site with the **highest measured failure incidence** from L0; where incidence
ties, prefer the loosest tolerance and highest call count. On current evidence that points at
**S1 (`vacuum`, 1 % relative, continues on non-convergence)**, but L0's counts decide.

Add one design variable and one equality consistency constraint. Measure:
- **Robustness — the primary result.** Does a previously-silent non-convergence now appear as a
  constraint violation? Run a **starting-point sensitivity scan**: perturb `x0` across a spread
  of feasible starts and count, for baseline versus lifted, how many runs fail, how many fail
  *visibly*, and how many complete carrying an unconverged inner value. The headline is the
  shift from silent failure to attributable failure.
- **Gradient quality** — secondary. Compare the constraint Jacobian against a high-accuracy
  reference (Richardson-extrapolated, or complex-step where the code permits) at a point away
  from the optimum and at the optimum.
- **Performance** — measured and reported as **two separate numbers**: the `n → n+1` dimension
  cost, and the reclaimed nested-solve time. Never netted.
- **Correctness** — `norm_objf` agreement plus a post-solve feasibility audit (D6). Never
  iteration variables.

**Gate.** Robustness improves or is neutral, and correctness holds. **A runtime regression does
not fail this gate** — it is a reported cost. What fails the gate is a robustness regression
(more failures, or failures that are still silent) or a correctness break.

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

1. ~~Does the refined reading of D5 hold?~~ **Resolved by D11** — it does, with an approval gate.
2. What fraction of wall clock do the nested solves actually consume? L0 answers it and it
   determines whether H3 survives.
3. Is `disp=False` at `pfcoil.py:4909` deliberate, given the identical call at
   `superconducting.py:1267` uses `disp=True`?
4. Are S2/S3/S4 called per coil, per conductor, or once — i.e. is the aggregate count large
   enough to matter?
5. Does `vacuum.py`'s unconverged-continue path ever trigger in the four scenarios?
