# Traps

Read before touching anything. These are not defects to be fixed — they are ways this codebase and
this project have already misled someone, recorded so it does not happen twice.

## T1 — Name-level analysis conflates `run()` and `output()` paths

A model attribute written by one model and read by another looks like a dependency edge. It is not
one if the read happens in an **`output()` method** — those run once after the solve, outside the
MDA and outside the finite-difference stencil.

**It has bitten three times.**

- `physics.b_plasma_vertical_required` is written by `pfcoil.py` and read in
  `PlasmaFields.output()`. It looked like a Coils→Physics feedback edge closing a cross-module
  cycle, and was briefly treated as refuting the partition hypothesis. The dependency analysis had
  correctly excluded it.
- `confinement_time.py:1160` root-finds on the H-factor over a bracket of `(0.01, 150)` at
  `xtol=0.001` with an expensive residual — the most attractive subdriver-lift candidate in the
  codebase. Its only caller chain ends at `output_confinement_comparison`, a reporting method. It
  never enters the stencil.

- `pfcoil.py:2727` reads `times.t_plant_pulse_burn` and was cited in the MDA partition plan's
  §2.3 as the M2-side read that made the burn-time edge symmetric — half the evidence for the
  central hypothesis. It is inside `PFCoil.outvolt()`, called only from `PFCoil.output()`. A2's
  runtime census sees no read of that field by `pfcoil` inside the MDA.

**How to avoid it:** confirm a candidate lies on a `run()` path **by counting invocations during an
optimisation run**, not by reading call graphs. Any instrument that greps attribute access must
exclude `output()` paths explicitly.

**And note the shape of the hazard, measured (A2, 2026-08-31): ten model objects call their own
`run()` from inside their `output()` method** — `costs`, `availability`, `pulse`, `divertor`,
`structure`, `ccfe_hcpb`, `power.acpow`, `vacuum`, `buildings`, `water_use` — three times each
per run, during the final output idempotence check. So even an instrument that hooks `run()`
rather than grepping names will record `output()`-path traffic unless it *closes the sweep* at
the end of `Caller._call_models_once` and refuses anything entered afterwards. Before A2's
instrument did that, it reported two back-edge fields that exist only on the output path.

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

## T7 — Ten models call their own `run()` from `output()`

The deeper form of T1. Instrumenting `run()` is **not** sufficient to separate MDA work from
reporting work, because `output()` re-enters `run()` in ten models. An instrument that hooks
`run()` alone will attribute post-solve reporting to the MDA and invent dependency edges — it
produced two phantom back edges in A2 before the sweep was closed at the end of
`_call_models_once` instead.

**How to avoid it:** close the sweep at the boundary of `_call_models_once`, not at `run()` entry
and exit. Treat any edge discovered only during an `output()` call as suspect until proven
otherwise.

## T8 — `pkill` and `ps` do not work across sandboxed Bash calls

Each sandboxed Bash call gets its own PID namespace, so `ps` shows nothing from a sibling call and
`pkill` kills nothing. A2 lost a full set of runs to two drivers overlapping while both `ps` and
`pkill` reported success.

**How to avoid it:** stop background work with `TaskStop`, never with `pkill`. If two runs may
overlap, serialise them explicitly rather than trying to detect and kill.

## T9 — Reading a sibling repository's generated exports races with its merges

`PROCESS_code_analysis` regenerates its shipped exports (`output/tokamak/dsm_collapsed.html` and
friends) **at every merge**. A task that reads them live can catch a half-written or
mid-regeneration state, and it also silently re-pins our analysis to whatever their tree happens
to hold that day — which is not necessarily the commit our documents claim.

Confirmed by their orchestrator, 2026-08-31, on their own initiative.

**How to avoid it:** never read a sibling repo's generated output live. The DSM node map is
**committed as data in this repository** (framework component C8), generated once from a named
pin and validated at run time. A task proposing to read their `output/` instead of our committed
copy is a design error, not an optimisation. If a re-derivation is genuinely needed, warn that
session before it runs.

## T10 — `process.__version__` reports the wrong commit in a frozen archive

`_version.py` is written when a tree is archived and then frozen with it. So a pinned reference
tree can report a **version string from a different commit than the one it actually contains**.
Measured case, reported by `PROCESS_code_analysis` 2026-09-01: their archive
`PROCESS_at_36ac820e` has `process.__version__` reporting **`710a75c9`** — the superseded commit
this project has already discarded evidence from (D4).

**Why it is a trap and not a nuisance:** `__version__` is the obvious thing to reach for when
writing "assert I imported the right tree", it looks authoritative, and it fails *silently* by
agreeing with a plausible-looking wrong answer.

**The rule:** assert on **`process.__file__`** — the path — never on `__version__`.
`arch_surgery/idf_probe/run_one.py:108` does this correctly and must keep doing it. Do not add a
`__version__` check believing it strengthens the assertion; it weakens it, because a passing
`__version__` check on the wrong tree is worse than no check at all.

This compounds with the standing environment hazard: `PROCESS_env` points at a *different clone at
a different commit* and imports without error. Path assertion is the only thing that catches it.

