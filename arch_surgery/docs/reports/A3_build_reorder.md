> **Document status** — **LIVE · CURRENT**
> The task report for A3 (build-reorder), open at the time of writing. It describes branch
> `A3-build-reorder`, off `architecture_surgery` at **`c9cc917f`** (experiment base commit
> `c0ae5b28`), and its numbers are current evidence. It will be archived to `deprecated/` at
> merge; position in that folder would record lifecycle, not staleness (trap T3).

# A3 (build-reorder) — moving `build` out of M1's span

| | |
|---|---|
| **Task** | A3 (build-reorder) — Stage 2 of the MDA partition experiment; framework variant point **VP1**, hook **F7a** |
| **Branch** | `A3-build-reorder`, in the isolated worktree `/home/wrutten/projects/PROCESS_surgery/.claude/worktrees/agent-afd5cf122f7d7b3e7` |
| **Base** | `c9cc917f` on `architecture_surgery`; experiment base commit `c0ae5b28` |
| **Environment** | `PROCESS_surgery_env`; `PYTHONPATH` pinned to the tree under test and the **exact** tree asserted per subprocess (trap T6) |
| **Date** | 2026-09-01 |
| **Status** | Complete — **the gate passes on all four scenarios** |

**Vocabulary, once.** A *sweep* is one execution of `Caller._call_models_once`, i.e. one pass over
the model sequence. A *node* is one model entry point that `_call_models_once` calls directly. The
*executing sequence* is the list of nodes a given input deck actually reaches, in order, measured
at run time — not the 26 `.run()` call sites visible in the source, because the toroidal-field-coil
branch and the blanket branch are selected by switches in the deck. *Bit-identical* means every
line of the MFILE matches and every float in it matches as a hex literal, with **no tolerance
applied anywhere**.

---

## 1. Verdict

**The reorder is exactly result-neutral, on all four scenarios, and the dependency graph's
prediction holds.** `build.run()` was moved from sequence position 2 to position 3 — out of M1
(Physics)' span and to the head of M2 (Coils)' span — and:

| | |
|---|---|
| MFILE lines differing, against the parent commit | **0** of 16 174 / 16 435 / 18 692 / 15 917 |
| MFILE floats differing, compared as hex literals | **0** of 13 559 / 13 455 / 13 493 / 13 487 |
| `ifail` | **1** on all four, in every arm |
| sweeps per solve | **unchanged**: 2029 / 4286 / 1891 / 29 |
| executing node calls per sweep | **unchanged**: 21 on all four |

**M1 is now contiguous.** The executing sequence is `plasma_geom, physics` (M1), then `build,
<TF turn model>, pfcoil` (M2), then `pulse`, then M3, then the feed-forward tail. Nothing else
moved. Phase B's per-module solvers (A5 / F10) are no longer blocked by the interleaving.

**The default path is byte-identical too.** The reorder is a *selection*, not an edit: the call
order is a list the caller walks, and with `PROCESS_ARCH_SEQUENCE` unset that list is the upstream
order. Default-path output against the parent commit is 0 differing lines and 0 differing floats
on all four scenarios, checked separately from the reorder gate.

**The gate was shown to be capable of failing** before its zeros were believed — §5.

---

## 2. What changed

One file: `process/core/caller.py`, which is on `CLAUDE.md`'s default-permitted surface. **Nothing
under `process/models/` was touched**, so decision D11's model-edit approval gate does not apply.

The three straight-line calls

```python
self.models.plasma_geom.run()
self.models.build.run()
self.models.physics.run()
```

became a module-level list and a loop over it:

```python
_SEQUENCE_HEADS = {
    "upstream":            ("plasma_geom", "build", "physics"),
    "build_after_physics": ("plasma_geom", "physics", "build"),
}
SEQUENCE_NAME = os.environ.get("PROCESS_ARCH_SEQUENCE", "").strip() or "upstream"
SEQUENCE_HEAD = _SEQUENCE_HEADS[SEQUENCE_NAME]      # unrecognised value raises
...
for _node in SEQUENCE_HEAD:
    getattr(self.models, _node).run()
```

**Why only these three nodes are in the list.** They are the whole of what VP1 currently varies,
they are adjacent, and they are the only unconditional calls at the head of the tokamak sequence.
Everything after them is switch-selected on the deck and is left exactly as upstream wrote it. This
is a permutation of three calls with an index resolved once at import — the framework document's
§5.1 records over-building as a live risk and the user has required the framework be minimal, so
there is no scheduler here and no `PROCESS_ARCH` composition parser (which the 2026-09-01
minimisation audit cut for Phase A).

An unrecognised `PROCESS_ARCH_SEQUENCE` raises at import rather than falling back to a default —
verified: `PROCESS_ARCH_SEQUENCE=nonsense` raises `RuntimeError` naming the two valid values. An
empty value resolves to `upstream`.

Instruments added under `arch_surgery/`, which change no PROCESS code:

| File | What it does |
|---|---|
| `arch_surgery/idf_probe/a3_sequence_census.py` | measures the executing sequence at run time by wrapping the models' bound entry points from outside |
| `arch_surgery/idf_probe/run_a3.py` | the 3-arm × 4-scenario × 2-probe-mode run matrix, one isolated subprocess per run |
| `arch_surgery/idf_probe/compare_a3.py` | the bit-comparison |
| `arch_surgery/idf_probe/a3_gate_sensitivity.py` | proves the comparison can fail (§5) |

Four lines were added to `arch_surgery/idf_probe/run_one.py` so every run records which sequence
the tree it imported actually resolved — read from the imported module, not from the environment
variable, so a run against a tree that predates the variant point says `null` instead of silently
reporting the arm the driver asked for.

---

## 3. The executing sequence, before and after

Measured at run time on each deck, not read from source. The instrument wraps each model object's
bound entry point and records only calls made at nesting depth 0 **inside** the window
`Caller._call_models_once` opens and closes.

**Trap T7 is handled structurally, not by a name filter.** Ten model objects call their own `run()`
from inside their `output()` method during the final output idempotence check. Closing the window
at the `_call_models_once` boundary puts that traffic outside it: **33 such calls per run** on every
scenario and in every arm, from eleven objects (the ten T7 names, plus `physics_detailed`, which
`_call_models_once` never calls at all). They are reported separately and are never counted as
sequence.

**Before** (`parent`, and `default` — identical, verified position by position):

| # | node | module |
|---|---|---|
| 1 | `plasma_geom` | M1 |
| **2** | **`build`** | **M2 — misplaced** |
| 3 | `physics` | M1 |
| 4 | `cicc_sctfcoil` (`croco_sctfcoil` on `st_regression`) | M2 |
| 5 | `pfcoil` | M2 |
| 6 | `pulse` | articulation point |
| 7–18 | `divertor`, `fw`, `shield`, `vacuum_vessel`, `ccfe_hcpb`, `cryostat`, `structure`, `power`, `vacuum`, `buildings`, `power.acpow`, `power.plant_electric_production` | M3 |
| 19 | `availability` | M3 |
| 20–21 | `water_use`, `costs` | feed-forward |

**After** (`reordered`): identical except that `build` moves from index 1 to index 2 (0-based) —
`plasma_geom, physics, build, …`. The two sequences differ in that one transposition and nothing
else; this was checked as a list equality per scenario, not by eye.

21 nodes execute per sweep on all four decks, out of 26 `.run()` call sites in `caller.py`. Exactly
one order occurs per scenario (`distinct_sweep_orders = 1` over 2029 / 4286 / 1891 / 29 sweeps), so
"the sequence" is well defined here rather than being a first-sweep sample.

---

## 4. The gate

Six PROCESS runs plus three census runs per scenario, 36 runs in total, all `rc = 0`. Each is a
fresh subprocess in its own working directory — `OutputFileManager` holds file handles as class
attributes and initialisation mutates a global data structure, so two runs in one process
contaminate each other. `PYTHONPATH` was set to the tree under test for every run, and each run
asserted `process.__file__` resolved to that **exact** tree (trap T6: a prefix test passes for the
main checkout as well, and the editable install points there).

**Arms.** `parent` is a `git archive` extraction of `c9cc917f` — the branch's parent commit, in
which `PROCESS_ARCH_SEQUENCE` does not exist in the code at all. `default` is this branch with the
variable unset. `reordered` is this branch with `PROCESS_ARCH_SEQUENCE=build_after_physics`. Each
was run once with the probe switch unset (the arm the MFILE comparison uses) and once with
`PROCESS_IDF_PROBE=baseline` (where the sweep counts come from).

**What is compared, and the denominators.** Three independent comparisons per arm pair:

1. **Whole MFILE, line by line.** `ovarre` writes floats as `f"{v:.17e}"` — 18 significant decimal
   digits, which round-trips an IEEE-754 double exactly, so an identical line is an identical
   double. Ten run-metadata keys are excluded by name — `date`, `time`, `username`, `computer`,
   `directory`, `fileprefix`, `tagno`, `branch_name`, `commsg`, `process_runtime` — because they
   are provenance, not results, and differ between any two runs of identical code. Nothing else is
   excluded.
2. **Every MFILE float, re-parsed and compared as a hex float literal.** Same content read a second
   way. On `large_tokamak_nof`: 16 174 non-volatile lines, of which 13 614 carry a variable name and
   13 559 have a value that parses as a float. The 55 named-but-not-float lines are string-valued
   variables and are covered by comparison (1).
3. **The in-memory exact signature** from `metrics.json` — `norm_objf`, `sqsumsq`, `conf_l2` and the
   iteration-variable vectors, as hex floats (4 signature fields plus 5–23 raw MFILE fields).

Iteration variables appear here only inside a *bit-identity* test. D6's prohibition is on gating
**correctness** on them across a changed driver, which is not what this is.

### Gate — `reordered` vs `parent`: **PASS 4/4**

| Scenario | MFILE lines compared | lines differing | MFILE floats compared | floats differing | signature fields compared | differing | total quantities compared | `ifail` (both arms) | sweeps (both) | node calls/sweep (both) |
|---|---|---|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 16 174 | **0** | 13 559 | **0** | 27 | **0** | 29 760 | 1 | 2029 | 21 |
| `low_aspect_ratio_DEMO` | 16 435 | **0** | 13 455 | **0** | 26 | **0** | 29 916 | 1 | 4286 | 21 |
| `st_regression` | 18 692 | **0** | 13 493 | **0** | 21 | **0** | 32 206 | 1 | 1891 | 21 |
| `large_tokamak_eval` | 15 917 | **0** | 13 487 | **0** | 9 | **0** | 29 413 | 1 | 29 | 21 |

No scenario is pooled with another; each row is one deck.

### Default-path neutrality — `default` vs `parent`: **PASS 4/4**

Identical numbers, column for column, to the table above. The VP1 list with the variable unset
reproduces the three straight-line calls it replaced, bit for bit, and its recorded resolved order
is `("plasma_geom", "build", "physics")` on every run.

### Probe-on arm — `reordered_probe` vs `parent_probe`: **PASS 4/4**

Also identical, column for column. The reorder is neutral with the probe on as well as off, so
the two switches do not interact.

### Counts

| Scenario | sweeps: `parent` / `default` / `reordered` | `call_models` | model calls (PROCESS's own counter) | solver iterations | depth-0 node calls in sweeps |
|---|---|---|---|---|---|
| `large_tokamak_nof` | 2029 / 2029 / 2029 | 630 | 2029 | 8 | 42 609 |
| `low_aspect_ratio_DEMO` | 4286 / 4286 / 4286 | 1240 | 4286 | 16 | 90 006 |
| `st_regression` | 1891 / 1891 / 1891 | 570 | 1891 | 10 | 39 711 |
| `large_tokamak_eval` | 29 / 29 / 29 | 11 | 29 | 0 | 609 |

Per-node call counts (21 nodes per deck) are equal across all three arms, node by node, not merely
equal in total. The sweep counts reproduce A20's independently measured 2029 / 4286 / 1891 / 29,
and the MFILE line counts reproduce its 16 174 / 16 435 / 18 692 / 15 917.

**No timing is reported as evidence.** The 36-run matrix took 385 s wall clock in one repetition
under unknown machine load, which is context and nothing else.

---

## 5. The gate was shown to be capable of failing

Trap T11 records this project publishing a `0` three times without the condition that limits it,
and a gate that passes vacuously on an empty comparison set has happened here before. Two checks
were run so that the zeros above mean something.

**A different permutation breaks the run.** A scratch tree identical to this branch except that the
default order is `("physics", "plasma_geom", "build")` was built and run on `large_tokamak_eval`
and `large_tokamak_nof`. Both **crash** with `ZeroDivisionError` in
`calculate_cylindrical_safety_factor`. So the list genuinely drives the call order, these three
calls are order-sensitive in general, and the passing result is not the loop quietly failing to
take effect. That control produces no MFILE, so it does not exercise the comparator; the next one
does.

**The comparator detects one unit in the last place.** `large_tokamak_nof`'s `parent` MFILE was
copied and the value of `rmajor` advanced by one ULP — `0x1.000000001315cp+3` →
`0x1.000000001315dp+3`, a relative change of `2.22e-16`, invisible at any printed-decimal
resolution below 17 digits. The unmodified comparator reports **FAIL**, with **1** differing line
out of 16 174 and **1** differing float out of 13 559, naming `rmajor`.

**And on two genuinely different solves.** `large_tokamak_nof`'s MFILE against
`low_aspect_ratio_DEMO`'s: 11 606 of 13 441 shared floats differ.

A defect in the comparator was found and fixed by the first of these. Its original line parser
anchored on the first `(...)` in a line, but MFILE descriptions routinely contain parentheses —
`Major_radius_(R0)_(m)____ (rmajor)____ 8.00e+00` — so such lines were parsed as a variable named
`R0` with an unparseable value and were **silently dropped from the float comparison**. It
understated the float denominator by about 1 000 per scenario (12 550 rather than 13 559 on
`large_tokamak_nof`). The whole-line comparison was never affected, and the verdict does not
change; the denominators in §4 are the corrected ones. This is worth recording because the failure
mode was exactly T11's: a mismatch count of 0 over a population quietly smaller than the one named.

---

## 6. What this says about the dependency graph

The partition plan §1.3 predicted this result from a static reading: `build.py` reads seven
`physics` attributes and every one is written by `plasma_geometry.py`, M1's *first* node; in the
other direction the physics package reads only `dr_fw_plasma_gap_inboard/_outboard` from `build`,
also written by `plasma_geometry.py`. So moving `build` across `physics` should change nothing.

**It changes nothing, on 121 295 compared quantities across four decks** (29 760 + 29 916 +
32 206 + 29 413, summed here only to size the evidence — the gate is judged per deck). The
prediction is now
measured rather than argued. Recorded as **V9** in
[`DSM_VALIDATION.md`](DSM_VALIDATION.md), which accumulates and is never archived.

The converse is worth stating plainly, because it is the limit of this result: a bit-identical
outcome shows there is no *live* edge from anything between `build`'s old and new positions into
`build`, **on these four decks**. It does not show that no such edge exists structurally, and it
does not transfer to a deck that resolves different switches. That is the same scope limit V6
places on the module boundaries themselves.

---

## 7. Autonomous decisions, and how to reverse each

| # | Decision | Why | Reversal |
|---|---|---|---|
| 1 | **Branch created at `c9cc917f`, not at the worktree's seed commit.** The worktree was seeded at `6df46205` — upstream `main`, with no `arch_surgery/` directory present at all. This is issue **I-11** recurring, on a second task. Detected before the first commit, as the brief required. | Working from upstream `main` would have produced a plausible-looking diff against the wrong base and no `arch_surgery/` to report into | Nothing to reverse; recorded here so the recurrence is counted |
| 2 | **Data-driven sequence rather than a direct edit**, as the brief preferred, but scoped to the three-node head only | Makes the order a driver choice with the upstream order as default, so the baseline arm survives; scoping it to three nodes keeps it a list and an index rather than a scheduler | Replace the loop with the three straight-line calls in the moved order; delete `_SEQUENCE_HEADS`, `SEQUENCE_NAME`, `SEQUENCE_HEAD` and the `os` import |
| 3 | **A dedicated environment variable `PROCESS_ARCH_SEQUENCE`, not `PROCESS_ARCH=seq:…`** | The framework's `PROCESS_ARCH` composition parser (C1) was cut for Phase A by the minimisation audit; half-implementing it here would build the thing that was cut. The switch lives inside `caller.py`, so the change stays within one file on the default-permitted surface and adds no new module to `process/core/` | Rename the variable, or fold it into `_experiment.py` when F1 consolidates. The two valid values are the dict keys and are the only external contract |
| 4 | **The variant is named `build_after_physics`, not `dsm`** | `PROCESS_ARCH=seq:dsm` in the framework document means the full DSM-sequenced order, which is A15 and is deferred. This is one transposition, and naming it `dsm` would claim more than was done | Rename the dict key |
| 5 | **An unrecognised value raises instead of defaulting** | A typo'd arm name that silently ran the baseline would produce a plausible wrong result — the same class of failure as I-11 and the `PROCESS_env` hazard | Change the `raise` to a fallback; not recommended |
| 6 | **The run-time sequence census is an external instrument, not a new probe mode** | Adding a probe mode is a PROCESS change needing its own neutrality gate, and the framework forbids adding hooks ad hoc. Wrapping the models' bound methods from outside is what A19's replay harness already does | Delete `a3_sequence_census.py`; nothing depends on it |
| 7 | **Four lines added to `run_one.py`** recording the resolved sequence | A run that cannot say which arm produced it is not a result. Read from the imported module rather than the environment so a pre-variant tree reports `null` rather than the arm that was asked for | Revert those lines; the gate does not depend on them |
| 8 | **A `V9` entry added to `DSM_VALIDATION.md`** | That register is the stated deliverable back to the dependency-analysis study, and this is a DSM prediction tested against measurement. V3 and V4 are already confirmation-shaped entries | Delete the entry |

---

## 8. What I did not do

- **Did not merge and did not push.** The branch `A3-build-reorder` is left for review.
- **Did not touch `process/models/`.** No D11 approval was needed and none was sought. The reorder
  required no model edit.
- **Did not implement VP1 beyond these three nodes.** The rest of the sequence is still hardcoded,
  including the switch-selected branches. A15 (dsm-sequencing), which would make the whole order
  data, is deferred.
- **Did not build the `PROCESS_ARCH` arm-composition parser**, the `in_loop`, `converged` or
  `solve_blocks` hooks, or anything else from the framework's variant-point table. No queued task
  consumes them yet.
- **Did not change the default.** With `PROCESS_ARCH_SEQUENCE` unset, PROCESS runs the upstream
  order. Nothing downstream of this branch sees a different sequence unless it asks for one.
- **Did not measure whether the reorder is faster.** It cannot be: the sweep counts and the
  per-node call counts are identical, so there is no less work to do. This task is a graph-integrity
  check and an enabler for A5/F10, not a performance change.
- **Did not run the reorder against decks outside the four scenarios**, so §6's scope limit stands.
- **Did not re-derive the DSM** or read the sibling repository's generated output (trap T9). The
  module assignment comes from this repository's committed `arch_surgery/docs/data/dsm_node_map.json`.
- **Did not commit run artifacts.** `arch_surgery/idf_probe/runs_a3/` is untracked, per the standing
  rule; the summaries and verdicts are in this report and in the committed scripts that reproduce
  them.

---

## 9. Reproducing it

```
SP=<scratch>                      # anywhere writable outside the repo
mkdir -p $SP/parent_c9cc917f
git archive c9cc917f | tar -x -C $SP/parent_c9cc917f

cd arch_surgery/idf_probe
/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python run_a3.py \
    --parent-tree $SP/parent_c9cc917f
/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python compare_a3.py
/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python a3_gate_sensitivity.py
```

Verdicts land in `runs_a3/_gates_a3.json` and `runs_a3/_gate_sensitivity.json`.

---

## Change log

| Date | Entry |
|---|---|
| 2026-09-01 | Branch created at `c9cc917f` after the worktree was found to be seeded at upstream `main` (I-11, second occurrence). VP1/F7a implemented in `caller.py` as a three-node sequence list with the upstream order as default. Gate matrix run: 36 isolated subprocesses, 3 arms × 4 scenarios × 2 probe modes plus 12 sequence-census runs, all `rc = 0`. Reorder gate and default-path neutrality both PASS 4/4, 0 differing MFILE lines and 0 differing floats on every scenario, `ifail = 1` throughout, sweep and per-node call counts unchanged. Gate sensitivity demonstrated at 1 ULP; a comparator defect found in the process and fixed, with the corrected denominators used throughout. `V9` appended to `DSM_VALIDATION.md`. |
