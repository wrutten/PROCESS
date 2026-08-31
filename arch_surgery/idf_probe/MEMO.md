> **Document status** — **SUPERSEDED · STALE**
> The Stage-0 verdict of the abandoned IDF study, measured at commit **`710a75c9`**. Every number
> here — sweep counts, the coupling census, the gradient-noise study — was rederived or discarded
> at `c0ae5b28` (decision D4), and the run artifacts it cites were deleted. **Do not cite it.**
> The current Stage-0 record is
> [`../docs/reports/deprecated/A1_stage0_rebaseline.md`](../docs/reports/deprecated/A1_stage0_rebaseline.md).
> Retained because its *methodology* — switch-neutrality gating, subprocess isolation, the census
> design, and the finding that `nviter` under-reports evaluations — carried forward.

# Track A verdict memo — one-shot IDF performance probe on PROCESS

**Study commit:** `main` @ `710a75c9d2b81053e92918bb6866a0e98f89d814` (merge of ukaea/main, 2026-07-29)
**Date:** 2026-08-06 · **Env:** conda `PROCESS_env`, Python 3.14.3, PyVMCON 2.4.x
**Scope:** tokamak only — `large_tokamak_nof`, `low_aspect_ratio_DEMO`, `st_regression` (optimisation)
plus `large_tokamak_eval` (evaluation).
All numbers below come from JSONs under `runs/`; every run was a fresh subprocess in its own work dir.

---

## 0. Gates

| Gate | Result |
|---|---|
| Instrumentation switch-neutrality (`PROCESS_IDF_PROBE` unset vs `=baseline`, `large_tokamak_eval`) | **PASS** — `norm_objf`, both itvars and `sqsumsq` bit-identical |
| Baseline reproducibility (two independent `large_tokamak_nof` runs, itvars to ~1e-6) | **PASS** — max relative itvar delta **0.0**, identical `norm_objf`, identical sweep count (2049) |
| Baseline solves all 4 scenarios | **PASS** — `ifail=1` everywhere, 0 solver retries |

Determinism is exact, not merely within 1e-6. Note the `census` runs reproduced the baseline sweep
counts exactly (2049 / 4284 / 3437), confirming that instrumentation does not perturb the trajectory.

---

## 1. Baseline anatomy — sweeps per `call_models`

| scenario | n (`nvar`) | m | `call_models` | sweeps | **mean S** | frac at floor 2 | histogram (sweeps: count) |
|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 20 | 26 | 630 | 2049 | **3.252** | 20.2 % | 2:127, 3:275, 4:172, 5:54, 6:2 |
| `low_aspect_ratio_DEMO` | 19 | 25 | 1240 | 4284 | **3.455** | 13.7 % | 2:170, 3:622, 4:162, 5:286 |
| `st_regression` | 14 | 18 | 1050 | 3437 | **3.273** | 15.8 % | 2:166, 3:485, 4:347, 5:50, 6:2 |
| `large_tokamak_eval` | 2 | 25 | 11 | 27 | 2.455 | 72.7 % | 2:8, 3:2, 5:1 |

Per phase (`large_tokamak_nof`): function evaluations S=3.60 (15 calls), FD gradient S=3.23
(600 calls), gradient reconciliation call S=3.93 (15 calls).

**The loop does *not* sit at its 2-sweep minimum.** Only 14–20 % of optimiser evaluations exit at the
structural floor; the mean is ~3.25–3.46 sweeps. This is the single most favourable number for IDF in
the whole study — the per-evaluation savings ceiling from deleting the idempotence loop is **S ≈ 3.3×**,
not the 2× the floor would have implied.

Structural check: `call_models` per VMCON iterate = `2n+2` (`fcnvmc1` 1 + `fcnvmc2` 2n+1). For
`large_tokamak_nof`, 630 = 15 × 42 — i.e. 15 gradient evaluations, though the MFILE reports
`nviter = 8`. **`nviter` under-reports the true evaluation count by ~2×**; use `ncalls`/sweeps for cost.

### Implied speedup ceiling

With `k` lifted coupling variables the per-iterate ratio is `S·(n+1)/(n+k+1)`:

| scenario | k=0 | k=4 | k=6 | k=8 | k=10 | k=12 |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` (n=20) | 3.25× | 2.73× | 2.53× | 2.36× | **2.20×** | 2.07× |
| `low_aspect_ratio_DEMO` (n=19) | 3.45× | 2.88× | 2.66× | 2.47× | **2.30×** | 2.16× |
| `st_regression` (n=14) | 3.27× | 2.58× | 2.34× | 2.13× | **1.96×** | 1.82× |
| `large_tokamak_eval` (n=2) | 2.45× | 1.05× | 0.82× | 0.67× | 0.57× | 0.49× |

> **Correction to the assessment.** Part 2 computed this with n = 83, which is
> `len(ITERATION_VARIABLES)` — the *registry* size, not any scenario's active `nvar` (20 / 19 / 14).
> The error inflated n ~4× and correspondingly hid the IDF dimension penalty. The assessment's ~2×
> headline turns out to be roughly right for k≈10, but for compensating reasons: S is higher than
> assumed (3.3 vs 2.5) and n is much lower. On the small eval scenarios IDF would be a **net loss**.

---

## 2. FD gradient noise — the assessment's claim is refuted

Claim under test: "MDA tol 1e-6 against FD step 1e-3 ⇒ relative gradient noise up to ~1e-3".
Measured on `large_tokamak_nof` (`epsfcn = 1e-3`, central differences, n=20):

| measurement | at x0 | at the optimum |
|---|---|---|
| M1 repeat at fixed x, 20× — `objf` peak-to-peak | **0.0** (exact) | **0.0** (exact) |
| M1 — max constraint peak-to-peak | 9.6e-11 | 7.6e-11 |
| M2 path dependence (x→x±δ→x, 20 evals) | **0.0** | **0.0** |
| M3 objective-gradient relative error | **0.0** for all 20 variables | **0.0** |
| M3 max constraint-Jacobian **relative** error | **5.55e-2** (1 column) | **2.26e-7** |
| M3 median constraint-Jacobian relative error | **0.0** (18/20 columns exact) | 0.0 |
| M3 columns with rel. error > 1e-3 | 2 / 20 | 0 / 20 |
| M3 max constraint-Jacobian absolute error | 1.55e-5 | 5.5e-9 |

**Findings.**
1. The idempotence loop is **deterministic and path-independent** — repeated evaluation at a fixed x
   reproduces the objective exactly. There is no stochastic gradient noise.
2. The **objective** gradient is exact everywhere measured: when the loop declares idempotence at
   `rtol=1e-6`, the objective has in fact reached its fixed point to double precision. The rtol
   criterion is far looser than the convergence actually achieved.
3. Noise exists only in the **constraint Jacobian**, is **sparse** (18 of 20 columns exactly zero),
   and reaches 5.6 % on one column at x0.
4. **It vanishes near the solution** (2.3e-7) — precisely where gradient quality governs convergence.

So "exact gradients" is a much weaker argument for IDF than the assessment supposed. It is not
nothing — a 5.6 % Jacobian error far from the optimum can plausibly cost early iterations — but the
claim of a uniform ~1e-3 relative noise floor that IDF removes at the root is **not supported**.

---

## 3. Single-sweep probe (A2) — the IDF evaluation without IDF's consistency constraints

`Caller.call_models` replaced by exactly one `_call_models_once` + objective + constraints.
Comparison is against the self-generated baseline (`baseline_rep1`), warm numba caches throughout.
Note that the final MFILE is written by an *independent* fully-converged idempotence loop
(`call_models_and_write_output`), so reported itvar deltas are genuine optimum shifts, not lag artifacts.

| scenario | ifail | Δ`norm_objf` (rel) | max itvar Δ | median itvar Δ | sweeps | wall | retries |
|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 1 → **1** | **5.77e-12** | **5.34e-2** | 5.14e-3 | 2049 → 672 (**3.05×**) | 24.1 → 12.4 s (**1.94×**) | 0 → **1** |
| `low_aspect_ratio_DEMO` | 1 → **2** (max iter) | 3.68e-2 | 2.96e-1 | 2.49e-4 | 4284 → 12480 (**0.34×**) | 43.3 → 98.1 s (0.44×) | 0 → 2 |
| `st_regression` | 1 → **crash** | — | — | — | 6660 (aborted) | 54.0 s | 0 → 2 |

**`st_regression` crash:** `ProcessValueError: znfuel is negative: -8.93e18` at
`process/models/physics/physics.py:1242` (`plasma_composition`), raised inside a PyVMCON line search
via `fcnvmc1`. This is exactly Risk 2 from the assessment — model breakdown at an inconsistent state.

**`large_tokamak_nof`** is the interesting case: the objective agrees to 5.8e-12 while iteration
variables differ by up to 5.3 %. The optimum is **flat in those directions** — worst offenders are
`f_nd_impurity_electrons(13)` (5.3 %), `f_c_plasma_non_inductive` (4.5 %),
`f_nd_alpha_thermal_electron` (2.9 %). It therefore *fails* a literal "itvars within 1 %" gate while
*passing* any objective-based criterion. **Recommendation for Track B: gate on `norm_objf` plus a
post-solve feasibility audit, not on itvar deltas** — several itvars are simply not identified by
this problem, and a 1 % itvar gate would generate false alarms.

**Robustness read: single-sweep evaluation is markedly less robust.** 1 of 3 scenarios converged
(and only after an `epsfcn` retry it did not need at baseline); 1 hit the iteration limit and got
*slower*; 1 crashed. This is expected — the probe deliberately omits the consistency constraints that
make IDF sound — but it does establish that the couplings are **not** weak.

**Best-case measured cost saving** (`large_tokamak_nof`, k=0): 3.05× in sweeps but only **1.94× in
wall time**. Per-sweep model evaluation is not the whole cost; constraint/objective evaluation, VMCON
linear algebra and output writing do not shrink. **Wall-clock speedup runs ~35 % below sweep-count
speedup — quote wall time, not sweeps.** Folding in a k=10 dimension penalty gives a realistic
Track B Stage-2 expectation of **~1.3–1.5× wall clock**, not 2–3×.

---

## 4. Coupling census (A3 input) — the feedback set is far larger than assessed

New measurement (`census` mode): follows the exact baseline trajectory and snapshots the whole
`DataStructure` after sweep 1 and after sweep 2 of every function-phase `call_models`, diffing them.
An entry that differs is state a single-sweep evaluation would have got wrong. Symmetric relative
measure `|b−a|/(|a|+|b|)` (bounded by 1, robust near zero).

| scenario | entries changed | >1e-3 | >0.01 | >0.1 | >0.5 |
|---|---|---|---|---|---|
| `large_tokamak_nof` | **473** | 319 | 228 | 180 | 111 |
| `low_aspect_ratio_DEMO` | **483** | 328 | 250 | 177 | 115 |
| `st_regression` | **459** | 301 | 149 | 62 | 16 |

**48 entries exceed 10 % drift in all three scenarios.** Of the >10 % set, roughly half sit in
upstream physics/engineering modules (`physics`, `build`, `pf_coil`, `fwbs`, `first_wall`,
`current_drive`, `blanket`, `divertor`) and half in downstream accounting modules (`costs`, `power`,
`heat_transport`, `buildings`).

Highest-drift entries common to all three scenarios include `current_drive.big_q_plasma`,
`physics.beta_norm_max_stambaugh`, `physics.nd_plasma_protons_vol_avg`,
`current_drive.f_c_plasma_bootstrap_sugiyama_h`, `build.a_blkt_total_surface`,
`first_wall.a_fw_total`, `blanket.n_fw_inboard_channels`, `divertor.deg_div_poloidal_plasma`.
Per-scenario leaders reach the saturation value (sym = 1.0, i.e. sign change or growth from ~0):
`pf_coil.stress_z_cs_self_midplane_profile`, `heat_transport.peakmva`, `costs.c22521`,
`pf_coil.vs_cs_burn`, `constraints.t_current_ramp_up_min`.

> **This is the study's most consequential finding.** The assessment states the feedback set is
> "≈ 8–12 scalars". Measured, **459–483 state entries are still moving after the first sweep**, of
> which 62–180 move by more than 10 %.

**Necessary caveat.** The census bounds the *inconsistency footprint*, not the *minimal cut set*. Many
of those 473 entries are downstream consequences of a smaller number of upstream lags, and downstream
accounting outputs (costs, power) do not need lifting at all — they are outputs, not feedback edges.
Identifying the true minimal cut requires the read-before-write dependency graph (the `ragraph`
analysis Track B Stage 1 plans), which this probe did not build. What the census *does* establish is
that the inconsistency after one sweep is pervasive rather than confined to a dozen scalars, so the
prior that a ~10-variable lift will suffice is not supported by evidence.

**A3 (registry-injection lift) was therefore not executed.** The plan's own abort rule — "if k > 6 and
optima still don't match, report *IDF lift is harder than assessed*" — is triggered by the census
before spending hours on injection. A speculative 6-variable lift chosen from a 48-variable
cross-scenario candidate set would most likely have produced an uninformative negative.

---

## 5. Verdict — qualified go for Track B, with re-scoped expectations

**Go, but re-scope Stage 1 and re-baseline the claims.**

The architectural case survives and is in fact strengthened; the *performance* case is real but
roughly half what was projected, and the *gradient-quality* case is largely refuted.

**What holds up**
- The idempotence loop genuinely costs ~3.3 sweeps per evaluation (not 2) — a real 3.3× per-evaluation
  ceiling, the strongest quantitative result here.
- The architecture is measurably ad hoc: `nviter` under-reports evaluations ~2×; a retry ladder
  silently rescales `epsfcn`; one scenario's models raise on physically inconsistent states.
- Determinism and reproducibility are exact, so a clean A/B is achievable — the methodology works.

**What must be revised**
1. **Speedup: expect ~1.3–1.5× wall clock at Stage 2, not 2–3×.** Sweep-count speedup overstates wall
   speedup by ~35 %, and the k-dimension penalty is material at n=14–20.
2. **Drop "exact gradients" as a headline claim.** Objective gradients are already exact; Jacobian
   noise is sparse and vanishes near the optimum. Keep it as a secondary, honestly-scoped observation.
3. **The coupling set is the dominant risk, and it is much bigger than assessed.** Stage 1's `ragraph`
   dependency analysis is no longer an optional tidy-up — it is the **gating prerequisite** that
   decides whether Stage 2 is feasible at all. Do Stage 1 first and *re-decide* Stage 2 on its output.
4. **Change the Stage-2 gate** from "itvars within 1 %" to `norm_objf` agreement plus a post-solve
   feasibility audit; some itvars are unidentified (5.3 % spread at a 5.8e-12 objective difference).
5. **Budget for NaN/robustness work.** 2 of 3 scenarios failed without consistency constraints, one by
   a hard model exception. The penalty-guard and bounds work in the Stage-2 plan is load-bearing, not
   a nicety.

**Highest-value next step (cheap, decisive):** the read-before-write dependency graph over
`_call_models_once`'s ~22-step sequence, intersected with the 48 cross-scenario census entries above.
That yields the true minimal cut set and converts this study's upper bound into the actual `k`. Until
`k` is known, the speedup table in §1 is the honest range, and `k > 20` would make IDF a net loss on
`st_regression`.

**If the paper needs a result now:** §1 (sweep anatomy), §2 (gradient-noise quantification, including
the negative), §3 (single-sweep A/B) and §4 (empirical coupling census) already constitute a defensible
quantified critique of the current architecture — the Stage-0 deliverable — without any refactor.

---

## Provenance

| Artifact | Path |
|---|---|
| Per-run metrics | `runs/<scenario>/<mode>/metrics.json` |
| Per-call sweep/phase/drift log | `runs/<scenario>/<mode>/probe.jsonl` |
| Baseline reference | `runs/baseline_summary.json` |
| Full A/B + drift ranking + gates | `runs/comparison.json` |
| Gradient noise | `runs/large_tokamak_nof/noise_x0_v2/noise.json`, `runs/large_tokamak_nof/noise_opt/noise.json` |
| Coupling census | `runs/<scenario>/census2/metrics.json` (`probe.census`) |

Modes run: `unpatched`, `baseline` (×2 for `large_tokamak_nof`), `single_sweep`,
`single_sweep_debug`, `census`. 18 PROCESS runs total, each in a fresh subprocess.
