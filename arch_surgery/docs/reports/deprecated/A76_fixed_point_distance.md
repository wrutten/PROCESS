# A76 (fixed-point-distance) — do the arms reach the *same* fixed point, not merely an equally converged one

> **Document status** — **MERGED 2026-09-15** at `8422dc38` (`--no-ff`); archived here at merge — folder position records lifecycle, not validity (trap T3). Records: `arch_surgery/idf_probe/runs/A76_runs/` (gates, stamp surveys, and a copy of the campaign tree seeded from A75). Orchestrator's assessment §11. Task **A76 (fixed-point-distance)**, branch `A76-fixed-point-distance`,
> base `14342a72` (the `architecture_surgery` tip at dispatch, 2026-09-15). Minted by the orchestrator
> at the user's instruction in this session (*"Register a second task to add the between-arm distance
> of phase A as an additional analysis to the analysis scripts, and add the results to the report.
> Inject this in the appropriate place, do not append. This is additional analysis on the v4 data,
> not a v5 item"*) and confirmed by the user in the orchestrating session. **Zero PROCESS runs.**
> Folder position records lifecycle, not validity (trap T3).

*Vocabulary as in the harness README: "exit state" (the coupling state a run writes to `y_exit.json`
before the exit audit's sweep), "restricted" (over the components the configuration's once-per-run
deferred nodes do not write), "frozen ruler" (`max|Δy_i| / s_i` with `s_i` the committed scale),
"ladder" (the evaluation phase's arms in rung order, `AR → A0 → A0p → A1`), "tally" and "analysis"
(the two implementations of every published cell), "tooth", `--resume`. Arms keep their **current**
names here (`A0p`, `A1`, `B3`): A78 (arm-renames) follows and renames what this task adds.*

## 1. Verdict in one page

- **The question.** V4's matched-accuracy table (§4.2) measures how far each arm's exit state is from
  *a* fixed point — one further sweep, per run. It does not say whether two arms reached the *same*
  point, and the per-call cost ratio assumes they do. The user asked (2026-09-15) whether that
  distance was measured at all; it was not — no table or gate compared `A0`'s exit state with `A1`'s
  at the same entry, though every Phase A run had written it.
- **The answer, from the campaign's records and no model run.** On the headline pair the restricted
  scaled distance between the two arms' exit states is **5.1e-12 / 0 / 1.2e-11** median (p90
  1.8e-10 / 0 / 4.6e-11; worst seed 2.7e-10 / 0 / 6.6e-11) for `A1/A0p` on `large_tokamak_nof` and
  `low_aspect_ratio_DEMO` and `A1/A0` on `st_regression`, displaced regime, **0 of 25** pairs with
  any restricted component at or above τ = 1e-6 on every configuration, 0 pairs with a discrete
  component or a constant differing. On `low_aspect_ratio_DEMO` the two exit states are
  **bit-identical** over every restricted component on all 25 seeds. The stencil regime reads the
  same (`A1/A0p` 2.6e-12 / 0 forward, 0 / 0 backward; `A1/A0` 1.1e-10 / 5.3e-11 on st; 0 pairs
  above τ). **The partition reaches the flat arrangement's fixed point, not a neighbouring one, on
  every entry of every configuration** — for the first time a measured cell rather than an
  assumption.
- **Two other rungs are on the page.** `A0/AR` reads 2.6e-8 / 0 / 1.5e-7 median — the distance
  upstream's stopping rule leaves, the same numbers as `AR`'s own audit residual (§5.1 already said
  `AR` stops 30–50× further out; this is the same fact seen between arms). `A0p/A0` reads
  **9.7e-2 / 7.0e-2** median on the pulsed configurations, **25 of 25** pairs above τ, argmax
  `power.qac` / `power.e_plant_net_electric_pulse_*`: pinning the burn time moves the plant block's
  fixed point by a tenth of its scale. That is the ownership rung's declared inconsistency (a
  burn-time residual of 6.3 % / 5.3 %) seen on the coupling state rather than on the burn time
  alone — and it is why the previous revision's pair `A1/A0`, published beside, reads the same
  9.7e-2 / 7.0e-2: V3's Phase A compared two different fixed points. The headline pair `A1/A0p` is
  the right one, as the plan declared.
- **Reported, not accepted on.** No acceptance rule was pre-declared for this quantity; it was
  added after the campaign. Every caption and the §5.1 paragraph say so. The acceptance verdicts
  stay with the checks that declared one.
- **Implemented the V4 way for a new cell**: one declaration (`stats.fixed_point_distance`, its
  docstring), one computation (`tally_evaluation.fixed_point_distance`, evaluating the predicate's
  own residual — `harness/child/ystate.py`, decision D14(c) — between two exit states), one
  independent re-derivation (`analysis._fixed_point_distance`, from the coupling-state artifact and
  the hex literals in `y_exit.json`, importing no line of the predicate), and the gates over both.
  `tally_contracts` gains an **eleventh tooth** that doctors an exit state in a scratch copy.
- **Gates at `d9e7c2a5` over the 949 campaign records at `57dc0c14`, all `--resume`:**
  `recomputation` PASS **13 174 compared / 0 mismatched** over 93 tables (from 12 715 / 84 — the
  459 new cells are the nine distance tables: 30 rows × 15 columns + 9 denominators);
  `tally_contracts` PASS 279 / 0 (+256 / 0 reference cells), 11/11 teeth; `run_kind_separation`
  PASS 2 994 / 0; `self_containment` PASS 52 / 0; self-check PASS; gate table **30 PASS, 156 of 156
  teeth**; `--plan-tables check` IDENTICAL (4 965 lines). Stamp survey before and after: **0 of
  1 096 run records re-made**, 0 new, 0 gone.
- **Where it landed in the report.** §4.2 gains a *fixed-point distance* table **beside each
  matched-accuracy table** (nine: three configurations × displaced, stencil forward, stencil
  backward), rendered by the button, not by hand; §4.4 the same nine recomputed; §5.1 gains one
  hand-written paragraph under the `A0p → A1` rung, from §4 cells only, each naming its table;
  Appendix C an entry. Nothing appended at the end of a section.

## 2. What was measured, and how

### 2.1 The statistic (the declaration is `stats.fixed_point_distance`'s docstring)

Per pair (one entry, two arms): the predicate's scaled residual evaluated between the two exit
states instead of between two successive sweeps — `max_i |y_arm,i − y_base,i| / s_i` over the
continuous components, `s_i` the committed scale (the frozen ruler, the one τ is stated on) —
**restricted** to the components not written by the configuration's once-per-run deferred nodes,
exactly the restriction the matched-accuracy table applies and for the same reason (those
components are stale at the partitioned arm's exit by design). With it: the argmax component, the
count of restricted components at or above τ, the whole-state maximum beside, and whether the pair
is *categorically clean* (no discrete component differs, no constant moved, no NaN on one side only).

Over the pairs of one row: `n` the pairs the two arms share at the pairing key (seed, or stencil
column), `n_compared` the pairs on which both exit states exist and both audits carry the
restriction, the shortfall named by reason (never dropped — trap T11), median (nearest-rank
upper-middle) and p90 (nearest-rank `ceil(0.9 n)`) of the restricted maximum, the worst pair and
its key (none when every pair reads exactly 0), the pairs with any component at or above τ, the
unclean pairs, the whole-state median and p90, and the exclusion count.

The mixed ruler is not offered: its denominator reads a *current* value, and a distance between two
states has no current side. The caption says so.

### 2.2 The rows: the ladder's rungs

One row per rung of the evaluation phase's ladder among the arms present — `A0/AR` (the stopping
rule), `A0p/A0` (ownership), `A1/A0p` (the partition; marked **headline** on the pulsed
configurations) — and on a pulsed configuration `A1/A0` **beside**, the previous revision's pair
and the steady-state configuration's headline, so the three configurations share a readable row.
On `st_regression` (`A0p` skipped) the rows are `A0/AR` and `A1/A0` (headline).

*Why rungs and not "every arm against the reference".* The first draft reported every arm against
`A0p` (the matched-accuracy verdicts' pairing). Its `AR/A0p` and `A0/A0p` rows were identical to
every digit — both dominated by the pin's displacement of `power.qac` — and said nothing about the
stopping rule. The ladder isolates one change per row, which is what the plan's §3.2 designed the
arms for (§7, decision (a)).

### 2.3 The exclusion, re-derived and checked against the record

The set of excluded components is **derived, never listed**: the per-run artifact's node list →
the committed write census → the spec's keys, the exit audit's own rule (`child.restricted_audit`).
The tally re-derives it from the artifacts in this tree's `harness/data/` and **checks the digest
against the one the audit stamped** in the record (`exit_audit.frozen.restricted.excluded_sha256`);
a derivation that lands elsewhere is a refusal, not a smaller table. That refusal fired once during
the build: the first derivation intersected the written set with *every* spec key and hashed to
`defab3ec…` against the record's `1ec977f7…`; the audit's digest is over the **tested** (continuous
and non-finite) components only — 122 / 123 / 123 per configuration. The restricted residual leaves
out every component the per-run nodes write, of any category (`written`), while the count published
and the digest checked are over the tested ones (`excluded`), so the column reads the same 122 / 123
/ 123 the matched-accuracy table reads.

### 2.4 Where the exit states come from

A record's own `outdir` names the tree the campaign ran in
(`…/PROCESS_surgery_worktrees/campaign-57dc0c14/…`), not the tree the records were seeded into. The
tally therefore maps each record's `job_digest` to the directory the pool resolved it from
(`RunRow.path`), and the analysis builds the same map independently from `source_directories`. A
record whose directory is unknown, whose `exit_state_written_to` is empty or whose file is missing is
a named shortfall in the `not compared` column. Over the campaign every one of the 674 Phase A
records carries its `y_exit.json` (921 files = 674 Phase A + 247 ok optimisations; the 28 crashed
optimisations have none and are Phase B, outside this table). `restore_snapshot` refuses a state
written against another component spec; the tally turns that into a `TallyError`.

### 2.5 The independent re-derivation

`analysis._fixed_point_distance` reads the coupling-state artifact (keys, categories, scales), decodes
`y_exit.json` from its hex literals with its own decoder, re-derives the exclusion with its own
crawl and its own digest check, and computes the scaled gap per component with its own rules (a
bool is not a float, an int is not a float, a list is float-valued only when every element is; a
changed NaN pattern or a NaN on the arm side is infinite; discrete and constant components are
tested for exact equality). Its median and p90 are the module's own `middle` and `ninetieth`. The
comparison is exact (`_same`, no tolerance), and it agrees on all 459 cells.

## 3. The numbers (all from §4.2 / §4.4 of the report at `d9e7c2a5`; displaced regime unless said)

*Caption: restricted scaled distance between the two arms' exit states, frozen ruler, over the
compared pairs; "above τ" counts pairs with any restricted component ≥ 1e-6. `n` = 25 seeds per row
in the displaced regime; the stencil rows are over 20 / 19 / 14 design-vector columns.*

| configuration | pair | role | median | p90 | worst | above τ | unclean | whole-state median |
|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | A0/AR | rung | 2.624e-08 | 1.542e-07 | 2.265e-07 | 0/25 | 0 | 3.255e-08 |
| large_tokamak_nof | A0p/A0 | rung | 9.665e-02 | 1.985e-01 | 2.563e-01 | 25/25 | 0 | 2.919e-01 |
| large_tokamak_nof | **A1/A0p** | **headline** | **5.094e-12** | **1.838e-10** | **2.709e-10** | **0/25** | 0 | 2.435e+00 |
| large_tokamak_nof | A1/A0 | beside | 9.665e-02 | 1.985e-01 | 2.563e-01 | 25/25 | 0 | 2.818e+00 |
| low_aspect_ratio_DEMO | A0/AR | rung | 0 | 0 | 0 | 0/25 | 0 | 0 |
| low_aspect_ratio_DEMO | A0p/A0 | rung | 7.026e-02 | 1.585e-01 | 2.047e-01 | 25/25 | 0 | 7.026e-02 |
| low_aspect_ratio_DEMO | **A1/A0p** | **headline** | **0** | **0** | **0** | **0/25** | 0 | 1.816e-01 |
| low_aspect_ratio_DEMO | A1/A0 | beside | 7.026e-02 | 1.585e-01 | 2.047e-01 | 25/25 | 0 | 1.839e-01 |
| st_regression | A0/AR | rung | 1.539e-07 | 2.793e-07 | 5.938e-07 | 0/25 | 0 | 1.539e-07 |
| st_regression | **A1/A0** | **headline** | **1.227e-11** | **4.620e-11** | **6.565e-11** | **0/25** | 0 | 2.575e-01 |

Stencil regime, headline pairs: nof `A1/A0p` 2.579e-12 (forward, n = 20) / 0 (backward; worst
4.6e-13); lad `A1/A0p` 0 / 0 (n = 19; backward worst 6.9e-19); st `A1/A0` 1.116e-10 / 5.339e-11
(n = 14). 0 pairs above τ in every stencil row of every headline pair.

Three readings, stated with their evidence:

1. **Same fixed point.** Headline distances sit four to six orders of magnitude under τ and two to
   three orders under the arms' own audit residuals (`A0p` and `A1` read 3.8e-10 median on nof):
   the two arms are closer to each other than either is to a converged point in the audit's sense.
   On lad, exactly 0 — the partitioned arrangement's sweeps and the flat arrangement's sweeps end on
   bit-identical values over 701 tested restricted components on 25 of 25 seeds. (A43
   (st-trust-gap) had found this bit-for-bit agreement on st on V3's records at block τ = 1e-14; here
   it is at the campaign's τ = 1e-6, on the pulsed configurations, and without the trust step.)
2. **The stopping rule's distance is the reference arm's residual.** `A0/AR` = 2.624e-08 median on
   nof, which is `AR`'s restricted audit median in the matched-accuracy table to every digit; 0 on
   lad, where both stop after exactly five sweeps on every seed (§5.1); 1.5e-7 on st. Upstream's
   test does not move the coupling state to a different point, it stops short of the same one.
3. **The pin moves the fixed point.** `A0p/A0` = 0.097 / 0.070 median, every seed above τ, on
   `power.qac` (nof) and `power.e_plant_net_electric_pulse_kwh/_mj` and `times.t_burn_0` (lad).
   The ownership rung's inconsistency is not confined to the burn time: the plant block's fixed
   point moves by a tenth of the component's scale. This is exactly why the plan made `A1/A0p` the
   headline pair (both on the same reduced map) and published `A1/A0` beside — the "beside" row
   reads 0.097 / 0.070 because it compares two different fixed points, and V3's Phase A pair was
   that one.

## 4. The tooth (protocol §12)

`tally_contracts` gains *the fixed-point distance's restriction*: on one real pair of the published
population (`large_tokamak_nof` `A1/A0p` at seed 1) the arm's `y_exit.json` is copied to a scratch
directory and doctored twice. A **kept** scalar continuous component
(`blanket.deg_blkt_inboard_poloidal_plasma`) moved by 1e-3 of its scale must raise the restricted
worst from 1.523e-10 to 1.000e-03, name itself as argmax and count the pair above τ — it does. An
**excluded** component (`costs.blkcst`) moved past the whole-state maximum (by 3.96 of its scale)
must leave the restricted worst at 1.523e-10 and carry the whole-state median from 0.980 to 3.960 —
it does. Both halves or the tooth is not tripped; the first attempt, which moved the excluded
component by only 1e-3 and expected the whole-state *median* to change, did not trip (the
whole-state maximum sat on another component) and was rewritten to move it past the maximum. The
gate reads 11/11 teeth. The digest refusal of §2.3 was exercised once during the build and is the
other demonstrated failure path.

## 5. Where it is injected

- **§4.2** — `fixed-point distance — <configuration> — <source>` immediately after
  `matched accuracy — …` and before `ownership rung …`, for each of the three configurations in
  each of the three evaluation sources that carry a pair (the entry-references source has one arm
  and emits none — the function returns `None` and the table is simply absent, not empty). Rendered
  by `--plan-tables write`; `--plan-tables check` IDENTICAL. The subsection's *Emitted by* line and
  the stage's registry description name the table.
- **§4.4** — the same nine, recomputed.
- **§5.1** — one paragraph, *The same fixed point, not merely an equally converged one*, between the
  `A0p → A1` and `A0 → A0p` rungs, from §4 cells only, each naming its table.
- **Appendix C** — one dated entry, appended (the change log is append-only by rule).
- **`harness/README.md`** — the tally paragraph (six tables) and the package-layout row for
  `child/` (the evaluation tally imports `predicate`).

## 6. Files, commits, presses

| file | change |
|---|---|
| `harness/measurement/stats.py` | `fixed_point_distance` — the declaration and the aggregation over pairs; exported |
| `harness/measurement/tally_evaluation.py` | `LADDER`, `ladder_pairs`, `_excluded_by_the_per_run_nodes`, `_exit_state`, `fixed_point_distance`; `tally()` builds the digest → directory map and emits the table after `matched_accuracy` |
| `harness/measurement/analysis.py` | `_decode_state_value`, `_as_floats`, `_values_equal`, `_scaled_gap`, `_state_distance`, `_written_by_the_per_run_nodes`, `_directories_by_digest`, `_fixed_point_distance`; wired into `recompute()` after `_matched_accuracy` |
| `harness/gates/gate_tally.py` | the eleventh tooth |
| `harness/gates/registry.py`, `harness/measurement/plan_tables.py` | the stage descriptions name the table |
| `harness/README.md` | as above |
| `EXPERIMENT_REPORT.md` | §4 re-rendered; §5.1 paragraph; Appendix C entry |

Commits on `A76-fixed-point-distance` (base `14342a72`): `d9e7c2a5` (the scripts and the report,
one commit — the report's §4 is the scripts' output and §5.1 cites it); the task report follows.
Presses at `d9e7c2a5`, tree clean, every verdict record stamped `d9e7c2a5`: `--gate
tally_contracts --resume`, `--gate recomputation --resume`, `--gate run_kind_separation --resume`,
`--gate self_containment --resume`, `--measure tally_evaluation|tally_optimisation|recomputed_tables|gate_table
--resume`, `--plan-tables write`, `--plan-tables check`; `--selfcheck` PASS. Stamp surveys:
`runs/stamp_surveys/before_A76.json` (1 096 records: 949 at `57dc0c14`, 96 at `0677a9b3`, 39 at
`4ca8cff5`, 6 at `fd480aff`, 3 at `61473c1d`, 3 at `47be2b0d`) against `after_A76_commit.json`:
0 changed, 0 gone, 0 new. No `--gate all`, no smoke, no campaign record, no edit under
`harness/child/` or `PROCESS/`, `EXECUTION_APPROVED` untouched.

## 7. Autonomous decisions, each with its reversal

| # | decision | why | reversal |
|---|---|---|---|
| (a) | Rows are the **ladder's rungs** plus the headline and (pulsed) `A1/A0` beside — not every arm against the reference | the first draft's `AR/A0p` and `A0/A0p` rows were identical to every digit, both dominated by the pin, and said nothing about the stopping rule; one change per row is what the ladder is for | `ladder_pairs` is one function in each implementation; replace its body with "every arm against `headline_base`" and both tables change together |
| (b) | **Frozen ruler only**; the mixed ruler is not offered | the mixed denominator reads a current value and a distance between two states has no current side; the caption says so | add a `ruler` loop in both implementations and a `ruler` key column; the sibling table's "both rulers or neither" clause would then apply |
| (c) | The restricted residual leaves out **every** component the per-run nodes write, of any category; the published count and the digest are over the **tested** ones | that is the audit's own construction (`restricted_audit` intersects with the scaled vector's keys), and matching its digest is the check that the artifacts on disk are the run's | intersect `written` with the tested keys too; the unclean count would then see per-run-written discrete components differ by design |
| (d) | **Reported, not accepted on** — no verdict column, `acceptance=False` | no acceptance rule was pre-declared; a rule written after the numbers is not a check | a V5 plan may declare one (a natural form: headline median and p90 below τ, 0 pairs above τ); then `acceptance=True` and a verdict column |
| (e) | The tooth lives in `tally_contracts`, not in a new gate | the table is a tally table and the gate over tally tables is that one; a gate whose code changed is pressed once (rule xiii) | move `_tooth_fixed_point_distance_restriction` to a gate of its own with `reads_from=("tally_evaluation",)` |
| (f) | The tally imports `harness.child.predicate` | D14(c): one implementation of the coupling-state test; the analysis is the independent one | re-implement the residual in the tally as well — which would be a third implementation of the predicate, the thing D14(c) forbids |
| (g) | The worst-pair key is `None` when every compared pair reads exactly 0 | "worst seed 1" over an all-zero row misleads | drop the condition in `stats.fixed_point_distance` and in the analysis's `worst_key` |
| (h) | §4's re-render at `d9e7c2a5` differs from `14342a72`'s only by the new tables and two gate-table rows (`tally_contracts`, `recomputation` populations/denominators); nothing else moved | verified by `git diff` on the report: 2 lines removed, both gate-table rows | — |

## 8. Limits

- **Post hoc.** The statistic was declared after the campaign, from the user's question. Its
  construction copies the matched-accuracy table's (same restriction, same ruler, same medians), and
  every caption says it is reported and not accepted on; but a reader should know the rows were
  chosen (§7 (a)) after a first draft had been seen.
- **It compares exit states, not fixed points.** A distance of 5e-12 between two states each
  within 4e-10 of *a* fixed point bounds the distance between the fixed points they are near, but
  is not the same as running both to machine precision. A43 (st-trust-gap) did that on st at block
  τ = 1e-14 on V3's records; nothing here tightens τ.
- **Phase A only.** The optimisation phase's accepted optima are compared on `norm_objf` (check 1)
  and audited per arm (achieved accuracy); no between-arm distance of the accepted coupling states
  is computed. The records carry `y_exit.json` for the 247 ok optimisations too, and the same
  functions would apply with `pairing_key` = seed, but the accepted `x` differs by arm and the
  statement would need a different declaration (a distance at different design vectors is not the
  same quantity). Not done; not in the brief.
- **The whole-state column is large for the partitioned arm by design** (2.4 / 0.18 / 0.26 median
  on the headline pair) and is published to show the exclusion's size; it is not a finding.
- **The tooth doctors one pair of one configuration** (`large_tokamak_nof` `A1/A0p` at seed 1, the
  first with both exit states). It proves the restriction's two directions on that pair; it does
  not sweep configurations.
- **Timing**: none reported; the tally stage takes ~4 s and the recomputation gate ~22 s on this
  machine, context only.

## 9. What should change elsewhere (proposed; not edited here)

- **Queue v2 (`MASTER_TODO_v2.md`)**: A76's row → merged, with the record path the retire script
  prints; the "no task open" state line. The V5 improvement list (A77) may cite this report for a
  pre-declared acceptance rule on the fixed-point distance (§7 (d)).
- **A78 (arm-renames)**: the new code names `A0p`, `A1` in `LADDER` / `FIXED_POINT_LADDER`,
  `ladder_pairs`, the captions, the tooth and the §5.1 paragraph — all to be renamed with the rest.
- **TRAPS.md**: nothing new. The digest mismatch of §2.3 is the shape of T11's "a count over a set
  nobody chose", already recorded, and the tooth's first attempt (a doctored component that did not
  move the maximum it was expected to move) is protocol §12 working as written.
- **Harness README §14 (the analysis)**: could name the fixed-point distance among the constructions
  re-derived; the §13 paragraph and the layout row are updated here.

## 10. Change log

| date | entry |
|---|---|
| 2026-09-15 | Report written at `d9e7c2a5`; task open, awaiting the orchestrator's assessment. |

## 11. Orchestrator's critical assessment (protocol §5)

*Written 2026-09-15 at `abff00a2` by the orchestrating session, by checks that differ from the agent's; gates the merge.*

**Checks made, none a repeat of the agent's press.**

1. **The headline row recomputed from the raw files with none of the branch's code.** A twenty-line script in the assessment session read the 25 `y_exit.json` pairs of `large_tokamak_nof` `A1`/`A0p` (displaced regime) as hex literals, took the scales from `harness/data/coupling_state_large_tokamak_nof.json`, derived the exclusion from the record's `per_run_nodes` (`vacuum`, `water_use`, `costs`) and `node_writesets.json`, and computed `max_i |Δy_i| / s_i` over the kept tested components. Result: median **5.093949426530372e-12**, p90 **1.8380370166410915e-10**, worst **2.709328238976662e-10**, 0 of 25 at or above τ, seed 1 **1.523322553612911e-10** on `heat_transport.tlvpmw`, whole-state median 2.435 on `costs.coecap` — every published digit of the row and of the tooth's baseline. The exclusion's digest was reproduced too: `sha256("\n".join(sorted excluded tested keys))` = `1ec977f7…`, the record's, and the "every spec key" variant the agent's first derivation made = `defab3ec…`, the refusal it described in §2.3. Both refusal and digest are as stated.
2. **The lad bit-identity claim checked on hex strings, not floats.** Over the 25 `low_aspect_ratio_DEMO` pairs `A1`/`A0p`, 0 pairs have any kept component whose hex literal differs — "bit-identical over every restricted component" is literally true.
3. **Gate records.** `runs/gates/{tally_contracts,recomputation,run_kind_separation,self_containment}/gate.json` in the worktree all read PASS, `tree_git_head` `d9e7c2a5`, 279/0, 13 174/0, 2 994/0, 52/0. The three stamp-survey files exist (`before_A76`, `after_A76`, `after_A76_commit`).
4. **What moved in the report.** `git diff 14342a72 d9e7c2a5` on `EXPERIMENT_REPORT.md`: 276 insertions, 4 deletions; the four removed lines are the two gate-table rows whose populations grew, the teeth total (155 → 156) and the §4.2 *Emitted by* line — decision (h) holds. The added prose is the eighteen table headers, their captions and one §5.1 paragraph; every number in that paragraph is in the table beside it.
5. **Scope.** No file under `harness/child/` or `PROCESS/` changed; `EXECUTION_APPROVED` untouched; no run-kind other than the existing records; the tally imports `harness.child.predicate` (decision (f)) — an import, not an edit, and D14(c)'s one implementation is the right call.

**Findings for the record, none blocking.**

- **The denominator line under each table reads `n = 100 (…pairs … over the ladder's rungs)`** while every row is over n = 25 (n = 50 / 80 / 76 / 28 likewise pooled over rows). The pooled figure is not wrong but it is not the number a reader needs, and the row already carries its own. Goes to the caption task the user has asked for (captions concise, the rest in the main text), with the pre-existing rendering defect this assessment noticed in passing: **every §4 caption is rendered twice** (380 `*Caption:` lines for 193 tables) and the *How to read* line twice for many — not this task's doing, present at `14342a72`.
- **Interpretation, agreed with a caveat.** The headline distance (5e-12) is two orders below the arms' own audit residual (3.8e-10 median): the two arms' exit iterates are closer to each other than either is to the point one further sweep reaches. That is consistent with both arms taking the same arithmetic on the kept components and stopping on the same predicate, and it licenses "the same fixed point to well within τ"; the agent's Limits §8 says correctly that it is not a statement at machine precision. The `A0p/A0` reading (0.097 / 0.070, 25/25 above τ) is the ownership rung's declared inconsistency measured on the state; the sentence that V3's Phase A pair compared two different fixed points is supported by the `A1/A0` beside row and by §3.4's declaration of `A1/A0p` as the pair.
- **Post hoc, as declared.** Rows chosen after a first draft (§7 (a)); reported, not accepted on; every caption says so. Acceptable for an added descriptive table; a V5 rule is A77's list's business.

**Verdict: merge.** Numbers verified by an independent route to every digit on the headline row and on the tooth's baseline; the gates that had to run ran and PASS at the commit the report names; zero PROCESS runs; scope as briefed. Records will be at the path the retire script prints.
