> **Document status** — **ARCHIVED · CURRENT**
> A merged task report, archived per protocol §7 because its task closed — **not because it is
> stale.** It describes commit **`c0ae5b28`** and is **the authoritative Stage-0 baseline**: every
> later stage compares against the numbers here. Position in `deprecated/` records lifecycle, not
> validity; the stale documents in this folder say so explicitly in their own headers.

# A1 (stage0-rebaseline) — Stage 0 re-baseline at `c0ae5b28`

| | |
|---|---|
| **Task** | A1 (stage0-rebaseline) |
| **Branch** | `A1-stage0-rebaseline`, off `architecture_surgery` |
| **Base commit** | `c0ae5b28` |
| **Stage** | 0 of [`../MDA_PARTITION_EXPERIMENT.md`](../MDA_PARTITION_EXPERIMENT.md) |
| **Environment** | `PROCESS_surgery_env` |
| **Date** | 2026-08-31 (re-gated after decision D9) |
| **Status** | Complete — **all three gates pass on all four scenarios** |

---
## 1. Verdict

The measurement apparatus is re-established at the base commit and **all three Stage-0 gates
pass on all four scenarios**.

| Gate | Result |
|---|---|
| **(a) Switch-neutrality** — probe off vs. probe on vs. untouched base commit | **PASS**, 4 / 4. Not merely within tolerance: every one of the ~16,000–18,700 lines of the MFILE is byte-identical across all eleven arms, once the run-metadata header is excluded. |
| **(b) Determinism** — independent runs agree exactly | **PASS**, 4 / 4, over **five** independent replicates per scenario. Results identical bit-for-bit and sweep counts identical to the last sweep. |
| **(c) Baseline solves** — `ifail = 1` everywhere | **PASS**, 4 / 4. |

*`ifail` is PROCESS's solver return code; `ifail = 1` means a feasible (or, for an evaluation
run, consistent) solution was found.*

### What changed since the first submission

The first revision of this report held gate (c) at **FAIL** on `st_regression`: the archived
scenario raised in the cable-in-conduit TF-coil model before the optimiser completed its first
function evaluation, and it did so on an untouched checkout of the base commit as well, so it
was never the probe's doing. The cause was a **stale input file** — the deck was archived from
the superseded study at `710a75c9` and had fallen behind `c0ae5b28`.

Two rulings arrived and both are now discharged:

- **D9 — patch the deck in place.** The scenario deck stays a frozen artifact of this study
  rather than tracking whatever upstream ships, so `st_regression.IN.DAT` was patched rather
  than re-pointed at `tests/regression/input_files/`. Five keys were added; §3.4 lists them
  and where each came from. With the patch the scenario solves at `ifail = 1` and passes all
  three gates, and its results are **bit-identical** to the diagnostic run made against the
  base commit's own input file — which is the check that the patch is equivalent rather than
  merely working.
- **I-1 closed — the environment was fixed by the user.** All the numbers below come from
  `PROCESS_surgery_env`, whose editable install points at this tree. The `PYTHONPATH`
  workaround has been removed from the harness. §5 has the detail.

Per protocol §6 the whole task was re-gated as one merge, not just the scenario that failed:
patching an input is not supposed to disturb gates (a) or (b), and demonstrating that is the
point. It did not.

### One thing D9 uncovered that nobody had noticed

**The scenario deck was never under version control.** Attempting to commit the D9 patch
revealed that `arch_surgery/idf_probe/scenarios/*.IN.DAT` is matched by the repository-root
`.gitignore`'s blanket `*.DAT` rule, and `git ls-files` on that directory returned nothing.
All four scenario files existed only in the working tree, on this machine.

This is not a consequence of the patch; it predates this task. But it makes D9's premise —
"the deck is a frozen artifact of this study" — untrue as stated: a deck that is not in
version control is not frozen, cannot be reviewed, and would be absent from any clone of this
branch. **Stage 0 was, until this commit, not reproducible by anyone else.**

Upstream's `.gitignore` already handles this shape of problem by un-ignoring its own input
decks by name (`!tests/regression/input_files/*.IN.DAT` and two others). I added the
equivalent scoped rule to `arch_surgery/idf_probe/.gitignore` and committed the four files
(§6, decision 10). This is a change I made without asking, because D9 is not implementable
without it; the reversal is two commands and is listed.

### Two things the re-run made worse, not better

1. **Wall-clock noise is larger than the first revision reported.** With `n = 5` per arm
   instead of `n = 2`, the within-arm spread reaches **19.6 %** on `low_aspect_ratio_DEMO`,
   not the 7.9 % first seen. Issue I-8 is therefore understated in the assessment: the noise
   band straddles the Stage-1 gate thresholds (proceed above 25 %, stop below 10 %) rather
   than merely approaching them. §4 carries the numbers and the repetition count behind every
   figure.
2. **`st_regression` is not the cheap free control the plan assumes.** It solves, and its
   sweep anatomy is unremarkable — but see §7, finding 8: with `i_pulsed_plant = 0` it shows
   the *same* above-floor sweep fraction as the pulsed cases, which is a result the plan's
   §2.3 does not predict.

Nothing else surprised me in a bad way. The probe's overhead is not statistically
distinguishable from zero on any scenario, the solver is exactly reproducible, and no scenario
needed a solver retry.

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

All runs: `PROCESS_surgery_env`, warm caches, executed serially (`--jobs 1`), one fresh
subprocess in its own working directory per run. Eleven arms per scenario — one `pristine`,
five `control`, five `baseline`.

### 3.1 (a) Switch-neutrality — PASS, 4 / 4

Three kinds of arm compared: `pristine` (an untouched `git archive` of `c0ae5b28`, in which
the probe module does not exist at all), `control` (this tree, `PROCESS_IDF_PROBE` unset) and
`baseline` (this tree, `PROCESS_IDF_PROBE=baseline`).

Compared on **hex float literals** — exact IEEE-754 doubles — so "identical" means identical,
with no re-parsing tolerance anywhere in the chain.

| Scenario | differing fields, pristine vs control | pristine vs baseline | MFILE lines compared | differing MFILE lines, all 10 arms vs pristine |
|---|---|---|---|---|
| `large_tokamak_nof` | none | none | 16,174 | 0 |
| `low_aspect_ratio_DEMO` | none | none | 16,435 | 0 |
| `st_regression` | none | none | 18,692 | 0 |
| `large_tokamak_eval` | none | none | 15,917 | 0 |

The fields compared are `norm_objf` (the normalised objective function), the full vector of
final iteration variables, `sqsumsq` (the root-sum-square of the equality-constraint
residuals), the L2 norm of the full constraint vector, and the raw ASCII MFILE fields.

The whole-MFILE check is stronger than the gate requires and is reported because it is the one
that would catch a perturbation the named quantities miss: every line, excluding only the
run-metadata header (date, time, user, host, paths, git tag and branch, wall-clock runtime),
matches across all eleven arms. `large_tokamak_eval` is an evaluation run solved by `fsolve`,
which has no objective function, so its in-memory `norm_objf` is `None`; for that scenario the
objective comparison is carried by the MFILE's raw `norm_objf` field
(`9.28606022088452665e-01`), which is present and identical.

### 3.2 (b) Determinism — PASS, 4 / 4

Five independent `baseline` runs per scenario, each a separate subprocess in a separate
working directory. Every replicate is compared against the first.

| Scenario | replicates | differing replicates | sweeps, all five runs |
|---|---|---|---|
| `large_tokamak_nof` | 5 | none | 2029, 2029, 2029, 2029, 2029 |
| `low_aspect_ratio_DEMO` | 5 | none | 4286, 4286, 4286, 4286, 4286 |
| `st_regression` | 5 | none | 1891, 1891, 1891, 1891, 1891 |
| `large_tokamak_eval` | 5 | none | 29, 29, 29, 29, 29 |

Results agree bit-for-bit and the sweep histograms agree entry for entry. No thread-count or
BLAS environment variables were pinned — determinism holds as the code stands.

### 3.3 (c) Baseline solves — PASS, 4 / 4

| Scenario | `ifail` | `nvar` | constraints | `norm_objf` |
|---|---|---|---|---|
| `large_tokamak_nof` | 1 | 20 | 26 | 1.6000000000277723 |
| `low_aspect_ratio_DEMO` | 1 | 19 | 25 | −0.40629623022785516 |
| `st_regression` | 1 | 14 | 18 | −16.58857650779731 |
| `large_tokamak_eval` | 1 | 2 | 25 | 0.928606022088452665 (from MFILE; `fsolve` has no objective) |

### 3.4 The D9 patch to `st_regression.IN.DAT`

**What was wrong.** The archived file set `i_tf_sc_mat = 9` (Hazelton-Zhai REBCO, a *tape*
superconductor) but did not set `i_tf_turn_type`, which defaults to `1`, cable-in-conduit. At
`c0ae5b28` `Caller._call_models_once` dispatches the TF-coil model on `i_tf_turn_type`, so a
tape material was handed to the cable-in-conduit model, which raises:

> `ProcessValueError: Cannot calculate cable in conduit superconductor properties for
> non-cable superconductors.`

**What was added.** Five keys, copied verbatim from
`tests/regression/input_files/st_regression.IN.DAT` at `c0ae5b28` — the base commit's own copy
of the same scenario. Nothing else in the file changed.

| Key | Value | Inserted | Purpose |
|---|---|---|---|
| `dx_tf_hts_tape_rebco` | `1.0e-6` | TF Coil section, before the *General settings* banner | REBCO layer thickness |
| `dx_tf_croco_strand_copper` | `2.0e-3` | ” | CroCo strand copper thickness |
| `dx_tf_hts_tape_copper` | `2.0e-4` | ” | tape copper thickness |
| `dx_tf_hts_tape_hastelloy` | `1e-5` | ” | tape Hastelloy thickness |
| `i_tf_turn_type` | `2` | after `n_tf_coils`, before `i_tf_shape` | CroCo turn geometry for HTS tapes — the key that routes the model dispatch correctly |

Both insertions carry a `* D9 PATCH …` provenance comment **in the file itself**, naming the
date, the source file and the commit, so the patch is auditable against upstream without
reading this report.

**Auditing the patch.** After patching, the archived file differs from
`tests/regression/input_files/st_regression.IN.DAT` at `c0ae5b28` by exactly: the three
obsolete-name lines that `update_obsolete=True` rewrites at run time (`ioptimz`, `minmax`,
`neqns`), the eight lines of `* D9 PATCH` provenance comment, and one pre-existing trailing
space. **No value-bearing key differs.**

**Evidence that the patch is equivalent, not merely sufficient.** The first revision of this
report ran a diagnostic arm using the base commit's own input file. The patched archived file
reproduces that run exactly — `norm_objf` hex `-0x1.096acf3342eefp+4`, 1891 sweeps, 570
`call_models`, `nvar = 14` — so the patch reproduces the reference input's behaviour rather
than merely producing *some* converged answer. The MFILE is 11 lines longer than the
diagnostic's, and all 11 are accounted for: the input file is echoed into the MFILE, so the
8 lines of `* D9 PATCH` provenance comment appear there, plus the 3 `* Replaced …` lines
`update_obsolete` writes for `ioptimz`, `minmax` and `neqns`. No physics line differs.

---
## 4. Sweep anatomy

Baseline arm, warm caches, serial execution. Sweep counts are exact integers and identical
across all five replicates (§3.2), so they carry no error bar; **the wall clock does, and is
reported separately in §4.2 with its repetition count.**

### 4.1 Sweeps

| Scenario | `nvar` | constraints (eq + ineq) | VMCON iterations | `call_models` | sweeps | mean sweeps / `call_models` | at the 2-sweep floor | max | histogram | retries |
|---|---|---|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 20 | 3 + 23 = 26 | 8 | 630 | 2029 | 3.217 | 20.2 % | 6 | 2:127 3:276 4:191 5:35 6:1 | 0 |
| — phase `fn` | | | | 15 | 53 | 3.533 | 46.7 % | 6 | 2:7 4:2 5:5 6:1 | |
| — phase `grad` | | | | 600 | 1915 | 3.192 | 20.0 % | 5 | 2:120 3:275 4:175 5:30 | |
| — phase `grad_reconcile` | | | | 15 | 59 | 3.933 | 0.0 % | 4 | 3:1 4:14 | |
| `low_aspect_ratio_DEMO` | 19 | 4 + 21 = 25 | 16 | 1240 | 4286 | 3.455 | 13.7 % | 5 | 2:170 3:622 4:162 5:286 | 0 |
| — phase `fn` | | | | 31 | 99 | 3.194 | 48.4 % | 5 | 2:15 3:2 4:7 5:7 | |
| — phase `grad` | | | | 1178 | 4092 | 3.474 | 13.2 % | 5 | 2:155 3:589 4:155 5:279 | |
| — phase `grad_reconcile` | | | | 31 | 93 | 3.000 | 0.0 % | 3 | 3:31 | |
| `st_regression` | 14 | 3 + 15 = 18 | 10 | 570 | 1891 | 3.314 | 13.9 % | 6 | 2:79 3:274 4:178 5:37 6:2 | 0 |
| — phase `fn` | | | | 19 | 62 | 3.263 | 52.6 % | 6 | 2:10 3:1 4:3 5:3 6:2 | |
| — phase `grad` | | | | 532 | 1776 | 3.338 | 11.8 % | 5 | 2:63 3:260 4:175 5:34 | |
| — phase `grad_reconcile` | | | | 19 | 51 | 2.684 | 31.6 % | 3 | 2:6 3:13 | |
| `large_tokamak_eval` | 2 | 2 + 23 = 25 | 0 (`fsolve`) | 11 | 29 | 2.455 | 72.7 % | 5 | 2:8 3:2 5:1 | 0 |
| — phase `fn` | | | | 11 | 27 | 2.455 | 72.7 % | 5 | 2:8 3:2 5:1 | |

Every scenario spends exactly **2** sweeps in the `output` phase — the final output-file
idempotence check converges at its floor every time. Those 2 sweeps are included in the
`sweeps` column and excluded from the per-phase rows, which is why the per-phase sweeps sum to
`sweeps − 2`.

The probe's own sweep counter agrees exactly with PROCESS's built-in `n_model_calls` in every
run (2029, 4286, 1891, 29), which is an independent check that the hook in
`_call_models_once` fires once per sweep and never twice.

Derived shares, quoted in §7:

| Scenario | `grad` share of `call_models` | `grad` share of sweeps | sweeps above the 2-sweep floor | `sqsumsq` |
|---|---|---|---|---|
| `large_tokamak_nof` | 95.2 % | 94.5 % | 37.8 % | 4.469e-09 |
| `low_aspect_ratio_DEMO` | 95.0 % | 95.5 % | 42.1 % | 3.046e-14 |
| `st_regression` | 93.3 % | 94.0 % | 39.7 % | 5.636e-14 |
| `large_tokamak_eval` | 0 % (no gradient: `fsolve`) | 0 % | 18.5 % | 1.253e-12 |

`large_tokamak_nof`'s `sqsumsq` of 4.5e-09 is five orders of magnitude looser than the other
three. It is well inside the code's warning threshold (1e-2), so this is not a failure, but a
later stage comparing "at matched final accuracy" has much less headroom on that scenario.

### 4.2 Wall clock — with the repetition count, per I-8

**Every figure here is `n = 5`** independent runs, each a fresh subprocess in its own working
directory, executed serially on an otherwise idle machine, warm caches. `pristine` is `n = 1`
and is shown only for orientation: it is an identity reference, not a timing arm.

| Scenario | arm | n | mean (s) | sd (s) | min | max | within-arm spread |
|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | pristine | 1 | 15.50 | — | — | — | — |
| | control | 5 | 14.67 | 0.53 | 14.10 | 15.36 | 8.5 % |
| | baseline | 5 | 14.31 | 0.17 | 14.17 | 14.58 | 2.9 % |
| `low_aspect_ratio_DEMO` | pristine | 1 | 31.57 | — | — | — | — |
| | control | 5 | 30.72 | 1.09 | 29.62 | 32.13 | 8.2 % |
| | baseline | 5 | 32.82 | 2.76 | 30.21 | 36.65 | **19.6 %** |
| `st_regression` | pristine | 1 | 13.59 | — | — | — | — |
| | control | 5 | 14.33 | 0.81 | 13.15 | 15.24 | 14.6 % |
| | baseline | 5 | 13.66 | 0.75 | 13.20 | 14.99 | 13.1 % |
| `large_tokamak_eval` | pristine | 1 | 1.22 | — | — | — | — |
| | control | 5 | 1.26 | 0.03 | 1.22 | 1.30 | 5.9 % |
| | baseline | 5 | 1.25 | 0.03 | 1.21 | 1.29 | 5.9 % |

**Probe overhead is not distinguishable from zero on any scenario.** The difference of means,
with a Welch two-standard-error band:

| Scenario | baseline − control | ± 2 SE | significant? | worst within-arm spread |
|---|---|---|---|---|
| `large_tokamak_nof` | −2.47 % | 3.38 % | no | 8.5 % |
| `low_aspect_ratio_DEMO` | +6.83 % | 8.65 % | no | 19.6 % |
| `st_regression` | −4.70 % | 6.92 % | no | 14.6 % |
| `large_tokamak_eval` | −0.95 % | 2.96 % | no | 5.9 % |

The sign is not even consistent: three scenarios come out *faster* with the probe on. I am not
claiming the overhead is zero — I am saying that at `n = 5` it is below the floor this
machine can resolve, and that the whole-MFILE identity result in §3.1 already establishes that
it changes no number.

**This sharpens I-8 rather than settling it.** With `n = 2` the first revision reported a
7.9 % spread; with `n = 5` the worst within-arm spread is **19.6 %**, and the two-standard-
error band on a difference of means is 3–9 %. The Stage-1 gate in the experiment plan is
"predicted saving > 25 % → proceed" with a stop rule at "< 10 %". **A 10 % effect is not
measurable on this machine at `n = 5`**, and a 25 % effect would be measurable only with a
comfortable margin. Before A2 quotes any timing it needs either a repetition count chosen
from a target minimum detectable effect, or a lower-variance metric than wall clock — sweep
counts, which are exact, are the obvious candidate for the mechanism, with wall clock reserved
for the headline and quoted with its interval.

A cold first run costs roughly 20–45 s extra (numba just-in-time compilation). The warm-up run
per tree is discarded, as the protocol requires.

### 4.3 Final results, for later stages to compare against

| Scenario | `norm_objf` | `norm_objf`, hex | `sqsumsq` (equality-residual norm) |
|---|---|---|---|
| `large_tokamak_nof` | 1.6000000000277723 | `0x1.99999999b822dp+0` | 4.469e-09 |
| `low_aspect_ratio_DEMO` | −0.40629623022785516 | `-0x1.a00c1e7544537p-2` | 3.046e-14 |
| `st_regression` | −16.58857650779731 | `-0x1.096acf3342eefp+4` | 5.636e-14 |
| `large_tokamak_eval` | 0.928606022088452665 (from MFILE; `fsolve` has no objective) | — | 1.253e-12 |

---
## 5. Environment

*I-1 was the issue-register entry for the editable install pointing at the wrong tree.*
**It is now closed.**

### 5.1 What was wrong, and how it was fixed

`pip show process` in `PROCESS_env` reported
`Editable project location: /home/wrutten/dev_libraries/PROCESS` — a different clone, pinned
at the superseded commit `710a75c9`. The editable install was a plain path entry in a `.pth`
file, so `import process` resolved to the surgery tree only when the current directory
happened to be the repository root. Every probe run executes in its own working directory, so
left alone, every measurement would have come from the wrong code.

I first worked around this with `PYTHONPATH`, which precedes site-packages `.pth` entries in
`sys.path`, and proved it from a non-repo-root directory. **The user has since created
`PROCESS_surgery_env`, whose editable install points at this tree**, which is the real fix and
was always theirs to make — `pip install -e` writes into site-packages, outside the paths
agents may write to, and re-pointing the old environment would have broken a sibling clone's
use of it.

**Every number in this report comes from `PROCESS_surgery_env`**
(`/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python`, Python 3.12.14). Verified from
`/tmp`:

```
process.__file__: /home/wrutten/projects/PROCESS_surgery/process/__init__.py
version:          3.4.3.dev8+g3a8d2af99.d20260831
```

The version string now derives from this tree's own HEAD rather than a foreign clone's, which
retires the last residue the workaround left behind. (It is baked at install time by
`hatch-vcs`, so it names the commit the environment was created at, `3a8d2af9`, not
necessarily the commit under test; the MFILE's adjacent `PROCESS_git_tag` and
`PROCESS_git_branch` fields are read live from the working tree and are exact.)

### 5.2 What changed in the harness

- The interpreter is now `PROCESS_surgery_env`'s.
- **`PYTHONPATH` injection was removed** from `run_stage0.py`'s `_env()` for the surgery
  arms: those runs now resolve `process` exactly the way every later stage will.
- `PYTHONPATH` is still set for the **`pristine` arm alone**, because that arm imports a
  throwaway `git archive` of `c0ae5b28` which is not installed in any environment and cannot
  be reached otherwise. `_env()` sets it only when the tree is not the installed one. This is
  not a residue of the workaround; it is the only way to point at an uninstalled tree.
- **The in-subprocess assertion stays**, and is now a standing rule rather than a defensive
  choice: `run_one.py` checks `process.__file__` against `--expect-tree` and aborts before
  doing any work if it is wrong. Every arm is covered, including `pristine`. **No measurement
  in this report could have come from the wrong tree without the run aborting.**

Dropping `PYTHONPATH` broke nothing. The numba caches carried over unchanged (the warm-up run
in the new environment took 21 s, in line with a warm run, not the 45–60 s of a cold one).

### 5.3 The environment switch changed no number

This is checkable rather than assumed. Every scalar this report gates on is bit-identical
between the two environments:

| Scenario | `norm_objf` hex | sweeps | both environments? |
|---|---|---|---|
| `large_tokamak_nof` | `0x1.99999999b822dp+0` | 2029 | yes |
| `low_aspect_ratio_DEMO` | `-0x1.a00c1e7544537p-2` | 4286 | yes |
| `st_regression` | `-0x1.096acf3342eefp+4` | 1891 | yes |
| `large_tokamak_eval` | MFILE `9.28606022088452665e-01` | 29 | yes |

The comparison is against the figures recorded in the previous revision of this report (in
git history at commit `d50b5fd0`, and for `st_regression` against that revision's base-input
diagnostic arm); the raw `PROCESS_env` run artifacts were deleted when `runs/` was cleared for
the re-gate, so this is a comparison of recorded values, not of files still on disk. The
numerically relevant packages are identical in the two environments — `numpy 2.5.2`,
`scipy 1.18.1`, `numba 0.67.0`, `llvmlite 0.49.0`, `CoolProp 8.0.0` — which is the reason to
expect this, and the bit-identity is the confirmation.

### 5.4 Packages, machine, isolation

Nothing was missing and **nothing was installed by me; no conda environment was created or
modified by me.** `PROCESS_surgery_env` was created by the user.

Machine: 16 cores, ~7 GB RAM. Every run is a fresh subprocess in its own working directory —
`OutputFileManager` holds its file handles as *class* attributes (process-wide) and
`init.init_process` mutates a global data structure, so two PROCESS runs in one interpreter
contaminate each other. The measured pass was executed serially (`--jobs 1`) so timings are
not contaminated by contention.

**One harness note worth recording.** Launching the run suite as a background command did not
work in this session: the backgrounded shell reported success, but its filesystem writes were
discarded and no run artifacts survived. All measured runs were therefore executed in the
foreground, one scenario at a time. Nothing was measured from a discarded run — the failure
was total and obvious, not partial.

---
## 6. Autonomous decisions, and how to reverse them

| # | Decision | Why | Reversal |
|---|---|---|---|
| 1 | ~~Resolved I-1 with `PYTHONPATH` rather than re-installing.~~ **Superseded.** The user created `PROCESS_surgery_env`; the workaround is gone from the harness and I-1 is closed. | Site-packages is outside the writable sandbox and the standing rule forbids overriding it; re-pointing the old env would have broken a sibling clone. | n/a — retired. `PYTHONPATH` survives only for the `pristine` arm, which imports an uninstalled tree (§5.2). |
| 2 | **Added a fourth kind of comparison arm, `pristine`** — an untouched `git archive` of `c0ae5b28` — beyond the `control` vs `baseline` pair the task specified. | Gate (a) asks for identity with "an uninstrumented run". Comparing the instrumented tree with the probe off against a tree that has never seen the probe is the stronger reading, and it costs one extra run per scenario. | Drop `("pristine", "pristine")` from `build_arms` in `run_stage0.py` and the `pristine` branches in `compare.py`. Gate (a) then compares `control` vs `baseline` only. |
| 3 | **Ran the scenarios with `update_obsolete=True`.** *Accepted by the coordinator.* | Three of the four archived IN.DATs use variable names retired by the base commit (`minmax`, `neqns`, `ioptimz`) and are rejected outright without it. The rewrite is a pure rename, applied identically in every arm, so it cannot bias a comparison. | Set `update_obsolete=False` in `run_one.py` and rename the keys in the scenario files instead. |
| 4 | ~~Ran a separate diagnostic arm for `st_regression` using the base commit's input.~~ **Discharged by D9.** The archived file is now patched in place and the diagnostic arm is deleted. | It distinguished a code failure from a stale input, which is what produced D9. | The diagnostic is reproducible with `run_one.py --input tests/regression/input_files/st_regression.IN.DAT`; the `--input` flag remains. |
| 5 | **Added a whole-MFILE identity check** alongside the named gate fields. | The named fields are a handful of numbers; a perturbation could hide in the other 16,000 lines. | Remove `mfile_identity` from `compare.py`. It is reported separately and no gate verdict depends on it. |
| 6 | **Left the superseded files in place** (`MEMO.md`, `NOISE_ANALYSIS.md`, `noise_probe.py`, `noise_deepdive.py`) and marked them stale in the README rather than deleting them. | They are another study's archive; deletion is not mine to decide. The two scripts import the old probe module and do not run against this tree. | Delete them, or leave them for A7 (repo-readme), which owns the staleness-header work (I-3). |
| 7 | **`arch_surgery/idf_probe/.gitignore` ignores `runs/`** rather than adding a rule to the repository-root `.gitignore`. | The root file is upstream PROCESS's and is shared with other work. | Delete the file and add `arch_surgery/idf_probe/runs/` to the root `.gitignore`. |
| 8 | **Five replicates per arm, not two**, and every wall-clock figure carries `n`, sd, spread and a Welch two-standard-error band. | I-8: a single run is not a timing measurement here. Two replicates cannot separate a real effect from noise, and the coordinator asked for the repetition count to be stated. | `run_stage0.py --reps 2` restores the original cost. Gates (a) and (b) need only two. |
| 10 | **Un-ignored and committed the four scenario `IN.DAT` files**, via a scoped `!scenarios/*.IN.DAT` rule in `arch_surgery/idf_probe/.gitignore`. | They were caught by the repository-root `.gitignore`'s blanket `*.DAT` and had never been committed, so the D9 patch could not have been delivered and Stage 0 was not reproducible off this machine. Upstream's own `.gitignore` un-ignores its input decks by name, so this follows an existing pattern rather than inventing one. The root file is upstream's and shared, so the rule is scoped to this directory. | `git rm --cached arch_surgery/idf_probe/scenarios/*.IN.DAT` and delete the `!scenarios/*.IN.DAT` line. Note that doing so re-opens the reproducibility hole. |
| 9 | **Put the D9 provenance in the `IN.DAT` itself**, as `* D9 PATCH` comment blocks naming the date, source file and commit, in addition to §3.4 of this report. | The coordinator asked for the patch to be auditable against upstream later. A comment in the file survives being copied out of this repository; a report section does not. | Delete the eight comment lines. They are inert `*` comments; removing them changes no value, and the MFILE would shrink by 8 lines. |

---
## 7. Things found in the code that bear on the partitioning hypothesis

Recorded, not investigated — Stage 1 (A2, module-convergence) owns this ground.

1. **The idempotence loop does real work: it is not sitting at its floor.** Across all three
   optimisation scenarios the mean is 3.2–3.5 sweeps per `call_models` against a structural
   floor of 2, and only 14–20 % of calls finish at the floor. Between **37.8 % and 42.1 % of
   all sweeps are above the floor** — that is the work a partition could in principle avoid.
   This is the headroom the whole hypothesis is aiming at, and it is real. (The evaluation
   scenario, `large_tokamak_eval`, sits much closer to the floor at 18.5 %, but it has
   `nvar = 2` and no gradient, so it is not comparable.)

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
   the state a `call_models` starts from affects how much work it does.

   **The coordinator's assessment (§10.2) offers a duller reading and I accept it as the more
   likely one:** the trailing call runs immediately after `2n` perturbations have left the
   state at a perturbed point, so it simply starts further from the fixed point — a worse
   initial guess, not pathological path dependence. The two readings share a mechanism but
   differ in consequence: benign warm-start sensitivity still makes **sweep counts
   path-dependent**, which matters for cost prediction, whereas path dependence in *results*
   would undermine the idempotence premise outright. My gate-(b) data speak only to
   whole-run reproducibility and cannot separate them. A2 should test both.

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

7. **`st_regression` does not behave like the free control the plan expects.** It is the only
   scenario with `i_pulsed_plant = 0`, and the plan's §2.3 uses exactly that to argue the
   burn-time edge — `Pulse` writing `t_plant_pulse_burn`, read back by both Module 1 and
   Module 2 — is absent there, so "the partition should already hold". If the burn-time edge
   were the dominant driver of reconciliation work, the steady-state case should sit closer
   to the 2-sweep floor than the pulsed cases. **It does not.** Its above-floor sweep
   fraction is **39.7 %**, squarely between `large_tokamak_nof`'s 37.8 % and
   `low_aspect_ratio_DEMO`'s 42.1 %, and its mean sweeps per `call_models` (3.314) sits
   between theirs (3.217, 3.455).

   I am deliberately not drawing the conclusion. Sweep count is not coupling — the plan's own
   §3.3 warns that it may be measuring the exit criterion — and `st_regression` differs from
   the other two in more than `i_pulsed_plant` (`itart = 1`, a different TF-coil path,
   `nvar = 14` not 19–20). But it is the cheapest available test of H2 and the sign is not
   the one H2 predicts. **A2 should treat this as a live risk to H2 rather than a formality**,
   and it is the first thing worth attributing per-module.

8. **The idempotence loop's ceiling is closer than the histograms suggest.** The loop raises
   after 10 sweeps. The observed maximum is 6, on two scenarios — comfortable, but the
   distributions have a tail, and `low_aspect_ratio_DEMO` puts 286 of 1240 calls at 5. Any
   later stage that presents the models with states the current architecture never visits
   (Stage 3's lift, off the consistency manifold) is spending headroom that is not as large
   as a 2-versus-10 comparison implies.


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
| 2026-08-31 | **Re-gate after D9 and the I-1 closure.** Patched `scenarios/st_regression.IN.DAT` in place per D9: five keys (`i_tf_turn_type = 2` and four HTS tape geometries) copied verbatim from `tests/regression/input_files/st_regression.IN.DAT` at `c0ae5b28`, with `* D9 PATCH` provenance comments in the file (§3.4). Moved the harness to `PROCESS_surgery_env` and removed the `PYTHONPATH` workaround for the surgery arms, keeping it only for the `pristine` arm's uninstalled checkout and keeping the in-subprocess tree assertion (§5). Raised replicates from 2 to 5 per arm and added Welch two-standard-error bands to every wall-clock figure (I-8). Deleted the base-input diagnostic arm, now redundant. Re-ran **all three gates on all four scenarios**: all PASS. Sweep counts and result signatures are bit-identical to the previous revision, so neither the environment switch nor the input patch changed any number that already existed. Discovered while committing that the scenario deck had never been tracked — the root `.gitignore`'s blanket `*.DAT` swallowed it — and committed the four `IN.DAT` files behind a scoped un-ignore rule, without which D9 is not implementable and Stage 0 is not reproducible off this machine. Rewrote §§1, 3, 4, 5, 6; updated §7 findings 1 and 4 and replaced finding 7; appended §11. |

---

## 10. Orchestrator's critical assessment

**Accepted as a Stage-0 result. Not merged — gate (c) failed, and protocol §6 freezes the task
until the fix lands on this branch.** The fix needs a user ruling (see below), so A1 stays open.

### What was done better than asked

Gate (a) was specified as "probe off versus probe on". The report compared **three** arms
including a `pristine` `git archive` of `c0ae5b28` that has never contained the probe, on **hex
float literals**, and then checked every line of a ~16,000-line MFILE. That is the correct
reading of "byte-identical to upstream" and it closes a hole the brief left open. Cross-checking
the probe's sweep counter against PROCESS's own `n_model_calls` is the same instinct.

**Keeping gate (c) at FAIL while holding a diagnostic arm that passes is the single most
important thing in this report.** The temptation to quietly adopt the working input and call the
gate green is exactly what protocol §6 exists to prevent.

Refusing to run `pip install -e` was correct on both counts — it writes outside the sandbox, and
it would have repointed a sibling clone's environment.

### Four things I would push on

1. **Wall clock is not yet a measurable quantity here, and every downstream headline depends on
   it.** Two runs that are bit-identical in results differ by up to **7.9 %** in wall time. The
   partition experiment's Stage-1 gate is "predicted saving > 25 %" and its stop rule is
   "< 10 %" — both inside or near that noise band at n = 2. **No repetition count or confidence
   interval is specified anywhere in the plans.** This is a gap A1 surfaced and nobody has
   costed. Filed as **I-8**; A2 must fix the protocol before it reports any timing.

2. **Finding 4's "model state carries memory across a `call_models` boundary" admits a duller
   explanation.** `fcnvmc2`'s trailing call runs immediately after `2n` perturbations have left
   the state at a perturbed point, so it simply starts further from the fixed point — a worse
   initial guess, not pathological path dependence. The two readings share a mechanism but differ
   in consequence: benign warm-start sensitivity still makes **sweep counts path-dependent**,
   which matters for cost prediction, while genuine path dependence in *results* would undermine
   the idempotence premise outright. The superseded study measured result path-independence
   exactly, which favours the duller reading. A2 should test both rather than adopt the dramatic
   one.

3. **Finding 2 sharpens E2 (converge-y) in a way the report does not draw out.** If 94–96 % of
   sweeps are gradient perturbations, then a change acting inside every sweep is multiplied by
   `2n` — good for E1 and E2. But the report does **not** measure what `objective_function` and
   `constraint_eqns` cost relative to `_call_models_once`, and E1's hoist of the objective and
   constraint evaluation out of the loop saves exactly that. **E1's saving is therefore still
   unquantified**; A13 must measure it before claiming it. E2's case rests on gradient quality
   regardless, which is unaffected.

4. **Losing `st_regression` costs more than one data point.** It is the **only** scenario with
   `i_pulsed_plant = 0`, and the MDA partition plan (§2.3) uses precisely that to test whether
   cross-module coupling exists in the *absence* of the burn-time edge — the cheapest test of H2
   in the whole design. Without it, H2 loses its free control. This raises the stakes on the
   scenario-set ruling well above "one of four scenarios is broken".

### Registry finding — elevated

§8's result invalidates the queue's reserved-ranges table as written.
`N_ITERATION_VARIABLES_MAX = 177` **with 177 taken**: there is no free iteration-variable number.
Every experiment that lifts anything — A4 (burn-time-lift), A9–A11 (subdriver lift) — needs the
cap raised first, or a retired gap reused, which would silently reinterpret existing `IN.DAT`
files. Filed as **I-7**. The cap lives in `numerics.py`, outside `process/models/`, so raising it
is D5-safe, but it is a shared change that must land once rather than per branch.

### Process failure, mine not the agent's

The two admin commits `787481a3` and `ac485237` landed on `A1-stage0-rebaseline` because I
committed into a **shared working tree** while the agent was switching branches. Repaired by
fast-forwarding `architecture_surgery` onto them — the two commits sat contiguously at the base
of A1's stack, so no history was rewritten and A1 now descends correctly.

The root cause is a protocol defect: `PROCESS_code_analysis` runs each task in an **isolated
worktree**, and I carried across "its own branch" without the worktree. One tree, two actors,
`git checkout` under each other's feet. Filed as **I-6**, with the protocol amended.

---

## 11. Response to the critical assessment

Appended below §10 rather than edited into it, per the coordinator's instruction. Taking the
four push-backs in order.

**1. Wall clock (I-8) — accepted, and it is worse than the assessment says.** I re-ran every
arm at `n = 5`. The worst within-arm spread is **19.6 %**, not 7.9 %, and the two-standard-
error band on a difference of means is 3–9 % (§4.2). So the noise band does not merely
approach the Stage-1 thresholds — a 10 % effect is **not measurable on this machine at
`n = 5`**, and the stop rule sits inside the noise. Two concrete suggestions for whoever fixes
the protocol, offered rather than adopted: (i) choose `n` from a target minimum detectable
effect rather than by habit — reaching a 2 SE band of 5 % on `low_aspect_ratio_DEMO` needs
roughly `n = 15` at the observed variance; (ii) make sweep count, which is exact and
reproduces bit-for-bit, the mechanism metric, and quote wall clock only as the headline with
its interval attached. Note the variance is not uniform: `large_tokamak_eval` and
`large_tokamak_nof`'s `baseline` arm sit at 3–6 %, so a per-scenario `n` may be cheaper than a
uniform one.

**2. Finding 4's duller reading — accepted, and folded into §7 finding 4.** The trailing call
starts from a perturbed point, so a worse initial guess is the more parsimonious explanation
and I have said so. I want to be explicit about what my data can and cannot settle: gate (b)
establishes that the *whole run* is reproducible, which is a statement about the sequence as a
whole, not about whether a single `call_models` reaches the same fixed point from different
starting states. Nothing I measured separates the two readings. A2's per-sweep attribution
can.

**3. Finding 2 does not quantify E1's saving — agreed, and I did not measure it.** The probe
counts sweeps; it does not time `objective_function` and `constraint_eqns` against
`_call_models_once`. That is a different instrument (a timer inside `call_models`, not a
counter) and I did not build it. §7 finding 2 should be read as bounding *what fraction of
sweeps a change would apply to*, not what fraction of wall clock it would save. A13's
measurement is the missing half.

**4. `st_regression`'s value — this one has grown, and not in the direction expected.** D9
restored the scenario, so the free control exists again. But it does not behave as the plan's
§2.3 predicts: with `i_pulsed_plant = 0` and the burn-time edge structurally absent, its
above-floor sweep fraction is 39.7 %, sitting *between* the two pulsed cases rather than below
them. This is now §7 finding 7, flagged as a live risk to H2 rather than a formality. I have
deliberately not drawn the conclusion — sweep count is not coupling, and the scenario differs
in `itart` and `nvar` too — but the cheapest test of H2 in the whole design has returned a
sign that H2 does not predict, and A2 should know that before it starts.

**On the registry finding (I-7) and the process failure (I-6):** nothing to add. Both readings
match mine, and the worktree isolation from A2 onward addresses the cause rather than the
symptom.

**One thing I would add to the assessment's list.** §7 finding 8: the idempotence loop's
ceiling is 10 sweeps and the observed maximum is 6, with a populated tail at 5. Stage 3 plans
to present the models with states off the consistency manifold, which is exactly the condition
that would push into that tail. The margin is a factor of ~1.7 on the worst observed call, not
the factor of 5 a floor-to-ceiling reading suggests. Worth budgeting.
