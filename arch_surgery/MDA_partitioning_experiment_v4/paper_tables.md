# Paper tables — Case 2: PROCESS

> **Document status** — **GENERATED, never hand-edited.** Written whole by `harness/measurement/paper_tables.py` (`experiment_runner.py --paper-tables write`) from the campaign's run records, and compared whole by `--paper-tables check`. It fills the three tables of `Structuring-fusion-MDAO-with-DSMs/3 results.tex` (`tab:phaseA_results`, `tab:phaseB_iterations`, `tab:phaseB_results`); each table is given as a Markdown grid and as LaTeX rows for the paper's `tabular` body.

*Over the **campaign** population — 949 run records at `57dc0c14`; sources `campaign_displaced` (phase A) and `campaign_optimisation` (phase B).*

**Conventions (the user, 2026-09-28).** A module cell is that module's **sweeps per run** — per `call_models` evaluation in phase A, per whole optimisation in phase B — averaged over the arm's n perturbed runs. Every model node of a module runs once per sweep, so a sweep ratio does not depend on whether one counts model calls or DSM rows. The ratio column is the **ratio of the means** (Σ intervened / Σ control over the paired runs); the next column is the per-run ratio's median with its [min, max]. **Feedforward** is the pulse node (run once per evaluation after M3, no iteration); **Post-processing** is the once-per-run set — nodes no objective or constraint depends on, which the partitioned arm runs once, after convergence, in the output pass. **Phase A charges `A2` that one execution** (1.0 in its Post-processing cell): the flat arms' final sweep already computes those outputs at the converged state, and without it `A2`'s evaluation would not produce the same information. The charge is by construction — phase A's census stops before the output pass, and `A2`'s measured count there is 0 on every run, which is checked; phase B's census measures the pass (`B2`'s Post-processing reads 1 per run once the exit audit is taken out). There is **no total row**: sweeps of different modules do not add. Rounding follows each quantity's sampling uncertainty over the starts (the counts themselves are exact): phase A sweep means and phase B iteration means to one decimal, phase B module sweeps to integers, every ratio, median and bracket to two decimals. `—` is a group that does not exist on the configuration or an arm that is inactive there (`A1`/`B1` on `st`).

Node groups per configuration (phase A; phase B's are restated in its section only where they differ):

- `tok`: Feedforward = `pulse`; Post-processing = `costs`, `vacuum`, `water_use`
- `lad`: Feedforward = `pulse`; Post-processing = `costs`, `vacuum`, `water_use`
- `st`: Feedforward = — (none); Post-processing = `costs`, `pulse`, `vacuum`, `water_use`

**Comparison with the stage records.** 156 cells these tables share with the report's Tables 9, 12 and 17 (the stage records under the records directory) compared exactly — `A2`'s phase A Post-processing mean before the charge and phase B's module means before the exit audit is taken out; phase B's module ratios have no stage counterpart once it is: **0 mismatched of 156**; the comparison caught a doctored cell on each of the three sides: **yes**. The phase A ratio against `A0` and its per-run distribution have no stage counterpart on the pulsed configurations (the report's reference there is `A1`).

## Table — how the three configurations differ

One row per configuration. Objective, design variables and constraints are the report's problem-definition table (the runs' own stamps); `a → b` is the flat arms (`BR`, `B0`) → the arms with the burn time taken out of the MDA (`B1`, `B2`), which add the burn time as an iteration variable and its consistency constraint. The objective's variable and the cross-module coupling's variable are derived from the committed per-run artifact and the runs.

| Configuration | Objective | Design variables | Constraints | Cross-module coupling |
|---|---|---:|---:|---|
| Large tokamak (`tok`) | min. plasma major radius (`rmajor`) | 20 → 21 | 26 → 27 | `t_plant_pulse_burn` |
| Low aspect ratio DEMO (`lad`) | max. pulse length (`t_plant_pulse_burn`) | 19 → 20 | 25 → 26 | `t_plant_pulse_burn` |
| Spherical tokamak (`st`) | max. fusion gain (`big_q_plasma`) | 14 | 18 | none (steady state) |

```latex
\begin{tabular}{l|l|c|c|l}
\hline
Configuration & Objective & Design variables & Constraints & Cross-module coupling \\
\hline
Large tokamak (\texttt{tok}) & min. plasma major radius (\texttt{rmajor}) & 20 $\rightarrow$ 21 & 26 $\rightarrow$ 27 & \texttt{t\_plant\_pulse\_burn} \\
Low aspect ratio DEMO (\texttt{lad}) & max. pulse length (\texttt{t\_plant\_pulse\_burn}) & 19 $\rightarrow$ 20 & 25 $\rightarrow$ 26 & \texttt{t\_plant\_pulse\_burn} \\
Spherical tokamak (\texttt{st}) & max. fusion gain (\texttt{big\_q\_plasma}) & 14 & 18 & none (steady state) \\
\hline
\end{tabular}
```

## Table `tab:phaseA_results` — phase A, module sweeps per evaluation

Mean sweeps of each module in one `call_models` evaluation over the n displaced-entry runs per arm; `A2/A0` is the ratio of the means over the runs both arms finished.

**`tok`** (large_tokamak_nof, n = 25)

| Module | AR | A0 | A1 | A2 | A2/A0 | A2/A0 median [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 5.0 | 5.5 | 5.1 | 4.0 | 0.72 | 0.67 [0.67, 0.80] |
| M2 | 5.0 | 5.5 | 5.1 | 5.2 | 0.93 | 1.00 [0.83, 1.00] |
| M3 | 5.0 | 5.5 | 5.1 | 3.0 | 0.54 | 0.50 [0.50, 0.60] |
| Feedforward | 5.0 | 5.5 | 5.1 | 1.0 | 0.18 | 0.17 [0.17, 0.20] |
| Post-processing | 5.0 | 5.5 | 5.1 | 1.0 | 0.18 | 0.17 [0.17, 0.20] |

**`lad`** (low_aspect_ratio_DEMO, n = 25)

| Module | AR | A0 | A1 | A2 | A2/A0 | A2/A0 median [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 5.0 | 5.0 | 4.9 | 4.0 | 0.80 | 0.80 [0.80, 0.80] |
| M2 | 5.0 | 5.0 | 4.9 | 4.9 | 0.98 | 1.00 [0.80, 1.00] |
| M3 | 5.0 | 5.0 | 4.9 | 3.0 | 0.60 | 0.60 [0.60, 0.60] |
| Feedforward | 5.0 | 5.0 | 4.9 | 1.0 | 0.20 | 0.20 [0.20, 0.20] |
| Post-processing | 5.0 | 5.0 | 4.9 | 1.0 | 0.20 | 0.20 [0.20, 0.20] |

**`st`** (st_regression, n = 25)

| Module | AR | A0 | A1 | A2 | A2/A0 | A2/A0 median [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 4.9 | 5.8 | — | 4.0 | 0.68 | 0.67 [0.67, 0.80] |
| M2 | 4.9 | 5.8 | — | 5.8 | 1.00 | 1.00 [1.00, 1.00] |
| M3 | 4.9 | 5.8 | — | 3.0 | 0.51 | 0.50 [0.50, 0.60] |
| Feedforward | — | — | — | — | — | — |
| Post-processing | 4.9 | 5.8 | — | 1.0 | 0.17 | 0.17 [0.17, 0.20] |

```latex
\begin{tabular}{l|rrrr|rc}
\hline
Module & AR & A0 & A1 & A2 & A2/A0 & A2/A0 median [min, max] \\
\hline
\multicolumn{7}{l}{\texttt{tok} ($n = 25$)} \\
\hline
M1              & 5.0 & 5.5 & 5.1 & 4.0 & 0.72 & 0.67 [0.67, 0.80] \\
M2              & 5.0 & 5.5 & 5.1 & 5.2 & 0.93 & 1.00 [0.83, 1.00] \\
M3              & 5.0 & 5.5 & 5.1 & 3.0 & 0.54 & 0.50 [0.50, 0.60] \\
Feedforward     & 5.0 & 5.5 & 5.1 & 1.0 & 0.18 & 0.17 [0.17, 0.20] \\
Post-processing & 5.0 & 5.5 & 5.1 & 1.0 & 0.18 & 0.17 [0.17, 0.20] \\
\hline
\multicolumn{7}{l}{\texttt{lad} ($n = 25$)} \\
\hline
M1              & 5.0 & 5.0 & 4.9 & 4.0 & 0.80 & 0.80 [0.80, 0.80] \\
M2              & 5.0 & 5.0 & 4.9 & 4.9 & 0.98 & 1.00 [0.80, 1.00] \\
M3              & 5.0 & 5.0 & 4.9 & 3.0 & 0.60 & 0.60 [0.60, 0.60] \\
Feedforward     & 5.0 & 5.0 & 4.9 & 1.0 & 0.20 & 0.20 [0.20, 0.20] \\
Post-processing & 5.0 & 5.0 & 4.9 & 1.0 & 0.20 & 0.20 [0.20, 0.20] \\
\hline
\multicolumn{7}{l}{\texttt{st} ($n = 25$)} \\
\hline
M1              & 4.9 & 5.8 & -- & 4.0 & 0.68 & 0.67 [0.67, 0.80] \\
M2              & 4.9 & 5.8 & -- & 5.8 & 1.00 & 1.00 [1.00, 1.00] \\
M3              & 4.9 & 5.8 & -- & 3.0 & 0.51 & 0.50 [0.50, 0.60] \\
Feedforward     & -- & -- & -- & -- & -- & -- \\
Post-processing & 4.9 & 5.8 & -- & 1.0 & 0.17 & 0.17 [0.17, 0.20] \\
\hline
\end{tabular}
```

## Table `tab:phaseB_iterations` — phase B, optimiser iterations

Mean optimiser iterations per run, summed over the optimiser's retry attempts, over the n seeds on which every arm reached an accepted optimum; `B2/B0` is the ratio of the means. The same statistic as the report's Table 12.

| Configuration | n | BR | B0 | B1 | B2 | B2/B0 | B2/B0 median [min, max] |
|---|---:|---:|---:|---:|---:|---:|---:|
| `tok` | 22 | 7.8 | 7.8 | 7.8 | 7.8 | 0.99 | 1.00 [0.88, 1.14] |
| `lad` | 11 | 29.8 | 29.8 | 20.9 | 20.9 | 0.70 | 0.81 [0.13, 5.91] |
| `st` | 22 | 31.2 | 25.1 | — | 24.0 | 0.95 | 1.00 [0.25, 1.36] |

```latex
\begin{tabular}{l|rrrr|rc}
\hline
Configuration & BR & B0 & B1 & B2 & B2/B0 & B2/B0 median [min, max] \\
\hline
\texttt{tok} ($n = 22$) & 7.8 & 7.8 & 7.8 & 7.8 & 0.99 & 1.00 [0.88, 1.14] \\
\texttt{lad} ($n = 11$) & 29.8 & 29.8 & 20.9 & 20.9 & 0.70 & 0.81 [0.13, 5.91] \\
\texttt{st} ($n = 22$) & 31.2 & 25.1 & -- & 24.0 & 0.95 & 1.00 [0.25, 1.36] \\
\hline
\end{tabular}
```

## Table `tab:phaseB_results` — phase B, module sweeps per optimisation

Mean sweeps of each module over one whole optimisation, rounded to integers (more digits than the seed-to-seed uncertainty supports). Every attempt and the output path, which is architecture (MDA_Output's sweeps in `BR`/`B0`, none in `B1`, the deferred nodes' one execution in `B2`). The exit audit's one sweep of every node is the harness's accuracy instrument and is **subtracted** (1 per node, checked on each run against the record's `audit_node_calls`); the report's Table 17 includes it. Over the n seeds on which every arm reached an accepted optimum; `B2/B0` is the ratio of the means. The paper prints `tok`; all three are given.

**`tok`** (large_tokamak_nof, n = 22)

| Module | BR | B0 | B1 | B2 | B2/B0 | B2/B0 median [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 1977 | 2027 | 2040 | 1388 | 0.68 | 0.69 [0.60, 0.80] |
| M2 | 1977 | 2027 | 2040 | 1761 | 0.87 | 0.88 [0.76, 1.01] |
| M3 | 1977 | 2027 | 2040 | 1541 | 0.76 | 0.77 [0.66, 0.89] |
| Feedforward | 1977 | 2027 | 2040 | 640 | 0.32 | 0.32 [0.28, 0.37] |
| Post-processing | 1977 | 2027 | 2040 | 1 | 0.00 | 0.00 [0.00, 0.00] |

**`lad`** (low_aspect_ratio_DEMO, n = 11)

| Module | BR | B0 | B1 | B2 | B2/B0 | B2/B0 median [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 8095 | 7859 | 5436 | 3670 | 0.47 | 0.54 [0.08, 4.13] |
| M2 | 8095 | 7859 | 5436 | 4660 | 0.59 | 0.69 [0.11, 5.24] |
| M3 | 8095 | 7859 | 5436 | 4273 | 0.54 | 0.63 [0.10, 4.80] |
| Feedforward | 8095 | 7859 | 5436 | 1714 | 0.22 | 0.25 [0.04, 1.93] |
| Post-processing | 8095 | 7859 | 5436 | 1 | 0.00 | 0.00 [0.00, 0.00] |

**`st`** (st_regression, n = 22)

| Module | BR | B0 | B1 | B2 | B2/B0 | B2/B0 median [min, max] |
|---|---:|---:|---:|---:|---:|---:|
| M1 | 6043 | 5050 | — | 3250 | 0.64 | 0.72 [0.16, 0.89] |
| M2 | 6043 | 5050 | — | 3373 | 0.67 | 0.72 [0.17, 0.96] |
| M3 | 6043 | 5050 | — | 3324 | 0.66 | 0.73 [0.17, 0.93] |
| Feedforward | — | — | — | — | — | — |
| Post-processing | 6043 | 5050 | — | 1 | 0.00 | 0.00 [0.00, 0.00] |

```latex
\begin{tabular}{l|cccc|cc}
\hline
Module & BR & B0 & B1 & B2 & B2/B0 & B2/B0 median [min, max] \\
\hline
\multicolumn{7}{l}{\texttt{tok} ($n = 22$)} \\
\hline
M1              & 1977 & 2027 & 2040 & 1388 & 0.68 & 0.69 [0.60, 0.80] \\
M2              & 1977 & 2027 & 2040 & 1761 & 0.87 & 0.88 [0.76, 1.01] \\
M3              & 1977 & 2027 & 2040 & 1541 & 0.76 & 0.77 [0.66, 0.89] \\
Feedforward     & 1977 & 2027 & 2040 & 640 & 0.32 & 0.32 [0.28, 0.37] \\
Post-processing & 1977 & 2027 & 2040 & 1 & 0.00 & 0.00 [0.00, 0.00] \\
\hline
\multicolumn{7}{l}{\texttt{lad} ($n = 11$)} \\
\hline
M1              & 8095 & 7859 & 5436 & 3670 & 0.47 & 0.54 [0.08, 4.13] \\
M2              & 8095 & 7859 & 5436 & 4660 & 0.59 & 0.69 [0.11, 5.24] \\
M3              & 8095 & 7859 & 5436 & 4273 & 0.54 & 0.63 [0.10, 4.80] \\
Feedforward     & 8095 & 7859 & 5436 & 1714 & 0.22 & 0.25 [0.04, 1.93] \\
Post-processing & 8095 & 7859 & 5436 & 1 & 0.00 & 0.00 [0.00, 0.00] \\
\hline
\multicolumn{7}{l}{\texttt{st} ($n = 22$)} \\
\hline
M1              & 6043 & 5050 & -- & 3250 & 0.64 & 0.72 [0.16, 0.89] \\
M2              & 6043 & 5050 & -- & 3373 & 0.67 & 0.72 [0.17, 0.96] \\
M3              & 6043 & 5050 & -- & 3324 & 0.66 & 0.73 [0.17, 0.93] \\
Feedforward     & -- & -- & -- & -- & -- & -- \\
Post-processing & 6043 & 5050 & -- & 1 & 0.00 & 0.00 [0.00, 0.00] \\
\hline
\end{tabular}
```

## How the optimiser's evaluations decompose (phase B)

Every point VMCON evaluates costs `k = 2·nvar + 2` model evaluations: one function evaluation, a central-difference gradient (`2·nvar`) and one reconcile call. An iteration evaluates its iterate and its line-search point, so a run of `it` iterations whose line searches accept their first trial makes `ε = (2·it − 1)·k`. *exact* counts the runs on which that holds with no further trial; *repeated* is the share of all evaluations spent re-evaluating an accepted line-search point at the next iteration's head, `Σ (it − 1)·k / Σ ε`. Over the phase B seed set; *exact*, the extra trials and *repeated* are over the runs solved in one attempt (a failed attempt may end before or after its line search), the retried runs counted apart.

| Configuration | arm | n | nvar | FD calls per gradient | evaluations per point k | mean iterations | mean ε | ε divisible by k | retried runs | exact | extra line-search trials | FD share | repeated share |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `tok` | BR | 22 | 20 | 40 | 42 | 7.8 | 610 | 22/22 | 0 | 22/22 | 0 | 0.95 | 0.47 |
| `tok` | B0 | 22 | 20 | 40 | 42 | 7.8 | 610 | 22/22 | 0 | 22/22 | 0 | 0.95 | 0.47 |
| `tok` | B1 | 22 | 21 | 42 | 44 | 7.8 | 640 | 22/22 | 0 | 22/22 | 0 | 0.95 | 0.47 |
| `tok` | B2 | 22 | 21 | 42 | 44 | 7.8 | 640 | 22/22 | 0 | 22/22 | 0 | 0.95 | 0.47 |
| `lad` | BR | 11 | 19 | 38 | 40 | 29.8 | 2300 | 11/11 | 1 | 10/10 | 0 | 0.95 | 0.49 |
| `lad` | B0 | 11 | 19 | 38 | 40 | 29.8 | 2300 | 11/11 | 1 | 10/10 | 0 | 0.95 | 0.49 |
| `lad` | B1 | 11 | 20 | 40 | 42 | 20.9 | 1700 | 11/11 | 0 | 11/11 | 0 | 0.95 | 0.49 |
| `lad` | B2 | 11 | 20 | 40 | 42 | 20.9 | 1700 | 11/11 | 0 | 11/11 | 0 | 0.95 | 0.49 |
| `st` | BR | 22 | 14 | 28 | 30 | 31.2 | 1800 | 22/22 | 3 | 19/19 | 0 | 0.93 | 0.49 |
| `st` | B0 | 22 | 14 | 28 | 30 | 25.1 | 1500 | 22/22 | 1 | 21/21 | 0 | 0.93 | 0.49 |
| `st` | B2 | 22 | 14 | 28 | 30 | 24.0 | 1400 | 22/22 | 0 | 22/22 | 0 | 0.93 | 0.49 |

