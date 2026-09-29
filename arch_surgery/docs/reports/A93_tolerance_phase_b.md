# A93 (tolerance-phase-b) — the census test set at the derived tolerance, in whole optimisations

> **Document status** — **OPEN.** Task A93 (tolerance-phase-b), 2026-09-29, on branch
> `A93-tolerance-phase-b`, worktree `.claude/worktrees/A93-tolerance-phase-b`, base `9cfb5687`
> (= `architecture_surgery`). V5 improvement list item 6, last prerequisite. Exploratory: **not** a
> V4 result — V4's campaign, harness and report are untouched and nothing was written to the V4
> folder. Scripts: `arch_surgery/coupling_subset_trial/narrowed_optimise.py` and
> `run_tolerance_phase_b.py` (and `narrowing.py`'s `once_per_run` switch) at `4abdc165`, the
> commit every run was made at; the summariser's tables at `002a4508` (two later commits touch
> the table renderer only, no run path). Records under `arch_surgery/idf_probe/runs/tolerance_phase_b/`
> (untracked; relocated at retirement). The campaign's records were read, never written, at
> `arch_surgery/idf_probe/runs/A90_runs/campaign/optimisation/` in the main checkout.

## 1. Verdict

**On the two pulsed configurations the census test set at the derived tolerance changes nothing
the optimiser sees and 18–19 % of what an evaluation of the partitioned arm costs. On
`st_regression` it changes the optimiser's path in both arms, and the partitioned arm's for the
worse.** In numbers, over the five seeds per configuration (§3, Tables T2–T5):

- **Path — `large_tokamak_nof` and `low_aspect_ratio_DEMO`: unchanged in every run.** All 30
  runs on the pulsed configurations (three variants × two configurations × five seeds) took
  exactly the campaign's attempts, iterations per attempt and evaluations (`C` ratio 1.0000 on
  30 of 30), the retried `low_aspect_ratio_DEMO` seed 1 included (100 + 16 iterations, 9 240
  evaluations, in all three variants). **`st_regression`: changed.** The tolerance alone (`B0`
  whole-`y` at 1e-8) moves 2 of 5 seeds (+9 and −5 iterations); the census set moves 3 of 5 on
  `B0` (−12, −10, −8 iterations; evaluations ×0.77, ×0.78, ×0.59) and **5 of 5 on `B2`** (+22 to
  +30 iterations on the four that converged, evaluations ×1.70 to ×4.16; seed 1 **failed**,
  `ifail = 2` — the iteration cap of 100 — on attempts 1 and 3 with `ifail = 5` between, 262
  iterations and 15 750 evaluations against the campaign's 59 and 3 510).
- **Optimum: the same, everywhere it was reached.** Paired relative `|Δ norm_objf|` against the
  campaign's record of the same arm and seed: ≤ 5.3e-13 on the pulsed configurations (bit-identical
  on 9 of 30), ≤ 2.2e-11 on `st_regression`'s accepted runs except seed 1's `B0` pair at 6.3e-9 —
  all under V4's same-optimum floor of 1e-6 by more than two decades. The one failed run ended
  1.3e-3 away and is not an optimum.
- **Cost per evaluation (ρ, solve-phase node calls per evaluation, pooled).** Against the
  campaign's arm at whole-`y` 1e-6: `B0` census 1e-8 **+4.6 % / +2.1 % / −8.0 %**
  (nof / lad / st); `B0` whole-`y` 1e-8 **+20.1 % / +18.5 % / +17.9 %**; `B2` census 1e-8
  **−18.1 % / −18.8 % / −16.1 %**. So the tolerance alone costs the flat control a fifth more;
  the census set gives almost all of it back on the flat arm and takes a further fifth off the
  partitioned arm. The decomposition `R = ρ × ε` for `B2 / B0`: the census pair at 1e-8 has
  **ρ = 0.482 / 0.489 / 0.508** where the campaign's whole-`y` pair at 1e-6 has
  **0.615 / 0.614 / 0.545**, with ε identical on the pulsed configurations (1.019 / 0.540) — and
  **ε = 2.45 on `st_regression`** (4 seeds; the campaign's 0.98), so there R rises from 0.53 to
  1.24 while ρ falls.
- **Exit audit: holds in all 45 runs.** Whole-`y` residual at the entry to the output path,
  recounted at 1e-8: 0 components at or above it on every `B0` run and on every `B2` run's
  restricted statistic (the per-run deferred nodes' writes excluded, as in V4). The 1e-8 flat
  loops exit at the exact fixed point (maximum 0.0) on 26 of 30 runs and at 4.9e-14 on the other
  four (all st `B0` census); the campaign's `B0` on nof left `heat_transport.tlvpmw` at 1.2e-11. **No carried variable
  missing from the census set was found on the optimiser's path**: the only restricted component
  the `B2` census loops leave above 1e-12 is `heat_transport.tlvpmw` on `st_regression`
  (2.4e-10 on four seeds), a feed-forward output of `M3` written by `Power` and read by `Costs`
  alone — a per-run deferred node in `B2` — so nothing in any loop reads it (T7). Constraint 93's
  normalised residual on the pulsed `B2` runs equals the campaign's on every seed.

**What this means for V5 item 6.** The ruled control (census set, τ = 1e-8) is safe on the pulsed
configurations at optimisation scale: the same path, the same optimum, exact fixed points at
exit, and a per-evaluation cost within 5 % of V4's control. The partitioned arm's per-evaluation
ratio at matched (exact) accuracy is **0.48–0.51, not 0.61–0.62**: V4's whole-`y` test at 1e-6
was charging the partitioned arm for sweeps its blocks did not need. On `st_regression` the
trajectory term is **not** neutral under the new rule — in either direction on the flat arm and
against the partitioned arm on every seed, with one failure in five — and V4's whole-`y` 1e-6
test was, by its lag, the more stable control there. Why is not settled by these runs (§5):
the tolerance alone already moves st's path, A89's noise ladder shows st's objective gradient
1.2e-8 relative under the census set at 1e-8 where the whole-`y` test reads 0, and the
partitioned census arm's exit is 2.4e-10 off a fixed point in one feed-forward quantity.
Proposals in §7.

**Time.** The first run of the matrix took 111 s (numba's compilation) and the next four 20–26 s,
which projected about 20 minutes for 45 runs; the campaign's own `wall_s` for the same seeds
(T6, `B0_campaign` + `B2_campaign`: 2 145 s) projected about an hour, which is what it took
(3 315 s over the 45 runs, plus 45 s for the lift). Nothing was dropped.

## 2. Question

The user's earlier question — *"does the change in MDA convergence or new tolerance change the
phase B optimisation iterations?"* — and V5 improvement list item 6's last prerequisite. V4's
optimisation arms stop every coupling-state loop on the whole measured state `y` (840 / 846 / 827
components) at τ = 1e-6. Ruling D32 (the user, 2026-09-29) makes V5 converge on the
**census-measured read-before-write set** — the components a sweep of the arm's own execution
order reads before it writes them (75 / 74 / 73 in the flat loop; 16 / 47 / 10 in the partitioned
arm's `M1` / `M2` / `M3`, plus 1 in st's `PULSE` block) — at the tolerance A89
(coupling-subset-trial) derived from the optimiser's own finite-difference step, **τ = 1e-8**
(`tolerance.json`, `chosen_tau`). A89 measured the effect on single evaluations. This task measures
it on **whole optimisations**: does the optimiser take the same path (iterations, evaluations),
reach the same optimum (`norm_objf`), what does each evaluation cost (node calls, sweeps), and does
the exit audit hold.

## 3. Method

**Runs.** Each run is V4's own optimisation child (`harness/child/optimise.py`) executed
unchanged in a fresh subprocess with its own working directory, by
`arch_surgery/coupling_subset_trial/narrowed_optimise.py`, which — the way A89's
`narrowed_evaluate.py` wraps the evaluation child — installs `narrowing.install` before the child
runs. The one substitution is the loops' test set (`module_solve.load_subsets` wrapped): `full`
is V4's whole-`y` test; `rbw` replaces each iterated block's test set with the census set of
`rbw_sets.json`, the flat block reading `A0`'s `FLAT` set and the partitioned arm's blocks `A2`'s
`M1` / `M2` / `M3` (the optimisation arm shares its census arm's loop shape and execution order;
`CENSUS_ARM_FOR` in the wrapper). The tolerance is not set by the wrapper: V4's pool composes the
arm's environment from a campaign whose `tau` is the derived value, so `PROCESS_ARCH_TAU=1e-08`
reaches the driver the way the campaign's `1e-06` did, and every record's `resolved_switches`
says `module_solve.TAU = 1e-08`. The per-run deferred nodes are **not** run after each evaluation
(`once_per_run=False`, the switch this task added to `narrowing.install`): an optimisation runs
them once at the output path already (`caller.write_output_files`), in every campaign arm alike.
Not narrowed: the seed's displacement of the design vector (the V4 child's own hook, so a run
pairs with the campaign's record of the same seed), the optimiser, the exit audit (every component
of `y`, at the entry to the output path) and the output path. Every child asserted
`process.__file__` under this worktree's V4 copy (`tree` in T1; trap T6), and every record
stamps a clean tree — 44 at `4abdc165`, one (nof `B2` census seed 0, re-made, §5 item 5) at
`fd1bbdaf`, which differs from it in the table renderer only.

**The lifted input file** `B2` reads on a pulsed configuration was derived in this task's runs
directory by V4's own stage (`input_files.stage_derive`: one `AR` evaluation measures the settled
burn time, the three-line edit is applied, and the bytes are gated on the committed digest). Both
pulsed configurations passed the digest gate: `8902a6a5…` (nof), `189c5e1e…` (lad) — the
campaign's bytes. `st_regression` is steady state and has none.

**Matrix.** Three variants per configuration and seed — `B0` census at 1e-8 (V5's control as
ruled), `B2` census at 1e-8 (V5's intervention), `B0` whole-`y` at 1e-8 (to separate the
tolerance's effect from the set's) — and the campaign's own `B0` and `B2` records at whole-`y`
1e-6 as the fourth and fifth members of each quintet, not re-run. Seeds: the first five, in
ascending order, of the campaign's every-arm-converged set for the configuration (V4's one
optimisation-phase seed set, `stats.every_arm_converged`: status `ok` and MFILE `ifail == 1` in
every arm), so every member has a converged campaign partner — **0–4 on `large_tokamak_nof` and
`st_regression`; 0, 1, 5, 6, 9 on `low_aspect_ratio_DEMO`**, whose seeds 2, 3, 4 are outside the
set (2 finished with `ifail = 5` after four attempts, 3 and 4 crashed, in every arm). 45
optimisations, one PROCESS process at a time (`workers = 1`; another task ran on the machine).
Run kind `smoke`: these records are outside every V4 tally.

**Comparison** (`run_tolerance_phase_b.py --summarise`, no PROCESS run). Every campaign record is
read through V4's `records.read`, which translates the arm names of its day (its `B3` directory is
today's `B2`; trap T16). Per configuration and seed, each new run against the campaign's record
of the same arm and seed:
- **pairing**: the displaced design vector, factor and clamped scaled value per iteration
  variable, hex for hex (`perturbation.json` on both sides; seed 0 is the input file's own point
  in both and has nothing to compare);
- **path**: status, `ifail`, attempts, optimiser iterations per attempt and summed over attempts
  (V4's construction), evaluations of the model set `C` (`sweeps_per_eval.n_evaluations`, the
  field V5 item 1 names as ε's correct source);
- **optimum**: `norm_objf`, as the paired relative difference `|Δf| / max(|a|, |b|)` against V4's
  same-optimum floor of 1e-6 relative;
- **cost**: solve-phase node calls `N`, `N / C`, sweeps per evaluation (histogram, min / median /
  mean / max), sweeps per solve by block, predicate evaluations and components compared;
- **exit audit**: the whole-`y` residual at the entry to the output path (frozen ruler), recounted
  from each record's `audit_residual.json` at **both** 1e-8 and 1e-6 so the two populations read
  on one ruler; for `B2` also V4's restricted statistic (the per-run deferred nodes' own writes
  excluded — those nodes have not run at the audit position), and constraint 93's normalised
  residual; and (T7) every restricted component at or above 1e-12, by name, with its membership
  of the census set, the DSM sets, its writing block and its DSM readers;
- **decomposition**: `R = ρ × ε` for `B2 / B0`, pooled over the seeds where both members are
  accepted optima (sums, so the identity is exact) and as per-seed medians with the bracket, for
  the census pair at 1e-8 and the campaign's pair at 1e-6; and the same for each new variant
  against its campaign partner.

Wall clock is reported once (T6), as context: one run each, another task on the machine, and
the first run of the matrix carrying numba's compilation.

## 4. Results

Every table below is printed by `arch_surgery/coupling_subset_trial/run_tolerance_phase_b.py
--summarise` at `002a4508` over the 45 records made at `4abdc165` / `fd1bbdaf` and the
campaign's 30 records (`tree_git_head 57dc0c14`). Members: `B0_campaign` = `B0` whole-`y` 1e-6
(campaign); `B0_full` = `B0` whole-`y` 1e-8; `B0_rbw` = `B0` census 1e-8; `B2_campaign` = `B2`
whole-`y` 1e-6 (campaign); `B2_rbw` = `B2` census 1e-8.

### 4.1 Seeds and test sets

**T0.** *Per configuration: the seeds run (the first five of the campaign's every-arm-converged
set, whose size is the third column) and the census test-set widths — components of `y` tested
by the flat loop (`B0`) and by each block loop (`B2`), from `rbw_sets.json`.*

| configuration | seeds run | n every-arm-converged (campaign) | census FLAT width (B0) | census widths per block (B2) |
|---|---|---|---|---|
| large_tokamak_nof | 0, 1, 2, 3, 4 | 22 | 75 | M1 16, M2 47, M3 10 |
| low_aspect_ratio_DEMO | 0, 1, 5, 6, 9 | 11 | 74 | M1 16, M2 46, M3 10 |
| st_regression | 0, 1, 2, 3, 4 | 22 | 73 | M1 16, M2 47, M3 10, PULSE 1 |

### 4.2 Pairing and outcome

**T1.** *One row per new run (45). `displaced x identical (hex)`: iteration variables whose
displacement factor and clamped scaled start equal the campaign record's bit for bit, over the
variables of the arm's design vector (20 / 21 on nof, 19 / 20 on lad, 14 on st; the lifted arm
has one more); seed 0 is undisplaced in both. `tree`: the commit the run's tree stamped, clean in
every case. Wall clock is context.*

| configuration | seed | run | status | ifail | attempts | displaced x identical (hex) | paired | tree | wall s (context) |
|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | 0 | B0_full | ok | 1 | 1 | n/a (seed 0) | yes | 4abdc165 | 31 |
| large_tokamak_nof | 0 | B0_rbw | ok | 1 | 1 | n/a (seed 0) | yes | 4abdc165 | 25 |
| large_tokamak_nof | 0 | B2_rbw | ok | 1 | 1 | n/a (seed 0) | yes | fd1bbdaf | 21 |
| large_tokamak_nof | 1 | B0_full | ok | 1 | 1 | 20/20 | yes | 4abdc165 | 33 |
| large_tokamak_nof | 1 | B0_rbw | ok | 1 | 1 | 20/20 | yes | 4abdc165 | 21 |
| large_tokamak_nof | 1 | B2_rbw | ok | 1 | 1 | 21/21 | yes | 4abdc165 | 22 |
| large_tokamak_nof | 2 | B0_full | ok | 1 | 1 | 20/20 | yes | 4abdc165 | 43 |
| large_tokamak_nof | 2 | B0_rbw | ok | 1 | 1 | 20/20 | yes | 4abdc165 | 23 |
| large_tokamak_nof | 2 | B2_rbw | ok | 1 | 1 | 21/21 | yes | 4abdc165 | 20 |
| large_tokamak_nof | 3 | B0_full | ok | 1 | 1 | 20/20 | yes | 4abdc165 | 32 |
| large_tokamak_nof | 3 | B0_rbw | ok | 1 | 1 | 20/20 | yes | 4abdc165 | 18 |
| large_tokamak_nof | 3 | B2_rbw | ok | 1 | 1 | 21/21 | yes | 4abdc165 | 16 |
| large_tokamak_nof | 4 | B0_full | ok | 1 | 1 | 20/20 | yes | 4abdc165 | 30 |
| large_tokamak_nof | 4 | B0_rbw | ok | 1 | 1 | 20/20 | yes | 4abdc165 | 17 |
| large_tokamak_nof | 4 | B2_rbw | ok | 1 | 1 | 21/21 | yes | 4abdc165 | 17 |
| low_aspect_ratio_DEMO | 0 | B0_full | ok | 1 | 1 | n/a (seed 0) | yes | 4abdc165 | 58 |
| low_aspect_ratio_DEMO | 0 | B0_rbw | ok | 1 | 1 | n/a (seed 0) | yes | 4abdc165 | 37 |
| low_aspect_ratio_DEMO | 0 | B2_rbw | ok | 1 | 1 | n/a (seed 0) | yes | 4abdc165 | 33 |
| low_aspect_ratio_DEMO | 1 | B0_full | ok | 1 | 2 | 19/19 | yes | 4abdc165 | 470 |
| low_aspect_ratio_DEMO | 1 | B0_rbw | ok | 1 | 2 | 19/19 | yes | 4abdc165 | 256 |
| low_aspect_ratio_DEMO | 1 | B2_rbw | ok | 1 | 1 | 20/20 | yes | 4abdc165 | 37 |
| low_aspect_ratio_DEMO | 5 | B0_full | ok | 1 | 1 | 19/19 | yes | 4abdc165 | 40 |
| low_aspect_ratio_DEMO | 5 | B0_rbw | ok | 1 | 1 | 19/19 | yes | 4abdc165 | 25 |
| low_aspect_ratio_DEMO | 5 | B2_rbw | ok | 1 | 1 | 20/20 | yes | 4abdc165 | 89 |
| low_aspect_ratio_DEMO | 6 | B0_full | ok | 1 | 1 | 19/19 | yes | 4abdc165 | 127 |
| low_aspect_ratio_DEMO | 6 | B0_rbw | ok | 1 | 1 | 19/19 | yes | 4abdc165 | 77 |
| low_aspect_ratio_DEMO | 6 | B2_rbw | ok | 1 | 1 | 20/20 | yes | 4abdc165 | 51 |
| low_aspect_ratio_DEMO | 9 | B0_full | ok | 1 | 1 | 19/19 | yes | 4abdc165 | 48 |
| low_aspect_ratio_DEMO | 9 | B0_rbw | ok | 1 | 1 | 19/19 | yes | 4abdc165 | 28 |
| low_aspect_ratio_DEMO | 9 | B2_rbw | ok | 1 | 1 | 20/20 | yes | 4abdc165 | 35 |
| st_regression | 0 | B0_full | ok | 1 | 1 | n/a (seed 0) | yes | 4abdc165 | 31 |
| st_regression | 0 | B0_rbw | ok | 1 | 1 | n/a (seed 0) | yes | 4abdc165 | 17 |
| st_regression | 0 | B2_rbw | ok | 1 | 1 | n/a (seed 0) | yes | 4abdc165 | 71 |
| st_regression | 1 | B0_full | ok | 1 | 1 | 14/14 | yes | 4abdc165 | 198 |
| st_regression | 1 | B0_rbw | ok | 1 | 1 | 14/14 | yes | 4abdc165 | 59 |
| st_regression | 1 | B2_rbw | ok | 2 | 3 | 14/14 | yes | 4abdc165 | 476 |
| st_regression | 2 | B0_full | ok | 1 | 1 | 14/14 | yes | 4abdc165 | 148 |
| st_regression | 2 | B0_rbw | ok | 1 | 1 | 14/14 | yes | 4abdc165 | 59 |
| st_regression | 2 | B2_rbw | ok | 1 | 1 | 14/14 | yes | 4abdc165 | 128 |
| st_regression | 3 | B0_full | ok | 1 | 1 | 14/14 | yes | 4abdc165 | 75 |
| st_regression | 3 | B0_rbw | ok | 1 | 1 | 14/14 | yes | 4abdc165 | 28 |
| st_regression | 3 | B2_rbw | ok | 1 | 1 | 14/14 | yes | 4abdc165 | 75 |
| st_regression | 4 | B0_full | ok | 1 | 1 | 14/14 | yes | 4abdc165 | 76 |
| st_regression | 4 | B0_rbw | ok | 1 | 1 | 14/14 | yes | 4abdc165 | 18 |
| st_regression | 4 | B2_rbw | ok | 1 | 1 | 14/14 | yes | 4abdc165 | 78 |

### 4.3 The optimiser's path and its optimum

**T2.** *Five rows per configuration and seed, one per member. `iterations Σ` is summed over
attempts (V4's construction); `C` is evaluations of the model set; `N` solve-phase node calls;
`|Δf|/max` the paired relative difference of `norm_objf` against the campaign's record of the
same arm and seed (floor 1e-6); `C ratio` and `N ratio` likewise paired. A campaign row carries
no paired columns.*

| configuration | seed | run | ifail | attempts | iterations per attempt | iterations Σ | evaluations C | node calls N | N/C | sweeps/eval mean | norm_objf | |Δf|/max rel. to campaign | Δ iterations Σ | C ratio | N ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | 0 | B0_campaign | 1 | 1 | 8 | 8 | 630 | 43449 | 69.0 | 3.28 | 1.60000000003 | — | — | — | — |
| large_tokamak_nof | 0 | B0_full | 1 | 1 | 8 | 8 | 630 | 52416 | 83.2 | 3.96 | 1.60000000003 | 5.6e-15 | 0 | 1.0000 | 1.2064 |
| large_tokamak_nof | 0 | B0_rbw | 1 | 1 | 8 | 8 | 630 | 45465 | 72.2 | 3.44 | 1.60000000003 | 2.8e-16 | 0 | 1.0000 | 1.0464 |
| large_tokamak_nof | 0 | B2_campaign | 1 | 1 | 8 | 8 | 660 | 28055 | 42.5 | 8.33 | 1.60000000016 | — | — | — | — |
| large_tokamak_nof | 0 | B2_rbw | 1 | 1 | 8 | 8 | 660 | 22944 | 34.8 | 7.50 | 1.60000000016 | 0.0e+00 | 0 | 1.0000 | 0.8178 |
| large_tokamak_nof | 1 | B0_campaign | 1 | 1 | 8 | 8 | 630 | 43491 | 69.0 | 3.29 | 1.60000000004 | — | — | — | — |
| large_tokamak_nof | 1 | B0_full | 1 | 1 | 8 | 8 | 630 | 52437 | 83.2 | 3.96 | 1.60000000004 | 0.0e+00 | 0 | 1.0000 | 1.2057 |
| large_tokamak_nof | 1 | B0_rbw | 1 | 1 | 8 | 8 | 630 | 45528 | 72.3 | 3.44 | 1.60000000004 | 0.0e+00 | 0 | 1.0000 | 1.0468 |
| large_tokamak_nof | 1 | B2_campaign | 1 | 1 | 8 | 8 | 660 | 28037 | 42.5 | 8.33 | 1.60000000003 | — | — | — | — |
| large_tokamak_nof | 1 | B2_rbw | 1 | 1 | 8 | 8 | 660 | 22941 | 34.8 | 7.50 | 1.60000000003 | 0.0e+00 | 0 | 1.0000 | 0.8182 |
| large_tokamak_nof | 2 | B0_campaign | 1 | 1 | 9 | 9 | 714 | 49623 | 69.5 | 3.31 | 1.60000000005 | — | — | — | — |
| large_tokamak_nof | 2 | B0_full | 1 | 1 | 9 | 9 | 714 | 58863 | 82.4 | 3.93 | 1.60000000005 | 0.0e+00 | 0 | 1.0000 | 1.1862 |
| large_tokamak_nof | 2 | B0_rbw | 1 | 1 | 9 | 9 | 714 | 51639 | 72.3 | 3.44 | 1.60000000005 | 0.0e+00 | 0 | 1.0000 | 1.0406 |
| large_tokamak_nof | 2 | B2_campaign | 1 | 1 | 8 | 8 | 660 | 28055 | 42.5 | 8.33 | 1.60000000008 | — | — | — | — |
| large_tokamak_nof | 2 | B2_rbw | 1 | 1 | 8 | 8 | 660 | 22935 | 34.8 | 7.49 | 1.60000000008 | 2.8e-16 | 0 | 1.0000 | 0.8175 |
| large_tokamak_nof | 3 | B0_campaign | 1 | 1 | 7 | 7 | 546 | 37695 | 69.0 | 3.29 | 1.60000000002 | — | — | — | — |
| large_tokamak_nof | 3 | B0_full | 1 | 1 | 7 | 7 | 546 | 45486 | 83.3 | 3.97 | 1.60000000002 | 0.0e+00 | 0 | 1.0000 | 1.2067 |
| large_tokamak_nof | 3 | B0_rbw | 1 | 1 | 7 | 7 | 546 | 39459 | 72.3 | 3.44 | 1.60000000002 | 1.4e-16 | 0 | 1.0000 | 1.0468 |
| large_tokamak_nof | 3 | B2_campaign | 1 | 1 | 7 | 7 | 572 | 24319 | 42.5 | 8.33 | 1.60000000006 | — | — | — | — |
| large_tokamak_nof | 3 | B2_rbw | 1 | 1 | 7 | 7 | 572 | 19938 | 34.9 | 7.51 | 1.60000000006 | 0.0e+00 | 0 | 1.0000 | 0.8199 |
| large_tokamak_nof | 4 | B0_campaign | 1 | 1 | 7 | 7 | 546 | 37590 | 68.8 | 3.28 | 1.60000000009 | — | — | — | — |
| large_tokamak_nof | 4 | B0_full | 1 | 1 | 7 | 7 | 546 | 45234 | 82.8 | 3.95 | 1.60000000009 | 5.3e-13 | 0 | 1.0000 | 1.2034 |
| large_tokamak_nof | 4 | B0_rbw | 1 | 1 | 7 | 7 | 546 | 39438 | 72.2 | 3.44 | 1.60000000009 | 2.9e-15 | 0 | 1.0000 | 1.0492 |
| large_tokamak_nof | 4 | B2_campaign | 1 | 1 | 7 | 7 | 572 | 24307 | 42.5 | 8.33 | 1.60000000003 | — | — | — | — |
| large_tokamak_nof | 4 | B2_rbw | 1 | 1 | 7 | 7 | 572 | 19938 | 34.9 | 7.51 | 1.60000000003 | 0.0e+00 | 0 | 1.0000 | 0.8203 |
| low_aspect_ratio_DEMO | 0 | B0_campaign | 1 | 1 | 16 | 16 | 1240 | 86877 | 70.1 | 3.34 | -0.406296230228 | — | — | — | — |
| low_aspect_ratio_DEMO | 0 | B0_full | 1 | 1 | 16 | 16 | 1240 | 103362 | 83.4 | 3.97 | -0.406296230228 | 3.1e-15 | 0 | 1.0000 | 1.1898 |
| low_aspect_ratio_DEMO | 0 | B0_rbw | 1 | 1 | 16 | 16 | 1240 | 89229 | 72.0 | 3.43 | -0.406296230228 | 1.1e-14 | 0 | 1.0000 | 1.0271 |
| low_aspect_ratio_DEMO | 0 | B2_campaign | 1 | 1 | 13 | 13 | 1050 | 45496 | 43.3 | 8.34 | -0.406295951953 | — | — | — | — |
| low_aspect_ratio_DEMO | 0 | B2_rbw | 1 | 1 | 13 | 13 | 1050 | 36984 | 35.2 | 7.44 | -0.406295951953 | 3.7e-15 | 0 | 1.0000 | 0.8129 |
| low_aspect_ratio_DEMO | 1 | B0_campaign | 1 | 2 | 100/16 | 116 | 9240 | 655473 | 70.9 | 3.38 | -0.405823482872 | — | — | — | — |
| low_aspect_ratio_DEMO | 1 | B0_full | 1 | 2 | 100/16 | 116 | 9240 | 774585 | 83.8 | 3.99 | -0.405823482872 | 3.7e-14 | 0 | 1.0000 | 1.1817 |
| low_aspect_ratio_DEMO | 1 | B0_rbw | 1 | 2 | 100/16 | 116 | 9240 | 666057 | 72.1 | 3.43 | -0.405823482872 | 3.3e-14 | 0 | 1.0000 | 1.0161 |
| low_aspect_ratio_DEMO | 1 | B2_campaign | 1 | 1 | 15 | 15 | 1218 | 52834 | 43.4 | 8.36 | -0.405951259711 | — | — | — | — |
| low_aspect_ratio_DEMO | 1 | B2_rbw | 1 | 1 | 15 | 15 | 1218 | 42929 | 35.2 | 7.45 | -0.405951259711 | 7.7e-15 | 0 | 1.0000 | 0.8125 |
| low_aspect_ratio_DEMO | 5 | B0_campaign | 1 | 1 | 11 | 11 | 840 | 58947 | 70.2 | 3.34 | -0.405947838712 | — | — | — | — |
| low_aspect_ratio_DEMO | 5 | B0_full | 1 | 1 | 11 | 11 | 840 | 70035 | 83.4 | 3.97 | -0.405947838712 | 4.1e-15 | 0 | 1.0000 | 1.1881 |
| low_aspect_ratio_DEMO | 5 | B0_rbw | 1 | 1 | 11 | 11 | 840 | 60480 | 72.0 | 3.43 | -0.405947838712 | 1.7e-14 | 0 | 1.0000 | 1.0260 |
| low_aspect_ratio_DEMO | 5 | B2_campaign | 1 | 1 | 36 | 36 | 2982 | 129215 | 43.3 | 8.34 | -0.405947838738 | — | — | — | — |
| low_aspect_ratio_DEMO | 5 | B2_rbw | 1 | 1 | 36 | 36 | 2982 | 104952 | 35.2 | 7.43 | -0.405947838738 | 2.3e-15 | 0 | 1.0000 | 0.8122 |
| low_aspect_ratio_DEMO | 6 | B0_campaign | 1 | 1 | 34 | 34 | 2680 | 187572 | 70.0 | 3.33 | -0.406291272886 | — | — | — | — |
| low_aspect_ratio_DEMO | 6 | B0_full | 1 | 1 | 34 | 34 | 2680 | 223230 | 83.3 | 3.97 | -0.406291272886 | 6.8e-16 | 0 | 1.0000 | 1.1901 |
| low_aspect_ratio_DEMO | 6 | B0_rbw | 1 | 1 | 34 | 34 | 2680 | 193074 | 72.0 | 3.43 | -0.406291272886 | 2.2e-14 | 0 | 1.0000 | 1.0293 |
| low_aspect_ratio_DEMO | 6 | B2_campaign | 1 | 1 | 21 | 21 | 1722 | 74687 | 43.4 | 8.35 | -0.406291106271 | — | — | — | — |
| low_aspect_ratio_DEMO | 6 | B2_rbw | 1 | 1 | 21 | 21 | 1722 | 60632 | 35.2 | 7.44 | -0.406291106271 | 5.7e-15 | 0 | 1.0000 | 0.8118 |
| low_aspect_ratio_DEMO | 9 | B0_campaign | 1 | 1 | 13 | 13 | 1000 | 70077 | 70.1 | 3.34 | -0.406075195937 | — | — | — | — |
| low_aspect_ratio_DEMO | 9 | B0_full | 1 | 1 | 13 | 13 | 1000 | 83328 | 83.3 | 3.97 | -0.406075195937 | 8.9e-15 | 0 | 1.0000 | 1.1891 |
| low_aspect_ratio_DEMO | 9 | B0_rbw | 1 | 1 | 13 | 13 | 1000 | 72240 | 72.2 | 3.44 | -0.406075195937 | 2.0e-14 | 0 | 1.0000 | 1.0309 |
| low_aspect_ratio_DEMO | 9 | B2_campaign | 1 | 1 | 14 | 14 | 1134 | 49194 | 43.4 | 8.36 | -0.406075196882 | — | — | — | — |
| low_aspect_ratio_DEMO | 9 | B2_rbw | 1 | 1 | 14 | 14 | 1134 | 39967 | 35.2 | 7.45 | -0.406075196882 | 1.8e-14 | 0 | 1.0000 | 0.8124 |
| st_regression | 0 | B0_campaign | 1 | 1 | 10 | 10 | 570 | 42756 | 75.0 | 3.57 | -16.5885765078 | — | — | — | — |
| st_regression | 0 | B0_full | 1 | 1 | 10 | 10 | 570 | 51366 | 90.1 | 4.29 | -16.5885765078 | 1.4e-14 | 0 | 1.0000 | 1.2014 |
| st_regression | 0 | B0_rbw | 1 | 1 | 10 | 10 | 570 | 38514 | 67.6 | 3.22 | -16.5885765078 | 4.8e-13 | 0 | 1.0000 | 0.9008 |
| st_regression | 0 | B2_campaign | 1 | 1 | 10 | 10 | 570 | 23505 | 41.2 | 9.23 | -16.5885765078 | — | — | — | — |
| st_regression | 0 | B2_rbw | 1 | 1 | 40 | 40 | 2370 | 80974 | 34.2 | 8.30 | -16.588576508 | 1.5e-11 | 30 | 4.1579 | 3.4450 |
| st_regression | 1 | B0_campaign | 1 | 1 | 53 | 53 | 3150 | 226002 | 71.7 | 3.42 | -16.8089052843 | — | — | — | — |
| st_regression | 1 | B0_full | 1 | 1 | 62 | 62 | 3690 | 316512 | 85.8 | 4.08 | -16.8089053908 | 6.3e-09 | 9 | 1.1714 | 1.4005 |
| st_regression | 1 | B0_rbw | 1 | 1 | 41 | 41 | 2430 | 162582 | 66.9 | 3.19 | -16.8089053892 | 6.2e-09 | -12 | 0.7714 | 0.7194 |
| st_regression | 1 | B2_campaign | 1 | 1 | 59 | 59 | 3510 | 134560 | 38.3 | 8.85 | -16.8089053904 | — | — | — | — |
| st_regression | 1 | B2_rbw | 2 | 3 | 100/62/100 | 262 | 15750 | 531034 | 33.7 | 8.23 | -16.8308736126 | 1.3e-03 | 203 | 4.4872 | 3.9464 |
| st_regression | 2 | B0_campaign | 1 | 2 | 27/21 | 48 | 2880 | 218820 | 76.0 | 3.62 | -16.5885765079 | — | — | — | — |
| st_regression | 2 | B0_full | 1 | 1 | 43 | 43 | 2550 | 218610 | 85.7 | 4.08 | -16.5885765082 | 1.8e-11 | -5 | 0.8854 | 0.9990 |
| st_regression | 2 | B0_rbw | 1 | 1 | 38 | 38 | 2250 | 151746 | 67.4 | 3.21 | -16.5885765082 | 2.0e-11 | -10 | 0.7812 | 0.6935 |
| st_regression | 2 | B2_campaign | 1 | 1 | 39 | 39 | 2310 | 93767 | 40.6 | 9.16 | -16.5885765081 | — | — | — | — |
| st_regression | 2 | B2_rbw | 1 | 1 | 66 | 66 | 3930 | 135183 | 34.4 | 8.35 | -16.5885765081 | 4.1e-12 | 27 | 1.7013 | 1.4417 |
| st_regression | 3 | B0_campaign | 1 | 1 | 18 | 18 | 1050 | 76461 | 72.8 | 3.47 | -16.5885765079 | — | — | — | — |
| st_regression | 3 | B0_full | 1 | 1 | 18 | 18 | 1050 | 91812 | 87.4 | 4.16 | -16.5885765079 | 3.6e-14 | 0 | 1.0000 | 1.2008 |
| st_regression | 3 | B0_rbw | 1 | 1 | 18 | 18 | 1050 | 70917 | 67.5 | 3.22 | -16.5885765078 | 3.9e-12 | 0 | 1.0000 | 0.9275 |
| st_regression | 3 | B2_campaign | 1 | 1 | 18 | 18 | 1050 | 43204 | 41.1 | 9.23 | -16.5885765079 | — | — | — | — |
| st_regression | 3 | B2_rbw | 1 | 1 | 40 | 40 | 2370 | 81434 | 34.4 | 8.35 | -16.5885765082 | 2.2e-11 | 22 | 2.2571 | 1.8849 |
| st_regression | 4 | B0_campaign | 1 | 1 | 20 | 20 | 1170 | 80661 | 68.9 | 3.28 | -16.588576508 | — | — | — | — |
| st_regression | 4 | B0_full | 1 | 1 | 20 | 20 | 1170 | 99687 | 85.2 | 4.06 | -16.588576508 | 2.7e-13 | 0 | 1.0000 | 1.2359 |
| st_regression | 4 | B0_rbw | 1 | 1 | 12 | 12 | 690 | 46410 | 67.3 | 3.20 | -16.5885765081 | 7.7e-12 | -8 | 0.5897 | 0.5754 |
| st_regression | 4 | B2_campaign | 1 | 1 | 20 | 20 | 1170 | 47985 | 41.0 | 9.16 | -16.588576508 | — | — | — | — |
| st_regression | 4 | B2_rbw | 1 | 1 | 42 | 42 | 2490 | 85081 | 34.2 | 8.30 | -16.5885765082 | 1.4e-11 | 22 | 2.1282 | 1.7731 |

### 4.4 Sweeps per evaluation and per block

**T3.** *Same rows. Sweeps of the loop per evaluation of the model set (histogram: sweeps →
count of evaluations); sweeps per solve of each iterated block (`B2`) or of the flat block;
predicate evaluations and components compared during the solve phase, and their ratio, the mean
test width.*

| configuration | seed | run | evaluations | sweeps/eval min/median/mean/max | histogram sweeps:count | sweeps per solve by block | predicate evaluations | components compared | mean test width |
|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | 0 | B0_campaign | 630 | 1/3/3.28/6 | 1:7 2:120 3:271 4:153 5:77 6:2 | FLAT 3.28 | 2069 | 1737960 | 840 |
| large_tokamak_nof | 0 | B0_full | 630 | 1/4/3.96/8 | 1:7 2:75 3:90 4:229 5:224 6:3 7:1 8:1 | FLAT 3.96 | 2496 | 2096640 | 840 |
| large_tokamak_nof | 0 | B0_rbw | 630 | 1/3/3.44/7 | 1:22 2:105 3:270 4:46 5:185 7:2 | FLAT 3.44 | 2165 | 162375 | 75 |
| large_tokamak_nof | 0 | B2_campaign | 660 | 4/9/8.33/14 | 4:7 5:15 6:135 7:105 8:60 9:136 10:105 11:75 12:16 13:4 14:2 | M1 2.17, M2 2.75, M3 2.41 | 4839 | 1156926 | 239 |
| large_tokamak_nof | 0 | B2_rbw | 660 | 4/7/7.50/13 | 4:22 5:90 6:180 7:45 8:15 9:225 10:46 11:35 13:2 | M1 1.80, M2 2.92, M3 1.78 | 4289 | 121262 | 28 |
| large_tokamak_nof | 1 | B0_campaign | 630 | 1/3/3.29/7 | 1:7 2:120 3:271 4:152 5:78 6:1 7:1 | FLAT 3.29 | 2071 | 1739640 | 840 |
| large_tokamak_nof | 1 | B0_full | 630 | 1/4/3.96/8 | 1:7 2:75 3:91 4:228 5:222 6:5 7:1 8:1 | FLAT 3.96 | 2497 | 2097480 | 840 |
| large_tokamak_nof | 1 | B0_rbw | 630 | 1/3/3.44/7 | 1:22 2:105 3:270 4:46 5:182 6:3 7:2 | FLAT 3.44 | 2168 | 162600 | 75 |
| large_tokamak_nof | 1 | B2_campaign | 660 | 4/9/8.33/14 | 4:7 5:15 6:135 7:105 8:60 9:135 10:107 11:75 12:16 13:4 14:1 | M1 2.17, M2 2.75, M3 2.41 | 4836 | 1156225 | 239 |
| large_tokamak_nof | 1 | B2_rbw | 660 | 4/7/7.50/13 | 4:22 5:90 6:180 7:45 8:15 9:226 10:45 11:34 12:2 13:1 | M1 1.80, M2 2.92, M3 1.78 | 4288 | 121215 | 28 |
| large_tokamak_nof | 2 | B0_campaign | 714 | 1/3/3.31/9 | 1:8 2:136 3:301 4:175 5:89 6:2 7:2 9:1 | FLAT 3.31 | 2363 | 1984920 | 840 |
| large_tokamak_nof | 2 | B0_full | 714 | 1/4/3.93/10 | 1:8 2:85 3:109 4:282 5:220 6:5 7:2 8:2 10:1 | FLAT 3.93 | 2803 | 2354520 | 840 |
| large_tokamak_nof | 2 | B0_rbw | 714 | 1/3/3.44/7 | 1:25 2:119 3:306 4:51 5:207 6:3 7:3 | FLAT 3.44 | 2459 | 184425 | 75 |
| large_tokamak_nof | 2 | B2_campaign | 660 | 4/9/8.33/14 | 4:7 5:15 6:135 7:105 8:60 9:134 10:106 11:78 12:14 13:5 14:1 | M1 2.17, M2 2.75, M3 2.41 | 4839 | 1156926 | 239 |
| large_tokamak_nof | 2 | B2_rbw | 660 | 4/7/7.49/13 | 4:22 5:92 6:178 7:45 8:19 9:222 10:46 11:32 12:2 13:2 | M1 1.78, M2 2.92, M3 1.78 | 4283 | 121259 | 28 |
| large_tokamak_nof | 3 | B0_campaign | 546 | 1/3/3.29/6 | 1:6 2:104 3:235 4:131 5:68 6:2 | FLAT 3.29 | 1795 | 1507800 | 840 |
| large_tokamak_nof | 3 | B0_full | 546 | 1/4/3.97/7 | 1:6 2:65 3:78 4:199 5:191 6:4 7:3 | FLAT 3.97 | 2166 | 1819440 | 840 |
| large_tokamak_nof | 3 | B0_rbw | 546 | 1/3/3.44/7 | 1:19 2:91 3:234 4:39 5:160 6:1 7:2 | FLAT 3.44 | 1879 | 140925 | 75 |
| large_tokamak_nof | 3 | B2_campaign | 572 | 4/9/8.33/14 | 4:6 5:13 6:117 7:91 8:52 9:116 10:93 11:65 12:15 13:2 14:2 | M1 2.17, M2 2.76, M3 2.41 | 4195 | 1002938 | 239 |
| large_tokamak_nof | 3 | B2_rbw | 572 | 4/7/7.51/13 | 4:19 5:78 6:152 7:43 8:13 9:195 10:39 11:31 13:2 | M1 1.80, M2 2.92, M3 1.79 | 3723 | 105188 | 28 |
| large_tokamak_nof | 4 | B0_campaign | 546 | 1/3/3.28/6 | 1:6 2:104 3:235 4:136 5:63 6:2 | FLAT 3.28 | 1790 | 1503600 | 840 |
| large_tokamak_nof | 4 | B0_full | 546 | 1/4/3.95/7 | 1:6 2:65 3:78 4:207 5:186 6:2 7:2 | FLAT 3.95 | 2154 | 1809360 | 840 |
| large_tokamak_nof | 4 | B0_rbw | 546 | 1/3/3.44/7 | 1:19 2:91 3:234 4:39 5:161 7:2 | FLAT 3.44 | 1878 | 140850 | 75 |
| large_tokamak_nof | 4 | B2_campaign | 572 | 4/9/8.33/14 | 4:6 5:13 6:117 7:91 8:52 9:119 10:90 11:66 12:13 13:4 14:1 | M1 2.17, M2 2.75, M3 2.41 | 4191 | 1001978 | 239 |
| large_tokamak_nof | 4 | B2_rbw | 572 | 4/7/7.51/13 | 4:19 5:78 6:152 7:43 8:13 9:195 10:39 11:31 13:2 | M1 1.80, M2 2.92, M3 1.79 | 3723 | 105188 | 28 |
| low_aspect_ratio_DEMO | 0 | B0_campaign | 1240 | 1/3/3.34/5 | 1:15 2:124 3:660 4:311 5:130 | FLAT 3.34 | 4137 | 3499902 | 846 |
| low_aspect_ratio_DEMO | 0 | B0_full | 1240 | 1/4/3.97/6 | 1:15 2:124 3:125 4:597 5:378 6:1 | FLAT 3.97 | 4922 | 4164012 | 846 |
| low_aspect_ratio_DEMO | 0 | B0_rbw | 1240 | 1/3/3.43/5 | 1:15 2:159 3:620 4:174 5:272 | FLAT 3.43 | 4249 | 314426 | 74 |
| low_aspect_ratio_DEMO | 0 | B2_campaign | 1050 | 4/8/8.34/13 | 4:12 6:150 7:179 8:253 9:179 10:124 11:151 12:1 13:1 | M1 2.14, M2 2.72, M3 2.49 | 7712 | 1855182 | 241 |
| low_aspect_ratio_DEMO | 0 | B2_rbw | 1050 | 4/7/7.44/11 | 4:12 5:150 6:224 7:151 8:113 9:298 10:99 11:3 | M1 1.71, M2 2.88, M3 1.85 | 6758 | 187334 | 28 |
| low_aspect_ratio_DEMO | 1 | B0_campaign | 9240 | 1/3/3.38/5 | 1:114 2:926 3:4642 4:2469 5:1089 | FLAT 3.38 | 31213 | 26406198 | 846 |
| low_aspect_ratio_DEMO | 1 | B0_full | 9240 | 1/4/3.99/6 | 1:114 2:800 3:991 4:4478 5:2856 6:1 | FLAT 3.99 | 36885 | 31204710 | 846 |
| low_aspect_ratio_DEMO | 1 | B0_rbw | 9240 | 1/3/3.43/5 | 1:114 2:1155 3:4682 4:1198 5:2091 | FLAT 3.43 | 31717 | 2347058 | 74 |
| low_aspect_ratio_DEMO | 1 | B2_campaign | 1218 | 4/8/8.36/13 | 4:14 6:175 7:204 8:290 9:206 10:150 11:176 12:1 13:2 | M1 2.14, M2 2.72, M3 2.49 | 8964 | 2156500 | 241 |
| low_aspect_ratio_DEMO | 1 | B2_rbw | 1218 | 4/7/7.45/11 | 4:14 5:174 6:261 7:174 8:119 9:355 10:118 11:3 | M1 1.71, M2 2.90, M3 1.85 | 7852 | 217954 | 28 |
| low_aspect_ratio_DEMO | 5 | B0_campaign | 840 | 1/3/3.34/5 | 1:10 2:84 3:447 4:207 5:92 | FLAT 3.34 | 2807 | 2374722 | 846 |
| low_aspect_ratio_DEMO | 5 | B0_full | 840 | 1/4/3.97/6 | 1:10 2:84 3:85 4:404 5:256 6:1 | FLAT 3.97 | 3335 | 2821410 | 846 |
| low_aspect_ratio_DEMO | 5 | B0_rbw | 840 | 1/3/3.43/5 | 1:10 2:105 3:425 4:115 5:185 | FLAT 3.43 | 2880 | 213120 | 74 |
| low_aspect_ratio_DEMO | 5 | B2_campaign | 2982 | 4/8/8.34/13 | 4:35 6:426 7:500 8:719 9:511 10:369 11:419 12:2 13:1 | M1 2.14, M2 2.71, M3 2.49 | 21901 | 5268614 | 241 |
| low_aspect_ratio_DEMO | 5 | B2_rbw | 2982 | 4/7/7.43/11 | 4:35 5:427 6:637 7:428 8:322 9:851 10:278 11:4 | M1 1.70, M2 2.88, M3 1.85 | 19170 | 531396 | 28 |
| low_aspect_ratio_DEMO | 6 | B0_campaign | 2680 | 1/3/3.33/5 | 1:33 2:268 3:1429 4:674 5:276 | FLAT 3.33 | 8932 | 7556472 | 846 |
| low_aspect_ratio_DEMO | 6 | B0_full | 2680 | 1/4/3.97/6 | 1:33 2:268 3:274 4:1288 5:815 6:2 | FLAT 3.97 | 10630 | 8992980 | 846 |
| low_aspect_ratio_DEMO | 6 | B0_rbw | 2680 | 1/3/3.43/5 | 1:33 2:345 3:1337 4:365 5:600 | FLAT 3.43 | 9194 | 680356 | 74 |
| low_aspect_ratio_DEMO | 6 | B2_campaign | 1722 | 4/8/8.35/13 | 4:20 6:246 7:289 8:414 9:288 10:220 11:243 13:2 | M1 2.14, M2 2.71, M3 2.50 | 12660 | 3045529 | 241 |
| low_aspect_ratio_DEMO | 6 | B2_rbw | 1722 | 4/7/7.44/11 | 4:20 5:246 6:371 7:244 8:176 9:496 10:166 11:3 | M1 1.70, M2 2.89, M3 1.84 | 11087 | 307616 | 28 |
| low_aspect_ratio_DEMO | 9 | B0_campaign | 1000 | 1/3/3.34/5 | 1:13 2:101 3:530 4:248 5:108 | FLAT 3.34 | 3337 | 2823102 | 846 |
| low_aspect_ratio_DEMO | 9 | B0_full | 1000 | 1/4/3.97/6 | 1:12 2:100 3:105 4:476 5:305 6:2 | FLAT 3.97 | 3968 | 3356928 | 846 |
| low_aspect_ratio_DEMO | 9 | B0_rbw | 1000 | 1/3/3.44/5 | 1:12 2:125 3:504 4:129 5:230 | FLAT 3.44 | 3440 | 254560 | 74 |
| low_aspect_ratio_DEMO | 9 | B2_campaign | 1134 | 4/8/8.36/13 | 4:13 6:163 7:190 8:270 9:194 10:137 11:163 12:1 13:3 | M1 2.14, M2 2.72, M3 2.49 | 8346 | 2007830 | 241 |
| low_aspect_ratio_DEMO | 9 | B2_rbw | 1134 | 4/7/7.45/11 | 4:13 5:162 6:244 7:161 8:110 9:330 10:108 11:6 | M1 1.71, M2 2.90, M3 1.84 | 7315 | 202978 | 28 |
| st_regression | 0 | B0_campaign | 570 | 1/3/3.57/12 | 1:9 2:49 3:272 4:194 5:22 7:1 9:12 10:10 12:1 | FLAT 3.57 | 2036 | 1683772 | 827 |
| st_regression | 0 | B0_full | 570 | 1/4/4.29/12 | 1:9 2:19 3:248 4:76 5:50 6:143 7:1 8:1 9:4 10:18 12:1 | FLAT 4.29 | 2446 | 2022842 | 827 |
| st_regression | 0 | B0_rbw | 570 | 1/2/3.22/7 | 1:28 2:260 3:64 4:2 5:212 6:2 7:2 | FLAT 3.22 | 1834 | 133882 | 73 |
| st_regression | 0 | B2_campaign | 570 | 5/9/9.23/17 | 5:9 6:19 7:13 8:137 9:171 10:116 11:59 12:41 13:1 14:2 15:1 17:1 | M1 2.39, M2 2.40, PULSE 1.00, M3 2.44 | 4119 | 970258 | 236 |
| st_regression | 0 | B2_rbw | 2370 | 5/8/8.30/15 | 5:118 6:211 7:654 8:404 9:166 10:501 11:306 12:6 13:2 14:1 15:1 | M1 1.78, M2 2.62, PULSE 1.00, M3 1.89 | 14923 | 404580 | 27 |
| st_regression | 1 | B0_campaign | 3150 | 1/3/3.42/12 | 1:61 2:449 3:1390 4:1040 5:110 6:7 7:1 8:2 9:48 10:38 11:2 12:2 | FLAT 3.42 | 10762 | 8900174 | 827 |
| st_regression | 1 | B0_full | 3690 | 1/3/4.08/12 | 1:61 2:242 3:1571 4:426 5:575 6:718 7:4 8:3 9:32 10:52 11:5 12:1 | FLAT 4.08 | 15072 | 12464544 | 827 |
| st_regression | 1 | B0_rbw | 2430 | 1/2/3.19/7 | 1:127 2:1135 3:253 4:12 5:883 6:17 7:3 | FLAT 3.19 | 7742 | 565166 | 73 |
| st_regression | 1 | B2_campaign | 3510 | 5/9/8.85/17 | 5:69 6:215 7:196 8:925 9:1092 10:502 11:358 12:130 13:12 14:5 15:5 17:1 | M1 2.25, M2 2.38, PULSE 1.00, M3 2.23 | 24051 | 5659602 | 235 |
| st_regression | 1 | B2_rbw | 15750 | 5/8/8.23/15 | 5:785 6:1842 7:4140 8:2676 9:1658 10:2277 11:2012 12:294 13:51 14:14 15:1 | M1 1.76, M2 2.60, PULSE 1.00, M3 1.87 | 98091 | 2661364 | 27 |
| st_regression | 2 | B0_campaign | 2880 | 1/3/3.62/12 | 1:47 2:231 3:1341 4:666 5:538 6:10 7:1 9:8 10:24 11:13 12:1 | FLAT 3.62 | 10420 | 8617340 | 827 |
| st_regression | 2 | B0_full | 2550 | 1/3/4.08/11 | 1:42 2:90 3:1173 4:271 5:362 6:574 7:14 8:1 9:6 10:16 11:1 | FLAT 4.08 | 10410 | 8609070 | 827 |
| st_regression | 2 | B0_rbw | 2250 | 1/2/3.21/7 | 1:112 2:1045 3:232 4:2 5:839 6:15 7:5 | FLAT 3.21 | 7226 | 527498 | 73 |
| st_regression | 2 | B2_campaign | 2310 | 5/9/9.16/17 | 5:38 6:79 7:124 8:552 9:676 10:419 11:233 12:126 13:40 14:11 15:11 17:1 | M1 2.35, M2 2.42, PULSE 1.00, M3 2.39 | 16533 | 3892592 | 235 |
| st_regression | 2 | B2_rbw | 3930 | 5/8/8.35/15 | 5:196 6:309 7:1129 8:664 9:201 10:864 11:529 12:14 13:19 14:4 15:1 | M1 1.79, M2 2.65, PULSE 1.00, M3 1.91 | 24943 | 677403 | 27 |
| st_regression | 3 | B0_campaign | 1050 | 1/3/3.47/10 | 1:17 2:101 3:509 4:334 5:62 6:3 7:1 9:6 10:17 | FLAT 3.47 | 3641 | 3011107 | 827 |
| st_regression | 3 | B0_full | 1050 | 1/4/4.16/11 | 1:17 2:35 3:471 4:125 5:130 6:242 7:5 8:2 9:12 10:10 11:1 | FLAT 4.16 | 4372 | 3615644 | 827 |
| st_regression | 3 | B0_rbw | 1050 | 1/2/3.22/7 | 1:52 2:484 3:112 4:2 5:390 6:7 7:3 | FLAT 3.22 | 3377 | 246521 | 73 |
| st_regression | 3 | B2_campaign | 1050 | 5/9/9.23/17 | 5:17 6:35 7:32 8:248 9:324 10:200 11:107 12:50 13:27 14:5 15:4 17:1 | M1 2.38, M2 2.42, PULSE 1.00, M3 2.43 | 7594 | 1788185 | 235 |
| st_regression | 3 | B2_rbw | 2370 | 5/8/8.35/15 | 5:118 6:199 7:666 8:400 9:98 10:553 11:318 12:8 13:7 14:2 15:1 | M1 1.79, M2 2.66, PULSE 1.00, M3 1.90 | 15046 | 409390 | 27 |
| st_regression | 4 | B0_campaign | 1170 | 1/3/3.28/7 | 1:19 2:134 3:568 4:399 5:47 6:2 7:1 | FLAT 3.28 | 3841 | 3176507 | 827 |
| st_regression | 4 | B0_full | 1170 | 1/3/4.06/8 | 1:19 2:39 3:543 4:125 5:150 6:289 7:3 8:2 | FLAT 4.06 | 4747 | 3925769 | 827 |
| st_regression | 4 | B0_rbw | 690 | 1/2/3.20/7 | 1:34 2:319 3:75 4:4 5:253 6:3 7:2 | FLAT 3.20 | 2210 | 161330 | 73 |
| st_regression | 4 | B2_campaign | 1170 | 5/9/9.16/17 | 5:19 6:42 7:53 8:260 9:347 10:241 11:122 12:80 13:1 14:2 15:2 17:1 | M1 2.35, M2 2.39, PULSE 1.00, M3 2.43 | 8381 | 1972937 | 235 |
| st_regression | 4 | B2_rbw | 2490 | 5/8/8.30/15 | 5:124 6:223 7:686 8:420 9:176 10:527 11:325 12:4 13:3 14:1 15:1 | M1 1.78, M2 2.63, PULSE 1.00, M3 1.89 | 15685 | 425429 | 27 |

### 4.5 The exit audit

**T4.** *Same rows. The whole-`y` residual (frozen ruler) at the entry to the output path,
recounted from `audit_residual.json` at 1e-6 and 1e-8: `all` over every continuous component;
`restricted` with the components the per-run deferred nodes write excluded (V4's statistic for
the arm whose per-run nodes have not run at the audit position; the 112 `costs.*` components
above 1e-6 on every `B2` row are those). `constraint 93 rcm` is the burn-time consistency
residual, normalised, on the lifted arm.*

| configuration | seed | run | τ of record | max (all) | n ≥ 1e-6 (all) | n ≥ 1e-8 (all) | max (restricted) | n ≥ 1e-6 (restr.) | n ≥ 1e-8 (restr.) | n excluded | discrete mismatches | constraint 93 rcm (B2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | 0 | B0_campaign | 1e-06 | 1.2e-11 | 0 | 0 | 1.2e-11 | 0 | 0 | 122 | 0 | — |
| large_tokamak_nof | 0 | B0_full | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 122 | 0 | — |
| large_tokamak_nof | 0 | B0_rbw | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 122 | 0 | — |
| large_tokamak_nof | 0 | B2_campaign | 1e-06 | 1.1e+00 | 112 | 112 | 0.0e+00 | 0 | 0 | 122 | 2 | 1.2e-08 |
| large_tokamak_nof | 0 | B2_rbw | 1e-08 | 1.1e+00 | 112 | 112 | 0.0e+00 | 0 | 0 | 122 | 2 | 1.2e-08 |
| large_tokamak_nof | 1 | B0_campaign | 1e-06 | 1.2e-11 | 0 | 0 | 1.2e-11 | 0 | 0 | 122 | 0 | — |
| large_tokamak_nof | 1 | B0_full | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 122 | 0 | — |
| large_tokamak_nof | 1 | B0_rbw | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 122 | 0 | — |
| large_tokamak_nof | 1 | B2_campaign | 1e-06 | 1.1e+00 | 112 | 112 | 0.0e+00 | 0 | 0 | 122 | 2 | 1.3e-09 |
| large_tokamak_nof | 1 | B2_rbw | 1e-08 | 1.1e+00 | 112 | 112 | 0.0e+00 | 0 | 0 | 122 | 2 | 1.3e-09 |
| large_tokamak_nof | 2 | B0_campaign | 1e-06 | 1.1e-11 | 0 | 0 | 1.1e-11 | 0 | 0 | 122 | 0 | — |
| large_tokamak_nof | 2 | B0_full | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 122 | 0 | — |
| large_tokamak_nof | 2 | B0_rbw | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 122 | 0 | — |
| large_tokamak_nof | 2 | B2_campaign | 1e-06 | 1.0e+00 | 112 | 112 | 0.0e+00 | 0 | 0 | 122 | 2 | 2.6e-08 |
| large_tokamak_nof | 2 | B2_rbw | 1e-08 | 1.0e+00 | 112 | 112 | 0.0e+00 | 0 | 0 | 122 | 2 | 2.6e-08 |
| large_tokamak_nof | 3 | B0_campaign | 1e-06 | 1.2e-11 | 0 | 0 | 1.2e-11 | 0 | 0 | 122 | 0 | — |
| large_tokamak_nof | 3 | B0_full | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 122 | 0 | — |
| large_tokamak_nof | 3 | B0_rbw | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 122 | 0 | — |
| large_tokamak_nof | 3 | B2_campaign | 1e-06 | 1.0e+00 | 112 | 112 | 0.0e+00 | 0 | 0 | 122 | 2 | 3.3e-08 |
| large_tokamak_nof | 3 | B2_rbw | 1e-08 | 1.0e+00 | 112 | 112 | 0.0e+00 | 0 | 0 | 122 | 2 | 3.3e-08 |
| large_tokamak_nof | 4 | B0_campaign | 1e-06 | 1.1e-11 | 0 | 0 | 1.1e-11 | 0 | 0 | 122 | 0 | — |
| large_tokamak_nof | 4 | B0_full | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 122 | 0 | — |
| large_tokamak_nof | 4 | B0_rbw | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 122 | 0 | — |
| large_tokamak_nof | 4 | B2_campaign | 1e-06 | 1.1e+00 | 112 | 112 | 7.3e-16 | 0 | 0 | 122 | 2 | 1.1e-07 |
| large_tokamak_nof | 4 | B2_rbw | 1e-08 | 1.1e+00 | 112 | 112 | 0.0e+00 | 0 | 0 | 122 | 2 | 1.1e-07 |
| low_aspect_ratio_DEMO | 0 | B0_campaign | 1e-06 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 123 | 0 | — |
| low_aspect_ratio_DEMO | 0 | B0_full | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 123 | 0 | — |
| low_aspect_ratio_DEMO | 0 | B0_rbw | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 123 | 0 | — |
| low_aspect_ratio_DEMO | 0 | B2_campaign | 1e-06 | 1.0e+00 | 112 | 112 | 0.0e+00 | 0 | 0 | 123 | 2 | 1.6e-10 |
| low_aspect_ratio_DEMO | 0 | B2_rbw | 1e-08 | 1.0e+00 | 112 | 112 | 0.0e+00 | 0 | 0 | 123 | 2 | 1.6e-10 |
| low_aspect_ratio_DEMO | 1 | B0_campaign | 1e-06 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 123 | 0 | — |
| low_aspect_ratio_DEMO | 1 | B0_full | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 123 | 0 | — |
| low_aspect_ratio_DEMO | 1 | B0_rbw | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 123 | 0 | — |
| low_aspect_ratio_DEMO | 1 | B2_campaign | 1e-06 | 1.0e+00 | 112 | 112 | 0.0e+00 | 0 | 0 | 123 | 2 | 2.1e-11 |
| low_aspect_ratio_DEMO | 1 | B2_rbw | 1e-08 | 1.0e+00 | 112 | 112 | 0.0e+00 | 0 | 0 | 123 | 2 | 2.1e-11 |
| low_aspect_ratio_DEMO | 5 | B0_campaign | 1e-06 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 123 | 0 | — |
| low_aspect_ratio_DEMO | 5 | B0_full | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 123 | 0 | — |
| low_aspect_ratio_DEMO | 5 | B0_rbw | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 123 | 0 | — |
| low_aspect_ratio_DEMO | 5 | B2_campaign | 1e-06 | 1.0e+00 | 112 | 112 | 0.0e+00 | 0 | 0 | 123 | 2 | 2.1e-10 |
| low_aspect_ratio_DEMO | 5 | B2_rbw | 1e-08 | 1.0e+00 | 112 | 112 | 4.4e-15 | 0 | 0 | 123 | 2 | 2.1e-10 |
| low_aspect_ratio_DEMO | 6 | B0_campaign | 1e-06 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 123 | 0 | — |
| low_aspect_ratio_DEMO | 6 | B0_full | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 123 | 0 | — |
| low_aspect_ratio_DEMO | 6 | B0_rbw | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 123 | 0 | — |
| low_aspect_ratio_DEMO | 6 | B2_campaign | 1e-06 | 1.0e+00 | 112 | 112 | 0.0e+00 | 0 | 0 | 123 | 2 | 1.8e-10 |
| low_aspect_ratio_DEMO | 6 | B2_rbw | 1e-08 | 1.0e+00 | 112 | 112 | 0.0e+00 | 0 | 0 | 123 | 2 | 1.8e-10 |
| low_aspect_ratio_DEMO | 9 | B0_campaign | 1e-06 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 123 | 0 | — |
| low_aspect_ratio_DEMO | 9 | B0_full | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 123 | 0 | — |
| low_aspect_ratio_DEMO | 9 | B0_rbw | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 123 | 0 | — |
| low_aspect_ratio_DEMO | 9 | B2_campaign | 1e-06 | 1.0e+00 | 112 | 112 | 0.0e+00 | 0 | 0 | 123 | 2 | 1.8e-09 |
| low_aspect_ratio_DEMO | 9 | B2_rbw | 1e-08 | 1.0e+00 | 112 | 112 | 0.0e+00 | 0 | 0 | 123 | 2 | 1.8e-09 |
| st_regression | 0 | B0_campaign | 1e-06 | 4.9e-14 | 0 | 0 | 4.9e-14 | 0 | 0 | 123 | 0 | — |
| st_regression | 0 | B0_full | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 123 | 0 | — |
| st_regression | 0 | B0_rbw | 1e-08 | 4.9e-14 | 0 | 0 | 4.9e-14 | 0 | 0 | 123 | 0 | — |
| st_regression | 0 | B2_campaign | 1e-06 | 1.0e+00 | 112 | 112 | 1.6e-11 | 0 | 0 | 123 | 2 | — |
| st_regression | 0 | B2_rbw | 1e-08 | 1.1e+00 | 112 | 112 | 2.4e-10 | 0 | 0 | 123 | 2 | — |
| st_regression | 1 | B0_campaign | 1e-06 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 123 | 0 | — |
| st_regression | 1 | B0_full | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 123 | 0 | — |
| st_regression | 1 | B0_rbw | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 123 | 0 | — |
| st_regression | 1 | B2_campaign | 1e-06 | 1.2e+01 | 112 | 112 | 4.4e-12 | 0 | 0 | 123 | 2 | — |
| st_regression | 1 | B2_rbw | 1e-08 | 1.5e+01 | 112 | 112 | 6.6e-12 | 0 | 0 | 123 | 2 | — |
| st_regression | 2 | B0_campaign | 1e-06 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 123 | 0 | — |
| st_regression | 2 | B0_full | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 123 | 0 | — |
| st_regression | 2 | B0_rbw | 1e-08 | 4.9e-14 | 0 | 0 | 4.9e-14 | 0 | 0 | 123 | 0 | — |
| st_regression | 2 | B2_campaign | 1e-06 | 2.5e+00 | 112 | 112 | 3.6e-11 | 0 | 0 | 123 | 2 | — |
| st_regression | 2 | B2_rbw | 1e-08 | 1.1e+00 | 112 | 112 | 2.4e-10 | 0 | 0 | 123 | 2 | — |
| st_regression | 3 | B0_campaign | 1e-06 | 4.9e-14 | 0 | 0 | 4.9e-14 | 0 | 0 | 123 | 0 | — |
| st_regression | 3 | B0_full | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 123 | 0 | — |
| st_regression | 3 | B0_rbw | 1e-08 | 4.9e-14 | 0 | 0 | 4.9e-14 | 0 | 0 | 123 | 0 | — |
| st_regression | 3 | B2_campaign | 1e-06 | 1.5e+00 | 112 | 112 | 4.9e-14 | 0 | 0 | 123 | 2 | — |
| st_regression | 3 | B2_rbw | 1e-08 | 1.1e+00 | 112 | 112 | 2.4e-10 | 0 | 0 | 123 | 2 | — |
| st_regression | 4 | B0_campaign | 1e-06 | 4.9e-14 | 0 | 0 | 4.9e-14 | 0 | 0 | 123 | 0 | — |
| st_regression | 4 | B0_full | 1e-08 | 0.0e+00 | 0 | 0 | 0.0e+00 | 0 | 0 | 123 | 0 | — |
| st_regression | 4 | B0_rbw | 1e-08 | 4.9e-14 | 0 | 0 | 4.9e-14 | 0 | 0 | 123 | 0 | — |
| st_regression | 4 | B2_campaign | 1e-06 | 1.5e+00 | 112 | 112 | 6.6e-12 | 0 | 0 | 123 | 2 | — |
| st_regression | 4 | B2_rbw | 1e-08 | 1.1e+00 | 112 | 112 | 2.4e-10 | 0 | 0 | 123 | 2 | — |

**T7.** *Every restricted component at or above 1e-12 at exit, by name, per run (runs with none
omitted): the largest four, and for each its membership of the arm's census set, its DSM set
(`test_sets.json`: feedback / interface / none), the block of V4's write set that writes it and
its DSM readers.*

| configuration | seed | run | n ≥ floor | largest four (name, scaled residual) | membership of each (census set; DSM set; writing block; DSM readers) |
|---|---|---|---|---|---|
| large_tokamak_nof | 0 | B0_campaign | 1 | `heat_transport.tlvpmw` 1.2e-11 | not census, interface, by M3, read by Costs |
| large_tokamak_nof | 1 | B0_campaign | 1 | `heat_transport.tlvpmw` 1.2e-11 | not census, interface, by M3, read by Costs |
| large_tokamak_nof | 2 | B0_campaign | 1 | `heat_transport.tlvpmw` 1.1e-11 | not census, interface, by M3, read by Costs |
| large_tokamak_nof | 3 | B0_campaign | 1 | `heat_transport.tlvpmw` 1.2e-11 | not census, interface, by M3, read by Costs |
| large_tokamak_nof | 4 | B0_campaign | 1 | `heat_transport.tlvpmw` 1.1e-11 | not census, interface, by M3, read by Costs |
| st_regression | 0 | B2_campaign | 18 | `fwbs.p_cp_shield_nuclear_heat_mw` 1.6e-11; `power.p_shld_heat_deposited_mw` 1.6e-11; `heat_transport.p_shld_coolant_pump_mw` 1.6e-11; `power.p_shld_coolant_pump_elec_mw` 1.6e-11 … | not census, interface, by M3, read by CCFE_HCPB,Power; not census, no DSM set, by M3, read by Power; not census, interface, by M3, read by Power; not census, no DSM set, by M3, read by Power |
| st_regression | 0 | B2_rbw | 1 | `heat_transport.tlvpmw` 2.4e-10 | not census, interface, by M3, read by Costs |
| st_regression | 1 | B2_campaign | 9 | `fwbs.p_cp_shield_nuclear_heat_mw` 4.4e-12; `power.p_shld_heat_deposited_mw` 4.4e-12; `heat_transport.p_shld_coolant_pump_mw` 4.4e-12; `power.p_shld_coolant_pump_elec_mw` 4.4e-12 … | not census, interface, by M3, read by CCFE_HCPB,Power; not census, no DSM set, by M3, read by Power; not census, interface, by M3, read by Power; not census, no DSM set, by M3, read by Power |
| st_regression | 1 | B2_rbw | 1 | `heat_transport.tlvpmw` 6.6e-12 | not census, interface, by M3, read by Costs |
| st_regression | 2 | B2_campaign | 28 | `fwbs.p_cp_shield_nuclear_heat_mw` 3.6e-11; `power.p_shld_coolant_pump_elec_mw` 3.6e-11; `heat_transport.p_shld_coolant_pump_mw` 3.6e-11; `power.p_shld_heat_deposited_mw` 3.6e-11 … | not census, interface, by M3, read by CCFE_HCPB,Power; not census, no DSM set, by M3, read by Power; not census, interface, by M3, read by Power; not census, no DSM set, by M3, read by Power |
| st_regression | 2 | B2_rbw | 1 | `heat_transport.tlvpmw` 2.4e-10 | not census, interface, by M3, read by Costs |
| st_regression | 3 | B2_rbw | 1 | `heat_transport.tlvpmw` 2.4e-10 | not census, interface, by M3, read by Costs |
| st_regression | 4 | B2_campaign | 18 | `fwbs.p_cp_shield_nuclear_heat_mw` 6.6e-12; `power.p_shld_heat_deposited_mw` 6.6e-12; `power.p_shld_coolant_pump_elec_mw` 6.6e-12; `heat_transport.p_shld_coolant_pump_mw` 6.6e-12 … | not census, interface, by M3, read by CCFE_HCPB,Power; not census, no DSM set, by M3, read by Power; not census, no DSM set, by M3, read by Power; not census, interface, by M3, read by Power |
| st_regression | 4 | B2_rbw | 1 | `heat_transport.tlvpmw` 2.4e-10 | not census, interface, by M3, read by Costs |

### 4.6 The decomposition

**T5.** *Per configuration and pair, `R = ρ × ε` with `N` solve-phase node calls and `C`
evaluations: pooled over the seeds where both members are accepted optima (`seeds used` of the
five offered; sums, so `R = ρ × ε` exactly), and the per-seed median (nearest-rank upper-middle,
V4's) with its [min, max]. `campaign_1e-6` is the campaign's `B2 / B0`; `census_1e-8` this task's;
the other four pairs each new variant against its campaign partner and the two `B0` 1e-8 variants
against each other.*

| configuration | pair | numerator / denominator | seeds used | R pooled | ρ pooled | ε pooled | R median [min, max] | ρ median [min, max] | ε median [min, max] | N num / den | C num / den |
|---|---|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | campaign_1e-6 | B2_campaign / B0_campaign | 5/5 | 0.6267 | 0.6151 | 1.0189 | 0.6452 [0.5654, 0.6466] | 0.6158 [0.6116, 0.6172] | 1.0476 [0.9244, 1.0476] | 132773 / 211848 | 3124 / 3066 |
| large_tokamak_nof | census_1e-8 | B2_rbw / B0_rbw | 5/5 | 0.4907 | 0.4816 | 1.0189 | 0.5047 [0.4441, 0.5056] | 0.4817 [0.4805, 0.4826] | 1.0476 [0.9244, 1.0476] | 108696 / 221529 | 3124 / 3066 |
| large_tokamak_nof | B0_full_1e-8_vs_B0_campaign | B0_full / B0_campaign | 5/5 | 1.2010 | 1.2010 | 1.0000 | 1.2057 [1.1862, 1.2067] | 1.2057 [1.1862, 1.2067] | 1.0000 [1.0000, 1.0000] | 254436 / 211848 | 3066 / 3066 |
| large_tokamak_nof | B0_rbw_1e-8_vs_B0_campaign | B0_rbw / B0_campaign | 5/5 | 1.0457 | 1.0457 | 1.0000 | 1.0468 [1.0406, 1.0492] | 1.0468 [1.0406, 1.0492] | 1.0000 [1.0000, 1.0000] | 221529 / 211848 | 3066 / 3066 |
| large_tokamak_nof | B2_rbw_1e-8_vs_B2_campaign | B2_rbw / B2_campaign | 5/5 | 0.8187 | 0.8187 | 1.0000 | 0.8182 [0.8175, 0.8203] | 0.8182 [0.8175, 0.8203] | 1.0000 [1.0000, 1.0000] | 108696 / 132773 | 3124 / 3124 |
| large_tokamak_nof | B0_rbw_1e-8_vs_B0_full_1e-8 | B0_rbw / B0_full | 5/5 | 0.8707 | 0.8707 | 1.0000 | 0.8682 [0.8674, 0.8773] | 0.8682 [0.8674, 0.8773] | 1.0000 [1.0000, 1.0000] | 221529 / 254436 | 3066 / 3066 |
| low_aspect_ratio_DEMO | campaign_1e-6 | B2_campaign / B0_campaign | 5/5 | 0.3319 | 0.6141 | 0.5404 | 0.5237 [0.0806, 2.1921] | 0.6184 [0.6115, 0.6197] | 0.8468 [0.1318, 3.5500] | 351426 / 1058946 | 8106 / 15000 |
| low_aspect_ratio_DEMO | census_1e-8 | B2_rbw / B0_rbw | 5/5 | 0.2641 | 0.4886 | 0.5404 | 0.4145 [0.0645, 1.7353] | 0.4888 [0.4879, 0.4895] | 0.8468 [0.1318, 3.5500] | 285464 / 1081080 | 8106 / 15000 |
| low_aspect_ratio_DEMO | B0_full_1e-8_vs_B0_campaign | B0_full / B0_campaign | 5/5 | 1.1847 | 1.1847 | 1.0000 | 1.1891 [1.1817, 1.1901] | 1.1891 [1.1817, 1.1901] | 1.0000 [1.0000, 1.0000] | 1254540 / 1058946 | 15000 / 15000 |
| low_aspect_ratio_DEMO | B0_rbw_1e-8_vs_B0_campaign | B0_rbw / B0_campaign | 5/5 | 1.0209 | 1.0209 | 1.0000 | 1.0271 [1.0161, 1.0309] | 1.0271 [1.0161, 1.0309] | 1.0000 [1.0000, 1.0000] | 1081080 / 1058946 | 15000 / 15000 |
| low_aspect_ratio_DEMO | B2_rbw_1e-8_vs_B2_campaign | B2_rbw / B2_campaign | 5/5 | 0.8123 | 0.8123 | 1.0000 | 0.8124 [0.8118, 0.8129] | 0.8124 [0.8118, 0.8129] | 1.0000 [1.0000, 1.0000] | 285464 / 351426 | 8106 / 8106 |
| low_aspect_ratio_DEMO | B0_rbw_1e-8_vs_B0_full_1e-8 | B0_rbw / B0_full | 5/5 | 0.8617 | 0.8617 | 1.0000 | 0.8636 [0.8599, 0.8669] | 0.8636 [0.8599, 0.8669] | 1.0000 [1.0000, 1.0000] | 1081080 / 1254540 | 15000 / 15000 |
| st_regression | campaign_1e-6 | B2_campaign / B0_campaign | 5/5 | 0.5321 | 0.5450 | 0.9762 | 0.5650 [0.4285, 0.5954] | 0.5497 [0.5342, 0.5949] | 1.0000 [0.8021, 1.1143] | 343021 / 644700 | 8610 / 8820 |
| st_regression | census_1e-8 | B2_rbw / B0_rbw | 4/5 | 1.2441 | 0.5083 | 2.4474 | 1.8332 [0.8909, 2.1025] | 0.5087 [0.5057, 0.5100] | 3.6087 [1.7467, 4.1579] | 382672 / 307587 | 11160 / 4560 |
| st_regression | B0_full_1e-8_vs_B0_campaign | B0_full / B0_campaign | 5/5 | 1.2067 | 1.1787 | 1.0238 | 1.2014 [0.9990, 1.4005] | 1.2008 [1.1283, 1.2359] | 1.0000 [0.8854, 1.1714] | 777987 / 644700 | 9030 / 8820 |
| st_regression | B0_rbw_1e-8_vs_B0_campaign | B0_rbw / B0_campaign | 5/5 | 0.7293 | 0.9202 | 0.7925 | 0.7194 [0.5754, 0.9275] | 0.9275 [0.8876, 0.9756] | 0.7812 [0.5897, 1.0000] | 470169 / 644700 | 6990 / 8820 |
| st_regression | B2_rbw_1e-8_vs_B2_campaign | B2_rbw / B2_campaign | 4/5 | 1.8357 | 0.8389 | 2.1882 | 1.8849 [1.4417, 3.4450] | 0.8351 [0.8285, 0.8474] | 2.2571 [1.7013, 4.1579] | 382672 / 208461 | 11160 / 5100 |
| st_regression | B0_rbw_1e-8_vs_B0_full_1e-8 | B0_rbw / B0_full | 5/5 | 0.6043 | 0.7807 | 0.7741 | 0.6941 [0.4656, 0.7724] | 0.7800 [0.7498, 0.7894] | 0.8824 [0.5897, 1.0000] | 470169 / 777987 | 6990 / 9030 |

### 4.7 Wall clock (context, never evidence)

**T6.** *Per configuration and member: n runs, their summed, minimum and maximum `wall_s` from
the records. One run each; another task on the machine; the first run of the matrix (nof `B0`
census seed 0, later re-made) carried numba's compilation.*

| configuration | run | n | Σ wall s | min | max |
|---|---|---|---|---|---|
| large_tokamak_nof | B0_campaign | 5 | 140 | 24 | 32 |
| large_tokamak_nof | B0_full | 5 | 169 | 30 | 43 |
| large_tokamak_nof | B0_rbw | 5 | 103 | 17 | 25 |
| large_tokamak_nof | B2_campaign | 5 | 141 | 26 | 30 |
| large_tokamak_nof | B2_rbw | 5 | 95 | 16 | 22 |
| low_aspect_ratio_DEMO | B0_campaign | 5 | 688 | 39 | 428 |
| low_aspect_ratio_DEMO | B0_full | 5 | 743 | 40 | 470 |
| low_aspect_ratio_DEMO | B0_rbw | 5 | 423 | 25 | 256 |
| low_aspect_ratio_DEMO | B2_campaign | 5 | 380 | 50 | 140 |
| low_aspect_ratio_DEMO | B2_rbw | 5 | 245 | 33 | 89 |
| st_regression | B0_campaign | 5 | 417 | 28 | 145 |
| st_regression | B0_full | 5 | 529 | 31 | 198 |
| st_regression | B0_rbw | 5 | 180 | 17 | 59 |
| st_regression | B2_campaign | 5 | 379 | 27 | 150 |
| st_regression | B2_rbw | 5 | 828 | 71 | 476 |

### 4.8 Reading the tables

1. **Pulsed configurations: the loops' change is invisible to the optimiser.** T2: on all 30
   nof / lad rows of the three new variants, `Δ iterations Σ = 0` and `C ratio = 1.0000`;
   `|Δf|/max` ≤ 5.3e-13. T4: the 1e-8 flat loops exit at the exact fixed point (maximum 0.0) on
   all 20 pulsed `B0` runs; the campaign's `B0` on nof left `tlvpmw` at 1.2e-11 (T7). The
   path is the same to the last evaluation because the loops end at the same fixed points:
   where the 1e-6 whole-`y` test stopped a sweep late and the 1e-8 test stops at the exact point,
   the function values VMCON compares differ by less than its own decisions notice.
2. **What the 1e-8 tolerance costs, and what the census set gives back (`B0`).** T5: whole-`y`
   at 1e-8 is +20.1 % / +18.5 % / +17.9 % node calls per evaluation over the campaign's control
   (sweeps per evaluation 3.96 / 3.97 / 4.08 against 3.28 / 3.34 / 3.47, T3); the census set at
   1e-8 is +4.6 % / +2.1 % / −8.0 % (3.44 / 3.43 / 3.21). T3's histograms show how: the census
   loop stops after one sweep on three times as many evaluations as the whole-`y` loop (nof:
   22 against 7 of 630) — those are the evaluations the whole-`y` test at 1e-6 held open for a
   component outside the carried set — and takes a fifth sweep on more of the rest.
3. **The partitioned arm at matched accuracy.** T5: `B2` census 1e-8 against `B2` campaign is
   0.819 / 0.812 / 0.839 per evaluation; per block (T3, nof) `M1` 2.17 → 1.80 sweeps per solve,
   `M3` 2.41 → 1.78, `M2` 2.75 → 2.92. The census pair's ρ is 0.482 / 0.489 / 0.508 against the
   campaign pair's 0.615 / 0.614 / 0.545. A89's evaluation-phase figure for the same pair
   (`A2 rbw / A0 rbw`, displaced entries) was 0.43 / 0.53 / 0.60.
4. **`st_regression`: the path moves, in both arms, under the tolerance alone and under the
   set.** T2: `B0` whole-`y` 1e-8 changes seeds 1 (+9 iterations) and 2 (−5); `B0` census changes
   seeds 1, 2, 4 (−12, −10, −8; the campaign's seed 2 had retried, 27 + 21 iterations, the census
   run does not); `B2` census changes every seed, always longer: 10 → 40, 59 → 262 (failed),
   39 → 66, 18 → 40, 20 → 42. The accepted optima agree with the campaign's to ≤ 2.2e-11 except
   seed 1's `B0` pair (6.3e-9, the same distance the campaign's own `B0` and `B2` are apart on
   that seed). So the trajectory changes and the optimum does not.
5. **The failure.** st seed 1 `B2` census: attempt 1 `ifail = 2` (`MAX_ITERATIONS`, `maxcal = 100`
   in the input file), attempt 2 at `epsfcn × 10` `ifail = 5`, attempt 3 at `epsfcn × 0.1` again
   `ifail = 2`; 15 750 evaluations, 531 034 node calls, final `norm_objf` −16.8309 with
   `sqsumsq` 2.8e-10 (the campaign's `B2` on this seed: 59 iterations, −16.80891, 6.1e-12). The
   campaign's own st `B2` failed seed 5 the same way (`ifail = 5` after three attempts, 82
   iterations); the failure is not new to the arm, but on this seed it is new to the census test.
6. **The exit audit and the census sets.** T4: `n ≥ 1e-8` is 0 on every one of the 45 runs'
   governing statistic (whole-`y` for `B0`, restricted for `B2`); no discrete mismatch and no
   moved constant on any `B0` row (the two on every `B2` row, `vacuum.n_vac_pumps_high` and
   `vacuum.n_vv_vacuum_ducts`, are per-run deferred writes, present on the campaign's rows
   too). T7: the only component a census loop leaves above 1e-12 is `heat_transport.tlvpmw`
   in st `B2` (2.4e-10 on seeds 0, 2, 3, 4; 6.6e-12 on seed 1) — outside every census set, a
   DSM interface (not feedback) component written by `Power` in `M3` and read only by `Costs`,
   which `B2` defers per run. `M3`'s loop stops on its ten census components and leaves this
   feed-forward output one sweep short; nothing in any loop reads it. The campaign's whole-`y`
   `B2` loops on st left 9–28 restricted components at ≤ 3.6e-11 (`fwbs.*`, `power.*`,
   `heat_transport.*` of `M3`), all also outside the census sets. **No carried variable outside
   the census sets was found at or above τ in 45 optimisations** — the evidence V5 item 6's
   prerequisite (2) asked for at optimisation scale, on these seeds.
7. **Why st's path moves is not settled here.** Three observations bound it: (i) the tolerance
   alone already moves st's `B0` path (item 4), so the census set is not the only cause; (ii)
   A89's committed noise ladder (`tolerance.json`, `st_regression/A0_rbw` and `A2_rbw`) puts the
   census-set control's objective-gradient error at 1e-8 at **1.2e-8 relative** on st where the
   whole-`y` test reads 0 at both 1e-6 and 1e-8 — st's figure of merit is computed through the
   loop, nof's (the major radius) is an iteration variable — so on st the census loops hand
   VMCON values that are within the h³ rule but not bit-stable, and VMCON's path on st is known
   to be sensitive (A43's three iteration constructions at 1.17 / 0.91 / 1.07 on 23 st pairs);
   (iii) the partitioned census arm's exit is 2.4e-10 off a fixed point in `tlvpmw` (item 6),
   consistently, which the flat census arm's is not — and it is `B2`, not `B0`, whose path
   lengthens on every seed. A `B2` whole-`y` 1e-8 variant and a τ ladder on st's `B2` census arm
   would separate these (§7).

## 5. Autonomous decisions, each with its reversal path

1. **Seeds by rule, not by list**: the first five of the campaign's every-arm-converged set,
   ascending, computed by the script from the campaign's records. Reversal: `N_SEEDS` or a
   literal seed list in `run_tolerance_phase_b.py`; the brief's "0–4 where possible" gives the same
   seeds on nof and st.
2. **`narrowing.install` gained `once_per_run`** (default `True`, A89's behaviour unchanged) so an
   optimisation does not run the per-run nodes after every evaluation. Reversal: remove the
   keyword and the early return; the alternative would have been a second copy of A89's module.
3. **The census arm is chosen by loop shape** (`B0 → A0`, `B2 → A2`) rather than a census taken on
   the optimisation arms' own evaluations. Reversal: run `narrowed_evaluate.py --census` on `B0` /
   `B2` records and re-derive; V5 item 6 already lists a census over an optimisation's evaluations
   as a prerequisite of option 2, and §4.8 item 6 is this task's evidence toward it.
4. **The lifted file is derived, not copied**, with V4's stage into this task's runs directory
   (`campaign.derived_input_dir = runs/tolerance_phase_b/input_files`). Reversal: none needed —
   the digest gate makes it the campaign's bytes.
5. **Six records were discarded and re-made so every record stamps a clean tree.** The first
   five (nof `B0` census, made before the scripts were committed, `9cfb5687` dirty) and one
   made while a renderer edit was briefly in the working tree (nof `B2` census seed 0, `4abdc165`
   dirty; re-made at `fd1bbdaf`, where the child code is identical). The discarded runs had
   matched the campaign's evaluation counts exactly; the re-made ones are what the tables read.
   Reversal: none; the stamp survey (T1's `tree` column, §3) is the check.
6. **Run kind `smoke`**, as A89: outside every V4 tally. Reversal: none; a `campaign` kind would
   be refused by the pool for an overridden arm anyway.
7. **T7's listing floor of 1e-12** (four decades under τ), to name what a loop leaves not at the
   exact fixed point. Reversal: `RESIDUAL_LISTING_FLOOR`.

## 6. Limits

- **Five seeds per configuration** of the campaign's 22 / 11 / 22, chosen by rule. "The path is
  unchanged" holds over 30 runs on the pulsed configurations and is a statement about those
  seeds; st's one failure in five `B2` census runs is a count, not a rate — the campaign's own
  st `B2` failed 1 of 25 — and a reliability comparison (V5 item 3) needs the full seed set.
- **`B2` whole-`y` at 1e-8 was not run** (the brief's third variant is `B0` only), so on
  `st_regression` the set's effect and the tolerance's are separated for the flat arm only.
- **The census sets are A89's**: four displaced evaluation entries per configuration and arm at
  τ = 1e-6, on `A0` / `A2`. Their adequacy on the optimiser's path is evidenced by the 45 exit
  audits (nothing outside the sets at or above τ at exit), not by a census over optimisation
  evaluations, and an exit audit sees the last evaluation only.
- **Not V4 numbers.** Run kind `smoke`; the campaign's records were read from the relocated copy
  (`A90_runs/`, `tree_git_head 57dc0c14`, arm names translated by `records.read`).
- **Timings are context**: one run each, another task on the machine.
- **One record at a later commit** (`fd1bbdaf`) than the other 44 (`4abdc165`); the two differ
  in the summariser's table renderer only (`git diff 4abdc165 fd1bbdaf`).

## 7. Proposals (the user's to rule)

- **(a)** V5 item 6 as ruled stands on the pulsed configurations: the census set at τ = 1e-8 is
  a control the optimiser cannot tell from V4's, at exact fixed points, within 5 % of V4's cost;
  and the partitioned arm's per-evaluation ratio at matched accuracy is 0.48–0.51 — the V5 plan
  should expect that, not V4's 0.61–0.62.
- **(b)** `st_regression` needs a pre-declared expectation that the trajectory term is *not*
  neutral under the new rule, and two cheap measurements before the plan fixes the rule for it:
  `B2` whole-`y` at 1e-8 (does the partitioned arm's path lengthen under the tolerance alone?)
  and the `B2` census arm at 1e-9 and 1e-10 (does the path return to the campaign's as the loops
  approach exact fixed points?). Both are one `--variant` each in `run_tolerance_phase_b.py`.
- **(c)** Consider, for the partitioned arm, one further sweep of a block's non-census outputs
  after its loop converges — `tlvpmw`'s 2.4e-10 is the shape of the lag — as a measured
  alternative, not a rule; on the pulsed configurations nothing was lagging.
- **(d)** Item 6's prerequisite (2), a census over an optimisation's evaluations: `narrowing`'s
  pass log can record, per evaluation, the whole-`y` residual outside the test set at every stop;
  45 exit audits are the first evidence, a per-evaluation audit would close it.

## 8. Change log

- 2026-09-29 — opened; scripts committed at `4abdc165`; lift stage PASS on both pulsed
  configurations; matrix launched (45 optimisations, serial).
- 2026-09-29 — matrix complete, all 45 records `status ok`; one record re-made for a clean stamp
  (`fd1bbdaf`); renderer tidy (`fd1bbdaf`) and T7 (`002a4508`) committed; results and verdict
  written.

## 9. Orchestrator's critical assessment (protocol §5) — 2026-09-29

**Verdict: merge.** The last prerequisite of V5 list item 6 is measured; its answer is split by
configuration, and the split is a finding the V5 plan must carry. Verified by different roads:

- **Every record read against its campaign record** (45 `metrics.json` under the task's records against
  `A90_runs/campaign/optimisation`, arm `B3` for today's `B2`; a five-line read, not the summariser). On the
  pulsed configurations: solver iterations and evaluations identical on 30 of 30 pairs (the retried lad seed 1
  at 9 240 included); the paired relative `norm_objf` difference at most 5.3e-13; solve-phase node calls per
  evaluation 83.2 / 83.3–83.8 (`B0` whole-`y` 1e-8) against the campaign's 69.0 / 70.0–70.9, 72.2 / 72.0–72.2
  (`B0` census) and 34.8 / 35.2 (`B2` census) against 42.5 / 43.3 — the report's +20 %, +2–5 %, −18 %. On
  `st_regression`: iterations 62/43/18/20 against 53/21/18/20 (`B0` whole-`y`), 41/38/18/12 against 53/21/18/20
  (`B0` census), 40/100/66/40/42 against 10/59/39/18/20 (`B2` census); seed 1 `B2` census `ifail` 2, 15 750
  evaluations, 1.3e-3 off the campaign's optimum. Stamps: 44 at `4abdc165`, one at `fd1bbdaf` (renderer only),
  none dirty. No tracked change under the V4 folder (diff empty).
- **A89's tolerance ladder re-read** (`tolerance.json`) for the reason st behaves differently. Under the
  census set at 1e-8 the st control's objective error is 4.9e-11 relative with a gradient error of 1.2e-8,
  where the whole-`y` control reads 0.0 at every τ from 1e-5 down; only at 1e-10 does the census set read 0.0 on
  st. On the pulsed configurations the census set reads 0.0 objective error from 1e-6 (lad) and at every τ (nof).
  So the rule's bound (function error ≤ h³) is met on st at 1e-8 by its own definition, but st is the one
  configuration where the census-set loop leaves a nonzero objective residual at that τ, and st's optimiser
  is the fragile one already in V4 (`BR → B0` moved its path, 31.2 → 25.1 iterations). That is the likeliest
  mechanism for the trajectory change, and it is testable: the τ ladder the report proposes (§7 (b)).

**What this settles for the V5 plan.** The ruled control is safe on the pulsed configurations: the same path,
the same optimum, exact fixed points, cost within 5 % of V4's control, and the partitioned arm's per-evaluation
ratio at matched accuracy is 0.48–0.51 — V4's whole-`y` test at 1e-6 charged the partitioned arm for sweeps
its blocks did not need, and the plan's expected reading (§6) is updated to that. On `st_regression` the
trajectory term is not neutral under the rule at 1e-8 and the plan must pre-declare it so; the user has ruled
(Q6, D36's note) that the tolerance rule stands and a lost start is a result. Before the plan fixes st's
declaration, the two cheap measurements of §7 (b) are worth their twenty runs: `B2` whole-`y` at 1e-8 on st
(tolerance alone, partitioned arm) and the `B2` census arm at 1e-9 / 1e-10 / 1e-12 on st (does the path return
as the objective residual goes to 0.0?). Dispatched as **A96 (st-trajectory-ladder)**. Proposal §7 (c) (an
extra sweep of non-census outputs) is not taken up: `tlvpmw` at 2.4e-10 is below τ and nothing in a loop reads
it. Proposal §7 (d) is discharged by A92's whole-run census.

**Where the report overstates.** "V4's whole-`y` 1e-6 test was, by its lag, the more stable control there" —
V4's `B0` on st also moved the path against `BR` (25.1 against 31.2 iterations); the comparison A93 can make is
against V4's control, not against a neutral one. And "the census set … takes 18–19 % off the partitioned
arm's per-evaluation cost" is against V4's `B2` at whole-`y` 1e-6, i.e. at a *different* achieved accuracy;
the matched-accuracy statement is the ρ = 0.48–0.51 one.

**Not done here.** The exit-audit recount (§4.5) is taken from the report; the pairing check (hex of the
displaced design vector) likewise — both are the summariser's, committed and named.