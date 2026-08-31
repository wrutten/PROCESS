# CLAUDE.md

Agent-facing rules for this repository. The queue's protocol section
([`arch_surgery/docs/plans/MASTER_TODO.md`](arch_surgery/docs/plans/MASTER_TODO.md)) is the
fuller version; the rules below are always in force.

**What this repository is.** A fork of PROCESS (`wrutten/PROCESS`) in which the *optimisation
architecture* — the arrangement of solvers and optimisers — is modified while every physics
and engineering model is left exactly as upstream wrote it. `process/`, `tests/`,
`documentation/` and everything else at the root are upstream PROCESS. The experiment lives
in `arch_surgery/`.

## Hard rules

- **The sandbox may never be overridden.** Never pass `dangerouslyDisableSandbox: true` or
  otherwise route around a sandbox restriction, even when a command just failed with clear
  evidence that the sandbox caused it. Report the blocker and the exact command that would fix
  it, and **ask the user** — they make environment changes themselves. This binds every agent
  working in this repo, including subagents.
- **The base commit is frozen.** `c0ae5b28` is the experiment's base and is not to be rebased,
  merged forward, or re-pinned (D2). It is the shared coordinate system with
  `functional_PROCESS` and with the dependency-analysis pin `PROCESS_at_36ac820e`; moving it
  forfeits every cross-study comparison. `upstream` may be fetched for drift measurement only.
- **The physics is frozen; model edits need approval.** Only the driver changes by default —
  `process/core/caller.py`, `process/core/solver/`, the probe. **Minimal structural edits under
  `process/models/` are permitted (D11)** — extracting a residual so its solution method becomes a
  driver choice, not changing what a model computes — but **every such change requires the user's
  approval before merging**. Changing what a model computes is still a change to the independent
  variable and invalidates the experiment (D5).
- **Never modify a sibling clone.** `/home/wrutten/dev_libraries/PROCESS`,
  `/home/wrutten/projects/functional_PROCESS` and `/home/wrutten/projects/PROCESS_code_analysis`
  are other working trees. Read them; never write to them.
- **Never commit to `main`.** `main` tracks upstream PROCESS. All work is on
  `architecture_surgery` or a task branch off it.
- **Never push without the user's explicit approval**, per push.

## Working rules

- **A failed gate is a result, not an obstacle.** Never tune, retry with different settings, or
  work around a gate to make it pass. Report what failed with the numbers.
- **Every number is rederived at `c0ae5b28`.** Nothing measured at `710a75c9` (the superseded
  study) may be cited as evidence. See D4.
- **Isolation is mandatory for every PROCESS run**: fresh subprocess, own working directory.
  `OutputFileManager` holds file handles as class attributes and initialisation mutates a
  global data structure, so two runs in one process contaminate each other. Discard the first
  run in a fresh environment for timing — numba JIT dominates it.
- **Compare at matched final accuracy**, never at matched tolerance settings (§3.3 of the
  experiment plan).
- **No conclusion rests on a timing.** Acceptance quantities are **counts or bit-comparisons** —
  sweeps, model evaluations, hex-float identity — which are exact and reproduce bit-for-bit.
  Timings are reported as context, with their interval and repetition count, and never as
  evidence. This is not caution about noise: I-10 showed a wall-clock-derived *cost weight* moving
  6.4 % → 4.4 % across runs of identical code, which had already reached the arithmetic behind a
  gate decision. A weighting whose instability is comparable to the effect it resolves is noise
  with a decimal point. *(Convention adopted from `PROCESS_code_analysis`, which reached it
  independently and for different reasons.)*
- Correctness is gated on `norm_objf` plus a post-solve feasibility audit — **never on
  iteration variables** (D6); some are not identified by the problem and differ at an unchanged
  optimum.
- Probe instrumentation is env-switched: with `PROCESS_IDF_PROBE` unset every hook is a no-op
  and behaviour is byte-identical to upstream. Switch-neutrality is a gate, not an aspiration.
- Task reports go to `arch_surgery/docs/reports/` while the task is open; they are archived to
  `arch_surgery/docs/reports/deprecated/` at merge. **Folder position records lifecycle, not
  validity** — read each document's `> **Document status**` header (trap T3).
- **Read [`arch_surgery/docs/TRAPS.md`](arch_surgery/docs/TRAPS.md) before touching anything.**
  Five recorded ways this project has already misled someone.
- Bulk run artifacts (`arch_surgery/idf_probe/runs/`) stay untracked. Summaries and verdicts
  are committed; raw JSONs are not.

## Orientation

- [`arch_surgery/docs/plans/MASTER_TODO.md`](arch_surgery/docs/plans/MASTER_TODO.md) — the
  queue: protocol, decisions, issues, task rows.
- [`arch_surgery/docs/plans/MDA_PARTITION_EXPERIMENT.md`](arch_surgery/docs/plans/MDA_PARTITION_EXPERIMENT.md)
  — the experiment plan: hypothesis, evidence, critical assessment, stages and gates.
- [`arch_surgery/docs/reports/PROCESS_architecture_evaluation.md`](arch_surgery/docs/reports/PROCESS_architecture_evaluation.md)
  — the F1–F14 critique of PROCESS's driver architecture. **Stale in its measurements**
  (`710a75c9`); its structural findings largely survive.
- [`arch_surgery/docs/TRAPS.md`](arch_surgery/docs/TRAPS.md) — binding; read first.
- `arch_surgery/idf_probe/` — the measurement instrument. Its `MEMO.md` and `NOISE_ANALYSIS.md`
  are **stale** (`710a75c9`) and carry status headers saying so.

## Environments

- **`PROCESS_surgery_env` runs this repository's PROCESS.**
  `/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python` (Python 3.12.14), editable
  install pointing at `/home/wrutten/projects/PROCESS_surgery`. Verified: `import process` from
  a directory outside the repo resolves to this tree.
- **Do not use `PROCESS_env`.** It is a sibling environment whose editable install points at
  `/home/wrutten/dev_libraries/PROCESS`, a different clone at the superseded commit `710a75c9`.
  It imports silently and would invalidate every measurement. `func_PROCESS_env` belongs to
  `functional_PROCESS`. Picking the wrong one is a silent failure, not an error — the run
  succeeds and the numbers are of the wrong tree.
- **Assert the tree, do not trust the environment.** Every measurement subprocess re-checks
  `process.__file__` and aborts if it is not under `PROCESS_surgery`. Keep that check even though
  the environment is now correct.
- The dependency-analysis instrument lives in the sibling repo
  `PROCESS_code_analysis/dependency_analysis`, runs in `ESL_env`, and is pinned at
  `ANALYSIS_PIN_NAME` in `dependency_analysis/core/inputs/config.py` — read it; never copy a
  hash into a document.
