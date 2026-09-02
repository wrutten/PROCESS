# A30 (phase-b-critique) — the adversarial pass over A28, re-derived from raw

> **Document status** — **CURRENT · TASK REPORT, open.** Written by task A30 (phase-b-critique),
> 2026-09-02, on branch `A30-phase-b-critique`, branched from `architecture_surgery` after A28's
> merge (`126a0d92`). It is archived to `deprecated/` when the task merges and stays authoritative
> there (trap T3). Nothing here is merged; nothing is pushed; **no merged document was edited** —
> corrections are proposed in §5 as exact quoted text, for the orchestrator to apply.

| | |
|---|---|
| **Task** | A30 (phase-b-critique) — critical evaluation of A28's Phase B results: methodology errors, systematic bias, and whether the comparison isolates the architecture (user, 2026-09-02) |
| **Method** | re-derivation from the **raw** per-start `metrics.json` and per-rung `result.json` artifacts under the main checkout's `runs/a28/` and `runs/a26/` (read-only). A28's analysis JSONs were used only as the thing to compare against, except §4.8 where an artifact's *coverage* is itself audited. **No PROCESS solve was run.** |
| **Script** | [`arch_surgery/idf_probe/a30_critique.py`](../../idf_probe/a30_critique.py) — every number below comes from `python a30_critique.py all`, run at commit `73329923` (protocol §15). Its own checks are shown capable of failing: **10 of 10 teeth bite** (stage `teeth`), each by doctoring an in-memory copy of the raw rows a check watches and confirming its output moves. |
| **Denominators** | 870 `metrics.json` records under `runs/a28/` were read; the campaign tables below re-derive from the 300 `h5/` records, the census from the 225 `h5_audit1/` records, the ladder from the 168 `ladder/` records, the matched re-run from the 25 `h5_matched/` records, Phase A from the 51 `runs/a26/*/replay_acc_*/result.json` rung records |
| **Date** | 2026-09-02 |

---

## 1. Verdict

**A28's arithmetic holds.** Every published Phase B table re-derives from the raw artifacts to the
digit: the paired robustness 2×2s, the drop censuses, all five paired-ratio comparisons on all
three decks, the accuracy census, the matched-robustness re-run, the ladder envelopes under both
constructions, the hoist shares, the gate-point table, the moved-constant census, the I-12 entry
census, the timing repetition counts, and Phase A's two published triplets (§4). The acceptance
rule is pre-declared, symmetric, and its numbers reproduce under both it and its natural
alternative (§4.1).

**Two labelling errors stand in the merged documents, both of the T11 class** — a number published
under a description that is not what was computed:

1. **The refusal table's column "starts not solved" actually counts crashed runs only**, and on
   two decks it contradicts the robustness table four sections earlier in the same document (§2.1).
2. **"The partition alone, on that test case, costs more" describes a comparison that varies the
   partition *and* the burn-time lift.** No arm pair in A28's design isolates the lift, so the
   partition's own share is not separately identified anywhere — and the document states the
   opposite in three places (§2.2).

**One omission is a real audit-trail gap**: the raw runs record **four different commits, most
with uncommitted changes present**, and neither report mentions it. From the artifacts alone the
risk is bounded but not closed — six repeated configurations reproduce **bit-identically** across
three of those heads, and no commit after the campaign head touches `process/` or the measurement
subprocess — but the gate stage ran on a *dirty branch-point tree whose content is in no commit*
(§2.3). Full tie-down is A29's from-scratch re-run, as the queue already assigns.

Everything else the queue row fixed in advance **passed**, each with its number in §4.

---

## 2. Findings, ranked by consequence

### 2.1 F1 — "starts not solved" counts crashes, and contradicts §7.6 in the same document

`MDA_partition_exp_results.md` §7.7 (and the identical table in the A28 report §1.2) is headed:

> | test case | arrangement | starts not solved | of | refusals by the coupling-state test | …

Re-derived from the 300 raw campaign records, the numbers in that column are the counts of starts
whose run **crashed** (`status ≠ ok` — the run raised), not the starts not solved
(`status ≠ ok` **or** `ifail ≠ 1`):

| deck | arm | §7.7 says "not solved" | actually crashed | actually not solved | of |
|---|---|---|---|---|---|
| `large_tokamak_nof` | R / A0′ / A1′ | 3 / 3 / 3 | 3 / 3 / 3 | 3 / 3 / 3 | 25 |
| `low_aspect_ratio_DEMO` | R / A0′ / A1′ | 2 / 4 / 5 | 2 / 4 / 5 | **13 / 13 / 14** | 25 |
| `st_regression` | R / A0′ / A1′ | **0 / 0 / 0** | 0 / 0 / 0 | **1 / 2 / 3** | 25 |

On `large_tokamak_nof` the two coincide, which is presumably how the label survived. On the other
two decks the same document already publishes the correct solved/not-solved picture in §7.6 — on
`st_regression` its 2×2 (21 both / 2 only control / 1 only variant / 1 neither) *implies* 2 and 3
not-solved for the arms §7.7 lists as 0 and 0, and on `low_aspect_ratio_DEMO` §7.6 implies A1′ has
14 not-solved where §7.7 says 5. **The same quantity is quoted twice with different values** — the
exact failure class this task was told to sweep for (it caught three errors in A18's report).

The *conclusions* drawn from the table survive relabelling: the refusal attribution itself is
correct (§4.4), because the attribution argument only ever needed the crashes. The A28 analysis
JSON even names the field correctly (`n_starts_not_ok`) and `a28_tables.py` prints "not ok"; the
error was introduced when the prose tables were written. Proposed corrections in §5 (C1).

### 2.2 F2 — "the partition alone" is the partition plus the lift; the lift is not separately identified

Queue check 1 asked whether any arm isolates the burn-time lift. **None does**, and this is
verifiable from the resolved arm records: on the pulsed decks `A1p_nohoist` carries
`arch_lift_sites = ['burn_time']` and `nvar = n+1` (21 on `large_tokamak_nof`, 20 on
`low_aspect_ratio_DEMO`) with the hoist off. So the arm-pair algebra over A28's five arms gives:

| pair | varies (from the resolved records; A28's own manifests agree) |
|---|---|
| `A0p → A1p` | grouping + lift + hoist (the headline) |
| `A1p_nohoist → A1p` | hoist alone |
| `A0p → A1p_nohoist` | **grouping + lift** — two things |

There is no `per_module + lift, no hoist` versus `per_module, no lift` pair and no `flat + lift`
arm, so the lift's own share cannot be extracted by any subtraction. That is a legitimate design
choice (D15(b): the architecture is tested as a package) — but the standing document then writes,
of the `A0p → A1p_nohoist` number **+2.88 %** on `large_tokamak_nof` (re-derived: +2.88 %, n = 22
kept of 25, 3 cheaper / 19 dearer):

> §7.8: "**The headline is therefore the proposed architecture and never the partition's
> benefit**: the partition alone, on that test case, costs more."
> §8: "The partition alone, on that test case, costs more."
> A28 report §1.4(2): "— the partition alone costs more there …"

**+2.88 % is the price of the partition *and* the lift together.** The lift is half of the user's
stated independent variable, it enlarges the design vector by one (a measured ~+4.8 % of optimiser
evaluations: 660 against 630 gradient-bearing `call_models` at the gate point), and its share of
the +2.88 % is unknown. The sentence claims an isolation the design does not have. On
`st_regression` the equivalent statement *would* be true (no lift exists there; `A0p →
A1p_nohoist` = −3.37 % is the partition alone) — which makes the unqualified cross-deck wording
worse, because the reader has just been told the decks are the same comparison. Proposed
corrections in §5 (C2). The honest summary sentence is: *the partition-plus-lift costs more there,
and no arm pair isolates the lift.*

### 2.3 F3 — the runs record four commits, most dirty, and the reports do not say so

Loose end (e). Census over all 870 `metrics.json` under `runs/a28/` (stage `provenance`):

| stage | head recorded | dirty | n |
|---|---|---|---|
| gate | `dc18c05b` (the branch point) | **True** | 16 |
| neutrality | `dc18c05b` | True | 26 |
| calibrate | `dc18c05b` / `9634bb06` / `9634bb06` | True / True / False | 55 / 47 / 6 |
| **h5 (the campaign)** | `9634bb06` | **True** | **300** |
| ladder | `9634bb06` / `492c6fc8` / `492c6fc8` | True / True / False | 17 / 89 / 62 |
| h5_audit1 | `492c6fc8` | True | 225 |
| h5_matched | `492c6fc8` / `0fae5e1a` | True / False | 14 / 11 |

Neither the A28 report nor the standing document mentions any of these heads or any dirty flag;
the standing document's Provenance section says only "all measurements are at base commit
`c0ae5b28`". Three artifact-level facts bound the risk:

1. **No commit after `9634bb06` touches measured code.** `git diff --name-only` per interval:
   `9634bb06..492c6fc8`, `492c6fc8..0fae5e1a` and `0fae5e1a..0c18dfcc` (the merge) touch **zero**
   files under `process/`, and neither `run_one.py` nor the `ystate_*/writeset_*` artifacts —
   only driver/analysis/report layers.
2. **Six repeated configurations reproduce bit-identically across heads.** For every deck × arm in
   {A0′, A1′}, the same configuration (unperturbed start, τ = 1e-6) was run in the gate stage
   (`dc18c05b`-dirty), the campaign (`9634bb06`-dirty) and the ladder (`9634bb06`-dirty or
   `492c6fc8`): **6 of 6 agree in cost to the model call *and* in `norm_objf` as exact hex** —
   e.g. `st_regression` A0′ = 42 756 and A1′ = 37 312 in all three stages.
3. `tree_contains_base_commit = True` in every record.

What the artifacts **cannot** close: the gate and neutrality runs are stamped
`dc18c05b`-**dirty**, i.e. they ran *before* the commit that built A0′ — the code they exercised
(including the `flat_state` arm they gate) existed only as uncommitted changes and is in no
commit as of that stamp. `dc18c05b..9634bb06` does touch `process/core/caller.py`,
`process/core/solver/module_solve.py` and `run_one.py`, which is the A0′ build itself; the
cross-stage identity above is the only artifact evidence that the dirty tree behaved as
`9634bb06`. That evidence is strong for the solve path (bit-identity of six configurations) and
absent for everything else. **This is exactly the paper trail A29's from-scratch re-run closes**,
and the reports should say what was run where — proposed text in §5 (C3).

### 2.4 F4 — two small misdescriptions of the start population

- The standing document's scope section (§8) says "**Phase B is 25 perturbed starts per
  arrangement**". Re-derived from the raw records: `start000` carries **no perturbation record**
  in any arm on any deck — `run_one.py` applies the perturbation only when the seed is non-zero,
  so the campaign is **24 perturbed starts plus the deck's own unperturbed point**, identical in
  every arm (pairing intact). One line, §5 (C4).
- §7.13 says the Phase B ladder's common population is "2 on `large_tokamak_nof`, 1 on
  `st_regression`" without saying **which** start survives: on both `st_regression` and
  `low_aspect_ratio_DEMO` it is `start000` — the **unperturbed deck point**. So the Phase B
  matched-accuracy cost figures on `st_regression` (−21.6 % / −22.5 %), and the inner tolerance
  0.01 that §7.9.1's matched-robustness re-run was read from, rest on the unperturbed point alone.
  The re-run's *outcome* is then measured over 25 starts, so the setting's provenance is the only
  thing affected — but "1 start" and "the unperturbed start" are different disclosures.

### 2.5 F5 — a stale improvement item

§6.7 item 2 asks for "a matched-accuracy robustness comparison where one is possible" as future
work, but §7.9.1 already made that comparison on `st_regression` — the only deck where the
document itself shows it is both possible (impossible on `large_tokamak_nof`: block arm's loosest
setting delivers 6.8e-13 against the flat arm's 1.3e-8, re-derived) and informative (identical
accuracy on every paired start on `low_aspect_ratio_DEMO`, re-derived: equal on 22 of 22). The
item as written asks for something the document elsewhere records as done or structurally
unavailable on every deck. Minor; §5 (C5).

---

## 3. The queue row's loose ends, each resolved with a number

### 3.1 (a) The acceptance rule — named, declared, symmetric, and both readings computed

**The rule** (re-implemented from raw, reproducing `gates.drop_census` + `a25_h5.compare`): a pair
of runs enters the paired cost ratio iff, in **both** arms, `status == ok` and `ifail == 1`, and
the two arms' `norm_objf` agree to **1e-6 relative** (`OBJF_RTOL`, PROCESS's own idempotence
rtol). The objf clause is decision **D15(c)**, fixed in A25 — before any A28 number existed — and
it is computed as a spread over the pair, with no reference to direction. **It is declared in the
standing document**: §7.8's drop-census table carries the `objf mismatch` column and the sentence
"a start leaves the comparison only through this table".

**Both readings, re-derived from the 300 raw records** (RULE A = published; RULE B = both-solve,
no objf gate):

| deck | comparison | RULE A | RULE B | pairs dropped by the objf clause (relative spread) |
|---|---|---|---|---|
| `large_tokamak_nof` | A0′→A1′ | **−1.63 %**, n = 22, 20/2 cheaper | −1.63 %, n = 22, 20/2 | none |
| `st_regression` | A0′→A1′ | **−6.18 %**, n = 20, 20/0 | **−6.15 %**, n = 21, 20/1 | `start015` (1.3e-2) |
| `low_aspect_ratio_DEMO` | A0′→A1′ | **−21.2 %**, n = 8, 6/2 | **−20.6 %**, n = 11, 8/3 | `start001` (3.1e-4), `start011` (**1.3e-6**), `start013` (**2.1e-6**) |
| `st_regression` | R→A0′ | +3.23 %, n = 22, 1/21 | +2.79 %, n = 23, 2/21 | `start024` (1.3e-3) |

This reproduces the orchestrator's raw recompute exactly (−6.15 % over 21, 20/21 cheaper;
−20.6 % over 11) and identifies the discrepancy as the objf clause. Three observations, none an
error:

- **The clause moved the headline toward the variant on both affected decks** (−6.15 → −6.18 and
  −20.64 → −21.21) — small (0.03 and 0.57 pp) and not evidence of bias, since the rule is
  symmetric and pre-dated the data, but worth having on the record.
- Two of `low_aspect_ratio_DEMO`'s three dropped pairs sit at relative spreads of **1.3e-6 and
  2.1e-6 against a 1e-6 gate** — barely over. On a deck already inconclusive at n = 8, the rule is
  doing borderline work; under RULE B (n = 11) the deck is still inconclusive (0.24–3.32 range),
  so no verdict moves.
- The verdict sentence "20 of 20 cheaper" is RULE A's; under RULE B it is 20 of 21. Both true of
  their own populations, both computable from the published census. No correction needed.

### 3.2 (b) The sixth rung — Phase A has six taus per family; Phase B has five; no phantom rung

Commit `a04e1cf7`'s "six joint rungs against six flat" describes **Phase A**, whose ladder is
defined in `run_a26.py`: `FLAT_TAUS = BLOCK_JOINT_TAUS = (1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-8)` —
six values, **the same six for both knobs**. `run_a28.py`'s five taus per family (no 1e-2) are
**Phase B's** ladder, a different instrument. Verified from the artifacts themselves: the
regenerated `runs/a26/` rung records carry exactly those six tau values in both families on 3 of 3
decks (`same_knob_same_values: True`), and the Phase B `runs/a28/ladder/` records carry five in
both families ({1e-3, 1e-4, 1e-5, 1e-6, 1e-8}), plus the inner-only family (5 rungs in Phase A,
4 in Phase B). **The matched-count construction is genuinely same-knob-same-values in both
phases.** The orchestrator's question dissolves: two phases, two ladder widths, each internally
matched.

### 3.3 (c) Headline-row selection — one declared rule, the same for both constructions

The published Phase A triplets are, in every case, **the comparison row whose flat rung is
τ = 1e-6** — "the accuracy the flat control delivers at the study's own calibration point", which
is exactly how §4.4.2's table annotates it ("*at the accuracy the flat control delivers at the
study's own calibration point, τ = 1e-6*") and how §7.13 annotates the Phase B table. Re-derived
from the 51 raw Phase A rung records (not from `matched_accuracy.json`), the row reads:

| deck | all-settings at the τ=1e-6 row | matched-count at the same row | published |
|---|---|---|---|
| `large_tokamak_nof` | −4.32 % (9 062 / 9 471) | +33.38 % (12 632 / 9 471) | −4.3 / +33.4 ✓ |
| `low_aspect_ratio_DEMO` | −4.53 % (19 086.8 / 19 992) | +27.36 % (25 462.8 / 19 992) | −4.5 / +27.4 ✓ |
| `st_regression` | −13.06 % (9 037 / 10 395) | −15.24 % (8 810.5 / 10 395) | −13.1 / −15.2 ✓ |

The rule is **identical for both constructions and all decks** (the rows come from the same flat
envelope; only the block curve changes), so no selection inconsistency exists. The full row tables
(stage `phase_a`) also show the chosen row is not adverse-selected: on `large_tokamak_nof` the
matched-count rows run +33.4 / **+38.6** / −16.3 / −14.3 / +15.0 — the headline row is neither the
best nor the worst for either construction. The orchestrator's spot-read is explained:
`low_aspect_ratio_DEMO`'s *first* all-settings row (+33.40 % at the flat τ=1e-8 accuracy, where
the bit-exact joint rung is the envelope in **both** constructions) numerically coincides with
`large_tokamak_nof`'s matched-count headline (+33.38 %) — two different cells that happen to round
to the same number.

### 3.4 (d) AD4 — the moved-constant contamination is bounded, and the headline does not move

On `st_regression`, per-start contamination re-derived from the raw `module_solve_totals` (both
arms carry the predicate; R does not):

- **No clean pair exists**: 0 of 20 kept pairs have zero affected solves in both arms, so
  "recompute excluding the affected solves" is not available from the artifacts (the cost of an
  individual affected solve is not recorded). What is available is restriction by the per-start
  contamination **difference** between the arms (`frac(A1′) − frac(A0′)`, range −0.131 to +0.015):

| restriction | n | median A1′/A0′ |
|---|---|---|
| none (the headline) | 20 | **0.9382 (−6.18 %)** |
| pairs with \|frac diff\| ≤ 0.02 | 10 | 0.9382 (−6.18 %) |
| pairs with \|frac diff\| ≤ 0.05 | 17 | 0.9378 (−6.22 %) |
| pairs with \|frac diff\| ≤ 0.10 | 19 | 0.9385 (−6.15 %) |
| both arms' fraction < 0.20 | 16 | 0.9382 (−6.18 %) |
| split-half, smaller vs larger frac diff | 10 / 10 | 0.9387 vs 0.9382 |

**Bound: every artifact-derivable restriction moves the −6.18 % median by ≤ 0.07 pp, and the sign
is stable in all of them.** The correlation that does exist (Pearson r = 0.674 between frac-diff
and ratio over the 20 kept pairs) is carried by a single start — `start012`, ratio 0.160 with the
largest differential (−0.131) — which is the distribution's **min**, not its median; §7.8 already
refuses to rest anything on that tail. What cannot be bounded from artifacts is a **common-mode**
inflation of both coupling-state arms (and of A0′ inside the R→A0′ = +3.23 % stopping-rule term,
where the contamination sits in one arm only); the run that closes it is the no-exclusion-predicate
re-run, which A28 itself names as the top successor item (§6.7-1). No new claim needed from A30.

### 3.5 (e) Provenance — see F3 (§2.3)

---

## 4. The eight fixed checks — results, with the evidence

### 4.1 Check 1 (factor identification) — **FINDING, see F2**

The lift is not separately identified; the identifiable decomposition is (grouping+lift) and
(hoist). Measured shares, re-derived: hoist −4.39 % / −4.32 % / −2.95 % (n = 22, 11, 19 kept;
cheaper on 22/22, 11/11, 18/19); grouping+lift +2.88 % (`large_tokamak_nof`, n = 22) and −17.65 %
(`low_aspect_ratio_DEMO`, n = 8, inconclusive deck); grouping+hoist-only deck: `st_regression`
−6.18 %. The report's numbers are right; three sentences describing them are not (§5, C2).

### 4.2 Check 2 (envelope bias) — **PASS**: treated in the standing document, for both phases, honestly

§7.13 exists, names both one-sided biases with the concentration argument (verified from
`run_a28.py`: all four extra Phase B rungs sit at outer τ = 1e-6), computes convexity instead of
asserting it, reports the matched-count construction beside the all-settings one for **both**
phases, gives the headline to matched-count, and reports the disagreement as a bracket. My
re-derivations of every cell in its Phase A/B table match (§3.3 above; Phase B: −24.23 % under
both constructions on `large_tokamak_nof` — premium exactly 1.000, every extra rung dominated;
−21.55 % matched vs −22.50 % all-settings on `st_regression` — premium 0.988; no curve on
`low_aspect_ratio_DEMO`, every rung's residual exactly zero). The bound the queue row asked about
is real and small in Phase B (1.2 % on one deck, 0 on the other) and sign-flipping in Phase A
(+33.4 vs −4.3, +27.4 vs −4.5), exactly as published.

### 4.3 Check 3 (n+1 charged; deck fairness) — **PASS**, re-verified at the merged tip

- Lifted decks: the non-comment diff against the frozen scenarios is exactly {`neqns` n→n+1,
  `icc = 93` inserted inside the equality block, `t_plant_pulse_burn = <baseline settled value>`,
  `ixc = 178`} on both pulsed decks — 1 line removed, 4 added, nothing else.
- Pairing: on 5 sampled starts × 3 decks, every shared `ixc` takes a **bit-identical** perturbation
  factor in R, A0′ and A1′; A1′'s only extra variable is `ixc = 178` (pulsed decks), absent on
  `st_regression` (14 = 14 = 14 variables).
- Charged: gate-point `call_models` 660 vs 630 on `large_tokamak_nof` (ratio 1.048 ≈ 21/20 = 1.05);
  `st_regression` 570 = 570 = 570. The finite-difference sweeps flow through the counted path.

### 4.4 Check 4 (three decks, two treatments) — **PASS with an observation**

From the resolved records: `st_regression` A1′ has `lift_sites = []`, `hoist = feedforward`,
`nvar = 14` (= R's); the pulsed decks have `lift_sites = ['burn_time']`,
`hoist = feedforward_lifted`, `nvar = n+1`. So `st_regression`'s −6.18 % is
**grouping + hoist, k = 0**, and the pulsed decks' figures are grouping + lift + hoist. The
standing document declares this (§7.1 arm table footnote, §7.3 note 2, and the manifests refuse a
`lift` declaration on that deck) but the verdict tables in §1/§8 list the three decks under one
"the architecture" heading without restating it. Not an error — a declared-once qualifier — but F2
(§2.2) shows how the k = 0 deck's clean semantics leaked into a sentence about a k = 1 deck.

### 4.5 Check 5 (accuracy statistic) — **PASS for Phase B; Phase A inherits the p50 degeneracy, sign stable**

Phase B (re-derived, stage `ladder`): the calibration-point reads are **identical under p90, p50
and max** on both decks with a curve (−24.23 / −24.23; −21.55 / −22.50) — with 1–2 starts per rung
the three statistics coincide. Phase A (stage `phase_a`): under **p50 the read does not exist** —
the flat τ=1e-6 rung's median exit residual is exactly 0, and 15 / 13 / 9 of each deck's 17 rungs
have p50 = 0 — the same degeneracy A26's critique recorded; under **max** the signs are unchanged
(matched-count +33.4 / +29.0 / −13.5; all-settings −4.3 / −6.5 / −13.1). So the published numbers
are p90-dependent in the sense that p50 gives no number at all, and not in the sense that another
statistic flips them. §4.4.2's caveat 1 states this for the all-settings construction; it does not
state it for the matched-count one, but the numbers above show it holds there too.

### 4.6 Check 5a (robustness at matched tolerance) — **PASS: measured, one-sided, and the re-run exists**

Re-derived from the 225 raw audit records: at τ = 1e-6 the arms do **not** achieve the same
accuracy on two decks — A1′ ends tighter than A0′ on 20 of 22 (`large_tokamak_nof`) and 25 of 25
(`st_regression`) paired starts and looser on 0; identical on 22 of 22 on
`low_aspect_ratio_DEMO`. Every cell of §7.9's distribution table reproduces (including R's worst
entries 1.47e+9 and `inf`). The direction is conservative against the variant, as claimed. The
matched-accuracy robustness re-run on the one deck where it is possible and informative reproduces
exactly: 22 both / 1 only-control (`start010`) / 1 only-variant (`start009`) / 1 neither; **23 vs
23**; cost −2.27 % over n = 19 (three objf mismatches at inner 0.01: starts 005, 015, 024, vs one
at inner 1e-6). The inner tolerance stamped in the raw matched runs is 0.01, and the block arm's
ladder rung at inner 0.01 delivers 3.28e-9 = the flat arm's τ=1e-6 accuracy (bit-equal p90 on the
common start). **No re-run falls to A30.**

### 4.7 Checks 6–7 (drop census; refusal attribution) — **PASS** (modulo F1's label)

All §7.6 2×2s and §7.8 censuses re-derive exactly (§3.1 table; `large_tokamak_nof`'s three
failures are the same three starts 005/020/021 in all four arms, all raising the same
`RuntimeError: Failed to converge after 50 iterations, value is nan`). Refusal attribution from
raw tracebacks: coupling-state refusals exist only on `low_aspect_ratio_DEMO` — A0′ refuses 2
(`start004`, `start022`), A1′ refuses 3 (those plus `start010`), A1′-no-hoist the same 3, every
one naming `current_drive.eta_cd_dimensionless_hcd_primary` (residual `inf`). So of A1′'s 3
refusals, 2 are shared with the predicate-matched flat control (the predicate) and 1 is the
architecture's own — "the flat control refuses two of the three" is exact. The dropped-start
asymmetries are named: the only asymmetric crash is `start010` (A1′-family arms only); the
`st_regression` non-convergences are ifail=5/2 completions, split 2 only-control / 1 only-variant
as §7.6 says.

### 4.8 Check 8 (gate teeth cover the headline arms) — **PASS with a scope note**

`_gate_sensitivity_a28.json` exercises all four non-reference arms — **A0′ and A1′, the two the
headline is built from, included** — with 28 of 28 must-fail perturbations failing and the 4
constraint-93 teeth NOT APPLICABLE precisely on the two arms with no lift. Scope note: by
construction of `a25_gates.sensitivity`, the perturbations are applied to records of
`scenarios[0]` (`large_tokamak_nof`) only, plus one cross-deck tooth — the predicates are
deck-independent code and the c93 teeth were exercised on a pulsed deck (the only kind where they
can bite), so this is adequate, but "8 corrupted inputs per arrangement" is per-arm-on-one-deck,
not per-arm-per-deck.

### 4.9 Everything else quoted twice, checked once more

The gate-point table (§7.4, all 15 rows including the A0′-reordered **bit-identity** on 3 of 3
decks — equal counts *and* equal `norm_objf` hex), the moved-constant census (§7.11, all six
cells), the I-12 entry census (§7.12, all cells; "~28 500" ≈ 28 130–28 825 measured), the timing
repetition counts and medians (§7.10, context only — re-derived to confirm the *n*s and medians
are the raw ones, no ratio formed), the quartiles under the report's own convention
(`statistics.quantiles`: 0.881–0.948 and 0.982–0.985), and the A28-report/standing-document
cross-quotes of the headline numbers (−1.63/−6.18/−21.2, +2.13/−3.38/+3.23, hoist shares,
robustness 2×2s) are mutually consistent and match the raw artifacts. The one internal
contradiction found is F1.

---

## 5. Proposed corrections (exact text; for the orchestrator — A30 edits no merged document)

**C1a** — `arch_surgery/docs/reports/MDA_partition_exp_results.md`, §7.7 table header (line ~1822):

> old: `| test case | arrangement | starts not solved | of | refusals by the coupling-state test | quantity named |`
> new: `| test case | arrangement | starts whose run crashed | of | refusals by the coupling-state test | quantity named |`

and append to the paragraph below the table:

> add: `(The crash counts above are the refusal population. The full solved/not-solved picture, including the ifail ≠ 1 completions this table does not count — 11 per arm on low_aspect_ratio_DEMO, 1–3 on st_regression — is §7.6's.)`

**C1b** — `arch_surgery/docs/reports/deprecated/A28_phase_b_rerun.md`, §1.2 table header (line 53): the same header substitution, `| deck | arm | starts not solved | of |` → `| deck | arm | starts whose run crashed | of |`.

**C2a** — standing document §7.8 (line ~1903):

> old: `proposed architecture and never the partition's benefit**: the partition alone, on that test case,`
> `costs more.`
> new: `proposed architecture and never the partition's benefit**: the partition-plus-lift, on that test`
> `case, costs more — and no arm pair varies the lift alone, so the partition's own share is not`
> `separately identified.`

**C2b** — standing document §8 (line ~2286):

> old: `partition alone, on that test case, costs more.`
> new: `partition-plus-lift, on that test case, costs more; no arm isolates the lift, so its share is not separately identified.`

**C2c** — A28 report §1.4(2) (line 144):

> old: `` `large_tokamak_nof` the architecture *without* it costs **+2.88 %** — the partition alone costs``
> new: `` `large_tokamak_nof` the architecture *without* it costs **+2.88 %** — the partition-plus-lift costs``

**C3** — standing document, Provenance section, after "Nothing measured at any other commit is cited.":

> add: `Phase B's raw runs were produced incrementally on the A28 task branch and record four successive commits (dc18c05b, 9634bb06 — the 300-run campaign — 492c6fc8, 0fae5e1a), most with uncommitted changes present at run time. No commit after 9634bb06 touches process/ or the measurement subprocess, and six repeated configurations (both arms, three decks, the unperturbed start at τ = 1e-6) reproduce bit-identically in cost and norm_objf across three of those heads (A30). The from-scratch verification at one commit is A29's.`

**C4** — standing document §8 scope (line ~2314):

> old: `Phase B is 25 perturbed starts per arrangement.`
> new: `Phase B is 24 perturbed starts plus each deck's own unperturbed point per arrangement.`

**C5** — standing document §6.7 item 2:

> old: `2. **A matched-accuracy robustness comparison where one is possible.** Cost is compared at matched`
> `   achieved accuracy and robustness is not; §7.9 measures the direction of the resulting bias but`
> `   does not remove it.`
> new: `2. **A matched-accuracy robustness comparison on more than one start population.** §7.9.1 made the comparison on st_regression, the one deck where it is possible and informative; a second starting-point distribution would test whether its one-start-each-way result is stable.`

---

## 6. What this task did not do

- **No PROCESS solve was run**; nothing in `runs/` was written; no merged document was edited;
  `MASTER_TODO.md` untouched. No push, no merge.
- **No check required a new run.** The two standing run-shaped items — the no-exclusion-predicate
  re-run and the from-scratch provenance tie-down — are already assigned (A28 §6.7-1 and A29).
- The critique of A28's *conclusions* is deliberately narrow: with the arithmetic verified, the
  verdict table stands as published, with F2's relabelling of what "the partition alone" means.
- Timings were re-derived only to confirm counts and medians; no timing-based statement is made.

## 7. Change log (append-only)

| # | Date | Change |
|---|---|---|
| 1 | 2026-09-02 | Worktree verified; CLAUDE.md, TRAPS.md, queue row A30, A28 report and standing-document Phase B sections read. |
| 2 | 2026-09-02 | `a30_critique.py` written: 12 stages, every table re-derived from raw artifacts; teeth 10 of 10 bite. |
| 3 | 2026-09-02 | Findings F1–F5 established; loose ends (a)–(e) resolved with numbers; corrections C1–C5 drafted. |
