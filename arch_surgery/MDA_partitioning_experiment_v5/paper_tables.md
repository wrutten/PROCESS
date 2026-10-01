# Paper tables — Case 2: PROCESS

> **Document status** — **GENERATED, never hand-edited.** Written whole by `harness/measurement/paper_tables.py` (`experiment_runner.py --paper-tables write`) from the campaign's run records and the stage records, and compared whole by `--paper-tables check`, which refuses when this file and the records disagree. The one document of V5 list item 10: the main-text tables of `Structuring-fusion-MDAO-with-DSMs/3 results.tex` and the appendix tables of the V5 plan §8; each table is a Markdown grid and, where the paper prints it, LaTeX rows for the paper's `tabular` body.

*Over the **campaign** population — 553 run records at `6221af70`, `f4a75f8e`; sources `campaign_displaced` (phase A) and `campaign_optimisation` (phase B); the exit audit at position(s) `after_single_evaluation`, `entry_to_write_output_files` on the ruler(s) `frozen`.*

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
| stopping rule | objf/conf | feedback couplings @ τ = 1e-08 | feedback couplings @ τ = 1e-08 | feedback couplings @ τ = 1e-08 per block | objf/conf | feedback couplings @ τ = 1e-08 | feedback couplings @ τ = 1e-08 | feedback couplings @ τ = 1e-08 per block |
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
stopping rule & objf/conf & feedback couplings @ $\tau$ = 1e-08 & feedback couplings @ $\tau$ = 1e-08 & feedback couplings @ $\tau$ = 1e-08 per block & objf/conf & feedback couplings @ $\tau$ = 1e-08 & feedback couplings @ $\tau$ = 1e-08 & feedback couplings @ $\tau$ = 1e-08 per block \\
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
| M1 | 5.0 | 5.9 | 5.9 | 3.0 | 0.51 | 0.50 [0.43, 0.60] |
| M2 | 5.0 | 5.9 | 5.9 | 5.9 | 1.00 | 1.00 [1.00, 1.00] |
| M3 | 5.0 | 5.9 | 5.9 | 2.0 | 0.34 | 0.33 [0.29, 0.40] |
| Feedforward | 5.0 | 5.9 | 5.9 | 1 | 0.17 | 0.17 [0.14, 0.20] |
| Post-processing | 5.0 | 5.9 | 5.9 | 1 | 0.17 | 0.17 [0.14, 0.20] |

**`lad`** (low_aspect_ratio_DEMO, n = 25; pair A1 → A2)

| Module | AR | A0 | A1 | A2 | A2/A1 | A2/A1 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 5.0 | 5.0 | 5.0 | 3.0 | 0.60 | 0.60 [0.60, 0.60] |
| M2 | 5.0 | 5.0 | 5.0 | 5.0 | 1.00 | 1.00 [1.00, 1.00] |
| M3 | 5.0 | 5.0 | 5.0 | 2.0 | 0.40 | 0.40 [0.40, 0.40] |
| Feedforward | 5.0 | 5.0 | 5.0 | 1 | 0.20 | 0.20 [0.20, 0.20] |
| Post-processing | 5.0 | 5.0 | 5.0 | 1 | 0.20 | 0.20 [0.20, 0.20] |

**`st`** (st_regression, n = 25; pair A0 → A2)

| Module | AR | A0 | A1 | A2 | A2/A0 | A2/A0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 4.9 | 6.0 | — | 3.0 | 0.50 | 0.50 [0.50, 0.60] |
| M2 | 4.9 | 6.0 | — | 6.0 | 1.00 | 1.00 [1.00, 1.00] |
| M3 | 4.9 | 6.0 | — | 3.0 | 0.50 | 0.50 [0.50, 0.60] |
| Feedforward | — | — | — | — | — | — |
| Post-processing | 4.9 | 6.0 | — | 1 | 0.17 | 0.17 [0.17, 0.20] |

```latex
\begin{tabular}{l|rrrr|rc}
\hline
Module & AR & A0 & A1 & A2 & A2/A1 (A2/A0 on st) & A2/A1 (A2/A0 on st) med [min, max] \\
\hline
\multicolumn{7}{l}{\texttt{tok} ($n = 25$, A2/A1)} \\
\hline
M1              & 5.0 & 5.9 & 5.9 & 3.0 & 0.51 & 0.50 [0.43, 0.60] \\
M2              & 5.0 & 5.9 & 5.9 & 5.9 & 1.00 & 1.00 [1.00, 1.00] \\
M3              & 5.0 & 5.9 & 5.9 & 2.0 & 0.34 & 0.33 [0.29, 0.40] \\
Feedforward     & 5.0 & 5.9 & 5.9 & 1 & 0.17 & 0.17 [0.14, 0.20] \\
Post-processing & 5.0 & 5.9 & 5.9 & 1 & 0.17 & 0.17 [0.14, 0.20] \\
\hline
\multicolumn{7}{l}{\texttt{lad} ($n = 25$, A2/A1)} \\
\hline
M1              & 5.0 & 5.0 & 5.0 & 3.0 & 0.60 & 0.60 [0.60, 0.60] \\
M2              & 5.0 & 5.0 & 5.0 & 5.0 & 1.00 & 1.00 [1.00, 1.00] \\
M3              & 5.0 & 5.0 & 5.0 & 2.0 & 0.40 & 0.40 [0.40, 0.40] \\
Feedforward     & 5.0 & 5.0 & 5.0 & 1 & 0.20 & 0.20 [0.20, 0.20] \\
Post-processing & 5.0 & 5.0 & 5.0 & 1 & 0.20 & 0.20 [0.20, 0.20] \\
\hline
\multicolumn{7}{l}{\texttt{st} ($n = 25$, A2/A0)} \\
\hline
M1              & 4.9 & 6.0 & -- & 3.0 & 0.50 & 0.50 [0.50, 0.60] \\
M2              & 4.9 & 6.0 & -- & 6.0 & 1.00 & 1.00 [1.00, 1.00] \\
M3              & 4.9 & 6.0 & -- & 3.0 & 0.50 & 0.50 [0.50, 0.60] \\
Feedforward     & -- & -- & -- & -- & -- & -- \\
Post-processing & 4.9 & 6.0 & -- & 1 & 0.17 & 0.17 [0.17, 0.20] \\
\hline
\end{tabular}
```

### Table `tab:phaseB_iterations` — phase B, optimiser iterations

Mean optimiser iterations per run, summed over the optimiser's retry attempts, over the n seeds on which every arm reached an accepted optimum; `B2/B0` is the ratio of the means.

| Configuration | n | BR | B0 | B1 | B2 | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|---:|
| `tok` | 22 | 7.8 | 7.8 | 7.8 | 7.8 | 0.99 | 1.00 [0.88, 1.14] |
| `lad` | 12 | 28.2 | 28.2 | 38.6 | 38.6 | 1.37 | 0.83 [0.13, 21.18] |
| `st` | 20 | 29.5 | 20.8 | — | 49.9 | 2.40 | 2.21 [0.56, 5.21] |

```latex
\begin{tabular}{l|rrrr|rc}
\hline
Configuration & BR & B0 & B1 & B2 & B2/B0 & B2/B0 med [min, max] \\
\hline
\texttt{tok} ($n = 22$) & 7.8 & 7.8 & 7.8 & 7.8 & 0.99 & 1.00 [0.88, 1.14] \\
\texttt{lad} ($n = 12$) & 28.2 & 28.2 & 38.6 & 38.6 & 1.37 & 0.83 [0.13, 21.18] \\
\texttt{st} ($n = 20$) & 29.5 & 20.8 & -- & 49.9 & 2.40 & 2.21 [0.56, 5.21] \\
\hline
\end{tabular}
```

### Table `tab:phaseB_results` — phase B, module sweeps per optimisation

Mean sweeps of each module over one whole optimisation, rounded to integers. Every attempt and the output path, which is architecture (MDA_Output's sweeps in `BR`/`B0`, none in `B1`, the deferred nodes' one execution in `B2`). The exit audit's one sweep of every node is the harness's accuracy instrument and is **subtracted** (1 per node, checked on each run against the record's `audit_node_calls`; D36). Over the n seeds on which every arm reached an accepted optimum; `B2/B0` is the ratio of the means.

**`tok`** (large_tokamak_nof, n = 22; pair B0 → B2)

| Module | BR | B0 | B1 | B2 | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 1977 | 2116 | 2055 | 1147 | 0.54 | 0.55 [0.48, 0.63] |
| M2 | 1977 | 2116 | 2055 | 1866 | 0.88 | 0.89 [0.77, 1.02] |
| M3 | 1977 | 2116 | 2055 | 1146 | 0.54 | 0.54 [0.47, 0.63] |
| Feedforward | 1977 | 2116 | 2055 | 640 | 0.30 | 0.30 [0.27, 0.35] |
| Post-processing | 1977 | 2116 | 2055 | 1 | 0.00 | 0.00 [0.00, 0.00] |

**`lad`** (low_aspect_ratio_DEMO, n = 12; pair B0 → B2)

| Module | BR | B0 | B1 | B2 | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 7662 | 7623 | 10124 | 5513 | 0.72 | 0.43 [0.07, 11.77] |
| M2 | 7662 | 7623 | 10124 | 9216 | 1.21 | 0.73 [0.11, 19.43] |
| M3 | 7662 | 7623 | 10124 | 5888 | 0.77 | 0.47 [0.07, 12.41] |
| Feedforward | 7662 | 7623 | 10124 | 3199 | 0.42 | 0.25 [0.04, 6.76] |
| Post-processing | 7662 | 7623 | 10124 | 1 | 0.00 | 0.00 [0.00, 0.00] |

**`st`** (st_regression, n = 20; pair B0 → B2)

| Module | BR | B0 | B1 | B2 | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 5734 | 3895 | — | 5302 | 1.36 | 1.25 [0.31, 2.93] |
| M2 | 5734 | 3895 | — | 7873 | 2.02 | 1.87 [0.45, 4.34] |
| M3 | 5734 | 3895 | — | 5608 | 1.44 | 1.34 [0.33, 3.11] |
| Feedforward | — | — | — | — | — | — |
| Post-processing | 5734 | 3895 | — | 1 | 0.00 | 0.00 [0.00, 0.00] |

```latex
\begin{tabular}{l|cccc|cc}
\hline
Module & BR & B0 & B1 & B2 & B2/B0 & B2/B0 med [min, max] \\
\hline
\multicolumn{7}{l}{\texttt{tok} ($n = 22$, B2/B0)} \\
\hline
M1              & 1977 & 2116 & 2055 & 1147 & 0.54 & 0.55 [0.48, 0.63] \\
M2              & 1977 & 2116 & 2055 & 1866 & 0.88 & 0.89 [0.77, 1.02] \\
M3              & 1977 & 2116 & 2055 & 1146 & 0.54 & 0.54 [0.47, 0.63] \\
Feedforward     & 1977 & 2116 & 2055 & 640 & 0.30 & 0.30 [0.27, 0.35] \\
Post-processing & 1977 & 2116 & 2055 & 1 & 0.00 & 0.00 [0.00, 0.00] \\
\hline
\multicolumn{7}{l}{\texttt{lad} ($n = 12$, B2/B0)} \\
\hline
M1              & 7662 & 7623 & 10124 & 5513 & 0.72 & 0.43 [0.07, 11.77] \\
M2              & 7662 & 7623 & 10124 & 9216 & 1.21 & 0.73 [0.11, 19.43] \\
M3              & 7662 & 7623 & 10124 & 5888 & 0.77 & 0.47 [0.07, 12.41] \\
Feedforward     & 7662 & 7623 & 10124 & 3199 & 0.42 & 0.25 [0.04, 6.76] \\
Post-processing & 7662 & 7623 & 10124 & 1 & 0.00 & 0.00 [0.00, 0.00] \\
\hline
\multicolumn{7}{l}{\texttt{st} ($n = 20$, B2/B0)} \\
\hline
M1              & 5734 & 3895 & -- & 5302 & 1.36 & 1.25 [0.31, 2.93] \\
M2              & 5734 & 3895 & -- & 7873 & 2.02 & 1.87 [0.45, 4.34] \\
M3              & 5734 & 3895 & -- & 5608 & 1.44 & 1.34 [0.33, 3.11] \\
Feedforward     & -- & -- & -- & -- & -- & -- \\
Post-processing & 5734 & 3895 & -- & 1 & 0.00 & 0.00 [0.00, 0.00] \\
\hline
\end{tabular}
```

## Appendix

### Tables — wall clock (plan §6)

**Context, never evidence (D33).** The wall-clock instrument of plan §6 (list item 9, driver change DR12, A101 (v5-timers-and-once)): observation-only timers in the driver copy (`PROCESS_ARCH_TIMERS=on`) per node, block loop, evaluation and run, harvested into every campaign record, with the launcher's independent wall beside. Excluded from every cell and measured separately: the exit-audit sweep, the state snapshots, the record assembly and the harness's set-up before the run. The rows are `harness/measurement/timing.py`'s; the repeatability stage (three repetitions at W = 1) and D38's validity check are that module's stages and their records say whether the campaign's timings may be printed here. The phase A rows are **warmed** (A102 (v5-campaign), plan §6): the evaluation child runs a discarded warm-up evaluation on the same entry, re-enters the entry bit-exact, resets the counters and times the measured evaluation, so the module rows carry no numba cache load; the fixed per-run term (process start to the warm-up's first evaluation) is stamped in every record and is not a row of the phase A table.

**Where these timings come from (D38).** The validity check (`--timing validity`, at `75b9e9d4`) found 1 of the campaign's timings of the repeatability seeds within the W = 1 repetitions' range and 21 outside. Every timing is the campaign's own, made with several workers at once and reported with its spread (D42, the user, 2026-09-30: the one-worker pass D38 would send phase A and B to is not run; the table below is the check's own rows); the worker counts the records are stamped with: W = 3, 4. Phase B is over the count tables' seed set (every arm at an accepted optimum; D41).

**the validity check, per job** — One row per repeatability job (one seed per configuration and arm, both phases): Total over the three W = 1 repetitions as [min, max] with the spread (max − min over the median), the campaign's Total of the same job, and the campaign's Total over the repetitions' median. Phase A in ms per evaluation, phase B in s per optimisation.

| phase | configuration | arm | seed | W = 1 repetitions [min, max] | spread | campaign | campaign / W = 1 median | within |
|---|---|---|---:|---:|---:|---:|---:|---|
| A | `large_tokamak_nof` | AR | 1 | [36.31, 38.40] | 5.6 % | 46.68 | 1.25 | no |
| A | `large_tokamak_nof` | A0 | 1 | [52.77, 53.71] | 1.7 % | 56.25 | 1.05 | no |
| A | `large_tokamak_nof` | A1 | 1 | [52.39, 62.82] | 19.8 % | 67.15 | 1.28 | no |
| A | `large_tokamak_nof` | A2 | 1 | [37.15, 38.93] | 4.8 % | 42.29 | 1.14 | no |
| B | `large_tokamak_nof` | BR | 0 | [17.86, 17.96] | 0.6 % | 24.95 | 1.39 | no |
| B | `large_tokamak_nof` | B0 | 0 | [20.01, 20.74] | 3.6 % | 27.35 | 1.36 | no |
| B | `large_tokamak_nof` | B1 | 0 | [19.24, 19.42] | 0.9 % | 27.45 | 1.41 | no |
| B | `large_tokamak_nof` | B2 | 0 | [16.07, 16.09] | 0.2 % | 22.77 | 1.42 | no |
| A | `low_aspect_ratio_DEMO` | AR | 1 | [35.27, 38.05] | 7.7 % | 42.11 | 1.16 | no |
| A | `low_aspect_ratio_DEMO` | A0 | 1 | [39.54, 41.07] | 3.9 % | 44.96 | 1.13 | no |
| A | `low_aspect_ratio_DEMO` | A1 | 1 | [39.37, 41.39] | 5.1 % | 46.09 | 1.15 | no |
| A | `low_aspect_ratio_DEMO` | A2 | 1 | [32.00, 33.55] | 4.7 % | 36.25 | 1.09 | no |
| B | `low_aspect_ratio_DEMO` | BR | 0 | [33.31, 33.80] | 1.5 % | 46.70 | 1.39 | no |
| B | `low_aspect_ratio_DEMO` | B0 | 0 | [35.58, 36.10] | 1.5 % | 52.06 | 1.46 | no |
| B | `low_aspect_ratio_DEMO` | B1 | 0 | [28.10, 28.53] | 1.5 % | 42.17 | 1.49 | no |
| B | `low_aspect_ratio_DEMO` | B2 | 0 | [23.07, 23.37] | 1.3 % | 31.93 | 1.37 | no |
| A | `st_regression` | AR | 1 | [34.06, 39.25] | 14.7 % | 39.89 | 1.13 | no |
| A | `st_regression` | A0 | 1 | [44.72, 48.68] | 8.6 % | 52.88 | 1.15 | no |
| A | `st_regression` | A2 | 1 | [34.33, 38.50] | 11.7 % | 37.61 | 1.05 | yes |
| B | `st_regression` | BR | 0 | [17.12, 17.84] | 4.1 % | 21.29 | 1.21 | no |
| B | `st_regression` | B0 | 0 | [18.20, 18.29] | 0.5 % | 24.54 | 1.34 | no |
| B | `st_regression` | B2 | 0 | [45.86, 46.20] | 0.8 % | 58.35 | 1.27 | no |

**phase A in wall clock, ms per evaluation** — Per configuration, arms as columns, ms per `call_models` evaluation: each module's own model time, the block loops' convergence test (read plus residual) and dispatch (the sweep body less its nodes and its test), the objective-and-constraints layer, the unattributed residual, and the evaluation's measured wall as Total; ratio of means and per-run median with [min, max] as the count tables. Harness-only costs — the exit-audit sweep, the state snapshots, the census hooks, the record assembly — are excluded from every cell (plan §6). Context, never evidence (D33).

**phase B in wall clock, s per optimisation** — As the phase A table, per whole optimisation in seconds, with the optimiser's own time (solve-phase wall less every evaluation) and the fixed per-run term (process start, imports, numba cache load, input parse, output writing, the once-per-run schedule derivation); Total is the run's wall less the harness-only costs (plan §6). **The module rows include one numba cache load per run**: a phase B run's first evaluation is not warmed (the fixed per-run term ends at its start), so its module rows carry the per-process cache load the warmed phase A records measure as warm-up less measured model time — a median of 0.26–0.44 s per run over the 11 configuration and arm rows, 0.6–3.3 % of the median module time per run of the arm's phase B twin, the same order in every arm (`--timing cache-load`, record at `c2295511`).

**cost breakdown, phase B** — Per configuration and arm: seconds per optimisation and ms per evaluation with the share of the total. Whether the architecture changes the overhead is read off the B0 and B2 columns of the per-sweep rows, normalised per evaluation (plan §6).

**`large_tokamak_nof` — phase A in wall clock, ms per evaluation** (pair A2/A1, 25 pair(s); W = 3, 4 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | AR (n=25) | A0 (n=25) | A1 (n=25) | A2 (n=25) | A2/A1 | A2/A1 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 21.03 | 21.29 | 22.64 | 10.91 | 0.48 | 0.49 [0.25, 0.99] |
| M2 | 22.68 | 22.53 | 23.73 | 21.54 | 0.91 | 0.92 [0.56, 1.47] |
| M3 | 4.91 | 4.55 | 4.92 | 1.51 | 0.31 | 0.30 [0.15, 0.65] |
| Feedforward | 0.09 | 0.07 | 0.06 | 0.02 | 0.30 | 0.28 [0.14, 0.69] |
| Post-processing | 1.37 | 1.23 | 1.37 | 0.36 | 0.26 | 0.25 [0.14, 0.55] |
| MDA convergence test | 0.30 | 5.70 | 5.97 | 6.66 | 1.12 | 1.05 [0.70, 2.00] |
| dispatch | 1.04 | 0.89 | 0.95 | 1.37 | 1.43 | 1.40 [0.87, 2.68] |
| objective and constraints | 1.13 | 0.23 | 0.25 | 0.22 | 0.85 | 0.89 [0.41, 1.69] |
| unattributed residual | 0.34 | 0.30 | 0.33 | 0.37 | 1.12 | 1.10 [0.71, 2.32] |
| Total | 52.89 | 56.89 | 60.31 | 43.03 | 0.71 | 0.71 [0.43, 1.15] |

**`large_tokamak_nof` — phase B in wall clock, s per optimisation** (pair B2/B0, 22 pair(s); W = 3, 4 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | BR (n=22) | B0 (n=22) | B1 (n=22) | B2 (n=22) | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 7.69 | 8.65 | 8.31 | 4.67 | 0.54 | 0.55 [0.46, 0.63] |
| M2 | 7.69 | 8.56 | 8.23 | 7.42 | 0.87 | 0.88 [0.73, 1.03] |
| M3 | 1.62 | 1.77 | 1.70 | 0.93 | 0.53 | 0.53 [0.44, 0.65] |
| Feedforward | 0.02 | 0.02 | 0.02 | 0.01 | 0.30 | 0.30 [0.25, 0.37] |
| Post-processing | 0.46 | 0.49 | 0.47 | 0.00 | 0.00 | 0.00 [0.00, 0.00] |
| MDA convergence test | 0.09 | 2.28 | 2.20 | 2.74 | 1.20 | 1.21 [1.02, 1.44] |
| dispatch | 0.27 | 0.32 | 0.32 | 0.53 | 1.62 | 1.64 [1.37, 1.92] |
| objective and constraints | 0.40 | 0.14 | 0.14 | 0.15 | 1.11 | 1.06 [0.89, 1.75] |
| optimiser own time | 0.17 | 0.13 | 0.12 | 0.10 | 0.73 | 0.88 [0.42, 1.81] |
| fixed per run | 5.83 | 5.79 | 5.02 | 4.99 | 0.86 | 0.87 [0.77, 0.96] |
| unattributed residual | 0.04 | 0.11 | 0.10 | 0.14 | 1.30 | 1.32 [0.98, 1.66] |
| Total | 24.28 | 28.25 | 26.62 | 21.68 | 0.77 | 0.77 [0.68, 0.89] |

**`large_tokamak_nof` — cost breakdown, phase B** (s per optimisation, the per-unit figure, share of Total; W = 3, 4 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | BR: s · per · share | B0: s · per · share | B1: s · per · share | B2: s · per · share |
|---|---|---|---|---|
| model evaluation (the modules summed) | 17.48 · 28.46 ms per evaluation · 71.9 % | 19.49 · 31.75 ms per evaluation · 68.9 % | 18.73 · 29.23 ms per evaluation · 70.3 % | 13.04 · 20.38 ms per evaluation · 60.1 % |
| MDA overhead per sweep: convergence test | 0.09 · 0.05 ms per sweep · 0.4 % | 2.28 · 1.08 ms per sweep · 8.1 % | 2.20 · 1.07 ms per sweep · 8.2 % | 2.74 · 0.57 ms per sweep · 12.6 % |
| MDA overhead per sweep: dispatch | 0.27 · 0.14 ms per sweep · 1.1 % | 0.32 · 0.15 ms per sweep · 1.1 % | 0.32 · 0.15 ms per sweep · 1.2 % | 0.53 · 0.11 ms per sweep · 2.4 % |
| optimiser overhead per iteration | 0.17 · 22.01 ms per iteration · 0.7 % | 0.13 · 16.76 ms per iteration · 0.5 % | 0.12 · 15.18 ms per iteration · 0.4 % | 0.10 · 12.26 ms per iteration · 0.4 % |
| fixed per run | 5.83 · 5.83 s per run · 24.1 % | 5.79 · 5.79 s per run · 20.5 % | 5.02 · 5.02 s per run · 19.0 % | 4.99 · 4.99 s per run · 23.1 % |
| Total | 24.28 · 39.62 ms per evaluation · 100.0 % | 28.25 · 46.07 ms per evaluation · 100.0 % | 26.62 · 41.61 ms per evaluation · 100.0 % | 21.68 · 33.93 ms per evaluation · 100.0 % |

**`low_aspect_ratio_DEMO` — phase A in wall clock, ms per evaluation** (pair A2/A1, 25 pair(s); W = 3, 4 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | AR (n=25) | A0 (n=25) | A1 (n=25) | A2 (n=25) | A2/A1 | A2/A1 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 16.77 | 18.07 | 19.45 | 10.40 | 0.53 | 0.57 [0.32, 0.98] |
| M2 | 18.06 | 19.49 | 20.87 | 18.97 | 0.91 | 0.95 [0.52, 1.72] |
| M3 | 3.51 | 3.83 | 4.10 | 1.49 | 0.36 | 0.37 [0.19, 0.80] |
| Feedforward | 0.05 | 0.05 | 0.05 | 0.02 | 0.38 | 0.36 [0.16, 0.89] |
| Post-processing | 0.98 | 1.10 | 1.11 | 0.37 | 0.33 | 0.32 [0.16, 0.68] |
| MDA convergence test | 0.17 | 4.94 | 5.13 | 6.17 | 1.20 | 1.30 [0.67, 2.46] |
| dispatch | 0.72 | 0.76 | 0.80 | 1.25 | 1.56 | 1.68 [0.90, 2.83] |
| objective and constraints | 0.88 | 0.23 | 0.25 | 0.23 | 0.92 | 0.89 [0.47, 1.97] |
| unattributed residual | 0.21 | 0.27 | 0.27 | 0.36 | 1.31 | 1.43 [0.66, 2.40] |
| Total | 41.37 | 48.83 | 52.12 | 39.34 | 0.75 | 0.80 [0.44, 1.40] |

**`low_aspect_ratio_DEMO` — phase B in wall clock, s per optimisation** (pair B2/B0, 12 pair(s); W = 3, 4 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | BR (n=12) | B0 (n=12) | B1 (n=12) | B2 (n=12) | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 28.79 | 29.67 | 39.44 | 21.60 | 0.73 | 0.41 [0.07, 11.82] |
| M2 | 30.12 | 31.30 | 41.81 | 37.59 | 1.20 | 0.67 [0.11, 19.80] |
| M3 | 6.21 | 6.27 | 8.42 | 4.85 | 0.77 | 0.42 [0.07, 13.06] |
| Feedforward | 0.08 | 0.08 | 0.10 | 0.03 | 0.42 | 0.24 [0.04, 6.86] |
| Post-processing | 1.72 | 1.69 | 2.25 | 0.00 | 0.00 | 0.00 [0.00, 0.00] |
| MDA convergence test | 0.33 | 8.08 | 10.75 | 13.54 | 1.68 | 0.94 [0.15, 28.43] |
| dispatch | 1.02 | 1.13 | 1.55 | 2.57 | 2.27 | 1.30 [0.20, 39.03] |
| objective and constraints | 1.50 | 0.49 | 0.72 | 0.76 | 1.54 | 1.15 [0.13, 25.12] |
| optimiser own time | 0.39 | 0.35 | 0.44 | 0.46 | 1.32 | 0.72 [0.13, 13.32] |
| fixed per run | 5.68 | 5.87 | 5.08 | 5.05 | 0.86 | 0.84 [0.74, 0.99] |
| unattributed residual | 0.23 | 0.45 | 0.63 | 0.80 | 1.79 | 1.03 [0.15, 37.37] |
| Total | 76.08 | 85.38 | 111.19 | 87.26 | 1.02 | 0.61 [0.11, 14.21] |

**`low_aspect_ratio_DEMO` — cost breakdown, phase B** (s per optimisation, the per-unit figure, share of Total; W = 3, 4 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | BR: s · per · share | B0: s · per · share | B1: s · per · share | B2: s · per · share |
|---|---|---|---|---|
| model evaluation (the modules summed) | 66.92 · 30.36 ms per evaluation · 83.7 % | 69.01 · 31.48 ms per evaluation · 77.4 % | 92.02 · 29.33 ms per evaluation · 78.6 % | 64.08 · 20.25 ms per evaluation · 68.6 % |
| MDA overhead per sweep: convergence test | 0.33 · 0.04 ms per sweep · 0.4 % | 8.08 · 1.06 ms per sweep · 9.0 % | 10.75 · 1.07 ms per sweep · 9.1 % | 13.54 · 0.57 ms per sweep · 14.4 % |
| MDA overhead per sweep: dispatch | 1.02 · 0.13 ms per sweep · 1.3 % | 1.13 · 0.15 ms per sweep · 1.3 % | 1.55 · 0.15 ms per sweep · 1.3 % | 2.57 · 0.11 ms per sweep · 2.7 % |
| optimiser overhead per iteration | 0.39 · 15.83 ms per iteration · 0.6 % | 0.35 · 13.11 ms per iteration · 0.4 % | 0.44 · 11.68 ms per iteration · 0.4 % | 0.46 · 12.25 ms per iteration · 0.5 % |
| fixed per run | 5.68 · 5.68 s per run · 11.9 % | 5.87 · 5.87 s per run · 10.9 % | 5.08 · 5.08 s per run · 9.5 % | 5.05 · 5.05 s per run · 12.1 % |
| Total | 76.08 · 36.41 ms per evaluation · 100.0 % | 85.38 · 40.79 ms per evaluation · 100.0 % | 111.19 · 37.44 ms per evaluation · 100.0 % | 87.26 · 29.61 ms per evaluation · 100.0 % |

**`st_regression` — phase A in wall clock, ms per evaluation** (pair A2/A0, 25 pair(s); W = 3, 4 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | AR (n=25) | A0 (n=25) | A1 (n=0) | A2 (n=25) | A2/A0 | A2/A0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 16.95 | 20.86 | — | 12.09 | 0.58 | 0.54 [0.37, 0.93] |
| M2 | 17.74 | 21.51 | — | 23.71 | 1.10 | 1.03 [0.65, 1.69] |
| M3 | 4.19 | 5.11 | — | 3.12 | 0.61 | 0.53 [0.27, 0.97] |
| Feedforward | 0.00 | 0.00 | — | 0.00 | — | — |
| Post-processing | 0.94 | 1.11 | — | 0.38 | 0.34 | 0.33 [0.19, 0.59] |
| MDA convergence test | 0.17 | 5.11 | — | 7.39 | 1.45 | 1.36 [0.85, 2.54] |
| dispatch | 0.64 | 0.76 | — | 1.41 | 1.84 | 1.76 [1.21, 3.09] |
| objective and constraints | 0.71 | 0.17 | — | 0.20 | 1.19 | 1.07 [0.60, 2.23] |
| unattributed residual | 0.15 | 0.25 | — | 0.41 | 1.62 | 1.47 [0.87, 3.13] |
| Total | 41.50 | 54.96 | — | 48.81 | 0.89 | 0.82 [0.52, 1.40] |

**`st_regression` — phase B in wall clock, s per optimisation** (pair B2/B0, 20 pair(s); W = 3, 4 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | BR (n=20) | B0 (n=20) | B1 (n=0) | B2 (n=20) | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 21.49 | 14.54 | — | 19.56 | 1.35 | 1.26 [0.35, 2.96] |
| M2 | 22.73 | 15.17 | — | 30.49 | 2.01 | 1.89 [0.48, 4.37] |
| M3 | 5.35 | 3.48 | — | 4.91 | 1.41 | 1.34 [0.34, 3.07] |
| Feedforward | 0.00 | 0.00 | — | 0.00 | — | — |
| Post-processing | 1.30 | 0.82 | — | 0.00 | 0.00 | 0.00 [0.00, 0.00] |
| MDA convergence test | 0.24 | 3.72 | — | 11.41 | 3.07 | 2.97 [0.72, 6.80] |
| dispatch | 0.73 | 0.50 | — | 2.05 | 4.08 | 3.98 [0.94, 9.07] |
| objective and constraints | 0.89 | 0.20 | — | 0.47 | 2.36 | 2.22 [0.55, 5.15] |
| optimiser own time | 0.32 | 0.22 | — | 0.51 | 2.32 | 2.18 [0.54, 4.79] |
| fixed per run | 5.47 | 5.47 | — | 4.87 | 0.89 | 0.90 [0.79, 0.99] |
| unattributed residual | 0.16 | 0.22 | — | 0.77 | 3.54 | 3.79 [0.53, 8.81] |
| Total | 58.69 | 44.33 | — | 75.03 | 1.69 | 1.52 [0.50, 3.75] |

**`st_regression` — cost breakdown, phase B** (s per optimisation, the per-unit figure, share of Total; W = 3, 4 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | BR: s · per · share | B0: s · per · share | B1: s · per · share | B2: s · per · share |
|---|---|---|---|---|
| model evaluation (the modules summed) | 50.88 · 29.15 ms per evaluation · 80.3 % | 34.01 · 27.95 ms per evaluation · 73.7 % | — | 54.96 · 18.91 ms per evaluation · 70.0 % |
| MDA overhead per sweep: convergence test | 0.24 · 0.04 ms per sweep · 0.4 % | 3.72 · 0.95 ms per sweep · 8.0 % | — | 11.41 · 0.47 ms per sweep · 14.4 % |
| MDA overhead per sweep: dispatch | 0.73 · 0.12 ms per sweep · 1.1 % | 0.50 · 0.13 ms per sweep · 1.1 % | — | 2.05 · 0.08 ms per sweep · 2.6 % |
| optimiser overhead per iteration | 0.32 · 11.33 ms per iteration · 0.5 % | 0.22 · 10.50 ms per iteration · 0.5 % | — | 0.51 · 10.17 ms per iteration · 0.6 % |
| fixed per run | 5.47 · 5.47 s per run · 16.1 % | 5.47 · 5.47 s per run · 15.9 % | — | 4.87 · 4.87 s per run · 10.8 % |
| Total | 58.69 · 36.53 ms per evaluation · 100.0 % | 44.33 · 38.08 ms per evaluation · 100.0 % | — | 75.03 · 27.24 ms per evaluation · 100.0 % |

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
| BR | 25 | 24 | 0 | 1 | 0 | 20 | finished, ifail = 5: 17 | — |
| B0 | 25 | 24 | 0 | 1 | 0 | 20 | finished, ifail = 5: 17 | — |
| B2 | 25 | 20 | 3 | 2 | 4 | 20 | finished, ifail = 2: 1, 9, 10; finished, ifail = 5: 15, 17 | 1, 9, 10, 15 |

### Table — verification

One row per check of plan §8, in its order. A gate's verdict is read from its record through the `gate_table` stage record, which this generator refuses when the verdict records have been re-made, removed or added to since the stage ran; `not pressed` is a gate with no verdict record (a declared placeholder that refuses, or one never pressed) or a rule that is not yet a construction. A verdict is PASS only with every tooth tripped.

*the gate_table stage record read 30 record(s) at ['0353c52471c95adbc903274ef93e82da351a200d', '06db785ccb4351f93087570359e95a9abeb21314', '2bd27bf5653552b4d88509000aa098f37b56a376', 'c2295511298249638e0c2e9a1bb3620dfc1bbe11'], and every one of them is byte-identical to what is on disk now*

| check | plan | verdict | detail |
|---|---|---|---|
| physics frozen | G0 | **PASS** | `g0prime` at `c2295511`: 1 of 77 mismatched; 4/4 teeth |
| switch neutrality | G1 | **PASS** | `switch_neutrality` at `c2295511`: 0 of 54988 mismatched; 9/9 teeth |
| matched accuracy — whole-state audit at 0 components above τ | A1 | **PASS** | `tok` A2/A1: similarity PASS, runs with a component ≥ τ A1 0 / A2 0 → **PASS**; `lad` A2/A1: similarity PASS, runs with a component ≥ τ A1 0 / A2 0 → **PASS**; `st` A2/A0: similarity PASS, runs with a component ≥ τ A0 0 / A2 0 → **PASS** (whole-state statistic, D36; the second half of the rule is the count column) |
| fixed-point distance between arms | A2 | **reported, no rule** | the tally's fixed-point distance table (plan §5 A2) |
| same optimum, attributed where it fails | B1 | **PASS tok · FAIL lad, st** | `tok` B0 → B1 PASS, B0 → B2 PASS (objf p90 4.6e-11 ≤ 1.0e-06; 0 hops of 22); `lad` B0 → B1 FAIL, B0 → B2 FAIL at p90 (objf p90 3.1e-04 > 1.0e-06): 4 hops of 12 (2 across clusters; seeds 1*, 10*, 11, 13), entering at B0 → B1 (the lift) 4 of 4; B1 → B2 (the partition) adds none: objf median 8.9e-15, p90 2.3e-14, same path on 12 of 12; the yardstick BR → B0 also hops on 0 of 4 of these seeds; `st` B0 → B2 FAIL at p90 (objf p90 1.3e-03 > 1.0e-06): 3 hops of 20 (3 across clusters; seeds 5*, 12*, 24*), entering at B0 → B2 3 of 3 — the partition, its block loops on the feedback couplings at τ = 1e-08; no B1 on this configuration; the yardstick BR → B0 also hops on 2 of 3 of these seeds (hop: objective difference above the floor; * = a retried arm; the tally's `same optimum by rung` table, plan §5 B1) |
| entry pairing | G6 | **PASS** | `entry_and_warm` at `c2295511`: 0 of 6717 mismatched; 3/3 teeth |
| arm composition | G5 | **PASS** | `switch_composition` at `c2295511`: 0 of 156 mismatched; 4/4 teeth |
| output-path equivalence | G9 | **PASS** | `output_path` at `c2295511`: 0 of 3879 mismatched; 4/4 teeth |
| the test set's teeth | GT | **PASS** | `test_set` at `c2295511`: 794 of 13424 mismatched; 4/4 teeth |

