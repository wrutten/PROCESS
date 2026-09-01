# Does the arrangement of solvers change the cost of solving PROCESS?

**An experiment on the fusion systems code PROCESS, with every physics model held fixed.**

> **Document status** — **INCOMPLETE BY DESIGN.** Sections 1-3 (goal, hypothesis, method) are
> written. **Sections 4-6 (results, discussion, conclusion) are deliberately empty**: the
> experiment has not been run, and nothing is written ahead of the data. · Base commit
> `c0ae5b28` · Companion script: `MDA_partition_experiment.py` (not yet written; it is built on
> the machinery task A18 is producing).

---

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
performs 2 027 passes over the model sequence at roughly 7.8 milliseconds each — about 89 % of
the program's fifteen-second runtime. Everything else, including the optimiser's own linear
algebra and all file output, is the remaining tenth.

**Almost all of it is spent computing derivatives.** The optimiser needs the slope of the
objective and constraints with respect to each design variable, and it obtains them by finite
differences: nudge one design variable, re-solve everything, and measure what changed. Each such
nudge is a full run of the model loop. Of the 630 loop solves in one run, **600 are derivative
evaluations** — and they account for 94.5 % of all model passes.

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
requirement, because the entering state is already available. **Predicted effect: up to one pass
saved per solve, which is 630 of 2 027 passes — 31 %.**

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
**Predicted effect: uncertain, and prior measurement is discouraging** — see §3.7.

### 2.1 Why H3 is doubted in advance

Honesty about a prediction is cheaper before the data than after. Two earlier measurements at
this same base commit argue against H3:

1. The three blocks **stop changing at roughly the same time**, rather than one lagging. A saving
   requires a *small* block to be holding up a *large* one; measured, the large plasma block was
   joint-last in 82-85 % of solves.
2. Under a separated arrangement the bottleneck moves to the **coil block**, which is ten of
   forty-six model nodes but 42 % of the computational cost. It is not small either.

Those measurements were made under the *current* stopping test. Because this experiment changes
that test, they do not transfer directly — which is the reason H3 is worth re-testing rather than
being treated as settled. But they are a reason to expect little, and they are stated here so
that a negative result cannot later be presented as a surprise.

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
from neither effect existing.

A fifth variation — running the models that feed nothing back only once, after the loop, instead
of on every pass — is applied to **all** arrangements, so that it cancels and the comparison
remains purely about loop structure.

### 3.4 When a solve is finished

Each model quantity is compared against its own typical size, measured from the recorded design
points, and the loop stops when the largest relative change falls below a threshold.

Scaling each quantity by its own magnitude is not a detail. The quantities span more than
fourteen orders of magnitude, from below 10⁻⁸ to above 10⁶, and a single shared tolerance
therefore means something different for each of them. The program's existing test has exactly
this defect: it uses a comparison whose hidden absolute floor dominates for any quantity below
10⁻², which is **18 % of the quantities reported**, and for the 203 quantities below 10⁻⁸ it
accepts any change at all.

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
changing the answer — beyond that point the loop is converging noise. The calibration is run once
and the resulting threshold is shared by all four arrangements, because a comparison in which the
arrangements stop at different standards is not a comparison.

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

It records design points from each test case, calibrates the threshold, runs all four
arrangements over the recorded points, and writes both a summary table and a machine-readable
record of every count.

Four test cases are used, spanning two structurally different machine types: two large
conventional tokamaks, a low-aspect-ratio design, and a steady-state spherical tokamak. The last
of these lacks the quantity that joins the blocks, so its blocks are already separate — it acts
as a free control for H3.

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

> **Not yet written. The experiment has not been run.**
>
> This section will report, per test case and per arrangement: the number of design points
> attempted and dropped with the reason; the distribution of passes to convergence; the residual
> each arrangement had reached when it stopped, verifying that they stopped at comparable
> standards; and the pairwise comparisons R→A0f, A0f→A0 and A0→A1.

## 5. Discussion

> **Not yet written.** Requires §4.

## 6. Conclusion

> **Not yet written.** Requires §4.

---

## Provenance

All measurements are made at base commit `c0ae5b28`, which is frozen for the duration of the
study. Every run prints the tree, branch and commit it is using and warns if that tree does not
descend from the base commit. Figures quoted in §1 and §2 are from earlier tasks at this same
commit and are cited in the project's task reports; nothing from any other commit is used.
