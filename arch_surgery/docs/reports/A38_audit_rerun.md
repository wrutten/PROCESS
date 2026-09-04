# A38 (audit-rerun) — V2's Phase A re-run under the corrected similarity audit: the check still fails, on the carrier alone; the correction is measured, gated with teeth, and the re-run reproduces V2 bit for bit

> **Document status** — **CURRENT · TASK REPORT, open.** Written by task A38 (audit-rerun),
> 2026-09-04, on branch `A38-audit-rerun`, branched from `architecture_surgery` at `a4446bed`
> (the mint commit), experiment base commit `c0ae5b28`. **No file under `process/` was
> touched.** Archived to `deprecated/` when the task merges and authoritative there (trap T3).
> Nothing is pushed.

| | |
|---|---|
| **Task** | V3 improvement-list item 4 / V3 plan §3.1 arm A1u, §4.1, gate G4: re-run V2's Phase A design unchanged under a similarity audit restricted to the components the solve phase actually writes, since V2's whole-state audit charged the block arm for δ-perturbed outputs of post-solve nodes it never executes (75 of 75 V2 audit maxima). V2's records held no per-component residual vector, so this is a re-run, not a re-tally |
| **Verdict** | **The corrected similarity criterion (F = 10 at median and p90) still FAILS on all three decks, by five to six orders of magnitude, on the carrier term alone** — exactly the pre-declared expectation. The block arm's restricted deficit is a few times 1e-4 scaled against the flat arm's 1e-9 or exact zero. On `large_tokamak_nof` the restricted maximum is one of A35's two closed images of the first-wall pair in **25 of 25** runs; on `st_regression` 17 of 25 are A35's image and the other 8 are a second linear image of the pair, gain 47.0 on the inboard displacement, constant across seeds to 2e-11; on `low_aspect_ratio_DEMO`, the deck A35 never traced, both A35 images hold at the same coefficients to 1e-11 in 25 of 25 runs, but the restricted maximum in 21 of 25 is the TF-coil superconductor mass, **which is not one linear image of the pair** (two-coefficient fit residual median 7 %, max 92 %) — the one open term this task leaves |
| **Reproduction of V2** | **150 of 150** seed runs bit-identical to V2's records (node calls, sweeps, block sweeps, outer passes, objective hex, whole-state audit hex, and the full 840 / 846 / 827-component exit state); the whole-state audit distributions reproduce V2's tally values bit for bit; the count ratios reproduce **0.5217 / 0.5680 / 0.5016** exactly |
| **Script** | [`arch_surgery/idf_probe/a38_audit_rerun.py`](../../idf_probe/a38_audit_rerun.py) — stages `preflight` / `smoke` / `campaign` / `tally` / `all`; committed at `4ea93408` before any run, campaign executed at `9fcedc92`, tally-only refinements through `ca736947`. The additive runner change is in [`arch_surgery/idf_probe/v2_eval_one.py`](../../idf_probe/v2_eval_one.py) (`--audit-exclude-postsolve`; `audit_residual.json` written beside every record) |
| **Runs** | **171 fresh-subprocess single-MDA-evaluation runs, 171 of 171 `status: ok`**, 57 per deck (1 reference, 2 entry-gate, 1 warm-gate, 3 restricted-teeth, 50 seed runs), W = 3, every record stamped `9fcedc92 dirty=False x171`. Plus 11 smoke runs on `st_regression` (machinery only) and two aborted campaign attempts whose runs are discarded and cited nowhere (§6) |
| **Environment** | `PROCESS_surgery_env`; `PYTHONPATH` pinned to this worktree per subprocess; exact tree asserted in-process (traps T6 / T10); a26 artifacts; τ = 1e-6; δ = 0.10; runs under `arch_surgery/idf_probe/runs/a38/` untracked; V2's records read read-only from the main checkout |
| **Date** | 2026-09-04 |

---

## 1. What was corrected, and how membership is derived

The audit is unchanged: one further full sweep of the complete model set at the single
evaluation's exit, the same scaled residual, the same τ. What changes is the **component set
the statistic is taken over**. The excluded set is derived, never listed: the deck's committed
post-solve artifact names *nodes* (the same file the driver validates); the committed run-time
write census maps each node to the fields it writes on that deck; the intersection with the
audit spec's keys is the excluded set. A prefix rule is deliberately not used — on
`st_regression` the node list contains `pulse`, which writes nothing there (V5), and a prefix
would either miss it or over-match. Both statistics are published.

*Caption: per deck, the post-solve node list, the number of spec components those nodes write
(over the full a26 spec, and over the continuous components the audit tests), and what
remains; dimensionless counts, from `preflight.json` and the run records (`exit_audit.restricted`).*

| deck | post-solve nodes | spec components | excluded (spec) | tested continuous | excluded (tested) | kept |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | vacuum, water_use, costs | 840 | 124 | 818 | 122 | 696 |
| `low_aspect_ratio_DEMO` | vacuum, water_use, costs | 846 | 125 | 824 | 123 | 701 |
| `st_regression` | pulse, vacuum, water_use, costs | 827 | 125 | 805 | 123 | 682 |

The three known-cut constants (`build.dr_fw_inboard`, `build.dr_fw_outboard`,
`pf_power.vpfskv`) are in the kept set on every deck, as they must be: they are written by
in-loop nodes.

## 2. Gates, with teeth — all PASS

*Caption: per deck, the four gates this task's numbers rest on. Entry and warm gates are V2's
own functions (A36), re-run unchanged; the restricted-audit teeth are this task's; the identity
gate compares every seed run against V2's record. Hex values are exact scaled residual maxima
(dimensionless, a26 ruler). Teeth columns name the doctored component and what it did.*

| deck | entry gate (audit vs threshold) | warm gate (cross max, above τ) | post-solve doctored: whole-state, restricted | in-loop doctored: block sweeps, restricted | identity vs V2 |
|---|---|---|---|---|---|
| `large_tokamak_nof` | PASS `0x1.3599f43fc8ddap-32` ≤ `0x1.f76312b8779a6p-27` | PASS `0x1.160774e05e9e3p-27`, 0 | `costs.c21`: whole `0x1.0425cd0e5ddbbp-1` from `0x1.075c4530fc877p-26`; restricted **bit-identical** `0x1.9fa768dbe4c0bp-36` | `blanket.deg_blkt_inboard_poloidal_plasma`: sweeps 4 → 6 | **50 / 50** |
| `low_aspect_ratio_DEMO` | PASS (reference audit exactly 0) | PASS `0x0.0p+0`, 0 | `costs.blkcst`: whole `0x1.0000000004ef7p-1` from `0x0.0p+0`; restricted **bit-identical** `0x0.0p+0` | `blanket.deg_blkt_inboard_poloidal_plasma`: sweeps 4 → 6 | **50 / 50** |
| `st_regression` | PASS `0x1.eae3a0e959de8p-34` ≤ `0x1.c22fb514702ddp-29` | PASS `0x1.c22fb514702ddp-29`, 0 | `costs.c21`: whole `0x1.f72fd02c36fa8p-2` from `0x1.2345ac5dd4c80p-32`; restricted **bit-identical** `0x1.eae3a0e959de8p-34` | `superconducting_tfcoil.a_tf_plasma_case`: sweeps 5 → 6, restricted moved to `0x1.1262727efeac2p-36` | **50 / 50** |

Every gate hex reproduces V2's (A36's smoke and the V2 campaign gates). The post-solve tooth
binds on more than "moved": the doctored component's own audit residual must equal its doctored
displacement over its scale (measured, all three decks, relative difference below 1e-9), because
the audit sweep recomputes the post-solve node from an otherwise unchanged state. The in-loop
tooth uses A36's OR semantics (the restricted statistic moved, or the measured call did more
work) because a re-converged component can land on identical bits at a bit-exact fixed point
(`low_aspect_ratio_DEMO`'s restricted audit is exactly 0 in both baseline and doctored runs, and
the doctoring costs two extra block sweeps). The tally's own restriction logic has a parser
tooth on a copy of a real residual vector (PASS, three decks). The identity gate is licensed by
hash: `process/`, `arch_surgery/fixedpoint/` and `arch_surgery/docs/data/` are tree-identical
between this branch and V2's two campaign commits (`ba69c05d`, `6d9ff4b9`); the runner's only
diff is the additive audit code.

## 3. The corrected similarity statistic

*Caption: per deck, median and nearest-rank p90 over the 25 paired-ok seeds of each arm's
audited maximum scaled residual (dimensionless), whole-state (as V2, reproduced bit for bit) and
restricted to the kept set; A1's restricted range in brackets; the ratio of restricted medians;
the F = 10 verdict at median and p90. A0 = flat, A1 = V2's unseeded block arm (trust mode,
post-solve suppressed, lift and pin on the pulsed decks).*

| deck | A0 whole med / p90 | A1 whole med / p90 | A0 restricted med / p90 | A1 restricted med / p90 [min – max] | ratio of restricted medians | verdict |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 6.3e-10 / 8.0e-9 | 2.44 / 9.86 | 5.0e-10 / 3.0e-9 | **6.4e-4 / 1.14e-3** [3.1e-4 – 1.27e-3] | 1.26e6 | **FAIL** (p90 ratio 3.9e5) |
| `low_aspect_ratio_DEMO` | 0.0 / 0.0 (25 exact zeros) | 0.182 / 0.288 | 0.0 / 0.0 | **9.8e-4 / 2.19e-3** [3.9e-4 – 3.08e-3] | unbounded | **FAIL** (one arm exactly zero) |
| `st_regression` | 5.4e-9 / 2.0e-8 | 0.258 / 0.337 | 5.4e-9 / 2.0e-8 | **1.15e-3 / 1.60e-3** [4.6e-4 – 1.77e-3] | 2.1e5 | **FAIL** (p90 ratio 7.9e4) |

Three readings. **The correction removes three orders of magnitude from the block arm's
audited deficit** (2.44 → 6.4e-4; 0.18 → 9.8e-4; 0.26 → 1.15e-3 at the median) and leaves the
flat arm essentially where it was (on `large_tokamak_nof` two of A0's 25 whole-state maxima
were post-solve dust and the restricted median falls from 6.3e-10 to 5.0e-10). **The
criterion still fails**, as pre-declared in the V3 plan §4.1 and the improvement list's item 4:
one trust pass from a δ-displaced entry leaves the machine build one displacement off through the
cut edge, and no accounting choice hides that. **The failure is now a statement about the
architecture**, not about the audit: it is the price of the trust step at a displaced entry, with
its carrier named below.

## 4. What sets the restricted maximum, and how much of it is the pair

*Caption: per deck, which component holds the block arm's restricted audit maximum, over the 25
runs; then A35's coefficient closure — the component's measured raw audit movement against the
raw image predicted from the pair's recorded entry displacement (`perturbation.json`, before and
after as exact hex), relative difference median / max over 25 runs; and the tally's
two-coefficient fit |a·Δin + b·Δout| where it converged. Traced = the deck was in A35's traced
scope. Gains and coefficients are dimensionless ratios of raw movements.*

| deck | restricted argmax census (of 25) | closed image, A35 predictor | closure rel. diff med / max | two-coefficient fit (a, b), max rel. residual |
|---|---|---|---|---|
| `large_tokamak_nof` (traced) | `build.dr_shld_vv_gap_outboard` 16, `build.dz_tf_upper_lower_midplane` 9 → **25 / 25 closed** | `dz_tf…`: 0.5·(Δin + Δout); `dr_shld_vv_gap_outboard`: −Δout | 1.8e-12 / 1.0e-11; 4.4e-9 / 6.1e-7 | `dz_tf…`: (0.500, 0.500), 2.5e-11 |
| `low_aspect_ratio_DEMO` (**not traced**) | `tfcoil.m_tf_coil_superconductor` 21, `dr_shld_vv_gap_outboard` 4 → **4 / 25 closed** | the two `large_tokamak_nof` images, tested as a hypothesis | 1.4e-12 / 7.2e-12; 8.4e-13 / 1.3e-11 | `dz_tf…`: (0.500, 0.500), 1.8e-11; `dr_shld…`: (0.0, −1.000), 1.3e-11; **`m_tf_coil_superconductor`: (17.4, 15.3), residual median 0.067, max 0.92 — not one linear image** |
| `st_regression` (traced) | `build.dr_shld_vv_gap_outboard` 17, `blanket.vol_shld_inboard` 8 → 17 / 25 closed by A35; **25 / 25 linear images** | `dr_shld_vv_gap_outboard`: −Δout | 8.9e-8 / 3.3e-6 | `vol_shld_inboard`: (47.0, 0.0), 2.0e-11 — a second image, gain measured not derived |

What this establishes, stated with its limits:

- **On the two large tokamak decks, A35's coefficients transfer exactly to `low_aspect_ratio_DEMO`.** The single-null vertical-build branch and the ripple branch of `build.py` are the same code on both decks, and the data recover the source coefficients with no source input: a = b = 0.500 for the TF-top clearance, (0, −1) for the outboard shield gap, in 25 of 25 runs at 1e-11. The two pair factors are independent draws (their ratio ranges from −40 to +12 across the seeds), which is what makes a fitted (0.5, 0.5) evidence rather than coincidence.
- **On `st_regression` every restricted maximum is a linear image of the pair.** The 8 runs where the maximum is the inboard shield volume carry a constant gain 47.0 on Δin alone (spread 2e-11 across seeds); the coefficient is measured, not read off the source, and is offered as such.
- **On `low_aspect_ratio_DEMO` the restricted maximum is, in 21 of 25 runs, a component the pair does not close.** The TF-coil superconductor mass moves by 29 to 38 times the pair's mean displacement, varying by ±12 % across seeds, and no pair of coefficients fits it (residual median 7 %, max 92 %). The pair's own images are present and exact on that deck; the mass carries something more — a nonlinear or branch-dependent response, or a second contributor among the perturbed inputs. **This task does not name it.** The instrument that would is A35's traced verified chain on that deck (the V3 plan's gate G3c), which A35 declared as its scope gap; the preseed counterfactual on that deck is informative precisely because of this term.

## 5. Consequences

1. **For the V2 report.** Its Phase A accuracy statement (§4) can now cite the restricted numbers of §3 as the block arm's genuine one-pass deficit, with the whole-state numbers kept beside as the accounting artifact they are; the argmax census of §4 replaces "75 of 75 post-solve-owned" with what lies underneath it.
2. **For the V3 plan.** §4.1's expectation is confirmed on all three decks; arm A1u is measured at this commit (the plan's §3.1 note); the counterfactual of the preseed (A1u → A1) has a per-deck baseline with named components. On `low_aspect_ratio_DEMO` the baseline carries the open term of §4, so the plan's pre-declared outcome "passes, or a new carrier is named" is already partly answered there: the pair's images will vanish, and whatever the mass carries beyond them will remain and be named.
3. **For the instrument.** `v2_eval_one.py` now writes `audit_residual.json` beside every record — the per-component scaled residual vector — so any future restriction of the statistic is a re-tally, not a re-run. V2's records and its `--verify` are unaffected (additive fields only; the identity gate is the proof).
4. **For the register.** Nothing new about the DSM: the carrier is V3's edge, and this task adds a third deck on which its two images are coefficient-exact, plus one open downstream term on that deck.

## 6. Autonomous decisions, with reversal paths

1. **Membership by node → fields → spec, not by prefix** (§1). Reversal: none needed; the prefix construction is recoverable from `audit_residual.json` in every record.
2. **A known post-solve node with no census entry is an empty contribution, not a refusal** (`st_regression`'s `pulse`, V5). The first campaign attempt refused on it and stopped; fixed at `300e9ee3` before any published run. Unknown nodes still refuse.
3. **OR semantics for the in-loop tooth**, as A36's. The second campaign attempt failed its own tooth on `large_tokamak_nof` because the reference audit's argmax there is `costs.coecap`, a post-solve-owned field, and the candidate list was unfiltered; fixed at `9fcedc92`, and that attempt's runs were discarded. Both aborted attempts are in the untracked logs and cited nowhere.
4. **The `low_aspect_ratio_DEMO` closure uses `large_tokamak_nof`'s coefficients as a tested hypothesis**, since A35 did not trace that deck. Reversal: the tally labels the deck untraced and reports the fit; a traced chain there (G3c) supersedes it.
5. **The gain analysis and the two-coefficient fit were added after the campaign**, as tally-only stages on the recorded data (`cd4d1845` … `ca736947`); they are offline analyses of committed records, declared here as post hoc rather than pre-declared. Reversal: delete the two functions; every §3 number is unaffected.

## 7. Provenance and reproduction

Every run: fresh subprocess, own working directory, `PYTHONPATH` pinned to this worktree, exact
tree asserted in-process; every campaign record stamped `9fcedc92 dirty=False x171`. V2's records were read
read-only from the main checkout's `runs/phase_a/campaign/` (stamps `ba69c05d` × 100,
`6d9ff4b9` × 50, all clean). Every published quantity is a count, a name, or a bit-exact hex
float; wall clock appears nowhere as evidence (runs took about 5 s each with a warm JIT cache,
reported as context only).

```
cd arch_surgery/idf_probe
python a38_audit_rerun.py preflight   # licence hashes, V2 records census, excluded sets  (§1, §2)
python a38_audit_rerun.py smoke       # st_regression, seeds 1..2: machinery only
python a38_audit_rerun.py campaign    # references, gates, teeth, 150 seed runs             (§2)
python a38_audit_rerun.py tally       # identity gate, both statistics, closure, fits      (§3, §4)
```

Which stage produced which figure: §1 — `runs/a38/preflight.json`; §2 — `runs/a38/campaign/
<deck>/{entry_gate,warm_gate,restricted_teeth}/gate.json` and `tally.json`'s
`identity_vs_v2` / `parser_teeth`; §3 — `tally.json` `whole_state_audit` / `restricted_audit`;
§4 — `tally.json` `argmax_census` / `closure` / `downstream_gain`.

## 8. Change log

- 2026-09-04 — task minted (`a4446bed`) at the user's instruction; worktree created by the
  sanctioned script; code committed (`4ea93408`) before any run.
- 2026-09-04 — smoke: two machinery defects found by the script's own refusals and fixed
  (`300e9ee3`, `70afc0fb`); smoke PASS on `st_regression`.
- 2026-09-04 — campaign attempt on `large_tokamak_nof` stopped by its own in-loop tooth (the
  reference argmax is post-solve-owned); tooth fixed (`9fcedc92`); campaign run at that commit,
  171 / 171 ok, all gates PASS, 150 / 150 identical to V2.
- 2026-09-04 — tally-only refinements: gain analysis, closure over every image, two-coefficient
  fit (`cd4d1845`, `e2e399a7`, `f5c81f90`, `ca736947`); report written.
