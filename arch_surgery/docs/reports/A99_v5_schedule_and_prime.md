# A99 (v5-schedule-and-prime) — DR9 (the schedule and the deferral sets resolved once per run), DR10 (the prime once per evaluation, before M1), and the count-neutrality gate GC

> **Document status** — **OPEN.** Task **A99 (v5-schedule-and-prime)**, branch `A99-v5-schedule-and-prime`
> (worktree `.claude/worktrees/A99-v5-schedule-and-prime`, seeded with A94 (v5-copy)'s relocated records
> `idf_probe/runs/A94_runs/v5_copy_gates/`), base **`43d31a04`** (= `architecture_surgery` at dispatch; the V5
> driver copy there is byte-identical to the copy commit `d6c246a1` — `git diff --stat d6c246a1 43d31a04 --
> …_v5/PROCESS/` is empty), tip **``a0de2e13`** (the last code commit; this report's own commit follows it and changes no code)**`**. Two driver changes, each its own commit and each needing the
> user's approval before merge (harness plan §3; D11's review rule): **DR9 = `e5137707`**, **DR10 = `a0de2e13`**.
> The physics is untouched (`g0prime` PASS at every press). Every number below was written by a gate of the
> committed harness (`experiment_runner.py --gate <name> --resume`, verdict records under the worktree's
> `MDA_partitioning_experiment_v5/runs/gates/<name>/gate.json`) or by `run_stamp_survey.py`; none was typed
> from inspection. Records are moved before retirement to
> `arch_surgery/idf_probe/runs/v5_schedule_and_prime/` (§8) so the retire script lands one tree.
> Arm names are today's (A78 (arm-renames)); no record read here predates the renaming.

---

## 1. Verdict

**Both driver changes are count-neutral and switch-neutral, measured; every gate the brief names PASSes with every tooth
tripped; one inherited gate FAILs as it did at the copy commit (`self_containment`, issue I-32, V4's help string).**

| gate | what it straddles | verdict | population and denominator | teeth |
|---|---|---|---|---|
| **GC** `count_neutrality` (new) | copy side (`3c46287b`, driver = `d6c246a1`'s) → **DR9** (`e5137707`) | **PASS** | 22 run pairs (11 evaluations from the displaced entry at seed 1, δ = 0.10; 11 optimisations from seed 0): **3 985 count leaves** under 42 declared paths, **0 differing**; 33 prime-count checks under the rule `identical`, 0 failing; **46 125 coupling-state components** over every state file the runs wrote, **0 differing** | 3/3 |
| **GC** `count_neutrality` | **DR9** (`e5137707`) → **DR10** (`a0de2e13`) | **PASS** | 22 run pairs (the same job set): **3 985 count leaves, 0 differing**; 33 prime-count checks under the rule `once_per_evaluation`, 0 failing — on the six pairs whose arm composes the prime the after side equals the evaluation count exactly (`A2`: 1 where the per-sweep form stamped 13 / 13 / 15 on nof / lad / st; `B2`: 660 / 1 050 / 570 where it stamped 5 500 / 8 763 / 5 260, and the first evaluation's own count 1 where it stamped 14 / 13 / 17), 0 on the sixteen that do not; **46 125 components, 0 differing** | 3/3 |
| **G1** `switch_neutrality` | pool fix (`f93d1df1`, driver = the copy's) → **DR9** (`e5137707`) | **PASS** | 6 pairs (`AR`, `BR` × 3 configurations): **3 980 record values** and **51 319 output-file lines** compared without tolerance, **0 differing**; 624 values and 45 lines excluded by name; the new `schedule_resolution` field conditionally excluded on 12 leaves (absent on the before side) | 9/9 |
| **G1** `switch_neutrality` | **DR9** (`e5137707`) → **DR10** (`a0de2e13`) | **PASS** | 6 pairs: **3 992 record values** and **51 319 output-file lines**, **0 differing**; 618 values and 45 lines excluded by name. Pressed **without** `--resume` after a first press with it had kept the `after` capture from the DR9 commit and said so ("BOTH CAPTURES AT e5137707 … NOT a driver-change result") — the gate's own straddle line caught trap T13; the kept verdict was overwritten by the real one | 9/9 |
| **G2** `prime_map` (re-formed) | the prime's once-per-evaluation form at `a0de2e13` | **PASS** | (i) 6 arrangement/configuration pairs (flat `A0` and partitioned `A2` × 3 configurations), 12 evaluations from the reference exit snapshots: **5 026 components compared, 0 differing** (840 / 846 / 827 declared, every one compared); the prime called 0 times off and **1** time on in every pair. (ii) 6 primed pairs of GC's `DR9 → DR10` straddle (`A2`, `B2` × 3): **12 565 components compared, 0 differing**, every prime count as declared | 3/3 |
| `copy_identity` | the copy at `a0de2e13` against `f2dc9243`'s `process/` | **PASS** | 224 files compared, the eight permitted files differing, each on exactly its recorded hunks and post-edit digest | 12/12 |
| `g0prime` (G0) | `process/models/` at `a0de2e13` against `c0ae5b28` | **PASS** | 77 model files, 76 identical, `pulse.py` on its approved edit (D14(b)) | 4/4 |
| `edit_behaviour` | the A48 existence check | **PASS** | — | 1/1 |
| run-free self-checks: `composition`, `rungs`, `capability`, `provenance`, `data`, `run_path`, `stage_provenance`, `resume_identity`, `artifacts_check`, `artifacts_derive_inputs` | the harness at `a0de2e13` | **PASS (10 of 10)** | as each verdict states; `resume_identity` carries the new tooth of §5 (10/10) | all tripped |
| `self_containment` (inherited) | V4's `experiment_runner.py:1033` help string | **FAIL** | 1 executable line naming `idf_probe/`; the finding A94 reported (I-32; A97 (v4-self-containment) is dispatched for V4) — not this task's | 1/1 |

**GR is not re-pressed** (V5 plan §7: "no GR beyond the copy"). GC's first press at the copy side (`3c46287b`, one
side compared with itself, §2.3) is a determinism result, labelled as such in its record, and is what makes the two
straddles above readable.

**What the user is asked to approve** (per change, before merge): the two driver diffs in §3 and §4, exactly as
committed. Nothing under `process/models/` changed. The harness-side files outside `PROCESS/` that this task touched
are listed in §6 for the merge over A98 (v5-reporting-trim).

---

## 2. GC — the count-neutrality gate (V5 plan §7)

### 2.1 What it binds

A driver change that is *meant* to change no count has to be shown to change none on the arms that compose the
switches — G1 runs only `AR`/`BR`, every switch unset, and says nothing about `A2`'s schedule or `B2`'s prime. GC is
the other half. **Job set** (the brief): both phases, every arm active on each of the three configurations, one seed
per configuration — the evaluation phase from the displaced entry at seed 1 (G6's pairing seed, δ = 0.10, entered from
the reference snapshot, the burn-time constant displaced with it through `reproduction.entry_pin`), the optimisation
phase from seed 0. Twenty-two jobs on V4's configurations (`A1`, `B1` inactive on `st_regression`), composed through
the campaign (`count_neutrality_jobs`, `jobs_read`) and run through the shared pool (`pool.run_all`); no directory is
named.

**Two sides at two commits under one pool.** The pool keeps one directory per job identity and a straddle's two sides
are one job at two commits. G1 names two directories; GC keeps the pool's rule and puts the **side into the identity**:
every job carries `override_env[HARNESS_COUNT_NEUTRALITY_LABEL] = <label>` — a variable the driver never reads — so the
two sides are two digests and two pool directories, and neither can be resolved to the other or to the campaign's run
of the same arm (the verdict checks the three digests are distinct on every row, `labels_are_distinct_identities`).
`STRADDLE = (before_label, after_label)` is a module constant committed **with** the driver change it straddles
(`("copy","copy")` at `3c46287b`, `("copy","DR9")` at `e5137707`, `("DR9","DR10")` at `a0de2e13`). The before side is
**read and never made** by the body (a side that can only be made at a commit behind us must not be handed to the pool
under `--resume`, which consults the current record contract and would re-make it at this commit — trap T13); where it
is absent the gate refuses, except on a press whose two labels are equal, which makes the one side and says out loud it
is a determinism result. One comparison record per straddle is kept at
`runs/gates/count_neutrality/straddles/<before>__<after>.json`, never overwritten by a later change's press, beside the
framework's latest `gate.json`.

**What is compared, per pair.** Every leaf under 42 declared count paths (`COUNT_PATHS`: node calls total / single
evaluation / solve phase, dispatch sweeps, `n_model_calls`, the per-evaluation sweep histogram and evaluation count, the
block loop's totals per block, the two predicates' evaluations and components compared, the block visits and empty
visits, the per-node census, the per-run deferral's own counts, the output path's counts, the optimiser's iterations,
every per-attempt count and the attempt accounting, the first evaluation's counts and hex floats, `mfile.ifail`, the
optimum's hex floats, the audit's residual maxima on both rulers and its own node calls, the burn time and the lift
residual as hex); a leaf present on one side only is a mismatch, never a smaller population. **Every coupling-state
file** the run wrote — `y_entry.json`, `y_exit.json`, and the output path's `y_entry_to_write_output_files.json` and
`y_before_finalise.json` — component by component, every kind of component, floats as hex literals (G2's
`full_state_compare`). **One count may change and only as declared** (`PRIME_CALLS_DECLARATION`, keyed by the after
label): `n_arrangement_method_calls` — `identical` for `copy` and `DR9`; `once_per_evaluation` for `DR10`, under which
the after side must equal the evaluation count (1 in phase A, `sweeps_per_eval.n_evaluations` in phase B) on every arm
whose driver read-back says the prime is composed and 0 on every other, with the first evaluation's own prime count 1
or 0 likewise; the before side is reported beside, not compared.

**Teeth** (each must be the one and only thing the comparison reports): one added to `node_calls_total` in a copy of an
after-side record; one unit in the last place on one float of a copy of an exit state; one added to
`n_arrangement_method_calls` under whichever rule is declared.

### 2.2 Files

`harness/gates/gate_count_neutrality.py` (new, `3c46287b` and `f188d3db`); registered as `count_neutrality` [GC] in
`harness/gates/registry.py` (the import line and one entry; at DR10 also one line in `GATE_ORDER`, where it replaces
`cold_chain`).

### 2.3 The three presses

| press | commit | STRADDLE | result |
|---|---|---|---|
| copy side | `3c46287b` (re-compared at `f188d3db` with `--resume`, 22/22 kept, to write the straddle file) | `copy`,`copy` | PASS as a self-comparison: "ONE SIDE, labelled 'copy', at 3c46287b: compared with itself — determinism and coverage of the declared paths, NOT a driver-change result." 3 985 leaves, 46 125 components, 0 differing; 3/3 teeth (`node_calls_total` 23509 → 23510 on `B/B2/st_regression` reported as the one differing leaf of 259; one ulp on `blanket.deg_blkt_inboard_poloidal_plasma` the one differing component of 827; +1 on the prime count 5260 → 5261 fails the rule) |
| DR9 | `e5137707` | `copy`,`DR9` | **PASS**, "straddles 'copy' at ['3c46287b'] -> 'DR9' at ['e5137707']: a count-neutrality result." 22 pairs; 3 985 count leaves, 0 differing; 33 prime checks (`identical`), 0 failing; 46 125 components, 0 differing; 3/3 teeth. The new stamp on the after side: `schedule_resolution.n_resolutions` = 1 on `A0 A1 A2 B0 B1 B2`, 0 on `AR BR` |
| DR10 | `a0de2e13` | `DR9`,`DR10` | **PASS**, "straddles 'DR9' at ['e5137707'] -> 'DR10' at ['a0de2e13']: a count-neutrality result." 22 pairs; 3 985 count leaves, 0 differing; 33 prime checks (`once_per_evaluation`), 0 failing; 46 125 components, 0 differing; 3/3 teeth (`node_calls_total` 23509 → 23510 the one differing leaf of 259; one ulp on one float the one differing component of 827; +1 on the prime count 570 → 571 fails the rule against the evaluation count 570) |

Record: `runs/gates/count_neutrality/gate.json` (the latest), `runs/gates/count_neutrality/straddles/{copy__copy,copy__DR9,DR9__DR10}.json`.

---

## 3. DR9 — the schedule and the deferral sets resolved once per run (commit `e5137707`)

**Ruling.** V5 list item 7; **D31** (the user: *"this should be fixed in v5"*); issue I-30 (A91 (block-sweep-timing)
measured 8–11 ms of `module_schedule` per evaluation of a deferring arm, 0 in the arms that defer nothing).

**The change, in the driver copy** (`PROCESS/process/core/caller.py`). One resolver, `resolve_schedule(i_figure_merit)`,
memoised on the figure of merit in `_SCHEDULE_CACHE`, does the `ast` walk of the two predicate sources
(`_predicate_read_fields`), the read of the committed write census (`_node_write_sets`) and the block membership on its
first call and returns the same objects on every later one. `resolved_defer_per_call_tails` and `module_schedule`
delegate to it and keep their signatures; `Caller._resolve_defer_per_call_tails` is unchanged (a cache hit now).
`SCHEDULE_RESOLUTION` is the once-per-run stamp: `n_resolutions` and, per resolution, the figure of merit, the deferral
name and the MDA mode, the pre-/post-predicate tails, the schedule (label, nodes, iterated) and whether one block covers
the loop, and the sha256 of every file read (the two predicate sources, `node_writesets.json`, `dsm_node_map.json`) with
the count of predicate read fields (215 on `large_tokamak_nof`). The per-call stamp goes: `_module_stats` loses its
`tail` argument and `deferred_tail` entry. With every switch unset the resolver is never reached.

**The harness side.** `records.py`: one field, `schedule_resolution` ("AB", always); `child.harvest_counters`: one block
that copies the stamp into the record (both phases); `gate_neutrality.FIELDS_ADDED_BY_A_DRIVER_CHANGE`: the new field,
conditional (compared wherever both sides carry it — on the DR10 straddle it is); `copy_gates.PERMITTED_EDIT_FILES`: one
row (kind `memoisation`) for `caller.py`; `PROVENANCE.json` regenerated (`copy_date` kept at 2026-09-10,
`permitted_edits_updated` gains the A99 entry, `files_changed = [caller.py]`); `CHANGES.md` §4.5.14; `PROCESS_diff.py`:
four annotation markers so the hunks are claimed by name. **The schema change re-makes every seeded record under
`--resume`** (amendment 17: a resume cannot cross a schema change) — the three entry references were re-made at
`e5137707`; nothing else seeded was pressed.

**The full diff of `caller.py`** (`git diff f93d1df1 e5137707 -- …_v5/PROCESS/process/core/caller.py`, 228 lines, unified
with two context lines):

```diff
diff --git a/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/caller.py b/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/caller.py
index 34c96f1e..ca285539 100644
--- a/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/caller.py
+++ b/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/caller.py
@@ -451,12 +451,6 @@ def resolved_defer_per_call_tails(i_figure_merit: int) -> tuple[tuple[str, ...],
     without reconstructing the rule.
     """
-    if not DEFER_PER_CALL_NODES:
-        return (), ()
-    reads = _predicate_read_fields(i_figure_merit)
-    writes = _node_write_sets()
-    pre, post = [], []
-    for n in DEFER_PER_CALL_NODES:
-        (pre if (writes.get(n, frozenset()) & reads) else post).append(n)
-    return tuple(pre), tuple(post)
+    pre, post, _schedule, _tail = resolve_schedule(i_figure_merit)
+    return pre, post
 
 
@@ -1158,27 +1152,6 @@ def module_schedule(i_figure_merit: int) -> tuple[tuple, ...]:
         deferred to after it (empty when the per-call deferral is off).
     """
-    tail = (
-        frozenset(resolved_defer_per_call_tail(i_figure_merit))
-        if DEFER_PER_CALL_ENABLED
-        else frozenset()
-    )
-    # ``flat`` (decision D18's control arm A0') is one block over every
-    # in-loop node: the same predicate, the same caps, the same failure policy,
-    # a different schedule.  It is written as a branch here rather than as a
-    # second solver because A26 §10 measured that it is the degenerate case of
-    # the block schedule, and two implementations of one loop is how they
-    # drift.
-    if module_solve.FLAT:
-        return (
-            (module_solve.FLAT_BLOCK_LABEL, _loop_node_set(tail), True),
-        ), tail
-    by_module: dict[str, set[str]] = {}
-    for node, mod in NODE_MODULE.items():
-        by_module.setdefault(mod, set()).add(node)
-    schedule = []
-    for label in module_solve.BLOCK_ORDER:
-        nodes = frozenset(by_module.get(label, set()) - tail)
-        schedule.append((label, nodes, label in module_solve.ITERATED))
-    return tuple(schedule), tail
+    _pre, _post, schedule, tail = resolve_schedule(i_figure_merit)
+    return schedule, tail
 
 
@@ -1223,4 +1196,129 @@ def _single_block_covers_loop(schedule, tail) -> bool:
 
 
+# --------------------------------------------------------------------------
+# DR9 (V5 list item 7, decision D31; task A99 (v5-schedule-and-prime)) -- the
+# block schedule and the deferral sets are resolved ONCE PER RUN.
+#
+# Until this change every ``call_models`` re-derived which nodes it defers:
+# ``_predicate_read_fields`` walked the objective and constraint sources with
+# ``ast`` and ``_node_write_sets`` re-read the committed write census, on
+# every evaluation of every deferring arm -- 8-11 ms before any model ran, 0
+# in the arms that defer nothing (issue I-30, measured by A91).  Not the
+# architecture: the models, their order and every count are identical with or
+# without it, and a driver written for the partitioned order would resolve
+# its schedule once at start-up.  The user ruled it fixed in V5 (D31).
+#
+# The resolution depends on exactly one run-time input, the figure of merit
+# (``_predicate_read_fields`` narrows the objective side to its branch), and
+# on things fixed for the process: the two predicate sources, the write
+# census, the node map, and the switches resolved at import.  So it is keyed
+# on the figure of merit alone and memoised in :data:`_SCHEDULE_CACHE`; a scan
+# that changed the figure of merit between calls would resolve a second entry
+# rather than reuse a wrong one.  :data:`SCHEDULE_RESOLUTION` is the stamp the
+# harness records once per run: what was resolved, from what (the digests of
+# the files read), and how many times the resolver ran -- 1 in every run of
+# this experiment, which gate GC checks beside every other count.
+#
+# With every switch unset nothing here executes: ``module_schedule`` is only
+# reached under a block schedule and the deferral tails only under a per-call
+# deferral, so the default path never touches the cache (gate G1).
+
+#: The once-per-run resolution, by figure of merit.
+_SCHEDULE_CACHE: dict[int, tuple] = {}
+
+#: The stamp: integer counts, names and digests only.  ``resolutions`` holds
+#: one entry per figure of merit the run resolved -- one, in this experiment.
+SCHEDULE_RESOLUTION: dict = {
+    "n_resolutions": 0,
+    "resolutions": [],
+}
+
+
+def _sha256_of(path: Path) -> str:
+    import hashlib  # noqa: PLC0415 - the resolution path only, once per run
+
+    return hashlib.sha256(path.read_bytes()).hexdigest()
+
+
+def resolve_schedule(
+    i_figure_merit: int,
+) -> tuple[tuple[str, ...], tuple[str, ...], tuple[tuple, ...], frozenset[str]]:
+    """``(pre_predicate, post_predicate, schedule, tail)`` for *i_figure_merit*, once.
+
+    The one place the routing rule (which slot a deferred node runs in) and
+    the block membership are computed.  Memoised on the figure of merit: the
+    first call for a value does the work and stamps the resolution, every
+    later call returns the same objects.  ``schedule`` is empty when no block
+    schedule is on; the tails are empty when nothing is deferred.
+    """
+    key = int(i_figure_merit)
+    hit = _SCHEDULE_CACHE.get(key)
+    if hit is not None:
+        return hit
+    pre: list[str] = []
+    post: list[str] = []
+    inputs: dict = {}
+    if DEFER_PER_CALL_NODES:
+        reads = _predicate_read_fields(key)
+        writes = _node_write_sets()
+        for n in DEFER_PER_CALL_NODES:
+            (pre if (writes.get(n, frozenset()) & reads) else post).append(n)
+        inputs["predicate_sources"] = {
+            p.name: _sha256_of(p) for p in _PREDICATE_SOURCES
+        }
+        inputs["node_write_sets"] = {
+            NODE_WRITESET_PATH.name: _sha256_of(NODE_WRITESET_PATH)
+        }
+        inputs["n_predicate_read_fields"] = len(reads)
+    tail = frozenset(pre) | frozenset(post)
+    schedule: tuple[tuple, ...] = ()
+    if MDA_ENABLED:
+        # ``flat`` (decision D18's control arm A0') is one block over every
+        # in-loop node: the same predicate, the same caps, the same failure
+        # policy, a different schedule.  It is written as a branch here rather
+        # than as a second solver because A26 §10 measured that it is the
+        # degenerate case of the block schedule, and two implementations of
+        # one loop is how they drift.
+        if module_solve.FLAT:
+            schedule = (
+                (module_solve.FLAT_BLOCK_LABEL, _loop_node_set(tail), True),
+            )
+        else:
+            by_module: dict[str, set[str]] = {}
+            for node, mod in NODE_MODULE.items():
+                by_module.setdefault(mod, set()).add(node)
+            schedule = tuple(
+                (
+                    label,
+                    frozenset(by_module.get(label, set()) - tail),
+                    label in module_solve.ITERATED,
+                )
+                for label in module_solve.BLOCK_ORDER
+            )
+        inputs["node_map"] = {NODE_MAP_PATH.name: _sha256_of(NODE_MAP_PATH)}
+    resolved = (tuple(pre), tuple(post), schedule, tail)
+    _SCHEDULE_CACHE[key] = resolved
+    SCHEDULE_RESOLUTION["n_resolutions"] += 1
+    SCHEDULE_RESOLUTION["resolutions"].append(
+        {
+            "i_figure_merit": key,
+            "figure_of_merit": FiguresOfMerit(abs(key)).name,
+            "defer_per_call": DEFER_PER_CALL_NAME,
+            "mda": MDA_MODE,
+            "pre_predicate": list(pre),
+            "post_predicate": list(post),
+            "schedule": [
+                [label, sorted(nodes), bool(iterate)]
+                for label, nodes, iterate in schedule
+            ],
+            "single_block_covers_loop": (
+                _single_block_covers_loop(schedule, tail) if schedule else None
+            ),
+            "inputs": inputs,
+        }
+    )
+    return resolved
+
+
 def _roll_up(stats: dict) -> None:
     """Fold one ``call_models``'s block counts into the run's totals."""
@@ -1270,7 +1368,8 @@ class Caller:
         # deferral-off path ever sees.
         self._pending: list | None = None
-        # VP2: the tail resolved for the current ``call_models``.  Re-resolved
-        # on every call rather than memoised: it depends on the configuration's
-        # figure of merit, and a scan may change that between calls.
+        # VP2: the tail resolved for the current ``call_models``.  Resolved
+        # once per run (DR9, :func:`resolve_schedule`) and looked up per call;
+        # keyed on the configuration's figure of merit, so a scan that changed
+        # it between calls would resolve a second entry, never reuse a wrong one.
         self._deferred_tail: frozenset[str] = frozenset()
         # VP2 / plan §4.1d: the deferred nodes split into a group that runs
@@ -1638,5 +1737,5 @@ class Caller:
                     block_sweeps, schedule_passes, inner_counts,
                     moved_constants, converged=False, cap_hit="block",
-                    tail=tail, single_block=single_block,
+                    single_block=single_block,
                 )
                 _roll_up(self.module_solve_stats)
@@ -1667,6 +1766,5 @@ class Caller:
         self.module_solve_stats = self._module_stats(
             block_sweeps, schedule_passes, inner_counts, moved_constants,
-            converged=True, cap_hit=None, tail=tail,
-            single_block=single_block,
+            converged=True, cap_hit=None, single_block=single_block,
         )
         _roll_up(self.module_solve_stats)
@@ -1696,5 +1794,5 @@ class Caller:
     def _module_stats(
         block_sweeps, schedule_passes, inner_counts, moved_constants,
-        *, converged, cap_hit, tail, single_block=False,
+        *, converged, cap_hit, single_block=False,
     ) -> dict:
         """The block schedule's own counts, for the run record.
@@ -1703,5 +1801,7 @@ class Caller:
         reproduction reference and every earlier record use for the number of
         schedule passes, and renaming a recorded field is a change to the
-        record schema rather than to the driver.  It is 1 in every arm.
+        record schema rather than to the driver.  It is 1 in every arm.  The
+        deferred tail is no longer stamped here per call: it is resolved once
+        per run and stamped once, in :data:`SCHEDULE_RESOLUTION` (DR9).
         """
         return {
@@ -1714,5 +1814,4 @@ class Caller:
             "inner_totals": {k: sum(v) for k, v in inner_counts.items()},
             "moved_constants": sorted(moved_constants),
-            "deferred_tail": sorted(tail),
         }
 
```

**Gates.** GC copy → DR9 PASS (§2.3); G1 `f93d1df1 → e5137707` PASS (3 980 values, 51 319 lines, 0 differing, 9/9
teeth; the straddle is against the pool-fix commit `f93d1df1`, whose driver copy is byte-identical to the copy
commit's — §5 (2) says why the before capture sits there); `copy_identity` PASS 12/12, `g0prime` PASS 4/4,
`edit_behaviour` PASS 1/1; the run-free self-checks PASS; `self_containment` FAIL (inherited, I-32).

---

## 4. DR10 — the prime once per evaluation, before M1 (commit `a0de2e13`)

**Ruling.** V5 list item 8 (the user: *"It is pre-processing before the partitioned MDAs can start. I see this as part of
the minimal sequencing operations (like moving build)."*); V5 plan §11 DR10; §12 Q3 (G3/G3c dropped).

**The change, in the driver copy.** The arrangement-method hook — two statements under one guard — moves from the head of
every sweep (`_call_models_once`, where V4 put it so every block sweep primed: about 9 calls per evaluation in phase B,
13–15 in phase A) to the head of every evaluation (`_call_models_inner`, before the per-run resolution and before the
block schedule or the flat loop starts). The output path and the exit audit call `_call_models_once` directly and no
longer prime — `FirstWall` has run by then and the pair holds the same bits. `n_arrangement_method_calls` becomes the
evaluation count. Three comments follow the move (the module-level VP6 comment, the read-back's comment, and the
`EMPTY_BLOCK_SWEEPS` comment that listed the prime among an empty visit's costs).

**The full diff of `caller.py`** (`git diff e5137707 a0de2e13 -- …_v5/PROCESS/process/core/caller.py`, 95 lines):

```diff
diff --git a/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/caller.py b/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/caller.py
index ca285539..0b741678 100644
--- a/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/caller.py
+++ b/arch_surgery/MDA_partitioning_experiment_v5/PROCESS/process/core/caller.py
@@ -88,14 +88,20 @@ ARRANGEMENT_NODE_HEAD: tuple[str, ...] = _ARRANGEMENT_NODE_ORDERS[ARRANGEMENT_NO
 # pair, once, with A35's measured linear coefficients.
 #
-# The prime executes that one method at the head of every sweep, so ``Build``
-# reads this pass's value.  It is a driver choice about *when* an existing
-# model method runs -- the same family as the VP1 reorder but finer-grained
-# (a method, not a node); nothing under ``process/models/`` changes, and
-# ``FirstWall``'s own execution is untouched (the prime *duplicates* a
-# run-constant of two floating-point operations, identical bits each time).
+# The prime executes that one method **once per evaluation, before the first
+# block** -- pre-processing of the sequenced schedule (DR10, V5 list item 8,
+# task A99 (v5-schedule-and-prime); the user: "it is pre-processing before the
+# partitioned MDAs can start") -- so ``Build`` reads this evaluation's value.
+# V4 executed it at the head of every sweep instead (about 9-15 stamped calls
+# per evaluation); the values are the same bits each time, so the exit states
+# are identical (gate G2) and the stamped count becomes the evaluation count
+# (gate GC).  It is a driver choice about *when* an existing model method runs
+# -- the same family as the VP1 reorder but finer-grained (a method, not a
+# node); nothing under ``process/models/`` changes, and ``FirstWall``'s own
+# execution is untouched (the prime *duplicates* a run-constant of two
+# floating-point operations, identical bits each time).
 #
 # ``off`` is the default and is upstream behaviour exactly: the guard in
-# ``_call_models_once`` is one module-level boolean read per sweep and the
-# counter never moves (gate G1: byte identity with the switch unset).
+# ``_call_models_inner`` is one module-level boolean read per evaluation and
+# the counter never moves (gate G1: byte identity with the switch unset).
 #
 # The call is deliberately NOT routed through :meth:`Caller._node`: it is
@@ -118,5 +124,6 @@ if ARRANGEMENT_METHOD_NAME not in _ARRANGEMENT_METHODS:
     )
 
-#: True when the first-wall geometry pair is primed at the sweep head.
+#: True when the first-wall geometry pair is primed once per evaluation,
+#: before the first block.
 ARRANGEMENT_METHOD_FW_GEOMETRY: bool = _ARRANGEMENT_METHODS[ARRANGEMENT_METHOD_NAME]
 
@@ -911,6 +918,6 @@ EMPTY_BLOCK_VISITS: dict[str, int] = {}
 #: schedule visits with no members costs **no** sweep; a block whose members
 #: are all skipped at the call site costs a full walk of the dispatch body --
-#: the design-vector injection at its head, the switch dispatch through every
-#: call site, and the arrangement method if it is on -- executing no model.
+#: the design-vector injection at its head and the switch dispatch through
+#: every call site -- executing no model.
 #: That is the cost the empty visit actually has, and it is the number a
 #: per-sweep-overhead table needs; the visit count alone would overstate it.
@@ -1859,4 +1866,20 @@ class Caller:
         of its own.
         """
+        # VP6 (D19, task A40; DR10, V5 list item 8, task A99): the
+        # arrangement's method-level move is PRE-PROCESSING of the evaluation.
+        # The first-wall geometry pair is a run-constant of two input-file
+        # values; priming it once here, before the first block of the schedule
+        # (or the first sweep of the flat loop), is what lets Build -- which
+        # the partitioned schedule runs before FirstWall -- read this
+        # evaluation's value rather than the previous one's.  V4 primed at the
+        # head of every sweep; the bits are the same each time, so the exit
+        # states are unchanged (gate G2) and the stamped count becomes the
+        # evaluation count (gate GC).  Not a node, not routed through _node,
+        # not counted in NODE_CALLS -- stamped via ARRANGEMENT_METHOD_CALLS.
+        # With the switch unset this is one boolean read (gate G1).
+        if ARRANGEMENT_METHOD_FW_GEOMETRY:
+            ARRANGEMENT_METHOD_CALLS[0] += 1
+            self.models.fw.set_fw_geometry()
+
         # VP2c: resolve (and on first use validate) the post-solve exclusion
         # set.  With the switch off ``_defer_per_run`` stays ``None`` and nothing
@@ -2159,17 +2182,10 @@ class Caller:
             return
 
-        # VP6 (D19, task A40): prime the first-wall geometry pair at the
-        # head of the sweep, so Build (which the schedule runs before
-        # FirstWall) reads this pass's value instead of the previous
-        # pass's.  Not a node, not routed through _node, not counted in
-        # NODE_CALLS -- stamped via ARRANGEMENT_METHOD_CALLS (see the module-level
-        # comment).  Because it sits here, it is on every path that walks
-        # the model sequence: the flat loop, every VP4 block sweep
-        # (Caller._sweep_block runs blocks through this method), the
-        # output phase and the exit audit (harmless, idempotent -- the
-        # write is the same run-constant every time).
-        if ARRANGEMENT_METHOD_FW_GEOMETRY:
-            ARRANGEMENT_METHOD_CALLS[0] += 1
-            self.models.fw.set_fw_geometry()
+        # VP6 (D19, task A40): the first-wall geometry prime used to sit
+        # here, at the head of every sweep; DR10 (A99) moved it to the head
+        # of ``_call_models_inner`` -- once per evaluation, before the first
+        # block.  The output path and the exit audit call this method
+        # directly and no longer prime: FirstWall has run by then and the
+        # pair holds the same bits.
 
         # Tokamak calls
```

**G2 re-formed** (`harness/gates/gate_prime.py`, rewritten; V5 plan §7): (i) from each reference exit snapshot, one flat
and one partitioned evaluation, prime on vs off, exit states bit-identical on N of N components, the method called
**once per evaluation** when on (a phase A run is one evaluation) and not at all when off; (ii) the once-per-evaluation
form's exit states bit-identical to the per-sweep form's on GC's job set — read from GC's `DR9__DR10` straddle record
(`per_sweep_form_comparison`; `reads_from=("count_neutrality",)`), requiring a real straddle, the rule
`once_per_evaluation`, and on every pair whose arm composes the prime (`A2`, `B2`: 6 pairs) 0 differing components and a
passing prime-count check. A missing record or one of another rule is a refusal, not a pass. Teeth: a doctored snapshot
component; a component missing from one side; **a doctored straddle row** (one differing component written into a copy
of GC's record must make (ii) fail). **G3/G3c (`cold_chain`) removed** from `gate_prime.py` and the registry (the ruling
of §12 Q3; its construction no longer exists).

**The harness side.** `copy_gates.py`: one row (kind `hook moved`); `PROVENANCE.json` regenerated; `CHANGES.md` §4.5.15;
`PROCESS_diff.py`: one marker; `gate_count_neutrality.py`: `STRADDLE = ("DR9","DR10")`, the `DR10` declaration
`once_per_evaluation`; `registry.py`: the `cold_chain` line removed, `count_neutrality` added to `GATE_ORDER` before
`prime_map`.

**Gates.** GC DR9 → DR10 PASS (§2.3); **G2 PASS** ((i) 5 026 components, 0 differing, the prime once per evaluation; (ii) 12 565 components over the six primed pairs of GC's straddle, 0 differing; 3/3 teeth, the doctored straddle row making (ii) fail); G1 `e5137707 → a0de2e13` PASS (3 992 values, 51 319 lines, 0 differing, 9/9); `copy_identity` PASS 12/12; `g0prime` PASS 4/4; `edit_behaviour` PASS 1/1; `composition` 7/7, `rungs` 3/3, `capability` 5/5, `provenance` 4/4, `data` 6/6, `run_path` 12/12, `stage_provenance` 5/5, `resume_identity` 10/10, `artifacts_check` 3/3, `artifacts_derive_inputs` 4/4 — all PASS; `self_containment` FAIL (inherited I-32). Records: `runs/gates/<name>/gate.json`, each stamped `a0de2e13`.

---

## 5. Autonomous decisions, each with its reversal path

1. **The side label as an identity field** (§2.1) rather than named directories: the brief asks for pool jobs with no
   directory named, and README §6's rule for a deliberate second run of one identity is "differ in an identity field —
   `override_env` …". *Reversal:* give GC named directories and `runs_under`, as G1 has; the comparison code is unchanged.
2. **The pool fix `f93d1df1` (`pool.directory_for`): a job that names its own directory resolves to it and never by
   digest** — issue I-29 in a form this task met on G1 itself. On this tree (no `after` capture yet) the first DR9 press
   resolved G1's `after` capture by digest **into the `before` records** and re-made them at the DR9 commit, and resolved
   the reference arm's capture into *other* gates' records of the same digest (A94's `input_files/<config>/baseline_evaluation`
   for nof and lad; GR's pool record `A_AR_st_regression_seed000_gate_52070b81…` for st) — so neither capture ever held
   `AR` under `switch_neutrality/`, and the before side was destroyed by the press meant to compare against it. What I
   did: stopped the chain; **reset the unpushed branch** to `f188d3db`, committed the fix with one tooth in
   `resume_identity` ("a named directory is the job's whatever holds its digest"; 10/10 tripped), cherry-picked DR9 on top
   (`9399a42f` → `e5137707`, same content); deleted every record stamped `9399a42f` (15 directories: GC's `DR9`-labelled
   runs, the re-made references, one half-written run, G1's overwritten captures); **restored the three seeded records
   byte-for-byte from `A94_runs/v5_copy_gates/`** (`diff -rq` identical); made G1's `before` capture at `f93d1df1` with the
   tree checked out there (detached, `dirty=0`), then pressed everything at `e5137707`. So G1's DR9 straddle is
   `f93d1df1 → e5137707`; the driver copy at `f93d1df1` is the copy commit's, byte for byte. *Reversal:* `git revert
   f93d1df1` restores the digest-first resolution; G1 then cannot be pressed on a fresh tree that holds a record of its
   identity anywhere — the defect is I-29's and the register already asks for a harness fix with a tooth. **Proposal: close
   I-29 with this fix** (§9). The harness file is `harness/core/pool.py` (one early return with its reason) and
   `harness/gates/gate_resume_identity.py` (one tooth); neither is A98's.
3. **G1's `before` for DR10 re-captured at `e5137707` with `--capture before`** (the runner's own two-step; 6 runs) after
   archiving the DR9 straddle's captures and verdict under `runs/gates/switch_neutrality/straddles/f93d1df1__e5137707/`
   (a copy; the re-capture removes only `before/<config>/<arm>`). Relabelling `after` → `before` by hand would have been
   a relocation of records with a wrong manifest label. *Reversal:* none needed; both straddles' records are on disk.
4. **The per-call `deferred_tail` stamp removed** from `_module_stats` (the brief: "the per-call stamp goes"); nothing in
   the harness read it (grep: no consumer; not in `REFERENCE_FIELDS`, not compared by G1 on `AR`/`BR`). *Reversal:* two
   lines back in `_module_stats` and its two call sites.
5. **The stamp records digests of what the resolution read** (the two predicate sources, the write census, the node map)
   — "the input identity the resolution depends on" — at one sha256 each, once per run. *Reversal:* drop `inputs`.
6. **`schedule_resolution` declared "always" in both phases** (null-safe: a tree without the name writes null; with every
   switch unset it reads `n_resolutions = 0`). This is the schema change that re-makes seeded records under `--resume`
   (amendment 17); it cost the three references. *Reversal:* declare it "finished"-only — the same re-make.
7. **`gate_neutrality.FIELDS_ADDED_BY_A_DRIVER_CHANGE` gains one entry** although the file is not on the brief's list:
   without it G1 reports the new field as "present on one side only" and cannot pass any DR9 straddle. The precedent is
   DR2's `output_loop_sweeps`. *Reversal:* none sensible.
8. **G2's part (ii) reads GC's straddle record** instead of re-running a per-sweep form that no longer exists in the tree;
   GC therefore writes one file per straddle (`f188d3db`). *Reversal:* make (ii) a one-time result in this report and
   drop it from G2's body — then G2 no longer carries item 8's second requirement.
9. **`CHANGES.md` heading count set from `copy_gates.py`** (16 recorded caller.py edits) and A90's block-trace edit noted
   there as recorded in `copy_gates.py` but undocumented in `CHANGES.md` (pre-existing); **`PROCESS_diff.py` already
   exits 1 at the copy commit** (A90's four `evaluators.py` hunks unclaimed, its `module_solve.py` summary missing) — not
   fixed here, reported (§9).
10. **No GR press, no G4/G5/G6/G7/G9 press.** The brief names GC, G1, G2 and copy identity; the schema change would re-make
    all of those gates' runs (≈100) for no question this task asks. Their seeded records at `d6c246a1` stand untouched in
    the tree (the stamp survey, §7). *Reversal:* one `--gate all --resume` at a merged tip, the orchestrator's call.

---

## 6. Files changed outside `PROCESS/` (for the merge over A98 (v5-reporting-trim))

| file | change | commit(s) |
|---|---|---|
| `harness/gates/gate_count_neutrality.py` | **new** — GC | `3c46287b`, `f188d3db`, `e5137707` (STRADDLE), `a0de2e13` (STRADDLE, declaration) |
| `harness/gates/registry.py` | the `_plan_gates` import line (`gate_count_neutrality` added); one entry `"count_neutrality"`; at DR10 the `"cold_chain"` entry removed and `"count_neutrality"` inserted before `"prime_map"` in `GATE_ORDER` | `3c46287b`, `a0de2e13` |
| `harness/gates/gate_prime.py` | rewritten: G2 re-formed, G3/G3c removed | `a0de2e13` |
| `harness/gates/gate_neutrality.py` | one entry in `FIELDS_ADDED_BY_A_DRIVER_CHANGE` (`schedule_resolution`) | `e5137707` |
| `harness/gates/gate_resume_identity.py` | one tooth (`a named directory is the job's whatever holds its digest`) | `f93d1df1` |
| `harness/core/pool.py` | `directory_for`: a job with `outdir` resolves to it (one early return, with its reason in the docstring) | `f93d1df1` |
| `harness/core/records.py` | one `SCHEMA` field, `schedule_resolution` | `e5137707` |
| `harness/child/child.py` | `harvest_counters`: one block stamping `schedule_resolution` | `e5137707` |
| `PROCESS_diff.py` (V5 root) | two mechanism constants and five annotation lines | `e5137707`, `a0de2e13` |
| `chain.py`, `measurement/*`, `experiment/*`, `experiment_runner.py` | **untouched** | — |

Under `PROCESS/`: `process/core/caller.py` (DR9, DR10), `copy_gates.py` (two rows), `PROVENANCE.json` (regenerated
twice, `copy_date` kept), `CHANGES.md` (§4.5.14, §4.5.15, the heading count). Nothing under `process/models/`.

---

## 7. Stamp survey of every record

`run_stamp_survey.py --json …/_press_logs/stamp_survey_before_move.json` (before the move) and `--runs idf_probe/runs/v5_schedule_and_prime --against …` (after it): **132 run records, 0 changed, 0 disappeared, 0 new** across the move. By group and by the commit stamped in the record itself:

| group | `tree_git_head` | records |
|---|---|---|
| pool: GC side `copy` | `3c46287b` | 22 |
| pool: GC side `DR9` | `e5137707` | 22 |
| pool: GC side `DR10` | `a0de2e13` | 22 |
| pool: G2 prime on / off (12 runs at DR10) | `a0de2e13` | 12 |
| pool: the three entry references (`A0` cold), re-made at DR9 by the schema change | `e5137707` | 3 |
| pool: seeded — GR's records (and the restored `A_AR_st_regression_seed000_gate_52070b81…`), untouched | `d6c246a1` | 24 |
| seeded: GR's teeth scratch record, untouched | `d6c246a1` | 1 |
| seeded: the two `input_files/<config>/baseline_evaluation` records — restored byte-identical from A94's tree, then re-made by `artifacts_derive_inputs --resume` at DR9 (the schema change made them incomplete) | `e5137707` | 2 |
| G1 `before` (current: the DR10 straddle's before side) | `e5137707` | 6 |
| G1 `after` (current: the DR10 straddle's after side) | `a0de2e13` | 6 |
| G1 archived DR9 straddle: `straddles/f93d1df1__e5137707/before` | `f93d1df1` | 6 |
| G1 archived DR9 straddle: `straddles/f93d1df1__e5137707/after` | `e5137707` | 6 |

Every verdict record (`gates/<name>/gate.json`) is stamped `a0de2e13` except `reproduction` (`d6c246a1`, seeded, not pressed) and the archived `switch_neutrality/straddles/f93d1df1__e5137707/gate.json` (`e5137707`). GC's three straddle files are stamped `f188d3db` (`copy__copy`, the re-comparison), `e5137707` (`copy__DR9`) and `a0de2e13` (`DR9__DR10`). No record on disk carries the abandoned commit `9399a42f`.

---

## 8. Where the records are

The whole V5 `runs/` tree was moved, before retirement, to
**`<worktree>/arch_surgery/idf_probe/runs/v5_schedule_and_prime/`** (one tree: `gates/` with every verdict, the pool `gates/_runs/`, G1's captures and the archived straddle, `input_files/`, and `_press_logs/` with the seven press logs and the two stamp surveys). The retire script relocates it as one entry, `idf_probe/runs/A99_v5_schedule_and_prime/` — the path to cite once it has run (the retire script prints it). The next V5 task seeds its worktree's `MDA_partitioning_experiment_v5/runs/` from that tree.

---

## 9. Proposals (nothing here edits the queue, the V5 list or the V5 plan)

1. **DR9's and DR10's rows for the harness plan's §3.2 table** (numbering continues from DR8):

   | # | driver change | status | harness impact | if declined |
   |---|---|---|---|---|
   | **DR9** | the block schedule and the per-call deferral sets resolved **once per run** by `resolve_schedule`, memoised on the figure of merit; the resolution stamped once per run (`SCHEDULE_RESOLUTION` → record field `schedule_resolution`, with the digests of what it read); the per-call `deferred_tail` stamp gone | *awaiting the user* (this report; commit `e5137707`) | one record field; one G1 conditional exclusion; gate GC (new); the fixed per-run term of V5 plan §6 | I-30's 8–11 ms per evaluation stays in every deferring arm; no count changes either way |
   | **DR10** | the arrangement-method prime executed **once per evaluation, before the first block** (`_call_models_inner`), never at a sweep head; the output path and the exit audit no longer prime; `n_arrangement_method_calls` = evaluations | *awaiting the user* (this report; commit `a0de2e13`) | G2 re-formed (part (ii) reads GC's `DR9__DR10` record); G3/G3c removed; GC's `once_per_evaluation` rule | the paper's caption must stay as V4 built it; ~9–15 stamped calls per evaluation |

2. **Close I-29 with `f93d1df1`** (§5 (2)): the register's proposed fix — "refuse, in `pool.run`, to re-make a record
   whose resolved directory is not the job's named one, or make `outdir` part of the identity for named jobs" — is
   discharged in its first form by resolving a named directory to itself; the tooth is in `resume_identity`. A90's guard
   can go.
3. **`DIAGNOSTIC_READBACKS` gains `(CALLER, "SCHEDULE_RESOLUTION")`** in `harness/experiment/switches.py` so the capability
   probe reports a tree lacking the stamp (not done: the file is outside the brief's list and A98 touched the module).
4. **`gate_resume_identity.by_design_pairs` gains GC's pair** (a labelled job against the unlabelled campaign job of the
   same arm) — the verdict already checks the three digests differ on every row; the pair table is the declared place.
5. **`PROCESS_diff.py` exits 1 at the copy commit**: A90's four `evaluators.py` hunks are UNEXPLAINED and its
   `module_solve.py` summary paragraph is missing; `CHANGES.md` has no §4 subsection for A90's block-trace edit. One
   small documentation task; not this one's.
6. **The per-sweep-form comparison (G2 (ii)) is a one-time result** like GR: once DR10 is merged no tree can re-make the
   per-sweep side. The V5 plan's G2 row could say so ("read from GC's `DR9__DR10` record").

---

## 10. Limits

- Three configurations, one seed per phase per configuration on the gate job set — the count-neutrality claim is exact on
  that set and is a claim about the driver's arithmetic (which node runs when), not a statistical one; a branch the job
  set never takes is not covered. The evaluation-phase pairs enter from seed 1 at δ = 0.10 only.
- G1 for DR9 straddles `f93d1df1 → e5137707`, not `3c46287b → …`: the `before` had to be made at a commit with the pool
  fix, and the driver at `f93d1df1` is the copy's byte for byte (`git diff d6c246a1 f93d1df1 -- …_v5/PROCESS/` empty).
- The `mixed` ruler is still in the copy (DR11's business); the audit residual is compared on both rulers by GC.
- Timings appear only as the pool's progress lines; none is cited.

---

## Appendix — change log (append-only)

| date | entry |
|---|---|
| 2026-09-29 | Worktree seeded from `A94_runs/v5_copy_gates/`. GC written and registered (`3c46287b`); pressed at the copy side (22 runs + 3 seeded references kept), PASS as a self-comparison, 3/3 teeth; G1 `before` captured (`3c46287b`). |
| 2026-09-29 | GC keeps one record per straddle (`f188d3db`); re-pressed with `--resume` (22/22 kept). |
| 2026-09-29 | DR9 committed as `9399a42f`; its G1 press refused ("no after record") — the after capture had been resolved by digest into the before records and the reference arm's into A94's baseline evaluations and GR's pool record (§5 (2)). Chain stopped; branch reset to `f188d3db`; pool fix + tooth `f93d1df1`; DR9 cherry-picked as `e5137707`; 15 record directories stamped `9399a42f` removed; three seeded records restored byte-identical; G1 `before` re-made at `f93d1df1` (detached, clean). |
| 2026-09-29 | At `e5137707`: G1 PASS (`f93d1df1 → e5137707`), GC PASS (`copy → DR9`), copy gates PASS, run-free self-checks PASS, `self_containment` FAIL (inherited). DR9 straddle archived under `switch_neutrality/straddles/f93d1df1__e5137707/`; G1 `before` re-captured at `e5137707`. |
| 2026-09-29 | DR10 committed as `a0de2e13`; at `a0de2e13`: GC PASS (`DR9 → DR10`, rule `once_per_evaluation`), G2 PASS (re-formed, 3 teeth), copy gates PASS, self-checks PASS, `self_containment` FAIL (inherited). G1's first DR10 press with `--resume` kept the DR9 `after` capture and said so; re-pressed without `--resume`: PASS `e5137707 → a0de2e13`. Stamp survey: 132 records; the tree moved to `idf_probe/runs/v5_schedule_and_prime/` (0 changed, 0 lost). Report written. | |

---

## 11. Orchestrator's critical assessment (protocol §5) — verdict: merge, both driver changes

*Written 2026-09-29 by the orchestrating session under **D37** (autonomous mode: the driver changes DR9 and
DR10 merge on this assessment; the two diffs stand in §3 and §4 for the user's review on return). Checked
differently from the agent, not by repeating its presses.*

**Checked.** (1) `git diff --name-only 43d31a04..HEAD`: 14 files — under `PROCESS/` only `caller.py`,
`copy_gates.py`, `PROVENANCE.json`, `CHANGES.md`; **nothing under `process/models/`** (0 paths); the nine
harness files are exactly §6's list; the worktree is clean. (2) The two GC straddle records read from disk
(`gates/count_neutrality/straddles/copy__DR9.json`, `DR9__DR10.json`): 22 pairs, 3 985 leaves compared and
0 mismatched, 33 prime checks and 0 failing, 46 125 components and 0 differing, stamped `e5137707` and
`a0de2e13` respectively — the report's figures. (3) The latest verdict records: `count_neutrality` PASS
(straddles DR9 → DR10, `straddles_a_change: true`), `switch_neutrality` PASS (`e5137707 → a0de2e13`, a
neutrality result), `prime_map` PASS (5 026 / 0), `copy_identity` PASS (224 / 8, the permitted files),
`g0prime` PASS (77 / 1, the approved `pulse.py`), `resume_identity` PASS (170 / 0), `self_containment` FAIL
(54 / 1: V4's help-string line, I-32, fixed on the trunk by A98 (v5-reporting-trim) at `43ce80ab`, so the
merged tip is expected to PASS — A100 presses it). (4) The records tree is one tree of 435 MB at
`idf_probe/runs/v5_schedule_and_prime/` with `_press_logs/`.

**Read against the rulings.** DR9 is D31's fix as the user ruled ("this should be fixed in v5"); the
memoisation key (the figure of merit) is the one run-time input the resolution depends on, and GC's stamp
`n_resolutions = 1` on every deferring arm is the count that shows it. DR10 is item 8 as the user framed it
("pre-processing before the partitioned MDAs can start"): the prime at the head of `_call_models_inner`, once
per evaluation, the output path and the exit audit no longer priming; G2's two parts show the exit states
identical to the per-sweep form on 12 565 + 5 026 components. The abandonment of G3/G3c is Q3's ruling. The
I-29 fix in `pool.directory_for` (decision 2) is a harness correctness fix met on the gate itself, with a
tooth; **I-29 closes with it.** The branch reset the agent performed was on an unpushed task branch with the
abandoned commit's records removed and the seeded records restored byte-identical — the right recovery,
and recorded.

**Merge over A98.** A98 (merged `43ce80ab`) rewrote `registry.py`, trimmed `gate_prime.py` (G3/G3c removed)
and `gate_resume_identity.py` (G8 pairs), and touched `PROCESS_diff.py`; A99 rewrote `gate_prime.py` (G2
re-formed, G3/G3c removed), added the `count_neutrality` entry and removed `cold_chain` in `registry.py`, added
one tooth in `gate_resume_identity.py`, and annotated `PROCESS_diff.py`. Resolution rule: A99's
`gate_prime.py` whole (it contains A98's removal); A98's `registry.py` with A99's real `count_neutrality`
entry replacing A98's refusing placeholder and `cold_chain` absent; both changes in the other two files.
The merged tip is compiled and its run-free self-checks pressed by the orchestrator before the next task.

**Not pressed at this merge (the agent's decision 10, endorsed).** GR, G4–G7, G9 stand at their seeded
`d6c246a1` records; the schema change (`schedule_resolution`) re-makes their ~100 runs under `--resume`, and
that press belongs to the next driver task (A100 (v5-test-set)) at the merged tip, where it also validates
the A98 + A99 harness together — one press, not two.

**Queue consequences applied at merge.** I-29 closed (`f93d1df1`); I-30 closed (DR9); proposals 1 (the DR
rows: into the V5 plan §11, where V5's change map lives), 3, 4 and 6 to A100's brief; proposal 5 (the
pre-existing `PROCESS_diff.py` exit 1 at the copy commit and `CHANGES.md`'s missing A90 subsection) filed
as an issue.
