# A63 (stage-provenance) — what a stage read, and which tree took a census

> **Document status** — **OPEN**. Task **A63 (stage-provenance)**, branch `A63-stage-provenance`,
> off `architecture_surgery` at `29904573`. Reports at `81bd6090`. Scope is issue **I-22** and
> nothing else: no PROCESS run was made, `EXECUTION_APPROVED` is `False`, and nothing under
> `arch_surgery/MDA_partitioning_experiment_v4/PROCESS/` or the repository-root `process/` was
> touched.

---

## 1. Verdict

Both halves of **I-22** are closed, each with a refusal and a tooth, and each demonstrated on this
tree's own records rather than on an invented one.

| | what it now does | shown by |
|---|---|---|
| **(a)** | the `gate_table` stage record carries `records_read` — path, sha256, commit, time and verdict for every verdict record it read, with the glob pattern beside the matches — and `--plan-tables` **refuses** when any of them has been re-made, removed or added to since, naming the gate, both commits and both times | gate `stage_provenance`, 4/4 teeth; and a live refusal on the real records (§4.2) |
| **(b)** | a census record stamps `tree_git_head` and the other thirteen fields the run records stamp for provenance (`record_format` `census-2`); an unstamped one is **refused by name** by the stage that reads a census, and the self-check names every one on disk | gate `artifacts_census`'s two new teeth, run without a PROCESS run via `--artifacts teeth` (13/13); the survey in gate `stage_provenance` |

**Every zero-run stage re-run, at `81bd6090`:**

| stage | result |
|---|---|
| `--gate stage_provenance --resume` | **PASS** — 46 compared, 0 mismatched, **4/4 teeth** |
| `--gate artifacts_check --resume` | **PASS** — 93 compared, 0 mismatched, 3/3 teeth |
| `--artifacts teeth` | **13/13 teeth tripped**, including the two new census teeth |
| `--selfcheck` | **PASS**, 7 of 7 checks |
| `--measure gate_table --resume` | 25 registered gates: **25 PASS, 0 FAIL, 0 not run; 143 of 143 teeth tripped** |
| `--plan-tables check` | freshness **agrees** (29 verdict records, all byte-identical to disk); the document's §4 against the records: **1 758 lines identical**, 3 only in the document, 4 only from the records, **4 hunks** — exit 3, nothing written |
| `--gates` | 25 gates, 9 measurement stages |

The four hunks are §1's own consequence and are listed with their reasons in §4.3. **The plan was
not edited**: `--plan-tables check` is a new mode that compares and writes nothing.

---

## 2. What I-22 (a) actually is, in one paragraph

The experiment plan's §4.1 is not rendered from the gate verdicts. It is rendered from the
`gate_table` **stage** record, which was built from the verdicts at the moment that stage ran. Run a
gate afterwards and the renderer reproduces the older verdict — same table, same denominator, same
PASS or FAIL — with nothing anywhere saying the file on disk now says something else. A55
(harness-smoke)'s first re-render reproduced a failing G1 row byte for byte for exactly that reason.
A54 (harness-analysis) had already closed this shape one level down, for the tally: a stage record
declares the run population it summarised, and the consumer compares it with its own survey
(`analysis.assert_the_tally_read_these_runs`). What was missing was the same discipline for a stage
whose sources are **files**, not a population.

---

## 3. What changed

### 3.1 One mechanism, in `framework.py` — and why there rather than beside the renderer

The brief asked whether the check belongs in `framework.Measurement` for every stage that reads
verdicts or other stage records, "if it is one mechanism rather than two". **It is one, and it is
there.** Three pieces, all in `harness/framework.py`:

* `Measurement.reads_records` — a tuple of glob patterns relative to the records directory,
  **declared on the stage**. `gate_table` declares `("*/gate.json",)`.
* `Measurement.run` surveys those patterns after the body and stamps `records_read` into the record
  it writes. The body is not asked to cooperate and cannot leave a source out: a body that stamped
  its own sources would have to be *believed* about what it omitted.
* `assert_records_read_are_current(stage_record, root, stage=…)` re-surveys the **patterns** and
  raises `StaleRecordError` (a `GateError`) naming every disagreement; it returns the agreeing
  sentence otherwise, so the agreeing case is stated rather than assumed — the convention `Gate.run`
  already follows for its runs.

Why the framework and not `plan_tables.py`: the declaration, the stamp and the assertion are one
idea, and the next stage that reads verdicts or another stage's record inherits all three by adding
one tuple. Putting the survey in the framework also keeps it beside `survey_heads`, which answers
the same question one level down (*which commit were the runs made at*), so a reader finds both
kinds of provenance in one file. `plan_tables.assert_stage_read_what_is_there` is a five-line
adapter that translates the framework's refusal into the renderer's own error type.

**What is deliberately *not* routed through it.** The tally stages and `recomputed_tables` read
**run** records, and their provenance is `runs_provenance` — commits and count, compared by
`analysis.py` against its own survey. That comparison is about a *population*; `records_read` is
about *files*. Declaring both for one stage would be two mechanisms answering one question, and the
run-record one is already gated. So `reads_records` is declared by exactly one stage today.

The stamped block is named `records_read`, not `verdicts_read` as the brief wrote it: the mechanism
is not about verdicts, and a name that says "verdict" on a block that will also hold stage records
would have to be renamed the first time it is reused (the standing rule: name a thing for what it
does). The block's contents are as the brief asked, per record: path, digest, `generated`,
`tree_git_head`, verdict.

### 3.2 The refusal in `--plan-tables`, and a check mode

`Section.records_read_required` is `True` for §4.1 only. `render()` asserts before it renders; the
agreeing sentence is printed as `freshness :`. A stage record written *before* this contract (no
block at all) is refused too — otherwise the silent path would simply move.

`--plan-tables` gained **`check`** beside `show` and `write`: it renders, compares with the section
the document already carries, prints the differences and **writes nothing**, exiting 3 when they
differ. It exists because this task must report the state of a shared document it may not edit.

The comparison is a **diff**, not a line-for-line comparison against position. The first
implementation was positional and reported *1 724 of 1 762 lines differing* for what is one inserted
table row — a count over a population no reader would recognise, which is trap T11's shape. With
`difflib` the same state reads **1 758 identical, 4 hunks**.

**One defect found and fixed in passing.** `plan_tables.population_marker` surveyed
`campaign.runs_dir/gates` while the tables were rendered from `records_dir`. They are the same
directory in every ordinary press and different whenever `--outdir` redirects the records — a
population marker describing one set of runs above tables computed from another. It now surveys the
directory it renders from.

### 3.3 Census records carry the tree's commit

`census.tree_stamp` flattens onto the record the fourteen fields `records.SCHEMA`'s *where it ran*
group declares for a run record — `tree`, `tree_git_head`, `tree_git_branch`, `tree_git_describe`,
the two dirt counts, `tree_git_dirty`, `tree_contains_base_commit`, `base_commit`, `process_file`,
`process_copy_provenance`, `python`, `python_version`, `pythonpath` — and keeps the nested
`provenance` block beside them so that a reader comparing an old record with a new one finds the
same block in both. `record_format` moves `census-1` → `census-2`; the bump is the convention here
(`records.FORMAT` is `run-record-1`, `reference.FORMAT` is `reproduction-reference-1`).

`census.assert_stamped` refuses a record missing any of them, by name, with its format, the count
missing and the command that re-takes it. It is called in `take()` **on both paths** — after a fresh
run and on the resume path — so the stage that reads a census (gate `artifacts_census`) refuses
rather than comparing a census nothing can place. `run_record()` refuses a census sitting beside no
record at all.

`tree_stamp` is a function rather than four lines inside the child so that the self-check can run
**that code** and report whether a census taken now would be complete; a restatement beside it would
pass while the child stamped nothing.

### 3.4 A seventh self-check, `stage_provenance`

`selfcheck.check_stage_provenance`, promoted to a gate by the existing machinery (`--gate
stage_provenance`, `--selfcheck`, `--gates`). It copies this tree's own verdict and stage records
into a scratch directory — only `gate.json` and `measurements.json`, never the runs — and breaks the
copy four ways, each of which `plan_tables.render` must refuse while the unmodified copy renders.
Nothing on disk is written.

---

## 4. The numbers, with their denominators

### 4.1 Gate `stage_provenance` — PASS, 46 compared, 0 mismatched, 4/4 teeth

*Caption: the population is this tree's records at `81bd6090`. "Compared" sums four kinds and names
each: a record is one file on disk except for the two path checks. Nothing here starts PROCESS.*

| what | how many |
|---|---|
| verdict records copied and surveyed | 29 |
| stage records copied | 9 |
| the live `gate_table` record's freshness, read | 1 |
| the census stamping path, run | 1 |
| census records on disk, surveyed by name | 6 |
| **total compared** | **46** |

| tooth | what it breaks | result |
|---|---|---|
| a verdict re-made at a later commit after the stage record was written | `artifacts_census`'s verdict moved from `f8bce151` at `2026-09-11T17:44:47` to `eeeeeeee` at `2099-01-01T00:00:00` in the scratch copy | **TRIPPED** — refused, naming the gate, both commits and both times; the same records unmodified rendered |
| a verdict record written after the stage record | a `gate.json` no stage ever read, added | **TRIPPED** — refused ("written after the stage record"); only the declared *pattern* can find this one, which is why the block carries the pattern and not just its matches |
| a verdict record the stage read and that is gone | one verdict deleted from the copy | **TRIPPED** — refused ("read by the stage and no longer on disk") |
| a stage record that does not say what it read | the `records_read` block removed from the copy | **TRIPPED** — refused, with the instruction to re-run `--measure gate_table` |

The refusal, as the button prints it (from the first tooth):

> `the gate_table stage record does not describe the records on disk: 1 disagreement(s) against the
> 29 record(s) it read.` / `artifacts_census: at a different commit from the one the stage read and
> newer than the one the stage read — the stage read f8bce151 generated 2026-09-11T17:44:47, disk
> has eeeeeeee generated 2099-01-01T00:00:00`

### 4.2 The same refusal on the real records, not a copy

Between `--gate stage_provenance` and the next `--measure gate_table`, the gate's own verdict is
newer than the stage record that summarises it. `--plan-tables check` then refuses, exit 3:

> `REFUSED — the gate_table stage record does not describe the records on disk: 1 disagreement(s)
> against the 29 record(s) it read.` / `stage_provenance: newer than the one the stage read — the
> stage read 29904573 generated 2026-09-11T18:45:19, disk has 29904573 generated
> 2026-09-11T18:48:17`

This is amendment 19's rule (ix) made mechanical: the order is `--gate …`, then `--measure
gate_table`, then `--plan-tables`; pressed the other way round the renderer stops instead of
publishing the older table. After `--measure gate_table --resume` the same command reports
`freshness : … every one of them is byte-identical to what is on disk now`.

**This is also why the self-check re-stamps its scratch baseline.** The first version inherited the
press order: because the check copies the *real* records, a gate run after the last `--measure`
made the unmodified copy legitimately stale and the check failed for a reason that has nothing to do
with what it binds. The four breaks now measure the mechanism against a baseline re-surveyed inside
the scratch directory, and the live state is **read and noted** — including the refusal the renderer
would print — rather than failed on. (Caught by running `--selfcheck` immediately after `--gate
stage_provenance`; it failed, correctly and for the wrong reason.)

### 4.3 `--plan-tables check`: the document against the records

131 tables, 3 621 cells; 1 761 lines in the document against 1 762 from the records; **1 758
identical**, 3 only in the document, 4 only from the records, in **4 hunks**:

*Caption: one row per hunk of the diff between `EXPERIMENT_PLAN.md` §4 as committed and §4 as these
stage records render it now. Nothing was written.*

| hunk | document | records | why |
|---|---|---|---|
| §4.1 caption, line 13 | "24 registered gate(s) … 13 of the harness's own checks" | "25 … 14" | this task's new gate |
| §4.1 row, line 24 | `artifacts_check` … 95 compared | 93 compared | **not this task's doing**: the two `input_file_lifted` rows are PENDING in this worktree because `artifacts_derive_inputs` (a PROCESS-running stage) has never run here. The gate PASSes at 93/93 and names both pending rows |
| §4.1, line 41 | — | one row, `stage_provenance` … PASS, 46, 0, 4/4 | this task's new gate |
| §4.1 summary, line 42 | 24 PASS, 139 of 139 teeth | 25 PASS, 143 of 143 teeth | this task's new gate and its four teeth |

Every other line of §4 — the whole of §4.2, §4.3, §4.4, 1 758 lines — is identical, which is also a
check on the renderer: the same records rendered at a different commit in a different worktree
reproduce the committed section exactly.

### 4.4 The census records: the "before", named

Gate `stage_provenance` surveys `runs/census/` and reports, without failing:

> `census records: 0 carry the tree stamp (none); 6 do not` — each named with its format, its
> missing count and where its commit can still be read:

*Caption: the six census records as seeded into this worktree, one per configuration and entry.
"Missing" is of the 14 declared provenance fields; `process_file` is the one they carry. The
commit column is `provenance.tree_git_head` — present in the record, but one level below where a
stamp survey looks.*

| record | format | missing | commit, reachable only as `provenance.tree_git_head` |
|---|---|---|---|
| `large_tokamak_nof/evaluation` | census-1 | 13 of 14 | `3d64625c` |
| `large_tokamak_nof/optimisation` | census-1 | 13 of 14 | `3347169c` |
| `low_aspect_ratio_DEMO/evaluation` | census-1 | 13 of 14 | `3d64625c` |
| `low_aspect_ratio_DEMO/optimisation` | census-1 | 13 of 14 | `3347169c` |
| `st_regression/evaluation` | census-1 | 13 of 14 | `3d64625c` |
| `st_regression/optimisation` | census-1 | 13 of 14 | `3347169c` |

They were **not** re-made — that is a PROCESS run, and they are the "before". The same check runs
`census.tree_stamp` itself and reports that a census taken now would carry all 14 fields.

### 4.5 The two new census teeth — `--artifacts teeth`, 13/13

*Caption: the four artifact stages' deliberate breaks in one press; no PROCESS run. The last two
rows are this task's.*

| tooth | evidence |
|---|---|
| a census record carrying no tree stamp | the real record at `runs/census/large_tokamak_nof/evaluation/metrics.json` (`census-1`, 13 of 14 fields missing): **refused**; the same record with the fields present (null counts as carried): **accepted** |
| a census with no run record beside it | a directory holding no `metrics.json`: **refused** |

The discriminating half matters: a check that refuses everything is not a check.

---

## 5. Autonomous decisions, each with its reversal

*Caption: one row per decision taken without asking, what it rests on, and the edit that reverses it.*

| # | decision | why | reversal |
|---|---|---|---|
| 1 | the freshness mechanism lives in `framework.py` (declaration, stamp, assertion), not beside the renderer | the brief's own test: it is one mechanism, and the next stage inherits it by declaring one tuple | move the three functions into `plan_tables.py` and drop `Measurement.reads_records`; the call sites are two |
| 2 | the block is `records_read`, not `verdicts_read` | it holds whatever a stage read; naming it for today's only content would force a rename on first reuse | rename the key in `framework.survey_records` and its two readers |
| 3 | the survey is by **glob pattern**, so it includes four legacy verdict records (`copy_identity`, `edit_behaviour`, `frozen_physics`, `smoke_import`) that the registry does not name and that carry no `generated` and no `tree_git_head` | only a re-glob can find a verdict written *after* the stage; over-inclusion refuses too often and loudly, under-inclusion is the silent defect I-22 is about | restrict `gate_table`'s stamp to the rows it rendered — one line in `Measurement.run` — and accept that a new verdict goes unnoticed |
| 4 | an unstamped census is **refused**, not silently re-taken, on the resume path | the brief asks for a refusal; and a stage asked to *compare* a census should not decide on its own to start a measurement | in `census.take`, replace the `assert_stamped` call on the resume path with `if missing_stamp_fields(...)`: fall through to the run. Then `--gate artifacts_census --resume` re-takes the three censuses (~4 s each) instead of failing. **This is the one thing I would put to the user** — see §7 |
| 5 | the six unstamped census records are **named** by the self-check, not failed on | what consumes them refuses; failing here would block a merge for a condition the brief told me to leave in place | turn the `check.note` into `check.fail` — one line |
| 6 | the self-check re-stamps its scratch baseline and *notes* the live record's freshness | otherwise the check's verdict depends on the press order rather than on the mechanism (§4.2) | drop the re-survey in `_scratch_records`' caller and the check fails whenever a gate was run after `--measure gate_table` |
| 7 | `--plan-tables check` compares as a **diff** | positional comparison reported 1 724 differences for one inserted row (trap T11) | revert to the positional comparator in `plan_tables.check` |
| 8 | `population_marker` follows `records_dir` | a marker describing one population above tables from another is the failure this module exists to prevent | restore `campaign.runs_dir` |

---

## 6. Limits

* **No PROCESS run was made**, so the `census-2` record shape has never been written by an actual
  census. What is measured is that the stamping path (`census.tree_stamp`, the function the child
  calls) produces all 14 declared fields when run against the copy — the code itself, not a
  restatement. The first real census is what proves the child writes them.
* **The refusals are one-directional.** They catch a stage record older than its sources; they do
  not catch a stage record built from records that were *themselves* wrong, and they say nothing
  about whether a verdict is correct.
* **The digest is decisive, the commit and the time are narrative.** Two verdicts with different
  bytes at the same commit and the same second are refused as "different bytes at the same commit
  and time"; the message cannot say more because there is no more in the records.
* **The `artifacts_census` gate could not be run here** — it starts PROCESS. Its two new teeth were
  run through `--artifacts teeth`, which does not. Until a census is re-taken, `--gate
  artifacts_census --resume` **will refuse** on all three configurations, naming the six records.
  That is the intended behaviour of decision 4 and the thing needing a ruling (§7).
* **§4.1's row count and teeth total move with this task** (24 → 25 gates, 139 → 143 teeth). The
  plan's §4 was not re-rendered here; whoever merges presses `--measure gate_table` then
  `--plan-tables write`.
* **`artifacts_check` reports 93, not A55's 95**, because this worktree has no derived input files —
  a property of the seed, not a regression. The gate names both pending rows.
* The population of every number above is this worktree's seeded records (167 run records under
  `runs/gates`, 6 census records), not the campaign, which has not run.

---

## 7. What needs a ruling, and what the plan and TRAPS should gain

**The one fork.** Decision 4: an unstamped census is refused rather than re-taken. The alternative
is the standing property recorded in harness plan amendment 17 (a) — *a record made before a schema
field existed is incomplete under the current contract and is re-run; this is the contract working,
not a defect* — which would make `--gate artifacts_census --resume` re-take the three evaluation
censuses (seconds each) and self-heal. I chose the refusal because the brief asks for one and
because a comparison stage should not start a measurement on its own; the two differ by one line.
**Whoever rules should also decide when the six records are re-taken**, since until then that gate
fails by design.

**The harness plan (Appendix A) should gain, at the merge:**

1. *A stage that reads records declares them; the framework stamps them; a consumer refuses when
   they have moved.* `runs_provenance` compares a **population** (commits, count) and `records_read`
   compares **files** (path, digest, commit, time, verdict); a stage uses whichever its sources are,
   and never both for one question.
2. *The order is a mechanism, not a convention:* `--gate …`, then `--measure gate_table`, then
   `--plan-tables`. Rule (ix) of amendment 19 is now enforced by a refusal rather than by memory,
   and `--plan-tables check` reports the document's state without editing it.
3. *A census record is a run record for provenance purposes* (`census-2`): it stamps the same
   "where it ran" group, because that is the key a stamp survey reads.
4. *A check that copies live records must re-stamp its own baseline*, or its verdict becomes a
   statement about the press order (§4.2).

**TRAPS should gain one entry** — the shape is new and it has already misled once:

> **A record rendered from a record is only as current as the file it was made from.** The plan's
> §4.1 is rendered from the `gate_table` *stage* record, not from the verdicts, so a gate re-run
> afterwards is published as it was — the same table, the same PASS — with nothing to mark it. A55's
> first re-render reproduced a failing row byte for byte after the gate had passed. **How to avoid
> it:** a stage that reads records declares them (`Measurement.reads_records`), the framework stamps
> path, digest, commit, time and verdict, and the consumer refuses; and the glob pattern travels
> with the stamp, because a verdict written *after* the stage can only be found by re-globbing.

A second, smaller note for TRAPS or the plan: **a provenance block one level down is invisible to a
survey**. The six census records always carried their commit — at `provenance.tree_git_head`, which
is not where `survey_heads` looks — so they read as "no stamp" in exactly the survey that catches a
`--resume` which kept what it should have re-made (T13).

---

## 8. Change log

*Caption: append-only; one row per commit on this branch, in order.*

| commit | what |
|---|---|
| `dd6fd80b` | `framework.Measurement.reads_records`, `survey_records`, `describe_record`, `records_read_disagreements`, `assert_records_read_are_current`, `StaleRecordError`; `gate_table` declares `*/gate.json` |
| `c5d604d7` | `plan_tables`: `Section.records_read_required`, the refusal in `render`, `section_span`, `check()` as a diff, the `population_marker` fix; `--plan-tables check` on the runner |
| `b316bff5` | `census`: `RECORD_FORMAT = "census-2"`, `STAMP_FIELDS`, `tree_stamp`, `missing_stamp_fields`, `assert_stamped`, `run_record`, the two calls in `take()`, two new teeth |
| `4fb5b57d` | `selfcheck.check_stage_provenance` and its four teeth; the census survey and the stamping-path check; the gate registered in `gates.py` with its declared teeth |
| `015908f9` | `harness/README.md`: the self-check table's seventh row, the census record shape, the `--plan-tables` order and check mode, the two new teeth rows |
| `81bd6090` | the self-check re-stamps its scratch baseline and notes the live record's freshness instead of failing on it (§4.2) |
