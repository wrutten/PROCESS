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

## Schedule and driver defects

### 2. Empty blocks are still swept *(I-20a)*

On `st_regression`, `Pulse.run()`'s entire body is guarded by `if i_pulsed_plant == 1` and is
a **pure no-op**; `times.t_plant_pulse_burn` is absent from that deck's measured 827-component
coupling state; the routing rule correctly demotes `pulse` to post-solve (5 executions per
run). **But the `PULSE` block survives in the schedule after its only member has left it, and
is swept 570 times per run in B3 and 1131 in B2, executing nothing** — the DSM register's V12
trap in live form. Roughly 3.4 % of st's B3 block sweeps are empty visits.

Fix, driver-side and provably neutral: **drop a block whose membership is empty after
hoisting**, and **skip a post-solve node whose measured write set is empty**. Costs no model
evaluations, so no V3 number moves — but it feeds the per-sweep-overhead question (item 3),
and it needs the user's approval as a driver change.

### 3. Count what the per-sweep overhead actually is **[data gap]**

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
