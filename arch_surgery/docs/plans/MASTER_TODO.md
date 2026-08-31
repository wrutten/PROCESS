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
9. **One actor per working tree.** Never `git commit` or `git checkout` in a tree another agent
   is working in — commits land on whatever branch that agent last checked out (I-6, 2026-08-31).
   The orchestrator's admin work goes on `architecture_surgery` in the main checkout; task work
   goes in its own worktree.
10. **Standing rules**: the sandbox is never overridden (report blockers and ask); never push
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

**Numbering** — next free: **A18**, **D9**, **I-5**. Numbers are never reused.

**Reserved optimiser-registry ranges.** Both planned experiments mint new entries in
`process/core/solver/iteration_variables.py` (`ITERATION_VARIABLES`, number-keyed;
`N_ITERATION_VARIABLES_MAX` derives from `max(keys)`) and in
`process/core/solver/constraints.py` (82 constraints, registered by number). Developed on
separate branches both would take the next free number, collide at merge, and produce
**different numberings per branch** — so an `IN.DAT` written against one is silently
misread by the other. Ranges are therefore reserved here before any task starts, and a task
takes numbers only from its own range:

A1 (stage0-rebaseline) §8 measured the registries at `c0ae5b28`, and the result **blocks
allocation**:

| Registry | State at `c0ae5b28` | First free |
|---|---|---|
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

---

## Issue register

Open issues only.

| # | Issue | Status |
|---|---|---|
| **I-1** | **The editable install points at the wrong tree.** `pip show process` reports `Editable project location: /home/wrutten/dev_libraries/PROCESS` — a different clone at the superseded commit `710a75c9`. `import process` resolves to the surgery tree only when cwd is the repo root; probe runs execute in their own work directories, so they would silently import the wrong code and every measurement would be invalid | **OPEN** — being addressed by A1 (stage0-rebaseline) as its first action |
| **I-2** | **`t_burn_0` is dead code.** `process/models/physics/physics.py:513` writes `times.t_burn_0` with a comment referring to "the convergence loop in `fcnvmc1`, `evaluators.f90`" — a file that no longer exists. The variable has no reader anywhere in `process/`. Evidence that burn time was historically *the* reconciliation variable, and a candidate small independent contribution upstream | **OPEN** — confirm no MFILE-path reader, then propose removal |
| **I-3** | **The superseded documents carry no staleness marking.** `IDF_EXPERIMENT_PLAN.md`, `PROCESS_architecture_evaluation.md`, `idf_probe/MEMO.md` and `NOISE_ANALYSIS.md` all describe the `710a75c9` study and read as current | **OPEN** — A7 (repo-readme) adds headers |
| **I-4** | **Name-level dependency analysis conflates `run()` and `output()`.** `physics.b_plasma_vertical_required` looked like a Coils→Physics feedback edge but the read is inside `PlasmaFields.output()`, a report-writing method outside the MDA. Any instrument that greps attribute access must exclude `output()` paths | **OPEN** — binding on A2 (module-convergence)'s instrument |
| **I-5** | **`st_regression.IN.DAT` is stale and does not solve at `c0ae5b28`.** Archived from `710a75c9`; sets `i_tf_sc_mat = 9` (REBCO tape) but not `i_tf_turn_type`, which defaults to cable-in-conduit, so the CICC model raises on the first `fcnvmc1` call. Reproduces on a pristine `c0ae5b28` archive, so it is the input, not the probe. The base commit's own `tests/regression/input_files/st_regression.IN.DAT` adds `i_tf_turn_type = 2` and solves. **Costs the MDA partition plan its only `i_pulsed_plant = 0` control** | **OPEN** — needs a `D<n>` ruling (open question 0b); blocks A1's merge |
| **I-6** | **Two actors in one working tree put commits on the wrong branch.** Orchestrator admin commits landed on `A1-stage0-rebaseline` because the agent had checked it out in the shared tree. Repaired by fast-forwarding `architecture_surgery` (contiguous commits, no history rewritten). Root cause: the protocol said "own branch" where `PROCESS_code_analysis` says **isolated worktree** | **CLOSED** by the protocol amendment at §3 and §9 above — task work now runs in its own `git worktree` |
| **I-7** | **No free iteration-variable number exists.** `N_ITERATION_VARIABLES_MAX = 177` and 177 is taken, so any task that lifts a variable to the optimiser — A4 (burn-time-lift), A9–A11 (subdriver lift) — must first raise the cap in `numerics.py`, or reuse a retired gap, which would **silently reinterpret existing `IN.DAT` files**. The cap is outside `process/models/`, so raising it is D5-safe, but it is a shared change that must land once, not per branch | **OPEN** — blocks all lifting tasks |
| **I-8** | **Wall clock is not yet a measurable quantity.** Two bit-identical baseline runs differ by up to **7.9 %** in wall time. The MDA partition plan's Stage-1 gate ("> 25 % predicted saving") and stop rule ("< 10 %") sit inside or near that band, and **no plan specifies a repetition count or a confidence interval** | **OPEN** — A2 (module-convergence) must fix the timing protocol before reporting any timing |

---

## The queue

### Open and queued

| # | Task | Prereqs | Status |
|---|---|---|---|
| **A1** | **stage0-rebaseline** — env-switched probe at `c0ae5b28`; sweep anatomy; three gates. Report [`../reports/A1_stage0_rebaseline.md`](../reports/A1_stage0_rebaseline.md) with the orchestrator's assessment appended | — | **COMPLETE, NOT MERGED — gate (c) FAILED.** Gates (a) switch-neutrality and (b) determinism PASS; (c) baseline-solves fails on `st_regression`, a stale input archived from `710a75c9` that also fails on the pristine base commit. Frozen under protocol §6 pending the scenario-set ruling (open question 0b) |
| **A2** | **module-convergence** — Stage 1, the gating measurement. Attribute per-sweep state change to M1 / M2 / M3 to obtain `S₁, S₂, S₃` and identify the laggard; confirm at runtime that `t_plant_pulse_burn` is the only cross-module coupler in a `run()` path. **Instrument must exclude `output()` (I-4).** Gate: predicted saving, with a stop rule if M1 is the laggard | A1 ✓ | QUEUED |
| **A3** | **build-reorder** — Stage 2. Move `build.run()` to after `PlasmaConfinementTime`. Gate: **bit-identical** results. Expected to be inert; it is a sharp integrity check on the dependency graph | A1 ✓ | QUEUED |
| **A4** | **burn-time-lift** — Stage 3. Lift `t_plant_pulse_burn` to a design variable with a consistency constraint; verify module independence before adding any solver. Report the `n → n+1` overhead separately from the partition's effect | A2 ✓, A3 ✓ | QUEUED |
| **A5** | **module-solvers** — Stage 4. Per-module solvers; retire the global loop. Gate: correctness as D6, plus measured `Sᵢ` against A2's prediction | A4 ✓ | QUEUED |
| **A6** | **characterise** — Stage 5. Scenario sweep; pulsed and steady-state reported separately; wall clock decomposed into model evaluation, VMCON overhead and I/O | A5 ✓ | QUEUED |
| **A7** | **repo-readme** — write the repository README for the flattened fork: what this is, the base-commit rationale, the relationship to `functional_PROCESS` and `PROCESS_code_analysis`, and where to start. Add staleness headers to the superseded documents (I-3) | — | QUEUED — awaiting user prompt |
| **A8** | **plan-relocation** — move `MDA_PARTITION_EXPERIMENT.md` into `docs/plans/` per the plans convention, and fold the corrected speedup mechanism (feed-forward nodes drop from `S_global ×` to `1 ×`, so `|all|` shrinks as well as the sweep counts) into §3.2 | A1 ✓ (the running agent holds the current path) | QUEUED |
| **A9** | **subdriver-count** *(PROPOSED)* — Stage L0 of [`SUBDRIVER_LIFT_EXPERIMENT.md`](SUBDRIVER_LIFT_EXPERIMENT.md): confirm each nested root-find is on a `run()` path **by invocation counting, not by reading** (I-4); time them as a fraction of wall clock; record non-convergence. Read-only, no refactor. Its gate decides whether the runtime claim survives | A1 ✓ | **BLOCKED** on the D5 ruling (open question 1) |
| **A10** | **subdriver-extract** *(PROPOSED)* — Stage L1: extract each residual into a named function behind an env switch, inner solve remaining the default. Gate: switch unset ⇒ bit-identical | A9 ✓ | **BLOCKED** on the D5 ruling |
| **A11** | **subdriver-lift-one** *(PROPOSED)* — Stage L2: lift the loosest-tolerance, highest-count residual. Primary result is Jacobian accuracy against a bounded reference; runtime secondary and may regress | A10 ✓ | **BLOCKED** |
| **A12** | **subdriver-failure-policy** *(PROPOSED)* — Stage L4, independent of the lift: resolve whether `disp=False` at `pfcoil.py:4909` is deliberate, given the identical call at `superconducting.py:1267` uses `disp=True`. Report as a PROCESS finding | — | **PROPOSED** — runnable without the D5 ruling |
| **A13** | **feedforward-hoist** *(PROPOSED)* — E1 of [`ARCHITECTURE_EXPERIMENT_CANDIDATES.md`](ARCHITECTURE_EXPERIMENT_CANDIDATES.md): run the DSM's feed-forward nodes once after the fixed point instead of every sweep. Pure `caller.py`, **no new design variables, no dimension penalty**. Gate: exact agreement on `norm_objf` and the full MFILE | A2 ✓ | **PROPOSED** — no D5 ruling needed |
| **A14** | **converge-y** *(PROPOSED)* — E2: converge the coupling variables instead of objective and constraints (finding F3), moving objective/constraint evaluation out of the loop. Pure `caller.py`. Judge on gradient quality and robustness, **not** sweep count — the criterion changes meaning | A2 ✓ (supplies the coupling set) | **PROPOSED** — no D5 ruling needed |
| **A15** | **dsm-sequencing** *(PROPOSED)* — E3: reorder `_call_models_once` to the sequenced DSM. **A3 (build-reorder) folds into this** — otherwise two tasks reorder the same sequence and neither is attributable. Not expected to be result-neutral (finding F4), so the gate is `norm_objf` plus feasibility, and every changed result must be explained by a named edge | A2 ✓ | **PROPOSED** — supersedes A3 if adopted |
| **A16** | **convergence-predicate-audit** *(PROPOSED)* — E4: measure how often `MDA_Idempotence` (objective+constraints) and `MDA_Output` (successive MFILEs) disagree, given only the second is reported to the user (finding F12). **Read-only, no code change** | A1 ✓ | **PROPOSED** — no D5 ruling needed |
| **A17** | **fixed-count-scan** *(PROPOSED)* — E5: scan the tokamak path for unrolled iteration with a literal trip count and no convergence test (finding F11, found in the stellarator path, unchecked for tokamak). **Read-only.** Naturally folded into A9 (subdriver-count) | A1 ✓ | **PROPOSED** — no D5 ruling needed |

### User-facing standing items (not tasks)

- Delete `github.com/wrutten/PROCESS_surgery` — orphaned, superseded by the flattened fork.
- Add `upstream` (`https://github.com/ukaea/PROCESS.git`) read-only, for drift measurement.
- Push `architecture_surgery` — commit `98615eb3` and everything since awaits per-push approval.

---

## Known open questions (parked, not blocking)

0. **Does D5's model freeze permit lifting a subdriver residual?** **BLOCKING** for A9–A11.
   Lifting requires edits under `process/models/` to expose residuals. Narrow reading: out of
   scope. Refined reading: the residual *expressions* are frozen while the *method of driving
   them to zero* is architecture, and is exactly this project's independent variable. A
   switch-gated extraction keeps the frozen path byte-identical either way. Needs a recorded
   `D9`. See [`SUBDRIVER_LIFT_EXPERIMENT.md`](SUBDRIVER_LIFT_EXPERIMENT.md) §3.4.
0b. **Does the scenario set re-point at `tests/regression/input_files/`?** **BLOCKING** A1's
   merge. The archived scenarios came from `710a75c9`; one no longer solves (I-5) and the other
   three need obsolete-name rewriting to load at all. Re-pointing at the base commit's own
   regression inputs fixes both and keeps the deck aligned with the frozen tree — at the cost
   that the deck is then whatever upstream ships rather than a frozen artifact of this study.
   Needs a recorded `D<n>`.
1. **Which module is the laggard?** Everything in the speedup argument turns on it. A2's
   central measurement.
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
