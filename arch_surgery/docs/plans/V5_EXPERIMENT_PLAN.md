# V5 experiment plan — the partitioned MDA as an existence proof in model-evaluation counts

> **Document status** — **DRAFT · NOT APPROVED as a whole; building of the ruled items authorised 2026-09-29**
> (the user: *"continue with implementation of the v5 changes whilst it runs"*): items 7, 8 (A99), 10 and the
> harness fixes (A98) in progress; the test-set change (DR11), the timers (DR12) and item 5 follow on the driver
> files; §3's tolerance paragraph for `st_regression` awaits A96. Every driver change still needs the user's
> approval per change before merge. Was: **DRAFT · NOT APPROVED. Nothing may be built from it until the user approves.**
> Written 2026-09-29 by task **A95 (v5-plan)** at `7986d408` (the tip of `architecture_surgery`), as a
> writing task: no PROCESS run, no code change, nothing written under any `MDA_partitioning_experiment_v*/`
> folder (A94 is making the V5 copy concurrently). **Its input is
> [`V5_IMPROVEMENT_LIST.md`](V5_IMPROVEMENT_LIST.md)**: every ruling there is the user's and binds this plan,
> and every quantity below is either cited to a list item and a decision row (D29–D34; the queue,
> [`../MASTER_TODO_v2.md`](../MASTER_TODO_v2.md) §2) or marked **[to be declared from A92]** /
> **[to be declared from A93]** — the two tasks running now (A92 (optimisation-path-census): the census over
> whole optimisations and its teeth; A93 (tolerance-phase-b): the optimisation-phase effect of the census set at
> τ = 1e-8). Their results are not guessed here. Where the plan needs a ruling the list does not carry, it is a
> numbered question in §12 with a recommendation, never a settled sentence (protocol §8).
>
> **Form.** V4's `EXPERIMENT_REPORT.md` §1–§3 is the model, at about a third of its length; the vocabulary is the
> harness README §3's (model, driver, node, sweep, coupling state, τ, arm, rung, configuration, seed, teeth,
> tally, construction). Arm names are today's — `AR A0 A1 A2` / `BR B0 B1 B2` (A78 (arm-renames), 2026-09-15);
> a document dated earlier spells them differently (trap T16). The paper this experiment serves is
> `Structuring-fusion-MDAO-with-DSMs/3 results.tex` (read-only from this repository).

---

## 1. Purpose and research questions

**The paper's claim** (list header, 2026-09-29; D29; D33): an existence proof that *the arrangement of solvers
and optimisers alone* — every physics and engineering model byte-identical to the frozen base `c0ae5b28` —
changes the cost of solving PROCESS, **in model-evaluation counts**, because the argument is that the real
impact is for models of higher computational cost. Wall clock goes to the paper's appendix as context with
one quantified sentence in the main text (item 9, D33); the paper keeps its optimiser-iterations table
(item 1). Three configurations is a case study, said in one clause (D29 (3)).

| RQ | question | phase and pair | V5 status |
|---|---|---|---|
| **RQ1** | per-call cost: at matched achieved accuracy, how many model-node evaluations does one MDA solve cost under the partitioned architecture against the flat one? | phase A, δ = 0.10 displaced entries only; the pair is **`A1 → A2` on the pulsed configurations, `A0 → A2` on `st_regression`** (where `A1` is inactive) — the comparison at matched accuracy and the same fixed point (**D34**, the user, 2026-09-29) | kept; the stencil regime is dropped (item 10) |
| **RQ2** | end-to-end cost and correctness: inside a full optimisation, the partitioned architecture's model-node evaluations against the flat control, at the same optimum | phase B, `B0 → B2` with the rungs `B0 → B1 → B2`; `BR → B2` beside | kept; the iteration-multiplier rule retired, `R = ρ × ε` published (item 1) |
| RQ3 | transfer from phase A to phase B | — | **dropped** with the stencil regime (item 10) |
| **RQ4** | the stopping rule: what upstream's objective/constraint test costs against the coupling test | `AR → A0`, `BR → B0` | **columns only**, one sentence of context; no prose section (item 10) |
| RQ5 | the trust step | — | **dropped** (item 10; answered by A43 on V3's records) |

**What does not change** (V4 §2.3): the base commit (D2); the models (D5/D11); correctness on `norm_objf`
plus a feasibility audit, never on iteration variables (D6); the partition from the collapsed DSM (D8); the
three configurations (D17; item 1's D22 note); the reference arm beside the predicate-matched control (D14c,
D18); the prime inside the intervention (D19); every acceptance quantity a count or a bit-comparison and no
conclusion resting on a timing (I-10, T5, D33).

---

## 2. The switch matrix and arms

The matrix is V4's Table 2 with four V5 changes, each stated on its row. The harness composes every arm from
this table and nothing else, every switch cleared first (V4 §3.2). `AR`/`BR` are PROCESS as shipped, every
switch unset. On `st_regression` (steady state, `k = 0`) the rows marked ⁺ are inactive: `A1` composes to
`A0`, `B1` to `B0`, both recorded as skipped.

**Table 1.** *The switch matrix: one column per arm, one row per switch; V5 changes in bold with the list
item that makes them; ⁺ = pulsed configurations only. Rows with a question mark in the margin are the subject
of §12 Q1.*

| | **AR** | **A0** | **A1** | **A2** | **BR** | **B0** | **B1** | **B2** | V5 change |
|---|---|---|---|---|---|---|---|---|---|
| MDA solve | upstream | flat | flat | partitioned | upstream | flat | flat | partitioned | — |
| **stopping rule** | objf/conf | **`c` @ τ** | **`c` @ τ** | **`c` @ τ per block** | objf/conf | **`c` @ τ** | **`c` @ τ** | **`c` @ τ per block** | the test set is the **census-measured feedback set `c`**, not the whole coupling state `y` (item 6, **D32**); τ from the declared rule (§3) |
| block schedule | — | one block | one block | one pass | — | one block | one block | one pass | **resolved once per run** with the deferral sets (item 7, **D31**) |
| arrangement · node (`build` after `physics`) | — | — | — | ✓ | — | — | — | ✓ | — |
| arrangement · method (prime) | — | — | — | ✓ | — | — | — | ✓ | **once per evaluation, before M1**, as pre-processing (item 8); stamped, never counted (D19) |
| deferral `per_call` ⁽?⁾ | — | — | — | ✓ | — | — | — | ✓ | phase A: **the deferred nodes are executed once after convergence and measured** (item 5); whether the flat arms `A0`/`A1` (and `B0`/`B1`) also defer is §12 **Q1** |
| deferral `per_run` ⁽?⁾ | — | — | — | ✓ | — | — | — | ✓ | as above |
| burn time out of the loop ⁺ | — | — | ✓ | ✓ | — | — | ✓ | ✓ | — |
| burn-time owner ⁺ | loop | loop | constant | constant | loop | loop | optimiser | optimiser | — |
| input file ⁺ | committed | committed | committed | committed | committed | committed | lifted | lifted | — |
| output-time loop (`MDA_Output`) | n/a | n/a | n/a | n/a | upstream | upstream | none | none | — |
| predicate mode | — | frozen | frozen | frozen | — | frozen | frozen | frozen | the `mixed` trial is **dropped** (item 10; D30's "or drop it") |

**The rungs** (V4 Table 3, unchanged in what they isolate): `AR → A0` / `BR → B0` the stopping rule
(reported, never accepted on); `A0 → A1` / `B0 → B1` burn-time ownership (and, in phase B only, the
output-time loop); `A1 → A2` / `B1 → B2` the partitioning intervention. **The published pairs (D34, the
user, 2026-09-29):** phase A prints **`A2/A1`** on the pulsed configurations and `A2/A0` on `st_regression`
(where `A1` is inactive) — the ratio of means, the per-run median and the `[min, max]` bracket all on that
pair — because it is the comparison at matched accuracy and the same fixed point (pinning the burn time
moves the plant block's fixed point by 7–10 % of scale on 25/25 pairs, V4 report §5.1); this supersedes the
paper-tables convention of 2026-09-28 (`A2/A0`). Phase B keeps **`B2/B0`**, the designed-architecture
comparison, with the rungs beside and `BR → B2` beside it, never instead.

**Phase A's partitioned arm produces the same information as the flat arms** (item 5, the user 2026-09-28:
*"In v5 it should be in the measurement (it should actually run once)"*): the MDA converged, then every
deferred node executed exactly once, by the run, counted by the census like any other node call. V4's
paper-table charge of 1 by construction (`paper_tables.CHARGED_ONCE`) is retired; the cell is measured. The
user extended this on 2026-09-29 to *all A arms* (list item 6) — for the flat arms this is either their final
sweep (which already computes every node at the converged state) or a deferral in the control too, as A89's
second-pass control was built; **§12 Q1**.

---

## 3. The convergence criterion

**The test set** (item 6, **D32**, the user: *"for v5 I want to use the census feedback variables. The
motivation is that the DSMs are not accurate enough to make this judgement, and suffer from the models not
being strictly functional"*). A loop stops on the components of the coupling state `y` that are **read before
their first write within a sweep of the arm's own execution order**, per block — the read-before-write census
of A89 §7.2 (`rbw_census.py`), measured at run time, not derived from the DSM. On V4's configurations the flat
set has 73–75 components and the blocks 16 / 46–47 / 10 (M1 / M2 / M3) plus 1 in `st`'s `PULSE` block (A89
§7.4). **The DSM feedback set** (75 / 73 / 53; A89 §7.2) is reported beside as a cross-check (DSM validation
V18, V19) and is never a stopping rule: it failed the whole-`y` audit once in 12 runs at τ = 1e-8
(`large_tokamak_nof`, cold `A0`, `costs.coecap` at 1.47e-8; A89 §7.4).

**What the census runs over** — **declared from A92 (optimisation-path-census), merged `7550c285`**: A92
measured the census over 12 whole optimisations (`B0`, `B2`, three configurations, seeds 000 and 001; 23 128
evaluations, 12 200 finite-difference probes, 313 line-search points) and found every component carried on
the optimiser's path in A89's 8-entry set for the twin arm, except four cold-start reads carried only at
evaluation 0 of both seeds (`physics.first_call`, `pf_coil.first_call`, `pf_coil.n_pf_coils_in_group`,
`build.dz_xpoint_divertor`; the first two only on `st_regression`); nothing in the 8-entry sets is absent on
the path. **V5's test set per block is the optimisation-run census union** — the larger set, measured where
the loops run — `coupling_subset_trial/optimisation_path_sets.json`: flat 79 / 78 / 75; `M1` 17; `M2` 50 /
49 / 48; `M3` 10; `PULSE` 1 on st (nof / lad / st). The cold-start components are carried (inert after
evaluation 0; 5 µs each per test). V5's census stage re-derives the sets on the V5 copy by the same rule and
must reproduce these before the campaign; a difference is a result. The census instrument is observation-only:
all 12 censused runs reproduced their campaign records to the `norm_objf` bit.
**A100 (v5-test-set), merged `d624f528`, took the census on the V5 tree** (16 censused optimisations, 16 of 16 reproducing
their twins to the bit): the flat sets are A92's (79/78/75); `M3` carries **two more components than A92 measured** on every
configuration — `build.dr_fw_inboard` and `build.dr_fw_outboard`, the first-wall geometry pair the prime computes, read
before written inside M3's sweep since DR10 moved the prime off the sweep head; a run-constant, inert to every stop, in
the set because the rule says so; and **`B1`'s set is measured** as `B0`'s minus `times.t_plant_pulse_burn` (78/77) —
the optimiser owns the burn time. The union with A92's path sets added nothing. The evaluation arms `A1`/`A2` are bound
by the twin rule and GT measures the bound sets on them directly.

**The tolerance** (item 6's rule, declared in A89 §7.3 before it was measured): VMCON's central-difference
step is h = `epsfcn` = 1e-3, its truncation error O(h²) and function noise ε adds O(ε/h); they balance at
ε ≈ h³ = 1e-9 (Gill, Murray & Wright). **τ is the largest ladder value at which the MDA-induced error of the
objective (relative) and of every normalised constraint (absolute) stays ≤ h³ at every stencil point of the
control, in every configuration.** A89 found **1e-8** on V4's configurations with the census set (at 1e-6 the
error reaches 2.8e-8). **τ = 1e-8, declared** (A93 (tolerance-phase-b), merged `0635dca2`; the user, 2026-09-29:
*"keep the tolerance: failed starts are results"*), re-measured by A89's `--choose-tau` on the V5 copy before the
campaign as a check that the value has not moved. **What A93 measured at this value** (45 whole optimisations,
5 seeds × 3 configurations, paired with V4's campaign records): on the pulsed configurations the census set
leaves the optimiser's path and optimum unchanged in 30 of 30 runs (`norm_objf` within 5.3e-13), the flat
control costs within 5 % of V4's per evaluation, and the partitioned arm's per-evaluation node-call ratio at
matched accuracy is **0.48–0.49** against V4's 0.61 — V4's whole-`y` test at 1e-6 charged the partitioned arm for
sweeps its blocks did not need. On **`st_regression` the trajectory term is not neutral**: the flat control's
path shortens on 3 of 5 seeds, the partitioned arm's lengthens 1.7–4.2× on all 5 and one seed fails at the
iteration cap; A89's ladder shows st as the one configuration where the census-set loop leaves a nonzero
objective residual at 1e-8 (4.9e-11; 0.0 only from 1e-10). **The plan pre-declares** that on `st_regression`
ε may differ from 1 in either direction and that a start lost at τ is a result on the per-arm success table
(§5 B5), never a reason to loosen. **A96 (st-trajectory-ladder), merged, settles the mechanism and the declaration** (the orchestrator under D37,
2026-09-29; for the user's approval on return): the tolerance alone (`B2` whole-`y` at 1e-8) leaves the partitioned
arm on the campaign's path on st's three stable seeds and at its optimum on all five, so the lengthening at 1e-8 is
the census set's; the set effect fades as τ tightens (`B2` census path = campaign 0/5 → 2/5 → 3/5 → 3/5 at
1e-8 / 1e-9 / 1e-10 / 1e-12) and returns where A89's objective residual first reads 0.0 (1e-10); seeds 1 and 2 are
**st's fragile seeds** (the campaign's path in no variant of either arm); seed 1's partitioned census arm changes
basin at 1e-8..1e-10 and holds the campaign's only at 1e-12. **The declared setting stays τ = 1e-8 with the census
set on st** — its trajectory term is pre-declared non-neutral with this mechanism, seed 1's basin change a known
failure mode, and every such start a result on the per-arm success table — and **a supplementary st stage at
τ = 1e-12** (`B0`, `B2`, the census set, the campaign's seed set) is reported beside, labelled supplementary,
the rung where the census loops are exact (A89) and the paths return: the paper's st column can then show the
partitioned cost at matched path as well as at the declared τ. One τ for every converger in every arm and both phases (D23 stands; there is no inner
tolerance). Note: the retry ladder's `epsfcn × 10` attempt would license h³ = 1e-6; τ stays at the first
attempt's value, which is tighter, and no attempt-dependent tolerance exists.

**The fallback criterion (D39, the user, 2026-09-29:** *"please ensure the v5 harness has the option to run the
convergence on the state with the 10e-6 tolerance, like v4 — as a fallback"*). The V5 harness keeps V4's
criterion selectable: the loop's test set is a switch with two values — the **census set at τ = 1e-8** (the V5
default, above) and the block's **whole write set at τ = 1e-6, exactly V4's predicate**. The choice is a
campaign-level setting, one value for every arm and both phases (D23: one tolerance per campaign), stamped in
every record, never mixed within a campaign. GT and the census stage bind the census value only; the
reproduction gate GR is V4's own criterion on the copy and must PASS under the fallback. If the census campaign
leaves too few converged starts to serve the paper, the fallback campaign is the paper's V5 — the user's
decision on return; under D37 the census campaign runs first.

**The accuracy instrument** is unchanged: the **whole-`y` exit audit** — one further full sweep of the whole
model set from the state the solve handed over, restored bit-exact (D25), on the same `frozen` ruler in every
arm, uncharged — with the count of components above τ per run. A narrow test set is licensed only because
the audit is wide: matched accuracy is verified per run on all 840 / 846 / 827 components, never assumed
from the shared τ (V4 §3.6).

**The teeth gate for the test set (GT)** — form **declared from A92**. A92 found that the whole-`y` audit at
τ is not the tooth: dropping the one component that decides the stop (`pf_coil.stress_z_cs_self_midplane_profile`
on `large_tokamak_nof`, found by the rule "largest exit residual among the carried components") stops the loop
one sweep early and the audit rises 50× but stays below τ — the truncated run is still *within τ*, so the full
set is conservative by one sweep there and the audit reports that correctly. What separates a binding drop
from the rest is the **exit state against the full-set run**: bit-identical for every non-binding drop (17 of
19) and every control (6 of 6), different (2.6e-09 / 2.7e-10 on the ruler) for the binding one. **GT's form:**
per configuration and arm, from the displaced entry at τ, (i) the component the declared rule finds binding is
dropped and the run must stop earlier *and* leave an exit state that differs from the full set's — the tooth;
(ii) a declared non-census control is dropped and the run must be bit-identical; (iii) the whole-`y` audit of
the truncated run is reported beside as the accuracy it left. A comparison gate against a reference run, not
a per-run audit; a row of the verification table (§8). Where no single component binds on the entry (lad at
τ = 1e-8: exit residual 0.0 in both arms), the gate reports that and (ii) alone is the check.

---

## 4. Phases, entries, seeds

**N = 25** per configuration per arm, both phases (V4 Table 6, from V3 (O2); unchanged).

**Phase A — one `call_models` evaluation per arm.** The reference per configuration is the converged flat
state at the design point (one `A0` evaluation from the cold entry of the committed input file — re-made for
V5, since the test set and τ change what "converged" means; its cost is the cold-start term, reported
beside, never pooled). Entries are the V4 δ-stream: `1 ± δ·u` on every coupling component, `u` uniform in
`[−1, 1)` from a hash of (seed, component), **δ = 0.10**, seeds 1–25, bit-identical across arms per seed
(**the user, list header: *"I like the hostile 10 % for the paper results. We see the actual result in phase B
anyway."***). Every arm, `AR` included, enters from the same displaced snapshot (D26). **No stencil regime**
(item 10). Failure taxonomy as V4 §3.4 check 4, denominators of 25.

**Phase B — one optimisation per arm.** `start000` unperturbed plus 24 perturbed at **δ = 0.10** on the
iteration variables' initial values (keyed on the variable number, bounds-clamped; V4 §3.5); no retries by
the harness (the optimiser's own retry ladder is recorded per attempt, DR7). Every phase B table is over
**the seeds on which every arm reached an accepted optimum** (`status == ok`, `ifail == 1`), one `n` per
configuration, with the per-arm success table (item 3 as reduced; A82's construction) explaining that `n`
and naming the starts lost to the intervention arms alone — descriptive, no expectation, no robustness claim.
**On `st_regression`, seeds 1 and 2 are named fragile in advance** (A96): a path comparison on st is a statement about
the other seeds; the optimum comparison (B1) is the statement on all.

**Configurations** — declared unconditionally: `large_tokamak_nof`, `low_aspect_ratio_DEMO`, `st_regression`
(D17; **item 1's D22 note, the user 2026-09-15: *"D22 – the conclusion was to keep. that is fine for v5 as
well"***). No drop rule exists, so no selection at configuration level can occur.

**Seed pairing**: the same seed gives every arm a bit-identical starting point in both phases, checked by
gate G6 (phase A entries) and by the composition of the phase B start (the displacement stream keyed on the
variable number); every comparison is paired.

---

## 5. Acceptance rules, pre-declared

Each rule's verdict is a row of the one verification table (§8); nothing else carries a verdict. The
median is nearest-rank, upper-middle (`sorted[n // 2]`, V4 §3.5).

| # | quantity | rule | provenance |
|---|---|---|---|
| **A1** | **RQ1 — matched accuracy** | per configuration and pair (**`A1 → A2` pulsed, `A0 → A2` st — D34's pair, the one the paper prints**), each arm's audited maximum scaled residual **over the whole state** (D36: with the deferred nodes executed, every component is audited alike) **within F = 10 at both median and p90**; the restricted statistic published beside for this revision; **0 components above τ on every accepted run**. The audit sweep is the harness's instrument: **excluded from every evaluation count and every timing** (D36) | V4 §3.4 check 1; D34; **D36** (§12 Q2); item 10's verification row |
| **A3** | **RQ1 — cost** | on D34's pair: the ratio of the means over the runs both arms finished, the per-run median with `[min, max]`; per module (sweeps per evaluation, the paper's cells); `A2/A0` on the pulsed configurations is not printed in the paper's table | D34; the paper's tables; V4 §3.4 check 3 |
| **A2** | **RQ1 — the fixed-point distance** | the between-arm distance at exit (A76's statistic) **reported**: median and p90, count of pairs above τ; no rule | item 10's dropped candidate (the user: one sentence that the arms reach the same fixed point) |
| **B1** | **RQ2 — same optimum** | per configuration, paired relative `|Δ norm_objf| / max(|a|, |b|)` at accepted optima for `B0 → B1`, `B0 → B2`; yardstick the `BR → B0` spread in the campaign; **accepted at median and p90 when `r ≤ max(F × yardstick, floor)`**, F = 10, floor = 1e-6; the statistic is published whether or not it passes, **with its attribution to the rung it fails on** (V4: `lad`, on the lift rung `B0 → B1`, not the partition); clusters at 10 × floor for the hop count | V4 check 1 (D6); **item 4 as reduced** (the user, 2026-09-29: "accepted"); the neighbouring-threshold grid is not a paper table |
| **B2** | **RQ2 — cost** | solve-phase node calls on the one seed set; per module (the paper's cells are module sweeps per run, `paper_tables.md` conventions); the ratio of the means and the per-run median with `[min, max]`; with and without retried seeds; the exit audit's sweep subtracted symmetrically | V4 §3.5 check 4; the paper's tables |
| **B3** | **RQ2 — the decomposition** | **no iteration-multiplier rule.** `R = ρ × ε` printed per configuration and pair: ρ the per-evaluation node-call ratio, ε the evaluation-count ratio from `sweeps_per_eval.n_evaluations`, R the pooled ratio, the identity's residual stated; iterations (summed over attempts, and final attempt) beside as context; a label only, never a verdict: `|log ε| ≤ log 1.05` → *trajectory-neutral*, else *trajectory changed by ε* | **item 1** (the user, 2026-09-15: the multiplier "imposes a statistical bias"); the paper keeps its iterations table and says in one sentence that `lad`'s lifted arms take the shorter path |
| **B4** | lift closed | constraint-93 residual at every accepted optimum, seconds and relative; reported per rung, no verdict | V4 check 3 |
| **B5** | per-arm success | accepted optima of 25 per arm and configuration, the other starts by outcome class, the starts lost to one arm alone; **reported, no expectation** | **item 3 as reduced** (the user: *"I'm not planning to make claims about robustness"*) |
| **—** | timing | **nothing rests on a timing**; every wall-clock number is context in the appendix (§6) | D33; CLAUDE.md; I-10; T5 |

---

## 6. The wall-clock instrument and tables

**Ruled — D33** (the user, 2026-09-29: *"discussion item 4 is accepted"*): wall clock is reported in the
paper's appendix as context beside the counts, from **V5's campaign at one worker**, with the instrument
below, **never as an acceptance quantity**. D33 supersedes D29 (2) **for V5 only**; V4 publishes no timing
(its campaign ran three workers and its harness bills the intervention arms for the whole-state test and
I-30). Items 5 and 7 are prerequisites of every wall-clock table.

**The instrument** (item 9). Env-switched timers in V5's driver copy, **observation-only** (the block
trace's precedent, DR8: with the switch unset every hook sets `None` and takes no branch; G1 byte-identical),
accumulated per run and stamped into the record:

| row | what is timed |
|---|---|
| per node | the model's own wall time, summed per module through the node map (M1, M2, M3, Feedforward, Post-processing) |
| per block loop | the **MDA convergence test** (read plus residual), and the **dispatch** (the sweep body less its nodes and its test) |
| per evaluation | the **objective and constraints** layer (what upstream's idempotence predicate compares — kept apart from the convergence test by name) |
| per run | the **optimiser's own time** (solve-phase wall less every evaluation); the **fixed per-run term** — process start, imports, numba cache load, input parse, output writing, and the once-per-run schedule derivation (item 7), folded here and not into dispatch |
| check | the run's wall time measured independently; the **unattributed residual** printed so the rows are seen to add up |
| excluded | **harness-only costs, excluded from every total and named in the caption**: the exit-audit sweep, the state snapshots, the census hooks, the record assembly |
| the instrument's own cost | one run per configuration with timers off, reported beside |

**Run discipline** *(amended by D38, the user, 2026-09-29: "you can parallelise the experiment campaign
itself")*: the campaign at **W = 4** on the 16-core machine, every child pinned to one thread
(`NUMBA_NUM_THREADS=1`, `OMP_NUM_THREADS=1`), load average recorded per run; the **repeatability check** of one
seed per configuration, three repetitions, at **W = 1** in A91's form (median and range; a case whose
repetitions differ in counts is refused) — and the **validity check for the campaign's timings**: the
campaign's timing of those same seeds must lie within the repetitions' range; if it does not, the appendix
timings come from a one-worker timing pass over the seed set and the report says so. Counts are unaffected by
W in either case.

**The three appendix tables** (per configuration; arms as columns; ratio of means and per-run median with
`[min, max]`, as the count tables):

1. **phase A in wall clock**, ms per evaluation: M1, M2, M3, Feedforward, Post-processing (model time each);
   MDA convergence test; dispatch; objective and constraints; residual; **Total** (the evaluation's measured
   wall).
2. **phase B in wall clock**, s per optimisation: the same rows plus optimiser own time and fixed per run;
   **Total** = the run's wall time less the harness-only costs.
3. **cost breakdown, phase B**: s per optimisation and ms per evaluation with the share of the total — model
   evaluation (the modules summed); MDA overhead per sweep: convergence test, dispatch; optimiser overhead
   per iteration; fixed per run; **Total**. Whether the architecture changes the overhead is read off the
   `B0` and `B2` columns of the per-sweep rows, normalised per evaluation.

**Expected reading** (item 9, from A91 and the campaign's sweep counts; context): reference to control a few
percent more model time and a test term of about 1 ms; control to modified, model time about 0.75 with every
overhead row equal within 0.3 ms; total per evaluation about 0.75–0.8 where V4's node-call ratio read 0.64 —
because node calls weight every model equally and the cost sits in a few physics and coil models, which is
the paper's argument. *(A93, 2026-09-29: at the census test and τ = 1e-8 the per-evaluation node-call ratio
on the pulsed configurations is 0.48–0.49, not 0.61–0.64, so the gap between the count ratio and the
wall-clock ratio is larger than this paragraph's V4 figures suggest; the wall-clock terms themselves are
unmeasured until V5's campaign.)*

---

## 7. Gates, each with teeth

A failed gate blocks the dependent stage and is a result (protocol §6); every gate has a tooth (§12) and
every count its denominator (T11). Gate records are reused across tasks (`--resume` on seeded records) and
re-made only where a change alters what the gate reads (harness plan amendment 15).

**Table 2.** *The V5 gates: one row per gate — V4's registry name where it exists, what it binds, the
criterion, the tooth. Kept, new and dropped are by list item 10 unless another item is named.*

| gate | V4 name | binds | criterion | tooth | status |
|---|---|---|---|---|---|
| **G0** | `g0prime` | every V5 commit | the copy's `process/models/` byte-identical to `c0ae5b28`'s | a 1-byte change to one model file | kept |
| **G1** | `switch_neutrality` | **each driver change, run per change, never batched** (DR9–DR13, §11) | with every switch unset, deterministic record values and every output-file line identical to a run at the pre-change commit, three configurations | a 1-ULP change to one float | kept |
| **G2** | `prime_map` (re-formed by A99; part (ii) reads GC's `DR9__DR10` straddle record — a **one-time result** like GR, since no tree after DR10 can re-make the per-sweep side) | the prime in its **once-per-evaluation form** (item 8) | from each reference exit snapshot, prime on vs off, exit states bit-identical on N/N components; **and** the once-per-evaluation form's exit states bit-identical to V4's per-sweep form on the gate job set (item 8's requirement); `n_prime_calls` = evaluations | a doctored snapshot component | kept, re-formed |
| **G4** | `audit_restriction` | the restricted statistic (A1) | a doctored `per_run`-owned component trips the whole-state audit and not the restricted one; a doctored in-loop component trips both; one from each excluded namespace | both directions, every namespace | **retires** once the whole-state and restricted statistics agree on the gate job set (D36, §12 Q2); kept until then |
| **G5** | `switch_composition` | `B2` | the arm composed from the matrix equals the arm composed switch by switch | `norm_objf` hex, `n_call_models` | kept |
| **G6** | `entry_and_warm` | phase A | seed-paired entries bit-identical across arms; each block arm from the reference snapshot reproduces the reference fixed point below τ — **at V5's τ and on the census set** | as V4 | kept |
| **G7** | `record_completeness` | the record contract | a forced-unconverged smoke run carries every declared field, the timer fields included; a record missing one is refused | field teeth | kept |
| **G9** | `output_path` | `MDA_Output` removal | on `B1`/`B2` the state the one-call path writes is bit-identical to the state at the entry to `write_output_files` | a 1-ULP perturbation before `finalise` | kept |
| **GT** *(new)* | `test_set` — **real since A100 (v5-test-set), merged `d624f528`**: 8 full-set runs (`A0`, `A1`, `A2` at seed 1), 8 binding drops of which 3 bite (nof, all arms, `pf_coil.stress_z_cs_self_midplane_profile`: one sweep fewer, 203–270 of 840 exit components differ, the audit below τ), 5 not individually binding, 8/8 controls bit-identical; PASS requires at least one bite over the job set | the test set (§3) | the census set minus one declared component is caught by the whole-`y` audit, or reported not individually binding; a dropped non-census control changes nothing — **form [to be declared from A92]** | the dropped component itself | new (item 6) |
| **GC** *(new)* | `count_neutrality` (declared by A98 as a refusing placeholder; the body is A99's) | items 7 and 8 (DR9, DR10) | on a job set (both phases, every arm, one seed per configuration) node calls, sweeps, predicate evaluations, components compared and every exit state **identical to the digit** before and after the change | a doctored count on one record | new — the count-neutrality gate |
| **GR** *(once)* | `reproduction` (`registry.RUN_ONCE`: refuses without `--resume`) | the V5 copy **at its copy commit, before any change** (A94) | reproduces V4's twenty reference records bit for bit on every count field and hex float | +1 on a count, 1 ULP on a hex, a missing reference | **run and PASSed** at `d6c246a1` (A94 (v5-copy), merged `b0e91eed`): 20/20 records, 256 values compared, 0 mismatched, 8/8 teeth; `g0prime` 4/4 and `copy_identity` 12/12 PASS beside it; records at `idf_probe/runs/A94_runs/v5_copy_gates/`. No GR beyond the copy |
| ~~G3 / G3c~~ | `cold_chain` | the prime's cold chain | reproduce A35's counts | — | **dropped** (the user, 2026-09-29, §12 Q3): its construction (a prime at every sweep head) no longer exists once item 8 moves the prime; G2 re-formed plus GC cover it |
| ~~G8~~ | `predicate_mode` | the `mixed` ruler | — | — | **dropped** (item 10; D30) |

**Self-checks — kept, not reported**: composition, rungs, capability, provenance, data, run path, stage
provenance, resume identity, run-kind separation, artifacts (check, derive inputs, census, per run), self
containment, `copy_identity`, `edit_behaviour`, `written_file_gap` — run on every press and stated in the
report as "N self-checks pass" in one line (item 10). I-29's harness fix (a pool-identical job with its own
`outdir` must be refused without `--resume`) is a self-check tooth in V5, not a gate.

---

## 8. Reporting

**Ruled — item 10** (the user, 2026-09-29: *"this v5 reporting approach is approved"*). **One generator** —
the existing paper-tables module extended, not the plan-tables renderer — writes **one document** for the
paper, as Markdown grids and LaTeX rows, with a `check` mode that refuses when the rendered file and the
records disagree:

- *Main text*: the switch matrix; the configurations table; phase A module sweeps per evaluation **with the
  ratio columns on `A2/A1` (pulsed) and `A2/A0` (st) — ratio of means, per-run median, `[min, max]` — per
  D34**, superseding today's `paper_tables.md` convention of `A2/A0`, and with `A2`'s post-processing cell
  measured (§2); phase B optimiser iterations and phase B module sweeps per optimisation on `B2/B0` with the
  rungs beside (D34).
- *Appendix*: the two module tables in wall clock with a totals row and the cost breakdown (§6); the per-arm
  success table (§5 B5); **one verification table**, one row per check: physics frozen (G0); switch
  neutrality (G1); matched accuracy (A1: whole-state audit at 0 components above τ on every accepted run, and
  the fixed-point distance A2); same optimum (B1, attributed where it fails); entry pairing (G6); arm
  composition (G5); output-path equivalence (G9); the test set's teeth (GT).

**Dropped from V5**: the stencil regime and RQ3; the predicate trial G8; RQ5; the three weightings (A88's
function-weighted twins); the companion file and every per-seed table; the iteration-multiplier rule; the
`AR → A0` stopping-rule prose (columns stay, one sentence).

**Replaced**: the second implementation (`analysis.py`, 6 464 lines) by **a short independent recount of
exactly the paper's cells** from the raw records — not a second rendering of every table.

**The V5 report** has four parts — method (matrix, criterion, settings, gate list with teeth), the paper
tables included verbatim, one short findings section per rung, the change log — **under 600 lines**. V4's
rules stand: every number from a committed script (protocol §15), cells preserved between renders, captions
of a few lines (§16), teeth for every gate. No companion file.

---

## 9. Declared settings

**Table 3.** *One row per knob — symbol, value, what it controls, provenance. None may change after approval
except by dated amendment; a value marked [A92]/[A93] is filled from that task's report before approval.*

| setting | value | controls | provenance |
|---|---|---|---|
| N | 25 per configuration per arm, both phases | sample size | V4 Table 6 (V3 (O2)) |
| δ (phase A) | 0.10, displaced entries; **no stencil regime** | entry displacement | the user, list header, 2026-09-29; item 10 |
| δ (phase B) | 0.10 | start displacement | D15; V4 |
| test set | `PROCESS_ARCH_TEST_SET=census`: the committed census artifacts `harness/data/test_sets_<config>.json` (A100; widths FLAT 79/78/75 for `A0`/`B0`, 78/77 for `A1`/`B1` on the pulsed configurations, M1 17 / M2 50–48 / M3 12 (+ PULSE 1 on st) for `A2`/`B2`; keyed by loop, the evaluation arms bound by the twin rule). **Fallback (D39):** `=write_set`, the block's whole write set at τ = 1e-6, V4's predicate exactly (proven bit-identical to V4's records), selectable per campaign, never mixed | what the loops stop on | **D32**, item 6; population A92 → **A100** (merged `d624f528`); **D39** (the user, 2026-09-29) |
| τ | **1e-8** by the rule ε ≤ `epsfcn`³ (A89; confirmed at optimisation scale by A93 on the pulsed configurations; st's trajectory term pre-declared non-neutral from A96, §3; **plus the supplementary st stage at 1e-12**, §3, §10) — one value, every converger, every arm, both phases; re-measured on the V5 copy before the campaign as a check | convergence and handover accuracy | item 6; D23 (one tolerance); the user, 2026-09-29 (Q6) |
| `epsfcn` | 1e-3 (PROCESS's default; no input file sets it) | the tolerance rule's step | A89 §7.3 |
| predicate mode | `frozen`; `mixed` never composed | the scale `s_i` of the scaled step | D30 ("or drop it"), item 10 |
| F | 10 | matched-accuracy (A) and same-optimum (B) factor, median and p90 | V4 Table 6 (V2 App. B) |
| floor | 1e-6 relative on `norm_objf` | same-optimum yardstick floor | V4 Table 6 (V3 (O3)) |
| cluster gap | 10 × floor = 1e-5 | the hop count in B1's attribution | V4 (V3; item 5 of V4's list) |
| median | nearest-rank, upper-middle | every phase B statistic | V3 |
| inner cap | 20 sweeps per block; a cap hit is a refusal, not a budget | every block loop, the flat one included | V4 |
| upstream cap | 10 passes → `unconverged-at-cap` | `AR`/`BR` | upstream |
| **W** | **4** for the campaign (children single-threaded), **1** for the repeatability check and the timers-off runs; gates at 3 | worker pool | **D38** amending D33; item 9 |
| iteration bound | **none** (`iteration_ratio_max` retired) | — | item 1 |
| timers | on for the campaign; off for one run per configuration | the instrument's own cost | item 9 |

---

## 10. Run budget

**Context, never evidence** (T5). From V4's Table 6 with the stencil regime (396) and the `mixed` runs (24)
removed:

| stage | runs | derivation |
|---|---|---|
| entry references | 3 | one cold `A0` per configuration |
| phase A, δ = 0.10 | **275** | `AR` 75 + `A0` 75 + `A1` 50 + `A2` 75 |
| phase B | **275** | 4 arms × 25 × 2 pulsed + 3 arms × 25 on st |
| supplementary st stage, τ = 1e-12 | **50** | `B0` and `B2` × 25 on st under the census set (A96; §3) — reported beside, labelled supplementary |
| repeatability check | 9 | one seed × 3 configurations × 3 repetitions (§6) |
| timers off | 3 | one per configuration (§6) |
| gates | ≈ 100–150 at a from-scratch press; **0–20 with seeded records** and `--resume` | amendment 15; GR once at the copy |

**One-worker time estimate.** The V4 campaign's per-run `wall_s` medians (three workers, contended; surveyed
for this brief from the campaign records, not from a committed script — a budget, not a result) are
**nof 17–30 s, lad 25–40 s, st 29–47 s** per optimisation. Serial, at those figures, phase B is
100 × (17–30) + 100 × (25–40) + 75 × (29–47) s ≈ **1.8–3.0 h**; an uncontended single worker should sit at or
below the lower figure. Phase A's 275 evaluations are dominated by process start and numba cache load
(V4: V3's 225 took ≈ 1.5 h at W = 3) — ≈ **1–2 h** serial. **Whole campaign ≈ 3–5 h at W = 1**, one heavy
slot, machine otherwise idle (§5.1 standing rule); the load average per run says whether it was.

---

## 11. Harness change map

The V5 copy is V4's folder copied whole by A94 and then modified (the user, 2026-09-29: "copy V4, then
modify"). One row per list item: the V4 modules that change, what is removed, the data artifacts regenerated
or added. Module names are V4's (README §10.1); names in V5 stay names for what a thing does (no task numbers
or version tokens; harness plan §11.1).

**Table 4.** *The change map.*

| item | what changes | modules that change | removed |
|---|---|---|---|
| **5** phase A deferred nodes executed once, measured | the evaluation entry runs the deferred set once after convergence (A89's mechanism: a sweep over the per-run set on the output path's own route), the census counts it; `CHARGED_ONCE` retired; the restricted statistic reconsidered (Q2) | `child/evaluate.py`, `child/census.py`, `measurement/stats.py` (`node_groups`), `measurement/paper_tables.py`, `gates/gate_audit.py` | the by-construction charge and its check |
| **6** census test set at the derived τ | the driver's predicate binds a **per-arm, per-block test set** (a new switch naming the artifact, or a field of the coupling-state artifact) and the loop stops on it; the census stage (A89's `rbw_census.py`, and A92's optimisation-path census) becomes a harness stage that derives and validates the sets; τ from `config.py`; G6's warm criterion at the new τ; **GT** | `PROCESS/process/core/solver/module_solve.py` (DR11), `child/ystate.py`, `child/predicate.py`, `child/census.py`, `experiment/artifacts.py`, `experiment/switches.py`, `core/config.py`, `gates/gate_entry.py`, new `gates/gate_test_set.py` | — |
| **7** deferral sets and schedule resolved once per run | `Caller._resolve_defer_per_call_tails` memoised at construction or first use, keyed on `i_figure_merit`; provenance stamped once per run; **GC** | `PROCESS/process/core/caller.py` (DR9), `core/records.py` (the stamp), new `gates/gate_count_neutrality.py` | the per-call `ast` walk and JSON read |
| **8** the prime once per evaluation before M1 | the arrangement-method hook moves from the sweep head to `call_models` pre-processing; `n_prime_calls` = evaluations; G2 re-formed | `PROCESS/process/core/caller.py` (DR10), `gates/gate_prime.py` | the per-sweep hook; G3/G3c's chain (Q3) |
| **9** wall-clock instrument | observation-only timers per node, block loop, evaluation, run; the independent run wall and load average; timer fields in the record contract; W = 1; the repeatability and timers-off stages; the three appendix tables | `PROCESS/process/core/caller.py`, `solver/module_solve.py`, `solver/evaluators.py`, `solver/solver_handler.py` (DR12), `child/child.py`, `core/records.py`, `core/pool.py`, `core/config.py`, `measurement/paper_tables.py`, `chain.py` | — |
| **1, 3, 4** reporting statistics | `R = ρ × ε` per configuration and pair with `C` from `sweeps_per_eval.n_evaluations`; the per-arm success table kept; the same-optimum statistic with its attribution; `iteration_ratio_max` retired | `measurement/stats.py`, `measurement/tally_optimisation.py`, `core/config.py` | check 2's verdict cell; the neighbouring-threshold grid from the paper |
| **10** reporting | one generator, one document; the recount | `measurement/paper_tables.py` (extended), new `paper_cells_recount.py` (short), `chain.py` (the stencil chain gone: `evaluation_stencil_chains`, `stage_evaluation_stencil`, `stencil_column_set`), `gates/registry.py`, `gates/exclusion_review.py` (G1's part kept), `gates/gate_composition.py` (the plan column's `predicate_mode` row) and `gates/gate_resume_identity.py` (G8's pairs) — *applied by A98 (v5-reporting-trim), merged `43ce80ab`* | `measurement/analysis.py`, `measurement/plan_tables.py`, `gates/gate_predicate_mode.py`, `RESULTS_TABLES_FULL.md`, `report_cells_preserved.py`, `report_citations_repoint.py`, `report_counts_check.py`, `block_binding.py` (A90's instrument; stays in V4), `harness/data/dsm_function_counts.json` and `stats.functions_by_group` / `weighted_total`'s function weight |

**Driver changes, in the harness plan's form** (its §3.2 table; numbering continues from DR8). Every row is
a change to the copied `process/`, carries G1 per change and — for DR9 and DR10 — GC, and **needs the user's
approval before merge** (harness plan §3; D11's review rule; collaborative mode since 2026-09-14). The ruling
that entails each is named; the merge approval is per change.

| # | driver change | entailed by | harness impact | if declined |
|---|---|---|---|---|
| **DR9** — **merged `f6e90f61`** (A99 (v5-schedule-and-prime), commit `e5137707`, under D37) | the deferral sets and the block schedule resolved **once per run** by `resolve_schedule`, memoised on the figure of merit, reused for every evaluation; the resolution stamped once per run (`schedule_resolution`, with the digests of what it read); G1 and GC neutral, 0 differing | item 7, **D31** (the user: *"this should be fixed in v5"*) | one stamp field; gate GC; the fixed per-run term of §6 | I-30's 8–11 ms per evaluation stays in every deferring arm and biases every wall-clock table against the intervention; no count changes either way |
| **DR10** — **merged `f6e90f61`** (A99, commit `a0de2e13`, under D37) | the prime executed **once per `call_models`, before M1** (the head of `_call_models_inner`), as a pre-processing step of the sequenced schedule; the output path and the exit audit no longer prime; `n_arrangement_method_calls` = evaluations (GC's rule `once_per_evaluation`, 0 failing) | item 8 (the user: *"pre-processing before the partitioned MDAs can start"*) | G2 re-formed; `n_prime_calls` = evaluations; G3/G3c reconsidered (Q3) | the paper's caption ("executing the FirstWall subfunction before every MDA sweep") must stay as V4 built it, ~9–15 stamped calls per evaluation |
| **DR11** — **merged `d624f528`** (A100 (v5-test-set), commit `5980c5dc`, under D37) | the loop's predicate binds a **declared test set per block** (the census set) instead of the block's whole write set; the DSM feedback set selectable for the cross-check only, never composed into an arm. **D39 (the user):** V4's whole-write-set test at τ = 1e-6 stays selectable as a campaign-level **fallback** — the same switch, the other value; τ follows the test set's declared value; GR runs under it | item 6, **D32**, **D39** | the test-set artifacts and their stage; GT; τ from the rule; the fallback value stamped per record | V4's whole-`y` test at 1e-6 stands: correct only because it stops one sweep late (A89 §7.3) and the test is 30–39 % of an evaluation's wall (A89 §7.5) |
| **DR12** | **observation-only timers** (the block trace's form, DR8): per node, per block loop (test, dispatch), per evaluation (objective and constraints), per run; unset ⇒ `None`, no branch | item 9, **D33** | record fields; the appendix tables; the timers-off runs | no wall-clock appendix; D29 (2)'s scope statement stands for V5 as for V4 |
| ~~DR13~~ | *(was: the flat arms' deferral, conditional on Q1)* — **not needed: Q1 ruled (c), D35**; the deferral stays on the intervention rung as the paper's matrix has it | — | — | — |
| **DR11** *(addition)* — **done in `5980c5dc`** | the `mixed` predicate ruler **removed** from the copy in the same change, the switch retired through the registry (`retired_names` / `RETIRED_SWITCHES`) | §12 Q5 (the user, 2026-09-29) | one fewer switch; the self-check compares the two retired lists | the mode stays in the copy uncomposed |

**Where V5's records live.** Under `MDA_partitioning_experiment_v5/runs/` (untracked, as V4's), seeded for
each modify task from the latest relocated tree — first `idf_probe/runs/A94_runs/v5_copy_gates/`, the copy's
own gate records at `d6c246a1`. The retire script relocates every directory named `runs` under `arch_surgery/`
(I-16), so a task's V5 records are safe at retirement; a task copies them into `idf_probe/runs/<name>/` first
only to land them as one tree under one name (A94's assessment). **The copy inherits V4's `self_containment`
finding** (I-32: a help-string example in `experiment_runner.py` names `idf_probe/`); the modify task under
item 10 removes it, and the V5 gate table carries no resumed V4 record for that gate.

**Data artifacts.** Regenerated: the entry references (§4). Added: **the census test sets per configuration,
arm and block** (`test_set_<configuration>.json`, with the DSM feedback set beside as the cross-check, by the
T9 route with the sibling's pin and digests recorded in `harness/data/PROVENANCE.json`); **the schedule
artifact** — the once-per-run resolution (block membership, per-call tails, per-run set) per configuration
and input file, committed so that the run's stamp can be compared with it (the `artifacts_per_run` stage's
twin). Unchanged: the coupling-state artifacts (the exit audit stays whole-`y`), the write sets, the per-run
sets, the input files, the node map.

---

## 12. Scope honesty, and decisions for the user

**Scope.** One code at one commit, three configurations (a case study, D29 (3)), tokamak only, one
partitioning, one lift, one optimiser, one perturbation stream at one amplitude. Per-configuration
conclusions; configurations are never pooled. No robustness claim (item 3). No claim that the arms reach the
same design point (D6). No timing is evidence (D33); the wall-clock appendix is context from one machine at
one worker, its repeatability stated beside it. The census test set is measured on the paths the census
observed (§3) and a branch taken elsewhere is not covered — GT and the whole-`y` audit are what bound that.
The `st` `PULSE` block is still visited empty (I-20a; D21 (d), disclaimed where it bears, now with a test set
of 1 component). Nothing here may be applied to V4.

**Decisions for the user** — numbered, each with the plan's recommendation; **none is settled until ruled**.

> **Rulings of 2026-09-29 (the user, on the orchestrator's presentation of this section):**
> **Q1 → (c), ruled D35**: *"no. the feedforward and postprocessing should run once in phase A. It should mimic a
> full model evaluation yielding the same output as the reference case."* The deferrals stay on the intervention
> rung; every A arm's evaluation ends with every node computed at the converged state (the flat arms' final
> sweep; `A2`'s one execution, measured). DR13 is not needed; Table 1's `⁽?⁾` rows stand as printed.
> **Q2 → yes, ruled D36**: the whole-state audit is the matched-accuracy statistic; the user adds that the audit
> sweep *"should be excluded from evaluation count and runtime measurements"* — it is (§5 B2 subtracts it; §6
> excludes it from every total), now stated as the ruling. G4 retires when the two statistics agree on the gate
> job set. **Q3 → drop G3/G3c** (*"fine"*). **Q5 → the `mixed` ruler is removed from the copy as part of DR11**
> (the user asked why it would be valuable to leave it in; it is not — the removal rides on DR11's neutrality
> press and retires the switch through the registry). **Q6 → the rule stands whatever A93 finds** (explained to
> the user as: a start lost at the tighter τ is a result on the success table, never a reason to loosen).
> Q7 and Q8 were answered at orchestration level in A95's assessment (§6 of its report).

1. **The flat arms and the deferrals ("all A arms", list item 6).** *Ruled (c), D35.* The user extended item 5 to all A arms
   on 2026-09-29, and A89's second-pass control (`A0`: feed-forward once per call after convergence, per-run
   nodes once after) was built at the user's request and is the control of item 6's cost projection. Three
   readings: **(a)** `A0`/`A1` defer in phase A as A89 built them; **(b)** (a) plus the twins `B0`/`B1` in
   phase B, so the rungs read the same in both phases; **(c)** the deferrals stay on the intervention rung as
   the paper's matrix has it, and "all A arms" is read as *every A arm's evaluation ends with every node
   computed at the converged state* — for the flat arms their final sweep, for `A2` the one execution.
   Consequences of (a)/(b): a matrix row moves (Table 1's `⁽?⁾` rows; the paper's "Models sequenced" caption
   must give up "taking the feedforward and post-processing models out of the MDA loop" to the control's
   definition, and `A2/A0` reads 1.00 on the Feedforward and Post-processing rows); the control becomes the
   textbook MDA the user asked for (*"a proper MDA for the control"*); `AR → A0` then changes the stopping
   rule *and* the deferral. **Recommendation: (b)** — the user's words and A89's construction point at (a),
   and the phase parallelism the arm renaming was made for (A78) asks for its phase B twin; the paper's matrix
   gains a row. If the user wants the paper's matrix untouched, (c).
2. **The matched-accuracy statistic (A1).** *Ruled yes, D36; the audit sweep excluded from counts and timings.* Item 5 asks that the restricted audit be reconsidered once the
   deferred nodes are executed: their components can then be audited like the rest. **Recommendation:** the
   whole-state audit becomes the statistic (F = 10 at median and p90 over all components, 0 above τ), the
   restricted one is published beside for one revision, and G4 is retired when the two agree on the gate job
   set; the verification table's row then reads on the whole state, which is what item 10 lists.
3. **G3/G3c (`cold_chain`).** *Ruled: dropped.* Its construction — the prime at every sweep head reproducing A35's cold-chain
   counts — does not exist once DR10 lands. **Recommendation: drop it**; G2's re-formed criterion (exit states
   bit-identical to V4's per-sweep form on the gate job set) plus GC cover what it bound.
4. *(Ruled while this plan was being written — **D34**, the user, 2026-09-29: the paper's phase A table
   prints `A2/A1` on the pulsed configurations and `A2/A0` on `st_regression`; phase B keeps `B2/B0`. Applied
   in §1, §2, §5 and §8; no question remains.)*
5. **The `mixed` predicate mode.** *Ruled: removed from the copy with DR11.* D30 says apply the rule before the campaign or drop it; item 10 drops G8.
   The task's recommendation was to leave the mode in the copy uncomposed (0 driver edits, no G1 press for
   it); the user saw no value in keeping it, and the removal rides on DR11's press.
6. **τ if A93 finds the derived value changes the optimiser's path or success on a configuration.**
   *Ruled: the rule stands.* **Recommendation:** declare it anyway — the rule is declared, the value follows it, and a start lost at the
   tighter τ is a result on the per-arm success table, not a reason to loosen (protocol §6).
7. **The reproduction gate's reference set (A94).** Item 10 says twenty records; which twenty is A94's to
   declare. **Recommendation:** V4's campaign records at `57dc0c14` for the arms and seeds V4's GR covered
   (14 optimisations + 6 evaluations), read through `RECORDED_ARM_NAMES`, compared on V4's `compared_fields()`.
8. **Workers for the gates.** D33 fixes W = 1 for the campaign; gates carry no timing. **Recommendation:**
   W = 1 for the campaign, the repeatability check and the timers-off runs; gates may run at W = 3.

---

## Appendix — change log

| date | entry |
|---|---|
| 2026-09-29 | Written by A95 (v5-plan) at `7986d408` from the V5 improvement list (items 1, 3–10 and their rulings D29–D33), V4's report §1–§3 and §6, the harness plan and README, A89 §7, A90 §0–§2, A91 §0 and §5, and the paper's results section. Status DRAFT · NOT APPROVED. Eight questions in §12; τ, the census population and GT's form await A92 and A93. |
| 2026-09-29 | **D34** (the user, relayed by the orchestrator while the draft was open): the paper's phase A table prints `A2/A1` on the pulsed configurations and `A2/A0` on `st_regression`; phase B keeps `B2/B0`. Applied in §1 (RQ1), §2 (the published pairs), §5 (A1, new A3) and §8 (the main-text tables); §12 Q4 closed by it — seven questions remain open. |
| 2026-09-29 | Merged at `5e4fd4e7`. The user rules on §12 (entered by the orchestrator): Q1 (c) — **D35**; Q2 yes with the audit sweep excluded from counts and timings — **D36**; Q3 G3/G3c dropped; Q5 the `mixed` ruler removed with DR11; Q6 the rule stands whatever A93 finds. Applied in §5 (A1 on the whole state), §7 (G3 dropped, G4 retiring), §11 (DR13 struck, DR11 extended). Still awaiting A92 (census population, GT's form) and A93 (τ). Status stays DRAFT · NOT APPROVED until those are filled and the user approves the whole. |
| 2026-09-29 | **D39** (the user, during the autonomous run): V4's criterion — the block's whole write set at τ = 1e-6 — stays selectable in V5 as a campaign-level fallback beside the census set; §3 (fallback paragraph), §9 (test-set row) and §11 (DR11 row) updated; the DR11 task builds it. |
| 2026-09-29 | A98 (v5-reporting-trim) merged at `43ce80ab`: item 10 applied in the copy; §7 Table 2's GT/GC/GR rows name the registry entries and their interim status; §11 row 10 lists the two further modules the task touched. |
| 2026-09-29 | A99 (v5-schedule-and-prime) merged at `f6e90f61` under D37: DR9 and DR10 rows marked merged with their commits and GC results; G2's row notes part (ii) as a one-time result read from GC's straddle record. |
| 2026-09-29 | A96 (st-trajectory-ladder) merged at `bc988eac`: §3's st paragraph filled with the mechanism and the declaration under D37 (τ = 1e-8 census stands; a supplementary st stage at 1e-12); §4 names st's fragile seeds; §9's τ row and §10's budget carry the supplementary stage. |
| 2026-09-29 | A100 (v5-test-set) merged at `d624f528` under D37: DR11 rows marked merged; GT's row real with its result; §9's test-set row names the artifacts and widths; §3's population paragraph gains the two census findings. |
