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

(14 further switches from the population below are identical across all five decks, `istell` and
`ife` among them.)

> **The counts are population-dependent, and the population must be stated (corrected
> 2026-09-01).** The `PROCESS_code_analysis` executor could not reproduce "12 / 5" under any
> denominator built from `ProcessConfig`'s own field set — it gets all-fields **17 / 7**,
> minus-derived **15 / 7**, set-in-both **8 / 4**. Both sides are right: **these are different
> field populations, so it is a non-comparison rather than a correction**, and the fault is that
> this entry first published a bare count.
>
> **Our population, stated so the number is reproducible:** 33 hand-selected switch names, grepped
> directly from the decks, **not** `ProcessConfig`'s field set — it adds `itart`, `i_tf_sup`,
> `i_blanket_type`, `i_tf_turn_type`, `i_plasma_ignited`, `i_rad_loss` (which the presets carry
> only for the non-tokamak configs) and omits fields `ProcessConfig` derives rather than reads.
> Method: strip `*` comments, match `^<name>\s*=\s*<value>`, treat **absent from the deck as a
> distinct value**, and count a switch as differing if value-or-absence differs. That last choice
> is why our counts run lower than the all-fields denominator: a switch absent from *both* decks
> counts as agreeing here.
>
> **What survives every denominator, and is the only load-bearing claim:** `st_regression` diverges
> from the DSM's source deck roughly **twice as far** as `low_aspect_ratio_DEMO`, on all four
> denominators (17/7, 15/7, 8/4, 12/5). The verdict table below rests on the ordering and on
> *which* switches differ — `i_pulsed_plant`, `itart`, `i_single_null`, the TF path — never on the
> count itself. Quote the ratio, not the integer.

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

**Available fix — requested, approved, and executing.** The tool builds a config from any `IN.DAT`
through PROCESS's own `INPUT_VARIABLES` registry (`ProcessConfig.from_scenario`), so a per-scenario
DSM is a supported operation rather than new work.

**Status, 2026-09-01:** registered by `PROCESS_code_analysis` as **M100 (run-all-scenarios)**,
approved by their user, now executing and slot-gated behind a gate suite. It adds a
`run_all_scenarios` entry point beside `main.py` / `overlap_dsm.py` / `serve_dsm.py`, emitting
**collapsed unsequenced HTML only** for the two extra decks, into **per-scenario output
directories**. Both riders were accepted into the executor's brief: the D9 provenance note travels
with our patched `st_regression` deck, and post-init generation asserts the imported tree rather
than trusting the environment.

**Deck integrity.** Our hashes were published to them *before* the copy, so their verification is a
comparison rather than a self-check:

| Deck | sha256 | bytes |
|---|---|---|
| `st_regression.IN.DAT` | `3f33d565b47dfef36eb4f40e63f26733f554194c09f1564e9d2f95d2e96ac5c7` | 136 043 |
| `low_aspect_ratio_DEMO.IN.DAT` | `72845515cdd9779c3b1c2f09f344c6f9ce626576e8e788e71d4df817bd828248` | 30 325 |

Both tracked on `architecture_surgery`, working tree clean; `st_regression` last changed in
`3baf34b8` (the D9 patch). A mismatch means the copy is wrong and M100 must not proceed on it.
This precaution exists because the deck was **not** under version control until I-9 was found — the
root `.gitignore`'s `*.DAT` swallowed it — so deck provenance is checkable now and was not before.

**RESOLVED, 2026-09-01 — the partition SURVIVES both scenarios. The withdrawal condition is NOT
triggered.**

`PROCESS_code_analysis` regenerated per-scenario collapsed DSMs (their M100). Result:

| Scenario | Model layer | Cross-module cells | Verdict |
|---|---|---|---|
| `low_aspect_ratio_DEMO` | identical, 52 nodes | **55 / 55 identical** — none new, none lost | **survives outright** |
| `st_regression` | 52 nodes, two substitutions | **zero new**; 9 lost, ~23 intra-module lost | **survives**, boundaries intact |

**Losses never break a block partition** — removing an edge cannot create a cycle across a
boundary. Only *new* cross-module cells could, and there are none.

**The row mapping is independently confirmed.** They resolved our rows through the export's
`supermodel_execution_order` (+3 for the driver rows at 1–3) and our ranges land on **exact
semantic boundaries** under it: M1 ends precisely at `ImpurityRadiation` (28), M2 precisely at
`CSCoil` (37), M3 = `Divertor` … `Availability` (40–51). Ranges chosen independently landing on
semantic joints is strong evidence the mapping is right rather than coincidental.

**Two substitutions in `st_regression`, both boundary-respecting — and both already handled here:**

1. `CICCSuperconductingTFCoil` → `CROCOSuperconductingTFCoil`, a drop-in inside M2 (the
   `i_tf_turn_type` flip, i.e. our D9 patch). Its entire coupling neighbourhood is CICC's.
   **Our node map already carries both** (`cicc_sctfcoil` and `croco_sctfcoil`, both M2), and both
   are top-level `run()` calls behind a branch at `caller.py:321` / `:328`.
2. `ElectronCyclotron` is new (the `i_hcd_primary` flip) and couples only with `CurrentDrive` and
   `Physics`, both M1. **It is not a node at our granularity** — constructed at `main.py:681` and
   passed *into* the physics-orchestrated block, never a top-level `run()`.

`CsFatigue` disappears (row 38, outside the partition). One new intra-M3 cell,
`CCFE_HCPB → Availability`.

**Membership refinement adopted:** M2 contains *"the TF coil model, selected by `i_tf_turn_type`"*,
**not** a named class. Describing a module by a class name is what would have made this look like a
structural change when it is a substitution.

**Why our map needed no patch, and what that vindicates.** The map and the coupling set are derived
from **runtime instrumentation across all four scenarios** (`y` set (b)), not from the DSM's
single-deck graph (set (a)). A map built from the DSM alone would have been wrong for
`st_regression` and would need patching now. **The choice of (b) over (a) was made on the argument
that the DSM might be incomplete; it has now been tested against exactly that failure and held.**

**Artefacts** (regenerated on their merged `3f8a822`; both decks sha256-verified against our
published hashes before every run):

- `dependency_analysis/output/st_regression/{dsm_collapsed.html, process_dependencies.json, diagnostics.txt}` — 2 580 nodes / 16 928 edges
- `dependency_analysis/output/low_aspect_ratio_DEMO/{same three}` — 2 667 / 18 291
- **Compare these by `diagnostics.txt`, never by the html/json hashes** — those embed run-specific
  UUIDs. The `diagnostics.txt` hashes were byte-identical across two independent runs and are the
  content-identity witness.

**Consequence:** `st_regression`'s block-arm result no longer carries the extrapolation caveat, and
the pre-committed withdrawal does not fire. The two large tokamaks still lead the write-up on the
separate ground that their DSM was generated for exactly their configuration.

## V7 — The DSM's feedback-edge set is not a usable convergence predicate

**Filed by A18 (experiment-framework), 2026-09-01.** This is the C10 cross-check the framework was
built to run: the coupling set is computed **two ways** — from run-time instrumentation (*set (b)*,
every field written by a model inside `Caller._call_models_once`) and from the DSM's cross-module
feedback edges (*set (a)*, the four fields in V2–V5) — and the sweep at which each *would have*
declared convergence is recorded for every design point.

Flat Gauss-Seidel, τ = 1e-6, all harvested design points, four scenarios:

| Scenario | points | set (a) stops **earlier** | agree | set (a) stops later | mean sweeps set (a) would have skipped |
|---|---|---|---|---|---|
| `large_tokamak_nof` | 149 | **142 (95.3 %)** | 7 | **0** | 0.96 |
| `low_aspect_ratio_DEMO` | 297 | **282 (94.9 %)** | 15 | **0** | 1.12 |
| `st_regression` | 144 | **135 (93.8 %)** | 9 | **0** | 2.44 |
| `large_tokamak_eval` | 10 | **7** | 3 | **0** | 1.20 |

**Never once later, in 600 design points.** Set (a) is a strict subset of set (b) in behaviour as
well as in membership: it declares the fixed point reached one to two-and-a-half sweeps before the
state has actually stopped moving.

**Why, measured rather than argued.** Of the four fields in set (a), **three are `constant` across
the entire harvest** — `build.dr_fw_inboard`, `build.dr_fw_outboard` and `pf_power.vpfskv`, the
three edges V3 and V4 already recorded as *structurally present but dead in this deck*. A18's
categoriser reaches that verdict independently, from 600 entry states, without being told. Only
`times.t_plant_pulse_burn` is a live continuous coupler, and on `st_regression` **even that is
absent from set (b) entirely**: with `i_pulsed_plant = 0` no in-loop model writes it, so the
`Pulse` block's coupling-state subset is empty. That is A2's `k = 0` re-derived by a second
instrument, and it is why `st_regression` is the scenario where set (a) is most misleading — there
the whole of set (a) is three constants, so it "converges" on the first sweep, always.

**Verdict: the DSM is not wrong; the *use* would be.** Nothing here contradicts the collapsed
DSM's edge list. What it refutes is the idea — live in EXPERIMENT_FRAMEWORK.md §2.4 as the
alternative option (a) — that the feedback-edge set could serve as the convergence predicate. A
partitioned solver that iterated to agreement on the DSM's couplers alone would exit with the rest
of the coupling state still moving, on 94–95 % of design points.

**Consequence.** Decision D13's choice of set (b) is vindicated by measurement rather than by
argument, and set (a) keeps exactly the role the framework gives it: a cross-check that produces
findings, never the predicate. Recorded here rather than only in A18's report because this register
accumulates and A18's will be archived.

## V8 — Per-scenario DSM regeneration

**Merged into V6 above** (2026-09-01). A18 (experiment-framework) and the orchestrator wrote this
result up independently from the same `PROCESS_code_analysis` delivery — the M100 regeneration V6
was waiting on — and two accounts of one result is how two accounts start to diverge. V6 carries
it: the partition survives on both inspection scenarios, the pre-committed withdrawal is not
triggered, and the run-time-derived node map needed no change.

A18's independent contribution to that conclusion is kept in **V7**, which is a different finding
and not a duplicate: the DSM's feedback-edge set, had it been used as the convergence predicate,
would have stopped early on 94-95 % of design points.

