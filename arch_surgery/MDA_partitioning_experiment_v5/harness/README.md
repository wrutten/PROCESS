# The V5 harness

> **Document status** — **CURRENT.** The harness's own description for the fifth revision of the
> experiment (V5), rewritten to V5's text by task A103 (v5-tally-and-tables), 2026-09-30, from V4's
> README that A94 (v5-copy) copied whole and later tasks amended section by section (V5 plan §8 left the
> rewrite pending since A98 (v5-reporting-trim)). Sections that described machinery V5 removed — the
> second implementation and its gate, the report renderer and its companion file, the predicate-mode
> gate and the `mixed` ruler, the cold-chain gate, the stencil entry regime, the function-weighted
> tables — are gone; V4's README in `../../MDA_partitioning_experiment_v4/harness/README.md` keeps
> them as history. Paths are relative to `MDA_partitioning_experiment_v5/` unless a line says otherwise.
> The plan is [`../../docs/plans/V5_EXPERIMENT_PLAN.md`](../../docs/plans/V5_EXPERIMENT_PLAN.md);
> where this file and the plan disagree, the plan is the declaration and this file is wrong.

---

## 1. What this folder is

The experiment asks one question: **does rearranging how PROCESS's models are solved — without
changing any model — reduce the number of model evaluations needed to reach the same answer at the
same accuracy?** V5 answers it as an existence proof in model-evaluation counts, on three
configurations (`large_tokamak_nof`, `low_aspect_ratio_DEMO`, `st_regression`; `tok`, `lad`, `st`),
in two phases: **phase A**, one evaluation of the model set (`call_models`) from 25 displaced entries
per arm, and **phase B**, one whole optimisation from 25 starts per arm (`seed000` unperturbed,
seeds 1–24 displaced by δ = 0.10). Wall clock is reported beside the counts in the paper's appendix,
as context, never as evidence (D33).

The folder holds four things:

| path | what it is |
|---|---|
| `PROCESS/` | **the experiment's own copy of PROCESS.** Every run measures this tree, never the repository root's. Its `process/models/` is byte-identical to the frozen base `c0ae5b28` (gate `g0prime`); its driver files carry the architecture changes as environment-switched branches, each proven neutral with every switch unset (gate G1). `PROCESS/copy_gates.py` holds the copy's gates; `PROCESS/PROVENANCE.json` and `PROCESS/CHANGES.md` say what was copied from where and what changed since. |
| `harness/` | this package: it composes each arm from the switch matrix, runs PROCESS in isolated subprocesses, records what each run cost and how accurately it stopped, checks itself with gates, and summarises the records into tables. |
| `experiment_runner.py` | **the one button.** Every stage — preflight, gates, measurements, the campaign, the timing stages, the census, the paper's document — is a flag of this script (§11). A refused start or a failed gate is a result printed from the same entry point, never a crash. |
| `paper_tables.md` | the one generated document of the paper's tables (V5 list item 10), written by `--paper-tables write` and compared by `--paper-tables check` — the document of the **declared default campaign** (run ID `census_tau1e-08`); a campaign under other settings writes `paper_tables_<run ID>.md` beside it (§12); beside it `paper_cells_recount.py`, a short independent recount of exactly those cells from the raw records. |

Also at the top level: `run_stamp_survey.py` (the commits, worker counts, dirty flags and load averages
every record under `runs/` was made with; trap T13's survey), `compare_record_trees.py` (two record trees
compared job by job), `copy_manifest.py` and `COPY_MANIFEST.json` (the copy of V4's folder, A94),
`PROCESS_diff.py` (the copy's driver against the base, by file), and `EXPERIMENT_REPORT.md` (the V5 report).
`runs/` holds every record and is not tracked (§12).

**Isolation.** Every PROCESS run is a fresh subprocess in its own directory (PROCESS holds output-file
handles as class attributes; two runs in one process contaminate each other), and every subprocess
asserts that `process.__file__` is under `PROCESS/` of this folder (traps T6, T10).

---

## 2. The package

A subpackage imports the ones above it in this table and never the ones below.

| directory | what it holds |
|---|---|
| `core/` | `config` (every declared setting as frozen data: configurations, N, δ, the test sets and τ, F and the floors, the workers, the timers, the supplementary stages, `EXECUTION_APPROVED`), `framework` (what a gate, a tooth, a check and a measurement stage are), `records` (the run record's schema and its completeness contract), `pool` (the only place a PROCESS run starts; the job identity, its digest, the shared pool and the `--resume` decision), `provenance` (interpreter, tree and git stamps), `failure` (the outcome taxonomy) |
| `experiment/` | `arms` (the switch matrix as data, the rungs), `switches` (the driver's vocabulary and the capability probe), `test_sets` (the census stage, §5), `input_files` (committed and lifted), `artifacts` and `data_provenance` (every committed artifact a run reads, with digests) |
| `child/` | what runs **inside** a measurement subprocess: `optimise` (phase B), `evaluate` (phase A, the warmed child, §8), `child` (the counters, the output file, the exit audit), `census` and `read_before_write_census` (the write and read-before-write instruments), `ystate` and `predicate` (the coupling state and the one convergence test the driver and the audit share), `perturb` (the seeded displacement streams), `data_structure` (the whole-data-structure snapshot, D25), `postsolve` (which nodes the optimiser never reads). **Nothing here is edited while a measurement run executes** (harness plan amendment 13). |
| `measurement/` | `stats` (every statistical construction, once), `tables` (a table cannot be emitted without caption, denominator, audit position; no timing column in an acceptance table), `tally`, `tally_evaluation`, `tally_optimisation`, `tally_supplementary` (§10), `timing` (the wall-clock rows and stages, §9), `paper_tables` (the paper's document), `test_set_smoke` |
| `gates/` | `registry` (every gate and stage by name, the order, the gate table), one module per gate family (§11), `reproduction` and `reference` (gate GR and its committed reference), `selfcheck` (the harness's own checks, no PROCESS run) |
| top level | `chain.py` (the sequence the smoke and the campaign both run, §10), `data/` (the committed per-configuration artifacts and `PROVENANCE.json`), `reference/` (V4's twenty reference records, `reproduction_reference.json`) |

---

## 3. The switch matrix and the arms

An **arm** is one assignment of the driver's switches. The harness composes every arm's environment
from `experiment/arms.py`'s matrix and nothing else: every known variable is cleared first, then only
what the arm declares is set, so an inherited value can never change what is measured
(`arms.env_for`). Before a run, a throwaway child asks the tree what the environment resolved to; a
switch the tree does not implement is a **refusal**, never a run of a different arm under the right
name (`switches.probe`, gate `capability`).

| | **AR** | **A0** | **A1** | **A2** | **BR** | **B0** | **B1** | **B2** |
|---|---|---|---|---|---|---|---|---|
| MDA solve | upstream | flat | flat | partitioned | upstream | flat | flat | partitioned |
| stopping rule | objf/conf | test set @ τ | test set @ τ | test set @ τ per block | objf/conf | test set @ τ | test set @ τ | test set @ τ per block |
| block schedule | — | (one block) | (one block) | one pass | — | (one block) | (one block) | one pass |
| arrangement · node (`build` after `physics`) | — | — | — | ✓ | — | — | — | ✓ |
| arrangement · method (prime) | — | — | — | ✓ | — | — | — | ✓ |
| deferral per_call | — | — | — | ✓ | — | — | — | ✓ |
| deferral per_run | — | — | — | ✓ | — | — | — | ✓ |
| burn time out of the loop ⁺ | — | — | ✓ | ✓ | — | — | ✓ | ✓ |
| burn-time owner ⁺ | loop | loop | constant | constant | loop | loop | optimiser | optimiser |
| input file ⁺ | committed | committed | committed | committed | committed | committed | lifted | lifted |
| output-time loop (`MDA_Output`) | n/a | n/a | n/a | n/a | upstream | upstream | none | none |

⁺ pulsed configurations only; on `st_regression` (steady state) `A1` composes to `A0` and `B1` to `B0`,
both recorded as skipped. **The stopping-rule cell is a form**: `test set` and `τ` are the campaign's
settings, not the arm's (§5); the paper's matrix fills them in (`arms.matrix(campaign)`, e.g.
`feedback couplings @ τ = 1e-08` under the census set), and the `rungs` self-check compares the form
with the plan's Table 1 (`arms.PLAN_MATRIX`).

**The rungs** (`arms.RUNGS`, checked against the composed environments): `AR → A0` / `BR → B0` the
stopping rule (reported, never accepted on); `A0 → A1` / `B0 → B1` the burn-time ownership — the
**lift** — and, in phase B only, the output-time loop; `A1 → A2` / `B1 → B2` the **partition**. The
published pairs (D34): phase A `A2/A1` on the pulsed configurations, `A2/A0` on `st`; phase B `B2/B0`
with the rungs beside.

**The switches** (`switches.REGISTRY`), in three kinds:

| kind | switches | where the value comes from |
|---|---|---|
| architecture (the matrix's rows) | `mda`, `arrangement_node`, `arrangement_method`, `defer_per_call`, `defer_per_run`, `burn_time_owner`, `output_loop` | the arm |
| campaign settings (one value for every arm and both phases) | `test_set` (`census` / `write_set`), `tolerance` (τ), `test_sets`, `coupling_state`, `write_sets` (the artifacts), `defer_per_run_execution` (phase A's deferring arm, §7) | `core/config.Campaign` and the phase |
| instruments (observe a run, never change it; `switches.INSTRUMENT_SWITCHES`) | `timers` | `Campaign.timers`: off for the gates, on for the campaign press and the timing stages |

The pass and block traces (`pass_trace`, `pass_trace_full_from`, `block_trace`) are debugging
instruments cleared before every arm and never composed; the `predicate_mode` switch is retired with
the `mixed` ruler (DR11).

---

## 4. What one run does, end to end

1. The pool composes the **job**: phase, arm, configuration, seed, regime, run kind (`gate`, `smoke`,
   `campaign`, `supplementary`, `timing`), the campaign's test set and τ, the timers, and any entry
   state or pinned burn time. The job's rendered identity and its digest name the record
   (`pool.Job.identity`, `records.job_digest`); `--resume` keeps an existing record only when it is
   the same job and complete under today's contract (trap T13) — finished (`status == "ok"`), or
   **complete as a crash** (`records.why_not_complete_as_a_crash`: status `crashed` in a result row —
   `crashed`, `unconverged`, `unconverged-at-cap` — the traceback's last line and the pool's launcher
   stamps; issue I-38), so a model's own raise is a kept result and never re-run by a resumed press.
   `pool.why_not_kept` is the one decision; `--jobs` prints it without running.
2. A fresh subprocess runs `child/optimise.py` (one optimisation) or `child/evaluate.py` (one
   evaluation, warmed, §8) against `PROCESS/`, under the composed environment.
3. **Inside the driver copy**, per run: the deferral sets and the block schedule are resolved **once**
   and stamped (`schedule_resolution`, DR9, §6); per evaluation, the prime runs **once, before M1**
   (DR10, §6); every block loop stops on its **test set** at τ (DR11, §5); in phase A the deferring arm
   executes its per-run set **once** after convergence (item 5, §7); with the timers on, every node,
   sweep, test, evaluation and the run are timed (DR12, §9).
4. The child takes the **exit audit** — one further sweep from the state the solve handed over,
   excluded from every count and every timing (D36) — at a declared position: after the single
   evaluation in phase A, at the entry to `write_output_files` in phase B.
5. The child writes `metrics.json`; the pool stamps the identity, the digest and its own launcher block
   (independent wall, workers, load average). A record missing a declared field is refused by every
   reader (`records.assert_usable`), never summarised over.

---

## 5. The test set and its census (DR11; D32, D39)

A block loop stops when its **test set** moves by less than τ between sweeps. Which set is a
campaign-level switch, `PROCESS_ARCH_TEST_SET`, one value for every arm and both phases, never mixed
within a campaign (D39):

| value | what the loop tests | τ | provenance |
|---|---|---|---|
| `census` (the default) | the **census test set**: per loop and block, the coupling components a sweep of the block reads before it writes them and writes later in the same sweep — the feedback couplings, measured at run time in the arm's own order over whole optimisations | 1e-8, the rule ε ≤ `epsfcn`³ | D32; `data/test_sets_<configuration>.json` |
| `write_set` (the fallback) | the block's **whole write set** — exactly V4's predicate | 1e-6, V4's | D39 |

τ follows the set (`config.TAU_BY_TEST_SET`) unless `--tau` overrides it, and an override is stamped.
**A named tolerance rule** (`--tau-rule <name>`, `Campaign.tau_rule`; `config.TAU_RULES`; A105) gives
each configuration its own τ = factor × `epsvmc`, read from the configuration's committed input file
(PROCESS's default where it sets none), the factor declared by the rule: `epsvmc_times_epsfcn` (factor
`epsfcn`, 1e-3 by default: tok 1e-10, lad 1e-11, st 1e-12) and `epsvmc_times_tenth_epsfcn` (a tenth of
it, the retry ladder's smallest step: 1e-11, 1e-12, 1e-13). Refused with `--tau`. The rule's name
(`tau_rule`) and each τ are job-identity fields — `tau_rule` rendered only when set — and stamped
(`campaign_tau_rule` by the child, `tau_rule_derivation` by the pool; owed only by a rule's record); a
rule campaign is its own run ID, `runs/<test set>_rule_<rule>/` (§12). It reaches the flat and partitioned
loops; the reference arm composes no tolerance; a supplementary stage keeps its own τ. **No rule is the
default, and then no job, identity, digest or record changes.** Which rule, if any, a campaign is pressed
under is the user's open question (OQ-tolerance).
The test set and τ are job-identity fields rendered only where they differ from V4's, so a fallback job
carries V4's identity — which is what makes every record made before DR11 a fallback record and lets
GR read V4's reference records on this tree. The pool refuses a job at another setting than the
campaign's unless a declared **supplementary stage** admits it (§10). The driver selects a loop's sets
by `<mda>/<burn-time owner>` (`arms.Arm.loop_key`); a loop the artifact does not name is refused.

**The census stage** (`--census take | write`; `experiment/test_sets.py`, the instrument in
`child/read_before_write_census.py`): 16 censused optimisations (seeds 0 and 1, every iterating
optimisation arm on every configuration), each against an uncensused **twin** — status, exit code,
iterations, evaluations, solve-phase node calls and `norm_objf` to the bit, or the stage fails; the
union per configuration, loop and block, unioned with and compared to the prior sets
(`data/test_set_prior_*.json`); one artifact per configuration with the provenance of every record it
came from and its `sets_sha256`. `take` writes under `runs/census_test_sets/` and compares the result
with the committed artifacts (A102); `write` also copies them into `data/`.

**Gate GT** (`test_set`) shows the census set binds: from G6's pairing entry, one carried component
dropped from the arm's loop must stop the run earlier and leave a different exit state, or be reported
not individually binding; a dropped non-census control must change nothing; PASS needs at least one
bite over the job set. Refused under the fallback.

---

## 6. The schedule and the prime (DR9, DR10; items 7, 8; D31)

**DR9** — the per-call deferral tails and the block schedule are resolved **once per run**
(`resolve_schedule`, memoised on the figure of merit) and reused by every evaluation; the resolution is
stamped once (`schedule_resolution`, with the digests of what it read). V4 re-derived them on every
evaluation (issue I-30), a harness cost that biased every wall-clock row against the intervention. No
count moves.

**DR10** — the arrangement's method-level move (the **prime**: the first-wall geometry method ahead of
M1) runs **once per `call_models`, before M1**, as pre-processing of the sequenced schedule, instead of
at every sweep head; the output path and the exit audit no longer prime; `n_arrangement_method_calls`
equals the evaluations. Gate G2 (`prime_map`) was re-formed for it: the prime is inert once the
first-wall model has run, and the once-per-evaluation form reaches the same exit states as V4's
per-sweep form (its part (ii) reads GC's DR9 → DR10 straddle, a one-time result).

**Gate GC** (`count_neutrality`) is the proof that a count-neutral change is count-neutral: on a job set
of both phases, every arm and one seed per configuration, node calls, sweeps, predicate evaluations,
components compared and every exit state identical to the digit before and after the change, with any
declared move (item 5's one sweep, DR10's prime count) predicted by a declared rule and every undeclared
move a mismatch. Its last straddle is `item5 → DR12`.

---

## 7. Phase A: the deferred set executed once (item 5; D35, D36)

A phase A run is one `call_models` and never reaches the output path, so under the per-run deferral its
deferred nodes' outputs were left uncomputed. `PROCESS_ARCH_DEFER_PER_RUN_EXECUTION` says where the
per-run set is executed once: `output_path` (unset; phase B's place) or `evaluation_exit`, at the exit of
the evaluation on the converged state. The harness composes `evaluation_exit` for `A2` alone. The
execution is one dispatch sweep over the set, **measured, not charged**: the per-run nodes' census reads 1
and the paper's `A2` post-processing cell is that measured 1 (V4's by-construction charge is retired). The
flat arms do not defer; their final sweep computes every node at the converged state (D35).

With the set executed, the **whole-state exit audit** is phase A's matched-accuracy statistic (D36; rule A1),
and the restricted statistic's gate G4 retired when the two agreed on the gate job set. **In phase B** the
audit snapshot is taken at the entry to `write_output_files`, *before* the deferred per-run nodes' one
execution there, so on `B2` the whole-state statistic reads large on the components those nodes own; the
optimisation tally prints it as context with the restricted statistic beside, and no phase B rule reads it.

---

## 8. The warmed evaluation child

A phase A record is one evaluation in a fresh process, so numba's per-process cache load used to land in
its module rows. The child (`child/evaluate.py`, A91's form) now runs a **discarded warm-up** evaluation on
the same entry, puts the whole data structure back to the entry snapshot (D25's mechanism, refused if any
field still differs), re-enters the coupling state bit-exact, resets every driver counter, and times the
**measured** evaluation. Both evaluations' count leaves and exit-state digests are stamped under
`evaluation_warmup` and the record is refused where they differ, so every phase A record carries its own
determinism check. The fixed per-run term ends at the warm-up's first evaluation. Gate `evaluation_warmup`
compares the cold child's records of the gate job set's evaluation half (archived on its first press) with
the warmed child's: every count and every exit-state component identical, each warmed record's check
re-derived. **Phase B is not warmed**: a run's first evaluation carries the cache load inside its module
rows; the paper's phase B wall-clock caption states its size from the `cache_load` timing stage (§9).

---

## 9. The wall-clock instrument and the timing stages (DR12; D33, D38, D41, D42)

`PROCESS_ARCH_TIMERS=on` makes the driver copy accumulate, per run, the wall of every node call, every
sweep of the dispatch body, the block loops' convergence test, the objective-and-constraints layer, every
`call_models`, the once-per-run set-up, the solve phase and the output path; unset, every hook is one
`is None` test (G1 byte-identical). The harness harvests the accumulators **before** its audit and names
its own costs apart (the audit sweep, the snapshots, the record assembly, its set-up; `timers.excluded`).
The rows (`timing.rows_of`): `M1`, `M2`, `M3`, `Feedforward`, `Post-processing` (model time through the
node map), `MDA convergence test`, `dispatch`, `objective and constraints`, phase B's `optimiser own time`
and `fixed per run`, the `unattributed residual`, and `Total`. **Context, never evidence**: no verdict
reads a number from here.

The campaign ran with the timers on at W = 4 and then 3, children single-threaded (D38). The stages
(`--timing <stage>`, records stamped `timing` under `runs/timing/`, never pooled):

| stage | what |
|---|---|
| `repeatability` | GC's job set three times at W = 1: per row the median and `[min, max]`; a job whose repetitions differ in any count is refused |
| `timers-off` | the same set once with the timers unset at W = 1: the instrument's own cost |
| `validity` | D38: is the campaign's timing of those seeds inside the repetitions' range? (A102: 21 of 22 outside; by **D42** the appendix reports the campaign's timings with the check's rows beside, and D38's one-worker remedy is not run) |
| `seed-set` | D38's remedy as built: the campaign's jobs re-run at W = 1 with the timers on, counts compared with the campaign record (`paper_tables.WALL_CLOCK_TIMINGS_FROM = "validity"` would read it; not used) |
| `cache-load` | phase A's warm-up less measured model time per arm, and phase B's module time per run beside: the first evaluation's cache load, which the phase B caption quotes |
| `tables` | the three appendix tables over the repeatability records, as test data |

The paper's wall-clock tables are built the way the count tables are (**D41**): phase B over the seed set
on which every arm reached an accepted optimum, phase A over the 25 paired evaluations; ratio of the means
and the per-run median with `[min, max]`; the caption prints the worker counts the records are stamped with.

---

## 10. The chain, the supplementary stage, the tally and the paper's document

**The chain** (`chain.py`) is one sequence with two parameterisations: the entry references (one flat `A0`
evaluation per configuration from the committed input file's design point), the displaced-entry
evaluations of every phase A arm, the optimisations of every phase B arm, then the **reading stages** —
`tally_evaluation`, `tally_optimisation` and gate `tally_contracts` (`chain.run_reading_stages`). The
**smoke** runs it on one seed and the cheapest configuration with every record stamped `smoke`; the
**campaign** on every configuration and the plan's seeds, stamped `campaign`, refused unless
`EXECUTION_APPROVED` (the user's dated approval) and composed with the timers on
(`experiment_runner.campaign_press_composition`). `--reading-stages campaign-press` presses the reading
stages alone over the records on disk under that composition, and `--reading-stages plain` under the
gates' — no run stage, no PROCESS run (issue I-37).

**The supplementary stage** (`config.SUPPLEMENTARY_STAGES`; `--supplementary st_census_exact`): `B0` and `B2`
on `st_regression` under the census set at **τ = 1e-12**, the rung where the census loops read exact and
the optimiser's path returns (A96). Its records are stamped `supplementary` under
`runs/supplementary/<name>/`, carry their own τ in the job identity, and are **reported beside the
campaign, never pooled** (`measurement/tally_supplementary.py`, `--measure tally_supplementary`).

**The tally** (`--measure tally_evaluation`, `tally_optimisation`, `tally_supplementary`) summarises the
records into captioned tables over one declared population per phase (`tally.published_sources`: the
campaign's own job sets once a campaign record exists) and writes a stage record naming every record it
read (trap T14). Against the plan's rules (§5):

- **A1** (matched accuracy): the whole-state audit per arm, the declared pair within F = 10 at median and p90,
  and 0 components above τ on every accepted run; **A2**: the fixed-point distance between arms, reported.
- **B1** (the same optimum): the paired relative `norm_objf` difference against `max(F × yardstick, floor)`
  at median and p90, the yardstick `BR → B0` (`same optimum (B1)`), **with its attribution**: per seed of
  the seed set, each ladder step's (`B0 → B1` the lift, `B1 → B2` the partition; on `st`, `B0 → B2`) and
  each judged pair's objective and design-point difference, a **hop** (objective above the floor) or a
  **relocation** (within the floor, the point moved), the retried arms, and the step the difference enters
  at (`same optimum per seed and rung`); one row per configuration and pair with the verdict and those
  counts (`same optimum by rung`), which the paper's verification row reads.
- **B2** (cost): solve-phase node calls and module sweeps per run on the one seed set, with and without the
  retried seeds, the audit's sweep subtracted symmetrically; **B3**: `R = ρ × ε` per configuration
  (`the optimiser's path over the configurations`) and the iterations in both constructions with ε and
  the plan's **label** beside it (`iterations and ε (B3)`: `|log ε| ≤ log 1.05` → trajectory-neutral, else
  trajectory changed by ε) — **no verdict**, V4's iteration multiplier is retired (V5 list item 1);
  **B4**: constraint 93's residual; **B5**: the per-arm success table, reported.

**The paper's document** (`--paper-tables show | check | write`; `measurement/paper_tables.py`) writes
`paper_tables.md`: the switch matrix (its stopping-rule cell from the campaign's test set and τ), the
configurations table, phase A module sweeps per evaluation (`A2/A1`, `A2/A0` on `st`), phase B optimiser
iterations and module sweeps per optimisation (`B2/B0`), and the appendix — the wall-clock tables with the
validity check's rows, the per-arm success table and **one verification table** (G0, G1, A1, A2, B1 with
its attribution, G6, G5, G9, GT; the gates' verdicts read through the `gate_table` stage record, refused
when the verdict records have moved since). Before writing, every cell the stage records also hold is
compared exactly (`cross_check`, with a tooth on each side). `check` refuses unless the file is
byte-identical to a fresh rendering. **`paper_cells_recount.py`** recounts the phase A, iterations,
phase B module and per-arm success cells from the raw `metrics.json` files with no import of `harness/`,
and prints a mismatch count.

---

## 11. The gates

A gate checks something about the tree or the records and has **teeth**: deliberate faults it must catch,
so its zeros are shown capable of failing (protocol §12). A failed gate is a result, never tuned around.
`--gates` lists the registry; `--gate all` runs every gate in dependency order, cheapest first; the
`gate_table` stage (`--measure gate_table`) collects the verdicts. **29 gates** at A103:

| gate | plan | binds | PROCESS runs |
|---|---|---|---|
| `g0prime` | G0 | the copy's `process/models/` byte-identical to `c0ae5b28` | no |
| `copy_identity`, `edit_behaviour` | — | the copy's `process/` against its source commit, byte for byte, with the permitted edits declared; the one edit that is not a rename or a comment behaves as declared | no |
| `self_containment` | — | nothing in the package imports from or calls into `idf_probe/` or `fixedpoint/` | no |
| `composition`, `rungs`, `provenance`, `data`, `run_path`, `capability`, `stage_provenance` | — | the harness itself: arm composition, the matrix and the rungs, the git stamps, the committed data, the record's run path, the tree's switches, the stage-record stamps | no |
| `resume_identity` | — | every `--resume` decision and every directory of the shared pool | no |
| `artifacts_check`, `artifacts_derive_inputs`, `artifacts_census`, `artifacts_per_run` | — | the committed artifacts, the lifted input files, the write census, the per-run deferral sets | the last three |
| `evaluation_warmup` | — | the warmed evaluation child (§8) | yes |
| `record_completeness` | G7 | a forced-unconverged run carries every declared field, the timer fields included | yes (its tooth re-makes one smoke evaluation on every press) |
| `count_neutrality` | GC | each count-neutral driver change (§6) | yes |
| `prime_map` | G2 | the prime in its once-per-evaluation form (§6) | yes |
| `entry_and_warm` | G6 | phase A entries bit-identical across arms per seed; the warm criterion at V5's τ on the census set | yes |
| `test_set` | GT | the census test set binds (§5) | yes |
| `switch_composition` | G5 | `B2` composed from the matrix equals `B2` composed switch by switch | yes |
| `switch_neutrality` | G1 | each driver change, per change: every switch unset, outputs identical to the pre-change commit | yes |
| `reproduction` | GR | the copy at its copy commit reproduces V4's twenty reference records bit for bit — **run once** (`registry.RUN_ONCE`); later presses read its verdict at `d6c246a1` | no (read-once) |
| `output_path` | G9 | the output-time loop's removal on `B1`/`B2` | yes |
| `written_file_gap` | — | the written-file gap on the one-call output path (issue I-21) | yes |
| `tally_contracts` | — | every tally table carries a caption and a real denominator, no acceptance table a timing; the tally reproduces V4's published cells on GR's twenty runs (236 cells), and resolves those runs to the same directories under every instrument switch (I-37) | no |
| `run_kind_separation` | — | every record's run kind, and every population the tally builds | no |

Dropped in V5: G3/G3c (the prime's cold chain), G8 (the `mixed` ruler), G4 (retired, D36), the second
implementation's `recomputation`. The measurement stages beside the gates: `gate_table`, `exclusion_review`
(G1's exclusion tables reviewed), and the three tallies. `--selfcheck` runs the harness's own checks with
their teeth and no PROCESS run.

**Gate records are reused** (harness plan amendment 15): a task seeds its `runs/` with the latest relocated
records and presses `--gate all --resume`; a gate is re-made from scratch only where a change alters what
it reads. G1 and GC compare two sides made at two commits and read their archived straddles.

---

## 12. Where records live: one folder per run ID, and what a record is

Everything under `runs/` is untracked. **Summaries and verdicts are committed; raw records are not**, so a
number is only published from a committed script and a record that exists only in `runs/` must be relocated
before a worktree is retired (`arch_surgery/bin/retire_task_worktree.sh`; the relocated trees are under
`arch_surgery/idf_probe/runs/`).

**The run ID** (task A107 (v5-campaign-settings-keys)). A campaign's settings — its test set and its
tolerance, or its tolerance rule — name a **run ID** (`config.run_id_for`): `<test set>_tau<τ>` without a
rule, `<test set>_rule_<rule>` under one, τ printed as Python's `repr` (the shortest string that reads back
as the same float) — `census_tau1e-08`, `write_set_tau1e-06`, `census_rule_epsvmc_times_epsfcn`. Injective
over the settings the harness admits: the test set is one of two declared names, what follows is `_tau`
and a round-tripping float or `_rule_` and a declared rule. The timers (a property of the press, not the
campaign) and a supplementary stage's own τ (in its jobs) are not in it. **Every record a press makes or
reads lives in that run ID's folder**, `runs/<run ID>/` — `Campaign.runs_dir` is that folder, so every
path the harness derives from it lands inside, and every job identity renders its paths relative to it
(a folder moved whole keeps every digest). Every entry point takes the settings as before (`--test-set`,
`--tau`, `--tau-rule`; the default is the declared default campaign, `census_tau1e-08`), resolves the run ID
from them and prints it first; there is no `--run-id`.

```
runs/
  _numba_cache/  _mplconfig/          shared caches (config.SHARED_CACHES)
  census_tau1e-08/                    the V5 campaign (adopted, A107)
    run_settings.json                 the settings this folder is of
    campaign/ supplementary/ gates/ timing/ single/ smoke/ census/ census_test_sets/
    artifacts/ input_files/ reading_stages/ _press_logs/
  write_set_tau1e-06/                 a second campaign's folder: the same tree
    run_settings.json  archived_records_copied.json  gates/ input_files/ smoke/ …
```

| under `runs/<run ID>/` | what |
|---|---|
| `run_settings.json` | the folder's settings (`run_layout`): written on the first press under them, or by the adoption with the evidence that decided it; a press whose settings disagree with it is refused |
| `campaign/entry_references/`, `campaign/evaluation/<configuration>/<arm>/seedNNN/`, `campaign/optimisation/…` | the campaign's records (553 in `census_tau1e-08`: 3 entry references, 275 evaluations, 275 optimisations) and `campaign/press.json` |
| `smoke/` | the smoke chain's records and `smoke/press.json` |
| `supplementary/<stage>/<configuration>/<arm>/seedNNN/` | the supplementary stage's records, pressed beside this run ID's campaign |
| `gates/_runs/` | the shared pool: every gate's runs, one directory per job digest. A job that names no directory resolves here, or by digest to a record elsewhere **in this run ID's folder** — never into another gate's root `gates/<gate>/` (issue I-36), never into another run ID's folder |
| `gates/<gate>/gate.json`, `gates/<stage>/measurements.json` | the verdict records and the measurement stages' records (the tallies, `gate_table`), each stamped with the run ID (`run`) |
| `timing/<stage>/` | the timing stages' records and their `measurements.json` |
| `census/`, `census_test_sets/` | the census stage's runs and the derived artifacts |
| `single/` | `--run` records and the smoke pairs; `artifacts/`, `input_files/` the artifact stages' output |
| `reading_stages/<composition>/` | `--reading-stages` presses written with `--outdir` (A103) |
| `_press_logs/` | the terminal output of every press a task makes under this run ID, by task and number |
| `archived_records_copied.json` | where the read-only records came from (below), every file's SHA-256 |

**What is shared, and why it is safe.** Only `_numba_cache/` and `_mplconfig/` at the top level of `runs/`:
pure caches that carry no result (numba's compiled functions keyed by source digest; matplotlib's font cache),
so a new run ID does not start with a cold compile and nothing a record says depends on them.

**Isolation, enforced in the pool.** Step 2 of `pool.directory_for` — the by-digest search — searches
`pool._record_index`, which is built over this run ID's folder alone; a job that *names* a directory in another
run ID's folder is refused by `pool.refuse_another_runs_folder`, through which every pool entry resolves, before
any directory is made or removed; `--outdir` into another run ID's folder is refused by the runner. Gate
`resume_identity`'s tooth *a job never resolves into another run ID's folder* and the acceptance check
`--run-isolation smoke` (`harness/run_isolation.py`: the smoke pressed under one run ID, every other run ID's
folder compared by path, size, modification time and run-record SHA-256 before and after) bind it. A stage record
stamped with another run ID is refused by its readers (`run_layout.assert_stage_record_is_of_this_run`: the
gate table, the paper's document); one with no stamp was made before the layout and is read as the folder's.

**Read-only records reach a new run ID by an explicit copy**, `--copy-archived-records <from run ID>` (a
listing; `--apply` copies; `harness/gates/archived_records.py`): the reproduction gate's verdict at the copy
commit and its job set's pool records, gate GC's straddle records and both labelled sides, gate G1's `before`
capture and archived straddles, the warm-up gate's cold-child records, the derived input files. Copied to the
same relative path, a record is the same job by construction (a shared area outside the folder would render
its paths against another root and the gates would make it again); copies, not hard links (a re-press rewrites
a verdict in place); every file's SHA-256 checked; afterwards the gates' job sets are composed under the
destination and must resolve and decide exactly as under the source, job for job. About 470 MB per run ID.

**The layout before run IDs** (everything directly under `runs/`) is refused by every stage, naming
`--adopt-records-layout`: a listing of the move, decided by the **campaign records'** job-identity settings
(gate, smoke, timing and supplementary records carry settings of their own by design and are carried along,
counted); `--apply` renames each entry into `runs/<run ID>/` on the same filesystem and compares a manifest of
every moved file (path relative to the entry, size, modification time, run-record SHA-256) before and after.
A tree whose campaign records carry more than one setting is refused with the list.

**The listing**, `--runs`: each run ID's settings, its campaign records by phase and status and the commits
they were made at, its run-record count, and whether its gate table, tallies and tables document exist. No
comparison between run IDs: the user compares from the folders.

A record (`metrics.json`, schema `core/records.py`) carries what was run (the job identity and digest, the
composed environment as the driver resolved it), where (interpreter, tree, commit, dirty state), what it
cost (node calls in total, per node and per attempt; sweeps; predicate evaluations), what it achieved
(`norm_objf` as a hex float, `ifail`, the exit audit with its position and instrument), how it ended (one
outcome of the taxonomy), and — with the timers on — the `timers` and `launcher` blocks. **A record's arm name
is the name at the time of the run** (trap T16): records made before 2026-09-15 are read through
`records.RECORDED_ARM_NAMES`, only through `records.read`.

---

## 13. Pressing each stage

Every command from this folder with `/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python` and
`PYTHONDONTWRITEBYTECODE=1`; add `--resume` to keep existing records (the tallies and the paper's document
refuse records from other commits without it).

```bash
python experiment_runner.py                          # preflight: interpreter, tree, configurations, the matrix, capability
python experiment_runner.py --selfcheck              # the harness's own checks with their teeth
python experiment_runner.py --gates                  # the registry: gates, measurement stages, teeth
python experiment_runner.py --gate all --resume      # every gate, cheapest first (G7's tooth makes one smoke run)
python experiment_runner.py --gate tally_contracts --resume
python experiment_runner.py --jobs <gate>            # one gate's jobs by identity, and whether --resume keeps each
python experiment_runner.py --jobs campaign          # the campaign press's jobs, composed as the press composes them, and whether --resume keeps each
python experiment_runner.py --measure gate_table --resume
python experiment_runner.py --measure tally_evaluation --resume
python experiment_runner.py --measure tally_optimisation --resume
python experiment_runner.py --measure tally_supplementary --resume
python experiment_runner.py --reading-stages campaign-press --resume --outdir runs/reading_stages/campaign_press
python experiment_runner.py --paper-tables write     # then: --paper-tables check
python paper_cells_recount.py                        # the independent recount of the paper's cells
python experiment_runner.py --census take --resume   # the census stage (write: also into harness/data/)
python experiment_runner.py --timing validity        # repeatability | timers-off | validity | seed-set | cache-load | tables
python experiment_runner.py --supplementary st_census_exact --resume
python experiment_runner.py --smoke                  # the chain once, one seed, cheapest configuration, smoke records
python experiment_runner.py --campaign --resume      # the campaign (refused unless EXECUTION_APPROVED)
python experiment_runner.py --run --arm B2 --configuration st_regression --seed 0   # one run, never a campaign record
python run_stamp_survey.py                           # the commit of every record under runs/ (--runs runs/<run ID> for one)
python experiment_runner.py --runs                   # the run IDs on disk and what each holds
python experiment_runner.py --adopt-records-layout   # re-lay runs/ in the old layout under its run ID (--apply to do it)
python experiment_runner.py --test-set write_set --copy-archived-records census_tau1e-08 --apply   # a new run ID's read-only records
python experiment_runner.py --test-set write_set --run-isolation smoke   # the smoke under that run ID, nothing else touched
```

`--test-set write_set` (or `--tau`, or `--tau-rule <name>`) sets the campaign-level test set or tolerance for any press, and so
**the run ID and its folder** (§12); `--outdir` sends a gate's or stage's records elsewhere (never into another run ID's
folder); `--no-teeth` skips a gate's teeth and says so in the verdict. `paper_cells_recount.py` reads `runs/census_tau1e-08/`
unless `--runs` names another run ID's folder (with `--document paper_tables_<run ID>.md`).

---

## Change log

- **2026-10-01, A107 (v5-campaign-settings-keys):** the run-ID layout (§12): one self-contained folder per campaign
  settings under `runs/`, named by `config.run_id_for`; the shared caches at the top level; `run_settings.json`, the
  guard, the run-ID stamp on every verdict and stage record, the adoption (`--adopt-records-layout`), the listing
  (`--runs`), the archived-records copy (`--copy-archived-records`), the acceptance check (`--run-isolation smoke`),
  the tables document per run ID; A105's rule-named chain root `runs/campaign_tau_rule_<rule>/` replaced by the run ID.

- **2026-09-30, A103 (v5-tally-and-tables):** rewritten to V5's text (V5 plan §8): V4's sections on the
  second implementation, the report renderer, the predicate-mode gate, the cold chain, the stencil regime
  and the function-weighted tables removed; the matrix with its stopping-rule form, the test set and census,
  the schedule and the prime, phase A's once-execution, the warmed child, the timers and timing stages, the
  supplementary stage, rule B1's attribution and B3's label, the reading stages (I-37), the 29 gates, the
  commands and the records layout written from the code at this commit. A101's and A102's sections (V4 README
  §§17–19) are folded into §§5, 7–10.
