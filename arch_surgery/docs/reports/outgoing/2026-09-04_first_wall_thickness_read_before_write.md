# The first-wall thicknesses are read before they are written — the full write-up of your owed M117 defect, with measured displaced-state magnitudes and a fix shape

> **Document status** — **DRAFT · STAGED FOR HANDOFF, not yet handed over.** Drafted
> 2026-09-04 by task A39 (v3-plan) of `PROCESS_surgery` as deliverable D-a of its V3
> development plan §6. **The handoff itself is the orchestrator's call**, per this
> repository's demonstrated-defect rule; until the orchestrator hands it over, this
> document binds nobody. Destination: `PROCESS_code_analysis/docs/bug_reports/`, as the
> individual write-up your `README.md` **Owed (M117, 2026-09-03)** row reserves.
> Filed here rather than written into the sibling clone because `PROCESS_surgery`'s
> `CLAUDE.md` forbids writing into a sibling clone.

**Found:** `PROCESS_surgery` — a fork of PROCESS in which the *arrangement of solvers* is
changed while every physics and engineering model is left exactly as upstream wrote it.
**Study commit:** PROCESS **`c0ae5b28`**, the `PROCESS_surgery` base commit. **Every line
number below is a line number at `c0ae5b28`, verified with `git show` for this document**
(the discipline our A31 §7 adopted after a stale-line-number incident) — **not** your pin
`PROCESS_at_36ac820e`; map before citing.
**Status:** **REPORTED, NOT PATCHED.** Nothing has been changed in any tree.
`PROCESS_surgery` freezes the models (its D5/D11), so this is a finding, not a fix; the
fix shape in §4 is what we would recommend upstream adopt, not what we did.

## 0. What this completes

Your M117 report (`docs/reports/deprecated/M117_firstwall_build_feedback.md`) verdicted
the `FirstWall → Build` DSM mark a **correct cell, inert at run time** for the shipped
tokamak deck, and filed one Owed defect: *"FirstWall reads its own wall thicknesses before
writing them."* Both halves stand. This note is the individual write-up that row reserves,
and it adds what our side has since measured: the defect is not only `FirstWall`'s
self-read — it is a **schedule-level read-before-write** whose consequence, invisible
under the shipped always-iterates driver, becomes an exactly-quantified error injector
under any one-pass schedule. Your inertness verdict was value-liveness; the missing
qualifier is displacement-liveness ("value-frozen ≠ displacement-inert", our register
entry V15).

## 1. The defect, with every site

**The writer.** `FirstWall.set_fw_geometry` (`process/models/fw.py:347-352`) writes:

```python
self.data.build.dr_fw_inboard = (
    2 * self.data.fwbs.radius_fw_channel + 2 * self.data.fwbs.dr_fw_wall
)
self.data.build.dr_fw_outboard = self.data.build.dr_fw_inboard
```

Both inputs are **pure deck inputs no model computes** (your M117 established this on the
tokamak deck; our per-deck run-time censuses confirm it on all three of our decks): the
value is a run-constant, written mid-sweep by the 38th of ~50 swept models.

**Readers that run earlier in the same sweep** (`Build.run` is 2nd):

- `process/models/build.py:836` — `z_tf_top` carries
  `0.5·(dr_fw_inboard + dr_fw_outboard)`; the downstream mover
  `build.dz_tf_upper_lower_midplane` is written from it at `:840`.
- `process/models/build.py:1940-1947` — `dr_shld_vv_gap_outboard` (the TF-ripple branch),
  via `r_shld_outboard_outer` (`:1887`), which carries `dr_fw_outboard`; further pair
  reads in the radial build at `:1867` (`rbld`) and `:1877` (`r_shld_inboard_inner`).

So in sweep *k*, `Build` consumes the value `FirstWall` wrote in sweep *k − 1* — your
M117's mechanism — and in **sweep 1 of the first evaluation** it consumes the
data-structure default `0.0`.

**The self-read your Owed row names.** `FirstWall.run` itself reads the pair at
`fw.py:54-55` (into `calculate_first_wall_half_height`) **before** its own
`set_fw_geometry()` call at `:110` — the first sweep's half-height is computed from
zero thickness even inside the writing model.

## 2. Measured consequence (our A35, merged 2026-09-04; single-evaluation experiments, fresh subprocess each)

Under the shipped driver the lag is absorbed by a sweep that happens anyway — your M117
verdict, which our measurements confirm. Under a **one-pass block schedule** (our trust
arm: verify nothing, run the feed-forward chain once) the lag is the entire cross-block
error:

- **The transient is a transport delay of depth one through this one edge**, not a slow
  contracting mode. From a cold deck entry on `large_tokamak_nof`, the one-pass exit
  differs from the flat fixed point by **1.459e-2** max scaled residual (243/840
  components above τ = 1e-6); **one** verified outer pass repairs it to **8.3e-16**
  (the third pass is a receipt, not repair). On `st_regression`: 1.79e-2, 124/827,
  repaired to 1.6e-11.
- **The error is exactly the entry displacement of the pair, linearly imaged.** Measured
  coefficients close to source arithmetic: `dz_tf_upper_lower_midplane` moves by
  0.5·(Δin + Δout) (relative difference to prediction 3.8e-14 cold), `dr_shld_vv_gap_outboard`
  by −Δout.
- **δ-linearity:** halving the entry perturbation halves every mover — per-mover ratio
  between δ = 0.10 and δ = 0.05 runs, **median ≈ 2.00** (1.999 over 153 movers on
  `large_tokamak_nof`, 2.000 over 59 on `st_regression`) — and identically 0 at
  fixed-point entries. The carrier is the state, not any hidden execution-history channel
  (chained fresh-process restarts reproduce the in-process repair bit-for-bit).

Our A38 (merged 2026-09-04) then measured the per-deck images across 25 δ-perturbed
entries per deck: on `large_tokamak_nof` and `st_regression` **25/25** of the
solve-writeset audit maxima are linear images of the pair (on `st_regression`, 17 the
A35 image and 8 a second image, `blanket.vol_shld_inboard`, at measured gain **47.0** on
Δin, constant across seeds to 2.3e-11 relative); on `low_aspect_ratio_DEMO` the pair's
images hold at the same coefficients, with one further term not closed by the pair
(under investigation on our side).

## 3. Why this is a defect and not a driver quirk

The write site makes a run-constant of two loader-written inputs *look like* a per-sweep
coupling: it forces `k = 1` lag semantics onto every schedule, costs the shipped driver
one warm-up sweep's worth of consistency on the first evaluation (your M117's transient),
computes a zero-thickness first-wall half-height in the first sweep (`fw.py:54-55`), and
under any one-pass or reduced-iteration driver becomes a δ-proportional error injector
with the measured magnitudes of §2. The same pattern, smaller: `Power.run` writes the
**literal** `20.0e0` into `pf_power.vpfskv` every sweep (`process/models/power.py:571`);
its sole computational reader is the Central Solenoid power-source emf term of the
ramp-time calculation, `process/models/pulse.py:224` (`v = self.data.pf_power.vpfskv * 1.0e3`;
line 326 in our current working tree after our A24 residual extraction `0a2e64f3` — which
is why we cite base-commit lines), feeding constraint 41 — inactive on all three of our
decks.

## 4. Fix shape (recommended, not applied)

Both fields are functions of loader-written constants, so the write belongs at
**initialisation time**, not in the sweep:

- Compute `build.dr_fw_inboard` / `dr_fw_outboard` in `check_process`
  (`process/core/init.py:251`), beside the existing double-null geometry derivation
  there (`init.py:607-617`, where `n_divertors` and `dz_fw_plasma_gap` are derived from
  `i_single_null` — the established home for deriving dependent geometry before any model
  runs); **delete the model's write** (`fw.py:347-352`). The self-read at `fw.py:54-55`
  then always sees the true value, and the DSM cell dissolves rather than being merely
  inert.
- Same treatment for `pf_power.vpfskv`: assign the constant at initialisation (or promote
  it to a deck input); delete the per-sweep write at `power.py:571`.

**Validity condition, stated:** this is equivalence, not approximation, *precisely
because* the inputs are pure deck inputs. If a future model ever computes
`fwbs.radius_fw_channel` or `fwbs.dr_fw_wall`, the write must return to the model and the
edge goes genuinely live (the standing clause on our register entry V3). In our own study
the models are frozen, so V3 of our experiment instead handles the lag at driver level
(re-executing the existing `set_fw_geometry` method at the sweep head — a driver choice,
no model edit); that is a workaround shaped by our freeze, and §4's initialisation-time
fix is the shape we would recommend to upstream.

## 5. Where the evidence lives (our repository)

- `arch_surgery/docs/reports/deprecated/A35_cold_census.md` — the carrier trace: sites,
  coefficients, δ-scaling, restart-identity exclusion of hidden state; orchestrator
  recheck in its §9.
- `arch_surgery/docs/reports/deprecated/A38_audit_rerun.md` — the 25-seed per-deck image
  census and the gain-47.0 second image; independent recheck in its §9.
- `arch_surgery/docs/reports/DSM_VALIDATION.md` — register entries V3 (value-dead edge),
  V15 (displacement-liveness; "value-frozen ≠ displacement-inert").
