# A70 (simplify-code-moves) — the three code-move items of the simplification survey

> **Document status** — **ARCHIVED at merge, 2026-09-14.** Task **A70 (simplify-code-moves)** merged into `architecture_surgery`
> at `bc53f4d6` (base `3154faa3`). Records relocated to `arch_surgery/idf_probe/runs/A70_runs/` (resumed, none made). The
> orchestrator's critical assessment is the last section. Folder position records lifecycle, not validity (trap T3).

## 1. Verdict in one page

| item | what was done | proof it still bites |
|---|---|---|
| **A1** | `harness/gates/gates.py` (6 948 lines) split along its own `# ----` section markers into six modules; every importer re-pointed to the module that now holds the name (no re-export); the retired stage sections not carried into any module | `self_containment` reported the moved `measurements()` line in `registry.py` as **1 finding, passed False** until the table named the file (§3.2); import walk 55/55; `--gates` listing identical to the baseline bar the two intended differences |
| **A2** | the two stages are gone from the registry, the module command line and `--gates`; their one unique construction, the sweep-decomposition identity, is now `records.sweep_decomposition` / `records.assert_sweep_decomposition`, asserted by `records.assert_usable` on every finished record; `attempts` removed from `records.AUDIT_POSITION_AFTER_RUN_CALLERS` | the identity holds on all **160 of 184** records the contract accepts today (the 2 with residual 1 are already refused as incomplete, §4.2); new `run path` tooth **tripped** (5 503 against 5 499 + 2 + 1); a job naming caller `attempts` is refused by `records.assert_audit_position_allowed` and by `pool.environment_for` (§4.3) |
| **A9** | `copy_identity` (4 teeth) and `edit_behaviour` (**1 new tooth**) registered as 0-PROCESS-run gates beside `g0prime`, loading `PROCESS/copy_gates.py` by path; `copy_gates.py all` still runs every criterion and writes no record of its own | `--gate copy_identity` PASS 224 compared / 7 mismatched (the 7 permitted-edit files) 4/4 teeth; `--gate edit_behaviour` PASS 3/0, 1/1 — the doctored copy raised `FileNotFoundError` and the gate said FAIL (§5.3) |

**Verification** (§6): `--selfcheck` PASS, 7 checks, **54 → 55 teeth**; import walk 55 modules, 0
failures; registry **26 gates + 9 stages → 28 gates + 7 stages**, every other name unchanged;
`--gate g0prime --resume`, `copy_identity`, `edit_behaviour`, `recomputation --resume` (2 066 / 0),
`run_kind_separation --resume` (215 / 0) all PASS; `--measure gate_table --resume` then
`--plan-tables write` then `--plan-tables check` IDENTICAL (1 795 lines); §4.1 gains two rows and
reads **28 PASS, 158 of 158 teeth** (was 26, 153/153). Stamp survey before and after: **184 run
records, 0 changed commit, 0 disappeared, 0 new — this task made no PROCESS run.**

## 2. Commits

| commit | content |
|---|---|
| `4408994e` | A1: the split, importers re-pointed, `DECLARED_OUTSIDE_REFERENCES["registry.py"]`; A2 part 1: the two stage sections (old lines 2 944–3 846) dropped with the registry entries and the module command line's branches |
| `1b9c7ca4` | A2 part 2: the identity into `records.py`, the `run path` tooth, the `attempts` row out of the callers table |
| `68bad455` | A9: the two gates in `gates.py`, registered and ordered in `registry.py`; `copy_gates.py` gains `root=` on `check_edit_behaviour`, `run_edit_behaviour_tooth`, and loses `--records` and its record writing |
| `f0889b65` | `harness/README.md` §0, §8, §10.1 |
| `d29f46b5` | `EXPERIMENT_PLAN.md` §4 re-rendered |
| *(this report)* | `A70_simplify_code_moves.md` |

Every verification press of §6 ran at `f0889b65` (the tree with every code change committed; the two
later commits touch the plan's rendered §4 and this report only); the verdict records stamp
`f0889b65`.

## 3. A1 — the split

### 3.1 The move table

*Caption: one row per section of the original `gates.py` at `3154faa3`, in file order, with its
original line range and where its lines now are. "lines" is the original section's length including
its `# ----` header. The new modules' totals include their own docstring, imports and the
`gate(campaign)` constructor added for the registry (see 3.3).*

| original section (its own `# ----` title) | lines | now in |
|---|---|---|
| module docstring, imports, framework aliases | 1–103 (103) | rewritten per module; the aliases `Gate`, `Tooth`, `Check`, `Measurement`, `GateError`, `GATES_SUBPATH` stay in `gates.py` (the plan names `gates.Gate`) |
| G0' — the physics stays frozen in the copy | 104–213 (110) | `gates.py` |
| G1 — switch neutrality, and *the earlier capture's vocabulary* | 214–1 987 (1 774) | **`gate_neutrality.py`** (1 844 total) |
| G9 — the output path writes the state the solve handed over | 1 988–2 488 (501) | **`gate_output_path.py`** |
| the output path, measured — not a gate | 2 489–2 943 (455) | `gate_output_path.py` (1 048 total) — built on G9's run directory and helpers; B5 (A71) retires it |
| the per-sweep overhead, counted (`predicate_counters`) | 2 944–3 389 (446) | **retired** (A2); `_reconcile_sweeps` → `records.py` |
| the retry ladder, per attempt (`attempts`) | 3 390–3 846 (457) | **retired** (A2) |
| G8 — the convergence predicate's trial, and `_load_ystate` | 3 847–4 589 (743) | **`gate_predicate_mode.py`** (941 total, with `print_predicate_mode`) |
| `_plan_gates` | 4 591–4 703 (113) | `registry.py`, as a dict of each module's `gate(campaign)` |
| the entry reference every warm gate is anchored on, `_with_capture` | 4 704–4 815 (112) | `gates.py` |
| gate GR, wrapped into the framework | 4 816–4 924 (109) | `gates.py` |
| the harness's own checks, promoted | 4 925–5 214 (290) | `gates.py` |
| the exclusion sets, reviewed | 5 215–5 769 (555) | **`exclusion_review.py`** (613 total) |
| self-containment, measured rather than asserted | 5 770–6 010 (241) | `gates.py` |
| the tally / the analysis / the chain (registry glue) | 6 011–6 142 (132) | `registry.py` |
| the measurement stages (`measurements()`) | 6 143–6 237 (95) | `registry.py` |
| the registry | 6 238–6 317 (80) | `registry.py` |
| the gate table, `gates_only`, `GATE_ORDER`, `ordered_gate_names` | 6 318–6 598 (281) | `registry.py` |
| `print_predicate_mode` | 6 599–6 714 (116) | `gate_predicate_mode.py` |
| `print_verdict`, `main` | 6 715–6 948 (234) | `registry.py` (906 total) |

Resulting sizes: `gate_neutrality.py` 1 844, `gates.py` 1 158 (after A9's additions), `gate_output_path.py`
1 048, `gate_predicate_mode.py` 941, `registry.py` 906, `exclusion_review.py` 613 — total 6 510 for
6 948 original lines (−892 retired, +454 module headers, `gate()` constructors and A9). **One module
is above the survey's ≤ 1 800 target**: `gate_neutrality.py` at 1 844, because G1's section alone is
1 774 lines and the exclusion tables stay with it whole and unchanged, as briefed. Splitting the
tables from the comparison machinery would put the thing G1 reads in a different file from G1; not
done.

The exclusion tables `ALWAYS_EXCLUDED`, `FIELDS_ADDED_BY_A_DRIVER_CHANGE`,
`FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE` (and `CONDITIONAL_WITNESS`, `INSTRUMENT_CHANGE_KIND`,
`VOLATILE_RECORD_PATHS`, `VOLATILE_MFILE_KEYS`) moved with G1, byte for byte. Every `runs_under`
tuple (`("switch_neutrality/after",)`, `("output_path/runs",)`), every `reads_from`, the
`REPRODUCTION_TEETH` list and every record path travelled unchanged (T12).

### 3.2 Every scanner string that held a path or module name, and the tooth that proves it still bites

| scanner | string | what happened at the move |
|---|---|---|
| `gates.self_containment` — `DECLARED_OUTSIDE_REFERENCES`, keyed by **file name** | `"gates.py"` (the stage's own declaration) stays valid: `FORBIDDEN_DIRECTORIES` and the stage stay in `gates.py` | the `measurements()` registry entry for `self_containment` carries the sentence *"…invoked as a subprocess into, idf_probe/ or fixedpoint/"* in an executable string; it moved to `registry.py`, a file the table did not name. **Run before the table was edited: 53 files, 44 hits, 13 executable, `n_findings` 1 (`harness/gates/registry.py:275`), `passed` False.** The table gained `"registry.py"` with the reason; run again: 53 / 44 / 13 / **0 findings / 0 imports / passed True**. That is the scanner biting on the move, as A65 §4 said it would |
| `analysis.FORBIDDEN_IMPORTS` and the `recomputation` independence tooth | five `harness.measurement.*` names | unaffected by a move inside `gates/`; the tooth still names `['harness.measurement.stats', 'harness.measurement.stats.median', 'harness.measurement.tables', 'harness.measurement.tally_optimisation']` (`--gate recomputation`, §6.4). `analysis.py`'s two lazy imports of the registry re-pointed to `harness.gates.registry` |
| `harness_survey.py` (A68's census script) | `HARNESS / "gates" / "gates.py"` for its section census; `from harness.gates import gates` for the registry | the path still exists (the file is smaller); the import re-pointed to `registry`. The script's "gates.py by section" number now measures the remainder; anyone re-running A68's census reads a different `gates.py` |
| `framework.py:591` docstring | `:func:`harness.gates.gates.registry`` | → `harness.gates.registry.registry` |
| usage lines `python -m harness.gates.gates …` | 11 in the old docstring, 1 in the retired `attempts` message | the module command line (`main`, `print_verdict`) moved to `registry.py`; usage lines are `python -m harness.gates.registry …`; the two retired stages' branches and `choices` are gone. Verified: `python -m harness.gates.registry --help` |

### 3.3 Imports — who holds what now

Every external use resolves via the module that now holds the name; **no re-export was needed**, because
no scanner reads a `harness.gates.gates.<name>` string (grep, §6.7).

| importer | before | after |
|---|---|---|
| `experiment_runner.py` | `gates_mod.{gates_only, ordered_gate_names, measurements, measurement_dependencies, registry, print_verdict, capture_neutrality}` | `registry_mod.*`; `neutrality_mod.capture_neutrality`; `gates_mod.{REPRODUCTION_LIFTED_FROM, CENSUS_ENTRY, GATES_SUBPATH, GateError}` stay |
| `chain.py` (2 lazy) | `.gates.gates` | `.gates.registry` |
| `measurement/analysis.py` (2 lazy) | `harness.gates.gates` | `harness.gates.registry` |
| `gates/selfcheck.py` (1 lazy) | `harness.gates.gates` | `harness.gates.registry` |
| `gates/gate_prime.py`, `gates/gate_audit.py` | `gates_mod.excluded_by_the_per_run_nodes` | `gate_output_path.excluded_by_the_per_run_nodes`; `gates_mod.{GATES_SUBPATH, entry_references, CENSUS_ENTRY}` stay |
| `gates/exit_audit_diagnosis.py` | `gates_mod.{compare_records, leaves}` | `gate_neutrality` (aliased `gates_mod`) |
| `gates/gate_written_file.py` (lazy), `gate_entry`, `gate_composition`, `gate_records` | `gates_mod.{_with_capture, GATES_SUBPATH, entry_references}` | unchanged — those stay in `gates.py` |
| `harness_survey.py` | `gates.registry`, `gates.ordered_gate_names` | `registry` |

Inside `gates/`: `registry` imports every gate module and is imported by no gate module;
`gate_output_path` and `gate_predicate_mode` import `gate_neutrality` (`_read_record`, `_same`,
`compare_mfiles`, `_mfile_for`, `compare_records`) and `gates` (`_with_capture`);
`exclusion_review` imports the three gate modules. No cycle: the import walk (§6.2) imports each of
the 55 modules in isolation from a directory outside the package.

Each gate module gained a `gate(campaign) -> Gate` (and `gates.py` a `g0prime_gate`,
`reproduction_gate`) holding the `Gate(...)` literal that `_plan_gates` held, moved verbatim — the
pattern `gate_prime.prime_map_gate` and `gate_tally.gate` already used. `_plan_gates` in
`registry.py` is now a dict of eleven calls.

## 4. A2 — the two stages retired

### 4.1 What went

Sections at old lines 2 944–3 846 (903 lines with headers): `predicate_counter_rows`, `_counter_row`,
`_reconcile_sweeps`, `predicate_counter_measurements`, `PREDICATE_PAIRS`, `predicate_pair_rows`,
`print_predicate_counters`; `LADDER_DEMONSTRATION_*`, `ladder_root/jobs`, `capture_ladder`,
`ladder_rows`, `attempt_rows`, `_attempt_row`, `attempt_measurements`, `_ladder_block`,
`print_attempts`. Their registry entries, the `--gates` lines and the module command line's
`predicate-counters` / `attempts [--capture runs]` branches went with them. The runner's `--measure`
choices are registry-driven, so nothing else names them; `plan_tables.py` never rendered either
(grep: 0), so §4 lost nothing.

The retry-ladder demonstration runs (`force_maxcal=2`, three runs at the `after_run` position) were
never made in the relocated set — `runs/gates/attempts/` held `measurements.json` only — so
retiring the capture retired no record. `pool.Job.force_maxcal` and `stats.FORCED_BUDGET_STAMP`
stay: the tally's and `gate_audit`'s *refusal* of a budget-capped record is a population rule
independent of the stage that used to make such records.

Every column the two stages emitted is the tally's — `per_sweep_overhead` (both phases) and
`attempts` (`tally_optimisation`) — and is recomputed by the analysis; `--gate recomputation
--resume` re-made both tally stages by dependency and compared **2 066 cells, 0 mismatched** (§6.4).

### 4.2 The identity, relocated

`_reconcile_sweeps` became `records.sweep_decomposition(record)` (the reconciliation block, same
terms, same `why`) and `records.assert_sweep_decomposition(record, where=)` beside
`assert_attempt_summation`, and `assert_usable` calls it third. The refusal applies to **finished**
records that carry `dispatch_sweeps`; a record that did not finish or has no total is passed over,
as `assert_both_rulers` and `assert_attempt_summation` pass over what does not apply.

Measured over all 184 run records under `runs/` before the change (committed script: the census
below is reproducible from `records.sweep_decomposition` over `runs/**/metrics.json`):

| | count |
|---|---|
| identity holds, block-schedule term | 130 |
| identity holds, analysis-loop term | 46 |
| not checkable (no `dispatch_sweeps`) | 6 (the census records) |
| **residual 1** | **2** — `gates/exit_audit_diagnosis/runs/{large_tokamak_nof,low_aspect_ratio_DEMO}/B3/seed000` |

The two are the diagnosis instrument's B3 records at `3d64625c` (B3 in A73 retires that instrument):
they carry `dispatch_sweeps` 5 500 and `sweeps_per_eval.n_sweeps` 5 499 but **no
`defer_per_run_totals` and no `block_loop_totals`**, so the per-run deferral sweep they spent is not
stamped where the identity looks for it. They are already refused by `assert_complete` (3 declared
fields missing) — `assert_usable` refused **24 of 184** records before this change (6 census
records: no ruler; 11 diagnosis records and 6 G1 `before` captures: incomplete under the current
schema; 1 GR tooth fixture) and refuses **the same 24** after it. The 160 it accepts all satisfy the
identity. So the contract is strengthened and no accepted record changes status; the two tally
populations (36 records) are unaffected, which `recomputation` and `run_kind_separation` confirm.

`assert_usable` is also what the child calls to stamp `completeness` into its own record
(`child/optimise.py:506`, `child/evaluate.py:676`); nothing under `child/` was edited, and a record a
future child makes that fails the identity would stamp `complete: False` with the refusal's
sentence rather than be lost. That is the contract working as `assert_attempt_summation` does.

### 4.3 The teeth

- **New tooth, `run path` self-check**: a synthetic finished record with `dispatch_sweeps` 5 502,
  `block_sweeps` 5 499, `output_loop_sweeps` 2 and one node executed once passes as the baseline;
  with `dispatch_sweeps` 5 503 it must be refused — **tripped** (`RecordError: the sweep total does
  not decompose for a tooth: dispatch_sweeps = 5503, but block_sweeps … = 5499 + output_loop_sweeps
  = 2 + per-run deferral sweep = 1 leaves a residual of 1`). Put in the self-check rather than G7
  (`record_completeness`) because the self-check runs with no PROCESS run and is pressed here; B6
  (A71) is the place to decide which of the two should carry the attempt-summation family of teeth.
- **`records.AUDIT_POSITION_AFTER_RUN_CALLERS`** lost its `attempts` row (3 callers remain:
  `reproduction`, `switch_neutrality`, `written_file_gap`; the self-check's note now reads *"3 declared
  caller(s), every one a registered stage"*). A job asking for `after_run` as caller `attempts` is
  refused at both levels: `records.assert_audit_position_allowed` → `RecordError: … asked for by
  'attempts', which is not a declared caller of it`; `pool.environment_for` → `PoolError` with the
  same sentence. The existing tooth *"an undeclared caller asking for the after_run audit position"*
  covers the mechanism and still trips.

## 5. A9 — the copy's gates on the one button

### 5.1 Registration

`gates.py` gained, beside G0' and in its shape: `copy_identity_body` / `_copy_identity_teeth` /
`copy_identity_gate`, `edit_behaviour_body` / `_edit_behaviour_teeth` / `edit_behaviour_gate`, and
`copy_gates(campaign)` returning the two; `registry.registry` adds them after `_plan_gates`, and
`GATE_ORDER` places them right after `g0prime` (no PROCESS run; ≈ 20 s each). Both load
`PROCESS/copy_gates.py` by path through the same `_copy_gates(campaign)` G0' uses — the criterion is
implemented once. Neither carries a `plan_name`: they are the copy's, not the plan's §3.9's, and
§4.1 lists them among the harness's own (17 now, 15 before).

| gate | body | population | headline pair | teeth |
|---|---|---|---|---|
| `copy_identity` | `check_copy_identity(prov, tree)` | 224 files under `PROCESS/process/` against source commit `f2dc9243` by `git cat-file`, plus the file set; 7 permitted-edit files on digest and hunks | 224 compared / **7 mismatched** — the seven permitted-edit files, each passing on its recorded digest and hunks; the verdict's `note` says so, the way G0' explains its 1 | the criterion's own four, shared through one `run_teeth` call: `one_byte_changed`, `file_removed`, `file_added`, `permitted_file_changed_elsewhere` — all TRIPPED |
| `edit_behaviour` | `check_edit_behaviour(prov, root=tree)` | three arms of one probe: copy with the artifact absent (→ `ArchitectureRefusal` naming `PROVENANCE.json`), source commit with it absent (→ `FileNotFoundError`), copy with it present (→ nothing) | 3 / 0 | **1 new** — `permitted_edit_doctored`, TRIPPED |

### 5.2 `edit_behaviour`'s tooth — a gate, not a measurement, and why

The gate has a criterion (three arms with three required outcomes), so it stays a gate and gets the
tooth the framework requires rather than being demoted to a `Measurement`. The tooth is the one the
brief names: **a doctored permitted edit whose behaviour differs must be caught.**
`copy_gates.run_edit_behaviour_tooth(prov, root)` stages a throwaway copy of `process/` (the
existing `_staged`), replaces the per-run path's `if not NODE_WRITESET_PATH.exists():` in
`process/core/caller.py` with `if False:  # doctored by the edit-behaviour tooth` — anchored on the
following two lines of its own refusal message, because the per-call path one function up has the
same `if` line — and runs `check_edit_behaviour(prov, root=staged)`. The doctored copy raised
`FileNotFoundError` and the gate said **FAIL** (*"the copy raised FileNotFoundError … expected an
ArchitectureRefusal naming harness/data/PROVENANCE.json"*), so the tooth TRIPPED. The real tree is
never modified; `PROCESS/process/` is untouched (`git status PROCESS/` shows `copy_gates.py` only).

To make that possible `check_edit_behaviour` gained `root: Path | None = None` (the copy's root for
the copy-side children; the committed artifacts stay the real tree's). Its criterion is unchanged.

### 5.3 `copy_gates.py`'s own command line

Every command stays (`all`, `copy-identity`, `frozen-physics`, `smoke-import`, `edit-behaviour`,
`provenance`); `all` and `edit-behaviour` now also run the new tooth. **It writes no record any more**:
`--records`, `DEFAULT_RECORDS` and the four `gate.json` writes are gone, because the harness's stamped
verdict under `runs/gates/<name>/gate.json` is the record. Pressed after the change:
`python copy_gates.py all` → smoke import PASS (tooth TRIPPED), edit-behaviour PASS (both teeth
TRIPPED), copy-identity PASS 224/217 (4/4), frozen-physics PASS 77/76 (4/4), `ALL GATES PASS`, exit 0.
The `PROCESS/CHANGES.md` §6 command named in the brief is not in this base; the command it names
works.

`smoke_import` is not registered (survey: subsumed by the `capability` probe); it stays a printed
check of the copy's own command line.

### 5.4 The four legacy records

`runs/gates/{copy_identity,edit_behaviour,frozen_physics,smoke_import}/gate.json` were `copy_gates.py
main`'s unstamped verdicts (A63 §5 d3). The first two were overwritten by the framework's verdicts at
`f0889b65`. The other two, and the two retired stages' `measurements.json`, now have no writer and no
reader — but the `gate_table` stage stamps every `*/gate.json` it finds (pattern, not list), so
leaving them would have kept an unstamped `None` head in its `records_read` for ever. **Moved out of
`runs/`** (kept in the session's scratch directory, not committed), then `--measure gate_table
--resume` re-made: `records_read` **30 → 28**, heads without the `None` entry; `--plan-tables check`
IDENTICAL. Reversal: nothing regenerates them; they were dead files.

## 6. Verification, in the brief's order

All at `f0889b65` unless said; worktree clean, nothing running, `git status --short | wc -l` = 0
before the first press.

1. **`--selfcheck`**: PASS, 7 of 7 checks. Teeth **54 → 55** (the new `run path` tooth). Baseline
   pressed at `3154faa3` before any edit: PASS, 7 checks, 54 teeth.
2. **Import walk** (`pkgutil.walk_packages` over `harness` plus the four top-level scripts, from the
   scratch directory): **55 modules, 0 failures** — before the split the same walk had 50 modules.
3. **`--gates`** against the baseline listing at `3154faa3`: `26 gate(s) and 9 measurement stage(s)`
   → `28 gate(s) and 7 measurement stage(s)`; `+ copy_identity [harness] 4 teeth no PROCESS run`,
   `+ edit_behaviour [harness] 1 teeth no PROCESS run` after `g0prime`; `− attempts`,
   `− predicate_counters`; every other line byte-identical (`diff`). The preflight (`--draft`)
   carries no registry listing — `--gates` is the catalogue; the preflight ran clean, exit 0.
4. **Gates**, 0 PROCESS runs each: `g0prime --resume` PASS 77/1, 4/4; `copy_identity` PASS 224/7,
   4/4; `edit_behaviour` PASS 3/0, 1/1; `recomputation --resume` PASS **2 066 compared, 0
   mismatched**, 9/9 teeth, *runs read 36 record(s) — 33 at f8bce151, 3 at 7ad8ea04 [resumed]* (the
   two tally stages re-made first by dependency); `run_kind_separation --resume` PASS 215/0, 6/6,
   *184 run record(s) under runs/, of which 31 are covered by one of the tally's 2 declared source(s)*.
5. **`--measure gate_table --resume`** → **28 PASS, 0 FAIL, 0 not run; 158 of 158 teeth tripped**;
   **`--plan-tables write`** → 1 795 lines replacing 1 794; **`--plan-tables check`** → 1 795 identical,
   0 only in the document, 0 only from the records, IDENTICAL. §4.1 changed by exactly: two new rows,
   the caption's population `26 registered gate(s) … 15 of the harness's own` → `28 … 17`, the
   summary `26 PASS … 153 of 153 teeth` → `28 PASS … 158 of 158`. §4.2–§4.4 unchanged. After the
   four dead records were moved out (§5.4) the stage was re-made and the check re-run: IDENTICAL.
6. **Stamp survey** (`run_stamp_survey.py --json after.json --against before.json`): **184 records
   then, 184 now; 0 whose commit changed, 0 disappeared, 0 new.** Histogram unchanged: 127 at
   `f8bce151`, 16 at `61473c1d`, 12 at `b784158c`, 11 at `3d64625c`, 6 at `09cc9f3e`, 6 at
   `fd480aff`, 3 at `47be2b0d`, 3 at `7ad8ea04`. **This task made no PROCESS run.**
7. **Grep** for the retired symbols (`capture_ladder`, `LADDER_DEMONSTRATION`, `attempt_measurements`,
   `predicate_counter_measurements`, `predicate-counters`, the stage names as registry keys) and for
   the old module path outside heritage docstrings (`harness.gates.gates`, `harness/gates/gates.py`):
   **empty**, except the live import `from harness.gates.gates import _with_capture` in two gate
   modules. The remaining occurrences of the words `attempts` and `predicate_counters` are the record
   *fields* of those names, the driver's `LADDER_STAGES`, tally/analysis column labels and task
   heritage (`A58 (driver-predicate-counters)`), none of them the stages.

## 7. Autonomous decisions, each with its reversal

| # | decision | reversal |
|---|---|---|
| d1 | `exclusion_review` got its own module rather than staying in `gates.py`: it reads three gates' tables, and inside any one of them or the remainder it would need lazy imports to avoid a cycle. B8 (A71) says "move it beside G1" — a file beside `gate_neutrality.py` is beside G1 | paste it back into `gates.py` with three in-function imports |
| d2 | the output-path measurement (`output_path_measurements`, `capture_contrast`) went with G9 into `gate_output_path.py`, not into `measurement/`: it is built on G9's run directory and comparison helpers, and `measurement/` may not import `gates/` (README §10.1's layering). B5 (A71) retires it | cut the section into its own module |
| d3 | `main`/`print_verdict` went to `registry.py`; usage is `python -m harness.gates.registry`. The one button is the runner; this command line predates it and now says so | keep a two-line `gates.py __main__` delegating to it |
| d4 | each gate module owns its `Gate(...)` literal as `gate(campaign)`; `_plan_gates` collects | inline the literals back into `_plan_gates` and import the private bodies/teeth |
| d5 | the sweep identity refuses **finished** records only and passes over a missing total, mirroring `assert_both_rulers` and `assert_attempt_summation` | drop the `status` guard; 0 accepted records change either way today |
| d6 | the new tooth lives in the `run path` self-check, not in G7 | add the doctored-record tooth to `gate_records.py` and press `--gate record_completeness --resume` |
| d7 | `edit_behaviour` stays a gate with one tooth, not a measurement | wrap `check_edit_behaviour` in a `Measurement` and delete `run_edit_behaviour_tooth` |
| d8 | `copy_gates.py` keeps every command and adds the new tooth to `edit-behaviour`/`all`; only its record writing goes | restore `--records` and the four writes (one commit's diff) |
| d9 | the four dead records under `runs/gates/` moved out (§5.4) | copy them back from the scratch directory; nothing writes them |
| d10 | `copy_identity`/`edit_behaviour` carry no `plan_name` and sit right after `g0prime` in `GATE_ORDER` | give them a label; move them in the tuple |

## 8. Limits

- **No `--gate all`** was pressed (D27: one rerun at A73). G1, G5–G9, GR were not run on the split
  tree; what was run is the self-check, the five gates the brief names, the two tally stages by
  dependency, the gate table and the render. The gate modules' bodies are verbatim moves and the
  import walk shows them importable, but a gate that runs only under `--gate all` has not executed
  its body since the split.
- **Line count target**: `gate_neutrality.py` is 1 844 lines against the survey's ≤ 1 800.
- **The identity census** (§4.2) is over the relocated set at one point in time; the two residual-1
  records belong to an instrument A73 retires. A future record that carries a total, no per-run
  block and a spent per-run sweep would be refused by the contract — which is the intended
  behaviour, but it has not been observed on an accepted record.
- **`harness_survey.py`'s "gates.py by section" census** now measures the remainder file; A68's
  numbers for it are historical.
- **Prose inside the moved sections** that says "this module", "above" or "below" was not re-read
  line by line; the moves are verbatim and such sentences may now point across a file boundary.
- **`smoke_import`** is neither registered nor given a tooth beyond its own PYTHONPATH tooth; the
  survey's claim that the capability probe subsumes it was not re-measured here.

## 9. What the queue, the plan and the README should gain (not edited here except the README)

- **Queue row A70**: MERGED with the numbers of §1; the four commits; the two findings — the
  `self_containment` bite on the move and the two residual-1 diagnosis records.
- **A71 (B5, B8, B6)** now finds `output_path_measurements`/`capture_contrast` in
  `gate_output_path.py`, `exclusion_review` in its own module beside G1, and the attempt-summation
  and sweep-decomposition teeth in the `run path` self-check; B6's 147 → 135 count is against a
  gate table that now reads 158.
- **A73**: the `--gate all` press covers `copy_identity` and `edit_behaviour` for the first time from
  the button; the four dead records are gone from the set to be relocated.
- **Harness plan**: the amendment that lists `runs/gates/<stage>` records should drop
  `predicate_counters` and `attempts`; §4.1's placeholder prose "one row per gate" is now 28 rows.
- **README**: edited — §0 layer 5, §8 (`run path` row, the callers list), §10.1 (the `gates/` row
  and the who-imports-whom paragraph).

---

## Orchestrator's critical assessment (protocol §5)

*Written 2026-09-14 at the branch tip `c44e6525`, before the merge. Checks chosen to differ from
the agent's.*

1. **Is the split a move?** I hashed the AST of every top-level definition in the old `gates.py`
   (113) and looked for each in the new `gates/`, `records.py` and `measurement/` modules. 17 are
   absent, all of them the two retired stages' functions (A2) plus `_reconcile_sweeps`, which lives
   on as `records.sweep_decomposition`. 4 changed body: `registry`, `measurements`, `_plan_gates`,
   `main` — exactly the four that lose two stages, gain two gates and re-point imports. The other 92
   are byte-identical by AST. No gate criterion changed.
2. **On a trial merge onto trunk (`5bccae08`, which carries A69's `CHANGES.md`):** clean; an import
   walk loads 51 modules with 0 failures; the registry lists 35 entries with `copy_identity` and
   `edit_behaviour` present and `attempts`/`predicate_counters` gone; the after-run caller table reads
   `reproduction, switch_neutrality, written_file_gap`; `copy_gates.py all` still reports ALL GATES
   PASS, so `CHANGES.md` §6's verification command is intact.
3. **The scanner hazard** the brief named was hit and caught by the scanner itself (`self_containment`
   flagged the moved line before the declaration was updated). That is the mechanism working; the
   declaration change is one string.
4. **The four dead records moved out of `runs/`** (two legacy verdicts without a tree stamp, two
   stage records of the retired stages): correct — `gate_table` would otherwise stamp a `None` head —
   and they will not exist in A73's from-scratch press anyway. Not put back.
5. **`gate_neutrality.py` at 1 844 lines** against the survey's ≤ 1 800: the exclusion tables stay
   with G1 whole, as briefed; the target was a guide, not a rule.
6. **0 PROCESS runs**, by the agent's stamp survey (184 → 184, 0 changed) — consistent with every
   press it lists being 0-run or `--resume` on kept records.

**Approved for merge.**
