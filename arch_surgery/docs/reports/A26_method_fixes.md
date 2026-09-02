# A26 (method-fixes) — fixing the experiment's method before Phase B is re-run

> **Document status** — **CURRENT · TASK REPORT, open.** Written by task A26 (method-fixes),
> 2026-09-02, on branch `A26-method-fixes` at base `c0ae5b28`. It is archived to
> `deprecated/` when the task merges, and stays authoritative there (trap T3: folder position
> records lifecycle, not validity). Nothing here is merged; nothing is pushed.
> **This task changed the instrument. It did not re-run Phase B** — that is a later task, on the
> instrument left behind here. §11 says what that task must do differently.

---

## 1. Verdict

### The matched-accuracy comparison overturns Phase A's headline

**Phase A reported that the three-block partition costs 46.8 % and 40.4 % more model evaluations
than the flat control on the two large pulsed decks. Measured at matched *achieved* accuracy, it
costs 4.3 % and 4.5 % *less*.** On the third deck, where it was already reported 4.6 % cheaper, it
is 13.1 % cheaper.

| deck | n | published, at matched **tolerance** | measured, at matched **achieved accuracy** |
|---|---|---|---|
| `large_tokamak_nof` | 149 | **+46.8 %** | **−4.3 %** (9 062 against 9 471) |
| `low_aspect_ratio_DEMO` | 297 | **+40.4 %** | **−4.5 %** (19 087 against 19 992) |
| `st_regression` | 144 | **−4.6 %** | **−13.1 %** (9 037 against 10 395) |

The report's own §6.1 named this as the strongest objection to its headline and worded the finding
as *"at most 47 %, 40 % and 18 % more"*. **The bound was doing all the work.** §6.1 also offered a
counter-argument — that the outer pass counts fall by much less than the inner solves cost, so an
inexact inner tolerance "would have to recover a very large factor". It recovers all of it. The
inner solves at τ = 1e-6 were doing work the outer test did not need, and once that stops, the
handicap is the whole of the published difference.

**Read with its four caveats, which are in §3.3 and are not decoration.** The result is on the p90
of the exit residual; on the **worst** design point the two arms are indistinguishable (A1/A0 spans
0.82–1.23), and on the median the comparison cannot be made at all because the median exit residual
is exactly zero on most rungs. The mechanism is that the over-solving was the cost — at its
cheapest matched setting the block arm runs 1 172 of 1 248 inner solves in a single sweep, so it is
barely a block solver. The block arm had eleven ladder rungs against the flat arm's six. And this
is Phase A, with the optimiser absent.

**So the honest replacement for the headline is: at matched achieved accuracy the partition is at
parity or cheaper, and the +47 % / +40 % were the handicap.** It still does not say the partition
is *worth* anything — what it removes is the claim that it costs.

### The rest, in one line each

- **§4 — accounting settled.** The driver-side figure is canonical; the replay engine's is a stated
  cross-check. One definition, in one module, stated per arm pair; the engine's loop-only headline
  is gone.
- **§5 — nothing is excluded for never having varied.** All 840 / 846 / 827 components are now
  tested; 40 / 41 / 54 of them at the recorded scale floor of 1.0; the exclusion list is empty and
  that is a measured result, not an omission.
- **§6 — a comparison that cannot say what it varies refuses to run**, for any number of arms, and
  the hoist becomes a three-slot routing rule keyed on the driver's own measured predicate read set.
- **§7 — `pulse` leaves the model loop under the lift**, into a pre-predicate slot that never hands
  the optimiser a stale constraint vector. **The gate plan §4.1d specifies is vacuous on all four
  decks** and would have reported a meaningless zero; the non-vacuous gate is here instead.
- **§8 — timings carry an interval**, and were taken only after 71.5 % of the block arm's
  coupling-state read traffic — pure bookkeeping whose result was discarded — had been removed.
- **§9 — `large_tokamak_eval` dropped**, dated in every entry point, with merged four-deck tables
  left standing as the record.

### And the gate that licenses all of it

Every change that touches previously merged arms was re-run at A18's settings and compared against
A18's recorded artifacts **bit for bit**: **0 differing of 4 800 arm records over 64 800 record
keys**, both hoist settings, four decks, with the comparison shown capable of catching a 1-ULP move
**32 times out of 32**. It failed once first — on 600 of 600 points, over a change in the recorded
artifact's *shape* that moved no count — and was fixed rather than absorbed (§2).

**One finding that is not about this task's changes**: §6.3's licence for reusing A18's harvest —
that the model sub-trees are hash-identical to the recording commit — **is no longer true at the
current tip**, because A25's lift touched `process/models/pulse.py` and
`process/data_structure/numerics.py`. The reproduction gate is the replacement, and it is a
stronger claim (§2.1).


---

## 2. What was gated, before any number below is read

Three of the changes touch code that **every previously merged arm runs through**: the
subset-aware coupling-state read, the restructured residual, and the routing rule for hoisted
nodes. All three are supposed to be inert at A18's settings. "Supposed to be" is not a
measurement, so the instrument was re-run at A18's settings and compared against A18's recorded
artifacts **bit for bit, with no tolerance anywhere**.

| | design points | arm records compared | record keys compared | differing | sensitivity |
|---|---|---|---|---|---|
| hoist off, `large_tokamak_nof` | 149 | 596 | 7 748 | **0** | 4 / 4 caught |
| hoist off, `low_aspect_ratio_DEMO` | 297 | 1 188 | 15 444 | **0** | 4 / 4 caught |
| hoist off, `st_regression` | 144 | 576 | 7 488 | **0** | 4 / 4 caught |
| hoist off, `large_tokamak_eval` | 10 | 40 | 520 | **0** | 4 / 4 caught |
| hoist on, `large_tokamak_nof` | 149 | 596 | 8 344 | **0** | 4 / 4 caught |
| hoist on, `low_aspect_ratio_DEMO` | 297 | 1 188 | 16 632 | **0** | 4 / 4 caught |
| hoist on, `st_regression` | 144 | 576 | 8 064 | **0** | 4 / 4 caught |
| hoist on, `large_tokamak_eval` | 10 | 40 | 560 | **0** | 4 / 4 caught |
| **total** | **600 × 2 settings** | **4 800** | **64 800** | **0** | **32 / 32** |

What is compared, per design point and per arm: pass counts, model-evaluation counts, module
sweeps, the converged flag, which cap was hit, the inner-solve counts per block, **the full
residual trace at every pass**, the named moved constants, the DSM cross-check sweep, and every
field of the exit audit — floats compared as exact `repr`, which round-trips, so two floats are
equal here if and only if they are the same double. The five fields A26 added are excluded **by
name** and the exclusion list is printed in every gate record, rather than being an implicit
"ignore unknown keys" that would also ignore a key that vanished.

**The sensitivity check is not decoration and it found the one real regression in this task.**
Four perturbations are applied to a copy of the fresh artifact — a model-evaluation count +1, a
residual-trace maximum +1 ULP, an exit-audit objective +1 ULP, and a converged flag flipped —
and each must be caught. All 32 were. Separately, the gate itself failed on its first hoist-on
run, on **600 of 600** design points: the rebuilt `build_blocks` was emitting an empty `FF`
block where A18 dropped the block entirely once the hoist had taken all of its nodes. No count
moved — the only differing key anywhere was `inner`, and every `total` was identical — but the
recorded artifact's *shape* had changed, and a shape change that nobody notices is how two
generations of a table stop being comparable. Fixed by dropping a block whose nodes the hoist
took, while still keeping a block that is empty because the deck never writes it
(`st_regression`'s `PULSE`), which is a different thing and must stay visible.

### 2.1 The licence for reusing A18's harvest no longer held, and this replaces it

§6.3 of the results report licensed reusing one task's recording in another's replay on two
grounds: the sub-trees that determine model behaviour are hash-identical to the recording
commit, and the driver is entered zero times during a replay. **The first half is no longer
true.** Against the recording commit `ad4e4536`:

| path | at `ad4e4536` | at this branch point | |
|---|---|---|---|
| `process/main.py` | `4f2c7ccf` | `4f2c7ccf` | same |
| `process/models` | `2a0d3149` | `3796b1c8` | **differs** |
| `process/data_structure` | `90f8bb7b` | `1bd7ff46` | **differs** |
| `process/core/solver` | `e5a6cfd2` | `ee1366ae` | **differs** |

`process/models/pulse.py` and `process/data_structure/numerics.py` changed when A25 built the
burn-time lift. Both changes are env-switched and inert by default, and A25 gated them — but the
hash argument as §6.3 words it is simply false at the current tip, and a document that keeps
citing it is citing something that has stopped holding.

**The replacement is the reproduction above**, and it is a stronger claim than the hash was:
instead of arguing that the code cannot have changed behaviour, it measures that it did not, over
every design point of every deck, on every recorded quantity. §6.3 should be amended to say so
when the results report is next updated.

---

## 3. Fix 1 — cost at matched **achieved** accuracy, and what it does to Phase A's headline

### 3.1 The objection, restated

The blocked arrangement solved each block to τ = 1e-6 against inputs that were about to change. The
flat arrangement has no inner loop and never paid that. The exit audit shows the blocked arm ending
roughly **10⁵ times more converged** at the same nominal setting: it did more work *and* got more
accuracy, and only the work was in the ratio. The results report said so, and worded its finding as
**"the partition costs *at most* 47 %, 40 % and 18 % more"**.

**This replaces "at most" with a measurement.** Both arms were run across ladders — the flat arm
across τ ∈ {1e-2 … 1e-8}, the block arm across the same joint ladder *and* across an inner-only
ladder at the calibrated outer tolerance, which is the parameter §6.1 says was never varied — and
each run's **achieved exit residual** was recorded alongside its cost. Cost is then read off at
equal achieved accuracy.

- **Accuracy** = the exit audit's global scaled coupling-state residual, taken one further full
  sweep of the complete model set past termination, identical for every arm at every setting.
  Summarised per deck as the **p90** over the design points a rung converged. Not the objective:
  under the lift, two of the three decks have an objective that is a design variable (§9), so
  objective movement is degenerate there.
- **Cost** = net model evaluations (§4's definition), which is a count.
- **Interpolation**: linear in log₁₀(cost) against log₁₀(accuracy), between the two bracketing
  points of each arm's **lower envelope** `cost(a) = min{cost_i : accuracy_i ≤ a}`. A target
  outside an arm's measured range is **not** extrapolated; it is reported as out of range, with the
  range.
- **Population**: every rung of both arms ran the same design points on each deck — 149, 297, 144 —
  and **no rung dropped a point on any deck**, so no ratio is over a censored population.

### 3.2 The result, per deck

At the accuracy the flat control actually delivers at the study's own calibration point (τ = 1e-6):

| deck | n | flat A0 cost | block A1 cost at the same achieved accuracy | A1 / A0 | **published, at matched tolerance** |
|---|---|---|---|---|---|
| `large_tokamak_nof` | 149 | 9 471 | **9 062** | **0.957** | +46.8 % |
| `low_aspect_ratio_DEMO` | 297 | 19 992 | **19 087** | **0.955** | +40.4 % |
| `st_regression` | 144 | 10 395 | **9 037** | **0.869** | −4.6 % |

Across every accuracy the flat arm reached that also lies inside the block arm's measured range:

| deck | A1 / A0 over the matched range | matched points |
|---|---|---|
| `large_tokamak_nof` | 0.957, 0.968, 0.837, 0.858, *1.150* | 5 of 5 flat rungs |
| `low_aspect_ratio_DEMO` | 0.955, 0.949, 0.793, 0.902, *1.094* | 5 of 6 (τ = 1e-8 is tighter than any block rung reached — reported, not extrapolated) |
| `st_regression` | 0.844, 0.869, 0.871, 0.923, 0.960, *1.119* | 6 of 6 |

*The italicised last entry on each deck is the loosest flat rung, where the block arm has no rung
as loose and the envelope is read flat. That is a limit of the ladder, not a win for either arm,
and it is labelled as such in the artifact.*

### 3.3 The verdict on the headline, and the caveats that bound it

**The partition does not cost 47 % and 40 % more. At matched achieved accuracy it is at parity or
cheaper on all three decks** — 4.3 %, 4.5 % and 13.1 % cheaper at each deck's own calibration
point. **The published +46.8 % and +40.4 % were the handicap, essentially in full.** §6.1's
counter-argument — "the outer pass counts fall by much less than the inner solves cost, so an
inexact inner tolerance would have to recover a very large factor" — is refuted by measurement: it
recovers all of it, because the inner solves at τ = 1e-6 were doing work the outer test did not
need.

Four things bound that, and none of them is a hedge that the framing contradicts:

1. **It is statistic-dependent, and the worst-case statistic straddles parity.** Rebuilding the
   same curves on the **maximum** exit residual instead of p90 gives A1/A0 ranging 0.907–1.150,
   0.816–1.228 and 0.824–1.119. So on the single worst design point the two arms are not
   distinguishable. On the **median** the comparison cannot be made at all: the median exit
   residual is exactly zero on 15 of 17 rungs on `large_tokamak_nof` and 13 of 17 on
   `low_aspect_ratio_DEMO` — the state is a bit-exact fixed point on most points — leaving one or
   two usable rungs. **The correct summary is "at parity or cheaper on the p90; indistinguishable
   on the worst point".**
2. **The mechanism is that the over-solving was the cost — not that the block structure wins.**
   The block arm's cheapest setting reaching the target accuracy on the two large decks is inner
   τ = 0.1, where **1 172 of 1 248 inner solves take a single sweep** (71 take two, 5 take three).
   At that setting the arm is barely a block solver: it is close to a flat sweep in block order
   with an outer state test. What the measurement establishes is that the partition **does not
   cost more** once it is not made to over-solve; it does not establish that partitioning is
   itself worth anything.
3. **The block arm had more settings tried** — eleven rungs against six, because the inner
   tolerance is a parameter the flat arm does not have. Best-of-eleven against best-of-six is a
   systematic advantage. It is bounded rather than eliminated: the flat arm's rungs are all on its
   own envelope on all three decks (none dominated), so its curve is already monotone and an extra
   flat rung between two existing ones could only land on the interpolation the comparison already
   assumes.
4. **This is Phase A**, with the optimiser absent, at fixed recorded design points. It says what
   the arrangement costs on the same problems; it says nothing about what an optimiser reacting to
   the arrangement would do. That is Phase B, and it is still not built.

**A reversal found by our own check is a good outcome, and this is one.** The published number was
formally hedged ("at most") and the hedge was correct. What was missing is that nobody had measured
where inside the bound the answer lay, and the answer turns out to be at the far end: the bound was
doing all the work.

## 4. Fix 2 — one accounting, and the two instruments made to agree

§6.2 recorded the study quoting two hoist figures that are not the same measurement:
**6.56 / 6.76 / 6.64 / 2.63 %** from PROCESS's own driver and **−6.38 / −6.55 / −13.70 / −5.71 %**
from the replay engine. Three reasons, and they had different statuses.

**The canonical figure is the driver's, and that is now settled rather than argued each time.**
It is what a user of PROCESS actually gets, it is over a whole optimisation, and it is gated on
bit-identity of the entire output file. The replay engine's figure is a **stated cross-check** and
never a co-headline. The definition lives in one place —
[`arch_surgery/fixedpoint/accounting.py`](../../fixedpoint/accounting.py) — and every A26-or-later
analysis calls it rather than summing fields itself:

> **net model evaluations = in-loop model calls + pre-predicate tail calls + post-predicate tail
> calls.** The exit audit's extra sweep is **never** charged to an arm: it is an instrument,
> identical across arms at a given setting, and charging it would count the measurement as part of
> what is measured.

| reason they differed | status |
|---|---|
| **Different populations** — a whole optimisation versus the recorded design points | **unchanged, and not a defect.** Two populations by design; that is what makes it a cross-check. It must be stated at every quotation, and `accounting_record` now emits the population with the number |
| **Different model sets on one deck** (I-13) — the engine had no guard and hoisted `costs` where the driver could not | **removed.** The routing rule (fix 4) is derived from the driver's own read set, so both instruments resolve the same node set on every deck |
| **Different accounting** — the engine's headline counted in-loop models only and reported the tail separately, giving −9.52 % where the comparable figure is −6.38 % | **fixed in one place.** `net_model_evaluations()` adds the tails back; `accounting_record()` still reports the three components separately so a reader can see −9.52 % and −6.38 % are one measurement under two accountings |

**One thing the settlement adds that §6.2 did not ask for.** Model evaluations are commensurable
between *any* two arms — a model call is a model call whatever loop it sits in, which is why the
unit was chosen over sweeps. What is **not** commensurable is what the arms converge, and a cost
ratio between arms that stop on different tests carries that difference inside it. `accounting.py`
now states this per arm pair, which matters immediately because Phase B runs three arms
(decision D18): `R → A0′` is the predicate's cost, `A0′ → A1′` is the architecture, `R → A1′` is
both and is legitimate only as the user-facing figure.

---

## 5. Fix 3 — a scale floor, and nothing excluded for never having varied

§6.3(ii): quantities that never vary across the harvest were **excluded** from the stopping test.
The run-time assertion that a constant stays constant is a real guard, but it guards against a
*move*, not a test the arm has to satisfy — and it says nothing about a component that moves by
less than everything, or about the 555 of 840 components `large_tokamak_eval` classified constant
from ten design points.

**The user's ruling was scale floor, no exclusion, and that is what is implemented.**
[`ystate.py`](../../fixedpoint/ystate.py) gains a second categorisation mode, `SPEC_MODE_A26`,
alongside A18's, which is kept verbatim so three merged tasks' artifacts keep reproducing:

- every **float-valued** component is tested, whether or not it varied, at `s_i = median |y_i|`
  over its nonzero harvested points;
- a component with **no observed magnitude** — identically zero at every harvested point, so no
  relative scale can be measured — gets the explicit, recorded **scale floor**;
- every **non-float** component is tested by exact equality, which a constant satisfies trivially
  and a mover fails loudly;
- a component that is **non-finite somewhere in the harvest** is *tested*, not dropped: its
  non-finite pattern must be unchanged and its finite entries must satisfy the scaled test;
- the only exclusions are the quantities named in `ACCUMULATORS`, each with a per-quantity
  justification, and **the only admissible justification is that the quantity accumulates within a
  sweep and therefore has no fixed point.** "It never varied" is explicitly not one.

### 5.1 The floor: what it is, why, and what a decade does

**`SCALE_FLOOR = 1.0`**, which makes the test on a magnitude-less component absolute
(`max|Δy_i| < τ` in the component's own units) rather than relative. Three reasons, stated as a
judgement because that is what it is:

1. It is the value A18 already used for the one case it met — a float that varies but is
   identically zero at every harvested point — so adopting it keeps one convention rather than
   inventing a second.
2. It is the only choice that does not require asserting a working magnitude for a quantity whose
   magnitude was never observed.
3. A floor far below 1 makes a quantity that ought to be inert unconvergeable, which manufactures
   invalid design points instead of measuring them.

**Reversal path.** The floor is a single module constant, it is recorded in every artifact and in
every result file, and `run_a26.py spec` runs the whole comparison at 0.1, 1.0 and 10.0. Changing
it is a one-line edit plus a re-run; §5.3 reports what the decade does.

### 5.2 The search for an accumulator, and why the exclusion list is empty

The one admissible exclusion is a quantity that accumulates within a sweep and therefore has no
fixed point. That has to be **looked for**, not assumed absent, so the frozen models were searched
by AST — 171 files under `process/`, against the 881 coupling components the three decks' committed
records name between them — for two patterns:

| pattern | hits |
|---|---|
| augmented assignment to a coupling component (`self.data.ns.field += ...`) | **38** |
| self-referential assignment (`self.data.ns.field = f(self.data.ns.field, ...)`) | **93** |

AST rather than a regex, so trap T2 (`= ` matching `==`) cannot bite: the parser is asked for the
expression context, and a name that only appears on the left of an assignment is a store.

**None of them is an accumulator in the sense that matters, and the reason is the same for all of
them**: every hit is a *within-`run()`* accumulation whose target is initialised before the
accumulation begins — `costs.c22221 = 0` then four `+=` terms, `physics.p_plasma_separatrix_mw`
built up from its components, and so on. A quantity like that is a pure function of the sweep's
inputs and has a perfectly good fixed point. An accumulator in the sense that would justify an
exclusion would have to carry a value **across** sweeps, and none does.

The search is the search; the run is the verdict. `ACCUMULATORS` is therefore **empty**, and that
is a measured result rather than an oversight. §5.3 is the check that matters: if one of them
genuinely could not converge, it shows up there as invalid design points, named.

### 5.3 What testing everything actually did: nothing, on all three decks, at all three floors

Every arm re-run at τ = 1e-6 under `SPEC_MODE_A26`, at floors 0.1, 1.0 and 10.0:

| deck | components tested | previously excluded, now tested | at the floor | design points invalidated | model evaluations vs A18 |
|---|---|---|---|---|---|
| `large_tokamak_nof` | **840 / 840** | 140 constant + 1 non-finite | 40 | **0 of 149**, every arm, every floor | **identical, every arm, every floor** |
| `low_aspect_ratio_DEMO` | **846 / 846** | 143 constant | 41 | **0 of 297** | **identical** |
| `st_regression` | **827 / 827** | 243 constant | 54 | **0 of 144** | **identical** |

"Identical" means exactly that: R / A0 / A0f / A1 total 9 471 / 9 471 / 9 618 / 13 906 on
`large_tokamak_nof`, 21 021 / 19 992 / 20 307 / 28 070 on `low_aspect_ratio_DEMO` and
9 744 / 10 395 / 10 584 / 9 917 on `st_regression` — the same numbers A18 recorded, to the last
digit, with 526 previously untested components now in the predicate.

**Three things follow, and the third is the one that matters.**

1. **The exclusion was harmless on these decks.** Every quantity A18 dropped for never having
   varied was genuinely inert: including it changes no count and invalidates no design point. A18's
   numbers are retrospectively confirmed under a strictly stronger test.
2. **The scale floor does not bind.** A decade in each direction — 0.1 and 10.0 — gives *identical*
   counts on every deck and every arm. The 40 / 41 / 54 components with no measurable magnitude
   never come within a decade of the tolerance, so the judgement in §5.1 has, on this evidence, no
   consequence at all. That is the strongest possible answer to "what changes if it moves a decade":
   nothing does, and the choice is therefore safe rather than merely defended.
3. **The hazard is closed for the future, at zero cost.** §6.3(ii)'s objection was never that the
   exclusion *had* misled — it was that if an excluded quantity genuinely coupled, every
   arrangement would inherit the same false convergence with no symptom. That is now structurally
   impossible: there is nothing to exclude. The fix costs nothing measured and removes a class of
   silent failure.

**And the limit, stated.** This is evidence about **these three decks**. `large_tokamak_eval` — the
deck where the guard was weakest, with 555 of 840 components classified constant from a ten-point
harvest — is dropped from the study (§9), and its behaviour under the A26 predicate is reported
separately in §5.4 as a historical check rather than as part of the result.

The user's expectation was that testing everything would make some design points invalid, and said
that would itself be a reportable result. **It did not**, on any deck, at any floor, for any arm —
0 of 590 design points — and that is the reportable result instead.

### 5.4 On the dropped deck it was **not** harmless — and a published claim is wrong

`large_tokamak_eval` was run under the A26 predicate too, as a historical check, because it is the
deck where §6.3(ii) said the guard was weakest. It is the only deck where the exclusion mattered,
and it mattered in the **opposite direction** to the one anyone was worried about:

| arm | A18, exclusions on | A26, everything tested | change |
|---|---|---|---|
| R | 462 | 462 | — (R does not use this predicate) |
| A0 | 525 | **378** | **−28.0 %** |
| A0f | 588 | **504** | **−14.3 %** |
| A1 | 618 | **457** | **−26.1 %** |

All 10 points converge either way, at every floor. **Excluding quantities made convergence
harder, not easier**, and the mechanism is exact: an excluded constant is guarded by an
**assertion that it is bit-identical**, which is far stricter than the scaled tolerance the same
quantity gets when it is included. Two quantities on that deck are not in fact constant, so the
assertion fired, blocked convergence, and bought extra sweeps. Per point, from the recorded
residual traces: call index 4 goes 3 sweeps → 1, index 5 goes 3 → 1, index 10 goes 3 → 1, index 9
goes 3 → 2, with `n_constant_moved = 2` on exactly the passes A18 spent and `0` under A26.

**The published claim this contradicts.** §6.3 of the results report states:

> *"across all 600 design points, all four arrangements and both hoist settings exactly **one**
> constant moved — `ccfe_hcpb.x_shield`, on 3 of `st_regression`'s 144 points — and it blocked
> convergence at those passes rather than passing silently."*

Read directly out of A18's own recorded artifacts, at both hoist settings:

| deck | constants that moved | occurrences | design points affected, per arm |
|---|---|---|---|
| `large_tokamak_nof` | none | 0 | 0 of 149 |
| `low_aspect_ratio_DEMO` | none | 0 | 0 of 297 |
| `st_regression` | `ccfe_hcpb.x_shield` | 3 | 1 of 144 |
| **`large_tokamak_eval`** | **`physics.vs_plasma_burn_required`, `physics.vs_plasma_total_required`** | **21 each** | **7 of 10** |

**Three constants moved, not one, and the two that were missed are on 7 of 10 points of a deck, in
every arm, at both hoist settings.** The sentence is wrong as written, and the error has a
consequence: `large_tokamak_eval`'s §4.4 percentages — including the **+27.3 %** and **−10.7 %**
that §6.5.3 itself called "two of the report's largest percentages" — were computed against arms
whose convergence was being blocked by a bit-identity assertion on two quantities that are simply
not constant there.

**What it does and does not change.**

- **It does not touch the three retained decks.** Zero movers on both large tokamaks; one mover on
  one point of `st_regression`, whose counts are identical under both predicates (§5.3).
- **It is an independent second reason to drop `large_tokamak_eval`** (§9), which was already
  decided on other grounds. The deck's numbers were weaker than the report knew.
- **It is the strongest argument for fix 3 that the task found**, and it was not the argument fix 3
  was commissioned on. §6.3(ii) feared an excluded quantity that genuinely couples would produce a
  *false convergence*. The measured failure is the mirror image: a quantity that is not really
  constant produces a *false non-convergence*, and inflates a cost figure. Both are removed by
  having nothing to exclude.
- **The results report needs a correction.** I have not made it (§13): it is a standing document
  and the orchestrator's assessment gates changes to it. The correction is to §6.3's second bullet
  and to §4.1's guard row, and it should carry this table.

---

## 6. Fix 4 — the manifest guard, and the routing rule that replaces two guards

### 6.1 A comparison that cannot say what it varies does not run

§6.3(iii): grouping the models by block also transposed `build` and `physics`, so the
flat-to-blocked comparison varied two things. Nobody named it while the comparison was designed,
built, measured or written up; an unrelated task's diff caught it. **The null came out clean and
that is not the lesson.** The lesson is that no check in the design was *capable* of noticing,
because nothing in the design ever wrote down what the comparison was supposed to be varying.

[`arch_surgery/fixedpoint/manifest.py`](../../fixedpoint/manifest.py) makes that a run-time
requirement. Every arm-versus-arm comparison carries a **manifest** — a declaration, from a closed
vocabulary, of exactly what differs between the two arms, plus a rationale. At run time the arms
are reduced to a flat descriptor of everything a comparison could be varying (node sequence, block
schedule and its shape, predicate, floor, outer and inner tolerance, hoist and lift settings, both
tail groups, loop node set, coupling-state spec mode, scale floor, spec hash, all three caps) and
the two descriptors are diffed.

Three things it refuses, and the third is the one that matters:

- a difference the manifest does not declare;
- a declared dimension that does not actually differ — an over-declared manifest launders the
  original confound by making "grouping and order" cover a comparison meant to vary only grouping;
- **an arm pair with no manifest at all.** Every ordered pair of arms actually run must be
  declared. That is what stops a third arm being added and quietly compared against the other two
  with no declaration — §6.3(iii)'s confound, one level up. It matters now: Phase B runs three arms
  (D18), and `R → A0′`, `A0′ → A1′` and `R → A1′` mean three different things.

The vocabulary is closed on purpose: a free-text "varies" field would let a comparison declare
"stuff" and pass. Adding a genuinely new dimension means adding it to `DIMENSIONS` with the
descriptor keys it licenses — never widening an existing one.

**What it cannot catch, stated as a limit.** It compares the *configuration* two arms were built
from. It cannot catch two identically configured arms running against different data, or a defect
inside a solver both arms share. Those are what the replay-fidelity, restore-exactness and
determinism gates are for. This is a guard against **undeclared** variation, not against all
variation.

**Shown capable of refusing.** The `A0 → A1` manifest declaring only `block_grouping` is refused
because `inner_tau` also differs — the block arm has an inner solve and the flat arm has none. The
declaration that passes names both, with the reason.

### 6.2 The hoist becomes a routing rule keyed on measured read sets

Two guards existed and neither was right.

- **A18's engine had none.** Every node the static node map labelled `FF` left the loop, whatever
  the deck.
- **A13's driver had a figure-of-merit guard**, which kept `costs` *in the loop* on decks whose
  figure of merit reads it. Correct, but more conservative than necessary, and it cost
  `large_tokamak_eval` its hoist saving (2.63 % against ~5.25 %).

The disagreement between them is **I-13**. Plan §4.1d/§4.1e replace both with three slots, and the
membership test is the **predicate layer** — the objective *or* the constraint layer, not the
constraint layer alone, because `objectives.py` reads model-written state too:

| slot | membership | runs |
|---|---|---|
| in the loop | the node feeds an in-loop model | every sweep |
| **pre-predicate** | it does not, **but** the predicate layer reads something it writes | once, on the converged state, **before** `objf`/`conf` |
| **post-predicate** | neither | once, **after** `conf` |

A node in the pre-predicate slot still leaves the sweep — that is the whole saving — but the
predicate never sees a stale value. **This generalises A13's guard and beats it**: the node runs
once instead of every sweep, so the deck keeps the saving without the staleness.

**Both inputs are measured, not listed.** The predicate's read set comes from an AST walk over
`objectives.py` and `constraints.py` for `data.<namespace>.<field>` in a *load* context — the
parser is asked for the expression context, so trap T2 (`= ` matching `==`) cannot bite, and a
field that only ever appears on the left of an assignment is a store and is not collected. It is
**exact on the objective side** (the active figure of merit's own branch of the `if`/`elif` chain)
and a **superset on the constraint side** (every registered constraint, not only the deck's `icc`).
The asymmetry is deliberate: over-reporting routes a node to the pre-predicate slot, which is never
wrong, only occasionally unnecessary; under-reporting hands the optimiser a stale `conf`. Node
write sets come from the run-time write census, committed as
[`node_writesets.json`](../data/node_writesets.json) — the same status as the DSM node map the
driver already reads, and for the same reason (trap T9).

**The objective read set the probe recovers is exactly the seventeen fields the plan names**, which
is an independent agreement rather than a restatement: the probe was written from the AST, the
plan's count from reading the file.

Measured routing, per deck, at the deck's own figure of merit:

| deck | figure of merit | `pulse` | `costs` | `water_use` |
|---|---|---|---|---|
| `large_tokamak_nof` | 1 `MAJOR_RADIUS` | **pre** (`constraints.t_current_ramp_up_min`, `times.t_plant_pulse_burn`) | post | post |
| `low_aspect_ratio_DEMO` | −14 `PULSE_LENGTH` | **pre** (same two) | post | post |
| `st_regression` | −5 `FUSION_GAIN_Q` | post (writes nothing: `i_pulsed_plant = 0`) | post | post |
| `large_tokamak_eval` *(dropped)* | 7 `CAPITAL_COST` | **pre** | **pre** (`costs.cdirt`, `costs.concost`) | post |

**On the three remaining decks the hoisted set is byte-identical to A13's**, so the routing rule
changes nothing there and the hoist-on reproduction gate passes at 0 of 2 400 arm records. The
deck where it changes something is the one that was dropped — which is exactly what the coordinator
predicted: **I-13 stops binding because a deck was dropped, not because the rule fixed it.** The
underlying asymmetry is still there for any future deck with a cost-based objective, and the rule
is what handles it when one appears.

**One thing checked and reported because it looked like a second instance of I-13.** The node map
labels `objective_constraints` as `FF`, and on `low_aspect_ratio_DEMO` it writes
`cs_fatigue.n_cycle_min`, which a constraint reads — which would have put a predicate-feeding node
in the post-predicate slot. It does not arise: `objective_constraints` is **not in the executed
node order** on any deck (21 nodes per sweep, and it is not one of them), so neither instrument has
ever hoisted it. Recorded here so the next person who notices the label does not have to re-derive
it.

---

## 7. Item 8 — `pulse` leaves the MDA under the lift (plan §4.1d)

Added to this task's scope mid-flight, by the coordinator, from a user ruling. Once the burn time
is a design variable, `pulse` should run **once per optimiser evaluation, not once per sweep**: its
burn-time write becomes a no-op (`subsolve` returns the design variable untouched), and the only
other field it writes on the pulsed decks, `constraints.t_current_ramp_up_min`, is read by a
constraint equation and by **no model**. It is the VP2 × VP5 composition the framework predicted
and flagged as a latent defect firing only when two arms compose; it never fired because the hoist
keyed on the static label and `pulse` is labelled `PULSE`.

**It is not feed-forward in the sense `water_use` is** — its output *is* consumed, by the predicate
layer — so it goes in the pre-predicate slot and never the post-predicate one. Putting it after
`conf` would hand the optimiser a constraint vector built from a stale value.

**Implementation.** `PROCESS_ARCH_HOIST=feedforward_lifted` is its **own arm name**, not an
automatic consequence of turning the lift on. Two reasons, and the first is the whole point of
fix 4: `feedforward` and `feedforward_lifted` at the same lift setting differ in exactly one thing,
which makes the gate a one-variable comparison. And an arm whose meaning changes silently with an
unrelated environment variable is the failure mode `caller.py` already refuses elsewhere — so
`feedforward_lifted` without `PROCESS_ARCH_LIFT=burn_time` is an import-time error, not a quiet
degradation to `feedforward`.

In `call_models`, when the loop converges: the pre-predicate group runs, **then `objf` and `conf`
are re-evaluated** on the state it produced, then the post-predicate group runs, then the call
returns. The re-evaluation is not an extra sweep — it is one call to `objective_function` and one
to `constraint_eqns` on a state that has just converged.

### 7.1 The gate plan §4.1d specifies is vacuous on this study's decks

**This is the finding, and it would have gone unnoticed.** §4.1d asks that the *constraint vector*
be bit-identical between the two arms. `constraints.t_current_ramp_up_min` is read by exactly one
constraint equation — **41**, the plasma-current ramp-up time lower limit — and

| deck | `icc = 41` active? |
|---|---|
| `large_tokamak_nof` | no |
| `low_aspect_ratio_DEMO` | no |
| `st_regression` | no |
| `large_tokamak_eval` | no |

**None of the four decks activates it.** So the constraint vector cannot move no matter where
`pulse` runs, and a comparison of `conf` alone would report a zero that means nothing — precisely
the failure mode protocol §12 exists for, and precisely the shape of trap T11 (a number published
without the condition that limits it). A gate whose watched quantity is never exercised is an
assertion.

So the gate compares three things, each with its denominator, and says which is which:

1. **`constraints.t_current_ramp_up_min` itself**, as an exact hex float at every `call_models`
   return. This is the non-vacuous version: the value the constraint *would* read.
2. **The constraint vector**, every entry as an exact hex float, at every call — reported **with
   the note that constraint 41 is inactive**, so its zero is read correctly.
3. **The whole output file**, line by line and float by float as hex.

plus a sensitivity check that perturbs each recorded quantity by **1 ULP** and confirms the
comparison catches it. A stale-by-one-sweep value on a converged state differs at tolerance level;
a comparator that rounded would pass it silently.

### 7.2 The gate, run

Two arms per pulsed deck, differing in exactly one setting — `PROCESS_ARCH_HOIST=feedforward`
against `feedforward_lifted`, with `PROCESS_ARCH_LIFT=burn_time` and A25's derived `ixc = 178` /
`icc = 93` deck on **both**. Full optimisations, fresh subprocess each, serial, exact tree asserted,
first run discarded.

| | `large_tokamak_nof` | `low_aspect_ratio_DEMO` |
|---|---|---|
| `call_models` invocations compared | **660** | **1 050** |
| `constraints.t_current_ramp_up_min` differing, as exact hex floats | **0 of 660** | **0 of 1 050** |
| constraint-vector entries differing, as exact hex floats | **0 of 17 820** | **0 of 27 300** |
| objective differing | **0 of 660** | **0 of 1 050** |
| MFILE lines differing | **0 of 16 201** | **0 of 16 462** |
| MFILE floats differing, as hex | **0 of 11 186** | **0 of 11 117** |
| sensitivity: 1-ULP perturbations caught | **4 / 4** | **4 / 4** |
| pre-predicate tail resolved | `pulse` | `pulse` |
| post-predicate tail resolved | `water_use`, `costs` | `water_use`, `costs` |
| **status** | **PASS** | **PASS** |

**The non-vacuous line is the first one.** `constraints.t_current_ramp_up_min` is bit-identical at
every `call_models` return, on 1 710 calls across the two decks — so running `pulse` once on the
converged state produces exactly the value running it on every sweep produced. That is what makes
the placement correct rather than merely harmless-looking, and it is not something the constraint
vector could have told us here, because **`icc = 41` is inactive on every deck** and `conf` could
not have moved whatever `pulse` did. The zeros in rows 2 and 3 are reported *with* that sentence,
never instead of it.

**The MFILE zeros are the user-facing statement**: the whole answer is unchanged, byte for byte,
with `pulse` out of the loop.

---

## 8. Fix 5 — timings, with an interval, and taken in the right order

The user asked for a simple timing of the arms with an uncertainty band on every number.
**I-10 is OPEN and says why the band is the point**: identical work has varied by up to 35 % in
CPU-seconds on this machine, the cause is *not known* (it is not scheduling contention — CPU time
tracks wall clock to two decimals, and descheduling would widen wall while leaving CPU flat), and
a wall-clock-derived cost weight has already moved 6.4 % → 4.4 % across runs of identical code,
after reaching the arithmetic behind a gate decision.

So every timing here is a **median with a stated interval over a stated number of repetitions**,
and carries the machine's load average, its peak resident memory, and the run's **position in the
sequence** — which is I-10's own recorded confound, the one that made three descending samples
look like a settling trend when only two of them were content-identical. The first run in a fresh
environment is discarded; numba JIT dominates it.

**These are context and never evidence.** The acceptance quantities in this study remain counts
and bit-comparisons. `_timing_rollup` refuses to report a mean, and refuses to compare arms: the
ratio of two of these numbers is exactly the quantity I-10 showed moving. Where the interval is
wide enough to swallow the effect, that is said in the same sentence as the number.

### 8.1 The timings were taken *after* the coupling-state read was fixed, deliberately

`YSpec.read` snapshotted and copied **every** component of the coupling state — 827 to 846 of
them, `ndarray.copy()` and list slices included — and `residual(..., subset=...)` then discarded
most of it, because an inner block solve tests only its own module's subset. The block arm was
copying ~840 components to compare ~50, on every inner sweep.

Reading only what is about to be tested has **zero methodological consequence**: the same
components are compared, the same residual is computed, the same decisions are made. It is the
pure-overhead half of the cost. Counted exactly, over the reproduction gate's own runs:

| deck | inner sweeps | component reads before | after | removed | |
|---|---|---|---|---|---|
| `large_tokamak_nof` | 2 047 | 2 735 040 | 779 593 | 1 955 447 | **71.5 %** |
| `low_aspect_ratio_DEMO` | 4 136 | 5 549 760 | 1 581 407 | 3 968 353 | **71.5 %** |
| `st_regression` | 1 411 | 1 859 096 | 530 397 | 1 328 699 | **71.5 %** |

That is a **count**, not a timing, which is why it is quoted: 71.5 % of the block arm's
coupling-state read traffic was bookkeeping whose result was thrown away. Timing the arms before
removing it would have measured our own harness, which is the misreading A25's §8 warned about.

**Gated as a bit-comparison, not as an approximation.** The subset-aware read is one of the three
changes the §2 reproduction gate covers: every arm reproduces its own residual traces, counts,
converged flags and exit audits exactly, over 600 design points at both hoist settings, 0 of
4 800 arm records differing, with the comparison shown capable of catching a 1-ULP move in a
residual trace 32 times out of 32.

### 8.2 The timings, and the sentence they have to be read with

Five repetitions of every arm on every one of 40 design points per deck — 200 samples per arm per
deck — with the first run in a fresh environment discarded. CPU-seconds per design-point solve:

| deck | arm | median | p10–p90 | **p10–p90 spread, as % of the median** |
|---|---|---|---|---|
| `large_tokamak_nof` | R | 30.10 ms | 22.93–37.92 | **49.8 %** |
| | A0 | 40.66 ms | 29.71–59.74 | **73.9 %** |
| | A0f | 40.34 ms | 29.97–60.41 | **75.5 %** |
| | A1 | 71.05 ms | 42.15–81.57 | **55.5 %** |
| `low_aspect_ratio_DEMO` | R | 31.54 ms | 24.29–44.03 | **62.6 %** |
| | A0 | 41.20 ms | 31.05–56.07 | **60.7 %** |
| | A0f | 42.08 ms | 31.45–55.83 | **57.9 %** |
| | A1 | 70.74 ms | 42.97–80.44 | **53.0 %** |
| `st_regression` | R | 31.38 ms | 23.43–43.18 | **63.0 %** |
| | A0 | 44.65 ms | 36.27–96.06 | **133.9 %** |
| | A0f | 45.92 ms | 36.55–102.25 | **143.1 %** |
| | A1 | 49.12 ms | 43.39–109.36 | **134.3 %** |

Machine state at the time, recorded with the numbers: load average 1.17–1.39 (1-minute), peak
resident memory 460–543 MB, sequence positions 2, 4 and 6 within one serial run, one repetition
discarded per deck as warm-up.

**The uncertainty band is wider than the effect, by an order of magnitude, and that is the finding
about the timings.** The differences this study argues about are 4–5 % in model evaluations. The
p10–p90 spread on a single arm's own CPU time is **50 % to 143 %** of its own median. No ratio of
two of these numbers can resolve a 4 % effect, and none is offered. This is the same phenomenon
I-10 records — identical work varying by up to 35 % in CPU-seconds with the cause unknown — showing
up again at a larger magnitude on a finer-grained workload.

**Two further reasons not to read the medians as an arm comparison**, both of which would make the
numbers wrong even if the spread were tight:

1. **They are at matched *tolerance*, not matched accuracy.** A1 at τ = 1e-6 is the over-converged
   configuration §3 exists to correct. Its median being ~1.7× A0's is a measurement of the
   handicapped arm.
2. **A1 still carries per-block bookkeeping A0 does not** — a residual evaluation per inner sweep,
   and the subset reads of §8.1. A model-evaluation count is blind to that by construction, which
   is why it is the acceptance quantity; a timing is not.

**What the repetitions did establish, and it is a count**: every arm produced **identical** pass
counts, model-evaluation counts, module sweeps, converged flags and cap outcomes across all five
repetitions — **640 of 640 comparisons on each deck, 1 920 in total, 0 mismatches**. That is the
gate the repetitions exist for; the timings are the by-product.

### 8.3 What I did **not** do, on instruction: shrink the tracked set

Only the `argmax` component can drive a convergence decision, and the coordinator measured that
just **22 / 24 / 25** of ~840 components ever do on the three decks. Reducing the tracked set to
those would be a much larger saving than the subset-aware read. **It was deliberately not done**,
and the reasons are worth keeping:

- that set would be derived from the very runs it would then be validated against — the
  circularity that made the DSM's declared coupling set look adequate until V7 measured it
  stopping 0.96–2.44 sweeps early on 94–95 % of points;
- the whole reason this study tracks *measured* state rather than *declared* state is that the
  declared set was insufficient. Replacing it with a differently-derived guess, in the task whose
  job is to make the headline trustworthy, would undo the thing that makes the predicate
  trustworthy.

**Proposed as a separate future change, with the guard specified** (§11.4).

---

## 9. Fix 6 — `large_tokamak_eval` dropped, dated, and not retro-applied

**The user's decision.** It runs 0 solver iterations, so it cannot inform a study about how an
architecture behaves when the optimiser reacts; its inequality constraints are never enforced, so
its "solution" is not a feasible optimum; and A22 found its evidence weaker than the other pulsed
decks — 555 of 840 coupling components classified constant from a **10-point** harvest. It was
carrying two of the results report's largest percentages (+27.3 % and −10.7 %, §4.4.1) on the
least foundation.

**Scope, carefully.** The study's decks from **2026-09-02** are `large_tokamak_nof`,
`low_aspect_ratio_DEMO` and `st_regression`. The drop is recorded with its date and its reasons as
a module constant, `DROPPED_2026_09_02`, in every entry point that carries a deck list —
`run_phase_a.py`, `run_a26.py`, `analyse.py`, `gen_ystate.py` and the repository-root
`MDA_partition_experiment.py` — so nobody reads a three-deck table as a four-deck one with a
missing column. The deck file itself is **not deleted** and `--scenarios` still accepts it, so a
historical re-derivation remains possible.

**Already-merged four-deck reports are not retro-edited.** They are the record of what was run.
This report's §2 gate table deliberately still shows all four decks, because that gate was run on
all four and its denominators are what they are.

**One consequence the drop creates rather than removes**, and it belongs in the calibration
wording rather than in a table: with the eval deck gone, plan §4.1e's observation binds. The three
remaining decks are figure of merit 1 (`MAJOR_RADIUS`, objective `0.2 × rmajor`, already a design
variable), −14 (`PULSE_LENGTH`, which the burn-time lift turns into a design variable) and −5
(`FUSION_GAIN_Q`, on the deck that takes no lift). **So in the Phase B variant, no deck has both a
computed objective and the lift.** §4.3's existing caveat — that `large_tokamak_nof`'s zeros in the
tolerance ladder are structural rather than evidence — now applies to `low_aspect_ratio_DEMO`'s
variant too. This is why fix 1's accuracy measure is the **coupling-state residual** and not
objective movement: an objective-movement measure would be degenerate on two of three decks.

---

## 10. Asked while the task was open: is `A0′` the degenerate case of `module_solve.py`?

The coordinator asked whether Phase B's predicate-matched flat control — `A0′`, flat fixed-point
iteration on the coupling state inside `caller.py` — is `process/core/solver/module_solve.py` with
a single block containing every node, and to report either way because it changes A28's estimate.

**Nearly, and the shortfall is two small named things, not a redesign.** Read from the code, not
run:

1. **The outer pass is redundant with one block, and is still paid.** `_call_models_by_module`
   always evaluates the outer residual after the block loop, and `y_outer_prev` is the state at
   entry to outer pass 1 — so outer pass 1 compares the entry state against the converged state
   and fails, outer pass 2 re-runs the block (converging immediately, one sweep) and then passes.
   That is **one extra full sweep per `call_models`**, which is approximately the wasted-pass
   effect A0f → A0 measured at 1.53–1.79 %. It needs a guard — skip the outer test when a single
   block covers every in-loop node — not a redesign.
2. **`_ARMS`, `BLOCK_ORDER`, `ITERATED` and `module_schedule()` hardcode the three-module
   partition**, so a `flat_state` arm is a new schedule branch. A handful of lines, but it is not
   a configuration of what already exists.

**And the hazard that killed A25's first attempt does not bind here**, which is the part worth
having. A25 found that `ystate`'s predicate scores a component `inf` whenever either snapshot is
not float-viewable, so an M1 inner solve was held open for all twenty sweeps by
`ccfe_hcpb.pnuc_tot_blk_sector` — a field M3 writes and M1 cannot touch. Measured: **the union of
the per-module write sets is the entire component set on all three decks** — 840/840, 846/846,
827/827 — so a single block containing every node writes everything on its first sweep and the
`inf` cannot persist. It may still cost one extra sweep on the very first `call_models` of a fresh
process, where a component is not float-viewable until something writes it; that is worth knowing
and is not a blocker.

So: **A28 should budget for a schedule branch plus a single-block outer-pass guard, and can
inherit the predicate, the spec loading, the subset machinery and the failure policy unchanged.**

---

## 11. What the Phase B re-run must do differently

1. **Quote the matched-accuracy comparison, not the matched-tolerance one.** Both arms run across
   a ladder; the reported cost is read off the **lower envelope** of each arm's cost-versus-achieved-
   accuracy curve at a common achieved accuracy, with the interpolation stated. A single ratio at a
   single tolerance setting is not a comparison and must not be presented as one.
2. **Use `run_a26.py`, not `run_phase_a.py`, for anything new.** `run_phase_a.py` still runs A18
   exactly and its defaults are A18's — that is deliberate, so three merged tasks keep reproducing.
   The new parameters (inner tolerance, coupling-state spec mode, scale floor, predicate-layer
   routing, timing repetitions) are exposed by `run_a26.py`.
3. **Three decks.** `large_tokamak_nof`, `low_aspect_ratio_DEMO`, `st_regression`. Any table that
   also shows `large_tokamak_eval` is a historical re-derivation and must say so.
4. **Declare every arm pair.** Phase B runs three arms, which is six ordered pairs of which three
   are meaningful. `manifest.check_all` **refuses to run** if any pair among the arms actually run
   has no manifest — so A28 must write `R → A0′` (predicate only), `A0′ → A1′` (architecture only)
   and `R → A1′` (both, user-facing figure only), each with its rationale.
5. **Run the reproduction gate first**, and treat it as the licence for reusing A18's harvest. The
   hash-identity argument §6.3 used no longer holds at the current tip; the empirical reproduction
   replaces it, and it has to be re-taken whenever `process/` moves again.
6. **Report the coupling-state residual as the accuracy measure, not objective movement.** Under
   the lift, two of the three decks have an objective that is a design variable (§9), so objective
   movement is degenerate there.
7. **Record net electric power at entry per start and the count of degenerate starts**, alongside
   every cost figure (I-12). D15's perturbed multi-starts will meet the diverging 1990 cost model
   by design.
8. **Take timings after, not before, any harness change**, report them as median plus interval with
   the repetition count, the load average and the sequence position, and never let a conclusion
   rest on one.
9. **Use `PROCESS_ARCH_HOIST=feedforward_lifted` in the Phase B variant**, not `feedforward`. The
   variant's whole claim is that the burn time is lifted; leaving `pulse` iterating inside the MDA
   would make the arm not the architecture being claimed.

### 11.4 One change proposed and deliberately not made: a reduced tracked set, with its guard

Only the `argmax` component can drive a convergence decision, and the coordinator measured that
just **22 / 24 / 25** of ~840 components ever do, on `large_tokamak_nof` / `low_aspect_ratio_DEMO`
/ `st_regression`. Tracking only those would dwarf the 71.5 % the subset-aware read removed.
**Not done here, on instruction and on the merits** (§8.3). If it is ever done, the guarded form
is the only defensible one, and the guard is the whole proposal:

- the **reduced set** is used in the hot path — the inner block sweeps, where the reads are;
- the **full set is still read and tested at every outer-pass boundary and at exit**, so a
  component outside the reduced set that starts mattering is detected within one outer pass rather
  than never;
- a detection is a **recorded failure that grows the set**, not a warning: the design point is
  marked invalid for that arm, the component is named, and the reduced set is regenerated. A miss
  that only prints is a miss;
- the reduced set is **derived from a different population than the one it is validated on** —
  otherwise it inherits exactly the circularity that made the DSM's declared set look adequate
  until V7 measured it stopping 0.96–2.44 sweeps early on 94–95 % of points;
- it is gated the way A26's changes were: bit-for-bit reproduction of every arm's residual traces,
  counts, converged flags and exit audits, with the comparison shown capable of failing.

Expected saving, stated as an expectation and not a result: the inner-loop read traffic falls by
roughly another order of magnitude on top of §8.1's 71.5 %. Expected risk: the guard's full-set
check at every outer boundary is itself a full read, so the saving is bounded by the ratio of
inner sweeps to outer passes — measured at 2 047/403, 4 136/808 and 1 411/279, i.e. **5.08, 5.12
and 5.06**. **A change that removes 90 % of the reads in 80 % of the sweeps is worth about 70 % of the
remaining traffic, not 90 %.** Anyone quoting it should quote that arithmetic with it.

---

## 12. Autonomous decisions, each with its reversal path

| # | Decision | Why | Reversal |
|---|---|---|---|
| AD1 | **Accuracy is the exit audit's global scaled coupling-state residual, summarised as p90** over the design points a rung converged | It is what every arm actually converges, it is identical across arms (one further full sweep of the complete model set), and objective movement is degenerate on two of three decks under the lift (§9). p90 rather than max because one straggler and five hundred movers are different things | `ACCURACY_STAT` is a module constant in `accuracy.py`; the same curves are rebuilt on p50 and max in every run and reported beside the headline, so the dependence is visible rather than assumed away |
| AD2 | **The cost curve is the lower envelope of the rungs**, `cost(a) = min{cost_i : accuracy_i ≤ a}` | Several settings deliver the same achieved accuracy at different costs; "what does this arm cost at accuracy *a*" has one honest answer, the cheapest setting delivering at least *a* | `curve()` keeps every rung, and the ones the envelope drops are recorded under `dominated` with what dominated them. Reading the rungs in tolerance order instead is a two-line change — and gives +21.9 % where the envelope gives −4.3 % on `large_tokamak_nof`, which is why the choice is called out here rather than buried |
| AD3 | **Scale floor 1.0**, applied only where no working magnitude could be measured | §5.1 | One module constant; `run_a26.py spec` runs 0.1 / 1.0 / 10.0 |
| AD4 | **`ACCUMULATORS` is empty**, so nothing is excluded from the A26 predicate | §5.2's search found no quantity that accumulates across sweeps | Adding an entry requires a per-quantity justification in the same dict; the census reports the exclusion set in every artifact |
| AD5 | **A18's spec hash is left byte-identical**; only a non-A18 mode adds a mode/floor preamble | Otherwise this change would silently invalidate three merged tasks' committed `ystate_*.json` records | Two lines in `components_sha256` |
| AD6 | **A block emptied by the hoist is dropped from the schedule; a block empty because the deck never writes it is kept** | The first is not part of the arm's schedule; the second is the `k = 0` case and must stay visible | `build_blocks`, one condition. The reproduction gate is what forced this: keeping both as empty blocks changed the recorded artifact's shape on 600 of 600 points |
| AD7 | **`feedforward_lifted` is its own hoist arm**, and errors at import if the lift is off | Makes the §7 gate a one-variable comparison, and refuses an arm that silently degrades to another | `_HOIST_REQUIRES_LIFT`, one dict entry |
| AD8 | **The constraint-side predicate read set is a superset** (every registered constraint, not the deck's `icc`); the objective side is exact | Over-reporting routes a node to the pre-predicate slot, which is never wrong; under-reporting hands the optimiser a stale `conf` | `predicate_reads.constraint_reads`; narrowing it to `icc` is a filter, but see the note there on why a routing rule that changes with a deck's constraint list is the wrong shape |
| AD9 | **A26's coupling-state records go in new files** (`ystate_a26_<deck>.json`), not over A18's | A18's records must keep validating | `replay.ystate_path` |
| AD10 | **Plan §4.1d/§4.1e were read from the main checkout read-only, not merged into this branch** | They landed after this branch point; merging them mid-task would have moved the tree under a running gate | Nothing to reverse; the next merge picks them up normally |

---

## 13. What I did not do

- **I did not re-run Phase B.** That is a later task, on this instrument.
- **I did not shrink the tracked coupling set** (§8.3, §11.4) — proposed, with its guard, and
  deliberately left for a separate task.
- **I did not retro-edit merged reports.** The four-deck tables in `MDA_partition_exp_results.md`
  and in the archived task reports stand as the record of what was run. §6.2, §6.3(ii),
  §6.3(iii) and §6.5 of that report describe conditions that this task has now changed; **updating
  it is a separate edit and I have not made it**, because it is a standing document and the
  orchestrator's assessment gates changes to it.
- **I did not route PROCESS's own defects to the sibling study** (§6.5.5) — explicitly out of
  scope.
- **I did not measure a per-model cost unit** (§6.5.2 item 2). Everything §5.2 of the results
  report says about the unit problem is still open.
- **I did not merge or push.** The branch is `A26-method-fixes` and stays there.
- **I did not build Phase B's third arm** `A0′` — A28's, per D18. §10 reports what it would take.

---

## 14. Change log

| when | what |
|---|---|
| 2026-09-02 | Task opened at `39d15401`. Read `CLAUDE.md`, `TRAPS.md`, results report §6, `MASTER_TODO` protocol §12/§12a and D6/D15/D16/I-10/I-12/I-13, plan §4.1c. |
| 2026-09-02 | `engine.solve_block` gains `inner_tau`, defaulting to `tau` — A18's behaviour, bit-identical. |
| 2026-09-02 | `ystate.py`: `SPEC_MODE_A26`, `SCALE_FLOOR`, `ACCUMULATORS`, the `NONFINITE` category tested rather than dropped, and the residual restructured into one category-dispatching loop. |
| 2026-09-02 | `manifest.py` written: closed-vocabulary comparison declarations, refusal on undeclared differences, over-declaration and undeclared arm pairs. |
| 2026-09-02 | `predicate_reads.py` written: AST read-set probe over `objectives.py` and `constraints.py`, exact per figure of merit on the objective side. Recovers exactly the seventeen objective-read fields the plan names. |
| 2026-09-02 | `arms.py` rebuilt around `hoist_split` — three slots, routed by the measured predicate read set. `caller.py`'s `_FOM_READS_NODE` table replaced by the same rule, derived rather than listed. |
| 2026-09-02 | `accounting.py` written: one definition of net model evaluations, stated per arm pair. |
| 2026-09-02 | Coordinator added plan §4.1d (`pulse` leaves the MDA under the lift), then corrected it to §4.1e (the split is on the **predicate** layer, not the constraint layer). Both folded in; the routing rule was written to the corrected version. |
| 2026-09-02 | `caller.py`: the deferred tail splits pre/post predicate; `feedforward_lifted` added as its own arm with an import-time error if the lift is off. |
| 2026-09-02 | Coordinator: make `YSpec.read` subset-aware; do **not** shrink the tracked set; take timings after. Done, gated, and the deferred change written up with its guard (§11.4). |
| 2026-09-02 | Coordinator: Phase B runs three arms (D18). `manifest.check_all` generalised to any number of arms and made to refuse an undeclared pair; `accounting.py` states the unit per pair; §10 answers the `A0′` / `module_solve.py` question. |
| 2026-09-02 | Reproduction gate **FAILED** on its first hoist-on run, 600 of 600 points: `build_blocks` emitted an empty `FF` block where A18 dropped it. Counts were identical; the artifact's shape was not. Fixed, re-run, **PASS**. |
| 2026-09-02 | Reproduction gate PASS: 0 differing of 4 800 arm records, 64 800 record keys, 32/32 sensitivity cases caught, both hoist settings, four decks. |
| 2026-09-02 | Matched-accuracy analysis **corrected mid-task**: the first version read the rungs in tolerance order and reported +21.9 % where the lower envelope reports −4.3 %. The envelope is the honest reading and is now what `curve()` computes; the dropped rungs are kept and named. |
| 2026-09-02 | Deck list reduced to three, dated and reasoned in every entry point. `MDA_partition_experiment.py` gains `method_gate`, `accuracy` and `pulse_gate` stages so the root entry point is still the single entry point. |
