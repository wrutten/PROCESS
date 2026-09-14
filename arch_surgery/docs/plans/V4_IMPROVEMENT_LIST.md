# V4 improvement list — method changes for a fourth experiment revision

> **Document status** — **CURRENT · PLANNING INPUT.** Opened 2026-09-07 from the user's
> review of [`V3_EXPERIMENT_REPORT.md`](../../MDA_partitioning_experiment_v3/V3_EXPERIMENT_REPORT.md).
> Same convention as [`V3_IMPROVEMENT_LIST.md`](V3_IMPROVEMENT_LIST.md): **this is a list of
> candidate design changes, not a plan.** Nothing here is decided, and a V4 experiment plan
> would restate its selections with pre-declared acceptance rules. Items marked **[data gap]**
> name instrumentation V3 lacked; the rest are design or analysis changes on data that already
> exists. Nothing here may be applied to the V3 harness — V3's campaign is measured and
> published, and changing its schedule or arm names retrospectively would break comparability.

## Arm lattice

### 0. The prime is part of the partitioning intervention, not a separate question *(user decision, 2026-09-07)*

**Decided, not a candidate.** From V4 onward the prime is **a component of the partitioning
intervention**, not a separately-attributed variant point. The V3 question — *does the prime
close the FirstWall→Build carrier?* — is **closed**, and `A1u` (its prime-free counterfactual)
is **retired from the arm lattice.**

**What closed it.** Two independent measurements, either of which would have sufficed:

- **Phase A (report §4, §4.4):** A1u and A0 are **entirely disjoint populations** on all three
  decks — A1u's minimum restricted residual exceeds A0's maximum by four to five orders, or
  unboundedly on lad where A0 reads exact zeros. On the integer statistic, A0 and A1 leave
  **zero components above τ in every run of every deck** while A1u leaves up to 167 in a single
  run. A1 reproduces A0 bit-identically on lad and st.
- **Gate G3 (cold chain, st):** trust mode with the prime **off** leaves **124 components above
  τ** (max residual 1.79e-2); with the prime **on**, **0** (max 3.28e-9). The blocks are true
  feedforward only when primed.

**And it costs nothing to include.** `A1u→A1` node-call ratio is exactly **1.0000**, bracket
`[1.0, 1.0]`, and §4.5's per-block table shows A1u and A1 **identical in every block on every
deck**. The prime changes what `Build` reads, not how often anything runs. Its own cost is
`n_prime_calls` — one `set_fw_geometry()` per sweep — which stays published beside every ratio
that excludes it (D19 keeps it out of `node_calls` by declaration; trap T11 requires it be
named).

**Consequences for V4.** The arm lattice loses one Phase A arm (75 runs: 3 decks × 25 seeds).
D19 stands as the record of the variant point and `PROCESS_ARCH_PRIME` remains an env switch
for gating, but **no V4 result attributes anything to the prime separately** — it is inside
"the partitioning intervention" wherever that phrase appears. Phase B already worked this way
(O5 declined prime-free twins); this makes Phase A consistent with it.

**What is *not* claimed.** That the prime is sufficient on its own, or that it is the only
thing the outer loop was repairing. On `st_regression` the trust step still differs from the
verified loop on 7 of 23 seeds (report §5.3) — primed blocks reach the flat fixed point
(G3: 0 above τ) but at 3.28e-9 against the verified loop's 1.12e-10, and that sub-tolerance gap
still moves the optimiser's path on a four-attractor deck. **Both arms are "converged"; they
are not the same point.** That remains open and is not what item 0 closes.


### 1. A Phase A reference arm, and a naming split: `AR` / `BR` *(user, 2026-09-07)*

**The change.** Rename V3's Phase B `R` to **`BR`**, and add a Phase A counterpart **`AR`**:
a reference run of `call_models` executing **only the hard-coded idempotence loop** —
`PROCESS_ARCH_MODULE_SOLVE` unset, everything else as A0. Phase A then decomposes on the same
four rungs Phase B already has:

| | Phase A | Phase B | isolates |
|---|---|---|---|
| reference | **`AR`** *(new)* | `BR` *(renamed from `R`)* | PROCESS as shipped |
| flat, predicate-matched | `A0` | `B0` | **the stopping rule** |
| partitioned (prime included) | `A1` | `B3` | **the partitioning intervention** |

*(`A1u` is retired — see item 0.)*

**Why V3 had no Phase A reference, and why that reasoning does not survive contact with the
instrument.** R was excluded because the two arms stop on different criteria over different
quantities — upstream sweeps until `objf` **and** `conf` are idempotent under
`check_agreement` (~27 output scalars, `caller.py:1326-1352`), while A0/B0 sweep until the
**coupling state** (840 / 846 / 827 components) converges at τ. Comparing their per-call costs
would compare cost at unmatched final accuracy, which the experiment plan forbids.

**But Phase A owns the instrument that measures exactly the unmatched quantity.** Phase A's
whole statistic is an exit audit of the coupling state on the a26 ruler. So `AR` converts the
objection into a measurement: it reports *where upstream's stopping rule actually leaves the
coupling state*. Three outcomes, all results:

- **AR's audit residual ≫ τ** — upstream under-converges the MDA, and its per-call cheapness
  is bought with accuracy. This would be the single most consequential thing the experiment
  could say about the shipped code, and **nothing in V2 or V3 measures it.**
- **AR's audit residual ≈ τ** — the two stopping rules are accidentally equivalent on these
  decks, and R→B0's measured cost difference (0.976 / 1.028 / **1.155**) is pure overhead.
- **AR's audit residual ≪ τ** — upstream over-solves, and the predicate-matched baseline is
  the cheaper *and* looser arm.

**Binding discipline if it runs.** `AR→A0`'s cost ratio is a comparison at unmatched accuracy
**by construction**, so it may never be published without **both arms' audit residuals beside
it in the same table**. The ratio alone would be exactly the error the exclusion was designed
to prevent.

**A pre-declarable failure mode, from the source.** Upstream's loop is `for _ in range(10)`
and then **raises** `RuntimeError` if idempotence is not reached. Phase A enters from a
δ = 0.10 perturbed point where A0 already needs 5–6 sweeps on the coupling predicate. So `AR`
may hit the cap and raise on some seeds. **That is a result, not a machinery failure** — it
would say upstream's loop cannot converge a displacement this size — and V4 must pre-declare
it as a taxonomy row (`unconverged-at-cap`), distinct from `crashed`, so it is never silently
dropped or misread as a harness fault (cf. the V3 launch incident, report §1).

**Cost of the rename, and one trap it sets.** The `R` → `BR` rename touches the harness, the
run-directory names, the tally keys and the report tables. It is forward-only: V3's committed
records keep `R` and V3's report stays valid. **But gate G0 reads V2's
`.../campaign/<deck>/R/start000/metrics.json` as its reference.** A V4 G0 comparing `BR`
against that path needs an explicit name mapping, and — the load-bearing part — **a gate that
cannot find its reference must refuse, not pass over an empty comparison** (trap T11's shape:
a check with no population is not a check; this is the defect A41 found in `--verify` and
repaired with `--mode smoke`).

**Prior art it would settle.** Report §5.5 now publishes `B3/BR` beside `B3/B0` because the
stopping-rule rung is not free (up to 9 percentage points on st). `AR` gives Phase A the same
honesty at the per-call level.

**Impact of the cap-10 constraint, measured.** In-loop, `R` never approaches it — mean 3.21 /
3.44 / 3.26 sweeps, and the largest bin observed anywhere is **7** (one evaluation of 53 700
on st). The δ = 0.10 entry costs A0 about 1.7× its in-loop sweep count (5–6 against 3.29), so
`AR` should land near 5–6 with a tail, against a cap of 10. **Headroom exists but is not
generous**, and st already carries the fattest tail (0.335 % of in-loop evaluations at ≥ 6).
Three consequences to pre-declare:
(i) a capped `AR` **raises** `RuntimeError` and therefore produces no metrics — which the
harness would otherwise classify as machinery failure, the exact confusion that wasted V3's
first launch (report §1); it needs its own taxonomy row, `unconverged-at-cap`;
(ii) a capped `AR` is a **genuine finding about the shipped code** — "PROCESS as shipped cannot
converge its own idempotence criterion from a 10 % displacement" — not an obstacle to route
around;
(iii) the real risk is **denominator bias, not the raise**: if `AR` fails on the hardest seeds,
its surviving set is a favourable subsample and `AR→A0`'s ratio is computed over easy seeds.
The identical-success-set construction already used throughout handles this **provided the drop
is reported with its seeds** (trap T11).

### 1a. δ: add a second amplitude, do not reduce the first *(user question, 2026-09-07)*

**The number that frames it: the optimiser's own finite-difference step is `epsfcn = 0.001`,
while Phase A enters at δ = 0.10 — two orders of magnitude apart.** Phase A's entry is
displaced 100× further than any point the gradient stencil actually visits. That is the
quantified form of §3.2's regime disclosure, and it is consistent with I-17's measured result
that Phase A evaluations take 1.5–1.7× the sweeps of in-loop ones.

**Do not reduce δ.** The prime result *requires* the hostile regime. The carrier (the `dr_fw`
pair) is a run-constant that **no optimiser-driven call after call 1 displaces**; only a
δ-stream that displaces run-constants makes it displacement-live and therefore measurable at
all. At δ = 1e-3 the A1u/A0 separation — currently five to six orders of magnitude — would
shrink, possibly into noise, and the experiment would lose the power to detect the thing it was
built to detect. D15 calibrated δ = 0.10; the V3 plan records that amplitude was measured *not*
to be the failure lever (improvement-list item 9, not adopted); and changing it breaks
comparability with V2, V3, A35 and A38.

**Add a second amplitude instead.** Phase A is being asked two questions that need opposite
regimes — *"does the prime close the carrier?"* (needs hostile) and *"does the per-call ratio
predict the in-loop one?"* (needs representative). One δ cannot serve both, and **I-17 is the
symptom of trying.** Proposal: δ ∈ {0.10, 0.001}, the second matched to `epsfcn` so it is
principled rather than arbitrary; **acceptance stays on δ = 0.10** (preserving both
comparability and the prime's detectability), with δ = 0.001 published as a representativeness
probe.

This is a direct test of I-17 with both outcomes as results: if the per-call ratio at δ = 0.001
predicts Phase B's realised ratio better than δ = 0.10 does, the regime mismatch **is** the
transfer gap; if it does not move, the cause is elsewhere — which is what the report's
trajectory hypothesis (§6) predicts. It also removes the cap-10 risk for `AR` at the second
amplitude.

Cost is small: Phase A is 225 single-evaluation runs against Phase B's 350 optimisations, so a
second δ roughly doubles the cheap phase and leaves the expensive one untouched.

### 1b. `MDA_Output` is not part of the architecture: keep it in B0, drop it from B1 / B2 / B3 *(user decision, 2026-09-07)*

**Decided, not a candidate.** From V4 onward the intervention arms **do not run `MDA_Output`**.
`R` and `B0` keep it — `R` is PROCESS as shipped and `B0` is the predicate-matched flat
baseline, so both run PROCESS's own output path unchanged. **A proper architecture does not
need a second convergence loop at output time**: its solve phase hands over a state it has
already verified (every block at `inner_tau`, the joint predicate on B2, the uncharged exit
audit on all of them), and re-solving that state with a different loop before writing it out
is a property of the incumbent, not of the intervention.

**What `MDA_Output` is.** `Caller.call_models_and_write_output()`
(`process/core/caller.py:1402`), reached from `write_output_files` in every arm. It loops up
to ten times: one **flat** `_call_models_once` sweep of every node, then `finalise` writes an
MFILE, and successive MFILEs are compared float by float at `rtol = 1e-6`. It never enters
`call_models`, so **the block schedule, the hoist and the post-solve exclusion do not apply to
it** — in B2 and B3 it is a flat sweep over the full node set, exactly as in B0 (the comment at
lines 1839–1842 says so). `finalise` additionally re-enters every model's `run()` from its
`output()` (trap T7), and those re-entries pass through no counter.

**What it did in V3, read from every ok run's record** (an inspection over the campaign
records on 2026-09-07 — `node_calls_total − node_calls_solve_phase`, less the post-solve
nodes, over the 21 executing nodes; under protocol §15 these are not citable until a committed
stage reproduces them, which is the first task below):

- **Two flat sweeps per run, in every arm, on every config** — the loop's minimum: one to
  write the first MFILE, one to confirm it. Symmetric across R / B0 / B1 / B2 / B3.
- **Three B3 runs on `st_regression` needed a third pass** (seeds 0, 14, 23; all `ifail = 1`).
  The state the block solve handed over was not MFILE-idempotent at `rtol = 1e-6` after two
  flat passes. No R, B0, B1 or B2 run did this on any config. It is the only asymmetry, and it
  is in the one place where the block arm's fixed point is re-tested by the flat loop.
- The census behind report §5.5.1 therefore carries **three** extra sweeps per module row per
  run (two `MDA_Output`, one exit audit), plus the once-per-run post-solve execution in B2/B3
  — not the "exactly one sweep" its denominator note states. Still symmetric, still ≈ 0.1 % of
  a run's ≈ 2 000 solve sweeps; no ratio moves. The sentence is wrong and should be corrected.

**Why it matters more than its node count.** The Phase B exit audit is taken **after**
`SingleRun.run()` returns (`run_one.py`, "A28 / A26 fix 1"), i.e. after `write_output_files`
has already put the block arm's exit state through `MDA_Output`'s two flat sweeps and the
post-solve sweep. **What the Phase B audit measures on B2 / B3 is the residual of a state the
flat loop has already relaxed twice, not the block arm's own exit state.** Check 1's
`norm_objf` is read from the MFILE `MDA_Output` writes, so the same applies to it. Phase A's
audit does not have this problem (`v2_eval_one.py` audits the single call directly). On the
three st runs above the relaxation was large enough to show in the MFILE at `1e-6`; on every
other run it was below that, which bounds the effect but does not remove it. Removing
`MDA_Output` from the intervention arms makes the Phase B audit read the state the
architecture actually produced — which is what "compare at matched achieved accuracy" was
always supposed to mean — and it is the exit audit, not `MDA_Output`, that then carries the
acceptance for the block arms' output state.

**What the V4 plan has to settle, in order.**

1. **Commit the count first.** A `--tables` cell in `v3_report_analysis.py` (or a `phase_b.py`
   tally field, so `--verify` can compare it): `MDA_Output` sweeps per run by arm and config,
   with the three-pass runs named. Then correct §5.5.1's denominator sentence from the
   committed number and record the audit-position finding in §8.
2. **Define the replacement output path for B1 / B2 / B3.** The natural reading: skip the
   idempotence loop and call `finalise` once on the accepted state (the `output()` re-entries of
   trap T7 remain — those are how PROCESS writes files, not a solve). Driver-side, in
   `write_output_files`, env-switched, and byte-identical to upstream with the switch unset
   (switch-neutrality is a gate). A driver change, so it needs the user's approval before
   merging (D11 applies to models; this is `caller.py`, but the same review rule).
3. **Declare the new difference in the lattice.** Every ordered pair of arms must declare what
   differs (report §5.5, enforced at run time). `B0 → B1` would now differ in the lift *and*
   the output path unless the removal is given its own rung or declared alongside; the plan
   must choose, and item 1's `AR` / `BR` reference arms need the same declaration.
4. **Move the exit audit, or record where it sits.** With `MDA_Output` gone from the block arms
   the post-run audit reads the right state on them; on `B0` it still reads a post-`MDA_Output`
   state. Either audit every arm at the entry to `write_output_files` (A28's
   `--exit-audit-at-call` mechanism already exists for a call-indexed variant) or publish the
   audit position per arm beside the residuals. What must not happen is a residual table whose
   arms were audited at different points without saying so.
5. **The three st runs are a result to keep, not a defect to remove.** They are the only V3
   evidence that a primed, trust-stepped block solve can hand over a state the flat loop still
   moves at `1e-6`; `MDA_Output` found them by accident. V4 should look for the same thing on
   purpose — the exit audit at the accepted point, per run, with the count of components above
   τ — since after this change nothing else will.

**What is *not* claimed.** That `MDA_Output` costs anything the headline can see — two flat
sweeps against ≈ 2 000 is noise — or that removing it changes any V3 ratio. The claim is about
what the intervention *is*: an architecture that certifies its own output state does not get
to borrow the incumbent's second loop to do it, and V3's block arms did.

### 1c. `A0p`: a flat arm that carries the pin, so Phase A varies ownership on its own *(user, 2026-09-10)*

**The change.** Add a Phase A arm **`A0p`** — `MODULE_SOLVE=flat_state` **+** `LIFT=burn_time`
**+** `PIN_BURN_TIME=<the seed's hex, the same value `A1` gets>`; no hoist, no post-solve, no
sequence, no prime, the frozen deck. It is the Phase A mirror of `B1`, which
[`v3_runner.py`](../../MDA_partitioning_experiment_v3/v3_runner.py) already builds for exactly
this reason: *"Flat solve + the lift, nothing else: B0 -> B1 varies the lift alone"*.

**Why.** On the pulsed configs V3's Phase A pins the burn time in the block arms and **not** in
the flat control, so `A0 -> A1` varies the burn time's *owner* (the loop → a constant) together
with the partition, the hoist, the sequence, the trust outer and the post-solve exclusion. The
displacement is not small and it is measured: Phase A's own tally carries
`lift_residual_distribution`, whose median is **155 s** (tok) and **526 s** (lad) in the block
arms against **0** in `A0`, and
[`phase_a.py`](../../MDA_partitioning_experiment_v3/phase_a.py) declares it *"excluded from the
similarity statistic"*. `A0p` turns that exclusion into a rung: `A0 -> A0p` is the ownership
change alone and `A0p -> A1` is the partitioning intervention against a control that sits on the
same reduced map.

**And it makes the two ladders term-for-term identical.** With `A0p` in place,
`A0p -> A1` and `B1 -> B3` are the **same set of switch changes** — `flat_state` -> `per_module`,
plus `SEQUENCE`, `OUTER=trust`, `HOIST`, `POST_SOLVE` and `PRIME` — with the deck held constant
inside each step. V3 had no Phase A step that matched any Phase B step, so no Phase A ratio could
be read against a Phase B one. (`B2` remains the one Phase B arm with no Phase A twin: it splits
that step into `B1 -> B2`, the partition, and `B2 -> B3`, the outer loop.)

**What it buys the headline.** The cross-arm audit comparison stops needing an exclusion where it
matters most. Pinned at the same value, `A0p` and `A1` converge the **same** map, so the pin's
inconsistency is common-mode and cancels. That construction is already validated on this
instrument: the warm equivalence gate G6 pins the block arm at the reference's *converged* burn
time and then demands cross-state max residual `< tau` plus bit-identity of the pinned component
— and it passes on both pulsed configs.

**What it does not buy, stated so it is not over-claimed.** (i) Agreement is to `tau`, not
bit-exact — only the pinned component is bit-identical, which is what G6's
`pin_component_bit_identical` field checks. (ii) It does **not** close I-17(iii): Phase B's
`B1`/`B2`/`B3` hand the burn time to *the optimiser* (`ixc = 178` on the derived lifted deck),
which is a different owner from a constant, and no Phase A arm can carry that. `A0p` removes the
*within-Phase-A* asymmetry only. (iii) Both pinned arms sit off consistency by construction, so
`A0p` is not a candidate architecture and its cost must never be quoted as production's.

**Why the pin does not simply go into `A0` instead.** Two reasons, the second load-bearing.
`A0` is the as-shipped flat control (`phase_a.py`: *"the flat architecture as shipped keeps those
nodes in its loop"*), and a pinned control models nothing that exists. And converging the burn
time is real work the flat loop does and the block arms do not: pinning both sides would delete
that term from the `A0 -> A1` cost ratio, improving the intervention's number by removing
something that belongs to it. The rung keeps it visible and priced.

**No prime, deliberately.** O4's finding stands — the flat arms self-repair the `FirstWall`→`Build`
lag within one sweep, so priming `A0p` would change nothing measurable and would move the arm's
first call. Consistent with `A0`, `B0` and `B1`.

**Cost, and one composition to check at preflight.** No `process/` change: flat + lift + pin is
already legal — the driver's only refusals are pin ⇒ lift
([`subsolve.py`](../../../process/core/solver/subsolve.py), `PIN_ENABLED and not is_lifted(...)`)
and decks naming `ixc = 178` ([`caller.py`](../../../process/core/caller.py),
`_apply_burn_time_pin`), and Phase A already runs the **frozen** deck for that reason. One branch
in `env_for_phase_a`, one `pin_hex` predicate widened from `arm in BLOCK_ARMS`. With `HOIST` off
`pulse` still executes — it just stops computing the burn time — so **`A0 -> A0p` changes the
owner without changing the node set**, which is what makes it a one-variable rung.

**Where it is inactive.** `st_regression` is `k = 0`: nothing to lift or pin, so `A0p` composes
to `A0` exactly. It must be **skipped there and recorded as skipped**, never run as a silent
duplicate — 2 configs x 25 seeds = **50 runs**. Net against V3's 225 Phase A runs, with `A1u`
retired (item 0) and `AR` added (item 1): **275**.

### 1d. Name deferral by how often a node runs, and fold the prime into "arrangement" *(user, 2026-09-10)*

**Two vocabulary changes, forward-only, each with a mapping to V3's names.**

**(a) Deferral is one ladder, not two mechanisms.** `HOIST` (VP2) and `POST_SOLVE` (VP2c) are
two levels of the same thing and nest — post-solve ⊂ hoist ⊂ in-loop
([`caller.py`](../../../process/core/caller.py), VP2c comment: *"VP2 moves a feed-forward node out of
the sweep but still runs it once per optimiser evaluation. VP2c goes further… running it even once
per call is pure cost"*). Their names say neither that they are levels nor what a level does. V4
names the frequency a node runs at:

| V4 name | the node runs | V3 mechanism it replaces |
|---|---|---|
| `per_sweep` | every MDA sweep — flat loop or partitioned block, no distinction | in the loop (the default) |
| `per_call` | once per `call_models` evaluation — every objective/constraint evaluation the optimiser requests, finite-difference perturbations included | `HOIST` (VP2); the pre-/post-predicate routing is kept unchanged |
| `per_run` | once in total, at the accepted optimum, before the output phase | `POST_SOLVE` (VP2c) |

*Caption: one row per deferral level; "the node runs" is the execution frequency in the solve
phase; the third column is the V3 env switch whose semantics the name takes over.*

**Why `per_call` and not `per_optit` (decided by the user, 2026-09-10).** The first draft named
the middle level `per_optit`, "once per optimiser iteration". That is not what the mechanism does:
`HOIST`'s node runs once per **`call_models` evaluation**, and PROCESS takes central differences, so
one VMCON major iteration makes on the order of `2n` such evaluations — about 40 on
`large_tokamak_nof` (`n = 20`). The finite-difference perturbations are calls too, and the node runs
on every one of them; `per_call` says so. A genuine once-per-major-iteration deferral — the `2n`
gradient perturbations reading the hoisted node's value from the unperturbed point — would be a
**different architecture**, with its own staleness question (the finite-difference gradient of
anything downstream of the hoisted node becomes exactly zero) and its own gate. It is not adopted
and not proposed here; if it is ever wanted it needs its own item.

**(b) The prime is arrangement at method granularity.** The driver already says so —
[`caller.py`](../../../process/core/caller.py): *"a driver choice about* when *an existing model
method runs — the same family as the VP1 reorder but finer-grained (a method, not a node)"*. The
matrix's `SEQUENCE` and `PRIME` rows merge into one **arrangement** row with two levels: **node**
(`SEQUENCE=build_after_physics`) and **method** (`PRIME=fw_geometry`). Item 0 already makes the
prime part of the partitioning intervention; this makes the matrix say so. What does not merge:
the cost accounting. `n_prime_calls` stays out of `node_calls` by declaration (D19) and is itemised
beside every ratio that excludes it (trap T11) — merged as a row, still named as a count.

**Cost, and the trap it shares with item 1.** Every V3 run record stores the env by its V3 names,
and `v3_report_analysis.py --verify` reads them back. The rename is forward-only: V3's records keep
their names and V3's report stays valid. Any V4 stage that reads a V3 record — G0 against
`campaign/<deck>/R/start000/metrics.json`, or a V3 baseline in a V4 table — needs an explicit
name mapping and **must refuse on a missing key, never pass over an empty comparison** (T11; the
shape A41 repaired with `--mode smoke`). And each renamed switch is re-gated for neutrality with
the variable unset (protocol §12) — a renamed switch that a stale tree silently ignores is exactly
the "measures the wrong arm under the right name" failure `env_for_phase_a` exists to refuse.

## Schedule and driver defects

### 2. Empty blocks are still swept *(I-20a)*

On `st_regression`, `Pulse.run()`'s entire body is guarded by `if i_pulsed_plant == 1` and is
a **pure no-op**; `times.t_plant_pulse_burn` is absent from that deck's measured 827-component
coupling state; the routing rule correctly demotes `pulse` to post-solve (5 executions per
run). **But the `PULSE` block survives in the schedule after its only member has left it, and
is swept 570 times per run in B3 and 1131 in B2, executing nothing** — the DSM register's V12
trap in live form. Roughly 3.4 % of st's B3 block sweeps are empty visits. *(Corrected 2026-09-10 by A43 (st-trust-gap) §7.2, from the same records: **10.84 %** on `start000`, **11.12 %** campaign-wide for B3 and **15.24 %** for B2 — the verification pass visited the empty block a second time, 49 887 empty visits across the st campaign. The filed 3.4 % was wrong; no published number moves. The user ruled (D21) that the visits stay and are disclaimed.)*

Fix, driver-side and provably neutral: **drop a block whose membership is empty after
hoisting**, and **skip a post-solve node whose measured write set is empty**. Costs no model
evaluations, so no V3 number moves — but it feeds the per-sweep-overhead question (item 3),
and it needs the user's approval as a driver change.

### 3. Count what the per-sweep overhead actually is **[data gap — CLOSED IN THE NEGATIVE, A58 (driver-predicate-counters), 2026-09-10]**

**Settled on counts (A58, gate GR's 20 runs, one seed per cell).** The counters exist in the copy (`PREDICATE_EVALUATIONS`,
`COMPONENTS_COMPARED`, per block). At matched configuration and seed the partitioned arm evaluates the convergence test
1.86–2.34× as often, each test is 0.284–0.285× as wide (its block's write set against the whole state), and the product is
**0.530–0.666×** the flat control's — **33–47 % fewer components compared**, tracking the node-call ratio (0.524–0.650) to within
0.02. A term that scales with node calls is not the non-node-proportional cost §8 requires, so **the convergence test is excluded**
as the carrier of the per-sweep overhead. What that overhead *is* remains open; the candidates the counters cannot resolve are the
dispatch body's own work per sweep (design-vector injection, switch dispatch through every call site, the arrangement method) and,
on `st_regression` alone, the 570 sweeps per run that execute nothing (I-20(a), now measured on all three configurations: item 2).
Also measured: upstream's stopping test is 30–59× narrower per evaluation than the experiment's (27 / 22 / 14 against 840 / 846 / 827).

Report §7's central unexplained result: B3 executes 36–55 % fewer model-node evaluations than
B0 and is **0–15 % slower in wall clock**, going backwards on nof. §8 proves a non-node-proportional
cost term must exist — every per-block node ratio is ≤ 0.870 on nof while the wall ratio is
1.074, and no re-weighting of node costs can bridge that. The **hypothesis** is per-sweep fixed
cost, with the convergence predicate over 840 / 846 / 827 components the prime suspect: B3 runs
2.6–2.8× as many dispatch sweeps as B0.

**This is settleable without a timing**, in the exact style of `NODE_CALLS` and
`SWEEPS_PER_EVAL_HIST`: counters for **predicate evaluations** and **components compared**, per
arm. Exact, concurrency-invariant, and it would confirm or kill the hypothesis on counts alone
— which matters because no conclusion in this project may rest on a timing (I-10).

## Design of the comparison

### 4. Break the objective/structure confound *(report §8 item 6a)*

The three decks optimise three different figures of merit (minimise R₀ / maximise pulse length
/ maximise Q), and the objective is **perfectly confounded** with the structural variable:
`st_regression` is simultaneously the only k = 0 deck, the only deck the lift does not touch,
the only Q-objective deck, and the only one whose `pulse` falls through to post-solve. When st
behaves differently, the design cannot say which caused it.

Two candidate repairs: **(a)** run one deck under two objectives — the cheapest break, and it
separates "lift of the objective" from "lift on a pulsed deck"; a scenario decision, not a
physics change, so it needs a D-number but not a model edit. **(b)** Drop cross-deck synthesis
and report three case studies. Note that `low_aspect_ratio_DEMO` maximises
`t_plant_pulse_burn`, **the very variable the lift promotes to iteration variable 178** — valid
IDF, but degenerate (the objective becomes linear in one variable and independent of the other
18, and all the physics moves into constraint 93). Any deck where the lifted coupling variable
is also the objective deserves its own check.

### 5. Check 1's clusters are coarser than its floor *(report §5.6)*

The clustering gap is `CLUSTER_GAP_FLOOR_FACTOR × OBJF_FLOOR_REL = 10 × 1e-6 = 1e-5` while
check 1's acceptance floor is `1e-6` — **the clusters are ten times coarser than the tolerance
they exist to interpret.** Two runs in one cluster may legitimately differ by ~1e-5; lad's
widest cluster is 8.4e-6 across. So on any deck whose optima are denser than 1e-5, the
within-cluster construction **cannot** separate "same optimum" from "different optimum less
than 1e-5 away", and lad's within-cluster p90 of 1.26e-6 is fully consistent with the latter.
V4 should either decouple the two constants or declare the resolution limit explicitly.

### 5a. A conventional convergence predicate: trial first, adopt if it passes *(user, 2026-09-07)*

**The change.** Replace the coupling-state predicate's frozen denominator with the textbook one.
Today ([`ystate.py`](../../fixedpoint/ystate.py), `_residual_aligned`) a continuous component
passes when `max|dy_i| / s_i < τ`, with `s_i` the median magnitude over the config's harvest
(149 / 297 / 144 design points on nof / lad / st), frozen in `ystate_a26_<config>.json`, and `s_i = 1.0` where no
magnitude was ever observed. The conventional form — Dennis & Schnabel's scaled step test, which
MINPACK's `diag`, KINSOL's scaling vectors and OpenMDAO's output `ref` all reduce to — keeps the
measured scale as the **floor** and adds the **current value**:

    max_i |dy_i| / max(|y_i|, s_i) < τ

with `|y_i|` read from the post-sweep iterate and, for an array component, its `max|elements|`
exactly as `_char_mag` measures the scale, so only the denominator changes. Two properties follow
by construction and are what make the trial cheap to interpret: **(i)** wherever `|y_i| ≤ s_i` the
test is **bit-identical** to today's; **(ii)** the new test is never tighter than the old one, so
no count can go up. Everything else stays — the max-norm, exact equality on discrete components,
the `inf` score for a field no model has written yet (A25's lesson), the `NONFINITE` pattern test,
and the recorded floor.

**What is *not* proposed, and why.** Not a 2-norm over the 800-odd components (OpenMDAO's
`NonlinearBlockGS` default): the experiment plan requires convergence *on every coupling
variable*, the exit audit's integer statistic is "components above τ", and a norm that averages
would declare convergence with named components still moving — that changes what "converged"
means, not how it is measured. Not relative-to-initial-residual (PETSc's `rtol‖r₀‖`): in a
per-call MDA `r₀` is set by the entry displacement, so the tolerance would depend on δ, the
confound §3.3 exists to remove. Not `np.allclose`'s hidden `atol = 1e-8`: the floor here stays
explicit, per component, and in the artifact (A27 already filed upstream's hidden constant as a
defect). This is the smallest change that makes the predicate conventional; it is not the most
conventional predicate available.

**Why it matters here, from the record.** I-12 is the measured case: `costs.coe` at 6.6e21
against `s_i = 1 251` made the old test ~10¹⁸ times tighter than intended and iterated seven of
st's 144 design points to bit-identity, and the amended I-12 records that upstream's
current-value test at the same point is *looser* than ours by 5.3e18. In V3 the post-solve hoist
took `costs` out of the loop, so that exact mechanism no longer fires in the driver arms — but the
convention is unchanged and the components remain in the audit. An ad hoc read of the committed
a26 artifacts (**not citable** until a committed stage re-derives it, protocol §15) puts the
harvest's spread within about 3× of the scale for 90 % of components on every config, with a
short list spanning more than 10×:

| config | components spanning > 10× over the harvest | the largest, as max / scale |
|---|---|---|
| nof | 2 | `power.e_plant_net_electric_pulse_{mj,kwh}`, 1.3 |
| lad | 2 | `tfcoil.m_tf_coil_superconductor`, **70** |
| st | 9 | `costs.{coe,coecap,coefuelt}`, 10¹⁶–10¹⁸; `power.e_plant_net_electric_pulse_{mj,kwh}`, **54.6** *(measured at a run-time state by A59 (driver-predicate-mode)'s gate G8, 2026-09-11; this table's other entries are the ad-hoc artifact read)*; `heat_transport.p_plant_electric_net_mw`, 13.8 *(measured, same stage)*; `physics.nd_plasma_electron_max_array`, 10 |

The lad entry is not incidental. `tfcoil.m_tf_coil_superconductor` is the argmax of lad's
restricted A1 residual in 21 of 25 A38 runs and the one similarity term no linear image of the
carrier explains (A38; V3 G3c). Under the frozen denominator a value 70× the harvest median is
scored 70× harsher than a current-value test would score it. **Whether that argmax is a scaling
artefact is a hypothesis the trial answers directly**, and either answer is a result.

**The trial, pre-declared.** One implementation, in `ystate.py`, selected by a spec-level mode
(`predicate: frozen | mixed`) recorded in every artifact and every run record, default
**`frozen`** so every V2/V3 record reproduces. The driver
([`module_solve.py`](../../../process/core/solver/module_solve.py)) and the replay engine both
import the predicate from there, so both consume the change with no second implementation (the
D14(c) rule). A pass is **decisive** when some component is at or above τ on the frozen
denominator and below it on the mixed one — the only way the two modes can disagree. Then:

1. **Neutrality gate.** Default mode reproduces V3's Phase A records bit-for-bit — node calls,
   objective hex, audit hex, exit state — the A38 construction, a bit-comparison not a tolerance.
2. **The identity with teeth.** Under `mixed`, every run with no decisive pass is bit-identical
   to `frozen` in counts and exit state. This holds by construction; a run where it does not is a
   defect in the implementation, not a finding.
3. **The binding set, named.** Per config and arm: the decisive passes, the components that made
   them decisive, `|y_i| / s_i` there, and whether that component was the pass-holding argmax
   under `frozen`. Plus a doctored-component tooth in G4's shape: a component set to `100 s_i`
   with `dy = 50 τ s_i` fails `frozen` and passes `mixed`; the same `dy` at `y = s_i` fails both.
4. **The measurement.** Phase A (A0, A1; 25 seeds; three configs; δ = 0.10) under both modes:
   per-arm sweep and node-call counts, the A1/A0 ratio with its seed bracket, and the exit audit
   **on both rulers** — frozen for comparability with V2 / V3 / A38, mixed because an audit on a
   ruler other than the predicate's is a comparison at unmatched accuracy (§3.3). Phase B (B0, B3)
   only if Phase A shows a decisive pass on an in-loop component.

**Acceptance for adoption.** Gates 1–3 pass, *and* the measurement lands in one of two places,
both of which adopt: **(a) neutral** — no decisive pass anywhere, or only on components that
never held a pass, and every ratio moves by less than its seed bracket — the conventional
predicate is adopted as the easier-to-defend equivalent; **(b) non-neutral** on a named set — it
is adopted **and** the V3 ratios that moved are re-stated as metric-dependent, with the size of
the move and the components responsible. The only outcome that blocks adoption is a gate
failure, which is a result about the implementation and is reported as such. Adoption means:
`mixed` becomes V4's default predicate *and* its audit ruler; `frozen` stays selectable for
cross-study comparison; V3's published numbers are not retro-edited.

**Cost.** Phase A under one extra mode is 150 single-evaluation runs (A1u retired, item 0) plus
gates — the same order as item 1a's second amplitude. The `ystate.py` change is one denominator
in two branches plus a mode field. A26's replay ladder (`run_a26.py`) can be re-run under
`mixed` for a cheap first look before Phase A is spent, and at `hoist = 0` it exercises the I-12
population directly, since there `costs` is still inside the loop.

**Two traps it sets.** *(i)* `components_sha256` covers keys, categories, scales, and — for a
non-A18 mode — the spec mode and floor in a preamble, but not the predicate form. A `mixed` run
whose record does not name the mode is indistinguishable from a `frozen` one after the fact; the
predicate mode must enter that preamble the way `SPEC_MODE_A26` and the floor did (A26 AD5), so a
mismatched pairing is refused rather than silent. *(ii)* The mixed ruler reads *lower* than the
frozen one wherever the term binds, by construction. A V4 table that shows only the mixed audit
beside V3's frozen one would report an accuracy gain that is a change of ruler. Both columns, or
neither.

### 5b. One convergence filter and one format for every Phase B cost table *(user question, 2026-09-07; **the approach to implement requires the user's review and approval**)*

**The problem.** V3's Phase B statistics filter seeds five different ways (census of
2026-09-07, from `v3_report_analysis.py`, not from the captions): the correctness checks (1, 2,
3, the location diagnostic) admit only **both-converged pairs**, a set per pair; §5.5's
node-call sums are published on **two** sets, identical-ok and identical-converged, with the
headline on converged; §5.5.1's per-module sweeps run on **identical-ok only**; §5.5's
prime-call table and §6's sweeps-per-evaluation sum **each arm's own ok runs**, unpaired; §7's
timing is unfiltered. So on lad §5.5.1 runs on 20 seeds while the headline above it runs on 11,
the prime table's node-call column disagrees with §5.5's for the same arm (lad B0: 1 976 331
against 1 917 384) and its caption does not say why, and §5.5 publishes sums whose magnitudes
carry the row's n while §5.5.1 and §5.3 publish per-run means. None of this is wrong in
isolation; together it means "the cost result" has no single denominator.

**What the two constructions actually differ by** (read from the campaign records on
2026-09-07 while answering the question; **not yet from a committed script** — the script that
implements this item re-derives every number here before any is published):

- **On every config the set where *every* arm converged equals the set where B0 and B3 both
  converged: 22 / 11 / 22.** A single converged set per config therefore costs check 2 and
  check 4 nothing, and is the set §5.3 already uses.
- **lad's 9 ok-but-unconverged seeds fail with `ifail = 5` in every arm**, at roughly 11 k
  node calls (B3 ≈ 7 k) against ≈ 165 k for a converged run. They are config-invalid seeds:
  uniform, cheap failures carrying no information about the architecture. The identical-ok
  construction puts those 9 failed runs into a 20-run set; the pooled ratio barely notices
  (0.460 against 0.450, report §5.5) but the per-run median moves from ≈ 0.52 to ≈ 0.62, because
  nearly half the "runs" are the cost of failing.
- **st's 3 are three different things.** Seed 17 fails cheaply in every arm. Seed 5 is a
  **B3-only** failure that cost ≈ 2.7 × B0's converged run. Seed 10 is a **B0-only** failure
  that cost ≈ 5.2 × B3's converged run. The two constructions differ (0.583 ok against 0.533
  converged) because of two asymmetric failures pointing opposite ways — and the converged set
  drops both silently.

**Candidate approach — for review, nothing decided.**

1. **One seed set per config, pre-declared: the seeds on which every arm converged**
   (`status == ok` AND MFILE `ifail == 1`). It is what the correctness checks already use, it
   equals the B0→B3 pair set on V3's data, and it makes every Phase B table — checks 1–4,
   §5.3, §5.5, §5.5.1, §6 — share one n per config.
2. **Failures accounted on the page, not dropped.** A per-config table of the seeds outside
   that set: which arm failed, its `ifail`, its node calls, and the other arms' node calls on
   the same seed. This is what the converged set hides, and it replaces the identical-ok
   construction as the sensitivity; the ok-set pooled ratio is published once beside it, not
   in every table.
3. **One format**, the one §5.3 now uses: absolute cells as per-run means with the seed
   bracket; the ratio against B0 as the pooled value (sum/sum, campaign cost), the per-run
   median with [min, max] (typical run), and the count of runs where the arm is worse. Sums
   retire, so no magnitude carries its row's n.
4. **One reference and one denominator.** B0 is the reference everywhere, B3/R published once
   (§5.5's second table) on the same set. Prime calls become a column of the same table on the
   same set, which satisfies trap T11 in-table and retires the per-arm-ok side table. The
   solve-phase node count is the denominator throughout; §5.5.1's output-pass sweep is
   subtracted or stated in every caption that uses the per-node census.
5. **Declare it.** V3's plan computed both constructions and accepted on neither (check 4 has
   no acceptance rule). V4's plan names the set and the failure table before the campaign.

**The fairness caveat to weigh.** Converged-only is the fairer *cost* statistic — a run that
produced no accepted answer did not pay the cost of the architecture doing its job, and on lad
the alternative is a set that is 45 % failures. But converged-only can flatter an arm that
fails on expensive seeds, and st seed 5 is exactly that for B3. Item 2 is what keeps item 1
honest: without the failure table, item 1 alone is tidier than today, not fairer.

**Can be applied to V3's data.** Everything above is analysis-only on records that exist; it
could be published beside V3's tables as a re-presentation, with the additivity check of
protocol §15. That is not done and is not proposed here without the user's decision on the
approach.

## Machinery owed

### 6. I-19's other half

The plan's pre-declared within-cluster construction was added to `v3_report_analysis.py` but
**not to `phase_b.py`'s tally**, so the recomputation currently computes a field the tally does
not. `--verify` cannot compare a cell that exists on only one side. Add it to the tally so both
sites agree.

### 6a. Two instrument weaknesses found while settling `vacuum`'s liveness *(2026-09-07)*

Both surfaced by an independent read-only investigation of whether `vacuum` is feed-forward
on the three experiment decks (it is — see report §4.5). Neither bites in V3; both are real.

**(a) `a33_postsolve.py` classifies read sites by file prefix, not by class.**
`CANDIDATE_FILES` maps `"vacuum"` to the prefix `process/models/vacuum`, but that file holds
**two** classes: `Vacuum` (the post-solve candidate, lines 18–733) and `VacuumVessel`
(lines 736–994), and `vacuum_vessel` is a live, needed M3 node. A read of a `vacuum.*` output
inside `VacuumVessel` would be silently classified "internal to candidate `vacuum`" and marked
dead — a wrong exclusion with no warning. Verified harmless here: zero reads of any of the six
`vacuum` output fields occur in lines 736–994. Fix: classify by the enclosing class, not the
file. **[data gap]** The classifier's strongest claim rests on an AST scan plus a DSM crawl; a
committed **runtime read census** (`PROCESS_IDF_PROBE=modules`, closed at the
`_call_models_once` boundary) would convert it to a direct observation. The investigation ran
one ad hoc and it agreed exactly; under protocol §15 it cannot be cited until it is a committed
stage — a natural `a33_postsolve.py readcensus` subcommand emitting `readcensus_<deck>.json`.

**(b) Phase A records do not carry their post-solve provenance.** In every Phase A run record
`post_solve_totals` is null and `PROCESS_ARCH_POST_SOLVE` is absent from the recorded `env_*`
list, even though `phase_a.py` sets it (to the *nolift* artifact). So a Phase A per-block table
cannot literally be "read from the run's own record" the way a Phase B one can; its grouping
came from the committed artifact. The content is independently confirmed (`node_census.counted`
shows `vacuum`/`costs`/`water_use` at 0 in the block arms while M3's other nodes run 3 each),
but the recording gap is in `run_one.py` and should be closed so Phase A and Phase B records
carry the same provenance fields.

**(c) G4's teeth never doctor a `vacuum.*` component.** They doctor `costs.blkcst`, which
demonstrates the exclusion *mechanism* in both directions but does not independently certify
`vacuum`'s *membership* — that rests on A33's derivation (and now on the read census in (a)).
A V4 G4 should doctor one component from each excluded namespace.

### 7. Re-run G1 / G2 / G3 / G3c at the campaign commit *(report §3)*

Those four gates bound A40's `process/` tree (`f117a854`); the campaign ran at `8e3723d2`. The
difference is the I-17 instrument alone — one file, 41 insertions, all counters, zero
non-comment lines — and G0 re-established neutrality at the campaign commit, so the gap is
judged closed. **The clean version re-runs all four at the commit that actually ran.**

### 8. B2 in the DSM overlay set *(see [`DSM_PLAN.md`](DSM_PLAN.md) §5)*

The originally requested arm set (A0/A1/B0/B3) cannot show the outer verification loop at all:
B0 skips it via the single-block guard, B3 via `trust`. Only B2 exercises it. Since the V3
campaign's sharpest result is B2 vs B3, the DSM needs B2 to depict what it most needs to
explain. Cost: one config entry.

## From A43 (st-trust-gap), 2026-09-10 — candidates, attributed to its report §9

### 9. Establish causality on `st_regression` with a controlled sub-tolerance injection *(A43 P5)*

A driver switch that perturbs the handover state by a named sub-τ amount in one named component,
then the optimiser's iteration count. A43 measured that `B2` and `B3` hand the optimiser states
differing by at most 3.3e-9 (below τ) and that st's trajectory differs on four clean seeds; that
the second causes the first is **inferred**, from V3's location diagnostics. If the count moves
under a controlled injection the mechanism is demonstrated; if it does not, A43's reading is wrong
and that is a result. A driver change (needs approval); one configuration; small run budget.

### 10. A permutation control for the block-slack discriminator *(A43 P7)*

Run the same blocks in a different order and check whether the pass-2 movers follow schedule
position rather than block identity — confirming A43 §6.3 from the other side. One arm, one
configuration.

### 6b. The trace instrument records an argmax on a zero residual *(A43 P8)*

`module_solve.trace_pass` records an `argmax` component even when `res.max == 0.0`, so a reader
can invent a mover where nothing moved (A43 §5.3 found and named the artifact). One-line fix in the
V4 copy: `argmax: null` when the residual is exactly zero.

### 11. `tfcoil.insstrain` above τ at the accepted point on the pulsed configurations *(A57 (driver-output-path), 2026-09-10 — for the user)*

**Measured, not diagnosed.** With the exit audit at the plan's declared position (the entry to `write_output_files`, from a
bit-exact snapshot), gate G9's seed-0 runs show exactly **one** restricted coupling-state component above τ = 1e-6 on both
pulsed configurations, in `B1` and `B3` alike: `tfcoil.insstrain` at 7.12e-3 (`large_tokamak_nof`) and 7.02e-3
(`low_aspect_ratio_DEMO`) scaled; `st_regression` has none (restricted max 1.6e-11). Identical between the flat and the
partitioned arm on the same seed, so it is a property of the handed-over state at the lifted optimum, not of the partition.
Candidate causes, none established: a genuinely unconverged coupling; a component whose measured scale is too small (the
frozen ruler); a discontinuity in the TF-coil insulation-strain model at the accepted point. **Decision for the user:**
diagnose before the campaign (one task: which node writes it, what it depends on, its scale in the coupling-state
artifact, its behaviour over seeds), or let the campaign measure it and report it as the dominant term of the restricted
statistic on those configurations. Until decided, G4 (A52) and the tally (A53) make it visible rather than average it away.

**Extended 2026-09-11 (A52 (harness-gates); confirmed from the orchestrator's own records).** The same component is above τ on the
**reference arm `BR`** — PROCESS as shipped, every switch unset — at 6.991e-3 (`large_tokamak_nof`) and 7.021e-3 (`low_aspect_ratio_DEMO`),
and on `B0` at the same values; `B1`/`B3` read 7.119e-3 / 7.021e-3. Its measured scale (6.05e-3) is its own magnitude (5.9e-3–7.7e-3), so
this is a ~0.7 % change of the value in one further sweep, not a scale artefact; `B0`'s flat loop converged every evaluation in 1–6 sweeps at τ.
The user asked why `B0` is then not converged, and **A61 (insstrain-diagnosis)** was dispatched (2026-09-11). **Its classification (verification
pending at its merge):** (d) in its output-mode form, and an artefact of the exit audit rather than of convergence — PROCESS's output path
permanently raises `tfcoil.n_rad_per_layer` from 100 to 500 before the snapshot; the field is not a coupling-state component, so the snapshot
neither captures nor restores it, and the audit's sweep runs the TF-coil stress model on a different grid than the loop did. Evidence: 0 of
840/846/827 components differ between the loop's last sweep and the audited state (9/9 runs); restoring that one field alone gives a residual of
exactly `0x0.0p+0` in every arm, restoring the other 85 changed fields and not it leaves it unchanged; a second sweep moves nothing; the grid
dependence is `v(n) = v_∞ + C/n`. On `st_regression` the stress model returns `None`, the component latches and is classified discrete. Two
PROCESS findings for `PROCESS_code_analysis`'s bug file: the MFILE's `insstrain` is not the value the solve converged (0.70–0.72 % off, every arm
including as shipped), and the `None` latch. **Consequence if verified:** the exit audit's snapshot must restore the whole data structure
(harness-side, a new task), which changes `exit_audit.*` on every record — G1 needs one more named exclusion and GR's compared set must drop the
audit residual with its reason; the "one component above τ" statements of A57 and A52 are then withdrawn as convergence statements.

**Verified and closed as a convergence finding, 2026-09-11 (A61 merged, `fd480aff`; orchestrator's assessment §12).** The classification
stands: the code lines were confirmed at `c0ae5b28` and one record spot-checked with an independent reader. `B0` and `B3` converged
to τ; the residual was the instrument's. **Ruling D25** carries the fix (A62 (exit-audit-restore)): the snapshot and restore cover the
whole data structure with a derived restored set; G1 straddles the instrument change against the orchestrator's before capture at
`fd480aff`; GR's compared set loses the inherited audit residual with its reason. What stays open is **I-21** (what else the output
pass leaves inconsistent in the written file). The three PROCESS findings were filed directly in
`PROCESS_code_analysis/docs/bug_reports/2026-09-11_tfcoil_output_mesh_written_insstrain_and_none_latch.md` at the user's instruction (uncommitted there; copy in `docs/reports/outgoing/`).
**Fix landed 2026-09-11 (A62 (exit-audit-restore), `a3407d5d`):** the statistic this item was about now reads **0 components above τ** on 31 of 31 declared-position records, and `tfcoil.insstrain`'s own residual is exactly `0x0.0p+0` on `BR`/`B0`/`B1`/`B3` on both pulsed configurations; the new maximum is 1.15e-11 (`heat_transport.tlvpmw`) on `large_tokamak_nof` and exactly 0 on `low_aspect_ratio_DEMO`. The 0.7 % gap between the written `insstrain` and the solved one persists as I-21's per-run handle (the `after_run` residual on the reference arm).

### 12. Gate G4's doctored runs bypass `--resume` — **discharged 2026-09-14 (A71, `24e5fe2f`): `--gate audit_restriction --resume` keeps its 12 records, 0 runs** *(A65 (harness-folders), 2026-09-14)*

`gates/gate_audit.py` passes `resume=False` to `run_all` for its doctored runs, so every press of `--gate all` makes **12 PROCESS runs** there whatever the tree holds (A65's stamp survey: 16 re-made of 178, 12 of them G4's). Gate G7's own tooth adds one by design. If the doctored runs' inputs are stamped like any job's, the pool can keep them under `--resume` and the fixed cost of a press falls from 13 runs to 1. Not a correctness matter — the gate passes either way — a run-budget one (the user, 2026-09-11: reduce PROCESS runs where not necessary). A small harness task; no schema change expected.

### 13. Gate G1's `--resume` press rewrites the `after` manifest's commit *(A67 (written-file-gap), 2026-09-14)*

Under `--gate switch_neutrality --resume` with every record kept, the `after` capture's manifest is rewritten with the pressing commit while the records it indexes stay at theirs (`b784158c` in A67's press). The verdict prints both lines, so nothing is hidden, but a manifest should carry the commit of the records it indexes, or state both fields by name. Cosmetic to the verdict; a trap for a reader of the manifest alone. Small harness task; no runs.
