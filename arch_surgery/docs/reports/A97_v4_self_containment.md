# A97 (v4-self-containment) — V4's `self_containment` gate: the stale PASS replaced, the one finding removed

> **Document status** — **OPEN.** Task **A97 (v4-self-containment)**, branch `A97-v4-self-containment`
> (worktree `.claude/worktrees/A97-v4-self-containment`), base **`74a59dfb`** (= `architecture_surgery` at
> dispatch), the fix at **`4b0673fd`** — the commit every verdict below was pressed at. Resolves issue **I-32**
> (V4's `self_containment` gate FAILs at the tip while its published gate table says PASS), filed at A94
> (v5-copy)'s merge. Every number in this document was printed by a committed script of
> `arch_surgery/MDA_partitioning_experiment_v4/` — `experiment_runner.py` (`--gate`, `--measure`,
> `--plan-tables`), `report_cells_preserved.py`, `run_stamp_survey.py`, `report_counts_check.py` — or read
> from a record those scripts wrote under the worktree's `runs/`. None was typed from inspection. Records:
> `runs/` is a seeded copy of the latest relocated tree (`../idf_probe/runs/A90_runs/`: `gates/`, `artifacts/`,
> `census/`, `input_files/`, `reference/` as briefed, plus `campaign/` — §6, decision 2); the one record this
> task re-made is `runs/gates/self_containment/gate.json`, the one stage record `runs/gates/gate_table/measurements.json`.
> Paths reading `runs/…` mean the worktree's copy until the retire script relocates it.

## 0. Verdict

- **The FAIL is reproduced from the button.** With A90's records seeded and no `--resume`,
  `experiment_runner.py --gate self_containment` at `74a59dfb` writes a record reading **FAIL**: 53 Python files
  scanned, 53 lines naming either superseded directory, 15 of them executable, **1 finding** —
  `experiment_runner.py:1033`, the `--paper-tables-runs` help-string example
  `"under it), e.g. a retired worktree's idf_probe/runs/A<n>_runs; "`, classified
  `UNCLASSIFIED — a finding`, `executable: true`; 0 imports, 0 stale declarations; the tooth tripped
  (1/1). Record stamped `tree_git_head` `74a59dfb`, generated 2026-09-29T17:39:47.
- **The stale record, and what it hid.** V4's latest record (`A90_runs/gates/self_containment/gate.json`) is a
  PASS stamped `f8147a00` (2026-09-17): 52 files, 49 lines, 14 executable. Between that stamp and the tip the
  population grew by one file and four lines, all from `38d2f21f` ("paper result tables", 2026-09-29):
  three prose (`harness/measurement/paper_tables.py:121`, `:487`; the runner's docstring `:707`) and the
  one executable line. Every `--resume` press since kept the record — the reuse rule's exception (a change that
  alters what a gate reads re-makes its record) was not applied at `38d2f21f`.
- **The fix** (`4b0673fd`, §2): the help-string example reworded so it names no directory. The reference is
  removed, not declared.
- **PASS from scratch**: 53 files, 52 lines naming either directory, 14 executable, **0 findings**, 0 imports,
  0 stale declarations, 53 compared / 0 mismatched, tooth tripped 1/1 (imports 0 → 1, findings 0 → 1,
  passed True → False). Record stamped `4b0673fd`, generated 2026-09-29T17:40:48.
- **The gate table re-made** with `--measure gate_table --resume`: 30 PASS, 0 FAIL, 0 not run, 176 of 176
  teeth; its `records_read` block stamps the new record (`4b0673fd`, digest `bef8d3ed…`).
  `--plan-tables write`, then `check`: **IDENTICAL** (Appendix D 1 332 lines, the companion 1 705, 0 dangling
  references). `report_cells_preserved.py --base 74a59dfb`: **2 003 rows and 21 296 cells compared, 0 missing,
  1 differing — the gate table's `self_containment` row** (population 52 → 53 files, 49 → 52 lines; the
  cells `verdict`, `compared`, `mismatched`, `teeth` unchanged).
- **0 PROCESS runs.** Stamp survey before and after: 1 102 run records, 0 whose commit changed, 0 new,
  0 disappeared. The one record re-made is the gate's own verdict record; nothing else under `runs/` moved.

## 1. The FAIL, reproduced — from the record on disk

`runs/gates/self_containment/gate.json` after the first press (no `--resume`, tree `74a59dfb`):

| field | value |
|---|---|
| `verdict` | **FAIL** |
| `tree_git_head` | `74a59dfbb608bc2291f3e3bf29fda97d590d7fe4` |
| `generated` | `2026-09-29T17:39:47` |
| `n_files_scanned` / `n_hits` / `n_in_prose` / `n_executable` | 53 / 53 / 38 / 15 |
| `n_findings` / `n_imports_of_either_directory` / `n_stale_declarations` | **1** / 0 / 0 |
| `n_compared` / `n_mismatched` | 53 / 1 |
| tooth `a_scratch_module_importing_the_directory` | TRIPPED: imports 0 → 1, findings 1 → 2, files 53 → 54, passed False → False |

The finding, verbatim:

```
file: experiment_runner.py   line: 1033   directory: idf_probe   executable: true
text: "under it), e.g. a retired worktree's idf_probe/runs/A<n>_runs; "
classification: UNCLASSIFIED — a finding
```

`git blame` attributes the line to `38d2f21f` (2026-09-29 09:53). The stale record's population against this
one, read from the two `hits` lists (the seeded `A90_runs` record against the new): lines present now and absent
then are exactly the four `38d2f21f` added — `harness/measurement/paper_tables.py:121` (prose),
`paper_tables.py:487` (prose), `experiment_runner.py:707` (prose, the `--paper-tables` docstring) and
`experiment_runner.py:1033` (executable); no line present then is absent now.

## 2. The fix

```diff
--- a/arch_surgery/MDA_partitioning_experiment_v4/experiment_runner.py
+++ b/arch_surgery/MDA_partitioning_experiment_v4/experiment_runner.py
@@ -1030,7 +1030,7 @@
         type=Path,
         default=None,
         help="for --paper-tables: the runs root to read (campaign/ and gates/ "
-        "under it), e.g. a retired worktree's idf_probe/runs/A<n>_runs; "
-        "default the experiment's own runs/",
+        "under it), e.g. a retired worktree's relocated records tree, the "
+        "path the retire script prints; default the experiment's own runs/",
     )
```

**Why reword rather than declare.** The gate classifies a line as prose only when it is a comment-only line, a
docstring, or a triple-quoted string (`_docstring_and_comment_lines`); every other line naming either
directory is executable and must be either in `DECLARED_OUTSIDE_REFERENCES` or a finding. The declaration
table is **keyed by file name** (`gates.py:1098`, `path.name in DECLARED_OUTSIDE_REFERENCES`): declaring the
runner would classify *every* executable line of `experiment_runner.py` naming either directory as allowed,
now and later — and the runner is the button, the file most likely to grow a real subprocess into the
superseded machinery. That is a weakening the brief forbids. The table's four entries are strings the code
*needs* (the gate's own search strings, provenance stamps written into records); a help-string example is not
needed — the guidance it gave ("where does such a runs root live?") survives without the directory name, since
`retire_task_worktree.sh` prints the path and protocol §7 says to cite what it prints. Removing the reference
keeps the runner fully scanned and the gate exactly as strong as before.

Nothing else was edited under the V4 folder: `harness/gates/gates.py` and the declaration table are untouched
(`git diff 74a59dfb 4b0673fd --stat`: one file, one hunk, two lines).

## 3. The PASS, the gate table and the documents

Second press, no `--resume`, tree `4b0673fd`:

| field | value |
|---|---|
| `verdict` | **PASS** |
| `tree_git_head` / `generated` | `4b0673fd…` / `2026-09-29T17:40:48` |
| `n_files_scanned` / `n_hits` / `n_executable` | 53 / 52 / 14 |
| `n_findings` / `n_imports_of_either_directory` / `n_stale_declarations` | 0 / 0 / 0 |
| `n_compared` / `n_mismatched` | 53 / 0 |
| tooth | TRIPPED: imports 0 → 1, findings 0 → 1, files 53 → 54, passed True → False |

Then, in order, each from the button:

1. `--measure gate_table --resume` — the stage re-made (it summarises the 30 verdict records; the new
   `self_containment` record is stamped in its `records_read`: `tree_git_head` `4b0673fd`, digest
   `bef8d3ed9f06…`, verdict PASS). Totals: `n_gates` 30, `n_pass` 30, `n_fail` 0, `n_not_run` 0,
   `n_teeth` 176, `n_teeth_tripped` 176.
2. `--plan-tables check` before writing: Appendix D **NOT IDENTICAL** in one hunk — line 543 of the rendered
   section, the `self_containment` row (`52 Python file(s) … 49 line(s)` → `53 … 52`, compared 52 → 53);
   the companion IDENTICAL; every §4 table IDENTICAL. *(A first `check`, before `campaign/` was seeded,
   also differed on the population header — §6, decision 2.)*
3. `--plan-tables write` — Appendix D 1 332 lines replacing 1 332; the companion 1 705 lines, whole; `git`
   shows one line changed in `EXPERIMENT_REPORT.md` and none in `RESULTS_TABLES_FULL.md`.
4. `--plan-tables check` — **IDENTICAL**: Appendix D 1 332 / 1 332, the companion 1 705 / 1 705; references
   41 to §3/§4's numbered tables, 66 to Appendix D, 18 to the companion, **0 dangling**; the change log held
   out. Table count unchanged (no number shifted; trap T17 does not apply).
5. `report_cells_preserved.py --base 74a59dfb` — grids 66 → 66 (report 43 → 43, companion 23 → 23),
   widest 13 / 25 / 26 columns before and after; **2 003 rows, 21 296 cells compared, of which 16 122 carry
   a number; 0 missing; 1 differing**: `DIFFERING gate table … 7 of 9 cell(s) matched at best` — the
   `self_containment` row, whose `population` and `compared` cells moved with the re-made record. Verdict
   `CELLS DIFFER; nothing withdrawn`, exit 1 — the expected result for a task whose one purpose is to change
   that row.

The V4 report's hand-written text: a dated as-built note at the end of §4.1's gates paragraph and one
Appendix C row (2026-09-29, A97), both naming I-32, `38d2f21f`, the stale stamp `f8147a00` and the two
from-scratch presses. Nothing else in the report is edited.

## 4. The stamp survey — 0 PROCESS runs

`run_stamp_survey.py` reads `tree_git_head` from every `metrics.json` under `runs/` (run records; gate
verdict records are `gate.json` and are not run records).

| survey | records | by commit |
|---|---|---|
| before, five briefed directories | 153 | 89 `0677a9b3`, 39 `4ca8cff5`, 6 `3983fb0c`, 6 `d6c48c88`, 3 each `47be2b0d` `50a35de1` `61473c1d` `6f5ba612`, 1 `8996b843` |
| before, with `campaign/` | 1 102 | the same, plus 949 `57dc0c14` |
| after (`--against` the previous) | 1 102 | **0 whose commit changed, 0 disappeared, 0 new** |

The re-made `self_containment` record and the re-made `gate_table` stage record are the only files this task
wrote under `runs/`; both are verdict/stage records, not runs. The gate's `--resume`-less press starts no
PROCESS process (its population is the package's source files), and neither `gate_table` nor `plan-tables` nor
`report_cells_preserved.py` does.

## 5. Environment

`/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH` =
this worktree's `arch_surgery/MDA_partitioning_experiment_v4/PROCESS` (trap T6). No PROCESS run was needed and
none was made, so the editable install's target never mattered to a number here; the variable was set on every
invocation regardless. Sandbox never overridden; nothing written under `MDA_partitioning_experiment_v5/`,
under `idf_probe/runs/A90_runs/`, or in any sibling clone.

## 6. Autonomous decisions, each with its reversal

1. **Reword, not declare** (§2). Reversal: revert `4b0673fd`'s hunk and add `"experiment_runner.py": ("a
   help-string example, data printed, no path read")` to `DECLARED_OUTSIDE_REFERENCES`; press the gate from
   scratch. The gate would PASS either way; the cost of the reversal is the file-level exemption stated in §2.
2. **`campaign/` seeded as well as the five briefed directories.** The first `--plan-tables check` (five
   directories only) differed in three places, two of them the population header — the renderer reads
   whether campaign records exist under `runs/` and wrote *"the gate population — 25 run records at
   `0677a9b3`"* for *"the campaign population — 949 run records at `57dc0c14`"*. A `write` in that state would
   have re-labelled Appendix D's population. `A90_runs/campaign/` (3.0 GB, 949 `metrics.json`) was copied in
   before any write; the survey and every check above were then run on the full seed. Reversal: none needed —
   the copy is untracked and the retire script relocates or discards it; a future brief seeding for a
   `plan-tables` write should list `campaign/`. *(Not copied: `block_trace/` and `_runs/`, which nothing here reads.)*
3. **The pre-existing counts-check differences are reported, not fixed.** `report_counts_check.py` at
   `4b0673fd` flags 6 lines, none about `self_containment`: the population's crash-class figures (records 20
   crashed / 8 unconverged, report 28 / 0), the stencil budget (396 vs the plan's 418), the gate table's teeth
   (records 176, §4.1's hand-written "168 of 168"), and the PASS rows with nonzero mismatches (`copy_identity`
   now 8, §4.1 says seven). All are hand-written figures of earlier days (A88's teeth count, A80's
   population sentence, the copy_identity count before `paper_tables.py` entered the permitted edits), and all
   six differ identically at `74a59dfb` — the script reads the same records and the same sentences there.
   Outside I-32; §4.1's note names the teeth figure so the paragraph does not contradict itself silently.
   Reversal: a one-line correction each, with the check re-run — proposed in §8.
4. **The task report's records path** reads `runs/…` (the worktree); the orchestrator's retire step relocates
   the tree and the archived header cites the path the script prints (memory rule; protocol §7).

## 7. What this does and does not establish

It establishes that V4 at `4b0673fd` earns the `self_containment` PASS its gate table states, from a record made
at that commit, and that no other published cell moved. It does not re-press any other gate: every other row
of Table D.1 is A90's record, reused under amendment 15, and this task's change (a help-string constant) alters
what no other gate reads. It does not touch the V5 copy, which carries the same line (`_v5/experiment_runner.py:1033`)
and whose own modify task removes it; V5's copy check compares against git at `7986d408`, not V4's live tree,
so this edit cannot reach it.

## 8. Proposals for the orchestrator (not applied here)

1. **Close I-32** at merge, with `4b0673fd` as the fixing commit and this report's §1 as the reproduction.
2. **A `--resume` press should refuse a `self_containment` record whose scanned file set or digest differs
   from the tree's.** The gate's population is source files, so its record could stamp the digest of the
   scanned set and `pool.run`-style reuse could compare it, as amendment 20 does for stage records — then the
   stale-record class I-32 belongs to could not recur for this gate. One tooth. A proposal, not a ruling.
3. **The six pre-existing counts-check lines** (§6, decision 3): a small correction task, or fold into V5's
   modify task where the report is rewritten anyway.
4. **Seeding lists for `plan-tables` tasks should include `campaign/`** (§6, decision 2), or the renderer's
   population header should refuse to write when the population kind changes between the record and the
   document — the second is the T14-shaped fix.

## 9. Change log (append-only)

| date | entry |
|---|---|
| 2026-09-29 | Worktree seeded from `A90_runs/` (five directories, then `campaign/`); FAIL reproduced at `74a59dfb` from the button, no `--resume`. |
| 2026-09-29 | `4b0673fd` — the help-string example reworded; gate pressed from scratch, PASS; `gate_table --resume`; `plan-tables write` then `check` IDENTICAL; `report_cells_preserved.py --base 74a59dfb` 2 003 / 21 296, 1 differing (the gate's row); stamp survey 1 102 / 0 changed. V4 report: §4.1 note and Appendix C row. This report written. |
