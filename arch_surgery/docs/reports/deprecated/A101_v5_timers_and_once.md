# A101 (v5-timers-and-once) — item 5 (the deferred set executed once at the evaluation's exit) and DR12 (observation-only timers)

> **Document status** — **MERGED 2026-09-29 at `451d7389` (`--no-ff`, under D37: item 5 and DR12 on the orchestrator's assessment, §15, the driver diffs in §3 and §7 for the user's review on return); archived.** Records relocated to `arch_surgery/idf_probe/runs/A101_runs/v5_timers_and_once/` (one tree, 509 records). Was: **OPEN** task report, branch `A101-v5-timers-and-once` from `architecture_surgery`
> at `ca7200ff`. Two driver changes to the V5 copy, each straddled by G1 and GC in its own commit, under
> autonomous mode (D37): the diffs of every file under `PROCESS/` are in §3 and §7 for the user's review
> on return. Records under `arch_surgery/idf_probe/runs/v5_timers_and_once/` (the worktree's
> `MDA_partitioning_experiment_v5/runs/`, copied whole at hand-back). Every number here names the commit
> it was made at; wall-clock numbers are context, never evidence (D33).

## 1. Verdict

**Both changes are in, each straddled, and no count moved that was not declared.**

1. **Item 5 (commit `cfa0d3ff`; D35).** `PROCESS_ARCH_DEFER_PER_RUN_EXECUTION=evaluation_exit` makes every
   `call_models` end with one sweep of the per-run deferred set on the converged state — the output
   path's own mechanism, measured, not charged. The harness composes it for the evaluation phase's
   deferring arm (`A2`) only. **G1 PASS** (straddle `c161500c → cfa0d3ff`: 3 669 record values and
   51 319 output-file lines compared, 0 differing, 9/9 teeth). **GC PASS** under a *declared count rule*
   (straddle `DR11 → item5`, 22 pairs, 3 989 count leaves under 41 paths, 0 differing from the rule's
   prediction; 46 125 exit-state components, 0 differing outside the declared set; 4/4 teeth): on the
   three `A2` evaluations the per-run nodes' census went 0 → 1 each, `node_calls_total` and
   `node_calls_single_eval` by their number (60 → 63, 60 → 63, 62 → 66), **and one dispatch sweep**
   (13 → 14, 13 → 14, 15 → 16) — the sweep the brief's "nothing else" did not foresee, because the
   execution *is* a sweep of the dispatch body (§4); 112 of the 124/125 components the per-run nodes
   write differ in the exit state, 0 others. Every optimisation-phase pair identical to the digit.
2. **G4 retired (commit `9ed0da4c`; D36).** Pressed after item 5, `audit_restriction` **FAILs** on its
   per-run-owned tooth — a component doctored in the entry snapshot is overwritten by the
   once-execution before the audit, so 9 of 9 doctorings no longer move the whole-state audit — while
   its agreement block reads **18 of 18** partitioned evaluation records agreeing (the whole-state and
   the restricted maximum the same hex float on the same component) on all three configurations, against
   6 of 51 records made before the change (§5). D36's retirement condition is met and the FAIL is its
   evidence; the gate is out of the registry and the tally's matched-accuracy table reads the whole state.
3. **DR12 (commit `24b78e2d`; D33, D38).** `PROCESS_ARCH_TIMERS=on` accumulates per node, per sweep, the
   convergence test's three pieces, the objective layer, per evaluation and per run; unset, every hook is
   one `is None` test. **G1 PASS** (straddle `9ed0da4c → 24b78e2d`: 3 669 record values and 51 319
   output-file lines compared, 0 differing, 9/9 teeth). **GC PASS** (straddle `item5 → DR12`, the DR12
   side made *with the timers on*: 22 pairs, 3 989 count leaves, 0 differing; 46 125 exit-state
   components, 0 differing; 4/4 teeth after one tooth was fixed, §8.2) — the instrument moves no count
   and no bit. The harness harvests before its audit and names every excluded cost as a number (§6).
4. **The timing stages** (`--timing repeatability | timers-off | validity | tables`) ran on the gate job
   set as their smoke (§9–§10): 22 jobs × 3 repetitions at W = 1, 0 refused (every count identical
   across repetitions); the unattributed residual 0.05–0.15 % of an evaluation's wall and
   0.10–0.93 % of an optimisation's; the instrument's own cost −4.4 % to +4.4 % of the launcher's
   wall (median −1.3 %, positive on 5 of 22 jobs: below the machine's noise); the validity check waits
   for a campaign record. The three appendix tables are wired into `paper_tables.py` and smoked on the
   timing records as test data. **One limit to read first**: a phase A run's timing is a
   first-evaluation-in-process figure (numba's cache load inside the nodes' first calls: 259–351 ms per
   evaluation against 21–32 ms inside an optimisation), §13.
5. **The gate table after** (§11): **27 PASS, 1 FAIL, 0 NOT RUN; 163 of 164 declared teeth tripped** (28 registered gates: G4 gone, every verdict but two at `b9b134d9`). `tally_contracts`' FAIL on I-35's population
   lines is inherited and reported, not fixed. Three teeth of this task's own could not trip on their
   first press and were fixed and re-pressed (§8.2, §8.3, §8.6); no gate was tuned.

## 2. What was briefed, and the order taken

Two driver changes, two commits, item 5 first (it changes counts on purpose) then DR12 (no count moves).
Between them, D36's consequence — G4's agreement press and retirement — in its own commit, because a
gate is retired on a result and the result had to be on disk first. A prep commit (`c161500c`) preceded
item 5: the pool's rule that a kept record must have been composed from the switch terms the arm sets
today, without which item 5's re-makes could not have been scoped to the `A2` evaluation records (§4.3).

Commits, in order (`git log ca7200ff..`):

| commit | what |
|---|---|
| `c161500c` | prep: `pool.why_not_composed_as_today` (a record's `switches_asked` against the arm's terms by name), a `resume_identity` tooth |
| `cfa0d3ff` | **item 5**: the driver change, its switch, GC's declared count rule, the copy's provenance |
| `0353c524` | D36: G4's agreement block and tooth; the tally's matched-accuracy statistic → whole state; the paper's A1 verification row |
| `9ed0da4c` | G4 retired from the registry (its module deleted; `resume_identity`'s three G4 pairs replaced) |
| `24b78e2d` | **DR12**: the timers in the driver, the harness's harvest, the stages, the appendix tables |
| `d8873d49` | after the DR12 presses: two teeth that could not trip and one refusal fixed (§8); README §18 |
| `b9b134d9` | `resume_identity`'s synthetic record stamps the default for an absent identity field (§8.6) |
| the hand-back commit | this report (the gate table and the stamp survey are read from the records at `b9b134d9`) |

## 3. Item 5 — the driver change, in full (`cfa0d3ff`; the user reviews this on return)

One file under `process/`: `process/core/caller.py` (+83/−4). Nothing under `process/models/` (G0 PASS,
`copy_gates.py all` ALL GATES PASS at the commit). The copy's `copy_gates.py` gains one `PermittedEdit`
row, `PROVENANCE.json` is regenerated, `CHANGES.md` gains §4.5.17 and `PROCESS_diff.py` its annotations
(its exit 1 is I-34's four pre-existing `evaluators.py` hunks, unchanged).

```diff
diff --git a/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/caller.py b/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/caller.py
index 7fa8978e..6091c810 100644
--- a/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/caller.py
+++ b/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/caller.py
@@ -521,13 +521,60 @@ if DEFER_PER_RUN_ENABLED and not Path(DEFER_PER_RUN_PATH).exists():
         f"refuse rather than silently run everything."
     )
 
+# V5 list item 5 (task A101 (v5-timers-and-once); decision D35): WHERE the
+# per-run deferred set is executed once.  Switch:
+# ``PROCESS_ARCH_DEFER_PER_RUN_EXECUTION``.
+#
+# ``output_path`` (the variable unset, the default): the set runs once at the
+# entry to :func:`write_output_files`, after the optimiser has accepted --
+# the optimisation phase's place for it, unchanged.  ``evaluation_exit``: the
+# set runs once at the exit of **every** :meth:`Caller.call_models`, on the
+# converged state, after the objective and constraints are computed (they
+# read nothing the set writes -- that is the set's defining property).  It
+# exists for the evaluation phase, whose one ``call_models`` is the whole run
+# and never reaches the output path: an evaluation is the MDA converged and
+# then every deferred node executed once, so that its exit state carries the
+# same information as a flat evaluation's (the user, 2026-09-29: "it should
+# mimic a full model evaluation yielding the same output as the reference
+# case").  The execution is one sweep of the dispatch body over the set --
+# the same route the output path takes -- counted like any other node call
+# (measured, not charged) and one dispatch sweep.  Composed by the harness
+# in the evaluation phase only; an optimisation composing it would execute
+# the set once per evaluation, which no arm of the experiment does.
+_DEFER_PER_RUN_EXECUTIONS: tuple[str, ...] = ("output_path", "evaluation_exit")
+
+DEFER_PER_RUN_EXECUTION: str = (
+    os.environ.get("PROCESS_ARCH_DEFER_PER_RUN_EXECUTION", "").strip()
+    or "output_path"
+)
+if DEFER_PER_RUN_EXECUTION not in _DEFER_PER_RUN_EXECUTIONS:
+    raise ArchitectureRefusal(
+        f"PROCESS_ARCH_DEFER_PER_RUN_EXECUTION={DEFER_PER_RUN_EXECUTION!r} is "
+        f"not a known execution point; expected one of "
+        f"{_DEFER_PER_RUN_EXECUTIONS} (or unset for 'output_path')."
+    )
+if DEFER_PER_RUN_EXECUTION != "output_path" and not DEFER_PER_RUN_ENABLED:
+    raise ArchitectureRefusal(
+        f"PROCESS_ARCH_DEFER_PER_RUN_EXECUTION={DEFER_PER_RUN_EXECUTION!r} "
+        f"with PROCESS_ARCH_DEFER_PER_RUN unset: there is no deferred set to "
+        f"execute.  Refused rather than silently a no-op."
+    )
+#: True when the set is executed at the exit of every ``call_models``.  One
+#: boolean read per evaluation on the default path (gate G1).
+DEFER_PER_RUN_AT_EVALUATION_EXIT: bool = DEFER_PER_RUN_EXECUTION == "evaluation_exit"
+
 #: Diagnostics for the run record.  Integer counts and names only.
 DEFER_PER_RUN_TOTALS: dict = {
     "artifact": DEFER_PER_RUN_PATH,
     "nodes": None,                      # filled after validation
     "n_call_sites_suppressed": 0,       # solve-phase _node sites skipped
     "suppressed_by_node": {},
-    "executed_once": None,              # set by write_output_files
+    "executed_once": None,              # set where the set is executed
+    # V5 list item 5: where the set was executed and how many times -- one
+    # execution per run in both phases (the output path's, or the evaluation
+    # phase's one call_models); gate GC compares the count.
+    "execution": DEFER_PER_RUN_EXECUTION,
+    "n_executions": 0,
     "validated": False,
 }
 
@@ -1509,6 +1556,28 @@ class Caller:
         for _name, run in pending:
             run()
 
+    def _execute_deferred_per_run_set_once(self, xc: np.ndarray) -> None:
+        """Execute the per-run deferred set once, on the state as it stands.
+
+        V5 list item 5 (A101 (v5-timers-and-once); decision D35).  The same
+        mechanism as the output path's execution of the set
+        (:func:`write_output_files`): one sweep of the dispatch body -- the
+        same ``_call_models_once`` walks the same switch dispatch in sequence
+        order and ``_node`` drops everything outside the set -- with the
+        exclusion lifted for it, so the set's nodes run and are counted like
+        any other node call, and the sweep is counted like any other sweep.
+        The exclusion is set again at the next ``call_models`` entry.
+        Reached only with PROCESS_ARCH_DEFER_PER_RUN_EXECUTION=evaluation_exit.
+        """
+        ps = _defer_per_run_nodes(self.data)
+        DEFER_PER_RUN_TOTALS["executed_once"] = sorted(ps)
+        DEFER_PER_RUN_TOTALS["executed_once_at_node_calls"] = NODE_CALLS[0]
+        DEFER_PER_RUN_TOTALS["n_executions"] += 1
+        if not ps:
+            return
+        self._defer_per_run = None
+        self._sweep_block(xc, ps)
+
     @staticmethod
     def check_agreement(
         previous: float | np.ndarray, current: float | np.ndarray
@@ -1868,7 +1937,14 @@ class Caller:
         # every path (normal return, the VP4 early return, or a raise).
         _sweeps_at_entry = DISPATCH_SWEEPS[0]
         try:
-            return self._call_models_inner(xc, m)
+            objf, conf = self._call_models_inner(xc, m)
+            # V5 list item 5 (A101; D35): with the execution point at the
+            # evaluation's exit, the per-run deferred set runs once here, on
+            # the converged state, inside this evaluation's sweep count.
+            # One boolean read with the switch unset (gate G1).
+            if DEFER_PER_RUN_AT_EVALUATION_EXIT:
+                self._execute_deferred_per_run_set_once(xc)
+            return objf, conf
         finally:
             _n = DISPATCH_SWEEPS[0] - _sweeps_at_entry
             _k = str(_n)
@@ -2490,6 +2566,9 @@ def write_output_files(
         ps = _defer_per_run_nodes(data)
         DEFER_PER_RUN_TOTALS["executed_once"] = sorted(ps)
         DEFER_PER_RUN_TOTALS["executed_once_at_node_calls"] = NODE_CALLS[0]
+        # V5 list item 5 (A101): the execution counted, so that a record says
+        # how many times the set ran -- one, here, in the optimisation phase.
+        DEFER_PER_RUN_TOTALS["n_executions"] += 1
         if ps:
             caller._sweep_block(x, ps)
     if runtime is not None:
```

**The switch, read back.** `PROCESS_ARCH_DEFER_PER_RUN_EXECUTION` ∈ {unset = `output_path`,
`evaluation_exit`}; refused on an unknown value and refused without `PROCESS_ARCH_DEFER_PER_RUN`.
Read-backs `caller.DEFER_PER_RUN_EXECUTION` (the string) and `caller.DEFER_PER_RUN_AT_EVALUATION_EXIT`
(the boolean the evaluation's exit tests). The harness composes it in `Arm.terms` for a deferring arm
of phase A (`A2`) — not a matrix row: it follows from the phase and the deferral (§12, decision 1).

## 4. Item 5's count change on GC's job set

### 4.1 G1 (`switch_neutrality`), `c161500c → cfa0d3ff`

The `before` side was captured at `c161500c` with the driver change stashed (the tree at that commit,
`tree_git_dirty` false), the `after` side at `cfa0d3ff`; every switch unset, `AR` and `BR` on the three
configurations, W = 3, children single-threaded. **PASS**: 6 pairs, 3 669 deterministic record values
compared, 0 differing, 666 excluded by name; 51 319 output-file lines, 0 differing; 9/9 teeth. Records
`runs/gates/switch_neutrality/straddles/c161500c__cfa0d3ff/` (archived at DR12's capture; the DR11
straddle's captures archived beside under `b1bb1594__60434c52/`). Log `A101_press3_G1_item5_compare.log`.

### 4.2 GC (`count_neutrality`), `DR11 → item5`, under the fallback, the declared rule

`STRADDLE = ("DR11", "item5")`, both sides under `write_set` (`STRADDLE_TEST_SET`); the after side made at
`cfa0d3ff` (22 labelled jobs; the three entry references kept). The change is *meant* to move counts, so
GC gained a **declared count rule** (`COUNT_RULE_DECLARATION["item5"] =
deferred_set_executed_once_at_evaluation_exit`): the after side is **predicted** from the before side
under the rule and the prediction compared leaf by leaf with the after side, so an undeclared move is a
mismatch like any other. The rule, on an evaluation-phase record whose read-back says
`DEFER_PER_RUN_AT_EVALUATION_EXIT`: the per-run nodes' census 0 → 1 each; `node_calls_total` and
`node_calls_single_eval` + their number; `dispatch_sweeps` and `n_model_calls_sweeps` + 1;
`sweeps_per_eval.hist` shifted by that sweep; `defer_per_run_totals.{executed_once,
executed_once_at_node_calls (= the before side's node_calls_total), execution = evaluation_exit,
n_executions = 1}`; the whole-state audit maximum reported on both sides and not compared. On an
optimisation-phase record of a deferring arm: `execution = output_path`, `n_executions = 1`, nothing else.
The exit-state comparison lets differ only the components the per-run nodes write on the configuration
(`gate_output_path.excluded_by_the_per_run_nodes`, the audit's own derivation), counted and named beside.

**PASS** (`A101_press4_GC_DR11_item5.log`; record `runs/gates/count_neutrality/straddles/DR11__item5.json`):
22 pairs; 3 989 count leaves under 41 paths and the rule, **0 differing**; 33 prime checks (`identical`),
0 failing; 46 125 components, **0 differing outside the declared set**; 4/4 teeth (the new one: `costs`
counted 1 → 2 on a copy of `A/A2/st_regression`'s after side is the one differing leaf of 148 under the
rule, 15 declared moves applied).

**Table 4.1 — item 5's declared moves on the three `A2` evaluations** (the displaced entry at seed 1,
δ = 0.10, write_set / 1e-6; before = `60434c52`, after = `cfa0d3ff`). *Every other leaf of the 41 count
paths identical; every optimisation-phase pair identical to the digit.*

| configuration | per-run nodes (0 → 1 each) | `node_calls_single_eval` = `node_calls_total` | `dispatch_sweeps` = `n_model_calls_sweeps` | exit-state components differing (declared set) | whole-state audit max before → after |
|---|---|---|---|---|---|
| `large_tokamak_nof` | costs, vacuum, water_use | 60 → 63 | 13 → 14 | 112 of 124; 0 of 716 outside | 0x1.f5b2a3ea40bd7p-1 (0.98) → 0x1.e01297621e3f8p-27 (1.4e-8) |
| `low_aspect_ratio_DEMO` | costs, vacuum, water_use | 60 → 63 | 13 → 14 | 112 of 125; 0 of 721 outside | 0x1.ad17b67239f49p-4 (0.105) → 0x0.0p+0 |
| `st_regression` | costs, pulse, vacuum, water_use | 62 → 66 | 15 → 16 | 112 of 125; 0 of 702 outside | 0x1.fabf584472547p-3 (0.247) → 0x1.9e44b1da8552dp-29 (2.9e-9) |

**The one move the brief did not foresee is the dispatch sweep.** The brief declared "the per-run
deferred nodes' calls 0 → 1 each and `node_calls` totals by that sum; nothing else". The execution is the
output path's own mechanism — `_sweep_block` over the set, one walk of `_call_models_once` — and a sweep
of the dispatch body increments `DISPATCH_SWEEPS` and `numerics.n_model_calls` like every other; the
optimisation phase already counts that sweep at the output path (`records.sweep_decomposition`'s
"per-run deferral sweep" term, which now decomposes the evaluation phase's total too). Declaring the
sweep rather than hiding it from the counter keeps one meaning of "sweep" in both phases; the
alternative — a special case in `_call_models_once` that does not count when it runs the set — would
have been a second code path for one sweep. Reported as a result (§12, decision 3).

### 4.3 Which records the change re-made, and how that was scoped

The job identity names the arm, never its switches, so every earlier `A2` evaluation record had the same
digest as the changed arm's and `--resume` would have kept it. The prep commit makes the pool compare a
kept record's `switches_asked` with the arm's terms **by name** (`pool.why_not_composed_as_today`; values
are not compared — a path term differs between two trees by construction, T20): a record composed
without a term the arm now sets is a record of a run the arm no longer makes and is re-made, with the
reason printed. Under `--resume` this re-made exactly the `A2` evaluation-phase records — G4's baselines
and doctorings, G6's pairing and warm runs, GT's full-set and dropped runs, G2's prime on/off pairs — and
kept every other pool record (`A0`, `A1`, `AR` evaluations; every optimisation). A `resume_identity` tooth
(one term fewer, one more) shows the rule can refuse; `resume_identity` PASS, 12 by-design pairs.

### 4.4 G2, G6, GT re-pressed — what they read that item 5 alters

All three read `A2` evaluation records (exit states that now carry the once-executed nodes' outputs), so
all three were re-pressed with `--resume` at `9ed0da4c` after the retirement commit (logs
`A101_press6`–`8`):

| gate | re-made | verdict | compared |
|---|---|---|---|
| G6 `entry_and_warm` | the three `A2` pairing runs at seed 1 and the `A2` warm runs | **PASS** | 8 entry pairs, 5 warm runs, 16 evaluations; 6 717 compared, 0 mismatched; 3/3 teeth |
| GT `test_set` | the three `A2` full-set runs and their drops | **PASS** | 8 full-set runs, 8 binding drops of which 3 bite, 8/8 controls bit-identical; 13 424 exit-state components, 794 differing (the three biting drops; 735 before item 5 — the exit states now carry the per-run nodes' outputs, which a one-sweep-earlier stop moves too); 4/4 teeth |
| G2 `prime_map` | the `A2` prime on/off pairs from the reference snapshot | **PASS** | (i) 6 pairs, 12 evaluations, 5 026 components, 0 differing; (ii) GC's DR9 → DR10 straddle read, 12 565 components, 0 differing; 3/3 teeth |

The paper's `A2` Post-processing cell now reads the measured **1** on every evaluation record
(`EXACT_CELLS` checks it is one integer on every run); `CHARGED_ONCE` stays retired.

## 5. G4's agreement and retirement (D36)

**The press** (`A101_press5_G4_after_item5.log`, at `0353c524`; the verdict kept as
`runs/gates/audit_restriction/gate_at_0353c524_FAIL_retired_under_D36.json`): `--gate audit_restriction
--resume` re-made the three `A2` baselines and the 12 doctored entries (`_entries/` re-doctored from the
same reference snapshots) and kept the three `B2` optimisations. **FAIL**, 12 compared, 9 mismatched:
every per-run-owned doctoring (`costs.c21`, `vacuum.dia_vv_vacuum_ducts`, `water_use.energypervol` on
nof and st; `costs.blkcst` on lad) fails
`the_whole_state_audit_reads_the_displacement` and `the_whole_state_maximum_moved` — the doctored
component is recomputed by the once-execution before the audit sweeps, so the audit reads no
displacement; the in-loop doctoring (`blanket.deg_blkt_inboard_poloidal_plasma`, 3/3) still trips; the
tooth "a doctored per-run-owned component" DID NOT TRIP. That is the restriction's premise gone: there is
no component of the exit state left stale by design for it to be blind to.

**Table 5.1 — the agreement, per configuration** (the block `agreement` of that verdict; population:
every finished `A2` evaluation-phase record under `runs/gates/` — the pool and the gates' directories —
split by the driver read-back `DEFER_PER_RUN_AT_EVALUATION_EXIT`; *agree* = the whole-state maximum and
the restricted maximum the same hex float on the same component).

| configuration | after item 5: agreeing / records | whole-state = restricted (hex, argmax) | before item 5: agreeing / records | before, typical (whole; restricted) |
|---|---|---|---|---|
| `large_tokamak_nof` | **6 / 6** | `0x1.fd33f63147e62p-42` on `pf_coil.stress_z_cs_self_midplane_profile` (5, the reference entry at `0353c524`); `0x1.e01297621e3f8p-27` on the same (seed 1, `cfa0d3ff`) | 0 / 17 | 1.5e-8 on `costs.coecap`; 2.4e-11 on `pf_coil.stress_z_cs_self_midplane_profile` |
| `low_aspect_ratio_DEMO` | **6 / 6** | `0x0.0p+0` on `blanket.deg_blkt_inboard_poloidal_plasma` (all 6) | 6 / 17 | 0.0 on both (the per-run outputs happened to be exact there) |
| `st_regression` | **6 / 6** | `0x1.eae3a0e959de8p-34` on `superconducting_tfcoil.a_tf_plasma_case` (5); `0x1.9e44b1da8552dp-29` on the same (seed 1) | 0 / 17 | 2.6e-10 on `costs.c22213`, or 0.5 on `water_use.energypervol`; 1.1e-10 on `superconducting_tfcoil.a_tf_plasma_case` |

18 of 18 after, 6 of 51 before. The tooth "a doctored whole-state maximum reads as disagreement" tripped
(nof's maximum doubled reads as disagreement; undoctored 6 of 6 agree).

**Retired** (`9ed0da4c`): `audit_restriction` removed from `registry._plan_gates` and `GATE_ORDER`,
`harness/gates/gate_audit.py` deleted (dead code is removed; the agreement construction lives in the kept
verdict and here); `resume_identity`'s three G4 pairs replaced (G7's forced optimisation against G5's
matrix-composed one; two named entry files for the entry-state class; GT's full-set run against G6's
pairing run of the same arm, which must be the same job — it is). The tally's `matched accuracy` table
reads the whole state only (`stats.whole_state_population`; columns whole-state median / p90, argmax,
runs with a component ≥ τ, worst run); `matched accuracy by configuration` and `full distributions`
likewise; the record keeps `exit_audit.restricted` (cheap, and G1/GC leaves name it) — §12, decision 6.
The paper's verification row **A1** is now a construction: D34's pair within F at median and p90 *and*
0 runs with a component above τ on both arms, from the evaluation tally's stage record.

## 6. DR12 — the timer design as built

**The switch.** `PROCESS_ARCH_TIMERS` ∈ {unset, `on`} (registry term `timers`; refused on any other
value); read-backs `caller.TIMERS_ENABLED`, `caller.TIMERS_NAME`, and `caller.TIMERS` (the accumulators,
`None` when off) as a diagnostic read-back. **Unset ⇒ `TIMERS is None` and every hook is one `is None`
test** — DR8's block-trace precedent; G1 is the proof (§8.1).

**What is accumulated in the driver** (`caller.TIMERS`; `time.perf_counter` for durations, `time.time`
for the epochs):

| accumulator | where | what |
|---|---|---|
| `node_s[node]`, `node_n[node]` | `_node`, around `run()` | the model's own wall, per node; **summed per module through the node map by the tables** (M1, M2, M3, Feedforward, Post-processing), kept per node in the record |
| `tail_node_s[node]` | `_run_deferred_tail` | the flat per-call tail's direct calls (outside every sweep; no V5 arm makes them) |
| `sweep_s`, `n_sweeps` | `_call_models_once`, the tokamak path | every sweep of the dispatch body |
| `test_bind_s`, `test_read_s`, `test_residual_s` (+ counts) | `_call_models_partitioned`: the bind once per evaluation; `read` and `residual` through two wrappers bound only when on | the **MDA convergence test** (the plan's "read plus residual", the bind beside) |
| `upstream_test_s` | the flat loop's `check_agreement` pair | the reference arms' own convergence test |
| `objective_s`, `n_objective` | `_timed_objective`, one helper at the four sites | the **objective and constraints** layer (the two long names kept apart: the table's "MDA convergence test" is the coupling-state predicate, "objective and constraints" what upstream's idempotence predicate compares) |
| `call_models_s`, `n_call_models`, `first_call_models_at`, `last_call_models_ended_at` | `call_models`'s `try/finally` | every evaluation, and the epochs of the first and the last |
| `run_setup_s` | `resolve_schedule`'s miss path, `_defer_per_run_nodes`' validation, the artifacts' first load | the once-per-run resolution inside the first evaluation (DR9's), **folded into the fixed term** and out of the evaluation rows |
| `solve_started_at`, `solve_ended_at`, `solve_s`, `at_solve_end` | `timers_solve_started/ended`, called by `solver_handler.run` around the ladder | the solve phase, and the accumulators frozen at its exit |
| `output_path_s` | `write_output_files` | the output path's wall |

**What the harness adds** (`child.harvest_timers` before its audit; `child.stamp_timers`; `pool.run`):
`timers.driver` (the copy above), `timers.excluded` — `exit_audit_wall_s` and the audit's share of the
driver's own timers (`exit_audit_driver_sweep_s`, `_node_s`, `_n_sweeps`), `state_snapshots_s` (the hook's
wall, phase B), `record_assembly_s`, `harness_before_run_s` (the record's identity half before the tree
assertion imports PROCESS), `census_hooks_s` (**not timed**: null with a note) — `timers.epochs`
(`main_entry_at`, `run_started_at`, `run_returned_at`, `audit_started_at`, `audit_ended_at`,
`record_written_at`), and `launcher` (`spawned_at`, `returned_at`, `wall_s`, `loadavg_at_spawn`,
`loadavg_at_return`, `workers`). The tables add one more excluded number, `process_exit_s` =
`launcher.returned_at − record_written_at` (the interpreter's teardown, in the launcher's wall and in no
timer).

**The rows** (`harness/measurement/timing.py`; seconds; phase A ms per evaluation, phase B s per
optimisation): modules = Σ `node_s` (+ `tail_node_s`) over the group's nodes, the count tables' grouping
(`tally_evaluation.node_grouping`; PULSE and FF fold into Feedforward, the once-per-run group into
Post-processing); MDA convergence test = bind + read + residual + upstream; dispatch = `sweep_s` − Σ
`node_s`; objective and constraints = `objective_s`; optimiser own time = `solve_s` − `call_models_s` at
the solve's exit; **fixed per run** = (`first_call_models_at` − `launcher.spawned_at` −
`harness_before_run_s`) + (`run_returned_at` − `solve_ended_at` − the output path's own sweeps, objective
and test time, which the module rows hold as the count tables hold the output path's sweeps) +
`run_setup_s`; Total = `call_models_s` (phase A, the one evaluation) or `launcher.wall_s` − Σ excluded
(phase B); unattributed residual = Total − Σ rows. The breakdown table divides the convergence test and
dispatch by `n_sweeps`, the optimiser's time by the iterations summed over attempts, the modules by the
evaluations.

**Identity and contract.** `timers` is an *instrument switch* (`switches.INSTRUMENT_SWITCHES`): composed
into every arm of a campaign that asks for it, the reference arms included, and left out of every "which
architecture switches are set" check (the composition self-check's reference-arm rule). `Campaign.timers`
is off by default — the gates run without it, their records keep their identity — and `CAMPAIGN_TIMERS =
True` is composed by the campaign press; `Job.timers` is an identity field rendered only when on, and
the three record fields (`campaign_timers`, `timers`, `launcher`) are owed only by a record made with the
timers on (`records.fields_for(..., timers_on)`; a child stamp absent from a record means the default),
so no seeded record was re-made by the contract. G7's two smoke jobs are timed, its completeness check
gains "the timers were composed and harvested" and three field teeth (`timers`, `launcher`,
`campaign_timers` removed from a copy → refused by name).

## 7. DR12 — the driver change, in full (`24b78e2d`; the user reviews this on return)

Two files under `process/`: `process/core/caller.py` (+232/−12) and `process/core/solver/solver_handler.py`
(+3). Nothing under `process/models/` (G0 PASS; `copy_gates.py all` ALL GATES PASS at the commit).
`copy_gates.py` gains two `PermittedEdit` rows, `PROVENANCE.json` is regenerated, `CHANGES.md` gains
§4.5.18 and §4.6.2, `PROCESS_diff.py` its annotations and two summary addenda.

```diff
diff --git a/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/caller.py b/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/caller.py
index 6091c810..ecf7ccdd 100644
--- a/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/caller.py
+++ b/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/caller.py
@@ -5,6 +5,7 @@ from __future__ import annotations
 import json
 import logging
 import os
+import time
 from contextlib import contextmanager
 from pathlib import Path
 from typing import TYPE_CHECKING
@@ -592,6 +593,8 @@ def _defer_per_run_nodes(data) -> frozenset[str]:
     cached = _DEFER_PER_RUN_CACHE.get("nodes")
     if cached is not None:
         return cached
+    # DR12 (A101): the artifact's validation is once-per-run set-up.
+    _setup_t0 = time.perf_counter() if TIMERS is not None else None
 
     import hashlib  # noqa: PLC0415 - validation path only
 
@@ -702,6 +705,8 @@ def _defer_per_run_nodes(data) -> frozenset[str]:
             )
 
     resolved = frozenset(nodes)
+    if _setup_t0 is not None:
+        TIMERS["run_setup_s"] += time.perf_counter() - _setup_t0
     _DEFER_PER_RUN_CACHE["nodes"] = resolved
     DEFER_PER_RUN_TOTALS["nodes"] = sorted(resolved)
     DEFER_PER_RUN_TOTALS["validated"] = True
@@ -745,6 +750,125 @@ MDA_ENABLED: bool = module_solve.ENABLED
 #: changing no branch a result depends on.
 NODE_CALLS: list[int] = [0]
 
+# --------------------------------------------------------------------------
+# DR12 (task A101 (v5-timers-and-once); V5 list item 9; decision D33):
+# observation-only wall-clock timers.  Switch: ``PROCESS_ARCH_TIMERS``.
+#
+# ``on`` accumulates, per run, the wall clock (``time.perf_counter``) of:
+# every node call (per node, ``_node``; the flat per-call tail's direct
+# calls separately, ``_run_deferred_tail``), every sweep of the dispatch body
+# (``_call_models_once``), the block loops' convergence test (the
+# coupling-state bind, read and residual), upstream's own idempotence
+# comparison in the reference arms, the objective-and-constraints layer,
+# every ``call_models`` evaluation, the once-per-run resolution inside the
+# first evaluation (DR9's schedule, the artifacts' first load and the
+# per-run set's validation), the solve phase (``solver_handler``) and the
+# output path; plus the epochs (``time.time``) of the first evaluation, the
+# solve's boundaries and the last evaluation's end, so a launcher that
+# stamps its own spawn time can attribute the fixed per-run term.  The
+# harness reads the dictionary after the run, before its own audit sweep.
+#
+# Unset (the default): :data:`TIMERS` is ``None`` and every hook is one
+# ``is None`` test that takes no branch -- the block trace's precedent
+# (DR8); gate G1 compares the outputs byte for byte.  On, the timers touch no
+# float a result depends on and change no branch: gate GC compares every
+# count and every exit state with the timers on against the side without.
+# Wall clock is context, never evidence (D33; CLAUDE.md; I-10; trap T5).
+_TIMERS_VALUES: tuple[str, ...] = ("on",)
+TIMERS_NAME: str | None = os.environ.get("PROCESS_ARCH_TIMERS", "").strip() or None
+if TIMERS_NAME is not None and TIMERS_NAME not in _TIMERS_VALUES:
+    raise ArchitectureRefusal(
+        f"PROCESS_ARCH_TIMERS={TIMERS_NAME!r} is not a known value; expected "
+        f"one of {_TIMERS_VALUES} (or unset for no timers)."
+    )
+TIMERS_ENABLED: bool = TIMERS_NAME is not None
+
+
+def _new_timers() -> dict:
+    return {
+        "node_s": {},                 # per node: wall inside its run(), through _node
+        "node_n": {},                 # per node: calls timed
+        "tail_node_s": {},            # per node: the flat per-call tail's direct calls
+        "tail_node_n": {},
+        "sweep_s": 0.0,               # every _call_models_once body (the tokamak path)
+        "n_sweeps": 0,
+        "test_bind_s": 0.0,           # the coupling-state bind, once per call_models
+        "n_test_binds": 0,
+        "test_read_s": 0.0,           # the coupling-state reads of the block loops
+        "n_test_reads": 0,
+        "test_residual_s": 0.0,       # the block loops' residuals
+        "n_test_residuals": 0,
+        "upstream_test_s": 0.0,       # upstream's objf/conf comparison (reference arms)
+        "n_upstream_tests": 0,
+        "objective_s": 0.0,           # objective_function + constraint_eqns
+        "n_objective": 0,
+        "call_models_s": 0.0,         # every call_models, entry to exit
+        "n_call_models": 0,
+        "run_setup_s": 0.0,           # once-per-run resolution inside the first evaluation
+        "first_call_models_at": None, # epochs (time.time)
+        "last_call_models_ended_at": None,
+        "solve_started_at": None,
+        "solve_ended_at": None,
+        "solve_s": None,              # solver_handler.run: the ladder, entry to exit
+        "at_solve_end": None,         # the accumulators frozen at the solve's exit
+        "output_path_s": None,        # write_output_files, entry to exit
+    }
+
+
+#: The accumulators, or ``None`` with the switch unset.
+TIMERS: dict | None = _new_timers() if TIMERS_ENABLED else None
+
+
+def timers_solve_started() -> None:
+    """Stamp the solve phase's entry (called by ``solver_handler.run``)."""
+    if TIMERS is None:
+        return
+    TIMERS["solve_started_at"] = time.time()
+    TIMERS["_solve_t0"] = time.perf_counter()
+
+
+def timers_solve_ended() -> None:
+    """Stamp the solve phase's exit and freeze the accumulators there, so the
+    run's tail (output writing, the once-per-run set at the output path) can
+    be told apart from the solve (called by ``solver_handler.run``)."""
+    if TIMERS is None:
+        return
+    TIMERS["solve_ended_at"] = time.time()
+    TIMERS["solve_s"] = time.perf_counter() - TIMERS.pop("_solve_t0")
+    TIMERS["at_solve_end"] = {
+        "call_models_s": TIMERS["call_models_s"],
+        "n_call_models": TIMERS["n_call_models"],
+        "sweep_s": TIMERS["sweep_s"],
+        "n_sweeps": TIMERS["n_sweeps"],
+        "node_s": sum(TIMERS["node_s"].values()),
+        "tail_s": sum(TIMERS["tail_node_s"].values()),
+        "objective_s": TIMERS["objective_s"],
+        "test_s": (
+            TIMERS["test_bind_s"] + TIMERS["test_read_s"]
+            + TIMERS["test_residual_s"] + TIMERS["upstream_test_s"]
+        ),
+    }
+
+
+def _timed_objective(i_figure_merit: int, m: int, data) -> tuple[float, np.ndarray]:
+    """The objective and the constraint vector, timed when the timers are on.
+
+    One call site for the layer upstream's idempotence predicate compares,
+    so the timer is one function and not four copies of a stopwatch.  With
+    the timers off this is the two calls it always was.
+    """
+    if TIMERS is None:
+        objf = objective_function(i_figure_merit, data)
+        conf, _, _, _, _ = constraints.constraint_eqns(m, -1, data)
+        return objf, conf
+    t0 = time.perf_counter()
+    objf = objective_function(i_figure_merit, data)
+    conf, _, _, _, _ = constraints.constraint_eqns(m, -1, data)
+    TIMERS["objective_s"] += time.perf_counter() - t0
+    TIMERS["n_objective"] += 1
+    return objf, conf
+
+
 #: Sweeps of ``_call_models_once`` executed inside ONE ``call_models`` — that
 #: is, per optimiser-driven evaluation — binned over the run.
 #:
@@ -1309,6 +1433,9 @@ def resolve_schedule(
     hit = _SCHEDULE_CACHE.get(key)
     if hit is not None:
         return hit
+    # DR12 (A101): the once-per-run resolution is set-up, folded into the
+    # fixed per-run term (V5 plan section 6) and not into the evaluation.
+    _setup_t0 = time.perf_counter() if TIMERS is not None else None
     pre: list[str] = []
     post: list[str] = []
     inputs: dict = {}
@@ -1351,6 +1478,8 @@ def resolve_schedule(
             )
         inputs["node_map"] = {NODE_MAP_PATH.name: _sha256_of(NODE_MAP_PATH)}
     resolved = (tuple(pre), tuple(post), schedule, tail)
+    if _setup_t0 is not None:
+        TIMERS["run_setup_s"] += time.perf_counter() - _setup_t0
     _SCHEDULE_CACHE[key] = resolved
     SCHEDULE_RESOLUTION["n_resolutions"] += 1
     SCHEDULE_RESOLUTION["resolutions"].append(
@@ -1549,12 +1678,32 @@ class Caller:
             self._pending.append((name, run))
             return
         NODE_CALLS[0] += 1
+        # DR12 (A101): the node's own wall, per node, timers on only.
+        if TIMERS is None:
+            run()
+            return
+        t0 = time.perf_counter()
         run()
+        dt = time.perf_counter() - t0
+        node_s = TIMERS["node_s"]
+        node_s[name] = node_s.get(name, 0.0) + dt
+        node_n = TIMERS["node_n"]
+        node_n[name] = node_n.get(name, 0) + 1
 
     def _run_deferred_tail(self, pending: list) -> None:
         """Run the deferred feed-forward nodes, once, in sequence order."""
-        for _name, run in pending:
+        if TIMERS is None:
+            for _name, run in pending:
+                run()
+            return
+        # DR12 (A101): these calls are outside every sweep and outside
+        # NODE_CALLS (the harness's census counts them apart); timed apart.
+        for name, run in pending:
+            t0 = time.perf_counter()
             run()
+            dt = time.perf_counter() - t0
+            TIMERS["tail_node_s"][name] = TIMERS["tail_node_s"].get(name, 0.0) + dt
+            TIMERS["tail_node_n"][name] = TIMERS["tail_node_n"].get(name, 0) + 1
 
     def _execute_deferred_per_run_set_once(self, xc: np.ndarray) -> None:
         """Execute the per-run deferred set once, on the state as it stands.
@@ -1655,6 +1804,9 @@ class Caller:
             )
 
         if self._yspec is None:
+            # DR12 (A101): the artifacts' first load is once-per-run set-up,
+            # folded into the fixed per-run term and not into the evaluation.
+            _setup_t0 = time.perf_counter() if TIMERS is not None else None
             self._yspec, self._yprov = module_solve.load_spec()
             self._ysubsets, _ = module_solve.load_subsets(self._yspec)
             # DR11 (A100 (v5-test-set)): what each block loop TESTS.  The
@@ -1668,6 +1820,8 @@ class Caller:
                 self._ysubsets,
                 loop_key=f"{module_solve.MDA_MODE}/{subsolve.BURN_TIME_OWNER}",
             )
+            if _setup_t0 is not None:
+                TIMERS["run_setup_s"] += time.perf_counter() - _setup_t0
         spec = self._yspec
         subsets = self._ysubsets
         tests = self._ytests
@@ -1682,8 +1836,34 @@ class Caller:
         # Evaluated from the schedule that was actually built rather than from
         # the arm's name, so a run record says what the schedule was.
         single_block = _single_block_covers_loop(schedule, tail)
-        bound = spec.bind(self.data)
-        read = spec.read
+        # DR12 (A101): the convergence test's three pieces -- bind, read and
+        # residual -- timed apart; ``read`` and ``residual`` are the timed
+        # wrappers below when the timers are on, the bare methods otherwise.
+        if TIMERS is None:
+            bound = spec.bind(self.data)
+            read = spec.read
+            residual = spec.residual
+        else:
+            _t0 = time.perf_counter()
+            bound = spec.bind(self.data)
+            TIMERS["test_bind_s"] += time.perf_counter() - _t0
+            TIMERS["n_test_binds"] += 1
+            _read = spec.read
+            _residual = spec.residual
+
+            def read(b):
+                t0 = time.perf_counter()
+                out = _read(b)
+                TIMERS["test_read_s"] += time.perf_counter() - t0
+                TIMERS["n_test_reads"] += 1
+                return out
+
+            def residual(prev, cur, **kw):
+                t0 = time.perf_counter()
+                out = _residual(prev, cur, **kw)
+                TIMERS["test_residual_s"] += time.perf_counter() - t0
+                TIMERS["n_test_residuals"] += 1
+                return out
 
         # The block schedule never uses the per-call deferral's pending list:
         # under a block schedule the deferred tail is a block, run once at the
@@ -1789,7 +1969,7 @@ class Caller:
                 # picks the denominator; it does not change which components
                 # are compared, which is why COMPONENTS_COMPARED below is the
                 # free consistency check between the two.
-                res = spec.residual(
+                res = residual(
                     y_prev, y, subset=subset,
                     ruler=module_solve.PREDICATE_MODE,
                 )
@@ -1850,8 +2030,7 @@ class Caller:
 
         if _idf_probe.ENABLED:
             _idf_probe.objective_begin()
-        objf = objective_function(self.data.numerics.i_figure_merit, self.data)
-        conf, _, _, _, _ = constraints.constraint_eqns(m, -1, self.data)
+        objf, conf = _timed_objective(self.data.numerics.i_figure_merit, m, self.data)
         if _idf_probe.ENABLED:
             _idf_probe.objective_end()
 
@@ -1936,6 +2115,12 @@ class Caller:
         # I-17 instrument: sweeps taken by THIS evaluation, binned on exit by
         # every path (normal return, the VP4 early return, or a raise).
         _sweeps_at_entry = DISPATCH_SWEEPS[0]
+        # DR12 (A101): the evaluation's wall and the epochs of the first and
+        # the last, timers on only.
+        if TIMERS is not None:
+            if TIMERS["first_call_models_at"] is None:
+                TIMERS["first_call_models_at"] = time.time()
+            _eval_t0 = time.perf_counter()
         try:
             objf, conf = self._call_models_inner(xc, m)
             # V5 list item 5 (A101; D35): with the execution point at the
@@ -1949,6 +2134,10 @@ class Caller:
             _n = DISPATCH_SWEEPS[0] - _sweeps_at_entry
             _k = str(_n)
             SWEEPS_PER_EVAL_HIST[_k] = SWEEPS_PER_EVAL_HIST.get(_k, 0) + 1
+            if TIMERS is not None:
+                TIMERS["call_models_s"] += time.perf_counter() - _eval_t0
+                TIMERS["n_call_models"] += 1
+                TIMERS["last_call_models_ended_at"] = time.time()
 
     def _call_models_inner(self, xc: np.ndarray, m: int) -> tuple[float, np.ndarray]:
         """The body of :meth:`call_models`; see it for the contract.
@@ -2016,8 +2205,7 @@ class Caller:
             # Evaluate objective function and constraints
             if _idf_probe.ENABLED:
                 _idf_probe.objective_begin()
-            objf = objective_function(self.data.numerics.i_figure_merit, self.data)
-            conf, _, _, _, _ = constraints.constraint_eqns(m, -1, self.data)
+            objf, conf = _timed_objective(self.data.numerics.i_figure_merit, m, self.data)
             if _idf_probe.ENABLED:
                 _idf_probe.objective_end()
 
@@ -2037,10 +2225,17 @@ class Caller:
             # evaluation in the same order; what it buys is an exact width,
             # since the pair short-circuits and the constraint vector is not
             # compared when the objective has moved.
+            _test_t0 = time.perf_counter() if TIMERS is not None else None
             _objf_agrees = self.check_agreement(objf_prev, objf)
             UPSTREAM_PREDICATE_EVALUATIONS[0] += 1
             UPSTREAM_COMPONENTS_COMPARED[0] += 1 + (len(conf) if _objf_agrees else 0)
-            if _objf_agrees and self.check_agreement(conf_prev, conf):
+            _agrees = _objf_agrees and self.check_agreement(conf_prev, conf)
+            if _test_t0 is not None:
+                # DR12 (A101): upstream's own stopping test, the reference
+                # arms' convergence test, timed as the block loops' is.
+                TIMERS["upstream_test_s"] += time.perf_counter() - _test_t0
+                TIMERS["n_upstream_tests"] += 1
+            if _agrees:
                 # Idempotent: no longer changing, so return
                 logger.debug(
                     "Model evaluations idempotent, returning objective "
@@ -2064,11 +2259,8 @@ class Caller:
                         self._run_deferred_tail(pre)
                         if _idf_probe.ENABLED:
                             _idf_probe.objective_begin()
-                        objf = objective_function(
-                            self.data.numerics.i_figure_merit, self.data
-                        )
-                        conf, _, _, _, _ = constraints.constraint_eqns(
-                            m, -1, self.data
+                        objf, conf = _timed_objective(
+                            self.data.numerics.i_figure_merit, m, self.data
                         )
                         if _idf_probe.ENABLED:
                             _idf_probe.objective_end()
@@ -2248,6 +2440,10 @@ class Caller:
         """
         # I-17 instrument: one sweep of the dispatch body.  Integer only.
         DISPATCH_SWEEPS[0] += 1
+        # DR12 (A101): the sweep's wall, from here to the end of the tokamak
+        # path (the stellarator and IFE returns below are not timed: no
+        # configuration of this experiment takes them).
+        _sweep_t0 = time.perf_counter() if TIMERS is not None else None
 
         if _idf_probe.ENABLED:
             _idf_probe.sweep(self.models, self.data)
@@ -2412,6 +2608,10 @@ class Caller:
         if _idf_probe.ENABLED:
             _idf_probe.sweep_end()
 
+        if _sweep_t0 is not None:
+            TIMERS["sweep_s"] += time.perf_counter() - _sweep_t0
+            TIMERS["n_sweeps"] += 1
+
 
 def finalise(models, data, ifail: int, non_idempotent_msg: str | None = None):
     """Routine to print out the final point in the scan.
@@ -2537,6 +2737,8 @@ def write_output_files(
     if NODE_CALLS_AT_OUTPUT[0] is None:
         NODE_CALLS_AT_OUTPUT[0] = NODE_CALLS[0]
         DISPATCH_SWEEPS_AT_OUTPUT[0] = DISPATCH_SWEEPS[0]
+    # DR12 (A101): the output path's wall, entry to exit.
+    _output_t0 = time.perf_counter() if TIMERS is not None else None
     # A57: the exit audit's declared position (experiment plan section 3.3).
     # HERE -- at the entry, before the per-run deferred nodes below and before
     # any output-time sweep -- is the state the solve handed over, and it is
@@ -2582,3 +2784,5 @@ def write_output_files(
         xc=x,
         ifail=ifail,
     )
+    if _output_t0 is not None:
+        TIMERS["output_path_s"] = time.perf_counter() - _output_t0
diff --git a/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/solver/solver_handler.py b/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/solver/solver_handler.py
index 31402bd0..f277acf6 100644
--- a/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/solver/solver_handler.py
+++ b/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/solver/solver_handler.py
@@ -97,6 +97,8 @@ class SolverHandler:
         # append to a list; the ladder -- which attempts run, in which order,
         # under which settings -- is exactly what it was.
         caller.open_ladder()
+        # DR12 (A101): the solve phase's boundaries, timers on only.
+        caller.timers_solve_started()
         with caller.attempt(LADDER_STAGES[0]):
             ifail = self.solver.solve()
 
@@ -134,6 +136,7 @@ class SolverHandler:
                 with caller.attempt(LADDER_STAGES[3]):
                     ifail = self.solver.solve()
 
+        caller.timers_solve_ended()
         self.output()
         return ifail
```

## 8. DR12's straddles, G7, G5 and the self-check

### 8.1 G1 (`switch_neutrality`), `9ed0da4c → 24b78e2d`

The `before` side captured at `9ed0da4c` (the retirement commit; the driver is item 5's, byte for byte),
the `after` side at `24b78e2d`; every switch unset (the timers included), `AR` and `BR` on the three
configurations, W = 3. **PASS** (`A101_press11_G1_DR12_compare.log`): 6 pairs, 3 669 deterministic
record values compared, **0 differing**, 769 excluded by name (666 before DR12: the new `timers` and
`campaign_timers` leaves are conditional — null / False on the after side, absent on the before — and
`launcher` is always excluded by kind, "a timing or the machine's state"); 51 319 output-file lines,
**0 differing**; 9/9 teeth. With every switch unset the driver is byte-identical across DR12: every hook
is one `is None` test. The item-5 straddle's captures are archived under
`switch_neutrality/straddles/c161500c__cfa0d3ff/`. *One blemish, disclosed:* the after side and every
run of the chain that followed it were made with one tracked file modified — `harness/README.md`, its
§18 appended after the chain had been launched — so those records read `tree_git_dirty = true` on a
documentation file; no code differed from `24b78e2d`.

### 8.2 GC (`count_neutrality`), `item5 → DR12`, the DR12 side **with the timers on**

`STRADDLE = ("item5", "DR12")`, both sides under `write_set`; the DR12 side made at `24b78e2d` with
`PROCESS_ARCH_TIMERS=on` by declaration (`STRADDLE_TIMERS`), 22 labelled jobs; the count rule
`identical`, the prime rule `identical`; `NOT_COUNTS_BY_KIND` names `timers`, `launcher` and
`campaign_timers` out of the count paths by kind (checked at import). **First press
(`A101_press12_GC_item5_DR12.log`): the criterion held and one tooth did not trip** — 22 pairs, 3 989
count leaves under 41 paths, **0 differing**; 33 prime checks, 0 failing; 46 125 coupling-state
components, **0 differing** — so the instrument moves no count and no bit of any exit state; the new
tooth "a per-run node counted twice" DID NOT TRIP because it doctored a fresh dictionary where the
optimisation-phase record keeps its census under `per_node_counted`, not `counted`. Fixed at `d8873d49`
(the tooth doctors the record's own census dictionary on an evaluation-phase row) and re-pressed with
`--resume` (both sides kept; `A101_press21_GC_DR12_repress.log`): **PASS**, 22 pairs, 3 989 count
leaves 0 differing, 33 prime checks 0 failing, 46 125 components 0 differing, **4/4 teeth** (the
per-run-node tooth now doctors `vacuum` 1 → 2 on `A/A2/st_regression`'s census: the one differing leaf).
Record `count_neutrality/straddles/item5__DR12.json`; the item-5 straddle's record beside it.

### 8.3 G7 (`record_completeness`), with the timer fields

G7's two smoke jobs are timed. First press (`A101_press13_G7.log`): 95 declared fields in the
optimisation phase and 88 in the evaluation phase, every one carried, "the timers were composed and
harvested" true on both; the teeth `timers` removed and `launcher` removed tripped; **`campaign_timers`
removed did not** — removing the stamp removed the witness that makes the fields owed. Fixed at
`d8873d49`: the contract owes the timer fields when the record stamps them composed *or* carries a
harvested timers block. Re-pressed with `--resume` (`A101_press22_G7_repress.log`): **PASS**, 183
compared, 0 mismatched, **12/12 teeth** (the three timer fields removed each refused by name).

### 8.4 G5 (`switch_composition`)

First press (`A101_press14_G5.log`): **FAIL** on `resolved_switches` alone (every count, hex float and
sweep identical): the switch-by-switch run gained the two new switch names in its `override_env`
(`PROCESS_ARCH_DEFER_PER_RUN_EXECUTION` and `PROCESS_ARCH_TIMERS`, both unset) and so a new identity
and was re-made at `24b78e2d`, while the matrix-composed run was kept from `bf395541` — a record of a
driver without the new read-backs. The gate compares the two runs' `resolved_switches` blocks whole, so
the pair has to be made at one driver: re-pressed **without** `--resume` (both runs re-made at
`d8873d49`; `A101_press20_G5_remade.log`): **PASS**, 156 compared (42 switch names and 10 run values per
configuration), 0 differing, 4/4 teeth.

### 8.5 The self-check

First press (`A101_press15_selfcheck.log`): `run path` FAIL — `Job.identity` rendered without a campaign
refused on an unresolved `timers` ("B2 no longer composes"), and five refusal teeth tripped for that
wrong reason. Fixed at `d8873d49`: an unresolved `timers` renders as off (the default every record
carries), never as a refusal. Re-pressed at `d8873d49` (`A101_press23_selfcheck.log`): **PASS** on every
check; the capability probe resolves every read-back the registry names on the tree under test,
`TIMERS` included.

### 8.6 `resume_identity`, found by `--gate all`

The first `--gate all --resume` at `d8873d49` (`A101_press24_gate_all.log`) stopped at `resume_identity`:
**FAIL, 2 of 11 teeth** — nine teeth raised `KeyError: 'timers'`, because the gate's synthetic complete
record copies every child-stamped identity field from the rendered identity, and `timers` is rendered
only when on. Fixed at `b9b134d9` (an absent field stamps its default) and re-pressed: **PASS**, 549 compared,
0 mismatched, 11/11 teeth. The gate had PASSed 12/12 at `9ed0da4c`, before `timers` became an identity
field; the tooth I added at the prep commit was among the nine, which is how it was noticed.

## 9. The timing stages on the gate job set (the smoke), the residual and the timers-off cost

All at `24b78e2d`, W = 1, children single-threaded; the job set is GC's (both phases, every arm active
on each configuration, the evaluation phase from the displaced entry at seed 1, the optimisation phase
from seed 0), records `timing` under `runs/timing/`. Load average 2.2 → 1.1 across the stage (one heavy
slot; the orchestrator's sessions were idle). **Context, never evidence**: no verdict reads a number
here; the counts of every repetition were identical (the refusal is real: `COUNT_FIELDS` compares
status, the node-call totals, the sweep totals, the evaluation count, the iterations and the objective
and audit hex floats).

**Repeatability** (`--timing repeatability`, `A101_press16_timing_repeatability.log`; record
`runs/timing/repeatability/measurements.json`): 22 jobs × 3 repetitions = 66 runs, **0 refused**.

**Table 9.1 — Total per job, median [min, max] over 3 repetitions** (phase A ms per evaluation; phase B s
per optimisation), the unattributed residual's median beside as a share of Total.

| job | Total med [min, max] | residual (share) | MDA test | dispatch | optimiser own | fixed per run |
|---|---|---|---|---|---|---|
| A/AR nof | 332.40 [323.50, 332.99] ms | 0.16 ms (0.05 %) | 0.21 ms | 0.59 ms | — | — |
| A/A0 nof | 346.09 [340.92, 348.13] ms | 0.22 (0.06 %) | 4.64 | 0.80 | — | — |
| A/A1 nof | 344.15 [343.90, 346.19] ms | 0.22 (0.06 %) | 4.56 | 0.77 | — | — |
| A/A2 nof | 351.04 [347.28, 352.80] ms | 0.41 (0.12 %) | 5.72 | 1.26 | — | — |
| B/BR nof | 17.92 [17.86, 17.96] s | 0.02 s (0.12 %) | 0.07 s | 0.18 s | 0.13 s | 4.28 s |
| B/B0 nof | 20.10 [20.01, 20.74] s | 0.06 (0.28 %) | 1.48 | 0.21 | 0.13 | 4.34 |
| B/B1 nof | 19.41 [19.24, 19.42] s | 0.06 (0.30 %) | 1.44 | 0.21 | 0.14 | 3.94 |
| B/B2 nof | 16.09 [16.07, 16.09] s | 0.09 (0.54 %) | 1.92 | 0.38 | 0.07 | 3.85 |
| A/AR lad | 327.37 [326.46, 332.28] ms | 0.16 (0.05 %) | 0.15 | 0.58 | — | — |
| A/A0 lad | 343.53 [332.49, 349.12] ms | 0.20 (0.06 %) | 3.41 | 0.58 | — | — |
| A/A1 lad | 337.04 [334.32, 347.66] ms | 0.20 (0.06 %) | 3.49 | 0.61 | — | — |
| A/A2 lad | 345.81 [344.81, 398.30] ms | 0.38 (0.11 %) | 4.84 | 1.08 | — | — |
| B/BR lad | 33.56 [33.31, 33.80] s | 0.07 (0.21 %) | 0.14 | 0.37 | 0.20 | 4.35 |
| B/B0 lad | 35.59 [35.58, 36.10] s | 0.13 (0.38 %) | 2.91 | 0.40 | 0.20 | 4.38 |
| B/B1 lad | 28.34 [28.10, 28.53] s | 0.10 (0.36 %) | 2.27 | 0.32 | 0.18 | 3.87 |
| B/B2 lad | 23.25 [23.07, 23.37] s | 0.22 (0.93 %) | 3.08 | 0.59 | 0.11 | 3.87 |
| A/AR st | 259.25 [254.85, 305.59] ms | 0.15 (0.06 %) | 0.15 | 0.48 | — | — |
| A/A0 st | 274.04 [271.97, 274.31] ms | 0.22 (0.08 %) | 3.80 | 0.63 | — | — |
| A/A2 st | 278.46 [275.07, 285.07] ms | 0.41 (0.15 %) | 5.34 | 1.10 | — | — |
| B/BR st | 17.54 [17.12, 17.84] s | 0.02 (0.10 %) | 0.05 | 0.14 | 0.08 | 4.47 |
| B/B0 st | 18.28 [18.20, 18.29] s | 0.05 (0.26 %) | 1.20 | 0.16 | 0.08 | 4.36 |
| B/B2 st | 45.97 [45.86, 46.20] s | 0.35 (0.76 %) | 6.48 | 1.20 | 0.31 | 3.90 |

**The residual is small**: 0.05–0.15 % of an evaluation's wall in phase A, 0.10–0.93 % of an
optimisation's in phase B (largest on the partitioned arms, whose per-evaluation bookkeeping outside
sweeps and tests — the schedule loop, the counters, `_module_stats` — is the most of any arm). It is
what the driver does inside `call_models` outside every sweep, test and objective evaluation, plus the
census wrappers around `_node` and `call_models` (§13).

**Two readings, context only.** (i) In phase B the flat arms' ranges are tight (`B0` nof 20.01–20.74 s
over three repetitions, `B2` nof 16.07–16.09 s); the `B2/B0` Total ratio of the means is **0.79** on nof
(med 0.80 [0.78, 0.80]), **0.65** on lad (0.65 [0.64, 0.66]) and **2.52** on st (2.53 [2.51, 2.53]). The stages
ran under the campaign's declared setting, the census set at τ = 1e-8 (the counts are A100's census
pair's: `B0` nof 45 465 and `B2` nof 22 944 solve-phase node calls, 630 and 660 evaluations), and st is
the configuration where that set lengthens the partitioned arm's path (A96; plan §3): here `B2` st
took 2 370 evaluations and 40 iterations against `B0`'s 570 and 10, so its wall ratio folds a 4.2×
longer path in. On nof the whole-run node-call ratio `B2/B0` is 0.50 (22 944 / 45 465) where the
model-time ratio is 0.70 (§10) — the modules' costs are not uniform, which is the paper's argument. (ii) The fixed per-run term is 3.9–4.5 s on
every arm — the interpreter, PROCESS's import, numba's cache load and the input parse — 20–24 % of a
nof optimisation and the whole of the difference between an evaluation-phase run's 4.4 s launcher wall
and its 0.3 s evaluation.

**Phase A's Total is a first-evaluation-in-process figure** (259–351 ms; §13): numba loads each
jitted function's cache inside the first call of every node, so M1 reads 167–182 ms and M2 147–168 ms
in every arm, against 3 ms per warmed sweep in A91. The arms are comparable with each other (each pays
the same load; `A2/A1` Total 1.02 on nof, 1.07 on lad, `A2/A0` 1.02 on st), and the MDA-test, dispatch
and objective rows are warm-comparable (the test 4.6 ms on `A0`/`A1` nof against 5.7 ms on `A2`,
dispatch 0.8 against 1.3 ms; the reference arm's test 0.2 ms), but the module rows are not the plan's
per-evaluation model time until a warm-up is added to the evaluation child.

**Timers off** (`--timing timers-off`, `A101_press17_timing_timers_off.log`; record
`runs/timing/timers_off/measurements.json`): 22 runs, timers unset, every count identical to the timed
repetitions' (`COUNT_FIELDS`). The instrument's own cost, read as the launcher's wall on against the
timed repetitions' median: **−4.4 % to +4.4 %**, median −1.3 %, positive on 5 of 22 jobs — the sign is
as often wrong as right, so the cost is below this machine's run-to-run noise (T5: identical code moved
a block's median by 2× in A91); the largest reading is `B2` st +1.91 s of 44.6 s. Per node the timed
path costs two `perf_counter` calls and two dictionary updates (~0.5 µs) per call: on `B2` nof's 22 944
solve-phase node calls that is ~10 ms of a 16 s run.

**Validity** (`--timing validity`, `A101_press18_timing_validity.log`): 22 jobs, every one "no campaign
record: the check waits for the campaign"; `appendix_timings_from: not decidable yet`. The stage is
wired and reads the campaign's directories by the chain's layout; it is exercised on a campaign timing
by the campaign task.

## 10. The three appendix tables, smoked on the timing records

`--timing tables` (`A101_press19_timing_tables.log`) rendered the three tables over the 66 repeatability
records into `runs/timing/tables/wall_clock_tables_from_timing_records.md` (133 lines; **test data**,
header "Never the paper's document"; never committed, never through `--paper-tables`). `paper_tables.py`
renders the same rows from the campaign populations through `timing.tables_over` (`wall_clock`,
`_wall_clock_lines`); `--paper-tables check` still refuses as A100 left it — no campaign record (§11).
The node grouping is the count tables' (`tally_evaluation.node_grouping`): 0 ungrouped nodes on every
table.

**Table 10.1 — `large_tokamak_nof`, phase B in wall clock, s per optimisation** (from the smoke file;
means over 3 repetitions, ratio of the means and the per-repetition median with [min, max]; W = 1;
exclusions as named in §6).

| row | BR | B0 | B1 | B2 | B2/B0 | med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 5.76 | 6.18 | 6.02 | 3.51 | 0.57 | 0.58 [0.55, 0.58] |
| M2 | 5.71 | 6.17 | 5.97 | 5.46 | 0.89 | 0.90 [0.86, 0.90] |
| M3 | 1.15 | 1.21 | 1.17 | 0.68 | 0.56 | 0.57 [0.54, 0.57] |
| Feedforward | 0.01 | 0.01 | 0.01 | 0.00 | 0.32 | 0.33 [0.31, 0.34] |
| Post-processing | 0.32 | 0.33 | 0.32 | 0.00 | 0.00 | 0.00 [0.00, 0.00] |
| MDA convergence test | 0.07 | 1.50 | 1.44 | 1.92 | 1.28 | 1.29 [1.25, 1.30] |
| dispatch | 0.18 | 0.21 | 0.21 | 0.38 | 1.82 | 1.86 [1.76, 1.87] |
| objective and constraints | 0.27 | 0.10 | 0.10 | 0.10 | 1.01 | 1.02 [0.98, 1.03] |
| optimiser own time | 0.13 | 0.14 | 0.14 | 0.07 | 0.51 | 0.52 [0.48, 0.54] |
| fixed per run | 4.31 | 4.38 | 3.92 | 3.86 | 0.88 | 0.88 [0.88, 0.89] |
| unattributed residual | 0.01 | 0.06 | 0.06 | 0.09 | 1.50 | 1.58 [1.36, 1.59] |
| Total | 17.92 | 20.28 | 19.35 | 16.08 | 0.79 | 0.80 [0.78, 0.80] |

**Table 10.2 — `large_tokamak_nof`, cost breakdown, phase B** (s per optimisation · the per-unit figure ·
share of Total).

| row | BR | B0 | B1 | B2 |
|---|---|---|---|---|
| model evaluation (the modules summed) | 12.94 · 20.55 ms/eval · 72.2 % | 13.90 · 22.07 · 68.5 % | 13.49 · 20.44 · 69.7 % | 9.66 · 14.63 · 60.1 % |
| MDA overhead per sweep: convergence test | 0.07 · 0.03 ms/sweep · 0.4 % | 1.50 · 0.69 · 7.4 % | 1.44 · 0.68 · 7.4 % | 1.92 · 0.39 · 12.0 % |
| MDA overhead per sweep: dispatch | 0.18 · 0.09 ms/sweep · 1.0 % | 0.21 · 0.10 · 1.0 % | 0.21 · 0.10 · 1.1 % | 0.38 · 0.08 · 2.4 % |
| optimiser overhead per iteration | 0.13 · 16.4 ms/iter · 0.7 % | 0.14 · 17.1 · 0.7 % | 0.14 · 17.0 · 0.7 % | 0.07 · 8.8 · 0.4 % |
| fixed per run | 4.31 · 4.31 s · 24.1 % | 4.38 · 4.38 · 21.6 % | 3.92 · 3.92 · 20.2 % | 3.86 · 3.86 · 24.0 % |
| Total | 17.92 · 28.4 ms/eval · 100 % | 20.28 · 32.2 · 100 % | 19.35 · 29.3 · 100 % | 16.08 · 24.4 · 100 % |

The smoke's reading, context only: the partitioned arm's model time is 0.70 of the flat control's on
nof (9.66 / 13.90 s) where its whole-run node-call ratio is 0.50 (22 944 / 45 465; the census set at
1e-8) — the modules' cost is not uniform, which is the paper's argument; its convergence test costs 0.39 ms per sweep against the flat
control's 0.69 (a narrower test) but is run 2.6× as often, so the row totals 1.92 against 1.50 s; the
dispatch row is 0.08–0.10 ms per sweep in every arm; the optimiser's own time halves with the shorter
path. The phase A tables are in the smoke file too (§9's caveat on the module rows).

## 11. The gate table after, the stamp survey and the paper-tables check

`--gate all --resume` at `b9b134d9` (`A101_press28_gate_all.log`; it ran through, re-making one record —
G7's tooth "a stale run is re-made without resume" re-makes its own smoke evaluation, by design) and
`--measure gate_table --resume` (`A101_press29_gate_table.log`; record `runs/gates/gate_table/measurements.json`).

**Table 11.1 — the gate table after DR12.** *One row per registered gate: the verdict on the criterion
and every tooth, what it compared, how many differed, teeth tripped of declared, the commit of the
verdict. Population: the 28 registered gates (29 at `ca7200ff`; G4 retired).*

| gate | plan | verdict | compared | mismatched | teeth | verdict at |
|---|---|---|---|---|---|---|
| `g0prime` | G0 | PASS | 77 | 1 (the approved `pulse.py`) | 4/4 | `b9b134d9` |
| `copy_identity` | — | PASS | 224 | 8 (the permitted-edit files; `caller.py` and `solver_handler.py` carry this task's rows) | 12/12 | `b9b134d9` |
| `edit_behaviour` | — | PASS | 3 | 0 | 1/1 | `b9b134d9` |
| `self_containment` | — | PASS | 55 | 0 | 1/1 | `b9b134d9` |
| `composition` | — | PASS | 42 | 0 | 7/7 | `b9b134d9` |
| `rungs` | — | PASS | 98 | 0 | 3/3 | `b9b134d9` |
| `provenance` | — | PASS | 4 | 0 | 4/4 | `b9b134d9` |
| `data` | — | PASS | 22 | 0 | 6/6 | `b9b134d9` |
| `run_path` | — | PASS | 12 | 0 | 12/12 | `b9b134d9` |
| `resume_identity` | — | PASS | 549 | 0 | 11/11 (the composed-terms tooth added; §8.6) | `b9b134d9` |
| `capability` | — | PASS | 61 | 0 | 5/5 (58 → 61: `defer_per_run_execution`, `timers`, the `TIMERS` read-back) | `b9b134d9` |
| `artifacts_check` | — | PASS | 119 | 0 | 3/3 | `b9b134d9` |
| `artifacts_derive_inputs` | — | PASS | 2 | 0 | 4/4 | `b9b134d9` |
| `artifacts_census` | — | PASS | 81 | 0 | 5/5 | `b9b134d9` |
| `artifacts_per_run` | — | PASS | 16 | 0 | 2/2 | `b9b134d9` |
| `record_completeness` | G7 | PASS | 183 | 0 | 12/12 (95 / 88 declared fields; the timer fields; §8.3) | `b9b134d9` |
| `count_neutrality` | GC | PASS | 50 114 (3 989 + 46 125) | 0 | 4/4 (**the `item5 → DR12` straddle**, the after side timed; §8.2) | `b9b134d9` |
| `prime_map` | G2 | PASS | 17 591 | 0 | 3/3 (§4.4) | `b9b134d9` |
| `entry_and_warm` | G6 | PASS | 6 717 | 0 | 3/3 (§4.4) | `b9b134d9` |
| `test_set` | GT | PASS | 13 424 | 794 (the three biting drops; §4.4) | 4/4 | `b9b134d9` |
| `switch_composition` | G5 | PASS | 156 | 0 | 4/4 (§8.4) | `b9b134d9` |
| `switch_neutrality` | G1 | PASS | 54 988 (3 669 + 51 319) | 0 | 9/9 (**the DR12 straddle `9ed0da4c → 24b78e2d`**; §8.1) | `b9b134d9` |
| `reproduction` | GR | PASS (read of the `d6c246a1` verdict) | 256 | 0 | 8/8 | `b9b134d9` |
| `output_path` | G9 | PASS | 3 879 | 0 | 4/4 | `b9b134d9` |
| `written_file_gap` | — | PASS | 42 | 0 | 4/4 | `b9b134d9` |
| `tally_contracts` | — | **FAIL** | 575 (339 + 236) | 40 | 16/17 | `b9b134d9` |
| `run_kind_separation` | — | PASS | 194 | 0 | 7/7 | `66bfa240` (resumed) |
| `stage_provenance` | — | PASS | 11 | 0 | 5/5 | `a0de2e13` (resumed) |
| ~~`audit_restriction`~~ | G4 | retired (§5); last verdict FAIL at `0353c524`, kept | — | — | — | — |

**`tally_contracts`' FAIL is I-35's, inherited**: 236/236 reference cells, 20 of 20 runs reproduced;
the 40 mismatches are the two tally stages' population lines on GR's read-only records (missing
`campaign_test_set`, `loop_test_sets`, `schedule_resolution` under the current contract) and the
fixed-point tooth that cannot trip over the gate population — exactly A100's count. Not fixed here (the
brief: report, do not fix).

**The stamp survey** (`run_stamp_survey.py --json runs/_press_logs/A101_stamp_survey_final.json`,
`A101_press31_stamp_survey.log`): 509 run records under `runs/`; by commit, the records this task made —
123 at `24b78e2d` (29 pool: GC's timed DR12 side and the entry references; G1's after capture; the 88
timing records), 22 at `cfa0d3ff` (GC's item-5 side), 15 at `0353c524` (G4's re-made baselines and
doctorings), 15 at `9ed0da4c` (G6's, GT's and G2's re-made `A2` records), 6 at `d8873d49` (G5's two runs
per configuration), 1 at `b9b134d9` (G7's tooth), 6 captures at `c161500c` and 6 at `9ed0da4c` (G1's
before sides); the rest are the seeded tree's (`d6c246a1` … `c4aa37b6`), kept. No record carries a
`tree_git_head` this task did not make or inherit; the records made during the DR12 chain read
`tree_git_dirty = true` on `harness/README.md` alone (§8.1). Two development smoke directories under
`runs/single/` (made with the driver change uncommitted, before each commit) were deleted before the
copy; no number in this report came from them.

**`--paper-tables check`** (`A101_press30_paper_tables_check.log`): REFUSED, exit 3 — "no campaign record
under `runs/`; the paper's tables are over the campaign and are not filled from gate runs", as A100 left
it. The wall-clock tables render through the same code the `--timing tables` smoke exercised (§10).

## 12. Autonomous decisions, each with its reversal path

Everything below is **autonomous** (D37); nothing was put to the orchestrator during the task.

1. **Item 5's execution point is a switch, `PROCESS_ARCH_DEFER_PER_RUN_EXECUTION`, composed by the
   harness for a deferring arm of phase A** — not a phase the driver knows (it never knows one) and not
   a matrix row (it follows from the phase and the deferral; the paper's matrix stands). The brief left
   the choice open ("a switch, or the phase the harness already composes"). *Reversal:* compose it from
   a phase term instead; the driver side is unchanged.
2. **The execution runs inside `call_models`, after the objective and constraints, inside the
   evaluation's sweep histogram**, through `self._sweep_block` with the exclusion lifted on the same
   `Caller` (the output path uses a fresh `Caller`; a fresh one here would re-apply the burn-time
   constant on every evaluation — bit-identical, but a write for nothing). *Reversal:* a fresh `Caller`
   as at the output path.
3. **The dispatch sweep the execution costs is declared, not hidden** (§4.2): GC's rule predicts
   `dispatch_sweeps` and `n_model_calls_sweeps` + 1 and the histogram's shift; the brief's "nothing
   else" was written before the mechanism was chosen. *Reversal:* a variant of `_call_models_once` that
   does not count when it runs the set — a second code path for one sweep, which is why it was not done.
4. **GC compares a prediction** (`predict_under_rule`) rather than excluding the declared leaves: an
   undeclared move is a mismatch, and the declared ones are checked to their value (the census 1, the
   totals + n, `executed_once_at_node_calls` = the before side's total). *Reversal:* exclude the declared
   leaves by name, as G1's tables do; the values would then be unchecked.
5. **The prep rule re-makes on the composed term names, never on values** (§4.3), so a seeded record
   from another tree (paths differ, T20) is kept. *Reversal:* put the composed terms into the job
   identity; every seeded record would then be re-made once.
6. **The restricted statistic stays in the record and leaves the tables**: `exit_audit.restricted` is
   still computed (cheap; G1's and GC's declared leaves name it; the per-namespace tally table and the
   fixed-point distance's restriction, plan §5 A2 / I-35's tooth, still read it), while the
   matched-accuracy constructions and the paper's A1 read the whole state (D36; the brief's "the
   restricted audit retired"). The fixed-point distance keeps A76's restriction — plan §5 A2 names A76's
   statistic and no ruling moved it; with item 5 the whole-state distance beside it is now meaningful,
   and dropping the restriction there is a later change with I-35's tooth to re-form. *Reversal:* drop
   the restricted block from the audit (`child.restricted_audit`) — G1's, GC's and the tally's readers of
   it go with it.
7. **G4's last verdict is kept on disk, the module deleted**, and the three `resume_identity` pairs that
   read it are replaced by equivalents (§5). *Reversal:* restore `gate_audit.py` from `0353c524`.
8. **The timers are an instrument switch composed into the reference arms too** (`INSTRUMENT_SWITCHES`):
   the campaign's tables need `AR`/`BR` timed, and the composition self-check's "every switch cleared"
   rule for the reference arm reads the architecture switches only. *Reversal:* keep the reference arms
   untimed; their appendix columns would then be empty.
9. **The timers are off for every gate and on for the campaign press** (`Campaign.timers = False`,
   `CAMPAIGN_TIMERS = True`), and the identity renders `timers` only when on, so no seeded gate record
   changed digest; the three record fields are owed only with the timers on (`when == "timers"`), so no
   seeded record was re-made by the contract. G7 times its own smoke jobs so its field teeth bite; GC's
   DR12 side is timed by declaration so count-neutrality is shown *with* the instrument. *Reversal:*
   make the fields always-owed (every pool record re-made once) and `timers` always rendered.
10. **The objective layer is timed through one helper (`_timed_objective`) at the four sites** — the
    same two calls in the same order, so the default path's floats are unchanged (G1). *Reversal:* four
    inline stopwatches.
11. **The once-per-run set-up is folded into the fixed term** by timing the cache-miss paths
    themselves (`resolve_schedule`, the per-run artifact's validation, the artifacts' first load), not
    the memoised calls. *Reversal:* leave it inside the first evaluation's rows.
12. **The run's "start" for the fixed term is the child's tree assertion** (which imports PROCESS): the
    record's identity half before it is the harness's set-up and excluded by name; the interpreter's own
    start and the harness modules' imports before `main` are inside the fixed term (spawn to
    `main_entry_at`). A development run before the commit had the epoch after the import and read
    PROCESS's ~2.7 s import as "harness set-up" — moved before committing; that run was deleted.
    *Reversal:* none sensible.
13. **`process_exit_s` is derived by the tables from the two epochs** and named as an excluded cost
    rather than left in the residual (a development run before the commit read a residual of 0.96 s of
    50.9 on `B2` st with the exit unnamed; the committed stage reads 0.35 s of 46.0, §9). *Reversal:*
    leave it in the residual.
14. **The repeatability job set is GC's job set** (both phases, every arm, one seed per configuration:
    22 jobs × 3 = 66 runs at W = 1), not one job per configuration: the validity check compares per job
    and the plan's budget line ("9") under-counted what "every arm" needs. *Reversal:* one arm per
    configuration.
15. **The repetition index travels in `override_env`** (`HARNESS_TIMING_REPETITION`, GC's label
    mechanism), so three repetitions are three identities and three directories under `runs/timing/`;
    the run kind `timing` is new and never pooled with the campaign. *Reversal:* three named directories
    with one identity — the pool's `_MADE_THIS_INVOCATION` would then serve the first to the others.
16. **The `tables` stage writes its rendering under `runs/timing/`, never through `--paper-tables`**:
    the generator refuses without a campaign (as A100 left it) and its cross-check is against the
    tally's stage records, which the timing records are not in. The same `timing.tables_over` renders
    both. *Reversal:* a `--paper-tables-population timing` switch on the generator with the cross-check
    skipped.
17. **A phase A record's timing is a first-evaluation-in-process figure** (numba's per-process cache
    load lands inside the first call of every jitted function): no warm-up evaluation was added to
    `evaluate.py`, because a warm-up would be a second evaluation in the measured process and the
    census, the entry state and the audit are built around exactly one. Reported as a limit (§13) with
    the repeatability stage's numbers. *Reversal:* A91's form — a warm-up evaluation discarded, the snapshot re-entered, a fresh
    `Caller` — as a harness change to the evaluation child with its own G1 capture.

## 13. Limits

- **No conclusion rests on a timing** (CLAUDE.md; D33). Every wall-clock number in this report is
  context with its repetition count; the acceptance quantities are the counts and bit-comparisons of
  §4, §5 and §8.
- **Phase A's per-evaluation wall is a cold-process figure.** The evaluation child runs one
  `call_models` in a fresh process; numba loads each jitted function's cache at its first call, inside
  the node's own timer. The repeatability stage reads 259–351 ms for the one evaluation of every
  phase A arm against 21–32 ms per evaluation inside the optimisations (Table 10.2: `B2` nof 24.4,
  `B0` nof 32.2 ms per evaluation of Total). The phase A appendix table is
  therefore a table of first evaluations, comparable between arms (every arm pays the same load) and not
  with the phase B per-evaluation figure; A91's warmed instrument (a discarded warm-up, the snapshot
  re-entered) is the remedy, a harness change to the evaluation child (§12, decision 17).
- **The node-census wrapper and the timers' own `perf_counter` calls are inside the dispatch row**:
  `install_node_census` wraps `_node` from outside the node's timer, so its per-call dictionary
  increment lands in the sweep's wall less the nodes; the timers-off stage measures the whole instrument's
  cost (§9) but not that split.
- **The census hooks are not timed** (`census_hooks_s` null): the read-before-write census runs only
  under the census stage, never in a campaign record.
- **The stellarator and IFE returns of `_call_models_once` are not timed**: no configuration takes them.
- **The residual is a number, not an explanation**: on the gate job set it is 0.05–0.15 % of an
  evaluation's wall and 0.10–0.93 % of an optimisation's (§9); what it holds is
  the per-evaluation bookkeeping of `_call_models_partitioned` outside sweeps and tests (the schedule
  loop, the counters, `_module_stats`), the evaluator's own work around `call_models`, and the census
  wrappers.
- **The validity check waits for the campaign**: with no campaign record every row reads "no campaign
  record"; the stage is wired, not exercised on a campaign timing.
- **`tally_contracts` FAILs as inherited** (I-35: the two tally stages' population lines on GR's
  read-only records) — reported, not fixed.
- **`PROCESS_diff.py` exits 1 as inherited** (I-34: A90's four `evaluators.py` hunks unclaimed);
  every hunk of this task's two changes is claimed.

## 14. Harness files changed

Under `PROCESS/`: `process/core/caller.py` (§3, §7), `process/core/solver/solver_handler.py` (§7);
`copy_gates.py` (three `PermittedEdit` rows), `PROVENANCE.json` (regenerated twice), `CHANGES.md`
(§4.5.17, §4.5.18, §4.6.2). Nothing under `process/models/`, nothing under
`MDA_partitioning_experiment_v4/` or any sibling clone.

| file | change |
|---|---|
| `harness/core/pool.py` | `why_not_composed_as_today` and its use in `_kept` (prep); `Job.timers`, the identity field, `readable_key`, `resolve_settings`, `--timers` on the command line, the launcher stamp (`stamp_identity(..., launcher=)`, `_loadavg`) |
| `harness/gates/gate_resume_identity.py` | the composed-terms tooth (prep); G4's three pairs replaced |
| `harness/experiment/switches.py` | `defer_per_run_execution` and `timers` switches; `INSTRUMENT_SWITCHES`; `DIAGNOSTIC_READBACKS` + `TIMERS` |
| `harness/experiment/arms.py` | `terms` composes `evaluation_exit` for a deferring phase-A arm, and `timers` for every arm of a timed campaign; `env_for(timers=)` |
| `harness/gates/gate_composition.py` | the plan column's `defer_per_run_execution` (unset) and `timers` rows |
| `harness/gates/gate_count_neutrality.py` | `STRADDLE` → `("item5", "DR12")`; `STRADDLE_TEST_SET`, `STRADDLE_TIMERS`, `COUNT_RULE_DECLARATION`, `PRIME_CALLS_DECLARATION` extended; `predict_under_rule`, `compare_counts_under_rule`, `compare_state_files(may_differ=)`, `NOT_COUNTS_BY_KIND`; the per-run-node-counted-twice tooth; timed jobs for a declared side |
| `harness/measurement/stats.py` | `whole_state_population`; `whole_state_statistic`'s docstring (D36) |
| `harness/measurement/tally_evaluation.py` | `matched_accuracy` on the whole state; `matched_accuracy_by_configuration` and `full_distributions` on `whole_state_population`; captions |
| `harness/measurement/paper_tables.py` | the verification row A1 as a construction (`_matched_accuracy_verdict`); the appendix's wall-clock tables rendered through `timing.tables_over` (`wall_clock`, `_wall_clock_lines`); the item-5 prose and `EXACT_CELLS` (Post-processing = 1); `_empty_grid` removed |
| `harness/measurement/timing.py` | **new** — the rows, the summaries, the four stages, the rendering |
| `harness/gates/registry.py`, `harness/gates/__init__.py` | G4 removed; `harness/gates/gate_audit.py` **deleted** (its agreement block and tooth lived at `0353c524`) |
| `harness/core/config.py` | `Campaign.timers`, `CAMPAIGN_TIMERS` |
| `harness/core/records.py` | `RUN_KINDS` + `timing`; the three timer fields with `when == "timers"`; `fields_for(timers_on)`; `IDENTITY_FIELDS_STAMPED_BY_THE_CHILD["timers"]`, `IDENTITY_DEFAULTS_WHEN_ABSENT["timers"]`; an absent child stamp means the default |
| `harness/child/child.py` | `open_record(timers=)`; `harvest_timers`, `stamp_timers`; the snapshot hook timed |
| `harness/child/evaluate.py`, `harness/child/optimise.py` | `--timers`; the epochs; the harvest before the audit; the excluded costs; `timers` dropped from the printed brief |
| `harness/gates/gate_neutrality.py`, `harness/gates/exclusion_review.py` | `campaign_timers`, `timers` in `FIELDS_ADDED_BY_A_DRIVER_CHANGE`; `launcher` always excluded, classified |
| `harness/gates/gate_records.py` | G7's jobs timed; `TIMER_FIELDS` teeth; the harvested check |
| `harness/gates/selfcheck.py` | the reference-arm rule skips instrument switches |
| `harness/README.md` | §18 |
| `harness/__init__.py` | `0.3.0 → 0.4.0` |
| `experiment_runner.py` | `--timing <stage>` (`stage_timing`); `--timers` for `--run`; the campaign press composes `CAMPAIGN_TIMERS` |
| `PROCESS_diff.py` | the item-5 and DR12 annotations and summary addenda |

## Appendix — change log (append-only)

- 2026-09-29 — `c161500c` prep; `cfa0d3ff` item 5 (G1 `c161500c → cfa0d3ff` PASS; GC `DR11 → item5`
  PASS under the declared rule); `0353c524` D36 harness (G4 pressed: FAIL on its per-run-owned tooth,
  agreement 18/18); `9ed0da4c` G4 retired (G6, GT, G2 re-pressed: PASS); `24b78e2d` DR12 (G1
  `9ed0da4c → 24b78e2d` PASS; GC `item5 → DR12` criterion held, one tooth did not trip; G7 one tooth did
  not trip; G5 FAIL on a stale matrix-composed record; the self-check's run path refused; the timing
  stages run on the gate job set, 66 + 22 runs at W = 1); `d8873d49` the three fixes (GC, G7 re-pressed
  PASS; G5 re-made PASS; self-check PASS; `--gate all` stopped at `resume_identity`); `b9b134d9` the
  `resume_identity` fix (PASS). Every record's `tree_git_head` surveyed (§11).

---

## 15. Orchestrator's critical assessment (protocol §5) — verdict: merge (item 5 and DR12, under D37)

*Written 2026-09-29 by the orchestrating session under D37: both driver changes merge on this assessment,
their diffs in §3 and §7 for the user's review on return. Checked differently from the agent.*

**Checked.** (1) `git diff --name-only ca7200ff..fd1ba0ff`: 32 files; under `PROCESS/` only `caller.py`,
`solver/solver_handler.py`, `copy_gates.py`, `PROVENANCE.json`, `CHANGES.md`; **0 paths under
`process/models/`, 0 under `_v4/`**; worktree clean; `merge-tree` against the trunk: no conflict; the report
commit `fd1ba0ff` changes no code beyond `b9b134d9`. (2) `compileall` clean and `--gates` constructs the
registry (28 gates) at the tip, run by the orchestrator. (3) The gate-table record on disk: **27 PASS, 1 FAIL**
(`tally_contracts`, I-35), 28 rows; every verdict record read: GC PASS 3 989 / 0 (the `item5 → DR12`
straddle), G1 PASS, G2 5 026 / 0, G6 6 717 / 0, GT 13 424 / 794 (the biting drops), G7 183 / 0, G5 156 / 0, GR
read 256 / 0; the two GC straddle files `DR11__item5` and `item5__DR12` each 22 pairs, 3 989 leaves and 46 125
components, 0 differing from the rule; G4's last verdict FAIL at `0353c524` kept on disk, the module gone.
(4) The stamp survey recounted from every `metrics.json`: 509 records; the commits are this task's and the
seeded tree's, none foreign.

**One disclosure the report does not make.** The **28 records at `cfa0d3ff` — GC's item-5 side and G1's
after capture — read `tree_git_dirty = true`** (the report discloses the DR12 chain's README-only dirt, §8.1,
and calls G1's after side at `cfa0d3ff` clean at §4.1 line 216; the records say otherwise, and which files
were dirty is not recorded). What bounds it: the `item5 → DR12` straddle's after side was made at `24b78e2d`
with the README alone dirty and reads **0 differing** against those 28 on every count leaf and every exit-state
component, so the counts and states of the item-5 side are exactly those of a committed driver — the
count-neutrality claim of item 5 (`DR11 → item5` under the declared rule) stands transitively through a
committed tree. Recorded as a protocol note; the campaign's own records at a clean tip are the product.

**Read against the rulings.** Item 5 is D35 (the flat arms do not defer; `A2`'s evaluation now yields the
reference's information) and the user's words ("it should actually run once … in the measurement"): the
once-execution is measured, counted, and — the unforeseen part — is one dispatch sweep, declared and predicted
leaf by leaf (decision 3 is right: a second code path for one sweep is how two implementations start). G4's
retirement is D36's condition met with the FAIL as its evidence (18 of 18 records agreeing on the whole state).
DR12 is D33's instrument as §6 specifies it — `None` when unset, G1 byte-identical, GC 0 differing *with the
timers on* — and D38's run discipline is in the stages (W = 1 repeatability; the validity check wired).
Decision 9 (timers off for gates, on for the campaign, in the identity only when on) is the choice that kept
every seeded record; its cost is that G7 times only its own smoke jobs, which is what G7 needs.

**The phase A timing limit is real and is acted on.** A phase A record is one evaluation in a fresh process,
so its module rows carry numba's cache load (259–351 ms against 21–32 ms warmed); the appendix's phase A
table would then be a table of first evaluations. The plan's §6 asks for the evaluation's cost. **Ruled
(autonomous): the campaign task adds A91's warmed form to the evaluation child** — a discarded warm-up
evaluation on the same entry, the entry snapshot re-entered bit-exact (D25's mechanism), a fresh `Caller`,
counters reset, then the measured evaluation; the child stamps both evaluations' counts and the exit-state
digest of each and refuses if they differ (the warm-up is then a per-record determinism check for free).
It is a harness change to the child, not a driver change: no G1; its neutrality is shown as GC shows it — the
gate job set's evaluation records before and after, every count and every exit-state component identical.
The fixed per-run term is unaffected (it is timed from process start to the *first* evaluation, which stays
the warm-up's; the table names which).

**Queue consequences at merge.** Item 5 and DR12 merged (V5 plan §11 rows; §5 A1 on the whole state, G4 gone
from §7 Table 2; §6's tables wired; §10's repeatability line corrected to GC's job set, 66 runs); the dirty
disclosure and the warm-up ruling logged; the campaign task (A102) briefed with the warm-up as its first
stage; I-35 unchanged.
