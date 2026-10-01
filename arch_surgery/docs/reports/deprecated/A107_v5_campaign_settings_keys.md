# A107 (v5-campaign-settings-keys) — one folder of records per campaign settings

> **Document status** — **MERGED 2026-10-01 at `3d369b6c` (`--no-ff`; the orchestrator's assessment at the end); archived.** Records relocated to `arch_surgery/idf_probe/runs/A107_runs/v5_campaign_settings_keys/` (the latest relocated V5 records tree, in the run-ID layout: `census_tau1e-08/`, `write_set_tau1e-06/`). Was: **OPEN (task report, awaiting the orchestrator's assessment).** Task A107, branch
> `A107-v5-campaign-settings-keys`, 2026-10-01. Harness only (`arch_surgery/MDA_partitioning_experiment_v5/`, nothing
> under its `PROCESS/`, nothing under `process/models/`, nothing in V4). Every number below comes from a committed
> entry point (`experiment_runner.py`, `paper_cells_recount.py`) at the commit named beside it; the press logs are under
> each run ID's `_press_logs/A107/` in the relocated tree
> `arch_surgery/idf_probe/runs/v5_campaign_settings_keys/` (§9).

## 1. Verdict

**The feature is built and its acceptance test passes.** The V5 harness now keeps one self-contained folder per
campaign settings, `runs/<run ID>/`, the run ID derived by one function from the test set and the tolerance or
tolerance rule. The seeded V5 tree was adopted under `census_tau1e-08` by one rename per entry. The adoption changed
0 of 17 092 files by path, size or modification time, and 0 of 1 175 run records by SHA-256. After it:

- the campaign resumes **553 of 553** (`--jobs campaign`, nothing re-made);
- `--paper-tables check` reads **IDENTICAL**, `paper_tables.md` has 0 changed bytes against `76de5646`, and the
  independent recount finds 44 cell rows, 0 mismatched;
- the gate table reads **29 PASS, 176 of 176 teeth** (`--measure gate_table --resume`).

The acceptance check `--run-isolation smoke` pressed the smoke chain under `write_set_tau1e-06` and found:

- **(a)** every file the press wrote is in `runs/write_set_tau1e-06/`;
- **(b)** `runs/census_tau1e-08/` is **identical**: 17 101 files by path, size and modification time, and 1 175
  `metrics.json` by SHA-256, the same before and after;
- **(c)** the reproduction gate was not pressed, and its verdict (PASS, 20 of 20, at `d6c246a1`) reads from the new
  folder;
- **(d)** the listing shows both run IDs;
- both teeth tripped.

**One finding the next task must act on (§7, L1).** The smoke's *reading stages* do not pass in a fresh run ID. Its
seven runs completed, but `tally_contracts` FAILed: 40 of 296 checks mismatched and 17 of 18 teeth tripped. A run ID
with no campaign records and no gate records of its own has, as the tally's gate population, only the reproduction
gate's twenty copied records. Those are made at the copy commit's record contract and are refused as incomplete. This
is a result, reported as it is. Once the next task's campaign records exist, the tally reads the campaign population
instead.

## 2. The layout as built

```
runs/                                      (in a worktree: MDA_partitioning_experiment_v5/runs/)
  _numba_cache/   _mplconfig/              shared caches — the only shared entries
  census_tau1e-08/                         the V5 campaign, adopted
    run_settings.json                      {run_id, test_set: census, tau: 1e-08, tau_rule: null, …, how: adopted …}
    campaign/{entry_references,evaluation,optimisation}/…   553 records, campaign/press.json
    supplementary/st_census_exact/…        50 records
    gates/_runs/ …  gates/<gate>/gate.json  gates/<stage>/measurements.json
    timing/  single/  census/  census_test_sets/  artifacts/  input_files/  reading_stages/
    _press_logs/                           every earlier task's logs, and A107's census-side ones
  write_set_tau1e-06/                      the next campaign's folder, initialised by this task
    run_settings.json                      {run_id, test_set: write_set, tau: 1e-06, …, how: first press …}
    archived_records_copied.json           what was copied from census_tau1e-08, every file's SHA-256
    gates/reproduction/ gates/_runs/ gates/count_neutrality/straddles/ gates/switch_neutrality/{before,straddles}/
    gates/evaluation_warmup/before/  input_files/*/…_lifted.IN.DAT          (the copied read-only records)
    smoke/                                 the smoke chain's 7 records and press.json
    gates/{tally_evaluation,tally_optimisation,tally_contracts,reproduction,resume_identity,count_neutrality}/
    run_isolation/smoke.json               the acceptance check's record (and the two earlier presses', §6)
    _press_logs/A107/
```

`Campaign.runs_dir` **is** the run ID's folder (`config.default_campaign`). Every path the harness derives from it lands
inside the folder without a second construction: the chain's roots, the shared pool, the verdicts, the tallies, the
timing stages, the derived input files and the single runs. Every job identity renders its paths relative to it, which
is why a folder moved whole keeps every digest.

## 3. The run ID

`config.run_id_for(test_set, tau, tau_rule)`:

- `<test set>_tau<repr(τ)>` without a rule, for example `census_tau1e-08`, `write_set_tau1e-06`, `census_tau1e-12`,
  `write_set_tau5e-07`;
- `<test set>_rule_<rule>` under a rule, for example `census_rule_epsvmc_times_epsfcn`.

**It is injective over the settings the harness admits:**

- The test set is one of the two declared names (`census`, `write_set`), and neither is a prefix of the other, so the
  test set can be read back unambiguously from the start of the ID.
- After the test set comes either `_tau` followed by Python's `repr` of the float, or `_rule_` followed by a declared
  rule name. `repr` round-trips, so two different τ never print alike. The rule names are distinct by declaration.
  `_tau` and `_rule_` cannot be confused with each other.
- A campaign is fully described by these two settings:
  - a rule replaces τ;
  - `--tau` equal to the declared value is the same campaign, with the same jobs and the same run ID;
  - the timers belong to the press, not the campaign;
  - a supplementary stage carries its own τ in its jobs.

A τ that is not positive and finite is refused, so `inf` and `nan` never become folder names. The ID is readable,
contains no spaces, and is stable. `config.DEFAULT_RUN_ID = census_tau1e-08`.

**Selecting the run.** Every entry point takes the settings as before (`--test-set`, `--tau`, `--tau-rule`); no
`--run-id` was added, because no case needed one. Every invocation prints the run ID line first, for example
`run ID write_set_tau1e-06: test set write_set, tau 1e-06; records under runs/write_set_tau1e-06/`.

Every verdict, stage, press, timing and listing record carries a `run` stamp:
- `framework.Gate.run` and `Measurement.run` read it from the folder's `run_settings.json` (`framework.run_stamp`);
- the chain's `press.json`, the runner's stage records, the timing records and the reading-stages record stamp it
  directly.

The readers refuse a record stamped with another run ID (`run_layout.assert_stage_record_is_of_this_run`):
- the gate table refuses such a verdict;
- the paper's document refuses such a stage record.

A record with no stamp was made before the layout and is read as belonging to its folder. The guard
`run_layout.open_run` refuses a press in three cases:
- `runs/` still in the old layout, naming the adoption;
- a folder whose `run_settings.json` disagrees with the settings asked for;
- an unreadable settings file.

## 4. What is shared, what is per run ID, and how read-only records reach a new run ID

**Shared** (`config.SHARED_CACHES`): `_numba_cache/` and `_mplconfig/` at the top level of `runs/`.
- Both are pure caches: numba's compiled functions are keyed by source digest, and matplotlib's font cache is never
  read by a child.
- Neither carries a result, so a new run ID starts warm.
- `switches.base_environment(cache_dir=…)` and the pool's directory creation use `Campaign.cache_dir`.
- After the adoption the cache paths are what they were, `runs/_numba_cache`.

**Per run ID:** everything else, including the press logs.

**Isolation, enforced in the pool:**
- **Step 2 of `pool.directory_for`** searches `pool._record_index`, which is built over `campaign.runs_dir`, the run
  ID's folder, and nothing else. Another run ID's record is therefore never a candidate.
- **A job that names a directory** in another run ID's folder is refused by `pool.refuse_another_runs_folder`. Both
  return paths of `directory_for` go through it, so every `pool.run` passes it before any directory is made or
  removed.
- **The runner refuses `--outdir`** into another run ID's folder.
- **Demonstrated from the button** (press20, press21 under `write_set_tau1e-06`): `--run --outdir
  runs/census_tau1e-08/…` and `--gate g0prime --outdir runs/census_tau1e-08/gates` are both REFUSED, exit 3, and
  nothing was created.

**Read-only records: an explicit copy, not a shared area.** The command is `--copy-archived-records <from run ID>`.
Without `--apply` it only lists what it would copy and creates no folder. The code is `harness/gates/archived_records.py`.

Why a copy: a job identity renders its entry-state paths relative to the run ID's folder.
- A record in a shared area outside the folder renders against another root. The gates' own job sets would never
  resolve to it and would make it again, which is exactly the press the copy exists to avoid.
- A record copied to the same relative path is the same job by construction, and the folder stays self-contained.
- Copies, not hard links: a re-press rewrites a verdict file in place, and a hard link would carry that write into the
  other run ID's folder.

What is copied (`ARCHIVES`, each with its reason):
- GR's verdict directory, and the pool records of its job set (27; 2 of its job set's directories were absent at the
  source too: the unnamed `AR` substitutes on tok and lad);
- GC's straddle records, and the 47 pool records of its references and both labelled sides;
- G1's `before` capture and archived straddles;
- the warm-up gate's cold-child records;
- the two lifted input files.

The cost is **1 904 files, 468.9 MB** per new run ID, and one command.

Copied at `9e05d87c`, press11:
- every copied file's SHA-256 was compared with the source's;
- `archived_records_copied.json` lists every one.

Then the archives' job sets were composed under each campaign and compared job for job (press12, at `3f19c89b`'s code):

| job set | under `write_set_tau1e-06` | under `census_tau1e-08` | jobs resolving or deciding differently |
|---|---|---|---|
| reproduction | 29 jobs, `--resume` keeps 3 | 29 jobs, keeps 3 | **0** |
| count_neutrality | 47 jobs, keeps 36 | 47 jobs, keeps 36 | **0** |

The non-kept rows are the same in both folders: records made at earlier record contracts, which these gates read and
never make.

**The new run ID's gate presses work with the copies** (`--resume`, under `write_set_tau1e-06`, at `ce84a759`):

| gate | result |
|---|---|
| `reproduction` | PASS, 8/8 teeth. A read of `verdict_at_d6c246a1.json` in the new folder; 256 compared, 0 mismatched |
| `count_neutrality` | PASS, 4/4 teeth. The item5 → DR12 straddle: 22 run pairs, 3 989 count leaves, 0 mismatched; 25 of 25 records kept, **0 runs made** |
| `resume_identity` | PASS, 14/14 teeth (13 before, plus this task's) |

## 5. The adoption command and its listing

```
python experiment_runner.py --adopt-records-layout          # the listing (press02)
python experiment_runner.py --adopt-records-layout --apply  # the move (press03, at 9f840d70)
```

**The run ID is decided by the campaign records' job-identity settings.** All 553 are `census`, τ 1e-08, no rule, so
the run ID is `census_tau1e-08`.

The other records are carried along and counted:

| run kind | settings | count |
|---|---|---|
| gate | census 1e-08 | 134 |
| gate | write_set 1e-06 | 280 |
| smoke | census 1e-08 | 8 |
| smoke | census 1e-12 | 26 |
| smoke | rule `epsvmc_times_epsfcn` | 7 |
| smoke | write_set 1e-06 | 7 |
| supplementary | census 1e-12 | 50 |
| timing | census 1e-08 | 110 |

These carry their own settings by design: GR's are V4's, GC's are its declared set, a `--run` smoke has whatever it
was asked for, and they belong to the press that made them.

**The move:**
- 11 renames, `runs/<entry>` → `runs/census_tau1e-08/<entry>`, for `_press_logs`, `artifacts`, `campaign`,
  `census`, `census_test_sets`, `gates`, `input_files`, `reading_stages`, `single`, `supplementary` and `timing`;
- `_numba_cache` and `_mplconfig` stay at the top level;
- 1 175 run records before and after;
- the manifest of the moved entries, compared by path relative to the entry: 17 092 files by size and modification
  time and 1 175 by SHA-256, **0 differing**;
- the comparison is written into `run_settings.json`.

A tree whose campaign records carry more than one setting is refused with the list. The settings file is written
before the renames, so an interrupted adoption leaves a folder that the next run completes. The renames were not
refused by the sandbox.

**The listing, `--runs`** (press24, at `ce84a759`):
- **`census_tau1e-08`:**
  - 553 campaign records at `6221af70` (458) and `f4a75f8e` (95), by phase:
    - entry references: ok 3;
    - evaluation: ok 275;
    - optimisation: ok 255, crashed 20.
  - 1 175 run records.
  - Gate table 29 PASS of 29.
  - Three tallies present.
  - `paper_tables.md` present.
- **`write_set_tau1e-06`:**
  - 0 campaign records.
  - 144 run records.
  - No gate table.
  - The two phase tallies present (the smoke's); no `tally_supplementary`.
  - `paper_tables_write_set_tau1e-06.md` not present.

## 6. The acceptance test

`harness/run_isolation.py`, pressed as `experiment_runner.py --test-set write_set --run-isolation smoke` at 2 workers
with the timers on. The check works as follows:
- it takes a manifest of every file under `runs/` except the shared caches: path, size, `mtime_ns`, and SHA-256 for
  every `metrics.json`;
- it presses the smoke;
- it takes the manifest again;
- it checks (a)–(d) and runs two teeth.

There were three presses; all three records are kept in `write_set_tau1e-06/run_isolation/`.

| | press14 (`e2a64e9f`, no `--resume`) | press16 (`ce84a759`, `--resume`) |
|---|---|---|
| smoke runs | **7 made** (st_regression: A0 ×2, AR, A2, BR, B0, B2), all `ok` | the same 7 kept |
| smoke reading stages | `tally_evaluation` refused: without `--resume` the tally refuses the copied records at other commits | `tally_contracts` **FAIL**: 40 of 296 mismatched, 17/18 teeth (§7, L1) |
| (a) written inside | 95 files: `_press_logs` 1, `smoke` 94; **0 outside**; 7 run records, all under `smoke/` → PASS | 5 files: `_press_logs` 1, `gates` 3, `smoke` 1; **0 outside** → PASS |
| (b) `census_tau1e-08` | 17 101 files, 1 175 records digested; added 0, removed 0, changed 0 → **IDENTICAL** | the same → **IDENTICAL** |
| (c) GR not pressed | 30 paths watched, 0 changed; verdict read PASS, 20/20, at `d6c246a1`, from `runs/write_set_tau1e-06/gates/reproduction/verdict_at_d6c246a1.json` → PASS | the same → PASS |
| (d) listing | `census_tau1e-08`, `write_set_tau1e-06` → PASS | the same → PASS |
| teeth | 2/2 | 2/2 |
| verdict | **PASS** | **PASS** |

The second press, press15 at `e2a64e9f` with `--resume`, failed (a). My criterion at the time required new run
records, and a resumed press keeps them. That is a defect of the check, not of the layout. The criterion was changed to
"the press record `smoke/press.json` was written inside" (`ce84a759`), and press16 was made under it. The FAIL record
is kept as `second_press_resume_criterion_a_required_new_records.json`.

**The teeth:**
1. **A job never resolves into another run ID's folder.** This is also a tooth of gate `resume_identity`. In a scratch
   `runs/` with two run IDs' folders:
   - a job naming its directory in the other folder is refused (PoolError);
   - an unnamed job whose digest is on disk only in the other folder resolves to its canonical directory in this one;
   - as a control, the same record put inside this folder is found by digest.
2. **A doctored after-manifest.** One `metrics.json` digest of `census_tau1e-08` is zeroed in a copy of the
   manifest, and the comparison reports exactly that file.

## 7. Limits: what a campaign under a second run ID still trips over

- **L1 — the tallies in a run ID with no campaign records.** The smoke's reading stages read the tally's gate
  population, which in a fresh run ID is GR's twenty copied records. Those were made at the copy commit's record
  contract and are refused as incomplete (missing `campaign_test_set`, `schedule_resolution`, `loop_test_sets`, and the
  evaluations' `evaluation_warmup`). As a result `tally_contracts` FAILs, 40 of 296, and its tooth "the fixed-point
  distance's restriction" does not trip on that population. Without `--resume` the tally refuses even earlier.
  - Before the next campaign this shows only on the smoke. Once campaign records exist, the tally's population is the
    campaign's.
  - The next task should read `tally_contracts` after its campaign press. It should not take the smoke's FAIL as
    evidence about the layout: in `census_tau1e-08` the same chain reads the campaign population.
- **L2 — the gates under `write_set_tau1e-06`.** `--jobs all` lists 120 distinct jobs over 29 gates, of which `--resume`
  keeps 25.
  - GT (`test_set`) is refused under the fallback by design.
  - G1 (`switch_neutrality`) and `evaluation_warmup` read archives made under **census** settings. Their copies are in
    place, but under write_set the gates compose write_set jobs, so whether they PASS is their verdict to give. It was
    not pressed here.
  - G2 (`prime_map`) would make 12 of its 15 jobs.
  - A full `--gate all --resume` under the new run ID is the next task's, and it makes PROCESS runs.
- **L3 — the supplementary stage** (`st_census_exact`, census at 1e-12) has jobs whose identity is independent of the
  campaign's settings. Pressed under `write_set_tau1e-06`, it would re-make its 50 records in that folder. Whether a
  write-set campaign is reported beside it at all is a decision, not a layout question, so it was not copied.
- **L4 — records of other settings inside `census_tau1e-08`.** The adoption carried along the 7 write-set smokes and 7
  rule smokes of earlier tasks; they are named by their settings under `single/`, plus one rule smoke in
  `gates/_runs/`. They are smoke records, never in a published population. They stay where they were made.
- **L5 — no comparison stage**, by the user's instruction: the folders are the comparison's input.
- **L6 — `paper_tables_<run ID>.md` is not yet rendered for any run ID.** Its header line ("Of run ID …") is printed
  only for a non-default run ID, so the committed `paper_tables.md` stays byte-identical. The default document's name
  is what says which campaign it is of.

## 8. Decisions taken alone, with reversals

1. **Copy, not a shared area, for the read-only records** (§4). Reversal: a shared area would need the pool to search
   a second root, and the identity to render paths against it.
2. **`Campaign.runs_dir` is the run ID's folder.** The run ID is a stored field, so a gate that replaces a setting for
   its own jobs (GC's straddle set, the census stage's fallback) keeps writing into the press's folder.
3. **The adoption is decided by the campaign records alone**, and the other kinds are carried along and counted. Under
   a stricter rule, counting every kind, the seeded tree itself would be refused: it holds rule and write-set smokes.
4. **The press logs are per run ID**; `_press_logs/` moved into `census_tau1e-08`.
5. **The lifted input files are copied** rather than derived again under the new run ID: their bytes are gated on the
   committed digest.
6. **The acceptance check is a runner stage with a record and teeth, not a registered gate.** A registered gate would
   be NOT RUN in `census_tau1e-08`'s table, and pressing it there would change the gate-table stamp line in
   `paper_tables.md`. For the same reason, no gate was pressed under `census_tau1e-08` in this task; only
   `--measure gate_table --resume` was.
7. **The pool's "experiment:" rendering of `override_env` paths** is anchored to `config.EXPERIMENT_DIR`, not to
   `runs/`'s parent. That parent moved one level down, and naming the directory keeps G5's three digests as they were.
8. **The gate table's `record` column** is now relative to the experiment folder, for example
   `runs/census_tau1e-08/gates/<gate>/gate.json`. It is not printed in `paper_tables.md`.
9. **Isolation criterion (a)** was changed after press15 (§6).

## 9. The gate table after, and the records

`--selfcheck` after the adoption: PASS (press09, at `9f840d70`).

`census_tau1e-08`: 29 PASS, 0 FAIL, 0 not run, 176 of 176 teeth (press06, `--measure gate_table --resume` at
`9f840d70`'s tree). The verdict files are the ones A105 left; none was re-pressed, so the verification table's stamp
line, and the whole of `paper_tables.md`, is unchanged.

**Relocation.** `MDA_partitioning_experiment_v5/runs/` was moved whole by `mv` on the same filesystem to
**`arch_surgery/idf_probe/runs/v5_campaign_settings_keys/`**:
- 1 319 run records before and after (1 175 in `census_tau1e-08`, 144 in `write_set_tau1e-06`);
- 20 101 files before and after.

The worktree's `runs/` no longer exists. Seed the next task's `runs/` from that path, keeping the run-ID folders.

## 10. Files changed

- `harness/core/config.py`: `RUNS_ROOT`, `run_id_for`, `SHARED_CACHES`, the `Campaign.run_id`/`runs_root` fields,
  `settings_run_id`, `cache_dir`, `default_campaign` resolving the run ID's folder, and `DEFAULT_RUN_ID`.
- `harness/core/run_layout.py` (new): the settings file, the guard, the stamps, the header, the stage-record check,
  the manifest, the adoption and the listing.
- `harness/core/pool.py`: `refuse_another_runs_folder` and `other_run_folder`, the index confinement documented, the
  caches in `cache_dir`, and the "experiment:" rendering.
- `harness/core/framework.py`: `run_stamp` on every verdict and stage record.
- `harness/gates/archived_records.py` (new): the copy, the resolution and the agreement.
- `harness/run_isolation.py` (new): the acceptance check.
- `harness/gates/gate_resume_identity.py`: the tooth `a_job_never_resolves_into_another_run_ids_folder`.
- `harness/gates/registry.py`: the gate table refuses verdicts of another run ID; the record column.
- `harness/measurement/paper_tables.py`: the document per run ID, the header line, and the stage-record run check.
- `harness/chain.py`: `chain_root` without A105's `_tau_rule_` root, and the press record stamped.
- `harness/experiment/switches.py` and `arms.py`, `harness/gates/selfcheck.py`: `cache_dir`.
- `experiment_runner.py`:
  - new flags `--runs`, `--adopt-records-layout`, `--copy-archived-records`, `--apply` and `--run-isolation`;
  - the run ID header and guard;
  - `--outdir` refused into another run ID's folder;
  - stage records stamped.
- `paper_cells_recount.py`: default `runs/census_tau1e-08/`.
- `run_stamp_survey.py`: help text.
- `harness/README.md`: §12 rewritten for the layout, plus §1, §5, §13 and the change log.

Commits: `9f840d70`, `9e05d87c`, `3f19c89b`, `e2a64e9f`, `ce84a759`, and this report's commit.

## Change log

- **2026-10-01, A107:** written.

---

## Orchestrator's critical assessment (protocol §5) — verdict: merge

*Written 2026-10-01 by the orchestrating session. Checked differently from the agent.*

**Checked.** (1) `git diff --name-only 76de5646..2bcc570b`: 18 files, harness, runner, two scripts, the
README and this report — **0 paths under the V5 driver copy `PROCESS/`, 0 under `process/models/`, 0 under
`_v4/`; `paper_tables.md` not in the diff** (byte-identical, as the brief required); worktree clean;
`merge-tree`: no conflict; the harness compiles. (2) The layout on disk is what the user asked for:
`runs/census_tau1e-08/` and `runs/write_set_tau1e-06/` side by side, each self-contained, the two caches
shared at the top. (3) **The adoption changed no campaign record**, checked by the orchestrator against the
archive made before this task: the SHA-256 of all 553 campaign `metrics.json` under
`census_tau1e-08/campaign/` equals that of `A105_runs/…/campaign/`, file for file. (4) The write-set folder
holds no campaign record (144 records: the smoke's and the copied read-only ones) — no campaign was run,
as briefed.

**Read against the user's words.** "I presume data will be stored under …\runs\<some run ID>": yes, and the
ID is the settings key, readable from the folder name. "No need to build comparison of runs into the
harness": none was built. The copy of the read-only records into a new run ID (469 MB each) rather than a
shared area is the choice that keeps "self-contained" true and the job identities untouched; its cost is
disk, which is not scarce here.

**What the next task inherits** (the report's point 8, accepted as stated): in a fresh run ID the tally's
contract gate fails until campaign records exist (the reproduction gate's copied records are of an older
record contract — I-35's shape, cleared by the campaign's presence as before); gate GT refuses under the
fallback by design; G1 and the warm-up gate read archives made under census settings and return their own
verdict under the write set; the supplementary st stage is the census campaign's and is not carried over.
`census_tau1e-08` holds 14 smoke records of earlier tasks made under other settings, in no published
population.
