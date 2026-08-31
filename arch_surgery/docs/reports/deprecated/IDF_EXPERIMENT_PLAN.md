> **Document status** — **SUPERSEDED · STALE**
> Describes the IDF experiment at commit **`710a75c9`**, not this repository's base `c0ae5b28`.
> **No number in this document is evidence** (decision D4); the study it plans was abandoned and
> its Stage-0 evidence deleted. Retained for **methodology only** — the gate design, the run
> isolation requirements and the measurement approach carried forward; the conclusions did not.
> Superseded by [`../../plans/MDA_PARTITION_EXPERIMENT.md`](../../plans/MDA_PARTITION_EXPERIMENT.md).

# PROCESS optimisation-architecture experiment — consolidated plan (v2)

**Date:** 2026-08-06, last revised 2026-08-10 · **Author context:** W.J. Rutten (TU/e) with Claude Code
**Supersedes:** `ARCHITECTURE_REFACTOR_PLAN.md` (deleted) and all session plan files. **This is the single source of truth for scope, status and terminology.** Executable detail lives in `plans/`; see `plans/README.md` for the index and the document conventions.
**Study commit:** PROCESS `main` @ `710a75c9d2b81053e92918bb6866a0e98f89d814` (fork IPP-SRS/PROCESS, merge of ukaea/main 2026-07-29). Repo: `/home/wrutten/dev_libraries/PROCESS`. Conda env: `PROCESS_env` (Python 3.14.3, PyVMCON 2.4.x; note `click>=8.3.2` was manually installed — a declared dependency missing from the env).

> **Moved 2026-08-19, content otherwise unchanged.** This plan lived at the root of
> `PROCESS_code_analysis`; Track A now has its own workspace and the plan moved here
> with it. Two consequences for the paths quoted throughout the document, which have
> deliberately *not* been rewritten:
>
> * Unqualified paths such as `dependency_analysis/…`, `plans/…` and `bug_reports/…`
>   refer to the [`PROCESS_code_analysis`](../../PROCESS_code_analysis/) repository,
>   not to this one. Track T (the instrument) stayed there.
> * In that repository `plans/` is now [`docs/plans/`](../../PROCESS_code_analysis/docs/plans/)
>   and `bug_reports/` is now [`docs/bug_reports/`](../../PROCESS_code_analysis/docs/bug_reports/).
> * `idf_probe/` moved here, to [`../idf_probe/`](../idf_probe/README.md).
>
> Track A is **deferred**; the status statements below are those of 2026-08-10 and
> have not been re-checked.

## 0. Two tracks, two letters

The project runs two tracks, numbered separately so that no document has to
disambiguate "phase 2":

| | |
|---|---|
| **Track A — the experiment** | **Stages 0, 0.5, 1, 1b, 2, 3, 4.** This document. Owns the research question. |
| **Track T — the instrument** | **Stages T0 … T5.** The dependency-analysis tool (`dependency_analysis/`): the DSM/xDSM extractor Track A's Stage 1 depends on, and a paper contribution in its own right. Planned in `plans/`. |

**Track A Stage 0.5 *is* Track T through T2.** Older documents say "Phase N" for what
is now "Stage TN" (Phase 0→T0 … Phase 5→T5).

**Status at 2026-08-10.** Track A: Stage 0 **DONE**; Stage 0.5 **IN PROGRESS**;
Stages 1–4 **TO DO**, blocked. Track T: T0, T1, T1.5 **DONE**; **T2 is the next work
to execute** and is the only thing standing between the project and Stage 1.

---

## 1. Research context

**Research question.** Does formalising the optimisation architecture of an established multidisciplinary systems code — reconfiguring its optimisers and solvers into an explicitly chosen MDO formulation without modifying its analysis models — measurably improve optimisation performance (cost, robustness) and correctness (well-defined derivatives, verifiable convergence)?

**Why PROCESS.** PROCESS (UKAEA fusion power-plant systems code, ~122 kLOC Python, 77 kLOC of models) is a production example of an *organically grown* architecture: a single SQP optimiser (VMCON) wrapped around an informal fixed-point loop over ~22 hardcoded, non-topologically-ordered models, with 12 equality "consistency" constraints handled IDF-style in the optimiser and further couplings resolved by iteration-until-idempotence. It is the argument's ideal subject because it is *close* to a formal architecture (single level, deterministic, models exchange state through one dataclass) yet exhibits the canonical informalities the MDO literature warns against: convergence-by-heuristic (relative-change early exit with a hidden absolute tolerance), hard failure at an arbitrary sweep cap, hand-patched execution order, silent solver-parameter retries, and evaluation-count bookkeeping that under-reports by ~2×.

**Why this supports the paper.** The paper argues from literature that architecture is a first-class design decision. The strongest evidence is empirical: measure the cost/robustness/correctness anatomy of the as-is architecture (done — Stage 0), then implement a formally chosen architecture reusing the models exactly, and A/B them at the same commit. Track A (Stage 0, complete) already yields a defensible quantified critique even without the refactor.

---

## 2. Background — what literature predicts, and why performance changes with architecture

**Formulations.** Monolithic single-level formulations (Cramer et al. 1994; Martins & Lambe 2013 survey; Martins & Ning, *Engineering Design Optimization*, ch. 13): MDF (optimiser sees only design variables; an MDA fully converges coupling at every evaluation), IDF (coupling targets become optimiser variables with consistency equality constraints; every evaluation is one feed-forward sweep), SAND/all-at-once (all states lifted; residual-form models required). Benchmarks with finite-difference gradients (e.g. Tedford & Martins 2010) generally show IDF ≤ MDF in total analysis evaluations when the coupling dimension is modest, because MDF pays the MDA iteration factor inside every FD perturbation.

**The cost model that makes the prediction concrete.** Total cost ≈ `N_iter · (2n+2) · S · c_sweep + overhead`, where `n` = optimiser dimension, `S` = mean model-sweeps per function evaluation, `c_sweep` = cost of one sweep of all models, `N_iter` = optimiser iterations. Architecture moves each factor:
- **S** — MDF/informal fixed-point pays S per evaluation (measured: **S ≈ 3.25–3.46** here); IDF pays S=1; better sequencing lowers S for any fixed-point scheme.
- **n** — IDF adds k lifted couplings: per-iterate ratio IDF/baseline = `S·(n+1)/(n+k+1)`. With the *actual* n = 14–20 (not the 83-entry registry — an early error, corrected), k is material: at S=3.3, k=10 → 1.96–2.30× per-iterate; at k=20 the small scenario becomes a net loss.
- **N_iter** — governed by gradient fidelity and problem conditioning. Here the as-is architecture's specific defect (established by Stage 0): the delivered FD Jacobian is **history- and order-dependent** — not the Jacobian of any function of x — because the idempotence loop's early exit leaves an O(1e-8) residual whose presence depends on the warm-start state inherited from the previous FD point. Reversing FD evaluation order changes 12/20 Jacobian columns (up to 1.13e-5); the fully converged MDA's FD is order-independent to 0.0. Magnitude is small (~1e-6 Frobenius, vanishing at the optimum), so the honest prediction is a **correctness** improvement with an uncertain, probably modest N_iter effect — not the "~1e-3 gradient noise" originally claimed (refuted) nor "exact gradients" (vacuous for linear objectives).
- **Robustness** — IDF's known weakness: models are evaluated at inconsistent coupling states; PROCESS models can raise hard exceptions there (observed: `znfuel negative` crash). MDF's weakness: MDA may fail to converge (the as-is `RuntimeError` at 10 sweeps). Architecture choice trades these; the experiment measures the trade with randomised-start feasibility rates.

**Expectation to test (calibrated by Stage 0):** IDF-completion yields ~**1.3–1.5× wall clock** on optimisation scenarios (sweep-count gains of ~3× shrink by the k-dimension penalty and the ~35% of wall time outside model sweeps), *plus* restored function-of-x semantics for derivatives, *minus* a robustness cost that consistency constraints and guards must recover. Sequencing alone (no formulation change) should reduce S measurably at zero robustness risk. If the true coupling dimension k comes out large (>~15–20), IDF is unattractive and the formal-MDA (MDF) arm becomes the primary comparison — this decision is Stage 1's output, not an assumption.

---

## 3. Experiment design

### 3.1 High-level code changes (the independent variable)

Architecture arms, all at the same commit, all selected by solver name / env switch so any scenario runs in any arm:

| Arm | What it is | Status |
|---|---|---|
| **baseline** | As-is: VMCON + idempotence loop (`Caller.call_models`). Never modified — its defects are the object of study | exists |
| **resequenced** | Same loop semantics, but the ~22-step model order replaced by a DSM-sequenced order declared as data, and termination formalised (explicit fixed-point/atol-declared criterion — part of the *new* architecture's definition, not a fix to baseline) | Stage 1b |
| **idf** | Single sweep per evaluation; feedback couplings lifted into VMCON as coupling variables + auto-generated consistency equalities (registry injection); **embedded sub-solvers lifted into the optimiser** (unknown → optimiser variable, solver residual → equality constraint); NaN/exception penalty guard | Stage 2 |
| **mdf** | Formal residual-based MDA (Gauss–Seidel + Aitken over declared couplings, explicit tolerance) replacing the idempotence heuristic; **embedded sub-solvers integrated into the MDA** (unknown → MDA state entry, solver residual → component of the MDA residual vector) | Stage 4 |
| **hybrid** | The general case both arms are built as: a per-coupling `lift` flag — lifted couplings go to the optimiser (IDF-style), unlifted ones are resolved by the MDA (MDF-style). Pure IDF and pure MDF are the flag's extremes. **Working hypothesis: the best architecture lifts only the strongest feedback cycles** — plausibly what PROCESS's existing 12 equality constraints already are, historically (worth a commit/docs archaeology aside) | Stage 4 |

**Note (added 2026-08-14, from Track T3.15) — the baseline's existing lifts, and what each arm must do with them.** The constraint classifier (`dependency_analysis/core/constraint_classes.py`, frozen in `gates/constraint_classes.json`) classifies every deck-active constraint by *where its operands come from*, and splits the baseline's equalities into two kinds that the arms must treat differently. Tokamak: **6 TEAR, 7 RESIDUAL, 13 DIRECT** (stellarator: 0 / 5 / 8 + 1 unclassified). This corrects the "12 equality constraints, plausibly the strongest cycles" guess in the **hybrid** row above: only 6 of them are lifts.

- **TEAR = the IDF consistency constraints PROCESS already has.** One operand is an iteration variable the optimiser owns, the other is a model's computation of the same quantity: `icc 11` (`physics.rmajor`, `ixc 3`), `icc 26` (`pf_coil.j_cs_flat_top_end`), `icc 1`/`icc 5`/`icc 24` (`beta_total_vol_avg`, `nd_plasma_electrons_vol_avg`), `icc 68` (`aspect`, `b_plasma_toroidal_on_axis`, `rmajor`). The baseline is therefore a **hybrid MDF/IDF**, not pure MDF, and these six are its pre-existing `lift=True` couplings. **Consequence for the arms: the `mdf` arm is not "baseline + a formal MDA" — it must additionally *demote* these six**, removing the copy variable from `ITERATION_VARIABLES` and the consistency equality from `icc`, and letting the MDA converge the coupling instead. Only then is it a *full* MDF, and only then does the lift-threshold sweep (§3.3 step 4) actually span MDF→hybrid→IDF: without the demotion its "lift none" end is really "lift 6". Demotion is the mirror of the lift transform and belongs in `lift.py`; the positional rule (equalities first in `icc`, §4.2) applies to removals too — `neqns`/`nvar` shrink. Each demotion is independently flagged, so the six are also a ready-made intermediate rung on the sweep.
- **RESIDUAL = SAND-like residuals already promoted to the optimiser, and the plan has no home for them.** Seven tokamak constraints compare two or more *model-computed* quantities with no copy variable anywhere — `icc 2` (global power balance) is nine model fields on both sides. These are governing equations delegated to VMCON: closer to **SAND/all-at-once** than to IDF, and they are in *every* arm by construction, baseline included. Three things follow that Stages 1b/2/4 must decide explicitly rather than inherit: **(i)** they are a third architectural axis the current arm table does not name — the arms differ in MDF/IDF character while all of them stay partially SAND, which must be stated in the paper rather than discovered by a reviewer; **(ii)** an MDA cannot converge them, because the state they would solve for is not lifted anywhere — so the `mdf` arm leaves them with the optimiser, and "full MDF" means *full MDF over the couplings*, a caveat that must appear next to every MDF claim; **(iii)** the alternative — demoting them too, by finding or introducing the implicit state each one closes and moving it into the MDA/sub-solver layer — is a real change of *model* content, which §4.1.2 forbids outside the sub-solver bypass class. **Working decision: leave RESIDUAL constraints with the optimiser in all arms, hold them fixed across the A/B so they cannot confound it, and report the residual SAND character as a stated limit of the study.** Revisit only if Stage 1 shows one of them dominating the coupling structure. Note the two classes are not disjoint in spirit: a TEAR whose copy variable is demoted does not vanish, it becomes an MDA convergence criterion, whereas a RESIDUAL has nothing to become.

**Sub-solver lifting (both formal arms).** The optimisers/solvers embedded inside models are integrated into the architecture rather than nested invisibly inside evaluations. In-loop inventory (tokamak): TF superconductor temperature margin `scipy.optimize.newton` (`models/tfcoil/superconducting.py:1163`), PF/CS temperature margin newton (`models/pfcoil.py:4897`), REBCO current-sharing newton (`models/superconductors.py:282`), vacuum-duct hand-rolled Newton (`models/vacuum.py:416-471`). Not lifted, by taxonomy: the cs_fatigue Paris-law march (time integration, not an implicit state), the PF SVD least-squares (direct solve, not iterative). Mechanism: a per-solver bypass switch inside the model file (~5 lines each: read the unknown from `DataStructure` and skip the internal solve when the arm owns it) — **this is the only change permitted to model files** (boundary condition §4.1.2), and each residual function already exists as a named callable, so the architecture reuses it directly.

### 3.2 Performance measurement (the dependent variables)

Per scenario × arm, from fresh-subprocess runs (methodology proven in Stage 0):
- **Cost:** wall time (primary — sweep counts overstate wall gains by ~35%), total model sweeps, true evaluation count (`ncalls`-derived; `nviter` under-reports ~2×), VMCON iterations, retries/final `epsfcn`.
- **Solution quality gate:** `norm_objf` agreement with baseline + **post-solve feasibility audit** (re-evaluate every original constraint and bound at the returned point). *Not* itvar deltas — Stage 0 showed 5.3% itvar spread at 5.8e-12 objective difference (flat directions ⇒ itvar gates false-alarm).
- **Robustness:** feasibility rate over N randomised starts (±20% within bounds) per scenario × arm; failure taxonomy (ifail codes, exceptions, retry ladder activations).
- **Correctness:** FD-Jacobian order-dependence test (forward vs reversed variable order; fully-converged reference), residual-at-exit statistics, step-size ladder (the as-is `epsfcn=1e-3` is 10–100× above the measured optimum δ≈1e-5 — report both, and A/B at matched epsfcn to avoid confounding).

**Scenarios:** tokamak only — `large_tokamak_nof` (n=20), `low_aspect_ratio_DEMO` (n=19), `st_regression` (n=14) optimisation + `large_tokamak_eval`/`spherical_tokamak_eval` (evaluation mode, fast dev loop). Stellarator/IFE out of scope (own hardcoded callers; the double-`st_phys` hand-fix at `stellarator.py:130-137` is cited as evidence, not refactored).

### 3.3 Coupling identification and strength estimation (the pivotal unknown)

Stage 0's census (state diff between sweeps 1→2 on the exact baseline trajectory) found 459–483 entries still moving, 48 drifting >10% in all scenarios. **This is the inconsistency *footprint*, not the coupling *cut set*.** Precise taxonomy (corrected 2026-08-06): a drifting entry belongs to one of
- **(a) a true cycle** — mutual dependence: A reads what B writes *and* B (possibly via a path) reads what A writes, i.e. the models share a strongly connected component of the dependency graph. No ordering resolves it; these are the genuine coupling candidates. (Candidate examples: Build↔TF coil via winding-pack radii/ripple; Physics↔Pulse via volt-seconds/burn time. **Struck 2026-08-06:** the FirstWall↔blanket `temp_fw_peak` lag — the documented lagged read at `models/fw.py:459-462` is real code but is **config-dead in all four study scenarios** (`i_p_coolant_pumping=3`; the MFILE value 873.0 is the untouched default). A cautionary instance: source comments describing lagged reads are not evidence of an *active* coupling — every candidate must be confirmed against the scenario configuration.)
- **(b) a pure execution-order violation** — a backward edge with *no* return path: the dependency is one-way and the hardcoded order just runs the reader first. Fixed for free by resequencing; needs no lifting. (Likely example: Availability→Buildings lifetimes.)
- **(c) downstream contamination** — the descendant cone of (a)+(b); roughly half the >10% set is costs/power/heat_transport/buildings accounting leaves.

The true k is obtained **in this order** (census strictly *after* sequencing):
1. **Graph:** read-before-write dependency graph over the sweep (ragraph tool, re-targeted to this commit).
2. **Sequencing:** DSM sequencing; the surviving above-diagonal edges are exactly the SCC cut candidates — class (b) is eliminated structurally.
3. **Census re-run under the new order:** the sweeps-1→2 drift and its 2→3→4 decay rate (per-variable contraction ρ; global ρ ≈ 0.05 measured) now measure *only* true-cycle strength plus its cone; rank candidates by drift magnitude, contraction, and targeted freeze tests (hold one candidate at its sweep-1 value, measure objective/constraint displacement).
4. **Decision — a lift *threshold*, not a binary:** the per-coupling `lift` flag makes the arm space continuous; sweep the threshold (lift top-1, top-3, … strongest cycles) and measure. Pure IDF (lift all) and pure MDF (lift none) bracket the sweep; the expected optimum is the hybrid interior. If even the strongest-cycle lift underperforms, the MDF arm is primary and that is a reportable finding.

---

## 4. Software implementation

### 4.1 Boundary conditions (from W.J. Rutten, binding — updated 2026-08-06)

1. **PROCESS may be modified**, preferring maximal reuse of existing code. **Deviation policy:** PROCESS is used as-is; behavioural modifications beyond arm dispatch are made only in very clear cases, each accompanied by a **separate bug report** (a short document explaining the issue and the fix), and only where *not* fixing would make the architecture comparison unfair. Fixes to models themselves are never required. The two termination defects found in Stage 0 (the hidden `atol=1e-8` in `check_agreement`'s `np.allclose`; the loop returning the iterate that *passed* the test instead of the newer one) get bug reports filed regardless, but the corrected termination lives only in the *new-architecture* arms — baseline keeps its defects, because they are what is being measured. Bug reports live in `PROCESS_code_analysis/bug_reports/`.
2. **Model *content* must not change** (`process/models/**` physics/engineering computations frozen), **with exactly one sanctioned change class: embedded sub-solver bypass switches**, so that the optimisers/solvers currently nested inside models are fully integrated into the architecture (see §3.1). Nothing else in model files may be touched. `first_call` latches are resettable from orchestration code (they live in `DataStructure`), which is allowed.
3. **The MDAO architecture must be verifiable and accurate**: declared coupling variables, explicit residual definitions and tolerances, deterministic termination, post-solve feasibility audits, A/B at one commit.
4. **The implemented architecture must be inspectable by the existing dependency-analysis tool** (`PROCESS_code_analysis/dependency_analysis/`, ragraph-based): for each arm/configuration, the tool must run and produce the MDM/graph the same way it does for the original architecture. **Content assertion, not just "it runs"** (a tool finding 3.5% of variables and 0 data edges also "runs" — see `dependency_analysis/docs/COVERAGE_INVESTIGATION.md`): the gate is a scripted check requiring (i) variable coverage ≥ the agreed threshold against an independent ground-truth access extraction, (ii) ≥N model↔model data edges, (iii) an extracted execution order matching the arm's actual caller sequence. **This gate now exists**: `dependency_analysis/gates/gate1/gate1.py`, 11 criteria, run against the frozen ground truth in the same directory (report: `gates/gate1/report.md`). Stage T2 adds a twelfth criterion and a runtime-trace oracle. Implementation implication: arm callers expose a statically-parsable call sequence (a `_call_models_once`-equivalent with resolvable `self.models.<x>.run()` calls — the tool's DFS seed) and prefer **registry-driven dispatch over enum-comparison guards**, which keeps both the DFS seed and `call_index` intact by construction.
5. **Budget cap: €25 out-of-bundle Fable credits** (user's conversion ≈ 2.5 Mtok; actual token yield depends on input/output mix and caching). Division of labour: **Fable orchestrates only** (briefing, reviewing reports, gate decisions); **Opus executes** (all implementation, debugging, runs) within in-bundle subscription sessions. Fable orchestration usage is estimated and tracked separately from that cap (§7); Fable must not be drawn into debugging loops — that work is delegated to Opus agents.

### 4.2 Mechanisms (all verified working or proven in Stage 0)

- **Arm selection:** solver-name dispatch — `get_solver` (`process/core/solver/solver.py:350-380`) + CLI `-s/--solver` + pytest `--solver`/`--opt-params-only` options (`tests/conftest.py:36,42`) give same-commit A/B with zero test changes. The Stage-0 env-var pattern (`PROCESS_IDF_PROBE`, logic concentrated in `process/core/_idf_probe.py`, no-op when unset — currently uncommitted in the working tree) is the template; production arms graduate to solver names.
- **Coupling lift (proven trivial):** `ITERATION_VARIABLES` (`process/core/solver/iteration_variables.py:40`) is a plain dict (free keys ≥200) of `IterationVariable(name, module, lb, ub, target_name, array_index)` with dynamic getattr/setattr into `DataStructure` and auto-normalisation to 1.0; `ConstraintManager.register_constraint` (`process/core/solver/constraints.py:96`) accepts any hashable name. Injection seam: `sr = SingleRun(inp); inject(sr.data); sr.run()` — `SingleRun.__init__` already parses input and populates `DataStructure` (`process/main.py:318-344`). **Positional rule:** equalities must occupy the first `neqns` entries of `icc` (`init.py:1188-1200`) — prepend lifted-consistency icc, bump `neqns`/`nvar`.
- **Caller replacement:** `Evaluators` owns a `Caller` (`evaluators.py:27`); an arm-specific caller duck-types `call_models(xc, m) -> (objf, conf)`. The final MFILE is written by the *independent* `call_models_and_write_output` loop (`caller.py:151-244`), so reported optima are always fully converged regardless of arm — a methodological gift (optimum deltas are real, never lag artifacts).
- **New code lives in** `process/core/` (e.g. `process/core/arch/`): `sequence.py` (declarative Step list, DSM-derived order committed as reviewed data, drift-guard unit test against `caller.py`), `coupling.py` (declarations + strengths from Stage 1, **per-coupling `lift` flag** — the hybrid mechanism), `lift.py` (problem transform + pseudo-itvar MFILE labels so `--opt-params-only` comparisons stay well-defined), `caller_idf.py`, `caller_mda.py`, `subsolver_lift.py` (registry of embedded-solver unknowns/residuals and their per-arm routing), solver registrations. Benchmarks under `benchmarks/arch_ab/`; tests under `tests/arch/`.
- **Sequencing must be adaptable, not trusted.** The dependency-analysis tool is not yet robust (known limitation); any statically-derived order is a *hypothesis*. `sequence.py` therefore supports cheap order overrides (data edit, no code change), and **every candidate order is validated empirically before use**: census drift + sweeps-to-idempotence + `norm_objf` match under the baseline loop semantics. An order that worsens S or breaks idempotence is rejected regardless of what the static analysis says.
- **Sub-solver integration:** each lifted solver contributes (unknown, residual-callable, bounds) to `subsolver_lift.py`; the IDF arm routes it through the same registry-injection path as couplings (unknown → `ITERATION_VARIABLES`, residual → registered equality), the MDF arm appends it to the MDA state/residual vectors. The model-side bypass switch (§3.1) is the single sanctioned model edit; the residual callables already exist as named functions and are reused unmodified.
- **Formalised termination** (new-architecture arms only; baseline untouched): explicit fixed-point criterion with declared atol/rtol; the two baseline termination defects are documented as bug reports per §4.1.1 (Stage 0 showed one extra sweep makes most carried residuals bitwise zero).
- **Analysability (§4.1.4):** each arm's caller keeps a statically-resolvable call sequence so the ragraph tool can trace it; running the tool on the arm and producing its MDM is a standing V&V step.

### 4.3 Run methodology (proven)

Fresh subprocess per run, own work dir (`OutputFileManager._outfile/._mfile` are class attributes — process-wide singletons); warm numba caches before timing (first cold run costs ~45 s JIT vs ~4 s warm); record final `epsfcn` + retry count on every run (`solver_handler.py:61-67` retries silently); baselines self-generated (fork commits may lack tracking-repo references); reproducibility gate: two independent baseline runs bit-identical (held exactly in Stage 0).

---

## 5. Gated implementation approach, agent orchestration, V&V

| Stage | Content | Gate (go/no-go) | Est. sessions |
|---|---|---|---|
| **0 — DONE** | Probe: sweep anatomy (S≈3.3), single-sweep A/B (1.94× wall on `nof`; 2 of 3 scenarios fail without consistency), census footprint, noise/correctness analysis (order-dependent Jacobian; epsfcn 10–100× above optimal) | — | done (~2 sessions incl. verification) |
| **0.5 — Instrument (IN PROGRESS)** | **= Track T, Stages T0–T2** (table below). Far larger than the "4 defects, ≈1 day" this row originally scoped: the repair turned out to need ~15 fixes, a rewritten configuration model and a gate suite. T0/T1/T1.5 are done; **T2 is outstanding and is the only blocker on Stage 1** | Gate 1 (11 criteria) passes **[held, 11/11]**; Gate 2 (runtime-trace oracle: runtime accesses ⊆ static graph; every statically-pruned branch unexecuted) passes; `DIFFERENTIAL_VALIDATION.md` signed off | ~2 agent-days remaining (T2); ~4 spent (T0–T1.5) |
| **1 — Coupling & sequencing analysis (GATING)** | Read-before-write graph over the sweep on the repaired tool; DSM sequencing; candidate cut set ∩ census strengths (census re-run **after** sequencing); decide k and the primary arm | Cut-set table with strengths exists; k decided; arm chosen | 1–3 |
| **1b — Resequenced arm** | `sequence.py` order + formalised termination variant; measure S drop and Jacobian order-independence | `norm_objf` match + feasibility audit; S not worse | 1–2 |
| **2 — IDF arm** (if k permits) | Registry-injection lift of the cut set **+ sub-solver lifting** (unknowns → optimiser variables, residuals → equalities; model bypass switches per §3.1); single-sweep caller; NaN/exception penalty guard; pseudo-itvar output; ragraph tool runs on the arm | `norm_objf` match + audit on 3/3 scenarios; wall time < baseline; robustness ≥ baseline − ε; arm MDM produced | 2–4 |
| **3 — Benchmark & robustness** | Full matrix: scenarios × arms × N randomised starts; paper tables/figures | Reproducible artifact (scripts + JSONs) | 1–2 |
| **4 — MDF arm + hybrid sweep** | Residual GS+Aitken MDA over declared couplings with sub-solvers in the MDA state; then the **lift-threshold sweep** (lift top-1, top-3, … strongest cycles) spanning MDF→hybrid→IDF — the experiment's expected headline figure | `norm_objf` match + audit; ragraph MDM per configuration | 2–4 |

### Track T — the instrument

| Stage | Content | Gate | Status | Plan |
|---|---|---|---|---|
| **T0** | Pin PROCESS at `710a75c9`; extract the analysis target to `dependency_analysis/reference_trees/`; freeze an independent ground-truth access extraction | archive clean; ground truth frozen | **DONE** 2026-08-07 | `plans/deprecated/v2_master_assessment.md` §B |
| **T1** | Repair: `self.data.<g>.<v>` recognition, full-tree enum registry, static MRO for inherited methods, secondary entry methods, local aliases, subscript reads, edge `family` annotation, `AnalysisContext`, config from IN.DAT | **Gate 1, 11 criteria** | **DONE** — 11/11 | `gates/gate1/report.md` |
| **T1.5** | Diagnostics-driven defects: `n_divertors` and `iohcl`/`i_hcd_calculations` correctness bugs, `[1.A]` classification, membership/enum-payload/local-scalar evaluation, three missed call classes, post-init config dump, instance-state edges | Gate 1 still 11/11; every edge loss carries a counterfactual | **DONE** 2026-08-10 | `dependency_analysis/docs/T1_5_diagnostics_report.md` |
| **T2** | **Validation & oracles**: compound-argument decomposition, one shared conditional evaluator, **runtime-trace oracle**, differential validation report, canonicaliser + reference re-cut, test overhaul, gate hardening | Gate 1 → 12/12; Gate 2 (runtime ⊆ static); signed differential report | **TO DO — next** | `plans/T2_validation_and_oracles.md` |
| **T3** | Workflow drivers + COOR: driver nodes, comment-directive scanner, five registry loaders, MDM with drivers | flags-off identity; registry cross-checks; `[1.K]` empty | **TO DO** (paper, not Track A) | `plans/T3_workflow_drivers_and_coor.md` |
| **T4** | Model/submodel hierarchy: two-level graph, build-time roll-up check, projection for mixed-level display | aggregation A1–A6 + synthetic fixture; flags-off identity | **TO DO** (paper, not Track A) | `plans/T4_submodel_hierarchy.md` |
| **T5** | Integration & closure: both feature flags together, final differential re-validation, README/doc updates, sub-solver inventory correction (**five**, not four — two are closures: `deltaj_rebco` and the confinement-time `root_scalar(fhz)`) | both flags on, gates hold | **TO DO** | this file |

**Track A opens at Stage 1 when T2 closes.** T3 and T4 serve the paper's xDSM
contribution and must not delay it — they may run in parallel with Stage 1, or after.

**Every Track-T stage closes with a README re-baseline, not with its gate pass.** The
last work package of each stage rewrites `dependency_analysis/README.md` to describe
the tool *as it now is* — behaviour, data model, diagnostics, file structure,
limitations, run commands — together with that stage's headline numbers, so the README
is the standing baseline of the code and never lags behind it. The stage report says
what happened; the README says what is true now. A stage whose gate passes while its
README still describes the previous behaviour is **not done**: the next stage would
then be planned against a stale description, which is precisely how the tool acquired
the drifted lookup tables that Stage T1 had to remove. Convention and per-stage detail:
`plans/README.md`.

### Honest status assessment (2026-08-10)

1. **The instrument has outgrown its brief, and that was necessary but must now stop.**
   Stage 0.5 was scoped at "≈1 day, 4 defects". It has cost ~4 agent-days and found
   ~15 defects, two of them live correctness bugs that decided branches the wrong way.
   That was the right call — a wrong DSM would have silently distorted every arm built
   on it — but T3 and T4 are another ~10 agent-days, and they buy the *paper*, not the
   experiment. **Do not let them precede Stage 1.**
2. **The evidence is still mostly self-referential.** 446 unit + 58 integration tests
   check the tool against itself. There are three independent oracles, and the newest
   of them found a live bug on its first run. Until T2's runtime-trace oracle exists,
   the honest confidence statement is: *the tool is internally consistent and agrees
   with the eight couplings and two configurations we have checked by hand.*
3. **Gate 1 cannot currently fail for the most important reason.** It scored 11/11
   both before and after T1.5 made an entire call class visible (+1 model node, +59
   edges). Criterion 8 in T2.7 fixes this. Treat the current 11/11 as *necessary, not
   sufficient*.
4. **Two Track-A assumptions are still unverified** and Stage 1 is where they get
   tested: that the coupling cut set is small enough for IDF (risk 1), and that a
   statically-derived order is trustworthy enough to sequence with (risk 5). Neither
   is a tool problem; both are why Stage 1 is gating.
5. **Nothing in Track A has been invalidated by the tool work.** Stage 0's numbers
   were measured by runtime instrumentation, independent of the static analysis, and
   stand as written.

**Agent orchestration.** **Fable is the orchestrator** (briefs agents, reviews their reports, runs gate checks, makes stage decisions — nothing else); **Opus agents execute** (all implementation, debugging, benchmark runs), in in-bundle sessions. One orchestrating pass per stage; human review at every gate (gates are cheap: `pytest tests/regression --solver=<arm> --opt-params-only` + the audit script + the ragraph run). Parallelise *runs* as background subprocesses, not agents. Fan out Opus subagents only where work is independent: per-scenario debugging in Stage 2, per-arm benchmark sweeps in Stage 3, tool-adaptation vs analysis in Stage 1. Every agent brief must contain: this file's path, **its stage's plan under `plans/`**, the study commit, the env, the boundary conditions (§4.1), the injection recipe (§4.2), the run methodology (§4.3), and its stage's gate. Track-T briefs must additionally point at `dependency_analysis/docs/TRAPS.md`. Stage-0 artifacts to reuse, not re-derive: `idf_probe/MEMO.md`, `idf_probe/NOISE_ANALYSIS.md`, `idf_probe/runs/**/*.json`, `idf_probe/noise_deepdive.py`, the census mode in `process/core/_idf_probe.py`.

**Verification & validation.**
- Unit: sequence-equivalence test (declared order vs `caller.py` statically parsed — drift guard against upstream); lift-transform tests (positional equality split preserved; bounds transferred); caller contract tests.
- Solution validity: post-solve audit re-evaluating **all original** constraints/bounds at the returned point — mandatory at every gate; `--opt-params-only` regression comparisons (original itvar subset; lifted variables as clearly-labelled extras).
- Methodology validity: switch-neutrality (arm machinery inert ⇒ bit-identical to baseline), reproducibility gate, retry-matched and epsfcn-matched timing comparisons, warm-cache timing only.
- Claims validity: every paper number backed by a JSON under version control; the correctness claims reproduced by `noise_deepdive.py`-style scripts (order-reversal test, step ladder, line scans).

---

## 6. Format of expected results

1. **Anatomy table** (as-is architecture): S per scenario/phase, true vs reported evaluation counts, retry activations, residual-at-exit stats. *(Exists — Stage 0.)*
2. **Correctness exhibit:** order-reversal Jacobian test (12/20 columns change; 0/20 when fully converged), step-size ladder with the V-curve and epsfcn mark, line-scan staircase near/far from optimum. *(Exists — Stage 0/noise deep-dive; re-run per arm.)*
3. **Coupling exhibit:** DSM before/after sequencing; cut-set table (variable, writer→reader, drift magnitude, contraction ρ); footprint-vs-cut-set figure. *(Stage 1.)*
4. **A/B cost table:** scenarios × arms — wall time, sweeps, evaluations, VMCON iterations, `norm_objf` delta, audit pass. *(Stages 1b–4.)*
5. **Robustness figure:** feasibility rate vs randomised starts per arm; failure taxonomy. *(Stage 3.)*
6. All under `benchmarks/arch_ab/` (scripts) + `runs/` (JSONs) + generated figures; every number traceable to a JSON.

---

## 7. Time, cost, risks, feasibility — honest judgement

**Time.** Stages 1–3 (core): **5–9 focused Claude Code sessions** (5-h limit windows, 2–4 h active each), realistically **1.5–3 calendar weeks** with gate reviews. +2–4 sessions for the MDF arm + hybrid sweep. Calibration: the entire Stage-0 probe including an independent verification pass and the noise deep-dive took ~3 agent-invocations totalling ~0.4M subagent tokens and ~1.5 h of agent wall time — the earlier 80–250M token estimate was over-conservative by an order of magnitude for probe-class work; heavy debugging stages (2) will cost more, but **5–30M tokens total (Opus execution, in-bundle)** is the better central estimate (throughput including cache reads higher; sessions are the binding budget, and Stage 2 is the variance driver).

**Fable budget (out-of-bundle, cap €25 ≈ 2.5 Mtok by the user's conversion — actual yield depends on I/O mix and caching).** Fable does orchestration only: per stage roughly one briefing pass, one report-review pass, one gate pass ≈ 100–300k tokens/stage → **estimated 0.6–1.8 Mtok across Stages 1–4**, inside the cap with margin *provided Fable never debugs*. Tracked per stage; hard stop with a report to the user if cumulative Fable usage reaches 80% of the cap. Opus execution costs are accounted separately (in-bundle sessions, above) and do not draw on this budget.

**Top risks (with mitigations).**
1. **k comes out large (>15–20)** → IDF per-iterate advantage evaporates. *Mitigation:* Stage 1 is gating; pivot to MDF arm as primary; "IDF infeasible at measured k" is itself a publishable, literature-relevant result.
2. **Model exceptions at inconsistent states** (observed: `znfuel` crash) make the IDF arm fragile. *Mitigation:* penalty guard + bounds from baseline ranges + consistency constraints (the probe deliberately lacked them); budgeted explicitly in Stage 2.
3. **The performance win is modest (~1.3–1.5×)** and reviewers ask "so what". *Mitigation:* the paper's spine is architecture-as-correctness (history-dependent Jacobians, silent retries, 2× evaluation under-reporting, hidden tolerances) with cost as one axis; Stage-0 results already carry this.
4. **The dependency-analysis tool was unfit for purpose** — *materialised, not hypothetical* (`dependency_analysis/docs/COVERAGE_INVESTIGATION.md`, 2026-08-06): as committed it found 3.5% of variables (really 0.0% — the 73 "variables" were enum members), **0 model↔model data edges**, and 0/8 of this plan's appendix couplings, while exiting 0 and emitting a plausible-looking MDM — a silent failure mode that could have propagated a wrong DSM into every downstream conclusion. *Status 2026-08-10:* **largely closed.** Track T's T0–T1.5 delivered 154 derived model↔model edges (tokamak), 8/8 curated couplings, exact `caller.py` execution order, and Gate 1 at 11/11 — but at ~4× the estimated cost, and it exposed two further live correctness bugs (`n_divertors`, `iohcl`/`i_hcd_calculations`) that the original defect list never mentioned. *Residual risk:* the validation is still largely self-referential; T2's runtime-trace oracle is what converts "internally consistent" into "checked against a real run". The fallback if T2's oracle stalls is unchanged — a runtime-instrumented read-before-write trace (census-style hooks already exist in `_idf_probe.py`), which is in fact the same instrument. **Standing lesson, now paid for twice: treat every static-analysis output as unvalidated until checked against an independent extraction.**
5. **Imperfect sequencing** — the dependency analysis is not yet robust; a wrong statically-derived order could silently distort every arm built on it. *Mitigation:* orders are hypotheses validated empirically before adoption (census drift + S + `norm_objf` under baseline semantics — §4.2); `sequence.py` is data, adaptable per configuration without code changes; the baseline order is always retained as a fallback arm configuration.
6. **Sub-solver lifting destabilises the optimisation** (temperature-margin unknowns give VMCON/MDA stiff, narrow-range states; model bypass switches add per-arm behaviour divergence in model files). *Mitigation:* per-solver lift flags (each independently revertible); bounds from baseline-run ranges; bypass switches are ~5 lines each behind a single registry check, unit-tested for inertness when unset.
7. **Fable budget overrun.** *Mitigation:* strict orchestration-only role; per-stage tracking; hard stop at 80% of the €25 cap with a report.
8. **Upstream drift / uncommitted probe code lost.** *Mitigation:* user commits the probe instrumentation to a branch now (manifest: new `process/core/_idf_probe.py`; +14/-1 `caller.py`; +10/-1 `evaluators.py`; +4 `solver_handler.py`); pin the study commit for all arms.

**Feasibility verdict.** **High confidence** that Stages 1–1b and 3 deliver publishable, quantified results regardless of outcomes (they measure; they don't bet). **Moderate confidence** in the IDF arm as the performance headline — it is hostage to k, and Stage 0's evidence says couplings are not weak. The experiment is deliberately structured so that every branch of the decision tree (IDF wins / IDF infeasible at k / MDF formalisation wins on correctness at equal cost) produces a defensible paper claim. What this experiment cannot deliver: bit-exact reproduction of baseline optima (project's own regression policy accepts solution drift; gates are objective+feasibility based), or architecture gains from analytic derivatives (out of scope — models frozen, FD retained).

---

## Appendix — quick-reference for future agents

- **Flow:** `process_cli` → `SingleRun` (`process/main.py:318`) → `Scan.doopt` (`core/scan.py:244`) → `SolverHandler.run` (`core/solver/solver_handler.py:30`, retry ladder :61-67) → `Vmcon`/`FSolve` (`core/solver/solver.py`; `get_solver` :350) → `Evaluators.fcnvmc1/2` (`core/solver/evaluators.py:31,84`; central FD, `epsfcn=1e-3` `data_structure/numerics.py:556`) → `Caller.call_models` (`core/caller.py:70`; `check_agreement` :47 — `np.allclose(rtol=1e-6)` **with numpy default `atol=1e-8`**) → `_call_models_once` (`caller.py:246-394`, hardcoded ~22-step tokamak sequence; stellarator/IFE early-return).
- **State:** one `DataStructure` (`core/model.py:46-88`, 36 sub-dataclasses, ~2290 fields); models read/write freely (~11.8k access sites); `first_call` latches `physics_variables.py:433`→`physics.py:1352`, `pfcoil_variables.py:115`→`pfcoil.py:617`; plasma Profile arrays live on model instances.
- **Numbers (Stage 0, `large_tokamak_nof` unless noted):** n=20/19/14; S=3.25/3.46/3.27 (floor 2 structural); single-sweep: 3.05× sweeps, 1.94× wall, Δobjf 5.8e-12, but `low_aspect_ratio_DEMO` ifail=2 and `st_regression` crashes; census: 473/483/459 entries drift, 48 common >10%; contraction ρ≈0.05; FD: order-reversal flips 12/20 columns (≤1.13e-5), converged-MDA FD order-independent, optimal δ≈1e-5; sweep cost ~12 ms.
- **Artifacts:** Stage-0 evidence `PROCESS_code_analysis/idf_probe/{MEMO.md, NOISE_ANALYSIS.md, noise_deepdive.py, runs/**}`; the instrument `PROCESS_code_analysis/dependency_analysis/` (now pinned to `710a75c9`, analysed from `reference_trees/PROCESS_at_710a75c9/` — **never** the live tree); explainer for the user: `PROCESS_code_analysis/EXPERIMENT_EXPLAINER.md`; repo map: `PROCESS_code_analysis/README.md`.
- **Instrument entry points:** `dependency_analysis/README.md` (how it works), `dependency_analysis/docs/TRAPS.md` (**read before touching anything**), `dependency_analysis/gates/gate1/gate1.py` (the §4.1.4 content gate), `dependency_analysis/gates/run_analysis.py` (one config, one tree, one output dir).
- **Probe instrumentation (env-gated `PROCESS_IDF_PROBE`, inert unset):** `process/core/_idf_probe.py` + small hooks in `caller.py`/`evaluators.py`/`solver_handler.py`. Committed to branch `stage0-probe` in `~/dev_libraries/PROCESS`; the live tree sits on that branch, which is why every tool and PROCESS-side script must be pointed at the pinned archive explicitly.

---

## Change log

Append-only. Each row says what changed and why; the reason a decision was reversed
is usually more valuable than the decision.

| date | change |
|---|---|
| 2026-08-05 | First consolidated version, superseding `ARCHITECTURE_REFACTOR_PLAN.md`. |
| 2026-08-06 | Stage 0 closed. Coupling taxonomy corrected (footprint ≠ cut set; classes a/b/c). `temp_fw_peak` struck as a live coupling candidate — config-dead in all four study scenarios. Sub-solver lifting added as the one sanctioned model-file change (§3.1, §4.1.2). **Stage 0.5 added** after `COVERAGE_INVESTIGATION.md` found the dependency tool finding 3.5% of variables and 0 data edges. Fable-budget cap (€25) and the orchestrate-only division of labour recorded (§4.1.5). |
| 2026-08-10 | **§0 added: two tracks, two letters.** The instrument work was called "Phase N" and collided with the experiment's "Stage N"; it is now **Track T, Stages T0–T5**, planned in `plans/`. Stage 0.5 rewritten to reference Track T and re-scoped honestly (≈1 day → ~6 agent-days). Track T status table and an **honest status assessment** added to §5. §4.1.4's gate now points at the gate suite that exists (`gates/gate1/gate1.py`) instead of two scratch scripts that were deleted. Risk 4 updated from "unfit for purpose" to "largely closed, residual risk is self-referential validation". Appendix paths updated for the repo restructure; probe instrumentation recorded as committed to branch `stage0-probe`. Sub-solver inventory correction (five, not four) scheduled in T5. |
| 2026-08-10 | Standing convention recorded (§5): **every Track-T stage closes with a README re-baseline, not with its gate pass.** Added as a closing work package in each stage plan (T2.8, T3.10, T4.9), as a gate condition, and as a convention in `plans/README.md`. |
| 2026-08-14 | **§3.1 note added from Track T3.15's constraint classification.** The baseline's equalities split 6 TEAR / 7 RESIDUAL / 13 DIRECT (tokamak), so PROCESS is a hybrid MDF/IDF with six pre-existing lifts — not the 12 the hybrid row guessed. Two consequences recorded as plan work: the **`mdf` arm must demote the six TEAR constraints** (copy variable out of `ITERATION_VARIABLES`, consistency equality out of `icc`) or it is not a full MDF and the lift-threshold sweep does not reach its MDF end; and the seven **SAND-like RESIDUAL constraints** (governing equations with no copy variable, e.g. `icc 2`) have no home in the arm taxonomy — working decision is to leave them with the optimiser in every arm, held fixed across the A/B, and report the residual SAND character as a stated limit. |
