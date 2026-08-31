# Master TO-DO — architecture surgery on PROCESS

| | |
|---|---|
| **Status** | ACTIVE — the standing execution queue for this repository |
| **Owner** | W.J. Rutten (paces execution); orchestrating agent dispatches |
| **Objective** | Determine whether **the arrangement of solvers and optimisers alone** — every physics and engineering model frozen at `c0ae5b28` — measurably changes the cost of solving PROCESS, by partitioning the global idempotence loop into per-module solvers |
| **Base commit** | `c0ae5b28` — frozen (D2). Shared coordinate system with `functional_PROCESS` and with the dependency-analysis pin `PROCESS_at_36ac820e` |
| **Supersedes** | The IDF experiment at `710a75c9` (`IDF_EXPERIMENT_PLAN.md`, `idf_probe/MEMO.md`, `NOISE_ANALYSIS.md`). Retained for methodology only; **no number from it is evidence** (D4) |
| **Stage detail** | [`../MDA_PARTITION_EXPERIMENT.md`](../MDA_PARTITION_EXPERIMENT.md) is the experiment plan — hypothesis, evidence, critical assessment, stages and gates. This file is the queue that sequences them |

---

## Project administration

**Orchestration protocol** (in force):

1. **The orchestrator dispatches; task agents plan and execute.** The orchestrator does not
   execute tasks itself.
2. **Every task is labeled `A<n>` with a keyword minted at the same time**, and the keyword
   always accompanies the number in prose — queue rows, change-log entries, reports and
   session messages write `A1 (stage0-rebaseline)`, never a bare `A1`. One keyword per task,
   never renamed. The keyword is the branch slug.
3. **Every task runs on its own branch** `A<n>-<keyword>` **in an isolated `git worktree`** off
   `architecture_surgery`, and writes
   a report to [`../reports/`](../reports/) — verdict first, autonomous decisions with their
   reversal paths, append-only change log. Commit messages carry the keyword:
   `A<n> <keyword>: …`.
4. **Reports avoid jargon.** Project shorthand — decision numbers, issue numbers, internal
   vocabulary — is spelled out at first use, so a report reads without the queue open beside it.
5. **The orchestrator appends a critical assessment to every task report** and acts as
   adversarial reviewer.
6. **A failed gate blocks the merge and is reported as a result.** No tuning a gate into
   passing, no conditional merges that defer a fix to a later task. The fix is made on the same
   branch and the task is re-gated as one merge.
7. **Merge discipline**: merges happen from the main checkout, one at a time; the branch is
   deleted with `-d`, never `-D`. At merge the task report is archived to
   [`../reports/deprecated/`](../reports/deprecated/) — the live directory holds only open
   tasks' reports.
8. **Pacing**: the user decides which tasks execute. Only the user adds tasks; agents may
   propose.
9. **Stop background work with `TaskStop`, never `pkill`.** Each sandboxed Bash call has its own
   PID namespace, so `ps` sees nothing from a sibling call and `pkill` kills nothing while
   reporting success (trap T8; A2 lost a set of runs to this).
10. **One actor per working tree.** Never `git commit` or `git checkout` in a tree another agent
   is working in — commits land on whatever branch that agent last checked out (I-6, 2026-08-31).
   The orchestrator's admin work goes on `architecture_surgery` in the main checkout; task work
   goes in its own worktree.
11. **Standing rules**: the sandbox is never overridden (report blockers and ask); never push
   without per-push approval; never modify a sibling clone; the base commit and the models
   are frozen. See [`../../../CLAUDE.md`](../../../CLAUDE.md).

**Work-item terminology** (one word, one meaning):

| Term | Label | Meaning | Rules |
|---|---|---|---|
| **Task** | `A<n>` | A queue row: one branch, one agent, one report, one merge decision | Only the user adds tasks |
| **Subtask** | `A<n>.<k>` | The agent's own decomposition, in its report | Never its own branch or report |
| **Issue** | `I-<n>` | Defect or gap in *this repository or its environment*, found outside a task's scope | Filed below, not fixed in passing |
| **PROCESS finding** | — | Defect or critique of *PROCESS itself* | Architecture critiques belong here; implementation defects go to `PROCESS_code_analysis/docs/bug_reports/` |
| **Decision** | `D<n>` | A recorded user decision | Append-only; a reversal is a new decision referencing the old |

**Numbering** — next free: **A18**, **D10**, **I-9**. Numbers are never reused.

**Optimiser-registry allocation** is administered in
[`REGISTRY_ALLOCATIONS.md`](REGISTRY_ALLOCATIONS.md) — one table, append-only (D10). Every task
takes its numbers from there; two branches allocating independently would both pick the same next
number and merge into a dict with one entry silently winning.

---|---|---|
| Constraints | 82 registered over 1–92, cap 500 | **93** — but `lablcc` has exactly 92 entries and must be extended in step |
| Iteration variables | 83 registered over 1–177, `N_ITERATION_VARIABLES_MAX = 177` | **none** — 177 is taken and the cap is the maximum |

**No iteration-variable block can be reserved until the cap is raised (I-7).** Constraint numbers
from 93 upward are available and will be blocked out when the first lifting task is authorised.

---

## Decisions (live set)

| # | Decision | Date |
|---|---|---|
| **D1** | `wrutten/PROCESS` is the canonical fork. `PROCESS_surgery` is flattened into it — the research artifacts live in `arch_surgery/` inside the fork, not in a separate repo with a submodule. `IPP-SRS` branches (`AST_parseable`, `stage0-probe`) are archived on the fork for reachability but are not merged | 2026-08-31 |
| **D2** | **The base commit is `c0ae5b28`, frozen.** Chosen because it is the last commit before `functional_PROCESS` begins its rewrite and is the ancestor of the dependency-analysis pin — the three studies share one coordinate system. Not to be rebased or re-pinned; `upstream` may be fetched to measure drift only | 2026-08-31 |
| **D3** | **A fresh rewrite.** The `PROCESS_rewritten/` scaffolding on `stage0-probe` (based on `710a75c9`) is not ported | 2026-08-31 |
| **D4** | **The `710a75c9` evidence is discarded**, raw run artifacts deleted. The superseded documents are retained for methodology only; every number is rederived at `c0ae5b28`. Recoverable from `adf863d7` if a specific figure is ever wanted | 2026-08-31 |
| **D5** | **The models are frozen; only the driver changes.** This is what distinguishes this study from `functional_PROCESS`: a rewritten back-end cannot isolate the architecture's contribution, because any measured difference confounds the architecture with the rewrite | 2026-08-31 |
| **D6** | **Correctness is gated on `norm_objf` plus a post-solve feasibility audit, never on iteration variables.** Some iteration variables are not identified by the problem and differ at an unchanged optimum, so an itvar gate generates false alarms | 2026-08-31 |
| **D7** | **A full IDF / MDF / SAND comparison is deferred** to a later study on the `functional_PROCESS` back-end. This experiment is not a stepping stone to it — it is the control that study will need | 2026-08-31 |
| **D8** | **The module partition is derived from the collapsed DSM, not assumed.** M1 Physics = rows 4, 6–28; M2 Coils = rows 5, 29–37; M3 Plant = rows 40–51; `CsFatigue` (38) and rows 52–55 feed-forward; `Pulse` (39) is the articulation point belonging to no module | 2026-08-31 |
| **D9** | **The archived scenario deck is patched in place, not re-pointed at upstream's regression inputs.** `st_regression.IN.DAT` gains `i_tf_turn_type = 2` and the four tape geometries; the other three stay as archived and continue to load via obsolete-name rewriting (A1 autonomous decision 3). Rationale: the deck stays a frozen artifact of this study rather than tracking whatever upstream ships, so a scenario cannot change under a result | 2026-08-31 |
| **D10** | **Registry numbers are appended, never fitted into gaps.** `ITERATION_VARIABLES` has 94 gaps in 1–177 from retired variables; reusing one silently reinterprets any existing `IN.DAT` naming that number. There is **no cap to raise** — `N_ITERATION_VARIABLES_MAX` is derived as `max(keys)`, so appending 178 raises it automatically and every array sized by it grows. Constraints append from 93, with `lablcc` extended in step. Allocations in [`REGISTRY_ALLOCATIONS.md`](REGISTRY_ALLOCATIONS.md) | 2026-08-31 |
| **D11** | **D5 refined: minimal edits to `process/models/` are permitted, and every change requires the user's approval before merging.** The physics is still frozen — what is licensed is structural work such as extracting a residual so its solution method becomes a driver choice, not changing what a model computes. The approval gate replaces the blanket prohibition. **Unblocks A9–A11** | 2026-08-31 |

---

## Issue register

Open issues only. **Traps — recurring ways to be misled, as opposed to defects to fix — live in
[`../TRAPS.md`](../TRAPS.md)** and are binding on every task.

| # | Issue | Status |
|---|---|---|
| **I-1** | **The editable install pointed at the wrong tree** (`dev_libraries/PROCESS`, at superseded commit `710a75c9`), so runs in their own working directories imported the wrong code silently | **CLOSED** 2026-08-31 — conda env `PROCESS_surgery_env` created by the user; A1 re-ran every gate under it and confirmed **bit-identical** results to the `PROCESS_env` figures. `PROCESS_env` must not be used here |
| **I-2** | **`t_burn_0` is dead code.** `process/models/physics/physics.py:513` writes `times.t_burn_0` with a comment referring to "the convergence loop in `fcnvmc1`, `evaluators.f90`" — a file that no longer exists. The variable has no reader anywhere in `process/`. Evidence that burn time was historically *the* reconciliation variable, and a candidate small independent contribution upstream | **OPEN** — confirm no MFILE-path reader, then propose removal |
| **I-3** | **Superseded documents carried no staleness marking** and read as current | **CLOSED** 2026-08-31 — every one now carries a `> **Document status**` header naming the commit it describes and whether its numbers may be cited. The header distinguishes *stale* from merely *archived*, because `reports/deprecated/` holds both (trap T3) |
| **I-5** | **`st_regression.IN.DAT` was stale and did not solve at `c0ae5b28`** — archived from `710a75c9`, missing `i_tf_turn_type` | **CLOSED** 2026-08-31 by D9's patch: five keys copied verbatim from the base commit's own regression input, carrying `* D9 PATCH` provenance comments. Reproduces the base-input diagnostic bit-for-bit, so the patch is equivalent, not merely sufficient |
| **I-6** | **Two actors in one working tree put commits on the wrong branch.** Orchestrator admin commits landed on `A1-stage0-rebaseline` because the agent had checked it out in the shared tree. Repaired by fast-forwarding `architecture_surgery` (contiguous commits, no history rewritten). Root cause: the protocol said "own branch" where `PROCESS_code_analysis` says **isolated worktree** | **CLOSED** by the protocol amendment at §3 and §9 above — task work now runs in its own `git worktree` |
| **I-7** | **~~No free iteration-variable number exists.~~ Overstated — corrected.** `N_ITERATION_VARIABLES_MAX` is *derived* (`max(keys)`), not a hand-set cap, so appending 178 raises it automatically; arrays grow and `lablxc` self-populates. Nothing hardcodes 177. The real risks are **reusing one of the 94 gaps** (silently reinterprets existing `IN.DAT`s) and two branches independently picking 178 | **DOWNGRADED** — not a blocker; handled by D10 and the allocation table |
| **I-8** | **Wall clock is not measurable at the thresholds the plans use.** Worst within-arm spread **19.6 %** at `n = 5`; 2 SE on a difference of means 3–9 %. A 10 % effect is not resolvable, so the partition plan's stop rule sits *inside* the noise. **Probably contention, not the code**: 16 cores but 7 GB RAM, no thread-pinning set (OpenBLAS defaults to all 16 per process), other sessions concurrent — and the difference being far less noisy than the marginal is the signature of common-mode noise | **OPEN** — A18/F3 fixes the protocol: interleave arms and pair the differences, pin threads, record CPU time as a **diagnostic** (narrow CPU spread against wide wall spread confirms contention), log load and free memory per run. **Run the CPU-time diagnostic first** — it decides whether the rest is warranted |
| **I-9** | **The scenario deck was never under version control.** The repository-root `.gitignore`'s blanket `*.DAT` swallowed `arch_surgery/idf_probe/scenarios/*.IN.DAT`; upstream un-ignores its own decks by name and this one was never added. All four files existed only in one working tree, so **Stage 0 was not reproducible by anyone else**, and D9's "frozen artifact" premise was false as written | **CLOSED** 2026-08-31 — A1 added a scoped `!scenarios/*.IN.DAT` in `arch_surgery/idf_probe/.gitignore` (upstream's own pattern, without editing the shared root file) and committed the deck, 208 KB. Verified the un-ignore also covers *new* files. Audit of `arch_surgery/` found nothing else untracked |
| **I-10** | **Identical work varies by up to 35 % in CPU-seconds, and the cause is not known.** A2's diagnostic shows the runs are CPU-bound (cpu ≈ 99.8 % of wall) and the CPU-time spread tracks the wall-clock spread to two decimals (13.60 % vs 13.64 %; 34.76 % vs 34.77 %, `n = 5`), with all replicates producing one result signature. **This is not a contention signature** — scheduling contention would widen wall clock without widening CPU time. It points at frequency scaling, cache or memory-bandwidth effects, or the WSL2 layer. **Supersedes the earlier reading of I-8 as "probably contention", which this does not support** | **OPEN** — A18 must not assume the cause is known. A2 recommends `perf stat` IPC or thread pinning over `getrusage` |

---

## The queue

### Open and queued

| # | Task | Prereqs | Status |
|---|---|---|---|
| **A1** | **stage0-rebaseline** — env-switched probe at `c0ae5b28`; sweep anatomy; three gates. Report archived at [`../reports/deprecated/A1_stage0_rebaseline.md`](../reports/deprecated/A1_stage0_rebaseline.md) | — | **MERGED** 2026-08-31 (`e9747707`). **All three gates PASS 4/4** under `PROCESS_surgery_env` at `n = 5`: switch-neutrality (0 differing MFILE lines across 11 arms), determinism (bit- and sweep-identical), baseline solves (`ifail = 1` everywhere) |
| **A2** | **module-convergence** — Stage 1, the gating measurement. Report [`../reports/deprecated/A2_module_convergence.md`](../reports/deprecated/A2_module_convergence.md) with the orchestrator's assessment | A1 ✓ | **MERGED** 2026-08-31 (`0c0466c5`). **GATE STOPS THE PARTITION.** No module is the laggard (`S_global ≈ S₁`; M1 joint-last in 82–85 % of loops, never strictly ahead). Predicted saving 4.8–23.2 %, of which the separable feed-forward hoist is 1.7–8.2 % and the partition's own contribution is **3.8 % and 7.2 %** on the two large pulsed tokamaks. **H2/H3 survive** (`k = 1`; `st_regression` has zero live cross-module back edges — open question 1b resolved *for* H2). **H4 refuted** |
| **A3** | **build-reorder** — move `build.run()` to after `PlasmaConfinementTime`. Gate: **bit-identical**. Still worth running as an **integrity check on the dependency graph** even though the partition is stopped — it predicts no change, so any change means the graph missed an edge | A1 ✓ | **QUEUED** — cheap, independent of the partition verdict |
| **A4** | **burn-time-lift** — Stage 3, of the MDA partition | — | **WITHDRAWN** 2026-08-31 — not justified as performance work. A2's measurement, which would have supported them, was taken and does not. Withdrawn rather than deferred: the evidence exists |
| **A5** | **module-solvers** — Stage 4, of the MDA partition | — | **WITHDRAWN** 2026-08-31 — not justified as performance work. A2's measurement, which would have supported them, was taken and does not. Withdrawn rather than deferred: the evidence exists |
| **A6** | **characterise** — Stage 5. Scenario sweep; pulsed and steady-state reported separately; wall clock decomposed into model evaluation, VMCON overhead and I/O | A5 ✓ | QUEUED |
| **A7** | **repo-readme** — [`../../README.md`](../../README.md) written as the study's entry point, plus a delimited fork notice at the top of upstream's root README. Staleness headers added to every superseded document (I-3) | — | **DONE** 2026-08-31 (orchestrator, not a task branch — documentation only, no code) |
| **A8** | **plan-relocation** — move `MDA_PARTITION_EXPERIMENT.md` into `docs/plans/` per the plans convention, and fold the corrected speedup mechanism (feed-forward nodes drop from `S_global ×` to `1 ×`, so `|all|` shrinks as well as the sweep counts) into §3.2 | A1 ✓ (the running agent holds the current path) | QUEUED |
| **A9** | **subdriver-count** *(PROPOSED)* — Stage L0 of [`SUBDRIVER_LIFT_EXPERIMENT.md`](SUBDRIVER_LIFT_EXPERIMENT.md): confirm each nested root-find is on a `run()` path **by invocation counting, not by reading** (trap T1); time them as a fraction of wall clock; record non-convergence. Read-only, no refactor. Its gate decides whether the runtime claim survives | A1 ✓ | **UNBLOCKED** by D11 |
| **A10** | **subdriver-extract** *(PROPOSED)* — Stage L1: extract each residual into a named function behind an env switch, inner solve remaining the default. Gate: switch unset ⇒ bit-identical | A9 ✓ | **UNBLOCKED** by D11 |
| **A11** | **subdriver-lift-one** *(PROPOSED)* — Stage L2: lift the loosest-tolerance, highest-count residual. Primary result is Jacobian accuracy against a bounded reference; runtime secondary and may regress | A10 ✓ | **UNBLOCKED** by D11 |
| **A12** | **subdriver-failure-policy** *(PROPOSED)* — Stage L4, independent of the lift: resolve whether `disp=False` at `pfcoil.py:4909` is deliberate, given the identical call at `superconducting.py:1267` uses `disp=True`. Report as a PROCESS finding | — | **PROPOSED** — runnable without the D5 ruling |
| **A18** | **experiment-framework** — build the shared harness in [`EXPERIMENT_FRAMEWORK.md`](EXPERIMENT_FRAMEWORK.md), steps F1–F6 + F7a: arm selection and identity in `metrics.json`, the registry allocation table with 178 appended, the timing protocol closing I-8, the DSM node map with run-time validation, the read-only `note_subsolve` census, and the correctness + robustness gates. **Framework-only — no behaviour change**, merging under neutrality and determinism alone | A1 ✓ | **PROPOSED — recommended next.** F1–F3 are the minimum before any further experiment: without them arms are unidentifiable and timings unreportable |

### Optional / deferred

**E1–E5 are not authorised for execution** (user, 2026-08-31). Their register, with the reasoning
and the interference analysis, is [`ARCHITECTURE_EXPERIMENT_CANDIDATES.md`](ARCHITECTURE_EXPERIMENT_CANDIDATES.md).

| # | Task | Status |
|---|---|---|
| A13 | **feedforward-hoist** — E1 | DEFERRED |
| A14 | **converge-y** — E2 | DEFERRED |
| A15 | **dsm-sequencing** — E3. **A3 no longer folds into it** while it is deferred | DEFERRED |
| A16 | **convergence-predicate-audit** — E4, read-only | DEFERRED |
| A17 | **fixed-count-scan** — E5, read-only | DEFERRED |
| — | **sequencing-comparison** — retired to [`deprecated/SEQUENCING_COMPARISON_EXPERIMENT.md`](deprecated/SEQUENCING_COMPARISON_EXPERIMENT.md); if revived its home is the `functional_PROCESS` programme, not this one | OUT OF SCOPE |

### User-facing standing items (not tasks)

- ~~Add `upstream` read-only for drift measurement~~ — **DONE**, verified
  (`upstream https://github.com/ukaea/PROCESS.git`).
- ~~Push `architecture_surgery`~~ — **DONE**, verified (0 commits ahead of origin).
- Delete `github.com/wrutten/PROCESS_surgery` — reported done by the user; **not verifiable from
  this session** (no network access to GitHub).
- **Run measurement work when the machine is otherwise idle** (user, 2026-08-31). With 7 GB RAM and
  no thread pinning, concurrent sessions are the leading suspect for I-8's spread.

---

## Known open questions (parked, not blocking)

1. ~~Which module is the laggard?~~ **Answered by A2: none is.** `S_global ≈ S₁ ≈ S₂ ≈ S₃`; M1 is
   joint-last in 82–85 % of loops and never strictly ahead. This is the case §3.2 named as fatal
   and it stopped the experiment.
1b. ~~Does H2 survive its own cheapest test?~~ **Yes.** `st_regression` has zero live cross-module
   back edges and is the most independent of the four scenarios; A1's 39.7 % was not diagnostic.
1c. **Should A13 (feed-forward hoist) be revived?** It is now the **only** intervention with a
   positive expected return — 4.6–8.2 % at `k = 0`, no new design variables, no dimension penalty.
   It was deferred before this evidence existed. **User decision.**
2. **Every task is labeled `A<n>` with a keyword minted at the same time**, and the keyword
   always accompanies the number in prose — queue rows, change-log entries, reports and
   session messages write `A1 (stage0-rebaseline)`, never a bare `A1`. One keyword per task,
   never renamed. The keyword is the branch slug.
3. **Every task runs on its own branch** `A<n>-<keyword>` **in an isolated `git worktree`** off
   `architecture_surgery`, and writes
   a report to [`../reports/`](../reports/) — verdict first, autonomous decisions with their
   reversal paths, append-only change log. Commit messages carry the keyword:
   `A<n> <keyword>: …`.
4. **Reports avoid jargon.** Project shorthand — decision numbers, issue numbers, internal
   vocabulary — is spelled out at first use, so a report reads without the queue open beside it.
5. **The orchestrator appends a critical assessment to every task report** and acts as
   adversarial reviewer.
6. **A failed gate blocks the merge and is reported as a result.** No tuning a gate into
   passing, no conditional merges that defer a fix to a later task. The fix is made on the same
   branch and the task is re-gated as one merge.
7. **Merge discipline**: merges happen from the main checkout, one at a time; the branch is
   deleted with `-d`, never `-D`. At merge the task report is archived to
   [`../reports/deprecated/`](../reports/deprecated/) — the live directory holds only open
   tasks' reports.
8. **Pacing**: the user decides which tasks execute. Only the user adds tasks; agents may
   propose.
9. **Stop background work with `TaskStop`, never `pkill`.** Each sandboxed Bash call has its own
   PID namespace, so `ps` sees nothing from a sibling call and `pkill` kills nothing while
   reporting success (trap T8; A2 lost a set of runs to this).
10. **One actor per working tree.** Never `git commit` or `git checkout` in a tree another agent
   is working in — commits land on whatever branch that agent last checked out (I-6, 2026-08-31).
   The orchestrator's admin work goes on `architecture_surgery` in the main checkout; task work
   goes in its own worktree.
11. **Standing rules**: the sandbox is never overridden (report blockers and ask); never push
   without per-push approval; never modify a sibling clone; the base commit and the models
   are frozen. See [`../../../CLAUDE.md`](../../../CLAUDE.md).

**Work-item terminology** (one word, one meaning):

| Term | Label | Meaning | Rules |
|---|---|---|---|
| **Task** | `A<n>` | A queue row: one branch, one agent, one report, one merge decision | Only the user adds tasks |
| **Subtask** | `A<n>.<k>` | The agent's own decomposition, in its report | Never its own branch or report |
| **Issue** | `I-<n>` | Defect or gap in *this repository or its environment*, found outside a task's scope | Filed below, not fixed in passing |
| **PROCESS finding** | — | Defect or critique of *PROCESS itself* | Architecture critiques belong here; implementation defects go to `PROCESS_code_analysis/docs/bug_reports/` |
| **Decision** | `D<n>` | A recorded user decision | Append-only; a reversal is a new decision referencing the old |

**Numbering** — next free: **A18**, **D10**, **I-9**. Numbers are never reused.

**Optimiser-registry allocation** is administered in
[`REGISTRY_ALLOCATIONS.md`](REGISTRY_ALLOCATIONS.md) — one table, append-only (D10). Every task
takes its numbers from there; two branches allocating independently would both pick the same next
number and merge into a dict with one entry silently winning.

---|---|---|
| Constraints | 82 registered over 1–92, cap 500 | **93** — but `lablcc` has exactly 92 entries and must be extended in step |
| Iteration variables | 83 registered over 1–177, `N_ITERATION_VARIABLES_MAX = 177` | **none** — 177 is taken and the cap is the maximum |

**No iteration-variable block can be reserved until the cap is raised (I-7).** Constraint numbers
from 93 upward are available and will be blocked out when the first lifting task is authorised.

---

## Decisions (live set)

| # | Decision | Date |
|---|---|---|
| **D1** | `wrutten/PROCESS` is the canonical fork. `PROCESS_surgery` is flattened into it — the research artifacts live in `arch_surgery/` inside the fork, not in a separate repo with a submodule. `IPP-SRS` branches (`AST_parseable`, `stage0-probe`) are archived on the fork for reachability but are not merged | 2026-08-31 |
| **D2** | **The base commit is `c0ae5b28`, frozen.** Chosen because it is the last commit before `functional_PROCESS` begins its rewrite and is the ancestor of the dependency-analysis pin — the three studies share one coordinate system. Not to be rebased or re-pinned; `upstream` may be fetched to measure drift only | 2026-08-31 |
| **D3** | **A fresh rewrite.** The `PROCESS_rewritten/` scaffolding on `stage0-probe` (based on `710a75c9`) is not ported | 2026-08-31 |
| **D4** | **The `710a75c9` evidence is discarded**, raw run artifacts deleted. The superseded documents are retained for methodology only; every number is rederived at `c0ae5b28`. Recoverable from `adf863d7` if a specific figure is ever wanted | 2026-08-31 |
| **D5** | **The models are frozen; only the driver changes.** This is what distinguishes this study from `functional_PROCESS`: a rewritten back-end cannot isolate the architecture's contribution, because any measured difference confounds the architecture with the rewrite | 2026-08-31 |
| **D6** | **Correctness is gated on `norm_objf` plus a post-solve feasibility audit, never on iteration variables.** Some iteration variables are not identified by the problem and differ at an unchanged optimum, so an itvar gate generates false alarms | 2026-08-31 |
| **D7** | **A full IDF / MDF / SAND comparison is deferred** to a later study on the `functional_PROCESS` back-end. This experiment is not a stepping stone to it — it is the control that study will need | 2026-08-31 |
| **D8** | **The module partition is derived from the collapsed DSM, not assumed.** M1 Physics = rows 4, 6–28; M2 Coils = rows 5, 29–37; M3 Plant = rows 40–51; `CsFatigue` (38) and rows 52–55 feed-forward; `Pulse` (39) is the articulation point belonging to no module | 2026-08-31 |
| **D9** | **The archived scenario deck is patched in place, not re-pointed at upstream's regression inputs.** `st_regression.IN.DAT` gains `i_tf_turn_type = 2` and the four tape geometries; the other three stay as archived and continue to load via obsolete-name rewriting (A1 autonomous decision 3). Rationale: the deck stays a frozen artifact of this study rather than tracking whatever upstream ships, so a scenario cannot change under a result | 2026-08-31 |
| **D10** | **Registry numbers are appended, never fitted into gaps.** `ITERATION_VARIABLES` has 94 gaps in 1–177 from retired variables; reusing one silently reinterprets any existing `IN.DAT` naming that number. There is **no cap to raise** — `N_ITERATION_VARIABLES_MAX` is derived as `max(keys)`, so appending 178 raises it automatically and every array sized by it grows. Constraints append from 93, with `lablcc` extended in step. Allocations in [`REGISTRY_ALLOCATIONS.md`](REGISTRY_ALLOCATIONS.md) | 2026-08-31 |
| **D11** | **D5 refined: minimal edits to `process/models/` are permitted, and every change requires the user's approval before merging.** The physics is still frozen — what is licensed is structural work such as extracting a residual so its solution method becomes a driver choice, not changing what a model computes. The approval gate replaces the blanket prohibition. **Unblocks A9–A11** | 2026-08-31 |

---

## Issue register

Open issues only. **Traps — recurring ways to be misled, as opposed to defects to fix — live in
[`../TRAPS.md`](../TRAPS.md)** and are binding on every task.

| # | Issue | Status |
|---|---|---|
| **I-1** | **The editable install pointed at the wrong tree** (`dev_libraries/PROCESS`, at superseded commit `710a75c9`), so runs in their own working directories imported the wrong code silently | **CLOSED** 2026-08-31 — conda env `PROCESS_surgery_env` created by the user; A1 re-ran every gate under it and confirmed **bit-identical** results to the `PROCESS_env` figures. `PROCESS_env` must not be used here |
| **I-2** | **`t_burn_0` is dead code.** `process/models/physics/physics.py:513` writes `times.t_burn_0` with a comment referring to "the convergence loop in `fcnvmc1`, `evaluators.f90`" — a file that no longer exists. The variable has no reader anywhere in `process/`. Evidence that burn time was historically *the* reconciliation variable, and a candidate small independent contribution upstream | **OPEN** — confirm no MFILE-path reader, then propose removal |
| **I-3** | **Superseded documents carried no staleness marking** and read as current | **CLOSED** 2026-08-31 — every one now carries a `> **Document status**` header naming the commit it describes and whether its numbers may be cited. The header distinguishes *stale* from merely *archived*, because `reports/deprecated/` holds both (trap T3) |
| **I-5** | **`st_regression.IN.DAT` was stale and did not solve at `c0ae5b28`** — archived from `710a75c9`, missing `i_tf_turn_type` | **CLOSED** 2026-08-31 by D9's patch: five keys copied verbatim from the base commit's own regression input, carrying `* D9 PATCH` provenance comments. Reproduces the base-input diagnostic bit-for-bit, so the patch is equivalent, not merely sufficient |
| **I-6** | **Two actors in one working tree put commits on the wrong branch.** Orchestrator admin commits landed on `A1-stage0-rebaseline` because the agent had checked it out in the shared tree. Repaired by fast-forwarding `architecture_surgery` (contiguous commits, no history rewritten). Root cause: the protocol said "own branch" where `PROCESS_code_analysis` says **isolated worktree** | **CLOSED** by the protocol amendment at §3 and §9 above — task work now runs in its own `git worktree` |
| **I-7** | **~~No free iteration-variable number exists.~~ Overstated — corrected.** `N_ITERATION_VARIABLES_MAX` is *derived* (`max(keys)`), not a hand-set cap, so appending 178 raises it automatically; arrays grow and `lablxc` self-populates. Nothing hardcodes 177. The real risks are **reusing one of the 94 gaps** (silently reinterprets existing `IN.DAT`s) and two branches independently picking 178 | **DOWNGRADED** — not a blocker; handled by D10 and the allocation table |
| **I-8** | **Wall clock is not measurable at the thresholds the plans use.** Worst within-arm spread **19.6 %** at `n = 5`; 2 SE on a difference of means 3–9 %. A 10 % effect is not resolvable, so the partition plan's stop rule sits *inside* the noise. **Probably contention, not the code**: 16 cores but 7 GB RAM, no thread-pinning set (OpenBLAS defaults to all 16 per process), other sessions concurrent — and the difference being far less noisy than the marginal is the signature of common-mode noise | **OPEN** — A18/F3 fixes the protocol: interleave arms and pair the differences, pin threads, record CPU time as a **diagnostic** (narrow CPU spread against wide wall spread confirms contention), log load and free memory per run. **Run the CPU-time diagnostic first** — it decides whether the rest is warranted |
| **I-9** | **The scenario deck was never under version control.** The repository-root `.gitignore`'s blanket `*.DAT` swallowed `arch_surgery/idf_probe/scenarios/*.IN.DAT`; upstream un-ignores its own decks by name and this one was never added. All four files existed only in one working tree, so **Stage 0 was not reproducible by anyone else**, and D9's "frozen artifact" premise was false as written | **CLOSED** 2026-08-31 — A1 added a scoped `!scenarios/*.IN.DAT` in `arch_surgery/idf_probe/.gitignore` (upstream's own pattern, without editing the shared root file) and committed the deck, 208 KB. Verified the un-ignore also covers *new* files. Audit of `arch_surgery/` found nothing else untracked |
| **I-10** | **Identical work varies by up to 35 % in CPU-seconds, and the cause is not known.** A2's diagnostic shows the runs are CPU-bound (cpu ≈ 99.8 % of wall) and the CPU-time spread tracks the wall-clock spread to two decimals (13.60 % vs 13.64 %; 34.76 % vs 34.77 %, `n = 5`), with all replicates producing one result signature. **This is not a contention signature** — scheduling contention would widen wall clock without widening CPU time. It points at frequency scaling, cache or memory-bandwidth effects, or the WSL2 layer. **Supersedes the earlier reading of I-8 as "probably contention", which this does not support** | **OPEN** — A18 must not assume the cause is known. A2 recommends `perf stat` IPC or thread pinning over `getrusage` |

---

## The queue

### Open and queued

| # | Task | Prereqs | Status |
|---|---|---|---|
| **A1** | **stage0-rebaseline** — env-switched probe at `c0ae5b28`; sweep anatomy; three gates. Report archived at [`../reports/deprecated/A1_stage0_rebaseline.md`](../reports/deprecated/A1_stage0_rebaseline.md) | — | **MERGED** 2026-08-31 (`e9747707`). **All three gates PASS 4/4** under `PROCESS_surgery_env` at `n = 5`: switch-neutrality (0 differing MFILE lines across 11 arms), determinism (bit- and sweep-identical), baseline solves (`ifail = 1` everywhere) |
| **A2** | **module-convergence** — Stage 1, the gating measurement. Report [`../reports/deprecated/A2_module_convergence.md`](../reports/deprecated/A2_module_convergence.md) with the orchestrator's assessment | A1 ✓ | **MERGED** 2026-08-31 (`0c0466c5`). **GATE STOPS THE PARTITION.** No module is the laggard (`S_global ≈ S₁`; M1 joint-last in 82–85 % of loops, never strictly ahead). Predicted saving 4.8–23.2 %, of which the separable feed-forward hoist is 1.7–8.2 % and the partition's own contribution is **3.8 % and 7.2 %** on the two large pulsed tokamaks. **H2/H3 survive** (`k = 1`; `st_regression` has zero live cross-module back edges — open question 1b resolved *for* H2). **H4 refuted** |
| **A3** | **build-reorder** — move `build.run()` to after `PlasmaConfinementTime`. Gate: **bit-identical**. Still worth running as an **integrity check on the dependency graph** even though the partition is stopped — it predicts no change, so any change means the graph missed an edge | A1 ✓ | **QUEUED** — cheap, independent of the partition verdict |
| **A4** | **burn-time-lift** — Stage 3, of the MDA partition | — | **WITHDRAWN** 2026-08-31 — not justified as performance work. A2's measurement, which would have supported them, was taken and does not. Withdrawn rather than deferred: the evidence exists |
| **A5** | **module-solvers** — Stage 4, of the MDA partition | — | **WITHDRAWN** 2026-08-31 — not justified as performance work. A2's measurement, which would have supported them, was taken and does not. Withdrawn rather than deferred: the evidence exists |
| **A6** | **characterise** — Stage 5. Scenario sweep; pulsed and steady-state reported separately; wall clock decomposed into model evaluation, VMCON overhead and I/O | A5 ✓ | QUEUED |
| **A7** | **repo-readme** — [`../../README.md`](../../README.md) written as the study's entry point, plus a delimited fork notice at the top of upstream's root README. Staleness headers added to every superseded document (I-3) | — | **DONE** 2026-08-31 (orchestrator, not a task branch — documentation only, no code) |
| **A8** | **plan-relocation** — move `MDA_PARTITION_EXPERIMENT.md` into `docs/plans/` per the plans convention, and fold the corrected speedup mechanism (feed-forward nodes drop from `S_global ×` to `1 ×`, so `|all|` shrinks as well as the sweep counts) into §3.2 | A1 ✓ (the running agent holds the current path) | QUEUED |
| **A9** | **subdriver-count** *(PROPOSED)* — Stage L0 of [`SUBDRIVER_LIFT_EXPERIMENT.md`](SUBDRIVER_LIFT_EXPERIMENT.md): confirm each nested root-find is on a `run()` path **by invocation counting, not by reading** (trap T1); time them as a fraction of wall clock; record non-convergence. Read-only, no refactor. Its gate decides whether the runtime claim survives | A1 ✓ | **UNBLOCKED** by D11 |
| **A10** | **subdriver-extract** *(PROPOSED)* — Stage L1: extract each residual into a named function behind an env switch, inner solve remaining the default. Gate: switch unset ⇒ bit-identical | A9 ✓ | **UNBLOCKED** by D11 |
| **A11** | **subdriver-lift-one** *(PROPOSED)* — Stage L2: lift the loosest-tolerance, highest-count residual. Primary result is Jacobian accuracy against a bounded reference; runtime secondary and may regress | A10 ✓ | **UNBLOCKED** by D11 |
| **A12** | **subdriver-failure-policy** *(PROPOSED)* — Stage L4, independent of the lift: resolve whether `disp=False` at `pfcoil.py:4909` is deliberate, given the identical call at `superconducting.py:1267` uses `disp=True`. Report as a PROCESS finding | — | **PROPOSED** — runnable without the D5 ruling |
| **A18** | **experiment-framework** — build the shared harness in [`EXPERIMENT_FRAMEWORK.md`](EXPERIMENT_FRAMEWORK.md), steps F1–F6 + F7a: arm selection and identity in `metrics.json`, the registry allocation table with 178 appended, the timing protocol closing I-8, the DSM node map with run-time validation, the read-only `note_subsolve` census, and the correctness + robustness gates. **Framework-only — no behaviour change**, merging under neutrality and determinism alone | A1 ✓ | **PROPOSED — recommended next.** F1–F3 are the minimum before any further experiment: without them arms are unidentifiable and timings unreportable |

### Optional / deferred

**E1–E5 are not authorised for execution** (user, 2026-08-31). Their register, with the reasoning
and the interference analysis, is [`ARCHITECTURE_EXPERIMENT_CANDIDATES.md`](ARCHITECTURE_EXPERIMENT_CANDIDATES.md).

| # | Task | Status |
|---|---|---|
| A13 | **feedforward-hoist** — E1 | DEFERRED |
| A14 | **converge-y** — E2 | DEFERRED |
| A15 | **dsm-sequencing** — E3. **A3 no longer folds into it** while it is deferred | DEFERRED |
| A16 | **convergence-predicate-audit** — E4, read-only | DEFERRED |
| A17 | **fixed-count-scan** — E5, read-only | DEFERRED |
| — | **sequencing-comparison** — retired to [`deprecated/SEQUENCING_COMPARISON_EXPERIMENT.md`](deprecated/SEQUENCING_COMPARISON_EXPERIMENT.md); if revived its home is the `functional_PROCESS` programme, not this one | OUT OF SCOPE |

### User-facing standing items (not tasks)

- ~~Add `upstream` read-only for drift measurement~~ — **DONE**, verified
  (`upstream https://github.com/ukaea/PROCESS.git`).
- ~~Push `architecture_surgery`~~ — **DONE**, verified (0 commits ahead of origin).
- Delete `github.com/wrutten/PROCESS_surgery` — reported done by the user; **not verifiable from
  this session** (no network access to GitHub).
- **Run measurement work when the machine is otherwise idle** (user, 2026-08-31). With 7 GB RAM and
  no thread pinning, concurrent sessions are the leading suspect for I-8's spread.

---

## Known open questions (parked, not blocking)

1. **Which module is the laggard?** Everything in the speedup argument turns on it. A2's
   central measurement.
1b. **Does H2 survive its own cheapest test?** `st_regression` has `i_pulsed_plant = 0`, so the
   burn-time cycle is structurally absent — the MDA partition plan §2.3 treats it as a free
   control that should partition cleanly. A1 measured its above-floor sweep fraction at
   **39.7 %**, sitting *between* the two pulsed cases (37.8 %, 42.1 %) rather than below them.
   Sweep count is not coupling and the scenario differs in `itart` and `nvar` too, so this is not
   a refutation — but the cheapest test of H2 has returned a sign H2 does not predict. **A2 must
   resolve this before the partition is built.**
2. Post-lift, does `Pulse` (row 39) join a module or remain a standalone feed-forward node?
3. Rows 52–55 (`Objective`, `Constraints`) are downstream of everything — can the objective be
   evaluated without re-running M3?
4. How many upstream commits now separate `c0ae5b28` from `ukaea/main`, and must the write-up
   state that drift?

---

## Change log

| Date | Entry |
|---|---|
| 2026-08-31 | Queue opened. Repository flattened into the `wrutten/PROCESS` fork (D1); base commit fixed at `c0ae5b28` (D2); `710a75c9` evidence discarded (D4). Experiment plan written and revised after the DSM module decomposition (D8) and the withdrawal of the `b_plasma_vertical_required` finding (I-4). A1 (stage0-rebaseline) dispatched. |
| 2026-08-31 | Subdriver-lift experiment planned ([`SUBDRIVER_LIFT_EXPERIMENT.md`](SUBDRIVER_LIFT_EXPERIMENT.md)); A9–A12 proposed, A9–A11 blocked on a D5 ruling. Superseded IDF plan moved to `reports/deprecated/`, architecture evaluation to `reports/`. **A1 (stage0-rebaseline) was dispatched before this protocol existed** — its original brief said to commit to `architecture_surgery` and to write its report to `idf_probe/STAGE0.md`; it was corrected in flight to branch `A1-stage0-rebaseline` and to report at `reports/A1_stage0_rebaseline.md`, and given the hard rules (sandbox never overridden, no sibling-clone writes, no `git add -A`). |
| 2026-08-31 | Subdriver-lift experiment **reframed around robustness** (primary), gradient quality secondary, performance penalty measured and reported as two separate numbers rather than netted; its Stage L0 gate moved from wall-clock share to failure incidence. Portfolio of further candidates added ([`ARCHITECTURE_EXPERIMENT_CANDIDATES.md`](ARCHITECTURE_EXPERIMENT_CANDIDATES.md)) with A13–A17 proposed — E1/E4/E5 need no D5 ruling. Interference between the two planned experiments analysed: **optimiser-registry ranges now reserved above**, and §2.4 records that the partition's outcome changes what the subdriver experiment *is* (a lifted residual gains a second possible host — the module's own solver — which costs no dimension), so the partition resolves first. |
| 2026-08-31 | **A1 (stage0-rebaseline) complete, not merged.** Gates (a) switch-neutrality and (b) determinism PASS — (a) verified more strongly than specified, against a pristine `git archive` arm on hex float literals plus whole-MFILE identity. Gate (c) **FAILS** on `st_regression` (I-5), a stale input that also fails on the pristine base commit; the agent held the gate at FAIL rather than adopting a working diagnostic input, which is the behaviour protocol §6 asks for. Frozen pending the scenario ruling (open question 0b). New issues **I-5** (stale scenario), **I-6** (shared-tree branch mishap, closed by amending §3/§9 to isolated worktrees), **I-7** (no free iteration-variable number — blocks every lifting task), **I-8** (7.9 % wall-clock noise versus gates set at 10–25 %). Registry reservation table replaced with A1's measured state. Sweep anatomy: mean 3.2–3.5 sweeps per `call_models`, 38–42 % of sweeps above the 2-sweep floor, and **94–96 % of all sweeps are finite-difference gradient perturbations**. |
| 2026-08-31 | **D9** ruled: patch `st_regression.IN.DAT` in place rather than re-pointing the deck at upstream's regression inputs, keeping the scenario set a frozen artifact of this study. A1 (stage0-rebaseline) re-dispatched to apply the patch and re-run all three gates on its own branch, per protocol §6 — one merge, re-gated, no deferred fix. Isolated-worktree convention (§3, §9) takes effect from A2 onward; A1's fix continues in the main checkout by sequential handoff, with no concurrent git access. |
| 2026-08-31 | **A1 (stage0-rebaseline) MERGED** (`e9747707`) — all three gates PASS 4/4 under `PROCESS_surgery_env` at `n = 5`; patching an input disturbed neither switch-neutrality nor determinism, which was the point of re-gating the whole task. **I-1 and I-5 CLOSED**; **I-9 filed and closed** (the scenario deck had never been under version control — the root `.gitignore`'s `*.DAT` swallowed it, so Stage 0 was not reproducible by anyone else and D9's "frozen artifact" premise was false as written). **I-8 revised upward**: worst within-arm wall-clock spread is 19.6 % at `n = 5`, so a 10 % effect is not measurable here and the partition plan's stop rule sits inside the noise. **I-7 downgraded** — the cap is derived, so appending is a one-entry change (D10, allocation table added). **Open question 1b filed**: `st_regression`, the free control for H2, does not behave as the plan predicts. E1–E5 moved to Optional / deferred; the sequencing comparison retired out of scope. Framework plan added, proposed as **A18**. |
| 2026-08-31 | **A2 (module-convergence) MERGED** (`0c0466c5`) — **the Stage-1 gate stops the MDA partition experiment.** No module is the laggard; the partition's own contribution is 3.8–7.2 % on the two large pulsed tokamaks against a 25 % gate, and most of the total saving belongs to the separable feed-forward hoist. **H2 and H3 survive** — `k = 1` confirmed, `st_regression` has zero live cross-module back edges, so open question 1b resolves *for* the hypothesis and A1's 39.7 % was not diagnostic. **H4 refuted.** A4 and A5 **withdrawn** (not deferred — the measurement exists); A3 stays queued as a dependency-graph integrity check; **A13 returned to the user as open question 1c**, being the only remaining positive-return item. New: **I-10** (identical work varies 35 % in CPU-seconds, cause unknown — supersedes the contention reading of I-8), traps **T7** (ten models call `run()` from `output()`) and **T8** (`pkill` is inert across sandboxed Bash calls), and protocol §9 (`TaskStop`, not `pkill`). Third instance of T1 found and withdrawn — it was the orchestrator's own citation in the partition plan. |
