# MDA partitioning experiment — plan

**Status:** draft, not yet started · **Base commit:** `c0ae5b28` (upstream PROCESS,
"Rename optimisation problem setup variables (#4481)") · **Branch:** `architecture_surgery`

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
| **H2** | `t_plant_pulse_burn` is the only variable closing a cross-module cycle | **Consistent with the evidence so far** (§2.3); Stage 1 must confirm |
| **H3** | After the reorder and the lift, the three modules are independent | Conditional on H2 |
| **H4** | Per-module solvers reduce wall clock | Untested — and see §3.2, this is *not* implied by H3 |
| **H5** | It does not cost optimiser iterations | Untested — the likeliest failure (§3.3) |

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
| **39** | **`Pulse`** | **the articulation point — see §2.3** |
| **40–51** | `Divertor` … `Availability` | **Module 3 — Plant** (12 nodes) |
| 52–55 | `WaterUse`, `Costs`, `Objective`, `Constraints` | feed-forward outputs |
| 56 | `MDA_Output` | — |

Each of the three modules contains internal cycles in the collapsed DSM, so each warrants a
solver of its own. Note the size asymmetry: **M1 is more than twice M2 or M3**. §3.2 turns on
that fact.

### 2.2 H1 — `Build` is misplaced, and moving it is safe

`Build` is DSM row **5**, i.e. Module 2, but `_call_models_once`
([process/core/caller.py:249](../../process/core/caller.py#L249)) executes it at sequence
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
cycle. At [process/models/pulse.py:158](../../process/models/pulse.py#L158):

```python
if self.data.pulse.i_pulsed_plant == 1:
    self.data.times.t_plant_pulse_burn = self.calculate_burn_time(
        vs_cs_pf_total_burn = pf_coil.vs_cs_pf_total_burn,   # Module 2 output
        v_plasma_loop_burn  = physics.v_plasma_loop_burn,    # Module 1 output
        t_plant_pulse_fusion_ramp = ...,
    )
```

and both modules read `t_plant_pulse_burn` back — `physics` at
[physics.py:504](../../process/models/physics/physics.py#L504), `pfcoil` at
[pfcoil.py:2727](../../process/models/pfcoil.py#L2727). One node, consuming from both modules
and feeding both, is precisely the structure that a lifted variable plus a consistency
constraint dissolves.

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
`if i_pulsed_plant == 1` and the default is `0`. Of the four archived scenarios,
`st_regression` sets `i_pulsed_plant = 0` — it is a *steady-state spherical tokamak*
(`runtitle = ST Regression`, `itart = 1`, `aspect = 1.8`; `istell` unset, so it is a tokamak
and in scope). In that case `t_plant_pulse_burn` is never written by `Pulse` and the M1/M2
cycle this hypothesis targets **does not exist**. So `st_regression` is not a test of the
lift; it is a **free control** — the partition should already hold there, and if it does not,
some other cross-module coupler is active.

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
- **Partitioned:** each module iterates alone. Total cost ≈
  `S₁ × |M1| + S₂ × |M2| + S₃ × |M3|`.

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

### Stage 0 — Re-baseline at `c0ae5b28`

Reinstate an env-switched probe (`process/core/_idf_probe.py` plus hooks in `caller.py`,
`solver/evaluators.py`, `solver/solver_handler.py`), written fresh against this tree. Record
per-`call_models` sweep counts and phase, model-evaluation counts, wall clock, `ifail`,
`norm_objf`, and final iteration variables, for all four scenarios.

**Gates.** (a) *Switch-neutrality*: probe disabled ⇒ bit-identical to an uninstrumented run.
(b) *Determinism*: two independent runs of one scenario agree exactly. (c) *Baseline solves*:
`ifail = 1` everywhere. **Any failure stops the study** — without exact determinism there is
no A/B.

### Stage 1 — Per-module convergence rates (the gating stage)

Extend the probe to attribute state change to modules: after each sweep, record which of M1 /
M2 / M3 still has changing state, and which specific entries. This gives `S₁`, `S₂`, `S₃` and
identifies the laggard, under the *current* architecture, with no refactor.

Also: confirm at runtime that `t_plant_pulse_burn` is the only variable whose read in a
`run()` path consumes a write from a later module. The instrument must exclude `output()`
paths (§2.4). Use `st_regression` as the control — with `i_pulsed_plant = 0` the burn-time
edge is absent, so any residual cross-module coupling there is *another* coupler.

**Gate.** Compute the predicted saving from `S_global × |all|` versus
`Σ Sᵢ × |Mᵢ|`.
- Predicted wall-clock saving **> 25 %** and `k = 1` → proceed.
- Saving 10–25 %, or `k = 2–3` → proceed, with the expectation revised down and stated.
- Saving **< 10 %**, or M1 is the laggard, or `k > 3` → **stop and report**. The measured
  per-module convergence structure is then itself the deliverable, and it is a publishable
  quantified critique without a refactor.

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
| Sweep count reflects the loop's exit criterion, not coupling | Compare at matched final accuracy; report the criterion's slack |
| Partitioning changes per-module convergence vs. the coupled loop | Stage 1 prediction checked against Stage 4 measurement |
| Name-level analysis conflates `run()` and `output()` paths | Instrument excludes `output()`; §2.4 is the worked example |
| Consistency constraint changes optimiser behaviour | Measured as a first-class result (H5), not assumed away |
| Models raise off the consistency manifold | Budgeted as Stage 3 work; failures reported, not silently worked around |
| `i_pulsed_plant` splits the coupling graph in two | Never pool pulsed and steady-state results |
| Four scenarios, tokamak only | No claim about stellarator, IFE, or unsampled configurations |

---

## 7. Open questions

1. **Which module is the laggard?** Everything turns on this and it is measurable now (§3.2).
2. Does `st_regression`, with no burn-time edge, already exhibit an independent partition?
3. Is `t_burn_0` truly dead, or read through an MFILE path outside `process/`? If dead,
   removing it is a small independent contribution.
4. How many upstream commits now separate `c0ae5b28` from `ukaea/main`, and does the write-up
   need to state that drift?
