# Changes to the PROCESS source in this copy

> **Document status** — reference, written 2026-09-14 (task A69 (process-copy-changes-doc)) from
> the diffs, not from the prose: every snippet below is copied from `git diff` between the named
> commit and the file on disk. The authoritative list of the copy's own edits is
> `PERMITTED_EDIT_FILES` in [`copy_gates.py`](copy_gates.py); the recorded hunks and post-edit
> digests are in [`PROVENANCE.json`](PROVENANCE.json). If this document and those two ever
> disagree, they are right and this is stale. §6 says how to check.

Written for a reader who knows PROCESS but has not followed this project.

---

## 1. What this copy is

`PROCESS/process/` is a complete copy of the PROCESS package, run by the experiment's harness
instead of the repository-root `process/` (decision D20). It is selected by `PYTHONPATH`, never by
an install (trap T6), and every measurement subprocess asserts `process.__file__` is under it.

**Two layers of change sit on top of upstream PROCESS.**

1. **The frozen base is `c0ae5b28`** (decision D5). The repository-root `process/` was developed
   on from that commit — on the `architecture_surgery` branch, never on `main` — through the
   earlier revisions of this experiment, and the copy was extracted with
   `git archive f2dc9243 process` (the source commit named in `PROVENANCE.json`). So the copy
   *inherits* every change made to the root tree between `c0ae5b28` and `f2dc9243`: thirteen files,
   all of them under `process/core/`, plus `process/data_structure/numerics.py` (decision D14(a))
   and `process/models/pulse.py` (decision D14(b)). §3 documents that layer.
2. **The copy's own edits**, made after extraction and recorded one by one in
   `copy_gates.PERMITTED_EDIT_FILES`: seven files, twenty-seven recorded edits. §4 documents that
   layer, one subsection per recorded edit.

Relative to the frozen base, then, the copy differs in **fourteen files**: six that do not exist
at `c0ae5b28` (`_idf_probe.py`, `_idf_probe_frozen.py`, `_idf_probe_harvest.py`,
`_idf_probe_modules.py`, `solver/module_solve.py`, `solver/subsolve.py`) and eight that do
(`caller.py`, `solver/__init__.py`, `solver/constraints.py`, `solver/evaluators.py`,
`solver/iteration_variables.py`, `solver/solver_handler.py`, `data_structure/numerics.py`,
`models/pulse.py`). The other 210 files are byte-identical to upstream at `c0ae5b28`.

**What is not changed.** Every file under `process/models/` is byte-identical to `c0ae5b28`
with one approved exception, `pulse.py` (§3.9), whose arithmetic is verbatim and whose expected
content is pinned by sha256. Gate **G0′** (`frozen-physics` in `copy_gates.py`) compares the
copy's `models/` against the *commit* `c0ae5b28` — read with `git cat-file`, never a working
tree — and fails on any other difference, on a missing file and on an added file. The rule
behind it: the experiment varies the *arrangement* of solvers and loops (the driver) and holds
*what each model computes* fixed; a change to the latter changes the independent variable and
invalidates the comparison (D5). Structural edits under `models/` that extract a residual so its
solution method becomes a driver choice, without changing what is computed, are permitted only
with the user's approval (D11) — `pulse.py` is the one such case.

**How the edits are switched.** Every driver change is behind an environment variable of the
form `PROCESS_ARCH_*` (the architecture switches, §2) or `PROCESS_IDF_PROBE` (the census
instrument). All are **read once at import** and resolved into module-level constants; none is
consulted per call. With every variable **unset** the copy takes upstream's own paths line for
line, and that is a gate rather than a claim: **G1** (switch neutrality, `harness/gates/gates.py`)
runs one optimisation and one evaluation per configuration with the whole switch vocabulary
cleared, before and after each driver change, and compares every deterministic value of the two
records and every line of PROCESS's own output file. Every switch name an earlier revision used
and this one retired **raises** if set (§4.1): an ignored switch runs a different arrangement
under the right name, which is a wrong answer with no symptom.

---

## 2. The switches

*One row per environment variable the copy reads. "Arms" are the columns of the experiment
plan's §3.2 matrix that set it (`AR`/`BR` are PROCESS as shipped and set nothing; the harness
clears every switch before composing an arm). "Reads it" names the file that resolves the
variable. "Change" names the driver change of the harness plan (`DR<n>`) where one exists, and the
task that made it.* *Arm names are the matrix's names since 2026-09-15 (`AR/A0/A1/A2`, `BR/B0/B1/B2`;
task A78 (arm-renames)); a run record or a document dated earlier spells the two Phase A arms after
the control and the partitioned optimisation arm differently — the table
`harness/core/records.py::RECORDED_ARM_NAMES` says how. The `A1`, `A2` in "inherited (A1, A2, A18,
A19)" below are task numbers, not arms.*

| variable | values | arms that set it | reads it | change / task |
|---|---|---|---|---|
| `PROCESS_ARCH_MDA` | `flat`, `partitioned` (unset = upstream's loop) | `A0`,`A1`,`B0`,`B1` → `flat`; `A2`,`B2` → `partitioned` | `solver/module_solve.py`, read back in `caller.py` | inherited (VP4, A25/A28); renamed by DR1 (A56) |
| `PROCESS_ARCH_TAU` | a number, default `1e-6` | every non-reference arm | `solver/module_solve.py` | inherited (A25, D15); the only tolerance since D23 |
| `PROCESS_ARCH_COUPLING_STATE` | a file | every non-reference arm | `solver/module_solve.py` | inherited; renamed by DR1 (A56) |
| `PROCESS_ARCH_WRITE_SETS` | a file | every non-reference arm | `solver/module_solve.py` | inherited; renamed by DR1 (A56) |
| `PROCESS_ARCH_ARRANGEMENT_NODE` | `build_after_physics` | `A2`, `B2` | `caller.py` | inherited (VP1, A3); renamed by DR1 (A56) |
| `PROCESS_ARCH_ARRANGEMENT_METHOD` | `fw_geometry` | `A2`, `B2` | `caller.py` | inherited (VP6, A40, D19); renamed by DR1 (A56) |
| `PROCESS_ARCH_DEFER_PER_CALL` | `feedforward`, `feedforward_lifted` | `A2`, `B2` (`feedforward_lifted` on pulsed configurations) | `caller.py` | inherited (VP2, A13); renamed by DR1 (A56) |
| `PROCESS_ARCH_DEFER_PER_RUN` | a file | `A2`, `B2` | `caller.py` | inherited (VP2c, A33); renamed by DR1 (A56) |
| `PROCESS_ARCH_BURN_TIME_OWNER` | `loop` (default), `optimiser`, `constant:<hex float>` | `A1`,`A2` → `constant:…`; `B1`,`B2` → `optimiser` (pulsed configurations only) | `solver/subsolve.py`, read back in `caller.py`, named in `solver/constraints.py` | inherited (VP5, A4/A34); folded from two switches by DR1 (A56) |
| `PROCESS_ARCH_OUTPUT_LOOP` | `upstream` (default), `none` | `B1`, `B2` → `none` | `caller.py` | DR2 (A57) |
| `PROCESS_ARCH_PREDICATE` | `frozen` (default), `mixed` | none in the campaign; the §3.6 trial only | `solver/module_solve.py`, passed at the call site in `caller.py` | DR5 (A59) |
| `PROCESS_ARCH_PASS_TRACE`, `…_PASS_TRACE_FULL_FROM` | a file; a number | never; observation only | `solver/module_solve.py` | inherited (A31) |
| `PROCESS_IDF_PROBE`, `…_PROBE_OUT` | `baseline`, `modules`, `harvest`, `frozen`; a file | never by an arm; the census stage only | `core/_idf_probe.py` and its mode modules | inherited (A1, A2, A18, A19) |

Retired names, each of which raises at the import of `process.core.solver` (§4.1):
`PROCESS_ARCH_MODULE_SOLVE`, `_OUTER`, `_INNER_TAU`, `_SEQUENCE`, `_PRIME`, `_HOIST`,
`_POST_SOLVE`, `_LIFT`, `_PIN_BURN_TIME`, `_YSTATE`, `_WRITESET`.

Things the driver *reports* and nothing sets — `NODE_CALLS`, `DISPATCH_SWEEPS`,
`OUTPUT_LOOP_SWEEPS`, the predicate counters, `ATTEMPT_STAMPS` and the rest — are counters, not
switches; the harness README §4.1 lists them with their record fields.

---

## 3. Changes inherited from the source commit (`c0ae5b28` → `f2dc9243`)

These were made to the repository-root `process/` by the earlier revisions of the experiment and
came into the copy with the extraction. They are gated here only indirectly: `copy-identity`
proves the copy *is* `f2dc9243:process/` bar the edits of §4, and the root tree's history from
`c0ae5b28` is what says these thirteen files are the whole of the difference. Snippets in this
section are shown with the **names the copy uses now**; where §4's rename edit changed a name,
the `f2dc9243` spelling is given in parentheses.

### 3.1 `process/core/_idf_probe.py` and its mode modules — new files

**What.** An env-switched census instrument: `_idf_probe.py` is the switch and the counters,
imported unconditionally by the driver files; `_idf_probe_modules.py`, `_idf_probe_harvest.py`
and `_idf_probe_frozen.py` are imported only when `PROCESS_IDF_PROBE` names their mode.

```python
_raw = os.environ.get("PROCESS_IDF_PROBE", "").strip()
MODE: str | None = _raw or None
ENABLED: bool = MODE is not None
```

Every hook site in the driver is of the form

```python
        if _idf_probe.ENABLED:
            _idf_probe.sweep(self.models, self.data)
```

**Why.** The experiment needed to know, from the shipped code and before any refactor, which
model writes which field, how many sweeps each candidate module would need if iterated alone,
and the design points at which to replay the fixed point (tasks A1, A2, A18, A19). The `modules`
mode attributes every read and write of a data-structure field to the model node executing at
the time, confined to the body of `_call_models_once` so that `output()`'s re-entry into `run()`
is excluded structurally (trap T7). The harness's census stage reads its report.

**Driver, not model.** No model file is touched; the hooks sit in the loop, and with the variable
unset every hook is one global boolean load. Attributing a write to a node does not change the
write.

### 3.2 `process/core/caller.py`

At `c0ae5b28` this file is 530 lines; at `f2dc9243` it is 1 859. Everything added is in the
driver's loop, its dispatch and its module-level constants. The features, in the order they
appear in the file:

**Node dispatch and the cost counter.** Every model call in `_call_models_once` was rewritten
from a direct call to a call through one method:

```python
-        self.models.pfcoil.run()
+        self._node("pfcoil", self.models.pfcoil.run)
```

and that method is where every variant point meets:

```python
    def _node(self, name: str, run) -> None:
        if self._active_nodes is not None and name not in self._active_nodes:
            return
        if self._defer_per_run is not None and name in self._defer_per_run:
            ...
            return
        if self._pending is not None and name in self._deferred_tail:
            self._pending.append((name, run))
            return
        NODE_CALLS[0] += 1
        run()
```

*Why.* The experiment's cost unit is the **model node call**, not the sweep: a block sweep runs
one module, so `numerics.n_model_calls` (sweeps) is not comparable between a flat loop and a
block schedule. `NODE_CALLS` is a plain integer increment per node call, on every arm. With every
switch unset the three guards are `None` tests and the call is made exactly where it was.

**Arrangement at node granularity (VP1, task A3).** The first three calls of the tokamak sequence
became a table lookup:

```python
_ARRANGEMENT_NODE_ORDERS: dict[str, tuple[str, ...]] = {
    "upstream": ("plasma_geom", "build", "physics"),
    "build_after_physics": ("plasma_geom", "physics", "build"),
}
...
        for _head_node in ARRANGEMENT_NODE_HEAD:
            self._node(_head_node, getattr(self.models, _head_node).run)
```

(`SEQUENCE_HEAD` / `PROCESS_ARCH_SEQUENCE` at `f2dc9243`.) *Why:* the dependency analysis puts
`build` in the coils block, after physics; moving it there gives the physics block a contiguous
span so it can be iterated on its own. A permutation of three calls, not a scheduler.

**Arrangement at method granularity — the prime (VP6, task A40, decision D19).**

```python
        if ARRANGEMENT_METHOD_FW_GEOMETRY:
            ARRANGEMENT_METHOD_CALLS[0] += 1
            self.models.fw.set_fw_geometry()
```

at the head of every sweep (`PRIME_FW_GEOMETRY` / `PRIME_CALLS` at `f2dc9243`). *Why:*
`FirstWall` computes a run-constant of two input values (`build.dr_fw_inboard` /
`dr_fw_outboard`) that `Build`, earlier in the schedule, reads from the *previous* pass; task A35
found it to be the one cut edge carrying a displaced entry into a one-pass exit. Running the
method first removes the lag. It is stamped (`n_prime_calls`), not counted as a node, so node
counts stay commensurable.

**Deferral per call — the feed-forward tail (VP2, task A13).** Nodes in the node map's `FF`
module (`water_use`, `costs`; plus `pulse` under `feedforward_lifted`) are collected instead of
run during the loop and run once after the fixed point:

```python
        if DEFER_PER_CALL_ENABLED:
            (
                self._defer_per_call_pre,
                self._defer_per_call_post,
            ) = self._resolve_defer_per_call_tails()
```

(`HOIST_*` / `PROCESS_ARCH_HOIST` at `f2dc9243`.) Which deferred nodes run *before* the objective
and constraints are evaluated is derived from the measured per-node write sets
(`NODE_WRITESET_PATH`) intersected with the predicate layer's read set, parsed from
`objective_function`'s figure-of-merit chain; a node the predicate reads is never left stale.
*Why:* nodes downstream of everything the loop decides are wasted work on every sweep but the
last.

**Deferral per run (VP2c, task A33).** Nodes whose outputs neither the objective nor any active
constraint reads leave the per-call path entirely and run once, at the accepted optimum:

```python
    if DEFER_PER_RUN_ENABLED:
        ps = _defer_per_run_nodes(data)
        ...
        if ps:
            caller._sweep_block(x, ps)
```

in `write_output_files` (`POST_SOLVE_*` / `PROCESS_ARCH_POST_SOLVE` at `f2dc9243`). Membership
comes from a committed artifact whose `nodes_sha256` is recomputed on load and whose
`i_figure_merit` and `icc` are checked against the run's own numerics; a listed node whose write
set intersects the predicate layer's read set is refused.

**The block schedule (VP4, tasks A24–A28).** `call_models` gains one branch:

```python
        if MDA_ENABLED:
            objf, conf = self._call_models_partitioned(xc, m)
```

(`MODULE_SOLVE_ENABLED` / `_call_models_by_module` at `f2dc9243`.) The branch iterates each DSM
block to its own fixed point on the **coupling state** — `max |Δy_i| / s_i < τ` over the block's
own write set, from the committed artifacts — and then evaluates the objective and constraints
once. `flat` is the same machinery on one block holding every in-loop node (decision D18's
predicate-matched control). The block sweep does not duplicate the sequence:

```python
    def _sweep_block(self, xc: np.ndarray, nodes: frozenset) -> None:
        self._active_nodes = nodes
        try:
            self._call_models_once(xc)
        finally:
            self._active_nodes = None
```

*Why:* a second copy of the model sequence — one measured, one not — is how a variant silently
stops computing what the baseline computes. The stopping rule is the coupling state and not
`objf`/`conf` because one module does not determine those quantities (decision D14(c)).

**The burn time held by a constant (task A34).** With `PROCESS_ARCH_BURN_TIME_OWNER=constant:…`
(`PROCESS_ARCH_PIN_BURN_TIME` at `f2dc9243`) the value is written into
`times.t_plant_pulse_burn` once, at `Caller` initialisation, refusing an input file that also
names iteration variable 178; a tripwire at the end of every sweep raises on any bit-level change.
*Why:* the evaluation phase runs the out-of-loop arrangement with no optimiser present, so
something else must own the variable, and a re-write each sweep would mask an unknown writer.

**Per-evaluation sweep histogram (issue I-17).** `call_models` was split into a wrapper and
`_call_models_inner` so that sweeps per evaluation can be binned on every exit path:

```python
        _sweeps_at_entry = DISPATCH_SWEEPS[0]
        try:
            return self._call_models_inner(xc, m)
        finally:
            _n = DISPATCH_SWEEPS[0] - _sweeps_at_entry
            _k = str(_n)
            SWEEPS_PER_EVAL_HIST[_k] = SWEEPS_PER_EVAL_HIST.get(_k, 0) + 1
```

(`_SWEEP_CALLS` at `f2dc9243`, renamed in §4.5.11.)

**Where the solve phase ends.** `write_output_files` freezes the node counter at its entry:

```python
    if NODE_CALLS_AT_OUTPUT[0] is None:
        NODE_CALLS_AT_OUTPUT[0] = NODE_CALLS[0]
```

*Why:* the output phase re-enters every model's `run()` from `output()` (trap T7) and is
identical work in every arm; pooling it into the cost would dilute the quantity compared.

**Driver, not model — for the whole file.** No expression any model evaluates is touched. The
file decides *when* and *how often* each node runs and *what test* the loop stops on. What would
have made any of this a model change: altering a model's `run()`, or the value any model writes
for a given input. The one place the loop's *result* can differ from upstream's — a different
stopping rule stops at a different point — is the independent variable of the experiment, and it
is behind a switch that is unset in the reference arms.

### 3.3 `process/core/solver/module_solve.py` — new file

**What.** The block schedule's settings, resolved at import: the shape of the loop (`MDA_MODE`),
the tolerance (`TAU`), the two committed artifacts (coupling state, write sets), the block order
and which blocks are iterated, the caps (detectors, not budgets — reaching one raises), the
loaders that rebuild the `YSpec` from the artifact and cross-check the two files' component
hashes, and the pass-trace diagnostic. It loads the coupling-state predicate by path (§5).

```python
MDA_MODE: str = os.environ.get("PROCESS_ARCH_MDA", "").strip() or "upstream"
...
ENABLED: bool = MDA_MODE != "upstream"
...
TAU: float = float(os.environ.get("PROCESS_ARCH_TAU", "1e-6"))
```

**Why.** The settings and the loaders were separated from the loop so that `caller.py` holds the
schedule and `module_solve.py` holds what the schedule is parameterised by; both artifacts are
required with no default, because a predicate silently taken from another configuration's scales
changes what "converged" means with no symptom.

**Driver, not model.** This file calls no model. It decides what "converged" means for the loop.

### 3.4 `process/core/solver/subsolve.py` — new file

**What.** The seam through which a model's own solve of one unknown can be routed to a different
owner (variant point VP5, task A4):

```python
def subsolve(residual, x0, args, *, site: str, direct):
    if site in SITES_OUT_OF_LOOP:
        return x0
    return direct(*args)
```

With the switch unset `SITES_OUT_OF_LOOP` is empty and every call goes straight to `direct`, the
model's original method with its original arguments.

**Why.** The burn time is the one cross-block feedback on pulsed configurations: `pulse` solves
for it in closed form and the physics block reads it. To cut that edge the burn time has to be
owned by something outside the loop — the optimiser (iteration variable 178 with constraint 93)
or a constant — and the model has to stop overwriting it. The seam is what makes that a
*driver* choice.

**Driver, not model.** The model's expression is not here; it stays in `pulse.py` (§3.9) and is
called unchanged on the default path. Had the residual or the root been rewritten here, that
would be a change to what the model computes.

### 3.5 `process/core/solver/constraints.py` — constraint 93

```python
+from process.models.pulse import burn_time_root
...
+@ConstraintManager.register_constraint(93, "sec", "=")
+def constraint_equation_93(constraint_registration, data):
+    ...
+    return eq(
+        data.times.t_plant_pulse_burn,
+        burn_time_root(
+            data.pf_coil.vs_cs_pf_total_burn,
+            data.physics.v_plasma_loop_burn,
+            data.times.t_plant_pulse_fusion_ramp,
+        ),
+        constraint_registration,
+    )
```

**Why.** When the optimiser owns the burn time, this equality is what determines it. Appended
from 93 upward (the fork's registry allocation), never fitted into a gap, so no existing input
file's `icc` is reinterpreted. Inert until an input file names `icc = 93`; none of the committed
ones does — the lifted input file, derived by a committed stage, does.

**Driver, not model.** The relation is the model's own, imported from `pulse.py`, not restated.

### 3.6 `process/core/solver/iteration_variables.py` — variable 178

```python
+    178: IterationVariable("t_plant_pulse_burn", "times", 1.0, 1.0e8),
```

**Why.** The optimiser's side of the same lift. Appended (`N_ITERATION_VARIABLES_MAX` is
`max(keys)`, so every array sized by it grows in step); inert until an input file names
`ixc = 178`.

### 3.7 `process/data_structure/numerics.py` — the constraint label (decision D14(a))

```python
+            "Burn time consistency            ",
```

appended to `lablcc`, with two docstring lines. **Why.** A constraint registered without its label
is a silent reporting gap. This file is outside the driver's default-permitted surface; the user
approved the extension as unavoidable for any constraint append (D14(a)).

### 3.8 `process/core/solver/evaluators.py` and `solver_handler.py` — probe hooks

`evaluators.py` gains three phase stamps (`fn`, `grad`, `grad_reconcile`) so the census can say
which solver phase each `call_models` belongs to; `solver_handler.py` gains three
`record_retry` calls, one before each rung of the optimiser's retry ladder:

```python
+                if _idf_probe.ENABLED:
+                    _idf_probe.record_retry("epsfcn_x10", ifail)
```

Each is a guarded no-op with `PROCESS_IDF_PROBE` unset. The ladder itself is not touched.

### 3.9 `process/models/pulse.py` — the one model file (decision D14(b))

**What.** The burn-time expression was moved out of `Pulse.calculate_burn_time` into a
module-level function, and its residual form written beside it:

```python
+def burn_time_root(
+    vs_cs_pf_total_burn: float,
+    v_plasma_loop_burn: float,
+    t_plant_pulse_fusion_ramp: float,
+) -> float:
+    ...
+    return (
+        abs(vs_cs_pf_total_burn) / v_plasma_loop_burn
+    ) - t_plant_pulse_fusion_ramp
+
+
+def burn_time_residual(
+    t_plant_pulse_burn: float,
+    vs_cs_pf_total_burn: float,
+    v_plasma_loop_burn: float,
+    t_plant_pulse_fusion_ramp: float,
+) -> float:
+    ...
+    return t_plant_pulse_burn - burn_time_root(
+        vs_cs_pf_total_burn,
+        v_plasma_loop_burn,
+        t_plant_pulse_fusion_ramp,
+    )
```

and `Pulse.run`'s assignment became a call through the seam:

```python
-            self.data.times.t_plant_pulse_burn = self.calculate_burn_time(
-                vs_cs_pf_total_burn=self.data.pf_coil.vs_cs_pf_total_burn,
-                v_plasma_loop_burn=self.data.physics.v_plasma_loop_burn,
-                t_plant_pulse_fusion_ramp=self.data.times.t_plant_pulse_fusion_ramp,
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

while `calculate_burn_time` itself now returns `burn_time_root(...)` in place of the inline
expression and keeps its negative-burn-time diagnostic.

**Why.** Without a residual the constraint layer has nothing to evaluate, and without the seam the
model overwrites whatever the optimiser or the constant put in the data structure on the first
sweep. This is the structural edit D11 licenses: the expression is *moved, not changed*, so its
solution method becomes a driver choice.

**Why it is still not a model change, and what would have been one.** The arithmetic is
verbatim; `burn_time_residual(burn_time_root(*inputs), *inputs) == 0` identically, and on the
default path `subsolve` calls `calculate_burn_time` with exactly the arguments the straight-line
assignment used and assigns exactly what it assigned. Changing the expression, its inputs, or the
diagnostic's threshold would have been a model change. This is the one file under `models/`
that G0′ expects to differ from `c0ae5b28`, and it expects it to differ in exactly this way: its
post-edit sha256 is pinned, so a further edit fails the gate too.

---

## 4. The copy's own edits (`f2dc9243` → copy), file by file

Each subsection is one entry of `copy_gates.PERMITTED_EDIT_FILES`, in the order recorded there.
Snippets are from `git diff f2dc9243:process/<path> -- PROCESS/process/<path>`.

### 4.1 `process/core/solver/__init__.py` — 2 recorded edits

At `f2dc9243` this file is one line, `"""Module containing solver routines"""` — the same as at
`c0ae5b28`. The copy adds 111 lines below it.

#### 4.1.1 `ArchitectureRefusal` — new definition

**What.** A typed exception for every refusal the driver makes about *how the models are
arranged*.

```python
+class ArchitectureRefusal(RuntimeError):
+    """The driver declining an architecture setting rather than failing at one.
+    ...
```

**Why.** The harness has to file a refused run (a guard working) in a different row of its
failure taxonomy from a crashed run (something broken). Before this class it matched fragments of
the message text, which a reworded message would defeat (task A56 (driver-renames), added at task
A50's merge). `harness/core/failure.py` catches it by type, with the text match kept as fallback.

**Driver, not model.** No model raises it and no solve that merely failed to converge does;
those stay `RuntimeError`/`ModuleSolveFailure`. It is placed in the package `__init__` because
every switched file in the package already imports through it.

#### 4.1.2 `RETIRED_SWITCHES` / `assert_no_retired_switches` — new definition

**What.** The eleven names the rename retired, each mapped to what replaced it, checked at the
import of the package:

```python
+RETIRED_SWITCHES: dict[str, str] = {
+    "PROCESS_ARCH_MODULE_SOLVE": (
+        "PROCESS_ARCH_MDA=flat|partitioned (unset for upstream's own loop)"
+    ),
+    "PROCESS_ARCH_OUTER": (
+        "nothing: the partitioned schedule runs exactly once, ..."
+    ),
+    ...
+    "PROCESS_ARCH_WRITESET": "PROCESS_ARCH_WRITE_SETS",
+}
+
+def assert_no_retired_switches(environ=None) -> None:
+    ...
+    raise ArchitectureRefusal(
+        "the environment sets architecture switch name(s) this driver has "
+        "retired:\n" ...
+
+assert_no_retired_switches()
```

**Why.** Before the rename an unrecognised `PROCESS_ARCH_*` name was ignored, so a script still
setting an old name would run a *different* arrangement under the right name with no error
anywhere (task A56 (driver-renames); harness plan DR1's "a retired name must raise"). The
harness's self-check compares this list with its own registry rather than assuming they agree.

**Driver, not model.** Eleven dictionary lookups at import; nothing allocated when none is set.

### 4.2 `process/core/solver/module_solve.py` — 8 recorded edits

The file does not exist at `c0ae5b28` (§3.3); the diff here is against `f2dc9243`.

#### 4.2.1 `YSTATE_MODULE_PATH` — path constant

*Recorded edit kind: path constant. Made by task A46 (process-copy).*

```python
 YSTATE_MODULE_PATH = (
-    Path(__file__).resolve().parents[3]
-    / "arch_surgery"
-    / "fixedpoint"
+    Path(__file__).resolve().parents[4]
+    / "harness"
+    / "child"
     / "ystate.py"
 )
```

**Why.** The coupling-state predicate is loaded by path (§5). The copy sits one directory deeper
than the root tree and must reach the V4 harness's own module, not V3's research tree (decision
D20: V4 runs its own copy and owes V3 no compatibility). The `/ "child"` segment is task A66
(ystate-into-child), carried by A73 under D27 on 2026-09-14: the module moved into `harness/child/`
with the rest of the set a measurement subprocess imports, and the literal, this row of
`PERMITTED_EDIT_FILES` and `PROVENANCE.json` changed in one commit.

**Driver, not model.** A path; which file defines "converged" for the loop.

#### 4.2.2 The coupling-state artifact's name — comment

*Recorded edit kind: comment. Made by task A48 (harness-data).*

The module docstring named the artifact by its path in the repository's shared data directory;
it now names the file the copy reads
(`harness/data/coupling_state_<configuration>.json`, `write_sets_<configuration>.json`), and the
constant's comment says the target is committed and where its provenance is recorded
(`harness/data/PROVENANCE.json`). Prose only.

#### 4.2.3 `PROCESS_ARCH_MDA` — switch rename

*Recorded edit kind: switch rename. Made by task A56 (driver-renames), DR1.*

```python
-_ARMS = ("off", "per_module", "flat_state")
-
-MODULE_SOLVE_NAME: str = (
-    os.environ.get("PROCESS_ARCH_MODULE_SOLVE", "").strip() or "off"
-)
+MDA_MODES = ("upstream", "flat", "partitioned")
+
+MDA_MODE: str = os.environ.get("PROCESS_ARCH_MDA", "").strip() or "upstream"
...
-ENABLED: bool = MODULE_SOLVE_NAME != "off"
+ENABLED: bool = MDA_MODE != "upstream"
...
-FLAT_STATE: bool = MODULE_SOLVE_NAME == "flat_state"
+FLAT: bool = MDA_MODE == "flat"
```

**Why.** The switch takes the plan's name and values (§3.2 of the experiment plan; harness plan
§11.2). The schedule, the predicate and the artifact loading are unchanged: `ENABLED` and `FLAT`
have the same truth table under the new spelling.

#### 4.2.4 `PROCESS_ARCH_OUTER` — switch retired

*Recorded edit kind: switch retired. Made by task A56 (driver-renames), DR1.*

Removed: the `_OUTER_MODES` table, `OUTER_MODE`, `TRUST_OUTER`, `OUTER_CAP`, and the two refusals
that guarded `trust` against `off` and against `flat_state`:

```python
-_OUTER_MODES = ("verify", "trust")
-
-OUTER_MODE: str = os.environ.get("PROCESS_ARCH_OUTER", "").strip() or "verify"
...
-TRUST_OUTER: bool = OUTER_MODE == "trust"
...
 INNER_CAP = 20
-OUTER_CAP = 20
```

**Why.** `partitioned` now *means* one pass over the block schedule. The earlier revision
offered a repeated schedule with a joint test over the whole coupling state; task A43
(st-trust-gap) measured that test triggering a further pass **zero times in 91 888
evaluations**, the user removed the arm that used it (decision D22) and the switch went with it.
What the verification pass bought is measured instead by the harness's uncharged exit audit.

**Driver, not model.** How many times a loop over models runs. Gate GR (reproduction) is what
proves every arm this experiment runs already took the single-pass path.

#### 4.2.5 `PROCESS_ARCH_INNER_TAU` — switch retired

*Recorded edit kind: switch retired. Made by task A56 (driver-renames), decision D23.*

```python
-INNER_TAU: float = float(
-    os.environ.get("PROCESS_ARCH_INNER_TAU", "").strip() or TAU
-)
-
-if FLAT_STATE and os.environ.get("PROCESS_ARCH_INNER_TAU", "").strip():
-    raise RuntimeError(
```

**Why.** One tolerance for every converger, in every arm and both phases (D23). A second one
existed because arms used to be compared at matched *settings*; they are compared at matched
*achieved* accuracy, recorded per run by the exit audit, so there is nothing for it to do. The
three reads of `INNER_TAU` in `caller.py` became reads of `TAU`.

#### 4.2.6 `PROCESS_ARCH_COUPLING_STATE` / `PROCESS_ARCH_WRITE_SETS` — switch rename

*Recorded edit kind: switch rename. Made by task A56 (driver-renames).*

```python
-YSTATE_PATH: str | None = os.environ.get("PROCESS_ARCH_YSTATE") or None
-WRITESET_PATH: str | None = os.environ.get("PROCESS_ARCH_WRITESET") or None
+COUPLING_STATE_PATH: str | None = (
+    os.environ.get("PROCESS_ARCH_COUPLING_STATE") or None
+)
+WRITE_SETS_PATH: str | None = os.environ.get("PROCESS_ARCH_WRITE_SETS") or None
```

**Why.** The two committed artifacts a block loop reads take names that say what they are for.
The files, their validation (`components_sha256` rebuilt on load) and their cross-check are
unchanged.

#### 4.2.7 `ArchitectureRefusal` — typed refusal

*Recorded edit kind: typed refusal. Made by task A56 (driver-renames).*

Every refusal of an architecture setting in this file — an unrecognised `MDA` value, a missing
artifact path, a pass trace with no loop to trace, a coupling-state module not at its path, an
artifact that does not rebuild or is from another generation — raises the typed class:

```python
-    raise RuntimeError(
+    raise ArchitectureRefusal(
```

(and `from process.core.solver import ArchitectureRefusal` at the top). Motivation in §4.1.1.

#### 4.2.8 `PROCESS_ARCH_PREDICATE` — switch added

*Recorded edit kind: switch added. Made by task A59 (driver-predicate-mode), DR5.*

**What.** Which denominator the coupling-state test scales a step by becomes a driver choice.

```python
+PREDICATE_MODES = ("frozen", "mixed")
+
+PREDICATE_MODE: str = (
+    os.environ.get("PROCESS_ARCH_PREDICATE", "").strip() or "frozen"
+)
+
+if PREDICATE_MODE not in PREDICATE_MODES:
+    raise ArchitectureRefusal(
```

The literal list is checked against the module that implements the rulers the first time that
module is loaded:

```python
+    rulers = getattr(mod, "RULERS", None)
+    if rulers is None or tuple(rulers) != tuple(PREDICATE_MODES):
+        raise ArchitectureRefusal(
```

and the mode is stamped into the loaded spec's provenance beside the tolerance:

```python
         "tau": TAU,
+        "predicate_mode": PREDICATE_MODE,
     }
```

**Why.** `frozen` — `max|Δy_i| / s_i` with `s_i` a scale measured once — is every earlier
revision's ruler and the default. Issue I-12 showed it ~10¹⁸ times tighter than intended on
`costs.coe` at a divergent design point. `mixed` — `max|Δy_i| / max(|y_i|, s_i)` — is the
conventional scaled step with the measured scale kept as a floor; wherever `|y_i| ≤ s_i` it is
bit-identical, and it is never tighter. The experiment plan §3.6 pre-declares a trial of the two;
this is the trial's driver side. The tolerance and the ruler together are what "converged"
means, so a record naming one without the other would name half its stopping rule.

**Driver, not model.** The test itself is not reimplemented here; it lives in the harness's
coupling-state module (§5), and this file only passes the name through. Unset is `frozen`,
upstream of this change line for line. Gate G8 (12/12 pairs bit-identical with an independent
detector of the decisive pass) proved the identity.

### 4.3 `process/core/solver/subsolve.py` — 1 recorded edit

The file does not exist at `c0ae5b28` (§3.4).

#### 4.3.1 `PROCESS_ARCH_BURN_TIME_OWNER` — switch rename

*Recorded edit kind: switch rename. Made by task A56 (driver-renames), DR1.*

**What.** Two switches — `PROCESS_ARCH_LIFT=<site list>` (take the burn time out of the model)
and `PROCESS_ARCH_PIN_BURN_TIME=<float>` (a constant holds it) — folded into one whose value says
who owns it:

```python
-_raw = os.environ.get("PROCESS_ARCH_LIFT", "").strip()
+OWNERS: tuple[str, ...] = ("loop", "optimiser", "constant")
+
+_CONSTANT_PREFIX = "constant:"
+
+_raw = os.environ.get("PROCESS_ARCH_BURN_TIME_OWNER", "").strip()
+
+def _parse_owner(raw: str) -> tuple[str, float | None]:
+    if not raw or raw == "loop":
+        return "loop", None
+    if raw == "optimiser":
+        return "optimiser", None
+    if raw.startswith(_CONSTANT_PREFIX):
+        ...
+            return "constant", float.fromhex(literal)
...
+BURN_TIME_OWNER, BURN_TIME_CONSTANT = _parse_owner(_raw)
+SITES_OUT_OF_LOOP: frozenset[str] = (
+    frozenset({SITE_BURN_TIME}) if BURN_TIME_OWNER != "loop" else frozenset()
+)
```

The seam's test and return are the same:

```python
-    if LIFT_ENABLED and site in LIFTED_SITES:
+    if site in SITES_OUT_OF_LOOP:
         return x0
```

Gone with the fold: the refusal of a pin without a lift —

```python
-if PIN_ENABLED and not is_lifted(SITE_BURN_TIME):
-    raise RuntimeError(
```

— because "a constant owns it, but the model still solves for it" can no longer be written down.
The tripwire (`assert_burn_time_constant`, was `assert_burn_time_pinned`) is unchanged in what it
checks and deliberately stays a plain `RuntimeError`: it is a finding about a writer, not a
refused setting. The constant is accepted as a C99 hex float only, so a measured value survives
the round trip exactly.

**Why.** The two non-default answers are one mechanism seen twice, and as two switches they could
disagree. One switch, three values, and the inconsistent pair has no spelling.

**Driver, not model.** The value returned on each path is what it was; `pulse.py` is not touched.

### 4.4 `process/core/solver/constraints.py` — 1 recorded edit

Relative to `c0ae5b28` this file also carries constraint 93 (§3.5, inherited).

#### 4.4.1 Constraint 93's docstring — comment

*Recorded edit kind: comment. Made by task A56 (driver-renames).*

```python
-    the answer into the data structure; with the site lifted
-    (`PROCESS_ARCH_LIFT=burn_time`) the burn time is instead iteration variable
+    the answer into the data structure; with the optimiser owning the burn time
+    (`PROCESS_ARCH_BURN_TIME_OWNER=optimiser`) it is instead iteration variable
```

The docstring named a retired switch; it names the one that replaced it. Nothing the constraint
computes changes.

### 4.5 `process/core/caller.py` — 13 recorded edits

Relative to `c0ae5b28` this file also carries everything in §3.2 (inherited).

#### 4.5.1 `NODE_WRITESET_PATH` — path constant

*Recorded edit kind: path constant. Made by task A46 (process-copy).*

```python
 NODE_WRITESET_PATH = (
-    Path(__file__).resolve().parents[2]
-    / "arch_surgery"
-    / "docs"
+    Path(__file__).resolve().parents[3]
+    / "harness"
     / "data"
     / "node_writesets.json"
 )
```

**Why.** The committed per-node write sets are read by path; the copy reads the harness's own
copy (D20). Read only when a deferral is on, never live from a generated artifact (trap T9).

#### 4.5.2 `NODE_MAP_PATH` — path constant

*Recorded edit kind: path constant. Made by task A46 (process-copy).*

```python
 NODE_MAP_PATH = (
-    Path(__file__).resolve().parents[2]
-    / "arch_surgery"
-    / "docs"
+    Path(__file__).resolve().parents[3]
+    / "harness"
     / "data"
     / "dsm_node_map.json"
 )
```

Same reason; the committed DSM node map, read when a deferral or a block schedule is on.

#### 4.5.3 `_defer_per_run_nodes`, step (4) — existence check

*Recorded edit kind: existence check. Made by task A48 (harness-data).*

```python
     scenario = record.get("scenario")
+    if not NODE_WRITESET_PATH.exists():
+        raise ArchitectureRefusal(
+            f"PROCESS_ARCH_DEFER_PER_RUN needs the committed per-node write "
+            f"sets at {NODE_WRITESET_PATH}, which is not present.  Its "
+            f"origin is recorded in harness/data/PROVENANCE.json."
+        )
     per_scenario = json.loads(NODE_WRITESET_PATH.read_text())["per_scenario"]
```

**Why.** The per-call deferral path checked the file was there and refused by name; the per-run
path did not, and raised a bare `FileNotFoundError` from inside `json.loads`. The copy-gate's
`edit-behaviour` gate exercises this in three arms: the copy with the artifact absent must raise
`ArchitectureRefusal` naming the provenance file, the source commit must raise
`FileNotFoundError` (so the edit is a change, not a restatement), and the copy with the artifact
present must not refuse (so the check is a guard on absence and not a new refusal on the path
every run takes).

**Driver, not model.** No behaviour change on any path where the file exists.

#### 4.5.4 The artifacts' origin — comment

*Recorded edit kind: comment. Made by task A48 (harness-data).*

The per-call refusal named a generator script in the research tree as the way to obtain the
write sets; a comment named the per-run artifact by its old path. Both name the committed copy in
`harness/data/` and its provenance file:

```python
-            f"Generate with arch_surgery/fixedpoint/gen_node_writesets.py."
+            f"It is a committed file of this experiment, copied into "
+            f"harness/data/ and recorded in harness/data/PROVENANCE.json."
```

#### 4.5.5 Every architecture switch this file reads — switch rename

*Recorded edit kind: switch rename. Made by task A56 (driver-renames), DR1.*

The four switches resolved here take their intended names, and so do the module-level readbacks
the harness reads them through:

```python
-SEQUENCE_NAME: str = os.environ.get("PROCESS_ARCH_SEQUENCE", "").strip() or "upstream"
+ARRANGEMENT_NODE_NAME: str = (
+    os.environ.get("PROCESS_ARCH_ARRANGEMENT_NODE", "").strip() or "upstream"
+)
...
-PRIME_NAME: str = os.environ.get("PROCESS_ARCH_PRIME", "").strip() or "off"
+ARRANGEMENT_METHOD_NAME: str = (
+    os.environ.get("PROCESS_ARCH_ARRANGEMENT_METHOD", "").strip() or "off"
+)
...
-HOIST_NAME: str = os.environ.get("PROCESS_ARCH_HOIST", "").strip() or "off"
+DEFER_PER_CALL_NAME: str = (
+    os.environ.get("PROCESS_ARCH_DEFER_PER_CALL", "").strip() or "off"
+)
...
-POST_SOLVE_PATH: str | None = os.environ.get("PROCESS_ARCH_POST_SOLVE") or None
+DEFER_PER_RUN_PATH: str | None = (
+    os.environ.get("PROCESS_ARCH_DEFER_PER_RUN") or None
+)
```

with the derived names following (`PRIME_CALLS` → `ARRANGEMENT_METHOD_CALLS`, `HOIST_NODES` →
`DEFER_PER_CALL_NODES`, `POST_SOLVE_TOTALS` → `DEFER_PER_RUN_TOTALS`, `MODULE_SOLVE_TOTALS` →
`MDA_TOTALS`, the methods `_resolve_hoist_tails` / `_run_hoisted_tail` / `_apply_burn_time_pin`
→ `_resolve_defer_per_call_tails` / `_run_deferred_tail` / `_apply_burn_time_constant`, and the
record keys `hoisted_tail` → `deferred_tail`, `single_block_outer_test_skipped` →
`single_block_covers_loop`). Every branch, table and derivation is unchanged. The mechanisms'
own words — *prime*, *hoist* — survive in the comments, because they name what the code does
rather than what an arm is called.

#### 4.5.6 The repeated schedule — removal

*Recorded edit kind: removal. Made by task A56 (driver-renames), DR1.*

**What.** In `_call_models_partitioned` the loop over schedule passes, the joint residual
evaluation that decided whether to repeat it, its trace hook and the pass-cap refusal are gone:

```python
-        y_outer_prev = read(bound)
...
-        converged = False
-        outer = 0
-        for outer in range(1, module_solve.OUTER_CAP + 1):
-            for label, nodes, iterate in schedule:
+        schedule_passes = 1
+        for label, nodes, iterate in schedule:
...
-            if single_block:
-                converged = True
-                break
-            if module_solve.TRUST_OUTER:
-                converged = True
-                break
-            y = read(bound)
-            res = spec.residual(y_outer_prev, y)
...
-        if not converged:
-            ...
-            raise module_solve.ModuleSolveFailure(
-                f"the outer loop over modules did not converge in "
```

and the block loop stops on `tau` where it stopped on `inner_tau`. The record key
`outer_passes` keeps its name (it is the reproduction reference's key) and is `1` in every arm;
`inner_tau` and `outer_residual_trace` leave the record.

**Why.** §4.2.4: the schedule runs once, and that is a decision (D22, D23) rather than an
omission. `_single_block_covers_loop` is kept as a *recorded* property of the schedule that was
actually built, no longer a guard that skips anything.

**Driver, not model.** Gate GR — the reproduction of the previous revision's twenty runs after
the rename — is what proved every arm this experiment runs already took the single-pass path.

#### 4.5.7 `ArchitectureRefusal` — typed refusal

*Recorded edit kind: typed refusal. Made by task A56 (driver-renames).*

Every refusal of an architecture setting in this file raises the typed class (§4.1.1); the
import is

```python
-from process.core.solver import constraints
+from process.core.solver import ArchitectureRefusal, constraints
```

Upstream's own ten-pass raise in `_call_models_inner` — `"After 10 model evaluations …"` — is
left a `RuntimeError`: it is a finding about the shipped code, not a refused setting.

#### 4.5.8 `PROCESS_ARCH_OUTPUT_LOOP` — switch added

*Recorded edit kind: switch added. Made by task A57 (driver-output-path), DR2.*

**What.** The output path becomes a driver choice.

```python
+_OUTPUT_LOOPS: dict[str, bool] = {"upstream": True, "none": False}
+
+OUTPUT_LOOP_NAME: str = (
+    os.environ.get("PROCESS_ARCH_OUTPUT_LOOP", "").strip() or "upstream"
+)
...
+OUTPUT_LOOP_UPSTREAM: bool = _OUTPUT_LOOPS[OUTPUT_LOOP_NAME]
+OUTPUT_LOOP_SWEEPS: list[int] = [0]
+OUTPUT_PATH_ENTRIES: list[int] = [0]
```

In `call_models_and_write_output`, before upstream's `try`:

```python
+        if not OUTPUT_LOOP_UPSTREAM:
+            _take_exit_snapshot(self.models, self.data, "before_finalise")
+            finalise(self.models, self.data, ifail)
+            return
+
         try:  # noqa: PLW0717
...
                 OutputFileManager.open_idempotence_files(self.data.globals.output_prefix)
+                OUTPUT_LOOP_SWEEPS[0] += 1
                 self._call_models_once(xc)
```

and `OUTPUT_PATH_ENTRIES[0] += 1` at the entry to `write_output_files`.

**Why.** Upstream writes its output files through a *second* flat idempotence loop: evaluate the
whole model set, write an MFILE to scratch, repeat up to ten times until two files agree float by
float at `rtol = 1e-6`, then write the real ones. That loop belongs to the incumbent's stopping
rule, not to the models: an arm whose solve has converged the coupling state to τ has nothing
left for it to find, and re-solving the state before writing means the files do not hold the
numbers the optimiser accepted. `none` calls `finalise` once on the accepted state. The two
counters make the second loop's cost a measured column (13/14 reference optimisations settle it
at 2 sweeps; `0` under `none` is a count, not a claim). Arms `B1` and `B2` set `none` (plan §3.3);
`BR` and `B0` keep the loop.

**Driver, not model.** Unset, the path is upstream's line for line. The models run in the loop
are the same models; what changes is whether they are run again after acceptance. Gate G9
proved the accepted state bit-identical at the entry to `write_output_files` across the two
settings (0/3 825 components).

#### 4.5.9 `EXIT_SNAPSHOT_HOOK` / `EXIT_SNAPSHOTS` — instrument hook

*Recorded edit kind: instrument hook. Made by task A57 (driver-output-path).*

**What.** A callable slot the measurement subprocess installs, called at two named positions:

```python
+EXIT_SNAPSHOT_POSITIONS: tuple[str, ...] = (
+    "entry_to_write_output_files",
+    "before_finalise",
+)
+EXIT_SNAPSHOT_HOOK: list = [None]
+EXIT_SNAPSHOTS: dict = {}
+EXIT_SNAPSHOT_ERRORS: dict = {}
+
+def _take_exit_snapshot(models, data, where: str) -> None:
+    hook = EXIT_SNAPSHOT_HOOK[0]
+    if hook is None or where in EXIT_SNAPSHOTS or where in EXIT_SNAPSHOT_ERRORS:
+        return
+    try:
+        EXIT_SNAPSHOTS[where] = hook(models, data, where)
+    except Exception as exc:  # noqa: BLE001 - recorded, never raised
+        EXIT_SNAPSHOT_ERRORS[where] = f"{type(exc).__name__}: {exc}"
```

with `_take_exit_snapshot(models, data, "entry_to_write_output_files")` at the entry to
`write_output_files` and `"before_finalise"` immediately before each of the three `finalise`
calls.

**Why.** The experiment audits each arm's achieved accuracy by one further full sweep past
termination, and the plan declares the position: the entry to `write_output_files`, before the
per-run deferred nodes and before any output-time sweep. The audit's sweep mutates the state it
measures, so it cannot run *there* without handing the output path an audited state; the state is
snapshotted there and the residual computed after the run from the restored snapshot (later
extended by decision D25 to the whole data structure, harness-side). The driver holds the
position; the shape of a snapshot is the harness's.

**Driver, not model.** Nothing here reads an environment variable or calls a model. With the hook
uninstalled — every run of PROCESS that is not being measured — the mechanism is two `is None`
tests per run. A hook that raises is recorded, never allowed to change the run's outcome.

#### 4.5.10 Predicate counters — counters

*Recorded edit kind: counters. Made by task A58 (driver-predicate-counters), DR4.*

**What.** Seven module-level integer counters and the increments that feed them:

```python
+PREDICATE_EVALUATIONS: list[int] = [0]
+COMPONENTS_COMPARED: list[int] = [0]
+PREDICATE_EVALUATIONS_BY_BLOCK: dict[str, int] = {}
+COMPONENTS_COMPARED_BY_BLOCK: dict[str, int] = {}
+BLOCK_VISITS: dict[str, int] = {}
+EMPTY_BLOCK_VISITS: dict[str, int] = {}
+EMPTY_BLOCK_SWEEPS: dict[str, int] = {}
+UPSTREAM_PREDICATE_EVALUATIONS: list[int] = [0]
+UPSTREAM_COMPONENTS_COMPARED: list[int] = [0]
```

In the block loop, beside each residual evaluation:

```python
+            width = len(subset) if subset is not None else len(spec.keys)
...
+                PREDICATE_EVALUATIONS[0] += 1
+                COMPONENTS_COMPARED[0] += width
```

and per block visit, `close_visit` records a visit as empty when `NODE_CALLS` did not move
across it, keeping the sweeps it spent separately. In upstream's own loop:

```python
-            if self.check_agreement(objf_prev, objf) and self.check_agreement(
-                conf_prev, conf
-            ):
+            _objf_agrees = self.check_agreement(objf_prev, objf)
+            UPSTREAM_PREDICATE_EVALUATIONS[0] += 1
+            UPSTREAM_COMPONENTS_COMPARED[0] += 1 + (len(conf) if _objf_agrees else 0)
+            if _objf_agrees and self.check_agreement(conf_prev, conf):
```

**Why.** The partitioned arm runs far more sweeps than the flat one while executing far fewer
model nodes, and V3 found it no faster in wall clock — which can only be if a sweep costs
something not proportional to its nodes. The convergence test is the suspect: a flat loop
compares 827–846 components per sweep, a block loop only its block's write set. No conclusion may
rest on a timing (I-10), so the question is asked in counts (experiment plan §3.5 check 5). Two
predicates are counted separately because an arm stops on exactly one of them, and upstream's
pair short-circuits, so the width recorded is the width *compared*. The empty-visit counters are
issue I-20(a) in live form: on `st_regression` the `PULSE` block is visited after its only member
left the loop; the user ruled (decision D21) it is counted and disclaimed, not repaired. Measured
by these counters: 570 empty sweeps at seed 0, 10.84 % of the run's block sweeps.

**Driver, not model.** Plain integer increments. `check_agreement` is a pure comparison, so
evaluating the objective half into a name and then using it is the same evaluation in the same
order. No float is touched and no branch a result depends on changes; gate **G1** is what proves
it (0/2 341 values, 0/51 319 output lines differing with every switch unset). The output-time
loop's own `check_agreement` calls are counted by neither predicate.

#### 4.5.11 `DISPATCH_SWEEPS` — rename

*Recorded edit kind: rename. Made by task A58 (driver-predicate-counters).*

```python
-_SWEEP_CALLS: list[int] = [0]
+DISPATCH_SWEEPS: list[int] = [0]
...
-        _SWEEP_CALLS[0] += 1
+        DISPATCH_SWEEPS[0] += 1
```

**Why.** The per-run count of sweeps of the dispatch body was private and existed only to be
differenced for the per-evaluation histogram (§3.2). The per-sweep-overhead question needs the
run total, and it cannot be asked of a counter a harness has to reach into a module's private
names to read. Same cell, same increment, same value.

#### 4.5.12 `PROCESS_ARCH_PREDICATE` at the predicate's call site — switch added

*Recorded edit kind: switch added. Made by task A59 (driver-predicate-mode), DR5.*

```python
-                    res = spec.residual(y_prev, y, subset=subset)
+                res = spec.residual(
+                    y_prev, y, subset=subset,
+                    ruler=module_solve.PREDICATE_MODE,
+                )
```

**Why.** The one place this file evaluates the coupling-state test passes the ruler the run asked
for (§4.2.8). The call site serves both arrangements — the flat one's single block and each block
loop of the partitioned one — so there is exactly one place the choice is made and no path where
a loop can stop on a ruler the record does not name.

**Driver, not model.** The ruler picks a denominator; it does not change which components are
compared, which is why `COMPONENTS_COMPARED` is the free consistency check between the two modes.

#### 4.5.13 `ATTEMPT_LADDERS` / `ATTEMPT_STAMPS` / `open_ladder` / `attempt` — counters

*Recorded edit kind: counters. Made by task A60 (driver-attempts), DR7.*

**What.** A context manager that reads the cost counters at the entry to and the exit from every
attempt of the optimiser's retry ladder:

```python
+ATTEMPT_LADDERS: list[int] = [0]
+ATTEMPT_STAMPS: list[dict] = []
+
+def open_ladder() -> int:
+    ATTEMPT_LADDERS[0] += 1
+    return ATTEMPT_LADDERS[0]
+
+def _stamp_attempt(boundary: str, ladder: int, index: int, stage: str) -> None:
+    ATTEMPT_STAMPS.append({
+        "boundary": boundary,
+        ...
+        "node_calls": NODE_CALLS[0],
+        "dispatch_sweeps": DISPATCH_SWEEPS[0],
+        "sweeps_per_eval_hist": dict(SWEEPS_PER_EVAL_HIST),
+        "sweeps_by_block": dict(MDA_TOTALS["inner_sweeps_by_block"]),
+    })
+
+@contextmanager
+def attempt(stage: str):
+    ...
+    _stamp_attempt("entry", ladder, index, stage)
+    try:
+        yield
+    finally:
+        _stamp_attempt("exit", ladder, index, stage)
```

and the sweep counter frozen where the node counter already was:

```python
     if NODE_CALLS_AT_OUTPUT[0] is None:
         NODE_CALLS_AT_OUTPUT[0] = NODE_CALLS[0]
+        DISPATCH_SWEEPS_AT_OUTPUT[0] = DISPATCH_SWEEPS[0]
```

**Why.** The optimiser is not tried once (§4.6.1). Until this change the record said how many
attempts there were and each one's exit code and iterations, but the *cost* was a single run
total, so a run that failed its first attempt and converged on the retry charged both attempts'
evaluations to one number. That is most of one configuration's published cost ratio in the
previous revision (0.450 with the one retried seed in it, 0.659 over the retry-free seeds), and
the experiment plan §3.5 now requires the ratio with and without retried seeds, which a run total
cannot give. The harness differences consecutive stamps and **refuses** a record whose parts do
not sum to `node_calls_solve_phase` / `dispatch_sweeps_solve_phase` (14/14 reference records:
residual 0). The exit stamp is taken in a `finally`, so an attempt that raises is still bounded.

**Driver, not model.** Four integer reads and two dict copies per boundary, at most eight
boundaries in a run; no float touched, no branch a result depends on. G1 (0/2 326 values).

### 4.6 `process/core/solver/solver_handler.py` — 1 recorded edit

Relative to `c0ae5b28` this file also carries the three probe `record_retry` hooks (§3.8).

#### 4.6.1 `LADDER_STAGES`, and the four attempts bracketed — counters

*Recorded edit kind: counters. Made by task A60 (driver-attempts), DR7.*

```python
-from process.core import _idf_probe, constants, process_output
+from process.core import _idf_probe, caller, constants, process_output
...
+LADDER_STAGES: tuple[str, ...] = (
+    "initial",
+    "epsfcn_x10",
+    "epsfcn_x0.1",
+    "hessian_reset_b2",
+)
...
-        ifail = self.solver.solve()
+        caller.open_ladder()
+        with caller.attempt(LADDER_STAGES[0]):
+            ifail = self.solver.solve()
...
                 with epsfcn_context(self.data.numerics, 10):
-                    ifail = self.solver.solve()
+                    with caller.attempt(LADDER_STAGES[1]):
+                        ifail = self.solver.solve()
```

(and likewise for `LADDER_STAGES[2]` under `epsfcn_context(..., 0.1)` and `LADDER_STAGES[3]`
after `self.solver.set_b(2.0)`).

**Why.** The ladder — the optimiser once; on any exit but "converged" again with the
finite-difference step ×10, then ×0.1; on exit code 5 with fewer than two iterations once more
from a reset second-derivative matrix — is upstream's, and every attempt evaluates the model set.
The rung names live here, beside the branches that implement them, so a ladder that gains a rung
cannot keep the old vocabulary silently; the harness compares the driver's own rung name with its
positional guess.

**Driver, not model.** Which attempts run, in which order, under which settings, is exactly what
it was; the only new statements are the stamps.

### 4.7 `process/core/_idf_probe_modules.py` — 1 recorded edit

The file does not exist at `c0ae5b28` (§3.1).

#### 4.7.1 `reads_by_node` — instrument report

*Recorded edit kind: instrument report. Made by task A58 (driver-predicate-counters); task A51 (harness-artifacts)'s handover.*

```python
         "writes_by_node": {n: sorted(f"{a}.{b}" for a, b in v) for n, v in _writes_all.items()},
+        "reads_by_node": {n: sorted(f"{a}.{b}" for a, b in v) for n, v in _reads_all.items()},
     }
```

(with a nine-line comment above it). **Why.** The census summary reported the *count* of a
node's reads and not the names, so the harness had to reach into the instrument's module-level
state from inside the same process; now it reads the report. One line, the same expression the
writes half uses, in a module that is not even imported with `PROCESS_IDF_PROBE` unset.

---

## 5. `ystate.py` — the coupling-state module, reached by path

`module_solve.py` loads the predicate that decides "converged" from a literal path (§4.2.1):

```python
YSTATE_MODULE_PATH = (
    Path(__file__).resolve().parents[4]
    / "harness"
    / "child"
    / "ystate.py"
)
```

via `importlib` in `_ystate_module()`, once, on the non-upstream path only; with `PROCESS_ARCH_MDA`
unset the module is never loaded.

**Why by path, and why the harness's module.** The harness is not an installed package, and
vendoring a second copy of the predicate into `process/` would create exactly the drift decision
D14(c) exists to prevent: there is one implementation of the predicate per revision of the
experiment, and the driver and the harness's exit audit must use the same one. `harness/child/ystate.py`
is byte-identical to its source in the research tree bar a provenance paragraph in its docstring
(`harness/data/PROVENANCE.json` records that and checks it), and it implements both rulers of
§4.2.8; the driver checks the module's `RULERS` against its own literal the first time it loads
the module.

**The file moved.** Task A66 (ystate-into-child), carried by A73 (run-path-edits-and-the-press)
under D27 on 2026-09-14, moved `harness/ystate.py` into `harness/child/` — a pure `git mv`, the
module's bytes unchanged (`harness/data/PROVENANCE.json` still records the same hunks and digest
under the new name). Because the driver reaches it by a literal, the move was a driver-copy edit:
the literal above and the `YSTATE_MODULE_PATH` row of `PERMITTED_EDIT_FILES` changed in one commit,
`PROVENANCE.json` was regenerated (`copy_gates.py provenance --force`), `copy_gates.py all` passed,
and G1 was run as a straddle across the change in A73's press. The harness README's layer 3 now
lists the file inside `child/`.

---

## 6. Verifying this document

Two commands, run from this directory with the experiment's interpreter
(`/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python`):

```
python copy_gates.py all
```

runs `copy-identity` (every file under `process/` is `f2dc9243`'s bar the seven permitted-edit
files, whose post-edit sha256 and whose exact zero-context hunks must match `PROVENANCE.json`;
the file *set* is compared too), `frozen-physics` — gate **G0′** (every file under
`process/models/` is `c0ae5b28`'s bar `pulse.py`, whose expected content is pinned), the
`smoke-import` (with `PYTHONPATH` set to this directory, `process.__file__` resolves under the
copy; without it, elsewhere) and `edit-behaviour` (§4.5.3), each with its teeth. It proves the
copy carries exactly the edits §4 documents and nothing else: an edit this document does not
describe would be an unexplained difference and the gate would fail. It does **not** prove §3 —
that layer is the root tree's history, `git log c0ae5b28..f2dc9243 -- process/`.

```
python ../experiment_runner.py --gate switch_neutrality
```

runs gate **G1** (registry name `switch_neutrality`): with every switch unset, one optimisation and one
evaluation per configuration, compared value by value and output line by line against the
capture taken before the last driver change. It proves the claim every "driver, not model"
paragraph above makes about the default path — that unset, the copy does what it did before — on
the whole record rather than on a curated list of fields, with each exclusion named and counted.

**Where this file lives.** At the copy's root, beside `copy_gates.py` and `PROVENANCE.json`,
*outside* `process/`. Both copy gates walk `process/` and nothing above it, so this document is
invisible to them: adding it changes no gate's file set, and it can be edited without regenerating
provenance. That is also why it can go stale without a gate noticing — hence the header.
