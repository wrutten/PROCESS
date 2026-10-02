# A114 (v5-campaign-feedback-couplings-1e-6): the V5 campaign under the census set at τ = 1e-6

> **Document status**: **OPEN (task report, awaiting the orchestrator's assessment).** Task A114, branch
> `A114-v5-campaign-feedback-couplings-1e-6`, worktree `.claude/worktrees/A114-v5-campaign-feedback-couplings-1e-6`, from
> trunk `12ba98e7`, 2026-10-02. This is a run task. Nothing changed in the driver copy (`MDA_partitioning_experiment_v5/PROCESS/`),
> in `process/`, in the harness or in V4.
>
> **This task's commits:**
> - `448d6bde`: `compare_campaigns.py` extended by three end-state tables. **Every campaign record, gate verdict and stage
>   record of this run ID was made at this commit**, on a clean tree.
> - `756b2014`: the tables document `paper_tables_census_tau1e-06.md`.
> - `8e144beb`: `campaign_comparison.md`, the script's committed output over the four run IDs, generated at `756b2014`.
> - The tip: this report.
>
> **Where the numbers come from.** Every number is printed by a committed entry point, at the commit named beside it:
> `experiment_runner.py`, `paper_cells_recount.py`, `run_stamp_survey.py`, `compare_campaigns.py` and
> `arch_surgery/st_stall_mechanism/optimiser_path_split.py`. The press logs are in
> `MDA_partitioning_experiment_v5/runs/census_tau1e-06/_press_logs/A114/` (`pressNN_*.log`, `disk_log.txt`, `START_MARKER`).
> `runs/` was left in place, and no records tree was copied wholesale.
>
> This is an instruction to run, not a ruling. The four campaigns now form a two-by-two, test set {census, whole write set}
> × τ {1e-6, 1e-8}. Which setting the paper uses is still the user's open question (OQ-tolerance), and nothing here
> recommends one. Each interpretive sentence is marked *(measured)* or *(inferred)*.

## 1. Verdict

**The campaign is complete: 553 of 553 records under run ID `census_tau1e-06`**, the name the harness gave these settings
(`press01`: "run ID census_tau1e-06: test set census, tau 1e-06 (overridden)"). Every record is stamped `448d6bde`, W = 3,
dirty 0, untracked paths 0 (`press07`, stamp survey).

- The chain passed, `tally_contracts` included: 302 compared, 0 mismatched, 18/18 teeth (`press05`, one press,
  12:44:55–14:34:04, rc 0, 553 made, 0 resumed).
- `--jobs campaign --resume` afterwards keeps 553 of 553 (`press06`).
- The tables document is written (cross-check 0 of 178; LaTeX against Markdown 0 of 258; `press28`), and
  `--paper-tables check` reads **IDENTICAL** at `8e144beb` (`press31`).
- `paper_cells_recount.py` recounts 44 cell rows, 0 mismatched (`press29`).

**The gate table: 27 PASS, 2 FAIL, 0 not run, of 29; 180 of 181 teeth tripped** (`press22`):

| verdict | gate | in one line |
|---|---|---|
| **FAIL** | `test_set` (GT) | 0 of 8 binding drops bite at τ = 1e-6; PASS needs at least one (§5.1) |
| **FAIL** | `switch_neutrality` (G1) | one value per pair differs, `job_digest`, on 6 of 6 pairs; 0 of 51 319 output-file lines differ (§5.2) |

GC and G9, the two gates of issue I-43, both **PASS** under this run ID (§5.3, §5.4). G1's FAIL comes from the same kind of
cause as I-43: a condition that recognises the setting by the test set and does not look at τ (§5.2).

**The three existing campaigns are untouched** (§7):

| check | `census_tau1e-08` | `write_set_tau1e-06` | `write_set_tau1e-08` |
|---|---|---|---|
| `--jobs campaign --resume` | 553 of 553 kept (`press32`) | 553 of 553 kept (`press34`) | 553 of 553 kept (`press36`) |
| `--paper-tables check` | IDENTICAL (`press33`) | IDENTICAL (`press35`) | IDENTICAL (`press37`) |
| `find -newermt '2026-10-02T12:41:22+02:00'` | 0 of 17 843 entries | 0 of 11 631 | 0 of 11 072 (`press38`) |

## 2. The presses, in order

All presses ran from `MDA_partitioning_experiment_v5/`, in `PROCESS_surgery_env`, with `PYTHONDONTWRITEBYTECODE=1`, and
with `--tau 1e-6` (the census set is the default) unless the row says otherwise. The task started at
2026-10-02T12:41:22+02:00.

| # | press | when | outcome |
|---|---|---|---|
| 00, 01 | `--runs`; `--jobs campaign` | 12:41 | run ID `census_tau1e-06` confirmed; 278 listed, 0 kept |
| 02 | `compare_campaigns.py` over the three existing run IDs (test of the extension, before commit) | 12:44 | every table printed before unchanged (diff with the committed `campaign_comparison.md`: the commit line only) |
| — | commit `448d6bde` (the extension) | 12:44 | the one commit the campaign is stamped with |
| 03, 04 | `--copy-archived-records census_tau1e-08` (listing), then `--apply` | 12:44 | 1 935 files (293.5 MB) copied, SHA-256 checked; the closing agreement check reads **YES** (§6) |
| 05 | `HARNESS_WORKERS=3 … --campaign --resume` | 12:44:55 – 14:34:04 | 553 made, chain PASS, rc 0 |
| 06, 07 | `--jobs campaign --resume`; `run_stamp_survey.py --runs runs/census_tau1e-06 --launch-summary campaign` | 14:34 | 553 / 553 kept; 553 at `448d6bde`, W 3, dirty 0 |
| 08 | `--archive-collisions` | 14:34 | before any gate (§6) |
| 09 | `--jobs all --resume` | 14:34 | — |
| 10 | `HARNESS_WORKERS=3 … --gate all --resume` | 14:34:40 – 14:44:36 | **killed by me by mistake** at the Bash tool's 600 s limit, inside GT's runs (decision 2) |
| 11 | `optimiser_path_split.py --runs ../MDA_partitioning_experiment_v5/runs/census_tau1e-06 --campaign-only --campaign-label c1e-6` | 14:35 | §4 |
| 12 | `HARNESS_WORKERS=3 … --gate all --resume`, relaunched | 14:45:00 – 14:46:20 | 20 PASS, then GT **FAIL** (rc 1); the chain stops |
| 14–21 | the 8 later gates one by one, `--gate <name> --resume`, with a disk check before each | 14:46 – 14:55 | §5 |
| 22 | `--measure gate_table --resume` | 14:56 | 27 PASS, 2 FAIL |
| 23–25 | `--archive-collisions`; the copy listing; the copy `--apply` again, as a byte check | 14:56 | §6 |
| 26, 27 | `--timing validity`, `--timing cache-load` | 14:57 | no PROCESS run (§8) |
| 28, 29 | `--paper-tables write`; `paper_cells_recount.py --runs runs/census_tau1e-06 --document paper_tables_census_tau1e-06.md` | 14:57 | written; 44 rows, 0 mismatched |
| — | commit `756b2014` (the tables document) | 14:57 | |
| 30 | `compare_campaigns.py census_tau1e-08 write_set_tau1e-06 write_set_tau1e-08 census_tau1e-06 --output campaign_comparison.md` | 14:57 | at `756b2014`, clean; committed as `8e144beb` |
| 31–38 | `--paper-tables check` (this run ID); the three existing run IDs' `--jobs campaign --resume` and `--paper-tables check`; `find -newermt` | 14:58 | IDENTICAL; 553 / 553 kept ×3; IDENTICAL ×3; 0 entries ×3 |
| 39 | `--runs` | 14:58 | below |

**`--runs` reads, for `census_tau1e-06`:** 553 campaign records at `448d6bde`; evaluation 275 ok; optimisation 255 ok,
20 crashed; 788 run records in the folder; 1.71 GB on disk, of which the campaign 1.26 GB; gate table 27 PASS of 29
(2 FAIL, 0 not run).

## 3. The four campaigns side by side

Every cell below is from `compare_campaigns.py` at `756b2014`, committed as `campaign_comparison.md` (`8e144beb`). That file
has the full tables. Phase B is over each campaign's own seed set (every arm accepted); phase A over 25 displaced-entry
evaluations per arm. Column shorthand: **c8** `census_tau1e-08`, **w6** `write_set_tau1e-06`, **w8** `write_set_tau1e-08`,
**c6** `census_tau1e-06` (this task).

### 3.1 Run outcomes, phase B (25 starts per arm)

Phase A: 25 of 25 `ok` in every arm on every configuration, in all four campaigns *(measured)*.

| config | arm | c8: acc / ifail≠1 / RE / cap | w6 | w8 | **c6** |
|---|---|---|---|---|---|
| `tok` | each of BR, B0, B1, B2 | 22 / 0 / 3 / 0 | 22 / 0 / 3 / 0 | 22 / 0 / 3 / 0 | **22 / 0 / 3 / 0** (RE seeds 5, 20, 21) |
| `lad` | BR | 12 / 11 / 2 / 0 | 12 / 11 / 2 / 0 | 12 / 11 / 2 / 0 | **12 / 11 / 2 / 0** |
| `lad` | B0 | 12 / 11 / 2 / 0 | 12 / 9 / 2 / 2 | 12 / 9 / 2 / 2 | **12 / 11 / 2 / 0** |
| `lad` | B1, B2 | 12 / 11 / 2 / 0 | 11 / 9 / 2 / 3 | 11 / 9 / 2 / 3 | **12 / 11 / 2 / 0** (RE 3, 21; ifail 5 on 11 seeds, as BR) |
| `st` | BR | 24 / 1 / 0 / 0 | 24 / 1 / 0 / 0 | 24 / 1 / 0 / 0 | **24 / 1 / 0 / 0** (ifail 5: 17) |
| `st` | B0 | 24 / 1 / 0 / 0 | 23 / 2 / 0 / 0 | 23 / 2 / 0 / 0 | **21 / 4 / 0 / 0** (ifail 2: 3, 5, 9; ifail 5: 17) |
| `st` | B2 | 20 / 5 / 0 / 0 | 23 / 2 / 0 / 0 | 24 / 1 / 0 / 0 | **18 / 7 / 0 / 0** (ifail 2: 3, 5, 9; ifail 5: 1, 10, 15, 17) |

*acc = accepted (`ok`, `ifail = 1`); RE = `RuntimeError`; cap = the coupling loop's sweep cap (`ModuleSolveFailure`).*
"Other": 0 everywhere.

**Crashes at c6: 20, all `RuntimeError`, 0 loop caps** *(measured)*. The 20 are the same 20 starts as in the other three
campaigns (tok seeds 5, 20, 21 and lad seeds 3, 21, on every arm). The sweep cap (20) was not changed; no c6 run reached it,
so there is no cap message to report. The write-set campaigns' 8 caps on `lad` (B0 seeds 4, 22; B1 and B2 seeds 4, 10, 22;
the message names `current_drive.eta_cd_dimensionless_hcd_primary`, residual inf) have no counterpart under either census
campaign *(measured)*.

### 3.2 Phase A: module sweeps per evaluation, and the declared pair

AR / A0 / A1 / A2 means, then the declared pair's ratio of means (`A2/A1` on `tok` and `lad`, `A2/A0` on `st`):

| config | module | c8 | w6 | w8 | **c6** |
|---|---|---|---|---|---|
| `tok` | M1 | 4.96 / 5.88 / 5.88 / 3.00 · 0.51 | 4.96 / 5.52 / 5.12 / 4.00 · 0.78 | 4.96 / 6.52 / 5.88 / 4.00 · 0.68 | **4.96 / 5.12 / 5.12 / 3.00 · 0.59** |
| `tok` | M3 | … / 2.00 · 0.34 | … / 3.00 · 0.59 | … / 3.00 · 0.51 | **… / 2.00 · 0.39** |
| `lad` | M1 | 5.00 / 5.00 / 5.00 / 3.00 · 0.60 | 5.00 / 5.00 / 4.92 / 4.00 · 0.81 | 5.00 / 5.40 / 5.00 / 4.00 · 0.80 | **5.00 / 4.92 / 4.92 / 3.00 · 0.61** |
| `lad` | M3 | … / 2.00 · 0.40 | … / 3.00 · 0.61 | … / 3.00 · 0.60 | **… / 2.00 · 0.41** |
| `st` | M1 | 4.92 / 5.96 / — / 3.00 · 0.50 | 4.92 / 5.84 / — / 4.00 · 0.68 | 4.92 / 6.96 / — / 4.00 · 0.57 | **4.92 / 4.84 / — / 3.00 · 0.62** |
| `st` | M3 | … / 3.00 · 0.50 | … / 3.00 · 0.51 | … / 3.96 · 0.57 | **… / 2.88 · 0.60** |

M2 reads 1.00 or 1.01 in every campaign. **Node calls per evaluation, pooled, at c6** (the tally's *per-call cost by
configuration*, `press05`): `tok` A1→A2 0.4602, `lad` A1→A2 0.4708, `st` A0→A2 0.5813.

### 3.3 Phase B: per run over the seed set, and the ratios of means

| config | campaign | n | iterations B2/B0 · B2/BR | ε B2/B0 | ρ B2/B0 | **R (node calls per run) B2/B0 · B1/B0 · B2/BR** | BR→B0 |
|---|---|---:|---|---:|---:|---|---:|
| `tok` | c8 | 22 | 0.9942 · 0.9942 | 1.0411 | 0.4821 | 0.5020 · 0.9721 · 0.5371 | 1.0700 |
| `tok` | w6 | 22 | 0.9942 · 0.9942 | 1.0411 | 0.6144 | 0.6395 · 1.0077 · 0.6554 | 1.0250 |
| `tok` | w8 | 22 | 0.9942 · 0.9942 | 1.0411 | 0.5627 | 0.5859 · 0.9717 · 0.7204 | 1.2296 |
| `tok` | **c6** | 22 | 0.9942 · 0.9942 | 1.0411 | 0.5187 | **0.5399 · 1.0238 · 0.5012** | 0.9283 |
| `lad` | c8 | 12 | 1.3658 · 1.3658 | 1.4410 | 0.4884 | 0.7031 · 1.3284 · 0.6995 | 0.9950 |
| `lad` | w6 | 11 | 0.7012 · 0.7012 | 0.7309 | 0.6183 | 0.4504 · 0.6919 · 0.4373 | 0.9709 |
| `lad` | w8 | 11 | 0.7012 · 0.7012 | 0.7309 | 0.5605 | 0.4091 · 0.6540 · 0.4713 | 1.1521 |
| `lad` | **c6** | 12 | 1.3658 · 1.3658 | 1.4410 | 0.5189 | **0.7465 · 1.4176 · 0.6413** | 0.8591 |
| `st` | c8 | 20 | 2.4048 · 1.6915 | 2.4432 | 0.5101 | 1.2419 · — · 0.8434 | 0.6791 |
| `st` | w6 | 22 | 0.9530 · 0.7682 | 0.9512 | 0.5716 | 0.5331 · — · 0.4454 | 0.8356 |
| `st` | w8 | 23 | 1.0115 · 0.8471 | 1.0126 | 0.5552 | 0.5582 · — · 0.5877 | 1.0529 |
| `st` | **c6** | 18 | 1.1101 · 4.2650 | 1.1103 | 0.6074 | **0.6744 · — · 2.0174** | **2.9915** |

**The arm means at c6** (iterations; node calls per run):

| config | iterations BR / B0 / B1 / B2 | node calls per run BR / B0 / B1 / B2 |
|---|---|---|
| `tok` | 7.818 / 7.818 / 7.773 / 7.773 | 41 480 / 38 506 / 39 425 / 20 791 |
| `lad` | 28.250 / 28.250 / 38.583 / 38.583 | 160 850 / 138 178 / 195 886 / 103 152 |
| `st` | 29.556 / **113.556** / — / **126.056** | 120 817 / 361 425 / — / 243 739 |

**Without the retried seeds** (the tally's *cost against both anchors*), c6, B2/B0 · B2/BR: `tok` (n 22) 0.5399 · 0.5012;
`lad` (n 10) 0.5534 · 0.4736; **`st` (n 0) —**: on `st` every start has a retried arm (§4).

### 3.4 The rules

| config | campaign | A1 (declared pair median / p90, verdict; A2 runs with a component ≥ τ) | B1 (judged pair: objf median / p90 against 1e-6, verdict, hops) |
|---|---|---|---|
| `tok` | c8, w6, w8 | PASS (1.00 / 1.00); 0 | PASS, 0 hops (2.823e-11 / 4.570e-11) |
| `tok` | **c6** | **PASS** (1.00 / 1.00); 0 | **PASS**, 2.823e-11 / 4.572e-11, 0 hops |
| `lad` | c8 | PASS (exactly 0); 0 | FAIL at p90: 5.829e-07 / 3.148e-04, 4 hops (1\*, 10\*, 11, 13) |
| `lad` | w6, w8 | PASS (exactly 0); 0 | FAIL at p90: 4.101e-07 / 2.148e-06, 3 hops (1\*, 11, 13) |
| `lad` | **c6** | **PASS** (exactly 0); 0 | **FAIL** at p90: 5.829e-07 / 3.148e-04, 4 hops (1\*, 10\*, 11, 13), entering at the lift `B0 → B1`, 4 of 4 |
| `st` | c8 | PASS; 0 | FAIL at p90: 6.211e-12 / 1.305e-03, 3 hops (5\*, 12\*, 24\*) |
| `st` | w6 | PASS; 0 | PASS: 3.467e-13 / 3.510e-09, 1 hop (12) |
| `st` | w8 | PASS; 0 | PASS: 2.936e-13 / 3.356e-10, 2 hops (12\*, 24\*) |
| `st` | **c6** | **PASS** (1.00 / 1.00); 0 | **PASS**: 9.364e-12 / 1.692e-11, n 18, 0 hops |

The tables document's verification row at c6 reads **B1 "PASS tok, st · FAIL lad"**, the same as at w6 and w8.

## 4. The three new tables (the user's question: where do the two approaches end?)

`compare_campaigns.py` at `756b2014`. **Every statistic was declared in the script's module docstring and committed
(`448d6bde`) before the script's output was first read**; the first run (press 02, over the three existing run IDs) came
after the declaration was written and was used only to check the script ran and left the old tables unchanged; the four-run
output was read after the campaign. The relative difference is `|a − b| / max(|a|, |b|)` (A104's `rel`); "bit-identical"
means every component of `y_exit.json`'s `state` equal as stored.

### 4.1 Phase A, same fixed point (25 displaced entries; bit-identical exits, then the rest)

| config | pair | c8 | w6 | w8 | **c6** |
|---|---|---|---|---|---|
| `tok` | A2/A1 | 12 of 25; 11 comps; 1.2e-13 / 2.3e-12 | 11; 11; 7.5e-11 / 3.1e-10 | 12; 11; 1.2e-13 / 2.3e-12 | **11; 11; 7.5e-11 / 3.1e-10** |
| `tok` | A0/AR | 11; 284; 3.1e-07 / 8.1e-07 | 11; 284; 3.0e-07 / 7.9e-07 | 9; 284; 2.7e-07 / 8.1e-07 | **21; 285.5; 6.1e-07 / 7.9e-07** |
| `lad` | A2/A1 | 25 | 25 | 25 | **25** |
| `lad` | A0/AR | 25 | 25 | 25 | **23; 11; 1.2e-09 / 2.3e-09** |
| `st` | A2/A0 | 0; 11; 8.0e-12 / 1.5e-11 | 0; 11; 8.5e-12 / 4.6e-11 | 0; 11; 2.7e-13 / 5.2e-13 | **0; 11; 3.1e-10 / 1.1e-08** |
| `st` | A0/AR | 0; 245; 1.1e-07 / 4.3e-07 | 2; 245; 1.1e-07 / 4.1e-07 | 0; 245; 1.1e-07 / 4.3e-07 | **23; 245; 5.8e-07 / 5.9e-07** |

*Each cell: bit-identical starts of 25; median differing components over the rest; largest relative difference median / max
over the rest.* The worst component most often: `tok` A2/A1 `costs.c243` (8 of 14 at c6); `tok` A0/AR
`pf_coil.stress_z_cs_self_midplane_profile`; `st` A2/A0 `heat_transport.tlvpmw` (17 of 25 at c6); `st` A0/AR
`superconducting_tfcoil.a_tf_plasma_case`.

- *(measured)* The partitioned and the flat arm never land on bit-identical states on `st` in any campaign; on `tok` they
  do on about half the starts; on `lad` on all 25 in all four. Where they differ, they differ in 11 components.
- *(measured)* At c6 the largest A2-against-flat distance is the largest of the four campaigns on `st` (max 1.1e-08) and
  equal to w6's on `tok`; it stays below τ = 1e-6 in every cell.
- *(measured)* At c6 the flat arm lands bit-identically on the reference arm's state far more often than in the other three
  (tok 21, lad 23, st 23 of 25, against at most 11).

### 4.2 Phase A, same arm across settings (exits bit-identical of 25; largest relative difference median / max)

Selected rows; the full table (all six pairs of run IDs, every arm, with the count of bit-identical entries) is in
`campaign_comparison.md`.

| config | arm | c6 vs w6 | c6 vs c8 | c6 vs w8 | w6 vs w8 | c8 vs w8 |
|---|---|---|---|---|---|---|
| `tok` | AR | 25 (0) | 7 / 2.2e-11 | 8 / 2.2e-11 | 8 / 2.2e-11 | 11 / 7.4e-13 |
| `tok` | A0 | 15 / 5.7e-07 | 0; 8.4e-09 / 5.8e-07 | 0; 8.4e-09 / 5.8e-07 | 0; 1.4e-09 / 1.5e-08 | 8 / 3.7e-09 |
| `tok` | A1, A2 | **25 (0)** | 0; 8.4e-09 / 5.8e-07 | 0; 8.4e-09 / 5.8e-07 | 0; 8.4e-09 / 5.8e-07 | 0; 4.1e-12 / 1.8e-10 |
| `lad` | AR, A1, A2 | 25 | 25 | 25 | 25 | 25 |
| `lad` | A0 | 23 / 2.3e-09 | 23 / 2.3e-09 | 23 / 2.3e-09 | 25 | 25 |
| `st` | AR | 0; 5.0e-14 / 2.0e-11 | 0; same | 0; same | 17 / 1.2e-13 | 17 / 1.2e-13 |
| `st` | A0, A2 | 0; 1.1e-07 / 5.9e-07 | 0; 1.1e-07 / 6.1e-07 | 0; 1.1e-07 / 6.1e-07 | 0; 3.8e-09 / 2.1e-08 | 0; 3.5e-09 / 6.7e-09 |

- *(measured)* On `tok`, entries are bit-identical between c6 and w6 (25 of 25), and the A1 and A2 exits are bit-identical
  on all 25: in phase A on `tok`, the census set at 1e-6 and the whole write set at 1e-6 reach the same states, bit for bit,
  on the lifted arms.
- *(measured)* On `st`, c6 shares no bit-identical entry or exit with any other campaign, and its A0 and A2 exits sit about
  1e-07 (max 6e-07) from all three others, against ≤ 2e-08 between the other three.
- *(inferred)* The phase A entries of a campaign are displacements of its own entry reference's exit state, so a campaign
  whose reference fixed point moved shares no entry with another; that is why the "entries" column is all-or-nothing.

### 4.3 Phase B, where the partitioned arm ends (B2 against B1; on `st` against B0; starts both accepted)

| config | campaign | n | design: largest relative difference, median / max | starts above 10 % | worst variable most often | objective: median / max | objective bit-identical |
|---|---|---:|---|---:|---|---|---:|
| `tok` | c8 | 22 | 1.2e-11 / 5.5e-10 | 0 | `dr_tf_nose_case` (12) | 0 / 2.8e-16 | 21 |
| `tok` | w6 | 22 | 0 / 6.7e-11 | 0 | `b_plasma_toroidal_on_axis` (18) | 0 / 0 | 22 |
| `tok` | w8 | 22 | 8.8e-12 / 4.1e-10 | 0 | `dr_tf_nose_case` (7) | 0 / 2.8e-16 | 20 |
| `tok` | **c6** | 22 | **2.8e-10 / 8.2e-08** | **0** | `dr_tf_nose_case` (14) | 2.1e-16 / 2.2e-14 | 10 |
| `lad` | c8 | 12 | 7.4e-12 / 3.7e-10 | 0 | `dr_cs` (8) | 8.6e-15 / 2.8e-14 | 0 |
| `lad` | w6 | 11 | 0 / 3.3e-11 | 0 | `b_plasma_toroidal_on_axis` (8) | 0 / 3.8e-14 | 8 |
| `lad` | w8 | 11 | 2.4e-12 / 9.0e-11 | 0 | `dr_cs` (6) | 8.1e-15 / 4.8e-14 | 3 |
| `lad` | **c6** | 12 | **6.4e-12 / 1.8e-10** | **0** | `dr_cs` (9) | 2.7e-14 / 9.0e-14 | 0 |
| `st` | c8 | 20 | 9.4e-01 / 1.0 | 14 | `dr_tf_nose_case` (12) | 6.2e-12 / 1.3e-02 | 0 |
| `st` | w6 | 22 | 3.8e-06 / 1.0 | 4 | `dr_shld_inboard` (14) | 2.2e-13 / 1.3e-02 | 0 |
| `st` | w8 | 23 | 4.6e-08 / 1.0 | 1 | `dr_shld_inboard` (14) | 2.9e-13 / 1.3e-02 | 0 |
| `st` | **c6** | 18 | **1.3e-01 / 9.6e-01** | **11** | `dr_bore` (9) | 9.0e-12 / 3.0e-09 | 0 |

The c8, w6 and w8 `st` rows agree with the orchestrator's ad-hoc reading in A113's assessment (median 9.4e-01 / 14 of 20;
3.8e-06 / 4 of 22; 4.6e-08 / 1 of 23), now from a committed script.

**The two bound counts for `st`'s B2** (`optimiser_path_split.py --runs …/runs/census_tau1e-06 --campaign-only
--campaign-label c1e-6`, at `448d6bde`, `press11`; population: B2's accepted runs):

| bound | **c6** | w8 | w6 | c8 |
|---|---|---|---|---|
| `dr_tf_nose_case` at its lower bound (0.01) | **7 of 18** | 0 of 24 | 0 of 23 | 10 of 20 |
| `dr_tf_wp_with_insulation` at its upper bound (0.8) | **1 of 18** | 0 of 24 | 5 of 23 | not reported |

At c6 the script also lists `dr_cs` at its lower bound 0.03 on 2 of B2's 18, and `dr_tf_wp_with_insulation` at its upper
bound on 1 of B0's 21 *(measured)*. The other three columns are A113's and A106's published counts.

- *(measured)* On `st`, the partitioned arm's final design is far from the flat arm's at both census settings (more than
  10 % on 14 of 20 at c8 and 11 of 18 at c6) and close at both write-set settings (4 of 22, 1 of 23). The objective
  difference at c6 is at most 3.0e-09.
- *(measured)* On `tok` and `lad`, no start ends more than 10 % apart in any campaign; at c6 the `tok` maximum (8.2e-08) is
  the largest of the four.

**Other `st` figures at c6, the same script** *(measured)*: every one of B0's and B2's 25 starts is retried (B0 25 of 25,
B2 25 of 25, BR 5 of 25); none of B0's or B2's accepted runs finishes in one attempt (`of which one attempt`: 0 and 0); the
`B0 → B2` class is "retried" on 25 of 25 starts. Hovering (`n_near > 10`): BR 7 of 24, B0 4 of 21, B2 12 of 18. Node calls
per evaluation over the seed set (n 18): BR 69.0, B0 53.3, B2 32.4 (B2 over B0 0.61).

## 5. The gate table under `census_tau1e-06`

Source: `--measure gate_table --resume` at `448d6bde` (`press22`; record `runs/census_tau1e-06/gates/gate_table/measurements.json`).

| gate | plan | verdict | compared | mismatched | teeth |
|---|---|---|---:|---:|---|
| `g0prime` | G0 | PASS | 77 | 1 (the approved model file) | 4/4 |
| `copy_identity` | — | PASS | 224 | 8 (declared edits) | 12/12 |
| `edit_behaviour`, `self_containment`, `composition`, `rungs`, `provenance`, `data`, `run_path`, `capability`, `artifacts_check`, `artifacts_derive_inputs`, `artifacts_census`, `artifacts_per_run` | — | PASS (each) | 3, 61, 53, 98, 4, 22, 12, 61, 119, 2, 81, 16 | 0 | all |
| `resume_identity` | — | PASS | 805 | 0 | 15/15 |
| `evaluation_warmup` | — | PASS (read once, D44; verdict at `c2295511`) | 19 876 | 0 | 5/5 |
| `record_completeness` | G7 | PASS | 281 | 0 | 14/14 |
| `count_neutrality` | GC | **PASS** (straddle `item5` → `DR12`) | 50 114 | 0 | 4/4 |
| `prime_map` | G2 | PASS | 17 591 | 0 | 3/3 |
| `entry_and_warm` | G6 | PASS | 6 717 | 0 | 3/3 |
| **`test_set`** | GT | **FAIL** | 13 424 | 0 | **3/4** |
| `switch_composition` | G5 | PASS | 156 | 0 | 4/4 |
| **`switch_neutrality`** | G1 | **FAIL** (straddle `9ed0da4c → 448d6bde`) | 54 979 | **6** | 9/9 |
| `reproduction` | GR | PASS (read once; verdict at `d6c246a1`) | 256 | 0 | 8/8 |
| `output_path` | G9 | **PASS** | 3 879 | 0 | 4/4 |
| `written_file_gap` | — | PASS | 42 | 0 | 4/4 |
| `tally_contracts` | — | PASS | 538 | 0 | 18/18 |
| `run_kind_separation` | — | PASS (788 run records) | 1 894 | 0 | 7/7 |
| `stage_provenance` | — | PASS | 12 | 0 | 5/5 |

### 5.1 GT (`test_set`): FAIL — no drop bites at τ = 1e-6

GT runs here (the census set is its own). **What failed** (`press12`; record `runs/census_tau1e-06/gates/test_set/gate.json`)
*(measured)*: 8 full-set runs at seed 1 over `tok`, `lad`, `st` and arms A0, A1, A2; 8 binding drops, **0 bite, 8 "not
individually binding on this entry"**; 8 controls, 8 bit-identical; 13 424 exit-state components compared, 0 differing.

| config | arm | component dropped | node calls full → dropped, **c6** | the same at c8 |
|---|---|---|---|---|
| `tok` | A0, A1 | `pf_coil.stress_z_cs_self_midplane_profile` | 105 → 105 | 147 → 126, **bites** |
| `tok` | A2 | the same | 49 → 49 | 55 → 52, **bites** |
| `lad` | A0 | `times.t_plant_pulse_burn` | 105 → 105 | 105 → 105 |
| `lad` | A1, A2 | `tfcoil.str_wp` | 105 → 105; 49 → 49 | the same |
| `st` | A0, A2 | `tfcoil.str_wp` | 105 → 105; 49 → 49 | 126 → 126; 64 → 64 |

**The cause, by line.** `harness/gates/gate_test_set.py:442–443`: `tooth_bit = n_bites >= 1`, `passed = passed and
tooth_bit`. Every row passes individually; the gate needs at least one drop to bite over the job set, and none does. The
tooth "a biting drop's exit state replaced by the full run's" did not trip because "no drop bit, so there is no biting exit
state to doctor" — the 1 of 181 teeth not tripped.

*(inferred)* At τ = 1e-6 the loop on `tok` stops before the dropped component is the last one moving (105 node calls, against
147 at 1e-8), so dropping it changes nothing; the gate's claim is that the census set binds, and at this τ it measures no
single component of it as binding at seed 1. That is the gate's result, not tuned.

### 5.2 G1 (`switch_neutrality`): FAIL — on `job_digest` alone

**What failed** (`press15`; record `runs/census_tau1e-06/gates/switch_neutrality/gate.json`) *(measured)*: 6 pairs (3
configurations × AR, BR), the before capture at `9ed0da4c` (archived, copied from c8), the after side made by this press at
`448d6bde`. 3 660 record values and 51 319 output-file lines compared; **6 values differ, one per pair, each
`job_digest`**; **0 output-file lines differ**. 9 of 9 teeth tripped.

**The cause, by line.** `harness/gates/gate_neutrality.py:563`: `CONDITIONAL_WITNESS["job_digest"] = "job_identity.test_set"`
— the digest is excluded only where the witness `job_identity.test_set` is present on exactly one side. The identities
(measured from the four run IDs' captures):

| run ID | before (`9ed0da4c`): `test_set`, `tau` | after: `test_set`, `tau` | witness on | digest | G1 |
|---|---|---|---|---|---|
| c8 | census, 1e-08 | census, 1e-08 | both | equal | PASS |
| w6 | census, 1e-08 | absent, absent | one side | excluded | PASS |
| w8 | census, 1e-08 | absent, 1e-08 | one side | excluded | PASS |
| **c6** | census, 1e-08 | **census, absent** | **both** | **compared, differs** | **FAIL** |

The identity renders τ only where it differs from V4's 1e-6, so a census job at 1e-6 carries `test_set` and no `tau`. The
witness sees `test_set` on both sides and compares two digests computed over two field sets. The `tau` leaf itself is
excluded as present on one side only, as the conditional name allows. *(inferred)* This is the same shape as I-43: a
condition that decides "same setting" from the test set and does not look at τ. Not worked around; the gate was not changed
or pressed again.

**What the verification table reads** (`paper_tables_census_tau1e-06.md`): G0 PASS, **G1 FAIL**, A1 PASS, A2 reported, B1
"PASS tok, st · FAIL lad", G6 PASS, G5 PASS, G9 PASS, **GT FAIL**.

### 5.3 GC (`count_neutrality`), issue I-43: PASS — the branch that replaces the campaign is taken

*(measured, `press10`)*: straddle `item5` at `cfa0d3ff` → `DR12` at `24b78e2d`, `d08e8ab4`; 22 run pairs; 3 989 count leaves,
0 differing; 33 prime-count checks, 0 failing; 46 125 coupling-state components, 0 differing; 4/4 teeth.

**Why, by line.** `harness/gates/gate_count_neutrality.py:823–832`: the campaign is replaced by
`dataclasses.replace(campaign, test_set=declared_set, tau=None)` when `campaign.test_set != declared_set`
(`declared_set = "write_set"`, line 116). The census set differs, so the replacement is taken and τ falls to the write set's
default, 1e-6 — exactly as under c8. The copy step's agreement check confirms it before any gate: GC's job set under c6
resolves and decides exactly as under c8 (47 jobs, `--resume` keeps 36 under each, 0 differing; `press04`). *(inferred)* GC
reads the same archived records under c6 as under c8, so its verdict here is the straddle's own, not a claim about τ = 1e-6
under the census set.

### 5.4 G9 (`output_path`), issue I-43: PASS — B0's sub-check is not gated

*(measured, `press17`)*: every arm whose loop the matrix removes passes (3 825 components compared in hex, 0 differing).
The reference arms' sub-check: `BR` 0 of 9 fields differ from GR's record on every configuration; **`B0` 4 of 9 differ on
every configuration, "not gated: the arm's loop stops on the 'census' set, GR's on the write set (D39)"**.

**Why, by line.** `harness/gates/gate_output_path.py:447–449`: `same_criterion = ARMS[arm].is_reference or
campaign.test_set == V4_TEST_SET`. Under the census set the condition is false for `B0`, so the differences are reported and
not gated — as under c8. I-43's FAIL appears only under a write-set run ID whose τ is not 1e-6.

### 5.5 I-42, `evaluation_warmup`, GT

- **I-42** *(measured, `press08` and `press23`)*: **not listed under this run ID**. After the gates the survey reads
  `count_neutrality: 47 archived record(s) … other gates' jobs carrying an archived identity: 3; resolving into the archived
  directory: 0` — GR's three `A0` seed-0 references, resolved elsewhere. No G6, G2 or GT job resolves into GC's records. (Under
  w8 it listed 9; there GC composed at 1e-8 and its references were records that task made. Here GC composes at 1e-6 under
  the write set, and the gates' own references are census jobs at 1e-6, a different identity.)
- **`evaluation_warmup`**: PASS, read once (D44) — the verdict at `c2295511` re-derived from its 11 archived pairs: 1 426
  count leaves, 0 differing; 18 450 components, 0 differing; 66 of 66 files byte-identical to the manifest.
- **GT**: runs under this run ID and FAILs (§5.1).

## 6. Archives and collisions

### Before any gate (`press08`)

- **GR:** 28 archived records, 27 identities, 27 in the read-only archive; 26 other-gate jobs resolve into it, all readers
  (`tally_contracts` 20; G9's 6 seed-0 jobs with `asked_by=reproduction`) — the same as under the other run IDs.
- **GC:** 47 archived records; 3 other-gate jobs carry an archived identity (GR's `A0` seed-0 references), 0 resolve into the
  archive.
- **G1:** 54 archived records, 12 identities; GR's 3 AR jobs resolve elsewhere.
- **Warm-up gate:** 22 records, 0 jobs. **Derived input files:** 0 records.
- **Not composable yet:** the jobs of GC, G6, G2 and GT ("the entry reference for large_tokamak_nof did not finish or is not
  made"), as under w8.

### After the gates (`press23`)

The same text, less the four "not composable" lines (and one dictionary printed in another order). **No collision listed.**

### Did any gate write into a copied archive? One file, by design of GC (measured, `press25`)

The copy's `--apply` re-run as a byte check **refused**: "1 file(s) are already in runs/census_tau1e-06/ with other bytes than
runs/census_tau1e-08/'s (first: `gates/count_neutrality/straddles/item5__DR12.json`); nothing was copied". I compared the two
files leaf by leaf: 1 097 leaves, 45 differ — 44 are the `before.path` / `after.path` of the 22 rows (now this worktree's
paths), and one is `tree_git_head` (`c412bbdb` → `448d6bde`). No compared count or state differs. GC's press rewrites the
straddle record of the straddle it presses (c8's own copy of this file was itself rewritten on 2026-10-01 at `c412bbdb`). Under
w8 GC refused, so A113's byte check found 0 differing. *(inferred)* This is GC writing its own verdict record, not a write into
a read-only run record; no record under `pool_records/` or any other archived run directory was reported as differing.

**The copy step's agreement check** reads **YES** at `press04` (before the campaign): reproduction 29 jobs, keeps 3 under both;
count_neutrality 47 jobs, keeps 36 under both; 0 differing.

## 7. The untouched-folders check and disk

Start time 2026-10-02T12:41:22+02:00 (`START_MARKER`). At the end (§1): 553 of 553 kept under each existing run ID; all three
documents IDENTICAL; `find runs/<run ID> -newermt '2026-10-02T12:41:22+02:00'` lists 0 entries under each of the three
folders. The copy reads from `census_tau1e-08` and wrote nothing there.

From `disk_log.txt` (`df -h /mnt/c`):

| when | C: free |
|---|---|
| 12:41, task start; 12:44 before the copy; 12:44 before the campaign | 131 GB |
| 14:34, after the campaign; before each gate press | 129 GB |
| 14:58, end | **129 GB** |

The floor (20 GB) was never approached. This run ID: 1.71 GB, of which the campaign 1.26 GB and the copied archives 293.5 MB.

## 8. The wall-clock stages (context, never evidence)

`--paper-tables write` needs two timing stage records; I pressed both, as A106 and A113 did; neither makes a PROCESS run.
`--timing validity` reads "no repetition record" for each job and "appendix timings from: not decidable yet"; `--timing
cache-load` reads the campaign's records. The tables document's wall-clock tables are the campaign's W = 3 records with no
validity check behind them. **No number in this report is a timing.**

## 9. Decisions taken alone, each with its reversal

1. **The comparison extension was written and committed before the campaign** (`448d6bde`), as the brief recommended, and
   tested against the three existing run IDs first. Statistics declared in the docstring before any output was read; one
   unplanned addition, declared there too: the across-settings table also counts bit-identical *entries*, so a reader can
   tell whether two campaigns started from the same states. Reversal: `git revert 448d6bde 8e144beb`.
2. **I killed the first `--gate all` press myself, by mistake, and relaunched it with `--resume`.** I launched it as a
   background command with a 600 s limit; the tool stopped it at 14:44:36, during GT's runs (G7, GC, G2 and G6 had written
   verdicts). Evidence of death: the tool's notification ("stopped after reaching its background time limit") and the log's
   mtime, written into `press10_gate_all.started`. The relaunch (`press12`, limit 2 h) kept every complete record
   (`[resumed]`; GT made one run, `st` A2 seed 1, presumably the one the kill interrupted — inferred, not inspected) and pressed every gate
   from the start. All gate records are at `448d6bde`. Reversal: none needed; no campaign record was involved.
3. **The gates after GT's FAIL were pressed one by one**, as the brief asks, with a disk check before each, in one background
   loop with one log per gate.
4. **The archive byte check uses the copy's own `--apply`** (`press25`). It refused, wrote nothing, and named the one file
   (§6); I then compared that file leaf by leaf with a read-only inline comparison (not a published number beyond "45 of
   1 097 leaves, 44 paths and one commit").
5. **The timing stages without a W = 1 pass** (§8), as A106 and A113 decided. Reversal: delete
   `runs/census_tau1e-06/timing/{validity,cache_load}/`; the tables document then refuses to render.
6. **`optimiser_path_split.py` was not changed**; label `c1e-6`.
7. **G1's cause was read in the records and the code, not tested.** The identity table in §5.2 is read from the eight capture
   records; I did not change the witness to see the gate pass.

## 10. The unexpected

1. **On `st`, the census set at 1e-6 sends every flat and partitioned optimisation into its retry ladder** (B0 25 of 25, B2 25
   of 25, BR 5 of 25), with the first attempt at 100 iterations on the starts the script shows; B0's mean iterations over the
   seed set are 113.6 against BR's 29.6, and B2/BR in node calls per run is 2.02 *(measured)*. Accepted starts drop to 21 (B0)
   and 18 (B2), with three `ifail = 2` on each.
2. **On `tok` and `lad`, phase B at c6 walks c8's optimiser paths, not w6's** *(measured)*: iterations, ε, the seed sets (22,
   12), the outcomes (no loop caps on `lad`) and B1's hops (lad 1\*, 10\*, 11, 13) are those of c8. In phase A on `tok`, by
   contrast, c6 and w6 reach bit-identical states on A1 and A2 for all 25 starts. *(inferred)* In phase B the test set, not τ,
   decides which path the optimiser takes on these two configurations; in phase A on `tok` the two sets at 1e-6 stop on the
   same sweep.
3. **GT FAILs under the census set at 1e-6** (§5.1): no single component of the census set binds at seed 1.
4. **G1 FAILs on `job_digest`** (§5.2), a fourth combination of the I-43 shape; the run ID is the first census one whose τ
   equals V4's.
5. **GC and G9 PASS** here, so I-43's two gates behave as under c8 (§5.3, §5.4).
6. **GC's press rewrites `item5__DR12.json` in the copied GC archive** (§6), which the byte check catches.
7. **The flat arm lands on the reference arm's exit state far more often at c6** (phase A A0/AR: tok 21, lad 23, st 23 of 25
   bit-identical, against ≤ 11 elsewhere) *(measured)*.
8. **My own 600 s timeout killed a gate press** (decision 2).

## 11. What I did not check

- **Why `st` retries every start at c6**, and why `tok` and `lad` keep c8's paths. §10 reports measurements; no explanation is
  tested.
- **Whether GT's and G1's outcomes are defects or scope decisions.** I read the lines and report the cause; nothing was
  changed or tested.
- **Whether 1e-6 or 1e-8, census or write set, is the right setting.** Not this task's question.
- **The wall-clock tables of the tables document:** not read beyond the generator's cross-checks.
- **G2 part (ii)** PASSes; I did not read which straddle files it took under this run ID.
- **The B4 table (constraint 93)** and the full tally tables: in the stage records, not re-quoted.
- **The record left partial by the killed gate press**: the relaunch re-made it; I did not inspect the partial directory
  before it was re-made.
- **The "existing folders untouched" claim** rests on modification times and the two committed checks per run ID, not on
  per-file hashes.
- **The c8, w6, w8 bound counts** in §4.3 are quoted from A113's and A106's reports, not re-run.
