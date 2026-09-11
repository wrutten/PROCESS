# A60 (driver-attempts) — per-attempt node-call accounting across the optimiser's retry ladder

> **Document status** — **OPEN.** The task report of `A60 (driver-attempts)`, driver change **DR7**
> of the approved V4 harness plan and the last change to V4's own copy of PROCESS. Written on the
> branch `A60-driver-attempts`; it is archived to `docs/reports/deprecated/` when the branch merges,
> at which point the folder records its lifecycle and this header records its validity (trap T3).

---

## 0. What this task did, and the words it uses

**In one sentence.** PROCESS does not call its optimiser once — when the optimiser returns anything
but "converged" the driver calls it again, up to three more times, under different settings — and
until this change the run record said how many of those *attempts* there were and how each one
ended, but charged all of their model evaluations to a single run total. This task makes the driver
stamp its cost counters at every attempt boundary, so the cost decomposes per attempt, and makes the
measurement harness refuse any record whose parts do not add up to the whole they replace.

**Vocabulary, spelled out once** (orchestration protocol §4 — a report should read without the queue
open beside it):

| term | meaning |
|---|---|
| **the driver** | the part of PROCESS that arranges solvers and optimisers — `process/core/caller.py`, `process/core/solver/`. It is the only thing this experiment changes; every physics and engineering model is frozen at base commit `c0ae5b28` (decision D5) |
| **V4's copy** | `arch_surgery/MDA_partitioning_experiment_v4/PROCESS/` — this revision of the experiment runs its own copy of the PROCESS package (decision D20), and every driver change is made there, never in the repository-root `process/` |
| **DR7** | the seventh row of the V4 harness plan's driver-change table (§3.2): *per-attempt node-call accounting*. Approved by the user on 2026-09-10 |
| **the retry ladder** | the sequence of optimiser calls in `SolverHandler.run`: the optimiser, then the same problem with a larger finite-difference step, then a smaller one, then a reset second-derivative matrix. §2 gives it exactly as the code has it |
| **attempt** | one call of the optimiser inside that ladder. A run has between one and four |
| **retried seed** | a start whose run made more than one attempt. The experiment plan publishes every cost ratio *with and without* the retried seeds |
| **node call** | one execution of one model. The cost unit of every Phase B table. `node_calls_solve_phase` is the count up to the moment the output path is entered |
| **sweep** | one walk of the model sequence (`_call_models_once`). `dispatch_sweeps` counts them over the whole run |
| **`ifail`** | the optimiser's exit code. 1 is "converged"; 5 is "no solution found" |
| **`epsfcn`** | the relative step the optimiser's finite-difference gradient uses |
| **G0′** | the gate that checks the copy's `process/models/` is byte-identical to the frozen base commit, at every commit |
| **G1** | the switch-neutrality gate: with every architecture switch unset, the copy after a driver change behaves byte-identically to the copy before it |
| **GR** | the reproduction gate: twenty runs reproducing the previous revision's records value for value |
| **tooth** | a deliberate break a gate must catch. A gate whose failure mode has never been exercised is an assertion, not a measurement (protocol §12) |
| **configuration** | one optimisation problem. Three of them: `large_tokamak_nof`, `low_aspect_ratio_DEMO`, `st_regression` |

---

## 1. Verdict

**DR7 is in V4's copy of PROCESS and the harness reads it back. Every gate passes.**

*Caption: one row per gate or check run for this task, with its verdict, its population and its
denominators. "Teeth" is the number of deliberate breaks the check was shown to catch. Every number
comes from executing a committed script at the commit named in §9's change log; the commands are in
§8.*

| check | verdict | numbers |
|---|---|---|
| **G0′** — the physics stays frozen in the copy | **PASS** | 77 model files compared byte for byte against base commit `c0ae5b28` (read with `git cat-file`, never a working tree), plus the file set; **76 identical**, 1 differing — `process/models/pulse.py`, the one structural edit decision D14(b) approved, pinned by sha256. **4 teeth** |
| **copy identity** — the copy is its source commit's `process/` plus the recorded edits | **PASS** | 224 files, **217 identical**, 0 missing, 0 added, **0 unexplained differences**; the seven that differ are the six permitted-edit files and `pulse.py`, each with its recorded hunks and post-edit sha256. **4 teeth** |
| **`PROCESS_diff.py`** | **exit 0** | 7 changed files, **0 unexplained hunks**; the unannotated-hunk tooth trips |
| **G1** — switch neutrality, `582d7a0d` → `7f4ce958` | **PASS** | 6 run pairs (3 configurations × 2 reference arms, seed 0); **0 of 2 326** deterministic record values differ, **0 of 51 319** output-file lines differ; 1 432 record values and 45 lines excluded, each named with its reason. **4 teeth** |
| **GR after DR7** — the reproduction gate | **PASS** | **20/20** runs reproduced, **270/270** compared values identical with no tolerance; record contract **20/20**; substitutes `A0p` PASS (2 pulsed configurations, 1 skipped with the reason recorded) and `AR` PASS (12/12). **7 teeth** |
| **the attempt-summation identity**, on GR's own records | **holds on all 14** | `Σ attempts.node_calls_solve_phase == node_calls_solve_phase` **and** `Σ attempts.sweeps == dispatch_sweeps_solve_phase`; **14 of 14** optimisation records decompose, largest \|residual\| **0** node calls and **0** sweeps; **0** node calls and **0** sweeps of the solve phase fall outside every attempt, on every one of the 14 |
| **the ladder exercised** (a demonstration, not a gate) | **3/3** | **0 of GR's 14 runs retried**, so the identity above is checked with one term per sum. Three deliberately budget-capped runs make the driver climb the ladder: **3 attempts each**, the identity still exact — **3 of 3** decompose with residual 0 |
| `experiment_runner.py --selfcheck` | **PASS** | 6/6 checks |

**The one result worth reading twice.** Every run of the reproduction gate converges on its *first*
attempt — **0 of 14 retried** — so `n_attempts = 1` everywhere, the share of node calls spent in
attempts that did not produce the accepted optimum is **0.00 % on all fourteen**, and check 2's two
constructions are **identical on all fourteen**. That is a fact about this population, not about the
optimiser: the reproduction gate runs seeds 0 and 1 only, and the retry the whole change exists for
is a seed-dependent event that `A44 (transfer-gap)` found on exactly one seed of one arm of one
configuration in a 25-seed campaign. Reporting the zeros without that sentence would be trap
**T11**'s exact shape — a number published without the condition that limits it — and it is why §5
carries the budget-capped runs beside them, where the ladder does run and the identity is checked
with three terms instead of one.

---

## 2. The retry ladder, as the code has it

All line numbers are in **V4's copy**, at this branch's tip. The ladder is one method:
`arch_surgery/MDA_partitioning_experiment_v4/PROCESS/process/core/solver/solver_handler.py`,
`SolverHandler.run` (**line 63**). It is reached once per problem —
`scan.Scan.doopt` → `SolverHandler.run` — and once per scan point on a parameter scan; the three
configurations this experiment runs are single problems and enter it once.

*Caption: one row per rung of the ladder, in the order the method tries them. "Trigger" is the
condition on the **previous** rung's result that makes this one run; "settings" is what differs from
the attempt before it. Read from the code, not from documentation: every line number is a line of
`solver_handler.py` in V4's copy at this branch's tip.*

| # | stage | trigger | settings | file:line |
|---|---|---|---|---|
| 1 | `initial` | always | the input file's own `epsfcn`; the optimiser's own initial second-derivative matrix | `solver_handler.py:100` |
| 2 | `epsfcn_x10` | attempt 1 returned `ifail != 1` | `epsfcn × 10`, restored on exit of the attempt | `solver_handler.py:108-109` |
| 3 | `epsfcn_x0.1` | attempt 2 (or 1, if 2 did not run) returned `ifail != 1` | `epsfcn × 0.1` **of the restored value**, not of attempt 2's | `solver_handler.py:114-115` |
| 4 | `hessian_reset_b2` | the previous attempt returned `ifail == 5` **and** `n_solver_iterations < 2` | the second-derivative matrix set to twice the identity; `epsfcn` back at the input file's value | `solver_handler.py:123-134` |

Two things about this table are worth stating because they are easy to get wrong from a reading of
the plan. First, **rungs 2 and 3 are not nested**: `epsfcn_context` is a context manager that
multiplies on entry and divides on exit, so rung 3 runs at one tenth of the *original* step, not at
one tenth of ten times it. Second, **rung 4 is conditional on two things**, an exit code and an
iteration count, so a run can end after three attempts with `ifail = 5` and never reach it.

**The attempt boundary** is the pair of instants immediately around each of those four calls to
`self.solver.solve()`. Nothing else in the run evaluates the model set: the work before the ladder
(`load_iteration_variables`, `load_scaled_bounds`, building the evaluator) touches no model, and the
work after it (`SolverHandler.output`, `constraints.constraints_output`) evaluates constraint
functions from state that is already there. That is the premise the whole decomposition rests on,
and §5 measures it rather than asserting it.

### 2.1 What the stamp is

`process/core/caller.py` gains, in the block of counters where `NODE_CALLS` and `DISPATCH_SWEEPS`
already live:

| name | line | what it is |
|---|---|---|
| `ATTEMPT_LADDERS` | `caller.py:986` | ladders entered, one per call of `SolverHandler.run` |
| `ATTEMPT_STAMPS` | `caller.py:992` | the boundary stamps themselves, in order |
| `open_ladder()` | `caller.py:995` | begins a ladder and returns its number |
| `attempt(stage)` | `caller.py:1016` | a context manager that stamps the entry and, **in a `finally`**, the exit |
| `DISPATCH_SWEEPS_AT_OUTPUT` | `caller.py:748`, frozen at `caller.py:2297` | the sweep counter frozen by the same statement that already froze the node counter |

One stamp records four readings: `NODE_CALLS[0]`, `DISPATCH_SWEEPS[0]`, a copy of the
per-evaluation sweep histogram and a copy of the per-block sweep totals. At most eight stamps are
taken in a run. No float is touched, no arithmetic a result depends on is done, and nothing here is
reachable from a branch any model or solver takes — which is the claim gate **G1** tests rather than
this paragraph.

The exit stamp is taken in a `finally` deliberately. An attempt that **raises** would otherwise leave
the list with an entry stamp and no exit, and a decomposition missing its last attempt is a *partial*
one — which the record module refuses, correctly but uselessly, on what is really a crash.

**Why `DISPATCH_SWEEPS_AT_OUTPUT` had to exist.** The per-attempt sweep counts need a whole to add up
to, and the run's sweep total is not it: `dispatch_sweeps` includes the output-time loop and the exit
audit, both of which happen after the last attempt exits. Freezing the sweep counter where the node
counter was already frozen gives the sweeps the same solve-phase whole the node calls have, and the
two identities then have the same shape.

**Where the stage names live.** In `solver_handler.py:34`, beside the four branches that implement
them — not in the harness. The harness has had a positional guess at the ladder's stages since the
run path was written (`child.LADDER`); it is kept, now under `attempts[].stage_positional`, and the
two are compared per attempt rather than assumed equal. A ladder that gains a rung therefore cannot
keep the old vocabulary silently.

---

## 3. What a record now carries

### 3.1 `attempts[]`

*Caption: one row per key of each element of the run record's `attempts` list, which has one element
per attempt in the order the ladder tried them. "Source" says which side of the measurement supplies
it: the **harness's** wrap of every solver's `solve` (`child.install_exit_forensics`), or the
**driver's** boundary stamps (DR7). Units: node calls are model executions, sweeps are walks of the
model sequence.*

| key | source | what it is |
|---|---|---|
| `attempt` | harness | 1-based index within the ladder |
| `stage` | **driver** | the ladder's own name for the rung: `initial`, `epsfcn_x10`, `epsfcn_x0.1`, `hessian_reset_b2` |
| `stage_positional` | harness | the harness's positional guess at the same name, kept so the two can be compared |
| `ladder` | **driver** | which ladder this attempt belongs to; 1 for a single problem |
| `epsfcn` | harness | the finite-difference step the attempt entered with |
| `n_iterations` | harness | the optimiser's iterations in this attempt |
| `ifail` | harness | this attempt's exit code |
| `raised` | harness | the exception type, if the attempt raised; null otherwise |
| `node_calls_solve_phase` | **driver** | model executions inside this attempt |
| `sweeps` | **driver** | sweeps of the model sequence inside this attempt |
| `sweeps_by_block` | **driver** | those sweeps per block of the schedule; an empty mapping where the arm runs none |
| `sweeps_per_eval` | **driver** | the attempt's own evaluations of the model set and the sweeps they took, binned — `{hist, n_evaluations, n_sweeps}` |

Two top-level fields go with it. **`attempts_node_calls_available`** says whether the driver stamped
this run's boundaries; it was `false` on every record before this task and is now `true` on every
optimisation record and `false` on every evaluation record, which run no optimiser.
**`dispatch_sweeps_solve_phase`** is the sweep total the per-attempt sweeps decompose, beside the
`node_calls_solve_phase` the per-attempt node calls decompose.

### 3.2 `attempt_accounting` — the decomposition, published with its residual

`attempts[]` is the table; `attempt_accounting` is the arithmetic that makes it believable. It
carries, per run: the number of attempts and whether the run **retried** (`n_attempts > 1` — the
flag the experiment plan's "with and without retried seeds" ratios are computed from, and it is
derivable from `attempts[]` alone, so nothing downstream depends on this field's existence); the
stages, exit codes and iteration counts as lists; and a `sums` block giving, for each of the two
quantities, the per-attempt values, their sum, the run total, and **the residual**.

Beside them it publishes `outside_attempts`: the node calls and sweeps of the solve phase that fall
**before the first attempt is entered or after the last one exits**. That is §2's premise — nothing
evaluates the model set during the solve except the optimiser — turned into a measurement. A future
driver change that put model work between the ladder and the output path would show up there as a
non-zero term instead of silently unbalancing the sum.

It also carries `stage_names_agree_with_position` (the driver's rung names against the harness's
positional guess, per attempt) and `sweeps_agree_with_the_evaluation_histogram` (each attempt's
dispatch sweeps against the sweeps its own binned evaluations account for). Both are consistency
checks that cost nothing and are published rather than assumed.

### 3.3 Phase A says so explicitly

An evaluation-phase record has `attempts: []` — and now also an `attempt_accounting` block whose
`applicable` is `false` and whose `why` says: *"this phase runs one evaluation of the model set with
no optimiser in the process, so there is no retry ladder, no attempt, and nothing for a per-attempt
cost to decompose."* The empty list was already there; what was missing was the sentence that tells
a reader of two records apart — "this phase has no optimiser" from "this run stopped before it had
one".

### 3.4 The refusal

`records.assert_attempt_summation` now enforces, on **every** record that goes through
`records.assert_usable`:

    Σ attempts[].node_calls_solve_phase == node_calls_solve_phase
    Σ attempts[].sweeps                 == dispatch_sweeps_solve_phase

A record where either fails is **refused**, not rounded, not warned about. So is a record where some
attempts carry a cost and others do not, because a partial decomposition cannot be summed. A record
whose attempts carry no cost at all — an evaluation, or a run that crashed before the driver stamped
anything — is passed over rather than refused, since there is nothing to add up.

The refusal was written by `A50 (harness-run)` against a driver that supplied nothing, so until now
it ran only against a synthetic tooth. It now runs against real numbers on every optimisation record
the harness makes; §4.3 reports what it found on GR's fourteen.

---

## 4. The gates, with their numbers

### 4.1 G0′ — the physics stays frozen in the copy

**PASS.** 77 files under `PROCESS/process/models/` compared byte for byte against base commit
`c0ae5b28`, read with `git cat-file` and never from a working tree, plus the file set itself.
**76 identical**; the one that differs is `process/models/pulse.py`, the structural edit decision
D14(b) approved, whose post-edit sha256 is pinned so a *further* edit to it fails too. Four teeth
trip: a one-byte change to a model file, a model file removed, a model file added, and a further
change to the approved file. Nothing in this task touches `process/models/` or the repository-root
`process/`.

### 4.2 G1 — switch neutrality across the driver change

**PASS.** The `before` capture was taken at **`582d7a0d`** — the branch point, with the copy's driver
byte-identical to the tip of `architecture_surgery`, verified by `git diff` before any edit — and the
`after` capture at **`7f4ce958`**, the commit at which the driver change and the harness's readback
of it were both in place. Both are the two reference arms (`BR`, an optimisation, and `AR`, an
evaluation) at seed 0 on all three configurations: six run pairs.

*One commit later than the `after` capture* is `078f1936`, this branch's last code commit. It
touches **`harness/gates.py` only** — the measurement stage of §5 and the wording of one exclusion's
reason — so it changes neither the copy's driver nor anything a run records, and re-capturing at it
would compare the same two records. The commit and the capture are named separately here rather than
rounded to "the tip", because a gate that says which commits it compared is the only kind whose
claim can be checked.

| | number |
|---|---|
| run pairs | **6** = 3 configurations × 2 reference arms |
| deterministic record values compared | **2 326** |
| record values **differing** | **0** |
| output-file lines compared | **51 319** |
| output-file lines **differing** | **0** |
| record values excluded, each named with its reason | 1 432 |
| output-file lines excluded (date, time, user, path, version, branch, runtime) | 45 |
| teeth | **4**, all tripped |

The four teeth: two captures audited at different positions must **refuse** rather than compare; one
float of a throwaway copy of a captured record moved by **one unit in the last place** must FAIL (it
did — 1 of 494 values); one line of a throwaway copy of a captured output file changed must FAIL (it
did — 1 of 16 173 lines); a missing `before` capture must **refuse**, not skip.

**The exclusion set: 48 names → 58.** Ten names were added, and the honest accounting of what they
cost the comparison is this. Together they exclude **164 leaves** across the six pairs, of which
**15 existed on the `before` side** — so the number of compared values fell by exactly 15, from
2 341 at `A59 (driver-predicate-mode)`'s merge to **2 326** here, and the other 149 are fields that
exist only after the change.

*Caption: one row per exclusion name this task added to G1's set, with the number of record leaves
it takes out of the comparison across the six pairs and the number of those that existed on the
`before` side (so the reduction in compared values is 15, not 164). Every name is matched against
the record path with its list indices normalised — `attempts[0].sweeps` and `attempts[2].sweeps`
both match `attempts[].sweeps` — which is the new matching rule described below.*

| name | leaves excluded | of which present before |
|---|---:|---:|
| `attempt_accounting` | 114 | 0 |
| `attempts[].sweeps_per_eval` | 20 | 0 |
| `attempts_node_calls_available` | 6 | 6 |
| `dispatch_sweeps_solve_phase` | 6 | 0 |
| `attempts[].node_calls_solve_phase` | 3 | 3 |
| `attempts[].sweeps` | 3 | 3 |
| `attempts[].cost_null_because` | 3 | 3 |
| `attempts[].sweeps_by_block` | 3 | 0 |
| `attempts[].stage_positional` | 3 | 0 |
| `attempts[].ladder` | 3 | 0 |
| **total** | **164** | **15** |

**The matching rule had to change, and why that is the conservative choice.** G1's exclusions were
matched against a record path's *bare* form — everything before the first list index — so an
exclusion named `attempts` would have taken **every leaf of every attempt** out of the comparison:
the exit code, the iteration count, the finite-difference step, the stage name. Hiding four new
fields by excluding twelve old ones is the "zero over a quietly smaller population" that trap T11
records. `gates.is_volatile` now matches a name containing `[]` against the path with its indices
normalised, so one leaf of every element can be excluded by name and the rest stay compared. A name
without `[]` takes the unchanged branch, so every exclusion written before this behaves exactly as it
did.

What is **not** excluded is the point: `attempts[].attempt`, `attempts[].stage`,
`attempts[].epsfcn`, `attempts[].n_iterations`, `attempts[].ifail` and `attempts[].raised` are
compared element by element on both sides, as are `node_calls_solve_phase`, `node_calls_total`,
`dispatch_sweeps`, the whole per-evaluation sweep histogram, the exit audit and every one of the
51 319 output-file lines. A stamp that had moved any of those would have been caught by them.

### 4.3 GR after DR7 — the reproduction gate

**PASS**, re-run in full at this branch's tip with the lifted input files staged from the previous
revision's run directory.

| | number |
|---|---|
| reference runs reproduced | **20 / 20** (14 optimisations + 6 evaluations, 3 configurations) |
| compared values identical | **270 / 270**, no tolerance on any of them |
| record contract — records carrying every declared field | **20 / 20** |
| substitute `A0p` (warm equivalence, for the arm GR cannot cover) | **PASS** — 2 pulsed configurations; 1 skipped with the reason recorded |
| substitute `AR` (first-`call_models` check, for the other arm GR cannot cover) | **PASS** — 3 configurations × 4 values = **12 / 12** |
| teeth | **7**, all tripped |

The seven teeth: a reproduced **count** raised by one must not reproduce; one character appended to
an objective **hex** string must not reproduce; a **missing reference file** must FAIL, not compare
over an empty set; a record with a compared field **removed** must FAIL, not skip it; asking the
previous revision's records for an arm name it never had must **raise**; the **composition** control
— `B3` on `st_regression` run with the analysis loop switched to `flat`, every other switch of the
arm unchanged — must not reproduce (**7 of 15** compared values differ); and the **attempt-summation**
tooth — a synthetic record whose `400 + 550 = 950` is claimed to decompose a run total of 1 000 —
must be **REFUSED**.

**The attempt-summation identity, on real records.** The record contract line above is where it is
enforced: `records.assert_usable` runs `assert_attempt_summation` on all 20 records before the gate
reports, and 20 of 20 pass. Stated as `A58 (driver-predicate-counters)` stated its sweep
decomposition:

    Σ attempts.node_calls_solve_phase == node_calls_solve_phase
    Σ attempts.sweeps                 == dispatch_sweeps_solve_phase

    14 optimisation records checked, 0 that do not decompose
    largest |residual|:  0 node calls,  0 sweeps
    node calls and sweeps of the solve phase outside every attempt:  0 and 0, on all 14

The last line is the identity's premise, measured rather than argued: nothing evaluates the model
set during the solve except the optimiser, so the attempts tile the solve phase exactly. The six
evaluation-phase records have no attempts and are passed over rather than refused, which their
`attempt_accounting.applicable = false` and its sentence say explicitly.

---

## 5. The measurement — the retry ladder, per attempt

Produced by the committed stage `python -m harness.gates attempts`, at commit `078f1936`. It reads
records and runs nothing; the three runs of §5.2 are made by `--capture runs` at the same commit.
**Nothing here is a gate and nothing here is a campaign statistic.**

### 5.1 The reproduction gate's fourteen optimisation runs

*Caption: one row per optimisation run of the reproduction gate — **seeds 0 and 1 only, one run
behind every cell, no campaign statistic anywhere in this table**. Columns: the number of attempts
the optimiser's retry ladder made; each attempt's stage name with its exit code in brackets (1 is
converged); the solve-phase node calls (model executions) of each attempt; the node calls spent in
attempts that did **not** produce the accepted optimum, which is every attempt but the last; and
that as a share of the run's solve-phase node calls. Units: node calls are model executions.*

| configuration | arm | seed | attempts | stages (`ifail`) | node calls / attempt | not accepted | share |
|---|---|---:|---:|---|---:|---:|---:|
| large_tokamak_nof | `BR` | 0 | 1 | initial (1) | 42 567 | 0 | 0.00 % |
| large_tokamak_nof | `B0` | 0 | 1 | initial (1) | 43 449 | 0 | 0.00 % |
| large_tokamak_nof | `B1` | 1 | 1 | initial (1) | 44 100 | 0 | 0.00 % |
| large_tokamak_nof | `B3` | 0 | 1 | initial (1) | 28 055 | 0 | 0.00 % |
| large_tokamak_nof | `B3` | 1 | 1 | initial (1) | 28 037 | 0 | 0.00 % |
| low_aspect_ratio_DEMO | `BR` | 0 | 1 | initial (1) | 89 964 | 0 | 0.00 % |
| low_aspect_ratio_DEMO | `B0` | 0 | 1 | initial (1) | 86 877 | 0 | 0.00 % |
| low_aspect_ratio_DEMO | `B1` | 1 | 1 | initial (1) | 81 228 | 0 | 0.00 % |
| low_aspect_ratio_DEMO | `B3` | 0 | 1 | initial (1) | 45 496 | 0 | 0.00 % |
| low_aspect_ratio_DEMO | `B3` | 1 | 1 | initial (1) | 52 834 | 0 | 0.00 % |
| st_regression | `BR` | 0 | 1 | initial (1) | 39 669 | 0 | 0.00 % |
| st_regression | `B0` | 0 | 1 | initial (1) | 42 756 | 0 | 0.00 % |
| st_regression | `B3` | 0 | 1 | initial (1) | 23 505 | 0 | 0.00 % |
| st_regression | `B3` | 1 | 1 | initial (1) | 134 560 | 0 | 0.00 % |

**Which runs retried: none of them.** 0 of 14. Every run converged on the ladder's first rung, so
every "not accepted" cell is 0 **by construction** (`n_attempts = 1` leaves no earlier attempt), and
the share column says nothing about what a retry costs. What it does say is that on this population
the previously published run totals and the per-attempt totals are the same numbers — which is the
right thing to find, because GR's job is to reproduce the previous revision and a difference here
would have been a defect.

### 5.2 Check 2's two constructions, side by side

*Caption: one row per run of the table above. "final" is the optimiser's iteration count on its last
attempt — the previous revision's construction, kept for comparability. "summed" is the count summed
over every attempt, failed attempts included — the acceptance statistic the experiment plan declares
(§3.5, check 2). "per attempt" is the breakdown the plan asks to print in the table. "evaluations" is
the run's own count of evaluations of the model set over all attempts, which is the multiplier the
transfer needs and which an iteration count cannot give. Same population as §5.1: one run per cell,
seeds 0 and 1.*

| configuration | arm | seed | attempts | final | summed | per attempt | evaluations |
|---|---|---:|---:|---:|---:|---|---:|
| large_tokamak_nof | `BR` | 0 | 1 | 8 | 8 | [8] | 630 |
| large_tokamak_nof | `B0` | 0 | 1 | 8 | 8 | [8] | 630 |
| large_tokamak_nof | `B1` | 1 | 1 | 8 | 8 | [8] | 660 |
| large_tokamak_nof | `B3` | 0 | 1 | 8 | 8 | [8] | 660 |
| large_tokamak_nof | `B3` | 1 | 1 | 8 | 8 | [8] | 660 |
| low_aspect_ratio_DEMO | `BR` | 0 | 1 | 16 | 16 | [16] | 1 240 |
| low_aspect_ratio_DEMO | `B0` | 0 | 1 | 16 | 16 | [16] | 1 240 |
| low_aspect_ratio_DEMO | `B1` | 1 | 1 | 15 | 15 | [15] | 1 218 |
| low_aspect_ratio_DEMO | `B3` | 0 | 1 | 13 | 13 | [13] | 1 050 |
| low_aspect_ratio_DEMO | `B3` | 1 | 1 | 15 | 15 | [15] | 1 218 |
| st_regression | `BR` | 0 | 1 | 10 | 10 | [10] | 570 |
| st_regression | `B0` | 0 | 1 | 10 | 10 | [10] | 570 |
| st_regression | `B3` | 0 | 1 | 10 | 10 | [10] | 570 |
| st_regression | `B3` | 1 | 1 | 59 | 59 | [59] | 3 510 |

The two constructions are **identical on all fourteen**, which is what one attempt per run makes
them. They can only differ on a retried run — which is exactly why the plan requires both, and
exactly why a table of this population alone would not show it.

### 5.3 The ladder exercised — the decomposition with more than one term

A decomposition checked only ever with one term in each sum is not a decomposition. So the stage
makes three runs that **must** retry: the reference arm at seed 0 on each configuration, with the
optimiser's iteration budget capped at 2 so its first attempt exits on "maximum iterations" and the
driver climbs the ladder. The cap is the harness's own gate-only switch; it is stamped into every
record as `force_maxcal`, so **no cost figure in this table is a measurement of the models and none
is comparable with any campaign number**.

*Caption: one row per demonstration run — **three deliberately budget-capped runs, one per
configuration, at seed 0**. Columns as §5.1, plus the residual of the summation identity for that
run. `ifail = 2` is "maximum iterations", which is what the cap produces and what makes the driver
try the next rung. Units: node calls are model executions.*

| configuration | attempts | stages (`ifail`) | node calls / attempt | not accepted | share | residual |
|---|---:|---|---|---:|---:|---:|
| large_tokamak_nof | 3 | initial (2), epsfcn_x10 (2), epsfcn_x0.1 (2) | 11 235 + 12 033 + 10 563 | 23 268 | 68.78 % | **0** |
| low_aspect_ratio_DEMO | 3 | initial (2), epsfcn_x10 (2), epsfcn_x0.1 (2) | 11 697 + 11 697 + 11 088 | 23 394 | 67.84 % | **0** |
| st_regression | 3 | initial (2), epsfcn_x10 (2), epsfcn_x0.1 (2) | 8 442 + 9 324 + 7 854 | 17 766 | 69.34 % | **0** |

**3 of 3** made more than one attempt; **3 of 3** decompose with residual 0, on node calls and on
sweeps alike. Three things this establishes that §5.1 cannot:

1. **The ladder's second and third rungs run, and the driver names them.** The stage column is the
   driver's own name for the rung, and it agrees with the harness's positional guess on every
   attempt of every run.
2. **The fourth rung does not run here**, and the code says why: it is conditional on `ifail == 5`
   *and* fewer than two optimiser iterations, and these runs exit with `ifail = 2` after two. So the
   `hessian_reset_b2` rung is **unexercised by anything in this report** — stated rather than left
   for a reader to notice.
3. **The share column is now a real number**, and it is a large one: roughly **68–69 %** of these
   runs' solve-phase node calls were spent in attempts that did not produce the accepted answer.
   That is a property of a run capped at two iterations per attempt, not of PROCESS — it is what the
   column *looks like* when the ladder fires, and it is the thing a run total cannot show at all.

### 5.4 What falls outside every attempt

*Caption: per run, the solve-phase node calls and sweeps that fall before the first attempt is
entered or after the last one exits. This is the premise the summation identity rests on, measured
on every record rather than argued from the code. Population: the 14 optimisation runs of §5.1.*

Zero, on every one of the fourteen: **0 node calls and 0 sweeps** outside every attempt, in all 14
records. Nothing evaluates the model set during the solve except the optimiser, and the attempts
therefore tile the solve phase exactly.

---

## 6. Autonomous decisions, each with its reversal path

*Caption: one row per call this task made without asking, what it costs if it is wrong, and exactly
what a later task would change to undo it. None of them changes what any model computes or what any
arm runs; all of them are about what is recorded and how it is checked.*

| # | decision | why | to reverse |
|---|---|---|---|
| 1 | The stamp lives in the **ladder** (`solver_handler.py`), not in the optimiser (`solver.py`) | only the ladder knows which rung it is on; a wrapper around `Vmcon.solve` would have to guess the stage from a counter, which is the positional guess this change exists to replace | move `caller.attempt(...)` into `_Solver.solve` and pass the stage down; the stamp's shape does not change |
| 2 | The stamp list lives in **`caller.py`**, beside the counters it reads | the harness reads every driver counter from one module; a second place to look is a second place to forget | move `ATTEMPT_STAMPS` to `solver_handler.py` and add the readback there; `child.harvest_attempt_stamps` takes the module as an argument already |
| 3 | `DISPATCH_SWEEPS_AT_OUTPUT` is added, so the **sweeps** have a solve-phase whole too | the plan's identity names node calls; sweeps without a matching total would be a column nobody could check, and the plan's `sweeps` field would be unverifiable | drop the field from the schema and remove the `sweeps` row from `records.ATTEMPT_SUMS`; the node-call identity is untouched |
| 4 | `attempts[].sweeps_per_eval` — the attempt's own **evaluation count** — is recorded although the plan's §4.4 row does not name it | the plan's §3.5 says in as many words that iterations "miss the lift's stencil column and the line-search evaluations that vary at equal iteration count", and the evaluation count per attempt exists nowhere else | delete the key in `records.attempts_from_forensics` and its G1 exclusion; nothing else reads it yet |
| 5 | `attempts[].stage` is the **driver's** name and the harness's guess moves to `stage_positional` | a field whose value is a guess should not be the one a table prints; and the two are now compared instead of assumed equal | swap the two assignments in `records.attempts_from_forensics` |
| 6 | G1's exclusion matcher learns `[]` — an exclusion may name **one leaf of every element of a list** | the alternative was to exclude `attempts` entirely, which would have taken every attempt's exit code, iteration count and step size out of the comparison to hide four new fields. That is the "zero over a quietly smaller population" trap T11 records | delete the `_LIST_INDEX` branch in `gates.is_volatile`; every pre-existing exclusion is matched by the unchanged branch |
| 7 | The measurement is a stage of `harness/gates.py` (`python -m harness.gates attempts`), not a new module | it is the third measurement-not-a-gate in that file and shares its record reader, its arm order and its printing helpers | move it to its own module; `A52 (harness-gates)` wires the name into the runner either way |
| 8 | `attempt_accounting` is one block rather than a dozen top-level fields | it is arithmetic *about* `attempts[]`, and keeping it together is what let G1's exclusion be one name instead of twelve | flatten it; each field then needs its own named G1 exclusion |

**What was deliberately not done.** The `retried` flag is *derivable* (`n_attempts > 1`) and is
published as a convenience, not as a source of truth — `A53 (harness-tally)` should compute it from
`attempts[]` so that a record written by an older harness cannot present a stale flag. And no
tally, ratio or table is produced here: this task supplies the per-attempt numbers and the identity
that makes them safe to sum; the "with and without retried seeds" ratios are `A53`'s.

---

## 7. Handover

### 7.1 To `A52 (harness-gates)`

- **Wire `attempts` into the runner.** `harness/gates.py` gained a measurement stage reached today
  by `python -m harness.gates attempts`. It belongs beside `predicate-counters`,
  `output-path-measurements` and `output-path-contrast` in `experiment_runner.py`'s dispatch — it is
  a measurement, not a gate, and must not be registered in `gates.registry`. This task did not edit
  `experiment_runner.py`, which is A52's file.
- **G1's exclusion set is now 58 names**, reviewed as one table — it was 48 at `A59
  (driver-predicate-mode)`'s merge. The ten added here are listed in §4.2 with the leaf counts they
  cover; **seven of them are `attempts[].…` names**, which is the new matching rule, so a review of
  the set should start by reading `gates.is_volatile`'s two branches rather than the table alone.
- **`gates.is_volatile` changed.** An exclusion name containing `[]` matches the path with its list
  indices normalised; a name without `[]` matches exactly as before. Every pre-existing exclusion
  takes the unchanged branch, so the change is additive — but it is a change to the thing that
  decides what a gate compares, and it should be read as such.

### 7.2 To `A53 (harness-tally)`

- **The retried-seeds column** of the experiment plan's §4.3.1 is `n_attempts > 1`, computed from
  `attempts[]` (not from `attempt_accounting.retried`, which is the same thing published for
  convenience and could be stale in a record written by an older harness).
- **Check 2's two constructions** are both on the record, per run: the final attempt's iterations
  (`n_solver_iterations`) and the sum over every attempt including failed ones
  (`exit_forensics.n_solver_iterations_summed_over_attempts`), with `attempts[].n_iterations` giving
  the per-attempt breakdown the plan asks to print in the table. The **acceptance statistic is the
  summed-over-attempts median**; the final-attempt median is published beside it for comparability.
  §5 prints both side by side on GR's runs as the format to follow.
- **The "with / without retried seeds" ratios** are computed from `node_calls_solve_phase` over two
  populations, not from a per-attempt subtraction: the plan wants the ratio *over the seeds that did
  not retry*, not the ratio *with the retries subtracted*. `attempts[].node_calls_solve_phase` is
  what makes the second reading *possible* to state, and §5's "share not accepted" column is that
  quantity per run — but it is a different number from the ratio, and a caption that confuses them
  would repeat trap T11's shape.
- **Every per-attempt sum is safe to take** because `records.assert_attempt_summation` refuses a
  record where it is not: a tally does not need to re-derive the identity, only to say it was
  enforced and over what population.
- **`dispatch_sweeps_solve_phase`** is the sweep column a per-sweep table should use when it is
  talking about the solve; `dispatch_sweeps` remains the whole-run total and includes the
  output-time loop and the exit audit. A table that mixes them is comparing two different
  populations.

### 7.3 To `A55 (harness-smoke)`

The one-seed end-to-end chain gets `attempts[]` populated for free. The thing worth asserting in the
smoke chain is the identity's *residual*, not the attempts themselves: a smoke run that reaches a
record whose `attempt_accounting.decomposes` is `true` has exercised the driver stamp, the harness
readback and the refusal in one pass.

---

## 8. How to re-run everything in this report

Interpreter: `/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python` — never `PROCESS_env`,
which imports a different clone of PROCESS at a superseded commit without any error at all. All
commands are run from `arch_surgery/MDA_partitioning_experiment_v4/`.

```
# the copy's own gates, and the diff view -- seconds, no PROCESS run
python PROCESS/copy_gates.py all
python PROCESS_diff.py                 # exit 0, 0 unexplained hunks
python PROCESS_diff.py --markdown      # the table this report quotes
python PROCESS_diff.py --teeth

# the harness's self-check -- seconds, no PROCESS run
python experiment_runner.py --selfcheck

# G1: the two captures, then the comparison.  The 'before' capture must be
# taken at the commit before the driver change and cannot be re-taken later.
git checkout <the commit before the change>
python -m harness.gates switch-neutrality --capture before
git checkout <the commit after the change>
python -m harness.gates switch-neutrality --capture after
python -m harness.gates switch-neutrality --compare

# GR after the change, with the previous revision's lifted input files
python experiment_runner.py --gate reproduction \
    --lifted-from /home/wrutten/projects/PROCESS_surgery/arch_surgery/MDA_partitioning_experiment_v3/runs/_decks

# the measurement (not a gate); reads GR's records, runs nothing
python -m harness.gates attempts
```

Every PROCESS run in this report went through `harness/pool.py` — a fresh subprocess in its own
working directory, with `PYTHONPATH` naming V4's copy and that exact tree asserted in-process before
any work is done. Background work was stopped with `TaskStop`, never `pkill`: each sandboxed shell
call has its own process namespace, so `pkill` reports success while killing nothing (trap T8).

---

## 9. Change log

*Append-only. One row per commit on `A60-driver-attempts`, in order.*

| commit | what |
|---|---|
| — | **G1's `before` capture**, taken at `582d7a0d` (the branch point, driver byte-identical to the tip of `architecture_surgery`) **before any edit**: six runs, the two reference arms on the three configurations. Nothing is committed by a capture — run artifacts are untracked by design — but the capture's manifest records the commit it was taken at, and it cannot be re-taken later to make a comparison agree |
| `252d8e40` | **DR7 in the copy.** `caller.py`: `ATTEMPT_LADDERS`, `ATTEMPT_STAMPS`, `open_ladder()`, the `attempt()` context manager, and `DISPATCH_SWEEPS_AT_OUTPUT` frozen by the statement that already froze `NODE_CALLS_AT_OUTPUT`. `solver_handler.py`: `LADDER_STAGES` beside the branches that implement them, and each of the four calls to the optimiser bracketed |
| `2c097267` | **The copy's provenance and diff view follow.** `copy_gates.py` gains a sixth permitted-edit file and a permitted edit on `caller.py`; `PROVENANCE.json` regenerated; `PROCESS_diff.py` gains the annotations and a paragraph for `solver_handler.py` |
| `7f4ce958` | **The harness reads the boundaries back.** `records.py` (the `attempts[]` schema, `attempt_accounting`, the summation refusal on both quantities), `child.py` (`harvest_attempt_stamps`), `switches.py` (four readbacks), `optimise.py`, `evaluate.py`, `gates.py` (the `[]` exclusion matcher, ten exclusions, the `attempts` measurement stage), `README.md`. **G1's `after` capture was taken here** |
| `078f1936` | **The ladder exercised.** `gates.py` only: the `--capture runs` demonstration — three deliberately budget-capped runs that must retry, because all fourteen of GR's optimisation runs converge on their first attempt — and the wording of one exclusion's reason. Neither the driver nor anything a run records changes |
| *(this commit)* | **The report**, and the measurement re-run at `078f1936` to produce §5's tables |

---

## 10. What this does not establish

Three limits, stated so that a later reader does not have to infer them.

1. **No cost ratio is published here.** This task supplies per-attempt costs and the identity that
   makes them safe to sum. The "with and without retried seeds" ratios the experiment plan asks for
   are computed by `A53 (harness-tally)` over the campaign, which has not run. §5's table is
   **fourteen single runs at seeds 0 and 1** — the reproduction gate's own set — and no cell in it
   is a campaign statistic.

2. **The identity's premise is measured on those runs, not proved in general.** `outside_attempts`
   is 0 on every run reported here, which is what makes Σ attempts equal the solve-phase totals. It
   is measured on every record, so a future change that breaks it is visible; it is not a theorem.

3. **The neutrality claim is G1's, over G1's population.** G1 compares the two reference arms on the
   three configurations at seed 0 — six run pairs — and the claim it supports is *"with every
   architecture switch unset, the copy after the change behaves byte-identically to the copy before
   it"*. It says nothing about the intervention arms, which is what GR and the copy's own gates are
   for, and it is the reason the driver change was made and gated **on its own** rather than batched
   with another (V4 harness plan §7.2).

---

## 11. Notes for the reader of the records

Run artifacts are untracked by design (`CLAUDE.md`); only verdicts and summaries are committed. The
runs behind this report live under the worktree's
`arch_surgery/MDA_partitioning_experiment_v4/runs/gates/` — `switch_neutrality/before`,
`switch_neutrality/after`, `reproduction/` and `attempts/ladder/` — and are relocated by
`arch_surgery/bin/retire_task_worktree.sh` at merge, which prints the path they end up at. **G1's
`before` capture cannot be regenerated**: it was taken at `582d7a0d`, before the driver change, and
re-taking it later would be taking it at a different commit.

The record files this report reads are `metrics.json` in each run directory; the gate verdicts are
`runs/gates/<gate>/gate.json`; the measurement's own record is
`runs/gates/attempts/measurements.json`.

---

## 12. The copy, as `PROCESS_diff.py` shows it

*Caption: the two files V4's copy of PROCESS gained a difference in for this task, from
`PROCESS_diff.py --markdown` at this branch's tip. Columns: lines added and removed by `git diff`
against the copy's source commit `f2dc9243` — against the commit, never a working tree — the number
of hunks, and the mechanism each hunk's annotation claims. Population: all 224 files of the copied
package; seven of them differ, of which these two differ because of this task. The full table for
all seven, and a paragraph per file, is the script's own output.*

| file | + | − | hunks | serves (this task's share) |
|---|---:|---:|---:|---|
| `process/core/caller.py` | 954 | 474 | 51 | DR7 stamps: what each attempt of the retry ladder cost — node calls and sweeps read at every attempt boundary, so the run's solve-phase totals decompose per attempt (**4 of 51 hunks**) |
| `process/core/solver/solver_handler.py` | 32 | 5 | 5 | DR7: the ladder's rungs named beside the branches that implement them, and each of its four calls to the optimiser bracketed by a boundary stamp (**5 of 5 hunks** — the file had no difference before this task) |

`PROCESS_diff.py` exits **0** with **0 unexplained hunks** across all seven changed files, and its
`unannotated_hunk` tooth still trips: one unclaimed line appended to `process/core/constants.py` is
reported as UNEXPLAINED.

---

## 13. Why the plan asked for this, in one paragraph

The V4 harness plan's §3.2 row DR7 says the cost of *not* doing it: *"the headline stays partly an
artefact of the mismatch — node calls are run totals while `n_solver_iterations` and `ifail` are per
VMCON attempt"*. `A44 (transfer-gap)` put a number on it from the previous revision's records:
`low_aspect_ratio_DEMO`'s published cost ratio `B3/B0 = 0.450` contains **one seed on which the flat
arm failed its first attempt and converged on the `epsfcn × 10` retry**, with both attempts'
evaluations charged to `B0`; over the ten retry-free seeds the same ratio is **0.659**. The
experiment plan's §3.5 now requires both readings to be published side by side — *"a retry the other
arm did not need is real cost the architecture avoided at that start, **and** it is a robustness
event, not a per-evaluation cost; pooling it into a cost ratio without saying so is what made the
previous revision's headline unreadable"* — and neither reading can be constructed from a run total.
That is what this task supplies: the cost, per attempt, with the arithmetic that proves the parts
are the whole's parts.

