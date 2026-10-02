# A116 (v5-gate-criterion-keys): three gates keyed on the criterion (test set and τ), G1's wall-clock leaf, and the four gate tables

> **Document status** — **OPEN (task report, awaiting the orchestrator's assessment).** Task A116
> (v5-gate-criterion-keys), 2026-10-02, branch `A116-v5-gate-criterion-keys`, worktree
> `.claude/worktrees/A116-v5-gate-criterion-keys`, base `e977c57d`. Harness only: nothing changed under the driver copy
> (`MDA_partitioning_experiment_v5/PROCESS/`), the repository's `process/` or V4. Start time recorded
> `2026-10-02T18:03:38+02:00` (`runs/<run ID>/_press_logs/A116/START_MARKER`).
>
> **Commits.**
> - `2c5e281a`: the three criterion keys (issue I-43), one tooth for each, and the exclusion review's timing block.
> - `9c5ea415`: `audit_snapshot.wall_s` added to G1's exclusion table (issue I-45), and the README.
> - `b484d807`: GC's job listing resolved against the declared campaign too. This was found before any gate press.
> - `12472063`: the four tables documents.
> - The tip: this report.
>
> **Where the records were made.** Every gate verdict and every run record made by this task is at `b484d807`, on a
> clean tree. The one exception is the exclusion-review stage record of `press02`, made at `2c5e281a` and re-pressed at
> `b484d807` (`press17`). Every number below is printed by a committed entry point at the commit named:
> `experiment_runner.py` (gates, `--jobs`, `--archive-collisions`, `--measure`, `--paper-tables`, `--traced-runs`),
> `run_stamp_survey.py` and `paper_cells_recount.py`. Press logs are in `runs/<run ID>/_press_logs/A116/`
> (`pressNN_*.log`, `disk_log.txt`). **Measured** means read from records or logs; **inferred** means reasoned to.

## 1. Verdict

- **All three I-43 conditions now key on the criterion, meaning the test set and τ together.** Under the run IDs where
  they failed, they now pass:
  - **GC** presses its declared straddle under `write_set_tau1e-08`. It reads PASS: 3 989 count leaves, 0 differing.
  - **G9** no longer gates `B0` at 1e-8 against GR's 1e-6 record. It reads PASS: 0 of 54 gated reference values
    differ.
  - **G1** under `census_tau1e-06` reads PASS: 0 of 3 654 values differ, 0 of 51 319 lines.
- **I-45.** G1 under `census_tau1e-08` reads PASS: 0 of 4 611 values differ. That is 3 values fewer than before, the
  three `audit_snapshot.wall_s`.
- **Every existing tooth still trips, and each changed gate has one new tooth, committed.** Totals:

  | gate | teeth now | teeth before |
  |---|---:|---:|
  | GC | 5/5 | 4/4 |
  | G9 | 5/5 | 4/4 |
  | G1 | 10/10 | 9/9 |

- **The gate tables at `b484d807`:**

  | run ID | PASS | FAIL | not run | teeth tripped |
  |---|---:|---:|---:|---|
  | `census_tau1e-08` | 28 | 1 | 0 | 184 of 184 |
  | `census_tau1e-06` | 27 | 2 | 0 | 183 of 184 |
  | `write_set_tau1e-06` | 27 | 1 | 1 | 180 of 184 |
  | `write_set_tau1e-08` | 27 | 1 | 1 | 180 of 184 |

  Gates other than PASS:
  - **GT (`test_set`), as expected:** it FAILs under `census_tau1e-06` (I-44) and refuses under the two write-set run
    IDs by design.
  - **G5 (`switch_composition`) FAILs under all four run IDs. I did not expect this** (§6). It is the same 3 values in
    each run ID, `resolved_switches` on the three `B2` pairs. One record was made before driver change DR13 and the
    other after it. The difference is DR13's new read-back key, present on one side only. I did not change or re-press
    anything to make it pass.
- **The campaigns and the traced runs are untouched (§8).**
  - `--jobs campaign --resume` keeps 553 of 553 under each run ID.
  - `--traced-runs check` reads 54 of 54 traced runs equal to their campaign records under each run ID.
  - `find -newermt '2026-10-02T18:03:38+02:00'` over the four `campaign/` folders lists 0 entries.
  - Over the four `traced_runs/` folders it listed 0 entries until the check itself ran. The check then rewrote its own
    `neutrality.json` (8 files). The only differences in those files are the commit stamp and the worktree paths.
- **The four tables documents.** Only verification-table rows and their stamp lines moved. No result cell moved.
  `--paper-tables check` reads IDENTICAL for all four, and `paper_cells_recount.py` reads 44 rows, 0 mismatched, for
  each.

## 2. The four changes

**One construction of "a criterion" (`harness/core/config.py`).** Three new functions:
- `is_at_declared_criterion(campaign, test_set)`. It requires the test set to be the one named, no tolerance rule, and
  every configuration's τ to equal the set's declared value (`TAU_BY_TEST_SET`).
- `at_declared_criterion(campaign, test_set)`. It returns the campaign itself when the campaign is already at that
  criterion. Otherwise it returns `replace(..., test_set=…, tau=None, tau_rule=None)`, keeping the run ID and its
  folder.
- `is_v4_criterion(campaign)`.

`archived_records._settings_are_v4s` already held the same predicate, including the tolerance rule. It now calls
`is_v4_criterion`.

### 2.1 GC (`count_neutrality`), `harness/gates/gate_count_neutrality.py`

**Was.** In `count_neutrality_body` (lines 853–862 at `e977c57d`):

```python
if declared_set is not None and campaign.test_set != declared_set:
    campaign = dataclasses.replace(campaign, test_set=declared_set, tau=None)
```

`archived_records._count_neutrality_jobs` held the same condition.

**Is.** A new function, `declared_campaign(campaign)`, returns `config.at_declared_criterion(campaign,
STRADDLE_TEST_SET[STRADDLE[1]])`. All three places that compose GC's jobs now use it:
- the body;
- `jobs_read`, which feeds the framework's survey and `--jobs count_neutrality`;
- the archived-records copy.

**Found on the way (`b484d807`, before any gate press).** `jobs_read` and the job listing composed GC's jobs under the
press's own campaign. Under the census run IDs, `--jobs count_neutrality` therefore listed 22 census-τ jobs as
"RUN — no record on disk". The body never makes those jobs (measured at `e977c57d`, `press00`). The framework's
staleness survey read the same non-existent paths, so GC's "runs read" line counted nothing it compared (trap T12's
shape).
- The pool resolves a job's test set and τ against the campaign it is listed under. The gate's
  `jobs=lambda: gates_mod.job_rows(jobs_read, declared_campaign(campaign))` now passes the declared campaign.
- At `b484d807`, `--jobs count_neutrality` under `census_tau1e-08` lists 25 jobs and keeps 25 (`press07`).
- GC's runs line now reads "25 record(s) — 22 at d1e94dc8, 3 at d08e8ab4".

The docstring of `STRADDLE_TEST_SET` said "the census value … a press under it is refused". That has been wrong since
the code began replacing the campaign. The docstring now states the criterion rule. The intent it states (V4's
predicate exactly) is the one this change implements.

**The new tooth, `a count moved, read under every run ID's settings`.**
- For each of the four settings {census, write set} × {1e-8, 1e-6}, the tooth builds a campaign from the press's
  campaign and composes GC's after-side job for the last compared pair through `declared_campaign`.
- All four must resolve to the very directory the press compared.
- One added to `node_calls_total` on a copy of that record must then be the one differing leaf.
- Keyed on the test set alone, the write set at 1e-8 would name another directory and the tooth would not trip
  (inferred from the code; not run against the old code).

Under every run ID the tooth tripped with the same text (measured, `press08` for `census_tau1e-08`, `press03` for the
others): "B/B2/st_regression's after-side job composed under the settings of 4 run IDs … resolves to this press's
directory under 4 of them; one added to node_calls_total (23509 → 23510) …: 1 differing leaf/leaves of 259".

### 2.2 G9 (`output_path`), `harness/gates/gate_output_path.py`

**Was.** Lines 447–450 at `e977c57d`:

```python
same_criterion = arms_mod.ARMS[arm].is_reference or campaign.test_set == V4_TEST_SET
```

**Is.** `same_criterion_as_the_reproduction_gate(campaign, arm)` returns `ARMS[arm].is_reference or
is_v4_criterion(campaign)`. Its docstring carries the reasoning, which the old inline comment held.

Two smaller changes in the same file:
- The comparison and the pass decision are extracted as `reference_arm_differences` and `reference_arm_check_passes`,
  so the tooth runs the body's own logic.
- `_reproduction_planned` builds GR's campaign through `at_declared_criterion(campaign, V4_TEST_SET)`. That also drops
  a tolerance rule, which GR's identities never carry; under the four run IDs nothing changes.

The "not gated" sentence now names τ ("… set at tau=1e-08, GR's on the write set at 1e-6").

**The new tooth, `a_solve_field_moved_on_a_reference_arm_at_the_same_criterion`.**
- **Part 1.** For every keep-the-loop arm the press gates, GR's own record stands in for the run, so the untouched
  sub-check passes. One added to `node_calls_solve_phase` on a copy must fail the sub-check and be the one field named.
  The gated arms are `BR` always, and `B0` too under the write set at 1e-6.
- **Part 2.** `B0` must be gated under the write set at 1e-6, and not under the write set at 1e-8, census at 1e-8 or
  census at 1e-6.

It tripped under all four run IDs (measured):
- Under `census_tau1e-08`: "gated here: BR ×3; … 3 of 3".
- Under `write_set_tau1e-06` there are 6 gated arms, `BR` and `B0` on three configurations, and it bites on 6 of 6.

### 2.3 G1 (`switch_neutrality`), `harness/gates/gate_neutrality.py`

**Was.** `CONDITIONAL_WITNESS["job_digest"] = "job_identity.test_set"` (line 563 at `e977c57d`). The digest was
excluded only where that one field was present on exactly one side.

**Is.** `job_digest` moves from `CONDITIONAL_WITNESS` to a new table, `FIELD_SET_WITNESS = {"job_digest":
"job_identity"}`.
- `compare_records` compares the digest only where both sides' `job_identity` blocks have the same top-level keys,
  meaning the same rendered fields.
- It excludes the digest where the keys differ or only one side carries the block.
- Where neither side carries the block, the name's own leaf decides, as before.

Top-level keys were chosen, not leaf paths. A nested `override_env` that differed in its keys still leaves the digest
compared, so the gate fails on it rather than excluding both.

**What it measures** (inspection at `2c5e281a` before the press; then the gate itself at `b484d807`):

| run ID | identity fields, before → after | digest | G1 |
|---|---|---|---|
| `census_tau1e-08` | same | compared | 4 611 compared, 0 differing |
| `census_tau1e-06` | τ on one side | excluded | 3 654, 0 (was 3 660, 6) |
| `write_set_tau1e-06` | test set and τ on one side | excluded | 3 648, 0 |
| `write_set_tau1e-08` | test set on one side | excluded | 3 654, 0 |

**The new tooth, `a_digest_moved_over_the_same_field_set`.**
- **Part 1.** One hex digit of `job_digest` changed on a copy of a captured record must be the one mismatch, named.
- **Part 2.** The same moved digest with `tau` rendered in one side's identity only (the census 1e-6 shape) must be
  excluded, with 0 differing.
- Witnessed by the test set alone, Part 2 would compare the digests and the tooth would not trip (inferred from the
  code).

Measured under `census_tau1e-08`: "job_digest 4789a0 -> 4789a1: over the same field set 1 of 833 values differ
(['job_digest']); with tau removed from one side's identity the digest is excluded and 0 of 831 differ".

### 2.4 I-45: `audit_snapshot.wall_s` through the exclusion review

**What the leaf is, by code.** `harness/child/child.py:971–976`, `install_exit_snapshot.hook`, adds
`time.perf_counter()` differences to `state["wall_s"]` on every call of the driver's snapshot hook.

**The review gained two committed blocks** (`harness/gates/exclusion_review.py`, `2c5e281a`):
- `G1_timing_named_leaves` covers every leaf of G1's pairs whose last name segment matches `(?:^|_)s$`. For each it
  reports:
  - which G1 table excludes it, or that none does;
  - the pairs carrying it on both sides, and how many read equal;
  - whether every value is a non-negative float;
  - for a compared name, how many other compared leaves of its own block differ.
- `G1_compared_leaves_differing` lists every compared leaf that differs, with the gate's own tables and name map.

**What it printed under `census_tau1e-08` at `2c5e281a`, before the leaf was listed** (`press02`):

```
G1's leaves named as a timing: 11 name(s); compared: ['audit_snapshot.wall_s', 'lift_residual.raw_s']
  audit_snapshot.wall_s   COMPARED  both sides on 3 pair(s), equal on 0, mismatched in G1 on 3; non-negative floats yes [0.030141944997012615, 0.04082065699913073]; same block: 72 compared, 0 differing []
  lift_residual.raw_s     COMPARED  both sides on 2 pair(s), equal on 2, mismatched in G1 on 0; non-negative floats yes [0.0, 0.0]; same block: 12 compared, 0 differing []
  (cpu_s, cpu_sys_s, cpu_user_s, evaluation_warmup.{measured.wall_s,restore_wall_s,warmup.wall_s,warmup_wall_s}, launcher.wall_s, wall_s: ALWAYS_EXCLUDED)
G1's compared leaves that differ: 1 name(s): {'audit_snapshot.wall_s': 3}
```

**Reading it.** `audit_snapshot.wall_s` is:
- a non-negative float of 0.030 to 0.041 s;
- different on all 3 BR pairs;
- the whole of G1's FAIL;
- beside 72 other compared values of its own block (positions, component counts, digests) that are all equal.

The stopwatch moved and the snapshots it timed did not. I listed it in `ALWAYS_EXCLUDED`, with its kind ("a timing or
the machine's state") in `ALWAYS_EXCLUDED_KIND` (`9c5ea415`).

**Not listed: `lift_residual.raw_s`.** It also matches the name pattern, but it is a physics residual in seconds: the
burn-time residual, `evaluate.py:1092–1102`. It reads equal and stays compared.

**At `b484d807`** (`press17`): compared timing-named leaves `['lift_residual.raw_s']`; compared leaves that differ: 0.

## 3. The README

`harness/README.md` changes in four places:
- **§6 (GC).** The declared criterion under every run ID. A sentence that GC writes its straddle record on every
  press, so inside a copied archive it rewrites the copied file, after which the copy step's byte check refuses (A114).
- **§11.** A paragraph on the three keys, the new teeth, and the I-45 leaf with the review that measured it.
- **Change log.** One entry.

## 4. The I-42 check before each press

Before any gate press under each run ID (at `b484d807`), I ran three checks. Their logs are in each run ID's press-log
folder:
- `--archive-collisions`;
- `--jobs all --resume`;
- `--jobs <gate>` for every run-making gate and reader.

| run ID | GC's archived records: other gates' jobs resolving into them | `--resume` on those jobs | what the presses would make |
|---|---|---|---|
| `census_tau1e-08` (`press04`, `press07`) | 0 | — | G5 3 (`B2` switch by switch, "no record on disk"); G7's tooth 1 smoke |
| `census_tau1e-06` (`press01`, `press02`) | 0 | — | GC 22 (the DR13 side, "no record on disk"); G5 3; G7 1 |
| `write_set_tau1e-06` (`press01`, `press02`) | **9**: G6, G2 and GT, 3 each, `A/A0/<configuration>/seed000/unperturbed/gate` | **KEPT** by all three | GC 22; G5 3; G7 1 (GT refuses before any run) |
| `write_set_tau1e-08` (`press01`, `press02`) | **0** (A113 listed 9) | — | GC 22; G5 3; G7 1 |

**Under `write_set_tau1e-08` the I-42 collision is gone.** GC now composes at 1e-6, so its references are the copied
V4-identity records, and G6, G2 and GT compose at 1e-8. The three 1e-8 references A113's refused GC press made are now
G6's and G2's own.

**Under `write_set_tau1e-06`** the nine jobs still resolve into GC's references. Every one would be kept, so nothing
was stopped for, and the stamp survey confirms none was re-made (§5).

**GR's archive.**
- GR's own 26 records and G9's 6 records listed "RUN — declared field(s) missing" are the read-only archive's records.
- GR is read once. G9 only reads its 6 (its capture runs only its own 11 jobs).
- `pool.refuse_a_read_only_archive` did not fire in any press. No press asked to write there (measured: no refusal in
  any log).

**G1** declares no job set, so `--jobs` cannot show its after capture. I composed G1's six after-capture jobs under
each run ID and asked `pool.job_listing`. This was a read-only inline inspection, not a committed script. All 6 were
kept under all four run IDs.

## 5. The gate tables, and what was kept and what was re-made

**Presses.**
- `--gate all --resume` per run ID: `census_tau1e-08` `press08`; the others `press03`.
- Under `census_tau1e-08` the chain stopped at G5's FAIL. Under `census_tau1e-06` it stopped at GT's FAIL, and under the
  write-set run IDs at GT's refusal.
- I pressed every later gate one by one, with a disk line before each: `press09`–`15` under `census_tau1e-08`,
  `press04`–`11` under the others.
- `--measure gate_table --resume`: `press16` under `census_tau1e-08`, `press12` under the others.

| gate | plan | `census_tau1e-08` | `census_tau1e-06` | `write_set_tau1e-06` | `write_set_tau1e-08` |
|---|---|---|---|---|---|
| `g0prime` | G0 | PASS 1/77, 4/4 | PASS 1/77, 4/4 | PASS 1/77, 4/4 | PASS 1/77, 4/4 |
| `copy_identity` | — | PASS 8/224, 12/12 | same | same | same |
| `edit_behaviour`, `self_containment`, `composition`, `rungs`, `provenance`, `data`, `run_path`, `capability`, `artifacts_check`, `artifacts_derive_inputs`, `artifacts_census`, `artifacts_per_run` | — | PASS (each), 0 mismatched | same | same | same |
| `resume_identity` | — | PASS 0/1 339, 15/15 | PASS 0/889, 15/15 | PASS 0/904, 15/15 | PASS 0/873, 15/15 |
| `evaluation_warmup` | — | PASS (read once) 0/19 876, 5/5 | same | same | same |
| `record_completeness` | G7 | PASS 0/281, 14/14 | same | same | same |
| **`count_neutrality`** | GC | PASS 0/50 114, **5/5** | PASS 0/50 114, 5/5 | PASS 0/50 114, 5/5 | **PASS** 0/50 114, 5/5 (was NOT RUN, refused) |
| `prime_map` | G2 | PASS 0/17 591, 3/3 | same | same | same |
| `entry_and_warm` | G6 | PASS 0/6 717, 3/3 | same | same | same |
| `test_set` | GT | PASS 794/13 424 (its drops), 4/4 | **FAIL** 0/13 424, 3/4 (I-44) | NOT RUN (refused, by design) | NOT RUN (refused, by design) |
| **`switch_composition`** | G5 | **FAIL 3/159**, 4/4 | **FAIL 3/159**, 4/4 | **FAIL 3/159**, 4/4 | **FAIL 3/159**, 4/4 |
| **`switch_neutrality`** | G1 | **PASS** 0/55 930, 10/10 (was FAIL 3/55 933) | **PASS** 0/54 973, 10/10 (was FAIL 6/54 979) | PASS 0/54 967, 10/10 | PASS 0/54 973, 10/10 |
| `reproduction` | GR | PASS (read once) 0/256, 8/8 | same | same | same |
| **`output_path`** | G9 | PASS 0/3 879, 5/5 | PASS 0/3 879, 5/5 | PASS 0/3 879, 5/5 | **PASS** 0/3 879, 5/5 (was FAIL 12/3 879) |
| `written_file_gap` | — | PASS 0/42, 4/4 | same | same | same |
| `tally_contracts` | — | PASS 0/538, 18/18 | same | same | same |
| `run_kind_separation` | — | PASS 0/2 401, 7/7 | PASS 0/1 973 | PASS 0/1 988 | PASS 0/1 957 |
| `stage_provenance` | — | PASS 0/13, 5/5 | same | same | same |
| **totals** | | **28 PASS, 1 FAIL**; 184/184 teeth | **27 PASS, 2 FAIL**; 183/184 | **27 PASS, 1 FAIL, 1 not run**; 180/184 | **27 PASS, 1 FAIL, 1 not run**; 180/184 |

**GC's straddle** under every run ID is `DR12` at [`24b78e2d`, `d08e8ab4`] → `DR13`, with 22 pairs, 3 989 count leaves
(0 differing), 33 prime checks (0 failing) and 46 125 components (0 differing):
- under `census_tau1e-08` the DR13 side is at `d1e94dc8` (A115's records, kept);
- under the other three it is at `b484d807` (made by this task).

**G9's not-gated `B0` rows** (measured; reported, not gated):

| run ID | fields differing from GR's record, tok / lad / st |
|---|---|
| `census_tau1e-06` | 4 / 4 / 6 of 9 |
| `write_set_tau1e-08` | 4 / 4 / 4 of 9 |
| `census_tau1e-08` | not re-read |

Under `write_set_tau1e-06` `B0` is gated, and 0 fields differ on all three configurations.

**GT under `census_tau1e-06`** (measured, `press03`; I-44): 0 of 8 binding drops bite and 8 controls are bit-identical.
The tooth "a biting drop's exit state replaced by the full run's" did not trip: "no drop bit, so there is no biting exit
state to doctor". This is unchanged from A114.

**What was kept and what was re-made** (`run_stamp_survey.py --runs runs/<run ID> --json …/stamp_survey_end.json`,
after every press; measured). Every gate verdict (`gate.json`) is stamped `b484d807`. The run records at `b484d807`:

| run ID | run records at `b484d807` | which | every other run record |
|---|---|---|---|
| `census_tau1e-08` (1 295 records) | 4 | G5's 3 switch-by-switch `B2` runs (new identities, no earlier record); G7's tooth re-made 1 smoke run (`A/AR/st_regression/seed000`, by design on every press) | kept at its earlier commit |
| `census_tau1e-06` (867) | 26 | GC's 22 DR13-side runs (new; this run ID had no DR13 side); G5's 3; G7's 1 | kept |
| `write_set_tau1e-06` (882) | 26 | the same 22 + 3 + 1 | kept |
| `write_set_tau1e-08` (851) | 26 | the same 22 + 3 + 1 | kept |

The 22 GC DR13 records carry the same 22 directory digests under all three run IDs, so the identity is the same
whatever the run ID (measured). No record was re-made in place: every record at `b484d807` is in a directory that had
no complete record of its job.

**Kept, by gate (measured from each verdict's "runs read" line):**
- G1's after captures, at `d1e94dc8`, `448d6bde`, `52ea57be` and `b44c88c4` respectively.
- GC's DR13 side under `census_tau1e-08` (`d1e94dc8`), and GC's references (`d08e8ab4`).
- G2, G6 and GT.
- G9's 11 runs (e.g. `521a753c` under `census_tau1e-08`) and GR's 6.
- `written_file_gap`.
- The read-once archives.

## 6. The unexpected: G5 FAILs under every run ID

**What failed** (measured; `runs/<run ID>/gates/switch_composition/gate.json`).
- On each of the three `B2` pairs, 1 of 10 run values differs: `resolved_switches`. 3 of 159 differ in all; 43 switch
  names compared, 0 differing.
- Inside `resolved_switches` the two sides agree on every common key. The one difference is
  `process.core.solver.module_solve.BLOCK_TRACE_CENSUS_PATH`, present (value `None`) on the switch-by-switch side only.
- The objective's hex, `ifail`, iterations and the other values are equal.

**The sides' commits.**

| run ID | matrix side (kept) | switch-by-switch side (made by this press) |
|---|---|---|
| `census_tau1e-08` | `d8873d49` | `b484d807` |
| `census_tau1e-06` | `448d6bde` | `b484d807` |
| `write_set_tau1e-06` | `52ea57be` | `b484d807` |
| `write_set_tau1e-08` | `b44c88c4` | `b484d807` |

**The code.**
- `harness/gates/gate_composition.py:166–187` (`COMPARED`, its last entry `("resolved_switches", "resolved_switches")`).
- `:360–372`, the loop that marks a value differing when `left != right` after `portable_resolved_switches`.

**The cause, inferred and not tested.**
- A115's DR13 added the driver read-back `BLOCK_TRACE_CENSUS_PATH` and the switch
  `PROCESS_ARCH_BLOCK_TRACE_CENSUS_SETS`.
- The new switch changed the identity of the switch-by-switch job, whose hand-built column names every switch. So that
  job had no record and was made now, after DR13.
- The matrix-composed job's identity did not change. Its pre-DR13 record is complete under the record contract and
  `--resume` kept it.
- The gate thus compares a pre-DR13 record with a post-DR13 one, and the new key is on one side.
- A115 did not press G5. This is the first press of G5 since DR13.

**Not changed, not re-pressed, not worked around.** A from-scratch G5 press, which would re-make the matrix side, would
very likely PASS. That is a choice about which records to compare, so it is the orchestrator's to make, not mine.

## 7. The four tables documents

Each was re-rendered with `--paper-tables write` (`press20`) and committed in `12472063`. Only lines of the
verification table moved (`git diff -U0`):

| document | lines out / in | what moved |
|---|---|---|
| `paper_tables.md` | 7 / 7 | the stamp line (now `[0353c524, b484d807]`); G0 re-dated; **G1 FAIL 3/55 933 → PASS 0/55 930, 10/10**; G6 re-dated; **G5 PASS 0/156 → FAIL 3/159**; G9 4/4 → 5/5 teeth; GT re-dated |
| `paper_tables_census_tau1e-06.md` | 7 / 7 | the stamp line; G0; **G1 FAIL 6/54 979 → PASS 0/54 973, 10/10**; G6; **G5 PASS → FAIL 3/159**; G9 5/5; GT re-dated (still FAIL 0/13 424, 3/4) |
| `paper_tables_write_set_tau1e-06.md` | 6 / 6 | the stamp line; G0; G1 (PASS, 10/10); G6; **G5 PASS → FAIL 3/159**; G9 5/5 |
| `paper_tables_write_set_tau1e-08.md` | 6 / 6 | the stamp line (27 → 28 records read); G0; G1 (PASS, 10/10); G6; **G5 PASS → FAIL 3/159**; **G9 FAIL 12/3 879 → PASS 0/3 879, 5/5** |

**No result cell moved.** Checks afterwards, per run ID:
- `--paper-tables check` reads **IDENTICAL** for all four (`press21`).
- `paper_cells_recount.py --runs runs/<run ID> --document <doc>` reads 44 cell rows, 0 mismatched, for all four
  (`press22`).

## 8. The campaigns and traced runs untouched (measured)

**Before the traced-run check** (`press23`), `find runs/<run ID>/campaign -newermt '2026-10-02T18:03:38+02:00'` and the
same over `traced_runs/` read:

| run ID | `campaign/` entries newer | `traced_runs/` entries newer |
|---|---|---|
| `census_tau1e-08` | 0 of 7 933 | 0 of 876 |
| `census_tau1e-06` | 0 of 7 933 | 0 of 873 |
| `write_set_tau1e-06` | 0 of 7 895 | 0 of 874 |
| `write_set_tau1e-08` | 0 of 7 893 | 0 of 873 |

**`--jobs campaign --resume`** (`press24`) keeps 553 of 553 and runs 0 under each run ID.

**`--traced-runs check`** (`press25`, both job sets per run ID):

| job set | equal to campaign record | state components, 0 differing | traces consistent |
|---|---|---|---|
| `sweep_residual` | 48 of 48 | 100 680 | 48 of 48 |
| `sweep_residual_st_more` | 6 of 6 | 14 886 | 6 of 6 |

The count leaves compared under `sweep_residual`, all 0 differing, are 3 585 / 3 570 / 3 600 / 3 618 for the four run
IDs.

**The check is not read-only.** `experiment_runner.py:1361–1363` writes `traced_runs/<job set>/neutrality.json`, so
afterwards `find -newermt` over `traced_runs/` lists exactly those 8 files and nothing else.
- I copied each file to my scratchpad before the check and compared it after.
- The only differences are `tree_git_head` and the 96 absolute paths in `rows[].campaign` and `rows[].traced` (A115's
  worktree → this one). No count differs.
- No traced run record or trace file changed.

## 9. Disk

| when | `/mnt/c` free |
|---|---|
| 18:03, task start | 131 GB |
| before every press (`disk_log.txt` per run ID) | 131 GB |
| end | 131 GB |

The 20 GB floor was never approached.

## 10. Every decision, and everything unexpected

**Decisions.**
1. **One shared predicate in `config.py`, not three local conditions.** GC, G9, the archived-records copy and GR's
   freeze all now answer "is this V4's criterion?" through `is_at_declared_criterion`. It includes the tolerance rule:
   a rule campaign would otherwise have kept its rule through GC's and G9's `replace(..., tau=None)`. That is latent at
   the four run IDs, which carry no rule.
   - Reversal: inline the old conditions.
2. **G1's digest condition is "the same top-level identity fields"** (`FIELD_SET_WITNESS`), not "the τ field present
   on one side". It is the general statement of when two digests are comparable, and it covers both test set and τ.
   - Reversal: restore `CONDITIONAL_WITNESS["job_digest"]`.
3. **GC's job listing composes under the declared campaign too** (`b484d807`). Without this, the brief's I-42 check
   (`--jobs count_neutrality`) would have listed jobs GC never makes. The fix changes GC's "runs read" line under the
   census run IDs from a survey of paths that do not exist to its real 25 records.
   - Reversal: `git revert b484d807`.
4. **I extended the exclusion review rather than hand-reading the records for I-45**, so the evidence is a committed
   stage's output. I pressed it once before listing the leaf (`2c5e281a`, `press02`) and once after (`b484d807`,
   `press17`). The name pattern caught one non-timing name, `lift_residual.raw_s`, which the review shows compared and
   equal. I did not list it.
5. **G5's FAIL was left as it is** (§6).
6. **GC's DR13 side was made by this task under the three other run IDs** (66 runs) rather than copied from
   `census_tau1e-08`.
   - The copy step refuses a run ID whose GC straddle file was rewritten (I-43's README note).
   - The gate's after side is by construction made at the pressing commit, whose driver equals `d1e94dc8`'s.
7. **The README sentence on GC rewriting its verdict file** describes the straddle record, `straddles/<b>__<a>.json`.
   That is the file A114's byte check named.

**Unexpected.**
1. **G5 FAILs under all four run IDs** (§6).
2. **GC's `--jobs` listing and its framework survey composed under the press's settings** (decision 3). This is a
   fourth instance of the I-43 class, in a listing rather than a verdict.
3. **`--traced-runs check` rewrites `neutrality.json`** (§8), so `find` over `traced_runs/` cannot list nothing after
   the check that the brief also asks for.
4. **Under `census_tau1e-06`, G9 reports `B0` on `st` with 6 of 9 fields differing from GR**, not 4 as on tok and lad.
   It is reported and not gated; it is not explained here.

## 11. What I did not check

- **The old code against the new teeth.** That each new tooth would not trip under the condition it replaces is
  inferred from the code. I did not revert the conditions and press.
- **Whether a from-scratch G5 press passes.** Not tried (§6).
- **A tolerance-rule run ID.** The `tau_rule` branch of `is_at_declared_criterion` is exercised by no press and no
  tooth.
- **`experiment/test_sets.census_campaign`** has the same test-set-and-τ predicate without the rule. It is not one of
  the three gates and was not changed.
- **G1's after captures under the three non-default run IDs** straddle `9ed0da4c` → their campaign commits, not DR13.
  G1's DR13 straddle was pressed only under `census_tau1e-08`, by A115. G1 binds the tree, not the settings.
- **The census-set `B0` differences against GR under G9** (4 to 6 of 9 fields). Reported, not explained.
- **The copy step's byte check** (`--copy-archived-records … --apply` again) was not re-run. GC rewrote `DR12__DR13.json`
  under `census_tau1e-08` at this press; the other run IDs had no copied file of that name.
- **"Untouched"** rests on modification times, the resume decision and the traced-run comparison, not on per-file
  hashes of the campaign records.
- **The G1 after-capture keep decision** was read by an inline, uncommitted composition (§4). The gate's own "runs read"
  line agrees: 6 records at each run ID's earlier commit.
