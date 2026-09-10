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

Steps 4–6 are built by later tasks. Steps 1–3 are this package as it stands.

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

Every switch is described once, in `switches.py`, as data. Three names matter for each: the word
V4 uses, the environment variable the driver implements **today**, and the name it is intended to
carry once the renaming change is made. When that change happens, `switches.py` is the only file
that has to change.

*Caption: one row per switch. "Composed" says whether an arm ever sets it or the harness only
clears it before composing. "Intended name" is the name planned for it; a dash means the switch is
meant to disappear rather than be renamed. "Not implemented" means no tree offers it yet and every
arm that asks for it is refused.*

| term | driver name today | intended name | values | composed |
|---|---|---|---|---|
| analysis loop | `PROCESS_ARCH_MODULE_SOLVE` | `PROCESS_ARCH_MDA` | `flat_state`, `per_module` (unset = upstream's own loop) | yes |
| tolerance | `PROCESS_ARCH_TAU` | unchanged | a number | yes |
| coupling state | `PROCESS_ARCH_YSTATE` | `PROCESS_ARCH_COUPLING_STATE` | a file | yes |
| write sets | `PROCESS_ARCH_WRITESET` | `PROCESS_ARCH_WRITE_SETS` | a file | yes |
| arrangement · node | `PROCESS_ARCH_SEQUENCE` | `PROCESS_ARCH_ARRANGEMENT_NODE` | `build_after_physics` | yes |
| arrangement · method | `PROCESS_ARCH_PRIME` | `PROCESS_ARCH_ARRANGEMENT_METHOD` | `fw_geometry` | yes |
| deferral `per_call` | `PROCESS_ARCH_HOIST` | `PROCESS_ARCH_DEFER_PER_CALL` | `feedforward`, `feedforward_lifted` | yes |
| deferral `per_run` | `PROCESS_ARCH_POST_SOLVE` | `PROCESS_ARCH_DEFER_PER_RUN` | a file | yes |
| burn time out of the loop | `PROCESS_ARCH_LIFT` | `PROCESS_ARCH_BURN_TIME_OWNER` | `burn_time` | yes |
| burn time owned by a constant | `PROCESS_ARCH_PIN_BURN_TIME` | `PROCESS_ARCH_BURN_TIME_OWNER` | a hexadecimal float | yes |
| schedule passes | `PROCESS_ARCH_OUTER` | — (folded into the analysis loop) | `trust` | yes, but never per arm |
| output-time loop | *not implemented* | `PROCESS_ARCH_OUTPUT_LOOP` | `none` | yes, once it exists |
| predicate mode | *not implemented* | `PROCESS_ARCH_PREDICATE` | `mixed` | only for the trial |
| second tolerance | `PROCESS_ARCH_INNER_TAU` | — (**retired**) | — | never; **refused if present** |
| pass trace | `PROCESS_ARCH_PASS_TRACE` | unchanged | a file | never; cleared |
| pass trace detail | `PROCESS_ARCH_PASS_TRACE_FULL_FROM` | unchanged | a number | never; cleared |

### 4.1 The names of the committed artifacts

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
```

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
name through `ARTIFACT_NAMES` (§4.1) and are not written out. Nothing downstream counts configurations for itself —
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

---

## 7. Where this differs from the plan's terminology table, and why

The harness plan's §11.2 fixed the vocabulary and gave this package the job of finalising it. Five
changes and five additions were made; each is listed here so the plan can absorb them.

1. **"deck" is gone; the word for the file is "input file".** §11.2 replaced "deck" with
   "configuration", and a configuration has *two* files — the **committed** one and its **lifted**
   derived copy — so the file still needs a word, and it is the plain one. A **configuration** is
   the problem; an **input file** is a file it is read from. **"Frozen" is reserved** for the
   physics freeze and the predicate mode, and names no file, field or matrix cell.
2. **"outer loop" is gone, but the switch that expresses it is still composed.** §11.2 lists
   `PROCESS_ARCH_OUTER` as retired. It is retired as something an *arm chooses*; the driver still
   needs it to be told to run the schedule once, so the registry supplies it whenever the
   partitioned loop is selected, and it disappears from the driver with the renaming change.
3. **"retired" is made operational for the second tolerance.** `PROCESS_ARCH_INNER_TAU` is not
   merely never set: an environment carrying it raises. A name that is only *not used* comes back.
4. **Two intended names were missing and are supplied**: `PROCESS_ARCH_COUPLING_STATE` (today
   `…_YSTATE`) and `PROCESS_ARCH_WRITE_SETS` (today `…_WRITESET`), so that the switch names follow
   the terms as §11.2 requires of the others.
5. **The single burn-time-owner switch folds two of today's switches**, and that is exact only
   because exactly one quantity is ever taken out of the loop. Today's "lift" switch takes a
   *list*; if a second quantity is ever lifted, the general form is needed back.
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

`harness/selfcheck.py` runs four checks, each with its teeth, in about half a minute, and starts no
PROCESS run.

*Caption: one row per check. "Compares" is the population; "teeth" are the deliberate breaks it is
shown to catch.*

| check | binds | teeth |
|---|---|---|
| **composition** | every arm composes on every configuration; a skipped arm refuses by name and quotes its recorded reason; the reference arms compose to every switch cleared; the arms the previous revision also ran compose to the *same switch settings* it used | a wrong value in one arm; a switch dropped from an arm; a skipped arm asked to compose |
| **rungs** | the plan's matrix regenerates cell for cell from the arm records; the difference between two arms equals the difference the plan declares for that step; no removed arm is present | a wrong expected difference; a wrong cell in the transcribed matrix; an arm compared with itself |
| **capability** | the tree resolves every switch each arm asks for, exactly as asked; an arm asking for something no tree implements is refused before anything runs | a switch name no tree defines; a switch the environment does not carry claimed as resolved; a retired name present in the environment |
| **provenance** | a modified tracked file and an untracked file are recorded separately, and only the first marks the tree dirty | each kind of change, one at a time, in a throwaway repository; and the tree asserted by a prefix instead of exactly |

Two of these deserve their reason stated.

**Why the previous revision's composition is compared.** A rewritten harness that changes the
measurement is not a rewrite; it is a new experiment. The six arms this revision shares with the
last one must compose to the same switch settings, or the difference between the two revisions'
numbers would be partly the harness. The expected settings are transcribed into `selfcheck.py`
rather than imported, because every check the experiment runs is implemented inside this package;
`--crosscheck-previous` then *executes* the previous revision's own two composition functions in a
subprocess and compares, so the transcription is measured rather than trusted.

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
- **what it achieved**: the normalised objective, the optimiser's exit code, and an audit of how
  far the coupling state still was from converged, taken at the same fixed point in every arm;
- **how it ended**: one of a small set of outcomes — finished, crashed, refused, did not converge,
  hit upstream's own pass cap, infeasible at the audit, or a machinery failure. Upstream's loop
  raising after ten passes is a *finding about the shipped code*, not a broken run, and has its
  own outcome so that the two are never confused again.

The record's schema and the code that reads it are a later task; this list is what it must carry.

---

## 10. What is not here yet

`config.py`, `switches.py`, `arms.py`, `provenance.py`, `selfcheck.py` and the runner's preflight
exist. The coupling-state module, the committed artifacts, the run path (the child process, the
two entry points, the worker pool, the record schema), the artifact and census stages, the gates
against the earlier revisions, the tally and the analysis are separate tasks. The preflight names
each missing piece and the stage that produces it rather than falling back to something that
happens to be there.

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
