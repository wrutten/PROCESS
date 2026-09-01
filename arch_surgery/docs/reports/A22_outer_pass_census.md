> **Document status** — **LIVE · CURRENT**
> The task report for A22 (outer-pass-census), open at the time of writing. It describes branch
> `A22-outer-pass-census`, off `architecture_surgery` at **`703dd7d4`** (experiment base commit
> `c0ae5b28`), and its numbers are current evidence. It will be archived to `deprecated/` at
> merge; position in that folder would record lifecycle, not staleness (trap T3).

# A22 (outer-pass-census) — which fields are still moving when a second outer pass is needed

| | |
|---|---|
| **Task** | A22 (outer-pass-census) |
| **Branch** | `A22-outer-pass-census`, in the isolated worktree `/home/wrutten/projects/PROCESS_surgery/.claude/worktrees/agent-af0ebc003bfa3bc40` |
| **Base** | `703dd7d4` on `architecture_surgery`; experiment base commit `c0ae5b28` |
| **Data** | A18 (experiment-framework)'s harvested design points, reused unchanged; no new harvest |
| **Environment** | `PROCESS_surgery_env`, `PYTHONPATH` pinned to this worktree, the exact tree asserted per subprocess (trap T6) |
| **PROCESS code changed** | **none** |
| **Date** | 2026-09-01 |
| **Status** | Complete |

**Vocabulary, once, so this reads without the queue open beside it.**

- A *deck* is one `IN.DAT` input file. Four are studied: `large_tokamak_nof`,
  `low_aspect_ratio_DEMO`, `st_regression`, `large_tokamak_eval`. They are never pooled.
- A *design point* is one set of values for the optimiser's design variables, captured during a
  real PROCESS run and replayed afterwards with the optimiser absent.
- The *coupling state* `y` is every quantity written by a model inside the solve loop — 827 to 846
  named quantities depending on the deck. It is measured by run-time instrumentation, not declared.
- The **modules** are decision **D8**'s three-way split of the model sequence: **M1 Physics**,
  **M2 Coils**, **M3 Plant**. Two further groups sit outside them: **PULSE**, the single `pulse`
  model, and **FF**, the feed-forward tail (`water_use`, `costs`). The *block arm* runs them in the
  order M1 → M2 → PULSE → M3 → FF, solving M1, M2 and M3 each to internal convergence before moving
  on, and repeating that whole sequence — an *outer pass* — until nothing moves.
- *Cross-module movement* means a quantity written in one of those groups changes what a **different**
  group computes. Within-module movement is a group's own state settling.
- `k` is the number of quantities that close a cycle between modules. An earlier task, **A2**,
  measured `k = 1` on the pulsed decks — the burn time `times.t_plant_pulse_burn` — and `k = 0` on
  `st_regression`, which sets `i_pulsed_plant = 0` and so has no burn-time coupler at all.
- **Phase B** is the next planned experiment: lift the burn time out of the loop and onto the
  optimiser, on the premise that it is the only quantity closing a cycle. This report exists to test
  that premise before any Phase B code is written.
- **tau** is the convergence tolerance: a quantity counts as settled when it moves by less than tau
  times its own typical size. Everything here is at **tau = 1e-6**, the value A18 calibrated.

---

## 1. Verdict

**Phase B's premise holds on all four decks.** On the three pulsed decks, the movement that forces a
second outer pass crosses a module boundary, and holding the burn time fixed removes **all** of it —
not most of it, all of it, on every design point. On `st_regression` there is no cross-module
movement at all, and its 2.139 outer passes are fully explained without any.

Per deck, over that deck's own harvested design points, in the block arm at tau = 1e-6:

| deck | design points | mean outer passes | cross-module movement other than the burn time? | with the burn time held fixed |
|---|---|---|---|---|
| `large_tokamak_nof` | 149 | 2.7047 | **No** | mean 1.9530; **0** fields above tau on any outer pass ≥ 2, on 149/149 points |
| `low_aspect_ratio_DEMO` | 297 | 2.7205 | **No** | mean 1.9495; **0** fields above tau on any outer pass ≥ 2, on 297/297 points |
| `large_tokamak_eval` | 10 | 2.4000 | **No** | mean 1.7000; **0** fields above tau on any outer pass ≥ 2, on 10/10 points |
| `st_regression` | 144 | 2.1389 | **No** — and no cross-module movement of any kind | unchanged (2.1389); `pulse` writes nothing in this deck |

**The `st_regression` explanation, separately, on that deck's own terms.** A2's back-edge census did
**not** miss an edge. On all 144 of `st_regression`'s harvested design points, **no module ever
re-solves on outer pass 2 or later** — M1, M2 and M3 each converge in a single inner sweep from the
second outer pass onwards, without exception. Its 2.139 passes decompose exactly:

- **9 of 144** points converge in **1** outer pass: the entry state was already at the fixed point.
- **128 of 144** converge in **2**: pass 1 does the work, pass 2 detects nothing and exists only
  because the loop cannot certify convergence without one pass that changes nothing.
- **7 of 144** run to 4, 6 or 7 passes. On every one of those, the *only* quantities above tau from
  outer pass 2 onwards are three fields of the 1990 cost model — `costs.coe`, `costs.coecap`,
  `costs.coefuelt` — which live in the feed-forward tail **FF**, downstream of every module. Six of
  those seven design points have **negative** net electric power (−1.6 to −3.0 MW, against a
  deck median of +110 MW over the other 137 points), which makes the cost of electricity diverge:
  `costs.coe` reaches 6.6 × 10²¹ against a characteristic scale of 1.25 × 10³. The relative test is
  therefore roughly 10¹⁸ times tighter than intended at exactly those points, and the loop runs on
  until the whole state is bit-identical.

So the second candidate explanation is the right one, in a sharper form than "the loop converges on
the whole coupling state rather than on the couplers": **`st_regression`'s extra passes are one
structural verification pass (128/144 points) plus a numerically degenerate cost evaluation in the
feed-forward tail (7/144 points).** Neither is coupling. A18's own `hoist = 1` variant, which lifts
the feed-forward tail out of the loop, confirms this independently and with no new run: it gives
`st_regression` a distribution of {1 pass: 9, 2 passes: 135} over 144 points, mean 1.9375 — the seven
long points vanish exactly, and no point exceeds two passes.

---

## 2. How "cross-module" was decided, and why it is not a name-matching argument

Trap **T1** records three occasions on which a quantity written by one model and read by another
looked like a dependency edge and was not, because the read happened in an `output()` method — after
the solve, outside the loop. Trap **T7** records the deeper form: ten model objects call their own
`run()` from inside `output()`, so even instrumenting `run()` is not enough. This task never greps
for names and never reads a call graph. It uses two run-time facts instead.

**The detector.** In the block arm, **M1 runs first in every outer pass**, preceded only by the
injection of the design variables, which are identical on every pass. So if M1's own state changes
when M1 is re-run at the start of outer pass 2 — after M1 had already converged internally during
pass 1 — then something M1 reads was changed by M2, PULSE, M3 or FF during pass 1. That is a live
edge crossing into M1, established by measurement, with no need to know what M1 reads. The same
count for M2 and M3 is not by itself unambiguous, because a group that runs later in the pass may
simply be reacting to M1 having moved; those counts are reported but are never the evidence.

**The attribution.** Which model writes each moving field comes from A18's harvest, which records
writes per model *inside* `Caller._call_models_once` and closes its sweep at that boundary. It
therefore cannot see an `output()`-path write at all. The replay process never calls `output()`.

**The counterfactual.** A third arm, `A1pin`, is the block arm with `times.t_plant_pulse_burn` held
at its entry value for the whole solve — re-imposed after every single model call, so `pulse`'s
write to it is discarded before any later model can read it. This is what "the burn time has been
lifted onto the optimiser, and is therefore an input to the loop" does to the loop's topology. If
`k = 1` is right, no module may move on outer pass 2 or later under this arm.

---

## 3. Evidence, per deck

### 3.1 `large_tokamak_nof` — 149 harvested design points

| arm | mean outer passes | distribution | ≥ 2 passes | ≥ 3 passes |
|---|---|---|---|---|
| block (`A1`) | 2.7047 | {1: 7, 2: 30, 3: 112} | 142/149 | 112/149 |
| block, burn time held fixed (`A1pin`) | 1.9530 | {1: 7, 2: 142} | 142/149 | **0/149** |
| block, tail iterated (`A1ffit`) | 2.7047 | {1: 7, 2: 30, 3: 112} | 142/149 | 112/149 |

**Which groups re-solve on outer pass 2 or later**, over 149 design points: M1 on **112**, M3 on
**112**, M2 on **0**. Under `A1pin`: **none, on any of the 149**.

**What M1 itself rewrote on its first inner sweep of outer pass 2** — the unambiguous cross-boundary
signal — on all 112 of the 112 design points where it moved. All five are written by `physics`, in
**M1**, and all five are functions of the burn time:

| field | written by | module | frequency |
|---|---|---|---|
| `times.t_burn_0` | `physics` | M1 | 112/112 |
| `times.t_plant_pulse_plasma_present` | `physics` | M1 | 112/112 |
| `times.t_plant_pulse_total` | `physics` | M1 | 112/112 |
| `physics.vs_plasma_burn_required` | `physics` | M1 | 112/112 |
| `physics.vs_plasma_total_required` | `physics` | M1 | 112/112 |

**The full set above tau on the outer-pass-2 residual** — the residual that forces a third pass —
on the 112 of 149 design points that have a non-empty one. Over those 112, the number of fields above tau is minimum 12, median 46, maximum 52. The most
frequent, with the model that writes each:

| field | written by | module | frequency |
|---|---|---|---|
| `costs.coecap`, `costs.coe`, `costs.coeoam`, `costs.coefuelt` | `costs` | FF | 112/112 each |
| `power.qac` | `power` | M3 | 112/112 |
| `costs.bktcycles`, `costs.cpfact` | `availability` | M3 | 112/112 each |
| the five M1 fields above | `physics` | M1 | 112/112 each |
| `tfcoil.cryo_cool_req`, `heat_transport.helpow`, `power.qmisc`, `heat_transport.p_cryo_plant_electric_mw` | `power` | M3 | 83/112 each |
| `power.p_cryo_plant_electric_profile_mw`, `power.p_plant_core_systems_elec_mw` | `power.plant_electric_production` | M3 | 83/112, 82/112 |
| `buildings.cryvol` | `buildings` | M3 | 83/112 |
| `costs.c2263`, `costs.c2174`, `costs.c226`, `costs.c2262`, `costs.cppa` | `costs` | FF | 81–83/112 |

Every one of these is M1, M3 or FF — that is, physics recomputing with the settled burn time, and
the plant and cost models downstream of it. **Under `A1pin` this set is empty on every outer pass
from 2 onwards, on all 149 design points.**

### 3.2 `low_aspect_ratio_DEMO` — 297 harvested design points

| arm | mean outer passes | distribution | ≥ 3 passes |
|---|---|---|---|
| block (`A1`) | 2.7205 | {1: 15, 2: 53, 3: 229} | 229/297 |
| block, burn time held fixed (`A1pin`) | 1.9495 | {1: 15, 2: 282} | **0/297** |
| block, tail iterated (`A1ffit`) | 2.7205 | {1: 15, 2: 53, 3: 229} | 229/297 |

Groups re-solving on outer pass ≥ 2, over 297 points: M1 on **229**, M3 on **229**, M2 on **0**;
under `A1pin`, **none of the 297**. The fields M1 rewrote on its first inner sweep of outer pass 2
are the **same five `physics`-written fields** as `large_tokamak_nof`, on 229 of the 229 points where
M1 moved. Over those 229 points the outer-pass-2 residual has minimum 17, median 46 and maximum 52
fields above tau, composed of those
five M1 fields, `power`/`availability`/`buildings` fields in M3, and `costs` fields in FF, in the same
pattern. **Under `A1pin` the set is empty on every outer pass from 2 onwards, on all 297 points.**

### 3.3 `large_tokamak_eval` — 10 harvested design points

| arm | mean outer passes | distribution | ≥ 3 passes |
|---|---|---|---|
| block (`A1`) | 2.4000 | {1: 3, 3: 7} | 7/10 |
| block, burn time held fixed (`A1pin`) | 1.7000 | {1: 3, 2: 7} | **0/10** |
| block, tail iterated (`A1ffit`) | 2.4000 | {1: 3, 3: 7} | 7/10 |

M1 re-solves on outer pass 2 on **7 of 10** points, M3 on 3, M2 on 0; under `A1pin`, none of the 10.

**This deck's bookkeeping differs and the difference must be stated.** Its harvest is a single
evaluation run of 10 design points, so 555 of its 840 coupling-state components do not vary across
the harvest and are classified *constant* — tested for exact equality rather than at tau. Two of the
five burn-time-dependent `physics` fields, `physics.vs_plasma_burn_required` and
`physics.vs_plasma_total_required`, fall into that class here, and they **move** on all 7 points at
outer pass 2. That is why 7 of 10 points need a third pass even though only 3 of 10 have a non-empty
above-tau residual at that pass. The cause is the same as on the other two pulsed decks — under
`A1pin` both stop moving and no point exceeds two passes — but the verdict for this deck rests on a
much weaker category assignment than for the other three, and should be read as consistent with them
rather than as independent confirmation.

### 3.4 `st_regression` — 144 harvested design points

| arm | mean outer passes | distribution |
|---|---|---|
| block (`A1`) | 2.1389 | {1: 9, 2: 128, 4: 1, 6: 3, 7: 3} |
| block, burn time held fixed (`A1pin`) | 2.1389 | identical — `pulse` writes nothing in this deck |
| block, tail iterated (`A1ffit`) | 2.1389 | identical |
| A18's `hoist = 1` (tail lifted out of the loop) | 1.9375 | {1: 9, 2: 135} |

**Groups re-solving on outer pass ≥ 2, over all 144 design points: none. Not M1, not M2, not M3, on
any point.** The measured coupling graph is what A2 said it was.

The complete list of fields above tau on any outer pass from 2 onwards, over all 144 points, is three
fields, all written by `costs`, all in **FF**:

| outer pass | design points with a non-empty residual | fields above tau |
|---|---|---|
| 2 | 7/144 | `costs.coecap`, `costs.coe`, `costs.coefuelt` |
| 3 | 7/144 | the same three |
| 4 | 6/144 | the same three |
| 5 | 6/144 | `costs.coecap`, `costs.coe` (and `coefuelt` on 5 of the 6) |
| 6 | 3/144 | the same three |

Iterating FF to its own fixed point (`A1ffit`) does not change the outer counts, but it does show FF
taking two inner sweeps on every outer pass of those seven points — the tail is genuinely still
moving, it is simply moving downstream of everything. Lifting the tail out of the loop entirely
(A18's `hoist = 1`) removes all seven long points.

The magnitudes make the mechanism plain. On the six points whose entry state has negative net
electric power, `costs.coe` and `costs.coecap` stand at 6.6 × 10²¹ and 6.5 × 10²¹ against
characteristic scales of 1 251 and 1 184, and `costs.coefuelt` at −4.6 × 10¹⁶ to −8.7 × 10¹⁶ against
2.62. The seventh point (call index 31) enters with +1 434 MW and `coe` = 116, and reaches the same
region during the first outer pass — its pass-1 residual moves `coecap` by 5.47 × 10¹⁸ scale units,
i.e. 6.5 × 10²¹ in absolute terms. Successive outer passes then shrink the residual by roughly a
factor of 30 per pass until the state becomes bit-identical and the residual is exactly zero. The
final pass of every one of the seven has a maximum residual of 0, 2 × 10⁻¹⁵ or 3 × 10⁻¹⁴.

---

## 4. What this does and does not say about Phase B's payoff

Removing the burn-time cycle from the block arm reduces that arm's model evaluations, over each
deck's own harvested design points, by:

| deck | design points | block-arm model evaluations | with the burn time held fixed | change |
|---|---|---|---|---|
| `large_tokamak_nof` | 149 | 13 906 | 9 848 | **−29.2 %** |
| `low_aspect_ratio_DEMO` | 297 | 28 070 | 19 774 | **−29.6 %** |
| `large_tokamak_eval` | 10 | 618 | 418 | **−32.4 %** |
| `st_regression` | 144 | 9 917 | 9 917 | 0.0 % |

**This is not the same quantity as the ~46 % figure the task brief quotes**, and it must not be
substituted for it. It is the block arm compared against *itself* with one coupler removed, at
tau = 1e-6, over the harvested points of one PROCESS run per deck. It says nothing about the block
arm against today's driver, and nothing about a deck other than these four.

**And the pin arm is a topology probe, not a validated architecture.** Holding the burn time at its
entry value holds it away from its self-consistent value, and on `low_aspect_ratio_DEMO` that moves
the objective at exit by a median relative 4.9 × 10⁻⁴ and a maximum of 3.6 × 10⁻¹ over 297 points.
(On `large_tokamak_nof` and `st_regression` the objective is bit-identical on every point; on
`large_tokamak_eval` the maximum is 2.5 × 10⁻⁵.) Phase B must add a constraint that drives the
burn-time residual to zero, and the equivalence of its answer to today's is a gate it still has to
pass. Nothing here pre-empts that.

---

## 5. The conditions every number above is limited by

Trap **T11** records three numbers this project published without the condition that limits them.
These are the conditions on these.

1. **Population.** Every count is over one deck's harvested design points from one PROCESS run:
   149, 297, 144 and 10. A18's harvest keeps every design point the optimiser actually visited and
   one in five of the finite-difference perturbations. It is not a sample of an arbitrary design
   space, and a deck's own numbers never transfer to another deck.
2. **Partition and order.** "Cross-module" is defined against decision D8's M1/M2/M3 split with
   PULSE and FF outside it, and against the block order M1 → M2 → PULSE → M3 → FF. A different
   ordering would turn some of these forward edges into back edges and vice versa. The M1-first
   detector in particular depends on M1 running first.
3. **What is being watched.** The convergence test is on the coupling state `y` — everything written
   by an in-loop model, 827 to 846 components per deck — at tau = 1e-6, with each component scaled by
   its median magnitude across the harvest. A quantity that no in-loop model writes is not in `y` and
   would not be seen. `y` is measured by instrumentation, not declared, so it does not inherit the
   dependency analysis's completeness or its gaps.
4. **`large_tokamak_eval`'s category assignment is weak.** 555 of its 840 components are classified
   constant from a 10-point harvest; see §3.3. Its verdict is consistent with the other two pulsed
   decks, not independent of them.
5. **The burn time itself is never the moving field.** On no pulsed deck is
   `times.t_plant_pulse_burn` above tau on any outer pass from 2 onwards. It settles during pass 1.
   What forces pass 3 is that M1 runs *before* PULSE in the block order, so M1 has not yet seen the
   settled value when it runs in pass 1. This is `k = 1` behaving exactly as a single one-step cycle
   should — it costs precisely one extra outer pass — and it is why the census had to look at what
   M1 rewrote rather than at what moved most.
6. **No conclusion here rests on a timing.** Every quantity reported is a count of design points, a
   count of model evaluations, a field name, or a bit-comparison.

---

## 6. Gate — the recording did not change what was measured

The instrumentation added for this task is two optional, default-off hooks in
`arch_surgery/fixedpoint/engine.py`, which is analysis code and not part of PROCESS. **No file under
`process/` was changed, and none needed to be.**

The block arm re-run here (`A1`) was compared against A18's recorded block arm on the same harvest at
the same tau, per design point, with **no tolerance applied anywhere in the comparison**:

| deck | points compared | count mismatches | residual-trace mismatches | exit-audit mismatches |
|---|---|---|---|---|
| `large_tokamak_nof` | 149 | 0 | 0 | 0 |
| `low_aspect_ratio_DEMO` | 297 | 0 | 0 | 0 |
| `st_regression` | 144 | 0 | 0 | 0 |
| `large_tokamak_eval` | 10 | 0 | 0 | 0 |

"Count" covers outer passes, model evaluations, module sweeps, the per-block inner sweep counts, the
converged flag and the moved-constant list. "Residual trace" covers the floating-point residual
maximum, the argmax field name and the above-tau count at every outer pass. "Exit audit" covers the
objective and the constraint-vector L2 and L∞ norms both at termination and after one further sweep.
**600 of 600 design points reproduce bit-for-bit.**

Reusing A18's harvest rather than re-harvesting is licensed by three git tree hashes, not by
assumption: `process/`, `arch_surgery/fixedpoint/` and `arch_surgery/docs/data/dsm_node_map.json` are
identical between A18's commit `ad4e4536` and this branch's base `703dd7d4`. The models replayed here
are the models that were harvested.

---

## 7. Autonomous decisions, and how to reverse each

| # | Decision | Why | Reversal |
|---|---|---|---|
| 1 | Reused A18's harvested design points instead of re-harvesting | The three inputs that determine a harvest have identical git tree hashes between A18's commit and this base (§6), and the task brief asks for analysis over new runs | Re-run `run_phase_a.py harvest` and point `run_a22.py --a18-runs` at the new directory; nothing else changes |
| 2 | Added two default-off hooks to `engine.py` (a `recorder` argument to `solve_block`, and a `pin` argument to `Sweeper`) rather than writing a parallel copy of the block solver | A copy would drift from the arm A18 measured, silently. The hooks are gated by a 600-point bit-comparison instead (§6) | Revert `arch_surgery/fixedpoint/engine.py`; `a22_census.py` then no longer runs, and nothing else is affected |
| 3 | Answered "cross-module" with the M1-first re-solve detector plus a pin counterfactual, rather than with a read census | Both traps T1 and T7 are about read censuses being wrong. The detector needs no read information at all, and the counterfactual is decisive | If a read census is later wanted, A2's instrument exists; it would corroborate, not replace |
| 4 | Reported the seven long `st_regression` points as a numerically degenerate cost evaluation rather than excluding them | A failed or odd result is a result. They are 7 of 144 and are stated with that denominator everywhere | Nothing to reverse; the raw per-point records are in the artifacts |
| 5 | Read A18's run artifacts from its locked worktree, and wrote nothing there | Those artifacts are untracked and exist only in that worktree | n/a |

**Not done, deliberately:** no merge, no push, no change to `process/`, no change to the frozen base
commit, and no re-tuning of tau or of any cap to make a number cleaner.

---

## 8. Where the artifacts and the code are

| what | where |
|---|---|
| census driver (one subprocess per deck) | `arch_surgery/fixedpoint/run_a22.py` |
| the census itself, the two counterfactual arms, and the gate | `arch_surgery/fixedpoint/a22_census.py` |
| the tables in §3 | `arch_surgery/fixedpoint/a22_tables.py` |
| the two default-off hooks | `arch_surgery/fixedpoint/engine.py` |
| raw per-point records (untracked, as required) | `arch_surgery/idf_probe/runs/a22/<deck>/census.json` |

Reproduce with:

```
PYTHONPATH=<this worktree> python arch_surgery/fixedpoint/run_a22.py \
    --a18-runs <A18 worktree>/arch_surgery/idf_probe/runs/a18
python arch_surgery/fixedpoint/a22_tables.py
```

---

## 9. Change log

Append-only.

| date | change |
|---|---|
| 2026-09-01 | Created. Census run on all four decks; gate passes on 600/600 design points; verdict as in §1. |
