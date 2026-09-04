# A35 (cold-census) — investigation plan: name the carrier of the displacement-scaled cross-block transient

> **Document status** — **CURRENT · INVESTIGATION PLAN, binding for task A35.** Written by task
> A35 (cold-census), 2026-09-04, on branch `A35-cold-census`, branched from
> `architecture_surgery` at `ba69c05d`, experiment base commit `c0ae5b28` (all `process/models/`
> content identical to the base; nothing in this task touches `process/` at all). Committed
> **before** any measurement run of this task; the measurement script
> [`arch_surgery/idf_probe/a35_cold_census.py`](../../idf_probe/a35_cold_census.py) is committed
> before any published number (protocol §15). Deviations found necessary during execution are
> dated amendments here, never silent changes.

## 1. The question

**Name the carrier of the displacement-scaled cross-block transient**: the mechanism by which a
one-pass feed-forward block chain's exit state differs from the flat MDA's fixed point, when the
validated DSM says inter-block edges are forward-only.

Evidence in hand (all artifact-derived, cited by task and run record):

- **Zero-point control (A36 warm gates):** entry AT the fixed point, one chain pass stays put —
  cross-max `0x1.160774e05e9e3p-27` (`large_tokamak_nof`, pinned), exactly `0x0.0p+0`
  (`low_aspect_ratio_DEMO`), `0x1.c22fb514702ddp-29` (`st_regression`).
- **Cold-entry displacement (A34 `pin_gate`, `large_tokamak_nof`, A18-artifact machinery gate):**
  one-pass exit 1.459e-2 from the flat fixed point, 243/840 components ≥ τ; top movers
  `build.dz_tf_upper_lower_midplane`, `build.dr_shld_vv_gap_outboard`, `pf_coil.ssq0`. The same
  pinned chain WITH the outer loop repairs to 1.53e-8 in **3 outer passes** (~30×/pass).
- **δ = 0.10 displaced warm entries (V2 Phase A, N = 25/deck):** A1 one-pass audit median
  2.44 / 0.18 / 0.26 (p90 9.86 / 0.29 / 0.34) vs A0's 6.3e-10 / 0.0 / 5.4e-9 — with
  **amplification** on `large_tokamak_nof` (p90 ≈ 10× the 0.1 input scatter).
- **The asymmetry argument:** any intra-block mechanism (step-test limits, slow local modes,
  symmetric non-idempotency) binds both arms equally at matched τ and cannot produce a 9-order
  asymmetry; the deficit is resolved only by repeated cross-block propagation.
- **R1a / V14:** a recorded cross-module transient cascade (~147 fields / 17 modules) that is
  bit-exact 0 at every accepted optimum and dormant at the harvest — invisible exactly where all
  dynamic feed-forwardness validation ran.
- **A31 precedent:** a static source scan already failed to close this class of question once;
  this investigation is **dynamic-first** (the user's ruling in the A35 row).

## 2. The four candidate carriers, with their discriminating signatures declared in advance

| # | Candidate | Signature, if it is the carrier |
|---|---|---|
| **(a)** | **An edge the DSM missed outright** — a computational cross-block read absent from the static graph | The traced verified chain shows pass-≥2 movers whose earliest-block writer's reconstructed input change is confined to components owned by **later** blocks (a backward data channel); the chained-restart identity (§4, S3) **holds** (the movement is carried by the coupling state); and the named read is **absent** from the frozen per-deck static export's reader set for that writer (`st_regression`), or absent from the DSM's recorded cross-module cell set with the read confirmed in source on the `run()` path (`large_tokamak_nof`) |
| **(b)** | **A state/branch-dependent edge** — structurally present, dead near fixed points (where all dynamic validation ran), live at displaced states | Same dynamic signature as (a) — backward channel, restart identity holds — but the frozen export **contains** the reader relation. Split from (a) by reading the edge's source at the traced state values: a branch condition false at fixed points and true at the displaced state, or a V3-pattern value (constant at every fixed point, moving only during transients) |
| **(c)** | **Schedule/DAG order mismatch** — a forward edge crossed backward by the block schedule | The named carrier edge is **forward in the DSM's own topological order** (writer earlier than reader in the export's `supermodel_execution_order`), but the A1′ schedule assigns the writer's node to a **later block** than the reader's. Statically checkable once an edge is named; additionally a full schedule audit (every variable-level cross-block writer→reader pair whose reader block precedes its writer block under `BLOCK_ORDER`) is run on the `st_regression` export unconditionally |
| **(d)** | **A non-idempotent model** — output differs on re-execution with bit-identical inputs; no data channel at all, invisible to any static analysis | The chained-restart identity (§4, S3) **fails**: a fresh process re-entered at the recorded end-of-pass-1 state does not reproduce the in-process pass 2 bit-for-bit on some component(s) — after the tail confounder is excluded (§4, S3 caveat). Or: a mover whose writer's reconstructed coupling-visible inputs are bit-identical between passes while its output moved. Named to the model by the dynamic writer census |

### 2a. User-directed addition (2026-09-04, relayed before execution completed): the lagged-edge sub-hypothesis of candidate (c), and its census

**Source pattern:** the sibling study's M119 contested-write audit
(`PROCESS_code_analysis/docs/reports/deprecated/M119_contested_write_audit.md`, read-only; the
file carries no `> Document status` header — their archive convention differs from ours — and is
read as delivered). Its issue #2: `divertor.a_div_surface_total` is seeded 50 m² by
`Stellarator.st_fwbs` (first evaluation only) and computed by `st_div`; on the solve path
`st_fwbs` (order 174) runs **before** `st_div` (175), so `st_fwbs` consumes the divertor area
**one evaluation late** — a *lagged edge*: a reader scheduled at-or-before its writer within one
pass, consuming the previous pass's (or the entry state's) value. The pattern class fits every
measured signature of our transient: identical to the current value at a fixed point (↔ the
bit-clean warm gates), error equal to the entry displacement away from it (↔ the δ-scaled
transient), refreshed once per additional full pass (↔ the ~30×/pass repair), self-healing
inside a block's own inner iterations but **never refreshed across blocks under one-pass trust
mode** (↔ the cross-block asymmetry).

**Candidate (c) therefore splits, and both halves are pre-declared:**

- **(c-order)** — §2's original reading: a forward DSM edge crossed backward by the *block
  assignment* (writer's block after reader's block).
- **(c-lag)** — the M119 pattern at our granularity: a **cross-block iteration-carried
  dependency** — a reader block earlier in `BLOCK_ORDER` than the writer block of a value it
  consumes, so each outer pass hands it the previous pass's value. Invisible to an
  ordering-blind DSM by construction (the sibling's I-44: same-pass vs next-pass timing is
  deliberately not encoded). Note (c-lag) and (b) can name the same edge: (c-lag) is the
  *timing* statement (the edge is live but consumed one pass late), (b) the *liveness*
  statement (dead at fixed points). The report names both aspects where both hold.

**The lagged-edge census (first-class measurement, not a footnote).** On the traced verified
chains, enumerate every above-τ pass-2 mover whose earliest-block writer's reconstructed input
change is confined to **later-block components' pass-1 movement** (§5's view rule): each such
mover is a demonstrated *consumer of a value written later in the pass by another block* — the
dynamic lagged-edge census at block granularity. Reader evidence (§5 step 5) then names the
individual edges. The census's real target is siblings of the M119 pattern **whose consumers do
reach the residuals/objective** — M119 audited only the 22 contested-write (two-writer) entries,
so absence there is not absence of single-writer lagged edges.

**Sub-discriminator, pre-declared: state-carried vs seed-type staleness.**

- *State-carried* (the reader consumes the perturbed entry value): pass-2 mover magnitude scales
  with entry displacement. Measured on three displacement points — cold (initialisation
  distance), δ = 0.10 warm, and **one added traced run per deck at δ = 0.05 (seed 1)** —
  expectation: warm-δ ratio ≈ 2 between δ = 0.10 and δ = 0.05 in the linear regime, and ≈ 0 at
  the fixed point (A36's warm gates, cited).
- *Seed-type* (M119's hard-coded 50 m²): a first-evaluation error **independent of δ** — ratio
  ≈ 1 between the two warm runs at matched pass. Any seed-type candidate must additionally be
  reconciled with the bit-clean warm gates by checking **which** of the two let it hide: the
  seeded variable is inside the restored ystate (the warm entry supplies the computed value), or
  its consumers never reach the audit's readset — checked against the a26 spec's key set, never
  assumed.

**The specific M119 instance is out of scope on our decks, demonstrated rather than assumed:**
`st_regression` is a *spherical-tokamak* deck, not a stellarator — neither of our decks sets
`istell` (unset → 0; register V6 records `istell` identical across all five decks), the traced
runs' node censuses contain **no stellarator-family node** (21 nodes each), and the block
schedule refuses `istell != 0` outright (`caller.py` `_call_models_by_module`, the
tokamak-only guard). Its inertness claim therefore needs no re-verification here — the code path
does not execute — and what transfers is the **pattern**, which the census above measures in
this tree at `c0ae5b28`.

### 2b. User-directed refinement + correction (2026-09-04, second relay): the frozen-edge set, the three orderings, and the KNOWN-CUT-first dichotomy

**Correction to §2a:** "intra-block lags self-heal inside a block's own inner iterations" holds
only for blocks the schedule **iterates** (M1/M2/M3). `PULSE` and `FF` execute once per pass, so
a read-before-write pair *inside* them is not refreshed under trust mode either. **The frozen
set is: every backward edge of the EXECUTED schedule not spanned by an iterating loop** —
cross-block backward edges AND intra-block backward edges inside non-iterating blocks. The
census enumerates both.

**Three orderings are in play; a feedback classification is a property of (edge, ordering):**
(1) the sibling instrument's native process line (static DFS source order; its `data_interface`
projected edges are writer→reader with **no within-pass ordering semantics** — a lagged read and
a fresh read produce the identical edge); (2) any sequenced/optimized DSM view (sequencing
minimizes below-diagonal marks, so an acyclic read-before-write pair is displayed writer-first —
the sequenced view *hides* the lag pattern by construction); (3) the **executed schedule**
(`build_after_physics` at module granularity, PROCESS-native intra-module order) — the only
ordering that determines runtime lag. Every classification below is stated against ordering (3),
with (1) as the edge-existence authority.

**Primary dichotomy, now at the top of the decision tree — KNOWN-CUT vs UNKNOWN edge.** Trust
mode deliberately cuts every backward edge of the executed schedule. The backward edges
**computable from the analysis's exports** (`data_interface` × executed order) are **known
cuts**: a carrier in that set means *no artifact is wrong anywhere* — the transient is the
priced cost of the trust bet, and the finding is "known cut edge X, magnitude underestimated".
The census enumerates this set explicitly (static, cheap: the frozen `st_regression` export ×
the run's own schedule; for `large_tokamak_nof`, the committed register's recorded cross-module
cells — V2–V5 under the V6 config-match — serve as the export authority, never a live sibling
read, trap T9). Only a carrier **not** in the known-cut set implicates the pipeline, and the
runtime census then discriminates the defect layer directly: a traced read absent from the
access records = **missing edge** (capture layer: undecidable branches, aliasing, dynamic
access); a recorded edge whose traced runtime position contradicts the static line =
**misplaced edge** (ordering projection error).

**The full label partition, pre-declared** — every above-τ carrier edge gets exactly one
primary label: **KNOWN-CUT / MISSING-EDGE / MISPLACED-EDGE / STATE-DEPENDENT (edge only live at
displaced states, absent from the cut enumeration) / NON-IDEMPOTENT (no data edge at all)** —
with liveness class (fixed-point-dead vs always-live; state-carried vs seed-type per §2a)
recorded as an annotation beside the primary label, since a known-cut edge can *also* be
fixed-point-dead, which is exactly what would have made its cut look free.

Pre-declared fifth possibility, for honesty rather than symmetry — **(e) inner-dust echo**: a
pass-2 mover could in principle be the pass-boundary echo of sub-τ intra-block dust (inner solves
stop at inner-τ = 1e-6, not at 0). Quantitative bound stated in advance: this mechanism cannot
move a component by more than ~O(10¹)·τ per pass; the measured pass-2 movement is ~1.5e-2, four
orders above it. If, contrary to the record, all observed movers sit within ~10× τ, mechanism (e)
is reported as the finding and no carrier among (a)–(d) is claimed.

## 3. Instruments (all existing; no driver or model edit is planned or expected)

| Instrument | What it yields | Provenance |
|---|---|---|
| `PROCESS_ARCH_PASS_TRACE` (+ `_FULL_FROM=1`) | Every **joint-test** residual evaluation as JSONL: outer-test records of the verified block schedule; the flat arm's per-sweep inner records (its single-block inner test IS the joint test). From the configured pass on, every above-τ mover with before/after **hex**, plus moved-constant and discrete-mismatch detail | A31; switch-neutrality gated there; trust mode emits **no** outer-test records, so the traced chain is the **verified** outer |
| `v2_eval_one.py` | One `call_models` under any env-selected architecture, no optimiser; exact-hex entry/exit snapshots (`y_entry.json` / `y_exit.json`), uncharged exit audit, per-node census; `--entry-state` restores a snapshot bit-for-bit (readback-checked) | A34/A36; gated with teeth there (`evalone_gate` 4/4, `entry_gate` 7/7 on `st_regression`) |
| Pin instrument `PROCESS_ARCH_PIN_BURN_TIME` (+`LIFT=burn_time`) | The burn-time coupling held bit-exact through the chain (tripwire, refusals) | A34; the pin was shown **sound** by the pin_gate's verified control |
| `writeset_a26_<deck>.json` `subsets` | y-component → owning block (V11: a partition — every component exactly one module) | A25/A33, committed |
| `node_writesets.json` | y-component → writer node(s), **dynamic** census (the writer authority; includes `<x_inject>`) | committed |
| Run's own `arch_block_schedule` + `module_solve_stats.hoisted_tail` | node → block under the actual schedule of the actual run | recorded per run |
| Frozen per-deck static export (`st_regression`), `runs/dsm_exports/` in the **main checkout, read-only** | variable-level writers/readers, supermodel execution order — the reader-evidence join and the (c) audit | delivered by the sibling study at their `bd74dacb`, sha-stamped (V14 follow-up 2); never read live from the sibling repo (trap T9) |
| Source reading at the study commit | file:line confirmation of a named read, `run()`-path discipline (traps T1/T7) | only **after** the trace points at an edge (candidate confirmation, never candidate generation — the A35 row's ruling) |

There is **no frozen static export for `large_tokamak_nof`**; the DSM's source config matches
that deck exactly (V6), so reader evidence there is: the recorded cross-module cell set
(V2–V5, V6) + source confirmation of trace-named reads. No cross-study request will be made
without a demonstrated defect (standing rule, V14 follow-up 3).

## 4. Measurement sequence — stages of `a35_cold_census.py` (all runs serial; ONE PROCESS subprocess at a time; every run a fresh subprocess in its own directory, `PYTHONPATH` pinned to this worktree, exact tree asserted in-process — traps T6/T10)

Decks: `large_tokamak_nof` (pulsed, k = 1, pin required) and `st_regression` (k = 0, nothing
pinned). Artifacts: **a26-generation ystate + writeset everywhere** (driver predicate,
perturbation spec and exit audit are all the same a26 artifact per deck, so exit snapshots chain
into `--entry-state` under the sha check). τ = 1e-6, inner τ = default (= τ). Displacement:
δ = 0.10, **seed 1** (pre-declared; fallback seed 2 only if the seed-1 run crashes, and the
substitution is reported). Original decks for every run (pin chains refuse the lifted deck by
design). Arm environments are composed from `run_a28.env_for` exactly as A34's pin_gate composed
them, with the a26 driver artifacts substituted and the trace variables added per stage.

**S0 — references (per deck).** One FLAT (`flat_state`) cold single-eval, **traced**
(`FULL_FROM=1`): yields (i) the flat cold-control trace (per-sweep movement census), (ii) the
reference exit snapshot (the warm base for displaced entries), (iii) the converged burn-time hex
(the pin value on `large_tokamak_nof` — A34's pin_gate recipe).

**S1 — gates (teeth first; §6).** G1 trace-inertness, G2 entry-restore fidelity on
`large_tokamak_nof`, G3 parser cross-checks with a doctored-line tooth and a known-mover tooth.

**S2 — traced verified chains (the core measurement).** Per deck × entry ∈ {cold,
displaced-warm(δ = 0.10, seed 1)}: the A1′ block chain (`per_module`, `build_after_physics`,
hoist as the arm defines it, `large_tokamak_nof` + lift + pin) with the **verified** outer
(`PROCESS_ARCH_OUTER` unset) and `PROCESS_ARCH_PASS_TRACE` + `FULL_FROM=1`. Pin values: cold =
the S0 flat-converged burn hex; displaced = that value × `perturb_factor(seed, "times.t_plant_pulse_burn", δ)`
(bit-identical to what the in-run perturbation computes — the Phase A campaign's own rule).
Every pass-≥2 above-τ mover comes out with before/after hex; pass-1 census recorded too
(`FULL_FROM=1`) because the input-change reconstruction (§5) needs pass-1 deltas.

**S3 — chained trust restarts (the (d) discriminator), cold entry, both decks.** Trust-mode
chain runs, each a fresh subprocess: T1 from the cold entry → exit `Y1`; T2 with
`--entry-state Y1` → `Y2`; T3 with `--entry-state Y2` → `Y3` (pin held at the same hex
throughout on `large_tokamak_nof`). Identity checks, all bit-level:

- **Chain check (integrity + physics):** for every pass-2 mover of the S2 traced verified run,
  `Y1[key]` (argmax element where the component is an array) must equal the trace's pass-2
  `before_hex`; pass-3 movers likewise against `Y2`.
- **Restart identity (the discriminator):** pass-2 movers' `after_hex` vs `Y2`; pass-3 movers'
  `after_hex` vs `Y3`; and the **full 840/827-component** comparison of `Y3` (respectively the
  chain state at the verified run's own outer-pass count) against the verified run's
  `y_exit.json`.
- **Verdict rule:** every comparison equal → the whole multi-pass repair is carried by the
  coupling state alone → candidate (d) is **excluded** as the carrier (its remaining scope is
  stated in §7). Any mismatch → localise by component and writer; **before** concluding (d),
  exclude the tail confounder: `Y1`/`Y2` include the hoisted tail's once-per-call writes, which
  the in-process verified pass 2 has not yet seen. License to treat that as inert: V10/A13
  measured the tail (`costs`, `water_use`) feeding **nothing** back, bit-identical over full cold
  optimisations. If a mismatch survives on a component whose writers could read tail-owned state,
  the pre-declared follow-up is one verified + one chained-trust rerun with the hoist **off**
  (no tail at all) — the only case in which extra runs are added, and they are reported as the
  follow-up, not as tuning.

**S4 — flat-arm controls from the same entries.** The S0 cold flat run is already traced. Add
one traced FLAT run from the displaced-warm entry (same snapshot + seed), per deck. Symmetry
check: the block arm's pass-≥2 mover families must be visible **contracting inside the flat
loop** (sweep-≥2 movers of the flat trace), with per-sweep contraction factors reported.
A flat loop with no trace of those families while the block arm moves them would point at a
schedule-specific mechanism ((c)/(d)) and is reported as such.

**S5 — analysis (offline, no PROCESS runs).** Classification of every above-τ pass-≥2 mover
(§5), the decision tree (§7), the static-export joins on `st_regression` including the
unconditional (c) audit, and source confirmation (file:line) for any named edge.

Run budget: ≈ 15 single-eval runs + 2 gate runs, strictly serial. Bulk artifacts under
`arch_surgery/idf_probe/runs/a35/` stay untracked; summaries and the verdict are committed.
No run reads or writes anything under the main checkout except the frozen static export
(read-only) and committed reference records named explicitly in the report.

## 5. Mover classification (the joins, and the view-reconstruction rule)

Per traced verified run, per outer pass p ≥ 2, per recorded mover (continuous above-τ, moved
constant, discrete mismatch):

1. **Owning block** — from the a26 writeset `subsets` (V11 guarantees uniqueness; a mover
   outside every subset is itself a finding and is reported, not dropped).
2. **Writer node(s)** — from `node_writesets.json` (dynamic authority); **writer block** — from
   the run's own recorded schedule + hoisted tail. A mover whose writers are all tail or
   post-solve nodes cannot have been rewritten during a pass; if one appears, that contradiction
   is reported as an integrity finding.
3. **Earliest moving block** b_min(p) — minimum writer block over the movers of pass p under
   `BLOCK_ORDER`. The cause of the whole pass-p movement lives at b_min: every later block's
   movement is (potentially) downstream echo, so **the carrier is named at b_min**.
4. **View-reconstruction rule** (what changed in block b's visible inputs between its pass-(p−1)
   and pass-p executions, from end-of-pass trace deltas alone):
   - components owned by blocks **before** b: their pass-p movement (they are rewritten before
     b runs in pass p);
   - components owned by b or by blocks **after** b: their pass-(p−1) movement (b sees
     end-of-pass-(p−1) values in pass p) — for p = 2 this is the pass-1 census, which is why
     `FULL_FROM=1`.
   For b_min at pass 2 the earlier-block set is empty by construction, so its entire reconstructed
   input change is **later-or-own-block pass-1 movement**. The carrier candidates are the
   later-block-owned members; own-block members are the inner solve's own converged state (an
   own-entry-iterate dependence, if it were the only change, is reported as an intra-block
   path-dependence finding, not forced into (a)–(d)).
5. **Reader evidence** — `st_regression`: the frozen export's reader map for b_min's writer
   nodes, intersected with the candidate carrier components; `large_tokamak_nof`: the recorded
   DSM cross-module cell set + source confirmation of the shortlisted reads (`run()`-path
   discipline, traps T1/T7; file:line at the study commit).
6. **Named edge** = (carrier component, its writer node/block, the reading node/block, file:line
   of the read). The (a)/(b)/(c) split then follows §2's signatures.

## 6. Gates, each with teeth (protocol §12 — shown, never asserted)

| Gate | Binds | Criterion | Teeth (each must trip) |
|---|---|---|---|
| **G1 trace-inertness** | every traced number | one verified cold chain on `large_tokamak_nof` run twice, traced vs untraced: `node_calls_single_eval`, `outer_passes`, exit-audit residual hex and `objf` hex **all identical** | comparator fed +1 on the count, +1 on outer passes, 1 ULP on each hex — 4 perturbations, each must flip the verdict |
| **G2 entry-restore fidelity (`large_tokamak_nof`)** | every `--entry-state` run on the deck A36 did not smoke | FLAT relaunched from its **own** unperturbed exit snapshot: readback bit-exact (0 mismatches, 0 skipped), block sweeps = 1, audit ≤ the reference's own exit-audit residual | the snapshot hand-perturbed ×1.5 on one continuous, non-zero component outside `spec_keys_owned_by_x` must produce a **nonzero** audit AND > 1 sweep (A36's binding form; the audit-below-threshold subtlety is inherited and recorded) |
| **G3 parser integrity** | the mover tables and every classification | (i) chain check: every pass-2 mover's `before_hex` equals `Y1` (S3), pass-3 vs `Y2`; (ii) `scaled` recomputed from the hex pair and the spec scale must reproduce the recorded `scaled` for every scalar mover; (iii) **known mover**: `build.dz_tf_upper_lower_midplane` (A34 pin_gate's top mover) must appear among cold-entry pass-2 movers on `large_tokamak_nof` — a trace without it is broken, not a discovery | a **copy** of a real trace with one mover's `before_hex` flipped by 1 ULP must be **refused** by the analyzer (check (i) or (ii) fires); a copy of `Y1` with one component doctored must fail the chain check |
| **G4 reconciliation** | the cold `large_tokamak_nof` findings | the S2 verified cold chain must reproduce A34 pin_gate's structure: 3 outer passes and a sub-τ exit vs the FLAT point (exact hexes may differ — A34 ran A18-generation driver artifacts; the artifact generation is stated beside every number, trap T11) | a mismatch in outer-pass count or an above-τ exit is a **reported discrepancy**, never adjusted for |

A failed gate stops the dependent stage and is reported with its numbers. Nothing is retried
with different settings.

## 7. Decision tree (observed signatures → named carrier)

1. **Does the verified chain from the cold entry need > 1 outer pass with above-τ pass-2 movers,
   under a26 artifacts?** NO → the phenomenon does not reproduce under the V2-generation
   artifacts; that is the finding (A34's was an A18-artifact machinery gate) and the
   investigation reports it and stops. YES → 2.
2. **Restart identity (S3).** HOLDS on every comparison → the carrier lives in the coupling
   state; (d) is excluded as the carrier of THIS transient (remaining scope: hidden state that
   never expresses above τ, unmeasurable by construction and stated as such) → 3. FAILS → tail
   confounder check (mismatching components' writers vs tail read evidence; hoist-off rerun if
   needed) → survives → **(d), named to the model** by writer census, with the mismatching
   components and hexes; does not survive (mismatch fully explained by tail writes feeding
   back) → that tail feedback **is itself a named backward edge** → 3 with the edge in hand.
3. **Earliest-block attribution (§5).** Candidate carrier components named at b_min. First the
   **lagged-edge census verdict** (§2a): movers whose reconstructed input change is confined to
   later-block pass-1 movement are demonstrated cross-block iteration-carried consumers —
   **(c-lag)** at block granularity — and the δ-scaling sub-discriminator (cold vs δ = 0.10 vs
   δ = 0.05 vs the cited zero-point) splits state-carried from seed-type staleness per §2a.
   **Then the §2b primary dichotomy before any defect hunt:** is the named edge in the
   enumerated KNOWN-CUT set (export `data_interface` × executed schedule)? YES → primary label
   **KNOWN-CUT**, no artifact wrong anywhere; the finding is the edge's underestimated
   displaced-state magnitude, with its liveness class annotated. NO → the pipeline is
   implicated; per-candidate reader evidence assigns MISSING-EDGE / MISPLACED-EDGE /
   STATE-DEPENDENT / NON-IDEMPOTENT:
   - read present in the frozen export (st) / recorded DSM cells (nof) → **(b)** if the DSM's
     own order also puts the writer after the reader (a genuine back edge, dead near fixed
     points — confirm liveness pattern in source: branch or V3-pattern value); **(c-order)** if
     the DSM's topological order puts the writer BEFORE the reader and only our block assignment
     reverses them (a forward edge crossed backward by the schedule);
   - read absent from the export/cells but confirmed in source on the `run()` path → **(a)**,
     with the file:line and the reason static analysis missed it if identifiable (aliasing,
     getattr, branch);
   - no read confirmable in source for any candidate → mixed-signature account (§8).
4. **Flat symmetry (S4)** is reported alongside whichever verdict: the same families contracting
   in the flat loop corroborates a coupling-structure carrier ((a)/(b)); their absence from the
   flat trace corroborates a schedule-specific one ((c)/(d)).

## 8. Pre-declared failure paths (what is reported if no clean verdict emerges)

- **A run crashes / times out / refuses:** a taxonomy row with the traceback, reachable from the
  committed entry point; the investigation proceeds on the remaining runs; the affected
  deck/entry cell is reported as not measured. The displaced-entry seed falls back 1 → 2 once,
  reported.
- **The verified chain from the displaced entry hits `OUTER_CAP`:** a result (the transient does
  not contract under the schedule there); passes 2..cap are still traced and classified.
- **Mixed signatures** (e.g. restart identity holds but no changed later-block input can be
  named for b_min at trace resolution): the honest account — every mover classified as far as
  the evidence goes, the specific gap named (movement carried below τ / outside the spec'd
  view), and the discriminating follow-up instrument described (an env-switched per-pass
  full-state dump in the driver — **proposed, not built**; driver scope would need its own
  neutrality gate).
- **Contradictory signatures** (restart mismatch AND a named backward edge): both mechanisms
  reported as live, each with its components and evidence; no forced single verdict.
- **A34's known mover absent under a26 artifacts (G3 tooth (iii) fires as FAIL):** reported as a
  generation-dependence finding; the classification proceeds on the movers that are present.

## 9. Protocol notes

- Every published number comes from executing `a35_cold_census.py` (stages: `refs`, `gates`,
  `trace`, `restarts`, `flatctl`, `analyze`; failure paths reachable from the same entry
  point), committed before the numbers (protocol §15).
- Acceptance quantities are counts, names and bit-exact hex floats; wall clock appears nowhere
  as evidence (trap T5).
- Concurrency: at most **one** PROCESS subprocess at any time (the V2 campaign owns the
  machine's workers); everything serial; no background PROCESS runs.
- The main checkout is read-only for this task; its running campaign's `runs/` are never
  touched; the frozen static export is read from it read-only with its sha recorded.
- Cross-study handoffs: none without a demonstrated defect (variable, file:line at the study
  commit, run evidence — V14 follow-up 3's standing rule); trap T9 forbids reading the sibling
  repository's live outputs.
- Deliverable 2 is [`arch_surgery/docs/reports/A35_cold_census.md`](../reports/A35_cold_census.md):
  the carrier named with component, file:line at the study commit and run evidence, or the
  honest mixed-signature account with what would discriminate further.
