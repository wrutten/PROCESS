# A89 (coupling-subset-trial) — stopping V4's loops on the DSM's coupling variables

> **Document status** — **CURRENT · TASK REPORT, OPEN.** Task A89 (coupling-subset-trial),
> 2026-09-29, on branch `A89-coupling-subset-trial`. The A89 label was taken by this session at
> the user's direct request; it has no queue row yet (provisional, protocol §8). Exploratory trial
> for the V5 improvement list. **Not** a V4 result: V4's campaign, harness and report are untouched,
> and nothing was written to the V4 folder. Scripts at `9d80c84b` (runs) and `80693be8` (table
> rendering); records at `arch_surgery/idf_probe/runs/coupling_subset_trial/` (untracked).

## 1. Question

The user, 2026-09-29: *"For each config, do one run using only the 'written by one model and read
by a different model (the data interfaces)' (ie. coupling vars), run once using 'of those, read by
a model that runs before the writer in the DSM's order (real feedback)' (feedback couplings), run
in both A0 and A2 arms. Compare the convergence properties of these cases. If you notice that
specific variables are missing, report about this. Build on the v4 machinery, but do not write any
files to the v4 folder."*

V4 stops every loop on the whole measured state `y`: every field an in-loop model writes (840 /
846 / 827 components). This trial stops the same loops on two DSM-derived subsets of `y` and asks
two things: does the loop stop sooner, and does it still stop at the same fixed point?

## 2. Method

**Test sets** (`arch_surgery/coupling_subset_trial/derive_test_sets.py` → `test_sets.json`). The
sibling's three per-configuration DSM exports were read once, read-only (trap T9). The sibling HEAD
(`05c0a4ba`), the pin (`PROCESS_at_36ac820e`) and each export's sha256 are recorded in the file.

- A "model" is a DSM supermodel that has a `supermodel_execution_order`. That includes the DSM's
  function-library supermodels, as the DSM draws them. The constraint blocks have no order; they
  are the optimiser's reads and are excluded.
- **interface**: a component of `y` written by one model and read by a different model.
- **feedback**: an interface component with at least one reader whose execution order is below its
  writer's.

| configuration | `y` | interface | feedback | self-read (DSM) | `y` not in DSM |
|---|---|---|---|---|---|
| large_tokamak_nof | 840 | 274 | 75 | 495 | 0 |
| low_aspect_ratio_DEMO | 846 | 273 | 73 | 501 | 0 |
| st_regression | 827 | 257 | 53 | 490 | 0 |

Every component of `y` is a DSM variable written by a DSM model, so the mapping needs no
translation. The sibling's own export annotates "the 75/55 MDA coupling variables"; this trial's
feedback count of 75 on the tokamak agrees.

**Narrowing** (`narrowed_evaluate.py`). The harness child `harness/child/evaluate.py` runs
unchanged, in-process, after one substitution from outside the V4 folder:
`module_solve.load_subsets` is wrapped.

- Each block's V4 write set is intersected with the test set.
- The flat block, which V4 tests on all of `y`, gets the test set.
- A per-pass log records, for every loop test, the narrowed residual that decided and the
  whole-`y` residual of the same two snapshots. It returns the driver's residual unchanged.
- The entry, the displacement and the **exit audit are not narrowed**. The audit sweeps once more
  over the whole of `y` from the committed coupling-state artifact.

**Jobs** (`run_trial.py`). V4's own `pool.environment_for`, `pool._command` and
`reproduction.entry_pin` compose the jobs; the campaign is `default_campaign()` with its run
directories moved out of the V4 folder. Bytecode writing is off and numba's cache is redirected.

- Per configuration: a reference, which is V4's entry-reference job (flat `A0`, full test, cold
  entry).
- Then `A0` and `A2` × {`full`, `interface`, `feedback`} × two entries:
  - **displaced**: seed 1, δ = 0.10 around the reference fixed point, as V4's campaign;
  - **cold**: the input file's own point.
- 39 runs in total, each in a fresh subprocess with its own directory. `git status --ignored` on
  the V4 folder was empty after the runs.

**Compared** (all counts or exact comparisons; no timing):

- node calls and sweeps per block of the one evaluation;
- the exit audit's **restricted** maximum, which excludes the once-per-run nodes' components.
  Those components are stale by design in `A2`, as in V4's own tables. Its whole-`y` maximum is in
  the records;
- the components above τ at exit, each marked by whether it was in the test set;
- the restricted distance between the narrowed run's exit state and the `full` run's exit state,
  same arm and entry (V4's frozen ruler, τ = 1e-6).

## 3. Result

Rendered by `run_trial.py --summarise` at `80693be8`:

| configuration | entry | arm | test set | components tested | node calls | sweeps per block | exit audit max (restricted) | above τ at exit | distance from `full` exit |
|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | displaced | A0 | full | 840 | 126 | FLAT 6 | 1.7e-09 | 0 | — |
| large_tokamak_nof | displaced | A0 | interface | 274 | 105 | FLAT 5 | 9.0e-08 | 0 | 9.0e-08 |
| large_tokamak_nof | displaced | A0 | feedback | 75 | 105 | FLAT 5 | 9.0e-08 | 0 | 9.0e-08 |
| large_tokamak_nof | displaced | A2 | full | 840 | 60 | M1 4, M2 5, M3 3 | 1.4e-08 | 0 | — |
| large_tokamak_nof | displaced | A2 | interface | 274 | 60 | M1 4, M2 5, M3 3 | 1.4e-08 | 0 | 0.0e+00 |
| large_tokamak_nof | displaced | A2 | feedback | 75 | 46 | M1 3, M2 5, M3 2 | 1.4e-08 | 0 | 0.0e+00 |
| large_tokamak_nof | cold | A0 | full | 840 | 126 | FLAT 6 | 8.1e-09 | 0 | — |
| large_tokamak_nof | cold | A0 | interface | 274 | 126 | FLAT 6 | 8.1e-09 | 0 | 0.0e+00 |
| large_tokamak_nof | cold | A0 | feedback | 75 | 105 | FLAT 5 | 4.2e-07 | 0 | 4.2e-07 |
| large_tokamak_nof | cold | A2 | full | 840 | 63 | M1 4, M2 6, M3 3 | 1.2e-09 | 0 | — |
| large_tokamak_nof | cold | A2 | interface | 274 | 63 | M1 4, M2 6, M3 3 | 1.2e-09 | 0 | 0.0e+00 |
| large_tokamak_nof | cold | A2 | feedback | 75 | 46 | M1 3, M2 5, M3 2 | 6.4e-08 | 0 | 6.4e-08 |
| low_aspect_ratio_DEMO | displaced | A0 | full | 846 | 105 | FLAT 5 | 0.0e+00 | 0 | — |
| low_aspect_ratio_DEMO | displaced | A0 | interface | 273 | 105 | FLAT 5 | 0.0e+00 | 0 | 0.0e+00 |
| low_aspect_ratio_DEMO | displaced | A0 | feedback | 73 | 84 | FLAT 4 | 1.6e-08 | 0 | 1.6e-08 |
| low_aspect_ratio_DEMO | displaced | A2 | full | 846 | 60 | M1 4, M2 5, M3 3 | 0.0e+00 | 0 | — |
| low_aspect_ratio_DEMO | displaced | A2 | interface | 273 | 57 | M1 4, M2 4, M3 3 | 0.0e+00 | 0 | 0.0e+00 |
| low_aspect_ratio_DEMO | displaced | A2 | feedback | 73 | 43 | M1 3, M2 4, M3 2 | 0.0e+00 | 0 | 0.0e+00 |
| low_aspect_ratio_DEMO | cold | A0 | full | 846 | 105 | FLAT 5 | 0.0e+00 | 0 | — |
| low_aspect_ratio_DEMO | cold | A0 | interface | 273 | 105 | FLAT 5 | 0.0e+00 | 0 | 0.0e+00 |
| low_aspect_ratio_DEMO | cold | A0 | feedback | 73 | 84 | FLAT 4 | 2.1e-07 | 0 | 2.1e-07 |
| low_aspect_ratio_DEMO | cold | A2 | full | 846 | 60 | M1 4, M2 5, M3 3 | 0.0e+00 | 0 | — |
| low_aspect_ratio_DEMO | cold | A2 | interface | 273 | 57 | M1 4, M2 4, M3 3 | 0.0e+00 | 0 | 0.0e+00 |
| low_aspect_ratio_DEMO | cold | A2 | feedback | 73 | 43 | M1 3, M2 4, M3 2 | 0.0e+00 | 0 | 0.0e+00 |
| st_regression | displaced | A0 | full | 827 | 126 | FLAT 6 | 3.0e-09 | 0 | — |
| st_regression | displaced | A0 | interface | 257 | 126 | FLAT 6 | 3.0e-09 | 0 | 0.0e+00 |
| st_regression | displaced | A0 | feedback | 53 | 105 | FLAT 5 | 8.8e-08 | 0 | 8.8e-08 |
| st_regression | displaced | A2 | full | 827 | 62 | M1 4, M2 6, PULSE 1, M3 3 | 3.0e-09 | 0 | — |
| st_regression | displaced | A2 | interface | 257 | 62 | M1 4, M2 6, PULSE 1, M3 3 | 3.0e-09 | 0 | 0.0e+00 |
| st_regression | displaced | A2 | feedback | 53 | 45 | M1 3, M2 5, PULSE 1, M3 2 | 8.8e-08 | 0 | 8.8e-08 |
| st_regression | cold | A0 | full | 827 | 147 | FLAT 7 | 3.3e-09 | 0 | — |
| st_regression | cold | A0 | interface | 257 | 147 | FLAT 7 | 3.3e-09 | 0 | 0.0e+00 |
| st_regression | cold | A0 | feedback | 53 | 126 | FLAT 6 | 9.6e-08 | 0 | 9.6e-08 |
| st_regression | cold | A2 | full | 827 | 77 | M1 4, M2 7, PULSE 1, M3 4 | 3.3e-09 | 0 | — |
| st_regression | cold | A2 | interface | 257 | 77 | M1 4, M2 7, PULSE 1, M3 4 | 3.3e-09 | 0 | 0.0e+00 |
| st_regression | cold | A2 | feedback | 53 | 60 | M1 3, M2 6, PULSE 1, M3 3 | 9.6e-08 | 0 | 9.6e-08 |

(`PULSE 1` on `st_regression` is the empty-block sweep of I-20a.)

**Reading.**

1. **Accuracy held in every narrowed run.**
   - The whole-`y` exit audit had 0 components above τ in all 24 narrowed runs, as in all 12
     `full` runs.
   - The largest restricted exit residual of a narrowed run is 4.2e-07 (`large_tokamak_nof`,
     cold, `A0`, feedback), where `full` reaches 8.1e-09. So the narrowed runs are less converged
     than `full` but still below τ.
   - The largest distance of a narrowed exit from the `full` exit is also 4.2e-07. No discrete
     component differs.
   - Where the narrowed test stopped at the same sweep as `full`, the exit state is bit-identical
     (distance 0).
2. **The interface set changes little.** Of 12 interface runs, the loop stopped earlier in 3:
   - `A0` displaced on `large_tokamak_nof`: 126 → 105 node calls;
   - `A2` on `low_aspect_ratio_DEMO`, both entries: M2 5 → 4 sweeps, 60 → 57 node calls.

   The other 9 are identical to `full`, bit for bit. The component that holds `full` open for its
   last sweep is usually an interface variable.
3. **The feedback set saves one sweep per loop.**

   | arm | configuration | node calls, `full` → feedback |
   |---|---|---|
   | `A0` | every configuration and entry | one flat sweep fewer: 126 → 105, 105 → 84, 147 → 126 (−14 % to −20 %) |
   | `A2` | `large_tokamak_nof` | 60 → 46, 63 → 46 |
   | `A2` | `low_aspect_ratio_DEMO` | 60 → 43 |
   | `A2` | `st_regression` | 62 → 45, 77 → 60 |

   In `A2`, M1 and M3 each lose one sweep, down to 3 and 2. **M2 stays at 4–6 sweeps** even
   tested on its 34 feedback components (14 on `st_regression`). M2's cost is its own internal
   feedback, not an over-wide test. That answers V5 item 2's question on this evidence: "its
   coupling is the loop's real work".
4. **What the narrowed test lets through at the stop is the one-time recomputation of downstream
   outputs.** At the pass where the narrowed test declared convergence, components outside it were
   still above τ in the whole-`y` residual of that pass. Examples:
   - `costs.coecap`, `power.qac` in flat `A0` on `large_tokamak_nof`;
   - `times.t_burn_0` and the pulse timings on `low_aspect_ratio_DEMO`, up to 5.3e-03;
   - first-wall and divertor outputs in M3, up to 2.6.

   The audit sweep after the stop moves every one of them by less than τ. So they were being
   recomputed from inputs that had already converged, not carried state that was still settling.
   Gauss–Seidel ordering predicts exactly this for variables downstream of the last feedback
   change. (In `A2`'s cold runs, the log's `inf` entries are components of blocks that had not yet
   run: an artefact of logging the whole of `y` at a block's test. They do not bear on the
   result.)

## 4. Missing variables

**No variable was shown to be missing.** An excluded variable that carries state across sweeps
would still be moving when the narrowed test stops, and would show above τ in the whole-`y` exit
audit. That did not happen in any of the 24 narrowed runs.

The components that set the narrowed runs' exit residual are named here, because they are where a
missing variable would show first:

- **`power.qac`** and **`costs.coecap` / `costs.coeoam`** (`large_tokamak_nof`). Each is written
  and read by one model only, so it is in neither set. `power.qac` is the argmax of the largest
  narrowed exit residual (4.2e-07). The DSM cannot say whether such a self read is a read of the
  previous sweep's value, which would be carried state and would need testing. This trial shows it
  stays below τ at these two entries; it does not show it is feed-forward.
- **`superconducting_tfcoil.a_tf_plasma_case`** (`st_regression`). Its argmax is 8.8e-08 / 9.6e-08
  in every feedback run. It is an interface variable only because the DSM splits
  `tfcoil.superconducting_functions` off as a separate model, so a self read by the TF coil model
  counts as an "interface". It is not a feedback variable.
- **`heat_transport.tlvpmw`** (`low_aspect_ratio_DEMO`, feedback `A0`), argmax 1.6e-08 / 2.1e-07.

**The burn time.** `times.t_plant_pulse_burn` is in both pulsed configurations' feedback sets
(reader `Physics` and `PlasmaInductance`, writer `Pulse`). On `st_regression` it is absent, which
is correct: that configuration is steady state.

**Coupling that `y` does not hold at all.** The DSM has 30 model-to-model `instance_state` edges
through attributes on model objects (e.g. `neprofile` / `teprofile`), not the data structure. `y`
does not contain them, so neither V4 nor this trial tests them. Narrowing does not change that.

## 5. Limits

- **One seed and one cold start per case, at δ = 0.10.** These loops converge in 4–7 sweeps. A
  carried variable outside the test set that happens to settle within those sweeps at these
  entries would pass unseen. The trial found no counter-example; it cannot certify the sets
  complete.
- **Phase A only.** Under VMCON (phase B), the loop runs at many design points and the optimiser
  reads the objective and constraints computed at the stop. The effect of a 0.4τ-level exit
  residual on the optimiser path was not measured.
- **The sets come from the sibling's current exports.** They are gitignored there and drifted once
  before (V17); digests are recorded. The order used is the DSM's upstream execution order, not
  each arm's arranged order. `A2` rearranges build after physics, so its true feedback set can
  differ.
- Run kind `smoke`. These records are outside every V4 tally and must never enter one.

## 6. Proposals for V5 (the user's to rule)

- **(a)** V5 item 6, "stop each loop on the DSM feedback set, audit on the whole of `y`", with this
  trial as its evidence: about −17 % node calls in `A0` and about −25 % in `A2` per evaluation,
  accuracy held below τ. It needs its own gate with teeth: remove a real feedback variable (e.g.
  the burn time) and the audit must fail.
- **(b)** Before (a), a runtime **read-before-write** measurement per node, to settle the
  self-read components that are in neither set (`power.qac`, `costs.coecap`). It would also derive
  each arm's feedback set from the order that arm actually runs.
- **(c)** The interface set is not worth a V5 item on this evidence: it matches `full` in 9 of 12
  runs.
