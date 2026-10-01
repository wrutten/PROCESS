# A109 (v5-write-set-gates) — the ten gates not yet pressed under run ID `write_set_tau1e-06`

> **Document status** — **MERGED 2026-10-01 at `cff49790` (`--no-ff`; the orchestrator's assessment at the end); archived.** The one V5 records tree moved on with the next task (A110); after A110's retirement read `arch_surgery/idf_probe/runs/A110_runs/`. Was: **OPEN (task report, awaiting the orchestrator's assessment).** Task A109, branch
> `A109-v5-write-set-gates`, worktree `.claude/worktrees/A109-v5-write-set-gates`, from trunk `52ea57be`, 2026-10-01.
> A run task: no change to the driver copy (`MDA_partitioning_experiment_v5/PROCESS/`), `process/`, V4 or the harness.
> Every number below is printed by `experiment_runner.py` at `52ea57be` (the harness and driver copy are unchanged at
> this branch's tip). The press logs are under `MDA_partitioning_experiment_v5/runs/write_set_tau1e-06/_press_logs/A109/`
> (`pressNN_*.log`, `disk_log.txt`). **`runs/` was left where it is** in this worktree; nothing in it was copied, moved
> or deleted. Gate `evaluation_warmup` was not pressed and keeps A106's recorded FAIL (I-40).

## 1. Verdict: the gate table under `write_set_tau1e-06`

`--measure gate_table --resume --test-set write_set` (`press11_gate_table.log`; record
`runs/write_set_tau1e-06/gates/gate_table/measurements.json`): **26 PASS, 2 FAIL, 1 not run, of 29; 172 of 177 teeth
tripped.** It was 18 PASS, 1 FAIL, 10 not run (A106).

| gate | plan | verdict | compared | mismatched | teeth | made at |
|---|---|---|---:|---:|---|---|
| `g0prime` | G0 | PASS | 77 | 1 (the approved model file) | 4/4 | A106, `a1db0a0c` |
| `copy_identity` | — | PASS | 224 | 8 (declared edits) | 12/12 | A106 |
| `edit_behaviour` | — | PASS | 3 | 0 | 1/1 | A106 |
| `self_containment` | — | PASS | 61 | 0 | 1/1 | A106 |
| `composition` | — | PASS | 53 | 0 | 12/12 | A106 |
| `rungs` | — | PASS | 98 | 0 | 3/3 | A106 |
| `provenance` | — | PASS | 4 | 0 | 4/4 | A106 |
| `data` | — | PASS | 22 | 0 | 6/6 | A106 |
| `run_path` | — | PASS | 12 | 0 | 12/12 | A106 |
| `resume_identity` | — | PASS | 744 | 0 | 14/14 | A106 |
| `capability` | — | PASS | 61 | 0 | 5/5 | A106 |
| `artifacts_check` | — | PASS | 119 | 0 | 3/3 | A106 |
| `artifacts_derive_inputs` | — | PASS | 2 | 0 | 4/4 | A106 |
| `artifacts_census` | — | PASS | 81 | 0 | 5/5 | A106 |
| `artifacts_per_run` | — | PASS | 16 | 0 | 2/2 | A106 |
| `evaluation_warmup` | — | **FAIL** | 19 880 | 2 256 | 1/2 | A106 (not re-pressed; I-40) |
| `record_completeness` | G7 | PASS | 281 | 0 | 14/14 | **A109**, `52ea57be` |
| `count_neutrality` | GC | PASS | 50 114 | 0 | 4/4 | A107 (archived straddle) |
| `prime_map` | G2 | PASS | 17 591 | 0 | 3/3 | **A109** |
| `entry_and_warm` | G6 | PASS | 6 717 | 0 | 3/3 | **A109** |
| `test_set` | GT | **NOT RUN** (refused) | — | — | —/4 | **A109** (refused, no verdict record) |
| `switch_composition` | G5 | PASS | 156 | 0 | 4/4 | **A109** |
| `switch_neutrality` | G1 | **FAIL** | 54 970 | 3 | 9/9 | **A109** |
| `reproduction` | GR | PASS | 256 | 0 | 8/8 | read-once, `d6c246a1` |
| `output_path` | G9 | PASS | 3 879 | 0 | 4/4 | **A109** |
| `written_file_gap` | — | PASS | 42 | 0 | 4/4 | **A109** |
| `tally_contracts` | — | PASS | 538 | 0 | 18/18 | A106 (campaign press) |
| `run_kind_separation` | — | PASS | 1 871 | 0 | 7/7 | **A109** |
| `stage_provenance` | — | PASS | 13 | 0 | 5/5 | **A109** |

The five teeth not tripped: `evaluation_warmup`'s "a doctored count on one record" (A106 §7) and GT's four (not run).

## 2. The ten gates pressed here

Each was pressed alone, in the brief's order, with
`HARNESS_WORKERS=3 PYTHONDONTWRITEBYTECODE=1 …/PROCESS_surgery_env/bin/python experiment_runner.py --test-set write_set --gate <name> --resume`,
13:28–13:36. Each gate's job list was printed first with `--jobs <name> --test-set write_set --resume` (`press00_jobs_<gate>_before.log`).
"Made" counts the runs the press launched; "kept" the records `--resume` kept.

| # | gate | made | kept | verdict | numbers | log |
|---|---|---:|---:|---|---|---|
| 01 | `record_completeness` (G7) | 3 + 1 | 0 + 1 | PASS | 3 runs on `st` (one under rule `epsvmc_times_epsfcn` at τ 1e-12); 281 compared, 0 mismatched; 14/14 teeth. The "+1": its stale-run tooth keeps one record with `--resume` and re-makes it without | `press01_gate_record_completeness.log` |
| 02 | `prime_map` (G2) | 12 | 3 | PASS | (i) 6 pairs, 12 evaluations, 5 026 components, 0 differing; (ii) GC's DR9/DR10 straddle, 6 pairs, 12 565 components, 0 differing; 3/3 teeth. Read 12 records at `52ea57be` and 3 at `d08e8ab4` | `press02_gate_prime_map.log` |
| 03 | `entry_and_warm` (G6) | 16 | 3 | PASS | 8 entry pairs at seed 1, 5 warm runs, 16 evaluations; 6 717 compared, 0 mismatched; 3/3 teeth | `press03_gate_entry_and_warm.log` |
| 04 | `test_set` (GT) | 0 | 0 | **REFUSED** (rc 3) | refused before any run; no verdict record written | `press04_gate_test_set.log` |
| 05 | `switch_composition` (G5) | 6 | 0 | PASS | 3 configurations, 6 optimisations, 42 switch names and 10 run values each; 156 compared, 0 mismatched; 4/4 teeth | `press05_gate_switch_composition.log` |
| 06 | `switch_neutrality` (G1) | 6 | 0 | **FAIL** (rc 1) | straddle `9ed0da4c → 52ea57be`, 6 pairs; 3 651 record values and 51 319 MFILE lines compared; **3 values differ, 0 lines differ**; 9/9 teeth | `press06_gate_switch_neutrality.log` |
| 07 | `output_path` (G9) | 11 | 0 | PASS | 11 runs at seed 0; 3 879 compared, 0 mismatched; 4/4 teeth. Read 11 records at `52ea57be` and 6 at `d6c246a1` (GR's) | `press07_gate_output_path.log` |
| 08 | `written_file_gap` | 6 | 0 | PASS | 6 runs (BR, B1, B2 × `tok`, `lad`); 42 checks, 0 failed; 4/4 teeth | `press08_gate_written_file_gap.log` |
| 09 | `run_kind_separation` | 0 | — | PASS | 765 run records under the run ID; 553 in the 3 published sources, 31 in the 2 unpublished; 1 871 compared, 0 mismatched; 7/7 teeth | `press09_gate_run_kind_separation.log` |
| 10 | `stage_provenance` | 0 | — | PASS | scratch records broken 4 ways plus census stamping; 13 compared, 0 mismatched; 5/5 teeth | `press10_gate_stage_provenance.log` |

**61 PROCESS runs in all** (60 gate runs plus the G7 tooth's re-make). Every one finished `status = ok`.

A106's estimate of about 650 jobs was mostly `run_kind_separation`'s listing. Its `--jobs` printout names the campaign's 553
jobs, each marked `RUN` because the listing composes them without the campaign's timers. The gate itself is
`needs_runs=False` and its body (`harness/chain.py:1216`, `separation_body`) only reads `metrics.json`. I read that code
before pressing it. It made no run, and the campaign records are untouched (§5).

## 3. The gates that did not PASS

### `test_set` (GT): refused, by design

`gate_test_set.test_set_body` (`harness/gates/gate_test_set.py:342–348`) raises `GateError` before any run when
`campaign.test_set != "census"`. The message: *"binds the census test set and the campaign composes 'write_set': under
the fallback (D39) the loops test the write set and there is no census set to drop a component from. Press it with
--test-set census."* No verdict record is written, so the gate table reads NOT RUN (—/4 teeth) and the verification
table reads "not pressed". **This is the gate's construction (README §5, "Refused under the fallback").** It says
nothing about this campaign's records.

### `switch_neutrality` (G1): FAIL on one absolute-path leaf (trap T20)

**What it compared.**
- The "before" side is the archived capture at `9ed0da4c`, which A107 copied into this run ID. It was made in A101's
  worktree (`.claude/worktrees/A101-v5-timers-and-once/`).
- The "after" side was made now at `52ea57be`, in this worktree.
- Both sides are AR and BR on each configuration, with every architecture switch unset.

**The numbers.**
- 3 651 record values and 51 319 MFILE lines were compared; 1 737 values and 45 lines were excluded by name.
- **3 values differ**, one on each BR pair; 0 MFILE lines differ; the three AR pairs pass.
- The one leaf is `audit_snapshot.coupling_state`. It is the absolute path of the committed coupling-state artifact:
  `…/worktrees/A101-v5-timers-and-once/…/harness/data/coupling_state_<configuration>.json` before,
  `…/worktrees/A109-v5-write-set-gates/…/harness/data/coupling_state_<configuration>.json` after.

**The cause, by line.**
- `harness/gates/gate_neutrality.py:83–130` (`ALWAYS_EXCLUDED`) declares the cross-tree path leaves. Its group "the
  cross-tree paths" names `exit_audit.coupling_state`, `coupling_state_artifact` and `coupling_state_provenance.path`,
  but not `audit_snapshot.coupling_state`.
- `audit_snapshot` appears only in the conditional group (line 321). That group excludes a field only where one side
  lacks it. Both captures carry the block, so its path leaf is compared verbatim.
- Under `census_tau1e-08` the gate PASSed because both captures were made in A101's tree (before at `9ed0da4c`, after at
  `24b78e2d`, read from the two records). The path agreed only because both sides were in the same place. This is the
  same class as T20 (GC's `defer_per_run_totals.artifact`, A100).

**Whose cause.** The gate's construction. A path leaf is missing from its declared path table, and this is the first
press where the two sides were made in two different trees. It is not this campaign's records, and not the run ID: G1's
arms (AR, BR) compose no test set, and every behavioural value and output line is identical across the straddle.

**An inference I did not test:** any re-press of G1 outside A101's tree would FAIL the same way, under either run ID.

No exclusion was added, and the gate was not re-pressed.

### `evaluation_warmup`: FAIL, kept from A106

Not pressed, per the brief. Its record is A106's: 2 256 of 19 880 mismatched, 1/2 teeth. Its cause is the gate's
construction under a non-default run ID (I-40; A106 §7).

## 4. The tables document

`--paper-tables write --test-set write_set` (`press12_paper_tables_write.log`) gives a cross-check of 0 mismatched of
178. It was committed at `770082a7`. `--paper-tables check --test-set write_set` (`press13_paper_tables_check.log`)
reads **IDENTICAL**.

**Diff extent** (`git diff` before the commit): 1 file, 5 insertions and 5 deletions. All of them are in the
verification table:
- the stamp line: *"read 19 record(s) at [a1db0a0c, ce84a759]"* became *"read 28 record(s) at [52ea57be, a1db0a0c,
  ce84a759]"*;
- the G1, G6, G5 and G9 rows changed from "not pressed".

No other line moved.

**The verification table as it now reads** (`paper_tables_write_set_tau1e-06.md`):

| check | plan | verdict |
|---|---|---|
| physics frozen | G0 | PASS (`g0prime` at `a1db0a0c`: 1 of 77; 4/4) |
| switch neutrality | G1 | **FAIL** (`switch_neutrality` at `52ea57be`: 3 of 54 970; 9/9) |
| matched accuracy | A1 | PASS on `tok`, `lad`, `st` |
| fixed-point distance | A2 | reported, no rule |
| same optimum | B1 | PASS tok, st · FAIL lad |
| entry pairing | G6 | PASS (0 of 6 717; 3/3) |
| arm composition | G5 | PASS (0 of 156; 4/4) |
| output-path equivalence | G9 | PASS (0 of 3 879; 4/4) |
| the test set's teeth | GT | not pressed (refused under the fallback) |

The G1 FAIL in this table is a path in a record, not behaviour (§3). Until the orchestrator rules on it, the document
should not be cited as verified on G1.

## 5. Both campaigns are untouched

| check | log | result |
|---|---|---|
| `--jobs campaign --resume` (default, `census_tau1e-08`) | `press14_census_jobs_campaign.log` | 553 of 553 kept, run 0 |
| `--paper-tables check` (default) | `press15_census_paper_tables_check.log` | `paper_tables.md`: IDENTICAL |
| `--jobs campaign --test-set write_set --resume` | `press16_write_set_jobs_campaign.log` | 553 of 553 kept, run 0 |

Also by inspection: `find -newer` against this task's first log finds no file under `runs/census_tau1e-08/` and none
under `runs/write_set_tau1e-06/campaign/` modified during the task.

## 6. Disk, decisions, the unexpected

**Disk** (`disk_log.txt`, `df -h /mnt/c`): 135 GB free at 13:27:27, before every press, at 13:36:25, after the last
press, and at 13:37:41, the end of the task. It read 135 GB, not the brief's ~145 GB, already at the start. It never
approached the 10 GB floor.

**Decisions taken alone.**
1. **The ten presses ran as one background script, one gate at a time**, with a disk check before each (a scratchpad
   wrapper, not committed). Each press is still the brief's exact command with its own log. The script was the
   launcher, not a producer of numbers. Reversal: none needed.
2. **`run_kind_separation` was pressed despite its listing marking 553 campaign jobs `RUN`.** I read
   `chain.separation_body` and `needs_runs=False` first, which showed the gate reads records only. Confirmed by 0 runs
   made and §5. Reversal: none needed.

**The unexpected.**
1. **G1 FAILs on a cross-tree path leaf** (§3). `audit_snapshot.coupling_state` is missing from G1's path table. This is
   the T20 class, and it first showed because this press is the first straddle of G1 across two trees.
2. `run_kind_separation`'s `--jobs` listing reads as if it would re-make the 553 campaign records. That is what inflated
   A106's "about 650 jobs" estimate. The listing is misleading, though the gate is harmless.
3. The census run ID's own G1 verdict (on disk, not re-pressed) says its straddle is *"one capture names no commit, so
   what this run straddles cannot be stated"* (`after_commit: null`), although its after records carry `24b78e2d`. This
   is noted only. It does not change that run ID's PASS, which was made in one tree.

## Orchestrator's critical assessment (protocol §5) — verdict: merge

*Written 2026-10-01 by the orchestrating session. Checked differently from the agent.*

**Checked.** (1) `git diff --stat 52ea57be..2aa32bb1`: two files, the tables document and this report; no code. The
tables document's diff is five lines out and five in, all in the verification table (the stamp line and the G1, G6,
G5, G9 rows); no cell of a result table moved. (2) Gate G1's record, read by the orchestrator
(`runs/write_set_tau1e-06/gates/switch_neutrality/gate.json`): 3 651 values and 51 319 output-file lines compared, 3
values differing, 0 lines; the three mismatches are one field, `audit_snapshot.coupling_state`, on runs 0, 2 and 4.
(3) `--runs` reads 26 PASS, 2 FAIL, 1 not run for `write_set_tau1e-06`; `--paper-tables check` reads IDENTICAL under
the write set and under the default settings. (4) No file under either run ID's `campaign/` has a modification time
after the task began.

**The G1 FAIL is a path, and the remedy is the gate's own table.** `ALWAYS_EXCLUDED` in `gate_neutrality.py` already
names the sibling leaves `exit_audit.coupling_state`, `coupling_state_artifact` and `coupling_state_provenance.path` as
absolute paths whose file is compared by content (`components_sha256`). `audit_snapshot.coupling_state` is the same
path under a block added later, and it agreed until now only because both captures were made in one tree (trap T20).
Naming it in that table is a correction of an omission, not a change to what the gate compares in behaviour. Decided
by the orchestrator as an implementation matter, carried by A110 with the gate re-pressed; reversal: remove the entry.
Until then the tables document's G1 row reads FAIL and the document is not to be cited as verified on G1.

**The agent's inference, accepted as stated and untested:** a re-press of G1 outside A101's tree would fail the same
way under the default run ID. A110 re-presses it under both.
