# A68 (harness-simplification-survey) — where the V4 harness can be simplified

> **Document status** — **OPEN TASK REPORT · INVESTIGATION ONLY.** Written 2026-09-14 by task
> **A68 (harness-simplification-survey)** on branch `A68-harness-simplification-survey` off
> `architecture_surgery` at `6a0e69f6`. Nothing was implemented, no queue, plan or improvement-list
> file was edited, and **no PROCESS run was made**. Every number below comes from one committed
> script, `arch_surgery/MDA_partitioning_experiment_v4/harness_survey.py` (committed at `dd3f6ee4`,
> run at that commit), except where a sentence names another committed script and the flag it was
> run with. Folder position records lifecycle, not validity (trap T3).

**The question (the user, 2026-09-14):** *"investigate where the whole v4 harness can be simplified
… compile a list of simplification items, with impact, risk and associated costs (what functionality
is sacrificed)."*

**Vocabulary, spelled out once** (protocol §4). *Gate*: a check with a verdict that must pass before
a number is believed; *tooth*: a deliberate break a gate must catch before its zeros are believed
(protocol §12); *measurement stage*: a stage that publishes numbers and has nothing to pass; *the
tally*: the code that turns run records into the plan's §4 tables; *the analysis*: the declared second
implementation of the same tables, compared cell by cell by gate `recomputation`; *press*: one
invocation of `experiment_runner.py --gate all`; *`--resume`*: keep a run whose directory holds a
complete record of the same job; *D-n / I-n / A-n*: a user ruling, a filed issue, a queue task in
`MASTER_TODO.md`; *T-n*: a trap in `TRAPS.md`; *amendment n, rule (k)*: the harness plan's Appendix A.

---

## 0. Verdict in one page

**Where the bulk is.** The harness is **46 973 lines** (43 516 under `harness/` plus the four
top-level scripts), against the plan's estimate of ≈ 6 570 — **7.2×**. Of that, **18 173 lines
(39 %) are prose**: 6 638 docstring, 3 097 comment, 8 438 lines lying wholly inside a string literal
(refusal messages, captions, printed sentences). Logic is roughly 25 500 lines. One module,
`gates/gates.py`, is **6 899 lines** and holds four gates, five measurement stages, the registry, the
gate table and the printers. Dead code is negligible: **5 of 795** module-level definitions (61
lines) are referenced nowhere. The harness is not bloated by accident; it is large because almost
every construction is a refusal, a stamp or a second check that a report says was earned. What
*can* be simplified is mostly (a) structure, (b) instruments that were built for a driver task and
are now computed again by the tally and the analysis, (c) runs a press re-makes although another
gate's directory already holds the bit-identical record, and (d) flags and prose that describe a
harness that no longer exists.

**Headline measurements** (`harness_survey.py` at `dd3f6ee4`, records read from
`idf_probe/runs/A65_runs/gates/` in the main checkout, read-only):

| what | measured |
|---|---|
| lines: total / code / docstring / comment / message strings | 46 973 / 33 963 / 6 638 / 3 097 / 8 438 |
| largest module | `gates/gates.py` 6 899 (1 829 message lines) |
| module-level definitions / referenced nowhere | 795 / **5** (61 lines) |
| function names defined in more than one module | 55 (most deliberate — see §5) |
| functions with byte-identical bodies (name-normalised, ≥ 6 lines) | 12 pairs, **9 of them `analysis.py` ↔ `stats.py`** |
| gates / teeth / measurement stages | 25 / 147 / 9 |
| gates that start PROCESS / that do not | 13 / 12 |
| record fields declared / named by no reader outside `records.py` and the writer | 100 / **9** (all provenance stamps) |
| run records per full press (A65's relocated set) | **170**, in-child wall 2 313 s (context only, T5/I-10) |
| of which bit-identical re-makes of a run another gate directory holds, excluding 23 second runs a gate makes by design | **44 (26 %)**, 396 s |
| runner flags / not mentioned in the README | 33 / **11** |
| measurement stage records nothing reads (grep over harness, runner, plans) | **5** of 9 (`predicate_counters`, `attempts`, `output_path_measurements`, `exclusion_review`, `self_containment`) |
| `--selfcheck --tree repository` (allowed press, `harness/gates/selfcheck.py` at `6a0e69f6`) | **FAIL — capability 19 of 55 mismatched**: the repository tree does not implement the V4 switch names since A56 |

**Tier counts.** **A (safe now, pure refactor): 12 items. B (changes what the button says;
orchestrator's call under D24): 8 items. C (touches a ruling or a binding rule; the user): 4
items.** Nothing in tier A changes a measurement, a gate criterion or a PROCESS run count.

**The five with the largest measured impact, in one line each:**

1. **A1 — split `gates.py`** (6 899 lines → eight modules by its own `# ----` sections; 0 behaviour
   change; A65 measured that a pure move re-makes 0 runs). Risk: path strings in source scanners
   (`analysis.FORBIDDEN_IMPORTS`, `self_containment`'s file list) — the hazard A65 hit once.
2. **B1 — a shared run pool** (44 of 170 records per press are bit-identical re-makes; 396 s
   in-child). Risk: T12/T13/T14 and amendment 21 rule (xi); precondition: `records.is_complete_for`
   must compare the whole job identity (today it ignores δ, predicate mode, pin, stencil column and
   overrides — a latent hazard hidden only by directory layout).
3. **A2 — retire the two driver-task measurement stages `predicate_counters` and `attempts`**
   (892 lines, 0 PROCESS runs, 0 readers) whose every column the tally and the analysis compute
   again and gate `recomputation` verifies. Risk: one identity (`_reconcile_sweeps`) lives only
   there and must move into the record contract.
4. **B2 — improvement item 12, G4's `resume=False`** (12 PROCESS runs and ≈ 112 s per press for one
   argument). Risk: none once the job identity is checked (each doctored run has its own directory).
5. **A3 + A4 — retire `--tree repository`, `repository_tree_campaign()` and `--crosscheck-previous`**
   (≈ 170 lines, a README section, one runner flag): the flag's documented purpose — "does the
   harness still compose against the tree the earlier revisions measured?" — is unreachable since
   the switch rename, measured as capability FAIL 19/55. Risk: none to any gate.

**Do not simplify** (§5): the two snapshot positions; the second implementation; the census stamps;
the run-kind separation; the exact-tree assertion; the derived restore and its `numerics` hold-back;
per-run isolation; G1's leaf-named exclusions; the switch-by-switch second run of G5; the
before/after two-commit structure of G1; the committed reference's bytes; the `--resume` schema
contract; the two compositions of the cold chain; `retried` derived from `attempts[]`.

---

## 1. Method — what was measured and how

`harness_survey.py` (committed `dd3f6ee4`; run as
`python harness_survey.py --records <main checkout>/arch_surgery/idf_probe/runs/A65_runs/gates --json …`)
measures nine things and prints them:

1. **lines** per module and subpackage — total, blank, comment-only, docstring (`ast` decides),
   and *message* lines (lines lying wholly inside a non-docstring string literal); plus
   `gates.py` sized by the blocks between its own `# ----` rule comments.
2. **imports** — the intra-package graph; modules nothing imports.
3. **definitions** — every module-level function/class and how many *other* source sites mention
   its name (docstrings and comments stripped first). Zero is a candidate, read before it is called
   dead.
4. **duplicates** — same name in two modules; identical bodies after normalising the name away.
5. **registry** — the 25 gates and 9 stages as the package builds them: teeth, `needs_runs`,
   `reads_from`, `reads_records`.
6. **records** — the 100 declared fields of `records.SCHEMA` against every reader outside
   `records.py`, by full path and by last path segment.
7. **runs per press** — from the relocated records of the last merged task: records per gate
   directory, their `tree_git_head` values, run kinds, entry points, `wall_s` sums (context only);
   and the sharper question: records whose (arm, configuration, seed, regime, composed environment,
   audit position, node calls, dispatch sweeps, objective hex) are identical to another record's in
   the same set, with the second runs a gate makes *by design* counted apart (G1's before capture,
   G5's switch-by-switch run, G4's in-child-doctored runs, the diagnosis stage's runs).
8. **flags** — the 33 `--flags` of `experiment_runner.py` against the README, the two plans, the
   improvement list, the assessment and the 19 archived A47–A65 reports.
9. **prose** — docstring+comment share per module; README paragraphs found verbatim elsewhere.

One further press was made because a claim needed it: `harness/gates/selfcheck.py --tree repository
--json …` at `6a0e69f6` (an allowed press; it starts no PROCESS run). Its verdict is quoted in A3.

Everything else is inspection: reading the modules, the plans, the 22 amendments and the archived
reports (two read-only research passes over A47–A65 fed §4 and §5's "reason it exists" columns).

---

## 2. Where the bulk is

*Caption: one row per subpackage (A65's grouping). "code" is every line that is neither blank,
comment-only nor docstring; "msg" is the subset of code lines lying wholly inside a string literal —
refusal messages, captions, printed sentences. Population: every `.py` under `harness/` plus
`experiment_runner.py`, `PROCESS_diff.py`, `run_stamp_survey.py`, `PROCESS/copy_gates.py`. Source:
`harness_survey.py` §1 at `dd3f6ee4`.*

| subpackage | total | code | docstring | comment | blank | msg |
|---|---|---|---|---|---|---|
| `gates/` | 17 680 | 13 244 | 1 866 | 1 450 | 1 120 | 3 554 |
| `measurement/` | 8 729 | 6 381 | 1 416 | 316 | 616 | 1 442 |
| `child/` | 7 111 | 4 956 | 1 185 | 454 | 516 | 1 185 |
| `experiment/` | 4 485 | 3 167 | 631 | 317 | 370 | 748 |
| top-level scripts | 3 457 | 2 768 | 326 | 125 | 238 | 782 |
| `core/` | 2 887 | 1 700 | 648 | 297 | 242 | 350 |
| `harness/` top (`__init__`, `chain`, `ystate`) | 2 624 | 1 747 | 566 | 138 | 173 | 377 |
| **all** | **46 973** | **33 963** | **6 638** | **3 097** | **3 275** | **8 438** |

**`gates.py` by its own sections** (lines; `harness_survey.py` §1):

| section | lines | what it is |
|---|---|---|
| G1 — switch neutrality + the earlier capture's vocabulary | 665 + 1 090 = **1 755** | gate G1, its comparator, translation through `FIELD_NAME_MAP`, 9 teeth |
| G8 — the predicate trial | 857 | gate |
| the gate table, ordering, printers, `main` | 628 | registry output |
| the exclusion sets, reviewed | 554 | measurement stage, **no reader** |
| G9 — the output path | 501 | gate |
| the output path, measured | 455 | measurement stage + 6 contrast optimisations, **no reader** |
| the per-sweep overhead, counted | 446 | measurement stage, **no reader**, content also in the tally |
| the retry ladder, per attempt | 446 | measurement stage, **no reader**, content also in the tally |
| the harness's own checks, promoted | 288 | registry |
| self-containment, measured | 241 | measurement stage, **no reader**, a requirement that cannot fail |
| entry references, GR wrapper, G0′, registries, measurements() | 110 + 112 + 109 + 53 + 48 + 19 + 95 + 79 = 625 | glue |

Five of the nine measurement stages write a record that nothing in the harness, the runner or the
plans reads (`grep` for their paths: 0 hits outside `gates.py`). Their content is printed at
`--measure` time and served a task report once.

**Where the runs are** (`harness_survey.py` §7; 170 records, A65's relocated set):

| gate directory | runs | in-child s | distinct jobs | commits |
|---|---|---|---|---|
| `reproduction` (GR) | 30 | 686 | 28 | one |
| `predicate_mode` (G8) | 27 | 16 | 15 | one |
| `audit_restriction` (G4) | 18 | 112 | 6 | two (12 re-made every press — item 12) |
| `output_path` (G9 + contrast) | 17 | 521 | 11 | two |
| `cold_chain` (G3) | 16 | 9 | 4 | one |
| `entry_and_warm` (G6) | 16 | 113 | 16 | two (A64's 3 new) |
| `prime_map` (G2) | 12 | 6 | 6 | one |
| `switch_neutrality` (G1) | 12 | 183 | 6 | two, by design |
| `exit_audit_diagnosis` | 11 | 444 | 9 | one, **outside `--gate all`** |
| `switch_composition` (G5) | 6 | 212 | 3 | one |
| `entry_references` | 3 | 3 | 3 | one |
| `record_completeness` (G7) | 2 | 10 | 2 | two (1 re-made by design) |

61 distinct (entry point, arm, configuration, seed, regime, δ, mode) jobs produce 170 records.
**44 records are bit-identical re-makes** of a run another gate directory already holds — same
composed environment, same audit position, same node calls, sweeps and objective hex — after setting
aside the 23 second runs that are the gate's point (G1 before/after at two commits; G5's
switch-by-switch run; G4's twelve in-child-doctored runs; the diagnosis stage). The largest groups:
the cold Phase A reference `A0` seed 0 made **three times** per configuration (`entry_references`,
GR's `phase_a_reference`, G8's `reference`); the perturbed `A0`/`A1` seed 1 made **three times** (G6 pairing, G8
`frozen`, GR); the warm `A1` seed 0 made three times (G4 baseline, G6 warm, G2 `prime_on`); `B3`
seed 0 made three times (G4 optimisation, G9, G5 from-the-matrix); `BR` seed 0 made three times at
one commit (G9, the contrast's `with_loop`, G1's after capture).

---

## 3. The ranked table

*Caption: one row per item; ranked within tier by impact over risk. "impact" is measured (lines from
`harness_survey.py` §1/§3/§4; runs and seconds from §7; teeth from §5) — never a guess; "seconds"
are in-child `wall_s` sums and are context only (I-10, T5). "risk" names the gate, tooth, trap, ruling
or amendment rule the change weakens and how a regression would then go unnoticed. "cost" is what
the button can no longer say or a reader can no longer check; "nothing" is argued in §4. "kind":
refactor = no measurement, gate criterion or run count changes; button = changes what a press
makes or prints; ruling = touches a D-row or a binding rule. "evidence" names the measurement or
gate result showing the thing unnecessary, or says "judgment".*

### Tier A — safe now, pure refactor

| # | item | impact | risk | cost | kind | evidence |
|---|---|---|---|---|---|---|
| A1 | split `gates/gates.py` along its own sections: `gate_neutrality.py` (G1, 1 755), `gate_predicate_mode.py` (G8, 857), `gate_output_path.py` (G9, 501), `registry.py` (registries, ordering, gate table, printers, ≈ 1 100), the stages of A2/B5/B8 into `measurement/` | 6 899 lines → 8 modules of ≤ 1 800; 0 runs; 0 behaviour | source scanners that hold path strings (`analysis.FORBIDDEN_IMPORTS`, `self_containment`, `recomputation`'s independence check) — A65 §4 had to rewrite one or the gate "passes vacuously"; `runs_under` strings must travel unchanged (T12) | nothing: every gate keeps its name, criterion, teeth, record path | refactor | A52 §9 d3 already put five gates in their own modules "because `gates.py` is 4 000 lines"; A65: a pure move re-made 0 runs, G1 byte-neutral |
| A2 | retire measurement stages `predicate_counters` and `attempts` (in `gates.py`), moving their one unique identity, `_reconcile_sweeps` (block + empty + dispatch sweep decomposition), into `records.assert_attempt_summation`'s neighbourhood | −892 lines; 0 runs (they read GR's); 2 fewer `--measure all` records | none to a gate: the same columns are the tally's `per_sweep_overhead` (both phases) and `attempts` tables and the analysis's recomputation of them, verified by `recomputation` (2 066 cells, 0 mismatched at A64) | the printed per-run counter dump at `--measure` time; the sweep-decomposition identity unless moved | refactor | §7 of the survey: 0 readers of either record; tally columns `dispatch_sweeps`, `output_loop_sweeps`, `coupling_evaluations`, `coupling_components`, `upstream_*`, `empty_sweep_share` are the stage's `_counter_row` keys under other names |
| A3 | retire `--tree repository` and `repository_tree_campaign()`; keep `Campaign.is_experiment_copy` and its two teeth (a constructed campaign at another path still exercises them) | −≈ 60 lines in `config.py`/runner/`selfcheck.py`; README §5 paragraph; `ARTIFACT_NAMES["repository"]` **stays** (read by `data_provenance` for the source names) | none: no gate reads it; the `provenance` selfcheck's positive/negative control is a constructed `Campaign` | the question "does the harness compose against the repository's tree?" can no longer be asked — and cannot be answered today | refactor | `selfcheck.py --tree repository` at `6a0e69f6`: **capability FAIL, 19 of 55 mismatched** (the root `process/` has no `MDA_MODE`; the copy has 16 mentions) |
| A4 | retire `selfcheck.crosscheck_previous`, `_CROSSCHECK_SOURCE` and the `--crosscheck-previous` flag of `selfcheck.py` (executes V3's `v3_runner.env_for` in a subprocess) | −≈ 110 lines; one fewer subprocess into `…_v3/` | none: it is opt-in, off the button, and not one of the 147 teeth; the transcription it verified is compared at every press by the `composition` gate (42 compared, 7 teeth) | the transcription of V3's composition is no longer re-measurable against V3's code — which is frozen (D20), so it cannot go stale | refactor | A47 §5 #8's own reversal path is "delete `crosscheck_previous`"; V3's functions compose V3's switch names, which the copy refuses since A56 |
| A5 | retire `--lifted-from`, `input_files.stage_lifted`, `gates.REPRODUCTION_LIFTED_FROM`; reword the refusal in `assert_lifted` that still says "until that exists" | −≈ 40 lines; 1 flag; a stale sentence | none: the lifted files are derived by `--artifacts derive-inputs` and their digests gated (`artifacts_derive_inputs` PASS 2/2 every press) | staging a previous revision's derived files by hand — a pre-A51 path | refactor | flag survey: 0 README mentions, 18 in A49/A50-era reports; the refusal's own text names A51 as the thing that will replace it |
| A6 | remove `failure.py`'s message-text fallback (`REFUSAL_MARKERS` and the `any(marker in text …)` branch) | −≈ 15 lines | G7's taxonomy: a refusal raised untyped by the copy would land in `crashed`, not `refused`. Check first: `grep -n "raise RuntimeError" PROCESS/process/core/` at the refusal sites (A56 said 34 sites raise `ArchitectureRefusal`) | nothing, if the grep finds no untyped refusal site | refactor | the module's own docstring: "kept as a fallback, and is marked for removal"; A50 §6 / A56 §5 state the deletion condition (typed refusal landed, A56) |
| A7 | delete the 5 unreferenced definitions: `predicate.provenance_of` (28), `records.schema_table` (4), `input_files.expected_constraint_set` (14), `tables.print_table` (9), `tally.load_json` (6); rename `child.stamp_capabilities_absent` (it stamps nulls, nothing is "absent") | −61 lines | none | nothing | refactor | survey §3: 0 mentions outside the definition, docstrings and comments excluded |
| A8 | one name, one meaning: `cheapest_configuration` means "cheapest by measured node calls" in `chain.py` and "fewest iteration variables" in `gate_records.py`; `_pin_for` in `gate_prime.py` is a strict subset of `chain._pin_for`; `pool.input_file_for` is `arms.input_file_for` plus `assert_lifted` | 3 renames / 2 merges, ≈ 30 lines | none | nothing | refactor | survey §4: 55 same-name pairs, these three are same name, different or nested meaning |
| A9 | register `copy_identity` and `edit_behaviour` (now run only by `PROCESS/copy_gates.py main`) in the harness registry as 0-PROCESS-run gates like `g0prime`; retire `copy_gates.py`'s own `main`/`report`/record writing (the criteria stay, loaded by path); give `edit_behaviour` a tooth or make it a measurement (it has **0 teeth** today — a gate the framework would refuse) | one gate runner instead of two; `--gate all` covers the copy gates; the 4 legacy verdict records without `tree_git_head` (A63 §5 d3) go | none; `smoke_import` (0 teeth) is subsumed by the capability probe | nothing: `copy_gates.py all` is a second button for three checks | refactor | A65 records: `copy_identity`, `edit_behaviour`, `frozen_physics`, `smoke_import` verdicts carry no commit; `frozen_physics` is `g0prime` already |
| A10 | keep one of `-P` / `PYTHONSAFEPATH=1` on the probe child; correct rule (iii)'s scope in prose (see C2) | 1 line | none | nothing | refactor | A52 §9 d13: "either alone would do" |
| A11 | stale prose in the README: §2 "step 6 is a later task" (line 54); §4.2 "`schedule passes` is composed but never declared … disappears from the driver when …" (370–380; A56 closed it and §7.2 says so); §7 item 9 "should use `seed001`" (done, D24); §9 "the record's schema … are a later task" (708); §5 "`--tree repository`" paragraph (A3); `EXPERIMENT_PLAN.md` §3.2 "Pending, refused until its driver change lands: `PROCESS_ARCH_PREDICATE` (A59)" (landed) | 5 passages | none | nothing | refactor | inspection (`grep -n "later task\|composed but never declared\|Pending, refused"`) |
| A12 | the harness plan's rules (i)–(xii) are scattered over amendments 13, 16, 19, 20, 21, 22 (333 lines of Appendix A); give them one table with an *enforced by* column (§6 below is that table); the vocabulary is defined three times (README §3, 41 rows; plan §0, 23 rows; plan §11.2, 14 rows) — make README §3 the one and the others point at it | prose only | none | nothing | refactor | §6 of this report; `wc`/row counts by inspection |

### Tier B — changes what the button makes or says; the orchestrator's call under D24

| # | item | impact | risk | cost | kind | evidence |
|---|---|---|---|---|---|---|
| B1 | **a shared run pool**: one directory per distinct job identity under `runs/gates/_runs/`; a gate's `runs_under` lists the jobs it reads; verdicts carry the paths. **Precondition:** `records.is_complete_for` (and `pool.Job.key`) compare δ, predicate mode, pin hex, stencil column/sign, `override_env`, `reproduction_overrides` and audit position — today they compare arm, configuration, seed, phase, regime, run kind only | −44 of 170 runs per full press (26 %); 396 of 2 313 in-child s; each gate's `runs_provenance` becomes the shared set's | T12 (paths relative to `runs/gates/`), T13 (resume must stay the record's decision), T14, amendment 21 rule (xi): `tally.SOURCES` names `reproduction/runs` and `entry_and_warm/*/pairing` **by directory**, so the tally's population declaration moves and the tally, `tally_contracts`, `recomputation`, `gate_table` and §4 are re-made (0 PROCESS runs); the G8/G9 `reads_from: reproduction` dependency becomes a job dependency | README §5's "every gate makes its own runs" and each verdict's "this gate's runs" sentence; GR's runs are no longer GR's alone (it audits at `after_run` — those records stay distinct by audit position, so GR's 14 optimisations are *not* among the 44; its 16 evaluation-phase records are) | button | survey §7: 44 bit-identical re-makes, groups listed in §2; `is_complete_for` at `records.py:799–834` |
| B2 | improvement item 12: drop `resume=False` at `gate_audit.py:419` | −12 PROCESS runs, ≈ 112 s per press | none once B1's precondition holds; today each doctored job has its own directory, so `--resume` is safe there too | nothing — the gate passes either way (A65 §12 j3) | button | A65's stamp survey: 16 re-made of 178, 12 of them G4's; survey §7 shows G4 at two commits in one set |
| B3 | retire the diagnosis instrument: `gates/exit_audit_diagnosis.py` (1 635) and `child/audit_map.py` (697) and the 3 lines in `optimise.py` that install the (off) trace on every optimisation | −2 332 lines; the 11 records at `3d64625c` leave the relocated set | **run-path edit** (rule xii): G1 straddle + GR re-made (6 + 30 runs, amendment 15); the leave-one-out attribution ("which field explains a residual") can no longer be pressed. **Hold until A67 (written-file-gap) reports** — if the `after_run` audit names a new component, this is the instrument that attributes it | the attribution stage; the trace's inertness check | button | its question is closed: D25 implemented (A62) and **confirmed by the user 2026-09-14**; the stage is off `--gate all` (`python -m` only); `exit_audit.instrument` stamps what the audit put back on every record. Against: A61 §12.2 j4 (orchestrator) ruled it stays "because A62's gate for the fixed audit is exactly this trace" |
| B4 | retire the allowance mechanism: `Job.allow_pending`, `--allow-pending`, `pending_switches_allowed` (record field), the "pending switch" vocabulary row, `stamp_capabilities_absent`'s nulls-for-unsupplied prose; keep `assert_capable`'s refusal | −≈ 150 lines, 1 flag, 1 record field, 2 teeth (`run_path`: "an allowance naming a switch the tree does implement", "a run asking for a switch the tree does not implement" — both bite on a **doctored registry** today) | **schema change → `--resume` re-makes every run** (amendment 17 (a): 170 runs); G7's field count moves | a future driver switch cannot be composed before the tree implements it — which is exactly what the refusal (kept) says | button | selfcheck at `6a0e69f6`: "0 registry entries with no driver name, so the two allowance teeth bite on a registry doctored back to the state before `PROCESS_ARCH_PREDICATE` landed"; D24's driver chain is closed (A60). **Bundle with the next schema change** or leave |
| B5 | retire `output_path_measurements` and `capture_contrast` (`gates.py` 455 lines) | −455 lines; −6 optimisation runs per `--measure all` (≈ 260 s) | the file-level "what the output-time loop moves in the MFILE" half exists nowhere else and bears on I-21 — **after A67** | the contrast table (A57's finding); `output_loop_sweeps` stays as a tally column | button | 0 readers; the sweep-count half is `tally_optimisation.per_sweep_overhead`'s `output_loop_sweeps` |
| B6 | fewer teeth for the same failures: the 11 `capability` teeth "the retired name `X` present in the environment" iterate one refusal — one tooth over the list; `record_completeness` and `run_path` both test `assert_both_rulers` and `assert_attempt_summation` (G7 on a real record, `run_path` synthetic) — keep G7's | 147 → **135** teeth, same code paths | none to coverage: the 11 names come from the registry's own list, which the `capability` *criterion* compares with the driver's `RETIRED_SWITCHES` | the §4.1 table's "147/147" becomes "135/135" and is re-rendered (`--measure gate_table`, `--plan-tables write`) | button | survey §5 tooth list; A56 §9.1 called per-name teeth "true and uninteresting" |
| B7 | `--reference extract/verify/teeth` and `--previous-runs` (≈ 350 lines of `reference.py`): the run-once re-derivation of the committed reference from V3's untracked records | −≈ 350 lines, 2 flags | the committed reference has no self-digest; `verify` is its only byte-for-byte check against its source — git history is the other | the button can no longer re-derive the reference; plan §7.4 designed it as "a second stage, run once" | button | plan §7.4; D25: "the reference is not regenerated"; V3's records still exist in the main checkout today |
| B8 | `self_containment` (241 lines) is a measurement of a **binding requirement** (plan §6: 0 imports of, 0 subprocesses into `idf_probe/`/`fixedpoint/`) and cannot fail — promote it to a gate with one tooth (a scratch module importing `idf_probe` must be counted), or drop it; `exclusion_review` (554 lines) stays as the review instrument the assessments require, but move it beside G1 | +1 gate, +1 tooth, −1 measurement; or −241 lines | dropping it leaves the user's requirement enforced by review only | nothing if promoted | button | measured at A65: 47 files, 0 imports; the plan's §6 row calls it a requirement, not a number |

### Tier C — touches a ruling or a binding rule; the user's call

| # | item | impact | risk | cost | kind | evidence |
|---|---|---|---|---|---|---|
| C1 | **the second implementation — keep, but record a measured caveat in decision (6)**: 9 of `analysis.py`'s constructions are byte-identical (after the name) to `stats.py`'s — `p90`, `finished`, `iterations_summed_over_attempts`, `relative_objective_difference`, `clusters`, `hops`, `similarity`, `failure_taxonomy`, `_label` — and gate `recomputation`'s independence check reads imports, not bodies. Proposal: no code change; the decision (6) row states that the independence is of *plumbing and populations* (which is where A54/A55's three defects were caught) and not of these nine bodies. Merging is **not** proposed: `recomputation` would then compare the tally with itself (R11, rejected) | 0 lines | none now; the risk is the one the caveat names | nothing | ruling (decision (6)) | survey §4: 12 identical-body pairs, 9 across the tally/analysis boundary; A54 §9 already said a hand-copied construction would pass |
| C2 | rule (iii) of amendment 13 says "every child that imports the copy runs with `-P` and `PYTHONSAFEPATH=1`"; the code does this for the **capability probe and the cross-check children only** (`switches.py:778`, `selfcheck.py:1720`). The measurement children (`pool._command`) carry neither and need neither — they run as scripts, so `sys.path[0]` is `harness/child/`, not the run directory. Correct the rule's text to what the code does, or extend the code to the pool (1 line, then a run-path change → G1 + GR) | prose, or 1 line + 36 runs | the `capability` tooth "the working directory holds a package that shadows the tree" covers the probe only | nothing | ruling (binding rule text) | `grep -rn SAFEPATH harness/` → 2 sites, neither in `pool.py` |
| C3 | rules (v) "do not commit while runs execute", (vi)/(xii) "no edit to `child/` + `ystate.py` while runs execute" are **not enforced**: `Gate.run` fails a two-commit population only *without* `--resume`, and states it with. Option (c), no schema change: `pool.run_all` records `git_head()` and a digest of `child/` + `ystate.py` before its first job and refuses to return a batch whose children stamped another head or whose digest changed; one tooth each. Options (a) prose only, (b) a child-stamped digest field (schema change, 170 runs) | + ≈ 60 lines, 2 teeth | none; it turns two prose rules into refusals | a mid-batch commit or edit becomes a refused batch instead of a straddle to be noticed in a stamp survey | ruling (binding rules v, vi, xii) | A53 §10: one edit during a press corrupted the population (G8 failed on a half-renamed record set); A52 §11: the staleness check "is about HEAD not code" |
| C4 | the `after_run` audit position "has exactly one caller" (GR) — A67 makes it two; and G1 uses it. If the user confirms D25's "measure before the audit pass" as final, the prose in `records.AUDIT_POSITION_AFTER_RUN_WHY`, `child.py` and README §3 "snapshot position" can drop the "exactly one caller" clause rather than count callers | prose | none | nothing | ruling (D25 follow-through; A67's row already says the prose is stale) | queue row A67 |

---

## 4. The items, one section each

### A1 — split `gates.py`

The module is 6 899 lines because the driver-change tasks (A56–A60) each added their gate and their
measurement stage to it, and A52 added the framework glue, the registry and the promoted checks.
A52 §9 d3 already chose separate modules for G2–G7 for exactly this reason. Its own `# ----`
sections (§2) are the split. What must travel unchanged: gate names, `runs_under` tuples (T12),
`reads_from`, the `REPRODUCTION_TEETH` list, the record paths. What must be re-checked after the
move: every source scanner that names a module path — `analysis.FORBIDDEN_IMPORTS`
(A65 §4: "else the gate passes vacuously"), `self_containment`'s file list (42 → 47 files at A65),
and `recomputation`'s independence tooth. Verification is A65's: `--selfcheck`, one
`--gate all --resume` that re-makes 0 runs, G1 byte-neutral.

### A2 — retire `predicate_counters` and `attempts`

Both were written by the driver task that added the counters (A58, A60) to publish them before the
tally existed; both read GR's runs; both are `Measurement`s with no consumer. The tally now emits the
per-sweep overhead in both phases (`tally_evaluation.per_sweep_overhead`,
`tally_optimisation.per_sweep_overhead`) and the attempts table (`tally_optimisation.attempts`), the
analysis recomputes them, and `recomputation` compares them cell by cell (2 066 compared, 0
mismatched, A64). One thing lives only in the stage: `_reconcile_sweeps`, which checks that block
sweeps, empty sweeps and dispatch sweeps decompose. Move it into the record contract beside
`assert_attempt_summation` (it is the same shape of identity) and the stage has nothing left.

### A3, A4 — `--tree repository`, `repository_tree_campaign()`, `--crosscheck-previous`

`repository_tree_campaign()` points the preflight and the self-check at the repository's own
`process/` "to ask whether the harness still composes against the tree the earlier revisions
measured". Since A56 renamed every switch in the copy, the repository tree implements none of the
names the harness composes: the self-check pressed against it at `6a0e69f6` fails its `capability`
check **19 of 55**. The flag can no longer do what its help text says. What remains reachable through
it — the `provenance` check's negative control (`is_experiment_copy` False) — is a constructed
`Campaign`, not a tree. `crosscheck_previous` executes V3's own two composition functions and
compares by role; it is opt-in (`selfcheck.py --crosscheck-previous`), off the button, and A47's
reversal path for it is "delete". The transcription it once measured is frozen with V3 (D20) and
compared at every press by the `composition` gate.

### A5 — `--lifted-from`

A50 needed a way to stage V3's derived lifted input files before A51 wrote the derivation; the
refusal in `input_files.assert_lifted` still reads "until that exists, stage it from a directory
holding the previous revision's derived files". The derivation exists, is gated by digest at every
press, and the flag is mentioned in no current document.

### A6 — `failure.py`'s text fallback

The module says so itself: "kept as a fallback, and is marked for removal: it exists only for a
record made by a tree before the typed refusal existed". No such tree makes a record now (every run
asserts the copy). The one check before deleting: no refusal site in the copy still raises an untyped
`RuntimeError` — otherwise G7's failure table would file it as `crashed`.

### A7, A8 — dead definitions; one name, one meaning

Sixty-one lines in five functions no line references. `cheapest_configuration` means two different
things in two modules; a reader who has met one will misread the other. `_pin_for` and
`input_file_for` are one function written twice with one of the two a subset.

### A9 — the copy's gates on the one button

`PROCESS/copy_gates.py` is the criterion library `g0prime` loads by path (correct: "two
implementations of one criterion is how they drift"). It also has its own `main`, runs
`copy_identity` and `edit_behaviour` and writes their verdicts under `runs/gates/` with no commit
stamp, and `edit_behaviour` has no tooth. Registering both in the harness registry gives them the
framework's stamp, ordering and staleness check, and leaves one gate runner. `edit_behaviour` then
needs a tooth (an edit outside the recorded hunks must be caught) or the `Measurement` type.

### A10–A12 — prose and one redundant flag

Listed in the table. The rule table of §6 is the shape A12 proposes for the plan.

### B1 — a shared run pool

The measurement is in §2: 44 of 170 records per press are the same run made again under another
gate's directory, at 396 in-child seconds, and neither the run count nor the seconds is what makes
it worth doing — the user's instruction of 2026-09-11 (*"reduce the number of PROCESS runs for gates
in general if it's not necessary"*) is. The design: `pool.run` already decides, from the record,
whether a job is complete; a pool keyed by the whole job identity makes that decision once per job
instead of once per gate directory. **Precondition, and a hazard on its own**: `records.is_complete_for`
compares arm, configuration, seed, phase, regime and run kind. It does not compare δ, predicate mode,
pin hex, stencil column and sign, `override_env`, `reproduction_overrides` or audit position. Today
those differ only between directories, so no record is kept wrongly; in a shared pool they would
collide. The comparison must widen first — and widening it is a record-contract change of the kind
T13 wants, not a schema change (no new field). Costs that a reader will notice: README §5's "every
gate makes its own runs" becomes false; verdicts' `runs_provenance` describe a shared set;
`tally.SOURCES` names directories and must name jobs instead (rule xi; the tally and its dependents
are re-made, 0 PROCESS runs). GR's fourteen optimisations are not among the 44 — they audit at
`after_run`, which the identity keeps distinct — but its six evaluations, its three cold references
and its five substitute runs are: 14 of GR's 30 records have a bit-identical twin in G6, G8 or G1.

### B2 — item 12

One argument, twelve runs, every press. Each doctored job has its own directory, so `--resume`'s
record check already distinguishes it from the baseline; what `resume=False` buys is nothing the
record does not.

### B3 — the diagnosis instrument

`exit_audit_diagnosis.py` and `audit_map.py` answered one question — which field explains the 7e-3
residual — and D25 acted on the answer; the user confirmed the approach on 2026-09-14. The stage is
reachable only as `python -m harness.gates.exit_audit_diagnosis` and its 11 records sit outside every
gate. Against retiring it: the orchestrator's ruling at A61 (§12.2 j4) that it stays as A62's
instrument, and A67, which is about to audit `after_run` on campaign-composed arms — if a component
other than `tfcoil.insstrain` appears there, this is the tool that says which field. **Hold until
A67 reports**; then it is a run-path edit (three lines in `optimise.py` install the off trace) and
costs a G1 straddle and a GR.

### B4 — the allowance mechanism

Built (A50) for the interval when arms declared switches the tree did not yet implement; the last
such switch landed with A59, and the self-check now says so in its own words. Its two teeth bite on
a doctored registry. Removing `pending_switches_allowed` from the record is a schema change and
re-makes every run (amendment 17 (a) is not to be weakened for a cheaper press), so this rides the
next schema change or stays. The refusal of an unimplemented switch (`assert_capable`) is not part
of this item and stays.

### B5 — the output-path contrast

Six optimisation runs per `--measure all` for a table only A57's report cited. Its `output_loop_sweeps`
half is a tally column. Its other half — which MFILE lines the output-time loop moves — is the one
measurement of I-21's shape that exists per press. After A67, either that question is closed and
this goes, or A67's gate is where the measurement lives and this goes too.

### B6 — teeth

Eleven `capability` teeth each set one retired name and observe the same refusal; the list they
iterate is the registry's own, and the gate's criterion — not its teeth — compares that list with
the driver's `RETIRED_SWITCHES`. One tooth over the list has the same power. The two duplicated
refusals between G7 and `run_path` are the same two functions, one on a real record and one on a
synthetic; G7's is the stronger. The plan's §4.1 count moves from 147 to 135 and is re-rendered.

### B7, B8 — the reference stages; `self_containment`

Listed in the table. `self_containment` is the one place in the package where a requirement with a
pass condition is a `Measurement`: the number it prints (0 imports) is not compared with anything.

### C1 — the second implementation

Decision (6) and R11 stand and this report does not propose merging: the value of `analysis.py` is
that a definition that reaches one implementation and not the other fails a gate (I-18, I-19), and
that value was realised three times during the build (A54 §4, A55 §6.1, §6.2). The measurement that
belongs beside the decision: nine constructions are the same text, and the gate that certifies
independence reads imports. A54 §9 said this. Recording it in the decision row is the honest form;
a body-identity tooth would only force nine functions to be rewritten differently for the sake of
differing.

### C2, C3, C4 — rules

§6 below.

---

## 5. Do not simplify — things that look redundant and are not

*Caption: one row per construction a fresh reader is likely to call duplicate or excess; "why it
stays" names the trap, ruling or report that shows what it prevents.*

| construction | looks like | why it stays |
|---|---|---|
| **two snapshot positions** (`entry_to_write_output_files`, `before_finalise`) in `child.install_exit_snapshot` | one snapshot twice | G9's criterion compares the two: the state written equals the state handed over (A57 §12 #2); dropping one removes G9's comparison |
| **`analysis.py`** beside `stats.py`/`tally*` | 3 528 lines computing what 4 573 lines already compute | decision (6), R11 rejected; the only mechanism that caught I-18 (26 of 144 cells) and I-19, and three wiring defects in this build. Its meaning is fixed by gate `recomputation`; merge it and the gate compares the tally with itself. See C1 for the caveat that belongs beside it |
| **census records stamped like run records** (`census-2`, 14 provenance fields) | stamps on a derived artifact | I-22 (b), T14: the commit one level down was invisible to the stamp survey that catches a wrong `--resume` (T13) |
| **run-kind separation** (`campaign_run_kind`, `MEASURABLE_RUN_KINDS` declared twice, `run_kind_separation` gate, `is_complete_for` comparing the kind) | a flag checked in four places | T11's shape: a one-seed smoke record summarised under a 25-seed caption; a stamp laundered by moving a directory (A55 §3.4). The two declarations are the tally's and the analysis's, independently, on purpose |
| **exact-tree assertion** on `process.__file__`, equality not prefix, never `__version__` | paranoia | T6 (a worktree does not redirect the editable install), T10 (`__version__` identical for the copy and the root tree and naming a third commit — measured live in this repository, A46) |
| **the derived restore** (`data_structure.py`), `numerics` held back, `EXIT_AUDIT_RESTORE` stamp, the "held back by rule" list per run | restoring one known field would do | D25; A61 §9.3 rejected "restore `n_rad_per_layer` alone" as a hand-written list of one; G1 caught the un-held-back `numerics` rewinding `n_model_calls` by two (A62 §3.4); a change to the set is a change of instrument and must move the stamp |
| **fresh subprocess, own directory, per run** (`pool.run`) | slow | `OutputFileManager` holds file handles as class attributes and initialisation mutates a global (CLAUDE.md); no in-process path exists by design |
| **G1's exclusion set names leaves, never blocks** (126 names, three kinds) | 126 lines that could be ten | excluding a block hid 416 leaves (A52 §5.1) and would hide 75 per record (A62 §7.2); `exclusion_review` exists to read them as one table |
| **G5's switch-by-switch second run** | the same job twice | the comparison *is* the second run: matrix-composed against hand-composed (A52 §4.7) — counted among the 23 by-design second runs, not the 44 |
| **G1's `before` capture never re-made; two commits** | a gate that will not make its own runs | rule (ii): a gate that made its own "before" compares the tree with itself; T13 (A55's `_capture_after` trusting a manifest) |
| **G4's twelve doctored runs** | the same evaluation twelve times | the doctoring is applied inside the child before the audit sweep; the solve is identical but the audit is not, and the audit is what the gate tests. Item 12 is about `resume=False`, not about the runs |
| **the committed reference's bytes** (`reproduction_reference.json`), `FIELD_NAME_MAP`, `FIELDS_NOT_COMPARED` | a stale file with a translation layer | a comparison against regenerated bytes is a comparison with itself (A53 §13); renames are translated, never excluded (rule viii); exclusions are named with reasons (D25) |
| **`--resume` cannot cross a schema change** | an expensive press | amendment 17 (a): "this is the contract working … not to be weakened for a cheaper press" |
| **the cold chain's two compositions** (G3) | one comparison would do | a single comparison failed with 112 components above τ owned by deferred nodes (A52 §4.5) |
| **`retried` derived from `attempts[]`, never the stored flag** | a stored boolean ignored | A53 §2: a tally that reads the flag cannot tell a driver that stopped stamping attempts; `recomputation` has a tooth for it |
| **`assert_one_commit` in both `tally.py` and `analysis.py`** | copy-paste | the analysis may import nothing from the tally (A54); the duplicate is the independence |
| **`exit_audit.frozen` beside the unprefixed `exit_audit.*`** | the same block twice | A59 §8 #2: the unprefixed block is what earlier records and the committed reference carry; reversible, but a rename would reach GR's compared set |
| **`Gate` refuses to exist without a `Tooth`; `Table` without a `Caption`** | ceremony | protocol §12 and §16 as `TypeError`s; the decoy tooth was caught on the first press (A52 §13) |
| **the shared cold-flat entry reference** (`gates.entry_references`, once per invocation) | already exists — why not also GR's and G8's? | it is the pattern B1 generalises; three gates making their own would be "three fixed points that have to be argued to be the same one" (`gates.py:4678`) |

---

## 6. The twelve rules of the amendments — enforced mechanically, or not

*Caption: one row per rule (i)–(xii) of harness plan amendments 13, 16, 19, 20, 21, 22, plus the
two protocol rules the framework enforces. "mechanical" names the code that makes a violation a
refusal or a failed tooth; "prose only" means the code does nothing and the rule lives in review.
The recommendation is the shape A12 proposes for the plan: one table, this column beside each rule.*

| rule | text (short) | enforced by | status | recommendation |
|---|---|---|---|---|
| (i) | `--resume` reaches every run; a verdict records the commits it read and fails without `--resume` when they are not its own | `Gate.run`'s `survey_heads` staleness check; `tally.assert_one_commit`; `analysis.assert_one_commit` | mechanical | shorten the prose to the mechanism |
| (ii) | G1's `before` is made in a tree at the earlier commit and never re-made; a same-commit G1 labels itself | `_capture_before_if_there_is_none`, `_straddle`, tooth `missing_before_record` | mechanical | shorten |
| (iii) | every child that imports the copy runs with `-P` and `PYTHONSAFEPATH=1` | `switches.py:778` (probe), `selfcheck.py:1720` (cross-check) — **not `pool._command`** | **prose overstates the code** | C2: correct the text (the pool's children are scripts and need neither) or extend the code |
| (iv) | `--gate all` order derived from `reads_from` | `ordered_gate_names`, `assert_declared_dependencies`, tooth "a gate declaring a stage the registry does not hold" | mechanical | shorten |
| (v) | do not commit while measurement runs execute | nothing; a two-commit population *fails* only without `--resume`, and is *stated* with it | **prose only** | C3 option (c): the pool refuses a batch whose children stamp two heads |
| (vi) | no edit to any module a child imports while runs execute | nothing | **prose only** | C3 option (c): digest of `child/` + `ystate.py` before and after a batch |
| (vii) | a `--resume` that consults anything but the record is not a resume | `pool.run` is the only decision; but any body may pass `resume=False` (G4 does) | mechanical for keeping, **not for re-making** | B2; and make `resume` a pool-level setting bodies cannot override |
| (viii) | a record-field rename is translated through `FIELD_NAME_MAP`, never excluded | `translate_leaves`, teeth `a_renamed_field_moved_by_one`, `a_one_sided_leaf_the_name_map_does_not_cover` | mechanical | shorten |
| (ix) | §4 is rendered from the `gate_table` stage record; a gate re-run needs `--measure gate_table` first | `assert_records_read_are_current`, `--plan-tables check`, `stage_provenance` gate (5 teeth) | mechanical since A63 | shorten |
| (x) | a self-check builds its own fixture | the self-check passes on every fresh worktree (7/7 at `6a0e69f6` here, "this tree holds no verdict record") | half: observed, not asserted | leave; state that a new worktree's first `--selfcheck` is the test |
| (xi) | a gate's arm/seed/configuration set is a tally population; a change re-makes the dependent stages in the same press | `analysis.assert_the_tally_read_these_runs` *refuses* a stale stage; the re-make is manual (`--gate recomputation --resume`) | half | after any `--gate X` press, run the stages whose `SOURCES` include X's runs (0 PROCESS runs); then shorten |
| (xii) | `child/` + `ystate.py` is rule (vi)'s set; the folder is the rule | nothing beyond the folder | **prose only** | as (vi) |
| §12 | every gate has a tooth | `Gate.__post_init__` | mechanical | — |
| §16 | every table has a caption with units, row, column, population, construction | `tables.Caption`/`Table` constructors, `tally_contracts` teeth 1–6 | mechanical | — |
| plan §6 | nothing in `harness/` imports or spawns into `idf_probe/` or `fixedpoint/` | `self_containment` **measurement** — prints a count, fails nothing | **cannot fail** | B8: a gate with one tooth |

---

## 7. Duplicated prose

- **Vocabulary, three times**: README §3 (41 rows), harness plan §0 (23 rows), harness plan §11.2
  (14 rows). The README's is the fullest and carries the "changed/added" markers; the other two could
  point at it (A12).
- **Rules, six places**: amendments 13, 16, 19, 20, 21, 22 each add rules to "the list"; §6 above is
  the one table.
- **Module docstrings that restate the README**: measured share of docstring+comment lines is 40 %
  in `config.py` and `ystate.py`, 38 % in `stats.py`, 69 % in `perturb.py`. Not proposed for cutting:
  `stats.py`'s docstrings *are* the declarations the captions quote (A53 §2), and the survey found
  **0** README paragraphs reproduced verbatim in either plan (120-character windows) — the prose is
  written three times in three registers rather than pasted, which is more work to shorten than it
  looks.
- **Refusal messages**: 8 438 lines of the package are message text — 25 % of the code lines.
  Nothing here proposes shortening them; they are the part of the harness a person reads when
  something refuses, and the archived reports show them being read.

---

## 8. What the queue, the plans and the improvement list should gain (not edited here)

- **Improvement list**: item 12 gains the measured count from this survey's §7 (12 of 170; two
  commits in one gate directory); a new item for B1 (44 of 170 records per press are bit-identical
  re-makes; precondition on `is_complete_for`); a new item for B6 (147 → 135 teeth); a note under
  item 11/D25 for B3's dependency on A67.
- **Harness plan**: the rules table of §6 as an appendix, replacing the scattered "rules added" lines;
  §4.1's target tree annotated with the actual 46 973 lines against the ≈ 6 570 estimate and where
  the difference is (§2 here — 39 % prose, one module of 6 899 lines); decision (6) gains C1's caveat.
- **README**: A11's five stale passages; §5 loses `--tree repository` (A3); §10.1's table gains the
  proposed split of `gates.py` when A1 lands.
- **Queue**: a D-row proposal for C3 (mechanical enforcement of rules v/vi/xii) and for C2 (the text
  of rule iii); B3 and B5 marked "after A67".
- **`TRAPS.md`**: nothing new. One near-trap is worth a line in the harness plan rather than the trap
  file: `records.is_complete_for` compares six of the job's identity fields, and a run directory
  layout is what keeps the others apart (B1's precondition).

---

## 9. Limits

- **Not every line was read.** The 46 973 lines were surveyed by script; read in full were
  `framework.py`, the runner, `pool.py`'s job and command composition, `records.is_complete_for`,
  the section structure and registries of `gates.py`, `selfcheck.py`'s outline, `chain.py`'s and the
  gate modules' outlines, and the passages each finding rests on. The 19 archived reports were read
  by two read-only research passes whose extracts fed §4 and §5; their citations were spot-checked
  against the reports, not re-read in full.
- **"Referenced nowhere" is by name mention**, with docstrings and comments stripped, not by resolved
  call graph. A name mentioned in a string literal counts as referenced, so the five dead definitions
  are an under-count, not an over-count. Conversely "9 record fields named by no reader" means no
  source names them outside the child; a human reading a record reads them, which is why none is
  proposed for removal.
- **"Bit-identical re-make" uses five fields** (composed environment, audit position, node calls,
  dispatch sweeps, objective hex), not the whole record. Two records equal on those and different
  elsewhere would be counted as duplicates; none was found by spot-checking the groups in §2 against
  `wall_s` (they are separate runs, not copies) and `outdir`.
- **Runs per press are read from A65's relocated set**, which is a `--resume` press: some directories
  hold two commits. A from-scratch press would show the same 170 records at one commit (A55 §4.1:
  140 made + 10 resumed + G1's 6 + `--measure all`'s 6 + smoke 13 at `f8bce151`).
- **Seconds are `wall_s` sums** from the records, context only (I-10, T5); no timing supports any row.
- **Teeth duplication was judged by name and by the refusal function named in the tooth**, not by
  executing the teeth against each other.
- **Rule enforcement (§6) was judged by reading the code path each rule names**, plus the two
  `grep`s cited; no rule was violated deliberately to see what happens.
- **One press was made** (`selfcheck.py --tree repository`); its JSON is in the session's scratch
  directory, not committed — the sentence quoted (capability FAIL 19/55) is reproducible from the
  committed script with that flag at `6a0e69f6`.
- **What was not surveyed**: `PROCESS/process/` (the copy; D5/D11, not harness), the V2/V3
  directories, `idf_probe/` and `fixedpoint/` (superseded, self-containment measured 0 links),
  `EXPERIMENT_PLAN.md` §4's 1 790 rendered lines (output, not harness).

---

## 10. Change log

| date | change |
|---|---|
| 2026-09-14 | Created. `harness_survey.py` committed at `dd3f6ee4` and run; report written from its output, one allowed self-check press, and the archived reports. No code, plan, queue or improvement-list change. |
