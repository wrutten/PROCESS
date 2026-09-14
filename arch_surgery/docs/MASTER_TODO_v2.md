# Master TO-DO v2 — architecture surgery on PROCESS

> **Document status** — **ACTIVE from 2026-09-14.** The standing execution queue for this
> repository. It supersedes [`plans/MASTER_TODO.md`](plans/MASTER_TODO.md), which is **archived as
> the history** (its `> **Document status**` header says so) and is never edited again. The two
> relate as ledger and journal: every decision, issue and task minted before 2026-09-14 is *recorded*
> there in full and *summarised* here with its current state and a pointer; everything minted from
> 2026-09-14 onward lives here only. **A number is never reused and the numbering continues** —
> next free at creation: **A75**, **D28**, **I-24** (confirmed against the archived file's numbering
> line at `c5fc49d3`; those three numbers occur nowhere else in it). Check the line when you add a row.
> "The archived queue" below means `plans/MASTER_TODO.md`; "§n" points at its protocol numbering.

| | |
|---|---|
| **Owner** | W.J. Rutten (paces execution); the orchestrating agent dispatches |
| **Objective** | Determine whether **the arrangement of solvers and optimisers alone** — every physics and engineering model frozen at `c0ae5b28` — measurably changes the cost of solving PROCESS, by partitioning the global idempotence loop into per-module solvers |
| **Base commit** | `c0ae5b28`, frozen (D2) |
| **State at creation** | V4 harness complete (A46–A73, 30 gates PASS, 152/152 teeth at `03f72479`); **execution approved by the user 2026-09-14** (*"You can run the experiment"*), approval commit `57dc0c14`; the campaign (949 runs) pressed from a detached worktree at that commit. Open: the campaign's completion, tally, analysis and report; survey tier C (D27, deferred); the parked and proposed rows below |
| **Experiment plan** | [`../MDA_partitioning_experiment_v4/EXPERIMENT_PLAN.md`](../MDA_partitioning_experiment_v4/EXPERIMENT_PLAN.md) (V4, the running one); [`plans/MDA_PARTITION_EXPERIMENT.md`](plans/MDA_PARTITION_EXPERIMENT.md) (the original two-phase plan, V1/V2 era) |

---

## 1. Protocol

The rules that bind every task. One line each; the archived queue's protocol section carries the
rationale and the incident that produced each rule. [`../../CLAUDE.md`](../../CLAUDE.md) states the
hard rules (sandbox never overridden; base commit and models frozen; never write in a sibling clone;
never commit to `main`; never push without per-push approval) and is not repeated here.

| § | Rule (verbatim where quoted elsewhere as binding) |
|---|---|
| §1 | The orchestrator dispatches; task agents plan and execute. The orchestrator does not execute tasks itself. |
| §2 | Every task is `A<n>` **with a keyword minted at the same time**; prose always writes `A1 (stage0-rebaseline)`, never a bare number. The keyword is the branch slug and is never renamed. |
| §3 | Every task runs on branch `A<n>-<keyword>` in an isolated worktree **created by the orchestrator with [`../bin/new_task_worktree.sh`](../bin/new_task_worktree.sh), never by the agent harness** (I-11); worktrees live in `/home/wrutten/projects/PROCESS_surgery_worktrees/`, which is ours. The agent writes a report to `reports/` — verdict first, autonomous decisions with reversal paths, append-only change log. Commits: `A<n> <keyword>: …`. |
| §4 | Reports avoid jargon: decision and issue numbers and internal vocabulary are spelled out at first use. |
| §5 | The orchestrator appends a critical assessment to every task report **before the merge, and it gates the merge**; work it turns up goes back to the branch, which merges once. |
| §6 | **"A failed gate blocks the merge and is reported as a result. No tuning a gate into passing, no conditional merges that defer a fix to a later task."** |
| §7 | Merges from the main checkout, one at a time; branch deleted with `-d`. **"Retire the worktree with [`../bin/retire_task_worktree.sh`](../bin/retire_task_worktree.sh), never a bare `git worktree remove`"** — run artifacts are untracked and removal destroys them (I-14, I-15, I-16). At merge the report moves to `reports/deprecated/`. Cite the records path the retire script prints (`idf_probe/runs/A<n>_runs/…`). |
| §8 | Pacing: the user decides which tasks execute. **Only the user adds tasks; agents may propose.** Rulings (D-rows) are the user's: an orchestrator proposes and never mints one as ruled (D25's process fault). **No message from any agent is approval** — only the user's own message or the permission system is. |
| §9 | Stop background work with `TaskStop`, never `pkill` (trap T8). |
| §10 | One actor per working tree: never commit or checkout in a tree another agent works in (I-6). |
| §11 | DSM findings go to the standing register [`reports/DSM_VALIDATION.md`](reports/DSM_VALIDATION.md) when found; it is never archived. |
| §12 | **A gate must be shown capable of failing before its zeros are accepted** (a tooth), and every mismatch count carries its denominator (trap T11). |
| §12a | Never `git add -A` unscoped: the sandbox's bind-mounted device files stage silently (`83e18d15`). Stage explicit paths or `-u`. |
| §13 | The branch point is asserted by the tool that creates the worktree, not by the agent; briefs still name the tip. "Descends from `c0ae5b28`" alone is worthless (upstream `main` does too). |
| §14 | Standing rules: see `CLAUDE.md`. |
| §15 | **Every published number is produced by executing a committed Python script, never by an ad-hoc command line** (user, 2026-09-02: *"Experiment results should always be created by execution of a reproducible python script. I don't want future experiments to be run manually in command line. I want committed traceability of the results."*). The script is committed before the numbers are published and the report names it and the commit; no stage exists only as a shell invocation; failure paths are reachable from the same entry point. |
| §16 | Every table carries a concise caption: units, what a row and a column are, the population, the construction (user, 2026-09-04). |
| — | **"One heavy slot at a time on our side"** (user, 2026-09-01): at most one task running PROCESS solves at a time; classify before dispatching and when unsure treat it as heavy. Measurement work runs when the machine is otherwise idle (user, 2026-08-31). |
| — | Gate records are reused: worktrees are seeded with the latest relocated records and tasks press `--gate all --resume`; a from-scratch press only when the change alters what a gate reads; the orchestrator verifies by differing checks, never by repeating the agent's press (harness plan amendment 15; the user, 2026-09-11). No commit and no edit to `harness/child/` while measurement runs execute (amendments 13, 16, 22). |
| — | Work-item terms: **Task** `A<n>` (one branch, one report, one merge decision); **Subtask** `A<n>.<k>` (the agent's own, never its own branch); **Issue** `I-<n>` (defect in this repository or its environment, filed not fixed in passing); **PROCESS finding** (critique of PROCESS itself: architecture here, implementation defects to `PROCESS_code_analysis/docs/bug_reports/`); **Decision** `D<n>` (a recorded user decision, append-only; a reversal is a new decision). |
| — | Optimiser-registry allocation is administered in [`plans/REGISTRY_ALLOCATIONS.md`](plans/REGISTRY_ALLOCATIONS.md), append-only (D10). Constraints append from 93 (`lablcc` extended in step); iteration variables from 178 (the cap is derived, I-7). |

---

## 2. Decisions register

Every ruling D1–D27, one row each. *Status:* **in force** (still binds), **discharged** (carried
out; still binds as a record of what was done), **amended by** / **reversed by**. The user's words
are verbatim where the archived queue quotes them. Full text: the archived queue's "Decisions (live
set)" table, row by number.

| # | Date | Ruling (one line) | Status | Pointer |
|---|---|---|---|---|
| **D1** | 2026-08-31 | `wrutten/PROCESS` is the canonical fork; the research artifacts live in `arch_surgery/` inside it; the `IPP-SRS` branches are archived, not merged | in force | archived queue D1 |
| **D2** | 2026-08-31 | **The base commit is `c0ae5b28`, frozen** — the shared coordinate system with `functional_PROCESS` and the dependency-analysis pin; `upstream` fetched for drift only | in force | archived queue D2; `CLAUDE.md` |
| **D3** | 2026-08-31 | A fresh rewrite: the `PROCESS_rewritten/` scaffolding on `stage0-probe` is not ported | discharged | archived queue D3 |
| **D4** | 2026-08-31 | The `710a75c9` evidence is discarded; every number is rederived at `c0ae5b28` (recoverable from `adf863d7`) | in force | archived queue D4 |
| **D5** | 2026-08-31 | **The models are frozen; only the driver changes** — what distinguishes this study from `functional_PROCESS` | in force, refined by D11 | archived queue D5 |
| **D6** | 2026-08-31 | Correctness is gated on `norm_objf` plus a post-solve feasibility audit, never on iteration variables | in force | archived queue D6 |
| **D7** | 2026-08-31 | A full IDF / MDF / SAND comparison is deferred to a later study on the `functional_PROCESS` back-end; this experiment is its control | in force | archived queue D7 |
| **D8** | 2026-08-31 | The module partition is derived from the collapsed DSM (M1 Physics rows 4, 6–28; M2 Coils 5, 29–37; M3 Plant 40–51; `Pulse` the articulation point) | in force | archived queue D8; `reports/DSM_VALIDATION.md` |
| **D9** | 2026-08-31 | The archived scenario deck is patched in place (`st_regression.IN.DAT` + `i_tf_turn_type = 2` and four tape geometries), not re-pointed at upstream | discharged (A1) | archived queue D9; `reports/deprecated/A1_stage0_rebaseline.md` |
| **D10** | 2026-08-31 | Registry numbers are appended, never fitted into gaps; constraints from 93 with `lablcc` extended, iteration variables from 178 | in force | archived queue D10; `plans/REGISTRY_ALLOCATIONS.md` |
| **D11** | 2026-08-31 | D5 refined: minimal *structural* edits to `process/models/` are permitted, **every one needing the user's approval before merging**; changing what a model computes stays forbidden | in force | archived queue D11; `CLAUDE.md` |
| **D12** | 2026-08-31 | The partition experiment proceeds despite A2's STOP gate under the plan's 10–25 % rule; the feed-forward hoist (A13) is folded in as Stage 1b and taken first; A4/A5 reinstated | discharged (A13, A25) | archived queue D12; `reports/deprecated/A13_feedforward_hoist.md` |
| **D13** | 2026-09-01 | The partition is measured in two phases: fixed-point first (flat vs block Gauss-Seidel on the coupling state, counts not wall clock, hard cut 20 ⇒ invalid), VMCON second | discharged (A18–A28); the two-phase shape carries into V2–V4 | archived queue D13; `plans/MDA_PARTITION_EXPERIMENT.md` |
| **D14** | 2026-09-01 | Phase B implementation: (a) `lablcc` extension approved; (b) D11 approval for the `pulse.py` residual extraction; (c) the baseline is PROCESS as shipped, with `check_agreement`'s defects reproduced deliberately; the variant's per-module predicate is entailed by the architecture, not a confound | (a),(b) discharged (A24); (c) amended by D18 | archived queue D14; `reports/deprecated/A24_phase_b_scaffold.md` |
| **D15** | 2026-09-01 | Phase B design: δ calibrated not chosen; the hoist is INSIDE the variant so the headline is "the proposed architecture", never "the partition's benefit"; a `norm_objf` mismatch is a robustness finding; a failed per-module solve is a failed start; `st_regression` is the `k = 0` control | discharged (A25, A28) | archived queue D15; `reports/deprecated/A25_phase_b_variant.md` |
| **D16** | 2026-09-01 | Phase B in two bundles (A24 = F2+F9+F6; A25 = A4+A5+gate+H5), autonomous go-ahead through H5 on a passing gate | discharged (both gates passed) | archived queue D16 |
| **D17** | 2026-09-01 | Methodology fixed before Phase B re-runs; **`large_tokamak_eval` dropped** (0 solver iterations); timings return as context only with an uncertainty band; merged reports are not retro-edited | in force (three configurations since) | archived queue D17; `reports/deprecated/A26_method_fixes.md` |
| **D18** | 2026-09-02 | Phase B gains a predicate-matched control `A0′`; **`A0′ → A1′` is the headline**, `R → A1′` beside it; D14(c)'s "single-variable" claim withdrawn | discharged (A28); the three-arm shape persists as `BR / B0 / …` | archived queue D18; `reports/deprecated/A28_phase_b_rerun.md` |
| **D19** | 2026-09-03/04 | The prime (`fw.set_fw_geometry()` at the head of every sweep, `PROCESS_ARCH_PRIME`) is part of the V3 intervention — method-level, no model edit, stamped never pooled | in force (V3, V4) | archived queue D19; `plans/V3_DEVELOPMENT_PLAN.md` §2; `reports/deprecated/A40_v3_prime.md` |
| **D20** | 2026-09-10 | **V4 runs its own copy of PROCESS and owes V3 no backward compatibility** (*"Duplicate the code into MDA_partitioning_experiment_v4/PROCESS"*); the copy's `models/` byte-identical to `c0ae5b28`, gated (G0′) | in force | archived queue D20; `plans/V4_HARNESS_IMPLEMENTATION_PLAN.md` amendment 2; `reports/deprecated/A46_process_copy.md` |
| **D21** | 2026-09-10 | V4 methodology on the plan's §3.7: stencil entry regime; no fourth configuration; one seed set and format; `MDA_Output` out of the intervention arms; **empty-block skipping rejected** (disclaimed); renames and predicate mode accepted; (e) `B2` held for A43 | in force; (e) reversed by D22 | archived queue D21; `plans/V4_IMPROVEMENT_LIST.md` |
| **D22** | 2026-09-10 | `B2` removed from V4 (Phase B is `BR / B0 / B1 / B3`); `st_regression` conditional on A43 (answered: it stays); no errata to the V3 report; DR4 counters accepted | in force | archived queue D22; `reports/deprecated/A43_st_trust_gap.md` |
| **D23** | 2026-09-10 | One tolerance τ = 1e-6 for every MDA converger in every arm and phase; no "inner" tolerance; A43's exchange rate recorded should τ ever tighten | in force | archived queue D23 |
| **D24** | 2026-09-10 | A47's two rulings approved and the rebuild delegated (*"you're on your own now, take autonomous decisions to finish the implementation … Give me a report … when everything is done"*): H0–H8 and DR1/2/4/5/7 minted in advance, driver changes merged on G1/G0′ without per-change approval; the campaign still waits for `EXECUTION_APPROVED` | discharged (A48–A63; `reports/V4_IMPLEMENTATION_ASSESSMENT.md`); approval came 2026-09-14 (`57dc0c14`) | archived queue D24 |
| **D25** | 2026-09-11 | The exit audit restores the whole data structure (derived restored set; `numerics` held back by a named rule; instrument stamp `child.EXIT_AUDIT_RESTORE`). Minted and implemented before it was put to the user — a process fault, recorded; approved "for now" 2026-09-11; **confirmed 2026-09-14** (*"i think the current approach of measuring before the audit pass makes sense. I don't want to rewrite PROCESS at this point to fix the issue."*). No accuracy comparison against `BR` is wanted | in force; discharged at A62 (`a3407d5d`) | archived queue D25; `reports/deprecated/A62_exit_audit_restore.md`; I-21 |
| **D26** | 2026-09-14 | The reference arm `AR` is entered from the same displaced snapshot as every other Phase A arm (*"we compare just the stopping rule, so thats fine"*); `PAIRED_ARMS` gains `AR` | discharged (A64, `dc437a82`) | archived queue D26; `reports/deprecated/A64_entry_pairing_reference.md` |
| **D27** | 2026-09-14 | Simplification survey tiers A and B approved with the `ystate.py` move and one gate rerun at the end (*"A and B changes are approved. Implement it, with the delayed file move of ystate.py. Rerun the gates once after the full changes"*). **Tier C (C1–C3) deferred by the user** (*"I'd like to defer tier c items."*) — not ruled, kept in A68's report §4 for a later ruling; C4 done by A67 | discharged for A/B (A70–A73, `03f72479`, amendment 25); **tier C open, awaiting the user** | archived queue D27; `reports/deprecated/A68_harness_simplification_survey.md` §4; `plans/V4_HARNESS_IMPLEMENTATION_PLAN.md` Appendix A.1 rows (v), (vi), (xii) |

---

## 3. Issue register

Traps — recurring ways to be misled rather than defects — live in [`TRAPS.md`](TRAPS.md) (T1–T14)
and bind every task. Full text of every issue: the archived queue's "Issue register" table.

### 3.1 Open

| # | Issue | State and what would close it |
|---|---|---|
| **I-2** | `times.t_burn_0` is dead code (`physics.py:513`, no reader in `process/`) — evidence that burn time was historically the reconciliation variable | **OPEN.** Confirm no MFILE-path reader, then propose removal upstream. Archived queue I-2 |
| **I-8** | Wall clock is not measurable at the thresholds the plans use (19.6 % within-arm spread at `n = 5`) | **OPEN, moot for acceptance**: acceptance is counts and bit-comparisons (`CLAUDE.md`); timings are context with an interval. Archived queue I-8; trap T5 |
| **I-10** | Identical work varies up to 35 % in CPU-seconds; not scheduling contention (CPU tracks wall, ≈ 1 core busy), not memory pressure (peak RSS 423 MB); left: frequency scaling, cache/bandwidth, the WSL2 layer | **OPEN — a mechanism eliminated, not identified.** Deferred by the user as irrelevant to a count-based experiment; a quiet re-baseline or `perf stat` on the shared host needs the user's word. Archived queue I-10 carries the full cross-project history |
| **I-12** | PROCESS's 1990 cost model diverges at negative net electric power (`costs.py:2751`: `max(kwhpy, 1e-10)` on a negative `kwhpy` → ×10¹⁹), inflating outer-pass counts on infeasible starts (7/144 on `st_regression`); the 10¹⁸× tightening there is our median-scaled predicate's, not upstream's | **OPEN, recurs by design in perturbed multi-starts.** Degenerate starts are counted and reported; per-run deferral of `costs` removes the mechanism from the loop. Sent to the sibling in A27's handoff. Archived queue I-12 |
| **I-13** | Phase A's `hoisted_nodes()` and the production hoist disagreed on `large_tokamak_eval` (no figure-of-merit guard) | **Marked OPEN in the archive; effectively moot** — A26 fix 4 derived both from the driver's read set and D17 dropped the deck. Closing it formally is the orchestrator's call; carried as the archive states it. Archived queue I-13; `reports/deprecated/A26_method_fixes.md` (the "Different model sets on one deck" table row) |
| **I-17** | In V2 the Phase A → Phase B transfer over-predicted B3's saving on all decks and the declared failure condition did not select the failing decks | **OPEN — ON THE USER'S LIST** (*he wants to dive into it himself*). Mechanism measured by A44 (transfer-gap): the gap factorises exactly into a uniform entry-regime term and an evaluation-count term; at the stencil regime (adopted, D21 a) the transfer closes to ≤ 5 %. Formally open pending the user. Archived queue I-17; `reports/deprecated/A44_transfer_gap.md`; `data/a44_transfer_gap_summary.json` |
| **I-20** | (a) On `st_regression` the `PULSE` block is swept empty (10.84 % of `B3` block sweeps at seed 0, 11.12 % campaign-wide in V3; all three configurations visit it, only st pays a sweep); (b) `low_aspect_ratio_DEMO`'s objective (`i_figure_merit = -14`) is literally the lifted variable, so after the lift the problem lives in constraint 93 | **OPEN.** (a) the user ruled the visits stay and are disclaimed (D21 d) — quote the *sweep* share on the table's own population, never the 40 % visit share; a driver-side skip would be a later task needing approval. (b) needs no fix: a reporting obligation (rung labels not comparable across configurations). Archived queue I-20; `reports/deprecated/A58_driver_predicate_counters.md` |

**Downgraded, not open:** **I-7** — "no free iteration-variable number" was overstated: the cap is derived (`max(keys)`), so appending 178 grows every array; the real risks (reusing one of the 94 gaps; two branches allocating independently) are handled by D10 and the allocation table.

### 3.2 Closed

| # | What it was | Closed by | Pointer |
|---|---|---|---|
| **I-1** | The editable install pointed at `dev_libraries/PROCESS` at `710a75c9` | 2026-08-31, `PROCESS_surgery_env` created by the user; A1 bit-identical under it | archived queue I-1; `CLAUDE.md` Environments |
| **I-3** | Superseded documents carried no staleness marking | 2026-08-31, `> **Document status**` headers everywhere (trap T3) | archived queue I-3 |
| **I-4** | The `b_plasma_vertical_required` finding, withdrawn while the plan was revised | 2026-08-31, withdrawn before a register row was written; the number was consumed | archived queue change log 2026-08-31 (first entry) |
| **I-5** | `st_regression.IN.DAT` stale, did not solve at `c0ae5b28` | 2026-08-31 by D9's patch (A1) | archived queue I-5 |
| **I-6** | Two actors in one working tree put commits on the wrong branch | Protocol §3/§9 amended to isolated worktrees | archived queue I-6 |
| **I-9** | The scenario deck was never under version control (root `*.DAT` ignore) | 2026-08-31, A1: scoped `!scenarios/*.IN.DAT`, deck committed | archived queue I-9 |
| **I-11** | Task worktrees were seeded from upstream `main` (7 of 7) with no rules loaded | STRUCTURALLY RESOLVED 2026-09-01: `bin/new_task_worktree.sh`, dispatch without harness isolation (§3, §13); residual risk stated | archived queue I-11 |
| **I-14** | `git worktree remove --force` destroyed A26's run artifacts (`matched_accuracy.json`) | 2026-09-02 for recurrence: `bin/retire_task_worktree.sh`; loss bounded, regenerated by A28 | archived queue I-14 |
| **I-15** | The retire script's skip-and-continue destroyed A29's artifacts | 2026-09-03: collisions namespaced, never skipped | archived queue I-15 |
| **I-16** | The retire script's location whitelist missed A41's records (third recurrence) | 2026-09-04: `find` every `runs*/` under `arch_surgery/`, refuse removal while anything populated remains; artifacts regenerated | archived queue I-16 |
| **I-18** | An adjudication reached the tally and not the independent recomputation; `--verify` failed 26/144 cells | 2026-09-04/07, `7108cf33`: restated from the plan text; 0/144 | archived queue I-18 |
| **I-19** | A pre-declared within-cluster construction reached neither implementation | 2026-09-04/07, `fc96e75e`, in `v3_report_analysis.py`; the tally-side half was owed in V3 and is moot in V4 (`stats.py` is the declared construction, `analysis.py` the second implementation) | archived queue I-19; `plans/V4_IMPROVEMENT_LIST.md` item 6 |
| **I-21** | What else PROCESS's output pass leaves inconsistent in the written file | 2026-09-14, A67 (written-file-gap), gate `written_file_gap` (`f8d67eb4`): the one-call path writes the same 0.7 % `tfcoil.insstrain` gap, nothing else moves, no acceptance quantity affected; the PROCESS-side fix is upstream's (bug report committed in the sibling by the user) | archived queue I-21; `reports/deprecated/A67_written_file_gap.md`; D25 |
| **I-22** | Two stage records carried no provenance (`gate_table` verdicts read; census records unstamped) | 2026-09-11, A63 (stage-provenance), `52264b53`; remainder: the three optimisation-entry census records stay `census-1` until a press asks for that entry | archived queue I-22; `reports/deprecated/A63_stage_provenance.md`; trap T14 |
| **I-23** | `--resume`'s job identity was six fields, not the job | 2026-09-14 by construction, A72 (`73be52e5`, amendment 24, rule xiv): a job digest over every composed field | archived queue I-23; `reports/deprecated/A72_resume_identity_and_shared_pool.md` |

---

## 4. The queue

Rows are filed by state. A task appears in exactly one table. Prerequisite marks: ✓ merged.

### 4.1 Open — dispatched, queued, proposed, deferred

| # | Task | Prereqs | State |
|---|---|---|---|
| **A74** | **queue-v2** — this file and the archiving of `plans/MASTER_TODO.md` (user, 2026-09-14: *"clean up the master to_do list. Clean it up so it is a good historical reference then deprecate it, and make a v2 version that is the active one to be used. Keep all decisions, issues, scheduled tasks and all other standing items. keep only what remains relevant and compact it, refer back to original to do or to individual reports where possible. put the new version in /docs"*). `CLAUDE.md`'s two pointers follow; the orchestrator's memory pointer is the orchestrator's. Report `reports/A74_queue_v2.md` | A73 ✓ | **DISPATCHED** 2026-09-14 |
| **A6** | **characterise** — original plan Stage 5: scenario sweep, pulsed and steady-state reported separately, wall clock decomposed into model evaluation, VMCON overhead and I/O | A5 ✓ (superseded by A25) | **QUEUED** (parked; written against the V1 plan — re-scope before dispatch) |
| **A8** | **plan-relocation** — move `MDA_PARTITION_EXPERIMENT.md` into `docs/plans/` per the plans convention and fold the corrected speedup mechanism into its §3.2 | A1 ✓ | **QUEUED** (parked; the file already sits in `docs/plans/` — check what remains before dispatch) |
| **A9** | **subdriver-count** — Stage L0 of [`plans/SUBDRIVER_LIFT_EXPERIMENT.md`](plans/SUBDRIVER_LIFT_EXPERIMENT.md): confirm each nested root-find is on a `run()` path by invocation counting (trap T1); non-convergence recorded; read-only | A1 ✓ | **PROPOSED**, unblocked by D11 |
| **A10** | **subdriver-extract** — Stage L1: each residual behind an env switch, inner solve the default; gate: switch unset ⇒ bit-identical | A9 | **PROPOSED**, unblocked by D11 |
| **A11** | **subdriver-lift-one** — Stage L2: lift the loosest-tolerance, highest-count residual; primary result Jacobian accuracy, runtime secondary | A10 | **PROPOSED**, unblocked by D11 |
| **A12** | **subdriver-failure-policy** — Stage L4: is `disp=False` at `pfcoil.py:4909` deliberate, given `superconducting.py:1267` uses `disp=True`? A PROCESS finding | — | **PROPOSED**, runnable without a D5 ruling |
| **A14** | **converge-y** — candidate E2 of [`plans/ARCHITECTURE_EXPERIMENT_CANDIDATES.md`](plans/ARCHITECTURE_EXPERIMENT_CANDIDATES.md) | — | **DEFERRED** (E1–E5 not authorised, user 2026-08-31) |
| **A15** | **dsm-sequencing** — E3; A3 no longer folds into it while deferred | — | **DEFERRED** |
| **A16** | **convergence-predicate-audit** — E4, read-only | — | **DEFERRED** |
| **A17** | **fixed-count-scan** — E5, read-only | — | **DEFERRED** |
| — | **experiment-v2** — the from-scratch revision listed in [`plans/MDA_PARTITION_V2_REVISION_LIST.md`](plans/MDA_PARTITION_V2_REVISION_LIST.md) | — | Archived row reads **PLANNED, not authorised** (2026-09-03). *Stale as written:* the V2 experiment was built and run (A33–A38, `../MDA_partitioning_experiment_v2/`) and superseded by V3 and V4. Carried for the orchestrator to retire |
| — | **sequencing-comparison** — retired to `plans/deprecated/SEQUENCING_COMPARISON_EXPERIMENT.md`; if revived, its home is `functional_PROCESS` | — | **OUT OF SCOPE** |

**Scheduled but not yet minted** (the user adds tasks, §8): the V4 campaign's tally, analysis and
experiment report once the 949-run press completes (the button's `--campaign` chain reaches them;
an `A`-row when the user asks); survey tier C's ruling (D27); a driver-side empty-block skip if the
user ever wants I-20(a) repaired (needs approval as a driver change).

### 4.2 Merged — the ledger

One row per task. *Report* paths are under `reports/deprecated/`; *records* are untracked and live
under `../idf_probe/runs/` where the archived row names a path (relocated by the retire script; the
path is the branch's name, not the report's `runs/<task>/`). Merge commits marked † are taken from
`git log --first-parent` because the archived row names none. Findings in full: the archived queue's
status cell for that row, then the report.

| # | Keyword | Merged | Commit | Report / records | Delivered |
|---|---|---|---|---|---|
| **A1** | stage0-rebaseline | 2026-08-31 | `e9747707` | `A1_stage0_rebaseline.md` | Env-switched probe at `c0ae5b28`; three gates PASS 4/4 under `PROCESS_surgery_env`; I-1, I-5, I-9 closed |
| **A2** | module-convergence | 2026-08-31 | `0c0466c5` | `A2_module_convergence.md` | Stage-1 gate STOPS the partition: no module is the laggard; partition's own share 3.8–7.2 %; H2/H3 survive, H4 refuted |
| **A3** | build-reorder | 2026-09-01 | `0171ac95`† | `A3_build_reorder.md`; `runs/a3/` | `PROCESS_ARCH_SEQUENCE`: `build` after `PlasmaConfinementTime`, bit-identical 4/4; origin of protocol §12 (teeth, denominators) |
| **A4** | burn-time-lift | — | — | — | **SUPERSEDED — delivered by A25** under D16; kept for A19's non-separability finding |
| **A5** | module-solvers | — | — | — | **SUPERSEDED — delivered by A25** in the same bundle |
| **A7** | repo-readme | 2026-08-31 | — (orchestrator, no branch) | `../README.md` | Study entry-point README, fork notice, staleness headers (I-3) |
| **A13** | feedforward-hoist | 2026-09-01 | `85e64ac4`† | `A13_feedforward_hoist.md`; `runs/a13/` | `PROCESS_ARCH_HOIST`: 6.56/6.76/6.64/2.63 % of model evaluations, sweeps unchanged; the hoistable set depends on the figure of merit (I-13) |
| **A18** | experiment-framework | 2026-09-01 | `9caf8a38`, fix `15d68a1c` | `A18_experiment_framework.md`; `runs/a18/` (the harvest) | Phase A engine, arms, harvest mode, τ ladder; 600 design points; the two-sweep-floor claim refuted; origin of §5 (assessment gates the merge) |
| **A19** | frozen-input-convergence | 2026-08-31 | `026b2e3a` | `A19_frozen_input_convergence.md` | The middle band: partition's contribution 11.3–19.5 % gross, 6.6–14.5 % netted for the lift; the laggard becomes M2; the lift is not separable |
| **A20** | registry-append | 2026-09-01 | `93f2d372` | `A20_registry_append.md`; `runs/a20/` | Appending 178/93 is inert; code withdrawn by the user's ruling; `set_active_constraints` loop-bound defect found |
| **A21** | partition-report | 2026-09-01 | `83e18d15`† | no archived report file — the deliverables are `reports/MDA_partition_exp_results.md` and `../../MDA_partition_experiment.py`; `data/a21_published.json` | `MDA_partition_experiment.py` + the standing results document (Phase A); three corrections to A18's report |
| **A22** | outer-pass-census | 2026-09-01 | `b3135228`† | `A22_outer_pass_census.md`; `runs/a22/` | `k = 1` holds per deck: the only cross-module movement is the burn time (149/149, 297/297, 10/10); I-12 found |
| **A23** | flat-arm-permutation | 2026-09-01 | `4739b152`† | `A23_flat_arm_permutation.md`; `runs/a23*/` | `A0 → A1` is the module grouping alone: 600/600 and 2 400/2 400 bit-identical; DSM register V9a |
| **A24** | phase-b-scaffold | 2026-09-01 | `83e18d15`† | `A24_phase_b_scaffold.md` | Variable 178, constraint 93 with `lablcc`, `pulse.py` residual extraction (D14), gate harness; 0/121 295 differ; the burn-time site is closed-form, not a root-find |
| **A25** | phase-b-variant | 2026-09-01 | `122bf149`† | `A25_phase_b_variant.md` | Lift + module solvers; equivalence gate 4/4; H5: the proposed architecture does not win (robustness deficit genuine); `icc` position defect caught |
| **A26** | method-fixes | 2026-09-02 | `9d83d1d3`† | `A26_method_fixes.md`; `runs/a26/` (regenerated by A28 after I-14) | Matched achieved accuracy overturns Phase A's headline: −4.3/−4.5/−13.1 % instead of +46.8/+40.4/−4.6 %; `large_tokamak_eval` dropped (D17) |
| **A27** | process-defect-handoff | 2026-09-02 | `9fdb2f0c`† | no archived report file — the deliverable is `reports/outgoing/2026-09-02_process_defects_from_the_architecture_experiment.md` | Five PROCESS defects routed to the sibling; I-12's attribution corrected (ours, not upstream's) |
| **A28** | phase-b-rerun | 2026-09-02 | `0c18dfcc` | `A28_phase_b_rerun.md`; `runs/a28/` | Three arms (D18): `A0′ → A1′` −1.63 % nof, −6.18 % st, inconclusive lad; two thirds of the refusal deficit is the predicate; `MDA_partition_opt_experiment.py` |
| **A29** | replication-verify | 2026-09-03 | `4dade3b0` | `A29_replication_verify.md` | Both entry points reproduce the published numbers from clean, 30/30; two from-clean defects fixed; 375 records at one clean commit; I-15 (artifacts lost at retirement) |
| **A30** | phase-b-critique | 2026-09-02 | `7ef7d2a1`, corrections `e63bab8a` | `A30_phase_b_critique.md` | A28's arithmetic holds; five real findings (crash-only column, no arm varies the lift alone, dirty-tree provenance, …), corrections applied |
| **A31** | drift-diagnostic | 2026-09-03 | `3a75b264` | `A31_drift_diagnostic.md` | st's 3+-pass tail is `pf_power.srcktpm` flickering 1–2 ULPs under an exact-equality predicate — our instrument's misclassification, no upstream or DSM defect (V14 resolved) |
| **A32** | tail-confirm | 2026-09-03 | `637a6bb6` | `A32_tail_confirm.md` | Under the a26-mode spec the tail vanishes: 2 802/54 480 → 25/49 920; mode-aware `load_spec` |
| **A33** | postsolve-hoist | 2026-09-03 | `4cf488f6` | `A33_postsolve_hoist.md` | `PROCESS_ARCH_POST_SOLVE`: `vacuum`, `costs`, `water_use` (and `pulse` on st) leave the per-call path; 8.34/8.35/11.33 % of solve-phase node calls; 12/12 fields bit-identical |
| **A34** | phase-a-instruments | 2026-09-03 | `38aefad1`† | `A34_phase_a_instruments.md` | Trust mode, burn-time pin, single-MDA-eval mode; cold-entry `pin_gate` FAIL-as-bound → warm-entry design |
| **A35** | cold-census | 2026-09-04 | `b20b6112` | `A35_cold_census.md` | The cold-entry carrier named KNOWN-CUT: `FirstWall` writes `build.dr_fw_*` that `Build` read earlier — a depth-1 transport delay; DSM register V15 |
| **A36** | phase-a-campaign | 2026-09-03 | `3dd2bb96` | `A36_phase_a_campaign.md` | Phase A warm-entry campaign and tally; warm equivalence gate PASS (3.3e-9); perturbation reach 751/805 |
| **A37** | process-line-vs-runtime-order | — | — | — | **CANCELLED HERE / TRANSFERRED** 2026-09-04 to `PROCESS_code_analysis` as their M120 (user decision); M120 reported, nothing routed back |
| **A38** | audit-rerun | 2026-09-04 | `e9e7e965` | `A38_audit_rerun.md` | Corrected (restricted) Phase A similarity still FAILS on the carrier alone; identity vs V2 150/150; lad's open term `tfcoil.m_tf_coil_superconductor` |
| **A39** | v3-plan | 2026-09-04 | `3eb3be30`† | `A39_v3_plan.md`; `../MDA_partitioning_experiment_v3/EXPERIMENT_PLAN.md` | V3 experiment plan (NOT YET APPROVED header); defect-note draft `reports/outgoing/2026-09-04_first_wall_thickness_read_before_write.md`; DSM two-qualifier liveness convention |
| **A40** | v3-prime | 2026-09-04 | `9a6a9a61` | `A40_v3_prime.md` | `PROCESS_ARCH_PRIME` (D19); G1/G2/G3/G3c PASS with teeth; **A38's open lad term closes** (pair-driven, nonlinear) |
| **A41** | v3-harness | 2026-09-04 | `e4096e84` | `A41_v3_harness.md` | V3 harness (verbatim V2 copy first), H3 exit forensics, tallies T-a…T-e, `--verify`; three defects reported not repaired; check-1 adjudication (`10a2ff36`, → I-18) |
| **A42** | v3-campaign | 2026-09-07 (DONE) | campaign at `362c0b47` (approval `a164c6cd`); analysis `fe36dae8` | `../MDA_partitioning_experiment_v3/V3_EXPERIMENT_REPORT.md` | Executed by the user, analysed by the orchestrator: the prime closes the carrier (A1 passes F = 10 on all three); B3/B0 node calls 0.639/0.450/0.533; lad's `B2→B3` prediction refuted; I-18, I-19 found |
| **A43** | st-trust-gap | 2026-09-10 | `4a2eaf19` | `A43_st_trust_gap.md`; `runs/A43_runs/a43/` | The outer verification loop never fired (0 third passes in 91 888 calls); `B2`/`B3` differ by inner-solve slack below τ; st stays (D22); DSM register V16; I-20(a) share corrected |
| **A44** | transfer-gap | 2026-09-10 | `7679c2c7` | `A44_transfer_gap.md`; `data/a44_transfer_gap_summary.json`; `runs/A44-transfer-gap_runs/a44/` | I-17's mechanism: the gap factorises into a uniform entry-regime term and an evaluation-count term; δ = 0.001 measured negative; the stencil regime adopted (D21 a) |
| **A45** | v4-harness-plan | 2026-09-10 | `546ccd47` | `A45_v4_harness_plan.md`; the plan stays live at `plans/V4_HARNESS_IMPLEMENTATION_PLAN.md` | The V4 harness implementation plan, three amendment rounds on the user's rulings (D20–D23), task decomposition H0–H8 / DR1–DR7 |
| **A46** | process-copy | 2026-09-10 | `38057e27` | `A46_process_copy.md`; `runs/A46_runs/gates/` | V4's own `PROCESS/` copy at `f2dc9243`, tree-hash identical, three path constants; G0′ (`models/` vs `c0ae5b28`, `pulse.py` the one D14(b) difference) |
| **A47** | harness-skeleton | 2026-09-10 | `42a1edd1` | `A47_harness_skeleton.md` | `config`, `switches`, `arms` (the §3.2 matrix as data), `provenance`, runner preflight, README; 15 teeth; D24's two rulings |
| **A48** | harness-data | 2026-09-10 | `d9fe737f` | `A48_harness_data.md` | H0 complete: `harness/data/` 16 files sha-identical to source, `ystate.py` moved whole, first 5/5 self-check against the copy |
| **A49** | harness-reference | 2026-09-10 | `92990fe7` | `A49_harness_reference.md`; `runs/A49_runs/` | `reproduction_reference.json`: 20 V3 records, 270 values, re-derived byte for byte; 4 teeth |
| **A50** | harness-run | 2026-09-10 | `6be26e85` | `A50_harness_run.md`; `runs/A50_runs/` | The run path (`child`, `optimise`, `evaluate`, `pool`, `records`); **gate GR PASS 270/270** before any driver change; seven teeth |
| **A51** | harness-artifacts | 2026-09-10 | `ed343e46` | `A51_harness_artifacts.md`; `runs/A51_runs/` | Artifact stages: lifted inputs byte-identical, census 0 differences, per-run sets reproduced 5/5; 11 teeth |
| **A52** | harness-gates | 2026-09-11 | `d13a54c7` | `A52_harness_gates.md`; `runs/A52_runs/gates/` | Every gate inside `harness/` on one button: 21 PASS, 109/109 teeth from scratch; six review defects fixed (incl. `--resume` not reaching runs); amendment 13 rules |
| **A53** | harness-tally | 2026-09-11 | `d98f602a` | `A53_harness_tally.md`; `runs/A53_runs/gates/` | `stats.py`, `tables.py`, the tally stages; `tally_contracts` 270/270 cells; record-field rename via `FIELD_NAME_MAP`; rule (vi) |
| **A54** | harness-analysis | 2026-09-11 | `72c343d1` | `A54_harness_analysis.md`; `runs/A54_runs/gates/` | `analysis.py`, the independent second implementation: `recomputation` 1 901/0, 9/9 teeth; stale-stage refusal; trap T12 |
| **A55** | harness-smoke | 2026-09-11 | `bfaee7ce` | `A55_harness_smoke.md`; `runs/A55_runs/` | `chain.py` (smoke and campaign as one chain); 24/24 gates, 139/139 teeth at one press; `plan_tables.py`; D26 proposed, I-22 filed; trap T13 |
| **A56** | driver-renames | 2026-09-10 | `16d7eb55` | `A56_driver_renames.md`; `runs/A56_runs/` | DR1: §11.2 switch names in the copy, `OUTER` removed, `BURN_TIME_OWNER`, typed `ArchitectureRefusal`; G0′/G1/GR PASS |
| **A57** | driver-output-path | 2026-09-10 | `6c7c742e` | `A57_driver_output_path.md`; `runs/A57_runs/` | DR2: `PROCESS_ARCH_OUTPUT_LOOP = upstream \| none`, the audit snapshot at the declared position; G9; `B1`/`B3` runnable; `insstrain` finding (item 11) |
| **A58** | driver-predicate-counters | 2026-09-10 | `e73113a9` | `A58_driver_predicate_counters.md`; `runs/A58_runs/` | DR4: six per-sweep counters; item 3 closed in the negative; I-20(a) extended to all configurations |
| **A59** | driver-predicate-mode | 2026-09-11 | `71f105c2` | `A59_driver_predicate_mode.md`; `runs/A59_runs/` | DR5: `PROCESS_ARCH_PREDICATE = frozen \| mixed`; G8 12/12 bit-identical, 0 verdicts changed |
| **A60** | driver-attempts | 2026-09-11 | `73525d1e` | `A60_driver_attempts.md`; `runs/A60_runs/` | DR7: per-attempt node-call accounting (`attempts[]`, summation enforced); **the driver chain closed** |
| **A61** | insstrain-diagnosis | 2026-09-11 | `fd480aff` | `A61_insstrain_diagnosis.md`; `runs/A61_runs/gates/exit_audit_diagnosis/` | The 7e-3 `tfcoil.insstrain` residual is an exit-audit instrument artefact (output path raises the TF mesh 100 → 500); `B0`/`B3` converged to τ; → D25, I-21; bug report `reports/outgoing/2026-09-11_…` |
| **A62** | exit-audit-restore | 2026-09-11 | `a3407d5d` | `A62_exit_audit_restore.md`; `runs/A62_runs/gates/` | D25 discharged: whole-structure snapshot, derived restore, `numerics` held back; G1 straddle with the instrument-change exclusion kind; GR 270 → 256 |
| **A63** | stage-provenance | 2026-09-11 | `52264b53` | `A63_stage_provenance.md`; `runs/A63_runs/` | I-22 closed: `Measurement.reads_records`, stale refusal, `--plan-tables check`, census-2 stamps; trap T14 |
| **A64** | entry-pairing-reference | 2026-09-14 | `dc437a82` | `A64_entry_pairing_reference.md`; `runs/A64_runs/` | D26 enforced by G6 (`PAIRED_ARMS` incl. `AR`, 6 717/0); amendment 21 (rule xi) |
| **A65** | harness-folders | 2026-09-14 | `28df7409` | `A65_harness_folders.md`; `runs/A65_runs/` | 38 modules grouped into `core/ experiment/ child/ gates/ measurement/`; 0 runs re-made; amendment 22 (rule xii) |
| **A66** | ystate-into-child | 2026-09-14 via A73 | `03f72479` (`7d333677` on A73's branch) | `A73_run_path_edits_and_the_press.md` | `harness/child/ystate.py`; the copy's literal path and `copy_gates.py` changed together; copy gates PASS |
| **A67** | written-file-gap | 2026-09-14 | `f8d67eb4` | `A67_written_file_gap.md`; `runs/A67_runs/` | I-21 measured and closed: the one-call path writes the same gap; 42/42 checks, 4/4 teeth |
| **A68** | harness-simplification-survey | 2026-09-14 | `047d3b43` | `A68_harness_simplification_survey.md` | 24 items in tiers A (12), B (8), C (4, the user's); 46 973 lines measured; I-23 filed |
| **A69** | process-copy-changes-doc | 2026-09-14 | `7f2a0606` | no archived report file — the deliverable is `../MDA_partitioning_experiment_v4/PROCESS/CHANGES.md`; the finding is in the archived row | `PROCESS/CHANGES.md`, 27/27 hunks with snippets; finding: the copy's source is `f2dc9243`, the inherited driver layer is gated by history not by `copy_gates.py` |
| **A70** | simplify-code-moves | 2026-09-14 | `bc53f4d6` | `A70_simplify_code_moves.md`; `runs/A70_runs/` | Survey A1/A2/A9: `gates.py` split into six modules; two stages retired; 0 runs |
| **A71** | simplify-refactors-and-teeth | 2026-09-14 | `24e5fe2f` | `A71_simplify_refactors_and_teeth.md`; `runs/A71_runs/` | 13 items; teeth 158 → 148; lines 47 728 → 46 318; amendment 23 (rule xiii); item 12 discharged |
| **A72** | resume-identity-and-shared-pool | 2026-09-14 | `73be52e5` | `A72_resume_identity_and_shared_pool.md`; `runs/A72_runs/` | I-23 closed: 20-field job identity; shared pool `runs/gates/_runs/`; amendment 24 (rule xiv); item 14 filed |
| **A73** | run-path-edits-and-the-press | 2026-09-14 | `03f72479` | `A73_run_path_edits_and_the_press.md`; `runs/A73_runs/` (the D27 from-scratch population) | B3 and A66, then D27's one press: 30 PASS, 152/152 teeth, GR 256/256, G1 0/2 825; lines → 45 390; amendment 25; item 15 filed |

---

## 5. Standing items

### 5.1 User-facing standing items (not tasks)

| Item | State |
|---|---|
| Add `upstream` read-only for drift measurement | **DONE**, verified (`upstream https://github.com/ukaea/PROCESS.git`) |
| Push `architecture_surgery` | **DONE** at the time (0 ahead); every later push needs the user's per-push approval |
| Delete `github.com/wrutten/PROCESS_surgery` | Reported done by the user; **not verifiable from a session** (no GitHub access) |
| **One heavy slot at a time on our side** (user, 2026-09-01) | **In force** — see Protocol; written after A13 and A23 were dispatched concurrently |
| Run measurement work when the machine is otherwise idle (user, 2026-08-31) | **In force** — I-8/I-10 context |
| The V4 campaign is running (pressed 2026-09-14 at `57dc0c14`, 949 runs, 3 workers, detached worktree) | **Open** — completion, tally, analysis and report follow; no commit while it runs (rule v) |
| Survey tier C (C1 duplication caveat beside decision (6); C2 rule (iii)'s `-P` text vs the pool children; C3 rules (v)/(vi)/(xii) prose-only → pool-level refusal) | **Awaiting the user's ruling** (D27, deferred 2026-09-14); text in `reports/deprecated/A68_harness_simplification_survey.md` §4 |
| V4 improvement list (`plans/V4_IMPROVEMENT_LIST.md`, items 0–15) | **The list is the authority on each item's state.** Its headings mark 3 (closed in the negative, A58), 12 (A71) and 13 (A73) discharged; 5a is a pre-declared trial (G8 built by A59; adoption is decided on the campaign); 5b requires the user's review and approval; 11 was diagnosed by A61/A62 with the PROCESS-side fix upstream's; 14 and 15 were filed 2026-09-14 by A72/A73 |
| Outgoing PROCESS defect notes (`reports/outgoing/`, five files) | Filed with the sibling (2026-09-01 NaN; 2026-09-02 five defects; 2026-09-11 `insstrain`/`None` latch, committed there by the user); 2026-09-03 st query and 2026-09-04 first-wall note staged, handoff the orchestrator's under the demonstrated-defect rule |

### 5.2 Known open questions (parked, not blocking)

| # | Question | State |
|---|---|---|
| 1 | Which module is the laggard? | **Answered, then revised**: none under the coupled loop (A2); **M2** at 42 % of cost under the lift (A19) |
| 1b | Does H2 survive its cheapest test? | **Yes** — `st_regression` has zero live cross-module back edges (A2, A22) |
| 1c | Should A13 be revived? | **Yes** — D12 folded it in as Stage 1b |
| 1d | Is the 10–25 % band enough to revive A4/A5? | **Yes** — D12; the risks recorded there (netted 6.6–14.5 %, H5 unmeasured then, laggard M2) stand as risks, and were then measured (A25, A26, A28) |
| 2 | Post-lift, does `Pulse` join a module or remain feed-forward? | **Answered** — pure feed-forward (partition plan §2.3a) |
| 3 | Rows 52–55 (`Objective`, `Constraints`) are downstream of everything — can the objective be evaluated without re-running M3? | **Open** in the archive; the per-run deferral of `costs`/`vacuum`/`water_use` (A33) is the practical relative of this question |
| 4 | How many upstream commits separate `c0ae5b28` from `ukaea/main`, and must the write-up state that drift? | **Open** in the archive; measure at write-up (`upstream` is fetched for this purpose only, D2) |

---

## 6. Where things live

| What | Where |
|---|---|
| This queue (active) / the history | `docs/MASTER_TODO_v2.md` / [`plans/MASTER_TODO.md`](plans/MASTER_TODO.md) (archived) |
| Agent rules | [`../../CLAUDE.md`](../../CLAUDE.md); traps [`TRAPS.md`](TRAPS.md) (T1–T14, binding) |
| Experiment plans | V4 (running): [`../MDA_partitioning_experiment_v4/EXPERIMENT_PLAN.md`](../MDA_partitioning_experiment_v4/EXPERIMENT_PLAN.md); V3 and V2: the sibling folders' `EXPERIMENT_PLAN.md` and `V*_EXPERIMENT_REPORT.md`; V1: [`plans/MDA_PARTITION_EXPERIMENT.md`](plans/MDA_PARTITION_EXPERIMENT.md) with `reports/MDA_partition_exp_results.md`; parked lines: `plans/SUBDRIVER_LIFT_EXPERIMENT.md`, `plans/ARCHITECTURE_EXPERIMENT_CANDIDATES.md`; superseded: `plans/deprecated/` |
| Harness plan, rules, amendments | [`plans/V4_HARNESS_IMPLEMENTATION_PLAN.md`](plans/V4_HARNESS_IMPLEMENTATION_PLAN.md) — Appendix A (amendments 1–25), Appendix A.1 (the twelve rules and what enforces each), §11 (terminology) |
| Improvement list | [`plans/V4_IMPROVEMENT_LIST.md`](plans/V4_IMPROVEMENT_LIST.md), items 0–15 (predecessor: `plans/V3_IMPROVEMENT_LIST.md`) |
| Harness README and button | [`../MDA_partitioning_experiment_v4/harness/README.md`](../MDA_partitioning_experiment_v4/harness/README.md); `../MDA_partitioning_experiment_v4/experiment_runner.py`; the copy's change record `PROCESS/CHANGES.md`, `PROCESS_diff.py` |
| Standing registers | `reports/DSM_VALIDATION.md` (never archived); `plans/REGISTRY_ALLOCATIONS.md`; `reports/V4_IMPLEMENTATION_ASSESSMENT.md`; `reports/PROCESS_architecture_evaluation.md` (stale measurements, structural findings survive) |
| Reports | open tasks: `reports/`; merged: `reports/deprecated/` (read each `> **Document status**` header, T3); to the sibling: `reports/outgoing/`; data: `data/` |
| Run records (untracked) | `../idf_probe/runs/A<n>_runs/…` per the ledger; the V4 pool `../MDA_partitioning_experiment_v4/runs/` in the tree that pressed it; A18's harvest `../idf_probe/runs/a18/` |
| Worktrees and their tools | `/home/wrutten/projects/PROCESS_surgery_worktrees/<branch>`; `../bin/new_task_worktree.sh`, `../bin/retire_task_worktree.sh` |
| Environments | `PROCESS_surgery_env` only (`CLAUDE.md` Environments); the dependency instrument in the sibling `PROCESS_code_analysis/src/PROCESS_DSM`, pin `ANALYSIS_PIN_NAME` |
| The orchestrator's memory rules (subjects only; the content is the orchestrator's) | the environment; the experiment's purpose; demonstrated defects before cross-study handoffs; verify simplifications against measurements; additive edits against a committed baseline; the V3 report's deck → config rename; investigative-agent registration; agents named by task and keyword; derive a decision's implications; no task numbers or versions in names; retire the worktree before writing record paths; "from scratch" means the run stamps say so; verify differently, not by repeating the press; rulings are the user's; reuse gate records |

---

## 7. Change log

| Date | Entry |
|---|---|
| 2026-09-14 | **Created by A74 (queue-v2) from the archived queue at `c5fc49d3`**, at the user's instruction: *"clean up the master to_do list. Clean it up so it is a good historical reference then deprecate it, and make a v2 version that is the active one to be used. Keep all decisions, issues, scheduled tasks and all other standing items. keep only what remains relevant and compact it, refer back to original to do or to individual reports where possible. put the new version in /docs"*. `plans/MASTER_TODO.md` archived with a status header (one cell changed, recorded there). Carried: D1–D27, I-1–I-23 (7 open, 1 downgraded, 15 closed), A1–A74 (11 open or parked, 63 in the ledger). Numbering continues at A75, D28, I-24. |
