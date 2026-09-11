> **Filing note (written directly by the `PROCESS_surgery` orchestrating session, 2026-09-11, at the
> user's instruction — no agent was active in this repository; not committed here, the user commits).**
> Every line number below is at PROCESS **`c0ae5b28`**, the surgery study's frozen base commit — **not this
> repository's analysis pin**; map locations before citing them against the pinned trees. The physics and
> engineering models at `c0ae5b28` are byte-identical to those in the surgery study's own copy of PROCESS
> (its gate G0′), so the quoted code is what the measurements ran.
> **Relation to what this directory already holds.** The `Owed (M36, 2026-08-21)` bullet in
> [`README.md`](README.md) records that `n_rad_per_layer` is forced 100 → 500 on the output path and never
> restored, and that every idempotence comparison after the first output pass compares two discretisations.
> This report does **not** re-derive that finding. It supplies what M36's recap did not: the measured
> consequence for one written quantity, a grid law that says what kind of error it is, the size of the artefact
> it produces in an instrument that evaluates the model set after an output call, and **one further defect M36
> did not list** — the `insstrain` guard latches `None`.

# The output path changes the TF-coil stress mesh and never restores it: the written `insstrain` is not the solved value, and its guard latches `None`

**Found:** `PROCESS_surgery`, task **A61 (insstrain-diagnosis)**, 2026-09-11 — a fork of PROCESS in which
the *arrangement of solvers* is changed while every model is left exactly as upstream wrote it. Found while
diagnosing why that experiment's exit audit reported one coupling-state component above its tolerance at the
accepted point of **PROCESS as shipped** (its reference arm, every architecture switch unset).
**Study commit:** PROCESS **`c0ae5b28`**. Every count and every hexadecimal float was measured against a
copy of that tree whose models are byte-identical to it.
**Status:** **REPORTED, NOT PATCHED.** Nothing was changed in any tree; the surgery study freezes the models.
**Throughout,** "configuration" means one PROCESS input file from `tests/regression/input_files/`
(`large_tokamak_nof`, `low_aspect_ratio_DEMO`, `st_regression`, unmodified); "arm" is one arrangement of the
solver driver, of which `BR` is PROCESS as shipped; "the solve" is the optimiser's last model evaluation at the
accepted design vector; "the output path" is everything from the solver's return to the end of
`write_output_files`.

---

## 0. What is handed over

| | Finding | Class | Where (`c0ae5b28`) | Status here |
|---|---|---|---|---|
| **1** | The output path raises `tfcoil.n_rad_per_layer` from 100 to 500 through four latching writes and nothing restores it; any evaluation of the model set after an output call runs the TF-coil stress calculation on a mesh the solve never used | **an undocumented one-way side effect of output mode** (M36's R1 headline, now with its consequence measured) | `process/models/tfcoil/superconducting.py:2523-2524`, `:4053-4054`, `:2100`; `process/models/tfcoil/resistive.py:103-104`; default at `process/data_structure/tfcoil_variables.py:303` | measured consequence, §1–§2 |
| **2** | The `insstrain` written to the output file is **not** the value the solve converged, by **0.70–0.72 %**, in every arm including PROCESS as shipped, on both pulsed configurations; neither value is the mesh-converged one | **a reporting defect** — the file reports a quantity computed on a mesh the solve did not use | consequence of 1 | measured, §2 |
| **3** | The guard `insstrain = insstrain if insstrain is None else new` keeps the stored value only when it is *already* `None`; since the default is `0.0`, the first call under a stress model that does not compute it stores `None` and every later call preserves it | **certainly a bug** — the guard does the opposite of what its shape suggests | `process/models/tfcoil/superconducting.py:2651-2655`; `process/models/tfcoil/base.py:2521`; default at `tfcoil_variables.py:208` | measured, §3 |

---

## 1. The mesh change is a one-way, latching write

### 1.1 The code, at `c0ae5b28`

`process/data_structure/tfcoil_variables.py:303`:

```python
    n_rad_per_layer: int = 100
```

`process/models/tfcoil/superconducting.py:2523-2524` (inside `CICCSuperconductingTFCoil.run`), the same
shape at `:4053-4054` (the other superconducting TF-coil node) and at `process/models/tfcoil/resistive.py:103-104`:

```python
        if output:
            self.data.tfcoil.n_rad_per_layer = 500
```

and `process/models/tfcoil/superconducting.py:2100`, unconditional, in the stress routine that `output()` calls:

```python
        self.data.tfcoil.n_rad_per_layer = 500
```

There is no assignment back to 100 anywhere under `process/models/`. The field is not part of the state the
idempotence loop compares (it is a discretisation setting, not a model output), so no convergence test sees
the change.

### 1.2 What we measured

The surgery study's exit audit takes a bit-exact snapshot of the coupling state (the ~840 model quantities the
solver iterates) at the entry to `write_output_files`, then runs **one further sweep** of the whole model set
from that snapshot and reports the largest scaled change. On both pulsed configurations, in every arm
measured (`BR` = PROCESS as shipped, and three re-arranged drivers), exactly one component moved:
`tfcoil.insstrain`, by **6.99 × 10⁻³** (`large_tokamak_nof`) and **7.02 × 10⁻³** (`low_aspect_ratio_DEMO`) in
units of its own measured scale — about 7 000 times the loop's tolerance of 10⁻⁶ — while the loop's own last
sweep had moved it by ≤ 1.24 × 10⁻¹¹.

Attribution, as a leave-one-out pair over the **86 of 2 288** data-structure fields that differ between the
solve's exit state and the state at the entry to `write_output_files`:

| what is put back before the audit sweep | `tfcoil.insstrain`'s scaled residual | components above 10⁻⁶ (of 696 / 701) |
|---|---|---|
| **only** `tfcoil.n_rad_per_layer` (500 → 100) | exactly `0x0.0p+0` in every arm, both configurations | 0 |
| the **other 85** fields, and not `n_rad_per_layer` | unchanged (`0x1.ca293e1fbbd05p-8` on `large_tokamak_nof`/`B0`) | 1 |

A second sweep from the state the first sweep produced changes nothing (`0x0.0p+0` on 9 of 9 runs): a one-off
recomputation on the new mesh, not a cycle. **Every other component of the accepted state was at its fixed
point**: 0 of 840 / 846 / 827 coupling-state components differ, bit for bit, between the loop's last sweep and
the state the output path starts from, on 9 of 9 runs.

### 1.3 Why it matters beyond this one value

This is the mechanism behind M36's headline, with a size attached. Any instrument or any code path that
evaluates the models after an output call — a second `call_models` in an output-time loop, a post-solve
consistency check, a re-evaluation at the accepted point — compares a 500-layer TF-coil stress calculation
with the 100-layer one the solve used. In PROCESS as shipped the output-time loop (`MDA_Output`) re-sweeps the
state twice at 500 before the files are written, so the written file is internally on the finer mesh while the
accepted design point was found on the coarser one.

---

## 2. The written `insstrain` is not the value the solve converged

*One row per run. "Converged by the solve" is `tfcoil.insstrain` in the state at the entry to
`write_output_files` (the solve's own value, mesh 100); "written" is the same run's MFILE value (mesh 500).
Compared as hexadecimal floats; identical in no row. `BR` is PROCESS as shipped.*

| run | converged by the solve | written to the output file | difference |
|---|---|---|---|
| `large_tokamak_nof` / `BR` / seed 0 | −5.8703384458e-03 | −5.9126070012e-03 | 0.72 % |
| `large_tokamak_nof` / `B0` / seed 0 | −5.8703422201e-03 | −5.9126108020e-03 | 0.72 % |
| `large_tokamak_nof` / `B0` / seed 1 | −5.7630537836e-03 | −5.8045484053e-03 | 0.72 % |
| `large_tokamak_nof` / `B1` / seed 0 | −5.9974760007e-03 | −6.0405181447e-03 | 0.72 % |
| `large_tokamak_nof` / `B3` / seed 0 | −5.9974760007e-03 | −6.0405181447e-03 | 0.72 % |
| `low_aspect_ratio_DEMO` / `BR` / seed 0 | −4.8289567355e-03 | −4.8628617723e-03 | 0.70 % |
| `low_aspect_ratio_DEMO` / `B0` / seed 0 | −4.8289567355e-03 | −4.8628617723e-03 | 0.70 % |
| `low_aspect_ratio_DEMO` / `B3` / seed 0 | −4.8289520177e-03 | −4.8628570292e-03 | 0.70 % |
| `st_regression` / `B0` / seed 0 | the component is `None` (§3); the file carries no `insstrain` line | — | — |

**Neither value is the mesh-converged one.** Sweeping the same accepted state at `n_rad_per_layer` ∈ {100, 200,
300, 400, 500} gives `v(n) = v_∞ + C/n` with the four consecutive estimates of `C` agreeing to **0.116–0.140 %**
across all eight runs — a first-order sampling error, the signature of a value read one grid step short of a
layer boundary, not a discontinuity. Extrapolated: the solved value is **0.87–0.89 %** from the limit, the
written one **0.17–0.18 %**. (`large_tokamak_nof`/`B0`/seed 0: `v_∞` = −5.9231691831e-03; `C` from consecutive
pairs 5.285326e-03, 5.281429e-03, 5.279969e-03, 5.279191e-03.)

**Class.** The output file reports a quantity computed on a mesh the solve never used, and the accepted design
point was found on a mesh whose value is the further of the two from the converged one. Which *other* written
quantities the finer mesh reaches — the TF-coil stress block's other outputs, and anything that reads them
during the output pass — **was not measured** and is stated as a limit in §4.

---

## 3. The `insstrain` guard latches `None`

### 3.1 The code, at `c0ae5b28`

`process/data_structure/tfcoil_variables.py:208`:

```python
    insstrain: float = 0.0
```

`process/models/tfcoil/base.py:2521`, in `TFCoil.stresscl`, on the branch where the stress model does not
compute the insulation strain:

```python
        insstrain = None
```

`process/models/tfcoil/superconducting.py:2651-2655`, in `CICCSuperconductingTFCoil.run`, after `stresscl`
returns:

```python
            self.data.tfcoil.insstrain = (
                self.data.tfcoil.insstrain
                if self.data.tfcoil.insstrain is None
                else insstrain
            )
```

The guard keeps the **stored** value when the stored value is already `None`, and otherwise assigns the new
one. With the default `0.0`, the first call under a stress model that returns `None` therefore **stores
`None`**, and every later call — the condition now true — preserves it for the life of the run. If the intent
was "keep the previous value when the new one is not computed", the test is on the wrong operand.

### 3.2 What we measured

On `st_regression` (`i_tf_stress_model = 0`) `tfcoil.insstrain` is `None` from the first model sweep onward
and stays `None`: across the surgery study's 144-point harvest of that configuration the component took one
distinct value, `null`, and its MFILE carries no `insstrain` line. The study's coupling-state census therefore
classified it as a *discrete* component on that configuration — which is why the mesh artefact of §1 never
showed there. Whether any consumer of `tfcoil.insstrain` is reached with `None` on that path was not
established (§4); the defect is in the guard regardless.

---

## 4. What we did not establish

- No published PROCESS result has been shown to change because of any of the three. The surgery study gates on
  the objective and a feasibility audit, neither of which reads `insstrain`.
- Which other written quantities the 500-layer mesh reaches during the output pass, and by how much.
- Whether the 500-layer value is what the authors intend the file to report (it is the closer of the two to the
  mesh-converged value); if so, the defect is that the *solve* runs on the coarser mesh, not that the file is
  written on the finer one.
- Whether the `None` latch has any consumer that fails or silently skips.
- Anything about configurations other than the three named, or about the stellarator path.

## 5. What we recommend, and what is yours

Finding 1 is already owed under M36 R1–R8; this report supplies its consequence. A maintainer's fix would be
either to restore `n_rad_per_layer` after the output pass or to run the solve on the mesh the file reports, and
to say which the file's value is. Finding 3 is a one-token fix (`insstrain is None` → test the *new* value);
its behavioural consequence should be measured on a configuration with `i_tf_stress_model = 0` before adopting.
Neither change is applied in `PROCESS_surgery`, whose models are frozen; what that study does about its own
instrument (restoring the whole data structure before its audit sweep) is recorded there.

## 6. Provenance

- Source report: `PROCESS_surgery/arch_surgery/docs/reports/A61_insstrain_diagnosis.md` (branch
  `A61-insstrain-diagnosis`, tip `767fb7cb`; every run made at `2ae57064`, through the study's own pool,
  against its copy of PROCESS; scripts `harness/audit_map.py` and `harness/exit_audit_diagnosis.py`, run as
  `python -m harness.exit_audit_diagnosis all`). Nine diagnosis runs plus two instrument-inertness runs; the
  instrument shown inert on 672 of 672 compared record leaves.
- The orchestrating session confirmed the quoted code lines and defaults at `c0ae5b28` by `git show` and by
  `grep` over the study's copy on 2026-09-11 (this filing). The numerical results are the A61 report's; the
  orchestrator's own spot check and critical assessment are recorded with that report at its merge.
- A copy of this document is kept at `PROCESS_surgery/arch_surgery/docs/reports/outgoing/` under the same
  filename.

## Change log

| date | change |
|---|---|
| 2026-09-11 | Created and filed directly by the `PROCESS_surgery` orchestrating session at the user's instruction; not committed in this repository. |
