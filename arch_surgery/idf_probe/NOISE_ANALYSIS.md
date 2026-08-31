> **Document status** — **SUPERSEDED · STALE**
> The gradient-noise study of the abandoned IDF experiment, measured at commit **`710a75c9`**.
> Not rederived at `c0ae5b28`; its figures are not evidence for anything in this repository
> (decision D4). The script that produced it, `noise_probe.py`, has not been run against this tree.
> Retained because the finite-difference-noise argument it develops is the basis of the subdriver
> lift's secondary case
> ([`../docs/plans/SUBDRIVER_LIFT_EXPERIMENT.md`](../docs/plans/SUBDRIVER_LIFT_EXPERIMENT.md) §3.2).

# Why the measured FD gradient noise in PROCESS was (almost) zero

**Subject:** reconciling "gradient error = 0.0" with the fact that PROCESS's models are full of
branches, clamps, table lookups and inner Newton solves.
**Study commit:** `main` @ `710a75c9`, probe instrumentation `process/core/_idf_probe.py` (env-gated,
`PROCESS_IDF_PROBE`). **Scenario:** `large_tokamak_nof` (n = 20, m = 26, `epsfcn` = 1e-3).
**Env:** conda `PROCESS_env`, Python 3.14.3. Every run in a fresh subprocess.
**New evidence:** `noise_deepdive.py`, outputs under `runs/noise_deepdive/`.

The short version: the earlier probe measured a real effect, but it measured *one* mechanism, at
*two* points, and reported it in a normalisation that inflated the worst case by four orders of
magnitude and reduced the objective result to a tautology. The corrected picture is that PROCESS's
evaluation is exactly deterministic and piecewise smooth, that the analysis the optimiser
differentiates is **not a function of `x` alone**, and that the resulting Jacobian contamination is
~1e-6 in Frobenius norm — not the 1e-3 originally asserted, and not the 5.6 % the probe reported.

---

## 1. What was actually measured

### 1.1 The probe's definition of "gradient error"

`noise_probe.py`, measurement **M3**, is the source of every number in MEMO.md §2. For each
iteration variable `i` it does exactly this (`noise_probe.py:105-111, 158-200`):

```python
def converged_eval(x, extra=10):
    """Loop value, then force `extra` more sweeps to approach the fixed point."""
    vo, vc = caller.call_models(np.asarray(x, dtype=np.float64), m)
    for _ in range(extra):
        caller._call_models_once(np.asarray(x, dtype=np.float64))
    co = objective_function(data.numerics.minmax, data)
    cc, _, _, _, _ = constraints.constraint_eqns(m, -1, data)
    return (vo, vc), (co, np.asarray(cc, dtype=np.float64))
```

```python
xf = x0.copy(); xf[i] = x0[i] * (1.0 + eps)
xb = x0.copy(); xb[i] = x0[i] * (1.0 - eps)
(of_loop, cf_loop), (of_conv, cf_conv) = converged_eval(xf)
(ob_loop, cb_loop), (ob_conv, cb_conv) = converged_eval(xb)
...
cerr = np.abs(cf_l - cf_c) + np.abs(cb_l - cb_c)
jac_loop = (cf_l - cb_l) / dx
jac_conv = (cf_c - cb_c) / dx
jac_abs_err = cerr / abs(dx)
denom = np.where(np.abs(jac_conv) > 1e-30, np.abs(jac_conv), np.nan)
jac_rel_err = jac_abs_err / denom
```

So, precisely:

| element | what it actually is |
|---|---|
| **reference gradient** | a *central finite difference at the same step* `δ = 1e-3·x_i`, of the MDA run to its fixed point (loop + 10 forced extra sweeps). **Not** an analytic, complex-step or Richardson-extrapolated derivative. |
| **differenced against** | the same central difference of the value the idempotence loop actually returns. |
| **objective metric** (`grad_rel_diff`, the "0.0") | `\|g_loop − g_conv\| / \|g_conv\|` — the realised error. |
| **constraint metric** (the "5.55e-2") | `(\|Δ_fwd\| + \|Δ_bwd\|)/2δ` divided **element-wise** by `\|J_conv[i][j]\|`, then **max over the 26 constraints**. A triangle-inequality *bound*, normalised by an individual matrix element. |
| **points** | 2. `x0` (all scaled variables = 1.0) and a vector read from `xcm001..020` of the previous baseline MFILE. |
| **samples** | 1 per stencil point. 20 variables × 2 sides × 1 sample. No repeats, no step-size variation, no ordering variation. |

**Consequence:** M3 answers "how much does terminating the MDA loop early change the finite-difference
Jacobian?" It does **not** answer "how accurate is the Jacobian?" — the reference carries the same
O(δ²) truncation error as the quantity under test, so truncation cancels out of the metric entirely.
It is silent on discontinuities, kinks, sub-solver tolerance effects and roundoff.

### 1.2 The objective result is vacuous

`large_tokamak_nof` has `minmax = 1`. In `process/core/solver/objectives.py`:

```python
if figure_of_merit == FiguresOfMerit.MAJOR_RADIUS:
    objective_metric = 0.2 * data.physics.rmajor
```

and `rmajor` is itself iteration variable `ixc = 3` (scaled index 1 of 20). `set_scaled_iteration_variable`
writes `x[1]` straight onto `data.physics.rmajor`; `objective_function` reads it straight back. Therefore

> **objf(x) = 0.2 · rmajor_init · x₁ = 1.6 · x₁, exactly, with zero dependence on any model output.**

Verified directly (`runs/noise_deepdive/info/info.json`): perturbing each of the other 19 variables by
±1 % and ±2 % leaves `objf` at `1.6` to every printed digit; the gradient is
`[0, 1.6, 0, 0, …, 0]`; and across an 11-point step ladder from δ = 3e-2 down to 1e-7 the objective
gradient varies by 2.2e-10 (pure roundoff).

So "objective-gradient error **exactly 0.0** for all 20 iteration variables at both points" is a
statement about the central difference of a linear function that never enters the MDA. It is true,
it is exact, and it carries **no information whatsoever** about gradient quality. It would not hold
for any scenario whose figure of merit is a genuine model output — `minmax` = 5 (Q), 6 (cost of
electricity), 7 (capital cost), 15 (availability), 17 (net electric). MEMO.md Finding 2 ("the
objective has in fact reached its fixed point to double precision") is a misattribution: the
objective never had a fixed point to reach.

---

## 2. The mechanism

### 2.1 Three things that are not the same

| | present in PROCESS? | evidence |
|---|---|---|
| **(a) stochastic noise / non-repeatability** | **No.** | Identical FD chain run twice at the same `x`: Jacobian reproduces to 1.2e-12 (roundoff). Baseline reruns bit-identical (MEMO §0). |
| **(b) genuine non-smoothness** (branches, clamps, table edges, sub-solver kinks) | **Yes, definitely.** | Perturbing a TF variable by ±50 % raises `RuntimeError: Failed to converge after 50 iterations, value is nan` out of `optimize.newton` at `superconducting.py:1163` (`disp=True`) — a hard failure surface in x-space. `st_regression` crashed on `znfuel < 0` under single-sweep evaluation. The census found 473 state entries still moving after one sweep. |
| **(c) solver-tolerance plateaus** (MDA early exit, inner Newton tolerances) | **Yes, and this is what the probe measured.** | §2.2 below. |

The user's intuition is about (b). The probe measured (c). Both statements can be true because the
signatures are completely different, and because (b) is a *measure-small* event per stencil.

### 2.2 What the idempotence loop actually does — sweep-by-sweep trace

`Caller._call_models_original` compares consecutive sweeps with
`np.allclose(previous, current, rtol=1.0e-6, equal_nan=True)` (`caller.py:67`). **numpy's default
`atol = 1e-8` applies**, so the effective test is `|Δc| ≤ 1e-8 + 1e-6·|c|`.

The critical empirical fact, which nobody had checked, is that **the Gauss-Seidel sweep converges in
a finite number of steps to a bitwise fixed point**, not asymptotically. The model chain in
`_call_models_once` is essentially a DAG with a short feedback path, so ~4 applications annihilate
the residual exactly.

Trace at the worst stencil point (`dx_tf_turn_steel` forward, at `x0`, after replaying the FD chain
for columns 0–12; `runs/noise_deepdive/trace_x0_v13/`):

| sweep | c₅ (icc 16, net electric power) | ‖c_k − c_k₋₁‖∞ | ‖c_k − c*‖∞ |
|---|---|---|---|
| 1 | −0.763295548291 | — | 1.1617e-05 |
| 2 | −0.763295424632 | 1.1012e-05 | 6.0572e-07 |
| **3** | **−0.763294861239** | **6.0572e-07** | **3.1039e-08** ← loop exits here |
| 4 | −0.763294830200 | 3.1039e-08 | **0.0 (exact)** |
| 5–12 | −0.763294830200 | 0.0 | 0.0 |

The loop exits at sweep 3 because the sweep-2→3 change (6.06e-7) is below the threshold
(1e-8 + 1e-6·0.763 = 7.73e-7). One more sweep would have been **bitwise exact**. Instead it returns
a value carrying a residual of **3.1039e-08**.

The residual obeys a simple law. With per-sweep contraction ρ:

> **residual ≈ ρ · (atol + rtol·|c|)** = 0.051 × 7.73e-7 = 3.9e-8. Measured: 3.10e-8.

The measured contraction factor is ρ = 3.1039e-8 / 6.0572e-7 = **0.0512**. This is why the original
"residual ≈ rtol = 1e-6" assumption overestimated by ~30×.

### 2.3 Why it is sparse: an integer race

Two integer-valued quantities are in play at every stencil point:

* `exit_sweep(x, incoming state)` — when `allclose` first fires;
* `fixpoint_sweep(x, incoming state)` — when the iterate first equals its bitwise limit.

**A residual is carried out if and only if `exit_sweep < fixpoint_sweep`.** Survey over all 40 FD
stencil points (`runs/noise_deepdive/survey_x0/`, `survey_opt/`):

| | at `x0` | at the optimum |
|---|---|---|
| stencil points with `exit_sweep < fixpoint_sweep` | **7 / 40** | **3 / 40** |
| stencil points with a non-zero residual | **7 / 40** | **3 / 40** |
| residual range | 1.3e-15 … **3.10e-08** | 2.2e-16 … **1.13e-11** |
| measured contraction ρ | 0.0042 … 0.0512 | 0.0194 … 0.0196 |
| affected constraint | always **icc 16** (net electric power) | icc 16 / 36 |
| typical ‖Δc‖ at exit | 6e-7 | 2.4e-10 |
| objective residual | 0.0 (linear) | 0.0 (linear) |

The correspondence is exact, at both points. That is the mechanism, confirmed.

`icc 16` is `p_plant_electric_net_mw ≥ p_plant_electric_net_required_mw` — the very last quantity in
the sweep, produced by `power.acpow()` and `power.plant_electric_production()`, which `caller.py`
itself notes "need to be run after vacuum/buildings otherwise output changes quite a lot". It is the
slowest-converging mode in the MDA, so it is the only one that ever loses the race.

### 2.4 Why it is not a staircase in `x` — and why it survives the central difference anyway

The brief's model was: the residual jumps by ε where an integer changes, and a jump falling inside
the `2δ` stencil contributes ε/(2δ). **The amplification law is exactly right; the "jump inside the
stencil" picture is not.**

Fine line scan along `dx_tf_turn_steel`, 801 points over ±2·`epsfcn` (±2e-3 relative, spacing 5e-6),
with the incoming state held fixed at the previous FD column's backward point — i.e. exactly the
history `fcnvmc2` produces (`runs/noise_deepdive/scan_pre_x0/`, 105 s):

| quantity | result over 801 points |
|---|---|
| sweep count at every point | **3** (constant) |
| exit residual on icc 16 | **−3.1039e-08 at every one of the 801 points** (constant) |
| exit residual on all other constraints | 0.0 (one point at 1.2e-15) |
| converged constraints `c*(t)`: max\|Δc\| / median\|Δc\| | **1.00** for all 7 varying constraints — perfectly smooth, no jumps |
| loop-exit constraints `c(t)`: jumps > 5× median step | **none** |
| resulting `J_loop − J_conv` across the ±1e-3 stencil | **0.0 for every constraint** |

And a second scan with a *deeply converged* incoming state (`runs/noise_deepdive/scan_x0_v13/`,
801 points, 89 s) gives exit residual **identically 0** everywhere and 2 sweeps at every point.

So over the FD window the residual is a **constant offset**, not a staircase, and a constant offset
**cancels exactly in a central difference**. If both stencil points shared a history, the column
would be clean.

**The contamination comes from history asymmetry, not from x-dependence.** `fcnvmc2`
(`evaluators.py:128-146`) evaluates, for each variable in turn:

```python
ffor, cfor = self.caller.call_models(xfor, m)   # reached from the PREVIOUS variable's xbac
fbac, cbac = self.caller.call_models(xbac, m)   # reached from xfor, one coordinate away
```

The two stencil points therefore arrive at different distances from their fixed points, exit on
different sweep numbers (3 and 2 for `dx_tf_turn_steel` at `x0`), and carry *different* residuals —
3.10e-8 and 0. It is the **difference of the residuals** that pollutes the column.

### 2.5 The function VMCON differentiates is not a function of `x`

Direct test (`runs/noise_deepdive/fdchain_x0/`): replicate `fcnvmc2` exactly — no extra sweeps —
several times at the same `x0`, after a throwaway warm-up chain. Errors are ‖ΔJ_col‖ / ‖J_col‖.

| comparison | max over columns | median | columns affected |
|---|---|---|---|
| same order, run twice (A vs B) | 1.2e-12 | 0.0 | 8/20 (roundoff) |
| reversed order, run twice (C vs D) | **0.0** | 0.0 | 0/20 |
| **forward vs reversed order (A vs C)** | **1.13e-05** | 3.4e-14 | **12/20** |
| forward vs converged-MDA FD (A vs REF) | 6.41e-06 | 1.3e-14 | 11/20 (5 above 1e-7) |
| reversed vs converged-MDA FD (C vs REF) | 1.13e-05 | 0.0 | 6/20 |
| **converged-MDA FD, forward vs reversed order** | **0.0** | 0.0 | **0/20** |

Two conclusions:

1. The FD of the **fully converged** MDA is order-independent to the last bit in all 20 columns. The
   converged analysis *is* a genuine function of `x`.
2. The Jacobian VMCON actually receives **changes when you reorder the loop over iteration
   variables**, in 12 of 20 columns, by up to 1.1e-5. It is reproducible (A vs B ≈ 0) but
   order- and history-dependent. **It is therefore not the Jacobian of any function.**

There is also a warm-up effect: the very first FD chain evaluated after a fresh `call_models(x0)` is
systematically worse (up to 1.15e-5 relative on 19/20 columns) than subsequent ones. Far-from-solution
gradients are the contaminated ones.

### 2.6 Why it vanishes at the optimum

At the optimum the sweep-to-sweep change at loop exit falls from ~6e-7 to ~2.4e-10 — three orders of
magnitude — so `allclose` fires only *after* the fixed point has been reached at 37 of 40 stencil
points. The three survivors carry residuals ≤ 1.13e-11 instead of 3.10e-8. Every measure of Jacobian
contamination drops by 3–4 orders (max column-norm-relative error 6.4e-6 → 7.0e-10).

---

## 3. Quantification: reconciling 3.1e-8 with "5.55e-2"

Chain of arithmetic, every step verified numerically:

| step | value |
|---|---|
| function-value residual carried out of the loop, on `icc 16` (\|c\| ≈ 0.76) | **ε = 3.1039e-08** |
| FD step: `δ = epsfcn·x_i = 1e-3`, so `2δ` | 2.000e-03 |
| **implied FD contamination `ε/(2δ)`** | **1.5519e-05** (absolute) |
| probe's reported `max_jac_abs_err` | **1.5520e-05** ✓ |
| divided by the affected element `J[13][5] = −2.7954e-04` | **5.5518e-02** ← the memo's headline ✓ |

The 5.6 % is a 1.55e-5 absolute error divided by the **smallest non-zero derivative in that column**.
Reported against any norm an optimiser can act on, the same measurement reads:

| normalisation | value at `x0` | at the optimum |
|---|---|---|
| vs the individual element `\|J[13][5]\|` = 2.80e-4 (the memo's metric) | **5.55e-02** | 2.26e-07 |
| vs the **constraint normal** `‖∂c₁₆/∂x‖` = 6.87 (what VMCON's QP uses) | **4.61e-06** | — |
| vs the **column norm** `‖∂c/∂x₁₃‖` = 3.94 | **3.94e-06** | 7.0e-10 |
| vs the **whole Jacobian**, Frobenius | **1.01e-06** | ~1e-09 |
| order-dependence of the delivered Jacobian, Frobenius | **1.01e-06** | — |

Only **one** constraint normal out of 26 is materially affected (icc 16, at 4.6e-6); the other 11
non-zero rows sit at 1e-12, i.e. roundoff.

### 3.1 The step-size ladder — the measurement that should have been made

An FD noise floor is exposed by shrinking the step, not by one measurement at one step. Central
differences at 11 steps from 3e-2 to 1e-7, reference = Richardson extrapolation from (3e-3, 1e-3)
(`runs/noise_deepdive/steps_x0/`, `steps_opt/`; ~4 s each):

| δ | max col. rel. err (x0) | **median (x0)** | median (opt) | implied ε_f (x0) |
|---|---|---|---|---|
| 3e-2 | 2.30e-02 | 1.33e-03 | 9.99e-04 | — |
| 1e-2 | 4.70e-03 | 1.17e-04 | 1.10e-04 | — |
| 3e-3 | 1.73e-04 | 1.17e-05 | 9.93e-06 | — |
| **1e-3 ← `epsfcn`** | 1.93e-05 | **1.30e-06** | 1.10e-06 | — |
| 3e-4 | 1.20e-05 | 3.05e-07 | 9.93e-08 | 2.2e-08 |
| 1e-4 | 2.18e-05 | 1.98e-07 | 1.11e-08 | 3.6e-08 |
| 3e-5 | 1.79e-04 | 1.00e-07 | 1.47e-09 | 1.9e-08 |
| **1e-5** | 5.21e-04 | **9.14e-08 ← minimum** | 4.41e-10 | 1.8e-08 |
| 3e-6 | 5.21e-04 | 1.02e-06 | 6.16e-08 | 2.1e-08 |
| 1e-6 | 1.48e-03 | 3.27e-05 | 2.87e-07 | 4.3e-08 |
| 1e-7 | 1.48e-03 | 3.27e-05 | 1.05e-06 | — |

This is the textbook V: a δ² truncation branch on the left, a 1/δ noise branch on the right, a
minimum near **δ ≈ 1e-5**. Back-solving the noise branch (`ε_f ≈ ‖ΔJ‖·2δ`) gives an effective
absolute function noise floor of **ε_f ≈ 2e-8**, in excellent agreement with the directly traced
3.1e-8 early-exit residual — i.e. the MDA early exit *is* the noise floor; there is no larger
hidden source.

Two consequences:

* **At the operating step `epsfcn = 1e-3` the FD error budget is truncation-dominated.** Median
  column truncation error is 1.30e-06; median early-exit contamination is 1.3e-14 (9 of 20 columns
  exactly zero, only 5 above 1e-7), 6.4e-6 at worst. The MDA tolerance is *not* the binding error
  term.
* `epsfcn` is 10–100× larger than optimal for these functions. That is a far more defensible
  criticism of the numerics than "noisy gradients".
* The objective gradient stays `[0, 1.6, 0, …]` across the whole ladder (spread 2.2e-10) — again,
  because it is linear.

---

## 4. Assessment of the original probe

### 4.1 Was two points adequate? No.

Both points were the two most favourable points on the trajectory: `x0` is a hand-tuned consistent
starting design, and the optimum is by construction the most converged state the run ever visits.
The 630 `call_models` of an actual solve — line-search trial points, 15 gradient evaluations, and any
`epsfcn` retry — were never sampled. Since the mechanism is a *race between two integers*, the
per-stencil-point hit rate (7/40 and 3/40, i.e. 8–18 %) is a small-sample binomial estimate at two
locations; nothing in the data licenses extrapolating it along the trajectory. Section 2.5's warm-up
result actively suggests the trajectory is worse than either sampled point.

### 4.2 Did it measure the right thing? Partly.

**Right:** the reference (loop + 10 forced sweeps) is the correct reference for isolating the
early-exit effect, and the 10 extra sweeps are genuinely enough — the fixed point is reached bitwise
by sweep 4–9.

**Wrong, in three ways:**

1. **The metric is not gradient accuracy.** Because the reference is itself a central difference at
   the same δ, the O(δ²) truncation error cancels out of the metric. The ladder shows truncation is
   the *larger* term at the operating step for most columns. The probe therefore reported a
   subdominant error component as if it were the error.
2. **The constraint metric is a bound, not the realised error.** `cerr = |Δ_fwd| + |Δ_bwd|` is a
   triangle inequality; the realised error is `|J_loop − J_conv|`. I recomputed both
   (`runs/noise_deepdive/jac_x0/`): here they coincide to the last digit, because one of the two
   residuals is always exactly zero — but that is a property of this problem, not of the metric.
   In general the bound can overstate by 2× or mask cancellation.
3. **The normalisation inflates the headline by ~4 orders of magnitude.** Dividing element-wise by
   `|J_conv[i][j]|` and taking a max over 26 constraints is a max over near-null denominators. See
   the table in §3.

### 4.3 Under-powered secondary measurements

* **M2 "path dependence = 0.0"** probed `i_probe = min(1, n-1) = 1`, which is `rmajor` — the pure
  objective variable — and reported `objf` peak-to-peak, which is `1.6·x₁` and therefore *zero by
  construction*. Meanwhile M1's own output records `conf_ptp_max = 9.6e-11` and
  `"deterministic": false` at fixed `x`. **MEMO.md Finding 1 ("deterministic and path-independent")
  is half wrong: deterministic yes, path-independent no** — §2.5 shows order-dependence at 1.1e-5.
* No step-size variation, no repeated chains, no reordering, no line scan. None of the structure in
  §2 was observable with the measurements taken.
* **A counting error in MEMO.md §2.** "M3 median constraint-Jacobian relative error: 0.0 (18/20
  columns exact)" is listed against the `x0` column. Recounting `noise_x0_v2/noise.json`: at `x0`
  **14 of 20** columns are exactly zero (non-zero at i = 6, 7, 8, 12, 13, 19); 18/20 is the count at
  the *optimum* (non-zero at i = 6, 8). The median is 0.0 at both, so the headline survives, but the
  sparsity at `x0` is 70 %, not 90 %.

### 4.4 What the earlier 1e-3 claim got right and wrong

The original assessment said: *"MDA idempotence tol 1e-6 against FD step 1e-3 implies relative
gradient noise up to ~1e-3."*

**The kernel of truth is the amplification law.** Dividing a function-value residual by `2δ` is
exactly the right dimensional argument, and it is confirmed to the digit here
(3.1039e-8 / 2e-3 = 1.5519e-5, matching the probe's `max_jac_abs_err` = 1.5520e-05).

**Three things it got wrong, each worth roughly an order of magnitude:**

1. **The residual is not `rtol·|f|`.** The sweep converges *finitely*, so at 33 of 40 stencil points
   the residual is exactly 0. Where it is non-zero it is `ρ · (atol + rtol·|c|)` with ρ ≈ 0.05 —
   about 30× below `rtol`.
2. **It is a near-constant offset over the stencil, so it largely cancels** in the central
   difference. Only history asymmetry between the two stencil points lets any of it through.
3. **It was implicitly assumed uniform across the Jacobian.** It is confined to a single constraint
   (icc 16) and, in the faithful `fcnvmc2` chain, to 5 of 20 columns above 1e-7.

Net: 1e-3 → **~1e-6 Frobenius, ~5e-6 on the single worst constraint normal**, sparse, worst far from
the solution, and essentially gone at the optimum.

### 4.5 On the user's objection — where do the discontinuities go?

They are real; they simply do not show up in this measurement, for a structural reason.

Branch boundaries, clamp activations and table edges are **codimension-1 surfaces in R²⁰**. A central
difference for variable `i` probes a *segment* of length `2δ = 2e-3` along a single coordinate. A
surface pollutes that column only if it intersects that particular segment. Per gradient evaluation
there are 20 such segments; per solve (~15 gradient evaluations) about 300. Hitting one is a
measure-small event *per stencil*, not an impossible one — a probe with 40 stencil samples at 2
points has essentially no power to detect it, and correctly reported zero.

The signature also differs: a branch crossing produces a **kink or jump in the converged function
itself**, which would show up as a large single step in the line scan and as a *step-size-dependent*
FD value that does not settle as δ shrinks. Neither appears in the 801-point scans (max/median step
ratio = 1.00) or in the ladder (which settles cleanly to a Richardson-consistent value between
δ = 3e-4 and 1e-5). So along the directions probed here, the converged analysis is genuinely smooth.

The inner solvers are subtler but bounded. `optimize.newton` at `superconducting.py:1163` uses a
*fixed* starting guess (`temp_tf_coolant_peak_field`, secant `x1 = 2·` that) rather than a warm start,
so its root is a deterministic function of `x`, with a tolerance-limited error that changes stepwise
when the secant iteration count changes — another integer-valued staircase. It contributes to the
ε_f ≈ 2e-8 floor and did not dominate at δ = 1e-3. It *does* produce hard failures: perturbing a TF
variable by ±50 % raised `RuntimeError: Failed to converge after 50 iterations, value is nan`, with
`disp=True` turning it into an exception rather than a returned value. That is a robustness hazard,
not a gradient-noise hazard.

---

## 5. What the paper should measure and claim

**Do not claim** "~1e-3 relative gradient noise" — refuted by 3 orders of magnitude on every
decision-relevant norm.
**Do not claim** "gradients are exact" — refuted: the delivered Jacobian is order-dependent at 1.1e-5.
**Do not quote the objective-gradient result** for a `minmax = 1` scenario; it is a tautology. If an
objective-gradient statement is wanted, rerun on `minmax` ∈ {5, 6, 7, 15, 17}, where the figure of
merit is a genuine model output and will behave like the constraints.

**Claim instead — the correctness argument, which is the strong one:**

> PROCESS's analysis is exactly deterministic and bitwise reproducible. However, the map the
> optimiser differentiates is *not a function of the design vector*. `Caller.call_models` terminates
> a Gauss-Seidel fixed-point iteration on a relative-change test
> (`np.allclose(prev, cur, rtol=1e-6)`, with numpy's default `atol=1e-8` silently active), not at the
> fixed point. Where the test fires before the iteration has converged, the returned values carry a
> residual ≈ ρ·(atol + rtol·|c|) ≈ 3e-8 whose presence depends on the *evaluation history*, not on
> `x`. Because `fcnvmc2` reaches the two central-difference stencil points from different histories,
> that residual does not cancel: reordering the finite-difference loop over iteration variables
> changes 12 of 20 Jacobian columns, by up to 1.1e-5 relative to the column norm, whereas the
> finite difference of the fully converged analysis is order-independent to the last bit. The
> resulting contamination is small (1.0e-6 in Frobenius norm at `x0`, ~1e-9 at the solution) and is
> dominated at the operating step by ordinary O(δ²) truncation error — but it means the SQP is being
> handed a Jacobian that is not the Jacobian of anything.

**Supporting numbers to quote** (all reproducible from `runs/noise_deepdive/`):

| claim | number | source |
|---|---|---|
| evaluation is deterministic | identical FD chain twice: ‖ΔJ‖ ≤ 1.2e-12 | `fdchain_x0.json` |
| converged analysis is a function of `x` | FD of converged MDA, forward vs reversed order: **0.0** in all 20 columns | `fdchain_x0.json` |
| delivered Jacobian is not | forward vs reversed order: **1.13e-05** max, 12/20 columns | `fdchain_x0.json` |
| early-exit contamination | 1.01e-06 Frobenius; 4.6e-06 on the worst constraint normal | `fdchain_x0.json` |
| mechanism | residual ≠ 0 **iff** `exit_sweep < fixpoint_sweep`: 7/40 at `x0`, 3/40 at the optimum | `survey_*.json` |
| residual law | ρ·(atol + rtol·|c|), ρ = 0.0042–0.0512 measured | `trace_x0_v13.json` |
| it vanishes at the solution | residual 3.10e-08 → 1.13e-11; column error 6.4e-6 → 7.0e-10 | `survey_opt.json`, `jac_opt.json` |
| converged constraints are smooth | 801-point scan, max/median step ratio = 1.00, no jumps | `scan_pre_x0/` |
| truncation dominates at `epsfcn` | median column truncation 1.30e-06 at δ=1e-3; V-minimum at δ≈1e-5 | `steps_x0.json` |
| noise floor | ε_f ≈ 2e-8, matching the traced 3.1e-8 residual | `steps_x0.json` |

**Two concrete, cheap defects worth naming:**

1. **`np.allclose`'s default `atol = 1e-8` is silently active** in `check_agreement`. For constraints
   with `|c| < 1e-2` the absolute floor dominates the intended relative test. That is almost
   certainly unintended.
2. **The loop returns the value that passed the test, not the next one.** At `x0`, 5 of the 7
   contaminated stencil points had `fixpoint_sweep = exit_sweep + 1` — including all four that carry
   a residual above 1e-9 — so one additional sweep after the test fires would have made them bitwise
   exact. (The remaining two had `fixpoint_sweep = exit_sweep + 5` with residuals of 2.2e-10 and
   6.4e-10, so a single extra sweep is a large improvement, not a cure.)

---

## 6. Reproduction

```
conda run -p /home/wrutten/anaconda3/envs/PROCESS_env python noise_deepdive.py <cmd> [...]
```
Each sub-command must run in a fresh interpreter and its own work dir (PROCESS mutates a global
`DataStructure`). `PROCESS_IDF_PROBE=baseline` is set inside the script so sweep counts are recorded;
that mode delegates to `Caller._call_models_original`, so semantics are unchanged.

| sub-command | what it does | cost | output |
|---|---|---|---|
| `info` | variable/constraint labels, objective functional form | ~5 s | `runs/noise_deepdive/info/` |
| `jac --at {x0,opt}` | realised vs bounded Jacobian error, per column and per constraint | ~5 s | `jac_x0/`, `jac_opt/` |
| `survey --at {x0,opt}` | `exit_sweep` vs `fixpoint_sweep` at all 40 stencil points | ~5 s | `survey_x0/`, `survey_opt/` |
| `trace --var 13` | sweep-by-sweep convergence at one stencil point | ~5 s | `trace_x0_v13/` |
| `fdchain --at x0` | replicate `fcnvmc2`; repeat / reverse / converged-reference | ~20 s | `fdchain_x0/` |
| `steps --at {x0,opt}` | 11-point FD step ladder | ~5 s | `steps_x0/`, `steps_opt/` |
| `scan --var 13 --precond "12,-0.001"` | 801-point line scan with FD-realistic history | ~105 s | `scan_pre_x0/` |
| `scan --var 13 --reset` | 801-point line scan with converged history | ~89 s | `scan_x0_v13/` |

No files in the PROCESS repository were modified; `process/core/_idf_probe.py` was used as-is
(mode `baseline` only, no new modes added).
