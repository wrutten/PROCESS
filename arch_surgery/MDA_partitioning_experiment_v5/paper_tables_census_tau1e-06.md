# Paper tables — Case 2: PROCESS

> **Document status** — **GENERATED, never hand-edited.** Written whole by `harness/measurement/paper_tables.py` (`experiment_runner.py --paper-tables write`) from the campaign's run records and the stage records, and compared whole by `--paper-tables check`, which refuses when this file and the records disagree. The one document of V5 list item 10: the main-text tables of `Structuring-fusion-MDAO-with-DSMs/3 results.tex` and the appendix tables of the V5 plan §8; each table is a Markdown grid and, where the paper prints it, LaTeX rows for the paper's `tabular` body.

*Over the **campaign** population — 553 run records at `448d6bde`; sources `campaign_displaced` (phase A) and `campaign_optimisation` (phase B); the exit audit at position(s) `after_single_evaluation`, `entry_to_write_output_files` on the ruler(s) `frozen`.*

*Of run ID **`census_tau1e-06`** — test set census, tau 1e-06 (overridden); records under runs/census_tau1e-06/; not the declared default campaign's (`census_tau1e-08`, whose document is `paper_tables.md`).*

**Conventions.** A module cell is that module's **sweeps per run** — per `call_models` evaluation in phase A, per whole optimisation in phase B — averaged over the arm's n runs. Every model node of a module runs once per sweep, so a sweep ratio does not depend on whether one counts model calls or DSM rows. The ratio column is the **ratio of the means** (Σ intervened / Σ control over the paired runs); the next column is the per-run ratio's median with its [min, max]. **The phase A pair is `A2/A1` on the pulsed configurations and `A2/A0` on `st` (D34)**: the comparison at matched accuracy and the same fixed point; phase B's is `B2/B0`. **Feedforward** is the pulse node and the feed-forward tail (run once per evaluation after M3, no iteration); **Post-processing** is the once-per-run set — nodes no objective or constraint depends on, which the partitioned arm defers. **`A2`'s Post-processing cell is measured, not charged**: V4 charged it 1 by construction (`CHARGED_ONCE`, retired); since item 5's driver change (A101, D35) the run executes the deferred set once after convergence and the census counts it, so the cell reads the measured 1. There is **no total row**: sweeps of different modules do not add. Rounding: phase A sweep means and phase B iteration means to one decimal, phase B module sweeps to integers, every ratio, median and bracket to two decimals; `A2`'s phase A Feedforward and Post-processing cells are the one integer every run reads (checked). `—` is a group that does not exist on the configuration or an arm inactive there (`A1`/`B1` on `st`).

Node groups per configuration (phase A; phase B's are restated in its section only where they differ):

- `tok`: Feedforward = `pulse`; Post-processing = `costs`, `vacuum`, `water_use`
- `lad`: Feedforward = `pulse`; Post-processing = `costs`, `vacuum`, `water_use`
- `st`: Feedforward = — (none); Post-processing = `costs`, `pulse`, `vacuum`, `water_use`

**Comparison with the stage records.** 178 cells these tables share with the tally's stage records compared exactly — phase A's per-arm means and, on D34's pair (the tally's own reference), its pooled ratios and pair counts; phase B's iteration cells and its module means before the exit audit is taken out: **0 mismatched of 178**; the comparison caught a doctored cell on each of the three sides: **yes**.

## Main text

### Table — the switch matrix

One column per arm, one row per switch, from `harness/experiment/arms.py`'s matrix — the data every arm is composed from, printed rather than transcribed. `⁺`-marked rows are pulsed configurations only; on `st` the arms `A1`/`B1` compose to `A0`/`B0`.

| | **AR** | **A0** | **A1** | **A2** | **BR** | **B0** | **B1** | **B2** |
|---|---|---|---|---|---|---|---|---|
| MDA solve | upstream | flat | flat | partitioned | upstream | flat | flat | partitioned |
| stopping rule | objf/conf | feedback couplings @ τ = 1e-06 | feedback couplings @ τ = 1e-06 | feedback couplings @ τ = 1e-06 per block | objf/conf | feedback couplings @ τ = 1e-06 | feedback couplings @ τ = 1e-06 | feedback couplings @ τ = 1e-06 per block |
| block schedule | — | (one block) | (one block) | one pass | — | (one block) | (one block) | one pass |
| arrangement · node (build after physics) | — | — | — | ✓ | — | — | — | ✓ |
| arrangement · method (prime) | — | — | — | ✓ | — | — | — | ✓ |
| deferral per_call | — | — | — | ✓ | — | — | — | ✓ |
| deferral per_run | — | — | — | ✓ | — | — | — | ✓ |
| burn time out of the loop | — | — | ✓ | ✓ | — | — | ✓ | ✓ |
| burn-time owner | loop | loop | constant | constant | loop | loop | optimiser | optimiser |
| input file ⁺ | committed | committed | committed | committed | committed | committed | lifted | lifted |
| output-time loop (MDA_Output) | n/a | n/a | n/a | n/a | upstream | upstream | none | none |

```latex
\begin{tabular}{l|cccccccc}
\hline
 & AR & A0 & A1 & A2 & BR & B0 & B1 & B2 \\
\hline
MDA solve & upstream & flat & flat & partitioned & upstream & flat & flat & partitioned \\
stopping rule & objf/conf & feedback couplings @ $\tau$ = 1e-06 & feedback couplings @ $\tau$ = 1e-06 & feedback couplings @ $\tau$ = 1e-06 per block & objf/conf & feedback couplings @ $\tau$ = 1e-06 & feedback couplings @ $\tau$ = 1e-06 & feedback couplings @ $\tau$ = 1e-06 per block \\
block schedule & -- & (one block) & (one block) & one pass & -- & (one block) & (one block) & one pass \\
arrangement · node (build after physics) & -- & -- & -- & $\checkmark$ & -- & -- & -- & $\checkmark$ \\
arrangement · method (prime) & -- & -- & -- & $\checkmark$ & -- & -- & -- & $\checkmark$ \\
deferral per_call & -- & -- & -- & $\checkmark$ & -- & -- & -- & $\checkmark$ \\
deferral per_run & -- & -- & -- & $\checkmark$ & -- & -- & -- & $\checkmark$ \\
burn time out of the loop & -- & -- & $\checkmark$ & $\checkmark$ & -- & -- & $\checkmark$ & $\checkmark$ \\
burn-time owner & loop & loop & constant & constant & loop & loop & optimiser & optimiser \\
input file ⁺ & committed & committed & committed & committed & committed & committed & lifted & lifted \\
output-time loop (MDA_Output) & n/a & n/a & n/a & n/a & upstream & upstream & none & none \\
\hline
\end{tabular}
```

### Table — how the three configurations differ

One row per configuration. Objective, design variables and constraints are the tally's problem-definition table (the runs' own stamps); `a → b` is the flat arms (`BR`, `B0`) → the arms with the burn time taken out of the MDA (`B1`, `B2`), which add the burn time as an iteration variable and its consistency constraint. The objective's variable and the cross-module coupling's variable are derived from the committed per-run artifact and the runs. Models is the committed node map's collapsed-DSM rows executed in a sweep (`units.dsm_rows.executed_in_a_sweep`), the constraints evaluation's row included (D40).

| Configuration | Models | Objective | Design var. | Constraints | Cross-module coupling |
|---|---:|---|---:|---:|---|
| Large tokamak (`tok`) | 52 | min. major radius (`rmajor`) | 20 → 21 | 26 → 27 | `t_plant_pulse_burn` |
| Low aspect ratio DEMO (`lad`) | 52 | max. pulse length (`t_plant_pulse_burn`) | 19 → 20 | 25 → 26 | `t_plant_pulse_burn` |
| Spherical tokamak (`st`) | 52 | max. fusion gain (`big_q_plasma`) | 14 | 18 | none (steady state) |

```latex
\begin{tabular}{l|c|l|c|c|l}
\hline
Configuration & Models & Objective & Design var. & Constraints & Cross-module coupling \\
\hline
Large tokamak (\texttt{tok}) & 52 & min. major radius (\texttt{rmajor}) & 20 $\rightarrow$ 21 & 26 $\rightarrow$ 27 & \texttt{t\_plant\_pulse\_burn} \\
Low aspect ratio DEMO (\texttt{lad}) & 52 & max. pulse length (\texttt{t\_plant\_pulse\_burn}) & 19 $\rightarrow$ 20 & 25 $\rightarrow$ 26 & \texttt{t\_plant\_pulse\_burn} \\
Spherical tokamak (\texttt{st}) & 52 & max. fusion gain (\texttt{big\_q\_plasma}) & 14 & 18 & none (steady state) \\
\hline
\end{tabular}
```

### Table `tab:phaseA_results` — phase A, module sweeps per evaluation

Mean sweeps of each module in one `call_models` evaluation over the n displaced-entry runs per arm; the ratio is of the means over the runs both arms of the pair finished — `A2/A1` on the pulsed configurations, `A2/A0` on `st` (D34).

**`tok`** (large_tokamak_nof, n = 25; pair A1 → A2)

| Module | AR | A0 | A1 | A2 | A2/A1 | A2/A1 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 5.0 | 5.1 | 5.1 | 3.0 | 0.59 | 0.60 [0.50, 0.75] |
| M2 | 5.0 | 5.1 | 5.1 | 5.2 | 1.01 | 1.00 [1.00, 1.25] |
| M3 | 5.0 | 5.1 | 5.1 | 2.0 | 0.39 | 0.40 [0.33, 0.50] |
| Feedforward | 5.0 | 5.1 | 5.1 | 1 | 0.20 | 0.20 [0.17, 0.25] |
| Post-processing | 5.0 | 5.1 | 5.1 | 1 | 0.20 | 0.20 [0.17, 0.25] |

**`lad`** (low_aspect_ratio_DEMO, n = 25; pair A1 → A2)

| Module | AR | A0 | A1 | A2 | A2/A1 | A2/A1 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 5.0 | 4.9 | 4.9 | 3.0 | 0.61 | 0.60 [0.60, 0.75] |
| M2 | 5.0 | 4.9 | 4.9 | 4.9 | 0.99 | 1.00 [0.80, 1.00] |
| M3 | 5.0 | 4.9 | 4.9 | 2.0 | 0.41 | 0.40 [0.40, 0.50] |
| Feedforward | 5.0 | 4.9 | 4.9 | 1 | 0.20 | 0.20 [0.20, 0.25] |
| Post-processing | 5.0 | 4.9 | 4.9 | 1 | 0.20 | 0.20 [0.20, 0.25] |

**`st`** (st_regression, n = 25; pair A0 → A2)

| Module | AR | A0 | A1 | A2 | A2/A0 | A2/A0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 4.9 | 4.8 | — | 3.0 | 0.62 | 0.60 [0.60, 0.75] |
| M2 | 4.9 | 4.8 | — | 4.8 | 1.00 | 1.00 [1.00, 1.00] |
| M3 | 4.9 | 4.8 | — | 2.9 | 0.60 | 0.60 [0.40, 0.75] |
| Feedforward | — | — | — | — | — | — |
| Post-processing | 4.9 | 4.8 | — | 1 | 0.21 | 0.20 [0.20, 0.25] |

```latex
\begin{tabular}{l|rrrr|rc}
\hline
Module & AR & A0 & A1 & A2 & A2/A1 (A2/A0 on st) & A2/A1 (A2/A0 on st) med [min, max] \\
\hline
\multicolumn{7}{l}{\texttt{tok} ($n = 25$, A2/A1)} \\
\hline
M1              & 5.0 & 5.1 & 5.1 & 3.0 & 0.59 & 0.60 [0.50, 0.75] \\
M2              & 5.0 & 5.1 & 5.1 & 5.2 & 1.01 & 1.00 [1.00, 1.25] \\
M3              & 5.0 & 5.1 & 5.1 & 2.0 & 0.39 & 0.40 [0.33, 0.50] \\
Feedforward     & 5.0 & 5.1 & 5.1 & 1 & 0.20 & 0.20 [0.17, 0.25] \\
Post-processing & 5.0 & 5.1 & 5.1 & 1 & 0.20 & 0.20 [0.17, 0.25] \\
\hline
\multicolumn{7}{l}{\texttt{lad} ($n = 25$, A2/A1)} \\
\hline
M1              & 5.0 & 4.9 & 4.9 & 3.0 & 0.61 & 0.60 [0.60, 0.75] \\
M2              & 5.0 & 4.9 & 4.9 & 4.9 & 0.99 & 1.00 [0.80, 1.00] \\
M3              & 5.0 & 4.9 & 4.9 & 2.0 & 0.41 & 0.40 [0.40, 0.50] \\
Feedforward     & 5.0 & 4.9 & 4.9 & 1 & 0.20 & 0.20 [0.20, 0.25] \\
Post-processing & 5.0 & 4.9 & 4.9 & 1 & 0.20 & 0.20 [0.20, 0.25] \\
\hline
\multicolumn{7}{l}{\texttt{st} ($n = 25$, A2/A0)} \\
\hline
M1              & 4.9 & 4.8 & -- & 3.0 & 0.62 & 0.60 [0.60, 0.75] \\
M2              & 4.9 & 4.8 & -- & 4.8 & 1.00 & 1.00 [1.00, 1.00] \\
M3              & 4.9 & 4.8 & -- & 2.9 & 0.60 & 0.60 [0.40, 0.75] \\
Feedforward     & -- & -- & -- & -- & -- & -- \\
Post-processing & 4.9 & 4.8 & -- & 1 & 0.21 & 0.20 [0.20, 0.25] \\
\hline
\end{tabular}
```

### Table `tab:phaseB_iterations` — phase B, optimiser iterations

Mean optimiser iterations per run, summed over the optimiser's retry attempts, over the n seeds on which every arm reached an accepted optimum; `B2/B0` is the ratio of the means.

| Configuration | n | BR | B0 | B1 | B2 | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|---:|
| `tok` | 22 | 7.8 | 7.8 | 7.8 | 7.8 | 0.99 | 1.00 [0.88, 1.14] |
| `lad` | 12 | 28.2 | 28.2 | 38.6 | 38.6 | 1.37 | 0.83 [0.13, 21.18] |
| `st` | 18 | 29.6 | 113.6 | — | 126.1 | 1.11 | 1.10 [0.88, 1.85] |

```latex
\begin{tabular}{l|rrrr|rc}
\hline
Configuration & BR & B0 & B1 & B2 & B2/B0 & B2/B0 med [min, max] \\
\hline
\texttt{tok} ($n = 22$) & 7.8 & 7.8 & 7.8 & 7.8 & 0.99 & 1.00 [0.88, 1.14] \\
\texttt{lad} ($n = 12$) & 28.2 & 28.2 & 38.6 & 38.6 & 1.37 & 0.83 [0.13, 21.18] \\
\texttt{st} ($n = 18$) & 29.6 & 113.6 & -- & 126.1 & 1.11 & 1.10 [0.88, 1.85] \\
\hline
\end{tabular}
```

### Table `tab:phaseB_results` — phase B, module sweeps per optimisation

Mean sweeps of each module over one whole optimisation, rounded to integers. Every attempt and the output path, which is architecture (MDA_Output's sweeps in `BR`/`B0`, none in `B1`, the deferred nodes' one execution in `B2`). The exit audit's one sweep of every node is the harness's accuracy instrument and is **subtracted** (1 per node, checked on each run against the record's `audit_node_calls`; D36). Over the n seeds on which every arm reached an accepted optimum; `B2/B0` is the ratio of the means.

**`tok`** (large_tokamak_nof, n = 22; pair B0 → B2)

| Module | BR | B0 | B1 | B2 | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 1977 | 1836 | 1877 | 973 | 0.53 | 0.53 [0.46, 0.62] |
| M2 | 1977 | 1836 | 1877 | 1732 | 0.94 | 0.95 [0.83, 1.10] |
| M3 | 1977 | 1836 | 1877 | 1084 | 0.59 | 0.59 [0.52, 0.69] |
| Feedforward | 1977 | 1836 | 1877 | 640 | 0.35 | 0.35 [0.31, 0.41] |
| Post-processing | 1977 | 1836 | 1877 | 1 | 0.00 | 0.00 [0.00, 0.00] |

**`lad`** (low_aspect_ratio_DEMO, n = 12; pair B0 → B2)

| Module | BR | B0 | B1 | B2 | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 7662 | 6582 | 9328 | 4958 | 0.75 | 0.45 [0.07, 12.26] |
| M2 | 7662 | 6582 | 9328 | 8556 | 1.30 | 0.78 [0.12, 21.00] |
| M3 | 7662 | 6582 | 9328 | 5364 | 0.81 | 0.49 [0.07, 13.13] |
| Feedforward | 7662 | 6582 | 9328 | 3199 | 0.49 | 0.29 [0.04, 7.84] |
| Post-processing | 7662 | 6582 | 9328 | 1 | 0.00 | 0.00 [0.00, 0.00] |

**`st`** (st_regression, n = 18; pair B0 → B2)

| Module | BR | B0 | B1 | B2 | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 5755 | 17213 | — | 12582 | 0.73 | 0.73 [0.56, 1.20] |
| M2 | 5755 | 17213 | — | 16094 | 0.93 | 0.93 [0.73, 1.51] |
| M3 | 5755 | 17213 | — | 14191 | 0.82 | 0.82 [0.63, 1.33] |
| Feedforward | — | — | — | — | — | — |
| Post-processing | 5755 | 17213 | — | 1 | 0.00 | 0.00 [0.00, 0.00] |

```latex
\begin{tabular}{l|cccc|cc}
\hline
Module & BR & B0 & B1 & B2 & B2/B0 & B2/B0 med [min, max] \\
\hline
\multicolumn{7}{l}{\texttt{tok} ($n = 22$, B2/B0)} \\
\hline
M1              & 1977 & 1836 & 1877 & 973 & 0.53 & 0.53 [0.46, 0.62] \\
M2              & 1977 & 1836 & 1877 & 1732 & 0.94 & 0.95 [0.83, 1.10] \\
M3              & 1977 & 1836 & 1877 & 1084 & 0.59 & 0.59 [0.52, 0.69] \\
Feedforward     & 1977 & 1836 & 1877 & 640 & 0.35 & 0.35 [0.31, 0.41] \\
Post-processing & 1977 & 1836 & 1877 & 1 & 0.00 & 0.00 [0.00, 0.00] \\
\hline
\multicolumn{7}{l}{\texttt{lad} ($n = 12$, B2/B0)} \\
\hline
M1              & 7662 & 6582 & 9328 & 4958 & 0.75 & 0.45 [0.07, 12.26] \\
M2              & 7662 & 6582 & 9328 & 8556 & 1.30 & 0.78 [0.12, 21.00] \\
M3              & 7662 & 6582 & 9328 & 5364 & 0.81 & 0.49 [0.07, 13.13] \\
Feedforward     & 7662 & 6582 & 9328 & 3199 & 0.49 & 0.29 [0.04, 7.84] \\
Post-processing & 7662 & 6582 & 9328 & 1 & 0.00 & 0.00 [0.00, 0.00] \\
\hline
\multicolumn{7}{l}{\texttt{st} ($n = 18$, B2/B0)} \\
\hline
M1              & 5755 & 17213 & -- & 12582 & 0.73 & 0.73 [0.56, 1.20] \\
M2              & 5755 & 17213 & -- & 16094 & 0.93 & 0.93 [0.73, 1.51] \\
M3              & 5755 & 17213 & -- & 14191 & 0.82 & 0.82 [0.63, 1.33] \\
Feedforward     & -- & -- & -- & -- & -- & -- \\
Post-processing & 5755 & 17213 & -- & 1 & 0.00 & 0.00 [0.00, 0.00] \\
\hline
\end{tabular}
```

## Appendix

### Tables — wall clock (plan §6)

**Context, never evidence (D33).** The wall-clock instrument of plan §6 (list item 9, driver change DR12, A101 (v5-timers-and-once)): observation-only timers in the driver copy (`PROCESS_ARCH_TIMERS=on`) per node, block loop, evaluation and run, harvested into every campaign record, with the launcher's independent wall beside. Excluded from every cell and measured separately: the exit-audit sweep, the state snapshots, the record assembly and the harness's set-up before the run. The rows are `harness/measurement/timing.py`'s; the repeatability stage (three repetitions at W = 1) and D38's validity check are that module's stages and their records say whether the campaign's timings may be printed here. The phase A rows are **warmed** (A102 (v5-campaign), plan §6): the evaluation child runs a discarded warm-up evaluation on the same entry, re-enters the entry bit-exact, resets the counters and times the measured evaluation, so the module rows carry no numba cache load; the fixed per-run term (process start to the warm-up's first evaluation) is stamped in every record and is not a row of the phase A table.

**Where these timings come from (D38).** The validity check (`--timing validity`, at `448d6bde`) found 0 of the campaign's timings of the repeatability seeds within the W = 1 repetitions' range and 0 outside. Every timing is the campaign's own, made with several workers at once and reported with its spread (D42, the user, 2026-09-30: the one-worker pass D38 would send no phase to is not run; the table below is the check's own rows); the worker counts the records are stamped with: W = 3. Phase B is over the count tables' seed set (every arm at an accepted optimum; D41).

**the validity check, per job** — One row per repeatability job (one seed per configuration and arm, both phases): Total over the three W = 1 repetitions as [min, max] with the spread (max − min over the median), the campaign's Total of the same job, and the campaign's Total over the repetitions' median. Phase A in ms per evaluation, phase B in s per optimisation.

| phase | configuration | arm | seed | W = 1 repetitions [min, max] | spread | campaign | campaign / W = 1 median | within |
|---|---|---|---:|---:|---:|---:|---:|---|
| A | `large_tokamak_nof` | AR | 1 | — | — | — | — | — |
| A | `large_tokamak_nof` | A0 | 1 | — | — | — | — | — |
| A | `large_tokamak_nof` | A1 | 1 | — | — | — | — | — |
| A | `large_tokamak_nof` | A2 | 1 | — | — | — | — | — |
| B | `large_tokamak_nof` | BR | 0 | — | — | — | — | — |
| B | `large_tokamak_nof` | B0 | 0 | — | — | — | — | — |
| B | `large_tokamak_nof` | B1 | 0 | — | — | — | — | — |
| B | `large_tokamak_nof` | B2 | 0 | — | — | — | — | — |
| A | `low_aspect_ratio_DEMO` | AR | 1 | — | — | — | — | — |
| A | `low_aspect_ratio_DEMO` | A0 | 1 | — | — | — | — | — |
| A | `low_aspect_ratio_DEMO` | A1 | 1 | — | — | — | — | — |
| A | `low_aspect_ratio_DEMO` | A2 | 1 | — | — | — | — | — |
| B | `low_aspect_ratio_DEMO` | BR | 0 | — | — | — | — | — |
| B | `low_aspect_ratio_DEMO` | B0 | 0 | — | — | — | — | — |
| B | `low_aspect_ratio_DEMO` | B1 | 0 | — | — | — | — | — |
| B | `low_aspect_ratio_DEMO` | B2 | 0 | — | — | — | — | — |
| A | `st_regression` | AR | 1 | — | — | — | — | — |
| A | `st_regression` | A0 | 1 | — | — | — | — | — |
| A | `st_regression` | A2 | 1 | — | — | — | — | — |
| B | `st_regression` | BR | 0 | — | — | — | — | — |
| B | `st_regression` | B0 | 0 | — | — | — | — | — |
| B | `st_regression` | B2 | 0 | — | — | — | — | — |

**phase A in wall clock, ms per evaluation** — Per configuration, arms as columns, ms per `call_models` evaluation: each module's own model time, the block loops' convergence test (read plus residual) and dispatch (the sweep body less its nodes and its test), the objective-and-constraints layer, the unattributed residual, and the evaluation's measured wall as Total; ratio of means and per-run median with [min, max] as the count tables. Harness-only costs — the exit-audit sweep, the state snapshots, the census hooks, the record assembly — are excluded from every cell (plan §6). Context, never evidence (D33).

**phase B in wall clock, s per optimisation** — As the phase A table, per whole optimisation in seconds, with the optimiser's own time (solve-phase wall less every evaluation) and the fixed per-run term (process start, imports, numba cache load, input parse, output writing, the once-per-run schedule derivation); Total is the run's wall less the harness-only costs (plan §6). **The module rows include one numba cache load per run**: a phase B run's first evaluation is not warmed (the fixed per-run term ends at its start), so its module rows carry the per-process cache load the warmed phase A records measure as warm-up less measured model time — a median of 0.25–0.40 s per run over the 11 configuration and arm rows, 0.2–3.3 % of the median module time per run of the arm's phase B twin, the same order in every arm (`--timing cache-load`, record at `448d6bde`).

**cost breakdown, phase B** — Per configuration and arm: seconds per optimisation and ms per evaluation with the share of the total. Whether the architecture changes the overhead is read off the B0 and B2 columns of the per-sweep rows, normalised per evaluation (plan §6).

**`large_tokamak_nof` — phase A in wall clock, ms per evaluation** (pair A2/A1, 25 pair(s); W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | AR (n=25) | A0 (n=25) | A1 (n=25) | A2 (n=25) | A2/A1 | A2/A1 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 19.11 | 16.93 | 17.91 | 9.63 | 0.54 | 0.56 [0.33, 0.82] |
| M2 | 20.13 | 17.93 | 18.34 | 16.75 | 0.91 | 0.96 [0.57, 1.56] |
| M3 | 4.10 | 3.54 | 3.77 | 1.34 | 0.35 | 0.38 [0.19, 0.66] |
| Feedforward | 0.06 | 0.05 | 0.05 | 0.01 | 0.32 | 0.35 [0.18, 0.52] |
| Post-processing | 1.20 | 0.98 | 1.02 | 0.31 | 0.30 | 0.31 [0.17, 0.42] |
| MDA convergence test | 0.26 | 4.31 | 4.56 | 5.08 | 1.11 | 1.15 [0.61, 2.02] |
| dispatch | 0.78 | 0.70 | 0.73 | 1.11 | 1.53 | 1.64 [1.00, 2.57] |
| objective and constraints | 0.99 | 0.21 | 0.21 | 0.20 | 0.97 | 1.04 [0.48, 1.88] |
| unattributed residual | 0.22 | 0.23 | 0.25 | 0.30 | 1.18 | 1.19 [0.64, 1.95] |
| Total | 46.85 | 44.95 | 46.93 | 34.81 | 0.74 | 0.79 [0.45, 1.24] |

**`large_tokamak_nof` — phase B in wall clock, s per optimisation** (pair B2/B0, 22 pair(s); W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | BR (n=22) | B0 (n=22) | B1 (n=22) | B2 (n=22) | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 7.06 | 6.85 | 6.87 | 3.99 | 0.58 | 0.58 [0.48, 0.71] |
| M2 | 7.02 | 6.72 | 6.78 | 6.63 | 0.99 | 0.98 [0.82, 1.20] |
| M3 | 1.47 | 1.39 | 1.39 | 0.86 | 0.62 | 0.61 [0.52, 0.77] |
| Feedforward | 0.02 | 0.02 | 0.02 | 0.01 | 0.40 | 0.40 [0.30, 0.52] |
| Post-processing | 0.41 | 0.38 | 0.38 | 0.00 | 0.00 | 0.00 [0.00, 0.00] |
| MDA convergence test | 0.08 | 1.80 | 1.80 | 2.66 | 1.47 | 1.46 [1.16, 1.86] |
| dispatch | 0.24 | 0.26 | 0.26 | 0.50 | 1.96 | 1.98 [1.45, 2.44] |
| objective and constraints | 0.36 | 0.12 | 0.13 | 0.22 | 1.79 | 1.85 [1.10, 2.30] |
| optimiser own time | 0.17 | 0.09 | 0.13 | 0.09 | 1.09 | 1.11 [0.91, 1.33] |
| fixed per run | 5.42 | 5.12 | 4.56 | 4.96 | 0.97 | 0.96 [0.84, 1.10] |
| unattributed residual | 0.03 | 0.09 | 0.09 | 0.15 | 1.74 | 1.80 [1.23, 2.66] |
| Total | 22.27 | 22.83 | 22.40 | 20.07 | 0.88 | 0.86 [0.75, 1.01] |

**`large_tokamak_nof` — cost breakdown, phase B** (s per optimisation, the per-unit figure, share of Total; W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | BR: s · per · share | B0: s · per · share | B1: s · per · share | B2: s · per · share |
|---|---|---|---|---|
| model evaluation (the modules summed) | 15.98 · 26.01 ms per evaluation · 71.7 % | 15.35 · 24.95 ms per evaluation · 67.2 % | 15.44 · 24.12 ms per evaluation · 68.8 % | 11.48 · 17.91 ms per evaluation · 57.2 % |
| MDA overhead per sweep: convergence test | 0.08 · 0.04 ms per sweep · 0.4 % | 1.80 · 0.98 ms per sweep · 7.9 % | 1.80 · 0.96 ms per sweep · 8.0 % | 2.66 · 0.60 ms per sweep · 13.2 % |
| MDA overhead per sweep: dispatch | 0.24 · 0.12 ms per sweep · 1.1 % | 0.26 · 0.14 ms per sweep · 1.1 % | 0.26 · 0.14 ms per sweep · 1.2 % | 0.50 · 0.11 ms per sweep · 2.5 % |
| optimiser overhead per iteration | 0.17 · 21.14 ms per iteration · 0.7 % | 0.09 · 11.08 ms per iteration · 0.4 % | 0.13 · 16.09 ms per iteration · 0.6 % | 0.09 · 12.13 ms per iteration · 0.5 % |
| fixed per run | 5.42 · 5.42 s per run · 24.3 % | 5.12 · 5.12 s per run · 22.5 % | 4.56 · 4.56 s per run · 20.5 % | 4.96 · 4.96 s per run · 24.8 % |
| Total | 22.27 · 36.27 ms per evaluation · 100.0 % | 22.83 · 37.16 ms per evaluation · 100.0 % | 22.40 · 35.03 ms per evaluation · 100.0 % | 20.07 · 31.34 ms per evaluation · 100.0 % |

**`low_aspect_ratio_DEMO` — phase A in wall clock, ms per evaluation** (pair A2/A1, 25 pair(s); W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | AR (n=25) | A0 (n=25) | A1 (n=25) | A2 (n=25) | A2/A1 | A2/A1 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 15.88 | 17.23 | 17.14 | 10.69 | 0.62 | 0.62 [0.29, 1.14] |
| M2 | 17.16 | 18.46 | 18.36 | 17.19 | 0.94 | 0.95 [0.50, 1.67] |
| M3 | 3.43 | 3.64 | 3.64 | 1.40 | 0.38 | 0.37 [0.19, 0.72] |
| Feedforward | 0.05 | 0.05 | 0.04 | 0.02 | 0.47 | 0.40 [0.25, 1.33] |
| Post-processing | 0.96 | 0.98 | 1.02 | 0.34 | 0.34 | 0.32 [0.19, 0.84] |
| MDA convergence test | 0.18 | 4.31 | 4.37 | 5.33 | 1.22 | 1.21 [0.61, 2.20] |
| dispatch | 0.63 | 0.66 | 0.69 | 1.15 | 1.67 | 1.66 [0.98, 2.88] |
| objective and constraints | 0.84 | 0.23 | 0.22 | 0.24 | 1.11 | 0.92 [0.64, 2.79] |
| unattributed residual | 0.18 | 0.23 | 0.24 | 0.32 | 1.36 | 1.24 [0.77, 2.68] |
| Total | 39.31 | 45.87 | 45.80 | 36.76 | 0.80 | 0.81 [0.44, 1.37] |

**`low_aspect_ratio_DEMO` — phase B in wall clock, s per optimisation** (pair B2/B0, 12 pair(s); W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | BR (n=12) | B0 (n=12) | B1 (n=12) | B2 (n=12) | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 26.92 | 24.38 | 34.22 | 18.73 | 0.77 | 0.49 [0.07, 12.63] |
| M2 | 28.41 | 25.60 | 35.96 | 32.77 | 1.28 | 0.81 [0.11, 21.38] |
| M3 | 5.77 | 5.14 | 7.27 | 4.14 | 0.80 | 0.51 [0.07, 13.98] |
| Feedforward | 0.07 | 0.07 | 0.09 | 0.04 | 0.48 | 0.33 [0.04, 9.90] |
| Post-processing | 1.59 | 1.40 | 1.97 | 0.00 | 0.00 | 0.00 [0.00, 0.00] |
| MDA convergence test | 0.32 | 6.85 | 9.52 | 12.59 | 1.84 | 1.22 [0.16, 32.52] |
| dispatch | 0.96 | 0.97 | 1.38 | 2.34 | 2.42 | 1.60 [0.21, 43.72] |
| objective and constraints | 1.39 | 0.47 | 0.68 | 0.68 | 1.47 | 0.92 [0.13, 26.04] |
| optimiser own time | 0.38 | 0.35 | 0.46 | 0.43 | 1.22 | 0.74 [0.11, 24.05] |
| fixed per run | 5.04 | 5.38 | 4.67 | 5.00 | 0.93 | 0.90 [0.80, 1.08] |
| unattributed residual | 0.22 | 0.43 | 0.60 | 0.80 | 1.87 | 1.24 [0.14, 41.68] |
| Total | 71.07 | 71.04 | 96.83 | 77.52 | 1.09 | 0.73 [0.12, 15.56] |

**`low_aspect_ratio_DEMO` — cost breakdown, phase B** (s per optimisation, the per-unit figure, share of Total; W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | BR: s · per · share | B0: s · per · share | B1: s · per · share | B2: s · per · share |
|---|---|---|---|---|
| model evaluation (the modules summed) | 62.76 · 28.70 ms per evaluation · 84.3 % | 56.60 · 25.55 ms per evaluation · 75.7 % | 79.51 · 25.36 ms per evaluation · 77.5 % | 55.67 · 17.93 ms per evaluation · 66.7 % |
| MDA overhead per sweep: convergence test | 0.32 · 0.04 ms per sweep · 0.4 % | 6.85 · 1.03 ms per sweep · 9.0 % | 9.52 · 1.04 ms per sweep · 9.3 % | 12.59 · 0.59 ms per sweep · 15.2 % |
| MDA overhead per sweep: dispatch | 0.96 · 0.13 ms per sweep · 1.3 % | 0.97 · 0.15 ms per sweep · 1.3 % | 1.38 · 0.15 ms per sweep · 1.3 % | 2.34 · 0.11 ms per sweep · 2.8 % |
| optimiser overhead per iteration | 0.38 · 15.91 ms per iteration · 0.6 % | 0.35 · 13.08 ms per iteration · 0.5 % | 0.46 · 13.15 ms per iteration · 0.5 % | 0.43 · 11.50 ms per iteration · 0.5 % |
| fixed per run | 5.04 · 5.04 s per run · 11.3 % | 5.38 · 5.38 s per run · 12.3 % | 4.67 · 4.67 s per run · 10.2 % | 5.00 · 5.00 s per run · 13.1 % |
| Total | 71.07 · 34.15 ms per evaluation · 100.0 % | 71.04 · 33.86 ms per evaluation · 100.0 % | 96.83 · 32.85 ms per evaluation · 100.0 % | 77.52 · 27.05 ms per evaluation · 100.0 % |

**`st_regression` — phase A in wall clock, ms per evaluation** (pair A2/A0, 25 pair(s); W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | AR (n=25) | A0 (n=25) | A1 (n=0) | A2 (n=25) | A2/A0 | A2/A0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 15.52 | 15.96 | — | 9.45 | 0.59 | 0.61 [0.37, 1.25] |
| M2 | 15.56 | 15.83 | — | 14.50 | 0.92 | 0.93 [0.63, 1.09] |
| M3 | 3.83 | 4.03 | — | 2.14 | 0.53 | 0.56 [0.20, 0.82] |
| Feedforward | 0.00 | 0.00 | — | 0.00 | — | — |
| Post-processing | 0.87 | 0.91 | — | 0.29 | 0.32 | 0.34 [0.19, 0.75] |
| MDA convergence test | 0.16 | 3.92 | — | 4.82 | 1.23 | 1.31 [0.73, 2.35] |
| dispatch | 0.57 | 0.59 | — | 1.00 | 1.69 | 1.76 [1.09, 3.12] |
| objective and constraints | 0.64 | 0.18 | — | 0.15 | 0.88 | 0.92 [0.42, 1.62] |
| unattributed residual | 0.14 | 0.21 | — | 0.29 | 1.39 | 1.45 [0.87, 2.91] |
| Total | 37.29 | 41.71 | — | 32.74 | 0.78 | 0.81 [0.53, 1.25] |

**`st_regression` — phase B in wall clock, s per optimisation** (pair B2/B0, 18 pair(s); W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | BR (n=18) | B0 (n=18) | B1 (n=0) | B2 (n=18) | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 20.92 | 62.86 | — | 46.89 | 0.75 | 0.74 [0.58, 1.27] |
| M2 | 22.26 | 67.03 | — | 63.29 | 0.94 | 0.95 [0.74, 1.58] |
| M3 | 5.20 | 15.46 | — | 12.73 | 0.82 | 0.82 [0.62, 1.34] |
| Feedforward | 0.00 | 0.00 | — | 0.00 | — | — |
| Post-processing | 1.24 | 3.65 | — | 0.00 | 0.00 | 0.00 [0.00, 0.00] |
| MDA convergence test | 0.23 | 16.88 | — | 26.43 | 1.57 | 1.54 [1.27, 2.66] |
| dispatch | 0.67 | 2.21 | — | 4.77 | 2.16 | 2.12 [1.73, 3.65] |
| objective and constraints | 0.87 | 1.11 | — | 1.22 | 1.09 | 1.11 [0.88, 1.90] |
| optimiser own time | 0.31 | 1.18 | — | 1.33 | 1.13 | 1.10 [0.87, 1.91] |
| fixed per run | 5.42 | 5.50 | — | 4.98 | 0.91 | 0.90 [0.80, 1.03] |
| unattributed residual | 0.14 | 1.20 | — | 1.84 | 1.53 | 1.53 [1.24, 2.58] |
| Total | 57.26 | 177.08 | — | 163.46 | 0.92 | 0.93 [0.73, 1.53] |

**`st_regression` — cost breakdown, phase B** (s per optimisation, the per-unit figure, share of Total; W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | BR: s · per · share | B0: s · per · share | B1: s · per · share | B2: s · per · share |
|---|---|---|---|---|
| model evaluation (the modules summed) | 49.62 · 28.57 ms per evaluation · 79.8 % | 149.01 · 21.96 ms per evaluation · 84.1 % | — | 122.91 · 16.30 ms per evaluation · 75.2 % |
| MDA overhead per sweep: convergence test | 0.23 · 0.04 ms per sweep · 0.4 % | 16.88 · 0.98 ms per sweep · 9.5 % | — | 26.43 · 0.46 ms per sweep · 16.2 % |
| MDA overhead per sweep: dispatch | 0.67 · 0.12 ms per sweep · 1.1 % | 2.21 · 0.13 ms per sweep · 1.2 % | — | 4.77 · 0.08 ms per sweep · 2.9 % |
| optimiser overhead per iteration | 0.31 · 10.73 ms per iteration · 0.5 % | 1.18 · 10.38 ms per iteration · 0.7 % | — | 1.33 · 10.50 ms per iteration · 0.8 % |
| fixed per run | 5.42 · 5.42 s per run · 16.7 % | 5.50 · 5.50 s per run · 3.2 % | — | 4.98 · 4.98 s per run · 3.1 % |
| Total | 57.26 · 36.02 ms per evaluation · 100.0 % | 177.08 · 26.11 ms per evaluation · 100.0 % | — | 163.46 · 21.69 ms per evaluation · 100.0 % |

**phase B in wall clock, s per optimisation — LaTeX** — The LaTeX form of the phase B wall-clock tables above, the 3 configurations in one `tabular` (n is each table's pair count): every cell the Markdown grid's own string, compared with it before writing — **0 mismatched of 258**; a doctored cell caught: **yes**. Wall clock is context, never evidence (D33).

```latex
\begin{tabular}{l|cccc|cc}
\hline
Row & BR & B0 & B1 & B2 & B2/B0 & B2/B0 med [min, max] \\
\hline
\multicolumn{7}{l}{\texttt{tok} ($n = 22$)} \\
\hline
M1                        & 7.06 & 6.85 & 6.87 & 3.99 & 0.58 & 0.58 [0.48, 0.71] \\
M2                        & 7.02 & 6.72 & 6.78 & 6.63 & 0.99 & 0.98 [0.82, 1.20] \\
M3                        & 1.47 & 1.39 & 1.39 & 0.86 & 0.62 & 0.61 [0.52, 0.77] \\
Feedforward               & 0.02 & 0.02 & 0.02 & 0.01 & 0.40 & 0.40 [0.30, 0.52] \\
Post-processing           & 0.41 & 0.38 & 0.38 & 0.00 & 0.00 & 0.00 [0.00, 0.00] \\
MDA convergence test      & 0.08 & 1.80 & 1.80 & 2.66 & 1.47 & 1.46 [1.16, 1.86] \\
dispatch                  & 0.24 & 0.26 & 0.26 & 0.50 & 1.96 & 1.98 [1.45, 2.44] \\
objective and constraints & 0.36 & 0.12 & 0.13 & 0.22 & 1.79 & 1.85 [1.10, 2.30] \\
optimiser own time        & 0.17 & 0.09 & 0.13 & 0.09 & 1.09 & 1.11 [0.91, 1.33] \\
fixed per run             & 5.42 & 5.12 & 4.56 & 4.96 & 0.97 & 0.96 [0.84, 1.10] \\
unattributed residual     & 0.03 & 0.09 & 0.09 & 0.15 & 1.74 & 1.80 [1.23, 2.66] \\
\hline
Total                     & 22.27 & 22.83 & 22.40 & 20.07 & 0.88 & 0.86 [0.75, 1.01] \\
\hline
\multicolumn{7}{l}{\texttt{lad} ($n = 12$)} \\
\hline
M1                        & 26.92 & 24.38 & 34.22 & 18.73 & 0.77 & 0.49 [0.07, 12.63] \\
M2                        & 28.41 & 25.60 & 35.96 & 32.77 & 1.28 & 0.81 [0.11, 21.38] \\
M3                        & 5.77 & 5.14 & 7.27 & 4.14 & 0.80 & 0.51 [0.07, 13.98] \\
Feedforward               & 0.07 & 0.07 & 0.09 & 0.04 & 0.48 & 0.33 [0.04, 9.90] \\
Post-processing           & 1.59 & 1.40 & 1.97 & 0.00 & 0.00 & 0.00 [0.00, 0.00] \\
MDA convergence test      & 0.32 & 6.85 & 9.52 & 12.59 & 1.84 & 1.22 [0.16, 32.52] \\
dispatch                  & 0.96 & 0.97 & 1.38 & 2.34 & 2.42 & 1.60 [0.21, 43.72] \\
objective and constraints & 1.39 & 0.47 & 0.68 & 0.68 & 1.47 & 0.92 [0.13, 26.04] \\
optimiser own time        & 0.38 & 0.35 & 0.46 & 0.43 & 1.22 & 0.74 [0.11, 24.05] \\
fixed per run             & 5.04 & 5.38 & 4.67 & 5.00 & 0.93 & 0.90 [0.80, 1.08] \\
unattributed residual     & 0.22 & 0.43 & 0.60 & 0.80 & 1.87 & 1.24 [0.14, 41.68] \\
\hline
Total                     & 71.07 & 71.04 & 96.83 & 77.52 & 1.09 & 0.73 [0.12, 15.56] \\
\hline
\multicolumn{7}{l}{\texttt{st} ($n = 18$)} \\
\hline
M1                        & 20.92 & 62.86 & -- & 46.89 & 0.75 & 0.74 [0.58, 1.27] \\
M2                        & 22.26 & 67.03 & -- & 63.29 & 0.94 & 0.95 [0.74, 1.58] \\
M3                        & 5.20 & 15.46 & -- & 12.73 & 0.82 & 0.82 [0.62, 1.34] \\
Feedforward               & 0.00 & 0.00 & -- & 0.00 & -- & -- \\
Post-processing           & 1.24 & 3.65 & -- & 0.00 & 0.00 & 0.00 [0.00, 0.00] \\
MDA convergence test      & 0.23 & 16.88 & -- & 26.43 & 1.57 & 1.54 [1.27, 2.66] \\
dispatch                  & 0.67 & 2.21 & -- & 4.77 & 2.16 & 2.12 [1.73, 3.65] \\
objective and constraints & 0.87 & 1.11 & -- & 1.22 & 1.09 & 1.11 [0.88, 1.90] \\
optimiser own time        & 0.31 & 1.18 & -- & 1.33 & 1.13 & 1.10 [0.87, 1.91] \\
fixed per run             & 5.42 & 5.50 & -- & 4.98 & 0.91 & 0.90 [0.80, 1.03] \\
unattributed residual     & 0.14 & 1.20 & -- & 1.84 & 1.53 & 1.53 [1.24, 2.58] \\
\hline
Total                     & 57.26 & 177.08 & -- & 163.46 & 0.92 & 0.93 [0.73, 1.53] \\
\hline
\end{tabular}
```

### Table — per-arm success

Per configuration and arm: the starts offered, the accepted optima (`status == ok`, `ifail == 1`), the other starts by outcome class, the one seed set every phase B table is over, and the starts lost to this arm alone. Reported, no expectation (plan §5 B5; item 3 as reduced). The tally's `per-arm success` table, republished.

**`tok`** (large_tokamak_nof)

| arm | offered | accepted | crashed (RuntimeError) | lost_another_arm_accepted | seed_set | seeds_not_accepted | lost_seeds |
|---|---|---|---|---|---|---|---|
| BR | 25 | 22 | 3 | 0 | 22 | crashed (RuntimeError): 5, 20, 21 | — |
| B0 | 25 | 22 | 3 | 0 | 22 | crashed (RuntimeError): 5, 20, 21 | — |
| B1 | 25 | 22 | 3 | 0 | 22 | crashed (RuntimeError): 5, 20, 21 | — |
| B2 | 25 | 22 | 3 | 0 | 22 | crashed (RuntimeError): 5, 20, 21 | — |

**`lad`** (low_aspect_ratio_DEMO)

| arm | offered | accepted | finished, ifail = 5 | crashed (RuntimeError) | lost_another_arm_accepted | seed_set | seeds_not_accepted | lost_seeds |
|---|---|---|---|---|---|---|---|---|
| BR | 25 | 12 | 11 | 2 | 0 | 12 | finished, ifail = 5: 2, 4, 7, 8, 14, 16, 17, 20, 22, 23, 24; crashed (RuntimeError): 3, 21 | — |
| B0 | 25 | 12 | 11 | 2 | 0 | 12 | finished, ifail = 5: 2, 4, 7, 8, 14, 16, 17, 20, 22, 23, 24; crashed (RuntimeError): 3, 21 | — |
| B1 | 25 | 12 | 11 | 2 | 0 | 12 | finished, ifail = 5: 2, 4, 7, 8, 14, 16, 17, 20, 22, 23, 24; crashed (RuntimeError): 3, 21 | — |
| B2 | 25 | 12 | 11 | 2 | 0 | 12 | finished, ifail = 5: 2, 4, 7, 8, 14, 16, 17, 20, 22, 23, 24; crashed (RuntimeError): 3, 21 | — |

**`st`** (st_regression)

| arm | offered | accepted | finished, ifail = 2 | finished, ifail = 5 | lost_another_arm_accepted | seed_set | seeds_not_accepted | lost_seeds |
|---|---|---|---|---|---|---|---|---|
| BR | 25 | 24 | 0 | 1 | 0 | 18 | finished, ifail = 5: 17 | — |
| B0 | 25 | 21 | 3 | 1 | 3 | 18 | finished, ifail = 2: 3, 5, 9; finished, ifail = 5: 17 | 3, 5, 9 |
| B2 | 25 | 18 | 3 | 4 | 6 | 18 | finished, ifail = 2: 3, 5, 9; finished, ifail = 5: 1, 10, 15, 17 | 1, 3, 5, 9, 10, 15 |

### Table — verification

One row per check of plan §8, in its order. A gate's verdict is read from its record through the `gate_table` stage record, which this generator refuses when the verdict records have been re-made, removed or added to since the stage ran; `not pressed` is a gate with no verdict record (a declared placeholder that refuses, or one never pressed) or a rule that is not yet a construction. A verdict is PASS only with every tooth tripped.

*the gate_table stage record read 29 record(s) at ['b484d8073e6d0c2fb34a0c9be9b4530eef5332c9'], and every one of them is byte-identical to what is on disk now*

| check | plan | verdict | detail |
|---|---|---|---|
| physics frozen | G0 | **PASS** | `g0prime` at `b484d807`: 1 of 77 mismatched; 4/4 teeth |
| switch neutrality | G1 | **PASS** | `switch_neutrality` at `b484d807`: 0 of 54973 mismatched; 10/10 teeth |
| matched accuracy — whole-state audit at 0 components above τ | A1 | **PASS** | `tok` A2/A1: similarity PASS, runs with a component ≥ τ A1 0 / A2 0 → **PASS**; `lad` A2/A1: similarity PASS, runs with a component ≥ τ A1 0 / A2 0 → **PASS**; `st` A2/A0: similarity PASS, runs with a component ≥ τ A0 0 / A2 0 → **PASS** (whole-state statistic, D36; the second half of the rule is the count column) |
| fixed-point distance between arms | A2 | **reported, no rule** | the tally's fixed-point distance table (plan §5 A2) |
| same optimum, attributed where it fails | B1 | **PASS tok, st · FAIL lad** | `tok` B0 → B1 PASS, B0 → B2 PASS (objf p90 4.6e-11 ≤ 1.0e-06; 0 hops of 22); `lad` B0 → B1 FAIL, B0 → B2 FAIL at p90 (objf p90 3.1e-04 > 1.0e-06): 4 hops of 12 (2 across clusters; seeds 1*, 10*, 11, 13), entering at B0 → B1 (the lift) 4 of 4; B1 → B2 (the partition) adds none: objf median 3.1e-14, p90 7.4e-14, same path on 12 of 12; the yardstick BR → B0 also hops on 0 of 4 of these seeds; `st` B0 → B2 PASS (objf p90 1.7e-11 ≤ 1.0e-06; 0 hops of 18) (hop: objective difference above the floor; * = a retried arm; the tally's `same optimum by rung` table, plan §5 B1) |
| entry pairing | G6 | **PASS** | `entry_and_warm` at `b484d807`: 0 of 6717 mismatched; 3/3 teeth |
| arm composition | G5 | **FAIL** | `switch_composition` at `b484d807`: 3 of 159 mismatched; 4/4 teeth |
| output-path equivalence | G9 | **PASS** | `output_path` at `b484d807`: 0 of 3879 mismatched; 5/5 teeth |
| the test set's teeth | GT | **FAIL** | `test_set` at `b484d807`: 0 of 13424 mismatched; 3/4 teeth |

