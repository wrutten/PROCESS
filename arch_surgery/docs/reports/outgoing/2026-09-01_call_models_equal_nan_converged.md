# `call_models` reports a NaN state as converged: `np.allclose(..., equal_nan=True)`

**Found:** `PROCESS_surgery`, MDA partition experiment, while specifying a replacement convergence
predicate (D13, 2026-09-01).
**Study commit:** PROCESS `c0ae5b28`, the `PROCESS_surgery` base commit.
**Verified at the pin** by the `PROCESS_code_analysis` orchestrator, 2026-09-01, read from the
frozen reference tree: the line is present **unchanged** at `PROCESS_at_36ac820e`, `caller.py:70`,
and it is the only `equal_nan` in the file.
**Status:** **REPORTED, NOT PATCHED.** Nothing has been changed in any tree. `PROCESS_surgery`
freezes the models and the base commit, so this is a finding, not a fix.
**Filed here rather than written into `PROCESS_code_analysis` directly** because `PROCESS_surgery`'s
`CLAUDE.md` forbids writing to a sibling clone. Move or copy as you see fit.

---

## 1. What is wrong

`process/core/caller.py:59-71` at `c0ae5b28`:

```python
    @staticmethod
    def check_agreement(previous, current) -> bool:
        ...
        # Check for same shape: mfile length can change between iterations
        if isinstance(previous, float) or previous.shape == current.shape:
            return np.allclose(previous, current, rtol=1.0e-6, equal_nan=True)
        return False
```

This is the convergence test of the MDA idempotence loop. `call_models` re-runs the whole model
sequence until the objective function and the constraint vector stop changing, and
`check_agreement` is what decides "stop changing".

`equal_nan=True` makes `np.allclose` treat NaN as **equal to NaN**. So if a quantity becomes NaN
and stays NaN across two successive sweeps — which is the normal behaviour of a NaN once it
appears, since almost every arithmetic operation propagates it — the loop concludes that the
values agree and **returns "converged"**.

A NaN that is *stable* is the easiest possible case for this predicate to pass.

## 2. Why it matters

The returned `objf` and `conf` go straight to VMCON:

- `fcnvmc1` (`process/core/solver/evaluators.py:66`) returns them as the objective and constraint
  values at the current point.
- `fcnvmc2` differences them to build the gradient — measured to be a **central-difference `2n`
  stencil**, so a NaN at any stencil point contaminates a whole gradient column.

Between 94 % and 96 % of all `call_models` calls in a solve are finite-difference perturbations
(measured across four scenarios at `c0ae5b28`), so the overwhelming majority of the calls this
predicate gates are gradient stencil points, where a silent NaN is least visible and most damaging.

The failure is silent in the specific sense that matters: the loop's own non-convergence counter
stays at zero. Instrumented runs of all four scenarios at `c0ae5b28` record
`call_models_nonconverged = 0` — the loop never reports failure — so a NaN reaching the optimiser
this way leaves no trace in the loop's own diagnostics.

## 3. Severity, honestly stated

**No instance of this firing has been observed.** All four scenarios instrumented at `c0ae5b28`
converge and produce finite results, and no NaN has been seen in the loop. This is a latent defect
found by reading the predicate, not a diagnosis of an observed failure.

What makes it worth reporting anyway is the *direction* of the failure: it converts a loud failure
(NaN propagating to the optimiser, which would eventually show up as a bad step or a solver error)
into a quiet one (the MDA declares success and hands the NaN on as a converged value).

## 4. The one-word fix, and the reason it is not applied here

```python
return np.allclose(previous, current, rtol=1.0e-6, equal_nan=False)   # or omit the kwarg
```

`equal_nan=False` is `np.allclose`'s default, so removing the keyword is sufficient. A NaN state
would then fail the agreement test, the loop would exhaust its cap of 10, and
`call_models` would raise the `RuntimeError` it already has at `caller.py:140` — which is the
correct behaviour and is already written.

`PROCESS_surgery` does not apply it because that repository's base commit is frozen as a shared
coordinate system with `functional_PROCESS` and with this study's analysis pin, and because a
change to the convergence predicate is exactly the independent variable of the experiment being
run there. It is reported so the defect is on record rather than only inside an experiment's
design notes.

## 4a. Both definitions of "converged" share this one predicate — and there is a second route in

**Verified by the `PROCESS_code_analysis` orchestrator at the pin, 2026-09-01**, and re-checked
here at `c0ae5b28`.

`MDA_Output` — the second convergence loop, which compares successive MFILEs variable by variable —
does **not** have a predicate of its own. `caller.py:205` calls the same
`self.check_agreement(previous_value, current_value)`. So F12's "two incompatible definitions of
converged" both run through **one code path and one `equal_nan=True`**. Fixing the keyword fixes
both loops; it also means the defect's blast radius is larger than the idempotence loop alone,
since `MDA_Output` is the one whose result is reported to the user.

**The second route.** One line above, at `caller.py:204`:

```python
current_value = mfile_data.get(var, np.nan)
```

A variable present in the *previous* MFILE and **absent from the current one** defaults to `NaN`.
Combined with `equal_nan=True`, a variable that was NaN last sweep and then disappears entirely is
compared NaN-to-NaN and **counts as agreeing**. Same direction as the primary finding — a state
that should be loud is quiet — by a different mechanism.

(The complementary case is handled correctly: a variable that was *finite* and then disappears
compares finite-to-NaN, `allclose` returns `False`, and it is reported as non-converged.)

## 5. Related

- **F8 / F3** in [`PROCESS_architecture_evaluation.md`](../PROCESS_architecture_evaluation.md):
  the same predicate converges *functionals of the state* rather than the coupling variables, which
  is also what gives the loop its structural floor of two sweeps.
- **F12**, same document: `MDA_Idempotence` and `MDA_Output` use two different definitions of
  "converged" on the same system. §4a resolves what that means for this defect — they share one
  predicate, so they share one loophole, and `MDA_Output` adds a second route through
  `.get(var, np.nan)`.
