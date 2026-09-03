# A34 (phase-a-instruments) — trust mode, burn-time pin, single-MDA-eval: built, gated; the pin equivalence gate FAILS from a cold entry, and the failure is localised to the skipped outer pass, not the pin

> **Document status** — **CURRENT · TASK REPORT, open.** Written by task A34
> (phase-a-instruments), 2026-09-03, on branch `A34-phase-a-instruments`, branched from
> `architecture_surgery` at `90bd0d9b`, experiment base commit `c0ae5b28`. Archived to
> `deprecated/` when the task merges and authoritative there (trap T3). Nothing here is merged;
> nothing is pushed.

| | |
|---|---|
| **Task** | The three remaining V2 instrumentation gaps (`EXPERIMENT_PLAN.md` Appendix A items 2/3; `v2_config.INSTRUMENTATION`): **(i)** trust mode — env-switched no-outer-loop for `per_module` block solves; **(ii)** pin instrument — the burn-time coupling held at an env-supplied value through a feed-forward block solve; **(iii)** single-MDA-eval mode — one `call_models` at a coupling-state-perturbed point, no optimiser, counts + uncharged exit audit |
| **Result** | All three built, env-switched, byte-neutral when unset (**gated**, teeth shown, not asserted). Gates: trust neutrality **PASS 3/3 bit-exact**, trust demo **PASS** (`outer_pass_hist` {1: 1170}), single-eval **PASS 4/4 bit-exact** against A28's control call 1, perturbation cross-arm identity **PASS** (799/799 rows bit-identical), pin refusals **PASS** (both fire). **The plan-§3 pin equivalence gate FAILS as bound** — cross-state residual 1.459e-2, 243/840 components above τ — and its in-stage verified-outer control **localises the cause**: the same pinned chain with the outer loop ON reproduces the FLAT fixed point at 1.53e-8 (0 above τ). One schedule pass from a **cold entry** does not reach the joint fixed point; the pin is sound |
| **Script** | [`arch_surgery/idf_probe/a34_instruments.py`](../../idf_probe/a34_instruments.py) — stages `trust_gate`, `trust_demo`, `evalone_gate`, `perturb_demo`, `pin_gate`, `pin_refusals`; plus the new runner [`v2_eval_one.py`](../../idf_probe/v2_eval_one.py). Committed at **`048c3aa3`** before any published number; every run record stamps `tree_git_head 048c3aa3…, dirty False` |
| **Runs** | 9 fresh-subprocess PROCESS runs from the committed clean tree (2 full optimisations, 6 single evals, 1 deliberate refusal) + 1 import-refusal subprocess + 1 lifted-deck derivation. 8/8 non-refusal runs `status: ok`; the refusal is `status: crashed` by design and named below |
| **Environment** | `PROCESS_surgery_env`; `PYTHONPATH` pinned to this worktree per subprocess; exact tree asserted in-process (traps T6/T10) |
| **Date** | 2026-09-03 |

---

## 1. What was built (env names, file:line at `048c3aa3`)

### (i) Trust mode — `PROCESS_ARCH_OUTER=trust`

With `PROCESS_ARCH_MODULE_SOLVE=per_module`, the block schedule runs **exactly once**: each
iterated block's inner solve converges at its inner tau as now, the feed-forward tail runs once
as now, and the outer joint predicate is **never evaluated** — no outer pass 2, no verification
receipt, `outer_residual_trace` empty. `outer_pass_hist` records `{1: n}`, so any tally can see
the mode. Unset ⇒ `verify`, the arm exactly as A25 built and A28/A32 measured it.

- `process/core/solver/module_solve.py:266-297` — env parse (`OUTER_MODE`, `TRUST_OUTER`);
  unrecognised value, `trust` with module-solve off, and `trust` with `flat_state` are all
  **import-time errors** (a knob that silently does nothing is a mislabelled arm; `flat_state`'s
  single-block guard already makes its inner test the joint test).
- `process/core/caller.py:905-918` — the one guarded break in `_call_models_by_module`, placed
  beside the A26 single-block guard. With the variable unset this is one module-attribute read
  per outer pass, and that neutrality is **gated** (§2), not asserted.

### (ii) Pin instrument — `PROCESS_ARCH_PIN_BURN_TIME=<float | C99 hex float>`

The burn-time coupling held at the supplied value — the lifted architecture's per-call
structure without an optimiser (plan §3: within one evaluation the optimiser holds the lifted
variable fixed; with no optimiser, the env is the owner). The ownership chain, each link
checked rather than trusted:

1. **The lift is required** (`process/core/solver/subsolve.py:154-163`): pin without
   `PROCESS_ARCH_LIFT=burn_time` is an import-time error, because the lift is what makes
   `Pulse.run`'s burn-time write the identity (`subsolve` returns the data-structure value).
   Without it the model would overwrite the pin on the first sweep.
2. **Fixed at initialisation** (`process/core/caller.py:642-643, 645-673`,
   `Caller._apply_burn_time_pin`): the value is written into `times.t_plant_pulse_burn` when
   the `Caller` is constructed, and a deck naming `ixc = 178` (the lifted burn time,
   `subsolve.BURN_TIME_IXC`, `subsolve.py:135`) is **refused** — the design-vector injection at
   the head of every sweep would silently overwrite the pin; two owners is a refusal, not a
   race. Pin chains run on the **original** deck.
3. **Tripwired, never re-pinned** (`process/core/caller.py:1393-1398`,
   `subsolve.assert_burn_time_pinned`, `subsolve.py:166-181`): at the end of every model sweep
   the value is bit-compared to the pin and any change raises, naming both hex values.
   A check rather than a re-pin, deliberately — re-forcing each sweep would mask the writer.
4. **Stamped**: `arch_pin_burn_time` / `_hex` / `arch_pin_enabled` in every `metrics.json`
   (`run_one.py:321-333`, `v2_eval_one.py`), plus `pin_intact_at_exit` in single-eval records.
   The env accepts `float.hex()` output so a measured value round-trips with zero loss.

### (iii) Single-MDA-eval mode — `arch_surgery/idf_probe/v2_eval_one.py`

Harness-side (no driver change): initialise the deck **exactly as a control run does**
(`SingleRun.__init__` + `load_iteration_variables` + `load_scaled_bounds` — everything a
control optimisation executes before its first function evaluation, and nothing more), apply an
optional seeded ±δ perturbation to the **coupling-state initial values** keyed on **component
NAME** from the a26 ystate spec (`sha256("a34|<seed>|<name>")`, `--delta`/`--seed` on the CLI;
seed 0 leaves the deck point unperturbed, the house convention), execute **exactly one**
`Caller.call_models` under whatever architecture the environment selects, record the standard
count fields for that single call, write the full exit state as exact hex (`y_exit.json`), take
the **uncharged** a26-style exit audit (fresh `Caller`, nothing hoisted, no block filter, node
calls counted and never charged), stop. No VMCON object exists in the process. Failure paths
(`unconverged` / `crashed` / the pin refusal) are recorded rows with tracebacks, not retries.

`run_one.py` additionally records `arch_outer_env`/`arch_outer_mode` (`run_one.py:364-372`) so
full-run records carry the resolved policy, read from the module, never the environment.

## 2. Gate: switch-neutrality (`trust_gate`) — PASS, 3/3 bit-exact, 3/3 teeth

With both new variables unset, on the driver carrying both capabilities, the a26-spec `A1′`
`st_regression` start000 run (A32's exact campaign recipe) against A32's recorded start000
(`runs/a32/campaign/A1p/start000/metrics.json`, main checkout, read-only; comparator =
`a31_drift_probe.gate_extract/gate_compare/gate_teeth`):

| field | A32's record | this run |
|---|---|---|
| `node_calls_solve_phase` | 37 312 | **identical** |
| `outer_pass_hist` | {1: 9, 2: 560, 3: 1} | **identical** |
| `norm_objf` (hex) | `-0x1.096acf3342e04p+4` | **identical** |

3 of 3 fields equal, 3 of 3 teeth trip (count+1, one histogram bucket+1, one ULP on the float —
each flips the comparison). `runs/a34/trust_gate/gate.json`. Everything this task added to the
default path — the trust check, the pin guards, the recording fields — is therefore
byte-neutral on the full campaign path, shown not argued.

## 3. Demo: trust mode end-to-end (`trust_demo`) — PASS; differences beside A32, not judged

Same configuration plus `PROCESS_ARCH_OUTER=trust`: runs to completion, **`outer_pass_hist`
= {1: 1170}** — all 1 170 `call_models` at exactly one outer pass, teeth on the all-ones check
2/2 (an injected 2-pass bucket, and a relabelled histogram, each trip). Reported **beside**
A32's verified-arm start000, differences reported, never judged (matched-accuracy comparison is
V2's job on V2's pre-declared rules):

| quantity | trust (this run) | A32 verified arm |
|---|---|---|
| `norm_objf` (hex) | `-0x1.096acf3360a2fp+4` | `-0x1.096acf3342e04p+4` (differ; relative ≈ 4e-9) |
| uncharged exit-audit residual max (hex) | `0x0.0p+0` | `0x0.0p+0` |
| `node_calls_solve_phase` | 54 366 | 37 312 |
| VMCON iterations | 20 | 10 |
| `ifail` | 1 (feasible) | 1 (feasible) |

Both exit audits are `run_one`'s **post-run** audit on the A18 ruler, which `run_one.py`'s own
help records as reading at or near zero for every arm (the output path re-converges the state
to MFILE idempotence); it is reported because the task brief names it, with that caveat. The
per-call accuracy difference that matters is measured where the arm stops — §5's single-eval
audits. The 20-vs-10 iteration count and 54 366-vs-37 312 node calls on this **one start** are
context only (N = 1, no acceptance applied): what the optimiser does with a cheaper, looser
per-call answer is exactly Phase B's question.

`runs/a34/trust_demo/demo.json`.

## 4. Gate: single-eval vs the control's call 1 (`evalone_gate`) — PASS, 4/4 bit-exact, 4/4 teeth

The FLAT arm's single eval at the **unperturbed** `st_regression` deck point, against the first
solve-phase call of A28's recorded control optimisation
(`runs/a28/h5_audit1/st_regression/A0p/start000`, whose audit-at-call-1 machinery stopped a
real optimisation at the return of `call_models` #1) — same A18 ruler the reference was
measured with:

| field | A28's record | this run |
|---|---|---|
| node calls of call 1 | 147 | **identical** |
| audit node calls | 21 | **identical** |
| audit residual max (hex) | `0x1.c22fb514702ddp-29` | **identical** |
| audit argmax | `superconducting_tfcoil.a_tf_plasma_case` | **identical** |

4/4 fields, 4/4 teeth (each field perturbed by the smallest registrable amount trips).
**What this comparison is and is not:** bit-identity of a one-sweep audit residual over the
full 827-component coupling state, plus both node-call counts and the argmax, is the strongest
agreement the recorded reference supports; the reference does **not** record `objf`/`conf` at
call 1, so those are not compared. `runs/a34/evalone_gate/gate.json`.

## 5. Demo: the perturbation stream (`perturb_demo`) — PASS on cross-arm identity, with a census the plan must see

FLAT and BLOCKS+trust at (δ = 0.10, seed = 3) on `st_regression` (the one deck whose
a26-generation artifacts are complete): the recorded per-component perturbations are
**bit-identical across the arms — 799 of 799 rows** (factor, before/after hex), which is the
name-keyed pairing property Phase A rests on. The BLOCKS+trust chain ran its single call at
exactly 1 outer pass with an empty outer-residual trace. `runs/a34/perturb_demo/demo.json`.

**The census (trap T11 — the condition that limits the number, in the same sentence):** of 799
continuous components, only **32 moved**; **767 are identically zero at cold initialisation**,
so a *multiplicative* ±δ stream leaves them unmoved (0 × factor = 0), and 28 more are
discrete/unviewable and untouched by design. The stream demonstrably reaches the trajectory —
the perturbed FLAT run's exit state differs from the unperturbed run's on **426 of 827**
components (both exits τ-converged; among the 401 bit-identical is the audit-argmax chain,
which is why both runs report the same audit-max hex) — but a Phase A that wants the *whole*
coupling state perturbed at a cold entry cannot get it multiplicatively. Design decision for
the plan: §8, item (c).

Context, reported not judged: at this perturbed entry the trust chain's exit sits
1.79e-2 (scaled, a26 ruler; 124 components ≥ τ, argmax `build.dr_shld_vv_gap_outboard`) from
the FLAT exit — the same phenomenon §6 measures on the pulsed deck, so it is **not**
pulsed-specific and not the pin.

## 6. Gate: pin equivalence (`pin_gate`) — **FAIL as bound**, and the failure is localised

Plan §3: *"one BLOCKS run pinned at the FLAT arm's converged coupling value must reproduce the
FLAT fixed point within the audit's resolution."* On `large_tokamak_nof`, **A18-generation
artifacts** (the pulsed decks' a26 write sets are A33's deliverable — this is a **machinery
gate**, to be re-run under the a26 pair when A33 lands), all three runs single-eval at the
unperturbed deck point, committed script, teeth 2/2 (a 3τ·s bump on a continuous component and
a discrete flip each force FAIL):

| run | node calls | outer passes | own one-more-sweep audit (hex) | cross-state residual vs FLAT |
|---|---|---|---|---|
| FLAT (`flat_state`) | 126 | — | `0x1.f76312b8779a6p-27` (≈ 1.5e-8) | — |
| BLOCKS + pin + **trust** | 68 | 1 | `0x1.de05b6285d3f4p-7` (≈ 1.46e-2) | **1.459e-2, 243/840 ≥ τ** — the gate quantity, **FAIL** (criterion: categorically clean AND < τ = 1e-6) |
| BLOCKS + pin + **verified** (control) | 139 | 3 | `0x0.0p+0` | **1.53e-8, 0/840 ≥ τ** — at the FLAT point |

- **The pin is sound.** In both pinned chains: pin applied at initialisation, tripwire silent,
  `pin_intact_at_exit` true, and `times.t_plant_pulse_burn` **bit-identical** to the FLAT run's
  converged value (passed as `0x1.41043caef8d92p+11`, no decimal round trip). The verified
  control — pin ON, only the outer policy differing — lands on the FLAT fixed point at 1.53e-8,
  which is **below τ and below both τ-grade arms' expected resolution**, with zero components
  above τ. Whatever fails, it is not the pin.
- **What fails is one-pass trust from a cold entry.** The trust chain's own one-more-sweep
  audit (1.46e-2) equals its distance to the FLAT point (1.459e-2) with the same argmax: its
  exit is simply not at the joint fixed point, and one more sweep moves it toward it. The
  verified control needed **3 outer passes** from this entry — corroborated by A28's record,
  where `large_tokamak_nof` `A1′`'s outer-pass histogram is {1: 7, 2: 652, **3: 1**} and the
  3-pass call is the cold first call. The skipped pass does genuine convergence work at cold
  entries.
- **Who moves:** `build.dz_tf_upper_lower_midplane` (1.46e-2), `build.dr_shld_vv_gap_outboard`
  (1.28e-2), `pf_coil.ssq0` (1.23e-2), then `costs.*`/`buildings.*` downstream — data flowing
  **backward into M2's `build`** from later-block state that is stale (cold) during pass 1.
  The same `build.*` family leads the k = 0 observation in §5. Which specific reads carry it is
  a follow-up measurement (A31's trace instrument fits), not asserted here.
- The "at the instrument's noise floor" reading (cross ≤ max of the two own-audit residuals) is
  reported unbound and is **degenerate here**: the trust chain's own audit *is* essentially its
  distance to the fixed point, so that reading cannot fail for an unconverged chain and must
  not become the binding criterion.

**A failed gate is a result.** Nothing was tuned or retried. What this means for V2 is a plan
decision, not this task's: Phase A's BLOCKS arm as declared (no outer loop) delivers, from a
cold entry at τ = 1e-6, an exit state ~1.5e-2 (scaled) short of the joint fixed point on both
decks measured, and its per-call saving (68 vs 126 node calls here) is bought at exactly that
accuracy difference — which is what the plan's matched-accuracy machinery (§3 accuracy rule,
fallback A26 fix 1) exists to price. `runs/a34/pin_gate/gate.json`.

## 7. Demo: the pin's refusal paths (`pin_refusals`) — PASS, both refuse

- Pin without lift: import-time `RuntimeError` naming both variables (subprocess rc 1).
- Pin on the derived lifted deck (`ixc = 178`; deck derived by `a25_variant_deck.py` the
  `run_a28 decks` way): `Caller` refusal naming the pin, ixc 178 and the injection mechanism;
  recorded as a `crashed` taxonomy row with the traceback, reachable from the committed entry
  point. `runs/a34/pin_refusals/refusals.json`.

## 8. Design decisions the plan should record

(a) **Env names fixed**: `PROCESS_ARCH_OUTER` ∈ {`verify` (default), `trust`};
`PROCESS_ARCH_PIN_BURN_TIME=<float | C99 hex float>`. `v2_config.INSTRUMENTATION` entries
`trust_mode`, `pin`, `single_mda_eval` can flip to available at merge (that file lives in the
main checkout, untracked — not touched by this task); `single_mda_eval`'s entry point is
`arch_surgery/idf_probe/v2_eval_one.py`.

(b) **Trust is a `per_module` policy**: `trust` with module-solve off or with `flat_state` is
an import-time error, not a silent no-op.

(c) **The coupling-state perturbation stream is multiplicative and mostly inert at a cold
initialisation** (§5: 767 of 799 continuous components are identically zero before any model
runs). If Phase A intends the whole state perturbed, the plan must choose: an additive stream
scaled by the spec's own `s_i` (δ·s_i·u), or perturbation of a warm state, or accept the
32-component stream as-is. Built as multiplicative to mirror D15's design-vector convention;
the instrument records the ineffective-component census loudly either way. **Not decided here.**

(d) **Pin chains run on the original deck**; the lifted deck (ixc 178) is refused by design
(two owners). The pin requires the lift; both are import-time-checked.

(e) **The equivalence gate's binding criterion** was fixed before the runs as *categorically
clean AND cross-max < τ* under the audit ruler, with the noise-floor reading reported unbound
(and shown degenerate for an unconverged chain, §6). If the plan wants a different binding —
e.g. the verified-outer chain as the equivalence subject, with trust's gap measured separately
— that is an amendment to declare there.

(f) **Cold-entry caveat on trust mode**: the instrument does exactly what the plan's Appendix A
item 3 specifies, and §6 measures what that specification delivers from a cold entry. Whether
Phase A's protocol treats the first (cold) call specially — as A28's data already treats the
cold call as the known 3-pass outlier — is a plan decision.

## 9. Provenance and reproduction

Every run: fresh subprocess, own working directory, `PYTHONPATH` pinned to this worktree, exact
tree asserted in-process; every record stamps `tree_git_head 048c3aa3…, dirty False`. Every
published quantity is a count, a name, or a bit-exact hex float; wall clock appears nowhere as
evidence. References read from the main checkout, read-only: A32's `campaign/A1p/start000`
record, A28's `h5_audit1/st_regression/A0p/start000` record. Bulk run artifacts under
`runs/a34/` stay untracked; the committed script regenerates them.

```
cd arch_surgery/idf_probe
python a34_instruments.py trust_gate     # §2  (PASS 3/3 + teeth 3/3)
python a34_instruments.py trust_demo     # §3  (PASS, hist {1: 1170})
python a34_instruments.py evalone_gate   # §4  (PASS 4/4 + teeth 4/4)
python a34_instruments.py perturb_demo   # §5  (PASS 799/799 identical)
python a34_instruments.py pin_gate       # §6  (FAIL as bound; control at 1.53e-8)
python a34_instruments.py pin_refusals   # §7  (PASS, both refuse)
```

Which stage produced which figure: §2 — `runs/a34/trust_gate/gate.json`; §3 —
`trust_demo/demo.json`; §4 — `evalone_gate/gate.json`; §5 — `perturb_demo/demo.json` plus the
per-run `perturbation.json`/`y_exit.json`; §6 — `pin_gate/gate.json` (three run directories
beneath it); §7 — `pin_refusals/refusals.json`.

## 10. Change log

- 2026-09-03 — task opened; mandatory reads; design settled (pin-requires-lift ownership
  model; trust as a `per_module` policy; harness-side single-eval runner).
- 2026-09-03 — instruments implemented and committed at `048c3aa3` **before any published
  number**; development smokes discarded.
- 2026-09-03 — full pipeline executed from the committed clean tree: 5 stages PASS with teeth,
  the pin equivalence gate **FAIL as bound** with its verified-outer control passing at
  1.53e-8 — cause localised to the skipped outer pass's genuine convergence work at cold
  entries, not the pin. Report written.
