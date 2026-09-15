# Master TO-DO v2 — architecture surgery on PROCESS

> **Document status** — **ACTIVE from 2026-09-14.** The standing execution queue for this
> repository. It supersedes [`plans/MASTER_TODO.md`](plans/MASTER_TODO.md), which is **archived as
> the history** (its `> **Document status**` header says so) and is never edited again. The two
> relate as ledger and journal: every decision, issue and task minted before 2026-09-14 is *recorded*
> there in full and *summarised* here with its current state and a pointer; everything minted from
> 2026-09-14 onward lives here only. **A number is never reused and the numbering continues** —
> next free: **A84**, **D31**, **I-27** *(at creation: A75, D28, I-24)* (confirmed against the archived file's numbering
> line at `c5fc49d3`; those three numbers occur nowhere else in it). Check the line when you add a row.
> "The archived queue" below means `plans/MASTER_TODO.md`; "§n" points at its protocol numbering.

| | |
|---|---|
| **Owner** | W.J. Rutten (paces execution); the orchestrating agent dispatches |
| **Objective** | Determine whether **the arrangement of solvers and optimisers alone** — every physics and engineering model frozen at `c0ae5b28` — measurably changes the cost of solving PROCESS, by partitioning the global idempotence loop into per-module solvers |
| **Base commit** | `c0ae5b28`, frozen (D2) |
| **State** | V4 executed and reported (2026-09-14): the campaign's 949 records at `57dc0c14`, §4–§6 of the plan written from them; every decision D1–D28 recorded here, six issues open; A78 (arm-renames) merged 2026-09-15 — arms now `AR/A0/A1/A2`, `BR/B0/B1/B2`; A79 (report-captions) merged 2026-09-15 — §4 conclusions, Appendix D, companion file; A82 (per-arm-success) merged 2026-09-15; A83 (headline-tables-in-text, with the formatting reassessment) next. *At creation (2026-09-14):* harness complete at `03f72479`, approval `57dc0c14`, campaign running. |
| **Experiment plan** | [`../MDA_partitioning_experiment_v4/EXPERIMENT_REPORT.md`](../MDA_partitioning_experiment_v4/EXPERIMENT_REPORT.md) (V4, executed and reported 2026-09-14); [`plans/MDA_PARTITION_EXPERIMENT.md`](plans/MDA_PARTITION_EXPERIMENT.md) (the original two-phase plan, V1/V2 era) |

---

## 1. Protocol

The rules that bind every task. One line each; the archived queue's protocol section carries the
rationale and the incident that produced each rule. [`../../CLAUDE.md`](../../CLAUDE.md) states the
hard rules (sandbox never overridden; base commit and models frozen; never write in a sibling clone;
never commit to `main`; never push without per-push approval) and is not repeated here. **§1 is how a task runs; §5.1 is what stands ruled about the project** — the base commit, the frozen models, the copy, the registry, who rules, the run budget.

| § | Rule (verbatim where quoted elsewhere as binding) |
|---|---|
| §1 | The orchestrator dispatches; task agents plan and execute. The orchestrator does not execute tasks itself. |
| §2 | Every task is `A<n>` **with a keyword minted at the same time**; prose always writes `A1 (stage0-rebaseline)`, never a bare number. The keyword is the branch slug and is never renamed. |
| §3 | Every task runs on branch `A<n>-<keyword>` in an isolated worktree **created by the orchestrator with [`../bin/new_task_worktree.sh`](../bin/new_task_worktree.sh), never by the agent harness** (I-11); worktrees live in `/home/wrutten/projects/PROCESS_surgery_worktrees/`, which is ours. The agent writes a report to `reports/` — verdict first, autonomous decisions with reversal paths, append-only change log. Commits: `A<n> <keyword>: …`. **A task's results live in its report** — the whole of them: findings, evaluations, tables, the analysis itself — and the orchestrator's assessment is appended to that one document. A task creates a separate file only for a *living artifact that outlives it* — code, a plan, a register or list, a generated rendering — and the report says what it delivered there. **A brief that asks for the results in a separate document is the orchestrator's fault, not the agent's** (A81 (benchmarking-practices), 2026-09-15: the evaluation was briefed as `docs/V4_METHOD_AGAINST_BENCHMARKING_PRACTICE.md` plus a short report, folded back into the report at the user's ruling — *"A81 should contain all of the results from the agent … on which you append your assessment"*). The orchestrator checks the brief against this rule before dispatch: one deliverable named, the report. |
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
| — | Gate records are reused: worktrees are seeded with the latest relocated records and tasks press `--gate all --resume`; a from-scratch press only when the change alters what a gate reads; the orchestrator verifies by differing checks, never by repeating the agent's press (harness plan amendment 15; the user, 2026-09-11). No commit and no edit to `harness/child/` while measurement runs execute (amendments 13, 16, 22). |
| — | Work-item terms: **Task** `A<n>` (one branch, one report, one merge decision); **Subtask** `A<n>.<k>` (the agent's own, never its own branch); **Issue** `I-<n>` (defect in this repository or its environment, filed not fixed in passing); **PROCESS finding** (critique of PROCESS itself: architecture here, implementation defects to `PROCESS_code_analysis/docs/bug_reports/`); **Decision** `D<n>` (a recorded user decision, append-only; a reversal is a new decision). |
| — | Optimiser-registry allocation is administered in [`plans/REGISTRY_ALLOCATIONS.md`](plans/REGISTRY_ALLOCATIONS.md), append-only (D10). Constraints append from 93 (`lablcc` extended in step); iteration variables from 178 (the cap is derived, I-7). |

---

## 2. Decisions register — methodology

*Arm names in rulings dated before 2026-09-15 are the names of their day (D22 among them): `A0p` is today's `A1`, `A1` today's `A2`, `B3` today's `B2`; a `B2` in those rulings is V3's removed joint-test arm. Renamed by A78 (arm-renames) at the user's ruling of 2026-09-15; D-rows are not rewritten.*

Every ruling on **what the experiment measures and how**, one row each. *Status:* **in force**, **discharged** (carried out; still binds as a record), **amended by** / **reversed by**. The user's words are verbatim where the archived queue quotes them. Full text: the archived queue's "Decisions (live set)" table, row by number. **The project-administration rulings — D1, D2, D3, D4, D5, D10, D11, D20, D24, D28 — are standing rules and live in §5.1, unified by subject with their numbers kept**; a number is never reused, so the gaps below are those rows.

| # | Date | Ruling (one line) | Status | Pointer |
|---|---|---|---|---|
| **D6** | 2026-08-31 | Correctness is gated on `norm_objf` plus a post-solve feasibility audit, never on iteration variables | in force | archived queue D6 |
| **D7** | 2026-08-31 | A full IDF / MDF / SAND comparison is deferred to a later study on the `functional_PROCESS` back-end; this experiment is its control | in force | archived queue D7 |
| **D8** | 2026-08-31 | The module partition is derived from the collapsed DSM (M1 Physics rows 4, 6–28; M2 Coils 5, 29–37; M3 Plant 40–51; `Pulse` the articulation point) | in force | archived queue D8; `reports/DSM_VALIDATION.md` |
| **D9** | 2026-08-31 | The archived scenario deck is patched in place (`st_regression.IN.DAT` + `i_tf_turn_type = 2` and four tape geometries), not re-pointed at upstream | discharged (A1) | archived queue D9; `reports/deprecated/A1_stage0_rebaseline.md` |
| **D12** | 2026-08-31 | The partition experiment proceeds despite A2's STOP gate under the plan's 10–25 % rule; the feed-forward hoist (A13) is folded in as Stage 1b and taken first; A4/A5 reinstated | discharged (A13, A25) | archived queue D12; `reports/deprecated/A13_feedforward_hoist.md` |
| **D13** | 2026-09-01 | The partition is measured in two phases: fixed-point first (flat vs block Gauss-Seidel on the coupling state, counts not wall clock, hard cut 20 ⇒ invalid), VMCON second | discharged (A18–A28); the two-phase shape carries into V2–V4 | archived queue D13; `plans/MDA_PARTITION_EXPERIMENT.md` |
| **D14** | 2026-09-01 | Phase B implementation: (a) `lablcc` extension approved; (b) D11 approval for the `pulse.py` residual extraction; (c) the baseline is PROCESS as shipped, with `check_agreement`'s defects reproduced deliberately; the variant's per-module predicate is entailed by the architecture, not a confound | (a),(b) discharged (A24); (c) amended by D18 | archived queue D14; `reports/deprecated/A24_phase_b_scaffold.md` |
| **D15** | 2026-09-01 | Phase B design: δ calibrated not chosen; the hoist is INSIDE the variant so the headline is "the proposed architecture", never "the partition's benefit"; a `norm_objf` mismatch is a robustness finding; a failed per-module solve is a failed start; `st_regression` is the `k = 0` control | discharged (A25, A28) | archived queue D15; `reports/deprecated/A25_phase_b_variant.md` |
| **D16** | 2026-09-01 | Phase B in two bundles (A24 = F2+F9+F6; A25 = A4+A5+gate+H5), autonomous go-ahead through H5 on a passing gate | discharged (both gates passed) | archived queue D16 |
| **D17** | 2026-09-01 | Methodology fixed before Phase B re-runs; **`large_tokamak_eval` dropped** (0 solver iterations); timings return as context only with an uncertainty band; merged reports are not retro-edited | in force (three configurations since) | archived queue D17; `reports/deprecated/A26_method_fixes.md` |
| **D18** | 2026-09-02 | Phase B gains a predicate-matched control `A0′`; **`A0′ → A1′` is the headline**, `R → A1′` beside it; D14(c)'s "single-variable" claim withdrawn | discharged (A28); the three-arm shape persists as `BR / B0 / …` | archived queue D18; `reports/deprecated/A28_phase_b_rerun.md` |
| **D19** | 2026-09-03/04 | The prime (`fw.set_fw_geometry()` at the head of every sweep, `PROCESS_ARCH_PRIME`) is part of the V3 intervention — method-level, no model edit, stamped never pooled | in force (V3, V4) | archived queue D19; `plans/V3_DEVELOPMENT_PLAN.md` §2; `reports/deprecated/A40_v3_prime.md` |
| **D21** | 2026-09-10 | V4 methodology on the plan's §3.7: stencil entry regime; no fourth configuration; one seed set and format; `MDA_Output` out of the intervention arms; **empty-block skipping rejected** (disclaimed); renames and predicate mode accepted; (e) `B2` held for A43 | in force; (e) reversed by D22 | archived queue D21; `plans/V4_IMPROVEMENT_LIST.md` |
| **D22** | 2026-09-10 | `B2` removed from V4 (Phase B is `BR / B0 / B1 / B3`); `st_regression` conditional on A43 (answered: it stays); no errata to the V3 report; DR4 counters accepted | in force | archived queue D22; `reports/deprecated/A43_st_trust_gap.md` |
| **D23** | 2026-09-10 | One tolerance τ = 1e-6 for every MDA converger in every arm and phase; no "inner" tolerance; A43's exchange rate recorded should τ ever tighten | in force | archived queue D23 |
| **D25** | 2026-09-11 | The exit audit restores the whole data structure (derived restored set; `numerics` held back by a named rule; instrument stamp `child.EXIT_AUDIT_RESTORE`). Minted and implemented before it was put to the user — a process fault, recorded; approved "for now" 2026-09-11; **confirmed 2026-09-14** (*"i think the current approach of measuring before the audit pass makes sense. I don't want to rewrite PROCESS at this point to fix the issue."*). No accuracy comparison against `BR` is wanted | in force; discharged at A62 (`a3407d5d`) | archived queue D25; `reports/deprecated/A62_exit_audit_restore.md`; I-21 |
| **D26** | 2026-09-14 | The reference arm `AR` is entered from the same displaced snapshot as every other Phase A arm (*"we compare just the stopping rule, so thats fine"*); `PAIRED_ARMS` gains `AR` | discharged (A64, `dc437a82`) | archived queue D26; `reports/deprecated/A64_entry_pairing_reference.md` |
| **D27** | 2026-09-14 | Simplification survey tiers A and B approved with the `ystate.py` move and one gate rerun at the end (*"A and B changes are approved. Implement it, with the delayed file move of ystate.py. Rerun the gates once after the full changes"*). **Tier C (C1–C3) deferred by the user** (*"I'd like to defer tier c items."*) — not ruled, kept in A68's report §4 for a later ruling; C4 done by A67 | discharged for A/B (A70–A73, `03f72479`, amendment 25); **tier C open, awaiting the user** | archived queue D27; `reports/deprecated/A68_harness_simplification_survey.md` §4; `plans/V4_HARNESS_IMPLEMENTATION_PLAN.md` Appendix A.1 rows (v), (vi), (xii) |
| **D29** | 2026-09-15 | **The V4 study is an existence proof, not a benchmark, and is reported as one.** On A81 (benchmarking-practices)'s findings the user ruled: (1) the reliability gap is closed on the V4 records — a per-arm success table with denominator 25 enters the report as a dated, descriptive addition (no verdict changes; A82 (per-arm-success)); data profiles and verdict sensitivity go to the V5 list (*"I follow your advice here"*). (2) **The non-node cost term and wall-clock time are out of scope** (*"the non-node cost term is not relevant, as is the wall-clock time. Because this is an existance proof, not a claim that we really improved process this much. I want to make a general argument that architecture matters, so the impact on node calls is enough, as it is reasonable to see the impact for applications dominated by node call runtime"*) — §3.5 check 5's promised wall-clock section is withdrawn as a promise, not added; the report states the scope. (3) **Three configurations is a case study, acknowledged in one clause** (*"yes, this is a case study, not a full benchmark indeed. So I don't think we need a big change to reporting"*) — §6 gains the clause and nothing more; no V5 item on configuration-set size |
| **D30** | 2026-09-15 | **V4 stands on the `frozen` ruler; the predicate trial's adoption rule was satisfied and not applied, and the departure is recorded, not repaired.** Report §3.6 pre-declared that gates 1–3 passing plus a neutral measurement *adopts* `mixed` (`max_i |Δy_i| / max(|y_i|, s_i)`) as V4's predicate and audit ruler; G8 passed with 12 of 12 pairs bit-identical and the campaign was pressed on `frozen` (`s_i` fixed from the pre-campaign harvest, V2/V3's ruler) without the rule being re-read. Found by A80 (report-accuracy-audit). The user (*"I am fine with recording the departure, please do"*): §5.6 and Appendix C state that V4's numbers are `frozen`-ruler numbers, that the rule was met and not applied, and why it changes nothing acceptance-bearing — the exit audit is printed on both rulers, the cost quantities are node calls of runs that were made under `frozen`, and `mixed` is never tighter than `frozen` so a retroactive change of ruler could not be applied to the runs, only to the reporting. Kept `frozen` also keeps V4 on V3's ruler (the 0.64 / 0.45 / 0.53 context numbers are comparable). **For V5:** apply the adoption rule before the campaign or drop it; a ruler is chosen before the numbers |

---

## 3. Issue register

Traps — recurring ways to be misled rather than defects — live in [`TRAPS.md`](TRAPS.md) (T1–T15) and bind every task. Issues I-1–I-23 are recorded in full in the archived queue's "Issue register"; their closures are there too, except the three ruled after the archive (index below). Issues from I-24 on belong to this file; a closed one keeps an index line (§5.1, rule Q2).

### 3.1 Open

| # | Issue | State and what would close it |
|---|---|---|
| **I-2** | `times.t_burn_0` is dead code (`physics.py:513`, no reader in `process/`) — evidence that burn time was historically the reconciliation variable | **OPEN.** Confirm no MFILE-path reader, then propose removal upstream. Archived queue I-2 |
| **I-8** | Wall clock is not measurable at the thresholds the plans use (19.6 % within-arm spread at `n = 5`) | **OPEN, moot for acceptance**: acceptance is counts and bit-comparisons (`CLAUDE.md`); timings are context with an interval. Archived queue I-8; trap T5 |
| **I-10** | Identical work varies up to 35 % in CPU-seconds; not scheduling contention (CPU tracks wall, ≈ 1 core busy), not memory pressure (peak RSS 423 MB); left: frequency scaling, cache/bandwidth, the WSL2 layer | **OPEN — a mechanism eliminated, not identified.** Deferred by the user as irrelevant to a count-based experiment; a quiet re-baseline or `perf stat` on the shared host needs the user's word. Archived queue I-10 carries the full cross-project history |
| **I-12** | PROCESS's 1990 cost model diverges at negative net electric power (`costs.py:2751`: `max(kwhpy, 1e-10)` on a negative `kwhpy` → ×10¹⁹), inflating outer-pass counts on infeasible starts (7/144 on `st_regression`); the 10¹⁸× tightening there is our median-scaled predicate's, not upstream's | **OPEN, recurs by design in perturbed multi-starts.** Degenerate starts are counted and reported; per-run deferral of `costs` removes the mechanism from the loop. Sent to the sibling in A27's handoff. Archived queue I-12 |
| **I-20** | (a) On `st_regression` the `PULSE` block is swept empty (10.84 % of the partitioned optimisation arm `B2`'s block sweeps at seed 0 — `B3` in the records and documents before A78 (arm-renames) —, 11.12 % campaign-wide in V3; all three configurations visit it, only st pays a sweep); (b) `low_aspect_ratio_DEMO`'s objective (`i_figure_merit = -14`) is literally the lifted variable, so after the lift the problem lives in constraint 93 | **OPEN.** (a) the user ruled the visits stay and are disclaimed (D21 d) — quote the *sweep* share on the table's own population, never the 40 % visit share; a driver-side skip would be a later task needing approval. (b) needs no fix: a reporting obligation (rung labels not comparable across configurations). Archived queue I-20; `reports/deprecated/A58_driver_predicate_counters.md` |
| **I-25** | **The campaign chain's `tally_contracts` part 1 wants GR's records in the same tree.** A campaign worktree with no `runs/gates/` stops at `tally_contracts` even with the campaign sources, because part 1 checks the reference cells over GR's 20 runs (A75 report, item 2). Options: the campaign plan declares the dependency and the press seeds or makes GR's records; or part 1 moves to the gate that owns it. Filed 2026-09-14 at A75's merge. | **OPEN** — small harness task; no runs if seeded |
### 3.2 Closed — the index

| # | Was | Closed | Recorded in |
|---|---|---|---|
| **I-7** | "no free iteration-variable number" — overstated; the cap is derived | 2026-09-15, D28 (the user) | archived queue I-7 (downgraded there); D28 |
| **I-13** | Phase A's `hoisted_nodes()` vs the production hoist on `large_tokamak_eval` | 2026-09-14 as moot (A26 fix 4, D17); confirmed by D28 | archived queue I-13; `reports/deprecated/A74_queue_v2.md` |
| **I-17** | the V2 Phase A → B transfer over-predicted B3's saving | 2026-09-15, D28 (the user), with A44 (transfer-gap)'s explanation | archived queue I-17; `reports/deprecated/A44_transfer_gap.md`; plan §5.2 |
| **I-24** | the tally had no campaign source; the first campaign press read 0 of 949 records | 2026-09-14, A75 | `reports/deprecated/A75_campaign_tally_source.md`; harness plan amendment 26; TRAPS T15 |
| **I-26** | the check-2 table's *evaluations median* column was the sweep ratio (`n_model_calls`), not the evaluation-count ratio | 2026-09-15, A80 (report-accuracy-audit): refilled from `sweeps_per_eval.n_evaluations` in tally and analysis, the sweep ratio kept beside, schema sentence corrected | `reports/deprecated/A80_report_accuracy_audit.md` §3; report Tables D.70–D.72 |

---

## 4. The queue

Rows are filed by state. A task appears in exactly one table. **Tasks A1–A74 live only in the archived queue** (its "The queue" tables: live chain, parked, optional/deferred, merged — one row each, with the merge commit, the report and the records path); A74 (queue-v2) is the last task of that file. By D28 (the user, 2026-09-15): A9–A12 (the subdriver line) are **cancelled**, A6 and A8 are **moot**, A14–A17 are **closed** (deferred, never authorised), the experiment-v2 and sequencing-comparison rows are history. Numbering continues from A76.

### 4.1 Open — PROPOSED, QUEUED, DISPATCHED, BLOCKED

| # | Task | Prereqs | State |
|---|---|---|---|
| **A83** | **headline-tables-in-text** — the report's tables reformatted to **one construction, one table**, and the headline tables back in the main text with their discussion. The user (2026-09-15): *"The previous task moved ALL tables to the appendix. Please keep the headline tables, with their discussion, in the main text of the v4 report"*; and, on Appendix D: *"these seem expanded over a bunch of different tables with one row, which makes no sense at all. Critically reassess the report formatting yourself, and improve the reporting."* The orchestrator's reassessment and the table-by-table layout are the second part of [`plans/REPORT_HEADLINE_TABLES.md`](plans/REPORT_HEADLINE_TABLES.md) (census at `d483c768`: 82 appendix tables for 17 constructions, 21 with one row; companion 162 with every table twice): main text §4.2 shape 3 (displaced) and §4.3 shapes 1 and 2, each rendered between markers, numbered `Table n`, followed by its discussion; Appendix D about fifteen tables — configurations stacked under sub-heading rows, regimes as column groups, one-row tables absorbed into their host table, the seed set and the optimisation-phase taxonomy absorbed into per-arm success; the companion one table per construction with seeds as rows and no recomputed copies. A **rendering** change only: the renderer combines the tally's per-(configuration, source) tables under a declared layout per construction kind; tally, stage records and the gates over cells unchanged; a committed cell-preservation check keyed by construction/configuration/source/row/column; `check` IDENTICAL both documents, 0 dangling; every citation re-pointed (T17). Zero PROCESS runs | A82 merged (`0d1fbfc4`, done) | **DISPATCHED 2026-09-15** (worktree `A83-headline-tables-in-text` off the trunk after the reassessment, seeded with the A82 records tree); QUEUED 2026-09-15 at the user's instruction |

### 4.2 Merged — the index

One line per task merged since this file was created (rule Q2); what a task delivered is its report's job.

| # | Keyword | Merged | Recorded in |
|---|---|---|---|
| **A75** | campaign-tally-source | 2026-09-14, `004eb06b` | `reports/deprecated/A75_campaign_tally_source.md`; `../idf_probe/runs/A75_runs/`; the campaign's own records `../idf_probe/runs/campaign_57dc0c14/` (949 at `57dc0c14`: 921 ok, 28 crashed; a first press was killed with the shell before any record and left nothing) |
| **A76** | fixed-point-distance | 2026-09-15, `8422dc38` | `reports/deprecated/A76_fixed_point_distance.md` (assessment §11: headline row recomputed independently to every digit); `../idf_probe/runs/A76_runs/`; 9 tables in report §4.2/§4.4, one §5.1 paragraph; 0 PROCESS runs; session `process-surgery-c1` |
| **A77** | v5-check2-decomposition | 2026-09-15, `f276fbb5` | `reports/deprecated/A77_v5_check2_decomposition.md`; `plans/V5_IMPROVEMENT_LIST.md` item 1; found I-26; doc-only; session `process-surgery-c1` |
| **A78** | arm-renames | 2026-09-15, `0b89e986` | `reports/deprecated/A78_arm_renames.md` (assessment §12); `../idf_probe/runs/A78_runs/` (latest records); `records.RECORDED_ARM_NAMES`; T16; harness plan amendment 27; `switch_composition`'s worktree-path comparison fixed on the branch (was FAIL 3/141 → 141/0, 4/4) |
| **A79** | report-captions | 2026-09-15, `6c9762bd` | `reports/deprecated/A79_report_captions.md` (assessment §12); `../idf_probe/runs/A79_runs/` (latest records); report §4 as conclusions, Appendix D (80 tables), companion `RESULTS_TABLES_FULL.md` (150); amendment 28; T17; V5 list item 2 |
| **A81** | benchmarking-practices | 2026-09-15, `95bd8d08` | `reports/deprecated/A81_benchmarking_practices.md` — the evaluation is its §2–§7 (34 criteria: 19 met, 8 partly, 4 not, 3 n.a.; findings F1–F8; first written as a separate document, folded in 2026-09-15 at the user's ruling, protocol §3); doc-only; rulings → D29 |
| **A80** | report-accuracy-audit | 2026-09-15, `e746a4a6` | `reports/deprecated/A80_report_accuracy_audit.md` (assessment §11); `../idf_probe/runs/A80_runs/` (latest records); 147 rows: 89 hold, 53 corrected, 1 withdrawn, 4 unverifiable; `report_counts_check.py`; I-26 closed; D30 candidate (the predicate trial's adoption rule) |
| **A82** | per-arm-success | 2026-09-15, `0d1fbfc4` | `reports/deprecated/A82_per_arm_success.md`; `../idf_probe/runs/A82_runs/` (latest records); Tables D.67–D.69 (per-arm success), §6 case-study clause, wall-clock section withdrawn, D30 stated in §5.6; D29 (1) table half and (2), (3) discharged, D30 discharged |

---

## 5. Standing items — project administration

### 5.1 Standing rules of project administration

Every rule here binds every task and every session. The rows unify the administrative rulings that
were D-rows (numbers kept in the *Rulings* column — a number is never reused) with the working rules
the user gave in conversation. `CLAUDE.md` restates the hard rules for agents; this table is their
register.

| Rule | What it says | Rulings, date, words |
|---|---|---|
| **The repository and its history** | `wrutten/PROCESS` is the canonical fork; the research lives in `arch_surgery/`; the `IPP-SRS` branches are archived, not merged; the `PROCESS_rewritten/` scaffolding was not ported; **every number measured at `710a75c9` is discarded** and rederived at the base — nothing from the superseded study is cited as evidence | D1, D3, D4 (2026-08-31), in force |
| **The base commit is frozen** | `c0ae5b28` is the experiment's base and is never rebased, merged forward or re-pinned: the shared coordinate system with `functional_PROCESS` and the dependency-analysis pin; `upstream` is fetched for drift measurement only (open question 4) | D2 (2026-08-31), in force; `CLAUDE.md` |
| **Only the driver changes; the models are frozen** | The independent variable is the arrangement of solvers and optimisers; every model under `process/models/` stays byte-identical to the base (gate G0′). Minimal *structural* edits to a model — extracting a residual so its solution method becomes a driver choice — are permitted, **each needing the user's approval before merging**; changing what a model computes is forbidden. The two approvals given: D14(a) `lablcc`, D14(b) the `pulse.py` residual | D5, D11 (2026-08-31), in force; `CLAUDE.md` |
| **V4 runs its own copy of PROCESS** | `MDA_partitioning_experiment_v4/PROCESS/` (*"Duplicate the code into MDA_partitioning_experiment_v4/PROCESS"*), owing V3 no backward compatibility; its `models/` byte-identical to the base, gated; its permitted driver edits recorded in `copy_gates.py` and `PROCESS/CHANGES.md` | D20 (2026-09-10), in force |
| **Registry numbers are appended, never fitted into gaps** | Constraints from 93 (`lablcc` extended), iteration variables from 178; the allocation table is `plans/REGISTRY_ALLOCATIONS.md` | D10 (2026-08-31), in force |
| **Rulings are the user's** | Anything decision-worthy is written as a proposal and stamped by the user before an implementing task is dispatched; the orchestrator's autonomous decisions are implementation-level, each recorded with its reversal. Origin: D25 was minted and implemented before it was put to the user (2026-09-11, a process fault, recorded) | user, 2026-09-11 (*"Rulings that are documented should always be my rulings"*); in force |
| **Delegation mode** | 2026-09-10 → 2026-09-14 the rebuild ran under a standing delegation (*"you're on your own now, take autonomous decisions to finish the implementation … Give me a report … when everything is done"*): tasks minted in advance, driver changes merged on G1/G0′ without per-change approval, one whole-implementation assessment. Since 2026-09-14 the mode is **collaborative** (user: *"We're in collaborative mode now"*): the user is asked at every decision-worthy fork | D24 (2026-09-10), discharged; collaborative since 2026-09-14 |
| **Merged reports are not retro-edited** | A merged task report is archived under `reports/deprecated/` with its status header replaced and is never rewritten; corrections are new rows, amendments or reports that point back | D17 (2026-09-01), in force; trap T3 |
| **The queue itself** | **Q1 States.** A task is PROPOSED, QUEUED, DISPATCHED, MERGED, CANCELLED, MOOT or BLOCKED; an issue OPEN, CLOSED or DOWNGRADED; a decision in force, discharged, amended by or reversed by. A row changes state in the same commit as the fact it records, never in a later tidying commit. **Q2 Leaving the file.** A row leaves v2 when its state is terminal (MERGED, CANCELLED, MOOT, CLOSED, DOWNGRADED), and only if its closure is recorded in a committed document the removing commit names — a task's archived report; the report or amendment that closed an issue. Decisions never leave. What remains is one index line (§3.2, §4.2): number, keyword or one clause, date, pointer. **Q3 Numbers.** Never reused; the numbering line is updated in the commit that consumes the number; the archived queue's line is never touched. **Q4 Dated events.** Every dated event attaches to the row it concerns; an event about the experiment rather than the queue goes in the experiment plan's Appendix C; this file's change log stays one line. **Q5 At every merge**, in the follow-up commit: the task row → §4.2 with the merge commit and the records path the retire script printed; every issue the task resolved closed with its pointer; the report archived with its status header replaced; every document that named a moved file re-pointed; any amendment or trap the task earned added. A rule the user gives in conversation enters this table with the date and the user's words; a live pointer leaves when what it points at reaches a terminal state. | D28 (2026-09-15), in force; Q1–Q5 proposed by the orchestrator and **accepted by the user 2026-09-15** (*"all accepted"*) |
| **One heavy slot at a time; measure on an idle machine** | One heavy PROCESS press at a time on our side (written after A13 and A23 ran concurrently); measurement work when the machine is otherwise idle; the run budget is reduced wherever a change does not alter what a gate reads (`--resume` on kept records, a dry-run with `--jobs` before a resume press) | user 2026-09-01, 2026-08-31, 2026-09-11 (*"try to reduce the number of PROCESS runs for gates in general if it's not necessary"*); in force; I-8/I-10 context |
| **Pushes** | Every push of `architecture_surgery` needs the user's explicit approval, per push; `main` is never committed to | user; `CLAUDE.md` |
| **One-time setup, done** | `upstream` added read-only for drift; the first push of `architecture_surgery`; the deletion of `github.com/wrutten/PROCESS_surgery` (reported by the user, not verifiable from a session) | archived queue, "User-facing standing items" |

**Live pointers** — things that change state without a task:

| Item | State |
|---|---|
| The V4 campaign (pressed 2026-09-14 at `57dc0c14`, 949 runs) | **Done and reported** — `EXPERIMENT_REPORT.md` §4–§6, header EXECUTED AND REPORTED; records `../idf_probe/runs/campaign_57dc0c14/` (3 GB, untracked) |
| Survey tier C (C1 duplication caveat beside decision (6); C2 rule (iii)'s `-P` text vs the pool children; C3 rules (v)/(vi)/(xii) prose-only → pool-level refusal) | **Awaiting the user's ruling** (D27, deferred 2026-09-14); text in `reports/deprecated/A68_harness_simplification_survey.md` §4 |
| V4 improvement list (`plans/V4_IMPROVEMENT_LIST.md`, items 0–15) | **The list is the authority on each item's state.** Its headings mark 3 (closed in the negative, A58), 12 (A71) and 13 (A73) discharged; 5a is a pre-declared trial (G8 built by A59; adoption is decided on the campaign); 5b requires the user's review and approval; 11 was diagnosed by A61/A62 with the PROCESS-side fix upstream's; 14 and 15 were filed 2026-09-14 by A72/A73 |
| The V5 improvement list ([`plans/V5_IMPROVEMENT_LIST.md`](plans/V5_IMPROVEMENT_LIST.md), opened 2026-09-15 by A77) | Item 1 (retire check 2 as acceptance; publish R = ρ × ε). Its D22 paragraph: the user ruled in session `process-surgery-c1` (2026-09-15, as relayed by that session: *"D22 - the conclusion was to keep. that is fine for v5 as well"*) — `st_regression` stays unconditionally in V5 as in V4; the paragraph is answered, not struck. **Confirmed by the user here 2026-09-15** (*"yes"*); the list's item 1 carries the answer |
| Outgoing PROCESS defect notes (`reports/outgoing/`, five files) | Filed with the sibling (2026-09-01 NaN; 2026-09-02 five defects; 2026-09-11 `insstrain`/`None` latch, committed there by the user); 2026-09-03 st query and 2026-09-04 first-wall note staged, handoff the orchestrator's under the demonstrated-defect rule |

### 5.2 Known open questions (parked, not blocking)

Questions 1, 1b–1d, 2 and 3 are answered (the archived queue's "Known open questions" table; 3 by the per-run deferral of `costs`/`vacuum`/`water_use`, A33, per D28). One remains:

| # | Question | State |
|---|---|---|
| 4 | How many upstream commits separate `c0ae5b28` from `ukaea/main`, and must the write-up state that drift? | **Open** in the archive; measure at write-up (`upstream` is fetched for this purpose only, D2) |

---

## 6. Where things live

| What | Where |
|---|---|
| This queue (active) / the history | `docs/MASTER_TODO_v2.md` / [`plans/MASTER_TODO.md`](plans/MASTER_TODO.md) (archived) |
| Agent rules | [`../../CLAUDE.md`](../../CLAUDE.md); traps [`TRAPS.md`](TRAPS.md) (T1–T15, binding) |
| Experiment plans | V4 (executed and reported 2026-09-14): [`../MDA_partitioning_experiment_v4/EXPERIMENT_REPORT.md`](../MDA_partitioning_experiment_v4/EXPERIMENT_REPORT.md); V3 and V2: the sibling folders' `EXPERIMENT_REPORT.md` and `V*_EXPERIMENT_REPORT.md`; V1: [`plans/MDA_PARTITION_EXPERIMENT.md`](plans/MDA_PARTITION_EXPERIMENT.md) with `reports/MDA_partition_exp_results.md`; parked lines: `plans/SUBDRIVER_LIFT_EXPERIMENT.md`, `plans/ARCHITECTURE_EXPERIMENT_CANDIDATES.md`; superseded: `plans/deprecated/` |
| Harness plan, rules, amendments | [`plans/V4_HARNESS_IMPLEMENTATION_PLAN.md`](plans/V4_HARNESS_IMPLEMENTATION_PLAN.md) — Appendix A (amendments 1–26), Appendix A.1 (the twelve rules and what enforces each), §11 (terminology) |
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

One entry. Everything before this file's creation is the archived queue's change log (`plans/MASTER_TODO.md`, "Change log", 2026-08-31 → 2026-09-14); everything after it is a decision row (§2), an issue row (§3) or a task row (§4) with its own date.

| Date | Entry |
|---|---|
| 2026-09-14 | **Created by A74 (queue-v2) from the archived queue at `c5fc49d3`**, at the user's instruction (*"clean up the master to_do list … make a v2 version that is the active one"*); reshaped 2026-09-15 by the user's D28 rulings (closed and historical rows removed, the archive referred to). |
