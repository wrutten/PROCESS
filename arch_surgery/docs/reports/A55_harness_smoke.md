# A55 (harness-smoke) — the chain, as the smoke and as the campaign

> **Document status** — **OPEN.** Task **A55 (harness-smoke)**, harness implementation plan item
> **H8**. Branch `A55-harness-smoke`, based on `architecture_surgery` at `c919f4c8` (the tip after
> A62 (exit-audit-restore) and A54 (harness-analysis) merged). Commits on the branch:
> `f8bce151` (the chain), `b784158c` (two defects the press found), `87951248` (this
> report and the experiment plan's filled §4), `d6f0fdf4` (G1's comparator, on the
> orchestrator's ruling).
> **`EXECUTION_APPROVED` is `False` and no campaign record exists.** Nothing under
> `arch_surgery/MDA_partitioning_experiment_v4/PROCESS/` or the repository-root `process/` was
> changed.
>
> **Every registered gate passes.** One failed on the press — G1 (`switch_neutrality`), 144 of
> 2 903 record values — and was reported with its numbers, not worked around; on the
> orchestrator's ruling its comparator now translates the earlier capture's vocabulary and it
> reads **0 of 2 831, 9/9 teeth**. §6.3 has both runs.

---

## 1. Verdict, in one page

**The button runs the whole chain.** `experiment_runner.py --smoke` runs the *campaign's own
stages* — the entry references, the evaluation phase's displaced-entry regime, the evaluation
phase's stencil regime, the optimisation phase — with one seed on the cheapest configuration and
every record stamped `smoke`, then the two tally stages, the tally's contract gate, the analysis's
tables and the analysis's `--verify`. It returns **0**, having made **13 runs, all `ok`**, and
reaching **`recomputation` PASS: 1 901 values compared, 0 mismatched, 9/9 teeth**, from one press.

**The smoke is not a second chain.** There is one sequence, in `harness/chain.py`, and a `ChainPlan`
says how to run it. The smoke's plan is one seed, one configuration, records stamped `smoke`; the
campaign's plan is every configuration, the plan's 25 seeds, records stamped `campaign`, and it
refuses to compose while `EXECUTION_APPROVED` is `False`. `experiment_runner.stage_campaign` is no
longer a stub naming stages that do not exist: it prints the chain the smoke also runs, its budget
(**949 runs**) and its refusals.

**The one press of `--gate all --resume --census-entry evaluation`, from the repository root at
`f8bce151`**, ran **140 runs** and passed 22 gates before stopping at `tally_contracts`, which
FAILED on **260 of 270 published cells, 10 moved**. Every one of the ten was
`exit_audit.residual_max_hex` on an optimisation run — the one field the reproduction gate excludes
**by name** under ruling D25. That is defect 1 of §6. With it fixed the gate reads **256 compared,
0 mismatched, 10/10 teeth**.

**Gate G1 passed that press over a stale capture, and failed once it did not.** `_capture_after`
returned early whenever `--resume` was given and a manifest existed, so the "after" side never
reached the completeness contract and A62's six incomplete records were kept: G1 reported a
straddle ending at `3d64625c`, a commit it had not measured. That is defect 2. With it fixed G1
re-made its after capture and became a genuine straddle for the first time — and **FAILED, 144 of
2 903, 7/7 teeth**, every one of the 144 "present on one side only" and every one a name **A53's
record-field rename** changed. On the orchestrator's ruling the comparator now **translates** the
earlier capture's leaf paths through `reference.FIELD_NAME_MAP`, segment-aware, and compares the
renamed leaves as values under their new names — never excludes them. Re-run at `d6f0fdf4`:
**PASS, 0 of 2 831 record values, 0 of 51 319 output-file lines, 9/9 teeth, 72 leaves renamed and
0 differing, 0 PROCESS runs.** The excluded count is unchanged, so nothing was excluded to make it
pass. §6.3.

*Caption: the press's headline numbers. "Compared" is the denominator of things actually compared
and "mismatched" the count that differed; "teeth" is tripped / declared. Every row is over the gate
population — one or two seeds per arm — at the commit named, never over a campaign.*

| what | verdict | compared | mismatched | teeth | commit of the records |
|---|---|---|---|---|---|
| `--gate all --resume` (24 gates) | 23 PASS, 1 FAIL **on the press**; **24 PASS after `d6f0fdf4`** | — | — | 137/137, then 139/139 | `f8bce151`; G1 at `fd480aff`→`d6f0fdf4` |
| `reproduction` (GR) | PASS | 256 | 0 | 8/8 | 30 records, all `f8bce151` |
| `switch_neutrality` (G1) | FAIL on the press, **PASS** at `d6f0fdf4` | 2 831 values + 51 319 lines | **0** + 0 | 9/9 | `fd480aff` (6) → `b784158c` (6), resumed |
| `tally_contracts` | PASS | 451 | 0 | 10/10 | 74 records |
| `recomputation` (`--verify`) | PASS | 1 901 | 0 | 9/9 | 33 records, all `f8bce151` |
| `run_kind_separation` (new) | PASS | 203 | 0 | 6/6 | 33 records |
| `--smoke` (the chain, one press) | exit 0 | 1 901 at `--verify` | 0 | 9/9 | 13 records, all `b784158c` |
| `--measure all` · `--artifacts all` · `--selfcheck` · preflight | 0 · 0 · 6/6 PASS · READY | — | — | 11/11 (artifacts) | — |
| `PROCESS/copy_gates.py all` · `PROCESS_diff.py --markdown` | ALL GATES PASS · exit 0 | 77 model files | 1 (the approved `pulse.py`) | 4/4 | — |

**The experiment plan's §4 is filled**, once, at this tip, by a committed script that reads the
measurement stages' own records: **131 tables, 3 620 cells**, no cell typed by hand.

---

## 2. Vocabulary

*Caption: one row per term this report uses in a sense particular to this project; the meaning is
the one the harness implements, not a general one.*

| term | what it means here |
|---|---|
| **smoke** | one press of the *campaign's own chain* with one seed, the cheapest configuration and every record stamped `smoke`. A test of the machinery, never a measurement: no table is ever computed over a smoke record, and two refusals plus a gate enforce that |
| **campaign record** | a run record stamped `campaign_run_kind = "campaign"`. **None exists.** `EXECUTION_APPROVED` is `False`, the campaign plan refuses to compose, and the survey of every record under `runs/` counts zero |
| **gate record** | a run record stamped `gate`: a run a verification gate made to reach its own verdict. Every published cell at this commit is over these — one or two seeds per arm, not the campaign's twenty-five |
| **press** | one invocation of `experiment_runner.py --gate all …`. A press re-makes every run a gate reads unless `--resume` is given, and `--resume` keeps a run only where its directory holds a *complete record of the same job* |
| **straddle** | a gate whose two compared sides were captured at two different commits. Gate G1 is the only one: its "before" capture is made in a tree at the earlier commit and is **never** re-made by the gate |
| **final tip** | the commit at which the one reproduction gate (GR) of the merged implementation is run. This task's press is it |
| **run kind** | the stamp that says what a record may be used for — `campaign`, `gate`, `smoke`, `reference`. It is the only thing that says so after the fact, so it is compared by resume and refused by every population |

---

## 3. What was built (deliverable 1)

### 3.1 One chain, two parameterisations

`harness/chain.py` holds the sequence the campaign runs. A `ChainPlan` says how to run it.

*Caption: one row per parameter the two plans differ in. Everything not listed — the stage list, the
job construction, the pool, the record schema, the tally and the analysis — is the same code, run
with different arguments.*

| | the smoke | the campaign |
|---|---|---|
| configurations | the cheapest one, **measured** (§3.3) | every one (3) |
| evaluation-phase seeds | one, undisplaced (`seed000`) | 1–25, all displaced at δ = 0.10 |
| optimisation-phase starts | one, unperturbed | `seed000` plus 24 displaced |
| stencil columns per arm | one | every column of the design vector |
| records stamped | `smoke` | `campaign` |
| needs the user's approval | no | **yes** — `EXECUTION_APPROVED` |
| runs one press makes | **13** | **949** |

They are one chain deliberately. A smoke written separately exercises its own code and reports on
the campaign's; when the campaign's first press then fails, the smoke has said nothing about it.

### 3.2 The stages, and what each printed

*Caption: the smoke's press, stage by stage, from `runs/smoke/press.json` at `b784158c`. "Runs made"
is this plan's own runs; "runs read" is the record count and commit each reading stage surveyed and
printed. Wall clock is summed in-child and is progress information, never evidence (I-10).*

| # | stage | kind | runs made | runs read | result |
|---|---|---|---|---|---|
| 1 | `entry_references` | runs | 1, `ok` | — | 4.4 s |
| 2 | `evaluation_displaced` | runs | 3, `ok` | — | 16.5 s |
| 3 | `evaluation_stencil` | runs | 6, `ok` | — | 26.3 s; restricted to 1 column per arm, recorded |
| 4 | `optimisation` | runs | 3, `ok` | — | 87.9 s |
| 5 | `tally_evaluation` | measurement | — | 33 at `f8bce151` | 27 tables |
| 6 | `tally_optimisation` | measurement | — | 33 at `f8bce151` | 38 tables |
| 7 | `tally_contracts` | gate | — | 74 records | **PASS** 195 / 0, 10/10 teeth |
| 8 | `recomputed_tables` | measurement | — | 33 at `f8bce151` | 65 tables |
| 9 | `recomputation` | gate | — | 33 at `f8bce151` | **PASS** 1 901 / 0, 9/9 teeth |

Stages 5–9 are the registry's. The chain **names** them and refuses if the registry does not hold
one, saying which name and which of the two registries it was looked for in: a stage that is
silently skipped turns a chain that ran nine stages into a chain that reports on nine and ran eight.

The stencil stage is worth one sentence because it is new: the forward point `x_i (1 + epsfcn)` is
entered from the reference fixed point and the backward point `x_i (1 − epsfcn)` from **that
forward point's exit**, which is the order the optimiser's own evaluator executes (plan §3.4), so
the pair runs serially and different columns go through the pool. The column set is *derived* — the
committed input file's variable count plus the one column the lifted input file adds where an arm
reads it — and then **checked against the `nvar` each run stamped**, because a rule about two files
can be wrong about one of them.

### 3.3 Which configuration the smoke runs, measured

Cost is model-node executions, which are exact; the wall clock beside them chooses nothing (I-10).
For each configuration the smoke's own job set is priced from the gate records on disk — the median
node calls of one run of each arm it would run, summed.

*Caption: per configuration, the runs the smoke would make and what they cost, from the committed
gate records. "Route" says whether the row is measured or falls back to the declared proxy; every
row here is measured. Wall clock is context.*

| configuration | runs in the smoke | node calls | wall s | route |
|---|---|---|---|---|
| `large_tokamak_nof` | 8 | 158 633 | 125.8 | measured |
| `low_aspect_ratio_DEMO` | 8 | 298 315 | 228.0 | measured |
| **`st_regression`** | **6** | **106 332** | **81.4** | measured |

`st_regression` is cheapest and is what the smoke runs: it is the configuration with the fewest
iteration variables (14) *and* the one where two arms are skipped by a recorded decision (`A0p` and
`B1` compose onto their predecessors at `k = 0`), so it is both the shortest runs and the fewest of
them.

### 3.4 The two separations, each a refusal with a tooth

**A smoke record is never summarised as a measurement.** The run kinds a published population may
contain are *declared* — `stats.MEASURABLE_RUN_KINDS` and, independently,
`analysis.MEASURABLE_RUN_KINDS`, because the analysis re-derives every declaration rather than
importing it — and a record of any other kind is **refused** where a population is built, not
filtered out of it. A filter shrinks a population quietly, which is the error this project has made
three times (trap T11).

**A campaign record is never made by the smoke.** `chain.plan_for` refuses a campaign plan while
`EXECUTION_APPROVED` is `False` or the tree is not the experiment's copy, and the smoke asks for the
smoke plan by name. Resume is closed the same way: `records.is_complete_for` now compares the run
kind, so a record of one kind is never kept for a job of another and a stamp cannot be laundered by
moving a directory.

Both directions are gate **`run_kind_separation`** (new, 6 teeth, no PROCESS run). Its criterion is a
survey of every record under `runs/` by kind: **PASS, 203 compared, 0 mismatched** over 175 records,
of which 28 are covered by a declared tally source, **0 stamped `campaign`**.

*Caption: one row per tooth; each is a deliberate break the gate must catch, with the positive
control that stops the refusal from passing by refusing everything.*

| tooth | the break | must |
|---|---|---|
| a smoke record offered to the tally | a record stamped `smoke` handed to `stats.Population.of` | refuse — **tripped** |
| a smoke record offered to the analysis | the same record handed to `analysis.Population.of` | refuse — **tripped** |
| a gate record is still summarised | a record stamped `gate` handed to the same population | **keep it** — tripped (1 of 1 kept) |
| a campaign plan without approval | the campaign plan composed while `EXECUTION_APPROVED` is `False` | refuse — **tripped** |
| the smoke's plan forged into a campaign | the smoke plan with its run kind changed to `campaign` | refuse — **tripped** |
| resume across run kinds | a `campaign` record offered to a smoke run's resume | not keep it — **tripped** |

---

## 4. The one press (deliverable 2)

Every command below was run under
`/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python`, **from the repository root of the
worktree**, in this order. No number in this report was produced by a shell invocation
(protocol §15).

```bash
PY=/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python
RUNNER=arch_surgery/MDA_partitioning_experiment_v4/experiment_runner.py
V3DECKS=/home/wrutten/projects/PROCESS_surgery/arch_surgery/MDA_partitioning_experiment_v3/runs/_decks

# the one press, at f8bce151 — exit 1, tally_contracts FAILED (§6.1)
$PY $RUNNER --gate all --resume --census-entry evaluation --lifted-from $V3DECKS

# ---- the two defects the press found were fixed and committed at b784158c ----

# the gates the failed chain never reached, plus G1, whose capture the fix changes
$PY $RUNNER --gate switch_neutrality --resume        # exit 1 — FAIL, §6.3
$PY $RUNNER --gate tally_contracts --resume          # exit 0
$PY $RUNNER --gate recomputation --resume --census-entry evaluation   # exit 0
$PY $RUNNER --gate run_kind_separation --resume      # exit 0

# the chain, once, end to end                        # exit 0
$PY $RUNNER --smoke --resume --census-entry evaluation --lifted-from $V3DECKS

$PY $RUNNER --measure all --resume --census-entry evaluation          # exit 0
$PY $RUNNER --artifacts all --census-entry evaluation --resume        # exit 0
$PY $RUNNER --selfcheck                                               # 6/6 PASS
$PY $RUNNER                                                           # preflight READY
$PY arch_surgery/MDA_partitioning_experiment_v4/PROCESS/copy_gates.py all      # ALL GATES PASS
$PY arch_surgery/MDA_partitioning_experiment_v4/PROCESS_diff.py --markdown     # exit 0

# the plan's §4, rendered from the measurement stages' records
$PY $RUNNER --plan-tables write                                       # exit 0
```

**`--gate all` was pressed exactly once.** What followed it was not a second press: it was the four
gates the failed chain never completed (`tally_contracts`, `recomputation`, `run_kind_separation`)
plus `switch_neutrality`, whose capture the §6.2 fix changes. Each is named above with its exit
code, and each verdict records the commit of the records it read.

### 4.1 Runs made, and what `--resume` kept

*Caption: one row per command that starts PROCESS. "Made" is runs executed, "resumed" runs kept
because the directory held a complete record of the same job. Wall clock is context (trap T5) and no
conclusion rests on it.*

| command | runs made | resumed | note |
|---|---|---|---|
| `--gate all --resume` | **140** | 10 | the 10 are the shared cold-flat entry references, made once **inside this press** by the first gate that needs them and kept by the next; not one seeded record |
| `--gate switch_neutrality --resume` (after the fix) | 6 | 0 | G1's after capture, re-made at `b784158c` |
| `--measure all` | 6 | 0 | the output-path contrast runs |
| `--artifacts all` | 0 | 2 | the lifted input files' baseline evaluations, made in the press |
| `--smoke` | 13 | 0 | the chain's own runs |
| **total** | **165** | | ≈ 63 min of summed in-child wall clock at three workers — **context only** |

**`--resume` kept none of the seeded run records.** The worktree was seeded with A62's relocated
records — 116 at `3d64625c`, 47 at `eb38c34a`, and G1's before capture at `fd480aff`. Under the
merged schema **0 of 167** were complete: A53 renamed three record fields
(`module_solve_totals` → `block_loop_totals`, `post_solve_totals` → `defer_per_run_totals`,
`n_prime_calls` → `n_arrangement_method_calls`) and A62 added `exit_audit.instrument{,.restores,
.n_restored,.n_not_restorable}` in parallel, so every seeded record is missing one set or the other.
Measured before the press: 167 records checked, 167 incomplete, 113 missing exactly A53's three,
53 missing A62's four as well.

**That is the contract working** (harness plan amendment 17, standing property (a)) and it was not
weakened. What survives the press is exactly what should: G1's before capture at `fd480aff`, which
the gate never re-makes by design, and 11 records under `gates/exit_audit_diagnosis/` at
`3d64625c`, which `--gate all` does not run at all.

### 4.2 The stamp survey

Every `metrics.json` under `runs/`, by the commit its child stamped.

*Caption: one row per distinct `tree_git_head` over all 188 run records after the whole press.
"Where" names the directories those records sit in. Every record has `status == ok`.*

| commit | records | where |
|---|---|---|
| `f8bce151` | **140** | every gate that makes runs: `reproduction` 30, `predicate_mode` 27, `audit_restriction` 18, `cold_chain` 16, `entry_and_warm` 13, `prime_map` 12, `output_path` 11, `switch_composition` 6, `entry_references` 3, `record_completeness` 2, plus 2 lifted-input baselines |
| `b784158c` | **25** | G1's after capture 6, the output-path contrast 6, the smoke's 13 |
| `3d64625c` | 11 | `gates/exit_audit_diagnosis/` — A62's diagnosis stage, which `--gate all` does not run |
| `fd480aff` | 6 | G1's **before** capture, never re-made (harness plan amendment 13, rule (ii)) |
| *(none)* | 6 | the three configurations' census runs, `record_format: census-1` — a different schema that carries **no tree or commit stamp at all** (§10, finding) |
| **by run kind** | | **173 `gate`, 15 `smoke`, 0 `campaign`** |

---

## 5. The gate table

The full table, with every population, denominator and tooth count, is the experiment plan's §4.1,
rendered there by `--measure gate_table` from the verdict records. The summary line reads:

> **24 PASS, 0 FAIL, 0 not run; 139 of 139 teeth tripped.**

The press itself left that table reading **23 PASS, 1 FAIL, 137 of 137**: G1 failed on it and passed
afterwards at `d6f0fdf4` with two teeth more (§6.3). The section was re-rendered from the records as
they now stand, so the plan reads the standing count, and its population marker names **every**
commit those records carry — `3d64625c`, `b784158c`, `f8bce151`, `fd480aff` — which is what the
marker is for. One ordering property is worth recording: `--plan-tables` renders §4.1 from the
`gate_table` **stage** record, not from the verdict records directly, so a gate re-run after a
`--measure` press needs `--measure gate_table` again before the section is re-rendered. Both are
zero-run stages.

*Caption: the gates whose numbers moved at this tip, or that are new. Every other gate's verdict and
denominator is unchanged from A62's and is in the plan's §4.1. "Compared" is the gate's own headline
denominator, summed where it compares more than one kind of thing, with the parts named in its
record.*

| gate | plan | verdict | compared | mismatched | teeth | what changed at this tip |
|---|---|---|---|---|---|---|
| `reproduction` | GR | **PASS** | 256 | 0 | 8/8 | 20/20 runs re-made at `f8bce151`; 270 in the reference, 14 excluded by name, 256 compared. **This is the one GR at the merged tip** |
| `switch_neutrality` | G1 | **PASS** at `d6f0fdf4` (FAIL on the press) | 2 831 values, 51 319 lines | **0**, 0 | 9/9 | a genuine straddle for the first time; the earlier capture's vocabulary is translated, 72 leaves renamed and compared, 0 differing; §6.3 |
| `tally_contracts` | — | **PASS** | 451 | 0 | 10/10 | 256 published cells (was comparing 270 and failing on 10); 195/195 table checks over 65 tables |
| `recomputation` | — | **PASS** | 1 901 | 0 | 9/9 | 1 863 table cells + 37 values beside them + 1 independence check, over 33 records all at `f8bce151` |
| `run_kind_separation` | — | **PASS** | 203 | 0 | 6/6 | **new** (§3.4) |
| `g0prime` | G0 / G0′ | **PASS** | 77 | 1 | 4/4 | the one mismatch is `process/models/pulse.py`, approved under D14(b), by name |
| `record_completeness` | G7 | **PASS** | 171 | 0 | 9/9 | 89 declared fields in the optimisation phase, 82 in the evaluation phase |
| `capability` | — | **PASS** | 55 | 0 | 15/15 | pressed from the repository root; the decoy tooth confirms the verdict does not depend on the working directory |

---

## 6. What failed, and what was found

Three things, all fixed on this branch. Two were wiring defects, committed at `b784158c`. The
third was a **gate that failed** — reported with its numbers and not worked around — and the
orchestrator then ruled how it should be fixed; that fix is `d6f0fdf4` and the gate now passes.

### 6.1 Defect 1 — the tally's compared set did not follow the reproduction gate's exclusion

**What failed.** `tally_contracts`, on the one press: **260 of 270 published cells reproduced, 10
moved, 0 runs reproduced whole.** Every one of the ten was the same field:

```
MOVED: BR/large_tokamak_nof/seed000 exit-audit maximum (hex) — expected '0x0.0p+0', found '0x1.ca292b56b673fp-8'
MOVED: B0/low_aspect_ratio_DEMO/seed000 exit-audit maximum (hex) — expected '0x0.0p+0', found '0x1.cc23ee7f374eap-8'
…  (10 rows: BR/B0/B3/B1 on the two pulsed configurations; st_regression's four reproduce exactly)
```

**Why.** Ruling **D25** and harness plan §7.1 drop `exit_audit.residual_max_hex` from the
optimisation phase's compared set **by name, with its reason**: the reference's side was measured by
the previous instrument, which did not restore the mesh PROCESS's output path had already changed,
and this revision's sweeps the loop's own map — comparing them compares two instruments. GR
implements that through `reference.compared_fields()`, which is why GR reads **256 of 270**.
`tally.cells_for` still read `reference.REFERENCE_FIELDS` directly, so **one criterion had two
implementations and one of them compared a cell the other does not**.

This is the wiring A53 wrote the derivation for. Its own comment says so: *"Deriving it rather than
writing it out means a later task that drops a field from the compared set — task A62
(exit-audit-restore) will drop the inherited audit residual — drops it here too."* A62 dropped it in
`FIELDS_NOT_COMPARED`, a separate dict that `cells_for` never consulted, and no press before this one
could see it: A54's records predate the instrument change, and A62 reused A53's `tally_contracts`
verdict rather than re-running it.

**The fix.** `cells_for` reads `reference.compared_fields(phase)`, and `reference_cells` now reports
`excluded_by_name` per run — the field, the value the reference holds and the recorded reason —
so the exclusion is named exactly as the gate names it and is never counted as a match. **Re-run:
PASS, 256 compared, 0 mismatched, 195/195 table checks, 10/10 teeth.**

This is not a gate tuned into passing: the criterion was changed by a ruling the project has already
made and implemented once; what was fixed is that the second implementation did not get it.

### 6.2 Defect 2 — G1's "after" capture escaped the completeness contract

**What was wrong.** `gates._capture_after` read:

```python
manifest = neutrality_root(campaign) / "after" / "manifest.json"
if resume and manifest.exists():
    return
```

so with `--resume` the capture never reached `pool.run`, and the *manifest's existence* was the
evidence — which is precisely what `pool.run`'s own docstring says a directory may never be
(*"A directory alone is never evidence: an interrupted run leaves one behind"*). Under the merged
schema all six records of A62's capture are incomplete; the gate kept all six anyway. **G1 therefore
passed the one press over a capture at `3d64625c`** — a commit this tree had not measured — and said
so honestly in its verdict (*"the gate read 6 run record(s) made at `3d64625c`, not all at this
verdict's `f8bce151`"*), which is the only reason it was noticed.

**The fix.** The capture goes to the pool, which decides per job. Harness plan amendment 17's
standing property — *`--resume` cannot cross a schema change, and it is not to be weakened for a
cheaper press* — applies to this capture again. Re-run, G1 re-made all six after-side runs at
`b784158c`: the fix works.

### 6.3 The gate that failed — G1 could not see through a record-field rename

**What failed.** With the after capture re-made, G1 became a genuine straddle for the first time
and **FAILED**:

*Caption: gate G1 at `b784158c`, straddling `fd480aff → b784158c` — **the failing run**, before the
fix. Population: 6 run pairs = 3 configurations × 2 reference arms, every architecture switch unset.
"Values" are deterministic record leaves, "lines" output-file lines; 1 632 values and 45 lines are
excluded as run metadata,
957 of them because the two captures' exit audits were taken by different instruments.*

| arm | configuration | values differing | lines differing |
|---|---|---|---|
| `BR` | `large_tokamak_nof` | 24 / 618 | 0 / 16 173 |
| `AR` | `large_tokamak_nof` | 24 / 399 | 0 / 7 |
| `BR` | `low_aspect_ratio_DEMO` | 24 / 611 | 0 / 16 434 |
| `AR` | `low_aspect_ratio_DEMO` | 24 / 386 | 0 / 7 |
| `BR` | `st_regression` | 24 / 528 | 0 / 18 691 |
| `AR` | `st_regression` | 24 / 361 | 0 / 7 |
| **total** | | **144 / 2 903** | **0 / 51 319** |

**Every one of the 144 has the same reason: "the field is present on one side only."** There is not
a single value that differs where both sides carry the field. The 26 distinct names are exactly
A53's record-field rename and its two sides:

`block_loop_totals.{block_sweeps, moved_constants[], n_call_models, n_call_models_single_block,
n_call_models_with_moved_constant, n_failed, schedule_passes_per_evaluation, solves_by_block,
sweeps_by_block}` and `module_solve_totals.{…}`; `defer_per_run_totals` and `post_solve_totals`;
`n_arrangement_method_calls` and `n_prime_calls`; `first_call_models.n_arrangement_method_calls` and
`first_call_models.n_prime_calls`; `burn_time_constant_intact_at_exit` and `pin_intact_at_exit`.

**Every one of the 144 had the same reason: "the field is present on one side only."** Not one
value differed where both sides carried the field. The 26 distinct names were exactly A53's
record-field rename and its two sides: `module_solve_totals.{block_sweeps, moved_constants[],
n_call_models, n_call_models_single_block, n_call_models_with_moved_constant, n_failed,
outer_pass_hist, inner_solves_by_block, inner_sweeps_by_block}` against
`block_loop_totals.{…, schedule_passes_per_evaluation, solves_by_block, sweeps_by_block}`;
`post_solve_totals` against `defer_per_run_totals`; `n_prime_calls` and
`first_call_models.n_prime_calls` against `n_arrangement_method_calls` and
`first_call_models.n_arrangement_method_calls`; `pin_intact_at_exit` against
`burn_time_constant_intact_at_exit`.

**The orchestrator's ruling, and the fix.** G1 is about **behaviour**, and a record-field rename is
a change of the record's *vocabulary*, not of behaviour. So the earlier capture's leaf paths are
**translated** through `harness.reference.FIELD_NAME_MAP` before anything is compared, and the
translated leaves are then **compared as values** under their new names. No new capture, no
exclusion. Adding the twelve names to the conditional exclusion table would also have made the gate
pass and would have **stopped comparing the block-loop totals across the straddle altogether**;
translation keeps every one of them compared.

The translation is **segment-aware, not prefix-aware**: a map entry names a dotted run of whole
segments and the run is matched anywhere in the path, so `n_prime_calls` reaches
`first_call_models.n_prime_calls` as well as the bare field, and `module_solve_totals` carries its
nine leaves with it. Runs are tried longest first (so `module_solve_totals.outer_pass_hist` is
renamed by the entry that names both segments, not by the entry that names the block), one
replacement is made at the leftmost match, list indices are kept
(`module_solve_totals.moved_constants[2]` stays element 2), and two paths translating onto one is a
**refusal** rather than a silent drop.

**The result.** `--gate switch_neutrality --resume`, from the repository root at `d6f0fdf4`, **0
PROCESS runs** — both captures exist and were resumed:

*Caption: gate G1 at `d6f0fdf4`, a genuine straddle `fd480aff → d6f0fdf4`. Population: 6 run pairs =
3 configurations × 2 reference arms, every architecture switch unset. "Values" are deterministic
record leaves, "lines" output-file lines.*

| arm | configuration | values differing | lines differing |
|---|---|---|---|
| `BR` | `large_tokamak_nof` | 0 / 606 | 0 / 16 173 |
| `AR` | `large_tokamak_nof` | 0 / 387 | 0 / 7 |
| `BR` | `low_aspect_ratio_DEMO` | 0 / 599 | 0 / 16 434 |
| `AR` | `low_aspect_ratio_DEMO` | 0 / 374 | 0 / 7 |
| `BR` | `st_regression` | 0 / 516 | 0 / 18 691 |
| `AR` | `st_regression` | 0 / 349 | 0 / 7 |
| **total** | | **0 / 2 831** | **0 / 51 319** |

**PASS. 9/9 teeth.** The verdict states the translation, as required: **72 leaves of the earlier
capture were renamed** through `harness.reference.FIELD_NAME_MAP` (**9 entries**) and then compared
as values, never excluded — **72 compared, 0 differing**. Every renamed leaf and every mismatch
carries `renamed_from_the_earlier_vocabulary`, so a reader can tell a translated comparison from an
untranslated one without leaving the record.

**All 144 disappeared through the map and none through a new exclusion**, and the arithmetic says
so on its face: each rename produced *two* one-sided leaves (the old name absent on the after side,
the new name absent on the before side), so 72 renames × 2 = **144**; and the compared denominator
fell by exactly 72, **2 903 → 2 831**, because each pair of one-sided paths became one compared
path. The excluded count is **1 632, unchanged** from the failing run — not one leaf was excluded to
make this pass. `--measure exclusion_review` at the same tip reports G1's set as **126 names, 36
structural and unconditional, 34 conditional on the field's own presence and 57 conditional on the
instrument stamps**, and puts **1 022 further leaves back into the comparison** over this pairing.

**The two new teeth.**

*Caption: one row per tooth added with the translation; each is a deliberate break the translated
comparison must catch.*

| tooth | the break | must | result |
|---|---|---|---|
| `a_renamed_field_moved_by_one` | a record rewritten into the earlier vocabulary compares clean (0 of 864 differing, 11 leaves renamed); then one renamed integer, `n_prime_calls`, moved 0 → 1 under its **old** name | be caught and **named under its new name** `n_arrangement_method_calls`, flagged as renamed | **tripped**, 1 of 864 |
| `a_one_sided_leaf_the_name_map_does_not_cover` | a field the map does not name, added to the earlier side alone | still be a mismatch, and **not** be reported as a rename | **tripped**, 1 of 865 |

Together they are the load-bearing pair: the first says the translation renames the field and still
compares its value, the second says it covers renames and nothing else.

**Two things the ruling did not close, recorded rather than acted on.** The before capture is still
A62's, made at `fd480aff` for A62's driver-instrument change, while A55 changes no driver file; and
the straddle therefore spans four merges. G1's claim at this tip is exactly what its population
sentence says it is — a neutrality result across `fd480aff → d6f0fdf4` — and not a statement about
A55's harness changes alone.

---

## 7. The plan's §4, filled (deliverable 3)

`harness/plan_tables.py` renders `EXPERIMENT_PLAN.md` §4 from the measurement stages' own records
under `runs/gates/<stage>/measurements.json`, and `experiment_runner.py --plan-tables {show,write}`
is the stage that runs it. Nothing in the renderer computes a number: every table, caption,
denominator and grid is the emitting stage's.

*Caption: one row per subsection of the plan's §4 and the stage whose record fills it. "Tables" and
"cells" are what was rendered; "not produced" are tables a stage declined to emit, each with its
reason in the document.*

| §4 subsection | rendered from | tables | not produced |
|---|---|---|---|
| 4.1 Gates | `--measure gate_table` | 1 (24 rows) | — |
| 4.2 The evaluation phase | `--measure tally_evaluation` | 27 | — |
| 4.3 The optimisation phase | `--measure tally_optimisation` | 38 | 6 |
| 4.4 The same cells, computed a second time | `--measure recomputed_tables` | 65 | 6 |
| **total** | | **131 tables, 3 620 cells** | |

The six not produced are the `B1·B3` arm groups' check 1, check 2 and check 4 on the two pulsed
configurations: that arm group carries no `B0` run and every pair of those checks is anchored on it.
Each is named in the document with that reason rather than silently absent.

**What the cells are over is stamped on the section and on every caption.** The §4 heading reads
*"the **gate** population — not the campaign — rendered from the records at `3d64625c`,
`b784158c`, `f8bce151`, `fd480aff`; the campaign fills the section again after execution approval"*,
the full statement follows it (record count, commits, run kinds, audit positions, rulers, and the
exit-audit instrument `whole_data_structure_derived_set`, all read back from the records rather than
written down), and **every one of the 131 captions carries the short form**: *"Population: the gate
runs at …, one or two seeds per arm — not the campaign, which has not run."*

The renderer refuses rather than guessing: a stage that has written no record, a stage that emitted
no table (a section with no population is not a section), and a plan document in which §4's heading
or §5's has moved or been reworded.

---

## 8. Autonomous decisions, each with its reversal

*Caption: one row per decision taken without asking, with the evidence for it and the single place a
reviewer changes to reverse it.*

| # | decision | why | reversal |
|---|---|---|---|
| 1 | The smoke and the campaign are **one** chain, parameterised | the orchestrator's instruction, and a smoke written separately reports on code the campaign does not run | split `chain.run`; one line at each of two call sites |
| 2 | The chain's records live under `runs/<plan name>/`, never under `runs/gates/` | the tally reads declared sources under `runs/gates/`; putting the chain's records there would make the smoke refusal depend on a directory layout instead of a decision | `chain.chain_root`, one line |
| 3 | **`AR` is entered from the same displaced snapshot as every other evaluation-phase arm** — **awaiting the user's ruling**; the orchestrator is putting this reading and the `PAIRED_ARMS` comment to the user side by side, and the code is unchanged meanwhile | plan §3.4 (*"campaign entries are … perturbations of that snapshot … each is evaluated by one `call_models` under each arm"*) and §3.3's binding rule that `AR → A0`'s ratio is published only beside both audit residuals — a ratio between a cold-entered arm and a warm-entered one would be a mixture of the entry and the arm. **Note the contrary comment in `gate_entry.PAIRED_ARMS`** (§10) | `chain.stage_evaluation_displaced`: `entry_state=None` for `AR` |
| 4 | An unsummarisable run kind **raises** at population construction rather than being excluded and counted like `force_maxcal` | a budget-capped demonstration is a member of the population that must be named; a smoke record is not a member at all | the one branch in each of `stats.Population.of` and `analysis.Population.of` |
| 5 | The run kind joins `records.is_complete_for`'s job identity | a record's kind is the only thing that says what it may be used for, so keeping one across kinds launders the stamp by moving a directory | drop the parameter; `pool.run` stops passing it |
| 6 | The smoke runs the stencil regime at **one column per arm** rather than skipping it | a stage no smoke presses is the stage the campaign's first press discovers. The restriction is recorded in the stage record and printed, so no table can be computed over it as the regime | `ChainPlan.stencil_columns`, one field |
| 7 | Campaign evaluation-phase seeds are 1–25 (all displaced); optimisation-phase starts are 0–24 (`seed000` unperturbed) | plan §3.4 and §3.5 respectively | `chain.campaign_plan`, two lines |
| 8 | `--plan-tables` is a stage of the runner, not a separate script | protocol §15: no stage may exist only as a shell invocation | the two options |
| 9 | The renderer refuses a plan document whose §4 or §5 heading has moved | a renderer that writes into the wrong part of a shared document is worse than one that does nothing | `plan_tables.write` |
| 10 | The two wiring defects of §6 were **fixed on this branch**; G1's failure was **reported and referred**, and fixed only after the orchestrator ruled how | protocol §6 puts the fix on the same branch, but the choice between translating a rename and excluding it changes what G1 compares for ever, which is a ruling and not a preference. The ruling: translate, never exclude | `compare_records(name_map=…)`; passing `None` restores the untranslated comparison and the 144 |
| 11 | After the failed chain, the four gates it never completed were re-run individually rather than pressing `--gate all` again | the brief forbids a second press; neither fix changes what any run computes, so the 20 verdicts at `f8bce151` stand over records that did not change | — |

---

## 9. Limits

- **No timing anywhere is evidence** (I-10, trap T5). Every wall clock in this report is summed
  in-child progress information, taken on a contended machine, and no verdict reads one.
- **The gate population is one or two seeds per arm.** Every cell in the plan's §4 is over it. It
  says nothing about the campaign's twenty-five, and the §4 heading and all 131 captions say so.
- **The smoke's stencil stage runs one column of the design vector per arm**, not the regime. The
  restriction is in the stage record; no table is computed over it.
- **The smoke's own 13 records are summarised by nothing**, deliberately — that is what the two
  refusals of §3.4 are for. So the smoke proves the chain *runs*; it proves nothing about what the
  campaign's numbers will be.
- **The chain has never been pressed with `run_kind = "campaign"`.** What is exercised is the
  refusal, not the campaign path's behaviour at 949 runs. §11 lists what its first press will do
  differently.
- **G1's straddle spans four merges**, two of them record-schema changes, and its before capture is
  A62's rather than one made at A55's base. It passes, and what it certifies is neutrality across
  `fd480aff → d6f0fdf4` — not a statement about A55's harness changes alone. Read §6.3 before
  quoting any G1 number from this tip.
- **The translation is only as good as the map.** `reference.FIELD_NAME_MAP` has 9 entries; a rename
  that never reaches it would read as 144 did. The second tooth is what keeps that failure loud.
- The 20 gate verdicts from the one press are at `f8bce151` while four are at `b784158c`. Neither
  fix changes what a run computes, but no single commit carries every verdict, and each verdict
  records its own.

---

## 10. Findings that are nobody's task yet

1. **`gate_entry.PAIRED_ARMS`'s comment overreaches.** It says the reference arm *"is entered from
   the input file's own point and never from a snapshot, which is what 'PROCESS as shipped' means."*
   That is true of G6's own population, and false of the campaign: plan §3.4 enters every
   evaluation-phase arm from the same displaced snapshot, and §3.3's binding rule on `AR → A0`
   requires it. I did not edit the comment (it is G6's), and decision 3 of §8 records the reading I
   implemented. **The orchestrator is putting both readings to the user**; whichever way it is
   ruled, `chain.stage_evaluation_displaced` is the one line, and the ratio it produces changes
   meaning, which is why it is a ruling and not a preference.
2. **The census record carries no commit stamp.** `runs/census/*/metrics.json` has
   `record_format: census-1` with `tree`, `tree_git_head` and `tree_git_branch` all `null`. Six such
   records exist. They are not run records a tally reads, but a record a survey cannot place at a
   commit is the shape traps T6 and T10 warn about, and the stamp survey has to report them as
   *(none)*.
3. **`--resume` keeps a record made at another commit** as long as it is complete for the same job.
   That is the declared behaviour and the verdicts state the straddle, but it means "resumed" and
   "made at this commit" are different questions and only the stamp survey answers the second.

---

## 11. Handover to the orchestrator's whole-implementation assessment

### 11.1 What the button can say now

One press of `experiment_runner.py` runs: the preflight (READY), every registered gate cheapest-first
and after what it reads, every measurement stage, every artifact stage, the harness's own six
self-checks with their teeth, the copy's two gates and the diff of every change the experiment has
made to PROCESS — and **the campaign's own chain end to end**, as the smoke, reaching an independent
recomputation of every published cell with 0 mismatches over 1 901 values. Every failure path is
reachable from the same entry point: the campaign's refusal, a missing stage, a gate that fails, a
run against the wrong tree, a switch the tree does not implement.

### 11.2 What it cannot yet say

- **That A55's own changes are neutral.** G1 passes across `fd480aff → d6f0fdf4`, but its before
  capture is A62's; a capture at A55's base `c919f4c8` is what would bind this task alone.
- **Anything about the campaign's numbers.** Every cell is a gate figure over one or two seeds.
- **That the campaign path works at scale.** 949 runs, 3 configurations, 25 seeds and a `campaign`
  record kind have never been executed; only the 13-run parameterisation has.
- **That the stencil regime is right.** One column per arm is exercised, not `2 (nvar + 1)`.

### 11.3 Open items I met

*Caption: one row per open item this task touched, and what it now stands at. None was edited in the
queue, the harness plan or the improvement list — §12 says what they should gain.*

| item | where it stands after this task |
|---|---|
| **I-20** (the empty `PULSE` block) | untouched. The chain does not change the schedule; the disclaimer obligation is unchanged |
| **I-21** (what else the output pass leaves inconsistent) | **still open, and I did not close it.** The queue assigns it to "the owner of G9 (A55 or a task after it)". The measurement it wants — one `after_run` audit on a **campaign-composed** `B1` — is still refused outside GR, so it needs a declared gate. The chain now makes campaign-composed `B1` runs routinely (`--smoke` on a pulsed configuration would make one), so the cheapest route is a gate that takes the `after_run` audit on one such run; that is a new task |
| **the fourth ladder rung** | untouched: `RUNGS` still carries six steps and the rung gate compares 98 cells over them. No rung was added or removed |
| **`mixed` adoption** | not adopted. `Campaign.predicate_mode_default` is still `frozen`; G8 passes at this tip with the frozen ruler as default and both rulers recorded on every audit. The §4.2.5 table is rendered with both columns |
| **I-11 / worktree discipline** | the worktree was created by the orchestrator and nothing was written in the main checkout or in any sibling clone |

### 11.4 What the campaign's first press will do that the smoke did not

*Caption: one row per way the campaign's parameterisation differs from the smoke's, with the run
count from the budget the preflight prints. The chain is the same code in both columns.*

| | smoke (measured) | campaign (from the budget print) |
|---|---|---|
| configurations | 1 (`st_regression`) | **3** |
| entry references | 1 | **3** |
| displaced-entry evaluations | 3 (1 seed × 3 arms) | **275** (25 seeds × the active evaluation arms) |
| stencil evaluations | 6 (1 column × 3 arms × 2 signs) | **396** (every column; the plan's own upper bound `2 (nvar + 1)` per arm is 418, and the chain derives the columns from the input file each arm reads) |
| optimisations | 3 | **275** |
| **total runs** | **13** | **949** |
| record kind | `smoke` | `campaign` |
| summarised by the tally | **no — refused** | yes |
| approval | none needed | **`EXECUTION_APPROVED` must be `True`** and the tree must be the experiment's copy |

Wall clock, as context only and from this task's own runs at three workers: the smoke's 13 runs took
about 2½ minutes of summed in-child time; the press's 140 took about 50. A linear extrapolation to
949 runs is **not** a prediction — the campaign's arms and seeds are not this population — and no
decision should rest on it.

### 11.5 What the queue, the harness plan and the improvement list should gain

*I edited none of them.* What they should record:

- **Harness plan, Appendix A, a new amendment: H8 delivered.** `harness/chain.py` — the campaign's
  stages written once and parameterised; `--smoke` reaches `--verify` with 0 mismatches over 1 901
  values from one press, 13 runs, records stamped `smoke`. `harness/plan_tables.py` and
  `--plan-tables` render the experiment plan's §4 from the measurement stages' records (131 tables,
  3 620 cells, no cell typed by hand). Gate `run_kind_separation` (6 teeth): a smoke record is
  refused by both population implementations, a campaign plan does not compose without approval, and
  resume compares the run kind. `experiment_runner.stage_campaign` is the chain's refusal and its
  budget rather than a stub.
- **A standing rule, from defect 2:** a gate's capture may not decide to keep runs on the strength of
  a manifest, an output directory or any other artifact that is not the run record itself. Only
  `pool.run`'s completeness contract decides.
- **A standing rule, from defect 1:** where one criterion has two implementations, the *declaration*
  is shared and only the computation is duplicated. `reference.compared_fields()` is the declaration;
  a second reader of `REFERENCE_FIELDS` is the defect.
- **TRAPS.md**, candidate T13, if the orchestrator judges it worth one: *a `--resume` that consults
  anything but the record is not a resume.* Defect 2 is its measured instance — six incomplete
  records kept, a straddle reported against a commit the tree had not measured, and the only reason
  it surfaced was that the verdict prints the commits of the records it read.
- **A standing rule, from §6.3:** a **record-field rename is a change of the record's vocabulary and
  not of the copy's behaviour.** A gate that compares two records across one translates the earlier
  side through `reference.FIELD_NAME_MAP` and keeps comparing the field; it never excludes it. The
  map is the one place a rename is written down, and a rename that does not reach it will read as a
  difference — which is the loud failure, and is what the second new tooth protects.
- **The A55 row:** H8 delivered; 24/24 gates PASS, 139/139 teeth; G1 failed on the press (144 of
  2 903, all of them A53's rename) and passes at `d6f0fdf4` with the vocabulary translated, 72
  leaves renamed and 0 differing; two wiring defects fixed; records to be relocated by the retire
  script.
- **The AR entry (§8 decision 3) is a methodology question the orchestrator is putting to the
  user**, with this task's reading and the `PAIRED_ARMS` comment side by side. Nothing in the code
  was changed for it and nothing waits on it: the chain runs either way, and the one line that
  reverses it is named.
- **I-21 stays open** (the orchestrator's ruling): the `after_run` audit on a campaign-composed `B1`
  is now cheap to reach because the chain makes such runs, but the position is refused outside GR,
  so it needs a declared gate — a new task, and the user decides.

---

## 12. Change log

*Caption: append-only; one row per change to this branch, in order.*

| commit | what |
|---|---|
| `f8bce151` | `harness/chain.py` (the chain, both plans, the stencil stage, gate `run_kind_separation`); `harness/plan_tables.py`; the run-kind refusals in `stats.py` and, independently, `analysis.py`; the run kind in `records.is_complete_for` and `pool.run`; `--smoke` and `--plan-tables`; `stage_campaign` rewritten; README §10, §15, §16 |
| `b784158c` | defect 1 — `tally.cells_for` reads `reference.compared_fields()` and `reference_cells` names every excluded field; defect 2 — `gates._capture_after` hands its capture to the pool |
| `87951248` | this report, and the experiment plan's §4 rendered by `--plan-tables write` |
| `d6f0fdf4` | G1's comparator translates the earlier capture's leaf paths through `reference.FIELD_NAME_MAP`, segment-aware, and compares the renamed leaves as values; the verdict states the translation; two new teeth. No exclusion added, no capture made. G1 PASS 0 / 2 831, 9/9 |
| `2f0ad599` | the report's §6.3, §1, §5, §8, §9, §11 and change log brought to the fixed gate |
| `14d3abdd` | the experiment plan's §4 re-rendered by `--measure gate_table` then `--plan-tables write`, zero PROCESS runs: §4.1 now reads **24 PASS, 0 FAIL, 139 of 139 teeth** with G1 PASS on the straddle `fd480aff → d6f0fdf4`, and the population marker names every commit the records carry. Documents only |

---

## 12. Orchestrator's critical assessment (protocol §5)

*Written 2026-09-11 at `611f4527`, before the merge. Verification by checks that differ from the
agent's; no PROCESS run was made for this review.*

**What was checked, and how it differed.**

* **Scope.** `git diff --name-only c919f4c8..611f4527`: `harness/chain.py` and `plan_tables.py`
  (new), `gates.py`, `pool.py`, `records.py`, `stats.py`, `tally.py`, `analysis.py`, the runner,
  the README, the experiment plan (46 hunks, every one inside §4) and this report. Nothing under
  `…_v4/PROCESS/`, the repository-root `process/`, the queue or the harness plan;
  `harness/config.py` untouched, `EXECUTION_APPROVED = False`.
* **Record kinds, read from every record.** 188 records under `runs/`: `campaign_run_kind` is
  `gate` on 173 and `smoke` on 15; **0 `campaign`**. Stamps: 140 at `f8bce151`, 25 at `b784158c`,
  11 at `3d64625c` (the diagnosis stage, which `--gate all` does not run), 6 at `fd480aff` (G1's
  before capture), 6 with no stamp (the census records — the agent's finding, recorded below).
* **Verdicts.** 28 verdict records, all PASS; G1's at `d6f0fdf4`, 9 teeth, its provenance naming
  the after capture at `b784158c`.
* **The translation, read.** `translate_path` matches a run of whole bare segments anywhere in the
  path, longest entry first, one replacement at the leftmost match, list index kept;
  `translate_leaves` refuses two paths translating onto one. The renamed leaves are compared, and
  the verdict counts them (72 renamed, 0 differing). The arithmetic the agent gives holds: 144
  one-sided leaves = 72 × 2; the compared denominator fell by exactly 72; `n_values_excluded`
  unchanged at 1 632. No exclusion table changed.
* **The merge.** A trial merge onto trunk `3173b23d` auto-merged without conflicts; the merged
  harness compiles, `--selfcheck` passes, and the preflight at the merged tree refuses the campaign
  for exactly two reasons (approval off; a campaign record may not be made while it is off) and
  prints the budget: 3 + 275 + 396 + 275 = **949 runs**.

**Assessment of the decisions.** Accepted: the one chain parameterised by run kind and seed count
(my scope addition; the campaign stage was a refusal stub naming stages that did not exist); the
two separations as refusals with teeth, in both directions; `is_complete_for` comparing the run
kind so `--resume` cannot launder a stamp; the two wiring defects fixed on the branch (the tally
consulting `REFERENCE_FIELDS` instead of `compared_fields()`, and `_capture_after` trusting a
manifest); the G1 translation as ruled. **Not ruled here, put to the user:** the reference arm's
entry in Phase A — the chain enters `AR` from the same displaced snapshot as `A0`/`A0p`/`A1`, and
`gate_entry.PAIRED_ARMS`'s comment says the opposite; one line reverses it and the `AR → A0` ratio
changes meaning. Recorded as a proposed decision awaiting the user's ruling.

**Three standing consequences, recorded at the merge.**

1. **A `--resume` that consults anything but the record is not a resume** (TRAPS T13): the
   manifest defect is the second instance of this shape (the first was the hard-coded
   `resume=True` A52 found), and both passed a press before a stamp survey caught them.
2. **A record-field rename is a change of vocabulary, not of behaviour**: a gate comparing across
   one translates the earlier side through `reference.FIELD_NAME_MAP` and keeps comparing the
   field; a rename that does not reach the map reads as a difference, which is the loud failure.
3. **§4 is rendered from the `gate_table` stage record, not from the verdicts**: a gate re-run
   after a `--measure` press needs `--measure gate_table` again before `--plan-tables`, or the
   section silently keeps the older verdicts. The agent's first re-render reproduced the failing
   table byte for byte for that reason. This is the stale-stage shape A54 closed for the tally
   with a provenance check, and `gate_table` / `plan_tables` do not have that check yet —
   recorded as an issue, with the census records' missing stamps.

**Limits that stand.** The §4 tables are the gate population at the commits the marker names,
not the campaign; the smoke is 13 runs on one configuration at one seed and is summarised by
nothing; the campaign's first press is 949 runs with records stamped `campaign`.

**Verdict: approved for merge at `611f4527`.** H8 done; the implementation is complete pending the
`AR` ruling and the whole-implementation assessment.
