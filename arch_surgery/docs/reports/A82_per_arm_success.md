# A82 (per-arm-success) — reliability stated per arm, the case study named, the wall-clock section withdrawn

> **Document status** — **OPEN**. Task report of **A82 (per-arm-success)**, branch
> `A82-per-arm-success` off `architecture_surgery` at `4878688e` (after A80
> (report-accuracy-audit)'s merge). Zero PROCESS runs: every number below comes from the campaign's
> 949 records at `57dc0c14`, read through the harness, and from a committed script named beside it
> (protocol §15). Rulings executed: **D29** (2026-09-15, the user, on A81 (benchmarking-practices)'s
> finding F1) and **D30** (2026-09-15, the user, on A80's §9 question), both quoted in the queue's
> decisions register. Arm names are today's `BR / B0 / B1 / B2`; the records stamp the names of their
> day and are translated at read (trap T16).

## 1. Verdict

**Done. One new construction, three new report tables, five prose edits and two dated brackets; no
verdict, ratio, residual or acceptance count changed.** Reliability is now stated per arm over the
starts offered, beside the seed-set filter it complements, and it is **reported, not accepted on** —
no pre-declared rule of the plan reads a per-arm rate, and the caption says so.

**The table as rendered** (Appendix D, `per_arm_success`; the seeds behind each cell are companion
Tables F.47–F.49, the per-seed classes companion Tables F.14, F.18 and F.22):

**Table D.67 — `large_tokamak_nof`.**

| arm | starts offered | accepted optima | crashed (RuntimeError) | lost, another arm accepted | seed set (every arm accepted) |
|---|---|---|---|---|---|
| BR | 25 | 22 | 3 | 0 | 22 |
| B0 | 25 | 22 | 3 | 0 | 22 |
| B1 | 25 | 22 | 3 | 0 | 22 |
| B2 | 25 | 22 | 3 | 0 | 22 |

**Table D.68 — `low_aspect_ratio_DEMO`.**

| arm | starts offered | accepted optima | finished, ifail = 5 | crashed (RuntimeError) | coupling-loop cap (ModuleSolveFailure) | lost, another arm accepted | seed set (every arm accepted) |
|---|---|---|---|---|---|---|---|
| BR | 25 | 12 | 11 | 2 | 0 | 0 | 11 |
| B0 | 25 | 12 | 9 | 2 | 2 | 0 | 11 |
| B1 | 25 | 11 | 9 | 2 | 3 | 1 | 11 |
| B2 | 25 | 11 | 9 | 2 | 3 | 1 | 11 |

**Table D.69 — `st_regression`** (`B1` is inactive there).

| arm | starts offered | accepted optima | finished, ifail = 5 | lost, another arm accepted | seed set (every arm accepted) |
|---|---|---|---|---|---|
| BR | 25 | 24 | 1 | 0 | 22 |
| B0 | 25 | 23 | 2 | 1 | 22 |
| B2 | 25 | 23 | 2 | 1 | 22 |

The accepted counts are the ones D29's dispatch expected and A80 (report-accuracy-audit) verified
from the records: **lad 12 / 12 / 11 / 11, st 24 / 23 / — / 23, nof 22 / 22 / 22 / 22**, all of 25.
The per-seed table on lad reproduces A80's `ifail` pattern exactly — 11 seeds `(1,1,1,1)`, 9
`(5,5,5,5)`, 2 all-crash, 2 `BR` at `ifail = 5` with the three coupling-state arms at their cap, and
**1 seed (10) `(1,1,cap,cap)`**: 11 + 9 + 2 + 2 + 1 = 25.

**The two sentences.** §4.3's population paragraph now ends: *"Per arm, of the 25 starts offered,
accepted optima are 22 / 22 / 22 / 22 on nof, 12 / 12 / 11 / 11 on lad and 24 / 23 / — / 23 on st for
`BR` / `B0` / `B1` / `B2` — 88 %, 48 % / 44 % and 96 % / 92 % — with every other start named by
outcome class in Tables D.67–D.69 (per-arm success) and per seed in companion Tables F.14, F.18 and
F.22; the table is reported, not accepted on (D29, 2026-09-15)."* §5.7 gains the same rates related
to the filter: the intervention arms lose one start on lad (seed 10) that the flat arms solve, and on
st the two asymmetric failures **cancel in count and not in cost** — `B2` gives up on seed 5 after
479 630 node calls where `B0` accepts at 175 413, and `B0` gives up on seed 10 after 667 989 where
`B2` accepts at 129 012 (companion Table F.23); the seed set drops both starts and neither cost
enters a ratio.

**§6, one clause** (D29 (3)): the preamble now reads *"…with its number, denominator and pre-declared
verdict — three configurations, so this is a case study and not a benchmark set, and the conclusion
it licenses is an existence proof that the architecture alone changes the cost in model-node
evaluations (D29, 2026-09-15)."* Nothing else in §6 moved.

**The withdrawn promise** (D29 (2)): §3.5 check 5's *"wall-clock context (3 serial repetitions, median
and range) is reported in its own section"* now carries a dated as-built bracket saying the section is
**not written and the promise withdrawn**, with the user's words in short; §1's other mention of the
non-node cost term carries the matching bracket. The plan text itself is not rewritten (D17: the plan
as approved stays on the page, the as-built note sits beside it).

**D30 recorded** (the coordinator's mid-task addition): §5.6 replaces A80's deferral with the ruling —
V4's numbers are `frozen`-ruler numbers; the adoption rule was met (G8, 12 of 12 pairs bit-identical)
and not applied because the campaign was pressed before the rule was re-read; nothing
acceptance-bearing depends on it (the exit audit is printed on both rulers, the cost quantities are
node calls of runs made under `frozen`, and since `mixed` is never tighter a change of ruler could
only have stopped some runs earlier — not applicable to runs already made, only to their reporting);
keeping `frozen` keeps V4 on V3's ruler, so the 0.64 / 0.45 / 0.53 context numbers stay comparable;
V5 applies the rule before its campaign or drops it. §3.6's as-built bracket gains *"— ruled D30,
2026-09-15: the departure stands"*.

**Gates at the end** (all `--resume`, 0 PROCESS runs): `recomputation` PASS **15 122 / 0** over 107
tables (from 14 445 / 0 over 101), 9 of 9 teeth; `tally_contracts` PASS **577 / 0** (321 table checks +
256 reference cells; from 559), 11 of 11 teeth; `run_kind_separation` PASS **3 000 / 0**, 9 of 9;
`self_containment` PASS **52 / 0**, 1 of 1; the gate table **30 PASS / 0 FAIL, 161 of 161 teeth**.
`--plan-tables check` IDENTICAL for both documents (1 256 and 4 209 lines), **0 dangling references**
over 124 + 30 resolved. Stamp survey **1 102 records, 0 whose commit changed, 0 new, 0 gone**.

## 2. The construction, and where it is injected

**Declared once** — `harness/measurement/stats.py`, whose docstring *is* the declaration:

- `stats.outcome_class(record)` — one label per start, from the same two sources
  `accepted_optimum` reads plus the harness's failure class: `accepted` (status ok **and** MFILE
  `ifail == 1`); `finished, ifail = k` (the run finished, the optimiser exited with another code —
  `ifail = 5` is VMCON's four-attempt ladder exhausted); `crashed (<Exception>)` for failure class
  `crashed`, the exception named from the traceback's last line; `coupling-loop cap
  (ModuleSolveFailure)` for failure class `unconverged` — the coupling-state loop refusing at its
  20-sweep cap, which the harness also stamps `crashed`; any other failure class by its own name. The
  classes partition the starts.
- `stats.per_arm_success(by_arm, seeds)` — per arm the starts offered, the accepted optima, every
  other start by class with its seeds, and the **starts lost that another arm accepted** (the
  asymmetric failures; a seed *no* arm accepted is configuration hardness and is not one), with the
  seed set beside and a per-seed part (each arm's class, how many arms accepted, membership of the
  set, which arms lost it).

**Computed** in `harness/measurement/tally_optimisation.py` (`per_arm_success`, kind
`per_arm_success` plus the detail kind `per_arm_success_by_seed`), emitted per configuration and arm
group immediately after the seed-set table. **Re-derived independently** in
`harness/measurement/analysis.py` (`_per_arm_success`, `outcome_of`), which imports none of the
tally's constructions and rebuilds the classification from the docstring and the record fields
`status`, `mfile.ifail`, `failure_class` and `traceback`; gate `recomputation` compares the two cell
by cell without tolerance. **Placed** in `harness/measurement/plan_tables.py`: the summarising table
joins group D.4 between `seed_set` and `same_optimum` (the renderer numbers), the per-seed table goes
to the companion file's F.2 group, both kinds get a title in `KIND_TITLES`, and D.4's context
paragraph gains one sentence.

**Captions** follow A79's rule: the report prints a few lines (the summary) with the construction name
under the grid; the full declaration — units, row, column, construction, the four clauses, how to read
— is printed once in D.0 under *per-arm success*. The first clause is the caption's own statement that
the table is **reported, not accepted on**.

## 3. The re-derivation's agreement

Two independent routes beside the tally's cells:

1. **Gate `recomputation`** — `analysis.py`'s tables against the tally's: 107 tables, **15 122 cells
   compared, 0 mismatched**, no tolerance. The six new tables (3 per-arm + 3 per-seed) and the 51
   cells A80 added account for the growth from 101 / 14 445.
2. **`report_counts_check.py` §12** (committed at `ca7eefa3`, run at `1b6a7522`) — a third route: it
   classifies every optimisation record by a rule written out in the script itself and prints the
   counts beside the cells the tally published in
   `runs/gates/tally_optimisation/measurements.json`. **20 comparison lines, 20 `same`, 0 `DIFFERS`**:
   accepted optima per arm on each configuration (twice — against the report's sentence and against
   the table's cells), each outcome-class column, the lost starts, the starts offered, and the
   partition identity *accepted + the class columns = starts offered* (25 in every row). The script's
   overall exit status is 3 because of the **four pre-existing `DIFFERS` lines A80 left deliberately**
   (the report's old "28 crashed" wording, the stencil budget 418 vs 396, and `copy_identity`'s 7
   recorded permitted-edit files); the committed version at `HEAD~4` prints the same four.

## 4. Gate results, with denominators (worktree root, everything committed, nothing running)

| step | result |
|---|---|
| `--measure all --resume` | exit 0; stages re-made over kept records; **0 PROCESS runs** |
| `--gate recomputation --resume` | **PASS**, 15 122 compared / 0 mismatched over 107 tables and 949 run records; 9 of 9 teeth tripped |
| `--gate tally_contracts --resume` | **PASS**, 577 compared (321 table checks + 256 reference cells) / 0; 11 of 11 teeth |
| `--gate run_kind_separation --resume` | **PASS**, 3 000 compared / 0 over 1 102 records; 9 of 9 teeth |
| `--gate self_containment --resume` | **PASS**, 52 files / 0 findings; 1 of 1 tooth |
| `--measure gate_table --resume` | **30 PASS, 0 FAIL, 0 not run; 161 of 161 teeth tripped** |
| `--plan-tables write`, then `check` | Appendix D **83 tables** (from 80), companion **162** (from 150), 38 836 cells; **IDENTICAL** for both documents, 0 hunks; 124 + 30 references resolved, **0 dangling** |
| `run_stamp_survey.py` before/after | 1 102 records both times; **0 whose commit changed, 0 new, 0 gone** — 949 at `57dc0c14`, the rest at the gate commits |
| `report_counts_check.py` | 68 comparison lines, 64 `same`, 4 `DIFFERS` — the same four the committed baseline prints; the 20 new §12 lines all `same` |
| `merged_names_check.py` | exit 0 — 24 (arm, configuration) pairs identical; 44 400 evaluations identical over 185 reference hex values |
| `harness_survey.py` | ran; harness 51 486 lines (measurement 13 394) |
| `--selfcheck` | **PASS**, every promoted self-check with its teeth |

Nothing under `arch_surgery/MDA_partitioning_experiment_v4/PROCESS/`, `harness/child/` or the root
`process/` changed; `EXECUTION_APPROVED` untouched; no `git add -A`.

## 5. The re-pointed citations (trap T17)

Appendix D grew by 3 tables placed at D.67–D.69, so **every `Table D.n` with n ≥ 67 moved by 3**; the
companion file grew by 12, so its numbering shifts from F.14 on. `--plan-tables check` catches a
dangling number, not a shifted one, so every numbered citation in the hand-written text was re-read.
**30 citations re-pointed**, all in `EXPERIMENT_REPORT.md` unless said otherwise:

| where | was | now | what it names |
|---|---|---|---|
| §4.3 (×2) | F.17 | F.19 | the lad failure table |
| §4.3 (×3), §5.1 (×2), §5.3, §5.8, `report_counts_check.py` (×2) | D.73–D.75 | D.76–D.78 | cost (check 4) |
| §4.3, §5.1 | D.70–D.71 | D.73–D.74 | check 2 on the pulsed configurations |
| §4.3 | D.67–D.69 | D.70–D.72 | check 1 (same optimum) |
| §4.3, §5.1 | D.70–D.72 | D.73–D.75 | check 2 |
| §4.3 | D.79–D.80 | D.82–D.83 | the lift closed (check 3) |
| §4.3, §5.4 | D.76–D.78 | D.79–D.81 | achieved accuracy |
| §4.3 | F.48 | F.54 | lad's per-run components-above-τ column |
| §4.3, §5.4 | F.47–F.49 | F.53–F.55 | the per-run accuracy columns |
| §4.3 | F.15–F.22 | F.16, F.20, F.24 (the identity) and F.17, F.21, F.25 (the per-run overhead) | split rather than re-ranged: the old range no longer names one thing |
| §4.4 | D.2–D.80 | D.2–D.83 | every recomputed table |
| §4.4 | F.50–F.150 | F.56–F.162 | the recomputed tables in the companion file |
| §5.1 | D.79–D.80 | D.82–D.83 | the lift closed |
| §5.1, §5.5 (×2) | F.16, F.19, F.22 | F.17, F.21, F.25 | the per-run overhead tables |
| §5.1 | D.68 | D.71 | check 1 on lad |
| §5.5 | F.16 | F.17 | nof's per-run overhead, seed-0 rows |
| §5.7 | F.14, F.17, F.20 | F.15, F.19, F.23 | the three failure tables |

Unchanged and re-read: every `D.n` with n ≤ 66, `F.1`–`F.13` (the evaluation phase's per-run tables and
the predicate trial). **Appendix C's dated entries keep the numbers of their day** — A79's entry still
says "150 tables" and "F.1–F.150", as the arm-name convention requires for a dated record; the new
entry says so.

## 6. Autonomous decisions, each with its reversal

1. **Two tables rather than one.** The counts go to Appendix D and the seeds to the companion file, as
   a summarising table plus a `detail` table (the user's rule that the report carries no per-seed
   tables). The report table still carries the seed columns in the record and names its full version.
   *Reverse:* drop `per_arm_success_by_seed` and let the omitted columns carry the seeds — one fewer
   table, a per-seed grid in the companion only.
2. **The outcome classes are named, not numbered.** `finished, ifail = 5`, `crashed (RuntimeError)`,
   `coupling-loop cap (ModuleSolveFailure)` are column headings derived from the records, so a class
   that never occurs never appears (nof has one column, lad three). *Reverse:* a fixed column set with
   zeros, at the cost of columns that mean "did not happen here".
3. **"Lost, another arm accepted" is the asymmetry column**, excluding seeds no arm accepted
   (configuration hardness, already the seed-set table's *configuration-invalid* column). *Reverse:*
   count every non-accepted start as lost — which would read 13 on lad for every arm and hide the one
   start the intervention arms actually lose.
4. **The `F.15–F.22` citation was split rather than re-ranged.** Its endpoints now map to tables of
   two kinds with three new tables between them, so a range would have been silently wrong. *Reverse:*
   write `F.16–F.25` and accept that the range names six tables it does not mean.
5. **`report_counts_check.py` extended rather than a new script.** A80's script is the committed route
   for "every count the report states"; the per-arm counts belong in it. *Reverse:* a separate
   `per_arm_success_check.py`, at the cost of two scripts to run for one question.
6. **The two brackets are as-built notes, not rewrites.** §3.5 check 5 and §1 keep their text and gain
   a dated bracket. *Reverse:* rewrite the plan sentences — which would erase what was promised before
   the campaign.

## 7. Limits

- **The per-arm rate is descriptive.** No pre-declared expectation exists for it, so it cannot be
  passed or failed; it says what the seed-set filter leaves out and nothing more. The V5 list's item 3
  is where an expectation and a data profile belong.
- **25 starts per arm is a small denominator**, and on lad 13 of the 25 are configuration-invalid, so
  the arm-to-arm difference the table shows there rests on one start.
- **No data profile.** D29 (1) sent it to V5; the construction is in A81's §5 and is not built here.
- **The outcome classes are the harness's**, one level above PROCESS's own: `ifail = 5` covers every
  way VMCON's ladder can end, and `crashed (RuntimeError)` is one exception text in this campaign but
  not a guarantee of one cause.
- **Timings remain unreported**, now by ruling rather than by omission; a reader wanting run time will
  not find it, and §3.5's bracket says why.

## 8. What should change elsewhere (proposals; nothing outside the branch's scope edited here)

1. **Queue**: A82's row to §4.2 with this report's path and the records path the retire script prints;
   D29 and D30 marked discharged for what this task executed (D29 (1) for the V4 half, (2) and (3) in
   full; D30 in full), with D29 (1)'s profile half left standing for V5.
2. **V5 list item 3** may now cite the table by number and name: *Tables D.67–D.69,
   `per-arm success`*. Proposed, not edited.
3. **Harness plan, Appendix A**: an amendment recording that a new table kind must be placed in
   `plan_tables.GROUPS` (the renderer refuses an unplaced kind — the rule worked) and that adding one
   renumbers every table after it, so the prose's numbered citations are re-read in the same task
   (T17's operational form). One line, at the merge.
4. **`harness/README.md` §4** lists what the tallies build; a clause naming per-arm success beside the
   failure taxonomy would keep it complete. Small, not done here.

## 9. Commits (branch `A82-per-arm-success`, off `4878688e`)

| commit | what |
|---|---|
| `068b6f7c` | the construction: `stats.per_arm_success` and `stats.outcome_class`, the two tables in `tally_optimisation.py`, the kind placed and titled in `plan_tables.py` |
| `a3d83122` | the second implementation in `analysis.py` (`_per_arm_success`, `outcome_of`), sharing no construction with the tally |
| `ca7eefa3` | `report_counts_check.py` §12 — the counts re-derived by a third route and printed beside the table's cells; its own citations re-pointed |
| `1b6a7522` | the report: Appendix D and the companion file re-rendered, the two sentences, §6's clause, the two withdrawal brackets, D30 in §5.6 and §3.6, the 30 re-pointed citations, the dated Appendix C entry |
| *(this file)* | the task report |

## 10. Change log

- 2026-09-15 — task opened at `4878688e`; the work above; D30 added to the task mid-flight by the
  orchestrating session on the user's ruling; report written at `1b6a7522`.

## Orchestrator's critical assessment (protocol §5)

*Written 2026-09-15 at `829e3058` by the orchestrating session; gates the merge.*

**Checks.** (1) Table D.68's cells against the `ifail` pattern I derived from the records at A80's merge (11 seeds all-accepted, 9 all-`ifail = 5`, 2 all-crash, 2 `BR` at 5 with the coupling-state arms at the cap, seed 10 lost to `B1`/`B2` alone): accepted 12 / 12 / 11 / 11; `ifail = 5` 11 / 9 / 9 / 9 (`BR` = 9 + 2); crashed 2 each; cap 0 / 2 / 3 / 3 (`B1`/`B2` = 2 + seed 10); lost-to-this-arm 0 / 0 / 1 / 1 — every cell agrees with a derivation that shares nothing with the tally or the analysis. (2) The st asymmetry's costs (479 630 vs 175 413; 667 989 vs 129 012) are the cells §5.7 now cites from the companion. (3) Gates at the tally commit: `recomputation` 15 122 / 0, `tally_contracts` 321 + 256 / 0; `check` IDENTICAL both documents; 0 re-made runs. (4) The D30 wording in §5.6 and §3.6 and the D29 brackets are as ruled. Scope by diff: nothing under `PROCESS/`, `harness/child/`, root `process/`. (5) The report's last two verification lines cite `merged_names_check.py` and `harness_survey.py`, removed from the trunk at `79d044b1` while this task ran — the last citations; the merge carries the deletion.

**Finding for the record, not this task's fault: the presentation of Appendix D.** Reading D.67–D.69 beside D.61–D.66 confirms what the user has just said of the report as a whole — the same construction is emitted once per configuration (and once per source in the evaluation phase), so a reader meets nine or twelve small tables where one table with a configuration column, or one stacked table as the block table already is, would do. That is the renderer's grouping, inherited from the tally's one-table-per-(construction, configuration, source) emission, and it is the subject of the orchestrator's formatting reassessment now and of A83.

**Verdict: merge.** D29 (1) and (3) and D30 executed as ruled; the added cells agree with an independent derivation; zero PROCESS runs.
