# MDA partitioning experiment — plan

> **Document status** — CURRENT · **live experiment** · rewritten 2026-09-01 against D13
> (two-phase design). Supersedes the staged 0-5 design; the evidence from A1, A2 and A19 is
> carried forward in §1.4 and §5, not discarded.

**Status:** **AUTHORISED TO PROCEED** (D12), **restructured into two phases** (D13).
· **Base commit:** `c0ae5b28` · **Scope:** tokamak only — stellarator and IFE take an early
return in `_call_models_once`.

**What this plan is for.** An **existence proof**: one fair case in which a simple, minimally
invasive change to the *arrangement* of solvers measurably changes the cost of solving PROCESS,
with every physics and engineering model untouched. It is **not** a verdict on whether this
particular partition should be adopted, and it does not claim to have found an optimal
architecture. That reframing (user, 2026-09-01) sets every gate below: the burden is
**fairness**, not effect size.

---

## 1. Problem context

### 1.1 The question

Does the arrangement of solvers and optimisers alone — with the models frozen — measurably
change the cost of solving PROCESS?

The frozen models are what makes the question answerable. A rewritten back-end cannot isolate
the architecture's contribution, because any measured difference confounds the architecture
with the rewrite. That is why this study is the control a later IDF/MDF/SAND comparison on
`functional_PROCESS` will need, and not a stepping stone to it (D5, D7).

### 1.2 What the driver does today

`Caller.call_models` ([caller.py:73-144](../../../process/core/caller.py#L73)) re-runs the whole
26-model sequence until the **objective function and the constraint vector** stop changing, at
`rtol = 1e-6`, capped at 10 sweeps. `_call_models_once` executes a hand-written order.

Three properties of that loop matter to this experiment, and all three are defects rather than
design choices:

**It converges on the wrong quantities.** `objf` and `conf` are *functionals* of the state. The
DSM's feedback edges identify **coupling variables**; those are what a fixed-point iteration is
supposed to converge. Coupling variables that do not move `f` or `c` by `rtol` are declared
converged — and the finite-difference stencil differences exactly `f` and `c`, so residual
motion invisible to the exit test is precisely what pollutes the gradient. A2 measured this
happening: in **24 % of `large_tokamak_nof`'s calls the state is still changing when the loop
declares idempotence**, driven almost entirely by
`pf_coil.stress_z_cs_self_midplane_profile`.

**It has a structural floor of two sweeps, and that floor is an artefact.** Because `objf` and
`conf` do not exist at entry, the loop must evaluate once purely to manufacture a `prev` to
compare against, then again to compare. The first sweep yields no information about
convergence. A coupling-variable predicate has no such problem: the entering state **is** `y0`
— it persists in the data structure from the previous call, with the new design vector injected
on top — so one sweep gives `y1 = G(y0)` and `norm(y1 - y0)` is immediately testable.
**The floor for a proper fixed-point iteration is 1, not 2.**

The size of that artefact, measured: of `large_tokamak_nof`'s **2 027** in-loop sweeps, **1 260**
are the structural minimum of two per call. One information-free sweep per call is **630 sweeps,
31.1 % of the total**, and the same arithmetic gives A1's "above floor" column directly —
37.8 %, 42.1 %, 39.7 %, 27.3 % of sweeps are the only ones any convergence-side change can act
on *while the floor stays at 2*.

**Its convergence test treats NaN as agreement.** `np.allclose(..., equal_nan=True)`
([caller.py:70](../../../process/core/caller.py#L70)) means a state that has gone NaN in two
consecutive sweeps is reported converged.

### 1.3 What the DSM says

From `dependency_analysis/output/tokamak/dsm_collapsed.html`, pin `PROCESS_at_36ac820e`, which
descends from `c0ae5b28` — the coordinate systems match.

> **The DSM is configuration-specific — checked, and the partition survives (V6, RESOLVED).** It resolves conditionals against the
> analysis tool's `tokamak` preset, which is built from `examples/data/large_tokamak_IN.DAT`. That
> deck matches `large_tokamak_nof` and `large_tokamak_eval` **exactly**, and diverges from
> `st_regression` roughly **twice as far** as from `low_aspect_ratio_DEMO` — on our 33-switch
> population, 12 against 5; on the analysis tool's own field set, 17/7, 15/7 or 8/4 depending on
> the denominator. **The ordering holds under every denominator; the integer does not travel, so
> quote the ratio.** What matters is *which* switches differ: `i_pulsed_plant`, `itart`,
> `i_single_null`, `i_plasma_current` and the TF path. **The module decomposition
> below is therefore authoritative for the two large tokamaks, a near neighbour for the DEMO case,
> and an extrapolation for `st_regression`.** Phase A's *predicate* does not depend on this — the
> coupling set is instrumented at run time — but the **block arm's module boundaries do**. Full
> switch table and the requested fix in
> [`../reports/DSM_VALIDATION.md`](../reports/DSM_VALIDATION.md) V6.

| Rows | Contents | Role |
|---|---|---|
| 1-3 | `COOR_SingleRun`, `VMCON`, `MDA_Idempotence` | driver stack, not in a sweep |
| **4, 6-28** | `PlasmaGeom`; `Physics` … `PlasmaConfinementTime` | **M1 — Physics** (24 nodes) |
| **5, 29-37** | `Build`; `CICCSuperconductingTFCoil` … `pfcoil_functions` | **M2 — Coils** (10 nodes) |
| 38 | `CsFatigue` | feed-forward |
| **39** | **`Pulse`** | the articulation point — belongs to no module |
| **40-51** | `Divertor` … `Availability` | **M3 — Plant** (12 nodes) |
| 52-55 | `WaterUse`, `Costs`, `Objective`, `Constraints` | feed-forward outputs |
| 56 | `MDA_Output` | not in a sweep |

`|all| = 52`. Each module carries internal cycles, so each warrants a solver of its own. **M1 is
more than twice either other module** — the fact §5.2 turns on.

**`Build` is misplaced.** It is DSM row 5 (M2) but `_call_models_once`
([caller.py:249](../../../process/core/caller.py#L249)) runs it at sequence position 4, between
`plasma_geom` and `physics` — inside M1's span. That interleaving, M1, M2, M1…, M2…, is what
prevents wrapping a solver around a contiguous span. Static check: `build.py` reads seven
`physics` attributes and every one is written by `plasma_geometry.py`, M1's *first* node;
in the other direction the physics package reads only `dr_fw_plasma_gap_inboard/_outboard` from
`build`, also written by `plasma_geometry.py`. So the reorder should be **exactly result-neutral**
— which makes it a sharp test of the dependency graph rather than a source of speedup.

**`Pulse` is the articulation point, and `k = 1`.** At
[pulse.py:158](../../../process/models/pulse.py#L158) it computes `times.t_plant_pulse_burn`
from `pf_coil.vs_cs_pf_total_burn` (M2) and `physics.v_plasma_loop_burn` (M1); `physics` reads it
back at [physics.py:504](../../../process/models/physics/physics.py#L504) and
[physics.py:948](../../../process/models/physics/physics.py#L948). `M1 -> M2 -> Pulse -> M1` is
the one cycle spanning modules. A2 confirmed at run time that it is the **only** back edge whose
value changes between sweeps.

Two further cross-module back edges are structurally present and **dead**: `build.dr_fw_inboard`
/ `dr_fw_outboard` (written by `FirstWall`, M3; read by `Build`, M2) are functions of pure
inputs, and `pf_power.vpfskv` (M3 -> `Pulse`) is the literal `20.0e0`. If a future model ever
computes `radius_fw_channel`, `dr_fw_wall` or `vpfskv`, `k` goes from 1 to 3.

**`Pulse` becomes feed-forward once the coupler is lifted.** It makes exactly two state writes —
`times.t_plant_pulse_burn` (the coupler) and `constraints.t_current_ramp_up_min`, read only by
`constraints.py:1101`, DSM row 55, downstream of everything. Post-lift the first stops being an
edge *from* `Pulse`, so `Pulse` has no consumer upstream of itself. Confirmed at run time in all
four scenarios; in `st_regression` (`i_pulsed_plant = 0`) it writes nothing at all.

**A vestige corroborates the whole picture.** `physics.py:513` still executes
`times.t_burn_0 = times.t_plant_pulse_burn` under a comment referring to "convergence loop in
fcnvmc1, evaluators.f90". `t_burn_0` has no reader anywhere in `process/`, and `evaluators.f90`
no longer exists. The Fortran original carried a **dedicated burn-time reconciliation loop**; the
Python port folded it into the generic idempotence loop and left the write behind. Burn time was
historically known to be *the* reconciliation variable. That is the organic-architecture thesis
in one dead line.

**One candidate coupler was checked and rejected.** `pfcoil.py` writes
`physics.b_plasma_vertical_required` and `plasma_fields.py` (row 10, M1) references it — but
inside `PlasmaFields.output()`, not `run()`. It does not participate in the MDA. This is trap
**T1**, and it has now produced three false positives in this project, one of them in an earlier
revision of this document.

### 1.4 What has already been measured, and what survives

| Task | Result | Status under this plan |
|---|---|---|
| **A1** (stage 0) | Gates pass 4/4; baseline counts; 94-96 % of sweeps are FD perturbations | **carried forward** |
| **A2** (module convergence) | `k = 1` confirmed; **no module is the laggard** — M1 joint-last in 82-85 % of loops; partition contribution 3.8-7.2 % | **predicate-bound — see below** |
| **A19** (frozen-input replay) | `S2` invariant under frozen inputs (2 447 loops, zero exceptions); `S1`'s fall is *entirely* the `k = 1` lift; contribution 11.3-19.5 % gross, 6.6-14.5 % netted; **laggard moves to M2** at 41.7-43.1 % of cost; **the lift is not separable** | **predicate-bound — see below** |

**The `Si` from A2 and A19 do not transfer to this plan.** Every one of them was measured under
the `objf`/`conf` predicate with its two-sweep floor. Phase A converges on coupling variables
with a floor of 1. That is a different iteration, and its sweep counts are a different quantity.
A2's and A19's numbers remain valid as statements about *the code as it stands* — and §4 uses
them as priors — but no gate in this plan may be read off them.

What **does** transfer, because it is structural rather than predicate-bound: `k = 1`, the module
decomposition, `Pulse` becoming feed-forward, the two dead back edges, the `Build` misplacement,
and A19's finding that the lift buys nothing without the partition.

---

## 2. Proposed approach

### 2.1 Two phases (D13)

**Phase A removes the optimiser entirely** and compares fixed-point architectures at fixed design
points. **Phase B** reintroduces VMCON to host the lifted coupler.

The split is not staging convenience. It buys four things:

1. **H5 is absent, not mitigated.** The dominant residual risk in the previous design was that a
   consistency constraint changes VMCON's path in ways replay cannot predict. With no optimiser
   there is no path to perturb.
2. **The metric becomes a count.** Sweeps and model evaluations are exact and reproduce
   bit-for-bit. This resolves the standing conflict between the old §6 ("primary: wall clock")
   and the project rule that no conclusion rests on a timing (I-10).
3. **VP4 becomes testable without VP5.** Without an optimiser there is no host for a lifted
   design variable — so the coupler is handled by an **outer fixed-point loop** instead. That
   **inverts the old Stage 3 -> Stage 4 dependency**: the partition no longer needs the lift to
   decouple the modules.
4. **Phase A touches no `process/` code at all** (§3.1), so it carries no D11 approval burden and
   its neutrality is trivially satisfied.

### 2.2 What "a proper fixed-point iteration" means here

Phase A does **not** reimplement the idempotence loop. It implements plain **Gauss-Seidel
(Picard) iteration** on a declared coupling-variable vector `y`:

```
y_{m+1} = G(y_m)          G = one pass over the in-loop node sequence
stop when  max_i |y_{m+1,i} - y_{m,i}| / (|y_{m,i}| + atol_i)  <  1e-6
```

with these decisions settled:

| | Decision | Rationale |
|---|---|---|
| **Floor** | **1 sweep**, not 2 | The entry state is `y0`. Nothing needs manufacturing (§1.2) |
| **`y` set** | **(b) all state written by in-loop models**, derived from the probe | Does not depend on the DSM being complete — and the DSM has produced three T1 false positives |
| **Cross-check** | **(a) DSM feedback-edge variables**, evaluated in parallel every sweep | Disagreement about when a point converged is a **DSM validation result** (§3.4) |
| **Tolerance** | `rtol = 1e-6` per component; **`atol_i` chosen and recorded per component** | Today's `np.allclose(rtol=1e-6)` carries a hidden `atol=1e-8` that dominates below `\|y\| = 1e-2` — **18.0 % of nonzero MFILE quantities**, with 203 so small that any change passes. Neither numpy's default nor zero is safe; the choice is stated, not inherited |
| **Exclusions** | accumulating fields only, each **measured and justified** in the report | Counters and accumulators never converge; an unjustified exclusion is the same class of silent defect as the NaN loophole |
| **NaN** | **never converged** | Today's `equal_nan=True` is not reproduced |
| **Acceleration** | **none** — plain Gauss-Seidel | Aitken/Anderson is a separate variant point; folding it in confounds it with the topology change |

**Hard cuts.** Inner (per-module) **20** sweeps; outer **20** iterations; and a **global budget of
200 module-sweeps per design point**. Reaching any of them marks the point **invalid** — never a
budget to be quietly consumed. The full sweep histogram is recorded so that pressure against a
cap is visible rather than inferred.

### 2.3 Arms

A **design point** is the pair `(x, y0)` — the design vector *and* the entry state it was reached
with — restored bit-identically for every arm. Not `x` alone: the entry state is what makes the
comparison paired, and it is what A19's harness already restores field by field.

| Arm | What it is | Role |
|---|---|---|
| **R — reference** | today's `call_models`, unmodified | **not a competitor.** Measures the size of the two defects in §1.2 |
| **A0 — flat** | one Gauss-Seidel loop over all in-loop nodes, converging `y` | **the control** |
| **A0f — flat, floor 2** | A0 with the two-sweep floor retained | **isolates the floor effect** from the predicate's cost (open question 4) |
| **A1 — block** | outer Gauss-Seidel over the coupler; inner Gauss-Seidel per M1/M2/M3 | the partition |

The **feed-forward hoist** (`CsFatigue`, rows 52-55, and `Pulse` when the coupler is lifted) is
applied to **both** A0 and A1 in the first results, so it cancels and the comparison is purely
topological. The framework builds it as a toggle (VP2) so a later run can isolate it.

Q4 is settled in favour of merit over mimicry: **A0 is a correct implementation, not a
reproduction of today's loop.** R exists precisely so that the artefact's size is measured rather
than argued.

### 2.4 Protocol

**Harvest.** One instrumented baseline run per scenario saves `(x, y0)` at every `call_models`,
cached to disk so the harvest is paid once rather than per arm.

**Subsample.** All `fn` and `grad_reconcile` points, plus **1 in 5** `grad` points. 94.5 % of
points are gradient perturbations, and A19 §5.2 established they behave no differently
(3.19 sweeps against `fn`'s 3.53 on `large_tokamak_nof`). This is what keeps a full four-scenario,
three-arm pass inside a few minutes (§3.3).

**Exit audit — this is how "matched final accuracy" is enforced.** On termination every arm gets
one further full sweep and the **same global residual** is evaluated and recorded. If A1
terminates at a larger global residual than A0, their counts are not comparable and the report
must say so. Matched accuracy is *verified per point*, not assumed from a shared tolerance
setting.

**Pairwise drop.** A design point enters the comparison only if **every** arm converged it.
Dropped points are reported with their count and their arm attribution beside every result —
because a control that cannot converge a point is itself a finding about the code as it stands.

**Phase B**, once Phase A has a result: lift `t_plant_pulse_burn` to VMCON as design variable 178
with a consistency constraint, and ask the sharper question — **does hosting the coupler on the
optimiser beat hosting it on an outer fixed-point loop?** — with Phase A's winner as the control.
H5 returns here, and here it can be measured.

---

### 2.5 Phase B, and how H5 gets measured

**H5** is the risk that adding a consistency constraint changes the optimiser's behaviour enough
to consume the saving. It is the one thing replay cannot reach, and it needs a protocol designed
before the run rather than an interpretation afterwards.

**The difficulty.** The baseline solves an *n*-variable problem. The variant solves *n*+1 with an
extra equality constraint. These are different problems, so *"the variant took more optimiser
iterations"* is not evidence of anything — the two arms follow different paths through different
spaces, and a single pair of runs is one sample from each.

**1. The metric is model evaluations, never iterations.** Count every model evaluation from start
to converged solution. Evaluations are the same unit of work in both arms, are exact, and
reproduce bit-for-bit. Iteration counts are not comparable and are recorded only as diagnostics.

**2. "Converged" means all three of these, checked identically for both arms.**

- `norm_objf` agreement to a stated tolerance (decision D6);
- a post-solve feasibility audit — every constraint satisfied to a stated tolerance;
- **for the variant only: the consistency residual is within tolerance.** Without this the variant
  can "win" by returning a point that is not on the consistency manifold at all, which is not a
  solution to the same problem. This check is not optional and its omission would invalidate the
  comparison.

Never gate on iteration variables: some are not identified by the problem and differ at an
unchanged optimum (D6).

**3. Multi-start, because one run is one sample from a path distribution.** Perturb the initial
design vector and solve from each start, comparing **distributions** rather than single numbers.

- 20-30 starts per scenario, per arm.
- Perturbations are **scale-aware** — each variable multiplied by `1 + δᵢ` — and **identical
  across arms**, so the comparison stays paired.
- The variant's extra variable is initialised from the deck's own burn time, and that choice is
  stated rather than tuned.

This also delivers the robustness answer as a by-product, and **robustness outranks cost**: the
fraction of starts each arm solves (`ifail = 1`) is a first-class result. An arm that is cheaper
on the starts it solves and fails on more of them has not won.

**4. Attribution, so a loss is explained rather than reported.** If the variant costs more,
decompose it: extra *optimiser iterations* (H5 proper) against extra *evaluations per iteration*
(the `2n → 2(n+1)` gradient penalty, already measured at 4.8-5.0 %). Both are countable, and they
answer different questions — one is the constraint hurting the search, the other is a known and
predictable dimension cost.

**5. Secondary: convergence history, not just the endpoint.** Record objective against cumulative
model evaluations for every run. This distinguishes *"the variant is slower per unit of progress"*
from *"the variant took a longer path to the same place"*, which the endpoint count alone cannot.

**6. Outcomes, declared in advance.**

| Finding | Reading |
|---|---|
| Variant's median evaluation count lower, success rate no worse | the architecture wins |
| Variant's success rate worse | **H5 fails; that is the headline regardless of cost** |
| Distributions overlap substantially | inconclusive, reported as such — not resolved by picking a summary statistic |

**7. Cost.** Roughly 30 starts x 2 arms x 4 scenarios at 15-30 s each: about one to two hours. The
outputs are counts and success flags, so machine load does not threaten them.

**7a. The variant includes the hoist (D15), so name the result accordingly.** The Phase B arm carries the lift, the per-module solvers **and** the feed-forward hoist. Its headline is therefore *the proposed architecture*, never *the partition's benefit*: the hoist is separable, was measured at 4.6-8.2 % in Phase A terms, and a combined number quoted as the partition's would be a units error of exactly the kind trap T11 records. An excluding arm can be run later — the hoist is a toggle (VP2) — and until it is, the components are not separately attributable.

**8. What it cannot answer.** Whether the result transfers to other decks, other starting-point
distributions, or a different optimiser. And it is counts, not time; a timing comparison can be
added under the paired protocol but is not the evidence.

---

## 3. Implementation impact

### 3.1 Phase A changes no PROCESS code

This is the single most important implementation fact about the new design. The replay harness
calls the models' bound `run()` methods directly, as A19's already does, so the entire Phase A
comparison lives under `arch_surgery/`:

| File | Change |
|---|---|
| `arch_surgery/idf_probe/` -> `_experiment.py` | harvest hook: save `(x, y0)` per `call_models` |
| `arch_surgery/fixedpoint/engine.py` | *new* — Gauss-Seidel, predicate, caps, exit audit |
| `arch_surgery/fixedpoint/arms.py` | *new* — A0 / A1 / R construction from the node map |
| `arch_surgery/fixedpoint/ystate.py` | *new* — `y` extraction, norm, exclusion list |
| `arch_surgery/docs/data/dsm_node_map.json` | *new* — checked-in node -> row -> module map (C8) |
| `process/` | **none** |

Consequences: **no D11 approval is needed for Phase A**; switch-neutrality is satisfied by
construction because nothing in the production path changes; and the harness cannot perturb the
baseline it is measuring.

The harness must preserve two properties A19 established and proved:

- **Warm start.** In the real solve each call starts from the previous call's state. Restoring a
  saved `y0` reproduces that exactly. Replaying cold, or in shuffled order, would overstate every
  arm's cost.
- **Exact restore.** A19 verified 0 mismatched fields across all 2 288 data-structure fields in
  2 447 replays, and its full-sequence replay reproduced the coupled loop's `Si` on 7 058/7 058
  pairs. That control is not optional; it is what separates "M1 converges faster alone" from "my
  replay is broken".

**Trap T7 applies.** Ten models call `run()` from `output()`. The replay must call the *unwrapped*
bound methods captured before instrumentation, as A19's does.

### 3.2 Phase B changes PROCESS code, and needs approval

| File | Change | Gate |
|---|---|---|
| `process/core/caller.py` | VP1 (sequence), VP2 (`in_loop`), VP3 (`converged`), VP4 (`solve_blocks`) hooks | neutrality: arm-off byte-identical |
| `process/core/solver/iteration_variables.py` | append key **178** (D10 — appended, never fitted into a gap) | `IN.DAT` language divergence stated in the write-up |
| `process/core/solver/constraints.py` | append constraint **93**, `lablcc` extended in step | as above |
| `process/models/pulse.py` | residual extraction only, under the VP5 pattern | **D11 — user approval before merging** |

### 3.3 Runtime

Measured, not estimated: `large_tokamak_nof` warm in an isolated subprocess is **15.9 s internal
for 2 027 sweeps = 7.8 ms per model sequence** (an upper bound — it includes VMCON and I/O). One
full pass over all four scenarios is ~8 200 sweeps, about **64 s**.

Phase A's cost is that multiplied by however much the strict predicate raises the sweep count,
times the number of arms — and **the multiplier is the quantity Phase A exists to measure**, so it
cannot be budgeted in advance:

| If the strict predicate averages | multiplier | 3 arms, no subsample |
|---|---|---|
| ~5 sweeps | 1.6x | ~6 min |
| ~8 sweeps | 2.5x | ~9 min |
| pressed to the cap of 20 | 6.2x | ~21 min |

With the 1-in-5 `grad` subsample and a cached harvest, the **worst case falls to roughly 5 min**
and a re-run after a code change to 2-3 min. That is the configuration to build.

Peak RSS is **423 MB** (measured, same run), which closes the memory branch of I-10.

---

## 4. Expected results

### 4.1 The four effects, separately

| Effect | Expected | Basis | Confidence |
|---|---|---|---|
| ~~**Floor removal** (R -> A0)~~ **MEASURED (A18)** | **1.53 / 1.55 / 1.79 / 10.7 %** | The 0-31 % band was an upper bound needing a sweep saved on *every* solve; it is saved only where the state is already converged on entry (4.7-30 % of design points). The floor is real and an order of magnitude less valuable than claimed | **settled** |
| **Strict predicate** (R -> A0) | **negative** — more sweeps | A19: `grad_reconcile` `S2 = 5.00` against `S_global = 3.93`, i.e. a module iterated to its own criterion needs more than the loop gives it. A2: state is still moving at exit in 24 % of calls | direction certain |
| ~~**Feed-forward hoist** (both arms)~~ **MEASURED (A13)** | **6.56 / 6.76 / 6.64 / 2.63 %** of **model evaluations**, per deck | The published `4.6-8.2 %` was wrong in three particulars: its `4.6 %` end came from *wall-clock* weighting (retired under I-10), its node set included `Pulse` (which joins the tail only once A4 lifts the coupler), and its unit was **DSM rows**, not model calls — only 2 of `FF`'s 5 rows are hoistable at all (`CsFatigue` is not a driver call site; `objective_constraints` **is** the convergence test). Restating A2's own arithmetic on A13's node set and unit accounts for the entire gap with no residue. `k = 0`, no dimension penalty, separable | **settled** |
| **Block vs flat** (A0 -> A1) | **negative to +19.5 %** | A19's gross contribution, *predicate-bound*; the tight inner tolerance biases low (§5.2) | weak |

The first two act in opposite directions and **A0 vs R measures their sum, not either one**. Arm
**A0f** (strict predicate, floor kept at 2) separates them and is **built up front** (user,
2026-09-01): `R -> A0f` is the predicate's cost alone, `A0f -> A0` is the floor removal alone. It
costs one flag in the engine, and without it a near-zero sum is indistinguishable from neither
effect existing.

### 4.1a What the burn-time lift is worth, and the arithmetic that limits it

**A22 (outer-pass-census) confirmed `k = 1`, per deck, and measured what removing that one
coupler is worth to the loop.** The counterfactual is the block arm with
`times.t_plant_pulse_burn` held at its entry value, re-imposed after every model call — the
loop topology Phase B creates by making the burn time an optimiser input:

| deck | block-arm model evaluations | burn time held fixed | change | mean outer passes |
|---|---|---|---|---|
| `large_tokamak_nof` | 13 906 | 9 848 | **-29.2 %** | 2.7047 -> 1.9530 |
| `low_aspect_ratio_DEMO` | 28 070 | 19 774 | **-29.6 %** | 2.7205 -> 1.9495 |
| `large_tokamak_eval` | 618 | 418 | **-32.4 %** | 2.4000 -> 1.7000 |
| `st_regression` | 9 917 | 9 917 | 0.0 % | 2.1389 (no burn-time coupler) |

**This is not Phase B's expected saving, and quoting it as one would repeat T11.** Three
conditions cut it down, and the third is not bounded by anything measured so far.

1. **It is the block arm against itself**, over one deck's harvested design points, at
   tau = 1e-6. It is not the block arm against today's driver, which is Phase B's baseline
   (D14). Phase B's own comparison has to be run.
2. **The lift costs a design variable.** These decks carry 20, 19, 14 and 2 `ixc` entries;
   the lift makes that 21, 20, — and 3. PROCESS takes central differences, so a gradient
   evaluation costs `2n` MDA solves, and one more variable is `1/n` more: **+5.0 %** on
   `large_tokamak_nof` and **+5.3 %** on `low_aspect_ratio_DEMO`. *(Stated against the*
   ***current*** *cost. A19's `4.8-5.0 %` is the same penalty against the* ***new*** *cost,
   `1/(n+1)`. Both are correct; neither is meaningful without the denominator, which is the
   T11 failure mode. Everything below uses the current-cost form.)* Composing:
   `1.050 x 0.708 = 0.743` and `1.053 x 0.704 = 0.741` — about **-26 %** on model
   evaluations, *if the optimiser's major-iteration count does not change*.
3. **Nothing bounds whether it changes.** Adding a variable and a consistency constraint
   changes the SQP subproblem VMCON solves. The major-iteration count could move in either
   direction by more than 26 %, which is precisely why H5 measures the paired distribution
   over 20-30 multi-starts rather than a single run, and why robustness outranks cost
   (D15).

**The pin arm is a topology probe, not a candidate architecture.** Holding the burn time
away from its self-consistent value moves the exit objective on `low_aspect_ratio_DEMO` by a
median relative 4.9e-4 and a maximum of 3.6e-1 over 297 points. Phase B must drive the
burn-time residual to zero through a constraint, and equivalence is a gate it still has to
pass — the -29 % is the loop-side saving that becomes available *once that gate passes*, not
before.

**What the census cost the premise, and what it cost nothing.** M1 (Physics) is the module
that re-solves — on 112/149, 229/297 and 7/10 points — and the five fields it rewrites are the
same five on every such point, all written by `physics`, all burn-time-dependent:
`times.t_burn_0`, `times.t_plant_pulse_plasma_present`, `times.t_plant_pulse_total`,
`physics.vs_plasma_burn_required`, `physics.vs_plasma_total_required`. M2 never re-solves.
The burn time itself is never the moving field — it settles in pass 1; the cost is the
one-step lag from M1 running before `pulse` in the block order. That is `k = 1` behaving as a
single one-step cycle should, and it costs exactly one outer pass.

### 4.1b The burn-time site is closed-form, not a root-find — corrected by A24

**Framework §2.5 and every brief before A24 described the VP5 default as "the existing inner
root-find". For the burn time that is wrong.** `Pulse.run` assigns a closed-form expression in one
statement: `t_burn = abs(vs_cs_pf_total_burn) / v_plasma_loop_burn - t_fusion_ramp`. There is no
iteration at the site at all.

Three consequences, and the second is the one that constrains what Phase B may claim:

1. **The extraction was easier and safer than budgeted.** D14(b)'s "structural only" is met with no
   judgement call — the arithmetic moved character for character into `burn_time_root`, and the
   bit-identity gate over 121 295 quantities confirms it.
2. **Lifting the burn time removes no inner-solve work, because there is none to remove.** A4/A25
   must never describe its result as "removing an inner solver". What the lift buys is a change of
   **loop topology** — the one-step cycle `pulse → physics` disappears, which is exactly what A22
   measured at −29.2 / −29.6 / −32.4 % of model evaluations. That is the whole mechanism, and
   §4.1a's arithmetic already accounts for it correctly.
3. **The expectation does not transfer to A9–A11.** Those subdriver sites *are* genuine nested
   root-finds, so the subdriver-lift experiment's cost model is a different one and cannot borrow
   this result in either direction.

### 4.2 What would count as the existence proof

Any **one** of these, measured fairly and reported with its dropped-point census:

- **A0 vs R** significantly below 1.0 in model evaluations at matched or better final accuracy —
  i.e. a correct fixed-point implementation is cheaper than the incumbent loop *and* converges
  something the incumbent does not. This is the most likely winner and the least invasive change
  in the whole portfolio.
- **The hoist**, on its own, at 4.6-8.2 % with `k = 0` and bit-identical results.
- **A1 vs A0** significantly below 1.0 on any scenario.

`st_regression` is the most promising scenario for the third **on the evidence, and the weakest on
the instrument**: it has zero live cross-module back edges (`i_pulsed_plant = 0`, so `Pulse` writes
nothing), the largest module-convergence gaps of the four, and A19 put its partition contribution at
18.0-18.1 %. It needs no lift at all, which makes it the one scenario where the partition is
available with `k = 0`.

**Its module boundaries were an extrapolation, and have now been checked (V6, RESOLVED
2026-09-01).** `st_regression`'s own collapsed DSM was regenerated and the three-module partition
**survives**: zero new cross-module cells, nine lost, boundaries intact, up to two
boundary-respecting model substitutions that our runtime-derived node map already covered. **The
pre-committed withdrawal does not fire and the caveat is lifted.** The two large tokamaks still
lead the write-up, on the separate ground that their DSM was generated for exactly their
configuration.

### 4.3 What the experiment produces even if every arm ties

A quantified account of the driver's convergence behaviour under a correct predicate: how many
sweeps the real problem needs when the state — rather than a functional of it — is converged, how
often the incumbent loop stops early, and which coupling variables are the last to settle. A2 and
A19 already produced publishable critique from measurement alone; Phase A extends it to the
predicate itself.

---

### 4.4 Robustness — expected to change, in both directions

Robustness is not a side effect here; **Phase A converts it from an assumption into a measured
quantity**, and the drop census (§2.4) is the measurement. Today's loop supplies no robustness
signal at all: `call_models_nonconverged = 0` on every scenario, so the incumbent never fails and
there is nothing to compare. Every Phase A arm will produce a failure rate, which is new
information regardless of how the cost comparison lands.

**Expected improvements**

- **Gradients stop being differenced across unconverged states.** The loop currently exits with
  state still moving in 24 % of `large_tokamak_nof`'s calls, and 94-96 % of calls are FD stencil
  points — so this is the mechanism behind F2/F3, and a state-based predicate removes it. This is
  the strongest robustness argument in the plan, and it predicts *fewer* VMCON retries, not more.
- **The NaN loophole closes.** `equal_nan=True` currently reports a NaN state as converged
  (§1.2). Detecting it is strictly better than propagating it.
- **Failure becomes localised.** Under the block arm a module that will not converge is
  identifiable *as that module*. Today an unconverged quantity anywhere costs sweeps and then
  exits quietly.

**Expected degradations**

- **A strict predicate will fail where a loose one always succeeded.** This is the big one, and it
  is not a regression in the code's behaviour — the non-convergence was always there, unreported —
  but as delivered software it converts silent tolerance into loud failure. Whether that reads as
  more or less robust depends on which property is being valued, and the report must say which.
- **Models evaluated off the consistency manifold may raise.** Per-module solvers present states
  the coupled loop would never produce. A19 is strong evidence against this: **every module ran in
  isolation without raising, in all 2 447 replays**. But those replays used the loose predicate;
  strict iteration pushes further from the manifold.
- **Phase B only — H5.** An equality consistency constraint changes the geometry of the feasible
  set, so previously feasible starting points may not be. Unmeasured, and unmeasurable by replay.
- **Phase B only — `n` rises by 1**, costing 4.8-5.0 % in gradient evaluations and whatever
  generic difficulty a higher-dimensional SQP problem carries.

**Block Gauss-Seidel's own convergence basin is a low risk here**, specifically because `k = 1` and
A19 measured `S2` to be insensitive to the coupler: the outer iteration should be near-trivial.
That reasoning does not transfer to a deck where the coupler is live and strong.

## 5. Critical assessment

### 5.1 What is strong

**The economics are excellent, and measured.** 94-96 % of all sweeps are finite-difference
gradient perturbations, and each one is a full MDA solve. At 2 027 sweeps x 7.8 ms the MDA is
**~89 % of runtime**. So a per-call saving multiplies across essentially the whole run. This
sharpens the architecture evaluation's summary line, *"derivatives are the bottleneck, not the
architecture"*: derivatives are the bottleneck **because each derivative component costs a full
MDA solve**, and cutting MDA cost per call is how you attack that without touching a model or
writing an adjoint.

**`k = 1`.** The previous IDF plan died on the lift penalty — gradient cost scales as `n + k + 1`,
and at `n = 14-20` a `k ~ 10` lift ate the saving. Lifting **one** variable costs 4.8-5.0 % (A19,
measured against the confirmed `2n` central-difference stencil). And Phase A avoids even that,
because an outer loop hosts the coupler for free.

**The partition is derived, not assumed.** The modules come out of the DSM and the articulation
point falls out of the same analysis rather than being posited.

**It is cheap to abandon.** No `process/` edits, a few minutes per pass, and the reference arm
alone produces a result.

### 5.2 Where it is most likely to break

**The tight inner tolerance is conservative against the partition — deliberately, and it must be
reported that way.** Converging M1 to `1e-6` against an outer coupler value that is about to
change is the known-inefficient regime for block methods; flat Gauss-Seidel never pays it because
it has no inner loop to over-solve. So **if A1 loses, the result does not distinguish "the
partition does not help" from "the partition was run in its worst configuration"**, and the report
must state the loss as an upper bound. Inner tolerance is the first axis to open if that happens.

**M2 is the laggard under partitioning, and M2 is not small.** §5.3's mechanism needs the global
loop to be driven by a *small* module. A19 found the laggard moves from M1 to M2, which is 10 of
46 module nodes but **41.7-43.1 % of measured cost**. The condition is still not met. This is the
strongest single argument against A1 winning, and it is stated rather than netted away.

**A correct predicate may not converge where a loose one always did.** Today's loop never hits its
cap of 10 (`call_models_nonconverged = 0`, measured). Under a strict predicate some points will
not converge — possibly in **A0, the control**. That would be a significant finding about the code
as it stands, and simultaneously a censoring problem: the pairwise-drop rule keeps the comparison
honest but shrinks the sample, and a large drop set makes the remaining comparison unrepresentative
of exactly the hard points that matter. **Report the drop census first, before any ratio.**

**The exclusion list is a silent-failure surface.** Excluding a field that genuinely couples would
declare convergence that has not happened, in every arm at once, invisibly. Hence the requirement
that each exclusion be measured and justified rather than asserted.

**Models may raise off the consistency manifold.** Physics models can be presented states the
idempotence loop would never have produced. Budget guard work as real work.

**A fixed point may not exist at every design point.** Gauss-Seidel converges only where the
iteration is contractive. The loose predicate has been hiding non-convergence, not preventing it.

### 5.3 The mechanism, and why it is weaker than it first looks

Independence of the modules does not by itself make three loops faster than one. Compare:

- **Flat:** one un-converged quantity anywhere re-runs all 52 nodes. Cost ~ `S_global x |all|`.
- **Block:** each module iterates alone and the feed-forward nodes leave the loop entirely.
  Cost ~ `S1 x |M1| + S2 x |M2| + S3 x |M3| + 1 x |FF|`.

With `|M1| = 24`, `|M2| = 10`, `|M3| = 12`, **the saving is real only if the modules need
materially different sweep counts, and specifically only if a *small* module is driving the
loop.** A2 measured that they stop changing together and M1 — the big one — is joint-last in
82-85 % of loops. A19 then showed that under partitioning the laggard becomes M2, also not small.
Both measurements were made under the old predicate and neither transfers directly, but neither
gives any reason to expect the condition to be met under the new one.

**Node counts are the weighting.** The measured-cost weighting is retired for anything a
conclusion depends on: I-10 showed a feed-forward cost weight moving 6.4 % -> 4.4 % across runs of
identical code, which had already reached the arithmetic behind a gate decision.

### 5.4 Threats to validity

| Threat | Handling |
|---|---|
| Sweep count measures the exit criterion, not the coupling | The exit audit (§2.4) verifies matched final accuracy per point. This is the threat Phase A exists to remove |
| Arms compared over different populations | Pairwise drop; drop census reported before any ratio |
| The trajectory is not stable — a different predicate would visit different design points | **Accepted, not engineered around.** Phase A measures cost-to-converge *these* points from *these* entry states. It is a per-point mechanism result, not a re-run solve. Sound for an existence proof; insufficient for an adoption decision, which is Phase B's job |
| DSM misses an edge | `y` set (b) does not depend on the DSM; set (a) runs as cross-check; disagreements become DSM findings, recorded in [`../reports/DSM_VALIDATION.md`](../reports/DSM_VALIDATION.md) |
| ~~DSM was generated for a different configuration~~ | **CLOSED (V6, 2026-09-01)** by regenerating per-scenario DSMs. The partition survives on both inspection scenarios — `low_aspect_ratio_DEMO` identically (55/55 cross-module cells), `st_regression` with zero new cross-module cells and two substitutions our runtime-derived map already carried. Row mapping independently confirmed to land on exact semantic boundaries |
| `run()` / `output()` conflation | Trap T1, three instances. The instrument excludes `output()` paths; the replay calls unwrapped bound methods (T7) |
| `i_pulsed_plant` splits the coupling graph | Never pool pulsed and steady-state results |
| Four scenarios, tokamak only | No claim about stellarator, IFE or unsampled configurations. `st_regression` also sets `itart = 1`, a different TF path — coverage, not a replicate |

### 5.5 Scope limits stated up front

Four scenarios. Tokamak only. Phase A is a **per-point mechanism measurement** with the optimiser
absent — it cannot speak to optimiser iteration count, and it does not claim to. The design points
come from a baseline VMCON trajectory, so Phase A's answer is "block beats flat *on the points the
baseline visited*", not a claim about the design space.

---

## 6. Open questions

**Tracked, not blocking** (user, 2026-09-01):

1. **Do the two dead back edges ever come alive?** `build.dr_fw_inboard/outboard` and
   `pf_power.vpfskv` are structurally present but constant in this deck. Any change making
   `radius_fw_channel`, `dr_fw_wall` or `vpfskv` computed would raise `k` from 1 to 3. **Keep
   under observation** — re-check whenever the base commit's relationship to upstream is revisited.
2. **Is `t_burn_0` truly dead**, or read through an MFILE path outside `process/`? It is written by
   `physics` every sweep and is one of the fields still changing at loop exit in
   `large_tokamak_nof`, so it costs sweeps as well as bytes. **Keep under observation.**

**Closed:**

3. ~~How many upstream commits separate `c0ae5b28` from `ukaea/main`?~~ **Not relevant at this
   time** (user, 2026-09-01). Revisit only if the write-up needs to state drift.
4. ~~Does the fourth arm get built up front?~~ **Yes — build it up front** (user, 2026-09-01).
   Arm **A0f**: strict coupling-variable predicate with the floor kept at 2. It separates the two
   effects that A0-vs-R otherwise measures only as a sum — the floor removal (worth up to 31 %) and
   the strict predicate's extra cost (negative). Without it, the two cancelling is
   indistinguishable from neither existing. It costs one more arm in the matrix and no new code
   beyond a flag in the engine, and it may be wanted later even if the sum comes out clearly
   signed.

**Arm matrix, settled:** `R` (today's loop, reference) · `A0` (flat, floor 1 — control) ·
**`A0f`** (flat, floor 2 — isolates the floor effect) · `A1` (block, floor 1). Hoist applied to all
of them in first results, so it cancels.
