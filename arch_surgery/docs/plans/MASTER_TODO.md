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
3. **Every task runs on its own branch** `A<n>-<keyword>` off `architecture_surgery` and writes
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
9. **Standing rules**: the sandbox is never overridden (report blockers and ask); never push
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

**Numbering** — next free: **A9**, **D9**, **I-5**. Numbers are never reused.

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

---

## The queue

### Open and queued

| # | Task | Prereqs | Status |
|---|---|---|---|
| **A1** | **stage0-rebaseline** — reinstate an env-switched probe against `c0ae5b28`; measure sweep anatomy for all four scenarios; pass the switch-neutrality, determinism and baseline-solve gates. Deliverables: probe, rewritten `idf_probe/README.md`, `idf_probe/STAGE0.md` | — | **IN PROGRESS** (dispatched 2026-08-31) |
| **A2** | **module-convergence** — Stage 1, the gating measurement. Attribute per-sweep state change to M1 / M2 / M3 to obtain `S₁, S₂, S₃` and identify the laggard; confirm at runtime that `t_plant_pulse_burn` is the only cross-module coupler in a `run()` path. **Instrument must exclude `output()` (I-4).** Gate: predicted saving, with a stop rule if M1 is the laggard | A1 ✓ | QUEUED |
| **A3** | **build-reorder** — Stage 2. Move `build.run()` to after `PlasmaConfinementTime`. Gate: **bit-identical** results. Expected to be inert; it is a sharp integrity check on the dependency graph | A1 ✓ | QUEUED |
| **A4** | **burn-time-lift** — Stage 3. Lift `t_plant_pulse_burn` to a design variable with a consistency constraint; verify module independence before adding any solver. Report the `n → n+1` overhead separately from the partition's effect | A2 ✓, A3 ✓ | QUEUED |
| **A5** | **module-solvers** — Stage 4. Per-module solvers; retire the global loop. Gate: correctness as D6, plus measured `Sᵢ` against A2's prediction | A4 ✓ | QUEUED |
| **A6** | **characterise** — Stage 5. Scenario sweep; pulsed and steady-state reported separately; wall clock decomposed into model evaluation, VMCON overhead and I/O | A5 ✓ | QUEUED |
| **A7** | **repo-readme** — write the repository README for the flattened fork: what this is, the base-commit rationale, the relationship to `functional_PROCESS` and `PROCESS_code_analysis`, and where to start. Add staleness headers to the superseded documents (I-3) | — | QUEUED — awaiting user prompt |
| **A8** | **plan-relocation** — move `MDA_PARTITION_EXPERIMENT.md` into `docs/plans/` per the plans convention, and fold the corrected speedup mechanism (feed-forward nodes drop from `S_global ×` to `1 ×`, so `|all|` shrinks as well as the sweep counts) into §3.2 | A1 ✓ (the running agent holds the current path) | QUEUED |

### User-facing standing items (not tasks)

- Delete `github.com/wrutten/PROCESS_surgery` — orphaned, superseded by the flattened fork.
- Add `upstream` (`https://github.com/ukaea/PROCESS.git`) read-only, for drift measurement.
- Push `architecture_surgery` — commit `98615eb3` and everything since awaits per-push approval.

---

## Known open questions (parked, not blocking)

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
