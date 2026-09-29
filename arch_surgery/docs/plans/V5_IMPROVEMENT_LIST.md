# V5 improvement list — method changes for a fifth experiment revision

> **Document status** — **CURRENT · PLANNING INPUT.** Opened 2026-09-15 from the user's review of
> the V4 method with task **A77 (v5-check2-decomposition)**, on the executed and reported V4
> experiment ([`EXPERIMENT_REPORT.md`](../../MDA_partitioning_experiment_v4/EXPERIMENT_REPORT.md),
> campaign records at `57dc0c14`, document at `14342a72`). Same convention as
> [`V4_IMPROVEMENT_LIST.md`](V4_IMPROVEMENT_LIST.md): **this is a list of candidate design changes,
> not a plan.** Nothing here is decided, and a V5 experiment plan would restate its selections with
> pre-declared acceptance rules. Nothing here may be applied to the V4 harness or its report — V4's
> campaign is measured and published, and a rule changed after the numbers is not a check. Arm
> names in item 1 are the V4 report's at `14342a72` (`BR / B0 / B1 / B3`), the names of its day;
> **A78 (arm-renames) renamed `B3` to `B2` (and `A0p`, `A1` to `A1`, `A2`) throughout the V4 folder on
> 2026-09-15** — the `B3` below is today's `B2` — and a V5 plan uses the names that stand when it is written.

## Design of the comparison

### 1. Retire check 2 (the iteration multiplier) as an acceptance rule; publish the decomposition `R = ρ × ε` as the result *(user, 2026-09-15)*

**The concern, in the user's words:** *"I think this iteration multiplier, if it fires, imposes a
statistical bias."* Check 2 accepts an arm pair when the nearest-rank median of the paired
optimiser-iteration ratio (summed over VMCON attempts) is **≤ 1.05** (V4 report §3.5 check 2). It
exists to control the trajectory term: a cost ratio is read as a per-evaluation saving only if the
optimiser took the same path.

**Where the bias actually sits.** A `FAIL` on check 2 selects nothing: the cost population is
"every arm converged", chosen independently of check 2, and the rules forbid retuning (protocol
§6). So the check *firing* biases no number. The bias is in the check **not firing**: the bound is
one-sided. A trajectory that gets *shorter* passes, and its saving is folded into the headline cost
ratio and read as a per-evaluation saving. V4 measured exactly this case:

- `low_aspect_ratio_DEMO`, `B0 → B1` (§4.3 "iteration multiplier"): summed-iteration median
  **0.8125**, sum ratio **0.7012**, verdict **PASS**; the same numbers for `B0 → B3`, since the
  partition leaves the path unchanged. The headline `B3/B0 = 0.450` pooled (§4.3 "cost") carries
  that 0.70–0.81 trajectory factor inside it and is stated as the cost of the architecture.
- `large_tokamak_nof` and `st_regression`: 1.0000 / 1.0000 — no trajectory change, no attribution
  problem.

The report mitigates this by publishing ε beside (the transfer statement of §3.5, §5.2) and by
stating in §5.1 that lad's lift *"also shortens the optimiser's path"*; but the acceptance rule
itself is asymmetric in the intervention's favour, and a reader who takes the verdict column at
its word is told the trajectory was controlled when it was only bounded from above.

**A second reason the rule is weak.** A43 (st-trust-gap) P2 measured the same 23 st pairs at
1.17, 0.91 and 1.07 under three constructions of "iterations"; V4 resolved that by *declaring*
one (summed over attempts) before its campaign, which is correct pre-registration, but the
declaration was chosen with V3's numbers in view. A rule whose sign is that sensitive to its
construction is a poor thing to hang a verdict on and a fine thing to publish as a number.

**The change.** Check 2 stops being an acceptance rule. The optimisation phase's cost table
publishes, per arm pair over the one seed set, the **decomposition the transfer already states**
(§3.5): with `N` solve-phase node calls and `C` optimiser evaluations (`call_models` calls),

    R  =  N_arm / N_base  =  (N_arm/C_arm) / (N_base/C_base)  ×  C_arm / C_base  =  ρ × ε

- **ρ**, the per-evaluation cost ratio — what an evaluation of the model set costs under the arm
  against the base; the quantity the architecture changes;
- **ε**, the evaluation-count ratio — how many evaluations the optimiser took; the trajectory
  term, which the architecture is *not* meant to change (pre-declared expectation for
  `B1 → B3`: exactly 1 on the pulsed configurations; for `B0 → B1`: `(nvar + 2)/(nvar + 1)` from
  the lift's extra stencil column, plus whatever the lift does to the path);
- **R**, the pooled node-call ratio already published, with the identity printed per configuration
  and its residual (zero by construction on pooled sums; the per-run median of `ρ` times the median
  of `ε` need not equal the median of `R`, and the table says which construction each cell is).

**Neither factor is gated.** The sentence V4 makes from a verdict — *"the partition changes what an
evaluation costs and not how many the optimiser takes"* — is made from ε directly: on the pulsed
configurations `ε(B1 → B3) = 1.000` reads it off the page. If a classification is still wanted, it
is **two-sided and a label, not a verdict**: `|log ε| ≤ log 1.05` → *trajectory-neutral*, otherwise
*trajectory changed by ε*, and a changed trajectory is a finding published beside ρ rather than a
reason to accept or reject. The two iteration constructions (summed over attempts, final attempt)
stay in the table as context for the trajectory, with the retry readings, exactly as V4 publishes
them; they just carry no `PASS`.

**Prerequisite — a defect in V4's own ε column, found while writing this item.** V4's check-2
table already carries an *evaluations median* column meant as ε (caption: *"the evaluation-count
ratio is beside both"*). It is built from the record field `n_model_calls`
(`tally_optimisation.py`, the `evaluation_ratios` loop), which the record schema describes as
*"evaluations of the model set the optimiser asked for"* but which is `numerics.n_model_calls` —
**sweeps** of the dispatch body, the very quantity the driver's counter docstring says *"is not
comparable between a flat loop and a block schedule"*. On `large_tokamak_nof` seed 1 the records
read `n_model_calls` = 2 074 / 2 100 / 5 498 for `B0 / B1 / B3` against `sweeps_per_eval.n_evaluations`
= 630 / 660 / 660; the published column therefore reads **2.65 / 2.12 / 2.78** for `B0 → B3`
(nof / lad / st), which is the sweep ratio §5.1 correctly describes as *"the dispatch runs 2.7 / 2.1 /
2.8 times as many sweeps"*, under a heading that says evaluations. The evaluation-count ratio from
the right field is 660/630 = 1.048 = 22/21 for both `B0 → B1` and `B0 → B3` on that seed — the
lift's stencil column, as pre-declared — and exactly 1 for `B1 → B3`. No V4 verdict rests on the
column (it is "beside"), and §5.2's transfer factors are computed from node calls; but a reader of
the table is misled, and a V5 decomposition must read `sweeps_per_eval.n_evaluations` (the count of
`call_models` entries) for `C`. Relabelling or refilling that column in V4 is a tally correction on
the V4 data, to be minted as its own task, not a V5 item; it is recorded here so the V5 construction
does not inherit the field.

**A related hazard, proposed by the agent — answered by the user 2026-09-15** (*"D22 - the conclusion was to keep. that is fine for v5 as well"*, confirmed in the orchestrating session): **`st_regression` stays in V5 unconditionally, as in V4**; the configuration set is declared without a drop rule. The hazard as written, for the record: D22 made `st_regression`'s place
conditional on an outcome (*"if A43 shows st's trust-mode `B3` unreliable, st is dropped"*). It did
not fire, but a configuration dropped on a measured outcome is a selection at configuration level —
the same shape as a one-sided rule, one grain coarser. A V5 plan should either declare configuration
membership unconditionally or declare the drop rule, its statistic and its threshold before the
campaign and publish the statistic whether or not it fires.

**What is *not* claimed.** That the one-sided bound changed any V4 verdict — every check-2 cell
`PASS`ed — or any V4 number: the cost tables already publish the ratio with and without the retried
seeds and the report states lad's trajectory change in prose. The bias is in *attribution* (what
the headline ratio is said to be the cost of), not in the data, and the fix is to stop gating on
the trajectory and print its factor.


### 2. The partition's saving by block — M2 is solved about as often as the flat arm sweeps it *(arising from A79 (report-captions), 2026-09-15; not the user's)*

The per-module optimisation-phase split (V4 report Tables D.2–D.4) and the per-block evaluation split (Table D.7) show where the saving is *not*: the coils block M2 reads `B2/B0` 0.87 / 0.59 / 0.67 pooled with a per-run median of 0.8765 on the large tokamak and one run above 1, and `A2/A1` 1.0078 / 0.9919 / 1.0000 per evaluation — the block is iterated as often as the flat loop swept it. The saving sits in the plant block (0.51–0.61), the pulse node (0.20) and the once-per-run nodes (0). A V5 partition should take this as a design input: either M2's own fixed point is as expensive as the flat sweep because its coupling is the loop's real work, or the block boundary is drawn through it; a per-block census of M2's internal residual would say which before a new schedule is proposed.

---


### 3. Reliability as a published measure — per-arm success rate over every start, and data profiles *(user, 2026-09-15, D29 (1), from A81 (benchmarking-practices) F1)*

The benchmarking literature (Beiranvand, Hare & Lucet 2017 §4.2) counts failures against the algorithm; V4 filters them into a seed set on which every arm converged and states the set's size (22 / 11 / 22 of 25) but not each arm's rate. On the low-aspect-ratio machine the intervention arms fail one start the flat arms solve (seed 10); on the spherical tokamak two failures are asymmetric and cancel in count, not in cost. A V5 plan declares the success rate per arm over all starts (denominator: starts offered) as a published measure with its own pre-declared expectation, and publishes a **data profile** per configuration (fraction of starts solved within a node-call budget, one curve per arm) beside the medians and brackets — constructible from the records, no extra run. A82 (per-arm-success) adds the table to V4 as a descriptive cell; the profile and the expectation are V5's.

### 4. Verdict sensitivity — the same-optimum floor and factor re-tallied at neighbouring values *(user, 2026-09-15, D29 (1), from A81 F5)*

V4's `lad` same-optimum FAIL sits at 2.15× the 1e-6 floor with the factor F at one value. A V5 plan pre-declares the verdict at the chosen setting **and** publishes the re-tally at neighbouring settings (F ∈ {3, 10, 30}; floor ∈ {1e-7, 1e-6, 1e-5}) so a reader sees whether a verdict is a threshold artefact — the tally can produce the grid from the records at no run; only the declared cell is a verdict.

### 5. Phase A charges the partitioned arm its one execution of the once-per-run nodes *(user, 2026-09-28)*

**The concern, in the user's words:** *"If phase A is a single evaluation run, it should converge
the MDA and then run all these other models exactly once right? Otherwise it doesn't produce the
same information as the reference case."* V4's phase A measures one `call_models` evaluation, and
its census stops before the exit audit's uncharged sweep. The flat arms (`AR`, `A0`, `A1`) run
the once-per-run nodes (`costs`, `vacuum`, `water_use`; plus `pulse` on `st_regression`) in every
sweep, so their final sweep computes those outputs at the converged state. The partitioned arm
`A2` defers them to the output pass, which phase A does not have. So its measured evaluation runs
them **0** times and leaves their outputs uncomputed (campaign record `large_tokamak_nof` seed 1:
`A0` counts 6 of each, `A2` none). V4's Table 9 prints that 0, so its once-per-run row compares two
evaluations that do not produce the same information. Item 2's "the once-per-run nodes (0)" reads
the same cell.

**The change.** A V5 phase A evaluation is the MDA converged, **then every deferred node executed
exactly once**. The run actually executes them, and the census counts that execution like any
other: it is **measured, not charged** (the user, 2026-09-28: *"In v5 it should be in the
measurement (it should actually run once)"*). The accuracy check's
restricted audit, which currently excludes the components those nodes write, should then be
reconsidered: with the nodes executed, their components can be audited like the rest.

**What V4 does meanwhile.** Nothing in V4's report or harness changes. The paper tables
(`MDA_partitioning_experiment_v4/paper_tables.md`, `harness/measurement/paper_tables.py`) charge
`A2` that one execution **by construction**: 1.0 in its post-processing cell, so `A2/A0` there is
0.18 / 0.20 / 0.17 rather than 0. They check on every run that the measured count is 0, and cite
phase B's whole-run census (`B2` reads 2 per run: the output pass and the exit audit) as the
measurement showing that the deferred pass is a single execution.

### 6. The control's MDA: stop on the coupling variables, at a tolerance derived from the optimiser *(user, 2026-09-29, from A89 (coupling-subset-trial))*

**The concern.** V4 stops every loop on the whole measured state `y`: every field an in-loop model
writes (840 / 846 / 827 components). The textbook MDA converges only the variables that carry
information from one sweep to the next, and evaluates everything downstream once they are fixed.
V4's tolerance τ = 1e-6 was also never derived from the optimiser it serves. The user wants a
proper MDA for the control, without acceleration or Newton, so that the paper isolates the
architecture change.

**What A89 measured** (evaluation phase, three configurations, `A0` and `A2`, displaced and cold
entries; report `reports/deprecated/A89_coupling_subset_trial.md` §3 and §7):

- **Two candidate test sets.**
  - (a) **DSM feedback set**: a component of `y` read by a DSM model that runs before its writer
    in the DSM's execution order (75 / 73 / 53 components).
  - (b) **census-measured set**: a component read before its first write within a sweep of the
    arm's own execution order, per block, measured at run time (73–75 in the flat loop; 16 / 46–47
    / 10 in M1 / M2 / M3).
  - Under half of (b) is in (a). (b) contains 26–28 components that a model reads from its own
    previous sweep, which the DSM cannot classify. 30–41 of (a) are never read before written at
    run time.
- **A tolerance derived from the optimiser.**
  - VMCON's central-difference step h = `epsfcn` = 1e-3 balances against function noise ε ≈ h³ =
    1e-9 (Gill, Murray & Wright).
  - Measured on the optimiser's own stencil, the census-set control first meets that bound at
    **τ = 1e-8** in every configuration. At 1e-6 the error reaches 2.8e-8.
  - V4's whole-`y` test meets it at 1e-6 only because it stops one sweep late.
- **At τ = 1e-8** (54 runs):
  - Set (b) ends every run with 0 whole-`y` components above τ.
  - Set (a) fails once: `large_tokamak_nof` cold `A0`, where `costs.coecap` is 1.47e-8 at exit.
    The loop stopped a sweep early while carried `pf_coil.*` components outside (a) were still
    moving.
- **Cost.** At matched accuracy, the census set costs about what V4's lagging whole-`y` test at
  1e-6 costs: −1 % / −5 % / −2 % node calls over the stencil. Its gain is correctness by
  construction and a cheaper check. The coupling-state check is 38–39 % of an evaluation's wall
  clock in V4's control and 7–8 % with the census set (context, not evidence).

**Ruled — D32 (the user, 2026-09-29): V5 converges on the census-measured feedback variables.**
*"The motivation is that the DSMs are not accurate enough to make this judgement, and suffer from
the models not being strictly functional"* (V18, V19). Option 2 below is the test; option 1 stays
as a cross-check the plan reports beside it, never as a stopping rule. **The text of the two
options as first written, for the record:** a V5 plan carries two candidate
definitions of the control's (and, per block, the partitioned arm's) convergence test:

1. the **DSM feedback set** (static, from the dependency analysis, in the DSM's order);
2. the **census-measured read-before-write set** (runtime, in each arm's own order and blocks).

Both use **τ from the declared rule ε ≤ `epsfcn`³**, re-measured on V5's configurations before the
campaign (1e-8 on V4's), and both keep the whole-`y` exit audit as the accuracy instrument. The plan
declares which option is the control, or runs both as rungs, before any number exists.

**What each option still needs before it can carry a verdict:**

- (1) a gate with teeth showing that the missing-variable failure A89 found is caught. It failed
  once in 12 A89 runs at 1e-8.
- (2) a census over an optimisation run's evaluations, not only 8 displaced entries per
  configuration and arm, since branches taken only on the optimiser's path go unobserved. Plus a
  gate with teeth: drop one carried component and the audit must fail.
- Both: the feed-forward and once-per-run nodes executed once after convergence in every
  evaluation-phase arm (item 5, extended by the user on 2026-09-29 to all A arms).
- Both: the per-sweep dispatch overhead of the partitioned path named beside any node-call ratio.
  In A89, `A2`'s wall-clock ratio against `A0` is 0.77–1.01 where its node-call ratio is 0.43–0.60
  (context).
- Both: the optimisation-phase effect of the tighter tolerance, which A89 did not measure.

**Cost, and why the test must be narrowed in both arms before wall clock is compared** *(the user,
2026-09-29, from A89 §7.5 and A91 (block-sweep-timing) §5; timings are context, never evidence)*.
The convergence test costs about 5 µs per component tested whichever block (A91), so its cost
scales with the test set: on `large_tokamak_nof` the whole-`y` test is 31 ms of a flat evaluation
and 20 ms of a partitioned one, the census set 4.6 and 4.9 ms (A89 §7.5). Narrowing the test
therefore removes most of the *advantage* the partition showed in that term. What remains is
model time — 38.8 ms flat against 27.6 ms partitioned on `large_tokamak_nof` (A91 §5: the sweeps
the partition saves are M3's cheap ones; M1 and M2, ≈ 2.8 ms a sweep each, are swept about as
often as before) — and the deferral machinery's own cost, which is not intrinsic: the driver copy
re-derives the deferral sets on every evaluation (8–11 ms, issue I-30). Projection from those
measured terms: with the census test in both arms the partition's wall-clock ratio is ≈ 0.97 as
implemented and ≈ 0.77 with I-30 fixed, against a node-call ratio of 0.50 — because node calls
weight every model equally and PROCESS's cost sits in a few physics and coil models. Two
consequences for the plan: **(i)** I-30 is a prerequisite for any wall-clock statement, and
**(ii)** the paper states the model-time ratio beside the node-call ratio, with the reason.

**A third option assessed and set aside: function-level (SCC) decoupling from the expanded DSM**
*(the user's question, 2026-09-29; `coupling_subset_trial/derive_function_level_sets.py` →
`function_level_sets.json`, read-only over the sibling's exports with digests)*. At submodel level
(417 functions on the tokamak) the DSM's graph over `y` has 7 strongly connected components (the
largest 39 functions). Any sequencing's tear set is a subset of the components carried by edges
inside those SCCs: 122 / 119 / 98 on nof / lad / st. That set is **larger** than both the model-level
feedback set (75 / 73 / 53) and the census cut set (75 / 74 / 73), and it **misses 36 / 37 / 41 of the
census's components** — 12 of the 36 on nof are read only by the function that writes them (a
self-read the DSM cannot classify at any level), the other 24 are read by a function the static
order puts after the writer but which, at run time, reads the previous sweep's value. Function-level
feedback in the code order, without sequencing, is 146 / 144 / 128 and misses 32 / 32 / 40. So the
finer DSM comes no closer to the carried set than the coarser one: the gap is not granularity but
the difference between a static read set and what a sweep actually reads before it writes. The
DSM-based option in this item is therefore the model-level feedback set as defined; a function-level
set is not a candidate unless a runtime read census is folded into it, at which point it is option
2.

### 7. The deferral sets are derived once per run, not on every evaluation *(the user, 2026-09-29, from A91 (block-sweep-timing), issue I-30)*

**The concern, in the user's words:** *"is this actually an architectural change? We run the same
models still right, only the experiment execution is more accurate in wall clock time because we
remove unnecessary overhead introduced by the experiment harness that wouldn't be there if you
actually implemented the order manually. If that is the case, this should be fixed in v5."*

**What it is.** The driver copy re-derives which nodes are deferred on every `call_models` —
`_predicate_read_fields` walks the objective and constraint sources with `ast`, `_node_write_sets`
re-reads `node_writesets.json`, and `Caller._resolve_defer_per_call_tails` calls both each time
(its comment: "re-resolved on every call rather than memoised") — 8–11 ms per evaluation in every
deferring arm (`A0` with deferrals, `A2`, `B1`, `B2`), 0 in the arms without deferral (A91 §5;
I-30). It is not the architecture: the models, their order and every count are identical with or
without it; a driver written for the partitioned order would resolve the schedule once at start-up.
It is an implementation cost that falls on the intervention arms only, so it biases every
wall-clock comparison against them.

**The change.** In V5's driver copy the deferral sets (and the block schedule) are resolved **once
per run** — at `Caller` construction or on first use, keyed on the figure of merit — and reused for
every evaluation. Requirements: no count changes (node calls, sweeps, predicate evaluations,
components compared identical to the digit on a gate job set, both phases); the switch-neutrality
gate G1 byte-identical with every switch unset; the resolution's provenance stamped once per run
as it is stamped now per call. A driver change: the user has said it should be fixed in V5, and
the ruling is recorded here as the user's instruction; the decision row D31 is ruled (the user, 2026-09-29: *"D31 also stands"*). Any other per-evaluation cost the instrument adds unequally to the
arms — A91 measured the block-sweep dispatch (0.08–0.09 ms) and found it negligible, and A89 the
whole-state read per sweep (small) — is checked the same way before V5's wall-clock table exists.

*Candidates proposed elsewhere and not yet listed here:* A76 (fixed-point-distance)'s report §7 (d)
notes that the between-arm fixed-point distance it added to V4's §4.2 as a reported statistic could
carry a pre-declared acceptance rule in a V5 plan (a natural form: headline median and p90 below τ,
0 pairs above τ). Whether it becomes an item is the user's call.
