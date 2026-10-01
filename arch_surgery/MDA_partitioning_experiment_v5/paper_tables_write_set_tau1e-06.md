# Paper tables — Case 2: PROCESS

> **Document status** — **GENERATED, never hand-edited.** Written whole by `harness/measurement/paper_tables.py` (`experiment_runner.py --paper-tables write`) from the campaign's run records and the stage records, and compared whole by `--paper-tables check`, which refuses when this file and the records disagree. The one document of V5 list item 10: the main-text tables of `Structuring-fusion-MDAO-with-DSMs/3 results.tex` and the appendix tables of the V5 plan §8; each table is a Markdown grid and, where the paper prints it, LaTeX rows for the paper's `tabular` body.

*Over the **campaign** population — 553 run records at `a1db0a0c`; sources `campaign_displaced` (phase A) and `campaign_optimisation` (phase B); the exit audit at position(s) `after_single_evaluation`, `entry_to_write_output_files` on the ruler(s) `frozen`.*

*Of run ID **`write_set_tau1e-06`** — test set write_set, tau 1e-06; records under runs/write_set_tau1e-06/; not the declared default campaign's (`census_tau1e-08`, whose document is `paper_tables.md`).*

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
| stopping rule | objf/conf | whole write set @ τ = 1e-06 | whole write set @ τ = 1e-06 | whole write set @ τ = 1e-06 per block | objf/conf | whole write set @ τ = 1e-06 | whole write set @ τ = 1e-06 | whole write set @ τ = 1e-06 per block |
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
stopping rule & objf/conf & whole write set @ $\tau$ = 1e-06 & whole write set @ $\tau$ = 1e-06 & whole write set @ $\tau$ = 1e-06 per block & objf/conf & whole write set @ $\tau$ = 1e-06 & whole write set @ $\tau$ = 1e-06 & whole write set @ $\tau$ = 1e-06 per block \\
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
| M1 | 5.0 | 5.5 | 5.1 | 4.0 | 0.78 | 0.80 [0.67, 1.00] |
| M2 | 5.0 | 5.5 | 5.1 | 5.2 | 1.01 | 1.00 [1.00, 1.25] |
| M3 | 5.0 | 5.5 | 5.1 | 3.0 | 0.59 | 0.60 [0.50, 0.75] |
| Feedforward | 5.0 | 5.5 | 5.1 | 1 | 0.20 | 0.20 [0.17, 0.25] |
| Post-processing | 5.0 | 5.5 | 5.1 | 1 | 0.20 | 0.20 [0.17, 0.25] |

**`lad`** (low_aspect_ratio_DEMO, n = 25; pair A1 → A2)

| Module | AR | A0 | A1 | A2 | A2/A1 | A2/A1 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 5.0 | 5.0 | 4.9 | 4.0 | 0.81 | 0.80 [0.80, 1.00] |
| M2 | 5.0 | 5.0 | 4.9 | 4.9 | 0.99 | 1.00 [0.80, 1.00] |
| M3 | 5.0 | 5.0 | 4.9 | 3.0 | 0.61 | 0.60 [0.60, 0.75] |
| Feedforward | 5.0 | 5.0 | 4.9 | 1 | 0.20 | 0.20 [0.20, 0.25] |
| Post-processing | 5.0 | 5.0 | 4.9 | 1 | 0.20 | 0.20 [0.20, 0.25] |

**`st`** (st_regression, n = 25; pair A0 → A2)

| Module | AR | A0 | A1 | A2 | A2/A0 | A2/A0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 4.9 | 5.8 | — | 4.0 | 0.68 | 0.67 [0.67, 0.80] |
| M2 | 4.9 | 5.8 | — | 5.8 | 1.00 | 1.00 [1.00, 1.00] |
| M3 | 4.9 | 5.8 | — | 3.0 | 0.51 | 0.50 [0.50, 0.60] |
| Feedforward | — | — | — | — | — | — |
| Post-processing | 4.9 | 5.8 | — | 1 | 0.17 | 0.17 [0.17, 0.20] |

```latex
\begin{tabular}{l|rrrr|rc}
\hline
Module & AR & A0 & A1 & A2 & A2/A1 (A2/A0 on st) & A2/A1 (A2/A0 on st) med [min, max] \\
\hline
\multicolumn{7}{l}{\texttt{tok} ($n = 25$, A2/A1)} \\
\hline
M1              & 5.0 & 5.5 & 5.1 & 4.0 & 0.78 & 0.80 [0.67, 1.00] \\
M2              & 5.0 & 5.5 & 5.1 & 5.2 & 1.01 & 1.00 [1.00, 1.25] \\
M3              & 5.0 & 5.5 & 5.1 & 3.0 & 0.59 & 0.60 [0.50, 0.75] \\
Feedforward     & 5.0 & 5.5 & 5.1 & 1 & 0.20 & 0.20 [0.17, 0.25] \\
Post-processing & 5.0 & 5.5 & 5.1 & 1 & 0.20 & 0.20 [0.17, 0.25] \\
\hline
\multicolumn{7}{l}{\texttt{lad} ($n = 25$, A2/A1)} \\
\hline
M1              & 5.0 & 5.0 & 4.9 & 4.0 & 0.81 & 0.80 [0.80, 1.00] \\
M2              & 5.0 & 5.0 & 4.9 & 4.9 & 0.99 & 1.00 [0.80, 1.00] \\
M3              & 5.0 & 5.0 & 4.9 & 3.0 & 0.61 & 0.60 [0.60, 0.75] \\
Feedforward     & 5.0 & 5.0 & 4.9 & 1 & 0.20 & 0.20 [0.20, 0.25] \\
Post-processing & 5.0 & 5.0 & 4.9 & 1 & 0.20 & 0.20 [0.20, 0.25] \\
\hline
\multicolumn{7}{l}{\texttt{st} ($n = 25$, A2/A0)} \\
\hline
M1              & 4.9 & 5.8 & -- & 4.0 & 0.68 & 0.67 [0.67, 0.80] \\
M2              & 4.9 & 5.8 & -- & 5.8 & 1.00 & 1.00 [1.00, 1.00] \\
M3              & 4.9 & 5.8 & -- & 3.0 & 0.51 & 0.50 [0.50, 0.60] \\
Feedforward     & -- & -- & -- & -- & -- & -- \\
Post-processing & 4.9 & 5.8 & -- & 1 & 0.17 & 0.17 [0.17, 0.20] \\
\hline
\end{tabular}
```

### Table `tab:phaseB_iterations` — phase B, optimiser iterations

Mean optimiser iterations per run, summed over the optimiser's retry attempts, over the n seeds on which every arm reached an accepted optimum; `B2/B0` is the ratio of the means.

| Configuration | n | BR | B0 | B1 | B2 | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|---:|
| `tok` | 22 | 7.8 | 7.8 | 7.8 | 7.8 | 0.99 | 1.00 [0.88, 1.14] |
| `lad` | 11 | 29.8 | 29.8 | 20.9 | 20.9 | 0.70 | 0.81 [0.13, 5.91] |
| `st` | 22 | 31.2 | 25.1 | — | 24.0 | 0.95 | 1.00 [0.25, 1.36] |

```latex
\begin{tabular}{l|rrrr|rc}
\hline
Configuration & BR & B0 & B1 & B2 & B2/B0 & B2/B0 med [min, max] \\
\hline
\texttt{tok} ($n = 22$) & 7.8 & 7.8 & 7.8 & 7.8 & 0.99 & 1.00 [0.88, 1.14] \\
\texttt{lad} ($n = 11$) & 29.8 & 29.8 & 20.9 & 20.9 & 0.70 & 0.81 [0.13, 5.91] \\
\texttt{st} ($n = 22$) & 31.2 & 25.1 & -- & 24.0 & 0.95 & 1.00 [0.25, 1.36] \\
\hline
\end{tabular}
```

### Table `tab:phaseB_results` — phase B, module sweeps per optimisation

Mean sweeps of each module over one whole optimisation, rounded to integers. Every attempt and the output path, which is architecture (MDA_Output's sweeps in `BR`/`B0`, none in `B1`, the deferred nodes' one execution in `B2`). The exit audit's one sweep of every node is the harness's accuracy instrument and is **subtracted** (1 per node, checked on each run against the record's `audit_node_calls`; D36). Over the n seeds on which every arm reached an accepted optimum; `B2/B0` is the ratio of the means.

**`tok`** (large_tokamak_nof, n = 22; pair B0 → B2)

| Module | BR | B0 | B1 | B2 | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 1977 | 2027 | 2040 | 1388 | 0.68 | 0.69 [0.60, 0.80] |
| M2 | 1977 | 2027 | 2040 | 1761 | 0.87 | 0.88 [0.76, 1.01] |
| M3 | 1977 | 2027 | 2040 | 1541 | 0.76 | 0.77 [0.66, 0.89] |
| Feedforward | 1977 | 2027 | 2040 | 640 | 0.32 | 0.32 [0.28, 0.37] |
| Post-processing | 1977 | 2027 | 2040 | 1 | 0.00 | 0.00 [0.00, 0.00] |

**`lad`** (low_aspect_ratio_DEMO, n = 11; pair B0 → B2)

| Module | BR | B0 | B1 | B2 | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 8095 | 7859 | 5436 | 3670 | 0.47 | 0.54 [0.08, 4.13] |
| M2 | 8095 | 7859 | 5436 | 4660 | 0.59 | 0.69 [0.11, 5.24] |
| M3 | 8095 | 7859 | 5436 | 4273 | 0.54 | 0.63 [0.10, 4.80] |
| Feedforward | 8095 | 7859 | 5436 | 1714 | 0.22 | 0.25 [0.04, 1.93] |
| Post-processing | 8095 | 7859 | 5436 | 1 | 0.00 | 0.00 [0.00, 0.00] |

**`st`** (st_regression, n = 22; pair B0 → B2)

| Module | BR | B0 | B1 | B2 | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 6043 | 5050 | — | 3250 | 0.64 | 0.72 [0.16, 0.89] |
| M2 | 6043 | 5050 | — | 3373 | 0.67 | 0.72 [0.17, 0.96] |
| M3 | 6043 | 5050 | — | 3324 | 0.66 | 0.73 [0.17, 0.93] |
| Feedforward | — | — | — | — | — | — |
| Post-processing | 6043 | 5050 | — | 1 | 0.00 | 0.00 [0.00, 0.00] |

```latex
\begin{tabular}{l|cccc|cc}
\hline
Module & BR & B0 & B1 & B2 & B2/B0 & B2/B0 med [min, max] \\
\hline
\multicolumn{7}{l}{\texttt{tok} ($n = 22$, B2/B0)} \\
\hline
M1              & 1977 & 2027 & 2040 & 1388 & 0.68 & 0.69 [0.60, 0.80] \\
M2              & 1977 & 2027 & 2040 & 1761 & 0.87 & 0.88 [0.76, 1.01] \\
M3              & 1977 & 2027 & 2040 & 1541 & 0.76 & 0.77 [0.66, 0.89] \\
Feedforward     & 1977 & 2027 & 2040 & 640 & 0.32 & 0.32 [0.28, 0.37] \\
Post-processing & 1977 & 2027 & 2040 & 1 & 0.00 & 0.00 [0.00, 0.00] \\
\hline
\multicolumn{7}{l}{\texttt{lad} ($n = 11$, B2/B0)} \\
\hline
M1              & 8095 & 7859 & 5436 & 3670 & 0.47 & 0.54 [0.08, 4.13] \\
M2              & 8095 & 7859 & 5436 & 4660 & 0.59 & 0.69 [0.11, 5.24] \\
M3              & 8095 & 7859 & 5436 & 4273 & 0.54 & 0.63 [0.10, 4.80] \\
Feedforward     & 8095 & 7859 & 5436 & 1714 & 0.22 & 0.25 [0.04, 1.93] \\
Post-processing & 8095 & 7859 & 5436 & 1 & 0.00 & 0.00 [0.00, 0.00] \\
\hline
\multicolumn{7}{l}{\texttt{st} ($n = 22$, B2/B0)} \\
\hline
M1              & 6043 & 5050 & -- & 3250 & 0.64 & 0.72 [0.16, 0.89] \\
M2              & 6043 & 5050 & -- & 3373 & 0.67 & 0.72 [0.17, 0.96] \\
M3              & 6043 & 5050 & -- & 3324 & 0.66 & 0.73 [0.17, 0.93] \\
Feedforward     & -- & -- & -- & -- & -- & -- \\
Post-processing & 6043 & 5050 & -- & 1 & 0.00 & 0.00 [0.00, 0.00] \\
\hline
\end{tabular}
```

## Appendix

### Tables — wall clock (plan §6)

**Context, never evidence (D33).** The wall-clock instrument of plan §6 (list item 9, driver change DR12, A101 (v5-timers-and-once)): observation-only timers in the driver copy (`PROCESS_ARCH_TIMERS=on`) per node, block loop, evaluation and run, harvested into every campaign record, with the launcher's independent wall beside. Excluded from every cell and measured separately: the exit-audit sweep, the state snapshots, the record assembly and the harness's set-up before the run. The rows are `harness/measurement/timing.py`'s; the repeatability stage (three repetitions at W = 1) and D38's validity check are that module's stages and their records say whether the campaign's timings may be printed here. The phase A rows are **warmed** (A102 (v5-campaign), plan §6): the evaluation child runs a discarded warm-up evaluation on the same entry, re-enters the entry bit-exact, resets the counters and times the measured evaluation, so the module rows carry no numba cache load; the fixed per-run term (process start to the warm-up's first evaluation) is stamped in every record and is not a row of the phase A table.

**Where these timings come from (D38).** The validity check (`--timing validity`, at `a1db0a0c`) found 0 of the campaign's timings of the repeatability seeds within the W = 1 repetitions' range and 0 outside. Every timing is the campaign's own, made with several workers at once and reported with its spread (D42, the user, 2026-09-30: the one-worker pass D38 would send no phase to is not run; the table below is the check's own rows); the worker counts the records are stamped with: W = 3. Phase B is over the count tables' seed set (every arm at an accepted optimum; D41).

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

**phase B in wall clock, s per optimisation** — As the phase A table, per whole optimisation in seconds, with the optimiser's own time (solve-phase wall less every evaluation) and the fixed per-run term (process start, imports, numba cache load, input parse, output writing, the once-per-run schedule derivation); Total is the run's wall less the harness-only costs (plan §6). **The module rows include one numba cache load per run**: a phase B run's first evaluation is not warmed (the fixed per-run term ends at its start), so its module rows carry the per-process cache load the warmed phase A records measure as warm-up less measured model time — a median of 0.24–0.40 s per run over the 11 configuration and arm rows, 0.9–3.2 % of the median module time per run of the arm's phase B twin, the same order in every arm (`--timing cache-load`, record at `a1db0a0c`).

**cost breakdown, phase B** — Per configuration and arm: seconds per optimisation and ms per evaluation with the share of the total. Whether the architecture changes the overhead is read off the B0 and B2 columns of the per-sweep rows, normalised per evaluation (plan §6).

**`large_tokamak_nof` — phase A in wall clock, ms per evaluation** (pair A2/A1, 25 pair(s); W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | AR (n=25) | A0 (n=25) | A1 (n=25) | A2 (n=25) | A2/A1 | A2/A1 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 17.34 | 18.69 | 17.95 | 13.08 | 0.73 | 0.73 [0.46, 1.24] |
| M2 | 17.85 | 19.05 | 18.28 | 17.19 | 0.94 | 0.93 [0.56, 1.62] |
| M3 | 3.71 | 3.90 | 3.77 | 2.15 | 0.57 | 0.56 [0.29, 1.14] |
| Feedforward | 0.05 | 0.06 | 0.05 | 0.02 | 0.32 | 0.36 [0.13, 0.71] |
| Post-processing | 1.05 | 1.12 | 1.09 | 0.34 | 0.31 | 0.30 [0.18, 0.55] |
| MDA convergence test | 0.23 | 26.46 | 25.14 | 19.88 | 0.79 | 0.77 [0.51, 1.36] |
| dispatch | 0.75 | 0.85 | 0.83 | 1.36 | 1.65 | 1.61 [1.10, 3.12] |
| objective and constraints | 0.92 | 0.25 | 0.24 | 0.21 | 0.89 | 0.92 [0.39, 1.93] |
| unattributed residual | 0.20 | 0.32 | 0.30 | 0.35 | 1.17 | 1.13 [0.67, 2.63] |
| Total | 42.09 | 70.75 | 67.71 | 54.64 | 0.81 | 0.79 [0.54, 1.36] |

**`large_tokamak_nof` — phase B in wall clock, s per optimisation** (pair B2/B0, 22 pair(s); W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | BR (n=22) | B0 (n=22) | B1 (n=22) | B2 (n=22) | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 6.69 | 7.54 | 7.41 | 5.06 | 0.67 | 0.69 [0.53, 0.84] |
| M2 | 6.52 | 7.25 | 7.14 | 6.09 | 0.84 | 0.87 [0.66, 1.08] |
| M3 | 1.37 | 1.52 | 1.49 | 1.11 | 0.73 | 0.73 [0.57, 0.95] |
| Feedforward | 0.02 | 0.02 | 0.02 | 0.01 | 0.34 | 0.35 [0.24, 0.46] |
| Post-processing | 0.39 | 0.42 | 0.42 | 0.00 | 0.00 | 0.00 [0.00, 0.00] |
| MDA convergence test | 0.08 | 10.63 | 10.48 | 8.22 | 0.77 | 0.79 [0.63, 1.01] |
| dispatch | 0.23 | 0.30 | 0.31 | 0.55 | 1.80 | 1.89 [1.25, 2.38] |
| objective and constraints | 0.33 | 0.14 | 0.14 | 0.14 | 1.02 | 1.01 [0.52, 2.01] |
| optimiser own time | 0.15 | 0.11 | 0.10 | 0.10 | 0.92 | 0.95 [0.45, 2.56] |
| fixed per run | 5.11 | 5.28 | 4.59 | 4.62 | 0.88 | 0.88 [0.73, 1.02] |
| unattributed residual | 0.03 | 0.11 | 0.11 | 0.15 | 1.35 | 1.42 [0.92, 1.96] |
| Total | 20.92 | 33.33 | 32.21 | 26.05 | 0.78 | 0.80 [0.62, 0.94] |

**`large_tokamak_nof` — cost breakdown, phase B** (s per optimisation, the per-unit figure, share of Total; W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | BR: s · per · share | B0: s · per · share | B1: s · per · share | B2: s · per · share |
|---|---|---|---|---|
| model evaluation (the modules summed) | 14.99 · 24.41 ms per evaluation · 71.6 % | 16.76 · 27.25 ms per evaluation · 50.2 % | 16.47 · 25.74 ms per evaluation · 51.1 % | 12.27 · 19.18 ms per evaluation · 47.1 % |
| MDA overhead per sweep: convergence test | 0.08 · 0.04 ms per sweep · 0.4 % | 10.63 · 5.24 ms per sweep · 31.9 % | 10.48 · 5.14 ms per sweep · 32.5 % | 8.22 · 1.54 ms per sweep · 31.5 % |
| MDA overhead per sweep: dispatch | 0.23 · 0.12 ms per sweep · 1.1 % | 0.30 · 0.15 ms per sweep · 0.9 % | 0.31 · 0.15 ms per sweep · 1.0 % | 0.55 · 0.10 ms per sweep · 2.1 % |
| optimiser overhead per iteration | 0.15 · 19.83 ms per iteration · 0.7 % | 0.11 · 14.34 ms per iteration · 0.3 % | 0.10 · 12.23 ms per iteration · 0.3 % | 0.10 · 13.28 ms per iteration · 0.4 % |
| fixed per run | 5.11 · 5.11 s per run · 24.4 % | 5.28 · 5.28 s per run · 15.9 % | 4.59 · 4.59 s per run · 14.3 % | 4.62 · 4.62 s per run · 17.8 % |
| Total | 20.92 · 34.10 ms per evaluation · 100.0 % | 33.33 · 54.26 ms per evaluation · 100.0 % | 32.21 · 50.37 ms per evaluation · 100.0 % | 26.05 · 40.76 ms per evaluation · 100.0 % |

**`low_aspect_ratio_DEMO` — phase A in wall clock, ms per evaluation** (pair A2/A1, 25 pair(s); W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | AR (n=25) | A0 (n=25) | A1 (n=25) | A2 (n=25) | A2/A1 | A2/A1 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 15.73 | 18.07 | 16.48 | 13.09 | 0.79 | 0.76 [0.42, 1.31] |
| M2 | 16.73 | 19.02 | 17.58 | 16.14 | 0.92 | 0.90 [0.52, 1.67] |
| M3 | 3.30 | 4.03 | 3.43 | 2.08 | 0.61 | 0.56 [0.25, 1.55] |
| Feedforward | 0.04 | 0.06 | 0.04 | 0.02 | 0.41 | 0.41 [0.21, 1.12] |
| Post-processing | 0.91 | 1.09 | 0.96 | 0.33 | 0.34 | 0.34 [0.15, 0.65] |
| MDA convergence test | 0.17 | 26.22 | 23.35 | 19.22 | 0.82 | 0.82 [0.41, 1.61] |
| dispatch | 0.62 | 0.80 | 0.75 | 1.31 | 1.75 | 1.90 [0.84, 3.81] |
| objective and constraints | 0.79 | 0.25 | 0.24 | 0.21 | 0.89 | 0.96 [0.46, 1.32] |
| unattributed residual | 0.18 | 0.29 | 0.28 | 0.36 | 1.28 | 1.43 [0.52, 3.08] |
| Total | 38.47 | 69.89 | 63.18 | 52.82 | 0.84 | 0.85 [0.43, 1.52] |

**`low_aspect_ratio_DEMO` — phase B in wall clock, s per optimisation** (pair B2/B0, 11 pair(s); W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | BR (n=11) | B0 (n=11) | B1 (n=11) | B2 (n=11) | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 27.62 | 27.17 | 18.54 | 12.68 | 0.47 | 0.57 [0.08, 4.11] |
| M2 | 28.65 | 27.88 | 19.03 | 16.43 | 0.59 | 0.71 [0.10, 5.22] |
| M3 | 5.89 | 5.60 | 3.81 | 3.02 | 0.54 | 0.65 [0.09, 4.89] |
| Feedforward | 0.07 | 0.07 | 0.04 | 0.02 | 0.25 | 0.30 [0.04, 2.30] |
| Post-processing | 1.64 | 1.53 | 1.03 | 0.00 | 0.00 | 0.00 [0.00, 0.00] |
| MDA convergence test | 0.32 | 40.16 | 27.25 | 21.83 | 0.54 | 0.65 [0.09, 4.98] |
| dispatch | 0.97 | 1.08 | 0.74 | 1.37 | 1.27 | 1.60 [0.22, 11.59] |
| objective and constraints | 1.42 | 0.50 | 0.36 | 0.37 | 0.75 | 0.75 [0.17, 7.01] |
| optimiser own time | 0.38 | 0.31 | 0.23 | 0.24 | 0.77 | 0.78 [0.13, 6.36] |
| fixed per run | 5.46 | 5.19 | 4.44 | 4.48 | 0.86 | 0.86 [0.80, 0.99] |
| unattributed residual | 0.23 | 0.47 | 0.31 | 0.42 | 0.88 | 1.13 [0.14, 9.36] |
| Total | 72.64 | 109.97 | 75.78 | 60.86 | 0.55 | 0.67 [0.10, 4.34] |

**`low_aspect_ratio_DEMO` — cost breakdown, phase B** (s per optimisation, the per-unit figure, share of Total; W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | BR: s · per · share | B0: s · per · share | B1: s · per · share | B2: s · per · share |
|---|---|---|---|---|
| model evaluation (the modules summed) | 63.87 · 27.54 ms per evaluation · 83.5 % | 62.26 · 26.49 ms per evaluation · 54.9 % | 42.46 · 25.03 ms per evaluation · 55.0 % | 32.14 · 18.87 ms per evaluation · 51.7 % |
| MDA overhead per sweep: convergence test | 0.32 · 0.04 ms per sweep · 0.4 % | 40.16 · 5.08 ms per sweep · 35.1 % | 27.25 · 5.04 ms per sweep · 35.2 % | 21.83 · 1.52 ms per sweep · 34.9 % |
| MDA overhead per sweep: dispatch | 0.97 · 0.12 ms per sweep · 1.3 % | 1.08 · 0.14 ms per sweep · 0.9 % | 0.74 · 0.14 ms per sweep · 1.0 % | 1.37 · 0.10 ms per sweep · 2.2 % |
| optimiser overhead per iteration | 0.38 · 14.79 ms per iteration · 0.6 % | 0.31 · 10.82 ms per iteration · 0.3 % | 0.23 · 11.00 ms per iteration · 0.3 % | 0.24 · 12.05 ms per iteration · 0.4 % |
| fixed per run | 5.46 · 5.46 s per run · 12.1 % | 5.19 · 5.19 s per run · 7.9 % | 4.44 · 4.44 s per run · 7.7 % | 4.48 · 4.48 s per run · 9.5 % |
| Total | 72.64 · 33.15 ms per evaluation · 100.0 % | 109.97 · 48.35 ms per evaluation · 100.0 % | 75.78 · 45.54 ms per evaluation · 100.0 % | 60.86 · 36.54 ms per evaluation · 100.0 % |

**`st_regression` — phase A in wall clock, ms per evaluation** (pair A2/A0, 25 pair(s); W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | AR (n=25) | A0 (n=25) | A1 (n=0) | A2 (n=25) | A2/A0 | A2/A0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 15.60 | 19.08 | — | 12.53 | 0.66 | 0.68 [0.39, 0.87] |
| M2 | 14.72 | 17.40 | — | 16.05 | 0.92 | 0.95 [0.61, 1.16] |
| M3 | 3.79 | 4.53 | — | 2.18 | 0.48 | 0.51 [0.28, 0.63] |
| Feedforward | 0.00 | 0.00 | — | 0.00 | — | — |
| Post-processing | 0.86 | 1.06 | — | 0.28 | 0.26 | 0.28 [0.15, 0.36] |
| MDA convergence test | 0.16 | 26.67 | — | 18.51 | 0.69 | 0.73 [0.43, 0.81] |
| dispatch | 0.54 | 0.69 | — | 1.20 | 1.73 | 1.78 [0.90, 2.65] |
| objective and constraints | 0.64 | 0.17 | — | 0.16 | 0.94 | 0.94 [0.67, 1.61] |
| unattributed residual | 0.14 | 0.25 | — | 0.34 | 1.39 | 1.35 [0.72, 2.58] |
| Total | 36.44 | 69.92 | — | 51.29 | 0.73 | 0.77 [0.46, 0.86] |

**`st_regression` — phase B in wall clock, s per optimisation** (pair B2/B0, 22 pair(s); W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | BR (n=22) | B0 (n=22) | B1 (n=0) | B2 (n=22) | B2/B0 | B2/B0 med [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 20.37 | 17.64 | — | 11.09 | 0.63 | 0.69 [0.16, 0.91] |
| M2 | 19.93 | 16.89 | — | 11.10 | 0.66 | 0.69 [0.17, 1.00] |
| M3 | 5.01 | 4.17 | — | 2.68 | 0.64 | 0.70 [0.16, 0.96] |
| Feedforward | 0.00 | 0.00 | — | 0.00 | — | — |
| Post-processing | 1.17 | 0.98 | — | 0.00 | 0.00 | 0.00 [0.00, 0.00] |
| MDA convergence test | 0.22 | 24.92 | — | 16.58 | 0.67 | 0.71 [0.17, 1.01] |
| dispatch | 0.62 | 0.64 | — | 1.00 | 1.57 | 1.61 [0.39, 2.49] |
| objective and constraints | 0.81 | 0.25 | — | 0.22 | 0.86 | 0.89 [0.22, 1.31] |
| optimiser own time | 0.29 | 0.24 | — | 0.24 | 0.99 | 0.99 [0.21, 1.84] |
| fixed per run | 5.19 | 5.17 | — | 4.60 | 0.89 | 0.89 [0.76, 1.03] |
| unattributed residual | 0.13 | 0.30 | — | 0.34 | 1.12 | 1.11 [0.24, 1.84] |
| Total | 53.73 | 71.20 | — | 47.83 | 0.67 | 0.72 [0.19, 0.98] |

**`st_regression` — cost breakdown, phase B** (s per optimisation, the per-unit figure, share of Total; W = 3 (as stamped); pairing key = the seed; the ratio is of the means over the paired runs and the bracket the per-run ratio's median with [min, max]; exclusions as stated above)

| row | BR: s · per · share | B0: s · per · share | B1: s · per · share | B2: s · per · share |
|---|---|---|---|---|
| model evaluation (the modules summed) | 46.47 · 25.58 ms per evaluation · 80.4 % | 39.68 · 26.93 ms per evaluation · 54.0 % | — | 24.86 · 17.74 ms per evaluation · 50.0 % |
| MDA overhead per sweep: convergence test | 0.22 · 0.04 ms per sweep · 0.4 % | 24.92 · 4.96 ms per sweep · 33.7 % | — | 16.58 · 1.28 ms per sweep · 33.1 % |
| MDA overhead per sweep: dispatch | 0.62 · 0.10 ms per sweep · 1.1 % | 0.64 · 0.13 ms per sweep · 0.9 % | — | 1.00 · 0.08 ms per sweep · 2.0 % |
| optimiser overhead per iteration | 0.29 · 9.51 ms per iteration · 0.5 % | 0.24 · 9.51 ms per iteration · 0.3 % | — | 0.24 · 9.95 ms per iteration · 0.5 % |
| fixed per run | 5.19 · 5.19 s per run · 16.0 % | 5.17 · 5.17 s per run · 10.3 % | — | 4.60 · 4.60 s per run · 13.4 % |
| Total | 53.73 · 32.08 ms per evaluation · 100.0 % | 71.20 · 50.01 ms per evaluation · 100.0 % | — | 47.83 · 35.66 ms per evaluation · 100.0 % |

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
| BR | 25 | 24 | 1 | 0 | 22 | finished, ifail = 5: 17 | — |
| B0 | 25 | 23 | 2 | 1 | 22 | finished, ifail = 5: 10, 17 | 10 |
| B2 | 25 | 23 | 2 | 1 | 22 | finished, ifail = 5: 5, 17 | 5 |

### Table — verification

One row per check of plan §8, in its order. A gate's verdict is read from its record through the `gate_table` stage record, which this generator refuses when the verdict records have been re-made, removed or added to since the stage ran; `not pressed` is a gate with no verdict record (a declared placeholder that refuses, or one never pressed) or a rule that is not yet a construction. A verdict is PASS only with every tooth tripped.

*the gate_table stage record read 28 record(s) at ['58307581301735f53eba73635214ae1b3a8038c0'], and every one of them is byte-identical to what is on disk now*

| check | plan | verdict | detail |
|---|---|---|---|
| physics frozen | G0 | **PASS** | `g0prime` at `58307581`: 1 of 77 mismatched; 4/4 teeth |
| switch neutrality | G1 | **PASS** | `switch_neutrality` at `58307581`: 0 of 54967 mismatched; 9/9 teeth |
| matched accuracy — whole-state audit at 0 components above τ | A1 | **PASS** | `tok` A2/A1: similarity PASS, runs with a component ≥ τ A1 0 / A2 0 → **PASS**; `lad` A2/A1: similarity PASS, runs with a component ≥ τ A1 0 / A2 0 → **PASS**; `st` A2/A0: similarity PASS, runs with a component ≥ τ A0 0 / A2 0 → **PASS** (whole-state statistic, D36; the second half of the rule is the count column) |
| fixed-point distance between arms | A2 | **reported, no rule** | the tally's fixed-point distance table (plan §5 A2) |
| same optimum, attributed where it fails | B1 | **PASS tok, st · FAIL lad** | `tok` B0 → B1 PASS, B0 → B2 PASS (objf p90 4.6e-11 ≤ 1.0e-06; 0 hops of 22); `lad` B0 → B1 FAIL, B0 → B2 FAIL at p90 (objf p90 2.1e-06 > 1.0e-06): 3 hops of 11 (1 across clusters; seeds 1*, 11, 13), entering at B0 → B1 (the lift) 3 of 3; B1 → B2 (the partition) adds none: objf median 0.0e+00, p90 2.7e-14, same path on 11 of 11; the yardstick BR → B0 also hops on 0 of 3 of these seeds; `st` B0 → B2 PASS (objf p90 3.5e-09 ≤ 1.0e-06; 1 hops of 22) (hop: objective difference above the floor; * = a retried arm; the tally's `same optimum by rung` table, plan §5 B1) |
| entry pairing | G6 | **PASS** | `entry_and_warm` at `58307581`: 0 of 6717 mismatched; 3/3 teeth |
| arm composition | G5 | **PASS** | `switch_composition` at `58307581`: 0 of 156 mismatched; 4/4 teeth |
| output-path equivalence | G9 | **PASS** | `output_path` at `58307581`: 0 of 3879 mismatched; 4/4 teeth |
| the test set's teeth | GT | **not pressed** | `test_set` has no verdict record |

