# Does the arrangement of solvers change the cost of solving PROCESS?

**An experiment on the fusion systems code PROCESS, with every physics model held fixed.**

> **Document status** — **CURRENT · STANDING DOCUMENT.** This is the results report for the MDA
> partitioning experiment, not a task report: it is **not** archived to `deprecated/` when the task
> that wrote it closes, and it is updated in place as later phases report. **Both phases are now
> complete and written up in full** — Phase A in §§4–6, Phase B in §7 — on the instrument A26
> (method-fixes) corrected. · Base commit `c0ae5b28` · Companion scripts:
> [`MDA_partition_experiment.py`](../../../MDA_partition_experiment.py) (Phase A) and
> [`MDA_partition_opt_experiment.py`](../../../MDA_partition_opt_experiment.py) (Phase B), both at
> the repository root · Written by task A21 (partition-report), 2026-09-01, and rewritten by task
> A28 (phase-b-rerun), 2026-09-02, from the recorded artifacts of tasks A18 (experiment-framework),
> A22 (outer-pass-census), A23 (flat-arm-permutation), A13 (feedforward-hoist), A3 (build-reorder),
> A26 (method-fixes) and A28 itself.
>
> **The correction banner this document used to open with has been resolved and removed.** Its
> content is folded into the body: the matched-accuracy result is §4.4.2 and §4.5(b), the
> moved-constant correction is §4.1 and §6.3, and the harvest-reuse licence is §6.3. A document
> should not open with a list of its own errors; it should not contain them.

---

## Abstract

PROCESS solves a fusion power plant design problem by wrapping an optimiser around a loop that
re-runs about twenty-six engineering and physics models until their outputs stop changing. This
experiment asks whether the **arrangement** of that machinery — how many loops there are, what they
iterate on, which models sit inside them, and which quantities the optimiser owns rather than the
loop — measurably changes the cost of solving, when not one line of any physics model is altered.

The models are frozen deliberately. A faster program with rewritten models proves nothing about
architecture, because the rewrite and the rearrangement cannot be told apart afterwards. Freezing
the models makes the arrangement the only thing that varies, and therefore the only thing a
measured difference can be attributed to.

It runs in two phases. **Phase A removes the optimiser** and replays four arrangements over design
points a real optimisation visited, which makes its numbers exact counts. **Phase B puts the
optimiser back** and runs whole optimisations from perturbed starting points, which is the only way
to ask whether the optimiser reacts to the rearrangement.

**Phase A's answer is that the published penalty was an artifact of the comparison, and that what
replaces it depends on how the comparison is built.** Compared at matched *tolerance*, as this
report originally did, the three-block partition appeared to cost 46.8 % and 40.4 % **more**.
Compared at matched *achieved* accuracy it costs between **4.3 % less and 33.4 % more**, depending
on whether the blocked arm is allowed the extra tuning knob the flat arm does not have — the two
constructions **disagree in sign on two of three test cases, by 32 and 38 percentage points**. Both
are reported. What survives without qualification is that the partition is nowhere near as expensive
as the matched-tolerance figure said, and that it is not shown to be worth anything.

**Phase B takes three arrangements, not two, and that is the methodological result.** PROCESS's
loop and the proposed one stop on different tests, so comparing them directly measures the
architecture and the stopping rule added together — and the stopping-rule term is +2.1 %, −3.4 %
and +3.2 %, comparable in size to the architecture term and not of one sign. With a
predicate-matched control in between, the architecture alone is **1.6 % and 6.2 % cheaper on two
test cases** (on 20 of 22 and 20 of 20 paired starting points) and **inconclusive on the third**.
Its robustness is **identical to the control's on one test case** and worse by a single start of 25
on the other two — and the refusals that an earlier two-arm run attributed to the architecture turn
out to be **two-thirds the stopping rule**, because the flat control refuses them too.

**The result that is not about the partition is the one that reproduces cleanly.** Running the
models that feed nothing back once after the loop instead of on every pass removes 6.6 % of model
evaluations in the flat arrangement with the whole output file bit-identical, and 4.4 %, 4.3 % and
3.0 % inside the proposed one. On one test case the proposed architecture *without* it costs 2.9 %
**more** — so the headline is *the proposed architecture*, never *the partition's benefit*.

Every acceptance quantity is a count or an exact bit-comparison. No conclusion rests on a timing.

## 1. Goal

### 1.1 What the program does now

PROCESS finds a plant design that minimises a cost-like objective subject to engineering and
physics constraints. Two nested pieces of machinery do this:

- An **optimiser** adjusts the design variables — around fourteen to twenty numbers such as major
  radius, magnetic field and plasma current — searching for the best feasible design.
- Inside every one of the optimiser's function evaluations, a **model loop** runs the twenty-six
  models in a fixed hand-written order, over and over, until the results settle.

The second piece exists because the models are mutually dependent: the coil models need plasma
quantities, and some plasma quantities depend on the coils. Running the models once does not give
a self-consistent design, so the loop runs them repeatedly until running them again changes
nothing. That is a **fixed-point iteration**, and it is the standard way to make a set of
mutually dependent models agree with one another.

### 1.2 Why the loop is where the cost is

Two measurements at the frozen base commit set the scale of the question.

**The loop is almost the whole program.** On the reference case `large_tokamak_nof`, one solve
performs 2 027 passes over the model sequence inside the loop at roughly 7.8 milliseconds each —
about 89 % of the program's fifteen-second runtime. Everything else, including the optimiser's own
linear algebra and all file output, is the remaining tenth. *(That 89 % is derived from wall clock
and is therefore context for why the question is worth asking, not evidence for any answer. No
result in §4 rests on it; the counts do not need it.)*

**Almost all of it is spent computing derivatives.** The optimiser needs the slope of the
objective and constraints with respect to each design variable, and it obtains them by finite
differences: nudge one design variable, re-solve everything, and measure what changed. Each such
nudge is a full run of the model loop. Of the 630 loop solves in one run of `large_tokamak_nof`,
**600 are derivative evaluations** — and they account for 94.5 % of all model passes.

Together these say something the project's earlier architecture review stated only half
correctly. That review concluded that *"derivatives are the bottleneck, not the architecture"*.
The measurement shows both halves are entangled: derivatives are the bottleneck **because each
derivative component costs a complete solve of the model loop**. Anything that makes the loop
cheaper is multiplied across essentially the entire run.

### 1.3 The question

Can the loop be made cheaper by rearranging it alone — not by approximating anything, not by
loosening any tolerance, and without touching a single physics model?

---

## 2. Hypothesis

Three claims, in increasing order of how much they assume.

**H1 — The current loop wastes a pass on every solve.** The loop's stopping test compares the
objective and constraint values from two successive passes. Those quantities are computed *from*
the model state, so they do not exist when the loop is entered: the loop must run once purely to
produce something to compare against, then again to compare. The first pass yields no information
about whether anything has converged. A stopping test based on the model state itself has no such
requirement, because the entering state is already available.

**Predicted effect: at most one pass saved per solve.** If every solve saved one, that would be
630 of 2 027 in-loop passes, or 31 % — but that figure is an **upper bound that requires the state
to be already converged on entry every time**, and there is no reason to expect that. The saving is
realised only on solves that would otherwise have stopped at the floor; on a solve needing four
passes, removing the floor saves nothing. **The bound is therefore expected to be far from
attained, and the quantity actually being predicted is the fraction of solves that converge
immediately, which is not known in advance.**

**H2 — The loop is stopping on the wrong quantity, and this is measurable.** The objective and
constraints are *summaries* of the state. State that no constraint depends on sensitively can
still be changing when the loop declares itself finished. Earlier instrumentation found this
happening in **24 % of solves** on the reference case. Because the optimiser computes derivatives
by differencing exactly those summaries, residual movement invisible to the stopping test is
precisely what contaminates the derivatives. **Predicted effect: a stopping test on the state
costs more passes but produces a more consistent answer — a trade, not a saving.** H1 and H2 act
in opposite directions and must be measured separately.

**H3 — The models fall into three groups that can be solved separately.** A dependency analysis
of PROCESS decomposes the model sequence into three blocks with internal circular dependencies —
plasma physics, coils, and plant systems — joined by exactly **one** quantity that closes a cycle
between blocks: the plant's burn time. If each block were solved to consistency on its own, a
block that settles quickly would stop being re-run for the benefit of a block that has not.
**Predicted effect: uncertain, and prior measurement is discouraging** — see §2.1.

### 2.1 Why H3 is doubted in advance

Honesty about a prediction is cheaper before the data than after. Two earlier measurements at
this same base commit argue against H3:

1. The three blocks **stop changing at roughly the same time**, rather than one lagging. A saving
   requires a *small* block to be holding up a *large* one; measured, the large plasma block was
   joint-last in 82–85 % of solves.
2. Under a separated arrangement the bottleneck moves to the **coil block**, which is ten of
   forty-six model nodes but 42 % of the computational cost. It is not small either. *(That 42 %
   is a wall-clock-derived weight, and this project retired such weights for anything a conclusion
   rests on after one moved from 6.4 % to 4.4 % across runs of identical code. It is quoted here as
   the reason the hypothesis was doubted, not as evidence; nothing in §4 uses it.)*

Those measurements were made under the *current* stopping test. Because this experiment changes
that test, they do not transfer directly — which is the reason H3 is worth re-testing rather than
being treated as settled. But they are a reason to expect little, and they are stated here so
that a negative result cannot later be presented as a surprise.

*(§4.4.2 records that H3 lost, and §5.2 records that the mechanism argument above was itself
stated in the wrong unit — the large plasma block is 24 of 52 dependency-graph rows but **2 of the
21 model calls** a deck actually executes. That unit problem cuts both ways and is discussed there
rather than netted away here.)*

---

## 3. Method

### 3.1 Design

The experiment compares four arrangements of the same frozen models, on the same inputs, and
counts the work each performs.

It does this **without the optimiser**. The optimiser is removed and replaced by a fixed list of
design points recorded from a real solve. This is the central design decision and it buys three
things:

- **It removes a confound.** With an optimiser present, a change to the loop changes the
  derivatives, which changes the search path, which changes how many solves happen. The measured
  difference would then mix the loop's cost with the optimiser's reaction to it. With the
  optimiser absent there is no search path to perturb.
- **It makes the measurement exact.** The quantities compared are counts of model passes, not
  timings. Counts reproduce exactly on repeated runs. Timings on the machine used here vary by up
  to 35 % on identical work for reasons that remain unidentified, so no conclusion in this
  experiment rests on one.
- **It requires no change to PROCESS.** The comparison runs entirely in separate analysis code.
  The program under test is untouched apart from a recording hook that is inactive unless
  switched on.

### 3.2 Design points

A **design point** is a pair: a design vector, and the model state that the program had reached
when it evaluated that vector. Both are needed. The state matters because each solve in a real
run starts from wherever the previous one finished, so a solve begun from a cold start is not the
same problem as the one the program actually solved.

Design points are recorded from one ordinary run per test case, saved to disk, and then restored
**identically** for every arrangement. Every arrangement therefore solves exactly the same
problems from exactly the same starting states, and the comparison is paired point by point.

Every design point the optimiser actually visited is kept, plus one in five of the
finite-difference perturbations. This gives 149, 297, 144 and 10 design points on the four test
cases — 600 in all — and every count in §4 is over those populations, never pooled across them.

### 3.3 The four arrangements

| | Name | What it does |
|---|---|---|
| **R** | Reference | The program's current loop, unmodified. Not a competitor — it measures the size of the two effects in H1 and H2 |
| **A0** | Flat | One loop over all models, stopping when the model state stops changing. **The control** |
| **A0f** | Flat, extra pass | A0 with the wasted first pass retained |
| **A1** | Blocked | Three inner loops, one per block, inside an outer loop over the single quantity joining them |

The comparisons are read as follows: **R to A0f** isolates the cost of changing what the loop
stops on; **A0f to A0** isolates the saving from removing the wasted pass; **A0 to A1** isolates
the effect of separating the blocks. Without A0f the first two effects can only be measured
together, and since they act in opposite directions a near-zero total would be indistinguishable
from neither effect existing. §4.4.1 records the test case on which that happened exactly.

A fifth variation — running the models that feed nothing back only once, after the loop, instead
of on every pass — is applied to **all** arrangements, so that it cancels and the comparison
remains purely about loop structure. It is also measured on its own, in PROCESS's own driver
rather than the replay engine, and that is where its headline number comes from (§4.4.3).

### 3.4 When a solve is finished

Each model quantity is compared against its own typical size, measured from the recorded design
points, and the loop stops when the largest relative change falls below a threshold.

Scaling each quantity by its own magnitude is not a detail. The quantities span more than forty
orders of magnitude, and a single shared tolerance therefore means something different for each of
them. The program's existing test has exactly this defect: it uses a comparison whose hidden
absolute floor dominates for any quantity below 10⁻², and §4.6 measures how much of the program's
own convergence test falls into that regime.

Three further rules follow from problems found in the existing test:

- Quantities that never vary are **excluded, and then checked at runtime for still not varying**.
  A quantity dropped from a convergence test without a check is a silent hole; this makes it a
  loud failure instead.
- Whole-number and flag quantities are compared **exactly**, since a relative test is meaningless
  for them.
- A value that has become "not a number" is **never** treated as converged. The program's current
  test does treat it so, which means a calculation that has failed can be reported as having
  succeeded.

The threshold itself is **calibrated rather than chosen**. Before the main comparison, the flat
arrangement is run at three thresholds and the threshold is set where tightening it further stops
changing the answer — beyond that point the extra convergence is real but no longer reaches the
objective. The calibration is run once
and the resulting threshold is shared by all four arrangements, because a comparison in which the
arrangements stop at different standards is not a comparison. §4.3 records the ladder.

Because a shared tolerance setting is not the same thing as a shared final accuracy, every
arrangement additionally runs **one further full pass past termination** and the same global
residual is recorded. Matched accuracy is verified per design point rather than assumed. §4.5
reports what that audit found, including the respect in which the arrangements turned out **not**
to be at equal accuracy.

### 3.5 Limits, and what counts as a failure

Each inner loop is limited to 20 passes, the outer loop to 20, and any single design point to 200
model-block passes in total. **Reaching a limit marks that design point failed, not finished.**
The distribution of passes is recorded so that pressure against a limit is visible; if a
substantial fraction of points reach one, the limit has become a budget and the result is
reported as such rather than adjusted.

A design point enters the comparison only if **every** arrangement solved it. The number of
points dropped, and which arrangement failed on them, is reported **before** any comparison of
counts, because arrangements averaged over different sets of problems cannot be compared — and
because an arrangement that cannot solve a problem the others can is itself a finding.

### 3.6 Running it

One command per phase:

```
python MDA_partition_experiment.py         # Phase A, the optimiser absent
python MDA_partition_opt_experiment.py     # Phase B, the optimiser present
```

Both accept `--quick`, which exercises every stage on one test case in a few minutes so that the
machinery can be confirmed before hours are committed; both print the tree, branch, commit and
dirty marker before anything runs, and an honest runtime and disk estimate; both fail immediately
and name the exact fix when a prerequisite is missing rather than dying in a traceback; and both
accept `--verify`, which runs nothing and compares a finished run's numbers against the ones
published here, per test case, with denominators. **A disagreement there is a finding to surface,
not an error to swallow.** Neither writes anything into the tracked tree.

The two files share one runner (`arch_surgery/experiment_runner.py`): they differ in which phase
they drive, not in how they drive it.

That file is at the repository root and is a **wrapper, not a reimplementation**. Each stage it
runs was written, reviewed and gated as its own piece of work, and the wrapper calls those pieces
rather than restating them, so that running the experiment from one file and running the stages
separately are two paths to the same numbers rather than two implementations of them. The stages,
in the order they must run:

| Stage | What it does | Underlying code |
|---|---|---|
| `phase_a` | records the design points, checks the recording changes nothing, calibrates the tolerance, replays all four arrangements — twice, and once more with the feed-forward models lifted out | `arch_surgery/fixedpoint/run_phase_a.py` |
| `census` | replays the blocked arrangement with the burn time pinned, to identify what forces a second outer pass | `arch_surgery/fixedpoint/run_a22.py` |
| `permutation` | replays the flat arrangement in the blocked arrangement's node order, to check the two differ by the grouping and not by an incidental reordering | `arch_surgery/fixedpoint/run_a23.py` |
| `driver_hoist` | the feed-forward hoist measured in PROCESS's own driver, against a reference checkout | `arch_surgery/idf_probe/run_a13.py` |
| `driver_reorder` | the build/physics reorder, likewise | `arch_surgery/idf_probe/run_a3.py` |
| `method_gate` | re-runs every arrangement at the recording's own settings and compares against the recorded artifacts bit for bit — the licence for reusing the recording at all (§6.3) | `arch_surgery/fixedpoint/run_a26.py` |
| `accuracy` | the tolerance ladders, and cost read off at matched **achieved** accuracy (§4.4.2) | `run_a26.py`, `arch_surgery/fixedpoint/accuracy.py` |
| `pulse_gate` | the burn-time model out of the loop under the lift, in PROCESS's own driver | `arch_surgery/idf_probe/run_a26_pulse.py` |
| `tables` | collates every recorded result into the tables §4 quotes | `arch_surgery/fixedpoint/analyse.py`, `tables.py` |

The last two stages compare against an untouched checkout of the base commit and need one:

```
git archive c0ae5b28 | tar -x -C /some/dir/pristine_c0ae5b28
python MDA_partition_experiment.py --parent-tree /some/dir/pristine_c0ae5b28
```

Without `--parent-tree` those two stages are skipped, and the run says so rather than passing
over them. To print the tables from artifacts that already exist, running nothing:

```
python MDA_partition_experiment.py --analyse-only --runs-root <dir>
```

**Test cases.** Phase A ran four, spanning two structurally different machine types: two large
conventional tokamaks (`large_tokamak_nof`, an optimisation run, and `large_tokamak_eval`, a
single evaluation run of the same deck), a low-aspect-ratio design (`low_aspect_ratio_DEMO`), and
a steady-state spherical tokamak (`st_regression`). The last of these lacks the quantity that
joins the blocks, so its blocks are already separate — it acts as a free control for H3.

**From 2026-09-02 the study runs three.** `large_tokamak_eval` is dropped: it runs **0 solver
iterations**, so it cannot inform a study about how an architecture behaves when the optimiser
reacts; its inequality constraints are never enforced, so its "solution" is not a feasible optimum;
its coupling-state classification rested on ten design points, on which 555 of 840 components look
constant; and two of those apparent constants are not constant and were inflating its counts
(§6.3). **Four-case tables in this report are the record of what was run** and are dated as such;
Phase B and everything measured after that date is three cases and says so.

### 3.7 Known limitations of the method

Stated in advance, so that none of them can be presented afterwards as a discovery.

**The comparison is of solve cost at fixed design points, not of a complete program run.** With
the optimiser removed, this experiment cannot say what a full optimisation would cost, because a
different loop would send the optimiser along a different path. The design points come from the
current program's path. The result is therefore about the mechanism, and a claim about total
runtime would require the optimiser to be put back — a separate, later phase.

**Solving each block tightly may be the wrong way to run a blocked arrangement.** Driving one
block to high precision against inputs from another block that is about to change is known to be
wasteful; the flat arrangement never pays this cost because it has no inner loop. The tight
setting is used here for simplicity and comparability. It is therefore **conservative against
H3**: if the blocked arrangement loses, the result does not distinguish "separating the blocks
does not help" from "separating the blocks was run in its least favourable configuration".
§4.5 quantifies how conservative, and §5.3 says what would have to be run to settle it.

**A stricter stopping test may fail where a loose one always succeeded.** The current loop never
reaches its own limit on any test case. A test on the model state may not converge at all in some
cases. This would not be a new fault introduced by the experiment — the non-convergence would
have been there all along, unreported — but it changes silent tolerance into visible failure, and
the report must say which of those it is valuing.

**The three-block decomposition comes from an analysis of one input file.** The dependency
analysis resolves conditional code against a specific configuration. It matches two of the four
test cases exactly. For the other two the decomposition was re-derived independently and the
three blocks survive, but this is a dependency on an external artefact and is recorded as such.

**Machine timings are not usable on this hardware.** Identical work varies by up to 35 % in
processor time for reasons not yet identified; contention and memory pressure have both been
eliminated by measurement. Timings are reported for context only, with the number of repetitions,
and never as evidence.

---

## 4. Results

Every number below is a count of model evaluations, a count of design points, or an exact
bit-comparison. Each is stated with the population it holds over. None is a timing; §4.9 reports
elapsed times, labelled as context, and nothing in §5 or §6 rests on them.

**Vocabulary used throughout.** A *sweep* (equivalently, a *pass*) is one execution of the model
sequence. A *model evaluation* is one invocation of one model within a sweep; each test case
reaches **21** models per sweep. Model evaluations are the primary unit because a flat sweep and a
blocked arrangement's inner sweep are not the same amount of work, and only per-model counting
makes them commensurable. §5.2 discusses what that unit does and does not capture.

### 4.1 The checks, reported before any measurement

| Check | Result | Denominator |
|---|---|---|
| The recording hook changes nothing when switched off | **0 differing output lines** on all four test cases | 16 174 / 16 435 / 18 692 / 15 917 lines, against an untouched `git archive` of the base commit |
| The recording hook changes nothing when switched **on** | **0 differing output lines**, same denominators | as above |
| Two identical runs agree | bit-for-bit, and sweep-for-sweep | all four test cases |
| The replay reproduces the live loop | arrangement R's pass count equals the real loop's, on **600 of 600** design points | 149 / 297 / 144 / 10 |
| The state is restored exactly for every arrangement | **0 mismatched fields** | all 2 288 data-structure fields, in every restore of every arrangement of every design point — 2 400 restores in the headline comparison alone |
| The recorded convergence scales match the recording they were measured from | hash-checked on every replay; a mismatch aborts before any work is done | 827–846 components per test case, committed as tracked data |

The replay-fidelity check failed once, at 599 of 600, and was root-caused rather than worked
around: PROCESS's loop does not always compare a constraint vector of the same length — the
`fsolve` path compares only the equality constraints — and the reproduction had assumed it did.
The fix records the length per design point, and **every artifact was regenerated from scratch**
so that no result mixes instrument versions.

The comparators were each shown capable of failing before their zeros were accepted: twenty
single-bit perturbations of a recorded result were caught 20 of 20 with 0 skipped, on every test
case; and a control arrangement running the same models in reverse order differs on **575 of 600**
design points (§4.4.4).

### 4.2 Drop census — reported before any ratio

| Test case | Design points | R | A0 | A0f | A1 | Complete for all four | Dropped | Limits reached |
|---|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 149 | 149 | 149 | 149 | 149 | **149** | **0** | none |
| `low_aspect_ratio_DEMO` | 297 | 297 | 297 | 297 | 297 | **297** | **0** | none |
| `st_regression` | 144 | 144 | 144 | 144 | 144 | **144** | **0** | none |
| `large_tokamak_eval` | 10 | 10 | 10 | 10 | 10 | **10** | **0** | none |

**Nothing was dropped, by any arrangement, on any test case, at either hoist setting.** No inner,
outer or global limit was reached at any point. The worst observed, over all 600 design points and
both hoist settings: **12** flat passes against an outer limit of 20; **7** outer passes in the
blocked arrangement against the same 20; **6** passes in any single inner block solve against an
inner limit of 20; and **45** block-passes for one design point against a global limit of 200. The
limits stayed detectors and never became budgets.

**This is a result in its own right and it went against expectation.** §3.7 and the experiment
plan both warned that a strict state-based stopping test might fail where the loose one always
succeeded, possibly in the control arrangement itself. It did not fail anywhere. Every ratio in
§4.4 is therefore over the same 600 design points for all four arrangements, with no censoring to
qualify it.

### 4.3 The tolerance, calibrated rather than chosen

Run on the flat arrangement alone, before any arrangement was compared. Convergence is tested on
the model state; the tolerance is *calibrated* by its effect on the objective and the constraint
vector at termination.

| Test case | τ | Converged | Mean passes | Model evaluations | Max relative move of the objective vs the tightest setting | Worst exit residual |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 1e-8 | 149/149 | 3.819 | 11 949 | — | 1.57e-11 |
| | **1e-6** | 149/149 | 3.027 | 9 471 | **0** | 1.05e-08 |
| | 1e-4 | 149/149 | 2.570 | 8 043 | **0** | 2.19e-05 |
| `low_aspect_ratio_DEMO` | 1e-8 | 297/297 | 3.848 | 24 003 | — | 9.51e-13 |
| | **1e-6** | 297/297 | 3.205 | 19 992 | **4.1e-16** | 1.67e-08 |
| | 1e-4 | 297/297 | 2.808 | 17 514 | **7.9e-07** | 2.20e-05 |
| `st_regression` | 1e-8 | 144/144 | 4.090 | 12 369 | — | 3.33e-10 |
| | **1e-6** | 144/144 | 3.438 | 10 395 | **2.0e-13** | 3.17e-08 |
| | 1e-4 | 144/144 | 2.931 | 8 862 | **2.7e-07** | 3.36e-06 |
| `large_tokamak_eval` | 1e-8 | 10/10 | 2.600 | 546 | — | 0 |
| | **1e-6** | 10/10 | 2.500 | 525 | **0** | 0 |
| | 1e-4 | 10/10 | 2.400 | 504 | **0** | 0 |

**τ = 1e-6 is the calibration point, and the ladder is itself a result.** Tightening from 1e-6 to
1e-8 moves the objective by at most 4.1 × 10⁻¹⁶ relative — machine epsilon, i.e. not at all —
while costing 26 %, 20 % and 19 % more model evaluations on the three optimisation cases and 4 %
on the evaluation case. Loosening to 1e-4 moves the objective by up to 7.9 × 10⁻⁷ relative, which
is larger than these decks' own solver convergence parameter of 1e-7, so 1e-4 is not safe even
though it is 12–15 % cheaper.

**Past 1e-6 the extra work is real convergence that does not reach the answer — it is *not*
round-off.** An earlier draft of this section said "the loop is converging noise", which is wrong
and worth correcting explicitly, because the two readings have different consequences. The state
residual keeps genuinely shrinking past 1e-6: the worst exit residual in the table above falls from
1.05e-08 to 1.57e-11 and from 1.67e-08 to 9.51e-13 across that step, and measured over every point
the residual after one further sweep falls by between 32× and 10⁶× per rung of the ladder and never
levels off. A round-off-limited iteration would flatten instead. What *does* stop is the objective:
it moves by at most 4.1e-16, 2.0e-13 and 0 relative on the three cases whose objective is actually
computed — far below these decks' own solver convergence parameter of 1e-7. So the last two decades
of tolerance refine state the objective does not depend on sensitively, and buy nothing for 19–26 %
more model evaluations. That is why 1e-6 is the calibration point; it is not because the arithmetic
has run out of precision. Plan §4.1c carries the measurement and its limits, including the one
place where the loop genuinely does iterate on a numerical artefact (issue I-12, 7 of 144 points on
`st_regression`).

Every point converged at every tolerance on the ladder: 1 800 of 1 800 point-solves, no limits, no
drops.

**One column carries a caveat that must not be dropped.** On `large_tokamak_nof` the objective is
`0.2 × rmajor` and `rmajor` **is a design variable**, so the objective there is a pure function of
the design vector and *cannot* move with τ. Its zeros are structural, not evidence. The other
three cases have computed objectives — maximise pulse length, maximise fusion gain, minimise
capital cost — and they are what carries the calibration.

### 4.4 The four effects, per test case

Reported separately, never pooled. Every figure is model evaluations over the pairwise-complete
population named in §4.2.

#### 4.4.1 The wasted pass, and the cost of a better stopping test

These two act in opposite directions, and arrangement A0f exists to separate them.

| Test case | n | R → A0f (stopping test only) | A0f → A0 (wasted pass only) | R → A0 (their sum) |
|---|---|---|---|---|
| `large_tokamak_nof` | 149 | **+1.55 %** | **−1.53 %** | **0.00 %** |
| `low_aspect_ratio_DEMO` | 297 | **−3.40 %** | **−1.55 %** | **−4.90 %** |
| `st_regression` | 144 | **+8.62 %** | **−1.79 %** | **+6.68 %** |
| `large_tokamak_eval` | 10 | **+27.3 %** | **−10.7 %** | **+13.6 %** |

**The wasted pass is real and it is worth 1.53 %, 1.55 %, 1.79 % and 10.7 %.** It is realised
exactly where the entering state is already converged, which is 7 of 149, 15 of 297, 9 of 144 and
3 of 10 design points — 4.7 %, 5.1 %, 6.3 % and 30 %. Those points converge in a **single** pass,
which is structurally impossible for arrangements R and A0f: their pass histograms have no `1:`
column and A0's does.

This is an order of magnitude below the "up to 31 %" the experiment plan carried before it was
measured. That bound required a pass to be saved on *every* solve; it is saved only on solves that
would otherwise have stopped at the two-pass floor. The correction is recorded in the project's
trap register as an instance of publishing a number without the condition that limits it.

**On `large_tokamak_nof` the two effects cancel to exactly zero — 9 471 model evaluations either
way — and that is the clearest justification for building A0f.** Per design point they do not
agree at all: the paired difference in passes is **−1 on 8 points, 0 on 134, +1 on 6, +2 on 1**.
A study that had measured only R → A0 would have reported "no effect" from two real, opposed
effects of about 1.5 % each.

**The stricter stopping test is not uniformly more expensive, and that direction was not
predicted.** On `low_aspect_ratio_DEMO` it is 3.40 % *cheaper*: 54 of 297 design points converge a
pass sooner, and one converges two passes sooner, because the objective and constraints were still
disagreeing after the model state had settled. The paired difference there is **−2 on 1 point, −1
on 54, 0 on 235, +1 on 7**. The loose test is not merely permissive; it is also sometimes slower.

`large_tokamak_eval`'s +27.3 % and −10.7 % are the largest figures in the table and rest on **10
design points**. They should be read as a direction, not a magnitude.

#### 4.4.2 The block partition against the flat control, at matched achieved accuracy

**This is the effect the study was designed around. Measured at matched tolerance it loses badly;
measured at matched achieved accuracy it does not lose at all — and the second is the honest
comparison.**

The two arrangements do not deliver the same accuracy when asked for the same tolerance. The
blocked arrangement solves each block to τ against inputs that are about to change, so it
terminates about **10⁵ times more converged** than the flat control at the same setting (§4.5(b)).
It did more work *and* got more accuracy, and only the work appears in a ratio. Comparing at
matched tolerance therefore measures a handicap.

**At matched tolerance** — the comparison this report carried before A26 measured the alternative:

| Test case | n | Flat **A0** | Blocked **A1** | A1 / A0 | Change |
|---|---|---|---|---|---|
| `large_tokamak_nof` | 149 | 9 471 | 13 906 | 1.468 | +46.8 % |
| `low_aspect_ratio_DEMO` | 297 | 19 992 | 28 070 | 1.404 | +40.4 % |
| `st_regression` | 144 | 10 395 | 9 917 | 0.954 | −4.6 % |
| `large_tokamak_eval` *(dropped, D17)* | 10 | 525 | 618 | 1.177 | +17.7 % |

**At matched achieved accuracy — and the answer depends on how the comparison is constructed, by
more than the effect either construction reports.** Both arms were run across ladders — the flat arm
across τ ∈ {1e-2 … 1e-8}, the blocked arm across the same joint ladder *and* across an inner-only
ladder at the calibrated outer tolerance — each run's achieved exit residual was recorded beside its
cost, and cost is read off each arm's **lower envelope**, `cost(a) = min{cost_i : accuracy_i ≤ a}`.

The blocked arm has **eleven** rungs to the flat arm's **six**, because the inner tolerance is a knob
the flat arm does not have. §7.13 explains why that is a one-sided advantage before any architecture
is involved. So the comparison is made twice:

| test case | n | **matched-count** — six joint rungs against six flat, one knob each | **all-settings** — eleven block rungs against six flat |
|---|---|---|---|
| `large_tokamak_nof` | 149 | **+33.4 %** (12 632 against 9 471) | **−4.3 %** (9 062 against 9 471) |
| `low_aspect_ratio_DEMO` | 297 | **+27.4 %** (25 463 against 19 992) | **−4.5 %** (19 087 against 19 992) |
| `st_regression` | 144 | **−15.2 %** (8 811 against 10 395) | **−13.1 %** (9 037 against 10 395) |

*(at the accuracy the flat control delivers at the study's own calibration point, τ = 1e-6.)*

**On two of three test cases the two constructions disagree in sign, and by 38 and 32 percentage
points.** That is an order of magnitude larger than the effect either of them reports. **Neither
number alone is the answer, and reporting one would be choosing on the reader's behalf.**

**What separates them, mechanically.** On the two large test cases the blocked arm's tight
same-knob rungs reach a **bit-exact fixed point** — the p90 achieved residual is exactly zero — and
cost 12 632 and 25 463. Its cheap tight rungs are the *inner-only* ones, at 9 062 and 19 087. So
**the whole of the −4.3 % and −4.5 % is bought by the second knob**, and at equal tuning effort the
partition costs a third more.

**And the matched-count reading has a bias of its own, in the other direction.** The blocked arm's
joint ladder is coarse in achieved accuracy: on `large_tokamak_nof` it jumps from 4.3 × 10⁻⁷ at
τ = 1e-4 straight to bit-exact at τ = 1e-5, with nothing near the 1.3 × 10⁻¹¹ target. The read is
therefore forced onto a rung that **overshoots** the target, which inflates the ratio. That is a
granularity limit of the ladder as run, not a property of the architecture.

**So the honest statement is a bracket, and its width is what this ladder can resolve.** On
`large_tokamak_nof` the partition's cost at matched achieved accuracy lies between **−4.3 % and
+33.4 %**; on `low_aspect_ratio_DEMO` between **−4.5 % and +27.4 %**; on `st_regression`, where the
two constructions agree to two percentage points, between **−13.1 % and −15.2 %**. Only the third
is a measurement in the sense the other numbers in this report are.

**This corrects, in part, the correction.** The finding that replaced this report's original
+46.8 % / +40.4 % was that at matched achieved accuracy the partition is *at parity or cheaper on
all three test cases*. **That holds under one construction of the envelope and not under the
other**, and the construction that supports it is the one that gives the blocked arm nearly twice
the draws. What survives without qualification is narrower and is still worth having: **the
published +46.8 % and +40.4 % were measured at matched tolerance, and at matched accuracy the
partition is nowhere near that expensive under any construction** — the widest matched-accuracy
figure is +33.4 %, and the cheapest is −15.2 %.

Across every accuracy the flat arm reached that also lies inside the blocked arm's measured range,
under the practitioner construction:

| Test case | A1 / A0 over the matched range | matched points |
|---|---|---|
| `large_tokamak_nof` | 0.957, 0.968, 0.837, 0.858, *1.150* | 5 of 5 flat rungs |
| `low_aspect_ratio_DEMO` | 1.334, 0.955, 0.949, 0.793, 0.902, *1.094* | 6 of 6 |
| `st_regression` | 0.844, 0.869, 0.871, 0.923, 0.960, *1.119* | 6 of 6 |

*The italicised last entry on each case is the loosest flat rung, where the blocked arm has no rung
as loose and the envelope is read flat. That is a limit of the ladder, not a win for either arm.*

**The replacement claim is narrow and must stay narrow.** What it removes is the *magnitude* of
the published penalty, not its sign: the +46.8 % and +40.4 % were an artifact of comparing at
matched tolerance, and at matched accuracy the partition costs somewhere between 4 % less and 33 %
more depending on how the envelope is built. It does **not** establish that the partition is worth
anything. Four further things bound it, and none is a hedge the surrounding framing contradicts:

1. **It is statistic-dependent, and the worst-case statistic straddles parity.** Rebuilt on the
   **maximum** exit residual instead of the p90, A1/A0 ranges 0.907–1.150, 0.816–1.228 and
   0.824–1.119: on the single worst design point the two arms are not distinguishable. On the
   **median** the comparison cannot be made at all, because the median exit residual is exactly
   zero on 15 of 17 rungs on `large_tokamak_nof` and 13 of 17 on `low_aspect_ratio_DEMO` — the
   state is a bit-exact fixed point on most points. **The correct summary is "at parity or cheaper
   on the p90; indistinguishable on the worst point".**
2. **The mechanism is that the over-solving was the cost, not that blocking wins.** The blocked
   arm's cheapest setting reaching the target accuracy on the two large cases is inner τ = 0.1,
   where **1 172 of 1 248 inner solves take a single sweep** (71 take two, 5 take three). At that
   setting the arm is barely a block solver: it is close to a flat sweep in block order with an
   outer state test.
3. **The blocked arm had more settings tried** — eleven rungs against six, because the inner
   tolerance is a parameter the flat arm does not have. Best-of-eleven against best-of-six is a
   systematic advantage. It is bounded rather than eliminated: the flat arm's rungs are all on its
   own envelope on all three cases, so its curve is already monotone.
4. **This is Phase A, with the optimiser absent.** What an optimiser reacting to the arrangement
   would do is §7.

**The construction matters and getting it wrong flips the sign.** Reading the rungs in tolerance
order instead of taking the lower envelope gives **+21.9 %** on `large_tokamak_nof` where the
envelope gives **−4.3 %**. Several settings deliver the same achieved accuracy at different costs —
on that case the blocked arm reaches 1.256 × 10⁻¹¹ at four different inner tolerances, costing
12 281, 11 543, 9 612 and 9 062 model evaluations — and "what does this arm cost at accuracy *a*"
has one honest answer: the cheapest setting delivering at least *a*. The comparison at the tightest
matched accuracy is exact rather than interpolated: blocked `inner0.1` achieves
`1.2556721063507803e-11`, **bit-identical** to flat `tau1e-06`, for 9 062 model evaluations against
9 471, at 2.792 mean sweeps against 3.027.

Two things about the matched-tolerance table remain true and are worth keeping.

**The blocked arrangement does what the partition hypothesis predicted, in the unit the hypothesis
was stated in.** Its outer pass count is lower everywhere: 2.705 against 3.027 on
`large_tokamak_nof`, 2.721 against 3.205 on `low_aspect_ratio_DEMO`, 2.139 against 3.438 on
`st_regression`, 2.400 against 2.500 on `large_tokamak_eval`. Against the flat control it falls on
36 of 149, 100 of 297, 120 of 144 and 1 of 10 design points, and **rises on none, on any deck**.

**The one case where it did not lose even at matched tolerance is the one with no coupler.**
`st_regression` sets `i_pulsed_plant = 0`, so the burn time that joins the blocks is never written
by any in-loop model: its blocks are already independent and its outer loop is trivial by
construction. That is the partition working exactly as designed, and simultaneously the case in
which the partition is doing the least.

**The comparison is the grouping alone, and that had to be established rather than assumed.**
Building the blocked arrangement by grouping the models by block also transposes two adjacent
models — `build` and `physics` — relative to the flat order. Nobody named that while the
comparison was built. It was closed afterwards by replaying the flat arrangement in the blocked
arrangement's node order: identical to the recorded flat arrangement on **600 of 600** design
points, and on **2 400 of 2 400** across every setting the flat arrangement was recorded under
(both hoist settings and all three tolerances), compared bit-for-bit with no tolerance anywhere —
pass counts, model-evaluation counts, the converged flag, the full residual trace at every pass,
and the exit audit. §4.4.4 records what that null does and does not license, and §7.4 measures the
same transposition a second time, in PROCESS's own driver, where it also costs exactly nothing.

#### 4.4.3 The feed-forward hoist

Two models — `water_use` and `costs` — write nothing that any model earlier in the loop reads.
Running them once after the loop instead of on every pass is the **feed-forward hoist**. It is the
only change measured here that is separable, carries no dimension penalty, and leaves the answer
bit-identical.

**Measured in PROCESS's own driver**, against an untouched checkout of the base commit:

| | `large_tokamak_nof` | `low_aspect_ratio_DEMO` | `st_regression` | `large_tokamak_eval` |
|---|---|---|---|---|
| tail resolved at run time | `water_use`, `costs` | `water_use`, `costs` | `water_use`, `costs` | **`water_use` only** |
| model evaluations, hook off | 42 609 | 90 006 | 39 711 | 609 |
| model evaluations, hook on | 39 815 | 83 918 | 37 073 | 593 |
| **evaluations removed** | **2 794** | **6 088** | **2 638** | **16** |
| **as a fraction of the hook-off total** | **6.56 %** | **6.76 %** | **6.64 %** | **2.63 %** |
| sweeps | 2 029 → 2 029 | 4 286 → 4 286 | 1 891 → 1 891 | 29 → 29 |
| output lines differing vs the reference checkout | **0** of 16 174 | **0** of 16 435 | **0** of 18 692 | **0** of 15 917 |
| output floats differing, as hex literals, no tolerance | **0** of 13 559 | **0** of 13 455 | **0** of 13 493 | **0** of 13 487 |
| solver exit flag | 1 → 1 | 1 → 1 | 1 → 1 | 1 → 1 |

*(The sweep counts in that row are totals recorded by this instrument, which sees two passes on
the post-solve output path as well as the 2 027 the loop itself performs. §1.2's 2 027 and this
row's 2 029 are the same run counted at two boundaries.)*

The saving is **not** the naive 2 of 21 models = 9.5 %, and the arithmetic is worth stating
because the difference is exactly the point of the hoist. On `large_tokamak_nof` the hook removes
**4 054** in-loop evaluations and adds back **1 260** — one run of each of the two models per
solve, 630 solves — for a net **2 794** of 42 609. The hoist does not remove the tail; it stops
re-running it.

**Sweeps are unchanged on all four cases.** The hoist removes work *within* passes, not passes.
This is the one measured effect in the study that a sweep-counting analysis would have valued at
exactly zero.

**The hoistable set depends on the deck, not only on the code, and this is the more important
finding.** PROCESS's loop stops on the objective and the constraint residuals. The objective
function reads `costs.coe` under figure of merit 6 and `costs.cdirt` / `costs.concost` under
figure of merit 7 — all written by `costs`, a tail model. `large_tokamak_eval` sets no `minmax`
and so takes the default figure of merit 7. On that deck the driver must keep `costs` inside the
loop and hoists `water_use` alone, which is why its saving is 2.63 % and not the ~5.3 % the same
arithmetic would otherwise give. The feed-forward tail is a property of the deck as well as of the
program.

**The `4.6–8.2 %` figure quoted in older documents is superseded and should not be requoted.** It
differed in three particulars, all of them established: its node set included `Pulse`, which cannot
leave the loop while the burn-time coupler is in it; its unit was dependency-graph rows rather
than model calls, and only 2 of the tail's 5 rows are reachable by a driver-level hoist at all
(one is not a driver call site, and one *is* the convergence test); and its low end came from a
wall-clock weighting that this project has since retired. Restating the older arithmetic on this
node set and in this unit accounts for the entire gap with no unexplained residue.

**Read that reconciliation as a reconciliation and not as a confirmation.** The restated
prediction is recomputed from the same run's own sweep and model-call counts — the very quantities
the measurement counted — so it is an algebraic identity and cannot disagree. What it establishes
is that the gap is *entirely* node set and unit. It does not independently corroborate the
measured value.

**The hoist measured inside the replay engine is a different quantity, and the two must not be put
in one column without saying so.** In the replay engine the hoist removes 2 of 21 loop models, and
the engine's headline model-evaluation totals count the in-loop models only, recording the single
post-loop tail run in a separate field. Loop-only, that is −9.52 % on three cases and −16.47 % on
`st_regression`. Adding the recorded tail runs back gives the net saving on the flat control:

| Test case | Flat control, hoist off | in-loop, hoist on | post-loop tail runs | net total | net saving |
|---|---|---|---|---|---|
| `large_tokamak_nof` | 9 471 | 8 569 | 298 | 8 867 | **−6.38 %** |
| `low_aspect_ratio_DEMO` | 19 992 | 18 088 | 594 | 18 682 | **−6.55 %** |
| `st_regression` | 10 395 | 8 683 | 288 | 8 971 | **−13.70 %** |
| `large_tokamak_eval` | 525 | 475 | 20 | 495 | **−5.71 %** |

The first two agree closely with the driver-side 6.56 % and 6.76 %, which is the right
cross-check: two instruments, two populations, one mechanism. `st_regression` is nearly double
because there the hoist also removes something else — see §4.8.

**On `large_tokamak_eval` the two instruments are not measuring the same architecture.** The
replay engine's hoist has no figure-of-merit guard and lifts `water_use` **and** `costs` on that
deck, where PROCESS's driver lifts `water_use` alone. This is confirmed by measurement, not by
reading: the engine's own recorded topology for that deck names both. Neither is wrong in its own
setting — the engine converges on the measured coupling state, not on the objective and
constraints, so lifting `costs` there does not corrupt its stopping test the way it would in the
driver. But it does mean that **the engine's −5.71 % and the driver's 2.63 % on that deck are
figures for two different model sets**, and no table may place them side by side without this
sentence. It is recorded as an open issue against the study.

#### 4.4.4 The node-order control, and what it licenses

| Arrangement | What it varies | Design points differing from the recorded flat arrangement |
|---|---|---|
| flat, in the blocked arrangement's node order | the `build`/`physics` transposition | **0 of 600** (and 0 of 2 400 across all settings) |
| flat, one design-vector component nudged by one bit | a single last-bit change to one input | **488 of 600** |
| flat, all models in **reverse** order | the ordering, comprehensively | **575 of 600** |

**This licenses one sentence and forbids another.** It licenses: *the flat-to-blocked comparison
isolates the module grouping; the sequence permutation that came with the grouping contributes
nothing.* It forbids: *node order does not matter.* Reversing the order changes 575 of 600 design
points at τ = 1e-6 with the hoist off, and 564 of 600 with it on. What is inert is **one
transposition of two adjacent models**, and the claim must be worded that way.

Per test case, the reversed-order control differs on 149/149, 284/297, 133/144 and 9/10; the
one-bit control on 129/149, 222/297, 127/144 and 10/10.

The same transposition was independently measured in PROCESS's own driver, where moving `build`
out of the physics block's span leaves **0 differing output lines** of 16 174 / 16 435 / 18 692 /
15 917 and **0 differing floats** of 13 559 / 13 455 / 13 493 / 13 487, with the solver exit flag
unchanged and the sweep count unchanged at 2 029 / 4 286 / 1 891 / 29. The two agree; neither
substitutes for the other, since they exercise different drivers and different stopping tests.

That transposition is also what makes the physics block contiguous in the call order, which a
per-block solver needs. It is the one architectural change in the study that is a precondition
rather than a result.

**One thing this does bear on that is not about this experiment.** The dependency graph
interleaves these two models at row level — `build` holds row 5 while `physics` holds row 4 and
rows 6–28, so `build`'s row sits inside `physics`'s span — yet transposing the two call sites is
inert at the trajectory level, not merely at the fixed point. Row adjacency in the collapsed
dependency graph is not evidence of coupling between the call sites those rows belong to.

### 4.5 What the incumbent loop leaves un-converged

Every arrangement runs one further full pass past termination and the same global residual is
recorded, so accuracy is verified per design point rather than assumed from a shared tolerance.

| Test case | Arrangement | Worst exit residual | Median | Design points failing the audit |
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

**(a) PROCESS's loop stops with named model outputs still moving, on 8 of 600 design points, and
it is always the cost model.** The fields above tolerance are `costs.coe`, `costs.coecap` and
`costs.coefuelt` on all 8, plus `costs.bktcycles`, `costs.coeoam` and `power.qac` on the
`large_tokamak_nof` one. These are in the feed-forward tail: nothing reads them back inside the
loop, which is exactly why a stopping test watching only the objective and the constraints cannot
see them move. The three state-based arrangements fail the same audit on **0 of 600**.

**Read that as a finding about the stopping test, not a physics claim, and note what limits it.**
`costs.coecap` ranges from 102 to 6.5 × 10²¹ across `st_regression`'s recorded entry states, so a
median-based scale is a weak normaliser for that particular field and the figure 8.11 × 10⁸
overstates how surprising the *absolute* change is. What does not depend on the normaliser is that
the field is still changing by orders of magnitude when the loop declares itself idempotent.

**(b) The arrangements are not at equal accuracy, and it is the audit that reveals it.** The
blocked arrangement terminates at a residual roughly **10⁵ times tighter** than the flat control at
the same tolerance, because its inner solves drive each block to τ and the outer test then passes
at once. Its +17.7 %, +40.4 % and +46.8 % are therefore **cost at better accuracy, not cost at
equal accuracy**. This is the quantification of the conservatism §3.7 declared in advance, and it
is why §4.4.2 reads cost off at matched *achieved* accuracy instead. **Measured that way the
handicap is the whole of the published difference**: the blocked arrangement is at parity or
cheaper on all three retained cases. The exit audit is also the accuracy measure §4.4.2's
envelopes are built on, which is why it is an instrument identical across arms — one further full
sweep of the complete model set, at every setting — rather than each arm's own stopping test.

**(c) With the feed-forward models lifted, all four arrangements fail the audit on the same 7 of
144 points of `st_regression`.** Hoisting does not converge those fields; it stops asking. The
audit still runs the full model set, and the tail has been solved once rather than iterated. That
is defensible — the tail feeds nothing back, so the state it is computed from is converged even if
it is not itself iterated — but it is a consequence and not a free saving. The worst residual there
is 8.11 × 10⁸ for R, A0 and A0f and 2.76 × 10⁷ for A1.

### 4.6 The magnitude distribution of the objective and constraint vector

This discharges a standing commitment to the sibling dependency-analysis study, whose own
addendum measured the magnitude distribution of the quantities in PROCESS's output file and
explicitly left the idempotence loop's own set unmeasured. Measured here, from every objective
value and every constraint vector evaluated inside the loop during a full optimisation run of each
case:

| Test case | Quantity | n | ≤1e-8 | 1e-8..1e-6 | 1e-6..1e-4 | 1e-4..1e-2 | 1e-2..1 | 1..1e3 | >1e3 | zero |
|---|---|---|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | objective | 2 027 | 0 | 0 | 0 | 0 | 0 | 2 027 | 0 | 0 |
| | constraints | 52 728 | **892** | 792 | 4 270 | 11 609 | 34 504 | 661 | 0 | 0 |
| `low_aspect_ratio_DEMO` | objective | 4 284 | 0 | 0 | 0 | 0 | 4 283 | 1 | 0 | 0 |
| | constraints | 107 125 | **20 342** | 4 626 | 8 085 | 22 199 | 51 731 | 141 | 1 | 0 |
| `st_regression` | objective | 1 889 | 0 | 0 | 0 | 0 | 0 | 1 888 | 0 | 1 |
| | constraints | 34 020 | **2 084** | 1 904 | 2 704 | 4 770 | 18 275 | 4 283 | 0 | 0 |
| `large_tokamak_eval` | objective | 30 | 0 | 0 | 0 | 0 | 29 | 0 | 1 | 0 |
| | constraints | 200 | **22** | 2 | 22 | 22 | 126 | 6 | 0 | 0 |

Bin membership is `|v| ≤ edge`; zeros are counted separately from every bin, and there are none in
the constraint vectors. No "not a number" or infinity appeared in any objective or constraint
vector on any case.

**The hole is larger in the loop's own set than in the output-file set.** PROCESS's stopping test
is `np.allclose(rtol=1e-6)`, which carries a hidden absolute term of 1e-8; below about 1e-2 that
absolute term rather than the relative one decides, and below 1e-8 agreement is unconditional.

| Test case | Non-zero constraint entries below **1e-2** | below **1e-8** |
|---|---|---|
| `large_tokamak_nof` | 17 563 / 52 728 = **33.3 %** | 892 = **1.7 %** |
| `low_aspect_ratio_DEMO` | 55 252 / 107 125 = **51.6 %** | 20 342 = **19.0 %** |
| `st_regression` | 11 462 / 34 020 = **33.7 %** | 2 084 = **6.1 %** |
| `large_tokamak_eval` | 68 / 200 = **34.0 %** | 22 = **11.0 %** |

Against the output-file set's 18.0 % below 1e-2 and 203 entries below 1e-8. On
`low_aspect_ratio_DEMO`, **19 % of every constraint value the loop ever compares is small enough
that the test reports agreement no matter what the value does**, and more than half are in the
regime where the absolute term rather than the relative term decides.

The same measurement on the *coupling state* — the quantities the new stopping test watches — is
sharper still. Continuous quantities span **2.4 × 10⁻²² to 9.1 × 10²¹**, 43 orders of magnitude;
2 to 6 components per case have a working magnitude *below* 1e-8, so a single inherited absolute
term would have sat up to fourteen orders of magnitude above the quantity itself and passed any
change whatsoever; and 5–7 % are in the regime where it would dominate.

| Test case | Continuous components | scale < 1e-8 | scale < 1e-2 | min scale | max scale |
|---|---|---|---|---|---|
| `large_tokamak_nof` | 694 | 2 (0.3 %) | 37 (5.3 %) | 2.96e-22 | 3.25e+21 |
| `low_aspect_ratio_DEMO` | 698 | 2 (0.3 %) | 35 (5.0 %) | 2.44e-22 | 4.74e+21 |
| `st_regression` | 582 | 6 (1.0 %) | 39 (6.7 %) | 4.25e-22 | 9.11e+21 |
| `large_tokamak_eval` | 285 | 2 (0.7 %) | 18 (6.3 %) | 2.81e-22 | 4.64e+21 |

A single absolute tolerance is not defensible on a set with that spread. The per-quantity scale
used here is not a refinement but a requirement, and it is committed as tracked data — key,
category, scale as decimal *and* exact hex float, and the number of design points the scale was
measured over, for every one of the 827–846 components per case — so that a wrong exclusion can be
found by inspection rather than only by its absence of symptoms.

**The commitment is therefore discharged, in both sets.** Nothing on this front remains owed.

### 4.7 What joins the blocks, and what removing it would be worth

The blocked arrangement was replayed a second time with the burn time held at its entry value and
re-imposed after every model call — the loop topology that would exist if the burn time became an
input supplied from outside the loop.

| Test case | n | Blocked, model evaluations | Burn time held fixed | Change | Mean outer passes |
|---|---|---|---|---|---|
| `large_tokamak_nof` | 149 | 13 906 | 9 848 | **−29.2 %** | 2.7047 → 1.9530 |
| `low_aspect_ratio_DEMO` | 297 | 28 070 | 19 774 | **−29.6 %** | 2.7205 → 1.9495 |
| `large_tokamak_eval` | 10 | 618 | 418 | **−32.4 %** | 2.4000 → 1.7000 |
| `st_regression` | 144 | 9 917 | 9 917 | **0.0 %** | 2.1389 (no burn-time coupler) |

On the three pulsed cases, holding the burn time fixed removes **every** quantity above tolerance
on outer pass 2 or later — not most of it, all of it, on 149/149, 297/297 and 10/10 design points.
The coil block never re-solves at all. On `st_regression` no block ever re-solves on outer pass 2
or later, on any of its 144 points: it has no cross-block movement of any kind.

**The mechanism is precise and it is not what "the burn time is the coupler" first suggests.** The
burn time itself is never the moving field; it settles during the first outer pass. What forces a
third pass is that the physics block runs *before* the pulse model in the block order, so it has
not yet seen the settled value when it runs. The five fields the physics block rewrites are the
same five on every such point — `times.t_burn_0`, `times.t_plant_pulse_plasma_present`,
`times.t_plant_pulse_total`, `physics.vs_plasma_burn_required`,
`physics.vs_plasma_total_required` — all written by `physics`, all functions of the burn time.
That is one one-step cycle behaving exactly as one should: it costs precisely one extra outer
pass.

**This is not a saving anyone can bank, and quoting it as one would be an error of exactly the
kind this project has already made three times.** Three conditions cut it down:

1. It is **the blocked arrangement against itself** with one coupler removed, over one deck's
   recorded design points, at τ = 1e-6. It is not the blocked arrangement against PROCESS's own
   driver, which is what a later phase would have to compare.
2. **Removing the coupler from the loop costs a design variable.** These decks carry 20, 19, 14 and
   2 design variables; hosting the burn time on the optimiser makes that 21, 20, — and 3. PROCESS
   takes central differences, so a gradient costs `2n` solves and one more variable is `1/n` more:
   **+5.0 %** on `large_tokamak_nof` and **+5.3 %** on `low_aspect_ratio_DEMO`, stated against the
   *current* cost. Composing, `1.050 × 0.708 = 0.743` and `1.053 × 0.704 = 0.741` — about **−26 %**
   — *if the optimiser's iteration count does not change.*
3. **Nothing bounds whether it changes.** Adding a variable and an equality constraint changes the
   subproblem the optimiser solves. Its iteration count could move either way by more than 26 %.

**And the pinned arrangement is a topology probe, not a candidate architecture.** Holding the burn
time away from its self-consistent value moves the exit objective on `low_aspect_ratio_DEMO` by a
median relative 4.9 × 10⁻⁴ and a maximum of 3.6 × 10⁻¹ over 297 points. Any real version would
have to drive that residual to zero through a constraint, and equivalence would be a gate it still
has to pass.

### 4.8 A degenerate cost evaluation inflates seven outer-pass counts

`st_regression` is the one case whose behaviour is not fully explained by architecture, and the
reason must be reported with its denominator rather than dropped.

Of its 144 design points, **9** converge in one outer pass and **128** in two — one pass of work
plus one pass that changes nothing and exists only because convergence cannot be certified without
it. The remaining **7 of 144** run to 4, 6 or 7 passes. On every one of those, the only quantities
above tolerance from outer pass 2 onwards are three fields of PROCESS's 1990 cost model —
`costs.coe`, `costs.coecap`, `costs.coefuelt` — which sit in the feed-forward tail, downstream of
every block.

**Six of those seven design points have negative net electric power** (−1.6 to −3.0 MW, against a
deck median of +110 MW over the other 137 points), which makes the cost of electricity diverge:
`costs.coe` reaches 6.6 × 10²¹ against a characteristic scale of 1.25 × 10³. The relative test,
scaled by a median magnitude, is therefore roughly **10¹⁸ times tighter than intended** at exactly
those points, and the loop runs on until the state is bit-identical. The seventh point enters
feasible (+1 434 MW) and reaches the same region during the first outer pass.

**This is not coupling.** All three fields are written in the feed-forward tail, downstream of
every block. But it inflates an outer-pass count, and outer-pass counts are an acceptance quantity
here.

It also explains why the hoist is worth nearly double on that case (§4.4.3): lifting the tail out
of the loop removes the mechanism entirely. `st_regression`'s blocked arrangement goes from
`{1: 9, 2: 128, 4: 1, 6: 3, 7: 3}` to `{1: 9, 2: 135}`, mean 2.139 → 1.938, with all seven long
points gone. That is a reason to want the hoist beyond its own saving, and it should be stated as
such rather than folded into the saving.

**It is also a robustness observation about PROCESS itself**, of the same class as the "not a
number counts as agreement" finding: a relative convergence test scaled by a characteristic
magnitude becomes arbitrarily tight wherever a quantity diverges, and PROCESS's 1990 cost model
diverges at infeasible points. It is owed to the sibling code-analysis study with the 7/144
denominator and the magnitudes.

### 4.9 Runtime, as context only

**No conclusion in this report rests on a timing.** Every acceptance quantity above is a count or
an exact bit-comparison, and all of them reproduced identically across two full pipeline runs. The
figures below are recorded because the plan gave a budget, and with two caveats: the machine was
**not quiet** while some of this ran, and identical work on this host has been observed to vary by
up to 35 % in processor time for reasons not yet identified.

| Stage | One full pass, four test cases |
|---|---|
| Recording the design points (one instrumented run per case) | 87 + 188 + 82 + 6 s = **364 s** |
| Tolerance ladder (12 replays) | 5.1–26.0 s each, **163 s** |
| Arm comparison — 4 arrangements × 4 cases × 2 repetitions, plus the hoist variant | 6.0–79.2 s each, **513 s** |
| Check suite (16 PROCESS runs) | 6.4–192 s each, **883 s** |

A **single** pass of all four arrangements over all four cases is **157 s**; the 513 s above is
three such passes. The plan's budget was "a few minutes for a full multi-arm pass with a cached
recording", and that is met. Peak resident memory during a PROCESS run is 423 MB.

### 4.10 One check this write-up performed on itself

**The full pipeline was not re-run for this write-up**, and that is stated rather than left to be
inferred: the machine has one heavy measurement slot and it was in use. What was run is the
analysis path, which is cheap.

The wrapper described in §3.6 was run in `--analyse-only` mode over the recorded artifacts, and
its collated result was compared against the same analysis invoked directly. The two are
**identical after normalising the artifact paths** — SHA-256 `14d18c70…` on both — and the
rendered tables are identical line for line, 300 lines. Two invocation paths agreeing is a
determinism check on the analysis, and it is what allows the numbers in §4 to be quoted from the
artifacts rather than transcribed from the earlier task reports. **No count differed from the
recorded one**; had one differed, that would have been a finding to report rather than a
discrepancy to reconcile.

Every number in §4 was in fact re-derived from the recorded artifacts for this write-up. Five
places where a re-derivation sharpened or corrected the wording of an earlier task report are
recorded in §6.4.

---

## 5. Discussion

### 5.1 What the experiment establishes

**The existence proof succeeds, on the hoist and not on the partition.** The study set out to find
one fair case in which a simple change to the arrangement of solvers measurably changes the cost
of solving PROCESS, with every model frozen. It found one: running two feed-forward models once
after the loop instead of on every pass removes 6.56 %, 6.76 %, 6.64 % and 2.63 % of all model
evaluations, on four test cases, with every number in the output file bit-identical to the
reference checkout — 0 differing floats of 13 559, 13 455, 13 493 and 13 487, compared as hex
literals with no tolerance anywhere. Architecture matters, measurably, in the direction of it
being possible to do better.

**The partition that motivated the study does not succeed.** It costs 46.8 %, 40.4 % and 17.7 %
more model evaluations on three of four cases — as an upper bound, per §4.5(b) — and its one
non-loss, 4.6 % cheaper, is on the case that has no cross-block coupler to break. Nothing in this report should be read as evidence for the partition,
and a summary that reported "the architecture change is worth 6.6 %" while implying the partition
delivered it would be a misattribution of exactly the kind this project has recorded three
instances of.

**The quiet results may outlast both.** The study's ancillary measurements say more about PROCESS
than either headline does:

- The loop's stopping test compares quantities of which **19 % (on `low_aspect_ratio_DEMO`) are
  small enough that agreement is unconditional**, and a third to a half of which sit where an
  absolute floor rather than a relative tolerance decides.
- The loop **stops with named model outputs still moving** on 8 of 600 design points, always
  including the levelised-cost family and on one point three further plant and cost quantities,
  precisely because those are the outputs the stopping test does not watch.
- The loop **treats a "not a number" state as converged**.
- The dependency graph's own feedback-edge set, had it been used as the convergence criterion,
  would have declared the fixed point reached **0.96 to 2.44 passes early**, on 142 of 149, 282 of
  297 and 135 of 144 design points on the three larger cases and 7 of 10 on the fourth — and
  **never late, in 600 tries**. Three of its four fields are classified constant across the whole
  recording, and on `st_regression` the fourth is absent from the measured coupling set entirely.

None of these is an architecture result. All four are things measurement found while looking for
one.

### 5.2 The unit problem, which reaches further than this experiment

**In passes the blocked arrangement wins on every test case. In model evaluations it loses by 18 %
to 47 %.** Both are exact counts of real things. They disagree because a pass over the physics
block is not the same work as a pass over everything.

That disagreement is not confined to the blocked arm. The mechanism argument that made the
partition look promising in the first place — *the physics block is more than twice either other
block, so partitioning cannot save much unless a small block is driving the loop* — is stated in
**dependency-graph rows**, and rows do not correspond to execution. The instrument records the
mapping directly:

| Block | Dependency-graph rows | Model calls actually executed |
|---|---|---|
| M1 Physics | 24 | **2** |
| M2 Coils | 10 | **3** |
| M3 Plant | 12 | **13** |
| Pulse | 1 | 1 |
| Feed-forward tail | 5 | **2** |

The physics block is 46 % of the rows and 2 of the 21 model calls, because `physics.run()`
orchestrates a whole sub-model block internally. The plant block is 23 % of the rows and 13 of the
21 calls. **The unit that made the argument inverts the argument.**

Three candidate units are available and none is satisfactory:

| Unit | Exact? | Tracks work? |
|---|---|---|
| dependency-graph rows | yes | no — the mapping above |
| model calls | yes | no — `physics.run()` and `cryostat.run()` count the same |
| measured cost | **no** — identical work varies up to 35 % on this host | yes |

This experiment counts model evaluations and applies no cost weight, because the only available
weight is a timing and this project retired timing-derived weights after one moved from 6.4 % to
4.4 % across runs of identical code — an instability comparable to the effect it was being used to
resolve. That is the right call under the project's rules and it leaves a real hole: **the exact
units are in the wrong currency and the right currency is not exact.** No statement of the
partition's cost should be made without naming its unit, and the same is true of the hoist, whose
older `4.6–8.2 %` band was wrong partly *because* it was quoted in rows.

The honest resolution is not available from this data. What would resolve it is a per-model cost
measure that is exact — a deterministic instruction or floating-point-operation count, for
instance — which nothing in this study provides.

### 5.3 Why the blocked arrangement lost, and what that does and does not settle

Four mechanisms, in decreasing order of how well the data supports them.

**1. It was run in its least favourable configuration, and that turned out to be the whole of the
difference.** The inner blocks were driven to the same tolerance as the outer loop, so the blocked
arrangement terminated at a residual about 10⁵ times tighter than the flat control at the same
nominal tolerance. It was paying for accuracy nobody asked for. **The inexact-block regime has now
been run**: across an inner-tolerance ladder, read off each arm's lower envelope at matched
achieved accuracy, the partition is at parity or cheaper on all three retained cases (§4.4.2). So
this mechanism is not one of four candidate explanations for a loss — it *is* the loss, and there
is no loss left to explain once it is removed. What remains to explain is the narrower fact that
the partition is not measurably *better* either, and mechanisms 2 to 4 below are about that.

**2. The condition the mechanism needs is not met.** A blocked arrangement saves when a *small*
block is holding up a *large* one. Measured under the old stopping test, the three blocks stop
changing together and the large physics block is joint-last in 82–85 % of solves; under
partitioning the laggard moves to the coil block, which is also not small on any available
weighting (10 of 46 nodes by count; the 42 %-of-cost figure is wall-clock-derived and is not used
as evidence — §2.1). Under the new stopping test the outer count does fall everywhere — which is
the mechanism working — but the blocks are not lopsided enough for the saving to exceed what the
inner solves cost.

**3. There is only one cross-block coupler, and it is weak.** The census in §4.7 shows the burn
time settles in the first outer pass on every pulsed case, and the extra pass exists only because
the physics block runs before the pulse model. There is very little cross-block iteration for a
blocked arrangement to *avoid*, because there was very little happening in the first place.

**4. The counting unit is unfavourable to blocks by construction** (§5.2). An inner sweep over the
two-call physics block and an inner sweep over the thirteen-call plant block count 2 and 13, but
the physics call is the expensive one. This does not rescue the result — the direction and the
magnitude are both large — but it means the true penalty is not known to be 47 %.

**What none of this settles.** Whether a differently-drawn partition would win; whether an inexact
inner tolerance would; whether any of it transfers to a deck resolving different switches. The
study measured one partition, derived from one dependency analysis, on four decks, at one commit.

### 5.4 The scope limits, stated as limits and not as apologies

- **Four decks, tokamak only, one commit.** Stellarator and inertial-fusion configurations take an
  early return in the driver and were not exercised at all. `st_regression` also sets `itart = 1`
  and a different toroidal-field path, so it is coverage, not a replicate.
- **`large_tokamak_eval` is the weakest of the four and every figure resting on it should be read
  as a direction.** Its recording is 10 design points from a single evaluation run. On that sample
  **555 of its 840 coupling-state components look constant**, against 140–243 on the cases with
  144–297 points — and two of those apparent constants were then observed to move 21 times each.
  They are not constants; the sample was too small to see them vary. This changed no result (its
  drop census is 10/10 on every arrangement) but no conclusion should rest on that deck's category
  counts, and its +27.3 % and −10.7 % in §4.4.1 are two of the largest figures in the report over
  ten points.
- **The dependency graph is configuration-specific.** It resolves conditionals against a preset
  built from one input file, which matches the two large tokamaks exactly, diverges from
  `low_aspect_ratio_DEMO` moderately and from `st_regression` about twice as far. The block
  boundaries were re-derived per deck and survive — zero new cross-block cells on `st_regression`,
  boundaries intact — but the block arrangement depends on an external artefact and the stopping
  test deliberately does not: the coupling set is instrumented at run time.
- **The design points come from PROCESS's own optimisation trajectory.** The answer is "this
  arrangement costs *this* on the points the current program visited", not a claim about the
  design space. A different loop would visit different points. This is accepted rather than
  engineered around: it is sound for an existence proof and insufficient for an adoption decision.
- **The comparison is per-solve cost with the optimiser absent.** Nothing here speaks to optimiser
  iteration counts, robustness of the search, or total runtime.

### 5.5 What Phase B adds, and what it takes away

**It adds the only measurement an adoption decision could rest on**, and it takes away the previous
version of its own answer.

**What it adds.** Phase A measures what an arrangement costs on the design points PROCESS's own
optimiser visited. That is sound for an existence proof and silent on the question that matters: a
loop that is cheaper per solve is worth nothing if the optimiser then takes more solves. Phase B
answers it, and the answer is that on these test cases **the optimiser barely reacts at all** — the
paired ratio of optimiser iterations is exactly 1.000 at the lower quartile, the median and the
upper quartile on two test cases, and moves in the variant's favour on the third. The risk this
phase was designed around did not materialise. Nothing bounded that in advance, and it could have
gone the other way by more than the whole saving.

**What it takes away is a verdict, and the mechanism is worth keeping.** Phase B's first run
compared the proposed architecture against PROCESS as shipped. Phase A's own design documentation
says that arrangement **"is a reference, not a competitor"**, and Phase A accordingly built a
control arm rather than comparing against it. The reason is that the two stop on different tests,
so their ratio contains both terms — and Phase A had already measured the stopping-rule term at
−3.4 % to +8.6 %, against a Phase B result of +2.0 %. **A study can carry the right warning in one
phase's design notes and violate it in the next phase's**, and what caught it was reading the two
phases against each other rather than any check inside either.

**A general lesson, which is the same shape as §6.1's.** Both of this study's reversals are the
same error: a comparison that varies two things and reports the answer as if it varied one. In
Phase A the two things were cost and accuracy; in Phase B they were architecture and stopping rule.
Neither was hidden — both were written down somewhere — and neither had a check capable of noticing.
The fix in both cases was a **control that differs in exactly one thing**, and in Phase B it is now
enforced at run time: every ordered pair of arrangements run must declare what differs between them,
checked against the arrangements as built, and an undeclared difference is a refusal.

---

## 6. A second pass: criticising this experiment's own method and results

Everything in this section is a criticism of the work reported above, made after the results were
in. Where it changes what §4 or §5 should say, the change has been made there and is cross-noted.

### 6.1 The strongest objection, raised here and then answered by measurement

The blocked arrangement solves each block to τ = 1e-6 against inputs that are about to change. The
flat arrangement has no inner loop and never pays that. **The two arms are not symmetric in the
freedom they were given**, and the direction of the asymmetry is exactly the direction of the
matched-tolerance result. The exit audit shows the blocked arm ending up 10⁵ times more converged
than the control at the same nominal setting — it did more work and got more accuracy, and only
the work was counted in the ratio.

This was declared in advance, which made it honest but did not make it fair. The report's earlier
wording was that the partition costs *at most* 47 %, 40 % and 18 % more, and that the study had not
measured what it costs at a comparable inner tolerance. **The bound was doing all the work.**

**It has since been run, and the objection was correct.** Measured at matched achieved accuracy
(§4.4.2) the partition is at parity or cheaper on all three retained cases: **−4.3 %, −4.5 % and
−13.1 %**. The counter-argument this section used to offer — that the outer pass counts fall by
much less than the inner solves cost, so an inexact inner tolerance "would have to recover a very
large factor" — is refuted by measurement: it recovers all of it, because the inner solves at
τ = 1e-6 were doing work the outer test did not need.

**A reversal found by the study's own critical pass is a good outcome, and this is one.** The
published number was formally hedged and the hedge was correct. What was missing is that nobody had
measured where inside the bound the answer lay, and the answer turned out to be at the far end.
**The replacement claim is narrower than the one it replaces**: it removes the finding that the
partition costs, and it does not establish that the partition is worth anything — at its cheapest
accuracy-matched setting the blocked arm has largely stopped blocking (§4.4.2, bound 2).

**The same objection, transposed, is the reason Phase B needed a third arm.** A comparison that
varies two things at once cannot attribute its answer to either, whether the two things are cost
and accuracy or architecture and stopping rule. §7.1 says what that cost the first Phase B run.

### 6.2 The winning arm's number is not one number

§4.4.3 quotes 6.56 / 6.76 / 6.64 / 2.63 % from PROCESS's own driver and −6.38 / −6.55 / −13.70 /
−5.71 % from the replay engine's flat control. These are close on two decks, far apart on two, and
they are **not the same measurement**:

- **Different populations.** The driver figure is over a whole optimisation run — 2 029, 4 286,
  1 891 and 29 sweeps. The engine figure is over the recorded design points, which keep every point
  the optimiser visited and one in five perturbations.
- **Different model sets on one deck.** On `large_tokamak_eval` the engine hoists two models where
  the driver hoists one, because the engine has no figure-of-merit guard and the driver needs one.
  The two numbers on that deck are for two different architectures, and the report says so at the
  point of quoting them.
- **Different accounting.** The engine's headline totals count in-loop models only, recording the
  post-loop tail run separately; §4.4.3 adds it back explicitly rather than quoting the loop-only
  −9.52 %.

The version to quote is the driver's, because it is what a user would get, and because it is gated
on bit-identity of the whole output file. That is what §4.4.3 leads with, and the engine figures
are presented as a cross-check with the accounting stated.

### 6.3 Things this method cannot see, and one it nearly missed

**The recording could have been wrong in a way every arrangement inherited.** All four
arrangements replay the same recorded states through the same restore path. A defect there would
move every arm together and cancel in the ratios. What guards it: the reference arrangement
reproduces the live loop's pass count on 600 of 600 points, and the restore is checked field by
field across all 2 288 fields on every restore. That is a strong guard, but it guards against
*divergence from the live loop*, not against a systematic bias shared by all arms.

**An excluded quantity that genuinely couples would be invisible — and this is the one place the
report got a fact wrong.** Quantities that never varied across the recording were excluded from
the stopping test. If one of them genuinely coupled, every arrangement would declare a convergence
that had not happened, with no symptom. The guard was that an excluded quantity is asserted at
runtime to stay constant.

This report previously stated that across all 600 design points, all four arrangements and both
hoist settings exactly **one** constant moved. **Three did**, read directly out of the recorded
artifacts and verified independently:

| Test case | constants that moved | occurrences | design points affected, per arm |
|---|---|---|---|
| `large_tokamak_nof` | none | 0 | 0 of 149 |
| `low_aspect_ratio_DEMO` | none | 0 | 0 of 297 |
| `st_regression` | `ccfe_hcpb.x_shield` | 3 | 1 of 144 |
| **`large_tokamak_eval`** | **`physics.vs_plasma_burn_required`, `physics.vs_plasma_total_required`** | **21 each** | **7 of 10** |

**On `large_tokamak_eval` the two missed movers blocked convergence and inflated that deck's
counts by 14–28 %**, which includes the +27.3 % and −10.7 % §6.5 called two of the report's largest
percentages. The failure mode is the mirror image of the one this bullet feared: a quantity that is
not really constant produces a *false non-convergence*, not a false convergence, because a
bit-identity assertion is far stricter than the scaled tolerance the same quantity would get if it
were included. It is an independent second reason to drop that deck (D17), and it does not touch
the three retained cases.

**The exclusion is now gone entirely.** Every float-valued component is tested whether or not it
varied, with a recorded scale floor of 1.0 where no working magnitude could be measured, and the
exclusion list is empty. On the three retained cases this changes **no count at all**, at any of
three floors a decade apart, and invalidates **0 of 590** design points — so the fix costs nothing
measured and closes a class of silent failure. That result is itself the answer to "what if an
excluded quantity mattered here": on these cases, none did.

**The confound that was nearly missed.** Grouping the models by block also transposed two adjacent
models, and the flat-to-blocked comparison therefore varied two things. Nobody named it while the
comparison was built or measured; it was found afterwards by cross-reading two pieces of work
against each other, and closed by a dedicated replay (§4.4.4). **The lesson is not that the null
came out clean.** It is that a headline comparison ran, and was written up, with an unnamed
confound in it, and that what caught it was an unrelated task's diff rather than any check the
design contained.

**A methodological point that outlasts the result, and it has now failed twice.** The licence to
reuse one task's recording in another's replay was first argued from the git tree being unchanged.
That argument stopped working the moment two later tasks touched the driver. It was then replaced
by a two-part argument — the sub-trees that determine model behaviour are hash-identical to the
recording commit, **and** the driver is entered zero times during a replay — and **the first half
stopped being true as well**, because a later task changed `process/models/pulse.py` and
`process/data_structure/numerics.py` (inert by default, and gated, but changed).

**The replacement is empirical and is stronger than either provenance argument.** Every arm is
re-run at the recording's own settings and compared against the recorded artifacts **bit for bit,
with no tolerance anywhere** — pass counts, model-evaluation counts, module sweeps, the converged
flag, the cap hit, the inner-solve counts per block, the full residual trace at every pass, the
named moved constants and every field of the exit audit, floats compared as exact `repr`:
**0 differing of 4 800 arm records over 64 800 record keys**, both hoist settings, four decks, with
the comparison shown capable of catching a 1-ULP move **32 times out of 32**. It failed once
first — on 600 of 600 design points, over a change in the recorded artifact's *shape* that moved no
count — and was fixed rather than absorbed.

The lesson is not that the argument was wrong each time; it is that **a licence argued from
provenance decays silently, and one argued from measurement does not.** A reproduction has to be
re-taken whenever `process/` moves; a hash argument merely stops being checked.

### 6.4 Where re-deriving the numbers changed the wording

Every figure in §4 was recomputed from the recorded artifacts rather than transcribed. Five
places where that changed something — three substantive, then two of wording:

1. **The hoist's `−9.5 %` in the replay engine is a loop-only figure.** The engine records the
   post-loop tail runs in a separate field and its headline model-evaluation total omits them. Net
   of the tail, the flat control's saving is −6.38 / −6.55 / −13.70 / −5.71 %, which is what §4.4.3
   reports and what makes it commensurable with the driver-side 6.56 / 6.76 / 6.64 / 2.63 %. The
   earlier task report's `−9.5 %` is arithmetically right for what it counts; it is the accounting
   that needed stating.
2. **"All four arrangements show an exit residual of 8.11 × 10⁸" on hoisted `st_regression` is
   right about the failure and loose about the number.** All four do fail the audit on the same 7
   of 144 points. Three of them sit at 8.11 × 10⁸; the blocked arrangement sits at 2.76 × 10⁷.
   §4.5(c) states both.
3. **A summary and its report disagreed on one denominator.** One completion summary reported
   replay fidelity as 1 800/1 800 where the report said 600/600, 600 being the total design-point
   count across the four cases. The 1 800 is most likely cumulative across three pipeline runs, but
   the two were never reconciled. This report uses **600/600**, which is what the recorded
   artifacts support: 149 + 297 + 144 + 10, checked directly.

Two further wording corrections from the same re-derivation:

- The tolerance ladder's cost of tightening from 1e-6 to 1e-8 is **26 %, 20 % and 19 %** on the
  three optimisation cases, not the "19–26 %" band an earlier report gave without saying which deck
  was which. Per-deck figures are in §4.3.
- **"The block arm's outer count falls on 43 and 115 design points and rises on none"** is measured
  against **arm R**, today's loop — not against the flat control — in a passage otherwise about the
  flat-to-blocked comparison. Against the flat control the counts are **36 of 149 and 100 of 297**
  (and 120 of 144 and 1 of 10 on the other two decks). Both are true; only the second belongs in a
  sentence about `A0 → A1`, and §4.4.2 uses that one. Against arm R the "rises on none" also fails
  on two decks — `st_regression` rises on 7 of 144 and `large_tokamak_eval` on 5 of 10 — whereas
  against the flat control it holds on all four.

### 6.5 What would most improve this study, in order — and what has since been done

The five items this section carried are now four done and one open. They are kept with their
outcomes rather than deleted, because what a critical pass asked for and what measurement then
said are both part of the record.

1. ~~**Run the blocked arrangement at a loose inner tolerance.**~~ **Done, and it overturned the
   headline** (§4.4.2, §6.1). It was the one change identified as able to do so, and it did.
2. **Find an exact per-model cost unit.** **Still open**, and everything in §5.2 is downstream of
   not having one. Nothing in either phase provides it: model evaluations are exact but do not
   track work, and the only weighting available is a timing this project has retired as evidence.
3. ~~**Enlarge `large_tokamak_eval`'s recording, or drop the deck.**~~ **Dropped** (D17), on the
   grounds that it runs 0 solver iterations and so cannot inform a study about an optimiser
   reacting to an arrangement, that its inequality constraints are never enforced, and that its
   coupling-state classification rested on ten design points. §6.3 then found a second, independent
   reason: two of its apparent constants are not constant, and the bit-identity assertion on them
   was inflating its counts by 14–28 %.
4. ~~**Give the replay engine's hoist the same figure-of-merit guard the driver has.**~~ **Replaced
   by something better.** Both guards are gone; the hoist is now a **routing rule** derived from
   the driver's own measured predicate read set, with three slots — in the loop, once before the
   objective and constraints are evaluated, once after. That generalises the guard rather than
   copying it: a node whose output the predicate layer reads leaves the sweep *and* is never stale.
   The disagreement between the two instruments was only ever on the deck that has since been
   dropped, and that should be said plainly: it stopped binding because a deck was dropped, not
   because the rule fixed it. The rule is what handles the next deck with a cost-based objective.
5. ~~**Route the findings that are about PROCESS rather than about architecture to the
   code-analysis study.**~~ **Done**, as five defects rather than the four this list named. The
   fifth is two loop bounds in `init.py` that are not the constraint count. That hand-off also
   corrected two of *our* records: the "10¹⁸ times tighter" figure is a property of **our**
   median-scaled predicate and not of upstream's, whose tolerance at the same point is *looser*
   than ours by 5.3 × 10¹⁸; and a NaN cannot reach the stopping test through the constraint vector,
   because `constraints.py` raises first.

**A sixth, added by Phase B and larger than any of them: measure the stopping rule and the
architecture separately.** Phase B's first run compared the proposed architecture directly against
PROCESS as shipped, which measures both at once, and the stopping-rule term is not small enough to
ignore. §7.1 is what that cost and what it took to fix.

### 6.6 A second pass over Phase B's own results

Everything above criticises Phase A. Phase B needs the same treatment, and four of its results do
not survive it intact.

**1. The headline rests on two test cases, and one of them is the one with the weakest instrument.**
`large_tokamak_nof` gives −1.63 % on 20 of 22 starts with a tight interquartile range, and
`st_regression` gives −6.18 % on 20 of 20 — but on `st_regression` **24 % of all optimiser
evaluations have a quantity the recording called constant moving inside them**, against 19 % in the
other arrangement (§7.11). The stopping test is not doing the same thing in the two arms there. The
`st_regression` figure should be read as provisional until the run is repeated on the
no-exclusion predicate, and the cleaner of the two headlines is the smaller one.

**2. The third test case is not merely inconclusive; it is inconclusive for a reason that would
also have made a positive result untrustworthy.** `low_aspect_ratio_DEMO` keeps 8 of 25 starts,
its ratios span 0.24 to 3.32, and most of its apparent −21 % is the lifted arrangements taking 13
optimiser iterations where the others take 16. A different search is not a cheaper loop. Had that
deck come out cleanly negative or cleanly positive, the same objection would apply, and it is worth
saying that the inconclusive verdict is not the weak case of a result — it is the honest one.

**3. The robustness criterion the plan declared in advance does not quite fit what happened.** It
reads *"variant's success rate worse ⇒ H5 fails, regardless of cost"*, and the earlier Phase B run
strengthened it in prose to *"the variant never solves a start the baseline cannot"*. The variant
now **does** solve a start the control cannot, on `st_regression`, while losing two others. A
criterion phrased as a rate handles that; a criterion phrased as domination does not. The rate is
what is applied, and the domination sentence is withdrawn rather than reinterpreted.

**4. A comparison at matched achieved accuracy is not available for robustness on one test case,
and that is a structural limit rather than a missing run.** On `large_tokamak_nof` the block
arrangement's loosest measured setting is four orders tighter than the flat one's. Solving each
block to *its own* fixed point produces a tight state whatever tolerance is asked for, so there is
no setting at which the two arrangements can be asked an equally easy question. Any future
comparison on that test case inherits this.

**And one thing that did survive, worth saying because it was checked rather than assumed.** The
node transposition that grouping into blocks brings with it costs **exactly nothing** in PROCESS's
own driver — identical counts to the last model evaluation on all three test cases (§7.4) — which
is the same null Phase A measured over 2 400 arm records in the replay engine. Two instruments,
two populations, the same zero.

### 6.7 What would most improve the study now, in order

1. **Re-run Phase B on the no-exclusion predicate.** It is the largest single limitation of the
   Phase B numbers, the fix is already built and gated, and Phase A measured it as changing no
   count at three scale floors a decade apart. `st_regression`'s figure most needs it.
2. **A matched-accuracy robustness comparison where one is possible.** Cost is compared at matched
   achieved accuracy and robustness is not; §7.9 measures the direction of the resulting bias but
   does not remove it.
3. **A thicker matched-accuracy ladder for Phase B.** Two starts per rung is not a distribution,
   and on one test case it yields no curve at all.
4. **An exact per-model cost unit.** Still open, still the thing everything in §5.2 is downstream
   of, and neither phase provides it.
5. **A partition drawn differently.** The study measured one partition, from one dependency
   analysis. Its own §5.3 mechanism argument says the blocks are not lopsided enough for the saving
   to be large, and that is a statement about *this* partition.

---

## 7. Phase B — the same question with the optimiser present

Phase A removed the optimiser deliberately, which is what made its numbers exact. The price is that
it cannot answer the question an adoption decision turns on: **what does the arrangement cost in a
whole optimisation, where the optimiser reacts to it?** Phase B is that measurement. Every run in
this section is a complete optimisation in PROCESS's own driver, from a starting design vector to a
converged plant design.

### 7.1 Why it takes three arrangements and not two

Phase B was first run with two: PROCESS as shipped against the proposed architecture. That
comparison cannot attribute its own answer, and the reason is the same shape as §6.1's.

**The two arrangements stop on different tests.** PROCESS's loop stops when the objective and the
constraint vector agree between passes under `np.allclose`, with that function's hidden absolute
tolerance and its `equal_nan=True`. The proposed architecture stops when about 840 measured state
components agree at a tolerance. So a ratio between them is **architecture plus stopping rule,
summed** — and the stopping-rule term is not small: Phase A measured it at −3.4 % to +8.6 %,
against a first Phase B result of +2.0 %. It can dominate the answer and it can flip its sign.

Phase A knew this. Its own design documentation says that PROCESS's loop **"is a reference, not a
competitor"**, and Phase A accordingly never compared against it — it built a control arrangement,
A0, for exactly this purpose. The first Phase B run compared against the reference directly, which
is the mistake Phase A's own design warns about.

**And it had already contaminated a published verdict.** All 13 starting points that first run's
variant refused were refusals of non-finite intermediate state — a property of the *stopping rule*,
which examines state the global loop never looks at — reported as a property of the architecture,
with no control that could have told the two apart. §7.6 is the measurement that settles it.

So Phase B runs three arrangements:

| | what it is |
|---|---|
| **R** | PROCESS as it ships. Every variant point unset, the existing objective/constraint idempotence test, the existing flat loop, the frozen input deck. The relevance anchor: it is what a user actually runs |
| **A0′** | the same flat loop, stopping instead on the coupling state at τ. One block containing every in-loop model, the **upstream** node order, no hoist, no lift, the frozen deck. The predicate-matched control |
| **A1′** | the proposed architecture: per-module block solves, the burn time lifted onto the optimiser with a consistency constraint, and the feed-forward models hoisted out of the loop |

and reports three comparisons that mean three different things:

- **`A0′ → A1′` is the headline** — the architecture alone, at matched stopping rule;
- **`R → A1′`** is reported beside it as the user-facing figure, and is legitimate *only* as that;
- **`R → A0′`** is what the stopping rule costs on its own, in production.

Two further arrangements are run as diagnostics and never in a headline: **A0′ with the node
transposition** that grouping into blocks brings with it (§7.4), and **A1′ without the hoist**, so
the hoist's share is measured inside this architecture rather than quoted from Phase A's
measurement of the flat one.

**Every ordered pair of arrangements that was run carries a written declaration of exactly what
differs between them**, checked at run time against the arrangements as they were actually built.
A difference nobody declared is a refusal, not a warning; so is a declaration of a difference that
is not there. This is the direct answer to §6.3's confound, one level up: it is what stops a third
arrangement being added and quietly compared with no declaration.

### 7.2 What A0′ is, and the one thing it needed beyond a configuration

A0′ is the **degenerate single-block case** of the same block solver A1′ uses — the same predicate,
the same per-deck coupling-state artifact, the same caps, the same failure policy, one block
containing every in-loop model. It is a schedule branch, not a second solver, and that matters:
two implementations of one predicate is how they drift.

It needed one correction beyond a configuration, and it is worth stating because it is a real
property of the block schedule rather than an implementation detail. **With one block covering
every in-loop model, the outer test is redundant with the block's own inner test.** The inner test
compares two successive full sweeps over the whole coupling vector; the outer test asks the same
question of the same index set. But the outer loop compares against the state at *entry*, so it
always fails on the first pass and always succeeds on the second — buying exactly one extra full
sweep per optimiser evaluation, for no information. The guard skips it, and it fires on a condition
evaluated from the schedule that was actually built rather than from the arrangement's name, so a
schedule that stops being a single block stops taking the guard. Every run records whether it
fired.

### 7.2a Three things that would otherwise be assumed, stated because they are checked

**The lifted input deck differs from the frozen one in exactly three ways.** The frozen decks are
never edited (a scenario must not change under a result); a derived copy is written into the run
directory and carries its provenance in a header comment and a JSON sidecar. The three lines are:
the burn time becomes design variable 178; its consistency residual becomes equality constraint 93,
inserted **inside the deck's equality block** and with the equality count raised in the same edit;
and the design variable's initial value is set. Nothing else changes.

That third line is the one that needs a rule, and **the rule is measured, not chosen: the initial
value is the burn time the baseline's own idempotence loop settles on at this deck's own starting
design vector.** That is the state the baseline arm itself enters its first optimiser iteration
from, and it is the value at which the lifted arrangement's consistency residual at entry is
**exactly 0.0** on both pulsed test cases. So the two arrangements start from the same design
point, and the lifted one starts on its own consistency manifold. It closes the objection that the
variant was handed a better starting guess. One sweep would *not* have done: the first sweep
computes the burn time from an entry loop voltage that has not settled and gives 9.7 × 10⁵ s on
`large_tokamak_nof` against a settled 2 568 s. Both numbers are recorded in the sidecar so the
choice between them is visible.

The equality-block placement is not pedantry. **PROCESS decides which constraints are equalities by
their position in the deck's constraint list**, not from the constraints themselves. A derived deck
that appends the consistency constraint at the end makes it the twenty-fourth *inequality*, and
that variant returns success, a plausible objective, and looks **38 % cheaper** — because nothing
forces the burn time onto its manifold at all. That is a real defect this study met, and it is why
the gate checks membership of the equality block directly rather than checking the residual alone.

**The starting points are genuinely paired.** Each perturbation factor is `1 + δ·(2u−1)` with `u`
drawn from a hash of *(seed, iteration-variable number)* — keyed on the **variable's number, not
its position in the design vector**. The lifted arrangement's design vector is one longer, so a
position-keyed perturbation would give the two arrangements different factors for the same physical
variable and the pairing would be fictitious. Keyed on the number, **every design variable the two
arrangements share takes an identical factor**, and the whole set is reproducible from the seed
alone. Perturbed starts are clamped into the deck's own scaled bounds — a start outside its own box
is a different problem, not a start — and the clamp is counted per variable per start.

**The extra design variable is part of the intervention, not a confound.** Lifting the burn time
buys its decoupling *by* enlarging the design vector: the arrangement cannot have the one without
the other. PROCESS takes central differences, so a gradient costs `2n` solves of the model loop and
one more variable is `1/n` more work — about 5 % on these decks. **That cost is charged to the
architecture**, and the cost unit does charge it: every finite-difference evaluation goes through
the same `call_models` path as every other, and nothing in the accounting excludes them. The
arithmetic is visible in the counts — on `large_tokamak_nof` the lifted arrangement makes 660
optimiser evaluations against 630, a ratio of 1.048 against the dimension ratio 21/20 = 1.05. A
comparison that quietly excluded the extra gradient work would be measuring an architecture nobody
can run.

### 7.3 The gates, and the stop rule

**If the equivalence gate fails, the multi-start campaign is not run.** That is not a formality: if
the arrangements do not reach the same optimum, a cost comparison between them compares two
different problems. Nothing was tuned, retried at another setting, or narrowed to make a gate pass.

Four gates, in the order they were run, each shown capable of failing before its zeros were
accepted.

**(i) Switch neutrality.** The three arrangements are selected by environment variables, and the
code that reads them sits on the path every run takes — including a run with every switch off. So
"off means upstream" is a claim about this tree and is gated rather than asserted: every number in
the output file, on every test case, against an unmodified checkout of the base commit.

| | `large_tokamak_nof` | `low_aspect_ratio_DEMO` | `st_regression` |
|---|---|---|---|
| output lines differing / compared | **0** / 16 174 | **0** / 16 435 | **0** / 18 692 |
| output floats differing / compared, as hex | **0** / 13 559 | **0** / 13 455 | **0** / 13 493 |
| total quantities compared | 29 760 | 29 916 | 32 206 |
| `ifail`, sweeps, solver iterations | unchanged | unchanged | unchanged |

**0 of 91 882 quantities differ**, per mode, with the instrumentation hook off *and* on — 183 764
in total. Its teeth: one unit in the last place of the major radius is caught on 3 of 3 test cases
as exactly one differing line and one differing float; one ULP of the objective and one of the
constraint residual norm flip the acceptance predicate on 3 of 3; a changed `ifail` on 3 of 3; and
two genuinely different test cases differ in **11 606 of 13 441** shared floats.

**(ii) What each comparison declares it varies.** Every ordered pair of arrangements run is
declared from a closed vocabulary and checked against a flat descriptor of everything a comparison
could be varying — node sequence, block schedule and its shape, stopping test, sweep floor,
tolerances, hoist and lift settings, both hoisted groups, loop node set, coupling-state
specification and its hash, and all three caps — read from what each run **resolved**, never from
what the driver asked for. **10 of 10 ordered pairs declared and checked on each of the three test
cases, 0 undeclared, 0 skipped.** Its teeth: an undeclared difference is refused, an over-declared
manifest is refused, and an arm pair with no declaration at all is refused — 3 of 3.

*This gate did real work rather than confirming an intention.* Its first run **refused
`R → A0′`**, because the descriptor recorded the two arrangements' single blocks under different
labels and reported a structural difference where there was none. The fix was to the descriptor,
not to the declaration: a one-block schedule's label carries no information, and encoding a naming
choice as a structural difference makes the descriptor lie about what the arrangements differ in.

**(iii) Do the arrangements run the same models, and does the cost unit count what it claims?** A
block schedule that fails to name a model does not fail — it silently stops running it, because the
node filter is a predicate on names. The model call sites are read out of the driver's own source
and checked against what each arrangement resolved: **26 call sites, all covered, on 15 of 15 arm
records.** The cost unit is checked the same way rather than asserted, by counting model calls per
name from the harness side: the per-name counts must equal the reported total plus the audit
sweep's own calls, and **nothing may have been run through the flat hoisted tail**, which does not
increment the counter. **0 uncounted tail calls on 15 of 15 records.**

*This gate found a defect in its own harness before it passed, which is the fifth consecutive task
in this project where the requirement to show a gate capable of failing has done so — in every
case while the gate was already passing.* The call-site extraction matched only plain assignments,
and the driver's node-order table is an *annotated* assignment, so the three head models —
`plasma_geom`, `build`, `physics` — were **not in the call-site set at all**. A set that does not
contain a model cannot notice the model missing, and the coverage figure was over 23 call sites
rather than 26. Found by the sensitivity check removing a model from a schedule and watching the
gate go on passing. The check now refuses to report a coverage figure at all if the table does not
parse, and exercises a head model by name.

**(iv) The equivalence gate.** Not bit identity: A1′ solves a problem with one more design variable
and one more equality constraint on the two pulsed test cases, so the question is whether the
arrangements land on the same optimum. Five checks per arrangement per test case — the solver's own
success flag; the objective to **1e-6 relative**, which is PROCESS's own idempotence tolerance and
Phase A's first rung and is therefore not a number chosen here; a post-solve feasibility audit on
the returned point; the achieved final accuracy reported rather than assumed equal; and, for the
lifted arrangement, the burn-time consistency residual **and** that its constraint sits inside the
input deck's equality block.

| test case | arrangement | verdict | objective, relative difference | margin to the tolerance | inequalities violated, R / arm | consistency residual |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | A0′ | **PASS** | 4.16e-16 | 2.4 × 10⁹ | 0 / 0 | — |
| | A1′ | **PASS** | 7.98e-11 | 1.25 × 10⁴ | 0 / 0 | 1.19e-08 |
| | A0′ reordered | **PASS** | 4.16e-16 | 2.4 × 10⁹ | 0 / 0 | — |
| | A1′ without the hoist | **PASS** | 7.98e-11 | 1.25 × 10⁴ | 0 / 0 | 1.19e-08 |
| `low_aspect_ratio_DEMO` | A0′ | **PASS** | 5.06e-15 | 2.0 × 10⁸ | 0 / 0 | — |
| | A1′ | **PASS** | **6.85e-07** | **1.46** | 0 / 0 | 1.63e-10 |
| | A0′ reordered | **PASS** | 5.06e-15 | 2.0 × 10⁸ | 0 / 0 | — |
| | A1′ without the hoist | **PASS** | 6.85e-07 | 1.46 | 0 / 0 | 1.63e-10 |
| `st_regression` | A0′ | **PASS** | 3.83e-14 | 2.6 × 10⁷ | 0 / 0 | — |
| | A1′ | **PASS** | 5.03e-14 | 2.0 × 10⁷ | 0 / 0 | — |
| | A0′ reordered | **PASS** | 3.83e-14 | 2.6 × 10⁷ | 0 / 0 | — |
| | A1′ without the hoist | **PASS** | 5.10e-14 | 2.0 × 10⁷ | 0 / 0 | — |

**PASS on 12 of 12 arrangement gates.** Three things must be read with it.

1. **`low_aspect_ratio_DEMO`'s lifted arrangement passes with a margin of 1.46, not 10⁴.** Its
   objective differs by 6.85 × 10⁻⁷ against a 1 × 10⁻⁶ gate — a pass, and the closest thing in
   Phase B to a near miss. A tolerance one third tighter would have failed it. The tolerance was
   fixed from PROCESS's own before the run and is not adjusted after.
2. **A dash in the last column is a test case that names no consistency constraint, not a silent
   pass.** `st_regression` has `i_pulsed_plant = 0` and an empty measured `PULSE` write set: there
   is no burn time to lift. It is the `k = 0` control.
3. **The gate is shown capable of failing on every arrangement, not just one.** Eight deliberately
   corrupted inputs per arrangement, through the production predicates unmodified: **28 of 28 that
   must fail, do.** Four more are reported **NOT APPLICABLE rather than counted either way** — the
   two consistency-residual perturbations watch a quantity that does not exist on an arrangement
   without the lift, so mutating it changes nothing and the gate correctly still passes. Counting
   those as passes would be exactly the vacuous-gate failure mode this study has met before.

**And the unit tests.** `tests/unit`: **843 passed, 4 skipped**, the same as the two tasks that
built this variant's scaffolding.

### 7.4 What the arrangements cost at each test case's own starting point

One run per cell, before any distribution: the deck's own unperturbed design vector.

| test case | arrangement | net model evaluations | sweeps | optimiser iterations | design variables |
|---|---|---|---|---|---|
| `large_tokamak_nof` | R | 42 567 | 2 030 | 8 | 20 |
| | A0′ | 43 449 | 2 072 | 8 | 20 |
| | A0′ reordered | **43 449** | **2 072** | 8 | 20 |
| | A1′ without the hoist | 44 734 | 9 437 | 8 | 21 |
| | A1′ | 42 772 | 7 469 | 8 | 21 |
| `low_aspect_ratio_DEMO` | R | 89 964 | 4 287 | 16 | 19 |
| | A0′ | 86 877 | 4 140 | 16 | 19 |
| | A0′ reordered | **86 877** | **4 140** | 16 | 19 |
| | A1′ without the hoist | 72 064 | 15 014 | 13 | 20 |
| | A1′ | 68 947 | 11 886 | 13 | 20 |
| `st_regression` | R | 39 669 | 1 892 | 10 | 14 |
| | A0′ | 42 756 | 2 039 | 10 | 14 |
| | A0′ reordered | **42 756** | **2 039** | 10 | 14 |
| | A1′ without the hoist | 40 725 | 8 620 | 10 | 14 |
| | A1′ | 37 312 | 7 513 | 10 | 14 |

| test case | `R → A0′` (stopping rule) | `A0′ → A1′` (architecture) | `R → A1′` (user-facing) |
|---|---|---|---|
| `large_tokamak_nof` | +2.07 % | **−1.56 %** | +0.48 % |
| `low_aspect_ratio_DEMO` | −3.43 % | **−20.64 %** | −23.36 % |
| `st_regression` | +7.78 % | **−12.73 %** | −5.94 % |

**The node transposition costs exactly nothing, measured rather than argued.** A0′ and A0′-reordered
differ in one thing — whether `build` runs before or after `physics` — and produce **identical**
counts on all three test cases, to the last model evaluation. Grouping the models into blocks brings
that transposition with it, so `A0′ → A1′` varies the grouping *and* the order; this measures the
order term at zero in PROCESS's own driver, as §4.4.4 measured it at zero in the replay engine over
2 400 arm records. The grouping is what `A0′ → A1′` is measuring.

**The sweep counts are not a cost and are shown to make that concrete.** A1′ runs 7 469 block
sweeps on `large_tokamak_nof` against R's 2 030, and costs slightly *less*. A block sweep runs one
module, not all of them; quoting sweeps would say the architecture is 3.7 times more expensive,
which is a units error and not a measurement.

**One number in that table is not architecture and must not be read as such.** On
`low_aspect_ratio_DEMO` the lifted arrangements take **13** optimiser iterations where R and A0′
take 16. Most of that deck's −20.6 % is a shorter search, not a cheaper loop. Iteration counts are
not comparable between arrangements of different dimension and are diagnostics only; §7.7
decomposes it.

### 7.5 The perturbation size, calibrated on the reference arrangement alone

How far to perturb a starting design vector must not be chosen after seeing a result. It is
measured on PROCESS as shipped, at 1 %, 5 % and 10 %, twelve starts each — 108 runs — and the
largest size that still solves most starts is taken. The whole table, not just the choice:

| test case | δ = 1 % | δ = 5 % | δ = 10 % | choice |
|---|---|---|---|---|
| `large_tokamak_nof` | 12 / 12 | 12 / 12 | **11 / 12** (1 crashed) | **10 %** |
| `low_aspect_ratio_DEMO` | 12 / 12 | 9 / 12 (3 fail to converge) | **7 / 12** (4 fail, 1 crashed) | **10 %** |
| `st_regression` | 12 / 12 | 11 / 12 (1 fails) | **12 / 12** | **10 %** |

**δ = 10 % on every test case**, so one perturbation size runs them all and the three campaigns are
comparable in it. Two things in that table are worth stating rather than smoothing.
`low_aspect_ratio_DEMO` is the fragile case, and it is fragile **in the reference arrangement**: at
10 % the incumbent solves 7 of 12. That is the floor everything else is measured against there, and
it is a property of the deck and PROCESS's own solver. And `st_regression` is not monotone in δ —
12, 11, 12 — because multi-start success is a property of a landscape and not a smooth function of
perturbation size; reading a trend into three points would be reading noise.

*This reproduces the earlier Phase B run's calibration exactly, on every cell of the table. The
reference arrangement is bit-identical to the one that run used, which the switch-neutrality gate
establishes, so the reproduction is a check on the harness rather than new evidence.*

### 7.6 Robustness first, because robustness outranks cost

25 starting points per arrangement per test case, the same ones for every arrangement — 300
complete optimisations. Which starts each arrangement solves, paired:

| test case | comparison | both | only the reference | only the other | neither | offered |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | R → A0′ | 22 | 0 | 0 | 3 | 25 |
| | **A0′ → A1′** | **22** | **0** | **0** | 3 | 25 |
| | R → A1′ | 22 | 0 | 0 | 3 | 25 |
| `low_aspect_ratio_DEMO` | R → A0′ | 12 | **0** | 0 | 13 | 25 |
| | **A0′ → A1′** | **11** | **1** | **0** | 13 | 25 |
| | R → A1′ | 11 | 1 | 0 | 13 | 25 |
| `st_regression` | R → A0′ | 23 | **1** | 0 | 1 | 25 |
| | **A0′ → A1′** | **21** | **2** | **1** | 1 | 25 |
| | R → A1′ | 22 | 2 | 0 | 1 | 25 |

**On `large_tokamak_nof` the three arrangements have identical success sets**: the same 22 starts,
and the same 3 failures, which are the same model-level failure in every arm — a root-find inside a
superconducting-coil model reporting `Failed to converge after 50 iterations, value is nan`. Not a
driver failure, and not caused by anything this study built.

**On `st_regression` the proposed architecture solves one start the control cannot** — the first
time in this study that the variant is not strictly dominated on robustness. It also loses two, so
the net is −1.

**And the deficit is now attributable, which is the whole reason for the third arrangement.**

### 7.7 The refused starts, re-attributed: predicate or architecture?

The earlier Phase B run reported that its variant refused 13 starts, all of them refusals of
non-finite intermediate state, and read that as a property of the architecture. There was no
control that could tell architecture from stopping rule. There is now.

| test case | arrangement | starts not solved | of | refusals by the coupling-state test | quantity named |
|---|---|---|---|---|---|
| `large_tokamak_nof` | R | 3 | 25 | 0 | — |
| | A0′ | 3 | 25 | **0** | — |
| | A1′ | 3 | 25 | **0** | — |
| `low_aspect_ratio_DEMO` | R | 2 | 25 | 0 | — |
| | A0′ | 4 | 25 | **2** | `current_drive.eta_cd_dimensionless_hcd_primary` |
| | A1′ | 5 | 25 | **3** | the same quantity |
| `st_regression` | R | 0 | 25 | 0 | — |
| | A0′ | 0 | 25 | 0 | — |
| | A1′ | 0 | 25 | 0 | — |

**The answer is: mostly the predicate.** On the one test case where the coupling-state test refuses
anything at all, the **flat control refuses two of the three**. The control shares the architecture
of PROCESS as shipped — one flat loop over every model — and differs from it only in what it stops
on. So two thirds of the refusals are the stopping rule declining to call a non-finite state
converged, and one is the architecture examining intermediate module state that a flat sweep
overwrites before anything looks at it.

It is the **same quantity** the earlier run named — `current_drive.eta_cd_dimensionless_hcd_primary`,
which goes `0.0 → NaN` — so this is a re-attribution of that finding rather than a different one.
And the reference arrangement refuses none of them, because its stopping test is
`np.allclose(..., equal_nan=True)`, which calls a state that has gone non-finite **idempotent with
itself**. That behaviour is deliberate here: the reference is PROCESS as shipped and repairing it
would flatter the comparison. It is filed as a defect against PROCESS and is not endorsed.

**What this does to the earlier verdict.** That verdict — *"the variant never solves a start the
baseline cannot, and robustness outranks cost, so H5 fails"* — rested on a robustness deficit
attributed to the architecture. Two thirds of the measured deficit is not the architecture, and on
one test case the variant now solves a start the control cannot. The verdict does not survive
unchanged; §8 states what replaces it.

### 7.8 Cost, over the kept starts only

The drop census comes before any ratio. A start leaves the comparison only through this table.

| test case | comparison | kept | crashed | did not converge | objective mismatch | offered |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | all | 22 | 3 | 0 | 0 | 25 |
| `low_aspect_ratio_DEMO` | R → A0′ | 12 | 4 | 9 | 0 | 25 |
| | A0′ → A1′ | **8** | 5 | 9 | 3 | 25 |
| `st_regression` | R → A0′ | 22 | 0 | 2 | 1 | 25 |
| | A0′ → A1′ | 20 | 0 | 4 | 1 | 25 |

Paired ratio of net model evaluations, per start, per test case, never pooled:

| test case | comparison | n | min | q1 | **median** | q3 | max | cheaper / dearer |
|---|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | R → A0′ *(stopping rule)* | 22 | 1.015 | 1.019 | **1.021 (+2.13 %)** | 1.025 | 1.060 | 0 / 22 |
| | **A0′ → A1′** *(architecture)* | 22 | 0.848 | 0.982 | **0.984 (−1.63 %)** | 0.985 | 1.138 | **20 / 2** |
| | R → A1′ *(user-facing)* | 22 | 0.871 | 1.003 | **1.005 (+0.48 %)** | 1.007 | 1.155 | 3 / 19 |
| `low_aspect_ratio_DEMO` | R → A0′ | 12 | 0.965 | 0.966 | **0.966 (−3.38 %)** | 0.968 | 0.980 | 12 / 0 |
| | **A0′ → A1′** | **8** | **0.241** | 0.603 | **0.788 (−21.2 %)** | 1.001 | **3.320** | 6 / 2 |
| | R → A1′ | 8 | 0.233 | 0.582 | **0.761 (−23.9 %)** | 0.968 | 3.213 | 6 / 2 |
| `st_regression` | R → A0′ | 22 | 0.999 | 1.008 | **1.032 (+3.23 %)** | 1.079 | 2.346 | 1 / 21 |
| | **A0′ → A1′** | 20 | 0.160 | 0.881 | **0.938 (−6.18 %)** | 0.948 | 0.961 | **20 / 0** |
| | R → A1′ | 20 | 0.239 | 0.941 | **0.949 (−5.06 %)** | 0.958 | 0.990 | **20 / 0** |

**`low_aspect_ratio_DEMO` is inconclusive and is reported as such.** A median of 0.788 over **8**
starts whose ratios run from 0.241 to 3.320 is not a result; the plan's own pre-declared outcome
table says *"distributions overlap substantially → inconclusive, reported as such — not resolved by
picking a summary statistic"*. Most of that deck's movement is not the loop at all: its lifted
arrangements take **13** optimiser iterations where the other two take 16, and the paired iteration
ratio has a median of 0.806 there. A shorter search is not a cheaper loop.

**On the other two the architecture is cheaper at matched stopping rule, and tightly.** −1.63 % on
20 of 22 starts and −6.18 % on 20 of 20, with interquartile ranges of 0.982–0.985 and 0.881–0.948.

**The stopping rule's own cost is not small and does not have one sign**: +2.13 %, −3.38 %,
+3.23 %. That is the term the earlier two-arm design folded into its answer, and it is comparable
in size to the architecture term it was folded into.

**The optimiser's own behaviour barely moves, which is the risk this phase existed to test.** The
paired ratio of optimiser iterations is exactly **1.000 at the lower quartile, the median and the
upper quartile** on `large_tokamak_nof` and `st_regression`, for every comparison. Adding a design
variable and a consistency constraint did not measurably disturb the search on those two. On
`low_aspect_ratio_DEMO` it moved **in the variant's favour**. Nothing bounded this in advance.

**The hoist's separable share, measured inside this architecture rather than quoted from the flat
one**: −4.39 %, −4.32 % and −2.95 % (22 / 22, 11 / 11 and 18 / 19 starts). So on
`large_tokamak_nof` the architecture without the hoist costs **+2.88 %**, the hoist takes 4.4
percentage points off, and the combined figure is **−1.63 %**. **The headline is therefore the
proposed architecture and never the partition's benefit**: the partition alone, on that test case,
costs more.

### 7.9 Is the robustness comparison on a level basis? A measured answer

**Cost is compared at matched achieved accuracy. Robustness is compared at a fixed tolerance.**
Those are not the same basis, and a reader should not have to derive that asymmetry from the code.
A fixed tolerance is not a fixed accuracy — that is precisely the distinction §4.4.2 shows flipping
the sign of a cost answer — so if one arrangement converges to a systematically looser final state
at τ = 1e-6, it is being asked an easier question and its success rate is not comparable.

**So it is measured, not assumed.** For every start the campaign ran, one further full sweep of the
complete model set at the return of the first optimiser evaluation, from an identical entry state
in every arrangement. Robustness is a tail property, so the whole distribution is reported:

| test case | arrangement | n | bit-exact 0 | p10 | p50 | p90 | max |
|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | R | 22 | 0 | 1.16e-08 | 5.12e-07 | 7.04e-05 | **1.47e+09** |
| | A0′ | 22 | 2 | 3.86e-10 | 6.30e-09 | 1.58e-08 | 1.88e-08 |
| | A1′ | 22 | **17** | 0 | **0** | 2.45e-16 | 4.00e-16 |
| `low_aspect_ratio_DEMO` | R | 24 | 20 | 0 | 0 | 5.31e-15 | **inf** |
| | A0′ | 22 | 20 | 0 | 0 | 0 | 5.31e-15 |
| | A1′ | 22 | 20 | 0 | 0 | 0 | 5.31e-15 |
| `st_regression` | R | 25 | 0 | 8.76e-08 | 9.30e-08 | 1.00e-07 | 1.04e-07 |
| | A0′ | 25 | 0 | 2.98e-09 | 3.17e-09 | 3.42e-09 | 3.54e-09 |
| | A1′ | 25 | 0 | 1.38e-13 | 3.52e-11 | 6.24e-11 | 7.80e-11 |

Paired, start by start:

| test case | R vs A0′ | R vs A1′ | A0′ vs A1′ |
|---|---|---|---|
| `large_tokamak_nof` | R looser on **16 of 22**, A0′ on 0 | R looser on **22 of 22**, A1′ on 0 | A0′ looser on **20 of 22**, A1′ on 0 |
| `low_aspect_ratio_DEMO` | identical on **22 of 22** | identical on **22 of 22** | identical on **22 of 22** |
| `st_regression` | R looser on **24 of 25**, A0′ on 0 | R looser on **25 of 25**, A1′ on 0 | A0′ looser on **25 of 25**, A1′ on 0 |

**The direction is one-sided and it is the opposite of the one that would flatter the variant.** At
the campaign's own setting the proposed architecture ends **strictly more converged** than the
control on 20 of 22 and 25 of 25 starts, and never less; and both end more converged than PROCESS
as shipped. So the robustness comparison is **conservative against the variant**: it is being asked
a harder question and still matches the control's success set on one test case, loses one start on
another, and loses two while gaining one on the third. On `low_aspect_ratio_DEMO` the three deliver
**identical** accuracy on every paired start, so that test case's robustness comparison is on
exactly level footing.

**Two things in that table are about PROCESS rather than about architecture.** Its own loop hands
the optimiser a state whose worst coupling residual is **1.47 × 10⁹** on one start of
`large_tokamak_nof`, and a **non-finite** one on a start of `low_aspect_ratio_DEMO` — measured at
the first optimiser evaluation, on a state its stopping test called idempotent.

**And on one test case the variant cannot be made as loose as the control at all.** On
`large_tokamak_nof` the block arm's loosest measured setting — inner tolerance 0.1, which is barely
a convergence demand — still delivers 6.8 × 10⁻¹³ against the flat arm's 1.3 × 10⁻⁸. That is
structural rather than a limit of the ladder: solving each block to *its own* fixed point produces
a tight state whatever tolerance is asked for. A matched-accuracy robustness comparison is
therefore not available on that test case, and saying so is the honest outcome.

#### 7.9.1 Where it *is* available, the verdict moves — and both readings are reported

On `st_regression` a matching setting exists: the block arrangement at outer tolerance 1e-6 and
**inner tolerance 0.01** delivers 3.28 × 10⁻⁹, which is the flat control's achieved accuracy at
τ = 1e-6 to three figures. That setting was read off the ladder **before** the re-run, not chosen
after seeing a success rate. Twenty-five starting points, the same ones, against the same
unchanged control runs:

| | both solve | only the control | only the variant | neither | success counts | cost, paired median |
|---|---|---|---|---|---|---|
| **at matched tolerance** (inner 1e-6) | 21 | **2** | 1 | 1 | 23 vs **22** | **0.938 (−6.18 %)**, n = 20 |
| **at matched achieved accuracy** (inner 0.01) | 22 | **1** | 1 | 1 | 23 vs **23** | **0.977 (−2.27 %)**, n = 19 |

**Both readings go in the report, with the tolerance each was measured at named. Neither replaces
the other.**

**At matched achieved accuracy the robustness deficit on this test case disappears and the cost
advantage shrinks.** The two arrangements solve **23 of 25 each** — not the same 23; one start each
way — and the architecture is 2.27 % cheaper rather than 6.18 %. By the outcome table declared in
advance, *"median evaluation count lower, success rate no worse"*, that is the architecture
winning on this test case at matched accuracy where at matched tolerance it failed the robustness
criterion by one start.

**Read that narrowly.** It is a **one-start** difference in each direction on a population of 25.
It says the earlier verdict on this test case was sensitive to a setting that was never chosen for
robustness purposes, not that the architecture is robustly better. And it moves the cost figure
against the architecture by 3.9 percentage points, which is the same over-solving effect §4.4.2
measures in the other direction: at the tighter inner tolerance the variant was buying accuracy
nobody asked for, and part of what looked like a saving was work the control was not doing.

**Why only this test case.** `large_tokamak_nof` has no setting at which the arrangements are
equally converged (above). `low_aspect_ratio_DEMO` needs none: the accuracy census shows all three
arrangements delivering **identical** accuracy on every paired start there, so its robustness
comparison is already on level footing. So the re-run was run where it was both possible and
informative, and that is stated rather than left to be inferred from a directory listing.

### 7.10 Timings, as context and never as evidence

Wall and processor seconds per whole optimisation, over the campaign's own starts, with the median,
the interval, the repetition count and each run's position in the sequence.

| test case | arrangement | n | CPU s median | p10–p90 | spread as % of the median |
|---|---|---|---|---|---|
| `large_tokamak_nof` | R | 22 | 20.8 | 18.4–22.7 | **21 %** |
| | A0′ | 22 | 32.4 | 28.5–34.8 | 19 % |
| | A1′ | 22 | 52.4 | 46.0–56.9 | 21 % |
| `low_aspect_ratio_DEMO` | R | 23 | 33.5 | 7.3–101.5 | **281 %** |
| | A0′ | 21 | 53.3 | 11.0–160.1 | 280 % |
| | A1′ | 20 | 75.4 | 16.4–162.2 | 193 % |
| `st_regression` | R | 25 | 34.2 | 19.5–130.1 | **323 %** |
| | A0′ | 25 | 54.4 | 38.1–346.9 | **568 %** |
| | A1′ | 25 | 96.3 | 53.9–524.1 | 488 % |

**The interval is between 19 % and 568 % of the median, against effects of 1.6 % to 6.2 %. No ratio
of two of these numbers can resolve one, and none is offered.** On two of the three test cases the
band is two orders of magnitude wider than the effect. The narrowest case, 19–21 %, is still an
order of magnitude wider.

Two further reasons not to read the medians as an arrangement comparison, either of which would
make them wrong even if the band were tight. They are at matched *tolerance*, and §7.9 measures the
proposed arrangement ending strictly more converged there. And the coupling-state arrangements
carry per-block bookkeeping the reference does not — a residual evaluation and a state snapshot per
inner sweep — which a model-evaluation count is blind to by construction, and which is exactly why
the count is the acceptance quantity and the clock is not. A production implementation of this
architecture would not do that bookkeeping the way an instrument does.

*Sequence positions are per driver invocation, and the campaign was interrupted by the run
environment at 173 of 300 and resumed. No run was re-measured — the resume skips only complete,
driver-stamped records — but the position counter restarts, so positions are comparable within a
driver invocation and not across the interruption. Recorded because the practice adopted under the
project's timing rules is that a timing carries its sequence position.*

### 7.11 What Phase B could not do on this instrument

Four things, stated as limits rather than as apologies, and the first is the largest.

**1. The coupling-state test is built from a recording taken at the unperturbed design point, and
perturbation breaks part of it.** Quantities that never varied across that recording are asserted
to stay constant, and a bit-identity assertion is far stricter than the scaled tolerance the same
quantity would get if it were tested normally. Under 10 % perturbation:

| test case | solves where a "constant" moved | of | distinct quantities |
|---|---|---|---|
| `large_tokamak_nof` | 234 (A0′) / 241 (A1′) | 13 524 / 14 080 | 89 / 65 |
| `low_aspect_ratio_DEMO` | 192 / 231 | 28 153 / 28 848 | 91 / 68 |
| `st_regression` | **13 817 / 10 528** | 57 030 / 54 480 | **180 / 147** |

**On `st_regression` a quarter of all optimiser evaluations have a quantity the recording called
constant moving inside them**, and the fraction is **not equal between the arrangements** — 24.2 %
against 19.3 %. That is the exact failure mode Phase A's method review found on the deck it
dropped, where two false constants inflated its counts by 14–28 %. It is a limitation of this
Phase B and not of the architecture, and the fix already exists: Phase A's method review replaced
exclusion-on-constancy with **testing every component at a recorded scale floor**, which changes no
Phase A count at any of three floors a decade apart. Phase B was run on the earlier artifact for
continuity with the run it replaces; **re-running it on the no-exclusion predicate is the single
most valuable thing a successor task could do**, and `st_regression`'s −6.18 % should be read with
that reservation.

**2. The matched-accuracy ladder is thin, and empty on one test case.** Two starts per rung,
restricted to the starts every rung of both arms kept: 2, 1 and — on `low_aspect_ratio_DEMO` —
**no curve at all**, because every rung's achieved residual there is exactly zero.

**3. Robustness is compared at a fixed tolerance** (§7.9). What is known about whether that is fair
is measured, and the answer is that the comparison is conservative against the variant; but it is
not a matched-accuracy comparison, and on one test case it cannot be made into one.

**4. One perturbation size, one starting-point distribution, one optimiser, three decks, one
commit.** The result does not transfer, and nothing here is a recommendation to adopt the
arrangement.

### 7.12 Issue I-12, which recurs — and an earlier reading of it was wrong

PROCESS's 1990 cost model diverges where net electric power is not positive, which makes a
median-scaled relative convergence test arbitrarily tight there. Perturbed multi-starts visit
infeasible entry states **by design**, so this was predicted to recur. Measured at the state each
optimiser evaluation was **entered** with:

| test case | arrangement | starts visiting a non-positive entry | of | non-positive entries | of | worst |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | R | **2** | 25 | 84 | 13 502 | −92.5 MW |
| | A0′ | **2** | 25 | 84 | 13 502 | −92.5 MW |
| | A1′ | **2** | 25 | 88 | 14 058 | −82.0 MW |
| `low_aspect_ratio_DEMO` | all three | **0** | 25 | 0 | ~28 500 | — |
| `st_regression` | R | **13** | 25 | 2 586 | 53 675 | −783 MW |
| | A0′ | **13** | 25 | 2 520 | 57 005 | −783 MW |
| | A1′ | **13** | 25 | 2 224 | 54 455 | −783 MW |

**It recurs, and on one test case it is not rare: 13 of 25 starting points, and 4.8 % of all
optimiser evaluations.** It is **identical across arrangements** on every test case, which is what
matters for the comparison — it inflates every arm's counts together rather than one of them.

**And it corrects an earlier reading.** The first Phase B run reported **zero** degenerate entries
in 300 runs. That measurement was taken at the point each run *returned*, which is a converged and
feasible design; the effect is at the states the loop is *entered* with along the way. Measured
where the issue says to measure it, it is present on two of three test cases. The earlier zero was
not wrong about what it measured; it measured the wrong place.

### 7.13 The envelope's asymmetry, and what is done about it — for both phases

The matched-accuracy comparison in §4.4.2 and the one in §7.8 rest on the same construction, and
that construction is not neutral between the two arrangements. **Declaring the bias is not
correcting it**, so both are computed and both are reported.

**The asymmetry.** The blocked arrangement has an inner tolerance the flat one does not have, so
more settings are tried: eleven rungs against six in Phase A, nine against five in Phase B. That
is inherent to the architecture — the flat arm has no inner loop to loosen — but it produces **two
one-sided biases, both favouring the blocked arm.**

**Bias 1, sampling.** A running minimum can only fall as draws are added, never rise. Two
arrangements with *identical* underlying cost-versus-accuracy behaviour, sampled nine times against
five, give the nine-sample arm the lower envelope from sampling alone. And the extra rungs are not
spread across the accuracy range: **every one of them sits at the calibrated outer tolerance and
varies only the inner one**, so the extra sampling is concentrated in a single narrow accuracy
band — and that band is at τ = 1e-6, the study's own calibration point, which is plausibly near
where the matched-accuracy readout lands. The advantage is concentrated exactly where it does the
most work.

**Bias 2, interpolation.** Cost is read between bracketing envelope points by a chord in
log₁₀(cost) against log₁₀(accuracy). Where the curve is **convex**, a chord lies *above* it. The
arm with fewer points has wider gaps, so more of its curve is replaced by an over-estimate, and
**fewer rungs makes the flat arm look more expensive than it is** — the same direction as bias 1.
Convexity is not assumed: it is computed per arm per test case from the actual envelope points, as
the sign of the discrete second difference at every interior point, and reported with its
denominator. Where the curve is not convex this bias does not apply and is dropped rather than
asserted.

**The fix, which needs no new runs: a matched-count envelope, reported beside the all-settings
one.** The blocked arm's *joint* rungs alone — one knob, the same tolerance values, the same number
of draws as the flat arm — against the flat arm's rungs. Both numbers, per test case, with their
denominators.

The difference between the two is a **tuning premium**: what the second knob buys, not what the
partition buys. They answer different questions and both are legitimate:

| construction | what it answers | who it is for |
|---|---|---|
| **matched-count** — five joint rungs against five flat | *what does partitioning cost at equal tuning effort?* | **the architecture question. The headline takes this number** |
| **all-settings** — nine block rungs against five flat | *what is the best I can do with each arrangement?* | a practitioner choosing between two implementations. Reported beside it and labelled as such |

**If the two disagree in sign, that is a finding to report, not to reconcile.**

**Why this is not pedantry, and it is the reason the rule is written down rather than assumed.**
This study's own matched-accuracy analysis **flipped sign once already on an
envelope-construction choice** — +21.9 % where the lower envelope gives −4.3 % on
`large_tokamak_nof` — against a final effect of about 4 %. The construction has demonstrated
leverage comparable to the quantity being measured. A reader is entitled to see both constructions
and judge, and a report that showed only the more favourable one would be choosing on the reader's
behalf.

**Phase A has the same asymmetry, and there it is not small — it changes the sign of the answer on
two of three test cases.** Its §4.4.2 figures are reported under both constructions for that reason.

| phase | test case | matched-count (architecture) | all-settings (practitioner) | tuning premium |
|---|---|---|---|---|
| **A** | `large_tokamak_nof` | **+33.4 %** | **−4.3 %** | **0.717** |
| | `low_aspect_ratio_DEMO` | **+27.4 %** | **−4.5 %** | **0.750** |
| | `st_regression` | −15.2 % | −13.1 % | 1.026 |
| **B** | `large_tokamak_nof` | −24.2 % | −24.2 % | **1.000** |
| | `st_regression` | −21.6 % | −22.5 % | 0.988 |
| | `low_aspect_ratio_DEMO` | *no curve* | *no curve* | — |

*(at each test case's own calibration accuracy; the premium is the all-settings ratio divided by the
matched-count one, so below 1 means the extra knob made the blocked arm look cheaper than it does at
equal tuning effort.)*

**In Phase A the second knob is worth 25–28 % on the two large test cases and flips the sign. In
Phase B it is worth nothing measurable.** The difference is not mysterious: Phase A's blocked arm
has bit-exact same-knob rungs whose cost is high, so restricting it to one knob forces an expensive
read; Phase B's ladder is coarser and its joint rungs already dominate the inner ones. **A bias that
is 1.000 on one phase and 0.717 on another is exactly why it has to be measured per case rather than
argued about once.**

**What the two constructions actually gave, measured.**

| test case | matched-count (architecture) | all-settings (practitioner) | tuning premium | convexity of the flat arm's envelope |
|---|---|---|---|---|
| `large_tokamak_nof` | −24.2 % | −24.2 % | **1.000** | **MIXED** — 1 of 2 interior points convex |
| `st_regression` | −21.6 % | −22.5 % | **0.988** | **CONVEX** — 1 of 1 interior points |
| `low_aspect_ratio_DEMO` | *no curve* | *no curve* | — | not testable |

*(at the accuracy the flat control delivers at τ = 1e-6; three accuracy statistics give the same
ranking on both test cases with a curve.)*

**So the bias is real in principle and small in this measurement.** On `large_tokamak_nof` the
extra four rungs add nothing at all: every one of them is dominated by a joint rung, the block
arm's envelope has two points either way, and the tuning premium is exactly 1.000. On
`st_regression` the second knob makes the block arm look **1.2 % cheaper** than it does at equal
tuning effort — real, one-directional, and an order of magnitude smaller than the effect. The
headline takes the matched-count number regardless, because the size of a bias is not a reason to
stop correcting for it.

**Bias 2 is dropped on `large_tokamak_nof` because the measurement says so.** The flat arm's
envelope there is convex at one interior point and concave at the other, so the chord argument does
not hold uniformly and is not asserted. On `st_regression` it does hold, and there the all-settings
reading is the one that benefits — consistent with the premium being below 1.

**And the Phase B ladder is thin, which is a larger limitation than the asymmetry.** It runs 2
starts per rung, restricted to the starts every rung of both arms kept — 2 on `large_tokamak_nof`,
1 on `st_regression`, and on `low_aspect_ratio_DEMO` **no curve at all**, because every rung's
achieved residual there is exactly zero and a log-log envelope cannot represent it. The
distributional cost result in §7.8 is over 20–22 starts and is the robust one; these matched-
accuracy figures are over 1–2 and are a different, weaker kind of evidence. **Both are reported and
neither is presented as the other.**

**Two rungs kept no start and are named rather than hidden.** On `st_regression`, both arms at
τ = 1e-3 solved none of the offered starts to the acceptance standard. A tolerance at which an arm
solves nothing is a measurement about that tolerance; letting it empty the common population would
have deleted the comparison instead of reporting it.

---

## 8. Conclusion

**The arrangement of solvers changes the cost of solving PROCESS, measurably, with every physics
model frozen.** That was the question, and the answer is yes in both phases.

### What each phase established

**Phase A, the optimiser absent, and the honest answer is a bracket.** At matched *tolerance* the
three-block partition appeared to cost **+46.8 % and +40.4 %** more than the flat control. At
matched *achieved* accuracy it costs **−4.3 % or +33.4 %** on one test case and **−4.5 % or
+27.4 %** on another, depending on whether the blocked arm is allowed the inner tolerance the flat
arm has no counterpart for; on the third the two constructions agree at **−13.1 % to −15.2 %**. The
published penalty was an artifact of comparing at matched tolerance — that part is settled — but
**the claim that replaced it, "at parity or cheaper on all three", holds under one construction of
the envelope and not the other**, and the one that supports it gives the blocked arm nearly twice
the draws. What survives without qualification: the partition is nowhere near as expensive as the
published figure said, and it is not shown to be worth anything.

**Phase B, the optimiser present, and it takes three arrangements to say anything.** Comparing the
proposed architecture directly against PROCESS as shipped measures the architecture and the
stopping rule *summed*, and the stopping-rule term is **+2.13 %, −3.38 % and +3.23 %** — comparable
in size to the architecture term and not of one sign. With a predicate-matched control between
them, the architecture alone, over 20–22 paired starting points:

| test case | architecture, `A0′ → A1′` | robustness, paired | verdict |
|---|---|---|---|
| `large_tokamak_nof` | **−1.63 %** (20 of 22 starts cheaper, q1–q3 0.982–0.985) | **identical success sets**, 22 both, 0 either way | **the architecture wins** |
| `st_regression` | **−6.18 %** (20 of 20 cheaper, q1–q3 0.881–0.948) | 21 both, **2 only the control**, **1 only the variant** — net −1 of 25 | **cheaper, but the success rate is net worse by one start** — *and see below* |
| `low_aspect_ratio_DEMO` | −21.2 % over **8** starts, ratios 0.241–3.320 | 11 both, 1 only the control, 0 only the variant | **inconclusive** — the distributions overlap, and the plan says so in advance |

**By the outcome table declared before the run, that is: wins on one test case, inconclusive on one,
and on the third cheaper but failing the robustness criterion by a single start.** Robustness
outranks cost, and one start is still one start.

**On that third test case the verdict is sensitive to a setting, and both readings are reported.**
Robustness above is compared at a fixed tolerance; at the setting that makes the two arrangements
equally converged — read off the ladder before the re-run — they solve **23 of 25 each** and the
architecture is 2.27 % cheaper rather than 6.18 % (§7.9.1). By the same outcome table that is the
architecture **winning** there. It is a one-start difference in each direction on 25, so the honest
statement is that `st_regression`'s verdict turns on a single start and on a tolerance that was
never chosen for robustness purposes — **not** that the architecture is robustly better.

### What changed against the first Phase B run, and why

That run reported that the architecture does not win anywhere and **never solves a start the
baseline cannot**. Three things move it.

1. **It compared against the wrong arm.** Against PROCESS as shipped the architecture is +0.48 %,
   −23.9 % and −5.06 %; against a predicate-matched control it is −1.63 %, inconclusive and
   −6.18 %. The difference is the stopping rule, which that design had no way to subtract.
2. **Two thirds of the measured robustness deficit is the stopping rule, not the architecture.** On
   the one test case where the coupling-state test refuses anything, the **flat control refuses two
   of the three** — the same quantity, `current_drive.eta_cd_dimensionless_hcd_primary`, going
   non-finite. The control shares PROCESS's own loop and differs only in what it stops on.
3. **The variant now solves a start the control cannot**, on `st_regression`. The earlier run's
   strongest sentence no longer holds.

**None of that makes it a clean win**, and the honest summary is the per-test-case table above.

### What the numbers are not

**They are not a matched-accuracy robustness comparison.** Cost is compared at matched achieved
accuracy; **robustness is compared at a fixed tolerance**, and those are not the same basis. What
is known about whether that is fair is measured rather than assumed (§7.9): at the campaign's own
setting the proposed architecture ends **strictly more converged** than the control on 20 of 22 and
25 of 25 starts and never less, and both end more converged than PROCESS as shipped. So the
robustness comparison is **conservative against the variant** — it is being asked a harder question.
On one test case the arrangements deliver **identical** accuracy on every paired start, and there
the comparison is exactly level. On `large_tokamak_nof` a matched-accuracy robustness comparison is
**not available at all**: the block arm's loosest measured setting is still four orders tighter
than the flat arm's, because solving each block to its own fixed point produces a tight state
whatever tolerance is asked for.

**The headline is the proposed architecture, never the partition's benefit.** Three things change
at once. Measured inside this architecture, the feed-forward hoist alone is worth −4.39 %, −4.32 %
and −2.95 %; on `large_tokamak_nof` the architecture **without** it costs **+2.88 %**. The
partition alone, on that test case, costs more.

**And the matched-accuracy figures for Phase B rest on 1–2 starting points**, against 20–22 for the
distributional result. They are a different and weaker kind of evidence and are labelled as such.

### The findings that are about PROCESS rather than about architecture

These may outlast both headlines.

- The loop's stopping test compares quantities of which **19 % on one test case are small enough
  that agreement is unconditional**, and it **treats a "not a number" state as converged**.
- It **stops with named model outputs still moving** on 8 of 600 replayed design points, always the
  levelised-cost family, precisely because those are the outputs it does not watch.
- Measured at the first optimiser evaluation of a perturbed start, it hands the optimiser a state
  whose worst coupling residual is **1.47 × 10⁹** on one start of `large_tokamak_nof` and
  **non-finite** on one start of `low_aspect_ratio_DEMO`.
- Its 1990 cost model **diverges at non-positive net electric power**, traced to a guard written
  against a zero denominator being applied to a negative one. Under 10 % perturbation this is not
  an edge case: **2 of 25 and 13 of 25 starting points** visit such a state, and on `st_regression`
  **2 586 of 53 675** optimiser evaluations are entered from one.
- Constraint **equality membership is decided by position** in the input deck's list, which once
  gave this study a plausible, converged, 38 %-cheaper wrong answer until a gate caught it.

### Scope, stated as limits

Three test cases, tokamak only, one commit, one starting-point distribution, one perturbation size,
one optimiser. Phase A is per-solve cost on the design points PROCESS's own optimiser visited;
Phase B is 25 perturbed starts per arrangement. The coupling-state test is built from a recording
taken at the **unperturbed** design point, and under 10 % perturbation a quantity that recording
classified constant moves on **1.7 %, 0.8 % and 24.2 %** of solves — on the third test case that is
a quarter of them, and it is not equal between arrangements. That is the largest single
methodological limitation of Phase B on this instrument and §7.11 states what would remove it.
Nothing here is a recommendation to adopt the arrangement; it is an existence proof that the
arrangement matters, and a measurement of by how much on these problems.

---

## Provenance

All measurements are at base commit `c0ae5b28`, frozen for the duration of the study. Every run
prints the tree, branch and commit it used and asserts the exact tree it imported — by path, never
by version string, because an archived tree can report a version from a different commit than the
one it contains. Nothing measured at any other commit is cited.

Recorded artifacts live under `arch_surgery/idf_probe/runs/` (`a18/`, `a22/`, `a23*/`, `a13/`,
`a3/`), which is untracked; the committed record is this document, the per-deck coupling-state
categorisation in `arch_surgery/docs/data/ystate_<deck>.json`, and the task reports in
`arch_surgery/docs/reports/deprecated/` — whose position in that folder records lifecycle, not
staleness, and each of which carries a status header saying which it is.

The effects and where each was measured:

| Effect | Measured by | Instrument |
|---|---|---|
| Two-pass floor; stricter stopping test; block vs flat; tolerance ladder; exit audit; magnitude distributions | A18 (experiment-framework) | replay engine, `arch_surgery/fixedpoint/` |
| What forces a second outer pass; the burn-time counterfactual; the degenerate cost evaluation | A22 (outer-pass-census) | same engine, two default-off hooks |
| The node-order control | A23 (flat-arm-permutation) | same engine, replay only |
| The feed-forward hoist | A13 (feedforward-hoist) | PROCESS's own driver, against a reference checkout |
| The build/physics reorder | A3 (build-reorder) | PROCESS's own driver, against a reference checkout |

Findings against the dependency analysis are recorded separately, and accumulate rather than being
archived, in [`DSM_VALIDATION.md`](DSM_VALIDATION.md).
