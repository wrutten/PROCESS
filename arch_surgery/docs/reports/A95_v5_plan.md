# A95 (v5-plan) — the V5 experiment plan, drafted from the improvement list's rulings

> **Document status** — **OPEN.** Task **A95 (v5-plan)**, branch `A95-v5-plan` (worktree
> `.claude/worktrees/A95-v5-plan`), base **`7986d408`** = `architecture_surgery`. A writing task: **no PROCESS run,
> no code change, no file written under any `MDA_partitioning_experiment_v*/` folder** (A94 makes the V5 copy
> concurrently). One living artifact delivered —
> [`../plans/V5_EXPERIMENT_PLAN.md`](../plans/V5_EXPERIMENT_PLAN.md), status **DRAFT · NOT APPROVED** — and this
> report. Arm names are today's (`AR A0 A1 A2` / `BR B0 B1 B2`; trap T16).

## 1. Verdict

The plan exists, in V4's form, with the twelve sections as briefed. **Length: 446 lines against 676 for V4's
§1–§3 (`wc -l`), two-thirds and not the third the brief aimed at**: the harness change map, the DR table, the
wall-clock instrument and the decisions section are content V4's §1–§3 did not carry (V4 kept them in the
harness plan and the improvement list), and each is a table rather than prose. Cutting further means dropping
one of the briefed sections; the plan's prose sections (§1, §3, §4) are already at or below a third. **Every declared quantity is cited to a ruling or marked as
awaiting A92 or A93**; nothing was guessed from either task. **Seven questions** are open for the user (§3
below); one more (the phase A pair) was ruled as D34 while the draft was open and is applied, not asked.

## 2. What was decided by citation

| plan section | what it declares | ruling |
|---|---|---|
| §1 purpose | existence proof in model-evaluation counts; wall clock in the appendix; iterations table kept; RQ3, RQ5 dropped; RQ4 columns only | list header and item 10; D29; D33; item 1 |
| §1 RQ1 pair | `A1 → A2` (pulsed), `A0 → A2` (st) | **D34** (2026-09-29) |
| §2 matrix | census-measured test set `c` @ τ in every non-reference arm; schedule and deferral sets once per run; prime once per evaluation before M1; phase A deferred nodes executed once and measured; `mixed` dropped | items 6 (D32), 7 (D31), 8, 5; item 10 with D30 |
| §3 criterion | read-before-write census set, DSM set a cross-check; τ by ε ≤ `epsfcn`³ (A89: 1e-8), value from A93; whole-`y` exit audit the instrument; GT the teeth gate | D32; item 6; A89 §7.2–§7.4; **[A92]**, **[A93]** |
| §4 phases | N = 25; phase A δ = 0.10, no stencil; phase B one unperturbed + 24 at δ = 0.10; three configurations unconditional; seed pairing | V4 Table 6; list header; item 10; item 1's D22 note; D26 |
| §5 acceptance | matched accuracy F = 10 median and p90 on D34's pair; fixed-point distance reported; same optimum F = 10, floor 1e-6, published with attribution; no iteration-multiplier rule, `R = ρ × ε`; per-arm success reported; nothing on a timing | V4 checks; item 4 reduced; item 1; item 3 reduced; D33 |
| §6 wall clock | the instrument, the rows, the exclusions, W = 1, the repeatability check, the three appendix tables, the expected reading; D33 supersedes D29 (2) for V5 only | item 9; D33 |
| §7 gates | kept G0, G1 per driver change, G2 re-formed, G4 (while the restriction stands), G5, G6, G7, G9; new GT (test-set teeth) and GC (count neutrality for items 7, 8); GR once at the copy; G3/G3c reconsidered; G8 dropped; self-checks kept, not reported | item 10; items 6, 7, 8; D30 |
| §8 reporting | one generator, one document, main text and appendix, one verification table, recount replaces the second implementation, report under 600 lines, no companion | item 10 |
| §9 settings | one row per knob with provenance; τ **[A93]**; W = 1; `iteration_ratio_max` retired; predicate `frozen` | as above |
| §10 budget | 3 + 275 + 275 + 9 + 3 runs; 3–5 h at W = 1 from V4's per-run `wall_s` medians (context) | V4 Table 6; the brief's figures |
| §11 change map | per item: modules changed and removed; DR9–DR13 in the harness plan's form; the census test sets and the schedule artifact added | items 5–10; harness plan §3.2 |

## 3. Open questions raised (plan §12)

1. **The flat arms and the deferrals.** "All A arms" (list item 6, the user 2026-09-29) read three ways: (a)
   `A0`/`A1` defer in phase A as A89's second-pass control was built; (b) that plus `B0`/`B1`; (c) the
   deferrals stay on the intervention rung as the paper's matrix has it. Recommendation **(b)**, with the
   paper's matrix consequence named (a row moves; `A2/A1`'s Feedforward and Post-processing rows read 1).
2. **Matched-accuracy statistic:** whole-state audit instead of the restricted one once item 5 executes the
   deferred nodes; G4 retired when the two agree on the gate job set. Recommendation: yes.
3. **G3/G3c (`cold_chain`):** its construction disappears with the prime as pre-processing. Recommendation:
   drop; G2 re-formed plus GC cover it.
4. *(Closed by D34.)*
5. **The `mixed` predicate mode:** leave in the copy uncomposed, no G1 press. Recommendation: yes.
6. **τ if A93 finds the derived value costs a start or moves the path:** declare it anyway; the rule is
   declared, the value follows; a lost start is a result.
7. **GR's twenty reference records (A94's to declare):** V4's campaign records at `57dc0c14` for the arms and
   seeds V4's GR covered, read through `RECORDED_ARM_NAMES`.
8. **Workers for the gates:** W = 1 for the campaign, repeatability and timers-off runs; gates may run at 3.

**Awaiting the two prerequisite tasks, marked in the plan:** the census population (displaced entries only, or
the optimiser's path too) and GT's form — **A92**; the campaign τ — **A93** (with A89's `--choose-tau` re-run on
the V5 copy).

## 4. Autonomous decisions, with reversal paths

- **DR numbering continues from DR8** (DR9 schedule once per run; DR10 prime once per evaluation; DR11 the
  test-set predicate; DR12 observation-only timers; DR13 conditional on Q1). Reversal: renumber in the plan's
  §11 table; nothing else cites them.
- **The count-neutrality gate is one gate (GC) covering items 7 and 8**, not one per change. Reversal: split
  its row.
- **The constraint-93 residual (V4 check 3) is a reported quantity per rung, not a verification-table row**,
  because item 10 fixes the table's rows. Reversal: add the row.
- **The run-budget time estimate uses the brief's per-run `wall_s` medians** (V4 campaign records, three
  workers, contended) and is labelled context, not a committed-script number (protocol §15 binds published
  results, not a plan's budget). Reversal: a small committed budget script reading the campaign records.

## 5. Change log (append-only)

| date | entry |
|---|---|
| 2026-09-29 | Read `CLAUDE.md`, `TRAPS.md`, the queue (§1, D29–D33, I-29/I-30, §4), the V5 list in full, V4 report §1–§3 and §6, the harness plan §0–§2 and amendments 1–34, README §0/§3/§10.1, `paper_tables.md`, A89 §7, A90 §0–§2, A91 §0/§5, the paper's results section (read-only). Plan written; report written. |
| 2026-09-29 | D34 relayed by the orchestrator (the paper's phase A pair `A2/A1` pulsed, `A2/A0` st; phase B `B2/B0`): applied in the plan's §1, §2, §5, §8; Q4 closed. |
