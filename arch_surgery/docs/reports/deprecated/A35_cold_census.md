# A35 (cold-census) — the carrier of the displacement-scaled cross-block transient is NAMED: the known-cut, fixed-point-dead edge `FirstWall (M3) → build.dr_fw_inboard / dr_fw_outboard → Build (M2)`

> **Document status** — **ARCHIVED · TASK REPORT, merged 2026-09-04 (merge `b20b6112`) and
> authoritative here** (trap T3: folder position records lifecycle, not validity). Written by
> task A35 (cold-census), 2026-09-04, on branch `A35-cold-census`, branched from
> `architecture_surgery` at `ba69c05d`, experiment base commit `c0ae5b28` (every `process/`
> file untouched by this task; the file:line citations below are at the base commit — `git log`
> shows both cited model files last changed by `c0ae5b28` itself). Orchestrator's critical
> assessment: §9 (independent recheck ALL PASS). Register entry: V15. Nothing is pushed.

| | |
|---|---|
| **Task** | Name the CARRIER of the displacement-scaled cross-block transient: the mechanism by which a one-pass feed-forward block chain's exit differs from the flat MDA's fixed point when the validated DSM says inter-block edges are forward-only (A34 pin_gate: 1.459e-2, 243/840 ≥ τ from a cold entry; V2 Phase A: one-pass audits ~0.2 at δ = 0.10 warm entries; bit-clean at the fixed point) |
| **Verdict** | **The carrier is one edge, named with coefficient-exact evidence: `fw` (FirstWall, block M3) writes `build.dr_fw_inboard` / `build.dr_fw_outboard`; `build` (block M2) reads them.** Primary label per the plan-§2b partition: **KNOWN-CUT** — the edge is present in the dependency analysis's export, is backward under the executed schedule, and is therefore an edge trust mode *deliberately* cuts; **no artifact is wrong anywhere**. Liveness annotation: **state-dependent, value-carried** — the computed value is a constant function of two pure inputs (V3), so the edge is bit-dead at every fixed point (where all prior dynamic validation ran) and transmits **exactly the entry displacement, once**, at any displaced entry. Candidates (a) missing edge, (c-order) schedule/DAG inversion and (d) non-idempotent model are each excluded by measurement below |
| **Plan** | [`arch_surgery/docs/plans/A35_INVESTIGATION_PLAN.md`](../../plans/A35_INVESTIGATION_PLAN.md), committed at `4275e450` **before execution**, with two dated user-directed amendments (`a2d1bfbb`: the (c-lag)/M119 lagged-edge sub-hypothesis, its census and the δ-scaling sub-discriminator; `dacf0e92`: the frozen-set correction, the three-orderings note, the KNOWN-CUT-first dichotomy and the five-label partition) |
| **Script** | [`arch_surgery/idf_probe/a35_cold_census.py`](../../../idf_probe/a35_cold_census.py) — stages `refs` / `gates` / `trace` / `restarts` / `flatctl` / `analyze`; committed at `fa63f57d` before any published number; extended at `a2d1bfbb` / `dacf0e92` before the numbers those extensions publish |
| **Runs** | **19 fresh-subprocess single-MDA-eval runs, 19/19 `status: ok`** (2 refs, 4 gate runs incl. the deliberately doctored snapshot, 7 traced verified chains, 6 chained trust restarts, 2 flat controls), strictly serial — at most ONE PROCESS subprocess existed at any time (the V2 campaign owns the machine's workers). No crash, no timeout, no seed fallback used; every pre-declared failure path stayed empty |
| **Environment** | `PROCESS_surgery_env`; `PYTHONPATH` pinned to this worktree per subprocess; exact tree asserted in-process (traps T6/T10); a26-generation ystate + writeset artifacts everywhere; τ = 1e-6 = inner τ; runs under `arch_surgery/idf_probe/runs/a35/` untracked |
| **Date** | 2026-09-04 |

---

## 1. The named carrier, with file:line at `c0ae5b28`

**Writer** — `FW.set_fw_geometry`, [`process/models/fw.py:347-352`](../../../../process/models/fw.py),
called from `FW.run` at `fw.py:110` (run path; the dynamic write census independently records
`fw` as the only runtime writer of both fields on both decks):

```python
self.data.build.dr_fw_inboard = (
    2 * self.data.fwbs.radius_fw_channel + 2 * self.data.fwbs.dr_fw_wall
)
self.data.build.dr_fw_outboard = self.data.build.dr_fw_inboard
```

Both inputs are pure deck inputs no model computes (V3; the per-deck export confirms their only
writer is the input loader), so the computed value is the run-constant
`0x1.26e978d4fdf3cp-6` = 1.798…e-2 m on both decks. The deck's cold initialisation of both
fields is `0x0.0p+0`.

**Readers** — `Build`, block M2, which the schedule runs **before** M3 (reads on the run path;
`calculate_vertical_build` / `calculate_radial_build` from `Build.run`):

| read | file:line | downstream mover it produces |
|---|---|---|
| `z_tf_top` carries `0.5·(dr_fw_inboard + dr_fw_outboard)` | `build.py:826-839` | `build.dz_tf_upper_lower_midplane = z_tf_top − const` (`build.py:840-842`) — the **top mover on `large_tokamak_nof`**, coefficient exactly 0.5·(Δin+Δout) |
| `rbld` | `build.py:1862-1869` | radial-build echo |
| `r_shld_inboard_inner` | `build.py:1872-1879` | mover, coefficient −Δin |
| `r_shld_outboard_outer` | `build.py:1882-1889` | feeds the ripple branch |
| `dr_shld_vv_gap_outboard` via `r_shld_outboard_outer` | `build.py:1940-1947` (ripple branch; else `:1956`) | the **top mover on `st_regression`**, coefficient exactly −Δout |

**Mechanism, exactly.** Within one outer pass the schedule runs M1 → M2 → PULSE → M3 → FF.
`build` (M2) consumes whatever `dr_fw_*` the entry state holds; `fw` (M3) then restores the
run-constant later in the same pass. So pass 1's M2 fixed point is built on the **displaced**
values, and the displacement — cold: the full 1.8e-2 m init-to-constant jump; warm: the
multiplicative δ-perturbation of the pair — lands, with the linear coefficients above, in M2's
exit state. The verified outer loop's pass 2 re-runs M2 with the corrected values and repairs it
**in one pass** (pass-3 residual 8.3e-16 / 1.6e-11 — the third pass is the receipt, not repair);
a one-pass trust chain never re-runs M2 and carries the deficit to its exit. This is a
**transport delay of depth one through one edge**, not a slow contracting mode — it sharpens
A34's "~30×/pass" reading, which averaged a one-shot repair over the pass count.

## 2. The evidence chain (every number from `a35_cold_census.py` at the commits above; artifact generation a26 throughout)

**(1) The phenomenon reproduces under a26 artifacts** (decision-tree node 1). Verified pinned
chain from the cold deck entry, `large_tokamak_nof`: **3 outer passes**; pass-2 residual max
**1.459e-2**, argmax `build.dz_tf_upper_lower_midplane`, 181/840 ≥ τ; exit vs the FLAT exit
**1.53e-8, 0 ≥ τ, categorically clean** (`0x1.075c6c890cd73p-26`). The one-pass trust exit vs
FLAT: **1.4588e-2 (`0x1.de05b6285d0b6p-7`), 243 ≥ τ** — reproducing A34's pin_gate quantities
(1.459e-2, 243/840, A18 ruler) under the a26 ruler. `st_regression`: 3 passes, pass-2 max
1.792e-2 argmax `build.dr_shld_vv_gap_outboard`; trust exit vs FLAT 1.79e-2, 124 ≥ τ —
matching A34 §5's k = 0 observation exactly. Pins bit-intact everywhere (`pin_intact_at_exit`
true; pinned at the FLAT-converged `0x1.41043caef8d92p+11`).

**(2) Candidate (d) — non-idempotent model — is EXCLUDED** (the chained-restart discriminator,
plan S3). Trust-mode chains T1→T2→T3, each a **fresh process** re-entered at the previous exit
snapshot, against the in-process verified chain's per-pass trace: every pass-2/3 mover's
before-hex equals the corresponding chain snapshot bit-for-bit and every after-hex likewise —
**181/181 and 181/181 on `large_tokamak_nof`, 82/82 and 82/82 on `st_regression`** — and the
full end-of-chain state equals the verified run's exit **bit-for-bit on 840/840 and 827/827
components**. The entire multi-pass repair is carried by the coupling state alone; no hidden
execution-history channel contributes anything expressible above the bit level.

**(3) The movement originates in M2, always.** Owner-block tally of every above-τ pass-2 mover:
`large_tokamak_nof` cold 88 M2 + 93 M3, warm 74 M2 + 83 M3; `st_regression` cold 5 M2 + 77 M3,
warm 5 M2 + 56 M3 — **zero M1- or PULSE-owned movers in any run**. M3/FF movers are downstream
recomputation from M2's corrected state; the backward channel terminates at M2.

**(4) The reader join names the pair and nothing else.** Against the frozen per-deck static
export (`st_regression`, sha `582b4a5f…` — the V14-follow-up-2 delivery, read read-only from the
main checkout): of the **210** later-block components that moved in pass 1, exactly **two** are
read by the earliest-block movers' writers (`build`, `croco_sctfcoil`):
`build.dr_fw_inboard` and `build.dr_fw_outboard`, read by `build`.

**(5) Coefficient-exact quantitative closure**, every deck × entry:

| deck / entry | Δ`dr_fw_in` (pass 1, raw) | Δ`dr_fw_out` | top pass-2 mover | measured raw Δ | predicted from source coefficient | rel. diff |
|---|---|---|---|---|---|---|
| nof / cold | 1.800000e-2 | 1.800000e-2 | `dz_tf_upper_lower_midplane` | 1.800000e-2 | 0.5·(Δin+Δout) = 1.800000e-2 | 3.8e-14 |
| nof / δ=0.10 | 5.466945e-4 | 5.317004e-4 | 〃 | 5.391974e-4 | 5.391974e-4 | 3.6e-13 |
| nof / δ=0.05 | 2.733472e-4 | 2.658502e-4 | 〃 | 2.695987e-4 | 2.695987e-4 | 3.7e-12 |
| st / cold | 1.800000e-2 | 1.800000e-2 | `dr_shld_vv_gap_outboard` | 1.800000e-2 | Δout = 1.800000e-2 | 2.4e-9 |
| st / δ=0.10 | 5.466945e-4 | 5.317004e-4 | 〃 | 5.317004e-4 | 5.317004e-4 | 7.4e-8 |
| st / δ=0.05 | 2.733472e-4 | 2.658502e-4 | 〃 | 2.658502e-4 | 2.658502e-4 | 7.4e-8 |

**(6) δ-scaling: state-carried, not seed-type** (the §2a sub-discriminator; M119's hard-coded
seed pattern would give ratio ≈ 1): per-mover pass-2 ratio between the δ = 0.10 and δ = 0.05
runs — **median 1.999 over 153 movers (q1–q3 [1.995, 2.000]) on `large_tokamak_nof`; median
2.000 over 59 (q1–q3 [2.000, 2.000]) on `st_regression`**; and identically 0 at the fixed point
(A36's warm gates, `0x0.0p+0` to `0x1.16…p-27`). Linear in the entry displacement across three
measured displacement scales plus the cited zero-point.

**(7) The KNOWN-CUT enumeration** (the §2b primary dichotomy): over the **entire** frozen
`st_regression` export crossed with the executed schedule, the backward-edge set trust mode cuts
is **exactly 2 cross-block edges — this pair — and 0 intra-non-iterated-block edges**. On
`large_tokamak_nof` the committed register's recorded cross-module cells (V2–V5, authoritative
under the V6 config match; no live sibling read, trap T9) give the cut set as the same pair plus
`pf_power.vpfskv` (Power→Pulse, the literal 20.0, dead) and the burn time (held bit-constant by
the pin in every A35 chain — it cannot carry the measured transient). **The carrier is inside
the known-cut set on both decks → primary label KNOWN-CUT: no defect in the dependency
analysis, the DSM, the node map, or the driver.** The DSM's own row order (Build row 5,
FirstWall row 41) already sequences reader before writer — a genuine back edge, recorded as
such and classified dead (V3) — so this is not (c-order) either; (a) is excluded by the edge's
presence in the export, (b)'s "structurally present, dead at fixed points, live at displaced
states" is exactly the liveness annotation the KNOWN-CUT label carries here, and the (c-lag)
reading is its timing statement: a cross-block iteration-carried dependency, refreshed once per
outer pass, never refreshed under one-pass trust.

**(8) Flat-arm symmetry** (plan S4). The same transient contracts inside the flat loop from the
same entries: overlap of the block arm's pass-2 mover set with the flat trace's sweep-≥2 mover
union — **179/181 (cold) and 157/157 (warm) on `large_tokamak_nof`; 82/82 and 61/61 on
`st_regression`** (the 2 absentees are `pf_coil.stress_mises_cs_peak` / `stress_shear_cs_peak`,
settled within flat sweep 1). Mechanistically the flat arm carries the **same lag** — its sweep
order also runs `build` before `fw` — but its predicate keeps sweeping until nothing moves, so
the lag costs at most one extra sweep and is invisible in the result; the trust chain stops
after one schedule pass and keeps it. That is the pre-declared asymmetry argument, now with the
mechanism attached.

## 3. Why every prior validation measured this edge dead — and was right, there

- **V3** (run-time census, four scenarios): "the value never changes between sweeps" — true at
  and near fixed points, and even from sweep 2 of any run, because the writer emits a
  run-constant.
- **V7 / A18**: `dr_fw_inboard/outboard` `constant` across the entire 600-point harvest — same
  reason.
- **V14 follow-up 2**: the pathway is "provably frozen" (its inputs are written only by the
  input loader) — correct, and precisely *why* the edge transmits exactly the entry
  displacement once: frozen output + displaced entry state = a one-shot correction of size
  equal to the displacement.
- **A22 / the warm gates**: at fixed-point entries the displacement of the pair is zero, so the
  transient is identically absent (measured `0x0.0p+0` on one deck).

Nothing in the register is contradicted; V3 and V14 stand. What this task adds is the missing
qualifier (trap T11): **"dead" meant value-frozen, which is not displacement-inert** — a frozen
back edge is a δ-proportional error injector for any one-pass schedule entered off the fixed
point. Per the standing rule (V14 follow-up 3) **no cross-study handoff follows**: there is no
demonstrated defect — the export contains the edge, the census found no missing or misplaced
edge, and the pipeline's orderings behaved exactly as documented.

## 4. The M119 pattern (user-directed addition), disposed

The lagged-edge (read-before-write) pattern transferred exactly: the carrier **is** a
cross-block instance of it, state-carried (§2 item 6: ratio ≈ 2, not ≈ 1), and the census that
the addition asked for (§2 item 7) returns it as the **only** member of the frozen set on
`st_regression`. The specific M119 instance (`Stellarator.st_fwbs` / `st_div`, 50 m² seed) is
**out of scope on our decks, demonstrated**: neither deck sets `istell` (unset → 0; V6 records
`istell` identical across all five decks), both runs' node censuses contain no
stellarator-family node (21 nodes each), and the block schedule refuses `istell != 0` outright
(`caller.py`, `_call_models_by_module`'s tokamak-only guard). The M119 file itself carries no
`> Document status` header (their archive convention differs from ours); it was read as
delivered, read-only.

## 5. Gates, with teeth — all PASS, all teeth tripped

| gate | result | teeth |
|---|---|---|
| **G1 trace-inertness** (verified cold chain traced vs untraced twin) | 4/4 fields identical: `node_calls_single_eval` 139, `outer_passes` 3, exit-audit hex, `objf` hex | 4/4 trip (count+1, passes+1, 1 ULP on each hex) |
| **G2 entry-restore fidelity, `large_tokamak_nof`** (the deck A36 did not smoke) | readback bit-exact 840/840, 0 skipped; 1 block sweep; audit `≤` reference's own | doctored snapshot (`superconducting_tfcoil.a_tf_plasma_case` × 1.5): audit nonzero AND 2 sweeps — trips |
| **G3 parser integrity** | chain checks §2(2); scaled-recompute 0 mismatches over every checked scalar mover | doctored trace line (1 ULP on a before-hex) **caught**; doctored Y1 snapshot **caught**; known mover `build.dz_tf_upper_lower_midplane` **present** (2/2 + presence) |
| **G4 reconciliation vs A34 pin_gate** | 3 outer passes; verified-vs-FLAT sub-τ (1.53e-8); trust-vs-FLAT 1.4588e-2 / **243 ≥ τ** — count identical to A34's 243/840, max matching to 4 digits across the a26-vs-A18 ruler change | a mismatch would have been reported, not adjusted; none occurred |

## 6. Consequences (stated, not executed)

1. **For V2 / B3's hostile-state validity bounds:** the one-pass trust deficit in y-space is,
   on these decks, **one linear image of the entry displacement of two components**, with
   measured coefficients (§2 item 5) — bounded by δ·(value/scale) of the `dr_fw` pair, not by
   any compounding process. "Verify the first call, trust thereafter" is exactly one refresh of
   the cold init-to-constant jump.
2. **The Phase A one-pass accuracy story decomposes.** The verified chains' pass-2 movement at
   δ = 0.10 warm entries is ~5e-4 scaled (max) — the genuine cross-block deficit. The campaign's
   ~0.24 one-pass audit medians are three orders larger; the plausible dominant term is the
   **post-solve-excluded nodes'** perturbed-but-never-recomputed components (A1 suppresses
   `pulse`/`vacuum`/`water_use`/`costs` from the measured call, and the audit then sees their
   δ-sized entry perturbations), which is an accounting artifact of the suppression, not
   cross-block physics. **Flagged as a reconciliation hypothesis for the V2 tally to check**
   (its audit mover census can split the post-solve-owned share), not asserted.
3. **A surgical fix exists but is a D11 decision, not this task's:** the lag dissolves if the
   `dr_fw_*` geometry write executes before `Build` (it depends only on pure inputs), e.g. by
   seeding the fields at initialisation or reassigning the write's schedule position. Any such
   change under `process/models/` requires the user's approval before merging; nothing was
   changed.
4. **For the register:** a V-entry is proposed recording the annotation of §3 (V3/V14 stand;
   "value-frozen ≠ displacement-inert"), owner the orchestrator. No sibling handoff (no defect).

## 7. Scope honesty

Two decks (the third, `low_aspect_ratio_DEMO`, not run — its artifacts and pin plumbing exist;
the campaign owns the machine), one cold entry and one seed at two δ values per deck, pin held
bit-constant throughout (the burn-time cut's own displaced-state behaviour is Phase A's
pin-scan question, untouched here). Sub-τ carriers are invisible to the trace by construction;
hidden state that never expresses above τ in y is unmeasurable by this design and is excluded
only as *the carrier of this transient* (restart identity, §2 item 2), not as existing. The
carrier claim is deck-conditional the way every liveness claim here is (V6): on a deck whose
switches route `Build` differently, the coefficient table would need remeasuring — the census
machinery is committed and reruns per deck.

## 8. Provenance and reproduction

Every run: fresh subprocess, own working directory, `PYTHONPATH` pinned to this worktree, exact
tree asserted in-process; strictly serial (concurrency cap honoured throughout). Every published
quantity is a count, a name, or a bit-exact hex float; wall clock appears nowhere as evidence.
Reads outside this worktree: the frozen `st_regression` export (main checkout, read-only, sha
recorded in `analysis/summary.json`) and the sibling's M119 report (read-only). The main
checkout's running campaign was not touched.

```
cd arch_surgery/idf_probe
python a35_cold_census.py refs       # 2 runs   (FLAT cold, traced; references + pin source)
python a35_cold_census.py gates      # 4 runs   (G1 PASS 4/4+4/4, G2 PASS + tooth)
python a35_cold_census.py trace      # 7 runs   (verified chains: cold, delta=0.10, delta=0.05)
python a35_cold_census.py restarts   # 6 runs   (trust chains T1..T3 per deck)
python a35_cold_census.py flatctl    # 2 runs   (flat controls from the displaced entries)
python a35_cold_census.py analyze    # 0 runs   (classification, censuses, teeth, summary)
```

Which stage produced which figure: §2(1),(5),(6) and §5 G4 — `runs/a35/trace/*` +
`runs/a35/analysis/summary.json`; §2(2) — `runs/a35/restarts/*` + `summary.json`
(`identity`, `full_state_Yk_vs_verified_exit`); §2(3),(4),(7) — `summary.json`
(`attribution`, `known_cut_census`, `carrier_closure`, `carrier_primary_label`); §2(8) —
`runs/a35/refs/*`, `runs/a35/flatctl/*` (`flat_symmetry_*`); §5 — `runs/a35/gates/gates.json`
and `summary.json` (`g3_teeth`, `g3_known_mover_present`, `scaled_recompute`). Commits: plan
`4275e450`; entry point `fa63f57d`; amendments `a2d1bfbb`, `dacf0e92` — each committed before
the numbers it publishes.

## 9. Change log

- 2026-09-04 — task opened; mandatory reads; plan written and committed (`4275e450`); entry
  point committed (`fa63f57d`); refs + gates executed (all PASS).
- 2026-09-04 — user-directed addition relayed mid-task (M119 lagged-edge pattern): plan amended
  (`a2d1bfbb`), δ = 0.05 runs and the δ-scaling sub-discriminator added; M119 instance scoped
  out on our decks with evidence.
- 2026-09-04 — second relay (frozen-set correction, three orderings, KNOWN-CUT dichotomy): plan
  amended and analyzer extended (`dacf0e92`); known-cut enumeration and carrier closure run.
- 2026-09-04 — all 19 runs complete (19/19 ok, no failure path taken); carrier named
  KNOWN-CUT with coefficient-exact closure; report written.

---

## 9. Orchestrator's critical assessment (2026-09-04, pre-merge)

Independent recomputation of the report's headline numbers from A35's **raw** artifacts —
per-pass traces, exact-hex snapshots, in-run metrics — deliberately not through
`a35_cold_census.py`'s analyzer (`summary.json` is consulted only for the owner-block tally,
whose inputs the raw traces corroborate by name). Script:
[`arch_surgery/idf_probe/a35_recheck.py`](../../../idf_probe/a35_recheck.py), committed with this
section; result **ALL CHECKS PASS**. Assessed by the orchestrating session; user-directed
("Critically assess A35's result thoroughly. Recheck numbers if necessary").

**Confirmed at the bit level (recomputed, not re-read):**

1. Frozen st export sha `582b4a5f…` — exact match.
2. Verified-chain pass structure, both decks: nof 659 / **181, `0x1.de05b6285d0b6p-7`, argmax
   `build.dz_tf_upper_lower_midplane`** / 0 at `8.3e-16`; st pass-2 82 movers, argmax
   `build.dr_shld_vv_gap_outboard`.
3. **Coefficient closure, all six deck×entry rows**, predictions re-derived from the source
   (the 0.5·(Δin+Δout) and −Δout coefficients read directly off `build.py:826-842` /
   `build.py:1940-1947`, writer form off `fw.py:347-352` — independently read before this
   assessment): measured = predicted at rel. diffs 3.8e-14 … 7.4e-8, identical to §2 item 5's
   table to the printed digit.
4. δ-scaling ratios recomputed from raw before/after hexes: nof median 1.9987 (n = 153,
   q1–q3 [1.9952, 2.0003]); st median 2.0000 (n = 59). State-carried, confirmed.
5. Restart end-of-chain vs verified exit: **755/755 (nof) and 746/746 (st) scalar-float
   components bit-identical** (the report's 840/827 counts are the full component sets
   including non-float kinds; every float agrees, none differs).
6. Owner-block tallies: nof cold 88 M2 + 93 M3, st cold 5 M2 + 77 M3, **zero M1/PULSE movers**.
7. Trust-vs-FLAT, nof: the analyzer's snapshot-pair max reproduces **exactly**
   (`0x1.de05b6285d0b6p-7`, argmax `dz_tf_upper_lower_midplane`).

**One precision finding (does not touch the verdict).** "Trust one-pass exit vs FLAT" has two
full-set operationalizations in the artifacts: the analyzer's snapshot pair (T1 exit vs this
task's flat-reference exit: max `0x1.de05b6285d0b6p-7`, **243** ≥ τ — the numbers §2 item 1 and
G4 quote) and the in-run `exit_audit` against the a26 ystate spec's recorded values (max
`0x1.de05b6285d3f4p-7`, **244** ≥ τ). The two agree to 11 significant digits on the max and
differ by one near-τ component; st likewise (`…effb134b` vs `…f0afff76`, 124 both ways). The
report cites the snapshot-pair consistently; the ±1 is reference-lineage noise at the τ
boundary and no conclusion is sensitive to it. (A scalar-float-only recomputation with the
spec ruler gives 207/120 — an expected undercount of the same comparison, documented in the
recheck script so nobody mistakes the subset for a discrepancy.)

**Independent corroborations beyond A35's own evidence chain:**

- **The register pre-recorded the edge.** `DSM_VALIDATION.md` **V3** is exactly this pair —
  "FirstWall (M3, row 41) → Build (M2, row 5) — structurally present … value never changes
  between sweeps … DSM correct, but the edge is dead in this deck. If a future model computes
  `radius_fw_channel` or `dr_fw_wall`, this edge goes live" — and **V4** is `pf_power.vpfskv`.
  The KNOWN-CUT label is therefore grounded twice over: the edge is in the sibling's export
  AND in this project's own committed validation register, with the go-live caveat already
  written. A35's contribution is the missing qualifier ("dead" = value-frozen ≠
  displacement-inert) and the coefficient-exact demonstration that this edge carries the
  displaced-entry transient.
- **The grounding figure shows the edge.** The native-ordered collapsed tokamak DSM the
  intervention was grounded in (`xDSM_paper/figures/paper_collapsed_tokamak.html`; V3's row
  numbers) draws FirstWall → Build below the diagonal, alongside `CICCSuperconductingTFCoil →
  Build` (intra-M2 under the executed partition, healed by M2's own iteration) and the
  Pulse-family marks. Nothing was invisible; the mark was classified dead-by-value, correctly
  for the property then checked.
- **V14 lineage kept distinct.** A31 dissolved V14's *recurring* tail as the `srcktpm` scoring
  artifact, and the register's earlier refutation of FirstWall→Build as *that* phenomenon's
  carrier stands. A35's phenomenon — the one-shot displaced-entry transient — is a different
  object, and V3's edge is its demonstrated carrier. Both register conclusions survive; the
  two phenomena must not be conflated when citing this report.

**Scope limits endorsed** (§7 declares them; restated as the merge's caveats): third deck
`low_aspect_ratio_DEMO` not run; one seed per δ per deck; the tokamak-side known-cut set rests
on register entries V2–V5 plus the dynamic zero-M1/PULSE-mover evidence rather than a tokamak
static-export enumeration (the st export enumeration is complete); the ~0.24 Phase A audit
reconciliation (§6 item 2) is a hypothesis for the V2 tally, not a result of this task.

**Assessment verdict: the named carrier, its KNOWN-CUT label, and every number checked stand.
Approved for merge.**
