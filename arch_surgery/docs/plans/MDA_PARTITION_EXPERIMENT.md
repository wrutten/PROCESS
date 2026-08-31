# MDA partitioning experiment — plan

> **Document status** — CURRENT · plan for the MDA partition experiment · last revised
> 2026-08-31 against A2 (module-convergence)'s measurements.

**Status:** **Stage 0 COMPLETE** (A1, merged `e9747707`). **Stage 1 COMPLETE (A2,
module-convergence) and its gate STOPS the study** — see the Stage 1 section and §3.2. Stages 3-5
are not authorised on this evidence. · **Base commit:** `c0ae5b28` · **Branch:**
`architecture_surgery`

**Scope:** tokamak only. Stellarator and IFE take an early return in `_call_models_once`
and are out of scope throughout.

---

## 0. What this experiment is, and what it is not

The question is whether **the arrangement of solvers and optimisers alone** — with every
physics and engineering model left exactly as upstream wrote it — measurably changes the
cost of solving PROCESS.

That constraint is what distinguishes this from `functional_PROCESS`. A rewritten back-end
cannot answer the architecture question, because any measured difference confounds the
architecture with the rewrite. Here the models are frozen at `c0ae5b28`; only the driver
changes. A full IDF/MDF/SAND comparison on the rewritten back-end is a separate, later
study, and this experiment is not a stepping stone to it — it is the control it will need.

**Superseded work.** The earlier IDF experiment plan and its Stage-0 probe measured
`710a75c9` and are retained for methodology only. Every number in them is stale and none is
carried into this plan as evidence.

---

## 1. The hypothesis

`Build` is called earlier in the sequence than its module membership warrants, and
`times.t_plant_pulse_burn` is the only variable closing a cycle across the whole model
sequence. Moving `Build` to after `PlasmaConfinementTime` and lifting `t_plant_pulse_burn`
to the optimiser as a design variable with a consistency constraint should leave three
mutually independent modules, each with internal cycles of its own. Giving each module its
own solver should reduce wall-clock time to solution without increasing the number of
optimiser iterations.

Testable claims:

| | Claim | Status |
|---|---|---|
| **H1** | `Build` sits inside Module 1's span but belongs to Module 2 | **Supported** (§2.2) |
| **H2** | `t_plant_pulse_burn` is the only variable closing a cross-module cycle | **CONFIRMED at run time** (A2). `k = 1`: it is the only back edge whose value changes between sweeps. Two further back edges exist and carry constants — see §2.3 |
| **H3** | After the reorder and the lift, the three modules are independent | **Supported** — with the lift there is no live cross-module back edge left, and `st_regression`, which lacks the coupler structurally, already has none (A2 §7) |
| **H4** | Per-module solvers reduce wall clock | **REFUTED in prediction** (A2). The modules converge *together*: predicted saving beyond the separable feed-forward hoist is 2.3-7.2 % on the two large pulsed tokamaks, and negative under the pessimistic treatment of censored counts. See §3.2 |
| **H5** | It does not cost optimiser iterations | Untested, and now moot — H4's failure means the lift is not worth making for performance |

---

## 2. What the code and the DSM say

Findings below are from `c0ae5b28` and from
`dependency_analysis/output/tokamak/dsm_collapsed.html` (regenerated 2026-08-31, pin
`PROCESS_at_36ac820e`, which descends from `c0ae5b28` — so the coordinate systems match).

### 2.1 The module decomposition

The collapsed DSM's 56 rows, with the proposed partition:

| Rows | Contents | Role |
|---|---|---|
| 1–3 | `COOR_SingleRun`, `VMCON`, `MDA_Idempotence` | driver stack |
| **4, 6–28** | `PlasmaGeom`; `Physics` … `PlasmaConfinementTime` | **Module 1 — Physics** (24 nodes) |
| **5, 29–37** | `Build`; `CICCSuperconductingTFCoil` … `pfcoil_functions` | **Module 2 — Coils** (10 nodes) |
| 38 | `CsFatigue` | feed-forward, between M2 and M3 |
| **39** | **`Pulse`** | **the articulation point — see §2.3. Becomes feed-forward once lifted** |
| **40–51** | `Divertor` … `Availability` | **Module 3 — Plant** (12 nodes) |
| 52–55 | `WaterUse`, `Costs`, `Objective`, `Constraints` | feed-forward outputs |
| 56 | `MDA_Output` | — |

Each of the three modules contains internal cycles in the collapsed DSM, so each warrants a
solver of its own. Note the size asymmetry: **M1 is more than twice M2 or M3**. §3.2 turns on
that fact.

### 2.2 H1 — `Build` is misplaced, and moving it is safe

`Build` is DSM row **5**, i.e. Module 2, but `_call_models_once`
([process/core/caller.py:249](../../../process/core/caller.py#L249)) executes it at sequence
position **4** — between `plasma_geom` and `physics`, inside Module 1's span. The execution
order therefore interleaves the modules as M1, M2, M1…, M2…, which is what prevents wrapping
a solver around a contiguous span. **The reorder is the enabler for the whole partition**,
not a source of speedup in itself.

Static confirmation that the move is safe: `build.py` reads seven attributes from the
`physics` namespace (`i_single_null`, `itart`, `kappa`, `rmajor`, `rminor`, `triang`,
`triangularity`), and every one is written by `plasma_geometry.py` — Module 1's *first* node,
row 4 — not by anything later in Module 1. In the other direction the physics package reads
only `dr_fw_plasma_gap_inboard` / `_outboard` from `build`, both also written by
`plasma_geometry.py`. Intersecting build's 41 writes against the physics package's 516
accesses leaves `physics.itart` and `divertor.n_divertors`, both configuration flags.

So `Build` depends on `PlasmaGeom` only, and nothing between rows 6 and 28 depends on
`Build`. Moving it to after `PlasmaConfinementTime` should be **exactly result-neutral** —
which makes it a sharp test of the dependency graph (§4, Stage 2).

### 2.3 H2 — `Pulse` is the articulation point

`Pulse` is row 39 and belongs to no module. It is the node that closes M1 and M2 into a single
cycle. At [process/models/pulse.py:158](../../../process/models/pulse.py#L158):

```python
if self.data.pulse.i_pulsed_plant == 1:
    self.data.times.t_plant_pulse_burn = self.calculate_burn_time(
        vs_cs_pf_total_burn = pf_coil.vs_cs_pf_total_burn,   # Module 2 output
        v_plasma_loop_burn  = physics.v_plasma_loop_burn,    # Module 1 output
        t_plant_pulse_fusion_ramp = ...,
    )
```

`physics` reads `t_plant_pulse_burn` back at
[physics.py:504](../../../process/models/physics/physics.py#L504) and again at
[physics.py:948](../../../process/models/physics/physics.py#L948). One node, consuming from both
modules and feeding one of them, is precisely the structure that a lifted variable plus a
consistency constraint dissolves.

> **Correction (A2, 2026-08-31).** This paragraph previously also cited
> [pfcoil.py:2727](../../../process/models/pfcoil.py#L2727) as an M2-side read, making the edge
> look symmetric. **It is not on a `run()` path**: that line is inside `PFCoil.outvolt()`, whose
> only caller is `PFCoil.output()`. **Third instance of trap T1**, and it was in this plan's
> central section. Runtime instrumentation sees no read of `t_plant_pulse_burn` by `pfcoil`
> inside the MDA. The mechanism survives — `Pulse` consumes `pf_coil.vs_cs_pf_total_burn`
> (M2) and `physics.v_plasma_loop_burn` (M1) and feeds M1, so `M1 -> M2 -> Pulse -> M1` is
> still a cycle spanning both modules — but the claimed M2-side read is withdrawn.

> **Two further cross-module back edges exist, and both are dead (A2, 2026-08-31).** Runtime
> census, all four scenarios: `build.dr_fw_inboard` and `build.dr_fw_outboard` are written by
> `FirstWall` (M3, row 41) and read by `Build` (M2, row 5); `pf_power.vpfskv` is written by
> `Power` (M3, row 48) and read by `Pulse` (row 39). **Neither value changes between sweeps** —
> the first is a function of two pure inputs no model computes, the second is the literal
> `20.0e0`. So `k = 1` stands. They are recorded because they are *structurally* present: if a
> future model ever computes `radius_fw_channel`, `dr_fw_wall` or `vpfskv`, an M3 -> M2 back
> edge becomes live and the partition acquires a second and a third coupler.

**A vestige corroborates this.** `physics.py:513` still executes:

```python
# Reset second self.data.times.t_plant_pulse_burn value (self.data.times.t_burn_0).
# This is used to ensure that the burn time is used consistently;
# see convergence loop in fcnvmc1, evaluators.f90
self.data.times.t_burn_0 = self.data.times.t_plant_pulse_burn
```

`t_burn_0` has **no reader anywhere** in `process/` outside its own declaration, and
`evaluators.f90` no longer exists. The Fortran original carried a *dedicated burn-time
reconciliation loop*; the Python port folded it into the generic idempotence loop and left the
write behind. Burn time was historically known to be **the** reconciliation variable. This is
the organic-architecture thesis in a single dead line, and it is worth quoting in the write-up.

**Caveat on scope: the edge is conditional.** The whole `pulse` body is behind
`if i_pulsed_plant == 1` and the default is `0`. Of the four scenarios, `st_regression` sets
`i_pulsed_plant = 0` — it is a *steady-state spherical tokamak* (`runtitle = ST Regression`,
`itart = 1`, `aspect = 1.8`; `istell` unset, so it is a tokamak and in scope). In that case
`t_plant_pulse_burn` is never written by `Pulse` and the M1/M2 cycle this hypothesis targets
**does not exist**. It should therefore have been a free control: the partition should already
hold there.

> **Measured, and it does not behave that way (A1, 2026-08-31).** `st_regression`'s above-floor
> sweep fraction is **39.7 %** — sitting *between* `large_tokamak_nof` (37.8 %) and
> `low_aspect_ratio_DEMO` (42.1 %), not below them. With the burn-time edge structurally absent
> it does about as much reconciliation work as the two pulsed cases.
>
> This is **not a refutation**. Sweep count is not coupling; `st_regression` also differs in
> `itart` and in `nvar` (14 against 20 and 19), and §3.3's warning that sweep counts may be
> measuring the exit criterion rather than the coupling applies with full force here. But the
> cheapest test of H2 in the whole design has returned **a sign H2 does not predict**, and the
> free control this section relied on is no longer free.
>
> **RESOLVED by A2 (2026-08-31), in the hypothesis's favour.** The prediction was tested
> directly and **it holds**. `st_regression` has **zero live cross-module back edges** — its only
> back edges are the two dead `build.dr_fw_*` ones above — and `Pulse` writes nothing at all
> there. Its modules are also the most nearly independent of the four scenarios
> (`S₁ = 2.64`, `S₂ = 2.80`, `S₃ = 2.91` against `S_global = 3.31`) and it shows the largest
> predicted partition saving.
>
> **A1's 39.7 % was not diagnostic**, exactly as §3.3 warned. `st_regression` reaches a
> comparable `S_global` by a different route: each module has internal cycles needing three
> sweeps, and the loop's exit criterion adds sweeps beyond module convergence (§3.2). Sweep
> count is not coupling, and this scenario now demonstrates that rather than merely being
> caveated by it.

### 2.3a `Pulse` becomes feed-forward once the lift is made — verified

`Pulse` makes exactly **two** state writes:

| Write | Consumers | Position |
|---|---|---|
| `times.t_plant_pulse_burn` ([pulse.py:158](../../../process/models/pulse.py#L158)) | `physics` (M1), `pfcoil` (M2), `availability` (M3), `costs` | the lifted variable |
| `constraints.t_current_ramp_up_min` ([pulse.py:247](../../../process/models/pulse.py#L247)) | `constraints.py:1101` only | DSM row 55 — downstream of everything |

Post-lift the first stops being an edge *from* `Pulse`: `physics` and `pfcoil` read the
design-vector value, which originates outside the MDA. The second only ever went forward. **So
`Pulse` has no consumer upstream of itself and becomes a pure feed-forward node**, correctly placed
at row 39 between M2 and M3.

Two consequences. It resolves the plan's own open question 2. And it means `Pulse` **joins the
feed-forward set**, so the `1 × |FF|` term of §3.2 gains a node — `Pulse` would run once per
`call_models` rather than every sweep.

*(Checked with care: an earlier extraction reported a third write, `pulse.i_pulsed_plant`, which
was a regex artefact — `= ` matching `== 1`. `Pulse` only reads that switch. See trap T2.)*

> **Confirmed at run time (A2, 2026-08-31).** In all three pulsed scenarios `Pulse` writes
> exactly those two fields and nothing else. In `st_regression` (`i_pulsed_plant = 0`) it writes
> **nothing** — the `t_current_ramp_up_min` write is behind the same switch. **This closes the
> plan's open question 2: `Pulse` joins the feed-forward set.**

### 2.4 A candidate coupler, checked and rejected

`pfcoil.py` writes `physics.b_plasma_vertical_required` and `plasma_fields.py` (row 10,
Module 1) references it, which looks like an M2 → M1 back edge. It is not: the reference is
inside `PlasmaFields.output()`, a report-writing method invoked once after the solve, not
inside `run()`. It does not participate in the MDA. Recorded here because the same
false-positive shape — a name shared between `run()` and `output()` — will recur in any
name-level analysis, and Stage 1's instrument must exclude `output()` paths explicitly.

---

## 3. Critical assessment

### 3.1 What is strong about this

**The `k` economics are excellent.** The previous IDF plan died on the lift penalty: with `k`
coupling variables raised to the optimiser, gradient cost scales as `n + k + 1`, and at
`n = 14–20` a `k ≈ 10` lift ate most of the projected saving. Lifting **one** variable takes
gradient cost from `n + 1` to `n + 2` — about **5 % at n = 20**. Essentially all of any saving
survives to the bottom line. That is a far better risk/reward profile than the architecture it
replaces.

**The partition is derived, not assumed.** The three modules come out of the DSM, and the
articulation point (`Pulse`, row 39, belonging to no module) falls out of the same analysis
rather than being posited. That is the right order of operations.

**It is cheaply falsifiable.** Stage 2 predicts a bit-identical result; Stage 1's central
measurement is three instrumented baseline runs. The study can be abandoned for very little.

### 3.2 The speedup argument needs a mechanism, and it is not the one implied

H3 ⇏ H4. Independence of the modules does not by itself make three solvers faster than one
loop. Consider what each costs:

- **Today:** one un-converged quantity *anywhere* forces a re-run of **all 56 nodes**. Total
  cost ≈ `S_global × |all|`, where `S_global` is set by the slowest-converging part.
- **Partitioned:** each module iterates alone, **and the feed-forward nodes drop out of the loop
  entirely** — they run once, not `S_global` times. Total cost ≈
  `S₁ × |M1| + S₂ × |M2| + S₃ × |M3| + 1 × |FF|`.

The second term matters as much as the first: `|all|` shrinks as well as the sweep counts, because
`CsFatigue` (38), `Pulse` (39, once lifted) and rows 52–55 currently re-run on every sweep despite
feeding nothing back. **That saving is available without partitioning at all** — it is candidate E1
in the deferred register — so the partition must be credited only with what remains after it.

With `|M1| = 24`, `|M2| = 10`, `|M3| = 12`, **the saving is real only if the modules need
materially different sweep counts** — specifically, only if the global loop is currently being
driven by a *small* module. If M3 is the laggard, partitioning stops re-running M1's 24 nodes
for M3's benefit and the win is large. If **M1** is the laggard, `S_global ≈ S₁`, and since M1
dominates the node count, the partition saves almost nothing.

**This is the single most important thing to measure, and it is measurable before any refactor
is written.** Instrument the existing loop to record, per sweep, which module still has
changing state. That yields `S₁`, `S₂`, `S₃` under the current architecture and predicts the
speedup analytically. If M1 is the laggard, the honest conclusion is available for the cost of
three runs. This measurement is now the Stage 1 gate.

> **MEASURED (A2, 2026-08-31): there is no laggard, and the honest conclusion is the one this
> section anticipated.** Mean sweeps per `call_models`:
>
> | Scenario | `S_global` | `S₁` (M1) | `S₂` (M2) | `S₃` (M3) |
> |---|---|---|---|---|
> | `large_tokamak_nof` | 3.217 | 3.159 | 2.979 | 3.216 |
> | `low_aspect_ratio_DEMO` | 3.455 | 3.146 | 3.202 | 3.269 |
> | `st_regression` | 3.314 | 2.640 | 2.800 | 2.911 |
> | `large_tokamak_eval` | 2.455 | 2.455 | 2.273 | 2.455 |
>
> The three modules stop changing together. **M1 is joint-last in 82 % of `large_tokamak_nof`'s
> 630 loops and 85 % of `low_aspect_ratio_DEMO`'s 1 240**, and is never strictly ahead in either.
> `S_global ≈ S₁` is the case this section identified as fatal.
>
> **Two corrections to the arithmetic above, both from A2's measurements.**
>
> 1. **`|all|` is 52, not 56.** Rows 1-3 are the driver stack and row 56 is the output node;
>    none runs inside a sweep. The feed-forward term is rows 38 and 52-55 (5 nodes) plus `Pulse`
>    once lifted.
> 2. **Node counts are a poor cost weight.** Measured cost share inside a sweep is
>    M1 38 %, M2 41-44 %, M3 12-15 %, feed-forward 6 %, `Pulse` 0.3 %. M3 is 26 % of the module
>    nodes but 12-15 % of the work; M2 is 22 % of the nodes but over 40 %. Three nodes carry the
>    run: `physics`, `pfcoil` and the superconducting TF-coil model.
>
> **The gate result.** Predicted saving as a fraction of today's cost, with the separable
> feed-forward hoist credited separately as this section requires:
>
> | Scenario | total | of which hoist | of which **partition** |
> |---|---|---|---|
> | `large_tokamak_nof` | 8.4 % | 4.6 % | **3.8 %** |
> | `low_aspect_ratio_DEMO` | 11.8 % | 4.6 % | **7.2 %** |
> | `st_regression` | 20.4 % | 4.6 % | **15.8 %** |
> | `large_tokamak_eval` | 4.8 % | 1.7 % | **3.2 %** |
>
> (measured-cost weighting, censored per-module counts treated optimistically; under DSM node
> counts the totals are 10.2 / 15.0 / 23.2 / 8.3 % and the verdict is the same. Under the
> pessimistic treatment the partition contribution on `large_tokamak_nof` is **negative**.)
>
> **Nothing reaches the 25 % proceed threshold, and on the two large pulsed tokamaks the
> partition's own contribution is at or below the 10 % stop line.** Most of what is available is
> the hoist. Per this section's own crediting rule, the honest conclusion is that **the hoist is
> the win and the partition is not**.
>
> **A third mechanism, not anticipated here.** The loop's exit test is on the objective function
> and the constraint vector only, so state that no constraint depends on sensitively can still be
> moving when the loop declares idempotence. In `large_tokamak_nof` that happens in **24 % of
> loops**, driven almost entirely by `pf_coil.stress_z_cs_self_midplane_profile`. Per-module
> solvers converging their own state would do *more* work there, not less — which is why the
> pessimistic column can go negative, and why any future comparison "at matched final accuracy"
> (§3.3) has to confront this directly.

A second-order effect cuts the other way and is worth watching: converging M1 fully before M2
runs changes the *information* M2 receives, so per-module sweep counts under partitioning need
not equal those measured in the coupled loop. Treat the analytic prediction as an estimate to
be checked at Stage 3, not as a result.

### 3.3 Where it is most likely to break

**H5 is the real risk.** Adding an equality consistency constraint changes the geometry of the
feasible set. VMCON must now drive to zero a residual that was previously satisfied identically
by construction. Iteration count can rise, line searches can shorten, and previously feasible
starting points may no longer be feasible. The hypothesis treats "no compromise in optimiser
iterations" as the null; it should be treated as the thing most likely to fail. Note also that
this is the *only* place the optimiser sees a change — so if H5 fails, it fails cleanly and
attributably, which is a virtue.

**Sweep counts may be measuring the exit criterion, not the coupling.** The idempotence loop
has a structural floor of two sweeps and exits on a relative tolerance. If that tolerance is
loose relative to the accuracy actually achieved, part of the observed sweep count is an
artefact of the criterion. A partition that "converges faster" could then be indistinguishable
from simply loosening a tolerance. **Every comparison must be made at matched final accuracy,
not matched tolerance settings.**

**Wall clock will improve less than sweep count.** Constraint and objective evaluation, VMCON
linear algebra and output writing do not shrink when sweeps do. Quote wall clock as the
headline and treat sweep counts as a mechanism diagnostic.

**Models may not be evaluable off the consistency manifold.** Physics models can raise on
states the idempotence loop would never have presented. Budget guard/bounds work as real work,
not as a contingency.

### 3.4 Scope limits to state up front

Four scenarios, tokamak only. `i_pulsed_plant` splits them into two regimes with structurally
different coupling graphs, so results never pool across them. `st_regression` additionally sets
`itart = 1`, which activates a different TF-coil path — useful for coverage, but it is not a
replicate of the large-tokamak cases.

---

## 4. Experiment design

### Stage 0 — Re-baseline at `c0ae5b28` · **COMPLETE**

Done as A1 (stage0-rebaseline), merged `e9747707`. Report:
[`../reports/deprecated/A1_stage0_rebaseline.md`](../reports/deprecated/A1_stage0_rebaseline.md).

**All three gates PASS 4/4** under `PROCESS_surgery_env` at `n = 5`: switch-neutrality (0 differing
MFILE lines across 11 arms, on hex float literals), determinism (bit- and sweep-identical), and
`ifail = 1` on every scenario.

Measured baseline, for later stages to compare against:

| Scenario | `nvar` | constraints | `call_models` | sweeps | mean/call | above floor |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 20 | 26 | 630 | 2029 | 3.22 | 37.8 % |
| `low_aspect_ratio_DEMO` | 19 | 25 | 1240 | 4286 | 3.46 | 42.1 % |
| `st_regression` | 14 | 18 | 570 | 1891 | 3.31 | 39.7 % |
| `large_tokamak_eval` | 2 | 25 | 11 | 29 | 2.45 | 27.3 % |

Two results from Stage 0 that bear directly on this plan:

- **94–96 % of all sweeps are finite-difference gradient perturbations.** A change acting inside
  every sweep is multiplied by `2n`; a change that does not touch a perturbation is capped at a few
  per cent. This cuts *for* the `k = 1` economics of §3.1.
- **Perturbed points are systematically harder to reconcile.** 47–53 % of function-phase calls
  finish at the two-sweep floor against only 12–20 % of gradient-phase calls — which is §3.3's
  coupling-versus-exit-criterion ambiguity showing up in the baseline itself.

### Stage 1 — Per-module convergence rates (the gating stage) · **COMPLETE — GATE: STOP**

Done as A2 (module-convergence). Report:
[`../reports/A2_module_convergence.md`](../reports/A2_module_convergence.md). Instrument:
`PROCESS_IDF_PROBE=modules`, a record-only mode verified byte-identical to `control` and
`baseline` across 15 916-18 691 MFILE lines on all four scenarios.

**Outcome: `k = 1` as hypothesised, but no module is the laggard and the predicted saving does
not reach the threshold.** The stop rule below is met on two of its three clauses. Stages 3-5 are
not authorised on this evidence; Stage 2 (A3) is still worth running as an integrity check, and
the feed-forward hoist (A13 / E1), which delivers 4.6-8.2 % with `k = 0` and no change to the
optimiser's problem, should be reconsidered. The original design of the stage is retained below.


Extend the probe to attribute state change to modules: after each sweep, record which of M1 /
M2 / M3 still has changing state, and which specific entries. This gives `S₁`, `S₂`, `S₃` and
identifies the laggard, under the *current* architecture, with no refactor.

Also: confirm at runtime that `t_plant_pulse_burn` is the only variable whose read in a
`run()` path consumes a write from a later module. The instrument must exclude `output()`
paths (§2.4). Use `st_regression` as the control — with `i_pulsed_plant = 0` the burn-time
edge is absent, so any residual cross-module coupling there is *another* coupler.

**Gate — computed from exact counts, not from wall clock.** Predict the saving from
`S_global × |all|` versus `Σ Sᵢ × |Mᵢ| + 1 × |FF|`. Sweep and model-evaluation counts are exact and
reproduce bit-for-bit; **wall clock cannot resolve a 10 % effect on this machine** (I-8: worst
within-arm spread 19.6 % at `n = 5`), so it confirms rather than decides.

- Predicted saving **> 25 %** in weighted model evaluations, and `k = 1` → proceed.
- **10–25 %**, or `k = 2–3` → proceed with the expectation revised down and stated.
- **< 10 %**, or M1 is the laggard, or `k > 3` → **stop and report**. The measured per-module
  convergence structure is then itself the deliverable — a publishable quantified critique with no
  refactor. ← **this is what happened**

**Credit the partition only with what E1 would not already deliver.** The feed-forward hoist is
separable; if most of the predicted saving comes from `|FF|` rather than from `Sᵢ` differing across
modules, the honest conclusion is that the hoist is the win and the partition is not.

### Stage 2 — Reorder `Build`

Move `build.run()` to after `PlasmaConfinementTime`. Nothing else changes.

**Gate.** Results **bit-identical** to Stage 0. §2.2 predicts exactly this. A difference means
the dependency graph missed an edge, and Stage 1's conclusions are unsafe. This is a cheap
integrity check on the instrument — run it even though it is expected to be inert.

### Stage 3 — Lift `t_plant_pulse_burn`

Add it as a design variable, add a consistency constraint tying it to the value `Pulse`
computes, and remove the idempotence loop's responsibility for reconciling it. Verify the
modules are now independent before adding any solver.

**Gates.** *Correctness*: `norm_objf` agrees with Stage 0 to a stated tolerance **and** a
post-solve feasibility audit passes. Do **not** gate on iteration variables — some are not
identified by the problem and will differ at an unchanged optimum. *Robustness*: `ifail = 1`
on all four scenarios, no retries beyond baseline. *Cost*: report the `n → n+1` overhead
separately, so it is not confused with the partition's effect.

### Stage 4 — Per-module solvers

Only if Stages 1–3 pass. Wrap each module in its own solver; retire the global loop.

**Gates.** As Stage 3, plus: measured `Sᵢ` under partitioning compared against Stage 1's
predictions (§3.2), and wall clock at matched final accuracy.

### Stage 5 — Characterise

Sweep the scenario set, report pulsed and steady-state separately, and decompose the
wall-clock change into model evaluation, VMCON overhead and I/O so the mechanism is visible
rather than asserted.

---

## 5. Measurement protocol

**Primary:** wall clock to converged solution, at matched final accuracy.
**Secondary:** model evaluations, sweeps per module, VMCON iterations, solver retries.
**Correctness:** `norm_objf`, post-solve constraint feasibility, `ifail`.

**Isolation is mandatory.** `OutputFileManager` holds file handles as class attributes and
initialisation mutates a global data structure, so **every run gets a fresh subprocess and its
own working directory**. Discard the first run in a fresh environment for timing — JIT
compilation dominates it.

**Matched accuracy, not matched settings.** Before comparing, verify baseline and variant have
converged to the same place to the same precision.

---

## 6. Threats to validity

| Threat | Handling |
|---|---|
| Sweep count reflects the loop's exit criterion, not coupling | Compare at matched final accuracy; report the criterion's slack. **Confirmed real by A2**: in 24 % of `large_tokamak_nof`'s loops the state is still changing when the loop exits |
| Partitioning changes per-module convergence vs. the coupled loop | Stage 1 prediction checked against Stage 4 measurement |
| Name-level analysis conflates `run()` and `output()` paths | Instrument excludes `output()`; §2.4 is the worked example |
| Consistency constraint changes optimiser behaviour | Measured as a first-class result (H5), not assumed away |
| Models raise off the consistency manifold | Budgeted as Stage 3 work; failures reported, not silently worked around |
| `i_pulsed_plant` splits the coupling graph in two | Never pool pulsed and steady-state results |
| Four scenarios, tokamak only | No claim about stellarator, IFE, or unsampled configurations |

---

## 7. Open questions

1. ~~**Which module is the laggard?**~~ **ANSWERED (A2): none is.** The three modules stop
   changing together and M1 is joint-last in over 80 % of loops in both large pulsed cases
   (§3.2). This is the answer that stops the study.
2. ~~Does `st_regression`, with no burn-time edge, already exhibit an independent partition?~~
   **ANSWERED (A2): yes.** Zero live cross-module back edges, and the largest module-convergence
   gaps of the four scenarios (§2.3).
3. Is `t_burn_0` truly dead, or read through an MFILE path outside `process/`? If dead,
   removing it is a small independent contribution. **A2 note:** it is written by `physics` on
   every sweep and is one of the fields still changing at loop exit in `large_tokamak_nof`, so it
   costs sweeps as well as bytes.
3b. **Do the two dead back edges ever come alive?** `build.dr_fw_inboard/outboard` and
   `pf_power.vpfskv` are structurally present but constant in this deck (§2.3). Any change that
   makes `radius_fw_channel`, `dr_fw_wall` or `vpfskv` computed rather than fixed would raise `k`
   from 1 to 3.
4. How many upstream commits now separate `c0ae5b28` from `ukaea/main`, and does the write-up
   need to state that drift?
