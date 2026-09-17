# The harness

This package decides **what to run** and **whether the tree can run it**. It is written to be
read by someone who has not followed the project, so everything it assumes is spelled out below.

---

## 0. The harness in plain language — an overview, layer by layer

*Written 2026-09-14 at the user's request, from the orchestrator's chat explanation. Paths are
relative to `MDA_partitioning_experiment_v4/`. The sections after this one go deeper; this one is
the map.*

**What it is for.** The experiment asks one question: does rearranging how PROCESS's models are
solved, without changing any model, reduce the number of model evaluations needed to reach the same
answer at the same accuracy? The harness exists to make that measurement honest. It composes each
experimental arm, runs PROCESS in isolation, records what each run cost and how accurately it
stopped, checks itself with gates, and renders the results into the plan. Nothing that reaches the
plan is typed by hand.

**The one button.** `experiment_runner.py` is the only entry point. Every flag selects a stage:
`--gate` runs one or all gates, `--measure` runs the tally and analysis stages, `--plan-tables`
renders the report's results appendix and its companion file, `--selfcheck` runs the harness's own tests, `--smoke` runs the
campaign's chain at one seed, `--run` runs one PROCESS job by hand. Failure paths are reachable from
the same button, so a refused start or a failed gate is a result rather than a crash.

**The copy of PROCESS.** The harness never runs the repository-root PROCESS. It runs a copy under
`PROCESS/`, whose driver files carry the architecture changes as environment-switched branches.
`PROCESS/copy_gates.py` proves the copy differs from the frozen base only in the permitted driver
files. With every switch unset the copy behaves byte-identically to upstream, and gate G1 measures
that.

### Layer 1 — the foundation: `harness/core/`

- `core/config.py` holds every declared setting as frozen data: configurations, seeds, tolerance,
  delta, and the `EXECUTION_APPROVED` flag that keeps the campaign from running until the user says
  so.
- `core/framework.py` defines what a gate, a tooth, a check and a measurement are. A gate checks
  something about the tree or the records. A tooth is a deliberate fault the gate must catch, so
  every gate is shown able to fail. A measurement stage declares which records it reads and stamps
  them, so a consumer can refuse a stage record the records have outrun.
- `core/records.py` is the schema of a run record and its completeness contract. A record missing a
  declared field is refused, never summarised over.
- `core/pool.py` is the only place a PROCESS run starts. Each job gets a fresh subprocess and its own
  directory. With `--resume`, a record whose job matches and whose schema is complete is kept rather
  than re-run.
- `core/provenance.py` stamps the interpreter, tree and commit on every record, and refuses to run if
  the imported PROCESS is not this tree.
- `core/failure.py` classifies every exception into one taxonomy row, so dropped runs are counted by
  cause.

### Layer 2 — what the experiment is: `harness/experiment/`

- `experiment/arms.py` is the switch matrix as data. Each arm — `BR`, `B0`, `B1`, `B2` and the Phase A
  arms — is a row of switch values, and the environment for a run is composed from that row. Nothing
  composes an arm by hand.
- `experiment/switches.py` is the vocabulary the driver copy reads, and a probe that checks the copy
  actually implements each switch.
- `experiment/input_files.py` provides the committed input file per configuration, and the lifted
  variant where the burn time is moved to the optimiser.
- `experiment/artifacts.py` and `experiment/data_provenance.py` resolve and check every committed
  artifact a run reads, with digests.

### Layer 3 — inside a run: `harness/child/`

These modules run inside the measurement subprocess, and they are the set nobody may edit while a
run executes (harness plan amendment 13, rule (vi)).

- `child/optimise.py` is the optimisation-phase entry point: one full PROCESS optimisation.
  `child/evaluate.py` is the evaluation-phase entry point: one pass through the models with no
  optimiser. `child/census.py` records which model writes which variable.
- `child/child.py` is the shared machinery: it reads the counters the driver copy keeps, reads the
  acceptance values from the written file, and takes the **exit audit** — the one further sweep after
  the accepted point that measures how far the state would still move. Under ruling D25 it first puts
  the whole data structure back to the solve-phase state via `child/data_structure.py`, so the sweep
  evaluates the map the loop iterated rather than the one the write pass left behind.
- `child/ystate.py` and `child/predicate.py` define the **coupling state**: the set of variables that
  flow between models, their scales, and the convergence test at tolerance τ. The driver copy loads
  `child/ystate.py` by a literal path (a permitted edit of the copy, asserted by `PROCESS/copy_gates.py`),
  so the driver and the harness's exit audit use one predicate.
- `child/perturb.py` is the seeded displacement stream. Every arm at a given seed starts from the same
  bytes, which is what makes cost differences paired.
- `child/postsolve.py` derives which model nodes the optimiser never reads, so they can be deferred to
  once per run.

### Layer 4 — what the records mean: `harness/measurement/`

- `measurement/tally_evaluation.py` and `measurement/tally_optimisation.py` read the run records and
  build the published tables: cost per arm, cost ratios against the control, achieved accuracy per
  arm, the output loop's sweeps as their own column, and the failure taxonomy. `measurement/tally.py`
  declares which record directories each table is over.
- `measurement/stats.py` holds every statistical construction once, with its declaration in the plan.
  `measurement/tables.py` refuses to emit a table without a caption, denominator, audit position and
  instrument version.
- `measurement/analysis.py` is a **deliberate second implementation** of every published cell,
  sharing no helper with the tally. Gate `recomputation` compares the two. Agreement means the tables
  are not an artefact of one piece of code.
- `measurement/plan_tables.py` renders the report's tables from the stage records. **One
  construction, one table** (`LAYOUTS`, a declaration per construction): the tally emits a table per
  *(configuration, source)*, and the renderer combines them into one grid — `stack` puts the
  configurations and regimes in row groups under a bold sub-heading row that names the group's
  configuration, its regime where the table holds more than one, and its own n, and **nothing
  more**: the tally's table name is on the construction line under the grid and what the n counts
  is in the caption, said once for the grid rather than once per group (task A87
  (v3-grid-polish)); `merge` aligns several constructions of one configuration on a join column, so a fact stated
  once per configuration (the seed set, the entry reference) is a column of the table it qualifies
  rather than a table of its own; `single` passes through a construction the tally already emits
  whole. **The previous revision's cell formats** are the layouts' too (task A85
  (v3-table-formats), the user's ruling of 2026-09-15 that the report's tables are the V3 report's
  §4 and §5 tables): `merges` puts a mean and its seed bracket in one cell (`1978 [1758, 2280]`,
  and a bare value where every run agreed) and a median and its p90 in one; `select` takes a
  declared, disjoint set of a stage table's rows, so a construction the previous revision published
  as several tables of one quantity each — the optimiser's path — renders as several tables and
  not as one stacked grid; `blocks` prints one grid per configuration under a bold heading line
  (``**`nof`** (n = 22)``), which is the per-module form, its heading line reduced to the previous
  revision's own (a `Table.block_denominator` declares the per-arm count where the table's own
  denominator is over every arm, and the arm set is named only where the block does not carry the
  phase's whole ladder); `bold` marks the result column and the verdict; `blank_repeats` blanks a
  repeated key on continuation rows; `omit` drops a column whose cell is the same label on every
  row the grid keeps and states it in the caption instead, as the previous revision's grids did
  (task A86 (v3-tables-remainder)); a `fraction` merge puts a count and its denominator in one
  cell (`0/22`); and a `verdict` merge puts a ratio at two quantiles and the verdict read against
  it in one cell (`0.76, 5.64 → **PASS**`, emboldening the verdict and no more), with `—` where
  the pair does not exist (task A87 (v3-grid-polish)). `column_order` declares the order a
  combined grid's columns print in, so a column set is not left in the order the first
  configuration to exhibit it happened to give it. Two layouts may **share** their stage tables by
  naming each other in `shares_tables_with`, and a cell then appears in two tables — per-arm
  success is the main text's grid in the previous revision's §5.1 form and a constituent of the
  appendix's merged reliability table; the second names the first's companion full version in
  `per_seed_columns_in` rather than rendering a copy of it. **A cell may appear in more than one
  table; it may never be lost or changed.** A `merge` may also print **blocks** — one merged
  grid per configuration under the block heading line — which is how the two
  **function-weighted twins** of the per-module sweep tables are made (task A88
  (function-weighted-sweeps), the user's instruction of 2026-09-17): the sweep table is shared
  with a construction that carries only the new cells (`functions` per group and a total row of
  Σ sweeps × functions), the two aligned on the module column; in a merge the constituents are
  taken in the layout's `kinds` order and the first cell wins, **except that an empty cell never
  claims a column** — empty is a column the row does not have, `—` a value that is missing — so
  the new construction's module rows leave every sweep cell to the table they are republished
  from. Every one of them is a
  rendering of cells a stage record already carries, and
  `report_cells_preserved.py` puts each old row through the same declarations — the omission
  included, counted and named in its output — before looking for it, so a merge that dropped or
  swapped a part would not reproduce the cell; the one heading this rendering has reused for a
  different statistic is declared in that script's `RENAMED_HEADINGS` and printed with every run.
  Twelve **headline tables** are rendered into the report's §4 itself, between
  `MAIN_START` / `MAIN_END` marker pairs carrying the layout's name and numbered `Table n` after
  §3's six; everything else is **Appendix D — Results tables** (`Table D.n`, one short caption
  each, the constructions declared once in D.0) and the companion file `RESULTS_TABLES_FULL.md`
  (every per-run, per-seed and per-pair table, and the full version of a report table whose
  per-seed columns it omits, `Table F.n`). The second implementation's tables are **not rendered
  anywhere**: gate `recomputation`'s row of Table D.1 is that check. Check mode diffs every block
  and both committed documents without writing, and resolves every `Table n` / `Table D.n` /
  `Table F.n` reference in the hand-written text — the change log's lines held out, since its
  entries state the table set of their own day (trap T17). §4 is hand-written conclusions beside those
  tables (task A79 (report-captions); the layouts and the main-text tables task A83
  (headline-tables-in-text), 2026-09-15).

### Layer 5 — the gates: `harness/gates/`

`gates/registry.py` holds the registry, the ordering by declared dependency, the gate table and the
printers; it implements no criterion. `gates/gates.py` holds the gates that need no module of their
own — G0′ and the copy's two sibling gates (`copy_identity`, `edit_behaviour`), all three loading
their one implementation from `PROCESS/copy_gates.py` by path — plus the shared entry references
every warm gate is anchored on (one job, `reproduction.entry_reference_job`, so one record in the
pool), gate GR's wrapper, the promoted self-checks and the `self_containment` gate (the package
scanned for any import of, or subprocess into, the two superseded directories; one tooth — a
scratch module importing one must be counted). `gates/gate_resume_identity.py` holds the gate over
the job identity itself: every `pool.Job` field classified, one by-design pair per class of
deliberate second run composed from the gate modules' own constructors and required to differ (or,
for the shared reference, to agree); five teeth. The important ones:

- **G1 switch neutrality** (`gates/gate_neutrality.py`, with the exclusion tables and the
  record/output-file comparison machinery G8, G9 and `exclusion_review` import) — with every switch
  unset, the copy's output is byte-identical to the frozen base, on values and on every output-file
  line.
- **G0′ copy integrity** — the copy differs from the base only in permitted files.
- **G9 output path** (`gates/gate_output_path.py`, which also holds the restricted statistic's
  excluded set G2/G3 and G4 import) — `B1` and `B2` write once with zero loop sweeps; `BR` and `B0`
  keep the loop. The output-loop sweep count is the tally's `output_loop_sweeps` column.
- **G8 predicate mode** (`gates/gate_predicate_mode.py`) — the two convergence rulers, one
  implementation.
- **`run_kind_separation`** — every published cell is over campaign records only, with gate and smoke
  records excluded by kind.
- **`recomputation`** — tally and analysis agree.

The dedicated modules: `gates/gate_entry.py` proves all Phase A arms start from the same bytes.
`gates/gate_audit.py` proves the audit's restricted statistic excludes exactly the deferred nodes.
`gates/gate_composition.py` proves an arm composed from the matrix equals one composed switch by
switch. `gates/gate_records.py` proves a record carries what it declares even when the run fails.
`gates/gate_tally.py` proves the tables land on their declared cells.

`gates/reproduction.py` with `gates/reference.py` is gate **GR**: did rewriting the harness change the
measurement? It re-runs twenty jobs from the previous revision and compares the reference values bit
for bit, naming each excluded value and why.

`gates/selfcheck.py` tests the harness itself with synthesised fixtures and no PROCESS run.

### The chain

`chain.py` is the sequence the campaign runs: entry references per configuration, displaced-entry
evaluations of every Phase A arm, the stencil evaluations, the optimisations of every Phase B arm,
then the tally, the analysis, the recomputation gate and the render. The **smoke** runs the same
chain at one seed on one configuration, writing smoke-kind records. The **campaign** runs it at every
seed on every configuration, writing campaign-kind records, and only when `EXECUTION_APPROVED` is
true.

### How a number reaches the plan

A run record is written by `child/`, stamped by `core/`, kept or re-made by the pool. The tally reads
a declared set of records and writes a stage record naming them. The analysis recomputes the same
cells independently. The recomputation gate compares. The gate table stage collects every verdict.
The renderer writes §4's three headline tables, Appendix D and the companion file from those stage
records and refuses if any record it reads has been outrun. Every table declares its units, row,
column, population and construction (printed once per construction in D.0) and carries a caption of
a few lines; a **combined** table's denominator is the number of row groups, and each group's
sub-heading row states its own n — there is no pooled one. Every cell is traced by the construction
names printed under its grid, never by its number. That chain is what lets the report's tables be read without trusting anyone's memory.

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

All six steps are built: step 6 is the tally (§13), the analysis (§14) and gate `recomputation`
between them.

---

## 3. The vocabulary

One row per word this project uses in a particular way. Where a word is *not* used, the word it
replaces is named so that older documents can still be read. **This table is the one vocabulary**:
the harness plan's §0 and §11.2 point here and keep only the rows that carry a ruling's words.

*Caption: the harness's terms. "Means" is the definition in force; "replaces" names the older
wording, kept only so that documents written before the rename remain readable. Rows marked
**changed** differ from the terminology table in the harness plan's §11.2; §7 says why.*

| term | means | replaces |
|---|---|---|
| **PROCESS** | the fusion power-plant systems code this repository forks: an optimiser (VMCON) wrapped around a loop that runs the models until their outputs stop changing. The experiment runs its own copy, `../PROCESS/` | — |
| **model** | one physics or engineering calculation. Frozen; the experiment never changes one | — |
| **driver** | the arrangement of loops and solvers around the models. The only thing the experiment changes | — |
| **node** | one place a model is called from inside the loop. One **node call** is one execution of one node, and node calls are the unit of cost | — |
| **sweep** | one pass over a sequence of nodes — the whole loop, or one block's share of it | — |
| **MDA** | multidisciplinary analysis: the loop that drives the models to a consistent coupling state at a fixed design vector. `PROCESS_ARCH_MDA = flat | partitioned` names its shape | — |
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
| **exit audit** | one further full sweep of the whole model set, taken past termination from the state the solve handed over, on the identical instrument in every arm. Its own model calls are never charged to the arm. Its residual is what "achieved accuracy" means here | — |
| **snapshot position** | where the exit audit's state is taken from. The driver snapshots at two: the entry to the output path — the state the solve handed over, which is the position the plan declares — and immediately before the files are written | — |
| **restored set** | the data-structure fields the audit puts back before it sweeps, so that the sweep evaluates the map the loop iterated and not the one PROCESS's output path left behind. **Derived** — what differs between the snapshot and the state the sweep would otherwise start from — never a list | — |
| **instrument version** | which mechanism produced a residual, stamped in every record. Two residuals made by different instruments are two measurements, not a difference; a gate comparing across an instrument change excludes the residual by name and a gate comparing two records of one instrument does not | — · **added** |
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
| **job identity** | every field the pool composes into a run, rendered once and digested; what `--resume` calls "the same job" and what names a directory of the shared pool. A switch term no tree implements is refused at composition; the allowance that once let a run omit one was retired (A72) | — · **added** |
| **tally** | the summary computed from the records: the experiment plan's §4 tables, each with its caption and its denominator. It has nothing to pass, so it is a measurement stage and not a gate | — |
| **construction** | one declared way of computing a published number — which median, which population, what counts as an accepted optimum. Each is one function in `harness/measurement/stats.py` and **its docstring is the declaration** a caption quotes | — · **added** |
| **source** | a named subtree of `runs/gates/` whose records are a comparable set, with the sentence saying why. The tally reads a source, never "the gate runs": several gates run the same arm at the same seed from different entries and three run it doctored | — · **added** |
| **caption** | the five things a table cannot be emitted without — units, what a row is, what a column is, the population, the construction — plus the clauses the plan requires in that particular caption | — |
| **denominator** | the count of things actually compared, stated beside every count. A table built with a letter where a count belongs is refused | — |
| **analysis** | the same summary computed independently, and compared with the tally cell by cell | — |
| **teeth** | a check's demonstrated ability to fail: a deliberate break that it must catch before its zeros are believed | — |
| **`ifail`** | VMCON's exit code, stamped in every optimisation record; `1` is converged | — |
| **switch neutrality** | with every `PROCESS_ARCH_*` variable unset the copy's behaviour is byte-identical to the frozen base, on record values and on every output-file line. Gate G1, run per driver change | — |

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
| how many **functions** — the dependency analysis's callable submodels — sit behind each block's DSM rows, per configuration; read by the measurement layer only | `dsm_function_counts.json` | `dsm_function_counts.json` |

The old spellings carry the number of the task that first produced the file, which the naming
rule for this revision forbids, and they use words the vocabulary has since replaced. Both
spellings resolve: `default_campaign()` uses the first column, and the second is what
`data_provenance` names as each copied file's source, so neither name is written twice.

**Those files are copies, and `data/PROVENANCE.json` says whose.** Seventeen files sit in `data/` —
the six kinds above for three configurations, the three committed input files, and the function
counts. Each was
copied out of the repository at a recorded commit, read from the commit itself rather than from
anyone's working tree, and each is byte-identical to what it was copied from. The function counts
entered after the one copy of 2026-09-14 and carry their **own** source commit on their entry
(`data_provenance.py add <name> --source-commit <commit>`, which enters one file and re-blesses
nothing; the check reads each file at its own commit). The record names,
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

`harness/child/ystate.py` — the code that decides what "converged" means — was moved here from the
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

**`schedule passes` no longer exists as a setting.** The partitioned arms work through their
three blocks once. The driver used to express "do not repeat the schedule" as a separate setting
the registry supplied whenever the partitioned loop was selected; since DR1 (A56
(driver-renames)) `partitioned` means one pass on its own, the setting is gone from the driver and
its old name (`PROCESS_ARCH_OUTER`) is on the retired list — set, it raises. §7.2 records why.

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

**There is no flag to run the experiment against another tree.** The only tree a record is ever
made against is the experiment's own copy of PROCESS in `../PROCESS/`; `pool.run` and every
campaign stage refuse a campaign pointed anywhere else, and the self-check proves both refusals on
a campaign it constructs at the repository root for the purpose. (The `--tree repository` flag that
once pointed the preflight at the repository's own tree was retired when that tree stopped
implementing the renamed switches — its capability check failed 19 of 55 by construction.)

```bash
PY=/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python
cd arch_surgery/MDA_partitioning_experiment_v4

# the button: preflight, the matrix, the rungs, what the tree can do
$PY experiment_runner.py

# the harness's own gates, with their teeth
$PY experiment_runner.py --selfcheck
$PY harness/gates/selfcheck.py --json runs/selfcheck.json

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
$PY experiment_runner.py --measure gate_table       # the report's gate table (Appendix D.1)
$PY experiment_runner.py --measure tally_evaluation # the evaluation phase's tables (D.2-D.3, companion F.1)
$PY experiment_runner.py --measure tally_optimisation  # the optimisation phase's tables (D.2, D.4, companion F.2)
$PY experiment_runner.py --measure all

# the tally's own gate: the cells it must land on, and what a table may not be
$PY experiment_runner.py --gate tally_contracts

# the analysis: the same cells recomputed by a second implementation, compared
$PY experiment_runner.py --gate recomputation --resume   # the verdict, with six teeth
$PY experiment_runner.py --measure recomputed_tables     # its own tables, beside the tally's
$PY -m harness.measurement.analysis --teeth                          # the six deliberate breaks alone

# THE CHAIN, once, on one seed and the cheapest configuration: both phases,
# every arm, then the tally, the analysis and its --verify.  Records stamped
# 'smoke'; no approval needed and no campaign record made
$PY experiment_runner.py --smoke --resume --census-entry evaluation

# the report's three headline tables (in §4, between the renderer's markers),
# its Appendix D and the companion RESULTS_TABLES_FULL.md, rendered from the
# measurement stages' records.  'check' compares all of them with what is
# committed, resolves every Table n / D.n / F.n reference in the hand-written
# text and writes nothing (exit 3 on a difference or a dangling reference);
# press --measure gate_table after any gate re-run, or the renderer refuses
# rather than reproducing the older verdict.  'show' also prints the census:
# how many stage tables each rendered table combines, and its shape
$PY experiment_runner.py --plan-tables show
$PY experiment_runner.py --plan-tables check
$PY experiment_runner.py --plan-tables write
```

**Every gate's runs are jobs in one shared pool, and `--resume` is what decides whether a job is
re-made.** A job's **identity** is every field the pool composes into the run — arm, configuration,
seed, phase, regime, run kind, δ, the pin, the entry state, the stencil point, the ruler, the
overrides, the audit position and its caller — listed once in `pool.JOB_IDENTITY_FIELDS`, rendered
as one dictionary, digested (`records.job_digest`) and stamped into the record as `job_identity` and
`job_digest`. One directory per distinct identity, `runs/gates/_runs/<phase>_<arm>_<configuration>_
seed<NNN>_<kind>_<digest>`; a gate declares the **jobs it reads** (`Gate.jobs`) and the pool resolves
them, so two gates composing the same job share one record and a gate that runs the same arm a second
way on purpose — a hand-composed environment, a doctored entry state, another audit position —
differs in an identity field and has its own directory by construction (gate `resume_identity`
checks one pair per class). `experiment_runner.py --jobs <gate|all>` lists a gate's job set with the
resume decision per job, without running anything.

Without `--resume` every job is made again — once per press, whichever gates share it — so a verdict
is never computed over records made before the change it is checking; with it, a directory holding a
*complete record of exactly this job* is kept, which is not a retry: `records.is_complete_for`
compares the readable six fields, every identity field the child also stamps, the stamped identity
field by field and the digest (which must re-derive from the stamped identity) before anything is
kept. A record made before the identity existed has no digest and is incomplete, so a change to what
the identity covers re-makes every run (harness plan amendment 17's property, by construction).
Every verdict says which commit the records it read were made at, and lists the jobs: records from
another commit are expected under `--resume`, stated either way, and a **failure** without it.

One exception, stated where it happens. Gate G1, switch neutrality, compares the copy *before* a
driver change with the copy *after* it, so its two sides are **one identity at two commits**: the
pool's one-directory-per-identity would put the second on top of the first, so its two captures keep
their own directories (`runs/gates/switch_neutrality/{before,after}/`), it cannot make its own
"before", and **never re-makes one that is there**. Move a "before" capture between trees by copying
the directory, never by re-running the stage — it was written by an earlier record schema, and
resume judges it against the current one.

```bash
$PY experiment_runner.py --gate switch_neutrality --capture before  # in a tree at the commit before
$PY experiment_runner.py --gate switch_neutrality --capture after   # in the tree at the commit after
$PY experiment_runner.py --gate switch_neutrality                   # compare, with teeth
```

**The order `--gate all` runs in is derived, not written down.** `GATE_ORDER` is a preference —
the repository-state checks before the hour of runs, so a failure is reported in seconds — and a
gate's `reads_from` declares which other gates' runs or verdicts it reads. Where the two conflict
the dependency wins: G9 compares its reference arms against gate GR's own records, so it follows
GR however much GR costs. A dependency on a gate the registry does not hold, or a cycle, raises.

`--outdir` sends a gate's verdict somewhere other than the campaign's records
directory; the shared pool stays where it is, because one gate reads
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
from harness import ARMS, default_campaign, env_for, input_file_for, rung

campaign = default_campaign()
nof = campaign.configuration("large_tokamak_nof")

rung("B0", "B2")                       # what separates the two arms, field by field
input_file_for("B2", nof, campaign=campaign)  # which input file B2 reads
env_for("A2", nof, seed=0, pin_hex=float(3600.0).hex(), campaign=campaign)
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

**A gate that makes runs.** Compose its jobs in one function of the campaign (`jobs_read`),
reading any prerequisite — the entry references, a baseline record — from disk through the pool
(`gates.entry_references_from_records`, `pool.directory_for`), and declare that function as the
gate's `jobs` (`gates.job_rows`); the body calls the same function and hands the jobs to
`pool.run_all`. Name no directory: a job's directory is the pool's, from its identity. A second run
the gate makes *on purpose* must differ from the first in an identity field — `override_env`, the
entry state's path, the audit position — or the pool hands it the first run's record; add the pair
to `gate_resume_identity.by_design_pairs` so the distinctness is checked, not assumed. **A field
added to `pool.Job`** must be put in `JOB_IDENTITY_FIELDS` or `JOB_NON_IDENTITY_FIELDS`, with the
reason; the module refuses to import otherwise, and a change to the identity re-makes every record
under `--resume`, which is the contract working.

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
   job identity (which replaced *pending switch* when the allowance was retired, A72). Each is a
   thing the harness has to name in a refusal message.
7. **The plan's matrix row "outer loop" is regenerated, not stored.** Four of the plan's eleven
   matrix rows — the stopping rule, the outer loop, whether the burn time is out of the loop, and
   which input file is read — follow from the other rows. They are computed, and the whole table is
   regenerated and compared against the plan's, cell for cell, so the plan's table still prints
   exactly as written while an arm has one field per *choice* rather than one per row.
8. **Two places where the plan disagreed with itself were found here and have since been ruled**
   (2026-09-10). See §8; the rulings are in the plan, and the code carries the reasons rather
   than a flag.
9. **Run directories are named for the seed.** §11.2 makes "seed" the word in both phases; the
   run path writes `seed001` (ruled at A47's assessment, approved under D24). The previous
   revision's `start001` survives only in the committed reference's `source_path` entries.

---

## 8. What the gates prove, and what "teeth" are

A **gate** is a check that must pass before a number is believed. A gate's **teeth** are deliberate
breaks that the check must catch: a check that has never been shown to fail is an assertion, not a
measurement. This project has published a zero over a population quietly smaller than the one it
named, and has once had a check that returned "pass" over an empty set, which is why every count
below carries the number of things actually compared.

`harness/gates/selfcheck.py` runs seven checks, each with its teeth, in about half a minute, and starts no
PROCESS run.

*Caption: one row per check. "Compares" is the population; "teeth" are the deliberate breaks it is
shown to catch.*

| check | binds | teeth |
|---|---|---|
| **composition** | every arm composes on every configuration; a skipped arm refuses by name and quotes its recorded reason; the reference arms compose to every switch cleared; the arms the previous revision also ran compose to the *same switch settings* it used | a wrong value in one arm; a switch dropped from an arm; a skipped arm asked to compose |
| **rungs** | the plan's matrix regenerates cell for cell from the arm records; the difference between two arms equals the difference the plan declares for that step; no removed arm is present | a wrong expected difference; a wrong cell in the transcribed matrix; an arm compared with itself |
| **capability** | the tree resolves every switch each arm asks for, exactly as asked; an arm asking for something no tree implements is refused before anything runs | a switch name no tree defines; a switch the environment does not carry claimed as resolved; each retired name of the registry's list present in the environment, one tooth over the list; the driver's own refusal of a retired name; a decoy `process/` package in the working directory |
| **provenance** | a modified tracked file and an untracked file are recorded separately, and only the first marks the tree dirty | each kind of change, one at a time, in a throwaway repository; and the tree asserted by a prefix instead of exactly |
| **data** | every committed file in `data/` is byte-identical to its source at the recorded commit and the file set matches exactly; `ystate.py`'s whole diff against its own source is exactly the hunks the record holds and its post-edit hash is the recorded one; the counts `config.py` declares are the ones the files carry | one byte changed; a file missing; a file the record does not name; a changed file whose recorded hash was updated to match it — which passes a record-only check and must still fail; and the same two on `ystate.py` itself |
| **run path** | a finished record carries every field it declares; a partial per-attempt decomposition is refused and its sweep total decomposes into the parts that claim it; the two displacement streams key on what they say they key on; a run against the wrong tree, or without a switch its arm declares, is refused rather than made | a declared field removed; a record that does not say what kind of run made it; per-attempt costs stamped at some attempts and not others; a sweep total that does not decompose; a run asking for a switch the tree does not implement. (One ruler and not both, and attempts that do not sum, are gate G7's teeth on a real record and are not repeated here) |
| **stage provenance** | a measurement stage that reads other records says which ones it read — path, bytes, commit, time and verdict — and a consumer refuses that stage record once those records have moved, so the plan's §4.1 can no longer reproduce a verdict the gate has since replaced; and every census record carries the commit of the tree it was taken in, or is named as one a stamp survey cannot place | a verdict re-made at a later commit after the stage record was written; a verdict written after it; a verdict it read that is gone; a stage record that does not say what it read |

Two of these deserve their reason stated.

**Why the previous revision's composition is compared.** A rewritten harness that changes the
measurement is not a rewrite; it is a new experiment. The six arms this revision shares with the
last one must compose to the same switch settings, or the difference between the two revisions'
numbers would be partly the harness. The expected settings are transcribed into `selfcheck.py`
rather than imported, because every check the experiment runs is implemented inside this package.
The transcription was measured once against the previous revision's own composition functions
(A47's `--crosscheck-previous`, retired: that revision is frozen with D20 and composes switch
names the copy has since refused, so the check could neither go stale nor still run).

**Why the predicate module is allowed to differ from its source at all, and what still refuses.**
`harness/child/ystate.py` was moved whole out of the repository's research tree, and for a while the
check on it could be the strongest one available: remove the one paragraph it had gained and the
rest was byte-identical to the source. The approved driver change that gave the convergence test a
second ruler is *in that module*, so that reconstruction no longer exists. The check was re-based
rather than dropped, on the model the copied PROCESS tree already uses: an edit is legal because it
is **recorded and reviewable**, not because it is absent. The record holds every hunk of the diff
and the post-edit hash, and each recorded edit says what it is, what it does and which task made
it. An edit nobody recorded still fails — by the hash if the hunks were left stale, and by the
hunks if the hash was updated to match — and both of those are teeth.

**Where the exit audit is taken, and who may move it.** Every optimisation run audits at the
position the plan declares — the entry to the file-writing routine, the state the solve handed
over — and says so in its record. One other position exists, `after_run`: the same one-sweep
instrument taken after the files are written, with the solve-phase settings put back but the
coupling state left as PROCESS wrote it out. Its residual is therefore *how far the written file is
from a fixed point of the solve's own map*, not how well an arm converged. Only stages named in
`records.AUDIT_POSITION_AFTER_RUN_CALLERS` may ask for it — today the reproduction gate, the
switch-neutrality gate and gate `written_file_gap` — each
with its reason beside its name; the run pool refuses any other caller and every campaign run,
and the `run path` self-check has a tooth for each refusal. The caller is stamped in the run's
`command.json` beside its record and in the caller's own verdict.

**Gate `written_file_gap`** is the one gate that exists to read that position. It runs the
reference arm and the two one-call arms (`BR`, `B1`, `B2`) at seed 0 on the pulsed
configurations, composed exactly as the campaign composes them, and publishes the written-file
gap per run with the component that carries it named. It passes or fails only on whether the runs
finished as the arms the matrix describes and audited where asked; **the size of the gap is a
finding about PROCESS's output pass, never a criterion.** Measured 2026-09-14: on both output
paths, exactly one component moves — `tfcoil.insstrain`, ~7e-3 scaled — and every other one by
exactly zero.

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
- The matrix gave the partitioned evaluation-phase arm `A2` the output-time loop, while the prose
  listing the arms that keep it left `A2` out. **Ruling: the evaluation-phase arms carry no switch
  for it at all** — an evaluation never reaches the output path — so the row reads `n/a` for all
  four of them, and the arms that keep the loop are the two optimisation-phase controls. One
  consequence matters: `A2` is runnable now, and only `B1` and `B2` wait on the driver change that
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
- **what the audit put back before it swept**: which positions were snapshotted, how many fields
  the derived restored set held and how many of those were read back equal, how many could not be
  restored **and which by name**, and how far the state the sweep actually started from was from
  the snapshot — split into the coupling state, whose restore the audit position governs, and
  everything else, which should be zero. The reason that block is in every record and not in a
  note somewhere: PROCESS's output path permanently changes model settings that are not
  coupling-state components, so a sweep taken afterwards from the coupling state alone is not the
  loop's own map. One such setting — the TF-coil stress mesh, raised 100 → 500 and never put
  back — held the largest residual in every arm on two of three configurations for two revisions,
  and was read as a convergence result until it was measured;
- **how it ended**: one of a small set of outcomes — finished, crashed, refused, did not converge,
  hit upstream's own pass cap, infeasible at the audit, or a machinery failure. Upstream's loop
  raising after ten passes is a *finding about the shipped code*, not a broken run, and has its
  own outcome so that the two are never confused again;
- **which job it is**: the pool's rendering of every field it composed into the run
  (`job_identity`) and its digest (`job_digest`), stamped after the child returns; what `--resume`
  compares, and what names the record's directory in the shared pool (§5).

The record's schema is `core/records.py`'s `SCHEMA` (101 declared fields: 90 in the optimisation
phase, 83 in the evaluation phase) and every reader goes through its contract (`assert_usable`);
this list is the plain-language version of what it carries.

**A record's arm name is the name at the time of the run.** The arms were renamed on 2026-09-15 at
the user's ruling, so that the two phases read rung for rung — `AR/A0/A1/A2` against
`BR/B0/B1/B2` — and the campaign's 949 records and every earlier gate record were **not** re-made:
they stamp the old names in `campaign_arm` and `job_identity.arm`, and their directories keep the
old names too. One table says what each old name is today — `core/records.py`'s
`RECORDED_ARM_NAMES`, the only place the old spellings are written — and it is applied in **one**
place, `records.read`, so every reader of a record sees today's names. A record made after the
renaming stamps the naming scheme (`arm_naming`, written by the pool beside `job_identity`) and is
read as written; a record without the stamp is translated, its `job_digest` re-derived over the
translated identity with the stamped digest kept in the one in-memory trace field `arm_name_translation` (as `job_digest_as_stamped`), so that
`--resume` keeps it (the pool's job computes the same digest). Nothing is written back to disk. A
record naming an arm neither the table nor the matrix knows is **refused by name** where it is
read. The pool resolves a job's directory by that digest (`pool.directory_for`) wherever a record
exists, and only otherwise by the layout, so a renamed arm finds its records under its old
directory name and never re-makes them on top of another arm's; a canonical directory occupied by
another job's record is refused, not removed. The `resume_identity` gate surveys every record
under `runs/` by how its name was read and has four teeth on this. Why a stamp and not a rule: two
of the three renamed arms took names that were another arm's before, so the bare string cannot say
which arm a record means.

---

## 10. What is here, and what is not

What exists: the declarations (`core/config.py`), the switch vocabulary and the capability probe
(`experiment/switches.py`), the arm matrix (`experiment/arms.py`), the provenance refusals
(`core/provenance.py`), the committed data in `data/`, the coupling state and its predicate
(`child/ystate.py`, `child/predicate.py`), the displacement streams (`child/perturb.py`), **the run path**
(`child/child.py`, `child/optimise.py`, `child/evaluate.py`, `core/pool.py`, `core/records.py`,
`core/failure.py`), the committed reproduction reference (`gates/reference.py`) and **gate GR**
(`gates/reproduction.py`), plus the self-check and the runner's preflight.

The **tally** is here too (§13): the declared constructions in `measurement/stats.py`, the table
module that refuses a table without a caption or a denominator, and the two stages that emit the
experiment plan's §4.2 and §4.3 tables from the records.  So is the **analysis** (§14): the second,
independent recomputation the tally's cells are verified against, in `measurement/analysis.py`.  And
so is **the chain** (§15): the sequence the campaign runs, which the one-seed smoke runs too.

### 10.1 The package layout — five subpackages, grouped by who imports them and when they run

*The grouping is by role, not by subject.  A subpackage imports the ones above it in this table and
never the ones below; the one exception is named in the `gates/` row.  Every module keeps the name
it had — this is a move, not a rename.*

| directory | what it holds | who imports it |
|---|---|---|
| `core/` | `framework` (what a gate, a tooth, a check and a measurement *are*), `config` (every declared setting), `failure` (the taxonomy), `provenance` (interpreter, tree and git stamps), `records` (the run-record schema and its completeness contract), `pool` (one run in its own directory, and the decision to keep an existing record) | everything |
| `experiment/` | `arms` (the switch matrix as data), `switches` (the driver's vocabulary and the capability probe), `input_files` (committed and lifted), `artifacts` (the committed per-configuration files), `data_provenance` (where the copied data came from) | everything but `core/` |
| `child/` | `child`, `evaluate`, `optimise`, `census` (the three entry points a measurement subprocess is started as, and what they load), `ystate` (the coupling state and its predicate; the copied driver loads it by path), `predicate`, `perturb`, `data_structure`, `postsolve` | the pool spawns them; the gates import them; the evaluation tally imports `predicate` to read exit states and evaluate the one predicate between them (the fixed-point distance) |
| `gates/` | `registry` (every gate and stage by name, the derived order, the gate table, the printers and the module's own command line), `gates` (G0′, `copy_identity` and `edit_behaviour` loading `PROCESS/copy_gates.py` by path; the shared entry references and `_with_capture`; GR's wrapper; the promoted self-checks; the `self_containment` gate), `gate_neutrality` (G1 and the comparison machinery), `gate_output_path` (G9, and the restricted statistic's excluded set), `gate_predicate_mode` (G8), `exclusion_review` (the review of G1's and G8's exclusion tables), `gate_audit`, `gate_composition`, `gate_entry`, `gate_prime`, `gate_records`, `gate_tally`, `gate_written_file`, `reproduction` and `reference` (gate GR and its committed reference), `selfcheck` | the runner, and `chain.py` |
| `measurement/` | `stats`, `tables`, `tally`, `tally_evaluation`, `tally_optimisation`, `analysis`, `plan_tables` | `gates/` imports it — a gate reads records, it does not decide what a record means |
| *(top level)* | `__init__.py` (the one public import surface), `chain.py` (the sequence the campaign and the smoke both run), `data/`, `reference/` | — |

**`ystate.py` is in `child/` since task A66 (carried by A73 under D27).** A measurement child loads
it, and so does the experiment's copied driver — by the literal path
`Path(__file__).resolve().parents[4] / "harness" / "child" / "ystate.py"`
(`PROCESS/process/core/solver/module_solve.py`), which `PROCESS/copy_gates.py` asserts as one of the
copy's permitted edits and `PROCESS/PROVENANCE.json` records. The move was a driver-copy edit for that
reason: the literal and the assertion changed in one commit, the provenance was regenerated, and
gate G1 was run as a straddle across it.

**Inside `gates/`, who imports whom.** `registry` imports every gate module and is imported by
the runner, `chain.py`, `selfcheck.py` and the analysis's dependency tooth — and by no gate module,
so a gate never reaches the registry that holds it. `gate_output_path` and `gate_predicate_mode`
import `gate_neutrality` (the comparison machinery) and `gates` (`_with_capture`);
`exclusion_review` imports all three gate modules; `gate_prime` and `gate_audit` import
`gate_output_path` for `excluded_by_the_per_run_nodes`. Every source scanner that holds a module name as a string — `self_containment`'s
`DECLARED_OUTSIDE_REFERENCES` (keyed by file name), `analysis.FORBIDDEN_IMPORTS` — was re-checked
at the split; the first found the moved line in `registry.py` and reported it until the table
named the file.

**The rule that makes the grouping worth having.** `child/` is exactly the set the harness
implementation plan's amendment 13, rule (vi) forbids editing while any measurement run executes.
Before, that set was a list in a change log; now it is a directory.

What is not here: **a campaign record**.  `EXECUTION_APPROVED` is `False`, every campaign stage
refuses and says why, and the refusal is reachable from the same button as the successes.  The
chain that will run the campaign is built and pressed — as the smoke — so what waits on the user's
approval is the press, not the code.

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
list lives in `REFERENCE_FIELDS` in `harness/gates/reference.py` and each field's one-line meaning is in
the committed file itself, so a reader does not have to open the plan to know what a cell is.

### Why it is committed rather than read from the records

The previous revision's records sit in an untracked bulk directory in the main checkout. Untracked
means git does not have them, and **this project has destroyed untracked run records three times** —
once taking with it the evidence behind a correction to a published headline (queue issues I-14,
I-15 and I-16; the trap is written up in `arch_surgery/docs/TRAPS.md`). A gate anchored on files
that can be deleted by retiring a working tree is a gate that will one day quietly have nothing to
compare against, and a check with no population is not a check.

So the compared fields were extracted **once** into a small committed file (32 KB), verified byte
for byte against the records at the time, and committed; the gate reads that and nothing
regenerates it (D25). The stages that extracted and verified it were retired with the survey's item
B7 — the file's `provenance` block names the root, commit and date it came from, and git history is
its second copy. If the records vanish tomorrow, the gate still works.

### How to read it

```bash
PY=/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python
cd arch_surgery/MDA_partitioning_experiment_v4

# what is committed, and what it does not cover — reads no records
$PY experiment_runner.py --reference show

# the report's two tables, rendered from the committed file with their captions
$PY experiment_runner.py --reference tables
```

Exit codes are the runner's: `0` pass, `3` the file is missing or in another format. `show` writes
its record under `../runs/reference/`, which is untracked. `harness/gates/reference.py --show |
--tables` takes the same two flags directly.

**What refuses.** An absent committed file, a file in another format, a lookup for an arm or seed
the set does not hold, a lookup by a retired arm name — each raises and says what it looked for.
The gate's own teeth (GR's eight, in `reproduction.py`) cover the comparison; the four teeth of the
retired extraction stage (a record deleted, a field deleted, the name map bypassed, a value changed
in a throwaway copy of the file) went with it; a doctored committed value is still caught by GR's
own `count` and `hex` teeth, which alter one reproduced value in a copy of the reference entry.

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
| `A1` — flat, with the burn time owned by a constant | the previous revision never ran that combination | the warm-equivalence gate: pinned at the reference's converged burn time it must reproduce the reference fixed point, with the cross-state residual below the tolerance and the pinned component bit-identical |

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
| `dsm_function_counts.json` | how many functions (the dependency analysis's submodels, a model with none counting as one) sit behind each block's collapsed-DSM rows, per configuration — the weight of the function-weighted twin of the per-module sweep tables; generated once from the analysis's exports at the named pin by `arch_surgery/fixedpoint/gen_function_counts.py`, committed, never read live (trap T9) | the measurement layer (`tally_*`, `analysis`) | check |

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

**A census record is placed like any other run record.** It carries `tree_git_head` and the rest of
the "where it ran" group on the record itself (`record_format` `census-2`), because that is the key
a survey of "which commit was each record under `runs/` made at" reads — the survey that catches a
`--resume` which kept what it should have re-made. The six records taken before this contract kept
the commit one level down, inside a nested `provenance` block, so the survey placed them nowhere;
the stage that reads a census now refuses an unstamped one by name, and the self-check names every
one on disk rather than leaving it merely absent from a survey.

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
| census | a census record carrying no tree stamp | the record contract: `census-2` stamps `tree_git_head` and the rest of the "where it ran" group on the record itself, and a record without them is refused by name rather than compared from nowhere |
| census | a census with no run record beside it | the same refusal, one step earlier |
| per-run | a node removed from the committed set | the node-by-node comparison |
| per-run | a live node added to the committed set | the node-by-node comparison — the direction that would defer a node the optimiser consumes |


---

## 13. The tally — the plan's tables, from the records

### What a tally is, and what it is not

A **tally** reads the run records and emits the experiment plan's §4 tables. It has **nothing to
pass**: what passes is the gate over the same records. So it is registered as a *measurement stage*
and runs under `--measure`, never under `--gate`, and nothing can read one of its tables as a
verdict. Where the tally *checks* something — a construction identity, a record contract, the cells
it must land on — that check is a **gate with teeth**, `tally_contracts`, and runs under `--gate`.

Three modules, and one rule each.

**`stats.py` — one function per declared construction, and the docstring is the declaration.** The
experiment plan declares how every published number is built: nearest-rank upper-middle median,
nearest-rank p90, *accepted optimum* = status ok **and** the output file's `ifail == 1`, the one
seed set (every arm converged), the pooled/median/worse ratio triple, the clustering rule and its
below-resolution category, the cost ratio with and without the retried seeds. Each is one function
here, and a report caption quotes its docstring rather than paraphrasing it. The previous revision
kept these as comments beside whichever code needed them, which is how one definition reached two
implementations and drifted twice.

Three of them are refusals rather than computations, because the plan states them as refusals:
`Population` refuses a record stamped `force_maxcal` (a budget-capped demonstration of the retry
ladder, never a measurement) and refuses a mixture of phases; `retried` is computed from
`attempts[]` and from nothing else, because there is no stored flag worth trusting; and
`attempt_summation` states the identity Σ attempts = the run's solve-phase total **as a number the
report prints**, which is what licenses publishing a cost ratio with and without the retried seeds.

**`tables.py` — four things a table cannot be emitted without.** A `Table` cannot be constructed
without a `Caption`, and a `Caption` cannot be constructed without units, what a row is, what a
column is, the population and the construction. Beyond that: a denominator that is a letter rather
than a count is refused by name (the plan's §4 placeholder tables print `n` where a count belongs,
deliberately, and a table copied from that template and half filled in must not be emitted); an
**acceptance** table carrying a wall-clock column is refused (no conclusion in this experiment rests
on a timing); a column that adds the two convergence tests' counts is refused (they are not the same
test and their widths differ by nearly two orders of magnitude, so their sum belongs to neither);
and a residual table whose rows were audited at two different positions without a column saying so
is refused.

**`tally_evaluation.py` and `tally_optimisation.py` — the two phases' tables.** Seven table kinds
for the evaluation phase (cost per call, matched accuracy on both rulers, the fixed-point distance
between arms — the predicate's residual between two arms' exit states at the same entry, restricted
as the audit is, reported and not accepted on; added from the exit states on disk after the campaign
by A76 (fixed-point-distance) — the ownership rung, the per-sweep overhead, the failure taxonomy,
and **node calls per block** with every configuration stacked) plus the predicate trial; ten for
the optimisation phase (the seed set, the failure table, the same-optimum check, check 2 in **both**
iteration constructions, the attempt summation identity, the cost with and without the retried
seeds, the achieved accuracy at the accepted optimum, the lift's residual, **node calls per
module** per configuration and **the optimiser's path** over the configurations — iterations, the
evaluation count ε from `sweeps_per_eval.n_evaluations`, the cost per evaluation ρ and the cost per
run R = ρ × ε). The last three are the report's headline tables (`docs/plans/REPORT_HEADLINE_TABLES.md`),
added by A79 (report-captions); their module grouping is derived from the committed node map and
the configuration's per-run artifact (`stats.node_groups`), never listed by hand.

**Every table carries a `kind`, a `summary` and a `detail` flag** (A79). The kind is the
construction key the report groups by and the numbers-unchanged proof keys cells by; the summary is
the caption of a few lines the report prints — what the table shows, its population, the one thing
not to infer — while the full declaration (units, row, column, construction, clauses, how to read)
is printed once per kind in the report's D.0 and is the same for every table of a kind; text that
varies per table (the reference arm and whether it is a fallback, the audit position, a
population's own share) lives in the summary. A table whose rows are runs, seeds or pairs of runs
is `detail=True` and goes to the companion file, never the report; `report_omits` names the
columns that list a value per seed inside one cell, which the report's copy leaves out and the
companion's keeps.

### The population problem, and the declared sources

`runs/gates/` is **not one population**. Several gates run the same arm at the same seed from
different entries, and three of them run it deliberately doctored. A per-run mean over that tree
would be a mean over a set nobody can state.

So the tally reads a **source**: a gate's **job set** whose records are a comparable set, declared in
`tally.SOURCES` with the sentence that says why and resolved through the pool — named by job set, not
by directory, because under the shared pool every gate's runs sit in one directory keyed by identity.
Two **gate** sources exist — the reproduction gate's planned runs, and the entry gate's pairing
runs — and five **campaign** sources: the campaign plan's own job set for each run stage
(`chain.campaign_jobs`), the stencil stage split into its forward and backward point sets, which pair
across arms by design-vector column rather than by seed. The campaign sources are declared only while
`EXECUTION_APPROVED` is True. **The tally publishes one family** (`tally.published_sources`): the
campaign family once a campaign record exists, the gate family otherwise — never both — and once the
campaign is present a gate record is *refused by kind* at the population's construction
(`stats.measurable_run_kinds(campaign_present=True)`; gate `run_kind_separation` proves both
directions). Every caption carries the source's sentence and names the kind of run it is over;
`analysis.SOURCES` declares the same seven, and the same one-family rule, independently. Records
under `runs/gates/` that belong to no gate source, and records under `runs/campaign/` that belong to
no campaign source, are **counted and named** in the stage's own record, so the smaller denominator
is a stated choice and not an omission. *(The campaign family was added by A75
(campaign-tally-source), issue I-24: the first campaign press found the tally with no source for the
949 records it had just made — the smoke could not expose it, because the tally refuses smoke
records by design and read seeded gate records instead.)*

Within a source, the optimisation phase is split again into **seed-complete arm groups**. The plan's
"the seeds on which every arm converged" assumes what a campaign guarantees — every arm at every
seed — and a gate's runs do not: the reproduction gate runs one set of arms at its unperturbed seed
and a different set at its perturbed one. Each group is a set of arms and the seeds at which all of
them ran, which *is* a population the construction applies to, and the group is named in every
table's title. In a campaign there is one group per configuration and the split is invisible.

### What the tally is checked against

The previous revision published a row of numbers for each of the twenty runs of the reproduction
reference. `tally_contracts` computes **the same cells from this revision's records** and compares
them without tolerance. Three of the cells are produced by one of this revision's own constructions
rather than read from a field — iterations on the final attempt, iterations summed over every
attempt, and the attempt count, all from `attempts[]` — which is what makes this a stronger
statement than the reproduction gate's field-for-field comparison: a *rule* landing on the previous
revision's published number says the rule is the same rule.

The committed reference is **never regenerated**; its bytes are the previous revision's numbers, and
a comparison that rewrote them would be a comparison with itself. Where a record field has been
renamed to the vocabulary's word for it, `reference.FIELD_NAME_MAP` translates the previous
revision's path to this revision's. The compared cell list is **derived** — the compared-field list
for the phase intersected with what that entry actually published — so a later task that drops a
field from the compared set drops it here too.

---

## 14. The analysis — the same cells, computed a second time

### Why a second implementation exists

Two implementations of one declared definition drifted apart **twice** in this project (queue issues
**I-18** and **I-19**): a rule was written down once, and the two places that computed it stopped
agreeing without anything failing. The tally is one implementation. `analysis.py` is the other, and
`--gate recomputation` is the only thing that can catch the drift.

What makes it a second implementation and not a second copy: **`analysis.py` imports no part of the
tally** — not `stats.py`, not either `tally*` module, not `tables.py`. Every construction in it is
re-derived from the declaration (the docstring in `stats.py`, which the experiment plan's §3.4–§3.6
wrote) and from the record fields `records.py` declares; the populations — the seven declared sources
and the one-family rule, the `force_maxcal` filter, the seed-complete arm groups, `retried` from `attempts[]` — are re-derived
the same way, and a population the two derive differently is reported as a **finding**, never
reconciled silently. What the analysis *reads* from the tally is its **output**: the two stage
records `runs/gates/tally_evaluation/measurements.json` and `…/tally_optimisation/measurements.json`,
cell by cell over `rows` keyed by `columns`.

### The gate, and what its denominator counts

`recomputation` reports three denominators rather than one, because they answer different questions:
how many **cells** were compared, how many **tables** they came from, and how many **run records**
were read — with the commits those records were made at, from `framework.survey_heads`. The cell
count is split again into cells produced by a **construction** and cells **composed as a string**
(`"3/3"`, `"[18, 68]"`, `"BR 0 · B0 0 · B2 0"`): agreement on a rendered string is weaker evidence
than agreement on a computed quantity, so the two are reported apart rather than added into one
number.

The tables are not the whole of what the tally publishes. The two stage records also carry the
**similarity verdict** of each evaluation-phase arm pair on each ruler and the **seed set** each
optimisation-phase arm group is over; a comparison that read only the tables would leave them
unverified, so they are compared beside the cells and counted in the same denominator.

Four refusals, each a way the comparison could pass over nothing:

| refused | why |
|---|---|
| an **empty comparison** — no table, or no cell in the tables there are | a gate that cannot find what it compares must refuse, never pass over nothing (trap T11) |
| a **budget-capped demonstration** (`force_maxcal`) in a population | such a record demonstrates a decomposition and is not a measurement of anything |
| a population **straddling two commits** without `--resume` | without it every run is re-made, so a record from another commit means one was kept that should not have been |
| the tally's **stage records absent** | `--verify` compares against the tally's output and never against its code, so the output has to be on disk |
| a tally stage record **computed over another run population** | a stage record left from before a change that moves cells produces mismatches that look exactly like a drift; each record's own `runs_provenance` is compared with this module's own survey, on the commits and the count, and a disagreement refuses with both sides named |

**A gate may declare that it reads a measurement stage.** `Gate.reads_from` names either kind:
`gates.assert_declared_dependencies` refuses, as the registry is built, a dependency naming something
nobody runs; `ordered_gate_names` orders the *gate* dependencies among themselves; and the button runs
each declared *stage* immediately before the gate that declares it, once per press, with the same
`--resume`. `recomputation` declares `reproduction`, `entry_and_warm`, `tally_evaluation` and
`tally_optimisation`, so `--gate all` makes what it reads and no chain needs reordering.

### The independence check, and the nine teeth

The property the whole gate rests on — *this module borrowed no construction* — is itself a
**checked criterion** and not a comment: the gate parses `analysis.py`'s own source and fails if it
imports `stats`, either `tally` module or `tables`. It is one more thing compared, so it is in the
denominator beside the cells.


| tooth | the deliberate break | what the gate must do |
|---|---|---|
| a tally cell moved by one | one integer cell of the tally's published output raised by 1 | report the mismatch — this half proves the comparison reads the tally |
| a construction altered in the analysis | the pooled ratio recomputed against **Σ arm** instead of **Σ reference**, for a whole recomputation | report the mismatches — this half proves the comparison reads the records through the analysis's own rules |
| an empty comparison | no table on either side | refuse |
| a demonstration record in a population | a record stamped `force_maxcal` | refuse |
| a retried flag trusted from a stored field | a record whose `attempt_accounting.retried` disagrees with `attempts[]`, in both directions | follow `attempts[]` and never the stored flag |
| a population straddling two commits | two records carrying different `tree_git_head` values | refuse without `--resume`; state the straddle with it |
| a construction imported from the tally | a source importing `harness.measurement.stats`, `harness.measurement.tally_optimisation` and `harness.measurement.tables` | name all three, and name nothing in a source that imports only the framework |
| a tally stage record over another run population | a stage record doctored to another commit, and one doctored to a smaller record count | refuse both, and accept one that agrees |
| a gate declaring a stage the registry does not hold | a gate whose `reads_from` names `a_stage_nobody_runs` | refuse as the registry is built |

### What cannot be recomputed from records

One emitted table — *the predicate trial* — is not built from run records at all. Its decisive-pass
counts come from an observer that watches each predicate evaluation **while the run happens** and
reads it again on the other ruler; nothing in a record afterwards reconstructs them. The analysis
recomputes that table's *shaping* from the same gate verdict the tally read
(`gates/predicate_mode/gate.json`) and the verdict names it, so a reader can see that those cells are
a check on the table and not on the measurement.

### The measurement stage

`recomputed_tables` emits the analysis's own markdown tables, with its own captions and its own
denominators, to be read beside the tally's. It has nothing to pass — the verdict on whether the two
agree is the gate's — and it refuses a table of its own built without a caption or without an integer
denominator, which is the same rule `tables.py` enforces for the tally, implemented a second time.

---

## 15. The chain — one sequence, two parameterisations

### What a "chain" is here

The campaign is not a single thing the harness does at the end; it is a **sequence of stages**, and
that sequence is written once, in `harness/chain.py`. A **plan** says how to run it: which
configurations, how many seeds, which entry regimes, and what kind of record the runs are stamped
with. Two plans exist.

| | the smoke | the campaign |
|---|---|---|
| configurations | the cheapest one, chosen from the records | every one |
| evaluation-phase seeds | one, undisplaced | 1–25, all displaced |
| optimisation-phase starts | one, unperturbed | `seed000` plus 24 displaced |
| stencil columns per arm | one | every column of the design vector |
| records stamped | `smoke` | `campaign` |
| needs the user's approval | no | **yes** — `EXECUTION_APPROVED` |

*Caption: one row per parameter the two plans differ in; everything not listed — the stage list, the
job construction, the pool, the record schema, the tally and the analysis — is the same code.*

They are one chain on purpose. A smoke written separately from the campaign exercises its own code
and reports on the campaign's; when the campaign's first press then fails, the smoke has said
nothing about it. Here the smoke's press *is* a press of the campaign's stages.

### The stages, in order

1. **`entry_references`** — one flat evaluation per configuration from the input file's own design
   point. Every evaluation-phase entry is a displacement of its exit state and the constant the
   pinned arms own is its converged burn time, so a reference that does not finish stops the chain
   rather than being entered from somewhere else.
2. **`evaluation_displaced`** — the plan's δ regime: every arm active on the configuration, every
   seed, one `call_models` each, all entered from the *same* displaced state at the same seed. The
   reference arm included — the published ratios are paired differences, and an arm entered
   somewhere else would make the difference partly the entry.
3. **`evaluation_stencil`** — the plan's stencil regime: the forward point `x_i (1 + epsfcn)` from
   the reference fixed point and the backward point `x_i (1 − epsfcn)` from **that forward point's
   exit**, which is the order the optimiser's own evaluator executes. The pair runs serially for
   that reason; different columns are independent and go through the pool. The column set is
   *derived* — the committed input file's variable count, plus the one column the lifted input file
   adds where an arm reads it — and then checked against the `nvar` each run stamped.
4. **`optimisation`** — every arm active on the configuration, one full optimisation per start.
5. **`tally_evaluation`**, 6. **`tally_optimisation`** — the two tally stages (§13).
7. **`tally_contracts`** — the tally's gate (§13).
8. **`recomputed_tables`**, 9. **`recomputation`** — the analysis's tables and its `--verify` (§14).

Stages 5–9 are the registry's. The chain names them and **refuses if the registry does not hold
one**, naming which and in which of the two registries it was looked for: a stage that is silently
skipped turns a chain that ran nine stages into a chain that reports on nine and ran eight.

Every stage prints a `runs read` line — how many records it read and at which commits — so a reader
never has to assume that the population a stage summarised is the one the press just made.

### Which configuration the smoke runs, and how it is chosen

Measured, not assumed. For each configuration the smoke's own job set is priced from the gate
records already on disk — the median **model-node executions** of one run of each arm it would run,
summed — and the cheapest wins. Node calls are exact and reproduce bit for bit; the wall clock
printed beside them is progress information and chooses nothing (I-10). A configuration the records
say nothing about falls back to a declared proxy and the row says so, so a reader can tell a
measurement from a derivation.

### The two separations, each a refusal with a tooth

**A smoke record is never summarised as a measurement.** A one-seed pass is a test of the machinery;
a median over one run published under a caption naming a population of twenty-five is trap T11 with
the denominator supplied. So the run kinds a published population may contain are *declared* —
`stats.MEASURABLE_RUN_KINDS` and, independently, `analysis.MEASURABLE_RUN_KINDS`, because the
analysis re-derives every declaration rather than importing it — and a record of any other kind is
**refused** where a population is built, not filtered out of it. A filter shrinks a population
quietly, which is the error this project has made three times.

**A campaign record is never made by the smoke.** The campaign plan refuses to compose while
`EXECUTION_APPROVED` is `False` or while the tree is not the experiment's own copy, and the smoke
asks for the smoke plan by name — there is no argument it could pass that would produce a campaign
record. Resume is closed the same way: the run kind is in the job identity `records.is_complete_for`
compares, so a record of one kind is never kept for a job of another, and a stamp cannot be laundered
by moving a directory.

Both directions are gate **`run_kind_separation`**, whose criterion is a survey of every record
under `runs/` by kind — including the positive statement that no record a declared tally source
covers is of an unsummarisable kind, and that no campaign record exists at all.

| tooth | the deliberate break | what the gate must do |
|---|---|---|
| a smoke record offered to the tally | a record stamped `smoke` handed to `stats.Population.of` | refuse |
| a smoke record offered to the analysis | the same record handed to `analysis.Population.of` | refuse |
| a gate record is still summarised | a record stamped `gate` handed to the same population | **keep it** — the positive control, so the refusal cannot pass by refusing everything |
| a campaign plan without approval | the campaign plan composed while `EXECUTION_APPROVED` is `False` | refuse |
| the smoke's plan forged into a campaign | the smoke plan with its run kind changed to `campaign` | refuse |
| resume across run kinds | a record stamped `campaign` offered to a smoke run's resume | not keep it |

### Where its records go

Under `runs/<plan name>/` — `runs/smoke/`, and `runs/campaign/` once there is one — never under
`runs/gates/`. The tally reads *declared sources* — the gate sources under `runs/gates/`, the
campaign sources under `runs/campaign/` — and never a directory as such; putting the chain's own
records under the gate tree would offer them to a stage that must refuse them, which would make
the refusal depend on a directory layout rather than on a decision. The chain also surveys its own
tree at the end of a press and refuses if it holds two run kinds.

---

## 16. The report's results tables, rendered rather than typed

`EXPERIMENT_REPORT.md` §4 once carried a template — every cell a *format*, `0.xxx` where a ratio
belongs and `n` where a count belongs — so the shape could be reviewed before anything was
measured, and the renderer then filled §4 with the tables the stages emitted. Since task A79
(report-captions) (2026-09-15, at the user's ruling that the report read as an academic paper does)
the tables are **Appendix D — Results tables** and §4 is hand-written conclusions that point at them
by number. `harness/measurement/plan_tables.py` reads the stages' records under
`runs/gates/<stage>/measurements.json` and writes two documents:

| document | holds | rendered from |
|---|---|---|
| `EXPERIMENT_REPORT.md`, the block between `## Appendix D — Results tables` and the end marker `<!-- plan_tables: end of the rendered results tables -->` | D.0 the constructions and populations, declared once per table kind from the stages' own records; D.1 the gate table; D.2 the evaluation phase's and D.4 the optimisation phase's **summarising** tables (per arm or arm pair and configuration), `Table D.1`–`D.n` in emission order, one caption of a few lines each, the construction name printed under each grid | `--measure gate_table`, `tally_evaluation`, `tally_optimisation` |
| `RESULTS_TABLES_FULL.md`, whole | F.1–F.2 every table with a row per run, seed or pair of runs and the evaluation phase's headline grids at the stencil entry points; F.3 the full versions of **every** table whose per-seed columns are omitted, the main text's as well as the appendix's; `Table F.1`–`F.m`; generated, never hand-edited | the same three stages |

*Caption: one row per document the renderer writes; the middle column is what it holds and how it
is numbered; the right column the stages whose records fill it. No cell is typed by hand and nothing
in the renderer computes a number.*

It refuses rather than guessing: a stage that has written no record, a stage that emitted no table
(a section with no population is not a section), a tally table without a `kind` or of a kind no
group of `plan_tables.GROUPS` declares (the grouping is a declaration, and whoever adds a table kind
places it), and a report in which the appendix heading or the end marker has moved or been reworded
— a renderer that writes into the wrong part of a shared document is worse than one that does
nothing.

**And it refuses a stage record the verdicts have outrun.** D.1 is rendered from the `gate_table`
*stage* record, not from the verdicts themselves, so a gate re-run after that stage would be
published here as it was rather than as it is — silently, and it happened once: a re-render
reproduced a failing row byte for byte after the gate had passed. The stage therefore declares what
it reads (`Measurement.reads_records`), the framework stamps every record it found — path, digest,
commit, time, verdict — into `records_read`, and the renderer re-surveys those same patterns and
refuses when a verdict has been re-made, removed or added since, naming the gate, both commits and
both times. The order is `--gate …`, then `--measure gate_table`, then `--plan-tables write`;
pressed the other way round the renderer stops instead of publishing the older table.

**`--plan-tables check`** compares both committed documents against what the records produce now,
as a diff and writing nothing, and also resolves every `Table D.n` / `Table F.n` reference in the
report's hand-written text against the numbers this rendering assigns — **table numbers are
positional** and move when a table is added, so a dangling reference fails the check. A cell is
traced by the construction name under its grid, never by its number
(A79 (report-captions)'s proof script keyed cells that way; removed with the other one-off proofs on 2026-09-15, in history at `c83aec6d`).

**What the cells are over is stamped on the appendix and in every caption's denominator.** While
`EXECUTION_APPROVED` is `False` there is no campaign, so every cell is over the **gate
population** — one or two seeds per arm — with the commit(s) those records were made at, the audit
position, the convergence ruler and the exit-audit instrument version, all read back from the
records themselves rather than written down. The campaign fills the tables again, over its own
seeds, after the user approves execution; the campaign of 2026-09-14 is what the report carries.
