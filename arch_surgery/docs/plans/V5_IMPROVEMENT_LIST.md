# V5 improvement list — method changes for a fifth experiment revision

> **Document status** — **CURRENT · PLANNING INPUT.** Opened 2026-09-15 from the user's review of
> the V4 method with task **A77 (v5-check2-decomposition)**, on the executed and reported V4
> experiment ([`EXPERIMENT_REPORT.md`](../../MDA_partitioning_experiment_v4/EXPERIMENT_REPORT.md),
> campaign records at `57dc0c14`, document at `14342a72`). Same convention as
> [`V4_IMPROVEMENT_LIST.md`](V4_IMPROVEMENT_LIST.md): **this is a list of candidate design changes,
> not a plan.** Nothing here is decided, and a V5 experiment plan would restate its selections with
> pre-declared acceptance rules. Nothing here may be applied to the V4 harness or its report — V4's
> campaign is measured and published, and a rule changed after the numbers is not a check. Arm
> names are the V4 report's at `14342a72` (`BR / B0 / B1 / B3`); A78 (arm-renames) renames `B3`
> to `B2` throughout the V4 folder and a V5 plan should use whatever names stand when it is written.

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

**A related hazard, proposed by the agent, not the user.** D22 made `st_regression`'s place
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

---

*Candidates proposed elsewhere and not yet listed here:* A76 (fixed-point-distance)'s report §7 (d)
notes that the between-arm fixed-point distance it added to V4's §4.2 as a reported statistic could
carry a pre-declared acceptance rule in a V5 plan (a natural form: headline median and p90 below τ,
0 pairs above τ). Whether it becomes an item is the user's call.
