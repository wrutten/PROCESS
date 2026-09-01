# DSM validation — findings against the dependency analysis

> **Document status** — CURRENT · **accumulating, never archived** · opened 2026-09-01 (D13, C10).
> Unlike task reports, this document is **not** moved to `deprecated/` at merge. It accumulates
> across tasks and is a deliverable back to the dependency-analysis study.

**Base commit:** `c0ae5b28` · **DSM pin:** `PROCESS_at_36ac820e` (descends from `c0ae5b28`, so the
coordinate systems match) · **Instrument:** `PROCESS_code_analysis/dependency_analysis`, run in
`ESL_env`, pinned at `ANALYSIS_PIN_NAME` in `dependency_analysis/core/inputs/config.py`.

## Why this document exists

The experiment framework computes the coupling-variable set **two ways** — from run-time
instrumentation, and from the DSM's feedback edges (EXPERIMENT_FRAMEWORK.md §2.4). When they
disagree, one of them is wrong, and which one is a finding worth keeping.

The project has already accumulated several such findings by accident, each rediscovered
independently. This register exists so the next one is not rediscovered a fourth time.

**Rule (project admin §11).** Anything found to be wrong, missing or misleading about the DSM gets
an entry here — the edge, the evidence, which artifact is wrong, and the consequence — at the time
it is found, not at write-up.

## Findings

| # | Edge / claim | Evidence | Verdict | Consequence |
|---|---|---|---|---|
| **V1** | `pfcoil` -> `physics.b_plasma_vertical_required`, read by `plasma_fields` (row 10, M1) — an apparent M2 -> M1 back edge | The read is inside `PlasmaFields.output()`, whose only caller is `output()`, not `run()` | **Analysis method wrong, DSM not consulted at the right granularity.** Name-level analysis conflates `run()` and `output()` paths | Trap **T1**. The instrument must exclude `output()` paths. Three instances found so far, one of them in the partition plan's own central section |
| **V2** | `pfcoil.py:2727` reads `t_plant_pulse_burn`, making the burn-time edge symmetric | The line is inside `PFCoil.outvolt()`, reached only from `PFCoil.output()`. Run-time instrumentation sees no read by `pfcoil` inside the MDA | **Same as V1** — second instance | The `M1 -> M2 -> Pulse -> M1` cycle survives; the claimed M2-side read is withdrawn |
| **V3** | `build.dr_fw_inboard` / `dr_fw_outboard`: `FirstWall` (M3, row 41) -> `Build` (M2, row 5) | Structurally present. Run-time census, all four scenarios: **the value never changes between sweeps** — it is a function of two pure inputs no model computes | **DSM correct, but the edge is dead in this deck** | `k = 1` stands. If a future model computes `radius_fw_channel` or `dr_fw_wall`, this edge goes live and the partition gains a coupler |
| **V4** | `pf_power.vpfskv`: `Power` (M3, row 48) -> `Pulse` (row 39) | Structurally present; the value is the literal `20.0e0` | **DSM correct, edge dead** | As V3 |
| **V5** | `Pulse` (row 39) writes three fields, including `pulse.i_pulsed_plant` | Regex artefact — `= ` matched `== 1`. `Pulse` only *reads* that switch. Run-time census: exactly two writes in pulsed scenarios, **zero** in `st_regression` | **Extraction method wrong**, not the DSM | Trap **T2**. `Pulse` has exactly two state writes, which is what makes it feed-forward post-lift |

## Open

- **The collapsed DSM's 56 rows do not map one-to-one onto the 26 `run()` calls** in
  `_call_models_once`. Node-count weighting (`|M1| = 24`, `|M2| = 10`, `|M3| = 12`, `|all| = 52`)
  is therefore in DSM-row units, not model-call units. This has not caused an error, but the two
  units are easy to confuse in a cost argument and the node map (C8) should carry both.
- **Rows 1-3 and 56 are not executed inside a sweep** (`COOR_SingleRun`, `VMCON`,
  `MDA_Idempotence`, `MDA_Output`). An earlier revision of the partition plan used `|all| = 56`;
  the correct figure is 52. Corrected by A2.
