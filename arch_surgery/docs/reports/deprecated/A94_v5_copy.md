# A94 (v5-copy) — `MDA_partitioning_experiment_v5/` as an exact copy of V4, with proof

> **Document status** — **MERGED 2026-09-29 at `b0e91eed` (`--no-ff`); archived.** The living artifact is
> `arch_surgery/MDA_partitioning_experiment_v5/` (V4 at `7986d408`, copied whole; one re-pointed line); records
> relocated to `arch_surgery/idf_probe/runs/A94_runs/v5_copy_gates/`; the orchestrator's assessment is §9.
> Was: **OPEN.** Task **A94 (v5-copy)**, branch `A94-v5-copy` (worktree
> `.claude/worktrees/A94-v5-copy`, no records seeded — every gate below pressed from scratch), base
> **`7986d408`** (= `architecture_surgery` at dispatch), copy commit **`d6c246a1`** — the commit that
> holds the copy, the manifest and the one re-pointed line, and where every gate below ran. Records:
> `arch_surgery/MDA_partitioning_experiment_v5/runs/` in the worktree (untracked, as V4's `runs/`
> is; the retire script relocates `arch_surgery/idf_probe/runs/`, which this task did not write to,
> so these records are relocated by nobody — see §6 (3)). Nothing under
> `arch_surgery/MDA_partitioning_experiment_v4/` was written.

The user, 2026-09-29: *"copy and then modify is suitable. I want to move towards v5."* This task is the
copy. No V5 improvement item is implemented here; nothing is removed, renamed or cleaned up.

## 0. Verdict

**`arch_surgery/MDA_partitioning_experiment_v5/` is an exact copy of `arch_surgery/MDA_partitioning_experiment_v4/`
at `7986d408`: 310 of 310 tracked files copied from the commit (never from a working tree), 309 byte-identical,
one line of one file re-pointed (`report_cells_preserved.py:342`, the `git show` path the script resolves), and
two files of its own added (`copy_manifest.py`, `COPY_MANIFEST.json`). The copy reproduces V4's twenty reference
records bit for bit: gate GR PASS at `d6c246a1`, 20 of 20 runs reproduced (14 optimisations + 6 evaluations over 3 configurations), 270 values in the committed reference, 14 excluded by name with their reason, **256 compared, 256 matched, 0 mismatched**, no tolerance on any of them, 8/8 teeth tripped, both substitutes (`A1`, `AR`) passed, the record contract passed, at one worker, every run record stamped `d6c246a1`.** The physics is byte-identical to `c0ae5b28`
(G0′ PASS, 77 files, the one approved `pulse.py` edit) and the driver copy is the source commit `f2dc9243` plus
exactly the eight recorded permitted edits (`copy_identity` PASS, 224 files). Twelve of the thirteen run-free
harness self-checks PASS with every tooth tripped.

**One gate FAILs, and it is V4's, not the copy's: `self_containment`** — one executable line of
`experiment_runner.py` (line 1033, the `--paper-tables-runs` help string, *"e.g. a retired worktree's
idf_probe/runs/A<n>_runs"*) names `idf_probe/` and no declaration accounts for it (53 files scanned, 53 lines
naming either directory, 1 finding, 0 imports, 0 stale declarations; tooth 1/1 tripped). The runner is
byte-identical to V4's, so V4's own `self_containment` gate FAILs the same way at `7986d408`; the line entered
at `38d2f21f` ("paper result tables", 2026-09-29) and the last V4 verdict on record for this gate is a PASS at
`f8147a00` (2026-09-17, `idf_probe/runs/A90_runs/gates/self_containment/gate.json`) — nobody has pressed it
since. Not tuned, not fixed here (a fix is an edit to the copy beyond the re-point, and to V4 it is a merge-time
matter); proposed as an issue in §7. The copy inherits the failure exactly, which is what an exact copy does.

## 1. What was copied, and how the copy is proven

**The script.** `arch_surgery/MDA_partitioning_experiment_v5/copy_manifest.py` (new, committed at `d6c246a1`),
three commands: `copy --source-commit 7986d408 --task "A94 (v5-copy)"` reads every blob `git ls-tree -r`
lists under `arch_surgery/MDA_partitioning_experiment_v4/` at the commit with `git cat-file --batch` and writes
it at the same relative path; `record` re-digests the copy and refuses unless the files differing from the
source commit are exactly its declared `REPOINTED_FILES`; `check` compares the folder against the manifest
(every manifest file present with its recorded copy digest, every source digest re-derived from git, no file
in the folder the manifest and the two own files do not name, no declared re-point without a difference) and
then runs three teeth in a temporary copy of the folder. It runs git at the repository top level: its first
version ran `git ls-tree -- <path>` in the V5 folder, listed 0 blobs and *passed a check over nothing* —
trap T12's shape — so both the copy and the check now refuse an empty population.

**The manifest.** `COPY_MANIFEST.json`: source `arch_surgery/MDA_partitioning_experiment_v4/` at
`7986d40822d7eaa56896f085353b0d4eb22112b1` (tree `8a8c0c29deddc8522d47819b3f23c1554a87f222`), 310 files,
11 431 460 bytes, sha256 per file at the source commit and in the copy, `repointed_files`, and a `recorded`
history (one entry, 2026-09-29, one file re-pointed).

**The proof, at `d6c246a1`** (`copy_manifest.py check`, 2026-09-29):

| | |
|---|---|
| files compared | 310 (227 under `PROCESS/`, 83 harness, scripts, data, documents; the `.gitignore` included) |
| identical to the recorded copy digest | 310 |
| re-pointed (copy digest ≠ source digest) | 1 — `report_cells_preserved.py` |
| missing / added / differing | 0 / 0 / 0 |
| source digests re-derived from git at `7986d408` | 310 of 310 |
| teeth | 3/3 tripped: one byte changed (`PROCESS/process/models/blankets/blanket_library.py`), one file removed (same), one file added — each FAILs the check in a temporary copy |

*Caption: one row per quantity of the check; population the 310 files git tracks under V4 at `7986d408`, excluding
`runs/`, `__pycache__` and `.claude/` (none of which is tracked). Independent confirmation by shell inspection, not
evidence: `diff -r` of the two folders excluding `runs/`, `__pycache__` and the two own files reports the one
changed line of §2 and nothing else; all 310 blobs are mode 100644, none a symlink.*

## 2. Self-references: what was re-pointed, and what was found and left

A grep over the whole V4 tree for `MDA_partitioning_experiment_v4` and `_v4` (`.py`, `.md`, `.json`, `.sh`,
`.IN.DAT`) finds nine files. Every path the *code resolves* is derived from `__file__`
(`config.EXPERIMENT_DIR`, `registry._EXPERIMENT_DIR`, the driver's `Path(__file__).resolve().parents[n]` for
`node_writesets.json`, `dsm_node_map.json` and `ystate.py`, `copy_gates.HERE`), so the driver copy, the harness
and `copy_gates.py`'s permitted-edit table (its `now=` literals are those relative expressions, unchanged)
needed no change and got none. One literal is resolved by code and was re-pointed:

| file | line | before | after | why |
|---|---|---|---|---|
| `report_cells_preserved.py` | 342 | `rel = f"arch_surgery/MDA_partitioning_experiment_v4/{name}"` | `rel = f"arch_surgery/MDA_partitioning_experiment_v5/{name}"` | the path `git show <base>:<rel>` resolves the committed report and companion at; with the V4 literal the V5 script would compare this folder's rendering against the V4 report at `<base>` |

*Caption: the complete list of changed lines in the copy (one). `--base` defaults to `c45cac1c`, a V4 commit at
which no V5 folder exists; a V5 caller passes a base at or after `d6c246a1` — left as it stands (§6 (2)).*

Found and **left unchanged**, each with the reason:

| file | lines | what it is | why unchanged |
|---|---|---|---|
| `harness/core/config.py` | 36, 40 | comments naming the package directory | prose; the values are derived from `__file__` |
| `harness/core/records.py` | 1017–1019 | the user's ruling quoted (*"in the v4 report, rename…"*) | history |
| `harness/gates/reference.py` | 471 | a local variable named `v4` | not a path |
| `harness/gates/gate_composition.py` | 173; 463, 466 | a docstring; a tooth's fixture record re-rooted at `/elsewhere/another-worktree/…_v4/PROCESS` | the tooth relativises against the record's own `tree` stamp, so the name is arbitrary; verified by the `composition` gate's 7/7 teeth |
| `harness/data/dsm_function_counts.json` | 36 | `driver_model_container.path` — the provenance of the file's derivation | data the `data` gate checks byte for byte against its source commit; editing it forfeits that (the same rule as `harness/data/PROVENANCE.json`'s `stale_internal_names`) |
| `PROCESS_diff.py` | 236, 424 | prose summaries of the permitted edits ("in the copy they resolve under `…_v4/harness/data/`") | the hunks they describe are byte-identical in the copy; the prose is V4's history, printed as such |
| `harness/README.md` | 11, 624, 743, 1124 | "paths are relative to `MDA_partitioning_experiment_v4/`"; `cd …_v4`; `sys.path.insert(0, "…_v4")` | documentation, not resolved by code; the later modify task rewrites the README under item 10, and a copy that edits documents for taste is no longer a copy (§7) |
| `EXPERIMENT_REPORT.md` | 616, 633, 1611 | the V4 report's own text | history |
| `PROCESS/process/models/physics/physics.py` | 2795 | `"Nuclear Fusion v47"` | not a self-reference |

**Provenance regeneration.** `PROCESS/copy_gates.py provenance --force --task "A94 (v5-copy)"` run in the copy
regenerated `PROCESS/PROVENANCE.json` **byte-identical** to V4's (the generator keeps `copy_date` and appends a
history entry only when a permitted-edit digest changes; none did). `harness/experiment/data_provenance.py record
--force` regenerated `harness/data/PROVENANCE.json` differing in **one line only** — `"copy_date": "2026-09-14"` →
`"2026-09-29"` (that generator stamps today's date; the data was not re-copied) — and the V4 file was restored
(§6 (1)). Both facts are what the `copy_identity` and `data` gates then re-checked (§4).

## 3. How the gates were pressed

Interpreter `/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python`, `PYTHONDONTWRITEBYTECODE=1`,
`PYTHONPATH` = this worktree's `MDA_partitioning_experiment_v5/PROCESS` (trap T6; the pool sets the same for every
child from `campaign.tree`, and every child asserts `process.__file__` is exactly under it — the `capability` gate's
fifth tooth shows the assertion holding from a decoy working directory), `HARNESS_WORKERS=1` (the pool's declared
override; one PROCESS process at a time, two other tasks on the machine). `runs/` was deleted before the press at
`d6c246a1`, so no `--resume` and no seeded record: every verdict's `tree_git_head` is `d6c246a1`. The thirteen gates
the registry lists as "no PROCESS run" and that read no record population were pressed one at a time by
`experiment_runner.py --gate <name>`; the three other run-free gates (`tally_contracts`, `recomputation`,
`run_kind_separation`) read tally and campaign records and have no population in a from-scratch tree — not
pressed, stated here rather than run over nothing (trap T12). Then `artifacts_derive_inputs` (GR's declared
prerequisite: GR refused to start without the lifted input files, naming that stage — §4.2), then `reproduction`.

## 4. Gate verdicts, from the records on disk

### 4.1 The run-free gates, at `d6c246a1`

| gate | plan | verdict | population (the gate's own words, shortened) | compared | mismatched | teeth |
|---|---|---|---|---|---|---|
| `g0prime` | G0/G0′ | **PASS** | 77 files under `PROCESS/process/models/` against `c0ae5b28` (git cat-file), plus the file set | 77 | 1 (the approved `pulse.py`, D14(b), on its expected digest) | 4/4 |
| `copy_identity` | harness | **PASS** | 224 files under `PROCESS/process/` against the source commit `f2dc9243`, plus the file set; 8 permitted-edit files on digest and hunks | 224 | 8 (the recorded permitted edits, by name) | 12/12 |
| `edit_behaviour` | harness | **PASS** | three arms of one probe: the copy with the write-set artifact absent, the source commit with it absent, the copy with it present | 3 | 0 | 1/1 |
| `self_containment` | harness | **FAIL** | 53 Python files; 53 lines naming either superseded directory, 15 executable | 53 | **1** | 1/1 |
| `composition` | harness | **PASS** | 8 arms × 3 configurations = 24 pairs | 42 | 0 | 7/7 |
| `rungs` | harness | **PASS** | 11 matrix rows × 8 arms = 88 cells; 6 rung steps | 98 | 0 | 3/3 |
| `provenance` | harness | **PASS** | one scratch repository, three states | 4 | 0 | 4/4 |
| `data` | harness | **PASS** | 17 files in `harness/data/` + the moved predicate module; 9 declared counts | 18 | 0 | 6/6 |
| `run_path` | harness | **PASS** | 2 phases × the declared field list; 2 displacement streams; 5 refusals | 12 | 0 | 12/12 |
| `resume_identity` | harness | **PASS** | 22 job fields; 13 by-design pairs; 3 recorded-name rows; 0 records under `runs/` | 38 | 0 | 9/9 |
| `capability` | harness | **PASS** | every active arm/configuration pair | 55 | 0 | 5/5 |
| `artifacts_check` | harness | **PASS** | 19 artifact rows over 3 configurations; 93 checks | 93 | 0 | 3/3 |
| `stage_provenance` | harness | **PASS** | a scratch records directory broken 4 ways; a scratch census; the live records surveyed | 10 | 0 | 5/5 |

*Caption: one row per gate pressed, read from `runs/gates/<gate>/gate.json` (`tree_git_head` `d6c246a1` on every
row, `generated` 2026-09-29 17:14–17:16); "compared / mismatched" are the record's `n_compared` / `n_mismatched`;
"teeth" tripped / declared. The same thirteen were pressed once before at `7986d408` with the copy untracked, with
identical verdicts and counts; those records were discarded when `runs/` was deleted for the press at the copy commit.*

**The `self_containment` finding**, verbatim from the record:

```
file: experiment_runner.py   line: 1033   directory: idf_probe   executable: true
text: "under it), e.g. a retired worktree's idf_probe/runs/A<n>_runs; "
classification: UNCLASSIFIED — a finding
```

It is the help string of `--paper-tables-runs` (added at `38d2f21f`). The gate classifies a line as prose only
when it is a comment or a docstring; an argument help string is executable code by its rule, and
`DECLARED_OUTSIDE_REFERENCES` names four files, none of them the runner. The tooth (a scratch module importing
`arch_surgery.idf_probe`) tripped: imports 0 → 1, findings 1 → 2. Two fixes are possible and neither is this
task's: declare the runner in the table with the reason, or move the example out of the help string. Which one is
the orchestrator's call for V4 (§7).

### 4.2 The prerequisite, and gate GR

`--gate reproduction` pressed first at `d6c246a1` **refused to start** (record kept as evidence, then overwritten
by the press below): *"the lifted input file for large_tokamak_nof is not at `runs/input_files/large_tokamak_nof/
large_tokamak_nof_lifted.IN.DAT`. It is derived from the committed input file by `experiment_runner.py --artifacts
derive-inputs`, whose gate checks the bytes against the recorded digest 8902a6a58bb3…; nothing stages it from
anywhere else."* A refusal with the producing stage named, from the same button — the failure path protocol §15
asks for. The stage was pressed as its gate (`artifacts_derive_inputs`, which runs the baseline evaluation the
third line of each lifted file is measured from, then checks the bytes) and GR after it:

| gate | plan | verdict | population (the gate's own words) | compared | mismatched | teeth | `tree_git_head` |
|---|---|---|---|---|---|---|---|
| `artifacts_derive_inputs` | harness | **PASS** | 3 configurations; the digest gate applies to the 2 pulsed ones | 2 | 0 | 4/4 | `d6c246a1` |
| `reproduction` | GR | **PASS** | 20 runs (14 optimisations + 6 evaluations) over 3 configurations; 270 values in the committed reference, 14 of them excluded by name with their reason, 256 compared, no tolerance on any of them | 256 | 0 | 8/8 | `d6c246a1` |

*Caption: read from `runs/gates/artifacts_derive_inputs/gate.json` (generated 2026-09-29 17:17:35) and
`runs/gates/reproduction/gate.json` (17:29:41); "compared / mismatched" are `n_compared` / `n_mismatched`.*

GR's record in detail (`runs/gates/reproduction/gate.json`): `n_runs` 20, `n_runs_reproduced` 20, `n_values_in_the_reference`
270, `n_values_excluded` 14, `n_values_compared` 256, `n_values_matched` 256, `n_values_mismatched` 0; per run, every one
of the twenty (`BR`, `B0`, `B2` at seed 0 and `B2`, `B1` at seed 1 on the three configurations — `B1` absent on
`st_regression` as the reference records it; `A0`, `A2` at seed 1) `passed`, 0 mismatched; `substitutes.A1` true,
`substitutes.AR` true; `record_contract_passed` true; `resumed` false; `workers` 1; `runs_provenance`: 29 records, one
head `d6c246a1`, 29 jobs; `refused` null. Teeth, all TRIPPED: `count` (one node call added must not reproduce), `hex`
(one character appended to `norm_objf`), `excluded field` (a doctored excluded value reported as excluded, not among the
mismatches), `missing reference` (no committed file must FAIL, not compare over an empty set), `missing key`, `bad name map`
(`BR` without the map must RAISE), `composition` (`B2` on `st_regression` run with the flat loop under the partitioned
arm's name must not reproduce — one extra run, the second `B_B2_st_regression_seed000_gate_*` directory), `attempt
summation` (400 + 550 against 1000 must be REFUSED).

**Stamp survey** (`run_stamp_survey.py --runs runs`, the committed script, at `d6c246a1`): 30 run records under `runs/`,
**30 at `d6c246a1`**, no other head — the from-scratch claim checked on the records rather than on the button (trap T13;
harness plan amendment 13 (i)). The 30 are GR's 3 evaluation-phase references, its 20 reference runs, the composition
tooth's 1, the substitutes' 3 (`A1` on the two pulsed configurations, `AR` on `st_regression`) and `derive-inputs`'
baselines.

**The gate table** (`experiment_runner.py --measure gate_table`, record `runs/gates/gate_table/`): 30 registered gates,
**14 PASS, 1 FAIL (`self_containment`), 15 not run**; 84 of 176 teeth tripped (every declared tooth of every gate that
ran). The 15 not run are the PROCESS-running gates outside this brief and the three record-reading run-free gates (§3).

## 5. What this does and does not establish

- The V5 folder at `d6c246a1` is V4 at `7986d408` in every byte that reaches a measurement: same driver copy
  (224 files, `copy_identity`), same physics (`g0prime`), same committed data (`data`), same harness (the manifest:
  309 identical files, one re-pointed line in a report-rendering script no gate reads).
- GR through the V5 copy is the *same* instrument reproducing the *same* twenty records; it says nothing about
  whether any V5 change is right — that is what a later task's GR press at *its* commit must say, and item 10's
  "one-time reproduction gate: the V5 copy at its copy commit, before any change" is this press.
- Not pressed: the gates that run PROCESS beyond GR and its prerequisite (G1–G9, the census and per-run artifact
  stages, `written_file_gap`, `predicate_mode`), and the three record-reading run-free gates. None was in the
  brief; each would be pressed by the task that changes what it reads.

## 6. Autonomous decisions, each with its reversal

1. **`harness/data/PROVENANCE.json` kept byte-identical to V4's** rather than committed as regenerated. The
   regeneration changed only `copy_date` (2026-09-14 → 2026-09-29); the data was not re-copied on that date and
   the driver-copy generator's own rule (A90: a regeneration keeps the copy's date) says the date is the copy's.
   *Reversal:* `harness/experiment/data_provenance.py record --force` in the V5 folder, commit the one-line diff.
2. **`report_cells_preserved.py`'s `--base` default (`c45cac1c`) left as it stands** while its path literal was
   re-pointed. The default names a V4 commit at which no V5 folder exists, so the V5 script's default press fails
   with git's own message until a V5 base exists; changing the default is a choice for the task that first renders
   V5 tables. *Reversal:* one literal.
3. **Run records left under `MDA_partitioning_experiment_v5/runs/`** (gitignored by the copied `.gitignore`), not
   copied or linked into `arch_surgery/idf_probe/runs/`. The retire script relocates only the latter, so retiring
   this worktree **destroys these records** unless they are moved first (issues I-14–I-16's shape). *Reversal /
   action at merge:* before retiring, `cp -r` the worktree's `MDA_partitioning_experiment_v5/runs/` beside the
   relocated records, or extend the retire script to relocate a V5 `runs/` as it does V4's — proposed in §7.
4. **The record-reading run-free gates not pressed** (§3). *Reversal:* `--gate tally_contracts`,
   `--gate recomputation`, `--gate run_kind_separation` once a population exists.
5. **`self_containment` reported, not fixed.** *Reversal:* none needed; the fix is a V4 decision (§7).
6. **The first GR refusal's record overwritten** by the successful press (the gate writes one `gate.json`). Its
   text is quoted in §4.2 verbatim; the runner printed it to the press log kept in the session's scratch
   directory. *Reversal:* re-press `--gate reproduction` in a tree with `runs/input_files/` removed.

## 7. Proposals for the orchestrator (not applied here)

1. **An issue row for V4**: `self_containment` FAILs at `7986d408` on `experiment_runner.py:1033` (since
   `38d2f21f`, 2026-09-29); every V4 verdict table that reports it PASS predates that commit. Fix in V4 by
   declaring the runner in `DECLARED_OUTSIDE_REFERENCES` (a help-string example, data printed, not a path read)
   or by moving the example out of the string; then one press of the gate.
2. **The retire script and a V5 `runs/`**: `arch_surgery/bin/retire_task_worktree.sh` relocates
   `arch_surgery/idf_probe/runs/`; V5's records live under `MDA_partitioning_experiment_v5/runs/` (as V4's did
   under `_v4/runs/`). Either relocate both or state where V5 records go, before the first V5 campaign.
3. **The README's four self-references** (§2) are the modify task's to rewrite under item 10, together with
   `PROCESS_diff.py`'s two summary strings and the "V4" wording in `PROCESS/PROVENANCE.json`'s `what` and
   `copy_gates.py`'s docstring. Recorded here so the later task has the list.
4. **`copy_manifest.py check` as a registered gate?** It is a top-level script like `PROCESS_diff.py`, run by
   hand; if V5 keeps a copy gate beyond this task, registering it costs one entry. Not proposed for V4.

## 8. Change log (append-only)

| date | commit | what |
|---|---|---|
| 2026-09-29 | `d6c246a1` | The copy: 310 files from `7986d408` via `copy_manifest.py copy`; `record` after the one re-point; `check` PASS 3/3 teeth; both provenance regenerations run (one identical, one restored) |
| 2026-09-29 | *(records, untracked)* | Thirteen run-free gates pressed at `7986d408` (V5 untracked) and again from scratch at `d6c246a1`: 12 PASS, `self_containment` FAIL (1 finding, V4's) |
| 2026-09-29 | *(records, untracked)* | `--gate reproduction` refused (no lifted input file); `--gate artifacts_derive_inputs` then `--gate reproduction` pressed at one worker — §4.2 |
| 2026-09-29 | the commit that adds this file (the branch tip at hand-back) | This report, with the gate verdicts of §4 read from the records |

## 9. Orchestrator's critical assessment (protocol §5) — 2026-09-29

**Verdict: merge.** The V5 directory is V4 at `7986d408`, proven two ways the task did not use:

- **Tree against tree in git.** `git diff --stat 7986d408:arch_surgery/MDA_partitioning_experiment_v4
  A94-v5-copy:arch_surgery/MDA_partitioning_experiment_v5` lists exactly three paths: `copy_manifest.py` (new),
  `COPY_MANIFEST.json` (new) and `report_cells_preserved.py` (one line, the `git show` path literal `_v4` → `_v5`).
  The V5 tree holds 312 entries = 310 copied + 2 new. `git diff --stat 7986d408 A94-v5-copy --
  arch_surgery/MDA_partitioning_experiment_v4` is empty: V4 untouched.
- **The gate records read from disk**, not from the report: `reproduction` PASS, 8/8 teeth; `g0prime` PASS 4/4;
  `copy_identity` PASS 12/12; `artifacts_derive_inputs` PASS 4/4; `self_containment` **FAIL** with one finding
  (`experiment_runner.py:1033`, the help-string example naming `idf_probe/`, classified as an executable line);
  all 30 run records stamped `d6c246a1`, none dirty.

**The FAIL is V4's, and V4's published gate table hides it.** The line entered at `38d2f21f` ("paper result
tables", 2026-09-29, the orchestrator's own commit of the paper-tables module); V4's latest `self_containment`
record (`A90_runs/gates/self_containment/gate.json`) is a PASS stamped `f8147a00` (2026-09-17) and was carried
into A90's re-rendered gate table by `--resume`. So the gate table at V4's tip states a PASS that the tree no
longer earns — a stale record of the kind the reuse rule (amendment 15) says must be re-made when a change
alters what the gate reads. Filed as **I-32**; the fix is V4's (declare the runner's help string, or move the
example out of it) plus one press of the gate and a re-render, a small task for the user to dispatch since V4
is published. The V5 copy inherits the line and the modify task removes it under item 10.

**Records.** The task wrote its records under `MDA_partitioning_experiment_v5/runs/` (124 MB) and believed the
retire script would not relocate them (§6 (3), §7 (2)). It would: since I-16 the script relocates every
directory named `runs` anywhere under `arch_surgery/`, entry by entry, namespaced with the task label — but as
three entries (`A94_gates`, `A94_input_files`, `A94__mplconfig`) rather than one tree. So before retirement
the orchestrator copied the whole tree into the worktree's `arch_surgery/idf_probe/runs/v5_copy_gates/`
(verified byte-identical with `diff -r`), removed the duplicate, and let the script relocate the one tree: it
lands at `idf_probe/runs/A94_v5_copy_gates/` and seeds the V5 folder's `runs/` for the modify tasks (the copy's
gate records at `d6c246a1`). Proposal §7 (2) needs no script change; the plan's §11 says where V5 records go.

**Accepted as decided.** Keeping `harness/data/PROVENANCE.json` with V4's `copy_date` rather than regenerating
a file that would differ only in the date (§6 (1)) is right: the date is V4's provenance, the copy's is the
manifest. The eight self-references left in place (README, `PROCESS_diff.py` strings, docstrings) are the
modify task's, as the report says. `copy_manifest.py check` is not registered as a gate: the manifest is a
one-time proof and the copy commit is its record.

**Not done here.** The task's report states GR's 256 compared / 0 mismatched; I read the verdict and the teeth
count from the record and did not recount the 256 values.