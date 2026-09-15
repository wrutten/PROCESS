# Results tables — the full result matrices

> **Document status** — **GENERATED, never hand-edited.** Written whole by `harness/measurement/plan_tables.py` (`experiment_runner.py --plan-tables write`) from the same stage records as the report's Appendix D, and compared whole by `--plan-tables check`. It holds every table with a row per run, seed, pair of runs or predicate evaluation, the full versions of the report's tables whose per-seed columns the report omits, and every table of the second implementation. Tables are numbered `Table F.n` in the order printed; the report cites them by that number and traces a cell by the construction name printed under each table. Populations, constructions and conventions are the report's Appendix D.0's, not repeated here. Arm names are today's (`AR/A0/A1/A2`, `BR/B0/B1/B2`); the records carry the names of their day (trap T16).

*Rendered from the **campaign** population — 949 run records at `57dc0c14`.*

## F.1 The evaluation phase — one row per run

The per-run tables of the evaluation phase: what each finished run's convergence test cost (one row per run; the two predicates in columns of their own, never summed) and the predicate trial (one row per pair of runs under the two rulers). Populations and constructions are as declared in Appendix D.0 of the report.

**Table F.1.** *Convergence-test cost per finished run on large_tokamak_nof, the entry reference: sweeps, and for the test the arm stops on its evaluations, components compared and mean width; the two predicates are never summed. The empty-visit sweep share over this population is 0 %. n = 1 (finished evaluation-phase campaign runs of large_tokamak_nof).*

| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 0 | coupling_state | 6 | 6 | 5040 | 840.0 | FLAT 840 | 0 | 0 | — | 0.00 % |

<sub>`per-sweep overhead — large_tokamak_nof — campaign_entry_references`</sub>

**Table F.2.** *Convergence-test cost per finished run on low_aspect_ratio_DEMO, the entry reference: sweeps, and for the test the arm stops on its evaluations, components compared and mean width; the two predicates are never summed. The empty-visit sweep share over this population is 0 %. n = 1 (finished evaluation-phase campaign runs of low_aspect_ratio_DEMO).*

| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846.0 | FLAT 846 | 0 | 0 | — | 0.00 % |

<sub>`per-sweep overhead — low_aspect_ratio_DEMO — campaign_entry_references`</sub>

**Table F.3.** *Convergence-test cost per finished run on st_regression, the entry reference: sweeps, and for the test the arm stops on its evaluations, components compared and mean width; the two predicates are never summed. The empty-visit sweep share over this population is 0 %. n = 1 (finished evaluation-phase campaign runs of st_regression).*

| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 0 | coupling_state | 7 | 7 | 5789 | 827.0 | FLAT 827 | 0 | 0 | — | 0.00 % |

<sub>`per-sweep overhead — st_regression — campaign_entry_references`</sub>

**Table F.4.** *Convergence-test cost per finished run on large_tokamak_nof, the displaced entries (δ = 0.10): sweeps, and for the test the arm stops on its evaluations, components compared and mean width; the two predicates are never summed. The empty-visit sweep share over this population is 0 %. n = 100 (finished evaluation-phase campaign runs of large_tokamak_nof).*

| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
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

<sub>`per-sweep overhead — large_tokamak_nof — campaign_displaced`</sub>

**Table F.5.** *Convergence-test cost per finished run on low_aspect_ratio_DEMO, the displaced entries (δ = 0.10): sweeps, and for the test the arm stops on its evaluations, components compared and mean width; the two predicates are never summed. The empty-visit sweep share over this population is 0 %. n = 100 (finished evaluation-phase campaign runs of low_aspect_ratio_DEMO).*

| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
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

<sub>`per-sweep overhead — low_aspect_ratio_DEMO — campaign_displaced`</sub>

**Table F.6.** *Convergence-test cost per finished run on st_regression, the displaced entries (δ = 0.10): sweeps, and for the test the arm stops on its evaluations, components compared and mean width; the two predicates are never summed. The empty-visit sweep share over this population is 0 %, 6.67 %, 7.14 %. n = 75 (finished evaluation-phase campaign runs of st_regression).*

| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
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

<sub>`per-sweep overhead — st_regression — campaign_displaced`</sub>

**Table F.7.** *Convergence-test cost per finished run on large_tokamak_nof, the forward stencil points: sweeps, and for the test the arm stops on its evaluations, components compared and mean width; the two predicates are never summed. The empty-visit sweep share over this population is 0 %. n = 80 (finished evaluation-phase campaign runs of large_tokamak_nof).*

| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
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

<sub>`per-sweep overhead — large_tokamak_nof — campaign_stencil_forward`</sub>

**Table F.8.** *Convergence-test cost per finished run on low_aspect_ratio_DEMO, the forward stencil points: sweeps, and for the test the arm stops on its evaluations, components compared and mean width; the two predicates are never summed. The empty-visit sweep share over this population is 0 %. n = 76 (finished evaluation-phase campaign runs of low_aspect_ratio_DEMO).*

| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
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

<sub>`per-sweep overhead — low_aspect_ratio_DEMO — campaign_stencil_forward`</sub>

**Table F.9.** *Convergence-test cost per finished run on st_regression, the forward stencil points: sweeps, and for the test the arm stops on its evaluations, components compared and mean width; the two predicates are never summed. The empty-visit sweep share over this population is 0 %, 10 %, 11.11 %, 12.5 %, 16.67 %. n = 42 (finished evaluation-phase campaign runs of st_regression).*

| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
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

<sub>`per-sweep overhead — st_regression — campaign_stencil_forward`</sub>

**Table F.10.** *Convergence-test cost per finished run on large_tokamak_nof, the backward stencil points: sweeps, and for the test the arm stops on its evaluations, components compared and mean width; the two predicates are never summed. The empty-visit sweep share over this population is 0 %. n = 80 (finished evaluation-phase campaign runs of large_tokamak_nof).*

| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
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

<sub>`per-sweep overhead — large_tokamak_nof — campaign_stencil_backward`</sub>

**Table F.11.** *Convergence-test cost per finished run on low_aspect_ratio_DEMO, the backward stencil points: sweeps, and for the test the arm stops on its evaluations, components compared and mean width; the two predicates are never summed. The empty-visit sweep share over this population is 0 %. n = 76 (finished evaluation-phase campaign runs of low_aspect_ratio_DEMO).*

| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
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

<sub>`per-sweep overhead — low_aspect_ratio_DEMO — campaign_stencil_backward`</sub>

**Table F.12.** *Convergence-test cost per finished run on st_regression, the backward stencil points: sweeps, and for the test the arm stops on its evaluations, components compared and mean width; the two predicates are never summed. The empty-visit sweep share over this population is 0 %, 9.09 %, 10 %, 11.11 %, 12.5 %, 16.67 %. n = 42 (finished evaluation-phase campaign runs of st_regression).*

| arm | seed | stops on | dispatch sweeps | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|
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

<sub>`per-sweep overhead — st_regression — campaign_stencil_backward`</sub>

**Table F.13.** *The predicate trial, frozen against mixed: per pair of runs, the decisive passes as crossings and as verdict changes, bit-identity, and the exit audit on both rulers. The decisive components carry |y|/s up to 54.59. From gate predicate_mode's verdict. n = 12 (pairs of runs, one per ruler).*

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

<sub>`the predicate trial — frozen against mixed`</sub>

## F.2 The optimisation phase — one row per seed or per run

The per-seed and per-run tables of the optimisation phase: per-arm success by seed (every start offered, each arm's outcome class there), the failure table (every seed outside the seed set, with what failed there and what the other arms cost at the same start), the attempt-summation identity (every run's per-attempt costs against its solve-phase total) and the per-run overhead.

**Table F.14.** *Per-arm success on large_tokamak_nof by seed: each arm's outcome class at every start offered, the count of arms that accepted, membership of the seed set, and the arms that lost the start while another accepted. n = 25 (distinct seeds run on large_tokamak_nof).*

| seed | BR | B0 | B1 | B2 | arms accepted | in the seed set | lost by (another arm accepted) |
|---|---|---|---|---|---|---|---|
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

<sub>`per-arm success by seed — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.15.** *Seeds of large_tokamak_nof outside the seed set: which arm failed there and how (ifail, attempts), its cost and the other arms' at the same start; a seed every arm failed on is configuration-invalid. n = 25 (distinct seeds run on large_tokamak_nof).*

| seed | failed arm(s) | not run | ifail | attempts | failed arm node calls | other arms' node calls | configuration-invalid |
|---|---|---|---|---|---|---|---|
| 5 | BR, B0, B1, B2 | — | None, None, None, None | 1, 1, 1, 1 | None, None, None, None | BR — / B0 — / B1 — / B2 — | yes |
| 20 | BR, B0, B1, B2 | — | None, None, None, None | 1, 1, 1, 1 | None, None, None, None | BR — / B0 — / B1 — / B2 — | yes |
| 21 | BR, B0, B1, B2 | — | None, None, None, None | 1, 1, 1, 1 | None, None, None, None | BR — / B0 — / B1 — / B2 — | yes |

<sub>`the failure table — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.16.** *The attempt-summation identity per run on large_tokamak_nof: each attempt's node calls and sweeps against the solve-phase totals and the residual, which the record contract requires to be 0 before a run reaches any other table. n = 100 (optimisation-phase campaign runs of large_tokamak_nof).*

| arm | seed | attempts | retried | node calls per attempt | = solve-phase total | residual | sweeps per attempt | = solve-phase total | residual | decomposes |
|---|---|---|---|---|---|---|---|---|---|---|
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

<sub>`the attempt summation identity — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.17.** *Convergence-test cost per finished optimisation on large_tokamak_nof: dispatch sweeps (solve phase and output-time loop apart), and for the test the arm stops on its evaluations, components compared and mean width; the two predicates are never summed. Empty-visit sweep share: 0 %. n = 88 (finished optimisation-phase campaign runs of large_tokamak_nof).*

| arm | seed | stops on | dispatch sweeps | of which solve phase | output-time loop | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
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

<sub>`per-sweep overhead — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.18.** *Per-arm success on low_aspect_ratio_DEMO by seed: each arm's outcome class at every start offered, the count of arms that accepted, membership of the seed set, and the arms that lost the start while another accepted. n = 25 (distinct seeds run on low_aspect_ratio_DEMO).*

| seed | BR | B0 | B1 | B2 | arms accepted | in the seed set | lost by (another arm accepted) |
|---|---|---|---|---|---|---|---|
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

<sub>`per-arm success by seed — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.19.** *Seeds of low_aspect_ratio_DEMO outside the seed set: which arm failed there and how (ifail, attempts), its cost and the other arms' at the same start; a seed every arm failed on is configuration-invalid. n = 25 (distinct seeds run on low_aspect_ratio_DEMO).*

| seed | failed arm(s) | not run | ifail | attempts | failed arm node calls | other arms' node calls | configuration-invalid |
|---|---|---|---|---|---|---|---|
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

<sub>`the failure table — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.20.** *The attempt-summation identity per run on low_aspect_ratio_DEMO: each attempt's node calls and sweeps against the solve-phase totals and the residual, which the record contract requires to be 0 before a run reaches any other table. n = 100 (optimisation-phase campaign runs of low_aspect_ratio_DEMO).*

| arm | seed | attempts | retried | node calls per attempt | = solve-phase total | residual | sweeps per attempt | = solve-phase total | residual | decomposes |
|---|---|---|---|---|---|---|---|---|---|---|
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

<sub>`the attempt summation identity — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.21.** *Convergence-test cost per finished optimisation on low_aspect_ratio_DEMO: dispatch sweeps (solve phase and output-time loop apart), and for the test the arm stops on its evaluations, components compared and mean width; the two predicates are never summed. Empty-visit sweep share: 0 %. n = 84 (finished optimisation-phase campaign runs of low_aspect_ratio_DEMO).*

| arm | seed | stops on | dispatch sweeps | of which solve phase | output-time loop | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
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

<sub>`per-sweep overhead — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.22.** *Per-arm success on st_regression by seed: each arm's outcome class at every start offered, the count of arms that accepted, membership of the seed set, and the arms that lost the start while another accepted. n = 25 (distinct seeds run on st_regression).*

| seed | BR | B0 | B2 | arms accepted | in the seed set | lost by (another arm accepted) |
|---|---|---|---|---|---|---|
| 0 | accepted | accepted | accepted | 3 | yes | — |
| 1 | accepted | accepted | accepted | 3 | yes | — |
| 2 | accepted | accepted | accepted | 3 | yes | — |
| 3 | accepted | accepted | accepted | 3 | yes | — |
| 4 | accepted | accepted | accepted | 3 | yes | — |
| 5 | accepted | accepted | finished, ifail = 5 | 2 | no | B2 |
| 6 | accepted | accepted | accepted | 3 | yes | — |
| 7 | accepted | accepted | accepted | 3 | yes | — |
| 8 | accepted | accepted | accepted | 3 | yes | — |
| 9 | accepted | accepted | accepted | 3 | yes | — |
| 10 | accepted | finished, ifail = 5 | accepted | 2 | no | B0 |
| 11 | accepted | accepted | accepted | 3 | yes | — |
| 12 | accepted | accepted | accepted | 3 | yes | — |
| 13 | accepted | accepted | accepted | 3 | yes | — |
| 14 | accepted | accepted | accepted | 3 | yes | — |
| 15 | accepted | accepted | accepted | 3 | yes | — |
| 16 | accepted | accepted | accepted | 3 | yes | — |
| 17 | finished, ifail = 5 | finished, ifail = 5 | finished, ifail = 5 | 0 | no | — |
| 18 | accepted | accepted | accepted | 3 | yes | — |
| 19 | accepted | accepted | accepted | 3 | yes | — |
| 20 | accepted | accepted | accepted | 3 | yes | — |
| 21 | accepted | accepted | accepted | 3 | yes | — |
| 22 | accepted | accepted | accepted | 3 | yes | — |
| 23 | accepted | accepted | accepted | 3 | yes | — |
| 24 | accepted | accepted | accepted | 3 | yes | — |

<sub>`per-arm success by seed — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table F.23.** *Seeds of st_regression outside the seed set: which arm failed there and how (ifail, attempts), its cost and the other arms' at the same start; a seed every arm failed on is configuration-invalid. n = 25 (distinct seeds run on st_regression).*

| seed | failed arm(s) | not run | ifail | attempts | failed arm node calls | other arms' node calls | configuration-invalid |
|---|---|---|---|---|---|---|---|
| 5 | B2 | — | 5.0 | 3 | 479630 | BR 160335 / B0 175413 / B2 — | no |
| 10 | B0 | — | 5.0 | 3 | 667989 | BR 717990 / B0 — / B2 129012 | no |
| 17 | BR, B0, B2 | — | 5.0, 5.0, 5.0 | 4, 4, 4 | 8064, 8820, 4921 | BR — / B0 — / B2 — | yes |

<sub>`the failure table — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table F.24.** *The attempt-summation identity per run on st_regression: each attempt's node calls and sweeps against the solve-phase totals and the residual, which the record contract requires to be 0 before a run reaches any other table. n = 75 (optimisation-phase campaign runs of st_regression).*

| arm | seed | attempts | retried | node calls per attempt | = solve-phase total | residual | sweeps per attempt | = solve-phase total | residual | decomposes |
|---|---|---|---|---|---|---|---|---|---|---|
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

<sub>`the attempt summation identity — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table F.25.** *Convergence-test cost per finished optimisation on st_regression: dispatch sweeps (solve phase and output-time loop apart), and for the test the arm stops on its evaluations, components compared and mean width; the two predicates are never summed. Empty-visit sweep share: 0 %, 10.7 %, 10.8 %, 10.82 %, 10.83 %, 10.84 %, 10.85 %, 10.86 %, 10.87 %, 10.9 %, 10.91 %, 10.92 %, 10.94 %, 11.15 %, 11.18 %, 11.22 %, 11.3 %, 11.57 %. n = 75 (finished optimisation-phase campaign runs of st_regression).*

| arm | seed | stops on | dispatch sweeps | of which solve phase | output-time loop | coupling-state tests | components compared | mean width | width by block | objective/constraint tests | values compared | mean width | empty-visit sweep share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
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

<sub>`per-sweep overhead — st_regression — campaign_optimisation · BR·B0·B2`</sub>

## F.3 Appendix D's tables with their per-seed columns

The full versions of the report's tables whose columns listing a value per seed inside one cell (the paired seeds, the seeds of the set, the attempts per seed, the components above τ per run) the report omits. Every other cell is identical to the report's.

**Table F.26.** *Node calls per evaluation by arm on large_tokamak_nof, the entry reference, with the ratio against A0 pooled, as the per-run median and as runs on which the arm cost more. **Fallback**: no A1 run here, so the ratio is against A0, not the declared pair. Prime calls stand beside the node calls, not in them. n = 1 (evaluation-phase campaign runs of large_tokamak_nof).*

| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A0 at seeds | vs A0 pooled | vs A0 median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 1/1 | 126.0 | [126, 126] | 6.00 | FLAT 6 | 0.0 | — | — | — | — |

<sub>`cost per call — large_tokamak_nof — campaign_entry_references`</sub>

**Table F.27.** *Node calls per evaluation by arm on low_aspect_ratio_DEMO, the entry reference, with the ratio against A0 pooled, as the per-run median and as runs on which the arm cost more. **Fallback**: no A1 run here, so the ratio is against A0, not the declared pair. Prime calls stand beside the node calls, not in them. n = 1 (evaluation-phase campaign runs of low_aspect_ratio_DEMO).*

| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A0 at seeds | vs A0 pooled | vs A0 median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 1/1 | 105.0 | [105, 105] | 5.00 | FLAT 5 | 0.0 | — | — | — | — |

<sub>`cost per call — low_aspect_ratio_DEMO — campaign_entry_references`</sub>

**Table F.28.** *Node calls per evaluation by arm on st_regression, the entry reference, with the ratio against A0 pooled, as the per-run median and as runs on which the arm cost more. A0 is the reference (steady state: no burn-time coupling). Prime calls stand beside the node calls, not in them. n = 1 (evaluation-phase campaign runs of st_regression).*

| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A0 at seeds | vs A0 pooled | vs A0 median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 1/1 | 147.0 | [147, 147] | 7.00 | FLAT 7 | 0.0 | — | — | — | — |

<sub>`cost per call — st_regression — campaign_entry_references`</sub>

**Table F.29.** *Node calls per evaluation by arm on large_tokamak_nof, the displaced entries (δ = 0.10), with the ratio against A1 pooled, as the per-run median and as runs on which the arm cost more. A1 is the declared reference (the same reduced map as A2). Prime calls stand beside the node calls, not in them. n = 100 (evaluation-phase campaign runs of large_tokamak_nof).*

| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A1 at seeds | vs A1 pooled | vs A1 median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 25/25 | 104.2 | [84, 105] | 4.96 | — | 0.0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.9688 | 1.0000 | 0 |
| A0 | 25/25 | 115.9 | [105, 126] | 5.52 | FLAT 138 | 0.0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 1.0781 | 1.0000 | 10 |
| A1 | 25/25 | 107.5 | [84, 126] | 5.12 | FLAT 128 | 0.0 | — | — | — | — |
| A2 | 25/25 | 60.5 | [60, 63] | 13.16 | FF 0, M1 100, M2 129, M3 75, PULSE 0 | 13.2 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.5625 | 0.5714 | 0 |

<sub>`cost per call — large_tokamak_nof — campaign_displaced`</sub>

**Table F.30.** *Node calls per evaluation by arm on low_aspect_ratio_DEMO, the displaced entries (δ = 0.10), with the ratio against A1 pooled, as the per-run median and as runs on which the arm cost more. A1 is the declared reference (the same reduced map as A2). Prime calls stand beside the node calls, not in them. n = 100 (evaluation-phase campaign runs of low_aspect_ratio_DEMO).*

| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A1 at seeds | vs A1 pooled | vs A1 median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 25/25 | 105.0 | [105, 105] | 5.00 | — | 0.0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 1.0163 | 1.0000 | 2 |
| A0 | 25/25 | 105.0 | [105, 105] | 5.00 | FLAT 125 | 0.0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 1.0163 | 1.0000 | 2 |
| A1 | 25/25 | 103.3 | [84, 105] | 4.92 | FLAT 123 | 0.0 | — | — | — | — |
| A2 | 25/25 | 59.6 | [57, 60] | 12.88 | FF 0, M1 100, M2 122, M3 75, PULSE 0 | 12.9 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.5772 | 0.5714 | 0 |

<sub>`cost per call — low_aspect_ratio_DEMO — campaign_displaced`</sub>

**Table F.31.** *Node calls per evaluation by arm on st_regression, the displaced entries (δ = 0.10), with the ratio against A0 pooled, as the per-run median and as runs on which the arm cost more. A0 is the reference (steady state: no burn-time coupling). Prime calls stand beside the node calls, not in them. n = 75 (evaluation-phase campaign runs of st_regression).*

| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A0 at seeds | vs A0 pooled | vs A0 median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 25/25 | 103.3 | [84, 105] | 4.92 | — | 0.0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.8425 | 0.8333 | 0 |
| A0 | 25/25 | 122.6 | [105, 126] | 5.84 | FLAT 146 | 0.0 | — | — | — | — |
| A2 | 25/25 | 61.5 | [59, 62] | 14.84 | FF 0, M1 100, M2 146, M3 75, PULSE 25 | 14.8 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.5016 | 0.4921 | 0 |

<sub>`cost per call — st_regression — campaign_displaced`</sub>

**Table F.32.** *Node calls per evaluation by arm on large_tokamak_nof, the forward stencil points, with the ratio against A1 pooled, as the per-run median and as runs on which the arm cost more. A1 is the declared reference (the same reduced map as A2). Prime calls stand beside the node calls, not in them. n = 80 (evaluation-phase campaign runs of large_tokamak_nof).*

| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A1 at columns | vs A1 pooled | vs A1 median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 20/20 | 62.0 | [42, 84] | 2.95 | — | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 0.9833 | 1.0000 | 0 |
| A0 | 20/20 | 66.2 | [42, 105] | 3.15 | FLAT 63 | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 1.0500 | 1.0000 | 3 |
| A1 | 20/20 | 63.0 | [42, 105] | 3.00 | FLAT 60 | 0.0 | — | — | — | — |
| A2 | 20/20 | 39.1 | [20, 55] | 7.60 | FF 0, M1 38, M2 49, M3 45, PULSE 0 | 7.6 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 0.6214 | 0.6071 | 0 |

<sub>`cost per call — large_tokamak_nof — campaign_stencil_forward`</sub>

**Table F.33.** *Node calls per evaluation by arm on low_aspect_ratio_DEMO, the forward stencil points, with the ratio against A1 pooled, as the per-run median and as runs on which the arm cost more. A1 is the declared reference (the same reduced map as A2). Prime calls stand beside the node calls, not in them. n = 76 (evaluation-phase campaign runs of low_aspect_ratio_DEMO).*

| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A1 at columns | vs A1 pooled | vs A1 median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 19/19 | 67.4 | [42, 105] | 3.21 | — | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 1.0702 | 1.0000 | 4 |
| A0 | 19/19 | 66.3 | [42, 105] | 3.16 | FLAT 60 | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 1.0526 | 1.0000 | 3 |
| A1 | 19/19 | 63.0 | [42, 84] | 3.00 | FLAT 57 | 0.0 | — | — | — | — |
| A2 | 19/19 | 40.3 | [33, 55] | 7.63 | FF 0, M1 36, M2 45, M3 45, PULSE 0 | 7.6 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 0.6399 | 0.6071 | 0 |

<sub>`cost per call — low_aspect_ratio_DEMO — campaign_stencil_forward`</sub>

**Table F.34.** *Node calls per evaluation by arm on st_regression, the forward stencil points, with the ratio against A0 pooled, as the per-run median and as runs on which the arm cost more. A0 is the reference (steady state: no burn-time coupling). Prime calls stand beside the node calls, not in them. n = 42 (evaluation-phase campaign runs of st_regression).*

| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A0 at columns | vs A0 pooled | vs A0 median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 14/14 | 63.0 | [42, 84] | 3.00 | — | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | 0.9333 | 1.0000 | 0 |
| A0 | 14/14 | 67.5 | [42, 84] | 3.21 | FLAT 45 | 0.0 | — | — | — | — |
| A2 | 14/14 | 38.9 | [19, 50] | 8.64 | FF 0, M1 31, M2 29, M3 33, PULSE 14 | 8.6 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | 0.5767 | 0.5714 | 0 |

<sub>`cost per call — st_regression — campaign_stencil_forward`</sub>

**Table F.35.** *Node calls per evaluation by arm on large_tokamak_nof, the backward stencil points, with the ratio against A1 pooled, as the per-run median and as runs on which the arm cost more. A1 is the declared reference (the same reduced map as A2). Prime calls stand beside the node calls, not in them. n = 80 (evaluation-phase campaign runs of large_tokamak_nof).*

| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A1 at columns | vs A1 pooled | vs A1 median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 20/20 | 60.9 | [42, 84] | 2.90 | — | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 0.9667 | 1.0000 | 0 |
| A0 | 20/20 | 66.2 | [42, 105] | 3.15 | FLAT 63 | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 1.0500 | 1.0000 | 3 |
| A1 | 20/20 | 63.0 | [42, 105] | 3.00 | FLAT 60 | 0.0 | — | — | — | — |
| A2 | 20/20 | 40.4 | [20, 55] | 7.70 | FF 0, M1 38, M2 49, M3 47, PULSE 0 | 7.7 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 0.6405 | 0.6071 | 0 |

<sub>`cost per call — large_tokamak_nof — campaign_stencil_backward`</sub>

**Table F.36.** *Node calls per evaluation by arm on low_aspect_ratio_DEMO, the backward stencil points, with the ratio against A1 pooled, as the per-run median and as runs on which the arm cost more. A1 is the declared reference (the same reduced map as A2). Prime calls stand beside the node calls, not in them. n = 76 (evaluation-phase campaign runs of low_aspect_ratio_DEMO).*

| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A1 at columns | vs A1 pooled | vs A1 median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 19/19 | 67.4 | [42, 105] | 3.21 | — | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 1.0517 | 1.0000 | 4 |
| A0 | 19/19 | 68.5 | [42, 105] | 3.26 | FLAT 62 | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 1.0690 | 1.0000 | 4 |
| A1 | 19/19 | 64.1 | [42, 84] | 3.05 | FLAT 58 | 0.0 | — | — | — | — |
| A2 | 19/19 | 42.4 | [33, 55] | 7.84 | FF 0, M1 36, M2 46, M3 48, PULSE 0 | 7.8 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 0.6609 | 0.7143 | 0 |

<sub>`cost per call — low_aspect_ratio_DEMO — campaign_stencil_backward`</sub>

**Table F.37.** *Node calls per evaluation by arm on st_regression, the backward stencil points, with the ratio against A0 pooled, as the per-run median and as runs on which the arm cost more. A0 is the reference (steady state: no burn-time coupling). Prime calls stand beside the node calls, not in them. n = 42 (evaluation-phase campaign runs of st_regression).*

| arm | ok/run | node calls / eval | bracket | sweeps / eval | sweeps by block | arrangement·method calls | paired with A0 at columns | vs A0 pooled | vs A0 median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 14/14 | 66.0 | [42, 84] | 3.14 | — | 0.0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | 0.9362 | 1.0000 | 0 |
| A0 | 14/14 | 70.5 | [42, 105] | 3.36 | FLAT 47 | 0.0 | — | — | — | — |
| A2 | 14/14 | 39.4 | [19, 53] | 8.79 | FF 0, M1 31, M2 31, M3 33, PULSE 14 | 8.8 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | 0.5583 | 0.5238 | 0 |

<sub>`cost per call — st_regression — campaign_stencil_backward`</sub>

**Table F.38.** *The rung A0 → A1 on large_tokamak_nof, the displaced entries (δ = 0.10): the per-call cost of pinning the burn time (A1/A0) and the residual the constant leaves at exit, in seconds and relative to the burn time. Not a claim about the partition. n = 50 (A0 and A1 campaign runs of large_tokamak_nof).*

| n | paired at seeds | A1/A0 pooled | median | worse | burn-time residual, s (median) | bracket, s | relative (median) |
|---|---|---|---|---|---|---|---|
| 25 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.9275 | 1.0000 | 0 | 1.546e+02 | [12.8111, 406.884] | 6.298e-02 |

<sub>`ownership rung A0 → A1 — large_tokamak_nof — campaign_displaced`</sub>

**Table F.39.** *The rung A0 → A1 on low_aspect_ratio_DEMO, the displaced entries (δ = 0.10): the per-call cost of pinning the burn time (A1/A0) and the residual the constant leaves at exit, in seconds and relative to the burn time. Not a claim about the partition. n = 50 (A0 and A1 campaign runs of low_aspect_ratio_DEMO).*

| n | paired at seeds | A1/A0 pooled | median | worse | burn-time residual, s (median) | bracket, s | relative (median) |
|---|---|---|---|---|---|---|---|
| 25 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.9840 | 1.0000 | 0 | 5.258e+02 | [1.64882, 1436.26] | 5.275e-02 |

<sub>`ownership rung A0 → A1 — low_aspect_ratio_DEMO — campaign_displaced`</sub>

**Table F.40.** *The rung A0 → A1 on large_tokamak_nof, the forward stencil points: the per-call cost of pinning the burn time (A1/A0) and the residual the constant leaves at exit, in seconds and relative to the burn time. Not a claim about the partition. n = 40 (A0 and A1 campaign runs of large_tokamak_nof).*

| n | paired at columns | A1/A0 pooled | median | worse | burn-time residual, s (median) | bracket, s | relative (median) |
|---|---|---|---|---|---|---|---|
| 20 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 0.9524 | 1.0000 | 0 | 1.173e+00 | [2.61319e-07, 13.1365] | 4.566e-04 |

<sub>`ownership rung A0 → A1 — large_tokamak_nof — campaign_stencil_forward`</sub>

**Table F.41.** *The rung A0 → A1 on low_aspect_ratio_DEMO, the forward stencil points: the per-call cost of pinning the burn time (A1/A0) and the residual the constant leaves at exit, in seconds and relative to the burn time. Not a claim about the partition. n = 38 (A0 and A1 campaign runs of low_aspect_ratio_DEMO).*

| n | paired at columns | A1/A0 pooled | median | worse | burn-time residual, s (median) | bracket, s | relative (median) |
|---|---|---|---|---|---|---|---|
| 19 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 0.9500 | 1.0000 | 0 | 4.176e+00 | [0, 34.2015] | 4.016e-04 |

<sub>`ownership rung A0 → A1 — low_aspect_ratio_DEMO — campaign_stencil_forward`</sub>

**Table F.42.** *The rung A0 → A1 on large_tokamak_nof, the backward stencil points: the per-call cost of pinning the burn time (A1/A0) and the residual the constant leaves at exit, in seconds and relative to the burn time. Not a claim about the partition. n = 40 (A0 and A1 campaign runs of large_tokamak_nof).*

| n | paired at columns | A1/A0 pooled | median | worse | burn-time residual, s (median) | bracket, s | relative (median) |
|---|---|---|---|---|---|---|---|
| 20 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 0.9524 | 1.0000 | 0 | 1.175e+00 | [2.61418e-07, 13.1158] | 4.574e-04 |

<sub>`ownership rung A0 → A1 — large_tokamak_nof — campaign_stencil_backward`</sub>

**Table F.43.** *The rung A0 → A1 on low_aspect_ratio_DEMO, the backward stencil points: the per-call cost of pinning the burn time (A1/A0) and the residual the constant leaves at exit, in seconds and relative to the burn time. Not a claim about the partition. n = 38 (A0 and A1 campaign runs of low_aspect_ratio_DEMO).*

| n | paired at columns | A1/A0 pooled | median | worse | burn-time residual, s (median) | bracket, s | relative (median) |
|---|---|---|---|---|---|---|---|
| 19 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 0.9355 | 1.0000 | 0 | 4.184e+00 | [0, 34.1746] | 4.024e-04 |

<sub>`ownership rung A0 → A1 — low_aspect_ratio_DEMO — campaign_stencil_backward`</sub>

**Table F.44.** *The seed set of large_tokamak_nof: seeds offered, seeds on which every arm (BR · B0 · B1 · B2) reached an accepted optimum (n, the denominator of every check on this configuration), configuration-invalid seeds and retried seeds per arm. n = 25 (distinct seeds run on large_tokamak_nof).*

| arms | which | seeds offered | n (every arm converged) | seeds in the set | configuration-invalid seeds | retried seeds per arm |
|---|---|---|---|---|---|---|
| 4 | BR · B0 · B1 · B2 | 25 | 22 | 0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 22, 23, 24 | 3 | BR 0 · B0 0 · B1 0 · B2 0 |

<sub>`the seed set — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.45.** *The seed set of low_aspect_ratio_DEMO: seeds offered, seeds on which every arm (BR · B0 · B1 · B2) reached an accepted optimum (n, the denominator of every check on this configuration), configuration-invalid seeds and retried seeds per arm. n = 25 (distinct seeds run on low_aspect_ratio_DEMO).*

| arms | which | seeds offered | n (every arm converged) | seeds in the set | configuration-invalid seeds | retried seeds per arm |
|---|---|---|---|---|---|---|
| 4 | BR · B0 · B1 · B2 | 25 | 11 | 0, 1, 5, 6, 9, 11, 12, 13, 15, 18, 19 | 13 | BR 12 · B0 10 · B1 10 · B2 10 |

<sub>`the seed set — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.46.** *The seed set of st_regression: seeds offered, seeds on which every arm (BR · B0 · B2) reached an accepted optimum (n, the denominator of every check on this configuration), configuration-invalid seeds and retried seeds per arm. n = 25 (distinct seeds run on st_regression).*

| arms | which | seeds offered | n (every arm converged) | seeds in the set | configuration-invalid seeds | retried seeds per arm |
|---|---|---|---|---|---|---|
| 3 | BR · B0 · B2 | 25 | 22 | 0, 1, 2, 3, 4, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 18, 19, 20, 21, 22, 23, 24 | 1 | BR 5 · B0 3 · B2 2 |

<sub>`the seed set — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table F.47.** *Per-arm success on large_tokamak_nof: of the 25 starts offered to each arm (BR · B0 · B1 · B2), the accepted optima (status ok and ifail == 1), the other starts by outcome class (finished with the optimiser's exit code; crashed in PROCESS's own code; refused at the coupling-state loop's sweep cap), the starts lost that another arm accepted, and the seed set beside. Reported, not accepted on: no pre-declared rule reads it (D29, 2026-09-15). n = 25 (starts offered per arm on large_tokamak_nof).*

| arm | starts offered | accepted optima | crashed (RuntimeError) | lost, another arm accepted | seed set (every arm accepted) | seeds not accepted, by class | seeds lost that another arm accepted |
|---|---|---|---|---|---|---|---|
| BR | 25 | 22 | 3 | 0 | 22 | crashed (RuntimeError): 5, 20, 21 | — |
| B0 | 25 | 22 | 3 | 0 | 22 | crashed (RuntimeError): 5, 20, 21 | — |
| B1 | 25 | 22 | 3 | 0 | 22 | crashed (RuntimeError): 5, 20, 21 | — |
| B2 | 25 | 22 | 3 | 0 | 22 | crashed (RuntimeError): 5, 20, 21 | — |

<sub>`per-arm success — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.48.** *Per-arm success on low_aspect_ratio_DEMO: of the 25 starts offered to each arm (BR · B0 · B1 · B2), the accepted optima (status ok and ifail == 1), the other starts by outcome class (finished with the optimiser's exit code; crashed in PROCESS's own code; refused at the coupling-state loop's sweep cap), the starts lost that another arm accepted, and the seed set beside. Reported, not accepted on: no pre-declared rule reads it (D29, 2026-09-15). n = 25 (starts offered per arm on low_aspect_ratio_DEMO).*

| arm | starts offered | accepted optima | finished, ifail = 5 | crashed (RuntimeError) | coupling-loop cap (ModuleSolveFailure) | lost, another arm accepted | seed set (every arm accepted) | seeds not accepted, by class | seeds lost that another arm accepted |
|---|---|---|---|---|---|---|---|---|---|
| BR | 25 | 12 | 11 | 2 | 0 | 0 | 11 | finished, ifail = 5: 2, 4, 7, 8, 14, 16, 17, 20, 22, 23, 24; crashed (RuntimeError): 3, 21 | — |
| B0 | 25 | 12 | 9 | 2 | 2 | 0 | 11 | finished, ifail = 5: 2, 7, 8, 14, 16, 17, 20, 23, 24; crashed (RuntimeError): 3, 21; coupling-loop cap (ModuleSolveFailure): 4, 22 | — |
| B1 | 25 | 11 | 9 | 2 | 3 | 1 | 11 | finished, ifail = 5: 2, 7, 8, 14, 16, 17, 20, 23, 24; crashed (RuntimeError): 3, 21; coupling-loop cap (ModuleSolveFailure): 4, 10, 22 | 10 |
| B2 | 25 | 11 | 9 | 2 | 3 | 1 | 11 | finished, ifail = 5: 2, 7, 8, 14, 16, 17, 20, 23, 24; crashed (RuntimeError): 3, 21; coupling-loop cap (ModuleSolveFailure): 4, 10, 22 | 10 |

<sub>`per-arm success — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.49.** *Per-arm success on st_regression: of the 25 starts offered to each arm (BR · B0 · B2), the accepted optima (status ok and ifail == 1), the other starts by outcome class (finished with the optimiser's exit code; crashed in PROCESS's own code; refused at the coupling-state loop's sweep cap), the starts lost that another arm accepted, and the seed set beside. Reported, not accepted on: no pre-declared rule reads it (D29, 2026-09-15). n = 25 (starts offered per arm on st_regression).*

| arm | starts offered | accepted optima | finished, ifail = 5 | lost, another arm accepted | seed set (every arm accepted) | seeds not accepted, by class | seeds lost that another arm accepted |
|---|---|---|---|---|---|---|---|
| BR | 25 | 24 | 1 | 0 | 22 | finished, ifail = 5: 17 | — |
| B0 | 25 | 23 | 2 | 1 | 22 | finished, ifail = 5: 10, 17 | 10 |
| B2 | 25 | 23 | 2 | 1 | 22 | finished, ifail = 5: 5, 17 | 5 |

<sub>`per-arm success — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table F.50.** *Check 2 on large_tokamak_nof: the optimiser's iterations against B0 over the seed set, summed over attempts (the acceptance statistic, median against 1.05) and on the final attempt, with the ratio of sums beside; ε is the evaluation-count ratio (sweeps_per_eval.n_evaluations, I-26 closed) with the seeds on which it is exactly 1, and the sweep ratio is its own column. The B1 → B2 row is the plan's pre-declared ε = 1. n = 22 (seeds on which every arm of large_tokamak_nof converged).*

| pair | n | summed median (acceptance) | summed sum ratio | verdict | final-attempt median | final-attempt sum ratio | ε median (evaluations) | ε = 1 on | sweeps median | attempts per seed (base/arm) | constructions disagree |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 → BR (beside) | 22 | 1.0000 | 1.0000 | beside | 1.0000 | 1.0000 | 1.0000 | 22 | 0.9795 | 0:1/1, 1:1/1, 2:1/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 10:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 17:1/1, 18:1/1, 19:1/1, 22:1/1, 23:1/1, 24:1/1 | 0 |
| B0 → B1 | 22 | 1.0000 | 0.9942 | PASS | 1.0000 | 0.9942 | 1.0476 | 0 | 1.0139 | 0:1/1, 1:1/1, 2:1/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 10:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 17:1/1, 18:1/1, 19:1/1, 22:1/1, 23:1/1, 24:1/1 | 0 |
| B0 → B2 | 22 | 1.0000 | 0.9942 | PASS | 1.0000 | 0.9942 | 1.0476 | 0 | 2.6524 | 0:1/1, 1:1/1, 2:1/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 10:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 17:1/1, 18:1/1, 19:1/1, 22:1/1, 23:1/1, 24:1/1 | 0 |
| B1 → B2 (beside) | 22 | 1.0000 | 1.0000 | beside | 1.0000 | 1.0000 | 1.0000 | 22 | 2.6158 | 0:1/1, 1:1/1, 2:1/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 10:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 17:1/1, 18:1/1, 19:1/1, 22:1/1, 23:1/1, 24:1/1 | 0 |

<sub>`iteration multiplier (check 2) — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.51.** *Check 2 on low_aspect_ratio_DEMO: the optimiser's iterations against B0 over the seed set, summed over attempts (the acceptance statistic, median against 1.05) and on the final attempt, with the ratio of sums beside; ε is the evaluation-count ratio (sweeps_per_eval.n_evaluations, I-26 closed) with the seeds on which it is exactly 1, and the sweep ratio is its own column. The B1 → B2 row is the plan's pre-declared ε = 1. n = 11 (seeds on which every arm of low_aspect_ratio_DEMO converged).*

| pair | n | summed median (acceptance) | summed sum ratio | verdict | final-attempt median | final-attempt sum ratio | ε median (evaluations) | ε = 1 on | sweeps median | attempts per seed (base/arm) | constructions disagree |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 → BR (beside) | 11 | 1.0000 | 1.0000 | beside | 1.0000 | 1.0000 | 1.0000 | 11 | 1.0352 | 0:1/1, 1:2/2, 5:1/1, 6:1/1, 9:1/1, 11:1/1, 12:1/1, 13:1/1, 15:1/1, 18:1/1, 19:1/1 | 1 |
| B0 → B1 | 11 | 0.8125 | 0.7012 | PASS | 0.8333 | 1.0088 | 0.8468 | 0 | 0.8046 | 0:1/1, 1:2/1, 5:1/1, 6:1/1, 9:1/1, 11:1/1, 12:1/1, 13:1/1, 15:1/1, 18:1/1, 19:1/1 | 1 |
| B0 → B2 | 11 | 0.8125 | 0.7012 | PASS | 0.8333 | 1.0088 | 0.8468 | 0 | 2.1169 | 0:1/1, 1:2/1, 5:1/1, 6:1/1, 9:1/1, 11:1/1, 12:1/1, 13:1/1, 15:1/1, 18:1/1, 19:1/1 | 1 |
| B1 → B2 (beside) | 11 | 1.0000 | 1.0000 | beside | 1.0000 | 1.0000 | 1.0000 | 11 | 2.6335 | 0:1/1, 1:1/1, 5:1/1, 6:1/1, 9:1/1, 11:1/1, 12:1/1, 13:1/1, 15:1/1, 18:1/1, 19:1/1 | 0 |

<sub>`iteration multiplier (check 2) — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.52.** *Check 2 on st_regression: the optimiser's iterations against B0 over the seed set, summed over attempts (the acceptance statistic, median against 1.05) and on the final attempt, with the ratio of sums beside; ε is the evaluation-count ratio (sweeps_per_eval.n_evaluations, I-26 closed) with the seeds on which it is exactly 1, and the sweep ratio is its own column. The B1 → B2 row is the plan's pre-declared ε = 1. n = 22 (seeds on which every arm of st_regression converged).*

| pair | n | summed median (acceptance) | summed sum ratio | verdict | final-attempt median | final-attempt sum ratio | ε median (evaluations) | ε = 1 on | sweeps median | attempts per seed (base/arm) | constructions disagree |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 → BR (beside) | 22 | 1.0000 | 1.2405 | beside | 1.0000 | 0.9221 | 1.0000 | 15 | 0.9906 | 0:1/1, 1:1/1, 2:2/2, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 11:1/1, 12:1/2, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 18:1/1, 19:1/1, 20:1/1, 21:1/1, 22:1/1, 23:1/1, 24:1/3 | 3 |
| B0 → B2 | 22 | 1.0000 | 0.9530 | PASS | 1.0000 | 1.0019 | 1.0000 | 14 | 2.7767 | 0:1/1, 1:1/1, 2:2/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 18:1/1, 19:1/1, 20:1/1, 21:1/1, 22:1/1, 23:1/1, 24:1/1 | 1 |

<sub>`iteration multiplier (check 2) — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table F.53.** *Exit accuracy by arm on large_tokamak_nof over the arm group's finished runs (accepted or not): the restricted maximum scaled residual (median, max) on both rulers, the argmax and the whole-state maximum; audit position entry_to_write_output_files. The whole-state column is large for B2 by design and is not judged. n = 100 (optimisation-phase runs of large_tokamak_nof in this arm group).*

| arm | ruler | n (runs) | with a restricted statistic | restricted median | restricted max | restricted argmax | components above τ | whole-state median | components excluded | audit position | audit instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | frozen | 22 | 22 | 1.150e-11 | 1.332e-11 | heat_transport.tlvpmw | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.150e-11 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| BR | mixed | 22 | 22 | 1.150e-11 | 1.253e-11 | heat_transport.tlvpmw | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.150e-11 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | frozen | 22 | 22 | 1.150e-11 | 1.332e-11 | heat_transport.tlvpmw | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.150e-11 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | mixed | 22 | 22 | 1.150e-11 | 1.253e-11 | heat_transport.tlvpmw | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.150e-11 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B1 | frozen | 22 | 22 | 0 | 7.257e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.c_pf_cs_coil_flat_top_ma | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B1 | mixed | 22 | 22 | 0 | 6.928e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.c_pf_cs_coil_flat_top_ma | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B2 | frozen | 22 | 22 | 0 | 7.257e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.c_pf_cs_coil_flat_top_ma | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.066e+00 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B2 | mixed | 22 | 22 | 0 | 6.928e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.c_pf_cs_coil_flat_top_ma | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.000e+00 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |

<sub>`achieved accuracy at the accepted optimum — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.54.** *Exit accuracy by arm on low_aspect_ratio_DEMO over the arm group's finished runs (accepted or not): the restricted maximum scaled residual (median, max) on both rulers, the argmax and the whole-state maximum; audit position entry_to_write_output_files. The whole-state column is large for B2 by design and is not judged. n = 100 (optimisation-phase runs of low_aspect_ratio_DEMO in this arm group).*

| arm | ruler | n (runs) | with a restricted statistic | restricted median | restricted max | restricted argmax | components above τ | whole-state median | components excluded | audit position | audit instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | frozen | 23 | 23 | 0 | inf | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.eta_cd_dimensionless_hcd_primary, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| BR | mixed | 23 | 23 | 0 | inf | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.eta_cd_dimensionless_hcd_primary, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | frozen | 21 | 21 | 0 | 5.315e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | mixed | 21 | 21 | 0 | 3.995e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B1 | frozen | 20 | 20 | 0 | 5.315e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B1 | mixed | 20 | 20 | 0 | 4.365e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B2 | frozen | 20 | 20 | 0 | 5.315e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.007e+00 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B2 | mixed | 20 | 20 | 0 | 3.995e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.000e+00 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |

<sub>`achieved accuracy at the accepted optimum — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.55.** *Exit accuracy by arm on st_regression over the arm group's finished runs (accepted or not): the restricted maximum scaled residual (median, max) on both rulers, the argmax and the whole-state maximum; audit position entry_to_write_output_files. The whole-state column is large for B2 by design and is not judged. n = 75 (optimisation-phase runs of st_regression in this arm group).*

| arm | ruler | n (runs) | with a restricted statistic | restricted median | restricted max | restricted argmax | components above τ | whole-state median | components excluded | audit position | audit instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | frozen | 25 | 25 | 4.875e-14 | 5.040e-14 | blanket.deg_blkt_inboard_poloidal_plasma, physics.f_beta_alpha_beam_thermal | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 4.875e-14 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| BR | mixed | 25 | 25 | 4.871e-14 | 5.035e-14 | blanket.deg_blkt_inboard_poloidal_plasma, physics.f_beta_alpha_beam_thermal | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 4.871e-14 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | frozen | 25 | 25 | 4.894e-14 | 4.967e-14 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.big_q_plasma, physics.f_beta_alpha_beam_thermal | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 4.894e-14 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | mixed | 25 | 25 | 4.889e-14 | 4.962e-14 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.big_q_plasma, physics.f_beta_alpha_beam_thermal | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 4.889e-14 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B2 | frozen | 25 | 25 | 7.497e-12 | 3.587e-11 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, heat_transport.tlvpmw, physics.f_beta_alpha_beam_thermal, superconducting_tfcoil.a_tf_plasma_case | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.598e+00 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B2 | mixed | 25 | 25 | 6.643e-12 | 3.585e-11 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, heat_transport.tlvpmw, physics.f_beta_alpha_beam_thermal, superconducting_tfcoil.a_tf_plasma_case | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.000e+00 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |

<sub>`achieved accuracy at the accepted optimum — st_regression — campaign_optimisation · BR·B0·B2`</sub>

## F.4 The same cells, computed a second time

Every table of the tally recomputed by `harness/measurement/analysis.py`, a second implementation that imports none of the tally's constructions. Column headings are the record keys, not the report's headings; the verdict on whether the two agree — table by table, row by row, cell by cell, without tolerance — is gate `recomputation`'s, one row of the report's gate table.

**Table F.56.** *units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state audit maximum over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the finished optimisation-phase runs of large_tokamak_nof in this arm group.  Construction: median nearest-rank upper-middle; the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: entry_to_write_output_files.  The audit instrument's version is **read from the record**: task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns, and this column is what tells two otherwise identical tables apart.  Both rulers or neither. n = 100 (optimisation-phase runs of large_tokamak_nof in this arm group).*

| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_max | argmax | n_above_tau | whole_median | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | frozen | 22 | 22 | 1.14998e-11 | 1.33158e-11 | heat_transport.tlvpmw | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.14998e-11 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| BR | mixed | 22 | 22 | 1.14998e-11 | 1.25276e-11 | heat_transport.tlvpmw | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.14998e-11 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | frozen | 22 | 22 | 1.14994e-11 | 1.33159e-11 | heat_transport.tlvpmw | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.14994e-11 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | mixed | 22 | 22 | 1.14994e-11 | 1.25278e-11 | heat_transport.tlvpmw | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.14994e-11 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B1 | frozen | 22 | 22 | 0 | 7.25732e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.c_pf_cs_coil_flat_top_ma | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B1 | mixed | 22 | 22 | 0 | 6.92805e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.c_pf_cs_coil_flat_top_ma | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B2 | frozen | 22 | 22 | 0 | 7.25732e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.c_pf_cs_coil_flat_top_ma | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.066 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B2 | mixed | 22 | 22 | 0 | 6.92805e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.c_pf_cs_coil_flat_top_ma | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1 | 122 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |

<sub>`achieved accuracy at the accepted optimum — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.57.** *units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state audit maximum over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the finished optimisation-phase runs of low_aspect_ratio_DEMO in this arm group.  Construction: median nearest-rank upper-middle; the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: entry_to_write_output_files.  The audit instrument's version is **read from the record**: task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns, and this column is what tells two otherwise identical tables apart.  Both rulers or neither. n = 100 (optimisation-phase runs of low_aspect_ratio_DEMO in this arm group).*

| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_max | argmax | n_above_tau | whole_median | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | frozen | 23 | 23 | 0 | inf | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.eta_cd_dimensionless_hcd_primary, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| BR | mixed | 23 | 23 | 0 | inf | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.eta_cd_dimensionless_hcd_primary, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | frozen | 21 | 21 | 0 | 5.31457e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | mixed | 21 | 21 | 0 | 3.99521e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B1 | frozen | 20 | 20 | 0 | 5.31457e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B1 | mixed | 20 | 20 | 0 | 4.36506e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B2 | frozen | 20 | 20 | 0 | 5.31457e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.00722 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B2 | mixed | 20 | 20 | 0 | 3.99521e-15 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |

<sub>`achieved accuracy at the accepted optimum — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.58.** *units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state audit maximum over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the finished optimisation-phase runs of st_regression in this arm group.  Construction: median nearest-rank upper-middle; the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: entry_to_write_output_files.  The audit instrument's version is **read from the record**: task A62 (exit-audit-restore) widens the snapshot to the whole data structure under decision D25, which moves every value in these columns, and this column is what tells two otherwise identical tables apart.  Both rulers or neither. n = 75 (optimisation-phase runs of st_regression in this arm group).*

| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_max | argmax | n_above_tau | whole_median | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | frozen | 25 | 25 | 4.8754e-14 | 5.04035e-14 | blanket.deg_blkt_inboard_poloidal_plasma, physics.f_beta_alpha_beam_thermal | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 4.8754e-14 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| BR | mixed | 25 | 25 | 4.87066e-14 | 5.03546e-14 | blanket.deg_blkt_inboard_poloidal_plasma, physics.f_beta_alpha_beam_thermal | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 4.87066e-14 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | frozen | 25 | 25 | 4.89373e-14 | 4.96704e-14 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.big_q_plasma, physics.f_beta_alpha_beam_thermal | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 4.89373e-14 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B0 | mixed | 25 | 25 | 4.88897e-14 | 4.96221e-14 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.big_q_plasma, physics.f_beta_alpha_beam_thermal | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 4.88897e-14 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B2 | frozen | 25 | 25 | 7.49746e-12 | 3.58709e-11 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, heat_transport.tlvpmw, physics.f_beta_alpha_beam_thermal, superconducting_tfcoil.a_tf_plasma_case | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1.5975 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |
| B2 | mixed | 25 | 25 | 6.64269e-12 | 3.58474e-11 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, heat_transport.tlvpmw, physics.f_beta_alpha_beam_thermal, superconducting_tfcoil.a_tf_plasma_case | 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 | 1 | 123 | entry_to_write_output_files | snapshot at before_finalise,entry_to_write_output_files |

<sub>`achieved accuracy at the accepted optimum — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table F.59.** *units: model executions during the solve; ratios dimensionless.  A row is one arm over the seed set.  A column is an absolute per-run mean with its bracket, or one reading of the ratio against the flat control.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 22 seed(s) on which every arm of large_tokamak_nof reached an accepted optimum.  Construction: solve-phase node calls **summed over attempts[]** per run, so the ratio is over the quantity the attempts decompose; pooled = Σ arm / Σ base, median nearest-rank upper-middle of the per-seed ratios, worse = seeds on which the arm cost more.  Retries are a term, not a footnote: the ratio is published with and without the retried seeds, and a seed counts as retried when **either** side of the pair retried.  The arrangement-method calls are two columns of their own — the per-run mean and the sum over the set — and are never pooled into the node calls. n = 22 (seeds on which every arm of large_tokamak_nof converged).*

| arm | n | node_calls_mean | bracket | arrangement_method_calls_per_run | arrangement_method_calls | with_pooled | with_median | with_worse | n_retried | without_pooled | without_median | without_n |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | 22 | 41479.8 | [36855, 47817] | 0 | 0 | 0.97564 | 0.979422 | 0 | 0 | 0.97564 | 0.979422 | 22 |
| B0 | 22 | 42515.5 | [37590, 50253] | 0 | 0 | 1 | 1 | 0 | 0 | 1 | 1 | 22 |
| B1 | 22 | 42841.9 | [38220, 49980] | 0 | 0 | 1.00768 | 1.01505 | 18 | 0 | 1.00768 | 1.01505 | 22 |
| B2 | 22 | 27187.5 | [24296, 31813] | 5330.95 | 117281 | 0.639472 | 0.645152 | 0 | 0 | 0.639472 | 0.645152 | 22 |

<sub>`cost (check 4) — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.60.** *units: model executions during the solve; ratios dimensionless.  A row is one arm over the seed set.  A column is an absolute per-run mean with its bracket, or one reading of the ratio against the flat control.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 11 seed(s) on which every arm of low_aspect_ratio_DEMO reached an accepted optimum.  Construction: solve-phase node calls **summed over attempts[]** per run, so the ratio is over the quantity the attempts decompose; pooled = Σ arm / Σ base, median nearest-rank upper-middle of the per-seed ratios, worse = seeds on which the arm cost more.  Retries are a term, not a footnote: the ratio is published with and without the retried seeds, and a seed counts as retried when **either** side of the pair retried.  The arrangement-method calls are two columns of their own — the per-run mean and the sum over the set — and are never pooled into the node calls. n = 11 (seeds on which every arm of low_aspect_ratio_DEMO converged).*

| arm | n | node_calls_mean | bracket | arrangement_method_calls_per_run | arrangement_method_calls | with_pooled | with_median | with_worse | n_retried | without_pooled | without_median | without_n |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | 11 | 169943 | [60921, 669207] | 0 | 0 | 1.02998 | 1.03517 | 11 | 1 | 1.03508 | 1.03518 | 10 |
| B0 | 11 | 164997 | [58947, 655473] | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 10 |
| B1 | 11 | 114154 | [53214, 360591] | 0 | 0 | 0.691856 | 0.804931 | 3 | 1 | 1.01291 | 0.825733 | 10 |
| B2 | 11 | 74312.4 | [34628, 234616] | 14318.5 | 157504 | 0.450386 | 0.523683 | 2 | 1 | 0.659427 | 0.537118 | 10 |

<sub>`cost (check 4) — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.61.** *units: model executions during the solve; ratios dimensionless.  A row is one arm over the seed set.  A column is an absolute per-run mean with its bracket, or one reading of the ratio against the flat control.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 22 seed(s) on which every arm of st_regression reached an accepted optimum.  Construction: solve-phase node calls **summed over attempts[]** per run, so the ratio is over the quantity the attempts decompose; pooled = Σ arm / Σ base, median nearest-rank upper-middle of the per-seed ratios, worse = seeds on which the arm cost more.  Retries are a term, not a footnote: the ratio is published with and without the retried seeds, and a seed counts as retried when **either** side of the pair retried.  The arrangement-method calls are two columns of their own — the per-run mean and the sum over the set — and are never pooled into the node calls. n = 22 (seeds on which every arm of st_regression converged).*

| arm | n | node_calls_mean | bracket | arrangement_method_calls_per_run | arrangement_method_calls | with_pooled | with_median | with_worse | n_retried | without_pooled | without_median | without_n |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | 22 | 126868 | [39627, 838929] | 0 | 0 | 1.19679 | 0.990627 | 3 | 3 | 0.89988 | 0.990627 | 19 |
| B0 | 22 | 106007 | [39732, 295701] | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 21 |
| B2 | 22 | 56507.3 | [23484, 169358] | 12762.5 | 280776 | 0.533052 | 0.59106 | 0 | 1 | 0.543877 | 0.59106 | 21 |

<sub>`cost (check 4) — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table F.62.** *units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A1.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 100 run(s) of large_tokamak_nof.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other. n = 100 (evaluation-phase runs of large_tokamak_nof).*

| arm | ok | calls_per_eval | calls_bracket | sweeps_per_eval | sweeps_by_block | arrangement_method_calls | paired_seeds | pooled | median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 25/25 | 104.16 | [84, 105] | 4.96 | — | 0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.96875 | 1 | 0 |
| A0 | 25/25 | 115.92 | [105, 126] | 5.52 | FLAT 138 | 0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 1.07812 | 1 | 10 |
| A1 | 25/25 | 107.52 | [84, 126] | 5.12 | FLAT 128 | 0 | — | — | — | — |
| A2 | 25/25 | 60.48 | [60, 63] | 13.16 | FF 0, M1 100, M2 129, M3 75, PULSE 0 | 13.16 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.5625 | 0.571429 | 0 |

<sub>`cost per call — large_tokamak_nof — campaign_displaced`</sub>

**Table F.63.** *units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; 1 run(s) of large_tokamak_nof.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other. n = 1 (evaluation-phase runs of large_tokamak_nof).*

| arm | ok | calls_per_eval | calls_bracket | sweeps_per_eval | sweeps_by_block | arrangement_method_calls | paired_seeds | pooled | median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 1/1 | 126 | [126, 126] | 6 | FLAT 6 | 0 | — | — | — | — |

<sub>`cost per call — large_tokamak_nof — campaign_entry_references`</sub>

**Table F.64.** *units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A1.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 80 run(s) of large_tokamak_nof.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other. n = 80 (evaluation-phase runs of large_tokamak_nof).*

| arm | ok | calls_per_eval | calls_bracket | sweeps_per_eval | sweeps_by_block | arrangement_method_calls | paired_seeds | pooled | median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 20/20 | 60.9 | [42, 84] | 2.9 | — | 0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 0.966667 | 1 | 0 |
| A0 | 20/20 | 66.15 | [42, 105] | 3.15 | FLAT 63 | 0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 1.05 | 1 | 3 |
| A1 | 20/20 | 63 | [42, 105] | 3 | FLAT 60 | 0 | — | — | — | — |
| A2 | 20/20 | 40.35 | [20, 55] | 7.7 | FF 0, M1 38, M2 49, M3 47, PULSE 0 | 7.7 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 0.640476 | 0.607143 | 0 |

<sub>`cost per call — large_tokamak_nof — campaign_stencil_backward`</sub>

**Table F.65.** *units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A1.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 80 run(s) of large_tokamak_nof.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other. n = 80 (evaluation-phase runs of large_tokamak_nof).*

| arm | ok | calls_per_eval | calls_bracket | sweeps_per_eval | sweeps_by_block | arrangement_method_calls | paired_seeds | pooled | median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 20/20 | 61.95 | [42, 84] | 2.95 | — | 0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 0.983333 | 1 | 0 |
| A0 | 20/20 | 66.15 | [42, 105] | 3.15 | FLAT 63 | 0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 1.05 | 1 | 3 |
| A1 | 20/20 | 63 | [42, 105] | 3 | FLAT 60 | 0 | — | — | — | — |
| A2 | 20/20 | 39.15 | [20, 55] | 7.6 | FF 0, M1 38, M2 49, M3 45, PULSE 0 | 7.6 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 0.621429 | 0.607143 | 0 |

<sub>`cost per call — large_tokamak_nof — campaign_stencil_forward`</sub>

**Table F.66.** *units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A1.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 100 run(s) of low_aspect_ratio_DEMO.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other. n = 100 (evaluation-phase runs of low_aspect_ratio_DEMO).*

| arm | ok | calls_per_eval | calls_bracket | sweeps_per_eval | sweeps_by_block | arrangement_method_calls | paired_seeds | pooled | median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 25/25 | 105 | [105, 105] | 5 | — | 0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 1.01626 | 1 | 2 |
| A0 | 25/25 | 105 | [105, 105] | 5 | FLAT 125 | 0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 1.01626 | 1 | 2 |
| A1 | 25/25 | 103.32 | [84, 105] | 4.92 | FLAT 123 | 0 | — | — | — | — |
| A2 | 25/25 | 59.64 | [57, 60] | 12.88 | FF 0, M1 100, M2 122, M3 75, PULSE 0 | 12.88 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.577236 | 0.571429 | 0 |

<sub>`cost per call — low_aspect_ratio_DEMO — campaign_displaced`</sub>

**Table F.67.** *units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; 1 run(s) of low_aspect_ratio_DEMO.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other. n = 1 (evaluation-phase runs of low_aspect_ratio_DEMO).*

| arm | ok | calls_per_eval | calls_bracket | sweeps_per_eval | sweeps_by_block | arrangement_method_calls | paired_seeds | pooled | median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 1/1 | 105 | [105, 105] | 5 | FLAT 5 | 0 | — | — | — | — |

<sub>`cost per call — low_aspect_ratio_DEMO — campaign_entry_references`</sub>

**Table F.68.** *units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A1.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 76 run(s) of low_aspect_ratio_DEMO.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other. n = 76 (evaluation-phase runs of low_aspect_ratio_DEMO).*

| arm | ok | calls_per_eval | calls_bracket | sweeps_per_eval | sweeps_by_block | arrangement_method_calls | paired_seeds | pooled | median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 19/19 | 67.4211 | [42, 105] | 3.21053 | — | 0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 1.05172 | 1 | 4 |
| A0 | 19/19 | 68.5263 | [42, 105] | 3.26316 | FLAT 62 | 0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 1.06897 | 1 | 4 |
| A1 | 19/19 | 64.1053 | [42, 84] | 3.05263 | FLAT 58 | 0 | — | — | — | — |
| A2 | 19/19 | 42.3684 | [33, 55] | 7.84211 | FF 0, M1 36, M2 46, M3 48, PULSE 0 | 7.84211 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 0.66092 | 0.714286 | 0 |

<sub>`cost per call — low_aspect_ratio_DEMO — campaign_stencil_backward`</sub>

**Table F.69.** *units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A1.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 76 run(s) of low_aspect_ratio_DEMO.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other. n = 76 (evaluation-phase runs of low_aspect_ratio_DEMO).*

| arm | ok | calls_per_eval | calls_bracket | sweeps_per_eval | sweeps_by_block | arrangement_method_calls | paired_seeds | pooled | median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 19/19 | 67.4211 | [42, 105] | 3.21053 | — | 0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 1.07018 | 1 | 4 |
| A0 | 19/19 | 66.3158 | [42, 105] | 3.15789 | FLAT 60 | 0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 1.05263 | 1 | 3 |
| A1 | 19/19 | 63 | [42, 84] | 3 | FLAT 57 | 0 | — | — | — | — |
| A2 | 19/19 | 40.3158 | [33, 55] | 7.63158 | FF 0, M1 36, M2 45, M3 45, PULSE 0 | 7.63158 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 0.639933 | 0.607143 | 0 |

<sub>`cost per call — low_aspect_ratio_DEMO — campaign_stencil_forward`</sub>

**Table F.70.** *units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 75 run(s) of st_regression.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other. n = 75 (evaluation-phase runs of st_regression).*

| arm | ok | calls_per_eval | calls_bracket | sweeps_per_eval | sweeps_by_block | arrangement_method_calls | paired_seeds | pooled | median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 25/25 | 103.32 | [84, 105] | 4.92 | — | 0 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.842466 | 0.833333 | 0 |
| A0 | 25/25 | 122.64 | [105, 126] | 5.84 | FLAT 146 | 0 | — | — | — | — |
| A2 | 25/25 | 61.52 | [59, 62] | 14.84 | FF 0, M1 100, M2 146, M3 75, PULSE 25 | 14.84 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.501631 | 0.492063 | 0 |

<sub>`cost per call — st_regression — campaign_displaced`</sub>

**Table F.71.** *units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; 1 run(s) of st_regression.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other. n = 1 (evaluation-phase runs of st_regression).*

| arm | ok | calls_per_eval | calls_bracket | sweeps_per_eval | sweeps_by_block | arrangement_method_calls | paired_seeds | pooled | median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 1/1 | 147 | [147, 147] | 7 | FLAT 7 | 0 | — | — | — | — |

<sub>`cost per call — st_regression — campaign_entry_references`</sub>

**Table F.72.** *units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 42 run(s) of st_regression.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other. n = 42 (evaluation-phase runs of st_regression).*

| arm | ok | calls_per_eval | calls_bracket | sweeps_per_eval | sweeps_by_block | arrangement_method_calls | paired_seeds | pooled | median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 14/14 | 66 | [42, 84] | 3.14286 | — | 0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | 0.93617 | 1 | 0 |
| A0 | 14/14 | 70.5 | [42, 105] | 3.35714 | FLAT 47 | 0 | — | — | — | — |
| A2 | 14/14 | 39.3571 | [19, 53] | 8.78571 | FF 0, M1 31, M2 31, M3 33, PULSE 14 | 8.78571 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | 0.558257 | 0.52381 | 0 |

<sub>`cost per call — st_regression — campaign_stencil_backward`</sub>

**Table F.73.** *units: model-node executions per evaluation; sweeps are walks of the model sequence; ratios dimensionless.  A row is one arm of the evaluation phase on this configuration.  A column is a per-run mean over that arm's finished runs with the observed bracket, or one of the three readings of the ratio against the reference arm A0.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 42 run(s) of st_regression.  Construction: pooled = Σ arm / Σ reference over the seed-paired runs, median = nearest-rank upper-middle of the per-run ratios, worse = runs on which the arm cost more, keyed by seed (displaced entries) or by design-vector column (stencil points).  The population is the one named and no other. n = 42 (evaluation-phase runs of st_regression).*

| arm | ok | calls_per_eval | calls_bracket | sweeps_per_eval | sweeps_by_block | arrangement_method_calls | paired_seeds | pooled | median | worse |
|---|---|---|---|---|---|---|---|---|---|---|
| AR | 14/14 | 63 | [42, 84] | 3 | — | 0 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | 0.933333 | 1 | 0 |
| A0 | 14/14 | 67.5 | [42, 84] | 3.21429 | FLAT 45 | 0 | — | — | — | — |
| A2 | 14/14 | 38.9286 | [19, 50] | 8.64286 | FF 0, M1 31, M2 29, M3 33, PULSE 14 | 8.64286 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | 0.57672 | 0.571429 | 0 |

<sub>`cost per call — st_regression — campaign_stencil_forward`</sub>

**Table F.74.** *units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; every run of large_tokamak_nof.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 100 (evaluation-phase runs of large_tokamak_nof).*

| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| AR | 25 | 25 | yes | — |
| A0 | 25 | 25 | yes | — |
| A1 | 25 | 25 | yes | — |
| A2 | 25 | 25 | yes | — |

<sub>`failure taxonomy — large_tokamak_nof — campaign_displaced`</sub>

**Table F.75.** *units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; every run of large_tokamak_nof.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 1 (evaluation-phase runs of large_tokamak_nof).*

| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| A0 | 1 | 1 | yes | — |

<sub>`failure taxonomy — large_tokamak_nof — campaign_entry_references`</sub>

**Table F.76.** *units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; every run of large_tokamak_nof.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 100 (optimisation-phase runs of large_tokamak_nof).*

| arm | denominator | crashed | ok | sums | detail |
|---|---|---|---|---|---|
| BR | 25 | 3 | 22 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×3 |
| B0 | 25 | 3 | 22 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×3 |
| B1 | 25 | 3 | 22 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×3 |
| B2 | 25 | 3 | 22 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×3 |

<sub>`failure taxonomy — large_tokamak_nof — campaign_optimisation`</sub>

**Table F.77.** *units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; every run of large_tokamak_nof.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 80 (evaluation-phase runs of large_tokamak_nof).*

| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| AR | 20 | 20 | yes | — |
| A0 | 20 | 20 | yes | — |
| A1 | 20 | 20 | yes | — |
| A2 | 20 | 20 | yes | — |

<sub>`failure taxonomy — large_tokamak_nof — campaign_stencil_backward`</sub>

**Table F.78.** *units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; every run of large_tokamak_nof.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 80 (evaluation-phase runs of large_tokamak_nof).*

| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| AR | 20 | 20 | yes | — |
| A0 | 20 | 20 | yes | — |
| A1 | 20 | 20 | yes | — |
| A2 | 20 | 20 | yes | — |

<sub>`failure taxonomy — large_tokamak_nof — campaign_stencil_forward`</sub>

**Table F.79.** *units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; every run of low_aspect_ratio_DEMO.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 100 (evaluation-phase runs of low_aspect_ratio_DEMO).*

| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| AR | 25 | 25 | yes | — |
| A0 | 25 | 25 | yes | — |
| A1 | 25 | 25 | yes | — |
| A2 | 25 | 25 | yes | — |

<sub>`failure taxonomy — low_aspect_ratio_DEMO — campaign_displaced`</sub>

**Table F.80.** *units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; every run of low_aspect_ratio_DEMO.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 1 (evaluation-phase runs of low_aspect_ratio_DEMO).*

| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| A0 | 1 | 1 | yes | — |

<sub>`failure taxonomy — low_aspect_ratio_DEMO — campaign_entry_references`</sub>

**Table F.81.** *units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; every run of low_aspect_ratio_DEMO.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 100 (optimisation-phase runs of low_aspect_ratio_DEMO).*

| arm | denominator | crashed | ok | unconverged | sums | detail |
|---|---|---|---|---|---|---|
| BR | 25 | 2 | 23 | 0 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×2 |
| B0 | 25 | 2 | 21 | 2 | yes | RuntimeError: Failed to converge after 50 iterations, value is nan. ×2; process.core.solver.module_solve.ModuleSolveFailure: block FLAT did not converge in 20 sweeps at tau=1e-06; max scaled residual inf on current_drive.eta_cd_dimensionless_hcd_primary, 1 components above tau ×2 |
| B1 | 25 | 2 | 20 | 3 | yes | process.core.solver.module_solve.ModuleSolveFailure: block FLAT did not converge in 20 sweeps at tau=1e-06; max scaled residual inf on current_drive.eta_cd_dimensionless_hcd_primary, 1 components above tau ×3; RuntimeError: Failed to converge after 50 iterations, value is nan. ×2 |
| B2 | 25 | 2 | 20 | 3 | yes | process.core.solver.module_solve.ModuleSolveFailure: block M1 did not converge in 20 sweeps at tau=1e-06; max scaled residual inf on current_drive.eta_cd_dimensionless_hcd_primary, 1 components above tau ×3; RuntimeError: Failed to converge after 50 iterations, value is nan. ×2 |

<sub>`failure taxonomy — low_aspect_ratio_DEMO — campaign_optimisation`</sub>

**Table F.82.** *units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; every run of low_aspect_ratio_DEMO.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 76 (evaluation-phase runs of low_aspect_ratio_DEMO).*

| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| AR | 19 | 19 | yes | — |
| A0 | 19 | 19 | yes | — |
| A1 | 19 | 19 | yes | — |
| A2 | 19 | 19 | yes | — |

<sub>`failure taxonomy — low_aspect_ratio_DEMO — campaign_stencil_backward`</sub>

**Table F.83.** *units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; every run of low_aspect_ratio_DEMO.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 76 (evaluation-phase runs of low_aspect_ratio_DEMO).*

| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| AR | 19 | 19 | yes | — |
| A0 | 19 | 19 | yes | — |
| A1 | 19 | 19 | yes | — |
| A2 | 19 | 19 | yes | — |

<sub>`failure taxonomy — low_aspect_ratio_DEMO — campaign_stencil_forward`</sub>

**Table F.84.** *units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; every run of st_regression.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 75 (evaluation-phase runs of st_regression).*

| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| AR | 25 | 25 | yes | — |
| A0 | 25 | 25 | yes | — |
| A2 | 25 | 25 | yes | — |

<sub>`failure taxonomy — st_regression — campaign_displaced`</sub>

**Table F.85.** *units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; every run of st_regression.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 1 (evaluation-phase runs of st_regression).*

| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| A0 | 1 | 1 | yes | — |

<sub>`failure taxonomy — st_regression — campaign_entry_references`</sub>

**Table F.86.** *units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; every run of st_regression.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 75 (optimisation-phase runs of st_regression).*

| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| BR | 25 | 25 | yes | — |
| B0 | 25 | 25 | yes | — |
| B2 | 25 | 25 | yes | — |

<sub>`failure taxonomy — st_regression — campaign_optimisation`</sub>

**Table F.87.** *units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; every run of st_regression.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 42 (evaluation-phase runs of st_regression).*

| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| AR | 14 | 14 | yes | — |
| A0 | 14 | 14 | yes | — |
| A2 | 14 | 14 | yes | — |

<sub>`failure taxonomy — st_regression — campaign_stencil_backward`</sub>

**Table F.88.** *units: counts of runs; the detail column is text.  A row is one arm on this configuration.  A column is one disposition of the taxonomy, and the detail is the last line of each unfinished run's traceback, distinct, with its count.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; every run of st_regression.  Construction: every scheduled run is a row and a run that wrote no record is counted as no_record, never skipped.  An arm inactive on a configuration is absent from this table rather than reading 0: a skipped arm and a failing arm are different results.  A crashed start reaches no cost cell. n = 42 (evaluation-phase runs of st_regression).*

| arm | denominator | ok | sums | detail |
|---|---|---|---|---|
| AR | 14 | 14 | yes | — |
| A0 | 14 | 14 | yes | — |
| A2 | 14 | 14 | yes | — |

<sub>`failure taxonomy — st_regression — campaign_stencil_forward`</sub>

**Table F.89.** *units: dimensionless — the largest scaled difference between two arms' exit coupling states at the same entry, in the units τ = 1e-06 is stated in.  A row is one pair of arms: each rung of the evaluation phase's ladder and, marked headline, the partitioned arm against A1; A2/A0 beside on a pulsed configuration.  A column is the pairs the two arms share (by seeds), how many were compared and why the rest were not, the restricted distance's median, p90 and worst pair, the components the maximum sat on, the pairs with any restricted component at or above τ, the pairs where a discrete component differs or a constant moved, and the whole-state distance beside.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 100 pair(s) of large_tokamak_nof.  Construction (re-derived here from the coupling-state artifact and the exit-state files, importing no line of the predicate): max_i |y_arm,i − y_base,i| / s_i over the continuous components not written by the once-per-run deferred nodes, s_i the committed scale; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  Reported, not accepted on: no acceptance rule was pre-declared for this quantity (added by task A76 (fixed-point-distance)). n = 100 (evaluation-phase pairs of large_tokamak_nof over the ladder's rungs).*

| pair | role | n | n_compared | not_compared | restricted_median | restricted_p90 | restricted_max | worst_pair | argmax | n_pairs_above_tau | n_pairs_unclean | whole_median | whole_p90 | n_excluded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A0/AR | rung | 25 | 25 | — | 2.62424e-08 | 1.542e-07 | 2.26469e-07 | 20 | blanket.deg_blkt_inboard_poloidal_plasma; heat_transport.tlvpmw; power.qac | 0 | 0 | 3.25488e-08 | 4.14213e-07 | 122 |
| A1/A0 | rung | 25 | 25 | — | 0.0966549 | 0.198527 | 0.256266 | 15 | power.qac | 25 | 0 | 0.291854 | 0.833263 | 122 |
| A2/A1 | headline | 25 | 25 | — | 5.09395e-12 | 1.83804e-10 | 2.70933e-10 | 15 | blanket.deg_blkt_inboard_poloidal_plasma; heat_transport.tlvpmw; pf_coil.stress_z_cs_self_midplane_profile | 0 | 0 | 2.43528 | 9.85963 | 122 |
| A2/A0 | beside | 25 | 25 | — | 0.0966549 | 0.198527 | 0.256266 | 15 | power.qac | 25 | 0 | 2.81844 | 10.2927 | 122 |

<sub>`fixed-point distance — large_tokamak_nof — campaign_displaced`</sub>

**Table F.90.** *units: dimensionless — the largest scaled difference between two arms' exit coupling states at the same entry, in the units τ = 1e-06 is stated in.  A row is one pair of arms: each rung of the evaluation phase's ladder and, marked headline, the partitioned arm against A1; A2/A0 beside on a pulsed configuration.  A column is the pairs the two arms share (by columns), how many were compared and why the rest were not, the restricted distance's median, p90 and worst pair, the components the maximum sat on, the pairs with any restricted component at or above τ, the pairs where a discrete component differs or a constant moved, and the whole-state distance beside.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 80 pair(s) of large_tokamak_nof.  Construction (re-derived here from the coupling-state artifact and the exit-state files, importing no line of the predicate): max_i |y_arm,i − y_base,i| / s_i over the continuous components not written by the once-per-run deferred nodes, s_i the committed scale; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  Reported, not accepted on: no acceptance rule was pre-declared for this quantity (added by task A76 (fixed-point-distance)). n = 80 (evaluation-phase pairs of large_tokamak_nof over the ladder's rungs).*

| pair | role | n | n_compared | not_compared | restricted_median | restricted_p90 | restricted_max | worst_pair | argmax | n_pairs_above_tau | n_pairs_unclean | whole_median | whole_p90 | n_excluded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A0/AR | rung | 20 | 20 | — | 0 | 1.7301e-10 | 2.64512e-06 | 19 | blanket.deg_blkt_inboard_poloidal_plasma; heat_transport.tlvpmw; power.qac | 1 | 0 | 0 | 1.7301e-10 | 122 |
| A1/A0 | rung | 20 | 20 | — | 0.000712723 | 0.00525179 | 0.00798438 | 8 | power.qac | 14 | 0 | 0.00179452 | 0.0132243 | 122 |
| A2/A1 | headline | 20 | 20 | — | 0 | 4.61348e-13 | 4.62179e-13 | 5 | blanket.deg_blkt_inboard_poloidal_plasma; heat_transport.tlvpmw; pf_coil.stress_z_cs_self_midplane_profile | 0 | 0 | 0.00201638 | 0.0697524 | 122 |
| A2/A0 | beside | 20 | 20 | — | 0.000712723 | 0.00525179 | 0.00798438 | 8 | power.qac | 14 | 0 | 0.0100329 | 0.0836696 | 122 |

<sub>`fixed-point distance — large_tokamak_nof — campaign_stencil_backward`</sub>

**Table F.91.** *units: dimensionless — the largest scaled difference between two arms' exit coupling states at the same entry, in the units τ = 1e-06 is stated in.  A row is one pair of arms: each rung of the evaluation phase's ladder and, marked headline, the partitioned arm against A1; A2/A0 beside on a pulsed configuration.  A column is the pairs the two arms share (by columns), how many were compared and why the rest were not, the restricted distance's median, p90 and worst pair, the components the maximum sat on, the pairs with any restricted component at or above τ, the pairs where a discrete component differs or a constant moved, and the whole-state distance beside.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 80 pair(s) of large_tokamak_nof.  Construction (re-derived here from the coupling-state artifact and the exit-state files, importing no line of the predicate): max_i |y_arm,i − y_base,i| / s_i over the continuous components not written by the once-per-run deferred nodes, s_i the committed scale; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  Reported, not accepted on: no acceptance rule was pre-declared for this quantity (added by task A76 (fixed-point-distance)). n = 80 (evaluation-phase pairs of large_tokamak_nof over the ladder's rungs).*

| pair | role | n | n_compared | not_compared | restricted_median | restricted_p90 | restricted_max | worst_pair | argmax | n_pairs_above_tau | n_pairs_unclean | whole_median | whole_p90 | n_excluded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A0/AR | rung | 20 | 20 | — | 0 | 1.86926e-08 | 7.18976e-08 | 8 | blanket.deg_blkt_inboard_poloidal_plasma; power.qac | 0 | 0 | 0 | 3.38483e-08 | 122 |
| A1/A0 | rung | 20 | 20 | — | 0.000710841 | 0.00531275 | 0.00793734 | 8 | power.qac | 14 | 0 | 0.00172697 | 0.012906 | 122 |
| A2/A1 | headline | 20 | 20 | — | 2.57916e-12 | 3.40875e-11 | 3.46179e-11 | 12 | blanket.deg_blkt_inboard_poloidal_plasma; heat_transport.tlvpmw; pf_coil.stress_z_cs_self_midplane_profile | 0 | 0 | 0.00201638 | 0.0711547 | 122 |
| A2/A0 | beside | 20 | 20 | — | 0.000710841 | 0.00531275 | 0.00793734 | 8 | power.qac | 14 | 0 | 0.00997377 | 0.0838118 | 122 |

<sub>`fixed-point distance — large_tokamak_nof — campaign_stencil_forward`</sub>

**Table F.92.** *units: dimensionless — the largest scaled difference between two arms' exit coupling states at the same entry, in the units τ = 1e-06 is stated in.  A row is one pair of arms: each rung of the evaluation phase's ladder and, marked headline, the partitioned arm against A1; A2/A0 beside on a pulsed configuration.  A column is the pairs the two arms share (by seeds), how many were compared and why the rest were not, the restricted distance's median, p90 and worst pair, the components the maximum sat on, the pairs with any restricted component at or above τ, the pairs where a discrete component differs or a constant moved, and the whole-state distance beside.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 100 pair(s) of low_aspect_ratio_DEMO.  Construction (re-derived here from the coupling-state artifact and the exit-state files, importing no line of the predicate): max_i |y_arm,i − y_base,i| / s_i over the continuous components not written by the once-per-run deferred nodes, s_i the committed scale; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  Reported, not accepted on: no acceptance rule was pre-declared for this quantity (added by task A76 (fixed-point-distance)). n = 100 (evaluation-phase pairs of low_aspect_ratio_DEMO over the ladder's rungs).*

| pair | role | n | n_compared | not_compared | restricted_median | restricted_p90 | restricted_max | worst_pair | argmax | n_pairs_above_tau | n_pairs_unclean | whole_median | whole_p90 | n_excluded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A0/AR | rung | 25 | 25 | — | 0 | 0 | 0 | — | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 0 | 0 | 123 |
| A1/A0 | rung | 25 | 25 | — | 0.0702559 | 0.15854 | 0.204676 | 15 | power.e_plant_net_electric_pulse_kwh; power.e_plant_net_electric_pulse_mj; times.t_burn_0 | 25 | 0 | 0.0702559 | 0.15854 | 123 |
| A2/A1 | headline | 25 | 25 | — | 0 | 0 | 0 | — | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 0.181599 | 0.287845 | 123 |
| A2/A0 | beside | 25 | 25 | — | 0.0702559 | 0.15854 | 0.204676 | 15 | power.e_plant_net_electric_pulse_kwh; power.e_plant_net_electric_pulse_mj; times.t_burn_0 | 25 | 0 | 0.183935 | 0.286352 | 123 |

<sub>`fixed-point distance — low_aspect_ratio_DEMO — campaign_displaced`</sub>

**Table F.93.** *units: dimensionless — the largest scaled difference between two arms' exit coupling states at the same entry, in the units τ = 1e-06 is stated in.  A row is one pair of arms: each rung of the evaluation phase's ladder and, marked headline, the partitioned arm against A1; A2/A0 beside on a pulsed configuration.  A column is the pairs the two arms share (by columns), how many were compared and why the rest were not, the restricted distance's median, p90 and worst pair, the components the maximum sat on, the pairs with any restricted component at or above τ, the pairs where a discrete component differs or a constant moved, and the whole-state distance beside.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 76 pair(s) of low_aspect_ratio_DEMO.  Construction (re-derived here from the coupling-state artifact and the exit-state files, importing no line of the predicate): max_i |y_arm,i − y_base,i| / s_i over the continuous components not written by the once-per-run deferred nodes, s_i the committed scale; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  Reported, not accepted on: no acceptance rule was pre-declared for this quantity (added by task A76 (fixed-point-distance)). n = 76 (evaluation-phase pairs of low_aspect_ratio_DEMO over the ladder's rungs).*

| pair | role | n | n_compared | not_compared | restricted_median | restricted_p90 | restricted_max | worst_pair | argmax | n_pairs_above_tau | n_pairs_unclean | whole_median | whole_p90 | n_excluded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A0/AR | rung | 19 | 19 | — | 0 | 0 | 0 | — | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 0 | 0 | 123 |
| A1/A0 | rung | 19 | 19 | — | 0.000548232 | 0.00377996 | 0.00450458 | 8 | blanket.deg_blkt_inboard_poloidal_plasma; power.e_plant_net_electric_pulse_kwh; power.e_plant_net_electric_pulse_mj | 14 | 0 | 0.000548232 | 0.00377996 | 123 |
| A2/A1 | headline | 19 | 19 | — | 0 | 0 | 6.86365e-19 | 3 | blanket.deg_blkt_inboard_poloidal_plasma; pf_coil.stress_z_cs_self_midplane_profile | 0 | 0 | 0.00150908 | 0.00837004 | 123 |
| A2/A0 | beside | 19 | 19 | — | 0.000548232 | 0.00377996 | 0.00450458 | 8 | blanket.deg_blkt_inboard_poloidal_plasma; power.e_plant_net_electric_pulse_kwh; power.e_plant_net_electric_pulse_mj | 14 | 0 | 0.00312409 | 0.00837004 | 123 |

<sub>`fixed-point distance — low_aspect_ratio_DEMO — campaign_stencil_backward`</sub>

**Table F.94.** *units: dimensionless — the largest scaled difference between two arms' exit coupling states at the same entry, in the units τ = 1e-06 is stated in.  A row is one pair of arms: each rung of the evaluation phase's ladder and, marked headline, the partitioned arm against A1; A2/A0 beside on a pulsed configuration.  A column is the pairs the two arms share (by columns), how many were compared and why the rest were not, the restricted distance's median, p90 and worst pair, the components the maximum sat on, the pairs with any restricted component at or above τ, the pairs where a discrete component differs or a constant moved, and the whole-state distance beside.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 76 pair(s) of low_aspect_ratio_DEMO.  Construction (re-derived here from the coupling-state artifact and the exit-state files, importing no line of the predicate): max_i |y_arm,i − y_base,i| / s_i over the continuous components not written by the once-per-run deferred nodes, s_i the committed scale; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  Reported, not accepted on: no acceptance rule was pre-declared for this quantity (added by task A76 (fixed-point-distance)). n = 76 (evaluation-phase pairs of low_aspect_ratio_DEMO over the ladder's rungs).*

| pair | role | n | n_compared | not_compared | restricted_median | restricted_p90 | restricted_max | worst_pair | argmax | n_pairs_above_tau | n_pairs_unclean | whole_median | whole_p90 | n_excluded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A0/AR | rung | 19 | 19 | — | 0 | 0 | 1.97648e-11 | 13 | blanket.deg_blkt_inboard_poloidal_plasma; heat_transport.tlvpmw | 0 | 0 | 0 | 0 | 123 |
| A1/A0 | rung | 19 | 19 | — | 0.000553643 | 0.00381021 | 0.00450814 | 8 | blanket.deg_blkt_inboard_poloidal_plasma; power.e_plant_net_electric_pulse_kwh; power.e_plant_net_electric_pulse_mj | 14 | 0 | 0.000553643 | 0.00381021 | 123 |
| A2/A1 | headline | 19 | 19 | — | 0 | 0 | 0 | — | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 0.00150362 | 0.00758377 | 123 |
| A2/A0 | beside | 19 | 19 | — | 0.000553643 | 0.00381021 | 0.00450814 | 8 | blanket.deg_blkt_inboard_poloidal_plasma; power.e_plant_net_electric_pulse_kwh; power.e_plant_net_electric_pulse_mj | 14 | 0 | 0.00312704 | 0.00758377 | 123 |

<sub>`fixed-point distance — low_aspect_ratio_DEMO — campaign_stencil_forward`</sub>

**Table F.95.** *units: dimensionless — the largest scaled difference between two arms' exit coupling states at the same entry, in the units τ = 1e-06 is stated in.  A row is one pair of arms: each rung of the evaluation phase's ladder and, marked headline, the partitioned arm against A0; A2/A0 beside on a pulsed configuration.  A column is the pairs the two arms share (by seeds), how many were compared and why the rest were not, the restricted distance's median, p90 and worst pair, the components the maximum sat on, the pairs with any restricted component at or above τ, the pairs where a discrete component differs or a constant moved, and the whole-state distance beside.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 50 pair(s) of st_regression.  Construction (re-derived here from the coupling-state artifact and the exit-state files, importing no line of the predicate): max_i |y_arm,i − y_base,i| / s_i over the continuous components not written by the once-per-run deferred nodes, s_i the committed scale; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  Reported, not accepted on: no acceptance rule was pre-declared for this quantity (added by task A76 (fixed-point-distance)). n = 50 (evaluation-phase pairs of st_regression over the ladder's rungs).*

| pair | role | n | n_compared | not_compared | restricted_median | restricted_p90 | restricted_max | worst_pair | argmax | n_pairs_above_tau | n_pairs_unclean | whole_median | whole_p90 | n_excluded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A0/AR | rung | 25 | 25 | — | 1.53939e-07 | 2.79264e-07 | 5.93831e-07 | 21 | blanket.deg_blkt_inboard_poloidal_plasma; superconducting_tfcoil.a_tf_plasma_case | 0 | 0 | 1.53939e-07 | 2.79264e-07 | 123 |
| A2/A0 | headline | 25 | 25 | — | 1.22663e-11 | 4.62003e-11 | 6.56516e-11 | 22 | heat_transport.tlvpmw | 0 | 0 | 0.257542 | 0.337422 | 123 |

<sub>`fixed-point distance — st_regression — campaign_displaced`</sub>

**Table F.96.** *units: dimensionless — the largest scaled difference between two arms' exit coupling states at the same entry, in the units τ = 1e-06 is stated in.  A row is one pair of arms: each rung of the evaluation phase's ladder and, marked headline, the partitioned arm against A0; A2/A0 beside on a pulsed configuration.  A column is the pairs the two arms share (by columns), how many were compared and why the rest were not, the restricted distance's median, p90 and worst pair, the components the maximum sat on, the pairs with any restricted component at or above τ, the pairs where a discrete component differs or a constant moved, and the whole-state distance beside.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 28 pair(s) of st_regression.  Construction (re-derived here from the coupling-state artifact and the exit-state files, importing no line of the predicate): max_i |y_arm,i − y_base,i| / s_i over the continuous components not written by the once-per-run deferred nodes, s_i the committed scale; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  Reported, not accepted on: no acceptance rule was pre-declared for this quantity (added by task A76 (fixed-point-distance)). n = 28 (evaluation-phase pairs of st_regression over the ladder's rungs).*

| pair | role | n | n_compared | not_compared | restricted_median | restricted_p90 | restricted_max | worst_pair | argmax | n_pairs_above_tau | n_pairs_unclean | whole_median | whole_p90 | n_excluded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A0/AR | rung | 14 | 14 | — | 0 | 4.27221e-08 | 6.40749e-08 | 11 | blanket.deg_blkt_inboard_poloidal_plasma; fwbs.p_cp_shield_nuclear_heat_mw; superconducting_tfcoil.a_tf_plasma_case | 0 | 0 | 0 | 4.27221e-08 | 123 |
| A2/A0 | headline | 14 | 14 | — | 5.33877e-11 | 6.09871e-11 | 7.31847e-11 | 6 | blanket.deg_blkt_inboard_poloidal_plasma; current_drive.radius_beam_tangency_max; fwbs.p_cp_shield_nuclear_heat_mw; heat_transport.tlvpmw | 0 | 0 | 0.00175996 | 0.00598788 | 123 |

<sub>`fixed-point distance — st_regression — campaign_stencil_backward`</sub>

**Table F.97.** *units: dimensionless — the largest scaled difference between two arms' exit coupling states at the same entry, in the units τ = 1e-06 is stated in.  A row is one pair of arms: each rung of the evaluation phase's ladder and, marked headline, the partitioned arm against A0; A2/A0 beside on a pulsed configuration.  A column is the pairs the two arms share (by columns), how many were compared and why the rest were not, the restricted distance's median, p90 and worst pair, the components the maximum sat on, the pairs with any restricted component at or above τ, the pairs where a discrete component differs or a constant moved, and the whole-state distance beside.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 28 pair(s) of st_regression.  Construction (re-derived here from the coupling-state artifact and the exit-state files, importing no line of the predicate): max_i |y_arm,i − y_base,i| / s_i over the continuous components not written by the once-per-run deferred nodes, s_i the committed scale; median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n).  Reported, not accepted on: no acceptance rule was pre-declared for this quantity (added by task A76 (fixed-point-distance)). n = 28 (evaluation-phase pairs of st_regression over the ladder's rungs).*

| pair | role | n | n_compared | not_compared | restricted_median | restricted_p90 | restricted_max | worst_pair | argmax | n_pairs_above_tau | n_pairs_unclean | whole_median | whole_p90 | n_excluded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A0/AR | rung | 14 | 14 | — | 0 | 3.91977e-07 | 4.70387e-07 | 6 | blanket.deg_blkt_inboard_poloidal_plasma; fwbs.p_cp_shield_nuclear_heat_mw; superconducting_tfcoil.a_tf_plasma_case | 0 | 0 | 0 | 3.91977e-07 | 123 |
| A2/A0 | headline | 14 | 14 | — | 1.11615e-10 | 1.15411e-10 | 1.15547e-10 | 0 | fwbs.p_cp_shield_nuclear_heat_mw; heat_transport.tlvpmw; superconducting_tfcoil.a_tf_plasma_case | 0 | 0 | 0.00176096 | 0.00596933 | 123 |

<sub>`fixed-point distance — st_regression — campaign_stencil_forward`</sub>

**Table F.98.** *units: dimensionless ratios of counts.  A row is one arm against the flat control over the seed set.  A column is one of check 2's two iteration constructions, its sum ratio, or the evaluation-count ratio beside them.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 22 seed(s) on which every arm of large_tokamak_nof reached an accepted optimum.  Construction: iterations summed over attempts[] is the declared acceptance statistic, nearest-rank upper-middle median against 1.05; the final attempt's count is the previous revision's construction, published beside.  Both are read from attempts[], so a disagreement between them is a disagreement about that list.  The sum ratio is beside every median because the two can point in opposite directions.  ε is the evaluation count summed over attempts[].sweeps_per_eval.n_evaluations (issue I-26), with the seeds on which it is exactly 1; the sweep ratio (n_model_calls) is its own column; the B1 → B2 row is the plan's step reported beside. n = 22 (seeds on which every arm of large_tokamak_nof converged).*

| pair | n | summed_median | summed_sum_ratio | acceptance | final_median | final_sum_ratio | evaluations_median | evaluations_equal | sweeps_median | attempts | constructions_disagree |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 → BR (beside) | 22 | 1 | 1 | beside | 1 | 1 | 1 | 22 | 0.979456 | 0:1/1, 1:1/1, 2:1/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 10:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 17:1/1, 18:1/1, 19:1/1, 22:1/1, 23:1/1, 24:1/1 | 0 |
| B0 → B1 | 22 | 1 | 0.994186 | PASS | 1 | 0.994186 | 1.04762 | 0 | 1.01391 | 0:1/1, 1:1/1, 2:1/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 10:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 17:1/1, 18:1/1, 19:1/1, 22:1/1, 23:1/1, 24:1/1 | 0 |
| B0 → B2 | 22 | 1 | 0.994186 | PASS | 1 | 0.994186 | 1.04762 | 0 | 2.65239 | 0:1/1, 1:1/1, 2:1/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 10:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 17:1/1, 18:1/1, 19:1/1, 22:1/1, 23:1/1, 24:1/1 | 0 |
| B1 → B2 (beside) | 22 | 1 | 1 | beside | 1 | 1 | 1 | 22 | 2.61579 | 0:1/1, 1:1/1, 2:1/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 10:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 17:1/1, 18:1/1, 19:1/1, 22:1/1, 23:1/1, 24:1/1 | 0 |

<sub>`iteration multiplier (check 2) — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.99.** *units: dimensionless ratios of counts.  A row is one arm against the flat control over the seed set.  A column is one of check 2's two iteration constructions, its sum ratio, or the evaluation-count ratio beside them.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 11 seed(s) on which every arm of low_aspect_ratio_DEMO reached an accepted optimum.  Construction: iterations summed over attempts[] is the declared acceptance statistic, nearest-rank upper-middle median against 1.05; the final attempt's count is the previous revision's construction, published beside.  Both are read from attempts[], so a disagreement between them is a disagreement about that list.  The sum ratio is beside every median because the two can point in opposite directions.  ε is the evaluation count summed over attempts[].sweeps_per_eval.n_evaluations (issue I-26), with the seeds on which it is exactly 1; the sweep ratio (n_model_calls) is its own column; the B1 → B2 row is the plan's step reported beside. n = 11 (seeds on which every arm of low_aspect_ratio_DEMO converged).*

| pair | n | summed_median | summed_sum_ratio | acceptance | final_median | final_sum_ratio | evaluations_median | evaluations_equal | sweeps_median | attempts | constructions_disagree |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 → BR (beside) | 11 | 1 | 1 | beside | 1 | 1 | 1 | 11 | 1.03515 | 0:1/1, 1:2/2, 5:1/1, 6:1/1, 9:1/1, 11:1/1, 12:1/1, 13:1/1, 15:1/1, 18:1/1, 19:1/1 | 1 |
| B0 → B1 | 11 | 0.8125 | 0.70122 | PASS | 0.833333 | 1.00877 | 0.846774 | 0 | 0.804589 | 0:1/1, 1:2/1, 5:1/1, 6:1/1, 9:1/1, 11:1/1, 12:1/1, 13:1/1, 15:1/1, 18:1/1, 19:1/1 | 1 |
| B0 → B2 | 11 | 0.8125 | 0.70122 | PASS | 0.833333 | 1.00877 | 0.846774 | 0 | 2.11691 | 0:1/1, 1:2/1, 5:1/1, 6:1/1, 9:1/1, 11:1/1, 12:1/1, 13:1/1, 15:1/1, 18:1/1, 19:1/1 | 1 |
| B1 → B2 (beside) | 11 | 1 | 1 | beside | 1 | 1 | 1 | 11 | 2.63353 | 0:1/1, 1:1/1, 5:1/1, 6:1/1, 9:1/1, 11:1/1, 12:1/1, 13:1/1, 15:1/1, 18:1/1, 19:1/1 | 0 |

<sub>`iteration multiplier (check 2) — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.100.** *units: dimensionless ratios of counts.  A row is one arm against the flat control over the seed set.  A column is one of check 2's two iteration constructions, its sum ratio, or the evaluation-count ratio beside them.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 22 seed(s) on which every arm of st_regression reached an accepted optimum.  Construction: iterations summed over attempts[] is the declared acceptance statistic, nearest-rank upper-middle median against 1.05; the final attempt's count is the previous revision's construction, published beside.  Both are read from attempts[], so a disagreement between them is a disagreement about that list.  The sum ratio is beside every median because the two can point in opposite directions.  ε is the evaluation count summed over attempts[].sweeps_per_eval.n_evaluations (issue I-26), with the seeds on which it is exactly 1; the sweep ratio (n_model_calls) is its own column; the B1 → B2 row is the plan's step reported beside. n = 22 (seeds on which every arm of st_regression converged).*

| pair | n | summed_median | summed_sum_ratio | acceptance | final_median | final_sum_ratio | evaluations_median | evaluations_equal | sweeps_median | attempts | constructions_disagree |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 → BR (beside) | 22 | 1 | 1.24051 | beside | 1 | 0.922053 | 1 | 15 | 0.990635 | 0:1/1, 1:1/1, 2:2/2, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 11:1/1, 12:1/2, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 18:1/1, 19:1/1, 20:1/1, 21:1/1, 22:1/1, 23:1/1, 24:1/3 | 3 |
| B0 → B2 | 22 | 1 | 0.952984 | PASS | 1 | 1.0019 | 1 | 14 | 2.77666 | 0:1/1, 1:1/1, 2:2/1, 3:1/1, 4:1/1, 6:1/1, 7:1/1, 8:1/1, 9:1/1, 11:1/1, 12:1/1, 13:1/1, 14:1/1, 15:1/1, 16:1/1, 18:1/1, 19:1/1, 20:1/1, 21:1/1, 22:1/1, 23:1/1, 24:1/1 | 1 |

<sub>`iteration multiplier (check 2) — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table F.101.** *units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 100 run(s) of large_tokamak_nof.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither. n = 100 (evaluation-phase runs of large_tokamak_nof).*

| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_p90 | argmax | whole_median | whole_p90 | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 25 | 25 | 2.62424e-08 | 1.542e-07 | blanket.deg_blkt_inboard_poloidal_plasma, heat_transport.tlvpmw, power.qac | 3.25488e-08 | 4.14213e-07 | 122 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 25 | 25 | 1.50054e-08 | 8.37157e-08 | blanket.deg_blkt_inboard_poloidal_plasma, heat_transport.tlvpmw, power.qac | 1.50054e-08 | 8.37157e-08 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 25 | 25 | 5.04239e-10 | 2.9629e-09 | blanket.deg_blkt_inboard_poloidal_plasma, power.qac | 6.25411e-10 | 7.95902e-09 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 25 | 25 | 2.88323e-10 | 1.60857e-09 | blanket.deg_blkt_inboard_poloidal_plasma, power.qac | 2.88323e-10 | 1.60857e-09 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 25 | 25 | 3.83344e-10 | 1.67131e-08 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.stress_z_cs_self_midplane_profile | 3.83344e-10 | 1.67131e-08 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A1 | mixed | 25 | 25 | 3.83344e-10 | 1.67131e-08 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.stress_z_cs_self_midplane_profile | 3.83344e-10 | 1.67131e-08 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A2 | frozen | 25 | 25 | 3.83344e-10 | 1.67131e-08 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.stress_z_cs_self_midplane_profile | 2.43528 | 9.85963 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A2 | mixed | 25 | 25 | 3.83344e-10 | 1.67131e-08 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.stress_z_cs_self_midplane_profile | 0.39768 | 0.616996 | 122 | after_single_evaluation | no snapshot recorded on this record |

<sub>`matched accuracy — large_tokamak_nof — campaign_displaced`</sub>

**Table F.102.** *units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; 1 run(s) of large_tokamak_nof.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither. n = 1 (evaluation-phase runs of large_tokamak_nof).*

| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_p90 | argmax | whole_median | whole_p90 | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | frozen | 1 | 1 | 8.09171e-09 | 8.09171e-09 | power.qac | 1.46505e-08 | 1.46505e-08 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 1 | 1 | 4.52872e-09 | 4.52872e-09 | power.qac | 4.52872e-09 | 4.52872e-09 | 122 | after_single_evaluation | no snapshot recorded on this record |

<sub>`matched accuracy — large_tokamak_nof — campaign_entry_references`</sub>

**Table F.103.** *units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 80 run(s) of large_tokamak_nof.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither. n = 80 (evaluation-phase runs of large_tokamak_nof).*

| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_p90 | argmax | whole_median | whole_p90 | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 20 | 20 | 5.33878e-15 | 1.72982e-10 | blanket.deg_blkt_inboard_poloidal_plasma, heat_transport.tlvpmw, power.qac | 5.33878e-15 | 1.72982e-10 | 122 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 20 | 20 | 2.98798e-15 | 1.72982e-10 | blanket.deg_blkt_inboard_poloidal_plasma, heat_transport.tlvpmw, power.qac | 2.98798e-15 | 1.72982e-10 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 20 | 20 | 0 | 5.33878e-15 | blanket.deg_blkt_inboard_poloidal_plasma, power.qac | 0 | 1.14372e-14 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 20 | 20 | 0 | 2.98798e-15 | blanket.deg_blkt_inboard_poloidal_plasma, power.qac | 0 | 2.98798e-15 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 20 | 20 | 0 | 8.30864e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top, pf_coil.stress_z_cs_self_midplane_profile | 0 | 8.30864e-16 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A1 | mixed | 20 | 20 | 0 | 8.30864e-16 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.bpf2, pf_coil.stress_z_cs_self_midplane_profile | 0 | 8.30864e-16 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A2 | frozen | 20 | 20 | 8.30864e-16 | 4.52263e-13 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.f_j_cs_start_end_flat_top, pf_coil.stress_z_cs_self_midplane_profile | 0.00201638 | 0.0697524 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A2 | mixed | 20 | 20 | 8.30864e-16 | 4.52263e-13 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.bpf2, pf_coil.stress_z_cs_self_midplane_profile | 0.00182634 | 0.0107935 | 122 | after_single_evaluation | no snapshot recorded on this record |

<sub>`matched accuracy — large_tokamak_nof — campaign_stencil_backward`</sub>

**Table F.104.** *units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 80 run(s) of large_tokamak_nof.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither. n = 80 (evaluation-phase runs of large_tokamak_nof).*

| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_p90 | argmax | whole_median | whole_p90 | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 20 | 20 | 2.97398e-12 | 1.86926e-08 | power.qac | 5.34367e-12 | 3.38483e-08 | 122 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 20 | 20 | 1.66446e-12 | 1.04618e-08 | power.qac | 1.66446e-12 | 1.04618e-08 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 20 | 20 | 2.97398e-12 | 3.59169e-10 | power.qac | 5.34367e-12 | 6.50359e-10 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 20 | 20 | 1.66446e-12 | 2.01018e-10 | power.qac | 1.66446e-12 | 2.01018e-10 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 20 | 20 | 4.52263e-13 | 2.78324e-09 | pf_coil.f_j_cs_start_end_flat_top, pf_coil.stress_z_cs_self_midplane_profile | 4.52263e-13 | 2.78324e-09 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A1 | mixed | 20 | 20 | 4.52263e-13 | 2.78324e-09 | pf_coil.f_j_cs_start_end_flat_top, pf_coil.stress_z_cs_self_midplane_profile | 4.52263e-13 | 2.78324e-09 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A2 | frozen | 20 | 20 | 2.36272e-11 | 2.78324e-09 | pf_coil.f_j_cs_start_end_flat_top, pf_coil.stress_z_cs_self_midplane_profile | 0.00201638 | 0.0711547 | 122 | after_single_evaluation | no snapshot recorded on this record |
| A2 | mixed | 20 | 20 | 2.36272e-11 | 2.78324e-09 | pf_coil.f_j_cs_start_end_flat_top, pf_coil.stress_z_cs_self_midplane_profile | 0.00182707 | 0.0107756 | 122 | after_single_evaluation | no snapshot recorded on this record |

<sub>`matched accuracy — large_tokamak_nof — campaign_stencil_forward`</sub>

**Table F.105.** *units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 100 run(s) of low_aspect_ratio_DEMO.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither. n = 100 (evaluation-phase runs of low_aspect_ratio_DEMO).*

| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_p90 | argmax | whole_median | whole_p90 | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 25 | 25 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 25 | 25 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 25 | 25 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 25 | 25 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 25 | 25 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | mixed | 25 | 25 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A2 | frozen | 25 | 25 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0.181599 | 0.287845 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A2 | mixed | 25 | 25 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0.168677 | 0.242 | 123 | after_single_evaluation | no snapshot recorded on this record |

<sub>`matched accuracy — low_aspect_ratio_DEMO — campaign_displaced`</sub>

**Table F.106.** *units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; 1 run(s) of low_aspect_ratio_DEMO.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither. n = 1 (evaluation-phase runs of low_aspect_ratio_DEMO).*

| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_p90 | argmax | whole_median | whole_p90 | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | frozen | 1 | 1 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 1 | 1 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |

<sub>`matched accuracy — low_aspect_ratio_DEMO — campaign_entry_references`</sub>

**Table F.107.** *units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 76 run(s) of low_aspect_ratio_DEMO.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither. n = 76 (evaluation-phase runs of low_aspect_ratio_DEMO).*

| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_p90 | argmax | whole_median | whole_p90 | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | mixed | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A2 | frozen | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.stress_z_cs_self_midplane_profile | 0.00150908 | 0.00837004 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A2 | mixed | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma, pf_coil.stress_z_cs_self_midplane_profile | 0.00146758 | 0.00837004 | 123 | after_single_evaluation | no snapshot recorded on this record |

<sub>`matched accuracy — low_aspect_ratio_DEMO — campaign_stencil_backward`</sub>

**Table F.108.** *units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 76 run(s) of low_aspect_ratio_DEMO.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither. n = 76 (evaluation-phase runs of low_aspect_ratio_DEMO).*

| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_p90 | argmax | whole_median | whole_p90 | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma, heat_transport.tlvpmw | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma, heat_transport.tlvpmw | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | frozen | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A1 | mixed | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0 | 0 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A2 | frozen | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0.00150362 | 0.00758377 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A2 | mixed | 19 | 19 | 0 | 0 | blanket.deg_blkt_inboard_poloidal_plasma | 0.00147063 | 0.00758377 | 123 | after_single_evaluation | no snapshot recorded on this record |

<sub>`matched accuracy — low_aspect_ratio_DEMO — campaign_stencil_forward`</sub>

**Table F.109.** *units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 75 run(s) of st_regression.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither. n = 75 (evaluation-phase runs of st_regression).*

| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_p90 | argmax | whole_median | whole_p90 | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 25 | 25 | 1.53939e-07 | 2.79264e-07 | superconducting_tfcoil.a_tf_plasma_case | 1.53939e-07 | 2.79264e-07 | 123 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 25 | 25 | 1.0743e-07 | 1.94891e-07 | superconducting_tfcoil.a_tf_plasma_case | 1.0743e-07 | 1.94891e-07 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 25 | 25 | 5.37197e-09 | 2.02343e-08 | superconducting_tfcoil.a_tf_plasma_case | 5.37197e-09 | 2.02343e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 25 | 25 | 3.74896e-09 | 1.4121e-08 | superconducting_tfcoil.a_tf_plasma_case | 3.74896e-09 | 1.4121e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A2 | frozen | 25 | 25 | 5.37197e-09 | 2.02343e-08 | superconducting_tfcoil.a_tf_plasma_case | 0.257542 | 0.337422 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A2 | mixed | 25 | 25 | 3.74896e-09 | 1.4121e-08 | superconducting_tfcoil.a_tf_plasma_case | 0.134306 | 0.181027 | 123 | after_single_evaluation | no snapshot recorded on this record |

<sub>`matched accuracy — st_regression — campaign_displaced`</sub>

**Table F.110.** *units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; 1 run(s) of st_regression.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither. n = 1 (evaluation-phase runs of st_regression).*

| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_p90 | argmax | whole_median | whole_p90 | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | frozen | 1 | 1 | 3.27554e-09 | 3.27554e-09 | superconducting_tfcoil.a_tf_plasma_case | 3.27554e-09 | 3.27554e-09 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 1 | 1 | 2.28591e-09 | 2.28591e-09 | superconducting_tfcoil.a_tf_plasma_case | 2.28591e-09 | 2.28591e-09 | 123 | after_single_evaluation | no snapshot recorded on this record |

<sub>`matched accuracy — st_regression — campaign_entry_references`</sub>

**Table F.111.** *units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 42 run(s) of st_regression.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither. n = 42 (evaluation-phase runs of st_regression).*

| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_p90 | argmax | whole_median | whole_p90 | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 14 | 14 | 6.45896e-14 | 4.27221e-08 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 6.45896e-14 | 4.27221e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 14 | 14 | 6.45896e-14 | 2.98301e-08 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 6.45896e-14 | 2.98301e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 14 | 14 | 0 | 2.67039e-08 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.radius_beam_tangency_max, superconducting_tfcoil.a_tf_plasma_case | 0 | 2.67039e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 14 | 14 | 0 | 1.8642e-08 | blanket.deg_blkt_inboard_poloidal_plasma, current_drive.radius_beam_tangency_max, superconducting_tfcoil.a_tf_plasma_case | 0 | 1.8642e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A2 | frozen | 14 | 14 | 1.55986e-11 | 2.67039e-08 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 0.00175996 | 0.00598788 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A2 | mixed | 14 | 14 | 5.91923e-12 | 1.8642e-08 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 0.00102212 | 0.00257926 | 123 | after_single_evaluation | no snapshot recorded on this record |

<sub>`matched accuracy — st_regression — campaign_stencil_backward`</sub>

**Table F.112.** *units: dimensionless — the largest scaled coupling-state residual found by one further full sweep past termination.  A row is one arm on one ruler.  A column is the restricted or whole-state maximum's median and p90 over that arm's finished runs, the component the restricted maximum sat on, and how many components the restriction removed.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 42 run(s) of st_regression.  Construction: median = nearest-rank upper-middle, p90 = nearest-rank ceil(0.9 n); the restricted maximum excludes the components the configuration's once-per-run deferred nodes write.  Audit position: after_single_evaluation — a residual taken at the entry to the output path and one taken after the run are different quantities.  The audit instrument's version is read from the record, never assumed: task A62 (exit-audit-restore) widens the snapshot under decision D25 and moves every value in these columns.  Both rulers or neither. n = 42 (evaluation-phase runs of st_regression).*

| arm | ruler | n | n_with_the_statistic | restricted_median | restricted_p90 | argmax | whole_median | whole_p90 | n_excluded | audit_position | instrument |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | frozen | 14 | 14 | 3.77932e-11 | 3.91977e-07 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 3.77932e-11 | 3.91977e-07 | 123 | after_single_evaluation | no snapshot recorded on this record |
| AR | mixed | 14 | 14 | 1.4342e-11 | 2.73462e-07 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 1.4342e-11 | 2.73462e-07 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | frozen | 14 | 14 | 3.77932e-11 | 2.13721e-08 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 3.77932e-11 | 2.13721e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A0 | mixed | 14 | 14 | 1.4342e-11 | 1.49073e-08 | current_drive.radius_beam_tangency_max, fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 1.4342e-11 | 1.49073e-08 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A2 | frozen | 14 | 14 | 1.11615e-10 | 2.13721e-08 | fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 0.00176096 | 0.00596933 | 123 | after_single_evaluation | no snapshot recorded on this record |
| A2 | mixed | 14 | 14 | 7.78935e-11 | 1.49073e-08 | fwbs.p_cp_shield_nuclear_heat_mw, superconducting_tfcoil.a_tf_plasma_case | 0.00102062 | 0.00256932 | 123 | after_single_evaluation | no snapshot recorded on this record |

<sub>`matched accuracy — st_regression — campaign_stencil_forward`</sub>

**Table F.113.** *recomputed: the measured evaluation's per-node census summed over the node map's groups (the once-per-run nodes apart), mean per arm over finished runs, and Σ A2 / Σ reference over the pairs both sides finished n = 275 (finished evaluation-phase runs of every configuration in this source).*

| configuration | block | n_nodes | nodes | AR | A0 | A1 | A2 | reference | ratio | n_pairs |
|---|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | M1 | 2 | physics, plasma_geom | 9.92 | 11.04 | 10.24 | 8 | A1 | 0.78125 | 25 |
| large_tokamak_nof | M2 | 3 | build, cicc_sctfcoil, pfcoil | 14.88 | 16.56 | 15.36 | 15.48 | A1 | 1.00781 | 25 |
| large_tokamak_nof | M3 | 12 | Plant: 12 nodes (the committed node map's members) | 59.52 | 66.24 | 61.44 | 36 | A1 | 0.585938 | 25 |
| large_tokamak_nof | PULSE | 1 | pulse | 4.96 | 5.52 | 5.12 | 1 | A1 | 0.195312 | 25 |
| large_tokamak_nof | once per run | 3 | costs, vacuum, water_use | 14.88 | 16.56 | 15.36 | 0 | A1 | 0 | 25 |
| large_tokamak_nof | TOTAL | 21 | all counted nodes | 104.16 | 115.92 | 107.52 | 60.48 | A1 | 0.5625 | 25 |
| low_aspect_ratio_DEMO | M1 | 2 | physics, plasma_geom | 10 | 10 | 9.84 | 8 | A1 | 0.813008 | 25 |
| low_aspect_ratio_DEMO | M2 | 3 | build, cicc_sctfcoil, pfcoil | 15 | 15 | 14.76 | 14.64 | A1 | 0.99187 | 25 |
| low_aspect_ratio_DEMO | M3 | 12 | Plant: 12 nodes (the committed node map's members) | 60 | 60 | 59.04 | 36 | A1 | 0.609756 | 25 |
| low_aspect_ratio_DEMO | PULSE | 1 | pulse | 5 | 5 | 4.92 | 1 | A1 | 0.203252 | 25 |
| low_aspect_ratio_DEMO | once per run | 3 | costs, vacuum, water_use | 15 | 15 | 14.76 | 0 | A1 | 0 | 25 |
| low_aspect_ratio_DEMO | TOTAL | 21 | all counted nodes | 105 | 105 | 103.32 | 59.64 | A1 | 0.577236 | 25 |
| st_regression | M1 | 2 | physics, plasma_geom | 9.84 | 11.68 | — | 8 | A0 | 0.684932 | 25 |
| st_regression | M2 | 3 | build, croco_sctfcoil, pfcoil | 14.76 | 17.52 | — | 17.52 | A0 | 1 | 25 |
| st_regression | M3 | 12 | Plant: 12 nodes (the committed node map's members) | 59.04 | 70.08 | — | 36 | A0 | 0.513699 | 25 |
| st_regression | once per run | 4 | costs, pulse, vacuum, water_use | 19.68 | 23.36 | — | 0 | A0 | 0 | 25 |
| st_regression | TOTAL | 21 | all counted nodes | 103.32 | 122.64 | — | 61.52 | A0 | 0.501631 | 25 |

<sub>`node calls per block — campaign_displaced`</sub>

**Table F.114.** *recomputed: the measured evaluation's per-node census summed over the node map's groups (the once-per-run nodes apart), mean per arm over finished runs, and Σ A2 / Σ reference over the pairs both sides finished n = 3 (finished evaluation-phase runs of every configuration in this source).*

| configuration | block | n_nodes | nodes | AR | A0 | A1 | A2 | reference | ratio | n_pairs |
|---|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | M1 | 2 | physics, plasma_geom | — | 12 | — | — | A0 | — | 0 |
| large_tokamak_nof | M2 | 3 | build, cicc_sctfcoil, pfcoil | — | 18 | — | — | A0 | — | 0 |
| large_tokamak_nof | M3 | 12 | Plant: 12 nodes (the committed node map's members) | — | 72 | — | — | A0 | — | 0 |
| large_tokamak_nof | PULSE | 1 | pulse | — | 6 | — | — | A0 | — | 0 |
| large_tokamak_nof | once per run | 3 | costs, vacuum, water_use | — | 18 | — | — | A0 | — | 0 |
| large_tokamak_nof | TOTAL | 21 | all counted nodes | — | 126 | — | — | A0 | — | 0 |
| low_aspect_ratio_DEMO | M1 | 2 | physics, plasma_geom | — | 10 | — | — | A0 | — | 0 |
| low_aspect_ratio_DEMO | M2 | 3 | build, cicc_sctfcoil, pfcoil | — | 15 | — | — | A0 | — | 0 |
| low_aspect_ratio_DEMO | M3 | 12 | Plant: 12 nodes (the committed node map's members) | — | 60 | — | — | A0 | — | 0 |
| low_aspect_ratio_DEMO | PULSE | 1 | pulse | — | 5 | — | — | A0 | — | 0 |
| low_aspect_ratio_DEMO | once per run | 3 | costs, vacuum, water_use | — | 15 | — | — | A0 | — | 0 |
| low_aspect_ratio_DEMO | TOTAL | 21 | all counted nodes | — | 105 | — | — | A0 | — | 0 |
| st_regression | M1 | 2 | physics, plasma_geom | — | 14 | — | — | A0 | — | 0 |
| st_regression | M2 | 3 | build, croco_sctfcoil, pfcoil | — | 21 | — | — | A0 | — | 0 |
| st_regression | M3 | 12 | Plant: 12 nodes (the committed node map's members) | — | 84 | — | — | A0 | — | 0 |
| st_regression | once per run | 4 | costs, pulse, vacuum, water_use | — | 28 | — | — | A0 | — | 0 |
| st_regression | TOTAL | 21 | all counted nodes | — | 147 | — | — | A0 | — | 0 |

<sub>`node calls per block — campaign_entry_references`</sub>

**Table F.115.** *recomputed: the measured evaluation's per-node census summed over the node map's groups (the once-per-run nodes apart), mean per arm over finished runs, and Σ A2 / Σ reference over the pairs both sides finished n = 198 (finished evaluation-phase runs of every configuration in this source).*

| configuration | block | n_nodes | nodes | AR | A0 | A1 | A2 | reference | ratio | n_pairs |
|---|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | M1 | 2 | physics, plasma_geom | 5.8 | 6.3 | 6 | 3.8 | A1 | 0.633333 | 20 |
| large_tokamak_nof | M2 | 3 | build, cicc_sctfcoil, pfcoil | 8.7 | 9.45 | 9 | 7.35 | A1 | 0.816667 | 20 |
| large_tokamak_nof | M3 | 12 | Plant: 12 nodes (the committed node map's members) | 34.8 | 37.8 | 36 | 28.2 | A1 | 0.783333 | 20 |
| large_tokamak_nof | PULSE | 1 | pulse | 2.9 | 3.15 | 3 | 1 | A1 | 0.333333 | 20 |
| large_tokamak_nof | once per run | 3 | costs, vacuum, water_use | 8.7 | 9.45 | 9 | 0 | A1 | 0 | 20 |
| large_tokamak_nof | TOTAL | 21 | all counted nodes | 60.9 | 66.15 | 63 | 40.35 | A1 | 0.640476 | 20 |
| low_aspect_ratio_DEMO | M1 | 2 | physics, plasma_geom | 6.42105 | 6.52632 | 6.10526 | 3.78947 | A1 | 0.62069 | 19 |
| low_aspect_ratio_DEMO | M2 | 3 | build, cicc_sctfcoil, pfcoil | 9.63158 | 9.78947 | 9.15789 | 7.26316 | A1 | 0.793103 | 19 |
| low_aspect_ratio_DEMO | M3 | 12 | Plant: 12 nodes (the committed node map's members) | 38.5263 | 39.1579 | 36.6316 | 30.3158 | A1 | 0.827586 | 19 |
| low_aspect_ratio_DEMO | PULSE | 1 | pulse | 3.21053 | 3.26316 | 3.05263 | 1 | A1 | 0.327586 | 19 |
| low_aspect_ratio_DEMO | once per run | 3 | costs, vacuum, water_use | 9.63158 | 9.78947 | 9.15789 | 0 | A1 | 0 | 19 |
| low_aspect_ratio_DEMO | TOTAL | 21 | all counted nodes | 67.4211 | 68.5263 | 64.1053 | 42.3684 | A1 | 0.66092 | 19 |
| st_regression | M1 | 2 | physics, plasma_geom | 6.28571 | 6.71429 | — | 4.42857 | A0 | 0.659574 | 14 |
| st_regression | M2 | 3 | build, croco_sctfcoil, pfcoil | 9.42857 | 10.0714 | — | 6.64286 | A0 | 0.659574 | 14 |
| st_regression | M3 | 12 | Plant: 12 nodes (the committed node map's members) | 37.7143 | 40.2857 | — | 28.2857 | A0 | 0.702128 | 14 |
| st_regression | once per run | 4 | costs, pulse, vacuum, water_use | 12.5714 | 13.4286 | — | 0 | A0 | 0 | 14 |
| st_regression | TOTAL | 21 | all counted nodes | 66 | 70.5 | — | 39.3571 | A0 | 0.558257 | 14 |

<sub>`node calls per block — campaign_stencil_backward`</sub>

**Table F.116.** *recomputed: the measured evaluation's per-node census summed over the node map's groups (the once-per-run nodes apart), mean per arm over finished runs, and Σ A2 / Σ reference over the pairs both sides finished n = 198 (finished evaluation-phase runs of every configuration in this source).*

| configuration | block | n_nodes | nodes | AR | A0 | A1 | A2 | reference | ratio | n_pairs |
|---|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | M1 | 2 | physics, plasma_geom | 5.9 | 6.3 | 6 | 3.8 | A1 | 0.633333 | 20 |
| large_tokamak_nof | M2 | 3 | build, cicc_sctfcoil, pfcoil | 8.85 | 9.45 | 9 | 7.35 | A1 | 0.816667 | 20 |
| large_tokamak_nof | M3 | 12 | Plant: 12 nodes (the committed node map's members) | 35.4 | 37.8 | 36 | 27 | A1 | 0.75 | 20 |
| large_tokamak_nof | PULSE | 1 | pulse | 2.95 | 3.15 | 3 | 1 | A1 | 0.333333 | 20 |
| large_tokamak_nof | once per run | 3 | costs, vacuum, water_use | 8.85 | 9.45 | 9 | 0 | A1 | 0 | 20 |
| large_tokamak_nof | TOTAL | 21 | all counted nodes | 61.95 | 66.15 | 63 | 39.15 | A1 | 0.621429 | 20 |
| low_aspect_ratio_DEMO | M1 | 2 | physics, plasma_geom | 6.42105 | 6.31579 | 6 | 3.78947 | A1 | 0.631579 | 19 |
| low_aspect_ratio_DEMO | M2 | 3 | build, cicc_sctfcoil, pfcoil | 9.63158 | 9.47368 | 9 | 7.10526 | A1 | 0.789474 | 19 |
| low_aspect_ratio_DEMO | M3 | 12 | Plant: 12 nodes (the committed node map's members) | 38.5263 | 37.8947 | 36 | 28.4211 | A1 | 0.789474 | 19 |
| low_aspect_ratio_DEMO | PULSE | 1 | pulse | 3.21053 | 3.15789 | 3 | 1 | A1 | 0.333333 | 19 |
| low_aspect_ratio_DEMO | once per run | 3 | costs, vacuum, water_use | 9.63158 | 9.47368 | 9 | 0 | A1 | 0 | 19 |
| low_aspect_ratio_DEMO | TOTAL | 21 | all counted nodes | 67.4211 | 66.3158 | 63 | 40.3158 | A1 | 0.639933 | 19 |
| st_regression | M1 | 2 | physics, plasma_geom | 6 | 6.42857 | — | 4.42857 | A0 | 0.688889 | 14 |
| st_regression | M2 | 3 | build, croco_sctfcoil, pfcoil | 9 | 9.64286 | — | 6.21429 | A0 | 0.644444 | 14 |
| st_regression | M3 | 12 | Plant: 12 nodes (the committed node map's members) | 36 | 38.5714 | — | 28.2857 | A0 | 0.733333 | 14 |
| st_regression | once per run | 4 | costs, pulse, vacuum, water_use | 12 | 12.8571 | — | 0 | A0 | 0 | 14 |
| st_regression | TOTAL | 21 | all counted nodes | 63 | 67.5 | — | 38.9286 | A0 | 0.57672 | 14 |

<sub>`node calls per block — campaign_stencil_forward`</sub>

**Table F.117.** *recomputed: the whole run's per-node census summed over the node map's groups (the once-per-run nodes apart), per-run mean and [min, max] per arm over the seed set, B2/B0 pooled, per-run median with [min, max] and the count of runs above 1; the last row is the census total less the solve-phase calls summed over attempts n = 22 (seeds on which every arm of large_tokamak_nof converged).*

| module | n_nodes | nodes | BR_mean | BR_bracket | B0_mean | B0_bracket | B1_mean | B1_bracket | B2_mean | B2_bracket | pooled | median | bracket | n_above_one | n_pairs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 | 2 | physics, plasma_geom | 3956.45 | [3516, 4560] | 4055.09 | [3586, 4792] | 4082.18 | [3642, 4762] | 2778.27 | [2482, 3248] | 0.685132 | 0.690935 | [0.598, 0.799] | 0 | 22 |
| M2 | 3 | build, cicc_sctfcoil, pfcoil | 5934.68 | [5274, 6840] | 6082.64 | [5379, 7188] | 6123.27 | [5463, 7143] | 5286.55 | [4719, 6174] | 0.869121 | 0.876461 | [0.761, 1.013] | 1 | 22 |
| M3 | 12 | Plant: 12 nodes (the committed node map's members) | 23738.7 | [21096, 27360] | 24330.5 | [21516, 28752] | 24493.1 | [21852, 28572] | 18499.6 | [16536, 21660] | 0.760346 | 0.767004 | [0.657, 0.887] | 0 | 22 |
| PULSE | 1 | pulse | 1978.23 | [1758, 2280] | 2027.55 | [1793, 2396] | 2041.09 | [1821, 2381] | 641 | [573, 749] | 0.316146 | 0.318862 | [0.276, 0.369] | 0 | 22 |
| once per run | 3 | costs, vacuum, water_use | 5934.68 | [5274, 6840] | 6082.64 | [5379, 7188] | 6123.27 | [5463, 7143] | 6 | [6, 6] | 0.000986414 | 0.000965717 | [0.001, 0.001] | 0 | 22 |
| all counted nodes | 21 | every node above | 41542.8 | [36918, 47880] | 42578.5 | [37653, 50316] | 42862.9 | [38241, 50001] | 27211.5 | [24320, 31837] | 0.63909 | 0.644711 | [0.555, 0.746] | 0 | 22 |
| of which outside the solve phase | — | the output path and the exit audit's sweep | 63 | [63, 63] | 63 | [63, 63] | 21 | [21, 21] | 24 | [24, 24] | 0.380952 | 0.380952 | [0.381, 0.381] | 0 | 22 |

<sub>`node calls per module — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.118.** *recomputed: the whole run's per-node census summed over the node map's groups (the once-per-run nodes apart), per-run mean and [min, max] per arm over the seed set, B2/B0 pooled, per-run median with [min, max] and the count of runs above 1; the last row is the census total less the solve-phase calls summed over attempts n = 11 (seeds on which every arm of low_aspect_ratio_DEMO converged).*

| module | n_nodes | nodes | BR_mean | BR_bracket | B0_mean | B0_bracket | B1_mean | B1_bracket | B2_mean | B2_bracket | pooled | median | bracket | n_above_one | n_pairs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 | 2 | physics, plasma_geom | 16191.1 | [5808, 63740] | 15720 | [5620, 62432] | 10873.8 | [5070, 34344] | 7342.36 | [3418, 23190] | 0.467071 | 0.542029 | [0.084, 4.126] | 2 | 11 |
| M2 | 3 | build, cicc_sctfcoil, pfcoil | 24286.6 | [8712, 95610] | 23580 | [8430, 93648] | 16310.7 | [7605, 51516] | 13982.5 | [6525, 44169] | 0.592979 | 0.68913 | [0.106, 5.240] | 2 | 11 |
| M3 | 12 | Plant: 12 nodes (the committed node map's members) | 97146.5 | [34848, 382440] | 94320 | [33720, 374592] | 65242.9 | [30420, 206064] | 51290.2 | [23904, 161856] | 0.543789 | 0.632367 | [0.097, 4.800] | 2 | 11 |
| PULSE | 1 | pulse | 8095.55 | [2904, 31870] | 7860 | [2810, 31216] | 5436.91 | [2535, 17172] | 1715.36 | [799, 5419] | 0.21824 | 0.253865 | [0.039, 1.928] | 2 | 11 |
| once per run | 3 | costs, vacuum, water_use | 24286.6 | [8712, 95610] | 23580 | [8430, 93648] | 16310.7 | [7605, 51516] | 6 | [6, 6] | 0.000254453 | 0.000483092 | [0.000, 0.001] | 0 | 11 |
| all counted nodes | 21 | every node above | 170006 | [60984, 669270] | 165060 | [59010, 655536] | 114175 | [53235, 360612] | 74336.4 | [34652, 234640] | 0.45036 | 0.523579 | [0.081, 3.976] | 2 | 11 |
| of which outside the solve phase | — | the output path and the exit audit's sweep | 63 | [63, 63] | 63 | [63, 63] | 21 | [21, 21] | 24 | [24, 24] | 0.380952 | 0.380952 | [0.381, 0.381] | 0 | 11 |

<sub>`node calls per module — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.119.** *recomputed: the whole run's per-node census summed over the node map's groups (the once-per-run nodes apart), per-run mean and [min, max] per arm over the seed set, B2/B0 pooled, per-run median with [min, max] and the count of runs above 1; the last row is the census total less the solve-phase calls summed over attempts n = 22 (seeds on which every arm of st_regression converged).*

| module | n_nodes | nodes | BR_mean | BR_bracket | B0_mean | B0_bracket | B1_mean | B1_bracket | B2_mean | B2_bracket | pooled | median | bracket | n_above_one | n_pairs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 | 2 | physics, plasma_geom | 12088.6 | [3780, 79904] | 10101.9 | [3790, 28168] | — | — | 6502.18 | [2726, 19270] | 0.643659 | 0.71561 | [0.165, 0.894] | 0 | 22 |
| M2 | 3 | build, croco_sctfcoil, pfcoil | 18133 | [5670, 119856] | 15152.9 | [5685, 42252] | — | — | 10121.6 | [4104, 30957] | 0.667966 | 0.723532 | [0.169, 0.955] | 0 | 22 |
| M3 | 12 | Plant: 12 nodes (the committed node map's members) | 72531.8 | [22680, 479424] | 60611.5 | [22740, 169008] | — | — | 39900.5 | [16668, 119148] | 0.6583 | 0.731429 | [0.168, 0.929] | 0 | 22 |
| once per run | 4 | costs, pulse, vacuum, water_use | 24177.3 | [7560, 159808] | 20203.8 | [7580, 56336] | — | — | 8 | [8, 8] | 0.000395965 | 0.00070373 | [0.000, 0.001] | 0 | 22 |
| all counted nodes | 21 | every node above | 126931 | [39690, 838992] | 106070 | [39795, 295764] | — | — | 56532.3 | [23509, 169383] | 0.532972 | 0.590753 | [0.136, 0.753] | 0 | 22 |
| of which outside the solve phase | — | the output path and the exit audit's sweep | 63 | [63, 63] | 63 | [63, 63] | — | — | 25 | [25, 25] | 0.396825 | 0.396825 | [0.397, 0.397] | 0 | 22 |

<sub>`node calls per module — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table F.120.** *units: the node-call ratio is dimensionless; the burn-time residual is in seconds and relative to the burn time.  A row is this configuration's rung.  A column is the cost of taking the burn time out of the flat loop, or the inconsistency the constant leaves behind.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 25 flat-control and 25 pinned run(s) of large_tokamak_nof.  Construction: the ratio triple on node calls of the single evaluation; the residual is the lifted component's own inconsistency at exit, |value|, median nearest-rank upper-middle.  Neither column is a claim about the partition: this rung moves one thing only. n = 50 (A0 and A1 runs of large_tokamak_nof).*

| n | paired_seeds | pooled | median | worse | residual_s_median | residual_s_bracket | relative_median |
|---|---|---|---|---|---|---|---|
| 25 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.927536 | 1 | 0 | 154.633 | [12.8111, 406.884] | 0.062979 |

<sub>`ownership rung A0 → A1 — large_tokamak_nof — campaign_displaced`</sub>

**Table F.121.** *units: the node-call ratio is dimensionless; the burn-time residual is in seconds and relative to the burn time.  A row is this configuration's rung.  A column is the cost of taking the burn time out of the flat loop, or the inconsistency the constant leaves behind.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 20 flat-control and 20 pinned run(s) of large_tokamak_nof.  Construction: the ratio triple on node calls of the single evaluation; the residual is the lifted component's own inconsistency at exit, |value|, median nearest-rank upper-middle.  Neither column is a claim about the partition: this rung moves one thing only. n = 40 (A0 and A1 runs of large_tokamak_nof).*

| n | paired_seeds | pooled | median | worse | residual_s_median | residual_s_bracket | relative_median |
|---|---|---|---|---|---|---|---|
| 20 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 0.952381 | 1 | 0 | 1.17471 | [2.61418e-07, 13.1158] | 0.000457418 |

<sub>`ownership rung A0 → A1 — large_tokamak_nof — campaign_stencil_backward`</sub>

**Table F.122.** *units: the node-call ratio is dimensionless; the burn-time residual is in seconds and relative to the burn time.  A row is this configuration's rung.  A column is the cost of taking the burn time out of the flat loop, or the inconsistency the constant leaves behind.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 20 flat-control and 20 pinned run(s) of large_tokamak_nof.  Construction: the ratio triple on node calls of the single evaluation; the residual is the lifted component's own inconsistency at exit, |value|, median nearest-rank upper-middle.  Neither column is a claim about the partition: this rung moves one thing only. n = 40 (A0 and A1 runs of large_tokamak_nof).*

| n | paired_seeds | pooled | median | worse | residual_s_median | residual_s_bracket | relative_median |
|---|---|---|---|---|---|---|---|
| 20 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 0.952381 | 1 | 0 | 1.17254 | [2.61319e-07, 13.1365] | 0.000456574 |

<sub>`ownership rung A0 → A1 — large_tokamak_nof — campaign_stencil_forward`</sub>

**Table F.123.** *units: the node-call ratio is dimensionless; the burn-time residual is in seconds and relative to the burn time.  A row is this configuration's rung.  A column is the cost of taking the burn time out of the flat loop, or the inconsistency the constant leaves behind.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; 25 flat-control and 25 pinned run(s) of low_aspect_ratio_DEMO.  Construction: the ratio triple on node calls of the single evaluation; the residual is the lifted component's own inconsistency at exit, |value|, median nearest-rank upper-middle.  Neither column is a claim about the partition: this rung moves one thing only. n = 50 (A0 and A1 runs of low_aspect_ratio_DEMO).*

| n | paired_seeds | pooled | median | worse | residual_s_median | residual_s_bracket | relative_median |
|---|---|---|---|---|---|---|---|
| 25 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 | 0.984 | 1 | 0 | 525.842 | [1.64882, 1436.26] | 0.0527537 |

<sub>`ownership rung A0 → A1 — low_aspect_ratio_DEMO — campaign_displaced`</sub>

**Table F.124.** *units: the node-call ratio is dimensionless; the burn-time residual is in seconds and relative to the burn time.  A row is this configuration's rung.  A column is the cost of taking the burn time out of the flat loop, or the inconsistency the constant leaves behind.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; 19 flat-control and 19 pinned run(s) of low_aspect_ratio_DEMO.  Construction: the ratio triple on node calls of the single evaluation; the residual is the lifted component's own inconsistency at exit, |value|, median nearest-rank upper-middle.  Neither column is a claim about the partition: this rung moves one thing only. n = 38 (A0 and A1 runs of low_aspect_ratio_DEMO).*

| n | paired_seeds | pooled | median | worse | residual_s_median | residual_s_bracket | relative_median |
|---|---|---|---|---|---|---|---|
| 19 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 0.935484 | 1 | 0 | 4.18366 | [0, 34.1746] | 0.000402376 |

<sub>`ownership rung A0 → A1 — low_aspect_ratio_DEMO — campaign_stencil_backward`</sub>

**Table F.125.** *units: the node-call ratio is dimensionless; the burn-time residual is in seconds and relative to the burn time.  A row is this configuration's rung.  A column is the cost of taking the burn time out of the flat loop, or the inconsistency the constant leaves behind.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; 19 flat-control and 19 pinned run(s) of low_aspect_ratio_DEMO.  Construction: the ratio triple on node calls of the single evaluation; the residual is the lifted component's own inconsistency at exit, |value|, median nearest-rank upper-middle.  Neither column is a claim about the partition: this rung moves one thing only. n = 38 (A0 and A1 runs of low_aspect_ratio_DEMO).*

| n | paired_seeds | pooled | median | worse | residual_s_median | residual_s_bracket | relative_median |
|---|---|---|---|---|---|---|---|
| 19 | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 0.95 | 1 | 0 | 4.17586 | [0, 34.2015] | 0.000401626 |

<sub>`ownership rung A0 → A1 — low_aspect_ratio_DEMO — campaign_stencil_forward`</sub>

**Table F.126.** *units: outcome labels (text) and counts of arms.  A row is one seed offered to every arm of the group.  A column is each arm's outcome at that seed, how many arms accepted, whether the seed is in the seed set, and which arms lost it while another accepted.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the arms here are BR · B0 · B1 · B2 at seeds 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24.  Construction: the per-seed part of the per-arm success table, same labels. n = 25 (distinct seeds run on large_tokamak_nof).*

| seed | BR | B0 | B1 | B2 | n_accepted | in_seed_set | lost_by |
|---|---|---|---|---|---|---|---|
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

<sub>`per-arm success by seed — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.127.** *units: outcome labels (text) and counts of arms.  A row is one seed offered to every arm of the group.  A column is each arm's outcome at that seed, how many arms accepted, whether the seed is in the seed set, and which arms lost it while another accepted.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the arms here are BR · B0 · B1 · B2 at seeds 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24.  Construction: the per-seed part of the per-arm success table, same labels. n = 25 (distinct seeds run on low_aspect_ratio_DEMO).*

| seed | BR | B0 | B1 | B2 | n_accepted | in_seed_set | lost_by |
|---|---|---|---|---|---|---|---|
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

<sub>`per-arm success by seed — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.128.** *units: outcome labels (text) and counts of arms.  A row is one seed offered to every arm of the group.  A column is each arm's outcome at that seed, how many arms accepted, whether the seed is in the seed set, and which arms lost it while another accepted.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the arms here are BR · B0 · B2 at seeds 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24.  Construction: the per-seed part of the per-arm success table, same labels. n = 25 (distinct seeds run on st_regression).*

| seed | BR | B0 | B2 | n_accepted | in_seed_set | lost_by |
|---|---|---|---|---|---|---|
| 0 | accepted | accepted | accepted | 3 | yes | — |
| 1 | accepted | accepted | accepted | 3 | yes | — |
| 2 | accepted | accepted | accepted | 3 | yes | — |
| 3 | accepted | accepted | accepted | 3 | yes | — |
| 4 | accepted | accepted | accepted | 3 | yes | — |
| 5 | accepted | accepted | finished, ifail = 5 | 2 | no | B2 |
| 6 | accepted | accepted | accepted | 3 | yes | — |
| 7 | accepted | accepted | accepted | 3 | yes | — |
| 8 | accepted | accepted | accepted | 3 | yes | — |
| 9 | accepted | accepted | accepted | 3 | yes | — |
| 10 | accepted | finished, ifail = 5 | accepted | 2 | no | B0 |
| 11 | accepted | accepted | accepted | 3 | yes | — |
| 12 | accepted | accepted | accepted | 3 | yes | — |
| 13 | accepted | accepted | accepted | 3 | yes | — |
| 14 | accepted | accepted | accepted | 3 | yes | — |
| 15 | accepted | accepted | accepted | 3 | yes | — |
| 16 | accepted | accepted | accepted | 3 | yes | — |
| 17 | finished, ifail = 5 | finished, ifail = 5 | finished, ifail = 5 | 0 | no | — |
| 18 | accepted | accepted | accepted | 3 | yes | — |
| 19 | accepted | accepted | accepted | 3 | yes | — |
| 20 | accepted | accepted | accepted | 3 | yes | — |
| 21 | accepted | accepted | accepted | 3 | yes | — |
| 22 | accepted | accepted | accepted | 3 | yes | — |
| 23 | accepted | accepted | accepted | 3 | yes | — |
| 24 | accepted | accepted | accepted | 3 | yes | — |

<sub>`per-arm success by seed — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table F.129.** *units: counts of starts.  A row is one optimisation arm on this configuration.  A column is the starts offered, the accepted optima, every other start by its outcome, the starts lost that another arm accepted, and the seed set beside.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the arms here are BR · B0 · B1 · B2 at seeds 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24.  Construction: accepted is status ok AND the output file's ifail == 1; a finished start with another exit code carries it; a crashed start is PROCESS's own exception, named from the traceback, or the coupling-state loop's sweep cap (ModuleSolveFailure) by the harness's failure class; a start is lost when this arm did not accept and another did.  Reported, not accepted on (D29). n = 25 (starts offered per arm on large_tokamak_nof).*

| arm | offered | accepted | crashed (RuntimeError) | lost_another_arm_accepted | seed_set | seeds_not_accepted | lost_seeds |
|---|---|---|---|---|---|---|---|
| BR | 25 | 22 | 3 | 0 | 22 | crashed (RuntimeError): 5, 20, 21 | — |
| B0 | 25 | 22 | 3 | 0 | 22 | crashed (RuntimeError): 5, 20, 21 | — |
| B1 | 25 | 22 | 3 | 0 | 22 | crashed (RuntimeError): 5, 20, 21 | — |
| B2 | 25 | 22 | 3 | 0 | 22 | crashed (RuntimeError): 5, 20, 21 | — |

<sub>`per-arm success — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.130.** *units: counts of starts.  A row is one optimisation arm on this configuration.  A column is the starts offered, the accepted optima, every other start by its outcome, the starts lost that another arm accepted, and the seed set beside.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the arms here are BR · B0 · B1 · B2 at seeds 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24.  Construction: accepted is status ok AND the output file's ifail == 1; a finished start with another exit code carries it; a crashed start is PROCESS's own exception, named from the traceback, or the coupling-state loop's sweep cap (ModuleSolveFailure) by the harness's failure class; a start is lost when this arm did not accept and another did.  Reported, not accepted on (D29). n = 25 (starts offered per arm on low_aspect_ratio_DEMO).*

| arm | offered | accepted | finished, ifail = 5 | crashed (RuntimeError) | coupling-loop cap (ModuleSolveFailure) | lost_another_arm_accepted | seed_set | seeds_not_accepted | lost_seeds |
|---|---|---|---|---|---|---|---|---|---|
| BR | 25 | 12 | 11 | 2 | 0 | 0 | 11 | finished, ifail = 5: 2, 4, 7, 8, 14, 16, 17, 20, 22, 23, 24; crashed (RuntimeError): 3, 21 | — |
| B0 | 25 | 12 | 9 | 2 | 2 | 0 | 11 | finished, ifail = 5: 2, 7, 8, 14, 16, 17, 20, 23, 24; crashed (RuntimeError): 3, 21; coupling-loop cap (ModuleSolveFailure): 4, 22 | — |
| B1 | 25 | 11 | 9 | 2 | 3 | 1 | 11 | finished, ifail = 5: 2, 7, 8, 14, 16, 17, 20, 23, 24; crashed (RuntimeError): 3, 21; coupling-loop cap (ModuleSolveFailure): 4, 10, 22 | 10 |
| B2 | 25 | 11 | 9 | 2 | 3 | 1 | 11 | finished, ifail = 5: 2, 7, 8, 14, 16, 17, 20, 23, 24; crashed (RuntimeError): 3, 21; coupling-loop cap (ModuleSolveFailure): 4, 10, 22 | 10 |

<sub>`per-arm success — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.131.** *units: counts of starts.  A row is one optimisation arm on this configuration.  A column is the starts offered, the accepted optima, every other start by its outcome, the starts lost that another arm accepted, and the seed set beside.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the arms here are BR · B0 · B2 at seeds 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24.  Construction: accepted is status ok AND the output file's ifail == 1; a finished start with another exit code carries it; a crashed start is PROCESS's own exception, named from the traceback, or the coupling-state loop's sweep cap (ModuleSolveFailure) by the harness's failure class; a start is lost when this arm did not accept and another did.  Reported, not accepted on (D29). n = 25 (starts offered per arm on st_regression).*

| arm | offered | accepted | finished, ifail = 5 | lost_another_arm_accepted | seed_set | seeds_not_accepted | lost_seeds |
|---|---|---|---|---|---|---|---|
| BR | 25 | 24 | 1 | 0 | 22 | finished, ifail = 5: 17 | — |
| B0 | 25 | 23 | 2 | 1 | 22 | finished, ifail = 5: 10, 17 | 10 |
| B2 | 25 | 23 | 2 | 1 | 22 | finished, ifail = 5: 5, 17 | 5 |

<sub>`per-arm success — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table F.132.** *units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; the finished evaluation-phase gate runs of large_tokamak_nof.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 100 (finished evaluation-phase runs of large_tokamak_nof).*

| arm | seed | stops_on | dispatch_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 1 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 2 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 3 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 4 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 5 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 6 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 7 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 8 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 9 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 10 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 11 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 12 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 13 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 14 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 15 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 16 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27 | 0 |
| AR | 17 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 18 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 19 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 20 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 21 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 22 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 23 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 24 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| AR | 25 | upstream | 5 | 0 | 0 | — | — | 4 | 108 | 27 | 0 |
| A0 | 1 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 2 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 3 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 4 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 5 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 6 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 7 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 8 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 9 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 10 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 11 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 12 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 13 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 14 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 15 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 16 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 17 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 18 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 19 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 20 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 21 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 22 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 23 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 24 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 25 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 1 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 2 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 3 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 4 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 5 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 6 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 7 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 8 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 9 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 10 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 11 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 12 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 13 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 14 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 15 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 16 | coupling_state | 4 | 4 | 3360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 17 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 18 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 19 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 20 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 21 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 22 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 23 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 24 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 25 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A2 | 1 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 2 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 3 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 4 | coupling_state | 14 | 13 | 3135 | 241.154 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 5 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 6 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 7 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 8 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 9 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 10 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 11 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 12 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 13 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 14 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 15 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 16 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 17 | coupling_state | 14 | 13 | 3135 | 241.154 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 18 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 19 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 20 | coupling_state | 14 | 13 | 3135 | 241.154 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 21 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 22 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 23 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 24 | coupling_state | 13 | 12 | 2895 | 241.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 25 | coupling_state | 14 | 13 | 3135 | 241.154 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |

<sub>`per-sweep overhead — large_tokamak_nof — campaign_displaced`</sub>

**Table F.133.** *units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; the finished evaluation-phase gate runs of large_tokamak_nof.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 1 (finished evaluation-phase runs of large_tokamak_nof).*

| arm | seed | stops_on | dispatch_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 0 | coupling_state | 6 | 6 | 5040 | 840 | FLAT 840 | 0 | 0 | — | 0 |

<sub>`per-sweep overhead — large_tokamak_nof — campaign_entry_references`</sub>

**Table F.134.** *units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished optimisation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the finished optimisation-phase gate runs of large_tokamak_nof.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 88 (finished optimisation-phase runs of large_tokamak_nof).*

| arm | seed | stops_on | dispatch_sweeps | solve_sweeps | output_loop_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | 0 | upstream | 2029 | 2027 | 2 | 0 | 0 | — | — | 1397 | 37719 | 27 | 0 |
| BR | 1 | upstream | 2021 | 2019 | 2 | 0 | 0 | — | — | 1389 | 37503 | 27 | 0 |
| BR | 2 | upstream | 2279 | 2277 | 2 | 0 | 0 | — | — | 1563 | 42201 | 27 | 0 |
| BR | 3 | upstream | 1759 | 1757 | 2 | 0 | 0 | — | — | 1211 | 32697 | 27 | 0 |
| BR | 4 | upstream | 1761 | 1759 | 2 | 0 | 0 | — | — | 1213 | 32751 | 27 | 0 |
| BR | 6 | upstream | 2036 | 2034 | 2 | 0 | 0 | — | — | 1404 | 37908 | 27 | 0 |
| BR | 7 | upstream | 2032 | 2030 | 2 | 0 | 0 | — | — | 1400 | 37800 | 27 | 0 |
| BR | 8 | upstream | 2034 | 2032 | 2 | 0 | 0 | — | — | 1402 | 37854 | 27 | 0 |
| BR | 9 | upstream | 2026 | 2024 | 2 | 0 | 0 | — | — | 1394 | 37638 | 27 | 0 |
| BR | 10 | upstream | 1766 | 1764 | 2 | 0 | 0 | — | — | 1218 | 32886 | 27 | 0 |
| BR | 11 | upstream | 2005 | 2003 | 2 | 0 | 0 | — | — | 1373 | 37071 | 27 | 0 |
| BR | 12 | upstream | 2029 | 2027 | 2 | 0 | 0 | — | — | 1397 | 37719 | 27 | 0 |
| BR | 13 | upstream | 2021 | 2019 | 2 | 0 | 0 | — | — | 1389 | 37503 | 27 | 0 |
| BR | 14 | upstream | 2279 | 2277 | 2 | 0 | 0 | — | — | 1563 | 42201 | 27 | 0 |
| BR | 15 | upstream | 1758 | 1756 | 2 | 0 | 0 | — | — | 1210 | 32670 | 27 | 0 |
| BR | 16 | upstream | 1757 | 1755 | 2 | 0 | 0 | — | — | 1209 | 32643 | 27 | 0 |
| BR | 17 | upstream | 2027 | 2025 | 2 | 0 | 0 | — | — | 1395 | 37665 | 27 | 0 |
| BR | 18 | upstream | 2027 | 2025 | 2 | 0 | 0 | — | — | 1395 | 37665 | 27 | 0 |
| BR | 19 | upstream | 2030 | 2028 | 2 | 0 | 0 | — | — | 1398 | 37746 | 27 | 0 |
| BR | 22 | upstream | 1763 | 1761 | 2 | 0 | 0 | — | — | 1215 | 32805 | 27 | 0 |
| BR | 23 | upstream | 2032 | 2030 | 2 | 0 | 0 | — | — | 1400 | 37800 | 27 | 0 |
| BR | 24 | upstream | 2028 | 2026 | 2 | 0 | 0 | — | — | 1396 | 37692 | 27 | 0 |
| B0 | 0 | coupling_state | 2071 | 2069 | 2 | 2069 | 1737960 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 1 | coupling_state | 2073 | 2071 | 2 | 2071 | 1739640 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 2 | coupling_state | 2365 | 2363 | 2 | 2363 | 1984920 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 3 | coupling_state | 1797 | 1795 | 2 | 1795 | 1507800 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 4 | coupling_state | 1792 | 1790 | 2 | 1790 | 1503600 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 6 | coupling_state | 2071 | 2069 | 2 | 2069 | 1737960 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 7 | coupling_state | 2070 | 2068 | 2 | 2068 | 1737120 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 8 | coupling_state | 2070 | 2068 | 2 | 2068 | 1737120 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 9 | coupling_state | 2072 | 2070 | 2 | 2070 | 1738800 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 10 | coupling_state | 1792 | 1790 | 2 | 1790 | 1503600 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 11 | coupling_state | 2125 | 2123 | 2 | 2123 | 1783320 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 12 | coupling_state | 2070 | 2068 | 2 | 2068 | 1737120 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 13 | coupling_state | 2075 | 2073 | 2 | 2073 | 1741320 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 14 | coupling_state | 2395 | 2393 | 2 | 2393 | 2010120 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 15 | coupling_state | 1799 | 1797 | 2 | 1797 | 1509480 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 16 | coupling_state | 1796 | 1794 | 2 | 1794 | 1506960 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 17 | coupling_state | 2072 | 2070 | 2 | 2070 | 1738800 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 18 | coupling_state | 2065 | 2063 | 2 | 2063 | 1732920 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 19 | coupling_state | 2069 | 2067 | 2 | 2067 | 1736280 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 22 | coupling_state | 1800 | 1798 | 2 | 1798 | 1510320 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 23 | coupling_state | 2068 | 2066 | 2 | 2066 | 1735440 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B0 | 24 | coupling_state | 2077 | 2075 | 2 | 2075 | 1743000 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 0 | coupling_state | 2102 | 2102 | 0 | 2102 | 1765680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 1 | coupling_state | 2100 | 2100 | 0 | 2100 | 1764000 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 2 | coupling_state | 2102 | 2102 | 0 | 2102 | 1765680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 3 | coupling_state | 1824 | 1824 | 0 | 1824 | 1532160 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 4 | coupling_state | 1820 | 1820 | 0 | 1820 | 1528800 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 6 | coupling_state | 2097 | 2097 | 0 | 2097 | 1761480 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 7 | coupling_state | 2097 | 2097 | 0 | 2097 | 1761480 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 8 | coupling_state | 2101 | 2101 | 0 | 2101 | 1764840 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 9 | coupling_state | 2103 | 2103 | 0 | 2103 | 1766520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 10 | coupling_state | 2100 | 2100 | 0 | 2100 | 1764000 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 11 | coupling_state | 2118 | 2118 | 0 | 2118 | 1779120 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 12 | coupling_state | 2103 | 2103 | 0 | 2103 | 1766520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 13 | coupling_state | 2102 | 2102 | 0 | 2102 | 1765680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 14 | coupling_state | 2141 | 2141 | 0 | 2141 | 1798440 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 15 | coupling_state | 1822 | 1822 | 0 | 1822 | 1530480 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 16 | coupling_state | 1821 | 1821 | 0 | 1821 | 1529640 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 17 | coupling_state | 2104 | 2104 | 0 | 2104 | 1767360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 18 | coupling_state | 1821 | 1821 | 0 | 1821 | 1529640 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 19 | coupling_state | 2380 | 2380 | 0 | 2380 | 1999200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 22 | coupling_state | 1824 | 1824 | 0 | 1824 | 1532160 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 23 | coupling_state | 2104 | 2104 | 0 | 2104 | 1767360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B1 | 24 | coupling_state | 2096 | 2096 | 0 | 2096 | 1760640 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| B2 | 0 | coupling_state | 5500 | 5499 | 0 | 4839 | 1156926 | 239.084 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B2 | 1 | coupling_state | 5497 | 5496 | 0 | 4836 | 1156225 | 239.087 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B2 | 2 | coupling_state | 5500 | 5499 | 0 | 4839 | 1156926 | 239.084 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B2 | 3 | coupling_state | 4768 | 4767 | 0 | 4195 | 1002938 | 239.079 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B2 | 4 | coupling_state | 4764 | 4763 | 0 | 4191 | 1001978 | 239.079 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B2 | 6 | coupling_state | 5492 | 5491 | 0 | 4831 | 1154989 | 239.079 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B2 | 7 | coupling_state | 5494 | 5493 | 0 | 4833 | 1155468 | 239.079 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B2 | 8 | coupling_state | 5498 | 5497 | 0 | 4837 | 1156465 | 239.087 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B2 | 9 | coupling_state | 5500 | 5499 | 0 | 4839 | 1156945 | 239.088 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B2 | 10 | coupling_state | 5498 | 5497 | 0 | 4837 | 1156446 | 239.083 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B2 | 11 | coupling_state | 5487 | 5486 | 0 | 4826 | 1153825 | 239.085 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B2 | 12 | coupling_state | 5500 | 5499 | 0 | 4839 | 1156871 | 239.072 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B2 | 13 | coupling_state | 5498 | 5497 | 0 | 4837 | 1156447 | 239.084 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B2 | 14 | coupling_state | 5495 | 5494 | 0 | 4834 | 1156031 | 239.146 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B2 | 15 | coupling_state | 4767 | 4766 | 0 | 4194 | 1002716 | 239.083 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B2 | 16 | coupling_state | 4767 | 4766 | 0 | 4194 | 1002697 | 239.079 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B2 | 17 | coupling_state | 5495 | 5494 | 0 | 4834 | 1155822 | 239.103 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B2 | 18 | coupling_state | 4764 | 4763 | 0 | 4191 | 1002033 | 239.092 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B2 | 19 | coupling_state | 6233 | 6232 | 0 | 5484 | 1311098 | 239.077 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B2 | 22 | coupling_state | 4769 | 4768 | 0 | 4196 | 1003196 | 239.084 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B2 | 23 | coupling_state | 5502 | 5501 | 0 | 4841 | 1157406 | 239.084 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| B2 | 24 | coupling_state | 5493 | 5492 | 0 | 4832 | 1155228 | 239.079 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |

<sub>`per-sweep overhead — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.135.** *units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; the finished evaluation-phase gate runs of large_tokamak_nof.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 80 (finished evaluation-phase runs of large_tokamak_nof).*

| arm | seed | stops_on | dispatch_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 4 | 4 | 3360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 4 | 4 | 3360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 4 | 4 | 3360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 4 | 4 | 3360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 10 | 9 | 2157 | 239.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 11 | 10 | 2397 | 239.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1456 | 242.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 9 | 8 | 1899 | 237.375 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1456 | 242.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 5 | 4 | 977 | 244.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 9 | 8 | 1881 | 235.125 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 10 | 9 | 2157 | 239.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 10 | 9 | 2121 | 235.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1420 | 236.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1456 | 242.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 6 | 5 | 1180 | 236 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 9 | 8 | 1881 | 235.125 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 6 | 5 | 1180 | 236 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 6 | 5 | 1180 | 236 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 6 | 5 | 1180 | 236 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1456 | 242.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 6 | 5 | 1180 | 236 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1456 | 242.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 9 | 8 | 1881 | 235.125 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |

<sub>`per-sweep overhead — large_tokamak_nof — campaign_stencil_backward`</sub>

**Table F.136.** *units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; the finished evaluation-phase gate runs of large_tokamak_nof.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 80 (finished evaluation-phase runs of large_tokamak_nof).*

| arm | seed | stops_on | dispatch_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 27 | 27 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 54 | 27 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 81 | 27 | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 4 | 4 | 3360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 4 | 4 | 3360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 5 | 5 | 4200 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 4 | 4 | 3360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 2 | 2 | 1680 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2520 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 4 | 4 | 3360 | 840 | FLAT 840 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 10 | 9 | 2157 | 239.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 11 | 10 | 2397 | 239.7 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1456 | 242.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 8 | 7 | 1678 | 239.714 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1456 | 242.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 5 | 4 | 977 | 244.25 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 9 | 8 | 1881 | 235.125 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 9 | 8 | 1936 | 242 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 10 | 9 | 2121 | 235.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1420 | 236.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1456 | 242.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 6 | 5 | 1180 | 236 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 9 | 8 | 1881 | 235.125 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 6 | 5 | 1180 | 236 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 6 | 5 | 1180 | 236 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 6 | 5 | 1180 | 236 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1456 | 242.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 6 | 5 | 1180 | 236 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1456 | 242.667 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 9 | 8 | 1881 | 235.125 | M1 258, M2 240, M3 221 | 0 | 0 | — | 0 |

<sub>`per-sweep overhead — large_tokamak_nof — campaign_stencil_forward`</sub>

**Table F.137.** *units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; the finished evaluation-phase gate runs of low_aspect_ratio_DEMO.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 100 (finished evaluation-phase runs of low_aspect_ratio_DEMO).*

| arm | seed | stops_on | dispatch_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 1 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 2 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 3 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 4 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 5 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 6 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 7 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 8 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 9 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 10 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 11 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 12 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 13 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 14 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 15 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 16 | upstream | 5 | 0 | 0 | — | — | 4 | 79 | 19.75 | 0 |
| AR | 17 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 18 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 19 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 20 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 21 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 22 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 23 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 24 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 25 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| A0 | 1 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 2 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 3 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 4 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 5 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 6 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 7 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 8 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 9 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 10 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 11 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 12 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 13 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 14 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 15 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 16 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 17 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 18 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 19 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 20 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 21 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 22 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 23 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 24 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 25 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 1 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 2 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 3 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 4 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 5 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 6 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 7 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 8 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 9 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 10 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 11 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 12 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 13 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 14 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 15 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 16 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 17 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 18 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 19 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 20 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 21 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 22 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 23 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 24 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 25 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A2 | 1 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 2 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 3 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 4 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 5 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 6 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 7 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 8 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 9 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 10 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 11 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 12 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 13 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 14 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 15 | coupling_state | 12 | 11 | 2675 | 243.182 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 16 | coupling_state | 12 | 11 | 2675 | 243.182 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 17 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 18 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 19 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 20 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 21 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 22 | coupling_state | 12 | 11 | 2675 | 243.182 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 23 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 24 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 25 | coupling_state | 13 | 12 | 2919 | 243.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |

<sub>`per-sweep overhead — low_aspect_ratio_DEMO — campaign_displaced`</sub>

**Table F.138.** *units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; the finished evaluation-phase gate runs of low_aspect_ratio_DEMO.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 1 (finished evaluation-phase runs of low_aspect_ratio_DEMO).*

| arm | seed | stops_on | dispatch_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |

<sub>`per-sweep overhead — low_aspect_ratio_DEMO — campaign_entry_references`</sub>

**Table F.139.** *units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished optimisation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the finished optimisation-phase gate runs of low_aspect_ratio_DEMO.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 84 (finished optimisation-phase runs of low_aspect_ratio_DEMO).*

| arm | seed | stops_on | dispatch_sweeps | solve_sweeps | output_loop_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | 0 | upstream | 4286 | 4284 | 2 | 0 | 0 | — | — | 3044 | 68069 | 22.3617 | 0 |
| BR | 1 | upstream | 31869 | 31867 | 2 | 0 | 0 | — | — | 22627 | 499852 | 22.091 | 0 |
| BR | 2 | upstream | 548 | 546 | 2 | 0 | 0 | — | — | 386 | 8311 | 21.5311 | 0 |
| BR | 4 | upstream | 515 | 513 | 2 | 0 | 0 | — | — | 353 | 7703 | 21.8215 | 0 |
| BR | 5 | upstream | 2903 | 2901 | 2 | 0 | 0 | — | — | 2061 | 45911 | 22.2761 | 0 |
| BR | 6 | upstream | 9255 | 9253 | 2 | 0 | 0 | — | — | 6573 | 146973 | 22.3601 | 0 |
| BR | 7 | upstream | 540 | 538 | 2 | 0 | 0 | — | — | 378 | 8353 | 22.0979 | 0 |
| BR | 8 | upstream | 527 | 525 | 2 | 0 | 0 | — | — | 365 | 8015 | 21.9589 | 0 |
| BR | 9 | upstream | 3455 | 3453 | 2 | 0 | 0 | — | — | 2453 | 54753 | 22.3208 | 0 |
| BR | 10 | upstream | 2898 | 2896 | 2 | 0 | 0 | — | — | 2056 | 45856 | 22.3035 | 0 |
| BR | 11 | upstream | 2906 | 2904 | 2 | 0 | 0 | — | — | 2064 | 45939 | 22.2573 | 0 |
| BR | 12 | upstream | 4287 | 4285 | 2 | 0 | 0 | — | — | 3045 | 68020 | 22.3383 | 0 |
| BR | 13 | upstream | 5388 | 5386 | 2 | 0 | 0 | — | — | 3826 | 85501 | 22.3474 | 0 |
| BR | 14 | upstream | 532 | 530 | 2 | 0 | 0 | — | — | 370 | 8095 | 21.8784 | 0 |
| BR | 15 | upstream | 17515 | 17513 | 2 | 0 | 0 | — | — | 12433 | 278158 | 22.3726 | 0 |
| BR | 16 | upstream | 541 | 539 | 2 | 0 | 0 | — | — | 379 | 8379 | 22.1082 | 0 |
| BR | 17 | upstream | 542 | 540 | 2 | 0 | 0 | — | — | 380 | 8405 | 22.1184 | 0 |
| BR | 18 | upstream | 4004 | 4002 | 2 | 0 | 0 | — | — | 2842 | 63492 | 22.3406 | 0 |
| BR | 19 | upstream | 3172 | 3170 | 2 | 0 | 0 | — | — | 2250 | 50250 | 22.3333 | 0 |
| BR | 20 | upstream | 536 | 534 | 2 | 0 | 0 | — | — | 374 | 8099 | 21.6551 | 0 |
| BR | 22 | upstream | 532 | 530 | 2 | 0 | 0 | — | — | 370 | 8145 | 22.0135 | 0 |
| BR | 23 | upstream | 542 | 540 | 2 | 0 | 0 | — | — | 380 | 8405 | 22.1184 | 0 |
| BR | 24 | upstream | 545 | 543 | 2 | 0 | 0 | — | — | 383 | 8483 | 22.1488 | 0 |
| B0 | 0 | coupling_state | 4139 | 4137 | 2 | 4137 | 3499902 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 1 | coupling_state | 31215 | 31213 | 2 | 31213 | 26406198 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 2 | coupling_state | 553 | 551 | 2 | 551 | 466146 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 5 | coupling_state | 2809 | 2807 | 2 | 2807 | 2374722 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 6 | coupling_state | 8934 | 8932 | 2 | 8932 | 7556472 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 7 | coupling_state | 542 | 540 | 2 | 540 | 456840 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 8 | coupling_state | 540 | 538 | 2 | 538 | 455148 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 9 | coupling_state | 3339 | 3337 | 2 | 3337 | 2823102 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 10 | coupling_state | 2809 | 2807 | 2 | 2807 | 2374722 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 11 | coupling_state | 2809 | 2807 | 2 | 2807 | 2374722 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 12 | coupling_state | 4141 | 4139 | 2 | 4139 | 3501594 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 13 | coupling_state | 5203 | 5201 | 2 | 5201 | 4400046 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 14 | coupling_state | 551 | 549 | 2 | 549 | 464454 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 15 | coupling_state | 16920 | 16918 | 2 | 16918 | 14312628 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 16 | coupling_state | 537 | 535 | 2 | 535 | 452610 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 17 | coupling_state | 539 | 537 | 2 | 537 | 454302 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 18 | coupling_state | 3868 | 3866 | 2 | 3866 | 3270636 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 19 | coupling_state | 3072 | 3070 | 2 | 3070 | 2597220 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 20 | coupling_state | 545 | 543 | 2 | 543 | 459378 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 23 | coupling_state | 541 | 539 | 2 | 539 | 455994 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B0 | 24 | coupling_state | 547 | 545 | 2 | 545 | 461070 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 0 | coupling_state | 3330 | 3330 | 0 | 3330 | 2817180 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 1 | coupling_state | 3868 | 3868 | 0 | 3868 | 3272328 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 2 | coupling_state | 538 | 538 | 0 | 538 | 455148 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 5 | coupling_state | 9440 | 9440 | 0 | 9440 | 7986240 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 6 | coupling_state | 5455 | 5455 | 0 | 5455 | 4614930 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 7 | coupling_state | 523 | 523 | 0 | 523 | 442458 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 8 | coupling_state | 523 | 523 | 0 | 523 | 442458 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 9 | coupling_state | 3600 | 3600 | 0 | 3600 | 3045600 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 11 | coupling_state | 17171 | 17171 | 0 | 17171 | 14526666 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 12 | coupling_state | 2534 | 2534 | 0 | 2534 | 2143764 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 13 | coupling_state | 4661 | 4661 | 0 | 4661 | 3943206 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 14 | coupling_state | 533 | 533 | 0 | 533 | 450918 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 15 | coupling_state | 4124 | 4124 | 0 | 4124 | 3488904 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 16 | coupling_state | 537 | 537 | 0 | 537 | 454302 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 17 | coupling_state | 538 | 538 | 0 | 538 | 455148 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 18 | coupling_state | 3077 | 3077 | 0 | 3077 | 2603142 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 19 | coupling_state | 2535 | 2535 | 0 | 2535 | 2144610 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 20 | coupling_state | 541 | 541 | 0 | 541 | 457686 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 23 | coupling_state | 539 | 539 | 0 | 539 | 455994 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B1 | 24 | coupling_state | 530 | 530 | 0 | 530 | 448380 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| B2 | 0 | coupling_state | 8763 | 8762 | 0 | 7712 | 1855182 | 240.558 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B2 | 1 | coupling_state | 10183 | 10182 | 0 | 8964 | 2156500 | 240.573 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B2 | 2 | coupling_state | 1393 | 1392 | 0 | 1224 | 294788 | 240.84 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B2 | 5 | coupling_state | 24884 | 24883 | 0 | 21901 | 5268614 | 240.565 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B2 | 6 | coupling_state | 14383 | 14382 | 0 | 12660 | 3045529 | 240.563 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B2 | 7 | coupling_state | 1385 | 1384 | 0 | 1216 | 292750 | 240.748 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B2 | 8 | coupling_state | 1380 | 1379 | 0 | 1211 | 291645 | 240.83 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B2 | 9 | coupling_state | 9481 | 9480 | 0 | 8346 | 2007830 | 240.574 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B2 | 11 | coupling_state | 45222 | 45221 | 0 | 39803 | 9575641 | 240.576 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B2 | 12 | coupling_state | 6676 | 6675 | 0 | 5877 | 1413837 | 240.571 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B2 | 13 | coupling_state | 12283 | 12282 | 0 | 10812 | 2601007 | 240.567 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B2 | 14 | coupling_state | 1396 | 1395 | 0 | 1227 | 295305 | 240.672 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B2 | 15 | coupling_state | 10869 | 10868 | 0 | 9566 | 2301183 | 240.559 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B2 | 16 | coupling_state | 1397 | 1396 | 0 | 1228 | 295694 | 240.793 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B2 | 17 | coupling_state | 1402 | 1401 | 0 | 1233 | 296769 | 240.689 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B2 | 18 | coupling_state | 8088 | 8087 | 0 | 7121 | 1713243 | 240.59 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B2 | 19 | coupling_state | 6672 | 6671 | 0 | 5873 | 1412839 | 240.565 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B2 | 20 | coupling_state | 1405 | 1404 | 0 | 1236 | 297630 | 240.801 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B2 | 23 | coupling_state | 1404 | 1403 | 0 | 1235 | 297287 | 240.718 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| B2 | 24 | coupling_state | 1392 | 1391 | 0 | 1223 | 294383 | 240.706 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |

<sub>`per-sweep overhead — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.140.** *units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; the finished evaluation-phase gate runs of low_aspect_ratio_DEMO.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 76 (finished evaluation-phase runs of low_aspect_ratio_DEMO).*

| arm | seed | stops_on | dispatch_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 53 | 17.6667 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 53 | 17.6667 | 0 |
| AR | 0 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26 | 0 |
| AR | 0 | upstream | 5 | 0 | 0 | — | — | 4 | 104 | 26 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 10 | 9 | 2172 | 241.333 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 11 | 10 | 2416 | 241.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1463 | 243.833 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 8 | 7 | 1669 | 238.429 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1463 | 243.833 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 8 | 7 | 1654 | 236.286 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 9 | 8 | 1898 | 237.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 10 | 9 | 2172 | 241.333 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 9 | 8 | 1898 | 237.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 8 | 7 | 1654 | 236.286 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 8 | 7 | 1654 | 236.286 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1463 | 243.833 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1410 | 235 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 8 | 7 | 1677 | 239.571 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1463 | 243.833 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1463 | 243.833 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |

<sub>`per-sweep overhead — low_aspect_ratio_DEMO — campaign_stencil_backward`</sub>

**Table F.141.** *units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; the finished evaluation-phase gate runs of low_aspect_ratio_DEMO.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 76 (finished evaluation-phase runs of low_aspect_ratio_DEMO).*

| arm | seed | stops_on | dispatch_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 53 | 17.6667 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 53 | 17.6667 | 0 |
| AR | 0 | upstream | 5 | 0 | 0 | — | — | 4 | 104 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 5 | 0 | 0 | — | — | 4 | 54 | 13.5 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26 | 0 |
| AR | 0 | upstream | 5 | 0 | 0 | — | — | 4 | 104 | 26 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 26 | 26 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 52 | 26 | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4230 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 4 | 4 | 3384 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 2 | 2 | 1692 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A1 | 0 | coupling_state | 3 | 3 | 2538 | 846 | FLAT 846 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 10 | 9 | 2172 | 241.333 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 11 | 10 | 2416 | 241.6 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1463 | 243.833 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 8 | 7 | 1669 | 238.429 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1463 | 243.833 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 8 | 7 | 1654 | 236.286 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 9 | 8 | 1898 | 237.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 9 | 8 | 1928 | 241 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 9 | 8 | 1898 | 237.25 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1433 | 238.833 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1433 | 238.833 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1463 | 243.833 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 8 | 7 | 1677 | 239.571 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1463 | 243.833 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 6 | 5 | 1189 | 237.8 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 7 | 6 | 1463 | 243.833 | M1 259, M2 244, M3 221 | 0 | 0 | — | 0 |

<sub>`per-sweep overhead — low_aspect_ratio_DEMO — campaign_stencil_forward`</sub>

**Table F.142.** *units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_displaced — the campaign population: the displaced-entry regime, every arm from the same seeded displacement of the reference fixed point, seeds 1–25; the finished evaluation-phase gate runs of st_regression.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %, 6.67 %, 7.14 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 75 (finished evaluation-phase runs of st_regression).*

| arm | seed | stops_on | dispatch_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 1 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 2 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 3 | upstream | 4 | 0 | 0 | — | — | 3 | 21 | 7 | 0 |
| AR | 4 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 5 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 6 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 7 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 8 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 9 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 10 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 11 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 12 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 13 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 14 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 15 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 16 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 17 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 18 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 19 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 20 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 21 | upstream | 4 | 0 | 0 | — | — | 3 | 21 | 7 | 0 |
| AR | 22 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 23 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 24 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| AR | 25 | upstream | 5 | 0 | 0 | — | — | 4 | 40 | 10 | 0 |
| A0 | 1 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 2 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 3 | coupling_state | 5 | 5 | 4135 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 4 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 5 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 6 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 7 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 8 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 9 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 10 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 11 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 12 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 13 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 14 | coupling_state | 5 | 5 | 4135 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 15 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 16 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 17 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 18 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 19 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 20 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 21 | coupling_state | 5 | 5 | 4135 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 22 | coupling_state | 5 | 5 | 4135 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 23 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 24 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 25 | coupling_state | 6 | 6 | 4962 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A2 | 1 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A2 | 2 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A2 | 3 | coupling_state | 14 | 12 | 2821 | 235.083 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0714286 |
| A2 | 4 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A2 | 5 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A2 | 6 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A2 | 7 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A2 | 8 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A2 | 9 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A2 | 10 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A2 | 11 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A2 | 12 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A2 | 13 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A2 | 14 | coupling_state | 14 | 12 | 2821 | 235.083 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0714286 |
| A2 | 15 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A2 | 16 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A2 | 17 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A2 | 18 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A2 | 19 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A2 | 20 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A2 | 21 | coupling_state | 14 | 12 | 2821 | 235.083 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0714286 |
| A2 | 22 | coupling_state | 14 | 12 | 2821 | 235.083 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0714286 |
| A2 | 23 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A2 | 24 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |
| A2 | 25 | coupling_state | 15 | 13 | 3037 | 233.615 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0666667 |

<sub>`per-sweep overhead — st_regression — campaign_displaced`</sub>

**Table F.143.** *units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_entry_references — the campaign population: one flat A0 evaluation per configuration from the input file's design point — the cold-start term, beside and never pooled; the finished evaluation-phase gate runs of st_regression.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 1 (finished evaluation-phase runs of st_regression).*

| arm | seed | stops_on | dispatch_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 0 | coupling_state | 7 | 7 | 5789 | 827 | FLAT 827 | 0 | 0 | — | 0 |

<sub>`per-sweep overhead — st_regression — campaign_entry_references`</sub>

**Table F.144.** *units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished optimisation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the finished optimisation-phase gate runs of st_regression.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %, 10.7 %, 10.8 %, 10.82 %, 10.83 %, 10.84 %, 10.85 %, 10.86 %, 10.87 %, 10.9 %, 10.91 %, 10.92 %, 10.94 %, 11.15 %, 11.18 %, 11.22 %, 11.3 %, 11.57 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 75 (finished optimisation-phase runs of st_regression).*

| arm | seed | stops_on | dispatch_sweeps | solve_sweeps | output_loop_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | 0 | upstream | 1891 | 1889 | 2 | 0 | 0 | — | — | 1319 | 18491 | 14.019 | 0 |
| BR | 1 | upstream | 8401 | 8399 | 2 | 0 | 0 | — | — | 5789 | 84431 | 14.5847 | 0 |
| BR | 2 | upstream | 10010 | 10008 | 2 | 0 | 0 | — | — | 7128 | 100674 | 14.1237 | 0 |
| BR | 3 | upstream | 3450 | 3448 | 2 | 0 | 0 | — | — | 2398 | 33646 | 14.0309 | 0 |
| BR | 4 | upstream | 3807 | 3805 | 2 | 0 | 0 | — | — | 2635 | 37357 | 14.1772 | 0 |
| BR | 5 | upstream | 7637 | 7635 | 2 | 0 | 0 | — | — | 5265 | 77049 | 14.6342 | 0 |
| BR | 6 | upstream | 3421 | 3419 | 2 | 0 | 0 | — | — | 2369 | 33527 | 14.1524 | 0 |
| BR | 7 | upstream | 1896 | 1894 | 2 | 0 | 0 | — | — | 1324 | 18586 | 14.0378 | 0 |
| BR | 8 | upstream | 2267 | 2265 | 2 | 0 | 0 | — | — | 1575 | 22113 | 14.04 | 0 |
| BR | 9 | upstream | 11612 | 11610 | 2 | 0 | 0 | — | — | 7980 | 117618 | 14.7391 | 0 |
| BR | 10 | upstream | 34192 | 34190 | 2 | 0 | 0 | — | — | 23600 | 343622 | 14.5603 | 0 |
| BR | 11 | upstream | 2091 | 2089 | 2 | 0 | 0 | — | — | 1459 | 20431 | 14.0034 | 0 |
| BR | 12 | upstream | 13324 | 13322 | 2 | 0 | 0 | — | — | 9362 | 132572 | 14.1606 | 0 |
| BR | 13 | upstream | 2658 | 2656 | 2 | 0 | 0 | — | — | 1846 | 25948 | 14.0563 | 0 |
| BR | 14 | upstream | 4225 | 4223 | 2 | 0 | 0 | — | — | 2933 | 41669 | 14.207 | 0 |
| BR | 15 | upstream | 5897 | 5895 | 2 | 0 | 0 | — | — | 4065 | 59235 | 14.572 | 0 |
| BR | 16 | upstream | 4614 | 4612 | 2 | 0 | 0 | — | — | 3202 | 45700 | 14.2723 | 0 |
| BR | 17 | upstream | 386 | 384 | 2 | 0 | 0 | — | — | 264 | 3468 | 13.1364 | 0 |
| BR | 18 | upstream | 2460 | 2458 | 2 | 0 | 0 | — | — | 1708 | 24136 | 14.1311 | 0 |
| BR | 19 | upstream | 2077 | 2075 | 2 | 0 | 0 | — | — | 1445 | 20255 | 14.0173 | 0 |
| BR | 20 | upstream | 2671 | 2669 | 2 | 0 | 0 | — | — | 1859 | 26069 | 14.0231 | 0 |
| BR | 21 | upstream | 1889 | 1887 | 2 | 0 | 0 | — | — | 1317 | 18471 | 14.0251 | 0 |
| BR | 22 | upstream | 2261 | 2259 | 2 | 0 | 0 | — | — | 1569 | 21999 | 14.021 | 0 |
| BR | 23 | upstream | 2080 | 2078 | 2 | 0 | 0 | — | — | 1448 | 20222 | 13.9655 | 0 |
| BR | 24 | upstream | 39951 | 39949 | 2 | 0 | 0 | — | — | 27559 | 401527 | 14.5697 | 0 |
| B0 | 0 | coupling_state | 2038 | 2036 | 2 | 2036 | 1683772 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 1 | coupling_state | 10764 | 10762 | 2 | 10762 | 8900174 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 2 | coupling_state | 10422 | 10420 | 2 | 10420 | 8617340 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 3 | coupling_state | 3643 | 3641 | 2 | 3641 | 3011107 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 4 | coupling_state | 3843 | 3841 | 2 | 3841 | 3176507 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 5 | coupling_state | 8355 | 8353 | 2 | 8353 | 6907931 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 6 | coupling_state | 3452 | 3450 | 2 | 3450 | 2853150 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 7 | coupling_state | 1894 | 1892 | 2 | 1892 | 1564684 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 8 | coupling_state | 2283 | 2281 | 2 | 2281 | 1886387 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 9 | coupling_state | 9074 | 9072 | 2 | 9072 | 7502544 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 10 | coupling_state | 31811 | 31809 | 2 | 31809 | 26306043 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 11 | coupling_state | 2099 | 2097 | 2 | 2097 | 1734219 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 12 | coupling_state | 14083 | 14081 | 2 | 14081 | 11644987 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 13 | coupling_state | 2672 | 2670 | 2 | 2670 | 2208090 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 14 | coupling_state | 4240 | 4238 | 2 | 4238 | 3504826 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 15 | coupling_state | 12000 | 11998 | 2 | 11998 | 9922346 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 16 | coupling_state | 4976 | 4974 | 2 | 4974 | 4113498 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 17 | coupling_state | 422 | 420 | 2 | 420 | 347340 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 18 | coupling_state | 2477 | 2475 | 2 | 2475 | 2046825 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 19 | coupling_state | 2667 | 2665 | 2 | 2665 | 2203955 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 20 | coupling_state | 2841 | 2839 | 2 | 2839 | 2347853 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 21 | coupling_state | 1894 | 1892 | 2 | 1892 | 1564684 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 22 | coupling_state | 2319 | 2317 | 2 | 2317 | 1916159 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 23 | coupling_state | 2239 | 2237 | 2 | 2237 | 1849999 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B0 | 24 | coupling_state | 9179 | 9177 | 2 | 9177 | 7589379 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| B2 | 0 | coupling_state | 5260 | 5259 | 0 | 4119 | 970258 | 235.557 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.108365 |
| B2 | 1 | coupling_state | 31072 | 31071 | 0 | 24051 | 5659602 | 235.317 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.112963 |
| B2 | 2 | coupling_state | 21154 | 21153 | 0 | 16533 | 3892592 | 235.444 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.109199 |
| B2 | 3 | coupling_state | 9695 | 9694 | 0 | 7594 | 1788185 | 235.473 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.108303 |
| B2 | 4 | coupling_state | 10722 | 10721 | 0 | 8381 | 1972937 | 235.406 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.109121 |
| B2 | 5 | coupling_state | 110386 | 110385 | 0 | 85605 | 20138750 | 235.252 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.112242 |
| B2 | 6 | coupling_state | 9633 | 9632 | 0 | 7532 | 1773223 | 235.425 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.109 |
| B2 | 7 | coupling_state | 5259 | 5258 | 0 | 4118 | 970028 | 235.558 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.108386 |
| B2 | 8 | coupling_state | 6353 | 6352 | 0 | 4972 | 1171089 | 235.537 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.10861 |
| B2 | 9 | coupling_state | 32470 | 32469 | 0 | 25209 | 5925850 | 235.069 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111796 |
| B2 | 10 | coupling_state | 30850 | 30849 | 0 | 23709 | 5588124 | 235.696 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.115721 |
| B2 | 11 | coupling_state | 5822 | 5821 | 0 | 4561 | 1074441 | 235.571 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.10821 |
| B2 | 12 | coupling_state | 9051 | 9050 | 0 | 7070 | 1664464 | 235.426 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.10938 |
| B2 | 13 | coupling_state | 7421 | 7420 | 0 | 5800 | 1366359 | 235.579 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.10915 |
| B2 | 14 | coupling_state | 11831 | 11830 | 0 | 9250 | 2177370 | 235.391 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.109036 |
| B2 | 15 | coupling_state | 38461 | 38460 | 0 | 29880 | 7024544 | 235.092 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111542 |
| B2 | 16 | coupling_state | 14015 | 14014 | 0 | 10954 | 2577921 | 235.341 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.109169 |
| B2 | 17 | coupling_state | 1122 | 1121 | 0 | 881 | 207690 | 235.743 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.106952 |
| B2 | 18 | coupling_state | 6898 | 6897 | 0 | 5397 | 1270730 | 235.451 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.108727 |
| B2 | 19 | coupling_state | 5808 | 5807 | 0 | 4547 | 1071105 | 235.563 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.108471 |
| B2 | 20 | coupling_state | 7433 | 7432 | 0 | 5812 | 1369273 | 235.594 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.108973 |
| B2 | 21 | coupling_state | 5262 | 5261 | 0 | 4121 | 970697 | 235.549 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.108324 |
| B2 | 22 | coupling_state | 6390 | 6389 | 0 | 5009 | 1179088 | 235.394 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.107981 |
| B2 | 23 | coupling_state | 5800 | 5799 | 0 | 4539 | 1069466 | 235.617 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.108621 |
| B2 | 24 | coupling_state | 24966 | 24965 | 0 | 19385 | 4558929 | 235.178 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111752 |

<sub>`per-sweep overhead — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table F.145.** *units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_stencil_backward — the campaign population: the stencil regime's backward points, each from its forward point's exit, one per design-vector column per arm, paired by column; the finished evaluation-phase gate runs of st_regression.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %, 9.09 %, 10 %, 11.11 %, 12.5 %, 16.67 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 42 (finished evaluation-phase runs of st_regression).*

| arm | seed | stops_on | dispatch_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 21 | 7 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 19 | 19 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 19 | 19 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 57 | 19 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 57 | 19 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 57 | 19 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 19 | 19 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 57 | 19 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10 | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1654 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1654 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4135 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 5 | 5 | 4135 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 10 | 8 | 1957 | 244.625 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.1 |
| A2 | 0 | coupling_state | 8 | 6 | 1414 | 235.667 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.125 |
| A2 | 0 | coupling_state | 9 | 7 | 1689 | 241.286 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111111 |
| A2 | 0 | coupling_state | 6 | 4 | 975 | 243.75 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.166667 |
| A2 | 0 | coupling_state | 9 | 7 | 1578 | 225.429 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111111 |
| A2 | 0 | coupling_state | 9 | 7 | 1682 | 240.286 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111111 |
| A2 | 0 | coupling_state | 9 | 7 | 1578 | 225.429 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111111 |
| A2 | 0 | coupling_state | 11 | 9 | 2017 | 224.111 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0909091 |
| A2 | 0 | coupling_state | 8 | 6 | 1369 | 228.167 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.125 |
| A2 | 0 | coupling_state | 9 | 7 | 1689 | 241.286 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111111 |
| A2 | 0 | coupling_state | 8 | 6 | 1466 | 244.333 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.125 |
| A2 | 0 | coupling_state | 11 | 9 | 2017 | 224.111 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.0909091 |
| A2 | 0 | coupling_state | 8 | 6 | 1466 | 244.333 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.125 |
| A2 | 0 | coupling_state | 8 | 6 | 1466 | 244.333 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.125 |

<sub>`per-sweep overhead — st_regression — campaign_stencil_backward`</sub>

**Table F.146.** *units: counts — evaluations of a convergence test, and components compared summed over them; sweeps are walks of the model sequence.  A row is one finished evaluation-phase run.  A column is a counter of one **named** convergence test, or a sweep total.  Population: campaign_stencil_forward — the campaign population: the stencil regime's forward points, one per design-vector column per arm, paired by column; the finished evaluation-phase gate runs of st_regression.  Construction: the driver's own counters, exact and concurrency-invariant.  The two predicates are never pooled.  The empty block visits are counted and disclaimed, never repaired, and the share quoted is the SWEEP share — over this population 0 %, 10 %, 11.11 %, 12.5 %, 16.67 %.  The visit share is larger and is never quoted.  No conclusion rests on a timing: the question is asked in counts alone. n = 42 (finished evaluation-phase runs of st_regression).*

| arm | seed | stops_on | dispatch_sweeps | coupling_evaluations | coupling_components | coupling_width | coupling_width_by_block | upstream_evaluations | upstream_components | upstream_width | empty_sweep_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 21 | 7 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 19 | 19 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 19 | 19 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 38 | 19 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 38 | 19 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 57 | 19 | 0 |
| AR | 0 | upstream | 2 | 0 | 0 | — | — | 1 | 19 | 19 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10 | 0 |
| AR | 0 | upstream | 4 | 0 | 0 | — | — | 3 | 57 | 19 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10 | 0 |
| AR | 0 | upstream | 3 | 0 | 0 | — | — | 2 | 20 | 10 | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1654 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 2 | 2 | 1654 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 4 | 4 | 3308 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A0 | 0 | coupling_state | 3 | 3 | 2481 | 827 | FLAT 827 | 0 | 0 | — | 0 |
| A2 | 0 | coupling_state | 10 | 8 | 1957 | 244.625 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.1 |
| A2 | 0 | coupling_state | 8 | 6 | 1414 | 235.667 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.125 |
| A2 | 0 | coupling_state | 9 | 7 | 1689 | 241.286 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111111 |
| A2 | 0 | coupling_state | 6 | 4 | 975 | 243.75 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.166667 |
| A2 | 0 | coupling_state | 9 | 7 | 1578 | 225.429 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111111 |
| A2 | 0 | coupling_state | 9 | 7 | 1682 | 240.286 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111111 |
| A2 | 0 | coupling_state | 9 | 7 | 1578 | 225.429 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111111 |
| A2 | 0 | coupling_state | 10 | 8 | 1801 | 225.125 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.1 |
| A2 | 0 | coupling_state | 8 | 6 | 1369 | 228.167 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.125 |
| A2 | 0 | coupling_state | 9 | 7 | 1689 | 241.286 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.111111 |
| A2 | 0 | coupling_state | 8 | 6 | 1466 | 244.333 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.125 |
| A2 | 0 | coupling_state | 10 | 8 | 1801 | 225.125 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.1 |
| A2 | 0 | coupling_state | 8 | 6 | 1466 | 244.333 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.125 |
| A2 | 0 | coupling_state | 8 | 6 | 1466 | 244.333 | M1 268, M2 216, M3 223 | 0 | 0 | — | 0.125 |

<sub>`per-sweep overhead — st_regression — campaign_stencil_forward`</sub>

**Table F.147.** *units: dimensionless — a relative difference of the normalised objective.  A row is one arm pair over the seed set.  A column is the paired relative objective difference's median and p90, the threshold they are judged against, and the clustering statistics.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 22 seed(s) on which every arm of large_tokamak_nof reached an accepted optimum.  Construction: |Δ norm_objf| / max(|a|, |b|) per pair from the hex floats; median nearest-rank upper-middle, p90 nearest-rank ceil(0.9 n); threshold = max(F × yardstick, floor) with F = 10 and floor = 1e-06, the yardstick being the BR → B0 spread in this same population; clusters at a relative gap of 1e-05.  The yardstick row carries no threshold and no verdict: it *is* the calibration.  *Below resolution* is a named category — distinct optima closer than the cluster gap and further apart than the correctness floor.  The retried column is computed from attempts[], never from a stored flag. n = 22 (seeds on which every arm of large_tokamak_nof converged).*

| pair | n | r_median | r_p90 | threshold_median | threshold_p90 | verdict | hops | below_resolution | retried_in_pair |
|---|---|---|---|---|---|---|---|---|---|
| BR → B0 (yardstick) | 22 | 2.08167e-15 | 6.8931e-13 | — | — | — | 0/22 (0.00) | 0 | 0 |
| B0 → B1 | 22 | 2.82345e-11 | 4.56971e-11 | 1e-06 | 1e-06 | PASS | 0/22 (0.00) | 0 | 0 |
| B0 → B2 | 22 | 2.82345e-11 | 4.56971e-11 | 1e-06 | 1e-06 | PASS | 0/22 (0.00) | 0 | 0 |

<sub>`same optimum (check 1) — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.148.** *units: dimensionless — a relative difference of the normalised objective.  A row is one arm pair over the seed set.  A column is the paired relative objective difference's median and p90, the threshold they are judged against, and the clustering statistics.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 11 seed(s) on which every arm of low_aspect_ratio_DEMO reached an accepted optimum.  Construction: |Δ norm_objf| / max(|a|, |b|) per pair from the hex floats; median nearest-rank upper-middle, p90 nearest-rank ceil(0.9 n); threshold = max(F × yardstick, floor) with F = 10 and floor = 1e-06, the yardstick being the BR → B0 spread in this same population; clusters at a relative gap of 1e-05.  The yardstick row carries no threshold and no verdict: it *is* the calibration.  *Below resolution* is a named category — distinct optima closer than the cluster gap and further apart than the correctness floor.  The retried column is computed from attempts[], never from a stored flag. n = 11 (seeds on which every arm of low_aspect_ratio_DEMO converged).*

| pair | n | r_median | r_p90 | threshold_median | threshold_p90 | verdict | hops | below_resolution | retried_in_pair |
|---|---|---|---|---|---|---|---|---|---|
| BR → B0 (yardstick) | 11 | 1.98217e-14 | 1.97589e-13 | — | — | — | 0/11 (0.00) | 0 | 1 |
| B0 → B1 | 11 | 4.10089e-07 | 2.14765e-06 | 1e-06 | 1e-06 | FAIL | 1/11 (0.09) | 2 | 1 |
| B0 → B2 | 11 | 4.10089e-07 | 2.14765e-06 | 1e-06 | 1e-06 | FAIL | 1/11 (0.09) | 2 | 1 |

<sub>`same optimum (check 1) — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.149.** *units: dimensionless — a relative difference of the normalised objective.  A row is one arm pair over the seed set.  A column is the paired relative objective difference's median and p90, the threshold they are judged against, and the clustering statistics.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 22 seed(s) on which every arm of st_regression reached an accepted optimum.  Construction: |Δ norm_objf| / max(|a|, |b|) per pair from the hex floats; median nearest-rank upper-middle, p90 nearest-rank ceil(0.9 n); threshold = max(F × yardstick, floor) with F = 10 and floor = 1e-06, the yardstick being the BR → B0 spread in this same population; clusters at a relative gap of 1e-05.  The yardstick row carries no threshold and no verdict: it *is* the calibration.  *Below resolution* is a named category — distinct optima closer than the cluster gap and further apart than the correctness floor.  The retried column is computed from attempts[], never from a stored flag. n = 22 (seeds on which every arm of st_regression converged).*

| pair | n | r_median | r_p90 | threshold_median | threshold_p90 | verdict | hops | below_resolution | retried_in_pair |
|---|---|---|---|---|---|---|---|---|---|
| BR → B0 (yardstick) | 22 | 1.55271e-13 | 5.90757e-09 | — | — | — | 2/22 (0.09) | 0 | 3 |
| B0 → B2 | 22 | 3.46735e-13 | 3.51e-09 | 1e-06 | 1e-06 | PASS | 1/22 (0.05) | 0 | 1 |

<sub>`same optimum (check 1) — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table F.150.** *units: counts — model executions and sweeps of the model sequence.  A row is one optimisation run.  A column is the per-attempt costs, the run's solve-phase total they decompose, and the residual between them.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 100 optimisation run(s) of large_tokamak_nof, of which 100 carry a per-attempt cost the identity can be checked on.  Construction: Σ over attempts[] against node_calls_solve_phase and dispatch_sweeps_solve_phase.  This identity is why the with- and without-retried-seeds cost ratios may be published: they are over quantities that visibly decompose the published total. n = 100 (optimisation-phase runs of large_tokamak_nof).*

| arm | seed | attempts | retried | node_per_attempt | node_total | node_residual | sweeps_per_attempt | sweeps_total | sweeps_residual | decomposes |
|---|---|---|---|---|---|---|---|---|---|---|
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

<sub>`the attempt summation identity — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.151.** *units: counts — model executions and sweeps of the model sequence.  A row is one optimisation run.  A column is the per-attempt costs, the run's solve-phase total they decompose, and the residual between them.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 100 optimisation run(s) of low_aspect_ratio_DEMO, of which 100 carry a per-attempt cost the identity can be checked on.  Construction: Σ over attempts[] against node_calls_solve_phase and dispatch_sweeps_solve_phase.  This identity is why the with- and without-retried-seeds cost ratios may be published: they are over quantities that visibly decompose the published total. n = 100 (optimisation-phase runs of low_aspect_ratio_DEMO).*

| arm | seed | attempts | retried | node_per_attempt | node_total | node_residual | sweeps_per_attempt | sweeps_total | sweeps_residual | decomposes |
|---|---|---|---|---|---|---|---|---|---|---|
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

<sub>`the attempt summation identity — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.152.** *units: counts — model executions and sweeps of the model sequence.  A row is one optimisation run.  A column is the per-attempt costs, the run's solve-phase total they decompose, and the residual between them.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 75 optimisation run(s) of st_regression, of which 75 carry a per-attempt cost the identity can be checked on.  Construction: Σ over attempts[] against node_calls_solve_phase and dispatch_sweeps_solve_phase.  This identity is why the with- and without-retried-seeds cost ratios may be published: they are over quantities that visibly decompose the published total. n = 75 (optimisation-phase runs of st_regression).*

| arm | seed | attempts | retried | node_per_attempt | node_total | node_residual | sweeps_per_attempt | sweeps_total | sweeps_residual | decomposes |
|---|---|---|---|---|---|---|---|---|---|---|
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

<sub>`the attempt summation identity — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table F.153.** *units: counts — model executions for the cost columns, optimiser exit codes for ifail.  A row is one seed outside the converged set.  A column is which arm failed there, how it failed, what it cost, and what the other arms cost at the same start.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 3 of 25 seed(s) on large_tokamak_nof lie outside the every-arm-converged set.  Construction: membership by accepted optimum; the cost column is node_calls_solve_phase, the same unit the cost table uses.  An arm the gate did not run at a seed reads *not run* rather than *failed*. n = 25 (distinct seeds run on large_tokamak_nof).*

| seed | failed | not_run | ifail | attempts | failed_cost | other_cost | configuration_invalid |
|---|---|---|---|---|---|---|---|
| 5 | BR, B0, B1, B2 | — | None, None, None, None | 1, 1, 1, 1 | None, None, None, None | BR — / B0 — / B1 — / B2 — | yes |
| 20 | BR, B0, B1, B2 | — | None, None, None, None | 1, 1, 1, 1 | None, None, None, None | BR — / B0 — / B1 — / B2 — | yes |
| 21 | BR, B0, B1, B2 | — | None, None, None, None | 1, 1, 1, 1 | None, None, None, None | BR — / B0 — / B1 — / B2 — | yes |

<sub>`the failure table — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.154.** *units: counts — model executions for the cost columns, optimiser exit codes for ifail.  A row is one seed outside the converged set.  A column is which arm failed there, how it failed, what it cost, and what the other arms cost at the same start.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 14 of 25 seed(s) on low_aspect_ratio_DEMO lie outside the every-arm-converged set.  Construction: membership by accepted optimum; the cost column is node_calls_solve_phase, the same unit the cost table uses.  An arm the gate did not run at a seed reads *not run* rather than *failed*. n = 25 (distinct seeds run on low_aspect_ratio_DEMO).*

| seed | failed | not_run | ifail | attempts | failed_cost | other_cost | configuration_invalid |
|---|---|---|---|---|---|---|---|
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

<sub>`the failure table — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.155.** *units: counts — model executions for the cost columns, optimiser exit codes for ifail.  A row is one seed outside the converged set.  A column is which arm failed there, how it failed, what it cost, and what the other arms cost at the same start.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; 3 of 25 seed(s) on st_regression lie outside the every-arm-converged set.  Construction: membership by accepted optimum; the cost column is node_calls_solve_phase, the same unit the cost table uses.  An arm the gate did not run at a seed reads *not run* rather than *failed*. n = 25 (distinct seeds run on st_regression).*

| seed | failed | not_run | ifail | attempts | failed_cost | other_cost | configuration_invalid |
|---|---|---|---|---|---|---|---|
| 5 | B2 | — | 5.0 | 3 | 479630 | BR 160335 / B0 175413 / B2 — | no |
| 10 | B0 | — | 5.0 | 3 | 667989 | BR 717990 / B0 — / B2 129012 | no |
| 17 | BR, B0, B2 | — | 5.0, 5.0, 5.0 | 4, 4, 4 | 8064, 8820, 4921 | BR — / B0 — / B2 — | yes |

<sub>`the failure table — st_regression — campaign_optimisation · BR·B0·B2`</sub>

**Table F.156.** *units: seconds for the residual; the relative column is dimensionless (residual / burn time).  A row is one arm whose runs name the burn-time consistency constraint.  A column is the residual of that constraint at the accepted optima.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the accepted optima of large_tokamak_nof whose input file names the constraint.  Construction: the model's own extracted consistency relation evaluated on the returned state, |value|, median nearest-rank upper-middle.  An arm whose input file does not name the constraint is absent from this table rather than reading 0; residuals at unconverged exits are never pooled with these. n = 100 (optimisation-phase runs of large_tokamak_nof).*

| arm | n | residual_s_median | bracket | relative_median | in_equality_block |
|---|---|---|---|---|---|
| B1 | 22 | 1.65911e-05 | [2.600e-06, 1.600e-03] | 2.30429e-09 | True |
| B2 | 22 | 1.65911e-05 | [2.600e-06, 1.600e-03] | 2.30429e-09 | True |

<sub>`the lift closed (check 3) — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.157.** *units: seconds for the residual; the relative column is dimensionless (residual / burn time).  A row is one arm whose runs name the burn-time consistency constraint.  A column is the residual of that constraint at the accepted optima.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the accepted optima of low_aspect_ratio_DEMO whose input file names the constraint.  Construction: the model's own extracted consistency relation evaluated on the returned state, |value|, median nearest-rank upper-middle.  An arm whose input file does not name the constraint is absent from this table rather than reading 0; residuals at unconverged exits are never pooled with these. n = 100 (optimisation-phase runs of low_aspect_ratio_DEMO).*

| arm | n | residual_s_median | bracket | relative_median | in_equality_block |
|---|---|---|---|---|---|
| B1 | 11 | 5.47958e-06 | [1.692e-07, 4.756e-05] | 6.74426e-10 | True |
| B2 | 11 | 5.47958e-06 | [1.692e-07, 4.756e-05] | 6.74426e-10 | True |

<sub>`the lift closed (check 3) — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.158.** *recomputed: iterations summed over attempts, evaluations summed over attempts[].sweeps_per_eval.n_evaluations, solve-phase node calls summed over attempts and their quotient, per arm over the seed set, with the B2/B0 per-seed ratio's mean, median, [min, max] and count above 1 n = 3 (configurations stacked, each over its own seed set — the n column: large_tokamak_nof 22 / low_aspect_ratio_DEMO 11 / st_regression 22 seeds on which every arm converged; never pooled).*

| quantity | configuration | arms | n | BR | B0 | B1 | B2 | ratio_mean | ratio_median | ratio_bracket | n_above_one |
|---|---|---|---|---|---|---|---|---|---|---|---|
| iterations (summed over attempts) | large_tokamak_nof | BR · B0 · B1 · B2 | 22 | 7.81818 | 7.81818 | 7.77273 | 7.77273 | 0.996392 | 1 | [0.875, 1.143] | 2 |
| evaluations of the model set, ε | large_tokamak_nof | BR · B0 · B1 · B2 | 22 | 614.727 | 614.727 | 640 | 640 | 1.04374 | 1.04762 | [0.908, 1.209] | 19 |
| node calls per evaluation, ρ | large_tokamak_nof | BR · B0 · B1 · B2 | 22 | 67.4888 | 69.1462 | 66.9394 | 42.481 | 0.614398 | 0.615854 | [0.600, 0.618] | 0 |
| node calls per run, R = ρ × ε | large_tokamak_nof | BR · B0 · B1 · B2 | 22 | 41479.8 | 42515.5 | 42841.9 | 27187.5 | 0.641385 | 0.645152 | [0.555, 0.746] | 0 |
| iterations (summed over attempts) | low_aspect_ratio_DEMO | BR · B0 · B1 · B2 | 11 | 29.8182 | 29.8182 | 20.9091 | 20.9091 | 1.38423 | 0.8125 | [0.129, 5.909] | 3 |
| evaluations of the model set, ε | low_aspect_ratio_DEMO | BR · B0 · B1 · B2 | 11 | 2345.45 | 2345.45 | 1714.36 | 1714.36 | 1.48158 | 0.846774 | [0.132, 6.450] | 3 |
| node calls per evaluation, ρ | low_aspect_ratio_DEMO | BR · B0 · B1 · B2 | 11 | 72.4906 | 70.1388 | 66.6274 | 43.3657 | 0.618292 | 0.619234 | [0.611, 0.620] | 0 |
| node calls per run, R = ρ × ε | low_aspect_ratio_DEMO | BR · B0 · B1 · B2 | 11 | 169943 | 164997 | 114154 | 74312.4 | 0.915576 | 0.523683 | [0.081, 3.980] | 2 |
| iterations (summed over attempts) | st_regression | BR · B0 · B2 | 22 | 31.1818 | 25.1364 | — | 23.9545 | 0.982797 | 1 | [0.246, 1.356] | 5 |
| evaluations of the model set, ε | st_regression | BR · B0 · B2 | 22 | 1846.36 | 1479.55 | — | 1407.27 | 0.982093 | 1 | [0.241, 1.360] | 5 |
| node calls per evaluation, ρ | st_regression | BR · B0 · B2 | 22 | 69.0146 | 71.1952 | — | 40.6929 | 0.572162 | 0.585836 | [0.534, 0.596] | 0 |
| node calls per run, R = ρ × ε | st_regression | BR · B0 · B2 | 22 | 126868 | 106007 | — | 56507.3 | 0.561574 | 0.59106 | [0.136, 0.753] | 0 |

<sub>`the optimiser's path over the configurations — campaign_optimisation`</sub>

**Table F.159.** *units: counts of predicate evaluations; the audit columns are hex floats of the largest scaled residual.  A row is one pair of runs — the same arm, configuration and seed under each ruler.  A column is a count of the trial, or one run's exit audit read on one named ruler.  Population: 12 pair(s) = 3 configuration(s) x the evaluation-phase arms active on each (A0, A2) x 2 seed(s), each run under both rulers = 24 runs at delta = 0.1; 8068 deterministic record values and 84 output-file lines compared without tolerance, 294 record values excluded as the setting being varied or as run metadata (each named, with its reason, in this record); 143 predicate evaluations observed on both rulers.  Construction: **read from the trial gate's verdict, not from run records** — the decisive-pass counts come from an observer that watches the run's own predicate evaluations and cannot be reconstructed from a record afterwards, so this recomputation checks the table's shaping and not the measurement.  Decisive passes are two counts, never one: crossings, and the verdict changes that alone can make two runs differ. n = 12 (pairs of runs, one per ruler).*

| configuration | arm | seed | evaluations | crossings | verdict_changes | identical | audit_frozen_run_frozen_ruler | audit_frozen_run_mixed_ruler | audit_mixed_run_frozen_ruler | audit_mixed_run_mixed_ruler |
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

<sub>`the predicate trial — frozen against mixed`</sub>

**Table F.160.** *units: counts of seeds.  A row is this configuration.  A column is the size of the one population every optimisation-phase table on this configuration is over, or a per-arm count of the seeds on which the optimiser was called more than once.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the arms here are BR, B0, B1, B2 at seeds 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24.  Construction: a seed is in the set when every arm present reached an accepted optimum (status ok AND the output file's ifail == 1); the retried count is computed from attempts[] and never from a stored flag.  This is one seed-complete arm group of the source — the plan's construction assumes every arm at every seed, which a gate's runs do not guarantee.  The seeds outside the set are the failure table, published beside. n = 25 (distinct seeds run on large_tokamak_nof).*

| arms | arm_names | seeds_offered | n | seeds | configuration_invalid | retried |
|---|---|---|---|---|---|---|
| 4 | BR · B0 · B1 · B2 | 25 | 22 | 0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 22, 23, 24 | 3 | BR 0 · B0 0 · B1 0 · B2 0 |

<sub>`the seed set — large_tokamak_nof — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.161.** *units: counts of seeds.  A row is this configuration.  A column is the size of the one population every optimisation-phase table on this configuration is over, or a per-arm count of the seeds on which the optimiser was called more than once.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the arms here are BR, B0, B1, B2 at seeds 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24.  Construction: a seed is in the set when every arm present reached an accepted optimum (status ok AND the output file's ifail == 1); the retried count is computed from attempts[] and never from a stored flag.  This is one seed-complete arm group of the source — the plan's construction assumes every arm at every seed, which a gate's runs do not guarantee.  The seeds outside the set are the failure table, published beside. n = 25 (distinct seeds run on low_aspect_ratio_DEMO).*

| arms | arm_names | seeds_offered | n | seeds | configuration_invalid | retried |
|---|---|---|---|---|---|---|
| 4 | BR · B0 · B1 · B2 | 25 | 11 | 0, 1, 5, 6, 9, 11, 12, 13, 15, 18, 19 | 13 | BR 12 · B0 10 · B1 10 · B2 10 |

<sub>`the seed set — low_aspect_ratio_DEMO — campaign_optimisation · BR·B0·B1·B2`</sub>

**Table F.162.** *units: counts of seeds.  A row is this configuration.  A column is the size of the one population every optimisation-phase table on this configuration is over, or a per-arm count of the seeds on which the optimiser was called more than once.  Population: campaign_optimisation — the campaign population: every optimisation-phase arm, 25 starts per configuration, seed000 unperturbed; a crashed start is a taxonomy row and never a cost; the arms here are BR, B0, B2 at seeds 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24.  Construction: a seed is in the set when every arm present reached an accepted optimum (status ok AND the output file's ifail == 1); the retried count is computed from attempts[] and never from a stored flag.  This is one seed-complete arm group of the source — the plan's construction assumes every arm at every seed, which a gate's runs do not guarantee.  The seeds outside the set are the failure table, published beside. n = 25 (distinct seeds run on st_regression).*

| arms | arm_names | seeds_offered | n | seeds | configuration_invalid | retried |
|---|---|---|---|---|---|---|
| 3 | BR · B0 · B2 | 25 | 22 | 0, 1, 2, 3, 4, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 18, 19, 20, 21, 22, 23, 24 | 1 | BR 5 · B0 3 · B2 2 |

<sub>`the seed set — st_regression — campaign_optimisation · BR·B0·B2`</sub>
