# A73 (run-path-edits-and-the-press) — B3, A66, the child-side remainder, and the one press of D27

> **Document status** — **ARCHIVED at merge, 2026-09-14.** Task **A73 (run-path-edits-and-the-press)** merged into `architecture_surgery`
> at `03f72479` (branch tip `bb34cee8`, base `2969fe66`). Records relocated to `arch_surgery/idf_probe/runs/A73_runs/` — **the D27 from-scratch
> population** (126 pool records at `0677a9b3`/`4ca8cff5`, G1's before capture at `fd480aff`). The orchestrator's critical assessment is
> the last section. Folder position records lifecycle, not validity (trap T3).

*Vocabulary is the harness README's §3. "Job", "identity", "digest", "shared pool" as A72's
report §2 defines them; "press", "tooth", `--resume`, "straddle" as in A68's preamble and A62 §7.
Every number below was produced by a committed script named in the same sentence; the wall clock
is context only, with the worker count (3, `Campaign.workers`), never evidence.*

## 1. Verdict in one page

**Part 1 is done, all four items, committed before any run** (§2). **The press is done, once,
with one interruption and one gate that failed at the press and passed after a ruled exclusion fix
— both results, both stated with their numbers** (§3, §4). **Final gate table: 30 PASS, 0 FAIL,
152 of 152 teeth** (§4, after §4.4):

| | result |
|---|---|
| gates | **30 registered; at the press 29 PASS, 1 FAIL** (`predicate_mode`, G8); **after the ruled fix of §4.4, 30 PASS, 0 FAIL**; 152 of 152 teeth tripped; every verdict names the commits of the records it read |
| G8 at the press | **FAIL**: 24 of 8 092 record values differ over 12 pairs — **exactly two per pair, `job_identity.predicate_mode` and `job_digest`**, the pool's stamp of the setting the gate varies (A72's identity fields, added after G8's exclusion table was written; G8 was on A72's unpressed list); 0 of 84 output-file lines and 0 other values differ (§4.3). A measured result, kept in the history |
| G8 after the ruling | **PASS** at `b485bf4c`: 12/12 pairs bit-identical, 0 of 8 068 values and 0 of 84 lines differ, 240 values excluded (the two new names: 24); **0 PROCESS runs**, 27 records kept (24 at `0677a9b3`, 3 at `4ca8cff5`) (§4.4) |
| GR | PASS, 20/20 runs reproduced, 0 of 256 compared values differ (270 in the reference, 14 excluded by name); read 29 records, 26 at `0677a9b3` and 3 at `4ca8cff5` |
| G1, a straddle `fd480aff` → `0677a9b3` across the run-path change | PASS, a neutrality result: 6 pairs, **0 of 2 825 record values and 0 of 51 319 output-file lines differ**; 1 758 values and 45 lines excluded, 951 of the values by the instrument-change kind A62 introduced (0 outside the exit audit and its stamp); the three A72 identity names one-sided as expected (`job_identity` 0/120 leaves, `job_digest` 0/6, `pending_switches_allowed` 6/0) |
| the population | **136 PROCESS runs made** (41 in the aborted press at `4ca8cff5`, 95 in the resumed press at `0677a9b3`); 147 run records under `runs/` afterwards: 126 shared-pool jobs (89 at `0677a9b3`, 37 at `4ca8cff5`), G1's 6 after-capture runs, G1's 6 kept before-capture runs at `fd480aff`, the 6 kept census records, 2 lifted-input baselines, 1 GR tooth fixture |
| the shared pool's saving | 242 gate-job declarations over 30 gates → **126 distinct jobs**, 42 read by more than one gate; run-making gates alone declare 167 jobs. Against the per-gate layout at A71's tip (152 runs per press) the pool plus G1's after capture is **132 — 20 fewer, A72 §7's projection exactly**. Against A67's 184-record seed population the tree holds 147 records (37 fewer; that figure also counts B3's 11 retired diagnosis records and B5's 6 retired contrast runs, so it is not the pool's saving alone) |
| lines | `harness_survey.py` §1: **47 728 (A68, before D27) → 45 390** after A73 (A72's tip: 47 783; the difference here is B3's 2 332 lines and the child-side remainder) |
| the harness plan's §4 | rendered from the records at `0677a9b3`, `4ca8cff5`, `fd480aff`; 131 tables, 3 932 cells; `--plan-tables check` clean; the gate table reads **30 PASS, 0 FAIL, 0 not run; 152 of 152 teeth** (first render, before §4.4: 29 PASS, 1 FAIL) |

**Two things happened during the press that the protocol asks to be said plainly.** (i) The first
`--gate all` at `4ca8cff5` crashed in gate G4's body after 41 runs on a `NameError`
(`gate_audit.py:546`, `excluded_keys`): A72's B1 commit renamed the assignment to `_excluded_keys`
and left two uses on the old name, and G4 had not been pressed since (A72 §9 item 4, rule (xiii)
debt). No run was executing; the one-line fix was committed (`0677a9b3`) and the press resumed with
`--resume`, keeping the 38 complete pool records at `4ca8cff5` (§4.1 — amendment 15's rule; the
reversal is to delete `runs/gates/_runs/` and press once more). (ii) The press stopped at G8's FAIL
by design; the four 0-run gates after it in the order (`tally_contracts`, `recomputation`,
`run_kind_separation`, `stage_provenance`) were run one by one with `--resume` so the gate table has
every row — all PASS, 0 PROCESS runs (§4.2). G8 was not touched by this task on its own
authority; the orchestrator ruled on it (§4.4), and both were the orchestrator's decisions on §9's
items 2 and 3.

## 2. Part 1 — the run-path edits, item by item

All four items were committed **before** any run was made (amendment 13 rules (v)/(vi)); the
press started at `4ca8cff5` with a clean tree, and after it started only records, the §4 render
and this report changed — with one exception, §4.1, a gate-module fix between two presses while
no run executed.

| item | what changed | commit | reversal |
|---|---|---|---|
| **B3** (survey) — retire the diagnosis instrument | `harness/gates/exit_audit_diagnosis.py` (1 635 lines) and `harness/child/audit_map.py` (697) deleted; in `child/optimise.py` the import, the `audit_map_mod.install(...)` call that installed the switched-off trace on every optimisation, the `on_ready_to_sweep=` lambda and the closing `audit_map_mod.observe(...)`; in `child/child.py` the `on_ready_to_sweep` parameter of `exit_audit` and its one call (the trace was its only caller); `harness_survey.py`'s `by_design` loses the `exit_audit_diagnosis/` clause; docstrings of `child/__init__.py`, `gates/__init__.py`, `child/data_structure.py` (heritage kept, retirement named); README layer 3 and §10.1. **There was no registry entry and no runner flag to remove**: the stage was a standalone module run as `python -m harness.gates.exit_audit_diagnosis`, outside `--gate all` (verified by grep over `registry.py`, `experiment_runner.py`). The attribution the instrument made — `tfcoil.insstrain`'s 7e-3 residual is the output path raising `n_rad_per_layer` 100 → 500 before the snapshot — stays recorded in A61's and A62's archived reports and in ruling D25; the instrument that runs on every record (`data_structure.py`, the derived restore set) is D25's and stays. Its 11 old records were not in this worktree's seed. | `82ea0377` | `git revert 82ea0377` restores both modules and the hook; nothing else reads them |
| **A66** — `ystate.py` into `child/` | `git mv harness/ystate.py harness/child/ystate.py` — **bytes unchanged** (`harness/data/PROVENANCE.json` re-recorded with `data_provenance.py record --force`: the diff is the `name` label, the date and one stale `harness/selfcheck.py` → `harness/gates/selfcheck.py` in the `what` prose; the 22 recorded hunks and the post-edit sha256 are the same). Imports: `child/predicate.py` (`from . import ystate`), `experiment/artifacts.py`, `gates/gate_predicate_mode.py`, `experiment/data_provenance.py` (`YSTATE`). **The copy:** `PROCESS/process/core/solver/module_solve.py`'s literal gains `/ "child"` and its comment names the new path; `PROCESS/copy_gates.py`'s `PermittedEdit(name="YSTATE_MODULE_PATH")` `now=` changes in the same commit; `PROCESS/PROVENANCE.json` regenerated (`copy_gates.py provenance --force`: the `now` string, the file's post-edit sha256, the hunk line numbers, the date). `PROCESS/CHANGES.md` §4.2.1 (snippet and *why*) and §5 ("the file moved"); `PROCESS_diff.py`'s annotation and prose; `child/__init__.py` docstring, README layer 3 and §10.1 lose the "one member outside" note; `EXPERIMENT_PLAN.md` line 589 names the new path (outside the rendered §4). Proven from a directory that is neither tree, with `PYTHONPATH` at the copy and `-P`: `module_solve.YSTATE_MODULE_PATH` resolves to `harness/child/ystate.py`, exists, and `_ystate_module().RULERS == ('frozen', 'mixed')`. | `7d333677` | `git revert 7d333677`, then `copy_gates.py provenance --force` and `data_provenance.py record --force` — the two records must be regenerated with the revert, exactly as they were with the move |
| **A72's hand-over, child side** (B4's remainder, A7's remainder) | `--pending-allowed` removed from `child/evaluate.py` and `child/optimise.py`; `child.open_record` loses `pending_switches_allowed` and no longer writes the field (out of `SCHEMA` since A72); `stamp_capabilities_absent` → **`stamp_driver_counters_null`**, the docstring says what it does and what it was; `predicate.provenance_of` deleted (**0 references, re-verified by grep** over the package and the top-level scripts before deletion); G1's conditional exclusion for `pending_switches_allowed` keeps its entry with the note updated (present on captures before A73, absent since). | `731a6be8` | `git revert 731a6be8` |
| **Improvement item 13** — G1's manifest commit | Manifest-writing only, so fixed: `capture_neutrality` reads `tree_git_head` from the records it indexes (`records_mod.read(job.outdir)`), writes it as the manifest's `tree_git_head` when they agree, lists them as `records_git_heads`, sets `tree_git_head` to `None` when they sit at two commits (so `_straddle` says the straddle cannot be stated rather than naming one side), and names the pressing commit apart as `pressed_at_git_head`; the runner's `--capture` printout says both. `_straddle` and `exclusion_review` read `tree_git_head` as before, so a straddle is now decided by the records' commits, which is the thing being claimed. | `4ca8cff5` | `git revert 4ca8cff5`; a manifest written by the reverted code is read by the same consumers |

**Not touched, as briefed:** improvement item 14 (δ at seed 0 composed two ways) — it reaches
G1's kept before capture.

### 2.1 The copy gates after the regeneration

`PROCESS/copy_gates.py all` at `7d333677` (and again inside `--gate all` at the press commit,
§4): `smoke-import` PASS, `edit-behaviour` PASS, `copy-identity` PASS (224 files compared, 217
identical, the 7 permitted-edit files matching their recorded hunks and digests, no file missing,
added or unexplained; 4 teeth tripped), `frozen-physics` G0′ PASS (77 model files, 76 identical,
`pulse.py` the one approved difference; 4 teeth tripped). `ALL GATES PASS`.

### 2.2 Verification of Part 1 before any run

`harness_survey.py --import-walk`: 55 modules, 0 failures (57 at A72's tip: the two retired
modules). `--selfcheck`: PASS, 7/7 (composition, rungs, capability, provenance, data, run path,
stage provenance), 37 s wall. `--gates`: **30 gates and 5 measurement stages, 152 teeth** — the
same registry as A72's tip: B3's stage was never registered, A66 and the hand-over add and remove
no tooth. `--jobs all` on the record-less tree at `4ca8cff5`: 20 distinct jobs composable (the
prerequisites — every dependent gate says "not composable yet" by name until a reference record
exists, as A72 §10 says it will), 0 shared, **`--resume` would keep 0**.

## 3. Part 2 — the press, in sequence

Everything below ran from the worktree's repository root with
`/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python`, on a clean tree. The worktree's `runs/`
held **only** `gates/switch_neutrality/before/` (6 records at `fd480aff`, the kept capture — never
re-made), `input_files/`, `artifacts/teeth.json` and `census/` (6 census-2 records at `47be2b0d` /
`61473c1d`, both entries, each with its tree stamp) before step 1. Logs are under
`runs/_press_logs/` (untracked, as every run artifact is).

| step | command | at | result |
|---|---|---|---|
| 1 | `--selfcheck` | `4ca8cff5` | PASS 7/7 |
| 1 | `--jobs all` | `4ca8cff5` | 20 distinct jobs (the prerequisites only — every dependent gate "not composable yet" until a reference record exists), 0 shared, **`--resume` would keep 0** |
| 2a | `--gate all --resume --census-entry evaluation` | `4ca8cff5` | 15 gates PASS (every 0-run gate, the four artifact gates, G7, G2, G3/G3c), **crashed inside G4** after 41 runs — §4.1. `--resume` was given so that the census stage keeps the 6 seeded census-2 records (it did: "resumed (a matching census is already on disk, its record census-2 at 47be2b0d)"); on the empty pool it kept nothing else |
| — | fix `gate_audit.py` line 482, commit | `0677a9b3` | one line; §4.1 |
| 2b | `--jobs all` | `0677a9b3` | 118 distinct jobs composable, 42 shared, **`--resume` would keep 38** (the pool records of 2a; G4's doctored jobs not yet composable) |
| 2c | `--gate all --resume --census-entry evaluation` | `0677a9b3` | 26 gates PASS, **G8 FAIL**, chain stopped there (`exit=1`); 95 runs made |
| 2d | `--gate tally_contracts --resume`, `--gate recomputation --resume`, `--gate run_kind_separation --resume`, `--gate stage_provenance --resume` | `0677a9b3` | PASS 195/0, PASS 2 066/0, PASS 178/0, PASS 16/0; 0 PROCESS runs; §4.2 |
| 3 | `--measure all --resume` | `0677a9b3` | 5 stages: `exclusion_review`, `gate_table`, `recomputed_tables`, `tally_evaluation`, `tally_optimisation`; `exit=0` |
| 3 | `--artifacts all` | — | **not run**: the four artifact stages ran as gates inside `--gate all` (`artifacts_check`, `artifacts_derive_inputs`, `artifacts_census`, `artifacts_per_run`, all PASS) and nothing reads `runs/artifacts/*.json` (grep over `plan_tables.py`, `registry.py`, `gates.py`) |
| 3 | `--plan-tables write`; `--plan-tables check` | `0677a9b3` | 131 tables, 3 932 cells, 1 797 lines replacing 1 797; check clean (`exit=0`) |
| 3 | `--selfcheck` | `0677a9b3` | PASS 7/7 |
| 4 | `run_stamp_survey.py --json` | `0677a9b3` | §5 |
| 4 | `--jobs all` | `0677a9b3` | 126 distinct jobs, 242 declarations, 42 shared, `--resume` would keep 126; §6 |
| 5 | `PROCESS_diff.py --markdown`; `copy_gates.py all` | `0677a9b3` | the copy's diff: `module_solve.py` 15 hunks, every one claimed by an annotation (the path-constant hunk reads `YSTATE_MODULE_PATH -> harness/child/ystate.py`), 0 `UNEXPLAINED`; `copy_gates.py all` runs inside `--gate all` as `g0prime`, `copy_identity`, `edit_behaviour` — all PASS |
| 6 (after the ruling, §4.4) | fix `gate_predicate_mode.py` + `exclusion_review.py`, commit; `--gate predicate_mode --resume`; `--measure gate_table --resume`; `--measure exclusion_review --resume`; `--plan-tables write`; `--plan-tables check`; `--selfcheck` | `b485bf4c` | G8 **PASS**, 0 runs, 27 kept; gate table **30 PASS, 0 FAIL; 152/152**; review lists the two names as KEPT (12/12 leaves, 0 equal — they differ by construction); §4 re-rendered (2 lines changed: G8's row and the headline), check clean; selfcheck PASS |

**Wall clock, as context, 3 workers:** press 2a 16:34 → ~16:38 (aborted); press 2c 16:39:39 →
16:54:16 (14.6 min for 95 runs); steps 2d–3 a further few minutes. Not evidence.

## 4. The gate table

Every row from the `gate_table` stage record (`runs/gates/gate_table/measurements.json`), rendered
into `EXPERIMENT_PLAN.md` §4 by `--plan-tables write`; "runs read" from each verdict's
`runs_provenance` as the runner printed it. The verdict commit is `0677a9b3` for every gate.

| gate | plan | verdict | compared / mismatched | teeth | runs read |
|---|---|---|---|---|---|
| `g0prime` | G0′ | PASS | 77 / 1 (`pulse.py`, approved) | 4/4 | — |
| `copy_identity` | — | PASS | 224 / 7 (the permitted-edit files, hunks and digests matching) | 4/4 | — |
| `edit_behaviour` | — | PASS | 3 / 0 | 1/1 | — |
| `self_containment` | — | PASS | 52 files / 0 | 1/1 | — |
| `composition` | — | PASS | 42 / 0 | 7/7 | — |
| `rungs` | — | PASS | 98 / 0 | 3/3 | — |
| `provenance` | — | PASS | 4 / 0 | 4/4 | — |
| `data` | — | PASS | 17 / 0 (16 files + `child/ystate.py`) | 6/6 | — |
| `run_path` | — | PASS | 12 / 0 | 12/12 | — |
| `resume_identity` | — | PASS | 35 / 0 (22 Job fields; 13 by-design pairs, 10 must differ, 3 agree) | 5/5 | — |
| `capability` | — | PASS | 55 / 0 | 5/5 | — |
| `artifacts_check` | — | PASS | 95 / 0 | 3/3 | — |
| `artifacts_derive_inputs` | — | PASS | 2 / 0 | 4/4 | 2 baselines at `4ca8cff5` (`runs/input_files/`) |
| `artifacts_census` | — | PASS | 81 / 0 | 5/5 | 3 census-2 records kept at `47be2b0d` |
| `artifacts_per_run` | — | PASS | 16 / 0 | 2/2 | (reads the census) |
| `record_completeness` | G7 | PASS | 173 / 0 (90 + 83 declared fields) | 9/9 | 2 — 2 at `4ca8cff5` [resumed] (the tooth's fresh re-make is at `0677a9b3` on disk) |
| `prime_map` | G2 | PASS | 5 026 / 0 | 2/2 | 15 — 15 at `4ca8cff5` [resumed] |
| `cold_chain` | G3 / G3c | PASS | 60 / 0 (244/124/240/218 reproduced) | 4/4 | 19 — 19 at `4ca8cff5` [resumed] |
| `audit_restriction` | G4 | PASS | 12 / 0 (13 doctored runs) | 6/6 | 21 — 13 at `0677a9b3`, 8 at `4ca8cff5` [resumed] |
| `entry_and_warm` | G6 | PASS | 6 717 / 0 | 3/3 | 19 — 15 at `0677a9b3`, 4 at `4ca8cff5` [resumed] |
| `switch_composition` | G5 | PASS | 141 / 0 | 3/3 | 6 — 6 at `0677a9b3` [resumed] |
| `switch_neutrality` | G1 | PASS | 54 144 / 0 (2 825 values + 51 319 lines) | 9/9 | 6 — 6 at `0677a9b3` [resumed]; before capture at `fd480aff` |
| `reproduction` | GR | PASS | 256 / 0 | 8/8 | 29 — 26 at `0677a9b3`, 3 at `4ca8cff5` [resumed] |
| `output_path` | G9 | PASS | 3 879 / 0 | 4/4 | 17 — 17 at `0677a9b3` [resumed] |
| `written_file_gap` | — | PASS | 42 / 0 | 4/4 | 12 — 12 at `0677a9b3` [resumed] |
| `predicate_mode` | G8 | **FAIL** at the press (`0677a9b3`) → **PASS** at `b485bf4c` (§4.4) | at the press 8 176 / **24** (8 092 values, 24 differing; 84 lines, 0); after: 8 152 / 0 (8 068 values, 84 lines) | 4/4 | 27 — 24 at `0677a9b3`, 3 at `4ca8cff5` [resumed], both times |
| `tally_contracts` | — | PASS | 195 / 0 (451 in the table's sum) | 10/10 | 25 — 25 at `0677a9b3` [resumed] |
| `recomputation` | — | PASS | 2 066 / 0 | 9/9 | 25 — 25 at `0677a9b3` [resumed] |
| `run_kind_separation` | — | PASS | 178 / 0 (147 records under `runs/`, 31 in the tally's sources) | 6/6 | 25 — 25 at `0677a9b3` [resumed] |
| `stage_provenance` | — | PASS | 16 / 0 | 5/5 | — |

**At the press: 29 PASS, 1 FAIL, 0 not run; 152 of 152 teeth tripped** (the first §4 render's own
line). **Final, after §4.4: 30 PASS, 0 FAIL, 0 not run; 152 of 152 teeth tripped** (the §4 render
at `b485bf4c`).

### 4.1 The interruption — a `NameError` in G4's body, and what was done

At `4ca8cff5` the first press reached G4 (`audit_restriction`), made its 13 doctored runs, and
crashed composing the per-row checks: `gate_audit.py:546`, `NameError: name 'excluded_keys' is not
defined`. `git log -S` places the cause in A72's B1 commit `b3144430`, which renamed the assignment
at line 482 to `_excluded_keys` and left the two reads at 546 and 570 on the old name. G4 was among
the ten gates A72 §9 item 4 lists as changed-but-unpressed, and this press was the first to run its
body — rule (xiii)'s case exactly, one task later than it should have been caught. **Done:** the
assignment restored to `excluded_keys` (one line), a scan of every function in the package for a
name read but never bound (an `ast` walk, `$TMPDIR/undefined_names.py`, not committed: it found
only `__file__`), commit `0677a9b3`, `--jobs all`, then `--gate all --resume`. No run was executing
between the crash and the commit (the runner had exited with `exit=1`; the log is kept as
`runs/_press_logs/gate_all_aborted_at_4ca8cff5.log`). **Why resume rather than start over:**
amendment 15 — a run is re-made only where the change alters what the gate reads; a gate-module fix
alters no record, and the 38 pool records at `4ca8cff5` were complete under the contract
(`--jobs all` said it would keep exactly those 38, and it did). **Cost of the choice:** the
population sits at two commits, which every verdict that read both states in its `runs read` line
and its NOTE, and which §5's stamp survey shows. **Reversal:** `rm -r runs/gates/_runs
runs/gates/<every gate but switch_neutrality>` and one more `--gate all --resume` at `0677a9b3`
(~136 runs, ~20 min at 3 workers) gives a one-commit population; nothing in Part 1 changes.

### 4.2 The four gates after G8

`--gate all` stops at the first failed gate ("A failed gate is a result, not an obstacle"), so
`tally_contracts`, `recomputation`, `run_kind_separation` and `stage_provenance` — the four 0-run
gates after G8 in the derived order — had no verdict. Each was pressed alone with `--resume`; each
reads records and starts no PROCESS run; all four PASS with the counts in the table. This is not a
re-press of G8 and changes nothing G8 read.

### 4.3 G8's FAIL, measured

The identity check (2) of G8 compares each pair of runs — one arm, configuration and seed under the
`frozen` and the `mixed` ruler — value for value where no predicate evaluation decided differently.
Over the 12 pairs, 0 pairs had a decisive evaluation, so all 12 must be bit-identical; **each of the
12 differs in exactly 2 of its 626–718 record values**, the same two every time:

```
DIFFERS job_digest: '8924999e…' -> '2f8e21f6…'
DIFFERS job_identity.predicate_mode: 'frozen' -> 'mixed'
```

0 of 84 output-file lines differ; 143 predicate evaluations were observed on both rulers; the
binding set (3) lists 66 component events, none `held`, none `changed`; GR's neutrality check (1)
PASSes. The two names are A72's identity stamp (rule (xiv)): `predicate_mode` is a `Job` field, so
it is in `job_identity`, and `job_digest` is a function of the identity. They are the setting being
varied under the pool's own spelling — the same thing G8's `PREDICATE_PAIR_EXCLUSIONS` already
excludes six ways (`campaign_predicate_mode`, `switches_asked.predicate_mode`,
`env_architecture.env_PROCESS_ARCH_PREDICATE`, `resolved_switches.…PREDICATE_MODE`,
`coupling_state_provenance.predicate_mode`, `exit_audit.predicate_mode`). A72 added the two names to
G1's conditional table (where the two captures are the *same* job and must agree) and not to G8's
(where the two sides are *different* jobs by construction, and G8 was not pressed).

**Not done on this task's own authority** — a gate-table change after a press that makes a failed
gate pass is a ruling, not an implementation detail. Everything G8 measured other than the stamp of
its own variable was 0 differing. Put to the orchestrator; ruled and done in §4.4.

### 4.4 The ruled fix, and G8 re-pressed over its kept records

**The ruling** (orchestrator, 2026-09-14, implementation-level under D24/D27, after verifying the
G8 verdict and the fix commit's diff): add the two names to `PREDICATE_PAIR_EXCLUSIONS`; re-press
G8 over its kept records; re-render §4; keep the FAIL in the history as a measured result.

**Done, `27c9dc8d` + `b485bf4c`** (no run executing; nothing under `child/` changed; committed
before the press): in `gate_predicate_mode.PREDICATE_PAIR_EXCLUSIONS`'s "the mode stamps -- the
thing being varied" block, `job_identity.predicate_mode` ("the pool's stamp of the setting being
varied — rule (xiv): `predicate_mode` is a `Job` field, so it is in the identity") and `job_digest`
("sha256 of the identity, which changes whenever any identity field does — here exactly because
`job_identity.predicate_mode` does; excluded on the condition that this gate's pairs differ in that
one field and no other, which the identity block's other leaves — all compared — hold; that two
distinct jobs carry distinct digests is gate `resume_identity`'s claim, not this one's"). The first
commit alone was refused at import by `exclusion_review._assert_every_name_is_classified` ("2 of gate
G8's excluded name(s) carry no declared kind") — the review's own guard against an unclassified
exclusion, working; `PREDICATE_PAIR_KIND` gained the two names under *the setting being varied, or a
stamp of it* in the second commit. **The class of the fix is A62's:** an exclusion for a field the
pair differs in *by construction* (there, the instrument stamp across two instruments; here, the
identity stamp across two rulers), conditional on the construction and reviewed as a named row.

**G8 at `b485bf4c`: PASS.** `--gate predicate_mode --resume`: **0 `rc=` lines, 27 records resumed**
("complete record of this job kept"), runs read 27 — 24 at `0677a9b3`, 3 at `4ca8cff5`; 12/12
pairs bit-identical; **0 of 8 068 record values and 0 of 84 output-file lines differ**; 240 values
excluded (216 before + the 24 that were the FAIL — the count moved from "differing" to "excluded by
name", and nowhere else); GR's neutrality check PASS; 4/4 teeth tripped (the `one_ulp` tooth: 1 of
664 compared values, so the pair is still compared value for value).
`--measure exclusion_review --resume`: the two names appear in G8's table as *KEPT*, 12 leaves on
each side, 0 equal — the shape the reason claims; G8's set 17 → 19 names. `--measure gate_table
--resume`, `--plan-tables write` (2 lines of `EXPERIMENT_PLAN.md` changed: G8's row and the
headline), `--plan-tables check` clean, `--selfcheck` PASS.

**Reversal:** `git revert b485bf4c 27c9dc8d`, `--gate predicate_mode --resume` (0 runs), and G8 reads
FAIL 24/8 092 again.

## 5. The stamp survey

`run_stamp_survey.py --json runs/_press_logs/stamp_survey_after.json` over every `metrics.json`
under `runs/` (147):

| commit | records | what |
|---|---|---|
| `0677a9b3` | 96 | 89 shared-pool jobs, G1's 6 after-capture runs, 1 GR tooth fixture (`reproduction/_teeth/missing_key/metrics.json`, a doctored copy the tooth writes) |
| `4ca8cff5` | 39 | 37 shared-pool jobs from the aborted press (38 kept; G7's tooth re-made one fresh at `0677a9b3`), 2 lifted-input baselines (`runs/input_files/`) |
| `fd480aff` | 6 | G1's before capture, kept, never re-made |
| `47be2b0d` | 3 | census-2 records, `evaluation` entry, kept by the census stage's own resume rule |
| `61473c1d` | 3 | census-2 records, `optimisation` entry, kept (not read by this press) |

Every record made by this task is at one of the two press commits; no record at any other
commit except the three kept sets above, each of which is a declared exception (rule (ii); amendment
17 (a)'s census path). No record is unstamped.

## 6. The population and the shared pool's saving

**Made:** 136 PROCESS runs (41 + 95 `rc=` lines in the two press logs): 126 distinct pool jobs,
6 G1 after-capture runs, 2 lifted-input baseline evaluations, 2 G7 fresh tooth re-makes (one per
press, the second replacing the first's record). **On disk:** 147 records (§5).

**Per gate (distinct jobs in its declared set, references included), from `--jobs <gate>`:**
G7 2 · G2 15 · G3/G3c 19 · G4 21 · G6 19 · G5 6 · G1 6 (+6 kept) · GR 29 · G9 17 · `written_file_gap`
12 · G8 27; the three 0-run readers 25 each. Sum over the run-making gates: 167 declarations; over
all 30: 242. **Distinct: 126.** 42 jobs are read by more than one gate — 14 by two, 13 by four, 12
by five, 3 by six (the cold `A0` seed-0 references, read by G2, G3, G4, G6, GR and G8).

**The saving, two ways, each with what it counts.** (a) Against the per-gate layout at A71's tip —
152 runs per full press, A72 §7's count — the pool's 126 plus G1's 6 after-capture runs is **132: 20
fewer**, exactly A72's projection, so the identity rule shared what A72 said it would and nothing
more. (b) Against A67's **184-record** population (the seed A72 was given: every record under
`runs/` at 8 commits) the tree now holds **147 records: 37 fewer** — but 184 counted B3's 11
diagnosis records and B5's 6 contrast runs, both retired by D27 rather than shared, and 147 counts
the kept census and before-capture records; (a) is the pool's own figure, (b) is the tree's.

## 7. The §4 changes

Rendered from the records at `0677a9b3`, `4ca8cff5`, `fd480aff` (was: seven commits `09cc9f3e` …
`fd480aff`). Gate count 30 (was 29 rows: `resume_identity` new since the last render); teeth **152 of
152** (was 148 of 148); the gate table's line reads **29 PASS, 1 FAIL, 0 not run** (was 29 PASS, 0
FAIL). `run_kind_separation`'s population 184 → 147 records; `recomputation` over 25 records (was
36 — the population marker: A64's 36 included G6's pairing runs at three commits, this press's tally
sources are 25 records at one commit). 131 tables, 3 932 cells (A64: 3 927). `--plan-tables check` is
clean.

## 8. D27's closing ledger

The twenty survey items and A66, where each landed. "Lines" is `harness_survey.py` §1's `ALL`
total.

| item | landed in | note |
|---|---|---|
| A1 split `gates.py` | A70 | six modules |
| A2 retire `predicate_counters`/`attempts` stages | A70 | `records.sweep_decomposition` |
| A9 register `copy_identity`/`edit_behaviour` | A70 | +1 tooth |
| A3 `--tree repository` | A71 | |
| A4 `crosscheck_previous` | A71 | |
| A5 `--lifted-from` | A71 | |
| A6 `REFUSAL_MARKERS` | A71 | |
| A7 five unreferenced definitions | A71 (4) + **A73 (1)** | `predicate.provenance_of` here |
| A8 one name, one meaning | A71 | |
| A10 one of `-P`/`PYTHONSAFEPATH` | A71 | rule (iii)'s prose is C2, the user's |
| A11 stale README prose | A71 | |
| A12 the rules table | A71 | Appendix A.1 |
| B1 the shared run pool | A72 | measured here: 126 jobs, 20 of 152 saved |
| B2 G4 resumes | A71 | |
| B3 retire the diagnosis instrument | **A73** | §2 |
| B4 retire the allowance | A72 (harness side) + **A73 (child side)** | §2 |
| B5 retire `output_path_measurements`/`capture_contrast` | A71 | |
| B6 fewer teeth | A71 | 158 → 148; A72 +5 (`resume_identity`), −1 (`run_path`) → 152 |
| B7 `--reference extract/verify/teeth` | A71 | |
| B8 `self_containment` a gate | A71 | |
| A66 `ystate.py` into `child/` | **A73** | §2; G1 straddle PASS, G0′/`copy_identity` PASS |
| (I-23, not a survey item) | A72 | closed by construction; every record here carries `job_digest` |

**Lines:** 47 728 at A68 (before D27) → 46 318 (A71) → 47 783 (A72) → **45 390 (A73)**. Net −2 338
over the programme; A72 added 1 465 (the pool, the identity gate) and A73 removed 2 393.
**Teeth:** 158 → 152. **Gates:** 28 + 7 stages (A70) → 30 + 5 stages. **PROCESS runs per full
press:** 152 (A71's tip) → 132 measured (§6). **Tier C (C1–C3) stays open**, unruled.

## 9. Autonomous decisions, each with its reversal

1. **`--resume` on the press, though the pool was empty.** So that the census stage keeps the six
   seeded census-2 records (its own resume rule; without the flag it re-takes them — PROCESS runs)
   and so that the after-crash continuation was one command. On an empty pool it kept nothing else
   (`--jobs all`: 0). *Reversal:* none needed; the flag decided nothing the record did not.
2. **Continuing after the G4 crash by fix-and-resume rather than fix-and-start-over** (§4.1).
   *Reversal:* delete the pool and press once more at `0677a9b3`.
3. **Not fixing G8's exclusion table on this task's own authority** (§4.3) — put to the
   orchestrator, who ruled yes; done in §4.4 with its reversal there.
4. **Pressing the four post-G8 0-run gates individually** (§4.2). *Reversal:* delete their four
   verdict directories; the gate table then shows them "not run".
5. **`--artifacts all` not run** (§3): its four stages ran as gates and nothing reads its stage
   records. *Reversal:* run it; it writes `runs/artifacts/*.json` and nothing else.
6. **Item 13's manifest shape**: `tree_git_head` = the records' commit when one, `None` when two
   (so `_straddle` refuses to name a side), plus `records_git_heads` and `pressed_at_git_head`.
   *Reversal:* `git revert 4ca8cff5`.
7. **`stamp_capabilities_absent` renamed `stamp_driver_counters_null`**, the brief's "or what it
   does". *Reversal:* rename back; two callers.
8. **`harness/data/PROVENANCE.json` re-recorded** for A66 (the `name` label; the stale
   `harness/selfcheck.py` path in its `what` prose came right as a side effect). The module's bytes,
   hunks and digest are unchanged. *Reversal:* `git checkout 2969fe66 -- harness/data/PROVENANCE.json`
   and the label reads the old path.
9. **The `on_ready_to_sweep` hook removed from `child.exit_audit`** with B3: the trace was its only
   caller. *Reversal:* part of `git revert 82ea0377`.
10. **`EXPERIMENT_PLAN.md` line 589** names the new path (outside the rendered §4). *Reversal:* one
    line.
11. **The `_teeth/missing_key` fixture record** GR writes under `runs/gates/reproduction/` is counted
    in the stamp survey as a record at `0677a9b3` and is a doctored copy, not a run. Left where the
    gate writes it; noted so that 147 ≠ 146 is not read as a stray run.

## 10. Limits

- The population sits at two commits (`4ca8cff5`, `0677a9b3`). **Accepted by the orchestrator's
  ruling of 2026-09-14, not re-pressed.** The evidence: `git show --stat 0677a9b3` lists exactly one
  file, `arch_surgery/MDA_partitioning_experiment_v4/harness/gates/gate_audit.py`, 1 insertion, 1
  deletion — gate code, nothing under `harness/child/`, nothing under `PROCESS/`, nothing the pool
  composes into a job — so records made at the two commits are of the same driver and the same child,
  and every verdict that read both states both. §4.1's reversal stands for a reader who wants one
  commit anyway.
- G8's verdict record on disk is the `b485bf4c` one; the FAIL at `0677a9b3` survives in
  `runs/_press_logs/gate_all_resume_at_0677a9b3.log` and in §4.3, not as a record.
- The saving in §6 (a) is against A72's count of the A71-tip layout, not against a re-press of that
  layout; (b) is a record count over two differently composed trees.
- The wall clock (§3) is one machine, one afternoon, 3 workers; it is context.
- B3's `by_design` clause in `harness_survey.py` was removed; the survey's redundancy count was not
  re-baselined against A68's, since the diagnosis records are gone from every tree that would be
  surveyed.
- No new trap was met that TRAPS.md does not already hold; the G4 crash is rule (xiii)'s existing
  shape (amendment 23), not a new one.

## 11. Commits

| commit | what |
|---|---|
| `82ea0377` | B3 |
| `7d333677` | A66 (the move, the literal, `copy_gates.py`, both provenance records, CHANGES.md §4.2.1 and §5, README, PROCESS_diff annotation) |
| `731a6be8` | A72's hand-over, child side; `predicate.provenance_of` |
| `4ca8cff5` | improvement item 13 — **the first press commit** |
| `0677a9b3` | `gate_audit.py` `excluded_keys` — **the second press commit** |
| `6280e220` | `EXPERIMENT_PLAN.md` §4 render (29/1); this report |
| `27c9dc8d` | G8's two exclusion rows (§4.4) |
| `b485bf4c` | `exclusion_review.PREDICATE_PAIR_KIND` classifies them — **G8's re-press commit** |
| (this report's second commit) | §4 re-render (30/0); this report updated |

## 12. What the documents should gain (not edited by this task)

**The queue.** A66 → MERGED (carried by A73); A73's row → its outcome (30/30 after the ruled
exclusion fix; the G4 crash and the G8 FAIL at the press named as results); D27 → discharged: the
twenty items and A66 have landed (§8) and the one press ends at 30 PASS, 0 FAIL, 152/152. The two
orchestrator rulings of §4.4 and §10 (the exclusion fix; the two-commit population accepted) are
implementation-level under D24/D27 and should be recorded in the change log, not as D-rows.

**The harness plan.** An amendment closing D27 with §8's ledger; the rules table's row for
rule (xiii) gains the measured instance: a gate left unpressed by the task that changed it (A72,
G4) crashed one task later. Rule (xiv)'s text should say that a gate comparing two *different*
jobs on purpose (G8) excludes the identity fields that differ by construction, while a gate comparing
the *same* job at two commits (G1) requires them equal — the distinction A72 §4 drew for G1 and did
not carry to G8.

**TRAPS.** Nothing new; the G4 and G8 findings are amendment 23's shape. One candidate sentence for
rule (xiv)'s amendment rather than a trap: *a schema field added to every record reaches every gate
that compares two records, and each such gate's exclusion table needs the decision "same job — must
agree" (G1) or "different jobs by construction — excluded" (G8) made explicitly.*

**The improvement list.** Item 13 → discharged (`4ca8cff5`). A candidate: a static
never-bound-name scan as a self-check tooth (the `ast` walk in §4.1 found the G4 defect in under a
second and nothing else), since no linter is installed in the environment.


---

## Orchestrator's critical assessment (protocol §5)

*Written 2026-09-14 at the branch tip `bb34cee8`, before the merge. Checks chosen to differ from the
agent's.*

1. **The population, surveyed by me from the pool's records:** 126 records under `runs/gates/_runs/`,
   89 at `0677a9b3` and 37 at `4ca8cff5`, 124 gate-kind and 2 smoke-kind (the run-kind separation
   gate's own positive control, as in every earlier population). Matches the report.
2. **The two-commit population is acceptable on the evidence:** `git show --stat 0677a9b3` is one file,
   `harness/gates/gate_audit.py`, one line; nothing under `harness/child/`, `ystate.py` or `PROCESS/`
   changed between the two press commits, so the driver and the child that made every record are the
   same. Every verdict names both commits. Ruled by the orchestrator under D27; reversal is a 20-minute
   re-press, not taken.
3. **G8's failure and its fix.** I read G8's failing verdict before ruling: 24 differing values over 12
   pairs, field names `job_identity.predicate_mode` and `job_digest` only, 0 output-file lines. The two
   are stamps of the setting the pair varies by construction, the same class as the six already in the
   table. The fix is two exclusion rows and their classification in the review; G8 re-pressed on kept
   records at 0 runs: 12/12 pairs identical, 0 of 8 068 values. The failure and its numbers stay in
   the report as a measured result. The review's import-time refusal of an unclassified exclusion
   caught the first commit — a guard working.
4. **G1 read from its verdict, not the summary:** PASS, 2 825 values compared, 0 differing, a declared
   straddle `fd480aff → 0677a9b3` with the instrument-change exclusion kind. **GR:** PASS, 256
   compared. **Gate table:** 30 rows, all PASS.
5. **The `ystate.py` move, proven through the copy from a third directory on a trial merge onto trunk
   (`605b5af7`):** with `PYTHONPATH` on the copy, `module_solve._ystate_module()` loads
   `harness/child/ystate.py`; `copy_gates.py all` reports ALL GATES PASS after the provenance
   regeneration; the import walk loads 50 modules with 0 failures; the merge is clean (28 files).
6. **Rule (xiii) debt, discharged the hard way.** Two of the ten gates A72 changed without pressing
   failed at this press (G4 by a crash on a renamed name, G8 by an unexcluded stamp). Both are exactly
   what the rule predicts and what a from-scratch press exists to find. The agent's proposed self-check
   tooth for a never-bound name goes to the improvement list.
7. **`--artifacts all` not pressed:** its four stages ran as gates and nothing reads its stage records;
   accepted.

**Approved for merge.** D27's programme is complete at this tip.
