# A39 (v3-plan) — the V3 experiment plan written with every acceptance rule pre-declared; the M117 defect note drafted; the register's two-qualifier liveness convention recorded

> **Document status** — **CURRENT · TASK REPORT of an OPEN task.** Written 2026-09-04 by
> task A39 (v3-plan) on branch `A39-v3-plan` (worktree
> `PROCESS_surgery_worktrees/A39-v3-plan`, branched from `architecture_surgery` at
> `b7dbd2a9`). Archived to `deprecated/` at merge; folder position records lifecycle, not
> validity (trap T3). Docs only — no file under `process/` or `arch_surgery/idf_probe/`
> touched; no run executed; no number minted (every figure cited below comes from a
> committed record: A35, A38, the V2 report, or the V3 development plan). Nothing pushed.

| | |
|---|---|
| **Task** | V3 development plan §8 row T1: write `arch_surgery/MDA_partitioning_experiment_v3/EXPERIMENT_PLAN.md` from [`V3_DEVELOPMENT_PLAN.md`](../plans/V3_DEVELOPMENT_PLAN.md) (§0 fully resolved), restating every selection with its pre-declared acceptance rule, on V2's structural template; plus D-a (draft the prime's defect note for the sibling's owed M117 row) and D-b (the `DSM_VALIDATION.md` two-qualifier liveness convention amendment) |
| **Deliverables** | All three delivered, in three commits (§1). The plan carries the **NOT YET APPROVED** header — the campaign task A42 stays blocked until the user's dated execution approval, recorded as a dated edit in the plan with `EXECUTION_APPROVED` flipped in the same commit |
| **Mid-task correction** | Folded in before the plan's first commit (orchestrator, trunk `0a8f5af2`, which landed after this worktree's branch point): the **nearest-rank (upper-middle) median is pre-declared as the single construction for every Phase B check**, and the lad B2→B3 prediction anchor is ≈ 1.40 under that construction (1.33 under mean-of-middles — the only cell where the two disagree, over the same 10 pairs) |
| **Findings** | Four inconsistencies/ambiguities in or around the development plan, reported in §3, none silently repaired; all source line citations for the defect note verified with `git show` at `c0ae5b28` (§4) |
| **Environment** | Docs-only task; `git show` used for citation verification (inspection, protocol §15's permitted use — no published number originates from it) |
| **Date** | 2026-09-04 |

---

## 1. Deliverables and commits

1. **`arch_surgery/MDA_partitioning_experiment_v3/EXPERIMENT_PLAN.md`** (commit
   `29f642a1`) — the V3 experiment plan. Carries, per the brief: the objective and claim
   structure; the intervention restated per development plan §2 (the **prime** as a
   method-level hoist — `fw.set_fw_geometry()` at the sweep head — explicitly **not** a
   node reorder; `n_prime_calls` stamped, never pooled; the coverage requirement A40
   verifies); arms per §3 (Phase A A0/A1u/A1 with the V2 entry regime and the regime
   disclosure quoted **verbatim** from the V2 report §7; Phase B R/B0/B1/B2/B3 with the
   prime in A1/B2/B3 only per O4/D19, `st_regression` skipping B1, no prime-free Phase B
   twins per O5); checks per §4 with every acceptance rule pre-declared (restricted
   similarity with the whole-state audit beside, F = 10 at median and p90; same-optimum
   with the R→B0 yardstick, **floor = 1e-6 relative on `norm_objf`** per O3 and acceptance
   `spread ≤ max(F × yardstick, floor)`; the multi-attractor clustering rule with hop
   rates and R→B0 as comparator; iteration multipliers over the **declared
   both-converged pairing** with the ≤ 1.05 bound on the **nearest-rank** median only;
   the pre-declared lad prediction with both outcomes declared results; lift closure;
   the deck-invalid-seed statistic; **no robustness claim**); gates G0–G7 with their
   teeth, carried verbatim from development plan §5; N = 25 / δ = 0.10 / τ = 1e-6; the
   A38-reuse clause (A1u measured at `9fcedc92` on the `a4446bed` mint lineage; reuse
   licensed by G1, else re-run — the V3 report states which); scope per §9; captions on
   every table (protocol §16); directory and run discipline as Appendix A
   (`EXECUTION_APPROVED = False` until the dated approval; A41's verbatim-copy-first
   rule).
2. **D-a** (commit `04f31e7d`) —
   [`outgoing/2026-09-04_first_wall_thickness_read_before_write.md`](outgoing/2026-09-04_first_wall_thickness_read_before_write.md),
   the draft defect note for the sibling's owed M117 row, plus its `README.md` table row
   **marked DRAFT**. Content: the read-before-write pair with every site (writer
   `fw.py:347-352`; earlier readers `build.py:836`/`:840` and `:1940-1947`, with the
   further pair reads `:1867`/`:1877`/`:1887`; the stale self-read `fw.py:54-55` before
   `:110`); A35's displaced-state magnitudes (depth-1 transport delay; 1.459e-2 →
   8.3e-16 in one verified pass on `large_tokamak_nof`; δ-ratio ≈ 2.00, identically 0 at
   fixed-point entries); A38's per-deck images (25/25 linear images of the pair on nof
   and st, the gain-47.0 second image on st, lad's open term); and the
   initialisation-time fix shape (compute the pair in `init.check_process`,
   `process/core/init.py:251`, beside the double-null geometry derivation at
   `:607-617`, delete the model's write; same treatment for the `vpfskv` literal —
   writer `power.py:571`, sole computational reader `pulse.py:224` at `c0ae5b28`, line
   326 in the working tree after A24's `0a2e64f3`). Every line number verified with
   `git show` at `c0ae5b28` per A31 §7, and the note says so. **The handoff itself is
   the orchestrator's**; the note's status header states it binds nobody until then.
3. **D-b** (commit `7ac105f0`) — dated convention amendment in
   [`DSM_VALIDATION.md`](DSM_VALIDATION.md), after the register's rule paragraph: a
   liveness verdict must state **both value-liveness and displacement-liveness**
   ("value-frozen ≠ displacement-inert", V15; user agreed 2026-09-04). Existing entries
   V1–V14 are grandfathered, not rewritten; V15 is named as the measured motivating case.

## 2. Autonomous decisions, with reversal paths

1. **The per-pair denominator of the relative same-optimum spread is fixed as
   max(|`norm_objf`|ₐ, |`norm_objf`|ᵦ)** (plan §4.2 check 1). O3 declared "floor = 1e-6
   relative on `norm_objf`" and the `max(F × yardstick, floor)` rule but left the
   per-pair relative construction unstated; a pre-declared acceptance rule cannot leave a
   denominator to the tally's discretion (trap T11). The symmetric max avoids an
   arbitrary side choice. *Reversal:* a dated amendment to the plan before approval —
   nothing has run.
2. **The clustering procedure of check 1a is operationalized**: accepted optima pooled
   per deck across arms and seeds, sorted by `norm_objf`, a relative gap > 10 × floor
   between consecutive values splits clusters; hop = a both-converged pair straddling
   clusters. The development plan named the gap rule but not the pooling/sorting.
   *Reversal:* as decision 1.
3. **D-a is a separate document staged in `outgoing/`** (the brief allowed a task-report
   section or a separate doc under `arch_surgery/docs/`): `outgoing/` is this
   repository's established convention for sibling-destined documents, its README says
   staging is not filing, and the note follows the destination's own naming and
   structure (their `<date>_<slug>.md`, their five-defect report's headers). The README
   row and the status header both mark it DRAFT with the handoff reserved. *Reversal:*
   delete the file and the README row; nothing references them.
4. **G2's component counts are labelled by deck in the plan** — 840 (nof) / 846 (lad) /
   827 (st) — rather than carried as the development plan's unlabelled "(827 / 840 /
   846)" (see finding 3.1). The numbers are identical as a set; only labels were added.
   *Reversal:* none needed if the labelling is confirmed; if my deck attribution were
   wrong, one table cell in plan §6 changes.

## 3. Findings — inconsistencies in and around the development plan (reported, not repaired; the source document is the orchestrating session's and is not edited here)

1. **G2's count ordering is ambiguous in the source.** Development plan §5 G2 writes
   "exit states bit-identical on N/N components (827 / 840 / 846)" — ascending order —
   while the document's deck order everywhere else (medians, ratios) is nof/lad/st,
   which is 840/846/827. The counts match the known per-deck spec sizes (A38 §1: 840
   nof, 846 lad, 827 st), so the set is right and only the ordering is unlabelled; the
   V3 plan labels each count explicitly.
2. **The lad prediction anchor in development plan §4.2 ("stays ≈ 1.33") is superseded**
   by the orchestrator's mid-task correction (trunk `0a8f5af2`): the V2 cell is
   construction-dependent — mean-of-middles 1.33, nearest-rank 1.40, same 10 pairs — and
   the correction landed after this worktree's branch point, so the V2 report's dated
   dagger note it cites is **not visible in this worktree's copy** of
   `V2_EXPERIMENT_REPORT.md` §5.3. The V3 plan pre-declares the nearest-rank
   construction and anchors at ≈ 1.40, and its change log records the supersession. The
   development plan still reads 1.33 and should be reconciled by its owner (a dated
   note), not by this task.
3. **O3's rule left the per-pair relative construction unstated** (decision 2.1 above) —
   flagged so the user's approval read sees that one construction in plan §4.2 check 1
   originates from this task, not from the development plan.
4. **A citation nuance in the task brief, harmless but worth the record:** `build.py:840`
   does not itself read the `dr_fw` pair — it writes the downstream mover
   `dz_tf_upper_lower_midplane` from `z_tf_top`, which carries the pair via the read at
   `:836`. The defect note cites the two lines in those distinct roles.

Verified consistent (no finding): the development plan §2 implementation sketch's site
names against `process/core/caller.py` at this branch (`_call_models_once`'s
stellarator/IFE early returns, the `SEQUENCE_HEAD` loop, `_sweep_block`); the A38 figures
quoted in §3.1 of the development plan against `deprecated/A38_audit_rerun.md`; the V2
prior-context ratios 0.522/0.568/0.502 against both the V2 report and A38's exact
0.5217/0.5680/0.5016; the regime-disclosure sentence against the V2 report §7 (quoted
verbatim in plan §3.2).

## 4. Citation verification (defect note, per A31 §7)

All with `git show` at `c0ae5b28`: `fw.py:347-352` (`set_fw_geometry` writes the pair);
`fw.py:54-55` (self-read into `calculate_first_wall_half_height`) before `:110` (its own
`set_fw_geometry()` call); `build.py:836` (`z_tf_top` carries 0.5·(in+out)), `:840`
(`dz_tf_upper_lower_midplane`), `:1867` (`rbld`), `:1877` (`r_shld_inboard_inner`),
`:1887` (`r_shld_outboard_outer`), `:1940-1947` (`dr_shld_vv_gap_outboard`, ripple
branch); `power.py:571` (`vpfskv = 20.0e0`); `pulse.py:224` (`v = vpfskv * 1.0e3`; the
same line is 326 at this branch's HEAD, after A24's `0a2e64f3`); `process/core/init.py:251`
(`def check_process`) and `:607-617` (the double-null `n_divertors` /
`dz_fw_plasma_gap` derivation). No discrepancy found against the task brief or the
development plan.

## 5. Change log

- 2026-09-04 — worktree entered at `b7dbd2a9`; read `CLAUDE.md`, `TRAPS.md`,
  `V3_DEVELOPMENT_PLAN.md` (full), queue rows A38–A42 and D19, V2's `EXPERIMENT_PLAN.md`
  (template), V2 report, A38 report, A35 report (carrier sections), `DSM_VALIDATION.md`,
  the sibling's M117 report and Owed row (read-only).
- 2026-09-04 — orchestrator mid-task correction received (nearest-rank median
  declaration; lad anchor 1.40) and folded into the plan before its first commit.
- 2026-09-04 — deliverable 1 committed (`29f642a1`); D-a committed (`04f31e7d`); D-b
  committed (`7ac105f0`); this report written.

## Orchestrator assessment (pre-merge, 2026-09-04)

Docs task — reviewed against the development plan, the V2 report and the records; no
numeric recheck applies. All four deliverables verified present and correctly scoped; key
declarations spot-checked in `EXPERIMENT_PLAN.md`: the **NOT YET APPROVED** header with the
same-commit `EXECUTION_APPROVED` flip rule; the nearest-rank median pre-declaration with
its 1.33/1.40 provenance (the mid-task correction folded in before the plan's first
commit, as instructed); floor = 1e-6 relative (O3); prime in A1/B2/B3 only (O4/D19);
G0–G7 verbatim with G3c owning A38's open lad term; the A38-reuse clause at `9fcedc92`
licensed by G1. Findings adjudicated: (1) the dev plan's unlabelled G2 counts — confirmed
(trunk line 246, "(827 / 840 / 846)" against the document's nof/lad/st order) and fixed on
trunk with a dated edit at merge; (2) the ≈ 1.33 supersession was already applied on trunk
at `0a8f5af2`, which post-dates this branch point — no action, correctly reported rather
than silently repaired; (3) the per-pair relative denominator (max of the two
`|norm_objf|`) is a sound symmetric construction, endorsed, and stays flagged for the
user's approval read exactly as the agent placed it; (4) the `build.py:836` read /
`:840` write role distinction matches A35's record. D-a's staging under
`docs/reports/outgoing/` with the handoff reserved to the orchestrator is the correct
pattern under the never-write-siblings rule. **Merge approved.**
