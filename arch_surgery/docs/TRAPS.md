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

## T11 — A number published without the condition that limits it

Three instances in this project, all by the orchestrator, all surviving its own review:

| | Claim | The missing qualifier | Caught by |
|---|---|---|---|
| 1 | Three descending timing samples read as a settling trend | Only two were content-identical; the third ran on lighter code | the sibling study |
| 2 | "`st_regression` differs in 12 switches, `low_aspect_ratio_DEMO` in 5" | No denominator stated — the population was 33 hand-picked names, not the analysis tool's field set, which gives 17/7, 15/7 or 8/4 | the sibling study |
| 3 | "Removing the two-sweep floor is worth **up to 31 %**" | The bound binds *only* where the state is already converged on entry. Measured: **1.5-1.8 %** | measurement (A18) |

**One shape.** A quantity is computed over an aggregate — 630 calls x 1 sweep, three samples, 33
switches — and published without the qualifier that constrains where it applies. Each was formally
defensible ("up to", "these switches") and each was read, correctly, as an estimate.

**Why the hedge does not save it.** Instance 3 carried "up to", and the expectation table said
"0-31 %, magnitude unknown". The surrounding prose called it *"plausibly the largest effect in the
whole portfolio"*. A hedge contradicted by its own framing is not a hedge.

**The specific error in instance 3 is worth keeping**, because it is a reasoning failure rather
than a bookkeeping one. The first sweep of the idempotence loop yields no *convergence
information* — true — and this was treated as meaning it is *extra work*. It is not: it is work
that would be done anyway. If the state settles after `k` sweeps then `F(y_{k-1}) = F(y_k)`, so the
old predicate stops at `k` and the new one stops at `k`. **They cost the same for every `k >= 2`.**
The floor binds only at `k = 1`. Two lines of counterfactual would have shown this, and were never
written.

**A confirming statistic was also misread.** 1 260 of 2 027 sweeps sit at the floor (62 %), which
was taken as "lots of room". Sitting at the floor means *converging as fast as possible*, not
*wasting a sweep*.

**The practice.** Before publishing a number, write the population or condition it holds over **in
the same sentence**. If that cannot be done in one clause, the number is not ready. This is
cheaper than it sounds and would have caught all three.

## T12 — A gate's `runs_under` is relative to `runs/gates/`, not to `runs/`

**A gate's `runs_under` is relative to `runs/gates/`, not to `runs/`.** A `tally.Source.subpath`
is relative to `runs/`, the two are one directory apart, and pasting one into the other makes
`Gate.run` survey a directory that does not exist. It does not fail: `survey_heads` returns
`n_records = 0`, the staleness check in `Gate.run` is gated on `n_records > 0`, and the verdict
prints **"0 record(s)"** where the straddle belongs — so a gate that has read nothing and a gate
whose runs are all current are indistinguishable in the record. **How to avoid it:** derive the
gate-relative path from the source declaration rather than retyping it, and read the new gate's
own `runs_provenance.n_records` in its first verdict — a 0 there is a bug, not a clean tree.
*(Found by A54 (harness-analysis), 2026-09-11, on the gate it was itself adding; lifted here at its
merge, `72c343d1`.)*

## T13 — A `--resume` that consults anything but the record is not a resume

Twice in one day a gate kept old runs while its verdict said it had made new ones. A52
(harness-gates)'s `--gate all` carried sixteen hard-coded `resume=True`; A55 (harness-smoke) found
`gates._capture_after` returning early whenever `--resume` was given and a *manifest* existed, so
G1 passed a press over a capture made at a commit the tree had not measured. In both cases the
verdict's own `runs read … at <commit>` line was the only thing that gave it away. **The rule:** the
one thing that may decide whether a run is kept is `pool.run`'s comparison of the existing record
with the job (arm, configuration, seed, phase, regime, run kind, and the current record contract).
A manifest, a directory's existence, a flag set by a caller — none of these is evidence.
**How to catch it:** survey `tree_git_head` on every run record after any press and compare it
with the commit the verdict names (harness plan amendment 13 (i), and rule (vii) of amendment 19). *(A52 and A55,
2026-09-11; lifted here at A55's merge, `bfaee7ce`.)*

## T14 — A record rendered from a record is only as current as the file it was made from

The plan's §4 is rendered from the `gate_table` *stage record*, not from the verdict records. On
2026-09-11 a gate was re-run and passed; the §4 re-render reproduced the failing table byte for byte,
because the stage record predated the re-run and nothing said so. Any document or table built from
a stage record inherits the staleness of that record, silently, unless the record says what it read
and the consumer checks it. **The rule (harness plan amendment 20):** a stage declares the records it
reads, the framework stamps them (path, digest, commit, time) into the stage record, and the consumer
refuses when the files have moved. A related blind spot: a provenance block one level down in a
record is invisible to a stamp survey that reads the top level — the census records carried their
commit only inside a nested block and read as "no stamp" (I-22 (b)). *(A55 and A63, 2026-09-11.)*

## T15 — A stage whose population is a gate job set passes the smoke and reads nothing at the campaign

The tally declared two sources, both gate job sets (GR's runs, G6's pairing). The smoke ran the campaign's chain at one seed and then the tally — which, by design, refuses smoke records and so read the *seeded gate records* instead. Every smoke press passed. At the first campaign press (2026-09-14, `57dc0c14`) the tally read 0 of 949 records and `tally_contracts` FAILed: no source had ever named the campaign's own jobs (I-24, fixed by A75 (campaign-tally-source)).

**How to avoid it:** a stage that summarises records must declare a source for every run kind it is meant to summarise, and the smoke must show the stage reading the smoke's *own* records (as a population it then refuses to publish) rather than a seeded population of another kind. A passing smoke that read no record of its own kind proved nothing about the campaign path.

## T16 — A name in a record is the name at the time of the run

On 2026-09-15 the arms were renamed (`A0p → A1`, `A1 → A2`, `B3 → B2`) so the rungs would read one letter apart across the phases. The 949 campaign records and every gate record stamp the old names — in `job_identity.arm`, in the job digest, in the directory they sit in (`runs/campaign/evaluation/<config>/A0p/…`). After the rename, `A1` on disk is not `A1` in the report: a reader that takes a directory name or a raw `metrics.json` at face value pairs today's `A1` (yesterday's `A0p`) with yesterday's `A1` (today's `A2`) and publishes a rung that does not exist. The same holds for every document dated before the rename: its `A1` is today's `A2`, and its `B2` is V3's removed joint-test arm, not today's partitioned optimisation arm.

**How to avoid it:** read records only through the harness (`records.read` applies the one declared table `records.RECORDED_ARM_NAMES` and refuses an arm neither the table nor the matrix knows); never by directory name or by loading the JSON yourself. Treat the date of a document as part of every arm name in it; the report's Appendix C, the queue's decisions register and the improvement lists carry a translation line at their heads. A renamed thing keeps its stamp; the translation lives in one place and is never applied by hand. *(A78 (arm-renames), 2026-09-15.)*

## T17 — A table number is a position, not a name

Since A79 (report-captions) the report's tables are numbered `Table D.n` in emission order and the companion file's `Table F.n` likewise. Add one table, or drop one, and every number after it shifts; the prose that cited `Table D.13` now points at a different table with a plausible-looking grid. `--plan-tables check` catches a *dangling* number (one that no longer exists), not a *shifted* one.

**How to avoid it:** cite by the construction name printed under each grid (`node calls per block — campaign_displaced`) when the citation must survive; when citing a number, re-read every numbered citation whenever the table set changes — the renderer's report of how many tables it emitted, before and after, is the signal. A citation that names both (number and construction) survives either check. *(A79 (report-captions), 2026-09-15.)*
