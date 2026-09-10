# A47 (harness-skeleton) — the harness package skeleton and the runner's preflight

> **Document status** — **OPEN TASK REPORT**, complete, with the orchestrator's **five pre-merge
> rulings of 2026-09-10 applied and re-gated** (§4.3); awaiting re-assessment and merge
> (protocol §5: the assessment gates the merge). Task **A47 (harness-skeleton)**, branch `A47-harness-skeleton` off
> `architecture_surgery` at `f2dc9243`. Implements task **H1** of the approved V4 harness plan
> [`../plans/V4_HARNESS_IMPLEMENTATION_PLAN.md`](../plans/V4_HARNESS_IMPLEMENTATION_PLAN.md).
> Every number below is produced by executing
> [`arch_surgery/MDA_partitioning_experiment_v4/harness/selfcheck.py`](../../MDA_partitioning_experiment_v4/harness/selfcheck.py)
> or
> [`arch_surgery/MDA_partitioning_experiment_v4/experiment_runner.py`](../../MDA_partitioning_experiment_v4/experiment_runner.py)
> at commit **`56edc585`** (protocol §15: every published number comes from a committed script).
> **No PROCESS run was made by this task**, and no file outside
> `arch_surgery/MDA_partitioning_experiment_v4/` was created or changed.

| | |
|---|---|
| **Verdict** | **PASS.** Eight arms on three configurations compose from one implementation; the composed environments of the six arms the previous revision (V3) also ran are equal to V3's **switch for switch**, verified twice — against a transcription and against V3's own two composition functions executed in a subprocess, **17 of 17 arm/configuration pairs, 0 mismatches, both routes**. The experiment plan's §3.2 matrix regenerates from the arm records **88 of 88 cells**, and all **6** rung steps reproduce the plan's declared differences. The capability probe examined **22** arm/configuration pairs: **17** probed and resolved every switch exactly as asked, **5** refused before probing because they declare a switch **no tree implements yet**. Provenance separates a tracked modification from an untracked file over three states of a throwaway repository, and refuses to call a campaign pointed at any tree but the experiment's copy a campaign records may be made against. **Fifteen teeth, fifteen tripped.** Total run time ≈ 25 s, no PROCESS run. |
| **What this delivers** | `harness/{__init__,config,switches,arms,provenance,selfcheck}.py`, `harness/README.md` and `experiment_runner.py` with preflight only — 3 822 lines. Plus the **V4 names of the four per-configuration committed artifacts** (§4.2), which the queue row for A48 (harness-data) defers to this task. |
| **Two findings inside the approved plan, both since ruled** | (i) The rung from the flat control to the optimiser-owned burn time (`B0 → B1`) moves **two** fields, not one — burn-time ownership *and* the output-time loop — while the plan's rung table names only ownership. The matrix places it there deliberately, so that the next rung matches its Phase A twin exactly; the *isolates* wording is what is incomplete. (ii) The matrix gave `A1` the output-time loop while §3.3's keep-list omitted `A1`. **Both were ruled on 2026-09-10 and the plan is amended**: the matrix stands and the rung's wording is completed; and the evaluation-phase arms carry no output-time-loop switch at all, so the row reads `n/a` for them. §6. |
| **One structural consequence, stated plainly** | On the tree as it stands, **`B1` and `B3` cannot be run at all** — they declare the output-time-loop switch, which the approved-but-unmade driver change DR2 supplies. The harness **refuses** them rather than composing an environment without it; that is a change from V3, which would have run them with the switch simply absent. The pending set is **exactly those five arm/configuration pairs**; `A1` carries no such switch and runs now. §5.2. |
| **Still open** | One item only: run directories should be named for the seed (`seed001`), not `start001` — wanted before the run-path task is written, not before merge (§4.1 item 9). |

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
| **configuration** | one optimisation problem (one plant, one objective, one constraint set), named by its input file's stem. V3 called it a *deck* or a *scenario* |
| **input file** | the file a configuration is read from: the **committed** one (never edited) or its **lifted** derived copy. "Frozen" is reserved for the physics freeze and the convergence predicate's mode and names no file |
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
| `…_v4/harness/config.py` | 460 | `Config` and `Campaign` as frozen dataclasses; the declared settings of the experiment plan §3.10; the configuration list and its removal mechanism; `EXECUTION_APPROVED` |
| `…_v4/harness/switches.py` | 672 | the switch vocabulary as data; `clear_all`; the retired-name refusal; the capability probe and `assert_capable` |
| `…_v4/harness/arms.py` | 584 | the plan's §3.2 matrix and rung table as data; `env_for`, `input_file_for`, `rung` |
| `…_v4/harness/provenance.py` | 222 | the interpreter refusal, the exact-tree assertion, the git stamp with the two kinds of dirt separated |
| `…_v4/harness/selfcheck.py` | 994 | four checks and their teeth, plus the opt-in cross-check against V3's own composition |
| `…_v4/harness/README.md` | 406 | the package in plain language, for a reader new to the project |
| `…_v4/harness/__init__.py` | 125 | the version string and the one public import surface |
| `…_v4/experiment_runner.py` | 359 | the button: preflight only; campaign stages refuse and say why |

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

All five checks were run at commit `56edc585` by
`harness/selfcheck.py --crosscheck-previous`, against the repository's own PROCESS tree. The
experiment's own copy is A46 (process-copy)'s, which merged on `architecture_surgery` while this
task was open; this branch is off `f2dc9243`, which predates that merge, so the copy is absent
here and the checks were run against the repository's tree instead. The tree was stamped with **0 tracked modifications** (its
own split working: the only thing outstanding at the time was this report, a tracked file, which
the stamp duly reports), head `56edc585`.

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
  were refused before probing — **exactly** `B1` and `B3` on the two pulsed configurations and
  `B3` on `st_regression` — because they declare the output-time-loop switch, which no tree
  implements. `A1` is not among them: an evaluation-phase arm carries no switch for the
  output-time loop at all (§4.3, ruling 3).
- **provenance, 4**: three states of one throwaway git repository — clean, one tracked file
  modified, one untracked file added — plus one check that a campaign pointed at any tree but the
  experiment's own copy reports itself as not being one records may be made against.
- **cross-check, 17**: 6 arms × 3 configurations = 18, minus `B1` on `st_regression`, which is a
  recorded skip.

### 3.2 The fifteen teeth

*Caption: one row per deliberate break. Every one tripped its check. A check whose failure mode has
never been exercised is an assertion, not a measurement (protocol §12).*

| check | tooth | what was broken |
|---|---|---|
| composition | a wrong switch value in one arm | `B0`'s analysis-loop switch set to the partitioned value must not match V3's `B0` |
| composition | one switch dropped from an arm | `B3` without the method-arrangement switch must not match V3's `B3` |
| composition | the wrong per-run artifact handed to an arm | the evaluation phase's block arm runs the *committed* input file, so it takes the artifact stamped for the base constraint set; handing it the *lifted* input file's artifact must not match |
| composition | a skipped arm asked to compose | `A0p` on `st_regression` must refuse and quote its recorded reason |
| rungs | a wrong expected difference | the partitioning rung with one deferral removed from its declared difference |
| rungs | a wrong cell in the transcribed matrix | `B1`'s burn-time owner written as the loop |
| rungs | an arm compared with itself | an empty difference must be reachable, so a non-empty one means something |
| capability | a switch name no tree defines | an invented switch with an invented readback must be refused |
| capability | a switch the environment does not carry, claimed as resolved | asking for the partitioned loop with the variable unset must be refused |
| capability | a retired name present in the environment | the second tolerance, retired by D23, must raise rather than be cleared and forgotten |
| provenance | a tracked file modified | must be counted as a tracked modification, not as untracked, and must mark the tree dirty |
| provenance | an untracked file beside the runner | must be counted as untracked, not as a modification, and must **not** mark the tree dirty |
| provenance | a campaign pointed at a tree that is not the experiment's copy | the checking campaign must not pass for the production one, so a record cannot be made against the wrong tree by forgetting a flag |
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
| `experiment_runner.py` (the default: V4's own copy of PROCESS) | NOT READY: the copy does not exist in this worktree, and each of the 21 artifact entries it would resolve (16 distinct files, the three committed input files among them) is named as missing. Nothing falls back to another tree | 3 |

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
| 1 | changed | **"deck" is gone; the file is an *input file*, committed or lifted.** `input_file_for()`, `Config.input_file`, `Campaign.input_dir`, `Campaign.derived_input_dir`. **"Frozen" is reserved** for the physics freeze and the predicate mode and names no file, field or matrix cell | a configuration has two files, so the file needs a word, and it is the plain one. *(Ruled by the orchestrator, 2026-09-10, applying harness plan §11.2; this task first proposed keeping "deck" for the file, which the ruling rejected as jargon and as a collision with the reserved word "frozen".)* |
| 2 | changed | **"outer loop" is gone as a term, but `PROCESS_ARCH_OUTER=trust` is still composed**, by the registry, whenever the partitioned loop is selected | §11.2 lists the variable as retired. It is retired as something an *arm chooses*; the driver still has to be told not to repeat the schedule. Making it a registry consequence rather than an arm field is what lets D23's "one kind of loop" be true of the arm records while the tree still needs the variable. It leaves the driver with the rename |
| 3 | changed | **"retired" is made operational**: `PROCESS_ARCH_INNER_TAU` is not merely never set — an environment carrying it **raises** | a name that is only *not used* comes back. This is the live content of the retired-name mechanism; the renamed deferral switches join it when the rename lands, and the registry is the only file that changes |
| 4 | added | two intended names §11.2 omits: **`PROCESS_ARCH_COUPLING_STATE`** (today `…_YSTATE`) and **`PROCESS_ARCH_WRITE_SETS`** (today `…_WRITESET`) | §11.2 renames the terms ("coupling state", "write sets") but leaves these two switch names at their old spellings, which is the inconsistency the note exists to remove |
| 5 | noted | **`PROCESS_ARCH_BURN_TIME_OWNER` folds two of today's switches** (the lift and the pin), and is exact only because exactly one quantity is ever taken out of the loop | today's lift switch takes a *list* of sites. If a second quantity is ever lifted, the general form is needed back. Recorded so the collapse is not mistaken for a simplification that always holds |
| 6 | added | five terms §11.2 has no row for: **rung**, **stopping rule**, **skip**, **capability probe**, **pending switch** | each is a thing the harness has to name in a refusal message, and a refusal that uses an undefined word is a refusal a reader cannot act on |
| 7 | changed | **four of the plan's eleven matrix rows are regenerated, not stored**: the stopping rule, the outer loop, whether the burn time is out of the loop, and which input file is read | each follows from another row. Storing them would make a one-thing rung look like a four-thing rung. The whole table is regenerated and compared with the plan's, cell for cell, so the plan's table still prints exactly as written |
| 8 | **ruled** | two places where the experiment plan disagreed with itself (§6 below) | found here, ruled by the orchestrator on 2026-09-10, and the plan amended. The code now carries the reason rather than a flag |
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
| the nodes deferred to once per run, for a run of the **committed** input file — the unmarked default | `defer_per_run_{name}.json` | `postsolve_nolift_{name}.json` |
| the same node set, stamped for a run of the **lifted** input file | `defer_per_run_lifted_{name}.json` | `postsolve_{name}.json` |
| what each node writes, measured | `node_writesets.json` | `node_writesets.json` |
| which block each node belongs to | `dsm_node_map.json` | `dsm_node_map.json` |

The two schemes mark **opposite** members of the per-run pair: V3 marked the committed input
file's artifact (`postsolve_nolift_`) and left the lifted one plain; V4 marks the lifted one and
leaves the committed one plain, because the committed input file is what most arms run. Because
that cannot be derived, `config.artifact_file_names()` states the steady-state configuration's
single artifact explicitly — it has no lifted input file, so both roles resolve to one file.

That makes **11 per-configuration artifacts**, plus the **3 committed input files** (which move
into `harness/data/` too, so that a run reads nothing from `idf_probe/` — ruling 2 of §4.3), plus
the **2** the driver's constants fix: **16 files** for A48 (harness-data) to copy, each
byte-identical to its original. The preflight against the copy names all **21 artifact entries**
it resolves.

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

### 4.3 The orchestrator's five pre-merge rulings, applied

Recorded at the orchestrator's assessment of this task. Each is **the orchestrator, 2026-09-10,
applying harness plan §11.2**; the experiment plan's §1.3, §3.2 and §3.3 and the harness plan's
§11.2 were amended on trunk in the same round (trunk commit `6f3c8e3a`), and the transcriptions
here were taken from those amended sections, not from the earlier text. This branch was **not**
merged with trunk; only the strings were read.

*Caption: one row per ruling, what changed in this package, and how it was re-gated. All five are
in commit `56edc585`.*

| # | ruling | applied here | re-gated by |
|---|---|---|---|
| 1 | **"deck" goes**; the word for the file is **input file**, *committed* or *lifted*, and **"frozen" is reserved** for the physics freeze and the predicate mode | `deck_for()` → `input_file_for()`; `Config.deck` → `Config.input_file`; `Campaign.derived_decks_dir` → `derived_input_dir`. The per-run artifacts swap marking: `defer_per_run_{name}.json` is the **committed** input file's (V3 `postsolve_nolift_{name}.json`) and `defer_per_run_lifted_{name}.json` the lifted one's (V3 `postsolve_{name}.json`). Matrix row `input file ⁺`, cells `committed` / `lifted`, transcribed from the amended §3.2 | the matrix check, 88 of 88 cells; the previous-revision comparison, 17 of 17, with the swap tooth rewritten to the new marking |
| 2 | **`scenario_dir` → `input_dir`**, and for the production campaign it is `harness/data/` | `Campaign.input_dir`; `default_campaign()` resolves the three committed input files inside `harness/data/`, so a run reads nothing from `idf_probe/`. `repository_tree_campaign()` keeps the repository's own directory | the preflight against the copy now names **21** missing artifact entries (16 distinct files), the three input files among them, and still exits 3 |
| 3 | **The Phase A arms carry no output-time-loop switch at all** | `Arm.output_loop` is `None` for `AR A0 A0p A1`; the regenerated row reads `n/a` for those four and `upstream upstream none none` for the optimisation phase | the matrix check; and the capability check confirms the pending set is **exactly** `B1`/`B3` on the two pulsed configurations and `B3` on `st_regression` — five pairs. **`A1` runs before driver change DR2**; only `B1` and `B3` wait on it |
| 4 | **`B0 → B1` is ruled**: the matrix stands, the plan's *isolates* wording is completed to name the Phase-B-only output-time loop and why it sits on that rung | `RUNGS` carries the completed wording and the rationale in place of the "flagged for the plan's next amendment" note; the runner no longer prints a flag | the rung check, 6 of 6 steps, unchanged |
| 5 | **`--tree repository` is preflight and self-check only** | `Campaign.is_experiment_copy`; the runner's campaign section refuses with *"the tree is not the experiment's copy; records are only ever made against `…_v4/PROCESS`"*; the README says so where it explains `--tree` | a fifteenth tooth: the checking campaign must not report itself as the production one |

---

---

## 5. Autonomous decisions, with their reversal paths

*Caption: one row per choice this task made without asking. "Reversal" is what it would cost to
undo, so that none of them is load-bearing by accident.*

| # | decision | why | reversal |
|---|---|---|---|
| 1 | **An arm declaring a switch no tree implements is refused, not composed without it.** `env_for(..., pending_ok=True)` returns the partial environment for *inspection* only; the run path never passes it | composing without the switch would run a different arm under this arm's name — the failure the capability probe exists to prevent. The flag is keyword-only and greppable, so it cannot happen by accident | delete the flag and the refusal; three lines in `arms.py` |
| 2 | **`PROCESS_ARCH_OUTER=trust` is supplied by the registry when the partitioned loop is selected, rather than being an arm field** | the brief and D23: the partitioned arms run the schedule once, so it is a consequence of the loop, not a choice. The plan's matrix row is regenerated from it, so the plan's table is unchanged | make it an `Arm` field and add a column to `PLAN_MATRIX`; about ten lines |
| 3 | **The per-run deferral artifact is chosen from the input file the arm reads**, not from which phase it belongs to | V3 chose `postsolve_nolift_*` in the evaluation phase and `postsolve_*` in the optimisation phase — the same decision written twice. Both spellings are reproduced exactly by the one rule, verified against V3's own code | restore the phase test in `Config.per_run_artifact`; two lines |
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

The pending set is **exactly five arm/configuration pairs** — `B1` and `B3` on the two pulsed
configurations, `B3` on `st_regression` — and the self-check prints them by name on every run.
**`A1` is not among them**: an evaluation-phase arm carries no output-time-loop switch at all
(§4.3, ruling 3), so the partitioned evaluation arm runs today.

This is the designed behaviour — "refuse, never degrade" — and it is the first thing that will
change when DR2 lands. It also means the composition equality with V3 currently holds **exactly**
for `B1` and `B3`: once DR2 lands they will differ from V3 by that one switch, by design. The
self-check states the pending switches per arm on every run, so that difference cannot arrive
unnoticed.

---

## 6. Two disagreements inside the experiment plan — found here, ruled, and closed

Both were found by transcribing the plan's §3.2 into data and computing what the arms actually
differ in. Both were ruled by the orchestrator on 2026-09-10 and the plan is amended; neither is
open.

**(i) The `B0 → B1` rung moves two fields, not one** — burn-time ownership *and* the output-time
loop — while the rung table's *isolates* column named only ownership. **Ruled: the matrix stands
and the wording is completed.** The placement is deliberate: `B0 → B1` is the rung already
declared to differ in kind between the phases, so putting the output-time loop's change there
leaves the headline rung `B1 → B3` with a switch set identical to its evaluation-phase twin
`A0p → A1`, which is what licenses reading one against the other. The plan's row now says so, and
`RUNGS` carries the same reason instead of a flag. The output-time loop's sweeps are counted per
run and published as their own column, so neither rung's attribution carries them silently.

**(ii) `A1`'s output-time-loop cell.** The matrix gave `A1` `upstream`; §3.3's keep-list omitted
it. **Ruled: the evaluation-phase arms carry no switch for the output-time loop at all** — an
evaluation never reaches the output path — so the matrix row reads `n/a` for all four of them and
the keep-list is `BR` and `B0`. One consequence is worth stating: **`A1` is runnable before driver
change DR2 lands**, and only `B1` and `B3` wait on it. The capability check confirms the pending
set is exactly those five arm/configuration pairs.

---

## 7. What a later task must fill in

*Caption: one row per piece the harness plan's §4.1 lists that this task did not build, and what
it must satisfy. "Owner" is the plan's task letter; the queue mints the task label when its
predecessor merges.*

| owner | piece | what it must satisfy that this task already assumes |
|---|---|---|
| H0 / **A46 (process-copy)**, **merged 2026-09-10** | `…_v4/PROCESS/process/` with its three re-pointed path constants, `PROCESS_diff.py`, the `.gitignore` for `runs/` | `Campaign.tree` defaults to exactly `…_v4/PROCESS`, which the merged copy provides |
| H0 remainder / **A48 (harness-data)**, queued behind this task | `…_v4/harness/data/` and `harness/ystate.py` | `Campaign.data_dir` **and `Campaign.input_dir`** both default to `…_v4/harness/data`, so the three committed input files are copied there too and a run reads nothing from `idf_probe/`. The **16 files** and their V4 names are §4.2's table, which A48's queue row defers to this task; the preflight names all **21** artifact entries it resolves by exactly those names |
| H2 | the reproduction reference extracted from V3's records | `switches.PREVIOUS_ARM_NAMES` maps V3's `R` to `BR` and `switches.RETIRED_ARM_NAMES` names `A1u` and `B2`; a lookup that misses must raise |
| H3 | the run path: the child process, the two entry points, the worker pool, the record schema, the perturbation stream and the predicate layer | must call `switches.assert_capable` before starting any run, must set `PYTHONPATH` to `Campaign.tree` and assert the exact tree inside the child, and must record the arm's environment **as the driver resolved it**. Run directories should be named `seed001`, not `start001` (§4.1 item 9) |
| H4 | the artifact, input-file, census and per-run-set stages | the preflight's artifact check here is existence plus the declared component count; the full validation — format, the components checksum rebuilt, the expected objective, the constraint set, the predicate mode — is that task's |
| H5 | every verification gate, reimplemented inside `harness/` | `selfcheck.py`'s `Check` record is a working shape but is **not** the plan's `Gate`/`Tooth` pair; H5 should promote it, keeping the rule that a gate with no tooth cannot be registered |
| H6 / H7 | the tally, the independent analysis and `--verify` | every population must derive from `Campaign.population`; `Campaign.without_configuration` exists so that removing a configuration re-derives every count rather than patching one |
| DR1 | the switch renames | `switches.REGISTRY` already carries `intended_name` for every switch and the retired-name refusal. When the rename lands, that file is the only one that changes, and the retired names move into the switch's `retired_names` tuple |
| DR2 | the output path without the output-time loop | the `output_loop` switch already exists in the registry with `driver_name = None` and a readback of `caller.OUTPUT_LOOP_NAME`; supplying the switch under that name and readback makes `B1` and `B3` runnable with no harness change. Only those two wait on it (§4.3, ruling 3) |
| DR5 | the predicate mode | same shape: `predicate_mode` is registered with `driver_name = None` and a readback of `module_solve.PREDICATE_MODE` |

---

## 8. Reproducing every number in this report

```bash
PY=/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python
cd arch_surgery/MDA_partitioning_experiment_v4

# §3, all five checks and fifteen teeth (~25 s, no PROCESS run)
$PY harness/selfcheck.py --tree repository --crosscheck-previous --json runs/selfcheck.json

# §3.4, the two preflight outcomes
$PY experiment_runner.py --tree repository   # READY, exit 0
$PY experiment_runner.py                     # NOT READY, exit 3
```

Both scripts were committed **before** the numbers above were taken — the package in `6713c07b`,
the artifact naming in `7aba492e`, the orchestrator's five rulings in `56edc585` — and the JSON
record carries the tree, the head commit, the configuration list and every check's population,
denominator and teeth. The comparison populations are identical at all three commits
(25 / 98 / 22 / 17); the provenance check went from 3 comparisons to 4 and the teeth from 13 to
15 as the later commits added them.

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
- **2026-09-10** — commit `56edc585`: the orchestrator's five pre-merge rulings applied and
  re-gated (§4.3) — "deck" removed in favour of *input file* with *committed* / *lifted* and
  "frozen" reserved; `scenario_dir` → `input_dir`, resolving the committed input files inside the
  experiment's own data directory; the evaluation-phase arms carrying no output-time-loop switch
  (`n/a`, and `A1` no longer waiting on driver change DR2); the `B0 → B1` rung's completed wording
  and rationale in place of the flag; and `--tree repository` refused for every campaign stage.
  Five checks PASS at 25 / 98 / 22 / 4 / 17 compared, 0 mismatched, **fifteen teeth tripped**;
  preflight READY (exit 0) against the repository tree and NOT READY (exit 3) against the copy.
  Trunk was **not** merged into this branch: the amended plan strings were read from the main
  checkout and transcribed.

---

## 10. Orchestrator's critical assessment (protocol §5) — 2026-09-10

*Appended by the orchestrating session before merge, against the report at `8cbd7e78` and the
package on the same branch. Load-bearing claims re-run, not taken from the report; the five
pre-merge rulings of §4.3 were mine, made at the first-round assessment of `2e078e94`.*

**Verified independently.** (1) `harness/selfcheck.py --tree repository --crosscheck-previous`
re-run into a fresh JSON record: five checks PASS, 25 / 98 / 22 / 4 / 17 compared, 0 mismatched,
15 teeth, 15 tripped — run twice on this branch, before and after the rulings (14 → 15 teeth).
(2) Both preflights: the default target (the copy, absent on this branch) NOT READY, exit 3, 21
missing artifact entries named, no fallback; `--tree repository` READY, exit 0, with the campaign
section refusing that tree as not the experiment's copy. (3) The regenerated matrix prints
`input file ⁺ | committed … lifted` and `output-time loop | n/a n/a n/a n/a upstream upstream none
none`, the exact strings of the amended plan §3.2 (trunk `6f3c8e3a`); the `B0 → B1` rung prints
the completed wording. (4) Scope: `f2dc9243..8cbd7e78` is nine files, all under `…_v4/` plus this
report; nothing under `process/`, `idf_probe/`, `fixedpoint/`, `…_v2/` or `…_v3/`. (5)
Vocabulary: no "deck" or "scenario" remains outside heritage mentions, the README's "replaces"
column and V3's own identifier inside the subprocess cross-check; one comment still reads "frozen
input file" (`config.py:64`) and is corrected at the merge by the orchestrator, one word. (6)
Names: no task or version token in any file, class or function.

**Endorsed.** One composition (`Arm.terms()`) instead of V3's two drifting chains, with the
previous revision's composition reproduced switch for switch on all 17 shared pairs and then
cross-checked against V3's own code in a subprocess. Capability measured by importing the driver
in a child and reading back what it resolved, with refuse-never-degrade for a switch no tree
implements — the concrete consequence, that `B1` and `B3` cannot run until DR2 lands, stated
rather than hidden. `Campaign.is_experiment_copy` closes the one route by which a V4 record could
have been made against the repository-root tree. The exact-tree assertion is equality and never
reads `__version__`. The run budget (275 + 418 + 275) is derived from the configuration list and
reproduces §3.10, which checks both.

**Limits I hold it to.** (a) The capability probe has not yet run against the copy: on this branch
the copy is absent, and on trunk the per-run deferral artifacts are absent until A48
(harness-data) lands — the copied driver checks that path at import (`caller.py:481`), so the
probe against the copy will refuse `A1` until then. The first PASS of the self-check against the
production target is A48's to show; the pre-A48 state is recorded at the merge. (b) The cross-check
against V3 executes code from the frozen `…_v3/` directory in a subprocess; it is opt-in and not a
gate, and stays acceptable only on that footing — the harness's gates import nothing from outside
`harness/`. (c) `selfcheck.Check` is not yet the plan's `Gate`/`Tooth` pair; H5 promotes it.
(d) The two artifact naming schemes mark opposite members of the per-run pair (§4.2), a deliberate
consequence of making the committed input file the unmarked default; A48 maps by role, which
`config.artifact_file_names()` gives it. (e) Both `--crosscheck-previous` and `--tree repository`
read the repository's `docs/data/`; once A48 lands the production self-check reads `harness/data/`,
and the two must agree by sha256 — A48's gate.

**Consequences drawn (orchestrator, today).** A48 (harness-data) is dispatched off the merged tip
with §4.2's sixteen files under the names fixed here, `harness/ystate.py`, and the two one-line
copy edits; A49 (harness-reference) is minted for H2 and dispatched in parallel —
`switches.PREVIOUS_ARM_NAMES` and `RETIRED_ARM_NAMES` are the map it uses. Run directories are
named `seed001` (harness plan §11.2 makes "seed" the word in both phases; ruled here and recorded
in the harness plan for the run-path task).

**Verdict.** Fit to merge; nothing returned. The skeleton is what the plan asked for —
configurations as a list, the matrix as data, capability measured, refusals as records — and its
own checks have been shown able to fail.
