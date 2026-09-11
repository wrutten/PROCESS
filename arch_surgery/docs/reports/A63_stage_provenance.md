# A63 (stage-provenance) — what a stage read, and which tree took a census

> **Document status** — **OPEN**. Task **A63 (stage-provenance)**, branch `A63-stage-provenance`,
> off `architecture_surgery` at `29904573`. Code at `1f281529`; the experiment plan's §4 re-rendered
> at `8cfbc153`. Scope is issue **I-22** plus the coordinator's two mid-task rulings.
> `EXECUTION_APPROVED` is `False`. Nothing under
> `arch_surgery/MDA_partitioning_experiment_v4/PROCESS/` or the repository-root `process/` was
> touched; the only edit to `EXPERIMENT_PLAN.md` is §4, written by `--plan-tables write` from the
> records.
>
> **Three PROCESS runs were made**, all after the coordinator's ruling and all of them evaluation
> censuses: the re-take of §4.3. Every other stage in this report is zero-run.

---

## 1. Verdict

Both halves of **I-22** are closed, each with a refusal and a tooth, and each demonstrated on this
tree's own records as well as on a fixture.

| | what it now does | shown by |
|---|---|---|
| **(a)** | the `gate_table` stage record carries `records_read` — path, sha256, commit, time and verdict for every verdict record it read, with the glob pattern beside the matches — and `--plan-tables` **refuses** when any of them has been re-made, removed or added to since, naming the gate, both commits and both times | gate `stage_provenance`, 5/5 teeth; and a live refusal on the real records (§4.2) |
| **(b)** | a census record stamps `tree_git_head` and the other thirteen fields the run records stamp (`record_format` `census-2`); an unstamped one is **not kept by `--resume`** — it is re-taken, as `pool.run` re-runs an incomplete run record — and is **refused by name** by every reader that cannot re-take it | the re-take of three censuses (§4.3); gate `artifacts_census`, 5/5 teeth |

**Every stage re-run after the rulings, at `1f281529` (plan at `8cfbc153`):**

| stage | result |
|---|---|
| `--gate artifacts_census --resume --census-entry evaluation`, from the repository root | **PASS** — 81 compared, 0 mismatched, **5/5 teeth**; three censuses re-taken, `census-1` → `census-2` |
| `--gate artifacts_check --resume` | **PASS** — 93 compared, 0 mismatched, 3/3 teeth |
| `--gate stage_provenance --resume` | **PASS** — 17 compared, 0 mismatched, **5/5 teeth** |
| `--artifacts teeth` | **14/14 teeth tripped** (three of them this task's) |
| `--selfcheck`, this tree | **PASS**, 7 of 7 checks |
| `--selfcheck`, a tree with no `runs/` at all | **PASS**, 7 of 7 — it was **FAIL (stage provenance)** before the fix of §3.5 |
| `--measure gate_table --resume` | 25 registered gates: **25 PASS, 0 FAIL, 0 not run; 147 of 147 teeth tripped** |
| `--plan-tables write` | 1 762 lines replacing 1 762; **5 lines changed, every one inside §4.1** |
| `--plan-tables check` (after) | **IDENTICAL** — 1 762 of 1 762 lines, 0 hunks, exit 0 |
| `--gates` | 25 gates, 9 measurement stages |

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
one tuple. Putting the survey there also keeps it beside `survey_heads`, which answers the same
question one level down (*which commit were the runs made at*), so a reader finds both kinds of
provenance in one file. `plan_tables.assert_stage_read_what_is_there` is a five-line adapter that
translates the framework's refusal into the renderer's own error type.

**What is deliberately *not* routed through it.** The tally stages and `recomputed_tables` read
**run** records, and their provenance is `runs_provenance` — commits and count, compared by
`analysis.py` against its own survey. That comparison is about a *population*; `records_read` is
about *files*. Declaring both for one stage would be two mechanisms answering one question.

The stamped block is named `records_read`, not `verdicts_read` as the brief wrote it: the mechanism
is not about verdicts, and a name that says "verdict" on a block that will also hold stage records
would have to be renamed on first reuse. Its contents are as the brief asked, per record: path,
digest, `generated`, `tree_git_head`, verdict.

### 3.2 The refusal in `--plan-tables`, and a check mode

`Section.records_read_required` is `True` for §4.1 only. `render()` asserts before it renders; the
agreeing sentence is printed as `freshness :`. A stage record written *before* this contract (no
block at all) is refused too — otherwise the silent path would simply move.

`--plan-tables` gained **`check`** beside `show` and `write`: it renders, compares with the section
the document carries, prints the differences and **writes nothing**, exiting 3 when they differ.

The comparison is a **diff**, not a line-for-line comparison against position. The first
implementation was positional and reported *1 724 of 1 762 lines differing* for what was one
inserted table row — a count over a population no reader would recognise, which is trap T11's shape.
With `difflib` the same state read **1 758 identical, 4 hunks**.

**One defect found in passing.** `plan_tables.population_marker` surveyed `campaign.runs_dir/gates`
while the tables were rendered from `records_dir` — the same directory in every ordinary press, and
different whenever `--outdir` redirects the records: a population marker describing one set of runs
above tables computed from another. It now surveys the directory it renders from.

### 3.3 Census records carry the tree's commit

`census.tree_stamp` flattens onto the record the fourteen fields `records.SCHEMA`'s *where it ran*
group declares for a run record — `tree`, `tree_git_head`, `tree_git_branch`, `tree_git_describe`,
the two dirt counts, `tree_git_dirty`, `tree_contains_base_commit`, `base_commit`, `process_file`,
`process_copy_provenance`, `python`, `python_version`, `pythonpath` — and keeps the nested
`provenance` block beside them so a reader comparing an old record with a new one finds the same
block in both. `record_format` moves `census-1` → `census-2`; the bump is the convention here
(`records.FORMAT` is `run-record-1`, `reference.FORMAT` is `reproduction-reference-1`).

`tree_stamp` is a function rather than four lines inside the child so that the self-check can run
**that code** and report whether a census taken now would be complete; a restatement beside it would
pass while the child stamped nothing.

### 3.4 The fork, as the coordinator ruled it

I had made an unstamped census a **refusal on every path**, including `--resume`, and put the
alternative to the coordinator. **The ruling: follow harness plan amendment 17's standing property
(a).** A record incomplete under the current contract is re-taken, exactly as `pool.run` re-runs an
incomplete run record; the refusal stays for every reader that cannot re-take the measurement.
Implemented as `census.resume_keeps(directory, configuration=…, entry=…, read_census=…) →
(keep, why)`:

* it is **what `--resume` consults and the only thing it consults** — the census and the record
  beside it, never a directory's existence (trap T13);
* an unstamped record is not kept, and the reason names the format and the missing fields;
* before the pool clears the directory, the superseded record is **read out and named** — its
  format and its commit — into the stage record (`run.superseded`) and onto the terminal, so what
  it said is not lost with it;
* `assert_stamped` is unchanged and still refuses, after a fresh run and for every other reader.

The decision is a pure function of two files, so the tooth for it starts no PROCESS run: it builds
both cases in a scratch directory.

### 3.5 The self-check writes its own fixture (the coordinator's second finding)

On a tree with no `runs/` directory at all — a fresh worktree, or a trial merge of this branch onto
trunk, which is what every new task worktree looks like before its first press — `--selfcheck`
reported **FAIL (stage provenance)** while the other six checks passed, because the check read the
tree's real records and there were none. A self-check may not depend on a press having happened
(A52's rule: the self-checks build their own scratch fixtures).

`selfcheck._scratch_records` now **synthesises** the fixture instead of copying the live records:
three verdict records and the four stage records §4 is rendered from, each with the least content
the renderer accepts, so the four breaks still run through `plan_tables.render` itself rather than
through a function beside it. A fifth tooth writes a scratch census record and shows the reader
refusing it and `--resume` declining to keep it unstamped, and both accepting it once stamped. The
live records are still read — their freshness and their stamps are **noted** — and a tree holding
none says so in one sentence.

This also removed a second-order defect I had introduced: the earlier version copied the live
records, so a gate run after the last `--measure gate_table` made the unmodified copy legitimately
stale and the check failed for a reason unrelated to what it binds. With a synthesised fixture the
check binds the mechanism and nothing else, on every tree.

Reproduced before and after, in a throwaway detached worktree of this branch's own tip
(`git worktree add --detach`, removed with `git worktree remove --force` when done; it held no
artifacts):

| tree | before the fix (`47be2b0d`) | after (`1f281529`) |
|---|---|---|
| no `runs/` directory at all | 6 PASS, **FAIL (stage provenance)** — *"there is no gate_table stage record to check"* | **7 PASS**; stage provenance 10 compared, 0 mismatched, **5/5 teeth**, noting *"this tree holds no verdict record, no stage record and no census record"* |
| this worktree, seeded | 7 PASS | 7 PASS |

### 3.6 A seventh self-check, `stage_provenance`

Promoted to a gate by the existing machinery (`--gate stage_provenance`, `--selfcheck`, `--gates`),
five declared teeth. Nothing on disk is written; no PROCESS run.

---

## 4. The numbers, with their denominators

### 4.1 Gate `stage_provenance` — PASS, 17 compared, 0 mismatched, 5/5 teeth

*Caption: the population, at `1f281529` in this worktree. "Compared" sums six kinds and names each;
a record is one file. Nothing here starts PROCESS.*

| what | how many |
|---|---|
| verdict records, written by the check into its scratch directory | 3 |
| stage records, likewise | 4 |
| a scratch census record, read unstamped and stamped | 2 |
| the live `gate_table` record's freshness, read | 1 |
| the census stamping path, run | 1 |
| live census records, surveyed and named | 6 |
| **total compared** | **17** |

On a tree with no records the same check compares **10** — the first three rows plus the stamping
path — and passes.

| tooth | what it breaks | result |
|---|---|---|
| a verdict re-made at a later commit after the stage record was written | one scratch verdict moved to commit `eeee…` at `2099-01-01` | **TRIPPED** — refused, naming the gate, both commits and both times; the unmodified fixture rendered |
| a verdict record written after the stage record | a `gate.json` no stage ever read, added | **TRIPPED** — refused ("written after the stage record"); only the declared *pattern* can find this one, which is why the block carries the pattern and not just its matches |
| a verdict record the stage read and that is gone | one verdict deleted | **TRIPPED** — refused ("read by the stage and no longer on disk") |
| a stage record that does not say what it read | the `records_read` block removed | **TRIPPED** — refused, with the instruction to re-run `--measure gate_table` |
| a scratch census record with no tree stamp | a census record written without the stamp, then with it | **TRIPPED** — the reader refused it and `--resume` did not keep it (so it is re-taken); stamped, the reader accepted it and `--resume` kept it |

The refusal, as the button prints it:

> `the gate_table stage record does not describe the records on disk: 1 disagreement(s) against the
> 3 record(s) it read.` / `a_first_gate: at a different commit from the one the stage read and newer
> than the one the stage read — the stage read 00000000 generated 2026-09-11T19:07:02, disk has
> eeeeeeee generated 2099-01-01T00:00:00`

### 4.2 The same refusal on the real records, not a fixture

Between `--gate stage_provenance` and the next `--measure gate_table`, the gate's own verdict is
newer than the stage record that summarises it. `--plan-tables check` then refuses, exit 3:

> `REFUSED — the gate_table stage record does not describe the records on disk: 1 disagreement(s)
> against the 29 record(s) it read.` / `stage_provenance: newer than the one the stage read — the
> stage read 29904573 generated 2026-09-11T18:45:19, disk has 29904573 generated
> 2026-09-11T18:48:17`

This is amendment 19's rule (ix) made mechanical: the order is `--gate …`, then `--measure
gate_table`, then `--plan-tables`; pressed the other way round the renderer stops instead of
publishing the older table. After `--measure gate_table --resume` the same command reports
`freshness : … every one of them is byte-identical to what is on disk now`, which is the state this
report closes in.

### 4.3 The census re-take — the only PROCESS runs of this task

`--gate artifacts_census --resume --census-entry evaluation`, pressed once from the repository root:
**PASS**, 81 compared, 0 mismatched, 5/5 teeth. Each of the three configurations printed

> `RE-TAKEN — the record beside it is 'census-1' and carries 13 of 14 declared provenance field(s):
> … A record incomplete under the current contract is re-taken, not kept — the stamp is what a
> survey places the record by (trap T13)`

*Caption: one row per census record under `runs/census/`, before and after the press. "Entry" is
what the census was taken over: the evaluation entry is one design point and seconds long, the
optimisation entry is a full optimisation. Wall clock is progress information, not a measurement
(I-10).*

| record | before | after | wall clock |
|---|---|---|---|
| `large_tokamak_nof/evaluation` | census-1, no top-level stamp | **census-2 at `47be2b0d`**, branch `A63-stage-provenance`, not dirty | 45.9 s (first run; numba JIT dominates it) |
| `low_aspect_ratio_DEMO/evaluation` | census-1 | **census-2 at `47be2b0d`** | 5.0 s |
| `st_regression/evaluation` | census-1 | **census-2 at `47be2b0d`** | 5.4 s |
| `large_tokamak_nof/optimisation` | census-1 | **census-1, unchanged** | — |
| `low_aspect_ratio_DEMO/optimisation` | census-1 | **census-1, unchanged** | — |
| `st_regression/optimisation` | census-1 | **census-1, unchanged** | — |

**Three of six are stamped.** The three optimisation-entry records were not touched, because the
press asked for the evaluation entry; they are re-taken the first time a stage asks for that entry
(`--census-entry optimisation`, one full optimisation each). Gate `stage_provenance` names all six
every time it runs — *"3 carry the tree stamp …; 3 do not"* — so the remainder is visible rather
than assumed.

### 4.4 `--plan-tables write`: §4 re-rendered from the records

1 762 lines replacing 1 762, of which **five changed, every one inside §4.1**; `--plan-tables check`
afterwards reports **1 762 of 1 762 identical, 0 hunks**, exit 0.

*Caption: one row per changed line of `EXPERIMENT_PLAN.md` §4. No cell was typed by hand; the
section is the `gate_table` stage record's output.*

| line | before | after | why |
|---|---|---|---|
| §4.1 caption | "24 registered gate(s) … 13 of the harness's own checks" | "25 … 14" | this task's new gate |
| `artifacts_check` row | 95 compared | 93 compared | **not this task's doing**: the two `input_file_lifted` rows are PENDING in this worktree because `artifacts_derive_inputs` (a PROCESS-running stage) has never run here. The gate PASSes at 93/93 and names both pending rows |
| `artifacts_census` row | 81 compared, 2/2 teeth | 81 compared, **5/5 teeth** | three more teeth; the denominator is unchanged, the re-taken census comparing against the same committed artifacts |
| new row | — | `stage_provenance` … PASS, 17, 0, 5/5 | this task's new gate |
| summary | 24 PASS, 139 of 139 teeth | **25 PASS, 147 of 147 teeth** | +5 (the new gate) +3 (`artifacts_census`) |

Everything else in §4 — 1 757 lines, the whole of §4.2, §4.3 and §4.4 — is unchanged, which is also
a check on the renderer: the same records rendered at a different commit in a different worktree
reproduce the committed section exactly.

### 4.5 `--artifacts teeth` — 14/14, three of them this task's

*Caption: the four artifact stages' deliberate breaks in one press; no PROCESS run.*

| tooth | evidence |
|---|---|
| a census record carrying no tree stamp | an on-disk `census-1` record (13 of 14 fields missing): **refused**; the same record with the fields present (null counts as carried): **accepted** |
| an unstamped census record offered to `--resume` | a scratch copy of a real census beside an unstamped record: **not kept**, so it is re-taken; beside a stamped record: **kept** |
| a census with no run record beside it | a directory holding no `metrics.json`: **refused** |

The discriminating half matters in each: a check that refuses everything is not a check.

---

## 5. Autonomous decisions, each with its reversal

*Caption: one row per decision taken without asking, what it rests on, and the edit that reverses
it. The fork that was **not** taken autonomously — the resume path — is §3.4, ruled by the
coordinator.*

| # | decision | why | reversal |
|---|---|---|---|
| 1 | the freshness mechanism lives in `framework.py` (declaration, stamp, assertion), not beside the renderer | the brief's own test: it is one mechanism, and the next stage inherits it by declaring one tuple | move the three functions into `plan_tables.py` and drop `Measurement.reads_records`; the call sites are two |
| 2 | the block is `records_read`, not `verdicts_read` | it holds whatever a stage read; naming it for today's only content forces a rename on first reuse | rename the key in `framework.survey_records` and its two readers |
| 3 | the survey is by **glob pattern**, so it includes four legacy verdict records (`copy_identity`, `edit_behaviour`, `frozen_physics`, `smoke_import`) that the registry does not name and that carry no `generated` and no `tree_git_head` | only a re-glob can find a verdict written *after* the stage; over-inclusion refuses too often and loudly, under-inclusion is the silent defect I-22 is about | restrict `gate_table`'s stamp to the rows it rendered — one line in `Measurement.run` — and accept that a new verdict goes unnoticed |
| 4 | the superseded census record is read out and **named** before the pool clears its directory | otherwise a re-take is silent about what it replaced, which is the shape of the defect this task exists to close | drop the `superseded` block in `census.take` |
| 5 | the self-check's fixture is **synthesised**, always, rather than copied when records exist | one code path, so the empty-tree case is the exercised case and not the rare one; and a fixture that changes shape with the tree gives a check whose meaning varies (§3.5) | branch in `_scratch_records`: copy when the live directory has records, synthesise otherwise — two tooth paths, one of them rarely run |
| 6 | the unstamped census records are **named** by the self-check, not failed on | what consumes them refuses, and `--resume` re-takes them; failing here would block a merge for a condition the press resolves | turn the `check.note` into `check.fail` — one line |
| 7 | `--plan-tables check` compares as a **diff** | positional comparison reported 1 724 differences for one inserted row (trap T11) | revert to the positional comparator in `plan_tables.check` |
| 8 | `population_marker` follows `records_dir` | a marker describing one population above tables from another is the failure this module exists to prevent | restore `campaign.runs_dir` |

---

## 6. Limits

* **The refusals are one-directional.** They catch a stage record older than its sources; they do
  not catch a stage record built from records that were themselves wrong, and they say nothing about
  whether a verdict is correct.
* **The digest is decisive, the commit and the time are narrative.** Two verdicts with different
  bytes at the same commit and the same second are refused as "different bytes at the same commit
  and time"; the message cannot say more because there is no more in the records.
* **Three census records are still `census-1`** — the optimisation-entry ones (§4.3). They are
  re-taken by the first press that asks for that entry, which is a full optimisation per
  configuration; until then the survey names them and any reader of them refuses.
* **The re-take was measured at the evaluation entry only.** That an optimisation-entry census
  stamps identically follows from the code path being the same one; it has not been observed.
* **`artifacts_check` reports 93, not A55's 95**, because this worktree has no derived input files —
  a property of the seed, not a regression. The gate names both pending rows.
* **The three timings in §4.3 are context, not evidence** (I-10): one sample each, on a shared
  machine, the first dominated by numba JIT.
* The population of every number above is this worktree's records — 173 run records, 167 under
  `runs/gates` and 6 under `runs/census` — not the campaign, which has not run.

---

## 7. What the harness plan and TRAPS should gain

**The harness plan (Appendix A), at the merge:**

1. *A stage that reads records declares them; the framework stamps them; a consumer refuses when
   they have moved.* `runs_provenance` compares a **population** (commits, count) and `records_read`
   compares **files** (path, digest, commit, time, verdict); a stage uses whichever its sources are,
   never both for one question.
2. *The order is a mechanism, not a convention:* `--gate …`, then `--measure gate_table`, then
   `--plan-tables`. Rule (ix) of amendment 19 is now enforced by a refusal rather than by memory,
   and `--plan-tables check` reports the document's state without editing it.
3. *A census record is a run record for provenance purposes* (`census-2`): it stamps the same
   "where it ran" group, because that is the key a stamp survey reads. Amendment 17's standing
   property (a) extends to it — an unstamped census is incomplete under the contract, so `--resume`
   re-takes it — and the superseded record is named before it is replaced.
4. *A self-check builds its own fixture, always.* A check that reads the tree's real records reports
   the state of a directory, not the health of a mechanism, and fails on every tree that has not
   been pressed — a fresh worktree, a trial merge (§3.5). Corollary: a check that *copies* live
   records inherits the press order and fails for reasons unrelated to what it binds.

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
| `4fb5b57d` | `selfcheck.check_stage_provenance` and its four teeth; the census survey and the stamping-path check; the gate registered in `gates.py` |
| `015908f9` | `harness/README.md`: the self-check table's seventh row, the census record shape, the `--plan-tables` order and check mode |
| `81bd6090` | the self-check re-stamps its scratch baseline and notes the live record's freshness instead of failing on it |
| `cf113470` | the report, first version |
| `47be2b0d` | **the coordinator's ruling on the fork**: `census.resume_keeps` — an unstamped record is not kept by `--resume` but re-taken, the superseded one named; `assert_stamped` unchanged for every other reader; the fifth census tooth |
| `b691c5bf` | **the coordinator's second finding**: `selfcheck._scratch_records` synthesises the fixture, so a tree with no `runs/` no longer fails; a scratch census tooth |
| `1f281529` | the self-check says so when a tree holds no records at all |
| `8cfbc153` | **documents only** — `EXPERIMENT_PLAN.md` §4 re-rendered by `--measure gate_table --resume` then `--plan-tables write`: 5 lines changed, all in §4.1 |
| *(this commit)* | the report brought to the rulings: §3.4, §3.5, §4.3, §4.4, the decisions, the limits and this log |

---

## 9. Orchestrator's critical assessment (protocol §5)

*Written 2026-09-11 at `2fe669ee`, before the merge. Verification by checks that differ from the
agent's; no PROCESS run was made for this review.*

* **Scope.** `git diff --name-only 29904573..2fe669ee`: `framework.py`, `census.py`, `gates.py`,
  `plan_tables.py`, `selfcheck.py`, the runner, the README, the experiment plan (hunks inside §4
  only, as permitted after the census ruling) and this report. Nothing under `…_v4/PROCESS/`, the
  repository-root `process/`, the queue or the harness plan; `EXECUTION_APPROVED` untouched.
* **The check the agent did not make first, and the defect it found.** A trial merge of the
  branch (at `cf113470`) onto trunk `47d934b7`, in a detached worktree with no `runs/` at all —
  the state of every new task worktree — gave `--selfcheck` 6 PASS and **FAIL (stage
  provenance)**: "there is no gate_table stage record to check". A self-check that depends on real
  records existing is the shape A52's rule for self-checks forbids. Reported to the agent, fixed at
  `b691c5bf` by synthesising the fixture always. **Re-checked at `2fe669ee` the same way: 7 of 7
  PASS** on the merged tree with no records.
* **The mechanism, read.** `records_read_disagreements` names three cases separately — written
  after the stage, read and gone, changed bytes with both commits and both times — and
  `assert_records_read_are_current` raises on any. One mechanism in the framework, declared by a
  tuple per stage; the tally stages' `runs_provenance` (a population comparison) is left as the
  other half of one question. Accepted.
* **The ruling on the census fork.** Re-take on the resume path, as amendment 17 (a) says; refusal
  for every reader that cannot re-take. The three optimisation-entry census records stay `census-1`
  until a press asks for `--census-entry optimisation`; the gate names them every run.
* **The merge.** Clean; the merged harness compiles.

**Decisions accepted** as the agent states them, including synthesise-always for the self-check
(one tooth path; it also removed the press-order dependence of the first version) and the
`population_marker` fix (the marker follows `records_dir`).

**Verdict: approved for merge at `2fe669ee`.** I-22 closed. Records to be relocated by the retire
script; the path is written in the queue row after it prints.
