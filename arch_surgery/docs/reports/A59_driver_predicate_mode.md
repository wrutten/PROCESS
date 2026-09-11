# A59 (driver-predicate-mode) — the convergence predicate's two rulers

> **Document status** — **OPEN.** Task **A59 (driver-predicate-mode)**, branch
> `A59-driver-predicate-mode` off `architecture_surgery` at `01afc009`. Driver change **DR5** of the
> V4 harness implementation plan; the pre-declared trial of improvement list item 5a; gate **G8** of
> the experiment plan §3.9. Awaiting the orchestrator's critical assessment (protocol §5). Folder
> position records lifecycle, not validity (trap T3).

---

## 1. Verdict

**DR5 landed and every gate passes.**

| gate | verdict | the numbers |
|---|---|---|
| **G0′** the physics is frozen in the copy | **PASS** | 77 model files compared against `c0ae5b28` byte for byte, 76 identical, the one difference approved (D14(b)); the file set matches; 4 teeth trip |
| **G1** switch neutrality | **PASS** | 6 run pairs (3 configurations × 2 reference arms); **0 of 2 341** record values differ, **0 of 51 319** output-file lines differ; 1 277 values and 45 lines excluded by name; 4 teeth trip. Exclusion set **43 → 48** names |
| **GR** the rewrite still reproduces the previous revision | **PASS** | **20/20** runs, **270/270** compared values, 0 mismatched; both §7.5 substitutes PASS; **7** teeth trip |
| **G8** the predicate trial | **PASS** | (1) neutrality — GR's own verdict, read: 20/20, 0 of 270. (2) the identity — **12/12** pairs bit-identical; **0 of 7 564** record values and **0 of 84** output-file lines differ. (3) the binding set — **66** component events over **143** observed predicate evaluations, **48** distinct components, `\|y\|/s` from **1.04 to 54.6**; **0** of them held the pass open, so **0** evaluations changed verdict. 4 teeth trip |
| copy identity / `PROCESS_diff.py` | PASS / exit 0 | 224 files, 218 identical, 6 permitted-edit files, **0 unexplained** hunks |
| `experiment_runner.py --selfcheck` | **PASS** | 6 checks, every tooth tripping |

**The headline result of the trial, stated with its population.** Across 24 runs — three
configurations × the evaluation-phase arms `A0` and `A1` × seeds 1 and 2, each under both rulers, at
δ = 0.10 — the two rulers disagreed about **66 components** at **13 of 143** predicate evaluations,
on **9 of 12** pairs, with the current magnitude up to **54.6 ×** the harvested scale. **Not one of
those components was the one holding its evaluation open.** So no evaluation changed its verdict,
no loop stopped earlier, and all twelve pairs are bit-identical on every record value and every
output-file line. `COMPONENTS_COMPARED` is identical within every pair, which is the free
consistency check A58 (driver-predicate-counters) handed over.

That is a result about these arms and these seeds, not a claim about the campaign. §7 says what it
does and does not license.

---

## 2. The words, spelled out once

| term | meaning |
|---|---|
| **configuration** | one optimisation problem. Three: `large_tokamak_nof` and `low_aspect_ratio_DEMO` (pulsed), `st_regression` (steady-state) |
| **arm** | one setting of the driver's switches. `AR`/`BR` are PROCESS as shipped; `A0` replaces its stopping rule with the coupling-state one; `A1` additionally solves the model set as three blocks |
| **coupling state** | the 827–846 state fields the in-loop models write and read from each other. The convergence test is a max-norm over them |
| **predicate** | the convergence test a loop stops on |
| **ruler** | *new in this task.* What the predicate divides a step by before comparing it with the tolerance. Two of them: `frozen` and `mixed` (§3) |
| **scale `s_i`** | the median magnitude of one component over a harvest of design points, measured once and committed in the coupling-state artifact. The `frozen` ruler *is* this number |
| **τ** | the one tolerance of every converger in every arm and both phases, 1e-6 (decision D23) |
| **decisive pass** | the experiment plan §3.6's term: a component at or above τ on `frozen` and below it on `mixed`. The only way the two rulers can disagree at all |
| **exit audit** | one further full sweep past termination, measuring how far the coupling state still moves. The same instrument in every arm; its own model calls are never charged to the arm |
| **tooth** | a deliberate break a gate must catch. A check never shown to fail is an assertion, not a measurement (protocol §12) |
| **D5 / D11 / D14(c) / D20 / D23** | recorded user decisions: the models are frozen; minimal structural model edits need approval; **exactly one implementation of the predicate per revision**; V4 runs its own copy of PROCESS; one tolerance everywhere |
| **I-12** | a recorded issue: a relative test scaled by a frozen median becomes arbitrarily tight where a quantity diverges, and PROCESS's 1990 cost model diverges at infeasible points |

---

## 3. The two rulers

A continuous component of the coupling state passes the convergence test when its largest scaled
step is below τ. **The scaled step's numerator is the same in both rulers. Only the denominator
differs.**

| ruler | a continuous component passes when | denominator |
|---|---|---|
| **`frozen`** | `max\|Δy_i\| / s_i < τ` | the measured scale alone |
| **`mixed`** | `max\|Δy_i\| / max(\|y_i\|, s_i) < τ` | that scale kept as a **floor**, under the current magnitude |

`mixed` is Dennis & Schnabel's scaled step test — what MINPACK's `diag`, KINSOL's scaling vectors
and OpenMDAO's output `ref` all reduce to.

**Which `y_i`, and why.** The **current** value: the post-sweep iterate `cur`, not the previous one.
The test asks how large the step is *relative to where the state now is*, which is what a reader
means by "converged to six digits"; taking the magnitude from the previous iterate would scale a
step by a magnitude the state has already left. For an array component the magnitude is
`max|elements|` over the finite entries — exactly what `_char_mag` measures the *scale* by — so only
the denominator differs and not the way a magnitude is taken.

**Three properties hold by construction**, and they are what make the pair cheap to interpret
rather than a second predicate to validate:

- wherever `|y_i| ≤ s_i` the two are **bit-identical** — the denominator is the same float and the
  division is the same division (G8's tooth `bit_identity_below_the_scale`);
- `mixed` is **never tighter**, because its denominator is never smaller, so no count of components
  above τ can go up;
- discrete components, moved constants, a new NaN, a changed non-finite pattern and a component no
  model has written yet (scored `inf`) behave **identically** under both. The ruler touches the
  continuous scaling and nothing else.

**Why a second ruler exists at all** is a measured case, not a preference. Issue **I-12**:
`costs.coe` reaches 6.6 × 10²¹ at a design point with negative net electric power, against a
harvested scale of 1 251, which makes the `frozen` test there roughly 10¹⁸ times tighter than it
reads and iterates the point until the state stops changing in its last bit. Upstream PROCESS's own
test, being relative to the current value, is *looser* than ours at that point by 5.3 × 10¹⁸.
`mixed` is the smallest change that removes the mechanism while keeping the measured scale as a
floor, so a quantity that is genuinely small is still tested absolutely rather than against its own
noise.

### 3.1 Where each is applied

*Caption: one row per site. Paths are relative to `arch_surgery/MDA_partitioning_experiment_v4/`;
line numbers are at the final commit of this branch.*

| site | file:line | what it does |
|---|---|---|
| the rulers' names | `harness/ystate.py:184,190` | `RULER_FROZEN`, `RULER_MIXED`, `RULERS`, `RULER_DEFAULT = frozen` |
| the refusal | `harness/ystate.py:208` | `assert_ruler` — a ruler that is neither raises `RulerError`, never defaults |
| the denominator, continuous | `harness/ystate.py:903-909` | `den = scale[i]`; under `mixed`, `mag = _char_mag(fb)` and `den = mag` if larger |
| the denominator, non-finite | `harness/ystate.py:937-947` | the same, with the magnitude taken over the **finite** entries only — a non-finite element must not set the denominator of a test it is excluded from |
| the entry points | `harness/ystate.py:812,834` | `YSpec.residual(..., ruler=...)`, `YSpec.residual_over(..., ruler=...)`, default `frozen` |
| the switch | `PROCESS/process/core/solver/module_solve.py:215-240` | `PREDICATE_MODES`, `PREDICATE_MODE`, the typed refusal |
| the guard's own check | `PROCESS/process/core/solver/module_solve.py:533` | the literal list is checked against the coupling-state module's `RULERS` the first time that module is loaded |
| the spec's stamp | `PROCESS/process/core/solver/module_solve.py:606` | `predicate_mode` in the loaded spec's provenance, **beside the tolerance** |
| **the one predicate call site** | `PROCESS/process/core/caller.py:1488` | `ruler=module_solve.PREDICATE_MODE` |
| the exit audit, both rulers | `harness/child.py:1245` | the loop over `ystate_rulers(spec)` |

**There is exactly one predicate call site in the driver**, and it serves both arrangements — the
flat one's single block over every in-loop node, and each block loop of the partitioned one. So
there is one place the choice is made and **no path on which a loop can stop on a ruler the record
does not name**.

---

## 4. The switch

| term | variable | values | composed by | readback | default |
|---|---|---|---|---|---|
| predicate mode | `PROCESS_ARCH_PREDICATE` | `frozen`, `mixed` | an arm, only for the trial — `frozen` composes nothing and is the variable unset | `module_solve.PREDICATE_MODE` | `frozen` |

- Resolved **once at import**, so an illegal value raises before any file is read:
  `PROCESS_ARCH_PREDICATE=Mixed` → `ArchitectureRefusal: … is not a recognised convergence ruler;
  expected one of ('frozen', 'mixed') (or unset for 'frozen'). Refused rather than defaulted: a run
  of one predicate recorded under the other's name cannot be told apart afterwards.`
- `switches.REGISTRY["predicate_mode"]` now carries its `driver_name`. **The registry has no entry
  left with `driver_name = None`** — A57 (driver-output-path) §13 predicted exactly this, and §8
  decision 5 says what was done about the two teeth that were biting on it.
- The campaign default is `frozen` (`config.Campaign.predicate_mode_default`). **Adoption is a
  later decision**, made by the experiment plan §3.6's own rule on the trial's numbers, not by this
  task.
- **`COMPONENTS_COMPARED` is unchanged by the ruler.** The width of an evaluation is the block's
  write set, which the ruler does not touch. A58 (driver-predicate-counters) handed this over as the
  free consistency check between the modes, and G8 uses it: the counter is identical within all
  twelve pairs (§6.2's table, column `comps`).

---

## 5. The predicate module's identity criterion, re-based

**The mechanism, stated.** `harness/ystate.py` is V4's own predicate module (D20; harness plan §5.3
option (v)), and D14(c) says there is exactly one implementation of the predicate per revision — the
copied driver loads *this* file by a fixed path and the harness imports it. DR5 is therefore
implemented **in it**, which broke the check A48 (harness-data) could make about it.

| | before (A48) | after (A59) |
|---|---|---|
| what the file is | its source at commit `30198919` plus one heritage paragraph | its source plus the recorded edits of `data_provenance.MODULE_EDITS` |
| the criterion | the diff is the one recorded hunk **and** removing it reproduces the source byte for byte | the whole diff is exactly the recorded hunks **and** the post-edit sha256 is the recorded one |
| recorded | 22 diff lines, 1 hunk | **342 diff lines, 22 hunks**, plus three `MODULE_EDITS` entries naming what each is, what it does and which task made it |
| reconstruction | required | **unavailable, not dropped** — it still runs and is still required wherever the recorded hunks are a pure addition (`data_provenance.is_pure_addition`) |

This is the model `PROCESS/copy_gates.py` already uses for the copied driver: **an edit is legal
because it is recorded and reviewable, not because it is absent.** Both halves of the criterion are
load-bearing and each catches what the other cannot:

- an edit with **stale hunks** is caught by the digest;
- an edit whose **digest was updated to match** is caught by the hunks — a digest cannot be updated
  to satisfy a hunk list.

Both are teeth of the self-check's `data` check and both trip. They were exercised for real, not
only synthetically: a late rename of `_assert_ruler` → `assert_ruler` in `ystate.py` made the check
FAIL before it was re-recorded, which is what it is for.

A new stage, `harness/data_provenance.py record --force`, rebuilds the record from the files as
they stand **without re-copying the data**. Re-copying would re-bless whatever the sources hold — a
far larger claim than the one being made — and the symmetry with `copy_gates.py provenance --force`
is deliberate.

---

## 6. The gates

Every number below comes from a committed script, run at the commit named. Bulk run artifacts are
untracked by design; the verdict records are under `runs/gates/` in the worktree.

### 6.1 G0′, G1, GR, and the copy's own gates

*Caption: one row per gate. "Population" is what was actually compared. Every criterion is a count
or a bit-comparison; no tolerance is applied anywhere and no timing is evidence.*

| gate | stage | population | result | teeth |
|---|---|---|---|---|
| **G0′** | `python PROCESS/copy_gates.py frozen-physics` | 77 files under `PROCESS/process/models/` against `git show c0ae5b28:process/models/…`, plus the file set | **PASS** — 76 identical, 1 approved (`pulse.py`, D14(b)), 0 unapproved | 4/4: a 1-byte change, a removed file, an added file, a further change to the approved file |
| **copy identity** | `python PROCESS/copy_gates.py copy-identity` | 224 files of the copied package against source commit `f2dc9243` | **PASS** — 218 identical, 6 permitted-edit files whose hunks and post-edit digests match, **0 unexplained** | 4/4 |
| **`PROCESS_diff.py`** | `python PROCESS_diff.py` | every hunk of the copy's diff against its source commit | **exit 0**, 0 unexplained hunks; DR5 claims 1 hunk in `caller.py` and 5 in `module_solve.py` | — |
| **G1** | `python -m harness.gates switch-neutrality --capture before\|after` then `… switch-neutrality` | 6 run pairs = 3 configurations × 2 reference arms (`AR`, `BR`), seed 0, both sides audited at `after_run` | **PASS** — **0 of 2 341** record values, **0 of 51 319** output-file lines; 1 277 values and 45 lines excluded by name | 4/4: a 1-ULP change to `norm_objf`; one output-file line changed; a missing `before` record (must refuse); two captures audited at different positions (must refuse) |
| **GR** | `python experiment_runner.py --gate reproduction --lifted-from …` | 20 previous-revision records (14 optimisations + 6 evaluations) over 3 configurations | **PASS** — **20/20** runs, **270/270** values, 0 mismatched; substitutes `A0p` and `AR` PASS | 7/7: count, hex, missing reference, missing key, bad name map, composition, attempt summation |
| **self-check** | `python experiment_runner.py --selfcheck` | 6 checks — composition, rungs, capability, provenance, data, run path | **PASS** | every tooth trips |

**G1's `before` capture was taken at the branch point `01afc009` with the driver byte-identical to
`architecture_surgery`'s tip** — the worktree was clean and at that commit (verified with
`git status` and `git log` before the capture ran), and the capture manifest stamps
`tree_git_head = 01afc0093023e917d92e634a604c2ea845fd9ec7`. The `after` capture was taken at this
branch's final driver state.

**G1's exclusion set: 43 → 48 names.** Five were added, and the reason is the same for all five:
the field is **absent** on the earlier side because the choice did not exist, not because the two
sides behave differently.

| name | why |
|---|---|
| `exit_audit.predicate_mode` | the ruler stamp; the name of the default, not a behaviour |
| `exit_audit.frozen` | the frozen ruler's audit under its own name, absent on the earlier side |
| `exit_audit.mixed` | the second ruler's audit, which the earlier side had no way to take |
| `exit_audit.rulers_note` | the sentence saying the two are published together |
| `coupling_state_provenance.predicate_mode` | the loaded spec's stamp of the ruler, beside the tolerance it already carried |

**What is *not* excluded is the load-bearing part.** The exit audit's unprefixed fields —
`residual_max`, `residual_max_hex`, the whole `brief` block, the whole `restricted` block — keep
their names and their values as the frozen ruler's and are **compared value for value on both
sides**. They are taken from the same computation that fills `exit_audit.frozen`, so there is one
computation and two presentations of it. The strongest thing G1 compares therefore stays inside the
comparison; what is excluded is a second presentation and a stamp of the setting.

### 6.2 G8 — the trial

Run in two stages, both committed:

```
python -m harness.gates predicate-mode --capture runs   # 3 references + 24 runs
python -m harness.gates predicate-mode                  # compare, with teeth
```

**Part (1), neutrality of the default ruler.** Not re-implemented here. Every run gate GR makes is
composed under the default ruler, so GR's bit-for-bit reproduction of the previous revision — its
evaluation-phase arms among them — *is* the neutrality criterion. G8 reads GR's committed verdict
and states what it covers; a second implementation of one comparison is the drift D14(c) exists to
prevent. **A missing GR verdict is a FAIL, never a skip** — and that path was exercised: G8 read
`NO EVIDENCE` and failed before GR had been run at this commit, then passed after. GR: **20/20 runs
reproduced, 0 of 270 compared values differ.**

**Part (2), the identity.** 12 pairs = 3 configurations × the evaluation-phase arms active on each
(`A0`, `A1`) × seeds 1 and 2, each run under both rulers, δ = 0.10, entered from the same reference
exit state with the same burn-time constant. **0 of 7 564 record values and 0 of 84 output-file
lines differ**; 216 record values excluded, each named with its reason (17 names, §6.4).

*Caption: one row per pair. "evals" is the number of predicate evaluations the observer watched on
the frozen run; "decisive" is how many of those had at least one component crossing τ between the
rulers; "verdict" is how many had the crossing component also holding the evaluation open — the
narrower event, and the only one that can make two runs differ. "comps" is `COMPONENTS_COMPARED`,
identical within every pair. The last two columns are the exit audit's maximum scaled residual as
an exact hex float, **on both rulers**, from the run made under `frozen`; the run made under
`mixed` reports the same two numbers, which is what being bit-identical means.*

| configuration | arm | seed | evals | decisive | verdict | record values | output lines | comps (frozen = mixed) | audit · frozen | audit · mixed |
|---|---|---:|---:|---:|---:|---|---|---:|---|---|
| `large_tokamak_nof` | A0 | 1 | 9 | 3 | 0 | 0/622 | 0/7 | 5 040 | `0x1.5fe433222bb97p-29` | `0x1.f8c2a9ec36d62p-31` |
| `large_tokamak_nof` | A0 | 2 | 8 | 1 | 0 | 0/622 | 0/7 | 4 200 | `0x0.0p+0` | `0x0.0p+0` |
| `large_tokamak_nof` | A1 | 1 | 15 | 2 | 0 | 0/674 | 0/7 | 2 895 | `0x1.f5b2a3ea40bd7p-1` | `0x1.774db44e2d2b1p-3` |
| `large_tokamak_nof` | A1 | 2 | 15 | 1 | 0 | 0/674 | 0/7 | 2 895 | `0x1.c4dcc35b240c9p+0` | `0x1.656469d523e7ep-2` |
| `low_aspect_ratio_DEMO` | A0 | 1 | 8 | 0 | 0 | 0/612 | 0/7 | 4 230 | `0x0.0p+0` | `0x0.0p+0` |
| `low_aspect_ratio_DEMO` | A0 | 2 | 8 | 1 | 0 | 0/608 | 0/7 | 4 230 | `0x0.0p+0` | `0x0.0p+0` |
| `low_aspect_ratio_DEMO` | A1 | 1 | 15 | 0 | 0 | 0/664 | 0/7 | 2 919 | `0x1.ad17b67239f49p-4` | `0x1.a621cc5cabcc8p-4` |
| `low_aspect_ratio_DEMO` | A1 | 2 | 15 | 0 | 0 | 0/660 | 0/7 | 2 919 | `0x1.2cdce94f65769p-3` | `0x1.24c92dd10e577p-3` |
| `st_regression` | A0 | 1 | 9 | 2 | 0 | 0/582 | 0/7 | 4 962 | `0x1.9e44b1da8552dp-29` | `0x1.211b7a2189fc0p-29` |
| `st_regression` | A0 | 2 | 9 | 1 | 0 | 0/582 | 0/7 | 4 962 | `0x1.05028b3bcc6bfp-27` | `0x1.6c4dec4c0f592p-28` |
| `st_regression` | A1 | 1 | 16 | 1 | 0 | 0/632 | 0/7 | 3 037 | `0x1.fabf584472547p-3` | `0x1.3cec1f486b6d0p-3` |
| `st_regression` | A1 | 2 | 16 | 1 | 0 | 0/632 | 0/7 | 3 037 | `0x1.e15dc1afec083p-3` | `0x1.ccd4e2d6e3fcap-4` |

**Both audit columns are shown because one alone would report a change of ruler as a change of
accuracy.** The `mixed` column reads lower wherever its denominator binds — by construction, not by
being more accurate. This is improvement item 5a's trap (ii), and the record now makes showing one
column alone difficult rather than merely discouraged: `records.assert_both_rulers` **refuses** a
finished record that carries one and not both, and the pair is in the completeness contract.

**Part (3), the binding set.** **66 component events** over the **143** predicate evaluations these
24 runs made, on **13** distinct evaluations across **9 of 12** pairs, involving **48 distinct
components**.

*Caption: one row per distinct component (grouped where the ratio is shared), with the largest
`|y_i| / s_i` observed for it in this population. Every one of these crossed τ between the rulers at
some evaluation; **none of them held its evaluation open**, so none changed a verdict — `held` and
`changed` were `False` for all 66 events. Population: 24 runs at δ = 0.10, arms `A0`/`A1`, seeds 1
and 2, three configurations.*

| component | max `\|y\|/s` |
|---|---:|
| `power.e_plant_net_electric_pulse_mj`, `power.e_plant_net_electric_pulse_kwh` | 54.59 |
| `heat_transport.p_plant_electric_net_mw` | 13.81 |
| `cs_fatigue.n_cycle` | 7.44 |
| `power.p_plant_electric_net_profile_mw` | 3.28 |
| `heat_transport.p_shld_coolant_pump_mw`, `fwbs.p_cp_shield_nuclear_heat_mw`, `power.p_shld_coolant_pump_elec_mw`, `power.p_shld_heat_deposited_mw` | 2.63 |
| `heat_transport.p_plant_electric_gross_mw`, `power.p_plant_electric_gross_profile_mw` | 2.37 |
| `heat_transport.p_plant_primary_heat_mw` | 2.30 |
| `pf_coil.temp_cs_superconductor_margin` | 2.28 |
| `costs.c26`, `power.p_turbine_loss_mw`, `water_use.evapvol`, `water_use.wateruseonethru`, `water_use.wateruserecirc`, `water_use.waterusetower` | 2.26 |
| `pf_coil.j_cs_conductor_critical_pulse_start`, `pf_coil.jcableoh_bop` | 2.13 |
| `costs.c2261`, `power.p_fw_heat_deposited_mw`, `costs.c23` | 2.04–2.15 |
| `tfcoil.j_crit_str_tf` | 1.61 |
| `costs.c2221` | 1.46 |
| `pf_coil.j_cs_critical_pulse_start`, `tfcoil.a_tf_inboard_total`, `tfcoil.a_tf_leg_outboard`, `tfcoil.drarea`, `tfcoil.insstrain`, `tfcoil.vforce`, `tfcoil.vforce_outboard`, `superconducting_tfcoil.vforce_inboard_tot`, `pf_coil.vs_cs_pf_total_ramp`, `build.r_sh_inboard_out` and 18 further components | 1.04–1.39 |

Events by configuration: `st_regression` 41, `large_tokamak_nof` 24, `low_aspect_ratio_DEMO` 1. The
full list, with the evaluation index and both scaled residuals as hex floats per event, is in
`runs/gates/predicate_mode/gate.json` under `binding_set`.

**Two observations worth carrying forward, both with their limits.**

1. **`power.e_plant_net_electric_pulse_{mj,kwh}` at 54.6 × its harvested scale on `st_regression`**
   is the same family improvement list item 5a flagged from an ad-hoc read of the artifacts, which
   put them at 50 ×. This is the first *committed* measurement of that ratio at a run-time state
   rather than over the harvest, and it agrees.
2. **`tfcoil.insstrain` appears in the binding set at 1.27 ×** on `large_tokamak_nof`. A57
   (driver-output-path) reported it ~7e-3 above τ at the accepted point on both pulsed
   configurations (improvement list item 11). Under `mixed` its scaled residual at the evaluations
   where it binds is about 21 % smaller. That does **not** resolve item 11 — 7e-3 is far above τ and
   21 % does not close it — and it is recorded here only so the two observations are not read
   independently later.

### 6.3 The teeth

*Caption: one row per gate's deliberate breaks. Every gate's teeth ran at the final commit and every
one tripped.*

| gate | tooth | construction | tripped? |
|---|---|---|---|
| **G8** | `doctored_component` | the plan's own: a synthetic component at `y = 100 s` with `Δy = 50 τ s`, and the same `Δy` at `y = s`, on the `Residual` directly | **yes** — 5.000e-05 frozen (≥ τ) and 5.000e-07 mixed (< τ); at `y = s`, 5.000e-05 on both |
| **G8** | `bit_identity_below_the_scale` | a component with `\|y\| = 1.875` well below `s = 7.5` | **yes** — both rulers give `0x1.2534000000000p-33` |
| **G8** | `one_ulp_between_identical_records` | one float of a real record moved by a single unit in the last place, compared under the gate's own exclusion set | **yes** — 1 of 622 compared values differ |
| **G8** | `the_mixed_audit_is_compared` | a changed `exit_audit.mixed.residual_max_hex` | **yes** — 1 differing value; the block the plan permits excluding is compared |
| **G1** | 1-ULP; one output line; missing `before` record; mismatched audit positions | as A57/A58 left them | **4/4** |
| **G0′** and copy identity | 1-byte; file removed; file added; approved file changed further | as A46/A48 left them | **8/8** |
| **GR** | count; hex; missing reference; missing key; bad name map; composition; attempt summation | as A50/A56 left them | **7/7** |
| self-check `data` | one byte changed; a file missing; a file the record does not name; a changed file whose digest was updated to match; **an unrecorded edit to the predicate module**; **an edited predicate module whose digest was updated to match** | the last two are new (§5) | **6/6** |
| self-check `run path` | a declared field removed; **an exit audit carrying one ruler and not both**; an unlabelled run kind; two attempt-summation breaks; two displacement-stream breaks; four run refusals, two of them the re-pointed allowance teeth | the ruler-pair tooth is new; the allowance pair is re-pointed (§8 decision 5) | **11/11** |

### 6.4 Two points about the gates' own construction

**(a) G8 does not infer "no decisive pass" from "the two runs agree".** That would be circular, and
a circular gate passes on a defect. A decisive pass is an event **inside a loop** and a record
carries counters, so the gate's runs carry an independent detector:
`child.install_ruler_observer` (`harness/child.py:951`) wraps the coupling-state spec's `residual`
on the instance, **returns the run's own residual unchanged** — the same object, from the same
method, so no float the run uses comes from the instrument — and computes the other ruler's
residual beside it, recording every crossing to its own file (`ruler_observation.json`, never into
the record). It is switched by `HARNESS_RULER_OBSERVER`, a **harness** variable the driver has never
heard of and which therefore cannot be mistaken for an architecture switch, and it **refuses
outright on a campaign run**: it doubles the predicate's cost, and a per-sweep cost measurement
taken with a doubled predicate would be a measurement of the instrument.

**Two events are counted, not one, and the difference is load-bearing.** The plan's *decisive pass*
is componentwise. Whether a pair's runs may then differ is narrower: the crossing component must
also have been the one holding the evaluation open, so the evaluation's verdict changes. Part (2)'s
criterion binds on the **narrower** one. Reporting the wider event as the narrower would let a
defect hide behind a crossing that could not have caused it; reporting the narrower as the wider
would understate the binding set. This measurement is exactly the case where they differ: 13
evaluations had a crossing, 0 changed a verdict.

**(b) G8 compares `exit_audit.mixed` rather than excluding it.** The plan permits excluding the
block. It is compared instead, because a pair with no decisive pass reaches the same exit state and
both audits of one exit state are the same numbers — so comparing it costs nothing and is strictly
stronger. A tooth confirms the block is genuinely in the comparison. **G8's exclusion set is 17
names against G1's 48**, and deliberately so: G1's two sides are at different commits and made by
different revisions of the harness, while G8's are the same code at the same commit run twice with
one setting changed, so almost nothing is licensed to differ. The 17 are the run's own directory,
nine run-metadata fields (wall clock, three cpu fields, peak memory, machine load, the output
file's own runtime, and the two untracked-path fields) and seven mode stamps
(`campaign_predicate_mode`, `switches_asked.predicate_mode`,
`env_architecture.env_PROCESS_ARCH_PREDICATE`, the driver's readback of it,
`coupling_state_provenance.predicate_mode`, `exit_audit.predicate_mode`, `exit_audit.rulers_note`).

**Before anything is concluded from a pair, each run's driver readback is checked**: the record's
`resolved_switches[…module_solve.PREDICATE_MODE]` must equal the ruler the job asked for. A setting
the tree ignored would otherwise produce a successful run of one ruler under the other's name —
the failure the switch registry exists to prevent, and exactly what the trial's whole argument
would rest on if it were not checked.

---

## 7. What this licenses and what it does not

**Licensed.** The implementation is correct on the criterion the plan set: under the default the
runs reproduce the previous revision bit for bit; under the trial ruler, every pair with no changed
verdict is bit-identical; the components where the two rulers differ are named with their ratios.
Gate G8 does not block adoption.

**Not licensed, and stated so it is not read as licensed.**

- **This is not the trial's measurement.** §3.6's measurement is Phase A — `A0`, `A0p`, `A1`, **25
  seeds**, three configurations, δ = 0.10 — under both modes, with counts, ratios and seed brackets.
  This gate ran **2 seeds** and two arms. The adoption decision is made on that measurement by
  §3.6's rule, by A53 (harness-tally) and the campaign, not here.
- **"0 evaluations changed verdict" is a statement about 143 evaluations at two seeds**, not about
  the campaign. The mechanism that would change one plainly exists — 66 crossings at ratios up to
  54.6 — and a seed whose trajectory puts one of those components at the argmax would change a
  verdict. Reading "no effect" out of this would be trap **T11** in its exact shape.
- **I-12's own population is not in this gate.** I-12 bites on `costs.coe` at a divergent point, and
  the arms here take `costs` out of the loop on the per-run deferral path, so the mechanism cannot
  fire in them. Item 5a notes that A26's replay ladder at `hoist = 0` exercises that population
  directly; nothing here does.
- **No timing is evidence.** None is quoted.

---

## 8. Autonomous decisions, with reversal paths

*Caption: one row per decision this task made without asking. "Reverse by" is what a later task does
to undo it; none of them is load-bearing for a measurement.*

| # | decision | why | reverse by |
|---|---|---|---|
| 1 | The exit audit carries **both** ruler blocks on **every** run, whatever ruler the run stopped on | item 5a's trap (ii) is "both columns or neither", and a record that sometimes has one column makes a table that sometimes reports a ruler change as accuracy. Cost: one further pass over two states already in memory, no model call | drop `exit_audit.mixed` when the run's ruler is `frozen`; remove `AUDIT_RULERS` from `records.CONTRACT` and the `assert_both_rulers` refusal |
| 2 | The unprefixed `exit_audit` fields stay the **frozen** ruler's, unchanged in name, shape and value, and `exit_audit.frozen` presents the same numbers under a symmetric name | GR reads `exit_audit.residual_max_hex` by path and G1 compares the block value for value; a rename would have moved the strongest thing G1 compares. The symmetric pair is what a tally should read. One computation, two presentations | delete the `exit_audit.frozen` block and have A53 read the unprefixed fields as the frozen column; G1's exclusion set loses one name |
| 3 | The per-component **vectors** live in `audit_residual.json`, not in the record; the record carries the summary and a pointer | the two rulers' vectors are ~3 400 further leaves per record, which a tally reads and a gate walks value by value. Found because G1's excluded-value count jumped to 20 829 | move `scaled_hex` / `value_over_scale` back into the ruler blocks in `child.take_exit_audit` |
| 4 | `artifacts.check`'s `predicate_mode` row reads **"not applicable — the ruler is a run setting"** rather than being stamped | the orchestrator's ruling (i). Both rulers read the same components and the same scales, so a committed artifact has nothing to stamp, and stamping one would break the byte identity the data check guards | stamp the committed artifacts and re-derive their digests — which also re-opens §5 |
| 5 | The two **allowance** teeth are re-pointed onto a **doctored registry** rather than retired | they used to bite on this very switch while it was pending. Going quiet would leave `pool.environment_for`'s two refusals untested for as long as the registry happens to be complete, and they would be found broken by the task that next needed them. The doctoring is stated in each tooth's evidence, confined to the two checks, and undone in a `finally`; a third, **live** check says `B0` under `mixed` composes the switch and needs no allowance at all | replace both with a note saying nothing is pending, in `selfcheck.check_run_path` |
| 6 | G8's detector is a **harness-side wrapper** on the spec's `residual`, not a driver hook | it needs no further edit to the copied driver, observes every evaluation of both arrangements, and returns the run's own residual unchanged. A driver hook would have been a third thing for G0′, G1 and `PROCESS_diff.py` to carry | add an observation mode to `module_solve.trace_pass` and delete `install_ruler_observer` |
| 7 | G8 **compares** `exit_audit.mixed` instead of excluding it | strictly stronger and free; the plan permits either (§6.4(b)) | add the name to `PREDICATE_PAIR_EXCLUSIONS` |
| 8 | A new stage `data_provenance.py record --force` that re-records without re-copying | re-copying re-blesses whatever the sources hold, a far larger claim than "this module's edits are recorded" | use `copy --force` and accept the wider claim |
| 9 | `Residual.brief()`'s six keys are **untouched**; the new per-component reporting is a separate method `ruler_detail()` | `brief` is compared value for value by G1 and appears in every earlier record; adding a key to it would move a gated field | fold `ruler_detail` into `brief` and add the exclusion |

**Two defects were found by the gates and fixed on the branch**, both reported rather than smoothed
over:

1. **G8 FAIL, 36 of 46 812 values** — the ruler stamp was written **twice**: once at
   `exit_audit.predicate_mode` and again inside each ruler block as
   `is_the_ruler_the_run_stopped_on`. Two of the three differing values per pair were that
   duplicate. Fixed by stamping once; the block's key says which ruler the block is. The third was
   `env_architecture.env_PROCESS_ARCH_PREDICATE`, whose key the exclusion set had spelled without
   the record's `env_` prefix.
2. **G1 PASS but with 20 829 excluded values against 2 341 compared** — decision 3 above. A pass
   whose exclusion count is an order of magnitude larger than its compared count is not a pass
   anybody should accept, which is why the number is published beside the zero. After the fix:
   1 277 excluded, 2 341 compared.

---

## 9. Handover

| to | what |
|---|---|
| **A52 (harness-gates)** | (a) wire `predicate-mode` into `experiment_runner.py --gate` beside `g0prime`, `switch_neutrality` and `output_path` — it is registered in `gates.registry` and has its own `__main__` CLI, and this task did not edit `experiment_runner.py`. (b) **G1's exclusion set is now 48 names** and is inherited for review as one table, not extended. (c) `compare_records` now takes its exclusion set as an argument; G8's own set (17 names) is the pattern for a gate whose two sides are at the same commit. (d) `harness/child.py`'s ruler observer is a gate instrument: it must never reach a campaign run, and it refuses one itself |
| **A53 (harness-tally)** | (a) **§4.2.5's table**: every residual column is published on **both** rulers or neither, and `records.assert_both_rulers` refuses a record carrying one. Read `exit_audit.frozen.*` and `exit_audit.mixed.*`; the unprefixed `exit_audit.residual_max*`, `brief` and `restricted` fields are the **frozen** ruler's and must never share an unlabelled column with a mixed one. (b) The decisive-pass count for §4.2.5 comes from the ruler observer's file, not from the record — and there are **two** counts, components crossing and verdicts changed; the "decisive passes (runs)" column must say which it is. (c) The per-component vectors are in `audit_residual.json` under `rulers.<ruler>.scaled_hex` and `…value_over_scale`. (d) Every ratio quoted from the trial is metric-dependent by §3.6's adoption rule |
| **A55 (harness-smoke)** | the smoke path should exercise one pair under each ruler; `records.assert_both_rulers` will refuse a smoke record whose audit is half-populated |
| **A60 (driver-attempts)** | DR5 is in; `caller.py:1488` is the only predicate call site and DR7 does not touch it. G1's `before` capture for A60 must be taken at this branch's merge commit, and its exclusion set starts at **48** |
| **the orchestrator** | §10 lists what needs a decision |

---

## 10. For the orchestrator

1. **G1's exclusion set is 48 names, not the 45 the brief anticipated.** The brief named
   `predicate_mode` and `exit_audit.mixed`; `campaign_predicate_mode` needed no exclusion at all
   (A47 declared it and it is `frozen` on both sides), and three further names were needed
   (`exit_audit.frozen`, `exit_audit.rulers_note`, `exit_audit.predicate_mode`). Decisions 1, 2 and
   9 of §8 are where that trade sits; each is reversible at the cost of an asymmetric record shape.
2. **The V4 experiment plan's §3.6, §3.9 and §4.2.5 are implementable as written** — no amendment is
   needed from this task. §4.2.5's "decisive passes (runs)" column needs the two-counts distinction
   of §6.4(a) spelled out in its caption; that is A53's row.
3. **Improvement item 5a's "components spanning > 10 ×" table** put
   `power.e_plant_net_electric_pulse_{mj,kwh}` at 50 × on `st_regression` from an ad-hoc read of the
   artifacts. This task measured **54.6 ×** at a run-time state from a committed stage. Whether that
   table should be corrected or left as the ad-hoc estimate it is labelled as is the orchestrator's
   call.
4. **`tfcoil.insstrain`** (improvement list item 11, A57's finding) is in the binding set at 1.27 ×.
   §6.2 states the limit of that observation; it does not resolve item 11.

---

## 11. How to re-run

```bash
PY=/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python
cd arch_surgery/MDA_partitioning_experiment_v4

# the copy's own gates: G0', copy identity, the permitted edit exercised
$PY PROCESS/copy_gates.py all

# where the experiment changed PROCESS, in one view; exit 0 = nothing unexplained
$PY PROCESS_diff.py
$PY PROCESS_diff.py --markdown

# the harness's own checks, including the re-based data check
$PY experiment_runner.py --selfcheck

# G1: capture each side at its own commit, then compare
$PY -m harness.gates switch-neutrality --capture before   # at the branch point
$PY -m harness.gates switch-neutrality --capture after    # at the final driver commit
$PY -m harness.gates switch-neutrality

# GR, which is also G8's part (1)
$PY experiment_runner.py --gate reproduction \
    --lifted-from /home/wrutten/projects/PROCESS_surgery/arch_surgery/MDA_partitioning_experiment_v3/runs/_decks

# G8: 3 reference runs + 24 paired runs, then the comparison
$PY -m harness.gates predicate-mode --capture runs
$PY -m harness.gates predicate-mode

# re-record the predicate module's hunks after an approved edit to it
$PY harness/data_provenance.py record --force
```

Verdict records:
`runs/gates/{frozen_physics,copy_identity,switch_neutrality,reproduction,predicate_mode}/gate.json`.
Per-run ruler observations:
`runs/gates/predicate_mode/<ruler>/<configuration>/<arm>/seed00N/ruler_observation.json`.

---

## 12. Change log

*Append-only.*

| date | commit | what |
|---|---|---|
| 2026-09-10 | — | G1 `before` captured at the branch point `01afc009`, driver byte-identical to `architecture_surgery`'s tip; 6 runs |
| 2026-09-10 | `f8986639` | the `mixed` ruler in `harness/ystate.py`: the `ruler` argument, the two denominators, `RulerError`, and `Residual`'s per-component reporting (`denominator`, `magnitude`, `bound_by`, `value_over_scale`, `binding_components`, `ruler_detail`) |
| 2026-09-10 | `5ac7115b` | the predicate module's identity criterion re-based on recorded hunks; `MODULE_EDITS`; `is_pure_addition`; the `record --force` stage; two new teeth |
| 2026-09-10 | `431fd9f3` | DR5 in the copy: `PROCESS_ARCH_PREDICATE`, the import-time refusal, the readback, the spec-provenance stamp, the guard-versus-module agreement check, the one call site in `caller.py`; two `PermittedEdit` rows; `PROVENANCE.json` regenerated; `PROCESS_diff.py` annotations and summaries |
| 2026-09-10 | `c31874dc` | the harness follows: the registry entry, the re-pointed allowance teeth, the both-ruler exit audit, the preamble stamps, `assert_both_rulers`, the `artifacts.check` row |
| 2026-09-10 | `56e130a1` | gate G8 with the ruler observer, four teeth, and its own exclusion set |
| 2026-09-11 | `9138534b` | G1's five exclusions; the ruler blocks trimmed of their per-component vectors (defect 2 of §8); G8's neutrality summary read GR's real key names; the README's registry section |
| 2026-09-11 | `081279d9` | `assert_ruler` made public so `predicate.cross_residual` uses the one refusal |
| 2026-09-11 | `053300be` | the predicate module's hunks re-recorded after that rename — the data check had already caught it |
| 2026-09-11 | `4528d3e4` | the DR5 annotation string carries no semicolon, which `PROCESS_diff.py --markdown` splits on |
| 2026-09-11 | this commit | the report |

---

## 13. Orchestrator's critical assessment (protocol §5) — 2026-09-11

*Appended by the orchestrating session before merge, against the report at `103fff3e` and the copy
and harness on the same branch. Every gate was re-run by the orchestrator, plus one check the gate
cannot make about itself.*

**Verified independently.** (1) **Gate GR after DR5**, re-run from scratch: 20 of 20 runs, **270 of
270 values identical**, both substitutes PASS, seven teeth tripped. (2) **G8**
(`gates.py predicate-mode`) on the branch's 24 runs: 12 of 12 pairs bit-identical on 0 of 7 564 record
values and 0 of 84 output-file lines; four teeth tripped, the plan's doctored component among them
(5.0e-5 `frozen` versus 5.0e-7 `mixed` at `y = 100 s`; identical below the scale). (3) **The observer
is inert** — the gate infers "no decisive pass" from a wrapper installed on the spec's `residual`, so
I compared G8's six `frozen` runs at seed 1, made *with* the observer, against the committed
reproduction reference, made by the previous revision *without* it: **60 of 60 Phase A values
identical** (`node_calls_single_eval`, `n_model_calls_sweeps`, `exact.objf`, the audit residual hex,
the block-solver totals, `n_attempts`). (4) **G1**: 6 pairs, 0 of 2 341 values, 0 of 51 319 lines,
four teeth; the exclusion set 43 → 48 by the ruler-block fields, and the per-component vectors that
first inflated the excluded count (20 829) are trimmed to 1 277 excluded leaves. (5) **G0′** PASS;
`copy_gates.py all` ALL GATES PASS; `PROCESS_diff.py` exit 0 over six files, 0 unexplained; the
self-check's `data` check accepts `harness/ystate.py` through 22 recorded hunks and its two teeth trip
on an unrecorded edit and on a re-hashed one. (6) Scope: eighteen files; the copy's `models/`, the
repository-root `process/`, `experiment_runner.py` and every committed data file except
`harness/data/PROVENANCE.json` untouched; no conflict with trunk.

**Endorsed.** The two rulers implemented in one module with one `residual`, the `frozen` path
bit-for-bit unchanged and `mixed` never tighter, exactly as §3.6 declares. The independent detector
of the decisive pass instead of the circular inference — and the two events kept apart: 13
evaluations had a component cross τ between rulers, 0 had the crossing component holding the
evaluation open, so 0 verdicts changed and all 12 pairs are identical; reporting the wider event as
the narrower would have hidden a defect, the reverse would have understated the binding set. The
exit audit on both rulers with a refusal of a record carrying one and not both — item 5a's trap (ii)
made structurally hard. The readback of the ruler checked before any pair is concluded. The two
defects the gates caught (the stamp written twice; the per-component vectors in the record) fixed and
reported. The predicate module's identity re-based on recorded hunks rather than relaxed, with teeth.

**Limits I hold it to.** (a) G8's part (3) is two seeds and two arms at δ = 0.10; §3.6's measurement
is 25 seeds, both phases as declared, and belongs to the campaign — nothing here adopts `mixed`; the
campaign default stays `frozen` and the adoption rule is the plan's. (b) The binding set is real and
substantial (48 components; `|y|/s` up to 54.6 on the pulsed-energy fields of `st_regression`), so
the campaign's decisive-pass count will not be zero by construction — the tally must carry both
counts (§4.2.5's caption). (c) The observer doubles the predicate's cost and refuses a campaign run;
its inertness is shown here on the compared fields, not on every field. (d) `tfcoil.insstrain` is in
the binding set at 1.27× and shrinks by 21 % under `mixed`; that does not resolve item 11.

**Rulings and consequences drawn (orchestrator, today).** Improvement item 5a's ad-hoc 50× for
`power.e_plant_net_electric_pulse_{mj,kwh}` on `st_regression` is corrected to the measured 54.6×,
labelled as measured from a committed stage. §4.2.5's "decisive passes" column is split into two
counts in the caption — components crossing τ between rulers, and verdicts changed — A53's row. A52
wires `predicate-mode` beside the other gates and reviews the 48-name exclusion set. A60
(driver-attempts), the last driver change, is dispatched off the merged tip.

**Verdict.** Fit to merge; nothing returned. The trial the plan pre-declared is now something the
harness can run, and its gates have been shown able to fail.
