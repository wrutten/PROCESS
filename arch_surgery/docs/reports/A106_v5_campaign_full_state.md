# A106 (v5-campaign-full-state) — the V5 campaign under the whole write set at τ = 1e-6 (D39's fallback)

> **Document status** — **OPEN (task report, awaiting the orchestrator's assessment).** Task A106, branch
> `A106-v5-campaign-full-state`, worktree `.claude/worktrees/A106-v5-campaign-full-state`, from trunk `a1db0a0c`,
> 2026-10-01. A run task: no change to the driver copy (`MDA_partitioning_experiment_v5/PROCESS/`), to `process/` or to V4;
> no harness change. One script change (A104's `optimiser_path_split.py`, two options, §10). **Stopped early on the disk
> floor**: after the campaign and the first 16 gates, the Windows C: drive read 2.59 GB free, below the brief's 3 GB
> floor, and no further PROCESS run was made (§7, §9). Every number below comes from a committed entry point
> (`experiment_runner.py`, `paper_cells_recount.py`, `run_stamp_survey.py`, `st_stall_mechanism/optimiser_path_split.py`)
> at the commit named beside it; the press logs are under `MDA_partitioning_experiment_v5/runs/write_set_tau1e-06/_press_logs/A106/`
> (`pressNN_*.log`, `disk_log.txt`). **`runs/` was left where it is** in this worktree. Which campaign the paper's main
> tables carry is the user's open question (OQ-tolerance); nothing here recommends or rules on it.

## 1. Verdict and completion

**The campaign is complete: 553 of 553 records under run ID `write_set_tau1e-06`**, every one made at `a1db0a0c` with
W = 3, not dirty, run kind `campaign` (the stamp survey, below). The chain's reading stages ran inside the press and
passed, `tally_contracts` included (302 compared, 0 mismatched, 18/18 teeth). The tables document
`paper_tables_write_set_tau1e-06.md` is written and committed (`0022d648`), and `--paper-tables check --test-set write_set`
reads **IDENTICAL**; its cross-check is 0 mismatched of 178 cells, and `paper_cells_recount.py` recounts 44 cell rows with
0 mismatched.

**The gates are not complete.** `--gate all --resume --test-set write_set` stopped at its 16th gate,
`evaluation_warmup`, which FAILed. That gate compares records made under the census settings with records made under the
write set (§7). Pressing the remaining 13 gates one by one was then refused by the disk floor before the first started.
The gate table reads **18 PASS, 1 FAIL, 10 not run** of 29.

**The census campaign is unchanged.** `--jobs campaign --resume` (default settings) keeps 553 of 553, and
`--paper-tables check` (default) reads IDENTICAL against `paper_tables.md` (`press11`, `press12`, at `1487d04e`).

**The headline.** In phase B, this run's three main tables equal V4's published tables cell for cell: iterations, module
sweeps per optimisation, and seed sets 22 / 11 / 22 (§3, §4). The phase A arm means equal V4's. The phase A ratio column
differs from V4's only because the column is a different pair (`A2/A1`, D34, against V4's `A2/A0`).

**Records made, by stage and status** (`press02_campaign_W3.log`; population: the campaign press's 553 jobs):

| stage | jobs | ok | crashed (status) | resumed |
|---|---:|---:|---:|---:|
| entry references | 3 | 3 | 0 | 0 |
| displaced-entry evaluations (phase A) | 275 | 275 | 0 | 0 |
| optimisations (phase B) | 275 | 247 | 28 | 0 |
| all | 553 | 525 | 28 | 0 |

The 28 crashed records are 20 `RuntimeError` (the same 20 starts as in the census campaign) and 8
`ModuleSolveFailure` at the coupling loop's sweep cap on `lad` (§6). `--jobs campaign --test-set write_set --resume`
after the press keeps 553 of 553 (`press13`): every crashed record is complete as a crash (I-38, A105).

**Stamp survey** (`run_stamp_survey.py --runs runs/write_set_tau1e-06 --launch-summary campaign`, `press15`, at `1487d04e`;
population: the 553 campaign records):

| group | n | commit | W | dirty | one-minute load at spawn, min / median / max |
|---|---:|---|---|---:|---|
| entry references | 3 | `a1db0a0c` | 3 | 0 | 0.15 |
| evaluation `tok` / `lad` / `st` | 100 / 100 / 75 | `a1db0a0c` | 3 | 0 | 1.97 / 3.08 / 3.41; 3.29 / 3.40 / 3.52; 3.21 / 3.31 / 3.51 |
| optimisation `tok` / `lad` / `st` | 100 / 100 / 75 | `a1db0a0c` | 3 | 0 | 3.04 / 3.18 / 3.48; 3.03 / 3.19 / 3.45; 3.08 / 3.19 / 3.46 |

All 553 records saw a one-minute load average above 1.5 at spawn or at return: three children ran at once. The folder
holds 713 run records in all. The other 160 are A107's smoke and the copied read-only gate records (at 13 older commits),
plus the 16 gate records this task made at `a1db0a0c`.

**The presses, in order** (all from `MDA_partitioning_experiment_v5/`, `PROCESS_surgery_env`, `PYTHONDONTWRITEBYTECODE=1`):

| # | command | when | outcome |
|---|---|---|---|
| 01 | `--jobs campaign --test-set write_set --resume` | 11:13 | 278 listed (275 evaluations follow once the entry references exist), 0 kept |
| 02 | `HARNESS_WORKERS=3 … --campaign --test-set write_set --resume` | 11:14:01 – 12:34:09 | 553 made, chain PASS, rc 0 |
| 03 | `--test-set write_set --reading-stages campaign-press --resume --outdir runs/write_set_tau1e-06/reading_stages/campaign_press` | 12:34 | 42 + 52 tables; `tally_contracts` PASS 302 / 0, 18/18 |
| 04 | `--test-set write_set --jobs all --resume` | 12:35 | 673 distinct jobs over 29 gates, 25 kept |
| 05 | `HARNESS_WORKERS=3 … --test-set write_set --gate all --resume` | 12:35:19 – 12:43:14 | 15 PASS, then `evaluation_warmup` FAIL; the chain stops (rc 1) |
| 06 | the 13 later gates one by one, `--gate <name> --resume` | 12:43:45 | **refused by the disk floor before the first** (C: 2 599 MB free) |
| 07 | `--test-set write_set --measure gate_table --resume` | 12:44 | 18 PASS, 1 FAIL, 10 not run |
| 08 | `--test-set write_set --timing validity`, `--timing cache-load` | 12:44 | no PROCESS run (§8) |
| 09–10 | `--test-set write_set --paper-tables write`, then `check` (after commit `0022d648`) | 12:44 – 12:45 | written; IDENTICAL |
| 11–12 | `--jobs campaign --resume`, `--paper-tables check` (default run ID) | 12:45 | 553 / 553 kept; IDENTICAL |
| 13–17 | `--jobs campaign` (write set), `paper_cells_recount.py`, `run_stamp_survey.py`, `optimiser_path_split.py`, `--runs` | 12:45 – | §1, §5, §9 |

## 2. The tally per rule (plan §5)

From the chain's reading stages in the campaign press (stage records `runs/write_set_tau1e-06/gates/tally_{evaluation,optimisation}/measurements.json`,
at `a1db0a0c`; re-pressed identically by `press03`). Phase A's population is the 275 displaced-entry evaluations, 25 per
arm per configuration. Phase B's is the 275 optimisations, each table over the configuration's **seed set**: the seeds on
which every arm reached an accepted optimum. That is 22 (`tok`), 11 (`lad`) and 22 (`st`); the census campaign's was
22 / 12 / 20.

- **A1, matched accuracy (whole state, D36): PASS on all three configurations.** Whole-state audit, median / p90 per arm, over 25 runs:
  `tok` A1 3.833e-10 / 1.671e-08, A2 the same, so `A2/A1` is 1.00 / 1.00; `lad` every arm exactly 0 (the
  trivially-similar clause); `st` A0 5.372e-09 / 2.023e-08, A2 the same, so `A2/A0` is 1.00 / 1.00. **0 runs with a
  component ≥ τ (1e-6) in any arm on any configuration**, 25/25 per arm. Beside them (not the declared pair): `tok` `A2/A0`
  1.63 / 2.10; AR's audit is 3.3e-08 / 4.1e-07 (`tok`) and 1.5e-07 / 2.8e-07 (`st`).
- **A2, fixed-point distance (reported).** On the headline pair, restricted statistic median / p90, over 25 seed pairs:
  `tok` `A2/A1` 5.1e-12 / 1.8e-10, 0 of 25 pairs ≥ τ; `lad` 0 / 0, 0 of 25; `st` `A2/A0` 1.2e-11 / 4.6e-11, 0 of 25.
  The burn-time rung `A1/A0` is above τ on 25 of 25 pairs on both pulsed configurations (9.7e-02 / 2.0e-01 `tok`,
  7.0e-02 / 1.6e-01 `lad`).
- **A3, cost (the paper's phase A pair, module sweeps per evaluation, 25 pairs).** `tok` `A2/A1`: M1 0.78, M2 1.01,
  M3 0.59, Feedforward 0.20, Post-processing 0.20. `lad` `A2/A1`: 0.81 / 0.99 / 0.61 / 0.20 / 0.20. `st` `A2/A0`:
  0.68 / 1.00 / 0.51 / — / 0.17. Node calls per evaluation, pooled: `tok` `A2/A1` 0.5904; `lad` 0.6063; `st` `A2/A0`
  0.5342 (the tally's `cost per call` tables).
- **B1, same optimum** (`same optimum by rung`; yardstick `BR → B0`, F = 10, floor 1e-6):
  - **`tok` PASS** on `B0 → B1` and `B0 → B2`: r median 2.8e-11, p90 4.6e-11, 0 hops of 22.
  - **`lad` FAIL at p90 on both** (median 4.1e-07, p90 2.1e-06 > 1e-06): 3 hops of 11 (seeds 1*, 11, 13), entering at
    `B0 → B1` (the lift) 3 of 3. `B1 → B2` (the partition) reads median 0, p90 2.7e-14, the same path on 11 of 11. The
    yardstick hops on 0 of these 3 seeds.
  - **`st` PASS** on `B0 → B2` (median 3.5e-13, p90 3.5e-09): 1 hop of 22 (seed 12), against the yardstick's 2 hops
    (seeds 12*, 24*). The yardstick also hops on that seed (1 of 1).
- **B2, cost** (`cost sums (check 4)`; solve-phase node calls summed over the seed set, with the audit's sweep subtracted
  symmetrically). `B2/B0`:
  - `tok` **0.6395** (n = 22; the same without retried seeds);
  - `lad` **0.4504** (n = 11), and **0.6594** without the one retried seed (n = 10);
  - `st` **0.5331** (n = 22), and **0.6150** without retried seeds (n = 19).
- **B3, `R = ρ × ε`** (`the optimiser's path over the configurations`, `B2/B0`, the seed set):

  | configuration | n | ρ (node calls per evaluation) | ε (evaluations) | R | iterations B2/B0 | label |
  |---|---:|---:|---:|---:|---:|---|
  | `tok` | 22 | 0.6144 | 1.0411 | 0.6395 | 0.9942 | trajectory-neutral (\|log ε\| ≤ log 1.05) |
  | `lad` | 11 | 0.6183 | 0.7309 | 0.4504 | 0.7012 | trajectory changed by ε |
  | `st` | 22 | 0.5716 | 0.9512 | 0.5331 | 0.9530 | trajectory-neutral |

  *Population: the seed set per configuration. ε is the ratio of the means of `n_evaluations` summed over attempts. The
  label is the plan's B3 label, never a verdict.* `lad`'s ε is the lift's. `B1` and `B2` are identical in evaluations and
  iterations on 11 of 11 pairs (`the identity B1 → B2`), and bit-identical in the objective on 8 of 11.
- **B4, lift closed.** The constraint-93 residual is in the tally's stage record. It is not re-quoted here (no rule
  reads it).
- **B5, per-arm success, of 25** (`per-arm success`; the tables document, lines 411–433):
  - `tok`: 22 in every arm (seeds 5, 20, 21 crash in every arm).
  - `lad`: `BR` 12, `B0` 12, `B1` 11, `B2` 11. Seed 10 is lost to `B1` and `B2` (a coupling-loop cap) and accepted by `BR`
    and `B0`.
  - `st`: `BR` 24, `B0` 23, `B2` 23. Seed 10 is lost to `B0` alone and seed 5 to `B2` alone (both `ifail = 5`); seed 17
    is `ifail = 5` in every arm.

## 3. The three campaigns side by side

Each cell is quoted verbatim from a committed tables document, with its line:

- **V4**: `arch_surgery/MDA_partitioning_experiment_v4/paper_tables.md`, the numbers in the paper.
- **V5 census**: `arch_surgery/MDA_partitioning_experiment_v5/paper_tables.md`, the census set at 1e-8.
- **V5 write set**: `arch_surgery/MDA_partitioning_experiment_v5/paper_tables_write_set_tau1e-06.md`, this run.

Each phase A cell lists the four arm means first, then the pair's ratio. **The ratio column is a different pair in V4**
(`A2/A0`) from V5 (`A2/A1` on the pulsed configurations, `A2/A0` on `st`, D34).

**Phase A, module sweeps per evaluation (n = 25 per arm). Cells: AR / A0 / A1 / A2 · ratio.**

| config | module | V4 (`A2/A0`) | V5 census (`A2/A1`; `st` `A2/A0`) | V5 write set (same pair as census) |
|---|---|---|---|---|
| `tok` | M1 | L47: 5.0 / 5.5 / 5.1 / 4.0 · 0.72 | L87: 5.0 / 5.9 / 5.9 / 3.0 · 0.51 | L89: 5.0 / 5.5 / 5.1 / 4.0 · 0.78 |
| `tok` | M2 | L48: 5.0 / 5.5 / 5.1 / 5.2 · 0.93 | L88: 5.0 / 5.9 / 5.9 / 5.9 · 1.00 | L90: 5.0 / 5.5 / 5.1 / 5.2 · 1.01 |
| `tok` | M3 | L49: … / 3.0 · 0.54 | L89: … / 2.0 · 0.34 | L91: … / 3.0 · 0.59 |
| `tok` | Feedforward | L50: 1 · 0.18 | L90: 1 · 0.17 | L92: 1 · 0.20 |
| `tok` | Post-processing | L51: 1 · 0.18 | L91: 1 · 0.17 | L93: 1 · 0.20 |
| `lad` | M1 | L57: 5.0 / 5.0 / 4.9 / 4.0 · 0.80 | L97: 5.0 / 5.0 / 5.0 / 3.0 · 0.60 | L99: 5.0 / 5.0 / 4.9 / 4.0 · 0.81 |
| `lad` | M2 | L58: … / 4.9 · 0.98 | L98: … / 5.0 · 1.00 | L100: … / 4.9 · 0.99 |
| `lad` | M3 | L59: … / 3.0 · 0.60 | L99: … / 2.0 · 0.40 | L101: … / 3.0 · 0.61 |
| `lad` | Feedforward | L60: 1 · 0.20 | L100: 1 · 0.20 | L102: 1 · 0.20 |
| `lad` | Post-processing | L61: 1 · 0.20 | L101: 1 · 0.20 | L103: 1 · 0.20 |
| `st` | M1 | L67: 4.9 / 5.8 / — / 4.0 · 0.68 | L107: 4.9 / 6.0 / — / 3.0 · 0.50 | L109: 4.9 / 5.8 / — / 4.0 · 0.68 |
| `st` | M2 | L68: … / 5.8 · 1.00 | L108: … / 6.0 · 1.00 | L110: … / 5.8 · 1.00 |
| `st` | M3 | L69: … / 3.0 · 0.51 | L109: … / 3.0 · 0.50 | L111: … / 3.0 · 0.51 |
| `st` | Post-processing | L71: 1 · 0.17 | L111: 1 · 0.17 | L113: 1 · 0.17 |

**Phase B, optimiser iterations** (summed over attempts, over the seed set):

| config | V4 | V5 census | V5 write set |
|---|---|---|---|
| `tok` | L111: n 22 · 7.8 / 7.8 / 7.8 / 7.8 · 0.99 · 1.00 [0.88, 1.14] | L151: n 22 · 7.8 / 7.8 / 7.8 / 7.8 · 0.99 · 1.00 [0.88, 1.14] | L153: n 22 · 7.8 / 7.8 / 7.8 / 7.8 · 0.99 · 1.00 [0.88, 1.14] |
| `lad` | L112: n 11 · 29.8 / 29.8 / 20.9 / 20.9 · 0.70 · 0.81 [0.13, 5.91] | L152: n 12 · 28.2 / 28.2 / 38.6 / 38.6 · 1.37 · 0.83 [0.13, 21.18] | L154: n 11 · 29.8 / 29.8 / 20.9 / 20.9 · 0.70 · 0.81 [0.13, 5.91] |
| `st` | L113: n 22 · 31.2 / 25.1 / — / 24.0 · 0.95 · 1.00 [0.25, 1.36] | L153: n 20 · 29.5 / 20.8 / — / 49.9 · 2.40 · 2.21 [0.56, 5.21] | L155: n 22 · 31.2 / 25.1 / — / 24.0 · 0.95 · 1.00 [0.25, 1.36] |

*Cells: n · BR / B0 / B1 / B2 · B2/B0 ratio of means · per-run median [min, max].*

**Phase B, module sweeps per optimisation. Cells: B2/B0 ratio of means, M1 / M2 / M3 / Feedforward.**

| config | V4 | V5 census | V5 write set |
|---|---|---|---|
| `tok` | L135–138: 0.68 / 0.87 / 0.76 / 0.32 (n 22) | L175–178: 0.54 / 0.88 / 0.54 / 0.30 (n 22) | L177–180: 0.68 / 0.87 / 0.76 / 0.32 (n 22) |
| `lad` | L145–148: 0.47 / 0.59 / 0.54 / 0.22 (n 11) | L185–188: 0.72 / 1.21 / 0.77 / 0.42 (n 12) | L187–190: 0.47 / 0.59 / 0.54 / 0.22 (n 11) |
| `st` | L155–157: 0.64 / 0.67 / 0.66 / — (n 22) | L195–197: 1.36 / 2.02 / 1.44 / — (n 20) | L197–199: 0.64 / 0.67 / 0.66 / — (n 22) |

The module means behind those ratios, BR / B0 / B1 / B2 of M1:
- `tok`: V4 L135 `1977 | 2027 | 2040 | 1388`; census L175 `1977 | 2116 | 2055 | 1147`; write set L177 `1977 | 2027 | 2040 | 1388`.
- `lad`: V4 L145 `8095 | 7859 | 5436 | 3670`; census L185 `7662 | 7623 | 10124 | 5513`; write set L187 `8095 | 7859 | 5436 | 3670`.
- `st`: V4 L155 `6043 | 5050 | — | 3250`; census L195 `5734 | 3895 | — | 5302`; write set L197 `6043 | 5050 | — | 3250`.

**Accepted optima of 25 per arm.** V4's document carries no success table.

| config | V5 census (L411–431) | V5 write set (L413–433) |
|---|---|---|
| `tok` | BR 22, B0 22, B1 22, B2 22 | BR 22, B0 22, B1 22, B2 22 |
| `lad` | BR 12, B0 12, B1 12, B2 12 | BR 12, B0 12, B1 11, B2 11 |
| `st` | BR 24, B0 24, B2 20 | BR 24, B0 23, B2 23 |

**Partitioned and flat over the reference** (solve-phase node calls per run over the seed set; the tally's `cost against
both anchors`). No tables document carries these ratios. V4's does not, and the two V5 documents print the module means
only. The census values are quoted from A102's committed Appendix B (`A102_v5_campaign.md` L2318–2322); this run's are
from its own stage record (`press03`):

| config | census: BR→B0 · B2/B0 · B2/BR | write set: BR→B0 · B2/B0 · B2/BR |
|---|---|---|
| `tok` | 1.0700 · 0.5020 · 0.5371 (n 22) | 1.0250 · 0.6395 · 0.6554 (n 22) |
| `lad` | 0.9950 · 0.7031 · 0.6995 (n 12) | 0.9709 · 0.4504 · 0.4373 (n 11) |
| `st` | 0.6791 · 1.2419 · 0.8434 (n 20) | 0.8356 · 0.5331 · 0.4454 (n 22) |

*Each ratio is over its own campaign's seed set, so the two columns are over different seeds where n differs.*

**The configurations table** ("Models"): V4 L23–25 print **51**, both V5 documents **52** (census L63–65, write set
L65–67). This is D40, a reporting decision, not a measurement.

## 4. Against V4

Per table, over the cells quoted in §3:

- **Phase B iterations, `tab:phaseB_iterations`: every cell equals V4's.** That is 3 rows × 8 cells: n, the four arm
  means, the ratio, the median and the bracket.
- **Phase B module sweeps, `tab:phaseB_results`: every cell equals V4's.** That is 3 configurations × 5 rows × 6 cells,
  compared line by line on L177–201 against V4 L135–159; the seed sets are the same (22 / 11 / 22).
- **Phase A module sweeps, `tab:phaseA_results`: every arm-mean cell equals V4's** (AR, A0, A1, A2 on every module and
  configuration). **The ratio and bracket columns differ** wherever V5's pair differs from V4's:
  - On `tok` and `lad` the column is `A2/A1` in V5 and `A2/A0` in V4 (D34), so the two columns are ratios of different
    pairs over the same arm means. For example, `tok` M1 is 4.0 / 5.1 = 0.78 here and 4.0 / 5.5 = 0.72 in V4.
  - On `st` the pair is `A2/A0` in both, and the ratio cells are equal (0.68, 1.00, 0.51, 0.17).
  - **The brackets differ on the pulsed configurations** for the same reason (a different denominator arm per run).
  - This is a change of reporting, not of measurement. **Not attributed to a driver change.**
- **Configurations table**: Models 51 → 52 (D40, reporting).
- **Per-arm success, the wall-clock tables, the verification table**: V4's document has none of these. No comparison.

**Attribution.** In the main-text count tables, no difference from V4 remains to be attributed to a driver change.
V5's driver changes against V4 are the once-per-evaluation prime (DR10), the once-per-run schedule (DR9) and phase A's
single execution of the deferred set (item 5). The only phase A cell those could move in the paper's tables is `A2`'s
Post-processing, which reads 1 in both: charged by construction in V4, measured in V5. The other differences are the
ratio pair (D34) and Models (D40). No arithmetic attribution was needed, and none was made.

## 5. `st_regression`, the partitioned arm

A104's committed script, pointed at this run ID:
`optimiser_path_split.py --runs runs/write_set_tau1e-06 --campaign-only --campaign-label ws1e-6` at `1487d04e` (`press16`).
The two options are this task's (§10). Without them the script's output over `runs/census_tau1e-08` is byte-identical to
the committed script's. The labels `B0@ws1e-6` and `B2@ws1e-6` are this campaign's `B0` and `B2`. No supplementary stage
exists under this run ID.

**Accepted starts and near-band behaviour per arm** (population: 25 starts per arm; "accepted" = final `ifail = 1`):

| arm | accepted | of which in one attempt | final measure median [min, max] | n_near median [min, max] | hovering (n_near > 10) |
|---|---:|---:|---|---|---|
| BR | 24 | 20 | 6.0e-10 [7.4e-11, 9.8e-10] | 4.5 [0, 75] | 7 of 24 |
| B0 | 23 | 22 | 5.9e-10 [8.1e-11, 9.8e-10] | 5 [0, 21] | 7 of 23 |
| B2 | 23 | 23 | 6.1e-10 [1.0e-10, 9.9e-10] | 3 [0, 16] | 8 of 23 |

**`B0 → B2`, classes over 25 starts** (A104's rule, declared in the script): identical 1, early 7, stall 1, shorter 12,
retried 4. Retried runs: BR 5 of 25 finished, B0 3, B2 2. Node calls per evaluation over the seed set (n = 22): `B2` 40.2,
`B0` 71.6, `BR` 68.7, so `B2` is 0.56 of `B0` and 0.58 of `BR`.

**Iterations per seed, attempt 1, `B0` / `B2`** (with attempts and final `ifail` where an arm was retried), and the
largest relative difference of the final iteration variables between the two arms. Both arms are accepted except where
marked. The rows are from the script's per-seed table:

| seed | iterations B0 / B2 | x max rel diff (variable) | | seed | iterations B0 / B2 | x max rel diff (variable) |
|---:|---|---|---|---:|---|---|
| 0 | 10 / 10 | 2.3e-07 (dr_shld_inboard) | | 13 | 14 / 14 | 1.0e-07 |
| 1 | 53 / 59 | **1.8e-01 (dr_tf_nose_case)** | | 14 | 22 / 22 | 1.1e-05 |
| 2 | 27 / 39 (B0 2 attempts) | **8.9e-02 (dr_shld_inboard)** | | 15 | 60 / 72 | **2.1e-01 (dr_tf_nose_case)** |
| 3 | 18 / 18 | 3.0e-06 | | 16 | 25 / 26 | 4.2e-05 |
| 4 | 20 / 20 | 4.5e-06 | | 17 | 0 / 0 (4 / 4 attempts, ifail 5 / 5) | — |
| 5 | 42 / 73 (B2 3 attempts, **B2 ifail 5**) | — | | 18 | 13 / 13 | 3.6e-10 |
| 6 | 18 / 18 | 8.7e-06 | | 19 | 14 / 11 | 2.5e-06 |
| 7 | 10 / 10 | 1.1e-08 | | 20 | 14 / 14 | 8.1e-06 |
| 8 | 12 / 12 | 8.3e-08 | | 21 | 10 / 10 | 1.2e-09 |
| 9 | 45 / 61 | **7.5e-02 (dr_tf_nose_case)** | | 22 | 12 / 12 | 2.0e-09 |
| 10 | 65 / 60 (B0 3 attempts, **B0 ifail 5**) | — | | 23 | 11 / 11 | 9.5e-07 |
| 11 | 11 / 11 | 1.2e-09 | | 24 | 44 / 47 | **2.6e-01 (dr_tf_nose_case)** |
| 12 | 69 / 17 | **1.0e+00 (f_nd_impurity_electrons(13))**; objective differs by 1.3e-02 | | | | |

*Population: 25 starts. The x difference is context only (D6: some iteration variables are not identified by the
problem).* **Does B2 end at B0's design?** On the 22 starts where both arms are accepted, 6 rows (seeds 1, 2, 9, 12, 15, 24)
show a final iteration variable more than 1e-3 apart. On 5 of them the objective agrees to within 1e-8 relative (6.3e-09,
9.2e-12, 6.8e-11, 6.3e-12, 3.5e-09). Seed 12 differs in the objective by 1.3e-02 (the one hop of §2 B1). On the other
16 starts, every final iteration variable is within 1e-4 relative.

**Where the accepted runs end, at a bound** (iteration variables within one finite-difference step of a bound the input
file sets; population: the accepted runs per arm):

| arm | runs judged | variable: runs at the bound |
|---|---|---|
| BR | 24 of 24 | `f_nd_plasma_pedestal_greenwald` lower 0.1: 24; `f_nd_plasma_separatrix_greenwald` lower 0.001: 24; `hfact` upper 1.2: 24 |
| B0 | 23 of 23 | the same three: 23 each |
| B2 | 23 of 23 | the same three: 23 each; **`dr_tf_wp_with_insulation` upper 0.8: 5** |

**`dr_tf_nose_case` ends at its lower bound in 0 of 23 `B2` runs here**, against 10 of 20 under the census set at 1e-8
(A104). `dr_tf_wp_with_insulation` at its upper bound appears in `B2` alone: 5 of 23 accepted runs (seeds 1, 9, 10, 15,
24; the bound list also names it on seed 5, which `B2` did not accept), in no `BR` or `B0` run. This section reports what
the records show; it does not explain it.

## 6. Failure taxonomy per phase and arm

**Phase A** (population: 25 displaced-entry evaluations per arm; the tally's `failure taxonomy — campaign_displaced`):
every arm on every configuration reads 25 of 25 `ok`. The 3 entry references are `ok`.

**Phase B** (population: 25 starts per arm; `failure taxonomy` and `per-arm success — campaign_optimisation`):

| config | arm | accepted (`ifail = 1`) | finished `ifail = 5` | crashed: `RuntimeError` | crashed: coupling-loop cap (`ModuleSolveFailure`) |
|---|---|---:|---:|---:|---:|
| `tok` | BR, B0, B1, B2 (each) | 22 | 0 | 3 (seeds 5, 20, 21) | 0 |
| `lad` | BR | 12 | 11 (2, 4, 7, 8, 14, 16, 17, 20, 22, 23, 24) | 2 (3, 21) | 0 |
| `lad` | B0 | 12 | 9 | 2 (3, 21) | 2 (4, 22) |
| `lad` | B1 | 11 | 9 | 2 (3, 21) | 3 (4, 10, 22) |
| `lad` | B2 | 11 | 9 | 2 (3, 21) | 3 (4, 10, 22) |
| `st` | BR | 24 | 1 (17) | 0 | 0 |
| `st` | B0 | 23 | 2 (10, 17) | 0 | 0 |
| `st` | B2 | 23 | 2 (5, 17) | 0 | 0 |

- **The 20 `RuntimeError` crashes** are the census campaign's 20 starts (`tok` 5, 20, 21 and `lad` 3, 21 in every arm),
  with the same last line: `RuntimeError: Failed to converge after 50 iterations, value is nan.` (A102 §8.1:
  `scipy.optimize.newton` at `superconducting.py:1266`).
- **The 8 coupling-loop caps are new in V5** (under the census set those `lad` starts finished `ifail = 5`; V4's document
  carries no success table). Each record's traceback ends at `PROCESS/process/core/caller.py:2016`
  (`_call_models_partitioned`, `raise module_solve.ModuleSolveFailure`). The message is "block FLAT did not converge in
  20 sweeps at tau=1e-06; max scaled residual inf on `current_drive.eta_cd_dimensionless_hcd_primary`, 1 components
  above tau" (`B0`, `B1`; the block is `M1` on `B2`). The run's `stderr.log` carries a `RuntimeWarning: invalid value
  encountered in scalar divide` at `PROCESS/process/models/physics/current_drive.py:2387` (`c_hcd_driven /
  p_hcd_injected`).
- Seed 10's cap on `B1` and `B2` came from the gradient (`evaluators.py:150`, `fcnvmc2`). Seeds 4 and 22 came from a
  function evaluation (`evaluators.py:71`, `fcnvmc1`).
- `BR`, whose loop stops on upstream's objective-and-constraint test, finishes those starts `ifail = 5` and does not reach
  the cap.
- The record class is `status = crashed`, `failure_class = unconverged`, which `--resume` keeps as complete (I-38).

## 7. The gate table

**Under `write_set_tau1e-06`** (`--measure gate_table --resume --test-set write_set` at `a1db0a0c`, `press07`;
record `runs/write_set_tau1e-06/gates/gate_table/measurements.json`):

| verdict | gates |
|---|---|
| **PASS (18)**, pressed by this task at `a1db0a0c` | `g0prime` (1 of 77, the approved model file; 4/4), `copy_identity`, `edit_behaviour`, `self_containment`, `composition`, `rungs`, `provenance`, `data`, `run_path`, `resume_identity`, `capability`, `artifacts_check`, `artifacts_derive_inputs`, `artifacts_census`, `artifacts_per_run` (`press05`), and `tally_contracts` (302 / 0, 18/18, in the campaign press) |
| **PASS**, verdicts on disk from A107 (`ce84a759`) | `count_neutrality` (GC; reads its archived `item5 → DR12` straddle), `reproduction` (GR; its copy-commit verdict at `d6c246a1`) |
| **FAIL (1)** | `evaluation_warmup`: 254 of 1 430 count leaves and 2 002 of 18 450 exit-state components differ over 11 pairs; tooth "a doctored count on one record" DID NOT TRIP, tooth "a doctored warm-up count" TRIPPED |
| **NOT RUN (10)** | `record_completeness` (G7), `prime_map` (G2), `entry_and_warm` (G6), `test_set` (GT), `switch_composition` (G5), `switch_neutrality` (G1), `output_path` (G9), `written_file_gap`, `run_kind_separation`, `stage_provenance` |

**The FAIL's cause, by function and line.**
- `gate_evaluation_warmup.body` (`harness/gates/gate_evaluation_warmup.py:271–288`) reads its before side from
  `before_archive(campaign, …)` (line 103), `runs/write_set_tau1e-06/gates/evaluation_warmup/before/<configuration>/A_<arm>/`.
  That is A107's copy of the census run ID's archive: the cold-child records made at `24b78e2d` / `d08e8ab4`, which
  stamp `campaign_test_set = census` and `campaign_tau = 1e-08`.
- The after side is composed under this run ID's campaign (`after_jobs(campaign, …)`, line 274): the write set at 1e-6.
- `gc_mod.compare_counts(before, after)` (line 288) compares two loops that stop on different tests, so the counts differ.
- The first tooth cannot trip, because the pair already differs before the doctoring.
- A107 §7 L2 named this gate as one that reads an archive made under census settings. The gate was not changed, and it
  was not re-pressed.

**Why 10 are not run.** `--gate all` stops at the first failed gate by design ("the chain stops here"). I then started the
13 later gates one at a time (decision 2, §10). The loop checks C: before each gate, and found 2 599 MB free before the
first, below the 3 GB floor. It made no run. Those 13 include GC and GR, which kept their A107 verdicts, and
`tally_contracts`, which kept the campaign press's.

**What the tables document's verification table reads**: G0 PASS, A1 PASS, B1 "PASS tok, st · FAIL lad", A2 reported;
G1, G6, G5, G9 and GT **not pressed** (`paper_tables_write_set_tau1e-06.md` L443–451). GT is refused under the fallback
by design (README §5).

**Under `census_tau1e-08`, unchanged** (`--runs`, `press17`): gate table **29 PASS of 29 (0 FAIL, 0 not run)**, written
2026-10-01T11:06:48 (A108). No gate was pressed under that run ID by this task. Its verification table is
`paper_tables.md` L439–451: G0, G1, A1, G6, G5, G9 and GT PASS; B1 "PASS tok · FAIL lad, st".

## 8. Wall-clock appendix tables (context, never evidence)

**What the generator needed, and what was made.**
- `--paper-tables write` refuses without two timing stage records under the run ID: `paper_tables.wall_clock_source`
  needs `timing/validity/measurements.json`, and `_cache_load_sentence` needs `timing/cache_load/measurements.json`.
- `--timing cache-load` reads the campaign's own records only.
- `--timing validity` compares the campaign with the repeatability stage's W = 1 records. That stage is a one-worker pass
  (66 runs), which the brief excludes, so none exists under this run ID.
- **I pressed both stages, which make no PROCESS run** (`press08`). The validity record says "no repetition record" for
  each of its 22 jobs, and "appendix timings from: not decidable yet".
- The document therefore prints the validity table with every cell `—`, and the sentence "found 0 … within … and 0
  outside" (L241–268). By D42 the tables are the campaign's own records either way (`WALL_CLOCK_TIMINGS_FROM =
  "campaign"`).
- The phase B caption's cache-load sentence reads 0.24–0.40 s per run, 0.9–3.2 % of module time per run (L272).

**Totals, as generated** (W = 3 as stamped; pairing key the seed; phase A over 25 pairs, phase B over the count tables'
seed set; ratio of means and per-run median [min, max]; `paper_tables_write_set_tau1e-06.md`):

| table | config | AR / BR | A0 / B0 | A1 / B1 | A2 / B2 | ratio | median [min, max] | line |
|---|---|---:|---:|---:|---:|---:|---|---|
| phase A, ms per evaluation (`A2/A1`; `st` `A2/A0`) | `tok` | 42.09 | 70.75 | 67.71 | 54.64 | 0.81 | 0.79 [0.54, 1.36] | L289 |
| | `lad` | 38.47 | 69.89 | 63.18 | 52.82 | 0.84 | 0.85 [0.43, 1.52] | L332 |
| | `st` | 36.44 | 69.92 | — | 51.29 | 0.73 | 0.77 [0.46, 0.86] | L375 |
| phase B, s per optimisation (`B2/B0`) | `tok` (22) | 20.92 | 33.33 | 32.21 | 26.05 | 0.78 | 0.80 [0.62, 0.94] | L306 |
| | `lad` (11) | 72.64 | 109.97 | 75.78 | 60.86 | 0.55 | 0.67 [0.10, 4.34] | L349 |
| | `st` (22) | 53.73 | 71.20 | — | 47.83 | 0.67 | 0.72 [0.19, 0.98] | L392 |

The full row tables (modules, convergence test, dispatch, objective and constraints, optimiser, fixed per run, residual)
and the cost breakdowns are at L276–403 of the document. No validity check backs them (no W = 1 repetitions exist under
this run ID). The census campaign's corresponding Totals, made at W = 3 and 4, are in `paper_tables.md` L287–390.

## 9. Disk log

From `runs/write_set_tau1e-06/_press_logs/A106/disk_log.txt` (`df -h /mnt/c`, and the virtual disk file's size as
`ls -la` / `stat` read it through `/mnt/c`):

| when | stage | C: free | `ext4.vhdx` size (bytes) |
|---|---|---|---|
| 11:13:54 | start, before the campaign | 8.7 GB | 229 147 410 432 |
| 11:15 – 12:25 (8 readings) | during the campaign | "9G" (`df -BG`, rounded up) | 229 147 410 432 |
| 12:34:22 | after the campaign | 5.1 GB | 229 147 410 432 |
| 12:35:03 | before `--gate all` | 5.1 GB | 229 147 410 432 |
| 12:43:45 | before the 13 later gates | **2 599 MB: below the floor; no run made** | — |
| 12:43:55 | recheck | 2 594 MB | 229 147 410 432 |
| 12:45:27 | end of run stages | 2 593 MB | 229 147 410 432 |

**The run ID's size** (`--runs`, `press17`): `write_set_tau1e-06` 1.49 GB on disk, of which the campaign 1.16 GB. It held
0.30 GB before this task (A108). `census_tau1e-08` 2.78 GB, of which its campaign 1.20 GB, unchanged.

**The user's question, whether new writes reuse freed space or grow the disk.** As read through `/mnt/c`, the virtual
disk file's size did not change at any reading: 229 147 410 432 bytes at start and at end, and `du` reports the same
allocated size. Over the same time:
- C: lost about 6.1 GB of free space (8.7 GB → 2.59 GB);
- this run ID grew by about 1.2 GB;
- the Linux root filesystem's used space rose from 95 GB to about 95.8 GB (`df /`).

From inside WSL I cannot tell where the 6.1 GB went. Either the file's size as reported through `/mnt/c` does not follow
its growth while it is open, or something on the Windows side wrote to C:. The figures are reported as read, not
explained. The 3.6 GB drop between 12:25 and 12:34 came while the press wrote its last ~25 records and the tally stage
records.

## 10. Decisions taken alone, each with its reversal; limits; the unexpected

**Decisions.**
1. **The wall-clock stages without a one-worker pass** (§8). I pressed `--timing validity` with no repeatability records,
   so it records "no repetition record" for each job, and `--timing cache-load`. Both are the minimum the committed entry
   point offers and make no PROCESS run. Reversal: delete `runs/write_set_tau1e-06/timing/{validity,cache_load}/`. The
   tables document then refuses to render until a later task presses them, or presses `--timing repeatability` first.
2. **The gates after the failed one were started one by one** (`--gate <name> --resume`). `--gate all` stops at its
   first FAIL, and the brief asks for the gate table as it reads. Reading the other gates' own verdicts does not touch the
   failed one. None ran (the disk floor). Reversal: none needed. The loop's log, `press06_gates_after_warmup.started`,
   shows the refusal.
3. **Read-only stages after the disk floor.** I took the floor as "stop making PROCESS runs" and continued the stages
   that make none, each writing a few kB to 1 MB: the gate table, the two timing stages, the tables document and its
   check, the recount, the stamp survey, A104's script and the listings. C: read 2 593 MB before and after them.
   Reversal: delete the stage records named in §1 and the tables document commit `0022d648`.
4. **`optimiser_path_split.py` gains `--campaign-only` and `--campaign-label`** (commit `1487d04e`, in
   `arch_surgery/st_stall_mechanism/`). Without them the script raised `KeyError` on this run ID: its context table reads
   `node_calls_solve_phase` of the absent supplementary-stage records. Its `@1e-8` labels would also have named this
   campaign by the census τ. With neither option the output over `runs/census_tau1e-08` is byte-identical to the
   committed script's (`cmp`, 491 lines). Reversal: `git revert 1487d04e`.
5. **No harness change.** The `evaluation_warmup` FAIL is the gate reading an archive made under census settings (§7). It
   is a gate's verdict, not run-ID plumbing, so it was reported and not worked around. Making it pass under this run ID
   would need a before side made under the write set, which is a harness or archive decision for the orchestrator.

**Limits.**
- Ten gates are not run under this run ID (§7), among them G1, G5, G6 and G9, which the verification table prints. The
  verification table reads them "not pressed".
- The wall-clock tables have no validity check behind them (§8). They are context only (D33).
- The B4 table (constraint 93) and the full tally tables are in the stage records. They are not re-quoted here.
- The §5 count of "6 rows more than 1e-3 apart" is read off the script's printed per-seed table. The script prints no
  such aggregate.

**The unexpected.**
1. **This run's phase B tables equal V4's published tables cell for cell, and its phase A arm means equal V4's** (§4).
2. **8 coupling-loop caps on `lad`** in `B0`, `B1` and `B2` (seeds 4, 22, and 10 in the lifted arms), at
   `caller.py:2016`, on an infinite residual of `current_drive.eta_cd_dimensionless_hcd_primary` (§6). `lad`'s seed set
   is 11, the same as V4's.
3. **`tally_contracts` PASSed inside the campaign press** (302 compared, 0 mismatched, 18/18 teeth). Under the census
   campaign, I-37 made it FAIL there (A102 §9.3). I did not investigate why it no longer does.
4. **`evaluation_warmup` FAILs and stops `--gate all` at gate 16 of 29** (§7). A107 named this gate as one whose verdict
   under the write set was open.
5. **C: lost 6.1 GB while the run ID grew 1.2 GB**, and the virtual disk file's size, as read through `/mnt/c`, did not
   change (§9).
6. `st` `B0` loses seed 10 and `B2` loses seed 5, each `ifail = 5`, each accepted by the other two arms (§2 B5).

**To resume** (when C: has room): from `MDA_partitioning_experiment_v5/` in this worktree, press each gate after
`evaluation_warmup` with `HARNESS_WORKERS=3 … experiment_runner.py --test-set write_set --gate <name> --resume`. The gates,
in order: `record_completeness`, `prime_map`, `entry_and_warm`, `test_set`, `switch_composition`, `switch_neutrality`,
`output_path`, `written_file_gap`, `run_kind_separation`, `stage_provenance`; `count_neutrality`, `reproduction` and
`tally_contracts` already hold verdicts. Then run `--measure gate_table --resume --test-set write_set`, then
`--paper-tables write --test-set write_set` (the verification table's stamp line will move) and commit. A107 §7 L2 says
G2 makes 12 of its 15 jobs. The others' job counts are in `press04_jobs_all_before_gates.log`.
