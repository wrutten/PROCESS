# A56 (driver-renames) — the V4 driver's switches take their intended names

> **Document status** — **OPEN.** Task report for `A56 (driver-renames)`, branch
> `A56-driver-renames`, worktree
> `/home/wrutten/projects/PROCESS_surgery_worktrees/A56-driver-renames`, off
> `architecture_surgery` at `f1f90c20`. Every number below was produced by a committed script in
> this branch and the section that quotes it names the script and the commit it ran at. Nothing
> here is a timing.

---

## 1. Verdict

The experiment's own copy of PROCESS now reads the switch names the plan settled on. Three
switches disappeared in the process: the one that chose how many times the block schedule runs, the
second convergence tolerance, and one half of the pair that said what happens to the burn time.
Setting any of the eleven names this leaves behind **raises**, in the driver and in the harness
both.

Three gates say what that cost:

| gate | what it asks | verdict | the numbers |
|---|---|---|---|
| **G0′** | the physics did not move | **PASS** | 77 model files compared against `c0ae5b28`, 76 byte-identical, `pulse.py` alone differing under its approval; 4 teeth tripped |
| **G1** | with every architecture switch unset, the copy after the change behaves byte-identically to the copy before it | **PASS** | 6 run pairs; **2 383** deterministic record values and **51 319** output-file lines compared without tolerance, **0** differing; 3 teeth tripped |
| **GR** | the twenty reference runs still reproduce the previous revision | **PASS** | **20/20** runs, **270/270** compared values, no tolerance; both substitutes PASS; 7 teeth tripped |

**GR is the load-bearing one.** G1 only says that a run with *no* switches set is unchanged — which
is most of the code but none of the arms. GR runs the partitioned arms (`A1`, `B3`) and the flat
ones (`A0`, `B0`, `B1`) against the numbers the previous revision recorded, and reproduces them to
every compared digit. That is what makes the claim "the rename is a rename, and folding the
schedule switch into the partitioned value changed no arm's behaviour" a measurement rather than an
assertion.

*Caption: one row per gate this task ran. "The numbers" states the population each verdict is over.
Every gate's record is under `arch_surgery/MDA_partitioning_experiment_v4/runs/gates/`, which is
untracked by design; the numbers are reproduced in §§6–8 below.*

---

## 2. The words, spelled out once

- **The driver** is the part of PROCESS that decides *when* each model runs and *what stops* the
  loop that runs them. This experiment changes only the driver; every physics and engineering model
  is frozen at the base commit `c0ae5b28`.
- **An architecture switch** is an environment variable, read once when PROCESS is imported, that
  selects one driver behaviour. `PROCESS_ARCH_MDA=partitioned` is one.
- **An arm** is one complete setting of those switches — one column of the experiment's matrix.
  `B3` is the partitioned arm of the optimisation phase.
- **The copy.** V4 runs its own copy of the PROCESS package at
  `arch_surgery/MDA_partitioning_experiment_v4/PROCESS/process/`, taken at commit `f2dc9243`. The
  repository-root `process/` belongs to the previous revision and is not touched.
- **A gate** is a check that must pass before a number is believed. Its **teeth** are deliberate
  breaks it must catch: a check that has never been shown to fail is an assertion, not a
  measurement.
- **The decisions referred to by number.** **D5** freezes the models. **D20** gives V4 its own copy
  of PROCESS and removes any obligation to stay compatible with the previous revision. **D22**
  removed the arm that repeated the block schedule. **D23** fixes one convergence tolerance for
  every loop in every arm. **D24** delegates the driver changes: they merge on their own gates,
  without a per-change approval, and the physics freeze is unchanged.
- **The previous revision** is the V3 harness and the V3 campaign, whose records the reproduction
  gate compares against. It is not a different program; it is this experiment one version back.

---

## 3. Every switch, before and after

*Caption: one row per architecture switch the copy understands. "Read at" is the file and line in
the copy where the environment is consulted, at commit `6ac91bf4`. "Readback" is the module-level
name a measurement harness reads to find out what the driver actually resolved — the difference
between "the tree did what I asked" and "the tree ignored me". "Retired" names the variable a caller
might still be setting; **setting one of those raises**. Population: all thirteen switches in
`harness/switches.py`'s registry, plus the two no tree implements yet.*

| term | name now | was | legal values | read at | readback | retired |
|---|---|---|---|---|---|---|
| analysis loop | `PROCESS_ARCH_MDA` | `…_MODULE_SOLVE` | `flat`, `partitioned`; unset ⇒ upstream's own loop | `module_solve.py:163` | `module_solve.MDA_MODE`, `.ENABLED`, `.FLAT` | `…_MODULE_SOLVE`, `…_OUTER` |
| tolerance | `PROCESS_ARCH_TAU` | unchanged | a number, default `1e-6` | `module_solve.py:194` | `module_solve.TAU` | `…_INNER_TAU` |
| coupling state | `PROCESS_ARCH_COUPLING_STATE` | `…_YSTATE` | a path to a committed artifact | `module_solve.py:198` | `module_solve.COUPLING_STATE_PATH` | `…_YSTATE` |
| write sets | `PROCESS_ARCH_WRITE_SETS` | `…_WRITESET` | a path to a committed artifact | `module_solve.py:203` | `module_solve.WRITE_SETS_PATH` | `…_WRITESET` |
| arrangement · node | `PROCESS_ARCH_ARRANGEMENT_NODE` | `…_SEQUENCE` | `build_after_physics`; unset ⇒ `upstream` | `caller.py:59` | `caller.ARRANGEMENT_NODE_NAME`, `.ARRANGEMENT_NODE_HEAD` | `…_SEQUENCE` |
| arrangement · method | `PROCESS_ARCH_ARRANGEMENT_METHOD` | `…_PRIME` | `fw_geometry`; unset ⇒ `off` | `caller.py:109` | `caller.ARRANGEMENT_METHOD_NAME`, `.ARRANGEMENT_METHOD_FW_GEOMETRY` | `…_PRIME` |
| deferral `per_call` | `PROCESS_ARCH_DEFER_PER_CALL` | `…_HOIST` | `feedforward`, `feedforward_lifted`; unset ⇒ `off` | `caller.py:187` | `caller.DEFER_PER_CALL_NAME`, `.DEFER_PER_CALL_ENABLED`, `.DEFER_PER_CALL_NODES` | `…_HOIST` |
| deferral `per_run` | `PROCESS_ARCH_DEFER_PER_RUN` | `…_POST_SOLVE` | a path to a committed artifact | `caller.py:510` | `caller.DEFER_PER_RUN_PATH`, `.DEFER_PER_RUN_ENABLED` | `…_POST_SOLVE` |
| burn-time owner | `PROCESS_ARCH_BURN_TIME_OWNER` | `…_LIFT` **and** `…_PIN_BURN_TIME` | `loop` (the default), `optimiser`, `constant:<hex float>` | `subsolve.py:110` | `subsolve.BURN_TIME_OWNER`, `.BURN_TIME_CONSTANT`, `.BURN_TIME_OUT_OF_LOOP`, `.SITES` | `…_LIFT`, `…_PIN_BURN_TIME` |
| pass trace | `PROCESS_ARCH_PASS_TRACE` | unchanged | a path | `module_solve.py:228` | `module_solve.PASS_TRACE_PATH`, `.TRACE_ENABLED` | — |
| pass trace detail | `PROCESS_ARCH_PASS_TRACE_FULL_FROM` | unchanged | a number, default `2` | `module_solve.py:247` | `module_solve.TRACE_FULL_FROM` | — |
| output-time loop | `PROCESS_ARCH_OUTPUT_LOOP` | — | `none` | *no tree implements it* | `caller.OUTPUT_LOOP_NAME` | — |
| predicate mode | `PROCESS_ARCH_PREDICATE` | — | `mixed` | *no tree implements it* | `module_solve.PREDICATE_MODE` | — |

**Where the value vocabulary comes from.** §11.2 of the harness plan names values for exactly two
switches: `flat | partitioned` for the analysis loop and `loop | constant:<hex> | optimiser` for the
burn time's owner. Both are implemented as written. **Every other switch keeps the values the driver
already used** — `build_after_physics`, `fw_geometry`, `feedforward`, `feedforward_lifted` — because
the terminology table names no replacements for them and inventing some would be a change nobody
asked for. `feedforward_lifted` is the one that reads oddly against the new vocabulary: "lifted" is
the mechanism's own word for taking a quantity out of the loop, and it survives here as a value name
and in docstrings, exactly as §11.2 permits ("*'lift' and 'pin' survive only as the mechanism names
in docstrings*").

**The two rows with no tree behind them.** `PROCESS_ARCH_OUTPUT_LOOP` and `PROCESS_ARCH_PREDICATE`
are declared by arms `B1` and `B3` and by the predicate trial, and **no tree implements either**.
Every arm that asks for one is refused rather than run without it — a run made without a switch its
arm declares is a successful run of a *different* arm under the right name. They arrive with
**A57 (driver-output-path)** and **A59 (driver-predicate-mode)**.

---

## 4. The three switches that disappeared

### 4.1 `PROCESS_ARCH_OUTER` — folded into the partitioned loop

**What it did.** The block schedule visits M1, M2, `PULSE`, M3 and the feed-forward tail in order,
each iterated block solved to its own fixed point. `PROCESS_ARCH_OUTER` chose what happened next:
`verify` (the driver's default) compared the whole coupling state across the pass and repeated the
entire schedule if anything had moved; `trust` stopped there.

**Why it is gone.** Task A43 (st-trust-gap) measured the verification pass across the previous
revision's records: over **91 888 evaluations** of that arm it triggered a further pass **zero
times**. The user removed the arm that used the verified schedule (D22) and fixed one tolerance for
every converger (D23). What remained was a switch with one reachable value and a default no arm
wanted — and a default that was actively dangerous, because A50 (harness-run)'s composition tooth
measured that clearing it made the driver resolve `OUTER_MODE = "verify"` and run the wrong
schedule under `B3`'s name.

**What was done: removed, not made unreachable.** The code that could repeat the schedule is gone
from `Caller._call_models_partitioned` (renamed from `_call_models_by_module`):

- the `for outer in range(1, OUTER_CAP + 1)` loop, replaced by the schedule body running once;
- the joint residual evaluation that decided whether to repeat it (`res = spec.residual(y_outer_prev,
  y)`), the `y_outer_prev` snapshot it compared against, and the `outer_trace` it appended to;
- that evaluation's diagnostic trace hook (`module_solve.trace_pass("outer", …)`);
- the `if not converged:` branch and its pass-cap refusal;
- in `module_solve.py`: `_OUTER_MODES`, `OUTER_MODE`, `TRUST_OUTER`, `OUTER_CAP`, and the two
  refusals that guarded `trust` against being set with no block schedule or with a single block.

**Why removing it is safe, and how that is checked rather than argued.** Every arm this experiment
runs already took the single-pass path: the partitioned arms because they set `OUTER=trust`, the
flat arms because one block covering every in-loop node hits the single-block guard first. The
removed code therefore ran only when `OUTER` was unset — a state V4 has no arm for. **Gate GR is
what checks that**: `A1` and `B3` on all three configurations reproduce the previous revision's
records on every compared value, including `module_solve_totals.block_sweeps`,
`…inner_sweeps_by_block` and `…outer_pass_hist`. Had the removal moved anything, those would have
moved with it.

**One name survives the removal, deliberately.** The run record still publishes
`module_solve_totals.outer_pass_hist`, and `_module_stats` still emits `outer_passes`. That is the
key the committed reproduction reference and every earlier record use, so renaming it is a change to
the *record schema*, not to the driver, and it belongs with the tally task that reads it (§11). It
is `1` in every arm, which is a statement — the schedule was not repeated — where a missing field
would be a silence.

### 4.2 `PROCESS_ARCH_INNER_TAU` — retired under one tolerance

**Exactly which code read it.** `module_solve.py` resolved `INNER_TAU` from the environment,
defaulting to `TAU`, and refused it outright under the single-block arrangement.
`caller._call_models_by_module` read `module_solve.INNER_TAU` into a local `inner_tau` and used it in
three places: the block loop's convergence test `res.converged(inner_tau)`, the non-convergence
refusal's message, and `_module_stats(inner_tau=…)`, which put it in the per-call diagnostics.

**What it reads now.** All three read `module_solve.TAU` — the one tolerance of D23. The refusal's
message says `tau=` instead of `inner_tau=`, the `inner_tau` key is gone from `module_solve_stats`,
and `module_solve.INNER_TAU` no longer exists. In the previous revision's campaign `INNER_TAU` was
never set, so it always *equalled* `TAU`; that is why GR reproduces.

### 4.3 `PROCESS_ARCH_LIFT` + `PROCESS_ARCH_PIN_BURN_TIME` → `PROCESS_ARCH_BURN_TIME_OWNER`

**The fold.** `optimiser` ⇒ the burn time leaves the model and becomes a design variable (what the
lift did). `constant:<hex float>` ⇒ it leaves the model and a fixed value holds it (the pin, which
*implies* the lift of that one site, which is what `subsolve.py` required). `loop`, or the variable
unset ⇒ neither; the model solves for it every sweep, which is upstream.

**A refusal disappears with the fold, and that is the point.** The previous form could be set
inconsistently — a constant owning a quantity the model still solved for — and `subsolve.py` had to
refuse that combination at import, because the model would overwrite the constant on the first
sweep. The combination can no longer be written down, so the refusal is gone with it. The *other*
two-owners refusal stays: an input file that names `ixc = 178` while a constant owns the burn time is
still refused by `Caller._apply_burn_time_constant`, because that fight is between the environment
and the input file and no switch spelling can prevent it.

**The general list form is not implemented, and a docstring says what would need it back.** The
earlier switch took a comma-separated list of sites because the seam is general; exactly one site is
routed through it and this experiment takes exactly one quantity out of the loop, so the switch names
the quantity. `subsolve.py`'s module docstring records: *"If a second quantity is ever taken out of
the loop, the general list form has to come back — a second single-quantity switch would multiply,
and the arms would stop being one column of a matrix each."* That is A47's note, kept where a reader
meets it.

**The constant is hex-only.** `constant:7200.0` is **refused**, naming `float.hex()` output as the
required form. The constant rides a per-seed displacement stream and a decimal literal would quietly
change the value being held; the harness has always passed it as hex.

---

## 5. The typed refusal

`ArchitectureRefusal(RuntimeError)` lives in **`PROCESS/process/core/solver/__init__.py:18`** — the
solver package's own `__init__`, which was one line of docstring before.

**Why there.** It had to be a file the source commit already has: the copy-identity gate compares
the file *set* as well as the contents, so a new module would have to be modelled as a permitted
*addition* and the gate would stop being a straight "these five files differ and here are their
hunks". It had to be somewhere every architecture-switched module already imports through, and
`process/core/solver/` holds all three of them (`caller.py` imports the package;
`module_solve.py` and `subsolve.py` are in it; `process/models/pulse.py` reaches the driver seam
through `process.core.solver.subsolve` and therefore through the package too). And the package
`__init__` runs **earliest**, which matters for the guard below.

**What raises it: 34 sites** — 21 in `caller.py`, 9 in `module_solve.py`, 3 in `subsolve.py`, 1 in the guard itself. Every driver-side refusal of an architecture setting — an unrecognised
switch name, an illegal value, a missing committed artifact, an artifact that does not rebuild its
own hash or belongs to another configuration, a node the configuration keeps per-call, two owners for
the burn time, a deferral asked for without the site being out of the loop, a trace with nothing to
trace, a routing rule that cannot be derived.

**What does not raise it, and why.** Two raises are deliberately left as plain `RuntimeError`:

- **upstream's own ten-pass raise** (`caller.py:1423`). That is a finding about the shipped code —
  a displaced entry may reach the cap by design — and it has its own taxonomy row,
  `unconverged-at-cap`. Making it a refusal would file it with the guards that worked.
- **the constant-owned burn time's tripwire** (`subsolve.assert_burn_time_constant`). It fires when
  something *overwrote* a value the driver guaranteed would not move. That is a finding about the
  run, not a setting being refused, and it should land in `crashed` where a reader will look at it.

**How the harness uses it.** `harness/failure.py` classifies by **type first**, matching the name
over the exception's inheritance chain (`type(exc).__mro__`) rather than with `isinstance`. The
harness classifies runs in the parent process, where the driver is not importable; a name walk needs
neither the import nor the tree, and a future subclass lands in the same row. The message-text match
is kept as the fallback, marked in the module's docstring and beside `REFUSAL_MARKERS` with the
condition for deleting it: *"once no record from a tree that predates the typed refusal is read any
more."*

### 5.1 The retired-name guard

Eleven names raise: `MODULE_SOLVE`, `OUTER`, `INNER_TAU`, `SEQUENCE`, `PRIME`, `HOIST`,
`POST_SOLVE`, `LIFT`, `PIN_BURN_TIME`, `YSTATE`, `WRITESET`. Each message names its replacement.

The guard is `assert_no_retired_switches()` in the same file, and it runs **at the import of
`process.core.solver`** — the earliest point every route into the driver passes through. Before the
rename an unrecognised `PROCESS_ARCH_*` name was simply ignored, so a script still setting an old
name would produce a *successful* run of a *different* arrangement under the right name, with no
error anywhere. That is the same shape as the two standing traps of this project: a worktree that
does not redirect the editable install (T6), and a version string that agrees with the wrong commit
(T10). The measurement of the eleven is in §9.

**The list exists twice, and the two copies are compared rather than trusted.** The driver has
`RETIRED_SWITCHES`; the harness registry has the same names in each `Switch`'s `retired_names`. The
self-check's capability probe reads the driver's own dict and compares the sets: a name on one list
and not the other would mean the harness is clearing a switch the driver still honours, or refusing
one the driver never heard of. Measured at `6ac91bf4`: **11 names, identical on both sides.**

---

## 6. What the copy now differs from its source commit in

`PROCESS_diff.py` at `24652a72`. Exit status **0**: every hunk is claimed and gate G0′ passes.
**5 changed files, 65 hunks, 0 unexplained.** The full `--markdown` output follows.

*Caption: one row per file in which V4's copy of the PROCESS package differs from its source commit
`f2dc9243`. Columns: the file's path inside the package; lines added and removed by `git diff`
against the commit (not against any working tree); the number of hunks; and, per hunk, the switch or
mechanism the annotation map in `PROCESS_diff.py` says it serves, with the number of the file's hunks
that claim names in brackets. A hunk may serve more than one mechanism. `UNEXPLAINED` means no
annotation claims the hunk. Population: all 224 files of the copied package.*

| file | + | − | hunks | serves |
|---|---:|---:|---:|---|
| `process/core/caller.py` | 495 | 466 | 43 | typed refusal (15); arrangement · node (3); vocabulary only (17); arrangement · method (3); deferral per-call (29); analysis loop (15); burn-time owner (6); the two path constants' comment (2); harness paths (2); `NODE_WRITESET_PATH` (2); `NODE_MAP_PATH` (1); the per-call refusal's comment (1); deferral per-run (11); the per-run artifact's comment (1); retired `…_OUTER` (11); retired `…_INNER_TAU` (3) |
| `process/core/solver/__init__.py` | 112 | 1 | 1 | typed refusal (1); the retired-name guard (1) |
| `process/core/solver/constraints.py` | 2 | 2 | 1 | burn-time owner (1) |
| `process/core/solver/module_solve.py` | 155 | 228 | 15 | the coupling-state artifact's comment (1); analysis loop (7); retired `…_OUTER` (4); retired `…_INNER_TAU` (5); vocabulary only (11); the write-set artifact's comment (1); coupling-state / write-sets switches (4); typed refusal (6); the predicate module's comment (1); `YSTATE_MODULE_PATH` (1) |
| `process/core/solver/subsolve.py` | 160 | 103 | 5 | burn-time owner (5); typed refusal (2) |

*(Claim names are abbreviated here for width; `PROCESS_diff.py --markdown` prints each in full, e.g.
"switch `PROCESS_ARCH_ARRANGEMENT_NODE` (was `…_SEQUENCE`): arrangement at node granularity".)*

**Frozen physics, restated for a reader.** The physics is frozen at base commit `c0ae5b28` (D5). Of
the **77** files under `process/models/` in this copy, **76** are byte-identical to that commit and
the file set matches exactly. The one file that differs is `process/models/pulse.py`, and it is
approved: D14(b), 2026-09-01 — the burn-time residual extracted into a driver-solvable form, the
arithmetic verbatim. Gate G0′ verdict: **PASS**.

**One tool change went with this.** A hunk's annotation now matches against the hunk's **changed**
lines only. A context line carrying a marker could otherwise claim a hunk for a mechanism it does not
serve, and a claim nobody can check is worse than an `UNEXPLAINED` nobody can miss. Its tooth — one
unclaimed line appended to a throwaway copy of `process/core/constants.py` — **TRIPPED**.

### 6.1 The copy's provenance

`PROCESS/copy_gates.py all` at `f22c6d61`: **ALL GATES PASS.**

| gate | verdict | numbers | teeth |
|---|---|---|---|
| smoke import | PASS | the copy is what `import process` resolves to under `PYTHONPATH`, from a directory that is neither tree | 1 (no `PYTHONPATH` ⇒ resolves elsewhere) TRIPPED |
| edit behaviour | PASS | the copy raises `ArchitectureRefusal` naming the artifact and its provenance file; the source commit raises the bare `FileNotFoundError` the edit repairs | 1 (artifact present ⇒ must not refuse) TRIPPED |
| copy-identity | PASS | **224** files compared, **219** identical, **5** permitted-edit files, 0 unexplained, 0 missing, 0 added | 4 TRIPPED |
| frozen-physics (G0′) | PASS | **77** compared, **76** identical, `pulse.py` alone, 0 unapproved | 4 TRIPPED |

*Caption: one row per gate in the copy's own gate script, at the commit that regenerated the
provenance file. "Numbers" states the population each verdict is over.*

`PROVENANCE.json` was regenerated on its own unchanged guard, which refuses to write unless the files
that actually differ are exactly the permitted-edit list — 5 and 5. Three files joined that list:
`process/core/solver/__init__.py`, `subsolve.py` and `constraints.py`. The `edit-behaviour` gate had
to learn to name the per-run deferral's switch and entry point **per side**, because the copy and the
source commit spell them differently now; without that, its source-commit arm would have failed on
the name rather than on the behaviour and the comparison would have said nothing.

---

## 7. Gate G1 — switch neutrality

**What it does.** Two runs on each of the three configurations — `BR` (one optimisation) and `AR`
(one evaluation), both reference arms, which compose to an environment with the *whole* switch
vocabulary cleared — recorded at the commit before the driver change and again after it, then
compared value by value and line by line.

**The two captures, and why they are separate stages.** Capturing and comparing are separate
commands so that the "before" side is taken at the commit it claims to be taken at and cannot be
re-taken later to make a comparison agree.

- **before**: at `90c5d67d`, the commit that added `harness/gates.py`. `git diff f1f90c20 90c5d67d
  -- …_v4/PROCESS/process` is **empty**: that capture ran the driver exactly as the branch point
  left it.
- **after**: at `6ac91bf4`. `git diff 6ac91bf4 HEAD -- …_v4/PROCESS/process` is **empty**: no commit
  since has touched the copy, so the capture is the driver as this task leaves it.
- between them, `git diff --stat` over the copy: **5 files, 891 insertions, 787 deletions.**

**Result: PASS.**

*Caption: one row per run pair. "Values" counts every deterministic leaf of the run record, lists
expanded element by element; "lines" counts PROCESS's own output file line by line. Both are
compared without tolerance, floats through their hexadecimal form so that ±0 and NaN behave. Script:
`harness/gates.py switch-neutrality`, committed at `90c5d67d`, run at `24652a72`.*

| arm | configuration | values differing / compared | output-file lines differing / compared |
|---|---|---:|---:|
| `BR` | `large_tokamak_nof` | **0** / 506 | **0** / 16 173 |
| `AR` | `large_tokamak_nof` | **0** / 339 | **0** / 7 |
| `BR` | `low_aspect_ratio_DEMO` | **0** / 500 | **0** / 16 434 |
| `AR` | `low_aspect_ratio_DEMO` | **0** / 326 | **0** / 7 |
| `BR` | `st_regression` | **0** / 413 | **0** / 18 691 |
| `AR` | `st_regression` | **0** / 299 | **0** / 7 |
| | **total** | **0 / 2 383** | **0 / 51 319** |

**What is excluded, and why an exclusion list is published.** A gate that compares "everything" and
does not say what it left out is trap T11's shape. **648 record values and 45 output-file lines** were
excluded, each by a named rule with its reason, and every rule is written into the gate's own record.
The rules are of four kinds:

1. **absolute paths** — the two runs are in different directories by construction (`outdir`,
   `campaign_input_file`, `tree`, `process_file`, `pythonpath`, the audit's artifact paths);
2. **wall clock and machine state** — `wall_s`, `cpu_*`, `maxrss_kb`, `loadavg`,
   `mfile.process_runtime`. No timing is evidence in this project and none is compared here;
3. **the commit** — `tree_git_head`, `tree_git_describe`, the working-tree state fields, and
   `process_copy_provenance.copy_date`. The two runs are at different commits: that is the point of
   the gate;
4. **the names being renamed** — the whole of `env_architecture` and `resolved_switches`. Every
   *value* in them is the off-state on both sides, because the arm sets nothing; the *keys* are the
   rename itself, and comparing them would be comparing the change to itself.

**The evaluation phase's output file is a header.** `AR` runs one evaluation and never reaches the
output path, so its `MFILE.DAT` is 14 lines of banner, 7 of them run metadata. Its line comparison is
therefore 7 lines and says almost nothing; **the record comparison (299–339 values per evaluation) is
what carries the evaluation phase**, and this is stated rather than left for a reader to notice that
a 7 is not a 16 000.

**Teeth — 3/3 tripped.**

| tooth | construction | result |
|---|---|---|
| one value moved by 1 ULP | `values.norm_objf` of a **throwaway copy** of a captured record moved one unit in the last place: `0x1.99999999b822dp+0` → `0x1.99999999b822ep+0` | **TRIPPED** — 1 of 506 values differ |
| one output-file line changed | the exit-code line of a throwaway copy of a captured output file changed | **TRIPPED** — 1 of 16 173 compared lines differ |
| a missing "before" record | the comparison pointed at a directory that does not exist | **TRIPPED** — refused, not skipped |

*Caption: one row per deliberate break. Neither capture is ever modified; each tooth works on a copy
in a temporary directory. The third is the one that matters most: a gate that skipped a missing side
would report a zero over an empty population.*

---

## 8. Gate GR after the rename

**Why it was re-run.** GR is defined to run **once**, at the copy commit, before any driver change —
at that moment the copy *is* the previous revision's driver, so any difference from its records is
the harness's. That is not what this re-run is for. Re-running it **after** the rename asks a
different and narrower question: **is the rename a rename?** G1 cannot answer it, because G1 runs
only with every switch unset and therefore exercises no arm. GR runs the arms.

Script: `experiment_runner.py --gate reproduction --lifted-from …_v3/runs/_decks`, at `24652a72`,
3 workers.

**Result: PASS. 20/20 runs reproduced, 270/270 compared values identical, 0 mismatched, no tolerance
on any of them.**

*Caption: one row per reference run. "Values" is the number of fields compared against the previous
revision's committed record for that run — 15 for an optimisation, 10 for an evaluation. Population:
20 runs (14 optimisations + 6 evaluations) over 3 configurations, 270 compared values.*

| arm | configuration | seed | values differing / compared |
|---|---|---:|---:|
| `BR` | `large_tokamak_nof` | 0 | 0 / 15 |
| `BR` | `low_aspect_ratio_DEMO` | 0 | 0 / 15 |
| `BR` | `st_regression` | 0 | 0 / 15 |
| `B0` | `large_tokamak_nof` | 0 | 0 / 15 |
| `B0` | `low_aspect_ratio_DEMO` | 0 | 0 / 15 |
| `B0` | `st_regression` | 0 | 0 / 15 |
| `B3` | `large_tokamak_nof` | 0 | 0 / 15 |
| `B3` | `low_aspect_ratio_DEMO` | 0 | 0 / 15 |
| `B3` | `st_regression` | 0 | 0 / 15 |
| `B3` | `large_tokamak_nof` | 1 | 0 / 15 |
| `B3` | `low_aspect_ratio_DEMO` | 1 | 0 / 15 |
| `B3` | `st_regression` | 1 | 0 / 15 |
| `B1` | `large_tokamak_nof` | 1 | 0 / 15 |
| `B1` | `low_aspect_ratio_DEMO` | 1 | 0 / 15 |
| `A0` | `large_tokamak_nof` | 1 | 0 / 10 |
| `A0` | `low_aspect_ratio_DEMO` | 1 | 0 / 10 |
| `A0` | `st_regression` | 1 | 0 / 10 |
| `A1` | `large_tokamak_nof` | 1 | 0 / 10 |
| `A1` | `low_aspect_ratio_DEMO` | 1 | 0 / 10 |
| `A1` | `st_regression` | 1 | 0 / 10 |
| | | **total** | **0 / 270** |

**The six partitioned rows are the ones that answer the question.** `A1` and `B3` on all three
configurations ran the block schedule through code from which the repeated-schedule path has been
deleted, under a switch name that did not exist when their reference records were made, and
reproduced `node_calls_solve_phase`, `block_sweeps`, `inner_sweeps_by_block`, `outer_pass_hist`, the
objective hex and the exit-audit residual hex exactly.

**Record contract**: 20/20 records carry every declared field.
**Substitutes**: `A0p` PASS (2 pulsed configurations; 1 skipped with the reason recorded); `AR` PASS
(3 configurations × 4 values = 12 compared values, no tolerance).
**The gate-only allowance still applies**: `B1` and `B3` declare `output_loop`, which no tree
implements until A57 lands. The allowance covers exactly that term for exactly those two arms, is
checked for set equality against what the tree cannot implement, and is written into every run record
it produces.

**Teeth — 7/7 tripped.**

| tooth | must | result |
|---|---|---|
| count | one reproduced count raised by 1 must FAIL | TRIPPED |
| hex | one character appended to an objective hex must FAIL | TRIPPED |
| missing reference | a reference file that does not exist must **FAIL, not skip** | TRIPPED (refused) |
| missing key | a compared field deleted from a copy of the reference must **FAIL, not skip** | TRIPPED |
| bad name map | asking for arm `BR`, which the previous revision never had, without the map must **RAISE** | TRIPPED |
| **composition** | one switch of `B3`'s composition deliberately wrong must FAIL | TRIPPED — **7 of 15** compared values differ |
| attempt summation | per-attempt costs that do not sum to the run total must be **REFUSED** | TRIPPED |

**The composition tooth changed, and here is exactly how.** It used to *clear*
`PROCESS_ARCH_OUTER`, because with that switch unset the driver ran the verified schedule under the
partitioned arm's name — a wrong arm with a right-looking name, which is what a positive control has
to be able to see. **The fold makes that particular mis-composition impossible to write down**:
there is no setting that makes the partitioned loop repeat its schedule, and the old name raises. So
the tooth now sets `PROCESS_ARCH_MDA=flat` under `B3`'s name, every other switch of the arm
unchanged, and 7 of 15 compared values move. That is a *narrowing of what can go wrong*, not a loss
of coverage — but it is a change to a tooth, so the tooth's docstring says so where a reader of the
gate will find it.

---

## 9. The harness self-check

`experiment_runner.py --selfcheck` at `24652a72`: **PASS, 6/6 checks.** With
`harness/selfcheck.py --crosscheck-previous` (which executes the previous revision's own composition
code in a subprocess and compares it with this package's transcription of it): **PASS, 7/7.**

*Caption: one row per check. "Compared" is the number of things the check actually compared; a count
without its denominator is not a result. Teeth are deliberate breaks the check must catch.*

| check | compared / mismatched | teeth | notes |
|---|---:|---:|---|
| composition | 42 / 0 | 6 | 17 arm-configuration pairs compared against the previous revision **by role**, 86 role values |
| rungs | 98 / 0 | 3 | the plan's 11 × 8 matrix regenerated cell for cell; 6 rung steps |
| capability | 32 / 0 | **14** | 17 pairs probed; 9 composed terms resolve every readback; 11 retired names identical in registry and driver |
| provenance | 4 / 0 | 4 | unchanged by this task |
| data | 17 / 0 | 4 | unchanged by this task |
| run path | 8 / 0 | 9 | unchanged by this task |
| crosscheck-previous | 17 / 0 | 1 | the transcription matches what the previous revision's code produces |

### 9.1 Comparing two revisions' compositions after a rename

The composition check asks whether the arms the previous revision also ran **ask the driver for the
same thing**. Before the rename that was a dictionary comparison of environment variables. After it,
a literal comparison would report every arm as different and prove nothing — the two sides spell the
same request differently.

So the comparison is made **by role**. `switches.canonical_roles(env, revision=…)` maps each
revision's variable names onto the term for what the switch *does*, and normalises the values the two
revisions spell differently (`flat_state` → `flat`, `per_module` → `partitioned`). Equality then
means: the same role carries the same value on both sides.

**Two foldings are part of that map, and both can fail loudly rather than absorb a difference.**

- `OUTER=trust` alongside `MODULE_SOLVE=per_module` is **dropped**, because the partitioned loop now
  means exactly that. Any *other* combination becomes an explicit `schedule_passes` role, so a real
  difference still reads as one.
- The two burn-time settings become one `burn_time_owner`. A constant without the lift — which the
  previous revision refused at import — **raises** here rather than being read as some other owner.

Two teeth pin the fold itself, and they are the ones a reviewer should look at:

| tooth | construction | must |
|---|---|---|
| the fold read as a difference | drop `PROCESS_ARCH_OUTER` from the previous revision's `B3` environment | the two sides must still ask for the **same** thing — if they did not, the comparison would be treating a rename as a change |
| a schedule policy the fold does not cover | set `PROCESS_ARCH_OUTER=verify` on the previous revision's `B3` | the two sides must **differ** — the fold drops that switch only where its value is the one the partitioned loop implies |

Both TRIPPED. The other four composition teeth (a wrong switch value, a switch dropped, the wrong
per-run artifact, a skipped arm asked to compose) were kept and re-expressed against the role
dictionary; breaking a variable name would only have proved that the two revisions spell things
differently, which is true and uninteresting.

### 9.2 The capability probe

Three things were added, all measured rather than declared:

1. **Every composed switch resolves every readback the registry names**, on the tree under test —
   9 composed terms. A readback that resolved to nothing would mean the tree does not implement the
   switch, and a tree that ignores a switch runs a different arm under this arm's name.
2. **The registry's retired list is compared with the driver's own `RETIRED_SWITCHES`** — 11 names,
   identical. A name on one list and not the other would mean the harness is describing a driver it
   is not running.
3. **Twelve teeth on the retired names**: one per name, each asserting that the *harness* refuses to
   compose an environment carrying it, plus one asserting that the **driver** refuses to import with
   one set. The last is what covers a caller that never goes through the harness.

**One default changed as a consequence.** `harness/selfcheck.py --tree` now defaults to `copy`
rather than `repository`. The repository-root package belongs to the previous revision and does not
implement the renamed switches, so its capability check **fails by design** — which is the probe
doing its job, not a defect. The help text and the module docstring say so.

---

## 10. Autonomous decisions, each with the way back

*Caption: one row per decision this task took without asking. "Reversal" is what undoing it costs,
concretely.*

| # | decision | why | reversal |
|---|---|---|---|
| 1 | `ArchitectureRefusal` and the retired-name guard live in `process/core/solver/__init__.py`, not in a new module | a new file would make the copy-identity gate's file-set comparison model an *addition*, which is a change to the gate's shape for one class; the package `__init__` is the earliest point every route into the driver passes through | move both to a new `process/core/solver/architecture.py`, add an "added file" kind to `copy_gates.PERMITTED_EDIT_FILES`, and import from it in three places |
| 2 | The repeated-schedule path is **removed**, not left unreachable | dead code that only a deleted switch could reach is a trap for the next reader, and the reproduction gate can check the removal directly | `git revert` the hunks; the loop, the joint test, the trace hook and the pass cap are one contiguous region of `_call_models_partitioned` |
| 3 | `constant:<hex float>` accepts **only** a hexadecimal literal | the constant rides a per-seed displacement stream and a decimal literal loses bits; the harness has always passed `float.hex()` output | one `elif` in `subsolve._parse_owner` |
| 4 | The recorded field names `module_solve_totals`, `outer_pass_hist`, `post_solve_totals`, `n_prime_calls`, `pin_intact_at_exit` are **not** renamed | they are the record's contract with the committed reproduction reference, which A49 built and gate GR reads; renaming them means regenerating that file from the previous revision's live records, which is a separate change with its own gate | §11 names it as A53's, with the exact cost |
| 5 | `PROCESS_diff.py` matches annotations against a hunk's **changed** lines only | a context line carrying a marker could claim a hunk for a mechanism it does not serve, and an unverifiable claim is worse than an `UNEXPLAINED` | four lines in `parse.close_hunk` |
| 6 | `selfcheck.py --tree` defaults to `copy` | the repository tree cannot implement V4's switches, so the old default made a direct invocation fail on something that is correct | one default value |
| 7 | GR's composition tooth perturbs `PROCESS_ARCH_MDA=flat` instead of clearing the retired schedule switch | the switch it used to clear no longer exists | choose another switch of `B3`'s composition; the tooth is one dict entry |
| 8 | Switch **values** that §11.2 does not name are unchanged (`build_after_physics`, `fw_geometry`, `feedforward`, `feedforward_lifted`) | inventing replacements for values the plan does not name would be a change nobody asked for, and each would need its own row in the reproduction reference's arm map | rename in `module_solve.py` / `caller.py`'s tables and in the registry's `values`; GR would then need a value map for the previous revision's records |

---

## 11. Handover

*Caption: one row per queued task, and the concrete thing this task leaves for it.*

| task | handover |
|---|---|
| **A57 (driver-output-path)** | `PROCESS_ARCH_OUTPUT_LOOP` is already a registry row with `driver_name=None`, its readback (`caller.OUTPUT_LOOP_NAME`) declared and its `pending_change` written; implementing it makes `B1`/`B3` runnable and empties `reproduction.GATE_ALLOWANCE`, at which point that mechanism is inert. Add the switch to the registry's `driver_name`, add a `PermittedEdit` row and one `ANNOTATIONS` line, regenerate `PROVENANCE.json`, and run `gates.py switch-neutrality --capture before` **before** the edit. |
| **A58 (driver-predicate-counters)** | same shape; the counters are record fields, not switches, so nothing in `switches.py` changes. |
| **A59 (driver-predicate-mode)** | `PROCESS_ARCH_PREDICATE` is a registry row already, readback `module_solve.PREDICATE_MODE`. |
| **A60 (driver-attempts)** | the per-attempt refusal already exists in `records.assert_attempt_summation` with its tooth; the driver side is what is missing. |
| **A52 (harness-gates)** | `harness/gates.py` has `Gate`/`Tooth` (a gate without a tooth is a `TypeError` at construction), `registry(campaign)`, verdict records under `runs/gates/<name>/`, and G0′ and G1 implemented. **One line to wire in**: give `experiment_runner.py` a `--gate <name>` value per registered gate and dispatch to `gates.registry`; nothing else here needs the runner. `selfcheck.Check` and `gates.Gate` have the same record shape on purpose. |
| **A53 (harness-tally)** | the record field names that still carry the previous revision's mechanism words — `module_solve_totals` (and its `outer_pass_hist` key), `post_solve_totals`, `n_prime_calls`, `pin_intact_at_exit`. Renaming them is a **record-schema** change: `reference.REFERENCE_FIELDS` and the committed `reproduction_reference.json` name them, so the reference has to be regenerated from the previous revision's live records under `…_v3/runs/` and re-verified byte for byte. Worth doing once, with the tally, rather than piecemeal. |
| **the experiment plan** | `EXPERIMENT_PLAN.md` §3.2's matrix still has a row spelt "outer loop" whose partitioned cells read `trust`. `arms.PLAN_MATRIX` transcribes it and the self-check compares the two cell for cell, so the transcription cannot be changed alone — the plan's table and the transcription move together, and the plan is not this task's to edit. |
| **`process/models/pulse.py`** | its comment at line 246 still names `PROCESS_ARCH_LIFT`. It is a **frozen model file** (G0′), so this task did not touch it; the switch it names no longer exists. Correcting a comment there needs the user's approval under D11 like any other model edit, and is not worth one on its own. |

---

## 12. How to re-run everything in this report

From `arch_surgery/MDA_partitioning_experiment_v4/`, with
`/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python`:

```
# §6.1 — the copy is what its provenance claims, and the physics is frozen
python PROCESS/copy_gates.py all

# §6 — what the copy does differently, per hunk, with the frozen-physics statement
python PROCESS_diff.py                 # exit 0 means every hunk is claimed
python PROCESS_diff.py --markdown      # the table in §6
python PROCESS_diff.py --teeth         # an unannotated hunk must be reported

# §1 — G0' on its own, with its four teeth and a verdict record
python -m harness.gates g0prime

# §7 — G1.  The two captures are separate stages on purpose.
python -m harness.gates switch-neutrality --capture before   # BEFORE the driver edit
python -m harness.gates switch-neutrality --capture after    # after it
python -m harness.gates switch-neutrality --compare

# §9 — the harness's own gates
python experiment_runner.py --selfcheck
python harness/selfcheck.py --crosscheck-previous

# §8 — gate GR
python experiment_runner.py --gate reproduction \
  --lifted-from /home/wrutten/projects/PROCESS_surgery/arch_surgery/MDA_partitioning_experiment_v3/runs/_decks
```

`HARNESS_WORKERS=3` was used for every stage that starts PROCESS runs. Records land under
`runs/gates/`, which is untracked by design; every number a report cites is reproduced in the report.

---

## 13. Change log

*Caption: one row per commit on `A56-driver-renames`, in order.*

| commit | what |
|---|---|
| `90c5d67d` | `harness/gates.py`: the gate framework (`Gate` requires at least one `Tooth`), G0′ wrapping `copy_gates.py frozen-physics` by path, G1 with its capture/compare stages and three teeth. G0′ verified PASS at this commit. |
| — | G1 "before" captured at `90c5d67d`: 6 runs, all `ok`. The driver is byte-identical to the branch point here. |
| `ce70ec5b` | **the driver rename** in `…_v4/PROCESS/process/` only: nine switches renamed, `OUTER` folded into `MDA=partitioned` (the repeated-schedule path removed), `INNER_TAU` retired, the burn-time pair folded into one owner switch, `ArchitectureRefusal` and the eleven-name guard added, module-level readbacks renamed. G0′ PASS at this commit. |
| `f22c6d61` | `copy_gates.py` permitted-edit list (3 new files), `PROVENANCE.json` regenerated on its unchanged guard, `PROCESS_diff.py` annotations regrouped by mechanism and matching restricted to changed lines. `copy_gates.py all` PASS; `PROCESS_diff.py` exit 0, 0 unexplained. |
| `6ac91bf4` | the harness follows: registry `driver_name`s and `retired_names`, `canonical_roles`, `Arm.terms`, the driver-side readbacks in `child.py`/`evaluate.py`, typed classification in `failure.py`, the self-check's role comparison and its new teeth, GR's composition tooth, README §4/§6/§7. Self-check PASS 6/6, `--crosscheck-previous` PASS 7/7. |
| — | G1 "after" captured at `6ac91bf4`. |
| `24652a72` | `PROCESS_diff.py --markdown` deduplicates a claim per file rather than per hunk, so the table is readable. |
| — | G1 compared: **PASS**, 0/2 383 values, 0/51 319 lines, 3 teeth. GR re-run: **PASS**, 20/20 runs, 270/270 values, 7 teeth, both substitutes. |
| *(this commit)* | this report. |

---

## 14. Orchestrator's critical assessment (protocol §5) — 2026-09-10

*Appended by the orchestrating session before merge, against the report at `a0c0526c` and the copy
and harness on the same branch. Every gate was re-run by the orchestrator, not read off the report.*

**Verified independently.** (1) **Gate GR re-run from scratch** against the renamed driver
(`--gate reproduction`, fresh records directory): 20 of 20 runs reproduced, **270 of 270 compared
values identical**, record contract 20 of 20, substitutes `A0p` and `AR` PASS, **seven teeth
tripped** — the composition control now runs `B3` with `PROCESS_ARCH_MDA=flat` and does not
reproduce. (2) **G1** through `harness/gates.py switch-neutrality --compare` on the branch's own
before/after captures: 6 run pairs, **0 of 2 383** deterministic record values and **0 of 51 319**
output-file lines differ; the three teeth trip (one ULP, one line, a missing before record refused).
(3) **G0′** through `gates.py g0prime` and `PROCESS/copy_gates.py all`: 77 model files, 76 identical,
`pulse.py` alone, all teeth; `copy-identity` PASS with five permitted-edit files and 0 unexplained;
`PROCESS_diff.py` exit 0, 65 hunks, 0 unexplained. (4) `experiment_runner.py --selfcheck` against the
copy: six checks PASS, the pending list still exactly the five `B1`/`B3` pairs. (5) Scope: eighteen
files — the five driver files of the copy, the copy's provenance and diff tooling, the harness files
the brief assigned, `gates.py`, the README's registry section and this report; `models/`, the
repository-root `process/`, `experiment_runner.py` and every A51-owned file untouched. (6) No
retired name is read anywhere in the copy outside the `RETIRED_SWITCHES` table that raises on it.

**Endorsed.** Removing the verified-schedule path rather than leaving it unreachable, with GR as the
check that removal moved nothing — the block-sweep, per-block and pass-histogram values of `A1` and
`B3` reproduce V3 through code the repeated schedule has been deleted from, which is a stronger
statement than "unreachable" and one the gate can make. The typed `ArchitectureRefusal` at 34 raise
sites with the harness classifying by type. The burn-time owner as one switch whose `constant:<hex>`
form makes pin-without-lift structurally impossible instead of refused. Comparing the driver's
`RETIRED_SWITCHES` table with the harness registry rather than assuming them equal. Capturing G1's
"before" at a commit verified byte-identical to the branch point.

**Limits I hold it to.** (a) G1's exclusions (648 record values, 45 output-file lines) are named
per item with a reason in the gate record; they are the non-deterministic and provenance fields, and
A52 (harness-gates) inherits the list as the declared exclusion set, to be reviewed rather than
extended. (b) The value vocabulary of the switches §11.2 does not name (`build_after_physics`,
`fw_geometry`, `feedforward`, `feedforward_lifted`) is unchanged; `feedforward_lifted` keeps the
mechanism word, as §11.2 permits. (c) `B1`/`B3` still run under the gate-only allowance for the
output-time-loop switch until A57 lands.

**Rulings and consequences drawn (orchestrator, today).** *Plan §3.2's "outer loop" row:* the
switch is gone, so the row is renamed **"block schedule"** with cells `one pass` where it said
`trust`, and the harness's transcription (`arms.PLAN_MATRIX`, `matrix_cell`) moves with it in the
same commit, verified by the self-check's rungs check; the rung table's "+ trust" becomes "+ one pass
over the block schedule"; the plan's switch list is restated in the §11.2 names. *Record fields
carrying V3 mechanism words* (`module_solve_totals`, `outer_pass_hist`, `post_solve_totals`,
`n_prime_calls`, `pin_intact_at_exit`): renamed by **A53 (harness-tally)** through a field-name map
in `reference.py` (V3 path → V4 path) so the committed reproduction reference keeps its bytes and
the comparator translates — the reference is not regenerated. *`process/models/pulse.py:246`'s
comment naming the retired `PROCESS_ARCH_LIFT`:* a frozen model file; left as it is and put to the
user in the final report as a D11 question (comment-only). *A52 (harness-gates)* wires
`gates.registry` into `experiment_runner.py --gate <name>` and completes the gate set; A57
(driver-output-path) is dispatched off the merged tip.

**Verdict.** Fit to merge; nothing returned. The rename is a rename: the copy says what the
experiment plan says, and every measured quantity is where it was.
