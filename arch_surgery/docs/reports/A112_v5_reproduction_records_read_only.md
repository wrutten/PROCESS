# A112 (v5-reproduction-records-read-only): the reproduction gate's records as a read-only archive (I-41)

> **Document status**: **OPEN (task report, awaiting the orchestrator's assessment).** Task A112, branch
> `A112-v5-reproduction-records-read-only`, worktree `.claude/worktrees/A112-v5-reproduction-records-read-only`, from trunk
> `ab576660`, 2026-10-01. Harness only. Nothing changed in the driver copy (`MDA_partitioning_experiment_v5/PROCESS/`),
> in `process/` or in V4.
>
> **Commits:**
> - Code: `c412bbdb`. Committed before any record was written.
> - Survey fix: `bd431aec`. It changes only the `--archive-collisions` printout. No gate reads it.
> - Tables documents: `4eff9b4b`.
> - README and this report: the tip.
>
> **Where the numbers come from.** Every gate verdict and stage record was made at `c412bbdb` on a clean tree. The
> collision survey and the tables documents were made at `bd431aec`.
>
> **Press logs:** `runs/census_tau1e-08/_press_logs/A112/` and `runs/write_set_tau1e-06/_press_logs/A112/`. Each folder
> holds `pressNN_*.log`, `disk_log.txt`, `START_MARKER` and `archive_collisions.json`. `runs/` was left in place, and no
> records tree was copied wholesale.
>
> **Disk.** C: had 135 GB free at the start (14:19) and 135 GB free at the end.

## 1. Verdict

**Fixed.** `tally_contracts` now reproduces **236 of 236** reference cells under both run IDs. It reads GR's twenty
runs from GR's read-only archive. No press can write into that archive.

G6 is unchanged under the write set: **PASS, 0 of 6 717, 3/3 teeth**. It still reads its own records made by
today's driver at `52ea57be`.

| run ID | gate table (`--measure gate_table --resume`) | teeth |
|---|---|---|
| `census_tau1e-08` | **29 PASS of 29** (`press07`) | 181 of 181 (was 180; the new tooth) |
| `write_set_tau1e-06` | **28 PASS, 0 FAIL, 1 not run** (GT, refused by design) (`press15`) | 177 of 181 (GT's 4 not run) |

**How the write set was pressed.** `--gate all --resume --test-set write_set` (`press06`) stopped at GT, which refuses
by design. I then pressed the eight gates after GT one at a time (`press07`–`press14`). GT itself was not changed.

**Runs made.** One PROCESS run under each run ID: G7's stale-run tooth, which re-makes one smoke evaluation on every
press. Every other job was kept under `--resume`.

## 2. The cause, by function and line, against the account in the brief

**What happens, step by step:**

1. **GR's jobs carry V4's identity.** `reproduction.v4_criterion` sets `test_set = write_set`, `tau = 1e-6` and every
   instrument switch to off.
2. **That identity renders the same as a write-set campaign job.** `pool.Job.identity` renders the test set and τ only
   where they differ from V4's (`records.IDENTITY_DEFAULTS_WHEN_ABSENT`). Under `write_set_tau1e-06`, the campaign's
   settings are V4's own. So G6's jobs render exactly like GR's (`gate_entry.pairing_jobs`, composed from
   `reproduction.entry_reference_job`, with timers off for gates). One example is A2 seed 1, entered from the A0 seed-0
   reference's `y_exit.json`. The digests are equal.
3. **Both gates land in the same directory.** `pool.canonical_directory_for` names the pool directory from the identity
   (`gates/_runs/<phase>_<arm>_<cfg>_seed…_gate_<digest16>`). So both gates' jobs have one canonical directory, and
   `pool.directory_for` returns it at **step 1**: the canonical directory holds a record with the same readable identity.
4. **The record is judged incomplete.** `pool.run` calls `_kept`, which calls `why_not_kept`, which calls
   `records.why_not_complete_for`. The copied records lack `campaign_test_set`, `loop_test_sets`, `evaluation_warmup`
   and `evaluation_warmup.agrees`. A109's log shows this: *"re-made: 4 declared field(s) missing"*
   (`write_set_tau1e-06/_press_logs/A109/press03_gate_entry_and_warm.log`).
5. **The record is replaced.** `pool.run` runs `assert_not_another_jobs_record` (same job), then `shutil.rmtree`, then a
   re-run by today's driver.
6. **The reproduction comparison reads the replacement.** `tally_contracts` calls `tally.reference_cells`, which calls
   `reproduction_run_directories`, which calls `reproduction.planned_directories`. That calls `attach_phase_a_entries`,
   which calls `pool.directory_for` and so resolves to the same shared-pool directory. The comparison therefore read
   today's driver's records.

**This matches the account in substance.** Two points differ. Neither one casts doubt on the fix.

- **The resolution was step 1 of `directory_for`, not step 2's by-digest search.** Equal identities give one canonical
  pool directory. The by-digest search (`_record_index`) never came into it.
- **A109's G6 press re-made eight of GR's records, not three:**
  - A0 seed 1 on all three configurations;
  - A2 seed 1 on all three configurations;
  - the A1 seed-0 substitute on `tok` and `lad`.

  All eight are stamped `52ea57be` in the write-set pool. Only the three A2 records show in the tally's cells. The three
  A0 records are among the twenty, but a flat arm's counts do not move under item 5. The A1 substitutes are not among
  the twenty. I restored all eight (§4).

## 3. The design

**GR's records are a separate, read-only archive** at `runs/<run ID>/gates/reproduction/pool_records/`. It holds one
directory per job, under the name the shared pool would give it.

- **Every GR reader names the archive.** `reproduction.attach_phase_a_entries` now reads the reference records from the
  archive and sets each planned job's `outdir` to `archived_directory_for(job)`. The same holds for everything built on
  it:
  - `jobs_read`, `planned_jobs` and `planned_directories`;
  - so `tally_contracts`, `instrument_invariance`, G9's GR reference arms, `--jobs reproduction`, the copy step and the
    run-isolation check.
- **No digest moves.** The entry state each identity names stays the pool's canonical path
  (`phase_a_entry_snapshot`). The archive's records therefore keep their stamped identities, and their digests re-derive.
- **The shared pool is not touched.** It keeps every record it held, and those records belong to whichever gate
  composes them. Under the write set, G6's re-made records stay in G6's canonical directories and are read by G6
  (requirement 3).
- **No unnamed job can resolve into the archive.** The archive lies under a gate's own root, and step 2 skips such
  directories (I-36). `pool.run` also refuses any job whose directory lies in a read-only archive. The new
  `pool.refuse_a_read_only_archive` / `pool.READ_ONLY_ARCHIVES` check runs before anything is kept, removed or made,
  whatever `--resume` says (requirement 1).
- **Making the archive:**
  - `--freeze-reproduction-records [--apply]` builds it from a run ID's own pool. It composes GR's job set the
    pre-A112 way (`jobs_read(from_the_pool=True)`), copies each record file with its mtime, checks each SHA-256, and
    writes `gates/reproduction/pool_records_frozen.json`. It is refused under a run ID whose settings are V4's own.
  - Otherwise, `--copy-archived-records <run ID> --archive reproduction` copies it from another run ID. The `reproduction`
    archive's paths are narrowed to `verdict_at_*.json`, `_teeth/`, `pool_records/` and the freeze record. They no longer
    cover the whole folder, because its `gate.json` is rewritten by every read and would refuse a one-archive copy (as at
    A110).
- **`--archive-collisions`** is a read-only survey of the I-41 class over every declared archive (§8).

**Alternatives I rejected:**

- *An identity field marking a reproduction job.* It changes 27 GR digests, so the archived records' stamped digests
  would no longer re-derive. That means writing into the archive or keeping an alias table.
- *Rendering test set and τ explicitly for every non-GR job at V4's values.* `census_tau1e-08` would stay byte-identical,
  but every digest under the write set would change, including its 553 campaign records. `--jobs campaign` would then
  keep 0.
- *Moving GR's records out of the pool instead of copying them.* GC, G6 and G2 share GR's three A0 seed-0 references.
  They would re-make those references, so the census pool would change.
- *A SHA-256 manifest check inside `tally_contracts`, like `evaluation_warmup`'s.* That changes what the gate checks,
  which is outside this task's licence. The pool's refusal guards the writes instead.

**Files changed** (all under `arch_surgery/MDA_partitioning_experiment_v5/`):

- `harness/core/pool.py`: `REPRODUCTION_ARCHIVE_SUBPATH`, `READ_ONLY_ARCHIVES`, `read_only_archive_of`,
  `refuse_a_read_only_archive`, and the call to it in `run`.
- `harness/gates/reproduction.py`:
  - new: `ARCHIVE_SUBPATH`, `archived_directory_for`, `phase_a_entry_snapshot`;
  - changed: `phase_a_reference_directory`, `attach_phase_a_entries` and `jobs_read` (each takes `from_the_pool`).
- `harness/gates/archived_records.py`: the GR archive's paths, `FREEZE_RECORD`, `freeze_reproduction_records`,
  `freeze_report`, `collisions` and `collisions_report`.
- `harness/gates/gate_resume_identity.py`: the new tooth (§5).
- `harness/gates/registry.py`: the read-once wrapper's description string.
- `experiment_runner.py`: `--freeze-reproduction-records` and `--archive-collisions`.
- `harness/README.md`.
- The two tables documents.

## 4. The restoration

**Census first.** Under `census_tau1e-08` the archive was frozen from the census pool:
`--freeze-reproduction-records --apply` (`census/…/A112/press01`).

- GR's job set is 29 jobs. 27 have a record in the pool; 2 have none (AR on `tok` and `lad`; see §8).
- 353 files (64.6 MB) were copied.
- Stamps on the 27 records: 16 at `d6c246a1`, 8 at `66bfa240`, 3 at `d08e8ab4`.
- The census pool was not written.

**Then the write set**, by the committed copy step:

```
experiment_runner.py --test-set write_set --copy-archived-records census_tau1e-08 --archive reproduction --apply
```

The output is in `write_set/…/A112/press01`, the copy record in `write_set_tau1e-06/archived_records_copied_reproduction.json`.

- 354 files were copied. 2 were already present with the same bytes (`verdict_at_d6c246a1.json`, `_teeth/`).
- GR's job set then resolves the same way under both run IDs. Each has 29 jobs and `--resume` keeps the same 3. Jobs that
  resolve or decide differently: **0**. Agreement: **YES**.

**What this restores.** The write-set archive now holds the census originals of all eight records today's driver had
re-made. For example, A2 seed 1 reads 13 / 13 / 15 sweeps and 60 / 60 / 62 node calls, stamped `66bfa240`.

**G6's eight records** stay where they were, in the write-set shared pool (`gates/_runs/…`, stamped `52ea57be`; 14 / 14 / 16
sweeps). They are G6's records, read by G6. Nothing was deleted or moved. The permission system refused nothing.

## 5. The new tooth

The tooth is **`resume_identity` tooth 15: "an archived reproduction record is never re-made"**
(`gate_resume_identity.an_archived_reproduction_record_is_never_re_made`).

**Set-up.** A scratch run ID at V4's settings. A GR-style record (AR seed 0) sits in the archive with one declared field
removed: incomplete under today's contract, as the copied records were at A109.

It requires all of the following:

- **(a)** Another gate's unnamed job of the same digest resolves to its canonical pool directory.
- **(b)** A resumed `pool.run` naming the archived directory is refused by `PoolError` before anything is removed, and
  the archived bytes are unchanged.
- **(c), the controls:**
  - the resume decision on that record says *"1 declared field(s) missing: record_format"*, so the refusal is not
    vacuous;
  - the pool directory is not refused.

It tripped under both run IDs: `resume_identity` reads 15/15 in each.

**Does the tooth bite?** I checked this by inspection, outside any committed script. With
`pool.refuse_a_read_only_archive` patched to a pass-through and `subprocess.run` stubbed, the tooth reads **not
caught**: the archived record was removed ("the archived bytes CHANGED"). That is I-41's shape.

## 6. The four gates under both settings (pressed individually, `press02`–`press05`)

| gate | census_tau1e-08 | write_set_tau1e-06 |
|---|---|---|
| `tally_contracts` | PASS, 0 of 538 (302 + 236 reference cells), 18/18. Read 573 records: 553 campaign + 20 GR (14 at `d6c246a1`, 6 at `66bfa240`) | **PASS, 0 of 538 (236 of 236 cells)**, 18/18. Read 553 campaign at `a1db0a0c` + 20 GR (14 at `d6c246a1`, 6 at `66bfa240`). Was FAIL 9 of 538 at A110 |
| `entry_and_warm` (G6) | PASS, 0 of 6 717, 3/3. 19 records (16 at `d08e8ab4`, 3 at `ff9e73a2`) | **PASS, 0 of 6 717, 3/3**. 19 records (**16 at `52ea57be`**, its own; 3 at `d08e8ab4`) |
| `reproduction` (GR, read-once) | PASS, 0 of 256, 8/8. 27 archived records (16 at `d6c246a1`, 8 at `66bfa240`, 3 at `d08e8ab4`) | PASS, 0 of 256, 8/8, the same 27 |
| `resume_identity` | PASS, 0 of 1 251, **15/15** | PASS, 0 of 850, **15/15** |

The values were the same in the `--gate all` presses and the gate tables.

## 7. Tables documents, campaigns, and what else changed

**Tables documents.** `--paper-tables write` changed only the verification table's stamp line and gate rows:

- `paper_tables.md`: 7 lines out, 7 in;
- the write-set document: 6 out, 6 in.

All rows were re-dated to `c412bbdb`. Counts and verdicts are unchanged, and **no result cell moved**. The cross-check
against the stage records read 0 of 178 under each setting, and LaTeX against Markdown read 0 of 258.
`--paper-tables check` reads **IDENTICAL** under both settings at `4eff9b4b` (`press10` and `press20`).

**Both campaigns are untouched:**

| check | census_tau1e-08 | write_set_tau1e-06 |
|---|---|---|
| `--jobs campaign --resume` | 553 of 553 kept, 0 run (`press11`) | 553 of 553 kept, 0 run (`press21`) |
| files under `campaign/` newer than `START_MARKER` (inspection, `find -newer`) | 0 of 7 348 | 0 of 7 308 |

**What changed in `census_tau1e-08`** (inspection): beyond the re-pressed gates' verdict and stage records, it gained
`gates/reproduction/pool_records/` (27 records) and `pool_records_frozen.json`. In `gates/_runs/`, the only new or
changed files are G7's tooth record `A_AR_st_regression_seed000_smoke_f5b7e5e33d7d55a9` (11 files). No other pool record
changed.

**The write set** shows the same, plus the copy record.

## 8. Decisions, limits, the unexpected

**Decisions taken alone, each with its reversal.**

1. **I restored all eight re-made GR records, not three.** I did it by copying the whole census archive (27 records). The
   five beyond the brief's three are the same defect.
   Reversal: delete `write_set_tau1e-06/gates/reproduction/pool_records/` and the copy record.
2. **The archive is a copy, and the pool keeps its records.** This keeps the census pool unchanged and leaves shared
   records to the gates that share them.
   Reversal: none needed. The archive can be deleted and readers pointed back at the pool by reverting
   `attach_phase_a_entries`.
3. **The freeze is refused at V4's settings.** Reversal: remove `_settings_are_v4s`'s check.
4. **The copy step's GR archive no longer copies `gates/reproduction/gate.json`.** The read-once wrapper reads
   `verdict_at_d6c246a1.json`. Reversal: restore `paths=("gates/reproduction",)`.
5. **GR's own `stage()` was left unchanged.** It is unreachable through the registry: `_run_once` reads and never calls
   it. Called directly, its planned runs would now be refused by the pool, but its prerequisites (the A0 references)
   would still run in the shared pool.
   Reversal: none; or make `stage()` refuse outright.
6. **`measurement/test_set_smoke.py` still reads GR's B-phase records through the pool.** Their identities carry GR's
   overrides and after-run audit, so no other gate composes them. Reversal: route it through `archived_directory_for`.

**Limits.**

- **The census "originals" are not all copy-commit records.** GR's phase A planned runs and A1 substitutes are stamped
  `66bfa240` (A100's merged tip), and the A0 references `d08e8ab4` (A102). Only the 16 B-phase and AR(st) records are at
  `d6c246a1`. Earlier presses had already re-made them in the census pool. They reproduce V4's cells (236 of 236), and
  the archive freezes them as they were today. It does not recover the copy commit's own phase A records, which no
  longer exist.
- **Nothing re-verifies the archive's bytes on read.** The pool refuses writes made through the pool. A process outside
  the pool, such as a hand `rm` or a log compaction, could still alter it. The freeze record holds every file's SHA-256
  if a later task wants a check.
- **The pool's refusal applies to the reproduction archive alone.**

**The unexpected, checked by `--archive-collisions` (`press17`, `archive_collisions.json` under each run ID).**

What the survey counts: per declared archive, the other gates' declared jobs that carry an archived record's identity,
and whether each resolves into the archived directory. "Makes runs" is a property of the gate, not of the job.

- **GR, both run IDs: 26 other-gate jobs resolve into the archive, and all of them read it.** 20 are `tally_contracts`'
  and 6 are G9's seed-0 reference arms. G9 reads those six and runs only its own; any run into the archive is now
  refused.
  Under the write set, 26 more jobs share GR identities and resolve to the shared pool, as intended. They are G6's 11,
  GT's 9 (GT is refused there), and the A0 references of GC (3) and G2 (3).
  Of the 28 records the survey finds for GR, 27 are in the read-only archive; the 28th is its `_teeth` record.
- **GC (`count_neutrality`) has the same class, unprotected, under the write set only.** 9 jobs of gates that make runs
  resolve into GC's archived pool records: the three A0 seed-0 entry references, composed by G6, G2 and GT. Under census
  the count is 0.
  - **The risk:** these are GC's inputs (entry references), not a compared side. They are flat-arm records, so item 5
    does not move them. But a future record-contract field would let G6 or G2 re-make them under the write set, just as
    G6 re-made GR's.
  - **Not changed here:** it is outside the brief. It can be closed the same way, with a GC archive added to
    `READ_ONLY_ARCHIVES`.
- **G1 (`switch_neutrality`): 0 jobs resolve into its captures under either run ID.** GR's three AR jobs share capture
  identities but resolve elsewhere (I-36).
- **Warm-up gate: 0 under either run ID.**
- **Derived input files: no records.**
- **No campaign, smoke, timing or supplementary job can carry an archived gate record's identity.** `run_kind` is an
  identity field. The archived records' run kinds are all `gate`, except the warm-up gate's 11 `timing` records (its
  cold side), which no gate composes.
- **GR's AR substitutes on `tok` and `lad` have no record under census.** Under the write set, before this change, they
  resolved by digest to `input_files/<configuration>/baseline_evaluation`, the derive-inputs stage's named record at
  `a1db0a0c`, which has the same identity. They now resolve to absent archive directories under both run IDs. That is
  consistent between the two, and GR's recorded verdict is unaffected.

**Hand-back state.** The records tree is the one V5 tree, left in place at
`arch_surgery/MDA_partitioning_experiment_v5/runs/`. The queue and the paper were not edited.
