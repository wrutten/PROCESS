# The harness

This package decides **what to run** and **whether the tree can run it**. It is written to be
read by someone who has not followed the project, so everything it assumes is spelled out below.

---

## 1. What the experiment measures, and why the physics is frozen

PROCESS is a fusion power-plant systems code. It wraps an optimiser around a loop that runs about
twenty-six physics and engineering **models** — plasma, coils, buildings, costs — over and over
until their outputs stop changing, and then asks the optimiser for a better design and does it
again. The models are the physics. The loop around them is the **driver**.

This experiment changes only the driver: how the models are arranged, how often each runs, and
what test decides that the loop has finished. It asks whether a driver that solves the models in
three smaller groups instead of one large one reaches the same answer for less work.

**Every physics and engineering model is byte-identical to the code this fork started from.** That
is not politeness; it is what makes the measurement mean anything. If a model changed, a cheaper
run could be cheaper because it is computing something different, and no comparison would settle
anything. So the models are frozen, a check confirms it at every commit, and a change to one needs
the user's explicit approval before it can be merged.

The experiment runs its **own copy** of the PROCESS package, in `../PROCESS/`, so that changes made
for it cannot reach the code the earlier revisions of the experiment measured. The harness sets
`PYTHONPATH` to that copy for every run and then asserts, inside the run, that the package it
actually imported is exactly that one.

---

## 2. What one run does, end to end

1. The harness picks an **arm** (one setting of the driver's switches), a **configuration** (one
   input file describing one plant to optimise) and a **seed** (which displaced starting point to
   use). Nothing else varies.
2. It builds the environment for that arm **from nothing**: every switch it knows about is
   removed first, then only the ones this arm declares are set. An inherited setting can therefore
   never change what is measured without saying so.
3. It asks the tree, in a throwaway child process, what that environment actually resolved to. If
   the tree does not implement a switch the arm asked for, the run is **refused**. It is never run
   with the switch quietly missing — that would produce a successful run of a *different* arm
   under the right name, which is the failure this whole package is shaped around.
4. It starts a fresh subprocess in its own working directory (two runs in one process contaminate
   each other: PROCESS holds output-file handles as class attributes) and runs either one
   evaluation of the whole model set, or one full optimisation.
5. Inside that subprocess the run records what the driver resolved, counts every model call, takes
   an **audit** of how converged the state actually was at a fixed point in the run, and writes a
   record.
6. Afterwards, the records — never the runs — are summarised twice, by two separate pieces of
   code, and the two summaries are compared cell by cell. Twice, because a definition that reached
   one implementation and not the other has slipped past review here before.

Steps 1–5 are built. Step 6 — the two summaries and the comparison between them — is a later task; the runner names it when you ask for it.

---

## 3. The vocabulary

One row per word this project uses in a particular way. Where a word is *not* used, the word it
replaces is named so that older documents can still be read.

*Caption: the harness's terms. "Means" is the definition in force; "replaces" names the older
wording, kept only so that documents written before the rename remain readable. Rows marked
**changed** differ from the terminology table in the harness plan's §11.2; §7 says why.*

| term | means | replaces |
|---|---|---|
| **model** | one physics or engineering calculation. Frozen; the experiment never changes one | — |
| **driver** | the arrangement of loops and solvers around the models. The only thing the experiment changes | — |
| **node** | one place a model is called from inside the loop. One **node call** is one execution of one node, and node calls are the unit of cost | — |
| **sweep** | one pass over a sequence of nodes — the whole loop, or one block's share of it | — |
| **coupling state** | the set of numbers the models pass to each other (about 830–850 of them). The loop's job is to make these stop changing | ystate, spec, harvest |
| **tolerance (τ)** | how small a scaled change in the coupling state counts as "stopped changing". **One value, 1e-6, for every loop in every arm** | tau, inner tau |
| **flat** | the loop as one block containing every node | `flat_state` |
| **partitioned** | three block solves, run one after another: plasma physics, then coils, then plant | `per_module` |
| **block loop** | the loop inside one block of a partitioned run. It uses the same tolerance as everything else | inner loop |
| **schedule passes** | how many times a partitioned run works through its three blocks. V4 runs the schedule **once**; the arm that repeated it was removed | outer loop, trust/verify · **changed** |
| **stopping rule** | what ends the loop: upstream's own objective-and-constraint test, or the coupling-state test at the tolerance | — · **added** |
| **arrangement · node** | *when* a node runs: moving `build` to after `physics` so the physics block is contiguous | `SEQUENCE=build_after_physics` |
| **arrangement · method** | *when* a method runs: executing the run-constant first-wall geometry calculation at the head of every sweep, so the next model reads this pass's value instead of the last one's | the prime |
| **deferral `per_call`** | a node runs once per evaluation of the model set instead of once per sweep | hoist |
| **deferral `per_run`** | a node runs once in total, at the accepted optimum | post-solve |
| **burn-time owner** | who decides the burn time on a pulsed plant: the **loop** (a model solves for it), a **constant** (a fixed value, for the phase that has no optimiser), or the **optimiser** (it becomes a design variable with a consistency constraint) | lift, pin, `ixc 178`, constraint 93 |
| **output-time loop** | upstream's second loop, which re-solves the accepted design until the output files stop changing before writing them. Only the optimisation phase reaches it; an evaluation-phase arm carries no switch for it at all | `MDA_Output`, idempotence loop |
| **arm** | one column of the switch matrix: one complete setting of the driver | variant |
| **reference arm** | PROCESS exactly as shipped, every switch unset. `AR` in the evaluation phase, `BR` in the optimisation phase | `R`, "PROCESS as shipped" |
| **rung** | a pair of adjacent arms differing by one named thing, so that a difference in cost can be attributed to that thing | — · **added** |
| **configuration** | one optimisation problem: which plant, which objective, which constraints, named by its input file's stem | deck, scenario |
| **input file** | the file a configuration is read from. A configuration has two: the **committed** one, never edited, and a derived **lifted** copy that hands the burn time to the optimiser | deck · **changed** |
| **frozen** | reserved for two things only: the physics freeze, and the convergence predicate's mode. It never describes an input file | — · **changed** |
| **seed** | which displaced starting point a run uses. The same word in both phases; the same seed gives every arm a bit-identical starting point, so comparisons are paired | seed / start |
| **δ regime** | Phase A entries displaced by 10 % from a converged state | warm δ-stream |
| **stencil regime** | Phase A entries taken from the optimiser's own finite-difference steps, which is what the loop actually sees during an optimisation | — |
| **skip** | an arm that is inactive on a configuration, with the reason recorded. On a steady-state plant there is no burn time to own, so the two arms that move its ownership have nothing to move | — · **added** |
| **capability probe** | a child process that imports the driver under an arm's environment and reports what it resolved, so that an unimplemented switch is refused rather than ignored | the instrumentation ledger · **added** |
| **pending switch** | something an arm declares that no tree implements yet, because the driver change that supplies it has not been made. Composing the arm without it is refused | — · **added** |
| **tally** | the summary computed from the records by the phase scripts | — |
| **analysis** | the same summary computed independently, and compared with the tally cell by cell | — |
| **teeth** | a check's demonstrated ability to fail: a deliberate break that it must catch before its zeros are believed | — |

---

## 4. The switch registry

Every switch is described once, in `switches.py`, as data: the word this experiment uses for it,
the environment variable the driver reads, its legal values, whether an arm ever sets it, and how
to read back what the driver actually resolved. `switches.py` is the only file that has to change
when a switch does.

*Caption: one row per switch the driver understands. "Composed" says whether an arm ever sets it or
the harness only clears it before composing. "Not implemented" means no tree offers it yet and every
arm that asks for it is refused rather than run without it. The last column names the variable a
caller might still be setting from before the rename; **setting one of those raises**, in the
harness and in the driver both.*

| term | variable | values | composed | raises if set instead |
|---|---|---|---|---|
| analysis loop | `PROCESS_ARCH_MDA` | `flat`, `partitioned` (unset = upstream's own loop) | yes | `…_MODULE_SOLVE`, `…_OUTER` |
| tolerance | `PROCESS_ARCH_TAU` | a number (default `1e-6`) | yes | `…_INNER_TAU` |
| coupling state | `PROCESS_ARCH_COUPLING_STATE` | a file | yes | `…_YSTATE` |
| write sets | `PROCESS_ARCH_WRITE_SETS` | a file | yes | `…_WRITESET` |
| arrangement · node | `PROCESS_ARCH_ARRANGEMENT_NODE` | `build_after_physics` | yes | `…_SEQUENCE` |
| arrangement · method | `PROCESS_ARCH_ARRANGEMENT_METHOD` | `fw_geometry` | yes | `…_PRIME` |
| deferral `per_call` | `PROCESS_ARCH_DEFER_PER_CALL` | `feedforward`, `feedforward_lifted` | yes | `…_HOIST` |
| deferral `per_run` | `PROCESS_ARCH_DEFER_PER_RUN` | a file | yes | `…_POST_SOLVE` |
| burn-time owner | `PROCESS_ARCH_BURN_TIME_OWNER` | `loop` (the default), `optimiser`, `constant:<hex float>` | yes | `…_LIFT`, `…_PIN_BURN_TIME` |
| output-time loop | `PROCESS_ARCH_OUTPUT_LOOP` | `upstream` (the default), `none` | yes, in the optimisation phase | — |
| predicate mode | `PROCESS_ARCH_PREDICATE` | `frozen` (the default), `mixed` | only for the trial | — |
| pass trace | `PROCESS_ARCH_PASS_TRACE` | a file | never; cleared | — |
| pass trace detail | `PROCESS_ARCH_PASS_TRACE_FULL_FROM` | a number | never; cleared | — |

**Five of those rows are worth a sentence: a switch disappeared behind three of them, one is where
the experiment's own intervention shows up in the driver, and one is a deliberate trial.**

*The output path is a choice.* Upstream writes its output files through a **second** loop. Having
accepted a design, it evaluates the whole model set again, writes an output file to a scratch
location, and repeats — up to ten times — until two successive files agree number for number; only
then does it write the real ones. That loop belongs to the incumbent's stopping rule and not to the
models: an arm whose solve has already converged the coupling state to the shared tolerance has
nothing left for it to find, and re-solving the state before writing it means the numbers in the
output files are not the numbers the optimiser accepted.
`PROCESS_ARCH_OUTPUT_LOOP=none` therefore writes the files once, from the accepted state, and runs
no output-time sweep at all. Unset, the loop is exactly where upstream put it. Either way the
driver now **counts** what it did — how many sweeps that loop took, and how many times the output
path was entered — so the second loop's cost is a column of a table rather than a term nobody
measured, and `0` under the one-call path is a count rather than a claim.

*How often the block schedule runs is no longer a setting.* Choosing `PROCESS_ARCH_MDA=partitioned`
*is* choosing to run the block schedule exactly once. An earlier revision had a second switch that
chose between running it once and repeating it while a test over the whole coupling state still saw
movement; that test was measured triggering a further pass **zero times in 91 888 evaluations**, the
arm that used it was removed by a recorded decision, and the switch went with it. Setting
`PROCESS_ARCH_OUTER` now raises.

*There is one tolerance.* `PROCESS_ARCH_TAU` is the tolerance of every converger in every arm and
both phases — the flat loop and each block loop alike. A second, "inner" one existed because arms
used to be compared at matched *settings*; they are compared at matched *achieved* accuracy, which
the exit audit records per run, so there is nothing for a second number to do. Setting
`PROCESS_ARCH_INNER_TAU` raises.

*The convergence test's ruler is a choice, and the choice is on trial.* The test asks whether the
largest **scaled step** of the coupling state is below the tolerance, and what it divides that step
by is called the **ruler**. Under `frozen` it divides by a scale measured once, over a harvest of
design points, and frozen in the committed artifact: `max|Δy| / s`. Under `mixed` it keeps that
measured scale as a **floor** and divides by the state's current magnitude wherever that is larger:
`max|Δy| / max(|y|, s)`. Two things follow from the definition rather than from measurement:
wherever the current magnitude is at or below the scale the two are **bit-identical**, and `mixed`
is **never tighter**, so no count of components still moving can go up.

The second ruler exists because of a measured case, not a preference. A cost figure reaching
6.6 × 10²¹ at a design point with negative net electric power, against a harvested scale of 1 251,
makes the frozen test there about 10¹⁸ times tighter than it reads, and the loop iterates that point
until the state stops changing in its last bit. Upstream PROCESS's own test, being relative to the
current value, is *looser* than ours at that point. `mixed` is the smallest change that removes the
mechanism while keeping the measured scale as a floor, so a quantity that is genuinely small is
still tested absolutely rather than against its own noise.

`frozen` is the default and the campaign's setting, so every earlier record reproduces; adoption is
a later decision made by the experiment plan's own rule, on the trial's numbers, and not by whoever
implemented the switch. Two consequences a reader should know. **The exit audit is published on
both rulers on every run, always** — the mixed one reads *lower* wherever its denominator binds, by
construction, so a table showing one column alone would report a change of ruler as a gain in
accuracy. And **which ruler a run stopped on is stamped** in the record and in the preamble of every
file a run writes, because a run under one ruler is otherwise indistinguishable from a run under the
other afterwards.

*One switch says who owns the burn time.* Taking the burn time out of the model and naming what
holds it instead used to be two settings, and they could disagree: "a constant owns it, but the
model still solves for it" had to be refused explicitly, because the model would overwrite the
constant on the first sweep. `PROCESS_ARCH_BURN_TIME_OWNER` says it once — the loop, the optimiser,
or a named constant, passed as a hexadecimal float so a measured value survives the round trip
exactly — and the inconsistent pair can no longer be written down.

### 4.1 The counters — things the driver reports, which nothing sets

*Caption: one row per module-level counter the driver exposes and every run record carries. None of
them is a switch: nothing sets one, no arm composes one, and none has an environment variable. They
are listed in `switches.py` beside the registry (`DIAGNOSTIC_READBACKS`) so that the self-check can
ask the tree under test whether it has them — a tree missing one would write a null into a record,
and a null is not something a reader can tell apart from "this run stopped early".*

| counter | what it counts | record field |
|---|---|---|
| `NODE_CALLS` | model executions, the whole run | `node_calls_total` |
| `NODE_CALLS_AT_OUTPUT` | the same, frozen when the output path is entered — the **cost unit** | `node_calls_solve_phase` |
| `ARRANGEMENT_METHOD_CALLS` | executions of the run-constant geometry method | `n_prime_calls` |
| `DISPATCH_SWEEPS` | sweeps of the model sequence, every path included | `dispatch_sweeps` |
| `SWEEPS_PER_EVAL_HIST` | the same sweeps, binned per evaluation of the model set | `sweeps_per_eval` |
| `OUTPUT_LOOP_SWEEPS` / `OUTPUT_PATH_ENTRIES` | what the output-time loop cost, and how often it ran | `output_loop_sweeps`, `output_path_entries` |
| `PREDICATE_EVALUATIONS` / `COMPONENTS_COMPARED` | the coupling-state convergence test: how often, and how wide | `predicate_evaluations`, `components_compared` |
| `PREDICATE_EVALUATIONS_BY_BLOCK` / `COMPONENTS_COMPARED_BY_BLOCK` | the same two, per block | inside `predicate_counters` |
| `BLOCK_VISITS` / `EMPTY_BLOCK_VISITS` / `EMPTY_BLOCK_SWEEPS` | the schedule's visits to each block, the ones that executed no model node, and what those cost | `block_visits`, `empty_block_visits`, `empty_block_sweeps` |
| `UPSTREAM_PREDICATE_EVALUATIONS` / `UPSTREAM_COMPONENTS_COMPARED` | upstream's own stopping test: how often, and how wide | `upstream_predicate_evaluations`, `upstream_components_compared` |
| `DISPATCH_SWEEPS_AT_OUTPUT` | the sweep counter frozen where the node counter is — the whole the per-attempt sweeps decompose | `dispatch_sweeps_solve_phase` |
| `ATTEMPT_STAMPS` / `ATTEMPT_LADDERS` | the cost counters read at the entry to and the exit from every attempt of the optimiser's retry ladder, and how many ladders were entered | `attempts[]`, `attempt_accounting` |

**Why the convergence test is counted at all.** The partitioned arrangement runs far more sweeps of
the model sequence than the flat one while executing far fewer model nodes, and the previous
revision found it no faster in wall clock. That can only be true if a sweep costs something that is
not proportional to the nodes it runs. The convergence test is the obvious suspect: a flat loop
compares the **whole** coupling state — 827 to 846 components, depending on the configuration — on
every one of its sweeps, while a block loop compares only its own block's write set. Nothing in this
experiment may rest on a clock, so the question is asked in counts instead: how many times a test
was evaluated, and how many components each of those tests walked. Their ratio is the average width
of the test, which is the number the question is about.

**Two predicates, counted separately.** An arm stops on exactly one of them and they are not the
same test, so pooling them would produce an average of two different things. The coupling-state
predicate is what the flat and partitioned arrangements stop on; upstream's own test compares the
objective and the constraint vector against the previous sweep's — about 27 values rather than 840 —
and the reference arms stop on that. Counting both is what keeps the reference arm's row in the
published table a measurement rather than a zero. Upstream's pair short-circuits, so the width
recorded for it is the width **compared**, not the width declared.

**Empty block visits are counted and disclaimed, never repaired.** On `st_regression` the `PULSE`
block survives in the schedule after its only member has left it: that configuration runs no pulsed
plant, `pulse` writes nothing the predicate reads, the routing rule correctly moves it out of the
loop — and the block stays behind and is visited once per evaluation, executing nothing. The user
ruled that this stays as it is. It is one of PROCESS's oddities this experiment does not undertake
to fix, and dropping the block would change the node weights the whole comparison rests on. So it is
counted, and **every table that weights sweeps must say that empty visits are included and how many
there were**.

*Empty is measured on the node counter, not on the block's membership*, and the two are not the
same. The routing rule moves `pulse` out of the loop **at the call site**, not out of the block, so
the `PULSE` block still lists its member: it is visited, a full sweep of the model sequence is
charged for it, and no model runs. Membership would have called that visit non-empty and missed the
whole finding. A block the per-call deferral has genuinely emptied — the feed-forward tail under the
intervention arms — is empty too, but costs **no** sweep at all. `EMPTY_BLOCK_SWEEPS` is what keeps
the two apart: it is the sweeps those empty visits actually spent, and it is the number a
per-sweep-overhead table needs, because the visit count alone would charge the free case as if it
cost a sweep.

**Why the optimiser's attempts are counted separately.** The optimiser is not tried once. When it
returns anything but "converged", the driver calls it again with the finite-difference step
multiplied by ten, then by a tenth, and finally — on exit code 5 with fewer than two iterations —
once more from a reset second-derivative matrix. That is the **retry ladder**, and every one of its
attempts evaluates the model set. Until these stamps existed the record could say how many attempts
there were, what each one's exit code was and how many optimiser iterations each took, but the
*cost* was a single run total: a run that failed its first attempt and converged on the retry
charged both attempts' evaluations to one number while reporting only the last attempt's iterations.
That is not a hypothetical. It is most of one configuration's published cost ratio in the previous
revision — 0.450 with the one retried seed in it, 0.659 over the retry-free seeds — and the
experiment plan now requires the ratio to be published *with and without* retried seeds, which a run
total cannot give. A **seed is retried** when its `attempts` list has more than one entry.

**The parts must add up, and a record where they do not is refused.** `attempts[].node_calls_solve_phase`
sums to `node_calls_solve_phase` and `attempts[].sweeps` sums to `dispatch_sweeps_solve_phase`, on
every optimisation record, checked by `records.assert_attempt_summation` before any summary reads it.
Per-attempt accounting whose parts do not decompose the whole is worse than none, because the
with-and-without ratio would then be computed over quantities that are not the published one's parts.
The identity holds because nothing evaluates the model set during the solve except the optimiser —
and that premise is **measured**, not assumed: `attempt_accounting.outside_attempts` publishes the
node calls and sweeps that fall before the first attempt or after the last one, so a future change
that put work between the ladder and the output path would show as a non-zero term rather than
silently unbalance the sum.

**Why the counters are safe.** Every one is a plain integer increment. None touches a float, none
changes a branch a result depends on, and all of them count the **solve** phase only — the
output-time loop's own comparisons are counted by neither predicate, exactly as the per-evaluation
sweep histogram excludes them. That the driver behaves identically with every switch unset is a
**gate**, not a claim: see §8.

**Why a retired name raises instead of being ignored.** Before the rename, a switch name the driver
did not recognise was simply ignored. A script still setting an old name would therefore produce a
*successful* run of a *different* arrangement under the right name, with no error anywhere — a wrong
answer with no symptom, which is the shape of failure this whole package is built against. The
eleven retired names are listed in the driver as well as in the registry, and the self-check
compares the two lists rather than assuming they agree: a name on one list and not the other would
mean the harness is describing a driver it is not running.

### 4.2 The names of the committed artifacts

Three of the switches above are handed a **file**: the coupling-state description, the per-block
write sets, and the set of nodes deferred to once per run. The experiment keeps its own copy of
those files in `data/`, and they are named for what each one *is for*:

*Caption: one row per committed artifact. "In `harness/data/`" is the name the experiment's own
copy uses; "in the repository's shared directory" is the older spelling of the same file, kept
because the earlier revisions of the experiment read it. `{name}` is the configuration's name. The
last two rows are named by a path constant inside the copied driver, so renaming either of them
is a change to the driver, not to the harness.*

| what it is | in `harness/data/` | in the repository's shared directory |
|---|---|---|
| which fields make up the coupling state, and the scale of each | `coupling_state_{name}.json` | `ystate_a26_{name}.json` |
| which of those fields each block writes | `write_sets_{name}.json` | `writeset_a26_{name}.json` |
| the nodes deferred to once per run, for a run of the **committed** input file — the unmarked default | `defer_per_run_{name}.json` | `postsolve_nolift_{name}.json` |
| the same node set, stamped for a run of the **lifted** input file | `defer_per_run_lifted_{name}.json` | `postsolve_{name}.json` |
| what each node writes, measured | `node_writesets.json` | `node_writesets.json` |
| which block each node belongs to | `dsm_node_map.json` | `dsm_node_map.json` |

The old spellings carry the number of the task that first produced the file, which the naming
rule for this revision forbids, and they use words the vocabulary has since replaced. Both
spellings resolve: `default_campaign()` uses the first column and `repository_tree_campaign()` the
second, so the harness can be pointed at either set of files without either name being written
twice.

**Those files are copies, and `data/PROVENANCE.json` says whose.** Sixteen files sit in `data/` —
the six kinds above for three configurations, plus the three committed input files. Each was
copied out of the repository at a recorded commit, read from the commit itself rather than from
anyone's working tree, and each is byte-identical to what it was copied from. The record names,
per file, the role it plays, the configuration it belongs to, the path it came from, its sha256
and the fields the artifact carries about its own making — the script that produced it and the
commit that script ran at. The self-check's **data** check compares both directions: the file
against the record, and the record against the source read back from the commit, so regenerating
the record cannot be the way a changed file becomes blessed.

Nothing here is ever *derived*. The scales inside the coupling-state artifacts are this
experiment's fixed ruler; re-deriving them from a fresh measurement would change what the
tolerance means and break comparability with every earlier revision that quoted a distance on that
ruler. A campaign that finds an artifact missing refuses — it does not make one.

One thing in the copies is deliberately stale. Each `write_sets_{name}.json` carries an internal
field naming the coupling-state file it was built against, under the older spelling
(`ystate_a26_{name}.json`), which is not the name that file has here. It is left exactly as it
was, because the copy being byte-identical to its source is worth more than the field being
tidy — and because **the driver never pairs the two files by name**. It requires the write set's
recorded hash of the component list to equal the loaded coupling-state description's own hash, and
raises otherwise. A wrong pairing is caught by the bytes; a renamed file is not noticed at all.

`harness/ystate.py` — the code that decides what "converged" means — was moved here from the
repository's research tree under the same rule, and is recorded in the same file. Its body is
byte-identical to its source: the only difference is a paragraph in its docstring saying where it
came from, and the check removes that paragraph again and compares the remainder byte for byte.

Because of that, the check that this revision composes the same environments as the last one
compares **which artifact each switch is handed**, not which file name — so a rename compares
equal and handing an arm the *wrong* artifact still compares unequal. There is a tooth for
exactly that: giving the evaluation phase's block arm the lifted input file's artifact, when it
runs the committed one, must be caught.

The two schemes mark **opposite** members of the per-run pair: the older one marked the committed
input file's artifact (`postsolve_nolift_`) and left the lifted one plain, and this one marks the
lifted artifact and leaves the committed one plain, because the committed input file is what most
arms run. A steady-state configuration has no lifted input file, so it has one artifact and both
names resolve to it.

Two more rows need a word.

**`schedule passes` is composed but never declared.** The partitioned arms work through their
three blocks once. The driver's own default is to repeat the whole schedule while anything is
still moving, and it expresses "do not repeat" as a separate setting. Since no arm in this
experiment repeats the schedule, that setting is not a choice an arm makes: the registry supplies
it whenever the partitioned loop is selected. It disappears from the driver when the partitioned
setting comes to mean one pass on its own.

**`second tolerance` is refused, not merely unused.** The driver still lets a block loop use a
different tolerance from the outer test. There is one tolerance in this experiment, so a run
carrying that variable would report an accuracy the campaign never declared. Composing an
environment that contains it raises.

---

## 5. Running it

Everything runs under the project's own interpreter. Another environment on this machine imports a
*different* copy of PROCESS without any error at all, which is a silent wrong answer rather than a
failure, so the harness refuses to start under an interpreter that cannot import the tree it is
about to measure.

**`--tree` is not a way to run the experiment somewhere else.** The default, and the only tree a
record is ever made against, is the experiment's own copy of PROCESS in `../PROCESS/`.
`--tree repository` points the preflight and the self-check at the repository's own tree, which is
useful for asking "does the harness still compose the way it did?" — and every campaign stage
refuses in that case, saying so, so a measurement of a tree nobody asked for cannot be produced by
forgetting a flag.

```bash
PY=/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python
cd arch_surgery/MDA_partitioning_experiment_v4

# the button: preflight, the matrix, the rungs, what the tree can do
$PY experiment_runner.py

# the same, against the repository's own PROCESS instead of the experiment's copy
$PY experiment_runner.py --tree repository

# the harness's own gates, with their teeth
$PY experiment_runner.py --selfcheck
$PY harness/selfcheck.py --tree repository --json runs/selfcheck.json

# quickly, without starting a child process per arm
$PY experiment_runner.py --no-capability

# ONE run: one arm, one configuration, one seed.  Never a campaign record.
$PY experiment_runner.py --run --arm A0 --configuration st_regression --seed 0

# what gates and measurement stages exist, what each binds, how many teeth
$PY experiment_runner.py --gates

# ONE gate, by its registry name; or every gate, cheapest first
$PY experiment_runner.py --gate reproduction        # gate GR
$PY experiment_runner.py --gate all --resume        # all of them, one button

# a measurement stage: it publishes numbers and has nothing to pass
$PY experiment_runner.py --measure gate_table       # the plan's §4.1 table
$PY experiment_runner.py --measure all
```

Every gate makes its own runs, with `--resume` keeping a complete record of the
same job rather than re-making it — **except one**. Gate G1, switch neutrality,
compares the copy *before* a driver change with the copy *after* it, so its two
sides are at two commits by construction and it cannot make its own "before":

```bash
$PY experiment_runner.py --gate switch_neutrality --capture before  # at the commit before
$PY experiment_runner.py --gate switch_neutrality --capture after   # at the commit after
$PY experiment_runner.py --gate switch_neutrality                   # compare, with teeth
```

`--outdir` sends a gate's verdict somewhere other than the campaign's records
directory; the gates' own runs stay where they are, because one gate reads
another's runs. `--no-teeth` skips the teeth and the verdict says so — a gate
whose teeth were not run is not an accepted gate.

A single run writes its record, its exit state, its displacement, its audit residual vector and
its entry-census series into its own directory under `../runs/`, and prints whether the record
carries everything it declares. Gate GR is about twenty-five runs and takes on the order of an
hour and a half at three workers; it writes one small verdict file whose contents are what the
report's tables quote.

Exit codes: `0` ready · `2` refused to start (wrong interpreter) · `3` not ready, with the missing
thing and the stage that produces it named on the line above.

`--draft` keeps the runner in preflight-and-gates mode even after execution is approved. Campaign
stages refuse while `EXECUTION_APPROVED` in `config.py` is `False`; the user flips it in the same
commit that records the dated approval in the experiment plan. The refusal is printed by the same
entry point that would print a result, so the failure path is as reproducible as the success path.

To inspect one arm without running anything:

```python
import sys; sys.path.insert(0, "arch_surgery/MDA_partitioning_experiment_v4")
from harness import ARMS, env_for, input_file_for, repository_tree_campaign, rung

campaign = repository_tree_campaign()
nof = campaign.configuration("large_tokamak_nof")

rung("B0", "B3")                       # what separates the two arms, field by field
input_file_for("B3", nof, campaign=campaign)  # which input file B3 reads
env_for("A1", nof, seed=0, pin_hex=float(3600.0).hex(), campaign=campaign)
```

**Stopping something that is running**: use the session's own task-stop mechanism, never `pkill`.
Each sandboxed shell call has its own process namespace, so `ps` sees nothing from a sibling call
and `pkill` reports success while killing nothing. A whole set of runs was lost to that once.

---

## 6. Adding things

**A configuration.** Add a row to `default_configurations()` in `config.py`: its name, whether the
plant is pulsed, its objective, its variable and constraint counts, its coupling-state component
count, and the arms that are inactive on it with the reason. Its artifact paths follow from its
name through `ARTIFACT_NAMES` (§4.2) and are not written out. Nothing downstream counts configurations for itself —
every population is derived from the campaign's list — so a fourth configuration needs no other
edit.

**Removing a configuration** is the same mechanism: `campaign.without_configuration(name,
decision=…, reason=…, date=…)` returns a new campaign with the configuration gone and the removal
recorded. Every count then re-derives. A denominator computed over three configurations and edited
down to two by hand is exactly how this project has published a zero over a population smaller
than the one it named, so no count is ever written by hand.

**An arm.** Add an `Arm` to `ARMS` in `arms.py` — one field per row of the plan's matrix — and add
its column to `PLAN_MATRIX`, which is the plan's own table transcribed for comparison. If the arm
takes part in a rung, add the rung to `RUNGS` with the fields it is declared to move. The
self-check then proves that what the arm actually changes is what the plan says it changes; if it
is not, the check fails and says so.

**A switch.** Add a `Switch` to `REGISTRY` in `switches.py`: the term, the variable the driver
implements, the intended name, the legal values, and **how to read back what the driver
resolved**. The readback is the load-bearing part: it is what lets the harness tell "the tree did
what I asked" from "the tree ignored me". Then set it from `Arm.terms()`.

**Renaming or retiring one.** Put the old name in that `Switch`'s `retired_names`, with the reason,
and add it to `RETIRED_SWITCHES` in the driver's `process/core/solver/__init__.py` with the same
reason. Both are needed: the harness one stops an arm from composing it, the driver one stops a
caller that never went through the harness. The self-check compares the two lists, so forgetting
either half is a failed check rather than a quiet gap. If the rename means two switches become one —
as the burn time's owner did — give `canonical_roles()` the folding, and give it a way to *fail*:
the folding must drop the old switch only where its value is the one the new one implies, and any
other value must survive as a role of its own so a real difference still reads as a difference.

---

## 7. Where this differs from the plan's terminology table, and why

The harness plan's §11.2 fixed the vocabulary and gave this package the job of finalising it. Five
changes and five additions were made; each is listed here so the plan can absorb them.

1. **"deck" is gone; the word for the file is "input file".** §11.2 replaced "deck" with
   "configuration", and a configuration has *two* files — the **committed** one and its **lifted**
   derived copy — so the file still needs a word, and it is the plain one. A **configuration** is
   the problem; an **input file** is a file it is read from. **"Frozen" is reserved** for the
   physics freeze and the predicate mode, and names no file, field or matrix cell.
2. **"outer loop" is gone, and so is the switch that expressed it** *(closed 2026-09-10 by the
   rename)*. §11.2 lists `PROCESS_ARCH_OUTER` as retired. Until the rename it was retired only as
   something an *arm chooses* — the driver still had to be told to run the schedule once, so the
   registry supplied it whenever the partitioned loop was selected. The driver now takes
   `PROCESS_ARCH_MDA=partitioned` to *mean* that, no arm composes anything for it, and setting the
   old name raises.
3. **"retired" is operational for every retired name, not only the second tolerance.** An
   environment carrying any of the eleven raises — in the harness when an arm is composed, and in
   the driver at import, so a caller that bypasses the harness is refused too. A name that is only
   *not used* comes back.
4. **Two intended names were missing and were supplied**: `PROCESS_ARCH_COUPLING_STATE` (was
   `…_YSTATE`) and `PROCESS_ARCH_WRITE_SETS` (was `…_WRITESET`), so that the switch names follow
   the terms as §11.2 requires of the others.
5. **The single burn-time-owner switch folds two of the earlier ones** *(done 2026-09-10)*, and
   that is exact only because exactly one quantity is ever taken out of the loop. The earlier
   "lift" switch took a *list*; if a second quantity is ever taken out, the general form is needed
   back, and the driver's own docstring says so where a reader will meet it.
6. **Five terms with no row in §11.2 are added**: rung, stopping rule, skip, capability probe,
   pending switch. Each is a thing the harness has to name in a refusal message.
7. **The plan's matrix row "outer loop" is regenerated, not stored.** Four of the plan's eleven
   matrix rows — the stopping rule, the outer loop, whether the burn time is out of the loop, and
   which input file is read — follow from the other rows. They are computed, and the whole table is
   regenerated and compared against the plan's, cell for cell, so the plan's table still prints
   exactly as written while an arm has one field per *choice* rather than one per row.
8. **Two places where the plan disagreed with itself were found here and have since been ruled**
   (2026-09-10). See §8; the rulings are in the plan, and the code carries the reasons rather
   than a flag.
9. **Run directories should be named for the seed.** §11.2 makes "seed" the word in both phases,
   but the run-layout decision still writes `start001`. The task that builds the run path should
   use `seed001`.

---

## 8. What the gates prove, and what "teeth" are

A **gate** is a check that must pass before a number is believed. A gate's **teeth** are deliberate
breaks that the check must catch: a check that has never been shown to fail is an assertion, not a
measurement. This project has published a zero over a population quietly smaller than the one it
named, and has once had a check that returned "pass" over an empty set, which is why every count
below carries the number of things actually compared.

`harness/selfcheck.py` runs six checks, each with its teeth, in about half a minute, and starts no
PROCESS run.

*Caption: one row per check. "Compares" is the population; "teeth" are the deliberate breaks it is
shown to catch.*

| check | binds | teeth |
|---|---|---|
| **composition** | every arm composes on every configuration; a skipped arm refuses by name and quotes its recorded reason; the reference arms compose to every switch cleared; the arms the previous revision also ran compose to the *same switch settings* it used | a wrong value in one arm; a switch dropped from an arm; a skipped arm asked to compose |
| **rungs** | the plan's matrix regenerates cell for cell from the arm records; the difference between two arms equals the difference the plan declares for that step; no removed arm is present | a wrong expected difference; a wrong cell in the transcribed matrix; an arm compared with itself |
| **capability** | the tree resolves every switch each arm asks for, exactly as asked; an arm asking for something no tree implements is refused before anything runs | a switch name no tree defines; a switch the environment does not carry claimed as resolved; a retired name present in the environment |
| **provenance** | a modified tracked file and an untracked file are recorded separately, and only the first marks the tree dirty | each kind of change, one at a time, in a throwaway repository; and the tree asserted by a prefix instead of exactly |
| **data** | every committed file in `data/` is byte-identical to its source at the recorded commit and the file set matches exactly; `ystate.py`'s whole diff against its own source is exactly the hunks the record holds and its post-edit hash is the recorded one; the counts `config.py` declares are the ones the files carry | one byte changed; a file missing; a file the record does not name; a changed file whose recorded hash was updated to match it — which passes a record-only check and must still fail; and the same two on `ystate.py` itself |
| **run path** | a finished record carries every field it declares, both convergence rulers included; the two displacement streams key on what they say they key on; a run against the wrong tree, or without a switch its arm declares, is refused rather than made | a declared field removed; an exit audit carrying one ruler and not both; a record that does not say what kind of run made it; per-attempt costs that do not sum to the run total; an allowance covering a switch the tree has |

Two of these deserve their reason stated.

**Why the previous revision's composition is compared.** A rewritten harness that changes the
measurement is not a rewrite; it is a new experiment. The six arms this revision shares with the
last one must compose to the same switch settings, or the difference between the two revisions'
numbers would be partly the harness. The expected settings are transcribed into `selfcheck.py`
rather than imported, because every check the experiment runs is implemented inside this package;
`--crosscheck-previous` then *executes* the previous revision's own two composition functions in a
subprocess and compares, so the transcription is measured rather than trusted.

**Why the predicate module is allowed to differ from its source at all, and what still refuses.**
`harness/ystate.py` was moved whole out of the repository's research tree, and for a while the
check on it could be the strongest one available: remove the one paragraph it had gained and the
rest was byte-identical to the source. The approved driver change that gave the convergence test a
second ruler is *in that module*, so that reconstruction no longer exists. The check was re-based
rather than dropped, on the model the copied PROCESS tree already uses: an edit is legal because it
is **recorded and reviewable**, not because it is absent. The record holds every hunk of the diff
and the post-edit hash, and each recorded edit says what it is, what it does and which task made
it. An edit nobody recorded still fails — by the hash if the hunks were left stale, and by the
hunks if the hash was updated to match — and both of those are teeth.

**Why the dirty flag is split.** A run stamped "dirty" because a draft file was sitting beside the
runner tells a reader nothing, and a whole set of records was stamped that way once while the
measured code was clean. A modified *tracked* file can change a measurement; an untracked one
cannot. Both are recorded; only the first marks the tree dirty.

**Two disagreements inside the plan were found here, and both have been ruled** (2026-09-10).

- The step from the flat control to the arm where the optimiser owns the burn time moves **two**
  things, not one: ownership, and the output-time loop. **Ruling: the matrix stands and the
  description was completed.** Putting the output-time loop's change on that step is deliberate —
  it is the step already declared to differ in kind between the two phases, so the *headline*
  step, the partitioning intervention, keeps a switch set identical to its evaluation-phase twin.
  The harness declares both fields and carries that reason.
- The matrix gave the partitioned evaluation-phase arm `A1` the output-time loop, while the prose
  listing the arms that keep it left `A1` out. **Ruling: the evaluation-phase arms carry no switch
  for it at all** — an evaluation never reaches the output path — so the row reads `n/a` for all
  four of them, and the arms that keep the loop are the two optimisation-phase controls. One
  consequence matters: `A1` is runnable now, and only `B1` and `B3` wait on the driver change that
  supplies the switch.

---

## 9. Where records go, and what a record contains

Bulk run artifacts go to `../runs/`, which is deliberately not tracked by git: hundreds of run
directories are not something to commit. **Summaries and verdicts are committed; raw records are
not** — so a summary must be reproducible from a committed script, and a record that only exists
in `runs/` can vanish when a working tree is retired. That has cost this project evidence three
times.

A record of one run carries, at minimum:

- **what was run**: configuration, arm, seed, entry regime, the input file's path, and the arm's whole
  composed environment **as the driver resolved it** — read back from the imported modules, not
  as the harness asked;
- **where it ran**: the interpreter, the exact tree, its commit and branch, whether that commit
  descends from the experiment's base commit, the tracked modifications and the untracked paths
  separately, and the identity of the PROCESS copy;
- **what it cost**: node calls in total and per node, sweeps per evaluation, and — per attempt,
  because the optimiser retries — the same counts again, so that a run total is never divided by a
  per-attempt count;
- **what its convergence tests cost**: how many times each of the two predicates was evaluated in
  the solve phase, how many components each of those tests walked, the schedule's visits to every
  block and how many of those executed nothing (§4.1);
- **what it achieved**: the normalised objective, the optimiser's exit code, and an audit of how
  far the coupling state still was from converged, taken at the same fixed point in every arm —
  **on both convergence rulers, always**, because the one that keeps the measured scale as a floor
  reads lower wherever that floor binds and a single column would read as accuracy rather than as
  a change of ruler. Which ruler the run's own loops stopped on is stamped beside them, and in the
  preamble of every file the run writes;
- **how it ended**: one of a small set of outcomes — finished, crashed, refused, did not converge,
  hit upstream's own pass cap, infeasible at the audit, or a machinery failure. Upstream's loop
  raising after ten passes is a *finding about the shipped code*, not a broken run, and has its
  own outcome so that the two are never confused again.

The record's schema and the code that reads it are a later task; this list is what it must carry.

---

## 10. What is not here yet

What exists: the declarations (`config.py`), the switch vocabulary and the capability probe
(`switches.py`), the arm matrix (`arms.py`), the provenance refusals (`provenance.py`), the
committed data in `data/`, the coupling state and its predicate (`ystate.py`, `predicate.py`), the
displacement streams (`perturb.py`), **the run path** (`child.py`, `optimise.py`, `evaluate.py`,
`pool.py`, `records.py`, `failure.py`), the committed reproduction reference (`reference.py`) and
**gate GR** (`reproduction.py`), plus the self-check and the runner's preflight.

What is not here yet: the **tally** and the **analysis**. Everything above them is built — the
artifact stages, the census, the derivation of the lifted input file, and **every gate of the
experiment plan, inside this package**, in one registry with the harness's own checks promoted
beside them (§8). The preflight names each missing piece and the stage that produces it rather than
falling back to something that happens to be there.

Nothing in a record is a placeholder any more. The driver chain is closed: the convergence test's
evaluations and the components it walked, what each optimiser attempt cost on its own, the
output-time loop's sweep count and which of the two output paths ran, and the exit audit on both
convergence rulers are all measured and stamped. Where a quantity does not apply — an evaluation
has no optimiser attempt to cost — the record says so explicitly rather than leaving the key out.

---

## 11. The reproduction reference — the previous revision's numbers, committed

### What it is

`harness/reference/reproduction_reference.json` holds the measured results of **twenty runs made by
the previous revision of this experiment**: three configurations, six arms, both phases. It is the
answer sheet for one question, asked once:

> *We rewrote the harness. Did the rewrite change the measurement?*

The way that question gets answered is **gate GR**. The experiment keeps its own copy of PROCESS
(`../PROCESS/`). At the commit where that copy is taken — and **before any change is made to it** —
the copy *is* the code the previous revision measured, character for character. So the rewritten
harness is pointed at it, the twenty runs are made again, and every compared number must come out
**exactly** the same: not close, not within a tolerance, the same. These are counts and hexadecimal
floating-point strings, both of which reproduce bit for bit or do not reproduce at all. If a number
moves, the only thing that changed is the harness, and that is precisely what the gate is for.

Fifteen numbers are compared per optimisation and ten per evaluation — model executions during the
solve, evaluations the optimiser asked for, sweeps per block, the objective at the exit as a hex
float, how far the coupling state still was from converged, the optimiser's exit code and iteration
count, and the per-attempt iteration counts the plan's second construction of check 2 needs. The
list lives in `REFERENCE_FIELDS` in `harness/reference.py` and each field's one-line meaning is in
the committed file itself, so a reader does not have to open the plan to know what a cell is.

### Why it is committed rather than read from the records

The previous revision's records sit in an untracked bulk directory in the main checkout. Untracked
means git does not have them, and **this project has destroyed untracked run records three times** —
once taking with it the evidence behind a correction to a published headline (queue issues I-14,
I-15 and I-16; the trap is written up in `arch_surgery/docs/TRAPS.md`). A gate anchored on files
that can be deleted by retiring a working tree is a gate that will one day quietly have nothing to
compare against, and a check with no population is not a check.

So the compared fields are extracted **once** into a small committed file (32 KB), and the gate reads
that. The live records are used only to *re-derive* the file and confirm, byte for byte, that
nothing has drifted. If the records vanish tomorrow, the gate still works; only the re-derivation
becomes unavailable, and it says so rather than passing.

### How to re-derive it and how to check it

The records live in the **main checkout**, so a task working in its own worktree has to be pointed
at them; there is no default that guesses at another checkout, because guessing would read numbers
nobody asked for.

```bash
PY=/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python
cd arch_surgery/MDA_partitioning_experiment_v4
RUNS=/home/wrutten/projects/PROCESS_surgery/arch_surgery/MDA_partitioning_experiment_v3/runs

# what is committed, and what it does not cover — reads no records
$PY experiment_runner.py --reference show

# re-derive it from the records and require byte-for-byte equality
$PY experiment_runner.py --reference verify --previous-runs $RUNS

# the four deliberate breaks, each of which must make a stage refuse
$PY experiment_runner.py --reference teeth --previous-runs $RUNS

# rebuild the committed file (only when the reference set or the field list changes)
$PY experiment_runner.py --reference extract --previous-runs $RUNS

# the report's two tables, rendered from the committed file with their captions
$PY experiment_runner.py --reference tables
```

Exit codes are the runner's: `0` pass, `3` fail. Each stage writes its own record under `../runs/`,
which is untracked. `harness/reference.py` takes the same flags directly if you want the module on
its own.

**Everything that could stop the comparison is a failure, never a skip.** A record that is not
there, a record that does not carry a field the plan names for its phase, a record made at a commit
other than the previous revision's campaign commit, an absent committed file, an absent records
directory — each one refuses and says which record and which field. The four **teeth** (a gate's
demonstrated ability to fail — §8) exercise exactly that: one record deleted from a throwaway copy;
one compared field deleted from a throwaway copy of a record; the arm-name map bypassed; one value
changed in a throwaway copy of the committed file. All four must trip before the gate's zeros mean
anything.

**One thing to know about the arm names.** The previous revision called the optimisation-phase
reference arm `R`; this revision calls it `BR`, because the phase belongs in the name. The map lives
in `switches.PREVIOUS_ARM_NAMES` and is inverted, never written a second time. Asking the previous
revision's records for `BR` **raises** rather than reporting a missing directory, and so does asking
for either of the two arms this revision retired. A lookup that misses has to say so.

### What it covers, and what it does not

It covers the six arms both revisions run, on the three configurations, at the unperturbed seed and
at the first perturbed one. **Two of this revision's arms are new and have no previous record at
all**, so GR cannot say anything about them; each is covered by a different named gate instead, and
the committed file states both rather than leaving a reader to notice an arm missing:

| arm | why the reference cannot cover it | covered instead by |
|---|---|---|
| `AR` — the evaluation-phase reference | the previous revision had no such arm | one evaluation with every architecture switch cleared must reproduce the first `call_models` of `BR` at seed 0, on that call's node calls, sweeps and objective hex |
| `A0p` — flat, with the burn time owned by a constant | the previous revision never ran that combination | the warm-equivalence gate: pinned at the reference's converged burn time it must reproduce the reference fixed point, with the cross-state residual below the tolerance and the pinned component bit-identical |

*Caption: one row per arm outside the reference's reach; "covered instead by" names the check that
does test the path. Neither substitute is a comparison against a prior record, because no prior
record exists — both are internal consistency checks against a reference the run itself produces.*

One row of the reference set is deliberately short. The arm where the optimiser owns the burn time
is not run on `st_regression`: that configuration is steady-state, has no burn-time coupling, and
the arm composes onto its predecessor there — so the previous revision never ran it and this file
records the absence with the reason rather than quietly holding nineteen entries where the table
says twenty.

Finally, the reference says nothing about whether the architecture is *better*. It only says the
harness that measures it is the same instrument. The experiment's own gates and checks do the rest.
---

## 12. The artifact stages — what is checked, what is derived, and what is only compared

The experiment reads a handful of committed files it does not compute at run time. Three of them
the **driver** reads directly, so they are not the harness's private business: getting one wrong
does not produce an error, it produces a converged run of a slightly different problem. This
section says what each file is, which stage looks at it, and — the part worth reading twice —
which stages *derive* something and which only *compare*.

Everything below is reachable from the one button:

```bash
# validate every committed artifact of every configuration
python experiment_runner.py --artifacts check

# derive the lifted input files (needs one PROCESS run per pulsed configuration)
python experiment_runner.py --artifacts derive-inputs

# take a runtime census and compare it with the committed one (one PROCESS run each)
python experiment_runner.py --artifacts census --census-entry optimisation

# re-derive the per-run deferral sets and compare them with the committed ones
python experiment_runner.py --artifacts per-run

# the deliberate breaks: every one must be caught
python experiment_runner.py --artifacts teeth

# all of the above, in order, stopping at the first failure
python experiment_runner.py --artifacts all
```

Each writes its record under `runs/artifacts/`, which is untracked. `--artifacts check` is also
the preflight's artifact half: the preflight used to ask whether each file existed and whether one
count matched, and it now runs this instead.

### 12.1 The files, and who reads them

*Caption: one row per committed file the experiment reads. "Read by" matters because a file the
driver reads cannot be corrected by the harness alone. "Stage" is the committed stage that looks
at it; **derive** means the harness reproduces the file's content from first principles, **compare**
means it reproduces something the file rests on and reports the difference, and **check** means it
rebuilds the file's own stamps and cross-checks them against the files it must agree with.*

| file | what it is | read by | stage |
|---|---|---|---|
| `<configuration>.IN.DAT` | the committed input file: one optimisation problem | the driver | check |
| `<configuration>_lifted.IN.DAT` | the same problem with the burn time owned by the optimiser | the driver | **derive** |
| `coupling_state_<configuration>.json` | which fields make up the state the analysis loop converges, and the measured scale of each | the driver and the harness | check |
| `write_sets_<configuration>.json` | which components of that state each block writes | the driver | check + **compare** |
| `defer_per_run_<configuration>.json` | which nodes run once per run instead of once per evaluation, for the committed input file | the driver | check + **derive** |
| `defer_per_run_lifted_<configuration>.json` | the same, for the lifted input file | the driver | check + **derive** |
| `node_writesets.json` | what every model node writes, measured | the driver | check + **compare** |
| `dsm_node_map.json` | which block each node belongs to, and how each node is invoked | the driver | check |

### 12.2 What is never derived, and why

The coupling-state artifact carries the **scales** every residual in this experiment is measured
against. They were measured once, from a file that is not committed, and they are the ruler: three
earlier revisions' residual figures are quoted on them, and a fresh measurement would change what
the tolerance means without changing any number's appearance.

So **there is no stage in this package that derives one**. Not disabled, not guarded — absent.
`--artifacts check` validates each from the artifact's **own harvest identity**: a hash of the file
it was measured from, plus a content hash over the coupling-key set, the model sequence and every
design point's exact design vector. An artifact carrying no such identity is **refused by name**,
because a file that cannot say what produced it cannot be checked at all. A campaign that finds an
artifact missing refuses; it does not make one.

### 12.3 The lifted input file — the one thing that is derived from scratch

Two arms hand the burn time to the optimiser. They read an input file that differs from the
committed one in exactly three lines:

1. the burn time becomes iteration variable 178;
2. its consistency residual becomes equality constraint 93, **inserted inside the equality block**
   with the count raised in the same edit;
3. the variable's initial value is set to the burn time the incumbent's own loop settles on at the
   configuration's own starting design vector.

Line 2's *position* is the one that has already gone wrong once. PROCESS does not decide which
constraints are equalities from the constraints themselves: it takes the first *n* entries of the
constraint list in file order. Appending the new one at the end therefore turned an equality into
the last inequality — a problem in which nothing forces the burn time onto its own consistency
manifold — and the run still converged, with an objective that looked right. It was caught by
reading an inequality count in a table, not by looking at the file.

Line 3 is a **measurement**, taken by one evaluation of the model set under the reference arm
(every architecture switch unset), through the pool like any other run. It is the reference arm and
not the flat control because the rule asks for the value the *incumbent's* stopping rule leaves
behind. The input file's own default is 1000 s and none of the pulsed configurations sets it, while
the settled values are thousands of seconds — so a derivation that quietly fell back on the default
would produce a file that looks right and starts the lifted arm at a design point the incumbent
never visits. The derivation refuses rather than defaulting.

**The gate is the bytes.** Each derived file's sha256 must equal the digest committed in
`input_files.py`, which was measured from the previous revision's own derived files. A steady-state
configuration records *not applicable* rather than deriving anything. The derived file's header and
its three edit comments are reproduced verbatim from the script that first produced it, task token
and all: the digest is the gate, and a tidier comment is a different file.

### 12.4 The census — a direct observation, not an inference

The driver carries an instrument that, while it is switched on, attributes every read and every
write of a state field to the model node executing at the time. `--artifacts census` runs one
PROCESS run with it on and compares what it saw with the committed per-node census, with the
per-block subsets that census was mapped into, and with the read set the deferral routing rule is
derived from.

Two entries are available. `--census-entry optimisation` is one full optimisation — the same
population of design points the committed census was measured over, and the only entry that can
reproduce it. `--census-entry evaluation` is one evaluation of the model set: every node runs, so
every node's write set is observed, but only at one point of the design space, and fields written
only elsewhere will be missing.

Two traps are handled structurally rather than carefully. Ten model objects call their own `run()`
from inside their `output()` method, three times each per run, during the final output check — so
an instrument that hooks `run()` alone attributes reporting traffic to the analysis loop and
*invents* dependency edges. The driver's instrument closes the sweep at the boundary of one pass
over the model sequence and refuses anything arriving afterwards; the census stage records the
refusal count, so a reader can see the mechanism working instead of assuming it.

### 12.5 The per-run deferral sets — derived, and compared node by node

A node whose outputs nothing the optimiser decides on ever reads cannot change what the optimiser
does, so it runs once per run at the accepted optimum instead of once per evaluation. Which nodes
those are is derived in four steps: the **seeds** (what the active figure of merit's own branch of
the objective reads, plus every active constraint's reads), a **backward closure** (a node is
needed if anything it writes is consumed; a needed node's reads join the consumed set), the
**candidates** (everything never needed), and a **confirmation** (every read site of every
candidate's outputs, anywhere in the tree, classified).

Reads are attributed **by enclosing class, not by file**. That correction is not cosmetic: one file
holds both the vacuum pumping model, which is a candidate, and the vacuum vessel, which is a live
plant node, and the file rule would have classified a read of a pumping output made inside the
vessel class as "internal to the candidate" and marked the node dead, with no warning. The
class-to-node map is derived from the driver's own model container rather than transcribed.

Three kinds of read site are excluded from the closure, and each is counted and named:

- a function reachable from a reporting entry point and from **no** node entry point — computed per
  class from the call graph, which is the rule that was missing the three times this project
  invented a dependency edge;
- a file no configuration here executes;
- a function this configuration's own switches make unreachable, such as the two plant-availability
  models no configuration selects.

Each is the direction in which a mistake marks a live node dead, which is why none is applied
quietly. The stage then compares the derived set with the committed artifact **node by node**. A
difference is a finding: either the derivation is wrong or the artifact is stale, and the task
report says which it thinks and why. Nothing is edited to make the other side agree.

### 12.6 The teeth

Every stage above has to be shown capable of failing before its zeros mean anything. `--artifacts
teeth` runs them all; each break is made on a throwaway copy in a temporary directory and the
committed files are never written to.

*Caption: one row per deliberate break; "must be caught by" names the check that has to notice it.*

| stage | break | must be caught by |
|---|---|---|
| check | the recorded component digest set to zeros | the rebuild from the components the file lists |
| check | the harvest identity removed | the refusal on an artifact that cannot say what produced it |
| check | the figure of merit changed **and its own hash recomputed to match** | the comparison with the input file — an artifact that rebuilds its own hash can still be the wrong problem's |
| input files | one byte of a derived file flipped | the digest |
| input files | a baseline evaluation that crashed, and one that carries no burn time | the refusal to derive without the measurement |
| input files | the constraint appended at the end of the file instead of inside the equality block | the digest |
| census | one node's write removed | the per-node comparison's counts |
| census | a node writing a field the committed census does not have | the this-run-only count, which fails the stage |
| per-run | a node removed from the committed set | the node-by-node comparison |
| per-run | a live node added to the committed set | the node-by-node comparison — the direction that would defer a node the optimiser consumes |
