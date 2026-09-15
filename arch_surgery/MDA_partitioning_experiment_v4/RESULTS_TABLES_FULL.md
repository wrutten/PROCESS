# Results tables — the full result matrices

> **Document status** — **GENERATED, never hand-edited.** Written whole by `harness/measurement/plan_tables.py` (`experiment_runner.py --plan-tables write`) from the same stage records as the report's Appendix D, and compared whole by `--plan-tables check`. It holds every table with a row per run, seed, pair of runs or predicate evaluation, and the full versions of the report's tables whose per-seed columns the report omits — **one construction, one table**, with the configurations and source regimes as row groups under a bold sub-heading row naming the group and stating its own n. The second implementation's recomputed copies are not rendered here: gate `recomputation`'s row of the report's Table D.1 is that check, and the gate's record holds the cells. Tables are numbered `Table F.n` in the order printed; the report cites them by that number and traces a cell by the construction names printed under each grid. Populations, constructions and conventions are the report's Appendix D.0's, not repeated here. Arm names are today's (`AR/A0/A1/A2`, `BR/B0/B1/B2`); the records carry the names of their day (trap T16).

*Rendered from the **campaign** population — 949 run records at `57dc0c14`.*

## F.1 The evaluation phase — one row per run

The per-run tables of the evaluation phase, one construction per table with the configurations and regimes as row groups: what each finished run's convergence test cost (one row per run; the two predicates in columns of their own, never summed) and the predicate trial (one row per pair of runs under the two rulers). Populations and constructions are as declared in Appendix D.0 of the report.

**Table F.1.** *Check 1's grid at the two **stencil** entry points — the optimiser's own finite-difference points, one per design-vector column, paired across arms by column — in the report's form. These are not the acceptance regime: the displaced entries are, and their table is in §4.2. A stencil point is a far smaller displacement, so a ratio there is over two very small numbers and swings widely; the verdict column is printed for completeness and the regime is not one the plan accepts on. n = 2 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and source regime and its own n, and that n counts finished evaluation-phase campaign runs over every configuration in this source).*

| configuration | n (runs) | AR | A0 | A1 | A2 | reference | A2/A1 med | A2/A1 p90 | A2/A1 verdict | A2/A0 med | A2/A0 p90 | A2/A0 verdict | verdict note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **campaign_stencil_forward (n = 198)** |  |  |  |  |  |  |  |  |  |  |  |  |  |
| large_tokamak_nof | 80 | 2.974e-12 / 1.869e-08 | 2.974e-12 / 3.592e-10 | 4.523e-13 / 2.783e-09 | 2.363e-11 / 2.783e-09 | A1 | 52.2421 | 1.0000 | **FAIL** | 7.9446 | 7.7491 | **PASS** | declared pair A2/A1 |
| low_aspect_ratio_DEMO | 76 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | A1 | — | — | **PASS** | — | — | **PASS** | A2/A1: both quantiles exactly 0 — the trivially-similar clause |
| st_regression | 42 | 3.779e-11 / 3.920e-07 | 3.779e-11 / 2.137e-08 | — / — | 1.116e-10 / 2.137e-08 | A0 | — | — | — | 2.9533 | 1.0000 | **PASS** | declared pair A2/A0 |
| **campaign_stencil_backward (n = 198)** |  |  |  |  |  |  |  |  |  |  |  |  |  |
| large_tokamak_nof | 80 | 5.339e-15 / 1.730e-10 | 0 / 5.339e-15 | 0 / 8.309e-16 | 8.309e-16 / 4.523e-13 | A1 | — | 544.3285 | **FAIL** | — | 84.7128 | **FAIL** | A2/A1: one side exactly 0 and the other not: unbounded |
| low_aspect_ratio_DEMO | 76 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | A1 | — | — | **PASS** | — | — | **PASS** | A2/A1: both quantiles exactly 0 — the trivially-similar clause |
| st_regression | 42 | 6.459e-14 / 4.272e-08 | 0 / 2.670e-08 | — / — | 1.560e-11 / 2.670e-08 | A0 | — | — | — | — | 1.0000 | **FAIL** | A2/A0: one side exactly 0 and the other not: unbounded |

<sub>`check 1, matched accuracy, the stencil regimes`</sub>

<sub>combining 2 stage table(s): `matched accuracy by configuration — campaign_stencil_forward`; `matched accuracy by configuration — campaign_stencil_backward`</sub>

**Table F.2.** *Per-call cost at the two **stencil** entry points, in the report's form: mean node calls per evaluation with the observed bracket, the ladder's rungs as pooled ratios, and the partitioned arm's prime calls per evaluation. Pairs are keyed by design-vector column here, not by seed. n = 2 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and source regime and its own n, and that n counts finished evaluation-phase campaign runs over every configuration in this source).*

| configuration | n (runs) | AR | A0 | A1 | A2 | AR→A0 | A0→A1 | A1→A2 | A0→A2 | reference | A2 prime calls / eval | pairs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **campaign_stencil_forward (n = 198)** |  |  |  |  |  |  |  |  |  |  |  |  |
| large_tokamak_nof | 80 | 62.0 [42, 84] | 66.2 [42, 105] | 63.0 [42, 105] | 39.1 [20, 55] | 1.0678 | 0.9524 | **0.6214** | — | A1 | 7.6 | 20 |
| low_aspect_ratio_DEMO | 76 | 67.4 [42, 105] | 66.3 [42, 105] | 63.0 [42, 84] | 40.3 [33, 55] | 0.9836 | 0.9500 | **0.6399** | — | A1 | 7.6 | 19 |
| st_regression | 42 | 63.0 [42, 84] | 67.5 [42, 84] | — | 38.9 [19, 50] | 1.0714 | — | — | **0.5767** | A0 | 8.6 | 14 |
| **campaign_stencil_backward (n = 198)** |  |  |  |  |  |  |  |  |  |  |  |  |
| large_tokamak_nof | 80 | 60.9 [42, 84] | 66.2 [42, 105] | 63.0 [42, 105] | 40.4 [20, 55] | 1.0862 | 0.9524 | **0.6405** | — | A1 | 7.7 | 20 |
| low_aspect_ratio_DEMO | 76 | 67.4 [42, 105] | 68.5 [42, 105] | 64.1 [42, 84] | 42.4 [33, 55] | 1.0164 | 0.9355 | **0.6609** | — | A1 | 7.8 | 19 |
| st_regression | 42 | 66.0 [42, 84] | 70.5 [42, 105] | — | 39.4 [19, 53] | 1.0682 | — | — | **0.5583** | A0 | 8.8 | 14 |

<sub>`per-call cost, the stencil regimes`</sub>

<sub>combining 2 stage table(s): `per-call cost by configuration — campaign_stencil_forward`; `per-call cost by configuration — campaign_stencil_backward`</sub>

**Table F.3.** ***Module sweeps per run** in the three regimes the report's table does not show — the entry reference and the forward and backward stencil points — one block per configuration and regime, in the same form: the mean with its [min, max] bracket, a bare integer where every run agreed, `models` the group's collapsed-DSM row count, the total Σ sweeps × models with its `[v = 1, v = 0]` interval. The entry reference carries one `A0` run per configuration and so no pair and no ratio. n = 9 (block(s) of this table, each over its own population with its own n in its heading line; never pooled).*

**`nof`** (n = 1 per arm)

| module | models | AR | A0 | A1 | A2 | reference | A2 / reference | pairs |
|---|---|---|---|---|---|---|---|---|
| M1 | 24 | — | 6 | — | — | A0 | — | 0 |
| M2 | 10 | — | 6 | — | — | A0 | — | 0 |
| M3 | 11 | — | 6 | — | — | A0 | — | 0 |
| PULSE | 1 | — | 6 | — | — | A0 | — | 0 |
| once per run | 3 | — | 6 | — | — | A0 | — | 0 |
| total calls | 49 | — | 294 | — | — | A0 | — | 0 |

**`lad`** (n = 1 per arm)

| module | models | AR | A0 | A1 | A2 | reference | A2 / reference | pairs |
|---|---|---|---|---|---|---|---|---|
| M1 | 24 | — | 5 | — | — | A0 | — | 0 |
| M2 | 10 | — | 5 | — | — | A0 | — | 0 |
| M3 | 11 | — | 5 | — | — | A0 | — | 0 |
| PULSE | 1 | — | 5 | — | — | A0 | — | 0 |
| once per run | 3 | — | 5 | — | — | A0 | — | 0 |
| total calls | 49 | — | 245 | — | — | A0 | — | 0 |

**`st`** (n = 1 per arm)

| module | models | AR | A0 | A1 | A2 | reference | A2 / reference | pairs |
|---|---|---|---|---|---|---|---|---|
| M1 | 24 | — | 7 | — | — | A0 | — | 0 |
| M2 | 10 | — | 7 | — | — | A0 | — | 0 |
| M3 | 11 | — | 7 | — | — | A0 | — | 0 |
| once per run | 4 | — | 7 | — | — | A0 | — | 0 |
| total calls | 49 | — | 343 | — | — | A0 | — | 0 |

**`nof`** (n = 20 per arm)

| module | models | AR | A0 | A1 | A2 | reference | A2 / reference | pairs |
|---|---|---|---|---|---|---|---|---|
| M1 | 24 | 2.95 [2, 4] | 3.15 [2, 5] | 3 [2, 5] | 1.9 [1, 3] | A1 | **0.6333** | 20 |
| M2 | 10 | 2.95 [2, 4] | 3.15 [2, 5] | 3 [2, 5] | 2.45 [1, 5] | A1 | **0.8167** | 20 |
| M3 | 11 | 2.95 [2, 4] | 3.15 [2, 5] | 3 [2, 5] | 2.25 [1, 3] | A1 | **0.7500** | 20 |
| PULSE | 1 | 2.95 [2, 4] | 3.15 [2, 5] | 3 [2, 5] | 1 | A1 | **0.3333** | 20 |
| once per run | 3 | 2.95 [2, 4] | 3.15 [2, 5] | 3 [2, 5] | 0 | A1 | **0.0000** | 20 |
| total calls | 49 | 144.6 | 154.3 | 147 | 95.85 | A1 | **[0.652, 0.696]** | 20 |

**`lad`** (n = 19 per arm)

| module | models | AR | A0 | A1 | A2 | reference | A2 / reference | pairs |
|---|---|---|---|---|---|---|---|---|
| M1 | 24 | 3.211 [2, 5] | 3.158 [2, 5] | 3 [2, 4] | 1.895 [1, 3] | A1 | **0.6316** | 19 |
| M2 | 10 | 3.211 [2, 5] | 3.158 [2, 5] | 3 [2, 4] | 2.368 [1, 4] | A1 | **0.7895** | 19 |
| M3 | 11 | 3.211 [2, 5] | 3.158 [2, 5] | 3 [2, 4] | 2.368 [2, 3] | A1 | **0.7895** | 19 |
| PULSE | 1 | 3.211 [2, 5] | 3.158 [2, 5] | 3 [2, 4] | 1 | A1 | **0.3333** | 19 |
| once per run | 3 | 3.211 [2, 5] | 3.158 [2, 5] | 3 [2, 4] | 0 | A1 | **0.0000** | 19 |
| total calls | 49 | 157.3 | 154.7 | 147 | 96.21 | A1 | **[0.654, 0.699]** | 19 |

**`st`** (n = 14 per arm)

| module | models | AR | A0 | A1 | A2 | reference | A2 / reference | pairs |
|---|---|---|---|---|---|---|---|---|
| M1 | 24 | 3 [2, 4] | 3.214 [2, 4] | — | 2.214 [1, 4] | A0 | **0.6889** | 14 |
| M2 | 10 | 3 [2, 4] | 3.214 [2, 4] | — | 2.071 [1, 4] | A0 | **0.6444** | 14 |
| M3 | 11 | 3 [2, 4] | 3.214 [2, 4] | — | 2.357 [1, 3] | A0 | **0.7333** | 14 |
| once per run | 4 | 3 [2, 4] | 3.214 [2, 4] | — | 0 | A0 | **0.0000** | 14 |
| total calls | 49 | 147 | 157.5 | — | 99.79 | A0 | **[0.634, 0.691]** | 14 |

**`nof`** (n = 20 per arm)

| module | models | AR | A0 | A1 | A2 | reference | A2 / reference | pairs |
|---|---|---|---|---|---|---|---|---|
| M1 | 24 | 2.9 [2, 4] | 3.15 [2, 5] | 3 [2, 5] | 1.9 [1, 3] | A1 | **0.6333** | 20 |
| M2 | 10 | 2.9 [2, 4] | 3.15 [2, 5] | 3 [2, 5] | 2.45 [1, 5] | A1 | **0.8167** | 20 |
| M3 | 11 | 2.9 [2, 4] | 3.15 [2, 5] | 3 [2, 5] | 2.35 [1, 3] | A1 | **0.7833** | 20 |
| PULSE | 1 | 2.9 [2, 4] | 3.15 [2, 5] | 3 [2, 5] | 1 | A1 | **0.3333** | 20 |
| once per run | 3 | 2.9 [2, 4] | 3.15 [2, 5] | 3 [2, 5] | 0 | A1 | **0.0000** | 20 |
| total calls | 49 | 142.1 | 154.3 | 147 | 96.95 | A1 | **[0.660, 0.704]** | 20 |

**`lad`** (n = 19 per arm)

| module | models | AR | A0 | A1 | A2 | reference | A2 / reference | pairs |
|---|---|---|---|---|---|---|---|---|
| M1 | 24 | 3.211 [2, 5] | 3.263 [2, 5] | 3.053 [2, 4] | 1.895 [1, 3] | A1 | **0.6207** | 19 |
| M2 | 10 | 3.211 [2, 5] | 3.263 [2, 5] | 3.053 [2, 4] | 2.421 [1, 4] | A1 | **0.7931** | 19 |
| M3 | 11 | 3.211 [2, 5] | 3.263 [2, 5] | 3.053 [2, 4] | 2.526 [2, 3] | A1 | **0.8276** | 19 |
| PULSE | 1 | 3.211 [2, 5] | 3.263 [2, 5] | 3.053 [2, 4] | 1 | A1 | **0.3276** | 19 |
| once per run | 3 | 3.211 [2, 5] | 3.263 [2, 5] | 3.053 [2, 4] | 0 | A1 | **0.0000** | 19 |
| total calls | 49 | 157.3 | 159.9 | 149.6 | 98.47 | A1 | **[0.658, 0.704]** | 19 |

**`st`** (n = 14 per arm)

| module | models | AR | A0 | A1 | A2 | reference | A2 / reference | pairs |
|---|---|---|---|---|---|---|---|---|
| M1 | 24 | 3.143 [2, 4] | 3.357 [2, 5] | — | 2.214 [1, 4] | A0 | **0.6596** | 14 |
| M2 | 10 | 3.143 [2, 4] | 3.357 [2, 5] | — | 2.214 [1, 5] | A0 | **0.6596** | 14 |
| M3 | 11 | 3.143 [2, 4] | 3.357 [2, 5] | — | 2.357 [1, 3] | A0 | **0.7021** | 14 |
| once per run | 4 | 3.143 [2, 4] | 3.357 [2, 5] | — | 0 | A0 | **0.0000** | 14 |
| total calls | 49 | 154 | 164.5 | — | 101.2 | A0 | **[0.615, 0.671]** | 14 |

<sub>`module sweeps per run, the other three regimes`</sub>

<sub>combining 9 stage table(s): `module sweeps per run — large_tokamak_nof — campaign_entry_references`; `module sweeps per run — low_aspect_ratio_DEMO — campaign_entry_references`; `module sweeps per run — st_regression — campaign_entry_references`; `module sweeps per run — large_tokamak_nof — campaign_stencil_forward`; `module sweeps per run — low_aspect_ratio_DEMO — campaign_stencil_forward`; `module sweeps per run — st_regression — campaign_stencil_forward`; `module sweeps per run — large_tokamak_nof — campaign_stencil_backward`; `module sweeps per run — low_aspect_ratio_DEMO — campaign_stencil_backward`; `module sweeps per run — st_regression — campaign_stencil_backward`</sub>

**Table F.4.** *What each finished evaluation-phase run's convergence test cost, one row per run, configurations and regimes stacked: sweeps, and for the test the arm stops on its evaluations, components compared and mean width. The two predicates are never summed. n = 12 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and source regime and its own n, and that n counts finished evaluation-phase campaign runs of that configuration).*

| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **large_tokamak_nof · campaign_entry_references (n = 1)** |  |  |  |  |  |  |  |  |  |  |  |
| A0 | 0 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| **low_aspect_ratio_DEMO · campaign_entry_references (n = 1)** |  |  |  |  |  |  |  |  |  |  |  |
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| **st_regression · campaign_entry_references (n = 1)** |  |  |  |  |  |  |  |  |  |  |  |
| A0 | 0 | coupling_state | 7 | 7 | 5789 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| **large_tokamak_nof · campaign_displaced (n = 100)** |  |  |  |  |  |  |  |  |  |  |  |
| AR | 1 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 2 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 3 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 4 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 5 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 6 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 7 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 8 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 9 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 10 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 11 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 12 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 13 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 14 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 15 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 16 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27.0 | 0.00 % |
| AR | 17 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 18 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 19 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 20 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 21 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 22 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 23 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 24 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| AR | 25 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27.0 | 0.00 % |
| A0 | 1 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 2 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 3 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 4 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 5 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 6 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 7 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 8 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 9 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 10 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 11 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 12 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 13 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 14 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 15 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 16 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 17 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 18 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 19 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 20 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 21 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 22 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 23 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 24 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 25 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 1 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 2 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 3 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 4 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 5 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 6 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 7 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 8 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 9 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 10 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 11 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 12 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 13 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 14 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 15 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 16 | coupling_state | 4 | 4 | 3360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 17 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 18 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 19 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 20 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 21 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 22 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 23 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 24 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 25 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A2 | 1 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 2 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 3 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 4 | coupling_state | 14 | 13 | 3135 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 5 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 6 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 7 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 8 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 9 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 10 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 11 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 12 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 13 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 14 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 15 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 16 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 17 | coupling_state | 14 | 13 | 3135 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 18 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 19 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 20 | coupling_state | 14 | 13 | 3135 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 21 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 22 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 23 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 24 | coupling_state | 13 | 12 | 2895 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 25 | coupling_state | 14 | 13 | 3135 | 241.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| **low_aspect_ratio_DEMO · campaign_displaced (n = 100)** |  |  |  |  |  |  |  |  |  |  |  |
| AR | 1 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 2 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 3 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 4 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 5 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 6 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 7 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 8 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 9 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 10 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 11 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 12 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 13 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 14 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 15 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 16 | upstream | 5 | 0 | 0 | — | — | 4 | 79 | 19.8 | 0.00 % |
| AR | 17 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 18 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 19 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 20 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 21 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 22 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 23 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 24 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 25 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| A0 | 1 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 2 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 3 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 4 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 5 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 6 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 7 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 8 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 9 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 10 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 11 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 12 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 13 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 14 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 15 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 16 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 17 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 18 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 19 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 20 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 21 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 22 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 23 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 24 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 25 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 1 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 2 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 3 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 4 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 5 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 6 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 7 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 8 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 9 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 10 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 11 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 12 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 13 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 14 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 15 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 16 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 17 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 18 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 19 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 20 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 21 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 22 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 23 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 24 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 25 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A2 | 1 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 2 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 3 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 4 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 5 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 6 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 7 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 8 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 9 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 10 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 11 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 12 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 13 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 14 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 15 | coupling_state | 12 | 11 | 2675 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 16 | coupling_state | 12 | 11 | 2675 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 17 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 18 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 19 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 20 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 21 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 22 | coupling_state | 12 | 11 | 2675 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 23 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 24 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 25 | coupling_state | 13 | 12 | 2919 | 243.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| **st_regression · campaign_displaced (n = 75)** |  |  |  |  |  |  |  |  |  |  |  |
| AR | 1 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 2 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 3 | upstream | 4 | 0 | 0 | — | — | 3 | 21 | 7.0 | 0.00 % |
| AR | 4 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 5 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 6 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 7 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 8 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 9 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 10 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 11 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 12 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 13 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 14 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 15 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 16 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 17 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 18 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 19 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 20 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 21 | upstream | 4 | 0 | 0 | — | — | 3 | 21 | 7.0 | 0.00 % |
| AR | 22 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 23 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 24 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| AR | 25 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10.0 | 0.00 % |
| A0 | 1 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 2 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 3 | coupling_state | 5 | 5 | 4135 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 4 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 5 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 6 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 7 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 8 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 9 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 10 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 11 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 12 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 13 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 14 | coupling_state | 5 | 5 | 4135 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 15 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 16 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 17 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 18 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 19 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 20 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 21 | coupling_state | 5 | 5 | 4135 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 22 | coupling_state | 5 | 5 | 4135 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 23 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 24 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 25 | coupling_state | 6 | 6 | 4962 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A2 | 1 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A2 | 2 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A2 | 3 | coupling_state | 14 | 12 | 2821 | 235.1 | M1 268, M2 216, M3 223 | 0 | 0 | — | 7.14 % |
| A2 | 4 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A2 | 5 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A2 | 6 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A2 | 7 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A2 | 8 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A2 | 9 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A2 | 10 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A2 | 11 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A2 | 12 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A2 | 13 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A2 | 14 | coupling_state | 14 | 12 | 2821 | 235.1 | M1 268, M2 216, M3 223 | 0 | 0 | — | 7.14 % |
| A2 | 15 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A2 | 16 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A2 | 17 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A2 | 18 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A2 | 19 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A2 | 20 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A2 | 21 | coupling_state | 14 | 12 | 2821 | 235.1 | M1 268, M2 216, M3 223 | 0 | 0 | — | 7.14 % |
| A2 | 22 | coupling_state | 14 | 12 | 2821 | 235.1 | M1 268, M2 216, M3 223 | 0 | 0 | — | 7.14 % |
| A2 | 23 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A2 | 24 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| A2 | 25 | coupling_state | 15 | 13 | 3037 | 233.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 6.67 % |
| **large_tokamak_nof · campaign_stencil_forward (n = 80)** |  |  |  |  |  |  |  |  |  |  |  |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27.0 | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 4 | 4 | 3360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 4 | 4 | 3360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 4 | 4 | 3360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 4 | 4 | 3360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 10 | 9 | 2157 | 239.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 11 | 10 | 2397 | 239.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1456 | 242.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 8 | 7 | 1678 | 239.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1456 | 242.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 5 | 4 | 977 | 244.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 9 | 8 | 1881 | 235.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 9 | 8 | 1936 | 242.0 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 10 | 9 | 2121 | 235.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1420 | 236.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1456 | 242.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 6 | 5 | 1180 | 236.0 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 9 | 8 | 1881 | 235.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 6 | 5 | 1180 | 236.0 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 6 | 5 | 1180 | 236.0 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 6 | 5 | 1180 | 236.0 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1456 | 242.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 6 | 5 | 1180 | 236.0 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1456 | 242.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 9 | 8 | 1881 | 235.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| **low_aspect_ratio_DEMO · campaign_stencil_forward (n = 76)** |  |  |  |  |  |  |  |  |  |  |  |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 53 | 17.7 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 53 | 17.7 | 0.00 % |
| AR | 0 | upstream | 5 | 0 | 0 | — | — | 4 | 104 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26.0 | 0.00 % |
| AR | 0 | upstream | 5 | 0 | 0 | — | — | 4 | 104 | 26.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 10 | 9 | 2172 | 241.3 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 11 | 10 | 2416 | 241.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1463 | 243.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 8 | 7 | 1669 | 238.4 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1463 | 243.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 8 | 7 | 1654 | 236.3 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 9 | 8 | 1898 | 237.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 9 | 8 | 1928 | 241.0 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 9 | 8 | 1898 | 237.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1433 | 238.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1433 | 238.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1463 | 243.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 8 | 7 | 1677 | 239.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1463 | 243.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1463 | 243.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| **st_regression · campaign_stencil_forward (n = 42)** |  |  |  |  |  |  |  |  |  |  |  |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 21 | 7.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 19 | 19.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 19 | 19.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 38 | 19.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 38 | 19.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 57 | 19.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 19 | 19.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 57 | 19.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10.0 | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1654 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1654 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 10 | 8 | 1957 | 244.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.00 % |
| A2 | 0 | coupling_state | 8 | 6 | 1414 | 235.7 | M1 268, M2 216, M3 223 | 0 | 0 | — | 12.50 % |
| A2 | 0 | coupling_state | 9 | 7 | 1689 | 241.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.11 % |
| A2 | 0 | coupling_state | 6 | 4 | 975 | 243.8 | M1 268, M2 216, M3 223 | 0 | 0 | — | 16.67 % |
| A2 | 0 | coupling_state | 9 | 7 | 1578 | 225.4 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.11 % |
| A2 | 0 | coupling_state | 9 | 7 | 1682 | 240.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.11 % |
| A2 | 0 | coupling_state | 9 | 7 | 1578 | 225.4 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.11 % |
| A2 | 0 | coupling_state | 10 | 8 | 1801 | 225.1 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.00 % |
| A2 | 0 | coupling_state | 8 | 6 | 1369 | 228.2 | M1 268, M2 216, M3 223 | 0 | 0 | — | 12.50 % |
| A2 | 0 | coupling_state | 9 | 7 | 1689 | 241.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.11 % |
| A2 | 0 | coupling_state | 8 | 6 | 1466 | 244.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 12.50 % |
| A2 | 0 | coupling_state | 10 | 8 | 1801 | 225.1 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.00 % |
| A2 | 0 | coupling_state | 8 | 6 | 1466 | 244.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 12.50 % |
| A2 | 0 | coupling_state | 8 | 6 | 1466 | 244.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 12.50 % |
| **large_tokamak_nof · campaign_stencil_backward (n = 80)** |  |  |  |  |  |  |  |  |  |  |  |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27.0 | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 4 | 4 | 3360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 4 | 4 | 3360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 5 | 5 | 4200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 4 | 4 | 3360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 2 | 2 | 1680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 4 | 4 | 3360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 10 | 9 | 2157 | 239.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 11 | 10 | 2397 | 239.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1456 | 242.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 9 | 8 | 1899 | 237.4 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1456 | 242.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 5 | 4 | 977 | 244.2 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 9 | 8 | 1881 | 235.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 10 | 9 | 2157 | 239.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 10 | 9 | 2121 | 235.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1420 | 236.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1456 | 242.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 6 | 5 | 1180 | 236.0 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 9 | 8 | 1881 | 235.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 6 | 5 | 1180 | 236.0 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 6 | 5 | 1180 | 236.0 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 6 | 5 | 1180 | 236.0 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1456 | 242.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 6 | 5 | 1180 | 236.0 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1456 | 242.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 9 | 8 | 1881 | 235.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| **low_aspect_ratio_DEMO · campaign_stencil_backward (n = 76)** |  |  |  |  |  |  |  |  |  |  |  |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 53 | 17.7 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 53 | 17.7 | 0.00 % |
| AR | 0 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26.0 | 0.00 % |
| AR | 0 | upstream | 5 | 0 | 0 | — | — | 4 | 104 | 26.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26.0 | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 4 | 4 | 3384 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 2 | 2 | 1692 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 10 | 9 | 2172 | 241.3 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 11 | 10 | 2416 | 241.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1463 | 243.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 8 | 7 | 1669 | 238.4 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1463 | 243.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 8 | 7 | 1654 | 236.3 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 9 | 8 | 1898 | 237.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 10 | 9 | 2172 | 241.3 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 9 | 8 | 1898 | 237.2 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 8 | 7 | 1654 | 236.3 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 8 | 7 | 1654 | 236.3 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1463 | 243.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1410 | 235.0 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 8 | 7 | 1677 | 239.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1463 | 243.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 7 | 6 | 1463 | 243.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| **st_regression · campaign_stencil_backward (n = 42)** |  |  |  |  |  |  |  |  |  |  |  |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 21 | 7.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 19 | 19.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 19 | 19.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 57 | 19.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 57 | 19.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 57 | 19.0 | 0.00 % |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 19 | 19.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10.0 | 0.00 % |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 57 | 19.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10.0 | 0.00 % |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10.0 | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1654 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 2 | 2 | 1654 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4135 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 5 | 5 | 4135 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| A2 | 0 | coupling_state | 10 | 8 | 1957 | 244.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.00 % |
| A2 | 0 | coupling_state | 8 | 6 | 1414 | 235.7 | M1 268, M2 216, M3 223 | 0 | 0 | — | 12.50 % |
| A2 | 0 | coupling_state | 9 | 7 | 1689 | 241.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.11 % |
| A2 | 0 | coupling_state | 6 | 4 | 975 | 243.8 | M1 268, M2 216, M3 223 | 0 | 0 | — | 16.67 % |
| A2 | 0 | coupling_state | 9 | 7 | 1578 | 225.4 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.11 % |
| A2 | 0 | coupling_state | 9 | 7 | 1682 | 240.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.11 % |
| A2 | 0 | coupling_state | 9 | 7 | 1578 | 225.4 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.11 % |
| A2 | 0 | coupling_state | 11 | 9 | 2017 | 224.1 | M1 268, M2 216, M3 223 | 0 | 0 | — | 9.09 % |
| A2 | 0 | coupling_state | 8 | 6 | 1369 | 228.2 | M1 268, M2 216, M3 223 | 0 | 0 | — | 12.50 % |
| A2 | 0 | coupling_state | 9 | 7 | 1689 | 241.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.11 % |
| A2 | 0 | coupling_state | 8 | 6 | 1466 | 244.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 12.50 % |
| A2 | 0 | coupling_state | 11 | 9 | 2017 | 224.1 | M1 268, M2 216, M3 223 | 0 | 0 | — | 9.09 % |
| A2 | 0 | coupling_state | 8 | 6 | 1466 | 244.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 12.50 % |
| A2 | 0 | coupling_state | 8 | 6 | 1466 | 244.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 12.50 % |

<sub>`per-sweep overhead, the evaluation phase`</sub>

<sub>combining 12 stage table(s): `per-sweep overhead — large_tokamak_nof — campaign_entry_references`; `per-sweep overhead — low_aspect_ratio_DEMO — campaign_entry_references`; `per-sweep overhead — st_regression — campaign_entry_references`; `per-sweep overhead — large_tokamak_nof — campaign_displaced`; `per-sweep overhead — low_aspect_ratio_DEMO — campaign_displaced`; `per-sweep overhead — st_regression — campaign_displaced`; `per-sweep overhead — large_tokamak_nof — campaign_stencil_forward`; `per-sweep overhead — low_aspect_ratio_DEMO — campaign_stencil_forward`; `per-sweep overhead — st_regression — campaign_stencil_forward`; `per-sweep overhead — large_tokamak_nof — campaign_stencil_backward`; `per-sweep overhead — low_aspect_ratio_DEMO — campaign_stencil_backward`; `per-sweep overhead — st_regression — campaign_stencil_backward`</sub>

**Table F.5.** *The predicate trial, frozen against mixed: per pair of runs, the decisive passes as crossings and as verdict changes, bit-identity, and the exit audit on both rulers. The decisive components carry |y|/s up to 54.59. From gate predicate_mode's verdict. n = 12 (pairs of runs, one per ruler).*

| configuration | arm | seed | predicate evaluations | decisive passes: crossings | decisive passes: verdicts changed | pair bit-identical | frozen run · frozen ruler | frozen run · mixed ruler | mixed run · frozen ruler | mixed run · mixed ruler |
|---|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | A0 | 1 | 9 | 3 | 0 | yes | 0x1.5fe433222bb97p-29 | 0x1.f8c2a9ec36d62p-31 | 0x1.5fe433222bb97p-29 | 0x1.f8c2a9ec36d62p-31 |
| large_tokamak_nof | A0 | 2 | 8 | 1 | 0 | yes | 0x0.0p+0 | 0x0.0p+0 | 0x0.0p+0 | 0x0.0p+0 |
| large_tokamak_nof | A2 | 1 | 15 | 2 | 0 | yes | 0x1.f5b2a3ea40bd7p-1 | 0x1.774db44e2d2b1p-3 | 0x1.f5b2a3ea40bd7p-1 | 0x1.774db44e2d2b1p-3 |
| large_tokamak_nof | A2 | 2 | 15 | 1 | 0 | yes | 0x1.c4dcc35b240c9p+0 | 0x1.656469d523e7ep-2 | 0x1.c4dcc35b240c9p+0 | 0x1.656469d523e7ep-2 |
| low_aspect_ratio_DEMO | A0 | 1 | 8 | 0 | 0 | yes | 0x0.0p+0 | 0x0.0p+0 | 0x0.0p+0 | 0x0.0p+0 |
| low_aspect_ratio_DEMO | A0 | 2 | 8 | 1 | 0 | yes | 0x0.0p+0 | 0x0.0p+0 | 0x0.0p+0 | 0x0.0p+0 |
| low_aspect_ratio_DEMO | A2 | 1 | 15 | 0 | 0 | yes | 0x1.ad17b67239f49p-4 | 0x1.a621cc5cabcc8p-4 | 0x1.ad17b67239f49p-4 | 0x1.a621cc5cabcc8p-4 |
| low_aspect_ratio_DEMO | A2 | 2 | 15 | 0 | 0 | yes | 0x1.2cdce94f65769p-3 | 0x1.24c92dd10e577p-3 | 0x1.2cdce94f65769p-3 | 0x1.24c92dd10e577p-3 |
| st_regression | A0 | 1 | 9 | 2 | 0 | yes | 0x1.9e44b1da8552dp-29 | 0x1.211b7a2189fc0p-29 | 0x1.9e44b1da8552dp-29 | 0x1.211b7a2189fc0p-29 |
| st_regression | A0 | 2 | 9 | 1 | 0 | yes | 0x1.05028b3bcc6bfp-27 | 0x1.6c4dec4c0f592p-28 | 0x1.05028b3bcc6bfp-27 | 0x1.6c4dec4c0f592p-28 |
| st_regression | A2 | 1 | 16 | 1 | 0 | yes | 0x1.fabf584472547p-3 | 0x1.3cec1f486b6d0p-3 | 0x1.fabf584472547p-3 | 0x1.3cec1f486b6d0p-3 |
| st_regression | A2 | 2 | 16 | 1 | 0 | yes | 0x1.e15dc1afec083p-3 | 0x1.ccd4e2d6e3fcap-4 | 0x1.e15dc1afec083p-3 | 0x1.ccd4e2d6e3fcap-4 |

<sub>`the predicate trial`</sub>

<sub>combining 1 stage table(s): `the predicate trial — frozen against mixed`</sub>

## F.2 The optimisation phase — one row per seed or per run

The per-seed and per-run tables of the optimisation phase, one construction per table with the configurations as row groups: per-arm success by seed (every start offered, each arm's outcome class there), the failure table (every seed outside the seed set, with what failed there and what the other arms cost at the same start), the attempt-summation identity (every run's per-attempt costs against its solve-phase total) and the per-run overhead.

**Table F.6.** *Every start offered, configurations stacked: each arm's outcome class at that seed, how many arms accepted it, whether it is in the seed set, and which arms lost it where another accepted. n = 3 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and its own n, and that n counts distinct seeds run on that configuration).*

| seed | BR | B0 | B1 | B2 | arms accepted | in the seed set | lost by (another arm accepted) |
|---|---|---|---|---|---|---|---|
| **large_tokamak_nof (n = 25)** |  |  |  |  |  |  |  |
| 0 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 1 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 2 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 3 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 4 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 5 | crashed (RuntimeError) | crashed (RuntimeError) | crashed (RuntimeError) | crashed (RuntimeError) | 0 | no | — |
| 6 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 7 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 8 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 9 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 10 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 11 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 12 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 13 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 14 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 15 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 16 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 17 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 18 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 19 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 20 | crashed (RuntimeError) | crashed (RuntimeError) | crashed (RuntimeError) | crashed (RuntimeError) | 0 | no | — |
| 21 | crashed (RuntimeError) | crashed (RuntimeError) | crashed (RuntimeError) | crashed (RuntimeError) | 0 | no | — |
| 22 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 23 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 24 | accepted | accepted | accepted | accepted | 4 | yes | — |
| **low_aspect_ratio_DEMO (n = 25)** |  |  |  |  |  |  |  |
| 0 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 1 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 2 | finished, ifail = 5 | finished, ifail = 5 | finished, ifail = 5 | finished, ifail = 5 | 0 | no | — |
| 3 | crashed (RuntimeError) | crashed (RuntimeError) | crashed (RuntimeError) | crashed (RuntimeError) | 0 | no | — |
| 4 | finished, ifail = 5 | coupling-loop cap (ModuleSolveFailure) | coupling-loop cap (ModuleSolveFailure) | coupling-loop cap (ModuleSolveFailure) | 0 | no | — |
| 5 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 6 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 7 | finished, ifail = 5 | finished, ifail = 5 | finished, ifail = 5 | finished, ifail = 5 | 0 | no | — |
| 8 | finished, ifail = 5 | finished, ifail = 5 | finished, ifail = 5 | finished, ifail = 5 | 0 | no | — |
| 9 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 10 | accepted | accepted | coupling-loop cap (ModuleSolveFailure) | coupling-loop cap (ModuleSolveFailure) | 2 | no | B1, B2 |
| 11 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 12 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 13 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 14 | finished, ifail = 5 | finished, ifail = 5 | finished, ifail = 5 | finished, ifail = 5 | 0 | no | — |
| 15 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 16 | finished, ifail = 5 | finished, ifail = 5 | finished, ifail = 5 | finished, ifail = 5 | 0 | no | — |
| 17 | finished, ifail = 5 | finished, ifail = 5 | finished, ifail = 5 | finished, ifail = 5 | 0 | no | — |
| 18 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 19 | accepted | accepted | accepted | accepted | 4 | yes | — |
| 20 | finished, ifail = 5 | finished, ifail = 5 | finished, ifail = 5 | finished, ifail = 5 | 0 | no | — |
| 21 | crashed (RuntimeError) | crashed (RuntimeError) | crashed (RuntimeError) | crashed (RuntimeError) | 0 | no | — |
| 22 | finished, ifail = 5 | coupling-loop cap (ModuleSolveFailure) | coupling-loop cap (ModuleSolveFailure) | coupling-loop cap (ModuleSolveFailure) | 0 | no | — |
| 23 | finished, ifail = 5 | finished, ifail = 5 | finished, ifail = 5 | finished, ifail = 5 | 0 | no | — |
| 24 | finished, ifail = 5 | finished, ifail = 5 | finished, ifail = 5 | finished, ifail = 5 | 0 | no | — |
| **st_regression (n = 25; arms BR·B0·B2)** |  |  |  |  |  |  |  |
| 0 | accepted | accepted |  | accepted | 3 | yes | — |
| 1 | accepted | accepted |  | accepted | 3 | yes | — |
| 2 | accepted | accepted |  | accepted | 3 | yes | — |
| 3 | accepted | accepted |  | accepted | 3 | yes | — |
| 4 | accepted | accepted |  | accepted | 3 | yes | — |
| 5 | accepted | accepted |  | finished, ifail = 5 | 2 | no | B2 |
| 6 | accepted | accepted |  | accepted | 3 | yes | — |
| 7 | accepted | accepted |  | accepted | 3 | yes | — |
| 8 | accepted | accepted |  | accepted | 3 | yes | — |
| 9 | accepted | accepted |  | accepted | 3 | yes | — |
| 10 | accepted | finished, ifail = 5 |  | accepted | 2 | no | B0 |
| 11 | accepted | accepted |  | accepted | 3 | yes | — |
| 12 | accepted | accepted |  | accepted | 3 | yes | — |
| 13 | accepted | accepted |  | accepted | 3 | yes | — |
| 14 | accepted | accepted |  | accepted | 3 | yes | — |
| 15 | accepted | accepted |  | accepted | 3 | yes | — |
| 16 | accepted | accepted |  | accepted | 3 | yes | — |
| 17 | finished, ifail = 5 | finished, ifail = 5 |  | finished, ifail = 5 | 0 | no | — |
| 18 | accepted | accepted |  | accepted | 3 | yes | — |
| 19 | accepted | accepted |  | accepted | 3 | yes | — |
| 20 | accepted | accepted |  | accepted | 3 | yes | — |
| 21 | accepted | accepted |  | accepted | 3 | yes | — |
| 22 | accepted | accepted |  | accepted | 3 | yes | — |
| 23 | accepted | accepted |  | accepted | 3 | yes | — |
| 24 | accepted | accepted |  | accepted | 3 | yes | — |

<sub>`per-arm success by seed`</sub>

<sub>combining 3 stage table(s): `per-arm success by seed — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`; `per-arm success by seed — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`; `per-arm success by seed — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table F.7.** *Every seed outside the seed set, configurations stacked: which arms failed there, what `ifail` and how many attempts, what the failed arm and the other arms cost at that start, and whether the seed is configuration-invalid (no arm accepted it). n = 3 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and its own n, and that n counts distinct seeds run on that configuration).*

| seed | failed arm(s) | not run | ifail | attempts | failed arm node calls | other arms' node calls | configuration-invalid |
|---|---|---|---|---|---|---|---|
| **large_tokamak_nof (n = 25)** |  |  |  |  |  |  |  |
| 5 | BR, B0, B1, B2 | — | None, None, None, None | 1, 1, 1, 1 | None, None, None, None | BR — / B0 — / B1 — / B2 — | yes |
| 20 | BR, B0, B1, B2 | — | None, None, None, None | 1, 1, 1, 1 | None, None, None, None | BR — / B0 — / B1 — / B2 — | yes |
| 21 | BR, B0, B1, B2 | — | None, None, None, None | 1, 1, 1, 1 | None, None, None, None | BR — / B0 — / B1 — / B2 — | yes |
| **low_aspect_ratio_DEMO (n = 25)** |  |  |  |  |  |  |  |
| 2 | BR, B0, B1, B2 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11466, 11571, 11298, 7092 | BR — / B0 — / B1 — / B2 — | yes |
| 3 | BR, B0, B1, B2 | — | None, None, None, None | 1, 1, 1, 1 | None, None, None, None | BR — / B0 — / B1 — / B2 — | yes |
| 4 | BR, B0, B1, B2 | — | 5.0, None, None, None | 4, 1, 1, 1 | 10773, None, None, None | BR — / B0 — / B1 — / B2 — | yes |
| 7 | BR, B0, B1, B2 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11298, 11340, 10983, 7126 | BR — / B0 — / B1 — / B2 — | yes |
| 8 | BR, B0, B1, B2 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11025, 11298, 10983, 7066 | BR — / B0 — / B1 — / B2 — | yes |
| 10 | B1, B2 | — | None, None | 2, 2 | None, None | BR 60816 / B0 58947 / B1 — / B2 — | no |
| 14 | BR, B0, B1, B2 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11130, 11529, 11193, 7190 | BR — / B0 — / B1 — / B2 — | yes |
| 16 | BR, B0, B1, B2 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11319, 11235, 11277, 7146 | BR — / B0 — / B1 — / B2 — | yes |
| 17 | BR, B0, B1, B2 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11340, 11277, 11298, 7208 | BR — / B0 — / B1 — / B2 — | yes |
| 20 | BR, B0, B1, B2 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11214, 11403, 11361, 7186 | BR — / B0 — / B1 — / B2 — | yes |
| 21 | BR, B0, B1, B2 | — | None, None, None, None | 1, 1, 1, 1 | None, None, None, None | BR — / B0 — / B1 — / B2 — | yes |
| 22 | BR, B0, B1, B2 | — | 5.0, None, None, None | 4, 1, 1, 1 | 11130, None, None, None | BR — / B0 — / B1 — / B2 — | yes |
| 23 | BR, B0, B1, B2 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11340, 11319, 11319, 7212 | BR — / B0 — / B1 — / B2 — | yes |
| 24 | BR, B0, B1, B2 | — | 5.0, 5.0, 5.0, 5.0 | 4, 4, 4, 4 | 11403, 11445, 11130, 7152 | BR — / B0 — / B1 — / B2 — | yes |
| **st_regression (n = 25; arms BR·B0·B2)** |  |  |  |  |  |  |  |
| 5 | B2 | — | 5.0 | 3 | 479630 | BR 160335 / B0 175413 / B2 — | no |
| 10 | B0 | — | 5.0 | 3 | 667989 | BR 717990 / B0 — / B2 129012 | no |
| 17 | BR, B0, B2 | — | 5.0, 5.0, 5.0 | 4, 4, 4 | 8064, 8820, 4921 | BR — / B0 — / B2 — | yes |

<sub>`the failure table`</sub>

<sub>combining 3 stage table(s): `the failure table — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`; `the failure table — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`; `the failure table — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table F.8.** *The identity that licenses summing an optimisation's cost over the optimiser's attempts, one row per run, configurations stacked: the per-attempt costs, their sum, the solve-phase total and the residual between them. A run that did not finish with status ok has no solve-phase total by construction and reads NO with no residual. n = 3 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and its own n, and that n counts optimisation-phase campaign runs of that configuration).*

| arm | seed | attempts | retried | node calls per attempt | = solve-phase total | residual | sweeps per attempt | = solve-phase total | residual | decomposes |
|---|---|---|---|---|---|---|---|---|---|---|
| **large_tokamak_nof (n = 100)** |  |  |  |  |  |  |  |  |  |  |
| BR | 0 | 1 | no | 42567 | 42567 | 0 | 2027 | 2027 | 0 | yes |
| BR | 1 | 1 | no | 42399 | 42399 | 0 | 2019 | 2019 | 0 | yes |
| BR | 2 | 1 | no | 47817 | 47817 | 0 | 2277 | 2277 | 0 | yes |
| BR | 3 | 1 | no | 36897 | 36897 | 0 | 1757 | 1757 | 0 | yes |
| BR | 4 | 1 | no | 36939 | 36939 | 0 | 1759 | 1759 | 0 | yes |
| BR | 5 | 1 | no | — | — | — | — | — | — | NO |
| BR | 6 | 1 | no | 42714 | 42714 | 0 | 2034 | 2034 | 0 | yes |
| BR | 7 | 1 | no | 42630 | 42630 | 0 | 2030 | 2030 | 0 | yes |
| BR | 8 | 1 | no | 42672 | 42672 | 0 | 2032 | 2032 | 0 | yes |
| BR | 9 | 1 | no | 42504 | 42504 | 0 | 2024 | 2024 | 0 | yes |
| BR | 10 | 1 | no | 37044 | 37044 | 0 | 1764 | 1764 | 0 | yes |
| BR | 11 | 1 | no | 42063 | 42063 | 0 | 2003 | 2003 | 0 | yes |
| BR | 12 | 1 | no | 42567 | 42567 | 0 | 2027 | 2027 | 0 | yes |
| BR | 13 | 1 | no | 42399 | 42399 | 0 | 2019 | 2019 | 0 | yes |
| BR | 14 | 1 | no | 47817 | 47817 | 0 | 2277 | 2277 | 0 | yes |
| BR | 15 | 1 | no | 36876 | 36876 | 0 | 1756 | 1756 | 0 | yes |
| BR | 16 | 1 | no | 36855 | 36855 | 0 | 1755 | 1755 | 0 | yes |
| BR | 17 | 1 | no | 42525 | 42525 | 0 | 2025 | 2025 | 0 | yes |
| BR | 18 | 1 | no | 42525 | 42525 | 0 | 2025 | 2025 | 0 | yes |
| BR | 19 | 1 | no | 42588 | 42588 | 0 | 2028 | 2028 | 0 | yes |
| BR | 20 | 1 | no | — | — | — | — | — | — | NO |
| BR | 21 | 1 | no | — | — | — | — | — | — | NO |
| BR | 22 | 1 | no | 36981 | 36981 | 0 | 1761 | 1761 | 0 | yes |
| BR | 23 | 1 | no | 42630 | 42630 | 0 | 2030 | 2030 | 0 | yes |
| BR | 24 | 1 | no | 42546 | 42546 | 0 | 2026 | 2026 | 0 | yes |
| B0 | 0 | 1 | no | 43449 | 43449 | 0 | 2069 | 2069 | 0 | yes |
| B0 | 1 | 1 | no | 43491 | 43491 | 0 | 2071 | 2071 | 0 | yes |
| B0 | 2 | 1 | no | 49623 | 49623 | 0 | 2363 | 2363 | 0 | yes |
| B0 | 3 | 1 | no | 37695 | 37695 | 0 | 1795 | 1795 | 0 | yes |
| B0 | 4 | 1 | no | 37590 | 37590 | 0 | 1790 | 1790 | 0 | yes |
| B0 | 5 | 1 | no | — | — | — | — | — | — | NO |
| B0 | 6 | 1 | no | 43449 | 43449 | 0 | 2069 | 2069 | 0 | yes |
| B0 | 7 | 1 | no | 43428 | 43428 | 0 | 2068 | 2068 | 0 | yes |
| B0 | 8 | 1 | no | 43428 | 43428 | 0 | 2068 | 2068 | 0 | yes |
| B0 | 9 | 1 | no | 43470 | 43470 | 0 | 2070 | 2070 | 0 | yes |
| B0 | 10 | 1 | no | 37590 | 37590 | 0 | 1790 | 1790 | 0 | yes |
| B0 | 11 | 1 | no | 44583 | 44583 | 0 | 2123 | 2123 | 0 | yes |
| B0 | 12 | 1 | no | 43428 | 43428 | 0 | 2068 | 2068 | 0 | yes |
| B0 | 13 | 1 | no | 43533 | 43533 | 0 | 2073 | 2073 | 0 | yes |
| B0 | 14 | 1 | no | 50253 | 50253 | 0 | 2393 | 2393 | 0 | yes |
| B0 | 15 | 1 | no | 37737 | 37737 | 0 | 1797 | 1797 | 0 | yes |
| B0 | 16 | 1 | no | 37674 | 37674 | 0 | 1794 | 1794 | 0 | yes |
| B0 | 17 | 1 | no | 43470 | 43470 | 0 | 2070 | 2070 | 0 | yes |
| B0 | 18 | 1 | no | 43323 | 43323 | 0 | 2063 | 2063 | 0 | yes |
| B0 | 19 | 1 | no | 43407 | 43407 | 0 | 2067 | 2067 | 0 | yes |
| B0 | 20 | 1 | no | — | — | — | — | — | — | NO |
| B0 | 21 | 1 | no | — | — | — | — | — | — | NO |
| B0 | 22 | 1 | no | 37758 | 37758 | 0 | 1798 | 1798 | 0 | yes |
| B0 | 23 | 1 | no | 43386 | 43386 | 0 | 2066 | 2066 | 0 | yes |
| B0 | 24 | 1 | no | 43575 | 43575 | 0 | 2075 | 2075 | 0 | yes |
| B1 | 0 | 1 | no | 44142 | 44142 | 0 | 2102 | 2102 | 0 | yes |
| B1 | 1 | 1 | no | 44100 | 44100 | 0 | 2100 | 2100 | 0 | yes |
| B1 | 2 | 1 | no | 44142 | 44142 | 0 | 2102 | 2102 | 0 | yes |
| B1 | 3 | 1 | no | 38304 | 38304 | 0 | 1824 | 1824 | 0 | yes |
| B1 | 4 | 1 | no | 38220 | 38220 | 0 | 1820 | 1820 | 0 | yes |
| B1 | 5 | 1 | no | — | — | — | — | — | — | NO |
| B1 | 6 | 1 | no | 44037 | 44037 | 0 | 2097 | 2097 | 0 | yes |
| B1 | 7 | 1 | no | 44037 | 44037 | 0 | 2097 | 2097 | 0 | yes |
| B1 | 8 | 1 | no | 44121 | 44121 | 0 | 2101 | 2101 | 0 | yes |
| B1 | 9 | 1 | no | 44163 | 44163 | 0 | 2103 | 2103 | 0 | yes |
| B1 | 10 | 1 | no | 44100 | 44100 | 0 | 2100 | 2100 | 0 | yes |
| B1 | 11 | 1 | no | 44478 | 44478 | 0 | 2118 | 2118 | 0 | yes |
| B1 | 12 | 1 | no | 44163 | 44163 | 0 | 2103 | 2103 | 0 | yes |
| B1 | 13 | 1 | no | 44142 | 44142 | 0 | 2102 | 2102 | 0 | yes |
| B1 | 14 | 1 | no | 44961 | 44961 | 0 | 2141 | 2141 | 0 | yes |
| B1 | 15 | 1 | no | 38262 | 38262 | 0 | 1822 | 1822 | 0 | yes |
| B1 | 16 | 1 | no | 38241 | 38241 | 0 | 1821 | 1821 | 0 | yes |
| B1 | 17 | 1 | no | 44184 | 44184 | 0 | 2104 | 2104 | 0 | yes |
| B1 | 18 | 1 | no | 38241 | 38241 | 0 | 1821 | 1821 | 0 | yes |
| B1 | 19 | 1 | no | 49980 | 49980 | 0 | 2380 | 2380 | 0 | yes |
| B1 | 20 | 1 | no | — | — | — | — | — | — | NO |
| B1 | 21 | 1 | no | — | — | — | — | — | — | NO |
| B1 | 22 | 1 | no | 38304 | 38304 | 0 | 1824 | 1824 | 0 | yes |
| B1 | 23 | 1 | no | 44184 | 44184 | 0 | 2104 | 2104 | 0 | yes |
| B1 | 24 | 1 | no | 44016 | 44016 | 0 | 2096 | 2096 | 0 | yes |
| B2 | 0 | 1 | no | 28055 | 28055 | 0 | 5499 | 5499 | 0 | yes |
| B2 | 1 | 1 | no | 28037 | 28037 | 0 | 5496 | 5496 | 0 | yes |
| B2 | 2 | 1 | no | 28055 | 28055 | 0 | 5499 | 5499 | 0 | yes |
| B2 | 3 | 1 | no | 24319 | 24319 | 0 | 4767 | 4767 | 0 | yes |
| B2 | 4 | 1 | no | 24307 | 24307 | 0 | 4763 | 4763 | 0 | yes |
| B2 | 5 | 1 | no | — | — | — | — | — | — | NO |
| B2 | 6 | 1 | no | 28024 | 28024 | 0 | 5491 | 5491 | 0 | yes |
| B2 | 7 | 1 | no | 28038 | 28038 | 0 | 5493 | 5493 | 0 | yes |
| B2 | 8 | 1 | no | 28040 | 28040 | 0 | 5497 | 5497 | 0 | yes |
| B2 | 9 | 1 | no | 28046 | 28046 | 0 | 5499 | 5499 | 0 | yes |
| B2 | 10 | 1 | no | 28049 | 28049 | 0 | 5497 | 5497 | 0 | yes |
| B2 | 11 | 1 | no | 28007 | 28007 | 0 | 5486 | 5486 | 0 | yes |
| B2 | 12 | 1 | no | 28066 | 28066 | 0 | 5499 | 5499 | 0 | yes |
| B2 | 13 | 1 | no | 28041 | 28041 | 0 | 5497 | 5497 | 0 | yes |
| B2 | 14 | 1 | no | 27888 | 27888 | 0 | 5494 | 5494 | 0 | yes |
| B2 | 15 | 1 | no | 24315 | 24315 | 0 | 4766 | 4766 | 0 | yes |
| B2 | 16 | 1 | no | 24324 | 24324 | 0 | 4766 | 4766 | 0 | yes |
| B2 | 17 | 1 | no | 27987 | 27987 | 0 | 5494 | 5494 | 0 | yes |
| B2 | 18 | 1 | no | 24296 | 24296 | 0 | 4763 | 4763 | 0 | yes |
| B2 | 19 | 1 | no | 31813 | 31813 | 0 | 6232 | 6232 | 0 | yes |
| B2 | 20 | 1 | no | — | — | — | — | — | — | NO |
| B2 | 21 | 1 | no | — | — | — | — | — | — | NO |
| B2 | 22 | 1 | no | 24321 | 24321 | 0 | 4768 | 4768 | 0 | yes |
| B2 | 23 | 1 | no | 28061 | 28061 | 0 | 5501 | 5501 | 0 | yes |
| B2 | 24 | 1 | no | 28035 | 28035 | 0 | 5492 | 5492 | 0 | yes |
| **low_aspect_ratio_DEMO (n = 100)** |  |  |  |  |  |  |  |  |  |  |
| BR | 0 | 1 | no | 89964 | 89964 | 0 | 4284 | 4284 | 0 | yes |
| BR | 1 | 2 | yes | 579369 + 89838 | 669207 | 0 | 27589 + 4278 | 31867 | 0 | yes |
| BR | 2 | 4 | yes | 2940 + 2877 + 2772 + 2877 | 11466 | 0 | 140 + 137 + 132 + 137 | 546 | 0 | yes |
| BR | 3 | 1 | no | — | — | — | — | — | — | NO |
| BR | 4 | 4 | yes | 2751 + 2877 + 2457 + 2688 | 10773 | 0 | 131 + 137 + 117 + 128 | 513 | 0 | yes |
| BR | 5 | 1 | no | 60921 | 60921 | 0 | 2901 | 2901 | 0 | yes |
| BR | 6 | 1 | no | 194313 | 194313 | 0 | 9253 | 9253 | 0 | yes |
| BR | 7 | 4 | yes | 2940 + 2877 + 2604 + 2877 | 11298 | 0 | 140 + 137 + 124 + 137 | 538 | 0 | yes |
| BR | 8 | 4 | yes | 2856 + 2877 + 2499 + 2793 | 11025 | 0 | 136 + 137 + 119 + 133 | 525 | 0 | yes |
| BR | 9 | 1 | no | 72513 | 72513 | 0 | 3453 | 3453 | 0 | yes |
| BR | 10 | 1 | no | 60816 | 60816 | 0 | 2896 | 2896 | 0 | yes |
| BR | 11 | 1 | no | 60984 | 60984 | 0 | 2904 | 2904 | 0 | yes |
| BR | 12 | 1 | no | 89985 | 89985 | 0 | 4285 | 4285 | 0 | yes |
| BR | 13 | 1 | no | 113106 | 113106 | 0 | 5386 | 5386 | 0 | yes |
| BR | 14 | 4 | yes | 2898 + 2877 + 2520 + 2835 | 11130 | 0 | 138 + 137 + 120 + 135 | 530 | 0 | yes |
| BR | 15 | 1 | no | 367773 | 367773 | 0 | 17513 | 17513 | 0 | yes |
| BR | 16 | 4 | yes | 2940 + 2877 + 2625 + 2877 | 11319 | 0 | 140 + 137 + 125 + 137 | 539 | 0 | yes |
| BR | 17 | 4 | yes | 2940 + 2877 + 2646 + 2877 | 11340 | 0 | 140 + 137 + 126 + 137 | 540 | 0 | yes |
| BR | 18 | 1 | no | 84042 | 84042 | 0 | 4002 | 4002 | 0 | yes |
| BR | 19 | 1 | no | 66570 | 66570 | 0 | 3170 | 3170 | 0 | yes |
| BR | 20 | 4 | yes | 2940 + 2877 + 2520 + 2877 | 11214 | 0 | 140 + 137 + 120 + 137 | 534 | 0 | yes |
| BR | 21 | 1 | no | — | — | — | — | — | — | NO |
| BR | 22 | 4 | yes | 2898 + 2877 + 2520 + 2835 | 11130 | 0 | 138 + 137 + 120 + 135 | 530 | 0 | yes |
| BR | 23 | 4 | yes | 2940 + 2877 + 2646 + 2877 | 11340 | 0 | 140 + 137 + 126 + 137 | 540 | 0 | yes |
| BR | 24 | 4 | yes | 2940 + 2877 + 2709 + 2877 | 11403 | 0 | 140 + 137 + 129 + 137 | 543 | 0 | yes |
| B0 | 0 | 1 | no | 86877 | 86877 | 0 | 4137 | 4137 | 0 | yes |
| B0 | 1 | 2 | yes | 558999 + 96474 | 655473 | 0 | 26619 + 4594 | 31213 | 0 | yes |
| B0 | 2 | 4 | yes | 2940 + 3087 + 2688 + 2856 | 11571 | 0 | 140 + 147 + 128 + 136 | 551 | 0 | yes |
| B0 | 3 | 1 | no | — | — | — | — | — | — | NO |
| B0 | 4 | 1 | no | — | — | — | — | — | — | NO |
| B0 | 5 | 1 | no | 58947 | 58947 | 0 | 2807 | 2807 | 0 | yes |
| B0 | 6 | 1 | no | 187572 | 187572 | 0 | 8932 | 8932 | 0 | yes |
| B0 | 7 | 4 | yes | 2877 + 3003 + 2667 + 2793 | 11340 | 0 | 137 + 143 + 127 + 133 | 540 | 0 | yes |
| B0 | 8 | 4 | yes | 2877 + 3003 + 2625 + 2793 | 11298 | 0 | 137 + 143 + 125 + 133 | 538 | 0 | yes |
| B0 | 9 | 1 | no | 70077 | 70077 | 0 | 3337 | 3337 | 0 | yes |
| B0 | 10 | 1 | no | 58947 | 58947 | 0 | 2807 | 2807 | 0 | yes |
| B0 | 11 | 1 | no | 58947 | 58947 | 0 | 2807 | 2807 | 0 | yes |
| B0 | 12 | 1 | no | 86919 | 86919 | 0 | 4139 | 4139 | 0 | yes |
| B0 | 13 | 1 | no | 109221 | 109221 | 0 | 5201 | 5201 | 0 | yes |
| B0 | 14 | 4 | yes | 2919 + 3087 + 2688 + 2835 | 11529 | 0 | 139 + 147 + 128 + 135 | 549 | 0 | yes |
| B0 | 15 | 1 | no | 355278 | 355278 | 0 | 16918 | 16918 | 0 | yes |
| B0 | 16 | 4 | yes | 2877 + 2982 + 2583 + 2793 | 11235 | 0 | 137 + 142 + 123 + 133 | 535 | 0 | yes |
| B0 | 17 | 4 | yes | 2877 + 2982 + 2625 + 2793 | 11277 | 0 | 137 + 142 + 125 + 133 | 537 | 0 | yes |
| B0 | 18 | 1 | no | 81186 | 81186 | 0 | 3866 | 3866 | 0 | yes |
| B0 | 19 | 1 | no | 64470 | 64470 | 0 | 3070 | 3070 | 0 | yes |
| B0 | 20 | 4 | yes | 2898 + 3024 + 2667 + 2814 | 11403 | 0 | 138 + 144 + 127 + 134 | 543 | 0 | yes |
| B0 | 21 | 1 | no | — | — | — | — | — | — | NO |
| B0 | 22 | 1 | no | — | — | — | — | — | — | NO |
| B0 | 23 | 4 | yes | 2877 + 3024 + 2625 + 2793 | 11319 | 0 | 137 + 144 + 125 + 133 | 539 | 0 | yes |
| B0 | 24 | 4 | yes | 2898 + 3045 + 2688 + 2814 | 11445 | 0 | 138 + 145 + 128 + 134 | 545 | 0 | yes |
| B1 | 0 | 1 | no | 69930 | 69930 | 0 | 3330 | 3330 | 0 | yes |
| B1 | 1 | 1 | no | 81228 | 81228 | 0 | 3868 | 3868 | 0 | yes |
| B1 | 2 | 4 | yes | 2856 + 2982 + 2688 + 2772 | 11298 | 0 | 136 + 142 + 128 + 132 | 538 | 0 | yes |
| B1 | 3 | 1 | no | — | — | — | — | — | — | NO |
| B1 | 4 | 1 | no | — | — | — | — | — | — | NO |
| B1 | 5 | 1 | no | 198240 | 198240 | 0 | 9440 | 9440 | 0 | yes |
| B1 | 6 | 1 | no | 114555 | 114555 | 0 | 5455 | 5455 | 0 | yes |
| B1 | 7 | 4 | yes | 2793 + 2835 + 2646 + 2709 | 10983 | 0 | 133 + 135 + 126 + 129 | 523 | 0 | yes |
| B1 | 8 | 4 | yes | 2793 + 2835 + 2646 + 2709 | 10983 | 0 | 133 + 135 + 126 + 129 | 523 | 0 | yes |
| B1 | 9 | 1 | no | 75600 | 75600 | 0 | 3600 | 3600 | 0 | yes |
| B1 | 10 | 2 | yes | — | — | — | — | — | — | NO |
| B1 | 11 | 1 | no | 360591 | 360591 | 0 | 17171 | 17171 | 0 | yes |
| B1 | 12 | 1 | no | 53214 | 53214 | 0 | 2534 | 2534 | 0 | yes |
| B1 | 13 | 1 | no | 97881 | 97881 | 0 | 4661 | 4661 | 0 | yes |
| B1 | 14 | 4 | yes | 2856 + 2898 + 2667 + 2772 | 11193 | 0 | 136 + 138 + 127 + 132 | 533 | 0 | yes |
| B1 | 15 | 1 | no | 86604 | 86604 | 0 | 4124 | 4124 | 0 | yes |
| B1 | 16 | 4 | yes | 2856 + 3024 + 2625 + 2772 | 11277 | 0 | 136 + 144 + 125 + 132 | 537 | 0 | yes |
| B1 | 17 | 4 | yes | 2856 + 3003 + 2667 + 2772 | 11298 | 0 | 136 + 143 + 127 + 132 | 538 | 0 | yes |
| B1 | 18 | 1 | no | 64617 | 64617 | 0 | 3077 | 3077 | 0 | yes |
| B1 | 19 | 1 | no | 53235 | 53235 | 0 | 2535 | 2535 | 0 | yes |
| B1 | 20 | 4 | yes | 2856 + 3003 + 2730 + 2772 | 11361 | 0 | 136 + 143 + 130 + 132 | 541 | 0 | yes |
| B1 | 21 | 1 | no | — | — | — | — | — | — | NO |
| B1 | 22 | 1 | no | — | — | — | — | — | — | NO |
| B1 | 23 | 4 | yes | 2856 + 3024 + 2667 + 2772 | 11319 | 0 | 136 + 144 + 127 + 132 | 539 | 0 | yes |
| B1 | 24 | 4 | yes | 2835 + 2877 + 2667 + 2751 | 11130 | 0 | 135 + 137 + 127 + 131 | 530 | 0 | yes |
| B2 | 0 | 1 | no | 45496 | 45496 | 0 | 8762 | 8762 | 0 | yes |
| B2 | 1 | 1 | no | 52834 | 52834 | 0 | 10182 | 10182 | 0 | yes |
| B2 | 2 | 4 | yes | 1792 + 1896 + 1654 + 1750 | 7092 | 0 | 353 + 363 + 332 + 344 | 1392 | 0 | yes |
| B2 | 3 | 1 | no | — | — | — | — | — | — | NO |
| B2 | 4 | 1 | no | — | — | — | — | — | — | NO |
| B2 | 5 | 1 | no | 129215 | 129215 | 0 | 24883 | 24883 | 0 | yes |
| B2 | 6 | 1 | no | 74687 | 74687 | 0 | 14382 | 14382 | 0 | yes |
| B2 | 7 | 4 | yes | 1819 + 1876 + 1654 + 1777 | 7126 | 0 | 353 + 357 + 330 + 344 | 1384 | 0 | yes |
| B2 | 8 | 4 | yes | 1795 + 1876 + 1642 + 1753 | 7066 | 0 | 351 + 357 + 329 + 342 | 1379 | 0 | yes |
| B2 | 9 | 1 | no | 49194 | 49194 | 0 | 9480 | 9480 | 0 | yes |
| B2 | 10 | 2 | yes | — | — | — | — | — | — | NO |
| B2 | 11 | 1 | no | 234616 | 234616 | 0 | 45221 | 45221 | 0 | yes |
| B2 | 12 | 1 | no | 34646 | 34646 | 0 | 6675 | 6675 | 0 | yes |
| B2 | 13 | 1 | no | 63761 | 63761 | 0 | 12282 | 12282 | 0 | yes |
| B2 | 14 | 4 | yes | 1837 + 1895 + 1663 + 1795 | 7190 | 0 | 356 + 360 + 332 + 347 | 1395 | 0 | yes |
| B2 | 15 | 1 | no | 56439 | 56439 | 0 | 10868 | 10868 | 0 | yes |
| B2 | 16 | 4 | yes | 1816 + 1912 + 1644 + 1774 | 7146 | 0 | 355 + 366 + 329 + 346 | 1396 | 0 | yes |
| B2 | 17 | 4 | yes | 1840 + 1908 + 1662 + 1798 | 7208 | 0 | 357 + 364 + 332 + 348 | 1401 | 0 | yes |
| B2 | 18 | 1 | no | 41920 | 41920 | 0 | 8087 | 8087 | 0 | yes |
| B2 | 19 | 1 | no | 34628 | 34628 | 0 | 6671 | 6671 | 0 | yes |
| B2 | 20 | 4 | yes | 1828 + 1900 + 1672 + 1786 | 7186 | 0 | 356 + 365 + 336 + 347 | 1404 | 0 | yes |
| B2 | 21 | 1 | no | — | — | — | — | — | — | NO |
| B2 | 22 | 1 | no | — | — | — | — | — | — | NO |
| B2 | 23 | 4 | yes | 1840 + 1912 + 1662 + 1798 | 7212 | 0 | 357 + 366 + 332 + 348 | 1403 | 0 | yes |
| B2 | 24 | 4 | yes | 1825 + 1881 + 1663 + 1783 | 7152 | 0 | 355 + 358 + 332 + 346 | 1391 | 0 | yes |
| **st_regression (n = 75; arms BR·B0·B2)** |  |  |  |  |  |  |  |  |  |  |
| BR | 0 | 1 | no | 39669 | 39669 | 0 | 1889 | 1889 | 0 | yes |
| BR | 1 | 1 | no | 176379 | 176379 | 0 | 8399 | 8399 | 0 | yes |
| BR | 2 | 2 | yes | 113442 + 96726 | 210168 | 0 | 5402 + 4606 | 10008 | 0 | yes |
| BR | 3 | 1 | no | 72408 | 72408 | 0 | 3448 | 3448 | 0 | yes |
| BR | 4 | 1 | no | 79905 | 79905 | 0 | 3805 | 3805 | 0 | yes |
| BR | 5 | 1 | no | 160335 | 160335 | 0 | 7635 | 7635 | 0 | yes |
| BR | 6 | 1 | no | 71799 | 71799 | 0 | 3419 | 3419 | 0 | yes |
| BR | 7 | 1 | no | 39774 | 39774 | 0 | 1894 | 1894 | 0 | yes |
| BR | 8 | 1 | no | 47565 | 47565 | 0 | 2265 | 2265 | 0 | yes |
| BR | 9 | 1 | no | 243810 | 243810 | 0 | 11610 | 11610 | 0 | yes |
| BR | 10 | 3 | yes | 226149 + 272601 + 219240 | 717990 | 0 | 10769 + 12981 + 10440 | 34190 | 0 | yes |
| BR | 11 | 1 | no | 43869 | 43869 | 0 | 2089 | 2089 | 0 | yes |
| BR | 12 | 2 | yes | 211659 + 68103 | 279762 | 0 | 10079 + 3243 | 13322 | 0 | yes |
| BR | 13 | 1 | no | 55776 | 55776 | 0 | 2656 | 2656 | 0 | yes |
| BR | 14 | 1 | no | 88683 | 88683 | 0 | 4223 | 4223 | 0 | yes |
| BR | 15 | 1 | no | 123795 | 123795 | 0 | 5895 | 5895 | 0 | yes |
| BR | 16 | 1 | no | 96852 | 96852 | 0 | 4612 | 4612 | 0 | yes |
| BR | 17 | 4 | yes | 2121 + 2121 + 1785 + 2037 | 8064 | 0 | 101 + 101 + 85 + 97 | 384 | 0 | yes |
| BR | 18 | 1 | no | 51618 | 51618 | 0 | 2458 | 2458 | 0 | yes |
| BR | 19 | 1 | no | 43575 | 43575 | 0 | 2075 | 2075 | 0 | yes |
| BR | 20 | 1 | no | 56049 | 56049 | 0 | 2669 | 2669 | 0 | yes |
| BR | 21 | 1 | no | 39627 | 39627 | 0 | 1887 | 1887 | 0 | yes |
| BR | 22 | 1 | no | 47439 | 47439 | 0 | 2259 | 2259 | 0 | yes |
| BR | 23 | 1 | no | 43638 | 43638 | 0 | 2078 | 2078 | 0 | yes |
| BR | 24 | 3 | yes | 249102 + 283311 + 306516 | 838929 | 0 | 11862 + 13491 + 14596 | 39949 | 0 | yes |
| B0 | 0 | 1 | no | 42756 | 42756 | 0 | 2036 | 2036 | 0 | yes |
| B0 | 1 | 1 | no | 226002 | 226002 | 0 | 10762 | 10762 | 0 | yes |
| B0 | 2 | 2 | yes | 117789 + 101031 | 218820 | 0 | 5609 + 4811 | 10420 | 0 | yes |
| B0 | 3 | 1 | no | 76461 | 76461 | 0 | 3641 | 3641 | 0 | yes |
| B0 | 4 | 1 | no | 80661 | 80661 | 0 | 3841 | 3841 | 0 | yes |
| B0 | 5 | 1 | no | 175413 | 175413 | 0 | 8353 | 8353 | 0 | yes |
| B0 | 6 | 1 | no | 72450 | 72450 | 0 | 3450 | 3450 | 0 | yes |
| B0 | 7 | 1 | no | 39732 | 39732 | 0 | 1892 | 1892 | 0 | yes |
| B0 | 8 | 1 | no | 47901 | 47901 | 0 | 2281 | 2281 | 0 | yes |
| B0 | 9 | 1 | no | 190512 | 190512 | 0 | 9072 | 9072 | 0 | yes |
| B0 | 10 | 3 | yes | 263676 + 239421 + 164892 | 667989 | 0 | 12556 + 11401 + 7852 | 31809 | 0 | yes |
| B0 | 11 | 1 | no | 44037 | 44037 | 0 | 2097 | 2097 | 0 | yes |
| B0 | 12 | 1 | no | 295701 | 295701 | 0 | 14081 | 14081 | 0 | yes |
| B0 | 13 | 1 | no | 56070 | 56070 | 0 | 2670 | 2670 | 0 | yes |
| B0 | 14 | 1 | no | 88998 | 88998 | 0 | 4238 | 4238 | 0 | yes |
| B0 | 15 | 1 | no | 251958 | 251958 | 0 | 11998 | 11998 | 0 | yes |
| B0 | 16 | 1 | no | 104454 | 104454 | 0 | 4974 | 4974 | 0 | yes |
| B0 | 17 | 4 | yes | 2289 + 2352 + 2016 + 2163 | 8820 | 0 | 109 + 112 + 96 + 103 | 420 | 0 | yes |
| B0 | 18 | 1 | no | 51975 | 51975 | 0 | 2475 | 2475 | 0 | yes |
| B0 | 19 | 1 | no | 55965 | 55965 | 0 | 2665 | 2665 | 0 | yes |
| B0 | 20 | 1 | no | 59619 | 59619 | 0 | 2839 | 2839 | 0 | yes |
| B0 | 21 | 1 | no | 39732 | 39732 | 0 | 1892 | 1892 | 0 | yes |
| B0 | 22 | 1 | no | 48657 | 48657 | 0 | 2317 | 2317 | 0 | yes |
| B0 | 23 | 1 | no | 46977 | 46977 | 0 | 2237 | 2237 | 0 | yes |
| B0 | 24 | 1 | no | 192717 | 192717 | 0 | 9177 | 9177 | 0 | yes |
| B2 | 0 | 1 | no | 23505 | 23505 | 0 | 5259 | 5259 | 0 | yes |
| B2 | 1 | 1 | no | 134560 | 134560 | 0 | 31071 | 31071 | 0 | yes |
| B2 | 2 | 1 | no | 93767 | 93767 | 0 | 21153 | 21153 | 0 | yes |
| B2 | 3 | 1 | no | 43204 | 43204 | 0 | 9694 | 9694 | 0 | yes |
| B2 | 4 | 1 | no | 47985 | 47985 | 0 | 10721 | 10721 | 0 | yes |
| B2 | 5 | 3 | yes | 175996 + 137488 + 166146 | 479630 | 0 | 39645 + 29681 + 41059 | 110385 | 0 | yes |
| B2 | 6 | 1 | no | 43103 | 43103 | 0 | 9632 | 9632 | 0 | yes |
| B2 | 7 | 1 | no | 23484 | 23484 | 0 | 5258 | 5258 | 0 | yes |
| B2 | 8 | 1 | no | 28385 | 28385 | 0 | 6352 | 6352 | 0 | yes |
| B2 | 9 | 1 | no | 143424 | 143424 | 0 | 32469 | 32469 | 0 | yes |
| B2 | 10 | 1 | no | 129012 | 129012 | 0 | 30849 | 30849 | 0 | yes |
| B2 | 11 | 1 | no | 25988 | 25988 | 0 | 5821 | 5821 | 0 | yes |
| B2 | 12 | 1 | no | 40163 | 40163 | 0 | 9050 | 9050 | 0 | yes |
| B2 | 13 | 1 | no | 32983 | 32983 | 0 | 7420 | 7420 | 0 | yes |
| B2 | 14 | 1 | no | 52965 | 52965 | 0 | 11830 | 11830 | 0 | yes |
| B2 | 15 | 1 | no | 169358 | 169358 | 0 | 38460 | 38460 | 0 | yes |
| B2 | 16 | 1 | no | 62796 | 62796 | 0 | 14014 | 14014 | 0 | yes |
| B2 | 17 | 4 | yes | 1288 + 1360 + 1045 + 1228 | 4921 | 0 | 290 + 295 + 258 + 278 | 1121 | 0 | yes |
| B2 | 18 | 1 | no | 30852 | 30852 | 0 | 6897 | 6897 | 0 | yes |
| B2 | 19 | 1 | no | 25952 | 25952 | 0 | 5807 | 5807 | 0 | yes |
| B2 | 20 | 1 | no | 32958 | 32958 | 0 | 7432 | 7432 | 0 | yes |
| B2 | 21 | 1 | no | 23520 | 23520 | 0 | 5261 | 5261 | 0 | yes |
| B2 | 22 | 1 | no | 28505 | 28505 | 0 | 6389 | 6389 | 0 | yes |
| B2 | 23 | 1 | no | 25771 | 25771 | 0 | 5799 | 5799 | 0 | yes |
| B2 | 24 | 1 | no | 109933 | 109933 | 0 | 24965 | 24965 | 0 | yes |

<sub>`the attempt-summation identity`</sub>

<sub>combining 3 stage table(s): `the attempt summation identity — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`; `the attempt summation identity — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`; `the attempt summation identity — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table F.9.** *What each optimisation run's convergence test cost, one row per run, configurations stacked: dispatch sweeps and the solve-phase part of them, the output-time loop's sweeps, and for the test the arm stops on its evaluations, components compared and mean width. The two predicates are never summed. n = 3 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and its own n, and that n counts finished optimisation-phase campaign runs of that configuration).*

| arm | seed | stops on | dispatch sweeps | of which solve phase | output-time loop | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **large_tokamak_nof (n = 88)** |  |  |  |  |  |  |  |  |  |  |  |  |  |
| BR | 0 | upstream | 2029 | 2027 | 2 | 0 | 0 | — | — | 1397 | 37719 | 27.0 | 0.00 % |
| BR | 1 | upstream | 2021 | 2019 | 2 | 0 | 0 | — | — | 1389 | 37503 | 27.0 | 0.00 % |
| BR | 2 | upstream | 2279 | 2277 | 2 | 0 | 0 | — | — | 1563 | 42201 | 27.0 | 0.00 % |
| BR | 3 | upstream | 1759 | 1757 | 2 | 0 | 0 | — | — | 1211 | 32697 | 27.0 | 0.00 % |
| BR | 4 | upstream | 1761 | 1759 | 2 | 0 | 0 | — | — | 1213 | 32751 | 27.0 | 0.00 % |
| BR | 6 | upstream | 2036 | 2034 | 2 | 0 | 0 | — | — | 1404 | 37908 | 27.0 | 0.00 % |
| BR | 7 | upstream | 2032 | 2030 | 2 | 0 | 0 | — | — | 1400 | 37800 | 27.0 | 0.00 % |
| BR | 8 | upstream | 2034 | 2032 | 2 | 0 | 0 | — | — | 1402 | 37854 | 27.0 | 0.00 % |
| BR | 9 | upstream | 2026 | 2024 | 2 | 0 | 0 | — | — | 1394 | 37638 | 27.0 | 0.00 % |
| BR | 10 | upstream | 1766 | 1764 | 2 | 0 | 0 | — | — | 1218 | 32886 | 27.0 | 0.00 % |
| BR | 11 | upstream | 2005 | 2003 | 2 | 0 | 0 | — | — | 1373 | 37071 | 27.0 | 0.00 % |
| BR | 12 | upstream | 2029 | 2027 | 2 | 0 | 0 | — | — | 1397 | 37719 | 27.0 | 0.00 % |
| BR | 13 | upstream | 2021 | 2019 | 2 | 0 | 0 | — | — | 1389 | 37503 | 27.0 | 0.00 % |
| BR | 14 | upstream | 2279 | 2277 | 2 | 0 | 0 | — | — | 1563 | 42201 | 27.0 | 0.00 % |
| BR | 15 | upstream | 1758 | 1756 | 2 | 0 | 0 | — | — | 1210 | 32670 | 27.0 | 0.00 % |
| BR | 16 | upstream | 1757 | 1755 | 2 | 0 | 0 | — | — | 1209 | 32643 | 27.0 | 0.00 % |
| BR | 17 | upstream | 2027 | 2025 | 2 | 0 | 0 | — | — | 1395 | 37665 | 27.0 | 0.00 % |
| BR | 18 | upstream | 2027 | 2025 | 2 | 0 | 0 | — | — | 1395 | 37665 | 27.0 | 0.00 % |
| BR | 19 | upstream | 2030 | 2028 | 2 | 0 | 0 | — | — | 1398 | 37746 | 27.0 | 0.00 % |
| BR | 22 | upstream | 1763 | 1761 | 2 | 0 | 0 | — | — | 1215 | 32805 | 27.0 | 0.00 % |
| BR | 23 | upstream | 2032 | 2030 | 2 | 0 | 0 | — | — | 1400 | 37800 | 27.0 | 0.00 % |
| BR | 24 | upstream | 2028 | 2026 | 2 | 0 | 0 | — | — | 1396 | 37692 | 27.0 | 0.00 % |
| B0 | 0 | coupling_state | 2071 | 2069 | 2 | 2069 | 1737960 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 1 | coupling_state | 2073 | 2071 | 2 | 2071 | 1739640 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 2 | coupling_state | 2365 | 2363 | 2 | 2363 | 1984920 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 3 | coupling_state | 1797 | 1795 | 2 | 1795 | 1507800 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 4 | coupling_state | 1792 | 1790 | 2 | 1790 | 1503600 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 6 | coupling_state | 2071 | 2069 | 2 | 2069 | 1737960 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 7 | coupling_state | 2070 | 2068 | 2 | 2068 | 1737120 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 8 | coupling_state | 2070 | 2068 | 2 | 2068 | 1737120 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 9 | coupling_state | 2072 | 2070 | 2 | 2070 | 1738800 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 10 | coupling_state | 1792 | 1790 | 2 | 1790 | 1503600 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 11 | coupling_state | 2125 | 2123 | 2 | 2123 | 1783320 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 12 | coupling_state | 2070 | 2068 | 2 | 2068 | 1737120 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 13 | coupling_state | 2075 | 2073 | 2 | 2073 | 1741320 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 14 | coupling_state | 2395 | 2393 | 2 | 2393 | 2010120 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 15 | coupling_state | 1799 | 1797 | 2 | 1797 | 1509480 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 16 | coupling_state | 1796 | 1794 | 2 | 1794 | 1506960 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 17 | coupling_state | 2072 | 2070 | 2 | 2070 | 1738800 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 18 | coupling_state | 2065 | 2063 | 2 | 2063 | 1732920 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 19 | coupling_state | 2069 | 2067 | 2 | 2067 | 1736280 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 22 | coupling_state | 1800 | 1798 | 2 | 1798 | 1510320 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 23 | coupling_state | 2068 | 2066 | 2 | 2066 | 1735440 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B0 | 24 | coupling_state | 2077 | 2075 | 2 | 2075 | 1743000 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 0 | coupling_state | 2102 | 2102 | 0 | 2102 | 1765680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 1 | coupling_state | 2100 | 2100 | 0 | 2100 | 1764000 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 2 | coupling_state | 2102 | 2102 | 0 | 2102 | 1765680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 3 | coupling_state | 1824 | 1824 | 0 | 1824 | 1532160 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 4 | coupling_state | 1820 | 1820 | 0 | 1820 | 1528800 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 6 | coupling_state | 2097 | 2097 | 0 | 2097 | 1761480 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 7 | coupling_state | 2097 | 2097 | 0 | 2097 | 1761480 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 8 | coupling_state | 2101 | 2101 | 0 | 2101 | 1764840 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 9 | coupling_state | 2103 | 2103 | 0 | 2103 | 1766520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 10 | coupling_state | 2100 | 2100 | 0 | 2100 | 1764000 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 11 | coupling_state | 2118 | 2118 | 0 | 2118 | 1779120 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 12 | coupling_state | 2103 | 2103 | 0 | 2103 | 1766520 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 13 | coupling_state | 2102 | 2102 | 0 | 2102 | 1765680 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 14 | coupling_state | 2141 | 2141 | 0 | 2141 | 1798440 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 15 | coupling_state | 1822 | 1822 | 0 | 1822 | 1530480 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 16 | coupling_state | 1821 | 1821 | 0 | 1821 | 1529640 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 17 | coupling_state | 2104 | 2104 | 0 | 2104 | 1767360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 18 | coupling_state | 1821 | 1821 | 0 | 1821 | 1529640 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 19 | coupling_state | 2380 | 2380 | 0 | 2380 | 1999200 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 22 | coupling_state | 1824 | 1824 | 0 | 1824 | 1532160 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 23 | coupling_state | 2104 | 2104 | 0 | 2104 | 1767360 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B1 | 24 | coupling_state | 2096 | 2096 | 0 | 2096 | 1760640 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |
| B2 | 0 | coupling_state | 5500 | 5499 | 0 | 4839 | 1156926 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 1 | coupling_state | 5497 | 5496 | 0 | 4836 | 1156225 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 2 | coupling_state | 5500 | 5499 | 0 | 4839 | 1156926 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 3 | coupling_state | 4768 | 4767 | 0 | 4195 | 1002938 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 4 | coupling_state | 4764 | 4763 | 0 | 4191 | 1001978 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 6 | coupling_state | 5492 | 5491 | 0 | 4831 | 1154989 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 7 | coupling_state | 5494 | 5493 | 0 | 4833 | 1155468 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 8 | coupling_state | 5498 | 5497 | 0 | 4837 | 1156465 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 9 | coupling_state | 5500 | 5499 | 0 | 4839 | 1156945 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 10 | coupling_state | 5498 | 5497 | 0 | 4837 | 1156446 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 11 | coupling_state | 5487 | 5486 | 0 | 4826 | 1153825 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 12 | coupling_state | 5500 | 5499 | 0 | 4839 | 1156871 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 13 | coupling_state | 5498 | 5497 | 0 | 4837 | 1156447 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 14 | coupling_state | 5495 | 5494 | 0 | 4834 | 1156031 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 15 | coupling_state | 4767 | 4766 | 0 | 4194 | 1002716 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 16 | coupling_state | 4767 | 4766 | 0 | 4194 | 1002697 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 17 | coupling_state | 5495 | 5494 | 0 | 4834 | 1155822 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 18 | coupling_state | 4764 | 4763 | 0 | 4191 | 1002033 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 19 | coupling_state | 6233 | 6232 | 0 | 5484 | 1311098 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 22 | coupling_state | 4769 | 4768 | 0 | 4196 | 1003196 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 23 | coupling_state | 5502 | 5501 | 0 | 4841 | 1157406 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 24 | coupling_state | 5493 | 5492 | 0 | 4832 | 1155228 | 239.1 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0.00 % |
| **low_aspect_ratio_DEMO (n = 84)** |  |  |  |  |  |  |  |  |  |  |  |  |  |
| BR | 0 | upstream | 4286 | 4284 | 2 | 0 | 0 | — | — | 3044 | 68069 | 22.4 | 0.00 % |
| BR | 1 | upstream | 31869 | 31867 | 2 | 0 | 0 | — | — | 22627 | 499852 | 22.1 | 0.00 % |
| BR | 2 | upstream | 548 | 546 | 2 | 0 | 0 | — | — | 386 | 8311 | 21.5 | 0.00 % |
| BR | 4 | upstream | 515 | 513 | 2 | 0 | 0 | — | — | 353 | 7703 | 21.8 | 0.00 % |
| BR | 5 | upstream | 2903 | 2901 | 2 | 0 | 0 | — | — | 2061 | 45911 | 22.3 | 0.00 % |
| BR | 6 | upstream | 9255 | 9253 | 2 | 0 | 0 | — | — | 6573 | 146973 | 22.4 | 0.00 % |
| BR | 7 | upstream | 540 | 538 | 2 | 0 | 0 | — | — | 378 | 8353 | 22.1 | 0.00 % |
| BR | 8 | upstream | 527 | 525 | 2 | 0 | 0 | — | — | 365 | 8015 | 22.0 | 0.00 % |
| BR | 9 | upstream | 3455 | 3453 | 2 | 0 | 0 | — | — | 2453 | 54753 | 22.3 | 0.00 % |
| BR | 10 | upstream | 2898 | 2896 | 2 | 0 | 0 | — | — | 2056 | 45856 | 22.3 | 0.00 % |
| BR | 11 | upstream | 2906 | 2904 | 2 | 0 | 0 | — | — | 2064 | 45939 | 22.3 | 0.00 % |
| BR | 12 | upstream | 4287 | 4285 | 2 | 0 | 0 | — | — | 3045 | 68020 | 22.3 | 0.00 % |
| BR | 13 | upstream | 5388 | 5386 | 2 | 0 | 0 | — | — | 3826 | 85501 | 22.3 | 0.00 % |
| BR | 14 | upstream | 532 | 530 | 2 | 0 | 0 | — | — | 370 | 8095 | 21.9 | 0.00 % |
| BR | 15 | upstream | 17515 | 17513 | 2 | 0 | 0 | — | — | 12433 | 278158 | 22.4 | 0.00 % |
| BR | 16 | upstream | 541 | 539 | 2 | 0 | 0 | — | — | 379 | 8379 | 22.1 | 0.00 % |
| BR | 17 | upstream | 542 | 540 | 2 | 0 | 0 | — | — | 380 | 8405 | 22.1 | 0.00 % |
| BR | 18 | upstream | 4004 | 4002 | 2 | 0 | 0 | — | — | 2842 | 63492 | 22.3 | 0.00 % |
| BR | 19 | upstream | 3172 | 3170 | 2 | 0 | 0 | — | — | 2250 | 50250 | 22.3 | 0.00 % |
| BR | 20 | upstream | 536 | 534 | 2 | 0 | 0 | — | — | 374 | 8099 | 21.7 | 0.00 % |
| BR | 22 | upstream | 532 | 530 | 2 | 0 | 0 | — | — | 370 | 8145 | 22.0 | 0.00 % |
| BR | 23 | upstream | 542 | 540 | 2 | 0 | 0 | — | — | 380 | 8405 | 22.1 | 0.00 % |
| BR | 24 | upstream | 545 | 543 | 2 | 0 | 0 | — | — | 383 | 8483 | 22.1 | 0.00 % |
| B0 | 0 | coupling_state | 4139 | 4137 | 2 | 4137 | 3499902 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 1 | coupling_state | 31215 | 31213 | 2 | 31213 | 26406198 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 2 | coupling_state | 553 | 551 | 2 | 551 | 466146 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 5 | coupling_state | 2809 | 2807 | 2 | 2807 | 2374722 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 6 | coupling_state | 8934 | 8932 | 2 | 8932 | 7556472 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 7 | coupling_state | 542 | 540 | 2 | 540 | 456840 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 8 | coupling_state | 540 | 538 | 2 | 538 | 455148 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 9 | coupling_state | 3339 | 3337 | 2 | 3337 | 2823102 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 10 | coupling_state | 2809 | 2807 | 2 | 2807 | 2374722 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 11 | coupling_state | 2809 | 2807 | 2 | 2807 | 2374722 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 12 | coupling_state | 4141 | 4139 | 2 | 4139 | 3501594 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 13 | coupling_state | 5203 | 5201 | 2 | 5201 | 4400046 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 14 | coupling_state | 551 | 549 | 2 | 549 | 464454 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 15 | coupling_state | 16920 | 16918 | 2 | 16918 | 14312628 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 16 | coupling_state | 537 | 535 | 2 | 535 | 452610 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 17 | coupling_state | 539 | 537 | 2 | 537 | 454302 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 18 | coupling_state | 3868 | 3866 | 2 | 3866 | 3270636 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 19 | coupling_state | 3072 | 3070 | 2 | 3070 | 2597220 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 20 | coupling_state | 545 | 543 | 2 | 543 | 459378 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 23 | coupling_state | 541 | 539 | 2 | 539 | 455994 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B0 | 24 | coupling_state | 547 | 545 | 2 | 545 | 461070 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 0 | coupling_state | 3330 | 3330 | 0 | 3330 | 2817180 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 1 | coupling_state | 3868 | 3868 | 0 | 3868 | 3272328 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 2 | coupling_state | 538 | 538 | 0 | 538 | 455148 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 5 | coupling_state | 9440 | 9440 | 0 | 9440 | 7986240 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 6 | coupling_state | 5455 | 5455 | 0 | 5455 | 4614930 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 7 | coupling_state | 523 | 523 | 0 | 523 | 442458 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 8 | coupling_state | 523 | 523 | 0 | 523 | 442458 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 9 | coupling_state | 3600 | 3600 | 0 | 3600 | 3045600 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 11 | coupling_state | 17171 | 17171 | 0 | 17171 | 14526666 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 12 | coupling_state | 2534 | 2534 | 0 | 2534 | 2143764 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 13 | coupling_state | 4661 | 4661 | 0 | 4661 | 3943206 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 14 | coupling_state | 533 | 533 | 0 | 533 | 450918 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 15 | coupling_state | 4124 | 4124 | 0 | 4124 | 3488904 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 16 | coupling_state | 537 | 537 | 0 | 537 | 454302 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 17 | coupling_state | 538 | 538 | 0 | 538 | 455148 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 18 | coupling_state | 3077 | 3077 | 0 | 3077 | 2603142 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 19 | coupling_state | 2535 | 2535 | 0 | 2535 | 2144610 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 20 | coupling_state | 541 | 541 | 0 | 541 | 457686 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 23 | coupling_state | 539 | 539 | 0 | 539 | 455994 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B1 | 24 | coupling_state | 530 | 530 | 0 | 530 | 448380 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |
| B2 | 0 | coupling_state | 8763 | 8762 | 0 | 7712 | 1855182 | 240.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 1 | coupling_state | 10183 | 10182 | 0 | 8964 | 2156500 | 240.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 2 | coupling_state | 1393 | 1392 | 0 | 1224 | 294788 | 240.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 5 | coupling_state | 24884 | 24883 | 0 | 21901 | 5268614 | 240.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 6 | coupling_state | 14383 | 14382 | 0 | 12660 | 3045529 | 240.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 7 | coupling_state | 1385 | 1384 | 0 | 1216 | 292750 | 240.7 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 8 | coupling_state | 1380 | 1379 | 0 | 1211 | 291645 | 240.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 9 | coupling_state | 9481 | 9480 | 0 | 8346 | 2007830 | 240.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 11 | coupling_state | 45222 | 45221 | 0 | 39803 | 9575641 | 240.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 12 | coupling_state | 6676 | 6675 | 0 | 5877 | 1413837 | 240.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 13 | coupling_state | 12283 | 12282 | 0 | 10812 | 2601007 | 240.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 14 | coupling_state | 1396 | 1395 | 0 | 1227 | 295305 | 240.7 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 15 | coupling_state | 10869 | 10868 | 0 | 9566 | 2301183 | 240.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 16 | coupling_state | 1397 | 1396 | 0 | 1228 | 295694 | 240.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 17 | coupling_state | 1402 | 1401 | 0 | 1233 | 296769 | 240.7 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 18 | coupling_state | 8088 | 8087 | 0 | 7121 | 1713243 | 240.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 19 | coupling_state | 6672 | 6671 | 0 | 5873 | 1412839 | 240.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 20 | coupling_state | 1405 | 1404 | 0 | 1236 | 297630 | 240.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 23 | coupling_state | 1404 | 1403 | 0 | 1235 | 297287 | 240.7 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| B2 | 24 | coupling_state | 1392 | 1391 | 0 | 1223 | 294383 | 240.7 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0.00 % |
| **st_regression (n = 75; arms BR·B0·B2)** |  |  |  |  |  |  |  |  |  |  |  |  |  |
| BR | 0 | upstream | 1891 | 1889 | 2 | 0 | 0 | — | — | 1319 | 18491 | 14.0 | 0.00 % |
| BR | 1 | upstream | 8401 | 8399 | 2 | 0 | 0 | — | — | 5789 | 84431 | 14.6 | 0.00 % |
| BR | 2 | upstream | 10010 | 10008 | 2 | 0 | 0 | — | — | 7128 | 100674 | 14.1 | 0.00 % |
| BR | 3 | upstream | 3450 | 3448 | 2 | 0 | 0 | — | — | 2398 | 33646 | 14.0 | 0.00 % |
| BR | 4 | upstream | 3807 | 3805 | 2 | 0 | 0 | — | — | 2635 | 37357 | 14.2 | 0.00 % |
| BR | 5 | upstream | 7637 | 7635 | 2 | 0 | 0 | — | — | 5265 | 77049 | 14.6 | 0.00 % |
| BR | 6 | upstream | 3421 | 3419 | 2 | 0 | 0 | — | — | 2369 | 33527 | 14.2 | 0.00 % |
| BR | 7 | upstream | 1896 | 1894 | 2 | 0 | 0 | — | — | 1324 | 18586 | 14.0 | 0.00 % |
| BR | 8 | upstream | 2267 | 2265 | 2 | 0 | 0 | — | — | 1575 | 22113 | 14.0 | 0.00 % |
| BR | 9 | upstream | 11612 | 11610 | 2 | 0 | 0 | — | — | 7980 | 117618 | 14.7 | 0.00 % |
| BR | 10 | upstream | 34192 | 34190 | 2 | 0 | 0 | — | — | 23600 | 343622 | 14.6 | 0.00 % |
| BR | 11 | upstream | 2091 | 2089 | 2 | 0 | 0 | — | — | 1459 | 20431 | 14.0 | 0.00 % |
| BR | 12 | upstream | 13324 | 13322 | 2 | 0 | 0 | — | — | 9362 | 132572 | 14.2 | 0.00 % |
| BR | 13 | upstream | 2658 | 2656 | 2 | 0 | 0 | — | — | 1846 | 25948 | 14.1 | 0.00 % |
| BR | 14 | upstream | 4225 | 4223 | 2 | 0 | 0 | — | — | 2933 | 41669 | 14.2 | 0.00 % |
| BR | 15 | upstream | 5897 | 5895 | 2 | 0 | 0 | — | — | 4065 | 59235 | 14.6 | 0.00 % |
| BR | 16 | upstream | 4614 | 4612 | 2 | 0 | 0 | — | — | 3202 | 45700 | 14.3 | 0.00 % |
| BR | 17 | upstream | 386 | 384 | 2 | 0 | 0 | — | — | 264 | 3468 | 13.1 | 0.00 % |
| BR | 18 | upstream | 2460 | 2458 | 2 | 0 | 0 | — | — | 1708 | 24136 | 14.1 | 0.00 % |
| BR | 19 | upstream | 2077 | 2075 | 2 | 0 | 0 | — | — | 1445 | 20255 | 14.0 | 0.00 % |
| BR | 20 | upstream | 2671 | 2669 | 2 | 0 | 0 | — | — | 1859 | 26069 | 14.0 | 0.00 % |
| BR | 21 | upstream | 1889 | 1887 | 2 | 0 | 0 | — | — | 1317 | 18471 | 14.0 | 0.00 % |
| BR | 22 | upstream | 2261 | 2259 | 2 | 0 | 0 | — | — | 1569 | 21999 | 14.0 | 0.00 % |
| BR | 23 | upstream | 2080 | 2078 | 2 | 0 | 0 | — | — | 1448 | 20222 | 14.0 | 0.00 % |
| BR | 24 | upstream | 39951 | 39949 | 2 | 0 | 0 | — | — | 27559 | 401527 | 14.6 | 0.00 % |
| B0 | 0 | coupling_state | 2038 | 2036 | 2 | 2036 | 1683772 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 1 | coupling_state | 10764 | 10762 | 2 | 10762 | 8900174 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 2 | coupling_state | 10422 | 10420 | 2 | 10420 | 8617340 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 3 | coupling_state | 3643 | 3641 | 2 | 3641 | 3011107 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 4 | coupling_state | 3843 | 3841 | 2 | 3841 | 3176507 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 5 | coupling_state | 8355 | 8353 | 2 | 8353 | 6907931 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 6 | coupling_state | 3452 | 3450 | 2 | 3450 | 2853150 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 7 | coupling_state | 1894 | 1892 | 2 | 1892 | 1564684 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 8 | coupling_state | 2283 | 2281 | 2 | 2281 | 1886387 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 9 | coupling_state | 9074 | 9072 | 2 | 9072 | 7502544 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 10 | coupling_state | 31811 | 31809 | 2 | 31809 | 26306043 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 11 | coupling_state | 2099 | 2097 | 2 | 2097 | 1734219 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 12 | coupling_state | 14083 | 14081 | 2 | 14081 | 11644987 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 13 | coupling_state | 2672 | 2670 | 2 | 2670 | 2208090 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 14 | coupling_state | 4240 | 4238 | 2 | 4238 | 3504826 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 15 | coupling_state | 12000 | 11998 | 2 | 11998 | 9922346 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 16 | coupling_state | 4976 | 4974 | 2 | 4974 | 4113498 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 17 | coupling_state | 422 | 420 | 2 | 420 | 347340 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 18 | coupling_state | 2477 | 2475 | 2 | 2475 | 2046825 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 19 | coupling_state | 2667 | 2665 | 2 | 2665 | 2203955 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 20 | coupling_state | 2841 | 2839 | 2 | 2839 | 2347853 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 21 | coupling_state | 1894 | 1892 | 2 | 1892 | 1564684 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 22 | coupling_state | 2319 | 2317 | 2 | 2317 | 1916159 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 23 | coupling_state | 2239 | 2237 | 2 | 2237 | 1849999 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B0 | 24 | coupling_state | 9179 | 9177 | 2 | 9177 | 7589379 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |
| B2 | 0 | coupling_state | 5260 | 5259 | 0 | 4119 | 970258 | 235.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.84 % |
| B2 | 1 | coupling_state | 31072 | 31071 | 0 | 24051 | 5659602 | 235.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.30 % |
| B2 | 2 | coupling_state | 21154 | 21153 | 0 | 16533 | 3892592 | 235.4 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.92 % |
| B2 | 3 | coupling_state | 9695 | 9694 | 0 | 7594 | 1788185 | 235.5 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.83 % |
| B2 | 4 | coupling_state | 10722 | 10721 | 0 | 8381 | 1972937 | 235.4 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.91 % |
| B2 | 5 | coupling_state | 110386 | 110385 | 0 | 85605 | 20138750 | 235.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.22 % |
| B2 | 6 | coupling_state | 9633 | 9632 | 0 | 7532 | 1773223 | 235.4 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.90 % |
| B2 | 7 | coupling_state | 5259 | 5258 | 0 | 4118 | 970028 | 235.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.84 % |
| B2 | 8 | coupling_state | 6353 | 6352 | 0 | 4972 | 1171089 | 235.5 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.86 % |
| B2 | 9 | coupling_state | 32470 | 32469 | 0 | 25209 | 5925850 | 235.1 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.18 % |
| B2 | 10 | coupling_state | 30850 | 30849 | 0 | 23709 | 5588124 | 235.7 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.57 % |
| B2 | 11 | coupling_state | 5822 | 5821 | 0 | 4561 | 1074441 | 235.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.82 % |
| B2 | 12 | coupling_state | 9051 | 9050 | 0 | 7070 | 1664464 | 235.4 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.94 % |
| B2 | 13 | coupling_state | 7421 | 7420 | 0 | 5800 | 1366359 | 235.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.91 % |
| B2 | 14 | coupling_state | 11831 | 11830 | 0 | 9250 | 2177370 | 235.4 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.90 % |
| B2 | 15 | coupling_state | 38461 | 38460 | 0 | 29880 | 7024544 | 235.1 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.15 % |
| B2 | 16 | coupling_state | 14015 | 14014 | 0 | 10954 | 2577921 | 235.3 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.92 % |
| B2 | 17 | coupling_state | 1122 | 1121 | 0 | 881 | 207690 | 235.7 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.70 % |
| B2 | 18 | coupling_state | 6898 | 6897 | 0 | 5397 | 1270730 | 235.5 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.87 % |
| B2 | 19 | coupling_state | 5808 | 5807 | 0 | 4547 | 1071105 | 235.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.85 % |
| B2 | 20 | coupling_state | 7433 | 7432 | 0 | 5812 | 1369273 | 235.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.90 % |
| B2 | 21 | coupling_state | 5262 | 5261 | 0 | 4121 | 970697 | 235.5 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.83 % |
| B2 | 22 | coupling_state | 6390 | 6389 | 0 | 5009 | 1179088 | 235.4 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.80 % |
| B2 | 23 | coupling_state | 5800 | 5799 | 0 | 4539 | 1069466 | 235.6 | M1 268, M2 216, M3 223 | 0 | 0 | — | 10.86 % |
| B2 | 24 | coupling_state | 24966 | 24965 | 0 | 19385 | 4558929 | 235.2 | M1 268, M2 216, M3 223 | 0 | 0 | — | 11.18 % |

<sub>`per-sweep overhead, the optimisation phase`</sub>

<sub>combining 3 stage table(s): `per-sweep overhead — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`; `per-sweep overhead — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`; `per-sweep overhead — st_regression — campaign_optimisation · BR·B0·B2`</sub>

## F.3 Appendix D's tables with their per-seed columns

The full versions of the report's tables whose columns listing a value per seed inside one cell (the paired seeds, the seeds of the set, the attempts per seed, the components above τ per run) the report omits. Every other cell is identical to the report's.

**Table F.10.** *The entry reference, one row per configuration and ruler: what one flat `A0` evaluation from the input file's own design point cost, what it left at exit on both rulers, and whether it finished. This is the once-per-run cold-start term of plan §3.4, reported beside the displaced and stencil regimes and never pooled with them; it carries one run per configuration, so there is no pair, no ratio and no bracket. The cost and outcome cells are per configuration and repeat down its two ruler rows. n = 9 (row group(s) of this table, each over its own population with its own n in its sub-heading row; never pooled).*

| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A0 at seeds | vs A0 pooled | vs A0 median | worse | ruler | n (runs) | with a restricted statistic | restricted median | restricted p90 | restricted argmax | whole-state median | whole-state p90 | components excluded | audit position | audit instrument (snapshot positions taken) | scheduled | ok | rows sum | detail (traceback's last line × count) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **large_tokamak_nof — 3 construction(s): `cost per call` n = 1; `matched accuracy` n = 1; `failure taxonomy` n = 1** |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| A0 | 1/1 | 126.0 | [126, 126] | 6.00 | FLAT 6 | 0.0 | — | — | — | — | frozen | 1 | 1 | 8.092e-09 | 8.092e-09 | power.qac | 1.465e-08 | 1.465e-08 | 122 | after_single_evaluation | no snapshot recorded on this record | 1 | 1 | yes | — |
| A0 | 1/1 | 126.0 | [126, 126] | 6.00 | FLAT 6 | 0.0 | — | — | — | — | mixed | 1 | 1 | 4.529e-09 | 4.529e-09 | power.qac | 4.529e-09 | 4.529e-09 | 122 | after_single_evaluation | no snapshot recorded on this record | 1 | 1 | yes | — |
| **low_aspect_ratio_DEMO — 3 construction(s): `cost per call` n = 1; `matched accuracy` n = 1; `failure taxonomy` n = 1** |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| A0 | 1/1 | 105.0 | [105, 105] | 5.00 | FLAT 5 | 0.0 | — | — | — | — | frozen | 1 | 1 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record | 1 | 1 | yes | — |
| A0 | 1/1 | 105.0 | [105, 105] | 5.00 | FLAT 5 | 0.0 | — | — | — | — | mixed | 1 | 1 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record | 1 | 1 | yes | — |
| **st_regression — 3 construction(s): `cost per call` n = 1; `matched accuracy` n = 1; `failure taxonomy` n = 1** |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| A0 | 1/1 | 147.0 | [147, 147] | 7.00 | FLAT 7 | 0.0 | — | — | — | — | frozen | 1 | 1 | 3.276e-09 | 3.276e-09 | superconducting_tfcoil.a_tf_plasma_case | 3.276e-09 | 3.276e-09 | 123 | after_single_evaluation | no snapshot recorded on this record | 1 | 1 | yes | — |
| A0 | 1/1 | 147.0 | [147, 147] | 7.00 | FLAT 7 | 0.0 | — | — | — | — | mixed | 1 | 1 | 2.286e-09 | 2.286e-09 | superconducting_tfcoil.a_tf_plasma_case | 2.286e-09 | 2.286e-09 | 123 | after_single_evaluation | no snapshot recorded on this record | 1 | 1 | yes | — |

<sub>`the reference entries`</sub>

<sub>combining 9 stage table(s): `cost per call — large_tokamak_nof — campaign_entry_references`; `matched accuracy — large_tokamak_nof — campaign_entry_references`; `failure taxonomy — large_tokamak_nof — campaign_entry_references`; `cost per call — low_aspect_ratio_DEMO — campaign_entry_references`; `matched accuracy — low_aspect_ratio_DEMO — campaign_entry_references`; `failure taxonomy — low_aspect_ratio_DEMO — campaign_entry_references`; `cost per call — st_regression — campaign_entry_references`; `matched accuracy — st_regression — campaign_entry_references`; `failure taxonomy — st_regression — campaign_entry_references`</sub>

**Table F.11.** *Node calls per `call_models` evaluation by arm, configuration and regime, with the ratio against the declared reference read three ways: pooled, as the per-run median, and as the count of runs on which the arm cost more. The reference is `A1` on a pulsed configuration and `A0` on `st_regression`; each sub-heading row names its regime and its own n. Prime (arrangement-method) calls stand beside the node calls and are never in them. n = 9 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and source regime and its own n, and that n counts evaluation-phase campaign runs of that configuration).*

| arm | ok/run | node calls per evaluation [min, max] | sweeps / eval | sweeps by block | arrangement·method calls | paired with the reference at | vs reference pooled | vs reference median | worse |
|---|---|---|---|---|---|---|---|---|---|
| **large_tokamak_nof · campaign_displaced (n = 100)** |  |  |  |  |  |  |  |  |  |
| AR | 25/25 | 104.2 [84, 105] | 4.96 | — | 0.0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | **0.9688** | 1.0000 | 0 |
| A0 | 25/25 | 115.9 [105, 126] | 5.52 | FLAT 138 | 0.0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | **1.0781** | 1.0000 | 10 |
| A1 | 25/25 | 107.5 [84, 126] | 5.12 | FLAT 128 | 0.0 | — | — | — | — |
| A2 | 25/25 | 60.5 [60, 63] | 13.16 | FF 0, M1 100, M2 129, M3 75, PULSE 0 | 13.2 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | **0.5625** | 0.5714 | 0 |
| **low_aspect_ratio_DEMO · campaign_displaced (n = 100)** |  |  |  |  |  |  |  |  |  |
| AR | 25/25 | 105 | 5.00 | — | 0.0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | **1.0163** | 1.0000 | 2 |
| A0 | 25/25 | 105 | 5.00 | FLAT 125 | 0.0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | **1.0163** | 1.0000 | 2 |
| A1 | 25/25 | 103.3 [84, 105] | 4.92 | FLAT 123 | 0.0 | — | — | — | — |
| A2 | 25/25 | 59.6 [57, 60] | 12.88 | FF 0, M1 100, M2 122, M3 75, PULSE 0 | 12.9 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | **0.5772** | 0.5714 | 0 |
| **st_regression · campaign_displaced (n = 75)** |  |  |  |  |  |  |  |  |  |
| AR | 25/25 | 103.3 [84, 105] | 4.92 | — | 0.0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | **0.8425** | 0.8333 | 0 |
| A0 | 25/25 | 122.6 [105, 126] | 5.84 | FLAT 146 | 0.0 | — | — | — | — |
| A2 | 25/25 | 61.5 [59, 62] | 14.84 | FF 0, M1 100, M2 146, M3 75, PULSE 25 | 14.8 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | **0.5016** | 0.4921 | 0 |
| **large_tokamak_nof · campaign_stencil_forward (n = 80)** |  |  |  |  |  |  |  |  |  |
| AR | 20/20 | 62.0 [42, 84] | 2.95 | — | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | **0.9833** | 1.0000 | 0 |
| A0 | 20/20 | 66.2 [42, 105] | 3.15 | FLAT 63 | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | **1.0500** | 1.0000 | 3 |
| A1 | 20/20 | 63.0 [42, 105] | 3.00 | FLAT 60 | 0.0 | — | — | — | — |
| A2 | 20/20 | 39.1 [20, 55] | 7.60 | FF 0, M1 38, M2 49, M3 45, PULSE 0 | 7.6 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | **0.6214** | 0.6071 | 0 |
| **low_aspect_ratio_DEMO · campaign_stencil_forward (n = 76)** |  |  |  |  |  |  |  |  |  |
| AR | 19/19 | 67.4 [42, 105] | 3.21 | — | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | **1.0702** | 1.0000 | 4 |
| A0 | 19/19 | 66.3 [42, 105] | 3.16 | FLAT 60 | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | **1.0526** | 1.0000 | 3 |
| A1 | 19/19 | 63.0 [42, 84] | 3.00 | FLAT 57 | 0.0 | — | — | — | — |
| A2 | 19/19 | 40.3 [33, 55] | 7.63 | FF 0, M1 36, M2 45, M3 45, PULSE 0 | 7.6 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | **0.6399** | 0.6071 | 0 |
| **st_regression · campaign_stencil_forward (n = 42)** |  |  |  |  |  |  |  |  |  |
| AR | 14/14 | 63.0 [42, 84] | 3.00 | — | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | **0.9333** | 1.0000 | 0 |
| A0 | 14/14 | 67.5 [42, 84] | 3.21 | FLAT 45 | 0.0 | — | — | — | — |
| A2 | 14/14 | 38.9 [19, 50] | 8.64 | FF 0, M1 31, M2 29, M3 33, PULSE 14 | 8.6 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | **0.5767** | 0.5714 | 0 |
| **large_tokamak_nof · campaign_stencil_backward (n = 80)** |  |  |  |  |  |  |  |  |  |
| AR | 20/20 | 60.9 [42, 84] | 2.90 | — | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | **0.9667** | 1.0000 | 0 |
| A0 | 20/20 | 66.2 [42, 105] | 3.15 | FLAT 63 | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | **1.0500** | 1.0000 | 3 |
| A1 | 20/20 | 63.0 [42, 105] | 3.00 | FLAT 60 | 0.0 | — | — | — | — |
| A2 | 20/20 | 40.4 [20, 55] | 7.70 | FF 0, M1 38, M2 49, M3 47, PULSE 0 | 7.7 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | **0.6405** | 0.6071 | 0 |
| **low_aspect_ratio_DEMO · campaign_stencil_backward (n = 76)** |  |  |  |  |  |  |  |  |  |
| AR | 19/19 | 67.4 [42, 105] | 3.21 | — | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | **1.0517** | 1.0000 | 4 |
| A0 | 19/19 | 68.5 [42, 105] | 3.26 | FLAT 62 | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | **1.0690** | 1.0000 | 4 |
| A1 | 19/19 | 64.1 [42, 84] | 3.05 | FLAT 58 | 0.0 | — | — | — | — |
| A2 | 19/19 | 42.4 [33, 55] | 7.84 | FF 0, M1 36, M2 46, M3 48, PULSE 0 | 7.8 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | **0.6609** | 0.7143 | 0 |
| **st_regression · campaign_stencil_backward (n = 42)** |  |  |  |  |  |  |  |  |  |
| AR | 14/14 | 66.0 [42, 84] | 3.14 | — | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | **0.9362** | 1.0000 | 0 |
| A0 | 14/14 | 70.5 [42, 105] | 3.36 | FLAT 47 | 0.0 | — | — | — | — |
| A2 | 14/14 | 39.4 [19, 53] | 8.79 | FF 0, M1 31, M2 31, M3 33, PULSE 14 | 8.8 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | **0.5583** | 0.5238 | 0 |

<sub>`cost per call`</sub>

<sub>combining 9 stage table(s): `cost per call — large_tokamak_nof — campaign_displaced`; `cost per call — low_aspect_ratio_DEMO — campaign_displaced`; `cost per call — st_regression — campaign_displaced`; `cost per call — large_tokamak_nof — campaign_stencil_forward`; `cost per call — low_aspect_ratio_DEMO — campaign_stencil_forward`; `cost per call — st_regression — campaign_stencil_forward`; `cost per call — large_tokamak_nof — campaign_stencil_backward`; `cost per call — low_aspect_ratio_DEMO — campaign_stencil_backward`; `cost per call — st_regression — campaign_stencil_backward`</sub>

**Table F.12.** *What pinning the burn time to a constant costs per call, and the inconsistency it leaves: six rows, one per pulsed configuration and regime. `st_regression` is steady-state and has no burn-time coupling, so the rung does not exist there. n = 6 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and source regime and its own n, and that n counts A0 and A1 campaign runs of that configuration).*

| n | paired at | A1/A0 pooled | median | worse | burn-time residual, s: median [min, max] | relative (median) |
|---|---|---|---|---|---|---|
| **large_tokamak_nof · campaign_displaced (n = 50)** |  |  |  |  |  |  |
| 25 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | **0.9275** | 1.0000 | 0 | 1.546e+02 [12.8111, 406.884] | 6.298e-02 |
| **low_aspect_ratio_DEMO · campaign_displaced (n = 50)** |  |  |  |  |  |  |
| 25 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | **0.9840** | 1.0000 | 0 | 5.258e+02 [1.64882, 1436.26] | 5.275e-02 |
| **large_tokamak_nof · campaign_stencil_forward (n = 40)** |  |  |  |  |  |  |
| 20 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | **0.9524** | 1.0000 | 0 | 1.173e+00 [2.61319e-07, 13.1365] | 4.566e-04 |
| **low_aspect_ratio_DEMO · campaign_stencil_forward (n = 38)** |  |  |  |  |  |  |
| 19 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | **0.9500** | 1.0000 | 0 | 4.176e+00 [0, 34.2015] | 4.016e-04 |
| **large_tokamak_nof · campaign_stencil_backward (n = 40)** |  |  |  |  |  |  |
| 20 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | **0.9524** | 1.0000 | 0 | 1.175e+00 [2.61418e-07, 13.1158] | 4.574e-04 |
| **low_aspect_ratio_DEMO · campaign_stencil_backward (n = 38)** |  |  |  |  |  |  |
| 19 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | **0.9355** | 1.0000 | 0 | 4.184e+00 [0, 34.1746] | 4.024e-04 |

<sub>`the ownership rung A0 → A1`</sub>

<sub>combining 6 stage table(s): `ownership rung A0 → A1 — large_tokamak_nof — campaign_displaced`; `ownership rung A0 → A1 — low_aspect_ratio_DEMO — campaign_displaced`; `ownership rung A0 → A1 — large_tokamak_nof — campaign_stencil_forward`; `ownership rung A0 → A1 — low_aspect_ratio_DEMO — campaign_stencil_forward`; `ownership rung A0 → A1 — large_tokamak_nof — campaign_stencil_backward`; `ownership rung A0 → A1 — low_aspect_ratio_DEMO — campaign_stencil_backward`</sub>

**Table F.13.** *Reliability read both ways, configurations stacked — **the whole of it**, of which the main text's per-arm success grid is the first seven columns. Per arm, of the 25 starts offered: accepted optima (status ok and the output file's `ifail == 1`), the other starts by outcome class, and the starts lost that another arm accepted. Beside them, the failure taxonomy over every optimisation-phase run of the configuration — scheduled, crashed, ok, the all-or-none *rows sum* check and the last line of each traceback with its count — and, per configuration and repeated down its arm rows, the **seed set**: the seeds on which *every* arm reached an accepted optimum, which every other optimisation table's n is, with the configuration-invalid seeds and the retried seeds per arm. The three constructions have three different denominators and each sub-heading row states them. Reported, not accepted on (D29, 2026-09-15). n = 9 (row group(s) of this table, each over its own population with its own n in its sub-heading row; never pooled).*

| arm | starts offered | accepted optima | crashed (RuntimeError) | lost, another arm accepted | seed set (every arm accepted) | seeds not accepted, by class | seeds lost that another arm accepted | scheduled | crashed | ok | rows sum | detail (traceback's last line × count) | arms | which | seeds offered | n (every arm converged) | seeds in the set | configuration-invalid seeds | retried seeds per arm | finished, ifail = 5 | coupling-loop cap (ModuleSolveFailure) | unconverged |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **large_tokamak_nof — 3 construction(s): `per-arm success` n = 25; `failure taxonomy` n = 100; `the seed set` n = 25** |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| BR | 25 | 22 | 3 | 0 | 22 | crashed (RuntimeError): 5, 20, 21 | — | 25 | 3 | 22 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×3 | 4 | BR · B0 · B1 · B2 | 25 | 22 | 0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 22, 23, 24 | 3 | BR 0 · B0 0 · B1 0 · B2 0 |  |  |  |
| B0 | 25 | 22 | 3 | 0 | 22 | crashed (RuntimeError): 5, 20, 21 | — | 25 | 3 | 22 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×3 | 4 | BR · B0 · B1 · B2 | 25 | 22 | 0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 22, 23, 24 | 3 | BR 0 · B0 0 · B1 0 · B2 0 |  |  |  |
| B1 | 25 | 22 | 3 | 0 | 22 | crashed (RuntimeError): 5, 20, 21 | — | 25 | 3 | 22 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×3 | 4 | BR · B0 · B1 · B2 | 25 | 22 | 0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 22, 23, 24 | 3 | BR 0 · B0 0 · B1 0 · B2 0 |  |  |  |
| B2 | 25 | 22 | 3 | 0 | 22 | crashed (RuntimeError): 5, 20, 21 | — | 25 | 3 | 22 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×3 | 4 | BR · B0 · B1 · B2 | 25 | 22 | 0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 22, 23, 24 | 3 | BR 0 · B0 0 · B1 0 · B2 0 |  |  |  |
| **low_aspect_ratio_DEMO — 3 construction(s): `per-arm success` n = 25; `failure taxonomy` n = 100; `the seed set` n = 25** |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| BR | 25 | 12 | 2 | 0 | 11 | finished, ifail = 5: 2, 4, 7, 8, 14, 16, 17, 20, 22, 23, 24; crashed (RuntimeError): 3, 21 | — | 25 | 2 | 23 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×2 | 4 | BR · B0 · B1 · B2 | 25 | 11 | 0, 1, 5, 6, 9, 11, 12, 13, 15, 18, 19 | 13 | BR 12 · B0 10 · B1 10 · B2 10 | 11 | 0 | 0 |
| B0 | 25 | 12 | 2 | 0 | 11 | finished, ifail = 5: 2, 7, 8, 14, 16, 17, 20, 23, 24; crashed (RuntimeError): 3, 21; coupling-loop cap (ModuleSolveFailure): 4, 22 | — | 25 | 2 | 21 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×2; process.core.solver.module_solve.ModuleSolveFailure: block FLAT did not converge in 20 sweeps at tau=1e-06; max scaled residual inf on current_drive.eta_cd_dimensionless_hcd_primary, 1 components above tau ×2 | 4 | BR · B0 · B1 · B2 | 25 | 11 | 0, 1, 5, 6, 9, 11, 12, 13, 15, 18, 19 | 13 | BR 12 · B0 10 · B1 10 · B2 10 | 9 | 2 | 2 |
| B1 | 25 | 11 | 2 | 1 | 11 | finished, ifail = 5: 2, 7, 8, 14, 16, 17, 20, 23, 24; crashed (RuntimeError): 3, 21; coupling-loop cap (ModuleSolveFailure): 4, 10, 22 | 10 | 25 | 2 | 20 | yes | process.core.solver.module_solve.ModuleSolveFailure: block FLAT did not converge in 20 sweeps at tau=1e-06; max scaled residual inf on current_drive.eta_cd_dimensionless_hcd_primary, 1 components above tau ×3; RuntimeError: Failed to converge after 50 iterations, value is nan. ×2 | 4 | BR · B0 · B1 · B2 | 25 | 11 | 0, 1, 5, 6, 9, 11, 12, 13, 15, 18, 19 | 13 | BR 12 · B0 10 · B1 10 · B2 10 | 9 | 3 | 3 |
| B2 | 25 | 11 | 2 | 1 | 11 | finished, ifail = 5: 2, 7, 8, 14, 16, 17, 20, 23, 24; crashed (RuntimeError): 3, 21; coupling-loop cap (ModuleSolveFailure): 4, 10, 22 | 10 | 25 | 2 | 20 | yes | process.core.solver.module_solve.ModuleSolveFailure: block M1 did not converge in 20 sweeps at tau=1e-06; max scaled residual inf on current_drive.eta_cd_dimensionless_hcd_primary, 1 components above tau ×3; RuntimeError: Failed to converge after 50 iterations, value is nan. ×2 | 4 | BR · B0 · B1 · B2 | 25 | 11 | 0, 1, 5, 6, 9, 11, 12, 13, 15, 18, 19 | 13 | BR 12 · B0 10 · B1 10 · B2 10 | 9 | 3 | 3 |
| **st_regression — 3 construction(s): `per-arm success` n = 25; `failure taxonomy` n = 75; `the seed set` n = 25** |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| BR | 25 | 24 |  | 0 | 22 | finished, ifail = 5: 17 | — | 25 |  | 25 | yes | — | 3 | BR · B0 · B2 | 25 | 22 | 0, 1, 2, 3, 4, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 18, 19, 20, 21, 22, 23, 24 | 1 | BR 5 · B0 3 · B2 2 | 1 |  |  |
| B0 | 25 | 23 |  | 1 | 22 | finished, ifail = 5: 10, 17 | 10 | 25 |  | 25 | yes | — | 3 | BR · B0 · B2 | 25 | 22 | 0, 1, 2, 3, 4, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 18, 19, 20, 21, 22, 23, 24 | 1 | BR 5 · B0 3 · B2 2 | 2 |  |  |
| B2 | 25 | 23 |  | 1 | 22 | finished, ifail = 5: 5, 17 | 5 | 25 |  | 25 | yes | — | 3 | BR · B0 · B2 | 25 | 22 | 0, 1, 2, 3, 4, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 18, 19, 20, 21, 22, 23, 24 | 1 | BR 5 · B0 3 · B2 2 | 2 |  |  |

<sub>`per-arm success, the seed set and the failure taxonomy`</sub>

<sub>combining 9 stage table(s): `per-arm success — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`; `failure taxonomy — large_tokamak_nof — campaign_optimisation`; `the seed set — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`; `per-arm success — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`; `failure taxonomy — low_aspect_ratio_DEMO — campaign_optimisation`; `the seed set — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`; `per-arm success — st_regression — campaign_optimisation · BR·B0·B2`; `failure taxonomy — st_regression — campaign_optimisation`; `the seed set — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table F.14.** *Check 2 by configuration and arm pair: the iteration ratio summed over the optimiser's attempts (the acceptance construction) as median and as a ratio of sums, the final-attempt construction beside it, the evaluation-count ratio ε from `sweeps_per_eval.n_evaluations` with the seeds on which it is exactly 1, and the dispatch-sweep ratio — a mechanism, not a cost. n = 3 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and its own n, and that n counts seeds on which every arm of that configuration converged).*

| pair | n | summed median (acceptance) | summed sum ratio | verdict | final-attempt median | final-attempt sum ratio | ε median (evaluations) | ε = 1 on | sweeps median | attempts per seed (base/arm) | constructions disagree |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **large_tokamak_nof (n = 22)** |  |  |  |  |  |  |  |  |  |  |  |
| B0 → BR (beside) | 22 | **1.0000** | 1.0000 | **beside** | 1.0000 | 1.0000 | 1.0000 | 22 | 0.9795 | 0:1/1, 1:1/1, 2:1/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 10:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 17:1/1, 18:1/1, 19:1/1, 22:1/1, 23:1/1, 24:1/1 | 0 |
| B0 → B1 | 22 | **1.0000** | 0.9942 | **PASS** | 1.0000 | 0.9942 | 1.0476 | 0 | 1.0139 | 0:1/1, 1:1/1, 2:1/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 10:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 17:1/1, 18:1/1, 19:1/1, 22:1/1, 23:1/1, 24:1/1 | 0 |
| B0 → B2 | 22 | **1.0000** | 0.9942 | **PASS** | 1.0000 | 0.9942 | 1.0476 | 0 | 2.6524 | 0:1/1, 1:1/1, 2:1/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 10:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 17:1/1, 18:1/1, 19:1/1, 22:1/1, 23:1/1, 24:1/1 | 0 |
| B1 → B2 (beside) | 22 | **1.0000** | 1.0000 | **beside** | 1.0000 | 1.0000 | 1.0000 | 22 | 2.6158 | 0:1/1, 1:1/1, 2:1/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 10:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 17:1/1, 18:1/1, 19:1/1, 22:1/1, 23:1/1, 24:1/1 | 0 |
| **low_aspect_ratio_DEMO (n = 11)** |  |  |  |  |  |  |  |  |  |  |  |
| B0 → BR (beside) | 11 | **1.0000** | 1.0000 | **beside** | 1.0000 | 1.0000 | 1.0000 | 11 | 1.0352 | 0:1/1, 1:2/2, 5:1/1, 6:1/1, 9:1/1, 11:1/1, 12:1/1, 13:1/1, 15:1/1, 18:1/1, 19:1/1 | 1 |
| B0 → B1 | 11 | **0.8125** | 0.7012 | **PASS** | 0.8333 | 1.0088 | 0.8468 | 0 | 0.8046 | 0:1/1, 1:2/1, 5:1/1, 6:1/1, 9:1/1, 11:1/1, 12:1/1, 13:1/1, 15:1/1, 18:1/1, 19:1/1 | 1 |
| B0 → B2 | 11 | **0.8125** | 0.7012 | **PASS** | 0.8333 | 1.0088 | 0.8468 | 0 | 2.1169 | 0:1/1, 1:2/1, 5:1/1, 6:1/1, 9:1/1, 11:1/1, 12:1/1, 13:1/1, 15:1/1, 18:1/1, 19:1/1 | 1 |
| B1 → B2 (beside) | 11 | **1.0000** | 1.0000 | **beside** | 1.0000 | 1.0000 | 1.0000 | 11 | 2.6335 | 0:1/1, 1:1/1, 5:1/1, 6:1/1, 9:1/1, 11:1/1, 12:1/1, 13:1/1, 15:1/1, 18:1/1, 19:1/1 | 0 |
| **st_regression (n = 22; arms BR·B0·B2)** |  |  |  |  |  |  |  |  |  |  |  |
| B0 → BR (beside) | 22 | **1.0000** | 1.2405 | **beside** | 1.0000 | 0.9221 | 1.0000 | 15 | 0.9906 | 0:1/1, 1:1/1, 2:2/2, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 11:1/1, 12:1/2, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 18:1/1, 19:1/1, 20:1/1, 21:1/1, 22:1/1, 23:1/1, 24:1/3 | 3 |
| B0 → B2 | 22 | **1.0000** | 0.9530 | **PASS** | 1.0000 | 1.0019 | 1.0000 | 14 | 2.7767 | 0:1/1, 1:1/1, 2:2/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 18:1/1, 19:1/1, 20:1/1, 21:1/1, 22:1/1, 23:1/1, 24:1/1 | 1 |

<sub>`iteration multiplier (check 2)`</sub>

<sub>combining 3 stage table(s): `iteration multiplier (check 2) — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`; `iteration multiplier (check 2) — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`; `iteration multiplier (check 2) — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table F.15.** *What each arm left at its accepted optimum, by configuration, arm and ruler: the restricted maximum scaled residual as median and maximum, its argmax component, and the whole-state median beside it. Matched accuracy is the condition the cost ratios are read under; this table is where it is met or not. n = 3 (row group(s) of this table, each over its own population and never pooled; a group's sub-heading row names its configuration and its own n, and that n counts optimisation-phase runs of that configuration in this arm group).*

| arm | ruler | n (runs) | with a restricted statistic | restricted median / max | restricted argmax | components above τ | whole-state median | components excluded | audit position | audit instrument |
|---|---|---|---|---|---|---|---|---|---|---|
| **large_tokamak_nof (n = 100)** |  |  |  |  |  |  |  |  |  |  |
| BR | frozen | 22 | 22 | 1.150e-11 / 1.332e-11 | heat_transport.tlvpmw | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.150e-11 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
|  | mixed | 22 | 22 | 1.150e-11 / 1.253e-11 | heat_transport.tlvpmw | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.150e-11 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | frozen | 22 | 22 | 1.150e-11 / 1.332e-11 | heat_transport.tlvpmw | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.150e-11 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
|  | mixed | 22 | 22 | 1.150e-11 / 1.253e-11 | heat_transport.tlvpmw | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.150e-11 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B1 | frozen | 22 | 22 | 0 / 7.257e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.c_pf_cs_coil_flat_top_ma | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
|  | mixed | 22 | 22 | 0 / 6.928e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.c_pf_cs_coil_flat_top_ma | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B2 | frozen | 22 | 22 | 0 / 7.257e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.c_pf_cs_coil_flat_top_ma | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.066e+00 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
|  | mixed | 22 | 22 | 0 / 6.928e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.c_pf_cs_coil_flat_top_ma | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.000e+00 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| **low_aspect_ratio_DEMO (n = 100)** |  |  |  |  |  |  |  |  |  |  |
| BR | frozen | 23 | 23 | 0 / inf | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.eta_cd_dimensionless_hcd_primary, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
|  | mixed | 23 | 23 | 0 / inf | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.eta_cd_dimensionless_hcd_primary, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | frozen | 21 | 21 | 0 / 5.315e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
|  | mixed | 21 | 21 | 0 / 3.995e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B1 | frozen | 20 | 20 | 0 / 5.315e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
|  | mixed | 20 | 20 | 0 / 4.365e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B2 | frozen | 20 | 20 | 0 / 5.315e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.007e+00 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
|  | mixed | 20 | 20 | 0 / 3.995e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.000e+00 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| **st_regression (n = 75; arms BR·B0·B2)** |  |  |  |  |  |  |  |  |  |  |
| BR | frozen | 25 | 25 | 4.875e-14 / 5.040e-14 | blanket.deg_blkt_inboard_poloidal_plasma, physics.f_beta_alpha_beam_thermal | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 4.875e-14 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
|  | mixed | 25 | 25 | 4.871e-14 / 5.035e-14 | blanket.deg_blkt_inboard_poloidal_plasma, physics.f_beta_alpha_beam_thermal | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 4.871e-14 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | frozen | 25 | 25 | 4.894e-14 / 4.967e-14 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.big_q_plasma, physics.f_beta_alpha_beam_thermal | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 4.894e-14 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
|  | mixed | 25 | 25 | 4.889e-14 / 4.962e-14 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.big_q_plasma, physics.f_beta_alpha_beam_thermal | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 4.889e-14 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B2 | frozen | 25 | 25 | 7.497e-12 / 3.587e-11 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, heat_transport.tlvpmw, physics.f_beta_alpha_beam_thermal, superconducting_tfcoil.a_tf_plasma_case | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.598e+00 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
|  | mixed | 25 | 25 | 6.643e-12 / 3.585e-11 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, heat_transport.tlvpmw, physics.f_beta_alpha_beam_thermal, superconducting_tfcoil.a_tf_plasma_case | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.000e+00 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |

<sub>`achieved accuracy at the accepted optimum`</sub>

<sub>combining 3 stage table(s): `achieved accuracy at the accepted optimum — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`; `achieved accuracy at the accepted optimum — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`; `achieved accuracy at the accepted optimum — st_regression — campaign_optimisation · BR·B0·B2`</sub>

*The second implementation emitted 141 table(s); none is rendered here. Whether they agree with the tally's, table by table, row by row and cell by cell without tolerance, is gate `recomputation`'s verdict — one row of the report's Table D.1 — and the gate's own record holds every compared cell.*
