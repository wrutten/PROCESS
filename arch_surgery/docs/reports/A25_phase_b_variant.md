> **Document status** — **OPEN · TASK REPORT**
> The task report for A25 (phase-b-variant), on branch `A25-phase-b-variant` at experiment base
> commit `c0ae5b28`. Not merged. Every number in it was measured in the isolated worktree
> `/home/wrutten/projects/PROCESS_surgery_worktrees/A25-phase-b-variant`, in
> `PROCESS_surgery_env`, with the **exact** tree asserted in every measurement subprocess (trap
> T6). Archive to `reports/deprecated/` at merge; folder position will then record lifecycle,
> not validity (trap T3).

# A25 (phase-b-variant) — Phase B implemented, gated and run

| | |
|---|---|
| **Task** | A25 (phase-b-variant) — **A4** (the burn-time lift) + **A5 / F10** (the per-module solvers), bundled because A19 established they are not separable, plus the equivalence gate and the **H5** multi-start campaign |
| **Branch** | `A25-phase-b-variant`, worktree `/home/wrutten/projects/PROCESS_surgery_worktrees/A25-phase-b-variant` |
| **Base** | `83e18d15` on `architecture_surgery`; experiment base commit `c0ae5b28` |
| **Governed by** | **D5**/**D11** (physics frozen; model edits need approval), **D6** (correctness never on iteration variables), **D14(b)/(c)** (the approved `pulse.py` extraction; the baseline is PROCESS as it is), **D15(a)–(d)** (calibrated δ, hoist inside the variant, objf-mismatch is a robustness finding, a failed module solve raises), **D16** (bundle; autonomous go-ahead on a passing gate) |
| **Environment** | `PROCESS_surgery_env` (`/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python`); `PYTHONPATH` pinned to this worktree per subprocess |
| **Date** | 2026-09-01 |

---

## 1. Verdict

**The equivalence gate PASSES on all four decks, so H5 was run. The proposed architecture does not
win. Per deck, plainly:**

| deck | wins / loses / inconclusive | cost, paired median | robustness, paired |
|---|---|---|---|
| `large_tokamak_nof` | **loses**, narrowly | **+2.0 %** (q1–q3 1.018–1.022, 19 of 22 starts dearer) | **identical** — 22 both, 0 only-baseline, 0 only-variant |
| `low_aspect_ratio_DEMO` | **inconclusive** | −22.8 %, but over **8** starts with ratios from 0.24 to 3.26 | variant loses **1** start of 25 |
| `st_regression` *(control: modules + hoist, **no lift**, k = 0)* | **wins on cost, loses on robustness** | **−5.1 %**, on **20 of 20** kept starts | variant loses **2** starts of 25 — **and both are the hoist's, not the partition's** |
| `large_tokamak_eval` | **loses** | **+16.8 %**, on 15 of 15 | variant loses **10** starts of 25 |

**Robustness outranks cost, and by the plan's pre-declared outcome table this is H5 failing**: the
variant's success rate is worse on three of four decks, and it never solves a start the baseline
cannot. That is the headline regardless of cost.

**Six things qualify it, and every one of them is measured.**

1. **The whole robustness deficit is one data-structure field.** All 13 `ModuleSolveFailure`s in
   300 runs name `current_drive.eta_cd_dimensionless_hcd_primary`, which goes `0.0 → NaN` inside
   M1. Phase A's predicate scores a non-finite component `inf` and refuses to converge;
   PROCESS's own `check_agreement` is `np.allclose(..., equal_nan=True)` and returns **`True`** for
   a NaN state against itself — measured, §6.2. At those starts the baseline reports `ifail = 1`
   over a state containing a NaN. The one deck where Phase A's harvest happened to catch that field
   non-finite categorises it `nan_in_harvest`, excludes it, and has **zero** extra failures.
2. **H5's own risk did not materialise.** The paired VMCON major-iteration ratio is exactly
   **1.000 at q1, median and q3** on `large_tokamak_nof` and on `st_regression`, and **0.806**
   (in the variant's favour) on `low_aspect_ratio_DEMO`. Adding a design variable and a consistency
   constraint did not measurably disturb the SQP search. Nothing bounded this in advance.
3. **§4.1a's ≈ −26 % expectation is not confirmed, and the measurement is the finding.** Measured
   against the incumbent driver, the loop-side saving is **−2.6 %** on `large_tokamak_nof` and
   **−5.9 %** on `st_regression`, an order of magnitude below A22's −29 %. The gap is exactly the
   one §4.1a's own condition 1 named: A22 measured the block arm *against itself*, not against
   today's driver.
4. **The headline is "the proposed architecture", never "the partition's benefit."** The hoist is
   inside the variant (D15(b)) and its separable share was measured **inside** the variant rather
   than quoted from A13: **−2.92 / −2.88 / −2.95 / −1.63 %**, against A13's flat-arm
   −6.56 / −6.76 / −6.64 / −2.63 %. **Inside this architecture the hoist is worth less than half
   what it is worth in the flat one.** On `large_tokamak_nof`, +5.09 % without the hoist, −2.9 pp
   from it, **+2.02 %** combined.
5. **On `st_regression` the partition is robustness-neutral and the hoist is not.** The arm without
   the hoist has an **identical success set to the baseline** (24 / 25, 0 asymmetric); adding the
   hoist costs 2 starts. A13's single-point bit-identity gate could not have seen this — it takes a
   multi-start.
6. **`st_regression` is the control, not a fourth replicate.** It has no burn-time coupler
   (`i_pulsed_plant = 0`; its measured `PULSE` write set is **empty**), so it runs modules + hoist
   **without** the lift, with the design vector unchanged at 14. That is why its −5.1 % carries no
   dimension penalty, and why it is the one deck where the loop-side saving is isolated.

**Issue I-12 did not recur.** Zero degenerate entries in 300 runs, over 22/22, 23/20, 25/25 and
25/15 completed runs per deck. The perturbed multi-starts were expected to visit infeasible entry
states by design; on these decks they did not visit ones with non-positive net electric power.

### 1.1 The gate found three defects in this task's own work before it passed

Protocol §12 has caught a defect in the agent's own harness on three consecutive tasks. It caught
three here, and one of them would have produced a false headline (§3):

- the **whole-`y` inner test**, which killed the first variant run at the cap after 40 node calls;
- the **`FF` block of no-ops**, 789 block sweeps that executed nothing;
- **`icc = 93` appended at the end of the deck**, which made the burn-time *equality* the
  twenty-fourth **inequality**. That variant returned `ifail = 1`, an objective that looked right,
  and appeared **38 % cheaper than the baseline**. Nothing forced the burn time onto its own
  consistency manifold. Had it been reported it would have been the headline of this task and it
  would have been false.

A fourth was found in the analysis rather than the gate: the I-12 census counted crashed runs'
partial MFILEs as degenerate entries and reported 10 on a deck that has none (§6.3).

### 1.2 What this does not say

- Nothing here claims the lift **removes an inner solver**. `Pulse.run` assigns a closed-form
  expression (A24, plan §4.1b); what the lift buys is a change of loop topology.
- Nothing here rests on a timing. Every acceptance and cost quantity is a count or a
  bit-comparison. The variant's wall clock is roughly twice the baseline's on `large_tokamak_nof`
  and that figure is not used as evidence anywhere — it is dominated by an instrument-grade
  coupling-state read that a production implementation would not perform (§8).
- The result is four decks, one starting-point distribution, one δ, one optimiser and one
  tolerance rung. It does not transfer.

---

## 2. What was built

### 2.1 VP4 — the per-module solvers (A5 / F10)

Two files, both inside `CLAUDE.md`'s default-permitted surface.

| File | Role |
|---|---|
| `process/core/solver/module_solve.py` (new) | the arm (`PROCESS_ARCH_MODULE_SOLVE`), the tolerance (`PROCESS_ARCH_TAU`), the two committed artifacts it needs (`PROCESS_ARCH_YSTATE`, `PROCESS_ARCH_WRITESET`), the caps, the failure exception, and the loader that rebuilds **Phase A's** `YSpec` from the committed artifact |
| `process/core/caller.py` | the schedule and the node filter — properties of *this* call sequence rather than of the predicate |

**The predicate is Phase A's code, not a reimplementation of it.** `module_solve` loads
`arch_surgery/fixedpoint/ystate.py` by path (lazily, on the VP4-on path only) and uses its
`YSpec.residual` / `Residual.converged` unchanged. Decision D14(c) requires the variant to be
tested by the rule Phase A measured; two implementations of one predicate is how they drift.
Reaching outside `process/` for it is the same move `caller.NODE_MAP_PATH` already makes for the
hoist's node map, and it is an autonomous decision with a stated reversal (§9, AD2).

**The schedule** is Phase A's, unchanged: `M1 → M2 → PULSE → M3 → FF` per outer pass, with `M1`,
`M2`, `M3` iterated to their own fixed point and `PULSE`/`FF` run once (a single node, and a
block that feeds nothing back, cannot benefit from an inner solve). Caps are Phase A's — inner 20,
outer 20, global 200 block sweeps — and are **detectors, not budgets**: reaching one raises
`ModuleSolveFailure`, which is D15(d).

**One model sequence, not two.** `_call_models_once` was not duplicated. Every model call in it
now routes through `Caller._node(name, run)`, which A13 had already introduced for three nodes;
a block sweep sets `_active_nodes` and the same method walks the same switch dispatch in the same
order, executing only that block's nodes. A second copy of the sequence — one measured, one not —
is how a variant silently stops computing what the baseline computes.

### 2.2 VP5 — the burn-time lift (A4)

No new code: A24 built iteration variable 178, constraint 93 and the `subsolve` seam. What A25
adds is a **derived deck**, `arch_surgery/idf_probe/a25_variant_deck.py`, which never touches the
frozen scenario (D9) and changes exactly three things, each with its provenance written into the
file and into a JSON sidecar.

**The lift is a change of loop topology, not the removal of an inner solver.** `Pulse.run`
assigns a closed-form expression; there is no iteration at that site (A24 §1, plan §4.1b). Nothing
in this report claims otherwise.

### 2.3 The measured artifacts this needed

| Artifact | What it is | How many |
|---|---|---|
| `arch_surgery/docs/data/writeset_<scenario>.json` (**new**) | each module's own write set, from a `PROCESS_IDF_PROBE=modules` write census mapped through the committed DSM node map and intersected with the deck's `ystate` components | 4 decks |
| `arch_surgery/docs/data/ystate_<scenario>.json` | Phase A's categories and scales, **unchanged** — loaded, sha-checked, never regenerated | 4 decks |
| `arch_surgery/docs/data/dsm_node_map.json` | node → module, **unchanged** | 1 |

Write-set census, per deck, with denominators:

| deck | M1 | M2 | M3 | PULSE | FF | covered / components | in two modules |
|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 258 | 240 | 221 | 2 | 119 | **840 / 840** | 0 |
| `low_aspect_ratio_DEMO` | 259 | 244 | 221 | 2 | 120 | **846 / 846** | 0 |
| `st_regression` | 268 | 216 | 223 | **0** | 120 | **827 / 827** | 0 |
| `large_tokamak_eval` | 258 | 240 | 221 | 2 | 119 | **840 / 840** | 0 |

The write sets **partition** the coupling state on all four decks: every component is written by
exactly one module, none by two, none by none. `st_regression`'s empty PULSE column is `k = 0`
measured rather than assumed — `Pulse` writes nothing there, which is why that deck runs the
variant **without** the lift.

### 2.4 Harness

`run_a25.py` (driver: gate / calibrate / campaign), `a25_gates.py` (the equivalence gate and its
teeth), `a25_h5.py` (calibration and H5 analysis, reusing `gates.py`'s census and
`cost_comparison` unchanged), `a25_module_probe.py` (what the code resolved), `a25_writeset.py`
(the artifact generator), `a25_variant_deck.py` (the derived deck). `run_one.py` gained the
multi-start perturbation, the VP4 record, the node-call counters and the constraint-93 audit.

**The cost unit is model node calls** — individual model `run()` invocations, split at the
solve/output boundary. That is Phase A's and A22's unit (`engine.Budget.node_calls`), and it is
the only unit in which the two arms are commensurable: `numerics.n_model_calls` counts *sweeps*
of `_call_models_once`, and a block sweep runs one module, not all of them. Quoting sweeps would
have said the variant costs 8 782 against the baseline's 2 029 on `large_tokamak_nof`, which is
not a cost comparison but a units error.

---

## 3. Three defects the gate found in this task's own work

Protocol §12 says to show every gate capable of failing before accepting its zeros, and records
that this has caught a real defect in the agent's own harness on three consecutive tasks. It
caught **three** here, and the second was invisible to every check except the one that reads the
constraint counts.

### 3.1 The whole-`y` inner test — wrong, and it killed the first variant run

The first implementation took each inner solve's convergence test over the **whole** coupling
vector, on the argument that a component no running node writes cannot move, so restricting the
index set could not change the arithmetic. The argument is wrong. Phase A's predicate scores a
component `inf` whenever *either* snapshot is not float-viewable, and in a fresh process that is
every field no model has written yet. The M1 inner solve was therefore held open by
`ccfe_hcpb.pnuc_tot_blk_sector` — a field M3 writes and M1 cannot touch — through all twenty
inner sweeps, and the run died at the cap having made 40 node calls.

**Equality of values is not equality of scores.** The fix is the measured per-module write sets of
§2.3, which is what Phase A's block arm always used. They are not an optimisation; they are
load-bearing.

### 3.2 `icc = 93` appended at the end of the deck made the equality an inequality

**PROCESS does not decide which constraints are equalities from the constraints themselves.**
`init.set_active_constraints` takes the first `n_equality_constraints` entries of `icc` **in the
order the input file lists them**, and all four decks set that count explicitly under the obsolete
name `neqns`. The first derived deck appended `icc = 93` after every other constraint line, which
made the burn-time *equality* the twenty-fourth **inequality**.

What that variant then did, on `large_tokamak_nof`:

| | first (defective) deck | corrected deck | baseline |
|---|---|---|---|
| `ifail` | **1** | 1 | 1 |
| `n_equality_constraints` | 3 | **4** | 3 |
| `n_inequality_constraints` | **24** | 23 | 23 |
| `norm_objf` | 1.600000000155… | 1.600000000156… | 1.600000000028… |
| model node calls | **26 200** | 43 426 | 42 567 |

It returned `ifail = 1` and an objective that looked right, and it appeared to be **38 % cheaper
than the baseline**. Nothing forced the burn time onto its own consistency manifold, so the
optimiser was free to move it wherever the objective liked. Had that number been reported it
would have been the headline of this task and it would have been false.

It was found by reading `n_inequality_constraints` in the gate table — 23 against the baseline's
23 becoming 24 — and it is now checked directly: the constraint-93 audit fails unless the
constraint is **inside the equality block**, and the sensitivity check exercises that path.

`large_tokamak_eval` failed loudly rather than quietly, and only by luck: `fsolve` solves the
equalities alone and needs as many of them as there are variables, so 3 variables against 2
equalities raised a shape error in scipy. The optimising decks had no such backstop.

### 3.3 The `FF` block ran 789 sweeps of nothing

The DSM node map names `objective_constraints` as an FF-module node with
`in_call_models_once: false` — it is the objective/constraint evaluation, not a call site inside
`_call_models_once`. The first schedule built its blocks from the module label alone, so with the
hoist on the `FF` block was non-empty (`{objective_constraints}`) and executed nothing: 789 block
sweeps on `large_tokamak_nof`, charged against the schedule and invisible in the node count
because no node ran. Fixed by filtering `NODE_MODULE` on `in_call_models_once`.

---

## 4. The equivalence gate

**Baseline is PROCESS as it currently is** (D14(c)): every variant point unset, the existing
`objf`/`conf` predicate, the existing flat loop, the frozen scenario deck. Not Phase A's
reimplemented flat arm — that would compare two codebases where this comparison varies one thing.

The gate is **not** bit identity. A24's bundle was inert, so identity was right there; A25's
variant solves a *different problem* — one more design variable and one more equality constraint
on three of the four decks — so the question is whether the two arms land on the same optimum.

**The tolerance is not chosen here.** `norm_objf` must agree to **1e-6 relative**, which is
PROCESS's own `Caller.check_agreement` rtol and Phase A's first τ rung. The *achieved* difference
is reported beside it per deck, so a deck that only just passes says so — and one does.

### 4.1 Result: **PASS 4 / 4**

| deck | `ifail` base → var | `norm_objf` relative difference | margin to rtol | equality residual base / var | inequalities violated base / var | constraint 93 residual (relative) |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 1 → 1 | 7.98e-11 | **12 525×** | 4.47e-09 / 3.84e-08 | 0 / 0 | 1.19e-08 |
| `low_aspect_ratio_DEMO` | 1 → 1 | **6.85e-07** | **1.46×** | 2.93e-14 / 1.63e-10 | 0 / 0 | 1.63e-10 |
| `st_regression` | 1 → 1 | 5.03e-14 | 1.99e+07× | 5.02e-14 / 2.55e-14 | 0 / 0 | *not applicable — no lift* |
| `large_tokamak_eval` | 1 → 1 | *void on both sides* | — | 1.25e-12 / 1.06e-10 | **3 / 3** | 1.06e-10 |

Reported per scenario, never pooled. Denominators: 5 checks per deck, of which 5 were decided on
`large_tokamak_nof` and `low_aspect_ratio_DEMO`, and 4 on the other two — `st_regression` has no
constraint 93 (no lift), and `large_tokamak_eval` has no objective (`fsolve`), both **named**
rather than counted as agreement.

**Three things this table must be read with.**

1. **`low_aspect_ratio_DEMO` passes with a margin of 1.46, not 12 525.** Its objective differs by
   6.85e-7 against a 1e-6 gate. That is a pass, and it is also the closest thing in this task to a
   near miss; a tolerance one third tighter would have failed it. The tolerance was fixed from
   PROCESS's own rtol before the run, and it is not being adjusted after.
2. **The variant terminates at a looser final accuracy than the baseline on three decks** — the
   equality-residual ratio is 8.6× on `large_tokamak_nof`, 5 342× on `low_aspect_ratio_DEMO` and
   85× on `large_tokamak_eval`, all still far below the audit's 1e-6 absolute ceiling and below
   PROCESS's own `epsvmc`. It is reported because "matched final accuracy" means comparing at the
   residual achieved, not asserting it is equal (plan §3.3). `st_regression` is the exception: the
   variant is *tighter* there, 2.55e-14 against 5.02e-14.
3. **`large_tokamak_eval`'s feasibility audit is comparative only.** It is infeasible in 3 of its
   23 inequalities at its own solution, in **both** arms — it is an `fsolve` evaluation run with 0
   solver iterations, so inequalities are never enforced. A24 found this; A25 reproduces it and
   does not treat 3 = 3 as a pass on absolute feasibility.

### 4.2 The gate shown capable of failing (protocol §12)

Eight deliberately corrupted inputs, through the **production** predicates unmodified:

| perturbation | verdict | required |
|---|---|---|
| `norm_objf` moved by 2 × rtol | **FAIL** | FAIL |
| `ifail` set to 5 | **FAIL** | FAIL |
| one inequality residual made negative | **FAIL** | FAIL |
| one equality residual set to 1.0 | **FAIL** | FAIL |
| constraint 93 residual 1 s on a 2 568 s burn time (3.9e-4 relative) | **FAIL** | FAIL |
| constraint 93 marked outside the equality block | **FAIL** | FAIL |
| variant run marked crashed | **FAIL** | FAIL |
| two genuinely different scenarios compared | **FAIL** | FAIL |
| *(control)* unperturbed copy | PASS | reproduce the real verdict |
| *(control)* `norm_objf` moved by one ULP | PASS | pass — 1 ULP is far below a 1e-6 gate |

**8 of 8 teeth bite.** The last control is stated rather than hidden: this is a tolerance gate, so
a variant differing by up to 1e-6 relative in the objective is accepted by design, and
`low_aspect_ratio_DEMO` uses 68 % of that budget.

### 4.3 Switch neutrality of the default path

Every model call in `_call_models_once` now routes through `Caller._node`, and a plain integer
counter increments per node call on **both** arms. That is a change to the default path, so it is
gated rather than argued: bit identity of the whole variant-point-off build against the parent
commit `83e18d15`, four decks, probe off and probe on, using A24's own comparator
(`compare_a3.compare_pair`, imported unchanged).

**PASS 4 / 4, probe off and probe on.**

| deck | MFILE lines differing / compared | MFILE floats differing / compared | total quantities differing / compared | `ifail` | sweeps |
|---|---|---|---|---|---|
| `large_tokamak_nof` | **0** / 16 174 | **0** / 13 559 | **0** / 29 760 | 1 → 1 | 2029 → 2029 |
| `low_aspect_ratio_DEMO` | **0** / 16 435 | **0** / 13 455 | **0** / 29 916 | 1 → 1 | 4286 → 4286 |
| `st_regression` | **0** / 18 692 | **0** / 13 493 | **0** / 32 206 | 1 → 1 | 1891 → 1891 |
| `large_tokamak_eval` | **0** / 15 917 | **0** / 13 487 | **0** / 29 413 | 1 → 1 | 29 → 29 |

**0 of 121 295** quantities differ, per mode, reported per scenario and never pooled; the total is
given only because the four rows are the evidence and this is their sum. The same four zeros over
the same four denominators with `PROCESS_IDF_PROBE=baseline`. Solver iterations unchanged: 8 / 16 /
10 / 0.

Its teeth, from A24's own sensitivity command run against this matrix: one unit in the last place
of `rmajor` is caught on **4 of 4** decks as exactly one differing line and one differing float;
one ULP of `norm_objf` flips the acceptance predicate to FAIL on **3 of 4** (the fourth,
`large_tokamak_eval`, has no `norm_objf` and is reported as ABSENT rather than as agreement); one
ULP of `sqsumsq` and a changed `ifail` on **4 of 4**; two genuinely different scenarios differ in
**11 606 of 13 441** shared floats.

---

## 5. δ calibration (D15(a))

Perturbation size is **calibrated, not chosen**: δ ∈ {1 %, 5 %, 10 %} on the **baseline alone**,
12 starts each, and the largest δ that keeps `ifail = 1` on more than half the starts is taken.
144 runs. The whole table is given, not just the choice.

| deck | δ = 1 % | δ = 5 % | δ = 10 % | choice |
|---|---|---|---|---|
| `large_tokamak_nof` | 12 / 12 | 12 / 12 | **11 / 12** (1 crashed) | **10 %** |
| `low_aspect_ratio_DEMO` | 12 / 12 | 9 / 12 (3 × `ifail = 5`) | **7 / 12** (4 × `ifail = 5`, 1 crashed) | **10 %** |
| `st_regression` | 12 / 12 | 11 / 12 (1 × `ifail = 5`) | **12 / 12** | **10 %** |
| `large_tokamak_eval` | 12 / 12 | 12 / 12 | **12 / 12** | **10 %** |

Counts are `ifail = 1` over 12 starts. **δ = 10 % on every deck**, so the campaign runs one δ and
the four campaigns are comparable in perturbation size.

**Four things in that table are worth stating rather than smoothing.**

1. **`low_aspect_ratio_DEMO` is the fragile deck, and it is fragile in the *baseline*.** At 10 %
   the incumbent architecture solves 7 of 12 starts. That is the floor the variant is measured
   against on that deck, and it is a property of the deck and the incumbent solver, not of
   anything A25 built.
2. **`st_regression` is not monotone in δ** — 12 / 12 at 1 %, 11 / 12 at 5 %, 12 / 12 at 10 %.
   Multi-start success is a property of a landscape, not a smooth function of perturbation size,
   and reading a trend into three points would be reading noise. The rule as written ("largest δ
   keeping most") is unaffected.
3. **Both crashes are model-level, in the baseline**, and identical in message:
   `RuntimeError: Failed to converge after 50 iterations, value is nan` from an inner root-find
   inside a model. Nothing to do with the driver, and a reminder that PROCESS's own robustness
   floor at a 10 % perturbation is not 100 %.
4. **The effective perturbation is smaller than 10 % for the variables that sit on a bound.**
   Perturbed starts are clamped into the deck's own scaled bounds and the clamp is counted: on
   `large_tokamak_nof` at δ = 5 %, 3–4 of the 20 iteration variables are clamped per start,
   because the deck's own point sits exactly on `boundl` for those (`rmajor` at `boundl(3) = 8.0`,
   for instance). The clamp is applied identically in both arms and is recorded per variable per
   start.

---
## 6. H5 — the paired multi-start campaign

**3 arms × 25 starts × 4 decks = 300 isolated runs**, δ = 10 %, start 0 unperturbed, perturbation
factors keyed on the iteration-variable number so the arms give bit-identical factors to every
variable they share. Cost is **model node calls**; nothing here reads wall clock.

The third arm, `variant_nohoist`, is the proposed architecture minus VP2. D15(b) defers it; it was
run because the brief asks for the hoist's share of the combined figure, and A13's separable
figures were measured in the **flat** architecture, so quoting them as the hoist's share *inside
this variant* would be a T11 units error.

### 6.1 Robustness first, because robustness outranks cost

A per-arm success count answers "how many", which is not the question when the starts are paired.
The table below is the 2 × 2: which starts each arm solves (`status ok` **and** `ifail = 1`).

| deck | both solve | only baseline | only variant | neither | denominator |
|---|---|---|---|---|---|
| `large_tokamak_nof` | 22 | **0** | **0** | 3 | 25 |
| `low_aspect_ratio_DEMO` | 11 | **1** | 0 | 13 | 25 |
| `st_regression` *(control, k = 0, no lift)* | 22 | **2** | 0 | 1 | 25 |
| `large_tokamak_eval` | 15 | **10** | 0 | 0 | 25 |

**The variant never solves a start the baseline cannot, and on three decks it loses starts the
baseline solves.** By the plan's own pre-declared outcome table that is H5 failing, and it is the
headline regardless of cost. The failure modes, per arm, per deck:

| deck | baseline | variant |
|---|---|---|
| `large_tokamak_nof` | 22 ok, 3 `RuntimeError` | 22 ok, 3 `RuntimeError` — **the same three starts** |
| `low_aspect_ratio_DEMO` | 12 ok, 11 `ifail = 5`, 2 `RuntimeError` | 11 ok, 9 `ifail = 5`, 2 `RuntimeError`, **3 `ModuleSolveFailure`** |
| `st_regression` | 24 ok, 1 `ifail = 5` | 22 ok, 3 `ifail = 5` |
| `large_tokamak_eval` | **25 ok** | 15 ok, **10 `ModuleSolveFailure`** |

`RuntimeError` is always the same model-level failure — `Failed to converge after 50 iterations,
value is nan` from `optimize.newton` inside `superconducting.py:1266` — and it hits both arms on
the same starts. It is a nested root-find in a *model*, exactly the class of site A9–A11 target,
and it is not caused by anything A25 built.

### 6.2 Every extra failure is one field, and the mechanism is measured

**13 of 13 `ModuleSolveFailure`s across the whole campaign name the same component:**
`current_drive.eta_cd_dimensionless_hcd_primary`, scored `inf` by Phase A's predicate in module
M1. The cause was measured, not inferred, by wrapping `YSpec.residual` from the harness side and
recording the raw snapshots behind the score:

```
component: current_drive.eta_cd_dimensionless_hcd_primary
category : continuous     scale: 0.7970116052927925
previous : 0.0            current: nan           cause: non-finite in the CURRENT snapshot
```

It goes `0.0 → NaN` on the first M1 sweep and stays NaN. Phase A's predicate scores a non-finite
component `inf` and never converges — deliberately, as the documented inverse of PROCESS's own
loophole. And that loophole is real, measured in the same probe:

```
Caller.check_agreement(nan_state, same_nan_state)  ->  True
Caller.check_agreement(finite_state, nan_state)    ->  False
```

`np.allclose(previous, current, rtol=1e-6, equal_nan=True)` calls a state that has gone NaN
**idempotent with itself**. So at those starts the baseline's loop exits, the solver proceeds, and
`ifail = 1` is reported over a state containing a NaN. Decision D14(c) says the baseline reproduces
`check_agreement`'s known defects in full, deliberately, because the baseline is PROCESS as
shipped; this is what that decision bought.

**Why one deck is immune, and it is not the architecture.** The field's category is per deck,
measured from the harvest:

| deck | category of `eta_cd_dimensionless_hcd_primary` | harvest points | extra variant failures |
|---|---|---|---|
| `large_tokamak_nof` | **`nan_in_harvest`** — excluded from the predicate | 149 | **0** |
| `low_aspect_ratio_DEMO` | `continuous`, scale 0.8937 | 297 | 3 |
| `st_regression` | `continuous`, scale 0.1703 | 144 | 0 |
| `large_tokamak_eval` | `continuous`, scale 0.7970 | **10** | 10 |

On `large_tokamak_nof` the Phase A harvest happened to catch this quantity non-finite, so it is
categorised `nan_in_harvest` and excluded — and that deck has **zero** extra variant failures. On
the other three the harvest did not catch it, so it is included and the variant refuses to
converge when it goes NaN. `large_tokamak_eval`'s scale rests on **10** harvested design points,
the weakest artifact of the four, and it is the deck with 10 failures.

**So the variant's robustness deficit is not a property of the block schedule. It is one
data-structure field going NaN, plus the coverage of a committed artifact.** Both readings are
true and both belong in the record:

- *As measured*, the variant solves fewer starts, on three of four decks. H5 fails on the declared
  criterion.
- *As explained*, it fails because it declines to call a NaN state converged, at points where the
  incumbent's predicate does exactly that. Whether that is worse behaviour is not a question a
  success count can answer.

**Neither of those is a licence to re-run with the field excluded.** Doing so would be tuning past
a gate, which the working rules forbid, and it would also hide the finding.

### 6.3 The drop census, before any ratio

| deck | kept | crashed | `ifail ≠ 1` | `objf_mismatch` | offered | I-12 degenerate entries |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | **22** | 3 | 0 | 0 | 25 | **0** / 22 completed both arms |
| `low_aspect_ratio_DEMO` | **8** | 5 | 9 | **3** | 25 | **0** / 23 and 20 |
| `st_regression` | **20** | 0 | 3 | **2** | 25 | **0** / 25 and 25 |
| `large_tokamak_eval` | **15** | 10 | 0 | 0 | 25 | **0** / 25 and 15 |

`objf_mismatch` is D15(c): a start where the arms' `norm_objf` differ by more than 1e-6 relative
leaves the cost comparison **and is counted as a robustness finding**. Five such starts, all on
the two decks whose objectives were already closest to the gate tolerance.

**Issue I-12 did not recur: zero degenerate entries in 300 runs.** Net electric power at the
returned point is positive on every completed run in both arms, on all four decks. That is the
opposite of what was expected, and it is a real result rather than an absence of measurement —
the count is over completed runs, with the denominators above.

*That census itself needed a correction.* Its first version counted every arm's rows, including
crashed runs, whose partial MFILE makes the parser return `0` for a key that is not there. It
reported **10 degenerate entries on `large_tokamak_eval`** — which were its ten crashed variant
runs and not degenerate entries at all. Caught by checking the count against the baseline arm,
which had none.

### 6.4 Cost, over the kept starts only

Paired ratio of model node calls, variant ÷ baseline, per start. Reported per deck, never pooled.

| deck | n | min | q1 | **median** | q3 | max | cheaper / dearer |
|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 22 | 0.885 | 1.018 | **1.020** | 1.022 | 1.172 | 3 / 19 |
| `low_aspect_ratio_DEMO` | 8 | **0.236** | 0.591 | **0.772** | 0.982 | **3.261** | 6 / 2 |
| `st_regression` *(control)* | 20 | 0.239 | 0.941 | **0.949** | 0.958 | 0.990 | **20 / 0** |
| `large_tokamak_eval` | 15 | 1.053 | 1.105 | **1.168** | 1.176 | 1.192 | 0 / 15 |

- **`large_tokamak_nof`: the variant costs 2.0 % more**, tightly (q1–q3 spans 1.018–1.022).
- **`low_aspect_ratio_DEMO`: inconclusive.** A median of 0.772 over **8** starts whose ratios run
  from 0.236 to 3.261 is not a result. The distributions overlap, and the plan's own outcome table
  says so: *"distributions overlap substantially → inconclusive, reported as such — not resolved by
  picking a summary statistic"*.
- **`st_regression`: the variant costs 5.1 % less, on 20 of 20 kept starts** and with a tight
  interquartile range. This is the cleanest cost result in the task, and it is the deck with **no
  lift and therefore no dimension penalty** — the partition and the hoist alone.
- **`large_tokamak_eval`: the variant costs 16.8 % more**, on 15 of 15. It is an `fsolve`
  evaluation run with 0 solver iterations, so there is no optimiser search for a block schedule to
  economise on; all the schedule adds is outer passes.

### 6.5 Attribution: the H5 risk did not materialise

Plan §2.5 step 4 asks that a loss be decomposed into extra *optimiser iterations* (H5 proper) and
extra *evaluations per iteration* (the `2n → 2(n+1)` gradient penalty). Paired VMCON
major-iteration ratio, variant ÷ baseline, per start:

| deck | n | q1 | **median** | q3 | design variables |
|---|---|---|---|---|---|
| `large_tokamak_nof` | 22 | **1.000** | **1.000** | **1.000** | 20 → 21 |
| `low_aspect_ratio_DEMO` | 8 | 0.620 | **0.806** | 1.016 | 19 → 20 |
| `st_regression` | 20 | **1.000** | **1.000** | **1.000** | 14 → 14 |
| `large_tokamak_eval` | 15 | — | — | — | 2 → 3 (`fsolve`, 0 iterations) |

**H5's own risk — that adding a variable and a consistency constraint changes the optimiser's
behaviour enough to consume the saving — did not materialise.** On `large_tokamak_nof` and on
`st_regression` the major-iteration count is *unchanged*, start for start, with the interquartile
range collapsed onto 1.000. On `low_aspect_ratio_DEMO` it moved in the variant's **favour** (median
0.806). Nothing bounded this in advance (plan §4.1a, condition 3), and the answer is that on these
decks the SQP subproblem is not measurably disturbed.

The cost ratio then factorises exactly. At each deck's own point, where the baseline's
`call_models` count is recorded by the probe:

| deck | MDA solves base → var | ratio | node calls per MDA solve base → var | ratio | product | measured total |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 630 → 660 | 1.0476 | 67.57 → 65.80 | 0.9738 | **1.0202** | **1.0202** |
| `low_aspect_ratio_DEMO` | 1240 → 1050 | 0.8468 | 72.55 → 66.65 | 0.9187 | **0.7779** | **0.7779** |
| `st_regression` | 570 → 570 | **1.0000** | 69.60 → 65.46 | 0.9405 | **0.9406** | **0.9406** |
| `large_tokamak_eval` | 11 → 12 | 1.0909 | 51.55 → 49.75 | 0.9651 | **1.0529** | **1.0529** |

*(n = 1 per deck: this is exact arithmetic on the gate-point run, not a distribution.)* The left
factor is the dimension penalty and any iteration-count change; the right factor is the loop-side
saving the block schedule buys. On `st_regression` the left factor is exactly 1 because the design
vector is unchanged, which isolates the loop-side saving at **−5.9 %**.

### 6.6 Against §4.1a's expectation, and the measurement is the finding

§4.1a put the loop-side saving near **−26 %** on model evaluations after the `1/n` penalty,
*conditional on VMCON's major-iteration count not moving*. The condition held. The number did not:

| deck | §4.1a expectation | measured (paired median) |
|---|---|---|
| `large_tokamak_nof` | ≈ −26 % | **+2.0 %** |
| `low_aspect_ratio_DEMO` | ≈ −26 % | −22.8 %, but **inconclusive** (n = 8, ratios 0.24–3.26) |
| `st_regression` | 0 % (no coupler) | **−5.1 %** |

The gap is exactly the one §4.1a's own condition 1 named: A22's −29 % was **the block arm against
itself**, over harvested design points, with Phase A's floor-1 predicate — not the block arm
against today's driver, which is Phase B's baseline. Measured against the incumbent, the loop-side
saving is **−2.6 %** on `large_tokamak_nof` and **−5.9 %** on `st_regression`, an order of
magnitude smaller. The plan warned that its own figure was not Phase B's expected saving and that
quoting it as one would repeat T11; that warning is now backed by a measurement.

### 6.7 The hoist's separable share, measured inside the variant

`variant` ÷ `variant_nohoist`, paired, over the starts both solve:

| deck | n | q1 | **median** | q3 | cheaper | A13's flat-arm figure |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 22 | 0.9707 | **0.9708** (−2.92 %) | 0.9708 | 22 / 22 | −6.56 % |
| `low_aspect_ratio_DEMO` | 11 | 0.9712 | **0.9712** (−2.88 %) | 0.9712 | 11 / 11 | −6.76 % |
| `st_regression` | 19 | 0.9412 | **0.9705** (−2.95 %) | 0.9706 | 18 / 19 | −6.64 % |
| `large_tokamak_eval` | 15 | 0.9835 | **0.9837** (−1.63 %) | 0.9841 | 15 / 15 | −2.63 % |

*Commensurability of the two columns, stated rather than assumed:* A13's unit is **total** model
node calls (its hook-off figure for `large_tokamak_nof` is 42 609, which is this task's
`node_calls_total` exactly); A25's cost unit is the **solve phase** alone (42 567 on the same run),
the difference being the 42 calls of the final-output path. The two differ by 0.1 % on that deck,
so the columns are comparable — but they are not the same quantity, and A13's arm is the flat
architecture while A25's is the block one.

**Inside the proposed architecture the hoist is worth less than half what it is worth in the flat
one** — 2.9 % against 6.6 %, on three decks. The mechanism is not mysterious: the hoist removes
the feed-forward tail from every sweep it would otherwise run on, and the block schedule already
runs fewer full-sequence sweeps, so there is less to remove. `large_tokamak_eval` is lower again
because its figure of merit is 7, so `costs` stays in the loop and only `water_use` is hoisted
(§7.1).

**The headline is therefore the proposed architecture, never the partition's benefit** (plan §7a,
D15(b)). Splitting the combined figure on `large_tokamak_nof`: the architecture without the hoist
costs **+5.09 %** (paired median 1.0509), the hoist takes **2.9 pp** off it, and the combined
figure is **+2.02 %**.

### 6.8 The hoist costs two starts on `st_regression`, and only a multi-start could see it

| `st_regression` | solves | vs baseline |
|---|---|---|
| baseline | **24** / 25 | — |
| `variant_nohoist` | **24** / 25 | 0 only-baseline, 0 only-variant — **identical success set** |
| `variant` (with the hoist) | **22** / 25 | 2 only-baseline |

The two starts are `start005` and `start010`. On both, the baseline and `variant_nohoist` return
`ifail = 1` in 40/39 and 60/60 major iterations; the hoisted variant returns `ifail = 5`.

**So on this deck the partition is robustness-neutral and the hoist is not.** A13 gated the hoist
as bit-identical at each deck's own point and it was; a single point cannot see a start that flips
under perturbation. This is the first evidence that the hoist has a robustness cost at all, it is
2 starts in 25 on one deck, and it is offered as a finding rather than a repair.

---
## 7. What VP4 resolved, measured rather than asserted

`a25_module_probe.py` reads every claim out of the imported modules, in subprocesses.

**Switch neutrality with the arm off** — `ENABLED` false, `MODULE_SOLVE_NAME` `"off"`,
`NODE_MODULE` empty (0 entries), `Caller.MODULE_SOLVE_ENABLED` false, Phase A's `ystate` module
**not loaded**, spec cache empty, and neither `PROCESS_ARCH_YSTATE` nor `PROCESS_ARCH_WRITESET`
required. The variant point costs nothing it does not use.

**Four negative paths, four import-time errors** — an unrecognised arm name; a lifted arm with no
`PROCESS_ARCH_YSTATE`; a lifted arm with no `PROCESS_ARCH_WRITESET`; and a *mismatched pair*
(one deck's ystate with another deck's write set), which is refused by comparing the artifact's
recorded `ystate_components_sha256` against the sha recomputed from the rebuilt spec. **4 of 4
raise**, naming the offending value.

**The spec rebuilds exactly** — `components_sha256` recomputed from the spec reconstructed out of
the committed artifact equals the value the artifact carries, on 4 of 4 decks. The subsets resolve
to real components, cover every component, and put none in two modules (§2.3).

### 7.1 VP2 × VP4 — the composition framework §2.5 flagged, tested rather than assumed

The framework flags this as a latent defect that fires only when two arms compose. It was tested
across every figure of merit the four decks use, plus the two the hoist's guard names:

| figure of merit | hoisted tail | `FF` block left in the loop | used by |
|---|---|---|---|
| 1 | `costs`, `water_use` | *(empty)* | `large_tokamak_nof` |
| −5 | `costs`, `water_use` | *(empty)* | `st_regression` |
| −14 | `costs`, `water_use` | *(empty)* | `low_aspect_ratio_DEMO` |
| **7** | `water_use` | **`costs`** | `large_tokamak_eval` |
| 6 | `water_use` | `costs` | — |

**The composition is correct.** Under figures of merit 6 and 7 the objective reads `costs.coe` /
`costs.cdirt` / `costs.concost`, so `costs` must keep running inside the loop; it does, as the FF
block, while `water_use` is still hoisted. Under every other figure of merit the whole tail is
hoisted and the FF block is empty and is skipped rather than swept. The live run confirms it:
`large_tokamak_eval`'s variant resolves `arch_hoist_tail_resolved = ['water_use']` and runs the FF
block 22 times, while the other three resolve `['water_use', 'costs']` and run the FF block 0
times.

### 7.2 A finding: `pulse` does **not** join the feed-forward tail under the lift

Framework note C2a, and A13's report, predict that `pulse` joins the hoisted tail once the
burn-time coupler is lifted, because the node set is derived at run time. **It does not**, and the
reason is structural rather than accidental: `A13`'s derivation asks the committed DSM node map
for each node's module and hoists those whose module is in `HOIST_MODULES = {"FF"}`. `pulse`'s
module in that map is `"PULSE"`, statically, whatever the lift is doing. No amount of lifting
changes a committed label.

The prediction is nevertheless **right on the substance**, and this is measured: `Pulse` writes
exactly two fields on the three pulsed decks —

- `times.t_plant_pulse_burn`, which under the lift the optimiser owns and `subsolve` returns
  untouched, and
- `constraints.t_current_ramp_up_min`, whose **only** reader anywhere in `process/` is constraint
  equation 41 (`constraints.py:1102`) — a constraint, not a model, evaluated after the sweep.

So under the lift `Pulse` genuinely feeds nothing back into the model sequence and could be
hoisted. In this variant it is not: it runs once per outer pass as its own block.

**What it costs, with its denominator.** On `large_tokamak_nof`'s gate run `pulse` ran 1 314 times
across 660 `call_models` invocations; hoisted it would have run 660. The 654 avoidable node calls
are **1.5 % of the variant's 43 426**. On `low_aspect_ratio_DEMO`: 2 089 against 1 050, i.e. 1 039
avoidable calls, **1.5 % of 69 986**.

This is an identified and **unexercised** improvement. It was not taken, because changing which
nodes the hoist selects mid-task would change the architecture being measured, and because the
right fix is a decision about the node map rather than a patch in `caller.py`. It is offered to
the queue rather than acted on.

---

## 8. What the cost unit does and does not count

**Counted:** every model node call — one increment per `run()` invocation of a model node inside
`_call_models_once` — in both arms, split at the entry to `write_output_files` so the output
phase (which re-enters every model's `run()` from its `output()`, trap T7, identically in both
arms) is excluded.

**Not counted, in either arm: each arm's own convergence test.** This is plan §2.5's unit and it
is the right one, but the omission is not symmetric and it is stated rather than elided:

| | baseline | variant |
|---|---|---|
| what its predicate evaluates | `objective_function` + `constraint_eqns`, **once per sweep** | Phase A's scaled residual over `y`, **once per block sweep** |
| how often, on `large_tokamak_nof`'s gate run | 2 029 | ~17 500 reads of an 840-component vector; 660 objective/constraint evaluations |

So the excluded work runs **in opposite directions**: the baseline evaluates the objective and the
whole constraint vector three times as often as the variant does, while the variant reads and
copies the coupling state thousands of times where the baseline reads nothing. The second of those
is why the variant's *wall clock* is roughly twice the baseline's on `large_tokamak_nof` while its
*model evaluations* are within 2 %.

**That wall-clock figure is not evidence of anything and is not used as any.** The `y` read is
instrument-grade — it copies every array in the coupling state on every block sweep — and a
production implementation of this architecture would not do it that way. A conclusion drawn from
it would be a conclusion about this harness.

---

## 9. Autonomous decisions, with reversal paths

**AD1 — The variant's burn time starts at the value the baseline's own idempotence loop settles
on at the deck's own starting design vector.**
Plan §2.5 says the extra variable is initialised from the deck's own burn time and that the choice
is stated rather than tuned. `times.t_plant_pulse_burn` defaults to 1000 s and none of the three
pulsed decks sets it, while their settled values are thousands of seconds, and
`load_iteration_variables` reads the field *before* any model runs — so leaving it alone would
have started the two arms from different design points, which is a confound rather than a
perturbation. One sweep is not enough either, and that is measured, not argued: the first sweep
computes the burn time from an entry loop voltage that has not settled and gives 9.7e5 s on
`large_tokamak_nof` against a settled 2 568.13 s. Both numbers are in the sidecar. The rule chosen
puts the variant **on its own consistency manifold at entry**: constraint 93's residual at the
chosen start is **exactly 0.0** on all three pulsed decks.
*Reversal:* one line in `a25_variant_deck.entry_burn_time`; the alternative value is already
recorded per deck.

**AD2 — VP4 imports Phase A's `ystate` module by path rather than vendoring the predicate into
`process/`.**
D14(c) requires the variant to use *Phase A's* coupling-state predicate. Copying it would create
two implementations of one rule, which is the drift the decision exists to prevent. The import is
lazy and happens only on the VP4-on path, so `process` still imports standalone with the variant
point off — verified, not assumed (§6). It is the same move `caller.NODE_MAP_PATH` already makes.
*Reversal:* move `ystate.py`'s ~200 lines into `process/core/solver/` and change one path; the
`components_sha256` check would then be the thing keeping the copies honest.

**AD3 — `PROCESS_ARCH_YSTATE` and `PROCESS_ARCH_WRITESET` are required, with no default.**
Both artifacts are per-deck. A predicate silently taking another deck's scales, or another deck's
subsets, changes what "converged" means with no symptom. Both are import-time errors when the arm
is on, and a mismatched *pair* is refused by a sha cross-check.
*Reversal:* derive the paths from the scenario name; the loaders already carry the provenance that
would make that checkable.

**AD4 — The cost unit is model node calls, not `numerics.n_model_calls`.**
Phase A's and A22's unit. `n_model_calls` counts sweeps of `_call_models_once`, and a block sweep
runs one module, so it is not commensurable between the arms. The counter is a module-level
integer in `caller.py`, incremented in `_node` on both arms, and snapshotted at the entry to
`write_output_files` so the solve phase can be separated from the output phase (which re-enters
every model's `run()` from its `output()`, trap T7, identically in both arms).
*Reversal:* delete two module-level lists and three lines in `run_one.py`; nothing else reads them.

**AD5 — Multi-start factors are keyed on the iteration-variable *number*, not its position.**
The variant's design vector is one longer than the baseline's, so a position-keyed perturbation
would give the two arms different factors for the same variable and the pairing would be
fictitious. `1 + δ·(2u−1)` with `u` from a SHA-256 of `(seed, ixc)` gives bit-identical factors to
every shared variable regardless of vector length, and is reproducible from the seed alone.
*Reversal:* one function in `run_one.py`.

**AD6 — Perturbed starts are clamped into the deck's own scaled bounds, and the clamp is counted.**
A start outside its own box is not a start; it is a different problem. The clamp count is recorded
per start and reported (§5), because on these decks it is not negligible — several iteration
variables sit exactly on a bound at the deck's own point, so a perturbation in one direction is
absorbed entirely.
*Reversal:* drop the `min`/`max`; the per-variable record already carries the unclamped value.

**AD7 — A third arm, `variant_nohoist`, was run rather than quoting A13's separable figure.**
D15(b) defers the excluding arm; the brief asks for the hoist's share of the combined figure.
A13's 6.56 / 6.76 / 6.64 / 2.63 % were measured in the **flat** architecture, so quoting them as
the hoist's share *inside this variant* would be a units error of the T11 kind. The excluding arm
costs one more arm in the campaign and answers the question directly.
*Reversal:* n/a — it is an extra arm, not a change to the other two.

**AD8 — The gate's `norm_objf` tolerance is 1e-6 relative, taken from PROCESS's own
`check_agreement` rtol and Phase A's first τ rung.**
A tolerance picked after seeing the numbers is not a gate. This one has two independent
pre-existing sources, and the achieved difference is reported per deck beside it — including the
deck that uses 68 % of the budget.
*Reversal:* one constant in `a25_gates.py`; every achieved difference is recorded, so any other
tolerance can be applied to the same data without re-running anything.

---

## 10. What I did not do

- **No physics change, and no `process/models/` change at all.** A24's `pulse.py` edit is the only
  one in the experiment and it is untouched here. D11's approval gate was not reached, because
  nothing needed it.
- **No re-derivation of `ystate_<scenario>.json`.** Phase A's categories and scales are loaded and
  sha-checked, never regenerated. The variant is tested by the rule Phase A measured.
- **No tuning of anything after seeing a result.** The gate tolerance, τ, the caps and the δ
  ladder were fixed from pre-existing sources before the runs.
- **The `pulse` hoist was not taken** (§7.2), although it is available and worth ~1.5 %.
- **No start was re-run with the NaN-going field excluded**, and no arm was re-run with any setting
  changed after seeing a result. Excluding `current_drive.eta_cd_dimensionless_hcd_primary` from the
  predicate would have raised the variant's success rate on three decks and would have been tuning
  past a gate.
- **The `equal_nan` loophole was not repaired in the baseline.** D14(c) requires the baseline to
  reproduce `check_agreement`'s known defects in full, because the baseline is PROCESS as shipped;
  silently repairing it would flatter the comparison. It is measured (§6.2) and filed, not endorsed.
- **No τ ladder was climbed.** D15 sets τ = 1e-6 as the start and multi-start success rate as the
  confirmatory signal; the success rates are reported, and no second rung was run.
- **`MASTER_TODO.md` was not edited.** It is the orchestrator's file.
- **Nothing was pushed, and nothing was merged.**
- **No conclusion rests on a timing.** Wall clock appears in this report only where a reader needs
  the reproduction cost, and `a25_h5.py` does not read it at all.

---

## 11. Reproduction

```bash
W=/home/wrutten/projects/PROCESS_surgery_worktrees/A25-phase-b-variant
PY=/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python
R=$W/arch_surgery/idf_probe/runs/a25

# --- the committed artifacts this task added -------------------------------
# one instrumented run per deck; writes_by_node -> per-module write sets
for S in large_tokamak_nof low_aspect_ratio_DEMO st_regression large_tokamak_eval; do
  (cd $R/_writeset/$S && PYTHONPATH=$W $PY $W/arch_surgery/idf_probe/run_one.py \
      --scenario $S --mode modules --outdir $R/_writeset/$S --expect-tree $W)
done
$PY $W/arch_surgery/idf_probe/a25_writeset.py --probe-runs $R/_writeset

# --- the derived decks (frozen scenarios untouched) ------------------------
for S in large_tokamak_nof low_aspect_ratio_DEMO large_tokamak_eval; do
  (cd $R/_decks/$S && PYTHONPATH=$W $PY $W/arch_surgery/idf_probe/a25_variant_deck.py \
      --scenario $S --outdir $R/_decks/$S --expect-tree $W)
done

# --- switch neutrality of the default path against the parent commit -------
git archive 83e18d15 | tar -x -C $R/_parent
$PY $W/arch_surgery/idf_probe/run_a24.py --parent-tree $R/_parent --runs $R/neutrality --jobs 2
PYTHONPATH=$W $PY $W/arch_surgery/idf_probe/gates.py gate        --runs $R/neutrality
PYTHONPATH=$W $PY $W/arch_surgery/idf_probe/gates.py sensitivity --runs $R/neutrality

# --- what VP4 resolved -----------------------------------------------------
(cd $R/_moduleprobe && PYTHONPATH=$W $PY $W/arch_surgery/idf_probe/a25_module_probe.py \
    --outdir $R/_moduleprobe --expect-tree $W)

# --- the equivalence gate, and its teeth -----------------------------------
$PY $W/arch_surgery/idf_probe/run_a25.py gate --runs $R --jobs 4
$PY $W/arch_surgery/idf_probe/a25_gates.py gate        --runs $R/gate
$PY $W/arch_surgery/idf_probe/a25_gates.py sensitivity --runs $R/gate

# --- H5: calibrate delta on the baseline, then the paired campaign ---------
$PY $W/arch_surgery/idf_probe/run_a25.py calibrate --runs $R --jobs 5 --starts 12
$PY $W/arch_surgery/idf_probe/a25_h5.py calibration --runs $R/calibrate
$PY $W/arch_surgery/idf_probe/run_a25.py campaign --runs $R --jobs 5 --starts 24 --delta 0.10
$PY $W/arch_surgery/idf_probe/a25_h5.py h5 --runs $R/h5

# --- why the variant fails starts the baseline "solves" --------------------
(cd $R/_nanprobe && PYTHONPATH=$W $PY $W/arch_surgery/idf_probe/a25_nan_probe.py \
    --scenario large_tokamak_eval --seed 1 --delta 0.1 --outdir $R/_nanprobe --expect-tree $W)
# and again with the variant environment set and --variant, to record the raw
# snapshots behind the inf score
```

`run_a25.py` sets `PYTHONPATH` to this worktree for every subprocess and `run_one.py` asserts the
**exact** tree it imported rather than a path prefix (trap T6). Raw artifacts under
`arch_surgery/idf_probe/runs/` stay untracked; the numbers in this report are the committed
summary. The gate's own outputs are `runs/a25/gate/_gate_a25.json`,
`runs/a25/gate/_gate_sensitivity_a25.json`, `runs/a25/neutrality/_gates_a24.json`,
`runs/a25/calibrate/_calibration_a25.json` and `runs/a25/h5/_h5_a25.json`.

**Machine cost, as context and not as evidence** (no conclusion in this report rests on a timing,
`CLAUDE.md` working rules and issue I-10): the gate matrix is 8 runs and about 85 s of wall clock
at 4 parallel jobs; the neutrality matrix 16 runs; the δ calibration 144 runs; the campaign 300, about two and a half hours at 5 parallel jobs.

---

## 12. Change log (append-only)

| # | Date | Change |
|---|---|---|
| 1 | 2026-09-01 | Worktree confirmed at `83e18d15` on `A25-phase-b-variant`, `arch_surgery/` present. `CLAUDE.md`, `TRAPS.md`, plan §2.5 / §4.1a / §4.1b / §7a, `MASTER_TODO.md` D5/D6/D11/D14/D15/D16 and I-12/I-13, A24, A22 and the Phase A results read. |
| 2 | 2026-09-01 | `process/core/solver/module_solve.py` added: VP4 arm, τ, the two required committed artifacts, Phase A's caps, `ModuleSolveFailure`, and the loader that rebuilds Phase A's `YSpec` from the committed artifact with a `components_sha256` check. |
| 3 | 2026-09-01 | `process/core/caller.py`: every model call routed through `Caller._node`; VP4 block filter, schedule, node-call counters and the block Gauss-Seidel loop added. Default path guarded by `MODULE_SOLVE_ENABLED`. |
| 4 | 2026-09-01 | `a25_variant_deck.py` added; three derived decks generated. Initial-value rule settled by measurement: one baseline sweep gives 9.7e5 s on `large_tokamak_nof`, the baseline's settled loop gives 2 568.13 s, and only the latter puts constraint 93's residual at exactly 0.0 at entry. |
| 5 | 2026-09-01 | **First variant run died at the inner cap after 40 node calls.** The whole-`y` inner test is not equivalent to the subset test: `ystate` scores a not-float-viewable component `inf`, and in a fresh process that is every unwritten field. Per-module write sets measured with the `modules` probe and committed as `writeset_<scenario>.json`; inner solves restricted to them. |
| 6 | 2026-09-01 | Second defect: the `FF` block was non-empty because `objective_constraints` carries module `FF` but `in_call_models_once: false` — 789 block sweeps of no-ops. `NODE_MODULE` now filters on that flag. |
| 7 | 2026-09-01 | **Third defect, and the serious one.** `icc = 93` appended at the end of the deck became the 24th *inequality*, because PROCESS decides equality membership by position in `icc`. The variant returned `ifail = 1` and looked **38 % cheaper**. Deck derivation now inserts the line after the last equality and raises `neqns` in the same edit; the constraint-93 audit checks equality-block membership; the sensitivity check exercises that path. |
| 8 | 2026-09-01 | `tests/unit`: **843 passed, 4 skipped** — the same as A24. |
| 9 | 2026-09-01 | Switch neutrality against parent `83e18d15`: **0 of 121 295** quantities differ, probe off and probe on, sweeps and `ifail` unchanged. A24's sensitivity command re-run against this matrix; every tooth bites. |
| 10 | 2026-09-01 | Equivalence gate: **PASS 4 / 4**. Its own sensitivity: **8 of 8** perturbations that must fail, fail. |
| 11 | 2026-09-01 | `a25_module_probe.py`: switch neutrality confirmed, 4 of 4 negative paths raise at import, spec rebuilds exactly on 4 of 4 decks, and the VP2 × VP4 composition is correct across every figure of merit the decks use. `pulse` does **not** join the hoisted tail under the lift — recorded as a finding, not fixed. |
| 12 | 2026-09-01 | δ calibrated on the baseline over 144 runs: **10 %** on all four decks. |
| 13 | 2026-09-01 | H5 campaign: 3 arms × 25 starts × 4 decks = 300 isolated runs at δ = 10 %. **The variant never solves a start the baseline cannot**, and loses 0 / 1 / 2 / 10 starts across the four decks; all 13 `ModuleSolveFailure`s name one field. Cost, paired median: +2.0 % / inconclusive / **−5.1 %** / +16.8 %. The paired VMCON iteration ratio is exactly 1.000 at q1, median and q3 on two decks — **H5's own risk did not materialise**. |
| 14 | 2026-09-01 | Third arm `variant_nohoist` run (D15(b)'s excluding arm), so the hoist's share is measured **inside** the variant: −2.92 / −2.88 / −2.95 / −1.63 %, against A13's flat-arm −6.56 / −6.76 / −6.64 / −2.63 %. On `st_regression` the arm without the hoist has an **identical success set to the baseline** while the hoisted variant loses 2 starts — the hoist's first measured robustness cost. |
| 15 | 2026-09-01 | **Fourth defect, in the analysis rather than the gate.** The I-12 census counted crashed runs' partial MFILEs (parser returns 0 for an absent key) as degenerate entries, reporting 10 on `large_tokamak_eval`, which has none. Restricted to completed runs; corrected count is **0 in 300 runs**, with denominators. |
| 16 | 2026-09-01 | The NaN mechanism measured end to end (`a25_nan_probe.py`): the field goes `0.0 → NaN` inside M1, and `Caller.check_agreement(nan, nan)` returns **True**. |
| 12b | 2026-09-01 | **Provenance note, recorded rather than elided.** During the campaign the two adjacent `from process.core.solver import …` lines in `caller.py` were briefly merged into one and then reverted, so a handful of runs may have imported a source file differing from the rest by that one line. The change is a namespace-identical import restructure: it touches no float, adds no branch, and cannot move any count. Recorded because the practice adopted under I-10 is that every measurement carries its content hash, and the honest form of that here is to say a byte changed and why it cannot matter. Final hashes: `caller.py` `624ebb3e…`, `module_solve.py` `9fb73abe…`. |
| 17 | 2026-09-01 | `DSM_VALIDATION.md` gains **V11** (the three-module partition of the coupling state is exact on all four decks), **V12** (`in_call_models_once` is load-bearing) and **V13** (`Pulse` is feed-forward under the lift but the hoist's classification is static). |
