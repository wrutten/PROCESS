# A47 (harness-skeleton) — the harness package skeleton and the runner's preflight

> **Document status** — **OPEN TASK REPORT**, complete, awaiting the orchestrator's assessment
> (protocol §5: the orchestrator appends a critical assessment before the merge, and it gates the
> merge). Task **A47 (harness-skeleton)**, branch `A47-harness-skeleton` off
> `architecture_surgery` at `f2dc9243`. Implements task **H1** of the approved V4 harness plan
> [`../plans/V4_HARNESS_IMPLEMENTATION_PLAN.md`](../plans/V4_HARNESS_IMPLEMENTATION_PLAN.md).
> Every number below is produced by executing
> [`arch_surgery/MDA_partitioning_experiment_v4/harness/selfcheck.py`](../../MDA_partitioning_experiment_v4/harness/selfcheck.py)
> or
> [`arch_surgery/MDA_partitioning_experiment_v4/experiment_runner.py`](../../MDA_partitioning_experiment_v4/experiment_runner.py)
> at commit **`7aba492e`** (protocol §15: every published number comes from a committed script).
> **No PROCESS run was made by this task**, and no file outside
> `arch_surgery/MDA_partitioning_experiment_v4/` was created or changed.

| | |
|---|---|
| **Verdict** | **PASS.** Eight arms on three configurations compose from one implementation; the composed environments of the six arms the previous revision (V3) also ran are equal to V3's **switch for switch**, verified twice — against a transcription and against V3's own two composition functions executed in a subprocess, **17 of 17 arm/configuration pairs, 0 mismatches, both routes**. The experiment plan's §3.2 matrix regenerates from the arm records **88 of 88 cells**, and all **6** rung steps reproduce the plan's declared differences. The capability probe examined **22** arm/configuration pairs: **17** probed and resolved every switch exactly as asked, **5** refused before probing because they declare a switch **no tree implements yet**. Provenance separates a tracked modification from an untracked file over three states of a throwaway repository. **Fourteen teeth, fourteen tripped.** Total run time ≈ 30 s, no PROCESS run. |
| **What this delivers** | `harness/{__init__,config,switches,arms,provenance,selfcheck}.py`, `harness/README.md` and `experiment_runner.py` with preflight only — 3 712 lines. Plus the **V4 names of the four per-configuration committed artifacts** (§4.2), which the queue row for A48 (harness-data) defers to this task. |
| **Two findings inside the approved plan** | (i) The rung from the flat control to the optimiser-owned burn time (`B0 → B1`) moves **two** fields, not one — burn-time ownership *and* the output-time loop — while the plan's rung table names only ownership. The matrix places it there deliberately, so that the next rung matches its Phase A twin exactly; the *isolates* wording is what is incomplete. (ii) The matrix gives `A1` the output-time loop while §3.3's keep-list omits `A1`. Both are flagged, not fixed: the plan is not this task's to amend. §6. |
| **One structural consequence, stated plainly** | On the tree as it stands, **`B1` and `B3` cannot be run at all** — they declare the output-time-loop switch, which the approved-but-unmade driver change DR2 supplies. The harness **refuses** them rather than composing an environment without it; that is a change from V3, which would have run them with the switch simply absent. §5.2. |
| **Nothing needing a decision blocks the merge** | Two items want the orchestrator's ruling before the *plan* is next amended (§6), and one wants a ruling before the run-path task is written (§7 item 9). Neither blocks this branch. |

---

## 1. Terms used in this report

Project shorthand is spelled out at first use (protocol §4). The same vocabulary, at length and in
plain language, is [`harness/README.md`](../../MDA_partitioning_experiment_v4/harness/README.md) §3.

*Caption: one row per term; the meaning is the one this repository uses. "Decision `D<n>`" is a
recorded ruling by the user; "task `A<n> (keyword)`" is a queue row; "trap `T<n>`" is a recorded
way this project has already been misled.*

| term | meaning |
|---|---|
| **driver** | the arrangement of loops and solvers around PROCESS's physics models — the experiment's only independent variable |
| **model** | one physics or engineering calculation. Frozen at the base commit; changing one invalidates the experiment (**D5**) |
| **arm** | one complete setting of the driver's environment switches; one column of the experiment plan's §3.2 matrix |
| **rung** | a pair of adjacent arms differing by one named thing, so a cost difference can be attributed to that thing |
| **configuration** | one optimisation problem (one plant, one objective, one constraint set). V3 called it a *deck*; V4 keeps "deck" for the input **file** |
| **coupling state** | the set of numbers the models pass to each other; what the analysis loop converges |
| **τ (tolerance)** | how small a scaled change in the coupling state counts as converged. **One value for every loop in every arm** — decision **D23** (user, 2026-09-10) |
| **teeth** | a check's demonstrated ability to fail: a deliberate break it must catch before its zeros are believed (protocol §12) |
| **capability probe** | a child process that imports the driver under an arm's environment and reports what it *resolved* |
| **pending switch** | something an arm declares that no tree implements yet, because the driver change supplying it has not been made |
| **D22** | the user's ruling of 2026-09-10 removing the arm `B2` (the partitioned arm that repeated its block schedule) from the arm set |
| **D23** | the user's ruling of 2026-09-10 that one tolerance, 1e-6, governs every converger in every arm, both phases |
| **DR1 / DR2 / DR4 / DR5 / DR7** | the five approved driver changes of the harness plan §3.2: the switch renames; the output path without the output-time loop; predicate-evaluation counters; the predicate mode; per-attempt node-call accounting. All are made in V4's own copy of PROCESS and none is made by this task |
| **trap T6** | a `git worktree` does not redirect the editable install, and a *prefix* assertion on the imported package's path passes on the main checkout even when the run is meant to measure a worktree |
| **trap T10** | `process.__version__` can report a different commit than the tree actually contains, so the assertion must be on the path and never on the version |
| **trap T11** | a number published without the population it holds over; this project has twice published a zero over a population quietly smaller than the one it named |

---

## 2. What was built

*Caption: one row per file this task added. "Lines" is `wc -l` at commit `6713c07b`. Nothing else
in the repository was created or changed.*

| file | lines | what it owns |
|---|---|---|
| `…_v4/harness/config.py` | 417 | `Config` and `Campaign` as frozen dataclasses; the declared settings of the experiment plan §3.10; the configuration list and its removal mechanism; `EXECUTION_APPROVED` |
| `…_v4/harness/switches.py` | 672 | the switch vocabulary as data; `clear_all`; the retired-name refusal; the capability probe and `assert_capable` |
| `…_v4/harness/arms.py` | 575 | the plan's §3.2 matrix and rung table as data; `env_for`, `deck_for`, `rung` |
| `…_v4/harness/provenance.py` | 222 | the interpreter refusal, the exact-tree assertion, the git stamp with the two kinds of dirt separated |
| `…_v4/harness/selfcheck.py` | 968 | four checks and their teeth, plus the opt-in cross-check against V3's own composition |
| `…_v4/harness/README.md` | 388 | the package in plain language, for a reader new to the project |
| `…_v4/harness/__init__.py` | 119 | the version string and the one public import surface |
| `…_v4/experiment_runner.py` | 351 | the button: preflight only; campaign stages refuse and say why |

Four design choices are worth naming, because each replaces something the harness plan's inventory
found wrong with the previous revision.

**One composition instead of two.** V3 built an arm's environment in two separate chains of `if`
statements — `v3_runner.env_for` for the optimisation phase and `phase_a.env_for_phase_a` for the
evaluation phase — over the same vocabulary, and they had already drifted apart in two places.
Here an `Arm` is a record with one field per matrix row, and `Arm.terms()` is the single place an
arm becomes switch settings.

**Capability is measured, not declared.** V3 carried a hand-edited dictionary of booleans saying
what a human believed the tree could do, and the inventory found it consulted on one code path and
not the other. It is replaced by a child process that imports the driver and reports what it
resolved.

**A skip is a record, not an absence.** `Config.skips` maps an arm to the reason it is inactive,
and asking for it raises with that reason quoted.

**No count is written by hand.** The run budget the runner prints — 275 displaced-entry
evaluations, 418 stencil-point evaluations, 275 optimisations — is derived from the configuration
list, the arm set and the declared sample size. It reproduces the experiment plan §3.10's figures
exactly, which is a check on both.

---

## 3. The gates, with their teeth

All five checks were run at commit `7aba492e` by
`harness/selfcheck.py --crosscheck-previous`, against the repository's own PROCESS tree. The
experiment's own copy is A46 (process-copy)'s, which merged on `architecture_surgery` while this
task was open; this branch is off `f2dc9243`, which predates that merge, so the copy is absent
here and the checks were run against the repository's tree instead. The tree was stamped with **0 tracked modifications** (its
own split working: the only thing outstanding at the time was this report, a tracked file, which
the stamp duly reports), head `7aba492e`.

*Caption: one row per check. "Compared" is the number of things actually compared — the
denominator (protocol §12); "mismatched" is how many of them disagreed. "Teeth" is the number of
deliberate breaks the check was shown to catch, over the number tried. Run time ≈ 30 s in total;
no PROCESS run.*

| check | binds | compared | mismatched | teeth tripped |
|---|---|---|---|---|
| composition | every arm composes on every configuration; skips refuse by name; reference arms compose to every switch cleared; the six shared arms equal V3's composition switch for switch | 25 | 0 | 4 / 4 |
| rungs | the plan's §3.2 matrix regenerates cell for cell; each rung's computed difference equals the plan's declared difference; no removed arm present | 98 | 0 | 3 / 3 |
| capability | the tree resolves every switch each arm asks for; an arm asking for an unimplemented switch is refused before anything runs | 22 | 0 | 3 / 3 |
| provenance | a tracked modification and an untracked file are recorded separately, and only the first marks the tree dirty | 3 | 0 | 3 / 3 |
| cross-check against V3 | the transcription of V3's composition matches what V3's own code produces | 17 | 0 | 1 / 1 |

### 3.1 What each denominator is

- **composition, 25**: 8 arms × 3 configurations = 24 pairs (22 composed, 2 refused as recorded
  skips), plus 1 comparison of the configuration-removal mechanism.
- **rungs, 98**: 11 matrix rows × 8 arms = 88 cells, plus 6 rung steps, plus 3 twin-declarations,
  plus 1 check that no removed arm is present.
- **capability, 22**: every arm/configuration pair whose arm is active — 24 minus the 2 recorded
  skips. **17** were probed in a child process each and resolved every switch as asked; **5**
  were refused before probing (`B1` and `B3` on the two pulsed configurations, `B3` on
  `st_regression`) because they declare the output-time-loop switch, which no tree implements.
- **provenance, 3**: three states of one throwaway git repository — clean, one tracked file
  modified, one untracked file added.
- **cross-check, 17**: 6 arms × 3 configurations = 18, minus `B1` on `st_regression`, which is a
  recorded skip.

### 3.2 The fourteen teeth

*Caption: one row per deliberate break. Every one tripped its check. A check whose failure mode has
never been exercised is an assertion, not a measurement (protocol §12).*

| check | tooth | what was broken |
|---|---|---|
| composition | a wrong switch value in one arm | `B0`'s analysis-loop switch set to the partitioned value must not match V3's `B0` |
| composition | one switch dropped from an arm | `B3` without the method-arrangement switch must not match V3's `B3` |
| composition | the wrong per-run artifact handed to an arm | the evaluation phase's block arm runs the frozen deck, so it takes the artifact stamped for the base constraint set; handing it the lifted deck's artifact must not match |
| composition | a skipped arm asked to compose | `A0p` on `st_regression` must refuse and quote its recorded reason |
| rungs | a wrong expected difference | the partitioning rung with one deferral removed from its declared difference |
| rungs | a wrong cell in the transcribed matrix | `B1`'s burn-time owner written as the loop |
| rungs | an arm compared with itself | an empty difference must be reachable, so a non-empty one means something |
| capability | a switch name no tree defines | an invented switch with an invented readback must be refused |
| capability | a switch the environment does not carry, claimed as resolved | asking for the partitioned loop with the variable unset must be refused |
| capability | a retired name present in the environment | the second tolerance, retired by D23, must raise rather than be cleared and forgotten |
| provenance | a tracked file modified | must be counted as a tracked modification, not as untracked, and must mark the tree dirty |
| provenance | an untracked file beside the runner | must be counted as untracked, not as a modification, and must **not** mark the tree dirty |
| provenance | the tree asserted by a prefix instead of exactly | the parent directory of the tree under test must be refused (trap T6) |
| cross-check | a wrong value in the transcription | the per-call deferral transcribed without its lifted variant must not match V3's output on a pulsed configuration |

### 3.3 Why V3's composition is compared twice

A rewritten harness that changes the measurement is not a rewrite; it is a new experiment. The six
arms V4 shares with V3 (`A0`, `A1`, `B0`, `B1`, `B3`, and V3's `R` renamed `BR`) must compose to
the same switch settings, or a difference between the two revisions' numbers would be partly the
harness.

The harness plan's §6 carries the user's binding requirement that **every verification gate is
implemented inside `harness/`**, with nothing imported from `arch_surgery/idf_probe/` or
`arch_surgery/fixedpoint/`. Importing `v3_runner` would pull five modules of superseded task
machinery onto the import path to obtain six dictionaries. So the committed check compares against
a **transcription** of V3's two composition functions, written into `selfcheck.py` with the source
lines cited.

A transcription compared against one's own code proves less than it appears to, so
`--crosscheck-previous` **executes** V3's `v3_runner.env_for` and `phase_a.env_for_phase_a` in a
subprocess and compares their output with the transcription: **17 of 17, 0 mismatches**, with a
tooth. It is opt-in, is not one of the four gates, and is labelled in the code as deliberately
reaching outside the package for exactly this one purpose. Comparison of path-valued switches is on the artifact's **role**, not its
file name (§4.2): V4's own copy of the artifacts is named for what each file is *for*, so a rename
must compare equal while handing an arm the wrong artifact must not — and there is a tooth for
exactly that.

### 3.4 The preflight, run both ways

*Caption: the button's outcome at commit `6713c07b`, against each of the two trees. Exit codes:
0 ready · 2 refused to start · 3 not ready.*

| invocation | outcome | exit |
|---|---|---|
| `experiment_runner.py --tree repository` | READY: interpreter accepted, tree stamped, 3 configurations resolved with 0 artifacts missing, matrix and rungs PASS (98/0), capability PASS (22 examined) | 0 |
| `experiment_runner.py` (the default: V4's own copy of PROCESS) | NOT READY: the copy does not exist in this worktree, and each of the 18 artifact entries it would resolve (13 distinct files) is named as missing. Nothing falls back to another tree | 3 |

The second row is the failure path, reached from the same entry point as the success path
(protocol §15). It will become the first row when A46 (process-copy) merges.

---

## 4. Naming and terminology

The user's three notes on the harness plan (§11) are binding. Two are this task's.

**No task numbers and no version tokens in file, class or function names** (§11.1). Nothing this
task added carries one. Heritage is in docstrings: each module names the file it descends from and
the commit — for example `arms.py` names
`arch_surgery/MDA_partitioning_experiment_v3/v3_runner.py::env_for` at `f2dc9243`. Where the code
must refer to the previous revision at all it says "the previous revision", not "V3".

**The README is in plain language** (§11.4), for a reader who has not followed the project: what
the experiment measures and why the models are frozen, what one run does end to end, every term in
one sentence, the switch registry with all three names per switch, how to run the button and a
single arm, how to add an arm or a configuration, where records go and what a record contains, and
what the gates prove. No decision, issue or task number appears without its meaning beside it.

### 4.1 The terminology table, as finalised

The harness plan §11.2 fixed the vocabulary and gave this task the job of finalising it. Nine
changes and additions were made. The full table in force is
[`harness/README.md`](../../MDA_partitioning_experiment_v4/harness/README.md) §3; what follows is
only what *differs* from §11.2, with the reason.

*Caption: one row per change to the harness plan's §11.2 terminology table. "Kind" is whether the
row changes a term §11.2 fixed, adds one it does not have, or corrects a switch name. Every change
is recorded here so §11.2 can absorb it.*

| # | kind | what changed | why |
|---|---|---|---|
| 1 | changed | **"configuration" and "deck" are both kept**, for different things: a configuration is the *problem*, a deck is an input *file* | §11.2 replaced "deck" outright, but a configuration has two files — the frozen one and the derived one that hands the burn time to the optimiser — so a word for the file is still needed. `deck_for()` keeps its V3 name because it answers "which file", not "which problem" |
| 2 | changed | **"outer loop" is gone as a term, but `PROCESS_ARCH_OUTER=trust` is still composed**, by the registry, whenever the partitioned loop is selected | §11.2 lists the variable as retired. It is retired as something an *arm chooses*; the driver still has to be told not to repeat the schedule. Making it a registry consequence rather than an arm field is what lets D23's "one kind of loop" be true of the arm records while the tree still needs the variable. It leaves the driver with the rename |
| 3 | changed | **"retired" is made operational**: `PROCESS_ARCH_INNER_TAU` is not merely never set — an environment carrying it **raises** | a name that is only *not used* comes back. This is the live content of the retired-name mechanism; the renamed deferral switches join it when the rename lands, and the registry is the only file that changes |
| 4 | added | two intended names §11.2 omits: **`PROCESS_ARCH_COUPLING_STATE`** (today `…_YSTATE`) and **`PROCESS_ARCH_WRITE_SETS`** (today `…_WRITESET`) | §11.2 renames the terms ("coupling state", "write sets") but leaves these two switch names at their old spellings, which is the inconsistency the note exists to remove |
| 5 | noted | **`PROCESS_ARCH_BURN_TIME_OWNER` folds two of today's switches** (the lift and the pin), and is exact only because exactly one quantity is ever taken out of the loop | today's lift switch takes a *list* of sites. If a second quantity is ever lifted, the general form is needed back. Recorded so the collapse is not mistaken for a simplification that always holds |
| 6 | added | five terms §11.2 has no row for: **rung**, **stopping rule**, **skip**, **capability probe**, **pending switch** | each is a thing the harness has to name in a refusal message, and a refusal that uses an undefined word is a refusal a reader cannot act on |
| 7 | changed | **four of the plan's eleven matrix rows are regenerated, not stored**: the stopping rule, the outer loop, whether the burn time is out of the loop, and which deck is read | each follows from another row. Storing them would make a one-thing rung look like a four-thing rung. The whole table is regenerated and compared with the plan's, cell for cell, so the plan's table still prints exactly as written |
| 8 | flagged | two places where the experiment plan disagrees with itself (§6 below) | flagged, not fixed: the plan is not this task's to amend |
| 9 | flagged | **run directories should be named for the seed** (`seed001`), not `start001` | §11.2 makes "seed" the word in both phases, but the harness plan's run-layout decision (5) still writes `start001`. The task that builds the run path should settle it |

The rest of §11.2 is adopted unchanged: **arm**; **flat** / **partitioned**; **block loop** and
one τ; **deferral `per_call` / `per_run`**; **arrangement · node** / **arrangement · method**;
**burn-time owner** loop / constant / optimiser; **reference arm**; **seed** in both phases;
**coupling state**; **output-time loop**; **stencil regime** / **δ regime**; **teeth**, **tally**,
**analysis**.

### 4.2 The names of the committed artifacts, decided here

While this task was open, **A46 (process-copy) merged** and the orchestrator minted **A48
(harness-data)** for the remainder of the copy task — `harness/data/` and `harness/ystate.py` —
and **queued it behind this task**, with the reason recorded in the queue row: *"the skeleton's
environment composer decides the names"*. So the names are settled here.

Three of the composed switches are handed a file. Their existing names carry the number of the
task that first produced them (`ystate_a26_…`) and use words the vocabulary has since replaced,
both of which the harness plan's naming note forbids. The names below say what each file is for.

*Caption: one row per committed per-configuration artifact. `{name}` is the configuration's name.
The last two rows are fixed by path constants inside the copied driver — A46 (process-copy)
re-pointed them at `harness/data/node_writesets.json` and `harness/data/dsm_node_map.json` — so
renaming either is a driver edit and neither is renamed here.*

| what the file is | name in `harness/data/` | name in `arch_surgery/docs/data/` |
|---|---|---|
| the coupling state's components and their measured scales | `coupling_state_{name}.json` | `ystate_a26_{name}.json` |
| which of those components each block writes | `write_sets_{name}.json` | `writeset_a26_{name}.json` |
| the nodes deferred to once per run, for a run of the lifted deck | `defer_per_run_{name}.json` | `postsolve_{name}.json` |
| the same node set, stamped for a run of the frozen deck | `defer_per_run_frozen_deck_{name}.json` | `postsolve_nolift_{name}.json` |
| what each node writes, measured | `node_writesets.json` | `node_writesets.json` |
| which block each node belongs to | `dsm_node_map.json` | `dsm_node_map.json` |

That makes **11 per-configuration files** — on the steady-state configuration the last two rows of
the first group are the same file — plus the **2** the driver's constants fix: **13 files** for
A48 to copy, each byte-identical to its original.

Both spellings resolve. `config.ARTIFACT_NAMES` holds the two schemes and
`default_configurations(..., naming=…)` selects one, so `default_campaign()` (the experiment's own
copy) and `repository_tree_campaign()` (the shared directory, as the earlier revisions read it)
differ in one argument and neither set of names is written out twice.

One consequence, and it improves the check rather than weakening it: the comparison against the
previous revision's composition is on the artifact's **role**, not its file name. A rename
therefore compares equal, and handing an arm the *wrong* artifact still compares unequal — with a
tooth that does exactly that, swapping the two per-run artifacts on a pulsed configuration. That
swap is a defect the previous revision's duplicated composition could have produced, since it made
the same choice twice in two files.

---

---

## 5. Autonomous decisions, with their reversal paths

*Caption: one row per choice this task made without asking. "Reversal" is what it would cost to
undo, so that none of them is load-bearing by accident.*

| # | decision | why | reversal |
|---|---|---|---|
| 1 | **An arm declaring a switch no tree implements is refused, not composed without it.** `env_for(..., pending_ok=True)` returns the partial environment for *inspection* only; the run path never passes it | composing without the switch would run a different arm under this arm's name — the failure the capability probe exists to prevent. The flag is keyword-only and greppable, so it cannot happen by accident | delete the flag and the refusal; three lines in `arms.py` |
| 2 | **`PROCESS_ARCH_OUTER=trust` is supplied by the registry when the partitioned loop is selected, rather than being an arm field** | the brief and D23: the partitioned arms run the schedule once, so it is a consequence of the loop, not a choice. The plan's matrix row is regenerated from it, so the plan's table is unchanged | make it an `Arm` field and add a column to `PLAN_MATRIX`; about ten lines |
| 3 | **The per-run deferral artifact is chosen from the deck the arm reads**, not from which phase it belongs to | V3 chose `postsolve_nolift_*` in the evaluation phase and `postsolve_*` in the optimisation phase — the same decision written twice. Both spellings are reproduced exactly by the one rule, verified against V3's own code | restore the phase test in `Config.per_run_artifact`; two lines |
| 4 | **Every probe variable is cleared, not only the parent one.** V3 cleared `PROCESS_IDF_PROBE`; V4 clears its twelve companions too | they are inert while the parent is unset, so clearing them changes nothing measurable and removes a way for an inherited value to matter later. The comparison with V3 is over variables *set*, so it is unaffected | remove them from `PROBE_VARIABLES` |
| 5 | **The V3-equality check compares path-valued switches by the artifact's role**, not by path or file name | V4's copy of the artifacts is renamed (§4.2), so a file-name comparison would fail for the one reason that is not a defect, while a role comparison still fails when an arm is handed the wrong artifact — which is a defect V3's duplicated composition could have produced. There is a tooth for it | compare file names and add a rename map |
| 5a | **The V4 names of the four per-configuration artifacts were decided here** (§4.2), because the queue row for A48 (harness-data) says the skeleton's environment composer decides them, and A48 is queued behind this task for that reason | the old names carry a task number, which the naming note forbids, and use words the vocabulary has replaced. Both spellings resolve, selected by a `naming` argument, so neither is written twice | change the four templates in `ARTIFACT_NAMES`; one dictionary in `config.py` |
| 6 | **`Campaign.tree` and `Campaign.data_dir` are parameters, defaulting to V4's own copy**; a second constructor points the whole campaign at the repository's tree | the copy is another task's and did not exist here. The default is the production target, so the checking variant has to be asked for explicitly and cannot be reached by forgetting a flag | drop `repository_tree_campaign()`; the self-check then needs the copy present |
| 7 | **`default_campaign()` is a function, not a module-level instance** | a settings object anything can reach and rebind is the module global the plan asked to remove | make it a constant |
| 8 | **The cross-check against V3's own composition is committed but opt-in**, and is not one of the four gates | it deliberately reaches outside `harness/`, which the user's requirement forbids for *gates*. Keeping it, labelled, measures the transcription instead of trusting it; keeping it out of the gate set honours the requirement | delete `crosscheck_previous`; the transcription then stands on review alone |
| 9 | **The self-check's capability probe runs the full matrix** (17 child processes at 3 workers, ≈ 20 s) rather than a deduplicated subset | a subset would have to decide which differences do not matter, and the artifact paths differ per configuration precisely where a mistake would hide | probe one representative per switch signature; ≈ 9 s instead of 20 s |

### 5.1 What was deliberately **not** done

- **No file under `process/`, `arch_surgery/idf_probe/`, `arch_surgery/fixedpoint/`,
  `…_v2/` or `…_v3/` was read into the harness or changed.** The four modules of V3 named in the
  brief were read; nothing was imported from them at run time except by the opt-in cross-check,
  which runs in a subprocess.
- **Nothing under `…_v4/PROCESS/`, `…_v4/harness/data/`, `harness/ystate.py`, `harness/child.py`
  or the run path was created**; the first belongs to A46 (process-copy), which merged while this
  task was open, the next two to A48 (harness-data), and the rest to later tasks. This branch is
  off `f2dc9243`, which predates A46's merge, so V4's copy of PROCESS is absent from this
  worktree; §4.2 records the names A48 needs from here.
- **No driver change was made.** The five approved ones are separate tasks with their own gates.
- **No PROCESS run.** The capability probe imports three driver modules in a child process and
  reads module-level names; it calls no model and opens no output file.

### 5.2 The consequence worth stating twice

On the tree as it stands, **`B1` and `B3` are not runnable**. They declare the output-time-loop
switch, which the approved driver change DR2 will supply and which no tree implements today. The
harness refuses them, by name, with the driver change named in the refusal. V3 had no such switch
at all and would simply have run those arms with upstream's output-time loop on.

This is the designed behaviour — "refuse, never degrade" — and it is the first thing that will
change when DR2 lands. It also means the composition equality with V3 currently holds **exactly**
for `B1` and `B3`: once DR2 lands they will differ from V3 by that one switch, by design. The
self-check states the pending switches per arm on every run, so that difference cannot arrive
unnoticed.

---

## 6. Two disagreements inside the approved experiment plan

Neither is this task's to fix. Both are recorded in the code (in `RUNGS`, printed by the runner)
and are raised here for the orchestrator.

**(i) The `B0 → B1` rung moves two fields, not one.** The experiment plan's §3.2 matrix gives
`B1` and `B3` the output-time loop set to *none*, and `AR A0 A0p A1 BR B0` *upstream*. So the step
`B0 → B1` changes **burn-time ownership and the output-time loop**, while the rung table's
"isolates" column names only ownership. The placement looks deliberate: putting the output-loop
change at that step makes the next step — `B1 → B3`, the partitioning intervention — move exactly
the same five fields as its Phase A twin `A0p → A1`, which is what lets a Phase A ratio be read
against its Phase B twin. So the matrix is probably right and the *isolates* wording incomplete.
The harness declares both fields and prints the note. **Two ways to settle it**: amend the rung
table's `B0 → B1` row to name the output-time loop; or move the output-loop change to `B3` only,
which would make `B1 → B3` move six fields and break the twinning. The first looks right; it is
the user's or the orchestrator's call.

**(ii) `A1`'s output-time-loop cell.** The matrix gives `A1` *upstream*; §3.3's prose lists the
arms that keep the output-time loop as `AR, A0, A0p, BR, B0` — omitting `A1` — and then says "the
intervention arms do not run it". It makes no difference to any measurement: Phase A runs one
evaluation of the model set and never reaches the output path. The cell and the sentence should be
made to agree, most cleanly by marking the Phase A cells *not applicable*.

---

## 7. What a later task must fill in

*Caption: one row per piece the harness plan's §4.1 lists that this task did not build, and what
it must satisfy. "Owner" is the plan's task letter; the queue mints the task label when its
predecessor merges.*

| owner | piece | what it must satisfy that this task already assumes |
|---|---|---|
| H0 / **A46 (process-copy)**, **merged 2026-09-10** | `…_v4/PROCESS/process/` with its three re-pointed path constants, `PROCESS_diff.py`, the `.gitignore` for `runs/` | `Campaign.tree` defaults to exactly `…_v4/PROCESS`, which the merged copy provides |
| H0 remainder / **A48 (harness-data)**, queued behind this task | `…_v4/harness/data/` and `harness/ystate.py` | `Campaign.data_dir` defaults to `…_v4/harness/data`; the 13 files and their V4 names are §4.2's table, which A48's queue row defers to this task; the preflight names all 18 artifact entries it resolves by exactly those names |
| H2 | the reproduction reference extracted from V3's records | `switches.PREVIOUS_ARM_NAMES` maps V3's `R` to `BR` and `switches.RETIRED_ARM_NAMES` names `A1u` and `B2`; a lookup that misses must raise |
| H3 | the run path: the child process, the two entry points, the worker pool, the record schema, the perturbation stream and the predicate layer | must call `switches.assert_capable` before starting any run, must set `PYTHONPATH` to `Campaign.tree` and assert the exact tree inside the child, and must record the arm's environment **as the driver resolved it**. Run directories should be named `seed001`, not `start001` (§4.1 item 9) |
| H4 | the artifact, deck, census and per-run-set stages | the preflight's artifact check here is existence plus the declared component count; the full validation — format, the components checksum rebuilt, the expected objective, the constraint set, the predicate mode — is that task's |
| H5 | every verification gate, reimplemented inside `harness/` | `selfcheck.py`'s `Check` record is a working shape but is **not** the plan's `Gate`/`Tooth` pair; H5 should promote it, keeping the rule that a gate with no tooth cannot be registered |
| H6 / H7 | the tally, the independent analysis and `--verify` | every population must derive from `Campaign.population`; `Campaign.without_configuration` exists so that removing a configuration re-derives every count rather than patching one |
| DR1 | the switch renames | `switches.REGISTRY` already carries `intended_name` for every switch and the retired-name refusal. When the rename lands, that file is the only one that changes, and the retired names move into the switch's `retired_names` tuple |
| DR2 | the output path without the output-time loop | the `output_loop` switch already exists in the registry with `driver_name = None` and a readback of `caller.OUTPUT_LOOP_NAME`; supplying the switch under that name and readback makes `B1` and `B3` runnable with no harness change |
| DR5 | the predicate mode | same shape: `predicate_mode` is registered with `driver_name = None` and a readback of `module_solve.PREDICATE_MODE` |

---

## 8. Reproducing every number in this report

```bash
PY=/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python
cd arch_surgery/MDA_partitioning_experiment_v4

# §3, all five checks and thirteen teeth (~30 s, no PROCESS run)
$PY harness/selfcheck.py --crosscheck-previous --json runs/selfcheck.json

# §3.4, the two preflight outcomes
$PY experiment_runner.py --tree repository   # READY, exit 0
$PY experiment_runner.py                     # NOT READY, exit 3
```

Both scripts were committed — the package in `6713c07b`, the artifact naming in `7aba492e` —
**before** the numbers above were taken, and the JSON record carries the tree, the head commit, the
configuration list and every check's population, denominator and teeth. The numbers are identical
at both commits; `7aba492e` adds the fourteenth tooth.

---

## 9. Change log (append-only)

- **2026-09-10** — task **A47 (harness-skeleton)** opened on branch `A47-harness-skeleton` off
  `architecture_surgery` at `f2dc9243`. Read `CLAUDE.md`, `TRAPS.md`, the orchestration protocol,
  the V4 harness implementation plan in full and the V4 experiment plan §1.3 / §3.2 / §3.3 / §3.7 /
  §3.10 / Appendix A, and V3's `v3_runner.py`, `phase_a.py`, `v3_config.py` and the driver's
  module-level switch definitions in `process/core/caller.py`,
  `process/core/solver/module_solve.py` and `process/core/solver/subsolve.py`.
- **2026-09-10** — commit `6713c07b`: `harness/{__init__,config,switches,arms,provenance,
  selfcheck}.py`, `harness/README.md` and `experiment_runner.py`. Five checks PASS, thirteen teeth
  tripped, no PROCESS run. Two disagreements inside the experiment plan flagged (§6); nine
  terminology decisions recorded (§4.1); nine autonomous decisions recorded with their reversals
  (§5).
- **2026-09-10** — commit `7aba492e`, after A46 (process-copy) merged on `architecture_surgery`
  and A48 (harness-data) was minted and queued behind this task with the artifact names deferred
  to it: the two naming schemes in `config.ARTIFACT_NAMES`, the V4 names of the four
  per-configuration artifacts (§4.2), and the previous-revision comparison moved from file names
  to artifact **roles**, with a fourteenth tooth that swaps the two per-run artifacts. Five checks
  PASS, fourteen teeth tripped, populations unchanged (25 / 98 / 22 / 3 / 17, 0 mismatches).
  This branch is off `f2dc9243` and therefore does not contain A46's merge; nothing here depends
  on it beyond the default paths, which already pointed at the copy.
