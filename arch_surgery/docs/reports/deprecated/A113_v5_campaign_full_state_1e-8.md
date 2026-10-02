# A113 (v5-campaign-full-state-1e-8): the V5 campaign under the whole write set at τ = 1e-8

> **Document status**: **MERGED 2026-10-02 at `e47c6ca2` (`--no-ff`; the orchestrator's assessment at the end, §12); archived.** The one V5 records tree (`census_tau1e-08/`, `write_set_tau1e-06/`, `write_set_tau1e-08/`, the shared caches) was moved on with A114 and is at `arch_surgery/idf_probe/runs/A114_runs/`; the paths below that begin `runs/` are read from there. **The gate table under this run ID reads 26 PASS, 1 FAIL (G9), 2 not run (GC refused; GT by design) — issue I-43.** Was: **OPEN (task report, awaiting the orchestrator's assessment).** Task A113, branch
> `A113-v5-campaign-full-state-1e-8`, worktree `.claude/worktrees/A113-v5-campaign-full-state-1e-8`, from trunk
> `a75d024b`, 2026-10-02. This is a run task. Nothing changed in the driver copy (`MDA_partitioning_experiment_v5/PROCESS/`),
> in `process/`, in the harness or in V4.
>
> **This task's commits:**
> - `b44c88c4`: a new read-only script, `compare_campaigns.py`. **Every campaign record, gate verdict and stage record of
>   this run ID was made at this commit**, on a clean tree.
> - `ce8072ef`: the tables document `paper_tables_write_set_tau1e-08.md`.
> - `d9a2f32f`: `campaign_comparison.md`, the script's committed output, generated at `ce8072ef`.
> - The tip: this report.
>
> **Where the numbers come from.** Every number is printed by a committed entry point, at the commit named beside it:
> `experiment_runner.py`, `paper_cells_recount.py`, `run_stamp_survey.py`, `compare_campaigns.py` and
> `arch_surgery/st_stall_mechanism/optimiser_path_split.py`. The press logs are in
> `MDA_partitioning_experiment_v5/runs/write_set_tau1e-08/_press_logs/A113/` (`pressNN_*.log`, `disk_log.txt`,
> `START_MARKER`). `runs/` was left in place, and no records tree was copied wholesale.
>
> This is an instruction to run, not a ruling. Which setting the paper uses stays the user's open question
> (OQ-tolerance), and nothing here recommends one.

## 1. Verdict

**The campaign is complete: 553 of 553 records under run ID `write_set_tau1e-08`.** Every one is stamped `b44c88c4`,
W = 3, not dirty, run kind `campaign` (`press07`, stamp survey).

- Its chain passed, `tally_contracts` included: 302 compared, 0 mismatched, 18/18 teeth (`press05`).
- `--jobs campaign --resume` afterwards keeps 553 of 553 (`press06`).
- The tables document is written (cross-check 0 of 178; LaTeX against Markdown 0 of 258), and `--paper-tables check`
  reads **IDENTICAL** at `d9a2f32f` (`press34`).
- `paper_cells_recount.py` recounts 44 cell rows, 0 mismatched (`press31`).

**The gate table: 26 PASS, 1 FAIL, 2 not run, of 29; 173 of 181 teeth tripped** (`press24`):

| verdict | gates |
|---|---|
| **FAIL** | `output_path` (G9) |
| **refused** (no verdict record) | `count_neutrality` (GC), `test_set` (GT; refused by design under the write set) |

Both non-design outcomes (GC and G9) come from one cause, in the gates' construction. Each gate decides whether it is
looking at V4's criterion from the **test set alone, not from τ**. That is true of every run ID made so far, but not of
this one (§5).

**Both existing campaigns are untouched:**

| check | `census_tau1e-08` | `write_set_tau1e-06` |
|---|---|---|
| `--jobs campaign --resume` | 553 of 553 kept (`press35`) | 553 of 553 kept (`press37`) |
| `--paper-tables check` | IDENTICAL (`press36`) | IDENTICAL (`press38`) |

Under both folders together, `find -newermt '2026-10-02T10:36:38+02:00'` finds **0** of 27 019 entries (files and
directories).

## 2. The presses, in order

All presses ran from `MDA_partitioning_experiment_v5/`, in `PROCESS_surgery_env`, with `PYTHONDONTWRITEBYTECODE=1`, and
with `--test-set write_set --tau 1e-8` unless the row says otherwise. Run ID `write_set_tau1e-08`, as the harness names
it (`press01`).

| # | press | when | outcome |
|---|---|---|---|
| 00, 01 | `--runs`; `--jobs campaign` | 10:36 | run ID confirmed; 278 listed, 0 kept (as at A106) |
| 02a | `HARNESS_WORKERS=3 … --campaign --resume` | 10:37 – 10:40 | **stopped and discarded by me** (decision 1): 71 records made, split across two commits |
| 02 | the same, relaunched on a fresh folder | 10:40:56 – 11:49:23 | 3 references, 275 evaluations, 175 optimisations made; **then rc 1** at the first `B1` job: `InputFileError`, the lifted input file absent under this run ID (decision 2) |
| 03, 04 | `--copy-archived-records census_tau1e-08` (listing), then `--apply` | 11:49 | 1 935 files copied (293.5 MB), SHA-256 checked; the closing agreement check reads **NO** (§6) |
| 05 | `HARNESS_WORKERS=3 … --campaign --resume` | 11:50:03 – 12:15:30 | 100 made, 453 resumed; chain PASS, rc 0 |
| 06, 07 | `--jobs campaign --resume`; `run_stamp_survey.py --runs runs/write_set_tau1e-08 --launch-summary campaign` | 12:16 | 553 / 553 kept; 553 at `b44c88c4`, W 3, dirty 0 |
| 08 | `--archive-collisions` | 12:16 | before any gate (§6) |
| 09 | `--jobs all --resume` | 12:16 | 608 distinct jobs over 29 gates; GC, G2, G6 and GT not composable yet |
| 10 | `HARNESS_WORKERS=3 … --gate all --resume` | 12:16:36 – 12:24:36 | 17 PASS, then GC **REFUSED** (rc 3); the chain stops |
| 13–23 | the 11 later gates one by one, `--gate <name> --resume`, with a disk check before each | 12:25 – 12:32 | §5 |
| 24 | `--measure gate_table --resume` | 12:33 | 26 PASS, 1 FAIL, 2 not run |
| 25–27 | `--archive-collisions`; the copy listing; the copy `--apply` again, as a byte check | 12:33 | §6 |
| 28, 29 | `--timing validity`, `--timing cache-load` | 12:33 | no PROCESS run (§8) |
| 30, 31 | `--paper-tables write`; `paper_cells_recount.py --runs runs/write_set_tau1e-08 --document paper_tables_write_set_tau1e-08.md` | 12:33 | written; 44 rows, 0 mismatched |
| 11, 32, 33 | `compare_campaigns.py census_tau1e-08 write_set_tau1e-06 write_set_tau1e-08 [--output campaign_comparison.md]` | 12:20, 12:34 | §3; the committed output was generated at `ce8072ef` |
| 12 | `optimiser_path_split.py --runs runs/write_set_tau1e-08 --campaign-only --campaign-label ws1e-8` | 12:20 | §4 |
| 34–38 | `--paper-tables check` (this run ID), then the two existing run IDs' `--jobs campaign --resume` and `--paper-tables check` | 12:34 | IDENTICAL; 553 / 553 kept under each; IDENTICAL ×2 |
| 39 | `--runs` (default settings) | 12:34 | below |

**`--runs` reads, for `write_set_tau1e-08`:**
- 553 campaign records at `b44c88c4`;
- evaluation: 275 ok; optimisation: 247 ok, 28 crashed;
- 772 run records in the folder;
- 1.59 GB on disk, of which the campaign 1.16 GB;
- gate table 26 PASS of 29 (1 FAIL, 2 not run).

## 3. The three campaigns side by side

Every cell below is from `compare_campaigns.py` at `ce8072ef`, committed as `campaign_comparison.md`. That file has the
full tables: phase A outcomes, every phase B quantity, both cost sets.

Phase B is over each campaign's own seed set (every arm accepted). Phase A is over 25 displaced-entry evaluations per
arm.

### 3.1 Run outcomes, phase B (25 starts per arm)

Phase A: 25 of 25 `ok` in every arm on every configuration, in all three campaigns.

| config | arm | census 1e-8: acc / ifail≠1 / RE / cap | write set 1e-6 | **write set 1e-8** |
|---|---|---|---|---|
| `tok` | each of BR, B0, B1, B2 | 22 / 0 / 3 / 0 | 22 / 0 / 3 / 0 | **22 / 0 / 3 / 0** (RE seeds 5, 20, 21) |
| `lad` | BR | 12 / 11 / 2 / 0 | 12 / 11 / 2 / 0 | **12 / 11 / 2 / 0** |
| `lad` | B0 | 12 / 11 / 2 / 0 | 12 / 9 / 2 / 2 | **12 / 9 / 2 / 2** (cap seeds 4, 22) |
| `lad` | B1 | 12 / 11 / 2 / 0 | 11 / 9 / 2 / 3 | **11 / 9 / 2 / 3** (cap seeds 4, 10, 22) |
| `lad` | B2 | 12 / 11 / 2 / 0 | 11 / 9 / 2 / 3 | **11 / 9 / 2 / 3** (cap seeds 4, 10, 22) |
| `st` | BR | 24 / 1 / 0 / 0 | 24 / 1 / 0 / 0 | **24 / 1 / 0 / 0** (ifail 5: 17) |
| `st` | B0 | 24 / 1 / 0 / 0 | 23 / 2 / 0 / 0 | **23 / 2 / 0 / 0** (ifail 5: 10, 17) |
| `st` | B2 | 20 / 5 / 0 / 0 | 23 / 2 / 0 / 0 | **24 / 1 / 0 / 0** (ifail 5: 17) |

*acc = accepted (`ok`, `ifail = 1`); RE = `RuntimeError`; cap = the coupling loop's sweep cap (`ModuleSolveFailure`).*
"Other": 0 everywhere. Census `st` `B2`'s five are `ifail = 2` on seeds 1, 9 and 10, and `ifail = 5` on 15 and 17.

**Crashes at write set 1e-8: 28 = 20 `RuntimeError` + 8 loop caps.**

- **The 20 `RuntimeError`s** are the same 20 starts in all three campaigns.
- **The 8 caps are all on `lad`**, on the same starts and arms as at 1e-6. The cap stays at 20 and was not changed.
- **The cap's message** (the residual component it names), measured from the records' tracebacks:
  > block FLAT (`B0`, `B1`; **M1** on `B2`) did not converge in 20 sweeps at tau=1e-08; max scaled residual **inf**
  > on `current_drive.eta_cd_dimensionless_hcd_primary`, 1 components above tau.

  The 1e-6 caps name the same component.
- **No cap on `tok` or `st`.**

### 3.2 Phase A: module sweeps per evaluation, and the declared pair

Each cell lists the AR / A0 / A1 / A2 means, then the declared pair's ratio of means: `A2/A1` on the pulsed
configurations, `A2/A0` on `st`.

| config | module | census 1e-8 | write set 1e-6 | **write set 1e-8** |
|---|---|---|---|---|
| `tok` | M1 | 4.96 / 5.88 / 5.88 / 3.00 · 0.51 | 4.96 / 5.52 / 5.12 / 4.00 · 0.78 | **4.96 / 6.52 / 5.88 / 4.00 · 0.68** |
| `tok` | M2 | … / 5.88 · 1.00 | … / 5.16 · 1.01 | **… / 5.88 · 1.00** |
| `tok` | M3 | … / 2.00 · 0.34 | … / 3.00 · 0.59 | **… / 3.00 · 0.51** |
| `tok` | Feedforward / Post-processing | 1 · 0.17 | 1 · 0.20 | **1 · 0.17** |
| `lad` | M1 | 5.00 / 5.00 / 5.00 / 3.00 · 0.60 | 5.00 / 5.00 / 4.92 / 4.00 · 0.81 | **5.00 / 5.40 / 5.00 / 4.00 · 0.80** |
| `lad` | M2 | … / 5.00 · 1.00 | … / 4.88 · 0.99 | **… / 5.00 · 1.00** |
| `lad` | M3 | … / 2.00 · 0.40 | … / 3.00 · 0.61 | **… / 3.00 · 0.60** |
| `lad` | Feedforward / Post-processing | 1 · 0.20 | 1 · 0.20 | **1 · 0.20** |
| `st` | M1 | 4.92 / 5.96 / — / 3.00 · 0.50 | 4.92 / 5.84 / — / 4.00 · 0.68 | **4.92 / 6.96 / — / 4.00 · 0.57** |
| `st` | M2 | … / 5.96 · 1.00 | … / 5.84 · 1.00 | **… / 6.96 · 1.00** |
| `st` | M3 | … / 3.00 · 0.50 | … / 3.00 · 0.51 | **… / 3.96 · 0.57** |
| `st` | Post-processing | 1 · 0.17 | 1 · 0.17 | **1 · 0.14** |

**Node calls per evaluation, pooled, at write set 1e-8** (the tally's *per-call cost by configuration*):

| config | pair | ratio |
|---|---|---:|
| `tok` | A2/A1 | 0.5316 |
| `lad` | A2/A1 | 0.6000 |
| `st` | A2/A0 | 0.5501 |

### 3.3 Phase B: per run over the seed set, and the ratios of means

| config | campaign | n | iterations B2/B0 · B1/B0 · B2/BR | ε B2/B0 | ρ B2/B0 | **R (node calls per run) B2/B0 · B1/B0 · B2/BR** |
|---|---|---:|---|---:|---:|---|
| `tok` | census 1e-8 | 22 | 0.9942 · 0.9942 · 0.9942 | 1.0411 | 0.4821 | 0.5020 · 0.9721 · 0.5371 |
| `tok` | write set 1e-6 | 22 | 0.9942 · 0.9942 · 0.9942 | 1.0411 | 0.6144 | 0.6395 · 1.0077 · 0.6554 |
| `tok` | **write set 1e-8** | 22 | 0.9942 · 0.9942 · 0.9942 | 1.0411 | 0.5627 | **0.5859 · 0.9717 · 0.7204** |
| `lad` | census 1e-8 | 12 | 1.3658 · 1.3658 · 1.3658 | 1.4410 | 0.4884 | 0.7031 · 1.3284 · 0.6995 |
| `lad` | write set 1e-6 | 11 | 0.7012 · 0.7012 · 0.7012 | 0.7309 | 0.6183 | 0.4504 · 0.6919 · 0.4373 |
| `lad` | **write set 1e-8** | 11 | 0.7012 · 0.7012 · 0.7012 | 0.7309 | 0.5605 | **0.4091 · 0.6540 · 0.4713** |
| `st` | census 1e-8 | 20 | 2.4048 · — · 1.6915 | 2.4432 | 0.5101 | 1.2419 · — · 0.8434 |
| `st` | write set 1e-6 | 22 | 0.9530 · — · 0.7682 | 0.9512 | 0.5716 | 0.5331 · — · 0.4454 |
| `st` | **write set 1e-8** | 23 | 1.0115 · — · 0.8471 | 1.0126 | 0.5552 | **0.5582 · — · 0.5877** |

**The arm means at write set 1e-8** (iterations; node calls per run):

| config | iterations BR / B0 / B1 / B2 | node calls per run BR / B0 / B1 / B2 |
|---|---|---|
| `tok` | 7.818 / 7.818 / 7.773 / 7.773 | 41 480 / 51 005 / 49 563 / 29 883 |
| `lad` | 29.818 / 29.818 / 20.909 / 20.909 | 169 944 / 195 789 / 128 043 / 80 092 |
| `st` | 31.565 / 26.435 / — / 26.739 | 128 323 / 135 116 / — / 75 417 |

**Without the retried seeds** (the tally's *cost against both anchors*), at write set 1e-8, B2/B0 · B2/BR:

| config | n | B2/B0 | B2/BR |
|---|---:|---:|---:|
| `tok` | 22 | 0.5859 | 0.7204 |
| `lad` | 10 | 0.5976 | 0.6866 |
| `st` | 20 | 0.5615 | 0.7075 |

**BR→B0** (every arm accepted): `tok` 1.2296, `lad` 1.1521, `st` 1.0529. At 1e-6 these read 1.0250, 0.9709 and 0.8356.

**B3's ε label at write set 1e-8:**

| config | pair | label |
|---|---|---|
| `tok` | B0 → B2 | trajectory-neutral |
| `lad` | B0 → B2 | trajectory changed by ε = 0.7309 |
| `st` | B0 → B2 | trajectory-neutral, ε 1.0126 |

**`B1 → B2`** (the identity):
- `tok`: identical evaluations and iterations on 22 of 22; objective bit-identical on 20 of 22.
- `lad`: identical evaluations and iterations on 11 of 11; objective bit-identical on 3 of 11.

### 3.4 The rules

| config | campaign | A1 (declared pair median / p90, verdict; A2 runs with a component ≥ τ) | B1 (judged pair: objf median / p90 against 1e-6, verdict, hops) |
|---|---|---|---|
| `tok` | census 1e-8 | A2/A1 1.00 / 1.00, PASS; 0 | B0 → B1 and B0 → B2: 2.823e-11 / 4.570e-11, PASS, 0 hops |
| `tok` | write set 1e-6 | the same: PASS; 0 | the same: PASS, 0 hops |
| `tok` | **write set 1e-8** | **PASS** (1.00 / 1.00); 0 | **PASS**, 2.823e-11 / 4.570e-11, 0 hops |
| `lad` | census 1e-8 | PASS (both quantiles exactly 0); 0 | **FAIL** at p90: 5.829e-07 / 3.148e-04, 4 hops (1\*, 10\*, 11, 13) |
| `lad` | write set 1e-6 | PASS (exactly 0); 0 | **FAIL** at p90: 4.101e-07 / 2.148e-06, 3 hops (1\*, 11, 13) |
| `lad` | **write set 1e-8** | **PASS** (exactly 0); 0 | **FAIL** at p90: 4.101e-07 / 2.148e-06, 3 hops (1\*, 11, 13), entering at the lift `B0 → B1`, 3 of 3; the yardstick hops on 0 of 3 |
| `st` | census 1e-8 | A2/A0 1.00 / 1.00, PASS; 0 | **FAIL** at p90: 6.211e-12 / 1.305e-03, 3 hops (5\*, 12\*, 24\*) |
| `st` | write set 1e-6 | PASS; 0 | PASS: 3.467e-13 / 3.510e-09, 1 hop (12) |
| `st` | **write set 1e-8** | **PASS** (1.00 / 1.00); 0 | **PASS**: 2.936e-13 / 3.356e-10, 2 hops (12\*, 24\*); the yardstick hops on 1 of 2 (24\*) |

The tables document's verification row reads **"PASS tok, st · FAIL lad"**, the same as at 1e-6.

**Whole-state audit at write set 1e-8** (A1's quantities, median / p90 over 25 runs per arm):

| config | arm | median | p90 |
|---|---|---:|---:|
| `tok` | A1 | 5.159e-12 | 8.486e-11 |
| `tok` | A2 | 5.159e-12 | 8.486e-11 |
| `tok` | A0 | 5.253e-12 | 1.361e-10 |
| `lad` | every arm | 0 | 0 |
| `st` | A0 | 1.707e-10 | 2.901e-10 |
| `st` | A2 | 1.707e-10 | 2.901e-10 |

**A2** (fixed-point distance, reported): on the headline pair, the restricted median / p90 over 25 pairs:

| config | pair | median | p90 | pairs ≥ τ |
|---|---|---:|---:|---:|
| `tok` | A2/A1 | 5.6e-14 | 9.5e-13 | 0 of 25 |
| `lad` | A2/A1 | 0 | 0 | 0 of 25 |
| `st` | A2/A0 | 3.9e-13 | 6.6e-13 | 0 of 25 |

## 4. `st_regression`, the partitioned arm (A104's script)

`optimiser_path_split.py --runs runs/write_set_tau1e-08 --campaign-only --campaign-label ws1e-8`, run at `b44c88c4`
(`press12`). It needed **no change**. Its two options (A106) already cover a run ID without a supplementary stage.

As a check that it reads post-compaction records the same way, I re-ran it over `runs/write_set_tau1e-06` with A106's
label. Its output is **byte-identical** to A106's `press16` (`press00b`, `diff` empty).

**Where the accepted runs end, at a bound** (iteration variables within one finite-difference step of a bound the input
file sets; population: the accepted runs per arm):

| arm | runs judged | at a bound |
|---|---|---|
| BR | 24 of 24 | `f_nd_plasma_pedestal_greenwald` lower 0.1: 24; `f_nd_plasma_separatrix_greenwald` lower 0.001: 24; `hfact` upper 1.2: 24 |
| B0@ws1e-8 | 23 of 23 | the same three: 23 each |
| B2@ws1e-8 | 24 of 24 | the same three: 24 each; **nothing else** |

**The two bound counts the brief asks for, `st` `B2`:**

| bound | write set 1e-8 | write set 1e-6 | census 1e-8 |
|---|---|---|---|
| `dr_tf_nose_case` at its lower bound | **0 of 24** | 0 of 23 | 10 of 20 |
| `dr_tf_wp_with_insulation` at its upper bound | **0 of 24** | 5 of 23 | not reported |

**Other st `B2` figures (measured):**

- **`B0 → B2` classes over 25 starts:** identical 1, early 5, stall 1, shorter 14, retried 4.
- **Retried:** BR 5 of 25 finished, B0 3, B2 2.
- **Node calls per evaluation over the seed set (n = 23):**

  | arm | per evaluation | over BR's |
  |---|---:|---:|
  | B2 | 47.9 | 0.70 |
  | B0 | 86.8 | 1.26 |
  | BR | 68.7 | — |

  So `B2` is 0.55 of `B0`.
- **Hovering** (`n_near > 10`): BR 7 of 24, B0 4 of 23, B2 6 of 24.
- **Seed 12 and seed 24:** `B2` ends with the objective 1.3e-2 relative from `B0` on both, and both are retried. These
  are the two B1 hops of §3.4.
- **Seed 5:** `B2` was lost at 1e-6 (`ifail = 5`) and is accepted here in one attempt, 40 iterations against `B0`'s 39.

This section reports what the records show. It explains none of it.

## 5. The gate table under `write_set_tau1e-08`

Source: `--measure gate_table --resume` at `b44c88c4` (`press24`; record `runs/write_set_tau1e-08/gates/gate_table/measurements.json`).
Every verdict was pressed by this task at `b44c88c4`, except as marked. The read-once gates read their archived verdicts.

| gate | plan | verdict | compared | mismatched | teeth | press |
|---|---|---|---:|---:|---|---|
| `g0prime` | G0 | PASS | 77 | 1 (the approved model file) | 4/4 | 10 |
| `copy_identity` | — | PASS | 224 | 8 (declared edits) | 12/12 | 10 |
| `edit_behaviour`, `self_containment`, `composition`, `rungs`, `provenance`, `data`, `run_path`, `capability`, `artifacts_check`, `artifacts_derive_inputs`, `artifacts_census`, `artifacts_per_run` | — | PASS (each) | 3, 61, 53, 98, 4, 22, 12, 61, 119, 2, 81, 16 | 0 | all | 10 |
| `resume_identity` | — | PASS | 751 | 0 | 15/15 | 10 |
| `evaluation_warmup` | — | PASS (read once, D44; verdict at `c2295511`) | 19 876 | 0 | 5/5 | 10 |
| `record_completeness` | G7 | PASS | 281 | 0 | 14/14 | 10 |
| **`count_neutrality`** | GC | **NOT RUN (refused)** | — | — | —/4 | 10 |
| `prime_map` | G2 | PASS | 17 591 | 0 | 3/3 | 13 |
| `entry_and_warm` | G6 | PASS | 6 717 | 0 | 3/3 | 14 |
| **`test_set`** | GT | **NOT RUN (refused, by design)** | — | — | —/4 | 15 |
| `switch_composition` | G5 | PASS | 156 | 0 | 4/4 | 16 |
| `switch_neutrality` | G1 | PASS (straddle `9ed0da4c → b44c88c4`) | 54 973 | 0 | 9/9 | 17 |
| `reproduction` | GR | PASS (read once; verdict at `d6c246a1`, 27 archived records) | 256 | 0 | 8/8 | 18 |
| **`output_path`** | G9 | **FAIL** | 3 879 | **12** | 4/4 | 19 |
| `written_file_gap` | — | PASS | 42 | 0 | 4/4 | 20 |
| `tally_contracts` | — | PASS (236 of 236 reference cells; 302 table checks) | 538 | 0 | 18/18 | 21 |
| `run_kind_separation` | — | PASS (772 run records) | 1 878 | 0 | 7/7 | 22 |
| `stage_provenance` | — | PASS | 12 | 0 | 5/5 | 23 |

The 8 teeth not tripped are GC's 4 and GT's 4 (not run).

### GT: refused by design

`gate_test_set` refuses before any run when the campaign's test set is not `census`. Its message: *"…under the fallback
(D39) the loops test the write set and there is no census set to drop a component from. Press it with --test-set
census."* This is the same refusal as under `write_set_tau1e-06` (A109).

### GC (`count_neutrality`): refused, because of the gate's construction under a non-default τ

**The message** (`press10`):

> GC's before side ('item5') has no record for 22 of 22 job(s) — first:
> `A/AR/large_tokamak_nof/seed001/perturbed/gate/delta=0.1/tau=1e-08/overridden`, …

**The cause, by function and line.** GC's sides are declared under the write set, at its default τ
(`STRADDLE_TEST_SET`, `harness/gates/gate_count_neutrality.py:116`). `count_neutrality_body` (lines 823–832) replaces the
campaign with the declared one, `dataclasses.replace(campaign, test_set=declared_set, tau=None)`. **It does so only when
`campaign.test_set != declared_set`.**

**What that does under each run ID:**
- **Census:** the test set differs, so the campaign is replaced, and τ falls to the write set's default, 1e-6.
- **`write_set_tau1e-06`:** τ already is that default.
- **`write_set_tau1e-08`:** the test set matches, so the campaign is kept with τ = 1e-8 (overridden). GC composes 22
  before-side jobs at 1e-8, and no record of them exists anywhere: the archived `item5` side was made at 1e-6.

**What the press made.** Before refusing, the press made the three `A0` seed-0 entry references at 1e-8 in the shared
pool. They are stamped `b44c88c4`, and G6 and G2 read them later.

**Not worked around.** GC was not pressed again, the gate was not changed, and no other settings were tried. Making it
press needs a decision on GC's construction, or a before side at 1e-8, which cannot be made because the before side is
the commit before the change.

### G9 (`output_path`): FAIL, by the same construction

**What failed** (`press19`; record `runs/write_set_tau1e-08/gates/output_path/gate.json`). Every arm whose loop the matrix
removes passes on all three configurations: `B1` and `B2` on `tok` and `lad`, and `B2` on `st`. That is 3 825 components
compared in hex, 0 differing, and objective and sweep checks all ok.

The FAIL is the reference arms' sub-check, *"nothing about the solve changed on the reference arm"*. G9 compares each
run's 9 solve-describing fields with GR's archived record of the same arm.

- **`BR`:** 0 of 9 differ, on all three configurations.
- **`B0`:** 4 of 9 differ, on all three:

  | config | `node_calls_solve_phase` (GR → here) | `n_model_calls` (GR → here) | `norm_objf` |
  |---|---|---|---|
  | `tok` | 43 449 → 52 416 | 2 072 → 2 499 | differs in its last hex digits |
  | `lad` | 86 877 → 103 362 | 4 140 → 4 925 | differs in its last hex digits |
  | `st` | 42 756 → 51 366 | 2 039 → 2 449 | differs in its last hex digits |

  `node_calls_total` differs too. Iterations, `ifail`, attempts and iterations summed over attempts are equal.

**The cause, by function and line.** `gate_output_path.py:446–449` gates this sub-check only where the two runs share a
criterion:

```python
same_criterion = arms_mod.ARMS[arm].is_reference or campaign.test_set == V4_TEST_SET
```

Its comment says GR's record is "the fallback test set at 1e-6". The condition tests the test set and not τ. So `B0`,
whose loop stops at τ = 1e-8, is gated against V4's run at 1e-6.

The measured differences are the size a tighter loop gives: about +20 % node calls, with the objective moving in the last
digits. **That attribution is inferred, not tested.**

**Not worked around.** The gate was not changed or pressed again.

**What the verification table reads** (`paper_tables_write_set_tau1e-08.md`): G0 PASS, **G1 PASS**, A1 PASS, A2 reported,
B1 "PASS tok, st · FAIL lad", G6 PASS, G5 PASS, **G9 FAIL**, GT not pressed. G1 now passes across two trees, which is
A110's fix holding. Until the G9 construction is ruled on, the document should not be cited as verified on G9.

## 6. Archives and collisions

### `--archive-collisions`, before any gate (`press08`)

**No collision listed.** The survey read:

- **GR:** 28 archived records, 27 identities, 27 in the read-only archive. 26 other-gate jobs resolve into it, all
  readers: `tally_contracts` 20, and G9's 6 seed-0 reference arms (`asked_by=reproduction`). This is the same as under
  both other run IDs (A112).
- **G1:** 54 archived records, 12 identities. GR's 3 AR jobs carry capture identities and resolve elsewhere; 0 resolve
  into G1's captures.
- **Warm-up gate:** 22 archived records; 0 jobs. **Derived input files:** 0 records.
- **Not composable yet:** GC's job set, and the jobs of gates GC, G6, G2 and GT. The reason: *"the entry reference for
  large_tokamak_nof did not finish or is not made"* (the `A0` seed-0 gate job at 1e-8).

**So the survey could not measure the I-42 class before a gate press.** It needs references that only a gate press makes.

### The same survey after the gates (`press25`)

GR, G1, the warm-up gate and the input files read as before. GC now composes:

> count_neutrality: 3 archived record(s) … other gates' jobs carrying an archived identity: 9; resolving into the
> archived directory: 9 (9 of them by a gate that makes runs) — entry_and_warm 3, prime_map 3, test_set 3, each
> `A/A0/<configuration>/seed000/unperturbed/gate/tau=1e-08`.

**This is I-42's shape. The records involved are not copied archive records.** The "3 archived records" are the 1e-8 entry
references that this task's GC press made at `b44c88c4` (above). Under this run ID, GC's job set names them because it
composes at 1e-8. G6 and G2 read them as their own references, made by the same driver at the same commit. The survey
lists it, and I report it. I did not act on it.

### Did any gate write into a copied archive? No (measured, `press27`)

Re-running `--copy-archived-records census_tau1e-08 --apply` refuses if any destination file has other bytes. It reported:

> copied 0 file(s); 1935 already present with the same bytes

The copy record was left as made. **All 1 935 copied archive files are byte-identical to census's after every gate.**

**The copy step's agreement check reads NO, at both presses:**

- **Before the gates** (`press04`): GC's job set was not composable.
- **After the gates** (`press27`):
  - reproduction: 29 jobs, keeps 3, under both run IDs; 0 differ.
  - count_neutrality: 47 jobs under each; `--resume` keeps 3 here against 36 under census; **94 job/decision rows
    differ.**

  The cause is GC composing at 1e-8 here, the same as GC's refusal (§5).

## 7. Disk

From `disk_log.txt` (`df -h /mnt/c`):

| when | C: free |
|---|---|
| 10:37, before the campaign | 132 GB |
| 11:49, before the copy | 131 GB |
| 12:15, after the campaign | 131 GB |
| before `--gate all` and before each of the 11 single presses | 131 GB |
| 12:34, end | **131 GB** |

The floor (20 GB) was never approached.

**This run ID:** 1.59 GB on disk, of which the campaign 1.16 GB and the copied archives 293.5 MB.

The first launch's discarded folder (54 MB) is in my session scratchpad, not in the repository (decision 1).

## 8. The wall-clock stages (context, never evidence)

`--paper-tables write` needs two timing stage records. I pressed both, as A106 did. Neither makes a PROCESS run.

- `--timing validity`: no W = 1 repetitions exist under this run ID, and none was wanted. So each of its 22 jobs reads
  "no repetition record", and the stage reads "appendix timings from: not decidable yet".
- `--timing cache-load`: reads the campaign's own records.

The tables document's wall-clock tables are therefore the campaign's W = 3 records, with no validity check behind them.
**No number in this report is a timing.** Progress context only: the campaign took 10:40:56–11:49:23 and 11:50:03–12:15:30.

## 9. Decisions taken alone, each with its reversal

1. **I discarded the first launch and relaunched from scratch.**
   - *What happened:* three minutes in, I committed `compare_campaigns.py` (`b44c88c4`) while the press ran. A stamp
     read taken just after the commit found 66 records: 49 at `a75d024b`, 14 at `a75d024b` listing the then-untracked
     script in `tree_untracked_paths`, and 3 at `b44c88c4`. The folder held 71 records when writing stopped.
   - *What I did:* I stopped the background task (`TaskStop`), confirmed from the files that writing had stopped, and
     moved the whole new folder (71 records, 54 MB) out of `runs/` into my scratchpad by `mv`. I then relaunched, so that
     all 553 carry one commit and no untracked path.
   - *What I did not do:* nothing under the two existing run IDs was touched. No commit was made during any later press.
   - *Reversal:* none needed. The discarded records exist only in the scratchpad.
2. **The read-only archives were copied in mid-campaign, not before the gates.**
   - *Why:* the relaunched press stopped (rc 1) at the first `B1` job. The lifted input files of `tok` and `lad` are
     absent in a new run ID. Under `write_set_tau1e-06` they came from A107's copy step before A106's campaign.
   - *What I did:* the brief's own step 3 command brings them in (`--copy-archived-records census_tau1e-08 --apply`), so
     I ran it then and resumed with `--resume`. This is no harness change: the lifted file is gated on its committed
     digest, and gate `artifacts_derive_inputs` PASSes.
   - *Reversal:* none. The copy is what step 3 would have made anyway.
3. **The gates after GC's refusal were pressed one by one**, as the brief asks, with a disk check before each. One
   background loop, one log per gate. The loop launched them and produced no number. Reversal: none needed.
4. **The archive byte check uses the copy's own `--apply`** (`press27`). It refuses on any byte difference and otherwise
   copies nothing and leaves the copy record. Reversal: none; it wrote nothing.
5. **The timing stages without a W = 1 pass** (§8), as A106 decided. Reversal: delete
   `runs/write_set_tau1e-08/timing/{validity,cache_load}/`; the tables document then refuses to render.
6. **A new script, not an extension.** `paper_cells_recount.py` prints one run ID against its document and has no
   multi-campaign or rule-verdict path, and A106's comparison was by hand from tables documents. So I wrote
   `compare_campaigns.py`:
   - it imports `paper_cells_recount` for phase A and the arm-name translation (T16);
   - it reads the outcomes from `metrics.json`;
   - it reads phase B and the rules from each run ID's tally stage records, and refuses a record stamped with another
     run ID.

   Over `write_set_tau1e-06` its phase B ratios equal A106's published ones (0.6395 / 0.4504 / 0.5331; ρ, ε and the
   anchors likewise). Reversal: `git revert b44c88c4 d9a2f32f`.
7. **`optimiser_path_split.py` was not changed.** It needed nothing.

## 10. The unexpected

1. **On `tok` and `lad`, phase B at write set 1e-8 walks the same optimiser paths as at 1e-6.** The following are
   identical to 1e-6 per arm:
   - the iteration means, the evaluation counts ε, the seed sets (22, 11), the outcomes, and the cap seeds;
   - the B1 numbers, 2.823e-11 / 4.570e-11 on `tok` and 4.101e-07 / 2.148e-06 on `lad`, with hops 1\*, 11, 13.

   Only node calls per evaluation (ρ) and the objectives' last digits move: on `lad` the partition step is bit-identical
   on 3 of 11 here.
2. **`st` differs.**
   - The seed set is 23: B2 accepts 24, with seed 5 recovered.
   - The two bound counts fall to 0 of 24 each.
   - B1's hops are 12\* and 24\*, against 12 at 1e-6.
3. **`BR → B0` exceeds 1 on every configuration** (tok 1.2296, lad 1.1521, st 1.0529, every arm accepted). The flat loop
   at 1e-8 costs more per run than upstream's own loop. So `B2/BR` (0.7204 / 0.4713 / 0.5877) rises against 1e-6 while
   `B2/B0` (0.5859 / 0.4091 / 0.5582) falls.
4. **The campaign could not complete in a fresh run ID before the archived records were copied** (decision 2). The brief
   ordered the copy after the campaign. The harness's own error message names the fix.
5. **GC refuses and G9 FAILs under this run ID**, both because a gate keys "V4's criterion" on the test set alone (§5).
   This is the first run ID whose test set is V4's and whose τ is not.
6. **`--archive-collisions` cannot see GC, G6, G2 or GT in a fresh run ID before a gate press.** After the presses it
   lists I-42's shape (9 jobs) over records this task made (§6).
7. **The first launch was split across two commits by my own commit** (decision 1).

## 11. What I did not check

- **Whether GC's and G9's τ-blindness is a defect or a scope decision.** I read the lines and report the cause. I did not
  test a change, and none was made.
- **Why `tok` and `lad` keep 1e-6's paths at 1e-8 while `st` does not.** §10.1 is a measurement, not an explanation.
- **Whether 1e-8 or 1e-6 is the right setting.** Not this task's question.
- **The wall-clock tables of the tables document:** not read beyond the generator's own cross-checks. No timing is
  cited.
- **G2 part (ii)** ("GC's DR9/DR10 straddle, 6 primed pairs, 12 565 components") PASSes. Its runs line says all 15
  records read are at `b44c88c4`. I did not read which straddle files part (ii) took under this run ID.
- **The B4 table (constraint 93)** and the full tally tables: in the stage records, not re-quoted.
- **The discarded first-launch records:** I did not check their contents beyond the stamp read of 66 of the 71
  (decision 1). They are not published anywhere.
- **The "existing folders untouched" claim** rests on modification times (`find -newermt`) and on the two committed
  checks per run ID. I did not hash every file before and after.

## 12. Orchestrator's critical assessment (protocol §5) — verdict: merge

*Written 2026-10-02 by the orchestrating session. Checked differently from the agent.*

**Checked.** (1) `git diff --name-only a75d024b..04eb25a9`: four files — `compare_campaigns.py` (new, read-only),
`campaign_comparison.md` (its output), `paper_tables_write_set_tau1e-08.md` and this report; 0 diff lines under the V5
driver copy, `process/`, the harness or V4; worktree clean; the script compiles. (2) `--runs` at the tip:
`write_set_tau1e-08` holds 553 campaign records, all at `b44c88c4`; gate table 26 PASS, 1 FAIL, 2 not run. (3)
`--paper-tables check` reads IDENTICAL under the three settings (cross-check 0 of 178 each). (4) The two older run-ID
folders: `find -newermt '2026-10-02T10:30:00+02:00'` lists 0 entries. (5) **The headline ratios recounted by the
orchestrator from the 275 phase B `metrics.json`, not through the agent's script** (`node_calls_solve_phase` summed over
the starts every arm accepted): `B2/B0` 0.5859 / 0.4091 / 0.5582 and `B2/BR` 0.7204 / 0.4713 / 0.5877, seed sets
22 / 11 / 23, accepted counts as §2 — the agent's figures to the last digit; the same recount gives the two older
campaigns' published ratios (0.6395 / 0.4504 / 0.5331 and 0.5020 / 0.7031 / 1.2419). (6) **A check the agent did not
make**: the distance between the partitioned arm's final design and the flat arm's (`B2` against `B1`, on `st` against
`B0`; the largest relative difference over the iteration variables, per start). `st`: census 1e-8 median 9.4e-01, 14 of
20 starts above 10 %; write set 1e-6 median 3.8e-06, 4 of 22 above 10 %; **write set 1e-8 median 4.6e-08, 1 of 23
above 10 %**. `tok` and `lad`: 0 starts above 10 % in every campaign (medians ≤ 1.2e-11). So the walk of `st`'s
partitioned arm along the flat direction, present at census 1e-8, is absent under the whole write set at 1e-8, in
agreement with the agent's two bound counts (0 of 24 each). This is the orchestrator's ad-hoc reading of the records,
not a committed script's output, and is not to be published as such. (7) The two gate conditions the agent cites, read
in the code: `gate_count_neutrality.py:823–832` and `gate_output_path.py:446–449` both compare the test set with V4's
and do not look at τ.

**The two gates (issue I-43, filed at merge).** Under a run ID whose test set is V4's and whose τ is not, GC composes
its sides at the run ID's τ and finds no before side, and G9 gates `B0` against GR's archived τ = 1e-6 record. Both are
the gates reading "V4's criterion" as "the whole write set" where V4's criterion is "the whole write set at 1e-6". The
G9 differences (node calls about +20 % on `B0`, `norm_objf` in the last hex digits; iterations, `ifail` and attempts
equal) are what a tighter loop gives; that this is all they are is the agent's inference and the orchestrator's too, not
a measurement. **The gate table of `write_set_tau1e-08` therefore reads 26 PASS, 1 FAIL, 2 not run, and the tables
document's verification table carries the G9 FAIL.** Nothing was changed to make either pass, and nothing is changed at
merge. The campaign's cells do not depend on either gate: G9 compares against another setting's record, and GC's
straddle is a claim about the τ = 1e-6 fallback.

**I-42, now observed.** After the gate presses the collision survey lists nine jobs (G6, G2, GT) resolving into GC's
three entry-reference records, which under this run ID are records this task made, not copied ones. Nothing was
overwritten. The issue stays open; its row gains this observation.

**The agent's decisions.** Discarding the first launch (records split across two commits by the agent's own commit) and
relaunching is what "from scratch means the stamps say so" asks for. Running the archived-records copy mid-campaign was
forced by the lifted input files not existing in a fresh run ID; the brief had the order wrong, and the next campaign's
brief puts the copy first. The two timing stages without a single-worker pass follow A106.

**Limits carried.** The wall-clock tables have no validity check (no single-worker pass). The untouched-folders claim
rests on modification times and the committed checks, not on per-file hashes. Why `tok` and `lad` walk the τ = 1e-6
paths at 1e-8 while `st` does not is not explained. Which setting the paper's tables carry remains the user's question
(OQ-tolerance, open).
