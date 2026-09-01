> **Document status** — **LIVE · CURRENT**
> The task report for A20 (registry-append), open at the time of writing. It describes branch
> `A20-registry-append`, off `architecture_surgery` at **`73439685`** (experiment base commit
> `c0ae5b28`), and its numbers are current evidence. It will be archived to `deprecated/` at
> merge; position in that folder would record lifecycle, not staleness (trap T3).

# A20 (registry-append) — appending iteration variable 178 and constraint 93

| | |
|---|---|
| **Task** | A20 (registry-append) — framework step F2 |
| **Branch** | `A20-registry-append`, in the isolated worktree `/home/wrutten/projects/PROCESS_surgery/.claude/worktrees/agent-a9ad897efd79e82be` |
| **Base** | `73439685` on `architecture_surgery`; experiment base commit `c0ae5b28` |
| **Governed by** | decision **D10** — *registry numbers are appended, never fitted into gaps* — and the allocation table [`../plans/REGISTRY_ALLOCATIONS.md`](../plans/REGISTRY_ALLOCATIONS.md) |
| **Environment** | `PROCESS_surgery_env`, `PYTHONPATH` pinned to this worktree and the exact tree asserted per subprocess (trap T6) |
| **Date** | 2026-09-01 |
| **Status** | Complete — **all four gates PASS on all four scenarios** |

**Vocabulary, once.** *Iteration variables* are the design variables the optimiser is allowed to
move; an input deck selects them by number in its `ixc` list. *Constraints* are selected the same
way by number in `icc`. Both are held in number-keyed registries in the solver: `ITERATION_VARIABLES`
in `process/core/solver/iteration_variables.py`, and a decorator-populated registry in
`process/core/solver/constraints.py`. `lablcc` is the parallel list of human-readable constraint
labels that the output writer indexes by constraint number. A *deck* is one `IN.DAT` input file.
*Byte-identical* here means every line of the MFILE output file matches, plus every quantity the
gates name compared as a hex float literal — an exact IEEE-754 double, not a tolerance.

---

## 1. Verdict

**Appending is inert, and the mechanism works.** Iteration variable **178** and constraint **93**
were appended to the solver registries. With no deck referencing them:

- all four scenarios produce **whole-MFILE-identical** output against a `git archive` of the
  frozen base commit `c0ae5b28` — **0 differing lines** out of 15 917–18 692 per scenario, in
  every arm;
- every hex-float signature (`norm_objf`, `conf_l2`, `sqsumsq`, the iteration-variable vector) is
  identical to the base commit *and* identical to the same tree measured before the append;
- sweep counts are unchanged to the unit: 2029 / 4286 / 1891 / 29;
- all four scenarios still solve, `ifail = 1`.

The derived cap moved 177 → 178 by itself, as D10 predicted, and **twelve** arrays sized by it
grew in step. No gap was consumed: the registry still has exactly 94 gaps in 1–177.

**The claim every planned lifting task depends on — that a registry can be appended to without
disturbing existing results — is upheld by measurement, not assumed.**

One code path *does* change its iteration count when the constraint registry grows. It is inert
for our decks, and the mechanism is stated in §5. It is a latent PROCESS defect worth reporting
upstream, not a blocker here.

---

## 2. What was appended

The pair (178, 93) is a **null lift**: one design variable and the one equality constraint that
determines it, touching no physics model. That shape deliberately rehearses what A4
(burn-time-lift) and A9–A11 (subdriver lift) will do for real.

| | |
|---|---|
| **Iteration variable 178** | `IterationVariable("framework_placeholder", "numerics", 0.1, 10.0)` in `process/core/solver/iteration_variables.py` |
| **Its target** | a new scalar `NumericsData.framework_placeholder = 1.0` in `process/data_structure/numerics.py` |
| **Constraint 93** | `constraint_equation_93` in `process/core/solver/constraints.py`, an equality pinning `framework_placeholder` to 1.0 |
| **Its label** | `"Framework placeholder consistency"`, appended to `lablcc` in the same file as the field |

Four files changed; 108 lines added, 12 removed, of which the allocation-table update is 71 lines.
Nothing under `process/models/` was touched, so decision **D11**'s model-edit approval gate does
not apply. The three docstring lists in `numerics.py` that enumerate constraint and
iteration-variable numbers were extended in step so the documentation does not fall behind the
registry.

---

## 3. Gates

Measured with `arch_surgery/idf_probe/run_stage0.py` (5 arms × 4 scenarios, `--reps 2`) and
`arch_surgery/idf_probe/compare.py`, at the strength those already implement. The reference arm
`pristine` is a `git archive` extraction of `c0ae5b28` with the probe absent entirely.

### Gate 1 — neutrality: **PASS 4/4**

Probe switch unset (`control`) and probe on (`baseline`), both against `pristine`.

| Scenario | hex-float signature fields differing | MFILE lines compared | MFILE lines differing (each of 4 arms) | `norm_objf` (hex) |
|---|---|---|---|---|
| `large_tokamak_nof` | 0 | 16 174 | 0 | `0x1.99999999b822dp+0` |
| `low_aspect_ratio_DEMO` | 0 | 16 435 | 0 | `-0x1.a00c1e7544537p-2` |
| `st_regression` | 0 | 18 692 | 0 | `-0x1.096acf3342eefp+4` |
| `large_tokamak_eval` | 0 | 15 917 | 0 | *(evaluation run: no objective; MFILE carries the comparison)* |

The signature compares `norm_objf`, `conf_l2`, `sqsumsq`, the full iteration-variable vector and
every raw MFILE field, all as hex float literals. Iteration variables are compared here only as
part of a *bit-identity* test, not as a correctness criterion — D6's prohibition is on gating
correctness on them across a changed driver, which is not what this is.

**A stronger check than the gate asks for.** The same matrix was run on this branch's base
`73439685` *before* the append, and its results were kept. Pre-append and post-append hex
signatures are identical for every scenario, and so are the sweep counts. So the append is
neutral both against the frozen base commit and against the immediately preceding state of this
branch — the two could in principle have differed, and do not.

### Gate 2 — determinism: **PASS 4/4**

Two independent `baseline` replicates per scenario, each a fresh subprocess in its own working
directory.

| Scenario | replicates | differing signature fields | sweeps (both replicates) |
|---|---|---|---|
| `large_tokamak_nof` | 2 | 0 | 2029 |
| `low_aspect_ratio_DEMO` | 2 | 0 | 4286 |
| `st_regression` | 2 | 0 | 1891 |
| `large_tokamak_eval` | 2 | 0 | 29 |

### Gate 3 — solves: **PASS 4/4**

`ifail = 1` on `large_tokamak_nof`, `low_aspect_ratio_DEMO`, `st_regression` and
`large_tokamak_eval`; run status `ok`, no error, in every arm.

### Gate 4 — derivation intact: **PASS**

`N_ITERATION_VARIABLES_MAX` is `max(ITERATION_VARIABLES.keys())` and was **not** edited. Measured
in the tree, not inferred:

| Quantity | Before | After |
|---|---|---|
| registry entries | 83 | **84** |
| highest key | 177 | **178** |
| `N_ITERATION_VARIABLES_MAX` | 177 | **178** |
| gaps in 1 … highest key | 94 | **94** (unchanged — no gap consumed) |
| constraints registered | 82 | **83** |
| highest constraint id | 92 | **93** |
| `len(lablcc)` | 92 | **93** |

**Every array sized by the derived cap** was checked individually rather than inferred, and all
twelve grew from 177 to 178: `ixc`, `lablxc`, `name_xc`, `boundl`, `boundu`, `scale`, `scafc`,
`xcm`, `xcs`, `itv_scaled_lower_bounds`, `itv_scaled_upper_bounds`, `vlam`. (The allocation table
named four; `vlam` and six others were found by enumeration.) `initialise_iteration_variables`
populated `lablxc[177] = "framework_placeholder"`, `boundl[177] = 0.1`, `boundu[177] = 10.0` from
the registry with no hand-maintained parallel list, and the input validator's accepted range for
`ixc` moved from `(1, 177)` to `(1, 178)` on its own.

### Supplementary — the pair is live, not decorative

Not a gate, and not committed: a scratch copy of `large_tokamak_nof` in the scratch directory,
with `icc = 93` and `ixc = 178` added and the equality-constraint count raised 3 → 4.

- Solves: `ifail = 1`, 21 iteration variables against the normal 20, 4 equality constraints
  against 3, 23 inequality constraints unchanged.
- The placeholder converges to exactly `1.0`; constraint 93's normalised residue is `-0.0`.
- The MFILE carries the whole path end to end: `framework_placeholder (itvar021)`, its scaled
  value, its range-normalised value and both bounds; and `Framework placeholder consistency`
  under `(eq_con093)`, `(res_eq_con093)`, `(val_eq_con093)`, `(eq_units_con093)` — the label
  resolved through the `lablcc` entry, confirming the label was extended in step and no reporting
  gap was left.
- The objective moves from `1.6000000000277723` to `1.600000000022661`, a relative change of
  **3.2 × 10⁻¹²** against a solver tolerance `epsvmc = 1 × 10⁻⁷`. The added variable perturbs the
  finite-difference and iterate path, not the optimum.

### Upstream's own test suite

`tests/unit` passes in full: **843 passed, 4 skipped**. Note that
`tests/unit/core/test_constraints.py::test_constraint_functions` parametrises itself over the
constraint registry, so the appended constraint 93 was picked up and exercised automatically —
177 cases ran where 176 would have before.

---

## 4. The input-language divergence

Requested explicitly, and measured in both directions rather than argued.

**A fork deck fed to upstream is refused at input-parse time, before any model runs.** Both
failures are `ProcessValidationError` raised from `parse_input_file`, i.e. during
`init.init_process`, so nothing is computed and nothing is written:

- `icc = 93` → `Variable 'icc' at line 47 is not one of (1, 2, 3, …, 92) (value = 93)`
- `ixc = 178` → `Variable 'ixc' at line 47 is not on the prescribed range (1, 177) (value = 178)`

This is the good failure mode: loud, immediate, and naming the offending line. It is precisely the
failure that reusing one of the 94 gaps would *not* have produced — a gap-reuse gives a silent
misinterpretation with no error at all, which is why D10 exists.

**An upstream deck fed to this fork loads and runs unchanged.** Appending only *widens* the
accepted sets — `ixc` from `(1, 177)` to `(1, 178)`, `icc` from 82 choices to 83 — and reassigns
no existing number, so every deck valid upstream stays valid here with the same meaning. This is
what gate 1 measures directly: the four scenario decks are upstream-shaped decks, and they produce
byte-identical output.

**So the divergence is one-way.** This fork is a strict superset of upstream's input language:
fork accepts upstream, upstream rejects fork. It is inherent to lifting anything and is not a
blocker, but every write-up that reports a lifted variable must say so.

**Not yet claimed upstream.** `upstream/main` at `6df46205` (2026-08-28, four days after the
frozen base) still ends at iteration variable 177 and constraint 92 — 82 registered constraints.
So 178 and 93 remain free upstream, and the fork's numbering does not yet collide with anything
real. That will not stay true indefinitely; it is a fact with a date on it, and any future
attempt to contribute a lifted variable upstream must re-check it.

---

## 5. What appending does change

Honest accounting: growing the registries is not a literal no-op in the source, only in the
results. Three code paths read a registry size.

1. **`set_active_constraints`** (`process/core/init.py`) scans
   `icc[0 : ConstraintManager.num_constraints()]` — a loop bounded by the **registry size**, not
   by the number of constraints the deck names. Appending 93 widens that scan from 82 to 83
   slots. `icc` is 500 long and zero-filled, and our decks name 18–26 constraints, so slot 82 is
   0 and the extra iteration counts nothing. Gate 1 confirms this empirically rather than by
   argument. **This is a latent PROCESS defect independent of our change**: a deck naming more
   than `num_constraints()` constraints would be silently truncated, and the bound should be
   `n_constraints` or the array length. Recommended for `PROCESS_code_analysis`'s bug reports.
2. **Input validation ranges widen.** `ixc` moves to `(1, 178)`; `icc` gains 93 as a choice;
   `n_equality_constraints` and `n_inequality_constraints` move from `range(0, 82)` to
   `range(0, 83)`. All strictly permissive — nothing previously accepted is now rejected.
3. **The probe's field enumeration grows by one.** `_idf_probe_modules.install` and
   `_idf_probe_frozen._save_state` walk every dataclass field of every namespace, so the new
   `numerics.framework_placeholder` adds one entry to the snapshot vector. Since nothing ever
   writes it, it produces no dependency edge and no state change. Verified: the probe's full
   sweep-anatomy output is identical before and after the append in every field except wall
   clock, which is not evidence (working rules; issue **I-10**).

Timings, for context only and carrying no argument: the post-append matrix took 217.7 s against
222.6 s pre-append, `n = 1` each, one arm per scenario per replicate, on a machine whose
identical-work spread is documented at up to 35 % (issue **I-10**). Nothing in this report rests
on that.

---

## 6. Autonomous decisions, with reversal paths

**AD1 — The placeholder is a live null pair, and it needed one new scalar on the numerics data
structure.**
The brief asked for entries that are minimal and clearly labelled. A registry entry pointing at a
non-existent attribute would have been smaller still, but it could not be exercised: constraint 93
must be a callable returning a real residual, and a variable whose target does not exist raises as
soon as any deck names it. So the pair was made genuinely usable by adding
`NumericsData.framework_placeholder: float = 1.0`.
*Why `numerics` and not a physics data structure:* `numerics` is the driver's own data, so the
placeholder cannot reach a model even if activated. `numerics.py` had to be edited anyway to
extend `lablcc`.
*Why not an existing variable:* every candidate was either already an iteration variable, or a
live physics quantity (activating it would change physics), or dead-but-overwritten — the last
would give a design variable the models silently clobber every sweep, which is a worse trap than
either alternative.
*Cost:* one field, which the probe now enumerates (§5.3, measured neutral).
*Reversal:* delete the field, the registry entry, the constraint function and the `lablcc` entry —
four contiguous hunks, no other code refers to any of them.

**AD2 — F2 took constraint 93; A4 and A9–A11 shifted up by one.**
The allocation table as written reserved constraint 93 for A4 (burn-time-lift) and gave F2 no
constraint at all, while the queue row for A20 (registry-append) in `MASTER_TODO.md` — and
decision D10's "constraints append from 93" — assign 93 to F2. Both cannot hold. The queue row is
the later statement and is the row this task was dispatched under, so F2 took 93 and the
reservations below it moved: A4 to constraint 94, A9–A11 to 95–98. Nothing had been allocated
under the old numbering, so no code, deck or document refers to the superseded reservations.
*Reversal:* renumber this pair's constraint and restore 93 → A4, 94–97 → A9–A11; a single-number
edit in three files plus the table.

**AD3 — The worktree was re-based onto `architecture_surgery`'s tip before any work.**
The worktree was created at `6df46205` — upstream `main`, which is *not* an ancestor of
`architecture_surgery` and contains no `arch_surgery/` directory at all. Work there would have
been unmergeable and would have measured a tree without the probe. Branch `A20-registry-append`
was created at `73439685`, the `architecture_surgery` tip that minted this task, and checked out
in place. The frozen base commit `c0ae5b28` was not touched, rebased or re-pinned.
*Reversal:* none needed; this restored the intended state rather than choosing between options.

**AD4 — A pre-append run of the whole gate matrix was taken and kept.**
Not asked for, and it doubled the run time (≈ 222 s). Rationale: without it, a neutrality failure
could not be attributed to the append rather than to something already present at `73439685`. It
also yielded the stronger pre/post identity statement in §3. It cost one extra matrix and
answered a question that would otherwise have been unanswerable after the fact.
*Reversal:* n/a — a measurement, not a change.

**AD5 — The demonstration deck was not committed.**
The scratch deck naming `ixc = 178` and `icc = 93` lives in the scratch directory only. The brief
requires that no scenario deck reference the appended entries, and a committed deck that did so
would be a standing invitation for a later task to pick it up as a scenario.
*Reversal:* recreate it — it is `large_tokamak_nof.IN.DAT` with `neqns` 3 → 4 and two lines added
after `icc = 11`; the recipe is in this report.

---

## 7. Things noticed, not fixed

- **`lablxc`'s docstring is stale in upstream.** It lists `(174) NOT USED` and `(175) NOT USED`,
  but the registry has had `174: triang` and `175: kappa` for some time, and 176 and 177 are
  absent from the list entirely. Only the `(178)` line was added; correcting upstream's existing
  entries is out of scope for this task and would enlarge the diff against upstream for no
  experimental gain.
- **`set_active_constraints`'s loop bound** — §5.1. A PROCESS defect, to be routed to
  `PROCESS_code_analysis/docs/bug_reports/` per protocol §11's split between architecture
  critiques and implementation defects.
- **`ruff` is not installed in `PROCESS_surgery_env`**, so the repository's linter and formatter
  could not be run over the changed files. The diff follows the surrounding style by inspection.
  Fixing this is an environment change and therefore the user's to make:
  `conda install -n PROCESS_surgery_env -c conda-forge ruff`. Not a blocker; flagged so the merge
  reviewer knows the check was not run.

---

## 8. Reproduction

```
# pristine reference: a git archive of the frozen base commit
git archive c0ae5b28 -o $TMPDIR/pristine.tar
mkdir -p $TMPDIR/pristine_c0ae5b28 && tar -xf $TMPDIR/pristine.tar -C $TMPDIR/pristine_c0ae5b28

# the gate matrix: 5 arms x 4 scenarios, each a fresh subprocess in its own directory
cd arch_surgery/idf_probe
/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python run_stage0.py \
    --pristine-tree $TMPDIR/pristine_c0ae5b28 --reps 2 --jobs 4
/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python compare.py
```

`run_stage0.py` sets `PYTHONPATH` to this worktree for every subprocess and `run_one.py` asserts
the **exact** tree it imported, not a path prefix — trap T6, without which the measurement
silently uses the main checkout. Raw artifacts land in `arch_surgery/idf_probe/runs/` and stay
untracked; the numbers above are the committed summary.

---

## 9. Change log (append-only)

| # | Date | Change |
|---|---|---|
| 1 | 2026-09-01 | Worktree found at `6df46205` (upstream `main`, not an ancestor of `architecture_surgery`, no `arch_surgery/`). Created branch `A20-registry-append` at `73439685` and checked it out (AD3). |
| 2 | 2026-09-01 | Read the governing documents; confirmed the base-commit archive and the branch base agree exactly on registry sizes — 83 iteration variables to 177, 82 constraints to 92, `lablcc` 92 — so no registry drift between `c0ae5b28` and `73439685`. |
| 3 | 2026-09-01 | Pre-append gate matrix run and kept (AD4). All gates PASS 4/4. |
| 4 | 2026-09-01 | Appended iteration variable 178 (`framework_placeholder`) with a comment stating why it is appended and not fitted into a gap. |
| 5 | 2026-09-01 | Added `NumericsData.framework_placeholder` (AD1); extended `lablcc` with the 93rd label in step, and the two enumerating docstrings. |
| 6 | 2026-09-01 | Registered constraint 93 pinning the placeholder to 1.0. |
| 7 | 2026-09-01 | Gate 4 checked directly in the tree: cap 177 → 178, twelve arrays grown, gap count unchanged at 94, `lablcc` 93, constraint 93 evaluable with residue 0. |
| 8 | 2026-09-01 | Post-append gate matrix. Gates 1–3 PASS 4/4; signatures and sweep counts identical to the pre-append run. |
| 9 | 2026-09-01 | Divergence measured in both directions against the pristine base tree; upstream `main` at `6df46205` confirmed still to end at 177 / 92. |
| 10 | 2026-09-01 | Supplementary live demonstration of the (178, 93) pair on a scratch deck; solves, `ifail = 1`, objective unchanged to 3.2e-12 relative. |
| 11 | 2026-09-01 | `tests/unit` run: 843 passed, 4 skipped; constraint 93 auto-exercised by upstream's own parametrised test. |
| 12 | 2026-09-01 | Allocation table updated in the same commit as the append: F2's row moved to ALLOCATED, A4 and A9–A11 constraint reservations shifted by one (AD2), measured facts folded into the rule and divergence sections. |
