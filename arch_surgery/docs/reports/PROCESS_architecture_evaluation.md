> **Document status** — **LIVE REFERENCE · MEASUREMENTS STALE**
> The F1–F14 critique of PROCESS's driver architecture. Its **structural findings are current and
> still cited** — F3, F4, F11, F12 and F14 are the basis of the live and deferred experiments. Its
> **measured figures were taken at `710a75c9`** and must not be quoted; the current baseline is
> A1 (stage0-rebaseline)'s, at `c0ae5b28`. It sits in `reports/` rather than `reports/deprecated/`
> precisely because it is still in use.

# PROCESS driver architecture — a critical evaluation

**Scope.** The workflow layer of PROCESS: the drivers between the command line and
`Caller._call_models_once`, the way they compose, and what they would look like
re-expressed as a canonical xDSM in the sense of Lambe & Martins (2012) and
Martins & Ning, *Engineering Design Optimization* (2021).

**Code under evaluation.** `~/dev_libraries/PROCESS`, branch `analysis-annotations`,
identical to the analysis pin `PROCESS_at_6503576a` up to `_version.py`. All line
references are to that tree. Structural figures are from the graphs this tool
produces ([`dependency_analysis/output/tokamak_sctf/`](../../PROCESS_code_analysis/dependency_analysis/output/tokamak_sctf/),
[`dependency_analysis/output/stellarator/`](../../PROCESS_code_analysis/dependency_analysis/output/stellarator/)) with `drivers=True`.

> **Moved 2026-08-19** from `PROCESS_code_analysis/dependency_analysis/docs/`. The
> document is unchanged apart from the links, which now point across into the
> [`PROCESS_code_analysis`](../../PROCESS_code_analysis/) repository where the tool
> and its outputs still live.

**Epistemic status.** Three tiers, kept separate throughout:

| Tier | Meaning |
|---|---|
| **Measured** | Read off the code or computed from the graph. Reproducible. |
| **Estimated** | Order-of-magnitude, under assumptions stated at the point of use. |
| **Judgement** | Architectural opinion. Argued, not proven. |

One bound applies to everything below and is repeated at the end: the runtime
oracle traces only lines 259–392 of `caller.py`, so **0 of the 9 top-level
drivers is corroborated by execution**. The chain is read from source.

---

## 1. Summary of findings

| # | Finding | Tier | Severity |
|---|---|---|---|
| F1 | Tolerance inversion: the optimizer's convergence test is 4 orders tighter than its gradient accuracy | Measured + Estimated | **High** |
| F2 | Finite differences are taken across an iterative solver; solver noise dominates truncation error by ~10⁴ | Estimated | **High** |
| F3 | The MDA converges the objective and constraints, not the coupling variables | Measured | **High** |
| F4 | The code documents that model ordering changes results — which contradicts the convergence claim | Measured | **High** |
| F5 | `epsfcn = 1e-3` is ~14× below the noise-optimal step; the retry ladder accidentally corrects it | Estimated | Medium |
| F6 | `FD_Gradients` is not architecture — it is the pyvmcon callback signature leaking upward | Judgement | Medium |
| F7 | `SolverHandler` is a restart controller, not a solver; it re-runs the optimization up to 4× | Measured | Medium |
| F8 | The MDA costs a minimum of 2 model sweeps even on a purely feed-forward system | Measured | Medium |
| F9 | Coupling is via one mutable blackboard; no declared interfaces, so IDF is not expressible | Measured | Medium |
| F10 | `_call_models_once` is one block containing three mutually exclusive architectures | Measured | Medium |
| F11 | The stellarator's two impromptu MDAs are fixed at 2 iterations with no convergence test | Measured | Medium |
| F12 | Two incompatible definitions of "converged" coexist (f/c idempotence vs MFILE idempotence) | Measured | Low |
| F13 | The FD step is purely relative, with no absolute floor: `x = 0` gives a zero denominator | Measured | Low |
| F14 | Seven root-finders sit inside the FD stencil, each adding a tolerance-level discontinuity | Measured | Low |
| C1 | *Credit:* scan points warm-start from the previous optimum — free continuation | Measured | — |

---

## 2. The architecture as built

```
COOR                                   (boundary: deck in, MFILE out)
 ├─ SingleRun.__init__                  main.py:328   ← deck read, init_process
 └─ SingleRun.run()                     main.py:355
     └─ run_scan()                      main.py:445   → constructs Scan
Scan.__init__ → run_scan()               scan.py:192/217   [hop 1: ctor side effect]
 └─ doopt()                              scan.py:251
SolverHandler.run()                      solver_handler.py:33  [hop 2: string factory]
 └─ solver.solve()                       solver_handler.py:69
Vmcon.solve()                            solver.py:189         [hop 3: pyvmcon callback]
 ├─ Evaluators_f.fcnvmc1()               evaluators.py:34
 └─ FD_Gradients.fcnvmc2()               evaluators.py:95
MDA_Idempotence.call_models()            caller.py:77   ← for _ in range(10)
 └─ _call_models_once()                  caller.py:260  ← the physics
```

Off to the side: `MDA_Output.call_models_and_write_output()` (`caller.py:146`),
invoked from `write_output_files` (`caller.py:436`) *after* `doopt` returns, not
inside the solve. And `FSolve` (`solver.py:324`), the alternative terminal driver
selected when `ioptimz == -2`.

Below the spine sit seven embedded sub-solvers (root-finders inside models) and,
in the stellarator, two impromptu MDAs. Neither group is in the driver chain;
both are reached from a model.

### 2.1 Problem size, as actually configured

Not the registry sizes. The registries say what PROCESS *can* vary
(83 iteration variables, 82 constraints, 16 figures of merit); the decks say what
each reference case *does* vary.

| | tokamak (`large_tokamak_IN.DAT`) | stellarator (`squid.IN.DAT`) |
|---|---|---|
| iteration variables `n` | **19** | **8** |
| constraints `m` | **26** | **14** |
| equality constraints | 3 | 2 |
| figure of merit | `minmax = 1` | `minmax = 6` |
| `epsfcn` (FD step) | 1e-3 (default) | 1e-3 (explicit) |
| `epsvmc` (VMCON tol) | **1e-7** | default |
| model nodes in graph | 46 | 33 |
| variable nodes in graph | 1431 | 954 |

> An earlier verbal version of this analysis used n = 83 for the cost figures.
> That is the registry size, not the active count. The corrected figures are below.

---

## 3. Findings in detail

### F1 — Tolerance inversion (High)

Three tolerances govern a PROCESS run, and they are ordered wrongly:

| Quantity | Value | Source |
|---|---|---|
| VMCON convergence test `epsvmc` | **1e-7** | `large_tokamak_IN.DAT` |
| MDA agreement `rtol` | **1e-6** | `caller.py:67`, `np.allclose(..., rtol=1.0e-6)` |
| Resulting gradient accuracy | **~1e-3** | estimated, §F2 |

The optimizer is asked to satisfy a first-order optimality test at 1e-7 using
gradients that are accurate to roughly 1e-3, computed from function values that
are only reproducible to 1e-6. The convergence criterion sits **four orders of
magnitude below the noise floor of the quantities it tests.**

What that produces is not a wrong answer so much as an uninformative `ifail`.
Convergence at 1e-7 under 1e-3 gradient error is not evidence that a KKT point
was found; it is evidence that the iterates stopped moving. This is the most
likely explanation for the retry ladder in `SolverHandler` existing at all, and
for scan convergence percentages being a reported statistic (`scan.py:908-911`)
rather than an expectation.

**The ordering should be inverted:** `epsvmc` must be *looser* than the achievable
gradient accuracy, or the MDA tolerance must be tightened until it is not.

### F2 — Finite differences across an iterative solver (High)

`fcnvmc2` (`evaluators.py:133-151`) takes **central differences** with a relative
step, calling `call_models` — a full MDA convergence loop — at each perturbed
point:

```python
xfor[i] = xv[j] * (1.0 + self.data.numerics.epsfcn)
xbac[i] = xv[j] * (1.0 - self.data.numerics.epsfcn)
ffor, cfor = self.caller.call_models(xfor, m)
fbac, cbac = self.caller.call_models(xbac, m)
fgrd[i] = (ffor - fbac) / (xfor[i] - xbac[i])
```

Each evaluation is the output of a fixed-point iteration terminated at
`rtol = 1e-6`. That termination is a **noise floor**, not a rounding error: the
returned value depends on how many sweeps the loop happened to take, which can
differ between `x+h` and `x−h`.

Standard error model for central differences with function noise ε_f:

> E(h) = ε_f/h + (h²/6)·|f‴|

*Estimated* — assumes f ~ O(1) and |f‴| ~ O(1) after scaling, which is the point
of scaling the iteration variables, but is not verified:

| step h | noise term | truncation term | total |
|---|---|---|---|
| 6.7e-6 *(optimal if ε_f were machine eps)* | 1.5e-1 | 7.5e-12 | 1.5e-1 |
| **1e-3 (as configured)** | **1.0e-3** | 1.7e-7 | **1.0e-3** |
| 1.4e-2 *(optimal for ε_f = 1e-6)* | 6.9e-5 | 3.5e-5 | **1.0e-4** |

Noise exceeds truncation by ~6000× at the configured step. **Every gradient
PROCESS computes is noise-limited**, and no reduction in step size can help —
reducing h makes it strictly worse.

This is the structural defect. Everything in F1, F5 and the `SolverHandler`
retry logic is downstream of it.

### F3 — The MDA converges the wrong variable (High)

Canonical MDA converges the **coupling variables** y. `MDA_Idempotence` converges
the **objective and constraints** (`caller.py:106-119`):

```python
self._call_models_once(xc)
objf = objective_function(self.data.numerics.minmax, self.data)
conf, _, _, _, _ = constraints.constraint_eqns(m, -1, self.data)
...
if self.check_agreement(objf_prev, objf) and self.check_agreement(conf_prev, conf):
    return objf, conf
```

Two consequences.

**It is a proxy, and a leaky one.** Coupling variables that do not move f or c by
1e-6 are declared converged. But the FD stencil differences exactly f and c, so
residual variation in y that is invisible to the convergence test is *precisely*
the quantity that pollutes the gradient. Converging functionals and then
differentiating them is the combination most likely to look healthy and behave
badly.

**It fuses the Function blocks into the MDA.** In XDSM, F and C are components
downstream of a converged MDA. Here they are inside its loop, which is why the
convergence variable is what it is. Moving them out is the same change as fixing
the convergence variable.

Mechanically, the loop is unaccelerated nonlinear block Gauss–Seidel: no
relaxation, no Aitken, no Newton, hard cap of 10, `RuntimeError` on failure
(`caller.py:133`). The iteration order is the hand-written call sequence.

### F4 — The code states that ordering changes the result (High)

`caller.py:383-385`:

```python
# These two methods need to be run after vacuum/buildings otherwise
# output changes quite a lot
# TODO: split these two sections into a new model with a .run method
self.models.power.acpow(output=False)
self.models.power.plant_electric_production()
```

A converged fixed point is order-independent by definition. If the sweep order
changes the answer "quite a lot", the iteration is not at a fixed point when it
returns — the idempotence test passed for some other reason (most plausibly:
the affected quantities are downstream of everything and do not feed back into
f or c, so F3's proxy cannot see them).

This is the single most direct piece of internal evidence that the MDA's
convergence claim is weaker than it appears. It is also an **ordering constraint
that no data dependency expresses** — the comment is the only record of it.

Note also that `power` runs at `caller.py:372` and again at `:387/:390`: one
discipline occupying two non-contiguous slots in the sequence. In XDSM that is
either two components or a component with a feedback loop; it cannot be drawn as
one block.

### F5 — The retry ladder accidentally finds the right step (Medium, estimated)

`SolverHandler.run()` (`solver_handler.py:70-105`), on `ifail != 1`:

1. `epsfcn ×= 10` → 1e-2, re-solve
2. `epsfcn /= 10` → 1e-4, re-solve
3. on `ifail == 5` with `nviter < 2`: `set_b(2.0)` (Hessian ← 2·I), re-solve

From the table in F2, the noise-optimal step is h\* ≈ 1.4e-2. **Retry 1 lands at
1e-2 — within 30% of optimal, and ~10× better than the default.** Retry 2 moves
the wrong way, to a strictly worse error (1e-2 total).

So the first retry is not a heuristic that happens to work; it is an empirical
rediscovery of the correct FD step. That it is reached only *after* a failed
optimization, and reset afterwards (`solver_handler.py:84`), means the
information is discarded every time.

**Cheapest high-value change in this document:** raise the default `epsfcn` to
~1e-2, or better, derive it from the MDA tolerance as h = (3·rtol)^(1/3).

### F6 — The gradient block is API leakage, not architecture (Judgement)

`fcnvmc1`/`fcnvmc2` are the pyvmcon callback pair. Their separation reflects the
solver library's interface, not a decomposition of the design problem. In XDSM,
a derivative component appears only when derivatives come from something other
than repeated analysis calls — analytic, adjoint, or AD. Finite differences are
interior to the optimizer.

`Vmcon` + `Evaluators_f` + `FD_Gradients` are **one Optimizer block**. This is a
relabelling; it changes no code and removes two boxes that suggest the gradient
is a peer of the solve rather than the bulk of it.

### F7 — `SolverHandler` is a restart controller (Medium)

It selects a solver by string, then implements the four-attempt policy of F5. In
XDSM that is a **loop around the optimizer**, and it should be drawn as one:
otherwise the diagram shows one optimization per scan point where up to four
occur. The name actively conceals this.

It also constructs `Evaluators` and loads/scales the iteration variables
(`solver_handler.py:35-53`) — the scaling belongs to the Optimizer block.

### F8 — The MDA's floor is two sweeps (Medium)

`call_models` requires **two successive agreeing** evaluations: the first pass
sets `objf_prev`/`conf_prev` and `continue`s (`caller.py:110-116`). So even a
perfectly feed-forward system pays 2 sweeps per evaluation — 100% overhead on
the acyclic part of the model graph.

Combined cost, per VMCON iteration, *measured* from the loop structure:

| | tokamak (n=19) | stellarator (n=8) |
|---|---|---|
| `call_models` per gradient (2n+1) | 39 | 17 |
| `call_models` per iteration (+1 for `fcnvmc1`) | 40 | 18 |
| `_call_models_once` per iteration (≥2× above) | **≥ 80** | **≥ 36** |
| × restart attempts | up to 4 | up to 4 |
| × scan points | `isweep` | `isweep` |

Essentially all runtime is inside a block the current architecture draws as a
peer of the optimizer rather than as its interior.

### F9 — The blackboard (Medium)

Models take no arguments and return nothing:

```python
self.models.plasma_geom.run()
self.models.build.run()
self.models.physics.run()
```

All coupling is through the single mutable `DataStructure`. Four consequences:

1. **The coupling graph is not declared.** It is recoverable only by static
   analysis — which is what this tool is. An xDSM of PROCESS cannot be drawn
   from PROCESS.
2. **Disciplines cannot be reordered or parallelised** without changing results
   (F4 is the proof).
3. **IDF is not expressible.** There are no named y_ij to promote to design
   variables and constrain.
4. **Ordering constraints live in comments**, not in the dependency structure.

### F10 — Three architectures behind a switch (Medium)

`_call_models_once` opens with two early returns (`caller.py:283-292`):

```python
if self.data.stellarator.istell != 0:
    self.models.stellarator.run()
    return
if self.data.ife.ife != 0:
    self.models.ife.run()
    return
# Tokamak calls ...
```

The tokamak sequence is unreachable in a stellarator run. These are not options
within one architecture; they are three analysis blocks with different internal
structure sharing a driver stack. The `# TODO Is this return safe?` above the
first one is the code's own reservation.

### F11 — Unconverged MDAs nested inside a converged one (Medium)

The stellarator's two impromptu MDAs are **unrolled iteration**: `st_phys` called
twice, no convergence test, fixed count of 2. They exist because a later model
consumes what an earlier one produced and the author knew one pass was not
enough. Architecturally: an unconverged fixed-point iteration inside a converged
one. Whatever error the 2-iteration truncation leaves is invisible to
`MDA_Idempotence`'s test unless it moves f or c by 1e-6 — and it feeds the FD
stencil regardless.

### F12 — Two definitions of convergence (Low)

`MDA_Idempotence` compares objective and constraints (`caller.py:118`).
`MDA_Output` compares successive **MFILEs** variable by variable
(`caller.py:199-204`), also capped at 10, also `rtol = 1e-6`. Same word, two
predicates, on the same system. A run can satisfy one and not the other, and
only the second is reported to the user.

### F13 — Relative FD step with no floor (Low)

`xfor[i] = xv[j] * (1.0 + epsfcn)` — at `xv[j] == 0` the perturbation is zero and
`fgrd[i] = (ffor - fbac) / (xfor[i] - xbac[i])` divides by zero. Scaling makes
iteration variables O(1) in normal operation, so this is latent rather than
active, but there is no guard.

### F14 — Root-finders inside the FD stencil (Low)

Seven embedded sub-solvers (current-sharing temperature, TF coil temperature
margin, PF coil zero margin, vacuum Newton, confinement `fhz`, L-H radius, coil
intersection) run inside model evaluations. Each terminates on its own tolerance,
so each contributes a small discontinuity at the scale of that tolerance, inside
every perturbed evaluation. They add to ε_f in F2 by an amount this analysis has
not quantified.

### C1 — Credit: implicit continuation (Measured)

`SolverHandler.output()` writes the solution back to `data.numerics.xcm`
(`solver_handler.py:117`), and `run()` reloads from it at the next call
(`solver_handler.py:35`). Since `Scan` calls `doopt()` repeatedly against a
persistent `DataStructure`, **each scan point warm-starts from the previous
point's optimum.** That is continuation, it is free, and it is a genuine strength
of the blackboard design.

It is also undocumented and unguarded: any future change that resets solver state
between scan points would silently remove it, and the only visible symptom would
be a worse convergence percentage.

---

## 4. Measured coupling structure

Computed from the derived model↔model data edges in the produced graphs
(Tarjan strongly-connected components):

| | tokamak | stellarator |
|---|---|---|
| model nodes | 46 | 33 |
| model→model coupling edges | 200 | 111 |
| distinct coupling variables | 273 | 203 |
| non-trivial SCCs | **1** | **2** |
| SCC sizes | **31** | 13, 2 |
| models inside cycles | 31 of 46 (67%) | 15 of 33 (45%) |
| edges inside cycles | 148 | 44 |
| **distinct coupling variables inside cycles** | **195** | **79** |

The tokamak's 31-model SCC:

> Availability, Build, Buildings, CCFE_HCPB, CICCSuperconductingTFCoil, CSCoil,
> Cryostat, CurrentDrive, Divertor, FirstWall, FusionReactionRate, NeProfile,
> PFCoil, Physics, PlasmaBeta, PlasmaBootstrapCurrent,
> PlasmaConfinementTransition, PlasmaCurrent, PlasmaDensityLimit, PlasmaExhaust,
> PlasmaFields, PlasmaInductance, PlasmaProfile, Power, Pulse,
> SauterBootstrapCurrent, Shield, Structure, TeProfile, VacuumVessel,
> physics.fusion_reactions_functions

Two things follow.

**The MDA is not optional.** Two thirds of the tokamak's disciplines are in a
single mutually-recursive block. There is no sequencing that makes this
feed-forward; the Gauss–Seidel loop is doing real work.

**But it is one block, not many.** A single SCC means the loop cannot be
decomposed into independent sub-MDAs. It also means the whole 31-model set is
re-swept on every iteration, including any member whose inputs did not change.

*Caveat:* this is the coupling structure the **static analysis** recovers. The
graph's `derived` edges come from writer×reader over variables, and its coverage
is bounded by the traversal; an SCC this large is also the shape a
false-positive-tolerant analysis would produce. Reducing it is a
tearing/sequencing question the tool can attack but has not.

---

## 5. Reformulation as a canonical xDSM

### 5.1 Mapping

| PROCESS driver | Canonical XDSM component | Note |
|---|---|---|
| `COOR` | *(none)* — external data nodes x⁽⁰⁾ / x\*, f\* | A device of this tool. Dissolves. |
| `Scan` | **Driver** (parametric sweep) | Outermost loop. Warm-started (C1). |
| `SolverHandler` | **Restart controller** (loop) | Currently invisible. Should be explicit. |
| `Vmcon` | **Optimizer** | ⎫ |
| `Evaluators_f` | *absorbed* | ⎬ one block |
| `FD_Gradients` | *absorbed* | ⎭ annotate "FD, 2n+1 MDA solves" |
| `FSolve` | **Solver** (alternative terminal) | Consistency solve, not optimization |
| `MDA_Idempotence` | **MDA** | Should converge y, not f/c |
| `_call_models_once` | **Analyses** ×N | Currently one block; should be N |
| `objective_function`, `constraint_eqns` | **Functions** F, C | Should sit *outside* the MDA |
| sub-solvers ×7 | internal solvers within Analyses | May be shown or hidden |
| impromptu MDAs ×2 | nested MDA blocks | Should carry a convergence test |
| `MDA_Output` | post-optimality Analysis | Fine where it is |

Nine driver blocks become **six components**, and the six say more.

### 5.2 Target structure

```
0.  x⁽⁰⁾, deck                                    → external inputs
1.  Driver (Scan)                     loop over sweep points, warm-started
2.    Restart controller              up to 4 attempts, varying h
3.      Optimizer (VMCON)             n design vars; gradients FD, 2n+1 MDA solves
4.        MDA                         Gauss–Seidel on y over the 31-model SCC
5.          Analysis 1..N             the disciplines, in sequence
6.        F, C                        objective and constraints, on converged y
7.  Post-optimality analysis          MFILE consistency (MDA_Output)
8.  → x*, f*, MFILE                   external outputs
```

Steps 1, 2, 3, 6 and 7 are **relabelling only** — no PROCESS code changes, the
diagram simply stops misrepresenting what runs. Step 5's decomposition is
available from this tool today. Step 4 is a real code change.

---

## 6. Reformulation options, ranked

### Tier 1 — no code change (documentation and diagram)

- Collapse the three optimizer blocks (F6); draw the restart controller (F7);
  move F/C outside the MDA (F3); decompose the Analysis block (F9).
- State the tolerance stack (F1) in the user documentation, with the gradient
  accuracy estimate. Users currently choose `epsvmc` with no way to know it is
  below the noise floor.

### Tier 2 — small, high-return code changes

- **Raise `epsfcn` to ~1e-2**, or derive it as h = (3·rtol_MDA)^(1/3) (F5).
  Estimated ~10× gradient accuracy for one constant. Verify against the
  regression suite before believing it.
- **Loosen `epsvmc`** to something above the gradient noise, or make the default
  a function of `epsfcn` and the MDA tolerance (F1).
- **Add an absolute floor to the FD step** (F13).
- **Give the impromptu MDAs a convergence test** instead of a fixed count (F11).
- **Record the FD step that succeeded** rather than resetting it (F5).

### Tier 3 — architectural

- **Converge y, not f/c** (F3). Requires naming the coupling variables — which is
  the same prerequisite as everything else in this tier, and which the graph now
  supplies. Add relaxation or Aitken acceleration while there.
- **Analytic or AD derivatives.** This is the only change that removes F2 rather
  than mitigating it. Cost: the models are a mix of Python and ported Fortran, so
  AD is not a drop-in.
- **IDF.** Removes the inner solver entirely, so gradients are no longer
  differentiated through a convergence loop. The sizing question is now
  answerable from §4: breaking the tokamak's single SCC requires promoting up to
  **195 coupling variables** (79 for the stellarator) to design variables, with
  matching consistency constraints — against a current n of 19. FD cost scales
  with n, so naive IDF + FD is roughly 10× worse per iteration, and IDF is only
  attractive here **in combination with analytic derivatives**. A minimum
  feedback set (tearing) would reduce 195, possibly a lot; that computation is a
  natural next use of this graph.

The honest summary of Tier 3: **derivatives are the bottleneck, not the
architecture.** MDF with exact gradients would outperform IDF with finite
differences at these sizes. The MDA is doing legitimate work on a genuinely
coupled system (§4); it is the differentiation *through* it that is unsound.

---

## 7. Limits of this evaluation

- **No runtime corroboration of the drivers.** The gate-2 oracle traces
  `caller.py` lines 259–392 only. `call_models` (77–137) and
  `call_models_and_write_output` (146–258) have zero traced lines, so 0 of 9
  top-level drivers is confirmed by execution. The chain in §2 is read from
  source, and its four unresolvable hops are declared judgements.
- **Two reference decks.** All configured figures (§2.1) are for
  `large_tokamak_IN.DAT` and `squid.IN.DAT`. A deck with 60 iteration variables
  changes every cost figure in §F8 proportionally.
- **The FD error model is an estimate.** It assumes f ~ O(1) and |f‴| ~ O(1)
  after scaling, and treats the MDA tolerance as the noise amplitude. Both are
  plausible and neither is measured. A numerical experiment — evaluate f at a
  fixed x many times with perturbed solver state, and measure the spread — would
  replace the estimate with a number, and is the single most valuable follow-up
  in this document.
- **The SCC is a static result** (§4 caveat), bounded by traversal coverage.
- **VaryRun is out of scope** by agreement: the analysis is rooted at
  `SingleRun`.

---

## 8. References

- Lambe, A. B. & Martins, J. R. R. A. (2012). *Extensions to the Design Structure
  Matrix for the Description of Multidisciplinary Design, Analysis, and
  Optimization Processes.* Structural and Multidisciplinary Optimization 46(2).
- Martins, J. R. R. A. & Ning, A. (2021). *Engineering Design Optimization.*
  Cambridge University Press.

Related documents, in the `PROCESS_code_analysis` repository:
[T3 execution report](../../PROCESS_code_analysis/dependency_analysis/docs/T3_execution_report.md) ·
[traps and invariants](../../PROCESS_code_analysis/dependency_analysis/docs/TRAPS.md) ·
[tool README](../../PROCESS_code_analysis/dependency_analysis/README.md) ·
[the PROCESS → xDSM interpretation](../../PROCESS_code_analysis/dependency_analysis/docs/PROCESS_architecture_interpretation.md)

In this repository: [`deprecated/IDF_EXPERIMENT_PLAN.md`](deprecated/IDF_EXPERIMENT_PLAN.md) ·
[`idf_probe/`](../idf_probe/README.md)
