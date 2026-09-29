# A91 (block-sweep-timing) — how long one sweep of each block takes

> **Document status** — **MERGED 2026-09-29** at `73793603` (`--no-ff`); archived here at merge — folder position records
> lifecycle, not validity (trap T3). Records: `arch_surgery/idf_probe/runs/A91_runs/block_sweep_timing/` (the worktree's
> `arch_surgery/idf_probe/runs/`, relocated whole by the retire script; every path below reading
> `arch_surgery/idf_probe/runs/block_sweep_timing/` means this location). Orchestrator's assessment at the end; its finding
> is issue I-30. Originally: **OPEN.** Task **A91 (block-sweep-timing)**, branch `A91-block-sweep-timing`
> (worktree `.claude/worktrees/A91-block-sweep-timing`, no records seeded — fresh evaluation runs
> only), base **`c2ac4077`**, tip **`c821dbd6`** — the last commit that touches code or a generated
> document, and where every number this report cites was produced (the entry and reference records,
> which carry counts and bit-exact states only, were made at `dfbf3749`; every timing was taken at
> `c821dbd6`; the tables were rendered at `c821dbd6`). Records: `arch_surgery/idf_probe/runs/block_sweep_timing/`
> in the worktree (untracked). **Every timing in this document is context, never evidence** (CLAUDE.md):
> no conclusion below rests on one, and §7 says what would.

The user, 2026-09-29: *"survey the wallclock time of individual module sweeps — I want to know roughly how
long each block takes."*

## 0. Verdict

**One sweep of block M1 (physics) or M2 (coils) costs about 3 ms of model time; one sweep of M3 (plant)
about 0.6–0.8 ms; the block's convergence test adds 1.3–1.6 ms per sweep on top of the sweep; the
dispatch walk of `_sweep_block` adds under 0.1 ms per sweep.** These figures are the same in the
partitioned arm and in the flat arms (where they are the node time per flat sweep of the block's member
nodes), so a block sweep costs what its nodes cost. Two things that are *not* per-sweep costs dominate
everything else: the whole-`y` residual (3.9 ms per flat sweep, ~4.7 µs per component tested, so a
block's narrower test is proportionally cheaper), and — new here — **`module_schedule` costs 8.7–9.3 ms
per evaluation in every arm that defers per call (`A0`, `A2`)**, because it re-reads the committed write
sets and re-walks the objective and constraint source on every `call_models`. That single per-evaluation
cost is 15 % of an `A2` evaluation and three M2 sweeps' worth; it is implementation, not architecture.
A89 §7.5's hypothesis that the partitioned arm pays a *per-sweep* dispatch cost 12–15 times is **not
supported**: measured, that cost is 0.08–0.09 ms per block sweep — 3 % of an M1 or M2 sweep, 10–13 % of
an M3 sweep (whose models are cheap), 1.5–1.7 % of a flat sweep.

Verdict table — one row per configuration and block of the partitioned arm's schedule; ms per block sweep,
median [min, max] over 7 timed repetitions of one displaced evaluation (τ = 1e-6, whole-`y` test,
displaced entry seed 1; the survey press, §3.5); "model" is the sum of the node calls inside the sweep,
"test" the coupling-state read plus residual charged to the block per sweep, "dispatch" the sweep's wall
clock less model, split in §3.3. The two flat columns are the node time per FLAT sweep of the nodes the
committed node map assigns to the block, in V4's control (`A0v4`) and A89's deferring control (`A0`), with
their node calls per sweep in brackets. Rendered by `run_survey.py --summarise` at `c821dbd6`
(`survey_tables.md`, "Verdict table").

| configuration | block | A2 sweeps | A2 node calls per sweep | A2 sweep wall | A2 model (Σ node) | A2 test (read + residual) | A2 dispatch (x inject + fw geometry + other) | A2 sweep + test | A0v4 members per FLAT sweep (calls) | A0 members per FLAT sweep (calls) |
|---|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | M1 | 4 | 2 | 2.94 [2.86, 3.14] | 2.84 [2.77, 3.03] | 1.52 [1.46, 1.69] | 0.092 [0.085, 0.107] | 4.46 [4.32, 4.73] | 2.84 [2.69, 3.31] (2) | 2.89 [2.68, 3.03] (2) |
| large_tokamak_nof | M2 | 5 | 3 | 2.92 [2.84, 3.00] | 2.84 [2.76, 2.92] | 1.38 [1.36, 1.40] | 0.083 [0.081, 0.090] | 4.28 [4.20, 4.40] | 2.89 [2.74, 3.79] (3) | 2.92 [2.77, 3.23] (3) |
| large_tokamak_nof | M3 | 3 | 12 | 0.67 [0.64, 0.69] | 0.58 [0.56, 0.60] | 1.27 [1.26, 1.38] | 0.083 [0.081, 0.091] | 1.95 [1.91, 2.07] | 0.66 [0.64, 0.75] (13) | 0.60 [0.54, 0.66] (12) |
| large_tokamak_nof | FF | 1 | 1 | 0.08 [0.08, 0.09] | 0.01 [0.01, 0.01] | 0.00 [0.00, 0.00] | 0.072 [0.070, 0.081] | 0.08 [0.08, 0.09] | 0.10 [0.08, 0.13] (2) | — |
| large_tokamak_nof | ONCE_PER_RUN | 1 | 3 | 0.24 [0.24, 0.31] | 0.18 [0.17, 0.25] | 0.00 [0.00, 0.00] | 0.065 [0.064, 0.067] | 0.24 [0.24, 0.31] | — | — |
| large_tokamak_nof | *A0v4 FLAT sweep (all nodes)* | 6 | 21 | 6.59 [6.30, 8.14] | 6.47 [6.19, 7.96] | 4.11 [4.06, 4.58] | 0.114 [0.105, 0.176] | 10.75 [10.39, 12.72] | — | — |
| large_tokamak_nof | *A0 FLAT sweep (all nodes)* | 6 | 18 | 6.51 [6.10, 7.10] | 6.39 [6.00, 6.94] | 4.22 [4.04, 4.64] | 0.113 [0.099, 0.169] | 10.80 [10.14, 11.75] | — | — |
| low_aspect_ratio_DEMO | M1 | 4 | 2 | 2.91 [2.87, 3.07] | 2.82 [2.78, 2.97] | 1.54 [1.51, 1.66] | 0.093 [0.085, 0.102] | 4.44 [4.39, 4.69] | 2.79 [2.71, 3.07] (2) | 2.94 [2.73, 3.31] (2) |
| low_aspect_ratio_DEMO | M2 | 5 | 3 | 3.21 [3.00, 3.58] | 3.11 [2.92, 3.47] | 1.49 [1.37, 1.64] | 0.093 [0.080, 0.121] | 4.63 [4.37, 5.20] | 2.95 [2.87, 3.12] (3) | 3.15 [3.06, 3.36] (3) |
| low_aspect_ratio_DEMO | M3 | 3 | 12 | 0.70 [0.67, 1.03] | 0.61 [0.58, 0.93] | 1.33 [1.25, 1.63] | 0.091 [0.080, 0.110] | 2.03 [1.92, 2.48] | 0.65 [0.60, 0.71] (13) | 0.61 [0.56, 0.67] (12) |
| low_aspect_ratio_DEMO | FF | 1 | 1 | 0.08 [0.08, 10.60] | 0.01 [0.01, 0.02] | 0.00 [0.00, 0.00] | 0.071 [0.068, 10.577] | 0.08 [0.08, 10.60] | 0.09 [0.08, 0.15] (2) | — |
| low_aspect_ratio_DEMO | ONCE_PER_RUN | 1 | 3 | 0.27 [0.24, 0.33] | 0.21 [0.18, 0.26] | 0.00 [0.00, 0.00] | 0.064 [0.062, 0.073] | 0.27 [0.24, 0.33] | — | — |
| low_aspect_ratio_DEMO | *A0v4 FLAT sweep (all nodes)* | 5 | 21 | 6.61 [6.37, 7.19] | 6.51 [6.27, 7.05] | 4.12 [4.04, 4.39] | 0.105 [0.099, 0.155] | 10.75 [10.41, 11.57] | — | — |
| low_aspect_ratio_DEMO | *A0 FLAT sweep (all nodes)* | 5 | 18 | 6.79 [6.48, 7.37] | 6.67 [6.38, 7.26] | 4.26 [4.07, 4.34] | 0.116 [0.103, 0.134] | 11.05 [10.55, 11.54] | — | — |
| st_regression | M1 | 4 | 2 | 3.07 [2.80, 3.18] | 2.99 [2.73, 3.07] | 1.58 [1.52, 1.73] | 0.083 [0.068, 0.107] | 4.65 [4.31, 4.90] | 3.00 [2.83, 3.28] (2) | 2.92 [2.75, 2.98] (2) |
| st_regression | M2 | 6 | 3 | 3.08 [2.87, 3.44] | 3.00 [2.80, 3.36] | 1.28 [1.20, 1.41] | 0.076 [0.069, 0.085] | 4.34 [4.10, 4.78] | 2.89 [2.76, 3.42] (3) | 2.98 [2.73, 3.12] (3) |
| st_regression | PULSE | 1 | 0 | 0.06 [0.06, 0.08] | 0.00 [0.00, 0.00] | 0.16 [0.15, 0.26] | 0.062 [0.060, 0.080] | 0.23 [0.21, 0.32] | 0.00 [0.00, 0.00] (1) | — |
| st_regression | M3 | 3 | 12 | 0.78 [0.75, 0.93] | 0.70 [0.69, 0.84] | 1.26 [1.22, 1.53] | 0.075 [0.066, 0.086] | 2.02 [1.99, 2.46] | 0.75 [0.70, 1.00] (13) | 0.72 [0.65, 0.80] (12) |
| st_regression | FF | 1 | 0 | 0.06 [0.06, 0.08] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.059 [0.056, 0.080] | 0.06 [0.06, 0.08] | 0.09 [0.08, 0.14] (2) | — |
| st_regression | ONCE_PER_RUN | 1 | 4 | 0.23 [0.22, 0.32] | 0.18 [0.17, 0.27] | 0.00 [0.00, 0.00] | 0.054 [0.051, 0.066] | 0.23 [0.22, 0.32] | — | — |
| st_regression | *A0v4 FLAT sweep (all nodes)* | 6 | 21 | 6.93 [6.49, 7.83] | 6.82 [6.40, 7.70] | 4.18 [4.06, 4.83] | 0.104 [0.089, 0.135] | 11.07 [10.55, 12.59] | — | — |
| st_regression | *A0 FLAT sweep (all nodes)* | 6 | 17 | 6.75 [6.23, 6.93] | 6.63 [6.14, 6.82] | 4.14 [3.98, 4.48] | 0.104 [0.088, 0.118] | 10.98 [10.22, 11.39] | — | — |

Node-call and sweep counts were identical across the 7 repetitions of every case, and the objective and
constraint vectors bit-identical (§3.2); a case whose repetitions differed would have been refused by the
summariser and would appear as "repetitions differ in counts". The **PULSE** row of `st_regression` is
a block visit whose one node (`pulse`) the per-run set suppresses in the solve phase, so it executes
nothing (on the pulsed configurations `pulse` is deferred to the tail and the PULSE block is empty and
never swept); the **FF** row is the per-call deferred tail swept once (which is where `pulse` runs on the
pulsed configurations); **ONCE_PER_RUN** is A89's once-after-convergence execution of the per-run set. A single repetition of `low_aspect_ratio_DEMO`'s
`A2` FF sweep took 10.6 ms (its median 0.08 ms): one hiccup, in the range, not in the median.

**What this is and is not.** Timings from one shared 16-core machine, one afternoon, 7 repetitions per case,
after the orchestrator's contention notice voided the first two presses (§8). Between the survey press and a
repeat press of identical code taken one minute later, block-sweep medians moved by up to 2× in one case
(`low_aspect_ratio_DEMO` `A2` M2: 3.21 → 6.30 ms) and by under 15 % in most (§3.6). The shape — M1 ≈ M2 ≈
3 ms, M3 < 1 ms, test ≈ 1.3–1.6 ms per block sweep, dispatch < 0.1 ms, `module_schedule` ≈ 9 ms per
evaluation — held in both presses. No number here is evidence for a decision; the counts beside them are.

## 1. Question and scope

The partition's blocks are **M1** (physics: `plasma_geom`, `physics`), **M2** (coils: `build`, the
TF-coil model the switch selects, `pfcoil`), **M3** (plant: 12–14 nodes from `divertor` to
`availability`), the single-node **PULSE** block and the feed-forward tail **FF** (`costs`, `water_use`,
and whatever the per-call deferral moves there), as the driver copy's `module_schedule` names them and the
committed node map (`harness/data/dsm_node_map.json`) assigns membership. The question is how long one
sweep of each takes, split into model time, convergence-test time and the dispatch overhead A89 §7.5
hypothesised but did not measure; with the flat arms' per-node times aggregated to the same blocks beside
them; and the cost of M2 broken down by node.

Evaluation phase only, three configurations, V4's τ = 1e-6 and whole-`y` test (A89's test set `full`),
displaced entry seed 1 from each configuration's reference fixed point. The cold entry was not timed
(§6, decision 2).

## 2. Method

**Code** (`arch_surgery/block_sweep_timing/`, committed before any number was produced; nothing under
`MDA_partitioning_experiment_v4/` or `process/` is edited, and `git status --ignored` on the V4 folder is
empty after every stage):

- `sweep_timers.py` — the instrument, installed on V4's driver copy from outside the V4 folder the way
  A89's `narrowing.py` installs its substitutions:
  - `Caller._sweep_block(xc, nodes)` is wrapped: wall clock (`perf_counter`) of the whole walk of the
    dispatch body restricted to `nodes`, labelled by the schedule block whose node set it is, `FF` for
    the per-call deferred tail, `ONCE_PER_RUN` for the per-run set A89 runs once after convergence;
  - `Caller._node(name, run)` is wrapped by handing it a timed closure around `run`, so only a node that
    actually executes is timed, the driver's own `NODE_CALLS` line still counts it, and a node `_node`
    drops (outside the block, deferred, suppressed) costs one closure allocation and nothing else;
  - the design-vector injection (`set_scaled_iteration_variable`) and the first-wall geometry prime
    (`models.fw.set_fw_geometry`) — the two named non-node pieces of the dispatch body — are timed
    separately, so **dispatch overhead per sweep = sweep wall − Σ node − x inject − fw geometry**: the
    switch tests, the `_node` filtering of the nodes outside the block, the counter increments;
  - the coupling-state predicate: `spec.read` and `spec.residual` are wrapped through `load_subsets` (as
    A89's timers are) and attributed to a block by position — the read after a sweep and the residual
    belong to the block just swept; the read *before* a block's first sweep (the loop's `y_prev`) is
    held pending and charged to the block swept next. The pending-read leftover at the end of every
    evaluation was 0.0 s in every repetition;
  - five per-evaluation pieces of `call_models` that are neither a sweep nor a test are timed by name:
    `module_schedule`, `_defer_per_run_nodes`, `spec.bind`, `objective_function`, `constraint_eqns`.
    What is left of `call_models` after Σ sweep wall, Σ test and these five is reported as
    "unattributed" (0.24–0.41 ms per evaluation, §3.2).
- `timed_evaluations_child.py` — A89's `inproc_child.py --mode timing` with the instrument installed
  beside A89's `narrowing` (test set `full`; the once-per-run execution where the arm defers per run).
  One subprocess per case, its own directory, the environment V4's `pool.environment_for` composes for
  the arm plus A89's overrides for its `A0`, `PYTHONPATH` = the worktree's V4 copy, `child.assert_tree`
  asserting the exact tree (verified beforehand from a directory that is neither tree: `process.__file__`
  resolved to the worktree's `MDA_partitioning_experiment_v4/PROCESS/process/__init__.py`). It enters the
  recorded displaced snapshot bit for bit (`entry_readback_bitexact` true in every record), runs one
  warm-up evaluation (discarded; numba's first-call cost lands there), then 7 timed evaluations of the
  same entry, each with a fresh Caller and the snapshot re-entered. Every record carries the tree's git
  stamp (`tree_git_head`, dirty flags — A89's in-process records did not), the subprocess's wall-clock
  window (`started_at`, `ended_at`, `taken_at` per repetition) and the load average at its end.
- `run_survey.py` — the stages, each a flag: `--references` (V4's entry-reference job per configuration:
  `A0v4`, cold, through A89's `run_evaluate`), `--entries` (one displaced seed-1 evaluation per
  configuration **and arm** through A89's wrapper, whose `y_entry.json` the timing child enters and whose
  counts the child is checked against), `--timing [--press N]` (serial; press 1 is the survey, a later
  press a repeat of identical code into its own directory), `--summarise` (records → `survey_summary.json`
  and `survey_tables.md`; no PROCESS run). It imports A89's `run_trial.py` and re-points its records
  directory, so the job composition is A89's unchanged: V4's `pool.Job`, `pool.environment_for`,
  `pool._command`, `reproduction.entry_pin`.

**Arms** (A89 §7.1's definitions, kept so these numbers sit beside A89 §7.5):

| arm | what | V4 relation |
|---|---|---|
| `A0v4` | flat: one block over every in-loop node, every node in every sweep, whole-`y` test | V4's `A0` unchanged |
| `A0` | flat; feed-forward nodes deferred to a tail run once per call after convergence, per-run nodes run once after convergence | V4's `A0` + `PROCESS_ARCH_DEFER_PER_CALL=feedforward` + the committed per-run artifact + one execution of that set (A89) |
| `A2` | partitioned: M1, M2, (PULSE,) M3 each iterated to its own fixed point, the tail once, the per-run set once | V4's `A2` + one execution of the per-run set (A89) |

All three run `_call_models_partitioned`: V4's flat control is the block schedule with a single `FLAT`
block, so "one flat sweep" and "one block sweep" are the same code path (`_sweep_block`), which is what
makes the dispatch column comparable between arms.

**Aggregation.** Per repetition, per block: totals over the evaluation divided by the block's sweep count.
Per node: wall clock divided by calls. Across the 7 repetitions: median and [min, max] of those
per-repetition values. Flat arms by block: the node time inside a FLAT sweep, summed over the nodes the
node map assigns to each module, divided by the FLAT sweep count. **Counts** (node calls, dispatch sweeps,
per-block sweeps/reads/residuals, per-node calls, `inner_counts`) must be identical across the repetitions
of a case, and the objective and constraint vectors bit-identical, or the summariser marks the case
refused; every case passed.

**Stages and commits.** `dfbf3749`: references, entries. `c821dbd6`: timing press 1 (the survey) and
press 2 (the repeat), summary. Two earlier presses at `dfbf3749`/`d65f9194` were voided by the
orchestrator's contention notice and set aside unpublished (§8).

## 3. Full tables

Every table below is a verbatim copy of `survey_tables.md` rendered at `c821dbd6`.

### 3.1 Entries and counts

One V4 evaluation per configuration and arm through A89's wrapper (displaced seed 1, τ = 1e-6, whole-`y`
test); the timing child enters the arm's own `y_entry.json`. Columns: the run's status, node calls of the
one evaluation (with the once-per-run execution counted in `A0` and `A2`), sweeps per block from the
driver's `inner_counts`, the exit audit's maximum whole-`y` residual, whether the three arms' entry
snapshots are byte-identical (they are: the displacement is keyed on component name), the record's git
head.

| configuration | arm | status | node calls | sweeps per block | exit audit max | `y_entry.json` identical across arms | record head |
|---|---|---|---|---|---|---|---|
| large_tokamak_nof | A0v4 | ok | 126 | FLAT 6 | 2.6e-09 | True | dfbf3749 |
| large_tokamak_nof | A0 | ok | 111 | FLAT 6 | 2.6e-09 | True | dfbf3749 |
| large_tokamak_nof | A2 | ok | 63 | M1 4, M2 5, M3 3 | 1.4e-08 | True | dfbf3749 |
| low_aspect_ratio_DEMO | A0v4 | ok | 105 | FLAT 5 | 0.0e+00 | True | dfbf3749 |
| low_aspect_ratio_DEMO | A0 | ok | 93 | FLAT 5 | 0.0e+00 | True | dfbf3749 |
| low_aspect_ratio_DEMO | A2 | ok | 63 | M1 4, M2 5, M3 3 | 0.0e+00 | True | dfbf3749 |
| st_regression | A0v4 | ok | 126 | FLAT 6 | 3.0e-09 | True | dfbf3749 |
| st_regression | A0 | ok | 106 | FLAT 6 | 3.0e-09 | True | dfbf3749 |
| st_regression | A2 | ok | 66 | M1 4, M2 6, PULSE 1, M3 3 | 3.0e-09 | True | dfbf3749 |

The timing child's node calls and sweeps per block (§3.2, §3.3) equal these in every case: the timed
evaluations are the evaluation the entry record describes. Every exit audit is below τ = 1e-6.

### 3.2 Per evaluation

ms, median [min, max] over the 7 timed repetitions (the survey press). Columns: node calls and dispatch
sweeps (identical across repetitions — "counts identical"), objective and constraint vectors bit-identical
across repetitions ("results identical"), the whole `call_models`, the sum of every `_sweep_block` wall
clock, the sum of every node call inside them, the sum of the convergence tests (reads + residuals), the
sum of the dispatch overheads (x inject + fw geometry + other), the five named per-evaluation pieces, what
is left ("unattributed"), A89's own predicate timer for cross-check (it equals Σ test to 0.1 ms), and the
once-per-run execution (inside Σ sweep wall).

| configuration | arm | reps | node calls | sweeps | counts identical | results identical | call_models | Σ sweep wall | Σ node | Σ test | Σ dispatch | module_schedule | per-run resolve | bind | objective | constraints | unattributed | A89 predicate | once-per-run | head |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | A0v4 | 7 | 126 | 6 | True | True | 65.0 [62.9, 77.0] | 39.6 [37.8, 48.8] | 38.8 [37.1, 47.8] | 24.7 [24.4, 27.5] | 0.68 [0.64, 1.06] | 0.01 [0.01, 0.02] | 0.000 [0.000, 0.000] | 0.06 [0.05, 0.08] | 0.007 [0.007, 0.009] | 0.18 [0.15, 0.18] | 0.26 [0.23, 0.39] | 24.6 [24.3, 27.4] | 0.00 [0.00, 0.00] | c821dbd6 |
| large_tokamak_nof | A0 | 7 | 111 | 8 | True | True | 74.9 [70.3, 152.9] | 39.4 [36.9, 43.2] | 38.5 [36.2, 42.0] | 25.3 [24.3, 27.9] | 0.84 [0.73, 1.18] | 9.30 [8.64, 86.59] | 0.002 [0.002, 0.002] | 0.09 [0.07, 0.16] | 0.006 [0.005, 0.007] | 0.16 [0.15, 0.18] | 0.26 [0.23, 0.40] | 25.3 [24.2, 27.8] | 0.25 [0.24, 0.44] | c821dbd6 |
| large_tokamak_nof | A2 | 7 | 63 | 14 | True | True | 55.5 [53.5, 56.6] | 28.8 [27.9, 29.8] | 27.6 [26.8, 28.5] | 16.9 [16.4, 17.8] | 1.18 [1.14, 1.24] | 8.77 [8.11, 10.58] | 0.002 [0.002, 0.003] | 0.08 [0.06, 0.10] | 0.005 [0.005, 0.006] | 0.15 [0.14, 0.17] | 0.36 [0.32, 0.39] | 16.8 [16.4, 17.8] | 0.25 [0.25, 0.32] | c821dbd6 |
| low_aspect_ratio_DEMO | A0v4 | 7 | 105 | 5 | True | True | 54.2 [52.5, 58.4] | 33.1 [31.8, 35.9] | 32.6 [31.3, 35.3] | 20.6 [20.2, 21.9] | 0.53 [0.50, 0.77] | 0.01 [0.01, 0.02] | 0.000 [0.000, 0.000] | 0.06 [0.06, 0.07] | 0.009 [0.008, 0.011] | 0.15 [0.14, 0.19] | 0.24 [0.20, 0.27] | 20.6 [20.2, 21.9] | 0.00 [0.00, 0.00] | c821dbd6 |
| low_aspect_ratio_DEMO | A0 | 7 | 93 | 7 | True | True | 65.6 [62.1, 138.7] | 34.4 [32.7, 37.1] | 33.7 [32.1, 36.4] | 21.3 [20.3, 21.7] | 0.71 [0.65, 0.79] | 8.94 [8.42, 80.58] | 0.002 [0.002, 0.002] | 0.08 [0.06, 0.12] | 0.009 [0.007, 0.010] | 0.16 [0.14, 0.18] | 0.24 [0.22, 0.35] | 21.3 [20.3, 21.7] | 0.24 [0.23, 0.35] | c821dbd6 |
| low_aspect_ratio_DEMO | A2 | 7 | 63 | 14 | True | True | 57.9 [54.9, 70.7] | 30.4 [28.8, 42.4] | 29.2 [27.7, 31.5] | 17.7 [16.7, 18.6] | 1.25 [1.16, 11.85] | 8.73 [8.41, 10.22] | 0.003 [0.002, 0.003] | 0.07 [0.06, 0.11] | 0.012 [0.010, 0.030] | 0.16 [0.15, 0.33] | 0.41 [0.33, 0.63] | 17.6 [16.7, 18.6] | 0.28 [0.25, 0.36] | c821dbd6 |
| st_regression | A0v4 | 7 | 126 | 6 | True | True | 66.9 [63.8, 76.1] | 41.6 [39.0, 47.0] | 40.9 [38.4, 46.2] | 25.1 [24.3, 29.0] | 0.62 [0.54, 0.79] | 0.02 [0.01, 0.02] | 0.000 [0.000, 0.000] | 0.06 [0.05, 0.06] | 0.009 [0.007, 0.011] | 0.13 [0.12, 0.16] | 0.26 [0.25, 0.34] | 25.1 [24.3, 29.0] | 0.00 [0.00, 0.00] | c821dbd6 |
| st_regression | A0 | 7 | 106 | 8 | True | True | 75.2 [70.8, 77.9] | 40.8 [37.7, 42.0] | 40.0 [37.0, 41.2] | 24.9 [23.9, 26.9] | 0.76 [0.65, 0.81] | 8.73 [8.25, 9.69] | 0.002 [0.002, 0.003] | 0.07 [0.06, 0.19] | 0.008 [0.006, 0.009] | 0.12 [0.11, 0.15] | 0.28 [0.24, 0.34] | 24.8 [23.9, 26.8] | 0.22 [0.22, 0.31] | c821dbd6 |
| st_regression | A2 | 7 | 66 | 16 | True | True | 61.0 [57.4, 65.8] | 33.5 [31.1, 35.9] | 32.3 [30.0, 34.7] | 17.9 [17.3, 20.1] | 1.18 [1.11, 1.37] | 9.02 [8.37, 11.55] | 0.003 [0.002, 0.020] | 0.07 [0.07, 0.09] | 0.008 [0.006, 0.025] | 0.13 [0.11, 0.16] | 0.40 [0.36, 0.48] | 17.8 [17.2, 20.1] | 0.24 [0.22, 0.33] | c821dbd6 |

The `A0` maxima on the two pulsed configurations (`call_models` 152.9 / 138.7 ms; `module_schedule` 86.6 /
80.6 ms) are **one repetition each — always the second timed repetition**, in both presses (press 2: 73.7 /
74.7 ms), and never on `st_regression`. Reproducible in position, unexplained; a hypothesis — the AST walk's
allocations tripping a generational garbage collection at a fixed point — is not tested here. Medians are
unaffected.

### 3.3 Per block sweep

ms per sweep of the block, median [min, max] over repetitions; each repetition's value is the block's total
over the evaluation divided by its sweep count. "nodes in block" is the size of the schedule's node set
for the block (the node map's membership, less any per-call deferral), "node calls per sweep" how many of
them this configuration executes. Dispatch is split into the design-vector injection, the first-wall
geometry prime (an `A2`-only arrangement method; `A0`/`A0v4` have it off, the 0.001 ms is the wrapper's
own cost) and everything else. "reads / residuals" are the predicate evaluations charged to the block: one
read more than residuals for an iterated block (the read before its first sweep).

| configuration | arm | block | sweeps | nodes in block | node calls per sweep | sweep wall | model (Σ node) | dispatch: x inject | dispatch: fw geometry | dispatch: other | test: read | test: residual | sweep + test | reads / residuals |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | A0v4 | FLAT | 6 | 28 | 21 | 6.59 [6.30, 8.14] | 6.47 [6.19, 7.96] | 0.064 [0.060, 0.100] | 0.001 [0.001, 0.001] | 0.049 [0.044, 0.074] | 0.22 [0.21, 0.32] | 3.89 [3.85, 4.26] | 10.75 [10.39, 12.72] | 7 / 6 |
| large_tokamak_nof | A0 | FF | 1 | 2 | 0 | 0.08 [0.07, 0.10] | 0.00 [0.00, 0.00] | 0.058 [0.055, 0.071] | 0.000 [0.000, 0.000] | 0.018 [0.017, 0.026] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.08 [0.07, 0.10] | 0 / 0 |
| large_tokamak_nof | A0 | ONCE_PER_RUN | 1 | 3 | 3 | 0.25 [0.24, 0.43] | 0.18 [0.18, 0.36] | 0.048 [0.047, 0.052] | 0.000 [0.000, 0.000] | 0.015 [0.014, 0.017] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.25 [0.24, 0.43] | 0 / 0 |
| large_tokamak_nof | A0 | FLAT | 6 | 26 | 18 | 6.51 [6.10, 7.10] | 6.39 [6.00, 6.94] | 0.064 [0.058, 0.100] | 0.001 [0.001, 0.002] | 0.048 [0.040, 0.067] | 0.27 [0.21, 0.37] | 3.97 [3.84, 4.28] | 10.80 [10.14, 11.75] | 7 / 6 |
| large_tokamak_nof | A2 | M1 | 4 | 2 | 2 | 2.94 [2.86, 3.14] | 2.84 [2.77, 3.03] | 0.062 [0.060, 0.075] | 0.001 [0.001, 0.001] | 0.029 [0.025, 0.030] | 0.24 [0.22, 0.26] | 1.27 [1.24, 1.44] | 4.46 [4.32, 4.73] | 5 / 4 |
| large_tokamak_nof | A2 | M2 | 5 | 9 | 3 | 2.92 [2.84, 3.00] | 2.84 [2.76, 2.92] | 0.056 [0.055, 0.059] | 0.001 [0.001, 0.001] | 0.026 [0.025, 0.030] | 0.21 [0.20, 0.22] | 1.17 [1.14, 1.20] | 4.28 [4.20, 4.40] | 6 / 5 |
| large_tokamak_nof | A2 | M3 | 3 | 14 | 12 | 0.67 [0.64, 0.69] | 0.58 [0.56, 0.60] | 0.054 [0.053, 0.058] | 0.001 [0.001, 0.002] | 0.028 [0.027, 0.031] | 0.22 [0.22, 0.24] | 1.06 [1.04, 1.14] | 1.95 [1.91, 2.07] | 4 / 3 |
| large_tokamak_nof | A2 | FF | 1 | 3 | 1 | 0.08 [0.08, 0.09] | 0.01 [0.01, 0.01] | 0.053 [0.052, 0.057] | 0.001 [0.001, 0.001] | 0.019 [0.017, 0.023] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.08 [0.08, 0.09] | 0 / 0 |
| large_tokamak_nof | A2 | ONCE_PER_RUN | 1 | 3 | 3 | 0.24 [0.24, 0.31] | 0.18 [0.17, 0.25] | 0.048 [0.048, 0.049] | 0.001 [0.001, 0.001] | 0.016 [0.016, 0.017] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.24 [0.24, 0.31] | 0 / 0 |
| low_aspect_ratio_DEMO | A0v4 | FLAT | 5 | 28 | 21 | 6.61 [6.37, 7.19] | 6.51 [6.27, 7.05] | 0.059 [0.055, 0.094] | 0.001 [0.001, 0.002] | 0.046 [0.043, 0.059] | 0.23 [0.20, 0.27] | 3.87 [3.82, 4.12] | 10.75 [10.41, 11.57] | 6 / 5 |
| low_aspect_ratio_DEMO | A0 | FF | 1 | 2 | 0 | 0.07 [0.07, 0.08] | 0.00 [0.00, 0.00] | 0.056 [0.054, 0.059] | 0.000 [0.000, 0.000] | 0.019 [0.017, 0.021] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.07 [0.07, 0.08] | 0 / 0 |
| low_aspect_ratio_DEMO | A0 | ONCE_PER_RUN | 1 | 3 | 3 | 0.24 [0.23, 0.35] | 0.18 [0.17, 0.29] | 0.047 [0.045, 0.055] | 0.000 [0.000, 0.000] | 0.015 [0.014, 0.018] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.24 [0.23, 0.35] | 0 / 0 |
| low_aspect_ratio_DEMO | A0 | FLAT | 5 | 26 | 18 | 6.79 [6.48, 7.37] | 6.67 [6.38, 7.26] | 0.062 [0.058, 0.075] | 0.001 [0.001, 0.001] | 0.053 [0.044, 0.058] | 0.26 [0.22, 0.29] | 3.98 [3.85, 4.05] | 11.05 [10.55, 11.54] | 6 / 5 |
| low_aspect_ratio_DEMO | A2 | M1 | 4 | 2 | 2 | 2.91 [2.87, 3.07] | 2.82 [2.78, 2.97] | 0.061 [0.056, 0.066] | 0.001 [0.001, 0.001] | 0.032 [0.028, 0.034] | 0.25 [0.23, 0.34] | 1.29 [1.27, 1.41] | 4.44 [4.39, 4.69] | 5 / 4 |
| low_aspect_ratio_DEMO | A2 | M2 | 5 | 9 | 3 | 3.21 [3.00, 3.58] | 3.11 [2.92, 3.47] | 0.060 [0.053, 0.074] | 0.001 [0.001, 0.002] | 0.032 [0.026, 0.045] | 0.24 [0.21, 0.29] | 1.24 [1.16, 1.37] | 4.63 [4.37, 5.20] | 6 / 5 |
| low_aspect_ratio_DEMO | A2 | M3 | 3 | 14 | 12 | 0.70 [0.67, 1.03] | 0.61 [0.58, 0.93] | 0.059 [0.052, 0.065] | 0.002 [0.001, 0.002] | 0.031 [0.027, 0.044] | 0.23 [0.22, 0.28] | 1.10 [1.03, 1.38] | 2.03 [1.92, 2.48] | 4 / 3 |
| low_aspect_ratio_DEMO | A2 | FF | 1 | 3 | 1 | 0.08 [0.08, 10.60] | 0.01 [0.01, 0.02] | 0.052 [0.050, 10.525] | 0.001 [0.001, 0.002] | 0.018 [0.018, 0.050] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.08 [0.08, 10.60] | 0 / 0 |
| low_aspect_ratio_DEMO | A2 | ONCE_PER_RUN | 1 | 3 | 3 | 0.27 [0.24, 0.33] | 0.21 [0.18, 0.26] | 0.047 [0.045, 0.052] | 0.001 [0.001, 0.001] | 0.016 [0.016, 0.020] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.27 [0.24, 0.33] | 0 / 0 |
| st_regression | A0v4 | FLAT | 6 | 28 | 21 | 6.93 [6.49, 7.83] | 6.82 [6.40, 7.70] | 0.054 [0.046, 0.068] | 0.001 [0.001, 0.002] | 0.049 [0.043, 0.065] | 0.24 [0.21, 0.31] | 3.93 [3.85, 4.54] | 11.07 [10.55, 12.59] | 7 / 6 |
| st_regression | A0 | FF | 1 | 2 | 0 | 0.07 [0.06, 0.09] | 0.00 [0.00, 0.00] | 0.050 [0.045, 0.073] | 0.000 [0.000, 0.000] | 0.021 [0.018, 0.027] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.07 [0.06, 0.09] | 0 / 0 |
| st_regression | A0 | ONCE_PER_RUN | 1 | 4 | 4 | 0.22 [0.21, 0.31] | 0.17 [0.16, 0.25] | 0.035 [0.035, 0.038] | 0.000 [0.000, 0.000] | 0.017 [0.016, 0.018] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.22 [0.21, 0.31] | 0 / 0 |
| st_regression | A0 | FLAT | 6 | 26 | 17 | 6.75 [6.23, 6.93] | 6.63 [6.14, 6.82] | 0.052 [0.046, 0.056] | 0.001 [0.001, 0.001] | 0.051 [0.042, 0.060] | 0.26 [0.21, 0.32] | 3.85 [3.76, 4.16] | 10.98 [10.22, 11.39] | 7 / 6 |
| st_regression | A2 | M1 | 4 | 2 | 2 | 3.07 [2.80, 3.18] | 2.99 [2.73, 3.07] | 0.053 [0.045, 0.070] | 0.001 [0.001, 0.001] | 0.029 [0.022, 0.036] | 0.25 [0.21, 0.29] | 1.33 [1.30, 1.48] | 4.65 [4.31, 4.90] | 5 / 4 |
| st_regression | A2 | M2 | 6 | 9 | 3 | 3.08 [2.87, 3.44] | 3.00 [2.80, 3.36] | 0.046 [0.043, 0.051] | 0.001 [0.001, 0.002] | 0.029 [0.025, 0.032] | 0.21 [0.19, 0.23] | 1.09 [1.00, 1.17] | 4.34 [4.10, 4.78] | 7 / 6 |
| st_regression | A2 | PULSE | 1 | 1 | 0 | 0.06 [0.06, 0.08] | 0.00 [0.00, 0.00] | 0.044 [0.042, 0.050] | 0.001 [0.001, 0.001] | 0.018 [0.017, 0.029] | 0.16 [0.15, 0.26] | 0.00 [0.00, 0.00] | 0.23 [0.21, 0.32] | 1 / 0 |
| st_regression | A2 | M3 | 3 | 14 | 12 | 0.78 [0.75, 0.93] | 0.70 [0.69, 0.84] | 0.044 [0.039, 0.050] | 0.001 [0.001, 0.002] | 0.030 [0.026, 0.034] | 0.17 [0.16, 0.20] | 1.09 [1.06, 1.35] | 2.02 [1.99, 2.46] | 3 / 3 |
| st_regression | A2 | FF | 1 | 2 | 0 | 0.06 [0.06, 0.08] | 0.00 [0.00, 0.00] | 0.041 [0.040, 0.057] | 0.001 [0.001, 0.001] | 0.017 [0.016, 0.021] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.06 [0.06, 0.08] | 0 / 0 |
| st_regression | A2 | ONCE_PER_RUN | 1 | 4 | 4 | 0.23 [0.22, 0.32] | 0.18 [0.17, 0.27] | 0.037 [0.035, 0.041] | 0.001 [0.001, 0.001] | 0.016 [0.015, 0.024] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.23 [0.22, 0.32] | 0 / 0 |

On `st_regression` the PULSE block holds its one node `pulse` (not deferred to the tail on a steady-state
configuration), which the per-run set suppresses in the solve phase, so the block's single non-iterated
sweep executes nothing; M3's entry read (`y_prev`) then follows a sweep, and the attribution rule charges
it to that sweep — which is why PULSE shows 1 read / 0 residuals and 0.16 ms of test, and M3 3 / 3 instead
of 4 / 3. It is the one case where the position rule and the block boundary disagree, and it moves 0.16 ms
from M3 to PULSE. (The FF row's 0 node calls on this configuration: `costs` and `water_use` are both in
the per-run set, executed in ONCE_PER_RUN.)

### 3.4 Flat arms: node time per sweep by node-map module

ms per FLAT sweep of the nodes the committed node map assigns to each module (membership only), median
[min, max]; node calls per sweep in brackets. The `A2` rows are a check: every node timed inside an M1,
M2 or M3 sweep belongs to that module, and the tail sweep (FF) holds `pulse` (module PULSE) on the pulsed
configurations. The ONCE_PER_RUN rows are the per-run set: `vacuum` (M3), `costs` and `water_use` (FF),
plus `pulse` on `st_regression`.

| configuration | arm | block swept | M1 | M2 | PULSE | M3 | FF |
|---|---|---|---|---|---|---|---|
| large_tokamak_nof | A0v4 | FLAT | 2.84 [2.69, 3.31] (2) | 2.89 [2.74, 3.79] (3) | 0.01 [0.01, 0.01] (1) | 0.66 [0.64, 0.75] (13) | 0.10 [0.08, 0.13] (2) |
| large_tokamak_nof | A0 | FF | — | — | — | — | — |
| large_tokamak_nof | A0 | ONCE_PER_RUN | — | — | — | 0.08 [0.08, 0.09] (1) | 0.10 [0.10, 0.27] (2) |
| large_tokamak_nof | A0 | FLAT | 2.89 [2.68, 3.03] (2) | 2.92 [2.77, 3.23] (3) | 0.01 [0.01, 0.01] (1) | 0.60 [0.54, 0.66] (12) | — |
| large_tokamak_nof | A2 | M1 | 2.84 [2.77, 3.03] (2) | — | — | — | — |
| large_tokamak_nof | A2 | M2 | — | 2.84 [2.76, 2.92] (3) | — | — | — |
| large_tokamak_nof | A2 | M3 | — | — | — | 0.58 [0.56, 0.60] (12) | — |
| large_tokamak_nof | A2 | FF | — | — | 0.01 [0.01, 0.01] (1) | — | — |
| large_tokamak_nof | A2 | ONCE_PER_RUN | — | — | — | 0.08 [0.07, 0.09] (1) | 0.10 [0.10, 0.16] (2) |
| low_aspect_ratio_DEMO | A0v4 | FLAT | 2.79 [2.71, 3.07] (2) | 2.95 [2.87, 3.12] (3) | 0.01 [0.01, 0.01] (1) | 0.65 [0.60, 0.71] (13) | 0.09 [0.08, 0.15] (2) |
| low_aspect_ratio_DEMO | A0 | FF | — | — | — | — | — |
| low_aspect_ratio_DEMO | A0 | ONCE_PER_RUN | — | — | — | 0.07 [0.07, 0.11] (1) | 0.10 [0.10, 0.18] (2) |
| low_aspect_ratio_DEMO | A0 | FLAT | 2.94 [2.73, 3.31] (2) | 3.15 [3.06, 3.36] (3) | 0.01 [0.01, 0.01] (1) | 0.61 [0.56, 0.67] (12) | — |
| low_aspect_ratio_DEMO | A2 | M1 | 2.82 [2.78, 2.97] (2) | — | — | — | — |
| low_aspect_ratio_DEMO | A2 | M2 | — | 3.11 [2.92, 3.47] (3) | — | — | — |
| low_aspect_ratio_DEMO | A2 | M3 | — | — | — | 0.61 [0.58, 0.93] (12) | — |
| low_aspect_ratio_DEMO | A2 | FF | — | — | 0.01 [0.01, 0.02] (1) | — | — |
| low_aspect_ratio_DEMO | A2 | ONCE_PER_RUN | — | — | — | 0.08 [0.07, 0.11] (1) | 0.11 [0.10, 0.17] (2) |
| st_regression | A0v4 | FLAT | 3.00 [2.83, 3.28] (2) | 2.89 [2.76, 3.42] (3) | 0.00 [0.00, 0.00] (1) | 0.75 [0.70, 1.00] (13) | 0.09 [0.08, 0.14] (2) |
| st_regression | A0 | FF | — | — | — | — | — |
| st_regression | A0 | ONCE_PER_RUN | — | — | 0.00 [0.00, 0.00] (1) | 0.06 [0.06, 0.08] (1) | 0.11 [0.10, 0.18] (2) |
| st_regression | A0 | FLAT | 2.92 [2.75, 2.98] (2) | 2.98 [2.73, 3.12] (3) | — | 0.72 [0.65, 0.80] (12) | — |
| st_regression | A2 | M1 | 2.99 [2.73, 3.07] (2) | — | — | — | — |
| st_regression | A2 | M2 | — | 3.00 [2.80, 3.36] (3) | — | — | — |
| st_regression | A2 | PULSE | — | — | — | — | — |
| st_regression | A2 | M3 | — | — | — | 0.70 [0.69, 0.84] (12) | — |
| st_regression | A2 | FF | — | — | — | — | — |
| st_regression | A2 | ONCE_PER_RUN | — | — | 0.00 [0.00, 0.00] (1) | 0.07 [0.06, 0.09] (1) | 0.11 [0.10, 0.19] (2) |

### 3.5 Subprocess windows

Local wall clock of each timing subprocess, first to last write; the 1-minute load average at its end
(this survey's own process is one of it; the earlier contention's decay is the rest, §8). Press 1 is the
survey every table above reads; press 2 the repeat of §3.6.

| configuration | arm | press | started | ended | head | load average (1 min) |
|---|---|---|---|---|---|---|
| large_tokamak_nof | A0v4 | 1 | 2026-09-29T14:02:59+02:00 | 2026-09-29T14:03:04+02:00 | c821dbd6 | 2.66 |
| large_tokamak_nof | A0 | 1 | 2026-09-29T14:03:04+02:00 | 2026-09-29T14:03:09+02:00 | c821dbd6 | 2.69 |
| large_tokamak_nof | A2 | 1 | 2026-09-29T14:03:09+02:00 | 2026-09-29T14:03:14+02:00 | c821dbd6 | 2.63 |
| low_aspect_ratio_DEMO | A0v4 | 1 | 2026-09-29T14:03:15+02:00 | 2026-09-29T14:03:20+02:00 | c821dbd6 | 2.50 |
| low_aspect_ratio_DEMO | A0 | 1 | 2026-09-29T14:03:20+02:00 | 2026-09-29T14:03:25+02:00 | c821dbd6 | 2.38 |
| low_aspect_ratio_DEMO | A2 | 1 | 2026-09-29T14:03:26+02:00 | 2026-09-29T14:03:31+02:00 | c821dbd6 | 2.27 |
| st_regression | A0v4 | 1 | 2026-09-29T14:03:31+02:00 | 2026-09-29T14:03:36+02:00 | c821dbd6 | 2.25 |
| st_regression | A0 | 1 | 2026-09-29T14:03:36+02:00 | 2026-09-29T14:03:41+02:00 | c821dbd6 | 2.31 |
| st_regression | A2 | 1 | 2026-09-29T14:03:42+02:00 | 2026-09-29T14:03:46+02:00 | c821dbd6 | 2.20 |
| large_tokamak_nof | A0v4 | 2 | 2026-09-29T14:03:47+02:00 | 2026-09-29T14:03:52+02:00 | c821dbd6 | 2.16 |
| large_tokamak_nof | A0 | 2 | 2026-09-29T14:03:52+02:00 | 2026-09-29T14:03:57+02:00 | c821dbd6 | 2.23 |
| large_tokamak_nof | A2 | 2 | 2026-09-29T14:03:58+02:00 | 2026-09-29T14:04:03+02:00 | c821dbd6 | 2.13 |
| low_aspect_ratio_DEMO | A0v4 | 2 | 2026-09-29T14:04:03+02:00 | 2026-09-29T14:04:08+02:00 | c821dbd6 | 2.04 |
| low_aspect_ratio_DEMO | A0 | 2 | 2026-09-29T14:04:08+02:00 | 2026-09-29T14:04:13+02:00 | c821dbd6 | 2.04 |
| low_aspect_ratio_DEMO | A2 | 2 | 2026-09-29T14:04:13+02:00 | 2026-09-29T14:04:19+02:00 | c821dbd6 | 1.96 |
| st_regression | A0v4 | 2 | 2026-09-29T14:04:19+02:00 | 2026-09-29T14:04:24+02:00 | c821dbd6 | 1.88 |
| st_regression | A0 | 2 | 2026-09-29T14:04:24+02:00 | 2026-09-29T14:04:29+02:00 | c821dbd6 | 1.81 |
| st_regression | A2 | 2 | 2026-09-29T14:04:29+02:00 | 2026-09-29T14:04:34+02:00 | c821dbd6 | 1.74 |

### 3.6 Repeatability across two presses of identical code

Press 2 ran one minute after press 1, same code, same commit, same machine state as far as this task can
tell. ms per block sweep, sweep wall median [min, max]; the counts of every case are identical across
presses (checked column).

| configuration | arm | block | press 1 | press 2 | counts identical across presses |
|---|---|---|---|---|---|
| large_tokamak_nof | A0v4 | FLAT | 6.59 [6.30, 8.14] | 6.47 [6.26, 6.60] | True |
| large_tokamak_nof | A0 | FF | 0.08 [0.07, 0.10] | 0.09 [0.08, 0.12] | True |
| large_tokamak_nof | A0 | ONCE_PER_RUN | 0.25 [0.24, 0.43] | 0.25 [0.23, 0.43] | True |
| large_tokamak_nof | A0 | FLAT | 6.51 [6.10, 7.10] | 6.77 [6.46, 7.86] | True |
| large_tokamak_nof | A2 | M1 | 2.94 [2.86, 3.14] | 3.16 [2.88, 4.24] | True |
| large_tokamak_nof | A2 | M2 | 2.92 [2.84, 3.00] | 3.34 [2.85, 3.67] | True |
| large_tokamak_nof | A2 | M3 | 0.67 [0.64, 0.69] | 0.71 [0.66, 0.88] | True |
| large_tokamak_nof | A2 | FF | 0.08 [0.08, 0.09] | 0.09 [0.08, 0.12] | True |
| large_tokamak_nof | A2 | ONCE_PER_RUN | 0.24 [0.24, 0.31] | 0.27 [0.24, 0.55] | True |
| low_aspect_ratio_DEMO | A0v4 | FLAT | 6.61 [6.37, 7.19] | 6.85 [6.43, 7.15] | True |
| low_aspect_ratio_DEMO | A0 | FF | 0.07 [0.07, 0.08] | 0.08 [0.07, 0.14] | True |
| low_aspect_ratio_DEMO | A0 | ONCE_PER_RUN | 0.24 [0.23, 0.35] | 0.25 [0.24, 0.35] | True |
| low_aspect_ratio_DEMO | A0 | FLAT | 6.79 [6.48, 7.37] | 6.50 [6.40, 8.06] | True |
| low_aspect_ratio_DEMO | A2 | M1 | 2.91 [2.87, 3.07] | 4.15 [2.91, 6.02] | True |
| low_aspect_ratio_DEMO | A2 | M2 | 3.21 [3.00, 3.58] | 6.30 [3.55, 6.72] | True |
| low_aspect_ratio_DEMO | A2 | M3 | 0.70 [0.67, 1.03] | 0.95 [0.75, 1.77] | True |
| low_aspect_ratio_DEMO | A2 | FF | 0.08 [0.08, 10.60] | 0.11 [0.08, 0.19] | True |
| low_aspect_ratio_DEMO | A2 | ONCE_PER_RUN | 0.27 [0.24, 0.33] | 0.34 [0.26, 0.75] | True |
| st_regression | A0v4 | FLAT | 6.93 [6.49, 7.83] | 6.30 [6.19, 7.51] | True |
| st_regression | A0 | FF | 0.07 [0.06, 0.09] | 0.07 [0.07, 0.11] | True |
| st_regression | A0 | ONCE_PER_RUN | 0.22 [0.21, 0.31] | 0.22 [0.21, 0.33] | True |
| st_regression | A0 | FLAT | 6.75 [6.23, 6.93] | 6.46 [6.23, 7.68] | True |
| st_regression | A2 | M1 | 3.07 [2.80, 3.18] | 3.34 [2.90, 3.73] | True |
| st_regression | A2 | M2 | 3.08 [2.87, 3.44] | 3.22 [3.05, 4.12] | True |
| st_regression | A2 | PULSE | 0.06 [0.06, 0.08] | 0.07 [0.06, 0.10] | True |
| st_regression | A2 | M3 | 0.78 [0.75, 0.93] | 0.85 [0.80, 1.25] | True |
| st_regression | A2 | FF | 0.06 [0.06, 0.08] | 0.06 [0.06, 0.08] | True |
| st_regression | A2 | ONCE_PER_RUN | 0.23 [0.22, 0.32] | 0.25 [0.22, 0.33] | True |

Per evaluation, ms, median [min, max]: `call_models` and the `module_schedule` share of it.

| configuration | arm | call_models press 1 | call_models press 2 | module_schedule press 1 | module_schedule press 2 |
|---|---|---|---|---|---|
| large_tokamak_nof | A0v4 | 65.0 [62.9, 77.0] | 64.5 [62.9, 66.7] | 0.01 [0.01, 0.02] | 0.01 [0.01, 0.02] |
| large_tokamak_nof | A0 | 74.9 [70.3, 152.9] | 82.2 [73.9, 139.0] | 9.30 [8.64, 86.59] | 9.20 [8.41, 73.68] |
| large_tokamak_nof | A2 | 55.5 [53.5, 56.6] | 63.1 [54.0, 70.0] | 8.77 [8.11, 10.58] | 9.49 [8.21, 12.30] |
| low_aspect_ratio_DEMO | A0v4 | 54.2 [52.5, 58.4] | 55.6 [53.1, 57.6] | 0.01 [0.01, 0.02] | 0.01 [0.01, 0.02] |
| low_aspect_ratio_DEMO | A0 | 65.6 [62.1, 138.7] | 63.2 [62.2, 137.8] | 8.94 [8.42, 80.58] | 8.98 [8.14, 74.66] |
| low_aspect_ratio_DEMO | A2 | 57.9 [54.9, 70.7] | 93.8 [64.3, 112.1] | 8.73 [8.41, 10.22] | 10.96 [8.50, 17.56] |
| st_regression | A0v4 | 66.9 [63.8, 76.1] | 62.1 [60.9, 73.2] | 0.02 [0.01, 0.02] | 0.01 [0.01, 0.02] |
| st_regression | A0 | 75.2 [70.8, 77.9] | 73.7 [71.1, 82.7] | 8.73 [8.25, 9.69] | 8.74 [8.04, 9.55] |
| st_regression | A2 | 61.0 [57.4, 65.8] | 63.9 [59.5, 76.7] | 9.02 [8.37, 11.55] | 9.06 [8.11, 10.91] |

Reading: 22 of 28 block rows agree between presses within 15 % of the median. Five of the six that do not
are the one `low_aspect_ratio_DEMO` `A2` subprocess (M1 2.91 → 4.15, M2 3.21 → 6.30, M3 0.70 → 0.95, FF
0.08 → 0.11, ONCE_PER_RUN 0.27 → 0.34; its `call_models` 57.9 → 93.8 ms), whose seven repetitions ran
slow together; the sixth is `st_regression`'s empty PULSE sweep, 0.06 → 0.07 ms. Nothing in the counts
distinguishes the slow subprocess. This is trap T5 in one line: a press of identical code can move a block's median by
2×; a block's cost is the shape across presses, not any one median.

## 4. The per-node breakdown of M2, and of every block in `A2`

ms per call, median [min, max] over repetitions of the per-repetition mean; calls per evaluation; module
from the node map. M2 is `build` + the TF-coil model the switch selects (`cicc_sctfcoil` on the two
tokamaks, `croco_sctfcoil` on `st_regression`) + `pfcoil`. In every arm and configuration **`pfcoil` is
about two thirds of an M2 sweep and the TF-coil model the other third**; `build` is under 0.1 ms.

M2's members in every arm (from the per-node tables of `survey_tables.md`):

| configuration | arm | `pfcoil` ms per call | TF-coil model ms per call | `build` ms per call | M2 calls per evaluation (each) |
|---|---|---|---|---|---|
| large_tokamak_nof | A0v4 | 1.865 [1.790, 2.268] | `cicc_sctfcoil` 0.943 [0.891, 1.434] | 0.061 [0.053, 0.085] | 6 |
| large_tokamak_nof | A0 | 1.855 [1.790, 2.044] | `cicc_sctfcoil` 0.984 [0.926, 1.116] | 0.061 [0.054, 0.074] | 6 |
| large_tokamak_nof | A2 | 1.837 [1.794, 1.866] | `cicc_sctfcoil` 0.948 [0.903, 1.012] | 0.056 [0.051, 0.062] | 5 |
| low_aspect_ratio_DEMO | A0v4 | 1.928 [1.844, 1.992] | `cicc_sctfcoil` 0.983 [0.949, 1.060] | 0.054 [0.048, 0.078] | 5 |
| low_aspect_ratio_DEMO | A0 | 1.997 [1.923, 2.172] | `cicc_sctfcoil` 1.099 [1.042, 1.243] | 0.058 [0.052, 0.070] | 5 |
| low_aspect_ratio_DEMO | A2 | 1.963 [1.881, 2.150] | `cicc_sctfcoil` 1.044 [0.980, 1.254] | 0.060 [0.053, 0.104] | 5 |
| st_regression | A0v4 | 1.634 [1.568, 2.022] | `croco_sctfcoil` 1.225 [1.114, 1.426] | 0.047 [0.036, 0.056] | 6 |
| st_regression | A0 | 1.671 [1.538, 1.752] | `croco_sctfcoil` 1.231 [1.158, 1.361] | 0.045 [0.039, 0.049] | 6 |
| st_regression | A2 | 1.662 [1.583, 1.875] | `croco_sctfcoil` 1.306 [1.124, 1.473] | 0.046 [0.044, 0.057] | 6 |

For comparison, `physics` (all of M1 but 0.02 ms) costs 2.77–2.98 ms per call in every case, and `power`
(the largest M3 node) 0.38–0.46 ms; the other eleven M3 nodes are each under 0.1 ms.

The full per-node tables of the partitioned arm (survey press):

*large_tokamak_nof, A2*

| node | module | calls | ms per call | ms per evaluation |
|---|---|---|---|---|
| physics | M1 | 4 | 2.821 [2.751, 2.997] | 11.28 [11.01, 11.99] |
| plasma_geom | M1 | 4 | 0.022 [0.019, 0.038] | 0.09 [0.08, 0.15] |
| pfcoil | M2 | 5 | 1.837 [1.794, 1.866] | 9.19 [8.97, 9.33] |
| cicc_sctfcoil | M2 | 5 | 0.948 [0.903, 1.012] | 4.74 [4.52, 5.06] |
| build | M2 | 5 | 0.056 [0.051, 0.062] | 0.28 [0.25, 0.31] |
| pulse | PULSE | 1 | 0.008 [0.008, 0.013] | 0.01 [0.01, 0.01] |
| power | M3 | 3 | 0.380 [0.368, 0.391] | 1.14 [1.10, 1.17] |
| vacuum | M3 | 1 | 0.081 [0.073, 0.086] | 0.08 [0.07, 0.09] |
| power.plant_electric_production | M3 | 3 | 0.066 [0.064, 0.078] | 0.20 [0.19, 0.23] |
| ccfe_hcpb | M3 | 3 | 0.049 [0.046, 0.057] | 0.15 [0.14, 0.17] |
| buildings | M3 | 3 | 0.015 [0.014, 0.017] | 0.04 [0.04, 0.05] |
| divertor | M3 | 3 | 0.013 [0.012, 0.014] | 0.04 [0.04, 0.04] |
| fw | M3 | 3 | 0.012 [0.011, 0.013] | 0.04 [0.03, 0.04] |
| shield | M3 | 3 | 0.010 [0.009, 0.011] | 0.03 [0.03, 0.03] |
| availability | M3 | 3 | 0.008 [0.007, 0.009] | 0.02 [0.02, 0.03] |
| cryostat | M3 | 3 | 0.008 [0.008, 0.009] | 0.02 [0.02, 0.03] |
| structure | M3 | 3 | 0.007 [0.007, 0.008] | 0.02 [0.02, 0.02] |
| vacuum_vessel | M3 | 3 | 0.006 [0.005, 0.010] | 0.02 [0.02, 0.03] |
| power.acpow | M3 | 3 | 0.002 [0.002, 0.002] | 0.01 [0.01, 0.01] |
| costs | FF | 1 | 0.080 [0.079, 0.142] | 0.08 [0.08, 0.14] |
| water_use | FF | 1 | 0.018 [0.017, 0.032] | 0.02 [0.02, 0.03] |

*low_aspect_ratio_DEMO, A2*

| node | module | calls | ms per call | ms per evaluation |
|---|---|---|---|---|
| physics | M1 | 4 | 2.796 [2.754, 2.910] | 11.19 [11.02, 11.64] |
| plasma_geom | M1 | 4 | 0.026 [0.023, 0.057] | 0.10 [0.09, 0.23] |
| pfcoil | M2 | 5 | 1.963 [1.881, 2.150] | 9.82 [9.40, 10.75] |
| cicc_sctfcoil | M2 | 5 | 1.044 [0.980, 1.254] | 5.22 [4.90, 6.27] |
| build | M2 | 5 | 0.060 [0.053, 0.104] | 0.30 [0.26, 0.52] |
| pulse | PULSE | 1 | 0.010 [0.008, 0.021] | 0.01 [0.01, 0.02] |
| power | M3 | 3 | 0.389 [0.383, 0.581] | 1.17 [1.15, 1.74] |
| vacuum | M3 | 1 | 0.080 [0.073, 0.108] | 0.08 [0.07, 0.11] |
| power.plant_electric_production | M3 | 3 | 0.066 [0.063, 0.144] | 0.20 [0.19, 0.43] |
| ccfe_hcpb | M3 | 3 | 0.052 [0.046, 0.094] | 0.16 [0.14, 0.28] |
| divertor | M3 | 3 | 0.016 [0.012, 0.021] | 0.05 [0.03, 0.06] |
| buildings | M3 | 3 | 0.015 [0.015, 0.023] | 0.05 [0.04, 0.07] |
| fw | M3 | 3 | 0.013 [0.011, 0.015] | 0.04 [0.03, 0.04] |
| shield | M3 | 3 | 0.010 [0.009, 0.012] | 0.03 [0.03, 0.04] |
| availability | M3 | 3 | 0.009 [0.009, 0.010] | 0.03 [0.03, 0.03] |
| cryostat | M3 | 3 | 0.008 [0.008, 0.021] | 0.03 [0.02, 0.06] |
| structure | M3 | 3 | 0.007 [0.007, 0.017] | 0.02 [0.02, 0.05] |
| vacuum_vessel | M3 | 3 | 0.006 [0.006, 0.010] | 0.02 [0.02, 0.03] |
| power.acpow | M3 | 3 | 0.002 [0.002, 0.006] | 0.01 [0.01, 0.02] |
| costs | FF | 1 | 0.095 [0.084, 0.149] | 0.09 [0.08, 0.15] |
| water_use | FF | 1 | 0.018 [0.017, 0.031] | 0.02 [0.02, 0.03] |

*st_regression, A2*

| node | module | calls | ms per call | ms per evaluation |
|---|---|---|---|---|
| physics | M1 | 4 | 2.967 [2.711, 3.038] | 11.87 [10.84, 12.15] |
| plasma_geom | M1 | 4 | 0.024 [0.018, 0.030] | 0.09 [0.07, 0.12] |
| pfcoil | M2 | 6 | 1.662 [1.583, 1.875] | 9.97 [9.50, 11.25] |
| croco_sctfcoil | M2 | 6 | 1.306 [1.124, 1.473] | 7.83 [6.74, 8.84] |
| build | M2 | 6 | 0.046 [0.044, 0.057] | 0.28 [0.26, 0.34] |
| pulse | PULSE | 1 | 0.001 [0.001, 0.002] | 0.00 [0.00, 0.00] |
| power | M3 | 3 | 0.460 [0.444, 0.557] | 1.38 [1.33, 1.67] |
| ccfe_hcpb | M3 | 3 | 0.082 [0.079, 0.096] | 0.25 [0.24, 0.29] |
| power.plant_electric_production | M3 | 3 | 0.074 [0.066, 0.089] | 0.22 [0.20, 0.27] |
| vacuum | M3 | 1 | 0.068 [0.063, 0.094] | 0.07 [0.06, 0.09] |
| divertor | M3 | 3 | 0.016 [0.015, 0.017] | 0.05 [0.04, 0.05] |
| buildings | M3 | 3 | 0.015 [0.015, 0.017] | 0.05 [0.04, 0.05] |
| availability | M3 | 3 | 0.011 [0.010, 0.011] | 0.03 [0.03, 0.03] |
| fw | M3 | 3 | 0.011 [0.010, 0.011] | 0.03 [0.03, 0.03] |
| shield | M3 | 3 | 0.010 [0.009, 0.012] | 0.03 [0.03, 0.04] |
| cryostat | M3 | 3 | 0.009 [0.008, 0.022] | 0.03 [0.02, 0.06] |
| structure | M3 | 3 | 0.008 [0.007, 0.018] | 0.02 [0.02, 0.05] |
| vacuum_vessel | M3 | 3 | 0.006 [0.005, 0.008] | 0.02 [0.02, 0.03] |
| power.acpow | M3 | 3 | 0.002 [0.002, 0.003] | 0.01 [0.01, 0.01] |
| costs | FF | 1 | 0.092 [0.086, 0.165] | 0.09 [0.09, 0.17] |
| water_use | FF | 1 | 0.018 [0.017, 0.023] | 0.02 [0.02, 0.02] |

On `st_regression` the `pulse` node's 0.001 ms is a call that returns at once (`i_pulsed_plant = 0`); the
per-run set on that configuration is four nodes (`pulse`, `vacuum`, `costs`, `water_use`), three on the
pulsed ones.

## 5. Readings (context, never evidence)

1. **A block sweep costs what its nodes cost.** M1 ≈ M2 ≈ 2.8–3.2 ms per sweep of model time, M3 ≈
   0.6–0.7 ms, in the partitioned arm and — per FLAT sweep of the same nodes — in both flat arms alike
   (verdict table). The per-node figures do not change with the arm: `physics` 2.8–3.0 ms, `pfcoil`
   1.6–2.0 ms, the TF-coil model 0.9–1.3 ms, `power` 0.4–0.5 ms, everything else under 0.1 ms per call.
   A flat sweep is 6.4–6.8 ms of model time; the three iterated blocks together are 6.3–6.7 ms.
2. **The test is 1.3–1.6 ms per block sweep, and it scales with the components tested.** Residual 1.06–1.33
   ms for the blocks' 216–268 components (4.8–5.1 µs each; the widths are the timing child's own
   `narrowing.json`: M1 258/259/268, M2 240/244/216, M3 221/221/223 on nof/lad/st) against 3.85–3.98 ms for
   the flat block's 840/846/827 (4.6–4.8 µs each); the read 0.2–0.3 ms. So a block sweep of M3 (0.7 ms of
   model) pays a test twice its own size, and a flat sweep pays a test 60 % of its own size — the same
   per-component rate. The narrower set A89
   measured (`rbw`, 10–47 components) is what makes the test cheap; this survey did not run it.
3. **Dispatch overhead per sweep is 0.06–0.12 ms** — the injection 0.04–0.06 ms, the rest 0.02–0.05 ms —
   i.e. 3 % of an M1 or M2 sweep, 10–13 % of an M3 sweep, 1.5–1.7 % of a flat sweep. `A2`'s 14–16 sweeps per evaluation
   pay 1.2–1.3 ms of it in all; the flat arms' 5–8 sweeps 0.5–0.8 ms. **A89 §7.5's per-sweep hypothesis
   does not hold at this size**: the walk of the dispatch body past the nodes outside the block is cheap.
4. **What actually separates the deferring arms from V4's control is `module_schedule`: 8.7–9.3 ms per
   evaluation**, in `A0` and `A2` alike, 0.01–0.02 ms in `A0v4`. With the per-call deferral on,
   `module_schedule` → `resolved_defer_per_call_tail` → `resolved_defer_per_call_tails`, which on every
   call re-reads `node_writesets.json` from disk (`_node_write_sets`) and re-walks the AST of the
   objective and constraint source (`_predicate_read_fields`) to route the tail, and caches neither. It is
   15–16 % of an `A2` evaluation (55.5–61.0 ms) and 12–14 % of an `A0` one, and it is the "non-predicate
   time per node call" A89 §7.5 saw rise from 0.32 ms (`A0v4`) to 0.42–0.91 ms (`A0`, `A2`) — a fixed 9 ms
   spread over fewer node calls, not a per-sweep cost. This is implementation cost in the driver copy,
   and removable by a cache keyed on `i_figure_merit`; whether to remove it is the user's ruling (§7).
5. **Everything else is small.** `spec.bind` 0.06–0.09 ms, `_defer_per_run_nodes` 0.002 ms (cached),
   the objective 0.01 ms, the constraints 0.12–0.18 ms, and 0.24–0.41 ms per evaluation left
   unattributed after all of it.
6. **On these numbers, an `A2` evaluation is** (nof, survey press, medians of each part; medians do not
   sum exactly): 28.8 ms of sweeps (27.6 of model, 1.2 of dispatch) + 16.9 ms of test + 8.8 ms of
   `module_schedule` + 0.6 ms of the rest ≈ 55 ms against a `call_models` median of 55.5; V4's control
   is 39.6 + 24.7 + 0.0 + 0.5 ≈ 65 ms against 65.0. The partition's wall-clock saving here is 15 %
   against its 50 % node-call saving (63 vs 126), and the test plus the schedule account for the gap.

## 6. Autonomous decisions, each with its reversal

1. **A89's arm definitions kept** (`A0v4`, `A0` with feed-forward and per-run deferral, `A2` with the
   per-run set once), so these tables sit beside A89 §7.5. *Reversal:* V4's own `A2` without the
   once-per-run execution is `--arm A2` with `narrowing` not installed; the ONCE_PER_RUN row (0.23–0.27
   ms) is the whole difference.
2. **The cold entry was not timed.** A cold repetition needs a fresh process — the state after the warm-up
   is no longer cold — and a fresh process's first evaluation carries numba's dispatcher cost, which
   cannot be separated from the model time in it. The brief asked for it "if cheap"; it is not cheap to
   do honestly. *Reversal:* time the cold entry as a process-level quantity (whole subprocess, N
   subprocesses) and say so; the child takes no code change, the driver one flag.
3. **Test-time attribution by position** (the read before a block's first sweep charged to the block
   swept next). Correct for every iterated block; it mis-charges 0.16 ms of M3's first read to the empty
   PULSE visit on `st_regression` (§3.3). *Reversal:* attribute reads by the `subset` argument of the
   residual that follows them; the instrument's `read` wrapper would then hold each read until its
   residual arrives.
4. **Two presses, not more.** The brief asked for one press of 7 repetitions; the second was added after
   the first two presses were voided by contention (§8), to show a reader what identical code does one
   minute apart. *Reversal:* `--timing --press N` for any N; the summary renders every press it finds.
5. **Named per-evaluation timers added to the instrument** (`module_schedule`, per-run resolve, `bind`,
   objective, constraints) when the smoke test showed a 9 ms remainder the brief's three-way split could
   not place. *Reversal:* none needed; they are additive and the "unattributed" column shows what they
   leave.
6. **Contended records set aside, not deleted**: the two voided presses sit under
   `runs/block_sweep_timing/contended_2026-09-29_1357-1401/` in the worktree, untracked, and no table
   reads them. *Reversal:* delete the directory.

## 7. Limits, and what would be evidence

- Timings from one shared machine, one afternoon, 7 repetitions after one warm-up, two presses. Trap T5
  applies in full and §3.6 shows it. The **counts** (node calls, sweeps per block, reads and residuals
  per block, calls per node) are the exact quantities; they are identical across every repetition and
  press, and the verdict's shape rests on the per-node medians agreeing across three arms and two presses,
  not on any one figure.
- The instrument adds a closure allocation per `_node` call site (about 25 per sweep) and a wrapper
  around every read and residual; that is inside the dispatch and test columns respectively, at the
  microsecond level, and is the same in every arm.
- One displaced entry per configuration; no stencil, no optimisation path. Node costs are state-dependent
  (`physics` iterates internally); the spread across the three configurations (2.8–3.0 ms) is the only
  measure of that here.
- The whole-`y` test only. A89's narrowed sets change the test column and nothing else in these tables.
- Reading 4's mechanism is read from the driver copy's source at `c2ac4077` (`caller.py`:
  `resolved_defer_per_call_tails`, `_node_write_sets`, `_predicate_read_fields`) and matched by the timer
  that brackets `module_schedule`; the cache that would remove it is not written, tested or proposed here
  beyond naming it. Any change to the driver copy is a change to V4's published tree and is the user's
  ruling.
- Nothing here is a gate, and no gate was run.

## 8. Change log (append-only)

- 2026-09-29 — `dfbf3749`: instrument, child and driver committed; references, entries and a first
  timing press made. `d65f9194`: `--press N`; second press made. `14aad56a`: repeatability table carries
  `call_models` and `module_schedule`.
- 2026-09-29 — **Contention notice** from the orchestrator (received about 14:02 local): another task ran
  4 optimisation runs on 3 workers for about 70 s in a window given as roughly 13:52–13:59. The first
  press (13:57:43–13:58:41) lies inside it entirely; the second (13:59:52–14:00:58) starts too close to
  its stated end to be cleared. Both were voided and set aside unpublished (decision 6). The child did
  not stamp its window; `c821dbd6` adds `started_at`, `ended_at`, `taken_at` per repetition and the load
  average at exit, and the summary renders them (§3.5). Both presses re-taken at `c821dbd6`,
  14:02:59–14:04:34, with nothing else running per the orchestrator; every table in this document is
  from those. The references and entries (13:56–13:57, inside the window) carry only counts and bit-exact
  states and were not re-made.
- 2026-09-29 — Report written (this document); committed after the tip, touching no code.

## Orchestrator's critical assessment (protocol §5) — 2026-09-29

*By the orchestrating session (`process-surgery-65`), which dispatched the task to a task agent and did not execute it. Verified by checks the agent did not make, over the records and the code; nothing re-pressed.*

**Scope.** Four files added under `arch_surgery/block_sweep_timing/` and this report; `git diff c2ac4077..133f82d8` over `arch_surgery/MDA_partitioning_experiment_v4/`, `process/` and `harness/` is empty, and `git status --ignored` on the V4 folder is empty. Records untracked under `arch_surgery/idf_probe/runs/block_sweep_timing/`. Survey only; nothing acceptance-bearing.

**Checks made here.**

1. **Recount from the raw sweep records** (`large_tokamak_nof/timing/A2/sweep_timing.json`, per repetition the mean over that block's sweeps, then the median and [min, max] over the 7 repetitions): M1 2.94 [2.86, 3.14], M2 2.92 [2.84, 3.00], M3 0.67 [0.64, 0.69] ms per sweep; dispatch (sweep wall − Σ node calls) 0.094 / 0.084 / 0.083 ms — the verdict table's cells to the rounding.
2. **Stamps and windows** on all 18 published timing records: every one at `c821dbd6`; every subprocess started between 14:02:59 and 14:04:29, i.e. after the contention window the orchestrator declared (A90's four control runs ended ≈ 13:59); node calls and sweeps identical across the 7 repetitions of every case and between the two presses (nof `A0v4`/`A0`/`A2` 126/111/63 calls, 6/8/14 sweeps; lad 105/93/63, 5/7/14; st 126/106/66, 6/8/16). The two contended presses are set aside under `contended_2026-09-29_1357-1401/` and cited nowhere.
3. **The `module_schedule` finding, in the code and in the records.** In the driver copy, `_predicate_read_fields` is an `ast` walk over the objective and constraint sources with no cache, `_node_write_sets` re-reads `node_writesets.json` on every call, and `Caller._resolve_defer_per_call_tails` calls both on every `call_models` (its comment: "re-resolved on every call rather than memoised"). In the records: `other.module_schedule_s` per repetition is 8.1–10.6 ms in `A2` and 8.6–11.0 ms in `A0` (plus the one 86.6 ms outlier the report names), 0 in `A0v4`, against `call_models` of 54–57 ms in `A2`. The finding stands: **the deferring arms' non-model cost is a per-evaluation re-derivation of the deferral sets, not per-sweep dispatch**, which corrects the hypothesis A89 §7.5 put forward (recorded there as a hypothesis). It is an implementation cost of the driver copy; whether to cache it is the user's ruling (a driver change), filed as issue I-30 at merge. No published V4 number depends on it: V4's wall-clock section was withdrawn (D29), and counts are unaffected.
4. **Counts against A89.** `A2` at 63 node calls / 14 dispatch sweeps is A89's first-pass `A2 full` (60 / 13, displaced seed 1, τ = 1e-6) plus the once-per-run set executed once (+3 calls, +1 sweep) — consistent.

**On the report.** The verdict states that every timing is context, never evidence, and the tables carry median, [min, max] and the repetition count; the PULSE mis-charge (0.16 ms of M3's entry read charged to the empty sweep by the position rule) is stated rather than corrected, which is right for a survey. The cold entry was not timed, for a stated reason with a reversal; the `A0` second-repetition `module_schedule` spike is reported as an unexplained oddity — acceptable, since nothing rests on it.

**Verdict: merge.** Carried forward: I-30 (the uncached deferral-set derivation, a candidate driver change for the user's ruling); the per-block test cost (≈5 µs per component tested, 1.3–1.6 ms per block sweep) is the context V5 item 6 should quote beside its census-set numbers.
