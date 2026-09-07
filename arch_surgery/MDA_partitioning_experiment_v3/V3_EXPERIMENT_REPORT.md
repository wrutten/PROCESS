# V3 experiment report — the prime: closing the FirstWall→Build carrier, and what the partitioned architecture costs and buys on three decks

> **Document status** — **CURRENT · EXPERIMENT REPORT.** Written 2026-09-07 by the
> orchestrating session after the approved full execution of
> [`EXPERIMENT_PLAN.md`](../../MDA_partitioning_experiment_v3/EXPERIMENT_PLAN.md) (approved by
> the user in their own commit `a164c6cd`, `EXECUTION_APPROVED` flipped in the same lineage).
> Campaign machinery and every run record at `362c0b47`, `dirty=False`. Analysis from
> [`v3_report_analysis.py`](../../MDA_partitioning_experiment_v3/v3_report_analysis.py) at
> `3a0bb8b1`. Experiment base commit `c0ae5b28`; **physics untouched throughout** — the only
> `process/` change in V3 is the driver (`caller.py`).

| | |
|---|---|
| **Task** | Execute the V3 experiment end-to-end: Phase A (per-call MDA cost and audit similarity; A0 flat / A1u unprimed / A1 primed, warm entries, N = 25, δ = 0.10) and Phase B (optimisation: R / B0 / B1 / B2 / B3, seed-paired N = 25), from the one-button `run_experiment.py` entry point |
| **Headline** | **The prime works.** Phase A's headline check (similarity within F = 10 at median and p90, restricted audit) **FAILS for A1u as pre-declared and PASSES for A1 on all three decks**: A1/A0 restricted medians 0.76 / exact-zeros / 1.00 against A1u/A0's 1.3e6 / ∞ / 2.2e5. On `low_aspect_ratio_DEMO` the result beats the plan's own expectation — A38's open term `tfcoil.m_tf_coil_superconductor` **closed** rather than needing naming. Cost of the prime in node calls: **A1u→A1 ratio exactly 1.0000, bracket [1.0, 1.0]**. **Phase B end-to-end** node calls B3/B0 over the identical-converged set: **0.639 / 0.450 / 0.533** (tok / lad / st). **Iteration bound (≤ 1.05 on the median) PASSES on every deck and every accepted pair.** **Same optimum (check 1): PASS on tok; FAIL on lad; FAIL on st all-pairs but passes within-cluster.** Check 1 measures **optimality, not location** — separately diagnosed (§5.2.2), tok and st agree on the optimum's *value* to 11 and 13 digits while landing at design points differing by up to 44 % and 100 %; the flat baseline does the same to itself under a stopping-rule change alone. A **pre-declared prediction was refuted**: lad's B2→B3 iteration multiplier, predicted to stay at ≈ 1.40, measured **1.00** |
| **Two defects found in the checking machinery, before any number was published** | **I-18** — the independent recomputation still implemented the *superseded* check-1 construction; `--verify` failed 26 of 144 cells and `--teeth` reported `baseline rc=1`. **I-19** — the plan's pre-declared within-cluster construction was implemented in *neither* script. Both fixed and committed before the numbers below; verdicts unchanged by I-18 |
| **Scripts** | `run_experiment.py` (F5 entry), `phase_a.py`, `phase_b.py`, `v3_runner.py`, `v3_config.py` — campaign + tally at `362c0b47`; `v3_report_analysis.py` — the independent recomputation and `--verify` / `--teeth`, at `3a0bb8b1` |
| **Runs** | Phase A: 249 metrics records (225 campaign = 3 decks × 3 arms × 25 seeds, **225/225 ok**, plus references and gates). Phase B: 350 optimisation runs (5 arms × 25 × 2 pulsed decks + 4 arms × 25 on st) + G0 / G5 / G7 gates + smoke. Serial context-timing block: 3 reps × 14 deck/arm cells |
| **Environment** | `PROCESS_surgery_env`; fresh subprocess and own working directory per run; `process.__file__` asserted in-process; W = 3 workers; every record stamps tree, commit and dirty flag |
| **Date** | 2026-09-07 (campaign 2026-09-04) |

---

## 1. What ran

Both phases, in full, from the single entry point, with no stage skipped and no run retried.
Every one of the 599 metrics records carries `tree_git_head = 362c0b47…`, `dirty = False`,
`python = …/PROCESS_surgery_env/bin/python` and
`process_file = /home/wrutten/projects/PROCESS_surgery/process/__init__.py`.

**Deck abbreviations**, used in the tables throughout: **`tok`** = `large_tokamak_nof`,
**`lad`** = `low_aspect_ratio_DEMO`, **`st`** = `st_regression`. They are display labels; the
deck identifiers in the records and scripts are unchanged.

**The A38-reuse clause (§3.3) — which path was taken.** The plan permitted reusing A38's
already-measured A1u records if gate G1 held at the V3 driver commit. **It was not used.**
A1u was re-run in full at `362c0b47`, 25 seeds × 3 decks, alongside A0 and A1. This is the
stronger of the two paths: all three arms are seed-paired at one commit, and the pairing
check confirms it — **25/25 seeds bit-identical entry state across all three arms on every
deck**.

**One launch failure, fixed before the campaign, not during it.** The first launch attempt
died on the A0 reference in 0.2 s and the harness reported it as *"the A0 reference did not
converge at the deck point — that failure is a result"*. It was nothing of the kind: the
entry point had been started under the system `python3.10`, and `import process` raised
`PackageNotFoundError`. Two defects, both fixed at `362c0b47` **before any campaign run**:
the entry point now subprocess-probes `sys.executable` and refuses up front naming the exact
fix, and Phase A now classifies `no_metrics`/`timeout` as `failure_class: machinery` with the
words *"MACHINERY FAILURE, not a physics result"*. A machinery failure wearing a physics
result's clothes is the worst failure mode this project has.

## 2. Two defects in the checking machinery, found before publication

Both were found by reading the committed plan against the committed records, and both are
the same class: **a declared definition that reached one implementation and not the other.**

**I-18 — the recomputation used the superseded check-1 construction.** Task A41 reported
that the harness's check 1 diverged from the plan (absolute Δ against an ensemble-median-scaled
floor, rather than the plan's per-pair relative statistic against a plain 1e-6 relative
floor). My adjudication `10a2ff36` fixed `phase_b.py`. It did **not** fix
`v3_report_analysis.py`, which by design restates every definition independently so that a
tally bug cannot vouch for itself. So the two implementations disagreed, and `--verify`
failed **26 of 144 cells** — every one a check-1 median or p90, on all three decks — with
`--teeth` reporting `baseline rc=1`, meaning no tooth demonstrated anything.

This was a defect in the *checker*, not in the campaign. Corrected at `7108cf33` by restating
the plan's declaration (committed at `29f642a1`, pre-campaign) in the recomputation, written
from the plan text rather than copied from `phase_b.py` so the two remain independent
implementations of one definition.

**The correction moves statistic values but not one verdict.** `verify()` compares the
`accepted` flag throughout and reported **zero acceptance mismatches even while failing**:

*Caption: check-1 acceptance under both constructions, per deck and arm pair. The superseded
construction is the absolute Δ against a median-scaled floor; the declared one is the
per-pair relative statistic against the plain 1e-6 floor. Verdicts are identical; only the
published numbers move.*

| deck | pair | superseded | declared |
|---|---|---|---|
| `large_tokamak_nof` | B0→B1 / B0→B2 / B0→B3 | True / True / True | True / True / True |
| `low_aspect_ratio_DEMO` | B0→B1 / B0→B2 / B0→B3 | False / False / False | False / False / False |
| `st_regression` | B0→B2 / B0→B3 | False / True | False / True |

**I-19 — the pre-declared within-cluster construction was in neither script.** Plan §4.2
check 1a ends: *"Within-cluster agreement (check 1's statistics over same-cluster pairs) is
published beside the all-pairs construction."* Neither `phase_b.py` nor
`v3_report_analysis.py` implemented it. It is a declared *reporting* rule with no acceptance
threshold, so it was added at `fc96e75e`, published beside, and never accepted against.
It changes how two of three decks read (§5.2).

**After both fixes:** `--verify` 144 cells, **0 mismatches**, `baseline rc=0`, **5/5 teeth
trip**.

## 3. Gates

*Caption: one row per gate — what it binds, the verdict, and the tooth that had to trip
first. G0/G5/G7 and Phase A's G4/G6 ran inside this campaign at `362c0b47`; G1/G2/G3/G3c ran
at task A40's commits (see the caveat below). No campaign number is cited before its gate.*

| gate | binds | verdict | teeth |
|---|---|---|---|
| **G0** V3 driver neutrality | every arm | **PASS** ×3 decks — R at `362c0b47` reproduces V2's recorded R start000 **bit-exactly** on `node_calls_solve_phase`, `n_model_calls` and `norm_objf` hex | +1 on each count, 1 ULP on each hex — all tripped |
| **G1** prime off, byte identity | R, B0, B1 | **PASS** (A40) | 1-ULP change caught |
| **G2** prime on, fixed-point map | the Phase B inertness disclosure | **PASS** (A40) | doctored snapshot component trips |
| **G3** prime on, cold chain | "no cut edge carries anything" | **PASS** (A40) | prime-off run reproduces A35's 3 passes and 244/124 |
| **G3c** lad carrier census | A38's open term | **PASS** (A40) — prime on ⇒ lad trust exit exactly `0x0.0p+0`, empty mover set | as G3 |
| **G4** audit restriction | the corrected similarity statistic | **PASS** ×3 decks (`restricted_teeth`) — a doctored post-solve component (`costs.blkcst`) trips whole-state and **not** restricted; a doctored in-loop component (`blanket.deg_blkt_inboard_poloidal_plasma`) trips both | both directions shown |
| **G5** B3 combined-switch equivalence | B3 | **PASS** ×3 decks — 7/7 checks incl. `norm_objf_hex`, `ifail`, `n_solver_iterations`, `outer_pass_hist`, `exit_audit_hex`; suppressed node calls 2910 / 4717 / 3100 | `norm_objf_hex` and `n_call_models` teeth both tripped |
| **G6** Phase A entry-state and warm equivalence | Phase A | **PASS** ×3 decks (`entry_gate`, `warm_gate_A1u`, `warm_gate_A1`) | as V2 |
| **G7** record completeness | the declared pairing and failure forensics | **PASS** — a forced-unconverged run (`ifail=2`, ladder `epsfcn_x0.1`) carries all five fields | 5/5 field teeth refused, each naming its field |

**Caveat, stated plainly: G1/G2/G3/G3c bind a `process/` tree that is not the one the
campaign ran.** Those gates executed at A40's commits, whose `process/` tree hashes to
`f117a854`; the campaign ran at `362c0b47`, whose `process/` hashes to `8e3723d2`. The
difference is exactly the I-17 instrument and nothing else — `git diff` over `process/`
between the two is **one file, 41 insertions, 0 deletions**, all of them a `dict`/`int`
counter increment and a function split with no behaviour of its own, touching no float and
no branch a result depends on. Two independent things close the gap empirically: the
instrument's own neutrality check at its commit (13 493 MFILE hex floats vs the pre-instrument
tree, 0 mismatches), and **G0, which ran at the campaign commit** and reproduces V2's records
bit-exactly. I judge the gap closed, and record it here so a reader can disagree.

## 4. Phase A results — does the prime close the carrier?

**Check 1 (the headline Phase A check): similarity within F = 10 at both median and p90, on
the restricted audit.**

*Caption: restricted-audit max-scaled-residual distributions, per deck, one column per arm,
over 25 seeds each (`n_paired_ok = 25/25`, all decks). The acceptance ratio is the arm's
statistic over A0's; the rule is within F = 10 at median **and** p90. "Restricted" excludes
components owned by the deck's post-solve node set, membership derived nodes → write census →
spec keys (A38's construction, gated by G4). The whole-state statistic is published beside in
§8.*

| deck | A0 (control) | A1u (no prime) | A1 (prime) | A1u/A0 med, p90 | A1/A0 med, p90 | verdict |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 5.04e-10 / 2.96e-9 | 6.36e-4 / 1.14e-3 | 3.83e-10 / 1.67e-8 | 1.3e6, 3.9e5 → **FAIL** | 0.76, 5.64 → **PASS** |  |
| `low_aspect_ratio_DEMO` | 0 / 0 | 9.81e-4 / 2.19e-3 | **0 / 0** | ∞ → **FAIL** | both exactly 0 → **PASS** | trivially-similar clause |
| `st_regression` | 5.37e-9 / 2.02e-8 | 1.15e-3 / 1.60e-3 | 5.37e-9 / 2.02e-8 | 2.2e5, 7.9e4 → **FAIL** | 1.00, 1.00 → **PASS** |  |

Both pre-declared expectations are met, and one is beaten:

- **A1u fails on the carrier alone**, exactly as §3.3 predicted from A38's measurement.
- **A1 passes on all three decks.** On st, A1's distribution is *bit-identical* to A0's.
- On lad the plan expected "the naming case" — the pair's images vanish and whatever
  `tfcoil.m_tf_coil_superconductor` carries beyond them survives and is named. **It did not
  survive.** lad reads exact zeros under the prime, so A38's open term **closed**. This is
  consistent with G3c, which found the lad trust exit at exactly `0x0.0p+0` with an empty
  mover set.

**Cost of the prime (check 3).** The pre-declared expectation was "A1u/A1 counts equal to
within one M2 inner sweep". Measured: **equal exactly.**

*Caption: Phase A per-call cost, per deck. Node calls are summed over the 25 paired-ok seeds.
The unweighted count ratio and its weighting-invariance bracket are the declared cost
statistics (the I-10 insurance: counts, never timings).*

| deck | A0 node calls | A1u | A1 | A0→A1u ratio | A0→A1 ratio | A1u→A1 ratio | bracket (A0→A1) |
|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 2898 | 1512 | 1512 | 0.5217 | 0.5217 | **1.0000** | [0, 0.935] |
| `low_aspect_ratio_DEMO` | 2625 | 1491 | 1491 | 0.5680 | 0.5680 | **1.0000** | [0, 0.976] |
| `st_regression` | 3066 | 1538 | 1538 | 0.5016 | 0.5016 | **1.0000** | [0, 1.0] |

**What that 1.0000 does and does not say — trap T11.** It says the prime changes *what*
`Build` reads, not how often any model node runs. It does **not** say the prime is free: by
declaration (D19) a prime call is stamped as `n_prime_calls` and never pooled into
`node_calls`, so the denominator above deliberately excludes it. The excluded quantity must
therefore be named. In Phase A, A1 executes **13 (tok) / 15 (st) prime calls** against 60 and
62 counted node calls. In Phase B it runs at **0.9999–1.0000 prime calls per sweep** and
**0.19–0.23 per counted node call** (§5.5). Whether that is cheap depends on the cost of one
`set_fw_geometry()` against one average model node — which is a timing, and no conclusion
here rests on one.

**Failure taxonomy.** 25/25 `ok` in every arm on every deck, denominators of 25.
`exit_forensics_complete: True` throughout.

**Carrier closure (check 2).** A1u's recorded entry displacement of the `dr_fw` pair predicts
the measured restricted-audit maximum to a relative difference of median 1.8e-12 (tok),
8.4e-13 (lad), 8.9e-8 (st) over 25 runs each — the carrier is closed and quantitative.

### 4.4 Phase A statistics and failure rates

Added 2026-09-07 at the user's request. §4's tables give medians and p90s; this is the full
picture, including the denominators and the failure count.

**Failure rate: zero.** 225 campaign runs (3 decks × 3 arms × 25 seeds), **225/225 `ok`**,
denominators of 25 per arm per deck, `exit_forensics_complete: True` throughout. No run
crashed, refused, timed out or was dropped, so every Phase A statistic below is over the full
declared sample with no seed selection of any kind. Phase A is the clean half of this campaign;
every failure discussed in this report is Phase B's.

*Caption: full restricted-audit distributions per deck and arm, over 25 ok runs each —
minimum, median and maximum of the max-scaled residual, then the count of components exceeding
τ = 1e-6 (summed over the 25 runs, and the worst single run). Sweeps and node calls per single
evaluation are given as ranges. Dimensionless; a26 ruler.*

| deck | arm | min | median | max | Σ components > τ | worst run | sweeps | node calls |
|---|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | A0 | 0 | 5.04e-10 | 4.35e-9 | **0** | 0 | 5–6 | 105–126 |
| | A1u | 3.10e-4 | 6.36e-4 | 1.27e-3 | **3906** | 167 | 13–14 | 60–63 |
| | A1 | 0 | 3.83e-10 | 1.87e-8 | **0** | 0 | 13–14 | 60–63 |
| `low_aspect_ratio_DEMO` | A0 | 0 | 0 | 0 | **0** | 0 | 5 | 105 |
| | A1u | 3.92e-4 | 9.81e-4 | 3.08e-3 | **3881** | 167 | 12–13 | 57–60 |
| | A1 | 0 | 0 | 0 | **0** | 0 | 12–13 | 57–60 |
| `st_regression` | A0 | 1.63e-9 | 5.37e-9 | 2.88e-8 | **0** | 0 | 5–6 | 105–126 |
| | A1u | 4.55e-4 | 1.15e-3 | 1.77e-3 | **1525** | 66 | 14–15 | 59–62 |
| | A1 | 1.63e-9 | 5.37e-9 | 2.88e-8 | **0** | 0 | 14–15 | 59–62 |

Three things the medians in §4 do not show:

**1. The distributions do not overlap at all.** On every deck, **A1u's minimum exceeds A0's
maximum** — by five orders on tok (3.10e-4 against 4.35e-9), four on st (4.55e-4 against
2.88e-8), and unboundedly on lad (3.92e-4 against exactly 0). There is no seed, on any deck,
where the unprimed block arm resembles the flat control. The F = 10 verdict is not a close
call decided by a summary statistic; the two populations are entirely disjoint.

**2. A1 reproduces A0 exactly on two decks, not merely closely.** On lad both arms read
**0 at min, median and max** across all 25 runs. On st the two distributions are
**bit-identical at all three order statistics** (1.63e-9 / 5.37e-9 / 2.88e-8). Only tok shows
any difference, and there A1's median is *below* A0's (3.83e-10 against 5.04e-10) with a
slightly longer tail (1.87e-8 against 4.35e-9).

**3. The count statistic is cleaner than the magnitude.** `Σ components > τ` is an integer and
needs no ruler: **A0 and A1 leave zero components unconverged in every run of every deck**,
while A1u leaves up to 167 in a single run. That is the result stated without reference to any
scale — the prime does not merely shrink the residual, it removes every above-tolerance
component.

**Audit population.** Each deck's coupling-state spec holds 840 (tok) / 846 (lad) / 827 (st)
components. Of these, **22 on every deck are discrete** and are tested by exact equality rather
than the scaled residual (`n_discrete_mismatch = 0` throughout); the remaining 818 / 824 / 805
carry the scaled test, and the restricted construction keeps **696 / 701 / 682** of them,
excluding **122 / 123 / 123** as owned by the deck's post-solve node set. The exclusion is
gated in both directions by G4.

**Cold-start term** (reported beside, never pooled into the per-call statistics): 126 node
calls over 6 sweeps (tok), 105 over 5 (lad), 147 over 7 (st) — the once-per-run cost of the
full flat MDA convergence at that deck's cold entry, A0 arm.

**Lift residual** (excluded from the similarity statistic by declaration, §4.4 of the plan):
reported separately per deck as `burn_time_residual` at exit; inactive on `st_regression`
(k = 0 — nothing lifted or pinned).

### 4.5 Per-module breakdown (Phase A), aligned to the collapsed DSM

Rewritten twice on 2026-09-07 at the user's request: first onto the **rows of the collapsed
DSM** (decision D8, `arch_surgery/docs/data/dsm_node_map.json`), with **the per-module ratios as
the headline rather than the total** — for a reason given below that is stronger than taste —
and then from seed-set **sums** to **sweeps per run with a seed bracket**, after the sums were
found to hide both the denominator and the run-to-run spread.

#### Module scope

*Caption: the D8 modules, their DSM row counts, and which model nodes execute in each on the
three decks. The static map holds 26 model nodes; **21 execute on any one deck** — the TF-coil
family (`aluminium_tf_coil`, `copper_tf_coil`, `croco_sctfcoil`, `resistive_tf_coil`,
`sctfcoil`, `tfcoil`, `cicc_sctfcoil`) contributes exactly one member per deck by conductor
choice, and `dcll` is an alternative blanket model to `ccfe_hcpb`. `vacuum` is listed with the
feed-forward set — see the reconciliation below the table.*

| DSM module | DSM rows | iterated | executing | nodes |
|---|---|---|---|---|
| **M1** Physics | 24 (rows 4, 6–28) | yes | 2 | `plasma_geom`, `physics` |
| **M2** Coils | 10 (rows 5, 29–37) | yes | 3 | `build`, `pfcoil`, + one TF model: `cicc_sctfcoil` (tok, lad) / `croco_sctfcoil` (st) |
| **M3** Plant, live | 12 (rows 40–51), of which one is `vacuum`'s | yes | 12 | `divertor`, `fw`, `shield`, `vacuum_vessel`, `ccfe_hcpb`, `cryostat`, `structure`, `power`, `power.acpow`, `power.plant_electric_production`, `availability`, `buildings` |
| **PULSE** | 1 (row 39) | no | 1 on tok, lad · 0 on st | `pulse` — on st it is post-solve, yet the block is still swept (§5.6, I-20) |
| **FF** feed-forward tail | 5 (row 38, 52–55) | no | 2 | `costs`, `water_use` |
| **`vacuum`** — measured feed-forward | 1 (inside M3's range) | — | 1 | `vacuum` |

**Reconciling `vacuum`: the static map and the measured liveness are both right, about
different things.** The DSM map places `vacuum`'s row in M3 — a *topological* assignment
from the collapsed call graph; `in_loop` there is a property of the module, and no node entry
in that file carries any liveness field. A33's post-solve derivation, a *runtime liveness*
classification, places `vacuum` in the feed-forward set. There is no contradiction: a node can
sit in an iterated block's rows and still have no live consumer. Whether it does was settled
independently on 2026-09-07 by a read-only investigation with its own runtime read census
(`PROCESS_IDF_PROBE=modules`, closed at the `_call_models_once` boundary, 2029 / 4286 / 1891
sweeps by deck): **the only node that reads any of `vacuum`'s five written fields is
`costs`, itself post-solve; `objective_constraints` reads none; `availability`'s reads are on
`i_plant_availability` = 2/3 branches and all three decks set 0.** The census's numbers are
ad hoc and are not cited here (protocol §15); the committed evidence is A33's per-field
`external_source_read_sites` in `postsolve_<deck>.json`, which the census reproduced exactly.
**`vacuum` is feed-forward on all three decks, and its status is joint with `costs`** — on a
cost-objective deck (`i_figure_merit` 6 or 7) `costs` stays live and `vacuum` would follow.
That case is not among the three scenarios.

#### Per-module ratios — the headline

*Caption: **module sweeps per run** — the number of times each DSM module was executed in one
evaluation, as the mean over each deck's 25 ok runs with its **seed bracket** [min, max]; a bare
integer means all 25 runs agreed exactly. A1u is identical to A1 in every cell, seed by seed
(the prime changes what `Build` reads, not how often anything runs). `models` is the module's
DSM row count — the models the collapsed DSM resolves inside it — so **total calls =
Σ sweeps × models**. **The ratio column is the result.** Within one module every model executes
the same number of times (refused by the script if it ever fails to, with a tooth), so the cell
is a sweep count and its ratio does not depend on whether one counts model calls or DSM rows.
The total does, and is bracketed — see below. From `v3_report_analysis.py --tables`.*

**`tok`** (n = 25)

| module | models | A0 | A1u | A1 | A1/A0 |
|---|---|---|---|---|---|
| M1 | 24 | 5.52 [5,6] | 4 | 4 | **0.725** |
| M2 | 10 | 5.52 [5,6] | 5.16 [5,6] | 5.16 [5,6] | **0.935** |
| M3 live | 11 | 5.52 [5,6] | 3 | 3 | **0.543** |
| `vacuum` | 1 | 5.52 [5,6] | 0 | 0 | **0.000** |
| PULSE | 1 | 5.52 [5,6] | 1 | 1 | **0.181** |
| FF | 5 | 5.52 [5,6] | 0 | 0 | **0.000** |
| **total calls** | 52 | 287.0 | 181.6 | 181.6 | **[0.633, 0.643]** |

**`lad`** (n = 25)

| module | models | A0 | A1u | A1 | A1/A0 |
|---|---|---|---|---|---|
| M1 | 24 | 5 | 4 | 4 | **0.800** |
| M2 | 10 | 5 | 4.88 [4,5] | 4.88 [4,5] | **0.976** |
| M3 live | 11 | 5 | 3 | 3 | **0.600** |
| `vacuum` | 1 | 5 | 0 | 0 | **0.000** |
| PULSE | 1 | 5 | 1 | 1 | **0.200** |
| FF | 5 | 5 | 0 | 0 | **0.000** |
| **total calls** | 52 | 260.0 | 178.8 | 178.8 | **[0.688, 0.699]** |

**`st`** (n = 25)

| module | models | A0 | A1u | A1 | A1/A0 |
|---|---|---|---|---|---|
| M1 | 24 | 5.84 [5,6] | 4 | 4 | **0.685** |
| M2 | 10 | 5.84 [5,6] | 5.84 [5,6] | 5.84 [5,6] | **1.000** |
| M3 live | 11 | 5.84 [5,6] | 3 | 3 | **0.514** |
| `vacuum` | 1 | 5.84 [5,6] | 0 | 0 | **0.000** |
| PULSE | 1 | 5.84 [5,6] | 0 | 0 | **0.000** |
| FF | 5 | 5.84 [5,6] | 0 | 0 | **0.000** |
| **total calls** | 52 | 303.7 | 187.4 | 187.4 | **[0.617, 0.627]** |

**What the sweep form shows that the node-call sums did not.** The flat arm's column is **one
repeated number** — a flat sweep executes every module equally often, which six different node
totals obscured. The block arm's M1, M3, `vacuum`, PULSE and FF cells are **exact constants
across all 25 runs**: 4, 3, 0, 1 and 0 sweeps, no spread whatever. All the Phase A seed
dispersion lives in M2 and in the flat arm's own sweep count, and it never exceeds **one
sweep**. And st's M2 = 1.000 stops being a coincidence: the partitioned arm runs 5.84 M2 sweeps
against the flat arm's 5.84, seed for seed — the partition buys that module nothing because it
does not reduce its sweep count at all.

**Why the total is demoted: it is unit-dependent by eleven to twelve points, and the
per-module ratios are not.** M1 is 2 model calls but 24 DSM rows; M3 is 12–13 model calls and 12 rows. M1 saves
least (0.725 / 0.800 / 0.685) and M3 saves most (0.543 / 0.600 / 0.514). Counting model calls
weights the total toward M3; counting DSM rows weights it toward M1. So the same campaign reads
**0.522 (node-weighted) or 0.633–0.643 (model-weighted) on tok** — and neither is more correct,
because the unit is a modelling choice. All of them sit inside the pre-published
weighting-invariance bracket `[0, 0.935]` (this table's minimum and maximum ratio), so the
bracket did its job; but the *point estimate* the report led with was not unit-free. The
per-module ratios are.

**Why the total is a bracket and not a number (trap T9).** `models` per module is committed;
`models` per *node* is not — `dsm_node_map.json` pins a DSM row for exactly four nodes
(`build` 5, `fw` 41, `power` 48, `pulse` 39) and nulls the rest, because T9 forbids reading the
dependency-analysis repository's exports live. M3 holds 12 rows across 13 executing nodes, so
how many of them `vacuum` owns is **unknown**. The interval brackets the two defensible cases:
`v = 1` gives `vacuum` a row of its own (0.633 / 0.688 / 0.617), `v = 0` leaves it inside M3
and therefore credits it with M3's sweep count, which the measured liveness says it does not
have (0.643 / 0.699 / 0.627). The earlier point estimate was the `v = 0` case, published
alongside a `vacuum` row reading 0.000 — the bracket removes that inconsistency rather than
restating it. **No per-module ratio is affected.** A second limit is stated and not resolved:
the map asserts 52 rows execute in a sweep while only 21 of 26 model nodes execute on any one
deck (TF family switch-selected, `dcll` unused), so the 52-row weight includes rows owned by
nodes that do not run on that deck; bounding that needs the per-node attribution T9 blocks.
**What the modules say, and Phase B agrees (§5.5.1):** M2 barely benefits — the partition saves
that module nothing at all on st, where it runs the same 5.84 sweeps in both arms; M3 carries
the largest absolute saving — **2.52 / 2.00 / 2.84 fewer sweeps per evaluation**, across the
most models of any live module — and is where the partition does real work; the feed-forward
set goes to zero. Per evaluation, A0 sweeps every module 5.0–5.8 times; A1 runs 4 (M1),
≈ 5.2 (M2), 3 (M3) and 1 (PULSE).

**Provenance of the grouping (a recording gap, named).** The Phase B tables read block
membership and the post-solve set from each run's own record. Phase A's records cannot supply
the second: `post_solve_totals` is null and `PROCESS_ARCH_POST_SOLVE` is absent from the
recorded environment in every Phase A run, although `phase_a.py` does set it. The grouping
above therefore comes from the committed artifact `postsolve_nolift_<deck>.json`, and its
content is confirmed by `node_census.counted`: in A1u and A1, `vacuum`, `costs` and
`water_use` are at **0** calls while M3's other twelve nodes run 3 each. The gap is in
`run_one.py` and is on the V4 list.

**Two denominators to keep straight (trap T11).** The feed-forward rows' 0 is *not* the claim
that the intervention removes those nodes: they execute zero times *inside the measured
evaluation*, because Phase A halts at the exit audit before the once-per-run post-solve
execution. Phase B, which reaches it, records them at ~4 executions per run against B0's
~2000; amortised, the block-arm cost is ≈ 0.02 per evaluation and 0 is right to two decimals.

#### What the exclusion set is load-bearing for

The restricted headline (§4) excludes **124 / 125 / 125** components of the coupling state
(122 / 123 / 123 continuous, 2 discrete), in five namespaces: `costs` (109–110),
`water_use` (8), `vacuum` (5), and one field each written by `costs` into other namespaces —
`fwbs.life_blkt` and `physics.wtgpd`. §8 item 6 says the headline rests entirely on that set
being right. This table says by how much.

*Caption: p90 across 25 runs of the per-run maximum scaled residual, restricted set against
each excluded namespace, from every run's own `audit_residual.json`. In the block arms every
excluded namespace is nonzero in **25/25 runs** on every deck. A0's excluded set is at
machine noise or exactly zero.*

| deck | arm | restricted (headline) | `costs` | `water_use` | `vacuum` | `fwbs` | `physics` |
|---|---|---|---|---|---|---|---|
| tok | A0 | 2.96e-9 | 7.96e-9 | 2.86e-16 | 1.15e-12 | 0 | 0 |
| | A1 | **1.67e-8** | 9.86 | 0.099 | **0.068** | 0.135 | 0.053 |
| lad | A0 | 0 | 0 | 0 | 0 | 0 | 0 |
| | A1 | **0** | 0.288 | 0.129 | **0.097** | 0.084 | 0.085 |
| st | A0 | 2.02e-8 | 1.58e-9 | 1.36e-11 | 8.91e-11 | 0 | 0 |
| | A1 | **2.02e-8** | 0.334 | 0.319 | **0.091** | 0.037 | 0.197 |

**Had `vacuum` been wrongly excluded, the restricted headline would read 0.068 / 0.097 / 0.091
instead of 1.7e-8 / 0 / 2.0e-8** — six to seven orders — and would exceed A1u's own values
(1.1e-3 / 2.2e-3 / 1.6e-3), destroying the A1u-fails / A1-passes discrimination on every deck.
The membership of every one of these five namespaces is therefore load-bearing, not
cosmetic; `vacuum`'s is now confirmed by an independent read census, and the other four rest on
A33's derivation and G4's teeth (which doctor a `costs` component, not one from each
namespace — V4 list, item 6a).

## 5. Phase B results — the declared checks, per deck, never pooled

### 5.1 Robustness and taxonomy (denominators of 25)

*Caption: per-arm outcome census, one row per arm. `deck_invalid_seeds` are seeds that fail
in **every** arm — a property of the deck point, excluded from the per-arm failure rate by
declaration so that a deck's own bad starts are not charged to an architecture.*

| deck | invalid seeds | arm | ok | converged (`ifail=1`) | not-converged among ok |
|---|---|---|---|---|---|
| `large_tokamak_nof` | 3 (5, 20, 21) | R / B0 / B1 / B2 / B3 | 22 each | 22 each | **0 in every arm** |
| `low_aspect_ratio_DEMO` | 13 | R | 23 | 12 | 0 |
| | | B0 | 21 | 12 | 0 |
| | | B1 / B2 / B3 | 20 each | 11 each | 1 each |
| `st_regression` | 1 (17) | R | 25 | 24 | 0 |
| | | B0 | 25 | 23 | 1 |
| | | B2 | 25 | 24 | 0 |
| | | B3 | 25 | 23 | 1 |

`low_aspect_ratio_DEMO` remains the hostile deck: **13 of 25 starts are invalid in every
arm**, and lad's B2→B3 verdict rests on **11 both-converged pairs** — published with that
denominator, as O2 required.

### 5.2 Same optimum (check 1) — and what "same" does and does not mean

**Read this before the table.** Check 1 compares `|Δ norm_objf|`: *how good* the optimum an
arm reached is. It does **not** compare *where* the arm landed. The two questions are
different, they are answered by different quantities, and on two of three decks they give
opposite impressions:

- **Optimality agreement** — do the arms find equally good optima? This is check 1, it is the
  declared acceptance, and it is gated on `norm_objf` alone.
- **Location agreement** — do the arms land on the same design point? This is **not** gated,
  by deliberate decision (D6: *"never on iteration variables — some are not identified by the
  problem and differ at an unchanged optimum"*). It is reported below as a diagnostic.

Conflating them is the easiest available misreading of this campaign, so both are tabulated
together. A pair can agree on the objective to thirteen digits and sit at design points
differing by 100 % in some variable — and on `st_regression` that is exactly what happens.

#### 5.2.1 Optimality (check 1 — the declared acceptance)

*Caption: per-pair relative |Δ `norm_objf`| at accepted optima (`ifail=1` both sides), median
and p90, nearest-rank throughout. Acceptance at **both** quantiles against
`max(F × yardstick, 1e-6)`, yardstick = the measured R→B0 spread. The within-cluster columns
are plan §4.2 check 1a's pre-declared companion construction (I-19), published beside and
never accepted against; `n_hops` is how many pairs it excludes.*

| deck | pair | all-pairs med | all-pairs p90 | **verdict** | hops | within-cluster med | within-cluster p90 | would accept |
|---|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | R→B0 (yardstick) | 2.08e-15 | 6.89e-13 | — | 0 | 2.08e-15 | 6.89e-13 | — |
| | B0→B1 / B2 / B3 | 2.82e-11 | 4.57e-11 | **PASS** | 0 | 2.82e-11 | 4.57e-11 | True |
| | B2→B3 | 0 | 0 | — | 0 | 0 | 0 | — |
| `low_aspect_ratio_DEMO` | R→B0 (yardstick) | 2.88e-14 | 3.15e-12 | — | 0 | 2.88e-14 | 3.15e-12 | — |
| | B0→B1 / B2 / B3 | 4.10e-7 | **2.15e-6** | **FAIL** | 1 | 4.10e-7 | **1.26e-6** | **False** |
| | B2→B3 | 1.76e-14 | 2.52e-14 | — | 0 | 1.76e-14 | 2.52e-14 | — |
| `st_regression` | R→B0 (yardstick) | 1.55e-13 | 5.91e-9 | — | **2** | 1.10e-13 | 2.21e-10 | — |
| | B0→B2 | 4.90e-13 | **1.26e-2** | **FAIL** | **4** | 1.76e-13 | 1.89e-10 | **True** |
| | B0→B3 | 3.47e-13 | 3.51e-9 | **PASS** | 1 | 1.02e-13 | 6.76e-11 | True |
| | B2→B3 | 1.43e-13 | 3.32e-9 | — | 2 | 3.62e-14 | 2.57e-10 | — |

**The two failures are not the same kind of failure, and the within-cluster construction is
what separates them.**

- **st's failure is attractor hopping, not disagreement.** st is a 4-cluster deck. B0→B2
  hops on 4 of 23 pairs; removing them takes the p90 from 1.26e-2 to **1.89e-10**, and it
  would pass. Decisively: **the R→B0 yardstick itself hops on 2 of 23 pairs** — and R→B0 is
  nothing but a change of *stopping rule*. Hopping is a property of this deck, not of the
  partition. The plan anticipated exactly this ("V2 measured the stopping-rule change itself
  hopping on st — a hop is a counted event, not an outlier").
- **lad's failure survives the hop removal and is real.** Only 1 pair is a hop; the
  within-cluster p90 is 1.26e-6, still above the 1e-6 floor. lad's arms genuinely disagree on
  the objective by ~4e-7 relative at the median. The failure is **marginal — the p90 exceeds
  its bound by a factor of 1.26** — and the median (4.10e-7) is *inside* the floor. It fails
  the declared rule at one quantile of two. That is a failure, and it is reported as one.

**Which ladder rung causes lad's disagreement?** B0→B1, B0→B2 and B0→B3 report the *same*
statistic to three significant figures, which localises it. A post-hoc diagnostic (not a
declared pair, published as a diagnostic) measures **B1→B2 at median 2.0e-14** on lad and
**0 on tok**. So B1, B2 and B3 agree with each other to machine noise, and the entire
disagreement enters at **B0→B1 — the burn-time lift**. **Neither the partition nor the prime
moves lad's objective.** The lift does.

#### 5.2.2 Location — where the arms actually landed (diagnostic, never an acceptance)

*Caption: over exactly check 1's both-converged pairs, the max over iteration variables of
the per-variable relative difference |Δx| / max(|x_a|, |x_b|) on the unscaled vector, with
the argmax variable named. Variables are matched **by name**, never by index: the lift adds
`t_plant_pulse_burn`, so B1/B2/B3 carry one more iteration variable than B0 on the pulsed
decks; the unshared variable is named, never compared. **This is a diagnostic. D6 forbids
gating on it, and nothing in this report's verdicts rests on it.** The objective columns are
check 1's, repeated for direct comparison.*

| deck | pair | objf med | objf p90 | check-1 verdict | **point med** | **point p90** | **point max** | shared / extra vars |
|---|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | R→B0 | 2.08e-15 | 6.89e-13 | — | 7.17e-7 | 2.55e-6 | 1.63e-4 | 20 / — |
| | B0→B1 / B2 / B3 | 2.82e-11 | 4.57e-11 | **PASS** | **4.56e-2** | **1.87e-1** | **4.41e-1** | 20 / `t_plant_pulse_burn` |
| | B2→B3 | 0 | 0 | — | 1.16e-9 | 4.16e-9 | 2.63e-8 | 21 / — |
| `low_aspect_ratio_DEMO` | R→B0 | 2.88e-14 | 3.15e-12 | — | 5.98e-12 | 8.98e-10 | 3.47e-7 | 19 / — |
| | B0→B1 / B2 / B3 | 4.10e-7 | 2.15e-6 | **FAIL** | 5.35e-6 | 1.01e-5 | 7.04e-3 | 19 / `t_plant_pulse_burn` |
| | B2→B3 | 1.76e-14 | 2.52e-14 | — | 7.89e-12 | 3.37e-11 | 1.44e-10 | 20 / — |
| `st_regression` | R→B0 | 1.55e-13 | 5.91e-9 | — | 4.46e-5 | **1.70e-1** | **1.00** | 14 / — |
| | B0→B2 | 4.90e-13 | 1.26e-2 | **FAIL** | 8.69e-6 | **2.51e-1** | **1.00** | 14 / — |
| | B0→B3 | 3.47e-13 | 3.51e-9 | **PASS** | 4.53e-6 | **2.07e-1** | **1.00** | 14 / — |
| | B2→B3 | 1.43e-13 | 3.32e-9 | — | 8.69e-6 | 1.94e-1 | 2.17e-1 | 14 / — |

**The two questions come apart, and not by a little.**

- **`large_tokamak_nof` passes check 1 at 2.8e-11 while its design point moves by 4.6 % at
  the median and 44 % at the worst.** Nine orders of magnitude separate the objective
  agreement from the location agreement. The argmax census names where it goes:
  `f_nd_alpha_thermal_electron` (12 of 22 pairs) and `f_nd_impurity_electrons(13)` (5 of 22)
  — composition fractions, which is what a weakly-identified direction looks like.
- **`st_regression` is the extreme case: objectives agree to 1e-13, and some pairs' points
  differ by 100 %** in `dr_shld_inboard` (argmax on 14 of 22 pairs) or `dr_tf_nose_case`
  (6 of 22). The optimum's *value* is reproduced to thirteen digits; its *location* is not
  pinned by the problem at all in those directions.
- **The deck that FAILS check 1 has the tightest point agreement of the three.** lad's
  objective disagrees by 4.1e-7 while its design point agrees to 5.4e-6 — the reverse of the
  other two decks. Whatever the lift does to lad, it is not relocating the design.

**Two attributions this makes cleanly, both of which matter for the headline:**

1. **The partition and the trust step are point-preserving.** B2→B3 point differences are
   1.2e-9 / 7.9e-12 / 8.7e-6 — at or near the noise on every deck. The architecture change
   this experiment is *about* does not move the design.
2. **On the pulsed decks the relocation enters at B0→B1, the lift** — the same rung that
   moves lad's objective. This is coherent rather than surprising: the lift *adds an
   iteration variable* (`t_plant_pulse_burn`) and a constraint, enlarging the search space,
   so the optimiser can reach an equally good point somewhere else in it. It is a change of
   problem parameterisation, and a relocated design is the expected consequence.

**And the control settles whether any of this indicts the architecture.** On st, **R→B0 — a
change of stopping rule and nothing else — moves the point by p90 0.17 and max 1.00**, as
much as any architectural rung does. Non-identification is a property of the deck and its
constraint set, not of the partition. This is precisely why D6 forbids gating on iteration
variables, and this campaign is the measurement that justifies that rule rather than merely
asserting it.

**What this costs the headline.** Nothing in §5.5's cost result or §4's prime result depends
on location agreement. But a reader who takes "same optimum (check 1): PASS" to mean "the
architectures produce the same machine" would be wrong on tok and badly wrong on st. The
honest statement is: **the architectures reach optima of the same quality; on two of three
decks they do so at materially different design points, and the flat baseline does the same
thing to itself when only its stopping rule changes.**

### 5.3 Iteration multiplier (check 2, bound ≤ 1.05 on the median paired ratio)

*Caption: paired optimiser-iteration ratios over **both-converged** pairs (the declared
pairing: `status == ok` AND MFILE `ifail == 1`). The declared acceptance is the nearest-rank
median for B0→B1/B2/B3 only. Summed iterations over exactly the ratio-contributing pairs are
published beside every median, per the pre-campaign amendment; `agree` is the declared
direction flag. **Totals are never carried across columns** — the contributing seed set
differs per pair.*

| deck | pair | n | median | sum a | sum b | sum ratio | agree | bound met |
|---|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | B0→B1 / B2 / B3 | 22 | 1.000 | 172 | 171 | 0.994 | ✓ | **PASS** |
| | B0→R | 22 | 1.000 | 172 | 172 | 1.000 | ✓ | beside |
| | B2→B3 | 22 | 1.000 | 171 | 171 | 1.000 | ✓ | beside |
| `low_aspect_ratio_DEMO` | B0→B1 / B2 / B3 | 11 | 0.833 | 228 | 230 | **1.009** | **✗** | **PASS** |
| | B0→R | 12 | 1.000 | 239 | 239 | 1.000 | ✓ | beside |
| | **B2→B3** | 11 | **1.000** | 230 | 230 | **1.000** | ✓ | beside |
| `st_regression` | B0→B2 | 23 | 1.000 | 568 | 508 | 0.894 | ✓ | **PASS** |
| | B0→B3 | 22 | 1.000 | 526 | 527 | 1.002 | ✓ | **PASS** |
| | B0→R | 23 | 1.000 | 568 | 525 | 0.924 | ✓ | beside |
| | **B2→B3** | 23 | **1.000** | 501 | **587** | **1.172** | ✓ | beside |

**The iteration bound passes on every deck and every accepted pair.** This is a change from
V2, where lad's B0→B3 median of 1.27 failed the bound and fired the plan's per-deck clause.

Three things must be said beside that pass:

**(i) A pre-declared prediction was refuted, and the sharp form of the result is stronger
than the median it was declared on.** The plan asked for a *median*; the records support an
exact, per-seed statement.

*Caption: per-seed identity of optimiser iteration counts between B2 (verified outer loop)
and B3 (trust), both primed, over both-converged pairs; objective bit-identity beside. The V2
column is the same comparison with the prime OFF on both sides, recomputed from V2's records.
Iteration counts are integers, so "identical" here is exact, not "within noise".*

| deck | pairs | iterations identical | objf bit-identical | V2, prime off |
|---|---|---|---|---|
| `large_tokamak_nof` | 22 | **22/22** | 20/22 | — |
| `low_aspect_ratio_DEMO` | 11 | **11/11** | 0/11 | nearest-rank 1.40; sums 209 → 247 over 10 pairs |
| `st_regression` | 23 | 16/23 | 0/23 | — |

On lad the per-seed vectors are *literally the same list* — B2 and B3 both run
[13, 15, 36, 21, 14, 65, 10, 18, 16, 12, 10]. And V3's B2 reproduces **V2's B2 seed for seed**
on the 10 shared seeds, while V2's B3 was a different vector entirely
([12, 19, 15, 12, 14, 14, 78, 39, 24, 20] — 78 iterations where B2 took 18). Since
`PROCESS_ARCH_PRIME` is the only run-affecting difference between V2's and V3's B2/B3
environments (verified by diffing `env_for`), this separates cleanly:

- **The prime is inert in B2**, which has the outer verification loop and therefore already
  repaired the stale first-call read by re-sweeping.
- **The prime is decisive in B3**, which has no outer loop and without it carried the
  first-call error into the optimisation at an erratic cost.
- **Under the prime, removing the outer verification loop costs exactly nothing on both
  pulsed decks.** Its only remaining job there was repairing the deficit the prime prevents.

**Not on `st_regression`**, the k = 0 deck: 7 of 23 seeds differ, B3 worse on 6 (38→59,
47→61, 37→72, 33→47) — the 501 → 587 sum in the table above. On the deck with nothing lifted
or pinned, the outer loop still does work the prime does not account for. **Hypothesis,
untested:** on the pulsed decks the pin removes the burn-time coupling and the prime removes
the first-wall carrier, together leaving nothing to verify; st has no pin, so another
coupling still needs it. Which coupling is not identified here, and st's 2 hops on B2→B3 mean
some of those 7 differences may be attractor selection rather than repair work.

**The original pre-declared statement.** The plan declared: lad's **B2→B3 stays
elevated at ≈ 1.40** under the nearest-rank construction, *"because the carrier is inert
after call 1"*; and — naming the alternative in advance — *"if it instead falls to ≈ 1.0, the
first-call deficit **was** the mechanism on lad and A35's inertness reasoning is refuted
there."* **Measured: 1.000, on both the median and the sum (230 vs 230), over 11 pairs.**
By the plan's own words, **A35's inertness reasoning is refuted on lad.** The prime — which
is present on both sides of B2→B3 and therefore cannot be the difference between them — has
removed the elevation that the unprimed V2 ladder showed. The first-call deficit was the
mechanism.

**(ii) lad's median and sum still disagree in direction, and V2's finding reproduces
exactly.** B0→B1's median of 0.833 ("a 17 % reduction per typical seed") sits against a sum
ratio of **1.009** (228 → 230) — the direction flag fires, as designed. These answer
different questions: the median answers *what happens to a typical seed*, the sum answers
*what does the campaign cost*. The campaign cost slightly more. That the V2 numbers
reproduce to the digit at a different commit is itself a determinism check.

**(iii) st's B2→B3 hides a 17 % iteration increase behind a median of 1.000.** Over its own
23 contributing pairs the trust step takes 501 → **587** iterations. The median is blind to
it because the increase is concentrated in a few seeds. B2→B3 is outside the acceptance rule
by declaration, so this changes no verdict — but a reader told only "median 1.000" would be
misled, which is exactly why the amendment requiring summed iterations exists.

### 5.4 Lift closure (check 3)

*Caption: `burn_time_residual` (constraint 93's own function) at exit, over accepted seeds,
per lifted arm. This is the pin's inconsistency: how far the lifted variable sits from the
value the coupling would have produced. `st_regression` is a k = 0 deck — nothing to lift.*

| deck | arm | n accepted | median abs residual (s) | max (s) |
|---|---|---|---|---|
| `large_tokamak_nof` | B1 / B2 / B3 | 22 | 1.659e-5 | 1.600e-3 |
| `low_aspect_ratio_DEMO` | B1 / B2 / B3 | 11 | 5.480e-6 | 4.756e-5 |
| `st_regression` | — | 0 | — | — (k = 0, inactive) |

The lift closes to ~1e-5 s on a burn time of order 1e4 s — a relative inconsistency of
~1e-9 (tok) and ~1.6e-10 (lad). **Note the tension with §5.2:** the lift closes to 1e-9
relative, yet it is the rung that moves lad's objective by 4e-7 relative. A residual small in
its own units is not therefore small in its effect on the optimum.

### 5.5 Cost (check 4): identical-success-set node-call sums, solve phase

*Caption: total model-node executions in the **solve** phase (everything before
`write_output_files`), summed over the identical seed set named in each block, one column per
arm. Two sets are published: identical-**ok** and identical-**converged**. Ratios are against
B0. `model_calls` is the number of dispatch sweeps, not node executions — the two diverge by
design in the block arms. Node calls are the declared cost statistic; timings appear in §7
and are never evidence.*

| deck | set | n | R | B0 | B1 | B2 | B3 | **B3/B0** |
|---|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | ok = converged | 22 | 912 555 | 935 340 | 942 522 | 834 951 | 598 124 | **0.639** |
| `low_aspect_ratio_DEMO` | ok | 20 | 1 970 913 | 1 917 384 | 1 356 537 | 1 223 922 | 881 814 | **0.460** |
| | converged | 11 | 1 869 378 | 1 814 967 | 1 255 695 | 1 134 299 | 817 436 | **0.450** |
| `st_regression` | ok | 25 | 3 677 478 | 3 184 377 | — | 2 776 339 | 1 856 724 | **0.583** |
| | converged | 22 | 2 791 089 | 2 332 155 | — | 1 979 117 | 1 243 161 | **0.533** |

**The partitioned, trust-stepped, primed architecture executes 36–55 % fewer model-node
evaluations than the flat baseline, on every deck and under both set constructions.** These are
sums over the seed set, so the claim is about **total work over the campaign**, and at that
level the sign is uniform with a margin far larger than anything in the noise. **It is not
uniform per run**: §5.5.1 resolves the same quantity run by run and finds B3 executing more
than B0 on 2 of 20 lad runs, 1 of 25 st runs, and — in module M2 alone — 1 of 22 tok runs. The
deck-level ratio is not a statement about every start.

**Against PROCESS as shipped, which is a different and often larger number.** B0 is not R:
they differ by the stopping rule alone, and that is not free — R→B0 measures 0.976 / 1.028 /
1.155 by deck. So "cheaper than the predicate-matched flat baseline" and "cheaper than the
code as shipped" are different claims, and a deployment question wants the second.

*Caption: B3's node-call ratio against both anchors, per deck and set. B3/B0 isolates the
architecture at a matched stopping rule and is the ladder's number; B3/R is the end-to-end
change a user switching from shipped PROCESS would see, and conflates the architecture with
the stopping-rule change. Both come from the same committed sums above.*

| deck | set | n | R→B0 | **B3/B0** | **B3/R** |
|---|---|---|---|---|---|
| `large_tokamak_nof` | ok = converged | 22 | 0.976 | 0.639 | **0.655** |
| `low_aspect_ratio_DEMO` | ok | 20 | 1.028 | 0.460 | **0.447** |
| | converged | 11 | 1.030 | 0.450 | **0.437** |
| `st_regression` | ok | 25 | 1.155 | 0.583 | **0.505** |
| | converged | 22 | 1.197 | 0.533 | **0.445** |

On `st_regression` the two anchors differ by 9 percentage points: the predicate-matched
baseline is already 15–20 % cheaper than shipped PROCESS there, so measuring against B0
**understates** what a user would gain. On `large_tokamak_nof` it goes the other way by 1.6
points. Neither ratio is more correct; they answer different questions, and the report's
headline uses B0 because that is the anchor the ladder decomposes against.

*Caption: sweeps and prime calls per arm over the ok set — the accounting that explains how
node calls fall while dispatch sweeps rise. `prime/sweep` verifies the prime's contract (one
`set_fw_geometry()` per sweep); `prime/node` is the cost D19 excludes from the ratios above,
named here per trap T11. Both are **counts**, never costs.*

| deck | arm | node calls | dispatch sweeps | prime calls | prime/sweep | prime/node |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | B0 | 935 340 | 44 606 | 0 | — | — |
| | B2 | 834 951 | 159 140 | 159 118 | 0.9999 | 0.191 |
| | B3 | 598 124 | 117 347 | 117 325 | 0.9998 | 0.196 |
| `low_aspect_ratio_DEMO` | B0 | 1 976 331 | 94 174 | 0 | — | — |
| | B3 | 881 814 | 170 118 | 170 098 | 0.9999 | 0.193 |
| `st_regression` | B0 | 3 184 377 | 151 712 | 0 | — | — |
| | B3 | 1 856 724 | 423 212 | 423 187 | 0.9999 | 0.228 |

The prime's contract holds exactly: **one prime call per dispatch sweep**, to four decimal
places, in every block arm on every deck.

#### 5.5.1 Per-module breakdown, aligned to the collapsed DSM

Rewritten twice on 2026-09-07, in step with §4.5; module scope and the `vacuum`
reconciliation are given there.

*Caption: **module sweeps per run** over each deck's identical-**ok** seed set, as the mean with
its **seed bracket** [min, max]; a bare integer means every run agreed exactly. These cells are
already per run — an optimisation executes ~2 000 sweeps, against a warm entry evaluation's ~5.
`models` is the module's DSM row count, so **total calls = Σ sweeps × models**. **The per-module
ratio columns are the result** (unit-invariant, §4.5); the total is bracketed over `vacuum`'s
unknown row count (§4.5, trap T9). The last two columns give the ratio's **per-run
distribution**, which the pooled ratio does not show: the median run, its range, and the number
of runs in which B3 executes **more** than B0. **Denominator note (trap T11):** these cells come
from the per-node census, which counts the solve phase **plus** the output pass — the output
pass runs every node once, so it adds exactly **one sweep to every module row, in every arm**;
§5.5's table sums `node_calls_solve_phase` and excludes it. It is symmetric across arms and
cancels from no ratio it appears in. From `v3_report_analysis.py --tables`.*

**`tok`** (n = 22)

| module | models | R | B0 | B1 | B2 | B3 | B3/B0 | per-run med [min, max] | runs B3 > B0 |
|---|---|---|---|---|---|---|---|---|---|
| M1 | 24 | 1978 [1758,2280] | 2028 [1793,2396] | 2043 [1823,2383] | 2024 [1809,2366] | 1391 [1243,1626] | **0.686** | 0.692 [0.598, 0.800] | 0/22 |
| M2 | 10 | 1978 [1758,2280] | 2028 [1793,2396] | 2043 [1823,2383] | 2397 [2141,2800] | 1764 [1575,2060] | **0.870** | 0.877 [0.762, **1.014**] | **1/22** |
| M3 live | 11 | 1978 [1758,2280] | 2028 [1793,2396] | 2043 [1823,2383] | 2177 [1946,2547] | 1544 [1380,1807] | **0.761** | 0.768 [0.658, 0.888] | 0/22 |
| `vacuum` | 1 | 1978 [1758,2280] | 2028 [1793,2396] | 2043 [1823,2383] | 4 | 4 | **0.002** | 0.002 [0.002, 0.002] | 0/22 |
| PULSE | 1 | 1978 [1758,2280] | 2028 [1793,2396] | 2043 [1823,2383] | 643 [575,751] | 643 [575,751] | **0.317** | 0.320 [0.277, 0.370] | 0/22 |
| FF | 5 | 1978 [1758,2280] | 2028 [1793,2396] | 2043 [1823,2383] | 4 | 4 | **0.002** | 0.002 [0.002, 0.002] | 0/22 |
| **total calls** | 52 | 102 868 | 105 432 | 106 241 | 97 171 | 68 676 | **[0.651, 0.666]** | 0.657 [0.568, 0.760] | 0/22 |

**`lad`** (n = 20)

| module | models | R | B0 | B1 | B2 | B3 | B3/B0 | per-run med [min, max] | runs B3 > B0 |
|---|---|---|---|---|---|---|---|---|---|
| M1 | 24 | 4696 [528,31870] | 4568 [538,31216] | 3233 [526,17174] | 3190 [525,16951] | 2183 [360,11597] | **0.478** | 0.655 [0.084, **4.127**] | **2/20** |
| M2 | 10 | 4696 [528,31870] | 4568 [538,31216] | 3233 [526,17174] | 3779 [614,20079] | 2772 [449,14725] | **0.607** | 0.833 [0.106, **5.240**] | **2/20** |
| M3 live | 11 | 4696 [528,31870] | 4568 [538,31216] | 3233 [526,17174] | 3543 [569,18844] | 2537 [404,13490] | **0.555** | 0.750 [0.097, **4.801**] | **2/20** |
| `vacuum` | 1 | 4696 [528,31870] | 4568 [538,31216] | 3233 [526,17174] | 4 | 4 | **0.001** | 0.001 [0.000, 0.007] | 0/20 |
| PULSE | 1 | 4696 [528,31870] | 4568 [538,31216] | 3233 [526,17174] | 1022 [171,5421] | 1022 [171,5421] | **0.224** | 0.311 [0.039, **1.929**] | **2/20** |
| FF | 5 | 4696 [528,31870] | 4568 [538,31216] | 3233 [526,17174] | 4 | 4 | **0.001** | 0.001 [0.000, 0.007] | 0/20 |
| **total calls** | 52 | 244 174 | 237 546 | 168 108 | 154 353 | 109 074 | **[0.459, 0.470]** | 0.629 [0.080, 3.965] | **2/20** |

**`st`** (n = 25; no B1, and `pulse` is post-solve rather than an executing PULSE block)

| module | models | R | B0 | B2 | B3 | B3/B0 | per-run med [min, max] | runs B3 > B0 |
|---|---|---|---|---|---|---|---|---|
| M1 | 24 | 7008 [387,39952] | 6068 [423,31812] | 6430 [416,35251] | 4313 [299,27946] | **0.711** | 0.715 [0.165, **3.344**] | **1/25** |
| M2 | 10 | 7008 [387,39952] | 6068 [423,31812] | 6673 [419,37010] | 4511 [302,29803] | **0.743** | 0.724 [0.169, **3.567**] | **1/25** |
| M3 live | 11 | 7008 [387,39952] | 6068 [423,31812] | 6519 [406,35554] | 4347 [289,27865] | **0.716** | 0.729 [0.168, **3.335**] | **1/25** |
| `vacuum` | 1 | 7008 [387,39952] | 6068 [423,31812] | 4 | 4.12 [4,5] | **0.001** | 0.001 [0.000, 0.009] | 0/25 |
| PULSE | 1 | 7008 [387,39952] | 6068 [423,31812] | 4 | 4.12 [4,5] | **0.001** | 0.001 [0.000, 0.009] | 0/25 |
| FF | 5 | 7008 [387,39952] | 6068 [423,31812] | 4 | 4.12 [4,5] | **0.001** | 0.001 [0.000, 0.009] | 0/25 |
| **total calls** | 52 | 364 401 | 315 561 | 292 774 | 196 457 | **[0.623, 0.636]** | 0.627 [0.144, 2.935] | **1/25** |

**Read the per-module columns; the totals are for reconciliation only.** Four things they
show that no total can:

- **The improvement is not per-run universal, and the pooled ratios hide that entirely.** On
  lad, **2 of 20 runs** have B3 executing *more* than B0 — up to 4.1× in M1, 5.2× in M2 and
  4.8× in M3. On st, **1 of 25**. Even on tok, uniform on the total, **one run's M2 comes out
  at 1.014**. The per-run medians also sit well above the pooled ratios on lad (0.629 against
  0.459), because the pooled figure is a total-work statistic dominated by a few very long runs
  (B0 sweeps per run: median ≈ 2 800, max 31 216). Both statistics are legitimate and they
  answer different questions; publishing only the pooled one asserted a uniformity the runs do
  not have.
- **B2 does not reduce model work at all — it increases it.** On tok B2 costs **18 % more in
  M2** and 7 % more in M3 than B0; on st it is worse in **every** live module (1.060 / 1.100 /
  1.074). Its total comes out below B0 only because FF and PULSE collapse. The verification
  loop's second pass is genuinely re-running the blocks. B3 removes it and every live module
  drops: 0.686 / 0.870 / 0.761 (tok), 0.478 / 0.607 / 0.555 (lad), 0.711 / 0.743 / 0.716 (st).
- **Flat arms have uniform sweeps across modules; partitioned arms do not.** R, B0 and B1 read
  the *same* number in every module row — a flat sweep executes everything once — so their
  ratios are 0.976 / 1.028 / 1.155 (R→B0) and 0.708 (B1 on lad) in every module alike. That
  uniformity is a free consistency check on the module accounting, and it holds exactly.
- **The feed-forward set is where the intervention is most extreme and least interesting.**
  `costs`, `water_use` and `vacuum` (and `pulse` on st) fall from every sweep to about four
  executions per optimisation — a factor of 500–1500. That is most of the headline saving in
  fractional terms and none of it in difficulty: nothing live reads them, so hoisting them is
  bookkeeping. **M3 is where the partition does real work**, and M2, the smallest live module,
  is where it does least.

The unit dependence of the total is smaller here than in Phase A (tok 0.640 node-weighted
against 0.651–0.666 model-weighted, lad 0.460 against 0.459–0.470, st 0.583 against
0.623–0.636) because the sweep counts are more balanced across modules inside an optimisation
than at a δ = 0.10 warm entry; but on st it is still four points.

**Two of the five DSM blocks execute nothing and appear in no row.** `FF`'s DSM rows are
swept in every arm but its only member with `in_call_models_once: false` never runs; st's
`PULSE` block is swept 570 times per run after its member left for post-solve. Both are pure
per-sweep overhead (§7, I-20) and are invisible to every node-call statistic in this report —
which is exactly why they went unnoticed.

### 5.6 Reading the three decks together: they do not optimise the same thing

Added 2026-09-07 at the user's request. Every cross-deck comparison above implicitly treats
the decks as three samples of one experiment. They are not: **each optimises a different
figure of merit**, and on one deck the objective *is* the quantity the ladder lifts.

*Caption: problem definition per deck, from each run's own record (`i_figure_merit`, `nvar`,
`n_constraints`) against the `FiguresOfMerit` enum in `process/data_structure/numerics.py:88`.
A negative `i_figure_merit` means maximise.*

| deck | `i_figure_merit` | objective | sense | vars | constraints (eq / ineq) | pulsed |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 1 | plasma major radius R₀ | minimise | 20 | 26 (3 / 23) | yes |
| `low_aspect_ratio_DEMO` | −14 | **pulse length `t_plant_pulse_burn`** | maximise | 19 | 25 (4 / 21) | yes |
| `st_regression` | −5 | fusion gain Q | maximise | 14 | 18 (3 / 15) | no (k = 0) |

**The consequence that matters: on `low_aspect_ratio_DEMO`, the burn-time lift promotes the
deck's own objective into the design vector.** Constraint 93 and iteration variable 178 are
`t_plant_pulse_burn` — which is exactly what lad maximises. So B0 computes the burn time
through the MDA and reports it as the objective; B1/B2/B3 let the optimiser *choose* it and
enforce consistency through c93. Those are not the same optimisation problem. On tok the same
switch is a pure architectural change (burn time is a constraint-side quantity, not the
objective); on st the switch is absent entirely.

**This is why B0 is the odd arm out on lad, and why B1 = B2 = B3 there.** §5.2 localised lad's
check-1 failure to B0→B1 by measurement; the objective table says why that rung and no other.

**But the lift does not bias lad's objective — it re-selects among nearby optima.** Per seed,
B1 is strictly better than B0 on 6 and worse on 5, with magnitudes from 2.6e-11 to 1.3e-4:

| seed | B0 | B1 | B1 − B0 |
|---|---|---|---|
| 1 | −0.405823482872 | −0.405951259711 | **−1.278e-4** (better; the one cluster hop) |
| 13 | −0.406240740695 | −0.406239868231 | +8.725e-7 (worse) |
| 11 | −0.406296108371 | −0.406295596151 | +5.122e-7 (worse) |
| 5 | −0.405947838712 | −0.405947838738 | −2.606e-11 (better) |

So lad's failure is **not** "the architecture computes a different answer". It is "the lift
changes which of ten densely-packed local optima the optimiser selects", in both directions.

**A construction limit this exposes, which applies to every deck.** The clustering gap is
`CLUSTER_GAP_FLOOR_FACTOR × OBJF_FLOOR_REL = 10 × 1e-6 = 1e-5`, while check 1's acceptance
floor is `1e-6` — **the clusters are ten times coarser than the tolerance they are meant to
help interpret.** Two runs in the same cluster may legitimately differ by up to ~1e-5, and
lad's widest cluster is 8.4e-6 across. So lad's within-cluster p90 of 1.26e-6 is entirely
consistent with "same cluster, different optimum inside it", and the within-cluster
construction **cannot** separate "same optimum" from "different optimum less than 1e-5 away".
Both constructions were pre-declared and neither is wrong; but a reader must not take
within-cluster agreement as proof of a shared optimum. On a deck whose optima are denser than
1e-5, check 1 as constructed has no resolution.

**The flat-direction reading, and what the argmax census supports.** §5.2.2's location
diagnostic names which variable differs most per pair. Set against each deck's objective:

| deck | objective | argmax of the point difference (B0→B3) | point median |
|---|---|---|---|
| tok | minimise R₀ | `f_nd_alpha_thermal_electron` (12/22), `f_nd_impurity_electrons(13)` (5/22) | 4.6e-2 |
| lad | maximise burn time | `j_cs_flat_top_end` (7/11), `dr_cs` (2), `f_j_cs_start_pulse_end_flat_top` (2) | 5.4e-6 |
| st | maximise Q | `dr_shld_inboard` (14/22), `dr_tf_nose_case` (6/22) | 4.5e-6 (p90 0.21) |

**Hypothesis (mine, not pre-declared):** the variables that differ most between arms are the
ones each deck's objective is least sensitive to. Radial-build thicknesses barely move Q, and
st's points differ by up to 100 % in exactly those. Composition fractions barely move R₀, and
tok's differ by 4.6 % in exactly those. lad, whose objective is set by CS flux swing, differs
most in the CS variables — but by only 5e-6, because its objective *does* depend on them
tightly. This is consistent across all three decks and it is n = 3; it is a pattern to test,
not a finding.

**The hoist set is DERIVED from the objective, not assumed — a methodological strength worth
naming.** `caller.py:_predicate_read_fields` does an AST walk for loaded `data.<ns>.<field>`
names, **narrowed to the active figure of merit's own branch** of `objective_function`, and
`resolved_hoist_tails` routes each hoisted node to the pre- or post-predicate slot according
to whether the predicate layer reads something it writes. So the schedule adapts to the
objective rather than presuming one. The three decks resolve differently, and correctly:

*Caption: resolved hoist tails and the resulting execution counts, B3 `start000`. "Block
sweeps" is how often the block was visited; "node executions" is how often the model actually
ran — they are different quantities, and their divergence on st is the point.*

| deck | objective | `pulse` routed to | PULSE block sweeps | `pulse` node executions |
|---|---|---|---|---|
| tok | minimise R₀ | **pre-predicate** | 0 | **663** (once per evaluation) |
| lad | maximise burn time | **pre-predicate** | 0 | 663-equivalent |
| st | maximise Q | **post-solve** | **570** | **5** |

On the pulsed decks the predicate layer reads what `pulse` writes, so it must run before the
predicate — it leaves the block but still executes once per evaluation. On st nothing in the
predicate reads the burn time (Q does not depend on it, and k = 0), so `pulse` falls all the
way through to post-solve and runs **5 times in the entire optimisation**.

**Which exposes a small real defect: st's PULSE block sweeps 570 times executing nothing.**
The block survives in the schedule after its only member has been hoisted out of it, so those
are no-op visits — the DSM register's V12 trap (`in_call_models_once: false`) in live form.
They cost no model evaluations, which is why no cost table shows them and why no result here
moves; they are wasted block-loop iterations, and they are worth removing.

*(Correction, 2026-09-07: an earlier draft of this section stated the inverse — that st's
PULSE block was the only live one. It is the only one that sweeps, and the only one that
executes nothing. Caught by reading `node_census` against `inner_sweeps_by_block`.)*

**What this does to the cross-deck comparisons.** The cost result (§5.5) is unaffected: node
calls are counted per deck against that deck's own baseline. The correctness results are not
comparable in the way a single table implies — tok's PASS, lad's FAIL and st's split verdict
are three different questions about three different optimisation problems, and only st asks
the partition-only question the experiment was designed around.

## 6. I-17: the Phase A → Phase B transfer, and what `sweeps_per_eval` says

The plan amended §5 before the campaign to record that V2's A→B transfer **over-predicted
B3's saving on all three decks** (+22.6 / +6.0 / +41.8 %), that the sign was uniform across
every construction, and that V2's declared failure condition *did not select the decks where
the transfer failed*. It bound this campaign to three things: no V3 number derived through
the transfer, the per-call ratio reported as a mechanism and an upper bound only, and the
per-deck error republished beside V3's own numbers. All three are honoured — §5.5's figures
are measured node-call ratios throughout.

*Caption: Phase A's per-call prediction against Phase B's realised end-to-end ratio, per deck
and per cost-set construction. Over-prediction is (realised / predicted − 1); positive means
Phase A promised more saving than the optimisation delivered. **No number elsewhere in this
report is derived through this table.***

| deck | Phase A A0→A1 | set | n | realised B0→B3 | over-prediction | V2's figure |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 0.5217 | ok = converged | 22 | 0.6395 | **+22.6 %** | +22.6 % |
| `low_aspect_ratio_DEMO` | 0.5680 | ok | 20 | 0.4599 | **−19.0 %** | +6.0 % |
| | | converged | 11 | 0.4504 | **−20.7 %** | |
| `st_regression` | 0.5016 | ok | 25 | 0.5831 | +16.2 % | +41.8 % |
| | | converged | 22 | 0.5331 | **+6.3 %** | |

**The uniform sign is gone.** tok reproduces its V2 over-prediction to the decimal; st's
shrinks from +41.8 % to +6.3 %; and **lad reverses — Phase A now under-predicts by 20 %.**
Whatever V2's "systematic" transfer error was, it is not systematic in V3.

**The pre-declared hypothesis, and its verdict.** §5 declared: *"if in-loop evaluations are
systematically shorter than Phase A's and the block arm's per-sweep advantage shrinks with
evaluation length, the hypothesis is supported; if the distributions are comparable and the
gap persists, it is refuted."* V2 could not test this — nothing recorded the in-loop sweep
distribution. V3 does.

*Caption: sweeps per optimiser-driven evaluation, same unit on both arms, from the driver
instrument (`SWEEPS_PER_EVAL_HIST`). Phase A means are over 25 δ-perturbed single
evaluations; Phase B means are over the whole campaign, with the binned total cross-checked
against the summed evaluation count in every cell (**all True**).*

| deck | Phase A A0 | Phase A A1 | Phase B B0 | Phase B B3 | A0/B0 | A1/B3 |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 5.52 | 13.16 | 3.29 | 8.33 | 1.68 | 1.58 |
| `low_aspect_ratio_DEMO` | 5.00 | 12.88 | 3.35 | 8.35 | 1.49 | 1.54 |
| `st_regression` | 5.84 | 14.84 | 3.38 | 9.00 | 1.73 | 1.65 |

**The first clause is confirmed; the hypothesis as an explanation is not.** In-loop
evaluations *are* systematically shorter than Phase A's — by a factor of 1.5–1.7, on every
deck. But they are shorter by **nearly the same factor in both arms**, so the effect very
largely cancels in a *ratio*. Quantitatively, the residual sweep-length asymmetry
(A0/B0 ÷ A1/B3) predicts an over-prediction of +6.1 % on tok, +4.8 % on st and −3.4 % on lad,
against measured +22.6 %, +6.3 % and −20.7 %. It accounts for st almost exactly, about a
quarter of tok, and has the right sign but a sixth of the magnitude on lad.

**Verdict: partially supported, and not the dominant term.** Phase A's evaluation is
genuinely a different and harder object than an in-loop one, as suspected — but that
difference is not what breaks the transfer. The cause is elsewhere, and I-17 stays open on
the user's list with the campaign's `sweeps_per_eval` records now available for it.

A mechanism finding worth recording for that investigation: on st, B3's sweep histogram is
**B2's histogram shifted down by exactly 4**, bin-count for bin-count (137, 171, 116, 59,
41 …). The outer verification loop costs a flat 4 sweeps per evaluation; the inner block work
is untouched by removing it.

## 7. Timing (context only — never evidence)

Per CLAUDE.md and D17/I-10, no conclusion in this report rests on a timing. I-10 measured a
wall-clock-derived cost weight moving 6.4 % → 4.4 % across runs of identical code. These are
published because omitting them would misrepresent §5.5, not because they decide anything.

*Caption: serial timing block, 3 repetitions per cell, median and full range, first run
discarded for JIT. Node-call ratios from §5.5 (identical-converged where the two sets differ)
are set beside for comparison.*

| deck | arm | median (s) | range (s) | wall vs B0 | **node calls vs B0** |
|---|---|---|---|---|---|
| `large_tokamak_nof` | R | 14.05 | 13.97 – 14.10 | 0.626 | 0.976 |
| | B0 | 22.44 | 22.35 – 22.61 | 1.000 | 1.000 |
| | B1 | 23.20 | 22.79 – 23.22 | 1.034 | 1.008 |
| | B2 | 36.60 | 36.40 – 36.65 | 1.631 | 0.893 |
| | **B3** | 24.11 | 24.09 – 24.19 | **1.074** | **0.639** |
| `low_aspect_ratio_DEMO` | B0 | 45.75 | 44.89 – 46.53 | 1.000 | 1.000 |
| | B1 | 36.18 | 36.16 – 36.96 | 0.791 | 0.692 |
| | B2 | 58.34 | 57.43 – 58.78 | 1.275 | 0.625 |
| | **B3** | 38.74 | 38.50 – 38.80 | **0.847** | **0.450** |
| `st_regression` | B0 | 22.47 | 22.22 – 22.63 | 1.000 | 1.000 |
| | B2 | 31.83 | 31.31 – 32.51 | 1.417 | 0.849 |
| | **B3** | 21.61 | 21.34 – 22.07 | **0.962** | **0.533** |

**This is the most important caveat in the report.** A 36–55 % reduction in model-node
executions buys between **−7 % and +15 %** of wall clock, and on `large_tokamak_nof` it goes
**backwards**: B3 is slower than B0 while executing 36 % fewer node evaluations. B2 is worse
still — 27–63 % slower everywhere.

The accounting in §5.5 says why. B3 executes 2.6–2.8× as many *dispatch sweeps* as B0
(117 347 vs 44 606 on tok), and each sweep carries fixed per-sweep overhead — dispatch, the
block-loop machinery, the convergence predicate, and one prime call — that the node-call
statistic does not see. The architecture trades many cheap sweeps for few expensive ones, and
at PROCESS's current per-node cost the trade is roughly break-even in time.

Two honest readings, and I will not adjudicate between them on this evidence: either the
node-call reduction is real and the implementation's per-sweep overhead is an engineering
problem yet to be paid down, or model-node executions are the wrong cost unit for this
architecture. The ranges above are tight (worst spread 3.6 %), so this is not measurement
noise — but three repetitions of one serial block is not a performance study either.

## 8. Critical assessment

**What this campaign establishes.**

1. **The prime closes the FirstWall→Build carrier.** This is the strongest result here. Phase
   A's headline check fails for A1u by five to six orders and passes for A1 on all three
   decks, with A1 bit-identical to the flat control on st and exactly zero on lad. It costs
   zero additional model-node executions. The mechanism was predicted, implemented as a
   method-level hoist, gated four ways (G1/G2/G3/G3c), and then confirmed by a campaign that
   was specified before it ran.
2. **A pre-declared prediction was refuted, and the plan named the consequence in advance.**
   lad's B2→B3 was predicted at ≈ 1.40 and measured 1.000. A35's inertness reasoning is
   refuted on lad, by the plan's own stated criterion. An experiment that can only confirm
   itself is not measuring anything; this one could not.
3. **The partitioned architecture executes 36–55 % fewer model-node evaluations**, uniformly
   across decks and set constructions, while passing the iteration bound everywhere.

**What it does not establish, and what argues against it.**

4. **The node-call win does not currently reach wall clock** (§7). This is the single largest
   threat to the practical claim, and it is not resolved by anything here.
5. **lad's objective genuinely disagrees, and the lift is responsible.** check 1 fails on lad
   at the p90 by a factor of 1.26, survives hop removal, and localises to B0→B1. The lift is
   the least exotic rung on the ladder and the one carried over unchanged from V2. It
   deserves scrutiny that this campaign did not give it.
5a. **Check 1 constrains optimality, not location, and the campaign shows how far apart those
   can be** (§5.2.2). On tok the objective agrees to 2.8e-11 while the design point moves
   4.6 % at the median and 44 % at the worst; on st the objective agrees to 1e-13 while some
   pairs' points differ by 100 %. The experiment therefore supports "these architectures find
   optima of equal quality" and **does not** support "these architectures produce the same
   machine". No verdict here rests on location — D6 forbids gating on it — but no reader
   should infer location agreement from a check-1 PASS. The mitigating control is that st's
   R→B0, a stopping-rule change alone, relocates the point just as much, so this is deck
   non-identification rather than an architectural defect. A design study using this
   architecture would still need to know it.
6. **The whole-state audit tells a different story from the restricted one, and the
   restricted statistic is the declared one.** A1u and A1 whole-state residuals are
   essentially identical (tok 2.4353 vs 2.4353; lad 0.1816 both; st 0.2575 both) against A0's
   6.3e-10 / 0 / 5.4e-9. The prime does nothing for whole-state, because the movement lives
   entirely in the post-solve tail — **`costs.*`, `water_use.*` and `vacuum.*`, plus
   `fwbs.life_blkt` and `physics.wtgpd`, which `costs` writes** — evaluated once per run by
   design rather than every sweep, and excluded from the restricted set by declaration.
   *(Corrected 2026-09-07: an earlier draft named only `costs.*` and `water_use.*`; the
   excluded set is five namespaces, every one nonzero in 25/25 block-arm runs on every deck,
   `vacuum.*` at p90 0.068 / 0.097 / 0.091 — §4.5's stakes table.)* This is the designed signature of the post-solve lift and not a defect; G4's
   teeth show the exclusion behaves in both directions. But it means **the headline Phase A
   result rests entirely on the correctness of A38's exclusion set.** If that set is wrong,
   the headline is wrong. It is gated, not proven.
6a. **The three decks optimise three different figures of merit, and the objective is
   perfectly confounded with the structural variable** (§5.6, added 2026-09-07). D17 selected
   decks by architecture property — two pulsed (k = 1), one steady (k = 0) — and the
   objectives came attached to them. The result is that `st_regression` is *simultaneously*
   the only k = 0 deck, the only deck the lift does not touch, the only deck whose objective
   is fusion gain, and the only deck whose `pulse` node falls through to post-solve. **When st
   behaves differently from the other two, this design cannot say which of those caused it.**
   That is not repairable by analysis; it needs more decks, or one deck run under two
   objectives.
   Three concrete consequences: (i) **the ladder's rung labels are not comparable across
   decks** — "B0→B1, the lift" means lifting a constraint-side quantity on tok, lifting *the
   objective itself* on lad, and nothing at all on st, so every sentence of the form "the lift
   does X" is really three sentences; (ii) **the cross-deck spread in the cost result
   (0.639 / 0.450 / 0.533) must not be read as physics** — the three optimisation problems
   differ in objective, in variable count (20 / 19 / 14) and in constraint count (26 / 25 /
   18); (iii) **I-17 gains a candidate explanation on lad**: Phase A's A1 *pins* the burn time
   to a constant while Phase B's B3 *lifts* it into the optimiser, and on lad that quantity is
   the objective — so the two phases differ far more on lad than on tok or st, and lad is
   exactly where the transfer error reverses sign. Hypothesis, untested.
   **Recorded evidence consistent with (iii), added 2026-09-07:** Phase A's own tally carries a
   `lift_residual_distribution` — `burn_time_residual` at each run's exit — whose median over
   the 25 seeds is **155 s** (tok) and **526 s** (lad) in both block arms, against **0** in the
   flat arm A0. The pin holds both pulsed decks off consistency by construction (its value is
   the reference burn time times the same 1 ± δ stream factor every other component receives),
   so what differs between the decks is not the displacement but *what it displaces* — on lad,
   the objective. It supports (iii)'s mechanism without testing it: §5.4's figure is an
   accepted optimum's exit state, and per-iterate residuals are recorded nowhere.
   **What is not affected:** Phase A's headline (§4) runs a single evaluation with no
   optimiser and no objective in its statistic; and every cost, iteration and check-1 verdict
   is computed within one deck against that deck's own baseline, where the objective is held
   constant. The confound damages cross-deck *synthesis*, not any single deck's comparison.
   **A design strength this exposed, in fairness:** the hoist split is *derived* from the
   active figure of merit by AST walk (`caller.py:_predicate_read_fields`), not assumed, and
   demonstrably resolves three different splits across the three decks. Had it hard-coded one,
   st would hoist `pulse` unnecessarily or lad would hand the optimiser a stale objective.
7. **Two declared definitions reached only one of two implementations** (I-18, I-19). Both
   were caught, but only because the verifier restates definitions independently and because
   the plan was read line-by-line against the records afterwards. I-18 was *my* adjudication
   error, propagated for three days across A41's merge and a campaign launch. The verifier
   earned its keep; the process that let a half-applied adjudication through did not.
8. **The prime's own cost is excluded from every cost ratio by declaration.** §4 and §5.5
   name the excluded quantity (0.19–0.23 prime calls per counted node call) rather than
   leaving the denominator silent, but the ratios in §5.5 would move if a prime call were
   charged as a node call, and nothing here says what it should be charged as.
9. **Denominators are small where the deck is hostile.** lad's B2→B3 verdict rests on 11
   both-converged pairs, and 13 of 25 seeds are invalid in every arm. O2 declined to extend
   N; that decision stands, and so does its consequence.
10. **st's check-1 pass at B0→B3 and fail at B0→B2 differ by hop count on a 4-cluster deck**
    (1 hop vs 4). With a yardstick that itself hops twice, the check is operating close to
    its resolution on this deck. Treating either verdict as a strong statement about the
    architecture would over-read it.

**On the gates.** G1/G2/G3/G3c bound a `process/` tree one instrument-commit older than the
one that ran (§3). I have shown the diff is 41 lines of counters and that G0 re-establishes
neutrality at the campaign commit, and I judge the gap closed — but the clean version of this
experiment re-runs those four gates at the campaign commit, and a future campaign should.

## 9. Scope honesty

- **No robustness claim is made** (deferred by the plan; not a powered campaign).
- **No per-factor attribution is made from the pulsed decks' Phase A numbers** — only
  `st_regression` (k = 0) separates the partition-and-hoist effect from the coupling term.
- **No timing is evidence** for any conclusion (§7).
- **The prime's full-run neutrality is not claimed and was never a gate.** Bit-identity across
  an optimisation is unattainable for any change to sweep 1 of call 1.
- **`MDA_output` runs unchanged in every arm**; `NODE_CALLS_AT_OUTPUT` freezes the solve-phase
  counter at output entry, so output-pass calls are excluded from every published comparison
  symmetrically.
- **The lad B2→B3 refutation is a refutation of A35's *inertness reasoning on lad*,** not of
  A35's carrier measurement, which G3c independently confirmed.
- **No claim is made that the arms reach the same design point.** Check 1 gates optimality
  only; §5.2.2's location diagnostic is published beside it and is gated by nothing (D6).
  The two disagree materially on `large_tokamak_nof` and `st_regression`.
- All numbers are at base commit `c0ae5b28`; nothing measured at `710a75c9` is cited.

## 10. Provenance and reproduction

| | |
|---|---|
| **Base commit** | `c0ae5b28` (frozen; D2) |
| **Campaign commit** | `362c0b47`, `dirty=False` on all 599 records |
| **Analysis commit** | `3a0bb8b1` (`v3_report_analysis.py`) |
| **Plan** | `EXPERIMENT_PLAN.md`, approved by the user at `a164c6cd` |
| **Reproduce** | `/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python arch_surgery/MDA_partitioning_experiment_v3/run_experiment.py` |
| **Re-verify without re-running** | `… python v3_report_analysis.py --teeth` → 144 cells, 0 mismatches, baseline rc=0, 5/5 teeth trip |
| **Raw records** | `arch_surgery/MDA_partitioning_experiment_v3/runs/` (untracked by policy); tallies and `report_analysis.json` are the committed summaries |

**Open items handed on.** I-17 (transfer over-prediction — partially explained, cause still
elsewhere; on the user's list). I-19's within-cluster construction should be added to
`phase_b.py`'s tally as well as the analysis. The lift's role in lad's check-1 failure (§5.2)
is unexamined. The wall-clock gap (§7) is the practical blocker for any claim that this
architecture is faster.
