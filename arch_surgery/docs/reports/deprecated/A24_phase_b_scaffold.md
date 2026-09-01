> **Document status** — **ARCHIVED · FINDINGS CURRENT**
> The task report for A24 (phase-b-scaffold), merged to `architecture_surgery` on 2026-09-01 at
> experiment base commit `c0ae5b28`. **Position in `deprecated/` records lifecycle, not staleness**
> (trap T3). The orchestrator read the `pulse.py` and `subsolve.py` diffs line by line before
> merging and confirms: the arithmetic `(abs(vs)/v) - t_ramp` is moved **verbatim** into
> `burn_time_root`, `calculate_burn_time` keeps its negative-burn-time diagnostic, and `subsolve`'s
> default path is a pure passthrough to `direct(*args)`. D5 and D11/D14(b) are satisfied.
>
> **Its §1 premise correction is the most consequential thing in it** and is now carried in the
> experiment plan: the burn-time site is **not** an inner root-find, so lifting it removes no
> inner-solve work. Any A4/A25 claim of "removing an inner solver" would be false.

# A24 (phase-b-scaffold) — the registry append, the VP5 seam, and the gate harness

| | |
|---|---|
| **Task** | A24 (phase-b-scaffold) — framework steps **F2** (registry append), **F9** (the VP5 pattern and constraint layer) and **F6** (correctness and robustness gates) |
| **Branch** | `A24-phase-b-scaffold`, in the isolated worktree `/home/wrutten/projects/PROCESS_surgery_worktrees/A24-phase-b-scaffold` |
| **Base** | `7a0f3f6e` on `architecture_surgery`; experiment base commit `c0ae5b28` |
| **Governed by** | decisions **D10** (append, never reuse a gap), **D11** and **D14(b)** (the model edit, approved), **D14(a)** (the `lablcc` edit, approved), **D6** (correctness never on iteration variables), **D15** (Phase B experiment design) |
| **Environment** | `PROCESS_surgery_env`; `PYTHONPATH` pinned to this worktree and the **exact** tree asserted per subprocess (trap T6) |
| **Date** | 2026-09-01 |
| **Status** | Complete — **the bundle gate PASSES on all four scenarios**, and was shown capable of failing first |

**Vocabulary, once.** *Iteration variables* are the design variables the optimiser may move; an
input deck selects them by number in its `ixc` list. *Constraints* are selected the same way by
number in `icc`. `lablcc` is the parallel list of human-readable constraint labels the output
writer indexes by constraint number. A *deck* is one `IN.DAT` input file. A *sweep* is one pass
over the model sequence. *VP5* is the experiment framework's fifth variant point: **whether a
model's inner unknown is solved inside the model or handed to the optimiser as a design variable**.
*Bit-identical* means every line of the MFILE output file matches and every quantity the gate
names matches as an exact IEEE-754 double, with **no tolerance applied anywhere**.

---

## 1. Verdict

**All three pieces are built, all three are inert, and the bundle is bit-identical to its parent
commit on all four scenarios.** The bundling premise held: nothing in the bundle changed anything.

| Scenario | MFILE lines differing / compared | MFILE floats differing / compared | Total quantities differing / compared | `ifail` |
|---|---|---|---|---|
| `large_tokamak_nof` | **0** / 16 174 | **0** / 13 559 | **0** / 29 760 | 1 → 1 |
| `low_aspect_ratio_DEMO` | **0** / 16 435 | **0** / 13 455 | **0** / 29 916 | 1 → 1 |
| `st_regression` | **0** / 18 692 | **0** / 13 493 | **0** / 32 206 | 1 → 1 |
| `large_tokamak_eval` | **0** / 15 917 | **0** / 13 487 | **0** / 29 413 | 1 → 1 |

**0 of 121 295** quantities differ across the four scenarios, reported per scenario and never
pooled — the total is given only because the four rows above are the evidence and this is their
sum. The same table with the probe switch **on** gives the same four zeros over the same four
denominators. Sweep counts are unchanged to the unit: 2029 / 4286 / 1891 / 29.

**The gate was shown capable of failing before its zeros were accepted** (protocol §12). One unit
in the last place of one MFILE float is caught on every scenario, as exactly one differing line
and one differing float; one unit in the last place of `norm_objf` or of `sqsumsq` flips the
acceptance predicate to FAIL; a changed `ifail` flips it to FAIL; two genuinely different
scenarios differ in 11 606 of 13 441 shared floats.

**The sensitivity check found a real defect in this task's own harness**, as it did for A3
(build-reorder). The first version of the robustness census keyed its `ifail` histogram on
`str(ifail)`, and the MFILE parser returns `ifail` as a **float** — so it reported
`n_ifail_1 = 0` over four runs that all had `ifail = 1`. Fixed and re-exercised; the fix is
`gates._ifail`, and the synthetic check that catches it is permanent.

**One premise in the brief needs correcting, and the orchestrator should carry it forward.** The
task brief and the framework's §2.5 both describe the VP5 default as *"the existing inner
root-find"*. **At the burn-time site there is no root-find.** `Pulse.run` assigns a **closed-form**
expression, `t_burn = |Vs| / V_loop − t_ramp`, in one statement. Three consequences:

1. The extraction was possible with the arithmetic untouched — the expression moved character for
   character — so D14(b)'s "structural only" condition is met without any judgement call. Had it
   been an iterative solve, re-parameterising it would have been much harder to keep bit-identical
   and the honest answer might have been to stop and report.
2. **Lifting the burn time saves no inner-solve work**, because there is none to save. Whatever
   A4 measures, it is the effect of moving an unknown into the design vector and its residual into
   the constraint set — never the removal of a nested iteration. A report that describes A4's
   result as "removing an inner solver" would be wrong.
3. The framework's VP5 description covers **two different things**: A4's site (a closed-form
   assignment) and A9–A11's sites (genuine inner root-finds, e.g. the H-factor bracket in
   `confinement_time.py`). `subsolve`'s `direct` argument is generic enough for both — it is "the
   model's own solve, whatever that is" — but the *expectation* of a saving is not transferable
   between them. Do not generalise from one to the other.

**One thing the bit-identity gate structurally cannot see**, and which is therefore checked
separately: the extracted residual is never called on the default path, so nothing in the gate
constrains it. It is checked directly — `burn_time_residual(burn_time_root(u), u) == 0.0`
exactly on **100 000 of 100 000** pseudo-random input triples, and non-zero one unit in the last
place away from the root on all 100 000.

---

## 2. What was built

### Piece 1 — F2: iteration variable 178 and constraint 93

| | |
|---|---|
| **Iteration variable 178** | `IterationVariable("t_plant_pulse_burn", "times", 1.0, 1.0e8)` in `process/core/solver/iteration_variables.py` |
| **Constraint 93** | `constraint_equation_93` in `process/core/solver/constraints.py` — `eq(times.t_plant_pulse_burn, burn_time_root(...))`, units `sec` |
| **Its label** | `"Burn time consistency"`, appended to `lablcc` in `process/data_structure/numerics.py` (decision **D14(a)**) |

No new field was invented: `t_plant_pulse_burn` already exists in
`process/data_structure/times_variables.py`. This is the difference from A20 (registry-append),
whose synthetic placeholder needed one and was withdrawn for it.

Measured in the tree rather than inferred (`a24_seam_probe.py`):

| Quantity | At `7a0f3f6e` | At `HEAD` |
|---|---|---|
| iteration variables registered | 83 | **84** |
| highest key / `N_ITERATION_VARIABLES_MAX` | 177 / 177 | **178 / 178** |
| cap derived from `max(keys)` | yes | **yes — not edited** |
| gaps in 1 … highest key | 94 | **94** (no gap consumed) |
| constraints registered / highest id | 82 / 92 | **83 / 93** |
| `len(lablcc)` | 92 | **93** |
| arrays sized by the cap, all grown 177 → 178 | — | **12 of 12** |

The twelve arrays are `ixc`, `lablxc`, `name_xc`, `boundl`, `boundu`, `scale`, `scafc`, `xcm`,
`xcs`, `itv_scaled_lower_bounds`, `itv_scaled_upper_bounds`, `vlam` — checked individually, not
inferred. `initialise_iteration_variables` populates `lablxc[177] = "t_plant_pulse_burn"`,
`boundl[177] = 1.0`, `boundu[177] = 1.0e8` from the registry, with no hand-maintained parallel
list.

Issue **I-7**'s real risk is reusing one of the 94 gaps, which would silently reinterpret an
existing deck. 178 and 93 were taken as allocated in
[`REGISTRY_ALLOCATIONS.md`](../plans/REGISTRY_ALLOCATIONS.md), which is updated in the same commit
per its own rule, and the gap count is unchanged at 94.

Upstream's own parametrised constraint test picks the new constraint up automatically:
`tests/unit/core/test_constraints.py` collects **83** cases here against **82** at the parent, and
the full `tests/unit` suite is **843 passed, 4 skipped**.

### Piece 2 — F9: the VP5 pattern and the constraint layer

`process/core/solver/subsolve.py` (new, 131 lines) holds the variant point:

- `PROCESS_ARCH_LIFT` is parsed **once at import** into `LIFTED_SITES` / `LIFT_ENABLED`; an
  unrecognised site name is an import-time `RuntimeError` naming the bad site, not a silent
  no-op (verified: return code 1, message names `no_such_site`);
- `subsolve(residual, x0, args, *, site, direct)` returns `direct(*args)` on the default path and
  `x0` when the site is lifted.

`process/models/pulse.py` is the **only** file under `process/models/` touched, and the whole diff
is quoted and explained in §6 (docstrings elided there and marked as such; every line of
executable code is quoted verbatim).

### Piece 3 — F6: the gate harness

Three files under `arch_surgery/idf_probe/`, none of them in the solve path:

| File | Role |
|---|---|
| `gates.py` | the reusable gate library — bit identity, the D6 acceptance predicate, the post-solve feasibility audit, matched final accuracy, the `ifail` census across starts, the drop census, and the §12 sensitivity checks. Plus A24's bundle gate as a command |
| `run_a24.py` | the run driver: two arms × four scenarios, fresh subprocess and working directory per run, `PYTHONPATH` pinned, exact tree asserted |
| `a24_seam_probe.py` | what the *code* resolved, as opposed to what the driver asked for: the VP5 selection, the registry state, the residual identity, the deck audit |

**No fourth comparator was written.** `gates.py` imports `compare_a3.compare_pair` unchanged — A3's
sensitivity check found that its first MFILE line parser anchored on the first `(...)` in a line
and silently dropped about a thousand floats per scenario, so the fixed parser is the one to keep
using. `compare_a13.acceptance` was **generalised**, not copied: `gates.acceptance` is that
predicate with the hoist-specific reporting fields lifted into a caller-supplied
`report_fields` list, and with one addition (below).

Two things `gates.py` does that its ancestors did not, both aimed at trap **T11**:

1. **An acceptance quantity absent on both sides is named, not counted.** `norm_objf` is
   legitimately `None` on `large_tokamak_eval`, which is an `fsolve` evaluation run with no
   objective. The predicate reports `quantities_compared = 3` with
   `denominator_acceptance_quantities = 4` and `quantities_void_on_both_sides = ["norm_objf"]`,
   rather than letting a `None == None` inflate a pass.
2. **A ratio cannot be computed without its census.** `cost_comparison(census, …)` takes the drop
   census positionally and echoes it into its own result, so a cost figure structurally carries
   the population it was computed over.

---

## 3. The gate

One gate for the whole bundle: **bit-identity against the parent commit `7a0f3f6e`**, four
scenarios, reported separately.

**Arms.** `parent` is a `git archive` extraction of `7a0f3f6e`, in which none of the three pieces
exists — no `PROCESS_ARCH_LIFT`, no iteration variable 178, no constraint 93. `default` is this
branch with every new switch unset. Each arm is run twice, once with the probe switch unset
(`control`, which the MFILE comparison uses) and once with `PROCESS_IDF_PROBE=baseline` (where the
sweep counts come from).

### 3.1 Bit identity — **PASS 4/4**, probe off and probe on

Three independent comparisons per arm pair, with no tolerance anywhere:

| Scenario | MFILE lines | MFILE floats (hex) | signature fields | raw MFILE fields | total |
|---|---|---|---|---|---|
| `large_tokamak_nof` | 0 / 16 174 | 0 / 13 559 | 0 / 4 | 0 / 23 | **0 / 29 760** |
| `low_aspect_ratio_DEMO` | 0 / 16 435 | 0 / 13 455 | 0 / 4 | 0 / 22 | **0 / 29 916** |
| `st_regression` | 0 / 18 692 | 0 / 13 493 | 0 / 4 | 0 / 17 | **0 / 32 206** |
| `large_tokamak_eval` | 0 / 15 917 | 0 / 13 487 | 0 / 4 | 0 / 5 | **0 / 29 413** |

No key is present in one arm and absent in the other (`mfile_keys_only_in_ref` and
`…_only_in_arm` are empty on all four), so the denominators are not quietly asymmetric. MFILE
floats are compared as **hex float literals** after re-parsing; MFILE lines carry `f"{v:.17e}"`,
18 significant digits, which round-trips an IEEE-754 double exactly. The `parent_probe` versus
`default_probe` pair gives the identical table.

### 3.2 Acceptance (decision D6) — **PASS 4/4**

`norm_objf`, `sqsumsq`, `conf_l2` as hex floats plus `ifail`. **Never iteration variables** — some
are not identified by the problem and differ at an unchanged optimum. They are reported by the bit
comparison beside this table and are not an acceptance quantity.

| Scenario | quantities compared / offered | void on both sides | status |
|---|---|---|---|
| `large_tokamak_nof` | 4 / 4 | — | PASS |
| `low_aspect_ratio_DEMO` | 4 / 4 | — | PASS |
| `st_regression` | 4 / 4 | — | PASS |
| `large_tokamak_eval` | **3 / 4** | `norm_objf` (evaluation run: no objective) | PASS |

### 3.3 Post-solve feasibility audit

The absolute audit the acceptance gate is paired with, from the constraint residual vector at the
returned point. Identical in both arms on every scenario, so the numbers below are one column.

| Scenario | equalities | max abs equality residual | inequalities | min inequality residual | violated |
|---|---|---|---|---|---|
| `large_tokamak_nof` | 3 | 4.47e-09 | 23 | +4.24e-06 | 0 / 23 |
| `low_aspect_ratio_DEMO` | 4 | 2.93e-14 | 21 | +1.27e-11 | 0 / 21 |
| `st_regression` | 3 | 5.02e-14 | 15 | +2.99e-12 | 0 / 15 |
| `large_tokamak_eval` | 2 | 1.25e-12 | 23 | **−0.553** | **3 / 23** |

**`large_tokamak_eval` is infeasible in three inequality constraints, in the baseline, with
`ifail = 1`.** That is not a difference between arms — it is bit-identical in both — and it is not
a defect introduced here. The deck runs in evaluation mode (`i_process_run_mode = -2`, solver
`fsolve`, 2 variables against 2 equalities, 0 solver iterations), so the 23 inequality constraints
are simply never enforced and `ifail = 1` is `fsolve`'s verdict on the two equalities alone.
**The consequence for A4 (burn-time-lift): on that deck the feasibility audit is usable
comparatively but not absolutely, and a gate that reads `ifail` alone would call the point
feasible.** Stated here because the audit is the machinery A4 inherits.

### 3.4 Matched final accuracy — **IDENTICAL 4/4**

Compared at the *achieved* residual, never at the tolerance setting asked for. `sqsumsq` and
`conf_l2` are hex-identical between arms on all four scenarios; the absolute `conf_l2` spread is
exactly 0.0. For an inert bundle this is an identity check; for a real variant it is the condition
without which a cost comparison is unsound, and it is the machinery A4 inherits.

### 3.5 Counts

| Scenario | sweeps | `call_models` | model calls | solver iterations |
|---|---|---|---|---|
| `large_tokamak_nof` | 2029 → 2029 | 630 → 630 | 2029 → 2029 | 8 → 8 |
| `low_aspect_ratio_DEMO` | 4286 → 4286 | 1240 → 1240 | 4286 → 4286 | 16 → 16 |
| `st_regression` | 1891 → 1891 | 570 → 570 | 1891 → 1891 | 10 → 10 |
| `large_tokamak_eval` | 29 → 29 | 11 → 11 | 29 → 29 | 0 → 0 |

These reproduce A20 (registry-append)'s sweep counts exactly, which is a determinism statement
across two independent tasks and two different sets of `process/` edits.

### 3.6 Robustness — built, and exercised at **n = 1 per scenario per arm**

The `ifail` census and the drop census are built and run, and the honest denominator is stated
plainly: **each scenario contributes one start** — the deck's own point — so the census is
`n_starts = 1` per arm, `ifail = 1`, `1 of 1` kept, `0` degenerate entries. That is **not** a
robustness result and must not be quoted as one. Multi-start robustness is A4's measurement under
decision D15; what A24 delivers is the machinery, exercised for correctness on synthetic sets
where every outcome can be constructed (§4).

The census records net electric power per start, because issue **I-12** requires the count of
degenerate starts beside every cost figure. `arch_surgery/idf_probe/metrics.py` gained
`p_plant_electric_net_mw` for this — without it the flag could never fire. At their own start
points the four decks give +400.0, +350.0, +105.4 and +385.3 MW, so none is degenerate; D15's
perturbed starts are where this will bind.

---

## 4. Showing the gate can fail (protocol §12)

Every check below uses the **production predicate unmodified**.

| Check | Perturbation | Result | Denominator |
|---|---|---|---|
| Bit comparator | 1 ULP on `(rmajor)` in the MFILE, `large_tokamak_nof` | FAIL, **exactly 1** differing line and **1** differing float | 16 174 lines, 13 559 floats |
| Bit comparator | same, `low_aspect_ratio_DEMO` | FAIL, 1 / 1 | 16 435 lines, 13 455 floats |
| Bit comparator | same, `st_regression` | FAIL, 1 / 1 | 18 692 lines, 13 493 floats |
| Bit comparator | same, `large_tokamak_eval` | FAIL, 1 / 1 | 15 917 lines, 13 487 floats |
| Bit comparator | two genuinely different scenarios | FAIL, **11 606** differing | 13 441 shared floats |
| Acceptance (D6) | 1 ULP on `norm_objf` | PASS → **FAIL**, 3 of 3 scenarios that have an objective | 4 acceptance quantities |
| Acceptance (D6) | 1 ULP on `sqsumsq` | PASS → **FAIL**, 4 of 4 | 4 acceptance quantities |
| Acceptance (D6) | `ifail` 1 → 2 | **FAIL**, 4 of 4 | 4 acceptance quantities |
| Drop census | five synthetic starts: one clean, one crashed, one `ifail = 5`, one `norm_objf` off by 1 ULP, one with negative net electric power | `{crashed: 1, ifail_not_1: 1, objf_mismatch: 1, kept: 2}` and `1` degenerate flag | 5 starts offered |
| Drop census, null case | two identical arms | `{kept: 5}` — invents no drop | 5 starts offered |
| `ifail` census | float-keyed input, all successes | `n_ifail_1 = 5` | 5 starts |
| `ifail` census | mixed input | `n_ifail_1 = 3`, `n_crashed = 1` | 5 starts |
| Residual identity | at the root, and 1 ULP off it | 0 non-zero at root, 0 blind one ULP off | 100 000 input triples |

**The `ifail` census rows are the ones that earned their keep.** They were added *after* the
first sensitivity run showed `n_ifail_1 = 0` beside a histogram reading `{"1.0": 1}` — a
histogram keyed on `str(float)` against a lookup keyed on `"1"`. Had the gate not been exercised,
A4 would have inherited a robustness census that reports zero successes for every successful
start. This is the second time in this project that a §12 sensitivity check has found a defect in
the comparator of the task that wrote it.

The `norm_objf` row reads *3 of 3 scenarios that have an objective*: `large_tokamak_eval` reports
`norm_objf ABSENT` and `detected: null`, which is a stated exclusion rather than a silent pass.
Its acceptance predicate is exercised by the `sqsumsq` and `ifail` rows instead.

---

## 5. Switch-neutrality of the new seams specifically

Bit-identity says the *results* did not move. It does not by itself say the new machinery was
unreachable rather than reachable-and-lucky. Four separate statements, each measured:

1. **The VP5 seam resolved to nothing.** Every run records what the imported module resolved, not
   what the environment asked for. `default` and `default_probe` report
   `arch_lift_sites = []` with `arch_lift_known_sites = ["burn_time"]`; `parent` and
   `parent_probe` report `arch_lift_module_present = false`, i.e. the module does not exist there
   at all. 4 arms × 4 scenarios, no arm lifted a site.
2. **The seam is a call-through when nothing is lifted.** `subsolve` was called against
   `Pulse.calculate_burn_time` on **20 000 of 20 000** pseudo-random input quadruples and returned
   the model's own value every time, and the design-vector value **0** times. Under
   `PROCESS_ARCH_LIFT=burn_time` the same 20 000 inputs invert exactly: 0 call-throughs, 20 000
   design-vector values. The claim is measured against its own counterfactual rather than argued
   from the source.
3. **No deck names the appended entries.** Counted from the four `IN.DAT` files rather than
   assumed: **0 of 4** name `ixc = 178` or `icc = 93`, over 26 / 25 / 18 / 25 constraints and
   20 / 19 / 14 / 2 iteration variables named. And no run activated it: `t_plant_pulse_burn` does
   not appear in any arm's `itvar_names`, on any scenario.
4. **A wrong arm is loud.** `PROCESS_ARCH_LIFT=no_such_site` raises at import with a message
   naming the offending value. A misspelled arm that quietly runs the baseline is the failure mode
   that makes a whole campaign worthless, so it is an error rather than a default.

The one residual gap, stated rather than papered over: the appended constraint widens
`set_active_constraints`' loop in `process/core/init.py` from 82 to 83 slots, because that loop is
bounded by **registry size** rather than by the deck's constraint count. `icc` is 500 long and
zero-filled and our decks name 18–26 constraints, so the extra iteration reads a zero and counts
nothing — which the bit-identity gate confirms empirically. This is the latent PROCESS defect A20
(registry-append) found and reported; A24 re-encounters it and changes nothing about it.

---

## 6. The diff to `process/models/pulse.py`, line by line

This is the **only** edit under `process/models/` in the whole experiment, and decision **D14(b)**
approves it structurally: the expression is unchanged and its *solution method* becomes a driver
choice. Four hunks.

### 6.1 One import

```python
+from process.core.solver.subsolve import SITE_BURN_TIME, subsolve
```

The model gains a dependency on the driver's variant-point module. `subsolve.py` imports only
`os`, so this creates no cycle: `constraints.py → pulse.py → subsolve.py` terminates. Verified by
import, not by inspection.

### 6.2 Two module-level functions, inserted before `class Pulse`

Preceded by a 22-line banner comment stating why they exist and that the expression is unchanged.

```python
+def burn_time_root(
+    vs_cs_pf_total_burn: float,
+    v_plasma_loop_burn: float,
+    t_plant_pulse_fusion_ramp: float,
+) -> float:
+    """[numpydoc docstring, 19 lines, elided here]"""
+    return (
+        abs(vs_cs_pf_total_burn) / v_plasma_loop_burn
+    ) - t_plant_pulse_fusion_ramp
```

**This is the original expression, moved, character for character.** It is the whole of what
`Pulse.calculate_burn_time` computed at `7a0f3f6e`:

```python
        t_plant_pulse_burn = (
            abs(vs_cs_pf_total_burn) / v_plasma_loop_burn
        ) - t_plant_pulse_fusion_ramp
```

The same three operations in the same order on the same three operands, so the same double comes
out. Nothing was reassociated, no intermediate was introduced, no `abs` moved. *Why it is separate
from `calculate_burn_time`:* the constraint layer must evaluate this relation on every solver call,
and `calculate_burn_time` emits a `logger.error` when the result is negative. That diagnostic is a
reporting side effect of the *model call*, not part of the relation; routing the constraint through
`calculate_burn_time` would have turned every infeasible trial point into a log line. The
diagnostic stays exactly where it was, on the model path.

```python
+def burn_time_residual(
+    t_plant_pulse_burn: float,
+    vs_cs_pf_total_burn: float,
+    v_plasma_loop_burn: float,
+    t_plant_pulse_fusion_ramp: float,
+) -> float:
+    """[numpydoc docstring, 19 lines, elided here]"""
+    return t_plant_pulse_burn - burn_time_root(
+        vs_cs_pf_total_burn,
+        v_plasma_loop_burn,
+        t_plant_pulse_fusion_ramp,
+    )
```

New code, computing nothing the model computed before: it is the *residual form* of the same
relation, and it exists because a lifted unknown needs one. It is what constraint equation 93
means, and it is what an iterative arm would root-find. It is called on **no** path a default run
takes, which is why §1's separate identity check exists — the bit-identity gate cannot see it.

### 6.3 The assignment in `Pulse.run` routes through the seam

```python
-            #  Burn time calculation
-
-            self.data.times.t_plant_pulse_burn = self.calculate_burn_time(
-                vs_cs_pf_total_burn=self.data.pf_coil.vs_cs_pf_total_burn,
-                v_plasma_loop_burn=self.data.physics.v_plasma_loop_burn,
-                t_plant_pulse_fusion_ramp=self.data.times.t_plant_pulse_fusion_ramp,
+            #  Burn time calculation.  VP5 seam: with `PROCESS_ARCH_LIFT`
+            #  unset this calls `calculate_burn_time` with exactly the
+            #  arguments the straight-line assignment it replaced used, and
+            #  assigns exactly what that assignment assigned.  With
+            #  `burn_time` lifted, the burn time is a design variable and this
+            #  returns it untouched, leaving constraint equation 93 to enforce
+            #  the relation.
+
+            self.data.times.t_plant_pulse_burn = subsolve(
+                burn_time_residual,
+                self.data.times.t_plant_pulse_burn,
+                (
+                    self.data.pf_coil.vs_cs_pf_total_burn,
+                    self.data.physics.v_plasma_loop_burn,
+                    self.data.times.t_plant_pulse_fusion_ramp,
+                ),
+                site=SITE_BURN_TIME,
+                direct=self.calculate_burn_time,
             )
```

Read the default path straight through: `LIFT_ENABLED` is `False`, so `subsolve` returns
`direct(*args)`, which is `self.calculate_burn_time(vs_cs_pf_total_burn, v_plasma_loop_burn,
t_plant_pulse_fusion_ramp)` — the same function on the same three values, positionally instead of
by keyword. The assignment target is unchanged. `calculate_burn_time` is a `@staticmethod`, so
`self.calculate_burn_time` is the plain function and no bound-method object is created.

The second argument is `x0`, the unknown's current value: on the default path it is ignored, and
on the lifted path it is the value the optimiser placed in `times.t_plant_pulse_burn` and is
returned untouched. Passing it in from the data structure — rather than from a separate lifted
store — is what makes the lifted path a one-line change rather than a plumbing exercise for A4.

**What this costs on the default path:** one Python function call and one three-element tuple per
`Pulse.run`, i.e. per sweep on a pulsed deck. It touches no float and changes no control flow, and
the bit-identity gate covers the result. Stated rather than elided, because the framework's §3.3
invariant is *"no hook allocates"* and this one allocates a tuple; the honest form of the invariant
here is *no hook touches a float or changes a branch a result depends on*.

### 6.4 `calculate_burn_time` now calls the extracted root

```python
-        t_plant_pulse_burn = (
-            abs(vs_cs_pf_total_burn) / v_plasma_loop_burn
-        ) - t_plant_pulse_fusion_ramp
+        t_plant_pulse_burn = burn_time_root(
+            vs_cs_pf_total_burn,
+            v_plasma_loop_burn,
+            t_plant_pulse_fusion_ramp,
+        )
```

Its signature, its docstring, its negative-burn-time `logger.error` and its return are all
unchanged. Upstream's own `tests/unit/models/test_pulse.py::test_calculate_burn_time_valid` calls
it directly and passes.

**What the diff does not do.** It does not change any number the model computes, does not add or
remove a state write, does not touch `tohswg`, `PulseTimings`, or the `i_pulsed_plant` guard, and
does not make `Pulse` feed-forward — `pulse` remains inside the idempotence loop and inside
`caller.py`'s `DEFERRABLE_NODES`, exactly as at `7a0f3f6e`. The framework's C2a note that `Pulse`
joins the feed-forward tail *once the coupler is lifted* still requires a lift, and no lift is
selected here.

---

## 7. Autonomous decisions, with reversal paths

**AD1 — Default bounds for iteration variable 178 are `(1.0, 1.0e8)`.**
The registry entry needs default bounds and nothing specified them. The upper bound is the range
`process/core/input.py` already accepts for `t_plant_pulse_burn`. The lower bound is 1 second
rather than 0: an iteration variable is scaled by its own initial value and a zero-length flat-top
is not a design point, so a zero lower bound is a hazard with no benefit. Both are **defaults an
input deck overrides** with `boundl` / `boundu`, so A4 is not bound by them.
*Reversal:* one line in `iteration_variables.py`; nothing else reads the numbers.

**AD2 — Constraint 93 recomputes the relation rather than reading a value recorded by
`subsolve`.**
The framework's §2.5 step 3 says `subsolve` "records the residual for the constraint layer". A
recorded residual is order-dependent — it is only valid if the constraint is evaluated after the
sweep that produced it — whereas recomputing from the data structure is stateless and correct
whenever the constraint is called. The relation is not duplicated: both paths call the same
`burn_time_root`.
*Reversal:* add a module-level slot in `subsolve.py`, write it on the lifted path, read it in
constraint 93. Two hunks; the current form is a strict subset of what that would need.

**AD3 — The VP5 seam lives in `process/core/solver/subsolve.py`, not in a consolidated
`_experiment.py`.**
The framework names `_experiment.subsolve`, but `_experiment.py` is framework item **F1**, which
§3.1 places explicitly *after* Phase A and which no queued task has done. Building it here would
have merged three probe modules and re-gated their neutrality inside a task whose gate is about
something else. `process/core/solver/` is inside `CLAUDE.md`'s default-permitted surface, and the
variant point is a solver decision.
*Reversal:* F1 moves the module's contents into `_experiment.py` and changes one import line in
`pulse.py`.

**AD4 — `arch_surgery/idf_probe/metrics.py` records `p_plant_electric_net_mw`.**
Issue I-12 obliges Phase B to report the count of degenerate starts beside every cost figure, and
the drop census cannot flag what is not recorded. Additive: the field is not in any gate's
comparison set, and `exact_signature`'s raw-field set is unchanged, so no existing comparison
changes shape.
*Reversal:* remove one tuple entry.

**AD5 — `run_one.py` records the resolved VP5 arm.**
Following the pattern A3 and A13 established for VP1 and VP2: read from the imported module, not
from the environment, so a tree predating the variant point reports `None` rather than echoing the
arm the driver asked for. Guarded with `try: import … except ImportError`, so the `parent` arm —
where the module does not exist — records `arch_lift_module_present: false`.
*Reversal:* delete one block; no other script requires the keys.

**AD6 — The robustness gate was exercised on synthetic starts, not on a real multi-start
campaign.**
D15 calibrates the perturbation size δ on the baseline and runs the multi-starts; that is A4's
measurement and it is not scaffolding. Running a small campaign here would have produced numbers
that look like a robustness result and are not one. Instead the census is exercised on constructed
sets where every outcome — crash, `ifail ≠ 1`, objective mismatch, degenerate entry, and the null
case — can be checked against a known answer. That is what found the `ifail` histogram defect.
*Reversal:* none needed; A4 supplies real starts to the same functions, which read
`runs/<scenario>/<arm>/start<k>/metrics.json` and fall back to a single start named `start000`.

**AD7 — Two new gate files rather than one, and no fourth `compare_*.py`.**
`gates.py` is the library plus A24's command; `run_a24.py` is the driver; `a24_seam_probe.py` is
the code-state probe. The comparator itself is imported from `compare_a3.py`, unchanged, per the
brief.
*Reversal:* n/a.

---

## 8. What I did not do

- **No lift was run.** `PROCESS_ARCH_LIFT=burn_time` exists, imports, and inverts the seam's
  behaviour on 20 000 synthetic inputs, but **no scenario was solved with it**. A deck naming
  `ixc = 178` / `icc = 93` does not exist and building one is A4's work. Nothing in this report
  says anything about whether the lift solves, converges, or costs less.
- **No `caller.py` change**, and therefore no VP1/VP2/VP3/VP4 work. `pulse` is still in the loop.
- **No multi-start campaign**, no δ calibration (D15(a)), no cost figure of any kind.
- **A20's live-deck demonstration was not repeated.** Its supplementary check that the (178, 93)
  mechanism works end to end stands on its own record; repeating it would need a synthetic deck of
  exactly the kind the user ruled out.
- **A20's input-language divergence measurement was not repeated.** It is one-way and recorded in
  the allocation table; nothing about A24's numbers changes it. Note it now applies to a **real**
  variable: a deck naming `ixc = 178` here is refused by upstream at input-parse time.
- **`MASTER_TODO.md` was not edited.** It is the orchestrator's file, and its registry-state lines
  ("Iteration variables … `N_ITERATION_VARIABLES_MAX = 177` … **none** free") are now stale. Flagged
  rather than fixed, per protocol §1 and §10.
- **No timing is cited as evidence anywhere in this report.** The gate matrix took 177.5 s of
  wall clock with four parallel jobs; that number carries no argument and appears here only so a
  reader knows the reproduction cost.
- **Nothing was added to `DSM_VALIDATION.md`.** Nothing was found wrong with the dependency
  analysis in the course of this task.

---

## 9. Things noticed, not fixed

- **`ruff` is still not installed in `PROCESS_surgery_env`**, so the repository's linter and
  formatter could not be run over the changed files. A20 (registry-append) flagged the same thing.
  The diff follows the surrounding style by inspection. The fix is an environment change and is
  therefore the user's to make:
  `conda install -n PROCESS_surgery_env -c conda-forge ruff`.
- **`set_active_constraints`' loop bound** (§5). The PROCESS defect A20 found; unchanged, and now
  reachable by one more slot.
- **`lablxc`'s docstring is stale in upstream** — it lists `(174) NOT USED` and `(175) NOT USED`
  where the registry has `174: triang` and `175: kappa`, and 176/177 are absent from the list.
  Only the `(178)` line was added, as A20 did; correcting upstream's existing entries would
  enlarge the diff against upstream for no experimental gain.
- **`large_tokamak_eval` is infeasible in 3 of 23 inequality constraints at its own solution**
  (§3.3), because it is an evaluation run. Identical in both arms and not caused by anything here,
  but A4 needs to know before it reads a feasibility audit on that deck.

---

## 10. Reproduction

```bash
# reference: a git archive of this branch's parent commit
git archive 7a0f3f6e -o $TMPDIR/parent.tar
mkdir -p $TMPDIR/parent_7a0f3f6e && tar -xf $TMPDIR/parent.tar -C $TMPDIR/parent_7a0f3f6e

cd arch_surgery/idf_probe
PY=/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python

# 2 arms x 2 probe modes x 4 scenarios, plus the two seam probes.
$PY run_a24.py --parent-tree $TMPDIR/parent_7a0f3f6e --runs $PWD/runs/a24 --jobs 4

# the bundle gate, then its teeth
$PY gates.py gate        --runs $PWD/runs/a24
PYTHONPATH=$PWD/../.. $PY gates.py sensitivity --runs $PWD/runs/a24
```

`run_a24.py` sets `PYTHONPATH` to this worktree for every subprocess, and both `run_one.py` and
`a24_seam_probe.py` assert the **exact** tree they imported rather than a path prefix — trap T6,
without which a worktree silently measures the main checkout. The sensitivity run needs
`PYTHONPATH` itself because its residual-identity check imports `process.models.pulse`.

Raw artifacts land in `arch_surgery/idf_probe/runs/a24/` and stay untracked; the numbers above are
the committed summary. The gate's own output is `runs/a24/_gates_a24.json` and
`runs/a24/_gate_sensitivity_a24.json`.

---

## 11. Change log (append-only)

| # | Date | Change |
|---|---|---|
| 1 | 2026-09-01 | Worktree confirmed at `7a0f3f6e` on `A24-phase-b-scaffold`, `arch_surgery/` present. Governing documents read. |
| 2 | 2026-09-01 | Found that the burn-time site is a **closed-form** solve, not an inner root-find. Extraction is therefore residual + root, and the seam's default path is a call-through rather than a re-parameterised root-finder. No arithmetic change was needed, so D14(b)'s "structural only" condition is met without compromise. |
| 3 | 2026-09-01 | `process/core/solver/subsolve.py` added: VP5 variant point, `PROCESS_ARCH_LIFT`, resolved once at import, unrecognised value is an import-time error. |
| 4 | 2026-09-01 | `process/models/pulse.py`: residual and root extracted, `Pulse.run` routed through `subsolve`, `calculate_burn_time` calls the root. Four hunks; §6. |
| 5 | 2026-09-01 | Iteration variable 178 (`t_plant_pulse_burn`) appended; constraint 93 registered; `lablcc` extended in step (D14(a)); two enumerating docstrings extended. |
| 6 | 2026-09-01 | Registry state checked in the tree: cap 177 → 178 by its own `max(keys)`, twelve arrays grown, gap count unchanged at 94, `lablcc` 93. |
| 7 | 2026-09-01 | Gate harness built: `gates.py` (library + command, reusing `compare_a3.compare_pair` unchanged), `run_a24.py`, `a24_seam_probe.py`. `metrics.py` gained `p_plant_electric_net_mw` (AD4); `run_one.py` records the resolved VP5 arm (AD5). |
| 8 | 2026-09-01 | Seam probe run in both lift arms: default path is a call-through on 20 000/20 000 inputs, lifted path returns the design-vector value on 20 000/20 000, residual identity 100 000/100 000, no deck names 178 or 93. |
| 9 | 2026-09-01 | Gate matrix run: 4 arms × 4 scenarios, fresh subprocess and working directory each. Bit identity PASS 4/4 probe off and probe on. |
| 10 | 2026-09-01 | Sensitivity run. **Defect found in this task's own `ifail` census** — histogram keyed on `str(float)`, so `n_ifail_1` was 0 over four successful runs. Fixed (`gates._ifail`), a permanent synthetic check added, gate re-run. |
| 11 | 2026-09-01 | `tests/unit`: 843 passed, 4 skipped. `test_constraints.py` collects 83 cases against the parent's 82, so upstream's own parametrised test exercises constraint 93. |
| 12 | 2026-09-01 | `REGISTRY_ALLOCATIONS.md` updated in the same commit as the append, per its own rule: F2 ALLOCATED to A24 for A4's use, next free 179 / 94, A20's withdrawal history preserved. |
