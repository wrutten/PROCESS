# A53 (harness-tally) — the experiment's tables, from the records, with the four things a table cannot be emitted without

> **Document status** — **OPEN.** Task **A53 (harness-tally)**, plan task **H6** of the approved V4
> harness plan. Branch `A53-harness-tally`, base `d13a54c7` (the merge of A52 (harness-gates)).
> Every gate run in this report was made in this worktree at `cd62c510`; the verdicts and tables
> were computed afterwards and each states, in its own provenance line, the commits of the records
> it read. No campaign record exists: `EXECUTION_APPROVED` is `False` and every run here is stamped
> `gate` or `smoke`.

---

## 0. What this task did, and the words it uses

**In one sentence.** The harness could make the records and could check them, but it could not turn
them into the experiment plan's tables — so this task builds the three pieces that do
(`stats.py`, the two tally stages, `tables.py`), makes every declaration of the plan a function
whose docstring *is* the declaration, makes the seven things a table may not be into refusals at
construction rather than review comments, and checks the whole thing against the one number
available: the previous revision's published cells, **270 of 270 reproduced**.

**Vocabulary, spelled out once** (orchestration protocol §4 — a report should read without the
queue open beside it):

| word | meaning |
|---|---|
| **tally** | the summary computed from the run records: the experiment plan's §4 tables. It has **nothing to pass**, so it is a *measurement stage* under `--measure`, never a gate |
| **construction** | one declared way of computing a published number — which median, which population, what an accepted optimum is. Each is one function in `harness/stats.py`, and **its docstring is the declaration** a caption quotes |
| **denominator** | the count of things actually compared, printed beside every count. A table whose denominator is a letter rather than a number is refused |
| **caption** | the five things a table cannot be emitted without — units, what a row is, what a column is, the population, the construction — plus the clauses the plan requires in that particular caption |
| **measurement stage vs gate** | a *measurement* publishes numbers and has no verdict; a *gate* has a criterion and at least one **tooth** (a deliberate break it must catch). The two are different types so that a table can never be read as a verdict |
| **source** | a named subtree of `runs/gates/` whose records are a comparable set, with the sentence saying why. The tally reads a source, never "the gate runs" |
| **audit position** | where a run's exit audit was taken. `entry_to_write_output_files` is the declared position — the state the solve handed over. `after_run` is where the previous revision measured, and is the reproduction gate's. **They are two different quantities** |
| **the two predicates** | the two convergence tests this experiment counts. The **coupling-state** test compares hundreds of components (827–846 flat, 216–268 per block); **upstream's** objective/constraint test compares 14–27 values. An arm stops on exactly one of them |
| **arm** | one column of the switch matrix. `AR`/`A0`/`A0p`/`A1` run one model evaluation; `BR`/`B0`/`B1`/`B3` run one optimisation |
| **the restricted statistic** | the exit-audit maximum with the components the once-per-run deferred nodes write taken out — those nodes run at the end by design and their outputs are meant to move |

**Project shorthand used below.** *T11* — a number published without the condition that limits it;
this project's recurring error. *Protocol §12* — a gate must be shown capable of failing, and every
count carries its denominator. *Protocol §15* — every published number comes from executing a
committed script. *Protocol §16* — every table carries a caption. *I-10* — a wall-clock-derived
weight moved 6.4 % → 4.4 % across runs of identical code; no conclusion here rests on a timing.
*D25* — the exit audit will restore the whole data structure (task A62, in flight).

---

## 1. Verdict

**The tally is built, it is on the button, and it lands on the previous revision's numbers.**

- `experiment_runner.py --gate all --census-entry evaluation`, pressed **from nothing** in this
  worktree at `cd62c510`, returns 0: **22 gates PASS, 0 FAIL, 119 of 119 teeth tripped**. That is
  A52's 21 gates plus this task's `tally_contracts`.
- **`tally_contracts` PASS.** The previous revision's published cells reproduce **270 of 270** over
  the twenty reference runs; **195 of 195** table-contract checks pass over **65 emitted tables**;
  **10 of 10 teeth trip**.
- **Gate GR still PASSES 270/270 after the record-field rename.** Every record field carrying a
  retired mechanism word is renamed to the vocabulary's word for it, and the committed reproduction
  reference keeps its bytes — the comparator translates through a map (§7).
- `--measure all` runs **eight** measurement stages and returns 0; the two new ones emit **65**
  tables (27 evaluation-phase, 38 optimisation-phase) with **6 further tables not produced and each
  named with its reason**.

**Three things the tally refuses, demonstrated rather than asserted.** A table without a caption or
a denominator is a `TypeError`-shaped refusal at construction. A population handed a budget-capped
demonstration record is refused by name. A tally whose records straddle two commits refuses unless
`--resume` was asked for, and the refusal prints as `REFUSED — …`, with exit code 3.

**One thing this task got wrong and had to redo.** The first full press was run while this task was
still editing `harness/child.py` — the file every measurement subprocess imports. Gate G8 failed on
that press, with one pair differing and no verdict change. The cause was the edit, not the code:
the whole run set was deleted and re-made from scratch with nothing touched while it executed, and
G8 passes. It is reported here because the failure is a result about this task's method (§10).

---

## 2. `stats.py` — the declarations, as functions

The experiment plan declares how every published number is built. The previous revision kept those
declarations as comments beside whichever code happened to need them, which is how one definition
reached two implementations and drifted apart twice (issues I-18 and I-19). Here each is **one
function**, and a caption quotes its docstring rather than paraphrasing it.

*Caption: one row per declared construction of experiment plan §3.4–§3.6, the function that
implements it, and the sentence its docstring declares. "Refusal" marks the three that are
refusals rather than computations, because the plan states them as refusals.*

| construction | function | what it declares | refusal |
|---|---|---|---|
| the median | `median` | nearest-rank, **upper-middle**: `sorted[n // 2]`. Never an interpolated value — every acceptance quantity here is a measured one | |
| p90 | `p90` | nearest-rank, element `ceil(0.9 n)` counting from 1 | |
| the seed bracket | `seed_bracket` | `[min, max]` over the table's population; an observed range, not a confidence interval | |
| an accepted optimum | `accepted_optimum` | `status == ok` **and** the output file's `ifail == 1`. Two sources, one of them independent of the harness | |
| the one seed set | `every_arm_converged` | the seeds on which *every* arm reached an accepted optimum | |
| configuration hardness | `configuration_invalid_seeds` | seeds on which **no** arm converged, counted separately and against no arm | |
| a retried seed | `retried` | the optimiser was called more than once, **computed from `attempts[]` and from nothing else** | ✔ |
| the summation identity | `attempt_summation` | Σ over `attempts[]` = the run's solve-phase total, for node calls and for sweeps, **with its residual, printed** | ✔ |
| check 2, construction one | `iterations_final_attempt` | the final attempt's iteration count — the previous revision's, kept for comparability | |
| check 2, construction two | `iterations_summed_over_attempts` | iterations summed over every attempt, failed attempts included — **the declared acceptance statistic** | |
| the ratio triple | `ratio_triple` | pooled (Σ/Σ), per-run median with `[min, max]`, and the count of seeds where the arm cost more | |
| retries as a term | `with_and_without_retried` | the cost ratio **with and without** the retried seeds, from `attempts[].node_calls_solve_phase` | |
| check 1's statistic | `relative_objective_difference` | `\|Δ norm_objf\| / max(\|a\|, \|b\|)`, per pair, relative | |
| check 1's acceptance | `acceptance_threshold` | `max(F × yardstick, floor)`, the yardstick measured inside the same campaign | |
| check 1a's clustering | `clusters`, `hops` | split where the relative gap between adjacent sorted optima exceeds `10 × floor` | |
| check 1b's category | `below_cluster_resolution` | `floor < r < gap`: *distinct optima below cluster resolution*, a named category | |
| the similarity verdict | `similarity` | `max/min ≤ F`, with the plan's zero clause: both zero is trivially similar, one zero is unbounded | |
| the taxonomy | `failure_taxonomy` | every scheduled run a row; a run that wrote no record is `no_record`, counted, never skipped | |
| the audit position | `audit_position_of` | where the run's exit audit was taken | |
| the audit instrument | `audit_instrument` | which instrument produced the residuals, **read from the record**, one accessor | |
| the restricted statistic | `restricted_statistic` | the audit maximum over the components the once-per-run nodes do not own, **with its argmax** | |
| the whole-state statistic | `whole_state_statistic` | the same maximum over every component, published beside, never judged alone | |
| the empty-visit disclaimer | `empty_visit_shares` | both shares, with the **sweep** share marked quotable and the visit share marked not | |
| the two predicates | `predicate_widths` | one block per named test, **and no total to reach for** | |
| what a table is over | `Population` | the records, the membership rule in one clause, and the denominator | ✔ |

**Three of these are worth their own sentence.**

`retried` is computed from `attempts[]` and the record's own derived
`attempt_accounting.retried` is deliberately *not* consulted. It is a copy of the same count, and a
tally that reads a stored flag cannot tell a driver that stopped stamping attempts from a run that
did not retry.

`attempt_summation` is printed, not assumed. The record contract already refuses a record whose
parts do not add up; this states the identity as a number a reader can see, which is what licenses
publishing a cost ratio *with and without* the retried seeds — the ratio is visibly over the
quantity the attempts decompose. Over the fourteen optimisation records here the residual is **0 on
every run, for both node calls and sweeps** (§8.2).

`Population` refuses. A record stamped `force_maxcal` — a budget-capped demonstration of the retry
ladder, never a measurement — is excluded **by name and counted**, and `assert_no_forced_budget()`
turns that into a refusal for a caller that must never have been handed one. One such record exists
in `runs/gates/record_completeness/`, and the tooth uses it.

---

## 3. `tables.py` — the four things a table cannot be emitted without

Protocol §16 has been a review rule. Here it is a type error.

*Caption: one row per refusal, the shape it takes, and the specific way this project has been
misled that it exists to prevent. Every one is exercised by a tooth of `tally_contracts` (§9).*

| refusal | shape | why |
|---|---|---|
| **no caption** | `Table` cannot be built without a `Caption`, and a `Caption` cannot be built without units, what a row is, what a column is, the population and the construction | a table whose meaning needs the surrounding prose to decode is incomplete (protocol §16) |
| **no denominator** | the denominator must be an `int ≥ 0` with a sentence saying what it counts | a count over a population quietly smaller than the one named is trap T11 |
| **a placeholder denominator** | the literal `n`, `nn`, `N`, `?`, `—`, `TBD` … is refused **by name** | the plan's §4 tables print a letter where a count belongs, deliberately, because nothing is measured there yet. A table emitted with one is a template that was half filled in |
| **a timing column in an acceptance table** | a column whose name contains `wall`, `cpu`, `clock`, `elapsed`, `runtime`, `maxrss`, … as a whole word | no conclusion rests on a timing (I-10). The matcher is word-based on purpose: the burn-time residual is published in **seconds** and is not a timing |
| **a pooled-predicates column** | a `Column` declares which predicate it belongs to; `"pooled"` is refused | the two tests are not the same test and their widths differ by nearly two orders of magnitude, so their sum belongs to neither |
| **an audit-position mix** | rows carrying more than one `audit_position` are refused unless the table declares the position as a column of its own | a residual at the entry to the output path and one after the run are two different quantities |

---

## 4. The two tally stages, and what they emit

Both are `framework.Measurement` entries in `gates.registry`, so they run under `--measure` and
cannot be read as verdicts. Where the tally *checks* something, that check is the gate of §9.

*Caption: one row per table the tally emits, the plan section it realises, and how many instances
were emitted over the gate populations at this commit. "Instances" is one table per (source, arm
group, configuration) — the population split of §5.*

| table | plan | what it carries | instances |
|---|---|---|---|
| cost per call | §4.2.1 | node calls and sweeps per evaluation, sweeps per block, arrangement-method calls beside them, and the ratio triple against the declared reference arm | 6 |
| matched accuracy | §4.2.2 | the exit-audit maximum, restricted and whole state, **on both rulers**, argmax named, exclusion counts per ruler, audit position and instrument | 6 |
| ownership rung | §4.2.3 | `A0 → A0p`: the loop's cost of converging the burn time, and the residual the constant leaves | 2 |
| per-sweep overhead (evaluation) | §3.5 check 5 | the two predicates in **separate** columns, with the empty-visit **sweep** share | 6 |
| failure taxonomy | §4.2.6 | every scheduled run a row, rows summing to the denominator | 6 |
| the predicate trial | §4.2.5 | the **two** decisive-pass counts and **both** rulers' audits per run | 1 |
| the seed set | §4.3.1 | the one population per configuration, and the retried-seed count per arm | 5 |
| the failure table | §4.3.1 | every seed outside the set, with each failed arm's cost beside the others' | 5 |
| same optimum | §4.3.2 / check 1 | the paired relative objective difference against the campaign's own yardstick, clusters, hops, below-resolution | 3 |
| iteration multiplier | check 2 | **both** constructions, both sum ratios, the evaluation ratio beside them | 3 |
| the attempt summation identity | §3.5, retries | Σ attempts against the run total, with the residual | 5 |
| cost | check 4 | node calls in the one format, **with and without** the retried seeds | 3 |
| achieved accuracy | — | the exit audit at the accepted optimum, both rulers, audit position and instrument in columns of their own | 5 |
| the lift closed | check 3 | constraint 93's residual at every accepted optimum | 4 |
| per-sweep overhead (optimisation) | §3.5 check 5 | as above, plus the solve-phase and output-time sweep split | 5 |

**65 emitted; 27 evaluation-phase, 38 optimisation-phase; all 65 are acceptance tables and none
carries a timing column.** Six further tables were **not produced**, each named with its reason in
the stage's own record: the `B1·B3` arm groups carry no `B0` run, and every pair of checks 1, 2 and
4 is anchored on it — a table over no comparison would state a denominator for nothing.

---

## 5. The population problem, and what the tally does about it

**`runs/gates/` is not one population.** Several gates run the same arm at the same seed from
different entries, and three of them run it deliberately doctored. The first version of this tally
averaged across that tree and produced, for `large_tokamak_nof`, "A1: 18 runs, 43.9 node calls per
evaluation, bracket [18, 68]" — a per-run mean over a set nobody can state, which is trap T11 in
its purest form. It was caught by reading the output, and it is the reason the design changed.

**The tally now reads a *declared source*.** Two exist, each with the sentence that says why its
records are comparable:

*Caption: one row per declared source, with the records it holds at this commit. `keep` is the
path filter where one is needed.*

| source | subtree | phases | records | why they are a comparable set |
|---|---|---|---|---|
| `reference_runs` | `gates/reproduction/runs` | A and B | 6 + 14 | one record per arm, configuration and seed of the reference set, each made by the committed run path, the optimisations from the configuration's own start and the evaluations from the same displaced entry |
| `paired_entries` | `gates/entry_and_warm/*/pairing` | A | 8 | every evaluation-phase arm entered from the **same** displaced coupling state at one seed — the plan's own Phase A entry construction |

**28 of the 156 records under `runs/gates/` are in a declared source; the other 128 are counted and
named by their gate** in the stage's record (`audit_restriction` 18, `cold_chain` 16,
`predicate_mode` 27, `prime_map` 12, `switch_neutrality` 12, `output_path` 11, …), so the smaller
denominator is a stated choice and not an omission.

**Within a source, the optimisation phase is split again into seed-complete arm groups.** The
plan's "the seeds on which *every* arm converged" assumes what a campaign guarantees — every arm at
every seed — and a gate's runs do not: the reproduction gate runs `BR`/`B0`/`B3` at its unperturbed
seed and `B1`/`B3` at its perturbed one. Over the whole source that construction returns an empty
set, and an empty set is not a population, it is an absence. Each group is a set of arms and the
seeds at which all of them ran, which *is* a population the construction applies to, and the group
is named in every table's title. **In a campaign there is one group per configuration and this
split is invisible.**

**Every pairing is seed-keyed.** The first version paired two arms' values by position; a ratio
paired by position compares whichever runs happened to sort first. The tables now print the seeds a
ratio is over.

---

## 6. The previous revision's published cells, reproduced

`tally_contracts` computes **the same cells the previous revision published** for each of the
twenty reference runs, from *this* revision's records, and compares them without tolerance.

**270 of 270 cells matched; 20 of 20 runs reproduced whole.**

Three of the cells are produced by one of **this revision's own constructions** rather than read
from a field, which is what makes this a stronger statement than the reproduction gate's
field-for-field comparison: a *rule* landing on the previous revision's published number says the
rule is the same rule.

*Caption: the three constructed cells, the construction that produces them, and the previous
revision's field they are compared against. Population: the 14 optimisation records of the
reference set; the evaluation records carry only the attempt count.*

| cell | this revision's construction | the previous revision's field |
|---|---|---|
| iterations, final attempt | `stats.iterations_final_attempt` — the last element of `attempts[]` | `n_solver_iterations` |
| iterations, summed over attempts | `stats.iterations_summed_over_attempts` — the sum over `attempts[]`, failed attempts included | `exit_forensics.n_solver_iterations_summed_over_attempts` |
| attempts | `stats.n_attempts` — the length of `attempts[]` | `exit_forensics.n_attempts` |

**The compared cell list is derived, not written out**: for each run it is
`reference.REFERENCE_FIELDS[phase]` intersected with the fields that run's entry actually
published, and the stage reports any drift between the two. This matters for the merge ahead: task
**A62 (exit-audit-restore)** will drop the inherited audit residual from the compared set, and when
it does, this comparison drops it too rather than continuing to compare a cell nobody compares.

**The reference is never regenerated.** Its bytes are the previous revision's numbers; a comparison
that rewrote them would be a comparison with itself.

---

## 7. The record-field rename, and the map that keeps the reference intact

The orchestrator's ruling at A56 (driver-renames)'s merge: record fields still carrying the
previous revision's mechanism words are renamed to the vocabulary's words through a field-name map
in `reference.py`, so the committed reference keeps its bytes and the comparator translates. This
task carried it out.

The evidence that it was owed: the **driver's own counters had already been renamed** by that
change — `ARRANGEMENT_METHOD_CALLS`, `DEFER_PER_RUN_TOTALS` — while the record fields that carry
them had not.

*Caption: one row per renamed record field. "Previous" is the spelling the committed reproduction
reference carries and the previous revision's records use; "this revision" is the record field
name now. The map is `reference.FIELD_NAME_MAP`, read through `field_name_map()`.*

| previous | this revision | why |
|---|---|---|
| `module_solve_totals` | `block_loop_totals` | named the driver module; what it counts is the **block loop**, the vocabulary's word for the retired "inner/outer loop" |
| `…​.outer_pass_hist` | `…​.schedule_passes_per_evaluation` | "outer pass" is the retired arm's word; the matrix row is the **block schedule**, which now runs once |
| `…​.inner_sweeps_by_block` | `…​.sweeps_by_block` | the sibling key carrying the other half of the retired pair *(this task's own extension of the ruling)* |
| `…​.inner_solves_by_block` | `…​.solves_by_block` | as above |
| `post_solve_totals` | `defer_per_run_totals` | "post-solve" is the mechanism; the term is the deferral's **frequency** |
| `n_prime_calls` | `n_arrangement_method_calls` | "the prime" is the mechanism; the matrix row is **arrangement · method**, and the driver's counter already carried that name |
| `pin_intact_at_exit` | `burn_time_constant_intact_at_exit` | "pin" survives only in docstrings; the matrix row is the **burn-time owner** |

The nested keys are translated in **one place** — `child.BLOCK_LOOP_KEYS`, where the driver's
counters become a record field — because the dictionary they come from belongs to the copied
`process/` tree, which this task does not touch.

**Gate GR was re-run and PASSES 270 of 270** with the map in place, and its verdict now records
which fields it translated. Every other gate that names these fields (G1's exclusion set, G2, G3,
G4, G5, G6, G7, G8, G9) was re-run in the same press and passes.

---

## 8. What the tables say, over the gate populations

**Read the denominator in every caption.** These are one or two seeds per arm per configuration.
They are here to show the constructions working on real records and to be compared with the
previous revision's own published values for plausibility — **not one of them is a campaign
statistic and none may be quoted as one.**

### 8.1 The evaluation phase

*Caption: node calls per `call_models` evaluation and the `A1/A0` ratio, per configuration, over
the `reference_runs` source at seed 1 — **one run per arm**, so the pooled ratio, the median and
the bracket are all the same single value. "V3, 25 seeds" is the previous revision's published
figure over its full campaign, quoted for magnitude only: it is a different population.*

| configuration | `A0` calls/eval | `A1` calls/eval | `A1/A0`, n = 1 | V3, 25 seeds |
|---|---|---|---|---|
| `large_tokamak_nof` | 126 | 60 | **0.4762** | 0.522 |
| `low_aspect_ratio_DEMO` | 105 | 60 | **0.5714** | 0.568 |
| `st_regression` | 126 | 62 | **0.4921** | 0.502 |

*Caption: the two predicates, per configuration, over the same runs — **in separate columns,
because their sum belongs to neither test**. "Width" is components compared per evaluation of that
test. The empty-visit share quoted is the **sweep** share.*

| configuration | arm | coupling-state tests | width | width by block | objective/constraint tests | empty-visit sweep share |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | `A0` | 6 | 840.0 | FLAT 840 | 0 | 0.00 % |
| `large_tokamak_nof` | `A1` | 12 | 241.2 | M1 258 · M2 240 · M3 221 | 0 | 0.00 % |
| `low_aspect_ratio_DEMO` | `A0` | 5 | 846.0 | FLAT 846 | 0 | 0.00 % |
| `low_aspect_ratio_DEMO` | `A1` | 12 | 243.2 | M1 259 · M2 244 · M3 221 | 0 | 0.00 % |
| `st_regression` | `A0` | 6 | 827.0 | FLAT 827 | 0 | 0.00 % |
| `st_regression` | `A1` | 13 | 233.6 | M1 268 · M2 216 · M3 223 | 0 | **6.67 %** |

The empty-visit sweep share is **0 / 0 / 6.67 %** over *these* runs — one empty block sweep out of
fifteen dispatch sweeps on `st_regression`'s `A1` at seed 1. The brief carries A58's figure of
10.84–11.30 % for the same configuration; that is a different population with a different sweep
total, and this table quotes what it measured rather than what a prior task measured elsewhere. The
**visit** share is larger and is never quoted: a block visited with no members costs no sweep at
all.

*Caption: the ownership rung over the `paired_entries` source — the flat control against the flat
control with the burn time held at the seed's perturbed constant, both entered from the same
displaced state at seed 1. n = 1 pair per configuration. The residual is constraint 93's own
function at exit, |value|.*

| configuration | `A0p/A0` | burn-time residual, s | relative |
|---|---|---|---|
| `large_tokamak_nof` | 0.8333 | 292.2 | 1.07e-01 |
| `low_aspect_ratio_DEMO` | 1.0000 | 1069.1 | 9.65e-02 |

*Caption: the predicate trial, from gate G8's own verdict, in the plan's §4.2.5 shape. Population:
12 pairs (2 arms × 3 configurations × 2 seeds), each run under both rulers = 24 runs at δ = 0.10.
"Crossings" and "verdicts changed" are the plan's **two** decisive-pass counts; only the second can
make two runs differ. The audit is read on **both** rulers for **both** runs of every pair.*

| | value |
|---|---|
| pairs | 12 |
| predicate evaluations observed | 143 |
| decisive passes — **crossings** | 13 |
| decisive passes — **verdicts changed** | **0** |
| component events behind those crossings | 66 |
| pairs bit-identical | **12 / 12** |

### 8.2 The optimisation phase

*Caption: the cost ratio against the flat control, per configuration, over the
`reference_runs · BR·B0·B3` arm group at seed 0 — n = 1 seed, every arm converged. Node calls are
summed over `attempts[]`; the identity that licenses that is below. "V3, campaign" is the previous
revision's published figure over its full campaign, quoted for magnitude only.*

| configuration | `BR` | `B0` | `B3` node calls | `B3/B0` with retried | without retried | retried seeds | V3, campaign |
|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 42 567 | 43 449 | 28 055 | **0.6457** | 0.6457 | 0 | 0.64 |
| `low_aspect_ratio_DEMO` | 89 964 | 86 877 | 45 496 | **0.5237** | 0.5237 | 0 | 0.45 |
| `st_regression` | 39 669 | 42 756 | 23 505 | **0.5497** | 0.5497 | 0 | 0.53 |

The `low_aspect_ratio_DEMO` figure differs from the previous revision's published 0.450 in the
direction A44 (transfer-gap) predicted: that revision's 0.450 carried one seed on which the flat
arm retried and both attempts were charged to it. **No run in this population retried**, so the
with- and without- columns are the same number and the pair of columns is the statement that
nothing here depended on a retry.

*Caption: the summation identity over every optimisation record of the reference set. "Residual" is
the run's solve-phase total minus the sum over its attempts, for node calls and for sweeps.*

| | value |
|---|---|
| optimisation records checked | 14 |
| residual 0 on node calls | **14 / 14** |
| residual 0 on sweeps | **14 / 14** |
| records retried | 0 |
| check 2's two constructions disagreeing | 0 |

*Caption: checks 1 and 2 over the `BR·B0·B3` groups at seed 0, n = 1 seed per configuration. `r` is
the paired relative objective difference; the threshold is `max(10 × yardstick, 1e-6)` with the
yardstick the `BR → B0` spread measured in the same population. Check 2's acceptance statistic is
the **summed** median; the final-attempt median is beside it, and equals it because nothing
retried.*

| configuration | yardstick `BR → B0` | `B0 → B3` r | threshold | check 1 | check 2 summed median | evaluations median | check 2 |
|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 4.16e-16 | 7.98e-11 | 1.00e-06 | **PASS** | 1.0000 | 2.6559 | **PASS** |
| `low_aspect_ratio_DEMO` | 5.06e-15 | 6.85e-07 | 1.00e-06 | **PASS** | 0.8125 | 2.1174 | **PASS** |
| `st_regression` | 3.83e-14 | 5.35e-15 | 1.00e-06 | **PASS** | 1.0000 | 2.5817 | **PASS** |

The evaluation-count column is why check 2 is published beside it: the iteration ratio is 1.00 on
two configurations while the evaluation ratio is 2.1–2.7, because iterations miss the lifted arm's
extra stencil column and the line-search evaluations that vary at equal iteration count.

### 8.3 The achieved accuracy, and why its caption names the instrument

*Caption: the exit audit at the accepted optimum over the reference runs. **Audit position:
`after_run`** on every row — the reproduction gate audits where the previous revision measured, and
the campaign's declared position is `entry_to_write_output_files`. The two are different quantities
and share this table only because the position is a column of its own.*

| | value |
|---|---|
| restricted maximum, every arm, both rulers | **exactly 0** |
| components above τ | 0 |
| components excluded from the restricted statistic | 122 (nof) · 123 (lad, st) |
| audit position | `after_run`, on all 14 |
| audit instrument | "snapshot recorded with no position taken" |

**This is the finding of A61 (insstrain-diagnosis) appearing in the tally's own table, from the
other side.** A61 showed that at the *declared* position the audit reports ~7e-3 on
`tfcoil.insstrain` because PROCESS's output path permanently changes a model setting the snapshot
does not restore — so the audit's sweep is not the loop's map. At `after_run` the audit is taken
*after* that path, so the sweep reproduces the state exactly and the residual is **0**. Same runs,
same models, two audit positions, two completely different numbers. That is precisely why the
position and the instrument are columns and not prose, and why **no argmax is written into this
tally**: it is read from the record, and where the maximum is exactly 0 the table says "every
component exactly 0" rather than naming a component.

---

## 9. The teeth

*Caption: one row per tooth of `tally_contracts`. "Break" is what is deliberately done; "must" is
what the criterion has to do about it. Every tooth acts on a **doctored in-memory copy** — a table
built to be wrong, a record dict with one number moved, a copy of the committed reference — and
**none starts a PROCESS run**. 10 of 10 tripped at every press.*

| # | tooth | break | must | tripped |
|---|---|---|---|---|
| 1 | no caption | a table built with no caption | REFUSE | ✔ |
| 2 | no denominator | a table built with no denominator | REFUSE | ✔ |
| 3 | placeholder denominator | the plan's `n` where a count belongs | REFUSE | ✔ |
| 4 | timing column | a wall-clock column in an acceptance table | REFUSE | ✔ |
| 5 | pooled predicates | one column adding the two tests' counts | REFUSE | ✔ |
| 6 | audit-position mix | two residuals at two positions, unlabelled | REFUSE | ✔ |
| 7 | a demonstration in a population | a record stamped `force_maxcal` | REFUSE, by name | ✔ |
| 8 | check 2's constructions | a **failed** attempt's iteration count moved by one | the two constructions must separate: final reads 7, summed reads 19 not 18 | ✔ |
| 9 | the summation identity | a run total moved by one against its attempts | the identity reports residual 1, and the contract refuses | ✔ |
| 10 | a reference cell moved | one published cell of the committed reference incremented | the comparison goes from **0 to 1** differing cells of 270 and does not pass | ✔ |

**Tooth 10 is differential, and that was a correction.** Its first form required the doctored
comparison to report exactly one differing cell, which only works once the criterion already
passes — a tooth that cannot be run until the gate passes is the wrong way round. It now compares
the doctored count against the undoctored one and requires exactly one more.

**Tooth 8 is not a refusal**, and it is the one that says something. Moving a *failed* attempt's
iteration count leaves the final-attempt construction unchanged and moves the summed one by exactly
one. That is the whole reason the plan publishes both, made into a check.

---

## 10. The runs this task made, and the one it had to throw away

*Caption: PROCESS runs started through `harness/pool.py`, counted from the records on disk. Every
run is a fresh subprocess in its own working directory with `PYTHONPATH` naming the experiment's
own copy of PROCESS, and asserts the exact tree it imported before doing any work. Wall clock is
the sum of the children's own timings and is **context, never evidence** (I-10).*

| | count |
|---|---|
| evaluation-phase runs | 109 |
| optimisation-phase runs | 49 |
| census runs | 3 |
| **records on disk** | **161** |
| of which made by `--gate all` from nothing, at `cd62c510` | 152 |
| of which made by `--measure all`'s output-path contrast stage, at `de7e5a2b` | 6 |
| stamped `campaign_run_kind = gate` | 159 |
| stamped `smoke` | 2 |
| stamped `force_maxcal` (a demonstration, never a population) | 1 |
| runs that did not finish | 0 |
| summed in-child wall clock | ≈ 2 182 s (≈ 36 min) at 3 workers — context only |

**No campaign record exists.** `EXECUTION_APPROVED` is `False` and every campaign stage refuses.

**One earlier press was discarded in full.** The first `--gate all` was started before the code was
finished, and this task edited `harness/child.py` — the module every measurement subprocess imports
— while it was still executing. Children started after that edit stamped records under the new
field names while the parent compared under the old ones, and **gate G8 failed**: 11 of 12 pairs
bit-identical, one pair differing with no verdict change, which is exactly what a half-renamed
record set looks like. The whole of `runs/` was deleted and the press re-run from nothing with
nothing touched while it executed; G8 passes. The queue's rule is "no commit while a measurement
run executes"; the lesson here is the stronger one — **no edit to anything a child imports**, and
the two are not the same rule. §12 proposes the amendment.

**The second press from the repository root was dropped** on the user's instruction (relayed
2026-09-11) to reduce PROCESS runs. Working-directory independence is therefore **not** demonstrated
by this task; it is covered by A52's capability gate, whose decoy tooth shows the probe importing
the tree under test from a working directory containing a shadowing `process/` package, and that
gate passes in this press. Every verdict and every table states, in its own provenance line, the
commits of the records it read.

---

## 11. Autonomous decisions, each with its reversal

*Caption: one row per decision this task took without asking, why, and how to undo it.*

| # | decision | why | reversal |
|---|---|---|---|
| 1 | the tally reads **declared sources**, not "the gate runs" | averaging across `runs/gates/` produced a per-run mean over a set nobody can state — caught in this task's own output | drop `tally.SOURCES` and walk the whole tree; the denominators then cover records that are not comparable |
| 2 | the optimisation phase is split into **seed-complete arm groups** | the plan's one-seed-set construction returns an empty set over a source that runs different arms at different seeds | remove `arm_groups`; every optimisation table then reads n = 0 over the gate runs |
| 3 | `stats.py`, `tables.py`, `tally.py`, `tally_evaluation.py`, `tally_optimisation.py`, `gate_tally.py` — six modules, all in `harness/` | the plan's tree puts `phase_a.py`/`phase_b.py` at the top level; the brief allows naming for what they do, and everything else the gates use already lives in `harness/` | move the two phase modules up a level; the imports change and nothing else |
| 4 | `inner_sweeps_by_block` and `inner_solves_by_block` renamed with `outer_pass_hist` | the ruling names `outer_pass_hist`; renaming one key of a dictionary and not its siblings leaves it half-translated | drop the two entries from `FIELD_NAME_MAP` and `child.BLOCK_LOOP_KEYS`; GR then compares the old names |
| 5 | the compared cell list is **derived** from `REFERENCE_FIELDS` ∩ what the entry published | A62 will change that list, and a hard-coded copy would keep comparing a cell nobody compares | write the list out; it then needs editing at every change to the compared set |
| 6 | three cells are compared through **this revision's constructions** rather than read from a field | a rule landing on the previous revision's number is a stronger statement than a field matching a field | read them as fields; the check then duplicates the reproduction gate |
| 7 | a base-anchored table is **not produced** where the arm group has no `B0`, and the omission is named | an emitted table with a denominator and no rows states a denominator for nothing | emit it empty; a reader then has to work out why it is blank |
| 8 | an argmax over an exactly-zero maximum prints "every component exactly 0" | `max()` over an all-zero vector names whichever key sorts first, which reads as a finding | print the argmax; the table then names a component for a residual of 0 |
| 9 | `TallyError` subclasses `framework.GateError` | the button reports every other refusal as `REFUSED — …`; an uncaught traceback reads like a crash | make it a plain `RuntimeError`; the refusal then escapes as a stack trace |
| 10 | the registry additions are **one contiguous block** in `gates.py` | the orchestrator asked for it, against A62's merge | scatter them; the merge conflicts in the middle of a dictionary |
| 11 | record-contract refusals are printed **five at a time** with a count of the rest | 100 identical sentences buried the tables; all of them are in the stage's own record | raise `REFUSALS_PRINTED`; the terminal fills with the same sentence |

---

## 12. Handover

### To the orchestrator — what the plans and the queue should gain

*This task edited no plan, no queue row and no improvement item; those are the orchestrator's.*

- **Harness plan, Appendix A — amendment 15**: H6 delivered. `stats.py` with every declared
  construction as a documented function; `tables.py` with six refusals at construction; the two
  tally stages over declared sources, split into seed-complete arm groups; `tally_contracts` with
  ten teeth; the record-field rename with `reference.FIELD_NAME_MAP`, GR re-run at 270/270. §4.2's
  `stats.py` and `tables.py` paragraphs are realised; §4.1's `phase_a.py`/`phase_b.py` are delivered
  as `harness/tally_evaluation.py` and `harness/tally_optimisation.py` (decision 3 above).
- **Harness plan, amendment 13 should gain a rule (vi)**: *no edit to any module a measurement
  child imports while runs execute.* Rule (v) forbids the commit; this task showed the edit alone
  is enough to corrupt a population, and it cost a full press (§10).
- **The experiment plan's §4 placeholder tables** can now be filled by
  `--measure tally_evaluation` / `--measure tally_optimisation`, which emit markdown. This task did
  not edit the plan.
- **The queue's A53 row** is delivered except for the second press from the repository root, which
  the user's instruction dropped; §10 says what covers it instead.
- **A62 (exit-audit-restore) will move every cell of the achieved-accuracy tables.** §8.3 is the
  before picture, measured: at `after_run` the restricted maximum is exactly 0 on all 14 records,
  while A61 measured ~7e-3 at the declared position on the same runs. The tally reads the
  instrument through one accessor (`stats.audit_instrument`) and prints it in a column, so the two
  are tellable apart after the merge.

### To A54 (harness-analysis)

- **`--verify` compares against the tally's *output*, never its code.** The stage records are
  `runs/gates/tally_evaluation/measurements.json` and `…/tally_optimisation/measurements.json`;
  each table is a `{table, caption, denominator, denominator_is, acceptance, audit_positions,
  columns, rows, markdown}` block, so a cell-by-cell comparison is over `rows` with `columns` as
  the key list. The full cell count at this commit is 65 tables.
- **Do not import `harness/stats.py`.** The whole point of the second implementation is that a
  declared definition reached one implementation and not the other twice (I-18, I-19); an analysis
  that imports the constructions cannot catch that. Read the docstrings as the specification —
  they are written to be readable as one.
- `tally.reference_cells` is the pattern for the previous revision's cells; `tally.SOURCES` and
  `tally_optimisation.arm_groups` are what a population is. A verify over a population the tally
  did not use is a comparison of two different things.
- `analysis.py --verify` is a **gate** and belongs under `--gate` with teeth; `--tables` is a
  measurement. `framework.gate_from_check` promotes a criterion without restating it.
- **`--verify` must refuse on an empty comparison.** `tally_contracts` already refuses when the
  tally emits no table at all; the same shape applies one level up.

### To A55 (harness-smoke)

- **The one-button chain is** `--gate all --resume --census-entry evaluation`, then `--measure all`.
  Both return 0 at this commit. `--gate all` runs cheapest first and stops at the first failure.
- **The tally stages start no PROCESS run** — they read records — so a smoke can run them for free
  after any gate press. `--measure output_path_measurements` **does** make runs (6 contrast runs);
  it is the only measurement stage that does.
- **`--resume` is load-bearing for the tally**: without it a population whose records were made at
  an earlier commit is refused with exit code 3. That is the right behaviour and a smoke should not
  route around it.
- The gate records are resume-compatible; a smoke that reuses `runs/gates/` re-makes nothing.

---

## 13. Limits of what is reported here

- **Every table in §8 is over one or two seeds per arm.** They demonstrate the constructions on
  real records; they are not campaign statistics and no cell may be quoted as one. The comparison
  with the previous revision's campaign figures is for **magnitude only** and the two populations
  are different.
- **The tally has been exercised on the gate populations, not on a campaign population.** Several
  constructions have not been exercised at all because nothing in these records triggers them: no
  run retried, so the with/without-retried split is two identical columns and the retry-specific
  paths of `with_and_without_retried` are untested against a real retry; no seed failed, so the
  failure table has no rows; no pair hopped clusters, and no pair fell below cluster resolution.
- **The empty-visit sweep share here is 0 / 0 / 6.67 %**, not the 10.84–11.30 % the brief quotes
  from A58. Different population, different sweep total. Neither number travels without its
  population.
- **`tfcoil.insstrain` does not appear in these tables** because the reference runs audit at
  `after_run`, where the instrument artefact A61 identified does not arise. On campaign-shaped
  records audited at the declared position it will, and the tally reads the argmax from the record
  rather than naming it.
- **The reproduction of the previous revision's cells covers 270 values over 20 runs**, which is
  what that revision published for those runs. It says nothing about cells it never published, and
  nothing about seeds it never ran.
- **Working-directory independence is not demonstrated by this task** (§10); A52's capability gate
  covers it and passes here.
- **Every timing in this report is context.** No verdict rests on one; every acceptance quantity is
  a count or a bit-comparison.
- **The first press was discarded**, so no number in this report comes from it. The figures come
  from the press at `cd62c510` and the reader stages run after it, each naming the commits of the
  records it read.

---

## 14. Change log

- **2026-09-11** — written by task **A53 (harness-tally)** at branch `A53-harness-tally`, base
  `d13a54c7`. Commits: `7cea0246` (`stats.py`, `tables.py`), `a067777f` (the two tally stages),
  `835b946e` (the record-field rename and `reference.FIELD_NAME_MAP`), `cd62c510` (the tally's gate
  and the registry block), `de7e5a2b` (the achieved-accuracy table, the derived cell list, the
  README's §13), `6cc71a07` (the not-produced tables, the zero argmax, the refusal's type).
- **The press every figure here comes from** is `experiment_runner.py --gate all --census-entry
  evaluation`, run from the experiment directory at `cd62c510` with `runs/` deleted first and
  nothing touched while it executed: **22 PASS, 0 FAIL, 119/119 teeth, 152 records**. Followed by
  `--measure all` (8 stages, 6 further records) and, after the last two commits, by
  `--gate tally_contracts --resume` and the two tally stages, which make no run: 161 records before
  and after.
- **An earlier press was discarded in full** (§10): it ran while `harness/child.py` was being
  edited, and gate G8 failed on a half-renamed record set. No number from it appears here.

---

## 15. Orchestrator's critical assessment (protocol §5)

*Written by the orchestrating session on 2026-09-11, before the merge, by differing checks and without repeating the agent's press (harness plan amendments 13 and 15).*

### 15.1 What was verified, and how

- **Scope.** Eighteen files, +5 895 / −45, all under `harness/`, the runner and the report; nothing under `…_v4/PROCESS/`, the repository-root `process/`, the plans, `harness/data/` or `harness/reference/`. Merge dry-run against trunk (`f6c522ed`, after A61's merge and amendment 15): no conflict.
- **The rename, read as one diff (`835b946e`).** Nine modules; the translation from the driver's dictionary keys happens at exactly one place, `child.BLOCK_LOOP_KEYS`, where the counters become record fields; `reference.FIELD_NAME_MAP` carries the reverse map with a reason per key; `REFERENCE_FIELDS` stays in the previous revision's spelling and the committed reference keeps its bytes. No retired name survives in executable harness code except the two maps and a display-label table keyed on the previous revision's paths. GR 270/270 on the branch is the agent's; the orchestrator did not repeat it — one GR runs at the tip after A62 merges, since both tasks touch the run path.
- **The gate, pressed by the orchestrator.** `--gate tally_contracts` starts no PROCESS run. Without `--resume` on the branch's final state it **FAILS** by the framework's provenance rule — the population is 68 records at `cd62c510` (the press) and 6 at `de7e5a2b` (the output-path contrast runs `--measure all` made afterwards) — and with `--resume` it **PASSES**: 270/270 published cells over the twenty reference runs, 195/195 table-contract checks over 65 emitted tables, 10/10 teeth. §1's "22 PASS from nothing at `cd62c510`" is true of that press and predates the six contrast runs; the branch's final on-disk state passes under the stated provenance, which is the honest form, and the report should have said so itself.
- **One published ratio recomputed by hand** from the records with an independent reader: `A1/A0` node calls per call at seed 1 — 60/126, 60/105, 62/126 — gives 0.4762 / 0.5714 / 0.4921 on the three configurations, the report's figures to four places.
- **Record stamps surveyed**: 150 at `cd62c510`, 6 at `de7e5a2b`, 0 campaign, as the report states.

### 15.2 Judgements

1. **Accepted.** The constructions are functions whose docstrings are the declarations; a table cannot exist without its caption and denominator; the tally refuses a demonstration record, a pooled-predicate column, an unlabelled audit-position mix and a mixed-commit population — each shown by a tooth. That is what H6 asked for.
2. **Decision 4 (two sibling keys renamed beyond the ruling) is endorsed**: a half-translated dictionary is worse than a wider rename, and the map records both.
3. **Decision 7 (base-anchored tables not produced, named with reasons) stands**; an empty table with a denominator states a denominator for nothing.
4. **The empty-visit sweep share is 0 / 0 / 6.67 % on this population, not A58's 10.84–11.30 %**, and the report says so rather than borrowing. A53's queue row had asked for A58's figures to be quoted in the disclaimers; the correct rule is the one the report applies — quote the share measured on the population the table is over — and the row is corrected at this merge.
5. **§8.3 is the before picture of A62's change** and is worth keeping in the archived report: at `after_run` the restricted maximum is exactly 0 on all 14 reference records, at the declared position ~7e-3 on the same runs (A61). Position and instrument are columns; no argmax is hard-coded; the compared cell list is derived, so A62's drop of the audit residual lands here without an edit.
6. **The agent's broken press.** Editing `child.py` while a press ran corrupted the population and cost a full press. Rule (vi), *no edit to any module a measurement child imports while runs execute*, is written into the harness plan at this merge.
7. **A54 must not import `harness/stats.py`** — endorsed and carried into A54's brief; the second implementation exists to catch a definition that reached one and not the other.

### 15.3 Consequences recorded at this merge

A53 row MERGED with the corrected disclaimer rule; A54 dispatched on a worktree seeded with A53's relocated records (no new press); harness plan amendment 16 (H6 delivered; rule (vi)); experiment plan change log. The plan's §4 tables are filled once at the final tip by the smoke, not now, since A62 will move every audit cell.

### 15.4 Limits

One gate pressed and one ratio recomputed; the rest is the agent's own records, read with their commit stamps. No timing is evidence.
