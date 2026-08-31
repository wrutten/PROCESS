# `idf_probe` — the measurement instrument

**Base commit:** `c0ae5b28` · **Branch:** `A1-stage0-rebaseline` (off `architecture_surgery`)
· **Stage:** 0 (re-baseline)

This directory holds the instrument that measures how much work PROCESS's driver does, and
the scripts that run it. The experiment it serves is described in
[`../docs/MDA_PARTITION_EXPERIMENT.md`](../docs/MDA_PARTITION_EXPERIMENT.md); the Stage-0
result is in [`../docs/reports/A1_stage0_rebaseline.md`](../docs/reports/A1_stage0_rebaseline.md).

> **The directory name is historical.** *IDF* — individual discipline feasible — was the
> architecture the superseded study tested. This study tests a different thing: partitioning
> the global idempotence loop into per-module solvers. The name was kept so that existing
> links keep working.

> **Stale files.** `MEMO.md`, `NOISE_ANALYSIS.md`, `noise_probe.py` and `noise_deepdive.py`
> are artifacts of the superseded study at commit `710a75c9`. **No number in them is
> evidence** and the two scripts do not run against this tree. They are retained for
> methodology only.

---

## 1. What the probe measures

PROCESS's optimiser (VMCON) does not call the physics models directly. It calls
`Caller.call_models`, which is an **idempotence loop**: it runs the whole model sequence
(`Caller._call_models_once`, a *sweep*) repeatedly until the objective function and the
constraint vector stop changing between consecutive sweeps. The loop has a structural floor
of **two** sweeps — it must run twice before it has two values to compare — and a ceiling of
ten, after which it raises.

The probe counts that work and attributes it:

| Quantity | Meaning |
|---|---|
| **sweep** | one execution of `_call_models_once`, i.e. one pass over the model sequence |
| **`call_models`** | one execution of the idempotence loop; between 2 and 10 sweeps |
| **phase** | which part of the solver asked for this `call_models` |

The phases are:

| Phase | Where | What it is |
|---|---|---|
| `fn` | `Evaluators.fcnvmc1` | objective and constraint evaluation |
| `grad` | `Evaluators.fcnvmc2`, inner loop | one of the `2n` finite-difference perturbations |
| `grad_reconcile` | `Evaluators.fcnvmc2`, trailing call | the extra call that restores consistency with the unperturbed `x` after the finite differences |
| `output` | `Caller.call_models_and_write_output` | the final output-file idempotence check; these sweeps are not inside a `call_models` and are counted separately |

It also records solver retries (`SolverHandler.run` has three retry branches), and the run
records `nvar`, the constraint counts, `ifail`, `norm_objf`, the constraint residual norm and
the final iteration variables.

Stage 0 implements exactly one probe mode, `baseline`: **record, change nothing**. The
control flow with the probe on is identical to the control flow with it off.

---

## 2. Change manifest

Four files in `process/`. Nothing under `process/models/` is touched — the models are frozen
at the base commit.

| File | Change |
|---|---|
| `process/core/_idf_probe.py` | **new.** All probe state and logic. Reads `PROCESS_IDF_PROBE` once, at import. |
| `process/core/caller.py` | 4 hooks: `call_models` entry, its converged return, its non-converged `raise`, and one in `_call_models_once`. Plus one import. |
| `process/core/solver/evaluators.py` | 3 hooks: phase marker at the top of `fcnvmc1`, at the top of `fcnvmc2`, and before `fcnvmc2`'s trailing consistency call. Plus one import. |
| `process/core/solver/solver_handler.py` | 3 hooks, one at each retry branch in `SolverHandler.run`. Plus one import. |

**Every hook has the same shape:**

```python
if _idf_probe.ENABLED:
    _idf_probe.<something>()
```

`ENABLED` is a module-level `bool` fixed at import time from the environment. With
`PROCESS_IDF_PROBE` unset the disabled path is a single global load and a branch: no
floating-point work, no state mutation, no allocation. That is gate (a), and it is verified
by measurement, not by inspection — see §5.

An unrecognised value of `PROCESS_IDF_PROBE` raises at import rather than silently disabling
the probe, so a typo cannot masquerade as a control run.

---

## 3. Running it — the setup trap first

**Read this before running anything.** In this environment `pip show process` reports

```
Editable project location: /home/wrutten/dev_libraries/PROCESS
```

which is a **different clone at a different commit**. `import process` resolves to the
surgery tree only when the current directory happens to be the repository root — and every
probe run executes in its own working directory. Left alone, every measurement would
silently come from the wrong code. This is issue **I-1** in the queue.

The workaround used by these scripts is to set `PYTHONPATH` explicitly for every run.
`PYTHONPATH` entries precede site-packages `.pth` entries in `sys.path`, so the surgery tree
wins. `run_one.py` then **asserts** which tree it actually imported (`--expect-tree`) and
aborts if it is the wrong one. Prove it yourself from a directory that is not the repo root:

```bash
cd /tmp && PYTHONPATH=/home/wrutten/projects/PROCESS_surgery \
  /home/wrutten/anaconda3/envs/PROCESS_env/bin/python -c \
  "import process, pathlib; p = pathlib.Path(process.__file__).resolve(); print(p); \
   assert pathlib.Path('/home/wrutten/projects/PROCESS_surgery') in p.parents"
```

The permanent fix is for the user to re-point the editable install (it writes into
site-packages, which agents may not touch):

```bash
/home/wrutten/anaconda3/envs/PROCESS_env/bin/pip install -e \
  /home/wrutten/projects/PROCESS_surgery --no-deps --no-build-isolation
```

Note that this would make `/home/wrutten/dev_libraries/PROCESS` no longer importable from
`PROCESS_env`, which is why it is the user's decision and not an agent's.

A side effect of the `PYTHONPATH` workaround: `process.__version__` comes from
`importlib.metadata`, so the MFILE header records the *installed distribution's* version
(`0.0.1.dev1152+g710a75c9d`, from the other clone) rather than this tree's. The MFILE's
`PROCESS_git_tag` / `PROCESS_git_branch` fields, which are read from the working tree, are
correct. Nothing numerical is affected; the version string is cosmetic. Every
`metrics.json` records `process_file`, `tree` and `tree_git_head` so provenance never
depends on the MFILE header.

### Isolation

**Every run is a fresh subprocess in its own working directory.** This is not tidiness:
`OutputFileManager` holds its file handles as *class* attributes (process-wide) and
`init.init_process` mutates a global data structure, so two PROCESS runs in one interpreter
contaminate each other. `run_stage0.py` enforces it.

**Discard the first run in a fresh environment for timing.** Numba compiles on first use; a
cold run costs roughly 45–60 s more than a warm one. `run_stage0.py` does a warm-up run per
tree and throws it away. The numba cache lives in `__pycache__` next to the source, so each
tree warms separately.

### Commands

```bash
# 1. Take a pristine checkout of the base commit, for the switch-neutrality gate.
mkdir -p /tmp/pristine && git archive c0ae5b28 | tar -x -C /tmp/pristine

# 2. Warm the caches and run every (scenario, arm) pair.  --jobs 1 for clean timings.
cd arch_surgery/idf_probe
/home/wrutten/anaconda3/envs/PROCESS_env/bin/python run_stage0.py \
    --pristine-tree /tmp/pristine --jobs 1

# 3. Evaluate the gates and print the sweep-anatomy table.
PYTHONPATH=/home/wrutten/projects/PROCESS_surgery \
  /home/wrutten/anaconda3/envs/PROCESS_env/bin/python compare.py
```

One run on its own:

```bash
PYTHONPATH=/home/wrutten/projects/PROCESS_surgery \
  /home/wrutten/anaconda3/envs/PROCESS_env/bin/python run_one.py \
    --scenario large_tokamak_nof --mode baseline --outdir runs/scratch \
    --expect-tree /home/wrutten/projects/PROCESS_surgery
```

`--mode control` leaves `PROCESS_IDF_PROBE` unset; `--mode baseline` sets it. A `_repN`
suffix marks a replicate and is stripped before the value reaches the probe.

### Arms

| Arm | Tree | `PROCESS_IDF_PROBE` | Purpose |
|---|---|---|---|
| `pristine` | untouched checkout of `c0ae5b28` | unset | reference for gate (a) |
| `control` | this tree | unset | the disabled path |
| `baseline` | this tree | `baseline` | the instrumented path |
| `baseline_rep2` | this tree | `baseline` | reference for gate (b) |

### Scenarios

The four IN.DATs in [`scenarios/`](scenarios/). They were archived from the superseded study
at `710a75c9`. Three of them differ from the base commit's own regression inputs
(`tests/regression/input_files/`) **only** by variable renames, which `run_one.py` applies
automatically (`update_obsolete=True`). `st_regression` differs substantively and does not
run at `c0ae5b28` — see the Stage-0 report.

---

## 4. Output

One `metrics.json` per run, at `runs/<scenario>/<arm>/metrics.json`, alongside the run's
own `IN.DAT`, `OUT.DAT`, `MFILE.DAT` and logs. `compare.py` writes `runs/_gates.json`.

**`runs/` is not committed** (`.gitignore` here). It is roughly 80 MB for a full set of arms and is
fully regenerable. Summaries and verdicts go in the task report.

Each `metrics.json` carries:

- provenance — `process_file`, `tree`, `tree_git_head`, `pythonpath`, `input_file`;
- problem size — `nvar`, `n_equality_constraints`, `n_inequality_constraints`,
  `n_solver_iterations`, `solver_name`;
- results — `values` (readable floats) and `exact` (**hex float literals**, i.e. exact
  IEEE-754 doubles, which is what the bit-identity gates compare);
- `mfile` — the same quantities re-read from `MFILE.DAT`, plus the raw ASCII fields;
- `probe` — the rollup: totals, per-phase blocks, sweep histograms, retries.

---

## 5. The Stage-0 gates

`compare.py` evaluates four things:

- **(a) switch-neutrality** — `pristine`, `control` and `baseline` must be **identical**,
  not close. Compared on hex float literals.
- **(b) determinism** — `baseline` and `baseline_rep2` must agree exactly, results *and*
  sweep counts.
- **(c) baseline solves** — every scenario returns `ifail = 1`.
- **whole-MFILE identity** — a stronger form of (a) and (b) that is not one of the named
  gates: every line of the ~16,000-line MFILE must match across all four arms, excluding the
  run-metadata header (date, time, user, host, paths, git tag/branch, runtime).

A failed gate is a result. It is reported with its numbers and never tuned into passing.

---

## 6. Files

| File | Status |
|---|---|
| `_idf_probe.py` is in `process/core/` | the probe itself |
| `run_one.py` | one scenario, one arm, one subprocess. Asserts the imported tree. |
| `run_stage0.py` | warms the caches, then drives every (scenario, arm) pair |
| `metrics.py` | MFILE parsing and rollups. **Rewritten** for `c0ae5b28`: the rename in that commit killed the old key names (`nvar`, `neqns`, `nineqns`, `ncalls`, `nviter`). |
| `compare.py` | **Rewritten.** The Stage-0 gate checker. |
| `scenarios/` | the four archived IN.DATs |
| `MEMO.md`, `NOISE_ANALYSIS.md`, `noise_probe.py`, `noise_deepdive.py` | **stale**, superseded study, do not run |
