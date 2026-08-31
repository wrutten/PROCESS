# Traps

Read before touching anything. These are not defects to be fixed — they are ways this codebase and
this project have already misled someone, recorded so it does not happen twice.

## T1 — Name-level analysis conflates `run()` and `output()` paths

A model attribute written by one model and read by another looks like a dependency edge. It is not
one if the read happens in an **`output()` method** — those run once after the solve, outside the
MDA and outside the finite-difference stencil.

**It has bitten twice.**

- `physics.b_plasma_vertical_required` is written by `pfcoil.py` and read in
  `PlasmaFields.output()`. It looked like a Coils→Physics feedback edge closing a cross-module
  cycle, and was briefly treated as refuting the partition hypothesis. The dependency analysis had
  correctly excluded it.
- `confinement_time.py:1160` root-finds on the H-factor over a bracket of `(0.01, 150)` at
  `xtol=0.001` with an expensive residual — the most attractive subdriver-lift candidate in the
  codebase. Its only caller chain ends at `output_confinement_comparison`, a reporting method. It
  never enters the stencil.

**How to avoid it:** confirm a candidate lies on a `run()` path **by counting invocations during an
optimisation run**, not by reading call graphs. Any instrument that greps attribute access must
exclude `output()` paths explicitly.

## T2 — `= ` matches `==`

Extracting "what does this model write" with a regex like `self\.data\.\w+\.\w+ *=` silently
matches `== 1` and reports comparisons as assignments. It produced a phantom write of
`pulse.i_pulsed_plant` and nearly put a spurious back-edge into the partition plan.

**How to avoid it:** anchor on `=[^=]`, and sanity-check any write list against the file by eye —
a model that appears to write a configuration switch it only reads is the tell.

## T3 — Folder position is not document status

`docs/reports/deprecated/` holds both merged task reports (archived because their task closed, and
still authoritative) and superseded documents (stale, not to be cited). A file's directory records
lifecycle, not validity.

**How to avoid it:** every document carries a `> **Document status**` header stating which it is.
Read the header, not the path.

## T4 — One working tree, one HEAD

Two actors in the same checkout will commit to each other's branches: `git` commits to whatever
branch that tree currently has checked out, regardless of who started the work. This put two
orchestrator commits onto a task branch (I-6).

**How to avoid it:** task work runs in its own `git worktree`. Creating a *branch* does not isolate
anything; creating a *worktree* does.

## T5 — Wall clock on this machine cannot resolve the effects the plans gate on

16 cores but 7 GB of RAM, no thread pinning, and concurrent sessions. Worst within-arm spread is
19.6 % at `n = 5` against gates set at 10–25 %.

**How to avoid it:** gate on sweep and model-evaluation counts, which are exact and reproduce
bit-for-bit. Interleave arms and pair the differences; pin thread counts; record CPU time as a
contention diagnostic; run when the machine is otherwise idle.

## T6 — A worktree does not redirect the editable install

The `PROCESS_surgery_env` editable install points at the **main checkout**,
`/home/wrutten/projects/PROCESS_surgery`. A task working in a `git worktree` gets the worktree's
`process/` only when cwd happens to be the worktree root — and measurement subprocesses run in
their own working directories, so they import the **main tree** instead. The task would silently
measure code it is not editing.

Worse, A1's guard does not catch it: it asserts `process.__file__` is under `PROCESS_surgery`,
which is true of the main tree even when running from a worktree.

**How to avoid it:** in a worktree, set `PYTHONPATH` to the worktree root for every measurement
subprocess, and tighten the assertion to the **exact tree** the task is editing, not a prefix.
Verify from a directory that is neither tree.
