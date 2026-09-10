# A48 (harness-data) — the committed data the experiment reads, and the copy's second round of edits

> **Document status** — **MERGED TASK REPORT, archived.** Merged into `architecture_surgery` on
> 2026-09-10 (`d9fe737f`); the orchestrator's critical assessment (protocol §5) is §13; folder
> position records lifecycle, not validity (trap T3). Task **A48 (harness-data)**, branch
> `A48-harness-data` off `architecture_surgery` at `30198919`. It completes task **H0** of the
> approved V4 harness plan
> [`../plans/V4_HARNESS_IMPLEMENTATION_PLAN.md`](../plans/V4_HARNESS_IMPLEMENTATION_PLAN.md),
> whose first half was A46 (process-copy).
> **Every number below is produced by executing a committed script at commit `e8111221`**
> (protocol §15) — `harness/data_provenance.py`, `harness/selfcheck.py`, `experiment_runner.py`,
> `PROCESS/copy_gates.py`, `PROCESS_diff.py`. §11 says how to re-run each of them.
> **No PROCESS run was made by this task.** No file outside
> `arch_surgery/MDA_partitioning_experiment_v4/` was created or changed, except this report.

| | |
|---|---|
| **Verdict** | **PASS.** The sixteen committed files the experiment reads are in `harness/data/`, each **byte-identical (sha256) to its source read back from commit `30198919`** — 16/16, plus the moved predicate module `harness/ystate.py`, whose body is byte-identical to its own source once the recorded 19-line heritage paragraph is removed again: **17 of 17 comparisons, 0 mismatches**. The three declared counts per configuration — coupling-state components, iteration variables, constraints — agree with the files: **9 of 9**. The copy of PROCESS received the five edits harness plan §3.3 assigns here; `copy_gates.py all` PASSes (**224 files compared, 222 identical, 2 permitted; 77 model files, 76 identical, `pulse.py` the one approved difference**) and `PROCESS_diff.py` exits 0 with **7 hunks, 0 unexplained**. **The first self-check against the production copy PASSes 5 of 5** with the pending list exactly the five `B1`/`B3` pairs, and the preflight reports **READY, exit 0, 0 artifacts missing**. **Twenty-nine teeth, twenty-nine tripped.** |
| **What this delivers** | `harness/data/` (16 files + `PROVENANCE.json`), `harness/data_provenance.py`, `harness/ystate.py` (821 lines moved whole + 19), five recorded edits to the copied driver, `copy_gates.py`'s permitted-edit model generalised from constant markers to **recorded hunks** plus a third gate `edit-behaviour`, four `PROCESS_diff.py` annotations, a fifth self-check `data`, and the data passages of `harness/README.md`. |
| **One finding, fixed and reported** | The three committed input files **could not be staged without `git add -f`**. The repository-root `.gitignore` ignores `*.DAT` as well as `*.dat`, gitignore matching is **case-sensitive**, and the V4 `.gitignore`'s `!*.dat` therefore never covered `<configuration>.IN.DAT`. Measured with `git check-ignore -v` before and after; the V4 `.gitignore` now re-includes `harness/data/*.IN.DAT`. §5.4. |
| **One thing deliberately left stale** | Each `write_sets_*.json` carries an internal field `ystate_artifact` naming the coupling-state file under the repository's older spelling. It stays, because byte-identity is worth more than tidiness — and because the driver **never pairs the two files by name**. §4.3 cites the lines that pair them by content hash instead. |
| **Nothing needs a user decision** | Four autonomous decisions, each with its reversal path: §9. |

---

## 1. Words used here, spelled out once

A report should read without the queue open beside it (protocol §4).

- **The experiment.** Whether *the arrangement of solvers and optimisers alone* changes the cost of
  solving PROCESS, with every physics and engineering model frozen. This revision of it lives in
  `arch_surgery/MDA_partitioning_experiment_v4/`.
- **The copy.** `…_v4/PROCESS/process/` — this revision's own copy of the PROCESS package, made by
  A46 (process-copy) from commit `f2dc9243`. The repository-root `process/` stays as the tree the
  earlier revisions' records were made against. Recorded as decision **D20**.
- **Configuration.** One optimisation problem. There are three: `large_tokamak_nof`,
  `low_aspect_ratio_DEMO` (both *pulsed*, so the burn time couples) and `st_regression` (*steady
  state*, so it does not).
- **Input file.** The file a configuration is read from — the *committed* one, never edited, or its
  *lifted* derived copy. ("Frozen" is reserved for the physics freeze and for the convergence
  predicate's mode, and names no file.)
- **Coupling state.** The ~840 quantities the models pass to each other, with a measured scale for
  each. Convergence means every one of them has stopped moving relative to its own scale.
- **Write sets.** Which of those quantities each block of the partition writes.
- **Deferral `per_call` / `per_run`.** Work moved out of the inner loop: `per_call` runs once per
  call to the models, `per_run` once per run.
- **Gate, tooth.** A gate is a check that must pass before a number is believed. A *tooth* is a
  deliberate break the check must catch — a check never shown to fail is an assertion, not a
  measurement (protocol §12).
- **Decisions** cited: **D5** the models are frozen; **D9** the committed input files are never
  edited; **D11** minimal structural model edits need the user's approval; **D14(b)** the one such
  edit, in `pulse.py`; **D20** the experiment runs its own copy of PROCESS; **D23** one tolerance
  everywhere; **D24** the orchestrator finishes this rebuild autonomously.
- **Traps** cited: **T6** a worktree does not redirect the editable install; **T9** never read a
  sibling repository's generated output live; **T10** `process.__version__` can name the wrong
  commit; **T11** a number published without the condition that limits it.

---

## 2. What was asked, and what was done

Harness plan **§10 row H0** delivers the copy of PROCESS *and* `harness/data/` *and*
`harness/ystate.py`. A46 (process-copy) delivered the copy alone, deliberately: mixing the copy
with an edit makes the copy unreviewable. This task delivers the rest, in five commits.

*Caption: one row per deliverable of the task brief, with the section that reports it and the
commit that carries it. "Gated by" names the check that would fail if the deliverable were wrong.*

| # | deliverable | gated by | §  | commit |
|---|---|---|---|---|
| 1 | `harness/data/` — 16 files, each byte-identical to its source | self-check `data`, 4 teeth | §4 | `e06650e8` |
| 2 | `harness/ystate.py` — the predicate module moved whole | self-check `data`, hunk-removal identity | §6 | `e672679b` |
| 3 | the copy's five edits, with the permitted-edit model generalised | `copy_gates.py all`, `PROCESS_diff.py` | §7 | `c37dcbdf` |
| 4 | a `data` check in `harness/selfcheck.py` | its own four teeth | §8 | `e8111221` |
| 5 | the first PASS of the self-check against the production copy | — (it *is* the result) | §8.3 | run at `e8111221` |
| 6 | this report | — | — | (this commit) |

---

## 3. The mapping authority, and how a disagreement would have been caught

The brief named sixteen files and their sources. `harness/config.py`'s `artifact_file_names()` —
the same function the arms use to hand a switch its artifact — names them too, under two schemes:
`harness` for the name in `harness/data/`, `repository` for the older spelling the file has in the
repository's shared data directory. **Neither is trusted.** `harness/data_provenance.py` derives
the list from the code and compares it against `EXPECTED_MAPPING`, a transcription of the brief;
a disagreement raises `SystemExit` naming both sides rather than picking one:

```
the artifact mapping in harness/config.py and the mapping this module declares
disagree, so neither is used.  From the code: {...}.  Declared here: {...}.
```

They agree, on all sixteen. The list is printed by `python harness/data_provenance.py plan`.

Two rows deserve a note.

- **`st_regression` has no lifted input file**, so its two per-run deferral roles resolve to *one*
  file, `defer_per_run_st_regression.json`, copied once. That is why the count is 3 + 2 + 3×3 + 2 =
  16 rather than 3 + 2 + 4×3 = 17.
- **The two schemes mark opposite members of the per-run pair.** The repository's spelling marks
  the committed input file's artifact (`postsolve_nolift_`) and leaves the lifted one plain; this
  revision marks the lifted one (`defer_per_run_lifted_`) and leaves the committed one plain,
  because the committed input file is what most arms run. On a steady-state configuration the
  unmarked name wins, so both schemes agree on the single file.

---

## 4. `harness/data/` — the sixteen files

### 4.1 What is there

*Caption: one row per file in `harness/data/`. "Role" is what the file is for — the name the
harness and the copied driver ask for it by. "Source" is the path in this repository the bytes were
read from, at commit `30198919`, with `git cat-file`, never from a working tree. The sha256 is of
the file as committed here and is identical to the source's; the first 12 hex digits are shown, the
full value is in `harness/data/PROVENANCE.json`. Population: all 16 copied files; `PROVENANCE.json`
itself is the record, not a copied file, and is excluded from every count in this section.*

| file in `harness/data/` | role | configuration | source | sha256 (first 12) | bytes |
|---|---|---|---|---|---:|
| `large_tokamak_nof.IN.DAT` | input_file | large_tokamak_nof | `arch_surgery/idf_probe/scenarios/large_tokamak_nof.IN.DAT` | `4ec4c4975bd0` | 12 774 |
| `coupling_state_large_tokamak_nof.json` | coupling_state | large_tokamak_nof | `arch_surgery/docs/data/ystate_a26_large_tokamak_nof.json` | `cf59c6ebd32b` | 339 985 |
| `write_sets_large_tokamak_nof.json` | write_sets | large_tokamak_nof | `arch_surgery/docs/data/writeset_a26_large_tokamak_nof.json` | `cdf035a4f0e2` | 31 747 |
| `defer_per_run_large_tokamak_nof.json` | defer_per_run | large_tokamak_nof | `arch_surgery/docs/data/postsolve_nolift_large_tokamak_nof.json` | `d53b608ddc23` | 111 221 |
| `defer_per_run_lifted_large_tokamak_nof.json` | defer_per_run_lifted | large_tokamak_nof | `arch_surgery/docs/data/postsolve_large_tokamak_nof.json` | `66385c944976` | 111 656 |
| `low_aspect_ratio_DEMO.IN.DAT` | input_file | low_aspect_ratio_DEMO | `arch_surgery/idf_probe/scenarios/low_aspect_ratio_DEMO.IN.DAT` | `72845515cdd9` | 30 325 |
| `coupling_state_low_aspect_ratio_DEMO.json` | coupling_state | low_aspect_ratio_DEMO | `arch_surgery/docs/data/ystate_a26_low_aspect_ratio_DEMO.json` | `918efe5dae6c` | 343 264 |
| `write_sets_low_aspect_ratio_DEMO.json` | write_sets | low_aspect_ratio_DEMO | `arch_surgery/docs/data/writeset_a26_low_aspect_ratio_DEMO.json` | `583711c7b047` | 32 073 |
| `defer_per_run_low_aspect_ratio_DEMO.json` | defer_per_run | low_aspect_ratio_DEMO | `arch_surgery/docs/data/postsolve_nolift_low_aspect_ratio_DEMO.json` | `39add341158a` | 112 379 |
| `defer_per_run_lifted_low_aspect_ratio_DEMO.json` | defer_per_run_lifted | low_aspect_ratio_DEMO | `arch_surgery/docs/data/postsolve_low_aspect_ratio_DEMO.json` | `2f76c9eadf31` | 112 814 |
| `st_regression.IN.DAT` | input_file | st_regression | `arch_surgery/idf_probe/scenarios/st_regression.IN.DAT` | `3f33d565b47d` | 136 043 |
| `coupling_state_st_regression.json` | coupling_state | st_regression | `arch_surgery/docs/data/ystate_a26_st_regression.json` | `7ea07d715e20` | 343 008 |
| `write_sets_st_regression.json` | write_sets | st_regression | `arch_surgery/docs/data/writeset_a26_st_regression.json` | `2300ce0bfa9d` | 31 363 |
| `defer_per_run_st_regression.json` | defer_per_run **and** defer_per_run_lifted | st_regression | `arch_surgery/docs/data/postsolve_st_regression.json` | `be86b7930c86` | 108 636 |
| `node_writesets.json` | node_write_sets | — (shared) | `arch_surgery/docs/data/node_writesets.json` | `7c0f2bee01a1` | 161 367 |
| `dsm_node_map.json` | node_map | — (shared) | `arch_surgery/docs/data/dsm_node_map.json` | `5195c268a3c4` | 14 366 |

The last two keep their names: a path constant inside the copied driver
(`caller.NODE_WRITESET_PATH`, `caller.NODE_MAP_PATH`) fixes them, so renaming either would be a
driver edit rather than a harness choice.

### 4.2 What `PROVENANCE.json` records

Per file: the role, the configuration, the source path, the source file name, the sha256, the byte
count, a sentence saying why the name changed or did not, and the fields the artifact carries about
its own making — `format`, `scenario`, `generated_by` and `tree_git_head` where the artifact has
them. Every artifact has all four; the input files, being PROCESS input, have none.

*Caption: one row per distinct producer among the thirteen copied JSON artifacts. "Tree at
generation" is the artifact's own `tree_git_head` field, the commit the generating script ran at —
recorded, not asserted on, because it is the artifact's claim about itself. Population: the 13
JSON artifacts of §4.1; the 3 input files carry no such fields.*

| producer (`generated_by`) | format | files | tree at generation |
|---|---|---:|---|
| `arch_surgery/fixedpoint/gen_ystate.py` | `a26-ystate-1` | 3 coupling states | `1b4df316` |
| `arch_surgery/idf_probe/a25_writeset.py` | `a25-writeset-1` | 3 write sets | `3820fa5d` (×2), `4abfaa75` (st) |
| `arch_surgery/idf_probe/a33_postsolve.py classify` | `a33-postsolve-1` | 5 per-run deferral sets | `59e91b62` (committed-input pair), `3820fa5d` (the rest) |
| `arch_surgery/fixedpoint/gen_node_writesets.py` | `a26-node-writesets-1` | `node_writesets.json` | `39d15401` |
| `arch_surgery/fixedpoint/gen_node_map.py` | `a18-node-map-1` | `dsm_node_map.json` | `7d5c1c03` |

The record also carries two standing statements.

**Nothing here is derivable in this revision.** The scales inside the coupling-state artifacts are
the experiment's fixed ruler; re-deriving them from a fresh measurement would change what the
tolerance means and break comparability with every earlier revision that quoted a distance on that
ruler. There is no derivation stage — not disabled, absent — and a campaign that finds an artifact
missing refuses (harness plan §5.4). The gap is stated rather than closed: the scales come from a
harvest that is untracked by policy.

**The DSM node map is a committed copy, never read live** (trap T9). It was already so in the
repository; copying it here does not change that.

### 4.3 The one deliberately stale internal name

Each `write_sets_*.json` carries a field

```
"ystate_artifact": "ystate_a26_<configuration>.json"
```

naming the coupling-state file it was built against under the repository's older spelling — which
is not the name that file has in `harness/data/`. **It is left exactly as it was.** Editing it
would forfeit byte-identity with the source, which is the whole claim this directory makes, in
exchange for tidiness inside a field nothing reads.

It is harmless for a checkable reason, not an assumed one: **the driver never pairs the two files
by name.** In the copy,
[`PROCESS/process/core/solver/module_solve.py`](../../MDA_partitioning_experiment_v4/PROCESS/process/core/solver/module_solve.py)'s
`load_subsets` states the rule in its docstring at **lines 633–634** —

> *the artifact's `ystate_components_sha256` must equal the spec's own `components_sha256` — one
> deck, one generation, both files*

— and enforces it at **lines 644–651**:

```python
    spec_sha = spec.components_sha256()
    art_sha = record.get("ystate_components_sha256")
    if art_sha and art_sha != spec_sha:
        raise RuntimeError(
            f"write set {p} was built against ystate components {art_sha} but "
            f"the loaded spec is {spec_sha}: the two artifacts are not from "
            f"the same deck and generation."
        )
```

That is a hash over the component list, not a file name. A wrong pairing is caught by the bytes; a
renamed file is not noticed at all. (At the source commit `f2dc9243` the same lines are 631–632 and
642–649; this task's edits to the file shifted them by two.) The measured agreement is visible in
the artifacts themselves: `coupling_state_large_tokamak_nof.json`'s `components_sha256` and
`write_sets_large_tokamak_nof.json`'s `ystate_components_sha256` are both
`fb09cd0d6ba0ab59a84c2dec221936f1dcaf1d090473f926569eb33d6b99fe79`.

`PROVENANCE.json` records the field, its value per file, and this reasoning, under
`stale_internal_names`.

### 4.4 The declarations, checked against the files

`harness/config.py` states three numbers per configuration. The preflight already re-read one of
them (the component count) from the artifact; the other two were declared and never checked
anywhere. All three are now read back from the files by
`data_provenance.declaration_checks()`, which the `data` self-check runs.

*Caption: one row per configuration. "Declared" is `harness/config.py`'s value; "in the file" is
read back — the component count from the coupling-state artifact's own `n_components`, the
iteration-variable and constraint counts by counting `ixc =` and `icc =` statements in the
committed input file, one entry per statement (no statement in any of the three files carries a
comma-separated list; checked). Population: 3 configurations × 3 quantities = 9 comparisons,
9 agreeing, 0 disagreeing.*

| configuration | coupling-state components | iteration variables | constraints |
|---|---:|---:|---:|
| `large_tokamak_nof` | 840 = 840 | 20 = 20 | 26 = 26 |
| `low_aspect_ratio_DEMO` | 846 = 846 | 19 = 19 | 25 = 25 |
| `st_regression` | 827 = 827 | 14 = 14 | 18 = 18 |

**No mismatch to report.** The brief asked for any mismatch as a finding; there is none.

---

## 5. Staging — the one finding

The brief asked for `git check-ignore -v` evidence that the files stage without `-f`. **They did
not**, and the reason is worth recording because it is exactly the shape of a silent failure.

### 5.1 What was expected

The repository-root `.gitignore` ignores `*.dat`; the V4 `.gitignore`, added at A46's merge,
re-includes `!*.dat` so that the copy's 42 tabulated-data files stage without `-f`.

### 5.2 What was measured

The root `.gitignore` ignores **`*.DAT` as well** (line 52), and **gitignore matching is
case-sensitive**, so `!*.dat` does not cover `<configuration>.IN.DAT`. Before the fix, on a
throwaway probe file and then on the real ones:

```
$ git check-ignore -v arch_surgery/MDA_partitioning_experiment_v4/harness/data/*
.gitignore:52:*.DAT   .../harness/data/large_tokamak_nof.IN.DAT
.gitignore:52:*.DAT   .../harness/data/low_aspect_ratio_DEMO.IN.DAT
.gitignore:52:*.DAT   .../harness/data/st_regression.IN.DAT
```

The 13 JSON files were not matched by any pattern (exit 1 on each). Only the three input files were
ignored — the three files that are literally the experiment's input.

### 5.3 Why it matters more than it looks

A46 hit the lowercase half of this and fixed it. The uppercase half survived because nothing had
yet put an uppercase `.DAT` file under `…_v4/` outside `runs/`. Had it not been checked, the three
input files would have been silently absent from the commit; the preflight would have reported
`3 artifact(s) missing`, and the failure would have looked like a copy that did not happen rather
than a commit that did not take.

### 5.4 The fix, and what it does not do

Eight commented lines and one pattern appended to `…_v4/.gitignore`:

```
!harness/data/*.IN.DAT
```

Scoped to the data directory on purpose. An unscoped `!*.DAT` would also un-ignore any `MFILE.DAT`
or `OUT.DAT` a future stage wrote **outside** `runs/` — `runs/` itself is safe either way, because
git does not descend into an ignored directory. After the fix:

```
$ git check-ignore -v arch_surgery/MDA_partitioning_experiment_v4/harness/data/*.IN.DAT
.../MDA_partitioning_experiment_v4/.gitignore:23:!harness/data/*.IN.DAT   harness/data/large_tokamak_nof.IN.DAT
   (and the same for the other two)
```

— a negation pattern, and `git status --untracked-files=all` lists all three as stageable. All 19
paths of commit `e06650e8` were staged by an explicit `git add` of three paths, never `git add -A`
(protocol §12a).

---

## 6. `harness/ystate.py` — the predicate module, moved whole

The coupling-state predicate — what "converged" means in this experiment — was
`arch_surgery/fixedpoint/ystate.py`, 821 lines, importing `numpy` and the standard library and
nothing else. Harness plan §5.3 ruled **option (v)**: move the whole module into the harness and
re-point the copied driver by one path constant, rather than vendoring a second copy into
`process/` or leaving the copy reaching outside its own directory. A46 already set
`module_solve.YSTATE_MODULE_PATH` to this file; this task supplies the file.

**The only change is a heritage paragraph appended to the module docstring** — 19 lines naming the
source path, the source commit `30198919`, this task, and why (D20 and harness plan §5.3 option
(v)). The file is 840 lines.

**The identity mechanism, stated because "byte-identical apart from a change" needs one.** The
paragraph is recorded in `harness/data/PROVENANCE.json` as `module.expected_hunks` — the
**zero-context unified diff** of the copy against its source, the same construction
`PROCESS/copy_gates.py` uses for the copied driver's permitted edits, so one reading habit covers
both. The `data` check then does three things:

1. the recorded hunk is **exactly one hunk and a pure addition** — a removal or a second hunk fails
   at once, so "the paragraph" cannot quietly become "the paragraph and something else";
2. the diff computed live equals the recorded one;
3. the recorded added lines are **removed again** at the position the hunk header names, and the
   remainder is compared byte for byte against the source read back with `git cat-file`.

Measured: 22 recorded diff lines (three of which are the diff's own `---`/`+++`/`@@` headers, 19
added lines), and with them removed the file's sha256 is `ce47ebef1ecb…`, equal to
`arch_surgery/fixedpoint/ystate.py` at `30198919`. The file in the copy is `aac11f0002a8…`.

It imports cleanly under the project interpreter (`SPEC_MODE_A26 = 'a26'`, `SCALE_FLOOR = 1.0`).

---

## 7. The copy's second round of edits

Harness plan §3.3, as amended at A46's merge, assigns five edits to this task: they land here
because this is the task that gives the path constants their targets.

### 7.1 What changed, and why

*Caption: one row per edit to `…_v4/PROCESS/process/`. "Line" is the line number in the copy after
the edit. "Kind" is the category `PROCESS/copy_gates.py` records it under. No row changes what any
model computes; `process/models/` is untouched and gate G0′ is re-run below. Population: the 2 files
of the copied package that differ from the source commit, out of 224.*

| # | file | line | kind | what | why |
|---|---|---:|---|---|---|
| a | `core/caller.py` | 592–597 | existence check | the per-run deferral path read the per-node write sets with **no existence check**; it now raises a `RuntimeError` naming the artifact and `harness/data/PROVENANCE.json`, mirroring the per-call check at 348–354 | plan §3.3 calls it "a one-line asymmetry worth fixing": the same artifact is read on two paths and only one of them said what was missing. Without it the failure is a bare `FileNotFoundError` from inside `json.loads` |
| b | `core/caller.py` | 352–353 | comment (message text) | the per-call refusal told the reader to `Generate with arch_surgery/fixedpoint/gen_node_writesets.py.`; it now names the committed copy in `harness/data/` and its provenance file | the instruction was wrong for this revision: there is no derivation stage, and a reader who followed it would produce a *new* artifact and change the ruler (§4.2) |
| c1 | `core/caller.py` | 462 | comment | the comment describing the per-run deferral artifact named `arch_surgery/docs/data/postsolve_<scenario>.json`; it names `harness/data/defer_per_run[_lifted]_<configuration>.json` | the copy does not read that path any more, and the vocabulary retired "scenario" for "configuration" |
| c2 | `core/solver/module_solve.py` | 33 | comment | the module docstring named `arch_surgery/docs/data/ystate_<scenario>.json`; it names `harness/data/coupling_state_<configuration>.json` | same |
| d | `core/caller.py` 247–249, 363–365; `core/solver/module_solve.py` 530–532 | comment | A46 wrote "The target does not exist yet; a later harness task creates it" beside each of the three path constants. That sentence is now false. It is replaced by one saying the target is a committed file of this experiment and naming `harness/data/PROVENANCE.json` | a comment that was true when written and is false now is worse than no comment. This is the one edit **not** in the brief's list; §9, decision 2 |

Line counts against the source commit `f2dc9243`: `caller.py` +24 / −9 in 5 hunks,
`module_solve.py` +12 / −9 in 2 hunks — both totals including A46's three path constants.

### 7.2 The permitted-edit model, generalised

A46 recorded permitted edits as **constant markers**: `PERMITTED_EDIT_FILES` mapped a file to the
list of constants it re-pointed, and `PROVENANCE.json` emitted a `constants` block. That model has
no place for an edit that is not a constant, and three of the five above are not.

The model is now the **recorded hunk**. `copy_gates.py` gains a `PermittedEdit` dataclass — `kind`
(`path constant` / `existence check` / `comment`), `name`, `description`, `task`, and `was`/`now`
for a path constant — and `PROVENANCE.json` emits an `edits` block in place of `constants`. What
the gate compares is unchanged and was already hunk-based: the file's **post-edit sha256** and its
**exact zero-context hunks**, both recorded. The descriptions are documentation; the hunks are the
check.

`PROVENANCE.json` was regenerated with `copy_gates.py provenance --force`. Its guard is unchanged
and did its job: it refuses to write unless the set of files that actually differ from the source
commit equals `PERMITTED_EDIT_FILES` exactly, so regenerating provenance cannot be the way an
unapproved edit becomes approved.

### 7.3 A third gate: `edit-behaviour`

Edit (a) is the only one that is not a comment, so it is the only one whose *behaviour* can be
wrong. `copy_gates.py edit-behaviour` exercises it in a child process — importing the driver and
calling the per-run deferral loader with a stub in place of the run's data object, which is all
that function touches. **No PROCESS run: nothing is solved, no model is called.** Three arms, and
both trees are handed the same two artifacts by hand so the only thing that differs is the code:

*Caption: the three arms of gate `edit-behaviour` and what each must produce. "Source commit" is
`f2dc9243`'s `process/` extracted to a temporary directory with `git archive`. The tooth is the
third row: a guard that also refuses when the file **is** there would be a new refusal on the path
every run takes, not a repair.*

| arm | write sets | must raise | measured |
|---|---|---|---|
| the copy | absent | `RuntimeError` naming the artifact and `harness/data/PROVENANCE.json` | `RuntimeError`: *"PROCESS_ARCH_POST_SOLVE needs the committed per-node write sets at …, which is not present. Its origin is recorded in harness/data/PROVENANCE.json."* |
| the source commit | absent | `FileNotFoundError` — the defect the edit repairs | `FileNotFoundError` |
| the copy (**tooth**) | present | nothing | nothing raised — **TRIPPED** |

Verdict **PASS**. The second row is what makes the first a change rather than a restatement, and it
is also the first executable confirmation of the asymmetry harness plan §3.3 asserted from reading
the source.

### 7.4 The gates

```
$ python PROCESS/copy_gates.py all
```

*Caption: the three gates `copy_gates.py all` runs, with their populations and teeth. "Compared" is
files; "identical" is files byte-equal to the reference commit. Every tooth is applied to a
throwaway copy of the tree — the real tree is never modified — and each must make the gate FAIL.
Records in `…_v4/runs/gates/`, untracked by design.*

| gate | reference | compared | identical | permitted / approved | teeth | verdict |
|---|---|---:|---:|---|---:|---|
| `smoke-import` | — | — | — | — | 1/1 tripped | **PASS** |
| `copy-identity` | `f2dc9243:process/` | 224 | 222 | 2 permitted-edit files, hunks and sha256 matched | 4/4 tripped | **PASS** |
| `frozen-physics` (G0′) | `c0ae5b28:process/models/` | 77 | 76 | `pulse.py`, D14(b) | 4/4 tripped | **PASS** |
| `edit-behaviour` | `f2dc9243:process/` | 3 arms | — | — | 1/1 tripped | **PASS** |

0 files missing from the copy, 0 added, 0 unexplained differences; 0 model files missing, 0 added,
0 unapproved differences. **G0′ is unaffected by this task: nothing under `process/models/` was
touched.** The `smoke-import` gate confirms trap T6 live — with `PYTHONPATH` set, `import process`
resolves under the copy; without it, it resolves in the main checkout — and records
`process.__version__` for both without ever asserting on it (trap T10: both report
`3.4.3.dev8+g3a8d2af99.d20260831`, which is neither tree's commit).

```
$ python PROCESS_diff.py          # exit 0
$ python PROCESS_diff.py --teeth  # tooth unannotated_hunk: TRIPPED
```

7 hunks across 2 files, **0 unexplained**, 0 files without a summary. Four annotations were added
(one per new mechanism) and both file summaries rewritten. The tooth appends one unclaimed line to
a third file on a throwaway copy and confirms it is reported `UNEXPLAINED`.

### 7.5 `PROCESS_diff.py --markdown`, as produced

*Caption: one row per file in which V4's copy of the PROCESS package differs from its source commit
`f2dc9243`. Columns: the file's path inside the package; lines added and removed by `git diff`
against the commit (not against any working tree); the number of hunks; and, per hunk, the switch or
mechanism the annotation map in `PROCESS_diff.py` says it serves. `UNEXPLAINED` means no annotation
claims the hunk. Population: all 224 files of the copied package.*

| file | + | − | hunks | serves |
|---|---:|---:|---:|---|
| `process/core/caller.py` | 24 | 9 | 5 | harness path constant NODE_WRITESET_PATH -> harness/data/ (D20, decision 3); comment: the artifacts the two path constants name are committed here, and their provenance file says so; comment: the per-call refusal names the committed artifact and its provenance file instead of a generator script in the research tree; harness path constant NODE_MAP_PATH -> harness/data/ (D20, decision 3); comment: the per-run deferral artifact named by the file the copy reads; existence check on the per-run deferral path, mirroring the per-call one (plan section 3.3); no behaviour change where the file exists |
| `process/core/solver/module_solve.py` | 12 | 9 | 2 | comment: the coupling-state artifact named by the file the copy reads; harness path constant YSTATE_MODULE_PATH -> harness/ystate.py (D20, decision 2 option v); comment: the predicate module the path constant names is committed here, and its provenance file says so |

**Frozen physics.** The physics is frozen at base commit `c0ae5b28` (decision D5). Of the 77 files
under `process/models/` in this copy, 76 are byte-identical to that commit and the file set matches
exactly. The one file that differs is `process/models/pulse.py`, and it is approved: D14(b),
2026-09-01 — the burn-time residual extracted into a driver-solvable form, the arithmetic verbatim;
structural only, D11's approval rule satisfied. **Gate G0′ verdict: PASS.**

*(The renderer emits one row per file and joins the hunks' claims, so a repeated claim appears once
per hunk that carries it. The per-hunk listing is in the script's default text output, recorded at
`…_v4/runs/gates/`.)*

---

## 8. The `data` check, and the first self-check against the production copy

### 8.1 What the check binds

`harness/selfcheck.py` gains a fifth check in the existing `Check` shape, `data`:

- every file in `harness/data/` has the sha256 `PROVENANCE.json` records, **and** that sha256
  equals the source read back from commit `30198919` with `git cat-file`. **Two comparisons, not
  one** — a record-only check would pass on a changed file whose record had been regenerated;
- the **file set** matches: no file the record names is missing, no file is present that the record
  does not name. `PROVENANCE.json` itself is excluded and that exclusion is named in the code;
- `harness/ystate.py`'s body identity, by the hunk-removal mechanism of §6;
- the nine declared counts of §4.4.

The source is read **from the commit** wherever the blob is there and from the working tree only if
it is not; which of the two was used is reported in the verdict (`sources read from commit
30198919`) rather than hidden, because "compared against a working tree" is a weaker claim than
"compared against the commit" and a reader must be able to tell which was made.

The check uses the **production** campaign's configurations even when the rest of the self-check
runs against the repository tree, because `harness/data/` is the experiment's own directory under
its own naming scheme in both cases. That is stated in the function's docstring.

### 8.2 Its teeth

*Caption: the four teeth of the `data` check. Each perturbation is applied to a **throwaway copy**
of `harness/data/` in a temporary directory and the same verification is re-run against it; the
real directory is never modified. All four must make the check FAIL. Population: one staged copy
per tooth, 4 teeth, 4 tripped, 0 blunt.*

| tooth | perturbation | why it is there | result |
|---|---|---|---|
| one byte changed in a copied file | one byte of `coupling_state_large_tokamak_nof.json` flipped | the base case: a per-file hash must catch a single byte | **TRIPPED** |
| a copied file missing | that file removed | a per-file loop over the record's keys would skip it silently | **TRIPPED** |
| a file added that the record does not name | `_a_file_nobody_recorded.json` written | a per-file loop that never compares the *set* passes on an added file | **TRIPPED** |
| a changed file whose recorded sha256 was updated to match it | the byte flipped **and** the staged record's sha256 rewritten to agree | this is the tooth that matters: it passes a record-only check, and is exactly what "regenerate the provenance and move on" would look like. It must still fail, because the record no longer equals the source | **TRIPPED** |

### 8.3 The first PASS against the production copy

```
$ python experiment_runner.py --selfcheck        # default target = the copy
```

*Caption: the five checks of the harness self-check, run against the experiment's own copy of
PROCESS for the first time (A47 (harness-skeleton) could only reach 4 of 5, the capability probe
failing on 11 pairs because `harness/data/` did not exist and the driver refuses at import).
"Compared" is the check's own denominator, named in its population line. Teeth are deliberate
breaks; every one must trip. Run at commit `e8111221`, ≈26 s wall clock, no PROCESS run.*

| check | population | compared | mismatched | teeth | verdict |
|---|---|---:|---:|---:|---|
| composition | 8 arms × 3 configurations = 24 pairs (+1 removal mechanism) | 25 | 0 | 4/4 | **PASS** |
| rungs | 11 matrix rows × 8 arms = 88 cells; 6 rung steps | 98 | 0 | 3/3 | **PASS** |
| capability | every arm/configuration pair whose arm is active | 22 | 0 | 3/3 | **PASS** |
| provenance | one scratch repository, three states | 4 | 0 | 4/4 | **PASS** |
| **data** | 16 files + the moved module = 17 comparisons; 9 declared counts | 17 | 0 | 4/4 | **PASS** |
| | | | | **18/18 tripped** | **5/5 PASS** |

**Capability, in the detail the brief asked for.** 22 arm/configuration pairs examined: **17
probed** — each in its own child process, importing the copied driver and reading back what it
resolved, all 17 resolving every switch exactly as asked — and **5 refused before probing** because
they declare a switch no tree implements yet. The pending list is **exactly** the five `B1`/`B3`
pairs:

```
B1/large_tokamak_nof, B3/large_tokamak_nof,
B1/low_aspect_ratio_DEMO, B3/low_aspect_ratio_DEMO,
B3/st_regression                                   — all on: output_loop
```

(`B1` is recorded as skipped on `st_regression`: on a steady-state configuration there is no
burn-time coupling, so `B1` composes to `B0`.) The switch is supplied by the approved-but-unmade
driver change A57 (driver-output-path). This is unchanged from A47's finding; what is new is that
it is now measured **against the copy**, which is the tree the records will be made against.

### 8.4 The preflight

```
$ python experiment_runner.py                    # default target = the copy
```

**READY, exit 0, 0 artifacts missing.** All three configurations resolve all seven of their files
(input file, coupling state, write sets, both per-run deferral roles, node write sets, node map);
the component counts printed are the artifacts' own; the two recorded skips on `st_regression` are
named with their reason. The tree stamp is clean — `A48-harness-data`, 0 modified tracked files,
0 untracked paths, `tree_git_dirty: false`.

The campaign section still **refuses**, on two grounds and no longer on a third:

```
REFUSED — the plan's execution is not approved: the user flips EXECUTION_APPROVED …
REFUSED — the run path is not built yet: the stages that start a PROCESS run … are separate tasks
  would run: 275 displaced-entry evaluations + 418 stencil-point evaluations + 275 optimisations
```

The third ground — *"the tree is not the experiment's copy"* — is absent because the tree now **is**
the copy and the copy now works. That is the change this task makes to the runner's behaviour,
without editing the runner.

### 8.5 The earlier self-check, re-run

```
$ python harness/selfcheck.py --tree repository --crosscheck-previous
```

**6 of 6 PASS.** The five that existed before this task all still pass with the same numbers
(composition 25/0, rungs 98/0, capability 22/0, provenance 4/0, crosscheck-previous 17/0), and the
new `data` check passes beside them (17/0). The brief asked to confirm "5/5 still PASS"; the count
is now 6 because this task adds a check, and the five are individually unchanged.

---

## 9. Autonomous decisions, with their reversal paths

**1 — the `.gitignore` re-include is scoped to `harness/data/*.IN.DAT`, not an unscoped `!*.DAT`.**
The V4 `.gitignore` is not on this task's owned-file list, but the alternative was three committed
input files that stage only with `git add -f`, which is how an artifact silently fails to be
committed. Scoped rather than unscoped so that a `.DAT` written outside `runs/` by a future stage is
still ignored. *Reversal:* delete the pattern and its comment from `…_v4/.gitignore`; the three
files stay tracked once committed (gitignore does not affect tracked files), so nothing breaks
immediately — the exposure returns only for a later `.IN.DAT`.

**2 — the three "the target does not exist yet" comments were updated, not left.** A46 wrote them
beside each re-pointed path constant as a forward reference to this task. They are now false. They
are replaced by a sentence saying the target is a committed file and naming
`harness/data/PROVENANCE.json`. This is one more kind of edit than the brief's list, it is
comment-only, and it is recorded as a permitted hunk like the rest. *Reversal:* restore the
original sentence and regenerate `PROCESS/PROVENANCE.json`; `copy_gates.py` and `PROCESS_diff.py`
need no change, because the hunks are recorded rather than enumerated by hand.

**3 — a new module, `harness/data_provenance.py`, rather than logic inside `selfcheck.py`.** The
copy, the record and the verification are one body of knowledge and the self-check needed to call
the third; putting all three in `selfcheck.py` would have put a file-writing stage inside a
read-only gate module. The name says what it holds, with no task or revision token (harness plan
§11.1). It does not collide with A49 (harness-reference)'s files. *Reversal:* inline `verify()`
into `selfcheck.py` and drop the module; the record format would be unaffected.

**4 — `copy_gates.py all` now depends on `harness/data/` existing**, because gate `edit-behaviour`
needs the artifacts to exercise the driver's read path. If they are absent the gate FAILs rather
than skipping — which is right, since the copy's path constants then point at nothing. *Reversal:*
drop `edit-behaviour` from the `all` list; it remains runnable as its own command.

**Not decided here, and deliberately so.** No file outside `…_v4/` was changed. The
`arch_surgery/docs/data/` and `arch_surgery/idf_probe/scenarios/` originals are untouched (D9), and
the repository-root `process/` is untouched.

---

## 10. What a later task must fill in

*Caption: one row per thing this task deliberately leaves for a named later task. "Why not here"
is the reason it is not simply an omission.*

| what | who | why not here |
|---|---|---|
| the two `B1`/`B3` arms' output-time-loop switch | **A57 (driver-output-path)** | it is a driver change; the harness refuses the five pairs rather than composing an environment without it, and that refusal is the measured result of §8.3 |
| the run path — child process, entry points, worker pool, record schema; gate GR | **A50 (harness-run)** | GR runs at the copy commit **before** any driver change; this task makes no PROCESS run |
| the derived (lifted) input files, the census and the per-run deferral derivation stages | **A51 (harness-artifacts)** | the committed artifacts are inputs here; deriving them is a separate stage with its own gate, and there is no derivation stage in this revision for the coupling-state scales at all (§4.2) |
| every gate reimplemented inside `harness/gates.py` | **A52 (harness-gates)** | `copy_gates.py` lives beside the copy it gates, by A46's design; whether it is re-expressed as a `harness.gates.Gate` is A52's call |
| `harness/predicate.py` — the thin layer above `ystate.py` (rebuild a spec from a committed artifact with its hash re-checked, restore snapshots, summarise a residual) | **A50 (harness-run)** | this task moves the module; wiring it to the run path is the run path's work |
| the `frozen \| mixed` predicate mode trial | **A59 (driver-predicate-mode)** | `ystate.py` carries both modes already; choosing between them per run is a driver switch |

One standing gap, stated once so it is not rediscovered: **the coupling-state scales are inherited
from a harvest that is not committed** (35 / 69 / 34 MB of pickles, untracked by policy). The
artifacts can be *verified* from the `harvest_identity` block they carry and from the sha256 of the
source, but not *regenerated*. This revision treats them as given, and that is the honest position
rather than a defect (harness plan §5.4, ruled 2026-09-10).

---

## 11. How to re-run everything

All of it runs in about a minute, under
`/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python`, from
`arch_surgery/MDA_partitioning_experiment_v4/`. **No PROCESS run is started by any of it.**

```bash
cd arch_surgery/MDA_partitioning_experiment_v4
PY=/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python

# §3, §4  the declared mapping, and the data verified against its sources
$PY harness/data_provenance.py plan          # the 16 files and where each came from
$PY harness/data_provenance.py verify        # 17/17 identical, 9/9 declared counts

# §7  the copy: what it changed, and that it changed nothing else
$PY PROCESS_diff.py                          # exit 0, 7 hunks, 0 unexplained
$PY PROCESS_diff.py --markdown               # the table in §7.5
$PY PROCESS_diff.py --teeth                  # unannotated_hunk: TRIPPED
$PY PROCESS/copy_gates.py all                # 3 gates + smoke import, 10 teeth
$PY PROCESS/copy_gates.py edit-behaviour     # §7.3 alone

# §8  the harness's own gates
$PY experiment_runner.py --selfcheck         # 5 checks, 18 teeth, against the copy
$PY experiment_runner.py                     # preflight: READY, exit 0
$PY harness/selfcheck.py --tree repository --crosscheck-previous   # 6/6
```

Re-copying the data (`harness/data_provenance.py copy --force --source-commit <sha>`) and
regenerating the copy's provenance (`PROCESS/copy_gates.py provenance --force`) both need `--force`
and a reviewer who reads the resulting diff, by design: regenerating a record must never be the way
a change becomes blessed.

Gate records are written to `…_v4/runs/gates/`, which is untracked by design (bulk run artifacts
stay untracked; summaries and verdicts are committed).

---

## 12. Change log

*Caption: append-only, one row per commit on `A48-harness-data`, in order.*

| commit | what |
|---|---|
| `e672679b` | `harness/ystate.py` — the predicate module moved whole from `arch_surgery/fixedpoint/ystate.py` at `30198919`; 821 lines, 19 added as a heritage paragraph in the module docstring, nothing else |
| `e06650e8` | `harness/data/` — the 16 committed files, `PROVENANCE.json`, `harness/data_provenance.py`, and the V4 `.gitignore` re-include for `harness/data/*.IN.DAT` |
| `c37dcbdf` | the copy's five edits; `copy_gates.py`'s permitted-edit model generalised to recorded hunks; `PROCESS/PROVENANCE.json` regenerated; gate `edit-behaviour`; four `PROCESS_diff.py` annotations and rewritten summaries |
| `e8111221` | the fifth self-check `data` with its four teeth; `harness/README.md` §4.1, §8 and §10 |
| *(this commit)* | this report |

---

## 13. Orchestrator's critical assessment (protocol §5) — 2026-09-10

*Appended by the orchestrating session before merge, against the report at `bce21213` and the
scripts on the same branch. Load-bearing claims re-run or re-derived, not taken from the report.*

**Verified independently.** (1) The sixteen files: hashed by me against `git cat-file
30198919:<source>` in the main repository — 16 of 16 identical, each matching the sha256 in
`harness/data/PROVENANCE.json`. (2) `harness/ystate.py` against `arch_surgery/fixedpoint/ystate.py`:
a unified diff shows 19 added lines, all inside the module docstring's heritage paragraph, and 0
removed. (3) `PROCESS/copy_gates.py all` into a fresh records directory: the smoke import,
`edit-behaviour`, `copy-identity` (224 compared, 222 identical, 0 unexplained) and G0′ (77 / 76,
`pulse.py` the one approved difference) all PASS, every tooth TRIPPED; `PROCESS_diff.py` exit 0,
two files, 7 hunks, 0 unexplained, `--teeth` TRIPPED; the copy's diff against the branch point is
+19 / −6 in two files, every changed line one of the five recorded edits. (4)
`experiment_runner.py --selfcheck` against the production copy: **5 of 5 PASS — the first time on
the production target** — with capability 22 examined, 17 probed and resolved as asked, 5 refused,
exactly `B1`/`B3` on the pulsed configurations and `B3` on `st_regression`; the preflight READY,
exit 0, 0 artifacts missing; `--tree repository --crosscheck-previous` 6 of 6. (5) `git
check-ignore`: `harness/data/st_regression.IN.DAT` is not ignored and a `.DAT` under `runs/` still
is. (6) Scope: 28 files, all under `…_v4/` plus this report; the copy's `models/` untouched.

**Endorsed, including one correction of my own.** The `.IN.DAT` finding: at A46's merge I wrote
that the V4 `.gitignore`'s `!*.dat` made the copy's data files stageable and tested it on a
lower-case `.dat` path; the root `.gitignore` also ignores `*.DAT`, matching is case-sensitive,
and the three input files would have needed `git add -f` — the exact shape of an artifact that
silently fails to be committed. A48's scoped re-include is the right fix, and this paragraph
corrects my earlier statement. Also endorsed: the role-to-name mapping taken from
`config.artifact_file_names()` with a refusal on disagreement rather than a list typed twice; the
permitted-edit model generalised to recorded hunks, so the copy's provenance states what each of
the seven hunks is and the gate fails on an eighth; the `edit-behaviour` gate exercising the one
non-comment edit on both branches (artifact present and absent); the stale `ystate_artifact` name
left byte-identical and documented, with the pairing verified to be by content hash.

**Limits I hold it to.** (a) `copy_gates.py all` now needs `harness/data/` — acceptable, the copy
and its data are one experiment — but `copy-identity` and `frozen-physics` stay independently
runnable and every driver-change task runs them at its commit. (b) The data check compares
against the sources at `30198919`; a later regeneration of the `docs/data/` originals would not be
noticed, and must not be — V4 reads `harness/data/` only. (c) The `write_sets_*` internal name is
stale by design; nothing parses it by name today, and review must keep it so. (d) No PROCESS run
yet — `edit-behaviour` imports the driver; the first run is A50's.

**Consequences drawn (orchestrator, today).** H0 is complete: the copy, its gates, its data and
the predicate module are in place, and the self-check passes against the production target. The
harness plan's disposition row for the input files ("resolve — they stay where they are") is
amended to the copy. A50 (harness-run) is dispatched off the merged tip: the run path, with gate
GR at that commit, before any driver change.

**Verdict.** Fit to merge; nothing returned.
