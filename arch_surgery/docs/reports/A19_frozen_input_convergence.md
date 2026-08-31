> **Document status** — **LIVE · CURRENT**
> The task report for A19 (frozen-input-convergence), open at the time of writing. It describes
> branch `A19-frozen-input-convergence`, off `architecture_surgery` at **`bb5d440c`** (experiment
> base commit `c0ae5b28`), and its numbers are current evidence. It will be archived to
> `deprecated/` at merge; position in that folder would record lifecycle, not staleness (trap T3).

# A19 (frozen-input-convergence) — do A2's `Sᵢ` transfer to the partitioned case?

| | |
|---|---|
| **Task** | A19 (frozen-input-convergence) |
| **Branch** | `A19-frozen-input-convergence`, in the isolated worktree `/home/wrutten/projects/PROCESS_surgery_A19` |
| **Base** | `bb5d440c` on `architecture_surgery`; experiment base commit `c0ae5b28` |
| **Tests** | [`deprecated/A2_module_convergence.md`](deprecated/A2_module_convergence.md) §11 threat row 1, and [`../plans/MDA_PARTITION_EXPERIMENT.md`](../plans/MDA_PARTITION_EXPERIMENT.md) §3.2's second-order caveat |
| **Environment** | `PROCESS_surgery_env`, `PYTHONPATH` pinned to the worktree (trap T6) |
| **Date** | 2026-08-31 |
| **Status** | Complete — **the middle band: A2's STOP is neither confirmed nor overturned** |

**Vocabulary, once.** A *sweep* is one pass over the model sequence (`Caller._call_models_once`).
A *`call_models`* is one execution of the idempotence loop, which repeats sweeps until the
objective function and the constraint vector stop changing; the number of sweeps it takes is
**`S_global`**. The proposed *partition* replaces that one loop with three, one per module —
**M1 Physics**, **M2 Coils**, **M3 Plant** — each needing **`S₁`, `S₂`, `S₃`** sweeps of its own
nodes, with the *feed-forward* nodes (which feed nothing back) *hoisted* out to run once. **`k`**
is the number of variables that must be *lifted* to the optimiser — made design variables with a
consistency constraint — to break the cross-module cycles; A2 measured **`k = 1`**, the variable
being `times.t_plant_pulse_burn`, written by the `Pulse` node and read by `physics`. A *design
point* is one optimisation parameter vector `x`; 94–96 % of them are *finite-difference
perturbations* generated while VMCON builds a gradient (probe phase `grad`), the rest are the
points VMCON actually visits (`fn`) plus a trailing reconciliation call (`grad_reconcile`).
*Right-censored* means a module was still changing when the loop exited, so its `Sᵢ` was never
observed. *Trap T1* is the recorded failure of confusing a model's `run()` method, which is inside
the loop, with its `output()` method, which is not; *T7* is that ten models call their own `run()`
from `output()`.

---

## 1. Verdict

**A2's `Sᵢ` do not transfer, and A2's estimate was biased against the partition — but not by the
mechanism the task was sent to test.**

Replaying 2 447 of the four scenarios' 2 451 `call_models` invocations, with each
module iterated in isolation on frozen upstream inputs:

- **M2 is completely unaffected.** `S₂` measured with M1 solved to convergence first is
  **identical, per `call_models`, to `S₂` measured inside the coupled loop** — 629/629,
  1 239/1 239, 569/569 and 10/10 loops, all four scenarios, no exceptions. **M2 is not chasing a
  moving target.** The directional argument the task was built on is refuted for M2.
- **M1 falls, and it is entirely the `k = 1` lift.** `S₁` with M1 iterated alone is identical,
  per loop, to `S₁` measured in the *whole* untouched sequence with `times.t_plant_pulse_burn`
  pinned — 100 % of loops in all four scenarios. Nothing else about isolation matters.
- **M3 falls for both reasons.** Beyond the lift, M3 genuinely converges in fewer sweeps on
  frozen inputs, in 23–35 % of the three optimising scenarios' loops, by 1–2 sweeps.

**The gate moves, materially, and lands in the middle band.** The partition's own contribution
beyond the feed-forward hoist, recomputed with frozen `Sᵢ`:

| Scenario | A2 (published) | **A19 (frozen `Sᵢ`)** | node counts | measured cost |
|---|---|---|---|---|
| `large_tokamak_nof` | 2.3 % / 3.8 % | **11.3 – 14.9 %** | 14.94 % | 11.33 % |
| `low_aspect_ratio_DEMO` | 6.8 % / 7.2 % | **16.8 – 19.5 %** | 19.53 % | 16.80 % |
| `st_regression` | 15.2 % / 15.8 % | **18.0 – 18.1 %** | 18.10 % | 18.01 % |
| `large_tokamak_eval` | 1.4 % / 3.2 % | **−1.3 – −0.4 %** | −0.35 % | −1.28 % |

(A2's two figures are its node-count and measured-cost columns under the optimistic censoring
treatment. `large_tokamak_eval` is the one scenario where A19 is *below* A2: it is an evaluation
run of 11 `call_models` with no gradient phase, three of them right-censored, and A2's optimistic
treatment of those three flattered the partition — §7.2 shows that bound is never attained. It
carries no weight either way.)

**Nothing reaches 25 %.** The maximum partition contribution is **19.5 %**, on
`low_aspect_ratio_DEMO` under the weighting that most flatters the partition. Three of four
scenarios now sit in the plan's **10–25 % band**, whose rule is *"proceed with the expectation
revised down and stated"* — but that is the user's call, not this task's. The two large pulsed
tokamaks have moved from *below the 10 % stop line* to *inside the band*.

**Two things must be read with that number, and both cut against it.**

1. **The lift is not free, and its cost is not in this arithmetic.** Almost all of the increase
   over A2 is the `k = 1` lift. Lifting one variable takes the finite-difference gradient from
   `2n` to `2(n + 1)` perturbation calls; at `n = 20` and `n = 19`, with 95 % of all
   `call_models` being gradient perturbations, that is a **4.8 % / 5.0 % penalty on total model
   evaluations** which A2's arithmetic — and therefore the table above — does not net off. Netted,
   `large_tokamak_nof` returns to **6.6 – 10.2 %**, at or below the stop line, and
   `low_aspect_ratio_DEMO` to **11.8 – 14.5 %**. H5's risk (the consistency constraint changing
   VMCON's iteration count) is on top of that and remains unmeasured.
2. **Under the partition, M2 becomes the laggard — and M2 is 41.7–43.1 % of the measured cost, level with M1.**
   `S₂` does not move at all, so once M1 and M3 fall, M2 is joint-last in **76 %** of
   `large_tokamak_nof`'s loops and **73 %** of `low_aspect_ratio_DEMO`'s, and strictly last in
   39 % and 36 %. Plan §3.2's condition for the partition to pay — that the loop is driven by a
   *small* module — is still not met. It has moved from M1 to M2, not to a small module.

**The user's ordering reading is refuted.** The hypothesis was that `S₁ ≈ S₂ ≈ S₃` reflects M1's
bottleneck propagating downstream. It does not: M2's count is provably insensitive to whether M1
has converged. The near-equality in the coupled loop is real coupling, but it runs through the
burn-time cycle `M1 → M2 → Pulse → M1`, which inflates **M1** (and M3 through it) rather than M2.

**Everything the gates asked for held.** Gate N19 (neutrality) PASS 4/4 — 0 differing MFILE lines
in 15 916–18 691. The method control is exact: replaying the whole sweep sequence reproduces the
coupled-loop `Sᵢ` on **all 7 058 uncensored module-loop pairs**, no exceptions. Every module ran
in isolation without raising, in every one of 2 447 replays. **No number below was tuned,
re-scoped or re-run to move it.**

---

## 2. Gates as they landed

### Gate N19 — neutrality of the replay · **PASS, 4 / 4**

A19's instrument mutates the data structure and restores it. If the restore were imperfect the
optimisation trajectory would move, so `control` (probe switch unset) and `frozen` must produce
the same run.

| Scenario | MFILE lines compared | differing | exact signature identical | `ifail` |
|---|---|---|---|---|
| `large_tokamak_nof` | 16 173 | **0** | yes | 1 |
| `low_aspect_ratio_DEMO` | 16 434 | **0** | yes | 1 |
| `st_regression` | 18 691 | **0** | yes | 1 |
| `large_tokamak_eval` | 15 916 | **0** | yes | 1 |

Comparison is the whole MFILE, byte for byte, excluding only the run-metadata header (date, time,
user, version, git tag, git branch, input path, measured runtime) — exactly A2's exclusion list.
"Exact signature" is the hex-float `norm_objf`, `sqsumsq`, both iteration-variable vectors, the
constraint residual vector and its L2 norm.

Independently, the instrument verified its own restore field by field after every replay:
**0 mismatched fields in 2 447 replays**, across all 2 288 data-structure fields.

### Gate M19 — the method control · **PASS, exact**

Before trusting any isolated number, the replay must be shown to reproduce the coupled loop when
it replays *everything*. From the same saved entry state, running the untouched full sweep
sequence must give back the `Sᵢ` the live instrument recorded.

| Scenario | M1 | M2 | M3 | coupled `Sᵢ` right-censored (M1/M2/M3) |
|---|---|---|---|---|
| `large_tokamak_nof` | 588/588 | 477/477 | 588/588 | 41 / 152 / 41 |
| `low_aspect_ratio_DEMO` | 1 239/1 239 | 1 239/1 239 | 1 215/1 215 | 0 / 0 / 24 |
| `st_regression` | 569/569 | 566/566 | 550/550 | 0 / 3 / 19 |
| `large_tokamak_eval` | 8/8 | 10/10 | 9/9 | 2 / 0 / 1 |

Cells are *exact agreements / loops where the coupled value was observed*. **7 058 of 7 058.**

### Gate V19 — the validation control · **PASS, in its corrected form**

Reported in full in §4. The task's control as stated — "`S₁_alone` should closely match A2's
`S₁`, because M1 has no live back edge from M2 or M3" — **holds exactly on the two scenarios
where its premise holds** and fails on the two where the premise is wrong, in a way that is fully
diagnosed and is a property of the code rather than of the instrument.

| Scenario | `S₁_alone` == coupled `S₁`, per loop | `S₁_alone` == coupled-with-coupler-pinned `S₁` |
|---|---|---|
| `st_regression` (`k = 0`) | **569 / 569 (100 %)** | 569 / 569 |
| `large_tokamak_eval` | **8 / 8 (100 %)** | 10 / 10 |
| `large_tokamak_nof` | 386 / 588 (66 %) | **629 / 629 (100 %)** |
| `low_aspect_ratio_DEMO` | 797 / 1 239 (64 %) | **1 239 / 1 239 (100 %)** |

### Gate S1 — the Stage-1 gate, recomputed

Reported in full in §7. **Middle band (10–25 %) on three of four scenarios; nothing reaches 25 %.**

---

## 3. What was measured, and how

### 3.1 The instrument

`PROCESS_IDF_PROBE=frozen` selects `process/core/_idf_probe_frozen.py`, imported *only* in that
mode, so `control`, `baseline` and `modules` are untouched by its existence. It delegates
everything to A2's `_idf_probe_modules` — so the coupled-loop `S_global`, `S₁`, `S₂`, `S₃` and the
per-node cost shares are re-measured in the same run, per `call_models`, and are directly pairable
with the frozen numbers — and adds a **replay**.

Let `entry` be the data-structure state at the top of `call_models` (the *previous* design point's
converged state) and `post` the state when the loop returns. For each sampled loop, after the loop
has finished and A2's ordinary numbers are recorded:

| # | Replay | Purpose |
|---|---|---|
| a | whole sweep sequence, from `entry` | **method control** (Gate M19); also gives the *uncensored* coupled `Sᵢ` the loop's own exit test never reveals |
| b | M1's nodes alone, from `entry` | `S₁_alone` |
| c | then M2's nodes alone, on M1's converged output, M2 warm-started from `entry` | `S₂_frozen` |
| d | then M3's nodes alone, M1 and M2 frozen | `S₃_frozen` |
| e | M1 + `Pulse`, from `entry` | diagnostic: is the gap the articulation point? |
| f | M1 + `build`, from `entry` | diagnostic: `build` is the M2 node that runs *between* M1's two nodes |
| g | whole sequence with `times.t_plant_pulse_burn` pinned, from `entry` | **the `k = 1` lift, emulated** |
| h | (b)–(d) with the design vector injected once instead of per sub-sweep | shows the injection convention does not carry the result |

Then `post` is restored and the restore is verified field by field. Nothing else is permanent.

**The warm start is the partition's warm start, not a convenient one.** At design point `p`,
`entry` is the converged state of design point `p − 1`. A partitioned solver arriving at `p` would
solve M1 from exactly that state with the new `x`, and would then start M2 from exactly the M2
state left over from `p − 1`, now reading M1's freshly converged output. That is what (b)→(c)→(d)
does. **The gate uses this warm start.** A cold start is not defined without building the
partition — there is no state to start from — and is not reported.

### 3.2 The convergence criterion is A2's, unchanged

`Sᵢ` is the first sub-sweep `s ≥ 2` at which no node of module `i` differs from sub-sweep `s − 1`,
where "differs" is `Caller.check_agreement`'s own predicate (`np.allclose`, `rtol = 1e-6`,
`atol = 1e-8`) applied to every field the node wrote on either sub-sweep, compared at that node's
exit. Writes are captured two ways and unioned — a `__setattr__` override and a full snapshot
differenced at each node boundary, which catches in-place numpy mutation. This is character for
character A2's definition, so `Sᵢ_frozen`, `Sᵢ_coupled` and `S_global` are commensurable. The
sub-solve ceiling is 10 sub-sweeps, matching `call_models`'s own ceiling; **it was never reached**
in any sub-solve of any scenario.

### 3.3 Traps

**T7 is not regressed.** The replay calls the *unwrapped* bound methods captured before A2's
instrument wrapped them, so it never enters the node accounting at all; the sweep is still closed
at the end of `_call_models_once` and an `output()`-path `run()` is still refused there.

**T6.** Every run is a fresh subprocess in its own working directory, executed serially.
`run_a19.py` sets `PYTHONPATH=/home/wrutten/projects/PROCESS_surgery_A19` for every subprocess and
`run_one.py` asserts the **exact** tree (`<expect>/process/__init__.py`), not a prefix. Verified.

**T8.** No `pkill` and no `ps` were used; the four scenarios ran as one serial shell sequence.

**T5 / I-10.** No wall-clock figure in this report is a result. Wall clock enters only as the
*measured-cost weighting* of §7, where it is a within-run ratio — and even there it is visibly
unstable; see §7.3.

### 3.4 Coverage: every `call_models`, not a sample

The task asked for "several design points per scenario, including finite-difference-perturbed
points". Because the replay proved cheap, **every `call_models` of every scenario was replayed**,
except the first of each run, during whose first sweep the node registry is still being built.

| Scenario | `call_models` | replayed | `fn` | `grad` (perturbations) | `grad_reconcile` |
|---|---|---|---|---|---|
| `large_tokamak_nof` | 630 | **629** | 14 | 600 | 15 |
| `low_aspect_ratio_DEMO` | 1 240 | **1 239** | 30 | 1 178 | 31 |
| `st_regression` | 570 | **569** | 18 | 532 | 19 |
| `large_tokamak_eval` | 11 | **10** | 10 | — | — |

There is therefore no sampling error and no representativeness question. §5.2 reports the
perturbed and unperturbed points separately anyway, because A1 found perturbed points converge
less readily.

The replay's reconstruction of the model sequence was checked against the nodes A2's instrument
actually saw execute: **identical node sets in all four scenarios**, no node missing, none extra.
`models.tfcoil.run()` is reached in none of the four decks (`st_regression` has `itart = 1` but
`i_tf_sup = 1`, and the call requires a non-superconducting coil).

---

## 4. The validation control, and what it found

### 4.1 The premise in the brief is inexact, and the code says why

The control was stated as: M1 runs first and has no live back edge from M2 or M3, so `S₁_alone`
should match A2's `S₁`. **M2 and M3 are indeed clean — but `Pulse` is neither.** A2's own `k = 1`
result *is* a live back edge into M1: `Pulse` writes `times.t_plant_pulse_burn`, `physics`
reads it, and `Pulse` runs after `physics`. In the coupled loop M1 is therefore reading a moving
input; under the partition that variable is lifted and it is fixed.

So `S₁_alone < S₁_coupled` is the expected result, not an isolation failure — and the instrument
was made to prove which it is, three ways.

### 4.2 The field-level trace names the mechanism

Recording *which* fields keep M1 live at each sweep, in the full replay and in the isolated
replay, over all loops:

| Field keeping M1 live (sweep boundaries, over all 629 loops) | full sequence | M1 alone |
|---|---|---|
| `physics.vs_plasma_burn_required` | 764 | **0** |
| `times.t_burn_0` | 764 | **0** |
| `times.t_plant_pulse_plasma_present` | 764 | **0** |
| `times.t_plant_pulse_total` | 741 | **0** |
| `physics.vs_plasma_total_required` | 706 | **0** |
| `current_drive.big_q_plasma` | 342 | 342 |
| `physics.f_beta_alpha_beam_thermal` | 297 | 297 |
| `current_drive.f_c_plasma_bootstrap_wilson` | 293 | 293 |
| … every other field | unchanged | unchanged |

(`large_tokamak_nof`; `low_aspect_ratio_DEMO` is identical in shape — 1 418 / 1 418 / 1 415 /
1 415 / 1 351 against zero, then every other field unchanged.) The fields that separate the
two cases are **exactly the burn-time family** and nothing else. `physics.py:513` sets
`times.t_burn_0 = times.t_plant_pulse_burn`, and `physics.py:4882` carries the model author's own
comment: *"N.B. t_plant_pulse_burn on first iteration will not be correct"*.

### 4.3 Three positive controls, all exact

| Control | Result |
|---|---|
| **`k = 0` scenario.** `st_regression` has `i_pulsed_plant = 0`, `Pulse` writes nothing, and A2 measured zero live cross-module back edges. `S₁_alone` must equal coupled `S₁` there. | **569 / 569 loops identical.** Also 8/8 on `large_tokamak_eval` |
| **The lift, emulated.** Run the whole untouched sequence with `times.t_plant_pulse_burn` pinned. If the gap is the burn-time cycle, `S₁_alone` must land on it exactly. | **629/629, 1 239/1 239, 569/569, 10/10 — 100 % in all four scenarios** |
| **Adding back the suspects.** M1 + `Pulse`, and M1 + `build` (the M2 node that runs between M1's two nodes). | **Identical to `S₁_alone` in every loop of every scenario** — neither closes the gap, because with M2 frozen the `M1 ↔ Pulse` two-node cycle settles immediately |

**Reading.** M1 is exactly separable once the one lifted variable is fixed — which is precisely the
state the partition creates. There is no state leakage, no hidden coupling and no isolation
artefact. The control passes; A2's `S₁` was measuring the burn-time cycle that the partition
removes by construction.

### 4.4 No module failed to run in isolation

The task flagged that a module might raise on a state the full sequence never presents, and that
this would be a finding about feasibility more important than the number. **It did not happen.**
Across 2 447 replays, no model raised, in any module, in
any scenario. Every module iterated alone to its own criterion inside the 10-sub-sweep ceiling.

---

## 5. The measurement

### 5.1 Frozen-input `Sᵢ` against coupled `Sᵢ`

Mean sweeps per `call_models`, over every `call_models`. **Coupled** is the *uncensored* coupled
value from the full-sequence replay — a strictly better comparator than A2's censored bounds, and
the reason the "optimistic/pessimistic" columns collapse (§7.2).

| Scenario | `S_global` | `S₁` coupled → **frozen** | `S₂` coupled → **frozen** | `S₃` coupled → **frozen** |
|---|---|---|---|---|
| `large_tokamak_nof` | 3.213 | 3.226 → **2.544** | 3.226 → **3.226** | 3.283 → **2.461** |
| `low_aspect_ratio_DEMO` | 3.454 | 3.144 → **2.561** | 3.201 → **3.201** | 3.287 → **2.527** |
| `st_regression` | 3.309 | 2.638 → **2.638** | 2.800 → **2.800** | 2.938 → **2.482** |
| `large_tokamak_eval` | 2.200 | 2.400 → **2.400** | 2.000 → **2.000** | 2.300 → **2.000** |

Decomposed per loop into the part the **lift** accounts for and the part **frozen inputs** account
for beyond it (mean sweeps):

| Scenario | `S₁`: coupled → lifted → frozen | `S₂` | `S₃`: coupled → lifted → frozen |
|---|---|---|---|
| `large_tokamak_nof` | 3.226 → 2.544 → 2.544 | 3.226 → 3.226 → 3.226 | 3.283 → 2.752 → 2.461 |
| `low_aspect_ratio_DEMO` | 3.144 → 2.561 → 2.561 | 3.201 → 3.201 → 3.201 | 3.287 → 2.780 → 2.527 |
| `st_regression` | 2.638 → 2.638 → 2.638 | 2.800 → 2.800 → 2.800 | 2.938 → 2.938 → 2.482 |
| `large_tokamak_eval` | 2.400 → 2.400 → 2.400 | 2.000 → 2.000 → 2.000 | 2.300 → 2.100 → 2.000 |

**The three columns say three different things.**

- **`S₂` is flat all the way across.** Identical per loop in every scenario — 2 447 loops, zero
  exceptions. M2 is not chasing a moving target and never was.
- **`S₁` moves only at the lift.** Identical per loop between "lifted" and "frozen" in every
  scenario. Isolation adds nothing once the coupler is fixed.
- **`S₃` moves at both.** The frozen-input effect proper is a fall of 0.10–0.46 sweeps, present in
  23–35 % of loops in the three optimising scenarios (10 % in the evaluation run) and worth
  1–2 sweeps when it occurs.

### 5.2 Perturbed points behave like unperturbed points

94–96 % of the work is finite-difference perturbations, and A1 found they converge less readily.
The pattern here is mixed — `grad` sits *below* `fn` on `large_tokamak_nof` and *above* it on
`low_aspect_ratio_DEMO` and `st_regression` — and the frozen numbers track it in both directions:

| Scenario | phase | n | `S_global` | `S₁` frozen | `S₂` frozen | `S₃` frozen |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | `fn` | 14 | 3.357 | 2.857 | 3.500 | 2.357 |
| | `grad` | 600 | 3.192 | 2.550 | 3.175 | 2.450 |
| | `grad_reconcile` | 15 | 3.933 | 2.000 | 5.000 | 3.000 |
| `low_aspect_ratio_DEMO` | `fn` | 30 | 3.133 | 2.433 | 3.033 | 2.300 |
| | `grad` | 1 178 | 3.474 | 2.553 | 3.237 | 2.547 |
| | `grad_reconcile` | 31 | 3.000 | 3.000 | 2.000 | 2.000 |
| `st_regression` | `fn` | 18 | 3.111 | 2.611 | 3.056 | 2.389 |
| | `grad` | 532 | 3.338 | 2.637 | 2.820 | 2.502 |
| | `grad_reconcile` | 19 | 2.684 | 2.684 | 2.000 | 2.000 |

**No qualitative difference between perturbed and unperturbed points.** The one striking cell —
`S₂ = 5.000` on `large_tokamak_nof`'s 15 `grad_reconcile` calls, against `S_global = 3.933` — is
M2 being iterated to its own criterion where the loop stopped earlier; it is the same phenomenon
A2 reported in its §4.2 and it makes the partition *worse*, not better, on those calls.

### 5.3 The design-vector injection convention does not carry the result

The sub-solves re-inject the design vector at the head of every sub-sweep, matching what the
coupled loop does. Injecting it once instead gives **identical counts in every loop of every
scenario**. Only 0–2 of the 3–21 injected fields are ever also written by a model, and those
writes do not change any count.

---

## 6. The ordering hypothesis

Per individual `call_models`, over every loop, using the uncensored coupled counts and the frozen
counts.

| Scenario | counts | `S₁ ≤ S₂ ≤ S₃` | all three equal | joint-last M1 / M2 / M3 | strictly last |
|---|---|---|---|---|---|
| `large_tokamak_nof` | coupled | 58.0 % | 58.0 % | **82 %** / 76 % / 82 % | M2 114, M1 0, M3 0 |
| (n = 629) | **frozen** | 29.7 % | 27.3 % | 58 % / **76 %** / 30 % | **M2 247**, M1 150, M3 0 |
| `low_aspect_ratio_DEMO` | coupled | 61.7 % | 59.6 % | **85 %** / 73 % / 87 % | M2 165, M3 24, M1 0 |
| (n = 1 239) | **frozen** | 36.2 % | 24.3 % | 52 % / **73 %** / 36 % | **M2 447**, M1 310, M3 24 |
| `st_regression` | coupled | 35.3 % | 10.9 % | 59 % / 49 % / **62 %** | M1 121, M2 95, M3 19 |
| (n = 569) | **frozen** | 14.1 % | 10.7 % | 59 % / 49 % / 41 % | M2 215, M1 121, M3 19 |
| `large_tokamak_eval` | coupled | 70 % | 70 % | 10/7/9 of 10 | M1 1 |
| (n = 10) | **frozen** | 70 % | 70 % | 10/7/7 | M1 3 |

Gap distributions, `large_tokamak_nof` (counts of loops):

| | `S₂ − S₁` | `S₃ − S₂` |
|---|---|---|
| coupled | −1: 150 · 0: 365 · +1: 82 · +2: 28 · +3: 4 | −1: 114 · 0: 365 · +1: 150 |
| **frozen** | −1: 150 · 0: 217 · +1: 80 · +2: 47 · +3: 135 | −3: 2 · −2: 185 · −1: 105 · 0: 337 |

and `low_aspect_ratio_DEMO`:

| | `S₂ − S₁` | `S₃ − S₂` |
|---|---|---|
| coupled | −1: 310 · 0: 763 · +1: 45 · +2: 28 · +3: 93 | −2: 62 · −1: 103 · 0: 740 · +1: 334 |
| **frozen** | −1: 310 · 0: 358 · +1: 256 · +2: 98 · +3: 217 | −3: 93 · −2: 193 · −1: 194 · 0: 735 · +1: 24 |

**What this settles.**

- **A2's ordering statistics reproduce exactly.** M1 joint-last in 82 % of `large_tokamak_nof`'s
  loops and 85 % of `low_aspect_ratio_DEMO`'s, never strictly last in either — A2's figures to the
  percentage point, now over the uncensored counts.
- **The "M1 gates everything" reading is refuted.** If M3 could not converge before M2, and M2 not
  before M1, then freezing M1 would have to move `S₂`. It moves it in **zero** of 2 447 loops.
  M2's internal cycles set `S₂` and nothing upstream touches it.
- **The near-equality in the coupled loop is real coupling, not insensitivity — but it is the
  burn-time cycle.** Under the coupled counts all three modules agree in 58–60 % of the pulsed
  scenarios' loops; under frozen inputs that falls to 24–27 %, and the ordering `S₁ ≤ S₂ ≤ S₃`
  from 58–62 % to 30–36 %. What breaks the tie is M1 and M3 dropping, not M2 rising.
- **The laggard moves from M1 to M2.** That is better for the partition than M1 (M2 is 10 of the
  46 module nodes against M1's 24) and worse than the plan hoped: M2 is 41.7–43.1 % of the
  *measured* cost, level with M1's 40.9–42.0 %. Plan §3.2's requirement — a *small* module
  driving the loop — is still not met.

---

## 7. The gate, recomputed

### 7.1 The arithmetic, unchanged from A2 §5.1

Per `call_models`, with `w` the cost of one pass over a module's nodes, summed over every
`call_models` of the run:

* **today** `C₀ = S_global × (w_M1 + w_M2 + w_M3 + w_Pulse + w_FF)`
* **feed-forward hoist alone (candidate E1)** `C_hoist = S_global × (w_M1 + w_M2 + w_M3) + 1 × (w_Pulse + w_FF)`
* **full partition** `C_part = S₁·w_M1 + S₂·w_M2 + S₃·w_M3 + 1 × (w_Pulse + w_FF)`

with the hoist credited separately because it is available without partitioning at all. Two
weightings: *DSM node counts* (|M1| = 24, |M2| = 10, |M3| = 12, |Pulse| = 1, |FF| = 5, |all| = 52)
and *measured cost share* inside the sweep.

**The implementation is validated against A2's published table.** Fed A2's own coupled `Sᵢ`, it
reproduces A2's node-count gate **to the second decimal on every row of every scenario** (e.g.
`large_tokamak_nof` 10.23 / 7.95 / 2.28 optimistic and 7.38 / 7.95 / −0.57 pessimistic;
`st_regression` 23.23 / 8.06 / 15.17; `large_tokamak_eval` 8.26 / 6.84 / 1.42).

### 7.2 The gate

`Sᵢ` sources: **frozen** = this task's `S₁_alone`, `S₂_frozen`, `S₃_frozen`. **lift only** = the
same three modules measured in the untouched coupled sequence with the one coupler pinned — the
partition without the frozen-input effect. **coupled** = A2's quantity, but uncensored.
**A2 as published** = A2's censored bounds, for reference.

| Scenario | `Sᵢ` source | weighting | total | of which hoist | of which **partition** |
|---|---|---|---|---|---|
| `large_tokamak_nof` | **frozen** | node counts | 22.89 % | 7.95 % | **14.94 %** |
| | lift only | node counts | 20.80 % | 7.95 % | 12.85 % |
| | coupled (uncensored) | node counts | 7.19 % | 7.95 % | −0.76 % |
| | A2 as published | node counts | 10.23 / 7.38 % | 7.95 % | 2.28 / −0.57 % |
| | **frozen** | measured cost | 14.45 % | 3.12 % | **11.33 %** |
| | lift only | measured cost | 13.39 % | 3.12 % | 10.27 % |
| | coupled (uncensored) | measured cost | 2.53 % | 3.12 % | −0.59 % |
| `low_aspect_ratio_DEMO` | **frozen** | node counts | 27.72 % | 8.20 % | **19.53 %** |
| | lift only | node counts | 26.04 % | 8.20 % | 17.84 % |
| | coupled (uncensored) | node counts | 14.85 % | 8.20 % | 6.65 % |
| | A2 as published | node counts | 14.97 / 14.84 % | 8.20 % | 6.77 / 6.64 % |
| | **frozen** | measured cost | 20.04 % | 3.24 % | **16.80 %** |
| | lift only | measured cost | 19.20 % | 3.24 % | 15.96 % |
| | coupled (uncensored) | measured cost | 10.60 % | 3.24 % | 7.36 % |
| `st_regression` | **frozen** | node counts | 26.15 % | 8.05 % | **18.10 %** |
| | lift only | node counts | 22.96 % | 8.05 % | 14.91 % |
| | coupled (uncensored) | node counts | 22.96 % | 8.05 % | 14.91 % |
| | A2 as published | node counts | 23.23 / 22.96 % | 8.06 % | 15.17 / 14.90 % |
| | **frozen** | measured cost | 20.80 % | 2.79 % | **18.01 %** |
| | coupled (uncensored) | measured cost | 19.09 % | 2.79 % | 16.30 % |
| `large_tokamak_eval` | **frozen** | node counts | 5.94 % | 6.29 % | **−0.35 %** |
| | coupled (uncensored) | node counts | 2.80 % | 6.29 % | −3.50 % |
| | A2 as published | node counts | 8.26 / 0.71 % | 6.84 % | 1.42 / −6.13 % |
| | **frozen** | measured cost | −0.60 % | 0.68 % | **−1.28 %** |

**On the censoring treatments.** A2 reported each gate twice because 24 % of `large_tokamak_nof`'s
loops leave a module still changing at exit, and its `Sᵢ` had to be *bounded* by `S_global` and
`S_global + 1`. **A19 removes that ambiguity rather than inheriting it**: a frozen sub-solve runs
to the module's own criterion, so its `Sᵢ` is observed, and no sub-solve in any scenario reached
the ceiling. The optimistic and pessimistic columns for the frozen rows are therefore *identical*,
and both are quoted above as one number. Where the two treatments still differ, in the "A2 as
published" rows, both are given as `optimistic / pessimistic`.

The full replay also **resolves A2's bounds**, and the answer is worth recording: on the 152
censored M2 loops of `large_tokamak_nof` the true value exceeds `S_global` by **+1 in 146 and +2
in 6**. So A2's *optimistic* column was never right and systematically flattered the partition,
and its *pessimistic* column was right 96 % of the time and slightly too generous the rest. The
truth sits at or just beyond the pessimistic bound — which is why the uncensored coupled partition
contribution on `large_tokamak_nof` is **−0.76 %**, below A2's own pessimistic −0.57 %.

### 7.3 Two caveats on the weightings

**Node counts are exact and reproduce A2 to the decimal. Measured cost does not reproduce.** The
cost shares are wall-clock ratios within a run, and I-10 (identical work varying up to 35 % in
CPU-seconds, cause unknown) reaches them:

| Scenario | source | M1 | M2 | M3 | Pulse | FF |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | A2 | 38.7 % | 41.6 % | 13.0 % | 0.3 % | 6.4 % |
| | **A19** | 42.0 % | 41.7 % | 11.7 % | 0.2 % | **4.4 %** |
| `low_aspect_ratio_DEMO` | A2 | 37.7 % | 43.7 % | 12.1 % | 0.2 % | 6.2 % |
| | **A19** | 40.9 % | 43.1 % | 11.5 % | 0.2 % | **4.4 %** |

The feed-forward share, which sets the hoist term, has moved by a third — A2's hoist of 4.6 % is
3.1 % here on the same code. **The measured-cost rows above should be read as one realisation of a
noisy weighting, not as a second measurement.** The node-count rows are exact and the verdict is
the same under both, which is what the two weightings are for.

### 7.4 The lift's cost, which this arithmetic omits

A2's arithmetic counts weighted model evaluations *within* a `call_models`. It does not count the
extra `call_models` a lifted design variable creates. The gradient phase uses central differences:
`2n` perturbation calls per gradient, confirmed exactly (600 / 15 = 40 = 2 × 20 on
`large_tokamak_nof`; 1 178 / 31 = 38 = 2 × 19 on `low_aspect_ratio_DEMO`; 532 / 19 = 28 = 2 × 14 on
`st_regression`). Lifting one variable makes that `2(n + 1)`.

| Scenario | `n` | gradient share of all `call_models` | **lift penalty** | partition, netted (node counts / measured cost) |
|---|---|---|---|---|
| `large_tokamak_nof` | 20 | 95.2 % | **4.76 %** | 10.2 % / 6.6 % |
| `low_aspect_ratio_DEMO` | 19 | 95.0 % | **5.00 %** | 14.5 % / 11.8 % |
| `st_regression` | 14 | 93.3 % | **n/a — `k = 0`** | 18.1 % / 18.0 % |
| `large_tokamak_eval` | 2 | 0 % (no gradient) | n/a | −0.4 % / −1.3 % |

`st_regression` needs no lift at all: `i_pulsed_plant = 0`, `Pulse` writes nothing, and A2 measured
zero live cross-module back edges. Its 18 % carries no dimension penalty — but it is also the
scenario furthest from the study's headline cases, and its 18 % is only 3 points above what A2
already measured for it.

**Netted, the two large pulsed tokamaks are at 6.6–10.2 % and 11.8–14.5 %.** H5 — the consistency
constraint changing VMCON's iteration count — is not in either figure and could move them in
either direction.

### 7.5 One thing that does *not* work: lifting without partitioning

If a per-module-state exit test replaced the objective/constraint test, the coupled loop would
need `max(S₁, S₂, S₃)` sweeps. Pinning the coupler changes that number **not at all**:

| Scenario | `max Sᵢ` coupled | `max Sᵢ` with the coupler pinned | `max Sᵢ` frozen |
|---|---|---|---|
| `large_tokamak_nof` | 3.4642 | 3.4642 | 3.4642 |
| `low_aspect_ratio_DEMO` | 3.4705 | 3.4705 | 3.4705 |
| `st_regression` | 3.3181 | 3.3181 | 3.3181 |
| `large_tokamak_eval` | 2.400 | 2.400 | 2.400 |

Because M2 is always the binding module and M2 never moves. **The lift buys nothing for a
monolithic loop; its entire value is realised only through the partition, which lets M1 stop
early on its own.** So the lift's contribution is correctly credited *to* the partition and is not
separable the way the feed-forward hoist is. This corrects a natural but wrong reading of §5.1's
decomposition.

---

## 8. What this changes

**In A2.** §11's first threat row — "`Sᵢ` measured in the coupled loop need not equal `Sᵢ` under
partitioning … the direction is not knowable a priori … residual risk: real" — is now measured.
The direction is *toward* the partition, the magnitude is +8 to +12 percentage points of partition
contribution on the two large pulsed tokamaks, and the mechanism is the `k = 1` coupler, not the
information M2 receives. A2's §4.1 "no laggard" claim and the orchestrator's push-back on it are
both vindicated in part: no module is conspicuously slower *in the coupled loop*, and A19 shows
the modules do **not** converge at similar rates in isolation — the spread of `Sᵢ` roughly doubles.

**In the plan.** §3.2's second-order caveat — "converging M1 fully before M2 runs changes the
information M2 receives, so per-module sweep counts under partitioning need not equal those
measured in the coupled loop" — is **half right and half refuted**. The counts do change. But not
because of the information M2 receives: M2's count is invariant. They change because the loop's
one live coupler is gone.

**Not changed.** `k = 1`, the coupler set, the two dead back edges, `Pulse` joining the
feed-forward set, `st_regression`'s `k = 0`, and A2's Gate N are all untouched by this work and
were re-confirmed incidentally where the instrument re-measures them.

---

## 9. Autonomous decisions, with reversal paths

| # | Decision | Why | How to reverse |
|---|---|---|---|
| 1 | **Added a method control (full-sequence replay) that the task did not ask for, and gated on it.** | Without it, "M1 alone converges faster" is indistinguishable from "my replay is broken". It reproduces the coupled `Sᵢ` on 7 058/7 058 pairs, so the isolated numbers can be trusted. | Delete the `(a)` block in `_replay`. The isolated numbers are unchanged; only their warrant is lost. |
| 2 | **Added a lift-emulating replay (the whole sequence with `times.t_plant_pulse_burn` pinned).** | The task's stated control failed on the two pulsed tokamaks, and the honest options were "report a failure" or "diagnose it". This diagnoses it exactly: `S₁_alone` equals the pinned-coupler `S₁` in 100 % of loops. It also supplies the lift/frozen-input decomposition §7.2 and §7.5 rest on. | Delete the `(d)` block. §4.3's second control and the "lift only" gate rows go with it. |
| 3 | **Replayed every `call_models` rather than a sample.** | The replay proved cheap (≈1 s per loop), and sampling would have left a representativeness question the task explicitly raised. | `--grad-stride N` restores sampling. |
| 4 | **Reported the *uncensored* coupled `Sᵢ` as the comparator, alongside A2's censored bounds.** | The full replay observes what the loop's exit test hides. Comparing frozen `Sᵢ` against a bound rather than a value would have understated or overstated the change depending on which bound was picked. Both are reported. | Use the "A2 as published" gate rows only. The frozen partition column is unchanged; the *change* relative to A2 grows on `large_tokamak_nof` (from 2.28 to 14.94 rather than from −0.76). |
| 5 | **Netted the lift's dimension penalty in §7.4 as a separate figure, not folded into the gate.** | A2's arithmetic does not include it and the tables must stay comparable; but quoting 19.5 % without it would overstate the case for reopening. Both are given. | Ignore §7.4. The gate rows are already A2-comparable. |
| 6 | **Kept the design vector injected at the head of every sub-sweep**, matching the coupled loop, and measured the alternative. | It is what `_call_models_once` does and what a per-module solver would do with its own inputs. The alternative gives identical counts everywhere, so the choice is immaterial. | `PROCESS_IDF_PROBE_FROZEN_NOINJECT=0` drops the variant; the primary numbers do not change. |
| 7 | **Excluded `Pulse` from all three sub-solves.** | Post-lift, A2 §6.2 established `Pulse` becomes a pure feed-forward node with no consumer upstream of itself. Including it would model a partition nobody proposes. Measured anyway as the M1 + `Pulse` diagnostic: identical counts. | The `S1_pulse` column already reports it. |
| 8 | **Switched off A2's read census** (`PROCESS_IDF_PROBE_READ_BUDGET=0`). | A19 does not use the coupler census — A2 established it completely — and it is the dominant cost of the `modules` instrument. It cannot affect sweep counts, and Gate N19 confirms the run is byte-identical to `control`. | Unset the two environment variables in `run_a19.py::_env`. |

| 9 | **Left `MASTER_TODO.md`'s duplicated body duplicated**, and added the A19 row to both copies rather than deduplicating. | The file at `bb5d440c` already contains everything from "## Project administration" onwards **twice** — the two queue blocks (lines 116–162 and 269–314 of the base file) are byte-identical, as are the decisions, issue register and open questions. This predates A19 and is not this task's to restructure; adding the row to only one copy would have made it inconsistent. **Flagged for the orchestrator.** | Delete lines 231 onwards up to the change log; nothing is lost. |

No edit was made under `process/models/`. **D11 approval was not needed.**

---

## 10. Threats to this result

| Threat | Handling / residual risk |
|---|---|
| The replay could perturb the trajectory | Gate N19: 0 differing MFILE lines in 15 916–18 691 across four scenarios, plus a field-by-field restore check that found 0 mismatches in 2 447 replays. **Residual risk: low.** State outside the data structure (model-instance attributes) is not snapshotted, but if any mattered the MFILE would have moved |
| The isolated counts might be an artefact of the isolation method | Gate M19: the same machinery replaying the *whole* sequence reproduces the coupled `Sᵢ` on 7 058/7 058 uncensored pairs |
| The warm start could be chosen to flatter the partition | The warm start is the previous design point's converged state — the only state a partitioned solver would have. A "hot" start from the current design point's converged state would give `Sᵢ = 2` trivially and was not used |
| The gate omits the lift's dimension penalty and H5 | §7.4 nets the dimension penalty explicitly. **H5 is unmeasured and is the dominant remaining unknown**; the plan's §3.3 already calls it the likeliest failure |
| Measured-cost weights are wall clock, and wall clock on this machine is unexplained (I-10) | §7.3 shows the feed-forward share moved by a third between A2's run and this one on identical code. Node counts are exact, reproduce A2 to the decimal, and give the same verdict. **Do not quote a measured-cost row alone** |
| The frozen `Sᵢ` assume the partition converges each module to its own state criterion | It does by construction, and that is *more* work than the current loop does in the 24 % of `large_tokamak_nof` loops that exit early — which is why `S₂_frozen` (3.226) exceeds A2's censored `S₂` (2.658). The arithmetic already charges this |
| A real partition would also pay per-module solver overhead, extra objective evaluations, and the consistency residual | None of these is in the arithmetic, on either side of A2's or A19's comparison. All push the partition down |
| Four scenarios, tokamak only; unsampled switch combinations | Unchanged from A2: no claim about stellarator, IFE, DCLL blankets, resistive TF coils or `i_tf_turn_type = 3` |
| One instrumented run per configuration | Sweep counts are exact and deterministic; A1 established bit-level determinism over five replicates per scenario. Repetition adds nothing to a count |

---

## 11. Reproducing this

```bash
cd /home/wrutten/projects/PROCESS_surgery_A19/arch_surgery/idf_probe
PY=/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python

# one scenario at a time, serially, on an otherwise idle machine
for sc in large_tokamak_nof low_aspect_ratio_DEMO st_regression large_tokamak_eval; do
  $PY run_a19.py --scenarios $sc --arms control frozen --grad-stride 1 --other-stride 1
done

# gates, controls, the ordering distribution and the gate arithmetic
$PY analyse_a19.py --json runs/a19/_a19_report.json
$PY _a19_tables.py runs/a19/_a19_report.json
```

`run_a19.py` sets `PYTHONPATH` to the tree it lives in for every subprocess and `run_one.py`
aborts if the imported tree is not exactly that one. `runs/` is untracked per the standing rule;
`runs/a19/_a19_report.json` holds every number quoted above, including the per-`call_models`
records.

---

## 12. Change log

| Date | Entry |
|---|---|
| 2026-08-31 | Report written. Instrument (`PROCESS_IDF_PROBE=frozen`), driver and analysis committed as `7fd6b3ae`. **Gate N19 PASS 4/4** (0 differing MFILE lines, 0 restore mismatches in 2 447 replays); **method control exact** (7 058/7 058); **validation control passes in its corrected form** — `S₁_alone` equals coupled `S₁` on 569/569 and 8/8 loops of the two `k = 0`-like scenarios, and equals the coupled-with-coupler-pinned `S₁` on 100 % of loops in all four. Findings: **`S₂` is invariant** under frozen inputs in all 2 447 loops, refuting the "M2 chases a moving target" and "M1 gates everything" readings; `S₁`'s fall is entirely the `k = 1` lift; `S₃` falls for both reasons. **Gate S1 recomputed: partition contribution 11.3–19.5 % on three of four scenarios — the middle band, nothing at 25 %**; netted for the lift's dimension penalty, 6.6–14.5 % on the two large pulsed tokamaks. New: the laggard moves from M1 to **M2** under the partition; A2's optimistic censoring bound shown never to be attained; the lift shown to buy nothing without the partition; A2's measured-cost feed-forward weight shown not to reproduce (I-10). |
