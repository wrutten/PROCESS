# A57 (driver-output-path) — the output path becomes a driver choice, and the exit audit moves to the position the plan declares

> **Document status** — **MERGED, archived.** Task **A57 (driver-output-path)**, branch `A57-driver-output-path`
> (retired) off `architecture_surgery` at `22bb8656`, merged on 2026-09-10 (`6c7c742e`); the orchestrator's
> critical assessment (protocol §5) is §16. Folder position records lifecycle, not validity (trap T3).

---

## 1. The words, spelled out once

This report is meant to read without the project's queue open beside it.

| term | what it means here |
|---|---|
| **the driver** | the part of PROCESS that decides *when* models run and *when* to stop: `process/core/caller.py` and `process/core/solver/`. This experiment changes only the driver; every physics and engineering model is frozen at the base commit `c0ae5b28` |
| **the copy** | `arch_surgery/MDA_partitioning_experiment_v4/PROCESS/` — this revision of the experiment runs **its own copy** of the whole PROCESS package (decision D20), so a change here cannot disturb the tree the previous revision's records were made against |
| **the harness** | `arch_surgery/MDA_partitioning_experiment_v4/harness/` — everything that composes an arm, starts a run, records it and checks it. It never runs PROCESS in its own process: one run, one fresh subprocess, its own working directory |
| **configuration** | one optimisation problem: an input file plus the committed artifacts describing it. Three of them, in the order used in every table: `large_tokamak_nof`, `low_aspect_ratio_DEMO`, `st_regression` |
| **arm** | one column of the experiment's switch matrix — one assignment of the driver's environment switches. `BR` is PROCESS as shipped; `B0` the flat control; `B1` the flat control with the optimiser owning the burn time; `B3` the partitioned architecture. `AR`/`A0`/`A0p`/`A1` are their evaluation-phase twins |
| **the coupling state** | the measured set of state fields the in-loop models write — 840 / 846 / 827 components on the three configurations. Convergence is tested on *it*, not on the objective |
| **the exit audit** | one further full sweep of the whole model set past termination, measuring how far the state moves. The same instrument in every arm; its own model calls are counted and **never charged** to the arm. It is what "compare at matched achieved accuracy" is measured with |
| **the output-time loop** | upstream PROCESS writes its output files through a **second** loop: having accepted a design, it evaluates the whole model set again, writes an output file to a scratch location, and repeats — up to ten times — until two successive files agree float by float at `rtol = 1e-6`. Only then does it write the real files. The code calls it `MDA_Output`; this project calls it the output-time loop |
| **per-run deferred nodes** | model nodes an arm runs **once per run**, at the accepted optimum, instead of once per sweep — `vacuum`, `water_use`, `costs`, and `pulse` on `st_regression`. They execute inside the output path |
| **a gate** | a check that must pass before a number is believed. **Teeth** are deliberate breaks the check must catch: a check whose failure mode has never been exercised is an assertion, not a measurement (orchestration protocol §12) |
| **DR2** | the driver change this task implements, as numbered in the V4 harness implementation plan §3.2: "output path without `MDA_Output` for the intervention arms, environment-switched" |
| **τ** | the one tolerance every convergence test in the experiment uses, `1e-6` (decision D23) |

---

## 2. Verdict, in one page

**DR2 is implemented, the exit-audit snapshot hook with it, and every gate passes.** One gate — G1
— **failed on its first run at the final commit**, on a defect in its own exclusion set rather than
in anything this task built; the defect was fixed and the gate re-run, and both runs are reported
(§7.4).

*Caption: one row per gate or check. "Population" is what the criterion was computed over — every
count carries its denominator. Every criterion is a count or a bit comparison and no tolerance is
applied anywhere in this table. "At" is the commit the gate ran at; three commits appear because a
gate is re-run when the code it reads changes, and the last of them is the fix G1's failure
produced. §14 gives the command per row.*

| gate | what it binds | at | verdict | population, and the result over it | teeth |
|---|---|---|---|---|---|
| **G0′** | the physics stays frozen in the copy | `29beeeae` | **PASS** | 77 files under the copy's `process/models/` against `c0ae5b28`, plus the file set: **76 byte-identical**, 1 differing and approved (`pulse.py`, D14(b)), **0 unapproved** | 4/4 |
| **G1** | DR2 is inert with its switch unset | `b78d96cd` | **FAIL** | **6 of 2 371** record values differ — one per run pair, all of them `tree_untracked_paths_n`, `0 → 1`; **0 of 51 319** output-file lines differ. §7.4 | 4/4 |
| **G1**, after the fix | the same | `29beeeae` | **PASS** | 6 run pairs: **0 of 2 359** record values and **0 of 51 319** output-file lines differ; 567 values and 45 lines excluded by name with their reasons | 4/4 |
| **G9** | the output path writes the state the solve handed over | `b78d96cd` | **PASS** | 11 runs at seed 0 (every optimisation-phase arm on every configuration where it is active): **0 of 3 825** coupling-state components differ in hex, **0 of 54** solve-describing values differ from gate GR's records, 49/49 individual checks pass | 4/4 |
| **GR** | the rewritten harness still reproduces the previous revision | `b78d96cd` | **PASS** | 20 runs (14 optimisations + 6 evaluations): **270 of 270** compared values identical, no tolerance; record contract 20/20; substitutes `A0p` PASS and `AR` PASS (12/12) | 7/7 |
| copy gates | the copy is its source commit plus its recorded edits | `29beeeae` | **PASS** | 224 files against `f2dc9243`: 219 identical, 5 differing and all recorded hunk by hunk, **0 unexplained** | 10/10 |
| `PROCESS_diff.py` | every hunk is claimed by a named mechanism | `29beeeae` | **exit 0** | 68 hunks in 5 files, **0 unexplained**; `caller.py`'s 46 hunks include 5 claiming the new switch and 10 the snapshot hook | — |
| self-check | the harness's declarations agree with the tree it runs | `29beeeae` | **PASS** | 6 of 6 checks, 203 comparisons, 0 mismatched | 43/43 |

**What changed, in three sentences.** The output path is a driver choice:
`PROCESS_ARCH_OUTPUT_LOOP=none` calls the file-writing step **once** on the accepted state and runs
no output-time sweep at all, while unset (or `=upstream`) leaves upstream's path exactly where it
was, line for line. The driver now counts what it did — the sweeps that loop ran, and the entries to
the output path — so every optimisation record carries `output_path` and a non-null
`output_loop_sweeps`, which is `0` under the one-call path by construction rather than by assertion.
And the exit audit has moved to the position the experiment plan declares for **every** arm — the
entry to the output path — reached by a snapshot the driver takes there, with the residual computed
after the run from the restored snapshot.

**Three findings worth reading past the verdict.**

1. **The output-time loop does move the accepted state before writing it out — on two of the three
   configurations.** Holding the solve fixed and varying only the output path, the reference arm's
   output file differs in **11 of 16 173** lines on `large_tokamak_nof`, **0 of 16 434** on
   `low_aspect_ratio_DEMO` and **10 of 18 691** on `st_regression`, at an identical accepted
   objective and an identical solve-phase cost. The `0` is as much the finding as the other two:
   the effect exists, it is small, and it is **configuration-dependent** (§10.1).
2. **The signal the plan asked to be "looked for on purpose" is there, and it is one component.**
   With the audit taken at the accepted point, the arms that write their files once leave exactly
   **one** coupling-state component above τ on both pulsed configurations and **none** on
   `st_regression` — the same component both times, `tfcoil.insstrain`, at 7.1e-3 and 7.0e-3
   scaled (§10.3).
3. **One `B3` run needed a third output-time sweep.** Of the 14 optimisation runs of gate GR, 13
   settle their output files after 2 sweeps and one — `B3` on `st_regression`, seed 0 — needs **3**
   (§10.2). That is the same shape of event the previous revision found by accident on three `st`
   `B3` runs and which the plan's §3.3 asks to be looked for deliberately. **1 of 14 runs at one
   seed each is not a rate**, and none is claimed.

---

## 3. The output path, before and after

*Caption: the optimisation-phase output path, statement by statement, before this task and after
it. Line numbers are `PROCESS/process/core/caller.py` in the experiment's own copy: at the branch
point `22bb8656` on the left, at the driver commit `234e0462` on the right. The per-run deferred
nodes' position is called out in both columns because keeping it unchanged is a requirement of this
task, not an accident of it.*

| # | before (`22bb8656`) | after (`234e0462`) |
|---|---|---|
| 1 | `write_output_files` entered (`:1838`) | `write_output_files` entered (`:1985`) |
| 2 | the solve-phase node counter is frozen — `NODE_CALLS_AT_OUTPUT[0] = NODE_CALLS[0]` (`:1855`) | unchanged (`:2002`) |
| 3 | — | **new**: `OUTPUT_PATH_ENTRIES[0] += 1`, then the snapshot hook at position `entry_to_write_output_files` (`:2010-2011`) |
| 4 | the accepted design vector is read out of `numerics.xcm` | unchanged |
| 5 | **the per-run deferred nodes run** — `caller._sweep_block(x, ps)` (`:1872-1877`) | **unchanged, and in the same place** (`:2028-2033`) |
| 6 | the run time is written to the output file | unchanged |
| 7 | `call_models_and_write_output` (`:1429`) | `call_models_and_write_output` (`:1555`) |
| 8 | up to ten iterations of: divert output to scratch files → `_call_models_once` → `finalise` → compare the two most recent files float by float at `rtol = 1e-6` (`:1463-1511`) | **under `upstream`, unchanged**, with one integer added per sweep: `OUTPUT_LOOP_SWEEPS[0] += 1` (`:1611`). **Under `none` the entire block is skipped** (`:1597`) |
| 9 | on agreement: stop diverting, then `finalise` on the real files (`:1511`) | unchanged, with the snapshot hook at position `before_finalise` immediately before it (`:1656`) |
| 10 | on ten sweeps without agreement: a warning, then `finalise` with the warning attached (`:1543`) | unchanged, with the same hook (`:1689`) |
| — | *(no such path)* | **under `none`**: the hook at `before_finalise`, then `finalise` **once**, then return (`:1597-1599`) |

**Where the per-run deferred nodes run, precisely.** Inside `write_output_files`, **after** the
solve-phase counter is frozen and **after** the snapshot is taken, and **before** the output path
proper — statement 5 above, at `caller.py:2028-2033`. Their model calls are therefore inside
`node_calls_total` and outside `node_calls_solve_phase`, which is what makes the solve-phase count
the cost unit the experiment compares. Nothing about that moved: it is the same statement, guarded
the same way, in the same position relative to both the freeze and `finalise`. Gate G1 compares the
whole record on the reference arms, `post_solve_totals` included, and finds no difference.

**What `none` does *not* do.** It does not skip writing the files, does not skip the per-run
deferred nodes, and does not change `finalise` — the same function writes the same two files from
the same data structure. What it skips is the *re-solving*: the up-to-ten evaluations of the whole
model set that upstream performs between accepting a design and writing it down.

### 3.1 The switch, as the registry now carries it

*Caption: the switch-registry row this task fills in, as `harness/switches.py` and the switch table
in `harness/README.md` now carry it. "Readback" is what a child process reads out of the **imported
driver** to say what the driver resolved — never the environment echoed back, because a tree that
ignored a switch would otherwise report the arm the harness asked for (the failure shape of traps
T6 and T10).*

| | |
|---|---|
| **term** | output-time loop |
| **variable** | `PROCESS_ARCH_OUTPUT_LOOP` |
| **values** | `upstream` — also what the driver does with the variable unset — and `none` |
| **composed by** | `B1` and `B3` (`none`). The evaluation-phase arms carry **no switch for it at all**: they run one evaluation and never reach the output path, so the matrix cell reads `n/a` for them |
| **readbacks** | `caller.OUTPUT_LOOP_NAME`, `caller.OUTPUT_PATH_NAME` |
| **counters** | `caller.OUTPUT_LOOP_SWEEPS` — sweeps the loop ran, `0` under `none` by construction; `caller.OUTPUT_PATH_ENTRIES` — entries to the output path, one per scan point |
| **record fields** | `output_path` ∈ `mda_output` \| `finalise_once`; `output_loop_sweeps`; `output_path_entries` |
| **illegal value** | `ArchitectureRefusal` at import, naming the legal set |
| **retired names** | none — the switch is new |

`upstream` is a listed value although it is also the unset behaviour, and that is deliberate: the
reproduction gate sets it **explicitly** on the two arms whose matrix cell turns the loop off (§8).
An override the driver reads back is an override that can be checked; one that relies on a default
cannot be told apart from having forgotten to set anything.

---

## 4. The audit's position, and why the plan's sentence could not be met in place

### 4.1 What the plan asks for, and why it was not already true

The experiment plan's §3.3 requires that "the exit audit is taken at the same position in every arm
— at the entry to `write_output_files`, before any output-time sweep — and the audit position is
recorded per run". The reason is a comparison, not a convention: the arms are compared at **matched
achieved accuracy**, and a residual table whose arms were measured at different points of their
runs, without saying so, puts two different quantities under one heading.

Before this task the audit was taken **after the run**, and the record said so —
`audit_position: after_run` beside `audit_position_declared: entry_to_write_output_files`, with a
recorded sentence naming why the declared position was out of reach. That sentence, filed by
A50 (harness-run), was right, and it is worth restating because it is the reason this task exists:

> the audit sweep mutates the state it measures, so taking it at the entry to `write_output_files`
> would hand the output path a state the optimiser never accepted: the output files, the MFILE exit
> code and the total node count would all be of the audited state.

That is the whole difficulty. The audit is *one more evaluation of every model*. Run it at the entry
to the output path and everything downstream — the per-run deferred nodes, the output-time loop, the
files themselves — proceeds from a state one sweep past the one the optimiser accepted. The
measurement would change the thing it measures, and it would change exactly the numbers the
experiment publishes.

The same sentence named a second obstacle: the declared position sits **before** the per-run
deferred nodes, which run inside `write_output_files`. That one turns out not to be an obstacle once
the first is solved, but it does change what a whole-state residual count means — §4.3, and every
caption that publishes one.

### 4.2 What is done instead

**The driver snapshots; the harness audits afterwards, from the snapshot.** At the entry to
`write_output_files` — before the per-run deferred nodes and before any output-time sweep — the
driver calls an installed hook that serialises the coupling state exactly: floats as hexadecimal
literals, so a state written out and read back is the same state to the bit. The run then proceeds
untouched — the per-run nodes run, the output path runs, the files are written, the exit code is the
optimiser's. **After** the run, the measurement subprocess writes that snapshot back into the data
structure, proves the write took bit for bit, and takes the same one-sweep audit it always took,
now on the state the solve handed over.

Three properties follow, and each is checked rather than asserted:

* **the audit changes nothing the run produces.** It happens after the last file is written. Its
  model calls are recorded (`exit_audit.audit_node_calls` — 21 on `st_regression`, one full sweep)
  and marked `charged_to_the_arm: false`; the arm's own counter was frozen long before;
* **the audit measures the state it says it measures.** `predicate.write_entry_state` reads the
  whole state back after writing it and compares it component by component against the snapshot. A
  restore that is **not** bit-exact **refuses** the audit and records why, rather than reporting a
  residual of a state nobody chose. On every run made in this task the restore was bit-exact on
  every component; the evidence is in each record at `exit_audit.restored_from_snapshot`;
* **every arm is audited at the same position.** `audit_position == audit_position_declared ==
  entry_to_write_output_files` on every optimisation record of the campaign composition — including
  the reference arm `BR`, which composes no architecture switch at all. Gate G9 checks that field
  first on each of its eleven runs, and all eleven pass it.

**Why the driver holds a hook rather than a serialiser.** The shape of a snapshot belongs to the
harness's coupling-state layer: it is defined by a committed per-configuration artifact and by
`harness/predicate.py`. Putting that definition into the copy would create a second copy of a shared
definition, which is precisely what decision D14(c) exists to prevent and what the driver's own
comment in `module_solve.py` already refuses to do for the predicate module. So the driver owns the
*position* and holds a callable slot; the measurement subprocess installs the callable. With nothing
installed — every run of PROCESS that is not being measured — the entire mechanism is two `is None`
tests per run. A hook that raises is **recorded and does not stop the run**: an instrument that can
change a measurement's outcome is not an instrument, and the harness refuses to report an audit
whose snapshot carries an error rather than reporting one it could not take.

**Two positions, not one.** The hook is called at `entry_to_write_output_files` and again at
`before_finalise`, immediately before the single call that writes the real files. The second is what
makes gate G9's first criterion a bit comparison rather than an argument from code structure: "the
state written out is the state handed over" is then two snapshots compared component by component,
not a claim that nothing could have happened in between.

### 4.3 The per-run deferred nodes, and what "restricted" now means

The snapshot is taken **before** the per-run deferred nodes run. That is the literal reading of "at
the entry to `write_output_files`", and it is the only one under which "the state the solve handed
over" is true.

It has a consequence that must travel with every residual this position produces. The audit sweep
runs **every** node, the per-run ones included. Measured from a state taken before they ran, their
own outputs necessarily move — and by a lot, since they were last computed from an earlier iterate.
A whole-state count of components above τ on an arm that defers per-run therefore reports that
movement as non-convergence. It is not: it is the deferral doing what it is for. §10.3 measures the
size of it: 113 components above τ whole-state against 1 restricted, on the same run.

The **restricted** statistic is what stays comparable, and it is the statistic the experiment
already used: the components the per-run deferrable nodes write are excluded, **derived** from the
committed per-run deferral artifact (which names the nodes) and the committed run-time write census
(which says what each node writes on each configuration), never listed by hand. One excluded set per
configuration, from the committed input file's artifact, so that every arm of that configuration is
restricted by the same set — which is the whole point of a restricted statistic. §10.3 publishes
both counts side by side with the derivation, and deliberately does **not** publish the whole-state
*maximum* on an arm that defers, because on such an arm that maximum is a per-run node's own output
and says nothing about convergence.

For the optimisation phase the restricted statistic is computed by the measurement stage from each
run's own committed residual vector plus those same two artifacts. Carrying it inside the
optimisation record belongs with gate **G4**, the audit-restriction gate, which is
**A52 (harness-gates)**'s; §13 hands that over with what it costs.

### 4.4 What still uses the old position, and why

`after_run` — the previous revision's audit position — remains reachable, and **exactly one caller
may ask for it: gate GR**, the reproduction gate. That gate exists to reproduce the previous
revision's twenty records bit for bit, and `exit_audit.residual_max_hex` is one of the 270 values it
compares. Reproducing a residual means measuring it where it was measured. Every optimisation run GR
makes therefore audits at `after_run` and says so in its own record
(`audit_position_note` carries the reason), and the gate's verdict record stamps the position
alongside the switch overrides as one block. Anything else asking for it would be a composition
nobody checked; the campaign composition never does, and `optimise.py` accepts only the two declared
values.

Gate G1 also pins the audit position — to `after_run`, on **both** of its captures — for a different
reason, given in §7.2.

---

## 5. The copy's provenance and the diff view

`PROCESS/copy_gates.py` gains two `PermittedEdit` rows for `caller.py`, both under task A57: a
**switch added** (`PROCESS_ARCH_OUTPUT_LOOP` with its two counters) and an **instrument hook**
(`EXIT_SNAPSHOT_HOOK` / `EXIT_SNAPSHOTS` at two named positions). `PROVENANCE.json` was regenerated
so that the recorded zero-context hunks and the post-edit sha256 are what the gate compares.
Regenerating provenance **refuses** unless the set of files differing from the source commit is
exactly the permitted-edit list, so it cannot become the way an unapproved edit is blessed.

`PROCESS_diff.py` gains two mechanism labels and nine annotation rows, so every new hunk is claimed
by a named mechanism instead of being reported `UNEXPLAINED`, and `caller.py`'s summary paragraph
gains the output path and the hook.

*Caption: `PROCESS_diff.py --markdown` at `29beeeae`, one row per file in which the copy differs
from its source commit `f2dc9243`. "+/−" are lines added and removed by `git diff` **against the
commit**, never against a working tree. "Claimed by A57" counts the file's hunks the annotation map
attributes to this task's two mechanisms; a hunk may serve more than one mechanism, so the
per-mechanism counts do not partition the hunk count. Population: all 224 files of the copied
package; the 219 that are byte-identical carry no row.*

| file | + | − | hunks | claimed by A57 |
|---|---:|---:|---:|---|
| `process/core/caller.py` | 651 | 466 | 46 | the snapshot hook (10); `PROCESS_ARCH_OUTPUT_LOOP` (5) |
| `process/core/solver/__init__.py` | 112 | 1 | 1 | — |
| `process/core/solver/constraints.py` | 2 | 2 | 1 | — |
| `process/core/solver/module_solve.py` | 155 | 228 | 15 | — |
| `process/core/solver/subsolve.py` | 160 | 103 | 5 | — |
| **total** | **1 080** | **800** | **68** | **0 hunks unexplained** |

`PROCESS_diff.py` exits **0**. Its frozen-physics section restates gate G0′'s verdict for a reader
who will not run it: 76 of 77 model files byte-identical to `c0ae5b28`, the one difference
`process/models/pulse.py`, approved under D14(b).

`PROCESS/copy_gates.py all` — **ALL GATES PASS**:

| gate | verdict | population | teeth |
|---|---|---|---|
| copy-identity | PASS | 224 files against `f2dc9243`; 219 identical, 5 differing and recorded hunk by hunk; 0 unexplained; file set matches | 4/4 |
| frozen-physics (G0′) | PASS | 77 model files against `c0ae5b28`; 76 identical, `pulse.py` the one approved difference; 0 unapproved | 4/4 |
| smoke-import | PASS | `import process` from a directory that is neither tree resolves under the copy; the tooth without `PYTHONPATH` resolves elsewhere | 1/1 |
| edit-behaviour | PASS | the added existence check refuses typed where the source commit raised a bare `FileNotFoundError` | 1/1 |

---

## 6. Gate G0′ — the physics stays frozen in the copy

Run through the harness gate framework, which loads the single implementation in
`PROCESS/copy_gates.py` **by path** rather than restating the criterion — two implementations of one
criterion is how they drift.

*Caption: gate G0′ at `29beeeae`. The comparison is against `git cat-file` at the base commit, never
against a working tree, so an edit in the repository-root tree cannot mask one in the copy or the
reverse. Population: every file under the copy's `process/models/`, plus the file set itself.*

| | |
|---|---|
| **verdict** | **PASS** |
| **files compared** | 77 |
| **byte-identical to `c0ae5b28`** | 76 |
| **differing** | 1 — `process/models/pulse.py`, approved under D14(b) (the burn-time residual extracted into a driver-solvable form, the arithmetic verbatim) |
| **unapproved differences** | 0 |
| **files missing / added** | 0 / 0 |
| **teeth** | 4 of 4 tripped: one byte of `vacuum.py` changed → FAIL; `vacuum.py` removed → FAIL; a file added → FAIL; the *approved* file changed further → FAIL |
| **record** | `runs/gates/g0prime/gate.json` |

The fourth tooth is the one that matters for a copy carrying an approved model edit: a per-file
sha256 loop that pardoned `pulse.py` wholesale would let any further change to it pass. It does not.

---

## 7. Gate G1 — switch neutrality

### 7.1 The construction

Two runs on each configuration — one optimisation (`BR`) and one evaluation (`AR`), both composing
to an environment with the **whole** switch vocabulary cleared, which is precisely the condition G1
is about. The "before" capture was taken at the branch point **`22bb8656`**, with the copy's driver
verified byte-identical to that commit (`git diff --stat 22bb8656 -- .../PROCESS/` empty) *before*
any edit was made; it cannot be re-taken, which is what makes it a *before*. The "after" capture was
re-taken at each commit the gate was run at. Every deterministic leaf of the two records is
compared, plus PROCESS's own output file line by line — not a curated list of interesting fields,
because a curated list cannot notice a field nobody thought of.

### 7.2 Both captures are pinned to one audit position, and a pair that is not refuses

G1 binds the *driver*, but its two captures are made by the *harness* as it stood at each commit,
and this change moves a harness-side instrument as well as the driver. Where that happens, pinning
the instrument to one position on both sides is what keeps the comparison about the driver: the
whole `exit_audit` block — residual, argmax, brief, restricted statistic, the audit's own node count
— is then compared value for value instead of excluded. G1's optimisation runs therefore audit at
`after_run` on **both** sides, the manifest records the position, and a capture pair whose records
disagree about it **refuses to compare** rather than being repaired by adding `exit_audit` to the
exclusion list. That refusal is one of the four teeth.

The alternative — letting each side audit wherever its own revision does, and excluding the block —
would have put the most sensitive thing G1 compares outside the comparison. It is named here because
it was the obvious cheap route and was not taken.

### 7.3 The result

*Caption: gate G1 at `29beeeae` against the branch point `22bb8656`. One row per run pair. "Values"
are deterministic leaves of the run record, compared without tolerance, floats through their hex
form so that NaN ≠ NaN and −0.0 ≠ 0.0 are not silently forgiven; "lines" are lines of PROCESS's own
output file. Excluded values and lines are named individually with their reasons in the gate record
and summarised below. Population: 3 configurations × 2 reference arms = 6 pairs.*

| arm | configuration | values differing / compared | output-file lines differing / compared |
|---|---|---:|---:|
| `BR` | `large_tokamak_nof` | **0 / 501** | **0 / 16 173** |
| `AR` | `large_tokamak_nof` | **0 / 336** | **0 / 7** |
| `BR` | `low_aspect_ratio_DEMO` | **0 / 495** | **0 / 16 434** |
| `AR` | `low_aspect_ratio_DEMO` | **0 / 323** | **0 / 7** |
| `BR` | `st_regression` | **0 / 408** | **0 / 18 691** |
| `AR` | `st_regression` | **0 / 296** | **0 / 7** |
| **total** | | **0 / 2 359** | **0 / 51 319** |

*(An evaluation-phase arm writes a 7-line output file: one evaluation produces no MFILE of the
optimisation's shape. The whole of its record is compared, which is where its 336 / 323 / 296 values
are.)*

**567 record values and 45 output-file lines are excluded, each by name with its reason.** 384 of
the 567 are two blocks the change itself rewrites — `env_architecture` (222) and `resolved_switches`
(162), the switch vocabulary and its readbacks, which gain a name on the "after" side by
construction. 144 are run metadata that cannot be equal between two runs of the same code: paths,
wall clock, cpu time, memory, load, and the commit, which differs *because* that is what G1
compares. The remaining **39 are this task's**:

*Caption: the eight exclusions added by this task, with the count of leaves each accounts for across
the six pairs and the reason each is excluded. The first six are fields the harness itself adds or
rewords between the two commits; the last two are the defect §7.4 exposed. Nothing else was added;
the 33-name set as a whole is inherited from A56 (driver-renames) to be reviewed, not extended.*

| excluded path | leaves | why |
|---|---:|---|
| `output_loop_sweeps` | 3 | the count is what the change adds: null where there was no counter, measured where there is one. What the two output paths *did* is still compared in full, through the output file and through `node_calls_total` |
| `output_loop_null_because` | 3 | the sentence explaining the absent counter, present only on the earlier side |
| `output_path_entries` | 3 | a counter the change adds; absent on the earlier side |
| `audit_snapshot` | 6 | the snapshot block the change adds. On these runs it reads `{installed: false, why: …}`, because G1 pins both sides to `after_run` |
| `reproduction_overrides` | 6 | a field the record gains so a run made under the reproduction gate's overrides says so; null on both sides here, absent on the earlier one |
| `audit_position_note` | 6 | the sentence saying how the audit position is reached, which is what the change rewrites. `audit_position` **itself is compared**, and a pair that disagrees about it refuses |
| `tree_untracked_paths_n` | 6 | the count of a list already excluded — §7.4 |
| `tree_modified_tracked_n` | 6 | the count of a list already excluded — §7.4 |

`output_path` is deliberately **not** excluded: it reads `mda_output` on both sides — declared as an
unimplemented capability before, resolved from the driver after — and is compared and equal.

**Teeth — 4 of 4 tripped.**

| tooth | construction | result |
|---|---|---|
| captures audited at different positions | a throwaway copy of a captured record with its audit position moved to the other legal value | **REFUSED** to compare, naming both positions |
| one value moved by one ULP | `values.norm_objf` of a throwaway copy nudged by one unit in the last place (`0x1.99999999b822dp+0` → `…82e`) | **FAIL**: 1 of 501 values differ, naming the field |
| one output-file line changed | the exit-code line of a throwaway copy of a captured output file changed | **FAIL**: 1 of 16 173 compared lines differ |
| missing "before" record | the "before" capture asked for at a directory that does not exist | **REFUSED**, not skipped (trap T11: a check with no population is not a check) |

### 7.4 G1 failed once, on a defect in its own exclusion set

**The failure, with its numbers.** Run at `b78d96cd`, G1 reported **FAIL**: **6 of 2 371** record
values differed, **0 of 51 319** output-file lines. The six were one per run pair and all the same
field — `tree_untracked_paths_n`, `0 → 1`. The tree carried exactly one untracked file while the
"after" capture ran: this task's own draft report. `tree_modified_tracked` was `[]` and
`tree_git_dirty` was `false` on both sides, so **no tracked file had moved**, and nothing about the
driver's behaviour differed.

**The defect.** G1's exclusion set excluded `tree_modified_tracked` and `tree_untracked_paths` —
the two lists — and did **not** exclude `tree_modified_tracked_n` and `tree_untracked_paths_n`,
their counts. A single scratch file beside the runner therefore failed a byte-identity gate on a
field that cannot change what the driver does. That is precisely the false alarm the run-record
schema was amended to prevent when it split "modified tracked" from "untracked": A44 (transfer-gap)
had a whole set of records stamped dirty because the scan counted untracked files while the measured
code was clean, and the harness plan's §4.4 records the rule as *"a campaign refusing on scratch
files is a false alarm; one passing over a modified tracked file is the real failure."* The list
half of that rule reached G1's exclusion set and the count half did not.

**What was done.** Both counts were added to the exclusion set, on the same reason as their lists
and with the reason recorded beside them (`29beeeae`), and G1 was re-run: **PASS, 0 of 2 359 values,
0 of 51 319 lines**, §7.3. The count of compared values falls by 12 — the two fields across six
pairs — and the excluded count rises by the same 12, which is the arithmetic a reader should be able
to check.

**What was deliberately not done.** Committing the report first would have made the gate pass
without fixing anything, and the next scratch file would have failed it again. A failed gate is a
result; the fix is to the defect it found.

**What this does not hide.** A modified *tracked* file is the thing that can move a measurement, and
excluding its count hides nothing: the list itself was already outside the comparison, the fact is
recorded in every run record, the harness self-check has a dedicated check and two teeth for the
tracked/untracked distinction, and a tracked modification that changed the driver would move the
behaviour — which is what the other 2 300-odd values and the 51 319 output-file lines compare.

---

## 8. Gate GR after DR2 — the harness still reproduces the previous revision

### 8.1 The allowance is gone; an override takes its place

Before this task, gate GR ran `B1` and `B3` under a **pending allowance**: those arms declared a
switch no tree implemented, and the gate was permitted to compose their environments without it.
That allowance is now meaningless — the tree implements the switch — and leaving it in place would
have made GR run the two arms with the loop **off**, against records made with it **on**. So it is
replaced by an explicit, recorded **override**, and the override is *derived from the matrix rather
than listed*:

* `reproduction_overrides(arm)` reads the arm's own output-loop matrix cell. A cell reading `none`
  yields `{output_loop: upstream}`; anything else yields nothing;
* `assert_overrides_match_matrix()` checks **set equality** between the arms that get an override
  and the arms whose cell reads `none`. An arm that gains the cell without gaining an override — or
  keeps an override after losing the cell — **refuses the gate**. The set is `{B1, B3}` and the
  gate's own record states it;
* the value is composed **explicitly** (`PROCESS_ARCH_OUTPUT_LOOP=upstream`), not left unset, so the
  driver reads it back and the run record carries what it resolved. Verified on GR's `B3` record for
  `large_tokamak_nof`: environment `upstream`, asked `upstream`, resolved `upstream`, 2 sweeps run;
* **the campaign may not carry one.** `pool.environment_for` refuses a `campaign` run with any
  override, refuses one naming a switch the registry does not know or the tree does not implement,
  refuses an illegal value, and refuses one whose value is what the arm composes anyway — an
  override that changes nothing is an override nobody checked. The first and last are teeth of the
  harness self-check;
* GR's audit position (`after_run`, §4.4) is stamped in the same block, so one field in the gate
  record says everything GR did differently from the campaign.

### 8.2 The result

*Caption: gate GR at `b78d96cd`, run with `--lifted-from` pointing at the previous revision's
derived input files. Every compared value is a count or a hex float and **no tolerance is applied to
any of them**. Population: 20 reference runs — 14 optimisations and 6 evaluations over the three
configurations — carrying 15 compared values each for an optimisation and 10 for an evaluation.*

| | |
|---|---|
| **verdict** | **PASS** |
| **runs reproduced** | **20 / 20** |
| **compared values identical** | **270 / 270** (0 mismatched) |
| **record contract** | 20 / 20 records carry every declared field |
| **substitute `A0p`** | PASS — 2 pulsed configurations; 1 configuration skipped with the reason recorded |
| **substitute `AR`** | PASS — 3 configurations × 4 values = 12 compared values, no tolerance |
| **overrides** | `{B1: output_loop=upstream, B3: output_loop=upstream}`, set-equal to the matrix's `none` cells; audit position `after_run`; not available to the campaign |
| **record** | `runs/gates/reproduction/gate.json` |

**Teeth — 7 of 7 tripped**: a count raised by one must not reproduce; one character appended to a
hex objective must not reproduce; a reference file that does not exist must **FAIL, not compare over
an empty set**; a record with a compared field removed must **FAIL, not skip the field**; asking for
this revision's arm name without the name map must **RAISE**; the composition control — `B3` on
`st_regression` run with the analysis-loop switch deliberately wrong — moved **7 of 15** compared
values; and a record whose per-attempt node calls do not sum to the run total is **REFUSED**.

The composition tooth is the positive control that matters: it proves GR is sensitive to *which arm
it ran*, not merely to whether a run succeeded.

---

## 9. Gate G9 — the output path writes the state the solve handed over

### 9.1 The construction

Eleven runs at seed 0: every optimisation-phase arm on every configuration where it is active, each
composed from the experiment's matrix with no override and no allowance, each audited at the
declared position. `B1` is inactive on `st_regression` and is skipped **by the configuration's own
recorded reason** ("steady state (no burn-time coupling): `B1` composes to `B0`"), not by a
condition written into the gate.

On an arm whose matrix cell turns the loop off, four criteria:

* **(i)** the coupling state immediately before the file-writing call is **bit-identical**, component
  by component in hex, to the snapshot taken at the entry to the output path — on every component
  the per-run deferred nodes do not own. Those nodes run between the two snapshots *by design*;
  their write set is derived from the same two committed artifacts the restricted audit derives it
  from, and the components they move are counted and reported separately rather than waved past;
* **(ii)** the output-time loop ran **0** sweeps;
* **(iii)** the objective in PROCESS's own output file is the accepted objective, to the bit;
* and the driver resolved `finalise_once`.

On an arm that keeps the loop, "nothing changes" is a comparison against a record made before this
change, not an assertion: nine fields describing the solve are compared against gate GR's record for
the same arm, configuration and seed. `exit_audit.residual_max_hex` is deliberately **not** among
them — the audit position moved for every arm in this same change, so the residual is expected to
differ, and comparing it would test the audit rather than the output path. Both residuals are
published side by side in the gate record instead.

### 9.2 The result

*Caption: gate G9 at `b78d96cd`. One row per run. "Components" are coupling-state components
compared in hex between the snapshot at the entry to the output path and the snapshot immediately
before the file-writing call, excluding the components the per-run deferred nodes own; "GR fields"
are the nine solve-describing values compared against gate GR's record for the same run. No
tolerance is applied to either. Population: 11 runs at seed 0 = every optimisation-phase arm on
every configuration where it is active; 3 825 components and 54 values in total.*

| arm | configuration | matrix cell | resolved path | sweeps | components differing / compared | GR fields differing / compared | verdict |
|---|---|---|---|---:|---:|---:|---|
| `BR` | `large_tokamak_nof` | upstream | `mda_output` | 2 | — | **0 / 9** | PASS |
| `B0` | `large_tokamak_nof` | upstream | `mda_output` | 2 | — | **0 / 9** | PASS |
| `B1` | `large_tokamak_nof` | none | `finalise_once` | **0** | **0 / 840** | — | PASS |
| `B3` | `large_tokamak_nof` | none | `finalise_once` | **0** | **0 / 716** | — | PASS |
| `BR` | `low_aspect_ratio_DEMO` | upstream | `mda_output` | 2 | — | **0 / 9** | PASS |
| `B0` | `low_aspect_ratio_DEMO` | upstream | `mda_output` | 2 | — | **0 / 9** | PASS |
| `B1` | `low_aspect_ratio_DEMO` | none | `finalise_once` | **0** | **0 / 846** | — | PASS |
| `B3` | `low_aspect_ratio_DEMO` | none | `finalise_once` | **0** | **0 / 721** | — | PASS |
| `BR` | `st_regression` | upstream | `mda_output` | 2 | — | **0 / 9** | PASS |
| `B0` | `st_regression` | upstream | `mda_output` | 2 | — | **0 / 9** | PASS |
| `B3` | `st_regression` | none | `finalise_once` | **0** | **0 / 702** | — | PASS |
| **total** | | | | | **0 / 3 825** | **0 / 54** | **PASS** |

*(`B3`'s component counts are lower than `B1`'s on the same configuration because `B3` defers three
or four nodes to once per run and those nodes' 124–125 written fields are excluded from criterion
(i) by derivation. `B1` defers nothing, so its comparison is over the whole tested state.)*

The accepted objective appears in the output file to the bit on every intervention run:
`0x1.9999999a4496cp+0` on `large_tokamak_nof`, `-0x1.a00c0bc88c2c6p-2` on `low_aspect_ratio_DEMO`,
`-0x1.096acf3342e55p+4` on `st_regression`, identical between `B1` and `B3` where both run. All 49
individual checks across the eleven runs pass.

**Teeth — 4 of 4 tripped.**

| tooth | construction | result |
|---|---|---|
| one component moved by one ULP before `finalise` | one float of a throwaway copy of the entry snapshot nudged by one unit in the last place — `blanket.deg_blkt_inboard_poloidal_plasma`, `0x1.ff303960c3129p+6` → `…12a` | **FAIL**, naming the component: 1 of 840 components differ |
| missing snapshot | one of the two snapshots asked for at a directory that has none | **REFUSED**, not skipped |
| an output-time sweep under the one-call path | a throwaway copy of an intervention run's record with `output_loop_sweeps = 1` | **FAIL** on criterion (ii) — the field the driver stamped; the run itself recorded 0 |
| the written objective moved | the output file's objective nudged by one unit in the last place | **FAIL**: no longer equals the accepted hex |

The first tooth is the one the plan's §3.9 names, and it bites where it must: **between** the
snapshot and `finalise`, on a component outside the per-run write sets, at the smallest amount that
should register.

---

## 10. Three measurements, not gates

All three come from `harness/gates.py`'s `output-path-contrast` and `output-path-measurements`
stages, committed at `b78d96cd` **before** the numbers were taken, and all are published with their
populations. None is an acceptance criterion for anything.

### 10.1 What the output-time loop moves in the output files

*Caption: one row per configuration. The reference arm is run at seed 0 and written out twice — once
through upstream's output-time loop and once through the one-call path — with everything else
identical. This is deliberately **not** a matrix composition: no arm of the experiment writes
upstream's own solve through the one-call path, and holding the solve fixed while varying only the
output path is the only construction that isolates the loop's effect on the numbers a reader of the
output file gets. The solve is held fixed and **checked** to be fixed: "solve identical" is the
accepted objective hex and the solve-phase node count agreeing on the two sides, and a row where
they did not agree would not be a statement about the output path at all. Lines differing are lines
of PROCESS's own output file, with the same metadata keys excluded that gate G1 excludes (date,
time, user, paths, version strings and PROCESS's own timing of itself). Counts, never timings.
Population: 6 runs = the reference arm at seed 0 on each of the 3 configurations, twice.*

| configuration | solve identical | accepted objective (hex) | solve-phase node calls | total node calls, loop on / off | sweeps, on / off | output-file lines differing / compared |
|---|---|---|---:|---:|---:|---:|
| `large_tokamak_nof` | yes | `0x1.99999999b822dp+0` | 42 567 | 42 609 / 42 567 | 2 / 0 | **11** / 16 173 |
| `low_aspect_ratio_DEMO` | yes | `-0x1.a00c1e7544537p-2` | 89 964 | 90 006 / 89 964 | 2 / 0 | **0** / 16 434 |
| `st_regression` | yes | `-0x1.096acf3342eefp+4` | 39 669 | 39 711 / 39 669 | 2 / 0 | **10** / 18 691 |

**What differs, by name.** On `large_tokamak_nof`: the cost of electricity, low-voltage equipment
cost, total account 24, plant direct cost, indirect cost, total contingency, constructed cost,
interest during construction, total capital investment, and the CS coil midplane axial stress at
time points 2 and 3. On `st_regression`: low-voltage equipment cost, the ratio of fast alpha and
beam beta to thermal beta, three volume-averaged betas, the normalised thermal beta, the plasma
thermal energy, the proton number density, the Wilson bootstrap fraction, and the fusion gain
factor. Every difference is in the last digits.

**Read with the condition that limits it, and it is a strong condition.** The effect is real, it is
small, and **on one of the three configurations it is exactly zero**. Three configurations at one
seed each is three case studies, not a rate: nothing here supports "the loop always moves the
answer" or "the loop never moves it". What it does support is the narrow claim the intervention arms
make — under the incumbent's output path, the numbers in the output files are **not necessarily**
the numbers at the point the optimiser accepted, and under the one-call path they are, by
construction and by gate G9.

### 10.2 What the output-time loop costs

*Caption: one row per optimisation run of gate GR. "Sweeps" is how many times upstream's output-time
loop evaluated the whole model set before writing the output files, read from the driver's own
counter; "entries" is how many times the output path was entered (one per scan point — these
configurations are single problems). "After the solve" is model node calls made after the
solve-phase counter was frozen: the per-run deferred nodes where an arm has them, plus the
output-time loop's own sweeps. Counts, never timings. Population: all 14 optimisation runs of gate
GR's reference set — the only run set in which every arm executes the loop, the two whose matrix
cell turns it off doing so under the gate's recorded override (§8.1).*

| arm | configuration | seed | path | sweeps | entries | solve-phase node calls | node calls after the solve |
|---|---|---:|---|---:|---:|---:|---:|
| `BR` | `large_tokamak_nof` | 0 | `mda_output` | 2 | 1 | 42 567 | 42 |
| `BR` | `low_aspect_ratio_DEMO` | 0 | `mda_output` | 2 | 1 | 89 964 | 42 |
| `BR` | `st_regression` | 0 | `mda_output` | 2 | 1 | 39 669 | 42 |
| `B0` | `large_tokamak_nof` | 0 | `mda_output` | 2 | 1 | 43 449 | 42 |
| `B0` | `low_aspect_ratio_DEMO` | 0 | `mda_output` | 2 | 1 | 86 877 | 42 |
| `B0` | `st_regression` | 0 | `mda_output` | 2 | 1 | 42 756 | 42 |
| `B3` | `large_tokamak_nof` | 0 | `mda_output` | 2 | 1 | 28 055 | 45 |
| `B3` | `low_aspect_ratio_DEMO` | 0 | `mda_output` | 2 | 1 | 45 496 | 45 |
| `B3` | `st_regression` | 0 | `mda_output` | **3** | 1 | 23 505 | **67** |
| `B3` | `large_tokamak_nof` | 1 | `mda_output` | 2 | 1 | 28 037 | 45 |
| `B3` | `low_aspect_ratio_DEMO` | 1 | `mda_output` | 2 | 1 | 52 834 | 45 |
| `B3` | `st_regression` | 1 | `mda_output` | 2 | 1 | 134 560 | 46 |
| `B1` | `large_tokamak_nof` | 1 | `mda_output` | 2 | 1 | 44 100 | 42 |
| `B1` | `low_aspect_ratio_DEMO` | 1 | `mda_output` | 2 | 1 | 81 228 | 42 |

**Two is the floor, not a measurement of effort.** The loop cannot stop at one sweep: it needs two
output files to compare. So the 13 rows reading 2 are at the minimum the construction allows, and
they say the state settled immediately — not that convergence took work. **The informative row is
the one that is not at the floor**: `B3` on `st_regression` at seed 0 took **3**, meaning the state
that arm handed over was not output-idempotent after two flat passes. That is the event the plan's
§3.3 asks to be looked for on purpose, and it appears in 1 of these 14 runs.

**In node calls it is small and it is not zero.** 42 node calls on a reference arm's output path
against 39 669–89 964 in the solve phase — under 0.11 % on every row. That is the honest scale of
what removing the loop saves in *model evaluations*. What removing it buys is not cost; it is
§10.1.

### 10.3 Where the accepted state sits against τ, at the declared position

*Caption: one row per run of gate G9 on an arm whose matrix cell turns the output-time loop off. The
exit audit is one further sweep of the whole model set from the state the solve handed over, and the
columns count how many coupling-state components moved by at least τ under it. **Whole state**
counts every tested component; **restricted** excludes the components the per-run deferrable nodes
write, derived from the committed per-run artifact and the committed run-time write census, one set
per configuration so every arm of it is on the same ruler. The two differ because the audit sweep
runs those nodes and the handed-over state is from before they ran, so their own outputs move by
construction — which is why the whole-state *maximum* is not published at all on an arm that defers:
there it is a per-run node's own output and says nothing about convergence. Population: 5 runs at
seed 0 = the arms whose matrix cell turns the loop off, on every configuration where they are
active, from gate G9's own runs; τ = 1e-6 throughout.*

| arm | configuration | tested | above τ, whole state | tested, restricted | above τ, restricted | restricted max | restricted argmax |
|---|---|---:|---:|---:|---:|---:|---|
| `B1` | `large_tokamak_nof` | 818 | 1 | 696 | **1** | 7.12e-3 | `tfcoil.insstrain` |
| `B3` | `large_tokamak_nof` | 818 | 113 | 696 | **1** | 7.12e-3 | `tfcoil.insstrain` |
| `B1` | `low_aspect_ratio_DEMO` | 824 | 1 | 701 | **1** | 7.02e-3 | `tfcoil.insstrain` |
| `B3` | `low_aspect_ratio_DEMO` | 824 | 113 | 701 | **1** | 7.02e-3 | `tfcoil.insstrain` |
| `B3` | `st_regression` | 805 | 112 | 682 | **0** | 1.60e-11 | `fwbs.p_cp_shield_nuclear_heat_mw` |

The excluded set, per configuration, derived and not listed: `large_tokamak_nof` — per-run nodes
`vacuum`, `water_use`, `costs`, 124 fields; `low_aspect_ratio_DEMO` — the same three nodes, 125
fields; `st_regression` — `pulse`, `vacuum`, `water_use`, `costs`, 125 fields.

**Three things this says, each with its qualifier.**

* **The 113 / 112 column is the deferral, not non-convergence.** `B1` defers nothing and shows 1
  above τ whole-state; `B3` on the same configuration and seed shows 113. The 112 extra are per-run
  nodes' own outputs measured from before those nodes ran. The restricted column, which excludes
  exactly them, reads 1 on both — identical between the arms, which is what "the same ruler" is
  supposed to produce, and is the first evidence that the restricted statistic survives the move of
  the audit position.
* **One component sits above τ on the pulsed configurations, in both arms, at ~7e-3 scaled.** It is
  `tfcoil.insstrain` both times. That is the plan's "looked for on purpose" signal, and it is
  specific enough to hand on: not a diffuse failure to converge, one named component. **This report
  does not diagnose it** — that is not this task's scope, and nothing here says whether it is a
  genuine unconverged coupling, a discontinuity, or a component whose measured scale is too small.
  It is filed for A52 (harness-gates) and A53 (harness-tally) in §13.
* **`st_regression` has nothing above τ at all**, restricted maximum 1.6e-11 — five orders of
  magnitude below τ. The partitioned arm's handover on that configuration is, at this seed,
  extremely tight.

**One seed each.** Every row is seed 0. Five runs is not a distribution and none is claimed; these
are the runs gate G9 makes, published because the plan asks for the quantity and because a number
nobody has looked at is not evidence of anything.

---

## 11. Timing, and what it is not

The whole gate chain of §14 — 6 + 20 + 11 + 6 PROCESS runs plus the checks — completes in about
twenty minutes at three workers on this machine. That sentence is the only timing in this report and
nothing rests on it. Per trap T5 this machine cannot resolve the effects the plans gate on: 16 cores
but 7 GB of RAM, no thread pinning, concurrent sessions, and a worst within-arm spread of 19.6 %
measured against gates set at 10–25 %. Every acceptance quantity above is a count or a bit
comparison, and each reproduced exactly across the three separate full runs of the chain made during
this task.

---

## 12. Autonomous decisions, each with the way back

*Caption: one row per decision taken without asking. "Reversal" is what undoing it costs and what
would have to be re-run.*

| # | decision | why | reversal |
|---|---|---|---|
| 1 | The snapshot is a **callable hook the harness installs**, not a driver-side serialiser writing a side file | the shape of a snapshot is defined by a committed artifact and `harness/predicate.py`; putting it in the copy would be a second copy of a shared definition, which D14(c) exists to prevent and which the driver already refuses to do for the predicate module | move `predicate.snapshot_record` into the copy and have the driver write a file. Costs the duplicated definition, and G1 would then have to exclude a new driver-side write |
| 2 | **Two** snapshot positions, not one: `before_finalise` as well as the entry | it turns G9's criterion (i) from an argument about code structure into a bit comparison between two states | delete the three `before_finalise` call sites; criterion (i) becomes "no sweep ran, therefore nothing changed", which is an assertion |
| 3 | The entry snapshot is taken at the **literal** entry — before the per-run deferred nodes | that is the plan's words, and the only reading under which "the state the solve handed over" is true | move the call after the per-run sweep. The whole-state count would stop charging the per-run nodes' movement, but the audit would no longer measure what the *solve* produced, and the evaluation-phase arms (which have no output path) would be measuring a different thing from the optimisation-phase ones. Consequences of the choice as made are in §4.3 and in every caption |
| 4 | G1's two captures are **pinned to one audit position on both sides**, and a pair that disagrees refuses | it keeps the whole `exit_audit` block inside G1's comparison instead of excluded | let each side audit at its own revision's position and add `exit_audit` to G1's exclusions. Costs the strongest thing G1 compares |
| 5 | Gate GR composes `output_loop = upstream` **explicitly** rather than leaving the variable unset | an override the driver reads back can be checked; one relying on a default cannot be told from having forgotten to set anything | drop the term from the override map and rely on the default. The set-equality guard would then have nothing to check and the run record would not say what the gate did |
| 6 | GR audits at `after_run`, recorded in the same override block | its compared values include a residual the previous revision measured there | compute **both** audits on every GR run and compare only the after-run one. Costs one extra uncharged sweep per run and a second residual field on every record |
| 7 | The restricted residual statistic for the optimisation phase is computed by the **measurement stage**, not added to the run record | adding it to the record would change every "after" record and force a G1 re-run with one more exclusion, for a field whose home is gate G4 — A52's | pass `--per-run-artifact` / `--node-write-sets` to `optimise.py` (`pool._command` already builds them for the evaluation phase) and re-run G1 with `exit_audit.restricted` excluded. Handed over in §13 |
| 8 | `records.FORMAT` and `harness.__version__` are **not** bumped | the schema change is additive and self-describing: `audit_position`, and the presence or absence of `output_loop_null_because`, tell a pre- from a post-A57 record. Bumping either would add two more G1 exclusions for no information | bump both and re-run G1 with two more named exclusions |
| 9 | `optimise.py`, `evaluate.py` and `pool.py` were edited although the task's owned-file list does not name them | the audit lives in `optimise.py` and the job description in `pool.py`; the deliverable is unreachable without them, and neither file is A51 (harness-artifacts)'s. **`experiment_runner.py` was not touched**, per the brief, and the new stages have their own `__main__` CLI | revert; there is then no way to move the audit position or to record an override |
| 10 | The self-check's two "allowance" teeth were **re-pointed** at the predicate trial's still-pending switch rather than deleted, and three new checks/teeth added on the reproduction override | the allowance mechanism still exists and still needs a tooth; with `output_loop` implemented, the only switch that can exercise it is the one A59 will land | none needed. When A59 lands, the teeth have nothing to bite on and the check says so in a note rather than passing silently |
| 11 | The composition self-check now compares only over roles **both** revisions can express, with the set-aside roles named, valued and counted, and the set **measured** from the previous revision's own composer rather than listed | with `output_loop` implemented, `B1`/`B3` ask for a role the previous revision had no switch for; comparing it against a side that could not express it reports a capability as a disagreement. A hand-written exception list would have become a place to hide a real difference | delete `switches.previous_revision_roles()` and compare over the union again. Every intervention arm then fails the check on a role that is not a disagreement |
| 12 | `tree_untracked_paths_n` and `tree_modified_tracked_n` added to G1's exclusion set | the lists were excluded and their counts were not, so a scratch file failed a byte-identity gate — §7.4 | remove them; G1 then fails whenever any untracked file exists in the tree while the second capture runs |

---

## 13. Handover

**To A52 (harness-gates).**

* **G9 is built and registered.** It is `gates.registry(campaign)["output_path"]` with four teeth,
  and it runs in two steps (`--capture runs`, then the comparison), the way G1 does. It needs
  wiring into `experiment_runner.py --gate output_path`, along with `g0prime` and
  `switch_neutrality`, which the A52 queue row already asks for.
* **G4 should also give the optimisation record its restricted audit statistic.** `optimise.py`
  does not pass `--per-run-artifact` / `--node-write-sets` to `child.take_exit_audit`, so
  `exit_audit.restricted` is null on every optimisation record; `pool._command` already builds both
  arguments for the evaluation phase. Adding them is three lines. **It will change every "after"
  record**, so G1 must be re-run at that commit with one more named exclusion
  (`exit_audit.restricted`, null before, populated after). That is written down here so it is not a
  surprise. Until then, §10.3's construction — the measurement stage, from the committed residual
  vector — is where the number comes from, and it is the same derivation.
* **G1's exclusion set is now 33 names.** Eight are this task's, listed in §7.3 with their leaf
  counts, of which two are the defect §7.4 exposed. A52 inherits the set to review, not extend.
* **`tfcoil.insstrain` is above τ at the accepted point on both pulsed configurations, in both
  intervention arms, at ~7e-3 scaled** (§10.3). Whatever G4 and the tally do with the restricted
  statistic, this component will dominate it on those configurations. It is worth deciding
  deliberately whether it is a convergence finding, a scale artefact, or a discontinuity, rather
  than discovering it in a campaign table.

**To A58 (driver-predicate-counters).** The predicate counters belong beside `OUTPUT_LOOP_SWEEPS`
in `caller.py` and follow exactly the pattern this task used: an integer counter at module level, a
readback in `switches.REGISTRY`, and the removal of the three lines in
`child.stamp_capabilities_absent` that currently write `predicate_evaluations` and
`components_compared` as nulls with the reason. This task removed the output-path equivalents there;
the shape is identical, and so is the G1 consequence (one named exclusion per field whose null
becomes a number).

**To A59 (driver-predicate-mode).** `predicate_mode` is now the **only** entry in
`switches.REGISTRY` with `driver_name = None`. Two consequences are already coded: the self-check's
two allowance teeth bite on it (they were re-pointed there when `output_loop` resolved) and will
report that they have nothing to bite on when it lands; and `switches.previous_revision_roles()`
already sets it aside as a capability the previous revision could not express, so the composition
check needs no edit.

**To A60 (driver-attempts).** Unchanged by this task: `attempts_node_calls_available` is still
`false` on every record and `records.assert_attempt_summation` is still the tooth that refuses a
decomposition which does not add up. GR exercises it.

**To A53 (harness-tally).** Three new record fields to read: `output_path`, `output_loop_sweeps`
(non-null from now on, `0` under the one-call path) and `output_path_entries`. The plan's §3.5 rule
that "the output-time and audit sweeps are excluded symmetrically and every caption that uses the
per-node census says so" now has a measured number behind it — §10.2's "node calls after the solve"
column. And **`audit_position` is `entry_to_write_output_files` on every campaign record**: any
table of residuals should say so in its caption, and any table mixing them with the reproduction
gate's records must not, because those are at `after_run`.

**To the orchestrator, at merge — two sentences in the experiment plan are now stale.** Neither was
edited here, because that document is shared; the exact replacements are:

* `MDA_partitioning_experiment_v4/EXPERIMENT_PLAN.md` §3.2, last line of the switch list — *"Pending,
  refused until their driver change lands: `PROCESS_ARCH_OUTPUT_LOOP = none` (A57) and
  `PROCESS_ARCH_PREDICATE = frozen | mixed` (A59)."* → *"`PROCESS_ARCH_OUTPUT_LOOP = upstream |
  none` landed with A57 (driver-output-path), 2026-09-10. Pending, refused until its driver change
  lands: `PROCESS_ARCH_PREDICATE = frozen | mixed` (A59)."*
* §3.3, the last sentence of the `MDA_Output` paragraph — *"The snapshot hook is a driver change in
  the copy and lands with A57 (driver-output-path); until then every record carries both
  `audit_position` … and `audit_position_declared`."* → *"The snapshot hook landed with
  A57 (driver-output-path), 2026-09-10: every campaign record carries `audit_position ==
  audit_position_declared == entry_to_write_output_files`, and the after-the-run position survives
  for the reproduction gate alone, whose compared values include a residual the previous revision
  measured there."*

**Run artifacts (I-14).** Everything this report cites lives under
`arch_surgery/MDA_partitioning_experiment_v4/runs/gates/` — `switch_neutrality/{before,after}`,
`reproduction/`, `output_path/` (with `contrast/` and `measurements.json` inside it), and
`g0prime/` — and is untracked by design. **Relocate it before retiring the worktree**;
`bin/retire_task_worktree.sh` is what does that, and a bare `git worktree remove` destroys it (I-14
cost this project the evidence behind a headline correction). The `before` capture of gate G1 is the
one artifact that **cannot be regenerated**: it was made at the branch point, before any edit.

---

## 14. How to re-run everything in this report

Every number above comes from one of these commands, run from
`arch_surgery/MDA_partitioning_experiment_v4/` with
`/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python`. §2's table names the commit each was
run at. The "before" capture of gate G1 is the one exception and cannot be re-taken: it was made at
the branch point `22bb8656`, before any edit, which is what makes it a *before*.

```
# the copy: is it its source commit plus exactly its recorded edits, and is the physics frozen?
python PROCESS/copy_gates.py all                      # §5
python PROCESS_diff.py --markdown                     # §5 (exit 0, 0 unexplained)

# G0' through the harness gate framework
python -m harness.gates g0prime                       # §6

# G1: the 'before' capture was taken at 22bb8656 BEFORE any edit; only the rest is repeatable
python -m harness.gates switch-neutrality --capture after
python -m harness.gates switch-neutrality --compare    # §7

# GR: does the rewritten harness still reproduce the previous revision, after DR2?
python experiment_runner.py --gate reproduction \
    --lifted-from /home/wrutten/projects/PROCESS_surgery/arch_surgery/MDA_partitioning_experiment_v3/runs/_decks   # §8

# G9: 11 runs, then the comparison
python -m harness.gates output-path --capture runs
python -m harness.gates output-path                    # §9

# the contrast: the reference arm down each output path, 6 runs
python -m harness.gates output-path-contrast --capture runs

# the three measurements (needs GR's, G9's and the contrast's runs to exist)
python -m harness.gates output-path-measurements       # §10

# the harness's own declarations against the tree it runs
python experiment_runner.py --selfcheck                # §2
```

`--gate reproduction` and G9's capture both need the derived (lifted) input files; GR stages them
from `--lifted-from`, and G9 refuses at its front door, by name, if they are not there.

---

## 15. Change log

*Append-only.*

| date | what |
|---|---|
| 2026-09-10 | Gate G1's **"before" capture** taken at the branch point `22bb8656`, with the copy's driver verified byte-identical to that commit first. 6 runs, all `status: ok`. It cannot be re-taken. |
| 2026-09-10 | **`234e0462`** — DR2 in the copy: `PROCESS_ARCH_OUTPUT_LOOP = upstream \| none`, `OUTPUT_LOOP_SWEEPS` and `OUTPUT_PATH_ENTRIES`, the two readbacks, the typed refusal on an illegal value, and the exit-audit snapshot hook at two named positions. The per-run deferred nodes keep their position exactly. |
| 2026-09-10 | **`9f94fa28`** — the copy's provenance and diff view follow: two `PermittedEdit` rows, `PROVENANCE.json` regenerated, two mechanism labels and nine annotation rows in `PROCESS_diff.py`, `caller.py`'s summary paragraph extended. |
| 2026-09-10 | **`59288aad`** — the harness follows: the switch resolves and nothing is pending on a run path; the audit moves to the declared position via the snapshot, with a bit-exact restore that refuses rather than mislead; `records.py` gains three output-path fields, `audit_snapshot` and `reproduction_overrides`; the reproduction gate's pending allowance becomes a matrix-derived, set-equality-guarded override; G1 pins its audit position and gains six named exclusions and a fourth tooth; **G9 is added** with four teeth; the composition self-check compares only over roles both revisions can express and gains three teeth. Self-check 6/6, 43 teeth. |
| 2026-09-10 | **`e62d3c05`** — the `output-path-measurements` stage: what the output-time loop costs, and where the accepted state sits against τ, with the restricted count derived from the committed artifacts and published beside the whole-state one. |
| 2026-09-10 | **`b78d96cd`** — the `output-path-contrast` stage: the reference arm written out down each output path, so that "what the loop moves" comes from a committed stage rather than the shell invocation it was first measured by. Gates **GR** and **G9** and the three measurements were taken at this commit. |
| 2026-09-10 | **Gate G1 FAILED** at `b78d96cd`: 6 of 2 371 values, one per pair, all `tree_untracked_paths_n` moving 0 → 1 because the tree held this task's own draft report. 0 of 51 319 output-file lines; no tracked file modified on either side. §7.4. |
| 2026-09-10 | **`29beeeae`** — the defect G1's failure exposed, fixed: its exclusion set excluded `tree_modified_tracked` and `tree_untracked_paths` but not their `_n` counts, so a scratch file failed a byte-identity gate on a field that cannot change what the driver does. Both counts excluded, with the reason. |
| 2026-09-10 | **G1 re-run at `29beeeae`: PASS** — 0 of 2 359 values, 0 of 51 319 lines, 6 pairs, 4 teeth. G0′, the copy gates, `PROCESS_diff.py` and the self-check re-run at the same commit and all PASS. |

---

## 16. Orchestrator's critical assessment (protocol §5) — 2026-09-10

*Appended by the orchestrating session before merge, against the report at `12c80f64` and the copy
and harness on the same branch. Every gate was re-run by the orchestrator, not read off the report.*

**Verified independently.** (1) **Gate GR after DR2**, re-run from scratch (the gate regenerated
the branch's reproduction records in place): 20 of 20 runs, **270 of 270 values identical**,
contract 20 of 20, both substitutes PASS, seven teeth tripped, with the recorded
`output_loop = upstream` override on `B1`/`B3` derived from the matrix and set-equality guarded.
(2) **G9** (`gates.py output-path`) compared against those fresh records: PASS on 11 runs — **0 of
3 825** coupling-state components differ in hex between the snapshot and the written state, **0 of
54** solve-describing values differ from GR's records, the loop ran 2 sweeps under `upstream` and 0
under `none` on every run; four teeth tripped, the one-ULP perturbation between snapshot and
`finalise` among them. (3) **G1** (`switch-neutrality --compare`): 6 pairs, 0 of 2 359 values, 0 of
51 319 output-file lines, four teeth including the new refusal of captures audited at different
positions. (4) **G0′** PASS; `PROCESS/copy_gates.py all` ALL GATES PASS; `PROCESS_diff.py` exit 0
over 68 hunks, 0 unexplained; `--selfcheck` six checks PASS with the pending list now empty. (5)
Scope: fifteen files — the copy's `caller.py` alone among driver files, its provenance and diff
tooling, the harness files the brief assigned plus `optimise.py`, `evaluate.py` and `pool.py` (the
audit lives in the first, the job description in the third — unavoidable and stated), the README's
registry section and this report; `models/`, the repository-root `process/` and
`experiment_runner.py` untouched. Against trunk, which took A51 (harness-artifacts) meanwhile, the
two files both sides changed (`pool.py`, the README) merge without conflict.

**Endorsed.** The snapshot hook as a callable slot the measurement installs, so the copy holds the
*position* and never a second definition of the coupling state (D14(c)); the restore proven bit-exact
before the audit is taken, and a restore that is not bit-exact refusing the audit rather than
reporting a residual of a state nobody chose. Two snapshot positions, so G9's first criterion is a
comparison and not an argument from code structure. GR's allowance replaced by an override derived
from the matrix cell rather than listed, refused for the campaign, and stamped with GR's audit
position in one block. **G1's failure reported in full** — six values differing, all the untracked
count moved by the task's own draft report — and the defect located in the gate's own exclusion set
(the `_n` counts of the two provenance fields were not excluded while the fields were), fixed, and
re-run; not committing the report first, which would have made it pass, is exactly the discipline
the protocol asks for. The sweep-count and above-τ measurements produced by committed stages, with
both whole-state and restricted constructions side by side and the reason the two differ stated in
the caption.

**Limits I hold it to.** (a) GR's optimisation runs audit at `after_run`, where the previous
revision measured, and only GR may ask for it; every campaign record audits at the declared entry.
The two positions must never appear in one table without saying so — A53 carries that as a caption
rule. (b) `exit_audit.restricted` is null on optimisation records until A52 passes the two
artifacts to the audit; §10.3's restricted numbers come from the committed residual vectors by the
same derivation, so nothing is lost, but the field is not yet in the record. (c) One seed each in
§10.3; five runs are not a distribution and none is claimed. (d) The runner's `--outdir` does not
redirect `--gate reproduction`, which writes to the campaign's records directory — harmless, and
worth one line in A52's wiring of the gates.

**The finding that matters for the experiment.** At the accepted point on both pulsed
configurations, in both arms whose burn time the optimiser owns, exactly one coupling-state
component sits above τ on the restricted ruler: **`tfcoil.insstrain`, at 7.1e-3 and 7.0e-3
scaled**, identical between `B1` and `B3` on the same seed; `st_regression` has nothing above τ
(restricted maximum 1.6e-11). This is the signal the plan said to look for on purpose. It is
**not diagnosed here** and I do not pretend to know its cause — a genuinely unconverged coupling, a
component whose measured scale is too small, or a discontinuity in the model are all open. It goes
on the improvement list as an item for the user, and A52's G4 and A53's tally will make it visible
rather than average it away.

**Rulings and consequences drawn (orchestrator, today).** The two stale plan sentences (§13) are
replaced at the merge with the text proposed here. A52 (harness-gates) wires `g0prime`,
`switch_neutrality` and `output_path` into the runner, passes the per-run artifact and the node
write sets to the optimisation-phase audit so `exit_audit.restricted` is populated (and re-runs G1
with that one named exclusion), and inherits G1's 33-name exclusion set to review. A53
(harness-tally) reads `output_path`, `output_loop_sweeps`, `output_path_entries`, and states the
audit position in every residual caption. A58 (driver-predicate-counters) follows the
`OUTPUT_LOOP_SWEEPS` pattern and removes the corresponding nulls from
`child.stamp_capabilities_absent`. The `--outdir` note goes to A52.

**Verdict.** Fit to merge; nothing returned. DR2 lands with its neutrality, its own gate and the
reproduction gate all passing, and the exit audit now measures what the plan said it should.
