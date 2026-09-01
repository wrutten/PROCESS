> **Document status** — **LIVE · CURRENT**
> The task report for A18 (experiment-framework), open at the time of writing. It describes
> branch `A18-experiment-framework`, off `architecture_surgery` at **`73439685`** (experiment base
> commit **`c0ae5b28`**), and its numbers are current evidence. It will be archived to
> `deprecated/` at merge; position in that folder records lifecycle, not staleness (trap T3 — the
> recorded hazard that a document's directory says when its task closed, not whether its numbers
> still hold).

# A18 (experiment-framework) — Phase A of the MDA partition experiment

| | |
|---|---|
| **Task** | A18 (experiment-framework) — build **Phase A only**: the DSM node map, the harvest probe mode, and the fixed-point engine with its arms, runner and tolerance ladder |
| **Branch** | `A18-experiment-framework`, in the isolated worktree `.claude/worktrees/agent-a6cde25df6d1bddf2` |
| **Base** | `73439685` on `architecture_surgery`; experiment base commit `c0ae5b28` |
| **Specification** | [`../plans/EXPERIMENT_FRAMEWORK.md`](../plans/EXPERIMENT_FRAMEWORK.md) §2.4 (component C9), §2.9 (C8), §3.1 (steps F4 and F11) |
| **Environment** | `PROCESS_surgery_env`, `PYTHONPATH` pinned to the worktree (trap T6) |
| **Date** | 2026-09-01 |
| **Status** | Complete — **all five gates PASS; the block partition costs more model evaluations than the flat loop on three of four scenarios** |

**Vocabulary, once, so this reads without the queue open beside it.**
A *sweep* is one pass over PROCESS's model sequence (`Caller._call_models_once`, 21 model calls in
these decks). A *`call_models`* is one execution of the *idempotence loop*, which repeats sweeps
until the objective function and the constraint vector stop changing. A *design point* is one
optimisation parameter vector `x` together with the plant state the loop was entered with; 94–96 %
of design points are finite-difference perturbations the optimiser generates while building a
gradient (probe phase `grad`), the rest are the points it actually visits (`fn`) plus a trailing
reconciliation call (`grad_reconcile`). The *coupling state* `y` is every data-structure field a
model writes inside a sweep. The proposed *partition* (decision **D8**) splits the model sequence
into three modules — **M1 Physics**, **M2 Coils**, **M3 Plant** — with `Pulse` as an articulation
point belonging to neither, and a *feed-forward tail* (`water_use`, `costs`) that feeds nothing
back and can therefore be *hoisted* out of the loop entirely. **D13** is the decision to measure
the partition in two phases, of which **Phase A** — this task — removes the optimiser and compares
fixed-point architectures only. *Trap T1* is the recorded failure of confusing a model's `run()`
method, which is inside the loop, with its `output()` method, which is not; *T6* is that a `git
worktree` does not redirect the editable install; *T9* is that reading a sibling repository's
generated exports live races with their tooling.

---

## 1. Verdict

**The framework is built, all five gates pass, and it has already produced three results that bear
on the partition — two of which cut against it.**

**1. The block partition is more expensive, not less, at matched accuracy.** Replaying every
harvested design point through both architectures at an identical tolerance, counting **model
evaluations** (the only unit in which flat sweeps and per-module sweeps are commensurable):

| Scenario | design points | flat control **A0** | block **A1** | A1 / A0 |
|---|---|---|---|---|
| `large_tokamak_nof` | 149 | 9 471 | 13 906 | **1.468** |
| `low_aspect_ratio_DEMO` | 297 | 19 992 | 28 070 | **1.404** |
| `st_regression` | 144 | 10 395 | 9 917 | **0.954** |
| `large_tokamak_eval` | 10 | 525 | 618 | **1.177** |

The block arm needs **fewer outer iterations** everywhere — 2.71 against 3.03 on
`large_tokamak_nof`, 2.14 against 3.44 on `st_regression` — and that is exactly what the partition
hypothesis predicts. It buys those with inner solves, and the inner solves cost more than the outer
iterations save. `st_regression` is the one scenario where it breaks even, and that is the
scenario with **no cross-module coupler at all** (`k = 0`), so its outer loop is trivial by
construction.

**2. The two-sweep floor is removable, and it is worth almost exactly what the strict convergence
test costs.** This is what arm A0f exists to separate, and without it the two effects would have
been indistinguishable from neither existing:

| Scenario | R → A0f (test only) | A0f → A0 (floor only) | R → A0 (both) |
|---|---|---|---|
| `large_tokamak_nof` | **+1.55 %** | **−1.53 %** | **0.00 %** |
| `low_aspect_ratio_DEMO` | −3.40 % | −1.55 % | −4.90 % |
| `st_regression` | +8.62 % | −1.79 % | +6.68 % |
| `large_tokamak_eval` | +27.3 % | −10.7 % | +13.6 % |

On `large_tokamak_nof` the sum is **exactly zero** — 9 471 model evaluations either way — while the
per-point differences are not zero at all: 8 points get cheaper by a sweep, 7 get more expensive.
A report that ran only `R → A0` would have concluded "no effect" from two real effects that
cancelled. Removing the floor lets **7 of 149** points (4.7 %) converge in a single sweep, which is
structurally impossible today.

**3. PROCESS's idempotence loop stops with named model outputs still moving, and it is the cost
model.** The exit audit — one further full sweep past termination, the same for every arm —
catches arm R (today's loop) leaving the coupling state above tolerance on **8 of 600** design
points. Every one of them is the levelised-cost family, `costs.coe`, `costs.coecap`,
`costs.coefuelt`, on `st_regression` (7 points) and `large_tokamak_nof` (1). The largest scaled
residual is **8.1 × 10⁸** times the field's own characteristic magnitude. Nothing reads those
fields back inside the loop — they are the feed-forward tail — which is precisely why a predicate
watching only `objf` and `conf` never notices. The three fixed-point arms fail the same audit on
**0 of 600**.

**Everything the gates asked for held.** Neutrality 4/4 with **0 differing MFILE lines** against a
pristine `git archive` of `c0ae5b28`; determinism bit-for-bit *and* sweep-for-sweep; harvest
inertness 0 differing lines; replay fidelity **600/600** design points reproducing the live loop's
sweep count exactly; restore exactness **0 mismatched fields** across all 2 288 fields in every
restore of every arm of every design point — 2 400 in the headline comparison alone. The drop census is **100 % on every arm, every scenario** — no design point
was dropped, and no cap was reached by any arm at any time.

**One gate failed on the way and was fixed rather than reported around**, and the sequence is
recorded in full in §10 and §12: replay fidelity initially came out 599/600, and the single
failure was a defect in **my** reproduction of `Caller.call_models`, not a property of PROCESS.
The diagnosis is in §2.4.

---

## 2. Gates as they landed

### 2.1 Gate N — neutrality · **PASS, 4 / 4**

With the probe switch unset the tree must behave identically to an untouched checkout of the base
commit; with the harvest mode on it must still write an identical MFILE.

| Scenario | pristine vs control | pristine vs harvest | control vs harvest (instrument only) | control vs harvest (cache written) | `ifail` |
|---|---|---|---|---|---|
| `large_tokamak_nof` | **0 / 0** | **0 / 0** | **0 / 0** | **0 / 0** | 1 |
| `low_aspect_ratio_DEMO` | **0 / 0** | **0 / 0** | **0 / 0** | **0 / 0** | 1 |
| `st_regression` | **0 / 0** | **0 / 0** | **0 / 0** | **0 / 0** | 1 |
| `large_tokamak_eval` | **0 / 0** | **0 / 0** | **0 / 0** | **0 / 0** | 1 |

Cells are *differing MFILE lines / differing fields of the exact hex-float signature*. The MFILE
comparison is every line except the run-metadata header (date, time, user, computer, directory,
file prefix, git tag, git branch, commit message, measured runtime) — A1's and A2's exclusion list,
unchanged. The signature is the hex-float `norm_objf`, `sqsumsq`, both iteration-variable vectors,
the constraint residual vector and its L2 norm. `pristine` is `git archive c0ae5b28` extracted to a
directory outside every working tree, with the probe module absent entirely.

### 2.2 Gate D — determinism · **PASS, 4 / 4, bit-for-bit and sweep-for-sweep**

Two independent harvest runs of each scenario. Bit-for-bit: 0 differing MFILE lines, 0 differing
signature fields. Sweep-for-sweep, which a byte comparison of the MFILE does not by itself
establish:

| Scenario | sweeps total | `call_models` | sweeps-per-`call_models` histogram |
|---|---|---|---|
| `large_tokamak_nof` | 2 029 | 630 | 2:127 · 3:276 · 4:191 · 5:35 · 6:1 |
| `low_aspect_ratio_DEMO` | 4 286 | 1 240 | 2:170 · 3:622 · 4:162 · 5:286 |
| `st_regression` | 1 891 | 570 | 2:79 · 3:274 · 4:178 · 5:37 · 6:2 |
| `large_tokamak_eval` | 29 | 11 | 2:8 · 3:2 · 5:1 |

Identical in both replicates in every scenario.

Replay-side determinism is stronger still: two independent replay *processes* produce
**byte-identical `result.json`** — every count, every residual, every trace entry — for all four
scenarios. Compared with wall clock and file paths removed, nothing else.

`control_rep2` is deliberately absent from this suite: A1 already gated the tree's own determinism
at this base commit, and what is new here is the harvest arm.

### 2.3 Gate H — harvest inertness · **PASS, 4 / 4**

The harvest must not perturb what it measures. Two comparisons, both 0 differing lines in every
scenario: `control` against a harvest run with the state cache switched off (isolating the
instrument), and `control` against the real harvest run that writes 36–72 MB of design points to
disk (isolating the disk write). A third, weaker, confirmation: the harvest was re-run from scratch
after the §2.4 fix and every reported count — sweep totals, point counts, magnitude histograms —
came back identical.

### 2.4 Gate F — replay fidelity · **PASS, 600 / 600 — after a failure that was mine**

Reproducing A19's method control: replaying the untouched sweep sequence from a saved entry state
must reproduce the coupled loop's own behaviour. A19 gated this on per-module sweep counts and got
7 058/7 058. The analogue here is stronger, because arm R reproduces the loop's *own exit
decision*: the replayed sweep count must equal the number of sweeps the live loop actually took.

| Scenario | design points | arm R sweeps == live loop sweeps |
|---|---|---|
| `large_tokamak_nof` | 149 | **149 / 149** |
| `low_aspect_ratio_DEMO` | 297 | **297 / 297** |
| `st_regression` | 144 | **144 / 144** |
| `large_tokamak_eval` | 10 | **10 / 10** |

**It did not pass first time, and the failure is worth recording.** The first pass gave 599/600.
The single failure was `large_tokamak_eval` design point 8: the live loop took 2 sweeps, my replay
took 3, deterministically, in every repetition and regardless of arm ordering.

The cause is a property of PROCESS that no document in this project had recorded.
`Caller.call_models(xc, m)` compares a constraint vector of length `m`, and **`m` is not always the
total constraint count.** On the `fsolve` path — which is how an *evaluation* run is solved —
`solver.py:383` calls the evaluator with `self.meq`, the number of *equality* constraints alone.
So `large_tokamak_eval`'s idempotence loop compares a **2-vector** for 25 of its 31 constraint
evaluations and a **25-vector** for the other 6. Arm R had hard-coded the total. Measured directly
by the corrected instrument:

| Scenario | constraint-vector lengths seen, with counts |
|---|---|
| `large_tokamak_nof` | 26 × 2 028 |
| `low_aspect_ratio_DEMO` | 25 × 4 285 |
| `st_regression` | 18 × 1 890 |
| `large_tokamak_eval` | **2 × 25, and 25 × 6** |

The three optimising scenarios use one length throughout, which is why their fidelity was 100 %
from the first pass; only the evaluation run mixes them. The disagreement was a predicate flip at
the tolerance boundary rather than a divergence — the objective agreed to 2.5 × 10⁻⁹ relative
between the two sweeps my replay called "not idempotent" — which is itself a demonstration of how
finely balanced `np.allclose(rtol=1e-6)` with its hidden `atol=1e-8` is on this constraint set
(see §5).

**This was fixed, not worked around.** The harvest now records the constraint-vector length per
design point, read off the `constraint_eqns` wrapper it already installs for the magnitude
histogram — so still **no new hook site in `process/`** — and arm R uses it. The whole pipeline
(harvest, ladder, all replays, all gates) was then re-run from scratch. Nothing was retried with
different settings and no tolerance, cap or subsample was touched.

**A hypothesis that was tested and refuted along the way**, recorded because it would otherwise be
the obvious explanation for anyone re-reading this: that a cross-process replay cannot capture
state held on model objects rather than in the `DataStructure`. Enumerated directly — model
instances hold **70 non-`DataStructure` attributes across the whole registry, and every one of them
is a file-unit integer**. There is no model-held numeric state for a cross-process harvest to miss.

### 2.5 Gate R — restore exactness · **PASS, 0 mismatched fields**

A19 verified its in-process restore field by field and got 0 mismatches across all 2 288 fields in
2 447 replays. This restore crosses a process boundary, so it is verified the same way, **before
every arm of every design point**: 600 design points × 4 arms = 2 400 restores, each checked across
all 2 288 data-structure fields, **0 mismatches**, in all four scenarios and at both hoist settings.

---

## 3. What was built, and where it lives

Everything is in `arch_surgery/` except **one new mode** in the existing probe module. **No new
hook call site was added to `process/`**, as EXPERIMENT_FRAMEWORK.md §1.4 anticipated: the
`sweep(models, data)` hook A1 installed at `caller.py:273` already hands over both the model
registry and the data structure, which is everything the harvest needs.

| Path | What | `process/` touched |
|---|---|---|
| `process/core/_idf_probe.py` | one line added to the valid-mode tuple, one import branch | additive only |
| `process/core/_idf_probe_harvest.py` | **new** — the harvest mode | new file, imported only in that mode |
| `arch_surgery/docs/data/dsm_node_map.json` | **F4 / C8** — the committed node map | no |
| `arch_surgery/fixedpoint/nodemap.py` | loader and the subset assertion | no |
| `arch_surgery/fixedpoint/gen_node_map.py` | generator for the map above | no |
| `arch_surgery/fixedpoint/ystate.py` | the coupling state, its categories, scales and predicate | no |
| `arch_surgery/fixedpoint/engine.py` | **C9** — Gauss-Seidel, caps, exit audit | no |
| `arch_surgery/fixedpoint/arms.py` | R / A0 / A0f / A1, and the hoist toggle | no |
| `arch_surgery/fixedpoint/replay.py` | the per-scenario replay subprocess | no |
| `arch_surgery/fixedpoint/run_phase_a.py` | **the entry point** — `run_all()` and its CLI | no |
| `arch_surgery/fixedpoint/analyse.py`, `tables.py` | gates, drop census, ratios, tables | no |

**Why the harvest is a separate file rather than a fourth branch inside `_idf_probe`.**
`_idf_probe` is imported unconditionally by every instrumented file, and the project's neutrality
argument rests on it staying a bare switch plus counters; anything placed *in* it is imported on
the disabled path too. A2's and A19's instruments are separate files for exactly that reason, and a
fourth follows the established shape. F1 (the probe consolidation) is scheduled to merge all four
afterwards under a bit-identity gate, and is unaffected by this choice.

### 3.1 F4 — the DSM node map

**Derived from `_idf_probe_modules.NODE_MODULE`, not reinvented**, as the brief required.
`NODE_MODULE` is A2's mapping, itself built from D8's collapsed-DSM decomposition and then
validated against a run-time node census in four scenarios. `gen_node_map.py` reads it and adds the
DSM-row information our own committed documents state.

**Validation is a three-line assertion**: observed nodes ⊆ mapped nodes, raising on an observed
node the map does not name. Not equality — per `DSM_VALIDATION.md` V6 the map is
configuration-specific, `Pulse` writes nothing under `i_pulsed_plant = 0`, and
`models.tfcoil.run()` is reached in none of the four decks, so an equality check would fail on a
correct run. Executed on every replay of every scenario: **0 unmapped observed nodes**, and the
mapped-but-not-observed set is exactly the switch-selected alternatives.

**The map carries both unit systems, deliberately.** The collapsed DSM's rows and the model calls
in `_call_models_once` do not correspond one to one, and conflating them in a cost argument is the
error `DSM_VALIDATION.md` flags under "Open":

| Unit | M1 | M2 | M3 | `Pulse` | feed-forward | total |
|---|---|---|---|---|---|---|
| **DSM rows** (D8) | 24 | 10 | 12 | 1 | 5 | 52 executed of 56 |
| **model calls observed** (all four decks) | 2 | 3 | 13 | 1 | 2 | 21 |

Thirteen of M3's twelve DSM rows are one `run()` call each; M1's 24 rows are **two** calls,
`plasma_geom` and `physics`, because `physics.run()` orchestrates a whole block of sub-models
internally. That is a factor of twelve between the two units on M1 alone, and it is why every
count in this report is stated in model calls and says so.

**What the map cannot carry, and why.** A per-node DSM *row number* exists only in the
dependency-analysis repository's generated exports, and trap T9 forbids reading those live. The map
fills in the four rows our own committed documents state (5, 39, 41, 48) and leaves the rest
`null`. Closing that needs a per-row name export from `PROCESS_code_analysis`, requested rather
than scraped. Recorded in `DSM_VALIDATION.md` "Open".

**External validation arrived during this task and required no change.** `PROCESS_code_analysis`
regenerated per-scenario DSMs (their M100). The three-module partition survives on
`low_aspect_ratio_DEMO` outright and on `st_regression` up to two boundary-respecting model
substitutions with zero new cross-module cells, so V6's pre-committed **withdrawal of the
`st_regression` block-arm result is not triggered**. Neither substitution touches this map, because
this map is derived from run-time instrumentation across all four scenarios rather than from the
DSM's single-deck graph: the TF-turn substitution is already covered (`cicc_sctfcoil` and
`croco_sctfcoil` are both M2), and `ElectronCyclotron` is not a node at this granularity. A map
built from the DSM alone would be under repair now. Full entry: `DSM_VALIDATION.md` **V8**.

### 3.2 The harvest mode

For a sampled subset of `call_models` invocations it saves the **pair** `(x, y0)` — the design
vector *and* the entry state, a copy of all 2 288 data-structure fields — plus the phase, the
sweeps the live loop took, and the constraint-vector length. Cached to disk, so the harvest is paid
once per scenario rather than once per arm.

| Scenario | `call_models` | design points kept | `fn` | `grad` | `grad_reconcile` | cache size |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 630 | 149 | 14 | 600 → 120 | 15 | 36 MB |
| `low_aspect_ratio_DEMO` | 1 240 | 297 | 30 | 1 178 → 236 | 31 | 72 MB |
| `st_regression` | 570 | 144 | 18 | 532 → 107 | 19 | 35 MB |
| `large_tokamak_eval` | 11 | 10 | 10 | — | — | 2.5 MB |

All `fn` and `grad_reconcile` points are kept; 1 in 5 `grad` points. A19 §5.2 established that
perturbed points behave no differently from unperturbed ones. The very first `call_models` of each
run is skipped, because the node registry is still being built during its first sweep — one point
out of hundreds, and the same exclusion A19 made.

**The snapshot is taken after design-vector injection**, on the first sweep of each sampled
`call_models`. This matches what the coupled loop presents to the models. A19 §5.3 measured the
alternative and found identical counts in every loop of every scenario, so the convention does not
carry any result — but it is now recorded rather than implicit, which was one of the three
decisions the brief asked to have stated.

**The model sequence is measured, not reconstructed.** The harvest records the nodes
`_idf_probe_modules` saw execute inside `_call_models_once`, in order, and the replay drives that
list. A19 had to mirror `_call_models_once`'s switch dispatch by hand, which is the one part of
that instrument that could silently drift from the driver. This cannot. The observed order is
identical on every sweep of every run (**1 distinct order per scenario**, from 2 029 / 4 286 /
1 891 / 29 sweeps), and differs between scenarios only in the switch-selected TF-turn model.

Trap **T7** — ten models call their own `run()` from `output()` — does not arise: the replay
process never calls `output()` at all.

---

## 4. The coupling state `y`, categorised by measurement

`y` is **set (b)** of EXPERIMENT_FRAMEWORK.md §2.4: every data-structure field written by a model
node inside a sweep, taken from run-time instrumentation rather than from the DSM. The design-vector
injection and the objective/constraint block are excluded — the first is an input to the fixed
point, the second computes the quantities the fixed point is deliberately *not* judged on.

Every component's category is decided **by measurement over the harvest**, never by hand:

| Scenario | components | continuous | discrete | constant | NaN in harvest | harvest points | median scale |
|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 840 | 694 | 5 | 140 | 1 | 149 | 45.3 |
| `low_aspect_ratio_DEMO` | 846 | 698 | 5 | 143 | 0 | 297 | 41.0 |
| `st_regression` | 827 | 582 | 2 | 243 | 0 | 144 | 40.3 |
| `large_tokamak_eval` | 840 | 285 | 0 | 555 | 0 | **10** | 56.4 |

**The scale.** `s_i = median |y_i|` over the harvested design points, restricted to the points
where the component is non-zero, so a component that is zero at half the points is still scaled by
its own working magnitude. Arrays get a **per-array** scale (the median over design points of
`max |elements|`) and an **element-wise** test, because elements of one array share units and a
per-element scale would make a quiet element of a loud array hypersensitive. This is what replaces
2 288 hand-set absolute tolerances, and it is what avoids inheriting numpy's hidden `atol = 1e-8`.

**Excluded components fail loudly, and they did not fire.** A component identical at every
harvested design point is classified `constant`, excluded from the tolerance test, and then
*asserted* to stay constant at run time. Across all 600 design points and all four arms, at both
hoist settings, exactly **one** constant moved in one scenario — `ccfe_hcpb.x_shield`, on 3 of
`st_regression`'s 144 points — and it blocked convergence at those sweeps rather than passing
silently, which is the intended behaviour. On `large_tokamak_nof`, `low_aspect_ratio_DEMO` and both
hoist settings the count is **zero**.

**`large_tokamak_eval`'s categorisation is under-powered and must be read with that caveat.** With
only 10 harvested entry states, 555 of 840 components look constant, against 140–243 in the
scenarios with 144–297 points. Two of those apparent constants (`physics.vs_plasma_burn_required`,
`physics.vs_plasma_total_required`) then moved 21 times each — they are not constants, the sample
was too small to see them vary. The reliability of the `constant` category is bounded by the
harvest size, and 10 points is not enough. It changed no result (that scenario's drop census is
still 10/10 on every arm) but no conclusion should rest on `large_tokamak_eval`'s category counts.

**NaN is never converged.** A component finite in the harvest and NaN during a solve is a hard
non-convergence, not an `equal_nan` pass. One component
(`current_drive.eta_cd_dimensionless_hcd_primary`, `large_tokamak_nof`) is NaN somewhere in the
harvest itself and is excluded and counted rather than silently admitted. `low_aspect_ratio_DEMO`
raises `RuntimeWarning: invalid value` in `pfcoil.py` during the replay — and raises the *same*
warnings in the live instrumented run, so it is upstream behaviour on that deck, not a replay
artefact. No new NaN appeared in any exit audit, in any arm, in any scenario.

---

## 5. The magnitude commitment (architecture-evaluation F1 addendum)

This is the outstanding commitment to `PROCESS_code_analysis` and it is now discharged. The F1
addendum measured the magnitude distribution of quantities in the **MFILE** set — `MDA_Output`'s —
and found 18.0 % of non-zero quantities below the 1e-2 crossover where `np.allclose`'s hidden
`atol = 1e-8` starts to dominate its `rtol = 1e-6` term, with 203 entries below 1e-8 where
agreement is unconditional. It explicitly left **the idempotence loop's own set** unmeasured.
Measured here, from every `objf` and every constraint vector evaluated inside `Caller.call_models`
during a full optimisation run of each scenario:

| Scenario | quantity | n | ≤1e-8 | 1e-8..1e-6 | 1e-6..1e-4 | 1e-4..1e-2 | 1e-2..1 | 1..1e3 | >1e3 | zero |
|---|---|---|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | `objf` | 2 027 | 0 | 0 | 0 | 0 | 0 | 2 027 | 0 | 0 |
| | `conf` | 52 728 | **892** | 792 | 4 270 | 11 609 | 34 504 | 661 | 0 | 0 |
| `low_aspect_ratio_DEMO` | `objf` | 4 284 | 0 | 0 | 0 | 0 | 4 283 | 1 | 0 | 0 |
| | `conf` | 107 125 | **20 342** | 4 626 | 8 085 | 22 199 | 51 731 | 141 | 1 | 0 |
| `st_regression` | `objf` | 1 889 | 0 | 0 | 0 | 0 | 0 | 1 888 | 0 | 1 |
| | `conf` | 34 020 | **2 084** | 1 904 | 2 704 | 4 770 | 18 275 | 4 283 | 0 | 0 |
| `large_tokamak_eval` | `objf` | 30 | 0 | 0 | 0 | 0 | 29 | 0 | 1 | 0 |
| | `conf` | 200 | **22** | 2 | 22 | 22 | 126 | 6 | 0 | 0 |

Bin membership is `|v| ≤ edge`; zeros are counted separately from every bin (there are none in the
constraint vectors). No NaN or infinity appeared in any `objf` or `conf` in any scenario.

**The hole is larger in the idempotence loop's set than in the MFILE set.**

| Scenario | non-zero `conf` entries below **1e-2** (`atol` dominates) | below **1e-8** (agreement unconditional) |
|---|---|---|
| `large_tokamak_nof` | 17 563 / 52 728 = **33.3 %** | 892 = **1.7 %** |
| `low_aspect_ratio_DEMO` | 55 252 / 107 125 = **51.6 %** | 20 342 = **19.0 %** |
| `st_regression` | 11 462 / 34 020 = **33.7 %** | 2 084 = **6.1 %** |
| `large_tokamak_eval` | 68 / 200 = **34.0 %** | 22 = **11.0 %** |

Against the MFILE set's 18.0 % below 1e-2 and 203 entries below 1e-8. On
`low_aspect_ratio_DEMO`, **19 % of every constraint value the idempotence loop ever compares is
small enough that `np.allclose` reports agreement no matter what the value does**, and more than
half are in the regime where the absolute term rather than the relative term decides. This is the
hole the Phase A predicate was designed not to inherit, quantified on the set that matters, and it
is the direct mechanism behind the §2.4 fidelity failure and the §7 exit-audit finding.

---

## 6. The τ calibration ladder

Run **first**, before any arm comparison, on the **flat arm only**, so that one tolerance is chosen
once and every arm is then held to it — a comparison at different tolerances is not paired. The
honest distinction: convergence is tested on `y`; τ is *calibrated* by its effect on `objf` and the
constraint vector, measured **at termination**, before the audit sweep relaxes the state any
further. Calibration is not the predicate.

| Scenario | τ | converged | mean sweeps | model evaluations | max \|Δ`objf`\| vs tightest | max \|Δ`conf`‖₂\| vs tightest | worst exit residual |
|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 1e-8 | 149/149 | 3.819 | 11 949 | — | — | 1.57e-11 |
| | **1e-6** | 149/149 | 3.027 | 9 471 | **0** | 5.0e-12 | 1.05e-08 |
| | 1e-4 | 149/149 | 2.570 | 8 043 | **0** | 6.9e-08 | 2.19e-05 |
| `low_aspect_ratio_DEMO` | 1e-8 | 297/297 | 3.848 | 24 003 | — | — | 9.51e-13 |
| | **1e-6** | 297/297 | 3.205 | 19 992 | **4.1e-16** | — | 1.67e-08 |
| | 1e-4 | 297/297 | 2.808 | 17 514 | **7.9e-07** | — | 2.20e-05 |
| `st_regression` | 1e-8 | 144/144 | 4.090 | 12 369 | — | — | 3.33e-10 |
| | **1e-6** | 144/144 | 3.438 | 10 395 | **2.0e-13** | — | 3.17e-08 |
| | 1e-4 | 144/144 | 2.931 | 8 862 | **2.7e-07** | — | 3.36e-06 |
| `large_tokamak_eval` | 1e-8 | 10/10 | 2.600 | 546 | — | — | 0 |
| | **1e-6** | 10/10 | 2.500 | 525 | **0** | — | 0 |
| | 1e-4 | 10/10 | 2.400 | 504 | **0** | — | 0 |

**τ = 1e-6 is the calibration point, and the ladder is itself the result.** Tightening from 1e-6
to 1e-8 moves the objective by **at most 4.1 × 10⁻¹⁶ relative** — machine epsilon, i.e. not at all
— while costing **19–26 % more model evaluations** on the three optimising scenarios (4 % on the evaluation run). Loosening to 1e-4 moves it by up to
**7.9 × 10⁻⁷ relative**, which is larger than these decks' own solver convergence parameter of
1e-7, so 1e-4 is not safe even though it is 12–15 % cheaper. Past 1e-6 you are converging noise, and
the ladder says so with numbers rather than by assertion.

**Every point converges at every tolerance on the ladder.** No caps, no drops, 1 800 / 1 800 point-solves.

**One column must be read with a caveat.** On `large_tokamak_nof` the objective is `0.2 × rmajor`
and `rmajor` **is an iteration variable** — the objective there is a pure function of `x` and
*cannot* move with τ, so its zeros are structural, not evidence. `low_aspect_ratio_DEMO` (maximise
pulse length), `st_regression` (maximise fusion gain) and `large_tokamak_eval` (minimise capital
cost) all have computed objectives, and they carry the calibration.

---

## 7. The comparison

### 7.1 Drop census — reported first, before any ratio

| Scenario | points | R | A0 | A0f | A1 | pairwise-complete | dropped | caps reached |
|---|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 149 | 149 | 149 | 149 | 149 | **149** | **0** | none |
| `low_aspect_ratio_DEMO` | 297 | 297 | 297 | 297 | 297 | **297** | **0** | none |
| `st_regression` | 144 | 144 | 144 | 144 | 144 | **144** | **0** | none |
| `large_tokamak_eval` | 10 | 10 | 10 | 10 | 10 | **10** | **0** | none |

**Nothing was dropped, by any arm, in any scenario, at either hoist setting.** No inner cap, no
outer cap and no global cap was reached at any point — the caps stayed detectors and never became
budgets. The observed maxima are far below them: 6 flat sweeps against an outer cap of 20, 12 in
the single worst case, and 12 inner module-sweeps against an inner cap of 20.

Every ratio below is therefore over the same 600 design points for all four arms.

### 7.2 Counts, hoist off

Model evaluations are the primary unit. A flat sweep is 21 model calls; a block outer iteration is
however many inner module-sweeps it took. **Nodes are not equal in cost** — `physics.run()`
orchestrates a whole sub-model block while `cryostat.run()` does not — so a model-call count is a
count, not a cost, and no cost weight is applied because the only available weight would be a
timing (working rules; issue I-10).

| Scenario | arm | mean sweeps | sweep histogram | model evaluations | vs R |
|---|---|---|---|---|---|
| `large_tokamak_nof` | R | 3.027 | 2:37 · 3:76 · 4:31 · 5:5 | 9 471 | 1.000 |
| n = 149 | A0 | 3.027 | **1:7** · 2:30 · 3:76 · 4:25 · 5:10 · 6:1 | 9 471 | **1.000** |
| | A0f | 3.074 | 2:37 · 3:76 · 4:25 · 5:10 · 6:1 | 9 618 | 1.016 |
| | A1 | **2.705** | 1:7 · 2:30 · 3:112 | 13 906 | **1.468** |
| `low_aspect_ratio_DEMO` | R | 3.370 | 2:48 · 3:151 · 4:38 · 5:60 | 21 021 | 1.000 |
| n = 297 | A0 | 3.205 | **1:15** · 2:26 · 3:165 · 4:65 · 5:26 | 19 992 | **0.951** |
| | A0f | 3.256 | 2:41 · 3:165 · 4:65 · 5:26 | 20 307 | 0.966 |
| | A1 | **2.721** | 1:15 · 2:53 · 3:229 | 28 070 | **1.335** |
| `st_regression` | R | 3.222 | 2:28 · 3:68 · 4:37 · 5:10 · 6:1 | 9 744 | 1.000 |
| n = 144 | A0 | 3.438 | **1:9** · 2:15 · 3:67 · 4:39 · 5:8 · **9:3 · 10:2 · 12:1** | 10 395 | 1.067 |
| | A0f | 3.500 | 2:24 · 3:67 · 4:39 · 5:8 · 9:3 · 10:2 · 12:1 | 10 584 | 1.086 |
| | A1 | **2.139** | 1:9 · 2:128 · 4:1 · 6:3 · 7:3 | 9 917 | **1.018** |
| `large_tokamak_eval` | R | 2.200 | 2:8 · 3:2 | 462 | 1.000 |
| n = 10 | A0 | 2.500 | 1:3 · 3:6 · 4:1 | 525 | 1.136 |
| | A0f | 2.800 | 2:3 · 3:6 · 4:1 | 588 | 1.273 |
| | A1 | 2.400 | 1:3 · 3:7 | 618 | 1.338 |

**What the sweep histograms say that the means do not.**

- **The floor of 1 is real.** A0's histogram has a `1:` column that is structurally impossible for
  R and for A0f. 7, 15, 9 and 3 design points respectively converge in a single sweep — 4.7 %,
  5.1 %, 6.3 % and 30 %.
- **The strict predicate has a tail, and on `st_regression` it is long.** A0 needs 9, 10 and 12
  sweeps on 6 of 144 points where R never exceeds 6. §7.4 identifies what those points are.
- **The block arm's outer count collapses.** On `st_regression`, 137 of 144 points need at most 2
  outer iterations. On the two large tokamaks the outer count falls on 43 and 115 points and rises
  on none.

### 7.3 The three-way decomposition — what A0f is for

`R → A0f` is the strict predicate's cost with the floor held at 2. `A0f → A0` is the floor removal
alone. `R → A0` can only ever report their sum, and they act in opposite directions.

| Scenario | R → A0f (predicate) | A0f → A0 (floor) | R → A0 (sum) |
|---|---|---|---|
| `large_tokamak_nof` | **+1.55 %** | **−1.53 %** | **0.00 %** |
| `low_aspect_ratio_DEMO` | −3.40 % | −1.55 % | −4.90 % |
| `st_regression` | +8.62 % | −1.79 % | +6.68 % |
| `large_tokamak_eval` | +27.3 % | −10.7 % | +13.6 % |

**`large_tokamak_nof` is the worked example the brief predicted.** The two arms produce *exactly*
9 471 model evaluations. Per design point they do not agree at all — the paired difference
histogram is `−1 sweep: 8 points · 0: 134 · +1: 6 · +2: 1` — so a study that ran only `R → A0`
would have reported "no effect" from two real, opposed effects of 1.5 % each. This is the single
clearest justification for A0f being in the design.

**The predicate is not uniformly a cost.** On `low_aspect_ratio_DEMO` the strict test is *cheaper*
than the loose one by 3.4 %: 54 points converge a sweep sooner because `objf`/`conf` were still
disagreeing when the coupling state had already settled. That direction was not anticipated.

### 7.4 Exit audit — matched final accuracy, verified per design point

Every arm gets one further full sweep past termination and the **same** global residual is
evaluated, so accuracy is verified per point rather than assumed from a shared tolerance.

| Scenario | arm | worst exit residual over points | median | points failing the audit at τ |
|---|---|---|---|---|
| `large_tokamak_nof` | R | **2.49e-06** | 0 | **1 / 149** |
| | A0 / A0f | 1.05e-08 | 0 | 0 / 149 |
| | A1 | 3.01e-13 | 0 | 0 / 149 |
| `low_aspect_ratio_DEMO` | R | 2.79e-10 | 0 | 0 / 297 |
| | A0 / A0f | 1.67e-08 | 0 | 0 / 297 |
| | A1 | 2.18e-11 | 0 | 0 / 297 |
| `st_regression` | R | **8.11e+08** | 2.6e-14 | **7 / 144** |
| | A0 / A0f | 3.17e-08 | 0 | 0 / 144 |
| | A1 | 1.08e-09 | 0 | 0 / 144 |
| `large_tokamak_eval` | R | 2.50e-10 | 3.9e-13 | 0 / 10 |
| | A0 / A0f / A1 | 0 | 0 | 0 / 10 |

**Two things this settles, and one caveat it raises.**

**(a) The incumbent loop stops with state still moving, on 8 of 600 design points, and it is always
the cost model.** The fields above tolerance are `costs.coe`, `costs.coecap`, `costs.coefuelt` on
all 8, plus `costs.bktcycles`, `costs.coeoam` and `power.qac` on the `large_tokamak_nof` one.
These are the feed-forward tail: nothing reads them back inside the loop, which is exactly why a
predicate watching only `objf` and `conf` cannot see them move. **Read this as a predicate finding,
not a physics claim.** `costs.coecap` ranges from 102 to 6.5 × 10²¹ across `st_regression`'s
harvested entry states, so its median-based scale is a weak normaliser for that particular field
and the figure 8.11 × 10⁸ overstates how surprising the *absolute* change is. What does not depend
on the normaliser is that the field is still changing by orders of magnitude when the loop declares
itself idempotent.

**(b) The arms are not at equal accuracy, and the exit audit is what reveals it.** A1 terminates
at a residual roughly **10⁵ times tighter** than A0 at the same τ, because its inner solves drive
each module to τ and the outer test then passes at once. So A1's +33–47 % is cost at *better*
accuracy, not cost at equal accuracy. D13 chose a tight inner tolerance and called it "conservative
against the partition"; this quantifies how conservative. The inexact-block regime — a looser inner
tolerance — is the axis D13 deferred, and it is the obvious next thing to vary if the partition is
pursued.

### 7.5 The feed-forward hoist

Applied to **all** arms so it cancels and the comparison stays topological. The tail (`water_use`,
`costs`) runs once **after the outer fixed point converges**, not after each inner solve.

| Scenario | arm | model evaluations, hoist off → on | A1 / A0, hoist off → on |
|---|---|---|---|
| `large_tokamak_nof` | A0 | 9 471 → 8 569 (**−9.5 %**) | 1.468 → 1.529 |
| `low_aspect_ratio_DEMO` | A0 | 19 992 → 18 088 (**−9.5 %**) | 1.404 → 1.463 |
| `st_regression` | A0 | 10 395 → 8 683 (**−16.5 %**) | 0.954 → 1.008 |
| `large_tokamak_eval` | A0 | 525 → 475 (**−9.5 %**) | 1.177 → 1.200 |

The hoist saves the arithmetic 2 of 21 nodes = 9.5 % everywhere, and on `st_regression` it saves
**16.5 %** — because it also removes the strict predicate's entire long tail. A0's histogram there
goes from `… 9:3 · 10:2 · 12:1` to a maximum of 6, and A1's outer count collapses to `1:9 · 2:135`.
**The stragglers were the cost model.** That is a mechanistic result, not a coincidence: the same
fields that arm R leaves un-converged in §7.4 are the ones the strict predicate spends its longest
tails converging.

**Two honest caveats on the hoist.**

- Hoisting does not converge those fields; it *stops asking*. At hoist = 1 on `st_regression` all
  four arms show an exit residual of 8.11e+08, because the audit still runs the full node set and
  the tail has been solved once rather than iterated. That is defensible — the tail feeds nothing
  back, so the state it is computed from is converged even if it is not itself iterated — but it
  should be stated rather than presented as a saving with no consequence.
- **The hoist is not neutral for arm R when the objective is a feed-forward quantity.**
  `large_tokamak_eval` minimises capital cost, computed by `costs`, which the hoist removes from
  the loop; R-with-hoist therefore evaluates its own predicate on a one-sweep-stale cost. It
  changed no count there, but it is a composition hazard of exactly the kind C2a warns about, and
  the hoist × arm-R combination should not be quoted without it.

---

## 8. The DSM cross-check (C10)

The coupling set is computed two ways: from run-time instrumentation (set (b), which decides
convergence) and from the DSM's cross-module feedback edges (set (a), the four fields recorded in
`DSM_VALIDATION.md` V2–V5). The sweep at which each *would have* declared convergence is recorded
for every design point.

| Scenario | points | set (a) stops **earlier** | agree | set (a) stops **later** | mean sweeps set (a) would have skipped |
|---|---|---|---|---|---|
| `large_tokamak_nof` | 149 | **142 (95.3 %)** | 7 | **0** | 0.96 |
| `low_aspect_ratio_DEMO` | 297 | **282 (94.9 %)** | 15 | **0** | 1.12 |
| `st_regression` | 144 | **135 (93.8 %)** | 9 | **0** | 2.44 |
| `large_tokamak_eval` | 10 | 7 | 3 | **0** | 1.20 |

**Never once later, in 600 design points.** Three of set (a)'s four fields are classified
`constant` across the whole harvest — the three edges V3 and V4 already recorded as structurally
present but dead in this deck — and the categoriser reaches that verdict independently, from 600
entry states, without being told. On `st_regression` the fourth, `times.t_plant_pulse_burn`, is
**absent from set (b) entirely**: with `i_pulsed_plant = 0` no in-loop model writes it, and the
`Pulse` block's coupling-state subset is empty. That is A2's `k = 0` re-derived by a second
instrument.

**The DSM is not wrong; using it as the predicate would be.** Filed as `DSM_VALIDATION.md` **V7**,
with **V8** recording the per-scenario regeneration result from §3.1. That register accumulates and
is not archived at merge, which is why the finding lives there rather than only here.

---

## 9. Runtime, as context only

**No conclusion in this report rests on a timing.** Every acceptance quantity above is a count of
model evaluations or an exact bit-comparison, and all of them reproduced identically across two
full pipeline runs. The figures below are recorded because the brief gave a budget, and with two
caveats: the machine was **not quiet** — a sibling project was running two analysis-pipeline passes
and a timed gate suite concurrently for part of this work, and some of my own stages overlapped —
and issue **I-10** records that identical work varies up to 35 % in CPU-seconds on this host for
reasons not yet identified.

| Stage | Cost, one full pass, four scenarios |
|---|---|
| Harvest (one instrumented PROCESS run per scenario) | 87 + 188 + 82 + 6 s = **364 s** |
| τ ladder (12 replays) | 5.1–26.0 s each, **163 s** |
| Arm comparison, 4 arms × 4 scenarios × 2 repetitions, plus the hoist variant | 6.0–79.2 s each, **513 s** |
| Gate suite (16 PROCESS runs) | 6.4–192 s each, **883 s** |

The brief's budget was "a few minutes for a full multi-arm pass with a cached harvest". A **single**
pass of all four arms over all four scenarios is **157 s**; the 513 s above is three such passes
(two repetitions for the determinism gate, plus the hoist variant). Inside the budget. The harvest and the gate suite are PROCESS runs and are the same cost they have
always been. Nothing here is above budget in a way that needed a design response, and nothing was
tuned to make a number look better.

---

## 10. Autonomous decisions, each with its reversal path

| # | Decision | Why | How to reverse |
|---|---|---|---|
| 1 | **The harvest is a new file, `_idf_probe_harvest.py`, not a branch inside `_idf_probe.py`** | `_idf_probe` is imported on the disabled path by every instrumented file; the neutrality argument rests on it staying a bare switch. A2 and A19 made the same choice | Delete the file and inline it; the mode tuple and import branch in `_idf_probe.py` are three lines |
| 2 | **`m`, the constraint-vector length, is recorded per design point and used by arm R** | Not doing so made arm R wrong on the fsolve path and cost a fidelity gate (§2.4) | Drop `p["m"]` and the `m=` argument to `Sweeper`; arm R falls back to the total, and the eval scenario's fidelity returns to 9/10 |
| 3 | **A moved constant blocks convergence at that sweep and is named, rather than raising** | The brief says excluded components must fail loudly. An exception would abort a whole scenario on one field; blocking convergence plus naming the field is loud without destroying the run. It fired on 3 design points of one scenario out of 600, and blocked convergence at those sweeps rather than passing silently | In `ystate.Residual.converged`, raise instead of returning False on `moved_constant` |
| 4 | **The category/scale spec is always built from the *whole* harvest, even when a subset is solved** | A scale from a handful of points is not a characteristic magnitude, and components look "constant" far too easily in a small sample — measured directly: at 6 points, 6 constants moved; at 149 points, none | Pass the solved subset to `YSpec.from_harvest` instead of `all_points` |
| 5 | **The `y` set is fixed across hoist settings** (it always contains the feed-forward tail's fields) | Keeps the exit audit identical across arms *and* across hoist settings, which is what makes §7.5's two columns comparable | Filter `y_keys` by the active hoist setting in `replay.py` |
| 6 | **The exit audit runs the full node set (hoist off) for every arm** | Makes "matched final accuracy" one number with one meaning. The consequence — hoisted arms show the tail un-converged — is reported in §7.5 rather than hidden by narrowing the audit | Pass `ln` instead of `all_nodes` to `exit_audit` |
| 7 | **The global cap counts one module-sweep per flat sweep and one per inner sub-sweep** | Makes the 200 cap a real guard for the block arm without making it bind absurdly early for the flat arm. Nothing came close to it | Change `Budget.charge_module_sweep` accounting in `engine.py` |
| 8 | **Both hoist settings are reported, with hoist off as the headline** | The brief asks for the hoist applied to all arms in first results; running both costs one extra pass and lets arm R stay literally "today's loop" in the headline table | Quote §7.5's hoist-on columns as the headline instead |
| 9 | **`control_rep2` dropped from the gate suite** | A1 already gated the tree's own determinism at this base commit; what is new is the harvest arm, whose replicate is present | Re-add the tuple entry in `run_phase_a.cmd_gates` |

---

## 11. Things that contradict, or sharpen, the plan

**Flagged prominently, as the brief asked, because the plan is a hypothesis.**

**11.1 The partition's own arithmetic points the wrong way once you count model evaluations.**
EXPERIMENT_FRAMEWORK.md and the partition plan reason about *sweeps*. Measured in sweeps the block
arm wins everywhere. Measured in **model evaluations**, which is what actually costs, it loses by
33–47 % on three of four scenarios. The two units diverge because a block arm's inner solves are
sweeps over a *subset* of nodes, and there are more of them. **Any future statement of the
partition's benefit has to name its unit**, and the DSM-row unit is a third one again (§3.1): 52
DSM rows against 21 model calls, with M1's 24 rows being 2 calls.

**11.2 The one scenario where the block arm breaks even is the one with no coupler.**
`st_regression` has `k = 0`, and A18's instrument re-derives that independently (§8). Its outer
loop converges in ≤ 2 iterations on 137 of 144 points. That is the partition working exactly as
designed — and it is also the case where the partition is doing the least, because there is no
cross-module cycle to break. The plan's §3.2 condition, that the loop be driven by a *small*
module, is still not met anywhere.

**11.3 The strict predicate is not uniformly more expensive than the incumbent one.** The plan
treats VP3 as a cost to be justified. On `low_aspect_ratio_DEMO` it is 3.4 % *cheaper*: 54 of 297
points converge a sweep sooner because `objf`/`conf` were still disagreeing after the coupling
state had settled. The loose predicate is not merely permissive, it is also sometimes slower.

**11.4 The two-sweep floor is removable and is worth 1.5–11 %, but that is a smaller number than
the framing suggests.** It was described in the brief as "the single most valuable finding behind
this task". It is real and it is measured — 4.7–30 % of design points converge in one sweep — but
on the two large tokamaks its 1.5 % saving is almost exactly cancelled by the predicate's 1.5 %
cost. The net effect of moving from today's loop to the flat control is **zero on
`large_tokamak_nof`**, −4.9 % on `low_aspect_ratio_DEMO` and **+6.7 %** on `st_regression`.

**11.5 `Caller.call_models` does not always compare the same constraint vector.** New, and not
recorded anywhere in this project before §2.4. On the fsolve path it compares `meq` equality
constraints; on the final call it compares all of them. Anything that reproduces or reasons about
the idempotence loop has to know this. It has no bearing on the optimising scenarios.

**11.6 What the exit audit implies for how Phase A's findings would be carried into production.**
Open question 4 of EXPERIMENT_FRAMEWORK.md asks whether VP3's predicate goes into `caller.py` at
all. The evidence here is mixed and should be read as such: it catches a real defect (§7.4a), it is
sometimes cheaper and sometimes dearer (§11.3), and it needs a scale calibrated from a harvest,
which is a run-time artefact the production driver does not have. A production version would need
scales baked in or derived on the fly, and that is a design problem this task did not solve.

---

## 12. Change log (append-only)

| # | Change |
|---|---|
| 1 | Branch `A18-experiment-framework` cut from `architecture_surgery` at `73439685`. Worktree confirmed; the worktree had been created from `main` and was moved onto the correct base before any work. |
| 2 | `_idf_probe_harvest.py` written; `harvest` registered as a fourth probe mode. First harvest run of `large_tokamak_nof` succeeded: 149 design points, 840 coupling components, 0.21 s of capture cost in a 152 s run. |
| 3 | `dsm_node_map.json` generated from `_idf_probe_modules.NODE_MODULE`; subset assertion added and exercised. |
| 4 | `ystate.py`, `engine.py`, `arms.py`, `replay.py`, `run_phase_a.py`, `analyse.py`, `tables.py` written. Vertical slice run first: one scenario, arms R and A0, 6 design points, gates passing, before any breadth was added. |
| 5 | Commit `7d5c1c03`: harvest mode, node map, fixed-point engine. |
| 6 | Full harvest of all four scenarios; τ ladder; four-arm comparison at τ = 1e-6; hoist variant; gate suite started. |
| 7 | **τ ladder re-run** after finding that the exit audit measured `objf` *after* its extra sweep, which understates how much τ moves the answer. Corrected to record `objf` and `conf` at termination as well. Not a tuning change — the previous numbers were measuring the wrong thing. |
| 8 | **Replay-fidelity gate failed 599/600.** Diagnosed to `Caller.call_models`'s constraint-vector length on the fsolve path (§2.4). The "model objects hold un-captured state" hypothesis was tested and refuted first (70 non-`DataStructure` attributes, all file units). |
| 9 | Fix applied: the harvest records `m` per design point; arm R uses it. Gate suite stopped mid-flight and **the entire pipeline re-run from scratch** — harvest, ladder, all replays, all gates — so no artifact mixes instrument versions. Commit `595bccba`. |
| 10 | `DSM_VALIDATION.md` gains **V7** (the DSM feedback set stops 0.96–2.44 sweeps early on 94–95 % of points, never late) and **V8** (per-scenario DSM regeneration: the partition survives, the `st_regression` withdrawal is not triggered, the run-time map needed no change). The "Open" item on DSM-row vs model-call units marked addressed, with the residual per-row-number gap stated. |
| 11 | Node map records M2's membership by switch (`i_tf_turn_type`) rather than by class name, per the sibling study's refinement. |
| 12 | Re-run complete: replay fidelity **600/600**, all five gates PASS, drop census 100 % on every arm. |
| 13 | `run_all()` added to `run_phase_a.py` as a callable entry point with every parameter surfaced in `PARAMETERS`, a plain-language docstring and a stated output shape; `all` subcommand added to the CLI. |
| 14 | This report written. |

---

## 13. Reproducing this

```
# a reference copy of the base commit, for the neutrality gate
git archive c0ae5b28 | tar -x -C /some/dir/pristine_c0ae5b28

# everything, in order
PYTHONPATH=<tree> python arch_surgery/fixedpoint/run_phase_a.py all \
    --pristine-tree /some/dir/pristine_c0ae5b28

# tables
python arch_surgery/fixedpoint/analyse.py --out report.json
python arch_surgery/fixedpoint/tables.py --report report.json
```

`run_all()` is importable and takes the same arguments. Artifacts land under
`arch_surgery/idf_probe/runs/a18/`, which is untracked; the summaries and verdicts in this document
are what is committed.

---

## Orchestrator's critical assessment (appended at merge, 2026-09-01)

**Verdict: accepted and merged. The task did what it was asked, and two of its three results
contradict the plan that commissioned it — including the plan's headline claim, which was mine.**

### What was done better than asked

**Gate F was failed, root-caused, and the whole pipeline re-run.** Replay fidelity came out
599/600. The cause is a genuine property of PROCESS that nobody had noticed: `Caller.call_models`
does not always compare a constraint vector of the same length, because the `fsolve` path passes
`meq` alone (`solver.py:383`), so `large_tokamak_eval`'s loop compares a 2-vector on 25 calls and
a 25-vector on 6. Arm R had hard-coded the total. The fix records the length per design point, and
**every artifact was regenerated from scratch** so that no result mixes instrument versions. The
obvious rival explanation — uncaptured state on the model objects — was tested and refuted rather
than assumed away. This is the behaviour §6 of the protocol asks for and it is rare to see it
taken this literally.

**A0f earned its place, exactly as predicted.** On `large_tokamak_nof` the reference and flat arms
produce *identically* 9 471 model evaluations — a 0.00 % difference — decomposing into +1.55 % for
the strict predicate and −1.53 % for the floor removal. Per design point they do not agree at all
(8 points cheaper, 7 dearer). A study without A0f would have reported "no effect" from two real,
opposed effects. The user's instruction to build it up front is vindicated by the one scenario
where it mattered most.

### The plan's headline claim is refuted, and the error was the orchestrator's

The partition plan (§1.2, §4.1) and the architecture evaluation's F8 addendum both state that
removing the two-sweep floor is worth **"up to 31 %"** of sweeps, on the arithmetic that one
information-free sweep per `call_models` is 630 of 2 027. **Measured: 1.53 %, 1.55 %, 1.79 % and
10.7 %.**

The arithmetic assumed a sweep is saved on *every* solve. It is saved only where the state is
already converged on entry, which is 4.7 %, 5.1 %, 6.3 % and 30 % of design points. "Up to" was
formally correct and practically misleading, and it was presented as the single most valuable
finding behind the task. **The floor is real — A0's histogram has a `1:` column that is
structurally impossible for the other arms — and it is worth about a fiftieth of what was
claimed.** Both documents must be corrected; the report `MDA_partition_exp_results.md` §2 (H1) is
now wrong as written and must not be published in its current form.

### The unit problem, which is the most consequential finding here

**In sweeps the block arm wins on every scenario. In model evaluations it loses by 33–47 %.** Both
are exact counts of real things. They disagree because a sweep over M1 is not the same work as a
sweep over everything.

This reaches further than the block arm. The plan's mechanism argument (§5.3) weights modules by
**DSM rows** — `|M1| = 24`, `|M2| = 10`, `|M3| = 12` — and that unit does not correspond to
execution: **M1 is 24 DSM rows but 2 of the 21 executing model calls**, because `physics.run()`
orchestrates a sub-model block internally. So the argument "M1 dominates the node count, therefore
partitioning saves little" is stated in a unit that overstates M1 by an order of magnitude.

Three candidate units, none of them satisfactory:

| Unit | Exact? | Tracks work? |
|---|---|---|
| DSM rows | yes | no — M1 is 52 % of rows, 38 % of measured cost |
| model calls | yes | no — `physics.run()` and `cryostat.run()` count the same |
| measured cost | **no** — issue I-10 | yes |

A18 chose model evaluations and refused to apply a cost weight, on the grounds that the only
available weight is a timing. That is the right call under this project's rules, and it leaves a
real hole: **the exact units are in the wrong currency and the right currency is not exact.** No
conclusion about the partition's cost should be stated without naming its unit, and §5.3 of the
plan needs rewriting rather than annotating.

### A reproducibility gap the task did not flag

**The per-quantity scales are computed from the harvest and never persisted.** `YState.from_points`
derives `s_i = median |y_i|` and uses it, but no artifact records the result, and `runs/` is
git-ignored. The predicate therefore depends on data that is not recorded anywhere.

In practice the numbers do reproduce — the determinism gate passes bit-for-bit and the harvest is
deterministic given a deterministic PROCESS run. What is lost is **auditability**: it is not
possible, after the fact, to inspect which scale a quantity received or to notice that one is
absurd. Given that the exclusion list is the design's most dangerous artifact and the scales are
what separate "excluded" from "included", they should be written to a committed artifact. Small
change; should be made before the results are published.

*(For the record, the scaling convention itself has precedent inside PROCESS: VMCON normalises each
iteration variable by its initial value, `scale[i] = 1.0/value`, having first rejected zero, NaN
and infinity — `iteration_variables.py:343-348`. The principle is the codebase's own. The code is
not reusable, since it covers ~20 design variables rather than ~2 288 state fields, and its choice
of the *initial* value is poorer than a median over observed states for this purpose.)*

### What now stands as evidence

- Appending, categorisation, the τ ladder and all five gates: **accepted**.
- The floor effect: **accepted, and an order of magnitude smaller than claimed**.
- The block arm's cost: **accepted in model evaluations, with the unit named**. It is not a
  refutation of the partition in every unit, and must not be reported as one.
- `st_regression` at 1.018: the one near-break-even, and the scenario with no cross-module coupler
  — consistent with the partition helping only where the blocks are genuinely independent.
- PROCESS's loop stopping with the cost model still moving (8/600): **a new finding about the
  program**, independent of the experiment, and worth routing.

