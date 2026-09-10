# A46 (process-copy) — V4's own copy of PROCESS

> **Document status** — OPEN task report. Task A46 (process-copy), branch `A46-process-copy`,
> worktree `/home/wrutten/projects/PROCESS_surgery_worktrees/A46-process-copy`. Awaiting the
> orchestrator's critical assessment before merge (protocol §5). Archived to
> `deprecated/` at merge; folder position records lifecycle, not validity (trap T3).

**Jargon, spelled out once** (protocol §4). *Decision `D<n>`* — a recorded user decision in the
master queue's register. *Gate* — a committed check that must pass before a number is cited;
*teeth* — deliberately breaking the thing a gate watches, to prove the gate can fail. *Driver* —
the arrangement of solvers, optimisers and the model-calling loop (`process/core/caller.py`,
`process/core/solver/`), as opposed to the physics and engineering *models* (`process/models/`).
*Source commit* — the commit the copy was taken from. *Base commit* — `c0ae5b28`, at which the
physics is frozen. *Copy* — `arch_surgery/MDA_partitioning_experiment_v4/PROCESS/process/`.

---

## 1. Verdict

**The copy was made, and it is exactly what it claims to be.**

The whole `process/` package — **224 files, 5 287 940 bytes, `du -sh` 5.6 MB** — was extracted
**from the commit `f2dc9243`** (`git archive f2dc9243 process | tar -x`), never from a working
tree. Before any edit, the copy's staged git tree hash was
`8e3723d28e64fb88785b08696e7afd8566acc96b`, **identical to `git rev-parse f2dc9243:process`** —
one number proving content, file set and file modes all match.

It then received **exactly three edits and nothing else**: the three path constants that the
driver uses to reach out of the package into the research tree, re-pointed at the V4 harness that
will sit beside the copy. Two files changed, **+20 / −15 lines**, all of it the constants and
their adjacent comments.

Both gates **PASS with every tooth tripping**:

- **`copy-identity`** — 224 of 224 files compared, 222 byte-identical to the source commit, 2
  differing and both on the permitted list with their post-edit sha256 and their exact hunks
  matching; **0 files missing, 0 files added, 0 unexplained differences**. Four teeth, all
  TRIPPED.
- **`frozen-physics` (gate G0′)** — 77 of 77 model files compared against the base commit
  `c0ae5b28`, **76 byte-identical**, file set identical, **exactly one differing file:
  `process/models/pulse.py`**, which is the one model edit this experiment has ever approved
  (**D14(b)**, 2026-09-01 — the burn-time residual extracted into a driver-solvable form,
  arithmetic verbatim). **0 unapproved differences.** Four teeth, all TRIPPED.

A third check, **`smoke-import`**, confirms that setting `PYTHONPATH` to the copy's directory is
what makes `import process` resolve under the copy, from a directory that is neither tree — and
its tooth shows that without `PYTHONPATH` the same subprocess resolves to
`/home/wrutten/projects/PROCESS_surgery/process/` (the **main checkout**, not even this worktree).
That is trap T6 demonstrated live.

**`PROCESS_diff.py`** runs in 0.15 s, claims all three hunks from its annotation map, reports 0
unexplained hunks, and restates gate G0′ for a reader. Its own tooth — an unannotated line
appended to a throwaway copy — is reported as **UNEXPLAINED** with a non-zero exit.

**Nothing needs a decision to proceed**, but **five items are flagged for the orchestrator** in
§9, one of which (the missing `…_v4/.gitignore` for `runs/`) would otherwise make every V4 run
record stamp `tree_git_dirty: true`.

---

## 2. What was copied, and from where

Decision **D20** (2026-09-10): *"don't make changes considering backwards compatibility. If v3
would break we have to make a new process folder and modify that. Duplicate the code into
`MDA_partitioning_experiment_v4/PROCESS`."* The repository-root `process/` stays as the tree V3's
records were made against; every V4 driver change is made in the copy.

*Table 1 — what the copy is. One row per property of the copied package. Sizes are `du -sh` of
the directory as it stands on disk; the byte total is the sum of the 224 files' contents at the
source commit, as recorded in `PROVENANCE.json`. Population: the whole `process/` package, all
224 tracked files, nothing excluded.*

| property | value |
|---|---|
| copy location | `arch_surgery/MDA_partitioning_experiment_v4/PROCESS/process/` |
| source path | `process/` — the PROCESS package at the repository root |
| source commit | `f2dc9243` (`f2dc92431f974cbda1ea967ddb42112766160ee5`), the branch point of `A46-process-copy` off `architecture_surgery` |
| source tree hash | `8e3723d28e64fb88785b08696e7afd8566acc96b` |
| extraction | `git archive f2dc9243 process \| tar -x -C PROCESS/` — from the commit, never the working tree |
| files | 224 (171 `.py`, 42 `.dat`, 11 `.png`), all mode `100644` |
| bytes at source commit | 5 287 940 |
| `du -sh PROCESS/process` | 5.6 MB |
| `du -sh PROCESS/process/models` | 3.0 MB |
| `du -sh PROCESS` (incl. `PROVENANCE.json`, `copy_gates.py`) | 5.7 MB |
| copy date | 2026-09-10 |

These match the harness plan §3's measured figures (5.6 MB, 224 files, 3.0 MB of it `models/`)
exactly.

**`PROVENANCE.json`** (342 lines, 32 945 bytes, human-readable without a script) records: the
source path, commit, full hash and tree hash; the copy date and the task; the sha256 of **every
one of the 224 files at the source commit**; the frozen-physics section (base commit, the 77
model files, the one approved difference with its sha256 at the base commit and its expected
sha256 in the copy); and the permitted-edit list — per file, each constant's name, the expression
it resolved to before and after, the expected post-edit sha256, and the **exact expected hunks**.

**One file present in the root working tree is absent from the copy: `process/_version.py`.** It
is untracked by design (`# don't change, don't track in version control`, generated by
vcs-versioning) and nothing in `process/` imports it. See §6 for what that implies.

---

## 3. What differs from the source commit, and why

*Table 2 — the complete set of edits the copy received. One row per re-pointed constant: the file
inside the package, the constant's name, the expression it resolved to at the source commit and
the expression it resolves to in the copy, and the decision that settled it. Nothing else in the
copied tree differs from the source commit — that is gate `copy-identity`'s claim, §4. The
`parents[n]` indices were verified by resolving them in the tree, not taken from the brief.*

| file in the copy | constant | was | now | settled by |
|---|---|---|---|---|
| `process/core/solver/module_solve.py` | `YSTATE_MODULE_PATH` | `parents[3] / "arch_surgery" / "fixedpoint" / "ystate.py"` | `parents[4] / "harness" / "ystate.py"` | D20, harness-plan decision (2), ruled option (v) |
| `process/core/caller.py` | `NODE_WRITESET_PATH` | `parents[2] / "arch_surgery" / "docs" / "data" / "node_writesets.json"` | `parents[3] / "harness" / "data" / "node_writesets.json"` | D20, harness-plan decision (3), ruled copy |
| `process/core/caller.py` | `NODE_MAP_PATH` | `parents[2] / "arch_surgery" / "docs" / "data" / "dsm_node_map.json"` | `parents[3] / "harness" / "data" / "dsm_node_map.json"` | D20, harness-plan decision (3), ruled copy |

**The index arithmetic, verified in the tree.** From the copy's `module_solve.py`,
`Path(__file__).resolve().parents[4]` is
`arch_surgery/MDA_partitioning_experiment_v4/` (parents 0–3 being `solver`, `core`, `process`,
`PROCESS`). From the copy's `caller.py`, `parents[3]` is the same directory (parents 0–2 being
`core`, `process`, `PROCESS`). Both were resolved by running Python against the copied files.

**Each constant's adjacent comment says the target does not exist yet** — `harness/ystate.py` and
`harness/data/` are created by later harness tasks — and names the decision and this task.

*Table 3 — the diff of the copy against its source commit, as `PROCESS_diff.py --markdown`
produced it. One row per changed file: lines added and removed by `git diff` against the commit
(not against any working tree), the hunk count, and the mechanism each hunk serves according to
the annotation map inside `PROCESS_diff.py`. `UNEXPLAINED` would mean no annotation claims the
hunk; there are none. Population: all 224 files of the copied package.*

| file | + | − | hunks | serves |
|---|---:|---:|---:|---|
| `process/core/caller.py` | 11 | 7 | 2 | `NODE_WRITESET_PATH` → `harness/data/` (D20, decision 3); `NODE_MAP_PATH` → `harness/data/` (D20, decision 3) |
| `process/core/solver/module_solve.py` | 9 | 8 | 1 | `YSTATE_MODULE_PATH` → `harness/ystate.py` (D20, decision 2 option v) |

**No other edit was made** — not the unguarded read the harness plan §3.3 offers to repair, not a
rename, not a cleanup. See §9(b).

**Audit of what else could reach outside the package.** Every `Path(__file__)` in the copy was
listed: five occurrences, of which two are `caller.py`'s `_PREDICATE_SOURCES` pointing at
`process/core/solver/objectives.py` and `constraints.py` — inside the package, correct as they
stand — and three are the constants above. There is no fourth research-tree path. The only other
externally-supplied path, `POST_SOLVE_PATH`, comes from the environment variable
`PROCESS_ARCH_POST_SOLVE` and is the harness's to supply. Twelve further mentions of
`arch_surgery/` survive in comments, docstrings and one error-message string; none is a path that
is opened. They are listed in §9(c)–(d).

---

## 4. Gate `copy-identity`

**Criterion.** Every file under `PROCESS/process/` is byte-identical (sha256) to the same path at
the source commit, read with `git cat-file` — against the commit, never a working tree — **except**
the permitted-edit files, whose post-edit sha256 **and** whose exact unified-diff hunks must match
the ones recorded in `PROVENANCE.json`. The **file set** is compared as well as the contents,
because a per-file hash loop that never compares the set passes on a removed and on an added file.

*Table 4 — gate `copy-identity` at commit `e130467a`, produced by
`PROCESS/copy_gates.py copy-identity`. One row per quantity the gate reports; the denominator is
the number of paths actually compared, not a subset. Record:
`…_v4/runs/gates/copy_identity/gate.json` (untracked bulk).*

| quantity | value |
|---|---|
| verdict | **PASS** |
| files at the source commit | 224 |
| files in the copy | 224 |
| files compared | 224 |
| files byte-identical | 222 |
| files missing from the copy | 0 |
| files added to the copy | 0 |
| permitted-edit files, hunks and post-edit sha256 matching | 2 of 2 |
| unexplained differences | **0** |

*Table 5 — the teeth of `copy-identity`. Each row is a perturbation applied to a **throwaway
temporary copy** of the package — the real tree is never modified — after which the gate is re-run
and must FAIL. "TRIPPED" means the gate did fail, i.e. the tooth worked.*

| tooth | perturbation | result |
|---|---|---|
| `one_byte_changed` | byte 4 of `process/core/constants.py`, `'i'` → `'I'` (same length) | **TRIPPED** |
| `file_removed` | `process/core/constants.py` deleted | **TRIPPED** |
| `file_added` | `process/core/_tooth_added.py` created | **TRIPPED** |
| `permitted_file_changed_elsewhere` | byte 4 of `process/core/caller.py`, `'o'` → `'O'` — a file the gate *is* allowed to differ in, changed somewhere other than the constants | **TRIPPED** |

The fourth tooth is the one the brief warned about and is not in the plan's list: without it, the
permitted-edit list would be a blanket pardon for `caller.py` and `module_solve.py`, and any later
edit to either would pass. It is caught by the recorded post-edit sha256 and by the recorded
hunks, independently.

---

## 5. Gate G0′ — the frozen physics

**Criterion.** Every file under `PROCESS/process/models/` has the sha256 it is supposed to have
against the frozen base commit `c0ae5b28` (D5, the physics freeze): the base commit's content,
except for model files an approved decision names, whose expected content is **also** pinned by
sha256 — so a *further* edit to an approved file fails as well. The file set is compared. The
comparison is against `c0ae5b28`, never against the repository-root working tree, so a root-tree
edit cannot mask a copy-tree edit or the reverse.

**It is not byte-identical, and here is exactly how it differs.**

*Table 6 — the `models/` diff against the frozen base commit `c0ae5b28`, measured file by file by
`PROCESS/copy_gates.py frozen-physics` at commit `e130467a`. One row per model file that differs;
the file **set** is identical (77 files at the base commit, 77 in the copy, 0 missing, 0 added),
and the 76 files not listed are byte-identical. Line counts from
`git diff --stat c0ae5b28 f2dc9243 -- process/models/`.*

| file | differs by | approved by | what the edit is |
|---|---|---|---|
| `process/models/pulse.py` | +113 / −9 lines | **D14(b)**, 2026-09-01 | The burn-time residual extracted into a driver-solvable form: `burn_time_root` holds the original closed-form expression *moved but not changed*, `burn_time_residual` says the same relation as a residual, and `Pulse.run` calls `subsolve(...)` with `direct=self.calculate_burn_time`. Structural only — what the model computes is unchanged, which is what D11's approval rule licenses |

**That is the whole list.** No other file under `models/` differs from `c0ae5b28` in any way. The
diff was read in full and is the D14(b) extraction and nothing else.

**Why the other approved model-adjacent edit does not appear here.** D14(a) approved the `lablcc`
extension in `process/data_structure/numerics.py`, which is **not** under `models/` and is
therefore outside this gate's scope. For context, the whole `process/` package differs from
`c0ae5b28` in **13 files** (+4 510 / −45 lines) — the probe modules, `caller.py`,
`module_solve.py`, `subsolve.py`, the registry files, `numerics.py`, and `pulse.py`. Twelve of
those thirteen are driver or instrument code, which the experiment is free to change; the
thirteenth is `pulse.py`, and it is the one G0′ exists to police.

*Table 7 — gate G0′ at commit `e130467a`. One row per quantity; the denominator is every file
under `models/`, not a sample. Record: `…_v4/runs/gates/frozen_physics/gate.json` (untracked).*

| quantity | value |
|---|---|
| verdict | **PASS** |
| base commit compared against | `c0ae5b28` (`c0ae5b28649f2b20fb7efc7904628b6defe4151c`) |
| model files at the base commit | 77 |
| model files in the copy | 77 |
| model files compared | 77 |
| model files byte-identical to the base commit | 76 |
| model files missing from the copy | 0 |
| model files added to the copy | 0 |
| model files differing from the base commit | 1 — `process/models/pulse.py` |
| **unapproved** differences | **0** |

*Table 8 — the teeth of G0′. As Table 5: each perturbation is applied to a throwaway temporary
copy, the gate is re-run, and it must FAIL.*

| tooth | perturbation | result |
|---|---|---|
| `one_byte_changed` | byte 4 of `process/models/vacuum.py`, `'o'` → `'O'` | **TRIPPED** |
| `file_removed` | `process/models/vacuum.py` deleted | **TRIPPED** |
| `file_added` | `process/models/_tooth_added.py` created | **TRIPPED** |
| `approved_file_changed_further` | byte 4 of `process/models/pulse.py`, `'o'` → `'O'` — the one file allowed to differ, changed further | **TRIPPED** |

The fourth tooth is the reason G0′ is not a blanket pardon for `pulse.py`. Without it, the
approved exception would be a hole the size of the file.

**G0′ is a stage, not a one-off.** It is a repository-state check costing 0.7 s including its
teeth, takes its commits from `PROVENANCE.json` rather than hard-coding them, and runs from any
working directory — so it can and should run at every future V4 commit, as the plan requires.

---

## 6. The smoke import, and what it measured about `__version__`

**Trap T6** is that a git worktree does not redirect the editable install: the `PROCESS_surgery_env`
install points at the **main checkout**, so a subprocess running in its own working directory
imports the main tree unless something else selects otherwise. The copy is a third tree again, so
the point is sharper here than it has ever been.

*Table 9 — the smoke import, produced by `PROCESS/copy_gates.py smoke-import` at commit
`e130467a`. Each row is one fresh subprocess of
`/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python`, running
`import process; print(process.__file__); print(process.__version__)` with its working directory
set to a fresh temporary directory that is neither tree. The second row is the tooth: it must
resolve somewhere other than the copy, or `PYTHONPATH` was not what selected the copy.*

| subprocess | `process.__file__` | `process.__version__` (recorded, not asserted) |
|---|---|---|
| `PYTHONPATH=…_v4/PROCESS` | `…/A46-process-copy/arch_surgery/MDA_partitioning_experiment_v4/PROCESS/process/__init__.py` | `3.4.3.dev8+g3a8d2af99.d20260831` |
| no `PYTHONPATH` (tooth) | `/home/wrutten/projects/PROCESS_surgery/process/__init__.py` | `3.4.3.dev8+g3a8d2af99.d20260831` |

Verdict **PASS**, tooth **TRIPPED**.

**Two things this measured that are worth keeping.**

1. Without `PYTHONPATH`, the import lands in the **main checkout** — not in this worktree, not in
   the copy. Setting `PYTHONPATH` to `…_v4/PROCESS` is the only thing that selects the copy, and
   `process.__file__` is the only thing that proves it did.
2. **`process.__version__` is identical for both trees** — `3.4.3.dev8+g3a8d2af99.d20260831` — and
   it names commit `3a8d2af9`, which is **neither** the copy's source commit `f2dc9243` **nor**
   the frozen base `c0ae5b28`. The copy has no `_version.py` at all, so `__version__` comes from
   `importlib.metadata.version("process")`, i.e. the installed distribution's metadata, i.e. the
   root tree's editable install. This is **trap T10** measured in this repository rather than
   inherited from the sibling study: a `__version__` check would pass on the wrong tree, which is
   worse than no check. The gate records the string and asserts on the path alone.

---

## 7. `PROCESS_diff.py`

At the top level of the V4 folder, beside where `experiment_runner.py` will go, with the name the
user asked for. It reads `PROVENANCE.json` for the source commit, extracts that commit's
`process/` into a temporary directory, and diffs the copy against it with `git diff --no-index` —
**against the commit, never the repository-root working tree**. It runs in **0.15 s** and needs no
PROCESS run.

What it prints: the copy's identity line (source commit, file count, copy date, task); per changed
file, lines added and removed, the hunk count, and a one-paragraph plain-language summary; per
hunk, the switch or mechanism it serves, taken from an annotation map inside the script; and the
frozen-physics statement — gate G0′ re-run live, with the approved D14(b) exception named — for a
reader who will not run the gates. Options `--full` (the raw unified diff), `--markdown` (Table 3
above, caption included), `--teeth`, `--context`.

**An unclaimed hunk is `UNEXPLAINED` and the exit status is non-zero.** Today: 3 hunks, 3 claimed,
0 unexplained, exit 0. A changed file with no summary paragraph is likewise reported and fails.

*Table 10 — the tooth of `PROCESS_diff.py`, run as `PROCESS_diff.py --teeth` at commit
`e130467a`. The perturbation is applied to a throwaway temporary copy of the package; the real
tree is never modified.*

| tooth | perturbation | result |
|---|---|---|
| `unannotated_hunk` | one unclaimed line appended to `process/core/constants.py` | **TRIPPED** — reported `UNEXPLAINED` at `@@ -312,3 +312,5 @@ SECDAY = 86400e0` |

**Extending it is one line.** A later driver-change task adds one `Annotation(path, marker,
serves)` row to `ANNOTATIONS` and one paragraph to `SUMMARIES`. G0′ is not reimplemented here: the
script imports `copy_gates.py` by path, so the frozen-physics criterion has exactly one
implementation.

---

## 8. Autonomous decisions, and how to reverse each

*Table 11 — decisions taken inside the task without asking. One row per decision: what was
decided, why, and the exact reversal path. None changes an experimental quantity; all are about
where code lives and how strictly the gates bind.*

| # | decision | why | reversal |
|---|---|---|---|
| 1 | The gates live in **one file**, `PROCESS/copy_gates.py`, with three subcommands and one entry point | A47 (harness-skeleton) owns `harness/`, and plan task H5 reimplements every gate there. Putting a `gates.py` under `…_v4/` now would collide. One file beside the copy it checks is also the least surprising place for a reviewer | H5 moves the checks into `harness/gates.py` and deletes this file, or imports it. Nothing outside it depends on it except `PROCESS_diff.py`, which loads it by path |
| 2 | The 42 `.dat` files were staged with **`git add -f`** | The repository-root `.gitignore:9` ignores `*.dat`. The root `process/` copies are tracked from before that pattern applied to them; the new copies are not, and `git add` would silently skip them | Add a negation to `.gitignore` (e.g. `!arch_surgery/MDA_partitioning_experiment_v4/PROCESS/process/**/*.dat`). Not done here because `.gitignore` is outside this task's write scope and A47 may edit the same file |
| 3 | The three constants' **adjacent comments were rewritten**, not merely extended by a line | `YSTATE_MODULE_PATH`'s comment justified reaching for the research tree by the D14(c) drift argument — *"vendoring a second copy … would create exactly the drift D14(c) exists to prevent"* — which the copy makes false. Leaving it would have left the code contradicted by the comment beside it | Restore the original comment text from `git show f2dc9243:…`; only the constant's value is load-bearing for the gates |
| 4 | **A fourth tooth per gate**, beyond the three the brief listed | Without it, "the permitted-edit list" and "the approved model edit" are blanket pardons for those files — the exact hole the gates exist to close | Delete the two rows from `teeth()` in `copy_gates.py` |
| 5 | The **smoke import is a subcommand of `copy_gates.py`**, not a separate script, and carries its own tooth | Protocol §15: one entry point, failure paths reachable from it. A separate script would be a stage existing only as a shell invocation | Split it out; it is one self-contained function |
| 6 | `PROVENANCE.json` records, per permitted-edit file, the **expected post-edit sha256 and the exact expected hunks** — beyond the brief's "file, constant name and expected new value" | Without them the gate can only say "this file is allowed to differ", which passes on any later edit | Drop the two keys; the gate degrades to a file-level allowance |
| 7 | G0′ **pins `pulse.py`'s expected content by sha256** as well as naming it approved | Same reason as 6, applied to the physics freeze | Drop `sha256_expected_in_copy` from the approved-differences record |
| 8 | `provenance` **refuses to overwrite** `PROVENANCE.json` without `--force`, and refuses outright if the set of files differing from the source commit is not exactly the declared permitted-edit set | Regenerating provenance must never be the way an unapproved edit becomes approved | Remove the two `SystemExit` guards in `build_provenance` |

---

## 9. For the orchestrator

**(a) `…_v4/.gitignore` with `runs/` is *not* delivered, and something must deliver it.** Harness
plan §10 row H0 lists it; this task's brief scoped it out (`PROCESS/` and `PROCESS_diff.py` only),
and A47 (harness-skeleton) works in the same folder, so creating it here risked a merge conflict.
**The consequence is concrete**: V3's own `.gitignore` states that without it
`git status --porcelain` is never empty while `runs/` exists, so **every V4 run record would stamp
`tree_git_dirty: true`** and the clean-tree stamp the plan asks for could never be reached. It is
one line and must land before any V4 record is made. `arch_surgery/idf_probe/.gitignore` and
`…_v3/.gitignore` are the precedents.

**(b) The `caller.py` unguarded-read repair was *not* made, on the brief's instruction, and the
harness plan says it should be.** Plan §3.3 says *"The `caller.py:583` missing-existence-check
asymmetry is repaired in the copy as part of the same edit."* The brief says *"No other edit — not
the unguarded read at `caller.py:583`."* The brief was followed. The site is now
`caller.py:587` in the copy: `NODE_MAP_PATH` is existence-checked on all three of its read paths
and `NODE_WRITESET_PATH` on one of its two, so the second raises a bare `FileNotFoundError`
instead of a `RuntimeError` naming the generator. **This matters more now than it did**, because
the constant points at a file that does not exist yet. One line, whenever it is authorised.

**(c) One user-facing error message in the copy is now stale.** `caller.py:350` reads
`f"Generate with arch_surgery/fixedpoint/gen_node_writesets.py."` — it names V3's generator for a
file that now lives at `harness/data/node_writesets.json`. It is a string in an error path, not a
filesystem path, so nothing breaks; but the first person to hit the missing file is told to look
in the wrong tree. Would be a fourth edit.

**(d) Twelve further `arch_surgery/` references survive in the copy, all inert.** In
`_idf_probe.py` (2), `caller.py` (2 comments), `module_solve.py` (1 docstring, 1 importlib module
name `"_arch_surgery_ystate"`), `subsolve.py` (3), `constraints.py` (2),
`iteration_variables.py` (2), `numerics.py` (1), `pulse.py` (1). All point at documents or
generators in the root research tree. None is opened at run time — every `Path(__file__)` in the
copy was enumerated and there are exactly five, three of them the re-pointed constants and two of
them internal to the package. Left alone under "no other edit"; worth a sweep whenever the
terminology homogenisation of plan §11.2 reaches the copy.

**(e) Three of H0's listed deliverables are not in this task and must be assigned.** Plan §10 row
H0 lists `…_v4/harness/data/` with its own provenance, `harness/ystate.py` moved whole, and the
`.gitignore`. The brief assigned this task only `PROCESS/` and `PROCESS_diff.py`. The copy's
constants already point at `harness/ystate.py` and `harness/data/`, so whichever task creates them
must put them at exactly those paths — and should re-run `PROCESS/copy_gates.py all`, which will
still pass (the gates do not require the targets to exist) but whose smoke import will then be
worth extending to an actual run.

**(f) Nothing needed a decision to complete the task.** No gate failed, no ambiguity in the brief
was resolved against it, and no edit outside the three constants was made.

---

## 10. Files, commits, and how to re-run everything

*Table 12 — the commits on branch `A46-process-copy`, oldest first. The copy and the edits are
separate commits so that the copy is reviewable by inspection: `git show --stat bdd9953a` is 224
added files and nothing else, `git show bcb2891e` is 35 lines.*

| commit | what |
|---|---|
| `bdd9953a` | verbatim copy of `process/` at `f2dc9243`, no edit — 224 files, tree hash identical to `f2dc9243:process` |
| `bcb2891e` | the three permitted path constants and their comments — 2 files, +20 / −15 |
| `2eec5fee` | `PROVENANCE.json`, `copy_gates.py` (both gates + smoke import, nine teeth), `PROCESS_diff.py` |
| `e130467a` | the smoke import records `process.__version__` beside `__file__`, without asserting on it (trap T10) |

*Table 13 — the committed scripts every number in this report came from (protocol §15), and the
commit they were run at. No number here came from an ad-hoc command line; the `du -sh`, tree-hash
and `git diff --stat` figures in §2, §3 and §5 are inspection of git and the filesystem and are
reproduced by the scripts' own records.*

| number in this report | produced by | at commit |
|---|---|---|
| Tables 4, 5 (gate `copy-identity` and its teeth) | `PROCESS/copy_gates.py copy-identity` | `e130467a` |
| Tables 6, 7, 8 (gate G0′, the `models/` diff, its teeth) | `PROCESS/copy_gates.py frozen-physics` | `e130467a` |
| Table 9 (smoke import) | `PROCESS/copy_gates.py smoke-import` | `e130467a` |
| Table 3 (the diff of the copy against its source commit) | `PROCESS_diff.py --markdown` | `e130467a` |
| Table 10 (`PROCESS_diff.py`'s tooth) | `PROCESS_diff.py --teeth` | `e130467a` |
| Table 1 (file count, byte total, shas) | `PROCESS/copy_gates.py provenance` → `PROVENANCE.json` | `2eec5fee` |

**To re-run all of it** (0.9 s total, no PROCESS run, from any working directory):

```
PY=/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python
cd arch_surgery/MDA_partitioning_experiment_v4
$PY PROCESS/copy_gates.py all      # smoke import + both gates + nine teeth
$PY PROCESS_diff.py                # the reviewer's overview
$PY PROCESS_diff.py --teeth        # the unexplained-hunk tooth
```

Gate records are written to `…_v4/runs/gates/{smoke_import,copy_identity,frozen_physics}/gate.json`
— untracked bulk, per CLAUDE.md; only this report's verdicts are committed.

*Table 14 — what this task added to the repository. One row per tracked path; `runs/` is untracked
and not listed.*

| path | size | what |
|---|---|---|
| `…_v4/PROCESS/process/` | 224 files, 5.6 MB | the copy |
| `…_v4/PROCESS/PROVENANCE.json` | 342 lines, 32 945 B | what the copy is and what it may differ in |
| `…_v4/PROCESS/copy_gates.py` | 766 lines, 31 269 B | `copy-identity`, `frozen-physics` (G0′), `smoke-import`, `provenance`; nine teeth |
| `…_v4/PROCESS_diff.py` | 397 lines, 15 458 B | the reviewer's one view of every change to PROCESS |
| `docs/reports/A46_process_copy.md` | this file | — |

---

## 11. Change log (append-only)

| date | entry |
|---|---|
| 2026-09-10 | Task opened. Documents read: `CLAUDE.md`, `TRAPS.md`, `MASTER_TODO.md` protocol §§1–16 and the D11/D14/D20/D22 register rows, `V4_HARNESS_IMPLEMENTATION_PLAN.md` §3, §7.6, §10 row H0 and §11 in full, `EXPERIMENT_PLAN.md` §3.8 (i) and Appendix A. |
| 2026-09-10 | `process/` extracted from `f2dc9243` with `git archive`; staged tree hash `8e3723d2…` confirmed identical to `git rev-parse f2dc9243:process`. Committed as `bdd9953a`. The 42 `.dat` files needed `git add -f` (root `.gitignore:9 *.dat`); recorded as autonomous decision 2. |
| 2026-09-10 | `parents[]` arithmetic resolved in the tree (module_solve → `parents[4]`, caller → `parents[3]`); the three constants re-pointed and their comments updated; both files compile. Committed as `bcb2891e`. |
| 2026-09-10 | `PROVENANCE.json` generated; `copy_gates.py` and `PROCESS_diff.py` written and committed as `2eec5fee`. Three defects found and fixed during development, all in the new scripts: `git ls-tree` and `git archive` resolve pathspecs relative to the working directory (fixed with `--full-tree` and `git -C <toplevel>`); `importlib` module loading needs `sys.modules` populated before `exec_module` or `@dataclass` fails; `git diff --no-index` strips the leading `/` of absolute paths and prefixes `a/`/`b/`, which broke the path normalisation and made every hunk read as `UNEXPLAINED` — an accidental but real demonstration of that alarm before the deliberate tooth was written. |
| 2026-09-10 | Smoke import extended to record `process.__version__` after measuring that it is identical for the copy and the root tree and names a third commit — trap T10 in this repository. Committed as `e130467a`. |
| 2026-09-10 | All gates re-run at `e130467a`: `copy-identity` PASS (224 compared, 222 identical, 0 missing, 0 added, 0 unexplained), G0′ PASS (77 compared, 76 identical, 1 approved difference `pulse.py` under D14(b), 0 unapproved), smoke import PASS; nine teeth all TRIPPED; `PROCESS_diff.py` 3 hunks all claimed, its tooth TRIPPED. Report written. |
