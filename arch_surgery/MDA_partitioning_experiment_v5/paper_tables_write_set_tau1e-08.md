# Paper tables — Case 2: PROCESS

> **Document status** — **GENERATED, never hand-edited.** Written whole by `harness/measurement/paper_tables.py` (`experiment_runner.py --paper-tables write`) from the campaign's run records and the stage records, and compared whole by `--paper-tables check`, which refuses when this file and the records disagree. The one document of V5 list item 10: the main-text tables of `Structuring-fusion-MDAO-with-DSMs/3 results.tex` and the appendix tables of the V5 plan §8; each table is a Markdown grid and, where the paper prints it, LaTeX rows for the paper's `tabular` body.

*Over the **campaign** population — 553 run records at `b44c88c4`; sources `campaign_displaced` (phase A) and `campaign_optimisation` (phase B); the exit audit at position(s) `after_single_evaluation`, `entry_to_write_output_files` on the ruler(s) `frozen`.*

*Of run ID **`write_set_tau1e-08`** — test set write_set, tau 1e-08 (overridden); records under runs/write_set_tau1e-08/; not the declared default campaign's (`census_tau1e-08`, whose document is `paper_tables.md`).*

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
| stopping rule | objf/conf | whole write set @ τ = 1e-08 | whole write set @ τ = 1e-08 | whole write set @ τ = 1e-08 per block | objf/conf | whole write set @ τ = 1e-08 | whole write set @ τ = 1e-08 | whole write set @ τ = 1e-08 per block |
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
stopping rule & objf/conf & whole write set @ $\tau$ = 1e-08 & whole write set @ $\tau$ = 1e-08 & whole write set @ $\tau$ = 1e-08 per block & objf/conf & whole write set @ $\tau$ = 1e-08 & whole write set @ $\tau$ = 1e-08 & whole write set @ $\tau$ = 1e-08 per block \\
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
| M1 | 5.0 | 6.5 | 5.9 | 4.0 | 0.68 | 0.67 [0.57, 0.80] |
| M2 | 5.0 | 6.5 | 5.9 | 5.9 | 1.00 | 1.00 [1.00, 1.00] |
| M3 | 5.0 | 6.5 | 5.9 | 3.0 | 0.51 | 0.50 [0.43, 0.60] |
| Feedforward | 5.0 | 6.5 | 5.9 | 1 | 0.17 | 0.17 [0.14, 0.20] |
| Post-processing | 5.0 | 6.5 | 5.9 | 1 | 0.17 | 0.17 [0.14, 0.20] |

**`lad`** (low_aspect_ratio_DEMO, n = 25; pair A1 → A2)

| Module | AR | A0 | A1 | A2 | A2/A1 | A2/A1 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 5.0 | 5.4 | 5.0 | 4.0 | 0.80 | 0.80 [0.80, 0.80] |
| M2 | 5.0 | 5.4 | 5.0 | 5.0 | 1.00 | 1.00 [1.00, 1.00] |
| M3 | 5.0 | 5.4 | 5.0 | 3.0 | 0.60 | 0.60 [0.60, 0.60] |
| Feedforward | 5.0 | 5.4 | 5.0 | 1 | 0.20 | 0.20 [0.20, 0.20] |
| Post-processing | 5.0 | 5.4 | 5.0 | 1 | 0.20 | 0.20 [0.20, 0.20] |

**`st`** (st_regression, n = 25; pair A0 → A2)

| Module | AR | A0 | A1 | A2 | A2/A0 | A2/A0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 4.9 | 7.0 | — | 4.0 | 0.57 | 0.57 [0.57, 0.67] |
| M2 | 4.9 | 7.0 | — | 7.0 | 1.00 | 1.00 [1.00, 1.00] |
| M3 | 4.9 | 7.0 | — | 4.0 | 0.57 | 0.57 [0.43, 0.67] |
| Feedforward | — | — | — | — | — | — |
| Post-processing | 4.9 | 7.0 | — | 1 | 0.14 | 0.14 [0.14, 0.17] |

```latex
\begin{tabular}{l|rrrr|rc}
\hline
Module & AR & A0 & A1 & A2 & A2/A1 (A2/A0 on st) & A2/A1 (A2/A0 on st) med [min, max] \\
\hline
\multicolumn{7}{l}{\texttt{tok} ($n = 25$, A2/A1)} \\
\hline
M1              & 5.0 & 6.5 & 5.9 & 4.0 & 0.68 & 0.67 [0.57, 0.80] \\
M2              & 5.0 & 6.5 & 5.9 & 5.9 & 1.00 & 1.00 [1.00, 1.00] \\
M3              & 5.0 & 6.5 & 5.9 & 3.0 & 0.51 & 0.50 [0.43, 0.60] \\
Feedforward     & 5.0 & 6.5 & 5.9 & 1 & 0.17 & 0.17 [0.14, 0.20] \\
Post-processing & 5.0 & 6.5 & 5.9 & 1 & 0.17 & 0.17 [0.14, 0.20] \\
\hline
\multicolumn{7}{l}{\texttt{lad} ($n = 25$, A2/A1)} \\
\hline
M1              & 5.0 & 5.4 & 5.0 & 4.0 & 0.80 & 0.80 [0.80, 0.80] \\
M2              & 5.0 & 5.4 & 5.0 & 5.0 & 1.00 & 1.00 [1.00, 1.00] \\
M3              & 5.0 & 5.4 & 5.0 & 3.0 & 0.60 & 0.60 [0.60, 0.60] \\
Feedforward     & 5.0 & 5.4 & 5.0 & 1 & 0.20 & 0.20 [0.20, 0.20] \\
Post-processing & 5.0 & 5.4 & 5.0 & 1 & 0.20 & 0.20 [0.20, 0.20] \\
\hline
\multicolumn{7}{l}{\texttt{st} ($n = 25$, A2/A0)} \\
\hline
M1              & 4.9 & 7.0 & -- & 4.0 & 0.57 & 0.57 [0.57, 0.67] \\
M2              & 4.9 & 7.0 & -- & 7.0 & 1.00 & 1.00 [1.00, 1.00] \\
M3              & 4.9 & 7.0 & -- & 4.0 & 0.57 & 0.57 [0.43, 0.67] \\
Feedforward     & -- & -- & -- & -- & -- & -- \\
Post-processing & 4.9 & 7.0 & -- & 1 & 0.14 & 0.14 [0.14, 0.17] \\
\hline
\end{tabular}
```

### Table `tab:phaseB_iterations` — phase B, optimiser iterations

Mean optimiser iterations per run, summed over the optimiser's retry attempts, over the n seeds on which every arm reached an accepted optimum; `B2/B0` is the ratio of the means.

| Configuration | n | BR | B0 | B1 | B2 | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|---:|
| `tok` | 22 | 7.8 | 7.8 | 7.8 | 7.8 | 0.99 | 1.00 [0.88, 1.14] |
| `lad` | 11 | 29.8 | 29.8 | 20.9 | 20.9 | 0.70 | 0.81 [0.13, 5.91] |
| `st` | 23 | 31.6 | 26.4 | — | 26.7 | 1.01 | 1.00 [0.59, 2.13] |

```latex
\begin{tabular}{l|rrrr|rc}
\hline
Configuration & BR & B0 & B1 & B2 & B2/B0 & B2/B0 med [min, max] \\
\hline
\texttt{tok} ($n = 22$) & 7.8 & 7.8 & 7.8 & 7.8 & 0.99 & 1.00 [0.88, 1.14] \\
\texttt{lad} ($n = 11$) & 29.8 & 29.8 & 20.9 & 20.9 & 0.70 & 0.81 [0.13, 5.91] \\
\texttt{st} ($n = 23$) & 31.6 & 26.4 & -- & 26.7 & 1.01 & 1.00 [0.59, 2.13] \\
\hline
\end{tabular}
```

### Table `tab:phaseB_results` — phase B, module sweeps per optimisation

Mean sweeps of each module over one whole optimisation, rounded to integers. Every attempt and the output path, which is architecture (MDA_Output's sweeps in `BR`/`B0`, none in `B1`, the deferred nodes' one execution in `B2`). The exit audit's one sweep of every node is the harness's accuracy instrument and is **subtracted** (1 per node, checked on each run against the record's `audit_node_calls`; D36). Over the n seeds on which every arm reached an accepted optimum; `B2/B0` is the ratio of the means.

**`tok`** (large_tokamak_nof, n = 22; pair B0 → B2)

| Module | BR | B0 | B1 | B2 | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 1977 | 2431 | 2360 | 1562 | 0.64 | 0.65 [0.56, 0.75] |
| M2 | 1977 | 2431 | 2360 | 1895 | 0.78 | 0.78 [0.68, 0.91] |
| M3 | 1977 | 2431 | 2360 | 1703 | 0.70 | 0.70 [0.61, 0.81] |
| Feedforward | 1977 | 2431 | 2360 | 640 | 0.26 | 0.26 [0.23, 0.31] |
| Post-processing | 1977 | 2431 | 2360 | 1 | 0.00 | 0.00 [0.00, 0.00] |

**`lad`** (low_aspect_ratio_DEMO, n = 11; pair B0 → B2)

| Module | BR | B0 | B1 | B2 | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 8095 | 9325 | 6097 | 3964 | 0.43 | 0.49 [0.08, 3.75] |
| M2 | 8095 | 9325 | 6097 | 5036 | 0.54 | 0.63 [0.10, 4.77] |
| M3 | 8095 | 9325 | 6097 | 4612 | 0.49 | 0.57 [0.09, 4.36] |
| Feedforward | 8095 | 9325 | 6097 | 1714 | 0.18 | 0.21 [0.03, 1.62] |
| Post-processing | 8095 | 9325 | 6097 | 1 | 0.00 | 0.00 [0.00, 0.00] |

**`st`** (st_regression, n = 23; pair B0 → B2)

| Module | BR | B0 | B1 | B2 | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 6113 | 6436 | — | 3914 | 0.61 | 0.61 [0.35, 1.27] |
| M2 | 6113 | 6436 | — | 4703 | 0.73 | 0.74 [0.41, 1.56] |
| M3 | 6113 | 6436 | — | 4457 | 0.69 | 0.70 [0.40, 1.44] |
| Feedforward | — | — | — | — | — | — |
| Post-processing | 6113 | 6436 | — | 1 | 0.00 | 0.00 [0.00, 0.00] |

```latex
\begin{tabular}{l|cccc|cc}
\hline
Module & BR & B0 & B1 & B2 & B2/B0 & B2/B0 med [min, max] \\
\hline
\multicolumn{7}{l}{\texttt{tok} ($n = 22$, B2/B0)} \\
\hline
M1              & 1977 & 2431 & 2360 & 1562 & 0.64 & 0.65 [0.56, 0.75] \\
M2              & 1977 & 2431 & 2360 & 1895 & 0.78 & 0.78 [0.68, 0.91] \\
M3              & 1977 & 2431 & 2360 & 1703 & 0.70 & 0.70 [0.61, 0.81] \\
Feedforward     & 1977 & 2431 & 2360 & 640 & 0.26 & 0.26 [0.23, 0.31] \\
Post-processing & 1977 & 2431 & 2360 & 1 & 0.00 & 0.00 [0.00, 0.00] \\
\hline
\multicolumn{7}{l}{\texttt{lad} ($n = 11$, B2/B0)} \\
\hline
M1              & 8095 & 9325 & 6097 & 3964 & 0.43 & 0.49 [0.08, 3.75] \\
M2              & 8095 & 9325 & 6097 & 5036 & 0.54 & 0.63 [0.10, 4.77] \\
M3              & 8095 & 9325 & 6097 & 4612 & 0.49 & 0.57 [0.09, 4.36] \\
Feedforward     & 8095 & 9325 & 6097 & 1714 & 0.18 & 0.21 [0.03, 1.62] \\
Post-processing & 8095 & 9325 & 6097 & 1 & 0.00 & 0.00 [0.00, 0.00] \\
\hline
\multicolumn{7}{l}{\texttt{st} ($n = 23$, B2/B0)} \\
\hline
M1              & 6113 & 6436 & -- & 3914 & 0.61 & 0.61 [0.35, 1.27] \\
M2              & 6113 & 6436 & -- & 4703 & 0.73 & 0.74 [0.41, 1.56] \\
M3              & 6113 & 6436 & -- & 4457 & 0.69 & 0.70 [0.40, 1.44] \\
Feedforward     & -- & -- & -- & -- & -- & -- \\
Post-processing & 6113 & 6436 & -- & 1 & 0.00 & 0.00 [0.00, 0.00] \\
\hline
\end{tabular}
```

## Appendix

### Tables — wall clock (plan §6)

**Context, never evidence (D33).** The wall-clock instrument of plan §6 (list item 9, driver change DR12, A101 (v5-timers-and-once)): observation-only timers in the driver copy (`PROCESS_ARCH_TIMERS=on`) per node, block loop, evaluation and run, harvested into every campaign record, with the launcher's independent wall beside. Excluded from every cell and measured separately: the exit-audit sweep, the state snapshots, the record assembly and the harness's set-up before the run. The rows are `harness/measurement/timing.py`'s; the repeatability stage (three repetitions at W = 1) and D38's validity check are that module's stages and their records say whether the campaign's timings may be printed here. The phase A rows are **warmed** (A102 (v5-campaign), plan §6): the evaluation child runs a discarded warm-up evaluation on the same entry, re-enters the entry bit-exact, resets the counters and times the measured evaluation, so the module rows carry no numba cache load; the fixed per-run term (process start to the warm-up's first evaluation) is stamped in every record and is not a row of the phase A table.

**Where these timings come from (D38).** The validity check (`--timing validity`, at `b44c88c4`) found 0 of the campaign's timings of the repeatability seeds within the W = 1 repetitions' range and 0 outside. Every timing is the campaign's own, made with several workers at once and reported with its spread (D42, the user, 2026-09-30: the one-worker pass D38 would send no phase to is not run; the table below is the check's own rows); the worker counts the records are stamped with: W = 3. Phase B is over the count tables' seed set (every arm at an accepted optimum; D41).

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

**phase B in wall clock, s per optimisation** — As the phase A table, per whole optimisation in seconds, with the optimiser's own time (solve-phase wall less every evaluation) and the fixed per-run term (process start, imports, numba cache load, input parse, output writing, the once-per-run schedule derivation); Total is the run's wall less the harness-only costs (plan §6). **The module rows include one numba cache load per run**: a phase B run's first evaluation is not warmed (the fixed per-run term ends at its start), so its module rows carry the per-process cache load the warmed phase A records measure as warm-up less measured model time — a median of 0.24–0.45 s per run over the 11 configuration and arm rows, 0.6–3.1 % of the median module time per run of the arm's phase B twin, the same order in every arm (`--timing cache-load`, record at `b44c88c4`).

**cost breakdown, phase B** — Per configuration and arm: seconds per optimisation and ms per evaluation with the share of the total. Whether the architecture changes the overhead is read off the B0 and B2 columns of the per-sweep rows, normalised per evaluation (plan §6).

**`large_tokamak_nof` — phase A in wall clock, ms per evaluation** (pair A2/A1, 25 pair(s); W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | AR (n=25) | A0 (n=25) | A1 (n=25) | A2 (n=25) | A2/A1 | A2/A1 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 18.13 | 23.85 | 21.63 | 14.71 | 0.68 | 0.64 [0.38, 1.18] |
| M2 | 18.70 | 24.95 | 22.24 | 23.08 | 1.04 | 0.99 [0.63, 1.76] |
| M3 | 3.88 | 4.98 | 4.64 | 2.40 | 0.52 | 0.52 [0.31, 0.97] |
| Feedforward | 0.07 | 0.08 | 0.07 | 0.02 | 0.31 | 0.28 [0.14, 0.79] |
| Post-processing | 1.13 | 1.39 | 1.31 | 0.35 | 0.27 | 0.27 [0.16, 0.39] |
| MDA convergence test | 0.26 | 34.05 | 30.18 | 24.58 | 0.81 | 0.78 [0.48, 1.30] |
| dispatch | 0.82 | 1.15 | 1.05 | 1.86 | 1.77 | 1.75 [0.71, 2.98] |
| objective and constraints | 0.96 | 0.26 | 0.26 | 0.22 | 0.87 | 0.94 [0.22, 2.00] |
| unattributed residual | 0.25 | 0.39 | 0.34 | 0.53 | 1.55 | 1.61 [0.31, 2.82] |
| Total | 44.18 | 91.16 | 81.78 | 67.80 | 0.83 | 0.79 [0.52, 1.29] |

**`large_tokamak_nof` — phase B in wall clock, s per optimisation** (pair B2/B0, 22 pair(s); W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | BR (n=22) | B0 (n=22) | B1 (n=22) | B2 (n=22) | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 7.17 | 9.17 | 9.07 | 5.95 | 0.65 | 0.66 [0.54, 0.75] |
| M2 | 7.11 | 9.04 | 8.92 | 7.07 | 0.78 | 0.79 [0.64, 0.94] |
| M3 | 1.49 | 1.85 | 1.84 | 1.29 | 0.70 | 0.71 [0.57, 0.83] |
| Feedforward | 0.02 | 0.03 | 0.02 | 0.01 | 0.28 | 0.29 [0.24, 0.36] |
| Post-processing | 0.42 | 0.52 | 0.51 | 0.00 | 0.00 | 0.00 [0.00, 0.00] |
| MDA convergence test | 0.08 | 12.86 | 12.79 | 9.50 | 0.74 | 0.75 [0.62, 0.89] |
| dispatch | 0.25 | 0.38 | 0.38 | 0.64 | 1.67 | 1.69 [1.42, 2.17] |
| objective and constraints | 0.37 | 0.14 | 0.15 | 0.14 | 1.03 | 1.05 [0.87, 1.24] |
| optimiser own time | 0.16 | 0.09 | 0.09 | 0.11 | 1.30 | 1.14 [0.91, 2.23] |
| fixed per run | 5.43 | 5.27 | 4.75 | 4.61 | 0.88 | 0.89 [0.68, 1.21] |
| unattributed residual | 0.04 | 0.13 | 0.13 | 0.17 | 1.32 | 1.29 [0.91, 2.02] |
| Total | 22.55 | 39.48 | 38.66 | 29.49 | 0.75 | 0.76 [0.64, 0.89] |

**`large_tokamak_nof` — cost breakdown, phase B** (s per optimisation, the per-unit figure, share of Total; W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | BR: s · per · share | B0: s · per · share | B1: s · per · share | B2: s · per · share |
|---|---|---|---|---|
| model evaluation (the modules summed) | 16.21 · 26.39 ms per evaluation · 71.9 % | 20.62 · 33.53 ms per evaluation · 52.2 % | 20.36 · 31.79 ms per evaluation · 52.6 % | 14.32 · 22.38 ms per evaluation · 48.5 % |
| MDA overhead per sweep: convergence test | 0.08 · 0.04 ms per sweep · 0.4 % | 12.86 · 5.29 ms per sweep · 32.6 % | 12.79 · 5.42 ms per sweep · 33.1 % | 9.50 · 1.64 ms per sweep · 32.2 % |
| MDA overhead per sweep: dispatch | 0.25 · 0.13 ms per sweep · 1.1 % | 0.38 · 0.16 ms per sweep · 1.0 % | 0.38 · 0.16 ms per sweep · 1.0 % | 0.64 · 0.11 ms per sweep · 2.2 % |
| optimiser overhead per iteration | 0.16 · 21.03 ms per iteration · 0.7 % | 0.09 · 10.93 ms per iteration · 0.2 % | 0.09 · 11.31 ms per iteration · 0.2 % | 0.11 · 14.29 ms per iteration · 0.4 % |
| fixed per run | 5.43 · 5.43 s per run · 24.1 % | 5.27 · 5.27 s per run · 13.4 % | 4.75 · 4.75 s per run · 12.4 % | 4.61 · 4.61 s per run · 15.7 % |
| Total | 22.55 · 36.74 ms per evaluation · 100.0 % | 39.48 · 64.27 ms per evaluation · 100.0 % | 38.66 · 60.41 ms per evaluation · 100.0 % | 29.49 · 46.12 ms per evaluation · 100.0 % |

**`low_aspect_ratio_DEMO` — phase A in wall clock, ms per evaluation** (pair A2/A1, 25 pair(s); W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | AR (n=25) | A0 (n=25) | A1 (n=25) | A2 (n=25) | A2/A1 | A2/A1 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 17.29 | 19.57 | 17.81 | 15.45 | 0.87 | 0.80 [0.46, 2.67] |
| M2 | 18.12 | 20.85 | 19.41 | 18.57 | 0.96 | 0.91 [0.57, 2.62] |
| M3 | 3.56 | 4.14 | 3.81 | 2.24 | 0.59 | 0.57 [0.31, 1.76] |
| Feedforward | 0.05 | 0.06 | 0.05 | 0.02 | 0.40 | 0.40 [0.19, 1.51] |
| Post-processing | 1.00 | 1.14 | 1.02 | 0.33 | 0.32 | 0.32 [0.16, 0.84] |
| MDA convergence test | 0.18 | 27.88 | 25.97 | 21.55 | 0.83 | 0.82 [0.45, 2.36] |
| dispatch | 0.66 | 0.87 | 0.75 | 1.68 | 2.24 | 1.85 [0.95, 9.64] |
| objective and constraints | 0.85 | 0.22 | 0.25 | 0.24 | 0.92 | 0.97 [0.32, 3.10] |
| unattributed residual | 0.19 | 0.30 | 0.28 | 0.48 | 1.73 | 1.42 [0.58, 10.54] |
| Total | 41.91 | 75.10 | 69.41 | 60.62 | 0.87 | 0.85 [0.49, 2.58] |

**`low_aspect_ratio_DEMO` — phase B in wall clock, s per optimisation** (pair B2/B0, 11 pair(s); W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | BR (n=11) | B0 (n=11) | B1 (n=11) | B2 (n=11) | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 28.77 | 33.77 | 23.27 | 15.08 | 0.45 | 0.50 [0.08, 4.01] |
| M2 | 30.38 | 35.21 | 24.25 | 19.78 | 0.56 | 0.62 [0.11, 4.99] |
| M3 | 6.18 | 7.00 | 4.85 | 3.57 | 0.51 | 0.57 [0.10, 4.73] |
| Feedforward | 0.08 | 0.10 | 0.06 | 0.02 | 0.21 | 0.21 [0.04, 2.02] |
| Post-processing | 1.72 | 1.93 | 1.34 | 0.00 | 0.00 | 0.00 [0.00, 0.00] |
| MDA convergence test | 0.34 | 49.18 | 33.59 | 25.58 | 0.52 | 0.59 [0.10, 4.79] |
| dispatch | 1.03 | 1.44 | 1.02 | 1.70 | 1.19 | 1.16 [0.22, 11.57] |
| objective and constraints | 1.52 | 0.52 | 0.41 | 0.39 | 0.75 | 0.80 [0.14, 7.14] |
| optimiser own time | 0.40 | 0.31 | 0.27 | 0.26 | 0.83 | 0.83 [0.21, 8.12] |
| fixed per run | 5.22 | 5.21 | 4.81 | 4.83 | 0.93 | 0.94 [0.83, 1.05] |
| unattributed residual | 0.25 | 0.58 | 0.42 | 0.53 | 0.91 | 0.91 [0.17, 10.81] |
| Total | 75.89 | 135.26 | 94.30 | 71.74 | 0.53 | 0.60 [0.11, 4.32] |

**`low_aspect_ratio_DEMO` — cost breakdown, phase B** (s per optimisation, the per-unit figure, share of Total; W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | BR: s · per · share | B0: s · per · share | B1: s · per · share | B2: s · per · share |
|---|---|---|---|---|
| model evaluation (the modules summed) | 67.14 · 29.09 ms per evaluation · 84.5 % | 78.01 · 33.56 ms per evaluation · 56.3 % | 53.78 · 31.72 ms per evaluation · 56.1 % | 38.44 · 22.46 ms per evaluation · 52.5 % |
| MDA overhead per sweep: convergence test | 0.34 · 0.04 ms per sweep · 0.4 % | 49.18 · 5.28 ms per sweep · 35.2 % | 33.59 · 5.56 ms per sweep · 35.0 % | 25.58 · 1.67 ms per sweep · 34.9 % |
| MDA overhead per sweep: dispatch | 1.03 · 0.13 ms per sweep · 1.3 % | 1.44 · 0.15 ms per sweep · 1.0 % | 1.02 · 0.17 ms per sweep · 1.1 % | 1.70 · 0.11 ms per sweep · 2.3 % |
| optimiser overhead per iteration | 0.40 · 15.25 ms per iteration · 0.6 % | 0.31 · 10.45 ms per iteration · 0.2 % | 0.27 · 13.68 ms per iteration · 0.3 % | 0.26 · 12.41 ms per iteration · 0.4 % |
| fixed per run | 5.22 · 5.22 s per run · 11.1 % | 5.21 · 5.21 s per run · 6.4 % | 4.81 · 4.81 s per run · 6.6 % | 4.83 · 4.83 s per run · 8.8 % |
| Total | 75.89 · 34.59 ms per evaluation · 100.0 % | 135.26 · 59.63 ms per evaluation · 100.0 % | 94.30 · 56.56 ms per evaluation · 100.0 % | 71.74 · 42.84 ms per evaluation · 100.0 % |

**`st_regression` — phase A in wall clock, ms per evaluation** (pair A2/A0, 25 pair(s); W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | AR (n=25) | A0 (n=25) | A1 (n=0) | A2 (n=25) | A2/A0 | A2/A0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 17.63 | 25.11 | — | 12.54 | 0.50 | 0.53 [0.24, 1.06] |
| M2 | 18.02 | 25.09 | — | 21.89 | 0.87 | 0.93 [0.41, 1.57] |
| M3 | 4.41 | 6.30 | — | 2.94 | 0.47 | 0.51 [0.17, 1.07] |
| Feedforward | 0.00 | 0.00 | — | 0.00 | — | — |
| Post-processing | 0.97 | 1.38 | — | 0.28 | 0.20 | 0.23 [0.07, 0.52] |
| MDA convergence test | 0.18 | 35.27 | — | 21.96 | 0.62 | 0.66 [0.34, 1.42] |
| dispatch | 0.65 | 1.02 | — | 1.33 | 1.30 | 1.53 [0.37, 2.76] |
| objective and constraints | 0.70 | 0.20 | — | 0.17 | 0.86 | 0.91 [0.33, 2.47] |
| unattributed residual | 0.15 | 0.39 | — | 0.36 | 0.94 | 1.14 [0.22, 2.07] |
| Total | 42.72 | 94.81 | — | 61.54 | 0.65 | 0.70 [0.31, 1.31] |

**`st_regression` — phase B in wall clock, s per optimisation** (pair B2/B0, 23 pair(s); W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | BR (n=23) | B0 (n=23) | B1 (n=0) | B2 (n=23) | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 21.96 | 24.34 | — | 14.28 | 0.59 | 0.61 [0.34, 0.98] |
| M2 | 23.41 | 25.35 | — | 18.10 | 0.71 | 0.74 [0.41, 1.23] |
| M3 | 5.44 | 5.86 | — | 3.86 | 0.66 | 0.69 [0.40, 1.09] |
| Feedforward | 0.00 | 0.00 | — | 0.00 | — | — |
| Post-processing | 1.30 | 1.38 | — | 0.00 | 0.00 | 0.00 [0.00, 0.00] |
| MDA convergence test | 0.24 | 34.14 | — | 22.82 | 0.67 | 0.69 [0.39, 1.14] |
| dispatch | 0.71 | 0.93 | — | 1.41 | 1.51 | 1.61 [0.89, 2.36] |
| objective and constraints | 0.91 | 0.29 | — | 0.27 | 0.92 | 0.95 [0.56, 1.50] |
| optimiser own time | 0.32 | 0.27 | — | 0.27 | 1.00 | 1.03 [0.57, 1.95] |
| fixed per run | 5.37 | 5.40 | — | 4.81 | 0.89 | 0.88 [0.79, 1.02] |
| unattributed residual | 0.15 | 0.41 | — | 0.50 | 1.22 | 1.31 [0.72, 5.87] |
| Total | 59.81 | 98.37 | — | 66.32 | 0.67 | 0.71 [0.39, 1.12] |

**`st_regression` — cost breakdown, phase B** (s per optimisation, the per-unit figure, share of Total; W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | BR: s · per · share | B0: s · per · share | B1: s · per · share | B2: s · per · share |
|---|---|---|---|---|
| model evaluation (the modules summed) | 52.10 · 28.24 ms per evaluation · 81.4 % | 56.92 · 36.44 ms per evaluation · 56.2 % | — | 36.24 · 23.80 ms per evaluation · 53.0 % |
| MDA overhead per sweep: convergence test | 0.24 · 0.04 ms per sweep · 0.4 % | 34.14 · 5.28 ms per sweep · 33.7 % | — | 22.82 · 1.44 ms per sweep · 33.2 % |
| MDA overhead per sweep: dispatch | 0.71 · 0.12 ms per sweep · 1.1 % | 0.93 · 0.14 ms per sweep · 0.9 % | — | 1.41 · 0.09 ms per sweep · 2.1 % |
| optimiser overhead per iteration | 0.32 · 10.80 ms per iteration · 0.5 % | 0.27 · 10.23 ms per iteration · 0.3 % | — | 0.27 · 10.27 ms per iteration · 0.4 % |
| fixed per run | 5.37 · 5.37 s per run · 14.9 % | 5.40 · 5.40 s per run · 8.3 % | — | 4.81 · 4.81 s per run · 10.3 % |
| Total | 59.81 · 34.97 ms per evaluation · 100.0 % | 98.37 · 64.90 ms per evaluation · 100.0 % | — | 66.32 · 45.11 ms per evaluation · 100.0 % |

**phase B in wall clock, s per optimisation — LaTeX** — The LaTeX form of the phase B wall-clock tables above, the 3 configurations in one `tabular` (n is each table's pair count): every cell the Markdown grid's own string, compared with it before writing — **0 mismatched of 258**; a doctored cell caught: **yes**. Wall clock is context, never evidence (D33).

```latex
\begin{tabular}{l|cccc|cc}
\hline
Row & BR & B0 & B1 & B2 & B2/B0 & B2/B0 med [min, max] \\
\hline
\multicolumn{7}{l}{\texttt{tok} ($n = 22$)} \\
\hline
M1                        & 7.17 & 9.17 & 9.07 & 5.95 & 0.65 & 0.66 [0.54, 0.75] \\
M2                        & 7.11 & 9.04 & 8.92 & 7.07 & 0.78 & 0.79 [0.64, 0.94] \\
M3                        & 1.49 & 1.85 & 1.84 & 1.29 & 0.70 & 0.71 [0.57, 0.83] \\
Feedforward               & 0.02 & 0.03 & 0.02 & 0.01 & 0.28 & 0.29 [0.24, 0.36] \\
Post-processing           & 0.42 & 0.52 & 0.51 & 0.00 & 0.00 & 0.00 [0.00, 0.00] \\
MDA convergence test      & 0.08 & 12.86 & 12.79 & 9.50 & 0.74 & 0.75 [0.62, 0.89] \\
dispatch                  & 0.25 & 0.38 & 0.38 & 0.64 & 1.67 & 1.69 [1.42, 2.17] \\
objective and constraints & 0.37 & 0.14 & 0.15 & 0.14 & 1.03 & 1.05 [0.87, 1.24] \\
optimiser own time        & 0.16 & 0.09 & 0.09 & 0.11 & 1.30 & 1.14 [0.91, 2.23] \\
fixed per run             & 5.43 & 5.27 & 4.75 & 4.61 & 0.88 & 0.89 [0.68, 1.21] \\
unattributed residual     & 0.04 & 0.13 & 0.13 & 0.17 & 1.32 & 1.29 [0.91, 2.02] \\
\hline
Total                     & 22.55 & 39.48 & 38.66 & 29.49 & 0.75 & 0.76 [0.64, 0.89] \\
\hline
\multicolumn{7}{l}{\texttt{lad} ($n = 11$)} \\
\hline
M1                        & 28.77 & 33.77 & 23.27 & 15.08 & 0.45 & 0.50 [0.08, 4.01] \\
M2                        & 30.38 & 35.21 & 24.25 & 19.78 & 0.56 & 0.62 [0.11, 4.99] \\
M3                        & 6.18 & 7.00 & 4.85 & 3.57 & 0.51 & 0.57 [0.10, 4.73] \\
Feedforward               & 0.08 & 0.10 & 0.06 & 0.02 & 0.21 & 0.21 [0.04, 2.02] \\
Post-processing           & 1.72 & 1.93 & 1.34 & 0.00 & 0.00 & 0.00 [0.00, 0.00] \\
MDA convergence test      & 0.34 & 49.18 & 33.59 & 25.58 & 0.52 & 0.59 [0.10, 4.79] \\
dispatch                  & 1.03 & 1.44 & 1.02 & 1.70 & 1.19 & 1.16 [0.22, 11.57] \\
objective and constraints & 1.52 & 0.52 & 0.41 & 0.39 & 0.75 & 0.80 [0.14, 7.14] \\
optimiser own time        & 0.40 & 0.31 & 0.27 & 0.26 & 0.83 & 0.83 [0.21, 8.12] \\
fixed per run             & 5.22 & 5.21 & 4.81 & 4.83 & 0.93 & 0.94 [0.83, 1.05] \\
unattributed residual     & 0.25 & 0.58 & 0.42 & 0.53 & 0.91 & 0.91 [0.17, 10.81] \\
\hline
Total                     & 75.89 & 135.26 & 94.30 & 71.74 & 0.53 & 0.60 [0.11, 4.32] \\
\hline
\multicolumn{7}{l}{\texttt{st} ($n = 23$)} \\
\hline
M1                        & 21.96 & 24.34 & -- & 14.28 & 0.59 & 0.61 [0.34, 0.98] \\
M2                        & 23.41 & 25.35 & -- & 18.10 & 0.71 & 0.74 [0.41, 1.23] \\
M3                        & 5.44 & 5.86 & -- & 3.86 & 0.66 & 0.69 [0.40, 1.09] \\
Feedforward               & 0.00 & 0.00 & -- & 0.00 & -- & -- \\
Post-processing           & 1.30 & 1.38 & -- & 0.00 & 0.00 & 0.00 [0.00, 0.00] \\
MDA convergence test      & 0.24 & 34.14 & -- & 22.82 & 0.67 & 0.69 [0.39, 1.14] \\
dispatch                  & 0.71 & 0.93 & -- & 1.41 & 1.51 & 1.61 [0.89, 2.36] \\
objective and constraints & 0.91 & 0.29 & -- & 0.27 & 0.92 & 0.95 [0.56, 1.50] \\
optimiser own time        & 0.32 & 0.27 & -- & 0.27 & 1.00 & 1.03 [0.57, 1.95] \\
fixed per run             & 5.37 & 5.40 & -- & 4.81 & 0.89 & 0.88 [0.79, 1.02] \\
unattributed residual     & 0.15 & 0.41 & -- & 0.50 & 1.22 & 1.31 [0.72, 5.87] \\
\hline
Total                     & 59.81 & 98.37 & -- & 66.32 & 0.67 & 0.71 [0.39, 1.12] \\
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

| arm | offered | accepted | finished, ifail = 5 | crashed (RuntimeError) | coupling-loop cap (ModuleSolveFailure) | lost_another_arm_accepted | seed_set | seeds_not_accepted | lost_seeds |
|---|---|---|---|---|---|---|---|---|---|
| BR | 25 | 12 | 11 | 2 | 0 | 0 | 11 | finished, ifail = 5: 2, 4, 7, 8, 14, 16, 17, 20, 22, 23, 24; crashed (RuntimeError): 3, 21 | — |
| B0 | 25 | 12 | 9 | 2 | 2 | 0 | 11 | finished, ifail = 5: 2, 7, 8, 14, 16, 17, 20, 23, 24; crashed (RuntimeError): 3, 21; coupling-loop cap (ModuleSolveFailure): 4, 22 | — |
| B1 | 25 | 11 | 9 | 2 | 3 | 1 | 11 | finished, ifail = 5: 2, 7, 8, 14, 16, 17, 20, 23, 24; crashed (RuntimeError): 3, 21; coupling-loop cap (ModuleSolveFailure): 4, 10, 22 | 10 |
| B2 | 25 | 11 | 9 | 2 | 3 | 1 | 11 | finished, ifail = 5: 2, 7, 8, 14, 16, 17, 20, 23, 24; crashed (RuntimeError): 3, 21; coupling-loop cap (ModuleSolveFailure): 4, 10, 22 | 10 |

**`st`** (st_regression)

| arm | offered | accepted | finished, ifail = 5 | lost_another_arm_accepted | seed_set | seeds_not_accepted | lost_seeds |
|---|---|---|---|---|---|---|---|
| BR | 25 | 24 | 1 | 0 | 23 | finished, ifail = 5: 17 | — |
| B0 | 25 | 23 | 2 | 1 | 23 | finished, ifail = 5: 10, 17 | 10 |
| B2 | 25 | 24 | 1 | 0 | 23 | finished, ifail = 5: 17 | — |

### Table — verification

One row per check of plan §8, in its order. A gate's verdict is read from its record through the `gate_table` stage record, which this generator refuses when the verdict records have been re-made, removed or added to since the stage ran; `not pressed` is a gate with no verdict record (a declared placeholder that refuses, or one never pressed) or a rule that is not yet a construction. A verdict is PASS only with every tooth tripped.

*the gate_table stage record read 28 record(s) at ['5447cca3148a0cbf96084238bd3e2ca7a63bb705'], and every one of them is byte-identical to what is on disk now*

| check | plan | verdict | detail |
|---|---|---|---|
| physics frozen | G0 | **PASS** | `g0prime` at `5447cca3`: 1 of 77 mismatched; 4/4 teeth |
| switch neutrality | G1 | **PASS** | `switch_neutrality` at `5447cca3`: 0 of 54973 mismatched; 10/10 teeth |
| matched accuracy — whole-state audit at 0 components above τ | A1 | **PASS** | `tok` A2/A1: similarity PASS, runs with a component ≥ τ A1 0 / A2 0 → **PASS**; `lad` A2/A1: similarity PASS, runs with a component ≥ τ A1 0 / A2 0 → **PASS**; `st` A2/A0: similarity PASS, runs with a component ≥ τ A0 0 / A2 0 → **PASS** (whole-state statistic, D36; the second half of the rule is the count column) |
| fixed-point distance between arms | A2 | **reported, no rule** | the tally's fixed-point distance table (plan §5 A2) |
| same optimum, attributed where it fails | B1 | **PASS tok, st · FAIL lad** | `tok` B0 → B1 PASS, B0 → B2 PASS (objf p90 4.6e-11 ≤ 1.0e-06; 0 hops of 22); `lad` B0 → B1 FAIL, B0 → B2 FAIL at p90 (objf p90 2.1e-06 > 1.0e-06): 3 hops of 11 (1 across clusters; seeds 1*, 11, 13), entering at B0 → B1 (the lift) 3 of 3; B1 → B2 (the partition) adds none: objf median 8.1e-15, p90 3.7e-14, same path on 11 of 11; the yardstick BR → B0 also hops on 0 of 3 of these seeds; `st` B0 → B2 PASS (objf p90 3.4e-10 ≤ 1.0e-06; 2 hops of 23) (hop: objective difference above the floor; * = a retried arm; the tally's `same optimum by rung` table, plan §5 B1) |
| entry pairing | G6 | **PASS** | `entry_and_warm` at `5447cca3`: 0 of 6717 mismatched; 3/3 teeth |
| arm composition | G5 | **PASS** | `switch_composition` at `5447cca3`: 0 of 159 mismatched; 4/4 teeth |
| output-path equivalence | G9 | **PASS** | `output_path` at `5447cca3`: 0 of 3879 mismatched; 5/5 teeth |
| the test set's teeth | GT | **not pressed** | `test_set` has no verdict record |

