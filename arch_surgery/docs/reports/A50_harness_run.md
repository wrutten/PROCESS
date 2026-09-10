# A50 (harness-run) — the run path, and gate GR

> **Document status** — **OPEN**, awaiting the orchestrator's critical assessment (protocol §5).
> Written by task **A50 (harness-run)** on branch `A50-harness-run`, off `architecture_surgery` at
> `9a8defa6`. This report describes task **H3** of the approved V4 harness implementation plan: the
> run path, and **gate GR**, the check that the rewritten harness is the same instrument as the one
> it replaces. Nothing under `arch_surgery/MDA_partitioning_experiment_v4/PROCESS/process/` was
> changed by this task; gate GR ran against that copy exactly as `9a8defa6` left it, which is what
> makes its single-variable argument work.

---

## 1. The words, spelled out once

This project's shorthand is dense, and this report is meant to be readable without the queue open
beside it (protocol §4).

*Caption: one row per term; the meaning is the one this repository uses, not a general one.*

| term | meaning |
|---|---|
| **PROCESS** | the fusion power-plant systems code this repository forks: an optimiser wrapped around a loop that runs ~26 physics and engineering **models** until their outputs stop changing |
| **driver** | the arrangement of solvers and loops — `process/core/caller.py` and `process/core/solver/`. The experiment's *independent variable*; the models are frozen |
| **configuration** | one optimisation problem: `large_tokamak_nof` (nof), `low_aspect_ratio_DEMO` (lad), `st_regression` (st) |
| **input file** | the file a configuration is read from: the **committed** one, or its **lifted** derived copy in which the burn time has become an optimiser variable |
| **arm** | one setting of the driver's switches. Evaluation phase `AR A0 A0p A1`; optimisation phase `BR B0 B1 B3` |
| **seed** | which displaced starting point a run uses. Seed 0 is the *undisplaced* one, in both phases |
| **regime** | how a starting point is displaced: `perturbed` (the coupling state multiplied by `1 ± δ·u`) or `stencil` (the optimiser's own finite-difference point) |
| **coupling state** `y` | the measured set of state fields the in-loop models write: 840 / 846 / 827 components on the three configurations |
| **τ** (tau) | the one convergence tolerance every converger uses, per component, scaled. τ = 1e-6 (D23) |
| **node** / **node call** | one model call site inside the driver's sweep, and one execution of one. The cost unit |
| **sweep** | one pass over the node sequence |
| **the audit** | one further full sweep of the complete model set past termination, the same instrument in every arm, whose own model calls are never charged to the arm. It measures the accuracy an arm *achieved* |
| **deferral `per_call` / `per_run`** | running a node once per evaluation, or once in total at the accepted optimum, instead of once per sweep |
| **the prime** | executing the run-constant first-wall geometry method at the head of every sweep. Stamped, never pooled into node calls |
| **teeth** | a gate's demonstrated ability to fail: a deliberately broken input that must trip it before its zeros are believed (protocol §12) |
| **the previous revision** | `arch_surgery/MDA_partitioning_experiment_v3/` and the `idf_probe/` machinery it drove — the harness this task replaces. Its campaign ran at commit `362c0b47` |
| **D`<n>` / I-`<n>` / A`<n>` / T`<n>`** | a recorded user decision / a filed issue / a queue task / a recorded trap |

---

## 2. What this task was for, in one page

**The problem.** The V4 harness is a rewrite. A rewritten harness that changes the measurement is
not a rewrite, it is a new experiment — and it would change it *silently*, because a run under a
subtly different instrument still succeeds and still produces plausible numbers. The two files this
task replaces are the ones where that risk concentrates: the previous revision's optimisation-phase
run driver is 1 126 lines with a single 1 000-line `main()`, and its evaluation-phase driver is
another 996 lines carrying a parallel copy of the same six instruments. Merging them is the
harness plan's highest-value change and its highest-risk one, and the plan says so in those words.

**The answer.** One shared in-subprocess module and two thin entry points, and a gate that runs
**before any driver change** at the commit where the experiment's own copy of PROCESS was taken.
At that commit the copy *is* the driver the previous revision measured, so if the rewritten harness
drives it and reproduces the previous revision's recorded numbers, the only thing that changed
between the two sets of numbers is the harness, and it changed nothing. That is a single-variable
comparison and it is the whole argument the rewrite needs.

**The result.** GR PASSED: **20 of 20 runs reproduced, 270 of 270 compared values identical, no
tolerance on any of them**. All seven teeth tripped. Both substitutes for the arms the reference
cannot cover passed. Details and denominators in §5.

**What the run path exposed about the driver**, for the tasks that follow: the experiment plan's
declared audit position is not reachable against this driver and needs a driver-side hook, and three
quantities the plan's tables want are not counted by it yet. All four are recorded in every run
record as explicit nulls naming the change that will supply them, and are itemised in §7.

---

## 3. What was built

*Caption: one row per module added under `arch_surgery/MDA_partitioning_experiment_v4/harness/`.
"Lines" is `wc -l`. "Descends from" names the file it was derived from, read at `9a8defa6`; every
module's own docstring carries the same attribution, per the harness plan's §11.1 rule that
heritage lives in docstrings and never in an identifier.*

| module | lines | what it is | descends from |
|---|---:|---|---|
| `perturb.py` | 93 | the seeded displacement factor `1 + δ·u`, and the two streams built on it | `idf_probe/v2_eval_one.py::perturb_factor`; the local `_factor` inside `idf_probe/run_one.py` |
| `predicate.py` | 308 | the thin layer over `ystate.py`: spec rebuild with its sha re-checked, exact snapshot / restore / entry-state write, the cross-state residual | `idf_probe/a34_instruments.py::load_spec_offline`, `::_cross_residual`; `idf_probe/v2_eval_one.py`'s snapshot machinery |
| `records.py` | 555 | the record schema as data, the completeness contract, three refusals, the dotted-path resolver | the record `run_one.py` / `v2_eval_one.py` write; the previous revision's `phase_b.py` completeness check (its gate G7) |
| `failure.py` | 76 | which taxonomy row an exception belongs in, decided once | the classification scattered across `phase_a.py` and `phase_b.py` |
| `input_files.py` | 180 | resolve and sha-check the lifted input file (its *derivation* is A51's) | `idf_probe/a25_variant_deck.py`; `…_v3/v3_runner.py::deck_for` |
| `child.py` | 1 000 | everything that executes inside a measurement subprocess and is common to both phases | `idf_probe/run_one.py` and `idf_probe/v2_eval_one.py` / `a44_eval_one.py`, deduplicated |
| `optimise.py` | 428 | one full optimisation | `idf_probe/run_one.py` |
| `evaluate.py` | 646 | one evaluation of the model set, in both entry regimes | `idf_probe/v2_eval_one.py`; the stencil entry from `idf_probe/a44_eval_one.py` |
| `pool.py` | 415 | the only place a PROCESS run starts: jobs, isolation, the pool, resume | `…_v3/v3_runner.py::run_job`/`run_pool`; `…_v3/phase_a.py::run_eval_job` |
| `reproduction.py` | 1 082 | gate GR: the twenty runs, the comparison, the seven teeth, the two substitutes | the harness plan §7; the previous revision's warm-equivalence gate for the `A0p` substitute |
| **total, new** | **4 783** | | |

Plus, in existing files: `experiment_runner.py` gains a single-run mode and the gate stage (+146
lines); `selfcheck.py` gains a sixth check with nine teeth (+292); `reference.py`'s private
dotted-path resolver is delegated to `records.resolve_path` so there is one implementation of it
(+42/−41 including the note that says why); `README.md` and `__init__.py` follow.

### 3.1 The one thing that is genuinely new

Every instrument in `child.py` has a predecessor in the previous revision except one. The
per-evaluation census, which the previous revision used only to read net electric power at each
entry, now also **freezes the run's first evaluation** — its model executions, its sweeps, the
prime count and the objective hex. Nothing in the previous revision's records carries those, and
they are what the evaluation-phase reference arm `AR` is checked against, since `AR` has no prior
record at all (§6.2). Like every other instrument it is a pure read: it appends to a dict and takes
no branch a result depends on.

### 3.2 What was deliberately not carried across

*Caption: one row per capability of the previous revision's run drivers that this run path does not
have. "Why it can go" is what establishes it is unused, not an opinion about it.*

| dropped | why it can go |
|---|---|
| the four in-driver probe modes on the run path (`--mode baseline\|modules\|frozen\|harvest`) | the previous revision's campaign passed `--mode control` on every run, always. The census stage that needs the `modules` probe is task A51's, and is a stage of its own rather than a mode of the run path |
| `--exit-audit-at-call N` | never passed by that campaign; the plan fixes **one** audit position for every arm, and the run record now carries which one |
| the coupling-state artifacts of the generation before the frozen ruler | the previous revision resolved the current ones everywhere |
| composing the per-pass residual trace | never composed by that campaign. The variables are still **cleared** before every arm, because they are driver capabilities and an inherited value would change the run |

---

## 4. The record, as implemented

The record is the previous revision's, minus the dead, plus what the V4 plan requires, under the
harness plan §11.1 names. It is declared as **data** in `records.py` — a list of `Field(name,
phases, when, why)` — and both entry points fill that list rather than each building a dict inline.
That is the defect this module exists to prevent: the previous revision built its ~90 keys inline in
two files, so a field could be dropped from one and not the other and the omission would surface as
a missing table column months later.

*Caption: one row per change against the previous revision's `metrics.json`. Fields not listed are
carried unchanged.*

| change | fields | why |
|---|---|---|
| **renamed** | `v3_arm` → `campaign_arm`, `v3_deck` → `campaign_configuration`, `v3_seed` → `campaign_seed`, `v3_delta` → `campaign_delta`, `v3_tau` → `campaign_tau`, `v3_phase` → `campaign_phase`, `v3_machinery_smoke` → `campaign_run_kind`, `v3_pin_hex` → `campaign_pin_hex`, `v3_entry_state` → `campaign_entry_state` | harness plan §11.1: a field is named for what it holds, never for the revision that wrote it. `campaign_run_kind` generalises a boolean into `campaign \| gate \| smoke \| reference` |
| **dropped** | `mode`, `probe_env`, `probe_enabled`, `probe_mode`, `probe_module_present`, `probe`, `audit_at_call` | the probe modes and the call-indexed audit leave the run path (§3.2) |
| **added — identity** | `record_format`, `harness_version`, `runner`, `regime`, `campaign_input_file`, `campaign_input_file_kind`, `campaign_predicate_mode` | a record that does not say which schema, which harness, which entry point, which regime and which input file produced it cannot be read back safely |
| **added — provenance** | `tree_modified_tracked`, `tree_modified_tracked_n`, `tree_untracked_paths`, `tree_untracked_paths_n`, `process_copy_provenance` | the single "dirty" boolean counted untracked files, and a whole set of the previous revision's records was stamped dirty for that reason alone while the measured code was clean. `tree_git_dirty` survives, derived from the tracked half only. `process_copy_provenance` names the copied driver from the copy's own file, so a record names its code without depending on a working tree's git state |
| **added — environment** | `env_architecture` (**every** known switch variable and its value, in both phases), `switches_asked`, `resolved_switches`, `pending_switches_allowed` | the previous revision's evaluation-phase records carried a handful of variables, so a per-block table could not be read from the run's own record. `resolved_switches` is what the driver *resolved*, read back from the imported modules — never the environment echoed back |
| **added — audit** | `audit_position`, `audit_position_declared`, `audit_position_note` | a residual table whose arms were audited at different points, without saying so, is the thing that must not happen. Here the declared position is **not reachable** and the record says so rather than implying it was reached (§7.1) |
| **added — taxonomy** | `failure_class` ∈ `ok \| crashed \| refused \| unconverged \| unconverged-at-cap \| infeasible-at-audit \| machinery \| timeout \| no_record` | upstream's own loop raises after ten passes and a displaced entry may reach that cap: a **finding about the shipped code**, not a broken run. `machinery` is separate again, because a machinery failure was once published as "the reference arm did not converge" |
| **added — per attempt** | `attempts[]` (`attempt`, `stage`, `epsfcn`, `n_iterations`, `ifail`, `raised`, `node_calls_solve_phase`, `sweeps`), `attempts_node_calls_available` | the run total is a run total while the iteration count and the exit code are per attempt. The solver-owned half is filled; the cost half is explicit nulls naming DR7 / A60 (§7.2) |
| **added — first evaluation** | `first_call_models` (optimisation phase) | §3.1; it is what `AR`'s substitute is checked against |
| **added — nulls with reasons** | `predicate_evaluations`, `components_compared`, `output_path`, `output_loop_sweeps`, and each one's `*_null_because` | the plan's tables want them and the driver does not count them. A reader must be able to tell "the driver does not count this yet" from "the harness forgot to write it down" (§7.2) |
| **added — contract** | `completeness` | whether the record satisfies its own declared field list, written into the record rather than raised, because a record that fails its contract is more useful written down than lost |

**The completeness contract.** `records.assert_complete` refuses a record missing a declared field.
A field that is *present and null* is complete — "the optimiser did not run, and here is the null
that says so" is information; "the key is not there" is not. On top of the schema it binds the
previous revision's own completeness list (its gate G7): a finished optimisation record must carry
`n_solver_iterations`, `mfile.ifail`, the ladder stage, the constraint residual vector and the
active set, or a summary over it refuses.

---

## 5. Gate GR

### 5.1 What it is, and why it runs exactly once

GR compares this harness's runs against the compared field values of the previous revision's twenty
reference runs, committed by task **A49 (harness-reference)** in
`harness/reference/reproduction_reference.json`. It runs at the commit that carries the copied
driver and the rewritten harness and **before any driver change**, because after a driver change a
difference is no longer attributable to the harness alone. A later driver change is covered by its
own switch-neutrality gate and by the frozen-physics gate, not by this one.

The comparator reads `reference.REFERENCE_FIELDS` and `reference.lookup(arm, configuration, seed)`
rather than keeping a second transcription of the field list — A49's contract, and the reason is
that a comparator with its own copy of the list can compare a different set from the one the
reference was written with, invisibly.

**No tolerance anywhere.** Every compared value is a count or a hex float. That is not caution
about noise: it is the standing rule of this study that acceptance quantities are counts or
bit-comparisons, because a wall-clock-derived weight has been measured moving by half its own size
across runs of identical code.

### 5.2 The gate-only allowance, stated

Two arms — `B1` and `B3` — declare a switch that selects an output path without upstream's
output-time loop. **No tree implements it**: it is approved driver change DR2, task
**A57 (driver-output-path)**. The run path refuses any arm asking for a switch the tree does not
have, because running without it would be a successful run of a *different* arm under the right
name. But the previous revision's records for those two arms were made **before that switch
existed**, so reproducing them means running them the way they were run.

The allowance is therefore explicit and narrow, and is implemented in `pool.environment_for`:

- the terms allowed must equal **exactly** the terms this tree cannot implement. Allowing a term the
  tree *does* implement is a refusal, and so is failing to allow one it does not — both are teeth of
  the run-path self-check;
- the allowed terms are written into the gate's record **and into every run record it produces**
  (`pending_switches_allowed`), so a run made under the allowance says so;
- **the campaign passes none.** It composes through the same function with an empty allowance and is
  refused, which is what the run-path self-check demonstrates.

### 5.3 The twenty runs — every one reproduced

*Caption: one row per reference run of gate GR.  "Fields" is how many compared values that run's phase carries — 15 for an optimisation, 10 for an evaluation — and "mismatches" how many of them differ from the previous revision's recorded value.  No tolerance is applied to any of them: every value is a count or a hex float.  "Wall" is the child process's own elapsed time and is context only; no conclusion of this experiment rests on a timing.  Population: 20 runs (14 optimisations + 6 evaluations) over 3 configurations; 270 compared values, no tolerance on any of them.*

| arm | previous name | configuration | seed | phase | fields | mismatches | status | wall (s) |
|---|---|---|---:|---|---:|---:|---|---:|
| `BR` | `R` | large_tokamak_nof | 0 | B | 15 | 0 | ok | 18.4 |
| `BR` | `R` | low_aspect_ratio_DEMO | 0 | B | 15 | 0 | ok | 37.2 |
| `BR` | `R` | st_regression | 0 | B | 15 | 0 | ok | 16.7 |
| `B0` | `B0` | large_tokamak_nof | 0 | B | 15 | 0 | ok | 28.4 |
| `B0` | `B0` | low_aspect_ratio_DEMO | 0 | B | 15 | 0 | ok | 56.9 |
| `B0` | `B0` | st_regression | 0 | B | 15 | 0 | ok | 27.9 |
| `B3` | `B3` | large_tokamak_nof | 0 | B | 15 | 0 | ok | 30.8 |
| `B3` | `B3` | low_aspect_ratio_DEMO | 0 | B | 15 | 0 | ok | 48.6 |
| `B3` | `B3` | st_regression | 0 | B | 15 | 0 | ok | 27.4 |
| `A0` | `A0` | large_tokamak_nof | 1 | A | 10 | 0 | ok | 0.6 |
| `A0` | `A0` | low_aspect_ratio_DEMO | 1 | A | 10 | 0 | ok | 0.5 |
| `A0` | `A0` | st_regression | 1 | A | 10 | 0 | ok | 0.5 |
| `A1` | `A1` | large_tokamak_nof | 1 | A | 10 | 0 | ok | 0.6 |
| `A1` | `A1` | low_aspect_ratio_DEMO | 1 | A | 10 | 0 | ok | 0.5 |
| `A1` | `A1` | st_regression | 1 | A | 10 | 0 | ok | 0.4 |
| `B3` | `B3` | large_tokamak_nof | 1 | B | 15 | 0 | ok | 30.5 |
| `B3` | `B3` | low_aspect_ratio_DEMO | 1 | B | 15 | 0 | ok | 55.3 |
| `B3` | `B3` | st_regression | 1 | B | 15 | 0 | ok | 139.2 |
| `B1` | `B1` | large_tokamak_nof | 1 | B | 15 | 0 | ok | 29.7 |
| `B1` | `B1` | low_aspect_ratio_DEMO | 1 | B | 15 | 0 | ok | 56.5 |

### 5.4 The field-level summary

**270 of 270 compared values are identical. 20 of 20 runs reproduced. 0 mismatches.**

*Caption: the same comparison summed by phase.  "Values" is runs x fields; "identical" is values minus mismatches.  The two phases compare different field lists because the evaluation phase's records carry no optimiser fields — 15 fields per optimisation, 10 per evaluation.*

| phase | runs | fields each | values | identical | mismatched |
|---|---:|---:|---:|---:|---:|
| A (one evaluation) | 6 | 10 | 60 | 60 | 0 |
| B (one optimisation) | 14 | 15 | 210 | 210 | 0 |
| **both** | **20** | — | **270** | **270** | **0** |

And the records were put through their own contract separately, because a record can carry the
right numbers and still be missing a field a later summary needs: **20 of 20 records carry every
field the schema declares for their phase**, including the previous revision's own completeness
list.

### 5.5 The seven teeth — all tripped

*Caption: one row per tooth of gate GR (harness plan §7.3).  A tooth is a deliberately broken input that the gate must refuse; a gate whose teeth have never been shown to trip is an assertion rather than a measurement (protocol §12).  Population: 7 teeth, all of which tripped.*

| tooth | what was broken | tripped |
|---|---|---|
| count | BR/large_tokamak_nof/seed000: node_calls_solve_phase raised by one must not reproduce | yes |
| hex | BR/large_tokamak_nof/seed000: one character appended to exact.norm_objf must not reproduce | yes |
| missing reference | a reference file that does not exist must FAIL, not compare over an empty set (ReferenceError: the reproduction reference is not committed at /home/wrutten/projects/PROCESS_surgery_worktrees/A50-harness-run/arch_surgery/MDA_partitioning_experiment_v4/runs) | yes |
| missing key | a record with 'node_calls_solve_phase' removed must FAIL, not skip the field | yes |
| bad name map | the previous revision's records are named R, not BR; asking for BR without the map must RAISE (ReferenceError: 'BR' is not a name the previous revision's records carry; those are A0, A1, A1u, B0, B1, B2, B3, R.  'BR' is this revision's name for it; the previous revision ) | yes |
| composition | B3 on st_regression run with PROCESS_ARCH_OUTER cleared — so the verified schedule ran under the partitioned arm's name — must not reproduce the previous revision's B3.  8 of 15 compared values differ | yes |
| attempt summation | 400 + 550 = 950 against a run total of 1000 must be REFUSED (RecordError: per-attempt node calls do not sum to the run total for a tooth: 400 + 550 = 950, node_calls_solve_phase = 1000.  REFUSED: the cost ratio published with and with) | yes |

**The composition tooth is the one worth reading twice.** It is the positive control: it proves
the gate is sensitive to *which arm ran*, not merely to whether a run finished. Running `B3` on
`st_regression` with `PROCESS_ARCH_OUTER` cleared makes the driver resolve its **default** schedule
— the one that repeats the block pass while anything is still moving — under the partitioned arm's
name. The run finished normally, `status: ok`, and the record shows the driver resolved
`OUTER_MODE = "verify"` rather than `"trust"`. **8 of the 15 compared values differ**:
`node_calls_solve_phase`, `node_calls_total`, `n_model_calls`, `n_prime_calls`,
`exact.norm_objf`, `module_solve_totals.block_sweeps`, `module_solve_totals.outer_pass_hist` and
`module_solve_totals.inner_sweeps_by_block`. That is exactly the failure mode this whole package is
shaped around — a successful run of a different arm under the right name — and the gate catches it.

### 5.6 The two substitutes, and what each can and cannot say

**`A0p` — the flat arm with a constant owning the burn time.** No earlier record exists: the
previous revision only ever pinned its *partitioned* arms. The check applied instead is the
construction that revision already used for those arms: enter from the reference's exit state, pin
the burn time at the reference's own converged value, and require the run to land back on the
reference fixed point.

*Caption: the substitute for `A0p`, the arm no earlier record covers.  Each row is one configuration; the criterion is the one quoted in the row above the table.  "Cross-state max" is the largest scaled residual between the arm's exit state and the reference's, over the coupling state's tested components; the tolerance is 1e-6.  Population: 2 pulsed configuration(s); 1 skipped with the reason recorded.*

| configuration | pin (hex) | cross-state max | as hex | argmax | above τ | categorically clean | pinned component identical | verdict |
|---|---|---:|---|---|---:|---|---|---|
| st_regression | — | — | — | — | — | — | — | skipped: steady state (no burn-time coupling): A0p composes to A0 |
| large_tokamak_nof | `0x1.41043caef8d92p+11` | 1.53e-08 | `0x1.075590f13be91p-26` | `costs.coecap` | 0 | True | True | PASS |
| low_aspect_ratio_DEMO | `0x1.44eb0e25837b3p+13` | 0 | `0x0.0p+0` | `blanket.deg_blkt_inboard_poloidal_plasma` | 0 | True | True | PASS |

Both pass with room to spare. On `large_tokamak_nof` the largest scaled residual between the
pinned arm's exit state and the reference's is **1.53e-08**, which is 65x below the tolerance of
1e-6, with **0 components above it** out of the coupling state's tested set, nothing out of its
category, and the pinned component bit-identical. On `low_aspect_ratio_DEMO` the residual is
**exactly 0.0** — the arm lands on the reference's bits. `st_regression` is a steady-state
configuration with no burn-time coupling, so the arm composes onto its predecessor and is recorded
as skipped with that reason, not silently absent.

**`AR` — one evaluation with every architecture switch cleared.** No earlier record exists at all:
the previous revision had no evaluation-phase reference arm.

*Caption: the substitute for `AR`, the arm no earlier record covers.  Each row is one configuration; the anchor is this gate's own `BR` run at seed 0 on that configuration, whose first evaluation of the model set the arm must reproduce exactly.  Four values per configuration, no tolerance.  Population: 3 configuration(s) x 4 values = 12 compared values, no tolerance.*

| configuration | node calls (AR / first call of BR) | sweeps | prime calls | objective hex | mismatches |
|---|---|---|---:|---|---:|
| large_tokamak_nof | 126 / 126 | 6 / 6 | 0 | `0x1.999999999999ap+0` | 0 |
| low_aspect_ratio_DEMO | 105 / 105 | 5 / 5 | 0 | `-0x1.0a2c4835ab329p-1` | 0 |
| st_regression | 126 / 126 | 6 / 6 | 0 | `-0x1.4d595f9d6a057p+5` | 0 |

**The weaker form, stated plainly.** This substitute is anchored on **this gate's own** `BR` runs,
not on the previous revision's records — because no record of that revision carries the first
evaluation's own quantities. Its optimisation-phase record reports run totals and a *binned
distribution* of sweeps per evaluation; the first call's node count, sweep count and objective are
not in it, and cannot be recovered from it. What can be said is: the anchor is itself one of the
twenty runs compared field for field against that revision, and it reproduced. What cannot be said
is that the first-call numbers themselves were reproduced from a prior record. There is no prior
record of them, and this report does not imply otherwise.

### 5.7 Wall time, as context only

The whole gate — **30 runs** (3 evaluation-phase reference runs, the 20 reference runs, 2 for the
`A0p` substitute, 3 for the `AR` substitute, 1 for the composition tooth, and one record copied on
disk for the missing-key tooth) — took **324 s** at 3 workers, from the first run's launch to the
verdict being written. The runs' own in-child elapsed times sum to **664 s**. The harness plan
estimated "roughly an hour and a half at W = 3" from the previous revision's timings; this was an
order of magnitude quicker, on an otherwise idle machine and without that revision's in-driver probe
on the path.

**None of that is evidence of anything** and no conclusion here rests on it. It is reported because
a run that takes ten times as long as its neighbours is worth looking at, and because a reader
planning the campaign needs a cost estimate. Acceptance is on the counts and the bit-comparisons
above.

### 5.8 How to re-derive every number in §5

Every figure above comes from executing a committed script (protocol §15). The gate itself ran at
commit `2570ec2b`, before `--tables` was added; the verdict record was **re-derived byte for byte
from the same run records at `f13a0e3a`** with `--resume`, which re-runs nothing, so the tables
below and the gate that produced them are at the same commit.

```bash
PY=/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python
cd arch_surgery/MDA_partitioning_experiment_v4

# the harness's own gates, no PROCESS run  (6/6 PASS, 27 teeth: 4 + 3 + 3 + 4 + 4 + 9)
$PY experiment_runner.py --selfcheck

# the committed reproduction reference re-derives from the previous revision's records
$PY experiment_runner.py --reference verify \
    --previous-runs /home/wrutten/projects/PROCESS_surgery/arch_surgery/MDA_partitioning_experiment_v3/runs

# gate GR itself: about 30 runs
$PY experiment_runner.py --gate reproduction \
    --lifted-from /home/wrutten/projects/PROCESS_surgery/arch_surgery/MDA_partitioning_experiment_v3/runs/_decks

# the same verdict re-derived from the records already on disk, running nothing
$PY experiment_runner.py --gate reproduction --resume

# the tables of this section, from the committed verdict record
$PY harness/reproduction.py --tables
```

Records go to `arch_surgery/MDA_partitioning_experiment_v4/runs/gates/reproduction/`, which is
untracked. The verdict record is `gate.json` there; its content is what §5's tables quote.

`--lifted-from` is needed only until task **A51 (harness-artifacts)** builds the derivation of the
lifted input file. It stages the previous revision's derived files **after checking their bytes
against the two digests committed in `harness/input_files.py`**, so gate GR runs the same problem
that revision ran, proven rather than assumed. A51's own gate is those two digests.

---

## 6. What the run path exposed about the driver

These are findings, not defects this task fixed: `…_v4/PROCESS/process/` is not this task's to
change, and gate GR only means what it means because that tree is exactly as `9a8defa6` left it.
Each is recorded in **every run record** as an explicit null or a stated position with the reason
and the task that will resolve it — never as an absent key, so a reader can tell "the driver does
not do this yet" from "the harness forgot to write it down".

*Caption: one row per thing the plan asks of a run record that this driver cannot supply. "Where it
shows" is the field a reader sees; "for" names the queued task.*

| # | what the plan wants | what this driver does | where it shows in the record | for |
|---|---|---|---|---|
| 1 | the exit audit taken **at the entry to `write_output_files`**, before any output-time sweep, in every arm | **not reachable.** The audit sweep mutates the state it measures, so taking it there hands the output path a state the optimiser never accepted — the output files, the exit code and the total node count would all be of the *audited* state. It would also sit **before** the per-run deferred nodes, which the driver runs inside that same function. Reaching the declared position needs a driver-side hook that audits a copy of the data structure, or an output path that does not re-solve so that "after the run" *is* the accepted point | `audit_position` = `after_run` (optimisation) / `after_single_evaluation` (evaluation), `audit_position_declared`, `audit_position_note` | **A57 (driver-output-path)** |
| 2 | node calls and the sweep histogram stamped **at each retry-ladder attempt boundary** | stamped once, at the end of the run. The solver-owned half of each attempt — ladder stage, finite-difference step, iterations, exit code — is recorded by the harness's own wrap; the cost half cannot be | `attempts[].node_calls_solve_phase` = null, `attempts[].sweeps` = null, `attempts[].cost_null_because`, `attempts_node_calls_available` = false | **A60 (driver-attempts)** |
| 3 | counters for predicate evaluations and components compared | not counted | `predicate_evaluations` = null, `components_compared` = null, `predicate_counters_null_because` | **A58 (driver-predicate-counters)** |
| 4 | a switch selecting an output path without the output-time loop, and that loop's sweep count | one output path, and its sweeps are not counted separately | `output_path` = `mda_output` on every optimisation record, `output_loop_sweeps` = null, `output_loop_null_because`; and the gate-only allowance of §5.2 | **A57 (driver-output-path)** |

Two further observations, both small and both worth a line in the task that touches them:

**The partitioned arms still need `PROCESS_ARCH_OUTER` explicitly.** The composition tooth measured
what happens without it: the driver resolves `OUTER_MODE = "verify"`, its default, which is the
schedule V4 has no arm for. The switch registry already marks the name as one that disappears
rather than one that is renamed, and `arms.terms` composes it as a *consequence* of choosing the
partitioned loop rather than as a per-arm declaration. **A56 (driver-renames)** folds it into the
partitioned value; until then the tooth is the evidence that it is load-bearing.

**A driver refusal is currently distinguishable only by the text of its message.** `failure.py`
classifies a run as `refused` rather than `crashed` by matching sentence fragments the driver
itself writes ("is not a recognised…", "two owners…", "must refuse rather than…"). That works and
is checked, but it is brittle in a way a typed exception would not be: a reworded refusal lands the
run in `crashed` — visibly, since the taxonomy row and the traceback are both recorded, but in the
wrong row. If **A56 (driver-renames)** is touching those raises anyway, a single
`ArchitectureRefusal(RuntimeError)` class in the copy would make the classification exact.

**One divergence from the previous revision that GR does not cover, measured rather than assumed.**
The previous revision handed its *restricted* audit statistic the per-run deferral artifact stamped
for the lifted constraint set, while handing the arm's environment the one stamped for the base
set — two different files for the same decision. This run path uses one file, the one the arm's
environment actually names. It changes nothing: the two artifacts' node lists are **identical**
(`vacuum`, `water_use`, `costs` on both pulsed configurations), so the derived excluded set and
therefore the restricted statistic are unchanged. This is stated because the restricted statistic is
not among GR's compared fields, so the gate is silent about it and a reader should not infer
coverage it does not have.

---

## 7. Autonomous decisions, each with the way back

*Caption: one row per decision this task took without asking. "Reversal" is what undoing it costs,
concretely.*

| # | decision | why | reversal |
|---|---|---|---|
| 1 | The exit audit is taken at the position the driver allows, and the record carries **both** the position used and the position declared | §6 row 1. The alternative — taking it at the declared position anyway — would corrupt the output files and the cost figure of every optimisation run | A57 adds the hook; `AUDIT_POSITION` in `optimise.py` and the position argument in `child.take_exit_audit` change, and `records.AUDIT_POSITIONS` already names the value |
| 2 | `harness/input_files.py` was created here, resolving and sha-checking the lifted input file but **not deriving it** | GR runs two arms that read it, and the derivation needs a PROCESS run and is task A51's. Deriving it here would also put a second variable into a comparison whose whole argument is that only the harness changed | A51 adds `derive_lifted` to the same module; the two committed digests become its gate, which is what its queue row already asks for |
| 3 | `reference._resolve` now delegates to `records.resolve_path` | two implementations of "how a dotted field name is resolved" is the shape D14(c) exists to prevent: a path that resolved for the gate and not for the reference would report a mismatch that is neither side's number | two lines; the implementation is A49's, moved unchanged, and `--reference verify` re-derives the committed file byte for byte after the move |
| 4 | A driver refusal is classified from its message text (`failure.py`) | there is no typed refusal in the driver to catch, and the driver is not this task's to change | §6; a typed exception class in the copy makes it exact |
| 5 | `first_call_models` added to the optimisation-phase record | `AR` has no earlier record and cannot be checked against one; without this field it cannot be checked against anything | delete the block in `child.install_call_models_census`; `AR`'s substitute then has no anchor |
| 6 | The gate-only allowance (`Job.allow_pending`) with **set equality**, not a permissive flag | reproducing the previous revision's `B1` / `B3` records means running them as they were run, and the switch they now declare did not exist then. Set equality is what stops it from becoming a general escape hatch | when DR2 lands (A57), `reproduction.GATE_ALLOWANCE` becomes empty and the mechanism is inert; the two teeth in the run-path self-check keep it honest meanwhile |
| 7 | Pool-width override renamed `V3_WORKERS` → `HARNESS_WORKERS` | §11.1: no revision token in a name. The width used is stamped per stage either way | one constant, `pool.WORKERS_VARIABLE` |
| 8 | The run path's checks went into `selfcheck.py` as a sixth check rather than waiting for the gate framework | they are cheap, they have teeth, and a run path with no demonstrated refusals is an assertion | A52 promotes them into `gates.py`; the criteria move unchanged |
| 9 | `records.read` returns a `no_record` taxonomy row for an absent or unreadable record rather than raising | a crashed subprocess that wrote nothing is a taxonomy row; turning it into an exception is how a class of failures once left a tally silently | one function |
| 10 | The harness version was bumped `0.1.0` → `0.2.0` and is stamped in every record | the public surface and the record schema both changed, and its own docstring says that is when it moves | one constant |
| 11 | The three evaluation-phase reference runs are launched in the pool rather than serially | they are independent of each other; only the runs *entered from* them are ordered after them, which the stage enforces by running them first | one call in `reproduction.stage` |
| 12 | The per-run job timeout stays at the previous revision's 5 400 s, and reaching it is a `timeout` taxonomy row, never a re-run at a longer limit | a budget that is raised until the run fits is not a budget | `pool.DEFAULT_TIMEOUT_S` |

---

## 8. What the later tasks must fill in

*Caption: one row per queued task, and what this task leaves for it. "Handover" is the concrete
thing, not a description of the task.*

| task | handover |
|---|---|
| **A51 (harness-artifacts)** | the **derivation** of the lifted input file, whose gate is the two digests committed in `harness/input_files.py`; `artifacts.py`'s validation of the committed per-configuration artifacts; `census.py`; `postsolve.py`'s class-level classifier. Note §6's last paragraph: this run path hands the restricted audit the per-run artifact the arm's environment names, and the two artifacts' node lists are identical, so nothing moves |
| **A52 (harness-gates)** | `gates.py`, and the registration of `reproduction.py` as gate GR and of `selfcheck.check_run_path` as its own gate. GR's comparator, its teeth and its two substitutes are already inside `harness/`; nothing in the run path imports from, or starts a subprocess into, the earlier revisions' directories |
| **A53 (harness-tally)** | the schema is data (`records.SCHEMA`) and the completeness contract is a function (`records.assert_usable`); a tally should read records through them rather than reaching into the dict. `attempts[]` exists and its cost half is null until A60, so the "with and without retried seeds" ratio is only computable after that task |
| **A54 (harness-analysis)** | the same, from the same records; `records.resolve_path` is the one field resolver both should use |
| **A55 (harness-smoke)** | `experiment_runner.py --run` is the one-run entry point, and `pool.run` refuses a campaign record against anything but the experiment's own copy. A one-seed end-to-end pass needs only the tally and analysis stages above it |
| **A56–A60 (the driver chain)** | §6's four rows, plus the two observations under it. Each is already a null with a reason in every record, so a driver change lands by filling a field rather than by adding one |

---

## 9. Change log

*Caption: one row per commit on `A50-harness-run`, in order.*

| commit | what |
|---|---|
| `196d4984` | `perturb.py`, `predicate.py`, `records.py`, `failure.py`, `input_files.py`; `reference._resolve` delegated to `records.resolve_path` |
| `92672c34` | `child.py`, `optimise.py`, `evaluate.py` — the shared in-subprocess driver and the two entry points |
| `4d0fbea8` | `pool.py`, the runner's single-run mode and gate stage, and the run path's self-check with nine teeth |
| `2570ec2b` | `reproduction.py` — gate GR, its seven teeth and its two substitutes. **Gate GR ran at this commit** |
| `f13a0e3a` | `reproduction.py --tables`, the formatter that emits §5's tables from the committed verdict record. The verdict was re-derived from the same records at this commit with `--resume` and is byte-identical |
| *(this commit)* | this report |

---

## 10. Loose ends and things a reviewer should look at

1. **The `AR` substitute's weaker form** (§5.6). It is anchored on this gate's own runs because no
   earlier record carries the quantity. That is stated in the gate's own record, in the module's
   docstring and here, but it is the one place where GR's argument is internal rather than against
   a prior measurement.
2. **The audit position** (§6 row 1). The experiment plan's §3.3 states the declared position as
   binding. This task cannot reach it and says so; whether the plan's sentence should be amended,
   or A57 should carry the obligation, is the orchestrator's call.
3. **Two of the twenty records carry `tree_untracked_paths_n = 1`** — a draft of this report that
   existed beside the runner for about two minutes while the gate ran. Every record has
   `tree_modified_tracked_n = 0` and `tree_git_dirty = false`, which is exactly the split the
   provenance module introduced after a whole set of the previous revision's records was stamped
   dirty for that reason alone. It is reported rather than tidied away because it is a live
   demonstration that the split works: an untracked file is context, and only a modified tracked
   file marks the tree dirty.
4. **The restricted-audit artifact divergence** (§6, last paragraph). Measured to change nothing,
   but outside GR's compared fields.
5. **`harness/input_files.py` is arguably A51's file.** It was created here because gate GR needs
   it; if the orchestrator would rather it be a private helper of `reproduction.py` until A51,
   moving it is a rename.

---

## 11. Orchestrator's critical assessment (protocol §5) — 2026-09-10

*Appended by the orchestrating session before merge, against the report at `d49ff1b5` and the
package on the same branch. The gate was re-run by the orchestrator, not read off the report.*

**Verified independently.** (1) **Gate GR re-run from scratch** into a fresh records directory
(`experiment_runner.py --gate reproduction --lifted-from <the main checkout's …_v3/runs/_decks>`):
30 PROCESS runs, **20 of 20 reproduced, 270 of 270 compared values identical, 0 mismatched**; the
record contract 20 of 20; substitute `A0p` PASS on both pulsed configurations with `st_regression`
skipped for the recorded reason; substitute `AR` PASS, 12 of 12 values; **seven teeth tripped**,
the composition positive control among them (`B3` on `st_regression` with `PROCESS_ARCH_OUTER`
cleared does not reproduce). The re-run's per-run wall clock was of the same order as the report's
(context only). (2) `experiment_runner.py --selfcheck` against the copy: six checks PASS;
`--reference verify` PASS; `PROCESS/copy_gates.py all` ALL GATES PASS. (3) Scope: sixteen files,
all under `…_v4/` plus this report; `git diff 9a8defa6..HEAD -- …_v4/PROCESS process` is empty —
the copy is byte-untouched, which is the premise of GR's single-variable argument. (4) Nothing
under `harness/` imports from, or starts a subprocess into, `idf_probe/`, `fixedpoint/` or `…_v3/`
at run time; the mentions found are heritage docstrings, the reference stage's default records
root and the opt-in cross-check already assessed at A47. (5) The gate-only allowance
(`Job.allow_pending`) is guarded in `pool.py`, `reproduction.py` and the runner by set equality and
by `Campaign.is_experiment_copy`, and is stamped in every run record.

**Endorsed.** The composition tooth is the strongest thing in the gate: it measured that the
partitioned arms still depend on `PROCESS_ARCH_OUTER` (the driver defaults to the verified
schedule without it, and 8 of 15 values move), so the switch the registry lists as disappearing is
load-bearing until A56 folds it into `partitioned`. Taking the `AR` substitute in its weaker form
and saying so, rather than implying a reproduction against a record that does not carry the
quantity. One dotted-path resolver shared by the reference and the comparator (D14(c)'s shape).
Recording every driver capability the plan asks for and this driver lacks as an explicit null with
a reason and the task that supplies it, so a tally cannot mistake "not yet" for "forgot". The
`first_call_models` field, without which `AR` could be checked against nothing.

**Limits I hold it to.** (a) GR's argument is complete only for the six arms V3 ran; `A0p` and
`AR` are covered by internal consistency, as §7.5 of the harness plan declares. (b) The lifted
input files GR ran were staged from V3's untracked `_decks/` after a digest check against the two
sha256s committed in `input_files.py`; the derivation that reproduces those digests is A51's, and
until it lands the digests are the only thing standing between GR and a lifted file nobody derived.
(c) The exit audit is taken after the run, not at the plan's declared position — see the ruling
below; GR is unaffected because V3 audited at the same place, which the matching
`exit_audit.residual_max_hex` values confirm. (d) The five-hour-per-run timeout and the
three-worker pool are the previous revision's settings, kept, not re-derived.

**Rulings and consequences drawn (orchestrator, today).** *Audit position (§6 row 1, §10 item 2):*
the plan's §3.3 stands — the accuracy compared across arms is the accuracy the *solve* delivered,
before any output-time sweep re-solves it on the arms that keep that loop. The implementation the
plan did not spell out is a **snapshot** of the coupling state at the entry to `write_output_files`,
with the residual computed after the run from the restored snapshot, so nothing the run writes is
touched by the audit sweep; the snapshot hook is a driver change in the copy and lands with **A57
(driver-output-path)**, which restructures that function anyway. Until then every record carries
both `audit_position` and `audit_position_declared`, as this task already does. §3.3 is amended to
say so. *`input_files.py`* stays where it is; A51 adds the derivation to it. *Typed refusal:* A56
(driver-renames) adds an `ArchitectureRefusal(RuntimeError)` to the copy and `failure.py` catches
the type; the message-text match is kept as the fallback for one release and then removed. *The
restricted-audit artifact divergence:* measured to change nothing, recorded here, no action.
A51 (harness-artifacts) and A56 (driver-renames) are dispatched in parallel off the merged tip —
disjoint files (`harness/` stages vs the copy and `switches.REGISTRY`).

**Verdict.** Fit to merge; nothing returned. The rewritten harness is, on every quantity the plan
compares, the same instrument as the one it replaces.
