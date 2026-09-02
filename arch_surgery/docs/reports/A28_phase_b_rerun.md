# A28 (phase-b-rerun) — Phase B re-run on the fixed instrument, with a control that can attribute the answer

> **Document status** — **CURRENT · TASK REPORT, open.** Written by task A28 (phase-b-rerun),
> 2026-09-02, on branch `A28-phase-b-rerun` at experiment base commit `c0ae5b28`, branch point
> `dc18c05b`. It is archived to `deprecated/` when the task merges and stays authoritative there
> (trap T3: folder position records lifecycle, not validity). Nothing here is merged; nothing is
> pushed.

| | |
|---|---|
| **Task** | A28 (phase-b-rerun) — re-run Phase B on the instrument A26 (method-fixes) left behind, with the third arm decision **D18** requires, and write up both phases |
| **Branch** | `A28-phase-b-rerun`, worktree `/home/wrutten/projects/PROCESS_surgery_worktrees/A28-phase-b-rerun` |
| **Governed by** | **D5**/**D11** (physics frozen; model edits need approval — none was needed), **D6** (correctness never on iteration variables), **D14** (the baseline is PROCESS as shipped), **D15** (calibrated δ, hoist inside the variant, objective mismatch is a robustness finding, a failed module solve raises), **D17** (`large_tokamak_eval` dropped; timings as context only), **D18** (three arms; `A0′ → A1′` is the headline) |
| **Environment** | `PROCESS_surgery_env` (`/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python`, Python 3.12.14); `PYTHONPATH` pinned to this worktree per subprocess; the **exact** tree asserted inside every subprocess (trap T6) |
| **Date** | 2026-09-02 |

---

## 1. Verdict

### The proposed architecture wins on one deck, is inconclusive on one, and on the third is cheaper but turns on a single start

**Every gate passed, so the campaign ran.** 300 complete optimisations, three arms plus one
diagnostic arm, 25 paired starting points per arm per deck.

| deck | `A0′ → A1′` — the architecture, at matched stopping rule | robustness, paired | verdict |
|---|---|---|---|
| `large_tokamak_nof` | **−1.63 %** (paired median; 20 of 22 starts cheaper; q1–q3 0.982–0.985) | **identical success sets** — 22 both, 0 either way, 3 neither | **wins** |
| `st_regression` | **−6.18 %** (20 of 20 cheaper; q1–q3 0.881–0.948) | 21 both, **2 only the control**, **1 only the variant** — net −1 of 25 | **cheaper, robustness net −1** — *and it flips at matched accuracy, §1.3* |
| `low_aspect_ratio_DEMO` | −21.2 % over **8** starts, ratios **0.241–3.320** | 11 both, 1 only the control, 0 only the variant | **inconclusive**, by the outcome table declared in advance |

**This is a materially different verdict from A25's**, which reported that the architecture does not
win anywhere and *never solves a start the baseline cannot*. Three things move it, and the first is
the whole reason D18 added a third arm.

### 1.1 A25 compared against the wrong arm, and the term it folded in is not small

| deck | `R → A0′` — the stopping rule alone | `A0′ → A1′` — the architecture alone | `R → A1′` — both, the user-facing figure |
|---|---|---|---|
| `large_tokamak_nof` | **+2.13 %** (0 of 22 cheaper) | **−1.63 %** | +0.48 % |
| `low_aspect_ratio_DEMO` | **−3.38 %** (12 of 12) | inconclusive | −23.9 %, inconclusive |
| `st_regression` | **+3.23 %** (1 of 22) | **−6.18 %** | −5.06 % |

**The stopping-rule term is +2.1 %, −3.4 % and +3.2 % — comparable in size to the architecture term
and not of one sign.** A25 measured `R → A1′` and reported it as the architecture. On
`large_tokamak_nof` that is +0.48 % where the architecture alone is −1.63 %: the sign of the answer
comes from the term that was folded in.

### 1.2 Two thirds of the robustness deficit is the predicate, not the architecture

This is the measurement A28 was commissioned for, and it is decisive.

| deck | arm | starts not solved | of | refusals by the coupling-state test | quantity named |
|---|---|---|---|---|---|
| `large_tokamak_nof` | R / A0′ / A1′ | 3 / 3 / 3 | 25 | **0 / 0 / 0** | — |
| `low_aspect_ratio_DEMO` | R | 2 | 25 | 0 | — |
| | **A0′** | 4 | 25 | **2** | `current_drive.eta_cd_dimensionless_hcd_primary` |
| | **A1′** | 5 | 25 | **3** | the same quantity |
| `st_regression` | R / A0′ / A1′ | 0 / 0 / 0 | 25 | 0 / 0 / 0 | — |

**On the one deck where the coupling-state test refuses anything, the flat control refuses two of
the three.** A0′ shares PROCESS's own loop — one flat sweep over every model — and differs from it
only in what it stops on. So two thirds of the deficit is the stopping rule declining to call a
non-finite state converged, and one is the architecture examining intermediate module state that a
flat sweep overwrites before anything looks at it. It is the **same quantity** A25 named.

A25's report attributed all 13 of its refusals to the architecture. The orchestrator's assessment
then overturned A25's own mitigating caveat and concluded the deficit was *"genuine, not an
accounting artifact"* and the negative verdict *"better supported than the report claims"*. **That
conclusion was right about the mechanism and wrong about the attribution**: the per-module solve
does examine state the global loop never tests, but so does the flat control, because the
attribution is to the *predicate* that both share and not to the schedule that only one has.

### 1.3 On `st_regression` the verdict turns on one start, and on a tolerance chosen for cost

Robustness is compared at a fixed tolerance while cost is compared at matched achieved accuracy.
Those are different bases. At the setting that makes the two arrangements equally converged — inner
tolerance 0.01, read off the ladder **before** the re-run:

| `st_regression` | both | only A0′ | only A1′ | neither | success counts | cost, paired median |
|---|---|---|---|---|---|---|
| at matched **tolerance** (inner 1e-6) | 21 | **2** | 1 | 1 | 23 vs **22** | **0.938 (−6.18 %)**, n = 20 |
| at matched **achieved accuracy** (inner 0.01) | 22 | **1** | 1 | 1 | 23 vs **23** | **0.977 (−2.27 %)**, n = 19 |

**The robustness deficit disappears and the cost advantage shrinks by 3.9 percentage points.** Both
readings are reported, with the tolerance each was measured at named. By the pre-declared outcome
table the matched-accuracy reading is the architecture winning on that deck. **It is a one-start
difference in each direction on 25**, so what it establishes is that the verdict was sensitive to a
setting never chosen for robustness purposes — not that the architecture is robustly better.

### 1.3a A finding outside Phase B: A26's overturning of Phase A holds under one envelope construction and not the other

The coordinator required the matched-accuracy envelope's asymmetry to be **corrected**, not merely
declared: the blocked arm has an inner tolerance the flat arm does not, so it gets eleven draws
against six on a running minimum, and the extra draws sit in one narrow accuracy band. The fix is a
**matched-count** envelope — six joint rungs against six flat, one knob each — reported beside the
all-settings one. I regenerated Phase A's ladders to compute it (A26's artifacts no longer exist,
issue I-14), and it changes the answer:

| deck | **matched-count** (architecture, equal tuning effort) | all-settings (practitioner, A26's published figure) | tuning premium |
|---|---|---|---|
| `large_tokamak_nof` | **+33.4 %** | **−4.3 %** | 0.717 |
| `low_aspect_ratio_DEMO` | **+27.4 %** | **−4.5 %** | 0.750 |
| `st_regression` | **−15.2 %** | −13.1 % | 1.026 |

**The two constructions disagree in sign on two of three decks, by 32 and 38 percentage points —
an order of magnitude larger than the effect either reports.** A26's replacement headline, *"at
matched achieved accuracy the partition is at parity or cheaper on all three decks"*, holds under
the construction that gives the blocked arm nearly twice the draws and **not** under equal tuning
effort. My regeneration reproduces A26's all-settings numbers to rounding (−4.32 / −4.53 / −13.06
against −4.3 / −4.5 / −13.1), so this is a construction difference and not a reproduction failure.

**The mechanism is exact.** On the two large decks the blocked arm's tight *same-knob* rungs reach a
bit-exact fixed point and cost 12 632 and 25 463; its cheap tight rungs are the *inner-only* ones, at
9 062 and 19 087. The whole of the −4.3 % and −4.5 % is bought by the second knob.

**And the matched-count reading is biased in the other direction**, which must be said with it. The
joint ladder is coarse in achieved accuracy — on `large_tokamak_nof` it jumps from 4.3e-07 straight
to bit-exact — so the read is forced onto a rung that overshoots the target. That is a granularity
limit of the ladder as run. **The honest object is therefore a bracket**: −4.3 % to +33.4 %, −4.5 %
to +27.4 %, and −13.1 % to −15.2 %. Only the third is a measurement in the sense the rest of this
study's numbers are.

**A defect in the envelope construction was found doing this, and it is inherited from A26.** Rungs
whose achieved residual is exactly zero were excluded from the envelope as well as from the log-log
fit, on the argument that they can never win it. That is true of the all-settings curve on these
decks and **false of a curve restricted to one knob**, where the tight rungs *are* the bit-exact
ones: the matched-count comparison reported OUT OF MEASURED RANGE for an arm that in fact reaches
the target exactly. `cost_at` now admits them to the envelope while still excluding them from the
fit. **This changes no all-settings number** — verified: −4.32 / −4.53 / −13.06 either way.

### 1.4 Six things that qualify it, all measured

1. **`st_regression`'s figure rests on a predicate that is not doing the same thing in the two
   arms.** Under 10 % perturbation, a quantity the Phase A recording called constant moves inside
   **24.2 %** of A0′'s optimiser evaluations and **19.3 %** of A1′'s (13 817 of 57 030 against
   10 528 of 54 480). On the other two decks it is 1.7 % / 1.7 % and 0.7 % / 0.8 %. This is the
   exact failure mode A26 §5.4 found on the dropped deck. **The fix already exists and was not
   used**: A26's no-exclusion predicate, which changes no Phase A count at three scale floors a
   decade apart. Phase B ran on A18's artifact for continuity with the run it replaces. This is the
   single largest caveat on this task's numbers.
2. **The headline is the proposed architecture, never the partition's benefit** (plan §7a). The
   hoist's separable share, measured **inside** this architecture: **−4.39 %, −4.32 %, −2.95 %**. On
   `large_tokamak_nof` the architecture *without* it costs **+2.88 %** — the partition alone costs
   more there, and the combined figure is negative only because of the hoist.
3. **H5's own risk did not materialise.** The paired optimiser-iteration ratio is exactly **1.000 at
   q1, median and q3** on two decks for every comparison, and moves in the variant's favour on the
   third (median 0.806). Adding a design variable and a consistency constraint did not measurably
   disturb the search.
4. **The robustness comparison is conservative against the variant.** At the campaign's own setting
   the variant ends **strictly more converged** than the control on 20 of 22 and 25 of 25 starts and
   never less, and both end more converged than PROCESS as shipped. On the third deck all three
   deliver **identical** accuracy on every paired start.
5. **The matched-accuracy cost figures rest on 1–2 starting points** against 20–22 for the
   distributional result, and on one deck the ladder yields **no curve at all**. They are a weaker
   kind of evidence and are labelled as such.
6. **Three decks, one perturbation size, one starting-point distribution, one optimiser, one
   commit.** It does not transfer.

### 1.5 What this task did not claim

- **No physics change and no `process/models/` change at all.** D11's approval gate was not reached.
- **Nothing rests on a timing.** The p10–p90 band is **19 % to 568 %** of the median against effects
  of 1.6–6.2 %; on two decks it is two orders of magnitude wider than the effect.
- **No setting was tuned after seeing a result.** δ was calibrated on the reference arm alone; the
  gate tolerance is PROCESS's own; the matched-accuracy inner tolerance was read off the ladder
  before the re-run; and both readings of the affected comparison are reported.

---

## 2. What was built

### 2.1 A0′ — the predicate-matched control, as the degenerate single-block case

A26 §10 asked whether Phase B's flat control is `module_solve.py` with one block containing every
node, and answered *nearly*, naming two blockers. It is now that degenerate case, and the two
blockers are fixed rather than worked around.

| file | change |
|---|---|
| `process/core/solver/module_solve.py` | `flat_state` arm; `PROCESS_ARCH_INNER_TAU`; `FLAT_BLOCK_ORDER` / `FLAT_ITERATED` and the `block_order()` / `iterated()` accessors |
| `process/core/caller.py` | the single-block schedule branch, `_loop_node_set`, `_single_block_covers_loop`, the outer-pass guard, and the inner tolerance threaded through `_call_models_by_module` |

**The outer-pass guard is a correctness statement, not an optimisation.** With one block covering
every in-loop node, the block's own inner test compares two successive full sweeps over the whole
coupling vector; the outer test asks the same question of the same index set. But the outer loop
compares against the state at *entry*, so it fails on pass 1 and succeeds on pass 2 — buying exactly
one wasted full sweep per `call_models`, which is A18's measured A0f → A0 effect of 1.53–1.79 %. The
guard fires on a condition evaluated from the schedule that was **actually built**, not from the arm
name, and every run records whether it fired (630 of 630 `call_models` on the gate run).

**A0′ takes the upstream node order**, so `R → A0′` varies the stopping rule and nothing else. The
transposition that block grouping brings with it is measured by a separate diagnostic arm (§3.4).

**The inner tolerance** exists because A26 fix 1 established that comparing at matched tolerance is
not a comparison. Setting it under `flat_state` is an import-time error rather than a value that
quietly does nothing: a knob that silently does nothing is how a ladder rung ends up mislabelled.

### 2.2 The measurement instruments added to `run_one.py`

All harness-side, applied identically to every arm, and none of them touches `process/` on a path a
measurement takes.

| instrument | what it measures | why |
|---|---|---|
| `--exit-audit` | the coupling-state residual after `SingleRun.run()` | **and it is useless — see §5.1** |
| `--exit-audit-at-call N` | the same, at the return of the *N*-th optimiser evaluation, then **stops the run** | the sweep mutates the state, so a run that takes one cannot also be a cost measurement |
| `--entry-census` | net electric power at the state each `call_models` is **entered** with | issue I-12, measured where the issue says to measure it |
| `--node-census` | model calls **per node name**, by wrapping `Caller._node` | the cost unit checked rather than asserted |

### 2.3 The harness

`run_a28.py` (arms, decks, the five stages, `--resume`), `a28_analysis.py` (descriptors and
manifests, the model-set gate, the equivalence gate over three arms, the ladder, H5, the accuracy
census, the matched-robustness comparison, timings), `a28_tables.py` (the tables, in the fixed
order: gates, robustness, drop census, then any ratio). `arch_surgery/experiment_runner.py` is the
machinery both root entry points share.

**Reused unchanged wherever possible**: `a25_gates.gate_scenario` (generalised only by giving it the
arm names as parameters, defaulting to A25's), `a25_h5.compare` and `calibration`, `gates.py`'s
census and cost-comparison, `fixedpoint/manifest.py`, `fixedpoint/accuracy.py`'s envelope and
`fixedpoint/accounting.py`'s definition. A second implementation of a predicate is how two
implementations drift.

---

## 3. The gates, each shown capable of failing

### 3.1 Switch neutrality — 0 of 91 882 quantities, per mode

Every architecture switch is read on a path every run takes, including a run with every switch off.

| | `large_tokamak_nof` | `low_aspect_ratio_DEMO` | `st_regression` |
|---|---|---|---|
| MFILE lines differing / compared | **0** / 16 174 | **0** / 16 435 | **0** / 18 692 |
| MFILE floats differing / compared, as hex | **0** / 13 559 | **0** / 13 455 | **0** / 13 493 |
| total quantities compared | 29 760 | 29 916 | 32 206 |

**0 of 91 882 per mode, probe off and probe on — 183 764 in total**, against a `git archive` of the
parent commit `dc18c05b`. `ifail`, sweeps and solver iterations unchanged (8/16/10). Teeth: 1 ULP of
`rmajor` caught on 3 of 3 as exactly one differing line and one differing float; 1 ULP of
`norm_objf` and of `sqsumsq` flip the acceptance predicate on 3 of 3; a changed `ifail` on 3 of 3;
two different decks differ on 11 606 of 13 441 shared floats. `tests/unit`: **843 passed, 4
skipped**, the same as A24 and A25.

### 3.2 The comparison manifests — 10 of 10 ordered arm pairs, on each of 3 decks

Every ordered pair of the five arms run carries a declaration from a closed vocabulary, checked at
run time against a flat descriptor of everything a comparison could be varying, **read from what
each run resolved** rather than from what the driver asked for.

**PASS, 10 of 10 pairs on all three decks, 0 undeclared, 0 skipped.** The declarations differ per
deck and the machinery forces that: on `st_regression` `A0′ → A1′` declares `block_grouping` and
`hoist` but **not** `lift`, because that deck has no burn-time coupler and declaring a dimension
that does not differ is refused as an over-declaration.

Teeth: an undeclared difference, an over-declared manifest and an undeclared arm pair are all
refused — **3 of 3**.

**It refused a real comparison first.** `R → A0′` was refused because my descriptor recorded the two
arms' single blocks under different labels (`LOOP` and `FLAT`) and reported a structural difference
where there was none. **The fix was to the descriptor, not to the declaration**: a one-block
schedule's label carries no information, and encoding my own naming as a structural difference makes
the descriptor lie about what the arms differ in.

### 3.3 Model-set coverage and the cost unit — and the fifth consecutive harness defect

A block schedule that fails to name a model does not fail; it silently stops running it. The model
call sites are read out of `caller.py`'s source and checked against what each arm resolved:
**26 call sites, all covered, on 15 of 15 arm records.** The cost unit is checked the same way:
the per-node counts must equal the reported total plus the audit sweep's own calls, and **nothing
may have been run through the flat hoisted tail**, which does not increment the counter (A26 §7.3's
accounting error). **0 uncounted tail calls on 15 of 15.**

**Protocol §12 found a defect in this task's own harness before the gate passed — the fifth
consecutive task, and in every case while the gate was already passing.** The call-site extraction
matched `ast.Assign` only, and `_SEQUENCE_HEADS` is an *annotated* assignment (`ast.AnnAssign`), so
the three head models — `plasma_geom`, `build`, `physics` — were **not in the call-site set at all**.
A set that does not contain a model cannot notice it missing; the coverage figure was over 23 sites
rather than 26. Found by the sensitivity check removing a model from a schedule and watching the
gate go on passing. The check now **refuses to report a coverage figure at all** if the table does
not parse, and exercises a head model by name. Teeth: **3 of 3** — dropping any covered node,
dropping a head node, and attributing three calls to the uncounted tail.

### 3.4 The equivalence gate — PASS on 12 of 12 arm gates

| deck | arm | verdict | objective, relative difference | margin | inequalities violated R / arm | consistency residual |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | A0′ | **PASS** | 4.16e-16 | 2.4e+09 | 0 / 0 | — |
| | A1′ | **PASS** | 7.98e-11 | 1.25e+04 | 0 / 0 | 1.19e-08 |
| | A0′ reordered | **PASS** | 4.16e-16 | 2.4e+09 | 0 / 0 | — |
| | A1′ no hoist | **PASS** | 7.98e-11 | 1.25e+04 | 0 / 0 | 1.19e-08 |
| `low_aspect_ratio_DEMO` | A0′ | **PASS** | 5.06e-15 | 2.0e+08 | 0 / 0 | — |
| | A1′ | **PASS** | **6.85e-07** | **1.46** | 0 / 0 | 1.63e-10 |
| | A0′ reordered | **PASS** | 5.06e-15 | 2.0e+08 | 0 / 0 | — |
| | A1′ no hoist | **PASS** | 6.85e-07 | 1.46 | 0 / 0 | 1.63e-10 |
| `st_regression` | A0′ | **PASS** | 3.83e-14 | 2.6e+07 | 0 / 0 | — |
| | A1′ | **PASS** | 5.03e-14 | 2.0e+07 | 0 / 0 | — |
| | A0′ reordered | **PASS** | 3.83e-14 | 2.6e+07 | 0 / 0 | — |
| | A1′ no hoist | **PASS** | 5.10e-14 | 2.0e+07 | 0 / 0 | — |

`low_aspect_ratio_DEMO`'s lifted arms pass with a margin of **1.46**, not 10⁴ — the closest thing in
this task to a near miss. The tolerance is PROCESS's own `check_agreement` rtol, fixed before the
run and not adjusted after. A dash in the last column is a deck that names no `icc = 93`, not a
silent pass.

Teeth: eight deliberately corrupted inputs per arm, through the production predicates unmodified —
**28 of 28 that must fail, do**. Four more are reported **NOT APPLICABLE rather than counted either
way**: the two consistency-residual perturbations watch a quantity that does not exist on an arm
without the lift, so mutating it changes nothing and the gate correctly still passes. Counting those
as passes would be the vacuous-gate failure mode A26 §7.1 records.

### 3.5 The node transposition, measured at exactly zero

`A0′` and `A0′`-with-`build`-after-`physics` produce **identical** counts on all three decks — 43 449,
86 877 and 42 756 net model evaluations, to the last call. So the node-order component of
`A0′ → A1′` is measured at zero in PROCESS's own driver, as A23 measured it at zero in the replay
engine over 2 400 arm records. Two instruments, two populations, the same null.

---

## 4. What was measured

The full tables are in the standing results document §7. This section reports only what is not
there.

### 4.1 The perturbation size reproduces A25's exactly

108 runs on the reference arm alone. **δ = 10 % on all three decks**, and every cell of the table
matches A25's: 12/12, 12/12, 11/12 · 12/12, 9/12, 7/12 · 12/12, 11/12, 12/12. The reference arm is
bit-identical to A25's (§3.1), so this is a check on the harness rather than new evidence — but
A25's artifacts no longer exist (issue I-14), so it had to be produced rather than cited.

### 4.2 Issue I-12 recurs, and A25's reading of it was measuring the wrong place

| deck | starts visiting a non-positive entry | of | non-positive entries | of | worst |
|---|---|---|---|---|---|
| `large_tokamak_nof` | **2** | 25 | 84 | 13 502 | −92.5 MW |
| `low_aspect_ratio_DEMO` | **0** | 25 | 0 | ~28 500 | — |
| `st_regression` | **13** | 25 | 2 586 | 53 675 | −783 MW |

**A25 reported zero degenerate entries in 300 runs.** That measurement was taken at the point each
run *returned* — a converged, feasible design. I-12 is about the states the loop is *entered* with,
which is where A22 measured it and what A26 §11.7 asks for. Measured there it is present on two of
three decks and on one of them is not rare: **13 of 25 starts and 4.8 % of all optimiser
evaluations**. It is **identical across arms** on every deck, so it inflates every arm's counts
together rather than biasing the comparison. The earlier zero was not wrong about what it measured.

### 4.3 Timings, with the sentence they have to be read with

| deck | R | A0′ | A1′ | spread as % of median |
|---|---|---|---|---|
| `large_tokamak_nof` | 20.8 s | 32.4 s | 52.4 s | 19–21 % |
| `low_aspect_ratio_DEMO` | 33.5 s | 53.3 s | 75.4 s | 193–281 % |
| `st_regression` | 34.2 s | 54.4 s | 96.3 s | 323–568 % |

*CPU-second medians over 20–25 repetitions, with p10–p90 as the interval.* **The interval is 19 % to
568 % of the median against effects of 1.6 % to 6.2 %; on two decks it is two orders of magnitude
wider than the effect. No ratio of two of these numbers can resolve one and none is offered.** The
analysis module refuses to emit one. Two further reasons not to read the medians as an arm
comparison: they are at matched *tolerance*, where §7.9 measures the variant ending strictly more
converged; and the coupling-state arms carry per-block bookkeeping the reference does not, which a
model-evaluation count is blind to by construction and a clock is not.

---

## 5. Three things that went wrong, and what they cost

### 5.1 The exit-audit instrument I built first could not discriminate at all

The first accuracy measure took one further full sweep **after `SingleRun.run()` completed**. It
reads exactly **0.0 for every arm at every tolerance on every deck**, because
`call_models_and_write_output` re-converges the state to MFILE idempotence — a stricter standard
than any arm's own test. An instrument that returns the same value for every arm is not an
instrument.

Replaced by an audit at the return of a chosen optimiser evaluation, which then **stops the run**,
because the sweep mutates the state and a run that continues after it is no longer the arm being
measured. That doubles the ladder's runs — one for cost, one for accuracy, same arm, same start,
same tolerance — and the audit runs are cheap because they stop after one evaluation. The post-run
audit is kept and reported, because *"all three arms return a bit-exact fixed point"* is itself
worth knowing.

### 5.2 The ladder mixed populations, twice

A rung that keeps one start and a rung that keeps two are two different populations, and a curve
built from both is a curve of the population as much as of the arm. Fixed by computing the starts
**every rung of both arms kept** and restricting every rung to them. Then a second problem: on
`st_regression` two rungs kept *no* start, which emptied the intersection and deleted the whole
comparison. A rung that solves nothing is a **failed rung** and is now named as one and excluded
from the intersection, rather than being allowed to delete the comparison.

Both were caught by reading the output, not by a gate. The ladder has no gate of its own, which is a
gap I am recording rather than fixing.

### 5.3 The campaign was interrupted at 173 of 300 by the run environment

Not a run failure. `--resume` was added, which skips only runs with a **complete, driver-stamped**
record — a directory alone is not evidence of a completed run — and the campaign continued. No run
was re-measured. One consequence is recorded rather than elided: the sequence-position counter
restarts per driver invocation, so timing sequence positions are comparable within an invocation and
not across the interruption.

---

## 6. Autonomous decisions, each with its reversal path

| # | Decision | Why | Reversal |
|---|---|---|---|
| AD1 | **A0′ takes the upstream node order**, and a separate diagnostic arm measures the transposition | Makes `R → A0′` vary the stopping rule and nothing else, which is what D18 asks of it. The transposition is then measured rather than left as a caveat — at exactly zero on all three decks (§3.5) | One line in `run_a28.env_for`; the diagnostic arm's runs already exist |
| AD2 | **The single-block outer-pass guard**, evaluated from the schedule actually built | A26 §10 item 1. Without it A0′ pays one wasted full sweep per optimiser evaluation and is not the degenerate case it is claimed to be | `caller._single_block_covers_loop` returning `False`; every run records whether it fired |
| AD3 | **The accuracy measure is an audit at the first optimiser evaluation, not after the run** | §5.1: the post-run audit reads 0 for every arm | `--exit-audit-at-call`; both audits are recorded |
| AD4 | **Phase B runs on A18's coupling-state artifact, not A26's no-exclusion one** | Continuity with the run being replaced: differences are then attributable to the third arm and the instrument fixes rather than to a predicate swap. A26 measured the swap as changing no Phase A count at three floors | The A26 artifacts are committed; the per-module write sets would need their spec hash re-stamped, which is a data step and not a run. **§1.4(1) says why this should be reversed in a successor task** |
| AD5 | **The matched-accuracy robustness re-run was done on `st_regression` only** | It is the only deck where a matching setting exists *and* the verdict could move: `large_tokamak_nof` has no setting at which the arms are equally converged, and on `low_aspect_ratio_DEMO` they already are | 25 runs per additional deck; the ladder gives the setting |
| AD6 | **A single-block schedule's label is canonicalised in the manifest descriptor** | A one-block schedule's label carries no information, and encoding a naming choice as a structural difference makes the descriptor lie (§3.2) | One constant in `a28_analysis.descriptor`; multi-block labels are untouched |
| AD7 | **`R` is described in the manifest as a single iterated block at tolerance 1e-6** | Because that is what it is: one flat sweep repeated until it stops moving, with `np.allclose`'s own rtol. Describing it otherwise would manufacture a structural difference from D18's actual claim | `a28_analysis.descriptor`; the observed differing keys are printed in every manifest record |
| AD8 | **A tooth that cannot bite is reported NOT APPLICABLE, not as a pass** | A26 §7.1's shape: a gate whose watched quantity is never exercised is an assertion | The four are named in the sensitivity record with the reason |
| AD10 | **A harvest's *file* hash no longer aborts a replay; its *content* hash still does** | `gen_ystate.harvest_identity` computes two hashes and its own docstring says which matters: the content hash covers the coupling-key set, the model sequence and every design point's identity and design vector as exact hex floats and "changes if and only if the harvest is a different measurement"; the file hash covers `pickle`'s byte layout. `replay.py` treated **both** as fatal, which made a from-scratch reproduction impossible — a freshly recorded harvest of the same run aborts on byte layout while its content hash and the categorisation hash both agree. Found by running the entry point from scratch. A file-hash difference is now recorded in every result file rather than hidden | Two lines in `replay._check_ystate`. **Verified inert against the recorded harvest**: the A26 reproduction gate still passes at 0 differing of 2 360 arm records over 30 680 keys, 12/12 sensitivity, after the change |
| AD9 | **`--runs` overrides added to `run_phase_a.py` and `run_a26.py`** | A from-scratch reproduction must be able to write where the caller chooses; and in a worktree `runs/a18` is a symlink into the main checkout, so a rebuild would overwrite the shared recording every other task replays. The entry point **refuses** to rebuild through such a symlink | Both default to the previous paths, so every existing invocation is unchanged |

---

## 7. What I did not do

- **No physics change and no `process/models/` change at all.** A24's `pulse.py` extraction is the
  only one in the experiment and is untouched. D11's approval gate was not reached.
- **I did not re-run Phase B on A26's no-exclusion predicate** (AD4). §1.4(1) measures why it
  matters — 24 % of one deck's solves have a false constant moving — and it is the largest single
  caveat on these numbers.
- **I did not run a matched-accuracy robustness comparison on all three decks** (AD5), and on one it
  is structurally impossible.
- **I did not thicken the Phase B ladder.** Two starts per rung is not a distribution, and on one
  deck it yields no curve at all.
- **I did not tune anything after seeing a result**, and where a re-run at a different setting was
  made, both readings are reported side by side with the tolerance each was measured at named.
- **I did not edit `MASTER_TODO.md`.** It is the orchestrator's file.
- **I did not merge and did not push.**
- **No conclusion rests on a timing.**

---

## 8. Reproduction

```bash
W=/home/wrutten/projects/PROCESS_surgery_worktrees/A28-phase-b-rerun
PY=/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python

# everything, from one entry point
$PY $W/MDA_partition_opt_experiment.py --quick        # smoke, one deck, minutes
$PY $W/MDA_partition_opt_experiment.py                # the full campaign
$PY $W/MDA_partition_opt_experiment.py --verify       # against the published numbers

# or stage by stage
R=$W/arch_surgery/idf_probe/runs/a28
$PY $W/arch_surgery/idf_probe/run_a28.py decks     --runs $R
$PY $W/arch_surgery/idf_probe/run_a28.py gate      --runs $R --arms R A0p A1p A0p_reordered A1p_nohoist
$PY $W/arch_surgery/idf_probe/run_a28.py calibrate --runs $R --starts 12
$PY $W/arch_surgery/idf_probe/run_a28.py campaign  --runs $R --arms R A0p A1p A1p_nohoist --starts 24 --delta 0.10
$PY $W/arch_surgery/idf_probe/run_a28.py audit     --runs $R --arms R A0p A1p --starts 24 --delta 0.10
$PY $W/arch_surgery/idf_probe/run_a28.py ladder    --runs $R --ladder-starts 2 --delta 0.10
$PY $W/arch_surgery/idf_probe/a28_analysis.py all  --runs $R --arms R A0p A1p A1p_nohoist
$PY $W/arch_surgery/idf_probe/a28_tables.py        --runs $R
```

Raw artifacts stay untracked under `arch_surgery/idf_probe/runs/`; the numbers in this report are
the committed summary.

**What it costs, measured rather than estimated**, on this machine (16 cores, 7 GB; above five
parallel jobs it competes for memory rather than cores), three decks, 25 starting points:

| stage | runs | minutes | disk |
|---|---|---|---|
| derive the lifted decks | 2 | 1 | 1 MB |
| switch neutrality *(needs `--parent-tree`)* | 16 | 5 | 250 MB |
| gate, five arms | 15 | 4 | 85 MB |
| δ calibration | 108 | 27 | 1.1 GB |
| the campaign, four arms | 300 | 75 | 3.5 GB |
| accuracy census | 225 | 6 | 30 MB |
| ladder, cost + audit | 168 | 55 | 1.7 GB |
| **total** | **834** | **≈ 175** | **≈ 7 GB** |

`--quick` is one deck, three arms, three starting points and a two-rung ladder: **≈ 8 minutes**,
75 MB, and it exercises every stage including every gate and every sensitivity check. Phase A's
entry point is **≈ 105 minutes** from scratch (most of it recording the design points) and
**≈ 13 minutes** under `--quick`.

**Both entry points were run end to end before this report was written.** Phase B: `--quick` on
every stage, and the full path for every number quoted. Phase A: `--quick` on every stage, from
scratch on one test case — and it **reproduces A18's published in-loop model-evaluation counts
exactly**, 9 471 / 9 471 / 9 618 / 13 906 for R / A0 / A0f / A1 on `large_tokamak_nof`, having
recorded its own design points rather than reading the committed ones. The full three-deck Phase A
path was **not** re-run end to end from one command; its `method_gate` and `accuracy` stages were
run in full on all three decks (§1.3a), and its `phase_a`, `census` and `permutation` stages were
run in full only on one test case under `--quick`. That is stated rather than implied.

---

## 9. Change log (append-only)

| # | Date | Change |
|---|---|---|
| 1 | 2026-09-02 | Worktree confirmed at `dc18c05b`, `arch_surgery/` present. `CLAUDE.md`, `TRAPS.md`, A26 (especially §11), `MASTER_TODO` D14/D15/D17/D18 and I-10/I-12/I-13, plan §2.5/§4.1a–e/§7a, A25 and the standing results report read. |
| 2 | 2026-09-02 | `module_solve.py` gains the `flat_state` arm and `PROCESS_ARCH_INNER_TAU`; `caller.py` gains the single-block schedule branch and the outer-pass guard A26 §10 named. |
| 3 | 2026-09-02 | `run_one.py` gains the exit audit (post-run and at a chosen evaluation), the I-12 entry census, the per-node cost-unit census and the resolved-schedule record. |
| 4 | 2026-09-02 | Switch neutrality against `dc18c05b`: **0 of 91 882** quantities per mode, probe off and on; every tooth bites. `tests/unit` 843 passed. |
| 5 | 2026-09-02 | **The manifest gate refused `R → A0′`** on a cosmetic label difference. Descriptor fixed, gate stage re-run, 10 of 10 pairs PASS on 3 decks. |
| 6 | 2026-09-02 | **Protocol §12 found a defect in this task's own model-set gate** — the call-site extraction missed the three head models because `_SEQUENCE_HEADS` is an annotated assignment. Fifth consecutive task. Fixed, and the check now refuses to report a figure at all if the table does not parse. |
| 7 | 2026-09-02 | Equivalence gate **PASS 12 of 12**; 28 of 28 teeth bite, 4 reported NOT APPLICABLE rather than counted. δ calibrated over 108 runs: **10 % on all three decks**, reproducing A25 cell for cell. |
| 8 | 2026-09-02 | Campaign: 300 runs, 4 arms × 25 starts × 3 decks. **Interrupted at 173 by the run environment**; `--resume` added and the campaign continued with no run re-measured. |
| 9 | 2026-09-02 | **The post-run exit audit reads exactly 0 for every arm** — the output path re-converges. Replaced by an audit at a chosen optimiser evaluation that stops the run. |
| 10 | 2026-09-02 | Ladder, 168 runs. **Two population defects found by reading the output**: rungs summed over different starts, and rungs that kept no start emptying the common set. Both fixed in the analysis; no re-run needed. |
| 11 | 2026-09-02 | Coordinator: the envelope's asymmetry must be addressed in the report, not declared in JSON. **Matched-count envelope** implemented for both phases, convexity **measured** rather than assumed, tuning premium reported: **1.000** on one deck, **0.988** on another. |
| 12 | 2026-09-02 | Coordinator: robustness is compared at fixed τ while cost is compared at matched achieved accuracy. **Accuracy census** over 225 cheap audit runs: the variant ends strictly more converged on 20 of 22 and 25 of 25 starts and never less. |
| 13 | 2026-09-02 | **Matched-accuracy robustness re-run on `st_regression`**, at the inner tolerance the ladder names: the deficit disappears (23 vs 23) and the cost advantage shrinks from −6.18 % to −2.27 %. Both readings reported. |
| 14 | 2026-09-02 | **Phase A's ladders regenerated** (A26's artifacts are gone, I-14) and its reproduction gate re-taken at this tip: **0 differing of 2 360 arm records over 30 680 keys**, 12/12 sensitivity cases caught. The matched-count envelope then **disagrees in sign with the all-settings one on two of three decks**: +33.4 % / +27.4 % / −15.2 % against −4.3 % / −4.5 % / −13.1 %. A defect in the envelope construction was found and fixed doing it — zero-residual rungs were excluded from the envelope as well as from the fit — which changes no all-settings number. |
| 15 | 2026-09-02 | **A `--quick` run from scratch found two defects the recorded-artifact path cannot reach.** (i) The equivalence gate's cross-deck tooth needs two decks and crashed on one — now reported NOT APPLICABLE with its reason rather than crashing or silently passing. (ii) **A replay aborts on a harvest's *file* hash**, which the instrument's own docstring calls meaningless, making a from-scratch Phase A reproduction impossible; the content hash and the categorisation hash both agreed. Made non-fatal and reported; the reproduction gate re-run after the change still passes 0 of 2 360. |
| 16 | 2026-09-02 | Standing results document rewritten: correction banner resolved and removed, §4.4.2 / §4.5(b) / §6.1 / §6.3 / §6.5 updated, §5.5 / §6.6 / §6.7 added, §7 rewritten from "not built" to Phase B's method, gates and results, abstract and conclusion rewritten. |
