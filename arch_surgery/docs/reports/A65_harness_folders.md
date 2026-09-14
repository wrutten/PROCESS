# A65 (harness-folders) — the harness's flat modules, grouped into five subpackages

> **Document status** — **OPEN.** Task **A65 (harness-folders)**, branch `A65-harness-folders`, off
> `architecture_surgery` at `486fa9ad` (the tip after A64 (entry-pairing-reference) merged).
> A pure move: no behaviour, no `records.SCHEMA` field, no gate name, no stage name and no value in
> `config.py` changes. Folder position records lifecycle, not validity (trap T3).

---

## 1. Verdict

`harness/`'s forty flat modules are now five subpackages — `core/`, `experiment/`, `child/`,
`gates/`, `measurement/` — grouped by **who imports them and when they run**, with `__init__.py`,
`chain.py`, `ystate.py`, `data/` and `reference/` left at the top. Thirty-eight modules moved by
`git mv`; **the only non-move edits are import statements, four `__file__`-derived path anchors, the
child spawn path, path spellings in prose, and one constant list of dotted module names that a gate
parses** (§4). `--selfcheck` **7/7 PASS**; `--gate all --resume` **25 gates PASS, 147/147 teeth**;
`--measure all --resume` re-made **0** runs. Gate **G1** (`switch_neutrality`) straddles
`fd480aff -> 61473c1d` and passes over kept records: 6 pairs, **2 831 record values and 51 319
output-file lines compared, 0 differing** — with every architecture switch unset the tree behaves
byte-identically to the tree before the move.

**`ystate.py` could not move, and this needs no decision but does need to be known.** The experiment's
copied driver reaches it by the literal path
`Path(__file__).resolve().parents[4] / "harness" / "ystate.py"`
(`PROCESS/process/core/solver/module_solve.py:502`), and `PROCESS/copy_gates.py:167` asserts that
literal as one of the copy's permitted edits. Moving the file into `child/` would mean editing the
frozen copy. It stays where the driver expects it, and `harness/child/__init__.py` and
`harness/README.md` §10.1 both say that it belongs to the `child/` set for the purpose of the rule
that set exists to make visible.

**The press re-made 16 of 178 run records, and none of them because of this change** (§6). Twelve are
gate G4's doctored runs, which `gate_audit.py:419` asks for with `resume=False` on every press by
design; one is gate G7's own tooth, which runs a job with and without `--resume` to prove the flag
reaches the runs; three are the `entry=optimisation` census records, which the seed carries in the
older `census-1` shape with 13 of 14 declared provenance fields and which `--resume` therefore
refuses — a property of the seeded records, not of this task. `records.py` is **byte-identical** to
`architecture_surgery` and `census.py` differs from it in nothing but its imports and one path anchor.

**`--plan-tables check` reports 137 differing lines and exits 3** (§7). 133 of them are one commit
added to a caption's list of the commits its records were made at; one is this task's rename of the
renderer in its own provenance sentence; three are consequences of the three re-taken censuses. No
cell's value changed except those three. The plan's §4 should be re-rendered at the merged tip, as
A64 did at its merge — this task deliberately did not write it.

---

## 2. What moved, module by module

*Caption: one row per module of `arch_surgery/MDA_partitioning_experiment_v4/harness/`. Every move is
a `git mv`, so `git log --follow` and `git blame` carry through. Population: the 38 modules that moved
plus the three modules and two directories that did not; no module was renamed, added or deleted. Detected as renames by
`git diff -M`: 38 of 38.*

| module | from | to |
|---|---|---|
| `framework` | `harness/framework.py` | `harness/core/framework.py` |
| `config` | `harness/config.py` | `harness/core/config.py` |
| `failure` | `harness/failure.py` | `harness/core/failure.py` |
| `provenance` | `harness/provenance.py` | `harness/core/provenance.py` |
| `records` | `harness/records.py` | `harness/core/records.py` |
| `pool` | `harness/pool.py` | `harness/core/pool.py` |
| `arms` | `harness/arms.py` | `harness/experiment/arms.py` |
| `switches` | `harness/switches.py` | `harness/experiment/switches.py` |
| `input_files` | `harness/input_files.py` | `harness/experiment/input_files.py` |
| `artifacts` | `harness/artifacts.py` | `harness/experiment/artifacts.py` |
| `data_provenance` | `harness/data_provenance.py` | `harness/experiment/data_provenance.py` |
| `child` | `harness/child.py` | `harness/child/child.py` |
| `evaluate` | `harness/evaluate.py` | `harness/child/evaluate.py` |
| `optimise` | `harness/optimise.py` | `harness/child/optimise.py` |
| `predicate` | `harness/predicate.py` | `harness/child/predicate.py` |
| `perturb` | `harness/perturb.py` | `harness/child/perturb.py` |
| `data_structure` | `harness/data_structure.py` | `harness/child/data_structure.py` |
| `audit_map` | `harness/audit_map.py` | `harness/child/audit_map.py` |
| `census` | `harness/census.py` | `harness/child/census.py` |
| `postsolve` | `harness/postsolve.py` | `harness/child/postsolve.py` |
| `gates` | `harness/gates.py` | `harness/gates/gates.py` |
| `gate_audit` | `harness/gate_audit.py` | `harness/gates/gate_audit.py` |
| `gate_composition` | `harness/gate_composition.py` | `harness/gates/gate_composition.py` |
| `gate_entry` | `harness/gate_entry.py` | `harness/gates/gate_entry.py` |
| `gate_prime` | `harness/gate_prime.py` | `harness/gates/gate_prime.py` |
| `gate_records` | `harness/gate_records.py` | `harness/gates/gate_records.py` |
| `gate_tally` | `harness/gate_tally.py` | `harness/gates/gate_tally.py` |
| `reproduction` | `harness/reproduction.py` | `harness/gates/reproduction.py` |
| `reference` | `harness/reference.py` | `harness/gates/reference.py` |
| `selfcheck` | `harness/selfcheck.py` | `harness/gates/selfcheck.py` |
| `exit_audit_diagnosis` | `harness/exit_audit_diagnosis.py` | `harness/gates/exit_audit_diagnosis.py` |
| `tally` | `harness/tally.py` | `harness/measurement/tally.py` |
| `tally_evaluation` | `harness/tally_evaluation.py` | `harness/measurement/tally_evaluation.py` |
| `tally_optimisation` | `harness/tally_optimisation.py` | `harness/measurement/tally_optimisation.py` |
| `stats` | `harness/stats.py` | `harness/measurement/stats.py` |
| `tables` | `harness/tables.py` | `harness/measurement/tables.py` |
| `analysis` | `harness/analysis.py` | `harness/measurement/analysis.py` |
| `plan_tables` | `harness/plan_tables.py` | `harness/measurement/plan_tables.py` |
| `__init__` | `harness/__init__.py` | **unchanged** — the one public import surface |
| `chain` | `harness/chain.py` | **unchanged** — the sequence the campaign and the smoke both run |
| `ystate` | `harness/ystate.py` | **unchanged** — see §3 |
| *(data)* | `harness/data/` | **unchanged** |
| *(reference)* | `harness/reference/` | **unchanged** — the committed reproduction reference |

Five new files: `core/__init__.py`, `experiment/__init__.py`, `child/__init__.py`,
`gates/__init__.py`, `measurement/__init__.py`. Each is a docstring and nothing else — no re-exports,
so no new import edge and no new cycle. The package's public surface is still `harness/__init__.py`.

---

## 3. `ystate.py`, and why the grouping has one member outside its directory

The approved grouping puts `ystate` in `child/`. It is not there.

`arch_surgery/MDA_partitioning_experiment_v4/PROCESS/process/core/solver/module_solve.py` holds

```python
YSTATE_MODULE_PATH = (
    Path(__file__).resolve().parents[4]
    / "harness"
    / "ystate.py"
)
```

and loads that file by `importlib.util.spec_from_file_location` on the partitioned path. The literal
is one of the copy's three declared path constants (harness plan §3.3, ruling D20 decision (2), option
(v)), and `PROCESS/copy_gates.py:167` asserts its exact text as a permitted edit of the frozen copy.
So moving `ystate.py` requires editing a file under `PROCESS/`, which this task may not do and which
gate G0′ exists to refuse.

**What was done instead.** `ystate.py` stays at the top of the package. `harness/child/__init__.py`
states that it belongs to the `child/` set and why it is not in the directory;
`harness/README.md` §10.1 states the same for a reader.

**The reversal**, if the user wants the file in `child/`: re-point `YSTATE_MODULE_PATH` to
`parents[4] / "harness" / "child" / "ystate.py"`, update the matching `now=` literal in
`copy_gates.py`'s permitted-edit record, and re-run G0′ and GR. That is a driver-copy change and needs
the user's approval; it is not something a folder task may take on its own.

---

## 4. Every non-move edit, by kind

*Caption: one row per kind of edit, with the count of lines and the files. Population: the complete
content diff of the two commits, `git diff -M 486fa9ad..HEAD`, minus the pure renames. No other kind
of edit exists in this branch.*

| kind | where | what |
|---|---|---|
| **relative imports** | 23 modules, `__init__.py`, `chain.py` | `from . import records` → `from ..core import records`; `from .config import Campaign` → `from ..core.config import Campaign`; at the top level `from .arms import …` → `from .experiment.arms import …`. `from . import __version__` in `child/child.py` → `from .. import …` |
| **absolute imports** | 12 modules and `experiment_runner.py` | `from harness import records as records_mod` → `from harness.core import records as records_mod`; `from harness.config import Campaign` → `from harness.core.config import Campaign`. The three names that stayed at the top level — `chain`, `ystate`, and the public surface `harness` itself — keep their spelling |
| **the child spawn path** | `core/pool.py` | `ENTRY_POINT` keeps its three file names; a new `CHILD_DIR = Path(__file__).resolve().parent.parent / "child"` names the directory, and `_command` builds `CHILD_DIR / ENTRY_POINT[phase]`. The absolute path in each run's `command.json` therefore gains one `child/` segment; nothing reads it back |
| **`__file__` anchors** | `core/config.py` (`HERE`), `core/framework.py` (`git_head`), `experiment/data_provenance.py` (`HERE`, `_EXPERIMENT_DIR`), `gates/reference.py` (`HERE`, `_EXPERIMENT_DIR`), `gates/gates.py` (`_EXPERIMENT_DIR`, `self_containment`'s `here`), `gates/selfcheck.py` and `gates/reproduction.py` (`_EXPERIMENT_DIR`), `child/evaluate.py`, `child/optimise.py`, `child/census.py` (`_EXPERIMENT_DIR`) | each gains the one directory level the module gained. In the three child entry points `_HERE` deliberately stays **the script's own directory**, because it is compared against `sys.path[0]`, which Python sets to the script's directory |
| **a gate's own data** | `measurement/analysis.py` | `FORBIDDEN_IMPORTS` — the five dotted module names the independence gate forbids this module to import — and the two source fixtures its tooth feeds to the same scanner. Left flat, they would have matched nothing and the gate would have passed vacuously. This is the one edit that is not cosmetic, and the gate's tooth is what proves it still bites: it names `['harness.measurement.stats', 'harness.measurement.stats.median', 'harness.measurement.tables', 'harness.measurement.tally_optimisation']` |
| **`python -m` usage lines** | `gates/gates.py` (11), `gates/exit_audit_diagnosis.py` (4) | `python -m harness.gates …` → `python -m harness.gates.gates …`; `-m harness.exit_audit_diagnosis` → `-m harness.gates.exit_audit_diagnosis` |
| **prose file paths** | 19 modules, `experiment_runner.py`, `harness/README.md` (6), the harness plan outside its change log (20) | `` `harness/<module>.py` `` → `` `harness/<group>/<module>.py` `` |
| **cross-references** | 9 modules | `:func:`harness.records.is_complete_for`` → `:func:`harness.core.records.is_complete_for``, and the same for `config`, `framework`, `stats`, `reference`, `pool`, `child`, `gates.registry` |
| **documentation** | `harness/README.md` | §10 rewritten in the new paths, and a new **§10.1 The package layout** — the five directories, what each holds, who imports it, and the rule that makes the grouping worth having |
| **new** | `MDA_partitioning_experiment_v4/run_stamp_survey.py` | the stamp survey of §6, as a committed script (protocol §15) |

### 4.1 Three strings that deliberately keep their flat spelling

| string | module | why it was not rewritten |
|---|---|---|
| `"generated_by": "harness/data_provenance.py copy"` | `experiment/data_provenance.py:790` | it is written into `harness/data/PROVENANCE.json`, a **committed** artifact whose bytes the data gate compares. Changing the code string would make a future `record --force` disagree with the committed file |
| `"written_by": "harness/reference.py (task A49 …)"` | `gates/reference.py:781` | it is written into the committed `harness/reference/reproduction_reference.json`, and `--reference verify` requires the re-derivation to equal that file **byte for byte** |
| `"generated_by": "harness/postsolve.py"` | `child/postsolve.py:954` | it is stamped into the derived per-run artifact that is compared with the committed one |

Each of the three is a *value in a record*, not an import or a path anything resolves. Rewriting them
is a one-line change in each module plus a regeneration of the artifact that carries them, which is a
data change and not a folder change. **A reader of those three records must translate the path.**

### 4.2 No circular import appeared

The regrouping introduced none: every one of the 46 Python files of the package imports cleanly, in
isolation, from a directory that is not the package (§8, check C). The lazy in-function imports that
already existed to break cycles were re-pointed and left in place; none was added and none was moved
between groups.

**When the verification ran.** Every press below ran at `61473c1d`, with the working tree clean and
nothing else executing. The one commit after it, `6441d3c5`, adds this report and no code: no module
a gate or a measurement child imports differs between the commit the records were made at and the
branch tip.

---

## 5. `--selfcheck` — 7 of 7

*Caption: one row per self-check, at commit `61473c1d` (the branch tip at the time of the press).
Population: the seven checks the suite declares; none is skipped. No PROCESS run.*

| check | verdict |
|---|---|
| composition | **PASS** |
| rungs | **PASS** |
| capability | **PASS** |
| provenance | **PASS** |
| data | **PASS** |
| run path | **PASS** (9 compared, 0 mismatched) |
| stage provenance | **PASS** (17 compared, 0 mismatched) |
| **overall** | **PASS** |

---

## 6. `--gate all --resume` — 25 gates PASS, 147/147 teeth, and the 16 runs that were re-made

Pressed once, at `61473c1d`, from the worktree's repository root, in a tree seeded with A64's
relocated gate records.

*Caption: one row per registered gate, in the order the dependency-derived press ran them.
Population: the 25 gates the registry holds; every one ran. Teeth are counted over all gates
together, as the press reports them.*

| gates pressed | PASS | FAIL | teeth tripped |
|---|---|---|---|
| 25 | **25** | 0 | **147 / 147** |

`g0prime`, `composition`, `rungs`, `provenance`, `data`, `run_path`, `capability`,
`artifacts_check`, `artifacts_derive_inputs`, `artifacts_census`, `artifacts_per_run`,
`record_completeness`, `prime_map`, `cold_chain`, `audit_restriction`, `entry_and_warm`,
`switch_composition`, `switch_neutrality`, `reproduction`, `output_path`, `predicate_mode`,
`tally_contracts`, `recomputation`, `run_kind_separation`, `stage_provenance` — all **PASS**.

Each verdict states the commit of the records it read. The three that carry the largest populations:

| gate | runs read | commits |
|---|---|---|
| `recomputation` | 36 record(s), 2 066 compared, 0 mismatched | 33 at `f8bce151`, 3 at `7ad8ea04` *(resumed)* |
| `run_kind_separation` | 36 record(s), 209 compared, 0 mismatched | 33 at `f8bce151`, 3 at `7ad8ea04` *(resumed)* |
| `audit_restriction` | 21 record(s), 12 compared, 0 mismatched | 12 at `61473c1d`, 9 at `f8bce151` *(resumed)* |

### 6.1 The stamp surveys

Produced by `run_stamp_survey.py`, committed at `61473c1d`, which reads `tree_git_head` out of every
`metrics.json` under `runs/` and diffs two surveys record by record (trap T13: the record is the only
thing that may say whether a run was kept).

*Caption: the same 178 run records before and after one `--gate all --resume` press. A record with no
top-level `tree_git_head` is reported as such, not as `None`, because a provenance block one level
down is invisible to a top-level survey (I-22 (b), trap T14).*

| commit | before the press | after the press |
|---|---|---|
| `3d64625c` | 11 | 11 |
| `47be2b0d` | 3 | 3 |
| `61473c1d` *(this branch)* | 0 | **16** |
| `7ad8ea04` | 3 | 3 |
| `b784158c` | 12 | 12 |
| `f8bce151` | 140 | 127 |
| `fd480aff` | 6 | 6 |
| *no top-level stamp* | 3 | 0 |
| **total** | **178** | **178** |

`records whose commit changed: 16 · records that disappeared: 0 · records that are new: 0`.

### 6.2 Each of the 16, and why

*Caption: one row per group of re-made records, with the mechanism that re-made it and the evidence
that the mechanism is not this task's. Population: the 16 records the survey named; every one is
accounted for.*

| n | records | why | not this task, because |
|---|---|---|---|
| **12** | `gates/audit_restriction/<configuration>/{in_loop,per_run_costs,per_run_vacuum,per_run_water_use}` | gate G4's **doctored** runs. `gate_audit.py:419` calls `pool_mod.run_all(…, resume=False)` for them: the doctored entry state is written fresh outside the run directory before each run, so a kept record would be a record of a *different* doctoring | the line is unchanged by this branch — `gate_audit.py` differs from `architecture_surgery` in nothing but seven import lines (`git diff` in §8, check D). These twelve are re-made by every press of this gate, at every commit |
| **3** | `census/<configuration>/optimisation/metrics.json` | the seeded records are in the older `census-1` shape and carry **13 of 14** declared provenance fields, so `--resume` refuses them by name and the census is re-taken | the seed's own copies — `arch_surgery/idf_probe/runs/A64_runs/census/*/optimisation/metrics.json` in the main checkout — carry `provenance.tree_git_head = 3347169c` and no top-level stamp. `records.py` is **byte-identical** to `architecture_surgery`; `census.py` differs in seven import lines and one `_EXPERIMENT_DIR` anchor, and in no declared provenance field |
| **1** | `gates/record_completeness/st_regression/evaluation/metrics.json` | gate G7's own tooth *"a stale run is re-made without `--resume`"* asks for one job twice — with `--resume`, where the record must be kept, and without, where it must be re-made (`gate_records.py:400–402`). The re-made record is what the tooth leaves behind | the tooth is unchanged by this branch, and it is the tooth that proves `--resume` reaches the runs at all |

**So: zero runs were re-made because a module moved.** Three were re-made because the seeded census
records predate the census provenance contract; thirteen are re-made by two gates on every press, by
design.

---

## 7. `--measure all --resume`, and `--plan-tables check`

`--measure all --resume`: every one of the nine measurement stages produced its record; **0** runs
re-made (the stamp survey against the post-gate survey: *records whose commit changed: 0, disappeared:
0, new: 0*).

One measured number moved, and it is the one that had to:

| stage | before | now | why |
|---|---|---|---|
| `self_containment` | 42 Python files scanned | **47** | the five subpackage `__init__.py` files. 44 lines name one of the two superseded directories, 31 in prose, 13 executable, **0 imports of either directory, 0 unclassified findings** — unchanged |

`--plan-tables check` **exits 3**: 131 tables, 3 927 cells, 1 792 lines rendered against 1 792 in the
document, **137 differing**. Classified line by line, by word-level diff:

*Caption: one row per kind of difference between the committed §4 of `EXPERIMENT_PLAN.md` and the
section rendered from the records now. Population: all 137 differing lines; every one is in exactly
one row.*

| n | difference | what it is |
|---|---|---|
| **133** | a caption's list of the commits its records were made at gains `` `61473c1d` `` | the press re-made 16 records at this commit, so every caption that names its population's commits names one more. No cell value changes on these lines |
| **1** | `` `harness/plan_tables.py` `` → `` `harness/measurement/plan_tables.py` `` | **this task's rename**, in the sentence where the renderer names itself |
| **1** | `switch_neutrality`'s straddle label `fd480aff -> d6f0fdf4` → `fd480aff -> 61473c1d` | the label names the verdict's own commit. **No capture was re-made**: the six after-side records were kept (6 at `b784158c`, resumed), and the gate compared 2 831 record values and 51 319 output-file lines with **0 differing** — the move is byte-neutral with every architecture switch unset |
| **1** | `artifacts_check`: `93` → `95` individual checks, 0 mismatched | two more artifact checks, because the three re-taken optimisation censuses became readable |
| **1** | `artifacts_census`: "one **evaluation** census each" → "one **optimisation** census each" | the same cause: the gate's population sentence is derived from the censuses it can read, and the optimisation censuses were refused by name before this press |

**Nothing was written.** The plan's §4 is rendered at the merged tip, as A64 did at its merge; this
branch leaves the document as it found it and states the diff here instead. A re-render at merge is
the T14 discipline, not an optional tidy: the committed §4 now describes verdicts that have been
re-made, and `--plan-tables check`'s exit 3 is that refusal working.

---

## 8. The checks that say nothing flat survived

*Caption: one row per check, with the command and its result. Population: the whole package
(46 Python files) plus `experiment_runner.py`, `harness/README.md` and the harness plan. Run from the
worktree's repository root at `61473c1d`.*

| # | check | result |
|---|---|---|
| A | `grep -rnPo "harness\.(?!core\|experiment\|child\|gates\|measurement\|chain\|ystate)[a-z_]+"` over `harness/` and the runner, `*.py` and `*.md` | **no matches** |
| B | `grep -rnE "from harness(\.[a-z_.]+)? import"` minus the five subpackages | 4 matches, all intended: `__init__.py`'s own usage example (`from harness import ARMS, …`), `experiment_runner.py:45` and `gates/gates.py:6093` (`from harness import chain`), `gates/gates.py:4556` (`from harness import ystate`) |
| C | every module of the package imported by name, from a directory that is not the package | **46 of 46 import; 0 failed** — strictly stronger than a grep for relative imports, since a wrong `..` resolves to a different package or to nothing |
| D | `harness/<module>.py` as a path spelling | 3 matches in the package — the three generator-stamped strings of §4.1 — and 8 in the harness plan's **change log**, which is a dated record of what each earlier task delivered and is not rewritten |

---

## 9. Autonomous decisions, each with its reversal

*Caption: one row per decision taken without asking, with what would undo it. Population: every
decision this task took that a reviewer could reasonably have taken differently.*

| decision | why | reversal |
|---|---|---|
| **`ystate.py` stays at the top level**, outside `child/` | moving it means editing `PROCESS/process/core/solver/module_solve.py` and `PROCESS/copy_gates.py`, which this task may not do | §3. A driver-copy change, needing the user's approval and a G0′ + GR re-run |
| **The subpackage `__init__.py` files re-export nothing** | a re-export would add an import edge that the flat layout did not have, and the package already has exactly one public surface | delete the five files' bodies' content or add `from .x import …` lines; nothing depends on their being empty |
| **The harness plan's Appendix A change log was not rewritten** | a dated entry recording what A52 or A53 delivered is a record of what was true then; rewriting its paths would falsify it | re-run the path rewrite without the line-range guard over lines 1140–1473 |
| **The three generator-stamped strings keep their flat spelling** | each is a value in a committed artifact whose bytes are what a gate compares | §4.1. Change the string and regenerate the artifact, in a task that owns that data |
| **`run_stamp_survey.py` was added** beside `PROCESS_diff.py` | protocol §15: the stamp survey is a published number and must come from a committed script, not a shell pipeline. Named for what it does, with no task number (§11.1) | delete it; the numbers of §6.1 would then have no committed derivation |
| **`--plan-tables` was not written** | the brief asks for the diff, and §4 belongs at the merged tip | `experiment_runner.py --plan-tables write` at the merge |

---

## 10. Limits — what a reader of an older document must translate

1. **Every report and plan written before this branch spells a harness module `harness/<module>.py`.**
   The map is §2. The harness plan has been updated outside its change log; the change log, the task
   reports in `docs/reports/deprecated/`, `MASTER_TODO.md` and the improvement list have **not**.
2. **`harness/data/PROVENANCE.json`, `harness/reference/reproduction_reference.json` and the derived
   per-run artifacts name three modules by their flat paths** (§4.1). Those are the files' recorded
   values, not stale prose: they will keep the old spelling until the data itself is regenerated.
3. **`self_containment`'s file count is 47 from this branch on**, not 42. A comparison with an
   earlier press must compare the *findings* (0, unchanged), not the denominator.
4. **`ystate.py` is in the `child/` set but not in the `child/` directory** (§3). Any statement of the
   form "the set amendment 13 rule (vi) forbids editing is `harness/child/`" must add it.
5. **A record's `command.json` now names the child entry point one directory deeper.** Nothing reads
   it back; `--resume` compares the record's fields, never a path.

---

## 11. What the queue and the improvement list should gain (not edited here)

- **`MASTER_TODO.md`**, row **A65**: MERGED, with the verification numbers of §5–§7, the ystate
  exception of §3 named, and the records' location once the worktree is retired.
- **The harness implementation plan**: an **amendment 22** at the merge, recording the layout, the
  rule it makes visible (`child/` *is* amendment 13 rule (vi)'s set), and the one member that could
  not move. §4.1's target tree is a 2026-09-10 record of the approved target and is left as it stands.
- **The improvement list**: nothing — this task adds no item. It removes one reading of the old one:
  "the harness is forty files in one directory" is no longer true.

---

## 12. Orchestrator's critical assessment (protocol §5)

*Written 2026-09-14 at the branch tip, before the merge. Checks chosen to differ from the agent's.*

1. **Is it a pure move?** I filtered the branch's whole harness diff for changed lines that are not
   imports, comments, path references or cross-references: 80 lines remain, and every one is a
   subpackage docstring, the README's package map, an `_EXPERIMENT_DIR` anchor gaining one parent
   level (three modules), the child spawn going through `pool.CHILD_DIR`, or the two fixture strings
   of the independence gate's tooth. No expression, branch or constant changed. Git detects all
   38 moves as renames.
2. **Does it import?** On a trial merge of the branch onto trunk (`486fa9ad`) I walked the package
   with `pkgutil` from outside it: 45 modules, 0 failures. `--selfcheck` on that record-less tree:
   PASS.
3. **The 16 re-made runs.** The agent's account is right and each cause is in the code: gate G4's
   doctored runs pass `resume=False` (`gate_audit.py`, the `run_all` call), so **every press of
   `--gate all` makes 12 PROCESS runs there regardless of the tree**; G7's own tooth makes one; the
   three `entry=optimisation` censuses are `census-1` and refused by name per amendment 17. None is
   caused by the move. G4's fixed cost goes to the improvement list at the merge.
4. **`ystate.py` staying at the package top** is the right call. The frozen driver copy reaches it by a
   literal path that `copy_gates.py` asserts as a permitted edit; moving it is a driver-copy change
   with G0′ and GR behind it, not a folder task. The README and `child/__init__.py` both say it
   belongs to the amendment-13 set.
5. **§4** was stale against the branch's own stage records (the agent left the render to the merge,
   correctly refusing to guess). I rendered it on the branch from those records: 137 lines, the
   classes the agent's word-diff named; `--plan-tables check` is clean at the tip.
6. **A fault of mine, recorded here because the report is where the run budget is accounted for.**
   Probing the button's failure path, I pressed `--gate all --resume` on the record-less trial tree.
   That is not a failure path: with no records the pool starts every run. It ran about ten minutes at
   three workers before I killed it and deleted the tree; the records were not counted before
   deletion (my counter keyed on the wrong field), so the waste is bounded only as "under one press".
   The rule I broke is my own memory's (re-make only what a change alters). Nothing outside the
   throwaway tree was touched.

**Approved for merge.** Records relocate to `arch_surgery/idf_probe/runs/A65_runs/` (path from the
retire script).
