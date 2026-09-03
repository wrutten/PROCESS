# A36 (phase-a-campaign) — Phase A executable under the warm-entry design: `--entry-state` built and gated, the warm equivalence gate PASSES where A34's cold pin gate failed, campaign and tally implemented; smoke complete on `st_regression`

> **Document status** — **CURRENT · TASK REPORT, open.** Written by task A36
> (phase-a-campaign), 2026-09-03, on branch `A36-phase-a-campaign`, branched from
> `architecture_surgery` at `c2458546`, experiment base commit `c0ae5b28`. Archived to
> `deprecated/` when the task merges and authoritative there (trap T3). Nothing here is merged;
> nothing is pushed.

| | |
|---|---|
| **Task** | Make Phase A executable under the **warm-entry design** (user decision 2026-09-03): (1) extend `v2_eval_one.py` with `--entry-state` — launch a single MDA eval from a previous run's exact-hex exit snapshot, seeded perturbation acting multiplicatively **around the warm state**; (2) implement `phase_a.py` `stage_campaign` / `stage_tally` (guarded stubs replaced, refusal discipline kept): per deck, A0 cold reference → extension gate → warm equivalence gate → seeds 1–25 both arms seed-paired → tally |
| **Result** | Both deliverables built and **gated with teeth** on `st_regression`. Extension gate **PASS 7/7 checks** (re-entered fixed point audits at `0x1.eae3a0e959de8p-34` ≈ 1.1e-10 against the pre-declared threshold `0x1.c22fb514702ddp-29` ≈ 3.3e-9, at exactly 1 block sweep / 21 node calls; teeth: a hand-perturbed snapshot produces a nonzero audit and 2 sweeps). **Warm equivalence gate PASS** — cross-state residual A1-vs-reference `0x1.c22fb514702ddp-29`, **0/827 above τ, categorically clean** — where A34's cold pin gate failed at 1.46e-2 (the warm entry removes exactly the cold-entry convergence work A34 localised). Smoke campaign 4/4 runs ok, entry pairing **2/2 seeds, 827/827 components bit-identical across arms**; tally carries every §3 field. At δ = 0.10 warm-perturbed entries the perturbation now reaches **751/805** continuous components (32/799 at a cold entry, A34 §5) — and A1's one-pass audits sit at ~0.24 scaled vs A0's ~5e-9, so the similarity criterion **fails at N = 2 smoke scale**; condition attached in §6 |
| **Script** | [`arch_surgery/MDA_partitioning_experiment_v2/phase_a.py`](../../MDA_partitioning_experiment_v2/phase_a.py) (stages `preflight` / `campaign` / `tally` / `smoke`) + the extended runner [`arch_surgery/idf_probe/v2_eval_one.py`](../../idf_probe/v2_eval_one.py). Committed at **`04f0fd49`** before any published number; every run record stamps `tree_git_head 04f0fd49…, dirty False` |
| **Runs** | 8 fresh-subprocess single-eval runs from the committed clean tree (1 cold reference, 3 gate runs incl. the deliberately doctored teeth run, 4 seed runs), all `status: ok`. All on `st_regression` (the smoke deck; artifacts complete, cheapest). No pulsed-deck run in this task — the campaign stage covers them on execution approval |
| **Environment** | `PROCESS_surgery_env`; `PYTHONPATH` pinned to this worktree per subprocess; exact tree asserted in-process (traps T6/T10); `runs/` untracked |
| **Date** | 2026-09-03 |

---

## 1. What was built (file:line at `04f0fd49`)

### (1) `v2_eval_one.py --entry-state` — the warm entry

- `v2_eval_one.py:188` `write_entry_state`: the snapshot's 827 components written into the
  data structure at initialisation, **before** the seeded perturbation
  (`v2_eval_one.py:499-574` fixes the order: restore → perturb → record). Float arrays whose
  dtype and shape match the live value are written element-wise **in place** (object identity
  preserved, as the perturbation multiplies in place); arrays that do not match are replaced
  via `setattr` and **named** in the record; a component serialised as a bare `repr` is
  skipped **by name**, loudly. After writing, the state is read back and compared
  **bit-for-bit** against the snapshot (`readback_bitexact`). Measured on the smoke runs:
  769 scalars, 36 arrays in place, 22 arrays replaced, 0 skipped, 0 readback mismatches.
- The sha refusal is **kept**: `restore_snapshot` (A34's loader, `v2_eval_one.py:224`)
  refuses a snapshot whose component spec sha differs from the run's `--perturb-spec`.
- `y_entry.json` (`v2_eval_one.py:574`): the exact post-restore, post-perturbation entry
  state, recorded per run — what the campaign's cross-arm pairing check compares.
- `--node-census` (`v2_eval_one.py:577-604, 645`): per-node evaluation counts for the
  measured single call, run_one's census pattern (counts only when `NODE_CALLS` moved, so
  suppressed post-solve nodes are not miscounted), **frozen before the uncharged audit**; the
  audit's own extra per-node counts recorded separately inside `exit_audit`.
- `lift_residual` (`v2_eval_one.py:684`): the pinned/lifted component's inconsistency at the
  exit state, measured by `burn_time_residual` — **the same pure function constraint 93
  evaluates** (`process/models/pulse.py:191`; imported, never modified — no `process/` edit
  in this task) — raw seconds as exact hex plus the spec-scaled magnitude; recorded for
  every arm; `inactive` with the reason on a k = 0 deck. Read before the audit sweep mutates
  the state.
- `spec_keys_owned_by_x` (`v2_eval_one.py:521`): which spec components the design-vector
  injection owns at the sweep head — now recorded unconditionally, so the entry-gate teeth
  can avoid hand-perturbing a component `x` would silently reset.

### (2) `phase_a.py` — campaign and tally

- `phase_a.py:140` `env_for_phase_a`: A0 = `flat_state` + a26 artifacts + τ, **no
  post-solve** (the flat architecture as shipped keeps those nodes in its loop, plan §3);
  A1 = the designed per-call structure (Phase B's B2): `build_after_physics` + `per_module`
  + `trust` + post-solve artifact + (pulsed) `LIFT=burn_time` and the pin. Composed locally
  from nothing with every switch cleared first (v2_runner's discipline; not borrowed from
  Phase B's `env_for`, whose arm names the orchestrator owns on the trunk). An unpinned A1
  on a pulsed deck is **refused**, not run.
- `phase_a.py:191` `run_eval_job` (fresh subprocess, exact tree asserted, resume semantics,
  `v2_*` stamps) and `phase_a.py:278` `run_pool` (W = 3, v2_runner's pool shape).
- `phase_a.py:346` `entry_gate` — §2 below; `phase_a.py:305` `_doctor_snapshot` builds the
  teeth's hand-perturbed snapshot.
- `phase_a.py:534` `warm_gate` — §3 below; teeth `phase_a.py:498` (A34 pin-gate comparators,
  unchanged in shape); cross-state residual via `a34_instruments.load_spec_offline` /
  `_cross_residual` — the identical instrument the superseded cold gate used.
- `phase_a.py:688` `deck_campaign`: reference → entry gate → warm gate → seeds; **any gate
  failure stops the campaign** (`phase_a.py:800` `_campaign`); per-seed pins for pulsed
  decks = the reference burn time × `perturb_factor(seed, "times.t_plant_pulse_burn", δ)` —
  bit-identical to what `apply_perturbation` computes in-process, passed as hex.
- `phase_a.py:657` `pairing_check`: cross-arm bit-identity of the full recorded entry state,
  every seed (the A34 799/799 check transposed to `y_entry.json`).
- `phase_a.py:893` `_tally` / `phase_a.py:1102` `stage_tally`: every §3 metric —
  per-node counts (summed over the identical-success set and per-run), the
  weighting-invariance bracket, the unweighted count ratio, audit similarity (median AND
  p90 within F = 10, quantile definitions declared in the record, full distributions kept),
  the lift residual distribution separate, the cold-start term, the failure taxonomy with
  denominators (every requested seed a row). Writes `runs/phase_a/tally.json` + a printed
  table.
- `phase_a.py:1111` `stage_smoke`: the full path on `st_regression`, seeds 1–2, under
  `runs/phase_a/smoke/`, stamped `machinery_smoke` — runnable while `EXECUTION_APPROVED` is
  False (the `phase_b.stage_smoke` pattern). `stage_campaign` (`phase_a.py:831`) **refuses**
  without approval; `run_experiment.py`'s call chain (`stage_campaign()` then
  `stage_tally()`) works unchanged. `v2_config.py`, `v2_runner.py`, `phase_b.py`,
  `run_experiment.py`, `EXPERIMENT_PLAN.md` untouched (concurrent trunk edits); the Phase A
  arm constants live locally in `phase_a.py:88-97`.

## 2. Gate: the `--entry-state` extension (`entry_gate`) — PASS 7/7 checks, teeth bind

A0 relaunched from its **own** unperturbed exit snapshot: the state is already the fixed
point, so one call under `flat_state` finds nothing to move. Thresholds **declared before the
gate run** (printed and recorded): audit ≤ the reference's own exit-audit residual
`0x1.c22fb514702ddp-29`; `block_sweeps == 1`; `node_calls == 21` (one sweep of the complete
in-loop set — the audit sweep's own count).

| quantity | reference (cold) | warm re-entry | verdict |
|---|---|---|---|
| entry state vs snapshot | — | **827/827 bit-identical** (readback and `y_entry.json` both; 0 skipped) | required, met |
| audit residual max (hex) | `0x1.c22fb514702ddp-29` (≈ 3.28e-9) | **`0x1.eae3a0e959de8p-34` (≈ 1.12e-10)** | ≤ threshold ✓ |
| block sweeps | 7 | **1** | == 1 ✓ |
| node calls of the call | 147 | **21** | == 21 ✓ |

The reference's 147 node calls / 7 sweeps and its audit hex agree with A28's recorded control
call 1 and A34's `evalone_gate` (147 / `0x1.c22fb514702ddp-29`) — the a26 ruler reproduces
the A18-ruler max on this deck because the argmax component
(`superconducting_tfcoil.a_tf_plasma_case`) and its scale are common to both artifacts.

**Teeth (a run, not a comparator):** the snapshot hand-perturbed on
`superconducting_tfcoil.a_tf_plasma_case` × 1.5 (`0x1.f1cce7ebabc80p-6` →
`0x1.7559adf0c0d60p-5`; chosen continuous, non-zero, outside `spec_keys_owned_by_x` so the
design-vector injection cannot silently erase it). Result: audit **nonzero**
(`0x1.1262727efeac2p-36`) and **2 block sweeps / 42 node calls** — both binding teeth trip.
Reported unbound: the doctored run's audit (≈ 1.6e-11) lands *below* the declared threshold,
because the flat arm re-converges the kicked component — which is why the binding teeth are
"nonzero audit AND more than minimal work", not "audit above threshold": re-convergence can
tighten an audit, it cannot fake a 1-sweep cost. `runs/phase_a/smoke/st_regression/entry_gate/gate.json`.

## 3. Gate: warm equivalence (`warm_gate`) — PASS; the cold-entry failure mode is gone

Supersedes A34's cold `pin_gate` (FAIL at cross 1.459e-2, cause localised to the skipped
outer pass's cold-entry convergence work, not the pin). Criterion **pre-declared** and
unchanged from A34 decision (e): categorically clean AND cross-state max < τ = 1e-6, under
the a26 audit ruler. On `st_regression` (k = 0: nothing pinned — the pin path is exercised
only on the pulsed decks, at campaign execution):

| quantity | value |
|---|---|
| A1 warm run | 17 node calls, outer passes **1**, every iterated block converged in **1 inner sweep** (M1/M2/PULSE/M3 = 1/1/1/1), own audit `0x1.2345ac5dd4c80p-32` ≈ 2.7e-10 |
| cross-state residual vs reference | **`0x1.c22fb514702ddp-29` ≈ 3.28e-9, 0/827 ≥ τ, categorically clean** (argmax `superconducting_tfcoil.a_tf_plasma_case`) |
| teeth | 2/2 trip (continuous +3τ·s bump; discrete flip) |
| verdict | **PASS** |

Context worth recording: the cross-state max is **bit-identical** to the reference's own
one-more-sweep audit residual, same argmax — from the warm entry, A1's exit differs from the
reference exit by exactly the amount one further flat sweep moves the reference itself. At
this instrument's resolution the two architectures' fixed points are indistinguishable here.
`runs/phase_a/smoke/st_regression/warm_gate/gate.json`.

## 4. The smoke campaign — pairing shown, perturbation reach measured

Seeds 1–2, δ = 0.10, both arms launched from the reference snapshot, 4/4 runs ok:

- **Pairing: 2/2 seeds, 827/827 components bit-identical across arms** (full
  `y_entry.json` compare, every seed — the A34 799/799 property, now on the entry state).
- **The warm entry does what it was adopted for** (A34 §5's design gap closed): at the warm
  state the multiplicative stream moves **751 of 805** continuous components (54 remain
  multiplicative zeros, 22 discrete untouched by design), against **32 of 799** at the cold
  deck initialisation. The only perturbed-and-reinjected key is
  `impurity_radiation.f_nd_impurity_electron_array` (recorded per run).
- Per run: A0 re-converges in 6 sweeps / 126 node calls from the perturbed warm entry
  (vs 7 / 147 cold); A1 does one outer pass at inner sweeps M1 = 4, M2 = 6, M3 = 3 (PULSE
  once) for 62 node calls, with the deck's committed post-solve set — exactly `pulse`,
  `vacuum`, `water_use`, `costs` — suppressed from the measured call and present in the
  audit's extra census, as designed.

## 5. The smoke tally — every §3 field, from the on-disk records

`runs/phase_a/smoke/tally.json`; printed table (**machinery smoke — not a measurement**):

```
deck                     gates        paired         A1/A0   bracket           similar  cold-start
st_regression            E:PASS W:PASS paired 2/2    0.4921  [0.000, 1.000]    False    147
```

- **Cold-start term**: 147 node calls / 7 sweeps — the once-per-run flat convergence at the
  cold deck point (this deck's cold entry only).
- **Unweighted count ratio** A1/A0 = 124/252 = **0.4921** over the 2 paired-ok seeds.
- **Weighting-invariance bracket** over nodes = **[0.0, 1.0]**: 0.0 is the suppressed
  post-solve set (`costs`, `pulse`, `vacuum`, `water_use` — 0 calls in A1's measured call,
  12 in A0's loop); 1.0 is the three M2 call sites that fire on this deck (`build`,
  `croco_sctfcoil`, `pfcoil`, 12 = 12). Per-node table (21 nodes, summed and per-run) in
  the JSON.
- **Audit similarity — FAILS at this scale**: A0 median 5.31e-9 / p90 7.60e-9; A1 median
  0.2412 / p90 0.2474 (hex values in the JSON); ratio ≈ 4.5e7 at the median, ≈ 3.3e7 at the
  p90, against F = 10. **Condition (trap T11, stated with the number): N = 2, one deck,
  machinery smoke — not a Phase A result.** But the direction is not noise: it is A34
  §5/§6's finding continued — one trust pass from a δ = 0.10-perturbed entry stops ~0.24
  scaled short of the joint fixed point now that the perturbation actually reaches 751
  components (A34 measured 1.8e-2 when it reached 32). If this holds at N = 25 the
  pre-declared similarity criterion fails on this deck and the plan's declared fallback —
  matched **measured** accuracy (A26 fix 1 / A28's envelope) — engages. That is the plan's
  decision rule doing its job, not something this task tunes around.
- **Lift residual**: `inactive` on this k = 0 deck, with the reason in the record; the
  distribution machinery (raw hex + spec-scaled, per arm, excluded from the similarity
  statistic) activates on the pulsed decks.
- **Failure taxonomy**: A0 {ok: 2} of 2, A1 {ok: 2} of 2, every requested seed a row.

## 6. What this smoke does and does not establish

Established: the extension reproduces a snapshot bit-for-bit at entry and is gated with
teeth; the warm equivalence gate passes where the cold one failed, with the cause A34
localised now absent; the campaign machinery (pairing, pins-from-the-stream plumbing,
refusal paths, tally fields) runs end to end from the committed entry point.

Not established: any Phase A number. N = 2, one deck, no pulsed deck executed, no pin
exercised in anger (the pin/lift/lift-residual path is composed and refusal-checked but its
first execution is the campaign's `large_tokamak_nof` warm gate). `EXECUTION_APPROVED` is
False and `stage_campaign` refuses accordingly; the smoke bypasses only the approval switch,
never a gate, and stamps every record `machinery_smoke`.

## 7. Provenance and reproduction

Every run: fresh subprocess, own working directory, `PYTHONPATH` pinned to this worktree,
exact tree asserted in-process; every record stamps `tree_git_head 04f0fd49…, dirty False`.
Every published quantity is a count, a name, or a bit-exact hex float; wall clock appears
nowhere as evidence (context: the reference's in-process solve took ~34 s wall, the warm
re-entry ~0.4 s — reported as JIT/warm-cache context only). Bulk artifacts under
`runs/phase_a/` stay untracked; the committed script regenerates them.

One audit-trail note: an intermediate session notification paraphrasing this smoke quoted
values (`0x1.19453808ca29cp-29`, `0x0.0p+0`, `0x1.a4d551011bf3fp-8`,
`0x1.34a19a231d95bp-21`) that appear in **no artifact**; the numbers above were re-read from
the on-disk records, which are internally consistent across the execution log, both gate
records, all eight run records and the tally (verified by grep and by diffing the two
independently captured copies of the execution log).

```
cd arch_surgery/MDA_partitioning_experiment_v2
python phase_a.py preflight   # ledger: READY
python phase_a.py smoke       # §2-§5 (8 runs, gates, pairing, tally)
python phase_a.py campaign    # REFUSES while EXECUTION_APPROVED is False
python phase_a.py tally       # refuses: no campaign records yet
```

Which stage produced which figure: §2 — `runs/phase_a/smoke/st_regression/entry_gate/gate.json`;
§3 — `warm_gate/gate.json`; §4 — the per-run `metrics.json` / `y_entry.json` /
`perturbation.json` and `pairing.json`; §5 — `runs/phase_a/smoke/tally.json`.

## 8. Change log

- 2026-09-03 — task opened; mandatory reads; design settled (restore-then-perturb order;
  entry-gate thresholds bound to the reference's own audit; warm gate keeps A34's criterion
  and comparator teeth; Phase A envs composed locally; lift residual = constraint 93's
  function evaluated harness-side).
- 2026-09-03 — both deliverables implemented and committed at `04f0fd49` **before any
  published number**.
- 2026-09-03 — smoke executed from the committed clean tree: extension gate PASS with
  teeth, warm equivalence gate PASS, pairing 2/2 × 827/827, tally complete; report written.
