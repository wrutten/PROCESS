# A117 (v5-switch-composition-one-commit): gate G5's two sides made at one commit (I-46)

> **Document status** — **OPEN (task report, awaiting the orchestrator's assessment).** Task A117, branch
> `A117-v5-switch-composition-one-commit`, worktree `.claude/worktrees/A117-v5-switch-composition-one-commit`, from trunk
> `4ea0870c`, 2026-10-02. **No harness change, no driver change**: nothing changed under
> `MDA_partitioning_experiment_v5/PROCESS/`, `harness/`, `process/` or V4.
>
> **Commits:**
> - `5447cca3`: `read_back_survey.py`, a read-only survey script at the experiment's top level (not harness). It was
>   committed before any press, and **every press, verdict and record of this task was made at `5447cca3`** on a
>   clean tree.
> - `6b0c7777`: the four tables documents.
> - The tip: this report.
>
> **Press logs:** `runs/<run ID>/_press_logs/A117/` under each of the four run IDs (`pressNN_*.log`, `disk_log.txt`,
> `START_MARKER`, the stamp and read-back surveys as JSON). Start time **2026-10-02T18:44:18+02:00**.

## 1. Verdict

**Fixed by the harness's existing means.** Gate G5 (`switch_composition`) was pressed **without `--resume`**
(`--gate switch_composition`) under each run ID, which re-made both sides at `5447cca3`. A101 used the same remedy
for the same class at DR12. After that, every gate was re-pressed with `--resume`.

G5 now reads **PASS, 0 of 159, 4/4 teeth** under all four run IDs. In each, 43 switch names and 10 run values per
configuration are compared over 3 configurations, and the verdict reads 6 records, all at `5447cca3`.

**No gate condition was changed and no exclusion was added.**

**Resume is not the place to fix this** (§3). A resume rule that refuses a record whose read-back set is not today's
would re-make all 553 campaign records under every run ID, every archived straddle side and every G1 capture. A
narrower recurrence guard inside G5 is proposed in §3.3, not made.

## 2. The entanglement, before anything was touched (measured)

These sources were run per run ID at `5447cca3`, before any press (`press01_*`):
- `--jobs switch_composition`;
- `--jobs all`, which lists every job that more than one gate reads;
- `--archive-collisions`;
- `read_back_survey.py --digests <G5's six>` (`press03`).

| run ID | G5 matrix-composed records (digest, commit) | G5 switch-by-switch records | other gates declaring these jobs (`--jobs all`) | in a read-only or gate archive (`--archive-collisions`) | campaign or traced record? |
|---|---|---|---|---|---|
| `census_tau1e-08` | `159053e9…`, `be6b106f…`, `51de14f1…`, all at `d8873d49`, 32 read-back keys | `8814b381…`, `04a7bc9f…`, `2c78dcf7…` at `b484d807`, 33 keys | **none**: the six digests are not in the 593 shared jobs | **no**: G5 appears under no archive's colliding jobs | no (run kind `gate`, in `gates/_runs/`) |
| `census_tau1e-06` | `aa0440b7…`, `814e0a09…`, `383ce31e…` at `448d6bde`, 32 keys | `74087885…`, `312ce174…`, `676e2fd3…` at `b484d807`, 33 keys | none | no | no |
| `write_set_tau1e-06` | `bcac7183…`, `d6647062…`, `9723df34…` at `52ea57be`, 32 keys | `2758342e…`, `f667e18c…`, `dd36162f…` at `b484d807`, 33 keys | none | no | no |
| `write_set_tau1e-08` | `03feac45…`, `8cad1079…`, `908c428d…` at `b44c88c4`, 32 keys | `552a951b…`, `1a55872b…`, `1c9a4614…` at `b484d807`, 33 keys | none | no | no |

**What else touches these records** (read from the code; inferred, not pressed separately):
- **Not the B2 seed-0 jobs of G9 and `written_file_gap`.** Those carry `delta=0.1` in their identity, so they are other
  jobs with other digests and directories.
- **Not GR's B2 records.** These are `audit=after_run/asked_by=reproduction` and live in GR's read-only archive.
- **G7 (`record_completeness`) and `resume_identity` only compose G5's jobs as identities**, in pair checks ("must
  differ") and in a collision tooth. Neither reads the records.
- **Three gates and stages survey the pool without reading a value of these records:**
  - `resume_identity` surveys every pool directory.
  - `run_kind_separation` reads every record's run kind.
  - The tallies' `records_outside_every_source` is a count.
- **The tallies' provenance (`runs_provenance`) names campaign records only.** The tally stage records therefore do not
  go stale when a pool record is re-made, and they were not re-pressed.
- **`gate_table` reads G5's verdict.**

**What would go stale:** G5's verdict, and the verdicts of the gates that survey the pool, through their "runs read"
lines. No verdict was the input of another verdict that read these records' values.

**No re-make could reach a gate archive, a campaign record or a traced record**, so I did not stop.

## 3. Why `--resume` kept the stale matrix-composed record

### 3.1 From the code

`pool.run` keeps a record exactly when `pool.why_not_kept` returns None (`harness/core/pool.py:1186–1214`). That is
two comparisons:

1. **`records.why_not_complete_for`** (`core/records.py:1467`). It checks:
   - the status, or completeness as a crash;
   - the readable identity against the child's stamps;
   - every child-stamped identity field;
   - the stamped `job_identity` field by field;
   - that `job_digest` equals the job's and re-derives;
   - the completeness contract, which asks whether each declared field is **present**.

   `resolved_switches` is declared `always` (`records.py:467`) and is present, but **its key set is never compared**.
2. **`pool.why_not_composed_as_today`** (`pool.py:1138`). It compares the switch **terms** the arm composes today with
   the record's `switches_asked`, by name.

**What DR13 changed.** It added the switch `block_trace_census_sets` (`experiment/switches.py:519`) with the
read-back `module_solve.BLOCK_TRACE_CENSUS_PATH`. That switch is an instrument that is cleared and **never composed**
by any arm (README §3).

**So the matrix-composed B2 job kept everything resume compares.** Its terms were unchanged (12 / 12 / 11 under
census, 11 / 11 / 10 under the write set, equal in record and job), and so were its identity and digest.

**The switch-by-switch job is different.** Its `override_env` names **every** switch (`gate_composition.py:225–251,
297`), so the new name entered its identity and gave it a new digest with no record.

**Each side's read-back block is built by the child from the harness registry at the time of the run**
(`child/child.py:162`, `switches.default_readbacks()`). So the two blocks differ by the one key, and G5 compares the
blocks whole (`gate_composition.py:186, 366–371`).

**The harness has no means today to see that a kept record pre-dates a driver change that added a read-back** not
composed by the arm.

**This is the second instance of the class.** A101 met it at DR12 (its report §8.4: the switch-by-switch job gained
two switch names, the matrix side was kept from `bf395541`, and G5 FAILed on `resolved_switches` alone). The remedy
there was the same no-resume G5 press used here.

**Why it did not recur at the switches added since.** Those switches were *composed* terms (timers, the test set), so
`why_not_composed_as_today` re-made the matrix side as well (inferred from the code and the key histories below).

### 3.2 Why a resume rule on the read-back set is not the honest fix (measured, `read_back_survey.py` at `5447cca3`, `press03`)

Today's registry names **33** read-back keys. The records carrying another key set, before any press:

| run ID | all records | another key set | of which campaign | traced runs | shared pool | G1's captures (`gates/switch_neutrality`) | GR archive | warm-up archive |
|---|---|---|---|---|---|---|---|---|
| `census_tau1e-08` | 1 295 | **1 206** | **553 of 553** | 0 of 54 | 343 of 369 | 66 of 72 | 28 of 28 | 22 of 22 |
| `census_tau1e-06` | 867 | **784** | **553 of 553** | 0 of 54 | 119 of 145 | 60 of 60 | 28 | 22 |
| `write_set_tau1e-06` | 882 | **799** | **553 of 553** | 0 of 54 | 116 of 142 | 60 of 60 | 28 | 33 |
| `write_set_tau1e-08` | 851 | **768** | **553 of 553** | 0 of 54 | 103 of 129 | 60 of 60 | 28 | 22 |

**The keys those records lack** are `BLOCK_TRACE_CENSUS_PATH` (every one of them). Some, made before DR11 or DR12, also
lack the `TEST_SET`, `TIMERS` or `DEFER_PER_RUN_EXECUTION` keys, or carry the retired `PREDICATE_MODE`.

**What such a rule in `pool.why_not_kept` would do:**
- It would make `--jobs campaign --resume` re-make all 553 campaign records under every run ID.
- It would make every resumed gate press re-make the named before and after sides of GC's and G1's straddles, which
  are made at earlier commits by construction. That would destroy the straddles.
- It would make every press reaching GR's archive raise `PoolError` (`refuse_a_read_only_archive`).

**This contradicts harness plan amendment 15 (gate records are reused across count-neutral changes).** GC's
DR12 → DR13 straddle has already proved DR13 count-neutral (PASS, 0 of 50 114 under every run ID). The key-set
difference is a property of the harness at each record's commit, not a sign that the record is stale.

**So I propose no change to resume.** The existing means is `--gate switch_composition` **without** `--resume`, which
makes both sides in one invocation at one commit.

### 3.3 A narrower recurrence guard, proposed and not made

The defect is G5's alone: it is the one gate whose two sides are composed so that a registry change moves one
identity and not the other. A guard belongs in G5's own press, not in resume.

**The proposal: keep a pair under `--resume` only when both its records are kept, and otherwise re-make both.** In
`harness/gates/gate_composition.py`, `switch_composition_body`, replace the one line
`pool_mod.run_all([job for *_r, job in jobs], campaign, resume=resume)` (line 355) by:

```python
    # Both sides of a pair at one commit (issue I-46; A101 met the same at DR12):
    # under --resume a configuration's pair is kept only where the pool would keep
    # both records; where it would make one side, both sides are made.
    pair_jobs = [job for *_r, job in jobs]
    if resume:
        why = {row["job_digest"]: row["why_not_complete"]
               for row in pool_mod.job_listing(pair_jobs, campaign)}
        by_config: dict[str, list[pool_mod.Job]] = {}
        for name, _label, job in jobs:
            by_config.setdefault(name, []).append(job)
        whole = [j for js in by_config.values()
                 if all(why[pool_mod.digest_for(j2, campaign)] is None for j2 in js) for j in js]
        pool_mod.run_all(whole, campaign, resume=True)
        pool_mod.run_all([j for j in pair_jobs if j not in whole], campaign, resume=False)
    else:
        pool_mod.run_all(pair_jobs, campaign, resume=False)
```

**It should come with one tooth.** On a scratch pair where one side has no record, the decision must re-make both;
on a pair where both are kept, it must keep both.

**It changes no condition, no compared value and no identity.** It changes which records G5's own press keeps. It is
not tested here, so it is the orchestrator's (or the user's) to take.

The alternative, a G5 check that both sides were made at one commit, would be a gate-condition change and is outside
this brief.

## 4. Both sides at one commit, and G5's verdict (measured; `press04_gate_switch_composition_no_resume.log`)

| run ID | runs made | G5 verdict | compared / mismatched | teeth | runs read |
|---|---|---|---|---|---|
| `census_tau1e-08` | 6 (3 matrix-composed, 3 switch-by-switch) | **PASS** | 0 / 159 | 4/4 | 6 at `5447cca3` |
| `census_tau1e-06` | 6 | **PASS** | 0 / 159 | 4/4 | 6 at `5447cca3` |
| `write_set_tau1e-06` | 6 | **PASS** | 0 / 159 | 4/4 | 6 at `5447cca3` |
| `write_set_tau1e-08` | 6 | **PASS** | 0 / 159 | 4/4 | 6 at `5447cca3` |

Afterwards all six G5 records under every run ID carry today's 33-key read-back set (`press17_read_back_survey_end`).

**The re-make went through `pool.run`.** The pool checked same job (`assert_not_another_jobs_record`), then removed
the directory and re-ran it. No directory was removed by hand.

## 5. The archive check before each press (measured)

**`--archive-collisions`** was run before the G5 press (`press01`) and again before the resumed presses (`press05`),
with the same result each time.

**Under `write_set_tau1e-06`, nine jobs resolve into GC's archived entry references (I-42):**
- G6 (`entry_and_warm`), G2 (`prime_map`) and GT (`test_set`), three each, on `A/A0/<configuration>/seed000/unperturbed/gate`.
- All are **KEPT** by `--jobs entry_and_warm`, `--jobs prime_map` and `--jobs test_set` (19/19, 15/15 and 11 kept; GT
  refuses before running there).

**Under the other three run IDs, 0 jobs resolve into GC's archive.**

**GR's archive:**
- 26 reader jobs (`tally_contracts` 20, G9 6) resolve into it under every run ID.
- These are listed "RUN — declared field(s) missing", but they are reads: G9 makes only its own 11 runs, and
  `tally_contracts` makes none.
- `pool.refuse_a_read_only_archive` fired in no press (no refusal in any log).

**`--jobs <gate>` per run-making gate (`press05_jobs_*`).** `--resume` would keep every job of:
- `count_neutrality` (25);
- `prime_map` (15);
- `entry_and_warm` (19);
- `switch_composition` (6, after the G5 press);
- `written_file_gap` (12);
- `record_completeness` (3);
- G9's own 11;
- GT's 27 under census (GT's 16 unrecorded write-set jobs are never run: GT refuses there by design).

**No press would re-make a record in any archive.**

## 6. The gate tables at `5447cca3` (measured, `--measure gate_table --resume`, `press15`)

**Presses:**
- `--gate all --resume` (`press06`) under each run ID.
- Under `census_tau1e-08` the press ran all 29 gates. Under `census_tau1e-06` it stopped at GT's FAIL, and under the
  write-set run IDs at GT's refusal.
- The eight gates after GT were then pressed one by one with `--resume` under those three (`press07`–`press14`): G5,
  G1, GR, G9, `written_file_gap`, `tally_contracts`, `run_kind_separation`, `stage_provenance`.

**Every verdict in all four tables is stamped `5447cca3`.**

| gate | plan | `census_tau1e-08` | `census_tau1e-06` | `write_set_tau1e-06` | `write_set_tau1e-08` |
|---|---|---|---|---|---|
| `g0prime` | G0 | PASS 1/77, 4/4 | same | same | same |
| `copy_identity` … `artifacts_per_run` (13 harness and artifact gates) | — | PASS each | same | same | same |
| `resume_identity` | — | PASS 0/1 342, 15/15 | PASS 0/914 | PASS 0/929 | PASS 0/898 |
| `evaluation_warmup` | — | PASS (read once) 0/19 876, 5/5 | same | same | same |
| `record_completeness` | G7 | PASS | same | same | same |
| `count_neutrality` | GC | PASS 0/50 114, 5/5 | same | same | same |
| `prime_map` | G2 | PASS | same | same | same |
| `entry_and_warm` | G6 | PASS 0/6 717, 3/3 | same | same | same |
| `test_set` | GT | PASS 794/13 424 (its drops), 4/4 | **FAIL** 0/13 424, 3/4 (I-44) | NOT RUN (refused, by design) | NOT RUN (refused, by design) |
| **`switch_composition`** | **G5** | **PASS 0/159, 4/4** | **PASS 0/159, 4/4** | **PASS 0/159, 4/4** | **PASS 0/159, 4/4** |
| `switch_neutrality` | G1 | PASS 0/55 930, 10/10 | PASS 0/54 973 | PASS 0/54 967 | PASS 0/54 973 |
| `reproduction` | GR | PASS (read once) 0/256, 8/8 | same | same | same |
| `output_path` | G9 | PASS 0/3 879, 5/5 | same | same | same |
| `written_file_gap`, `tally_contracts`, `stage_provenance` | — | PASS | same | same | same |
| `run_kind_separation` | — | PASS 0/2 401, 7/7 | PASS 0/1 973 | PASS 0/1 988 | PASS 0/1 957 |
| **totals** | | **29 PASS**; 184/184 teeth | **28 PASS, 1 FAIL**; 183/184 | **28 PASS, 1 not run**; 180/184 | **28 PASS, 1 not run**; 180/184 |

**The only rows not PASS are the two the brief named.**
- **GT refuses under the two write-set run IDs by design.**
- **GT FAILs under `census_tau1e-06` (I-44, unchanged from A114 and A116).** The verdict reads: "8 binding drop(s): 0
  bite, 8 not individually binding; 8 control(s), 8 bit-identical". The tooth "a biting drop's exit state replaced"
  has nothing to doctor.

**The default run ID's `gate_table` stamp line reads `[0353c524, 5447cca3]`.** The `0353c524` file is
`gates/audit_restriction/gate.json`, the retired G4's verdict, which the stage's file pattern still reads. It is the
same as at A116.

## 7. Kept and re-made (measured; `run_stamp_survey.py --against stamp_survey_start.json`, `press16`)

| run ID | records | commit changed | gone | new | which |
|---|---|---|---|---|---|
| `census_tau1e-08` | 1 295 | **7** | 0 | 0 | G5's 3 matrix-composed (`d8873d49` → `5447cca3`) and 3 switch-by-switch (`b484d807` → `5447cca3`); G7's tooth smoke run `A_AR_st_regression_seed000_smoke_f5b7e5e3…` (by design on every press) |
| `census_tau1e-06` | 867 | **7** | 0 | 0 | G5's 3 (`448d6bde` →) + 3 (`b484d807` →); G7's tooth run |
| `write_set_tau1e-06` | 882 | **7** | 0 | 0 | G5's 3 (`52ea57be` →) + 3 (`b484d807` →); G7's tooth run |
| `write_set_tau1e-08` | 851 | **7** | 0 | 0 | G5's 3 (`b44c88c4` →) + 3 (`b484d807` →); G7's tooth run |

**Every other run record was kept at its earlier commit.** That includes:
- G1's captures, GC's both sides and GC's references;
- G2, G6 and GT;
- G9's own runs;
- the archives.

Each resumed verdict's "runs read" line says so.

## 8. The four tables documents (`--paper-tables write`, `press18`; committed `6b0c7777`)

`git diff -U0` shows **only the verification table** moved:

| document | lines out / in | what moved |
|---|---|---|
| `paper_tables.md` | 7 / 7 | the stamp line (`[0353c524, b484d807]` → `[0353c524, 5447cca3]`); G0, G1, G6, G9 and GT re-dated to `5447cca3`; **G5 FAIL 3 of 159 → PASS 0 of 159, 4/4** |
| `paper_tables_census_tau1e-06.md` | 7 / 7 | the stamp line; G0, G1, G6, G9 and GT re-dated (GT still FAIL 0/13 424, 3/4); **G5 FAIL → PASS 0 of 159** |
| `paper_tables_write_set_tau1e-06.md` | 6 / 6 | the stamp line; G0, G1, G6 and G9 re-dated; **G5 FAIL → PASS 0 of 159** |
| `paper_tables_write_set_tau1e-08.md` | 6 / 6 | the stamp line; G0, G1, G6 and G9 re-dated; **G5 FAIL → PASS 0 of 159** |

**No result cell moved.** At `6b0c7777`:
- `--paper-tables check` reads **IDENTICAL** for all four (`press19`).
- `paper_cells_recount.py --runs runs/<run ID> --document <doc>` reads **44 cell rows, 0 mismatched** for all four
  (`press21`).

## 9. The campaigns and traced runs untouched (measured)

**`--jobs campaign --resume`** (`press20`) keeps every campaign job and runs none under each run ID: 3 + 275 + 275 =
**553 of 553**.

**`find … -newermt '2026-10-02T18:44:18+02:00'`** before the traced-run check (`press22_find_before_traced_check.txt`):

| run ID | `campaign/` entries newer | `traced_runs/` entries newer |
|---|---|---|
| `census_tau1e-08` | 0 of 7 933 | 0 of 876 |
| `census_tau1e-06` | 0 of 7 933 | 0 of 873 |
| `write_set_tau1e-06` | 0 of 7 895 | 0 of 874 |
| `write_set_tau1e-08` | 0 of 7 893 | 0 of 873 |

**`--traced-runs check`, run last** (`press23`, both job sets under each run ID):

| job set | equal to campaign record | count leaves differing | coupling-state components differing | traces consistent |
|---|---|---|---|---|
| `sweep_residual` | 48 of 48 | 0 (of 3 585 / 3 570 / 3 600 / 3 618) | 0 of 100 680 | 48 of 48 |
| `sweep_residual_st_more` | 6 of 6 | 0 (of 546 / 537 / 549 / 555) | 0 of 14 886 | 6 of 6 |

**After it, `find` lists exactly the eight `neutrality.json` files** (two per run ID) and nothing else, under
`campaign/` or `traced_runs/`.
- I copied each file to my scratchpad before the check.
- The only differences are `tree_git_head` and the absolute paths in its rows (96 or 12 per file), from A116's
  worktree to this one.

## 10. Disk

| when | `/mnt/c` free |
|---|---|
| 18:44, start | 131 GB |
| before every press (`disk_log.txt` per run ID) | 131 GB |
| end | 131 GB |

## 11. Every decision, and everything unexpected

**Decisions.**
1. **Re-made both sides of G5 by a no-resume `--gate switch_composition`**, the harness's own entry point, rather than
   only the stale side. The harness has no entry point that re-makes one side alone, and making both at one commit
   is what the gate needs. A101 used the same remedy.
   - Reversal: none needed. The prior records are gone, and the new ones are of the same jobs.
2. **No harness change.** A resume rule on the read-back set is rejected on measurement (§3.2). G5's pair-coherence
   guard is proposed (§3.3) and not made, as the brief requires agreement first.
3. **Wrote and committed `read_back_survey.py`** (top level, read-only, outside `harness/`) so that the §3.2 numbers
   come from a committed script, not a shell one-liner (protocol §15). It writes nothing into `runs/`.
   - Reversal: `git rm` it. No gate or stage reads it.
4. **Re-pressed every gate with `--resume`**, not only those that survey the pool, so that the four gate tables are
   all at one commit. The only run this made was G7's by-design tooth run.
5. **Did not re-press the tallies.** Their provenance names campaign records only, and their pool count is
   unchanged (the same 7 records were re-made in place, none added or removed).

**Unexpected.**
1. **I-46 is the second instance of the class.** A101 met it at DR12 (§3.1). The queue and A116's account treat it as
   new.
2. **Every campaign record under all four run IDs carries a read-back set other than today's**, 553 of 553 each. So
   "complete under today's contract" has never meant "made by today's harness". This is by design (amendment 15),
   but it is invisible to the stamp survey.
3. **The traced runs carry today's key set** (54 of 54 per run ID), because they were made at `d1e94dc8`, after DR13.

## 12. What I did not check

- **The proposed G5 guard** (§3.3) was not written or run. Its lines were read against `pool.job_listing` and
  `pool.digest_for`, not executed.
- **Whether the gates that survey the pool would have read anything different** had they not been re-pressed. I
  re-pressed them rather than test it.
- **The entanglement for jobs no gate declares**: G1 declares runs_under, not a job set. A116 composed G1's
  after-capture jobs inline; I relied on G1's resumed "runs read" line (6 records at each run ID's earlier commit) and
  the stamp survey (no G1 record moved).
- **"Untouched"** rests on modification times, the resume decision, the stamp survey and the traced-run comparison.
  It does not rest on per-file hashes of the campaign records.
- **The tallies' stage records** were not re-pressed (decision 5). That the paper documents read IDENTICAL after
  re-rendering is the evidence that they are still consistent.
- **GT under `census_tau1e-06` (I-44)** is reported, not investigated.

**Branch tip:** this report's commit, on `6b0c7777`; the press commit is `5447cca3`.

## Orchestrator's critical assessment (protocol §5) — verdict: merge

*Written 2026-10-02 by the orchestrating session. Checked differently from the agent.*

**Checked.** (1) `git diff --stat 4ea0870c..71c8abcf`: six files — `read_back_survey.py` (new, read-only), the four
tables documents and this report; **no harness, driver-copy, `process/` or V4 line**; worktree clean. (2) `--runs` at
the tip: `census_tau1e-08` 29 PASS of 29; `census_tau1e-06` 28 PASS, 1 FAIL; `write_set_tau1e-06` and
`write_set_tau1e-08` 28 PASS, 0 FAIL, 1 not run. (3) `--paper-tables check` IDENTICAL for the four documents. (4)
**G5's verdict records and the run records behind them, read by the orchestrator**: under each run ID the verdict is
PASS, 0 of 159, teeth tripped, and the six run records it names (`runs_provenance`) are all stamped `5447cca3`, not
dirty, each with 33 read-back keys — both sides are one commit's. (5) No file under the four `campaign/` folders is
newer than the dispatch; under `traced_runs/` only the two `neutrality.json` per run ID that the check stage rewrites.
(6) Nothing was writing into the records tree when the hand-back was read (the last write 19:03:33).

**The remedy is the right one, and is not a retry until it passes.** G5's claim is about two compositions of one arm
at one commit; a press without `--resume` makes exactly that comparison, with the same settings, and the gate's
condition and compared values are unchanged. The agent's entanglement table shows no other gate reads the six records'
values, no archive holds them, and the stamp survey shows exactly seven records re-made per run ID (G5's six and the
one G7's tooth re-makes on every press).

**On resume.** The agent's survey settles the question the brief asked: a resume rule on the read-back key set would
re-make all 553 campaign records under every run ID (their sets pre-date today's registry by design: gate and campaign
records are reused across count-neutral driver changes) and break the archives. No such rule is made. **The agent's
proposed guard inside G5's own press** (keep a configuration's pair under `--resume` only when both records would be
kept; otherwise re-make both) is the narrow fix for a defect that has now occurred twice (DR12 in A101, DR13 here). It
was not made and not run; it is put to the user (issue I-47).

**State after this task.** The only rows not PASS in the four gate tables are gate `test_set`: its refusal by design
under the two write-set run IDs, and its FAIL under `census_tau1e-06` (I-44, the user's). `paper_tables.md` and
`paper_tables_write_set_tau1e-06.md` are back to a verification table with no FAIL.

**Limits carried.** "Untouched" rests on modification times, resume decisions, the stamp survey and the traced-run
check, not per-file hashes. The tallies were not re-pressed (their provenance names campaign records only).
