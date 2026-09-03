# A31 (drift-diagnostic) — the recurring 3rd–7th outer passes on `st_regression`, named to the bit

> **Document status** — **CURRENT · TASK REPORT, open.** Written by task A31 (drift-diagnostic),
> 2026-09-03, on branch `A31-drift-diagnostic`, branched from `architecture_surgery` at
> `377de650`. Archived to `deprecated/` when the task merges and authoritative there (trap T3).
> Nothing here is merged; nothing is pushed; no model file was touched.

| | |
|---|---|
| **Task** | A31 (drift-diagnostic) — name the component(s) and mechanism behind the recurring above-tolerance cross-pass movement on `st_regression` (DSM register V14; revision-list item R1a): 2 802 of 54 480 block-arm optimiser evaluations (5.14 %) needed a 3rd–7th outer pass on an already-converged block schedule |
| **Method** | a per-pass trace of the driver's **joint test** — the residual evaluation that decides whether an outer pass sufficed — behind a new environment variable `PROCESS_ARCH_PASS_TRACE`, recording per optimiser evaluation, per pass, every component that failed the test with its before/after values as exact hex floats. Driver files only: `process/core/caller.py`, `process/core/solver/module_solve.py`. `process/models/` untouched |
| **Script** | [`arch_surgery/idf_probe/a31_drift_probe.py`](../../idf_probe/a31_drift_probe.py) — every number below comes from its stages (`neutrality`, `trace`, `retrace`, `a0p`, `analyze --with-a0p`), instrument committed at `a1a4a9ce` (protocol §15). Source line numbers are verified against the frozen base commit with `git show c0ae5b28:…`, never the working tree (A27's lesson) |
| **Runs** | 6 fresh-subprocess PROCESS solves in this worktree, serial (beside A29's heavy slot, per the brief): 2 neutrality-gate runs, 1 instrument-validation run, traced block-arm runs at start010 and start005, one traced block-arm re-run at start010 under the committed instrument, one traced flat-control run at start010 |
| **Date** | 2026-09-03 |

---

## 1. Verdict

**Neither hypothesis. The component is `pf_power.srcktpm`; the model that writes it is `power`
(the plant power model, routine `pfpwr`); and the mechanism is a misclassified
constant under an exact-equality assertion, flickering by one to two units in the last place
(ULPs) of its floating-point representation.**

The question as posed — *which coupling-state component moves by more than τ = 1e-6 on outer
pass 2* — has a measured answer nobody expected: **none does.** On the two heaviest starts,
covering 1 479 of the campaign's 2 802 recurring calls (52.8 %), every recurring failure of the
joint test is a **moved constant**, not a continuous component above tolerance:

- `pf_power.srcktpm` — "total PF coil resistive power (kW)" — is category **`constant`** in the
  committed coupling-state artifact (`ystate_st_regression.json`, SPEC_MODE_A18): it held the
  bit-identical value 1 106.688 kW (`0x1.14ac083126e97p+10`) at every one of the 144 harvested
  design points. The predicate therefore excludes it from the τ-tolerance test but **asserts it
  stays constant, with no tolerance at all** — a deliberate design (the inverse of PROCESS's
  `equal_nan` defect), and it worked exactly as built.
- At the hostile states D15's perturbed multi-starts visit, `srcktpm` is not constant: it is
  recomputed from scratch every sweep from PF-coil quantities that are still contracting
  sub-τ, and its value lands on **adjacent representable doubles** — every recorded move is
  exactly 1 or 2 ULPs (2.274e-13 or 4.547e-13 kW; relative 2.06e-16 / 4.11e-16; the value only
  ever takes `…e96`/`…e97`/`…e98`). At start005 call 91 it moved `e97→e96` on pass 2 and
  **back `e96→e97` on pass 3** — a one-bit oscillation, each flip buying one more outer pass.
- Meanwhile the **largest τ-tested residual on any recurring failing record is 7.5e-08** — a
  factor 13 below τ — with `superconducting_tfcoil.a_tf_plasma_case` as its argmax on 89 % of
  failing records. That is why A28's ladder audits kept naming `a_tf_plasma_case`: it is the
  slowest *continuous* mode, and it never once tripped the tolerance.

The loop stops when the coil-side contraction reaches its floating-point fixed point and
`srcktpm` reproduces bit-exactly — after 1 to 5 extra passes (the observed 3rd–7th-pass tail).
The extra passes purchase nothing: `srcktpm`'s only model reader is the cost model
(`costs.py:2167` at `c0ae5b28`), which the block arm hoists out of the loop into the
feed-forward tail; the objective branch that reads it (`objectives.py:61`) is not the active
figure of merit on this deck (`i_figure_merit = -5`, fusion gain Q).

Denominators, per traced start (block arm `A1'`, τ = 1e-6, perturbation δ = 0.10, exactly
A28's machinery):

| start | outer-test evaluations | at pass ≥ 2 | failing at pass ≥ 2 | of which `srcktpm` **alone** | with any τ-exceedance | pass histogram vs A28 |
|---|---|---|---|---|---|---|
| start010 | 23 778 | 12 408 | 1 294 (over 858 calls) | **1 293** | 1 (the cold first call) | identical, 858 calls at 3+ |
| start005 | 21 729 | 11 199 | 961 (over 621 calls) | **960** | 1 (the cold first call) | identical, 621 calls at 3+ |

The one exception per run is **call 1, pass 2** — the cold first evaluation (66 continuous
components above τ, max scaled 1.79e-02, plus 14 moved constants): first-evaluation
initialization staleness, the same once-per-run artifact already recorded on the pulsed decks
(22/14 080 and 20/20 370), and not part of the recurring class.

**Campaign fingerprint**: `pf_power.srcktpm` appears in the run-level moved-constant union of
**25 of 25** recorded A28 `A1'` starts on this deck (stage `analyze`, reading the main
checkout's records; the per-pass attribution above is measured on 2 of 25 starts, which hold
52.8 % of the campaign's recurring calls).

## 2. Why both hypotheses fail

**(A) A live cross-block feedback edge invisible to static analysis — refuted.** The full
census over the frozen per-deck static export (sha256 `582b4a5f…`, built by the sibling study
at their commit `bd74dacb` from a byte-identical deck) finds, under the `A1'` block schedule,
**exactly one** cross-block loop-carried variable pathway at model level: `fw` (block M3)
writes `build.dr_fw_inboard` / `build.dr_fw_outboard`, read by `build` (block M2). That is the
pair V14 follow-up 2 already proved frozen — verified again at the pin: `fw.py:348–352`
computes `dr_fw_inboard = 2·radius_fw_channel + 2·dr_fw_wall`, both inputs written only by the
input-file loader per the export, and `dr_fw_outboard = dr_fw_inboard`. No other
model-run-path variable is written by a later block and read by an earlier one. Dynamically:
**zero** cross-block components above τ on any recurring record (§1's table); the largest
τ-tested residual anywhere at pass ≥ 2 outside the cold call is 2.15e-07 (start010, over all
12 408 pass ≥ 2 evaluations, failing or not). No invisible edge is needed, and none shows.

**(B) A non-idempotent model — refuted for the recurring class.** The two implicated
quantities are both pure same-sweep functions at `c0ae5b28`:

- `pf_power.srcktpm` is **reset to zero and re-accumulated on every sweep**
  (`power.py:352` reset, `power.py:411` accumulation over the PF circuit groups, inside
  `pfpwr`) from `pf_coil.*` quantities (written by `pfcoil`, block M2) and `physics.rmajor`
  (bus length, block M1). No state survives between executions.
- `superconducting_tfcoil.a_tf_plasma_case` — the measured slow mode — is written at
  `superconducting.py:201` inside `run_base_superconducting_tf` from pure case geometry
  (`:1878`/`:1883`), and its only run-path read (`:4129`, the `stresscl` call in
  `CROCOSuperconductingTFCoil.run`) happens **after** `run_base_superconducting_tf` runs at
  `:3789` — the self-read is same-sweep fresh, not stale. (The read at `:2176` is under
  `output()`; the export correctly attributes it to the output pass.)

The static graph's history-carrying structures — the three model self-loop-back edges
(`CROCOSuperconductingTFCoil`, `pfcoil` functions, `Vacuum`) and the embedded sub-solvers
(TF temperature margin: a secant root find started from `temp_tf_coolant_peak_field`, an
input, not warm-started from its own previous root; `superconducting.py:1266`) — are not
needed to explain a single recurring record, because nothing above τ recurs at all. The 498
written-and-read-by-one-model variables remain unmeasured as a class (their same-sweep
vs last-sweep timing is still the instrument's declared blind spot); this task shows the
recurring `st_regression` tail is not evidence for any of them.

The `physics.py:387/:395` one-sweep stale read of `b_plasma_inboard_toroidal` (verified at the
pin) remains real, remains intra-model, and appears in the trace exactly once — in the cold
first call — as V14 predicted.

## 3. The mechanism, one level deeper

Between two consecutive outer passes, the coil chain (M1 physics → M2 build/TF/PF) contracts
by roughly a factor 30: the continuous argmax `a_tf_plasma_case` reads 5e-09…2.8e-08 scaled on
pass-2 failing records and roughly 30× less per further pass. `srcktpm`'s inputs therefore
move at relative magnitudes around 1e-08 and below. `srcktpm` itself is *functionally* almost
constant on this deck — at three different accepted optima (A31 neutrality run, A31
instrument-validation run, A28 start010) its MFILE value agrees to 13 significant digits and
differs only in the final bits — so the sub-τ input drift perturbs only the rounding of its
accumulation chain, and the recomputed sum lands one representable double away. Exact
equality has no tolerance: one ULP is a fail. The pass histogram's decay (858 → 342 → 66 → 24
→ 4 at start010) is the coil contraction marching the sum to its bit-exact fixed point.

The flat predicate-matched control `A0'` (same predicate, one block, its inner sweep-to-sweep
test being the joint test — traced at start010) confirms the mechanism is a property of the
predicate, not of the block architecture:

- 39 232 joint-test evaluations over 11 730 optimiser evaluations, reproducing A28's `A0'`
  start010 record exactly (sweep count, histogram, `norm_objf` hex).
- 16 074 sweep ≥ 2 evaluations fail, but almost all during the flat arm's normal multi-sweep
  relaxation (continuous components legitimately above τ mid-relaxation).
- **1 547 failing evaluations (over 1 012 calls) have no τ-exceedance at all**: 1 371 are the
  pair {`pf_power.srcktpm`, `costs.c22524`} — both at ULP level (max relative 4.11e-16 and
  3.11e-16) — and 176 are `physics.beta_norm_max_stambaugh` (max relative 6.5e-07), a second,
  smaller member of the same off-harvest-constant class. `costs.c22524` (a 1990 cost account
  computed *from* `srcktpm`, `costs.py:2167`) co-moves in this arm because `A0'` has no hoist:
  `costs` runs inside the loop, so the flicker propagates into it the same sweep. In `A1'`,
  `costs` is hoisted and only `srcktpm` itself shows.

So both arms pay for the same bit flicker — 1 293 extra outer passes at `A1'` start010,
1 547 extra full sweeps at `A0'` start010 — and neither arm's recurring tail is coupling.

## 4. The switch-neutrality gate (protocol §12), with its teeth

`PROCESS_ARCH_PASS_TRACE` unset must be byte-identical to the pre-A31 driver. Gated, not
asserted — stage `neutrality`, run on the clean committed tree at `a1a4a9ce`:

one untraced `st_regression` `A1'` run at start000, compared field-by-field against the main
checkout's recorded A28 metrics (`runs/a28/h5/st_regression/A1p/start000/metrics.json`,
sha256 `11f1b943…`), **3 of 3 fields exactly equal**:

| field | reference (A28) | this run |
|---|---|---|
| `node_calls_solve_phase` | 37 312 | 37 312 |
| `outer_pass_hist` | {1: 9, 2: 560, 3: 1} | identical |
| `norm_objf` (hex) | `-0x1.096acf3342e04p+4` | identical |

**Teeth: 3 of 3 perturbations trip.** A deliberate minimal perturbation of the comparator's
own input — +1 on the node-call count, +1 on one histogram bucket, one ULP on the objective —
each flips the gate to FAIL (stage `neutrality`, `gate_teeth`; recorded in
`runs/a31/neutrality/gate.json`).

Beyond the gate, every traced run **is itself a bit-level neutrality demonstration**: with the
trace *on*, all four runs reproduce their A28 counterparts exactly — outer-pass histograms
(858 and 621 calls at 3+ passes, per bucket), `node_calls_solve_phase` (744 021 / 692 304 /
823 872), block sweeps (151 645 / 140 237 / 39 232), calls-with-moved-constant counts (3 320 /
2 232), failure counts (0), and `norm_objf` as exact hex. The count reconciliation the brief
required is therefore exact, with nothing to explain.

## 5. What this resolves, and what it costs

- **V14's open verdict closes.** "Recurring above-τ cross-pass movement with no known live
  back edge to carry it" resolves to: *there was no above-τ movement to carry*. The joint
  test was failing on the no-tolerance leg of the predicate, on a component whose constancy
  is an artifact of the 144-point harvest, at amplitudes of one ULP.
- **R1a's mechanism question closes on branch (1), in a sharper form than either candidate**:
  not a slow mode creeping past the step-size test (the slow mode stays 13× under τ), but a
  categorisation of the A18-mode coupling-state spec meeting states the harvest never visited.
  Benign for correctness — the assertion is conservative and delivers slightly *more*
  converged states — and priced above in passes and sweeps for both arms.
- **The already-committed SPEC_MODE_A26 artifact dissolves the recurring tail by
  construction** (derived, not run): `ystate_a26_st_regression.json` classifies
  `pf_power.srcktpm` as `continuous` with measured scale 1 106.688, so its worst recorded
  move scores 4.547e-13 / 1 106.688 = 4.11e-16 — ten orders below τ. A V2 experiment testing
  under the a26-mode spec should see `st_regression`'s recurring 3+-pass tail collapse to the
  cold first call, matching the pulsed decks. (Inference from committed artifact plus measured
  deltas; one campaign run under the a26 spec would confirm it and was not in this task's
  budget.)
- **A28's published numbers are untouched**: the tails were real work actually done; this task
  explains them without re-measuring any Phase B figure.
- **Nothing here asks for a model edit.** `power.pfpwr` is bit-stable at fixed inputs; the
  finding is about the measurement spec, not the physics code. The upstream-noteworthy items
  remain the ones already on record (`physics.py:387/:395`).

## 6. Autonomous decisions, with reversal paths

1. **Instrument-validation run** (56 s, `A1'` start000 traced, `runs/a31/smoke/`) before the
   heavy runs. No published number rests on it. Reversal: delete the directory.
2. **Trace format upgraded mid-task.** The first traced run showed the mover class is the
   equality-tested components, which the first format recorded by name only; the committed
   format (`a1a4a9ce`) adds before/after hex for every moved constant and discrete mismatch.
   Start010 was re-run under the committed instrument (`runs/a31/trace2/`), and the two
   generations agree on every shared count bit-for-bit. Published per-pass numbers for
   start010 come from `trace2/`; start005 ran the committed format's content. Reversal: none
   needed — both generations are kept.
3. **Neutrality gate re-run on the clean committed tree** after noting the first gate run
   carried uncommitted instrument edits (the audit-trail gap A30 flagged in A28, applied to
   this task's own runs). Both gate runs passed 3/3 with 3/3 teeth. Provenance of every run
   generation is disclosed in §7.
4. **The optional `A0'` run was taken** (authorized as optional in the brief) and produced
   §3's cross-arm confirmation.
5. **A V14 follow-up entry was appended to the DSM register** (protocol §11) pointing at this
   report; the register is append-only and unarchived.

## 7. Provenance and reproduction

Run generations (every run: fresh subprocess, own working directory, `PYTHONPATH` pinned to
this worktree, exact tree asserted in-process — traps T6/T10):

| generation | runs | tree state recorded by `run_one.py` |
|---|---|---|
| `runs/a31/neutrality/` (final) | gate run | `a1a4a9ce`, clean |
| `runs/a31/trace/` | `A1'` start010 (v1 trace format), start005 (committed format's content) | `377de650` + uncommitted instrument edits, identical in content to `a1a4a9ce` for start005; start010's v1 differed only in not recording constant detail |
| `runs/a31/trace2/` | `A1'` start010 re-run, `A0'` start010 | `A1'`: `a1a4a9ce` content (stamped dirty — the subprocess started seconds before the commit landed); `A0'`: `a1a4a9ce`, clean |
| `runs/a31/smoke/` | instrument validation | `377de650` + edits; unpublished |

Where two generations exist (start010), every published count is bit-identical across them.

Reproduction, from this worktree (environment `PROCESS_surgery_env`):

```
cd arch_surgery/idf_probe
python a31_drift_probe.py neutrality          # the gate, teeth included
python a31_drift_probe.py trace               # traced A1' runs, start010 + start005
python a31_drift_probe.py retrace             # A1' start010 under the committed trace format
python a31_drift_probe.py a0p                 # traced A0' run, start010
python a31_drift_probe.py analyze --with-a0p  # every table and count in this report
```

Which stage produced which figure: §1's table and the campaign fingerprint — `analyze`
(`runs/a31/analysis/summary.json`, `per_pass_movers_*.json`); §3's `A0'` numbers — `analyze
--with-a0p` over the `a0p` stage's trace; §4's gate — `neutrality`
(`runs/a31/neutrality/gate.json`); ULP examples — the `moved_constant_detail` records in
`runs/a31/trace/A1p_start005/pass_trace.jsonl` and `runs/a31/trace2/A1p_start010/pass_trace.jsonl`.
Source citations: `git show c0ae5b28:process/models/power.py` (`:352`, `:411`),
`…/models/fw.py` (`:348–352`), `…/models/tfcoil/superconducting.py` (`:201`, `:1266`, `:1878`,
`:1883`, `:3789`, `:4129`, `:2176`), `…/models/costs/costs.py` (`:2167`),
`…/core/solver/objectives.py` (`:61`), `…/models/physics/physics.py` (`:387`, `:395`).
Bulk trace artifacts stay untracked per the standing rule; the committed script regenerates
them.

## 8. Change log

- 2026-09-03 — task opened; mandatory reads done; instrument designed against V14 +
  follow-ups and R1a.
- 2026-09-03 — trace hooks added to `caller.py`/`module_solve.py` behind
  `PROCESS_ARCH_PASS_TRACE`; committed driver script `a31_drift_probe.py`; first neutrality
  gate PASS (3/3 fields, 3/3 teeth).
- 2026-09-03 — instrument validation at start000; traced `A1'` start010: recurring failures
  are **moved constants**, not τ-exceedances; trace format upgraded to record constant
  before/after hex; instrument committed (`a1a4a9ce`).
- 2026-09-03 — traced `A1'` start005 (upgraded format): `pf_power.srcktpm` alone on all 960
  recurring failing records, deltas exactly 1–2 ULPs; start010 re-run under committed
  instrument (bit-identical counts); optional `A0'` start010 run: same flicker, plus
  `costs.c22524` (in-loop there) and the smaller `beta_norm_max_stambaugh` member.
- 2026-09-03 — final neutrality gate on clean tree PASS; `analyze --with-a0p` produced the
  published summary; campaign fingerprint 25/25; report written; V14 follow-up appended to
  the DSM register.
