# A43 (st-trust-gap) — the outer verification loop has never once fired, and what it buys on `st_regression` is sub-tolerance accuracy that a tighter inner tolerance buys instead

> **Document status** — **CURRENT · OPEN TASK REPORT.** Written by task A43 (st-trust-gap),
> 2026-09-10, on branch `A43-st-trust-gap` in worktree
> `/home/wrutten/projects/PROCESS_surgery_worktrees/A43-st-trust-gap`, branched from
> `architecture_surgery` at `16a6e87e`; experiment base commit `c0ae5b28`.
> **This task modified no file outside `arch_surgery/`**: `git diff 16a6e87e HEAD --name-only`
> names exactly `arch_surgery/idf_probe/a43_trust_gap.py` and this report.
> `git diff 362c0b47 HEAD -- process/` — against the V3 campaign commit — is **empty**, so every
> run here executed the code the campaign executed. Nothing under
> `arch_surgery/MDA_partitioning_experiment_v3/` was touched. **No driver change was needed and
> none was made**, so D11's review rule and its `caller.py` analogue do not arise. Nothing is
> pushed. Archived to `deprecated/` at merge — read this header, not the folder (trap T3).

---

## 1. Verdict

**Hypothesis (a) is wrong, and for a reason stronger than "no edge was found": on this config a
single schedule pass reaches the flat fixed point *exactly*, bit for bit, once the blocks are
solved exactly. There is no cross-block feedback for the dependency-structure matrix (DSM) to have
missed. Hypothesis (b) is right, in its third form — the one the brief asked me to be able to
recognise. This is a handover-tolerance finding, not a coupling.**

Four measurements, in the order they close the question.

**The verification has never fired.** The outer loop takes another whole-schedule pass whenever
the joint predicate finds a coupling-state component moving by more than τ = 1e-6. Across the
entire V3 Phase B campaign — **91 888** `call_models` of arm B2 on three configs — it took a
second pass 90 398 times and a **third pass zero times**. On `st_regression` alone: 48 960 calls,
47 967 second passes, **0** third passes. Traced at component level over all 25 `st_regression`
seeds, that zero is exhaustive: **0 components at or above τ** over 47 967 pass-2 records ×
827 components ≈ 39.7 million component-tests, with **0** discrete mismatches, **0** moved
constants and **0** new NaNs beside it. The zero is not an instrument that cannot register: drop τ
to 1e-9 and the same loop takes third and fourth passes immediately; drop it to 1e-12 and it takes
up to eight. So there was never anything above τ for a missed edge to carry, and the V3 report's
untested hypothesis — *"another coupling still needs it"* — is refuted.

**What the second pass does instead is relax the state below τ.** At a matched single evaluation —
one `call_models` per arm from a common initialisation, no optimiser — the state B3 hands the
objective and the state B2 hands it differ in **183 of 805** tested continuous components,
**0 of them at or above τ**, with a maximum scaled difference of **3.27554e-9**, 305× below the
tolerance both arms declare converged. The movers sit in blocks **M2 (108) and M3 (75)**;
**M1 contributes 0 of the 265 components it writes**, and so does the feed-forward tail.

**That difference is the blocks' own inner-solve slack, and the discriminator is exact.** A live
cross-block feedback edge is a property of *pass order*: on pass 2 an earlier block would see a
later block's entire pass-1 movement, a first-order quantity that does not care how precisely each
block was solved. Inner slack is a property of *inner tolerance*. So hold τ at 1e-6 — the pass
structure then stays at exactly two passes throughout — and move only the inner block tolerance.
The gap collapses **3.27554e-9 → 1.11615e-10 → 3.77907e-11 → 6.45896e-14 → 0**, and at inner
τ = 1e-14 the two arms hand over **bit-identical states: 0 of 805 components differ, maximum
scaled difference exactly `0.0`**, on every one of five seeds. One schedule pass reaches the same
point as two, exactly. Two further identities make the substitution literal rather than
approximate: **B3 at inner τ = 1e-8 achieves `1.11615e-10`, the value B2 achieves at inner
τ = 1e-6 to every digit**, and **B3 at 1e-12 achieves `6.45896e-14`, the value B2 achieves at
1e-10** — on all five seeds. The outer verification pass is worth exactly two rungs of inner
tolerance, and it costs more: at 21 block sweeps apiece, B2 at inner τ = 1e-6 achieves 1.12e-10
where B3 at inner τ = 1e-12 achieves 6.46e-14, a factor of **1 728** better for the same work.

**And the DSM is corroborated, not contradicted.** Every one of the 40 largest movers is written
and read inside its own block: **0 of 40** have any static writer that runs *after* one of its
readers in the executed schedule, which is what a loop-carried cross-block edge would look like.
The mechanism is entirely local, and the per-pass inner-sweep counts name the block responsible:
M1 reaches its own fixed point in 4 sweeps at every tolerance from 1e-6 to 1e-14 and contributes
nothing, while **M2's inner solve is the one that grows — 7, 8, 10, 11, 13 sweeps** — and M3 sits
downstream of it in the schedule. On the second outer pass **every block takes exactly one inner
sweep** and stops: four sweeps that confirm nothing changed.

**What this does to the cost claim the question was attached to.** V3 report §5.3(iii) reads
"st's B2→B3 hides a 17 % iteration increase", 501 → 587. `n_solver_iterations` records only the
**final** VMCON attempt, and on `st_regression` **B2 invoked the retry ladder on seeds 1 and 15
while B3 invoked it on neither** — the same two seeds that supply the two largest increases, and
the only two attractor hops. Counting every attempt, the same 23 pairs give 643 → 587, a **9 %
decrease**; restricted to pairs where neither arm retried, 426 → 456, a 7 % increase. The
direction is not established under any of the three: p = 0.0625, 0.500 and 0.1875 against a
fair-coin null. A 17 % cost that becomes −9 % under an equally defensible reading of the same
records is a statistic waiting for a declaration, not a measurement of trust mode.

**Scope.** All of the above is `st_regression`. The pulsed-config numbers are read from committed
records; no run was taken on either, per the brief. The single-evaluation ladder is five seeds and
one `call_models` each; the pass census is all 25 seeds and every in-loop call.

---

## 2. What was measured, and with what

| | |
|---|---|
| **Task** | A43 (st-trust-gap) — decide by measurement whether the B2/B3 difference on `st_regression` is **(a)** a live cross-block feedback edge the DSM misses, or **(b)** something the Phase B methodology or harness manufactures that is not a coupling; and recognise the third outcome if the data show it — the verification pass finds nothing above τ yet relaxes the state by a sub-τ amount the optimiser is sensitive to |
| **Script** | [`arch_surgery/idf_probe/a43_trust_gap.py`](../../idf_probe/a43_trust_gap.py) — stages `pairing`, `divergence`, `neutrality`, `trace`, `tooth`, `ladder`, `exitgap`, `classify`, `tables`. Every number below names its stage (protocol §15). Committed at `4f05320b` before any number was published; extended at `e2418cbc`, `bf2214e3` and `08792116`, each before the numbers that extension publishes |
| **Driver changes** | **none.** Every instrument this task needed already existed: A31's per-pass joint-test trace (`PROCESS_ARCH_PASS_TRACE`), A34's trust mode (`PROCESS_ARCH_OUTER`), A33's post-solve artifact, A38's restricted audit, A41's exit forensics, and `PROCESS_ARCH_INNER_TAU` |
| **Runs** | 79 fresh-subprocess PROCESS runs in this worktree, ≤ 3 concurrent: 2 neutrality, 25 traced B2 + 1 traced B3, 2 tooth (both refused by design), 10 tolerance-ladder optimisations, 50 single-evaluation handover runs (5 seeds × 5 inner tolerances × 2 arms, all `ok`). Composed through V3's own `v3_runner.env_for` / `run_job` so the arm measured is the campaign's arm. `st_regression` only |
| **Environment** | `PROCESS_surgery_env`; `PYTHONPATH` pinned to this worktree per subprocess and the **exact** tree asserted in-process (traps T6 and T10 — the editable install points at the main checkout and a prefix test would pass there). Every run record stamps `process_file` under this worktree |
| **Artifacts** | `arch_surgery/idf_probe/runs/a43/out/{pairing,divergence,neutrality,trace,tooth,ladder,exitgap,classify}.json` and `tables.md` (untracked by policy; regenerable from the script) |
| **Date** | 2026-09-10 |

### 2.1 Vocabulary, spelled out

- **B2** and **B3** are two arms of V3's Phase B ladder. Both run the coupling state as a **block
  Gauss–Seidel**: the model set is partitioned into blocks **M1** (Physics), **M2** (Coils and
  Build), **PULSE** and **M3** (Plant) from the committed DSM node map; each iterated block is
  solved to its own fixed point on its own write set; the blocks run in schedule order. Both carry
  the **prime** (`PROCESS_ARCH_PRIME=fw_geometry`, a run-constant first-wall geometry computation
  executed at the head of every sweep — decision D19), the **resequencing**
  (`PROCESS_ARCH_SEQUENCE=build_after_physics`), the **hoist** (feed-forward nodes lifted out of
  the loop) and the **post-solve exclusion** (nodes whose output no in-loop model reads run once
  at the end). They differ in exactly one switch.
- **B2** then runs the **outer verification loop**: the joint convergence predicate is evaluated
  over the whole coupling-state vector and another whole-schedule pass is taken if anything moved
  by more than **τ = 1e-6** (`PROCESS_ARCH_OUTER` unset → `verify`).
- **B3** is **trust mode** (`PROCESS_ARCH_OUTER=trust`): one schedule pass, no verification.
- **τ** is the outer tolerance; **inner τ** is the tolerance each block's own solve stops at. In
  the campaign both are 1e-6.
- **The predicate** scores each continuous coupling-state component as `max|Δy_i| / s_i`, with
  `s_i` a frozen per-component scale from the deck's harvest, and requires exact equality on
  discrete components. 827 components on `st_regression`: 805 continuous, 22 discrete.
- **D-numbers** are recorded user decisions and **I-numbers** filed issues, both in
  [`MASTER_TODO.md`](../plans/MASTER_TODO.md). **V-numbers** are entries in the standing
  dependency-analysis register [`DSM_VALIDATION.md`](DSM_VALIDATION.md).
- `st_regression` is the **k = 0** config: no burn-time coupling, so nothing is lifted and nothing
  is pinned. It is the only config on which B2 → B3 is a pure architectural change.

### 2.2 The structure of the argument

Four questions, each answering the next one's premise:

1. **Did the verification ever fire?** If the outer loop never found a component above τ after the
   schedule's second pass, there is nothing above τ for a missed edge to carry, and hypothesis (a)
   has no object. — §3 and §5, stages `pairing` and `trace`.
2. **Then what does the second pass change?** The exact, component-by-component difference between
   the state B3 hands the objective and the state B2 hands it, at a matched single evaluation. —
   §6, stage `exitgap`.
3. **Is that difference a coupling or is it slack?** Move the inner tolerance and hold τ: slack
   must collapse, an edge must not. — §6 (matched single evaluations) and §5.4 (whole
   optimisations, stage `ladder`).
4. **Could the movers carry feedback at all?** Every mover's static writers and readers, mapped to
   the blocks of the executed schedule, looking for a writer that runs *after* its reader within
   one pass. — §6.3, stage `classify`.

---

## 3. The verification has never once fired — on any config, in the whole campaign

*Stage `pairing`, from the committed V3 campaign records only. No run was taken for this section.*

The outer loop's stopping rule is the standard one for a block Gauss–Seidel: iterate until a whole
pass changes nothing. It therefore cannot terminate before pass 2 unless the state it was entered
with was already the fixed point — you cannot know a pass changed nothing until you have taken a
pass that changed nothing. So the interesting number is not how often it takes a second pass; it
is how often it takes a **third**, because a third pass is the loop saying *the second pass found
something above τ*. That is the event trust mode declines to look for.

**It has never happened.** (Table T1.)

| config | arm | runs | calls | pass 1 | pass 2 | **pass ≥ 3** | block-solve failures |
|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | B2 | 25 | 14 080 | 149 | 13 931 | **0** | 0 |
| `large_tokamak_nof` | B3 | 25 | 14 080 | 14 080 | 0 | **0** | 0 |
| `low_aspect_ratio_DEMO` | B2 | 25 | 28 848 | 348 | 28 500 | **0** | 3 |
| `low_aspect_ratio_DEMO` | B3 | 25 | 28 848 | 28 848 | 0 | **0** | 3 |
| `st_regression` | B2 | 25 | 48 960 | 993 | 47 967 | **0** | 0 |
| `st_regression` | B3 | 25 | 47 040 | 47 040 | 0 | **0** | 0 |

*Caption: how many whole-schedule passes the outer verification loop took, summed over every
`call_models` of every seed. A row is one (config, arm); a column is the number of calls that
terminated at that pass index. "pass ≥ 3" counts calls where the joint predicate still found a
component at or above τ = 1e-6 after a second full pass. B3 never evaluates the predicate, so all
its calls terminate at pass 1 by construction. `OUTER_CAP` is 20, so the histogram is not
truncated. Units: calls. Source: committed campaign records, `module_solve_totals.outer_pass_hist`;
stage `pairing`.*

- **91 888** B2 `call_models` across the three configs; **90 398** second passes; **0** third.
- The 993 st calls (2.03 %), 149 tok calls (1.06 %) and 348 lad calls (1.21 %) that stopped at
  pass 1 were entered at a state the schedule did not move above τ — the only calls on which B2
  and B3 do identical work by construction.
- The 3 block-solve failures on `low_aspect_ratio_DEMO` occur in **both** arms in equal number,
  and no call there reached outer pass 3, so they are inner-solve cap hits, not outer ones.

**The zero has teeth, and they come from §5.4.** A zero whose failure mode has never been
exercised is an assertion (protocol §12). Lowering τ to 1e-9 with the inner tolerance unchanged
makes the same loop take third passes on 215 of 570 calls and fourth passes on 4; at τ = 1e-12 it
runs to seven and eight passes. The instrument registers a third pass the moment there is one to
register.

**What the second pass costs.** (Table T1b.)

| config | B2 | B3 | B2 / B3 |
|---|---|---|---|
| `large_tokamak_nof` | 11.2963 | 8.3281 | **1.3564** |
| `low_aspect_ratio_DEMO` | 11.3124 | 8.3486 | **1.3550** |
| `st_regression` | 12.9942 | 8.9947 | **1.4447** |

*Caption: block sweeps per `call_models`, summed over all 25 seeds and divided by that arm's own
`call_models` count. A block sweep is one `charge()` in the schedule — one pass of one block's node
list. The two arms' call counts differ once their trajectories part, so this ratio is a campaign
aggregate and not a per-call difference; the matched per-call figure is in §6, where one evaluation
under each arm from a common initialisation costs 21 block sweeps in B2 and 17 in B3. Units: sweeps
per call. Source: committed campaign records, `module_solve_totals`; stage `pairing`.*

`st_regression`'s ratio is the largest of the three, and part of its excess is not work at all —
see §7.2.

---

## 4. The cost the question was attached to: same records, three constructions, two signs

*Stage `pairing`, from the committed campaign records only.*

V3 report §5.3(iii) states that **"st's B2→B3 hides a 17 % iteration increase behind a median of
1.000"** — 501 → 587 optimiser iterations over 23 contributing pairs. That number is what made the
`st_regression` gap look like a cost worth explaining. It is construction-dependent, and the sign
flips.

`n_solver_iterations` records **the final VMCON attempt only**. When VMCON exits `ifail != 1` the
driver retries on a ladder — `epsfcn` × 10, then × 0.1, then a reset Hessian — and the discarded
attempts' iterations are real optimiser work the reported number does not carry. On
`st_regression`, within the both-converged pair set, **B2 retried on seeds 1 and 15 and B3 retried
on neither**; those two seeds are exactly two of the six the V3 report lists as "B3 worse", at
38 → 59 and 37 → 72.

(Table T2b.)

| construction | pairs | Σ B2 | Σ B3 | B3/B2 | differing | B3 worse | B3 better | one-sided p |
|---|---|---|---|---|---|---|---|---|
| final attempt (V3 check 2) | 23 | 501 | 587 | **1.1717** | 7 | 6 | 1 | 0.0625 |
| summed over attempts | 23 | 643 | 587 | **0.9129** | 7 | 4 | 3 | 0.500 |
| clean pairs (neither arm retried) | 21 | 426 | 456 | **1.0704** | 5 | 4 | 1 | 0.1875 |

*Caption: the B2 → B3 optimiser-iteration comparison over the same both-converged pairs
(`status == ok` AND MFILE `ifail == 1`) under three constructions of the same records. "final
attempt" is `n_solver_iterations`; "summed over attempts" adds every attempt the retry ladder
discarded; "clean pairs" restricts to pairs where neither arm invoked the ladder, where the two
coincide. "differing" counts pairs whose two numbers differ at all under that construction; `p` is
the exact one-sided binomial tail on the direction over those pairs against a fair-coin null.
Units: optimiser iterations. Source: committed campaign records, `exit_forensics`; stage `pairing`.*

The two retried seeds in full:

| seed | B2 attempts (stage : iterations : ifail) | B3 attempts | B2 final | B3 final | B2 summed | B3 summed |
|---|---|---|---|---|---|---|
| 1 | `initial:64:5`; `epsfcn_x10:38:1` | `initial:59:1` | 38 | 59 | **102** | 59 |
| 15 | `initial:78:5`; `epsfcn_x10:37:1` | `initial:72:1` | 37 | 72 | **115** | 72 |

*Caption: every VMCON attempt of the two `st_regression` seeds where the two arms took different
numbers of attempts. "stage" is the retry ladder's positional name, "ifail" the solver's exit code
(1 = converged, 5 = failed). Units: optimiser iterations. Source: committed campaign records,
`exit_forensics.attempts`; stage `pairing`.*

On both, **B3 does less total optimiser work than B2**, and the published comparison says the
opposite.

Three things follow, and only the third is a verdict.

1. **The direction is not established under any construction.** Six of seven in one direction is
   p = 0.0625; four of seven is p = 0.5; four of five is p = 0.1875. None reaches 0.05. Whether
   the fair-coin null is the right one depends on the mechanism — a systematically less accurate
   handover has a reason to be signed, a sub-tolerance path perturbation does not — and §5 and §6
   are about which of those it is. (It is the first: B3's handover *is* systematically less
   accurate. That makes the fair-coin null the conservative choice, and the data still do not
   reject it.)
2. **The two largest increases are attractor hops.** Seeds 1 and 15 are the only two pairs whose
   B2 and B3 exits land in different `norm_objf` clusters under V3's own check-1a construction
   (repeated here for per-seed detail and cross-checked against `v3_report_analysis`'s own hop
   count for this pair: 2 and 2, agreeing). They are also exactly the two retried seeds. An
   iteration count for a solve that landed at a different optimum, reached through a different
   `epsfcn`, is not a count for the same problem.
3. **A 17 % "cost of trust mode" that becomes −9 % under an equally defensible reading of the same
   records is not a cost measurement.** V3's B2 → B3 is outside the acceptance rule by
   declaration, so no verdict of that report moves; but the sentence a reader takes away does.
   The declaration belongs to V4 (§9, P2); this report publishes all three.

**Reconciliation with task A44 (transfer-gap)**, which factorised the same records independently,
on problem-calls rather than iterations, over the identical-converged B0/B3 set of 22 rather than
the both-converged B2/B3 set of 23. Their B2 → B3 differing seeds are [1, 2, 9, 15, 19, 24]; mine
are [1, 2, 9, **10**, 15, 19, 24]. The whole difference is seed 10, and the reason is derived here
rather than taken from them: **B0 did not converge on seeds 10 and 17**, so seed 10 cannot enter a
B0-anchored population — while a B2 → B3 comparison has no reason to require B0. Our retried-seed
lists agree exactly on the shared population (B2 [1, 15], B3 []). Their artifact is untracked and
was in flight while this ran; it is cross-checked by sha256 and no number in this report comes
from it.

---

## 5. The traced census: 39.7 million component-tests, and not one exceedance

### 5.1 Neutrality, with teeth

*Stage `neutrality`, and the per-run comparator repeated across stage `trace`.*

Two reruns of B2 at seed 21 in this worktree — one untraced, one with the per-pass trace on — each
compared against the main checkout's campaign record on eight exact fields: `n_solver_iterations`,
`n_model_calls`, `node_calls_solve_phase`, `block_sweeps`, `outer_pass_hist`, `norm_objf` and
`sqsumsq` as hex floats, and MFILE `ifail`. **8/8 fields match on both.** The teeth: each field
perturbed by the smallest amount that should register — +1 on an integer count, +1 on one
histogram bucket, one ULP on a hex float — and the comparator required to report exactly that
field. **8/8 teeth bit and were caught.**

The same comparator then runs once per traced run: **25/25 traced `st_regression` B2 runs
reproduce their campaign record on all eight fields.** So the trace is observation-only, gated with
a denominator rather than asserted, and this worktree reproduces the campaign bit for bit.

### 5.2 The census

*Stage `trace`, aggregated by stage `classify`.*

A pass-1 record compares the state `call_models` was **entered** with against the state after one
whole schedule pass; a pass-2 record compares the state after pass 1 against the state after pass 2.
On `st_regression` the feed-forward tail (`water_use`, `costs`) is on the post-solve exclusion list
and executes nothing during the solve — measured, 50/50 runs, §7.2 — so **a pass-2 record is
exactly the distance between the state B3 hands the objective and the state B2 hands it**, not a
proxy for it.

| quantity | value |
|---|---|
| runs traced | 25 |
| `call_models` traced (= pass-1 records) | 48 960 |
| pass ≥ 2 records | 47 967 |
| highest pass index seen | **2** |
| **components at or above τ at pass ≥ 2** | **0** |
| pass ≥ 2 records with any component above τ | **0** |
| discrete mismatches / moved constants / new NaNs at pass ≥ 2 | **0 / 0 / 0** |
| pass ≥ 2 records with residual **exactly 0.0** | 18 720 (39.0 %) |

*Caption: every joint-test evaluation recorded by the per-pass trace across the 25 traced B2 runs
at the campaign's own settings (τ = inner τ = 1e-6). The above-τ population is the full set, not
the argmax: `trace_pass` records **every** component at or above τ from pass 2 onward, and the set
is empty on every record. The component-test denominator is 47 967 records × 827 components ≈
39.7 million. Units: counts; residuals are the predicate's scaled residual, dimensionless. Source:
stage `trace`, pooled by stage `classify`.*

| pass | records | min | n-weighted mean of run medians | n-weighted mean of run p90s | max |
|---|---|---|---|---|---|
| 1 | 48 960 | 0 | 1.5054e-2 | 2.3433e-1 | ∞ |
| ≥ 2 | 47 967 | 0 | **4.5563e-12** | **1.6380e-8** | **2.1559e-7** |

*Caption: the scaled joint-test residual by pass index, pooled over the 25 runs. "n-weighted mean
of run medians" is exactly that and is **not** a median of the pooled population — a median of
medians is not a median, and the pooled distribution was not retained. `min` and `max` are the true
extremes. Pass 1's `∞` is the predicate scoring a component that is not float-viewable in the entry
snapshot, which is every field no model has written yet in a fresh process (A25's lesson), and is
expected on the first calls of a run. Units: dimensionless scaled residual. Source: stage `trace`,
pooled by stage `classify`.*

**The largest pass-2 residual anywhere in the campaign is 2.156e-7 — 4.6× below τ.** Every seed
individually: 0 components above τ, maxima between 3.0e-8 and 2.2e-7.

### 5.3 The argmax, with its artifact named

**39 % of pass-2 records have a residual of exactly `0.0`** — the second pass moved the state by
not one bit — and those records have no argmax. `numpy.argmax` over an all-zero array returns
index 0, so the spec's first component, `blanket.deg_blkt_inboard_poloidal_plasma`, is named on
every one of them and is not moving. The census below is over the **29 247** records that did move.

| component | records | share | writing block | residual (n-weighted mean of run medians) | max |
|---|---|---|---|---|---|
| `superconducting_tfcoil.a_tf_plasma_case` | 23 111 | 79.02 % | M2 | 6.792e-9 | 2.156e-7 |
| `fwbs.p_cp_shield_nuclear_heat_mw` | 3 263 | 11.16 % | M3 | 1.226e-11 | 1.035e-10 |
| `physics.f_beta_alpha_beam_thermal` | 1 076 | 3.68 % | M1 | 3.810e-14 | 4.913e-8 |
| `heat_transport.tlvpmw` | 1 022 | 3.49 % | M3 | 4.459e-12 | 2.208e-11 |
| `current_drive.radius_beam_tangency_max` | 311 | 1.06 % | M2 | 3.236e-15 | 6.513e-13 |
| `current_drive.big_q_plasma` | 265 | 0.91 % | M1 | 4.290e-16 | 6.061e-8 |
| `superconducting_tfcoil.f_a_tf_turn_copper` | 72 | 0.25 % | M2 | 4.388e-8 | 2.117e-7 |

*Caption: which component holds the residual maximum on a pass-2 record, over the 29 247 records
whose residual is non-zero (the 18 720 zero-residual records are excluded and reported separately —
see the paragraph above). "writing block" is from the committed per-block write subsets, which
cover all 827 components with no overlap. **Holding the argmax is not the same question as being
above τ**, and the answer to the second question is *none* — A31 recorded that its argmax was an
innocent bystander on 89 % of its records, and the same caution applies here. Units: counts and
dimensionless scaled residual. Source: stage `trace`, pooled by stage `classify`.*

`superconducting_tfcoil.a_tf_plasma_case` is the same component A31 named as the (correct but
sub-τ) argmax of the recurring tail it dissolved. **A31's `pf_power.srcktpm` mechanism is absent
here, as A31 predicted it would be**: 0 moved constants over 47 967 records, because the a26-mode
spec that V3 ran under reclassifies that field as continuous. The recurring above-τ tail is gone,
and what remains is this: a sub-τ residual whose argmax is in M2, 79 % of the time.

M1 does appear — on 1 341 of 29 247 non-zero records (4.6 %) — and it is worth saying plainly
rather than eliding, because §6 reports 0 M1 movers at the matched single evaluations. The two are
consistent: the in-loop population visits states the five single evaluations do not, and when an
M1 component does hold the argmax its residual is at the arithmetic floor (3.8e-14 and
4.3e-16 respectively, in the table's units). M1 has slack of its own; it is simply the smallest.

### 5.4 The B3 control, and the tooth for its zero

*Stages `trace` and `tooth`.*

A traced B3 run at seed 0 writes **0 joint-test records** — in fact the trace file is never
created, because the driver opens it lazily on the first `trace_pass` call and trust mode never
makes one. The run reproduces its campaign record on all eight fields.

A zero like that is only evidence about trust mode if the trace variable actually reached the
subprocess. `module_solve` refuses at import when a trace is requested of an arm with no joint test
(`PROCESS_ARCH_MODULE_SOLVE=off`), so the same plumbing plus that one variable must kill the run
naming `PROCESS_ARCH_PASS_TRACE`.

| case | env added to B3's | rc | refused | message named |
|---|---|---|---|---|
| `trust_and_off` | `MODULE_SOLVE=off` | 1 | yes | `PROCESS_ARCH_OUTER=trust …` — the **trust** guard |
| `trace_and_off` | `MODULE_SOLVE=off`, `OUTER` removed | 1 | yes | **`PROCESS_ARCH_PASS_TRACE is set with PROCESS_ARCH_MODULE_SOLVE=off`** |

*Caption: the plumbing tooth for the B3 control's zero. `module_solve`'s guards are ordered and the
first one wins: with trust mode still set, the run dies on the trust guard, which proves the arm
switches arrive and says nothing about the trace variable. `trace_and_off` removes
`PROCESS_ARCH_OUTER` so the trace guard is the first reached — that case is the tooth. The first
case is recorded rather than deleted because it was the first version of this tooth and it does
not bite (§8, decision 7). Gate: **PASS**. Source: stage `tooth`.*

### 5.5 The tolerance ladder in whole optimisations

*Stage `ladder`. Every setting here changes the optimiser's trajectory, so **no iteration or cost
number from this stage compares to B2 or B3**; only the residual structure does.*

Two knobs, moved one at a time from the campaign's 1e-6 / 1e-6, on seeds 21 and 19:

| setting | τ | inner τ | outer-pass histogram | pass-2 max residual | pass-3 max | pass-4 max | … | last pass max |
|---|---|---|---|---|---|---|---|---|
| `as_run` | 1e-6 | 1e-6 | {1: 9, 2: 561} | 7.271e-8 | — | — | | — |
| `outer_tau_1e-9` | 1e-9 | 1e-6 | {1: 9, 2: 342, 3: 215, 4: 4} | 7.272e-8 | 2.250e-9 | 7.666e-11 | | 7.666e-11 |
| `outer_tau_1e-12` | 1e-12 | 1e-6 | {1: 9, 2: 342, 5: 81, 6: 84, 7: 54} | 7.272e-8 | 2.250e-9 | 7.665e-11 | … | **4.513e-14** |
| `inner_tau_1e-8` | 1e-6 | 1e-8 | {1: 9, 2: 561} | **3.278e-10** | — | — | | — |
| `inner_tau_1e-10` | 1e-6 | 1e-10 | {1: 9, 2: 561} | **5.117e-11** | — | — | | — |

*Caption: seed 21 (seed 19 is in `ladder.json` and agrees). A row is one whole optimisation. The
histogram is over that run's `call_models`. Residual maxima are the scaled joint-test residual at
that pass index over that run's records. **The `above` counts in `ladder.json` are relative to that
run's own τ, not to 1e-6** — the trace filters at the running tolerance — so they are not
comparable across rows and are not reproduced here. Units: calls, and dimensionless scaled
residual. Source: stage `ladder`.*

Two readings, and they are the discriminator in its in-loop form:

- **Lower τ, inner tolerance held.** The outer residual contracts geometrically, roughly 30× per
  pass — 7.3e-8, 2.3e-9, 7.7e-11 — and at τ = 1e-12 keeps going to **4.5e-14** by pass 7. It
  converges. A live cross-block edge that one pass could not carry would put a floor under this
  sequence at the edge's transmitted magnitude, and there is none.
- **Tighten the inner tolerance, τ held at 1e-6.** The pass structure does not change at all — the
  histogram stays `{1: 9, 2: 561}` — and the pass-2 residual falls from 7.27e-8 to **5.12e-11**, a
  factor of 1 420, with the median becoming exactly 0.0. The second pass finds less because the
  blocks left less, not because the schedule changed.

---

## 6. The handover, measured directly: what each arm actually hands the optimiser

*Stage `exitgap`. 50 single evaluations — 5 seeds × 5 inner tolerances × 2 arms — all `status: ok`.
One `call_models` per run through Phase A's own single-evaluation instrument (`v2_eval_one.py`,
task A34, gated by `a34_instruments.py`) under V3's own B2 and B3 environments. **No optimiser runs
in this stage**, so no iteration or cost figure here is a campaign cost.*

### 6.1 The accuracy each arm achieves, and what it costs

| inner τ | B2 sweeps | B2 achieved | B3 sweeps | B3 achieved |
|---|---|---|---|---|
| 1e-6 (as run) | 21 | 1.11615e-10 | 17 | 3.27554e-9 |
| 1e-8 | 22 | 1.55970e-11 | 18 | **1.11615e-10** |
| 1e-10 | 24 | 6.45896e-14 | 20 | 3.77907e-11 |
| 1e-12 | 25 | 7.69199e-16 | **21** | **6.45896e-14** |
| 1e-14 | 27 | **0** | 23 | **0** |

*Caption: seed 0 (the deck's own point, unperturbed). "achieved" is the **restricted** uncharged
exit audit: one further full sweep of the complete model set through a fresh `Caller` at the
evaluation's exit, scored over the in-loop write set only — the post-solve nodes' fields are
excluded because no arm runs them during the solve (A38's statistic). It is the accuracy the arm
ACHIEVED, not the tolerance it was set. The instrument is identical in both arms. "sweeps" is that
evaluation's own block-sweep count. The outer tolerance τ is 1e-6 in every row; only the inner
block tolerance moves. Units: sweeps, and dimensionless scaled residual. Source: stage `exitgap`.
Seeds 1–4 (δ = 0.10 perturbed coupling states) reproduce every value in the two "achieved" columns
to all printed digits — see below.*

**The bolded cells are exact identities, on all five seeds:**

- B3 at inner τ = 1e-8 achieves `1.11615e-10` — the value B2 achieves at inner τ = 1e-6.
- B3 at inner τ = 1e-12 achieves `6.45896e-14` — the value B2 achieves at inner τ = 1e-10.

The outer verification pass is worth **exactly two rungs of inner tolerance**. And the substitution
is cheaper: **B3 at inner τ = 1e-12 costs 21 block sweeps, the same 21 B2 costs at inner τ = 1e-6,
and achieves 6.46e-14 against 1.12e-10** — better by a factor of 1 728 for identical work, at one
evaluation on this deck.

That the "achieved" columns are identical across a seed at the deck point and four seeds at
δ = 0.10 perturbed coupling states is itself a finding: **the block schedule's one-pass residual on
this config is a property of the schedule and the tolerance, not of the entry state.** It also
independently corroborates gate G3, quoted in V4 improvement-list item 0 as 3.28e-9 for primed
trust mode against 1.12e-10 for the verified loop — reproduced here to three digits in a different
harness, at five different entry states.

### 6.2 The exact difference between the two arms' handover states

| inner τ | components differing / 805 | **at or above τ** | max scaled | argmax | argmax block | movers by block |
|---|---|---|---|---|---|---|
| 1e-6 (as run) | 183 | **0** | 3.27554e-9 | `superconducting_tfcoil.a_tf_plasma_case` | M2 | M2 108, M3 75 |
| 1e-8 | 182 | **0** | 1.11615e-10 | `superconducting_tfcoil.a_tf_plasma_case` | M2 | M2 108, M3 74 |
| 1e-10 | 179 | **0** | 3.77907e-11 | `fwbs.p_cp_shield_nuclear_heat_mw` | M3 | M2 112, M3 67 |
| 1e-12 | 74 | **0** | 6.45896e-14 | `current_drive.radius_beam_tangency_max` | M2 | M2 70, M3 4 |
| 1e-14 | **0** | **0** | **0** | — | — | **none** |

*Caption: seed 0. The state B3 hands the objective against the state B2 hands it, at the same seed
and the same inner tolerance, compared component by component through the project's own predicate
over the two runs' recorded exit snapshots (`y_exit.json`, written before the audit sweep mutates
anything). **This is not a proxy for the B2/B3 gap; it is the gap.** "components differing" counts
components whose scaled difference is strictly positive, out of the 805 continuous components
(827 total, 22 discrete, none of which mismatched anywhere). Movers are attributed to the block
that writes them, from the committed per-block write subsets; the continuous components each block
writes are **M1 265, M2 204, M3 216, FF 120**. Units: counts and dimensionless scaled residual.
Source: stage `exitgap`. Seeds 1–4 agree on every column: 182–183 differing at 1e-6, 0 at or above
τ at every rung, max identical to all printed digits, and **0 differing at 1e-14 on all five**.*

Three things this table settles.

1. **Nothing the two arms disagree about is above τ, at any inner tolerance.** Both arms are
   converged by the predicate they declare; they are not at the same point. That is the third
   outcome, stated exactly.
2. **M1 never moves, and neither does the tail.** 0 of the 265 continuous components M1 writes,
   and 0 of FF's 120, at every rung on every seed. M1 runs **first**. Feedback into it from M2 or
   M3 would move it on pass 2 by a first-order amount, and it does not move by one ULP.
3. **At inner τ = 1e-14 the difference is exactly zero.** One schedule pass and two schedule passes
   hand over bit-identical states. This is the sharpest form of the refutation of (a): a live
   cross-block feedback edge cannot coexist with a one-pass arm reaching the two-pass arm's state
   bit-for-bit.

### 6.3 The mechanism, named to the block

*Stage `exitgap`, `inner_counts_per_outer_pass`; and stage `classify` for the static join.*

Per-block inner sweeps, by outer pass, seed 0:

| inner τ | M1 | M2 | PULSE | M3 |
|---|---|---|---|---|
| 1e-6 | [4, **1**] | [7, **1**] | [1, **1**] | [4, **1**] |
| 1e-8 | [4, **1**] | [8, **1**] | [1, **1**] | [4, **1**] |
| 1e-10 | [4, **1**] | [10, **1**] | [1, **1**] | [4, **1**] |
| 1e-12 | [4, **1**] | [11, **1**] | [1, **1**] | [4, **1**] |
| 1e-14 | [4, **1**] | [13, **1**] | [1, **1**] | [4, **1**] |

*Caption: how many inner sweeps each block took on outer pass 1 and on outer pass 2, for one B2
evaluation at seed 0. An inner solve that converges in exactly one sweep found its own write set
moving by less than the inner tolerance in that sweep — it had nothing to do. Units: sweeps.
Source: stage `exitgap`, `module_solve_stats.inner_counts`.*

- **On pass 2, every block takes exactly one sweep, at every tolerance.** The second pass is four
  sweeps that confirm nothing changed. That is what a verification pass is, and it is all it is.
- **M1 takes 4 sweeps on pass 1 regardless of tolerance** — from 1e-6 to 1e-14 — so M1 reaches its
  exact fixed point and contributes no slack. That is why it never appears among the movers.
- **M2 is the block whose inner solve grows: 7 → 8 → 10 → 11 → 13.** M2 is the slack. M3 runs after
  M2 in the schedule and inherits its change, which is why the movers are M2 and M3 and in that
  proportion. This is the same M2 the experiment plan §5.2 flagged: *"M2 is the laggard under
  partitioning, and M2 is not small"* — measured here in a different currency.

**The static join.** Every one of the 40 largest movers, looked up in the frozen per-deck
dependency export (sha256 `582b4a5f861f4216…`), with each static writer and reader mapped to the
block it runs in under the run's own recorded schedule:

| movers joined | with a loop-carried cross-block writer → reader pair |
|---|---|
| 40 sub-τ handover movers | **0** |
| 0 above-τ movers | (none existed to join) |

*Caption: a "loop-carried cross-block pair" is a (writer block → reader block) pair whose writer
runs **after** its reader within one schedule pass — the only shape that makes a component a
cross-block feedback carrier under a block schedule. All 40 movers matched the export by their
fully-qualified name. The export's workflow drivers — `COOR_SingleRun` (the input loader) and the
`MDA_Output` / `MDA_Idempotence` pseudo-nodes — are **hubs** whose writer and reader edges do not
pair (DSM register V14 follow-up 2 withdrew a three-pathway claim built on exactly that artifact);
they are recorded by name and excluded from the pairing. Source: stage `classify`.*

The top movers are `M2 → M2`: `superconducting_tfcoil.a_tf_plasma_case`, `tfcoil.m_tf_coil_case`,
`tfcoil.a_tf_coil_inboard_case` and the rest of the TF-coil chain are written by M2 and read by M2,
with `MDA_Output` as their only other reader — the output path, not the loop.

---

## 7. Two things that fall out

### 7.1 Why `st_regression` and not the pulsed configs

The orchestrator sharpened the question during this task: *whatever the outer loop repairs on st is
absent on nof and lad even though those carry more coupling, not less.*

**The premise does not survive §3.** The outer loop repairs nothing on any config. What differs is
whether the sub-tolerance relaxation it performs is visible downstream, and that ordering is not
the coupling ordering:

| config | k | pairs | objf bit-identical | iterations identical |
|---|---|---|---|---|
| `large_tokamak_nof` | 1 | 22 | **20/22** | 22/22 |
| `low_aspect_ratio_DEMO` | 1 | 11 | **0/11** | 11/11 |
| `st_regression` | **0** | 23 | **0/23** | 16/23 |

*Caption: per config, over V3's both-converged B2/B3 pairs. "objf bit-identical" counts pairs whose
`norm_objf` hex floats are equal — the second pass did not change the objective by a single bit.
"iterations identical" counts pairs whose final-attempt `n_solver_iterations` are equal. Units:
pairs. Source: committed campaign records; stage `pairing`, `b2_b3_trust_step_identity`.*

On `low_aspect_ratio_DEMO` — the config with the most coupling, whose objective *is* the lifted
variable — the second pass changes the objective's bits on **every** pair and the iteration count
on **none**. That row alone refutes "more coupling ⇒ more sensitivity to the trust step".

`st_regression`'s sensitivity is documented independently of this task. V3 report §5.2.2 measured
that on st a change of **stopping rule alone** — R → B0, no partition, no lift, no trust step —
moves the design point by p90 0.17 and max 1.00, and that st's accepted optima fall into **four**
clusters whose separations are of the same order as the acceptance floor. A config that relocates
its design point by 100 % in some directions when only its stopping rule changes will relocate it
when its handover state changes in the tenth significant figure. That is a property of
`st_regression`'s constraint set — which is what D6 (never gate on iteration variables) exists for.

**So the sharpened question has the causality backwards.** The outer loop does the same thing on
all three configs. The configs differ in whether it is visible, and the one where it is visible is
the one with the flattest, most degenerate optimum — not the one with the most coupling.

### 7.2 I-20(a): the empty block visit, measured — and its published share is wrong

*Stage `pairing`, from committed records.*

On `st_regression` the `PULSE` block keeps `pulse` as its only member while the post-solve
exclusion suppresses every call site of that node inside the solve. Per run, block visits equal
block sweeps equal suppressed call sites: **50/50 runs, every `PULSE` block visit executed
nothing**, and `pulse` executes 4 times in an entire run (post-solve plus the output path). The
same check on the feed-forward tail: **50/50 runs, `water_use` and `costs` each suppressed exactly
once per `call_models`**, which is what makes §5.2's pass-2 record the handover difference itself
rather than a proxy.

**The size is larger than I-20 records.** That row states "~3.4 % of st's B3 block sweeps are empty
visits". Measured from the same records: on `start000`, B3's `PULSE` sweeps are **570 of 5 259 =
10.84 %**; campaign-wide, **47 040 of 423 109 = 11.12 %** for B3 and **96 927 of 636 194 = 15.24 %**
for B2 — because the verification pass visits the empty block a second time. The verification loop
adds **49 887 block visits that execute nothing** across the `st_regression` campaign. No published
number moves (they cost no model evaluations, exactly as I-20 says), but the fix is worth more than
its filed size, and one full sweep of `st_regression`'s 4.0 extra block sweeps per verified call is
a visit to a block with nothing in it.

---

## 8. Autonomous decisions, and how to reverse each

| # | Decision | Why | Reversal |
|---|---|---|---|
| 1 | **Traced all 25 B2 seeds**, not only the differing ones the brief named | A count of "components above τ" is worth nothing without its denominator (trap T11), and the differing seeds are not a random sample | `--seeds 1,2,9,10,15,19,24,3,21,23` reproduces the brief's population from the same stage |
| 2 | **Measured the handover difference with Phase A's own single-evaluation instrument** (`v2_eval_one.py`) rather than adding a driver hook | A second instrument measuring "the same" quantity a different way is how two numbers end up incomparable; `v2_eval_one` already runs exactly one `call_models` under whatever architecture the environment selects, writes the exact exit state, and takes the uncharged exit audit | The driver-hook variant is a strictly larger change and would need `caller.py` review; nothing here depends on the choice, because the two arms are compared to each other |
| 3 | **Chose the inner-tolerance ladder as the discriminator** rather than a schedule permutation | Permuting the block order changes which edges are loop-carried and so changes the object being measured; moving the inner tolerance leaves the schedule alone and separates the two candidate mechanisms by their different dependence on it | A23's permutation machinery exists; the permutation arm is proposed as P7 |
| 4 | **Published the iteration comparison on three constructions** instead of one | The three disagree in sign, and choosing one silently is exactly trap T11 | V4 declares one as the acceptance statistic (P2); this report declares none |
| 5 | **Kept seed 10 in the differing set** where A44's B0-anchored population drops it | A B2 → B3 comparison does not need B0 to have converged; B0 failed on seed 10, which is a fact about B0 | Adopt A44's identical-converged population and the set becomes theirs; the reconciliation is computed and published, not asserted |
| 6 | **Ran no new arm** — no B3-with-tighter-inner-tolerance optimisation, no verify-once variant | The brief states such a variant is a V4 proposal, not something this task runs | The `ladder` stage's settings are the diagnostic half and are labelled as diagnostics; the arm is proposed as P1 |
| 7 | **Recorded a gate that does not bite, instead of deleting it** | The first plumbing tooth is pre-empted by an earlier guard in `module_solve` and therefore proves the wrong thing. A tooth quietly replaced is a tooth whose failure mode is never seen | Both cases are in `tooth.json` and §5.4 says which is the tooth |
| 8 | **Split the pass-2 argmax census by whether the residual was zero**, after finding the first version misleading | `numpy.argmax` over an all-zero array returns index 0, so 39 % of records named the spec's first component as the "mover". Publishing that would have invented a finding | The unsplit census is still in `classify.json` as `pass_ge2_argmax_census` |

---

## 9. Proposals for V4 — proposals only; nothing here is added to the queue

**P1. Replace the outer verification pass with a tighter inner tolerance, and measure at matched
achieved accuracy.** §6.1 shows the two buy the same thing and gives the exchange rate: one outer
pass ≡ two rungs of inner tolerance, and B3 at 1e-12 matches B2 at 1e-6's cost while beating its
accuracy by 1 728×. The experiment: B3 at inner τ ∈ {1e-8, 1e-10, 1e-12} against B2 at 1e-6, on all
three configs, with the exit audit taken at each arm's own handover point (which V4 item 1b already
requires) so the comparison is at matched *achieved* accuracy rather than matched settings.
`PROCESS_ARCH_INNER_TAU` exists and its docstring already calls it "the parameter that moves [the
block arm's] achieved accuracy independently of its outer one", so no new instrument is needed.
Note the tension with experiment plan §5.2, which records a tight inner tolerance as *conservative
against the partition*: that argument is about block-versus-flat, a different comparison, and P1
should measure which effect dominates rather than assume.

**P2. Declare which iteration statistic check 2 accepts on, and publish both.** §4 shows the same
23 pairs give 1.17, 0.91 and 1.07. A check whose sign depends on an undeclared choice is not a
check.

**P3. Make retry contamination a reported category in every Phase B table.** Two tasks found it
independently on the same day, on different arms and different statistics. The records already
carry everything needed (`exit_forensics.attempts`); no table shows it.

**P4. If verification is kept, make it cheap; if it is dropped, say what replaces the
certificate.** The joint predicate has never rejected a schedule pass in 90 398 opportunities
across three configs, and the pass costs 1.36–1.44× the block sweeps. Two coherent designs follow
and the plan should choose rather than inherit: drop the outer pass and let the block tolerances
plus the uncharged exit audit be the certificate (which is what B3 already is, and what P1 would
make accurate enough); or keep a verification that does not cost a whole schedule pass. What must
not happen is keeping a pass that has never found anything.

**P5. Establish causality on `st_regression` with a controlled sub-tolerance injection.** A driver
switch that perturbs the handover state by a named sub-τ amount in one named component, and the
resulting iteration count. If the count moves, §7.1's mechanism is demonstrated rather than
inferred; if it does not, this report's reading is wrong and that is a result. This is the one
measurement A43 wanted and could not take without a driver change.

**P6. I-20(a) is measured and its published share is wrong.** §7.2 gives the counts: 10.8–11.1 % of
B3's `st_regression` block sweeps and 15.2 % of B2's, against the filed ~3.4 %. The fix is already
a V4 item; what changes is its size.

**P7. A permutation control for the discriminator.** Run the same blocks in a different order and
see whether the pass-2 movers follow schedule position rather than block identity. It would confirm
§6.3 from the other side and cost one arm on one config.

**P8. Give the trace instrument a null argmax on a zero residual.** §5.3's artifact is a
one-line fix in `trace_pass` (record `argmax: null` when `res.max == 0.0`), and it would stop the
next reader inventing a mover.

---

## 10. What this task could not determine

1. **Whether the direction of the B2 → B3 iteration difference is real.** No construction reaches
   p ≤ 0.05, and two of them disagree about which arm is worse. Five to seven differing pairs on
   one config cannot settle it.
2. **Whether the sub-tolerance handover difference *causes* the differing seeds or merely
   accompanies them.** This task measures that the arms hand over different states, that the
   difference is sub-τ, and that `st_regression`'s optimiser path is independently known to be
   sub-τ sensitive. It does not perform the controlled injection (P5).
3. **Displacement-liveness of any cross-block edge under a schedule that never revisits the
   reader** (the V15 qualifier). Every measurement here has the prime on in both arms, which is
   what closes V15's carrier; this task did not re-open it.
4. **Whether the same mechanism accounts for the pulsed configs' exact zero.** The brief forbids
   running them; every pulsed-config number here is read from committed records.
5. **Whether a coupling with a coefficient below about 1e-13 relative exists.** The discriminator
   excludes an edge strong enough to matter; it cannot exclude one whose transmitted signal is
   below the arithmetic. At inner τ = 1e-14 the handover difference is exactly zero on all five
   seeds, which bounds any such edge below the representable.

---

## 11. What goes to the dependency analysis: a register entry, and no handoff

**Nothing is owed to `PROCESS_code_analysis`.** The standing rule for the register (V14 follow-up
3, 2026-09-03) is that a V-entry against the dependency analysis, or any cross-study handoff,
carries a **demonstrated defect** with variable, `file:line` at the study commit, and run evidence —
never a question or a suspicion. This task found no defect. It found the opposite: the export's
assertion about `st_regression` — that the deck contains exactly one cross-block loop-carried
variable pathway, `FirstWall (M3) → build.dr_fw_inboard / dr_fw_outboard → Build (M2)`, and that it
is frozen — is **corroborated dynamically**, at a resolution four orders below the tolerance the
earlier corroborations were taken at, and in the strongest available form: with the blocks solved
exactly, one schedule pass reaches the two-pass fixed point bit for bit.

A register entry is filed as **V16** in [`DSM_VALIDATION.md`](DSM_VALIDATION.md), because the
register records liveness verdicts and this is one: it closes V3 report §5.3's untested hypothesis
with a measurement and states both qualifiers the 2026-09-04 convention requires. It is a
corroboration and says so.

---

## 12. Provenance and reproduction

| | |
|---|---|
| **Base commit** | `c0ae5b28` (frozen; D2) |
| **Branch point** | `16a6e87e` on `architecture_surgery` |
| **Campaign commit the records were made at** | `362c0b47`; `git diff 362c0b47 HEAD -- process/` is empty |
| **Script** | `arch_surgery/idf_probe/a43_trust_gap.py`; `4f05320b` (stages `pairing`…`tables`), `e2418cbc` (the matched handover measurement, the retry split, the static join, the tables), `bf2214e3` (the standalone `tooth` stage), `08792116` (the zero-residual argmax split), `6ab6a60a` (the `verify` stage). Each precedes the numbers it publishes |
| **Which stage ran at which commit** | `pairing`, `divergence`, `neutrality`, `exitgap` at `e2418cbc`; those four functions are **byte-identical** at `08792116` (`git diff e2418cbc 08792116 -- …a43_trust_gap.py` touches only `summarise_trace`, `stage_trace`, `stage_classify`, `stage_tables`, `_fmt` and `main`), so their artifacts are what the final commit produces. `tooth` at `bf2214e3`. `trace` and `ladder` **re-run** at `08792116` so their embedded summaries come from the final summariser — the ladder re-run reproduced every residual and every histogram bit-for-bit, which is a determinism check in itself. `classify`, `tables`, `verify` at `6ab6a60a` |
| **Reproduce** | `PYTHONPATH=<this worktree> /home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python arch_surgery/idf_probe/a43_trust_gap.py all --jobs 3` |
| **Re-verify without re-running** | `… a43_trust_gap.py verify` → **69/69 cells agree, 4/4 teeth trip, gate PASS**. Every figure this report states is checked against the stage artifact it claims to come from, floats by hex; the teeth perturb an artifact value by one ULP or one count and require the check to fail |
| **Records-only stages** (no PROCESS run): `pairing`, `divergence`, `classify`, `tables`, `verify` | reproducible in seconds from the committed campaign records and the traces |
| **Raw artifacts** | `arch_surgery/idf_probe/runs/a43/` — untracked by policy (bulk run artifacts); the stage JSONs and `tables.md` are the summaries every figure above is read from |
| **Cross-checked, never cited** | task A44's `factorisation.json`, read from its worktree by sha256; §4's reconciliation is derived here from the campaign records |

---

## 13. Change log (append-only)

| Date | Change |
|---|---|
| 2026-09-10 | Task opened. Script committed at `4f05320b` with stages `pairing`, `divergence`, `neutrality`, `trace`, `ladder`, `exitgap`, `classify`, `tables`, before any number was published. |
| 2026-09-10 | **The discriminator changed shape before it ran.** The first design measured the handover gap indirectly, through the outer trace's pass-2 residual. It was replaced by the direct measurement — one `call_models` per arm from a common initialisation, then the two arms' recorded exit states compared component by component — because the indirect version is a proxy and the direct one is the quantity. An inner-tolerance ladder was added to it as the discriminator. Committed at `e2418cbc`. |
| 2026-09-10 | **Two inputs from task A44 (transfer-gap), relayed by the orchestrator, changed the analysis** and are folded into §4: `n_solver_iterations` records the final VMCON attempt only, and B2 retried on `st_regression` seeds 1 and 15 while B3 did not. The retry split, the three constructions and the reconciliation of the two tasks' seed lists were added and committed at `e2418cbc` before any of those numbers were published. |
| 2026-09-10 | **A gate was found not to bite and was replaced rather than deleted.** The plumbing tooth for the B3 control's zero is pre-empted by `module_solve`'s trust-mode guard, which is checked first. A standalone `tooth` stage was added with the guard order accounted for, and both cases are recorded (§5.4). Committed at `bf2214e3`. |
| 2026-09-10 | **A `verify` stage was added** so the report's own figures are checked against the artifacts they claim to come from rather than transcribed by hand: 69 cells, floats by hex, with four teeth that perturb an artifact value by one ULP or one count and require the check to fail. 69/69 agree, 4/4 teeth trip. Committed at `6ab6a60a`. |
| 2026-09-10 | **An argmax artifact was found and the census was split.** 39 % of pass-2 records have a residual of exactly zero, and `numpy.argmax` over an all-zero array returns index 0 — so the spec's first component was being reported as the mover on 18 720 records where nothing moved. The census is now published over the non-zero population only, with the artifact named (§5.3). Committed at `08792116`; stages `classify` and `tables` re-run at that commit, and `trace` re-run so its summaries come from the same commit. |
