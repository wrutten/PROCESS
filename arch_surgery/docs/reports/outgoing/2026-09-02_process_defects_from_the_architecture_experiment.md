# Five defects in PROCESS, found while re-architecting its solver driver

**Found:** `PROCESS_surgery` — a fork of PROCESS in which the *arrangement of solvers* is changed
while every physics and engineering model is left exactly as upstream wrote it. All five were
found as by-products of that experiment, not by looking for bugs.
**Study commit:** PROCESS **`c0ae5b28`**, the `PROCESS_surgery` base commit. Every line number
below is a line number *at `c0ae5b28`*, and every count was measured at `c0ae5b28`.
**Status:** **REPORTED, NOT PATCHED.** Nothing has been changed in any tree. `PROCESS_surgery`
freezes the models and the base commit, so these are findings, not fixes.
**Filed here rather than written into `PROCESS_code_analysis` directly** because
`PROCESS_surgery`'s `CLAUDE.md` forbids writing into a sibling clone. Move or copy as you see fit.

**Supersession.** This document **supersedes**
[`2026-09-01_call_models_equal_nan_converged.md`](2026-09-01_call_models_equal_nan_converged.md)
in this directory. That report covered defect **A** below and is correct in its central claim;
§A here carries it forward with two additions and **one correction to its blast-radius argument**.
If you have already filed the earlier document, keep it and read §A as an amendment; if you have
not, file this one instead. Nothing else in this report was in that one.

**Three line numbers in that earlier report are wrong**, and are corrected here. Verified at
`c0ae5b28` for this document: the `MDA_Output` NaN default `mfile_data.get(var, np.nan)` is at
**`caller.py:192`** (it said 204), the `check_agreement` call beneath it at **`:193`** (it said
205), and the `RuntimeError` the loop would raise at **`:129`** (it said 140). Its citations of
`check_agreement` itself — `caller.py:51-72` and the `equal_nan` line at `:70` — are correct.

---

## 0. What is being handed over

Five findings about upstream PROCESS itself, as opposed to about its architecture. The
architecture critique stays in `PROCESS_surgery`; this is the part that is a property of the code
as shipped and would affect any user.

| | Defect | Class | Where | How we met it |
|---|---|---|---|---|
| **A** | The idempotence loop's stopping test reports a "not a number" state as converged | **certainly a bug** | `process/core/caller.py:70` | reproduced deliberately (our control arm is PROCESS as shipped) |
| **B** | That stopping test's tolerance is not `1e-6` relative; `numpy`'s default absolute term dominates below `1e-2` | **an undocumented consequence of a library default** | `process/core/caller.py:70` | measured, and it forced a design decision on us |
| **C** | The 1990 cost model returns `coe ≈ 6.6 × 10²¹` at negative net electric power, because a guard against `kwhpy = 0` clamps a *negative* denominator to `1e-10` | **a deliberate guard with an undocumented consequence** | `process/models/costs/costs.py:2751` | our experiment was affected by it — it inflated an acceptance quantity |
| **D** | Which constraints are equalities is decided by **position in the input deck**, not by anything about the constraints | **certainly a bug, and the one most likely to bite another user** | `process/core/input.py:44`, `process/core/solver/constraints.py:1958`, `process/core/solver/solver_handler.py:72` | we walked into it, and it produced a plausible false result that a gate caught |
| **E** | Two loops in `process/core/init.py` are bounded by something other than the deck's constraint count | **certainly bugs, both latent on our decks** | `process/core/init.py:306` and `:1277` | found by reading, while appending a registry entry |

Throughout, **"deck"** means a PROCESS input file (`IN.DAT`) plus the scenario it describes. Our
four are `large_tokamak_nof`, `low_aspect_ratio_DEMO`, `st_regression` and `large_tokamak_eval`,
taken unmodified from `tests/regression/input_files/`. **"The loop"** or **"the idempotence
loop"** means `Caller.call_models`, which re-runs the whole model sequence until the objective and
the constraint vector stop changing. **`A20`, `A22`, `A24`, `A25`** are numbered tasks in our
queue; each has a written report and its numbers are quoted here with their denominators.

---

## A. The stopping test reports a "not a number" state as converged

### A.1 What we measured

`process/core/caller.py:51-72` at `c0ae5b28`:

```python
    @staticmethod
    def check_agreement(previous, current) -> bool:
        ...
        # Check for same shape: mfile length can change between iterations
        if isinstance(previous, float) or previous.shape == current.shape:
            return np.allclose(previous, current, rtol=1.0e-6, equal_nan=True)
        return False
```

`equal_nan=True` makes `np.allclose` treat NaN as equal to NaN. A quantity that has become NaN
stays NaN — nearly every arithmetic operation propagates it — so a NaN state compares equal to
itself on the next sweep and the loop returns **"converged"**. A NaN that is *stable* is the
easiest possible case for this predicate to pass.

Three independent confirmations, all direct rather than inferred:

1. **The library semantics**, checked in the study environment:
   `np.allclose(nan, nan, rtol=1e-6, equal_nan=True)` → `True`;
   `np.allclose(1.0, nan, rtol=1e-6, equal_nan=True)` → `False`.
2. **The method itself, on a real state.** Task **A25** wrapped its residual evaluator and
   recorded a state in which `current_drive.eta_cd_dimensionless_hcd_primary` went `0.0 → NaN`
   inside the first module sweep and stayed NaN. Called on that state:
   ```
   Caller.check_agreement(nan_state, same_nan_state)  ->  True
   Caller.check_agreement(finite_state, nan_state)    ->  False
   ```
3. **Present unchanged at your pin.** Your orchestrator confirmed on 2026-09-01, reading
   `PROCESS_at_36ac820e`, that the line is present unchanged at `caller.py:70` and is the only
   `equal_nan` in the file.

**A second route into the same hole**, at `caller.py:192`, inside `MDA_Output` — the *other*
convergence loop, the one that compares successive `MFILE`s variable by variable:

```python
current_value = mfile_data.get(var, np.nan)
```

A variable present in the previous MFILE and **absent from the current one** defaults to NaN.
Combined with `equal_nan=True`, a variable that was NaN last sweep and then disappears entirely
compares NaN-to-NaN and counts as agreeing. The complementary case is handled correctly: a
variable that was finite and then disappears compares finite-to-NaN and is reported as
non-converged. `MDA_Output` has no predicate of its own — `caller.py:192` onwards calls the same
`self.check_agreement` — so both convergence loops share one predicate and one loophole.

### A.2 Correction to the earlier report — the blast radius is narrower than we said

The 2026-09-01 report argued that a NaN reaching `call_models` is handed to VMCON as objective
**and constraints**, and that a NaN at a finite-difference stencil point contaminates a whole
gradient column. **The constraint half of that is wrong, and we are correcting it here rather
than letting you find it.**

`call_models` builds its constraint vector by calling `constraints.constraint_eqns`
(`process/core/solver/constraints.py:1958`), which contains, at `:1997`:

```python
if np.isnan(tmp_cc) or np.isinf(tmp_cc) or abs(tmp_cc) > 9.99e99:
    raise ProcessValueError(f"Constraint equation {constraint_id} returned an invalid residual")
```

`tmp_cc` is the normalised residual, and the returned vector entry is exactly `-tmp_cc`. So a NaN
in a constraint entry **raises before `check_agreement` ever sees it**. The predicate's NaN
loophole cannot be reached through the constraint vector.

It is reachable through the other two paths, and neither has a guard:

- **The objective.** `objective_function` (`process/core/solver/objectives.py:11`) selects one of
  fifteen figures of merit and returns it with no finiteness check on any branch. A NaN objective
  reaches `check_agreement`, passes, and is returned to `Evaluators.fcnvmc1`.
- **`MDA_Output`'s MFILE comparison**, per §A.1 — and that is the loop whose result is reported
  to the user.

The correction narrows the finding; it does not remove it.

### A.3 What we did **not** establish

**We have never observed this defect change a PROCESS result, and we are not claiming that it
has.** Two measurements bound that statement rather than merely hedging it:

- Across four scenarios instrumented at `c0ae5b28`, the loop's own non-convergence counter is
  **`0`** on all four: the loop never reports failure, and no NaN was seen in any objective or
  constraint vector on any case (`n` = 2 027, 4 284, 1 889 and 30 objective evaluations; 52 728,
  107 125, 34 020 and 200 constraint-vector entries respectively).
- **A25** ran a stricter predicate as an experimental arm and found **13 starting points, out of
  300 runs, where the strict arm refused to converge and stock PROCESS succeeded.** The obvious
  reading — that stock PROCESS was exiting over a NaN at those 13 — was checked and **refuted from
  the artifacts**: on **13 of 13**, the baseline's final MFILE is entirely finite, **0 non-finite
  of 13**. The non-finiteness detector was shown capable of firing first: it flags **9 of the 300
  retained MFILEs**, all on `large_tokamak_nof` starts 014 and 017, which are starts *both* arms
  crash on.

So: the loophole is real and measured on the predicate; **no run of upstream PROCESS in our
records has been observed to exit the loop over a NaN state.** What makes it worth reporting is
the *direction* of the failure, not an observed instance — it converts a loud failure into a
quiet one.

### A.4 Whether our experiment worked around it

**We reproduced it deliberately.** Our control arm is PROCESS as shipped, so it reproduces
`check_agreement`'s defects in full, by an explicit written decision. Our *variant* arm's
predicate scores a non-finite component as infinitely far from agreement and refuses to converge —
which is what produced the 13 refusals in §A.3, and is the documented inverse of this loophole.
That asymmetry is load-bearing for how you read our evidence: the strict arm is the instrument
that made the loophole visible, and it is not upstream behaviour.

### A.5 The one-word fix, and why it is not applied here

```python
return np.allclose(previous, current, rtol=1.0e-6, equal_nan=False)   # or omit the kwarg
```

`equal_nan=False` is `np.allclose`'s default, so removing the keyword suffices. A NaN state would
then fail agreement, the loop would exhaust its cap of 10 sweeps, and `call_models` would raise
the `RuntimeError` it already has at `caller.py:129` — behaviour that is already written and is
the correct one. `PROCESS_surgery` does not apply it because its base commit is frozen as a shared
coordinate system with two sibling studies, and because a change to this predicate is the
independent variable of the experiment being run there.

---

## B. The stopping test's tolerance is not `1e-6`, and for part of the state it is unconditional

### B.1 What we measured

`np.allclose(a, b, rtol=1.0e-6)` does not test a relative tolerance. It tests

```
|a - b|  <=  atol + rtol * |b|          with numpy's default atol = 1e-8
```

so the **absolute** term dominates whenever `|b| < atol/rtol = 1e-2`. Below that crossover the
test is effectively absolute at `1e-8`, which in relative terms is **looser**, not tighter:

| `\|x\|` | effective relative tolerance |
|---|---|
| 1e-6 | **1.0e-2** |
| 1e-4 | **1.0e-4** |
| 1e-3 | 1.1e-5 |
| 1e-2 | 2.0e-6 |
| ≥ 1 | 1.0e-6 |

Below `1e-8` the absolute term exceeds any possible difference, and **agreement is
unconditional**: no change whatever can fail the test.

**How much of the state this reaches — two populations, each with its denominator.**

*(i) The reported state.* Counted from `large_tokamak_nof`'s MFILE only — **11 191 numeric
entries, of which 10 813 are nonzero.** The MFILE set is exactly what `MDA_Output` compares, so
this is on-target for that loop rather than an analogy. **This is one deck's MFILE and should not
be read as a figure for PROCESS in general.**

| band | count | share of the 10 813 nonzero |
|---|---|---|
| `< 1e-8` — **agreement is unconditional** | **203** | 1.9 % |
| 1e-8 … 1e-6 | 10 | 0.1 % |
| 1e-6 … 1e-4 | 120 | 1.1 % |
| 1e-4 … 1e-2 | 1 614 | 14.9 % |
| **total below the 1e-2 crossover** | **1 947** | **18.0 %** |
| ≥ 1e-2 (tolerance is genuinely ~1e-6 relative) | 8 866 | 82.0 % |

*(ii) The constraint vectors the idempotence loop actually compares.* Every constraint vector
evaluated inside the loop during one full optimisation run of each deck; `n` is the number of
individual entries, and there are no zeros in any of them.

| deck | `n` entries compared | ≤ 1e-8 — unconditional | below the 1e-2 crossover |
|---|---|---|---|
| `large_tokamak_nof` | 52 728 | 892 = **1.7 %** | 17 563 = **33.3 %** |
| `low_aspect_ratio_DEMO` | 107 125 | 20 342 = **19.0 %** | 55 252 = **51.6 %** |
| `st_regression` | 34 020 | 2 084 = **6.1 %** | 11 462 = **33.7 %** |
| `large_tokamak_eval` | 200 | 22 = **11.0 %** | 68 = **34.0 %** |

On `low_aspect_ratio_DEMO`, **19 % of every constraint value that loop compares, over 107 125
comparisons in one run, is small enough that the test reports agreement no matter what the value
does** — and more than half are in the regime where the absolute term rather than the relative
term decides. The hole is larger in the loop's own set than in the reported set.

### B.2 What we infer

The reproducibility floor of PROCESS's convergence test is **magnitude-dependent, not a single
number at `1e-6`**. For a quantity at `1e-4` the effective relative tolerance is `1e-4` — two
orders of magnitude looser than the constant in the source suggests. This matters most where a
tight optimiser tolerance is being asked to resolve quantities whose agreement floor sits far
above it.

We also measured the spread of the underlying quantities directly, over the continuous components
of the model state, per deck: **2.4 × 10⁻²² to 9.1 × 10²¹, about 43 orders of magnitude**, with
2 to 6 components per deck (of 694, 698, 582 and 285 continuous components respectively) whose
working magnitude is *below* `1e-8`, and 5–7 % below `1e-2`. A single absolute tolerance is not
defensible on a set with that spread.

### B.3 Class, and whether we worked around it

Not obviously a *bug* — it is the documented behaviour of `np.allclose`, reached by using its
default `atol`. It is a defect in the sense that the code reads as a `1e-6` relative test and is
not one for 18 % of the reported state, and nothing in the source or the documentation says so.

**Our experiment was forced to work around it**: our replacement predicate carries a
**per-quantity scale** for every one of the 827–846 state components per deck, precisely because
one inherited absolute term would have sat up to fourteen orders of magnitude above the smallest
quantities and passed any change whatsoever. That is not a refinement in our design; it is a
requirement, and this measurement is why.

**Credit where due:** your own orchestrator raised the `atol` question first, on the same
predicate; the numbers above are our quantification of it at `c0ae5b28`.

---

## C. The 1990 cost model diverges at negative net electric power

### C.1 What we measured

Task **A22** enumerated, for each of `st_regression`'s **144** recorded design points, how many
passes of the model sequence the state needs before it stops changing. **135 of 144** need one or
two. **7 of 144** run to 4, 6 or 7 passes, and on every one of those seven the only quantities
still moving from pass 2 onward are three fields of PROCESS's 1990 cost model — `costs.coe`,
`costs.coecap`, `costs.coefuelt`.

**Six of those seven design points have negative net electric power**, from **−1.6 to −3.0 MW**,
against a **median of +110 MW over the other 137 points of the same deck**. At those six:

| field | value | characteristic scale on this deck |
|---|---|---|
| `costs.coe` | 6.6 × 10²¹ | 1 251 |
| `costs.coecap` | 6.5 × 10²¹ | 1 184 |
| `costs.coefuelt` | −4.6 × 10¹⁶ to −8.7 × 10¹⁶ | 2.62 |

The seventh point enters feasible (+1 434 MW, `coe` = 116) and reaches the same region during the
first pass. `st_regression` uses `i_cost_model = 0` — the 1990 model — and `ifueltyp = 0`.

### C.2 The mechanism, read from the source and confirmed arithmetically

`process/models/costs/costs.py`, in `coelc` (`:2703`):

```python
kwhpy = (1.0e3 * self.data.heat_transport.p_plant_electric_net_mw
         * (24.0e0 * constants.N_DAY_YEAR) * self.data.costs.f_t_plant_available
         * self.data.times.t_plant_pulse_burn / self.data.times.t_plant_pulse_total)   # :2722
...
# SJP Issue #836
# Check for the condition when kwhpy=0
kwhpy = max(kwhpy, 1.0e-10)                                                            # :2751
self.data.costs.coecap = 1.0e9 * anncap / kwhpy                                        # :2755
```

`kwhpy` is annual electrical output, and it is **linear in `p_plant_electric_net_mw`**. The guard
at `:2751` is written against `kwhpy = 0`. Applied to a **negative** `kwhpy` it does not protect
anything: it replaces the negative value with `1e-10`, so the division becomes a multiplication by
`1e19`. Every one of the eight cost-of-electricity components in the routine (`:2755`, `:2782`,
`:2815`, `:2842`, `:2875`, `:2900`, `:2932`, `:2946`) divides by that same clamped `kwhpy`.

The arithmetic closes: `coecap = 1e9 · anncap / 1e-10 = 1e19 · anncap`, and the observed
`coecap = 6.5 × 10²¹` implies `anncap ≈ 650` M$/yr — an entirely ordinary annual capital cost for
these decks. We regard the mechanism as established.

**One thing the clamp does not explain**, stated rather than glossed: `coefuelt` is *negative*
(−4.6 × 10¹⁶ to −8.7 × 10¹⁶) at those points, while a clamped positive `kwhpy` with positive
annual costs would make every component positive. The multiplier that can flip these terms'
sign — `1 - life_component_fpy / life_plant`, applied when `ifueltyp == 2` — is not active on this
deck (`ifueltyp = 0`). **We did not chase this and we do not have an explanation for it.**

### C.3 What we infer, and the scoping we owe you

The direct consequence is that PROCESS silently reports a cost of electricity of order `10²¹`
m$/kWh at design points with negative net electric power, and writes it to the MFILE as if it were
a number. There is no error, no warning, and no non-finite value for a guard to catch: the
`|residual| > 9.99e99` check in `constraint_eqns` is nineteen orders of magnitude away from
firing here.

**Two scoping corrections we want on the record, because our own queue's issue text overstates
this in one direction:**

1. Our issue entry says the divergence makes a relative convergence test "roughly 10¹⁸ times
   tighter than intended". **That is true of *our* convergence test, not of PROCESS's.** Our
   predicate scales each component by a *characteristic* magnitude harvested in advance (1 251 for
   `coe`), so a value of 6.6 × 10²¹ is 10¹⁸ scale units away from anything. Upstream's
   `np.allclose` is relative to the **current** value, so a large-but-stable `coe` costs it
   nothing. The upstream-facing finding is the divergence itself, not a tightening of upstream's
   test.
2. **None of our four decks minimises the cost of electricity.** Their figures of merit are
   `1`, `-14`, `-5` and (for the evaluation-only deck) none. Had a deck used `i_figure_merit = ±6`,
   `objective_function` would return `coe / 100` — an objective of order `10¹⁹` — straight to
   VMCON. We have not run that case and are not asserting what would happen; we are pointing at
   the path.

### C.4 Class, and how it affected us

**A deliberate guard with an undocumented consequence, not a coding slip.** The clamp is commented
and traceable to an issue number. It is correct for `kwhpy = 0` and wrong for `kwhpy < 0`, and
nothing in the code or the comment says the routine has no meaning at negative net electric power.

**Our experiment was affected by it**, which is why we hold the numbers: those 7 of 144 points
inflated an acceptance quantity — a pass count — for a reason that has nothing to do with
architecture. We did not work around it. We reported it with its denominator and noted that the
one architectural change that removes the mechanism entirely (lifting the cost model out of the
loop) takes `st_regression` from `{1: 9, 2: 128, 4: 1, 6: 3, 7: 3}` passes to `{1: 9, 2: 135}`,
with all seven long points gone.

**It did not recur** in our later 300-run campaign: **0 degenerate entries** over 22, 23/20, 25/25
and 25/15 completed runs per deck. Deliberately perturbed starting points were expected to visit
infeasible states, and on these decks they did not visit ones with non-positive net electric power.

---

## D. Constraint equality membership is decided by position in the input file

**This is the one we would put first if you file only one.** It is a usability trap, it is silent,
and it produces a result that looks right.

### D.1 What we measured

PROCESS does not decide which constraints are equalities from anything about the constraints. The
decision is **the order in which they appear in the input deck**, and it is assembled from three
places:

1. `process/core/input.py:44-48` — every `icc = ...` line in the deck appends to `icc` **in file
   order**:
   ```python
   def _icc_additional_actions(_name, value, _array_index, _config, data):
       data.numerics.icc[data.numerics.n_constraints] = value
       data.numerics.n_constraints += 1
   ```
2. `process/core/solver/constraints.py:1958` — `constraint_eqns` builds the constraint vector by
   iterating `icc` in that same order.
3. `process/core/solver/solver_handler.py:72-76` — the solver is told
   `meq = n_equality_constraints`, and VMCON treats **the first `meq` entries** of that vector as
   the equalities.

So the equality block is `icc[0 : n_equality_constraints]` — the first `n_equality_constraints`
lines of the deck, whichever they happen to be. `n_equality_constraints` is set by the user (under
the obsolete name `neqns`) and is not derived from, or checked against, the constraints named.

**Correction to our own record.** Our task report attributes the positional split to
`init.set_active_constraints`. That is where the *count* is reconciled
(`process/core/init.py:1277-1294` sets `n_inequality_constraints = num_constraints -
n_equality_constraints`), not where the split is made. The mechanism as described above is what we
verified in the source for this report.

### D.2 What happened to us

We needed to add one equality constraint to a deck. We appended `icc = 93` after every other
constraint line, which is the natural place to put it, and left `neqns` alone. That made our new
**equality** the twenty-fourth **inequality**. On `large_tokamak_nof`:

| | deck with the line appended at the end | deck with the line inserted inside the equality block | unmodified baseline |
|---|---|---|---|
| `ifail` | **1** (converged) | 1 | 1 |
| `n_equality_constraints` | 3 | **4** | 3 |
| `n_inequality_constraints` | **24** | 23 | 23 |
| `norm_objf` | 1.600000000155… | 1.600000000156… | 1.600000000028… |
| model node calls | **26 200** | 43 426 | 42 567 |

**It converged, it reported a normal objective, and it looked 38 % cheaper than the baseline**
(26 200 against 42 567 model node calls). Nothing forced the new quantity onto its consistency
manifold, so the optimiser was free to move it wherever the objective liked. Had that number been
reported it would have been the headline of the task, and it would have been false. It was caught
only because a gate compared `n_inequality_constraints` against the baseline and saw 24 where 23
was expected.

**One of our four decks failed loudly instead, and only by luck.** `large_tokamak_eval` solves the
equalities alone with `fsolve`, which needs as many equations as unknowns; 3 variables against 2
equalities raised a shape error inside SciPy. The optimising decks had no such backstop.

### D.3 What validation exists, and what it does not catch

`process/core/init.py:314-325` does check the constraint count:

```python
if (data.numerics.icc[: n_equality_constraints + n_inequality_constraints] == 0).any():
    raise ProcessValidationError("The number of constraints specified is smaller than the number"
                                 " stated in n_equality_constraints+n_inequality_constraints", ...)
```

That catches a deck that *under*-declares. It cannot catch our case: the totals were consistent
(27 = 3 + 24), only the split was wrong.

The rule is documented **only in deck comments, and not in all of them**. Of our four decks, two
carry a comment saying the first `neqns` `icc` entries are the equality constraints
(`large_tokamak_nof` and `st_regression`) and two do not (`low_aspect_ratio_DEMO`,
`large_tokamak_eval`). The data-structure docstring for `n_equality_constraints` reads "number of
equality constraints to be satisfied" and does not mention ordering. `grep` finds no mention of
`neqns` anywhere under `documentation/` at `c0ae5b28`. The only other statement of the rule in the
source is a comment in the input writer, `process/core/io/in_dat/base.py:1273`.

### D.4 Class, and how it affected us

**Certainly a bug in usability terms**, even though every individual line behaves as written. A
constraint's mathematical role is determined by an invisible, unvalidated property of where its
line sits in a text file, and getting it wrong yields a converged solve of a different problem.
**Our experiment was affected by it directly** — we hit it, and it nearly produced a false
headline.

---

## E. Two loops in `init.py` are bounded by the wrong quantity

Both were found by reading, while appending an entry to the constraint registry (task **A20**,
re-encountered in **A24**). **Neither has been observed to fire**, and we changed nothing about
either.

### E.1 `set_active_constraints` is bounded by the registry size

`process/core/init.py:1277-1283`:

```python
num_constraints = 0
for i in range(ConstraintManager.num_constraints()):
    if data.numerics.icc[i] != 0:
        data.numerics.active_constraints[data.numerics.icc[i] - 1] = True
        num_constraints += 1
```

The loop scans `icc[0 : ConstraintManager.num_constraints()]` — bounded by **how many constraints
exist in the registry** (82 at `c0ae5b28`), not by how many the deck names. `icc` is 500 long
(`N_CONSTRAINT_EQUATIONS_MAX`, `process/data_structure/numerics.py:142`) and zero-filled, and the
parser already maintains the correct count in `data.numerics.n_constraints`
(`process/core/input.py:47`), which this function ignores.

- **Harmless on ordinary decks.** Ours name **18–26** constraints, so the scan reads zeros past
  the end and counts nothing. We confirmed empirically that widening the bound from 82 to 83 slots
  changes no output bit.
- **Reachable, narrowly.** A deck naming **more than 82** `icc` entries would be silently
  truncated: `num_constraints` would come out as 82, and `n_inequality_constraints` would be set
  from it, wrongly. With 82 distinct constraint ids, that requires a deck to repeat ids — which
  nothing forbids. We have not constructed such a deck.
- The bound should be `data.numerics.n_constraints`, or the array length.

### E.2 The `icc = 77` check is bounded by the *iteration-variable* count

`process/core/init.py:305-307`:

```python
if (data.numerics.ixc[: data.numerics.n_iteration_variables] == 60).any() and (
    data.numerics.icc[: data.numerics.n_iteration_variables] == 77
).any():
```

The second slice indexes **`icc`** by **`n_iteration_variables`**. This is the only one of the
**16** `icc[...]` slices in the file bounded by anything other than
`n_equality_constraints + n_inequality_constraints`; the other 15 all use the constraint count.
We read it as a copy-paste from the `ixc` slice on the line above.

**Consequence.** Where a deck has fewer iteration variables than constraints, constraint 77 sitting
past that position is invisible to the check, and the validation silently does not fire. Measured
on our four decks (`icc` lines / `ixc` lines): `large_tokamak_nof` **26 / 20**,
`low_aspect_ratio_DEMO` 25 / 19, `st_regression` 18 / 14, `large_tokamak_eval` 25 / 2. So on
`large_tokamak_nof` — the one deck of the four that does use `ixc = 60` — **6 of its 26 constraint
slots lie outside the scanned range**. None of the four names `icc = 77`, so nothing fired; the
miss window is real but unexercised. Where a deck has *more* iteration variables than constraints
the slice over-reads into zeros, which is harmless.

---

## F. What we did not establish

Stated explicitly, so nothing here is read as more than it is.

- **No defect above has been shown to have changed a published PROCESS result.** For A we have a
  measured refutation of the one candidate we had (13 of 13 baseline MFILEs finite, §A.3). For B,
  C, D and E we simply have not looked, and looking is out of scope for our experiment.
- **B's 18.0 % is one deck's MFILE** (`large_tokamak_nof`, 1 947 of 10 813 nonzero entries). The
  per-deck constraint-vector figures in §B.1 range from 33.3 % to 51.6 % below the crossover; we
  have no figure for PROCESS's decks in general.
- **C's negative `coefuelt` is unexplained** (§C.2). The `kwhpy` clamp accounts for the magnitude
  of `coe` and `coecap` and not for that sign.
- **C's route into a cost-of-electricity objective is untested** (§C.3). No deck of ours uses
  `i_figure_merit = ±6`.
- **E.1's truncation and E.2's miss window are both unexercised.** We constructed no deck that
  triggers either.
- **We did not check any of these against `develop` or against your pin**, except A, which your
  orchestrator confirmed at `PROCESS_at_36ac820e`. Everything else is stated at `c0ae5b28` only.
  Our base commit is frozen and we do not track upstream forward, so drift since `c0ae5b28` is
  yours to check.

---

## G. What we recommend, and what is yours to decide

We are handing over evidence, not filing fixes. Ranked by our own reading of severity:

1. **D — positional equality membership.** The cheapest useful change is a *check*, not a
   redesign: validate at load time that the constraints inside `icc[:n_equality_constraints]` are
   the ones a deck intends to be equalities, or at minimum warn when `neqns` is set while the
   deck's constraint list has changed. Long-term, an equality/inequality flag that travels with
   the constraint rather than with its line position removes the class.
2. **A — `equal_nan=True`.** Delete the keyword. `equal_nan=False` is the default; the
   `RuntimeError` the loop should raise is already written at `caller.py:129`. Fixing the keyword
   fixes both convergence loops, since they share the predicate. The `.get(var, np.nan)` default
   at `caller.py:192` is a separate line and wants its own decision.
3. **C — the `kwhpy` clamp.** `max(kwhpy, 1e-10)` on a signed quantity is the specific fault; a
   guard on the *magnitude*, or an explicit refusal to cost a plant with negative net electric
   output, would both be defensible where the current clamp is not.
4. **E.2 then E.1 — the two loop bounds.** Both are one-token changes to `n_constraints`.
5. **B — the hidden `atol`.** Not a one-line fix and we do not propose one; the useful output is
   the measurement, which says any single tolerance is wrong across a state spanning 43 orders of
   magnitude.

---

## H. Provenance

- All line numbers and source quotations are from PROCESS **`c0ae5b28`**, read via
  `git show c0ae5b28:<path>` in `PROCESS_surgery`. `process/models/costs/costs.py`,
  `process/core/init.py` and `process/core/input.py` are byte-identical between `c0ae5b28` and the
  branch this was written on, so their line numbers are unambiguous;
  `process/core/solver/constraints.py` differs by one appended registry entry on our branch, and
  the numbers quoted are the `c0ae5b28` ones.
- Counts in §A.3 and §B.1 come from instrumented runs of the four scenarios at `c0ae5b28`; each
  reproduced identically across two full pipeline runs. Counts in §C.1 come from a per-design-point
  census of `st_regression`'s 144 points. Counts in §D.2 come from three runs of
  `large_tokamak_nof` differing only in the input deck.
- **No conclusion in this document rests on a timing.** Every quantity is a count or an exact
  comparison.
- The underlying task reports live in `PROCESS_surgery` under
  `arch_surgery/docs/reports/` and `arch_surgery/docs/reports/deprecated/` (A20, A22, A24, A25,
  and the Phase A results report). They are internal documents and are not part of this handoff;
  ask if you want any of them.

---

## Change log

| # | Date | Change |
|---|---|---|
| 1 | 2026-09-02 | Written. Consolidates five findings; supersedes `2026-09-01_call_models_equal_nan_converged.md`, carrying defect A forward with the A25 measurement, the 13-of-13 refutation, and a correction narrowing its blast-radius argument (a NaN cannot reach `check_agreement` through the constraint vector). |
