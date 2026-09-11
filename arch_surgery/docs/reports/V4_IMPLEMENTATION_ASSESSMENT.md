# V4 harness — the orchestrator's whole-implementation assessment

> **Document status** — **CURRENT.** Written 2026-09-11 by the orchestrating session at the close of
> the V4 harness implementation (plan items H1–H8 and driver changes DR1–DR7 merged; the last fix task, A63
> (stage-provenance), merged at `52264b53`). This is the assessment the user's
> delegation of 2026-09-10 (D24) asked for: *"Critically assess the implementation once it's done,
> and implement fixes to problems you find (via dispatched agents). Give me a report with what's
> happened (and what decisions are made) when everything is done."* Every number here is read from a
> committed verdict or stage record at the commit named beside it; none is produced by a shell
> invocation. Folder position records lifecycle, not validity (trap T3).

---

## 0. In one paragraph

The V4 measurement harness is built and gated. At the one press from the repository root (`f8bce151`, G1 at `d6f0fdf4`, the last gate and
teeth added at `52264b53`) the button reports **25 gates PASS, 0 FAIL, 147 of 147 teeth tripped**; the
reproduction gate reproduces the previous revision's twenty runs bit for bit on 256 of its 270
reference values, the 14 excluded by name with their reason; the smoke runs the campaign's own chain
at one seed on one configuration and reaches the independent recomputation with 0 mismatches over
1 901 values. Eight harness tasks and seven driver tasks were merged between 2026-09-10 and
2026-09-11, each with a per-task critical assessment appended before its merge. The campaign is
**not** started: `EXECUTION_APPROVED` is `False`, and one methodology decision (D26, how the reference
arm is entered in Phase A) awaits the user before the first press of 949 runs.

## 1. What the exit audit is, what went wrong, and what D25 changed — in plain language

*Written at the user's request (2026-09-11, on approving D25) as part of this report.*

Every run in the experiment ends by asking one question of the point the optimiser accepted: **if
every engineering and physics model were run once more from exactly this state, how much would the
state move?** That one extra sweep is the exit audit. If nothing moves, the accepted point was a
true fixed point of the models, and the run's accuracy is settled independently of whatever stopping
rule the arm used. Every arm gets the same sweep, it is never charged to the arm's cost, and its
result is the ruler the experiment uses to say two arms were compared at matched accuracy.

For two revisions the audit reported that one quantity, the insulation strain in the toroidal-field
coil, moved by about 0.7 % on every pulsed run in every arm, including PROCESS exactly as shipped.
That read as "no arm converges this component", and it was published as such (improvement item 11).

The cause was in the instrument, not in the runs. After the optimiser accepts a point, PROCESS
writes its output files. Doing so, the TF-coil stress routine switches its radial mesh from 100 to
500 layers and never switches it back. The audit ran after that, so its sweep computed the strain on
500 layers against a state converged on 100. The 0.7 % was the difference between two meshes, not a
movement of the state. Putting the mesh back gave exactly zero (A61).

**D25** says: before the audit sweeps, put back everything the output path changed, not only the
coupling variables. The set of fields to put back is derived per run by comparing the state at the
accepted point with the state after output, so it does not depend on knowing which field is the
culprit today. The audit records what it put back (85 fields on the reference arm), what it could
not (0, with two fields named that can never round-trip), and which fields it deliberately left
alone: PROCESS's own call counters, so that the instrument's work is not subtracted from the run's
cost. Nothing in any arm's run changed. The straddle comparison across the change (G1) showed
every one of 51 319 output-file lines identical before and after.

**What it does not do.** It does not remove the output loop from any arm: BR and B0 still run
upstream's two output-time sweeps, B1 and B3 call the output routines once, exactly as the switch
matrix says. It does not correct a number: it restores state bit-exactly and measures again. And it
does not touch the gap between the accepted point and the file PROCESS writes: that gap is real,
about 0.7 % on the TF-coil strain on the reference arm, it is a property of PROCESS as shipped, and
it is now visible per run as the after-run audit (issue I-21).

**What it means for the ladder.** Matched accuracy holds from B0 onward: B0 is the control at a
fixed tolerance τ, and before D25 the ruler said B0 missed τ on one component on every pulsed run,
which contradicted the control's defining property. After D25 the handed-over state in B0, B1 and B3
is a fixed point of the solve's own map to 1e-11 or exactly, on every configuration: 0 of 31
declared-position records have any component above τ. The rung comparisons are therefore between
arms that are all at fixed points, which is what the method demands. The `BR → B0` rung stays
"reported, never accepted on", as the plan says; the reference's own residual is context for RQ4.

## 2. What was built

*Caption: one row per plan item, the task that delivered it, its merge commit, and the gate that
binds it. The harness lives in `arch_surgery/MDA_partitioning_experiment_v4/harness/`; the
experiment's own copy of PROCESS is under `…_v4/PROCESS/` at `f2dc9243` plus the seven driver
changes; nothing under `process/models/` changed except the one approved edit (`pulse.py`, D11).*

| item | task | merged | what it is | bound by |
|---|---|---|---|---|
| H0 | A48 (harness-data) | `d9fe737f` | the 16 committed data files | `data` |
| H1 | A47 (harness-skeleton) | `42a1edd1` | config, switches, arms, provenance, the runner's preflight | `composition`, `rungs`, `provenance`, `capability` |
| H2 | A49 (harness-reference) | `92990fe7` | the 20-record reproduction reference | GR |
| H3 | A50 (harness-run) | `6be26e85` | the run path: one in-subprocess driver, records, pool | `run_path`, G7 |
| H4 | A51 (harness-artifacts) | `ed343e46` | artifacts, input files, census, per-run sets | `artifacts_*` |
| DR1–DR7 | A56–A60 | `16d7eb55` … `73525d1e` | switch renames, the one-call output path, predicate counters, the two rulers, the retry ladder | G1 per change, G8, G9 |
| H5 | A52 (harness-gates) | `d13a54c7` | every plan gate inside the harness, with teeth | itself |
| — | A61 (insstrain-diagnosis) | `fd480aff` | item 11 diagnosed as an instrument artefact | — |
| H6 | A53 (harness-tally) | `d98f602a` | the constructions, the tally stages, the tables | `tally_contracts` |
| D25 | A62 (exit-audit-restore) | `a3407d5d` | the whole-structure restore before the audit sweep | G1 straddle, GR, G4 |
| H7 | A54 (harness-analysis) | `72c343d1` | the independent second implementation of every cell | `recomputation` |
| H8 | A55 (harness-smoke) | `bfaee7ce` | one chain for smoke and campaign; §4 rendered from records | `run_kind_separation` |
| I-22 | A63 (stage-provenance) | `52264b53` | stage records declare and stamp what they read; consumers refuse stale ones; census records stamped; self-checks build their own fixtures | `stage_provenance` |

## 3. The gates at the final press

*Caption: from the experiment plan's §4.1 as rendered by `--plan-tables` from the `gate_table` stage
record, over the one press at `f8bce151` (G1 re-run at `d6f0fdf4`). Counts are the gate's own;
"compared" is its denominator. The population is the **gate population**, not the campaign.*

| gate | plan | verdict | compared | mismatched | teeth |
|---|---|---|---|---|---|
| `g0prime` | G0′ | PASS | 77 files | 1 (the approved `pulse.py`) | 4/4 |
| `reproduction` | GR | PASS | 256 of 270 reference values, 20/20 runs | 0 | 8/8 |
| `switch_neutrality` | G1 | PASS (straddle `fd480aff` → `d6f0fdf4`) | 2 831 values + 51 319 lines | 0 | 9/9 |
| `prime_map` | G2 | PASS | 5 026 components | 0 | 2/2 |
| `cold_chain` | G3/G3c | PASS | 60 | 0 | 4/4 |
| `audit_restriction` | G4 | PASS | 12 | 0 | 6/6 |
| `switch_composition` | G5 | PASS | 141 | 0 | 3/3 |
| `entry_and_warm` | G6 | PASS | 4 204 | 0 | 3/3 |
| `record_completeness` | G7 | PASS | 89 + 82 declared fields | 0 | 9/9 |
| `predicate_mode` | G8 | PASS | 12 pairs | 0 | 4/4 |
| `output_path` | G9 | PASS | 11 runs | 0 | 4/4 |
| `tally_contracts` | — | PASS | 451 | 0 | 10/10 |
| `recomputation` | — | PASS | 1 901 | 0 | 9/9 |
| `run_kind_separation` | — | PASS | 175 records | 0 | 6/6 |
| `stage_provenance` | — | PASS | 17 | 0 | 5/5 |
| 10 harness self-checks and artifact gates | — | PASS | — | 0 | 61/61 |

**25 PASS, 0 FAIL, 147/147 teeth** (24/139 at A55's press; A63 added one gate and three teeth to `artifacts_census`). Run records at the press: 140 at `f8bce151`, 25 at `b784158c`
(G1's after capture, the smoke, the output-path contrast), 6 at `fd480aff` (G1's before capture,
never re-made), 11 at `3d64625c` (A61's diagnosis stage, outside `--gate all`); 173 `gate`,
15 `smoke`, **0 `campaign`**.

## 4. Decisions made, and by whom

*Caption: every decision-register entry since the delegation, with its author. The rule that came out
of D25 is stated once here and recorded in the queue's protocol.*

| decision | author | what |
|---|---|---|
| **D24** | user, 2026-09-10 | A47's two rulings approved; the rebuild delegated to the orchestrator with autonomous implementation decisions, per-task review, fixes via agents, a report at the end |
| **D25** | **proposed and implemented by the orchestrator, approved by the user 2026-09-11 "for now"** | the exit audit restores the whole data structure (§1). **Process fault, recorded:** the ruling was minted, dispatched (A62) and merged before it was put to the user. The user: *"Rulings that are documented should always be my rulings. If it is decision-worthy, it should be stamped with my approval first at least."* **Rule from it:** a decision-worthy item is written as a *proposal* in the register and stamped by the user before the implementing task is dispatched; implementation choices inside a task stay in the task's own "autonomous decisions, each with its reversal" table |
| **D26** | proposed by the orchestrator 2026-09-11, **awaiting the user** | how the reference arm `AR` is entered in Phase A: from the same displaced snapshot as the other arms (A55's chain; the rung then isolates the stopping rule) or from the input file's own point (the entry gate's comment). Recommendation: the paired entry. Nothing runs until ruled |

**Implementation decisions taken by the orchestrator under D24**, each recorded in the task row
and the archived report it belongs to: gate records are re-made only when a change touches what
the gate reads (amendment 15, the user's run-budget instruction); the verifier's review differs from
the agent's press rather than repeating it; G1's exclusions name leaves, never blocks; a
record-field rename is translated, never excluded; a gate may declare that it reads a measurement
stage and a stale stage record is refused; the accuracy tables' `n` counts runs; the smoke and the
campaign are one chain parameterised by run kind. Each has its reversal in the report it came from.

## 5. Findings, in order of consequence

1. **Improvement item 11 was an instrument artefact, not a convergence failure** (A61, A62). The
   7e-3 residual on `tfcoil.insstrain` in every arm was the output path's mesh change. With the
   instrument corrected, 0 components are above τ in every arm on every configuration at the
   accepted point. Item 11 is closed as a convergence finding.
2. **PROCESS as shipped writes an output file that is not its solved state** on the TF-coil
   strain (0.70–0.72 % off, both pulsed configurations), and latches `None` on the steady-state
   deck. Filed at the user's instruction directly into
   `PROCESS_code_analysis/docs/bug_reports/2026-09-11_tfcoil_output_mesh_written_insstrain_and_none_latch.md`
   with its README row, **left uncommitted there for the user**; a copy sits in
   `docs/reports/outgoing/`. Issue **I-21** (what else the output pass leaves inconsistent) is open,
   with a per-run handle: the after-run audit reads 6.99e-03 / 7.02e-03 on the reference arm. **Not
   measured:** whether the one-call output path (B1/B3 as the campaign composes them) writes the same
   gap — GR's B1/B3 records carry the output-loop override, so their after-run numbers do not
   speak to it. One after-run audit on a campaign-composed B1 would settle it; the position is
   refused outside GR today, so that is a small declared gate.
3. **`--resume` cannot cross a schema change**, and two schema changes landed in parallel (A53's
   rename, A62's instrument fields), so no record population was complete under the merged schema
   and the smoke's one press re-made every run (167/167). This is the record contract working; the
   lesson is to sequence schema-changing tasks (amendment 17).
4. **Six wiring defects were caught by gates during the implementation and fixed before merge**,
   none by inspection: the hard-coded `resume=True` (A52); the G1 self-comparison hiding 42
   cross-tree leaves (A52); the `numerics` rewind moving `n_model_calls` (A62); the tally reading
   `REFERENCE_FIELDS` where GR reads `compared_fields()` (A55); G1's after capture trusting a manifest
   (A55); the accuracy tables' `n` built two ways (A54). The last three were found by the
   independent recomputation and the one press — the two mechanisms the plan added for exactly
   this reason.
5. **The campaign stage was a refusal stub** until A55: it named summarising stages that did not
   exist. It is now the same chain the smoke runs, at 949 runs, and refuses for exactly two
   reasons while approval is off.

## 6. What is open at completion

| item | state | who decides |
|---|---|---|
| **D26**, the reference arm's Phase A entry | proposed; the chain enters `AR` paired, the entry gate's comment says otherwise | **user** — blocks the campaign |
| **Execution approval** | the plan's header is DRAFT · NOT APPROVED; `EXECUTION_APPROVED = False`. The user said on 2026-09-11 *"When everything is done, you can run it"*; the approval commit (dated header edit + flag flip) is made only after D26 is ruled and this assessment is read | user |
| **I-21** | open, handle per run; the one-call case unmeasured | user (a small gate task) |
| **I-22** | closed by A63 (`52264b53`); the three optimisation-entry census records stay `census-1` until a press asks for that entry | — |
| **I-20** | the empty `pulse` visits on `st_regression`; disclaimed in captions, not fixed (plan §3.7 (d)) | recorded |
| `mixed` predicate adoption | both rulers published on every run (DR5); adopting one is the campaign's reading, not the harness's | campaign |
| Outgoing drafts | `2026-09-02_process_defects…` and `2026-09-04_first_wall_thickness…` staged, never handed over | user |
| The §4 tables | filled from the **gate population**; the campaign fills them again | campaign |

## 7. What running it will do

From the runner's budget at `bfaee7ce`: **949 runs** — 3 entry references, 275 displaced-entry
evaluations, 396 stencil-point evaluations, 275 optimisations — over three configurations at 25
seeds, records stamped `campaign`, then the tally, the independent recomputation and its verify, then
`--plan-tables` re-renders §4 from the campaign population. The smoke did 13 runs on one
configuration at one seed. Wall clock is context only: the 165 gate runs of the last press summed to
about 63 minutes in-child at three workers.

## 8. Change log

| date | change |
|---|---|
| 2026-09-11 | Created at A55's merge; A63 dispatched. |
| 2026-09-11 | A63 merged (`52264b53`); §2, §3 and §6 updated; the document committed. |
