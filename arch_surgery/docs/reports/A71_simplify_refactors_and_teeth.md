# A71 (simplify-refactors-and-teeth) — the pure refactors and the zero-schema B items of the simplification survey

> **Document status** — **OPEN.** Task **A71 (simplify-refactors-and-teeth)**, branch
> `A71-simplify-refactors-and-teeth` off `architecture_surgery` at base **`34c5c3e4`** (A70
> (simplify-code-moves) merged). Ruling D27. Items carried: **A3, A4, A5, A6, A7, A8, A10, A11, A12,
> B2, B5, B6, B7, B8** of [`deprecated/A68_harness_simplification_survey.md`](deprecated/A68_harness_simplification_survey.md).
> No `records.SCHEMA` change; nothing under `harness/child/`, `ystate.py`, `PROCESS/process/` or the
> repository-root `process/` touched. **0 PROCESS runs made by this task** (§4.8). Folder position
> records lifecycle, not validity (trap T3).

*Vocabulary is the harness README's §3 (which A12 made the one vocabulary). "Tooth", "gate",
"measurement stage", "press", `--resume` as in A68's preamble.*

## 1. Verdict in one page

| item | done | what changed | the evidence, re-verified here |
|---|---|---|---|
| **A3** | yes | `--tree repository` (runner and `selfcheck.py`), `repository_tree_campaign()`, the package export; the two wrong-tree teeth run on `selfcheck._campaign_elsewhere(campaign)` — the campaign under check with its `tree` pointed at the repository root, built on the spot; `ARTIFACT_NAMES["repository"]` stays (`data_provenance` names it); README §5 paragraph and both usage lines | both teeth still trip (`--selfcheck` and `--gate run_path`/`provenance`); the refusal names the constructed tree |
| **A4** | yes | `crosscheck_previous`, `_CROSSCHECK_SOURCE`, `--crosscheck-previous`, `run_all(include_crosscheck=)` — 105 lines and the one subprocess into `…_v3/`; README §8 paragraph rewritten | `composition` gate unchanged: 7 teeth, still the comparison by role at every press |
| **A5** | yes | `--lifted-from` (runner and `reproduction.py`), `input_files.stage_lifted`, `gates.REPRODUCTION_LIFTED_FROM`; `reproduction._stage_input_files` → `_resolve_input_files` (assert only); `assert_lifted`'s refusal names `--artifacts derive-inputs` instead of "until that exists" | `artifacts_derive_inputs` is the gate on the derived bytes; nothing else stages them |
| **A6** | yes | `failure.REFUSAL_MARKERS` and the text-match branch; module docstring records the condition that licensed it | `grep -rn "raise RuntimeError\|raise ValueError" PROCESS/process/core/`: 22 sites, **37** `raise ArchitectureRefusal`; every marker text that matches a raise in the copy matches an `ArchitectureRefusal` except one — §3.6 |
| **A7** | 4 of 5 | `records.schema_table`, `input_files.expected_constraint_set`, `tables.print_table`, `tally.load_json` deleted (0 references each, re-verified); the imports they alone used go with them. **`predicate.provenance_of` left**: it is under `child/` (and the `data` check pins that module's hunks) — A73's. `child.stamp_capabilities_absent` rename: left, as briefed | `harness_survey.py` §3 after: 1 definition referenced nowhere (that one) |
| **A8** | yes | `gate_records.cheapest_configuration` → `fewest_variables_configuration` (declared size, not measured cost; `chain.cheapest_configuration` keeps its name and its runner caller); `chain._pin_for` + `gate_prime._pin_for` → one `reproduction.entry_pin(config, arm, reference, *, seed=0, delta=None)`; `pool.input_file_for` → `assert_input_file_for`, built on `arms.input_file_for` | **`merged_names_check.py`** (committed): the replaced bodies, verbatim from `34c5c3e4`, against the merged ones — **24/24 (arm, configuration) pairs identical in path and kind; 3 120/3 120 pin evaluations identical** over 13 reference hex values × 3 seeds × 3 displacements |
| **A10** | yes | the probe child keeps `-P`, drops `PYTHONSAFEPATH=1`; rule (iii)'s prose untouched (C2, the user's) | `capability` tooth *"the working directory holds a package that shadows the tree"* TRIPPED |
| **A11** | yes | README: §2 "step 6 is a later task"; §4.2 "`schedule passes` is composed but never declared"; §7 item 9 "should use `seed001`"; §9 "the record's schema … are a later task"; §5 `--tree repository`. `EXPERIMENT_PLAN.md` §3.2 "Pending, refused until…" | inspection; the self-check's own sentence *"0 registry entries with no driver name"* is quoted |
| **A12** | yes | harness plan **Appendix A.1**: the twelve rules (i)–(xii) + §12, §16, plan §6 in one table with *enforced by* and *status* columns, re-read against this tree; a pointer at the head of Appendix A; the amendments' text not rewritten. README §3 is the one vocabulary (+4 rows: PROCESS, MDA, `ifail`, switch neutrality); plan §0 keeps the ruling-bearing rows (D5, D22, D19, D6) and the three queue-shorthand rows; §11.2 keeps its two ruled rows verbatim | — |
| **B2** | yes | `gate_audit.py`: `resume=False` → `resume=resume` on the doctored runs (one line, one comment) | **`--gate audit_restriction --resume`: PASS 12/0, 6/6 teeth, *runs read 21 record(s) — 12 at `61473c1d`, 9 at `f8bce151` [resumed]*; 0 runs made** (stamp survey §4.8). Improvement item 12 is discharged |
| **B5** | yes | `output_path_measurements`, `capture_contrast`, `CONTRAST_LABELS`, `contrast_*`, `print_measurements`, `_residual_vector` out of `gate_output_path.py` (1 048 → 631 lines); registry entry, imports and the module command line's two branches; `excluded_by_the_per_run_nodes` stays under its own header | gate `output_path` unchanged (4 teeth, `runs_under` untouched); `output_loop_sweeps` is a tally column (`--gate recomputation --resume` 2 066/0) |
| **B6** | yes | **158 → 148 registered teeth** (§2): the 11 per-name `capability` teeth → 1 over the registry's list; `run_path` loses the 2 teeth G7 has on a real record, keeps the 2 G7 has not; the promoted gates' *declared* lists follow | `--selfcheck` 55 → 43 teeth tripped, 0 not; §4.1 re-rendered 148/148. **Finding:** `--gate run_path` **FAILed at `34c5c3e4`** on an undeclared tooth (§3.11) |
| **B7** | yes | `--reference extract/verify/teeth`, `--previous-runs`; `reference.py` 1 424 → 750 lines (`extract_entry`, `build`, `serialise`, `stage_extract`, `stage_verify`, `stage_teeth`, `report`, `ReferenceRun.source_path`, `PREVIOUS_RUNS_SUBPATH`, `PREVIOUS_CAMPAIGN_COMMIT` and their helpers); the committed bytes, `FIELD_NAME_MAP`, `compared_fields()`, `load`, `lookup`, `summary`, `tables` stay; README §11 | `--reference show` and `--reference tables` press; GR's `count`/`hex` teeth still doctor a reference value |
| **B8** | yes | `self_containment` is a **gate** (registry name unchanged, after `edit_behaviour` in `GATE_ORDER`) with one tooth; the scan takes its file list; a declared file with nothing left to declare is a **stale declaration** and fails; a trailing comment no longer hides a code line. `exclusion_review` already sits beside G1 (its own module, A70 d1) — no registry change needed | `--gate self_containment`: PASS 53/0, tooth TRIPPED *(imports 0 → 1, findings 0 → 1, passed True → False)*; the stale-declaration check bit on `registry.py` at once (§3.13) |

**Verification** (§4), every press at the final code commit `92217de7` on a clean tree: `--selfcheck`
PASS 7/7, **55 → 43 teeth**; import walk **56 modules, 0 failures**; `--gates` differs from `34c5c3e4`
by exactly the intended lines; `--gate audit_restriction --resume` **0 runs**; `self_containment`,
`run_path`, `capability` PASS (0 runs); `recomputation --resume` 2 066/0, `run_kind_separation
--resume` 215/0; `--measure gate_table --resume` → `--plan-tables write` → `check` **IDENTICAL**
(1 796 lines), §4.1 **28 PASS 158/158 → 29 PASS 148/148**; stamp survey **184 → 184 records, 0
changed, 0 gone, 0 new**; the retired-symbol grep is empty outside heritage prose. Line count
**47 728 → 46 318 (−1 410)** by `harness_survey.py`.

## 2. Commits

| commit | content |
|---|---|
| `82b615cc` | A3, A4 (and the runner's `--lifted-from` flag, which shares the runner diff) |
| `7f353651` | A5 |
| `7c05e963` | A6 |
| `f15b4307` | A7 (four of five) |
| `eb8df761`, `6c6a8112` | A8 and `merged_names_check.py` (the second corrects where the script reads the burn-time hex; the first commit's message says "1 200 pin evaluations" — the script's own count, 3 120, is what this report cites) |
| `e5edf83f` | A10 |
| `a3b8ec75` | B2 |
| `5243400b` | B5 |
| `c2d11219` | B8 |
| `2facb3ae`, `a324547c` | B6: the checks, then the promoted gates' declared tooth lists (and the undeclared A70 tooth, §3.11) |
| `b103d525` | B7 |
| `fcf87e1b` | A11, A12 and the items' README/plan prose |
| `92217de7` | B8 follow-through: `print_self_containment` (no caller once the stage became a gate) deleted — **the final code commit; every verification press of §4 ran here** |
| `b52e40a5` | `EXPERIMENT_PLAN.md` §4 re-rendered |
| *(this report)* | |

## 3. The items, one section each

### 3.1 A3 — `--tree repository`

`repository_tree_campaign()` (22 lines, `config.py`), the runner's `--tree`, `selfcheck.py`'s `--tree`
and the `harness/__init__.py` export are gone. The survey's evidence stands as recorded (capability
FAIL 19/55 at `6a0e69f6`; not re-pressed here, the flag no longer exists to press). What the function
still served — the `provenance` check's negative control and the `run path` check's wrong-tree
refusal — is now `selfcheck._campaign_elsewhere(campaign)`: `dataclasses.replace(campaign,
tree=<repository root>)`, built from the campaign under check (rule (x)), the repository root chosen
because it is the one other directory on this machine holding a `process/` package. Both teeth trip
and the refusal names the constructed path. `Campaign.is_experiment_copy` is unchanged.
**Reversal:** restore the function from `34c5c3e4` and the two flags; one commit's diff.

### 3.2 A4 — `--crosscheck-previous`

105 lines of `selfcheck.py` (the source string, the function, the `run_all` parameter, the flag) and
the module's one `subprocess` into `MDA_partitioning_experiment_v3/`. The `composition` gate is the
live comparison (7 teeth, unchanged); the transcription it measured is frozen with V3 (D20). The
README's §8 paragraph now says it was measured once and why it cannot go stale. A stray "entry point"
section header that sat before section 6 in the file went with it. **Reversal:** restore from
`34c5c3e4`.

### 3.3 A5 — `--lifted-from`

`stage_lifted` (36 lines), `REPRODUCTION_LIFTED_FROM`, the two runner assignments and both flags.
`reproduction.stage()` loses its `lifted_from` parameter; `_stage_input_files` becomes
`_resolve_input_files`, which only asserts. The refusal in `assert_lifted` no longer says "until that
exists": it names `--artifacts derive-inputs`, whose gate checks the derived bytes against the
recorded digest (the digests and their `LIFTED_INPUT_PROVENANCE` stay). **Reversal:** restore.

### 3.4 A6 — `failure.py`'s text fallback

The grep the survey asked for, at `34c5c3e4`, over `PROCESS/process/core/`:

| | count |
|---|---|
| `raise RuntimeError` or `raise ValueError` sites | 22 — 16 in `io/` (plots, MFILE tools, input-file creation, `scan.py`), `solver/constraints.py:122` (a duplicate constraint name), and three on the run path below |
| `raise ArchitectureRefusal` sites | **37** |
| marker texts of `REFUSAL_MARKERS` matching a `raise` in the copy | "is not a recognised" → 5 `ArchitectureRefusal` + **1 `RuntimeError`** (`_idf_probe.py:101`); "refuse rather than" → 1 `ArchitectureRefusal`; "which is not present" → 5; "must not be guessed" → 1; "does not rebuild" → 2; the other four match nothing |

The three run-path `RuntimeError` sites: `caller.py:1840` is upstream's pass-cap raise, classified
`unconverged-at-cap` by its own markers before the fallback was reached; `solver/subsolve.py:229` is
the burn-time tripwire whose docstring says *"a plain RuntimeError: the run crashed on a finding"* —
`crashed` is its intended row; `_idf_probe.py:101` refuses an unrecognised `PROCESS_IDF_PROBE` mode —
the superseded probe's own guard, an instrument setting no arm composes and not an architecture
switch (those are `PROCESS_ARCH_*`, all typed). So **no untyped architecture refusal exists**, and the
fallback went (16 lines); the module docstring records the grep. The one behavioural difference: a
record whose child died on `_idf_probe.py:101` would now be filed `crashed` rather than `refused` —
which is the right row for a probe mode nobody set. All 184 records on disk are `ok`. `failure.py` is
imported by the child but is not under `child/`; no record's `failure_class` changes.
**Reversal:** restore the tuple and the branch.

### 3.5 A7 — the dead definitions

Each re-verified with `grep -rn "\bname\b"` over `*.py` and `*.md` outside `deprecated/`: one hit each,
the definition. Four deleted (33 lines) with `Iterable` (`records.py`) and `json` (`tally.py`), which
only they used. `predicate.provenance_of` (28 lines) is under `child/` **and** the `data` check
asserts that module differs from its source by exactly the recorded hunks — deleting a function
there is a run-path edit and a recorded-hunk change; **A73's**, with the rename of
`child.stamp_capabilities_absent`. The survey after: **1** definition referenced nowhere (that one).

### 3.6 A8 — one name, one meaning

- `gate_records.cheapest_configuration` → **`fewest_variables_configuration`**; its docstring now says
  what it is not (`chain.cheapest_configuration`, measured node calls). Two callers in the module,
  renamed. `chain.cheapest_configuration` and its runner caller untouched.
- `chain._pin_for` (seed and δ aware) and `gate_prime._pin_for` (its seed-0 subset) → one
  **`reproduction.entry_pin`** beside `pin_for`, whose defaults (`seed=0, delta=None`) *are* the
  subset. `chain.py` imports it lazily in the two stages that call it (as it already imported
  `reproduction` lazily); `gate_prime.py` imports `reproduction` at module level (no cycle: the
  import walk passes). `gate_entry._pin` and `gate_audit._pin` are the same function written a third
  and fourth time; **not touched** (outside the survey's list) — noted for a later pass.
- `pool.input_file_for` → **`assert_input_file_for`**: *which* file is `arms.input_file_for`'s one
  answer; the pool adds the lifted-file assertion when the answer is not the committed file.

**How the callers were checked:** `merged_names_check.py` (committed, `arch_surgery/MDA_partitioning_experiment_v4/`)
carries the three replaced bodies verbatim from `34c5c3e4` and evaluates them beside the merged ones
over every (arm, configuration) pair (24), every burn-time hex the 184 records carry (13), seeds
{0, 1, 7} and displacements {None, 0.0, 0.1}: **24/24 paths and kinds identical; 3 120/3 120 pin
values identical**; exit 0. The assertion half of `assert_input_file_for` is `assert_lifted`'s and is
not evaluated by the script (it needs the lifted file on disk); its behaviour is unchanged by
construction — the same call, on the same condition.

### 3.7 A10 — one of `-P` / `PYTHONSAFEPATH=1`

`-P` stays on the probe's command line; the environment variable went (one line, the comment
rewritten). The `capability` decoy tooth is the proof and tripped. Rule (iii)'s text still says both;
the Appendix A.1 row says what the code does and points at C2. The cross-check child that also
carried both is A4's and is gone.

### 3.8 A11 — the stale prose

Five README passages and the plan's §3.2 sentence, each replaced by the current state with its
source: step 6 → §13/§14 and `recomputation`; `schedule passes` → retired with DR1, `PROCESS_ARCH_OUTER`
on the retired list; item 9 → `seed001` is written (D24); the schema → `records.SCHEMA`, 100 fields,
`assert_usable`; `--tree repository` → §3.1's paragraph; `PROCESS_ARCH_PREDICATE` → landed with A59.

### 3.9 A12 — one rules table, one vocabulary

**Appendix A.1** of the harness plan: 15 rows (rules (i)–(xii), protocol §12 and §16, plan §6), each
with the amendment that binds it, the short text, *enforced by* (the function or tooth by name) and
*status*. Against A68's §6: (iii) now names the one flag and the retired cross-check; (vii) notes
that no body passes `resume=False` any more (B2) and that the widened identity is A72's; (x) names
`_campaign_elsewhere`; plan §6 is "mechanical since A71". (v), (vi), (xii) stay **prose only** and
point at C3. A pointer paragraph heads Appendix A; no amendment's text was rewritten.

Vocabulary: README §3 gained the four terms the plan's §0 had and it lacked (PROCESS, MDA, `ifail`,
switch neutrality) and a sentence saying it is the one table. Plan §0 keeps 4 ruling-bearing rows
(**model**/D5, **arm**/D22, **prime**/D19, **`norm_objf`**/D6) and the 3 queue-shorthand rows out of 23;
§11.2 keeps its 2 ruled rows (input file; seed/D24) **verbatim** out of 14, both tables pointing at the
README. The "decisions cited" paragraph of §0 and the switch-name paragraph of §11.2 stay.

### 3.10 B2 — improvement item 12

One line: `pool_mod.run_all([...], campaign, resume=False)` → `resume=resume`, with a four-line
comment. Each doctored job has its own directory (`<config>/in_loop`, `per_run_<unit>`), so the
record check already distinguishes it from the baseline; the doctored entry file is re-derived from
the resumed baseline's snapshot and is deterministic. **Proof:** `--gate audit_restriction --resume`
PASS 12/0, 6/6, *runs read 21 record(s) — 12 at `61473c1d`, 9 at `f8bce151` [resumed]*; the stamp
survey shows 0 records changed. The 12 runs A65's stamp survey saw re-made every press are kept.
**Reversal:** the one line.

### 3.11 B6 — 158 → 148 teeth, and what the count hid

*Caption: registered teeth by gate, before (`34c5c3e4`, `--gates`) and after (`92217de7`); only the
rows that moved. "ran" is what the check executed, "declared" what the promoted gate lists — the
framework fails the gate when they differ.*

| gate | declared before | ran before | after | change |
|---|---|---|---|---|
| `capability` | 15 | 15 | **5** | the 11 *"the retired name X present in the environment"* → 1 *"a retired switch name present in the environment, each of the registry's list in turn"*, evidence *"11 of 11 refused"* (names printed if any is not) |
| `run_path` | 14 | **15** | **13** | −2 (one ruler; attempts that do not sum — G7's `one_ruler`, `attempts_that_do_not_add_up` on a real record); +1 **declared**: A70's *"a sweep total that does not decompose…"* |
| `self_containment` | — (measurement) | — | **1** | B8 |
| **all** | **158** | 159 | **148** | |

The survey's 147 → 135 was against a table that read 147; A70 raised it to 158 (+5 copy gates, +6
`written_file_gap`), so the same −12 lands at 146, plus B8's tooth and the newly declared one: **148**.

**Finding.** A70 added the sweep-decomposition tooth to `check_run_path` and not to
`_selfcheck_gates`'s declared list; `framework.gate_from_check` fails a gate whose criterion runs a
tooth it does not declare. So **`--gate run_path` FAILed at `34c5c3e4`** — measured, not argued: a
detached scratch worktree at that commit, `experiment_runner.py --gate run_path` → `FAIL`,
`declared 14, ran 15, undeclared_teeth = ['a sweep total that does not decompose into the parts that
claim it']` (the worktree was removed afterwards). It was invisible because the relocated `run_path`
verdict in every seeded set was made at `09cc9f3e`, before the tooth, and `--measure gate_table
--resume` reads verdicts. A73's `--gate all` would have found it. Declared now; `--gate run_path`
PASS 13/13. The two G7 teeth I removed here are on a real record and stay G7's; the two kept
(partial decomposition, sweep decomposition) have no G7 counterpart and adding them there would cost
a G7 press (its own tooth re-makes one run by design), which this task may not make — **the
summation family is split by that reason, stated in the check's comment**.

### 3.12 B5 and B7 — two stages retired

B5: 417 lines out of `gate_output_path.py`; the excluded set G2/G3 and G4 import keeps its section
header, which now says where the two halves of the retired measurement live (`output_loop_sweeps` in
the tally; the written-file question in `written_file_gap`). B7: 674 lines out of `reference.py`; the
runner's `_run_reference_stage` keeps `show` and `tables`; `load()`'s refusal no longer tells a reader
to run `--extract`. `ReferenceRun.source_path` and the two directory-spelling constants went with the
extraction (the committed entries carry `source_path` as data). README §11's re-derivation section
is now "How to read it", and says which GR teeth still doctor a reference value (`count`, `hex`).
The retired stages' records on disk: `runs/gates/output_path_measurements/measurements.json` and
`runs/gates/self_containment/measurements.json` had no writer and no reader and were moved out of
`runs/` to the session's scratch directory (A70 §5.4's precedent); the six contrast **run** records
under `runs/gates/output_path/contrast/` were left — they are stamped run records, and removing them
would make the stamp survey read "6 disappeared" for a change that made no run. A73's from-scratch
press drops them.

### 3.13 B8 — `self_containment` as a gate

`scan_self_containment(files, *, relative_to)` takes its file list; `self_containment(campaign)` is
the body (criterion, population, `n_compared` = files, `n_mismatched` = findings + imports + stale
declarations); `self_containment_gate` registers it. **The tooth** writes
`a_scratch_module_for_the_tooth.py` in a temporary directory — never inside the package — containing
`from arch_surgery.idf_probe import run_one  # the tooth's import`, widens the scanned *list* by that
one file and requires imports +1, findings +1, files +1, the scratch file named on both lists and
`passed` False. It tripped: *imports 0 → 1, findings 0 → 1, files 53 → 54, passed True → False*.

Two things the promotion found:

1. **The tooth's first run did not trip** (*findings 0 → 0*): `_docstring_and_comment_lines` counted
   any line carrying a comment token as prose, so a code line with a trailing comment — the tooth's
   import line — was classified "heritage". A comment now makes a line prose only when nothing
   precedes it on the line. On the real package the change moved no count (46 hits, 13 executable,
   before and after).
2. **Stale declarations.** `DECLARED_OUTSIDE_REFERENCES` is keyed by file name and a declared file
   with no executable hit was silently fine — so `reference.py`'s declaration had been stale since it
   was written (its lines name `…_v3/runs`, not either forbidden directory). The gate now fails on a
   declared file with nothing left to declare, and **bit at once on `registry.py`** after the
   stage's sentence moved into `gates.py`'s `binds=`. Declarations after: `data_provenance.py`,
   `gates.py`, `input_files.py` (rewritten: the hit is the digest provenance list, not the
   `--lifted-from` message the old text described), `ystate.py`. Gone: `config.py` (A3),
   `selfcheck.py` (A4), `reference.py` (stale), `registry.py` (moved).

`exclusion_review` "beside G1": it is in its own module beside `gate_neutrality.py` (A70 d1) and is
the first measurement stage the registry lists; no one-line registry change would move it further.

## 4. Verification, in the brief's order

All at **`92217de7`** on a clean tree (`git status --short | wc -l` = 0; the §4 render was stashed
for the presses, found byte-identical to `--plan-tables write`'s output, and committed after as
`b52e40a5`). Nothing else ran concurrently.

1. **`--selfcheck`**: PASS, 7/7 checks; teeth **55 → 43** tripped, 0 not tripped. Baseline at
   `34c5c3e4`: PASS, 7/7, 55.
2. **Import walk** (`pkgutil.walk_packages` over `harness` + the five top-level scripts, from `/tmp`):
   **56 modules, 0 failures** (55 + `merged_names_check.py`).
3. **`--gates`** against `34c5c3e4`: `28 gate(s) and 7 measurement stage(s)` → `29 gate(s) and 5
   measurement stage(s)`; `+ self_containment [harness] 1 teeth no PROCESS run` after `edit_behaviour`;
   `run_path 14 → 13 teeth`, `capability 15 → 5 teeth`; `− output_path_measurements`, `−
   self_containment` (as a stage). Every other line byte-identical.
4. **Gates**, 0 PROCESS runs each: `audit_restriction --resume` PASS 12/0, 6/6, **21 records read, all
   kept** (B2's proof); `self_containment` PASS 53/0, 1/1; `run_path` PASS 12/0, 13/13; `capability`
   PASS 55/0, 5/5; `recomputation --resume` PASS **2 066/0**, 9/9, *36 records — 33 at `f8bce151`, 3 at
   `7ad8ea04`*; `run_kind_separation --resume` PASS 215/0, 6/6, *184 run records under `runs/`, 31 in a
   declared source*.
5. **`--measure gate_table --resume`** → **29 PASS, 0 FAIL, 0 not run; 148 of 148 teeth**;
   **`--plan-tables write`** → 1 796 lines replacing 1 796; **`--plan-tables check`** → 1 796
   identical, 0/0, **IDENTICAL**. §4.1 changed by exactly: the `self_containment` row, `run_path`
   14/14 → 13/13 (and its population "4 refusals" → "5 refusals", the re-run verdict's own string),
   `capability` 15/15 → 5/5, the summary line. §4.2–§4.4 unchanged.
6. **Stamp survey** (`run_stamp_survey.py --against`): **184 records then, 184 now; 0 whose commit
   changed, 0 disappeared, 0 new.** Histogram unchanged (127 `f8bce151`, 16 `61473c1d`, 12 `b784158c`,
   11 `3d64625c`, 6 `09cc9f3e`, 6 `fd480aff`, 3 `47be2b0d`, 3 `7ad8ea04`). **This task made no PROCESS
   run.**
7. **Grep** over `*.py`/`*.md` outside `deprecated/` for every retired symbol and flag
   (`repository_tree_campaign`, `--tree repository`, `crosscheck_previous`, `_CROSSCHECK_SOURCE`,
   `lifted_from`/`--lifted-from`, `stage_lifted`, `REPRODUCTION_LIFTED_FROM`, `REFUSAL_MARKERS`,
   `schema_table`, `expected_constraint_set`, `print_table`, `load_json`, `PYTHONSAFEPATH`,
   `output_path_measurements`, `capture_contrast`, `--previous-runs`, `stage_extract`, `stage_verify`,
   `print_self_containment`): **empty in code**; the remaining hits are heritage sentences that record
   the retirement (`switches.py:774`, `gate_output_path.py:12, 568`), rule (iii)'s text and the A.1 row
   that quotes it (C2's), and the queue's own rows. `merged_names_check.py` names the old
   `pool.input_file_for`/`gate_prime._pin_for` in its docstring on purpose.
8. **`harness_survey.py`** (`--records runs/gates`), before → after:

   | | `34c5c3e4` | `92217de7` |
   |---|---|---|
   | lines total / code / docstring / comment / msg | 47 728 / 34 338 / 6 883 / 3 135 / 8 468 | **46 318** / 33 179 / 6 782 / 3 097 / 8 175 |
   | `gates/` | 18 129 | 16 912 |
   | definitions referenced nowhere | 5 | **1** (`predicate.provenance_of`) |
   | gates / teeth / measurement stages | 28 / 158 / 7 | **29 / 148 / 5** |
   | same-name pairs | 58 | 55 |

   By module: `reference.py` 1 424 → 750, `gate_output_path.py` 1 048 → 631, `selfcheck.py` 2 423 →
   2 281, `experiment_runner.py` 1 111 → 1 055, `registry.py` 879 → 827, `input_files.py` 816 → 762,
   `config.py` 461 → 440, `failure.py` 112 → 96, `chain.py` 1 352 → 1 329; `gates.py` 1 158 → 1 212
   (the gate and its tooth are longer than the stage), `pool.py` 595 → 600, +143 `merged_names_check.py`.
9. **Lint** (ruff F401/F811/F821/F841 from a read-only sibling environment, an isolated config): the
   17 pre-existing findings at `34c5c3e4` are the 17 after; none added, none of the old ones touched.

## 5. Autonomous decisions, each with its reversal

| # | decision | reversal |
|---|---|---|
| d1 | `_campaign_elsewhere` points at the repository root rather than a temp directory: the one other `process/` package on the machine, the shape a wrong tree actually has | `replace(campaign, tree=Path(tempfile.mkdtemp()))` |
| d2 | A6 went ahead with `_idf_probe.py:101` untyped: a probe-mode guard, not an architecture refusal, and no arm sets the variable | restore `REFUSAL_MARKERS` with that one text |
| d3 | `entry_pin` lives in `reproduction.py` beside `pin_for`, not in `chain.py` or `arms.py`; `gate_entry._pin`/`gate_audit._pin` left alone (not in the survey's list) | inline; or point the other two at it (a fifth caller for `merged_names_check.py`) |
| d4 | `merged_names_check.py` committed as a standalone script beside `harness_survey.py` rather than as a tooth: the comparison is against bodies that no longer exist in the tree | delete it once A71 is merged and the equivalence is history |
| d5 | B6's non-duplicated `run_path` teeth stay in the self-check rather than moving to G7 (a G7 press makes one run by design) | add them to `gate_records._teeth` and press G7 at A73 |
| d6 | the stale-declaration check is part of `self_containment`'s criterion (a FAIL), not a note | move `n_stale_declarations` out of `passed` |
| d7 | the trailing-comment fix to `_docstring_and_comment_lines` | revert the four lines; the tooth then does not trip |
| d8 | the two dead stage records moved out of `runs/`; the six contrast run records left in | copy back from scratch / delete the contrast directory |
| d9 | plan §0 keeps the three queue-shorthand rows (D/I/A, protocol §, trap T) that README §3 has no reason to carry; README §3 gains PROCESS, MDA, `ifail`, switch neutrality | drop the rows either way |
| d10 | `print_self_containment` deleted after the promotion (0 callers) | restore and give the gate a `printer` |
| d11 | A70's undeclared tooth declared here rather than left for A73 | remove the line; `--gate run_path` FAILs again |

## 6. Limits

- **No `--gate all`** (D27). G1, G2, G3, G5, G6, G7, G8, G9, GR and the artifact gates were not pressed
  on this tree; their bodies changed only where an item says (G4's one line; GR's `stage()` signature
  and `_resolve_input_files`; G2's pin call). The import walk shows every module importable; a body
  that runs only under `--gate all` has not executed since the change.
- **`assert_input_file_for`'s assertion half** is not exercised by `merged_names_check.py`; it is the
  unchanged `assert_lifted`, gated by `artifacts_derive_inputs` at A73's press.
- **A6's condition was checked by grep and by reading three sites**, not by driving a refusal
  through a child; no record with a refusal exists on disk (all 184 are `ok`).
- **B2's proof is a `--resume` press over kept records.** A from-scratch press (A73) is where the
  doctored runs are made once and the *next* resume keeps them — the case measured here has the
  records already at two commits.
- **The tooth count "159 ran before"** is inferred from the A70 finding (declared 14, ran 15 on
  `run_path`) plus the other gates' declared counts; it was not measured as one number.
- **`harness_survey.py`'s "top-level scripts" row** does not include `merged_names_check.py` (the
  script's list is fixed); the module table in §4.8 does.
- **Prose inside the edited modules** that says "this stage" or "measurement" for `self_containment`
  was re-read in `gates.py` and `registry.py`; other modules' docstrings that mention the retired
  flags were not audited line by line beyond the grep in §4.7.

## 7. What the queue, the harness plan and the improvement list should gain (not edited here)

- **Improvement list, item 12**: **discharged** by B2 (`a3b8ec75`); the proof is §3.10. **Item 13**
  (G1's resume press rewrites the `after` manifest's commit) is **not this task's** and is not trivial
  from here: the manifest write is in `gate_neutrality._capture_after` and changing what it stamps is
  a verdict-record contract question for A73's press, where G1 actually runs.
- **Queue row A71**: MERGED with §1's numbers; the finding of §3.11 (`--gate run_path` FAILed at
  `34c5c3e4` on A70's undeclared tooth; declared here). **A73**: its `--gate all` is the first press
  of `run_path` from the button since A70, and of `self_containment` as a gate; `predicate.provenance_of`
  and `child.stamp_capabilities_absent` are its (A7's leftovers); the six contrast run records drop
  from the relocated set. **A72**: `assert_input_file_for` and `entry_pin` are the names now.
- **Harness plan**: Appendix A.1 is in; the change log should gain an amendment line for A71 (rule
  (vii)'s `resume=False` gone; plan §6 mechanical; item 12 discharged). C2's row in A.1 states what
  the code does now (probe: `-P` only).
- **README**: edited (§0 layer 5, §2, §3, §4.2, §5, §7, §8, §9, §10.1, §11).
- **`TRAPS.md`**: nothing new. One near-trap for the plan rather than the trap file: a promoted
  self-check's *declared* tooth list is a second copy of the check's teeth, and the framework's
  refusal on a mismatch is what makes the copy safe — it fired here on a tooth A70 added three days
  ago, and only because a gate that reads verdicts (`gate_table`) cannot see it.

## 8. Change log

| date | change |
|---|---|
| 2026-09-14 | Created at branch tip `b52e40a5` (code final at `92217de7`). Fourteen items; 13 done, A7 4 of 5 with the fifth named for A73. 0 PROCESS runs. |

---

## Orchestrator's critical assessment (protocol §5)

*Written 2026-09-14 at the branch tip `5ba21fd8`, before the merge. Checks chosen to differ from the
agent's.*

1. **A6's precondition, re-grepped by me.** Four untyped raises remain in the copy's driver:
   `caller.py:1840` (upstream's output-loop pass cap — `failure.py` keeps its own marker for that,
   `UPSTREAM_PASS_CAP_MARKERS`, which is a taxonomy row, not a refusal), `subsolve.py:229` (the
   deliberate tripwire), `constraints.py:122` (a duplicate-registration guard, set by no switch), and
   `_idf_probe.py:101` (the superseded probe's mode guard). None is an architecture refusal; 37 sites
   raise `ArchitectureRefusal`. The removed fallback was `REFUSAL_MARKERS` only. Correct.
2. **On a trial merge onto trunk (`34c5c3e4`)**: clean; import walk 51 modules, 0 failures; the
   registry has 34 entries (29 gates + 5 stages); **`--gate run_path` PASSes on the record-less merged
   tree** — the gate the agent found FAILing at the base for an undeclared tooth, now declared.
3. **The `run_path` finding is the important one and is a process lesson.** A70 added a tooth to a
   gate's check without adding it to the gate's declared list; the framework refuses that, which is
   right, but every seeded verdict predated the tooth and `gate_table --resume` reads verdicts, so
   the FAIL was invisible to A70's own presses and to my assessment. A gate whose *code* changed must
   be pressed once even when its records are kept; goes to the harness plan as a rule at the merge.
4. **B7 kept `--reference show/tables`** and retired only `extract/verify/teeth`, as specified. The
   committed reference is still readable from the button.
5. **A8's equivalence** is proven by a committed script over every (arm, configuration) pair and
   3 120 pin evaluations — the right form for a merge of two bodies.
6. **The `git add -A <paths>` slip** was caught and undone by the agent before committing; recorded, no
   effect on the tree.
7. **0 PROCESS runs**, consistent with the stamp survey (184 → 184) and every listed press being
   0-run or on kept records.

**Approved for merge.**
