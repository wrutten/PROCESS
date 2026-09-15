# A77 (v5-check2-decomposition) — the V5 improvement list opened, with item 1

> **Document status** — **OPEN.** Task **A77 (v5-check2-decomposition)**, branch
> `A77-v5-check2-decomposition`, base `14342a72` (2026-09-15). Doc-only: one new file,
> [`plans/V5_IMPROVEMENT_LIST.md`](../plans/V5_IMPROVEMENT_LIST.md), in the V4 list's format, with a
> status header and item 1. Minted by the orchestrator at the user's instruction in the requesting
> session (*"Yes, rewrite the V5 item as you propose"*) and confirmed by the user in the orchestrating
> session. No code, no run, no edit to the V4 folder. Folder position records lifecycle, not validity
> (trap T3).

## 1. Verdict in one page

- **Item 1 is written**: *retire check 2 (the iteration multiplier) as an acceptance rule; publish
  the decomposition `R = ρ × ε` as the result*. It records the user's concern in their words, locates
  the bias where the measurement shows it — the rule is one-sided (`median ≤ 1.05`), a shortened
  trajectory passes and its saving is folded into the headline cost ratio; V4's
  `low_aspect_ratio_DEMO` `B0 → B1` reads 0.8125 summed-iteration median, 0.7012 sum ratio, `PASS`,
  and the headline `B3/B0 = 0.450` carries it — and states the change: per-evaluation cost ratio ρ
  and evaluation-count ratio ε published as two numbers with the identity printed, neither gated; a
  two-sided label (*trajectory-neutral* / *changed by ε*) if a classification is wanted; the
  iteration constructions kept as context without a verdict.
- **What a `FAIL` does is stated honestly**: nothing — the cost population is chosen independently
  and retuning is forbidden — so the item says the bias is in the rule *not* firing, not in it
  firing, which is where the discussion with the user landed.
- **A defect in V4's own ε column, found while writing the item and recorded as a prerequisite.**
  The check-2 table's *evaluations median* column is built from `n_model_calls`, which is
  `numerics.n_model_calls` — the **sweep** count, declared in the driver as not comparable between a
  flat loop and a block schedule — not the `call_models` evaluation count. On `large_tokamak_nof`
  seed 1: `n_model_calls` 2 074 / 2 100 / 5 498 for `B0 / B1 / B3` against
  `sweeps_per_eval.n_evaluations` 630 / 660 / 660. The published column reads 2.65 / 2.12 / 2.78
  for `B0 → B3` under a heading that says evaluations; the true evaluation ratio is 22/21 = 1.048
  (the lift's stencil column) for `B0 → B1` and `B0 → B3` and exactly 1 for `B1 → B3`. No V4
  verdict rests on the column and §5.1's prose describes the number correctly as sweeps, but the
  table misleads. **Not fixed here** — A77 is doc-only and the correction is a V4 tally task on the
  V4 data; proposed for minting as an issue (§3).
- **A related hazard is marked as the agent's proposal, not the user's**: D22's conditional drop of
  `st_regression` is a selection at configuration level of the same shape; a V5 plan should declare
  membership unconditionally or the drop rule before the campaign.
- **Naming**: the item uses the V4 report's names at `14342a72` (`B0 / B1 / B3`) and says so; A78
  (arm-renames) follows.

## 2. What was written, and from what

Every number in the item is a cell of the V4 report at `14342a72` (§4.3 "iteration multiplier",
§4.3 "cost", §5.1, §5.2) or a field read from a campaign record at `57dc0c14`
(`runs/campaign/optimisation/large_tokamak_nof/{B0,B1,B3}/seed001/metrics.json`, fields
`n_model_calls`, `sweeps_per_eval.n_evaluations`, `dispatch_sweeps`), read in the A76 worktree's
seeded copy. The tally's construction of the column is
`harness/measurement/tally_optimisation.py` (`evaluation_ratios`, from `record.get("n_model_calls")`);
the record schema's description is `harness/core/records.py` (`_f("n_model_calls", "B", …,
"evaluations of the model set the optimiser asked for")`); the driver's statement that the field is
sweeps is `PROCESS/process/core/caller.py`'s `NODE_CALLS` docstring.

## 3. What should change elsewhere (proposed; not edited here)

- **Queue v2**: an issue for the mislabelled column — *check 2's "evaluations median" column reads
  `n_model_calls` (sweeps), not `sweeps_per_eval.n_evaluations` (evaluations); the record schema's
  sentence for `n_model_calls` is wrong* — and, if the user wants it corrected on the V4 data, a
  task: relabel the column as the sweep ratio it is, or refill it from the right field, in both the
  tally and the analysis, under the recomputation gate, with the report's §4 re-rendered and §5.1
  re-read. Numbers in §5.1 that cite the column as sweeps (*"2.7 / 2.1 / 2.8 times as many
  sweeps"*) are correct as written.
- **Queue v2**: the live pointer to `plans/V5_IMPROVEMENT_LIST.md` (the orchestrator adds it at
  merge, per the brief); A77's row → merged.
- **V5 improvement list**: the pointer at its end names A76's candidate (a pre-declared acceptance
  rule for the fixed-point distance) without listing it; the user decides whether it becomes item 2.

## 4. Limits

- The item argues from three configurations' worth of V4 cells; the attribution bias it names
  changed no V4 verdict, and the item says so.
- The "related hazard" paragraph (D22's conditional drop) goes beyond what the user asked and is
  labelled as the agent's proposal so it can be struck.
- The ε defect was checked on one seed of one configuration against the driver's own docstring and
  the schema's sentence; the column's three published values (2.65 / 2.12 / 2.78) match §5.1's
  sweep ratios (2.7 / 2.1 / 2.8), which is the corroboration. A task that corrects it should survey
  every record.

## 5. Change log

| date | entry |
|---|---|
| 2026-09-15 | List opened with item 1; report written; task open, awaiting the orchestrator's assessment. |
