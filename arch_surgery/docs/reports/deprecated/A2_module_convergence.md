> **Document status** — **LIVE · CURRENT**
> The task report for A2 (module-convergence), open at the time of writing. It describes commit
> **`c0ae5b28`** (branch `A2-module-convergence`, off `92b65c0c`) and its numbers are current
> evidence. It will be archived to `deprecated/` at merge; position in that folder would record
> lifecycle, not staleness (trap T3).

# A2 (module-convergence) — Stage 1: per-module convergence and the cross-module coupler set

| | |
|---|---|
| **Task** | A2 (module-convergence) |
| **Branch** | `A2-module-convergence`, in the isolated worktree `/home/wrutten/projects/PROCESS_surgery_A2` |
| **Base commit** | `c0ae5b28` (branch point `92b65c0c`) |
| **Stage** | 1 of [`../plans/MDA_PARTITION_EXPERIMENT.md`](../plans/MDA_PARTITION_EXPERIMENT.md) |
| **Environment** | `PROCESS_surgery_env`, with `PYTHONPATH` pinned to the worktree (trap T6) |
| **Date** | 2026-08-31 |
| **Status** | Complete — **the Stage-1 gate stops the study** |

**Vocabulary, once.** A *sweep* is one pass over the model sequence
(`Caller._call_models_once`). A *`call_models`* is one execution of the idempotence loop, which
repeats sweeps until the objective function and the constraint vector stop changing; the number
of sweeps it takes is **`S_global`**. The partition would replace that one loop with three, one
per module — **M1 Physics**, **M2 Coils**, **M3 Plant** — each needing **`S₁`, `S₂`, `S₃`**
sweeps of its own nodes only, with the *feed-forward* nodes (which feed nothing back) hoisted
out to run once. **`k`** is the number of variables that would have to be lifted to the
optimiser to break the cross-module cycles. *Trap T1* is the recorded failure of confusing a
model's `run()` method, which is inside the loop, with its `output()` method, which is not.

---

## 1. Verdict

**The laggard is not a small module: the three modules converge together.** In the two large
pulsed tokamaks — the primary cases — no module is meaningfully ahead of the others, and M1
Physics is joint-last in 82 % of `large_tokamak_nof`'s 630 idempotence loops. The condition
§3.2 of the plan named as the thing that would make the partition worthless is met.

**The coupler set is confirmed and it is small: `k = 1`.** `times.t_plant_pulse_burn` is the
only field whose read on a `run()` path consumes a write from a later module *and* whose value
actually changes between sweeps. Two other structural back edges exist and both carry
constants. This is the hypothesis's strongest result and it survives fully.

**Open question 1b is resolved in the hypothesis's favour.** `st_regression`, with
`i_pulsed_plant = 0`, has **zero live cross-module back edges** — exactly what H2 predicts —
and its modules are the most nearly independent of the four scenarios, with the largest
predicted partition saving. A1's 39.7 % above-floor sweep fraction was not evidence against H2;
sweep count was measuring something other than cross-module coupling.

**The gate stops the study.** Predicted saving in weighted model evaluations, computed from
exact sweep counts, is **4.8 % – 23.2 %** total; but the separable feed-forward hoist accounts
for **1.7 % – 8.2 %** of that, and **the partition's own contribution is below 10 % in three of
the four scenarios**, including both large pulsed tokamaks (3.8 % and 7.2 %). Nothing reaches
the 25 % "proceed" threshold; the two headline scenarios sit at or below the 10 % stop line
once the hoist is credited separately.

| Gate criterion (plan §4, Stage 1) | Measured | Outcome |
|---|---|---|
| Predicted saving **> 25 %** with `k = 1` → proceed | max 23.2 %, on `st_regression` under the weighting that most flatters the partition; 8.4 % and 11.8 % on the two large pulsed tokamaks | **not met** |
| **10–25 %**, or `k = 2–3` → proceed with expectation revised down | total saving is in band for 2 of 4 scenarios; `k = 1` | partially met |
| **< 10 %**, or **M1 is the laggard**, or `k > 3` → **stop and report** | partition-only saving < 10 % in 3 of 4; M1 is joint laggard in the largest case | **met — STOP** |

**Recommendation: do not proceed to A4 (burn-time-lift) or A5 (module-solvers) as a performance
measure.** The measured per-module convergence structure is the deliverable, per the plan's own
stop rule. Two smaller pieces of work are still worth doing and are argued for in §8: A3
(build-reorder) as a cheap integrity check on the dependency graph, and the feed-forward hoist
(A13/E1), which is separable, needs no lifted variable, and delivers 4.6–8.2 % on its own.

**A failed gate is a result.** No number below was tuned, re-scoped or re-run to move it.

---

## 2. Gates as they landed

### Gate N — neutrality of the Stage-1 instrument · **PASS, 4 / 4**

The new probe mode must change nothing. Three arms per scenario: `control` (switch unset),
`baseline` (the Stage-0 probe), `modules` (the Stage-1 instrument).

| Scenario | MFILE lines compared | control vs baseline | control vs modules | sweep shape baseline vs modules | `ifail` |
|---|---|---|---|---|---|
| `large_tokamak_nof` | 16 173 | 0 differing | 0 differing | identical | 1 |
| `low_aspect_ratio_DEMO` | 16 434 | 0 differing | 0 differing | identical | 1 |
| `st_regression` | 18 691 | 0 differing | 0 differing | identical | 1 |
| `large_tokamak_eval` | 15 916 | 0 differing | 0 differing | identical | 1 |

Comparison is on the whole MFILE, byte for byte, excluding only the run-metadata header
(date, time of run, user, version string, git tag, git branch, input path, measured runtime),
plus the exact hex-float signature A1 used (`norm_objf`, `sqsumsq`, the iteration-variable
vector, the constraint-residual norm). "Sweep shape identical" means the two arms agree on
total sweeps, total `call_models`, the per-phase sweep histograms and the retry count.

The instrumented run also reproduces A1's Stage-0 anatomy exactly: `call_models` totals
630 / 1240 / 570 / 11, matching [`deprecated/A1_stage0_rebaseline.md`](deprecated/A1_stage0_rebaseline.md)
to the unit.

### Gate S1 — the Stage-1 gate · **STOP**

Reported in full in §5.

---

## 3. What was measured, and how

### 3.1 The instrument

`PROCESS_IDF_PROBE=modules` selects `process/core/_idf_probe_modules.py`, which is imported
*only* in that mode, so `control` and `baseline` are untouched by its existence. It does three
things, all of them read-only with respect to model state:

1. **Node attribution.** On the first sweep it wraps the `run()` method of every model object
   the caller reaches, plus `Power.acpow`, `Power.plant_electric_production`, the design-vector
   injection and the objective/constraint block. That gives 23 runtime nodes, each mapped to a
   module by decision D8's collapsed-DSM decomposition.
2. **Write and read census.** `__setattr__` is overridden on all 36 data namespaces so an
   assignment `self.data.physics.rmajor = …` is recorded exactly, and a full snapshot of all
   2 288 data-structure fields is differenced at every node boundary, which additionally catches
   in-place numpy mutation (`arr[:] = …`) that never reaches `__setattr__`. `__getattribute__`
   is overridden to record reads. The read census ran on **every** in-loop sweep of every
   scenario (2 027 / 4 284 / 1 889 / 27), so it is a complete census, not a sample; the
   discovered-edge count is flat from sweep 3 onwards in all four runs.
3. **Per-module convergence.** After each sweep, each node's output state is compared with the
   same node's output state on the previous sweep of the same `call_models`, using
   `Caller.check_agreement`'s own predicate (`np.allclose`, `rtol = 1e-6`, `atol = 1e-8`), so a
   per-module sweep count is directly comparable with `S_global`. `Sᵢ` is the first sweep
   `s ≥ 2` at which no node of module `i` differs from sweep `s − 1` — the same shape of
   criterion the real loop uses, applied to the module's own state.

### 3.2 Trap T1, enforced structurally rather than by a filter

**Ten model objects call their own `run()` from inside their `output()` method**: `costs`,
`availability`, `pulse`, `divertor`, `structure`, `ccfe_hcpb`, `power.acpow`, `vacuum`,
`buildings`, `water_use`. Each does so three times per run, once per `finalise` call during the
final output idempotence check. Those invocations are outside the MDA.

The instrument closes the sweep at the end of `_call_models_once` and refuses any node entered
afterwards, so an `output()`-path `run()` cannot contribute a write, a read or an edge; the
refused count is reported (`output_path_calls_refused`, 30 per run). This is not cosmetic —
before the guard was added, the first smoke run reported **two extra back-edge fields**
(`tfcoil.insstrain`, `tfcoil.n_rad_per_layer`) that exist only on the output path.

### 3.3 Isolation and the timing caveat

Every run is a fresh subprocess in its own working directory, executed serially. **Trap T6**:
`PROCESS_surgery_env`'s editable install points at the *main* checkout, so every subprocess is
given `PYTHONPATH=/home/wrutten/projects/PROCESS_surgery_A2` and `run_one.py` now asserts the
**exact** tree (`<expect>/process/__init__.py`) rather than a path prefix — the prefix test A1
used passes for the main checkout as well. Verified from `$TMPDIR`, which is neither tree.

**All wall-clock figures in this report are contended and are not evidence.** A concurrent
Remote Control session was active for part of the measurement window, and I additionally
discovered mid-task that two of my own driver invocations had overlapped (the sandbox gives each
Bash call its own PID namespace, so `ps` and `pkill` could not see the other run). **That
contaminated data was deleted and every arm re-run serially.** The gate is computed from sweep
counts, which are exact and reproduce bit-for-bit; wall clock enters only as a *weighting* in
§5.2, where it is a ratio between nodes within the same run and is therefore insensitive to a
common-mode slowdown.

---

## 4. Per-module convergence — the headline measurement

Mean sweeps per `call_models`. `Sᵢ` is given as *optimistic / pessimistic*: when a module is
still changing on the loop's final sweep its `Sᵢ` is right-censored, and the two figures bound
it by `S_global` and `S_global + 1`.

| Scenario | `call_models` | `S_global` | `S₁` (M1, 24 nodes) | `S₂` (M2, 10) | `S₃` (M3, 12) |
|---|---|---|---|---|---|
| `large_tokamak_nof` | 630 | **3.217** | 3.159 / 3.224 | 2.979 / 3.222 | 3.216 / 3.281 |
| `low_aspect_ratio_DEMO` | 1 240 | **3.455** | 3.146 / 3.146 | 3.202 / 3.202 | 3.269 / 3.289 |
| `st_regression` | 570 | **3.314** | 2.640 / 2.640 | 2.800 / 2.807 | 2.911 / 2.944 |
| `large_tokamak_eval` | 11 | **2.455** | 2.455 / 2.727 | 2.273 / 2.364 | 2.455 / 2.636 |

Censoring (module still changing when the loop exits), as a count of `call_models`:

| Scenario | M1 | M2 | M3 |
|---|---|---|---|
| `large_tokamak_nof` | 41 / 630 | **153 / 630 (24 %)** | 41 / 630 |
| `low_aspect_ratio_DEMO` | 0 | 0 | 24 / 1240 |
| `st_regression` | 0 | 4 / 570 | 19 / 570 |
| `large_tokamak_eval` | 3 / 11 | 1 / 11 | 2 / 11 |

### 4.1 Which module is the laggard

| Scenario | joint-last (of `n`) | strictly last |
|---|---|---|
| `large_tokamak_nof` (n = 630) | M1 517, M3 517, M2 480 | M2 113, M1 0, M3 0 |
| `low_aspect_ratio_DEMO` (n = 1240) | M3 1075, M1 1050, M2 906 | M2 165, M3 24, M1 0 |
| `st_regression` (n = 570) | M3 353, M1 335, M2 278 | M1 121, M2 96, M3 19 |
| `large_tokamak_eval` (n = 11) | M1 11, M3 10, M2 8 | M1 1 |

**There is no laggard in the sense the plan needs.** In `large_tokamak_nof` all three modules
are still changing at the final sweep together in 480 of 630 loops, and M1 — the module the plan
identified as fatal if it lagged, because it is 24 of the 46 module nodes — is joint-last in
82 % of them and never strictly ahead. `low_aspect_ratio_DEMO` is the same picture: M1 joint-last
in 85 %.

This is the answer to the plan's open question 1, and it is the negative answer. The
partition's saving comes from *not re-running module A for module B's benefit*, and there is
almost no such waste to recover: when one module is still moving, the others usually are too.

### 4.2 The one thing that is genuinely lagging

The single most persistent laggard is not a module but a field:
`pf_coil.stress_z_cs_self_midplane_profile` (M2, written by `pfcoil`), still changing on the
loop's final sweep in **153 of 630** `large_tokamak_nof` loops — the entire M2 censoring column.
Nothing else in that scenario comes close; the next entries are `times.t_burn_0`,
`physics.vs_plasma_burn_required`, `times.t_plant_pulse_plasma_present`, `power.qac` and the
cost-of-electricity block, each at 36–41.

In `low_aspect_ratio_DEMO` and `st_regression` the late-changer list is almost empty
(`heat_transport.tlvpmw` 24 and 19, `costs.c243` 12 and 19) — those two scenarios' modules
really do settle before the loop exits.

**This is a finding about the idempotence loop, not about the partition.** The loop's exit test
is on the objective function and the constraint vector only. State that no constraint depends on
sensitively — a central-solenoid stress profile, a burn-time vestige, an electricity cost — can
still be moving when the loop declares idempotence. Per-module solvers with per-module state
criteria would *not* reproduce this behaviour: they would converge state the global loop leaves
unconverged, doing more work, not less. §6 lists this as the main threat to any future
comparison "at matched final accuracy".

---

## 5. The Stage-1 gate

### 5.1 The arithmetic

Per `call_models`, with `w` the cost of one pass over a module's nodes:

* **today** `C₀ = S_global × (w_M1 + w_M2 + w_M3 + w_Pulse + w_FF)`
* **feed-forward hoist alone (candidate E1)** `C_hoist = S_global × (w_M1 + w_M2 + w_M3) + 1 × (w_Pulse + w_FF)`
* **full partition** `C_part = S₁·w_M1 + S₂·w_M2 + S₃·w_M3 + 1 × (w_Pulse + w_FF)`

summed over every `call_models` of the run. The hoist term is separated because **it is
available without partitioning at all** and the partition must be credited only with the
remainder.

Two weightings. *DSM node counts* is the plan's own arithmetic: |M1| = 24, |M2| = 10, |M3| = 12,
|Pulse| = 1, |FF| = 5 (rows 38, 52–55), |all| = 52. *Measured cost* uses the wall-clock share of
each node inside the sweep, measured by the instrument and excluding its own snapshot work — a
ratio within a single run, not a timing claim.

### 5.2 Measured cost share — why node counts mislead

| Scenario | M1 | M2 | M3 | Pulse | FF |
|---|---|---|---|---|---|
| `large_tokamak_nof` | 38.7 % | 41.6 % | 13.0 % | 0.3 % | 6.4 % |
| `low_aspect_ratio_DEMO` | 37.7 % | 43.7 % | 12.1 % | 0.2 % | 6.2 % |
| `st_regression` | 37.6 % | 40.4 % | 15.4 % | 0.0 % | 6.5 % |
| `large_tokamak_eval` | 47.6 % | 43.0 % | 6.7 % | 0.1 % | 2.6 % |

**M3 is 12 of the 46 module nodes (26 %) but only 6.7–15.4 % of the work; M2 is 10 nodes (22 %)
but 40–44 %.** Three nodes carry the run: `physics` (37–48 %), `pfcoil` (16–28 %) and the
superconducting TF-coil model (14–26 %). Node counts overstate what a partition could save by
letting M3 go fast and understate M2. Both weightings are reported below; they agree on the
verdict.

### 5.3 The gate

Predicted saving as a percentage of `C₀`. "Partition" is the column the plan's crediting rule
asks for: what the partition delivers *beyond* the hoist.

| Scenario | weighting | censored `Sᵢ` | total | of which hoist | of which **partition** |
|---|---|---|---|---|---|
| `large_tokamak_nof` | node counts | `S_global` | 10.23 % | 7.95 % | **2.28 %** |
| | node counts | `S_global+1` | 7.38 % | 7.95 % | **−0.57 %** |
| | measured cost | `S_global` | 8.41 % | 4.62 % | **3.79 %** |
| | measured cost | `S_global+1` | 4.22 % | 4.62 % | **−0.39 %** |
| `low_aspect_ratio_DEMO` | node counts | `S_global` | 14.97 % | 8.20 % | **6.77 %** |
| | node counts | `S_global+1` | 14.84 % | 8.20 % | **6.64 %** |
| | measured cost | `S_global` | 11.77 % | 4.55 % | **7.22 %** |
| | measured cost | `S_global+1` | 11.70 % | 4.55 % | **7.15 %** |
| `st_regression` | node counts | `S_global` | 23.23 % | 8.06 % | **15.17 %** |
| | node counts | `S_global+1` | 22.96 % | 8.06 % | **14.90 %** |
| | measured cost | `S_global` | 20.37 % | 4.58 % | **15.79 %** |
| | measured cost | `S_global+1` | 20.13 % | 4.58 % | **15.55 %** |
| `large_tokamak_eval` | node counts | `S_global` | 8.26 % | 6.84 % | **1.42 %** |
| | node counts | `S_global+1` | 0.71 % | 6.84 % | **−6.13 %** |
| | measured cost | `S_global` | 4.83 % | 1.65 % | **3.18 %** |
| | measured cost | `S_global+1` | −2.54 % | 1.65 % | **−4.19 %** |

**Nothing reaches 25 %.** The maximum total is 23.2 %, on `st_regression`, under the weighting
that most flatters the partition. On the two large pulsed tokamaks the partition's own
contribution is **2.3–7.2 %** optimistically and **−0.6 % to +7.2 %** pessimistically — at or
below the stop line. The negative entries are not an artefact: if a module is still changing
when the loop exits, iterating it alone to its own criterion costs *more* sweeps than the loop
spends, and the partition loses.

**Most of the available saving is the hoist, not the partition.** In `large_tokamak_nof` and
`large_tokamak_eval` the hoist is the larger of the two contributions under both weightings.
That is precisely the outcome the plan's crediting rule was written to detect, and the honest
conclusion it prescribes: **the hoist is the win and the partition is not.**

---

## 6. The cross-module coupler set, confirmed at runtime

Every edge below was established by observing reads and writes during optimisation runs, with
`output()` paths excluded structurally (§3.2). "Back edge" means the reading module comes
*before* the writing module in the order the partition would impose (M1, M2, Pulse, M3,
feed-forward).

| Field | Edge | Changes between sweeps? | Live coupler? |
|---|---|---|---|
| `times.t_plant_pulse_burn` | `pulse` (Pulse) → `physics` (M1) | **yes** | **yes** |
| `build.dr_fw_inboard` | `fw` (M3) → `build` (M2) | no | no |
| `build.dr_fw_outboard` | `fw` (M3) → `build` (M2) | no | no |
| `pf_power.vpfskv` | `power` (M3) → `pulse` (Pulse) | no | no |

Identical in all three pulsed scenarios. **`k = 1`.**

**The two dead edges are structural, not imaginary, and should be recorded as such.**
`FirstWall.set_fw_geometry` writes `build.dr_fw_inboard = 2·radius_fw_channel + 2·dr_fw_wall`,
and `Build.run()` reads it at eight sites; neither input is computed by any model in
`process/models/`, so the value is constant throughout the MDA in this deck. `pf_power.vpfskv`
is the literal `20.0e0` assigned in `Power.pfpwr`. **If a future model ever computes
`radius_fw_channel`, `dr_fw_wall` or `vpfskv`, an M3 → M2 back edge becomes live and the
partition acquires a second and third coupler.** The DSM would not flag this, because
statically the edges are already there.

### 6.1 A correction to the plan: `pfcoil` does **not** read burn time on a `run()` path

Plan §2.3 cites two reads of `t_plant_pulse_burn` as the evidence that `Pulse` closes M1 and M2
into one cycle: `physics.py:504` and `pfcoil.py:2727`. The instrument sees only the first.
`pfcoil.py:2727` is inside `PFCoil.outvolt()`, whose sole caller is `PFCoil.output()`.

**This is the third recorded instance of trap T1**, after `physics.b_plasma_vertical_required`
and `confinement_time.py:1160`, and it landed in the plan's central section. The mechanism
survives — `Pulse` consumes `pf_coil.vs_cs_pf_total_burn` from M2 and `physics.v_plasma_loop_burn`
from M1, and feeds M1, so `M1 → M2 → Pulse → M1` is still a cycle spanning both modules and
`Pulse` is still the articulation point — but the M2-side *read* does not exist inside the loop,
and §2.3 should not claim it. Corrected in the plan on this branch.

### 6.2 `Pulse` makes exactly two state writes — confirmed at runtime

§2.3a's static finding reproduces exactly. In all three pulsed scenarios `Pulse` writes
`times.t_plant_pulse_burn` and `constraints.t_current_ramp_up_min`, and nothing else. In
`st_regression` (`i_pulsed_plant = 0`) it writes **nothing at all** — the whole body is behind
the switch, including the `t_current_ramp_up_min` write. Post-lift, `t_plant_pulse_burn`
originates in the design vector and `t_current_ramp_up_min` is read only by
`constraints.py` (DSM row 55, downstream of everything), so `Pulse` has no consumer upstream of
itself and becomes a pure feed-forward node. **The queue's open question 2 — "post-lift, does
`Pulse` join a module or remain a standalone feed-forward node?" — is closed: it joins the
feed-forward set.**

---

## 7. Open question 1b — resolved, and in the hypothesis's favour

The plan's prediction: if burn time is the only cross-module coupler, then `st_regression`,
where `i_pulsed_plant = 0` removes it structurally, should show **no cross-module back edges at
all** and its modules should already be nearly independent.

**Both halves hold.**

* `st_regression`'s only back edges are the two dead `build.dr_fw_*` ones. **`k = 0` live
  couplers**, and `Pulse` writes nothing. The prediction is met exactly.
* Its modules are the most nearly independent of the four: `S₁ = 2.64`, `S₂ = 2.80`,
  `S₃ = 2.91` against `S_global = 3.31` — gaps of 0.40 to 0.67 sweeps, the largest anywhere.
  It has the **largest** predicted partition saving of the four scenarios (15.2–15.8 %).

**So A1's 39.7 % figure was not a sign against H2.** A1 measured the fraction of `call_models`
that exceed the two-sweep structural floor, and found `st_regression` between the two pulsed
cases. The present measurement shows why that was not diagnostic: `st_regression` reaches a
similar `S_global` by a different route — its modules each have internal cycles that need three
sweeps, and the loop's exit criterion (§4.2) adds sweeps beyond module convergence. Sweep count
is not coupling, exactly as the plan's §3.3 warned; **this scenario now demonstrates that
directly rather than as a caveat.**

That is the good news for H2, and it is worth stating plainly: **the hypothesis's structural
claims are all confirmed. What fails is the economic claim built on top of them** — the modules
are decoupled enough, but they are not *unbalanced* enough for decoupling to pay.

---

## 8. What is still worth doing

**A3 (build-reorder) — yes, run it.** It is a bit-identity check on the dependency graph and
costs three runs. The measurement above strengthens its case rather than weakening it: nothing
in the read census contradicts §2.2, so the reorder should be inert, and if it is not, the whole
dependency analysis is unsafe.

**A13 / E1 (feed-forward hoist) — this is where the saving is.** It delivers **4.6 % (measured
cost) to 8.2 % (node counts)** with `k = 0`: no lifted variable, no consistency constraint, no
change to the optimiser's problem, and therefore none of H5's risk. It is the largest
architecture-only saving this study has identified. It is currently DEFERRED; on this evidence
it should be reconsidered.

**A4 / A5 (lift and per-module solvers) — no, not as a performance measure.** The gate stops
them. They would remain defensible as a *structural* demonstration — "PROCESS's MDA can be
partitioned, here is the working code" — but that is a different claim from the one the plan
set out to test, and it should be re-authorised deliberately rather than continued by momentum.

**A18 (experiment-framework) — the I-8 diagnostic changes its shape; see §9.**

---

## 9. The I-8 diagnostic — one paragraph, as commissioned

I-8 asks whether the 19.6 % within-arm wall-clock spread is machine contention or the code, and
proposes CPU time as the discriminator: a narrow CPU spread against a wide wall spread would
confirm contention. **The diagnostic does not discriminate, because these runs are
CPU-bound.** Five `control` replicates per scenario, fresh subprocess each, serial:
`large_tokamak_nof` wall mean 15.54 s, spread 13.60 %; CPU mean 15.51 s, spread **13.64 %**.
`st_regression` wall mean 15.05 s, spread 34.76 %; CPU mean 15.01 s, spread **34.77 %**. CPU
time is 99.8 % of wall time and its spread tracks wall's to two decimal places, so descheduling
is not the mechanism — the process is running the whole time. All five replicates of each
scenario produced a *single* result signature, so the work performed is bit-identical; the same
instructions are simply taking up to 35 % more CPU-seconds on some runs than others. That is
still consistent with contention, but of a kind CPU accounting cannot filter out (last-level
cache and memory-bandwidth pressure, SMT sharing, or frequency scaling on a 16-core / 7 GB box),
and it is equally consistent with anything else that changes instructions-per-cycle without
changing instructions. Load average was 1.25–2.24 throughout and a Remote Control session was
concurrent, so this window was *not* idle and the 34.8 % figure should not be quoted as a floor.
**Recommendation for A18: drop `getrusage` as the discriminator — it is already recorded, and it
answers nothing — and use either a hardware instruction/cycle counter (`perf stat`, giving IPC
directly) or thread pinning plus an isolated core. Fixing the timing protocol remains A18's job,
not this task's.**

---

## 10. Autonomous decisions, with reversal paths

| # | Decision | Why | How to reverse |
|---|---|---|---|
| 1 | **Instrumented at the granularity of the caller's `run()` invocations (23 nodes), not the DSM's 46 module nodes.** Sub-nodes inside `physics.run()` and `pfcoil.run()` are folded into their parent. | Module attribution is what the task needs, and every sub-node of `physics` is M1, every sub-node of `pfcoil` is M2 — folding them cannot move a node across a module boundary. Finer granularity would need hooks inside `process/models/`, which D11 permits only with approval, and would buy nothing for this gate. | Wrap the sub-model `run()` methods listed in `Models.__init__` the same way `_WRAP_RUN` does. The only attribution that would actually change is `CsFatigue` (DSM row 38, feed-forward), currently folded into `pfcoil` (M2) because its work is reached through `pfcoil.run()`; it is < 0.1 % of cost and the gate uses DSM node counts for the feed-forward term regardless. |
| 2 | **Defined "module `i` is converged at sweep `s`" as: every field written by every node of module `i` agrees with the previous sweep under `Caller.check_agreement`'s own predicate.** | It is the same criterion the real loop applies, applied to a different quantity, so `Sᵢ` and `S_global` are commensurable. Any looser criterion would flatter the partition. | Change `RTOL`/`ATOL` in `_idf_probe_modules.py` and re-run. A looser tolerance raises the predicted saving; it would also stop matching the loop. |
| 3 | **Reported censored `Sᵢ` as a bound (`S_global` and `S_global + 1`) rather than picking one.** | 24 % of `large_tokamak_nof`'s loops leave M2 still changing; a point estimate would hide that the partition can be *negative* there. | Quote only the optimistic column. It raises `large_tokamak_nof`'s partition contribution from −0.4 % to +3.8 % and still does not reach the gate. |
| 4 | **Weighted the gate by measured per-node cost as well as by DSM node counts.** | The plan asks for "weighted model evaluations"; node counts imply `cryostat.run()` costs what `physics.run()` costs, which is wrong by two orders of magnitude. Both are reported; they agree. | Ignore the `measured_cost` rows. The verdict is unchanged under node counts alone. |
| 5 | **Ran the read census on every sweep rather than a sampled subset.** | A sampled census can only under-report couplers, and the whole `k` result rests on completeness. Cost is ~5× wall clock on the instrumented arm, which is irrelevant because the arm is not a timing arm. | `PROCESS_IDF_PROBE_READ_BUDGET` and `..._READ_STRIDE` restore sampling. |
| 6 | **Excluded the run-metadata header from the MFILE identity check** (date, time of run, user, version, git tag, git branch, input path, runtime). | Gate N first read FAIL on one differing line per scenario, which was `Time_of_run` ticking over between two arms. Reported here rather than silently fixed. | Remove entries from `skip` in `analyse_a2.py::_mfile_lines`. With `time` restored the gate fails on a clock reading. |
| 7 | **Deleted a first, contaminated set of runs and re-ran everything serially.** | Two driver invocations overlapped without my knowing — each sandboxed Bash call has its own PID namespace, so `ps` reported no processes and `pkill` killed nothing. Concurrent runs invalidate the timing weights and, worse, one arm had been started before a probe edit. | The re-run is the only data in `runs/a2/`; nothing from the contaminated set survives. |
| 8 | **Fixed `run_stage0.py`'s `PYTHONPATH` handling and tightened `run_one.py`'s tree assertion**, though A2 is a measurement task. | Trap T6: without this, a worktree measures the main checkout, and A1's prefix assertion does not catch it. Leaving it broken would silently invalidate A3 and everything after. | `git revert` the harness hunks of `dc6ba4d2`. The Stage-0 runs would then need cwd to be the tree root. |

| 9 | **Appended the third instance to trap T1 in `arch_surgery/docs/TRAPS.md`**, together with the measured shape of the hazard (ten models call `run()` from `output()`). | T1's own text keeps a count of how often it has bitten, and this instance landed in the partition plan's central section. Recording it where the next agent will read it is the point of the file. | Revert the `TRAPS.md` hunk of `40022610`; the same material is in §3.2 and §6.1 here. |
| 10 | **Did not merge `architecture_surgery`'s `dc27a6d9` (trap T6, D11, refreshed plan) into this branch.** T6 was taken from the task brief and acted on. | Merging mid-task would have changed the tree under measurement. The orchestrator merges this branch anyway. | `git merge architecture_surgery` before review. Note that `TRAPS.md` will need a manual resolution if T6 was added near T1. |

No edit was made under `process/models/`. D11 approval was not needed.

---

## 11. Threats to this result

| Threat | Handling / residual risk |
|---|---|
| `Sᵢ` measured in the *coupled* loop need not equal `Sᵢ` under partitioning — converging M1 fully before M2 runs changes the information M2 receives | The plan flags this (§3.2) and calls the prediction an estimate. It cuts both ways and cannot be resolved without building the partition. **Residual risk: real.** The direction is not knowable a priori; the second-order effect could be larger than the 2–7 % first-order saving it would modify. |
| `Sᵢ` is right-censored where a module still changes at loop exit | Bounded, both bounds reported. Material only for `large_tokamak_nof` M2 (24 %). |
| Node-cost weights are wall clock, and wall clock on this machine is contended | Used only as a *within-run ratio*, which a common-mode slowdown does not change. The two weightings agree on the verdict, and the verdict also holds under pure node counts. |
| The read census could miss a branch never taken in these four scenarios | Census is complete over all sweeps of all four scenarios, and the edge count is flat from sweep 3. It cannot cover configurations the deck does not exercise — `i_blanket_type = 5` (DCLL), resistive TF coils, and `i_tf_turn_type = 3` are unsampled. **A coupler could exist in an unsampled configuration.** |
| Writes that assign an unchanged value are invisible to snapshot differencing | Caught independently by the `__setattr__` override; the write set is the union of the two. |
| Four scenarios, tokamak only | No claim about stellarator, IFE, or unsampled switch combinations. |
| One instrumented run per scenario | Sweep counts are exact and A1 established bit-level determinism over five replicates per scenario; five `control` replicates here reproduce a single result signature. Repetition would add nothing to a count. |

---

## 12. Reproducing this

```bash
cd /home/wrutten/projects/PROCESS_surgery_A2/arch_surgery/idf_probe
PY=/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python

# one scenario at a time, serially, on an otherwise idle machine
$PY run_a2.py --scenarios large_tokamak_nof     --arms control baseline modules --skip-warm
$PY run_a2.py --scenarios low_aspect_ratio_DEMO --arms control baseline modules --skip-warm
$PY run_a2.py --scenarios st_regression large_tokamak_eval \
                                                --arms control baseline modules --skip-warm

# the I-8 diagnostic
$PY run_a2.py --scenarios large_tokamak_nof st_regression --arms control --reps 5 --skip-warm

# gates, per-module convergence, the gate arithmetic and the coupler census
$PY analyse_a2.py --json runs/a2/_a2_report.json
```

`run_a2.py` sets `PYTHONPATH` to the tree it lives in for every subprocess and `run_one.py`
aborts if the imported tree is not exactly that one. `runs/` is untracked, per the standing
rule; `runs/a2/_a2_report.json` holds every number quoted above.

---

## 13. Change log

| Date | Entry |
|---|---|
| 2026-08-31 | Report written. Instrument (`PROCESS_IDF_PROBE=modules`), A2 harness and T6 fixes committed as `dc6ba4d2`. Gate N PASS 4/4; **Stage-1 gate STOP**. Findings: no module is the laggard and M1 is joint-last in 82 % of the largest scenario's loops; `k = 1` (`times.t_plant_pulse_burn`), with two structurally-present but dynamically-dead back edges recorded; open question 1b resolved *for* H2 (`st_regression` has `k = 0` and the most independent modules); plan §2.3's `pfcoil.py:2727` citation withdrawn as a third instance of trap T1; §2.3a and open question 2 confirmed at runtime; I-8's CPU-time diagnostic shown not to discriminate because the runs are CPU-bound. |

---

## Orchestrator's critical assessment

**Accepted, and the Stage-1 gate is upheld: the MDA partition experiment stops here.** Merged
`0c0466c5`. This is the outcome the plan was written to make possible, and reaching it in one
task rather than after building a partition is the point of gating.

### What this task did well

It **separated the two mechanisms the plan bundled together**. §3.2 warned that independence of
the modules does not imply the partition is faster, and asked for the feed-forward term to be
credited separately. A2 did exactly that, and the answer is decisive: the hoist is 1.7–8.2 %, the
partition's own contribution is 3.8–7.2 % on the two large pulsed tokamaks. Had those been
reported as one number — 4.8–23.2 % — the study would plausibly have continued on a saving that
belongs almost entirely to a change the partition does not require.

**It resolved open question 1b in the direction I did not expect, and said so.** A1's 39.7 %
looked like a warning against H2. A2 shows `st_regression` has **zero** live cross-module back
edges and is the most independent of the four scenarios. The sweep-count signal was not
diagnostic — which vindicates the plan's own §3.3 caution that sweep counts may be measuring the
exit criterion rather than the coupling, and is a useful reminder that a suggestive aggregate is
not evidence of a mechanism.

**It reported the finding that undercuts its own remaining upside.** The loop exits with M2 still
changing in 24 % of `large_tokamak_nof`'s calls. Per-module solvers would converge state the
global loop currently leaves moving — *more* work, not less. Volunteering the fact that the
pessimistic column goes negative, rather than quoting the optimistic one, is the behaviour the
protocol asks for.

### Where I push back

1. **"No module is the laggard" is a stronger claim than the data licenses, though the gate does
   not depend on it.** `S₁ ≈ S₂ ≈ S₃ ≈ S_global` is measured under the *current* schedule, where
   every module sees every other module's most recent state each sweep. That is exactly the
   condition under which per-module counts would be expected to track each other — the plan says
   as much in §3.2's second-order caveat. The measurement establishes that **no module is
   *conspicuously* slower**, which is enough to fail the gate, but it is not the same as showing
   the modules would converge at similar rates in isolation. The distinction matters only if
   someone later revives the partition; the gate outcome stands either way.

2. **The cost-weighted and node-count weightings agreeing is reassuring but not independent.**
   Both are computed from the same evaluation counts; they differ only in the weight vector. Two
   weightings of one measurement agreeing tells you the result is insensitive to weighting, not
   that it is robust to a different measurement.

3. **The I-8 result deserves more alarm than it got.** CPU time tracking wall clock to two decimal
   places while identical work varies by up to 35 % in CPU-seconds is not a contention signature
   at all — it says the *same instructions* are taking materially more CPU time run to run. That
   points at frequency scaling, cache or memory-bandwidth effects, or the WSL2 layer, not at
   scheduling. My earlier reading of I-8 as "probably contention" is not supported by this. It is
   filed as **I-10** and A18 should not assume the cause is known.

### My own error, recorded

The plan's §2.3 cited `pfcoil.py:2727` as a reader of `t_plant_pulse_burn` inside the MDA. It is
inside `PFCoil.outvolt()`, reached only from `output()` — **the third instance of trap T1, and it
was mine, in the document warning about T1.** A2 caught it and withdrew it. The live edge is
`Pulse → physics` alone, which makes the coupling structure simpler than the plan claimed, not
weaker: H2 and `k = 1` survive.

The related discovery that **ten models call their own `run()` from `output()`** is the deeper
version of the same trap and is now T7. It means instrumenting `run()` is insufficient on its own,
which invalidated two phantom edges before A2 closed the sweep at the end of `_call_models_once`.

### What follows

- **A4 (burn-time-lift) and A5 (module-solvers) are not justified as performance work.** They are
  withdrawn from the live queue, not deferred — the measurement that would have supported them has
  been taken and does not.
- **A13 (feed-forward hoist) is now the only intervention with a positive expected return** —
  4.6–8.2 % at `k = 0`, with no change to the optimiser's problem and no dimension penalty. It was
  deferred at the user's instruction before this evidence existed. **Returned to the user as a
  decision, not revived unilaterally.**
- **A3 (build-reorder)** remains worth running as an integrity check on the dependency graph, since
  it predicts a bit-identical result.
- The architectural critique is unaffected and arguably strengthened: the loop exits before its
  state converges, ten models call `run()` from `output()`, and a hand-ordered sequence leaves
  6 % of work in nodes that feed nothing back.
