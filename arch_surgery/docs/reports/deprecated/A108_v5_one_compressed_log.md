# A108 (v5-one-compressed-log) — one PROCESS log per run folder, compressed

> **Document status** — **MERGED 2026-10-01 at `0e676a1c` (`--no-ff`; the orchestrator's assessment at the end); archived.** The records tree was not relocated to `idf_probe/runs/`: it exists once and was **moved** (I-39) into the next task's worktree, and, at A106's retirement, on to `arch_surgery/idf_probe/runs/A106_runs/`; the paths in this report that begin `runs/` are read from there. Was: **OPEN (task report, awaiting the orchestrator's assessment).** Task A108, branch
> `A108-v5-one-compressed-log`, 2026-10-01, from `e9decb5c`. Harness only (`arch_surgery/MDA_partitioning_experiment_v5/`,
> nothing under its `PROCESS/`, nothing under `process/models/`). Every number below comes from a committed entry point,
> `experiment_runner.py`, at the commit named beside it. The press logs are under
> `runs/census_tau1e-08/_press_logs/log_compaction_*` in this worktree's V5 folder. **`runs/` was left where it is**
> for the orchestrator to relocate by `mv`.

## 1. Verdict

**Done, and applied to both run IDs.** The V5 records tree went from **8.28 GB to 2.78 GB** for `census_tau1e-08`
(its campaign from 3.64 GB to 1.20 GB) and from **0.51 GB to 0.30 GB** for `write_set_tau1e-06` (`--runs`; size on disk).
The PROCESS logs went from **5 821.1 MB to 112.4 MB**: 1 321 run folders, every one compacted, none left. The two
plain logs were byte-identical in every one of the 1 321 folders.

- **New runs.** The pool's close-out now leaves each run folder with one `process.log.gz`. Two smoke runs on
  `st_regression` (one phase A evaluation, one phase B optimisation) each hold one `process.log.gz` and no plain log.
  Each record is complete, and the reader reads the log back: 62 lines and 46 166 lines.
- **Existing records unchanged.** The campaign resumes **553 of 553** before and after the compaction (`--jobs campaign`).
  Every `metrics.json` has the same SHA-256 before and after: 1 175 of 1 175 in `census_tau1e-08` and 144 of 144 in
  `write_set_tau1e-06`, 0 differing. All 20 crashed campaign records still read their traceback line after compaction.
- **Checks.**
  - `--selfcheck` PASS, including a new `process log` check with 4 teeth.
  - Three gates re-pressed with `--resume`: `resume_identity`, `record_completeness` (once) and `run_kind_separation`, all PASS.
  - `--measure gate_table --resume`: **29 PASS, 0 FAIL, 177 of 177 teeth**.
  - `--paper-tables check`: **IDENTICAL**, after a re-render that moved only the stamp line of the verification table (§7).

## 2. Where the two logs came from

**Both files come from PROCESS. Neither comes from the harness.** Both are written in `PROCESS/process/main.py`, which I
read only:

| file | written by |
|---|---|
| `process.log` | `logging_file_handler = logging.FileHandler("process.log", mode="a")` at module level (line 979). It is opened relative to the **working directory** when `process.main` is imported. The pool starts every child with `cwd=<run folder>`. |
| `<configuration>.process.log` | `setup_loggers(Path(self.output_path…replace("OUT.DAT", "process.log")))` in `SingleRun.initialise` (line 427). It adds a second `FileHandler` at the output prefix, `mode="w"` (line 1011). |

Both handlers sit on the same logger at the same level (INFO) with the same formatter. So the two files are identical
whenever nothing is logged between the import and `initialise`. On disk that held for 1 321 of 1 321 folders.

To avoid the second file, the harness would have to change PROCESS's logging set-up: a driver change, or a child that
detaches PROCESS's handler. Neither was made. Instead the harness's close-out **verifies the pair identical and
removes the duplicate**, as the brief allowed.

## 3. What a new run folder holds

The folder holds `metrics.json`, `command.json`, `stdout.log`, `stderr.log`, the input file, `OUT.DAT` and `MFILE.DAT`,
and the state snapshots, all as before. PROCESS's log is now **one `process.log.gz`**. Neither plain file remains.

The close-out (`pool.run` → `process_log.close_out`) runs **after** `stamp_identity` and after the record is read back.
It does not read or write any field of `metrics.json`. It does five things, in order:

1. Verify the plain pair byte-identical by SHA-256.
2. Write `process.log.gz.partial`: gzip level 6, no file name and a zero time in the header, so the same log always
   compresses to the same bytes. Then fsync it.
3. Verify that it decompresses to the plain SHA-256 and length.
4. Rename it into place as `process.log.gz`.
5. Remove both plain files.

If the pair differs, the folder is left as it is and the pool prints a line. Nothing is removed whose content the kept
file does not hold.

The evidence is two `--run` smoke runs at `06db785c`, on `st_regression`, run kind `smoke`, under `census_tau1e-08`.
`df -h /mnt/c` showed 8.4 GB free before them.

| run | folder (`runs/census_tau1e-08/single/st_regression/…`) | log files | record | read back |
|---|---|---|---|---|
| A0, seed 1, perturbed (phase A) | `A0/census_tau1e-08/seed001/` | `process.log.gz` only, 894 B | contract complete, status ok | 62 lines |
| BR, seed 0 (phase B) | `BR/census_tau1e-08/seed000/` | `process.log.gz` only, 128 245 B | contract complete, status ok, ifail 1 | 46 166 lines |

`record_completeness`'s tooth also made one new pool run, `gates/_runs/A_AR_st_regression_seed000_smoke_…`. It too holds
`process.log.gz` only. After all presses, `find runs -name '*process.log'` finds **0** files.

## 4. The readers, and the record contract

**No harness code read PROCESS's log before this task, and none had to change.** I searched for `process.log`, `.log`,
`traceback` and every file a run folder is read for. The failure taxonomy's detail — `stats.traceback_last_line`,
`records.traceback_last_line` — reads the record's own `traceback` field. The child writes that field from the
exception it caught; it does not come from the log. The other files read from run folders are `MFILE.DAT`, `y_exit.json`
and `audit_residual.json`. The only `.log` writes in the harness are the pool's `stdout.log` and `stderr.log`, which are
untouched.

What was added:

- **`harness/core/process_log.py`.**
  - `FORMS` lists the forms a log can take: `compressed`, `plain pair`, `plain single`, `none`.
  - `form_of(directory)` says which form a folder holds.
  - `open_text(directory)` is **the one reader**. It reads every form: the compressed file first, then `process.log`,
    then `<configuration>.process.log`.
  - `compact` and `close_out` do the work.
  - The module docstring says where the two files come from.
- **The record contract** (`records.py` docstring) names the forms. **Every form is valid for a complete record**,
  because no record field is derived from the log. A record made before this change is therefore complete and kept,
  as before. The form is read from the folder; nothing about it is stamped into `metrics.json` (decision 2).
- **`--run`'s report** now prints the folder's log form and reads the log back through `open_text`. That is the reader
  the smoke evidence in §3 shows.

## 5. The compaction command

`experiment_runner.py --compact-run-logs [<run ID>]` covers every run ID when none is named. It is a dry run unless
`--apply` is given (`run_layout.compact_process_logs`). It runs before the run-ID guard, like `--runs` and the adoption.
It walks every folder under the run ID that holds a log in any form.

For each folder:

- **Both plain files present:** compare them by SHA-256. If they differ, the folder is left and listed. Otherwise
  compress one, verify the round trip and rename into place, then remove the plain files.
- **One plain file:** compressed the same way.
- **`process.log.gz` alone:** skipped (`already compacted`).
- **`process.log.gz` beside a plain file:** this is an interrupted compaction. If the compressed file decompresses to
  each plain file's SHA-256, the plain files are removed (`finished`). Otherwise the folder is left and listed.
- **A leftover `process.log.gz.partial`:** removed first. It is never a finished file.

**The dry run** measures each folder's size after by compressing the log into a counting sink, so it writes nothing to
disk. **With `--apply`**, the command also:

- digests every `metrics.json` of the run ID before and after and reports the number that differ;
- reads back the traceback line of every crashed record in a compacted folder;
- appends the whole record to `runs/<run ID>/process_log_compaction.json`.

The exit status is 1 if any folder was left or any record changed.

The command touches only `process.log`, `*.process.log`, `process.log.gz` and `process.log.gz.partial`.

**Dry run** at `f8538480` (`log_compaction_dry_run.txt` / `.json`):

| run ID | folders with a PROCESS log | outcome | log bytes now | log bytes after |
|---|---|---|---|---|
| `census_tau1e-08` | 1 178 | would compact 1 178 | 5 612.6 MB | 108.8 MB |
| `write_set_tau1e-06` | 143 | would compact 143 | 208.5 MB | 3.6 MB |
| total | 1 321 | | 5 821.1 MB | 112.4 MB |

**Applied** at `f8538480` (`log_compaction_apply.txt` / `.json`). The permission system allowed the removals.

| run ID | compacted | left | log bytes before → after | `metrics.json` by SHA-256 before / after / differing | crashed records: traceback line read |
|---|---|---|---|---|---|
| `census_tau1e-08` | 1 178 | 0 | 5 612.6 → 108.8 MB | 1 175 / 1 175 / 0 | 20 of 20 |
| `write_set_tau1e-06` | 143 | 0 | 208.5 → 3.6 MB | 144 / 144 / 0 | 0 of 0 |

- **Folders skipped:** none. Every folder held an identical plain pair; there were no `already compacted`, `left` or
  partial cases.
- **Crashed-record example:** a compacted crashed campaign record reads
  `RuntimeError: Failed to converge after 50 iterations, value is nan.` with log form `compressed`.
- **Size on disk** (`--runs`):
  - `census_tau1e-08`: 8.28 GB → 2.78 GB; its `campaign/`: 3.64 GB → 1.20 GB.
  - `write_set_tau1e-06`: 0.51 GB → 0.30 GB.
- **Host disk:** C: still shows 8.4 GB free. The WSL virtual disk does not shrink until it is compacted; the space
  freed inside it is reused by later writes.

The "before" `--runs` listing was printed by the working tree one minute before the identical code was committed as
`21a18834` (the commit added nothing else). The "after" listing ran at `f8538480`
(`log_compaction_runs_after.txt`).

## 6. The listing

`--runs` now prints, for each run ID, `size on disk: X GB, of which the campaign (campaign/) Y GB`
(`run_layout.disk_bytes`). It counts allocated blocks, as `du` does, and counts each hard-linked file once.

## 7. Checks

| check | at | result |
|---|---|---|
| `--jobs campaign`, `census_tau1e-08`, before compaction | `f8538480` | 553 distinct jobs, `--resume` keeps **553**, runs 0 |
| the same after compaction | `f8538480` | keeps **553**, runs 0 |
| every `metrics.json` SHA-256 before and after (inside `--apply`) | `f8538480` | 1 175/1 175 and 144/144, **0 differing** |
| a crashed record's traceback line from a compacted folder | `f8538480` | 20 of 20 crashed campaign records (in `--apply`); selfcheck's synthetic crashed record in a compacted folder |
| new-run evidence: 2 smoke runs (§3) | `06db785c` | `process.log.gz` only; contracts complete; read back |
| `--selfcheck` (with the capability probe) | `06db785c` | **PASS**, 8 checks; `process log`: 3 compared, 0 mismatched, **4 of 4 teeth tripped** — the plain pair differs (left untouched); interrupted between the rename and the removals (finished); a partial file (removed, then compacted); a compressed file that does not hold its plain log (left) |
| `--gate resume_identity --resume` | `06db785c` | PASS |
| `--gate record_completeness --resume` (pressed once) | `06db785c` | PASS |
| `--gate run_kind_separation --resume` | `06db785c` | PASS (read 553 records, made at `6221af70` and `f4a75f8e`) |
| `--measure gate_table --resume` | `06db785c` | **29 PASS, 0 FAIL, 0 not run; 177 of 177 teeth tripped** |
| `--paper-tables check` | `06db785c` | first press: **REFUSED** — the document did not match. `--paper-tables show` diffed against the file: **one line**, line 437, the verification table's stamp line (*"the gate_table stage record read 30 record(s) at […]"*). Its commit list gained `06db785c` (the three re-pressed gates) and lost `d218b879`. Re-rendered with `write`; `check` then reads **IDENTICAL**. Committed as `3afe3b32` |

Why these three gates: the change touches `pool.run`, which every gate's runs go through; `run_layout`, which the
run-ID guard and the resume search use; and nothing a gate compares. `resume_identity` binds the keep decision.
`record_completeness` makes a new run through the close-out. `run_kind_separation` reads the campaign's records.

## 8. Decisions taken alone, with reversals

1. **The duplicate is removed in the close-out, not avoided.** Avoiding it means changing PROCESS's logging
   (`process/main.py`): either the driver, or a child that removes PROCESS's handler. The brief ruled that out.
   *Reversal:* a driver change that drops the module-level handler. The close-out would then compress a single file,
   with no other change.
2. **The log form is not stamped into `metrics.json`.** It is read from the folder (`process_log.form_of`), and the
   contract declares every form valid. A stamp would mean rewriting `metrics.json` after the record is assembled. It
   would also add a field that the neutrality gates' record comparisons would have to classify, and the compaction
   could not stamp existing records without changing them. *Reversal:* the close-out adds a `process_log` block
   (form, SHA-256 of the plain log) in `stamp_identity`'s write, and G1's exclusion table names it.
3. **A plain pair that differs is left as two plain files**, in a new run and in the compaction, and printed or listed.
   Nothing whose content is not kept is removed. It never happened on disk (0 of 1 321).
   *Reversal:* compress both files.
4. **Hidden entries of `runs/` are not "the layout before run IDs"** (`f8538480`, its own commit). The agent
   environment created `runs/.claude/.cc-writes/` (empty) in this worktree at 10:47. `run_layout.legacy_entries` read
   it as a legacy entry, so **every press refused**. It will appear wherever an agent's tools write under `runs/`.
   *Reversal:* revert `f8538480` and remove the directory by hand before each press. I left `runs/.claude/` in place;
   it is not mine to delete.
5. **The compressed file is deterministic** (gzip level 6, empty name, `mtime=0`). The same log always gives the same
   bytes, so two compactions can be compared by digest. *Reversal:* none needed.
6. **`--run`'s report reads the log back** (§4). It is the harness's only use of the reader beyond the compaction and
   the selfcheck. It is the evidence that a reader reads the new form; it is not a gate.
7. **The press logs** use names that say what they hold (`log_compaction_*.txt`), with no task number. They sit in
   `census_tau1e-08/_press_logs/` because the compaction covers both run IDs.

## 9. Limits

- The close-out covers runs made by `pool.run`. That is every PROCESS run that writes a record. The capability probe
  and the driver-asking subprocess of `artifacts.py` run in temporary directories, or write no run folder.
- Records made **before** this task and relocated elsewhere (`arch_surgery/idf_probe/runs/A<n>_runs/…`, V4's trees)
  are not compacted. `--compact-run-logs` acts on this V5 folder's `runs/` only. Compacting another tree would need
  the command pointed at it (not built) or a move into a `runs/`.
- The host disk shows no gain until the WSL virtual disk is compacted (user action, outside the sandbox).
- **Proposal only, nothing done.** A shell inspection of the class sizes, not a published result, finds the largest
  remaining class in `census_tau1e-08` is `<configuration>.MFILE.DAT`, at about 1.34 GB over 1 180 files. It is read
  by `child.py`, `gate_neutrality.py` and `gate_written_file.py`, so compressing it would need those readers changed,
  as here. The next classes are `SIG_TF.json` (about 0.21 GB over 599 files) and `y_exit.json` (about 0.17 GB). The
  two pre-output snapshots `y_before_finalise.json` and `y_entry_to_write_output_files.json` are not redundant: they
  are identical in 60 of 255 campaign optimisation folders.

## 10. Commits

| commit | what |
|---|---|
| `8e61a2b0` | part 1: `process_log.py`, the pool's close-out, the record contract's log forms, selfcheck `process log` |
| `b5b54006` | part 2: `--compact-run-logs [<run ID>]` (`run_layout.compact_process_logs`) |
| `21a18834` | part 3: `--runs` prints each run ID's size and its campaign's |
| `f8538480` | hidden entries of `runs/` are not the old layout (decision 4) |
| `06db785c` | `--run` reports and reads back the log; `harness/README.md` (§4 step 6, §12, §13, change log) |
| `3afe3b32` | `paper_tables.md` re-rendered: the stamp line only |

## Change log

- 2026-10-01 — report written; parts 1–3 committed; compaction applied to both run IDs; checks run.

## Orchestrator's critical assessment (protocol §5) — verdict: merge

*Written 2026-10-01 by the orchestrating session. Checked differently from the agent.*

**Checked.** (1) `git diff --stat e9decb5c..48073c53`: 9 files — the runner, six harness files, `paper_tables.md`
and this report; **0 diff lines under the V5 driver copy `PROCESS/` and under `process/`**; worktree clean; the
harness compiles. (2) `paper_tables.md` differs in **one line**, the verification table's stamp (the commit list of
the gate records the `gate_table` stage read); no cell of any table moved, and `--paper-tables check` at the tip
reads **IDENTICAL**. (3) **Every compressed log is whole**: `gzip -t` over all 1 323 `process.log.gz` under `runs/`
reports 0 failures; 0 plain logs and 0 partial files remain; the header time is zero in the five sampled (the
deterministic form of decision 5). (4) **No record was modified**, checked without the agent's digests: the only
`metrics.json` files with a modification time after the task began are the three runs it made new (the two smoke
runs of §3 and the `record_completeness` tooth's run); the newest campaign record is dated 2026-09-30 12:01, and
there are 553. (5) `--jobs campaign --resume` at the tip: **553 distinct jobs, keeps 553, runs 0**. `--runs` prints
2.78 GB (campaign 1.20 GB) and 0.30 GB.

**The counts reconciled.** 1 323 compressed logs against 1 321 records: four folders hold a log and no record (three
under `single/st_census_exact/` and one under `timing/seed_set/`, runs interrupted before their record was written),
and two records hold no log (the reproduction gate's `missing_key` tooth, a synthetic record); 1 323 − 4 = 1 321 − 2.
The agent's 1 321 compacted folders plus its two smoke runs give 1 323; the tooth's run re-made an existing folder.

**The decisions taken alone**, all accepted. Removing the duplicate in the close-out rather than silencing PROCESS's
handler keeps the driver copy untouched (decision 1). Not stamping the log form into the record (decision 2) is what
lets the compaction leave every existing record byte-identical, which check (4) relies on. A hidden entry of `runs/`
no longer reading as the old layout (decision 4) is right for a reason beyond this worktree: the harness writes no
hidden entry, and the agent environment will create that one wherever an agent's tools write under `runs/`.

**A limit the report does not state.** `process_log_compaction.json` records how many `metrics.json` digests were
compared and how many differed, not the digests themselves, so the before-and-after comparison cannot be repeated
from the record. The evidence that survives is check (4) and the unchanged tables.

**Not taken.** Compressing `MFILE.DAT` (about 1.34 GB in `census_tau1e-08`, three readers to change) is the agent's
proposal and is left for the user; nothing in this merge depends on it.
