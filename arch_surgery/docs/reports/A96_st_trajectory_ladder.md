# A96 (st-trajectory-ladder) — does `st_regression`'s path return as the loops' tolerance tightens?

> **Document status** — **OPEN.** Task A96 (st-trajectory-ladder), 2026-09-29, on branch
> `A96-st-trajectory-ladder`, worktree `.claude/worktrees/A96-st-trajectory-ladder`, base `0635dca2`
> (= `architecture_surgery` after the A93 (tolerance-phase-b) merge). Follow-up to A93's st finding
> (its §9, the orchestrator's assessment, states the hypothesis tested here). Exploratory: **not** a V4
> result — V4's campaign, harness and report are untouched and nothing was written to the V4 or V5
> folder. Script: `arch_surgery/coupling_subset_trial/run_tolerance_phase_b.py --ladder` (A93's
> script, extended; A93's own variants, records and summary untouched) at **`6a51108b`**, the commit
> every run was made at and the commit the summariser's tables were printed at (no script change
> after it). Records under `arch_surgery/idf_probe/runs/st_trajectory_ladder/` (untracked; relocated
> at retirement). The campaign's records (`A90_runs/campaign/optimisation/st_regression/`, its `B3`
> = today's `B2`) and A93's (`A93_runs/tolerance_phase_b/st_regression/`) were read, never written,
> in the main checkout.

## 1. Verdict

**st's path change is a set effect on top of st's own fragility, not a tolerance effect; the set
effect resolves as τ tightens; and the failure mode A93 found on seed 1 is cured only at τ = 1e-12.**
Twenty-five optimisations on `st_regression`, five seeds, compared with the campaign's records
(whole-`y` 1e-6), A93's (census and whole-`y` at 1e-8) and each other (§4, Tables L1–L9):

- **The tolerance alone does not lengthen the partitioned arm's path.** `B2` whole-`y` at 1e-8
  takes the campaign's exact path (same iterations per attempt, same evaluations) on **3 of 5**
  seeds (0, 3, 4) and is within one iteration on the other two — seed 1: 58 iterations / 3 450
  evaluations against the campaign's 59 / 3 510; seed 2: 40 / 2 370 against 39 / 2 310 — and
  reaches the campaign's optimum on all five (`|Δ norm_objf|` ≤ 1.1e-10 relative). By the
  iteration-per-attempt comparison **seeds 1 and 2 are *not* the campaign's path**; they are a
  path of nearly the same length to the same optimum. This is exactly what the flat arm did under
  the tolerance alone in A93 (`B0` whole-`y` 1e-8: seeds 0, 3, 4 equal; 1, 2 not). A93's
  `B2` census at 1e-8 — 0 of 5 equal, evaluations ×1.7 to ×4.2, one failure — was therefore the
  **set's** doing at that τ, not the tolerance's.
- **The set effect fades as τ tightens, and the path returns where A89's objective residual
  reads 0.0.** `B2` census: **0/5** equal at 1e-8 (A93) → **2/5** at 1e-9 (seeds 3, 4; seed 0 one
  iteration over, 11 / 630 against 10 / 570) → **3/5** at 1e-10 (0, 3, 4) → **3/5** at 1e-12
  (0, 3, 4). `B0` census: 2/5 at 1e-8 (A93; seed 4 had shortened to 12 iterations) → **3/5** at
  1e-10 (0, 3, 4; seed 4 back at 20 / 1 170). A89's evaluation-phase ladder (L1) reads the census
  set's objective relative error on st at 4.9e-11 at 1e-8 and 1e-9 and **0.0 from 1e-10** — the
  rung at which both census arms first reproduce the path of the whole-`y` test at 1e-8, seed for
  seed. So on the seeds whose path returns at all, "objective residual 0.0" and "path returns"
  coincide.
- **Seeds 1 and 2 are the campaign's path in no variant of either arm** — not under the tolerance
  alone, not under the set at any τ, not in A93, not here (10 variants × 2 seeds: 0 of 20 equal).
  Their optimum is the campaign's on every accepted run except the two named next, and their
  lengths move both ways (seed 2 `B2`: 39 campaign, 66 / 43 / 46 / 41 / 40 on the five variants;
  seed 1 `B0`: 53 campaign, 62 / 41 / 58). That is st's fragility, present in V4 already (its
  own `B0` seed 2 needed a retry, 27 + 21 iterations, where its `B2` took 39) and not a property
  of the loop's test.
- **Seed 1, the partitioned census arm, changes basin at 1e-8, 1e-9 and 1e-10 and converges to
  the campaign's optimum only at 1e-12.** Seed 1's campaign optimum is a different local optimum
  from the other four seeds' (`norm_objf` −16.80891 against −16.58858). Under the census set at
  1e-8 (A93) the arm hit the 100-iteration cap on attempts 1 and 3 and failed at −16.83087;
  **at 1e-9 and 1e-10 it converges** (`ifail = 1`) — but after hitting the cap on attempt 1 and
  retrying at `epsfcn × 10` (1e-9: 100 + 61 iterations, 9 630 evaluations) or `× 10` then `× 0.1`
  (1e-10: 100 + 64 + 62, 13 560) — **in a different basin**: −16.59657 at 1e-9 (1.3e-2 relative
  above the campaign's) and −16.83087 at 1e-10 (1.3e-3 relative *below* it, feasible, `sqsumsq`
  4.4e-12 — the value the 1e-8 failure had been heading for). Both are "accepted optima" by V4's
  status rule and both violate V4's same-optimum floor (1e-6): a path that ends at a different
  optimum, not the same optimum by a longer path. **At 1e-12** — the rung where A89 reads the
  constraint error 0.0 as well — seed 1 converges in one attempt, 55 iterations / 3 270
  evaluations, to the campaign's optimum (3.5e-11). `B2` whole-`y` at 1e-8 converges there too
  (58 / 3 450, 1.1e-10).
- **Cost.** Per evaluation, against the campaign's own arm at whole-`y` 1e-6: `B2` census
  **0.896 / 0.917 / 0.971** at 1e-9 / 1e-10 / 1e-12 (A93's 0.839 at 1e-8; `M2` rises from 2.62 to
  2.98 / 3.16 / 3.67 sweeps per solve as τ tightens); `B2` whole-`y` 1e-8 **1.201** (the same
  +20 % the flat arm paid in A93); `B0` census 1e-10 **1.086** (A93's 0.920 at 1e-8, 1.179
  whole-`y`). The census pair at 1e-10, `B2 / B0`: **ρ = 0.460** pooled (per seed 0.458–0.468),
  ε median 1.000 [1.000, 3.930] — the one outlier seed 1 — so R is 0.46 on four seeds and 1.01
  pooled. A93's census pair at 1e-8 had ρ = 0.508 and the campaign's 0.545.
- **The exit audit holds at each run's own τ in all 25** (0 components at or above τ on the
  governing statistic; L6), and from 1e-9 down the census loops leave **nothing** at or above
  1e-12 at exit — `heat_transport.tlvpmw`'s 2.4e-10 lag at 1e-8 (A93 T7) is gone at 1e-9, where
  the path is still 2 of 5. The lag was not the mechanism.

**What this means for V5 on `st_regression`.** At the ruled τ = 1e-8 the census set is not a
neutral control for the partitioned arm on st: it lengthens every seed's path and, on one seed in
five, sends the optimiser to another basin. The path returns on the three stable seeds at 1e-10, and
seed 1's basin holds only at 1e-12. Proposals in §7: declare seeds 1 and 2 as st's fragile seeds
(neither arm's path is the campaign's under any loop change), state the expected reading of the
trajectory term on st at each τ from this ladder, and — if st's partitioned arm is to be run at
matched accuracy — run it at 1e-12 on st, where the census loops are exact (A89: objective and
constraint error 0.0) and the per-evaluation cost is 0.97 of V4's partitioned arm.

**Time (context only).** 25 runs, 2 108 s of recorded `wall_s` (L9); the first run of the matrix
carried numba's compilation into a fresh cache directory; another task shared the machine, and for
part of the window a second copy of this run (§3, the double launch) did too.

## 2. Question

A93 (tolerance-phase-b) ran the census test set (ruling D32: converge each coupling-state loop on
the census-measured read-before-write set) at the derived tolerance τ = 1e-8 in whole optimisations.
On the two pulsed configurations the optimiser's path was the campaign's to the last evaluation in
30 of 30 runs. On `st_regression` alone the path moved: the flat control `B0` shortened on 3 of 5
seeds (−12, −10, −8 iterations) and the partitioned arm `B2` lengthened on all 5 (iterations
40 / 100+62+100 / 66 / 40 / 42 against the campaign's 10 / 59 / 39 / 18 / 20; evaluations ×1.7 to
×4.2), seed 1 failing at the iteration cap (`ifail = 2` on attempts 1 and 3). The tolerance alone
(`B0` whole-`y` at 1e-8) already moved `B0`'s path on 2 of 5 seeds.

The hypothesis (A93 §9): st is the one configuration where the census-set loop leaves a nonzero
objective residual at 1e-8 — A89's evaluation-phase ladder (`tolerance.json`) reads the census-set
control's objective relative error on st at **4.9e-11 at τ = 1e-8 and 1e-9, and 0.0 only from
1e-10**, where the whole-`y` control reads 0.0 at every τ — and st's optimiser is fragile enough
(V4's own `BR → B0` moved its path) that a nonzero residual changes its finite-difference decisions.
Two questions, each one variant of A93's script:

1. **Does the path return to the campaign's as τ tightens?** `B2` census at 1e-9, 1e-10 and 1e-12
   (the rungs where A89's objective error is still 4.9e-11, first 0.0, and 0.0 with the constraint
   error 0.0 too), and `B0` census at 1e-10 as the flat control at the first 0.0 rung.
2. **Does the tolerance alone move `B2`'s path?** `B2` whole-`y` at 1e-8 — the partitioned arm under
   V4's own test set, at A93's tolerance.

Twenty-five optimisations, `st_regression` only, A93's five seeds (0–4), serial.

## 3. Method

**Runs.** Each run is V4's own optimisation child (`harness/child/optimise.py`) executed unchanged
in a fresh subprocess with its own working directory, through A93's
`arch_surgery/coupling_subset_trial/narrowed_optimise.py`, which installs `narrowing.install`
(the loops' test set: `full` = V4's whole-`y` test; `rbw` = the census set of `rbw_sets.json`,
`A0`'s `FLAT` for `B0`, `A2`'s `M1` / `M2` / `M3` / `PULSE` for `B2`; `once_per_run=False`) before
the child runs. Nothing in the V4 folder is edited. **The tolerance** is the campaign's `tau`: the
script builds one V4 campaign per rung (`campaign(tau, runs=LADDER_RUNS)`), and V4's pool composes
`PROCESS_ARCH_TAU` and `--tau` from it, so each record's `resolved_switches` carries
`module_solve.TAU` at the rung's value and `narrowed_optimise.json` the same (L2, "τ of record").
`PYTHONPATH` is asserted equal to this worktree's V4 copy of the tree (`camp.tree`; trap T6) before
every launch; the child asserts `process.__file__` under that exact tree and stamps it — every one
of the 25 records has `process_file` under this worktree's V4 copy, `tree_git_head 6a51108b`, no
tracked modification (L2). `NUMBA_CACHE_DIR` is set under the ladder's runs directory for every
launch (issue I-31: V4's pool sets none). One PROCESS process at a time (`workers = 1`) by
construction of the script; see the next paragraph for the interval where that did not hold.

**How the 25 records were made (a resume and a double launch).** The matrix was launched once,
serially, at 17:39 (`run.log`). After its eleventh record the orchestrator read an empty `ps` inside
the sandbox as a dead run (the sandbox gives every Bash call its own PID namespace, trap T8; the
run was alive) and had a second copy launched at 18:03 with `nohup … &`, which the sandbox ends with
the Bash call that started it (now trap T19) — but not before it had opened `B2_rbw_1e-10/seed001`
while the original was in the same directory. The original ran to completion (25 result lines,
`exit 0`, 18:20). To make the population provably clean the simplest rule was applied: **every
record directory whose `command.json` is later than 18:03:00 was deleted** — the 14 from
`B2_rbw_1e-10/seed001` onward, whichever parent made them — and **the 11 made before 18:03 were
kept** (`B2_full_1e-08` seeds 0–4, `B2_rbw_1e-09` seeds 0–4, `B2_rbw_1e-10` seed 0; `command.json`
17:39:15–17:55:35). A third launch at 18:23 was `nohup`'d too and died the same way after opening
`B2_rbw_1e-10/seed001` (deleted again, no `metrics.json`). The 14 missing records were then made by
**one run started at 18:33 through the Bash tool's background mode, after both earlier processes
had ended** (`run_relaunch.log`: 11 `kept`, 14 result lines, `exit 0`; `command.json`
18:33:47–18:53:44). The script's resume is its `metrics.json` skip only (a record is kept when the
file exists), so the 11 kept records are the originals. Every record, kept or re-made, stamps the
same clean tree at `6a51108b`. Timings in L2/L9 are context: two parents shared the machine for part
of the 18:03–18:20 window, on top of A94.

**Not narrowed, as in A93:** the seed's displacement of the design vector (the V4 child's own hook,
so a run pairs with the campaign's record of the same seed — verified hex for hex against the
campaign's `perturbation.json`, 14 of 14 iteration variables on every displaced run, L2), the
optimiser, the exit audit (every component of `y` at the entry to the output path) and the output
path. `st_regression` is steady state: no arm reads a lifted input file (`input_files.assert_lifted`
refuses one), so A93's `--lift` stage is not a ladder stage and the script refuses `--lift --ladder`.

**Matrix.** Five variants × five seeds, the seeds A93's rule gives on st (the first five of the
campaign's every-arm-converged set: 0, 1, 2, 3, 4):

| variant | arm | test set | τ | what it separates |
|---|---|---|---|---|
| `B2_full_1e-08` | B2 | whole `y` | 1e-8 | the tolerance alone, on the partitioned arm |
| `B2_rbw_1e-09` | B2 | census | 1e-9 | A89's objective error still 4.9e-11 |
| `B2_rbw_1e-10` | B2 | census | 1e-10 | A89's objective error first 0.0; constraint error 3.1e-12 |
| `B2_rbw_1e-12` | B2 | census | 1e-12 | A89's objective and constraint error both 0.0 |
| `B0_rbw_1e-10` | B0 | census | 1e-10 | the flat control at the first 0.0 rung |

**Comparison** (`run_tolerance_phase_b.py --summarise --ladder`, no PROCESS run). Per seed, ten
members: the campaign's `B0` and `B2` (whole-`y` 1e-6), A93's `B0_full`, `B0_rbw` and `B2_rbw`
(1e-8), and the five above. Every non-campaign member is compared with **the campaign's record of
its arm** and with **A93's census record of its arm at 1e-8** (`B0_rbw` / `B2_rbw`): status and
`ifail` (per attempt), attempts and retries, iterations per attempt and summed over attempts (V4's
construction), evaluations `C` (`sweeps_per_eval.n_evaluations`), solve-phase node calls `N` and
`N / C`, `norm_objf` as the paired relative difference against V4's same-optimum floor 1e-6, and
**path equality** — defined here as *the same iterations per attempt and the same number of
evaluations* — which is the count the verdict is stated in (an evaluation count alone can agree by
coincidence; the iteration-per-attempt list is the test). The exit audit is recounted from each
record's `audit_residual.json` at 1e-6, 1e-8 and the run's own τ (whole `y` for `B0`; V4's
restricted statistic for `B2`, the per-run deferred nodes' writes excluded), and every restricted
component at or above 1e-12 is named with its set memberships (A93's T7). `R = ρ × ε` is pooled over
the seeds where both members are accepted optima. A89's ladder rows for st (`A0_rbw`, `A2_rbw`,
`A0_full`: objective relative error, constraint absolute error, objective-gradient relative error)
are printed beside the path result at each τ (L1).

## 4. Results

Every table below is printed by `arch_surgery/coupling_subset_trial/run_tolerance_phase_b.py
--summarise --ladder` at `6a51108b` over the 25 ladder records (all at `6a51108b`), A93's 15 st
records (`4abdc165`) and the campaign's 10 (`57dc0c14`). Members: `B0_campaign` / `B2_campaign` =
whole-`y` 1e-6 (campaign); `B0_full` = `B0` whole-`y` 1e-8 (A93); `B0_rbw` / `B2_rbw` = census
1e-8 (A93); `B0_rbw_1e-10`, `B2_full_1e-08`, `B2_rbw_1e-09`, `B2_rbw_1e-10`, `B2_rbw_1e-12` = this
task's. "Path = campaign" is the same iterations per attempt and the same evaluations.

### 4.1 A89's ladder beside the path result

**L1.** *One row per τ of the ladder. Columns 2–9: A89's evaluation-phase ladder on st
(`tolerance.json`; 29 stencil points at four displaced entries) for the census-set flat control
`A0_rbw`, the census-set partitioned arm `A2_rbw` and the whole-`y` control `A0_full` — objective
relative error and constraint absolute error against the ladder's tightest τ, and the
objective-gradient relative error. Columns 10–13: the number of seeds (of 5 run) on which the
optimisation arm's path equals the campaign's under that test set at that τ, with the member's
label; "(reference)" is the campaign's own τ.*

| τ | A0 census objf rel err | A0 census conf abs err | A0 census grad objf rel err | A2 census objf rel err | A2 census conf abs err | A2 census grad objf rel err | A0 whole-y objf rel err | A0 whole-y conf abs err | B0 census: path = campaign | B2 census: path = campaign | B0 whole-y: path = campaign | B2 whole-y: path = campaign |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1e-06 | 1.2e-08 | 1.0e-08 | 4.4e-06 | 1.2e-08 | 1.0e-08 | 4.4e-06 | 0.0e+00 | 2.6e-10 | (reference) | (reference) | (reference) | (reference) |
| 1e-08 | 4.9e-11 | 1.8e-11 | 1.2e-08 | 4.9e-11 | 1.8e-11 | 1.2e-08 | 0.0e+00 | 2.8e-12 | 2/5 (`B0_rbw`) | 0/5 (`B2_rbw`) | 3/5 (`B0_full`) | 3/5 (`B2_full_1e-08`) |
| 1e-09 | 4.9e-11 | 1.0e-11 | 1.2e-08 | 4.9e-11 | 1.0e-11 | 1.2e-08 | 0.0e+00 | 2.6e-12 | — | 2/5 (`B2_rbw_1e-09`) | — | — |
| 1e-10 | 0.0e+00 | 2.2e-12 | 0.0e+00 | 0.0e+00 | 3.1e-12 | 0.0e+00 | 0.0e+00 | 2.6e-12 | 3/5 (`B0_rbw_1e-10`) | 3/5 (`B2_rbw_1e-10`) | — | — |
| 1e-12 | 0.0e+00 | 0.0e+00 | 0.0e+00 | 0.0e+00 | 0.0e+00 | 0.0e+00 | 0.0e+00 | 0.0e+00 | — | 3/5 (`B2_rbw_1e-12`) | — | — |

### 4.2 Pairing, tree and outcome

**L2.** *One row per ladder run (25). `ifail per attempt` is V4's attempt accounting (2 = iteration
cap, 5 = VMCON's line-search failure, 1 = converged); `displaced x identical (hex)`: iteration
variables whose displacement factor and clamped scaled start equal the campaign record's bit for
bit (14 on st; seed 0 is undisplaced in both); `tree` / `tree dirty` / `process under this tree`:
the record's stamp of the commit, of tracked modifications, and whether `process.__file__` is under
this worktree's V4 copy; `test set installed` from `narrowing.json`; `τ of record` from the record's
`campaign_tau`. Wall clock is context.*

| seed | run | status | ifail | attempts | ifail per attempt | displaced x identical (hex) | paired | tree | tree dirty | process under this tree | test set installed | τ of record | wall s (context) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | B0_rbw_1e-10 | ok | 1 | 1 | 1 | n/a (seed 0) | yes | 6a51108b | no | yes | rbw | 1e-10 | 18 |
| 0 | B2_full_1e-08 | ok | 1 | 1 | 1 | n/a (seed 0) | yes | 6a51108b | no | yes | full | 1e-08 | 72 |
| 0 | B2_rbw_1e-09 | ok | 1 | 1 | 1 | n/a (seed 0) | yes | 6a51108b | no | yes | rbw | 1e-09 | 25 |
| 0 | B2_rbw_1e-10 | ok | 1 | 1 | 1 | n/a (seed 0) | yes | 6a51108b | no | yes | rbw | 1e-10 | 24 |
| 0 | B2_rbw_1e-12 | ok | 1 | 1 | 1 | n/a (seed 0) | yes | 6a51108b | no | yes | rbw | 1e-12 | 20 |
| 1 | B0_rbw_1e-10 | ok | 1 | 1 | 1 | 14/14 | yes | 6a51108b | no | yes | rbw | 1e-10 | 99 |
| 1 | B2_full_1e-08 | ok | 1 | 1 | 1 | 14/14 | yes | 6a51108b | no | yes | full | 1e-08 | 173 |
| 1 | B2_rbw_1e-09 | ok | 1 | 2 | 2/1 | 14/14 | yes | 6a51108b | no | yes | rbw | 1e-09 | 308 |
| 1 | B2_rbw_1e-10 | ok | 1 | 3 | 2/5/1 | 14/14 | yes | 6a51108b | no | yes | rbw | 1e-10 | 441 |
| 1 | B2_rbw_1e-12 | ok | 1 | 1 | 1 | 14/14 | yes | 6a51108b | no | yes | rbw | 1e-12 | 114 |
| 2 | B0_rbw_1e-10 | ok | 1 | 1 | 1 | 14/14 | yes | 6a51108b | no | yes | rbw | 1e-10 | 71 |
| 2 | B2_full_1e-08 | ok | 1 | 1 | 1 | 14/14 | yes | 6a51108b | no | yes | full | 1e-08 | 101 |
| 2 | B2_rbw_1e-09 | ok | 1 | 1 | 1 | 14/14 | yes | 6a51108b | no | yes | rbw | 1e-09 | 73 |
| 2 | B2_rbw_1e-10 | ok | 1 | 2 | 5/1 | 14/14 | yes | 6a51108b | no | yes | rbw | 1e-10 | 94 |
| 2 | B2_rbw_1e-12 | ok | 1 | 1 | 1 | 14/14 | yes | 6a51108b | no | yes | rbw | 1e-12 | 86 |
| 3 | B0_rbw_1e-10 | ok | 1 | 1 | 1 | 14/14 | yes | 6a51108b | no | yes | rbw | 1e-10 | 30 |
| 3 | B2_full_1e-08 | ok | 1 | 1 | 1 | 14/14 | yes | 6a51108b | no | yes | full | 1e-08 | 45 |
| 3 | B2_rbw_1e-09 | ok | 1 | 1 | 1 | 14/14 | yes | 6a51108b | no | yes | rbw | 1e-09 | 31 |
| 3 | B2_rbw_1e-10 | ok | 1 | 1 | 1 | 14/14 | yes | 6a51108b | no | yes | rbw | 1e-10 | 36 |
| 3 | B2_rbw_1e-12 | ok | 1 | 1 | 1 | 14/14 | yes | 6a51108b | no | yes | rbw | 1e-12 | 37 |
| 4 | B0_rbw_1e-10 | ok | 1 | 1 | 1 | 14/14 | yes | 6a51108b | no | yes | rbw | 1e-10 | 35 |
| 4 | B2_full_1e-08 | ok | 1 | 1 | 1 | 14/14 | yes | 6a51108b | no | yes | full | 1e-08 | 54 |
| 4 | B2_rbw_1e-09 | ok | 1 | 1 | 1 | 14/14 | yes | 6a51108b | no | yes | rbw | 1e-09 | 37 |
| 4 | B2_rbw_1e-10 | ok | 1 | 1 | 1 | 14/14 | yes | 6a51108b | no | yes | rbw | 1e-10 | 39 |
| 4 | B2_rbw_1e-12 | ok | 1 | 1 | 1 | 14/14 | yes | 6a51108b | no | yes | rbw | 1e-12 | 43 |

### 4.3 The optimiser's path and its optimum

**L3.** *Ten rows per seed, one per member. `iterations Σ` is summed over attempts; `C` is
evaluations of the model set; `N` solve-phase node calls; `|Δf|/max` the paired relative difference
of `norm_objf` (floor 1e-6); `Δ iterations Σ`, `C ratio` and `path =` against the campaign's record
of the same arm and seed, then against A93's census record of the same arm at 1e-8 (`B0_rbw` /
`B2_rbw`; the reference rows themselves carry no such columns).*

| seed | run | ifail | attempts | iterations per attempt | iterations Σ | evaluations C | node calls N | N/C | sweeps/eval mean | norm_objf | |Δf|/max vs campaign | Δ iterations Σ vs campaign | C ratio vs campaign | path = campaign | |Δf|/max vs A93 1e-8 | Δ iterations Σ vs A93 1e-8 | C ratio vs A93 1e-8 | path = A93 1e-8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | B0_campaign | 1 | 1 | 10 | 10 | 570 | 42756 | 75.0 | 3.57 | -16.5885765078 | — | — | — | — | — | — | — | — |
| 0 | B0_full | 1 | 1 | 10 | 10 | 570 | 51366 | 90.1 | 4.29 | -16.5885765078 | 1.4e-14 | 0 | 1.0000 | yes | 5.0e-13 | 0 | 1.0000 | yes |
| 0 | B0_rbw | 1 | 1 | 10 | 10 | 570 | 38514 | 67.6 | 3.22 | -16.5885765078 | 4.8e-13 | 0 | 1.0000 | yes | — | — | — | — |
| 0 | B0_rbw_1e-10 | 1 | 1 | 10 | 10 | 570 | 45801 | 80.4 | 3.83 | -16.5885765078 | 1.4e-14 | 0 | 1.0000 | yes | 5.0e-13 | 0 | 1.0000 | yes |
| 0 | B2_campaign | 1 | 1 | 10 | 10 | 570 | 23505 | 41.2 | 9.23 | -16.5885765078 | — | — | — | — | — | — | — | — |
| 0 | B2_rbw | 1 | 1 | 40 | 40 | 2370 | 80974 | 34.2 | 8.30 | -16.588576508 | 1.5e-11 | 30 | 4.1579 | no | — | — | — | — |
| 0 | B2_full_1e-08 | 1 | 1 | 10 | 10 | 570 | 27712 | 48.6 | 10.43 | -16.5885765078 | 1.9e-14 | 0 | 1.0000 | yes | 1.5e-11 | -30 | 0.2405 | no |
| 0 | B2_rbw_1e-09 | 1 | 1 | 11 | 11 | 630 | 22775 | 36.2 | 8.86 | -16.5885765082 | 2.5e-11 | 1 | 1.1053 | no | 1.0e-11 | -29 | 0.2658 | no |
| 0 | B2_rbw_1e-10 | 1 | 1 | 10 | 10 | 570 | 21038 | 36.9 | 9.15 | -16.5885765078 | 2.0e-14 | 0 | 1.0000 | yes | 1.5e-11 | -30 | 0.2405 | no |
| 0 | B2_rbw_1e-12 | 1 | 1 | 10 | 10 | 570 | 22092 | 38.8 | 9.78 | -16.5885765078 | 2.0e-14 | 0 | 1.0000 | yes | 1.5e-11 | -30 | 0.2405 | no |
| 1 | B0_campaign | 1 | 1 | 53 | 53 | 3150 | 226002 | 71.7 | 3.42 | -16.8089052843 | — | — | — | — | — | — | — | — |
| 1 | B0_full | 1 | 1 | 62 | 62 | 3690 | 316512 | 85.8 | 4.08 | -16.8089053908 | 6.3e-09 | 9 | 1.1714 | no | 9.4e-11 | 21 | 1.5185 | no |
| 1 | B0_rbw | 1 | 1 | 41 | 41 | 2430 | 162582 | 66.9 | 3.19 | -16.8089053892 | 6.2e-09 | -12 | 0.7714 | no | — | — | — | — |
| 1 | B0_rbw_1e-10 | 1 | 1 | 58 | 58 | 3450 | 267414 | 77.5 | 3.69 | -16.8089053915 | 6.4e-09 | 5 | 1.0952 | no | 1.3e-10 | 17 | 1.4198 | no |
| 1 | B2_campaign | 1 | 1 | 59 | 59 | 3510 | 134560 | 38.3 | 8.85 | -16.8089053904 | — | — | — | — | — | — | — | — |
| 1 | B2_rbw | 2 | 3 | 100/62/100 | 262 | 15750 | 531034 | 33.7 | 8.23 | -16.8308736126 | 1.3e-03 | 203 | 4.4872 | no | — | — | — | — |
| 1 | B2_full_1e-08 | 1 | 1 | 58 | 58 | 3450 | 163247 | 47.3 | 10.19 | -16.8089053922 | 1.1e-10 | -1 | 0.9829 | no | 1.3e-03 | -204 | 0.2190 | no |
| 1 | B2_rbw_1e-09 | 1 | 2 | 100/61 | 161 | 9630 | 341592 | 35.5 | 8.69 | -16.5965677939 | 1.3e-02 | 102 | 2.7436 | no | 1.4e-02 | -101 | 0.6114 | no |
| 1 | B2_rbw_1e-10 | 1 | 3 | 100/64/62 | 226 | 13560 | 491963 | 36.3 | 8.93 | -16.8308735829 | 1.3e-03 | 167 | 3.8632 | no | 1.8e-09 | -36 | 0.8610 | no |
| 1 | B2_rbw_1e-12 | 1 | 1 | 55 | 55 | 3270 | 126285 | 38.6 | 9.72 | -16.808905391 | 3.5e-11 | -4 | 0.9316 | no | 1.3e-03 | -207 | 0.2076 | no |
| 2 | B0_campaign | 1 | 2 | 27/21 | 48 | 2880 | 218820 | 76.0 | 3.62 | -16.5885765079 | — | — | — | — | — | — | — | — |
| 2 | B0_full | 1 | 1 | 43 | 43 | 2550 | 218610 | 85.7 | 4.08 | -16.5885765082 | 1.8e-11 | -5 | 0.8854 | no | 2.2e-12 | 5 | 1.1333 | no |
| 2 | B0_rbw | 1 | 1 | 38 | 38 | 2250 | 151746 | 67.4 | 3.21 | -16.5885765082 | 2.0e-11 | -10 | 0.7812 | no | — | — | — | — |
| 2 | B0_rbw_1e-10 | 1 | 1 | 41 | 41 | 2430 | 196539 | 80.9 | 3.85 | -16.5885765082 | 1.7e-11 | -7 | 0.8438 | no | 3.2e-12 | 3 | 1.0800 | no |
| 2 | B2_campaign | 1 | 1 | 39 | 39 | 2310 | 93767 | 40.6 | 9.16 | -16.5885765081 | — | — | — | — | — | — | — | — |
| 2 | B2_rbw | 1 | 1 | 66 | 66 | 3930 | 135183 | 34.4 | 8.35 | -16.5885765081 | 4.1e-12 | 27 | 1.7013 | no | — | — | — | — |
| 2 | B2_full_1e-08 | 1 | 1 | 40 | 40 | 2370 | 113813 | 48.0 | 10.33 | -16.5885765082 | 6.5e-12 | 1 | 1.0260 | no | 2.4e-12 | -26 | 0.6031 | no |
| 2 | B2_rbw_1e-09 | 1 | 1 | 43 | 43 | 2550 | 91602 | 35.9 | 8.77 | -16.5885765082 | 1.0e-11 | 4 | 1.1039 | no | 6.1e-12 | -23 | 0.6489 | no |
| 2 | B2_rbw_1e-10 | 1 | 2 | 25/21 | 46 | 2760 | 103218 | 37.4 | 9.31 | -16.5885765079 | 1.0e-11 | 7 | 1.1948 | no | 1.4e-11 | -20 | 0.7023 | no |
| 2 | B2_rbw_1e-12 | 1 | 1 | 41 | 41 | 2430 | 94058 | 38.7 | 9.76 | -16.588576508 | 4.5e-12 | 2 | 1.0519 | no | 8.6e-12 | -25 | 0.6183 | no |
| 3 | B0_campaign | 1 | 1 | 18 | 18 | 1050 | 76461 | 72.8 | 3.47 | -16.5885765079 | — | — | — | — | — | — | — | — |
| 3 | B0_full | 1 | 1 | 18 | 18 | 1050 | 91812 | 87.4 | 4.16 | -16.5885765079 | 3.6e-14 | 0 | 1.0000 | yes | 3.8e-12 | 0 | 1.0000 | yes |
| 3 | B0_rbw | 1 | 1 | 18 | 18 | 1050 | 70917 | 67.5 | 3.22 | -16.5885765078 | 3.9e-12 | 0 | 1.0000 | yes | — | — | — | — |
| 3 | B0_rbw_1e-10 | 1 | 1 | 18 | 18 | 1050 | 84609 | 80.6 | 3.84 | -16.5885765079 | 3.6e-14 | 0 | 1.0000 | yes | 3.8e-12 | 0 | 1.0000 | yes |
| 3 | B2_campaign | 1 | 1 | 18 | 18 | 1050 | 43204 | 41.1 | 9.23 | -16.5885765079 | — | — | — | — | — | — | — | — |
| 3 | B2_rbw | 1 | 1 | 40 | 40 | 2370 | 81434 | 34.4 | 8.35 | -16.5885765082 | 2.2e-11 | 22 | 2.2571 | no | — | — | — | — |
| 3 | B2_full_1e-08 | 1 | 1 | 18 | 18 | 1050 | 50796 | 48.4 | 10.38 | -16.5885765079 | 3.8e-14 | 0 | 1.0000 | yes | 2.2e-11 | -22 | 0.4430 | no |
| 3 | B2_rbw_1e-09 | 1 | 1 | 18 | 18 | 1050 | 38130 | 36.3 | 8.95 | -16.5885765079 | 1.3e-13 | 0 | 1.0000 | yes | 2.2e-11 | -22 | 0.4430 | no |
| 3 | B2_rbw_1e-10 | 1 | 1 | 18 | 18 | 1050 | 38774 | 36.9 | 9.16 | -16.5885765079 | 3.9e-14 | 0 | 1.0000 | yes | 2.2e-11 | -22 | 0.4430 | no |
| 3 | B2_rbw_1e-12 | 1 | 1 | 18 | 18 | 1050 | 40695 | 38.8 | 9.78 | -16.5885765079 | 3.9e-14 | 0 | 1.0000 | yes | 2.2e-11 | -22 | 0.4430 | no |
| 4 | B0_campaign | 1 | 1 | 20 | 20 | 1170 | 80661 | 68.9 | 3.28 | -16.588576508 | — | — | — | — | — | — | — | — |
| 4 | B0_full | 1 | 1 | 20 | 20 | 1170 | 99687 | 85.2 | 4.06 | -16.588576508 | 2.7e-13 | 0 | 1.0000 | yes | 8.0e-12 | 8 | 1.6957 | no |
| 4 | B0_rbw | 1 | 1 | 12 | 12 | 690 | 46410 | 67.3 | 3.20 | -16.5885765081 | 7.7e-12 | -8 | 0.5897 | no | — | — | — | — |
| 4 | B0_rbw_1e-10 | 1 | 1 | 20 | 20 | 1170 | 93786 | 80.2 | 3.82 | -16.588576508 | 7.9e-13 | 0 | 1.0000 | yes | 6.9e-12 | 8 | 1.6957 | no |
| 4 | B2_campaign | 1 | 1 | 20 | 20 | 1170 | 47985 | 41.0 | 9.16 | -16.588576508 | — | — | — | — | — | — | — | — |
| 4 | B2_rbw | 1 | 1 | 42 | 42 | 2490 | 85081 | 34.2 | 8.30 | -16.5885765082 | 1.4e-11 | 22 | 2.1282 | no | — | — | — | — |
| 4 | B2_full_1e-08 | 1 | 1 | 20 | 20 | 1170 | 56369 | 48.2 | 10.34 | -16.588576508 | 7.0e-13 | 0 | 1.0000 | yes | 1.3e-11 | -22 | 0.4699 | no |
| 4 | B2_rbw_1e-09 | 1 | 1 | 20 | 20 | 1170 | 42338 | 36.2 | 8.89 | -16.588576508 | 7.3e-13 | 0 | 1.0000 | yes | 1.3e-11 | -22 | 0.4699 | no |
| 4 | B2_rbw_1e-10 | 1 | 1 | 20 | 20 | 1170 | 43098 | 36.8 | 9.12 | -16.588576508 | 5.3e-13 | 0 | 1.0000 | yes | 1.3e-11 | -22 | 0.4699 | no |
| 4 | B2_rbw_1e-12 | 1 | 1 | 20 | 20 | 1170 | 45247 | 38.7 | 9.74 | -16.588576508 | 2.5e-13 | 0 | 1.0000 | yes | 1.3e-11 | -22 | 0.4699 | no |

**L4.** *One row per non-campaign member: counts over the five seeds — status `ok`, `ifail = 1`,
accepted optimum (V4's rule: status `ok` and `ifail = 1`), retried (more than one attempt), path
equal to the campaign's, path equal to A93's census record of the arm at 1e-8; iterations Σ and
evaluations by seed (0–4); runs whose `norm_objf` is within V4's same-optimum floor of the
campaign's, and the largest paired difference over the accepted runs; seed 1's outcome; and A89's
row for the matching evaluation-phase variant at the member's τ.*

| run | member | status ok | ifail = 1 | accepted optimum | retried | path = campaign | path = A93 census 1e-8 | iterations Σ by seed | evaluations by seed | |Δf| ≤ 1e-6 vs campaign | max |Δf|/max (accepted) | seed 1 | A89 variant | A89 objf rel err | A89 conf abs err | A89 grad objf rel err |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0_full | B0 whole-y 1e-08 (A93) | 5/5 | 5/5 | 5/5 | 0 | 3/5 | 2/5 (`B0_rbw`) | 10 62 43 18 20 | 570 3690 2550 1050 1170 | 5/5 | 6.3e-09 | ifail 1, it 62, C 3690 | A0_full | 0.0e+00 | 2.8e-12 | 0.0e+00 |
| B0_rbw | B0 census 1e-08 (A93) | 5/5 | 5/5 | 5/5 | 0 | 2/5 | (is the reference) | 10 41 38 18 12 | 570 2430 2250 1050 690 | 5/5 | 6.2e-09 | ifail 1, it 41, C 2430 | A0_rbw | 4.9e-11 | 1.8e-11 | 1.2e-08 |
| B0_rbw_1e-10 | B0 census 1e-10 | 5/5 | 5/5 | 5/5 | 0 | 3/5 | 2/5 (`B0_rbw`) | 10 58 41 18 20 | 570 3450 2430 1050 1170 | 5/5 | 6.4e-09 | ifail 1, it 58, C 3450 | A0_rbw | 0.0e+00 | 2.2e-12 | 0.0e+00 |
| B2_rbw | B2 census 1e-08 (A93) | 5/5 | 4/5 | 4/5 | 1 | 0/5 | (is the reference) | 40 262 66 40 42 | 2370 15750 3930 2370 2490 | 4/5 | 2.2e-11 | ifail 2, it 100/62/100, C 15750 | A2_rbw | 4.9e-11 | 1.8e-11 | 1.2e-08 |
| B2_full_1e-08 | B2 whole-y 1e-08 | 5/5 | 5/5 | 5/5 | 0 | 3/5 | 0/5 (`B2_rbw`) | 10 58 40 18 20 | 570 3450 2370 1050 1170 | 5/5 | 1.1e-10 | ifail 1, it 58, C 3450 | A0_full | 0.0e+00 | 2.8e-12 | 0.0e+00 |
| B2_rbw_1e-09 | B2 census 1e-09 | 5/5 | 5/5 | 5/5 | 1 | 2/5 | 0/5 (`B2_rbw`) | 11 161 43 18 20 | 630 9630 2550 1050 1170 | 4/5 | 1.3e-02 | ifail 1, it 100/61, C 9630 | A2_rbw | 4.9e-11 | 1.0e-11 | 1.2e-08 |
| B2_rbw_1e-10 | B2 census 1e-10 | 5/5 | 5/5 | 5/5 | 2 | 3/5 | 0/5 (`B2_rbw`) | 10 226 46 18 20 | 570 13560 2760 1050 1170 | 4/5 | 1.3e-03 | ifail 1, it 100/64/62, C 13560 | A2_rbw | 0.0e+00 | 3.1e-12 | 0.0e+00 |
| B2_rbw_1e-12 | B2 census 1e-12 | 5/5 | 5/5 | 5/5 | 0 | 3/5 | 0/5 (`B2_rbw`) | 10 55 41 18 20 | 570 3270 2430 1050 1170 | 5/5 | 3.5e-11 | ifail 1, it 55, C 3270 | A2_rbw | 0.0e+00 | 0.0e+00 | 0.0e+00 |

### 4.4 Sweeps per evaluation and per block

**L5.** *Same rows as L3. Sweeps of the loop per evaluation (histogram: sweeps → count of
evaluations); sweeps per solve of each iterated block (`B2`: `M1`, `M2`, `PULSE`, `M3`) or of the
flat block; predicate evaluations and components compared during the solve phase, and their ratio,
the mean test width.*

| seed | run | evaluations | sweeps/eval min/median/mean/max | histogram sweeps:count | sweeps per solve by block | predicate evaluations | components compared | mean test width |
|---|---|---|---|---|---|---|---|---|
| 0 | B0_campaign | 570 | 1/3/3.57/12 | 1:9 2:49 3:272 4:194 5:22 7:1 9:12 10:10 12:1 | FLAT 3.57 | 2036 | 1683772 | 827 |
| 0 | B0_full | 570 | 1/4/4.29/12 | 1:9 2:19 3:248 4:76 5:50 6:143 7:1 8:1 9:4 10:18 12:1 | FLAT 4.29 | 2446 | 2022842 | 827 |
| 0 | B0_rbw | 570 | 1/2/3.22/7 | 1:28 2:260 3:64 4:2 5:212 6:2 7:2 | FLAT 3.22 | 1834 | 133882 | 73 |
| 0 | B0_rbw_1e-10 | 570 | 1/3/3.83/8 | 1:28 2:151 3:172 4:1 5:2 6:193 7:21 8:2 | FLAT 3.83 | 2181 | 159213 | 73 |
| 0 | B2_campaign | 570 | 5/9/9.23/17 | 5:9 6:19 7:13 8:137 9:171 10:116 11:59 12:41 13:1 14:2 15:1 17:1 | M1 2.39, M2 2.40, PULSE 1.00, M3 2.44 | 4119 | 970258 | 236 |
| 0 | B2_rbw | 2370 | 5/8/8.30/15 | 5:118 6:211 7:654 8:404 9:166 10:501 11:306 12:6 13:2 14:1 15:1 | M1 1.78, M2 2.62, PULSE 1.00, M3 1.89 | 14923 | 404580 | 27 |
| 0 | B2_full_1e-08 | 570 | 5/10/10.43/18 | 5:9 6:19 8:36 9:169 10:98 11:21 12:132 13:36 14:40 15:7 16:1 17:1 18:1 | M1 2.53, M2 3.03, PULSE 1.00, M3 2.87 | 4807 | 1124755 | 234 |
| 0 | B2_rbw_1e-09 | 630 | 5/8/8.86/16 | 5:31 6:21 7:146 8:138 9:54 10:45 11:123 12:55 13:14 14:2 16:1 | M1 2.00, M2 2.91, PULSE 1.00, M3 1.95 | 4322 | 118533 | 27 |
| 0 | B2_rbw_1e-10 | 570 | 5/8/9.15/16 | 5:28 6:19 7:113 8:134 9:57 10:1 11:115 12:39 13:59 14:3 15:1 16:1 | M1 2.10, M2 3.09, PULSE 1.00, M3 1.95 | 4073 | 113112 | 28 |
| 0 | B2_rbw_1e-12 | 570 | 5/8/9.78/18 | 5:28 6:19 7:90 8:157 9:57 11:1 12:40 13:94 14:59 15:22 16:2 18:1 | M1 2.14, M2 3.68, PULSE 1.00, M3 1.95 | 4432 | 129272 | 29 |
| 1 | B0_campaign | 3150 | 1/3/3.42/12 | 1:61 2:449 3:1390 4:1040 5:110 6:7 7:1 8:2 9:48 10:38 11:2 12:2 | FLAT 3.42 | 10762 | 8900174 | 827 |
| 1 | B0_full | 3690 | 1/3/4.08/12 | 1:61 2:242 3:1571 4:426 5:575 6:718 7:4 8:3 9:32 10:52 11:5 12:1 | FLAT 4.08 | 15072 | 12464544 | 827 |
| 1 | B0_rbw | 2430 | 1/2/3.19/7 | 1:127 2:1135 3:253 4:12 5:883 6:17 7:3 | FLAT 3.19 | 7742 | 565166 | 73 |
| 1 | B0_rbw_1e-10 | 3450 | 1/3/3.69/9 | 1:172 2:1538 3:431 4:5 5:11 6:942 7:343 8:7 9:1 | FLAT 3.69 | 12734 | 929582 | 73 |
| 1 | B2_campaign | 3510 | 5/9/8.85/17 | 5:69 6:215 7:196 8:925 9:1092 10:502 11:358 12:130 13:12 14:5 15:5 17:1 | M1 2.25, M2 2.38, PULSE 1.00, M3 2.23 | 24051 | 5659602 | 235 |
| 1 | B2_rbw | 15750 | 5/8/8.23/15 | 5:785 6:1842 7:4140 8:2676 9:1658 10:2277 11:2012 12:294 13:51 14:14 15:1 | M1 1.76, M2 2.60, PULSE 1.00, M3 1.87 | 98091 | 2661364 | 27 |
| 1 | B2_full_1e-08 | 3450 | 5/10/10.19/18 | 5:57 6:117 7:105 8:337 9:819 10:587 11:363 12:567 13:332 14:132 15:25 16:7 17:1 18:1 | M1 2.45, M2 2.93, PULSE 1.00, M3 2.80 | 28242 | 6608055 | 234 |
| 1 | B2_rbw_1e-09 | 9630 | 5/8/8.69/16 | 5:480 6:694 7:2774 8:1648 9:375 10:611 11:1867 12:886 13:267 14:25 15:2 16:1 | M1 1.80, M2 2.98, PULSE 1.00, M3 1.91 | 64427 | 1808782 | 28 |
| 1 | B2_rbw_1e-10 | 13560 | 5/8/8.93/16 | 5:676 6:763 7:3830 8:2457 9:656 10:381 11:1917 12:1833 13:892 14:116 15:35 16:4 | M1 1.84, M2 3.16, PULSE 1.00, M3 1.93 | 93910 | 2672649 | 28 |
| 1 | B2_rbw_1e-12 | 3270 | 5/8/9.72/18 | 5:163 6:109 7:636 8:781 9:327 10:7 12:233 13:541 14:325 15:138 16:8 17:1 18:1 | M1 2.10, M2 3.67, PULSE 1.00, M3 1.95 | 25254 | 737703 | 29 |
| 2 | B0_campaign | 2880 | 1/3/3.62/12 | 1:47 2:231 3:1341 4:666 5:538 6:10 7:1 9:8 10:24 11:13 12:1 | FLAT 3.62 | 10420 | 8617340 | 827 |
| 2 | B0_full | 2550 | 1/3/4.08/11 | 1:42 2:90 3:1173 4:271 5:362 6:574 7:14 8:1 9:6 10:16 11:1 | FLAT 4.08 | 10410 | 8609070 | 827 |
| 2 | B0_rbw | 2250 | 1/2/3.21/7 | 1:112 2:1045 3:232 4:2 5:839 6:15 7:5 | FLAT 3.21 | 7226 | 527498 | 73 |
| 2 | B0_rbw_1e-10 | 2430 | 1/3/3.85/9 | 1:121 2:666 3:713 5:1 6:752 7:167 8:9 9:1 | FLAT 3.85 | 9359 | 683207 | 73 |
| 2 | B2_campaign | 2310 | 5/9/9.16/17 | 5:38 6:79 7:124 8:552 9:676 10:419 11:233 12:126 13:40 14:11 15:11 17:1 | M1 2.35, M2 2.42, PULSE 1.00, M3 2.39 | 16533 | 3892592 | 235 |
| 2 | B2_rbw | 3930 | 5/8/8.35/15 | 5:196 6:309 7:1129 8:664 9:201 10:864 11:529 12:14 13:19 14:4 15:1 | M1 1.79, M2 2.65, PULSE 1.00, M3 1.91 | 24943 | 677403 | 27 |
| 2 | B2_full_1e-08 | 2370 | 5/10/10.33/18 | 5:39 6:79 7:2 8:211 9:669 10:382 11:188 12:444 13:159 14:162 15:19 16:14 17:1 18:1 | M1 2.52, M2 2.98, PULSE 1.00, M3 2.84 | 19747 | 4622458 | 234 |
| 2 | B2_rbw_1e-09 | 2550 | 5/8/8.77/16 | 5:127 6:93 7:680 8:507 9:167 10:222 11:487 12:202 13:50 14:14 16:1 | M1 1.93, M2 2.90, PULSE 1.00, M3 1.95 | 17275 | 475756 | 28 |
| 2 | B2_rbw_1e-10 | 2760 | 5/8/9.31/17 | 5:137 6:94 7:556 8:644 9:270 11:313 12:368 13:192 14:172 15:13 17:1 | M1 2.08, M2 3.28, PULSE 1.00, M3 1.95 | 20178 | 570858 | 28 |
| 2 | B2_rbw_1e-12 | 2430 | 5/8/9.76/18 | 5:121 6:81 7:444 8:609 9:243 12:164 13:405 14:246 15:101 16:15 18:1 | M1 2.12, M2 3.69, PULSE 1.00, M3 1.95 | 18848 | 550950 | 29 |
| 3 | B0_campaign | 1050 | 1/3/3.47/10 | 1:17 2:101 3:509 4:334 5:62 6:3 7:1 9:6 10:17 | FLAT 3.47 | 3641 | 3011107 | 827 |
| 3 | B0_full | 1050 | 1/4/4.16/11 | 1:17 2:35 3:471 4:125 5:130 6:242 7:5 8:2 9:12 10:10 11:1 | FLAT 4.16 | 4372 | 3615644 | 827 |
| 3 | B0_rbw | 1050 | 1/2/3.22/7 | 1:52 2:484 3:112 4:2 5:390 6:7 7:3 | FLAT 3.22 | 3377 | 246521 | 73 |
| 3 | B0_rbw_1e-10 | 1050 | 1/3/3.84/8 | 1:52 2:279 3:316 4:1 6:351 7:47 8:4 | FLAT 3.84 | 4029 | 294117 | 73 |
| 3 | B2_campaign | 1050 | 5/9/9.23/17 | 5:17 6:35 7:32 8:248 9:324 10:200 11:107 12:50 13:27 14:5 15:4 17:1 | M1 2.38, M2 2.42, PULSE 1.00, M3 2.43 | 7594 | 1788185 | 235 |
| 3 | B2_rbw | 2370 | 5/8/8.35/15 | 5:118 6:199 7:666 8:400 9:98 10:553 11:318 12:8 13:7 14:2 15:1 | M1 1.79, M2 2.66, PULSE 1.00, M3 1.90 | 15046 | 409390 | 27 |
| 3 | B2_full_1e-08 | 1050 | 5/10/10.38/18 | 5:17 6:35 8:76 9:305 10:178 11:71 12:210 13:69 14:71 15:10 16:6 17:1 18:1 | M1 2.53, M2 2.99, PULSE 1.00, M3 2.86 | 8801 | 2059955 | 234 |
| 3 | B2_rbw_1e-09 | 1050 | 5/8/8.95/16 | 5:52 6:35 7:210 8:245 9:106 10:90 11:156 12:107 13:44 14:4 16:1 | M1 2.10, M2 2.90, PULSE 1.00, M3 1.95 | 7298 | 198838 | 27 |
| 3 | B2_rbw_1e-10 | 1050 | 5/8/9.16/16 | 5:52 6:35 7:209 8:246 9:105 10:1 11:211 12:67 13:109 14:11 15:3 16:1 | M1 2.10, M2 3.10, PULSE 1.00, M3 1.95 | 7513 | 208912 | 28 |
| 3 | B2_rbw_1e-12 | 1050 | 5/8/9.78/18 | 5:52 6:35 7:172 8:283 9:105 12:72 13:174 14:107 15:43 16:6 18:1 | M1 2.14, M2 3.69, PULSE 1.00, M3 1.95 | 8166 | 238425 | 29 |
| 4 | B0_campaign | 1170 | 1/3/3.28/7 | 1:19 2:134 3:568 4:399 5:47 6:2 7:1 | FLAT 3.28 | 3841 | 3176507 | 827 |
| 4 | B0_full | 1170 | 1/3/4.06/8 | 1:19 2:39 3:543 4:125 5:150 6:289 7:3 8:2 | FLAT 4.06 | 4747 | 3925769 | 827 |
| 4 | B0_rbw | 690 | 1/2/3.20/7 | 1:34 2:319 3:75 4:4 5:253 6:3 7:2 | FLAT 3.20 | 2210 | 161330 | 73 |
| 4 | B0_rbw_1e-10 | 1170 | 1/3/3.82/8 | 1:58 2:310 3:356 4:1 5:2 6:397 7:44 8:2 | FLAT 3.82 | 4466 | 326018 | 73 |
| 4 | B2_campaign | 1170 | 5/9/9.16/17 | 5:19 6:42 7:53 8:260 9:347 10:241 11:122 12:80 13:1 14:2 15:2 17:1 | M1 2.35, M2 2.39, PULSE 1.00, M3 2.43 | 8381 | 1972937 | 235 |
| 4 | B2_rbw | 2490 | 5/8/8.30/15 | 5:124 6:223 7:686 8:420 9:176 10:527 11:325 12:4 13:3 14:1 15:1 | M1 1.78, M2 2.63, PULSE 1.00, M3 1.89 | 15685 | 425429 | 27 |
| 4 | B2_full_1e-08 | 1170 | 5/10/10.34/18 | 5:19 6:39 8:95 9:333 10:199 11:79 12:238 13:76 14:82 15:7 16:1 17:1 18:1 | M1 2.50, M2 2.99, PULSE 1.00, M3 2.85 | 9753 | 2282003 | 234 |
| 4 | B2_rbw_1e-09 | 1170 | 5/8/8.89/16 | 5:58 6:39 7:254 8:266 9:109 10:84 11:215 12:110 13:32 14:2 16:1 | M1 2.03, M2 2.90, PULSE 1.00, M3 1.95 | 8056 | 220474 | 27 |
| 4 | B2_rbw_1e-10 | 1170 | 5/8/9.12/16 | 5:58 6:39 7:232 8:277 9:119 10:1 11:239 12:77 13:122 14:4 15:1 16:1 | M1 2.09, M2 3.08, PULSE 1.00, M3 1.95 | 8331 | 231384 | 28 |
| 4 | B2_rbw_1e-12 | 1170 | 5/8/9.74/18 | 5:58 6:39 7:208 8:299 9:117 11:2 12:82 13:196 14:122 15:44 16:1 17:1 18:1 | M1 2.11, M2 3.68, PULSE 1.00, M3 1.95 | 9058 | 264561 | 29 |

### 4.5 The exit audit

**L6.** *Same rows. The whole-`y` residual (frozen ruler) at the entry to the output path,
recounted from `audit_residual.json` at 1e-6, 1e-8 and the run's own τ: `all` over every continuous
component; `restricted` with the components the per-run deferred nodes write excluded (V4's
statistic for `B2`, whose per-run nodes have not run at the audit position — the 112 `costs.*`
components above 1e-6 on every `B2` row are those); the last column counts restricted components at
or above 1e-12, named in L7.*

| seed | run | τ of run | max (all) | n ≥ 1e-6 (all) | n ≥ 1e-8 (all) | n ≥ τ of run (all) | max (restricted) | n ≥ 1e-6 (restr.) | n ≥ 1e-8 (restr.) | n ≥ τ of run (restr.) | n excluded | discrete mismatches | n restr. ≥ 1e-12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | B0_campaign | 1e-06 | 4.9e-14 | 0 | 0 | 0 | 4.9e-14 | 0 | 0 | 0 | 123 | 0 | 0 |
| 0 | B0_full | 1e-08 | 0.0e+00 | 0 | 0 | 0 | 0.0e+00 | 0 | 0 | 0 | 123 | 0 | 0 |
| 0 | B0_rbw | 1e-08 | 4.9e-14 | 0 | 0 | 0 | 4.9e-14 | 0 | 0 | 0 | 123 | 0 | 0 |
| 0 | B0_rbw_1e-10 | 1e-10 | 5.0e-14 | 0 | 0 | 0 | 5.0e-14 | 0 | 0 | 0 | 123 | 0 | 0 |
| 0 | B2_campaign | 1e-06 | 1.0e+00 | 112 | 112 | 112 | 1.6e-11 | 0 | 0 | 0 | 123 | 2 | 18 |
| 0 | B2_rbw | 1e-08 | 1.1e+00 | 112 | 112 | 112 | 2.4e-10 | 0 | 0 | 0 | 123 | 2 | 1 |
| 0 | B2_full_1e-08 | 1e-08 | 1.0e+00 | 112 | 112 | 112 | 0.0e+00 | 0 | 0 | 0 | 123 | 2 | 0 |
| 0 | B2_rbw_1e-09 | 1e-09 | 1.0e+00 | 112 | 112 | 112 | 4.9e-14 | 0 | 0 | 0 | 123 | 2 | 0 |
| 0 | B2_rbw_1e-10 | 1e-10 | 1.0e+00 | 112 | 112 | 112 | 5.0e-14 | 0 | 0 | 0 | 123 | 2 | 0 |
| 0 | B2_rbw_1e-12 | 1e-12 | 1.0e+00 | 112 | 112 | 112 | 5.0e-14 | 0 | 0 | 0 | 123 | 2 | 0 |
| 1 | B0_campaign | 1e-06 | 0.0e+00 | 0 | 0 | 0 | 0.0e+00 | 0 | 0 | 0 | 123 | 0 | 0 |
| 1 | B0_full | 1e-08 | 0.0e+00 | 0 | 0 | 0 | 0.0e+00 | 0 | 0 | 0 | 123 | 0 | 0 |
| 1 | B0_rbw | 1e-08 | 0.0e+00 | 0 | 0 | 0 | 0.0e+00 | 0 | 0 | 0 | 123 | 0 | 0 |
| 1 | B0_rbw_1e-10 | 1e-10 | 0.0e+00 | 0 | 0 | 0 | 0.0e+00 | 0 | 0 | 0 | 123 | 0 | 0 |
| 1 | B2_campaign | 1e-06 | 1.2e+01 | 112 | 112 | 112 | 4.4e-12 | 0 | 0 | 0 | 123 | 2 | 9 |
| 1 | B2_rbw | 1e-08 | 1.5e+01 | 112 | 112 | 112 | 6.6e-12 | 0 | 0 | 0 | 123 | 2 | 1 |
| 1 | B2_full_1e-08 | 1e-08 | 1.7e+01 | 112 | 112 | 112 | 0.0e+00 | 0 | 0 | 0 | 123 | 2 | 0 |
| 1 | B2_rbw_1e-09 | 1e-09 | 1.8e+01 | 112 | 112 | 112 | 2.5e-14 | 0 | 0 | 0 | 123 | 2 | 0 |
| 1 | B2_rbw_1e-10 | 1e-10 | 1.4e+01 | 112 | 112 | 112 | 0.0e+00 | 0 | 0 | 0 | 123 | 2 | 0 |
| 1 | B2_rbw_1e-12 | 1e-12 | 1.7e+01 | 112 | 112 | 112 | 3.7e-16 | 0 | 0 | 0 | 123 | 2 | 0 |
| 2 | B0_campaign | 1e-06 | 0.0e+00 | 0 | 0 | 0 | 0.0e+00 | 0 | 0 | 0 | 123 | 0 | 0 |
| 2 | B0_full | 1e-08 | 0.0e+00 | 0 | 0 | 0 | 0.0e+00 | 0 | 0 | 0 | 123 | 0 | 0 |
| 2 | B0_rbw | 1e-08 | 4.9e-14 | 0 | 0 | 0 | 4.9e-14 | 0 | 0 | 0 | 123 | 0 | 0 |
| 2 | B0_rbw_1e-10 | 1e-10 | 4.9e-14 | 0 | 0 | 0 | 4.9e-14 | 0 | 0 | 0 | 123 | 0 | 0 |
| 2 | B2_campaign | 1e-06 | 2.5e+00 | 112 | 112 | 112 | 3.6e-11 | 0 | 0 | 0 | 123 | 2 | 28 |
| 2 | B2_rbw | 1e-08 | 1.1e+00 | 112 | 112 | 112 | 2.4e-10 | 0 | 0 | 0 | 123 | 2 | 1 |
| 2 | B2_full_1e-08 | 1e-08 | 2.1e+00 | 112 | 112 | 112 | 0.0e+00 | 0 | 0 | 0 | 123 | 2 | 0 |
| 2 | B2_rbw_1e-09 | 1e-09 | 1.9e+00 | 112 | 112 | 112 | 4.9e-14 | 0 | 0 | 0 | 123 | 2 | 0 |
| 2 | B2_rbw_1e-10 | 1e-10 | 1.7e+00 | 112 | 112 | 112 | 4.9e-13 | 0 | 0 | 0 | 123 | 2 | 0 |
| 2 | B2_rbw_1e-12 | 1e-12 | 2.1e+00 | 112 | 112 | 112 | 4.9e-14 | 0 | 0 | 0 | 123 | 2 | 0 |
| 3 | B0_campaign | 1e-06 | 4.9e-14 | 0 | 0 | 0 | 4.9e-14 | 0 | 0 | 0 | 123 | 0 | 0 |
| 3 | B0_full | 1e-08 | 0.0e+00 | 0 | 0 | 0 | 0.0e+00 | 0 | 0 | 0 | 123 | 0 | 0 |
| 3 | B0_rbw | 1e-08 | 4.9e-14 | 0 | 0 | 0 | 4.9e-14 | 0 | 0 | 0 | 123 | 0 | 0 |
| 3 | B0_rbw_1e-10 | 1e-10 | 4.9e-14 | 0 | 0 | 0 | 4.9e-14 | 0 | 0 | 0 | 123 | 0 | 0 |
| 3 | B2_campaign | 1e-06 | 1.5e+00 | 112 | 112 | 112 | 4.9e-14 | 0 | 0 | 0 | 123 | 2 | 0 |
| 3 | B2_rbw | 1e-08 | 1.1e+00 | 112 | 112 | 112 | 2.4e-10 | 0 | 0 | 0 | 123 | 2 | 1 |
| 3 | B2_full_1e-08 | 1e-08 | 1.5e+00 | 112 | 112 | 112 | 0.0e+00 | 0 | 0 | 0 | 123 | 2 | 0 |
| 3 | B2_rbw_1e-09 | 1e-09 | 1.5e+00 | 112 | 112 | 112 | 4.9e-14 | 0 | 0 | 0 | 123 | 2 | 0 |
| 3 | B2_rbw_1e-10 | 1e-10 | 1.5e+00 | 112 | 112 | 112 | 4.9e-14 | 0 | 0 | 0 | 123 | 2 | 0 |
| 3 | B2_rbw_1e-12 | 1e-12 | 1.5e+00 | 112 | 112 | 112 | 5.0e-14 | 0 | 0 | 0 | 123 | 2 | 0 |
| 4 | B0_campaign | 1e-06 | 4.9e-14 | 0 | 0 | 0 | 4.9e-14 | 0 | 0 | 0 | 123 | 0 | 0 |
| 4 | B0_full | 1e-08 | 0.0e+00 | 0 | 0 | 0 | 0.0e+00 | 0 | 0 | 0 | 123 | 0 | 0 |
| 4 | B0_rbw | 1e-08 | 4.9e-14 | 0 | 0 | 0 | 4.9e-14 | 0 | 0 | 0 | 123 | 0 | 0 |
| 4 | B0_rbw_1e-10 | 1e-10 | 4.9e-14 | 0 | 0 | 0 | 4.9e-14 | 0 | 0 | 0 | 123 | 0 | 0 |
| 4 | B2_campaign | 1e-06 | 1.5e+00 | 112 | 112 | 112 | 6.6e-12 | 0 | 0 | 0 | 123 | 2 | 18 |
| 4 | B2_rbw | 1e-08 | 1.1e+00 | 112 | 112 | 112 | 2.4e-10 | 0 | 0 | 0 | 123 | 2 | 1 |
| 4 | B2_full_1e-08 | 1e-08 | 1.5e+00 | 112 | 112 | 112 | 0.0e+00 | 0 | 0 | 0 | 123 | 2 | 0 |
| 4 | B2_rbw_1e-09 | 1e-09 | 1.5e+00 | 112 | 112 | 112 | 4.9e-14 | 0 | 0 | 0 | 123 | 2 | 0 |
| 4 | B2_rbw_1e-10 | 1e-10 | 1.5e+00 | 112 | 112 | 112 | 4.9e-14 | 0 | 0 | 0 | 123 | 2 | 0 |
| 4 | B2_rbw_1e-12 | 1e-12 | 1.5e+00 | 112 | 112 | 112 | 4.9e-14 | 0 | 0 | 0 | 123 | 2 | 0 |

**L7.** *Every restricted component at or above 1e-12 at exit, by name, per run (runs with none
omitted): the largest four, each with its membership of the arm's census set, its DSM set, the
block of V4's write set that writes it and its DSM readers. No ladder run appears: every census loop
at 1e-9 and below, and the whole-`y` `B2` loop at 1e-8, exits at the exact fixed point on the
restricted statistic (L6, max ≤ 4.9e-13).*

| seed | run | n ≥ floor | largest four (name, scaled residual) | membership of each (census set; DSM set; writing block; DSM readers) |
|---|---|---|---|---|
| 0 | B2_campaign | 18 | `fwbs.p_cp_shield_nuclear_heat_mw` 1.6e-11; `power.p_shld_heat_deposited_mw` 1.6e-11; `heat_transport.p_shld_coolant_pump_mw` 1.6e-11; `power.p_shld_coolant_pump_elec_mw` 1.6e-11 … | not census, interface, by M3, read by CCFE_HCPB,Power; not census, no DSM set, by M3, read by Power; not census, interface, by M3, read by Power; not census, no DSM set, by M3, read by Power |
| 0 | B2_rbw | 1 | `heat_transport.tlvpmw` 2.4e-10 | not census, interface, by M3, read by Costs |
| 1 | B2_campaign | 9 | `fwbs.p_cp_shield_nuclear_heat_mw` 4.4e-12; `power.p_shld_heat_deposited_mw` 4.4e-12; `heat_transport.p_shld_coolant_pump_mw` 4.4e-12; `power.p_shld_coolant_pump_elec_mw` 4.4e-12 … | not census, interface, by M3, read by CCFE_HCPB,Power; not census, no DSM set, by M3, read by Power; not census, interface, by M3, read by Power; not census, no DSM set, by M3, read by Power |
| 1 | B2_rbw | 1 | `heat_transport.tlvpmw` 6.6e-12 | not census, interface, by M3, read by Costs |
| 2 | B2_campaign | 28 | `fwbs.p_cp_shield_nuclear_heat_mw` 3.6e-11; `power.p_shld_coolant_pump_elec_mw` 3.6e-11; `heat_transport.p_shld_coolant_pump_mw` 3.6e-11; `power.p_shld_heat_deposited_mw` 3.6e-11 … | not census, interface, by M3, read by CCFE_HCPB,Power; not census, no DSM set, by M3, read by Power; not census, interface, by M3, read by Power; not census, no DSM set, by M3, read by Power |
| 2 | B2_rbw | 1 | `heat_transport.tlvpmw` 2.4e-10 | not census, interface, by M3, read by Costs |
| 3 | B2_rbw | 1 | `heat_transport.tlvpmw` 2.4e-10 | not census, interface, by M3, read by Costs |
| 4 | B2_campaign | 18 | `fwbs.p_cp_shield_nuclear_heat_mw` 6.6e-12; `power.p_shld_heat_deposited_mw` 6.6e-12; `power.p_shld_coolant_pump_elec_mw` 6.6e-12; `heat_transport.p_shld_coolant_pump_mw` 6.6e-12 … | not census, interface, by M3, read by CCFE_HCPB,Power; not census, no DSM set, by M3, read by Power; not census, no DSM set, by M3, read by Power; not census, interface, by M3, read by Power |
| 4 | B2_rbw | 1 | `heat_transport.tlvpmw` 2.4e-10 | not census, interface, by M3, read by Costs |

### 4.6 The decomposition

**L8.** *Per pair, `R = ρ × ε` with `N` solve-phase node calls and `C` evaluations: pooled over
the seeds where both members are accepted optima (sums, so `R = ρ × ε` exactly), and the per-seed
median (nearest-rank upper-middle, V4's) with its [min, max]. The first four pairs are `B2 / B0` at
the campaign's whole-`y` 1e-6, A93's census 1e-8, whole-`y` 1e-8 (this task's `B2` with A93's
`B0`), and this task's census 1e-10; the rest pair each ladder variant with its campaign partner and
with A93's census record of the arm at 1e-8. Note that "accepted" admits `B2_rbw_1e-09` and
`B2_rbw_1e-10` seed 1, which converged in another basin (L3).*

| pair | numerator / denominator | seeds used | R pooled | ρ pooled | ε pooled | R median [min, max] | ρ median [min, max] | ε median [min, max] | N num / den | C num / den |
|---|---|---|---|---|---|---|---|---|---|---|
| campaign_1e-6 | B2_campaign / B0_campaign | 5/5 | 0.5321 | 0.5450 | 0.9762 | 0.5650 [0.4285, 0.5954] | 0.5497 [0.5342, 0.5949] | 1.0000 [0.8021, 1.1143] | 343021 / 644700 | 8610 / 8820 |
| census_1e-8 (A93) | B2_rbw / B0_rbw | 4/5 | 1.2441 | 0.5083 | 2.4474 | 1.8332 [0.8909, 2.1025] | 0.5087 [0.5057, 0.5100] | 3.6087 [1.7467, 4.1579] | 382672 / 307587 | 11160 / 4560 |
| whole-y_1e-8 | B2_full_1e-08 / B0_full | 5/5 | 0.5295 | 0.5553 | 0.9535 | 0.5395 [0.5158, 0.5655] | 0.5533 [0.5395, 0.5655] | 1.0000 [0.9294, 1.0000] | 411937 / 777987 | 8610 / 9030 |
| census_1e-10 | B2_rbw_1e-10 / B0_rbw_1e-10 | 5/5 | 1.0144 | 0.4602 | 2.2042 | 0.4595 [0.4583, 1.8397] | 0.4595 [0.4583, 0.4681] | 1.0000 [1.0000, 3.9304] | 698091 / 688149 | 19110 / 8670 |
| B0_rbw_1e-10_vs_B0_campaign | B0_rbw_1e-10 / B0_campaign | 5/5 | 1.0674 | 1.0859 | 0.9830 | 1.1066 [0.8982, 1.1832] | 1.0803 [1.0645, 1.1627] | 1.0000 [0.8438, 1.0952] | 688149 / 644700 | 8670 / 8820 |
| B0_rbw_1e-10_vs_B0_rbw_1e-08 | B0_rbw_1e-10 / B0_rbw | 5/5 | 1.4636 | 1.1800 | 1.2403 | 1.2952 [1.1892, 2.0208] | 1.1918 [1.1585, 1.1992] | 1.0800 [1.0000, 1.6957] | 688149 / 470169 | 8670 / 6990 |
| B2_full_1e-08_vs_B2_campaign | B2_full_1e-08 / B2_campaign | 5/5 | 1.2009 | 1.2009 | 1.0000 | 1.1790 [1.1747, 1.2138] | 1.1790 [1.1747, 1.2343] | 1.0000 [0.9829, 1.0260] | 411937 / 343021 | 8610 / 8610 |
| B2_full_1e-08_vs_B2_rbw_1e-08 | B2_full_1e-08 / B2_rbw | 4/5 | 0.6499 | 1.4055 | 0.4624 | 0.6625 [0.3422, 0.8419] | 1.4100 [1.3961, 1.4230] | 0.4699 [0.2405, 0.6031] | 248690 / 382672 | 5160 / 11160 |
| B2_rbw_1e-09_vs_B2_campaign | B2_rbw_1e-09 / B2_campaign | 5/5 | 1.5639 | 0.8959 | 1.7456 | 0.9689 [0.8823, 2.5386] | 0.8826 [0.8767, 0.9253] | 1.1039 [1.0000, 2.7436] | 536437 / 343021 | 15030 / 8610 |
| B2_rbw_1e-09_vs_B2_rbw_1e-08 | B2_rbw_1e-09 / B2_rbw | 4/5 | 0.5092 | 1.0523 | 0.4839 | 0.4976 [0.2813, 0.6776] | 1.0581 [1.0443, 1.0590] | 0.4699 [0.2658, 0.6489] | 194845 / 382672 | 5400 / 11160 |
| B2_rbw_1e-10_vs_B2_campaign | B2_rbw_1e-10 / B2_campaign | 5/5 | 2.0351 | 0.9169 | 2.2195 | 0.8982 [0.8950, 3.6561] | 0.8982 [0.8950, 0.9464] | 1.0000 [1.0000, 3.8632] | 698091 / 343021 | 19110 / 8610 |
| B2_rbw_1e-10_vs_B2_rbw_1e-08 | B2_rbw_1e-10 / B2_rbw | 4/5 | 0.5387 | 1.0831 | 0.4973 | 0.5066 [0.2598, 0.7635] | 1.0803 [1.0747, 1.0872] | 0.4699 [0.2405, 0.7023] | 206128 / 382672 | 5550 / 11160 |
| B2_rbw_1e-12_vs_B2_campaign | B2_rbw_1e-12 / B2_campaign | 5/5 | 0.9573 | 0.9708 | 0.9861 | 0.9419 [0.9385, 1.0031] | 0.9429 [0.9399, 1.0074] | 1.0000 [0.9316, 1.0519] | 328377 / 343021 | 8490 / 8610 |
| B2_rbw_1e-12_vs_B2_rbw_1e-08 | B2_rbw_1e-12 / B2_rbw | 4/5 | 0.5281 | 1.1291 | 0.4677 | 0.5318 [0.2728, 0.6958] | 1.1318 [1.1253, 1.1344] | 0.4699 [0.2405, 0.6183] | 202092 / 382672 | 5220 / 11160 |

### 4.7 Wall clock (context, never evidence)

**L9.** *Per member: n runs, their summed, minimum and maximum `wall_s` from the records. One run
each; another task on the machine; the double launch of §3 overlapped the kept records' window
only after they were complete, but the original parent's later (discarded) runs shared the machine
with the second copy's one child.*

| run | n | Σ wall s | min | max |
|---|---|---|---|---|
| B0_campaign | 5 | 417 | 28 | 145 |
| B0_full | 5 | 529 | 31 | 198 |
| B0_rbw | 5 | 180 | 17 | 59 |
| B0_rbw_1e-10 | 5 | 253 | 18 | 99 |
| B2_campaign | 5 | 379 | 27 | 150 |
| B2_rbw | 5 | 828 | 71 | 476 |
| B2_full_1e-08 | 5 | 446 | 45 | 173 |
| B2_rbw_1e-09 | 5 | 474 | 25 | 308 |
| B2_rbw_1e-10 | 5 | 634 | 24 | 441 |
| B2_rbw_1e-12 | 5 | 301 | 20 | 114 |

### 4.8 Reading the tables

1. **The tolerance alone, on the partitioned arm (L3, L4: `B2_full_1e-08`).** Path equal to the
   campaign's on seeds 0, 3, 4; seed 1 at 58 iterations / 3 450 evaluations against 59 / 3 510
   and seed 2 at 40 / 2 370 against 39 / 2 310 — by the iteration-per-attempt list these two are
   **not** the campaign's path, though the counts differ by one iteration; the optimum is the
   campaign's on all five (max 1.1e-10). Against A93's `B2` census 1e-8 the same arm at the same
   τ took 0.24–0.60 of the evaluations (seeds 0, 2, 3, 4) and converged where the census run had
   failed (seed 1). The per-evaluation cost is 1.201 of the campaign's `B2` (L8) — the same +20 %
   the flat arm paid for 1e-8 in A93 — and the exit is at the exact fixed point on all five
   (L6: restricted max 0.0).
2. **The census arm down the ladder (L4).** Paths equal to the campaign's: 0/5 (1e-8, A93) →
   2/5 (1e-9: 3, 4) → 3/5 (1e-10: 0, 3, 4) → 3/5 (1e-12: 0, 3, 4). Evaluations by seed at 1e-12
   are 570 / 3 270 / 2 430 / 1 050 / 1 170 against the campaign's 570 / 3 510 / 2 310 / 1 050 /
   1 170. The flat census control at 1e-10: 3/5 (0, 3, 4), where A93's at 1e-8 was 2/5 (seed 4
   had shortened to 12 iterations; at 1e-10 it is the campaign's 20 again).
3. **Read against A89's ladder (L1).** The census set's objective error on st is 4.9e-11 at 1e-8
   and 1e-9 and 0.0 at 1e-10 and 1e-12; the path count is 0/5 → 2/5 at the two nonzero rungs and
   3/5 at the two zero rungs, on both arms where run. 3/5 with seeds 0, 3, 4 is also what the
   whole-`y` test at 1e-8 gives on both arms (`B0_full`, `B2_full_1e-08`). So at the rung where the
   census loop hands VMCON the same objective the whole-`y` loop does, the two test sets give the
   same path on the same seeds.
4. **Seeds 1 and 2 (L3).** Equal to the campaign's path in none of the ten members' twenty runs;
   the campaign's own two arms differ on them too (seed 1: 53 against 59; seed 2: 27 + 21 against
   39). On every accepted run but two their optimum is the campaign's (≤ 6.4e-9 on `B0` seed 1,
   the distance the campaign's own `B0` and `B2` are apart there; ≤ 2.0e-11 elsewhere).
5. **The two exceptions, both seed 1 `B2` census (L3, L4).** At 1e-9: attempt 1 `ifail = 2` at the
   100-iteration cap, attempt 2 (`epsfcn × 10`) `ifail = 1` after 61 — `norm_objf` −16.59657,
   1.3e-2 relative above the campaign's −16.80891 and in the basin of seeds 0, 2, 3, 4
   (−16.58858, not that either). At 1e-10: attempts `ifail` 2 / 5 / 1 (100 / 64 / 62 iterations),
   `norm_objf` −16.83087 — 1.3e-3 relative *below* the campaign's, feasible (`sqsumsq` 4.4e-12),
   and the value A93's failed 1e-8 run had reached (−16.83087, `ifail = 2`). Three basins on one
   seed, then: the campaign's (−16.80891; also `B2` whole-`y` 1e-8 and census 1e-12), the other
   seeds' (−16.58858 / −16.59657) and a lower one (−16.83087) that V4's whole-`y` loops never
   found. Whether −16.83087 is the better optimum of the problem is a question about st's
   problem, not about the loop; here it is a different end state, which is what the same-optimum
   floor is for.
6. **Cost (L5, L8).** Tightening τ costs the census arm sweeps: `M2` 2.62 (1e-8) → 2.98 → 3.16 →
   3.67 (1e-12) per solve, `M1` 1.78 → 2.14, `M3` 1.89 → 1.95; per evaluation `B2` census is
   0.896 / 0.917 / 0.971 of the campaign's `B2` at 1e-9 / 1e-10 / 1e-12. The `B2 / B0` census pair
   at 1e-10 has ρ = 0.460 pooled (0.458–0.468 per seed) against A93's 0.508 at 1e-8 and the
   campaign's 0.545; ε is 1.000 on seeds 0, 2, 3, 4 and 3.93 on seed 1, so the pooled R (1.014)
   is seed 1's and the median R (0.4595) the other four's. The whole-`y` pair at 1e-8
   (`B2_full_1e-08 / B0_full`) reproduces the campaign's R: 0.530 against 0.532, ρ 0.555 against
   0.545.
7. **The exit audit (L6, L7).** 0 components at or above the run's τ on the governing statistic in
   all 25; the `B2` census loops at 1e-9 and below leave nothing at or above 1e-12 (restricted max
   4.9e-14 to 4.9e-13), where A93's at 1e-8 left `tlvpmw` at 2.4e-10 on four seeds; so the lag A93
   named as observation (iii) is gone one rung down, where the path is still 2 of 5. The lag was
   not the mechanism. The two discrete mismatches on every `B2` row are the per-run deferred writes
   (`vacuum.n_vac_pumps_high`, `vacuum.n_vv_vacuum_ducts`), on the campaign's rows too.

## 5. Autonomous decisions, each with its reversal path

1. **The ladder lives in A93's script under one flag (`--ladder`)** rather than a new script, as the
   brief asked; A93's code paths are unchanged in behaviour (its variant tuple, records directory,
   summary and tables are untouched; `campaign()` gained a `runs` keyword defaulting to A93's
   directory, and the numba cache directory follows the campaign's `runs_dir`, which for A93's
   variants is the same path as before). Reversal: split `stage_run_ladder` / `summarise_ladder` /
   `print_ladder_tables` into their own module; they import nothing A93's stages do not.
2. **Variant labels carry the tolerance** (`B2_rbw_1e-10`) so a ladder record's directory names its
   rung; A93's labels (`B2_rbw`) stay tolerance-free because A93 had one τ. Reversal: rename the
   directories and `ladder_label`.
3. **The A93 reference is the census run of the arm at 1e-8** (`B0_rbw` for `B0` variants, `B2_rbw`
   for `B2` variants), as the brief names it; A93's `B0_full` is carried as a member and compared
   with `B0_rbw` too. Reversal: `A93_REFERENCE_FOR`.
4. **Path equality = same iterations per attempt and same evaluations.** A stricter test (hex
   identity of every function value) was not needed: the coarse test already separates the seeds,
   and where it says "equal" the campaign's `norm_objf` agrees to ≤ 7.9e-13. Reversal: add an
   evaluation-log comparison; V4 records no per-evaluation log, so it would need `narrowing`'s
   pass log (A93 §7 (d), now A92's census).
5. **Seeds by A93's rule** (the first five of the campaign's every-arm-converged set on st: 0–4).
   Reversal: `N_SEEDS`.
6. **`--lift` is refused under `--ladder`** rather than run to no effect: st has no lifted input
   file. Reversal: drop the refusal; the stage would derive the two pulsed files into the ladder's
   directory, which no ladder run reads.
7. **Run kind `smoke`**, as A93 and A89: outside every V4 tally. Reversal: none.
8. **The discard rule after the double launch** (§3): delete by `command.json` mtime later than
   18:03:00 regardless of which parent wrote the record, keep the 11 before it. Chosen over
   "delete only the contaminated directory" because the second parent's stdout could not be
   trusted as a complete list of what it had touched. Reversal: none needed — the 14 re-made
   records stamp the same commit, and the original parent had made all 14 too before they were
   discarded: its result lines (`run.log`) and the relaunch's (`run_relaunch.log`) agree on the
   evaluation count of all 14 (13 560 / 2 760 / 1 050 / 1 170; 570 / 3 270 / 2 430 / 1 050 /
   1 170; 570 / 3 450 / 2 430 / 1 050 / 1 170) and on `ifail` of 13; the one that differs is the
   contaminated `B2_rbw_1e-10` seed 1 itself, whose `run.log` line (`ifail=0`) was read from a
   directory two children were writing. The counts are the acceptance quantities, so the
   discarded population and the kept one are the same measurement.

## 6. Limits

- **Five seeds** of the campaign's 22 on st, by rule. Counts, not rates: "n of 5" throughout, and
  "seeds 1 and 2 are fragile" is a statement about two seeds, not about a fraction of st's starts.
- **`st_regression` only**, by the brief; the pulsed configurations' paths were unchanged in A93 at
  1e-8 and were not re-run at tighter τ.
- **No `B0` census at 1e-9 or 1e-12**, so the census pair `B2 / B0` is measured at 1e-10 only
  (A93's at 1e-8); the 1e-12 statement about seed 1 is about the partitioned arm alone.
- **The ladder compares whole runs by their end state and counts.** Where a path differs, the
  first evaluation at which it differs is not located (no per-evaluation log in V4's record).
- **A89's ladder is evaluation-phase** (29 stencil points at four displaced entries, `A0` / `A2`);
  it is read beside, not re-measured on, the optimiser's path. "Objective residual 0.0" is A89's
  reading at those points, not a property of every evaluation of these runs.
- **Which of seed 1's three basins is the problem's optimum is not settled here**; the report
  uses the campaign's as the reference because that is what V4's same-optimum floor compares with.
- **Timings are context**: one run each, another task on the machine, a second copy of this run
  for part of the window (§3), and the first run of the matrix carrying numba's compilation.
- **Not V4 numbers.** Run kind `smoke`; the campaign's and A93's records were read from their
  relocated copies (`A90_runs/`, `tree_git_head 57dc0c14`; `A93_runs/`, `4abdc165`), arm names
  translated by `records.read`.

## 7. Proposals (the user's to rule)

- **(a) Declare st's trajectory term per τ, from this ladder, in the V5 plan.** At τ = 1e-8 under
  the census set the partitioned arm's path is not the campaign's on any seed and one seed in five
  leaves the basin (A93); at 1e-10 the three stable seeds' paths are the campaign's and seed 1
  converges — in another basin; at 1e-12 the three stable seeds' paths are the campaign's and
  seed 1 converges in the campaign's basin. The tolerance alone (whole `y` at 1e-8) does none of
  this. The plan's expected reading for st should say which of these it is running at.
- **(b) Name seeds 1 and 2 as st's fragile seeds.** Neither arm's path equals the campaign's on
  them under any change to the loop's test (20 of 20 runs); the campaign's own arms differ there.
  A path-equality comparison on st is a statement about the other three seeds; the optimum
  comparison (`norm_objf` within 1e-6 plus the feasibility audit, D6) is the statement on all
  five, with seed 1's basin change as a known failure mode of the census set at 1e-8 to 1e-10.
- **(c) If st's partitioned arm is to be run at matched accuracy under the census set, run it at
  1e-12 on st** — the rung where A89 reads the census loops exact (objective and constraint error
  0.0), where the path returns on the stable seeds, where seed 1 converges in the campaign's basin,
  and where the per-evaluation cost is 0.971 of V4's partitioned arm (against 0.839 at 1e-8, an
  accuracy V4's arm did not reach). A `B0` census at 1e-12 (five runs) would complete that pair.
- **(d) Seed 1's lower basin (−16.83087)** — reached by the census arm at 1e-8 (failed) and 1e-10
  (converged, feasible) and by no whole-`y` run — is a finding about st's problem, not about the
  loop: a feasible point 1.3e-3 relative below the optimum V4's arms report on that seed. Worth a
  line in `DSM_VALIDATION.md` or the st configuration's notes, not a task.
- **(e) Trap T19** (a `nohup … &` child does not outlive the sandboxed Bash call that started it;
  the Bash tool's background mode does) has been filed by the orchestrator; this task is its
  instance.

## 8. Change log

- 2026-09-29 — opened; `--ladder` committed at `6a51108b`; matrix launched (25 optimisations,
  serial, `B2_full_1e-08` first, then `B2_rbw_1e-09`, `B2_rbw_1e-10`, `B2_rbw_1e-12`,
  `B0_rbw_1e-10`).
- 2026-09-29 — 11 records in when the run was wrongly diagnosed as dead and a second copy launched
  (§3); the second copy died with its Bash call; the original completed all 25; the 14 records
  after 18:03:00 discarded by rule, one further `nohup` relaunch died the same way, the 14 re-made
  by one background-mode run (18:33–18:54). All 25 at `6a51108b`, clean.
- 2026-09-29 — `--summarise --ladder` at `6a51108b`; results, verdict and proposals written.

## 9. Orchestrator's critical assessment (protocol §5) — verdict: merge

*Written 2026-09-29 by the orchestrating session under D37; checked differently from the agent.*

**Checked.** (1) All 25 records recounted by the orchestrator from `metrics.json` against the campaign's
records (`A90_runs/campaign/optimisation/st_regression/`, `B3` = today's `B2`), by iterations per attempt,
evaluations and paired relative `norm_objf`: every cell of the hand-back's per-rung table reproduces —
`B2` whole-`y` 1e-8 path = campaign on seeds 0, 3, 4 (seed 1 58/3 450 vs 59/3 510, seed 2 40/2 370 vs
39/2 310; optimum within 1.1e-10 on all five); `B2` census 1e-9 2/5, 1e-10 3/5, 1e-12 3/5; `B0` census
1e-10 3/5; seed 1's `B2` census optimum 1.3e-2 off at 1e-9 (100 + 61 iterations) and 1.3e-3 off at 1e-10
(100 + 64 + 62), and 3.5e-11 at 1e-12 (55 iterations, one attempt). (2) Every record stamped `6a51108b`,
the script's commit; the worktree is clean; nothing under the V4 or V5 folders. (3) The double launch
(the orchestrator's mistake, T19) is stated in §3 and decision 8 with the discard rule; the discarded
population and the re-made one agree on every evaluation count, which is the acceptance quantity.

**Read against the question.** A93's hypothesis (a nonzero objective residual of the census-set loop at
1e-8 on st moves a fragile optimiser) is confirmed in its observable form: the tolerance alone does not
move the partitioned arm (whole-`y` 1e-8 is the flat arm's behaviour in A93), the set does, and the effect
fades exactly where A89's residual reads 0.0. The 1e-12 result on seed 1 is the new fact: the census set
needs the loops exact, not merely below h³, before st's most fragile seed stays in its basin.

**Decision under D37 (autonomous; the user: "you can modify the convergence set and tolerance as you see fit
(inform me after)").** The campaign's declared setting stays **the census set at τ = 1e-8 in every
configuration** — the rule's value, D32, and the user's "keep the tolerance: failed starts are results" —
with `st_regression`'s trajectory term pre-declared non-neutral from this ladder (the mechanism named, seeds
1 and 2 named as st's fragile seeds, seed 1's basin change a known failure mode of the census set at
1e-8..1e-10). **Added: a supplementary st stage at τ = 1e-12**, `B0` and `B2` under the census set on the
campaign's seed set (50 optimisations, ~10 % of the budget), reported beside the declared cell and labelled
supplementary — the rung where A89 reads the census loops exact, the stable seeds' paths return and seed 1
holds its basin, so the paper's st column can show the partitioned cost at matched path as well as at the
declared τ. Not chosen: a per-configuration τ (a rule fitted to the outcome) or 1e-12 everywhere (unmeasured
on the pulsed configurations, where 1e-8 is path-identical 30/30). Proposal (d) (seed 1's lower feasible
basin) is noted in the queue as a finding about st's problem.
