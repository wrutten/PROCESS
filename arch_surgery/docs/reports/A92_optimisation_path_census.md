# A92 (optimisation-path-census) — the read-before-write census over an optimisation run, and its teeth

> **Document status** — **OPEN.** Task A92 (optimisation-path-census), 2026-09-29, on branch
> `A92-optimisation-path-census`, worktree `.claude/worktrees/A92-optimisation-path-census`, base
> `9cfb5687` (= `architecture_surgery`). V5 improvement list item 6, prerequisite (2): the
> census-measured feedback set (ruling D32) measured over an optimisation run's evaluations, and a
> test with teeth. Exploratory for V5; **not** a V4 result — V4's campaign, harness and report are
> untouched, and no source file under the V4 folder was written (numba cache files were, §7
> decision 4). Records (untracked): `arch_surgery/idf_probe/runs/optimisation_path_census/`.
> Scripts: `arch_surgery/coupling_subset_trial/` — `optimisation_path_census.py` (the stages),
> `censused_optimise.py`, `rbw_census.py`, `narrowing.py`; the commit each stage ran at is under
> every table, and the record stamps are surveyed in §6.1. The orchestrator's assessment is
> appended before merge.

## 1. Verdict

1. **The 8-entry census set covers the optimiser's path.** Over twelve whole optimisation runs
   (three configurations × `B0` flat / `B2` partitioned × the campaign's seed 0 and seed 1; 23 128
   evaluations, of them 12 200 finite-difference probes, 313 line-search points and 311 repeated
   points — `--summarise-census` totals at `f7f9b136`), every component read
   before its first write in any loop sweep is either in A89's 8-entry set for the twin
   evaluation-phase arm or is carried **only at evaluation 0 of the run, in both seeds** — the cold
   start's first sweep, where two models' `first_call` flags and two `pf_coil`/`build` fields are
   read at their defaults before being set. No component of the 8-entry sets is absent on the
   path. **Nothing must be added for the optimiser's path**; the cold-start components (4 on the
   pulsed configurations, 2 on `st_regression`) are inert after their first write and cannot hold a
   loop open or let it stop early (§4.2); V5 may carry them or not, and §8 says which.
2. **The census is observation-only.** All 12 censused runs reproduce their campaign record on
   status, `ifail`, solver iterations, evaluations, solve-phase node calls and `norm_objf` bit for
   bit (12 of 12, §4.1).
3. **The teeth do not bite at τ = 1e-8, and the declared criterion fails.** Of 19 carried
   components dropped one at a time (evaluation phase, displaced entry, 3 configurations × `A0`/`A2`),
   17 are not individually binding on that entry (sweeps identical, exit state bit-identical) and 6
   of 6 controls pass. The two remaining drops — `pf_coil.stress_z_cs_self_midplane_profile` on
   `large_tokamak_nof`, in both arms — stop the loop **one sweep earlier** (flat 7 → 6; `M2` 7 → 6)
   and the whole-`y` exit audit rises 50× (4.9e-11 → 2.6e-09) and 50× (5.2e-12 → 2.7e-10) but
   **stays below τ**: the dropped component escapes the audit *as a threshold test at τ*. The
   mechanism (§5.2): the audit measures the next sweep's contraction, which after a one-sweep-early
   stop is the very quantity the full loop just accepted as converged. **A whole-`y` audit at τ is
   not a tooth for a one-sweep-early stop**; the exit-state comparison against the full set's exit
   is (bit-identical for the 17 non-binding drops and every control, 2.6e-09 / 2.7e-10 for the
   two that bit). This is a result, not tuned; what would make a tooth is proposed in §8.

## 2. Question

A89 (coupling-subset-trial) measured the **read-before-write set** — the components of the
coupling state `y` a sweep reads before it first writes them, and writes later in the same sweep;
per block, in the arm's own execution order — on 8 displaced entries per configuration and arm
(`coupling_subset_trial/rbw_sets.json`: `FLAT` for the flat loop `A0`, `M1`/`M2`/`M3` for the
partitioned arm `A2`; A89 §7.2). V5 converges on that set (D32). Two things stand between the
8-entry set and a verdict (V5 list item 6, prerequisite (2)):

1. **Coverage of the optimiser's path.** An optimisation visits points the displaced entries do
   not: finite-difference probes of one design variable, line-search points, retries, and the cold
   start. A branch taken only there is unobserved by an 8-entry census. Is the 8-entry set the set
   an optimisation carries?
2. **Teeth.** A test set is shown *capable of failing* before its zeros are accepted (protocol
   §12): dropping one carried component must be caught by the whole-`y` exit audit. Does it bite?

## 3. Method

### 3.1 Machinery

Everything is in `arch_surgery/coupling_subset_trial/`, built on A89's scratch machinery, outside
the V4 folder. V4's own children, pool composition and driver copy run unchanged, in-process, with
wrappers installed after `process` is imported.

| file | what |
|---|---|
| `rbw_census.py` | A89's instrument: `__getattribute__` / `__setattr__` hooks on the data-structure namespaces restricted to `y`, a value diff of every `y` component across each node (an in-place array write never reaches `__setattr__`; the fetch that precedes it counts as a read, so such a component is included — the conservative direction, A89 §7.2), one window per `Caller._sweep_block`. **A92 additions, additive:** a per-evaluation mode (`enable_per_evaluation`, `begin_evaluation`, `end_evaluation`) writing its own file `rbw_census_per_evaluation.json` — per evaluation the sweeps per block, the set per block, and how many design-vector components moved since the previous evaluation (one = a finite-difference probe); and a snapshot robust to a component's type changing between nodes (§7, decision 2). A89's `rbw_census.json` format and `--derive-rbw` are unchanged. |
| `censused_optimise.py` | V4's `harness/child/optimise.py` run in-process with the census installed on the first `call_models` and every `call_models` bracketed as one evaluation. **Observation-only**: nothing is narrowed; the loops test what the arm's environment says, the burn time is owned by whoever the arm says, the once-per-run set runs where the driver runs it. |
| `narrowing.py` | A89's substitutions. **A92 addition:** the test-set kind `rbw-minus:<key>` — the arm's 8-entry sets with one component removed from every block that carries it; `narrowing.json` records the key and the blocks it was removed from (an empty list = the control). |
| `optimisation_path_census.py` | The stages: `--lifted-inputs`, `--census`, `--estimate`, `--check-reproduction`, `--summarise-census`, `--references`, `--teeth`, `--summarise-teeth`. The teeth's selection rules and criterion are declared in its docstring (§3.4). It rebinds A89's `run_trial.RUNS` to this task's records directory and otherwise calls A89's stages as they stand. |
| `optimisation_path_sets.json` | Generated by `--summarise-census`, committed (`1821dae1`, totals block added at `f7f9b136`): the sets on the path per configuration, arm and block, first appearance and carry counts per component, the per-evaluation size distributions, the comparison with the 8-entry sets, the totals over the runs. |

Every PROCESS run is a fresh subprocess in its own directory, `PYTHONPATH` at this worktree's V4
copy and `process.__file__` asserted equal to it in the child (trap T6),
`PYTHONDONTWRITEBYTECODE=1`, numba's cache under the runs directory (except the derivation stage,
§7 decision 4). One PROCESS process at a time throughout (A93 shares the machine; timings are
context only, never evidence).

### 3.2 The optimisation-path census

- **Arms.** `B0` (V4's flat optimisation arm: one block over every in-loop node, burn time in the
  loop, upstream output loop) and `B2` (partitioned: block Gauss–Seidel `M1`/`M2`/`M3`, burn time
  owned by the optimiser, lifted input file, no output loop). Composed by V4's
  `pool.environment_for` and `pool._command`; the lifted input files derived in this tree by V4's
  committed derivation (`input_files.derive_one`: one gate-kind `AR` evaluation per pulsed
  configuration, bytes gated on the declared digest — both PASS, `summary/lifted_inputs.json`).
- **Starts.** The campaign's `seed000` (the input file's own point) and `seed001` (the design
  vector displaced by the V4 child's own seeded stream at δ = 0.10), so each run pairs with a
  campaign record. Twelve whole runs; run kind `smoke`.
- **Reproduction check** (`--check-reproduction`): each censused run against its campaign record
  (`idf_probe/runs/A90_runs/campaign/optimisation/`, read through `records.read` so the recorded
  arm name `B3` translates to today's `B2`, trap T16) on `status`, `ifail`, `n_solver_iterations`,
  `sweeps_per_eval.n_evaluations`, `node_calls_solve_phase` and `norm_objf` (hex). A mismatch is a
  finding.
- **Twin sets.** `B0` is compared with A89's `A0` set, `B2` with A89's `A2` sets — the same loop
  shapes in the evaluation phase — with two declared differences: A89's `A0` deferred the
  feed-forward nodes out of its flat block (`PROCESS_ARCH_DEFER_PER_CALL=feedforward`) where `B0`
  sweeps them; and the burn time is a loop variable in `B0`, a constant in `A2`, the optimiser's in
  `B2`. The comparison names the reader and writer node and module of every differing component.
- **Per evaluation:** the set per block; the union over the run; the evaluation at which each
  component first appears (with what moved in the design vector there); how many evaluations carry
  it and the last one that does; the set-size distribution, also by the evaluation's sweep count.

### 3.3 Cost of the instrument, and the decision to run all twelve

The first whole run (`large_tokamak_nof` `B0` seed 0) was made alone; `--estimate` projected the
other eleven from the campaign records' wall clock at its factor (4.7×): 1.3 h. That fits, so all
twelve were run — whole runs only; a truncated run observes no path (§4.1).

### 3.4 Teeth — rules and criterion, declared before the stage ran

From `optimisation_path_census.py`'s docstring at `5a0b419a` (the tie-break was added to the text
at that commit, before the stage ran; the selection code was unchanged since `9404f632`).

Evaluation phase, A89's `--run` machinery: displaced entry (seed 1, δ = 0.10 around the entry
reference made in this tree), arms `A0` (flat, feed-forward nodes deferred, per-run set once after
convergence) and `A2` (partitioned), τ = 1e-8 (`tolerance.json`), test set = the arm's 8-entry
census set minus one component, chosen per configuration and arm by rule:

1. `max_exit_residual_carried` — the carried component with the largest whole-`y` exit residual
   under the full census test (from the full `rbw` run's `audit_residual.json`; ties, including a
   whole set at 0.0, go to the alphabetically last key);
2. `pf_coil_self_read` — the alphabetically first `pf_coil.*` component among the set's
   DSM-self-read-only components;
3. `most_sweeps_carried` — the component carried in the most census sweeps
   (`detail[*][key].n_sweeps` summed over blocks; ties alphabetical);
4. `burn_time` — `times.t_plant_pulse_burn` where the set carries it;
5. control `max_exit_residual_not_carried` — the component **not** in the set with the largest
   whole-`y` exit residual under the full census test (ties as rule 1).

A component satisfying several rules is run once and listed under all of them.

**Criterion.** With a carried component dropped, either the loop stops earlier (some block takes
fewer sweeps than with the full set) **and** the whole-`y` exit audit shows ≥ 1 component ≥ τ
(*bites*); or nothing changes — sweeps identical per block and the exit state bit-identical — in
which case the component is not individually binding on that entry (*not binding*; a set can be a
correct cut set while no single member binds on a given entry). Fewer sweeps with a clean audit
means the drop escaped the audit at τ (*escapes*); any other outcome is reported as it is
(*other*). With the control dropped nothing may change (*control PASS* / *FAIL*). No run is tuned
or repeated.

## 4. The optimisation-path census

### 4.1 The instrument's cost (context) and reproduction of the campaign records

**Table 1** — each censused run against its campaign record. *Rows:* one whole optimisation
(configuration, arm, campaign seed). *Columns:* the six compared fields (`ifail` from the exit
forensics, evaluations = `sweeps_per_eval.n_evaluations`, node calls of the solve phase,
`norm_objf` as a hex float), then context: solve-phase sweeps, optimiser attempts, wall clock of
the campaign run and of the censused run (seconds; this machine, A93 running concurrently, never
evidence), and whether every compared field is identical. *Population:* 12 of 12 runs.
`optimisation_path_census.py --check-reproduction` at `1e997a55` over records stamped
`9f3d4148`/`5a0b419a`/`84dde2f7` (§6.1); campaign records at `57dc0c14`.

| configuration | arm | seed | status | ifail | iterations | evaluations | node calls (solve) | norm_objf (hex) | sweeps (solve) | attempts | wall s campaign / censused | identical |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | B0 | 0 | ok | 1 | 8 | 630 | 43449 | 0x1.99999999b822ap+0 | 2069 | 1 | 28 / 133 | yes |
| large_tokamak_nof | B0 | 1 | ok | 1 | 8 | 630 | 43491 | 0x1.99999999c8db5p+0 | 2071 | 1 | 29 / 91 | yes |
| large_tokamak_nof | B2 | 0 | ok | 1 | 8 | 660 | 28055 | 0x1.9999999a4496cp+0 | 5499 | 1 | 30 / 73 | yes |
| large_tokamak_nof | B2 | 1 | ok | 1 | 8 | 660 | 28037 | 0x1.99999999bb397p+0 | 5496 | 1 | 29 / 71 | yes |
| low_aspect_ratio_DEMO | B0 | 0 | ok | 1 | 16 | 1240 | 86877 | -0x1.a00c1e754455cp-2 | 4137 | 1 | 56 / 172 | yes |
| low_aspect_ratio_DEMO | B0 | 1 | ok | 1 | 16 | 9240 | 655473 | -0x1.9f9030eb8b43dp-2 | 31213 | 2 | 428 / 1365 | yes |
| low_aspect_ratio_DEMO | B2 | 0 | ok | 1 | 13 | 1050 | 45496 | -0x1.a00c0bc88c2c6p-2 | 8762 | 1 | 50 / 116 | yes |
| low_aspect_ratio_DEMO | B2 | 1 | ok | 1 | 15 | 1218 | 52834 | -0x1.9fb1afe0ebcf7p-2 | 10182 | 1 | 57 / 131 | yes |
| st_regression | B0 | 0 | ok | 1 | 10 | 570 | 42756 | -0x1.096acf3342e3cp+4 | 2036 | 1 | 28 / 95 | yes |
| st_regression | B0 | 1 | ok | 1 | 53 | 3150 | 226002 | -0x1.0cf146aad761fp+4 | 10762 | 1 | 145 / 443 | yes |
| st_regression | B2 | 0 | ok | 1 | 10 | 570 | 23505 | -0x1.096acf3342e55p+4 | 5259 | 1 | 27 / 65 | yes |
| st_regression | B2 | 1 | ok | 1 | 59 | 3510 | 134560 | -0x1.0cf146c754521p+4 | 31071 | 1 | 150 / 347 | yes |

**12 of 12 reproduce.** The census is observation-only on every count and on the objective's bits,
including the retried `low_aspect_ratio_DEMO` `B0` seed 1 (2 attempts, 9 240 evaluations). The
wall-clock factor of the instrument is 2.3–4.7 (median 2.7; the first run, 4.7, carries numba's
JIT in a fresh cache); it is what the hooks cost, and no number here rests on it.

### 4.2 The sets on the optimiser's path against the 8-entry sets

**Table 2** — the read-before-write set per iterated block, union over the run's evaluations,
both seeds pooled. *Columns:* evaluations in the two runs; components on the path; in A89's 8-entry
set for the twin arm; common to both; on the path but not in the 8-entry set; in the 8-entry set
but never on the path; how many of the path's components are first seen at evaluation 0 / later;
the per-evaluation set size (min / median / max over both runs). *Population:* the twelve runs of
Table 1; the once-run node sets (`PULSE` on `st_regression`, the per-call tail and the once-per-run
set, unlabelled) are not loops and have no row. `optimisation_path_census.py --summarise-census` at
`84dde2f7` (`optimisation_path_sets.json` committed at `1821dae1`; re-run at `f7f9b136`, which
regenerated the file byte-identical but for the added `totals` block); 8-entry sets from
`rbw_sets.json` (`2b6aaca4`).

| configuration | arm | block | evaluations (seed 0 / seed 1) | on path | 8-entry | common | on path, not 8-entry | 8-entry, not on path | first seen at evaluation 0 / later | set size per evaluation min / median / max |
|---|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | B0 | FLAT | 630/630 | 79 | 75 | 75 | 4 | 0 | 79 / 0 | 45 / 68 / 79 |
| large_tokamak_nof | B2 | M1 | 660/660 | 17 | 16 | 16 | 1 | 0 | 17 / 0 | 16 / 16 / 17 |
| large_tokamak_nof | B2 | M2 | 660/660 | 50 | 47 | 47 | 3 | 0 | 50 / 0 | 18 / 40 / 50 |
| large_tokamak_nof | B2 | M3 | 660/660 | 10 | 10 | 10 | 0 | 0 | 10 / 0 | 9 / 10 / 10 |
| low_aspect_ratio_DEMO | B0 | FLAT | 1240/9240 | 78 | 74 | 74 | 4 | 0 | 78 / 0 | 44 / 67 / 78 |
| low_aspect_ratio_DEMO | B2 | M1 | 1050/1218 | 17 | 16 | 16 | 1 | 0 | 17 / 0 | 16 / 16 / 17 |
| low_aspect_ratio_DEMO | B2 | M2 | 1050/1218 | 49 | 46 | 46 | 3 | 0 | 49 / 0 | 17 / 39 / 49 |
| low_aspect_ratio_DEMO | B2 | M3 | 1050/1218 | 10 | 10 | 10 | 0 | 0 | 10 / 0 | 9 / 10 / 10 |
| st_regression | B0 | FLAT | 570/3150 | 75 | 73 | 73 | 2 | 0 | 75 / 0 | 44 / 71 / 75 |
| st_regression | B2 | M1 | 570/3510 | 17 | 16 | 16 | 1 | 0 | 17 / 0 | 16 / 16 / 17 |
| st_regression | B2 | M2 | 570/3510 | 48 | 47 | 47 | 1 | 0 | 48 / 0 | 19 / 45 / 48 |
| st_regression | B2 | M3 | 570/3510 | 10 | 10 | 10 | 0 | 0 | 10 / 0 | 9 / 10 / 10 |

Three readings.

1. **The 8-entry set is contained in the path's set in every block of every arm and
   configuration**, and every component of it is carried on the path (the "8-entry, not on path"
   column is 0 throughout). The 8 displaced entries missed no component the optimiser's path
   carries, other than the cold start's.
2. **Every component on the path beyond the 8-entry set is carried at evaluation 0 only, in both
   seeds** (Table 3). They are the cold start's first sweep: a flag or field read at its default
   before the model sets it. The four on the pulsed configurations are `physics.first_call`
   (reader and writer `physics`, `M1`), `pf_coil.first_call` (reader and writer `pfcoil`, `M2`),
   `pf_coil.n_pf_coils_in_group` (writer `pfcoil`, reader `cicc_sctfcoil`, `M2`) and
   `build.dz_xpoint_divertor` (reader and writer `build`, `M2`); `st_regression` carries the two
   `first_call` flags only. In `B2` they land in the block of their writer. After that first
   write they are constant for the rest of the run (carried in 1 of 570–9 240 evaluations, last at
   evaluation 0), so whether a test set holds them changes no loop's stopping: a constant
   component contributes 0 to every residual after its first write, and a set without it cannot
   stop early on its account because it never moves again.
3. **The feed-forward nodes that `B0` sweeps and A89's `A0` deferred carry nothing.** `B0`'s
   flat block includes `costs`, `water_use` and the other `FF` nodes in every sweep; none of their
   writes is read before written by anything in the loop, so the flat set on the path is A89's
   flat set plus the cold-start components and nothing else. The same holds for the burn time
   (§4.4).

**Table 3** — the components on the path but not in the 8-entry set, one row each. *Columns:* the
component, its reader and writer node with the node map's module, the evaluation at which it
first appears (with the number of design-vector components that moved into that evaluation —
none at evaluation 0, the first), the evaluations that carry it out of the run's total, per seed.
*Population:* the 4 / 4 / 2 components of Table 2's "on path, not 8-entry" column, on `B0`; on
`B2` the same components fall in the block of their writer (`physics.first_call` in `M1`, the
other three in `M2`) with identical counts. `--summarise-census` at `84dde2f7`.

| configuration | component | reader [module] | writer [module] | first at evaluation | carried in evaluations, seed 0 / seed 1 |
|---|---|---|---|---|---|
| large_tokamak_nof | `build.dz_xpoint_divertor` | build [M2] | build [M2] | 0 | 1 of 630 / 1 of 630 |
| large_tokamak_nof | `pf_coil.first_call` | pfcoil [M2] | pfcoil [M2] | 0 | 1 of 630 / 1 of 630 |
| large_tokamak_nof | `pf_coil.n_pf_coils_in_group` | cicc_sctfcoil [M2] | pfcoil [M2] | 0 | 1 of 630 / 1 of 630 |
| large_tokamak_nof | `physics.first_call` | physics [M1] | physics [M1] | 0 | 1 of 630 / 1 of 630 |
| low_aspect_ratio_DEMO | `build.dz_xpoint_divertor` | build [M2] | build [M2] | 0 | 1 of 1240 / 1 of 9240 |
| low_aspect_ratio_DEMO | `pf_coil.first_call` | pfcoil [M2] | pfcoil [M2] | 0 | 1 of 1240 / 1 of 9240 |
| low_aspect_ratio_DEMO | `pf_coil.n_pf_coils_in_group` | cicc_sctfcoil [M2] | pfcoil [M2] | 0 | 1 of 1240 / 1 of 9240 |
| low_aspect_ratio_DEMO | `physics.first_call` | physics [M1] | physics [M1] | 0 | 1 of 1240 / 1 of 9240 |
| st_regression | `pf_coil.first_call` | pfcoil [M2] | pfcoil [M2] | 0 | 1 of 570 / 1 of 3150 |
| st_regression | `physics.first_call` | physics [M1] | physics [M1] | 0 | 1 of 570 / 1 of 3150 |

### 4.3 What the per-evaluation set looks like

**Table 4** — per run and iterated block: what the optimiser's evaluations were and how the set
varies across them. *Columns:* evaluations; evaluations into which exactly one design-vector
component moved (finite-difference probes); two moved (the step from `x_i(1−h)` to `x_{i+1}(1+h)`
in VMCON's central-difference stencil); all `n` moved (line-search points); none moved (a repeated
evaluation of the same point); then per block the components carried in **every** evaluation, the
number of distinct per-evaluation sets, the evaluations whose set equals the run's union, and the
median set size by the evaluation's sweep count (1 / 2 / 3 sweeps, and the range for 4 or more).
*Population:* the twelve runs. Extracted from `optimisation_path_sets.json` (`1821dae1`) by the
census-summary stage's per-run fields.

| configuration | arm | seed | evaluations | 1 moved (probes) | 2 moved | all moved | none moved | block | carried in every evaluation | distinct sets | equal to run union | median size at 1 / 2 / 3 sweeps; range at 4+ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | B0 | 0 | 630 | 330 | 285 | 7 | 7 | FLAT | 45 | 11 | 1 | 45 / 45 / 50; 73–79 |
| large_tokamak_nof | B0 | 1 | 630 | 330 | 285 | 7 | 7 | FLAT | 45 | 10 | 1 | 45 / 45 / 50; 73–79 |
| large_tokamak_nof | B2 | 0 | 660 | 345 | 300 | 7 | 7 | M1 | 16 | 2 | 1 | 16 / 16 / 16; 16–17 |
| large_tokamak_nof | B2 | 0 | 660 | 345 | 300 | 7 | 7 | M2 | 18 | 9 | 1 | 18 / 18 / 40; 45–50 |
| large_tokamak_nof | B2 | 0 | 660 | 345 | 300 | 7 | 7 | M3 | 9 | 2 | 383 | 9 / 9 / 10; — |
| large_tokamak_nof | B2 | 1 | 660 | 345 | 300 | 7 | 7 | M1 | 16 | 2 | 1 | 16 / 16 / 16; 16–17 |
| large_tokamak_nof | B2 | 1 | 660 | 345 | 300 | 7 | 7 | M2 | 18 | 9 | 1 | 18 / 18 / 40; 45–50 |
| large_tokamak_nof | B2 | 1 | 660 | 345 | 300 | 7 | 7 | M3 | 9 | 2 | 398 | 9 / 9 / 10; — |
| low_aspect_ratio_DEMO | B0 | 0 | 1240 | 651 | 558 | 15 | 15 | FLAT | 44 | 18 | 1 | 44 / 44 / 58; 71–78 |
| low_aspect_ratio_DEMO | B0 | 1 | 9240 | 4851 | 4158 | 116 | 114 | FLAT | 44 | 15 | 1 | 44 / 44 / 49; 45–78 |
| low_aspect_ratio_DEMO | B2 | 0 | 1050 | 550 | 475 | 12 | 12 | M1 | 16 | 2 | 1 | 16 / 16 / 16; 17 |
| low_aspect_ratio_DEMO | B2 | 0 | 1050 | 550 | 475 | 12 | 12 | M2 | 17 | 12 | 1 | 17 / 17 / 39; 43–49 |
| low_aspect_ratio_DEMO | B2 | 0 | 1050 | 550 | 475 | 12 | 12 | M3 | 9 | 2 | 688 | 9 / 9 / 10; — |
| low_aspect_ratio_DEMO | B2 | 1 | 1218 | 638 | 551 | 14 | 14 | M1 | 16 | 2 | 1 | 16 / 16 / 16; 16–17 |
| low_aspect_ratio_DEMO | B2 | 1 | 1218 | 638 | 551 | 14 | 14 | M2 | 17 | 12 | 1 | 17 / 17 / 39; 43–49 |
| low_aspect_ratio_DEMO | B2 | 1 | 1218 | 638 | 551 | 14 | 14 | M3 | 9 | 2 | 798 | 9 / 9 / 10; — |
| st_regression | B0 | 0 | 570 | 304 | 247 | 9 | 9 | FLAT | 44 | 6 | 1 | 44 / 44 / 66; 44–75 |
| st_regression | B0 | 1 | 3150 | 1680 | 1365 | 52 | 52 | FLAT | 44 | 17 | 1 | 44 / 44 / 66; 44–75 |
| st_regression | B2 | 0 | 570 | 304 | 247 | 9 | 9 | M1 | 16 | 2 | 1 | 16 / 16 / 16; 16–17 |
| st_regression | B2 | 0 | 570 | 304 | 247 | 9 | 9 | M2 | 19 | 14 | 1 | 19 / 45 / 46; 45–48 |
| st_regression | B2 | 0 | 570 | 304 | 247 | 9 | 9 | M3 | 9 | 2 | 447 | 9 / 10 / 10; 10 |
| st_regression | B2 | 1 | 3510 | 1872 | 1521 | 58 | 58 | M1 | 16 | 2 | 1 | 16 / 16 / 16; 16–17 |
| st_regression | B2 | 1 | 3510 | 1872 | 1521 | 58 | 58 | M2 | 19 | 39 | 1 | 19 / 45 / 46; 45–48 |
| st_regression | B2 | 1 | 3510 | 1872 | 1521 | 58 | 58 | M3 | 9 | 2 | 2679 | 9 / 10 / 10; 10 |

Two readings.

1. **The per-evaluation set is not the structural set; the union is.** The instrument sees an
   in-place array write only when the value changes, so an evaluation that converges in one or two
   sweeps registers the scalar reads (44–45 in the flat loop, 16–19 in `M1`/`M2`) and few of the
   array ones; an evaluation of four or more sweeps registers 73–79. The structural set — what a
   sweep *can* read before it writes — is the union, which the 8 displaced entries (each of 5–7
   sweeps at τ = 1e-6, A89 §7.2) reached. This is why the 8-entry census agrees with the path: it
   was taken on the sweeps that register everything, and the path adds only the cold start. The
   union equals the run's set at exactly one evaluation in every loop block — evaluation 0 — with
   the cold-start components; `M3`'s 10 components register in most evaluations.
2. **The probes are where the path differs from a displaced entry, and they add nothing.** Half of
   every run's evaluations are one-variable probes (330 of 630, 4 851 of 9 240) and the line-search
   points are 1–2 %. No component first appears on a probe or a line-search point (Table 3: every
   first appearance beyond the 8-entry set is at evaluation 0, before any variable has moved).

### 4.4 The burn time

`times.t_plant_pulse_burn` is carried in `B0`'s flat loop on both pulsed configurations (writer
`pulse`, reader `physics`, in every sweep: 2 069 of 2 069 on `large_tokamak_nof` seed 0, 4 137 of
4 137 on `low_aspect_ratio_DEMO` seed 0) and in A89's `A0` set likewise — the loop owns it in
both. In `B2` it is nowhere on the path (no block reads it before writing it): the optimiser owns
it, `pulse`'s write is the value the owner put there (plan §4.1d), and `pulse` itself is in the
per-call tail, swept once per evaluation outside every loop. A89's `A2` (a constant owns it) does
not carry it either. On `st_regression` neither arm carries it (no burn-time coupling). So the
two phases own the burn time differently and the census sees the same thing in both: **a loop
variable where the loop owns it, absent where it does not** — no reader of the burn time appears
on the optimiser's path that the displaced entries did not show.

## 5. Teeth

### 5.1 The table

**Table 5** — one evaluation per row, displaced entry (seed 1, δ = 0.10), τ = 1e-8. *Rows:* per
configuration and arm, the full census set (A89's `rbw`, the reference row), then each dropped
component with the rule(s) that chose it and the blocks it was removed from (`none` = the
control). *Columns:* sweeps per block (full → dropped), node calls of the evaluation (full →
dropped; the per-run set's single execution included, as in A89), the whole-`y` exit-audit
maximum, components ≥ τ at exit, the exit state against the full set's exit (bit-identical, or
the maximum scaled residual between the two on V4's frozen ruler), and the verdict by §3.4's
criterion. *Population:* 3 configurations × 2 arms: 6 full runs, 19 carried drops, 6 controls.
`optimisation_path_census.py --references --teeth` (records stamped `84dde2f7`/`1821dae1`/
`1e997a55`, §6.1) and `--summarise-teeth` at `1e997a55`.

| configuration | arm | dropped component | rule(s) | dropped from blocks | sweeps per block (full → dropped) | node calls (full → dropped) | exit audit max (whole y) | above τ at exit | exit state vs full | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | A0 | — (full census set) | — | — | FLAT 7 | 129 | 4.9e-11 | 0 | — | — |
| large_tokamak_nof | A0 | `blanket.deg_blkt_inboard_poloidal_plasma` | most_sweeps_carried | FLAT | FLAT 7 → 7 | 129 → 129 | 4.9e-11 | 0 | bit-identical | not binding |
| large_tokamak_nof | A0 | `costs.coecap` | max_exit_residual_not_carried | none (control) | FLAT 7 → 7 | 129 → 129 | 4.9e-11 | 0 | bit-identical | control PASS |
| large_tokamak_nof | A0 | `pf_coil.ccl0_ma` | pf_coil_self_read | FLAT | FLAT 7 → 7 | 129 → 129 | 4.9e-11 | 0 | bit-identical | not binding |
| large_tokamak_nof | A0 | `pf_coil.stress_z_cs_self_midplane_profile` | max_exit_residual_carried | FLAT | FLAT 7 → 6 | 129 → 111 | 2.6e-09 | 0 | 2.6e-09 | **ESCAPES** |
| large_tokamak_nof | A0 | `times.t_plant_pulse_burn` | burn_time | FLAT | FLAT 7 → 7 | 129 → 129 | 4.9e-11 | 0 | bit-identical | not binding |
| large_tokamak_nof | A2 | — (full census set) | — | — | M1 3, M2 7, M3 2 | 55 | 5.2e-12 | 0 | — | — |
| large_tokamak_nof | A2 | `impurity_radiation.f_nd_impurity_electron_array` | most_sweeps_carried | M1, M2, M3 | M1 3 → 3, M2 7 → 7, M3 2 → 2 | 55 → 55 | 5.2e-12 | 0 | bit-identical | not binding |
| large_tokamak_nof | A2 | `pf_coil.ccl0_ma` | pf_coil_self_read | M2 | M1 3 → 3, M2 7 → 7, M3 2 → 2 | 55 → 55 | 5.2e-12 | 0 | bit-identical | not binding |
| large_tokamak_nof | A2 | `pf_coil.stress_z_cs_self_midplane_profile` | max_exit_residual_carried | M2 | M1 3 → 3, M2 7 → 6, M3 2 → 2 | 55 → 52 | 2.7e-10 | 0 | 2.7e-10 | **ESCAPES** |
| large_tokamak_nof | A2 | `superconducting_tfcoil.a_tf_plasma_case` | max_exit_residual_not_carried | none (control) | M1 3 → 3, M2 7 → 7, M3 2 → 2 | 55 → 55 | 5.2e-12 | 0 | bit-identical | control PASS |
| low_aspect_ratio_DEMO | A0 | — (full census set) | — | — | FLAT 5 | 93 | 0.0e+00 | 0 | — | — |
| low_aspect_ratio_DEMO | A0 | `blanket.deg_blkt_inboard_poloidal_plasma` | most_sweeps_carried | FLAT | FLAT 5 → 5 | 93 → 93 | 0.0e+00 | 0 | bit-identical | not binding |
| low_aspect_ratio_DEMO | A0 | `pf_coil.ccl0_ma` | pf_coil_self_read | FLAT | FLAT 5 → 5 | 93 → 93 | 0.0e+00 | 0 | bit-identical | not binding |
| low_aspect_ratio_DEMO | A0 | `times.t_plant_pulse_burn` | max_exit_residual_carried, burn_time | FLAT | FLAT 5 → 5 | 93 → 93 | 0.0e+00 | 0 | bit-identical | not binding |
| low_aspect_ratio_DEMO | A0 | `water_use.waterusetower` | max_exit_residual_not_carried | none (control) | FLAT 5 → 5 | 93 → 93 | 0.0e+00 | 0 | bit-identical | control PASS |
| low_aspect_ratio_DEMO | A2 | — (full census set) | — | — | M1 3, M2 5, M3 2 | 49 | 0.0e+00 | 0 | — | — |
| low_aspect_ratio_DEMO | A2 | `impurity_radiation.f_nd_impurity_electron_array` | most_sweeps_carried | M1, M2, M3 | M1 3 → 3, M2 5 → 5, M3 2 → 2 | 49 → 49 | 0.0e+00 | 0 | bit-identical | not binding |
| low_aspect_ratio_DEMO | A2 | `pf_coil.ccl0_ma` | pf_coil_self_read | M2 | M1 3 → 3, M2 5 → 5, M3 2 → 2 | 49 → 49 | 0.0e+00 | 0 | bit-identical | not binding |
| low_aspect_ratio_DEMO | A2 | `tfcoil.str_wp` | max_exit_residual_carried | M2 | M1 3 → 3, M2 5 → 5, M3 2 → 2 | 49 → 49 | 0.0e+00 | 0 | bit-identical | not binding |
| low_aspect_ratio_DEMO | A2 | `water_use.waterusetower` | max_exit_residual_not_carried | none (control) | M1 3 → 3, M2 5 → 5, M3 2 → 2 | 49 → 49 | 0.0e+00 | 0 | bit-identical | control PASS |
| st_regression | A0 | — (full census set) | — | — | FLAT 6 | 106 | 3.0e-09 | 0 | — | — |
| st_regression | A0 | `blanket.deg_blkt_inboard_poloidal_plasma` | most_sweeps_carried | FLAT | FLAT 6 → 6 | 106 → 106 | 3.0e-09 | 0 | bit-identical | not binding |
| st_regression | A0 | `pf_coil.ccls` | pf_coil_self_read | FLAT | FLAT 6 → 6 | 106 → 106 | 3.0e-09 | 0 | bit-identical | not binding |
| st_regression | A0 | `superconducting_tfcoil.a_tf_plasma_case` | max_exit_residual_not_carried | none (control) | FLAT 6 → 6 | 106 → 106 | 3.0e-09 | 0 | bit-identical | control PASS |
| st_regression | A0 | `tfcoil.str_wp` | max_exit_residual_carried | FLAT | FLAT 6 → 6 | 106 → 106 | 3.0e-09 | 0 | bit-identical | not binding |
| st_regression | A2 | — (full census set) | — | — | M1 3, M2 6, PULSE 1, M3 3 | 64 | 3.0e-09 | 0 | — | — |
| st_regression | A2 | `impurity_radiation.f_nd_impurity_electron_array` | most_sweeps_carried | M1, M2, M3, PULSE | M1 3 → 3, M2 6 → 6, M3 3 → 3, PULSE 1 → 1 | 64 → 64 | 3.0e-09 | 0 | bit-identical | not binding |
| st_regression | A2 | `pf_coil.ccls` | pf_coil_self_read | M2 | M1 3 → 3, M2 6 → 6, M3 3 → 3, PULSE 1 → 1 | 64 → 64 | 3.0e-09 | 0 | bit-identical | not binding |
| st_regression | A2 | `superconducting_tfcoil.a_tf_plasma_case` | max_exit_residual_not_carried | none (control) | M1 3 → 3, M2 6 → 6, M3 3 → 3, PULSE 1 → 1 | 64 → 64 | 3.0e-09 | 0 | bit-identical | control PASS |
| st_regression | A2 | `tfcoil.str_wp` | max_exit_residual_carried | M2 | M1 3 → 3, M2 6 → 6, M3 3 → 3, PULSE 1 → 1 | 64 → 64 | 3.0e-09 | 0 | bit-identical | not binding |

Verdicts: **not binding 17, control PASS 6, ESCAPES 2, bites 0.** The six full-set reference rows
reproduce A89 §7.4's `rbw` displaced rows in node calls and sweeps (129 / 55, 93 / 49, 106 / 64;
A89 §8 check 2), as the same job in this tree should.

### 5.2 Readings

1. **No single carried component binds on 17 of 19 drops, and the controls are clean.** Dropping
   the component carried in the most census sweeps, the first `pf_coil.*` self-read, the burn
   time (both pulsed configurations, `A0`), or the largest-residual carried component on
   `low_aspect_ratio_DEMO` and `st_regression` changes nothing: sweeps identical in every block,
   node calls identical, exit state bit-identical. A set can be a correct cut set while no single
   member binds on a given entry; the test set is over-determined on these entries in the sense
   that another carried component reaches τ last. On `low_aspect_ratio_DEMO` the whole exit
   residual is 0.0 in both arms — the loops settle to bit-identical sweeps at τ = 1e-8 there — so
   nothing can bind on that entry at all, and rule 1 chose by tie-break. **A tooth cannot be shown
   on an entry where nothing binds**; it can only be shown on the component that decided, and that
   is what rule 1 found on `large_tokamak_nof`.
2. **The two drops that bit escaped the audit at τ, and the mechanism is general.** On
   `large_tokamak_nof`, `pf_coil.stress_z_cs_self_midplane_profile` is the component that holds
   the loop open for its last sweep (A89 §8 check 1 found the same component deciding the DSM set's
   failure). With it dropped the flat loop stops at 6 sweeps instead of 7 and `M2` at 6 instead of
   7; the exit state differs from the full set's by 2.6e-09 (`A0`) and 2.7e-10 (`A2`) on V4's
   ruler; the whole-`y` audit maximum rises from 4.9e-11 to 2.6e-09 and from 5.2e-12 to 2.7e-10 —
   50× each — and stays a factor 4 and 40 **below** τ. Why it must: the audit takes one further
   sweep past termination and measures how far the state moves. After a stop one sweep early, that
   further sweep is the sweep the full loop took last, whose movement the full loop measured as
   `< τ` on the test set and which the audit now measures on the whole of `y`. With geometric
   contraction that movement is bounded by the loop's own last accepted step, so **the audit at τ
   can flag a one-sweep-early stop only where the dropped component moves more than τ in that one
   sweep** — which is the case A89 found at τ = 1e-8 for the DSM set (`costs.coecap` at 1.47e-08,
   two components decided) and not the case here. The audit is not insensitive — it moved 50× — it
   is thresholded at the wrong quantity for this purpose.
3. **The exit-state comparison is the tooth the audit is not.** Against the full set's exit the
   17 non-binding drops and the 6 controls are bit-identical and the 2 that bit are 2.6e-09 and
   2.7e-10 — a clean separation with no threshold to choose. But it is a comparison against a
   reference run, not a property of one run, so it is a *gate* (a tooth for a gate that asserts a
   test set) rather than a per-run *audit*.

## 6. Limits

### 6.1 Record stamps

Surveyed by the stamp script over every `metrics.json` under the task's records (excluding
`discarded/`); the survey is reproducible from the records with a five-line read of
`tree_git_head` / `tree_git_dirty`.

| records | n | `tree_git_head` | dirty | what changed between those commits |
|---|---|---|---|---|
| lifted-input baseline evaluations (`AR`, gate kind) | 2 | `9cfb5687` | yes (the task's scripts, untracked, not yet committed) | — (the derivation is V4's; the digest gate PASSed) |
| censused optimisations | 1 / 1 / 10 | `9f3d4148` / `5a0b419a` / `84dde2f7` | no | docstring tie-break text (`5a0b419a`), summary-only edits to the driver (`6723383f`, `84dde2f7`); the instrument, the wrapper, `narrowing.py` and the V4 copy unchanged since `9f3d4148` |
| references and teeth evaluations | 6 / 10 / 1 / 18 | `84dde2f7` / `1821dae1` / `1821dae1` dirty / `1e997a55` | one dirty | `optimisation_path_sets.json` added (`1821dae1`); the lifted-input stage's cache redirection (`1e997a55`, a stage the teeth do not run); the one dirty record is that edit in progress in the driver's own file |

Every commit after `9f3d4148` touched only the driver's summary code, its docstring, or the
generated JSON; no child, wrapper or driver-copy file changed while a run executed. The straddle is
recorded here rather than repaired: re-making 39 runs to change a stamp would be a repeat of the
press, not a verification.

### 6.2 What the census cannot see

- A read through a reference a model kept from an earlier sweep, or coupling through attributes
  on model objects, which `y` does not hold (A89 §7.6). The reproduction of every count is not
  evidence against this — an unobserved read changes nothing the census observes.
- The value-diff half of the instrument registers an in-place array write only when the value
  changes, so a per-evaluation set is a lower bound on the structural set (§4.3 reading 1). The
  union over runs of 570–9 240 evaluations is what this report compares; it is bounded below by the
  8-entry set and above by nothing the instrument can state.
- A fetch that precedes an in-place mutation counts as a read, so a component a node only
  *writes* in place is included (A89's declared conservative direction).
  `impurity_radiation.f_nd_impurity_electron_array` is the visible case: it is in every block's set
  including the once-swept tail and `PULSE`, and dropping it from all of them changes nothing
  (Table 5, `most_sweeps_carried`, `A2`, three configurations).
- Twelve runs, two starts per arm and configuration; retries observed once (`low_aspect_ratio_DEMO`
  `B0` seed 1, 2 attempts). Branches taken only on other starts are unobserved, as before.

### 6.3 What the teeth do not show

- One displaced entry per configuration and arm, at τ = 1e-8; a component not binding here may
  bind on another entry or at another tolerance. The two that bit are on `large_tokamak_nof`
  only; `low_aspect_ratio_DEMO` has no binding component on this entry at all (exit residual 0.0).
- The criterion asked the whole-`y` audit at τ to catch the drop; §5.2 shows why it cannot catch a
  one-sweep-early stop in general. That is the finding; the criterion is not revised in this task.
- The drops are single components. A dropped *pair* or a dropped block was not tested.

### 6.4 Wall clock

Every timing is context: a shared machine, A93 running concurrently, no repetitions. The
instrument's factor (2.3–4.7) is a property of the hooks, not of any arm.

## 7. Autonomous decisions, each with its reversal path

1. **Whole runs with the full instrument, all twelve.** The brief allowed reducing to what fits;
   the first run's factor projected 1.3 h for the rest, which fits. *Reversal:* none needed; the
   records are complete.
2. **The census snapshot made type-robust (`9f3d4148`).** The first trial run crashed after one
   evaluation: a `y` component that is a list default at the first `call_models` is replaced by a
   scalar on the cold start, and A89's snapshot typed each component once at install. Now every
   component is snapshotted around each node (arrays copied, scalars held, a type change counted as
   a write). Neutral for A89's records (a scalar changes only through `__setattr__`, already
   recorded); the crashed record is kept under `runs/…/discarded/`. *Reversal:* revert the commit
   and the census cannot run from a cold start; A89's `--derive-rbw` is unaffected either way.
3. **Twin sets `B0 ↔ A0`, `B2 ↔ A2`** with the two named differences (feed-forward nodes in the
   flat block; burn-time owner). The comparison names every differing component's writer module
   so the difference can be attributed; none was attributable to either (§4.2 reading 3, §4.4).
   *Reversal:* re-census A89's arms without the feed-forward deferral — one `--census` press of
   A89's stage with `overrides()` returning `{}` for `A0`; predicted to change nothing.
4. **Numba cache files under the V4 folder, by V4's own pool** (`arch_surgery/MDA_partitioning_experiment_v4/PROCESS/process/models/{,engineering,physics,tfcoil}/__pycache__/*.nbi|*.nbc`,
   122 files, stamped 16:14–16:15, the lifted-input stage). The derivation's baseline evaluation
   goes through `pool.run`, whose environment copies this process's and sets no `NUMBA_CACHE_DIR`;
   every other stage of this task launches with its own environment and cache directory. The files
   are gitignored (`git status --ignored` shows them as `!!`; no tracked file changed) and are
   numba's compiled kernels, not source. **The hard rule was breached by mechanism, not by an
   edit, and it is reported, not repaired:** nothing under the V4 folder was deleted either. Fixed
   for any later press at `1e997a55` (`NUMBA_CACHE_DIR` set before the derivation). *Reversal /
   clean-up, the orchestrator's call:* `find arch_surgery/MDA_partitioning_experiment_v4/PROCESS/process -name "__pycache__" -type d -exec rm -r {} +`
   in the worktree removes exactly those directories; the copy-identity gates read tracked files
   and are unaffected.
5. **Records of kind `smoke`** for every run this task made, as A89 did, so no V4 tally can read
   them. *Reversal:* none needed.
6. **The teeth's full-set reference runs re-made in this tree** rather than read from A89's
   relocated records, so exit states are compared within one tree and one commit; they reproduce
   A89's node calls and sweeps (§5.1). *Reversal:* none needed.
7. **The report holds the results; the only committed artifact beyond scripts is
   `optimisation_path_sets.json`**, a living artifact for V5 (the sets on the path per block, with
   provenance), like A89's `rbw_sets.json`. *Reversal:* delete it; §4's tables carry every number
   a reader needs.

## 8. Proposals (the user's to rule; nothing here edits the lists)

1. **V5 list item 6, prerequisite (2), first half — discharged with a finding:** the 8-entry
   census set covers the optimiser's path on the three configurations; the only additions are the
   cold start's `first_call` flags and two fields, inert after evaluation 0. *Proposed rule for
   V5:* the test set per block is the union over an optimisation-run census (this task's
   `optimisation_path_sets.json`: flat 79 / 78 / 75; `M1` 17, `M2` 50 / 49 / 48, `M3` 10) **or**
   the 8-entry set — the two differ only in components that can neither hold a loop open nor let
   it stop early, so the choice is a convention, and the report proposes the run census (it is the
   larger and it is measured where the loops run).
2. **Second half — the teeth — not discharged:** a whole-`y` audit at τ is not a tooth for a
   one-sweep-early stop (§5.2). *Proposed for V5:* the gate that asserts a test set drops the
   component the full-set run finds binding (rule 1, which found it) and asserts that the exit
   state differs from the full set's exit (bit comparison, as here: bit-identical for every
   non-binding drop and control, 2.6e-09 / 2.7e-10 for the binding one) and that the loop stopped
   earlier — a comparison gate, run per configuration and block, with the control beside it. The
   per-run whole-`y` audit stays as the accuracy instrument it is; it is not asked to be a tooth.
   Whether the audit's threshold should instead be a *ratio* to the full loop's last accepted
   residual is a design question for V5's plan, not settled here.
3. **Issue candidate (the orchestrator's to file):** V4's `pool.run` composes the child's
   environment from `os.environ` without a `NUMBA_CACHE_DIR`, so any caller outside the V4 folder
   that runs a job through it leaves numba's cache under the V4 copy (§7 decision 4). A
   harness-side default (`NUMBA_CACHE_DIR` under `campaign.runs_dir`, beside the `MPLCONFIGDIR` it
   already sets) would close it; a driver-copy gate is unaffected either way.
4. **DSM validation, no new entry:** nothing here bears on the DSM; V18 stands.
5. **Trap candidate:** an instrument that types a snapshot once at install is wrong on a cold
   start (decision 2) — the shape of A89's typed snapshot and of any `__setattr__`-only write
   census: the default value's type is not the run's.

## Change log (append-only)

- 2026-09-29 — task opened on `9cfb5687`. Scripts committed (`9404f632`). First trial run
  (`large_tokamak_nof` `B0` seed 0) crashed after one evaluation on the instrument's typed
  snapshot; record set aside under `runs/…/discarded/`; fixed (`9f3d4148`); trial re-run reproduced
  the campaign record on every field, factor 4.7 (context), all twelve runs decided. Teeth
  tie-break declared before the stage ran (`5a0b419a`). Summary refinements (`6723383f`,
  `84dde2f7`). Twelve censused runs finished; 12 of 12 reproduce. `optimisation_path_sets.json`
  committed (`1821dae1`). References and teeth run; numba cache files found under the V4 folder
  from the derivation stage (§7 decision 4), stage fixed (`1e997a55`), nothing deleted. Teeth
  summarised: not binding 17, control PASS 6, ESCAPES 2. Report drafted; three headline totals
  in its verdict had been summed by hand and two were wrong (11 907 and 249 for what the script
  gives as 12 200 and 313) — the totals moved into `--summarise-census` (`f7f9b136`), the file
  regenerated (identical but for the `totals` block), the report corrected before its first
  commit.
