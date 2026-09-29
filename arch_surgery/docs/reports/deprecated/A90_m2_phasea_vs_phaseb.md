# A90 (m2-phasea-vs-phaseb) — why the partitioned arm's M2 saves nothing per evaluation in phase A and ~15–30 % in phase B

> **Document status** — **MERGED 2026-09-29** at `f2bb2e6e` (`--no-ff`); archived here at merge — folder position records
> lifecycle, not validity (trap T3). Records: `arch_surgery/idf_probe/runs/A90_runs/` — the worktree's whole V4 records tree,
> relocated by the retire script: `A90_runs/block_trace/{optimisation,evaluation,untraced}/` are this task's 52 records,
> `A90_runs/gates/` the gates re-pressed at `1474cd8b` (the **latest relocated records tree**, to seed the next worktree from),
> the rest the seeded copy of A88's tree with the four restored pool records. Every path below reading `runs/…` means this
> location. Orchestrator's assessment in §8; issue I-29 filed from it; harness plan amendment 34. Originally: **OPEN.** Task **A90 (m2-phasea-vs-phaseb)**, branch `A90-m2-phasea-vs-phaseb` (worktree `.claude/worktrees/A90-m2-phasea-vs-phaseb`, seeded with A88 (function-weighted-sweeps)'s records tree), base **`524b69fd`**, tip **`1474cd8b`** — the last commit that touches code or a generated document, and where every verdict this report cites was pressed. Minted provisionally as `m2-probe-binding` and renamed at the user's confirmation; commit `d6c48c88` carries the provisional keyword. Arm names are today's; the campaign records stamp the names of their day and are read through the harness, which translates them (trap T16). **Every number in this report was printed by `arch_surgery/MDA_partitioning_experiment_v4/block_binding.py` at `1474cd8b`** — its `records` subcommand (from the campaign records) or its `trace` subcommand (from this task's traced runs) — or read from a gate verdict record pressed at that commit, or from a committed data file named where it is used. None was typed from inspection. Two figures that first were typed from inspection, in a message to the orchestrator, are corrected in the change log.

---

## 1. Verdict

**M2 binds the flat loop when every module is disturbed, and only then.** The flat loop sweeps every model node until the whole coupling state is within the tolerance τ, so each evaluation costs as many sweeps as its *slowest-settling* module needs. The partitioned arm solves each module as its own block, so its M2 block costs only what M2 itself needs.

- **In phase A** (one evaluation from a coupling state displaced by δ = 0.10 everywhere) every module is disturbed and M2 is the slowest to settle, so the flat loop's count *is* M2's count, and the partitioned M2 block needs the same number.
- **In phase B** 93–95 % of evaluations are the optimiser's finite-difference probes (`paper_tables.md`, "FD share"), each moving **one** design variable a little from a nearly converged state. A probe on a plasma-composition or confinement variable disturbs M1 and leaves M2 within τ after one or two sweeps; the flat loop keeps sweeping M2 until M1 settles, the partitioned arm does not. A probe on a geometry or magnet variable disturbs M2 most, and there M2 binds and saves nothing.

The phase-B per-evaluation ratio is therefore fixed by the optimiser's probe pattern — which variables exist and which module each one disturbs — and that pattern repeats every iteration. This is why the ratio is the same on every seed and for every run length.

**The four predictions registered with the task, all confirmed.** n = **3 seeds per configuration and arm** (the first three of the paper's seed set in phase B, the first three displaced seeds in phase A); every traced run reproduces its campaign run exactly (§3.1).

| | prediction | verdict | the evidence, with its population |
|---|---|---|---|
| (a) | in the flat arm, M2 binds only part of the optimiser's evaluations | **confirmed** | M2 binds `B1` on **1374/1980** evaluations (`tok`) and **3552/5250** (`lad`); `B0` on **2528/6600** (`st`). Per (design variable, probe sign) M2 binds on none or on all of the paired probes on **42/42** pairs (`tok`), **36/40** (`lad`), **28/28** (`st`, 90 pairs only, see (b)) |
| (b) | where M2 does not bind, the partitioned M2 block takes 1–2 sweeps | **confirmed, and exact** | on those evaluations `B2`'s M2 took 1 sweep 426 times and 2 sweeps 180 times (`tok`, n = 606), 1061 / 637 (`lad`, n = 1698), 36 / 15 (`st`, n = 51). Evaluation by evaluation, `B2`'s M2 sweeps **equal M2's own settle count in the flat loop** on **1980/1980** (`tok`) and **5250/5250** (`lad`) evaluations — every evaluation, because `B1` and `B2` take the same optimiser path — and on **90/90** on `st`, where `B0` and `B2` diverge and only the bit-identical pairs of **6030** can be paired |
| (c) | weighting the per-probe counts by the probe pattern reproduces the ratio as a count | **confirmed exactly on `tok`/`lad`; statistically on `st`** | from the flat trace alone, Σ(M2 settle count) / Σ(flat sweeps) = **5449/6304 = 0.8644** (`tok`) and **14251/16638 = 0.8565** (`lad`), equal to the observed `B2`/`B1` M2 sweeps per evaluation in the campaign records of the same seeds (**0.8644**, **0.8565**). **100 %** of the saving comes from evaluations where M2 does not bind. On `st` the prediction from `B0`'s trace is **0.6982** against **0.6809** observed: the two arms' paths diverge there, so it is a prediction over a different set of evaluations, not a pairing |
| (d) | in phase A, M2 binds the flat loop on (nearly) every evaluation | **confirmed** | against the flat arm with the same node set as `A2`'s blocks: M2 binds `A1` on **3/3** (`tok`, sole binder on 2) and **3/3** (`lad`, sole on 3), `A0` on **3/3** on `st` (sole). With the burn time still in the loop (`A0` on the pulsed configurations) the binders are joint: all of FF, M1, M2, M3 on 2/3 (`tok`) and 3/3 (`lad`) |

**For the paper.** The per-module phase-B ratio for M2 (0.87 / 0.59 / 0.67 in `paper_tables.md`) should not be read as "the partition makes M2 cheaper to converge". It is the partition *no longer charging M2 for the other modules' settling*. On the probes that disturb M2 most, the partitioned M2 costs exactly what the flat loop costs. The phase-A statement "M2 binds" holds for a uniformly displaced entry and not for the optimiser's single-variable probes.

---

## 2. The observation

**The terms.** The phase-A arms are one `call_models` evaluation each:
- `AR` is PROCESS as shipped.
- `A0` is the flat loop, stopping on the coupling state at τ.
- `A1` is `A0` with the burn time taken out of the loop.
- `A2` is the partitioned arm: blocks M1 → M2 → M3, each iterated to τ.

The phase-B arms `BR`, `B0`, `B1` and `B2` are the same four arms inside a full optimisation. `B1` and `B2` hand the burn time to the optimiser as a design variable.

The configurations are `tok` (`large_tokamak_nof`), `lad` (`low_aspect_ratio_DEMO`) and `st` (`st_regression`, steady state; no `A1`/`B1`).

**The quantity.** *M2 sweeps per evaluation* is the solve phase's count per `call_models`: `block_loop_totals.sweeps_by_block` (M2 in `B2`; the one `FLAT` block in a flat arm, which sweeps every in-loop node, M2's included) over `block_loop_totals.n_call_models`. The paper's phase-B cells are the whole-run census less the exit audit. They equal this solve-phase count plus the output loop's sweeps on **198/198** runs of the paper's seed set (0 mismatches of 88 / 44 / 66).

**Table 1 — the paper's `B2`/`B0` M2 ratio, decomposed exactly.** Over the paper's seed set (n = 22 / 11 / 22 seeds on which every arm reached an accepted optimum). Each factor is a ratio of pooled sums over those seeds, and the arm pair is named in the row. The product identity holds with residual 0 on every configuration.

| factor | arm pair | `tok` | `lad` | `st` |
|---|---|---:|---:|---:|
| M2 sweeps per run (the paper's cell ratio, solve phase) | `B2`/`B0` | 0.8699 | 0.5931 | 0.6682 |
| = M2 sweeps per evaluation | `B2`/`B0` | 0.8356 | 0.8114 | 0.7025 |
| × evaluations per run | `B2`/`B0` | 1.0411 | 0.7309 | 0.9512 |
| per evaluation, the burn-time ownership rung | `B1`/`B0` | 0.9679 | 0.9465 | — |
| per evaluation, the partition | `B2`/`B1` | 0.8633 | 0.8572 | — |

The partition's per-evaluation saving is about 14 % on both pulsed configurations. It does not come from the evaluation count: on `tok`, `B2` makes 4 % *more* evaluations than `B0`. In phase A the same comparison reads 1.0078 (`tok`) and 0.9919 (`lad`) against `A1`, and 1.0000 (`st`) against `A0`. `A2`'s M2 sweeps equal the flat loop's on **24/25, 24/25, 25/25** displaced runs, and M2 is the (joint-)largest of `A2`'s blocks on 25/25 on every configuration.

**Two properties of the phase-B ratio that point at the mechanism** (`records`, paper seed set):
- **`B1` and `B2` follow the same optimiser path.** They make the same number of evaluations and iterations on 22/22 (`tok`) and 11/11 (`lad`) seeds. The per-evaluation entry value of `p_plant_electric_net_mw` agrees to ≤ 7.5e-11 relative, and is bit-identical on 12000/14080 and 11145/18858 evaluations. So the search direction is not the cause. On `st`, `B0` and `B2` diverge: equal counts on only 14/22 seeds.
- **The per-seed ratio is tight and independent of run length.**

| | `tok`, `B2`/`B1` | `lad`, `B2`/`B1` | `st`, `B2`/`B0` |
|---|---:|---:|---:|
| median over seeds | 0.8644 | 0.8575 | 0.7229 |
| [min, max] | [0.8522, 0.8646] | [0.8560, 0.8586] | [0.6678, 0.7281] |
| shorter half of runs by evaluations: median | 0.8641 (572–660) | 0.8578 (798–1134) | 0.7230 (570–810) |
| longer half: median | 0.8644 (660–748) | 0.8574 (1218–5418) | 0.7026 (990–4290) |

A `lad` run of 800 evaluations and one of 5400 give the same ratio. A saving that depended on where the optimiser is would drift with the run; one set by the probe pattern would not.

---

## 3. The cause, with the evidence

### 3.1 The instrument and the population

**The trace.** `PROCESS_ARCH_BLOCK_TRACE` is a new switch in the experiment's copy of the driver (§5). It observes only; with it unset, nothing runs. It writes one line per `call_models`, containing:
- **The evaluation kind**, taken from the optimiser's own call site in `evaluators.py`: a function evaluation, a gradient probe with its column and sign, or the reconcile call. It is not inferred from position in the sequence.
- **The design vector**, as exact hex floats.
- **For each block, its sweep count**, and after every sweep the maximum scaled step of each module's own components and whether that module would still fail the test at τ.

The modules' components are the committed write sets. They partition the coupling state with no overlap and full cover (on `tok`, FF 119, M1 258, M2 240, M3 221 and PULSE 2 components, from the committed `harness/data/write_sets_large_tokamak_nof.json`).

**The binding block (the definition used throughout).** After each flat sweep, a module is *open* if any of its own components would fail the test at τ. Let L_m be the last sweep after which module m was open (0 if never). The flat loop stops at k = 1 + max L_m. This identity held on **27124/27124** flat optimisation-phase evaluations and **15/15** flat evaluation-phase runs. The **binding** modules are those with L_m = max L, the last to reach τ. **M2's settle count** is L_M2 + 1.

**The runs.** All are run kind `gate`, under `runs/block_trace/`. Each is the campaign's own job with only its directory, run kind and `override_env` (which carries the trace path) changed.
- **Phase B:** `tok` `B0`/`B1`/`B2` × seeds 0, 1, 2; `lad` `B0`/`B1`/`B2` × seeds 0, 1, 5 (seeds 2–4 are not in the paper's set); `st` `B0`/`B2` × seeds 0, 1, 2. That is 24 runs.
- **Phase A:** `tok` and `lad` `A0`/`A1`/`A2`, `st` `A0`/`A2`, × displaced seeds 1, 2, 3. That is 24 runs.
- **Stop rule:** any run that did not reproduce its campaign run exactly would end the press.
- **Result:** **48/48** reproduce their campaign run exactly on status, `n_call_models`, `sweeps_by_block`, `n_solver_iterations`, `norm_objf` (hex) and `node_calls_solve_phase`. Every trace has one line per evaluation, and its per-block sweeps sum to the record's.
- **The trace changes nothing it measures.** The driver copy is byte-identical between the campaign commit `57dc0c14` and the last pre-change commit `d6c48c88`, and the traced runs reproduce the campaign bit for bit.

### 3.2 (a) Which module binds depends on the probe, not on the phase of the run

**Table 2 — M2's binding share in the flat arm, by evaluation kind** (3 seeds per configuration).

| configuration, flat arm | function evaluations | gradient probes | reconcile calls | all |
|---|---:|---:|---:|---:|
| `tok`, `B1` | 24/45 | 1350/1890 | 0/45 | 1374/1980 |
| `lad`, `B1` | 64/125 | 3488/5000 | 0/125 | 3552/5250 |
| `st`, `B0` | 95/220 | 2433/6160 | 0/220 | 2528/6600 |
| `tok`, `B0` (burn time in the loop) | 21/47 | 1281/1880 | 44/47 | 1346/1974 |
| `lad`, `B0` (burn time in the loop) | 137/283 | 6499/10754 | 0/283 | 6636/11320 |

**By design variable, the binder is almost a constant of the probe.** Taking each gradient probe of `B1` paired with its `B2` counterpart (§3.3), and grouping by (design variable, sign), M2 binds on none or on all of that group's probes on **42/42** groups (`tok`), **36/40** (`lad`) and **28/28** (`st`, on the 90 pairable evaluations).

**Probes on which M2 never binds** (`tok`, each 45 probes; `B2` M2 sweeps / flat sweeps in brackets):
- `hfact` + (0.333) and − (0.500)
- `f_nd_alpha_thermal_electron` − (0.333) and + (0.667)
- `f_nd_impurity_electrons(13)` − (0.333) and + (0.667)
- `f_c_plasma_non_inductive` − (0.333)
- `nd_plasma_electrons_vol_avg` − (0.333)
- `temp_plasma_electron_vol_avg_kev` − (0.333)
- `t_plant_pulse_burn` − (0.500)
- `f_a_cs_turn_steel` + (0.667)
- `t_tf_superconductor_quench` + (0.667)

In `B1` these are bound by M1: `hfact` by M1 alone on 88 of 90 probes and by FF and M1 on 2, `f_nd_alpha_thermal_electron` and `f_nd_impurity_electrons(13)` by M1 alone on 90 of 90.

**Probes on which M2 binds on every probe** (ratio 1.000), both signs:
- `b_plasma_toroidal_on_axis`, `rmajor`, `beta_total_vol_avg`, `q95`
- `dr_bore`, `dr_cs`, `dr_tf_nose_case`, `dr_tf_wp_with_insulation`
- `dx_tf_turn_steel`, `c_tf_turn`, `f_a_tf_turn_cable_copper`, `j_cs_flat_top_end`

`lad` shows the same partition of variables.

**Several variables split by sign** (on `tok`; on `lad`, `t_plant_pulse_burn` binds M2 on neither sign). `nd_plasma_electrons_vol_avg`, `temp_plasma_electron_vol_avg_kev`, `f_c_plasma_non_inductive`, `f_a_cs_turn_steel`, `t_tf_superconductor_quench` and `t_plant_pulse_burn` each bind M2 on one sign and not the other, on every probe. The trace does not say why: it records which module is open, not which model branch a probe crosses.

**The four `lad` groups where M2 binds on some probes but not all** are findings about those probes, not noise:

| `lad`, (design variable, sign) | probes | M2 binds | `B2` M2 / flat sweeps |
|---|---:|---:|---:|
| `beta_total_vol_avg` + | 125 | 0.960 | 0.987 |
| `nd_plasma_electrons_vol_avg` + | 125 | 0.960 | 0.987 |
| `beta_total_vol_avg` − | 125 | 0.976 | 0.992 |
| `t_tf_superconductor_quench` − | 125 | 0.008 | 0.668 |

**The reconcile call.** This is the optimiser's re-evaluation at the iterate after its gradient loop. It is never bound by M2 once the burn time is out of the loop (0/45, 0/125, 0/220). With it in the loop (`B0` on `tok`) all four modules bind jointly (44/47): the burn-time coupling through the pulse model ties every module together. That is the ownership rung `B0` → `B1`, not the partition.

### 3.3 (b) Where M2 does not bind, the partitioned M2 stops as soon as its own components settle

**Pairing.** An evaluation of the flat reference is paired with the partitioned arm's evaluation of the same index when the two runs take the same optimiser path. That means the same number of evaluations, the same optimiser label on every pair, and design vectors within 1e-8 relative. All six `tok`/`lad` seeds qualify (largest difference 1.3e-9; 1188/1980 and 2310/5250 pairs bit-identical), so every evaluation pairs. On `st` none of the three seeds qualifies (largest difference 2.7e-7 on seed 0, where the counts agree; the others differ in count), so only the **90** of **6030** pairs at a bit-identical design vector are used.

**Table 3 — the flat reference against `B2`, evaluation by evaluation.**

| configuration (pairs) | group | n | flat sweeps (mean) | `B2` M2 sweeps (mean) | ratio | share of the saving | `B2` M2 sweeps: histogram |
|---|---|---:|---:|---:|---:|---:|---|
| `tok`, `B1`/`B2` (1980) | M2 binds the flat loop | 1374 | 3.394 | 3.394 | 1.0000 | 0 | 2: 315, 3: 363, 4: 540, 5: 152, 6: 4 |
| | M2 does not bind | 606 | 2.708 | 1.297 | 0.4790 | 1.0000 | 1: 426, 2: 180 |
| `lad`, `B1`/`B2` (5250) | M2 binds | 3552 | 3.355 | 3.355 | 1.0000 | 0 | 2: 501, 3: 1302, 4: 1737, 5: 12 |
| | M2 does not bind | 1698 | 2.781 | 1.375 | 0.4945 | 1.0000 | 1: 1061, 2: 637 |
| `st`, `B0`/`B2` (90 of 6030) | M2 binds | 39 | 4.333 | 4.333 | 1.0000 | 0 | 2: 3, 4: 23, 5: 10, 7: 3 |
| | M2 does not bind | 51 | 3.118 | 1.294 | 0.4151 | 1.0000 | 1: 36, 2: 15 |

**The identity.** On every paired evaluation, `B2`'s M2 sweeps equal M2's settle count in the flat loop, L_M2 + 1: **1980/1980** (`tok`), **5250/5250** (`lad`), **90/90** (`st`). Where M2 binds, the settle count *is* the flat count, hence the ratio of exactly 1.0000.

**This identity is empirical, not true by construction.** In the flat loop M2's nodes run in every sweep while M1's and M3's outputs are still moving. In `B2`, M2 iterates only after M1 has reached τ and before M3 runs. The two loops therefore present M2 with different inputs on every sweep but the last, and nothing in their definitions makes the counts equal.

The trace shows two things:
- Where M2 does not bind, M2's own components stayed within τ while another module was still open. That is what not binding means.
- The number of sweeps M2 needed to get there was the same in both arrangements.

A reading consistent with both is that M2's settling on these probes is insensitive to what M1 and M3 do in the sweeps after M2's inputs first move. The trace records per-module residuals, not the sensitivity of one module's components to another's, so it cannot test that reading. The identity is reported as an observation.

### 3.4 (c) The probe pattern accounts for the whole ratio

Because the identity holds on every evaluation, the partitioned arm's per-evaluation ratio can be computed from a flat run's trace alone, as Σ(M2 settle count) / Σ(flat sweeps):

| prediction from the trace of | `tok` | observed (campaign records, same seeds) | `lad` | observed | `st` | observed |
|---|---:|---:|---:|---:|---:|---:|
| `B1` (same path as `B2`) | 5449/6304 = **0.8644** | `B2`/`B1` **0.8644** | 14251/16638 = **0.8565** | `B2`/`B1` **0.8565** | — | — |
| `B0` | 5611/6503 = 0.8628 | `B2`/`B0` 0.8354 | 31853/38157 = 0.8348 | `B2`/`B0` 0.8053 | 16210/23218 = 0.6982 | `B2`/`B0` 0.6809 |

The prediction from `B1` reproduces the observed ratio to four decimals: it is the identity summed. The prediction from `B0` does not, and should not:
- `B0` → `B2` also changes who owns the burn time, which moves M2's settle count as well (Table 1, `B1`/`B0` row).
- On `st`, `B0` and `B2` evaluate different points.

The `st` prediction (0.6982 against 0.6809) is a statement about the same kind of probe on a different path, not a pairing.

### 3.5 (d) Phase A: every module is disturbed, and M2 is the slowest

| configuration, flat arm | runs | M2 binds | M2 sole binder | binders |
|---|---:|---:|---:|---|
| `tok`, `A1` | 3 | 3 | 2 | M2 (2); FF+M2+M3+PULSE (1) |
| `lad`, `A1` | 3 | 3 | 3 | M2 (3) |
| `st`, `A0` | 3 | 3 | 3 | M2 (3) |
| `tok`, `A0` (burn time in the loop) | 3 | 2 | 0 | FF+M1+M2+M3 (2); FF+M1+M3 (1) |
| `lad`, `A0` (burn time in the loop) | 3 | 3 | 0 | FF+M1+M2+M3 (3) |

With the burn time out of the loop, M2 is among the last modules to settle on each of the three displaced runs of every configuration (sole binder on 2 of 3 on `tok`, 3 of 3 on `lad` and `st`). That is why `A2`'s M2 block, which needs M2's settle count, costs what the flat loop costs (24/25, 24/25, 25/25 over the campaign's 25 seeds, §2). With the burn time in the loop, the pulse coupling holds every module open together. That is the `A0` → `A1` rung, and it is why the paper's phase-A `A2`/`A0` M2 ratio on `tok` (0.93) differs from the `A2`/`A1` one (1.0078).

For context, not evidence: A91 (block-sweep-timing, merged `73793603`) measured the wall-clock cost of one sweep of each block. Nothing in this report's verdict rests on a timing.

---

## 4. What this means

1. **The partition's per-evaluation saving on M2 is a scheduling effect, not a convergence effect.** No probe makes M2 cheaper to converge than it is inside the flat loop. The saving is the flat loop's sweeps of M2 while *another* module settles, which the partitioned arm does not pay. On `tok` and `lad` the per-evaluation ratio is 0.8644 and 0.8565, and all of the saving comes from the evaluations M2 does not bind: 606 of 1980 and 1698 of 5250.
2. **The size of the saving is a property of the configuration's design variables.** It depends on how many of them disturb M2 less than M1 or M3, weighted by how often the optimiser probes each. Since every probe is repeated every iteration, it is the same for every seed and every run length. A configuration whose design variables are mostly geometry and magnet variables would show less; one dominated by plasma-composition variables would show more.
3. **Phase A cannot show it.** A uniformly displaced entry disturbs every module, so the slowest module binds the flat loop on every run, and that module's block costs what the flat loop costs. Phase A's "M2 binds" is correct for its entry and says nothing about the optimiser's probes.

---

## 5. Autonomous decisions, with reversal paths

| decision | why | reversal |
|---|---|---|
| **The instrument goes into the copy's driver** (`module_solve.py`, `caller.py`, `evaluators.py`), registered as permitted edits in `copy_gates.PERMITTED_EDIT_FILES`, with `evaluators.py` a new permitted file. The switch is registered in `switches.py` as cleared and never composed | the evaluation kind has to come from the optimiser's call site (orchestrator's rule 4); per-module residuals exist only inside the block loop | remove the three hunks and the registry rows, regenerate `PROVENANCE.json` with `--task`, re-press G1 and `copy_identity` |
| **Traced runs pass the switch in `Job.override_env`** (the `gate_predicate_mode` precedent), under `runs/block_trace/`, run kind `gate` | a distinct job identity from every campaign and gate job; no new `Job` field | delete `runs/block_trace/` |
| **The `PROVENANCE.json` generator keeps `copy_date`** and records each regeneration in `permitted_edits_updated`, with `--task` required and `--copy-date` as a recorded correction; `copy_date` restored to 2026-09-10 | regenerations had moved it: 2026-09-10 (A46, `2eec5fee`) → 09-11 (A60, `2c097267`) → 09-14 (A73, `7d333677`) → 09-29 (this task's first regeneration). Records stamp `process_copy_provenance.copy_date`; G1 excludes it by name; the reproduction gate GR's 18 compared fields do not include it, so GR stays `--resume` | revert `carry_history` in `copy_gates.py` |
| **`copy_identity` checks the recorded permitted-file list against the committed `PERMITTED_EDIT_FILES`**, with one changed-elsewhere tooth per permitted file and a provenance-only-blessing tooth; the harness registers teeth keyed by (tooth, target) | the orchestrator asked that the new permitted file be covered by a tooth; in doing so it emerged that the harness had cached teeth by name alone, so the per-file teeth overwrote one another | revert the two hunks in `copy_gates.py` and `harness/gates/gates.py` |
| **The pairing rule**: same count, same labels, design vectors within `SAME_PATH_REL = 1e-8`; otherwise bit-identical pairs only | `B1`/`B2` agree to ~1e-11, not bitwise; bit-identity alone kept 60 % / 44 % of pairs, a biased subset (a first version did that) | change `SAME_PATH_REL` and re-run `trace` |
| **Population 3 seeds** per configuration and arm | the orchestrator's ruling on the user's "a few seeds each"; no verdict turns on the per-seed spread, because the identity in (b) holds on every evaluation of every seed | extend `N_SEEDS` with the user's approval |

---

## 6. Gates (verdict records under the worktree's `runs/gates/`, pressed `--resume` at `1474cd8b`)

| gate | verdict | teeth | what it read |
|---|---|---:|---|
| `switch_neutrality` (G1) | PASS | 9/9 | before capture at `d6c48c88` (the last pre-change commit), after at `3983fb0c`: **0/3980** record values and **0/51319** output-file lines differ. Nothing under `PROCESS/` or `harness/` changed after `3983fb0c`. G1 runs only the arms with every switch unset (`AR`, `BR`), which exercise the `evaluators.py` hook but not the block-schedule hook; that path is covered by the 4 untraced controls (§7), which reproduce their campaign runs exactly |
| `copy_identity` | PASS | 12/12 | 224 files against the source commit `f2dc9243`; 8 permitted-edit files. Teeth: 3 generic, 8 per-file, 1 provenance-only (was 4) |
| `edit_behaviour` | PASS | 1/1 | — |
| `g0prime` (physics freeze) | PASS | 4/4 | 77 model files against `c0ae5b28` |

**A finding on the harness.** At base, `copy_identity`'s verdict carried **4** teeth, one of them a single changed-elsewhere tooth on whichever permitted file sorted last: `_copy_identity_teeth` cached `run_teeth` records by tooth name. Keyed by (tooth, target), the verdict carries **12**. The report's gate-table caption (in `harness/gates/registry.py`) now says 8 permitted driver-edit files instead of 7; `EXPERIMENT_REPORT.md`'s gate table needs a re-render at merge.

**Stamp survey** (`run_stamp_survey.py`) against the tree as seeded:
- 1102 → 1154 records; 0 disappeared.
- Changed: the 12 G1 capture records.
- New: 52 — 24 optimisation and 24 evaluation runs at `1faf43fc`, and 4 controls at `3983fb0c`.

---

## 7. Change log (append-only)

- **2026-09-29** — registered as an investigative task; minted provisionally A90 (m2-probe-binding), worktree seeded with A88's records tree.
- **2026-09-29** — step 1, before any run: `block_binding.py records` (`d6c48c88`) re-derived the preliminary ratios from the campaign records. Keyword renamed to m2-phasea-vs-phaseb at the user's confirmation; worktree moved.
- **2026-09-29** — instrumentation `fc216937`; `PROVENANCE.json` history and `copy_date` restore `5d7a6788`; harness registers every `copy_identity` tooth `5d2e2f09`; per-module split vectorised and `trace-runs`/`trace` `3983fb0c`. **Wrong count in two commit messages:** `5d7a6788` and `5d2e2f09` say 13 `copy_identity` teeth; the gate record says **12** (3 + 8 + 1). History is not rewritten.
- **2026-09-29** — **process fault 1.** I pressed the 4 untraced controls in the same turn I sent the orchestrator the planned population, before its reply. They ran on 3 workers for ~70 s, concurrently with A91 (block-sweep-timing)'s wall-clock measurements. A91 was told to treat that window as contended and re-take any overlapping repetition.
- **2026-09-29** — **process fault 2 (issue I-29).** The 4 controls did not land in `runs/block_trace/untraced/`: they re-made four seeded shared-pool gate records in place, each moving from `0677a9b3` to `3983fb0c`:
  - `gates/_runs/B_B1_large_tokamak_nof_seed000_gate_ba6438f1ed8876f3`
  - `gates/_runs/B_B3_large_tokamak_nof_seed000_gate_7bd638903b73a796`
  - `gates/_runs/B_B3_low_aspect_ratio_DEMO_seed000_gate_72addc6ba87c0522`
  - `gates/_runs/B_B3_st_regression_seed000_gate_e556e4694af1443e`

  **Cause:** a job's directory is not an identity field, so an untraced control (the campaign job with run kind `gate` and an empty `override_env`) has the digest of the gate pool's own job. `pool.directory_for` resolves by digest before the named directory, and `pool.run` without `--resume` removed and re-made the record there.

  **Found by** the mid-task stamp survey. **Restored:** the orchestrator staged the originals from A88's records tree. I moved the four re-made records to the controls' named directories, `runs/block_trace/untraced/<configuration>/<arm>/seed000`, not to directories named after the pool records, so the pool resolves each control unambiguously by its first rule. I moved the originals back under their own names and verified each byte-identical (`diff -rq`) to `arch_surgery/idf_probe/runs/A88_runs/gates/_runs/<same name>`, stamped `0677a9b3`. No gate was re-pressed over them.

  The relocated control records keep the `outdir` field they were made with, which names the pool directory. It is left as made. They reproduce their campaign runs exactly on the six fields, with no trace file, and are this task's control result: the hooks off on the block-schedule path. `trace-runs` now refuses any job the pool would resolve anywhere but its named directory, and refuses to re-make the controls without `--resume` (`32eadcb6`, docstring `1faf43fc`). The harness fix is I-29's, a later task.
- **2026-09-29** — population restricted to 3 seeds per configuration and arm at the orchestrator's ruling (`8a71591f`); pressed after A91 finished: 48/48 reproduce their campaign runs.
- **2026-09-29** — analysis `024ae768`: the pairing rule replaced bit-identical-only pairing, which had kept a biased 60 % / 44 % / 1.5 % of pairs; per-evaluation identity; prediction from the flat trace; probe-sign split. **Two figures first sent to the orchestrator from inspection were wrong:** "25,128 flat evaluations" and "0 or 1 on 38/42 pairs on `tok`". Corrected to the script's 27124/27124 and 42/42 (36/40 on `lad`), and printed by the script from `9f284a0f`.
- **2026-09-29** — gates re-pressed `--resume` at `9f284a0f`; `records` and `trace` re-run there; report drafted.
- **2026-09-29** — checking the draft against its own rule found figures I had summed or derived by hand: Table 2's "all" column, "14 %" and "31–32 %", `hfact`'s binders. The script now prints them (`1474cd8b`); the write-set sizes are cited from their committed file. Gates re-pressed `--resume`, and `records`/`trace` re-run, at `1474cd8b`; `records`' output is byte-identical to its run at `9f284a0f`.

## 8. Orchestrator's critical assessment (protocol §5) — 2026-09-29

*By the orchestrating session (`process-surgery-65`). The task was executed by session `process-surgery-7d`, which registered, was minted A90, and ended after committing the report. Verified by checks the task did not make: an independent recount over the raw trace lines, one run's reproduction fields read directly against its campaign record, the four gate records read from disk, and the stamp survey. Read-only except for the gate-table re-render below.*

**Scope.** 11 files against `524b69fd`: three driver-copy files (`caller.py`, `module_solve.py`, `evaluators.py` — an observation-only hook; with `PROCESS_ARCH_BLOCK_TRACE` unset the hunks set a `None` and take no branch, which G1 measures), `copy_gates.py` and `PROVENANCE.json` (the permitted-edit list gains `evaluators.py`; the copy date restored to 2026-09-10 and the regeneration recorded as history), `switches.py` (registered, never composed), `gates.py` / `registry.py` (the copy-identity teeth keyed by tooth *and* target), `block_binding.py`, the harness README, and the report. Nothing under `process/models/`. The user confirmed the mint and renamed the keyword; the first commit `d6c48c88` carries the provisional one.

**Checks made here.**

1. **Prediction (c) and identity (b) recounted from the raw trace lines** (`block_trace.jsonl`, `large_tokamak_nof`, `B1` and `B2`, seeds 0–2, 1980 evaluations), applying §3.1's definition myself: Σ(L_M2 + 1) / Σ k = 5449 / 6304 = 0.8644 from `B1`'s trace alone; Σ `B2` M2 sweeps / Σ k = 5449 / 6304 — the same integers; `B2`'s M2 sweeps = L_M2 + 1 on 1980/1980; k = 1 + max L on 1980/1980. The binding share reproduces as 1374/1980 = 0.6939 once the 21 evaluations that entered converged (max L = 0, nothing binds) are excluded as the definition says; counted as "M2 among the binders" they would read 1395 — the definition's exclusion is stated in §3.1 and is the right one.
2. **Reproduction of a traced run against its campaign record**, read directly from the two `metrics.json` (`B1` `large_tokamak_nof` seed 0, traced at `1faf43fc` vs campaign at `57dc0c14`): status, `n_solver_iterations` 8, `node_calls_solve_phase` 44 142, `norm_objf` `0x1.9999999a4496cp+0`, `sqsumsq`, the accepted design vector — identical. (The record's own `n_call_models` field is `None` in both; the trace's 661 lines are the evaluation count the report uses.)
3. **Gate records at `1474cd8b`**: `switch_neutrality` PASS, 9/9 teeth, 3 980 values and 51 319 output-file lines compared, 0 differing, captures `d6c48c88 → 3983fb0c`; `copy_identity` PASS, 12/12 teeth, 224 files compared, 8 mismatched (the eight permitted files); `edit_behaviour` PASS 1/1; `g0prime` PASS 4/4.
4. **Stamp survey** over `runs/block_trace/`: 24 optimisation + 24 evaluation records at `1faf43fc`, 4 controls at `3983fb0c`, all `ok`, all run kind `gate`; the four restored pool records at `0677a9b3`.
5. **The gate table.** The report's Appendix D gate table was rendered from a stage record older than the gate verdicts (the runner's check refused it, as designed). I re-ran `--measure gate_table --resume` and `--plan-tables write` at `1474cd8b`: three lines change, all in the gate table (copy_identity's caption and teeth, G1's straddle, 168 → 176 teeth); the companion file IDENTICAL; `report_cells_preserved.py --base 524b69fd` 21 296/21 296 cells preserved with the gate table's own two rows the only differing ones. Committed on the branch as `a9c4fad1` by me, since the task's session had ended.

**Findings on the report.** §3.3 states the identity as empirical with the reading it cannot test, as required. The two process faults, the I-29 restore with the four directory names, the corrected figures and the 13 → 12 tooth count are in the change log with commits. One reading to carry into the paper carefully: "M2 saves ~15–30 % in phase B" is a per-evaluation statement over the paired population; the campaign-level M2 ratio (0.83 / 0.81 / 0.70) also contains the evaluation-count factor, which the report's §2 separates — the paper should quote both factors.

**Verdict: merge.** Carried forward: I-29 (harness fix, a later task); the copy-identity tooth fix is a harness improvement recorded here and in the gate table; the finding itself — M2 binds only on the probes that disturb it — is context for V5 item 2 and for the paper's mechanism section.
