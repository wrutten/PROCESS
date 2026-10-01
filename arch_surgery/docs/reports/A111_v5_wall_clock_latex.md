# A111 (v5-wall-clock-latex): a LaTeX block for the phase B wall-clock tables

> **Document status**: **OPEN (task report, awaiting the orchestrator's assessment).** Task A111, branch
> `A111-v5-wall-clock-latex`, worktree `.claude/worktrees/A111-v5-wall-clock-latex`, from trunk `decde489`,
> 2026-10-01. Harness generator only: no change to the driver copy (`MDA_partitioning_experiment_v5/PROCESS/`),
> to `process/` or to V4; no PROCESS run made beyond what `--selfcheck` makes itself.
>
> **Commits:**
> - Generator: `4ea5ac59`, committed before either document was written.
> - Both tables documents: `9e1e99e1`.
> - This report: the commit that adds it.

## The request

The user, 2026-10-01: *"In the paper tables, please add a latex variant of the phase B in wall clock, s per
optimisation, for all three configs"*, then *"for e-6"*. The campaign at τ = 1e-6 is run ID
`write_set_tau1e-06` (`--test-set write_set`), document `paper_tables_write_set_tau1e-06.md`. The generator is
shared, so the default campaign's `paper_tables.md` gains the same block over its own numbers.

## What changed in the generator

`arch_surgery/MDA_partitioning_experiment_v5/harness/measurement/`:

- **`timing.py`** — new `table_cells(table)`: one phase table's printed cells row by row (one per arm, then the
  ratio of the means and the median with [min, max]), formatted by the existing `_fmt` / `_fmt_ratio`.
  `render_markdown` now prints its phase A and phase B grids through it; its output is unchanged (shown by the
  documents' diff below: no existing line moved, and the timing stage's own test document uses the same call).
- **`paper_tables.py`**
  - `wall_phase_b_tabular(tables)` — the three configurations' phase B wall-clock tables as **one** `tabular`
    in the house style of `tab:phaseB_results`: column spec `l|cccc|cc`; header
    `Row & BR & B0 & B1 & B2 & B2/B0 & B2/B0 med [min, max] \\`; per configuration a
    `\multicolumn{7}{l}{\texttt{<short>} ($n = <n_pairs>$)} \\` line and `\hline`, the table's rows in order,
    an `\hline` above `Total`, and an `\hline` closing the block. Every cell is `timing.table_cells`'s string
    (the one the Markdown grid prints), passed through the existing `_tex` (`—` → `--`); labels through a new
    `_latex_label` (escapes `\ & % $ # _ { }`, then `_tex`). The header's pair and arms are the tables' own and it
    refuses if the three tables disagree on them.
  - `wall_latex_check(md_lines, tex_lines)` — reads both renderings back: per configuration `n` (Markdown:
    the `N pair(s)` of the table's caption; LaTeX: `$n = N$`), then row by row the label and every cell; a
    row or configuration on one side only is a mismatch. `_wall_latex_tooth` doctors one LaTeX cell (the first
    row's first arm cell, one digit appended) and requires the check to catch it.
  - `render` carries the result as `wall_latex_check`; `_refuse_on_mismatch` (used by both `write` and `check`)
    refuses on any mismatch or a tooth that does not bite; `report` prints the line
    `phase B wall-clock LaTeX against its Markdown grids: … mismatched of … compared; tooth bites|DOES NOT BITE`.

There was no existing LaTeX-vs-Markdown cross-check for the main-text tables (their cross-check, `cross_check`,
compares built values with the stage records, not the two renderings), so the check is new and covers this
block only.

**Gates.** The change touches nothing a gate reads: `stage_provenance` calls `assert_gate_table_current` /
`assert_stage_read_what_is_there` (unchanged); `tally_contracts` does not read the generator. No gate was
pressed.

## Where the block sits

At the **end of the wall-clock section** (`### Tables — wall clock (plan §6)`), after the last configuration's
(`st_regression`) phase B cost-breakdown table and before `### Table — per-arm success` — appended after
`timing.render_markdown`'s output, which keeps the generator simple. Above it, one line: its title
(`phase B in wall clock, s per optimisation — LaTeX`), that it is the LaTeX form of the phase B wall-clock tables
above, the check's result, and *"Wall clock is context, never evidence (D33)."*

## Diff extent of the two documents

`git diff --stat` of the re-rendered documents against `decde489`:

```
 .../MDA_partitioning_experiment_v5/paper_tables.md | 58 ++++++++++++++++++++++
 .../paper_tables_write_set_tau1e-06.md             | 58 ++++++++++++++++++++++
 2 files changed, 116 insertions(+)
```

One hunk in each, pure insertion, 0 lines deleted: `paper_tables.md` `@@ -402,0 +403,58 @@`,
`paper_tables_write_set_tau1e-06.md` `@@ -404,0 +405,58 @@`. No existing cell moved; the generator does not stamp
its own commit into the document, so there is no stamp-line change.

## Checks

| check | result |
|---|---|
| `--paper-tables check --test-set write_set` | cross-check with the stage records 0 mismatched of 178, tooth bites; phase B wall-clock LaTeX against its Markdown grids **0 mismatched of 258**, tooth bites; `paper_tables_write_set_tau1e-06.md`: **IDENTICAL** |
| `--paper-tables check` (default, `census_tau1e-08`) | cross-check 0 of 178, tooth bites; LaTeX against Markdown **0 mismatched of 258**, tooth bites; `paper_tables.md`: **IDENTICAL** |
| `--selfcheck` | **verdict: PASS** (8 checks PASS, 0 otherwise) |

258 compared cells = 3 configurations × (the `n` pair, 2 cells + 12 rows × 7 cells: label, four arms, ratio,
median with bracket).

## The LaTeX block of `paper_tables_write_set_tau1e-06.md`, verbatim

**phase B in wall clock, s per optimisation — LaTeX** — The LaTeX form of the phase B wall-clock tables above, the 3 configurations in one `tabular` (n is each table's pair count): every cell the Markdown grid's own string, compared with it before writing — **0 mismatched of 258**; a doctored cell caught: **yes**. Wall clock is context, never evidence (D33).

```latex
\begin{tabular}{l|cccc|cc}
\hline
Row & BR & B0 & B1 & B2 & B2/B0 & B2/B0 med [min, max] \\
\hline
\multicolumn{7}{l}{\texttt{tok} ($n = 22$)} \\
\hline
M1                        & 6.69 & 7.54 & 7.41 & 5.06 & 0.67 & 0.69 [0.53, 0.84] \\
M2                        & 6.52 & 7.25 & 7.14 & 6.09 & 0.84 & 0.87 [0.66, 1.08] \\
M3                        & 1.37 & 1.52 & 1.49 & 1.11 & 0.73 & 0.73 [0.57, 0.95] \\
Feedforward               & 0.02 & 0.02 & 0.02 & 0.01 & 0.34 & 0.35 [0.24, 0.46] \\
Post-processing           & 0.39 & 0.42 & 0.42 & 0.00 & 0.00 & 0.00 [0.00, 0.00] \\
MDA convergence test      & 0.08 & 10.63 & 10.48 & 8.22 & 0.77 & 0.79 [0.63, 1.01] \\
dispatch                  & 0.23 & 0.30 & 0.31 & 0.55 & 1.80 & 1.89 [1.25, 2.38] \\
objective and constraints & 0.33 & 0.14 & 0.14 & 0.14 & 1.02 & 1.01 [0.52, 2.01] \\
optimiser own time        & 0.15 & 0.11 & 0.10 & 0.10 & 0.92 & 0.95 [0.45, 2.56] \\
fixed per run             & 5.11 & 5.28 & 4.59 & 4.62 & 0.88 & 0.88 [0.73, 1.02] \\
unattributed residual     & 0.03 & 0.11 & 0.11 & 0.15 & 1.35 & 1.42 [0.92, 1.96] \\
\hline
Total                     & 20.92 & 33.33 & 32.21 & 26.05 & 0.78 & 0.80 [0.62, 0.94] \\
\hline
\multicolumn{7}{l}{\texttt{lad} ($n = 11$)} \\
\hline
M1                        & 27.62 & 27.17 & 18.54 & 12.68 & 0.47 & 0.57 [0.08, 4.11] \\
M2                        & 28.65 & 27.88 & 19.03 & 16.43 & 0.59 & 0.71 [0.10, 5.22] \\
M3                        & 5.89 & 5.60 & 3.81 & 3.02 & 0.54 & 0.65 [0.09, 4.89] \\
Feedforward               & 0.07 & 0.07 & 0.04 & 0.02 & 0.25 & 0.30 [0.04, 2.30] \\
Post-processing           & 1.64 & 1.53 & 1.03 & 0.00 & 0.00 & 0.00 [0.00, 0.00] \\
MDA convergence test      & 0.32 & 40.16 & 27.25 & 21.83 & 0.54 & 0.65 [0.09, 4.98] \\
dispatch                  & 0.97 & 1.08 & 0.74 & 1.37 & 1.27 & 1.60 [0.22, 11.59] \\
objective and constraints & 1.42 & 0.50 & 0.36 & 0.37 & 0.75 & 0.75 [0.17, 7.01] \\
optimiser own time        & 0.38 & 0.31 & 0.23 & 0.24 & 0.77 & 0.78 [0.13, 6.36] \\
fixed per run             & 5.46 & 5.19 & 4.44 & 4.48 & 0.86 & 0.86 [0.80, 0.99] \\
unattributed residual     & 0.23 & 0.47 & 0.31 & 0.42 & 0.88 & 1.13 [0.14, 9.36] \\
\hline
Total                     & 72.64 & 109.97 & 75.78 & 60.86 & 0.55 & 0.67 [0.10, 4.34] \\
\hline
\multicolumn{7}{l}{\texttt{st} ($n = 22$)} \\
\hline
M1                        & 20.37 & 17.64 & -- & 11.09 & 0.63 & 0.69 [0.16, 0.91] \\
M2                        & 19.93 & 16.89 & -- & 11.10 & 0.66 & 0.69 [0.17, 1.00] \\
M3                        & 5.01 & 4.17 & -- & 2.68 & 0.64 & 0.70 [0.16, 0.96] \\
Feedforward               & 0.00 & 0.00 & -- & 0.00 & -- & -- \\
Post-processing           & 1.17 & 0.98 & -- & 0.00 & 0.00 & 0.00 [0.00, 0.00] \\
MDA convergence test      & 0.22 & 24.92 & -- & 16.58 & 0.67 & 0.71 [0.17, 1.01] \\
dispatch                  & 0.62 & 0.64 & -- & 1.00 & 1.57 & 1.61 [0.39, 2.49] \\
objective and constraints & 0.81 & 0.25 & -- & 0.22 & 0.86 & 0.89 [0.22, 1.31] \\
optimiser own time        & 0.29 & 0.24 & -- & 0.24 & 0.99 & 0.99 [0.21, 1.84] \\
fixed per run             & 5.19 & 5.17 & -- & 4.60 & 0.89 & 0.89 [0.76, 1.03] \\
unattributed residual     & 0.13 & 0.30 & -- & 0.34 & 1.12 & 1.11 [0.24, 1.84] \\
\hline
Total                     & 53.73 & 71.20 & -- & 47.83 & 0.67 & 0.72 [0.19, 0.98] \\
\hline
\end{tabular}
```

## Orchestrator's critical assessment (protocol §5) — verdict: merge

*Written 2026-10-01 by the orchestrating session. Checked differently from the agent.*

**Checked.** (1) `git diff --stat decde489..9bebbd51`: five files — the generator (`paper_tables.py`, `timing.py`), the
two tables documents and this report; 0 diff lines under the V5 driver copy, `process/` or V4; worktree clean. (2) The
two documents gain 58 lines each and lose none: no existing line moved. (3) `--paper-tables check` reads IDENTICAL
under both settings at the tip. (4) The LaTeX block of `paper_tables_write_set_tau1e-06.md`, parsed by the
orchestrator with its own few lines and compared with the three Markdown phase B wall-clock grids of the same
document: 12 rows per configuration, every cell equal on `tok`, `lad` and `st`.

**One thing a reader of the block should know.** On `st` the Feedforward row prints 0.00 in three arms with no ratio,
where the count tables print the group as absent (`--`). It is what the Markdown grid prints, so the block is faithful
to it; whether the row is kept in the paper is the user's choice. Wall clock is context, never evidence (D33).
