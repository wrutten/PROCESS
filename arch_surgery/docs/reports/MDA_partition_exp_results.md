# Does the arrangement of solvers change the cost of solving PROCESS?

**An experiment on the fusion systems code PROCESS, with every physics model held fixed.**

> **Document status** — **CURRENT · STANDING DOCUMENT.** This is the results report for the MDA
> partitioning experiment, not a task report: it is **not** archived to `deprecated/` when the task
> that wrote it closes, and it is updated in place as later phases report. **Phase A is complete
> and written up in full (§§4–6). Phase B has not been built; §7 states it as a gap and says what
> it would have to measure.** · Base commit `c0ae5b28` · Companion script:
> [`MDA_partition_experiment.py`](../../../MDA_partition_experiment.py) at the repository root ·
> Written by task A21 (partition-report), 2026-09-01, from the recorded artifacts of tasks A18
> (experiment-framework), A22 (outer-pass-census), A23 (flat-arm-permutation), A13
> (feedforward-hoist) and A3 (build-reorder).

---

> ## ⚠ CORRECTION PENDING — the headline below is superseded (2026-09-02)
>
> **A26 (method-fixes) acted on this report's own §6.1 and the result overturns §4.4.2, §5.3 and §8.**
> Those sections say the blocked arrangement costs **+46.8 % / +40.4 % / +17.7 %** more, hedged as
> "at most" because the arms were compared at matched *tolerance* rather than matched *achieved
> accuracy*. Compared properly — cost read off each arm's lower envelope, `cost(a) = min{cost_i :
> accuracy_i ≤ a}` — the blocked arrangement costs **−4.3 % / −4.5 %** on the two large pulsed decks
> and **−13.1 %** on `st_regression`. §6.1's counter-argument, that a loose inner tolerance "would
> have to recover a very large factor", is refuted: it recovers all of it.
>
> **Read the replacement claim narrowly.** This removes the finding that the partition *costs*; it
> does **not** establish that the partition is worth anything. At its cheapest accuracy-matched
> setting the blocked arm runs **1 172 of 1 248 inner solves in a single sweep** — it has largely
> stopped blocking. The comparison rests on the **p90** of achieved accuracy, because the median
> exit residual is exactly **0** on 15 of 17 rungs, and on the *worst* design point the two arms are
> indistinguishable (ratio spans 0.82–1.23). The defensible sentence is: **the published penalty was
> an artifact of over-solving, not a property of the partition.**
>
> **§6.3 also contains a factual error.** It states that "exactly **one** constant moved". Three did,
> verified independently from A18's artifacts: `ccfe_hcpb.x_shield` (9 arm-records, `st_regression`)
> plus `physics.vs_plasma_burn_required` and `physics.vs_plasma_total_required` (63 arm-records each,
> `large_tokamak_eval`). On that deck they blocked convergence and inflated its counts by 14–28 %,
> which includes the very percentages §6.5.3 called its largest — a further reason the deck is
> dropped (D17).
>
> **A28 rewrites this document** to fold in both phases on the corrected instrument. Until then, treat
> §§4.4.2, 5.3, 6.1, 6.3 and 8 as superseded and this banner as the current statement.

## Abstract

PROCESS solves a fusion power plant design problem by wrapping an optimiser around a loop that
re-runs twenty-six engineering and physics models until their outputs stop changing. This
experiment asks whether the **arrangement** of that machinery — how many loops there are, what
they iterate on, and which models sit inside them — measurably changes the cost of solving, when
not one line of any physics model is altered.

The models are frozen deliberately. A faster program with rewritten models proves nothing about
architecture, because the rewrite and the rearrangement cannot be told apart afterwards. Freezing
the models makes the arrangement the only thing that varies, and therefore the only thing a
measured difference can be attributed to.

The experiment is designed as an **existence proof**. It does not attempt to find the best
possible arrangement, and it makes no claim that the arrangement it tests should be adopted. It
asks a narrower question that a single fair comparison can answer: *does a simple change to the
arrangement produce a difference large enough to care about?*

**The answer is yes, and it is not the answer the experiment was designed to look for.** The
three-block partition that motivated the study **costs more** on three of the four test cases —
46.8 %, 40.4 % and 17.7 % more model evaluations, over 149, 297 and 10 recorded design points —
and is 4.6 % cheaper on the fourth, over 144, which is the one case with no quantity joining the
blocks at all. Those three figures are upper bounds: the blocked arrangement was run with its
inner blocks over-converged, and §4.5 measures by how much. A change nobody designed the study
around, running the two models that feed nothing back once after the loop instead of on every
pass, **saves 6.56 %, 6.76 %, 6.64 % and 2.63 %** of all model evaluations, with every number in
the output file bit-identical to a reference checkout. Both results are counts, both reproduce
exactly, and together they say that the arrangement matters — while saying nothing in favour of
the particular rearrangement the study set out to test.

---

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

One command:

```
python MDA_partition_experiment.py
```

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

Four test cases are used, spanning two structurally different machine types: two large
conventional tokamaks (`large_tokamak_nof`, an optimisation run, and `large_tokamak_eval`, a
single evaluation run of the same deck), a low-aspect-ratio design (`low_aspect_ratio_DEMO`), and
a steady-state spherical tokamak (`st_regression`). The last of these lacks the quantity that
joins the blocks, so its blocks are already separate — it acts as a free control for H3.

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

#### 4.4.2 The block partition against the flat control

**This is the effect the study was designed around, and it lost.**

| Test case | n | Flat **A0** | Blocked **A1** | A1 / A0 | Change |
|---|---|---|---|---|---|
| `large_tokamak_nof` | 149 | 9 471 | 13 906 | **1.468** | **+46.8 %** |
| `low_aspect_ratio_DEMO` | 297 | 19 992 | 28 070 | **1.404** | **+40.4 %** |
| `st_regression` | 144 | 10 395 | 9 917 | **0.954** | **−4.6 %** |
| `large_tokamak_eval` | 10 | 525 | 618 | **1.177** | **+17.7 %** |

Two things are true at once, and both matter.

**The blocked arrangement does what the partition hypothesis predicted, in the unit the hypothesis
was stated in.** Its outer pass count is lower everywhere: 2.705 against 3.027 on
`large_tokamak_nof`, 2.721 against 3.205 on `low_aspect_ratio_DEMO`, 2.139 against 3.438 on
`st_regression`, 2.400 against 2.500 on `large_tokamak_eval`. Against the flat control it falls on
36 of 149, 100 of 297, 120 of 144 and 1 of 10 design points, and **rises on none, on any deck**.

**It buys those outer passes with inner solves, and the inner solves cost more than the outer
passes save.** Counted in model evaluations — the only unit in which a flat sweep and a per-block
sweep are commensurable — it is 18 % to 47 % more expensive on three of four cases.

**The one case where it does not lose is the one with no coupler.** `st_regression` sets
`i_pulsed_plant = 0`, so the burn time that joins the blocks is never written by any in-loop
model: its blocks are already independent and its outer loop is trivial by construction. That is
the partition working exactly as designed, and simultaneously the case in which the partition is
doing the least. Its −4.6 % is also fragile: with the feed-forward models lifted out of the loop —
the setting in which every arrangement is otherwise better off — it becomes **+0.77 %**.

For completeness, the same comparison with the feed-forward models lifted:

| Test case | Flat **A0** | Blocked **A1** | A1 / A0 |
|---|---|---|---|
| `large_tokamak_nof` | 8 569 | 13 100 | 1.529 |
| `low_aspect_ratio_DEMO` | 18 088 | 26 454 | 1.463 |
| `st_regression` | 8 683 | 8 750 | 1.008 |
| `large_tokamak_eval` | 475 | 570 | 1.200 |

*(These counts are the in-loop models only; §4.4.3 states the accounting.)*

**The comparison is the grouping alone, and that had to be established rather than assumed.**
Building the blocked arrangement by grouping the models by block also transposes two adjacent
models — `build` and `physics` — relative to the flat order. Nobody named that while the
comparison was built. It was closed afterwards by replaying the flat arrangement in the blocked
arrangement's node order: identical to the recorded flat arrangement on **600 of 600** design
points, and on **2 400 of 2 400** across every setting the flat arrangement was recorded under
(both hoist settings and all three tolerances), compared bit-for-bit with no tolerance anywhere —
pass counts, model-evaluation counts, the converged flag, the full residual trace at every pass,
and the exit audit. §4.4.4 records what that null does and does not license.

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
equal accuracy**.
This is the quantification of the conservatism §3.7 declared in advance, and it is the strongest
single argument that the blocked arrangement was run in an unfavourable configuration rather than
being simply worse. §5.3 says what would settle it.

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

**1. It was run in its least favourable configuration, and the exit audit measures how much.** The
inner blocks are driven to the same tolerance as the outer loop, so the blocked arrangement
terminates at a residual about 10⁵ times tighter than the flat control at the same nominal
tolerance. It is paying for accuracy nobody asked for. This was declared conservative in advance,
and §4.5(b) is the quantification. **The +18 % to +47 % is therefore an upper bound on the
partition's cost, not an estimate of it.** The obvious next thing to vary is the inner tolerance —
the inexact-block regime — and it has not been run.

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

---

## 6. A second pass: criticising this experiment's own method and results

Everything in this section is a criticism of the work reported above, made after the results were
in. Where it changes what §4 or §5 should say, the change has been made there and is cross-noted.

### 6.1 The strongest objection: the losing arm was handicapped and the winning arm was not

The blocked arrangement solves each block to τ = 1e-6 against inputs that are about to change. The
flat arrangement has no inner loop and never pays that. **The two arms are not symmetric in the
freedom they were given**, and the direction of the asymmetry is exactly the direction of the
result. The exit audit shows the blocked arm ending up 10⁵ times more converged than the control at
the same nominal setting — it did more work and got more accuracy, and only the work is counted in
the ratio.

This was declared in advance, which makes it honest but does not make it fair. **The correct
statement of the result is that the partition costs *at most* 47 %, 40 % and 18 % more, and that
the study did not measure what it costs at a comparable inner tolerance.** §4.4.2, §5.3 and §8 are
worded that way. A study that reported "the partition costs 47 % more" without that clause would
be overstating its own finding.

The counter-argument, and it is not nothing: the outer pass counts fall by much less than the
inner solves cost, on every case, so an inexact inner tolerance would have to recover a very large
factor. But "would have to" is not "does not", and the run has not been made.

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

**An excluded quantity that genuinely couples would be invisible.** Quantities that never vary
across the recording are excluded from the stopping test. If one of them genuinely coupled, every
arrangement would declare a convergence that had not happened, with no symptom. What guards it: an
excluded quantity is asserted at runtime to stay constant, and across all 600 design points, all
four arrangements and both hoist settings exactly **one** constant moved — `ccfe_hcpb.x_shield`, on
3 of `st_regression`'s 144 points — and it blocked convergence at those passes rather than passing
silently. On `large_tokamak_eval` this guard is weakest, because 555 of 840 components were
classified constant from 10 points (§5.4).

**The confound that was nearly missed.** Grouping the models by block also transposed two adjacent
models, and the flat-to-blocked comparison therefore varied two things. Nobody named it while the
comparison was built or measured; it was found afterwards by cross-reading two pieces of work
against each other, and closed by a dedicated replay (§4.4.4). **The lesson is not that the null
came out clean.** It is that a headline comparison ran, and was written up, with an unnamed
confound in it, and that what caught it was an unrelated task's diff rather than any check the
design contained.

**A methodological point that outlasts the result.** The licence to reuse one task's recording in
another's replay was originally argued from the git tree being unchanged. That argument stopped
working the moment two later tasks touched the driver. The replacement is better and should be the
pattern: the sub-trees that determine model behaviour are hash-identical to the recording commit,
**and the driver is entered zero times during a replay, counted rather than asserted**. That cuts
both ways, and it should be said plainly: the bit-identity gates on the driver changes do not
license the reuse at all, because they gate a path the replay never executes.

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

### 6.5 What would most improve this study, in order

1. **Run the blocked arrangement at a loose inner tolerance.** It is the one change that could
   overturn the headline, it is a replay rather than a solve, and the design already has the
   parameter.
2. **Find an exact per-model cost unit.** Everything in §5.2 is downstream of not having one.
3. **Enlarge `large_tokamak_eval`'s recording, or drop the deck.** Ten design points is not enough
   to classify 840 quantities, and the deck currently carries two of the report's largest
   percentages.
4. **Give the replay engine's hoist the same figure-of-merit guard the driver has**, so that the
   two instruments measure one architecture on every deck rather than three of four.
5. **Route the two findings that are about PROCESS rather than about architecture** — the
   unconditional-agreement hole in the stopping test, and the cost model diverging at negative net
   electric power — to the code-analysis study, with their denominators.

---

## 7. Phase B — not built, stated as a gap

**Phase B does not exist.** Nothing in this report is evidence about it, and the experiment plan's
expectations for it are expectations, not results.

Phase A removed the optimiser deliberately, which is what made its numbers exact. The price is
that it cannot answer the question an adoption decision turns on: **what does the arrangement cost
in a whole optimisation, where the optimiser reacts to it?** Phase B is the design for that
question. It would host the burn time on the optimiser as a design variable with an equality
consistency constraint, put the per-block solvers and the hoist into PROCESS's own driver, and
compare against PROCESS as it currently ships.

Four things about it are settled in advance and are worth stating here, because each is a place
where a careless reading of Phase A would mislead:

- **Its baseline is PROCESS as shipped**, not Phase A's re-implemented flat arm. Our harness
  against PROCESS's loop compares two codebases; baseline-PROCESS against modified-PROCESS varies
  one thing.
- **Its variant carries the lift, the per-block solvers *and* the hoist together.** Its headline is
  therefore *the proposed architecture*, never *the partition's benefit*. The hoist is separable
  and is measured separately here; a combined number quoted as the partition's would be exactly
  the units error this project has recorded.
- **Robustness outranks cost.** The fraction of perturbed starting points each arm solves is a
  first-class result. An arm that is cheaper on the starts it solves and fails on more of them has
  not won.
- **The metric is model evaluations, never optimiser iterations.** The two arms solve problems of
  different dimension; iteration counts are not comparable between them and are diagnostics only.

Two Phase A results bear on Phase B and both are constraints rather than encouragement. The
burn-time counterfactual in §4.7 is the loop-side saving that would become *available* if a
consistency constraint were driven to zero — about −26 % after the dimension penalty, and
conditional on an optimiser iteration count that nothing bounds. And **on `large_tokamak_eval`,
Phase A's hoist and the production hoist resolve different model sets** (§4.4.3), so any future
table putting a Phase A and a Phase B hoist figure near each other owes the reader that sentence
for that deck.

A third thing Phase A can already tell Phase B: its perturbed multi-starts will meet §4.8's
degenerate cost evaluation **by design**, because they deliberately perturb the starting point and
so will visit infeasible entry states. An arm that happens to visit more of them would show more
passes for a reason that has nothing to do with architecture. Net electric power at entry should be
recorded per start, and the count of degenerate starts reported alongside every cost figure, as
§4.8 does with its 7/144.

---

## 8. Conclusion

**The arrangement of solvers changes the cost of solving PROCESS, measurably, with every physics
model frozen.** That was the question, and the answer is yes.

**It is not the partition that demonstrates it.** The three-block partition costs 46.8 %, 40.4 %
and 17.7 % more model evaluations than the flat control on `large_tokamak_nof`,
`low_aspect_ratio_DEMO` and `large_tokamak_eval` respectively, over 149, 297 and 10 recorded
design points, and 4.6 % *less* on `st_regression` over 144 — the one case with no cross-block
coupler, and therefore the case in which the partition is doing the least. Those figures are
**upper bounds**: the blocked arm was run with its inner blocks driven to the same tolerance as
the outer loop, and the exit audit shows it terminating about 10⁵ times more converged than the
control. What the study has not measured is what the partition costs at a comparable inner
tolerance.

**What demonstrates it is the change nobody designed the study around.** Running the two
feed-forward models once after the loop instead of on every pass removes **6.56 %, 6.76 %, 6.64 %
and 2.63 %** of all model evaluations, measured in PROCESS's own driver over whole optimisation
runs, with **0 of 13 559 / 13 455 / 13 493 / 13 487** output floats differing from the reference
checkout when compared as hex literals with no tolerance. It changes no pass counts at all: it
removes work *within* passes, which is why a sweep-counting analysis would have valued it at zero.
Its hoistable set depends on the deck's figure of merit, not only on the code.

**The two-pass floor is real and small.** Removing it is worth 1.53 %, 1.55 %, 1.79 % and 10.7 %,
realised on the 4.7 %, 5.1 %, 6.3 % and 30 % of design points whose entering state is already
converged — an order of magnitude below the "up to 31 %" the study carried before measuring it.
On `large_tokamak_nof` it is cancelled exactly by the cost of the stricter stopping test: 9 471
model evaluations either way, from two real effects of about 1.5 % pulling in opposite directions.

**The stricter stopping test is not the trade it was predicted to be.** It costs 1.55 % and 8.62 %
on two cases, and *saves* 3.40 % on a third, where 54 of 297 design points converge a pass sooner
because the objective and constraints were still disagreeing after the model state had settled.
It converged every one of 600 design points on every arrangement, with no limit reached anywhere —
the predicted robustness cost did not appear.

**The findings that are about PROCESS rather than about architecture may be the durable ones.**
The loop compares constraint values of which 19 % on one deck are small enough that its test
reports agreement unconditionally; it stops with the levelised-cost family still moving on 8 of
600 design points, because those are the outputs its test does not watch; it treats a "not a
number" state as converged; and its 1990 cost model diverges at negative net electric power in a
way that makes a scaled relative test roughly 10¹⁸ times too tight on 7 of `st_regression`'s 144
points.

**Scope.** Four decks, tokamak only, one commit, per-solve cost with the optimiser absent, on the
design points PROCESS's own optimiser visited. Phase B, which would put the optimiser back and ask
what any of this costs in a whole run, has not been built.

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
