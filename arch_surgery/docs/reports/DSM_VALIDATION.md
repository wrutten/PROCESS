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

## V6 — The DSM is config-specific, and matches only two of our four scenarios

**This is the most consequential entry in this register, and it was not previously recorded
anywhere.**

The dependency analysis resolves conditionals against a `ProcessConfig`. Its `tokamak` preset —
`dependency_analysis/core/inputs/config.py`, `tokamak_default` — is built from
**`examples/data/large_tokamak_IN.DAT`**, and every module boundary this project quotes (M1 = rows
4, 6-28; M2 = rows 5, 29-37; M3 = rows 40-51) was derived under that configuration. A different
deck resolves different branches and can therefore produce a different graph.

Switch-by-switch comparison of the four experiment scenarios against the DSM's source deck
(only differing switches shown):

| switch | DSM source | `large_tokamak_nof` | `low_aspect_ratio_DEMO` | `st_regression` | `large_tokamak_eval` |
|---|---|---|---|---|---|
| `i_plasma_geometry` | 0 | 0 | **10** | 0 | 0 |
| `i_single_null` | 1 | 1 | 1 | **0** | 1 |
| `i_plasma_current` | 4 | 4 | 4 | **9** | 4 |
| `i_beta_component` | 1 | 1 | 1 | **3** | 1 |
| `i_beta_fast_alpha` | 1 | 1 | 1 | **unset** | 1 |
| `i_confinement_time` | 34 | 34 | 34 | **unset** | 34 |
| `i_hcd_primary` | 10 | 10 | 10 | **13** | 10 |
| **`i_pulsed_plant`** | **1** | **1** | **1** | **0** | **1** |
| `pulsetimings` | 0 | 0 | 0 | **unset** | 0 |
| `i_div_heat_load` | 2 | 2 | **unset** | **unset** | 2 |
| `inuclear` | 1 | 1 | 1 | **0** | 1 |
| `i_cs_superconductor` | 1 | 1 | **5** | **unset** | 1 |
| `i_pf_superconductor` | 3 | 3 | 3 | **9** | 3 |
| `output_costs` | 1 | 1 | **0** | 1 | 1 |
| `i_tf_sc_mat` | 1 | 1 | **5** | **9** | 1 |
| `itart` | unset | unset | unset | **1** | unset |
| `i_tf_sup` | unset | unset | unset | **1** | unset |
| `i_blanket_type` | unset | unset | **1** | **1** | unset |
| `i_tf_turn_type` | unset | unset | unset | **2** | unset |

(14 further config switches are identical across all five decks, `istell` and `ife` among them.)

**Verdict, per scenario:**

| Scenario | Correspondence | Standing of the module decomposition |
|---|---|---|
| `large_tokamak_nof` | **exact** on every switch the config models | **Authoritative.** The DSM was generated for this configuration |
| `large_tokamak_eval` | **exact** | **Authoritative.** (Same deck family, evaluation mode rather than optimisation) |
| `low_aspect_ratio_DEMO` | **5 switches differ** — plasma-geometry model, CS and TF superconductor materials, blanket type, cost output | **Probably sound, unverified.** The differences select alternative correlations *within* M1 and M2 nodes rather than obviously adding or removing edges — but "probably" is not "measured" |
| `st_regression` | **12 switches differ**, including `i_pulsed_plant`, `itart`, `i_single_null`, `i_plasma_current` and the TF path | **Extrapolation, not measurement.** It corresponds to *none* of the tool's presets — closest is `tart` (`itart=1`), which also sets `i_tf_sup=0` where this deck sets `1` |

**Consequence for the partition experiment.** The Phase A *predicate* is unaffected: the coupling
set is derived from run-time instrumentation (`y` set (b)), not from the DSM. What depends on the
DSM is the **block arm's module boundaries**. So:

- On `large_tokamak_nof` and `large_tokamak_eval` the block arm rests on a DSM generated for
  exactly that configuration.
- On `low_aspect_ratio_DEMO` it rests on a near neighbour.
- **On `st_regression` it rests on an extrapolation**, and the partition plan's §4.2 previously
  named `st_regression` as the *most promising* scenario for a block-vs-flat win. That
  recommendation now carries a caveat: its `k = 0` claim is run-time measured by A2 and stands,
  but *which node belongs to which module* there is imported from a different configuration.

**Available fix.** The tool builds a config from any `IN.DAT` through PROCESS's own
`INPUT_VARIABLES` registry (`ProcessConfig.from_scenario`), so a per-scenario DSM is a supported
operation rather than new work. **Requested of `PROCESS_code_analysis`:** regenerate the collapsed
DSM for `st_regression` and `low_aspect_ratio_DEMO` and report whether the module decomposition
survives. Until then, block-arm results on those two scenarios carry this caveat.

**Also note:** the DSM source deck is `examples/data/large_tokamak_IN.DAT`, which is **not** one of
the four experiment scenarios. `large_tokamak_nof` is a regression deck. They agree on every
modelled switch, but they are different files, and no result should describe the DSM as having
been generated "from our scenario".

---

## Open

- **The collapsed DSM's 56 rows do not map one-to-one onto the 26 `run()` calls** in
  `_call_models_once`. Node-count weighting (`|M1| = 24`, `|M2| = 10`, `|M3| = 12`, `|all| = 52`)
  is therefore in DSM-row units, not model-call units. This has not caused an error, but the two
  units are easy to confuse in a cost argument and the node map (C8) should carry both.
- **Rows 1-3 and 56 are not executed inside a sweep** (`COOR_SingleRun`, `VMCON`,
  `MDA_Idempotence`, `MDA_Output`). An earlier revision of the partition plan used `|all| = 56`;
  the correct figure is 52. Corrected by A2.
