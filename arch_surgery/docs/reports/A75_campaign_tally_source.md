# A75 (campaign-tally-source) — the campaign source family, and the tables over the 949

> **Document status** — **OPEN.** Task **A75 (campaign-tally-source)**, branch `A75-campaign-tally-source`
> off `architecture_surgery` at base `b72ef578`. Closes issue **I-24** (the tally had no campaign
> source). Every number here comes from a committed press of `experiment_runner.py` at the commit
> named beside it; the records read are the campaign's 949 at `57dc0c14` and the reproduction gate's
> 20 at `0677a9b3`, both seeded into this worktree. **0 PROCESS runs** (stamp survey §10).
> Folder position records lifecycle, not validity (trap T3).

*Vocabulary as in the harness README: "source" (a named, statable job set the tally may summarise),
"family" (this task: the gate sources or the campaign sources), "population" (`stats.Population`,
the records one table is over), "press", "tooth", `--resume`.*

## 1. Verdict in one page

- **I-24 was real and is closed by construction.** `tally.SOURCES` named two gate job sets and
  nothing for the campaign; the chain's tally stages read 0 records at the first campaign press.
  `tally.SOURCES` and `analysis.SOURCES` now each declare — independently, no shared list — five
  **campaign** sources, one per run stage of `chain.campaign_plan`, composed by the chain's own
  job functions (`chain.campaign_jobs`, extracted from the stages that run them, so the tally names
  exactly the jobs the chain made: all 949 identities match their records, the 28 crashed differing
  only by `status`).
- **One family is published, never both.** `tally.published_sources(campaign)` is the campaign
  family once any campaign record exists, the gate family otherwise. With the campaign present a
  gate record is **refused by kind** at `Population.of` (`stats.measurable_run_kinds(campaign_present=True)`
  is `("campaign",)`; the analysis re-derives the same rule as `allowed_run_kinds`). Gate
  `run_kind_separation` states both directions and proves them with 9/9 teeth.
- **Per-source counts (both implementations agree, `recomputation` compares them):**
  `campaign_entry_references` 3 (A) · `campaign_displaced` 275 (A) · `campaign_stencil_forward` 198 (A)
  · `campaign_stencil_backward` 198 (A) · `campaign_optimisation` 275 (B) = **949**; unpublished
  gate family `reference_runs` 20, `paired_entries` 11. 949 of 949 records under `runs/campaign/`
  are in a campaign source, 0 outside.
- **Gates at `4e2f79e6` over the 949 at `57dc0c14`:** `tally_contracts` PASS 252/0 (+256/0
  reference cells; 84 tables), `recomputation` PASS **12 715 compared / 0 mismatched** (84 tables,
  1 071 rows), `run_kind_separation` PASS 2 994/0; self-check 7/7; gate table **30 PASS, 155/155
  teeth**; `--plan-tables check` identical (4 716 lines).
- **§4 of the plan is now the campaign population**: header marker, the population sentence, and
  every §4.2–§4.4 caption name the campaign at `57dc0c14`; §4.1 stays the gates' own table.
- **Two findings the brief did not anticipate**, both reported as results (§7, §8): (i) the record
  contract refused all 28 crashed optimisations (per-attempt cost without a run total — the shape of
  every crash), so `tally_contracts` would have FAILed on part 4 even with a source; (ii) part 1 of
  `tally_contracts` needs the reproduction gate's 20 records in the same tree, and the campaign
  worktree at `57dc0c14` had none — a re-press there stops at the same gate for a second reason
  until GR's records are seeded or ruled out of that gate.

## 2. The situation, measured

The press record `runs/campaign/press.json` (made at `57dc0c14` in worktree `campaign-57dc0c14`):
four run stages `ok` (3 + 275 + 396 + 275 − 28 crashed), then `tally_evaluation` population
`reference_runs: 0 record(s); paired_entries: 0 record(s)`, `tally_optimisation` `reference_runs: 0`,
`tally_contracts` FAIL, chain refused. Two things were absent from that worktree: a campaign source,
and the gate records the two gate sources resolve to (a fresh detached worktree holds no
`runs/gates/`). In this worktree — seeded with A73's gate records — the pre-A75 code would have read
the 31 gate records and published *gate* tables beside 949 unread campaign records, which is trap T11
with the denominator hidden; that is the case the one-family rule (§3.3) exists for.

Why the smoke could not see it (proposed trap **T15**, §9): the tally refuses smoke records by
design, so the smoke's own 20 records were never a population; the smoke passed over the seeded gate
records, and the campaign source was exercised for the first time by the campaign.

## 3. The source definitions, side by side

### 3.1 The job composition (one place, the chain's)

`harness/chain.py` gains `entry_reference_jobs`, `references_from_records`,
`evaluation_displaced_jobs`, `evaluation_stencil_chains`, `optimisation_jobs`, `RUN_STAGES` and
`campaign_jobs(campaign, stage)`; the four stage functions now call these instead of composing
inline. `campaign_jobs` builds `campaign_plan(campaign)` whether or not it may run and composes the
stage's jobs without running anything; the dependent stages read the entry-reference records for the
entry state and the constant and raise `ChainError` where one is missing (a source over it is then
empty, stated — `tally.COMPOSITION_REFUSALS` gained `ChainError`). Rule (xiv): one job identity —
`pool.job_listing` over the composed sets reports `why_not_complete = None` for 921 records and
`status is 'crashed', not 'ok'` for 28.

### 3.2 The declarations

| | `harness/measurement/tally.py` | `harness/measurement/analysis.py` |
|---|---|---|
| dataclass | `Source(name, owner, jobs, phases, what, family, run_kind)` | `Source(name, owner, jobs, phases, what, family, run_kind)` |
| gate sources | `GATE_SOURCES`: `reference_runs` (GR, AB), `paired_entries` (G6, A) — `family="gate"` | same two, own `what` text |
| campaign sources | `CAMPAIGN_SOURCES`: `campaign_entry_references` (A), `campaign_displaced` (A), `campaign_stencil_forward` (A, `stencil_sign == 1`), `campaign_stencil_backward` (A, `stencil_sign == -1`), `campaign_optimisation` (B) — each `jobs=_campaign_stage(stage[, sign])` calling `chain.campaign_jobs`; `family="campaign"`, `run_kind="campaign"` | same five, `jobs=_campaign_run_stage(stage[, sign])`, own `what` text |
| `SOURCES` | `GATE_SOURCES + (CAMPAIGN_SOURCES if EXECUTION_APPROVED else ())` | same expression, own constants |
| run-kind check | `source_jobs` refuses a composed job whose `run_kind != source.run_kind` (`TallyError`) | `source_jobs` refuses the same (`AnalysisError`) |
| campaign present | `campaign_present(campaign)`: any campaign source has a `metrics.json` | `campaign_present(campaign)`: same rule, own code |
| published family | `published_sources` / `unpublished_sources` / `why_not_published` | `published_sources` |
| kind rule | `stats.CAMPAIGN_PUBLISHED_RUN_KINDS = ("campaign",)`, `stats.measurable_run_kinds(campaign_present=)`, `Population.of(..., campaign_present=)` | `CAMPAIGN_PUBLISHED_RUN_KINDS`, `allowed_run_kinds(campaign_present=)`, `Population.of(..., campaign_present=)` |
| stencil pairing | `tally_evaluation.pairing_key`: seed, or `job_identity.stencil_column` for `regime == "stencil"` | `analysis.pairing_key`: same rule, own code |
| crash detail | `stats.traceback_last_line`, `stats.crash_detail` | `last_traceback_line`, `crash_lines` |

`FORBIDDEN_IMPORTS` is unchanged and the recomputation gate's import tooth still trips; the analysis
imports `harness.chain` for the job composition exactly as it already imported
`harness.gates.reproduction` and `harness.gates.gate_entry` for the gate sources — the owner composes
the job set, the two modules independently declare *which* job sets are sources and what each is.

### 3.3 The one-family rule

Both tally stages iterate `published_sources` only; the other family is listed in the stage record
under `sources_not_published` with counts and `why_not_published`'s sentence. `declared_paths`
(the `runs read` survey) is over the published sources, so a stage's provenance names the records
its tables are over. `records_outside_every_source` (gate tree) is joined by
`campaign_records_outside_every_source` (campaign tree): 949 / 949 / 0 outside.

## 4. Per-source record counts, as the stages state them

| stage / source | phase | records | run kinds | contract refusals |
|---|---|---|---|---|
| `tally_evaluation` · `campaign_entry_references` | A | 3 | campaign | 0 |
| `tally_evaluation` · `campaign_displaced` | A | 275 | campaign | 0 |
| `tally_evaluation` · `campaign_stencil_forward` | A | 198 | campaign | 0 |
| `tally_evaluation` · `campaign_stencil_backward` | A | 198 | campaign | 0 |
| `tally_optimisation` · `campaign_optimisation` | B | 275 | campaign | 0 (28 before §7.2) |
| not published · `reference_runs` | AB | 20 | gate | — |
| not published · `paired_entries` | A | 11 | gate | — |

`runs surveyed: 949 record(s) at ['57dc0c14…']` on both stages, with the `--resume` straddle note
naming this tree's commit. `recomputed_tables` derives the same five populations with the same counts.

## 5. Gate verdicts, with denominators (all at `4e2f79e6`, records at `57dc0c14`)

| press | verdict | population (the gate's own words, abridged) | compared / mismatched | teeth | runs read |
|---|---|---|---|---|---|
| `--selfcheck` | PASS 7/7 | composition, rungs, capability, provenance, data, run path, stage provenance | — | all tripped | — |
| `--measure tally_evaluation --resume` | 55 tables | 4 campaign sources, 674 records | — | — | 949 at `57dc0c14` |
| `--measure tally_optimisation --resume` | 29 tables | `campaign_optimisation`, 275 records | — | — | 949 at `57dc0c14` |
| `--gate tally_contracts --resume` | **PASS** | 20 reference runs, 256 published cells, no tolerance; and 84 tables over the campaign population (3 / 275 / 198 / 198 / 275) | 252 / 0; reference cells 256 / 0 | 10/10 | 969 — 949 at `57dc0c14`, 20 at `0677a9b3` |
| `--measure recomputed_tables --resume` | 84 tables, 17 019 cells | the same five populations | — | — | 949 at `57dc0c14` |
| `--gate recomputation --resume` | **PASS** | 84 tables recomputed cell by cell from 949 records under the 5 published sources of the campaign population (7 declared), plus the import list | **12 715 / 0** (1 071 rows; 9 639 constructed + 2 976 composite cells + tables/denominators) | 9/9 | 949 at `57dc0c14` |
| `--gate run_kind_separation --resume` | **PASS** | 1 096 records under `runs/`, 949 covered by the 5 published sources (campaign family), 31 by the 2 unpublished; 949 campaign records checked against the campaign sources | 2 994 / 0 | 9/9 | 949 at `57dc0c14` |
| `--measure gate_table --resume` | 30 PASS, 0 FAIL, 0 not run | — | — | 155/155 | verdicts at `0677a9b3`, `b485bf4c`, `4e2f79e6` |
| `--plan-tables write` / `check` | written; **identical** | 949 records at `57dc0c14`, kind `{campaign: 949}` | 4 716 lines, 0 hunks | — | — |

Every verdict carries `runs_are_not_this_commit's` naming the records' commit and its own, as
`--resume` asks. `run_kind_separation`'s record: `records_by_run_kind {campaign 949, gate 145,
smoke 2}`, `published_source_records_by_run_kind {campaign 949}`,
`unpublished_source_records_by_run_kind {gate 31}`, `run_kinds_a_published_cell_may_be_over
['campaign']`. Its nine teeth: smoke → tally REFUSE; smoke → analysis REFUSE; gate record kept with
no campaign (positive control); **gate → tally with campaign present REFUSE; gate → analysis with
campaign present REFUSE; campaign record kept with campaign present (positive control)**; campaign
plan refused with the switch read as False; forged smoke plan refused likewise; resume across kinds
not kept.

## 6. What §4 now says

**Header marker** (line 683 of `EXPERIMENT_PLAN.md`):

> `## 4. Results` *(the **campaign** population — 949 records at `57dc0c14` — rendered from the
> campaign's records; the gate population at `0677a9b3`, `4ca8cff5`, `fd480aff` was the section's
> earlier fill, before execution approval, and is excluded by kind)*

**Population sentence:** "**Population: the campaign, not the gate runs.** `EXECUTION_APPROVED` is
True and the campaign has run: every cell in §4.2–§4.4 is over the 949 campaign run record(s) made at
commit(s) `57dc0c14`, by run kind {'campaign': 949}, by source `campaign_entry_references` 3,
`campaign_displaced` 275, `campaign_stencil_forward` 198, `campaign_stencil_backward` 198,
`campaign_optimisation` 275. The 139 gate run record(s) at `0677a9b3`, `4ca8cff5`, `fd480aff` (by run
kind {'gate': 137, 'smoke': 2}) were this section's earlier fill, before execution approval; they are
excluded from every published cell **by kind** (gate `run_kind_separation`) and appear only in §4.1,
which is the gates' own table. The exit audit was taken at position(s) `after_single_evaluation`,
`entry_to_write_output_files` with the convergence ruler(s) `frozen` and the exit-audit instrument
`whole_data_structure_derived_set`."

**Captions.** §4.2–§4.4: "Population: the campaign runs at `57dc0c14` — the source named in the
caption, twenty-five seeds per arm — **not** the gate runs, which filled this section before
execution approval and are excluded by kind; …". §4.1: "Population: each gate's own, stated in its
row — the gate population (139 run record(s) at …), never the campaign's; gates are gates. §4.2–§4.4
are over the campaign population." Inside the tally's own captions the hard-coded "these are gate
runs at one or two seeds" clauses are gone; the kind is read from the records
(`Population.runs_word`) and every `denominator_is` says "campaign runs".

**Which tables changed population.** Every table of §4.2, §4.3 and §4.4 — 55 + 29 + 84 = 168 — is now
over a campaign source (the gate-source tables are not emitted while the campaign is present). §4.1's
one table is unchanged in population. New in the set: the stencil regime's tables (never tallied
before — no gate source carried stencil records), the entry-reference tables, and the
optimisation phase's **failure taxonomy** (§6.1). `--plan-tables write` reports 169 tables, 34 068
cells, 4 716 lines replacing 1 798.

### 6.1 The failure taxonomy, as rendered (§4.3, `campaign_optimisation`)

**`failure taxonomy — large_tokamak_nof — campaign_optimisation`** (n = 100)

| arm | scheduled | crashed | ok | rows sum | detail (traceback's last line × count) |
|---|---|---|---|---|---|
| BR | 25 | 3 | 22 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×3 |
| B0 | 25 | 3 | 22 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×3 |
| B1 | 25 | 3 | 22 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×3 |
| B3 | 25 | 3 | 22 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×3 |

**`failure taxonomy — low_aspect_ratio_DEMO — campaign_optimisation`** (n = 100)

| arm | scheduled | crashed | ok | unconverged | rows sum | detail (traceback's last line × count) |
|---|---|---|---|---|---|---|
| BR | 25 | 2 | 23 | 0 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×2 |
| B0 | 25 | 2 | 21 | 2 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×2; process.core.solver.module_solve.ModuleSolveFailure: block FLAT did not converge in 20 sweeps at tau=1e-06; max scaled residual inf on current_drive.eta_cd_dimensionless_hcd_primary, 1 components above tau ×2 |
| B1 | 25 | 2 | 20 | 3 | yes | process.core.solver.module_solve.ModuleSolveFailure: block FLAT did not converge in 20 sweeps at tau=1e-06; max scaled residual inf on current_drive.eta_cd_dimensionless_hcd_primary, 1 components above tau ×3; RuntimeError: Failed to converge after 50 iterations, value is nan. ×2 |
| B3 | 25 | 2 | 20 | 3 | yes | process.core.solver.module_solve.ModuleSolveFailure: block M1 did not converge in 20 sweeps at tau=1e-06; max scaled residual inf on current_drive.eta_cd_dimensionless_hcd_primary, 1 components above tau ×3; RuntimeError: Failed to converge after 50 iterations, value is nan. ×2 |

**`failure taxonomy — st_regression — campaign_optimisation`** (n = 75): BR 25/25 ok, B0 25/25 ok,
B3 25/25 ok, detail —.

The 28 by seed (from the records; the failure tables of §4.3 carry them per seed with the other
arms' node calls): nof seeds 5, 20, 21 in all four arms (12, all `RuntimeError … value is nan`);
lad `RuntimeError … nan` at seeds 3 and 21 in all four arms (8), and `ModuleSolveFailure` (block
FLAT, or M1 for B3, `current_drive.eta_cd_dimensionless_hcd_primary` at `inf`) at seeds 4 and 22 in
B0, B1, B3 and seed 10 in B1, B3 (8) — these eight are `status crashed`, `failure_class
unconverged`. Phase A: every taxonomy table reads `ok` only (12 tables, 674 + 3 records).

Read beside the seed-set tables, also rendered: nof's every-arm-converged set is **22 of 25** seeds
(3 configuration-invalid), lad's is **11 of 25** (13 configuration-invalid; retried seeds BR 12 · B0
10 · B1 10 · B3 10), st's is **22 of 25** (1 configuration-invalid; retried BR 5 · B0 3 · B3 2). The
16 crashes on lad do not account for its 14 excluded seeds alone; the rest are accepted-optimum
failures (`ifail ≠ 1`) that the failure table lists. This report does not interpret those numbers.

## 7. Autonomous decisions, each with its reversal

1. **Five campaign sources, the stencil stage split into forward and backward sets** (the brief
   listed one `campaign_stencil` of 396). Every stencil point carries `campaign_seed = 0`, so the
   tables' seed-keyed pairing over one source of 396 would silently pair one point per arm — the
   `setdefault` keeps the first — under a caption naming the whole set. Splitting by sign gives the
   plan's own bracket (§3.4: "the forward and backward sets as the published bracket") and lets the
   pairing key be the design-vector column (an `int`, so every existing construction is untouched).
   *Reversal:* one `Source` with `stencil_sign=None` and a pairing key that carries the sign too.
2. **`pairing_key` reads `job_identity.stencil_column`.** The child stamps neither `stencil_column`
   nor `stencil_sign` at the record's top level (both are `None` there); the pool's identity stamp
   carries them. No child edit was allowed, and the identity stamp is the record's own. *Reversal:*
   stamp them at the top level in the child (a run-path change, out of scope here) and read that.
3. **The attempt-summation contract skips the *total* comparison for a record that says it did not
   finish** (`records.assert_attempt_summation`; the all-or-none rule still applies, and a record
   with no `status` — the reproduction gate's synthetic tooth — is held to the full rule). Measured
   before the change: 28 of 28 crashed records refused ("per-attempt `node_calls_solve_phase`
   without a run total"), 0 of 921 finished records refused; the sibling
   `assert_sweep_decomposition` already passed unfinished records over, and the docstring's own
   intent ("a run that crashed … has nothing to check") did not match the code for a crash that
   stamped one attempt. This is a `records.py` edit, not a `SCHEMA` change; it loosens a contract,
   so it is flagged for the user. *Reversal:* remove the `if not finished: continue`; the 28 then
   reappear as `record_contract_refusals` and `tally_contracts` FAILs on part 4 — the numbers above
   are what that verdict would read.
4. **The optimisation phase gains a `failure_taxonomy` table** (over the whole source population per
   configuration, before the seed-complete grouping), with a `detail` column — the traceback's last
   line per unfinished run, distinct with counts — added to the evaluation phase's taxonomy too;
   both implemented in the tally (`stats.crash_detail`) and the analysis (`crash_lines`) and
   compared by `recomputation`. The plan's §3.5 check 4 asks for the taxonomy "with denominators of
   25"; the tally had it for Phase A only. *Reversal:* delete `tally_optimisation.failure_taxonomy`,
   the phase-B call in `analysis.recompute`, and the `detail` column in both.
5. **The two plan teeth run with `EXECUTION_APPROVED` read as False** (`chain._approval_off`
   patches this module's own binding for the check and restores it). With the switch on, "a campaign
   plan without approval" and "the smoke's plan forged into a campaign" would both fail to trip —
   the refusal they prove *is* the switch — and `run_kind_separation` had not been pressed since
   approval. *Reversal:* drop the context manager and accept that the two teeth cannot trip while the
   campaign is approved (a gate that fails by design is not a gate).
6. **`tally_contracts` part 1 stays over GR's 20 runs whatever the published family**, and the gate's
   `jobs` list the published sources plus GR's. Part 1 reproduces the previous revision's cells and
   has nothing to do with which family is published; its precondition is discussed in §8.
7. **Gate-family tables are not emitted while the campaign is present** rather than emitted and
   labelled. The brief's (3) — "every published cell is over campaign records only" — reads as the
   former; the stage record still counts and names the unpublished sources. *Reversal:* iterate
   `SOURCES` and pass `campaign_present=False` for gate sources — which the one-family refusal would
   then have to be relaxed for.
8. **`records_dir` surveys in `plan_tables.population_marker`**: the campaign population is derived
   from the tally's published sources (under `campaign.runs_dir`), the gate population from
   `records_dir` as before. `--outdir` redirects the gate records only, as it always did.

## 8. Limits

- **`tally_contracts` needs the reproduction gate's 20 records in the same tree.** Part 1
  (`reference_cells`) refuses an empty comparison by design (trap T11). In the campaign worktree at
  `57dc0c14` there were no gate records, so the chain would stop at `tally_contracts` there even with
  A75's sources. Here the gate PASSes because A73's records are seeded. Options for the user (a
  ruling, not mine): seed GR's records into any tree that presses the campaign (0 runs; the
  "reuse gate records" habit), or press `--gate reproduction` there (20 PROCESS runs), or rule that
  part 1 belongs to gate `reproduction` alone and `tally_contracts` drops it. The chain's stage list
  (`READING_STAGES`) needs no change for the tally itself: with the sources populated and GR's
  records present, `chain.run` proceeds through `tally_evaluation`, `tally_optimisation`,
  `tally_contracts`, `recomputed_tables`, `recomputation` — the same five stages this task pressed
  one by one. Not pressed as a chain (that is `--campaign`, a run-making button).
- **Every verdict here straddles**: records at `57dc0c14` (and GR's at `0677a9b3`), verdicts at
  `4e2f79e6`; every press was `--resume` and every verdict says so. A from-scratch press is 949
  PROCESS runs and is not this task's.
- **The stencil sources hold `n_iteration_variables` columns per arm — 20 / 19 / 14 on nof / lad /
  st — for every Phase A arm**: all four (`AR`, `A0`, `A0p`, `A1`) read the `committed` input file,
  so `plan.stencil_column_set`'s "+1 lifted column" applies to no Phase A arm and the plan's
  "`2(nvar + 1)` per arm" reads `2·nvar` here. Stated from the composed job set; not investigated.
- **Composite cells** (2 976 of the 12 715 compared) are rendered strings — the `detail` column,
  seed lists, brackets; agreement on them is weaker evidence than on the 9 639 constructed cells,
  which the gate already reports apart.
- **The rendered §4 duplicates each table's caption and how-to-read line** (the table's own markdown
  carries them and `plan_tables._table_block` adds them again). Pre-existing (visible in the gate
  population render at `03f72479`); not touched — an improvement item, not a number.
- The `campaign_entry_references` source (3 records, arm A0 only) produces a one-row cost table per
  configuration with a FALLBACK reference-arm clause; it is the cold-start term "beside, never
  pooled" and is published as such.

## 9. What should change elsewhere (proposed; not edited here)

- **Queue (`MASTER_TODO_v2.md`):** I-24 → **CLOSED at A75's merge** (the closing conditions in its
  row are met: both declarations, the 949 read, `tally_contracts` and `recomputation` PASS over them,
  §4 rendered as the campaign population). A75 → MERGED with this report's path and
  `runs/A75_runs/` once relocated. A new issue for §8's first limit: *the campaign press needs GR's
  records in its tree, or a ruling on `tally_contracts` part 1* — a decision for the user. A note in
  the change log that decision 3 of §7 loosened the record contract for unfinished records.
- **Harness plan:** an **amendment 26** — the campaign source family; `published_sources` and the
  one-family rule; rule (xi) extended: *a chain plan's job set is a tally population, composed by
  the chain's own functions (`chain.campaign_jobs`) and never re-derived from a directory*; the
  pairing key for the stencil regime; the phase-B taxonomy. Appendix A.1's rule (xi) row: "half"
  → the campaign population is now mechanical too. Rule (xiii) applied here: `run_kind_separation`
  and `tally_contracts` were pressed at the commit that changed them.
- **TRAPS.md, T15:** *A stage whose declared population is a gate's job set passes the smoke because
  the smoke's own records are refused by kind.* The smoke read seeded gate records and reported on a
  population the campaign never uses; the first press with campaign records found the tally with no
  source for them (I-24). How to catch it: a smoke tree with **no** seeded gate records must make the
  reading stages report `0 record(s)` for every gate source and a non-zero count for a smoke-family
  source — or the smoke must assert that the plan's own run kind is in some declared source's
  `run_kind`. (A `smoke` source family would be the mechanical fix; it needs a ruling because the
  smoke must still never be *published*.)
- **Improvement list:** (a) the duplicated caption / how-to-read lines in the §4 render; (b) stamp
  `stencil_column` and `stencil_sign` at the record's top level in the child; (c) a `--jobs
  campaign_<stage>` listing for the campaign sources, as `--jobs <gate>` exists for gates; (d) a
  press of `run_kind_separation` belongs in the approval commit, since two of its teeth depended on
  the switch's state.

## 10. Presses, commits, stamp survey

Presses, from `arch_surgery/MDA_partitioning_experiment_v4/` at `4e2f79e6`, in this order (outputs
in the session scratchpad; the verdict and stage records under `runs/gates/<name>/`):
`--selfcheck`; `--measure tally_evaluation --resume`; `--measure tally_optimisation --resume`;
`--gate tally_contracts --resume`; `--measure recomputed_tables --resume`; `--gate recomputation
--resume`; `--gate run_kind_separation --resume`; `--measure gate_table --resume`; `--plan-tables
write`; `--plan-tables check`. The same sequence was pressed once before at `9b4e92f3`/`8833795a`
(identical verdicts); `records.py` changed afterwards (§7.3's synthetic-tooth clause), so the
sequence was repeated at the final code commit (rule xiii).

**Stamp survey** (`run_stamp_survey.py`, before at `b72ef578` / after at `bee28494`): 1 096 records
under `runs/` both times — 949 at `57dc0c14`, 96 at `0677a9b3`, 39 at `4ca8cff5`, 6 at `fd480aff`,
3 at `47be2b0d`, 3 at `61473c1d` (census) — **0 changed, 0 disappeared, 0 new: 0 PROCESS runs.**

Commits on `A75-campaign-tally-source` (base `b72ef578`):

| commit | what |
|---|---|
| `9b4e92f3` | the campaign source family: `chain.campaign_jobs`; `tally.SOURCES` / `analysis.SOURCES` (five campaign sources each, independently); `published_sources` and the one-family refusal (`stats`, `analysis`); `run_kind_separation` criterion and teeth; phase-B taxonomy with detail; attempt-summation total skipped for unfinished records; `plan_tables` marker |
| `8833795a` | the recomputation verdict names the published family and its source count |
| `85c8c041` | attempt-summation: a record with no `status` is held to the full rule (the reproduction gate's synthetic tooth) |
| `4e2f79e6` | README: the campaign source family and the one-family rule |
| `bee28494` | `EXPERIMENT_PLAN.md` §4 rendered over the campaign population (169 tables, 34 068 cells); `--plan-tables check` identical |

Files changed: `harness/chain.py`, `harness/core/records.py`, `harness/measurement/{stats,tally,
tally_evaluation,tally_optimisation,analysis,plan_tables}.py`, `harness/gates/gate_tally.py`,
`harness/README.md`, `EXPERIMENT_PLAN.md`. Nothing under `harness/child/`, `ystate.py`, `PROCESS/`;
`records.SCHEMA` unchanged; the queue, the harness plan, TRAPS and the improvement list unedited.

---

## Orchestrator's critical assessment (protocol §5)

*Written 2026-09-14 at the branch tip `95270651`, before the merge. Checks chosen to differ from the
agent's.*

1. **The cost table, recomputed from the records without the tally or the analysis.** Over the seeds
   on which all four arms finished on `large_tokamak_nof` I get 41 479.8 / 42 515.5 / 42 841.9 /
   27 187.5 solve-phase node calls per run for BR / B0 / B1 / B3 and ratios 0.976 / 1.008 / 0.640
   against B0 — the rendered cells to the last digit. A third construction agreeing with two
   independent ones is as much as a table can be checked.
2. **The seed sets.** My status-only count gives 20 common finished seeds on `low_aspect_ratio_DEMO`;
   the tally's seed set is 11, because its rule is "every arm converged" (`ifail = 1`), not "every arm
   finished", and it names the 13 configuration-invalid seeds. The stricter rule is the plan's (§3.5)
   and the table says which it used. Correct.
3. **The contract loosening (autonomous decision 1).** A crashed run has no solve-phase total by
   construction — the driver writes it at a finished exit — so asking the attempt-summation identity
   of it refuses every crash for a reason that says nothing. Skipping the total check for
   `status != "ok"` while keeping the all-or-none rule is right; the 28 crashed records are still
   counted, by arm, seed and traceback line, in the taxonomy table, and never as a cost. Accepted.
4. **Item 2 (`tally_contracts` part 1 wants GR's 20 records in the same tree).** Ruled: the campaign
   worktree is seeded with GR's records from the gate population at the next press; a re-press of the
   campaign chain there is not needed for this report, since every stage after the runs was pressed
   here over the same 949 records. Filed as an issue for the chain (the campaign plan's stage list
   should declare that dependency, or part 1 should move to the gate that owns it).
5. **The stencil source split** (forward / backward, 198 each) is right for the reason given: every
   stencil point carries seed 0, and a seed-keyed pairing would have paired one point per arm silently.
6. **Recomputation 12 715 / 0 over 84 tables** and **run_kind_separation 2 994 / 0** read from their
   verdicts; **0 PROCESS runs** by the stamp survey (1 096 records, 949 at `57dc0c14`, 0 changed).

**Approved for merge.** With this, the campaign's records are the population of every §4.2–§4.4 cell.
