# A61 (insstrain-diagnosis) — why one component sits above the tolerance at the accepted point, and what it is actually measuring

> **Document status** — **OPEN**. Task **A61 (insstrain-diagnosis)**, branch `A61-insstrain-diagnosis`,
> off `architecture_surgery` at `0a023d63`. Every number below was produced by running
> `arch_surgery/MDA_partitioning_experiment_v4/harness/exit_audit_diagnosis.py` at commit
> `2ae57064`; the eleven PROCESS runs it made are stamped with that commit, a clean tree and the
> experiment's own copy of PROCESS, each asserted inside the run. The
> physics is unchanged: nothing under `PROCESS/process/models/` was edited, read-only throughout
> (D5). Numbers from the superseded study at `710a75c9` are not cited (D4).

---

## 0. The words, spelled out once

*Caption: one row per term this report uses in a particular way. "Means" is the definition in
force here; where the project's own vocabulary already fixes a word, this is that definition and
not a new one.*

| term | means |
|---|---|
| **coupling state**, `y` | the measured set of state fields the in-loop models write and read from each other — 840 components on `large_tokamak_nof`, 846 on `low_aspect_ratio_DEMO`, 827 on `st_regression`. It is what the fixed-point loop converges |
| **predicate** | the test that ends a loop. Here: `max_i |Δy_i| / s_i < τ` over the continuous components, exact equality over the discrete ones, with `s_i` a scale measured once and frozen in the committed per-configuration artifact (the **frozen ruler**), τ = 1e-6 |
| **exit audit** | **one further full sweep of the whole model set**, taken outside the arm and charged to no arm, from the state the solve handed over. Its residual is read as *how far from converged the accepted point still was* |
| **the audit's declared position** | the entry to `write_output_files`, before the per-run deferred nodes and before any output-time sweep — the state the solve handed over (experiment plan §3.3) |
| **snapshot** | one exact serialisation of a state: floats as hexadecimal literals, so a state written out and read back is the identical state to the bit. The driver takes one at the declared position; the audit is taken afterwards from the restored snapshot, because the audit's own sweep would otherwise hand the output path a state the optimiser never accepted |
| **restricted statistic** | the exit-audit maximum over the components that are **not** written by the nodes deferred to once per run. Membership is derived from the committed per-run deferral artifact and the committed run-time write census, never listed by hand |
| **whole-state statistic** | the same maximum over every tested component. On an arm that defers nodes to once per run it necessarily reports those nodes' own outputs as movement, because the snapshot is from before they ran |
| **the map** | the function one sweep of the model set computes, `y ↦ F(y)`. The loop iterates `F` to a fixed point; the audit is supposed to evaluate the same `F` once more |
| **dose response** | the same sweep repeated with one setting varied over a declared series of values, so that an attribution is a curve rather than an argument |
| **arm** | one column of the experiment's switch matrix. `BR` is PROCESS as shipped; `B0` is the flat fixed-point control; `B1` adds the burn-time lift and the one-call output path; `B3` is the partitioned intervention |

---

## 1. Verdict

**The classification is (d), in its "output-mode branch" form — and it is an artefact of the exit
audit, not of the models' convergence.** More precisely, and this is the sentence the rest of the
report defends:

> The audit's sweep is **not the loop's map**. Between the snapshot the audit is taken from and
> the sweep the audit takes, PROCESS's output path permanently changes a model setting that is
> **not** part of the coupling state — `tfcoil.n_rad_per_layer`, the radial discretisation of the
> TF-coil stress calculation, from its default **100** to its maximum **500** — and the snapshot
> neither captures nor restores it. `tfcoil.insstrain` is a value sampled on that grid, so it
> moves. Nothing about the fixed point moved.

The four alternatives the task named are answered as follows, each against a measurement.

*Caption: one row per candidate explanation, with the measurement that settles it and the section
that carries it. Population: nine optimisation runs — `BR`/`B0`/`B1`/`B3` on `large_tokamak_nof`
(plus `B0` at seed 1), `BR`/`B0`/`B3` on `low_aspect_ratio_DEMO`, `B0` on `st_regression` — all at
seed 0 unless stated, all `ifail = 1`.*

| candidate | verdict | the measurement |
|---|---|---|
| **(a)** the audited state is not the loop's exit state | **refuted** | 0 of 840 / 846 / 827 coupling-state components differ, bit for bit, between the loop's own last sweep, the exit of the last evaluation, and the entry to `write_output_files` — on **9 of 9** runs. The last evaluation was made at the same design vector the audit injects, bit for bit, on 9 of 9 (§4) |
| **(b)** the component is not iterated, or not compared by the loop | **refuted on the pulsed configurations; confirmed on `st_regression`** | On both pulsed configurations it is a **continuous** coupling-state component, written in the loop by node `cicc_sctfcoil`, and in block `M2`'s write set, so the flat loop compares it on every sweep. On `st_regression` it is `None` from the first sweep onward, classified **discrete**, and tested by exact equality — which is the whole reason that configuration shows nothing (§3) |
| **(c)** genuine non-convergence of the fixed-point map — a cycle or a drift | **refuted** | A second sweep from the state the first sweep produced gives residual **`0x0.0p+0`** — bit-identical — on 9 of 9 runs. A one-off recomputation, not a cycle. And under the loop's own map the *first* sweep already gives ≤ `0x1.b49f565f80d44p-37` (1.24e-11) with **0** components above τ (§5, §6) |
| **(d)** a discontinuity or output-mode branch in the TF-coil insulation-strain model at the accepted point | **confirmed as an output-mode branch; refuted as a discontinuity** | The branch is `if output: self.data.tfcoil.n_rad_per_layer = 500`, in each TF-coil node's own `run`, plus an unconditional assignment in `run_and_output_stress`, which `output()` calls. Putting that one field back collapses the component's own scaled residual from ~7e-3 to **exactly `0x0.0p+0`** in every arm; putting back the other 85 changed fields and not that one leaves it **unchanged**. The value is not discontinuous: over a dose series of five discretisations it obeys `v(n) = v_∞ + C/n` with the four estimates of `C` agreeing to **0.12–0.14 %** (§6, §7) |

**Two consequences follow, and one of them is about PROCESS rather than about this experiment.**

1. **For the experiment.** The restricted exit-audit statistic at the plan's declared position is,
   on both pulsed configurations and in every arm, **a measurement of a discretisation change and
   not of convergence**. Published as it stands it would say "one component above τ at the accepted
   point" about an instrument. The fix is harness-side and small (§9).
2. **For PROCESS.** The value of `tfcoil.insstrain` that a run writes into its output file is
   **not** the value its solve converged, in every arm including the reference arm, by 0.70–0.72 %
   — `-5.8703422201e-03` converged against `-5.9126108020e-03` written, on `B0` / `large_tokamak_nof`
   / seed 0. Neither is the grid-converged value: extrapolation puts that at `-5.9231691831e-03`,
   **0.892 %** from the solved value and **0.178 %** from the written one (§7, §8).

`B0` and `B3` **did** converge to τ. The captions that say so are correct; what was wrong was
reading the audit residual as evidence against them.

---

## 2. How to re-run everything in this report

Every number comes from one committed entry point, in four stages, with no shell invocation in
between. From `arch_surgery/MDA_partitioning_experiment_v4`:

```bash
PY=/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python

# what the component is, who writes it, and what the code does with it
PYTHONPATH=PROCESS $PY -m harness.exit_audit_diagnosis census

# the nine runs, through harness/pool.py, every one --run-kind gate
HARNESS_WORKERS=3 PYTHONPATH=PROCESS $PY -m harness.exit_audit_diagnosis runs

# the same job with the trace and without it, compared leaf by leaf
HARNESS_WORKERS=1 PYTHONPATH=PROCESS $PY -m harness.exit_audit_diagnosis inertness

# the tables
PYTHONPATH=PROCESS $PY -m harness.exit_audit_diagnosis report

# all four, in order
HARNESS_WORKERS=3 PYTHONPATH=PROCESS $PY -m harness.exit_audit_diagnosis all
```

`--only <configuration>/<arm>/seedNNN` narrows the declared set for a smoke run; it never adds a
run, and the report stage applies the same filter and names what it is missing rather than
shrinking its own denominator. A missing observation is a **refusal** (exit code 1 with the runs
named), not a quietly shorter table.

The stage writes `census.json`, `manifest.json`, `inertness.json`, `summary.json` and
`summary.md`. **The tables in
this report are that `summary.md`**, quoted; nothing here was computed by hand.

**Where the artifacts are.** Live, in this worktree:
`arch_surgery/MDA_partitioning_experiment_v4/runs/gates/exit_audit_diagnosis/`. They are untracked
by design. `arch_surgery/bin/retire_task_worktree.sh A61-insstrain-diagnosis` relocates them; by
that script's own namespacing rule (`${BRANCH%%-*}_<entry>`) they will land at
`arch_surgery/idf_probe/runs/A61_gates/exit_audit_diagnosis/`. **The orchestrator should confirm
that path against what the script prints** — this project has written the wrong recorded path
twice (I-14, I-15, I-16).

### 2.1 The instrument is shown inert, not asserted to be

The trace only reads: it wraps three calls and each returns exactly what the unwrapped call
returns. That is a claim about code, and this project gates such claims. So the same job —
`B0` / `st_regression` / seed 0 — runs **twice at the same commit**, differing in one environment
variable, and every deterministic leaf of the two run records is compared without tolerance.

*Caption: the inertness check, from the `inertness` stage. "Compared" is the number of record
leaves actually compared; "excluded" names the eleven that cannot be equal between two runs in two
directories (paths, timings, the two wall-clock stamps) with a reason each. "Declared leaves" is a
list of thirteen the claim depends on — the objective and its hexadecimal form, the four cost
counters, the iteration count, the two predicate counters and the exit audit on both rulers — each
asserted to be present on both sides and not excluded, rather than assumed to be in the population.
The tooth adds one to a single leaf of a copy of the traced record and requires the comparison to
report it.*

| quantity | result |
|---|---|
| leaves compared | 672 |
| mismatches | **0** |
| leaves excluded, each with a reason | 11 |
| declared leaves confirmed in the compared population | **13 of 13** |
| tooth (`node_calls_total` + 1 on a copy) | **bit** |
| observation file written with the trace / absent without it | yes / yes |

The check **fails** on any mismatch and names the leaves; nothing is retried and no exclusion was
added to make it pass.

---

## 3. Question 1 — what the component is, and what writes it

*Caption: one row per configuration, from `census` (stage 1). "Writer" is derived from the
committed run-time write census `harness/data/node_writesets.json`, which closes the sweep at the
boundary of `_call_models_once` and therefore excludes `output()`-path traffic (traps T1/T7).
"Category" and "scale" come from the committed coupling-state artifact for that configuration.
Blocks are the committed per-block write sets; the flat arms have one block containing every
in-loop node, so a component in any block is compared on every sweep.*

| configuration | components | writer node (of *n* census nodes) | block | category | scale | measured over | magnitude range in the harvest |
|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 840 | `cicc_sctfcoil` (of 22) | `M2` | continuous | 6.046156594601506e-03 (`0x1.8c3dacd71e702p-8`) | 149 design points | 5.868846e-03 – 7.703100e-03 |
| `low_aspect_ratio_DEMO` | 846 | `cicc_sctfcoil` (of 23) | `M2` | continuous | 4.828962411843177e-03 (`0x1.3c788ba1ea310p-8`) | 297 design points | 4.817661e-03 – 5.208915e-03 |
| `st_regression` | 827 | `croco_sctfcoil` (of 21) | `M2` | **discrete**, value `null` | — | — | — |

**The scale is its own magnitude**, measured as the median `|y_i|` over the harvest's design
points restricted to the points where the component is non-zero. So a scaled residual of 7e-3 is a
0.7 % change in the value, not an artefact of a small denominator. **That rules out the "measured
scale too small" candidate on its face**, and it is why this report does not spend a section on it.

**What computes it, with line numbers.** The census locates every line of the copy's model code
that mentions the component or the discretisation setting, with the innermost `if` it sits under,
taken from the file at the commit the stage ran at:

| file | line | in | statement | guard |
|---|---|---|---|---|
| `process/models/tfcoil/base.py` | 2521 | `TFCoil.stresscl` | `insstrain = None` | — |
| `process/models/tfcoil/base.py` | 2994 | `TFCoil.stresscl` | `insstrain = ( sig_tf_r[n_radial_array - 1] * eyoung_wp_stiffest_leg / eyoung_wp_trans_eff / eyoung_ins )` | `if i_tf_stress_model == 1` |
| `process/models/tfcoil/superconducting.py` | 2524 | `CICCSuperconductingTFCoil.run` | `self.data.tfcoil.n_rad_per_layer = 500` | **`if output`** |
| `process/models/tfcoil/superconducting.py` | 2564 | `CICCSuperconductingTFCoil.run` | `n_radial_array=int(self.data.tfcoil.n_rad_per_layer)` | — |
| `process/models/tfcoil/superconducting.py` | 2651 | `CICCSuperconductingTFCoil.run` | `self.data.tfcoil.insstrain = ( self.data.tfcoil.insstrain if self.data.tfcoil.insstrain is None else insstrain )` | — |
| `process/models/tfcoil/superconducting.py` | 2100 | `SuperconductingTFCoil.run_and_output_stress` | `self.data.tfcoil.n_rad_per_layer = 500` | — (unconditional; `output()` calls this method) |
| `process/models/tfcoil/superconducting.py` | 4054 | `CROCOSuperconductingTFCoil.run` | `self.data.tfcoil.n_rad_per_layer = 500` | **`if output`** |
| `process/models/tfcoil/resistive.py` | 104 | `ResistiveTFCoil.run` | `self.data.tfcoil.n_rad_per_layer = 500` | **`if output`** |
| `process/data_structure/tfcoil_variables.py` | 208 | — | `insstrain: float = 0.0` | — (the default) |
| `process/data_structure/tfcoil_variables.py` | 303 | — | `n_rad_per_layer: int = 100` | — (the default) |

Four facts follow from that table alone, and each is checked by a measurement later.

* **The component is a grid sample.** `sig_tf_r[n_radial_array - 1]` is the **last radial point of
  the first layer**, and `plane_stress` lays those points out as
  `rad[ii] + ((rad[ii+1] - rad[ii]) / n) * (jj - n·ii)` — so the last point of a layer sits one
  step *short* of that layer's outer edge, at a radius that depends on `n`. Change `n` and the
  value changes.
* **`n_rad_per_layer` is a persistent field with a latching write.** Its default is 100. Three
  `run` methods raise it to 500 under `if output` — the cable-in-conduit, the cross-conductor and
  the resistive TF-coil models — and `run_and_output_stress`, which every superconducting TF
  `output()` calls, raises it **unconditionally**. The census finds four assignments of `500` in
  the whole tree and **no assignment anywhere that puts it back**.
* **It is not a coupling-state component.** It appears in none of the three committed artifacts, so
  the audit's snapshot does not capture it and the audit's restore does not restore it.
* **The `None` latch explains `st_regression`.** `insstrain` is computed only under
  `i_tf_stress_model == 1`; `st_regression.IN.DAT` sets `i_tf_stress_model = 0`, so the model
  returns `None`. The guard at line 2651 keeps the *stored* value if it is already `None` and
  otherwise assigns — and the stored default is `0.0`, not `None`, so the **first** call assigns
  `None` and every later call keeps it. The harvest therefore saw one distinct value (`null`) and
  classified the component **discrete**, tested by exact equality, which never moves.

The two pulsed input files name no `i_tf_stress_model`, so they take the data structure's default,
`1` — the plane-stress branch that computes it.

---

## 4. Question 2 — is the audited state the loop's exit state?

**Measured with a harness-side trace, not argued.** `harness/audit_map.py` installs three wraps,
each of which returns exactly what the unwrapped call returns:

* `Caller._call_models_once` — the coupling state after **every** sweep of the model set, kept only
  as the latest and frozen the moment the output path is entered. The coupling-state predicate is
  evaluated immediately after a sweep, so that latest one **is** the loop's own exit state;
* `Caller.call_models` — the same one step later, after the objective and constraint layer has run;
* the driver's own exit-snapshot hook, so that a **whole-data-structure** snapshot is taken beside
  the coupling-state snapshot the driver already takes there.

It is a gate instrument: installed by `HARNESS_AUDIT_MAP_TRACE`, **refused on a campaign run**, and
writing to its own file (`audit_map_observation.json`) so nothing it produces can reach a record a
gate compares value for value. The runs are started by `harness/pool.py` as `--run-kind gate`, with
the variable passed through `Job.override_env`.

*Caption: one row per run. Each cell is the number of coupling-state components that are **not
bit-identical** between the two positions, out of the configuration's whole component set (840 /
846 / 827).*

| run | last sweep → last evaluation | last evaluation → output entry | last sweep → output entry | output entry → before `finalise` |
|---|---|---|---|---|
| `large_tokamak_nof/B0/seed000` | 0 | 0 | **0** | 13 |
| `large_tokamak_nof/BR/seed000` | 0 | 0 | **0** | 13 |
| `large_tokamak_nof/B0/seed001` | 0 | 0 | **0** | 12 |
| `large_tokamak_nof/B1/seed000` | 0 | 0 | **0** | 0 |
| `large_tokamak_nof/B3/seed000` | 0 | 0 | **0** | 114 |
| `low_aspect_ratio_DEMO/B0/seed000` | 0 | 0 | **0** | 1 |
| `low_aspect_ratio_DEMO/BR/seed000` | 0 | 0 | **0** | 1 |
| `low_aspect_ratio_DEMO/B3/seed000` | 0 | 0 | **0** | 114 |
| `st_regression/B0/seed000` | 0 | 0 | **0** | 9 |

**Candidate (a) is refuted.** The state the audit is taken from is the state the loop's last sweep
left, bit for bit, on every run. And the audit injects the same design vector the last evaluation
used: `numerics.xcm` equals the last evaluation's `xc` element for element, 9 of 9 runs, over 14 to
21 iteration variables.

**What runs between the loop's exit and the audit's declared position, named with the census.**

* **The objective and constraint layer.** On the arms that stop on the coupling state (`B0`, `B1`,
  `B3`), `_call_models_partitioned` evaluates `objective_function` and
  `constraints.constraint_eqns` once **after** the predicate has broken the loop, before returning;
  on the reference arm `BR` those two *are* the predicate's inputs and are computed inside the
  loop, so nothing runs after it at all. Either way the write census carries that layer as its own
  node, `objective_constraints`: it writes **nothing** on `large_tokamak_nof` and on
  `st_regression`, and **one field** on `low_aspect_ratio_DEMO` — `cs_fatigue.n_cycle_min`, which
  is **not** in that configuration's coupling state. Consistent with the 0 measured above.
* **The optimiser's own return.** VMCON accepts and `SingleRun` calls `write_output_files` with
  `numerics.xcm`. On `B0` and `B1` that is all; neither arm sets the per-call or per-run deferral.
* **On `B1` there is nothing else either.** The matrix gives `B1` the flat solve, the burn-time
  lift and the one-call output path; it defers no node. The census's per-run node sets exist but no
  `B1` composition enables them.
* **Everything else happens *after* the snapshot, inside `write_output_files`**: the per-run
  deferred nodes (`vacuum`, `water_use`, `costs` on the pulsed configurations; plus `pulse` on
  `st_regression`) on the arms that defer, then the output path. That is why the last column above
  reads 114 on `B3` and 0 on `B1`, and it is the reason the **restricted** statistic exists.

The last column is itself a measurement worth keeping: **on `low_aspect_ratio_DEMO`, exactly one
coupling-state component differs between the state the solve handed over and the state PROCESS is
about to write out — `tfcoil.insstrain`.** On `large_tokamak_nof` thirteen do, twelve of them cost
fields moving below τ, and the thirteenth is again `tfcoil.insstrain`, holding the maximum at
6.990983645422282e-03.

---

## 5. Question 3 — one sweep, then another: cycle or one-off?

*Caption: one row per run; the cell is the component's **own** scaled residual on the frozen ruler
under that sweep, as a hexadecimal float, whatever its place in the ordering — so the partitioned
arm, whose whole-state maximum belongs to the per-run deferred nodes, is on the same ruler as every
other row. `—` is a configuration where the component is not a continuous coupling-state component
at all. τ = 1e-6.*

| run | as found | as found, 2nd sweep | solve-phase map | only `tfcoil.n_rad_per_layer` put back | every other field put back |
|---|---|---|---|---|---|
| `large_tokamak_nof/B0/seed000` | `0x1.ca293e1fbbd05p-8` | **`0x0.0p+0`** | `0x0.0p+0` | **`0x0.0p+0`** | `0x1.ca293e1fbbd05p-8` |
| `large_tokamak_nof/BR/seed000` | `0x1.ca292b56b673fp-8` | **`0x0.0p+0`** | `0x0.0p+0` | **`0x0.0p+0`** | `0x1.ca292b56b673fp-8` |
| `large_tokamak_nof/B0/seed001` | `0x1.c1c59d472b6dap-8` | **`0x0.0p+0`** | `0x0.0p+0` | **`0x0.0p+0`** | `0x1.c1c59d472b6dap-8` |
| `large_tokamak_nof/B1/seed000` | `0x1.d28bc4431f7fep-8` | **`0x0.0p+0`** | `0x0.0p+0` | **`0x0.0p+0`** | `0x1.d28bc4431f7fep-8` |
| `large_tokamak_nof/B3/seed000` | `0x1.d28bc4431f7fep-8` | **`0x0.0p+0`** | `0x0.0p+0` | **`0x0.0p+0`** | `0x1.d28bc4431f7fep-8` |
| `low_aspect_ratio_DEMO/B0/seed000` | `0x1.cc23ee7f374eap-8` | **`0x0.0p+0`** | `0x0.0p+0` | **`0x0.0p+0`** | `0x1.cc23ee7f374eap-8` |
| `low_aspect_ratio_DEMO/BR/seed000` | `0x1.cc23ee7f371aep-8` | **`0x0.0p+0`** | `0x0.0p+0` | **`0x0.0p+0`** | `0x1.cc23ee7f371aep-8` |
| `low_aspect_ratio_DEMO/B3/seed000` | `0x1.cc23d7ea8f685p-8` | **`0x0.0p+0`** | `0x0.0p+0` | **`0x0.0p+0`** | `0x1.cc23d7ea8f685p-8` |
| `st_regression/B0/seed000` | — | — | — | — | — |

The whole-state maxima behave the same way where the whole state is comparable. On
`large_tokamak_nof` / `B0` / seed 0 the first sweep gives `0x1.ca293e1fbbd05p-8`
(6.990983645422282e-03, 1 component above τ) and the second gives **`0x0.0p+0`** — every one of
the 840 components bit-identical to the state the first sweep produced.

**Candidate (c) is refuted.** A cycle would repeat; a drift would continue. This is a **one-off
recomputation**: the sweep recomputes the component once on a different grid and then the state is
a fixed point of that grid's map.

---

## 6. The attribution, as a leave-one-out pair

The trace compares the whole data structure — every field of every namespace — at the entry to the
output path against the moment the record's own exit audit is taken. The difference set is
**derived**, never listed.

*Caption: one row per run. Population: 2 288 fields over 36 namespaces. The count is those that
differ between the two moments, with the coupling-state components themselves excluded (they are
restored by the snapshot and cannot be the cause).*

| run | fields compared | differ, outside the coupling state | by namespace | `tfcoil.n_rad_per_layer` among them |
|---|---|---|---|---|
| `large_tokamak_nof/B0/seed000` | 2288 | 86 | build 3, impurity_radiation 2, numerics 1, pf_coil 1, physics 78, **tfcoil 1** | yes |
| `large_tokamak_nof/BR/seed000` | 2288 | 86 | build 3, impurity_radiation 2, numerics 1, pf_coil 1, physics 78, **tfcoil 1** | yes |
| `large_tokamak_nof/B0/seed001` | 2288 | 86 | build 3, impurity_radiation 2, numerics 1, pf_coil 1, physics 78, **tfcoil 1** | yes |
| `large_tokamak_nof/B1/seed000` | 2288 | 85 | build 3, impurity_radiation 2, pf_coil 1, physics 78, **tfcoil 1** | yes |
| `large_tokamak_nof/B3/seed000` | 2288 | 86 | build 3, impurity_radiation 2, numerics 1, pf_coil 1, physics 78, **tfcoil 1** | yes |
| `low_aspect_ratio_DEMO/B0/seed000` | 2288 | 86 | build 3, impurity_radiation 2, numerics 1, pf_coil 1, physics 78, **tfcoil 1** | yes |
| `low_aspect_ratio_DEMO/BR/seed000` | 2288 | 86 | build 3, impurity_radiation 2, numerics 1, pf_coil 1, physics 78, **tfcoil 1** | yes |
| `low_aspect_ratio_DEMO/B3/seed000` | 2288 | 86 | build 3, impurity_radiation 2, numerics 1, pf_coil 1, physics 78, **tfcoil 1** | yes |
| `st_regression/B0/seed000` | 2288 | 83 | build 1, impurity_radiation 2, numerics 1, physics 78, **tfcoil 1** | yes |

The 78 `physics` fields are the detailed-physics reporting model's own outputs, written only on the
output path; they are not read by any in-loop model. The one `tfcoil` field is
`tfcoil.n_rad_per_layer`, **100 at the entry, 500 at the audit, on 9 of 9 runs**.

**The attribution is a pair, not an argument** (§5's last two columns):

* put back **only** `tfcoil.n_rad_per_layer` → the component's own residual is **exactly
  `0x0.0p+0`** in every arm, and the whole-state maximum falls to `0x1.94d12c769164ep-37`
  (1.1505593553918033e-11) or to `0x0.0p+0`, with **0** components above τ out of 840 / 846;
* put back **every other changed field and not that one** (85 of 86) → the residual is
  **unchanged**, to the last bit, and one component is still above τ.

Since one field alone reproduces the whole effect and the other 85 together reproduce none of it,
the attribution is exact.

---

## 7. It is a grid sample, not a discontinuity

The dose series sweeps the same handed-over state five times with the discretisation set to 100,
200, 300, 400 and 500 and everything else as the run left it.

*Caption: `large_tokamak_nof` / `B0` / seed 0. `v(n)` is `tfcoil.insstrain` after one sweep at that
setting; `C` is `(v(a) − v(b)) / (1/a − 1/b)` for each consecutive pair. The solve ran at 100
throughout; the output path sets 500.*

| n | `v(n)` | scaled residual of that sweep | `C` from the pair ending here |
|---|---|---|---|
| 100 | -5.8703422201e-03 | `0x1.94d12c769164ep-37` (1.15e-11, 0 above τ) | — |
| 200 | -5.8967688503e-03 | `0x1.1e721a3db2d94p-8` (4.370815e-03) | 5.285326e-03 |
| 300 | -5.9055712324e-03 | `0x1.7ddb72d159f36p-8` (5.826679e-03) | 5.281429e-03 |
| 400 | -5.9099712067e-03 | `0x1.ad8cbeb645505p-8` (6.554410e-03) | 5.279969e-03 |
| 500 | -5.9126108020e-03 | `0x1.ca293e1fbbd05p-8` (6.990984e-03) | 5.279191e-03 |

*Caption: one row per run. The four estimates of `C` and how far apart they are; the extrapolated
limit is `v(500) − C/500` with `C` from the last pair.*

| run | relative spread of the four `C` | extrapolated limit `v_∞` | solved value (n = 100) from the limit | written value (n = 500) from the limit |
|---|---|---|---|---|
| `large_tokamak_nof/B0/seed000` | 0.116 % | -5.9231691831e-03 | 0.892 % | 0.178 % |
| `large_tokamak_nof/BR/seed000` | 0.116 % | -5.9231653757e-03 | 0.892 % | 0.178 % |
| `large_tokamak_nof/B0/seed001` | 0.116 % | -5.8149134544e-03 | 0.892 % | 0.178 % |
| `large_tokamak_nof/B1/seed000` | 0.119 % | -6.0512695129e-03 | 0.889 % | 0.178 % |
| `large_tokamak_nof/B3/seed000` | 0.119 % | -6.0512695129e-03 | 0.889 % | 0.178 % |
| `low_aspect_ratio_DEMO/B0/seed000` | 0.140 % | -4.8713295470e-03 | 0.870 % | 0.174 % |
| `low_aspect_ratio_DEMO/BR/seed000` | 0.140 % | -4.8713295470e-03 | 0.870 % | 0.174 % |
| `low_aspect_ratio_DEMO/B3/seed000` | 0.140 % | -4.8713247975e-03 | 0.870 % | 0.174 % |
| `st_regression/B0/seed000` | not measured — the component has no float value in that coupling state | — | — | — |

Four independent estimates of `C` agreeing to about a tenth of a percent is the signature of a
**first-order** error, `v(n) = v_∞ + C/n`, which is exactly what a sample taken one grid step short
of a layer boundary has. A discontinuity would not produce that; nor would a solver that had
stopped in the wrong place. **Candidate (d)'s "discontinuity" half is refuted; its "output-mode
branch" half is what is left.**

---

## 8. What PROCESS writes, against what it solved

*Caption: one row per run. `converged by the solve` is `tfcoil.insstrain` in the state at the
audit's declared position, read from that run's own snapshot; `written to the output file` is the
value the same run put in its MFILE, read from that file. Compared as hexadecimal floats.*

| run | converged by the solve | written to the output file | identical |
|---|---|---|---|
| `large_tokamak_nof/B0/seed000` | -5.8703422201e-03 | -5.9126108020e-03 | **no** |
| `large_tokamak_nof/BR/seed000` | -5.8703384458e-03 | -5.9126070012e-03 | **no** |
| `large_tokamak_nof/B0/seed001` | -5.7630537836e-03 | -5.8045484053e-03 | **no** |
| `large_tokamak_nof/B1/seed000` | -5.9974760007e-03 | -6.0405181447e-03 | **no** |
| `large_tokamak_nof/B3/seed000` | -5.9974760007e-03 | -6.0405181447e-03 | **no** |
| `low_aspect_ratio_DEMO/B0/seed000` | -4.8289567355e-03 | -4.8628617723e-03 | **no** |
| `low_aspect_ratio_DEMO/BR/seed000` | -4.8289567355e-03 | -4.8628617723e-03 | **no** |
| `low_aspect_ratio_DEMO/B3/seed000` | -4.8289520177e-03 | -4.8628570292e-03 | **no** |
| `st_regression/B0/seed000` | the component is `None`; the output file carries no `(insstrain)` line | — | — |

This is a property of **PROCESS as shipped** — the reference arm `BR` shows it with every
architecture switch unset — and it is the **same difference** the audit reports, expressed on a
different denominator: the audit divides by the component's frozen measured scale and gets
6.990984e-03 on `B0` / `large_tokamak_nof` / seed 0, while dividing by the value itself gives
0.720 %. The MFILE's `insstrain` is the 500-point value; the state the optimiser accepted
carries the 100-point value; nothing reconciles them, because the output path never re-enters the
MDA at the coarse grid and the coarse grid is never restored.

Under upstream's output-time loop (`BR`, `B0`) the *rest* of the state is re-swept twice at 500
before the files are written. Under the one-call output path (`B1`, `B3`) `finalise` is called once
and only the models that re-enter their own `run()` from `output()` (trap T7) recompute — among
them the TF-coil stress block, which is the one thing the discretisation reaches. **What else those
re-entries change in the written file was not measured here** and is named in §10 as a limit.

---

## 9. What it means for the experiment, and what to do

### 9.1 The restricted exit-audit statistic

At the plan's declared position, on both pulsed configurations, in **every** arm measured —
`BR`, `B0`, `B1`, `B3` — the restricted statistic is:

| | `large_tokamak_nof` | `low_aspect_ratio_DEMO` | `st_regression` |
|---|---|---|---|
| restricted maximum, seed 0 | 6.990984e-03 (`B0`), 6.990979e-03 (`BR`), 7.118926e-03 (`B1` and `B3`) | 7.021185e-03 (`B0`, `BR`), 7.021179e-03 (`B3`) | 4.930383e-14 |
| components above τ, of 696 / 701 / 682 kept | 1 | 1 | 0 |
| argmax | `tfcoil.insstrain` | `tfcoil.insstrain` | `physics.f_beta_alpha_beam_thermal` |

These reproduce A57 (driver-output-path) §10.3 and A52 (harness-gates) §6.4 exactly, which is the
cross-check that this task's instrument is measuring the same thing those tasks published.

**If nothing changes, the campaign will publish a restricted statistic that on 2 of 3
configurations is dominated, in every arm, by a quantity that measures the output path's
discretisation change.** It would not be wrong arithmetic; it would be the wrong reading — the
statistic exists to say "how converged was the handed-over state", and on those configurations it
would be saying "by how much does the output path's grid differ from the solve's".

**What it does *not* threaten.** The statistic is the same in every arm to within the arms' own
optima, so it cannot bias a comparison *between* arms; and it is the whole of the difference — with
the setting put back, 0 of 696 / 701 components are above τ and the maxima are ≤ 1.24e-11. Every
arm's handed-over state is converged to five orders below τ.

### 9.2 The captions

Every arm converged to τ on every evaluation it made.

*Caption: one row per run, from the run record. "Sweeps per evaluation" is the range of the
solve-phase histogram — what the loop needed to reach τ on its hardest and easiest evaluation;
every evaluation is inside it, none hit a cap. "Node calls" is the solve phase's, the cost unit.
The output-time loop's sweeps are counted separately and happen **after** the audit's declared
position.*

| run | `ifail` | optimiser iterations | evaluations | sweeps per evaluation | node calls, solve phase | output path | output-time sweeps |
|---|---|---|---|---|---|---|---|
| `large_tokamak_nof/B0/seed000` | 1 | 8 | 630 | 1–6 | 43 449 | `mda_output` | 2 |
| `large_tokamak_nof/BR/seed000` | 1 | 8 | 630 | 2–6 | 42 567 | `mda_output` | 2 |
| `large_tokamak_nof/B0/seed001` | 1 | 8 | 630 | 1–7 | 43 491 | `mda_output` | 2 |
| `large_tokamak_nof/B1/seed000` | 1 | 8 | 660 | 1–6 | 44 142 | `finalise_once` | 0 |
| `large_tokamak_nof/B3/seed000` | 1 | 8 | 660 | 4–14 | 28 055 | `finalise_once` | 0 |
| `low_aspect_ratio_DEMO/B0/seed000` | 1 | 16 | 1 240 | 1–5 | 86 877 | `mda_output` | 2 |
| `low_aspect_ratio_DEMO/BR/seed000` | 1 | 16 | 1 240 | 2–5 | 89 964 | `mda_output` | 2 |
| `low_aspect_ratio_DEMO/B3/seed000` | 1 | 13 | 1 050 | 4–13 | 45 496 | `finalise_once` | 0 |
| `st_regression/B0/seed000` | 1 | 10 | 570 | 1–12 | 42 756 | `mda_output` | 2 |

Those captions stand. What must **not** be written is "one component of the accepted state is still
above τ", because on the evidence above that sentence is about `n_rad_per_layer` and not about the
fixed point.

### 9.3 Recommendation, with what it costs

**Preferred — make the audit evaluate the loop's map.** Extend the exit-audit snapshot from the
coupling state to the whole data structure, and restore both before the audit sweep. The set of
fields restored is then **derived** (what differs between the two positions), not a list, so it
survives any future model that latches another output-mode setting.

* *Cost.* The snapshot hook gains one whole-structure snapshot per position — 2 288 fields over 36
  namespaces, at the two positions the driver offers — and `child.take_exit_audit` gains a
  restore. Both are harness-side; **no driver change and no model change.**
* *Consequence to plan for.* It changes `exit_audit.*` on **every** record, so gate **G1** must be
  re-run at that commit with one more named exclusion, and any reference value that quotes an exit
  audit — gate GR's 270 compared values include one — has to be re-taken or excluded explicitly.
  That is the same shape of consequence A57 §13 flagged for `exit_audit.restricted`, and it is
  about one task's work.
* *Two fields cannot be put back and both are named*: `globals.fileprefix` (serialised as a bare
  `repr`, not rebuildable) and `numerics.name_xc` (does not read back equal). Neither is read by a
  model. The **coupling-state** restore — the one the residual is measured against — was bit-exact
  on 11 of 11 sweeps that take one, on 9 of 9 runs.

**Minimal — restore `tfcoil.n_rad_per_layer` alone.** Measured to be sufficient today: it collapses
the component's residual to exactly `0x0.0p+0` in every arm. But it is a hand-written list of one,
which is the construction this project has been bitten by before; the derived version costs little
more.

**Do nothing.** Defensible only if the campaign's captions carry this diagnosis, name the component
and say what it measures. The statistic is then still comparable between arms — but a reader has to
be told, every time, that the one component above τ is an instrument artefact.

**Not recommended: exclude the component.** It would hide a real finding (§8) behind a restriction
that the restricted statistic's own derivation rule does not license.

### 9.4 Owed to the sibling study, if the user wants it sent

Three demonstrated defects in PROCESS as shipped, each with a measurement rather than a reading:

1. **`n_rad_per_layer` is a latching output-mode setting.** Three `run(output=True)` paths and one
   `output()` path raise it from 100 to 500; nothing restores it. Any code that evaluates the model
   set after an output call is silently on a different grid.
2. **The output file's `insstrain` is not the value the run solved**, by 0.70–0.72 % on both pulsed
   configurations, in PROCESS as shipped (§8), and neither value is the grid-converged one (§7).
3. **The `insstrain` guard latches `None` for the life of a run.** `self.data.tfcoil.insstrain =
   self.data.tfcoil.insstrain if self.data.tfcoil.insstrain is None else insstrain` keeps the
   stored value when it is already `None`; since the default is `0.0`, the first call under a
   stress model that does not compute it stores `None` and every later call preserves it. Measured
   consequence: on `st_regression` the component is a constant `null` across a 144-point harvest.

Per the standing rule on cross-study handoffs, each of these is stated as "the code does X,
measurement shows Y", and none is sent without the user's word.

---

## 10. Limits

* **Nine diagnosis runs, not a distribution** (plus the two the inertness check makes). One seed
  on eight of the nine (seed 0), with `B0` on `large_tokamak_nof` also at seed 1. Every count and
  every hexadecimal float reproduced exactly across each repeated full run of the chain made during
  this task, so the quantities are deterministic; they are not a sample of anything.
* **`B3` was measured on the two pulsed configurations only**, and `B1` on `large_tokamak_nof`
  only. `B1` is inactive on `st_regression` by that configuration's own recorded reason.
* **The dose response varies one setting over five values.** It is not a grid-convergence study of
  the TF-coil stress model, and the extrapolated `v_∞` is a two-point Richardson estimate from the
  last pair, not a fit. It is used only to separate "grid sample" from "discontinuity", which it
  does at a spread of 0.116–0.140 % across four estimates.
* **What else the one-call output path leaves inconsistent in the written file was not measured.**
  §8 shows the difference for this one component. The general question — what the models that
  re-enter their own `run()` from `output()` (trap T7) recompute on the finer grid while the rest
  of the state stays on the coarse one — is open, and is a question for whoever owns gate G9. This
  report measured only that the two positions the driver snapshots differ in 0 components on `B1`
  and 114 on `B3`, and that the written `insstrain` differs from the handed-over one in every arm.
* **The residual is reported on the frozen ruler.** The observation carries the mixed ruler beside
  it on every sweep; the two are not published in one column here because this report's question is
  not about rulers. Wherever `|y| ≤ s` the two are bit-identical, which is the case for this
  component (its magnitude is its scale).
* **Two data-structure fields cannot be restored exactly** (§9.3). Neither is read by a model, but
  a whole-structure restore is therefore *not* provably total, and the report says so rather than
  claiming 2 288 of 2 288.
* **The instrument is refused on campaign runs and was never run as one.** All eleven runs are
  `--run-kind gate`. Its per-sweep cost — one further read of the coupling state — would otherwise
  contaminate a per-sweep cost measurement.
* **No conclusion here rests on a timing**, and none is quoted.

---

## 11. Change log

*Caption: append-only. One row per change to this document or to the code it reports on.*

| date | change |
|---|---|
| 2026-09-11 | Created. `harness/audit_map.py` (the trace and the sweep series), `harness/exit_audit_diagnosis.py` (the stage), three lines in `harness/optimise.py`. Nine diagnosis runs plus two inertness runs at `2ae57064`; classification (d), output-mode branch, attributed to `tfcoil.n_rad_per_layer` by a leave-one-out pair and a dose response. |
