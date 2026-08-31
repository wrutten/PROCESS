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
- **The models are frozen.** Only the driver changes — `process/core/caller.py`,
  `process/core/solver/`, and the probe. A change under `process/models/` is a change to the
  independent variable and invalidates the experiment (D5). If a model must change, that is a
  user decision, recorded as a `D<n>`.
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
- Correctness is gated on `norm_objf` plus a post-solve feasibility audit — **never on
  iteration variables** (D6); some are not identified by the problem and differ at an unchanged
  optimum.
- Probe instrumentation is env-switched: with `PROCESS_IDF_PROBE` unset every hook is a no-op
  and behaviour is byte-identical to upstream. Switch-neutrality is a gate, not an aspiration.
- Task reports go to `arch_surgery/docs/reports/` while the task is open; they are archived to
  `arch_surgery/docs/reports/deprecated/` at merge.
- Bulk run artifacts (`arch_surgery/idf_probe/runs/`) stay untracked. Summaries and verdicts
  are committed; raw JSONs are not.

## Orientation

- [`arch_surgery/docs/plans/MASTER_TODO.md`](arch_surgery/docs/plans/MASTER_TODO.md) — the
  queue: protocol, decisions, issues, task rows.
- [`arch_surgery/docs/MDA_PARTITION_EXPERIMENT.md`](arch_surgery/docs/MDA_PARTITION_EXPERIMENT.md)
  — the experiment plan: hypothesis, evidence, critical assessment, stages and gates.
- [`arch_surgery/docs/reports/PROCESS_architecture_evaluation.md`](arch_surgery/docs/reports/PROCESS_architecture_evaluation.md)
  — the F1–F14 critique of PROCESS's driver architecture. **Stale in its measurements**
  (`710a75c9`); its structural findings largely survive.
- `arch_surgery/idf_probe/` — the measurement instrument and its stage reports.

## Environments

- `PROCESS_env` runs PROCESS: `/home/wrutten/anaconda3/envs/PROCESS_env/bin/python`
  (Python 3.12.14).
- **Check the editable install before every measurement session.** `pip show process` must
  report an editable location of `/home/wrutten/projects/PROCESS_surgery`. It has pointed at
  `/home/wrutten/dev_libraries/PROCESS` (I-1) — a different clone at the superseded commit,
  which imports silently and invalidates every number. Prove it from a directory that is *not*
  the repo root: `process.__file__` must be under `PROCESS_surgery`.
- The dependency-analysis instrument lives in the sibling repo
  `PROCESS_code_analysis/dependency_analysis`, runs in `ESL_env`, and is pinned at
  `ANALYSIS_PIN_NAME` in `dependency_analysis/core/inputs/config.py` — read it; never copy a
  hash into a document.
