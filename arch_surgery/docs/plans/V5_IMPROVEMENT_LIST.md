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
>
> **Trimmed against the paper's purpose, 2026-09-29 (the user's rulings on the orchestrator's assessment).** The paper
> (`Structuring-fusion-MDAO-with-DSMs/3 results.tex`) claims an existence proof in **model-evaluation counts** — the
> main result, because the argument is that the real impact is for models of higher computational cost — with
> **wall clock in the appendix** and a quantified sentence in the main text, and it **keeps its optimiser-iterations
> table**. Under that: item 1 stands (its stated prerequisite was already resolved); item 2 is **closed** (A90);
> item 3 is reduced to the descriptive per-arm success table, done only when needed; item 4 is reduced to the
> statistic and its attribution; items 5, 6, 7 stand; the A76 candidate is **dropped**; items 8 (the prime as
> pre-processing) and 9 (wall clock as a declared measurement) are added; the phase A entry regime stays the
> hostile δ = 0.10 for the paper's table (the user: *"I like the hostile 10 % for the paper results. We see the actual
> result in phase B anyway."*); **the phase A table prints `A2/A1`** on the pulsed configurations (`A2/A0` on st),
> the matched-accuracy pair at the same fixed point (**D34**, the user, 2026-09-29).

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
does not inherit the field. *(Struck 2026-09-29: A80 (report-accuracy-audit) closed issue I-26 the same day this
was written — the column reads `sweeps_per_eval.n_evaluations` (V4 report Table 13) and the old ratio is kept
beside it as "sweeps median"; no task is needed.)*

**The paper's use of it (the user, 2026-09-29).** The paper keeps its optimiser-iterations table, which is ε in
the paper's terms; the module-evaluation tables remain the main result. On `lad` the module ratio `B2/B0`
(0.47–0.59) contains the shorter path (0.70 sum, 0.81 median iterations), and the paper says so in one sentence.
V5 prints ρ beside the iterations so that sentence is a number; the check-2 rule goes as above.

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


### 2. The partition's saving by block — M2 is solved about as often as the flat arm sweeps it *(arising from A79 (report-captions), 2026-09-15; not the user's)* — **CLOSED 2026-09-29**

**Closed by A90 (m2-phasea-vs-phaseb), merged `f2bb2e6e`; the user, 2026-09-29: "agreed, not relevant for v5 anymore."**
M2 binds the flat loop only on the finite-difference probes that move geometry or magnet variables (binding
share 0 or 1 per variable and sign on 42/42 pairs on the large tokamak); in phase A the δ displacement disturbs
every module, so the partition saves nothing on M2 there; in phase B `B2`'s M2 sweeps equal M2's own settle
count in the flat loop on every paired evaluation (1980/1980, 5250/5250, 90/90). No block boundary is
redrawn. The paper's phase B paragraph already states the mechanism. The text as first written, for the record:

The per-module optimisation-phase split (V4 report Tables D.2–D.4) and the per-block evaluation split (Table D.7) show where the saving is *not*: the coils block M2 reads `B2/B0` 0.87 / 0.59 / 0.67 pooled with a per-run median of 0.8765 on the large tokamak and one run above 1, and `A2/A1` 1.0078 / 0.9919 / 1.0000 per evaluation — the block is iterated as often as the flat loop swept it. The saving sits in the plant block (0.51–0.61), the pulse node (0.20) and the once-per-run nodes (0). A V5 partition should take this as a design input: either M2's own fixed point is as expensive as the flat sweep because its coupling is the loop's real work, or the block boundary is drawn through it; a per-block census of M2's internal residual would say which before a new schedule is proposed.

---


### 3. Reliability as a published measure — per-arm success rate over every start, and data profiles *(user, 2026-09-15, D29 (1), from A81 (benchmarking-practices) F1)*

The benchmarking literature (Beiranvand, Hare & Lucet 2017 §4.2) counts failures against the algorithm; V4 filters them into a seed set on which every arm converged and states the set's size (22 / 11 / 22 of 25) but not each arm's rate. On the low-aspect-ratio machine the intervention arms fail one start the flat arms solve (seed 10); on the spherical tokamak two failures are asymmetric and cancel in count, not in cost. A V5 plan declares the success rate per arm over all starts (denominator: starts offered) as a published measure with its own pre-declared expectation, and publishes a **data profile** per configuration (fraction of starts solved within a node-call budget, one curve per arm) beside the medians and brackets — constructible from the records, no extra run. A82 (per-arm-success) adds the table to V4 as a descriptive cell; the profile and the expectation are V5's.

**Reduced 2026-09-29 (the user: *"do it only if it is not too much over-engineering. I'm not planning to make claims about robustness … We do it when it is necessary"*).** V5 keeps A82's **descriptive per-arm success table** (it explains the paper's n per configuration and names the one start lost to the intervention arms alone) — no data profile, no pre-declared expectation, no robustness claim. Nothing else of this item is built unless a claim needs it.

### 4. Verdict sensitivity — the same-optimum floor and factor re-tallied at neighbouring values *(user, 2026-09-15, D29 (1), from A81 F5)*

V4's `lad` same-optimum FAIL sits at 2.15× the 1e-6 floor with the factor F at one value. A V5 plan pre-declares the verdict at the chosen setting **and** publishes the re-tally at neighbouring settings (F ∈ {3, 10, 30}; floor ∈ {1e-7, 1e-6, 1e-5}) so a reader sees whether a verdict is a threshold artefact — the tally can produce the grid from the records at no run; only the declared cell is a verdict.

**Reduced 2026-09-29 (the user: "accepted" on the orchestrator's proposal).** The paper's appendix carries the same-optimum **statistic** (median and p90 paired relative objective difference against the declared floor) and, where it fails, its attribution to the rung it fails on (V4: `lad`, on the lift rung `B0 → B1`, not the partition). The neighbouring-threshold grid is produced for the internal report only, if at all; it is not a paper table.

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

> **D39 (the user, 2026-09-29):** V4's criterion (whole write set, τ = 1e-6) stays **selectable as a fallback** in V5 — the same switch, the other value, campaign-level, never mixed. See the V5 plan §3.

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

### 8. The prime is pre-processing: executed once per evaluation, before the first block *(the user, 2026-09-29)*

**What it is.** The first-wall geometry method that V4 calls the prime depends only on user inputs. V4 executes it
at the head of **every block sweep** of the partitioned arms (about 9 calls per evaluation in phase B, 13–15 in
phase A; stamped, never counted — D19), which was the simplest way to guarantee `build` reads this pass's value;
gate G2 shows every execution after the first computes the same value bit for bit. The paper's footnote describes
it as extracted and run before M2. The user: *"I need it to make sense from an architectural perspective. The prime
was needed to fully decouple the first iteration. It is pre-processing before the partitioned MDAs can start. I see
this as part of the minimal sequencing operations (like moving build)."*

**The change.** In V5's driver copy the prime runs **once per `call_models` evaluation, before M1** — a
pre-processing step of the sequenced schedule, not a per-sweep hook. Requirements: no count changes (it is not a
model node and stays out of every node-call column); the exit states of a job set bit-identical to V4's
per-sweep form (the G2 construction); the stamp records one call per evaluation. Pre-processing is once per
evaluation, not once per sweep. The paper's caption then reads as written ("executing the FirstWall subfunction"
before the partitioned MDAs).

### 9. Wall clock as a declared measurement, for the paper's appendix *(the user, 2026-09-29; reverses D29 (2) of 2026-09-15)*

**The concern, in the user's words:** *"I want the current tables that are in the paper also in terms of wall
clock time. Include a row for the totals for each config and arm/case. I will include these in the appendix of
the paper … I want an overview of cost break down, in terms of model evaluation cost, and overhead (flat and per
iteration, algorithm runtime cost (both for the MDA and opt), perhaps split in dispatch and test cost). I want to
be able to see if the architecture change makes a significant difference in terms of overhead."* And on its place:
*"the wall clock time is for the appendix, and to quantify a bit in the main text what I write about the wall clock
time"*; the model-evaluation counts stay the main result.

**Ruled — D33 (the user, 2026-09-29: "discussion item 4 is accepted").** Wall clock is reported in the paper's
appendix as context beside the counts, from V5's campaign at one worker with the instrument below, never as an
acceptance quantity (CLAUDE.md; I-10); **V4 publishes no timing** (its campaign ran three workers, so its per-run
`wall_s` is contended, and its harness bills the intervention arms for the whole-state test and I-30). D29 (2)
stands for V4 and is superseded for V5. Items 5 and 7 are prerequisites of any wall-clock table.

**The instrument.** Env-switched timers in V5's driver copy, observation-only (the block trace's precedent, DR8),
accumulated per run and stamped into the record: per node, the model's own wall time, summed per module through
the node map; per block loop, the **MDA convergence test** (read plus residual) and the **dispatch** (the sweep
body less its nodes and test); per evaluation, the **objective and constraints** layer; the **optimiser's own
time** (solve-phase wall less every evaluation); the **fixed per-run term** — process start, imports, numba cache
load, input parse, output writing, and the once-per-run schedule derivation (item 7), which is folded here and not
into dispatch. The run's wall time is measured independently and the unattributed residual printed, so the rows
are checked to add up. **Harness-only costs are excluded from the total and named in the caption**: the exit audit
sweep, the state snapshots, the census hooks, the record assembly. The instrument's own cost: one run per
configuration with timers off, reported beside. Two words to keep apart: the *convergence test* is the
coupling-state predicate the loops stop on; the *objective and constraints* layer is what upstream's idempotence
predicate compares — the tables use the two long names.

**Run discipline.** The whole campaign at **one worker**, so timings and counts come from the same runs; load
average recorded per run; a repeatability check of one seed per configuration, three repetitions (A91's form).

**The tables** (appendix; per configuration; arms as columns; ratio of means and per-run median with [min, max]
as in the count tables):
1. *phase A in wall clock*, ms per evaluation: M1, M2, M3, Feedforward, Post-processing (model time each); MDA
   convergence test; dispatch; objective and constraints; residual; **Total** (the evaluation's measured wall).
2. *phase B in wall clock*, s per optimisation: the same rows, plus optimiser own time and fixed per run;
   **Total** = the run's wall time less the harness-only costs.
3. *cost breakdown, phase B*: s per optimisation and ms per evaluation with the share of the total — model
   evaluation (the modules summed); MDA overhead per sweep: convergence test, dispatch; optimiser overhead per
   iteration; fixed per run; **Total**. Whether the architecture changes the overhead is read off the `B0` and
   `B2` columns of the per-sweep rows, normalised per evaluation.

**Expected reading** (from A91 and the campaign's sweep counts, large tokamak): reference to control, a few
percent more model time and a test term of about 1 ms; control to modified, model time about 0.75 with every
overhead row equal within 0.3 ms (dispatch 0.5 → 0.7 ms is the architecture's whole intrinsic overhead); total per
evaluation about 0.75–0.8 where the node-call ratio reads 0.64 — because node calls weight every model equally and
the cost sits in a few physics and coil models, which is the paper's argument for models of higher cost.

### 10. Reporting: one generated document for the paper, a report under 600 lines *(the user, 2026-09-29: "this v5 reporting approach is approved")*

**The gap.** V4's report is 3 100 lines with 83 appendix tables, a 162-table companion file, 30 gates and a
6 500-line second implementation recomputing every cell; the paper prints three result tables.

**What V5 delivers, and nothing more.**
- *Main text:* the switch matrix, the configurations table, phase A module sweeps, phase B optimiser
  iterations, phase B module sweeps (all in today's `paper_tables.md`).
- *Appendix:* the two module tables in wall clock with a totals row (item 9), the cost breakdown (item 9), the
  per-arm success table (item 3), and **one verification table**, one row per check: physics frozen; switch
  neutrality; matched accuracy (whole-state exit audit at 0 components above τ on every accepted run, and the
  between-arm fixed-point distance); same optimum (median and p90 against the floor, attributed where it
  fails); entry pairing; arm composition; output-path equivalence; the test set's teeth (A92).

**Dropped from V5:** the stencil entry regime and RQ3 (the transfer); the predicate trial G8 (D30); RQ5 (the
trust step, A43); the three weightings (A88); the companion file and every per-seed table; the
iteration-multiplier rule (item 1); the `AR → A0` stopping-rule prose (the columns stay, one sentence of context).

**Kept, not reported:** the harness self-checks (composition, rungs, provenance, data, resume identity, run-kind
separation, artifacts, …) — run, stated as "N self-checks pass" in one line; and a **one-time reproduction gate**:
the V5 copy at its copy commit, before any change, reproduces V4's twenty reference records bit for bit.

**Replaced:** the second implementation — a short independent recount of exactly the paper's cells from the raw
records, not a second rendering of every table.

**How.** One generator (the existing paper-tables module extended, not the plan-tables renderer) writes one
document — the paper tables, main text and appendix, as Markdown and LaTeX rows — with a `check` mode that
refuses when the rendered file and the records disagree. The V5 report has four parts: method (matrix,
criterion, settings, gate list with teeth), the paper tables included verbatim, one short findings section per
rung, the change log; target under 600 lines. V4's rules stand: every number from a committed script (protocol
§15), cells preserved between renders, captions of a few lines, teeth for every gate.

*A candidate assessed and dropped (the user, 2026-09-29):* A76 (fixed-point-distance)'s report §7 (d)
proposed that the between-arm fixed-point distance it added to V4's §4.2 as a reported statistic could
carry a pre-declared acceptance rule in a V5 plan (a natural form: headline median and p90 below τ,
0 pairs above τ). The paper needs one sentence that the arms reach the same fixed point, which the reported
distance is; no rule is added.
