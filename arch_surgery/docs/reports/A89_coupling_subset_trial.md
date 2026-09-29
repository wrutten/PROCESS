# A89 (coupling-subset-trial) — stopping V4's loops on the DSM's coupling variables

> **Document status** — **CURRENT · TASK REPORT, OPEN.** Task A89 (coupling-subset-trial),
> 2026-09-29, two passes (§1–6 the first, §7 the second), on branch `A89-coupling-subset-trial`. The A89 label was taken by this session at
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

## 7. Second pass — read-before-write census, a measured tolerance, wall clock

The user, 2026-09-29: *"Rerun the scratch experiment you just did. With a few modifications: Build a
proof-of-principle for the read-before-write census to determine the feedback set to converge (ie.
implement the structural fix). Change the tolerance to a principled value. Measure beforehand what
that would be. Explain to me after. Compare wall clock time."* And: *"v5 improvement plan notes that
the feedforward/post-processing models should be run once in all A arms."*

Code: `arch_surgery/coupling_subset_trial/` — `rbw_census.py`, `narrowing.py`, `inproc_child.py`, and
`run_trial.py` (stages `--references --census --derive-rbw --noise --choose-tau --run --timing
--summarise`). Commits: `27dc1008` (code), `2b6aaca4` (`rbw_sets.json`), `33ca7b52` (`tolerance.json`); every
stage ran at `33ca7b52` or earlier, and `--choose-tau` re-run afterwards reproduces `tolerance.json` byte for byte. Records: `arch_surgery/idf_probe/runs/coupling_subset_trial/rerun/`
(untracked). The V4 folder is untouched: `git status --ignored` on it is empty after every stage.

### 7.1 Arms

| arm | what | V4 relation |
|---|---|---|
| `A0v4` | flat, every node in every sweep, whole-`y` test | V4's `A0` unchanged |
| `A0` | flat; feed-forward nodes once per call after convergence, per-run nodes once after convergence | V4's `A0` + `PROCESS_ARCH_DEFER_PER_CALL=feedforward` + the committed per-run artifact + one execution of that set |
| `A2` | partitioned | V4's `A2` + one execution of the per-run set |

The once-per-run execution is the output path's own mechanism (a fresh Caller's `_sweep_block`
over the per-run set) and is counted in node calls.

### 7.2 The read-before-write census (the structural fix)

**Rule.** Within one Gauss–Seidel sweep, a read sees either a value written earlier in the same
sweep, or the previous sweep's value. A loop must test exactly the components read **before their
first write in a sweep** and written later in it. This covers feedback edges and self-carried
state alike, in the order the arm actually runs, block by block.

**Instrument** (`rbw_census.py`):
- `__getattribute__` / `__setattr__` hooks on the data-structure namespace classes, restricted to
  `y`;
- a value diff of every array-valued `y` field across each node, since in-place mutation never
  reaches `__setattr__`, and the fetch that precedes it counts as a read, so it is included
  conservatively;
- one window per `Caller._sweep_block`, one node per `Caller._node`.

**Census.** `A0` and `A2`, whole-`y` test at τ = 1e-6, displaced seeds 2–5. These are disjoint
from the trial's entries (seed 1, and cold), so the trial is out-of-sample for the census. Union
per configuration, arm and block → `rbw_sets.json`.

| configuration | `A0` flat | `A2` M1 / M2 / M3 | of `A0`'s set: in DSM feedback | DSM interface, not feedback | DSM self-read only | DSM feedback never carried |
|---|---|---|---|---|---|---|
| large_tokamak_nof | 75 | 16 / 47 / 10 | 34 | 14 | 27 | 41 |
| low_aspect_ratio_DEMO | 74 | 16 / 46 / 10 | 33 | 15 | 26 | 40 |
| st_regression | 73 | 16 / 47 / 10 | 23 | 22 | 28 | 30 |

The count matches the DSM feedback set (75 on the tokamak), but the membership does not: under
half of the carried set is DSM feedback.
- 26–28 carried components are self-reads, which the DSM cannot classify (e.g. `fwbs.breeder_f`,
  `pf_coil.ccls`).
- 30–41 DSM "feedback" components are never read before written at run time: branches not taken,
  or the DSM's order is not the runtime order.
- The burn time is carried on both pulsed configurations and absent on `st_regression`.
- M2 carries 46–47 components, the most of any block, which is consistent with its sweep count.

### 7.3 The tolerance, measured before the trial

**Declared rule** (in `run_trial.py`'s docstring before the stage ran):
- VMCON's gradient is a central difference with relative step h = `epsfcn` = 1e-3 (PROCESS's
  default; no input file sets it).
- Its truncation error is O(h²); function noise ε adds O(ε/h). They balance at ε ≈ h³ (Gill,
  Murray & Wright, *Practical Optimization*: optimal central step h ≈ ε^(1/3)).
- τ is therefore the largest ladder value at which the MDA-induced error of the objective
  (relative) and of every normalised constraint (absolute) stays ≤ h³ = 1e-9 at every stencil
  point, on the control (`A0`, `rbw`), in every configuration.

**Measurement** (`--noise`): the optimiser's own stencil, i.e. x and x_i(1 ± h) for every design
variable, each entered from the previous exit as VMCON does, at τ ∈ {1e-5 … 1e-12}, against τ =
1e-12. Control `A0 rbw`, maximum error over all 2n+1 points:

| τ | nof f / c | lad f / c | st f / c | meets h³ |
|---|---|---|---|---|
| 1e-5 | 0 / 3.0e-08 | 9.7e-07 / 2.0e-06 | 3.0e-06 / 9.2e-08 | no |
| 1e-6 | 0 / 2.8e-08 | 0 / 1.7e-08 | 1.2e-08 / 1.0e-08 | no |
| 1e-7 | 0 / 9.6e-12 | 0 / 0 | 1.2e-08 / 5.2e-10 | no (st) |
| **1e-8** | 0 / 9.6e-12 | 0 / 0 | 4.9e-11 / 1.8e-11 | **yes** |
| 1e-9 | 0 / 1.4e-13 | 0 / 0 | 4.9e-11 / 1.0e-11 | yes |

**Chosen τ = 1e-8** (`tolerance.json`). At it the gradient error relative to the gradient's size
is ≤ 1.2e-08 (st objective), against a truncation term of order h² = 1e-6. At V4's 1e-6 the same
control's st objective-gradient error is 4.4e-06, above that term.

V4's own control (`A0 full`) meets the rule already at 1e-6 in every configuration. Its test on
all of `y` stops one sweep late (§3, reading 4), and that sweep is what buys the accuracy. The
full `--choose-tau` output, including `A0 full` and `A2 rbw` at every τ, is in `tolerance.json`.

### 7.4 The trial at τ = 1e-8

Rendered by `run_trial.py --summarise`:

| configuration | entry | arm | test set | components tested (iterated blocks) | node calls | sweeps per block | exit audit max (whole y) | above τ at exit | distance from `full` exit |
|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | displaced | A0v4 | full | FLAT None | 147 | FLAT 7 | 4.9e-11 | 0 | — |
| large_tokamak_nof | displaced | A0 | full | FLAT None | 129 | FLAT 7 | 4.9e-11 | 0 | — |
| large_tokamak_nof | displaced | A0 | interface | FLAT 274 | 129 | FLAT 7 | 4.9e-11 | 0 | 0.0e+00 |
| large_tokamak_nof | displaced | A0 | feedback | FLAT 75 | 111 | FLAT 6 | 2.6e-09 | 0 | 2.6e-09 |
| large_tokamak_nof | displaced | A0 | rbw | FLAT 75 | 129 | FLAT 7 | 4.9e-11 | 0 | 0.0e+00 |
| large_tokamak_nof | displaced | A2 | full | M1 258, M2 240, M3 221 | 69 | M1 4, M2 7, M3 3 | 5.2e-12 | 0 | — |
| large_tokamak_nof | displaced | A2 | interface | M1 98, M2 91, M3 84 | 66 | M1 4, M2 6, M3 3 | 2.7e-10 | 0 | 2.7e-10 |
| large_tokamak_nof | displaced | A2 | feedback | M1 34, M2 34, M3 6 | 52 | M1 3, M2 6, M3 2 | 2.7e-10 | 0 | 2.7e-10 |
| large_tokamak_nof | displaced | A2 | rbw | M1 16, M2 47, M3 10 | 55 | M1 3, M2 7, M3 2 | 5.2e-12 | 0 | 0.0e+00 |
| large_tokamak_nof | cold | A0v4 | full | FLAT None | 168 | FLAT 8 | 5.4e-12 | 0 | — |
| large_tokamak_nof | cold | A0 | full | FLAT None | 129 | FLAT 7 | 2.8e-10 | 0 | — |
| large_tokamak_nof | cold | A0 | interface | FLAT 274 | 129 | FLAT 7 | 2.8e-10 | 0 | 0.0e+00 |
| large_tokamak_nof | cold | A0 | feedback | FLAT 75 | 111 | FLAT 6 | 1.5e-08 | 2 | 1.5e-08 |
| large_tokamak_nof | cold | A0 | rbw | FLAT 75 | 129 | FLAT 7 | 2.8e-10 | 0 | 0.0e+00 |
| large_tokamak_nof | cold | A2 | full | M1 258, M2 240, M3 221 | 69 | M1 4, M2 7, M3 3 | 2.4e-11 | 0 | — |
| large_tokamak_nof | cold | A2 | interface | M1 98, M2 91, M3 84 | 69 | M1 4, M2 7, M3 3 | 2.4e-11 | 0 | 0.0e+00 |
| large_tokamak_nof | cold | A2 | feedback | M1 34, M2 34, M3 6 | 52 | M1 3, M2 6, M3 2 | 1.2e-09 | 0 | 1.2e-09 |
| large_tokamak_nof | cold | A2 | rbw | M1 16, M2 47, M3 10 | 55 | M1 3, M2 7, M3 2 | 2.4e-11 | 0 | 0.0e+00 |
| low_aspect_ratio_DEMO | displaced | A0v4 | full | FLAT None | 126 | FLAT 6 | 0.0e+00 | 0 | — |
| low_aspect_ratio_DEMO | displaced | A0 | full | FLAT None | 111 | FLAT 6 | 0.0e+00 | 0 | — |
| low_aspect_ratio_DEMO | displaced | A0 | interface | FLAT 273 | 111 | FLAT 6 | 0.0e+00 | 0 | 0.0e+00 |
| low_aspect_ratio_DEMO | displaced | A0 | feedback | FLAT 73 | 93 | FLAT 5 | 0.0e+00 | 0 | 0.0e+00 |
| low_aspect_ratio_DEMO | displaced | A0 | rbw | FLAT 74 | 93 | FLAT 5 | 0.0e+00 | 0 | 0.0e+00 |
| low_aspect_ratio_DEMO | displaced | A2 | full | M1 259, M2 244, M3 221 | 63 | M1 4, M2 5, M3 3 | 0.0e+00 | 0 | — |
| low_aspect_ratio_DEMO | displaced | A2 | interface | M1 98, M2 91, M3 83 | 60 | M1 4, M2 4, M3 3 | 0.0e+00 | 0 | 0.0e+00 |
| low_aspect_ratio_DEMO | displaced | A2 | feedback | M1 32, M2 34, M3 6 | 46 | M1 3, M2 4, M3 2 | 0.0e+00 | 0 | 0.0e+00 |
| low_aspect_ratio_DEMO | displaced | A2 | rbw | M1 16, M2 46, M3 10 | 49 | M1 3, M2 5, M3 2 | 0.0e+00 | 0 | 0.0e+00 |
| low_aspect_ratio_DEMO | cold | A0v4 | full | FLAT None | 126 | FLAT 6 | 0.0e+00 | 0 | — |
| low_aspect_ratio_DEMO | cold | A0 | full | FLAT None | 111 | FLAT 6 | 0.0e+00 | 0 | — |
| low_aspect_ratio_DEMO | cold | A0 | interface | FLAT 273 | 111 | FLAT 6 | 0.0e+00 | 0 | 0.0e+00 |
| low_aspect_ratio_DEMO | cold | A0 | feedback | FLAT 73 | 93 | FLAT 5 | 0.0e+00 | 0 | 0.0e+00 |
| low_aspect_ratio_DEMO | cold | A0 | rbw | FLAT 74 | 93 | FLAT 5 | 0.0e+00 | 0 | 0.0e+00 |
| low_aspect_ratio_DEMO | cold | A2 | full | M1 259, M2 244, M3 221 | 63 | M1 4, M2 5, M3 3 | 0.0e+00 | 0 | — |
| low_aspect_ratio_DEMO | cold | A2 | interface | M1 98, M2 91, M3 83 | 60 | M1 4, M2 4, M3 3 | 0.0e+00 | 0 | 0.0e+00 |
| low_aspect_ratio_DEMO | cold | A2 | feedback | M1 32, M2 34, M3 6 | 46 | M1 3, M2 4, M3 2 | 0.0e+00 | 0 | 0.0e+00 |
| low_aspect_ratio_DEMO | cold | A2 | rbw | M1 16, M2 46, M3 10 | 49 | M1 3, M2 5, M3 2 | 0.0e+00 | 0 | 0.0e+00 |
| st_regression | displaced | A0v4 | full | FLAT None | 147 | FLAT 7 | 1.0e-10 | 0 | — |
| st_regression | displaced | A0 | full | FLAT None | 123 | FLAT 7 | 1.0e-10 | 0 | — |
| st_regression | displaced | A0 | interface | FLAT 257 | 123 | FLAT 7 | 1.0e-10 | 0 | 0.0e+00 |
| st_regression | displaced | A0 | feedback | FLAT 53 | 106 | FLAT 6 | 3.0e-09 | 0 | 3.0e-09 |
| st_regression | displaced | A0 | rbw | FLAT 73 | 106 | FLAT 6 | 3.0e-09 | 0 | 3.0e-09 |
| st_regression | displaced | A2 | full | M1 268, M2 216, PULSE 0, M3 223 | 81 | M1 4, M2 7, PULSE 1, M3 4 | 1.0e-10 | 0 | — |
| st_regression | displaced | A2 | interface | M1 99, M2 72, PULSE 0, M3 86 | 81 | M1 4, M2 7, PULSE 1, M3 4 | 1.0e-10 | 0 | 0.0e+00 |
| st_regression | displaced | A2 | feedback | M1 34, M2 14, PULSE 0, M3 5 | 64 | M1 3, M2 6, PULSE 1, M3 3 | 3.0e-09 | 0 | 3.0e-09 |
| st_regression | displaced | A2 | rbw | M1 16, M2 47, PULSE 1, M3 10 | 64 | M1 3, M2 6, PULSE 1, M3 3 | 3.0e-09 | 0 | 3.0e-09 |
| st_regression | cold | A0v4 | full | FLAT None | 168 | FLAT 8 | 1.1e-10 | 0 | — |
| st_regression | cold | A0 | full | FLAT None | 140 | FLAT 8 | 1.1e-10 | 0 | — |
| st_regression | cold | A0 | interface | FLAT 257 | 140 | FLAT 8 | 1.1e-10 | 0 | 0.0e+00 |
| st_regression | cold | A0 | feedback | FLAT 53 | 123 | FLAT 7 | 3.3e-09 | 0 | 3.3e-09 |
| st_regression | cold | A0 | rbw | FLAT 73 | 123 | FLAT 7 | 3.3e-09 | 0 | 3.3e-09 |
| st_regression | cold | A2 | full | M1 268, M2 216, PULSE 0, M3 223 | 84 | M1 4, M2 8, PULSE 1, M3 4 | 1.1e-10 | 0 | — |
| st_regression | cold | A2 | interface | M1 99, M2 72, PULSE 0, M3 86 | 84 | M1 4, M2 8, PULSE 1, M3 4 | 1.1e-10 | 0 | 0.0e+00 |
| st_regression | cold | A2 | feedback | M1 34, M2 14, PULSE 0, M3 5 | 67 | M1 3, M2 7, PULSE 1, M3 3 | 3.3e-09 | 0 | 3.3e-09 |
| st_regression | cold | A2 | rbw | M1 16, M2 47, PULSE 1, M3 10 | 67 | M1 3, M2 7, PULSE 1, M3 3 | 3.3e-09 | 0 | 3.3e-09 |

**Reading.**
1. **`rbw` is safe where the DSM set is not.** All 12 `rbw` runs end with 0 whole-`y` components
   above τ (maximum 3.3e-09). The DSM feedback set fails once: `large_tokamak_nof`, cold, `A0`,
   with `costs.coecap` at 1.47e-08 and `costs.coe` at 1.43e-08.
   - The two tests see the same trajectory, because the test does not change the computation.
     The DSM-set run stopped after 6 sweeps; the `rbw` run's test failed at sweep 6 and it took a
     7th.
   - So at sweep 6 a component in `rbw` minus DSM-feedback was still moving by at least τ. In
     this run, those carried-but-missing components are M2's `pf_coil.*` self-carried arrays
     (e.g. `pf_coil.stress_z_cs_self_midplane_profile`).
   - This is the demonstrated case of a missing variable that the first pass (at τ = 1e-6) could
     not show.
2. **What the fixed control costs.** Node calls (displaced / cold), matched rule, matched τ:

   | configuration | `A0v4` | `A0` full | `A0` rbw | `A2` full | `A2` rbw | `A2 rbw / A0 rbw` |
   |---|---|---|---|---|---|---|
   | large_tokamak_nof | 147 / 168 | 129 / 129 | 129 / 129 | 69 / 69 | 55 / 55 | 0.43 / 0.43 |
   | low_aspect_ratio_DEMO | 126 / 126 | 111 / 111 | 93 / 93 | 63 / 63 | 49 / 49 | 0.53 / 0.53 |
   | st_regression | 147 / 168 | 123 / 140 | 106 / 123 | 81 / 84 | 64 / 67 | 0.60 / 0.54 |

   - `rbw` exits are bit-identical to the `full` exits on nof and lad, and 3.0e-09 away on st.
   - Deferring feed-forward and per-run nodes (`A0v4` → `A0 full`) removes 12–23 % of node calls.
   - `rbw` removes one further sweep where one is removable: lad, st, and `A2` everywhere.
3. **The noise stencil prices the tolerance** (node calls over the 2n+1 points, `A0`). `rbw` at
   1e-8 costs 2589 / 2367 / 1782 (nof / lad / st). V4's whole-`y` test at 1e-6 costs
   2607 / 2493 / 1816 at comparable accuracy (§7.3). So at the accuracy the optimiser needs, the
   structural fix costs about what V4's lagging whole-state test costs: −1 % / −5 % / −2 %. **Its
   value is correctness by construction and a cheaper test, not fewer sweeps.**

### 7.5 Wall clock (context, never evidence)

One subprocess per case, one warm-up evaluation discarded, then 7 timed evaluations of the same
displaced entry (seed 1), serial, τ = 1e-8. Node calls were identical in all 7 repetitions of
every case.
- "predicate" is the coupling-state reads plus the residuals inside `call_models`.
- "model ms per node call" is (`call_models` − predicate) / node calls, so it includes every
  non-predicate overhead.

| configuration | arm | test set | reps | node calls | sweeps | call_models ms, median [min, max] | predicate ms, median [min, max] | predicate share | once-per-run ms | model ms per node call |
|---|---|---|---|---|---|---|---|---|---|---|
| large_tokamak_nof | A0v4 | full | 7 | 147 | 7 | 77.3 [73.8, 78.7] | 30.01 [28.83, 30.77] | 38.9 % | 0.0 | 0.32 |
| large_tokamak_nof | A0 | full | 7 | 129 | 9 | 87.5 [82.5, 191.0] | 31.39 [29.11, 32.95] | 34.8 % | 0.2 | 0.43 |
| large_tokamak_nof | A0 | rbw | 7 | 129 | 9 | 58.6 [56.7, 135.5] | 4.64 [4.22, 5.21] | 7.5 % | 0.2 | 0.42 |
| large_tokamak_nof | A2 | full | 7 | 69 | 16 | 67.4 [64.4, 145.3] | 20.18 [19.03, 24.79] | 29.6 % | 0.3 | 0.70 |
| large_tokamak_nof | A2 | rbw | 7 | 55 | 14 | 45.1 [43.4, 116.4] | 4.93 [4.80, 5.27] | 10.9 % | 0.2 | 0.73 |
| low_aspect_ratio_DEMO | A0v4 | full | 7 | 126 | 6 | 64.7 [62.6, 67.4] | 24.34 [24.21, 25.37] | 38.3 % | 0.0 | 0.32 |
| low_aspect_ratio_DEMO | A0 | full | 7 | 111 | 8 | 74.8 [73.6, 144.7] | 25.31 [24.94, 25.79] | 33.9 % | 0.2 | 0.45 |
| low_aspect_ratio_DEMO | A0 | rbw | 7 | 93 | 7 | 49.6 [45.9, 139.8] | 4.26 [3.39, 4.70] | 7.4 % | 0.2 | 0.49 |
| low_aspect_ratio_DEMO | A2 | full | 7 | 63 | 14 | 57.9 [55.4, 128.9] | 17.74 [16.74, 18.10] | 30.8 % | 0.3 | 0.63 |
| low_aspect_ratio_DEMO | A2 | rbw | 7 | 49 | 12 | 50.2 [43.3, 136.7] | 5.75 [4.45, 7.30] | 11.0 % | 0.3 | 0.91 |
| st_regression | A0v4 | full | 7 | 147 | 7 | 77.1 [73.1, 83.6] | 30.17 [28.62, 32.30] | 38.6 % | 0.0 | 0.32 |
| st_regression | A0 | full | 7 | 123 | 9 | 86.0 [81.2, 94.6] | 29.54 [28.52, 33.22] | 34.5 % | 0.2 | 0.46 |
| st_regression | A0 | rbw | 7 | 106 | 8 | 49.4 [48.8, 60.9] | 3.67 [3.51, 6.06] | 7.4 % | 0.2 | 0.43 |
| st_regression | A2 | full | 7 | 81 | 18 | 64.3 [61.5, 67.3] | 20.11 [19.52, 23.46] | 31.8 % | 0.2 | 0.54 |
| st_regression | A2 | rbw | 7 | 64 | 15 | 40.7 [39.8, 43.6] | 4.59 [4.49, 5.08] | 11.5 % | 0.2 | 0.57 |

**Reading** (medians; each case's range is in the table):
- **The convergence check is a large share of an evaluation.**
  - In V4's control it takes 38–39 % of `call_models` time (24–30 ms of 65–77 ms).
  - In `A2` with the whole-`y` test it takes 30–32 %.
  - With the `rbw` test, 7.4–7.5 % in `A0` and 10.9–11.5 % in `A2`.
  - The residual's cost scales with the number of components tested, and the models are fast
    (about 0.3 ms per node call), so an 840-component Python residual per sweep is comparable to a
    sweep of models.
- **The fixed control runs 24–36 % faster than V4's.** `A0v4` → `A0 rbw`: 77 → 59 ms (nof),
  65 → 50 ms (lad), 77 → 49 ms (st).
- **Wall-clock savings of the partition are much smaller than its node-call savings.**
  - `A2 rbw / A0 rbw` is 0.77 / 1.01 / 0.82 in wall clock against 0.43 / 0.53 / 0.60 in node
    calls.
  - The non-predicate time per node call is 0.32 ms in `A0v4`, 0.42–0.49 ms in `A0`, and
    0.54–0.91 ms in `A2`. The partitioned and deferring paths spend time per sweep that is not
    model time.
  - Hypothesis, not measured here: `_sweep_block` walks the whole dispatch body for every block
    sweep and drops the nodes outside the block, so `A2`'s 12–15 dispatch sweeps pay the
    dispatch cost 12–15 times.
  - The paper should state this beside any node-call ratio.
- Some cases have one slow repetition (maximum up to 2.5× the median); medians are quoted.

### 7.6 Limits of the second pass

- The census is a union over 8 evaluations per configuration and arm (4 seeds × 2 arms, same
  δ). A branch taken only elsewhere, e.g. along an optimisation path, is not observed. The next
  step toward a V5 artifact is a census over an optimisation run's evaluations, and a gate with
  teeth: drop one carried component and the audit must fail.
- The per-node read attribution cannot see reads through references a model kept from an earlier
  sweep, or instance-state coupling.
- The tolerance rule uses the standard balance ε ≈ h³ and the measured stencil at the reference
  point only. The optimiser's path visits other points.
- Timings come from one machine, one day, 7 repetitions; they are context. Node calls and
  bit-comparisons are the acceptance quantities.

### 7.7 Proposals (the user's to rule)

- **(a)** V5's control: flat Gauss–Seidel stopping on the `rbw` set measured for the arm's own
  order, τ from the declared h³ rule (1e-8 here), feed-forward and per-run nodes once after
  convergence. `A2` uses the same definition per block.
- **(b)** Retire the DSM feedback set as a test set. It misses carried self-reads and failed the
  audit once at τ = 1e-8.
- **(c)** Report wall clock beside node calls in the paper, with the per-sweep dispatch overhead
  named. Consider, as a separate and approved driver change, whether `_sweep_block`'s full walk
  per block sweep is part of the architecture or an implementation cost to remove.

## 8. Orchestrator's critical assessment (protocol §5) — 2026-09-29

*Written by the orchestrating session (`process-surgery-65`), which also executed the task at the user's direct request; the assessment therefore verifies by checks the task did not make (the standing rule: verify differently, never by repeating the press), not by re-reading its own work. All checks below are read-only over the records and one 6-second re-made run in a scratch directory; scripted where they produce a number.*

**Scope.** Exploratory, evaluation phase only, no implementation for V4 or V5. Zero edits under `MDA_partitioning_experiment_v4/`, `harness/child/` or the root `process/`: `git diff 38d2f21f..HEAD --stat` over those paths is empty, and `git status --ignored` on the V4 folder is empty after every stage. The 13 files the branch adds are the task folder, this report, and three documents (queue row, V5 item 6, DSM validation V18). Records are `smoke` kind throughout, so no V4 tally can read them.

**Checks made here, and what they found.**

1. **The one audit failure's mechanism, from the per-pass logs, not the audit.** At `large_tokamak_nof`, cold, `A0`: the DSM-feedback run's pass-6 residual over its set is 3.4e-09 (stop); in the same pass the whole-`y` residual has `pf_coil.stress_z_cs_self_midplane_profile` at 6.4e-08 — a component in the census set and not in the DSM set. The census run's pass-6 residual over *its* set is exactly 6.399e-08 and it takes a seventh sweep. So §7.4's reading 1 holds on the logs: the carried component the DSM set lacks is the one that decided. The components the audit then flags (`costs.coecap`, `costs.coe`) are downstream of it, in neither set, and settle after the seventh sweep.
2. **Headline node calls recounted** from `metrics.json` (`node_calls_single_eval`), displaced entry: 147/129/129/69/55 (nof), 126/111/93/63/49 (lad), 147/123/106/81/64 (st) — every cell of §7.4's table agrees. The `A0` count decomposes as the record's node census says: 7 sweeps × 18 in-loop nodes + `costs`, `vacuum`, `water_use` once each = 129, against `A0v4`'s 21 nodes × 7 = 147. The once-per-run execution is therefore counted, and counted once.
3. **The tolerance rule re-applied independently** to `tolerance.json`'s rows (largest τ such that it and every tighter τ meet `max(objf_rel_err, conf_abs_err) ≤ epsfcn³` on `A0 rbw` in every configuration): 1e-08, as the file records.
4. **Timing repetitions**: node calls and sweeps identical across all 7 repetitions and the discarded warm-up in all 15 cases; every entry readback bit-exact. The medians §7.5 quotes are of same-computation repetitions.
5. **Stamp survey** (every `metrics.json` under the task's records): 39 first-pass records at `9d80c84b`; 24 census + 2 reference at `27dc1008`; 54 trial at `33ca7b52`; **one deviation** — the `st_regression` reference at `2977fcb3` with the tree dirty (2 modified, 3 untracked: the second-pass scripts, written but not yet committed when the smoke test made it). Every st entry derives from that reference's exit state. Checked by re-making the same job at the clean tip `fea99a9f` into a scratch directory: `y_exit.json` state identical component for component, objective bit-identical, 147 node calls both. The deviation is recorded and is without consequence.
6. **The in-process records (`inproc.json`, noise and timing) carry no tree stamp** — only `process_file`, which places them in this worktree but not at a commit. Their commit is established by this session's ordering (noise pressed after `2b6aaca4`, timing after `33ca7b52`) and by `--choose-tau` re-run at `bd543f49` reproducing `tolerance.json` byte for byte. A V5 instrument built from `inproc_child.py` must stamp `tree_git_head` the way `evaluate.py` does; noted as a defect of the scratch instrument, not of the finding.

**Findings on the report itself.**

- §7.3's claim "V4's own control (`A0 full`) meets the rule already at 1e-6" is read from `tolerance.json` (nof 9.6e-12, lad 0, st 2.6e-10) and holds; the report should not be read as saying V4's campaign numbers are wrong — they are not, and D30's `frozen` ruler is unaffected.
- The first pass (§3–§4) said "no variable was shown to be missing" at τ = 1e-6; the second pass shows one at τ = 1e-8. Both statements are true at their tolerance; §4 stands as the record of its day and §7 supersedes it as the finding.
- §7.5's dispatch-overhead explanation for `A2`'s wall-clock ratio is labelled a hypothesis and is not measured; it stays a hypothesis in V5 item 6.
- Numbers quoted in the user's chat (e.g. "24–36 % faster") are the report's §7.5 medians; nothing was published outside the committed scripts' output.

**Verdict: merge.** Nothing acceptance-bearing depends on this task; its outputs are a V5 improvement item (6), a DSM-validation entry (V18) and a queue row, and the trial's evidence for them is reproducible from the committed scripts at the stamped commits. The deviation in check 5 is recorded here rather than repaired, because the re-made reference is bit-identical and re-pressing 27 st records to change a stamp would be a repeat of the press, not a verification.

**Carried forward** (not this task's to fix): the census over an optimisation run and a gate with teeth (V5 item 6); the tree stamp on in-process instruments; A90 (m2-probe-binding), registered during this assessment, reads the same block-sweep counters and should cite §7.2's per-block carried-set sizes (M2 46–47 of 240–244) as context for M2's binding.
