# DSM plan — Design Structure Matrices of the MDA-partitioning arms (A0, A1, B0, B2, B3)

> **Document status** — **DRAFT · PLAN, AWAITING USER REVIEW.** Written 2026-09-07 at the
> user's request, after the V3 campaign. Nothing here has been run; no sibling clone was
> written to; the dependency-analysis instrument was **not** executed. Every factual claim
> below was verified read-only against the committed records and the sibling repository, and
> the four load-bearing ones were re-verified independently by the orchestrator (§0).
> Base commit `c0ae5b28`; the V3 report this supports is
> [`../../MDA_partitioning_experiment_v3/V3_EXPERIMENT_REPORT.md`](../../MDA_partitioning_experiment_v3/V3_EXPERIMENT_REPORT.md).

## 0. The four claims this plan rests on, each verified

| claim | verification | result |
|---|---|---|
| The arms are one source tree plus environment switches, resolved at import | read `v3_runner.env_for`, `phase_a.env_for_phase_a`, `caller.py`, `module_solve.py` | confirmed |
| `c0ae5b28` is an **ancestor** of the analysis pin, and the driver drift between them is comment-only | `git merge-base --is-ancestor`; `git diff -U0 … -- process/core/` filtered for non-comment additions | confirmed: 5 commits, **70 insertions in `process/core/`, 0 non-comment** |
| The outer verification loop is a **B2 vs B3** difference, not B0 vs B3 | `module_solve_totals.outer_pass_hist` across arms | confirmed: B0 `{1: 630}`, B2 `{2: 653, 1: 7}`, B3 `{1: 660}` |
| `CLAUDE.md`'s instrument path is stale | `ls` both paths; locate `ANALYSIS_PIN_NAME` | confirmed: `dependency_analysis/` absent; it is `src/PROCESS_DSM/inputs/config.py:955` |

## 1. The central subtlety, resolved

**The four arms are one source tree and seven environment variables**, every one resolved
once at import from `os.environ`, with an unrecognised value raising at import rather than
falling back silently.

| switch | A0 | A1 | B0 | B2 | B3 |
|---|---|---|---|---|---|
| `PROCESS_ARCH_MODULE_SOLVE` | `flat_state` | `per_module` | `flat_state` | `per_module` | `per_module` |
| `PROCESS_ARCH_SEQUENCE` | — | `build_after_physics` | — | `build_after_physics` | `build_after_physics` |
| `PROCESS_ARCH_OUTER` | — (`verify`) | `trust` | — (`verify`) | — (`verify`) | `trust` |
| `PROCESS_ARCH_HOIST` | — | `feedforward[_lifted]` | — | `feedforward[_lifted]` | `feedforward[_lifted]` |
| `PROCESS_ARCH_POST_SOLVE` | — | `postsolve_nolift_<deck>` | — | `postsolve_<deck>` | `postsolve_<deck>` |
| `PROCESS_ARCH_LIFT` | — | `burn_time` (pulsed) | — | `burn_time` (pulsed) | `burn_time` (pulsed) |
| `PROCESS_ARCH_PIN_BURN_TIME` | — | `<hex>` (pulsed) | — | — | — |
| `PROCESS_ARCH_PRIME` | — | `fw_geometry` | — | `fw_geometry` | `fw_geometry` |

**Consequence, and it is stronger than "the DSMs would look similar":** a static source-level
DSM cannot represent an arm *at all*. The arm-selecting statements are `os.environ.get(...)`
at import, and none of the variant-point machinery exists in the tree the instrument is
pinned to (§2). Deriving four static DSMs produces four identical files.

**The object worth putting in a matrix** is the executed dependency structure of one
`Caller.call_models` evaluation under the arm's resolved settings. It has four separable
parts, all already recorded in our own committed campaign records:

1. **Row/column order** — `arch_sequence_head`. A0/B0 `(plasma_geom, build, physics)`;
   A1/B2/B3 `(plasma_geom, physics, build)`.
2. **The partition drawn on the matrix** — `arch_block_schedule`. Flat arms: one block
   `FLAT`. Block arms: `[M1, M2, PULSE, M3, FF]`.
3. **Membership of the iterated set** — `arch_loop_nodes` vs `arch_hoist_tails_resolved` vs
   `post_solve_totals.nodes`.
4. **Per-cell disposition** — for each data edge: iterated in-block, deferred to the outer
   pass, **cut**, reordered, primed, lifted, pinned, or hoisted.

The **edge inventory** — which node writes what that which node reads — is a property of
(deck × source tree) and is identical across arms by construction.

### Recommended deliverable

**One shared edge inventory per deck, four (five, with B2) per-arm overlays, and a per-arm
weighted diagonal.** Three layers: a 5×5 block matrix, a ~21×21 node matrix, and field-level
cells. Reasons, in order of force:

- The static cell set *cannot* differ, so deriving it per arm is a copy, not evidence.
  Publishing four static DSMs invites the conclusion that the arms are structurally
  identical — true at source level, false at schedule level. The inventory-plus-overlay form
  states both and cannot be read as either alone.
- Everything that differs is a permutation, a partition, and a per-cell mark on that one
  inventory — which is exactly what an overlay is. One derivation to gate, five presentations.
- **The arm-specific numbers live on the diagonal, not in the cells.** B0's diagonal is flat
  by construction (one sweep runs everything: every node at 2072 on nof `start000`); B3's is
  the block profile. That contrast is the most legible thing these matrices can show, and it
  is exact — counts, never timings.

## 2. The pin problem

### 2.1 Drift: measured, and not the issue

`ANALYSIS_PIN_NAME` is defined at `src/PROCESS_DSM/inputs/config.py:955` in the sibling. Cite
it via the `dsm_pin` field of our committed `arch_surgery/docs/data/dsm_node_map.json`; never
transcribe a hash into a document.

`c0ae5b28` is an **ancestor** of the pin, five commits behind. In `process/core/` the whole
diff is **70 added lines, every one a comment** — the `[XDSM-DRIVER]` declaration blocks the
instrument reads. Zero executable change in the driver. The three executable changes in the
whole range are semantics-preserving refactors made so the static analyser can resolve calls;
two live inside the `physics` node, one is stellarator-only and unreachable from every deck
here. **At model-node, module and cross-node-edge granularity the pin and our base are the
same graph.** State this with its measurement; it is not the reason for caution.

### 2.2 The real problem

**The pin's tree contains none of the arms' machinery.** `git ls-tree` at the pin lists seven
files under `process/core/solver/` — no `module_solve.py`, no `subsolve.py`, and no variant
points in `caller.py`. The instrument at its pin cannot see an arm even in principle.

Pointing it at our tree is refused twice: `config.assert_analysis_target` rejects trees
outside `data/reference_trees/`, and `process_dsm.py` refuses a tree carrying no `[XDSM-*]`
declarations because a drivers-on run there *"would silently produce the models-only graph"*.
Our tree carries zero such blocks.

### 2.3 Recommendation

**Do not run the instrument. Consume its committed export once, derive our own edge
inventory, and commit that as data in this repository.** The pin is fit for exactly the job
needed — the baseline model-layer read graph at a commit whose driver drift from ours is
comment-only — and unfit for the job it superficially resembles. This is the construction
`arch_surgery/idf_probe/a33_postsolve.py` already uses and gates, so it is precedented here.

Alternatives, rejected:

- **Re-pin to `c0ae5b28`.** Refused three ways: D2 freezes our base; the pin belongs to
  another study whose repo is read-only to us; and `c0ae5b28` carries no `[XDSM-*]` blocks,
  so a pin there yields a models-only graph with no driver layer — strictly worse.
- **Ask the sibling to analyse our fork tip.** Possible, but needs an archive of our commit
  cut into their reference trees, `[XDSM-*]` blocks authored for our six variant points, and
  one of their heavy slots. **Record as a named option with its cost; do not make this
  deliverable depend on it.**
- **Publish four static DSMs.** Refused — the null described in §1.

**Freshness, checked:** all three exports our committed `postsolve_<deck>.json` artifacts
consumed still hash-match their recorded `dsm.sha256_at_read`, though the sibling's HEAD has
moved. Trap T9 has not fired. That is luck; stage 1 turns it into a gate.

## 3. Staged plan

Single entry point `arch_surgery/dsm/run_dsm.py`, with `dsm_config.py` and `dsm_build.py`
beside it, modelled on `run_experiment.py`. Every stage **refuses rather than degrades**;
every failure path is reachable from the same button (protocol §15). Findings against the
instrument go to `DSM_VALIDATION.md` as V16+ (protocol §11), never into a task report.

| # | stage | consumes | produces | answers | refuses when |
|---|---|---|---|---|---|
| 1 | `preflight` | sibling `config.py` (regex for the pin name, never copied); git; the three `postsolve_<deck>.json` provenance blocks | `runs/preflight.json` — pin name, base↔pin distance, per-file executable-vs-comment drift, export sha256 recomputed vs recorded | *Is the instrument's coordinate system still the one our artifacts were built in?* | any export hash differs; pin name changed; interpreter cannot import `process` from the tree |
| 2 | `inventory` | `docs/data/node_writesets.json` (measured writes) × `a33_postsolve.dsm_reads(deck)` (static reads, `CLASS_TO_NODE` collapse) | **committed** `docs/data/dsm_edges_<deck>.json` + `edges_sha256` + the T1 probe result | *Which node writes what that which node reads?* | the T1 probe finds `physics.b_plasma_vertical_required` read by an M1 unit; any supermodel unmapped |
| 3 | `schedules` | `env_for` re-composed here **and** the campaign records' `arch_block_schedule`, `arch_loop_nodes`, `arch_hoist_tails_resolved`, `arch_sequence_head`, `arch_prime_name`, `arch_outer_mode`, `arch_lift_sites`, `arch_pin_enabled` | `runs/arm_schedules_<deck>.json` | *What did each arm execute, and does it match what its environment declared?* | declared ≠ executed on any field, any seed |
| 4 | `overlay` | 2 + 3 | `runs/dsm_overlay_<deck>_<arm>.json` — every cell tagged `in_block_iterated` / `deferred_to_outer` / `cut` / `reordered` / `primed` / `lifted` / `pinned` / `hoisted_pre` / `hoisted_post` / `post_solve` | *Which edges does this arm cut, defer or reorder — by name?* | a cell's endpoints are not both in the arm's node set; `objective_constraints` reaches a block (V12) |
| 5 | `weights` | `node_census`, `module_solve_totals.inner_sweeps_by_block`, `n_prime_calls`, `post_solve_totals` | `runs/dsm_weights_<deck>_<arm>.json` — diagonal counts **with denominators** | *How much work does each row cost this arm?* | `counted_matches_node_calls_total` false; census sum does not reconcile with `node_calls_solve_phase` |
| 6 | `figures` | 4 + 5 | 3 layers × 5 arms per deck, plus baseline↔intervened difference matrices | — | — |
| 7 | `tally` | 4 + 5 | `runs/dsm_tally.json` + report tables: cells by disposition, **cut/deferred/reordered/primed/lifted edges enumerated by name**, diagonal ratios with populations in the same sentence (T11) | *What changed structurally from baseline to intervened?* | any published cell has no stated population |
| 8 | `teeth` | — | `runs/teeth.json` | *Would this pipeline notice if it were wrong?* | fewer than 5/5 teeth trip |

**Teeth**, each of which must be refused and must name what it caught: (i) a doctored
`dsm_edges_<deck>.json` whose `edges_sha256` no longer matches; (ii) an export whose sha256
differs from the recorded one; (iii) an overlay built with the `tokamak` export against
`low_aspect_ratio_DEMO` (V6 — wrong deck's graph); (iv) a schedule whose declared environment
disagrees with the executed record; (v) an inventory built from a write set whose
`ystate_components_sha256` does not match the deck's spec.

**Sequencing.** 1 → 2 (once, ever) → 3 → 4 → 5 → 6 → 7; 8 standalone. After stage 2 commits
`dsm_edges_<deck>.json`, **the sibling's `output/` is never read again** — the T9 fix, and the
handling `dsm_node_map.json` already receives. Warn the sibling session before any
re-derivation.

## 4. What the matrices should show

**A0** — one block `FLAT`, order `plasma_geom → build → physics`, 21 executing nodes,
**diagonal uniformly 6** (6 sweeps × 21 = 126 node calls in one evaluation). Every
above-diagonal cell is loop-carried and resolved by re-sweeping.

**A1** — five blocks, order `plasma_geom → physics → build`. **Diagonal M1 4, M2 6, M3 3,
PULSE 1, FF 0** — 63 node calls, 0.5217 of A0, `n_prime_calls: 14`, burn time pinned. Under
`trust`, every above-diagonal cell crossing a block boundary is **cut, not deferred**.

**B0** — A0's topology under VMCON: 630 `call_models`, 2069 flat sweeps, 43 449 solve-phase
node calls, diagonal flat at 2072.

**B2** — the same partition as B3 **with the verification loop**: `outer_pass_hist
{2: 653, 1: 7}`, 39 156 node calls. *Include this arm* — see §5.

**B3** — 660 `call_models`, `outer_pass_hist {1: 660}`, 28 055 node calls, block diagonal
M1 1432 / M2 1817 / M3 1590, `n_prime_calls: 5502`. On pulsed decks the deck itself changes
and **VMCON's own row/column gains one design variable (ixc 178) and one equality constraint
(icc 93)**.

### The baseline → intervened difference, edge by edge

1. **The FirstWall → Build carrier, primed.** `fw` (M3, late) writes `build.dr_fw_inboard` /
   `dr_fw_outboard`; `build` (M2, early) reads the previous pass's values. Under A0/B0 an
   above-diagonal cell resolved by the second sweep. Under the primed arms,
   `caller.py:1571-1573` runs `set_fw_geometry()` at the head of every sweep, so the cell is
   **satisfied within the pass**. This is the only cell whose disposition differs between A1u
   and A1, and it moves the Phase A headline from FAIL to PASS at an A1u→A1 node-call ratio of
   exactly 1.0000. **Draw the prime as an annotation on that cell, not as a row** — it is
   deliberately not routed through `Caller._node` and never pooled into `node_calls`.
2. **The burn-time coupler, lifted then pinned.** `times.t_plant_pulse_burn`: writer `pulse`,
   reader `physics` — the only live cross-module back edge in the node map. Under the lift the
   cell **leaves the model layer** and reappears as (ixc 178, icc 93) in the optimiser's
   row/column; in Phase A the pin severs it entirely. **The cell is empty on `st_regression`**
   (k = 0). This migration is the most useful thing a DSM can say about the lift, and no cost
   table shows it.
3. **The post-solve hoist — rows leaving the loop.** `vacuum`, `water_use`, `costs` drop from
   2072 executions to **4**; `pulse` to 663. Their outgoing cells become non-loop-carried by
   construction — which is why the whole-state and restricted audits tell different stories
   (report §8 item 6).
4. **The `build`/`physics` reorder.** Mark it, and mark it **measured inert** (register V9a:
   bit-for-bit on 600/600 design points). A reader who sees it highlighted will over-read it.
5. **The outer verification loop is B2 vs B3, not B0 vs B3** — see §5.
6. **The cut set, enumerated.** Under `trust` every above-diagonal cell straddling a block
   boundary is severed for that evaluation. That set **is** the arm's correctness exposure,
   and its residual is what the exit audit measures. List it by field name; never summarise it
   as a count.

## 5. Scope correction: B2 must be included

The originally requested arm set (A0/A1/B0/B3) **cannot show the outer verification loop at
all.** B0 has one outer pass because the single-block guard skips the test; B3 has one because
`trust` removes it. Only B2 exercises it (`{2: 653, 1: 7}`). Since the V3 campaign's sharpest
result lives in B2 vs B3 — under the prime the trust step is *exactly* free on both pulsed
decks, 22/22 and 11/11 seeds — omitting B2 would make the DSM unable to depict the finding it
most needs to explain. **Cost: one entry in `dsm_config.py`.**

## 6. Risks and traps

- **T1 / T7 — `run()` vs `output()`.** Has bitten three times. Reads come from the export
  (rooted at `run()`); writes from the `PROCESS_IDF_PROBE=modules` census, closed at the
  boundary of `_call_models_once`, because ten models call their own `run()` from `output()`.
- **T2 — `=` matches `==`.** Never regex for writes. Write side is the census; read side is
  AST. A phantom write nearly entered the partition plan this way (V5).
- **T9 — reading a sibling's generated exports races their merges.** Answer is structural:
  derive once, commit here, gate on the hash.
- **T3 — folder position is not document status.** Several authoritative inputs live under
  `reports/deprecated/`.
- **T11 — a number without its limiting condition.** Every DSM number needs its population in
  the same clause, and `n_prime_calls` must be printed beside every ratio that excludes it.
- **V6 — the DSM is configuration-specific.** Each deck has its own export; using the
  `tokamak` export elsewhere is a silently wrong graph.
- **V7 — the DSM's feedback-edge set is not a convergence predicate.** Its four cross-module
  cells would declare convergence 1–2.5 sweeps early on 94–95 % of design points. The coupling
  that matters is the write-census state (840 / 846 / 827 components). **Print both on the same
  page**, or a reader will conclude the partition has nothing to cut.
- **V12 — `objective_constraints` has `in_call_models_once: false`.** A schedule derived from
  `module` alone gives `FF` a node that executes nothing: 789 no-op block sweeps, invisible in
  the model-evaluation count.
- **V13 — the hoist keys on the static node-map label.** `pulse` is labelled `PULSE` and does
  not join `FF` after the lift; the DSM must show it leaving by the pre-predicate/post-solve
  route or it misdescribes the mechanism.
- **V15 — "dead" needs two qualifiers.** The likeliest way a reader is misled here.
  `fw → build` is **value-frozen and displacement-live**: the value never changes between
  sweeps *and* it transmits the entry displacement exactly once under any one-pass schedule. A
  matrix that greys that cell out because "the value never changes" erases the edge the whole
  intervention exists to close. Every liveness mark must carry both qualifiers.
- **The unit problem (A18).** M1 is 24 DSM rows but 2 of 21 executing model calls. Weighting by
  DSM rows overstates M1 by an order of magnitude. State the unit on every figure.
- **Over-attribution.** `dsm_reads` attributes a shared helper's reads to every transitive
  caller — conservative (can only add readers) but it inflates cell counts. Say so.

## 7. What this analysis cannot show

1. **Nothing about convergence or optimality.** Check 1 failed on lad and on st all-pairs; the
   DSM cannot see why. Localising lad's failure to the lift was done by measurement.
2. **Nothing about wall clock** — the largest threat to the practical claim (report §7).
3. **Nothing about whether a cut is safe.** Only the exit audit measures the residual a severed
   edge leaves. The matrix shows what was cut, never what it cost.
4. **It cannot validate the post-solve exclusion set.** The DSM's backward crawl is one of that
   set's *inputs*, so using it to check the set is circular — and the Phase A headline rests
   entirely on that set. State this explicitly.
5. **It cannot see the arms in the source.** Anyone re-running the instrument at its pin gets
   the baseline, five times.
6. **It cannot decide location agreement** (report §5.2.2), and D6 forbids gating on iteration
   variables in any case.
7. **It cannot show edge magnitude, error direction, or δ-sensitivity** — those are A35's
   linear-coefficient measurements, not matrix cells.

## 8. Open items for the user

- **B2 as a fifth overlay** — recommended, §5.
- **Stale instrument paths** in `CLAUDE.md` and the `DSM_VALIDATION.md` header
  (`dependency_analysis/core/inputs/config.py` → `src/PROCESS_DSM/inputs/config.py`).
  *Approved by the user 2026-09-07 and handled as a separate task.*
