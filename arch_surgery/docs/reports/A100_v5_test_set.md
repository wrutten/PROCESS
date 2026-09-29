# A100 (v5-test-set) — DR11: the loop's test set as a switch (the census set of D32 at 1e-8, V4's whole write set at 1e-6 as the fallback of D39), the census stage, gate GT, the mixed ruler removed

> **Document status** — **OPEN.** Task **A100 (v5-test-set)**, branch `A100-v5-test-set` (worktree
> `.claude/worktrees/A100-v5-test-set`, seeded with A99 (v5-schedule-and-prime)'s relocated records
> `idf_probe/runs/A99_runs/v5_schedule_and_prime/`), base **`66bfa240`** (= `architecture_surgery` at
> dispatch, the merged tip of A98 (v5-reporting-trim) and A99). Written 2026-09-29 under **D37**
> (autonomous mode): the driver change merges on the orchestrator's assessment; **its full diff is §4**
> for the user's review on return; every decision taken without the user is in §11 with the word
> *autonomous* and its reversal. Commits: the harness prep before the change **`b1bb1594`**, the driver
> change **DR11 = `5980c5dc`**, one pool fix **`60434c52`** (harness only; `git diff 5980c5dc 60434c52 --
> …_v5/PROCESS/` is empty), then the harness-only commits `3d56c4ad` → `ba440ecd` (twelve, each named in the change log; `git diff 60434c52 ba440ecd -- …_v5/PROCESS/process/` is empty — the one file under `PROCESS/` touched after DR11 is `CHANGES.md`, at `3d56c4ad`). The physics is untouched (`g0prime` PASS at every press).
> Every number below was written by a gate or stage of the committed harness
> (`experiment_runner.py --gate <name>`, `--census`, `--smoke-test-set`, `--measure gate_table`; verdict
> records under the worktree's `MDA_partitioning_experiment_v5/runs/…`) or by `run_stamp_survey.py`;
> none was typed from inspection. Records are moved before retirement to
> `arch_surgery/idf_probe/runs/v5_test_set/` (§9) so the retire script lands one tree. Arm names are
> today's (A78 (arm-renames)). Vocabulary: a **test set** is which components of the coupling state
> `y` a block loop tests for convergence; the **census set** is the set measured at run time (the
> components a sweep reads before it first writes them and writes later in the same sweep); the
> **write set** is every component the block writes, V4's test; τ is the tolerance; a **twin** is the
> same optimisation without the census instrument; the **fallback** is the write set at 1e-6.

---

## 1. Verdict

**DR11 is built, pressed and neutral where it must be; the census set is measured and bound; the gate
table after it reads 28 PASS, 1 FAIL (`tally_contracts`, failing at the merged tip before this task on
two causes that are not this task's), 0 NOT RUN, 164 of 165 teeth** (`--measure gate_table --resume` at
`ba440ecd`, §8.2). In eight lines:

1. **The switch.** `PROCESS_ARCH_TEST_SET ∈ {census, write_set}` with `PROCESS_ARCH_TEST_SETS` (the
   artifact, required iff census), τ following the set (`census` 1e-8, `write_set` 1e-6), both in the job
   identity (rendered only off V4's values); `write_set` is V4's predicate exactly (D39); the `mixed`
   ruler and `PROCESS_ARCH_PREDICATE` are gone; the driver diff is §4 in full (31 edits, three files).
2. **G1 straddling DR11 alone PASSes** (`b1bb1594 → 60434c52`, 6 pairs, 3 642 leaves + 51 319 output-file
   lines, 0 differing, 9/9 teeth) after 27 harness-stamp leaves were declared by name (§7.1).
3. **GC straddling DR10 → DR11 under the fallback PASSes** (22 pairs, 3 957 count leaves + 46 125
   components, 0 differing, 3/3 teeth; the prime count `identical`) after one absolute-path leaf was
   declared (§7.2).
4. **The census** (`--census`, 16 of 16 censused optimisations reproduce their twins on six fields to the
   `norm_objf` bit): `B0`/`B2`'s rows equal A92's Table 1 to the bit; the flat sets are A92's (79/78/75);
   `M3` carries two inert first-wall components since DR10 on every configuration; `B1`'s set is `B0`'s
   minus the burn time (78/77), measured; `added_from_prior` is empty everywhere (§5).
5. **GT PASSes** (8 full-set runs, 8 binding drops of which **3 bite** — `large_tokamak_nof`, all three
   arms, on `pf_coil.stress_z_cs_self_midplane_profile`: one sweep fewer, 203–270 of 840 exit components
   differ — 5 not individually binding; 8 of 8 controls bit-identical; 4/4 teeth; §6).
6. **G6 at census/1e-8 PASSes** (8 pairs, 5 warm, 6 717 compared, 0 differing); G5, G7, G9, the artifacts
   row and every self-check PASS; GR is read from its `d6c246a1` verdict, never pressed (§2.1).
7. **The smoke pairs** (§8.1): the `write_set` pair reproduces A94's seeded GR records to the `norm_objf`
   bit (IDENTICAL on every compared field); the supplementary `st_regression` `B2` at census/1e-12
   reproduces A96's record (570 evaluations, 10 iterations, 22 092 node calls, `-0x1.096acf3342df8p+4`);
   under census `B0` costs +4.6 % node calls and `B2` −18.2 % against the fallback; the per-evaluation
   `B2/B0` ratio is 0.482 under census beside A93's 0.48–0.49, and 0.616 under the fallback.
8. **`tally_contracts` stays FAIL** (§2.2, §8.2): its reference cells are now 236/236 with 20 of 20 runs
   reproduced whole (after the `n_prime_calls` exclusion the orchestrator ruled and after GR's jobs were
   given V4's criterion explicitly, `ba440ecd`); what fails is its population check — the 20 GR records
   made before DR11 lack the fields DR11 added, and GR never re-makes them — and one tooth that cannot
   trip on the gate population. Both were FAIL at `66bfa240`; neither touches what this task changed.

---

## 2. Step 0 — the merged harness (A98 + A99) pressed once at `66bfa240`, before any change

`experiment_runner.py --gate all --resume` on the seeded records, then the gates the chain had not
reached one by one, then `--measure gate_table --resume`. Logs under `runs/_press_logs/A100_press0*.log`;
stamp survey `runs/_press_logs/A100_stamp_survey_step0.json`.

**Table 2.1 — the merged harness before DR11.** *One row per registered gate: the verdict, what it
compared (the denominator) and how many differed, teeth tripped of declared, the commit the verdict is
stamped with. Population: the 29 registered gates at `66bfa240`; every run-needing gate re-made its runs
under `--resume` where A99's schema change (`schedule_resolution`) had made the seeded record incomplete
— 57 PROCESS runs in this press (40 in the chain, 11 for `output_path`, 6 for `written_file_gap`), which
is what the brief expected for G4–G7 and G9.*

| gate | plan | verdict | compared | mismatched | teeth | stamped at |
|---|---|---|---|---|---|---|
| `g0prime` | G0 | PASS | 77 | 1 (the approved `pulse.py`) | 4/4 | `66bfa240` |
| `copy_identity` | — | PASS | 224 | 8 (the permitted-edit files) | 12/12 | `66bfa240` |
| `edit_behaviour` | — | PASS | 3 | 0 | 1/1 | `66bfa240` |
| `self_containment` | — | **PASS** (A98's fix of I-32 holds: 51 files, 0 findings) | 51 | 0 | 1/1 | `66bfa240` |
| `composition` | — | PASS | 42 | 0 | 7/7 | `66bfa240` |
| `rungs` | — | PASS | 98 | 0 | 3/3 | `66bfa240` |
| `provenance` | — | PASS | 4 | 0 | 4/4 | `66bfa240` |
| `data` | — | PASS | 17 | 0 | 6/6 | `66bfa240` |
| `run_path` | — | PASS | 12 | 0 | 12/12 | `66bfa240` |
| `resume_identity` | — | PASS | 168 | 0 | 10/10 | `66bfa240` |
| `capability` | — | PASS (11 retired names identical in registry and driver; 1 pending, `PROCESS_ARCH_PREDICATE`) | 54 | 0 | 5/5 | `66bfa240` |
| `artifacts_check` | — | PASS | 95 | 0 | 3/3 | `66bfa240` |
| `artifacts_derive_inputs` | — | PASS | 2 | 0 | 4/4 | `66bfa240` |
| `artifacts_census` | — | PASS | 81 | 0 | 5/5 | `66bfa240` |
| `artifacts_per_run` | — | PASS | 16 | 0 | 2/2 | `66bfa240` |
| `record_completeness` | G7 | PASS (2 runs re-made) | 175 | 0 | 9/9 | `66bfa240` |
| `count_neutrality` | GC | PASS (read: the `DR9__DR10` straddle, 22 pairs) | 50 110 (3 985 + 46 125) | 0 | 3/3 | `66bfa240` |
| `prime_map` | G2 | PASS (resumed) | 17 591 (5 026 + 12 565) | 0 | 3/3 | `66bfa240` |
| `audit_restriction` | G4 | PASS (18 runs re-made) | 12 | 0 | 6/6 | `66bfa240` |
| `entry_and_warm` | G6 | PASS (16 runs re-made) | 6 717 | 0 | 3/3 | `66bfa240` |
| `switch_composition` | G5 | PASS (6 runs re-made) | 144 | 0 | 4/4 | `66bfa240` |
| `switch_neutrality` | G1 | PASS (read: A99's DR10 straddle `e5137707 → a0de2e13`) | 55 311 (3 992 + 51 319) | 0 | 9/9 | `66bfa240` |
| `reproduction` | GR | PASS **as read from the seeded verdict** (`d6c246a1`; the gate itself was not pressed to completion — §2.1) | 256 | 0 | 8/8 | `d6c246a1` |
| `output_path` | G9 | PASS (11 runs re-made) | 3 879 | 0 | 4/4 | `66bfa240` |
| `written_file_gap` | — | PASS (6 runs re-made) | 42 | 0 | 4/4 | `66bfa240` |
| `tally_contracts` | — | **FAIL** (§2.2) | 595 (339 + 256) | 31 | 16/17 | `66bfa240` |
| `run_kind_separation` | — | PASS | 194 | 0 | 7/7 | `66bfa240` |
| `stage_provenance` | — | PASS | 11 | 0 | 5/5 | `a0de2e13` |
| `test_set` | GT | NOT RUN (A98's declared placeholder, refuses) | — | — | —/1 | — |

**27 PASS, 1 FAIL, 1 NOT RUN; 160 of 162 declared teeth tripped** (`--measure gate_table --resume` at
`66bfa240`, `runs/gates/gate_table/measurements.json`, log `A100_press0e_gate_table.log`). The stamp
survey after the press: **180 run records** — 56 at `66bfa240` (this press), 40 at `a0de2e13`, 39 at
`e5137707`, 22 at `3c46287b`, 6 at `f93d1df1` (A99's captures and GC sides), 17 at `d6c246a1` (16 of
GR's pool records and its teeth scratch record).

### 2.1 Result: GR is not read under `--resume` on the merged harness — it re-makes

The brief said GR "reads its record — run-once". It did not. A98's `_run_once` wrapper refuses a press
*without* `--resume`; with it the body calls `reproduction.stage(resume=True)`, whose
`pool.run_all(resume=True)` re-makes every record the current contract finds incomplete — and A99's
`schedule_resolution` field made all 24 seeded records incomplete. `--gate all --resume` reached GR
after `switch_neutrality`, printed "3 evaluation-phase reference run(s), then 20 reference runs at 3
workers", kept the three references and **began deleting and re-making the twenty**. I stopped the press
(`TaskStop`) as soon as the log showed it; the first three jobs (`BR` seed 0 on the three
configurations, W = 3) had already had their `metrics.json` removed and PROCESS started. I restored those
three directories byte-for-byte from the relocated A99 tree
(`idf_probe/runs/A99_runs/v5_schedule_and_prime/gates/_runs/B_BR_{large_tokamak_nof_seed000_gate_446fd13a…,
low_aspect_ratio_DEMO_seed000_gate_e40c5e21…, st_regression_seed000_gate_538041e4…}`; `diff -rq` clean
on all three). Eight other GR pool records had already been re-made at `66bfa240` earlier in the same
press by gates sharing their identity (G6's pairing runs are GR's `A0`/`A2` seed-1 evaluations; G4/G5
share others) — expected, and the reason 17 and not 25 records remain at `d6c246a1`. **GR's verdict
record is what GR is** (`gates/reproduction/gate.json` at `d6c246a1`, 20/20, 256/0, 8/8); its pool
records are now shared with the other gates at the current contract. A second finding from the same
press: `--jobs reproduction` refuses on this tree — GR's unnamed `AR` substitute job resolves by digest
to five directories (G1's `before`/`after`, the archived straddle's two, the input-file stage's baseline
evaluation) — I-29's remaining edge on an *unnamed* job; reported in §10, not fixed here (the
orchestrator's ruling).

**Fix, at the orchestrator's ruling (commit `b1bb1594`):** the run-once body under `--resume` **reads the
recorded verdict** — `gates/reproduction/gate.json`, archived on first read as
`verdict_at_d6c246a1.json` and read from the archive thereafter — refuses when it is absent or its stamp
is not the copy commit (`registry.RUN_ONCE_COMMIT`), never calls the stage, and says in its output that it
is a read of the copy-commit verdict, not a press (`read_of_the_recorded_verdict` in the outcome). Pressed
at `b1bb1594`: PASS, 256/0, 8/8 teeth read from the record, 0 runs.

### 2.2 Result: `tally_contracts` FAILs at the merged tip — three causes, one of them DR10's

Pressed alone at `66bfa240` (`A100_press0b_tally_contracts.log`): **FAIL**, 595 checks, 31 mismatched,
16/17 teeth.

1. **The reference cells: 253/256, 17 of 20 runs reproduced whole.** The three differing cells are
   *"MOVED: A2/<configuration>/seed001 arrangement-method calls — expected 13 / 13 / 15, found 1"* on
   the three GR records that G6 re-made under DR10 (the prime once per evaluation). The one count DR10
   declared changed was not excluded by name from the reference-cells check. **Fix, at the
   orchestrator's ruling (`b1bb1594`):** `reference.FIELDS_NOT_COMPARED` names `n_prime_calls` out in both
   phases with DR10's reason, the same mechanism as G1's `FIELDS_ADDED_BY_A_DRIVER_CHANGE`. Re-pressed at
   `b1bb1594`: **236/236 cells, 20 of 20 runs reproduced whole**, 34 cells excluded by name
   (`exit_audit.residual_max_hex` in the optimisation phase, `n_prime_calls` in both).
2. **The tally's `reference_runs` population refuses 14 of GR's seeded records as incomplete**
   (`schedule_resolution` missing, one line per record and per tally: the 28 remaining mismatches). Those
   are the seeded `d6c246a1` records GR reads and never re-makes; the tally reads the same pool records
   as a gate population. Not touched here: a consequence of GR being read-only, gone the day a campaign
   exists (the tally then reads campaign records) — reported for the orchestrator.
3. **One tooth does not trip on this population**: *"the fixed-point distance's restriction"* — on
   `large_tokamak_nof`'s `A2/A0` pair at seed 1 the restricted worst is 1.763e-01 (argmax `power.qac`),
   so moving a kept component by 1e-3 of its scale cannot change the worst. The tooth is built for a
   population where the worst is small; it is a tooth-design limit over the gate population, reported.

So `tally_contracts` stays FAIL after (1) — for (2) and (3), neither of which touches what this task
changes. After DR11, (2) grows to all 20 GR records (DR11's own `campaign_test_set` and `loop_test_sets`
are missing from every record made before it, as A99's `schedule_resolution` is from the 14 seeded ones):
40 population lines, §8.2.

---

## 3. What was built — the switch, τ, the identity, the supplementary hook

**The switch** (`module_solve.py`, §4). `PROCESS_ARCH_TEST_SET` ∈ {`census`, `write_set`} says which
components each block loop **tests**; the driver refuses it unset while the loop is on and refuses it
set while the loop is off (the two guards are the write sets' guards, in both directions). `write_set`
binds the block's whole write set — the same `subsets` object `load_subsets` returned, so **nothing on
that path differs from the copy before DR11** (GC's straddle is the proof, §7). `census` binds the
committed census artifact named by `PROCESS_ARCH_TEST_SETS` (required with `census`, refused with
`write_set`), loaded by a new `load_test_sets` with the write sets' two checks — the coupling-state
digest bound, every key resolving — and **selected by loop**, `<mda>/<burn-time owner>` as the driver
resolved them, because the driver never knows an arm's name. A block the artifact does not list gets an
**empty** set and converges at its first pass (the predicate scores an unwritten component `inf`, so
"everything" would hold a loop open for ever); the stamp names such blocks. `load_loop_tests` returns
the subsets the loop tests and stamps once per run, in `LOOP_TEST_SETS`, what was bound — the set, the
loop key, the artifact's digests, the width per block — which the child records as `loop_test_sets`.
In the caller the change is one line of behaviour: `subset = tests.get(label)` where it read
`subsets.get(label)`; the write sets stay loaded for the block trace.

**τ follows the test set** (`config.py`). `TAU_BY_TEST_SET = {"census": 1e-8, "write_set": 1e-6}`;
`Campaign.tau` is `None` by default and `__post_init__` resolves it from the test set (D23: one value for
every arm and both phases); the runner's `--tau` overrides and `tau_overridden` is stamped. The
campaign default is `census` (D32); `--test-set write_set` selects the fallback. `campaign_test_set` is
a new always-field of the record beside `campaign_tau`; the child takes `--test-set` from the pool's
command line.

**The identity** (`pool.py`, `records.py`). `Job.test_set` and `Job.tau` are identity fields; the pool
resolves them against the campaign at every entry (`resolve_settings`) and **refuses a job whose values
are not the campaign's** — unless a declared supplementary stage admits its phase, configuration and arm
at exactly those values (below). They are **rendered only where they differ from V4's** (the fallback at
1e-6; `records.IDENTITY_DEFAULTS_WHEN_ABSENT`): a fallback job carries V4's identity and V4's digest,
which is what makes every record made before DR11 a record of the fallback and the seeded reproduction
records exactly what GR reads; a census job, or any job at another tolerance, has a digest no earlier
record has. `why_not_complete_for` compares the child's `campaign_test_set` / `campaign_tau` stamps
against the identity's value *or the default*, so a `d6c246a1` record at `campaign_tau = 1e-6` is the
same job as a fallback job that renders no `tau`. Census and fallback records therefore coexist in one
pool without one resolving into the other (the smoke pairs, §8, are the demonstration). The readable
key prints `set=census` / `tau=…` where they are rendered.

**The supplementary hook** (the coordinator's addition, from A96 (st-trajectory-ladder)'s merge).
`config.SupplementaryStage` declares a stage reported *beside* the campaign under its own test set and
τ; `SUPPLEMENTARY_STAGES` holds one, `st_census_exact`: `B0` and `B2` on `st_regression`, `census`,
1e-12, run kind `supplementary` (a new `records.RUN_KINDS` value, never pooled with the campaign).
`chain.supplementary_jobs` composes its job set under `runs/supplementary/<name>/` with the stage's
values on every job — admitted by the pool because the stage is declared, τ in the identity so the
records never resolve into the campaign's 1e-8 records of the same arm and seed, `campaign_tau = 1e-12`
stamped by the child — and `experiment_runner.py --supplementary st_census_exact` runs it (`--arm`,
`--seed`, `--configuration` narrow it; `--run-kind smoke` makes a smoke record). The census artifacts
are the same whatever τ is. The campaign task presses the whole stage; this task pressed one smoke
record from it (§8).

**The `mixed` ruler removed** (D30; V5 plan §12 Q5; the user: dead code is removed). In the driver,
`PREDICATE_MODES = ("frozen",)`, `PREDICATE_MODE = "frozen"` (a constant, no environment read),
`PROCESS_ARCH_PREDICATE` in `RETIRED_SWITCHES` with the reason; the harness's coupling-state module
`ystate.py` (the predicate the driver loads by path) has `RULERS = ("frozen",)`, no `RULER_MIXED` and no
mixed branch in the residual — the `ruler` argument, its refusal and the per-component reporting stay,
so every record keeps its shape (`harness/data/PROVENANCE.json` re-recorded: 22 hunks against the
source, the edit named in `MODULE_EDITS`). `switches.RETIRED_PENDING_IN_DRIVER` is **empty** in the
same commit (the `capability` self-check PASSes: 12 retired names identical in the registry and the
driver, 0 pending). The record contract: `records.AUDIT_RULERS = ("frozen",)`, `exit_audit.mixed`
gone from the schema, `assert_both_rulers` renamed `assert_audit_ruler` (every declared ruler or none),
G7's tooth becomes "an exit audit naming no ruler"; the ruler observer of V4's G8 (`install_ruler_observer`,
`HARNESS_RULER_OBSERVER`) is removed from `child.py` and `evaluate.py`; the tally's full-distributions
table loses its two `mixed` columns. **`pool.Job.predicate_mode` stays** (autonomous, §11): it is in
every job's identity as `"frozen"` and removing it would change every digest — GC's DR10 side would be
unreadable and every seeded record orphaned — for a field that now names the one ruler.

**A99's proposals applied**: `DIAGNOSTIC_READBACKS` gains `(CALLER, "SCHEDULE_RESOLUTION")` (and
`(MODULE_SOLVE, "LOOP_TEST_SETS")` for the new stamp); `gate_resume_identity.by_design_pairs` gains GC's
pair (a labelled side against the unlabelled job of the same arm, must differ; `resume_identity`
PASS, 12 pairs); the `RETIRED_PENDING_IN_DRIVER` note said "DR11 (task A99)" — corrected to A100 in
`b1bb1594`, then the table emptied in `5980c5dc`. `switches.base_environment` sets `NUMBA_NUM_THREADS=1`
and `OMP_NUM_THREADS=1` as defaults beside `NUMBA_CACHE_DIR` (D38), from `b1bb1594` on: G1's `before`
capture and every run of this task ran single-threaded.

**The census stage, GT and the smoke stage** are §5, §6 and §8; the README's new §17 is their manual.

---

## 4. The driver change, in full — every file under `PROCESS/` (for the user's review)

`git diff 66bfa240 5980c5dc -- arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/`; three
files, nothing under `process/models/` (`g0prime` PASS, 77 files, the one approved `pulse.py`).
`PROCESS_diff.py` claims every hunk of the three under the mechanisms `DR11 (A100): switches
PROCESS_ARCH_TEST_SET / PROCESS_ARCH_TEST_SETS …` and `DR11 (A100): the 'mixed' ruler removed …`; its
exit status is still 1 for A90's four `evaluators.py` hunks (issue I-34, pre-existing).
`copy_gates.py` records the four edits (`PERMITTED_EDIT_FILES`: `__init__.py` +1, `module_solve.py` +2,
`caller.py` +1; `PROVENANCE.json` regenerated with `--task "A100 (v5-test-set)"`), and `CHANGES.md`
documents them (§4.1.3, §4.2.9, §4.2.10, §4.5.16).

```diff
diff --git a/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/caller.py b/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/caller.py
index 0b741678..7fa8978e 100644
--- a/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/caller.py
+++ b/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/caller.py
@@ -1396,11 +1396,14 @@ class Caller:
         # whole sequence runs.  ``None`` is the default and the only value the
         # flat-loop path ever sees.
         self._active_nodes: frozenset[str] | None = None
-        # VP4: the coupling-state spec, the per-module subsets its inner
-        # solves test, and their provenance.  Loaded once.
+        # VP4: the coupling-state spec, the per-module write sets, and the
+        # subsets its inner solves test (DR11: the write sets themselves
+        # under PROCESS_ARCH_TEST_SET=write_set, the census test sets under
+        # =census), with their provenance.  Loaded once.
         self._yspec = None
         self._yprov = None
         self._ysubsets: dict | None = None
+        self._ytests: dict | None = None
         #: VP4 diagnostics for the last ``call_models`` -- block sweeps,
         #: schedule passes and per-block sweep counts.  Reported, never gated
         #: on.
@@ -1585,8 +1588,20 @@ class Caller:
         if self._yspec is None:
             self._yspec, self._yprov = module_solve.load_spec()
             self._ysubsets, _ = module_solve.load_subsets(self._yspec)
+            # DR11 (A100 (v5-test-set)): what each block loop TESTS.  The
+            # write sets above stay loaded for the block trace and the
+            # harness's audit; the loop's stopping subset is the test set the
+            # run asked for -- the write sets themselves (V4's predicate, the
+            # fallback of D39) or the census set (D32), selected by the loop
+            # this driver runs: its arrangement and who owns the burn time.
+            self._ytests, _ = module_solve.load_loop_tests(
+                self._yspec,
+                self._ysubsets,
+                loop_key=f"{module_solve.MDA_MODE}/{subsolve.BURN_TIME_OWNER}",
+            )
         spec = self._yspec
         subsets = self._ysubsets
+        tests = self._ytests
         # One tolerance, for every block loop of every arm (D23).  The switch
         # that used to set a second, "inner" one is retired: comparisons are
         # made at matched *achieved* accuracy, which the exit audit records per
@@ -1674,14 +1689,15 @@ class Caller:
                 inner_counts[label].append(1)
                 close_visit(label, visit_nodes, visit_sweeps)
                 continue
-            # A block loop's test is restricted to that block's own write set,
-            # as the evaluation phase's block arm restricts it.  Not an
-            # optimisation: the coupling-state predicate scores any component
-            # that is not float-viewable in *either* snapshot as ``inf``, and
-            # in a fresh process that is every field no model has written yet
-            # -- so an unrestricted test is held open for ever by a field the
-            # running block cannot touch.
-            subset = subsets.get(label)
+            # A block loop's test is restricted to that block's own test set
+            # (DR11): its whole write set under the fallback, as the
+            # evaluation phase's block arm restricts it, or its census set.
+            # Not an optimisation: the coupling-state predicate scores any
+            # component that is not float-viewable in *either* snapshot as
+            # ``inf``, and in a fresh process that is every field no model
+            # has written yet -- so an unrestricted test is held open for
+            # ever by a field the running block cannot touch.
+            subset = tests.get(label)
             # DR4 (A58): how wide this block's convergence test is.  The
             # predicate walks exactly the indices the subset names, and the
             # whole component list when there is no subset -- which is the flat
diff --git a/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/solver/__init__.py b/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/solver/__init__.py
index 815dd1f7..0cfc53a5 100644
--- a/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/solver/__init__.py
+++ b/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/solver/__init__.py
@@ -81,13 +81,21 @@ RETIRED_SWITCHES: dict[str, str] = {
     ),
     "PROCESS_ARCH_YSTATE": "PROCESS_ARCH_COUPLING_STATE",
     "PROCESS_ARCH_WRITESET": "PROCESS_ARCH_WRITE_SETS",
+    # DR11 (A100 (v5-test-set)): removed -- the frozen ruler is the only
+    # ruler (decision D30; V5 plan §12 Q5).  The 'mixed' ruler of driver
+    # change DR5 is gone from the coupling-state module, so a run naming it
+    # would be asking for a denominator this driver no longer has.
+    "PROCESS_ARCH_PREDICATE": (
+        "nothing: the frozen ruler (max|dy_i| / s_i, the measured scale "
+        "alone) is the only ruler; the 'mixed' ruler is removed (D30, DR11)"
+    ),
 }
 
 
 def assert_no_retired_switches(environ=None) -> None:
     """Raise if a retired switch name is set, naming what replaced it.
 
-    Idempotent and cheap: eleven dictionary lookups, and nothing is allocated
+    Idempotent and cheap: twelve dictionary lookups, and nothing is allocated
     on the path that finds nothing.  Called at the import of this package, so
     it binds every entry point into the driver.
     """
diff --git a/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/solver/module_solve.py b/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/solver/module_solve.py
index eaa53500..893fc1ab 100644
--- a/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/solver/module_solve.py
+++ b/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/solver/module_solve.py
@@ -95,16 +95,48 @@ Selection
     *achieved* accuracy, which the exit audit records per run, rather than at
     matched settings.
 ``PROCESS_ARCH_PREDICATE``
-    ``frozen`` or ``mixed``; unset is ``frozen``.  Which denominator the
-    coupling-state predicate scales a step by -- the measured scale alone, or
-    the measured scale kept as a floor under the current magnitude
-    (``max|dy_i| / max(|y_i|, s_i)``).  The two are bit-identical wherever the
-    current magnitude is at or below the scale, and ``mixed`` is never tighter,
-    so no count can go up.  The choice is passed to every predicate evaluation
-    this arrangement makes -- the flat loop's single block and each block loop
-    alike -- and read back as :data:`PREDICATE_MODE`; the test itself lives in
-    the harness's coupling-state module and is not reimplemented here.  Driver
-    change DR5, improvement item 5a's pre-declared trial.
+    **Retired** (driver change DR11, task A100 (v5-test-set); decision D30
+    and the V5 plan's §12 Q5).  There is one ruler, ``frozen`` --
+    ``max|dy_i| / s_i`` with the measured scale alone -- and it is not a
+    setting: :data:`PREDICATE_MODE` names it for the record and the second
+    ruler of driver change DR5 (``mixed``, the scale kept as a floor under
+    the current magnitude) is removed from the coupling-state module.  The
+    name raises at import if set (``process.core.solver.RETIRED_SWITCHES``).
+``PROCESS_ARCH_TEST_SET``
+    ``census`` or ``write_set``; **required** when this arrangement is on
+    and refused when it is off.  Which components of ``y`` each block loop
+    **tests** for convergence (driver change DR11, V5 list item 6):
+
+    * ``write_set`` -- the block's whole write set from the committed write
+      sets, at whatever ``PROCESS_ARCH_TAU`` says.  This is **exactly V4's
+      predicate**, kept selectable as the fallback (decision D39, the user:
+      "the option to run the convergence on the state with the 10e-6
+      tolerance, like v4 -- as a fallback").  Nothing on this path differs
+      from the copy before DR11.
+    * ``census`` -- the block's **census test set**: the components a sweep
+      of the block reads before it first writes them and writes later in the
+      same sweep, measured at run time over whole optimisations in the arm's
+      own execution order (decision D32; the harness's
+      ``experiment/test_sets.py`` measures and commits them).  The loop stops
+      on those components alone; the write sets are still loaded, because
+      the block trace and the harness's exit audit read them, but the loop's
+      stopping subset is the test set.  A block the census never saw sweep
+      has no set and tests nothing: it converges at its first pass.
+
+    There is no default: a run that relied on one could not be told apart
+    afterwards from a run that asked for the other.  Which set the loop bound,
+    its width per block and the artifact's digests are stamped once per run
+    in :data:`LOOP_TEST_SETS` for the record.
+``PROCESS_ARCH_TEST_SETS``
+    Path to the committed census test-set artifact for the configuration
+    being run (``harness/data/test_sets_<configuration>.json``).  Required
+    when ``PROCESS_ARCH_TEST_SET=census`` and refused otherwise, for the same
+    reason the write sets have no default; cross-checked against the
+    coupling-state artifact's ``components_sha256`` so the two cannot be from
+    different generations of the same configuration.  The artifact is keyed
+    by **loop** -- ``<mda>/<burn-time owner>`` as this driver resolved them --
+    because the driver never knows an arm's name and that pair is what
+    distinguishes the loops the census measured.
 ``PROCESS_ARCH_COUPLING_STATE``
     Path to the committed coupling-state artifact for the configuration being
     run.  **Required** when this arrangement is on: there is no default, because
@@ -162,19 +194,25 @@ __all__ = [
     "GLOBAL_BLOCK_SWEEP_CAP",
     "INNER_CAP",
     "ITERATED",
+    "LOOP_TEST_SETS",
     "MDA_MODE",
     "MDA_MODES",
     "PASS_TRACE_PATH",
     "PREDICATE_MODE",
     "PREDICATE_MODES",
     "TAU",
+    "TEST_SET",
+    "TEST_SETS",
+    "TEST_SETS_PATH",
     "TRACE_ENABLED",
     "WRITE_SETS_PATH",
     "ModuleSolveFailure",
     "block_order",
     "iterated",
+    "load_loop_tests",
     "load_spec",
     "load_subsets",
+    "load_test_sets",
     "trace_pass",
 ]
 
@@ -218,37 +256,24 @@ FLAT: bool = MDA_MODE == "flat"
 #: rung (decision D15).
 TAU: float = float(os.environ.get("PROCESS_ARCH_TAU", "1e-6"))
 
-#: The two rulers the coupling-state predicate can scale a step by.  The names
-#: are the harness module's own (``ystate.RULERS``); they are repeated here as
-#: a literal rather than imported because this guard runs at *import*, before
-#: any coupling state has been loaded, and a driver that could only refuse a
-#: misspelt setting after it had found a file would refuse it too late.  That
-#: the two lists agree is checked where the predicate is first used, below.
-PREDICATE_MODES = ("frozen", "mixed")
-
-#: Which denominator the coupling-state predicate scales a step by: ``frozen``
-#: -- the measured scale alone, every earlier revision's ruler and the default
-#: here -- or ``mixed``, the conventional scaled step with that scale kept as a
-#: floor under the current magnitude.  Driver change DR5.
-#:
-#: It selects a denominator and nothing else.  The number of components each
-#: evaluation compares is fixed by the block's write set, so
-#: ``COMPONENTS_COMPARED`` is the same under both rulers for the same schedule
-#: -- which is the free consistency check between them: a ``mixed`` run that
-#: never crossed the tolerance differently must reproduce the ``frozen`` run's
-#: counter exactly.
-PREDICATE_MODE: str = (
-    os.environ.get("PROCESS_ARCH_PREDICATE", "").strip() or "frozen"
-)
-
-if PREDICATE_MODE not in PREDICATE_MODES:
-    raise ArchitectureRefusal(
-        f"PROCESS_ARCH_PREDICATE={PREDICATE_MODE!r} is not a recognised "
-        f"convergence ruler; expected one of {PREDICATE_MODES} (or unset for "
-        f"{'frozen'!r}).  Refused rather than defaulted: a run of one "
-        f"predicate recorded under the other's name cannot be told apart "
-        f"afterwards."
-    )
+#: The rulers the coupling-state predicate can scale a step by: **one**.  The
+#: name is the harness module's own (``ystate.RULERS``); it is repeated here
+#: as a literal rather than imported because the check that the two lists
+#: agree runs where the predicate is first used, below, and a driver whose
+#: guard disagreed with the module implementing the ruler would be accepting
+#: a setting the predicate ignores.  DR11 (A100 (v5-test-set)) removed the
+#: second ruler of driver change DR5 (``mixed``: the measured scale kept as a
+#: floor under the current magnitude) under decision D30 and the V5 plan's
+#: §12 Q5, and retired the switch that selected it
+#: (``process.core.solver.RETIRED_SWITCHES``).
+PREDICATE_MODES = ("frozen",)
+
+#: The one denominator the coupling-state predicate scales a step by: the
+#: measured scale alone, ``max|dy_i| / s_i`` -- every revision's ruler.  Not
+#: a setting since DR11: named here so the record can say which ruler its
+#: loops stopped on, and passed to every predicate evaluation this
+#: arrangement makes (the flat loop's single block and each block loop alike).
+PREDICATE_MODE: str = "frozen"
 
 #: The configuration's committed coupling-state artifact.  No default: see the
 #: module docstring.
@@ -277,6 +302,72 @@ if ENABLED and not COUPLING_STATE_PATH:
         f"change what 'converged' means with no symptom."
     )
 
+# --------------------------------------------------------------------------
+# DR11 (A100 (v5-test-set)): which components each block loop tests
+# --------------------------------------------------------------------------
+
+#: The two things a block loop can stop on.  ``write_set`` is V4's predicate
+#: exactly -- the block's whole write set -- kept as the fallback (decision
+#: D39); ``census`` is the measured test set (decision D32).
+TEST_SETS = ("census", "write_set")
+
+#: Which of the two this run's loops test, or ``None`` with the variable
+#: unset -- which is a refusal when the arrangement is on and the only legal
+#: state when it is off.
+TEST_SET: str | None = os.environ.get("PROCESS_ARCH_TEST_SET", "").strip() or None
+
+if TEST_SET is not None and TEST_SET not in TEST_SETS:
+    raise ArchitectureRefusal(
+        f"PROCESS_ARCH_TEST_SET={TEST_SET!r} is not a recognised test set; "
+        f"expected one of {TEST_SETS}.  Refused rather than defaulted: a run "
+        f"that tested one set under the other's name could not be told apart "
+        f"afterwards."
+    )
+
+if ENABLED and TEST_SET is None:
+    raise ArchitectureRefusal(
+        f"PROCESS_ARCH_MDA={MDA_MODE!r} needs PROCESS_ARCH_TEST_SET to say "
+        f"which components each block loop tests: 'census' (the measured "
+        f"test set, decision D32) or 'write_set' (the block's whole write "
+        f"set, V4's predicate, the fallback of decision D39).  There is no "
+        f"default, so that no run relies on one."
+    )
+
+if TEST_SET is not None and not ENABLED:
+    raise ArchitectureRefusal(
+        f"PROCESS_ARCH_TEST_SET={TEST_SET!r} is set with PROCESS_ARCH_MDA "
+        f"unset, so the run uses upstream's own loop and has no block loop "
+        f"to hand a test set to.  A setting that changes nothing under the "
+        f"right name is refused."
+    )
+
+#: The configuration's committed census test-set artifact.  Required with
+#: ``census``, refused with ``write_set``; no default, as the write sets.
+TEST_SETS_PATH: str | None = os.environ.get("PROCESS_ARCH_TEST_SETS") or None
+
+if TEST_SET == "census" and not TEST_SETS_PATH:
+    raise ArchitectureRefusal(
+        "PROCESS_ARCH_TEST_SET='census' needs PROCESS_ARCH_TEST_SETS to name "
+        "the committed census test-set artifact for the configuration being "
+        "run.  There is no default: another configuration's sets would "
+        "silently test the wrong components."
+    )
+
+if TEST_SETS_PATH and TEST_SET != "census":
+    raise ArchitectureRefusal(
+        f"PROCESS_ARCH_TEST_SETS is set with PROCESS_ARCH_TEST_SET="
+        f"{TEST_SET!r}: a census artifact named for a loop that tests the "
+        f"write set (or for no loop at all) would be a setting that changes "
+        f"nothing under the right name.  Refused."
+    )
+
+#: What the loops bound, stamped once per run when the sets are first loaded
+#: (``load_loop_tests``): the test set, its source artifact and digests, the
+#: loop key the artifact was selected by, and the width per block.  Read by
+#: the harness into the run record as ``loop_test_sets``; null there with
+#: the arrangement off, when this is never filled.
+LOOP_TEST_SETS: dict = {"test_set": TEST_SET, "loaded": False}
+
 # --------------------------------------------------------------------------
 # A31 (drift-diagnostic): the per-pass joint-test trace.  Observation only.
 # --------------------------------------------------------------------------
@@ -637,11 +728,11 @@ def _ystate_module():
     )
     mod = importlib.util.module_from_spec(spec)
     spec.loader.exec_module(mod)
-    # DR5.  The ruler names are guarded at import from a literal (the refusal
-    # has to happen before any file is read), so the literal is checked against
-    # the module that actually implements them the first time that module is
-    # loaded.  A driver that accepted a setting the predicate does not know
-    # would refuse nothing and run the default under the other's name.
+    # DR5, kept under DR11 with one ruler: the ruler list is a literal here
+    # (there is nothing to read a file for before the predicate is loaded), so
+    # the literal is checked against the module that actually implements it
+    # the first time that module is loaded.  A driver whose list disagreed
+    # with the predicate's would be naming a ruler the predicate ignores.
     rulers = getattr(mod, "RULERS", None)
     if rulers is None or tuple(rulers) != tuple(PREDICATE_MODES):
         raise ArchitectureRefusal(
@@ -715,8 +806,9 @@ def load_spec(path: str | Path | None = None):
         # DR5.  The tolerance and the ruler together are what "converged"
         # means; a block that carried one and not the other would leave a
         # record naming half of its own stopping rule (improvement item 5a's
-        # trap (i)).
+        # trap (i)).  DR11 adds the third part: which set the loops test.
         "predicate_mode": PREDICATE_MODE,
+        "test_set": TEST_SET,
     }
     _SPEC_CACHE[str(p)] = (spec, provenance)
     return spec, provenance
@@ -791,3 +883,132 @@ def load_subsets(spec, path: str | Path | None = None):
     }
     _SUBSET_CACHE[str(p)] = (subsets, provenance)
     return subsets, provenance
+
+
+_TEST_SET_CACHE: dict = {}
+
+
+def load_test_sets(spec, path: str | Path | None = None, *, loop_key: str):
+    """``{block: frozenset(y indices)}`` from the committed census test sets.
+
+    DR11 (A100 (v5-test-set)).  The artifact holds one entry per **loop** --
+    keyed ``<mda>/<burn-time owner>`` -- and each entry one key list per
+    block.  The same two things are checked as for the write sets, and for
+    the same reason (a set that silently misses components is a convergence
+    test that silently passes early):
+
+    * the artifact's ``ystate_components_sha256`` must equal the spec's own
+      ``components_sha256`` -- one configuration, one generation;
+    * every key named in a block's set must resolve to a component of the
+      spec.
+
+    Coverage is **not** required, and that is the point: a test set is a
+    subset of the block's write set, and a block the census never saw sweep
+    has no list at all and tests nothing (V5 plan §3).  The entry for
+    *loop_key* must exist; a loop the artifact does not know is refused, not
+    given another loop's sets.
+    """
+    p = Path(path or TEST_SETS_PATH)
+    cache_key = (str(p), loop_key)
+    cached = _TEST_SET_CACHE.get(cache_key)
+    if cached is not None:
+        return cached
+    record = json.loads(p.read_text())
+
+    spec_sha = spec.components_sha256()
+    art_sha = record.get("ystate_components_sha256")
+    if art_sha != spec_sha:
+        raise ArchitectureRefusal(
+            f"census test sets {p} were built against ystate components "
+            f"{art_sha} but the loaded spec is {spec_sha}: the two artifacts "
+            f"are not from the same configuration and generation."
+        )
+    entry = (record.get("sets") or {}).get(loop_key)
+    if entry is None:
+        raise ArchitectureRefusal(
+            f"census test sets {p} carry no entry for loop {loop_key!r}; the "
+            f"loops it knows are {sorted(record.get('sets') or {})}.  Another "
+            f"loop's sets would silently test the wrong components, so the "
+            f"run is refused."
+        )
+
+    index = {f"{ns}.{fld}": i for i, (ns, fld) in enumerate(spec.keys)}
+    tests: dict[str, frozenset] = {}
+    unknown: list[str] = []
+    for block, keys in entry["blocks"].items():
+        idx = set()
+        for k in keys:
+            i = index.get(k)
+            if i is None:
+                unknown.append(k)
+            else:
+                idx.add(i)
+        tests[block] = frozenset(idx)
+    if unknown:
+        raise ArchitectureRefusal(
+            f"census test sets {p} name {len(unknown)} keys the coupling-state "
+            f"spec does not have, e.g. {sorted(unknown)[:5]}"
+        )
+
+    provenance = {
+        "path": str(p),
+        "scenario": record.get("scenario"),
+        "format": record.get("format"),
+        "loop_key": loop_key,
+        "census_arm": entry.get("census_arm"),
+        "sets_sha256": record.get("sets_sha256"),
+        "ystate_components_sha256": art_sha,
+        "n_by_block": {b: len(v) for b, v in sorted(tests.items())},
+        "n_components": len(spec.keys),
+    }
+    _TEST_SET_CACHE[cache_key] = (tests, provenance)
+    return tests, provenance
+
+
+def load_loop_tests(spec, write_sets: dict, *, loop_key: str):
+    """The subsets each block loop **tests**, under the test set the run asked for.
+
+    DR11.  Under ``write_set`` this is *write_sets* itself -- V4's predicate,
+    the block's whole write set, the fallback of decision D39 -- and nothing
+    is read.  Under ``census`` it is :func:`load_test_sets` for *loop_key*,
+    with every block of the schedule that the artifact does not list given
+    an **empty** set, so that such a block tests nothing rather than
+    everything (the predicate scores an unwritten component ``inf``, so
+    "everything" would hold a loop open for ever; see ``load_subsets``).
+
+    Either way the choice is stamped once, in :data:`LOOP_TEST_SETS`, so the
+    record says what the loops bound.
+    """
+    if TEST_SET == "write_set":
+        tests = write_sets
+        provenance = {
+            "test_set": TEST_SET,
+            "loop_key": loop_key,
+            "source": "the committed write sets (V4's predicate, decision D39)",
+            "path": WRITE_SETS_PATH,
+            "n_by_block": {b: len(v) for b, v in sorted(write_sets.items())},
+        }
+    elif TEST_SET == "census":
+        loaded, loaded_prov = load_test_sets(spec, loop_key=loop_key)
+        tests = dict(loaded)
+        for block in write_sets:
+            tests.setdefault(block, frozenset())
+        provenance = {
+            "test_set": TEST_SET,
+            **loaded_prov,
+            "n_by_block": {b: len(v) for b, v in sorted(tests.items())},
+            "blocks_never_censused": sorted(
+                b for b in write_sets if b not in loaded
+            ),
+        }
+    else:  # pragma: no cover - the import-time guard refuses this
+        raise ArchitectureRefusal(
+            f"PROCESS_ARCH_TEST_SET={TEST_SET!r}: no test set to bind"
+        )
+    if not LOOP_TEST_SETS.get("loaded"):
+        LOOP_TEST_SETS.clear()
+        LOOP_TEST_SETS.update(provenance)
+        LOOP_TEST_SETS["tau"] = TAU
+        LOOP_TEST_SETS["predicate_mode"] = PREDICATE_MODE
+        LOOP_TEST_SETS["loaded"] = True
+    return tests, provenance
```

---

## 5. The census stage — the population of the test sets

`experiment_runner.py --census take` at `60434c52` (log `A100_press4_census_take.log`; stage record
`runs/artifacts/census_test_sets.json`, the derivation `runs/census_test_sets/stage.json`), then
`--census write --resume` (`A100_press7_census_write.log`: 32 of 32 records resumed, 0 re-made, the
three artifacts byte-identical to the `take` press's) — committed as `3d56c4ad`, entered in
`harness/data/PROVENANCE.json` at that commit (`c533701c`; `data` gate PASS, 21 files + the predicate
module). **PASS: 96 reproduction fields compared, 0 mismatched.**

**The job set.** Seeds 0 and 1 × every iterating optimisation arm active on each configuration —
`B0`, `B1` (pulsed only), `B2` — = 16 censused optimisations and their 16 uncensused twins, 32
optimisations at W = 3 under the fallback (write set at 1e-6) by construction. Every record stamped
`60434c52`; the census file `read_before_write_census.json` beside each censused record (86 898–88 284
snapshots on nof's flat runs, one before and one after every node call).

**Table 5.1 — the instrument is observation-only.** *One row per censused optimisation; the twin's
value of each field and whether the censused run reproduced it. Population: 16 of 16 pairs; the six
fields `status`, `mfile.ifail`, `n_solver_iterations`, `sweeps_per_eval.n_evaluations`,
`node_calls_solve_phase`, `exact.norm_objf`. Every row identical on all six.*

| configuration | arm | seed | iterations | evaluations | node calls (solve) | `norm_objf` (hex) | identical |
|---|---|---|---|---|---|---|---|
| large_tokamak_nof | B0 | 0 | 8 | 630 | 43 449 | `0x1.99999999b822ap+0` | yes |
| large_tokamak_nof | B0 | 1 | 8 | 630 | 43 491 | `0x1.99999999c8db5p+0` | yes |
| large_tokamak_nof | B1 | 0 | 8 | 660 | 44 142 | `0x1.9999999a4496cp+0` | yes |
| large_tokamak_nof | B1 | 1 | 8 | 660 | 44 100 | `0x1.99999999bb397p+0` | yes |
| large_tokamak_nof | B2 | 0 | 8 | 660 | 28 055 | `0x1.9999999a4496cp+0` | yes |
| large_tokamak_nof | B2 | 1 | 8 | 660 | 28 037 | `0x1.99999999bb397p+0` | yes |
| low_aspect_ratio_DEMO | B0 | 0 | 16 | 1 240 | 86 877 | `-0x1.a00c1e754455cp-2` | yes |
| low_aspect_ratio_DEMO | B0 | 1 | 16 | 9 240 | 655 473 | `-0x1.9f9030eb8b43dp-2` | yes |
| low_aspect_ratio_DEMO | B1 | 0 | 13 | 1 050 | 69 930 | `-0x1.a00c0bc88c2c6p-2` | yes |
| low_aspect_ratio_DEMO | B1 | 1 | 15 | 1 218 | 81 228 | `-0x1.9fb1afe0ebcf7p-2` | yes |
| low_aspect_ratio_DEMO | B2 | 0 | 13 | 1 050 | 45 496 | `-0x1.a00c0bc88c2c6p-2` | yes |
| low_aspect_ratio_DEMO | B2 | 1 | 15 | 1 218 | 52 834 | `-0x1.9fb1afe0ebcf7p-2` | yes |
| st_regression | B0 | 0 | 10 | 570 | 42 756 | `-0x1.096acf3342e3cp+4` | yes |
| st_regression | B0 | 1 | 53 | 3 150 | 226 002 | `-0x1.0cf146aad761fp+4` | yes |
| st_regression | B2 | 0 | 10 | 570 | 23 505 | `-0x1.096acf3342e55p+4` | yes |
| st_regression | B2 | 1 | 59 | 3 510 | 134 560 | `-0x1.0cf146c754521p+4` | yes |

The `B0` and `B2` rows are, to the bit, A92's Table 1 (made on V4's copy at `7986d408`, before DR9 and
DR10): the same iterations, evaluations, solve-phase node calls and `norm_objf` on all twelve — a
count-neutrality reading of DR9 + DR10 on twelve whole optimisations beyond GC's job set, free.

**Table 5.2 — the population, per configuration and loop.** *Widths per block of the binding set
(the census union over the two seeds, unioned with A92's optimisation-path set of the twin arm where
one exists — the union added nothing anywhere: `added_from_prior_optimisation_path` is empty on every
loop); the delta against A92's path sets (`test_set_prior_optimisation_path.json`) and A89's eight-entry
sets (`test_set_prior_eight_entry.json`); the artifact's `sets_sha256`. Population: 16 censused runs;
the loop keys are what the driver selects by; `B1` has no prior (measured here first).*

| configuration | loop key (arms) | census arm | widths per block | against A92's path set | against A89's eight-entry set | `sets_sha256` |
|---|---|---|---|---|---|---|
| large_tokamak_nof | `flat/loop` (A0, B0) | B0 | FLAT 79 | identical | FLAT 79 vs 75: +4 (the cold-start components), −0 | `61be31eb9770…` |
| large_tokamak_nof | `flat/optimiser` (B1) | B1 | FLAT 78 | no prior | no prior; = B0's set minus `times.t_plant_pulse_burn` | `61be31eb9770…` |
| large_tokamak_nof | `partitioned/optimiser` (B2; A2 = `partitioned/constant`, see below) | B2 | M1 17, M2 50, **M3 12** | **M3: +2** (`build.dr_fw_inboard`, `build.dr_fw_outboard`), M1 and M2 identical | M1 17 vs 16 (+1), M2 50 vs 47 (+3), M3 12 vs 10 (+2) | `61be31eb9770…` |
| low_aspect_ratio_DEMO | `flat/loop` (A0, B0) | B0 | FLAT 78 | identical | 78 vs 74: +4, −0 | `4a9a7fe422d4…` |
| low_aspect_ratio_DEMO | `flat/optimiser` (B1) | B1 | FLAT 77 | no prior | no prior; = B0's minus the burn time | `4a9a7fe422d4…` |
| low_aspect_ratio_DEMO | `partitioned/optimiser` (B2) | B2 | M1 17, M2 49, **M3 12** | **M3: +2** (the same two), M1 and M2 identical | M1 17 vs 16, M2 49 vs 46, M3 12 vs 10 | `4a9a7fe422d4…` |
| st_regression | `flat/loop` (A0, B0) | B0 | FLAT 75 | identical | 75 vs 73: +2, −0 | `3b3a1f3d1e65…` |
| st_regression | `partitioned/loop` (A2, B2) | B2 | M1 17, M2 48, **M3 12**, PULSE 1 | **M3: +2** (the same two); PULSE: +1 (`impurity_radiation.f_nd_impurity_electron_array`, which A92's JSON listed as a once-run block's; PULSE is not iterated, so its set is never consulted); M1 and M2 identical | M1 17 vs 16, M2 48 vs 47, M3 12 vs 10, PULSE 1 vs 1 | `3b3a1f3d1e65…` |

**Two results, neither foreseen by the plan's population paragraph.**

1. **`M3` carries two more components than A92 measured, on every configuration:** `build.dr_fw_inboard`
   and `build.dr_fw_outboard` — the first-wall geometry pair that the arrangement-method prime computes —
   reader `fw`, writer `fw`, carried in every M3 sweep of both seeds (3 179 sweeps on nof, 9 200 on st).
   This is **DR10's doing**: on V4's copy the prime wrote the pair at the head of every block sweep, so no
   sweep read them before writing them; since the prime executes once per evaluation (A99), the `fw` node
   reads its own previous value of the pair before it writes it inside M3's sweep, which is the census's
   rule. The pair is a run-constant of two input-file values (D19) — it never moves after the prime — so
   carrying it changes no stop; it is inert the way the four cold-start components are. **The new sets
   stand** (the brief: "if not, the difference is a result and the new sets stand").
2. **`B1`'s set is measured, not assumed:** `B0`'s set minus exactly `times.t_plant_pulse_burn` on both
   pulsed configurations (78 / 77) — the optimiser owns the burn time, no loop node writes it, so it cannot
   be read-before-written. `A1` (`flat/constant`) has no loop entry of its own: it is not an optimisation
   arm and no census ran it; the driver selects `flat/constant`, which the artifact does not carry. **This
   is a gap the plan's arm list did not foresee** — the brief's "A1/B1 (the lifted flat block) measured"
   was met for `B1` and for `A1` only through the arm mapping (the artifact's `flat/constant` entry is `B1`'s set bound for `A1` with `twin_of` stamped, decision 18 of §11; GT then measures that set on `A1` directly, §6, which is the check the mapping gets).

**A block the census never saw sweep**: none in this population — every iterated block of every loop
(FLAT; M1, M2, M3) was swept in both seeds of every configuration; `PULSE` on st is visited but not
iterated (I-20a); no `blocks_never_censused` entry is non-empty in any smoke or gate record.

The sets on the optimiser's path beyond A89's eight entries are the cold-start components A92 named
(`physics.first_call`, `pf_coil.first_call`, `pf_coil.n_pf_coils_in_group`, `build.dz_xpoint_divertor`
on the pulsed configurations, the two `first_call` flags on st) plus the pair above.

---

## 6. Gate GT — the test set's teeth

`harness/gates/gate_test_set.py`, registry name `test_set`, plan name GT; the form V5 plan §3
declares from A92 (§17.2 of the README). Pressed at `bf395541` (its runs: 3 references, 8 full-set
runs — G6's pairing jobs, shared — and 16 drops, 27 evaluations, `A100_press14_GT.log`); the comparison
raised a key error on that press and, after the fix, a tooth did on the next (`572be14d`; verdicts kept
as `test_set/press_at_572be14d_tooth_raised.json`); **the verdict below is the press at `521a753c`
with every run kept** (`A100_press18_GT.log`): **PASS** — 8 binding drops: **3 bite**, 5 not individually binding; **8 of 8 controls bit-identical**; 13 424 exit-state components compared, 735 differing (all in the three biting drops); **4/4 teeth**.

**Table 6.1 — the teeth of the census set, per configuration and block arm.** *Rows: per configuration
and arm (`A0`, `A1` where active, `A2`), from the displaced entry at seed 1 (δ = 0.10) under the census set
at τ = 1e-8: the full-set run, then the binding drop (the carried component with the largest whole-`y`
exit residual under the full set; ties to the alphabetically last key — on `low_aspect_ratio_DEMO` every
carried residual is 0.0 in the flat arms, so the rule chose by tie-break) and the control (the
non-carried component with the largest exit residual). Columns: the blocks the key was removed from;
sweeps per block and node calls of the evaluation (full → dropped); the loop's width per block as the
driver stamped it (full → dropped — the check that the narrowed set was bound); the exit state against
the full run's (components differing of the whole `y`, bit comparison); the whole-`y` and restricted
exit-audit maxima of the dropped run; the verdict by §3's criterion. Population: 8 full runs, 8 binding
drops, 8 controls; 13 424 exit-state components compared.*

| configuration | arm | role | dropped component | from | sweeps full → dropped | node calls | width full → dropped | exit state vs full | audit whole-`y` / restricted | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | A0 | binding | `pf_coil.stress_z_cs_self_midplane_profile` | FLAT | FLAT 7 → **6** | 147 → 126 | 79 → 78 | **270 / 840 differ** | 2.56e-09 / 2.56e-09 (full 4.92e-11) | **bites** |
| large_tokamak_nof | A0 | control | `costs.coecap` | — | 7 → 7 | 147 → 147 | 79 → 79 | 0 / 840 | 4.92e-11 | control PASS |
| large_tokamak_nof | A1 | binding | `pf_coil.stress_z_cs_self_midplane_profile` | FLAT | FLAT 7 → **6** | 147 → 126 | 78 → 77 | **262 / 840 differ** | 2.68e-10 / 2.68e-10 (full 5.16e-12) | **bites** |
| large_tokamak_nof | A1 | control | `superconducting_tfcoil.a_tf_plasma_case` | — | 7 → 7 | 147 → 147 | 78 → 78 | 0 / 840 | 5.16e-12 | control PASS |
| large_tokamak_nof | A2 | binding | `pf_coil.stress_z_cs_self_midplane_profile` | M2 | M1 3, M2 7 → **6**, M3 2 | 52 → 49 | M2 50 → 49 | **203 / 840 differ** | 0.98 (whole, the deferred nodes' outputs) / **2.68e-10** restricted (full 5.16e-12) | **bites** |
| large_tokamak_nof | A2 | control | `costs.coecap` | — | 3, 7, 2 | 52 → 52 | unchanged | 0 / 840 | 0.98 / 5.16e-12 | control PASS |
| low_aspect_ratio_DEMO | A0 | binding | `times.t_plant_pulse_burn` (tie-break, every carried residual 0.0) | FLAT | 5 → 5 | 105 → 105 | 78 → 77 | 0 / 846 | 0.0 / 0.0 | not individually binding |
| low_aspect_ratio_DEMO | A0 | control | `water_use.waterusetower` | — | 5 → 5 | 105 → 105 | 78 → 78 | 0 / 846 | 0.0 | control PASS |
| low_aspect_ratio_DEMO | A1 | binding | `tfcoil.str_wp` (tie-break) | FLAT | 5 → 5 | 105 → 105 | 77 → 76 | 0 / 846 | 0.0 / 0.0 | not individually binding |
| low_aspect_ratio_DEMO | A1 | control | `water_use.waterusetower` | — | 5 → 5 | 105 → 105 | 77 → 77 | 0 / 846 | 0.0 | control PASS |
| low_aspect_ratio_DEMO | A2 | binding | `tfcoil.str_wp` | M2 | 3, 5, 2 → same | 46 → 46 | M2 49 → 48 | 0 / 846 | 0.10 (whole) / 0.0 restricted (full 0.0) | not individually binding |
| low_aspect_ratio_DEMO | A2 | control | `water_use.wateruseonethru` | — | same | 46 → 46 | unchanged | 0 / 846 | 0.10 | control PASS |
| st_regression | A0 | binding | `tfcoil.str_wp` | FLAT | 6 → 6 | 126 → 126 | 75 → 74 | 0 / 827 | 3.01e-09 / 3.01e-09 | not individually binding |
| st_regression | A0 | control | `superconducting_tfcoil.a_tf_plasma_case` | — | 6 → 6 | 126 → 126 | 75 → 75 | 0 / 827 | 3.01e-09 | control PASS |
| st_regression | A2 | binding | `tfcoil.str_wp` | M2 | 3, 6, PULSE 1, 3 → same | 60 → 60 | M2 48 → 47 | 0 / 827 | 0.25 (whole) / 3.01e-09 restricted (full 3.01e-09) | not individually binding |
| st_regression | A2 | control | `water_use.wateruseonethru` | — | same | 60 → 60 | unchanged | 0 / 827 | 0.25 | control PASS |

**Readings.** (i) On `large_tokamak_nof` the declared rule finds the same component A92 found,
`pf_coil.stress_z_cs_self_midplane_profile`, and it **bites in all three arms**: the loop stops one sweep
earlier (flat 7 → 6; `M2` 7 → 6) and the exit state differs on 203–270 of 840 components — the tooth. On
`A1` it bites too, which A92 never ran. (ii) Every control is bit-identical on every count and every
component, 8 of 8: the artifact's path changing changes nothing, and the driver binds exactly the set it
is handed (the width stamps read one fewer in exactly the blocks the key was removed from, 16 of 16). (iii)
The whole-`y` audit stays below τ on the flat arms' biting drops (2.6e-09, 2.7e-10 against 1e-8 — A92's
mechanism: the audit measures the next sweep's contraction, which the full loop just accepted) and the
restricted audit likewise (`A2` on nof: 5.2e-12 → 2.7e-10, 50× as A92 measured, still below τ); on `A2` the *whole*-`y` maximum is 0.98 / 0.10 / 0.25 on every run, full or
dropped, because in the evaluation phase the per-run deferred nodes are not yet executed after
convergence (V5 list item 5, a later task) and their outputs move at the audit's sweep — the restricted
statistic is the one to read there (5.2e-12 on nof). (iv) On `low_aspect_ratio_DEMO` and `st_regression`
no single component binds on this entry, as A92 found: the loops settle to bit-identical sweeps (lad, the
exit residual 0.0 everywhere) or another carried component reaches τ last (st); the rows say so and (ii)
is the check there, as the plan declares. **Under the census set the flat arms' restricted audit on this
entry reads 5.2e-12 (nof `A1`), 0.0 (lad) and 3.0e-09 (st) where the same entries under the fallback read
1.4e-08 on nof (the seeded `A2` record at `66bfa240`)** — context on what 1e-8 buys.

---

## 7. The straddles — G1 and GC across the DR11 commit

Both gates were pressed twice: a first press that **FAILed on harness bookkeeping alone** — recorded
as a result, its verdict kept beside the gate — then the leaves declared by name with their reasons
(the mechanism both gates are built on: A52's conditional exclusions, G1's cross-tree paths) in one
commit, then a re-press that reads the same captures. No driver value and no output-file line differed
on either press.

### 7.1 G1 `switch_neutrality` — `b1bb1594` (the prep commit; the driver = the merged tip's) → `60434c52` (DR11's driver)

The `before` side was captured at `b1bb1594` with the tree checked out there (the DR10 straddle's
captures archived first under `switch_neutrality/straddles/e5137707__a0de2e13/`); the `after` side at
`60434c52`. Every switch unset, `AR` and `BR` on the three configurations, W = 3, every child
single-threaded on both sides.

**First press** (`A100_press5_G1_DR11.log`; verdict kept as
`switch_neutrality/first_press_at_60434c52_FAIL.json`): **FAIL** — 3 669 deterministic record values
compared, **27 differing**, 998 excluded by name; **51 319 output-file lines compared, 0 differing**;
9/9 teeth. The 27 are five names on six runs, every one a stamp the harness writes about itself or the
campaign and none a driver value: `campaign_tau` (1e-6 → 1e-8: the campaign default followed the test
set; the driver's own resolved `TAU` is compared and equal), `harness_version` (0.2.0 → 0.3.0),
`exit_audit.rulers_note` (a sentence, reworded when the second ruler went), `job_digest` (the identity
gained the test set and τ, rendered under the census campaign; every identity field both sides carry
agrees) and, on the three `AR` runs, `coupling_state_provenance.test_set` (absent before, null after).
**Declared** (`gate_neutrality.py`, commit `3d56c4ad`): the first three in `ALWAYS_EXCLUDED` with
their reasons (the campaign's declared settings are compared through `resolved_switches`; a version
and a sentence are not behaviours), `coupling_state_provenance.test_set` in
`FIELDS_ADDED_BY_A_DRIVER_CHANGE`, and `job_digest` witnessed by `job_identity.test_set` in
`CONDITIONAL_WITNESS` — excluded exactly where the two identities were computed over different field
sets, compared where both or neither side renders the field (the witness logic gained the
"absent on both sides → the leaf decides" case).

**Re-press** (`--gate switch_neutrality --resume` at `7aa3c0b4`, `A100_press8_G1_DR11_repress.log`; both
captures kept — the after side at `60434c52`, whose driver is DR11's byte for byte): **PASS** — straddles
`b1bb1594 → 60434c52`, 6 pairs, **3 642 deterministic record values compared, 0 differing**, 1 025
excluded by name with their reasons; **51 319 output-file lines compared, 0 differing**; 9/9 teeth.
With every switch unset the driver is byte-identical across DR11: the test-set code is never reached.

### 7.2 GC `count_neutrality` — `DR10` (`a0de2e13`, A99's after side) → `DR11` (`60434c52`), under the fallback

`--gate count_neutrality --test-set write_set --resume`: the DR11 side made under `write_set` **by
declaration** (`STRADDLE_TEST_SET`; a press under `census` is refused), 22 labelled jobs at V4's job
identity plus the label, the prime count under the rule `identical`. The three entry references were
re-made under the new record contract (`campaign_test_set`).

**First press** (`A100_press6_GC_DR10_DR11.log`; kept as `count_neutrality/first_press_at_60434c52_FAIL.json`
and `straddles/DR10__DR11_first_press_at_60434c52_FAIL.json`): **FAIL** — 22 pairs; 3 963 count leaves
under 41 declared paths, **6 differing**; 33 prime-count checks under `identical`, 0 failing; **46 125
coupling-state components over every state file, 0 differing**; teeth 2/3. The six differing leaves are
one name on the six deferring pairs (`A2`, `B2` × 3): `defer_per_run_totals.artifact`, an **absolute
path** — A99's worktree on the before side, this worktree on the after — the first GC straddle whose two
sides were made in two working trees (A99's three presses were one tree, where the path agrees by
location; the class G1 declares as its cross-tree paths). The tooth that did not trip is the same
finding: it expects its doctored count to be the one differing leaf and found two. **Declared**
(`gate_count_neutrality.PATH_LEAVES_NOT_COMPARED`, commit `3d56c4ad`): the path leaf named out with
its reason; the artifact's content stays compared through `defer_per_run_totals.nodes_sha256` and the
node lists beside it.

**Re-press** (`--gate count_neutrality --resume` at `7aa3c0b4`, `A100_press9_GC_DR10_DR11_repress.log`;
22 of 22 after-side records and the 3 references kept, 0 re-made): **PASS** — "straddles 'DR10' at
`a0de2e13` → 'DR11' at `60434c52`: a count-neutrality result": 22 pairs (11 evaluations from the
displaced entry at seed 1, δ = 0.10; 11 optimisations from seed 0); **3 957 count leaves under 41 declared
paths, 0 differing**; 33 prime-count checks under `identical`, 0 failing; **46 125 coupling-state
components compared bit for bit over every state file the runs wrote, 0 differing**; 3/3 teeth. The
after side stamps `campaign_test_set = write_set`, `campaign_tau = 1e-6` and `loop_test_sets.test_set =
write_set` with V4's widths per block. **This is the proof of D39: the fallback is V4's predicate exactly,
to the count and to the bit, on every arm of both phases.** Record: `count_neutrality/straddles/DR10__DR11.json`.

---

## 8. The smoke pairs, the supplementary record, and the gate table after

### 8.1 The smoke pairs — `--smoke-test-set --ladder-record <A96's record>`

`harness/measurement/test_set_smoke.py` at `65e7a24a` (`A100_press26_smoke_test_set.log`; stage record
`runs/artifacts/smoke_test_set.json`): **PASS** — every run finished, the fallback pair reproduces the
seeded reproduction records, the supplementary record reproduces A96's. Five smoke records (run kind
`smoke`, named directories under `runs/single/test_set_smoke/`), each through the pool and composed by
the campaign — the census pair by the census campaign, the fallback pair by the fallback campaign the
stage builds, the supplementary record by the declared stage `st_census_exact`. (A first press at
`271168be` chose `low_aspect_ratio_DEMO` by fewest iteration variables; its two pairs, kept as smoke
records, reproduce the seeded GR records to the bit as well — `A100_press21_smoke_test_set.log` — and
read `B2/B0` 0.489 under the census set and 0.618 under the fallback. The supplementary record was made
in that first press and resumed in the second: its `tree_git_head` is `271168be`, §9.)

**Table 8.1 — the five smoke records and what they carry.** *One row per record: the test set and τ
the harness stamped, the loop key and the width per block the driver stamped (`loop_test_sets`), the
optimiser's iterations and evaluations, the solve-phase node calls, `norm_objf` in hex, and what the
record was compared with. Population: `B0` and `B2` on `large_tokamak_nof` at seed 0 under each test
set; the supplementary stage's `B2` on `st_regression` at seed 0. The fallback comparison is on the six
fields status, `mfile.ifail`, iterations, evaluations, solve-phase node calls, `norm_objf`; the ladder
comparison on the last four.*

| record | `campaign_test_set` / `campaign_tau` | loop key | widths stamped | iterations | evaluations | node calls (solve) | `norm_objf` | compared with |
|---|---|---|---|---|---|---|---|---|
| `census/B0` | census / 1e-8 | `flat/loop` | FLAT 79 | 8 | 630 | 45 465 | `0x1.99999999b822cp+0` | — |
| `census/B2` | census / 1e-8 | `partitioned/optimiser` | M1 17, M2 50, M3 12 | 8 | 660 | 22 944 | `0x1.9999999a4496cp+0` | — |
| `write_set/B0` | write_set / 1e-6 | `flat/loop` | FF 119, M1 258, M2 240, M3 221, PULSE 2 (= 840) | 8 | 630 | 43 449 | `0x1.99999999b822ap+0` | GR's seeded `B_B0_large_tokamak_nof_seed000_gate_0b71f621…` at `d6c246a1`: **IDENTICAL on all six** |
| `write_set/B2` | write_set / 1e-6 | `partitioned/optimiser` | the same 840 | 8 | 660 | 28 055 | `0x1.9999999a4496cp+0` | GR's seeded `B_B2_large_tokamak_nof_seed000_gate_268a4f78…` at `d6c246a1`: **IDENTICAL on all six** |
| `supplementary/st_census_exact/B2` | census / **1e-12** | `partitioned/loop` | M1 17, M2 48, M3 12, PULSE 1 | 10 | 570 | 22 092 | `-0x1.096acf3342df8p+4` | A96's `B2_rbw_1e-12/seed000` at `6a51108b` (V4's copy, before DR9/DR10): **IDENTICAL on evaluations, iterations, node calls, `norm_objf`** |

**Readings.** (a) **The fallback is V4 on this tree, to the `norm_objf` bit**: both `write_set` records
reproduce A94's seeded reproduction records of the same arm and seed on every compared field, with the
seeded record carrying no `campaign_test_set` (made before DR11) and `campaign_tau = 1e-6`, and the smoke
record carrying `write_set` / 1e-6 and V4's widths — the identity rule of §3 in action: the smoke job
renders neither field and differs from GR's job only in run kind and directory. (b) **The supplementary
hook composes as the coordinator asked**: τ = 1e-12 in the job identity (digest `10c2ea3fe01a…`, no
census record of the same arm and seed shares it), `campaign_tau = 1e-12` stamped, and the record matches
A96's — made on V4's copy at `6a51108b`, before DR9 and DR10 — on 570 evaluations, 10 iterations, 22 092
solve-phase node calls and `norm_objf` to the bit: DR9 + DR10 + DR11 are count-neutral on st at 1e-12 on
this run, and the census set the driver bound (M1 17, M2 48, M3 12 — A92's path sets plus the two
first-wall components) reaches the same optimum by the same path as A89's eight-entry set A96 ran with.
(c) **The census pair beside the fallback pair**: the flat control costs +4.6 % node calls per run under
the census set at 1e-8 (45 465 vs 43 449; A93 measured +4.6 % on nof's `B0`), the partitioned arm −18.2 %
(22 944 vs 28 055; A93: −18.1 %); the same iterations and evaluations on both arms; `norm_objf` two units
in the last place apart on `B0`, identical on `B2`. **The per-evaluation node-call ratio `B2/B0`: 0.482
under the census set, 0.616 under the fallback** — beside A93's 0.48–0.49 and V4's 0.61 (context, never
evidence, D33).

### 8.2 The gate table after DR11, under the census default

`experiment_runner.py --measure gate_table --resume` at **`ba440ecd`** (`A100_press38_gate_table_final.log`;
record `runs/gates/gate_table/measurements.json`), after `--gate all --resume` at `c4aa37b6`
(`A100_press30_gate_all_census.log`) and the four re-presses at `ba440ecd` (`tally_contracts`,
`resume_identity`, `output_path`, `count_neutrality`; logs `A100_press34`–`37`). No PROCESS run was made
after `c4aa37b6` (the stamp survey is unchanged, §9).

**Table 8.2 — the gate table after DR11, under the census default.** *One row per registered gate; the
columns are the table measurement's own (verdict on criterion and teeth, what was compared, how many
differed, teeth tripped of declared). Population: the 29 registered gates. Where a row differs from
Table 2.1 the note says how.*

| gate | plan | verdict | compared | mismatched | teeth | note against Table 2.1 |
|---|---|---|---|---|---|---|
| `g0prime` | G0 | PASS | 77 | 1 (the approved `pulse.py`) | 4/4 | — |
| `copy_identity` | — | PASS | 224 | 8 (the permitted-edit files, as before) | 12/12 | DR11's four `PermittedEdit` rows fall on three of the eight files |
| `edit_behaviour` | — | PASS | 3 | 0 | 1/1 | — |
| `self_containment` | — | PASS | 55 | 0 | 1/1 | 51 → 55 files (four new modules) |
| `composition` | — | PASS | 42 | 0 | 7/7 | `test_set`/`test_sets` plan columns |
| `rungs` | — | PASS | 98 | 0 | 3/3 | — |
| `provenance` | — | PASS | 4 | 0 | 4/4 | — |
| `data` | — | PASS | 22 | 0 | 6/6 | 17 → 22 (two priors, three census artifacts) |
| `run_path` | — | PASS | 12 | 0 | 12/12 | — |
| `resume_identity` | — | PASS | 379 | 0 | 10/10 | 168 → 379 (24 identity fields, 12 by-design pairs incl. GC's, 340 records) |
| `capability` | — | PASS | 58 | 0 | 5/5 | 54 → 58 (the two new switches); `PROCESS_ARCH_PREDICATE` retired in the driver, the pending table empty |
| `artifacts_check` | — | PASS | 119 | 0 | 3/3 | 95 → 119 (the `test_sets` row per configuration) |
| `artifacts_derive_inputs` | — | PASS | 2 | 0 | 4/4 | — |
| `artifacts_census` | — | PASS | 81 | 0 | 5/5 | — |
| `artifacts_per_run` | — | PASS | 16 | 0 | 2/2 | — |
| `record_completeness` | G7 | PASS | 177 | 0 | 9/9 | 92 declared fields (+`campaign_test_set`, `loop_test_sets`; −`exit_audit.mixed`) |
| `count_neutrality` | GC | PASS | 50 082 (3 957 + 46 125) | 0 | 3/3 | **the DR10 → DR11 straddle** (§7.2), not DR9 → DR10 |
| `prime_map` | G2 | PASS (resumed) | 17 591 | 0 | 3/3 | — |
| `audit_restriction` | G4 | PASS | 12 | 0 | 6/6 | restricted audit at census/1e-8 |
| `entry_and_warm` | G6 | PASS | 6 717 | 0 | 3/3 | **at census/1e-8** (8 pairs, 5 warm) |
| `test_set` | GT | **PASS** | 13 424 | 735 (the three biting drops) | 4/4 | **new** (§6); was NOT RUN |
| `switch_composition` | G5 | PASS | 150 | 0 | 4/4 | 144 → 150 (two switch names more per configuration) |
| `switch_neutrality` | G1 | PASS | 54 961 (3 642 + 51 319) | 0 | 9/9 | **the DR11 straddle `b1bb1594 → 60434c52`** (§7.1) |
| `reproduction` | GR | PASS (read of the `d6c246a1` verdict) | 256 | 0 | 8/8 | read, never pressed (§2.1) |
| `output_path` | G9 | PASS | 3 879 | 0 | 4/4 | GR's records composed under V4's criterion; the "nothing about the solve changed" sub-check gated only under the same criterion (§11, 17 and 23) |
| `written_file_gap` | — | PASS | 42 | 0 | 4/4 | reads `records.AUDIT_RULERS` (§11, 22) |
| `tally_contracts` | — | **FAIL** | 575 (339 + 236) | 40 | 16/17 | reference cells **236/236, 20 of 20** (was 253/256); the 40 are the population check's lines (§2.2 cause 2, now 20 records × 2 tallies); the fixed-point tooth (cause 3) |
| `run_kind_separation` | — | PASS | 194 | 0 | 7/7 | 163 pool records, 31 in the tally's populations; the `smoke` and `supplementary` kinds never pooled |
| `stage_provenance` | — | PASS | 11 | 0 | 5/5 | — |

**28 PASS, 1 FAIL, 0 NOT RUN; 164 of 165 declared teeth tripped** (160 of 162 at `66bfa240`: GT's four
teeth added, one of `tally_contracts`' — "a reference cell moved by one" — tripping again now that the
cells match). `--paper-tables check` refuses as A98 left it ("no campaign record under `runs/`";
`A100_press39_paper_tables_check.log`): the paper's tables are over the campaign, and none exists.

**What `tally_contracts`' 40 mismatches are.** The two tally stages' `reference_runs` population refuses
each of GR's 20 pool records as incomplete under the current contract — `campaign_test_set` and
`loop_test_sets` (DR11's fields) on all 20, `schedule_resolution` (A99's) on the 14 seeded at `d6c246a1`
— one line per record and per tally. GR is read-only (§2.1), so its records never gain the fields; the
reference-cells check, which reads the same records through the previous revision's cell list, is
236/236. At `c4aa37b6` the same gate read **236 cells, 38 matched, 2 of 20 runs reproduced**: under the
census default the tally's `planned_directories(campaign)` had resolved GR's arms to their *census*
records (G6's, GT's). The fix (`ba440ecd`, §11 decision 23) gives every job GR composes V4's criterion
explicitly; the pool admits V4's criterion for any non-campaign job.

---

## 9. Where the records are, and the stamp survey

Every run record, verdict record, stage record and press log of this task is under **one tree**,
`arch_surgery/idf_probe/runs/v5_test_set/` (the worktree's `MDA_partitioning_experiment_v5/runs/` moved
whole before hand-back; the original removed; 1.3 GB, untracked as bulk artifacts are):

| under `v5_test_set/` | what |
|---|---|
| `gates/<name>/gate.json` | every gate's verdict record; `gates/_runs/` the shared pool (163 records); `gates/reproduction/verdict_at_d6c246a1.json` GR's archived verdict; `gates/switch_neutrality/{before,after}/` the DR11 straddle's captures and `straddles/e5137707__a0de2e13/` A99's archived; `gates/count_neutrality/` the DR10 → DR11 sides; `gates/test_set/` GT's runs and `press_at_572be14d_tooth_raised.json`; `gates/gate_table/measurements.json` |
| `census/<configuration>/` | the 16 censused optimisations and their twins (`--census take`, `60434c52`; the two pulsed configurations regenerated at `bfdc7439`) |
| `census_test_sets/` | the stage record and the three artifacts as written (the committed copies are `harness/data/test_sets_<configuration>.json`) |
| `single/test_set_smoke/{census,write_set}/large_tokamak_nof/{B0,B2}/seed000` | the four smoke pairs' records (kind `smoke`); `single/test_set_smoke/supplementary_st_census_exact/st_regression/B2/seed000` the supplementary record (census, τ = 1e-12); `single/st_regression/…` the first `--run` under `write_set` (`60434c52`) |
| `artifacts/smoke_test_set.json` | the smoke stage's record (§8.1) |
| `input_files/` | the lifted input files' stage records |
| `_press_logs/A100_press*.log`, `A100_stamp_survey_{step0,final}.json` | every press of this task in order (0–40) and the two surveys |

**The stamp survey** (`run_stamp_survey.py --json runs/_press_logs/A100_stamp_survey_final.json` at
`ba440ecd`, `A100_press40_stamp_survey.log`): **340 run records**, by `tree_git_head`:

| commit | records | what |
|---|---|---|
| `d6c246a1` | 17 | GR's seeded pool records (16) and its teeth scratch record — the copy commit; never re-made |
| `e5137707`, `f93d1df1`, `3c46287b`, `a0de2e13` | 34, 6, 22, 40 | A99's captures, GC sides and DR10 records (seeded, relocated from `A99_runs/`) |
| `66bfa240` | 56 | the step-0 press (§2): the merged harness before any change |
| `b1bb1594` | 6 | G1's `before` side at the prep commit (`gates/switch_neutrality/before/`) |
| `5980c5dc` | 1 | the first `--run` under `write_set` on `st_regression` (`single/st_regression/A0/write_set_tau1e-06/seed000`) |
| `60434c52` | 63 | G1's `after` side (6, `gates/switch_neutrality/after/`) and 57 pool records: GC's DR11 side and the census stage's runs (`--census take`, resumed by every later census press) |
| `7aa3c0b4` | 3 | the three `A0` seed-0 entry references under the census identity (`gates/_runs/A_A0_*_seed000_gate_*`) |
| `bf395541` | 62 | 60 pool records — GT's runs, G6/G4/G5 at census/1e-8 — and the two pulsed configurations' input-file stage records |
| `521a753c` | 14 | optimisation-phase seed-0 pool records under the census identity (`BR`, `B0`, `B1`, `B2` on the three configurations: G9's runs and `written_file_gap`'s first press) |
| `271168be` | 5 | the smoke pairs on `low_aspect_ratio_DEMO` (the first choice, kept) and **the supplementary record** (`single/test_set_smoke/supplementary_st_census_exact/st_regression/B2/seed000`) |
| `65e7a24a` | 10 | the smoke pairs on `large_tokamak_nof` (4) and six optimisation-phase pool records on the pulsed configurations (`BR`, `B1`, `B2` × 2: `written_file_gap`'s re-press) |
| `c4aa37b6` | 1 | one tooth's scratch record of kind `smoke` (`gates/_runs/A_AR_st_regression_seed000_smoke_*`) |

No record is stamped at `ba440ecd`: the four re-presses after the last driver-facing commit read records
and made none. Records of kinds `smoke` and `supplementary` live under `single/`, never in the pool; the
`run_kind_separation` gate (Table 8.2) is the check.

---

## 10. Proposals (nothing here edits the queue, the V5 list or the V5 plan)

1. **DR11's row for the V5 plan's §11 table**, in the form A99 proposed for DR9/DR10:

   | # | driver change | status | harness impact | if declined |
   |---|---|---|---|---|
   | **DR11** | the loop's stopping subset is the **test set** the run asks for: `PROCESS_ARCH_TEST_SET=census` binds the committed census test sets of the configuration (`PROCESS_ARCH_TEST_SETS`, selected by loop `<mda>/<burn-time owner>`; D32), `=write_set` binds the block's whole write set — V4's predicate exactly, the fallback (D39); required whenever the loop is on, refused when off; what was bound stamped once (`LOOP_TEST_SETS` → `loop_test_sets`); the `mixed` ruler removed and `PROCESS_ARCH_PREDICATE` retired (D30; §12 Q5) | *this report; commit `5980c5dc`, under D37* | τ from `config.TAU_BY_TEST_SET`; the test set and τ in the job identity; the census stage and its artifacts; gate GT; GC's DR10 → DR11 straddle under the fallback; one ruler in the record contract; the supplementary stage hook | V4's whole-`y` test at 1e-6 stands (correct only because it stops one sweep late, A89 §7.3) and the census campaign cannot be run |

2. **Issue: I-29's remaining edge on an unnamed job** (§2.1). `--jobs reproduction` refuses on any tree
   holding G1's captures: GR's unnamed `AR` substitute job resolves by digest to five directories
   (`switch_neutrality/{before,after}/…/AR`, the archived straddle's two, `input_files/…/baseline_evaluation`)
   and the pool refuses to pick. A named directory under GR's root for the substitutes, or a rule that a
   directory under another gate's root is never a candidate for an unnamed job, would close it; a tooth
   either way. Not fixed here (the orchestrator's ruling).
3. **Issue: `tally_contracts` on a tree whose GR records are read-only** (§2.2, cause 2). The tally's
   `reference_runs` population refuses GR's seeded `d6c246a1` records as incomplete under the current
   contract, and GR never re-makes them; until a campaign exists the gate FAILs on 28 population lines
   and on one tooth that cannot trip on the gate population (cause 3). Either the tally's gate-family
   source reads GR's records through the record's *own* contract version, or the campaign's arrival
   moots it; the orchestrator's call. After DR11 the lines are 40 (every field a later schema adds
   is missing from GR's read-only records; §8.2).
4. **Queue rows.** The V5 plan §9 test-set row can name the artifacts (`harness/data/test_sets_<configuration>.json`)
   and their widths (§5); §7 Table 2's GT row can drop "declared placeholder" and cite this report; §3's
   population paragraph gains the result of §5 (the two first-wall geometry components carried in `M3`
   since DR10 — `build.dr_fw_inboard` and `build.dr_fw_outboard`, reader and writer `fw`, run-constants, inert).
5. **The README rewrite** (plan §8) is still pending; §17 is DR11's part of it.
6. **Trap candidate** (for `TRAPS.md`): a gate whose two sides were only ever made in one working
   tree can carry an absolute path in a compared leaf for months without a symptom (GC's
   `defer_per_run_totals.artifact`, A99's three presses); the first straddle across two trees finds it.
   G1 met the same class earlier (its cross-tree paths); a leaf that is a path belongs in a declared
   path-kind table from the day the gate is written.
7. **The GC straddle's `PRIME_CALLS_DECLARATION` and `STRADDLE_TEST_SET` are the two tables the next
   driver change (DR12, the timers) extends** — one row each, committed with the change, as A99 said.

---

## 11. Autonomous decisions, each with its reversal path

Two things were ruled by the orchestrator during the task and are not autonomous: the run-once GR
reading its recorded verdict (§2.1) and the `n_prime_calls` exclusion in the reference cells (§2.2),
both on my message reporting the step-0 findings. Everything below is **autonomous**.

1. **The test set and τ are rendered into the job identity only where they differ from V4's values**
   (`write_set`, 1e-6), so a fallback job carries V4's identity and V4's digest (§3). Chosen because
   D39 says the fallback *is* V4's predicate and every record made before DR11 was made under it — and
   because rendering them always would have orphaned every seeded pool record and made GC's DR10 side
   (22 records at `a0de2e13`) unfindable, so the DR10 → DR11 straddle the brief asks for could not have
   been pressed. *Reversal:* render both fields always (two lines in `Job.identity`, the defaults table
   dropped); every seeded record is then re-made under `--resume`, and GC's before side would have to
   be found by label rather than by digest.
2. **`pool.Job.predicate_mode` and the record's `campaign_predicate_mode` stay** (always `"frozen"`),
   although the brief allowed removing them with the ruler. Removing the identity field changes every
   digest for a field that now names the one ruler. *Reversal:* remove the field from `Job`,
   `JOB_IDENTITY_FIELDS`, the child's `--predicate-mode` and `open_record`, and the schema; the same
   re-make as decision 1's reversal.
3. **The census artifact is keyed by loop, `<mda>/<burn-time owner>`**, not by arm: the driver never
   knows an arm's name, and adding a third switch to tell it one would be a switch that changes
   nothing but a lookup. The mapping arm → loop key is `arms.Arm.loop_key` and the artifact names the
   census arm and the arms each entry applies to. *Reversal:* a `PROCESS_ARCH_TEST_SET_LOOP` switch
   naming the entry; one more registry row and one more composed term.
4. **The binding population of a block is the census union unioned with A92's prior optimisation-path
   set of the twin arm** (the brief's rule: A92's sets — which hold A89's eight-entry sets and the four
   cold-start components — are the starting population); `B1` has no prior and its set is its own
   census, as the brief's "measured, not assumed" asks. *Reversal:* bind the census union alone
   (`derive`: drop the union with `prior_path`); the artifact records both widths so the difference is
   visible without re-running.
5. **The census stage builds the fallback campaign itself** (`test_sets.census_campaign`: the campaign
   with `test_set = write_set`, τ resolved) rather than requiring `--test-set write_set` on the press:
   the census is observation-only on V4's predicate by construction and should not depend on how the
   button was pressed. *Reversal:* refuse unless the campaign is the fallback.
6. **GT's job set is every block arm of the evaluation phase** — `A0`, `A1` (where active), `A2` — from
   G6's pairing entry, not the partitioned arm alone: the brief's "per configuration and partitioned
   arm" read against the plan's "per configuration and arm" and A92's `A0`/`A2` table; the flat arms'
   sets are load-bearing too. *Reversal:* `gate_test_set.ARMS = ("A2",)`.
7. **GT PASSes only if at least one drop bites over the whole job set** (`at_least_one_drop_bit`),
   beside every control clean and every drop biting or not binding: a gate whose tooth never bit has not
   been shown capable of failing (protocol §12), and A92 found the bite on `large_tokamak_nof` in both
   arms. *Reversal:* drop the requirement; the count of bites is still in the verdict.
8. **GC's DR11 side declares `identical` for the prime count** (`PRIME_CALLS_DECLARATION["DR11"]`), the
   stronger check: DR11 changes no count, and DR10's `once_per_evaluation` already holds on both sides.
   **GC's DR11 side is made under the fallback by declaration** (`STRADDLE_TEST_SET`; a press under
   `census` is refused): the census value is another campaign and not a straddle. *Reversal:* declare
   `once_per_evaluation`; drop the declaration table.
9. **The two prior populations live in `harness/data/`** (`test_set_prior_*.json`, entered with
   `data_provenance.py add` from their source commits `2b6aaca4` and `f322ae85`) and **the generated
   test-set artifacts are entered the same way at their own commit** (`GENERATED_ARTIFACT_ROLES`), so
   the `data` gate covers all five and the folder reads nothing outside itself at run time. *Reversal:*
   pass the priors' paths on the command line and drop the five entries.
10. **The `--run` directory names the test set and τ** (`runs/single/<configuration>/<arm>/<set>_tau<τ>/seedNNN`):
    a census run and a fallback run of one arm and seed are two records, and a named directory is the
    job's (I-29's fix). *Reversal:* the old path; a second `--run` of the same arm under the other set
    would then be refused by the pool as another job's record.
11. **The supplementary stage's run kind is a new `records.RUN_KINDS` value, `supplementary`**, with
    the stage's own root under `runs/supplementary/<name>/` (the coordinator asked for "a
    `supplementary` run kind or stage"; the kind is the part that keeps the tally from ever pooling it).
    *Reversal:* stamp it `gate`; the stage root and τ-in-identity stay.
12. **The tally's full-distributions table loses its two `mixed` columns** and **V4's G8 ruler observer
    is removed** from the child (`install_ruler_observer`, `HARNESS_RULER_OBSERVER`): both read the
    ruler that is gone. *Reversal:* restore from `66bfa240`; neither is read by any gate.
13. **The three GR pool records the stopped press had deleted were restored byte-identical** from the
    relocated A99 tree (§2.1), rather than re-made: a re-make would have been a GR run beyond the copy.
    *Reversal:* none needed; the restored directories are `diff -rq` clean against the source.
14. **The thread-pinning defaults went into the prep commit before G1's `before` capture**, so both
    sides of the straddle ran single-threaded (D38). *Reversal:* none sensible; a capture with the
    threads unpinned on one side would compare two environments.
15. **G1's DR10 straddle captures were archived** under
    `runs/gates/switch_neutrality/straddles/e5137707__a0de2e13/` (a copy, as A99 did) before the
    `before` side was re-captured at `b1bb1594`. *Reversal:* none needed; both straddles are on disk.
16. **The 27 G1 leaves and the one GC path leaf were declared by name, with reasons, and the gates
    re-pressed** (§7) rather than the FAILs left standing: every one is a harness stamp or a path,
    none a driver value, and declaring such names is the mechanism both gates are built on (A52's
    conditional exclusions, G1's cross-tree paths; A99 did the same for `schedule_resolution`). Both
    first-press verdicts are kept beside the gates. *Reversal:* remove the entries; both gates then
    FAIL on the same leaves with 0 output-file lines and 0 components differing.
17. **GC makes its declared-fallback side under a fallback campaign it builds itself** (as the census
    stage does), so `--gate all` under the census default presses the DR10 → DR11 straddle instead of
    stopping at a refusal (`7aa3c0b4`). **G9 composes the reproduction gate's records the same way**
    (`271168be`): GR's records carry V4's identity, and the census-default press refused "no
    reproduction gate record for BR/large_tokamak_nof" (`521a753c`). *Reversal:* refuse under the census
    default and require `--test-set write_set` for both.
18. **The census artifact carries the twin arms' loop keys** — `flat/constant` (A1) and
    `partitioned/constant` (A2) bound to B1's and B2's sets with `twin_of` stamped — after GT's first
    press refused A1's loop as unknown (`bf395541`). The twin rule was A92's for A0/A2; extended to A1/B1
    here. *Reversal:* drop the twin entries; GT then cannot run A1 or A2 on a pulsed configuration.
19. **`Job.identity` takes the campaign** to resolve an unresolved test set (the `resume_identity`
    teeth and the run-kind tooth render jobs directly; `resume_identity` FAILed 2/10 teeth at `7aa3c0b4`
    on the unresolved refusal, PASS at `bfdc7439`). *Reversal:* none sensible; the refusal on an
    unresolved job stays.
20. **GT's two crashes** (`n_compared` vs `n_components` in the exit-state comparison, `572be14d`; the
    ulp tooth reading `components` where the snapshot says `state`, `521a753c`) were fixed and the gate
    re-pressed on its kept runs; the crashed verdict is kept (`test_set/press_at_572be14d_tooth_raised.json`).
    Every run GT reads was made at `bf395541`, before either fix, and none was re-made.
21. **The `st_regression` artifact restored from its commit** after `--census write --resume` re-stamped
    it with a later `generated_at_tree_git_head` (its sets and `sets_sha256` unchanged): the committed
    file is the record and the `data` gate binds it. *Reversal:* none needed.
22. **`written_file_gap` reads `records.AUDIT_RULERS`** instead of its own `("frozen", "mixed")` literal
    (`c4aa37b6`): it FAILed 6 of 42 checks at `65e7a24a` ("an argmax or a count is missing" on every run) —
    the one consumer that wrote the ruler pair out rather than reading it. *Reversal:* none sensible; a
    literal here would fail again on the next ruler change.
23. **The reproduction gate's jobs carry V4's criterion explicitly** (`reproduction.v4_criterion` on every
    job GR composes: the twenty planned runs, the `A0` prerequisites, the `A1` pins, the `AR` substitutes,
    the composition tooth; `ba440ecd`) **and the pool admits V4's criterion for any job that is not a
    campaign record**: GR's records are V4's own numbers on the copy (D39), so a gate that reads them
    must resolve GR's directories whatever campaign the button was pressed from. Found by
    `tally_contracts` at `c4aa37b6` (236 cells, 38 matched, 2 of 20 runs reproduced: the census records of
    GR's arms); after, 236/236, 20 of 20. Decision 17's fallback-campaign composition in G9 and the smoke
    stage stays and is now redundant with it. *Reversal:* compose GR's jobs under the campaign and require
    `--test-set write_set` to read them; the tally then FAILs on every cell under the census default.


---

## 12. Limits

- **The census is a union over what it observed** (V5 plan §12): two seeds per configuration and arm,
  the input file's own start and the first displaced one; a branch the optimiser takes only on another
  seed is unobserved. What bounds that is GT and the whole-`y` exit audit on every run, not the census.
- **GT's binding rule finds a bite only where one component decides the stop.** On the entries where the
  whole exit residual is 0.0 (the loops settle to bit-identical sweeps) nothing can bind and the row
  reports it; the gate's tooth is shown on the configurations where a component does bind. On `low_aspect_ratio_DEMO` the three binding rows are tie-breaks (every carried residual 0.0) and on `st_regression` `tfcoil.str_wp` is not the last to reach τ; GT's `at_least_one_drop_bit` requirement is met over the whole job set (3 bites, all on `large_tokamak_nof`) and would not be met on a campaign of the other two configurations alone — a limit of the rule, not of the sets.
- **The first-wall pair carried in `M3` is inert** (a run-constant, D19): it widens the census set by two
  without changing any stop. It is in the set because the rule says so; it is not evidence that DR10
  changed a coupling.
- **`A1`'s and `A2`'s loop entries are bound by the twin rule**, not censused: no census ran an
  evaluation-phase arm, and the constant-owned burn time is, like the optimiser-owned one, written by no
  loop node. GT measures the bound sets on `A1` and `A2` directly (§6), which is the check the twin rule
  gets.
- **G1 and GC each FAILed on a first press on harness bookkeeping** (§7) — 27 stamp leaves, one path leaf —
  and PASSed after the leaves were declared by name; the declarations are conditional or path-kind, and
  the exclusion review lists them. No driver value was ever in a differing leaf.
- **The test set and τ are absent from a fallback job's identity by design** (§3, decision 1): a reader
  of a raw `job_identity` must know that "no `test_set` key" means the fallback at 1e-6. The child's
  `campaign_test_set` / `campaign_tau` stamps say it explicitly on every record, and `--jobs` prints
  `set=…`/`tau=…` only where they differ from V4's.
- **`tally_contracts` FAILs at the merged tip and after** for reasons this task does not touch (§2.2,
  §8.2): 20 read-only GR records missing later fields, and one tooth that cannot trip on the gate
  population; its reference cells are 236/236. The gate table carries the FAIL.
- Timings appear only as the pool's progress lines and as the census instrument's cost (a censused
  optimisation took 2.3–4× its twin's wall clock); none is cited as evidence.
- Nothing here has been applied to V4; the two prior populations were copied from their commits, never
  edited.

---

## 13. Files changed outside `PROCESS/`

Under `PROCESS/`: `process/core/caller.py`, `process/core/solver/__init__.py`,
`process/core/solver/module_solve.py` (§4); `copy_gates.py` (four `PermittedEdit` rows),
`PROVENANCE.json` (regenerated), `CHANGES.md` (§4.1.3, §4.2.9, §4.2.10, §4.5.16). Nothing under
`process/models/`. Nothing under `MDA_partitioning_experiment_v4/` or any sibling clone.

| file | change |
|---|---|
| `harness/child/read_before_write_census.py` | **new** — the census instrument (A89's `rbw_census.py` and A92's per-evaluation form, T18's snapshot-around-every-node) |
| `harness/experiment/test_sets.py` | **new** — the census stage: job set, twins, the reproduction check, the union, the priors, the artifact, the teeth |
| `harness/gates/gate_test_set.py` | **new** — gate GT |
| `harness/measurement/test_set_smoke.py` | **new** — the smoke pairs stage |
| `harness/data/test_set_prior_eight_entry.json`, `harness/data/test_set_prior_optimisation_path.json` | **new** — A89's `rbw_sets.json` (source commit `2b6aaca4`) and A92's `optimisation_path_sets.json` (`f322ae85`), entered with `data_provenance.py add` |
| `harness/data/test_sets_<configuration>.json` (3) | **new** — the census test sets, written by `--census write`, entered with `add` at their own commit (§5) |
| `harness/data/PROVENANCE.json` | re-recorded (`ystate.py`'s hunks; the five new files) |
| `harness/child/ystate.py` | the `mixed` ruler removed |
| `harness/child/child.py` | `open_record` stamps `campaign_test_set`; `harvest_counters` reads `LOOP_TEST_SETS`; the null stamp; the ruler observer removed; the one-ruler note |
| `harness/child/optimise.py`, `harness/child/evaluate.py` | `--test-set`; the census hook (optimise); the ruler observer's call sites removed (evaluate) |
| `harness/core/config.py` | `TEST_SETS`, `TAU_BY_TEST_SET`, `DEFAULT_TEST_SET`, `V4_TEST_SET`, `SupplementaryStage`, `SUPPLEMENTARY_STAGES`; `Campaign.test_set` / `tau` / `tau_overridden` / `supplementary`; `Config.test_sets_path`; the artifact names; `MEASUREMENT_ARTIFACTS`, `MEASUREMENT_ARTIFACT_SOURCES`, `GENERATED_ARTIFACT_ROLES`; `default_campaign(test_set, tau)` |
| `harness/core/records.py` | `RUN_KINDS` + `supplementary`; the schema (`campaign_test_set`, `loop_test_sets`; `exit_audit.mixed` gone); `AUDIT_RULERS`; `assert_audit_ruler`; `IDENTITY_FIELDS_STAMPED_BY_THE_CHILD` + `IDENTITY_DEFAULTS_WHEN_ABSENT` |
| `harness/core/pool.py` | `Job.test_set` / `tau`; the identity rendering; `readable_key`; `resolve_settings`; `--test-set` on the command line |
| `harness/experiment/arms.py` | `Arm.loop_key`; `terms` / `env_for` take the test set and τ; the `test_set` / `test_sets` terms |
| `harness/experiment/switches.py` | the `test_set` and `test_sets` switches; `DIAGNOSTIC_READBACKS`; `RETIRED_PENDING_IN_DRIVER` emptied; the thread defaults |
| `harness/experiment/artifacts.py` | the `test_sets` format and `_check_test_sets`; the teeth's throwaway campaign |
| `harness/experiment/data_provenance.py` | generated and prior artifacts in `declared_files`, `EXPECTED_MAPPING`, `add`, `build_provenance`; `MODULE_EDITS` |
| `harness/chain.py` | `supplementary_jobs` |
| `harness/gates/registry.py` | GT real, `DECLARED_NOT_IMPLEMENTED` empty, `GATE_ORDER`; the run-once read form and `RUN_ONCE_COMMIT` |
| `harness/gates/gate_count_neutrality.py` | `STRADDLE = ("DR10", "DR11")`, `STRADDLE_TEST_SET`, the `identical` declaration, the mixed leaf gone |
| `harness/gates/gate_neutrality.py` | `loop_test_sets`, `campaign_test_set` and the reworded `exit_audit.mixed` in `FIELDS_ADDED_BY_A_DRIVER_CHANGE` |
| `harness/gates/gate_composition.py` | the plan column's `test_set` / `test_sets` rows |
| `harness/gates/gate_records.py` | the one-ruler check and tooth |
| `harness/gates/gate_resume_identity.py` | GC's by-design pair |
| `harness/gates/reference.py` | `n_prime_calls` named out (DR10) |
| `harness/gates/selfcheck.py` | `_ROLE_ORDER` + `test_sets` |
| `harness/measurement/tally_evaluation.py` | the two `mixed` columns gone |
| `harness/README.md` | §17 |
| `harness/__init__.py` | `0.2.0 → 0.3.0` (the record schema changed) |
| `experiment_runner.py` | `--test-set`, `--tau`, `--census`, `--smoke-test-set`, `--ladder-record`, `--supplementary`; the single-run directory names the test set and τ; the fifth artifact teeth stage |
| `PROCESS_diff.py` | the two DR11 mechanisms, fourteen annotations, three summary addenda |

---

## Appendix — change log (append-only)

- 2026-09-29 — created at `66bfa240` with the step-0 press (§2) and the two orchestrator rulings (GR
  read-once; `n_prime_calls` excluded), commit `b1bb1594`.
- 2026-09-29 — DR11 (`5980c5dc`), the pool fix (`60434c52`), the census, G1 and GC straddles, the
  artifacts row, README §17 (`3d56c4ad`, `c533701c`); §3–§5, §7 written.
- 2026-09-29 — the coordinator's supplementary-stage addition (A96 merged): `SupplementaryStage`,
  `st_census_exact`, the `supplementary` run kind, the smoke record beside A96's; §3 and §8.1.
- 2026-09-29 — GT's presses (`bfdc7439`, `572be14d`, `521a753c`); §6.
- 2026-09-29 — the `--gate all` presses under the census default and their fixes (`7aa3c0b4`, `271168be`,
  `65e7a24a`, `c4aa37b6`); §8.
- 2026-09-29 — `ba440ecd`: GR's jobs under V4's criterion; the final gate table (§8.2), records and
  survey (§9), verdict (§1), decisions 22–23; report committed; runs moved to
  `idf_probe/runs/v5_test_set/`.
