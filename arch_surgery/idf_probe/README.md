# IDF probe (Track A)

One-shot performance probe answering "what speedup is (not) achievable from an IDF reformulation of
PROCESS, and which feedback couplings actually matter?" — **without** refactoring PROCESS.

**Verdict: see [MEMO.md](MEMO.md).**

Study commit: PROCESS `main` @ `710a75c9`. Env: conda `PROCESS_env`.

## Status (2026-08-19) — what still runs

Moved here from `PROCESS_code_analysis` on 2026-08-19 together with the rest of Track A.

`run_one.py` and `noise_deepdive.py` import `process.core._idf_probe`. That module exists
**only** on the PROCESS repo branch `stage0-probe` (see the change manifest below); it is not
in PROCESS `main` and not in the current checkout of `~/dev_libraries/PROCESS`. Both scripts
are therefore **non-runnable against the current checkout** — they fail at import. Their
recorded outputs under `runs/` remain valid evidence for the study commit.

`noise_probe.py` does not import the probe module and **still runs**. `metrics.py` and
`compare.py` operate on the recorded `runs/` JSONs and still run.

To make the two probe scripts runnable again, check out branch `stage0-probe` of the PROCESS
repository (or re-apply the change manifest below) into the environment they import from.

## Design

PROCESS is instrumented in-repo behind an environment switch (see the change manifest below).
`PROCESS_IDF_PROBE` unset ⇒ every hook is a no-op and behaviour is byte-identical to baseline
(verified by a switch-neutrality gate).

Modes (`PROCESS_IDF_PROBE=...`):

| mode | behaviour |
|---|---|
| *(unset)* | baseline, no instrumentation |
| `baseline` | unmodified control flow; records sweeps-per-`call_models` + phase (`func`/`grad`/`grad_reconcile`) |
| `single_sweep` | `call_models` does exactly ONE sweep — the idempotence loop is removed (the IDF-like evaluation) |
| `single_sweep_debug` | as above + a second sweep to log per-constraint lag drift; returns the *first* sweep's values (timing invalid by construction) |
| `census` | baseline trajectory, but snapshots the whole `DataStructure` after sweeps 1 and 2 and diffs them — empirical enumeration of the feedback set |

**Isolation is mandatory:** `OutputFileManager`'s file handles are class attributes (process-wide) and
`init_process` mutates a global `DataStructure`, so every run gets a fresh subprocess and its own work
dir. (PROCESS does *not* chdir — only `io/vary_run/config.py` does.)

## Layout

```
run_one.py      # subprocess entry: ONE scenario x ONE mode -> runs/<scenario>/<mode>/metrics.json
noise_probe.py  # gradient-noise study (M1 fixed-x repeat, M2 path dependence, M3 loop-exit -> Jacobian error)
metrics.py      # MFILE -> metrics, sweep histograms, itvar comparison, speedup formula
compare.py      # gates + A/B tables + drift ranking -> runs/comparison.json, runs/baseline_summary.json
scenarios/      # copies of the 4 IN.DATs from tests/regression/input_files/
runs/           # work dirs + JSON results
MEMO.md         # the deliverable
```

## Running

```bash
export PYTHONDONTWRITEBYTECODE=1
P=/home/wrutten/anaconda3/envs/PROCESS_env/bin/python

# one run
$P run_one.py --scenario large_tokamak_nof --mode baseline --outdir runs/large_tokamak_nof/baseline_rep1

# gradient noise
$P noise_probe.py --scenario large_tokamak_nof --outdir runs/large_tokamak_nof/noise_x0_v2 --at x0
$P noise_probe.py --scenario large_tokamak_nof --outdir runs/large_tokamak_nof/noise_opt   --at opt

# analysis
$P compare.py
```

Runs are ~12–100 s each with warm numba caches; the **first** run in a fresh environment takes ~45 s
extra for JIT compilation, so discard it for timing. Parallelise across scenarios with `&`.

## Change manifest (PROCESS repo, uncommitted)

| File | Change |
|---|---|
| `process/core/_idf_probe.py` | **new** — all probe logic |
| `process/core/caller.py` | import; `call_models` dispatches to the probe when active (original body → `_call_models_original`); `note_sweep()` in the loop |
| `process/core/solver/evaluators.py` | import; set `PHASE` around `fcnvmc1`/`fcnvmc2` |
| `process/core/solver/solver_handler.py` | import; `note_retry()` at the three VMCON retry branches |

Restore baseline:

```bash
cd /home/wrutten/dev_libraries/PROCESS
git checkout -- process/core/caller.py process/core/solver/evaluators.py process/core/solver/solver_handler.py
rm process/core/_idf_probe.py
```

Also installed into `PROCESS_env`: `click>=8.3.2` — a *declared* dependency of this commit
(`pyproject.toml`) that was missing from the env; `process.main` cannot import without it.
