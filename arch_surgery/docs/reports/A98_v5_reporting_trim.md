# A98 (v5-reporting-trim) — item 10's removals, the harness fixes, the one generator and the recount

> **Document status** — **TASK REPORT, OPEN.** Written 2026-09-29 by task A98 (v5-reporting-trim) on
> branch `A98-v5-reporting-trim` from `43d31a04` (the tip of `architecture_surgery`). Two commits,
> `288b6d2a` and `0d1db315`; every number below was produced by a committed script at one of those
> commits and the record it came from is named beside it. **No PROCESS run was made**: the 30 run
> records the gates read are A94 (v5-copy)'s, every one stamped `d6c246a1` (§6.4). The task touched
> nothing under `MDA_partitioning_experiment_v5/PROCESS/` (A99's) and nothing under
> `MDA_partitioning_experiment_v4/` (published). Vocabulary: *item n* is the V5 improvement list's
> (`docs/plans/V5_IMPROVEMENT_LIST.md`); *plan §n* is `docs/plans/V5_EXPERIMENT_PLAN.md`; D30–D36 are
> the queue's decisions register; I-31 and I-32 its issue register; T14 and T16 are traps.

---

## 0. Verdict

**Done, every self-check passing, no run made.** In the V5 copy (`arch_surgery/MDA_partitioning_experiment_v5/`):

- **Removed what item 10 drops** (plan §8, §11 row 10): nine files, 21 117 lines, and the parts of
  eleven kept modules that served them (§1). The Python under the copy's harness and top level went
  from **62 483 to 46 746 lines** (−25 %); the measurement package alone from 22 309 to 10 910 (§1.2).
- **The harness fixes** (§2): I-31 closed (a default `NUMBA_CACHE_DIR` beside `MPLCONFIGDIR`), I-32
  closed in the copy (the help-string example no longer names the superseded directory;
  `self_containment` **PASS from scratch**, 50 files, 13 executable lines naming either directory, 0
  findings, 0 imports, 0 stale declarations, 1/1 teeth), A94 §2's self-references re-pointed.
- **The `mixed` predicate mode retired on the harness side** (§3): the switch's name is in
  `retired_names` ("dropped, D30 / item 10"), the campaign composes `frozen` alone, and the interim
  before DR11 retires it in the driver is declared by name in `switches.RETIRED_PENDING_IN_DRIVER`;
  the `capability` self-check compares the registry's list *minus* the pending names with the driver's
  and requires every pending name absent there — **PASS**, 11 names identical, 1 pending.
- **The one generator and the recount** (§4): `harness/measurement/paper_tables.py` writes the one
  document of plan §8 (main text: matrix, configurations, phase A on D34's pair, phase B iterations
  and modules; appendix: the three wall-clock grids as declared placeholders, per-arm success, the
  verification table); `--paper-tables check` refuses on any difference; `CHARGED_ONCE` retired.
  `paper_cells_recount.py` recounts exactly the paper's cells with no shared code. Smoked against V4's
  campaign records as **test data only** (read-only; nothing from them committed): the generator's
  cross-check **178 cells, 0 mismatched, tooth bites**; the recount **44 cell rows, 0 mismatched**;
  `check` refuses a file with one byte changed; the recount counts 1 mismatch on a doctored cell.
- **The registry is plan §7 Table 2** (§5): G8, G3/G3c, `recomputation` gone; **GT and GC declared
  placeholders that refuse with "not implemented"** (pressed: both REFUSED TO RUN, exit 3, no record
  written); **GR run once** (pressed without `--resume`: REFUSED; with it, PASS read from the record).
  `--measure gate_table --resume`: **16 PASS, 0 FAIL, 13 NOT RUN** (the run-needing gates and the two
  placeholders); its stamp block names 16 verdict records, every one current.
- **Self-checks** (§6): the run-free set pressed as gates on the seeded records — 16 PASS, 91/91 teeth
  tripped on the pressed gates; `--selfcheck` **7 self-checks pass**; `python -m compileall` clean; the
  stamp survey: **30 run records, 30 at `d6c246a1`** — nothing re-made.

Not done here, by scope: the driver copy, item 5's execution (so `A2`'s post-processing cell reads
the measured **0** on today's records and the caption names item 5), the wall-clock instrument, GT's
and GC's bodies, the README's rewrite to V5's text (§8).

---

## 1. What was removed

### 1.1 The files

All nine removed at `288b6d2a` with `git rm`; line counts from `git show 43d31a04:<path>` (the
counting script is the inline one in §1.2's provenance).

| file | lines | what it was |
|---|---:|---|
| `harness/measurement/analysis.py` | 6 464 | the second implementation (A54); replaced by the recount |
| `harness/measurement/plan_tables.py` | 4 361 | the report renderer and companion-file writer; its stamp check and population marker moved into the generator |
| `harness/data/dsm_function_counts.json` | 4 968 | A88's function weights |
| `RESULTS_TABLES_FULL.md` | 1 705 | the companion file (V4's rendering, copied) |
| `block_binding.py` | 1 060 | A90's instrument; stays in V4 |
| `harness/gates/gate_predicate_mode.py` | 986 | gate G8, the `mixed` ruler trial |
| `report_cells_preserved.py` | 747 | the cells-preserved check of the removed renderer |
| `report_counts_check.py` | 582 | V4's report-count check |
| `report_citations_repoint.py` | 244 | V4's citation sweep |
| **total** | **21 117** | |

### 1.2 The parts of kept modules

| module | removed | kept |
|---|---|---|
| `harness/chain.py` | the stencil regime end to end: `ChainPlan.entry_regimes` and `stencil_columns`, `stencil_column_set`, `evaluation_stencil_chains`, `stage_evaluation_stencil`, `_assert_columns`, the `evaluation_stencil` run stage, the budget line; `READING_STAGES`' `recomputed_tables` and `recomputation`; the three analysis teeth of `run_kind_separation` | one evaluation regime (displaced), the two tally stages and `tally_contracts`; the six remaining teeth |
| `harness/measurement/tally.py` | the two stencil sources (`campaign_stencil_forward`/`_backward`) and `_campaign_stage`'s sign filter | the three campaign sources and the two gate sources |
| `harness/measurement/tally_evaluation.py` | `function_counts`, `FUNCTION_WEIGHTED_NAME`, `module_sweeps_function_weighted`, `absent_cell`; `predicate_trial` (G8's table) and its emission | every other table; `matched_accuracy` now iterates the record contract's `records.AUDIT_RULERS` (the audit is *measured* on both rulers) instead of `campaign.predicate_modes` (what an arm *composes*) |
| `harness/measurement/tally_optimisation.py` | `module_sweeps_function_weighted` and its emission | — |
| `harness/measurement/stats.py` | `functions_by_group`, `FUNCTION_COUNTS_FORMAT`; `weighted_total`'s docstring no longer names a function weight | `weighted_total` (the DSM-row weight of the node-calls-per-block tables) |
| `harness/gates/gate_tally.py` | `_tooth_function_count_not_guessed` and its `Tooth` row (17 teeth remain) | the reference-cell check and its tooth |
| `harness/gates/gate_prime.py` | the whole G3/G3c section (`PREVIOUS_FIGURES`, `COMPOSITIONS`, `cold_chain_*`, its teeth), the `G3C_*` constants, `CARRIER_COMPONENTS`; 990 → 373 lines | G2 `prime_map`, unchanged (its re-forming is item 8's task) |
| `harness/gates/exclusion_review.py` | G8's part: the import, `PREDICATE_PAIR_KIND`, its classification assert, `_predicate_pairs`, the rows, the count, the record block, the printer key | G1's part (plan §11 row 10) and G9's field list |
| `harness/gates/gate_resume_identity.py` | the two G8 pairs; the shared-reference pair's `b` re-pointed from G8's reference jobs to `gates.entry_reference_jobs` | 11 by-design pairs (8 must differ, 3 must agree) |
| `harness/gates/registry.py` | the `predicate_mode` and `cold_chain` rows, `_analysis_gates`, `_analysis_measurements`, the `predicate-mode` command line and printer branch | see §5 for what was added |
| `harness/gates/gate_composition.py` | the `predicate_mode` row of `PLAN_COLUMN` (`0d1db315`; §6.2 says why) | — |
| `harness/core/config.py` | `stencil_runs`; `MEASUREMENT_ARTIFACTS`' one entry; `predicate_modes` → `("frozen",)` | `MEASUREMENT_ARTIFACTS` as an empty mechanism |
| `experiment_runner.py` | the `plan_tables` import, `stage_plan_tables`, `--plan-tables`; the stencil budget lines; the analysis mentions | `--run`'s `--stencil-column`/`--stencil-sign` (§7 (5)) |

**Line counts per package**, Python files under the copy excluding `PROCESS/`, at `43d31a04` and at
`0d1db315` (counted by the inline script of §6.5 from `git show`, never from a working tree):

| package | before | after | Δ |
|---|---:|---:|---:|
| `harness/` (top: `__init__`, `chain`) | 1 771 | 1 481 | −290 |
| `harness/core/` | 3 984 | 3 977 | −7 |
| `harness/experiment/` | 4 585 | 4 611 | +26 |
| `harness/child/` | 7 456 | 7 456 | 0 |
| `harness/gates/` | 17 178 | 15 475 | −1 703 |
| `harness/measurement/` | 22 309 | 10 910 | −11 399 |
| top level (`experiment_runner.py`, `PROCESS_diff.py`, `copy_manifest.py`, `run_stamp_survey.py`, `paper_cells_recount.py`) | 5 200 | 2 836 | −2 364 |
| **total Python** | **62 483** | **46 746** | **−15 737** |
| Markdown/JSON beside (data, README, report, companion) | 49 435 | 42 775 | −6 660 |

`harness/child/` is untouched. `git diff --stat 43d31a04..0d1db315`: 33 files, +1 439 / −23 836.

---

## 2. The harness fixes

**I-31** — `switches.base_environment` (the one place the pool's child environment is composed; the
pool reaches it through `arms.env_for`) now sets `NUMBA_CACHE_DIR` to `<runs_dir>/_numba_cache` beside
the `MPLCONFIGDIR` it already set — as a **default** (`setdefault`): a caller that sets its own keeps
it. With it, numba's compiled cache no longer lands under the copied driver's `__pycache__`
directories. Not measured here (no run was made; the first V5 run will show `_numba_cache` under
`runs/` and nothing new under `PROCESS/`).

**I-32** — the `--paper-tables-runs` help string in `experiment_runner.py` no longer names the
superseded directory (it reads "the runs root to read … in place of the experiment's own runs/ — a
relocated records tree, read only; nothing is written there"). **`self_containment` pressed from
scratch at `288b6d2a`: PASS** — 50 Python files scanned, 45 lines naming either directory, 32 in
prose, 13 executable and every one classified, 0 findings, 0 imports, 0 stale declarations; the
tooth (a scratch module importing the directory, counted) tripped. The `data_provenance.py`
declaration's wording lost its A88 clause with the function counts (the file still carries its three
declared source strings, so the declaration is not stale). Record: `runs/gates/self_containment/gate.json`.

**A94 §2's self-references** — the README's four `_v4` mentions (the paths sentence, two `cd` lines,
one `sys.path.insert`) and `PROCESS_diff.py`'s two summary strings now say `_v5`.
`harness/data/PROVENANCE.json`'s `what` does not say V4 ("this experiment"); the file was regenerated
anyway, by its own generator (`data_provenance.py record --force`), because a data file it names was
removed: the diff is the dropped `dsm_function_counts.json` entry and `copy_date` `2026-09-14 →
2026-09-29`, nothing else (A94 kept V4's date because nothing had changed; here the file set did).
`data_provenance.py verify` and the **`data` gate from scratch: PASS**, 16 files + the predicate module
= 17 comparisons, 9/9 declared counts, 6/6 teeth.

---

## 3. The `mixed` predicate mode, retired on the harness side

The `predicate_mode` entry of `switches.REGISTRY` now has no driver name, is not composed, and carries
`retired_names={"PROCESS_ARCH_PREDICATE": "dropped, D30 / item 10 (the 'mixed' ruler trial)"}` — so
the name is **cleared** before every arm (`all_names`) and **refused** if present
(`assert_no_retired`); `campaign.predicate_modes` is `("frozen",)` and `arms.Arm.terms` refuses any
other value. Nothing under `PROCESS/` changed: the driver still honours the name (until DR11) and
resolves its absence to the frozen ruler, which is what every arm now composes.

**How the self-check tolerates the interim.** `switches.RETIRED_PENDING_IN_DRIVER` declares, by name
and with the change that carries the retirement, the names the harness has retired ahead of the
driver: `{"PROCESS_ARCH_PREDICATE": "DR11 (task A99) …"}`. The `capability` self-check now requires the
driver's `RETIRED_SWITCHES` to equal the registry's list **minus** the pending names, **and** every
pending name to be absent from the driver's list — so the day DR11 lands the table must be emptied in
the same commit or the check fails, and the interim cannot outlive the change silently. Pressed at
`288b6d2a`: PASS, "11 retired switch name(s), identical in the registry and in the driver's own list …;
1 retired by the harness ahead of the driver, declared pending and absent from the driver's list:
PROCESS_ARCH_PREDICATE"; 5/5 teeth, the retired-name tooth over all 12 names. Record:
`runs/gates/capability/gate.json`.

**What was not retired**: the exit audit's two rulers (`records.AUDIT_RULERS = ("frozen", "mixed")`)
and the record fields that carry them — the record contract, which GR compares and G7 binds; the
matched-accuracy table still reports the audit on both. `pool.Job.predicate_mode` stays a job-identity
field (always `"frozen"`): removing it would change every job digest and re-make every seeded record.

**The unimplemented-switch tooth** of the `run_path` self-check doctored the predicate-mode switch back
to "no driver name" to bite; a retired switch has none, so the tooth is re-pointed at a doctored
`output_loop` switch and `B2` (which composes it as `none`), with the live half now also checking that
no retired name is in `B2`'s composed environment. `run_path`: PASS, 12/12 teeth.

---

## 4. The generator and the recount

### 4.1 `harness/measurement/paper_tables.py` — the one document (1 300 lines; V4's was 1 123)

One `render`, one file, `paper_tables.md`, as Markdown grids and, where the paper prints the table,
LaTeX rows. Main text: the **switch matrix** from `arms.matrix()` (the data every arm is composed from,
printed rather than transcribed); the **configurations table**; **phase A module sweeps per
evaluation with the ratio columns on D34's pair** — `phase_a_pair(pulsed)` returns `A1 → A2` on a
pulsed configuration and `A0 → A2` on `st_regression` — ratio of means, per-run median, `[min, max]`;
**phase B iterations** and **phase B module sweeps** on `B2/B0` with the rungs beside. Appendix: the
**three wall-clock tables of plan §6** as declared placeholders (rows and captions, every cell empty,
a sentence saying the instrument is item 9's later driver task); the **per-arm success table**
(republished from the tally's stage table); the **verification table**, one row per check of plan §8
(G0, G1, A1, A2, B1, G6, G5, G9, GT), each gate's verdict read through the `gate_table` stage record
after `assert_gate_table_current` (the T14 stamp check, moved here from the removed renderer, with the
population marker), "not pressed" where no verdict record exists (a placeholder, or a gate never
pressed) and a stated reason where the check is not yet a construction (A1: V5's whole-state rule,
D36, waits on item 5; B1: V4's check 1 verdicts are printed, the attribution rule is item 4's).

**`CHARGED_ONCE` is retired.** `A2`'s Post-processing cell reads the measured count; on today's records
that is **0** on every run (the exact-integer check holds) and the caption says the run will execute
the deferred set once after convergence when item 5's driver change lands. The cell is not the
paper's cell until then, and the document says so.

**`check` refuses.** `--paper-tables check` renders, runs the cross-check and its tooth, and raises
unless the file on disk is byte-identical to the rendering; the runner prints `REFUSED` and exits 3.
`--paper-tables-out` names the file to write or compare, and is **required** with
`--paper-tables-runs` so a rendering from another tree's records never becomes the folder's
`paper_tables.md` (the runner refuses the combination without it).

**Dropped from the document**: the optimiser-evaluations decomposition section of 2026-09-29 (not in
plan §8's list; reversible from `43d31a04`'s `paper_tables.py`), and the "Models" column's read of the
removed function-counts file — it now reads the committed node map's
`units.dsm_rows.executed_in_a_sweep` (52) less `CONSTRAINT_ROWS_EXECUTED_IN_A_SWEEP = 1`, **the one
typed number in the document** (§7 (3)), which keeps the paper's 51.

### 4.2 `paper_cells_recount.py` — the independent recount (319 lines)

Imports nothing from `harness/`. Reads `metrics.json` files under `campaign/evaluation/…` and
`campaign/optimisation/…`, the node map and the per-run artifacts directly; carries its own
three-entry `RECORDED_ARM_NAMES` and applies it to `campaign_arm` of records without an `arm_naming`
stamp (T16: never by directory name); recounts phase A's module rows on D34's pair, phase B's
iterations and module rows (audit sweep subtracted, `audit_node_calls` checked), and per-arm success
(offered, accepted); parses the generator's rendered document and prints the two readings side by
side with a mismatch count. Exit 1 on any mismatch.

### 4.3 Smoke against V4's campaign records — test data, nothing published

Read-only from `arch_surgery/idf_probe/runs/A90_runs/` (949 campaign records at `57dc0c14`, arm names
translated at read); rendered into the worktree's `runs/paper_tables_from_test_data/paper_tables.md`
(429 lines; untracked, relocated with the records, **not** committed — the folder's committed
`paper_tables.md` is V4's rendering, untouched, pending V5's campaign).

| press (at `288b6d2a`) | result |
|---|---|
| `--paper-tables write --paper-tables-runs <A90> --paper-tables-out runs/paper_tables_from_test_data/paper_tables.md` | cross-check **0 mismatched of 178** cells; tooth **bites** (a doctored cell on each of the three sides caught); verification G0/G1/G6/G5/G9 PASS from A90's gate table, A1 not pressed, A2 reported, B1 `tok` PASS PASS · `lad` FAIL FAIL · `st` PASS, GT not pressed; written |
| `paper_cells_recount.py --runs <A90> --document <that file>` | **44 cell rows compared, 0 mismatched**, exit 0 |
| `--paper-tables check …` on the same file | IDENTICAL, exit 0 |
| `--paper-tables check …` on a copy with one cell's digit changed (`4.0 → 4.1`) | **REFUSED**, exit 3 ("does not match what the records now produce … Nothing was written") |
| `paper_cells_recount.py` on that copy | 44 compared, **1 mismatched**, exit 1 |
| `--paper-tables check --paper-tables-runs <A90>` without `--paper-tables-out` | REFUSED (the combination) |

The 178: phase A's per-arm means on every row and configuration, plus its pooled ratios and pair
counts on D34's pair (which is the tally's own reference on all three configurations now — V4's
convention compared the ratio on `st` alone); phase B's iteration cells (n, four arm means, pooled,
median, bracket) and module means before the audit is taken out with pair counts. The 44 rows:
5 phase A rows + 1 iterations row + 5 phase B module rows + 3–4 success rows per configuration.

---

## 5. The registry after (plan §7 Table 2)

| gate | plan | status in the registry | tooth count |
|---|---|---|---|
| `g0prime` | G0 | kept | 4 |
| `switch_neutrality` | G1 | kept | 9 |
| `prime_map` | G2 | kept (its re-forming is item 8's) | 2 |
| `audit_restriction` | G4 | kept until D36's retirement condition | 6 |
| `switch_composition` | G5 | kept | 4 |
| `entry_and_warm` | G6 | kept | 3 |
| `record_completeness` | G7 | kept | 9 |
| `output_path` | G9 | kept | 4 |
| `test_set` | GT | **declared placeholder — refuses "not implemented"** (`DECLARED_NOT_IMPLEMENTED`); the body is DR11's | 1 (the placeholder cannot be made to pass) |
| `count_neutrality` | GC | **declared placeholder — refuses**; the body is DR9/DR10's | 1 |
| `reproduction` | GR | **run once** (`RUN_ONCE`): its body refuses without `--resume`; with it, the record at `d6c246a1` is read | 8 |
| `cold_chain` | G3 / G3c | **gone** (plan §12 Q3) | — |
| `predicate_mode` | G8 | **gone** (item 10, D30) | — |
| `recomputation`, `recomputed_tables` | — | **gone** (item 10) | — |
| self-checks and artifact stages (`composition`, `rungs`, `capability`, `provenance`, `data`, `run_path`, `stage_provenance`, `resume_identity`, `self_containment`, `copy_identity`, `edit_behaviour`, `artifacts_*`, `written_file_gap`, `tally_contracts`, `run_kind_separation`) | — | kept | as V4, less the one function-count tooth |

The two placeholders rank **last** in `ordered_gate_names` (after every listed and unlisted name),
because each refuses and a refusal stops `--gate all`. Pressed from the button at `288b6d2a`:
`--gate test_set` → "REFUSED TO RUN — gate test_set (GT) is not implemented: it binds DR11 …", exit 3,
no `gate.json` written; `--gate count_neutrality` → the same for DR9 and DR10. `--gate reproduction`
without `--resume` → "REFUSED TO RUN — gate reproduction is pressed once, at the copy commit, and is not
re-made …", exit 3. Log: `runs/gate_press.log`.

**The gate table** (`--measure gate_table --resume` at `0d1db315`, after every press;
`runs/gates/gate_table/measurements.json`): 29 registered gates — 11 of the plan's table, 18 of the
harness's own; **16 PASS, 0 FAIL, 13 NOT RUN** (the ten run-needing gates, `tally_contracts` which
needs the tally stages, and the two placeholders); 91 of 158 declared teeth tripped, all 91 on the
pressed gates. Its `records_read` block names 16 verdict records at `0d1db315`, `288b6d2a` and
`d6c246a1`, "every one of them byte-identical to what is on disk now" (checked by
`paper_tables.assert_gate_table_current` after the render — an inspection, quoted as such).

---

## 6. Self-checks and presses — the numbers

### 6.1 The run-free gates, pressed on the seeded records

Seed: `idf_probe/runs/A94_runs/v5_copy_gates/` copied whole into the worktree's V5 `runs/` (124 MB,
30 run records, 17 gate records at `d6c246a1`). Presses from `experiment_runner.py --gate <name>
--resume` except where marked *from scratch*; log `runs/gate_press.log`; every verdict PASS with every
tooth tripped:

| gate | pressed at | compared / mismatched | teeth |
|---|---|---:|---:|
| `g0prime` | `288b6d2a` | 77 / 1 (the one approved model file, by name) | 4/4 |
| `copy_identity` | `288b6d2a` | 224 / 8 (the recorded permitted driver-edit files) | 12/12 |
| `edit_behaviour` | `288b6d2a` | 3 / 0 | 1/1 |
| `composition` | `288b6d2a` | 42 / 0 | 7/7 |
| `rungs` | `288b6d2a` | 98 / 0 | 3/3 |
| `provenance` | `0d1db315` (re-pressed at the clean tip) | 4 / 0 | 4/4 |
| `run_path` | `288b6d2a` | 12 / 0 | 12/12 |
| `resume_identity` | `0d1db315` (§6.2) | 66 / 0 | 9/9 |
| `capability` | `288b6d2a` | 54 / 0 | 5/5 |
| `artifacts_check` | `288b6d2a` | 95 / 0 | 3/3 |
| `reproduction` (`--resume`, run-once) | `288b6d2a` | 256 / 0; 29 records read, all at `d6c246a1` | 8/8 |
| `run_kind_separation` | `288b6d2a` | 56 / 0; 20 records read at `d6c246a1` | 7/7 |
| `stage_provenance` | `288b6d2a` | 10 / 0 | 5/5 |
| `self_containment` *(from scratch)* | `288b6d2a` | 50 / 0 | 1/1 |
| `data` *(from scratch)* | `288b6d2a` | 17 / 0 | 6/6 |
| `artifacts_derive_inputs` | A94's record, `d6c246a1` (not re-pressed: it runs PROCESS) | 2 / 0 | 4/4 |

`--selfcheck` at `0d1db315` (`runs/selfcheck.log`): **7 self-checks pass** — composition, rungs,
capability, provenance, data, run path, stage provenance — verdict PASS, exit 0. The
`stage_provenance` check's four teeth now break a scratch copy against the generator's
`assert_gate_table_current` ("PaperTablesError: the gate_table stage record does not describe the
records on disk …") — the same mechanism, one consumer fewer.

### 6.2 The one refusal met, and its fix

At `288b6d2a`, `--gate resume_identity --resume` **REFUSED TO RUN**: "the switch registry gives
'predicate_mode' no driver name; this tree cannot compose the plan's column". G5's hand-transcribed
plan column (`gate_composition.PLAN_COLUMN`) still carried a `predicate_mode` row (value `None`, to
compose the default by leaving the switch unset) and required the switch to have a driver name; a
retired switch has none. The row is gone at `0d1db315`: V5's matrix composes the frozen ruler by
leaving the retired name cleared, which `switch_by_switch` does for every retired name before the rows
apply, and the gate's `resolved_switches` comparison still catches a tree resolving the cleared name to
anything else. `resume_identity` re-pressed at `0d1db315`: PASS (22 Job fields, 11 by-design pairs, 3
recorded-name rows, 30 records read by arm name; 66 compared, 0 mismatched, 9/9 teeth).
`--jobs switch_composition` composes G5's 6 jobs (no run).

### 6.3 Compile

`python -m compileall -q harness experiment_runner.py copy_manifest.py run_stamp_survey.py
PROCESS_diff.py paper_cells_recount.py` at `0d1db315`, `PYTHONDONTWRITEBYTECODE=1`: clean.
`experiment_runner.py --gates` constructs every registry entry (29 gates, 4 measurement stages).

### 6.4 The stamp survey

`run_stamp_survey.py --json runs/stamp_survey.json` at `0d1db315`, after every press: **30 run
records under `runs/`, 30 at `d6c246a1`**. No run was made by this task; every gate that ran read A94's
records under `--resume` or made none.

### 6.5 Provenance of the numbers

Interpreter `/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python`; the capability probe's
children import the worktree's copy (`PYTHONPATH` = the copy, `process.__file__` asserted equal —
`capability` PASS is that assertion, 54 arm/configuration pairs). The line counts of §1.2 come from an
inline `git show`/`git ls-tree` count over both commits (an inspection of the tree in git, not a
measurement of any run; the numbers are reproducible from the two commits by anyone with the same
two commands and are not cited as results).

---

## 7. Autonomous decisions, each with its reversal

1. **`pool.Job.predicate_mode` and `records.AUDIT_RULERS` kept.** The brief retires the *mode* on the
   harness side; the job-identity field and the audit's two rulers are the record contract that GR
   compares and G7 binds, and removing them would re-make every seeded record. *Reversal*: DR11's task
   removes the field and the `mixed` ruler in one change with its G1 press.
2. **`campaign.predicate_modes = ("frozen",)` with `matched_accuracy` reading `AUDIT_RULERS`.** The one
   setting served two roles (what an arm composes, what the audit reports); they are now two names.
   *Reversal*: one line each in `config.py` and `tally_evaluation.py`.
3. **`CONSTRAINT_ROWS_EXECUTED_IN_A_SWEEP = 1`, a typed number.** The removed function-counts file
   carried per-row kinds; the committed node map does not, so the constraint row executed in a sweep
   is declared with its provenance (the pin's single `Constraints` row) rather than read, keeping the
   paper's "Models 51". The document's caption names it. *Reversal*: regenerate the node map with row
   kinds (the T9 route) and read them; or rule that "Models" counts the 52 executed rows.
4. **The optimiser-evaluations decomposition dropped from the document.** Plan §8 lists the document's
   tables and it is not among them. *Reversal*: the section's code is in `43d31a04`'s `paper_tables.py`.
5. **`--run`'s `--stencil-column`/`--stencil-sign` kept.** They feed `pool.Job`'s identity fields, which
   stay (decision 1's reasoning); the regime's chain, stage, sources and budget are gone. *Reversal*:
   drop the two arguments with the fields when the job identity is next re-made.
6. **`gate_prime.py`'s G3/G3c section removed whole**, not only its registry row: dead code with
   `PREVIOUS_FIGURES` typed from A35 would invite a re-registration; V4 keeps it. *Reversal*: `git show
   43d31a04:…/gate_prime.py`.
7. **The placeholders carry one tooth each** ("a press of the placeholder … REFUSE"): `framework.Gate`
   refuses construction without a tooth, and a placeholder that could be made to pass would be the
   defect. *Reversal*: none needed; the real gates replace the placeholders with their own teeth.
8. **`RETIRED_PENDING_IN_DRIVER` as the interim mechanism** (§3), with the fail-on-landing rule.
   *Reversal*: empty the table when DR11 lands (required by the check itself).
9. **`NUMBA_CACHE_DIR` as `setdefault`**, not an override: I-31 asks for "a harness default".
   *Reversal*: one word.
10. **The README not rewritten**: its four self-references re-pointed and a status note added at its
    head naming every section that now describes removed machinery; the rewrite to V5's text is a later
    task (plan §8's report form). *Reversal*: none needed.
11. **`copy_manifest.py` and `COPY_MANIFEST.json` left as they are**: the one-time proof of the copy at
    its commit (A94 §9: "the copy commit is its record"); `copy_manifest.py check` now reports the nine
    removed files as missing, by design. *Reversal*: none; it is history.
12. **`EXPERIMENT_REPORT.md`**: a status header inserted before V4's own header, nothing else changed
    (the brief's rule).

---

## 8. Limits

- **No campaign, no V5 numbers.** Every number here is a self-check count, a test-data cross-check or
  a line count. The generator's document from V5's own records does not exist yet; `--paper-tables
  write` on the folder's `runs/` refuses ("no campaign record").
- **The A1 and B1 rows of the verification table are declarative** until item 5 (whole-state rule,
  D36) and item 4 (the attribution rule) become tally constructions; the generator prints "not pressed"
  and V4's check 1 verdicts respectively, and says so in the cell.
- **`A2`'s Post-processing cell reads 0** on today's records (V4's, and V5's until item 5 lands); the
  caption says it is not the paper's cell yet.
- **The wall-clock grids are empty by construction** until DR12.
- **The interim of §3 is a declared inconsistency** between the harness and the driver, tolerated by
  name; it ends with DR11.
- **The gate table's 13 NOT RUN** are the run-needing gates: a from-scratch press of them is the
  campaign's business (plan §7; amendment 15), not this task's.
- **`copy_manifest.py check` no longer passes** on the copy (nine files removed) — expected, and the
  manifest is the copy's proof at `d6c246a1`, not a living gate.
- The recount parses the generator's Markdown; a change of the document's headings or cell format
  needs a matching change in its parser (it would then report every cell as a mismatch, not agree
  silently).

---

## 9. Proposals (not applied here)

1. **Queue**: close I-31 (fixed in the copy; V4 left as published) and note I-32 fixed in V5 with
   A97's V4 fix pending; a task row for the README's V5 rewrite (plan §8) if the orchestrator wants
   it separate from the report task.
2. **V5 plan §7 Table 2**: GT's and GC's rows could name the registry entries (`test_set`,
   `count_neutrality`) and say "declared, refuses" until their tasks; GR's row could cite
   `registry.RUN_ONCE`.
3. **V5 plan §11 row 10**: `gates/gate_composition.py` (the plan column's row) and
   `gates/gate_resume_identity.py` (the G8 pairs) belong in its "modules that change" list; both were
   touched here.
4. **The "Models" column** (decision 3): a ruling on whether the paper's count is the 51 model rows
   (the constraint row declared) or the 52 executed rows (read from the node map alone).
5. **Retirement**: the records are at `<worktree>/arch_surgery/idf_probe/runs/v5_reporting_trim/`
   as one tree (the V5 `runs/` copied there and the original removed, per the brief); the retire
   script relocates it under `idf_probe/runs/`, and the merge note should cite the path it prints.

---

## 10. Change log (append-only)

| date | entry |
|---|---|
| 2026-09-29 | `288b6d2a` — item 10's removals (nine files, the parts of eleven modules), the harness fixes (I-31, I-32, self-references, `PROVENANCE.json` regenerated), the `mixed` mode retired on the harness side with `RETIRED_PENDING_IN_DRIVER`, the one generator and the recount, GT/GC placeholders and GR run-once, the report's status header. |
| 2026-09-29 | `0d1db315` — G5's plan column drops the retired predicate-mode row (the one refusal met on the seeded records, §6.2). |
| 2026-09-29 | Presses: 16 run-free gates PASS on the seeded records (`self_containment` and `data` from scratch), `--selfcheck` 7 pass, `compileall` clean, the placeholders and GR-without-resume refused, `gate_table` rendered (16 PASS / 0 FAIL / 13 NOT RUN), stamp survey 30/30 at `d6c246a1`; the generator and the recount smoked on A90's records as test data (178/0, 44/0, both teeth bite). This report written. |
| 2026-09-29 | Records relocated as one tree to `arch_surgery/idf_probe/runs/v5_reporting_trim/` (byte-identical copy, original removed). Observed there: a `_numba_cache` directory created **empty** by the capability probe's children — the I-31 default reached them, and an import-only probe compiles nothing — and no numba cache file under the copy's `PROCESS/` (its three `__pycache__` directories hold bytecode only). Consistent with §2's "in place, not measured here". |

---

## 11. Orchestrator's critical assessment (protocol §5) — verdict: merge

*Written 2026-09-29 by the orchestrating session under D37 (autonomous); checked differently from
the agent, not by repeating its presses.*

**Checked.** (1) `git diff --stat 43d31a04..444ca05b`: 34 files, +1 877 / −23 836; **no path under
`MDA_partitioning_experiment_v5/PROCESS/` or `MDA_partitioning_experiment_v4/`** (the scope boundary
with A99 and the published folder holds). (2) `compileall` over the harness and the five top-level
scripts at the tip: clean, run by the orchestrator. (3) The gate-table record read from disk
(`v5_reporting_trim/gates/gate_table/measurements.json`): 29 rows, **16 PASS, 13 NOT RUN, 0 FAIL** —
the report's figures. (4) The records tree is one tree of 125 MB at
`idf_probe/runs/v5_reporting_trim/`, the folder's `runs/` removed, as briefed. (5) `merge-tree` against
the trunk: no conflict (the trunk moved only in `docs/` since `43d31a04`). (6) The worktree is clean.

**Read against the rulings.** Item 10's list is applied as ruled (the user: "this v5 reporting approach
is approved"); D34's pair is the generator's phase A reference on all three configurations; the
`mixed` retirement is the harness half of Q5 with the driver half left to DR11 by a *declared* interim
(`RETIRED_PENDING_IN_DRIVER`) whose self-check fails the day the driver lands without the table being
emptied — the right shape for a two-task removal. The typed number
`CONSTRAINT_ROWS_EXECUTED_IN_A_SWEEP = 1` (decision 3) is the one number in the document not read from a
record; it is declared with its provenance and named in the caption, which satisfies protocol §15's
letter; **whether the paper's "Models" count is 51 or 52 is a question for the user** (return update).

**Two corrections for the follow-on tasks, not for this merge.** (a) `RETIRED_PENDING_IN_DRIVER`'s note
says "DR11 (task A99)": DR11 is the test-set task (A100), A99 carries DR9/DR10 — the note is text only
and DR11's task rewrites it when it empties the table. (b) The GC placeholder will collide with A99's
real `count_neutrality` gate at the registry; resolved at A99's merge in favour of the real gate.

**Not verified here.** No V5 run was made by the task and none by this assessment; the I-31 default is
observed reaching the probe's children (an empty `_numba_cache`) but not yet a PROCESS child — the
first V5 run under DR11's task will show it. The generator's smoke on A90's records is test data and
is cited as such.

**Queue consequences applied at merge.** I-31 closed (fixed in V5; V4 left as published); I-32 noted
fixed in the copy (V4's fix is A97, merged); proposals 2–3 applied to the V5 plan (§7 Table 2 names the
registry entries and "declared, refuses"; §11 row 10 lists the two extra modules); proposal 4 filed
for the user's return; the README rewrite folded into the V5 report task.
