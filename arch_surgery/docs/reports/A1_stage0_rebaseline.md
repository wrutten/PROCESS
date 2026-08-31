# A1 (stage0-rebaseline) — Stage 0 re-baseline at `c0ae5b28`

| | |
|---|---|
| **Task** | A1 (stage0-rebaseline) |
| **Branch** | `A1-stage0-rebaseline`, off `architecture_surgery` at `01f3471f` |
| **Base commit** | `c0ae5b28` |
| **Stage** | 0 of [`../MDA_PARTITION_EXPERIMENT.md`](../MDA_PARTITION_EXPERIMENT.md) |
| **Date** | 2026-08-31 |
| **Status** | Complete — **two gates pass, one fails on one scenario** |

---

## 1. Verdict

The measurement apparatus is re-established at the base commit and it is sound. Two of the
three gates pass on every scenario that runs. The third fails on one scenario, and the cause
is a **stale input file**, not the code.

| Gate | Result |
|---|---|
| **(a) Switch-neutrality** — probe off vs. probe on vs. untouched base commit | **PASS** on all three scenarios that run. Not merely within tolerance: every one of the ~16,000 lines of the MFILE is byte-identical across all four arms, once the run-metadata header is excluded. |
| **(b) Determinism** — two independent runs agree exactly | **PASS** on all three scenarios that run. Results identical bit-for-bit *and* sweep counts identical to the last sweep. |
| **(c) Baseline solves** — `ifail = 1` everywhere | **FAIL on `st_regression`**, PASS on the other three. `st_regression` does not return a bad `ifail`; it **raises** before the optimiser completes its first function evaluation. |

*`ifail` is PROCESS's solver return code; `ifail = 1` means a feasible (or, for an evaluation
run, consistent) solution was found.*

**The `st_regression` failure is a stale scenario file, and it reproduces on an untouched
checkout of the base commit.** It is therefore not caused by the probe, and it is not
something the probe can fix.

- The archived `arch_surgery/idf_probe/scenarios/st_regression.IN.DAT` was copied from the
  superseded study at commit `710a75c9`. It sets `i_tf_sc_mat = 9` (Hazelton-Zhai REBCO, a
  *tape* superconductor) but does not set `i_tf_turn_type`, which defaults to `1`
  (cable-in-conduit). At `c0ae5b28` the caller dispatches on `i_tf_turn_type`, lands in the
  cable-in-conduit TF-coil model, and that model raises:

  > `ProcessValueError: Cannot calculate cable in conduit superconductor properties for
  > non-cable superconductors.`

- The base commit's *own* copy of the same scenario,
  `tests/regression/input_files/st_regression.IN.DAT`, additionally sets `i_tf_turn_type = 2`
  (CroCo turn geometry for HTS tape) and four tape-geometry lengths. Run with that file, the
  scenario **solves at `ifail = 1` and passes all three gates**, including whole-MFILE
  identity across arms.
- The other three archived scenarios differ from the base commit's regression inputs **only**
  by variable renames, which the runner applies automatically. They are equivalent.

I ran the corrected input as a **clearly separated diagnostic arm**
(`runs/st_regression__base_input/`), not as the gate. **Gate (c) stands as FAIL.** The
diagnostic exists to distinguish "the code cannot solve this scenario" from "this input file
does not belong to this commit", and it settles that question: it is the input file.

**Recommendation for the user (a decision, not something I took):** re-point the scenario set
at `tests/regression/input_files/` for all four scenarios, so the inputs are pinned to the
same commit as the code. That is a one-line change to `run_one.py`'s default plus a fresh
Stage-0 run, and it should be recorded as a `D<n>` because it changes what "the four
scenarios" means for every later stage. Until then, **`st_regression` is not measurable and
Stage 1 has three scenarios, not four.**

Nothing else surprised me in a bad way. The probe costs nothing measurable, the solver is
exactly reproducible, and no scenario needed a solver retry.

---

## 2. What was built

An env-switched probe, written fresh against this tree. Nothing was carried over from the
superseded probe.

*Env-switched* means: the instrumentation is controlled by the environment variable
`PROCESS_IDF_PROBE`. Unset, every hook is a no-op — a single global boolean load and a
branch, with no floating-point work and no state mutation. Set to `baseline`, the probe
records; it never alters control flow.

| File | Change |
|---|---|
| `process/core/_idf_probe.py` | **new** — all probe state and logic |
| `process/core/caller.py` | 4 hooks + 1 import |
| `process/core/solver/evaluators.py` | 3 hooks + 1 import |
| `process/core/solver/solver_handler.py` | 3 hooks + 1 import |

Nothing under `process/models/` is touched (D5 — "the models are frozen; only the driver
changes"). Full manifest and run instructions:
[`../../idf_probe/README.md`](../../idf_probe/README.md).

**Vocabulary used throughout this report.** A *sweep* is one execution of
`Caller._call_models_once`, i.e. one pass over the whole model sequence. A *`call_models`* is
one execution of `Caller.call_models`, the **idempotence loop**, which repeats sweeps until
the objective and constraints stop changing; it has a structural floor of **two** sweeps
(it must run twice to have two values to compare) and a ceiling of ten. A *phase* records
which part of the solver asked for a given `call_models`: `fn` (objective and constraint
evaluation, in `fcnvmc1`), `grad` (one of the `2n` finite-difference perturbations in
`fcnvmc2`), `grad_reconcile` (the trailing call at the end of `fcnvmc2` that restores
consistency with the unperturbed point), and `output` (the final output-file idempotence
check, which sits outside any `call_models`).

---

## 3. Gates, with the numbers

### (a) Switch-neutrality — PASS

Three arms compared: `pristine` (an untouched `git archive` of `c0ae5b28`, where the probe
module does not exist at all), `control` (this tree, `PROCESS_IDF_PROBE` unset) and
`baseline` (this tree, `PROCESS_IDF_PROBE=baseline`).

Compared on **hex float literals** — exact IEEE-754 doubles — so "identical" means identical,
with no re-parsing tolerance anywhere in the chain.

| Scenario | differing fields, pristine vs control | pristine vs baseline | MFILE lines compared | differing MFILE lines |
|---|---|---|---|---|
| `large_tokamak_nof` | none | none | 16,174 | 0 / 0 / 0 |
| `low_aspect_ratio_DEMO` | none | none | 16,435 | 0 / 0 / 0 |
| `large_tokamak_eval` | none | none | 15,917 | 0 / 0 / 0 |
| `st_regression` | — run crashed in every arm — | | | |
| *(diagnostic)* `st_regression`, base-commit input | none | none | 18,681 | 0 / 0 / 0 |

The fields compared are `norm_objf` (the normalised objective function), the full vector of
final iteration variables, `sqsumsq` (the root-sum-square of the equality-constraint
residuals), the L2 norm of the full constraint vector, and the raw ASCII MFILE fields.

The whole-MFILE check is stronger than the gate requires and I report it because it is the
one that would catch a subtle perturbation the named quantities miss: every line of the
MFILE, excluding only the run-metadata header (date, time, user, host, paths, git tag and
branch, wall-clock runtime), matches across all four arms. `large_tokamak_eval` is an
evaluation run solved by `fsolve`, which has no objective function, so its in-memory
`norm_objf` is `None`; for that scenario the objective comparison is carried by the MFILE's
raw `norm_objf` field (`9.28606022088452665e-01`), which is present and identical.

### (b) Determinism — PASS

Two independent `baseline` runs, separate subprocesses, separate working directories.

| Scenario | differing fields | sweeps, run 1 vs run 2 |
|---|---|---|
| `large_tokamak_nof` | none | 2029 vs 2029 |
| `low_aspect_ratio_DEMO` | none | 4286 vs 4286 |
| `large_tokamak_eval` | none | 29 vs 29 |
| *(diagnostic)* `st_regression`, base-commit input | none | 1891 vs 1891 |

Results agree bit-for-bit and the sweep histograms agree entry for entry. No thread-count or
BLAS environment variables were pinned — determinism holds as the code stands.

### (c) Baseline solves — FAIL on one of four

| Scenario | `ifail` | Outcome |
|---|---|---|
| `large_tokamak_nof` | 1 | PASS |
| `low_aspect_ratio_DEMO` | 1 | PASS |
| `large_tokamak_eval` | 1 | PASS |
| **`st_regression`** | — | **FAIL — raises `ProcessValueError` in the cable-in-conduit TF-coil model, on the first `fcnvmc1` call, in all four arms including `pristine`** |
| *(diagnostic)* `st_regression`, base-commit input | 1 | PASS |

Cause, mechanism and recommendation are in §1.

---

## 4. Sweep anatomy

Baseline arm, warm caches, runs executed serially.

| Scenario | `nvar` | constraints (eq + ineq) | VMCON iterations | `call_models` | sweeps | mean sweeps / `call_models` | at the 2-sweep floor | max | histogram | retries | wall clock |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 20 | 3 + 23 = 26 | 8 | 630 | 2029 | 3.217 | 20.2 % | 6 | 2:127 3:276 4:191 5:35 6:1 | 0 | 14.8 s |
| — phase `fn` | | | | 15 | 53 | 3.533 | 46.7 % | 6 | 2:7 4:2 5:5 6:1 | | |
| — phase `grad` | | | | 600 | 1915 | 3.192 | 20.0 % | 5 | 2:120 3:275 4:175 5:30 | | |
| — phase `grad_reconcile` | | | | 15 | 59 | 3.933 | 0.0 % | 4 | 3:1 4:14 | | |
| `low_aspect_ratio_DEMO` | 19 | 4 + 21 = 25 | 16 | 1240 | 4286 | 3.455 | 13.7 % | 5 | 2:170 3:622 4:162 5:286 | 0 | 31.8 s |
| — phase `fn` | | | | 31 | 99 | 3.194 | 48.4 % | 5 | 2:15 3:2 4:7 5:7 | | |
| — phase `grad` | | | | 1178 | 4092 | 3.474 | 13.2 % | 5 | 2:155 3:589 4:155 5:279 | | |
| — phase `grad_reconcile` | | | | 31 | 93 | 3.000 | 0.0 % | 3 | 3:31 | | |
| `large_tokamak_eval` | 2 | 2 + 23 = 25 | 0 (`fsolve`) | 11 | 29 | 2.455 | 72.7 % | 5 | 2:8 3:2 5:1 | 0 | 1.3 s |
| — phase `fn` | | | | 11 | 27 | 2.455 | 72.7 % | 5 | 2:8 3:2 5:1 | | |
| **`st_regression`** | — | — | — | **0** | **1** | — | — | — | — | 0 | crashed at 0.3 s |
| *(diag.)* `st_regression`, base input | 14 | 3 + 15 = 18 | 10 | 570 | 1891 | 3.314 | 13.9 % | 6 | 2:79 3:274 4:178 5:37 6:2 | 0 | 13.9 s |
| — phase `fn` | | | | 19 | 62 | 3.263 | 52.6 % | 6 | 2:10 3:1 4:3 5:3 6:2 | | |
| — phase `grad` | | | | 532 | 1776 | 3.338 | 11.8 % | 5 | 2:63 3:260 4:175 5:34 | | |
| — phase `grad_reconcile` | | | | 19 | 51 | 2.684 | 31.6 % | 3 | 2:6 3:13 | | |

Every scenario spends exactly **2** sweeps in the `output` phase — the final output-file
idempotence check converges at its floor every time. Those 2 sweeps are included in the
`sweeps` column and excluded from the per-phase rows, which is why the per-phase sweeps sum
to `sweeps − 2`.

The probe's own sweep counter agrees exactly with PROCESS's built-in `n_model_calls` in every
run, which is an independent check that the hook in `_call_models_once` fires once per sweep
and never twice.

### Wall clock, warm, serial (seconds inside `SingleRun.run`)

| Scenario | pristine | control | baseline | baseline rep 2 |
|---|---|---|---|---|
| `large_tokamak_nof` | 14.50 | 14.62 | 14.75 | 15.91 |
| `low_aspect_ratio_DEMO` | 34.30 | 34.15 | 31.77 | 31.09 |
| `large_tokamak_eval` | 1.24 | 1.27 | 1.26 | 1.28 |
| *(diag.)* `st_regression`, base input | 14.13 | 14.22 | 13.85 | 13.88 |

**Probe overhead is not resolvable at this sample size.** The `baseline`-minus-`control`
difference is +0.9 %, −7.0 % and −0.8 % on the three scenarios; the spread *between two
identical `baseline` runs* is up to 7.9 %. The overhead is smaller than run-to-run noise and
its sign is not consistent. I am not claiming it is zero; I am saying two runs per arm cannot
measure it, and the whole-MFILE identity result already establishes that it changes no
number.

A cold first run costs roughly 45–60 s extra (numba just-in-time compilation). The warm-up
run per tree is discarded, as the protocol requires.

### Final results, for later stages to compare against

| Scenario | `norm_objf` | `norm_objf`, hex | `sqsumsq` (equality-residual norm) |
|---|---|---|---|
| `large_tokamak_nof` | 1.6000000000277723 | `0x1.99999999b822dp+0` | 4.469e-09 |
| `low_aspect_ratio_DEMO` | −0.40629623022785516 | `-0x1.a00c1e7544537p-2` | 3.046e-14 |
| `large_tokamak_eval` | 0.928606022088452665 (from MFILE; `fsolve` has no objective) | — | 1.253e-12 |
| *(diag.)* `st_regression`, base input | −16.58857650779731 | `-0x1.096acf3342eefp+4` | 5.636e-14 |

`large_tokamak_nof`'s `sqsumsq` of 4.5e-09 is five orders of magnitude looser than the other
three. It is well inside the warning threshold (1e-2), so this is not a failure, but it means
a later stage comparing "at matched final accuracy" has much less headroom on that scenario
than on the others.

---

## 5. Environment

*I-1 is the issue-register entry for the editable install pointing at the wrong tree.*

**What I found.** `pip show process` reports
`Editable project location: /home/wrutten/dev_libraries/PROCESS` — a different clone, pinned
at the superseded commit `710a75c9`. The editable install is a plain path entry in
`_editable_impl_process.pth`, so `import process` resolves to the surgery tree only when the
current directory happens to be the repository root. Every probe run executes in its own
working directory, so left alone, every measurement would have come from the wrong code.

**What I did.** I set `PYTHONPATH` explicitly for every run. `PYTHONPATH` entries precede
site-packages `.pth` entries in `sys.path`, so the surgery tree wins. Proof, from a directory
that is not the repository root:

```
cwd             : /home/wrutten
process.__file__: /home/wrutten/projects/PROCESS_surgery/process/__init__.py
ASSERTION PASSED
```

`run_one.py` re-asserts this inside every run subprocess (`--expect-tree`) and aborts before
doing any work if the wrong tree was imported. The `pristine` arm asserts against the
pristine checkout in the same way. No measurement in this report could have come from the
wrong tree without the run aborting.

**What I did not do, and why.** I did not re-run the editable install. Two reasons. First,
`pip install -e` writes into `/home/wrutten/anaconda3/envs/PROCESS_env/lib/.../site-packages`,
which is outside the paths agents may write to; the standing rule is that the sandbox is
never overridden and environment changes are the user's to make. Second, re-pointing the
install would make `/home/wrutten/dev_libraries/PROCESS` — someone else's working clone —
no longer importable from `PROCESS_env`, which is a decision with consequences beyond this
task.

**The command that closes I-1 permanently**, for the user to run:

```bash
/home/wrutten/anaconda3/envs/PROCESS_env/bin/pip install -e \
  /home/wrutten/projects/PROCESS_surgery --no-deps --no-build-isolation
```

I-1 should stay **OPEN** until that is run. The `PYTHONPATH` mechanism is a per-run
guarantee, not a fix; anyone who runs `process ...` or `python -m process` by hand in this
environment still gets the wrong tree, silently.

**A side effect worth knowing about.** `process.__version__` comes from
`importlib.metadata`, which reads the *installed distribution's* metadata. Under the
`PYTHONPATH` workaround the MFILE header therefore records
`Version : 0.0.1.dev1152+g710a75c9d` — the other clone's version. The adjacent
`PROCESS_git_tag` and `PROCESS_git_branch` fields are read from the working tree and are
correct (`v3.4.2-…`, `A1-stage0-rebaseline`). Nothing numerical is affected. Every
`metrics.json` records `process_file`, `tree` and `tree_git_head` independently, so
provenance never rests on the MFILE header. Fixing I-1 fixes the version string too.

**Packages.** Nothing was missing and nothing was installed. The `PROCESS_env` environment
already satisfied every dependency, `click 8.5.0` included (the old notes mention
`click>=8.3.2` having been absent once; it is present now). **No change was made to any
conda environment.**

**Machine.** 16 cores, ~7 GB RAM. The final measured pass was run serially (`--jobs 1`) so
timings are not contaminated by contention; an earlier two-way-parallel pass produced the
same gate outcomes and the same sweep counts.

---

## 6. Autonomous decisions, and how to reverse them

| # | Decision | Why | Reversal |
|---|---|---|---|
| 1 | **Resolved I-1 with `PYTHONPATH` rather than re-installing.** | Site-packages is outside the writable sandbox and the standing rule forbids overriding it; re-pointing would break a sibling clone's use of the env. | Run the `pip install -e` command in §5. `run_stage0.py`'s `_env()` sets `PYTHONPATH`; it is harmless to leave in place afterwards. |
| 2 | **Added a fourth comparison arm, `pristine`** — an untouched `git archive` of `c0ae5b28` — beyond the `control` vs `baseline` pair the task specified. | Gate (a) asks for identity with "an uninstrumented run". Comparing the instrumented tree with the probe off against a tree that has never seen the probe is the stronger reading, and it costs one extra run per scenario. | Drop `("pristine", "pristine")` from `ARMS` in `run_stage0.py` and drop the `pristine` branches in `compare.py`. Gate (a) then compares `control` vs `baseline` only. |
| 3 | **Ran the scenarios with `update_obsolete=True`.** | Three of the four archived IN.DATs use variable names retired by the base commit (`minmax`, `neqns`, `ioptimz`) and are rejected outright without it. The rewrite is a pure rename, applied identically in every arm, so it cannot bias a comparison. | Set `update_obsolete=False` in `run_one.py` and update the scenario files to the base commit's names instead. |
| 4 | **Ran a separate diagnostic arm for `st_regression` using `tests/regression/input_files/st_regression.IN.DAT`.** | To distinguish a code failure from a stale input. Reported as a diagnostic; **gate (c) was left as FAIL** and no gate result was taken from it. | Delete `runs/st_regression__base_input/`. The `--input` flag on `run_one.py` can stay; it defaults to the archived scenario. |
| 5 | **Added a whole-MFILE identity check** alongside the named gate fields. | The named fields are a handful of numbers; a perturbation could hide in the other 16,000 lines. | Remove `mfile_identity` from `compare.py`. It is reported separately and no gate verdict depends on it. |
| 6 | **Left the superseded files in place** (`MEMO.md`, `NOISE_ANALYSIS.md`, `noise_probe.py`, `noise_deepdive.py`) and marked them stale in the README rather than deleting them. | They are another study's archive; deletion is not mine to decide. `noise_probe.py` and `noise_deepdive.py` import the old probe module and do not run against this tree. | Delete them, or leave them for A7 (repo-readme), which owns the staleness-header work (I-3). |
| 7 | **`arch_surgery/idf_probe/.gitignore` ignores `runs/`** rather than adding a rule to the repository-root `.gitignore`. | The root file is upstream PROCESS's and is shared with other work. | Delete the file and add `arch_surgery/idf_probe/runs/` to the root `.gitignore`. |

---

## 7. Things found in the code that bear on the partitioning hypothesis

Recorded, not investigated — Stage 1 (A2, module-convergence) owns this ground.

1. **The idempotence loop does real work: it is not sitting at its floor.** Across the three
   optimisation scenarios the mean is 3.2–3.5 sweeps per `call_models` against a structural
   floor of 2, and only 14–20 % of calls finish at the floor. Between **38 % and 42 % of all
   sweeps are above the floor** — that is the work a partition could in principle avoid.
   This is the headroom the whole hypothesis is aiming at, and it is real.

2. **Almost all of the cost is the finite-difference gradient.** 93–95 % of `call_models`
   invocations, and 94–96 % of all sweeps, are `grad` — the `2n` perturbations. The objective
   and constraint evaluations that VMCON actually iterates on are 2–3 % of the work. Any
   speedup that does not reduce the cost of a gradient perturbation is arithmetically capped
   at a few per cent. Note that this cuts *for* the plan's `k` economics argument (§3.1 of the
   experiment plan): a saving inside the perturbation loop is multiplied by `2n`.

3. **The `fn` phase converges much more readily than the `grad` phase.** The fraction of
   calls finishing at the 2-sweep floor is 47–53 % for `fn` but only 12–20 % for `grad`. The
   perturbed points the finite-difference loop presents are systematically harder to
   reconcile than the points VMCON actually visits. Whether that is a coupling effect or an
   artefact of stepping off the consistency manifold is exactly what Stage 1 must
   disentangle — and it matters, because §3.3 of the plan warns that sweep counts may be
   measuring the exit criterion rather than the coupling.

4. **`fcnvmc2`'s trailing consistency call is the most expensive single `call_models` in the
   run.** On `large_tokamak_nof` it never finishes at the floor (mean 3.93 sweeps, 14 of 15
   calls take 4). That call exists only to undo the last finite-difference perturbation. It
   is one call out of 630, so it is not a cost problem, but its cost is a clean signal that
   the model state carries memory of the previous point across a `call_models` boundary — the
   idempotence loop does not start from a clean slate.

5. **`low_aspect_ratio_DEMO`'s sweep histogram is bimodal** — 622 calls at 3 sweeps and 286
   at 5, with only 162 in between. The other scenarios decay monotonically. A bimodal
   distribution suggests two distinct convergence regimes rather than one; if a module-level
   attribution can say which module is still moving in the 5-sweep tail, that is a direct
   read on the laggard question (open question 1 in the queue).

6. **No solver retry fired anywhere.** `SolverHandler.run`'s three retry branches
   (`epsfcn × 10`, `epsfcn × 0.1`, Hessian reset) were never taken in any run, in any arm. So
   the baseline is retry-free and any retry a later stage provokes is attributable — but it
   also means **the retry hooks are untested at run time.** I verified them by inspection
   only; they have never executed.

7. **The measurement is on three scenarios, not four**, until the `st_regression` input is
   re-pinned. `st_regression` is the plan's free control for the steady-state case
   (`i_pulsed_plant = 0`), so its absence removes the one scenario in which the burn-time
   coupling edge is structurally absent. That matters for Stage 1's design, not just its
   coverage. The diagnostic run shows the scenario is healthy at `c0ae5b28` once the right
   input file is used — `nvar = 14`, 18 constraints, `ifail = 1`, and a sweep anatomy in line
   with the pulsed cases.

---

## 8. Registry state at `c0ae5b28`, for number-block reservation

The queue reserves ranges of iteration-variable and constraint numbers per experiment so
that two branches cannot allocate the same number and silently misread each other's
`IN.DAT` files, and it asks this task — the first to read both registries at the base
commit — to report the concrete first-free numbers. Here they are.

**Constraint equations** — registered by `@ConstraintManager.register_constraint(<n>, …)` in
`process/core/solver/constraints.py`:

| | |
|---|---|
| Registered | **82** equations |
| Range used | 1 – 92 |
| Unused numbers inside that range | 10, 38, 47, 49, 55, 57, 58, 69, 70, 71 (retired) |
| **First free number above the range** | **93** |
| Hard cap | `N_CONSTRAINT_EQUATIONS_MAX = 500` (the size of `numerics.icc`) |
| Headroom | 93 – 500, i.e. **408 numbers** |

There is one thing to do before number 93 is usable: `numerics.lablcc`, the list of
constraint descriptions, has exactly **92** entries, so it must be extended in step. It
carries a `TODO` warning that its comments are parsed by tooling, so extend it, do not
restructure it.

**Iteration variables** — keys of `ITERATION_VARIABLES` in
`process/core/solver/iteration_variables.py`:

| | |
|---|---|
| Registered | **83** variables |
| Range used | 1 – 177 |
| Unused numbers inside that range | **94** of them, first few: 8, 9, 14, 15, 21, 22, 24 – 28, 30, 32 – 36, … |
| **First free number above the range** | **none** |
| Hard cap | `N_ITERATION_VARIABLES_MAX = 177` — and it is the size of *both* `numerics.ixc` and `numerics.lablxc` |
| Headroom above the cap | **zero** |

**This is a constraint on the plan, and it should be settled before A4 (burn-time-lift) or
A9–A11 (subdriver lift) start.** Number 177 is taken
(`f_a_tf_turn_cable_space_extra_void`), and the cap equals it exactly. Adding an iteration
variable at `c0ae5b28` therefore requires one of:

1. **raise `N_ITERATION_VARIABLES_MAX`** to 178 or beyond, which resizes `ixc` and `lablxc`
   — a one-line change in `process/data_structure/numerics.py`, outside `process/models/`,
   so it does not breach the model freeze (D5); or
2. **reuse a retired number** from the 94 gaps. Cheaper, and *worse*: an existing `IN.DAT`
   naming a retired `ixc` would silently be reinterpreted as the new variable rather than
   rejected. I would not do this.

Option 1 is the safe one, and because the two lift experiments both need at least one new
iteration variable, whoever raises the cap first should raise it far enough for both blocks
rather than by one.

I have **not** allocated any block. That is the orchestrator's call, and it belongs in the
queue, not in a task report.

---

## 9. Change log

| Date | Entry |
|---|---|
| 2026-08-31 | Probe written (`process/core/_idf_probe.py` + hooks in `caller.py`, `solver/evaluators.py`, `solver/solver_handler.py`). `idf_probe/metrics.py` and `compare.py` rewritten for `c0ae5b28`; `run_one.py` rewritten; `run_stage0.py` added. `idf_probe/README.md` rewritten. I-1 worked around with `PYTHONPATH` and proved. Gates (a) and (b) PASS on all runnable scenarios; gate (c) FAILS on `st_regression` because the archived input file predates the base commit. Diagnostic arm with the base commit's own `st_regression` input passes all three gates. Report written. |
