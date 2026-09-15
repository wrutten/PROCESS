# The V4 report's tables — V3's formats, reproduced

> **Document status** — **RULING, 2026-09-15; binding on A85 (v3-table-formats).** The user, on
> A83's rendering: *"these headline tables are not what I gave you as images. How I want them
> formatted is based on v3 report section 4 and 5. Start by reproducing these kinds of tables,
> considering the name change of the arms. If you deviate, justify it."* This file maps every
> table of [`../../MDA_partitioning_experiment_v3/V3_EXPERIMENT_REPORT.md`](../../MDA_partitioning_experiment_v3/V3_EXPERIMENT_REPORT.md)
> §4 and §5 to the V4 table that reproduces it — same rows, same columns, same cell format —
> with the arm names translated and every deviation named and justified. It supersedes the
> layout list at the end of [`REPORT_HEADLINE_TABLES.md`](REPORT_HEADLINE_TABLES.md) (the rule
> *one construction, one table* stands; V3's per-configuration blocks under a bold
> **`config`** (n = …) line are how that rule is met for the per-module tables, exactly as V3 did).
> V3's numbers appear here only to fix the format and must not appear in the V4 report.

## 0. The arm translation, and the conventions V3's tables use

| V3 | V4 | note |
|---|---|---|
| `A0` (flat control) | `A0` | flat MDA, coupling-state test at τ |
| `A1u` (blocks, no prime) | — | not run in V4 (the prime is inside the intervention, item 0); its column is dropped and the caption says so |
| `A1` (blocks + prime) | `A2` | the partitioned arm |
| — | `A1` | V4's ownership rung (burn time pinned to a constant); V3 had no such arm |
| — | `AR` | V4's stopping-rule reference (upstream's test); V3 had no Phase A reference arm |
| `R` | `BR` | PROCESS as shipped |
| `B0` | `B0` | flat, coupling-state test |
| `B1` | `B1` | lift, flat |
| `B2` (joint test / verified outer loop) | — | removed in V4 (D22); its column is dropped |
| `B3` (trust step) | `B2` | the partitioned optimisation arm |

Conventions, all V3's, all kept: configurations in the order `large_tokamak_nof` /
`low_aspect_ratio_DEMO` / `st_regression`, written in full in the first column of a
cross-configuration table and abbreviated `tok` / `lad` / `st` only in the bold heading line of a
per-configuration block; the configuration cell blank on continuation rows of the same
configuration; a mean with its seed bracket in **one cell**, `1978 [1758, 2280]`, a bare integer
when all runs agree; ratios to three or four decimals, the result column in **bold**; verdicts
**PASS** / **FAIL** in bold; counts as `k/n`; one caption in italics *above* the table, a few
lines, saying population, denominator and construction; a bold heading line **`tok`** (n = 22)
above each per-configuration block. Where V4's arm sets differ per configuration (`B1` absent on
st; `A1` absent on st) the column is dropped for that block and the heading line says so, as V3's
st block did (*"no B1"*).

## 1. Section 4 — the evaluation phase (V3 §4, §4.4, §4.5)

**T4.1 Check 1 — matched accuracy, the headline Phase A check.** V3: one row per configuration;
columns `A0 (control)`, `A1u`, `A1` as `median / p90` of the restricted audit maximum; ratio
columns `A1u/A0 med, p90` and `A1/A0 med, p90` each ending in **→ PASS/FAIL**; `verdict` notes.
**V4:** rows the three configurations; columns `AR`, `A0`, `A1`, `A2` as `median / p90`; ratio
columns `A2/A1 med, p90` (pulsed; the declared pair) and `A2/A0 med, p90`, each with its verdict
against the factor F; `verdict` notes (the trivially-similar clause where both read 0). Displaced
regime, restricted set, frozen ruler; the stencil regimes as two further rows per configuration
labelled `stencil fwd` / `stencil bwd` in a second column, **not** separate tables. *Deviation:*
`A1u` is gone (not run); `AR` and `A1` are added (V4's arms); the mixed ruler is in T4.3, not here.

**T4.2 Cost of the prime (V3 check 3) → V4 per-call cost.** V3: one row per configuration; `A0
node calls`, `A1u`, `A1` summed over 25 seeds; ratios `A0→A1u`, `A0→A1`, `A1u→A1`; `bracket`.
**V4:** rows the three configurations (displaced regime; stencil rows below as in T4.1); columns
`AR`, `A0`, `A1`, `A2` **mean node calls per evaluation** with the seed bracket in one cell;
ratios `AR→A0`, `A0→A1`, `A1→A2` (`A0→A2` on st); prime calls per evaluation of `A2` in the last
column (V3 named them in prose; V4 has the cell). *Deviation:* per-evaluation means with a bracket
instead of V3's 25-seed sums — V3's own §4.5 rewrite moved from sums to per-run values with a
bracket for the reason it gives ("the sums hid both the denominator and the run-to-run spread");
the sums add nothing at n = 25 per arm.

**T4.3 Full distributions per configuration and arm (V3 §4.4).** V3: rows configuration × arm;
columns `min`, `median`, `max` of the restricted maximum, `Σ components > τ`, `worst run`,
`sweeps`, `node calls` as ranges. **V4:** the same rows (`AR`, `A0`, `A1`, `A2`) and columns, on
the frozen ruler; a second block with the mixed ruler's `median` and `p90` beside (V4 audits on
both rulers; both columns or neither). Displaced regime; the stencil regimes in the companion.

**T4.4 Module scope (V3 §4.5, static).** Reproduced as V4's own: DSM module, DSM rows, iterated,
executing nodes per configuration — from `harness/data/dsm_node_map.json` and the per-run
artifacts. One table; no numbers from runs.

**T4.5 Per-module sweeps per run — the Phase A headline (V3 §4.5).** V3: one block per
configuration under **`tok`** (n = 25); rows `M1`, `M2`, `M3 live`, `` `vacuum` ``, `PULSE`, `FF`,
**total calls**; columns `models` (DSM rows), `A0`, `A1u`, `A1` as **module sweeps per run** with
the bracket, `A1/A0` in bold; the total row as `Σ sweeps × models` with the `[v = 1, v = 0]`
bracket over `vacuum`'s row. **V4:** the same three blocks and rows; columns `models`, `AR`,
`A0`, `A1`, `A2`, `A2/A1` (`A2/A0` on st) — the cells are **sweeps per run** as V3's were, from
`sweeps_by_block` and the per-node census (a module's nodes execute equally often; the script
refuses if not, with a tooth, as V3's did); the total row bracketed the same way. Displaced regime
in the report; the three other regimes as the same three blocks in the companion. *Deviation:*
none in form; V4 adds the `AR` and `A1` columns and drops `A1u`.

**T4.6 The exclusion set's namespaces (V3 §4.5, "what the exclusion set is load-bearing for").**
V3: rows configuration × arm (`A0`, `A1`); columns `restricted (headline)` then p90 per excluded
namespace (`costs`, `water_use`, `vacuum`, `fwbs`, `physics`). **V4:** the same, arms `A0` and
`A2`, from each run's `audit_residual.json`. Appendix D.

**Fixed-point distance (V4 only, A76).** No V3 counterpart. One table in V3's style: rows
configuration × pair (`A0/AR`, `A1/A0`, `A2/A1` headline, `A2/A0` beside), columns `median`,
`p90`, `worst`, `≥ τ` for the displaced regime, then `median / p90` for stencil fwd and bwd.
*Justification:* the table was added at the user's request (A76) and has no V3 shape; this is the
V3 check-1 layout applied to pairs.

## 2. Section 5 — the optimisation phase (V3 §5.1–§5.6)

**T5.1 Robustness and taxonomy (V3 §5.1).** V3: rows configuration × arm (arms with identical
counts collapsed into one row, `R / B0 / B1 / B2 / B3 · 22 each`); columns `invalid seeds` (count
and the seed numbers), `ok`, `converged (ifail=1)`, `not-converged among ok`. **V4:** the same;
arms `BR`, `B0`, `B1`, `B2`; plus V4's two crash classes as two columns (`crashed (RuntimeError)`,
`coupling-loop cap`) since V4 distinguishes them (A80). This is A82's per-arm success table in
V3's form; the seed set is a column.

**T5.2 Same optimum, check 1 (V3 §5.2.1).** V3: rows configuration × pair (`R→B0 (yardstick)`,
`B0→B1 / B2 / B3` collapsed when identical, `B2→B3`); columns `all-pairs med`, `all-pairs p90`,
**verdict**, `hops`, `within-cluster med`, `within-cluster p90`, `would accept`. **V4:** rows
`BR→B0 (yardstick)`, `B0→B1`, `B0→B2`, `B1→B2` per configuration; the same columns. The `lad`
FAIL in bold as V3 printed it.

**T5.3 Location diagnostic (V3 §5.2.2).** V3: over check 1's pairs, the max relative difference
over iteration variables with the argmax named; `shared / extra vars`. **V4:** reproduce **if** the
records carry the accepted design vector (the MFILE does); a new construction under the
recomputation gate, D6's warning in the caption verbatim ("a diagnostic, never an acceptance").
If the vector is not recoverable from the records without a run, omit and say so in the report.

**T5.4 Iteration multiplier, check 2 (V3 §5.3).** V3: rows `tok` / `lad` / `st`; columns `n`,
`R`, `B0`, `B3` mean iterations, `B3/B0 mean`, `B3/B0 median [min, max]`, `B3/B0 > 1`. **V4:**
the same with `BR`, `B0`, `B1`, `B2` and `B2/B0`; the lad median 0.8125 with its bracket. The ε
row (evaluations) and the ρ row of A79's Table 9 become **two further tables of the same
shape** (V3's shape holds one quantity per table), each with its caption saying which field.

**T5.5 Identity table (V3's B2/B3 identity).** V3: `pairs`, `iterations identical`, `objf
bit-identical`. **V4:** the pair is `B1 → B2` (the partition at unchanged trajectory, ε = 1
pre-declared): `pairs`, `evaluations identical` (22/22, 11/11 — A80), `iterations identical`,
`objf bit-identical`. *Justification:* V3's table proved the trust step left the path unchanged;
V4's proves the partition does — the same claim, one rung over.

**T5.6 Lift closure, check 3 (V3 §5.4).** V3: rows configuration × lifted arm; `n accepted`,
`median abs residual (s)`, `max (s)`. **V4:** the same with `B1 / B2`; st's row `— (k = 0,
inactive)`.

**T5.7 Cost, check 4 (V3 §5.5).** V3: rows configuration × set (`ok`, `converged`); columns `n`,
`R`, `B0`, `B1`, `B2`, `B3` **summed solve-phase node calls**, **B3/B0**. **V4:** rows
configuration × set with the sets V4 declares — `every arm accepted` and `without retried seeds`
— columns `n`, `BR`, `B0`, `B1`, `B2`, **B2/B0**. *Deviation:* V4's second set differs from V3's
(V4 has one acceptance set and publishes the retried-seed exclusion beside; V3 had ok vs
converged); the caption says which.

**T5.8 Both anchors (V3 §5.5, second table).** `config`, `set`, `n`, `R→B0`, **B3/B0**, **B3/R**
→ `BR→B0`, **B2/B0**, **B2/BR**. Same rows as T5.7.

**T5.9 Sweeps and prime calls (V3 §5.5, third table).** Rows configuration × arm (`B0`, `B2`,
and `B1` where run); `node calls`, `dispatch sweeps`, `prime calls`, `prime/sweep`, `prime/node`.
V4 has every cell (`n_model_calls` is the sweep count — I-26 — `n_arrangement_method_calls` the
prime calls).

**T5.10 Per-module breakdown — the Phase B headline (V3 §5.5.1).** V3: one block per
configuration under **`tok`** (n = 22); rows `M1`, `M2`, `M3 live`, `` `vacuum` ``, `PULSE`, `FF`,
**total calls**; columns `models` (DSM rows), then per arm **module sweeps per run** with the
bracket in one cell (`1978 [1758,2280]`), `B3/B0` bold, `per-run med [min, max]`, `runs B3 > B0`
as `k/n`; the total row `Σ sweeps × models` with the bracket. **V4:** the same three blocks and
rows; columns `models`, `BR`, `B0`, `B1`, `B2`, `B2/B0`, `per-run med [min, max]`, `runs B2 > B0`;
st's block without `B1` and with V3's note that `pulse` is once-per-run there. Whole-run census
counts as V3's were (the output pass adds one sweep to every row in every arm; the caption says
so, as V3's did). *Deviation:* none in form.

**T5.11 Problem definition per configuration (V3 §5.6).** `i_figure_merit`, objective, sense,
vars, constraints (eq / ineq), pulsed — static, from the records. Reproduced as is.

## 3. What this replaces, and what stays

- A83's Tables 7–9 and Appendix D's D.2–D.14 are re-rendered in these formats; the cells are the
  same cells (the renderer's `Layout` grows the V3 forms: per-configuration blocks with a heading
  line; merged `mean [min, max]` cells; the `models`/DSM-row column; the bracketed total row).
  Where a format needs a cell the tally does not yet emit (sweeps per module per run; the
  `Σ sweeps × models` total and its `v` bracket; `Σ components > τ` and `worst run`; the
  namespace p90s; the identity counts; the location diagnostic), the tally and the analysis both
  gain it under `recomputation` — zero PROCESS runs, everything is in the records.
- The main text carries, as V3 §4 and §5 did, the tables the discussion reads from: T4.1, T4.2,
  T4.5 in §4.2; T5.1, T5.2, T5.4, T5.7, T5.10 in §4.3 — each followed by its discussion. The
  rest (T4.3, T4.4, T4.6, the fixed-point distance, T5.3, T5.5, T5.6, T5.8, T5.9, T5.11) in
  Appendix D. Every table numbered; captions above, italic, a few lines.
- The companion file keeps the per-seed and other-regime blocks in the same formats.
- Deviations beyond those named above are the task's to justify in its report, one line each.
