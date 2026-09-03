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


## V9 — `Build` is genuinely separable from `Physics`, measured

**A confirmation, not a defect.** The partition plan §1.3 predicted from a static reading that
moving `Build` (DSM row 5, M2) across `Physics` would be *exactly* result-neutral: `build.py` reads
seven `physics` attributes and every one is written by `plasma_geometry.py`, M1's first node, while
the physics package reads only `dr_fw_plasma_gap_inboard`/`_outboard` from `build`, also written by
`plasma_geometry.py`. A3 (build-reorder) made the move and tested the prediction.

| | |
|---|---|
| **Claim tested** | no live edge runs from any node between `Build`'s old position (sequence index 1) and its new one (index 2) back into `Build` |
| **Evidence** | A3, base `c9cc917f`, four scenarios, each run in a fresh subprocess. **0 differing MFILE lines** out of 16 174 / 16 435 / 18 692 / 15 917 and **0 differing MFILE floats**, compared as hex literals with no tolerance, out of 13 559 / 13 455 / 13 493 / 13 487. `ifail = 1` throughout; sweeps unchanged at 2029 / 4286 / 1891 / 29; the 21 executing node calls per sweep unchanged node by node |
| **Verdict** | **DSM correct.** The prediction holds by measurement, not by argument. The comparison was shown to detect a 1-ULP change in a single value before its zeros were accepted |
| **Consequence** | M1 (Physics) is now contiguous in the call order, which is what A5 / F10 needed. **Scope:** a bit-identical result shows no *live* edge on these four decks; it does not show none exists structurally, and it does not transfer to a deck resolving different switches — the same limit V6 places on the module boundaries |

Full numbers and method in [`A3_build_reorder.md`](A3_build_reorder.md) (archived to
`deprecated/` at merge; folder position records lifecycle, not validity — trap T3).

### V9a — corroborated a second time, in a different driver and at the trajectory level

**A23 (flat-arm-permutation) tested the same claim independently and more sharply.** A3 compared
*final output* in PROCESS's own driver. A23 compared the *whole trajectory* in the experiment's
fixed-point engine: arm A0 replayed with `physics` and `build` transposed reproduces A18's recorded
A0 on **600 of 600 design points across the four decks**, with **0** differing — sweep counts,
model-evaluation counts, the converged flag, the moved-constant list, the residual max, argmax
name and above-tau count **at every sweep**, and the exit audit. Extended over every setting A18
recorded A0 under (hoist off and on, and the tolerance ladder at 1e-4 / 1e-6 / 1e-8): **2 400 of
2 400 identical.**

Identical *trajectories*, not merely identical fixed points, is the stronger statement: if either
node read anything the other writes inside the loop, the first sweep after transposition would
already differ. It does not, anywhere.

| | |
|---|---|
| **Why this is worth a separate entry** | The DSM interleaves these two nodes at row level — `build` holds row 5 and rows 29–37, `physics` holds row 4 and rows 6–28 — so `build`'s row sits *inside* `physics`'s span. **That interleaving does not correspond to a call-level data dependence.** Row adjacency in the collapsed DSM is not evidence of coupling between the call sites those rows belong to; this is a **granularity mismatch** of the kind protocol §11 exists to record, and it is the third distinct instance of DSM granularity misleading a reader (see V5, V10b) |
| **Teeth** | The comparison was shown capable of failing before its zeros were accepted: one ULP of one design-vector component moves **488 of 600** points; a reversed-order control arm moves **575 of 600** |
| **Scope, and it is narrow** | This licenses "**one transposition of two adjacent nodes is inert**". It does **not** license "node order does not matter to the flat arm" — the reversed-order control is the counterexample, on the same instrument, on the same points |

Full numbers and method in [`A23_flat_arm_permutation.md`](A23_flat_arm_permutation.md).


## V10 — The feed-forward tail is real, but only two of its five DSM rows can be hoisted

**A confirmation and a correction, from A13 (feedforward-hoist).** The DSM's `FF` module is
right about what feeds nothing back; what is wrong is any cost weighting that treats all of it as
work a driver change can defer.

### V10a — `costs` and `water_use` are genuinely feed-forward, measured

| | |
|---|---|
| **Claim tested** | nothing `costs` or `water_use` writes is read by any model that runs before them inside the idempotence loop |
| **Evidence** | A13, base `4433bc67`, four scenarios, each run in a fresh subprocess. Deferring both nodes out of every sweep and running them once after the fixed point leaves the result **bit-identical**: **0 differing MFILE lines** of 16 174 / 16 435 / 18 692 / 15 917 and **0 differing MFILE floats**, as hex literals with no tolerance, of 13 559 / 13 455 / 13 493 / 13 487 — **121 295 quantities compared in total**. `ifail = 1` throughout; sweeps unchanged at 2 029 / 4 286 / 1 891 / 29. Run-time write sets, from fingerprinting all 2 288 data-structure fields across the two nodes: `water_use` writes 8 fields, `costs` 102 (103 on `st_regression`) |
| **Verdict** | **DSM correct.** If either node fed anything back, the deferred trajectory would diverge and the MFILE would say so |
| **Consequence** | The hoist is available with `k = 0` and no dimension penalty, and it is worth 6.56 / 6.76 / 6.64 / 2.63 % of model evaluations on the four decks |

### V10b — Only 2 of `FF`'s 5 rows are hoistable, so a 5-row weighting overstates the hoist

`FF` is `|FF| = 5` DSM rows: row 38 plus rows 52-55. Of those:

* **`CsFatigue` (row 38) is not a driver call site at all.** It never appears in
  `_call_models_once`; it runs nested inside an M2 node. A driver-level hoist cannot reach it.
* **`objective_constraints` is the convergence test.** The committed node map already flags it
  `in_call_models_once: false`, and it is the objective function plus the constraint residuals —
  the very quantities `Caller.call_models` compares to decide it has converged. It cannot be
  hoisted out of the loop that uses it.
* **`costs` and `water_use` are the whole hoistable set** — 2 rows, and 2 of the 21 model-call
  nodes a deck executes.

**Why it matters, with the number.** A2's Stage-1 gate weighted the hoist by `w_Pulse + w_FF` =
6 of 52 DSM rows and published **4.6-8.2 %**. Restated over the node set a driver hoist can
actually defer, and in model-call units, the same arithmetic gives **6.56 / 6.76 / 6.64 / 5.25 %**,
and the measurement returns **6.56 / 6.76 / 6.64 / 2.63 %** — the last short because the deck's
figure of merit reads a `costs` output (V10c). **This is not a defect in the DSM.** The module
boundary is correct; the error is in reading a row count as a count of deferrable driver work.
Anything that weights architecture options by DSM rows should first ask, per row, whether the
driver can address it.

### V10c — `Pulse` is not feed-forward before the lift, measured both ways

`Pulse` writes exactly two fields on the three pulsed decks — `times.t_plant_pulse_burn` and
`constraints.t_current_ramp_up_min` — and **zero** on `st_regression`, which reproduces V5 exactly
from an independent instrument. Both fields are read by the idempotence loop's own predicate:
`t_plant_pulse_burn` by `objectives.py` (figures of merit 14, 16, 19) and both by
`constraints.py`. So `Pulse` cannot be deferred while the burn-time coupler is in the loop, which
is framework item C2a stated as a measurement rather than an expectation.

### V10d — the loop's predicate reads the tail on one of the four decks

`objectives.py` reads `costs.coe` (figure of merit 6) and `costs.cdirt` / `costs.concost` (7); all
three are in the `costs` model's measured write set. `constraints.py` reads **nothing** any
hoisted node writes, on any of the four decks (denominators: 2 288 fields fingerprinted, 17
distinct data reads in `objectives.py`, 212 in `constraints.py`). Evaluating all 16 figures of
merit before and after each tail node confirms the same set by measurement: only 6 and 7 move, and
only across `costs`.

`large_tokamak_eval` sets no `minmax` and therefore takes the **default** figure of merit, **7**.
On that deck the driver must keep `costs` inside the loop. **Consequence for Phase B:**
`arch_surgery/fixedpoint/arms.py:hoisted_nodes()` has no such guard and would hoist `costs` there
anyway, so on that deck the engine and the incumbent driver would be hoisting different sets under
the same nominal toggle. Recorded here rather than fixed, because changing a merged instrument was
out of A13's scope.

Full numbers and method in [`A13_feedforward_hoist.md`](A13_feedforward_hoist.md).

## V11 — The three-module partition of the *coupling state* is exact on all four decks

Measured by A25 (phase-b-variant), which needed per-module write sets to restrict each inner
solve's convergence test and could not assume them. The `PROCESS_IDF_PROBE=modules` write census
(`__setattr__` interception unioned with snapshot differencing at node boundaries, confined to
`Caller._call_models_once` — traps T1 and T7) was mapped to modules through the committed DSM node
map and intersected with each deck's committed `ystate` component set.

| deck | M1 | M2 | M3 | `PULSE` | `FF` | covered / components | in **two** modules | written by **none** |
|---|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 258 | 240 | 221 | 2 | 119 | 840 / 840 | **0** | **0** |
| `low_aspect_ratio_DEMO` | 259 | 244 | 221 | 2 | 120 | 846 / 846 | **0** | **0** |
| `st_regression` | 268 | 216 | 223 | **0** | 120 | 827 / 827 | **0** | **0** |
| `large_tokamak_eval` | 258 | 240 | 221 | 2 | 119 | 840 / 840 | **0** | **0** |

**Every coupling component is written by exactly one module on every deck.** Decision D8's
decomposition is a *partition* of the written state at run time, not merely a grouping — which is
the property a block Gauss-Seidel schedule needs and which nothing had previously checked. The
`PULSE` column reproduces V5 and V10c from a third instrument: two writes on the pulsed decks,
zero on `st_regression`.

**Consequence, and it is not a validation footnote.** A25 first tried to take each inner solve's
convergence test over the whole coupling vector, reasoning that a component no running node writes
cannot move, so the subsets could not matter. That reasoning is wrong for a reason unrelated to the
DSM: `ystate`'s predicate scores a component `inf` whenever *either* snapshot is not
float-viewable, which in a fresh process is every field no model has yet written. The M1 inner
solve was therefore held open by `ccfe_hcpb.pnuc_tot_blk_sector` — an M3 field M1 cannot touch —
until it hit its cap. **Equality of values is not equality of scores**, and the partition above is
load-bearing rather than descriptive.

## V12 — `objective_constraints` is correctly flagged `in_call_models_once: false`, and that flag is load-bearing

The node map assigns `objective_constraints` to module `FF`. It is the objective and
constraint-vector evaluation, not a call site inside `Caller._call_models_once`, and the map says
so with `in_call_models_once: false`. A25's first block schedule read the module label and ignored
the flag, which gave the `FF` block a non-empty node set that executed nothing — **789 block
sweeps of pure no-ops** on `large_tokamak_nof`, charged against the schedule and invisible in the
model-evaluation count because no model ran.

**The map is right; the consumer was wrong.** Recorded because the flag looks like metadata and is
not: any consumer that derives an execution schedule from `module` alone will build one containing
a node that cannot execute.

## V13 — After the burn-time lift `Pulse` *is* feed-forward, but the hoist cannot see it

Framework note C2a and A13's report both predict that `pulse` joins the feed-forward tail
automatically once the burn-time coupler is lifted, because the hoisted node set is derived at run
time rather than hard-coded. **Measured under the lift: it does not.**

The substance of the prediction is correct. Under `PROCESS_ARCH_LIFT=burn_time`, `Pulse`'s two
writes are `times.t_plant_pulse_burn` — which the optimiser now owns and `subsolve` returns
untouched — and `constraints.t_current_ramp_up_min`, whose only reader anywhere in `process/` is
constraint equation 41 (`constraints.py:1102`), a constraint rather than a model. So `Pulse` feeds
nothing back into the model sequence.

The mechanism fails because the derivation asks the **committed DSM node map** for each node's
module and hoists those in `HOIST_MODULES = {"FF"}`. `pulse`'s module there is `"PULSE"`,
statically. Lifting a coupler does not relabel a committed artifact. **"Derived at run time" was
true of the node *set* and false of the node *classification*.**

Cost of the gap, with denominators, from A25's gate runs: `pulse` ran 1 314 times over 660
`call_models` on `large_tokamak_nof` where a hoisted `pulse` would run 660 — 654 avoidable node
calls, **1.5 %** of that arm's 43 426. On `low_aspect_ratio_DEMO`: 2 089 against 1 050, **1.5 %**
of 69 986. Not taken by A25, because changing which nodes the hoist selects mid-task would change
the architecture being measured, and because the fix is a decision about the node map rather than a
patch in `caller.py`.

## V14 — `st_regression` shows recurring above-τ cross-pass movement with **no known live back edge to carry it**

Under D15's perturbed multi-starts (A28 campaign), the block arm on `st_regression` needs a 3rd–7th
outer pass on **2 802 of 54 480** MDA calls (5.14 %) — recurring through entire optimisations, on
25 of 25 starts — where the collapsed DSM for this scenario carries **no live cross-module back
edge** (A2, confirmed dynamically by A22 at the harvested states: zero cross-module movement of any
kind). The pulsed decks show exactly **one** such call per run (the cold first call; 22/14 080 and
20/20 370), which staleness explains. The slow mode is the TF-coil chain:
`superconducting_tfcoil.a_tf_plasma_case` (computed in `tfcoil/superconducting.py` ~line 1878 at
`c0ae5b28`; `st_regression` has `i_tf_sup = 1` — superconducting TF despite `itart = 1`; the
orchestrator's first "resistive model" attribution is corrected in the addendum) is the argmax exit residual on 22/28 ladder audit records **in both arms**,
decaying ~30× per rung of τ. The movement is transient — bit-exact 0 at every accepted optimum —
and dormant at the harvest, so A2/A22 measured correctly *there*; D15's perturbation visits states
the harvest never did (the failure mode A22's own caveat predicted).

A source scan eliminated the obvious carriers, in exactly the V1/V2 pattern:
`physics ← pf_coil.p_pf_electric_supplies_mw` is inside `outplas()` (output path,
`physics.py:2601` at `c0ae5b28`); `build.dr_fw_plasma_gap_*` is written by `plasma_geometry`
itself (M1-internal); `physics.b_plasma_*_toroidal` is physics-internal (with a one-sweep stale
read at `physics.py:387/395` — `b_plasma_inboard_total` computed from the *previous* iteration's
`b_plasma_inboard_toroidal` — resolved by iteration, worth an upstream note).

**Verdict: open.** Either (i) a computational cross-block read the scan missed — referred to
`PROCESS_code_analysis` (outgoing report, 2026-09-03), whose pinned instrument can enumerate
readsets authoritatively; or (ii) a **non-idempotent model** in the coils block (an internal solve
whose output depends on its own execution history), which is a class **no DSM edge can represent**
and would need its own register category. Consequence either way: "the collapsed DSM has no back
edge" does not imply "one outer pass suffices" at states far from self-consistency, and V2's
trust-mode design must treat edge-liveness as state-dependent (see
[`../plans/MDA_PARTITION_V2_REVISION_LIST.md`](../plans/MDA_PARTITION_V2_REVISION_LIST.md) R1a).

**V14 addendum (2026-09-03, from the `PROCESS_code_analysis` orchestrator, after the query was
withdrawn — volunteered, not owed).** Two pointers that reshape the diagnostic:
1. **Their graph exports are deck-specific and `st_regression` is not one of the standing
   configurations** (theirs are the large-tokamak and stellarator decks; `st_regression` is an
   MFILE-level inspection scenario, their D77). Our own **V6** already records the same thing from
   our side: the DSM's source config matches `large_tokamak_*` and differs from `st_regression` on
   `i_single_null`, `i_plasma_current`, `i_beta_component`. **Correction while acting on this:** `st_regression` has `i_tf_sup = 1` — the superconducting
   TF chain, the *same* family as the DSM's config — so the TF-writer path is **not** a
   configuration difference (the orchestrator's "resistive model" reading is withdrawn). The
   deck still differs on ten-plus switches (V6: `i_plasma_current = 9`, `i_beta_component = 3`,
   `i_single_null = 0`, `itart = 1`, `i_pulsed_plant = 0`, …), so branch-liveness differences
   remain possible elsewhere in the chain — "the collapsed DSM has no back edge here" partly
   means "the DSM never executed this code path". Any future named read must state **which deck's
   switches it needs**; they will check it against the pinned deck-independent *source* as well as
   the export.
2. **Mechanism (ii) — execution-history-dependent output at fixed inputs — is not hypothetical:
   they hold measured members** in upstream PROCESS at their pin: a cross-sweep stale read (the
   2015 cost model's turns count, read 8 lines before its only writer runs — consumed one optimiser
   evaluation late); first-evaluation reads of fields defaulting to 0.0 that a later step writes
   (first-wall coolant void); and an output-path mesh switch (100→500, never restored). Citations
   in their M84 direct-cycle audit and M36 output-pass reports. Their DSM **deliberately does not
   encode same-pass vs next-pass timing** (their I-44), so the caveat V14 states — no back edge
   does not imply one pass suffices — is one they already hold as true for that timing class, and
   `physics.py:387/:395` reads as a textbook member of it.

**V14 follow-up (2026-09-03).** On the user's instruction (*"Ensure that process_code_analysis
parses the same scenario config as you run"*), the alignment request went to their orchestrator:
per-deck graph exports (or a switch-conditioned liveness diff) built from our three frozen
`IN.DAT`s, `st_regression` first. Our register V6 table was sent as the delta list, with the
`i_tf_sup = 1` correction. Outcome to be recorded here when they answer.

**V14 follow-up 2 (2026-09-03) — the per-deck exports arrived and reshape the question.**
Provenance: built by the sibling study at their instrument commit `bd74dacb` from deck files
byte-identical to ours (sha256 matched both sides); frozen copies under
`arch_surgery/idf_probe/runs/dsm_exports/` (untracked; sha256 of the graphs:
`582b4a5f…` st, `0c3f23b7…` lad). Three results from querying the `st_regression` graph:
1. **The user's candidate — V3's `FirstWall → Build` edge — is refuted as the carrier**, now at
   perturbed states too: `dr_fw_inboard = 2·radius_fw_channel + 2·dr_fw_wall`, and the export
   confirms both inputs are written **only by `COOR_SingleRun`** (the input loader). The field is
   frozen after the first evaluation; its appearance in A28's moved census is a first-call
   initialization artifact, once per run. V3 stands.
2. **CORRECTED (same day): the "three named pathways" reading was a star artifact.** The
   `MDA_Idempotence` pseudo-node (absorbing `Caller`/`check_agreement`) is a **hub**: models
   writing loop-tested state connect in, models reading loop-carried state connect out, and the
   **pairing is lost** — a writer edge and a reader edge on the hub do not make a pathway. The
   earlier claim that `Build::plasma_outboard_edge_toroidal_ripple`, `CROCO::stresscl` and
   `PFCoil::efc` feed next-pass plasma reads is **withdrawn**. The correct structural statement,
   from a full pairwise census over the graph's variable-level edges (every variable's writers'
   blocks against its readers' blocks, pseudo-nodes excluded): **the `st_regression` static graph
   contains exactly ONE cross-block loop-carried pathway — `FirstWall (M3) → build.dr_fw_inboard/
   outboard → Build (M2)` — and it is provably frozen** (finding 1). So statically there is **no
   live cross-block feedback on this deck at all**, and the recurring drift must come from
   mechanism (ii) or from an edge invisible to static analysis. A31 (drift-diagnostic) decides.
3. **The instrument declares the mechanism-(ii) blind spot as a measured population**: its
   `coupling_bound` note states **498 variables** are written and read by one and the same model
   and by no other pair, and "whether such a read takes this sweep's value or the last one depends
   on statement order inside the body, which is not measured" — excluded from the coupling set
   rather than assumed into it. Our `physics.py:387/395` stale read is a member of exactly this
   population. Non-idempotent models live here.
The instrumented `start010` run now has named targets: per-call pass ≥ 2 argmax against
{ripple, stresscl chain, efc} and the 498-population. Still queued behind A29's heavy slot.

**V14 follow-up 3 (2026-09-03).** The root-cause investigation requested of the sibling study is
**cancelled** (user: a handoff requires a demonstrated mistake in the dependency analysis, and
there is none — the `FirstWall → build.dr_fw_*` edge is correctly present and correctly dead, the
census found no missing edge, and the hub representation and the 498-variable timing exclusion are
their documented decisions, not defects). Standing rule for this register from here: **a V-entry
against the dependency analysis, or any cross-study handoff, carries a demonstrated defect with
variable, `file:line` at the study commit, and run evidence — never a question, a suspicion, or a
request to revisit a recorded decision.** A31's verdict decides whether anything further goes
their way (only if it names a component the graph asserts and gets wrong); the non-idempotence
outcome routes to upstream-PROCESS defect reporting instead.

**V14 follow-up 3, closure (2026-09-03).** The cancellation landed in time but not free of cost:
the sibling had already dispatched an investigation agent under their relay precedent — stopped
two minutes in, nothing produced, zero commits, worktree removed — and their task number **M116 is
consumed** by the mint-and-cancel, logged in their queue with our reasoning quoted. That consumed
number is the concrete price of a premature handoff, and is why the demonstrated-defect rule above
exists. One kernel survives on their side as a parked candidate for their user: the
statement-order classifier splitting self-coupled reads into same-sweep / last-sweep (our
question (b)), which they note is the engine their I-44 diagnostic would need anyway. Their
standing position mirrors ours: variable, `file:line` at the study commit, run evidence — or
nothing. The per-deck export lane (their D77 inspection scenarios) remains available on request.
