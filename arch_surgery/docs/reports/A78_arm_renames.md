# A78 (arm-renames) — the arms renamed so the rungs read rung for rung; the records not re-made

> **Document status** — **OPEN.** Task **A78 (arm-renames)**, branch `A78-arm-renames`, worktree
> `/home/wrutten/projects/PROCESS_surgery_worktrees/A78-arm-renames`, base `abcd15e0`
> (`architecture_surgery`, 2026-09-15). Ruling implemented: the user, 2026-09-15 — *"In the v4 report,
> rename A0p and A1 to A1 and A2, and B3 to B2. That makes the naming of the rungs reflect the
> parallelism in the switch matrix … I don't value consistency of naming with v3 report, but it
> should be applied consistently throughout the v4 folder. Check this thoroughly."* Records made:
> 7 runs through the pool — 6 gate-kind, 1 smoke-kind tooth run (§6(b)); every campaign record kept. Folder position records lifecycle, not validity
> (trap T3).

## 1. Verdict in one page

- **The arms are `AR / A0 / A1 / A2` and `BR / B0 / B1 / B2`** — reference, flat control, burn-time
  ownership, partition — one letter apart per rung in the two phases. `A0p → A1`, `A1 → A2`,
  `B3 → B2`, applied throughout `arch_surgery/MDA_partitioning_experiment_v4/`: the matrix
  (`arms.py`), the switch registry's V3 name map, every gate, both tallies, the analysis, the
  self-check, the README, `PROCESS/CHANGES.md` (prose only; `copy_identity` and `g0prime` PASS, no
  `.py` under `PROCESS/` changed), the report's §1–§3, §5–§6 and Appendices A–B in place, §4 by
  re-rendering. **No number changed** (§6(c)).
- **The 949 campaign records and the 139 seeded gate records were not re-made.** They stamp the
  names of their day. One declared table, `harness/core/records.py::RECORDED_ARM_NAMES =
  {"A0p": "A1", "A1": "A2", "B3": "B2"}`, is applied in **one** place — `records.read`, the one
  reader — so every consumer sees today's names (§2). `--jobs all` lists **1075** distinct jobs and
  `--resume` would keep **1044** of them before the renaming and **1044** after it, the same 31 not
  kept (28 crashed campaign optimisations, 3 hand-composed G5 jobs) (§6(b)).
- **The press in this worktree: 30 PASS, 0 FAIL, 161 of 161 teeth tripped** — after one fix on the
  branch at the orchestrator's instruction (§6(b), §7 d11). At the first press `switch_composition`
  (G5) FAILed **3 of 141**: its kept from-the-matrix records were made in the A73 worktree and its
  hand-composed records had to be re-made here (their identity carried the pressing worktree's
  absolute artifact paths, so `--jobs all` at the base already listed them "no record on disk"); the
  three mismatches were `resolved_switches`' artifact paths naming the two worktrees, **every physics
  value of the ten compared equal**. The gate now compares those paths relative to the record's own
  experiment directory (a tooth added), and the pool renders path-valued identity entries
  tree-relative so the job resumes across worktrees. G5 pressed once after: **141 / 0**, 4/4 teeth.
- **Runs made: 7**, all through the pool (6 gate-kind, 1 smoke-kind): G7's stale-record tooth re-makes
  one `AR` smoke evaluation every press by design (4.4 s here), and G5's three hand-composed `B2`
  optimisations twice — once under the old identity, once under the portable one (29–52 s each). The
  stamp surveys before and after are in §6(b): 1096 → 1102 records, 0 disappeared, 7 with a changed
  commit (the one re-made plus the six new), 949 campaign records at `57dc0c14` untouched.
- **Two defects of my own found by the press and fixed on kept records, each pressed once after:**
  (i) the translation's in-memory trace fields were read by G8's value-for-value comparison as 18
  differing values (FAIL, first press) — folded into one field, `arm_name_translation`, declared in
  G8's reviewed exclusion set (§7 d3); (ii) `records.read` added a phantom `arm_naming` field in
  memory that G1 and G8 then counted (+6, +12 compared values) — removed (§7 d4). §6(b) states the
  first press's numbers beside the final press's.
- **A tooth for the translation and three more** in gate `resume_identity`: an arm nobody declared is
  refused by name; a pre-renaming record of a renamed arm is complete for today's job; a
  post-renaming record is not translated (the stamp alone tells today's `A1` from yesterday's); a
  canonical directory occupied by another job's record is not removed. The gate also surveys every
  record under `runs/` by how its name was read: **1099 records — 458 translated (`A0p → A1` 132,
  `A1 → A2` 233, `B3 → B2` 93), 636 unchanged, 5 stamped, 0 refused.**
- **The reproduction reference regenerated names-only** (`reference.py --rename-arms`: 9 `arm`
  fields, 3 per-arm provenance keys, the naming stamp; `previous_arm`, `source_path`, every compared
  value untouched) and GR pressed: **256 / 0**.
- **§4 against the base with the names reversed** (`renamed_section_diff.py`): 1439 tokens reversed;
  **13 of 4966 line positions differ**, every one in the §4.1 gate table or its marker re-made by this
  press, or in G8's caption quoting its excluded-value count; **0 in a measurement cell** (§6(c)).

## 2. The translation: one table, one place, and why a stamp

**The table.** `records.RECORDED_ARM_NAMES = {"A0p": "A1", "A1": "A2", "B3": "B2"}`, with the date
and the user's words in its docstring; the only place in the harness the old spellings are written
(the V3 name maps spell V3's names, which coincide — §4).

**Where it is applied.** `records.read(outdir)` → `translate_recorded_arm_names(record)`. Every
reader of a run record goes through `records.read`: the pool's resume comparison (`_kept` →
`is_complete_for`), `job_listing`, the tallies (`tally.gather*`), the analysis (`source_records`,
`_directories_by_digest` — routed through it by this task, §7 d6), the gates that read records by
value (`gate_audit`, `gate_written_file`, `gate_neutrality`, routed likewise), `chain._measured_arm_costs`,
the population marker. Readers that consume only `tree_git_head` or `campaign_run_kind`
(`run_stamp_survey.py`, `framework.survey_heads`, `plan_tables._survey`, `chain` run-kind counts)
were left reading the bytes: they see no name. The two sites that **write a record back** —
`stamp_identity` and G7's stale-record tooth — read the bytes, as they must (a translated record
written back would be translated again). A read record that is written again goes through
`records.stamped_as_today` (the reproduction tooth's scratch copy is the one site, §7 d7).

**What the translation does to a record.** `campaign_arm` and `job_identity.arm` through the table.
Where the arm's name changed, `job_digest` is **re-derived** over the translated identity — and only
if the stamped digest re-derived from the stamped identity in the first place; a record whose digest
never matched keeps its mismatch and is refused downstream as before. The stamped digest is kept in
the record's one in-memory trace field, `arm_name_translation` (`recorded_campaign_arm`,
`campaign_arm`, `recorded_job_identity_arm`, `job_identity_arm`, `job_digest_as_stamped`,
`job_digest`, a note, the table's name). Nothing is written to disk; `outdir`, `entry_state` paths
and directory names stay as the run wrote them.

**Why re-derive rather than compare both.** The digest is a pure function of the identity, and
the identity is now spelled in today's names; a digest of the old spelling identifies no job the
pool composes today. Re-deriving at read keeps the pool's comparison
(`records.why_not_complete_for`, unchanged) as *the* resume decision — rule (vii), trap T13 — with
one construction of "the same job" (rule xiv), rather than teaching the pool a second digest to
accept. Reversal: empty the table; `read` then returns every record as written and every record of a
renamed arm is re-made (as at any schema change, amendment 17).

**Why a stamp and not a rule.** Two of the three renamed arms took names that were another arm's
before: today's `A1` (the pinned flat arm) spells the same as a pre-renaming record's `A1` (today's
`A2`). No rule on the string can separate them; a record made after the renaming therefore carries
`arm_naming = "rungs-2026-09-15"`, stamped by the pool beside `job_identity`
(`pool.stamp_identity`), and `records.read` leaves a stamped record alone. The stamp is deliberately
**not** a schema field: a schema field is required of every record, and requiring it of the 949
campaign records would make `--resume` cross the renaming as though it were a schema change, which
it is not. Tooth: *a post-renaming record is not translated* writes the same complete record of
today's `A1` with and without the stamp; with it, read back as `A1` and complete for the job; without
it, read back as `A2` and not complete.

**Directories.** `pool.directory_for(job)` resolves a job's directory in three steps: (1) the
canonical directory (`canonical_directory_for`: the job's own `outdir`, or the shared pool's
identity-named directory) if it holds a record of the same **readable** identity — arm,
configuration, seed, phase, regime, run kind, as `records.read` reports them; (2) otherwise the one
directory under `runs/` whose record carries this job's **digest** (an index built once per process
over `runs/**/metrics.json`, kept current by `run`; two such directories refuse); (3) otherwise the
canonical directory, where the run will be made. Step 1 first so that a caller naming an explicit
directory for a deliberate second record of one identity — G1's two captures — keeps it (the first
version of this rule redirected G1's `before` to `after`; the gate's by-design pair caught it, §7 d5).
Measured over the 949 campaign jobs: **565 resolve to their canonical directory, 384 are redirected**
(128 `A1` → `…/A0p/…`, 181 `A2` → `…/A1/…`, 75 `B2` → `…/B3/…`), every one to an existing record.
`run` refuses (`assert_not_another_jobs_record`, `PoolError`) to remove a canonical directory that
holds a record of a different readable job — reachable only when a job has no record anywhere and its
canonical directory is taken, which the renaming made possible (`…/A1/seed001` holds today's `A2`).
The stencil backward point's `entry_state` — part of its identity — now names the forward point's
*resolved* directory (`chain.evaluation_stencil_chains`), so the 198 stencil records match their jobs.

**The tooth for the table.** A complete record naming arm `ZZ`, unstamped and stamped, is refused
by `records.read` with `RecordError` naming the arm, both ways; the refusal reaches the pool's index
build and every gather, so such a record is never kept under a name nobody declared nor dropped from
a population without a word. The gate also checks the table's values are distinct arms of the matrix.

## 3. The rename, file by file

Whole-word token counts at the base and now, per file this task changed (`git diff --name-only
abcd15e0..HEAD`), from a `git show` + regex pass over each file — an inspection aid, not a published
result; the published verification is §6. The report's counts include §4
(re-rendered); `A1` and `A2` in the queue and the plans include task numbers, which were not touched
(§4 lists them). The residues are classified in §6(e).

| file | `A0p` base→now | `A1` (whole word) base→now | `B3` base→now | `A2` base→now | `B2` base→now |
|---|---|---|---|---|---|
| `v4/EXPERIMENT_REPORT.md` | 468→8 | 556→487 | 539→21 | 0→559 | 18→562 |
| `v4/PROCESS/CHANGES.md` | 2→0 | 8→7 | 8→0 | 2→11 | 0→9 |
| `v4/harness/README.md` | 1→0 | 4→2 | 8→0 | 0→5 | 0→9 |
| `v4/harness/experiment/arms.py` | 7→0 | 6→8 | 9→0 | 0→7 | 3→12 |
| `v4/harness/experiment/switches.py` | 0→0 | 0→3 | 0→3 | 0→2 | 2→5 |
| `v4/harness/core/config.py` | 2→0 | 0→2 | 0→0 | 0→0 | 0→0 |
| `v4/harness/core/records.py` | 0→2 | 0→8 | 0→2 | 1→5 | 0→3 |
| `v4/harness/core/pool.py` | 0→0 | 0→5 | 0→0 | 0→3 | 0→0 |
| `v4/harness/chain.py` | 0→0 | 0→2 | 0→0 | 0→0 | 0→0 |
| `v4/harness/gates/selfcheck.py` | 3→0 | 7→5 | 13→4 | 0→7 | 0→14 |
| `v4/harness/gates/gate_entry.py` | 2→0 | 2→2 | 0→0 | 0→2 | 0→0 |
| `v4/harness/gates/gate_prime.py` | 0→0 | 3→0 | 0→0 | 0→3 | 0→0 |
| `v4/harness/gates/gate_audit.py` | 0→0 | 1→0 | 1→0 | 0→1 | 0→1 |
| `v4/harness/gates/gate_predicate_mode.py` | 0→0 | 1→0 | 0→0 | 0→1 | 0→0 |
| `v4/harness/gates/gate_composition.py` | 0→0 | 0→0 | 3→0 | 0→0 | 0→3 |
| `v4/harness/gates/gate_written_file.py` | 0→0 | 0→0 | 6→0 | 0→0 | 0→6 |
| `v4/harness/gates/gate_resume_identity.py` | 0→0 | 0→1 | 7→0 | 0→0 | 0→7 |
| `v4/harness/gates/gate_tally.py` | 0→0 | 0→0 | 2→0 | 0→0 | 0→2 |
| `v4/harness/gates/gate_output_path.py` | 0→0 | 0→0 | 1→0 | 0→0 | 0→1 |
| `v4/harness/gates/reproduction.py` | 13→0 | 0→13 | 9→1 | 0→0 | 0→8 |
| `v4/harness/gates/reference.py` | 1→0 | 1→4 | 2→3 | 0→3 | 0→5 |
| `v4/harness/reference/reproduction_reference.json` | 1→0 | 10→7 | 19→12 | 0→4 | 0→7 |
| `v4/harness/measurement/tally_evaluation.py` | 15→0 | 7→15 | 0→0 | 0→7 | 0→0 |
| `v4/harness/measurement/tally_optimisation.py` | 0→0 | 0→0 | 1→0 | 0→0 | 0→1 |
| `v4/harness/measurement/analysis.py` | 10→0 | 5→10 | 2→0 | 0→5 | 0→2 |
| `v4/harness/child/evaluate.py`, `optimise.py` (usage docstrings) | 0→0 | 1→0 | 1→0 | 0→1 | 0→1 |
| `arch_surgery/docs/MASTER_TODO_v2.md` (rows I-20, I-26 only) | 2→2 | 11→11 | 9→6 | 5→5 | 7→12 |
| `arch_surgery/docs/plans/V4_HARNESS_IMPLEMENTATION_PLAN.md` | 6→6 | 10→21 | 26→29 | 2→10 | 18→29 |
| `arch_surgery/docs/plans/V4_IMPROVEMENT_LIST.md` (note only) | 13→14 | 15→18 | 34→35 | 0→2 | 19→22 |
| `arch_surgery/docs/plans/V5_IMPROVEMENT_LIST.md` (header only) | 0→1 | 0→2 | 11→12 | 0→1 | 1→2 |

Not in the table because unchanged and correct as they are: `gate_neutrality.py`,
`exclusion_review.py` (one exclusion row added, no arm names).

**Where V3's names stay, by design.** `switches.PREVIOUS_ARM_NAMES` (V3's name → V4's:
`{"R": "BR", "A1": "A2", "B3": "B2"}`) and `RETIRED_ARM_NAMES = ("A1u", "B2")`, both documented as
V3's spellings; `selfcheck._PREVIOUS_NAME` (V4 → V3: `{…, "A2": "A1", "B2": "B3"}`), cross-checked at
run time against `reference.previous_arm_name`; `reference.ARMS_WITHOUT_PREVIOUS_RECORDS` keyed by
V4 names (`AR`, `A1`); the reproduction reference's `previous_arm` and `source_path`
(`phase_b/campaign/<config>/B3/start000/…`). `reference.previous_arm_names()` — the set V3's
directories can carry — derives to `{A0, B0, B1, R, A1, B3, A1u, B2}`, and `previous_arm_name` maps
every V4 arm correctly (`A2 → A1`, `B2 → B3`, `A1` and `AR` refused as arms V3 never ran).

**The self-check's retired-arm check** used to fail any V4 arm whose *string* was in
`RETIRED_ARM_NAMES`; today's `B2` would have tripped it. It now compares by what each V4 arm was
called in V3 (`_PREVIOUS_NAME`), requires every arm V3 ran to have an entry there, and cross-checks
the map against `reference.previous_arm_name` (§7 d2).

## 4. Sites that share the letters and were left alone

| site | tokens | what they mean there |
|---|---|---|
| `PROCESS/process/core/_idf_probe*.py` | `A1`, `A2` | task numbers of the probe's heritage (A1 (stage0-rebaseline), A2 (runtime census)) — the frozen copy; not opened |
| `PROCESS/PROVENANCE.json` (lines 716–717) | `B3` | a recorded diff hunk of the copy's own edit (an I-17 comment); generated, frozen |
| `PROCESS/CHANGES.md` lines "inherited (A1, A2, A18, A19)", "tasks A1, A2, A18, A19" | `A1`, `A2` | task numbers; a sentence added to the table's lead-in says so |
| `harness/data/dsm_node_map.json` (3) | `A2` | task A2's census as the map's provenance |
| `harness/data/st_regression.IN.DAT` (2) | `A1` | the D9 patch comments name task A1 (stage0-rebaseline) |
| `harness/child/data_structure.py:30` | `B3` | the simplification survey's item B3, not an arm |
| `harness/core/records.py:191` | `A2` | the simplification survey's item A2 |
| `arch_surgery/docs/TRAPS.md:84` ("A1's guard") | `A1` | task A1 |
| `arch_surgery/docs/MASTER_TODO_v2.md` §2, D9, D18, D22, I-17, §4's index line | `A1`, `A1′`, `B2`, `B3` | task numbers (§2, D9, §4 index), V2's `A1′` (D18), the D22 ruling's own text (see §9), the closed I-17 line (history) |
| `arch_surgery/MDA_partitioning_experiment_v2/`, `_v3/`, `reports/deprecated/`, `plans/MASTER_TODO.md` | all | frozen records and archives, never edited |
| `runs/**` | `A0p`, `A1`, `B3` in `campaign_arm`, `job_identity.arm`, `outdir`, `entry_state` paths, directory names | the records and where they were made; read through the table (§2) |

## 5. The `B2` rewordings

Every mention of V3's removed joint-test arm in the folder now says whose `B2` it is. In the report:
§1.2 RQ5 ("V3's joint-test arm — V3's `B2`, not today's — is removed"); §1.3 *block loop* ("V3's arm
`B2` — removed in V4; today's `B2` is a different arm"); §2.1's V3 results ("V3's `B2 → B3` (its
joint-test arm to its partitioned arm)"); §3.2's removal paragraph rewritten to open "**V3's `B2` — …
V3's joint-test arm — is removed and is not today's `B2`**" with the difference "between V3's `B2`
and V3's `B3`"; §3.3 ("V3's removed two-pass joint-test arm (V3's `B2`)"); §3.7 rows (e) and (g);
§3.8 item 8; §3.10's run budget; §5.4; Appendix B item 8; Appendix C's head line. In code:
`arms.py`'s `ARMS` docstring, `switches.RETIRED_ARM_NAMES`'s docstring, `selfcheck`'s retired-arm
check, `reference.assert_previous_arm_name`'s docstring (reads its argument in V3's namespace). §2.1
opens with a sentence saying it quotes V3's results under V3's names and what each is today. The
report's header gained an *Arm names (2026-09-15)* paragraph; Appendix C a translation line at its
head for the entries before this date, and a dated entry for the renaming with the press's numbers.

## 6. Verification (from the worktree's repository root, everything committed; §15 scripts named)

Interpreter `/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python`; entry point
`arch_surgery/MDA_partitioning_experiment_v4/experiment_runner.py`. The final press ran at
`8996b843` (harness code final) with the two later commits (`336b1b05`, `350a58c4`) changing the
reference JSON's provenance keys and the reproduction tooth, after which `reproduction` was pressed
once more and the stages re-run; §4 re-rendered identically.

**(a) `--selfcheck`** (with the capability probe): **PASS**, 7 checks, 42 teeth tripped, 43 s.

**(b) `--gate all --resume`, then the gates the stopped chain did not reach, one press each.**

*Stamp survey before* (`run_stamp_survey.py --json`, the seeded tree): 1096 records — 949 at
`57dc0c14`, 96 at `0677a9b3`, 39 at `4ca8cff5`, 6 at `fd480aff`, 3 at `47be2b0d`, 3 at `61473c1d`.

*The press.* `--gate all --resume` pressed 21 gates cheapest first and stopped at the FAIL:

| gate | verdict | compared / mismatched | teeth | runs read (commit) |
|---|---|---|---|---|
| g0prime, copy_identity, edit_behaviour, self_containment, composition, rungs, provenance, data, run_path, capability, artifacts_check, artifacts_derive_inputs, artifacts_census, artifacts_per_run, record_completeness, prime_map, cold_chain, audit_restriction, entry_and_warm | PASS ×19 | — | all tripped | kept, `0677a9b3` / `4ca8cff5` |
| resume_identity | PASS | 1137 / 0 (22 Job fields; 13 by-design pairs; 3 table rows; 1099 records by name) | 9/9 | — |
| switch_composition (G5), first press | FAIL | 141 / 3 | 3/3 | 6 records — 3 at `0677a9b3`, 3 at `50a35de1` |
| **switch_composition (G5), after the fix (`6f5ba612`)** | **PASS** | **141 / 0** | **4/4** | 6 records — 3 at `0677a9b3`, 3 at `6f5ba612` |
| switch_neutrality (G1) | PASS | 2825 values + 51 319 lines / 0 | 9/9 | 6 at `0677a9b3` |
| reproduction (GR) | PASS | 256 / 0 | 8/8 | 29 — 26 at `0677a9b3`, 3 at `4ca8cff5` |
| output_path (G9) | PASS | — | 4/4 | 17 at `0677a9b3` |
| written_file_gap | PASS | 42 / 0 | 4/4 | 12 at `0677a9b3` |
| predicate_mode (G8) | PASS | 8068 values + 84 lines / 0; 294 excluded | 4/4 | 27 — 24 at `0677a9b3`, 3 at `4ca8cff5` |
| tally_contracts | PASS | 279 / 0 | 11/11 | 969 — 949 at `57dc0c14`, 20 at `0677a9b3` |
| recomputation | PASS | 13 174 / 0 | 9/9 | 949 at `57dc0c14` |
| run_kind_separation | PASS | 2997 / 0 | 9/9 | 949 at `57dc0c14` |
| stage_provenance | PASS | 17 / 0 | 5/5 | — |

**30 PASS, 0 FAIL, 161 of 161 teeth** (the gate table's own summary in §4.1, after `--measure gate_table --resume` at `6f5ba612`; `resume_identity` re-pressed after the pool change: 1140 / 0, 9/9). `reproduction` was
pressed twice more after code changes that touched what it reads (the JSON's provenance keys, its
tooth's scratch copy): 256 / 0 each time.

*The FAIL.* G5 composes `B2` twice per configuration — from the matrix, and switch by switch with
every name forced through `override_env` — and compares ten values of the two records. The
from-the-matrix records were kept (made at `0677a9b3` in the A73 worktree); the hand-composed ones
had no record here because their `override_env` carries the artifact paths of the composing
worktree, so the identity differs per worktree — `--jobs all` **at the base `abcd15e0`, before any
change of this task**, listed exactly these three jobs "no record on disk" (§6(b) dry run). They
were made (34–52 s each). The three mismatches are `resolved_switches`: `COUPLING_STATE_PATH`,
`WRITE_SETS_PATH`, `DEFER_PER_RUN_PATH` under
`…/PROCESS_surgery_worktrees/A73-run-path-edits-and-the-press/…` on one side and `…/A78-arm-renames/…`
on the other; the other nine compared values — `norm_objf` hex, `ifail`, iterations, the outer-pass
histogram, the exit-audit hex, the model-call count and the rest — are equal on all three
configurations. Not the renaming's: the same press at the base in any worktree but A73's fails the
same way. **Fixed on the branch at the orchestrator's instruction** (protocol §6: a failed gate blocks
the merge): (1) G5 compares `resolved_switches` through `portable_resolved_switches` — a string value
that is an absolute path under the experiment directory of the record that carries it (the parent of
the record's own `tree` stamp) becomes `experiment:<relative posix path>`; every other value exactly
as resolved; declared in the gate's docstring and the `COMPARED` comment. The existing teeth did not
cover a resolved-switch value; one was added: the resolved `MDA_MODE` flipped on one side must
disagree, and the same resolved switches re-rooted under another worktree (3 artifact paths) must
agree — tripped. (2) `pool.Job.identity` renders a mapping value that is an absolute path under
`runs/` relative to it and one under the experiment directory as `experiment:…`
(`pool._render_string`), so G5's hand-composed identity is portable. Proof it changed nothing else:
`--jobs all` 1075 / **1044** before the change and 1075 / **1044** after it (the 3 hand-composed
jobs' digests changed and their records of the first press could not be kept — their stamped
identity holds the absolute paths, the same reason they never resumed — so they were made once more
under the portable identity: 29–48 s each), then 1075 / **1047**. The 3 first-press records
(`B_B2_*_seed000_gate_{5b82bc37…,b8ba719b…,6069c6c9…}`, at `50a35de1`) remain under `runs/gates/_runs/`
as records of an identity nothing composes now; untracked, harmless, listed here.

*Runs made.* 7, all through the pool at gate/smoke kind: G7's stale-record tooth re-makes one `AR`
`st_regression` seed-0 smoke evaluation every press by construction (it stamps the record stale and
asks for it again without resume; 4.4 s), and G5's three `B2` optimisations twice (above).

*Stamp survey after* (`run_stamp_survey.py --json … --against before`): 1099 records — 949 at
`57dc0c14`, 95 at `0677a9b3`, 39 at `4ca8cff5`, 6 at `fd480aff`, 3 at `47be2b0d`, 3 at `61473c1d`,
3 at `50a35de1`, 3 at `6f5ba612`, 1 at `8996b843`: **1102 records; records whose commit changed: 7**
(`A_AR_st_regression_seed000_smoke` `0677a9b3 → 8996b843`; three `B_B2_*_seed000_gate` at `50a35de1`
and three at `6f5ba612`, all from none); **disappeared: 0; new: 6.** Every campaign record at its
commit. (`run_kind_separation`'s §4.1 row still counts 1099 records: it was pressed before the
last three; not re-pressed, per the instruction's scope.)

*Dry run of the resume decision* (`--jobs all`): at the base `abcd15e0` — **1075 distinct jobs over
30 gates, 3034 declarations, 986 shared, `--resume` would keep 1044**; after the renaming and before
the press — **1075 / 1044**, the same 31 not kept (28 campaign optimisations with `status = crashed`,
G5's 3 hand-composed jobs "no record on disk"); after the identity change, before its press —
**1075 / 1044** (the 3 with new digests, again "no record on disk", every other job unchanged);
after G5's press — **1075 / 1047**.

*The first press, for the record.* The same sequence at `50a35de1` (the code before commits
`02f641ba`, `8996b843`): G5 FAIL 141 / 3 for the reason above, and **G8 FAIL: 8140 values compared,
18 differing** — three per pair on the six pairs of translated (`A2`) records: `job_digest_as_stamped`
and two leaves of `arm_name_translation`, the translation's in-memory trace, which the gate's
value-for-value comparison walked. Fixed by folding the trace into one field declared in G8's
reviewed exclusion set and the exclusion review's kinds (§7 d3), and by no longer adding a phantom
`arm_naming` in memory (§7 d4; G1 had read 2831 values, G8 8080 — now 2825 and 8068, the base's
counts). Pressed once after: G8 PASS 8068 / 0, 294 excluded (240 at the base + the 54 trace leaves).

**(c) `--measure all --resume`** (tally_evaluation, tally_optimisation, recomputed_tables,
exclusion_review, gate_table: 0 PROCESS runs, ~25 s), then **`--plan-tables write`** (187 tables,
34 968 cells, 4965 lines replacing 4966) and **`--plan-tables check`: IDENTICAL** (4965 of 4965).
**`renamed_section_diff.py --base abcd15e0`** (committed; cuts §4 by the renderer's markers, applies
the reverse table `A1 → A0p, A2 → A1, B2 → B3` in one pass, diffs line for line): 1439 tokens
reversed; 1353 of 4966 lines differ before the reversal, **13 line positions after it** (32
unified-diff lines), by subsection: marker 2, §4.1 7, §4.2 2, §4.4 2. Each, at character level:

| where | difference | cause |
|---|---|---|
| §4 marker (2 lines) | gate commits gain `50a35de1`, `6f5ba612`, `8996b843`; gate records 139 → 145, gate-kind 137 → 143 | the 7 runs of this press |
| §4.1 `resume_identity` | population "…; 3 recorded-name row(s); 1099 record(s) under runs/ read by arm name", compared 35 → 1137, teeth 5/5 → 9/9 | this task's survey and teeth |
| §4.1 `artifacts_census` | "one evaluation census each" → "one optimisation census each" | the button's `--census-entry` default is `optimisation`; the seeded verdict was pressed with `evaluation`; both censuses are on disk and were resumed |
| §4.1 `switch_composition` | teeth 3/3 → 4/4 | the added tooth |
| §4.1 `run_kind_separation` | 1096 → 1099 records, 2994 → 2997 compared | the 3 new gate records |
| §4.1 `stage_provenance` | 16 → 17 compared | "whatever live records this tree holds, surveyed and named" — one more |
| §4.1 summary | 156 teeth → 161 | above |
| §4.2, §4.4 predicate-trial captions (2 + 2 lines) | "240 record values excluded" → "294" | G8's verdict, from which the trial table is shaped: the 54 trace leaves excluded by name |

**0 of the residual differences is a cell of a measurement table.** The report's §4.2–§4.4 cells
are the base's cells with the names translated.

**(d)** `merged_names_check.py`: 24 (arm, configuration) pairs, path and kind identical; pins:
44 400 evaluations identical over 185 reference hex values, seeds (0, 1, 7), displacements
(None, 0.0, 0.1). `harness_survey.py`: exit 0; README 1621 lines, report 6043, harness plan 1594;
0 README paragraphs found verbatim in the plan or the report.

**(e) The greps.** `grep -rnE "A0p|\bB3\b"` over the folder minus `runs/`, `PROCESS/process/`,
`harness/data/`, `__pycache__` and §4 of the report: **51 lines**, every one classified — the
translation table and its docstring in `records.py` (2), the header of the report quoting the user's
words (1), `renamed_section_diff.py`'s docstring (1), the V3 name maps and their docstrings in
`switches.py` (3), `selfcheck.py` (4), `reference.py` (3), `reproduction.py`'s tooth message (1), the
reference JSON's `previous_arm` and `source_path` (12), `PROVENANCE.json`'s recorded hunk (2),
`data_structure.py`'s survey item B3 (1), and the report: §2.1's V3-labelled results (6), §3.2's and
§3.7's V3-labelled removal (3), §3.9's GR row in V3's names (1), Appendix C's translation line (2)
and its pre-renaming entries (11). `grep -rnwE "B2"`: 587 lines outside §4, 5 of them V3's `B2`, each
written "V3's `B2`" (§5); the rest today's arm.

## 7. Autonomous decisions, each with its reversal

1. **Translate at read; re-derive the digest; keep the stamped one in a trace field** (§2).
   Reversal: empty `RECORDED_ARM_NAMES`; records of renamed arms are then re-made.
2. **The self-check's retired-arm check compares by V3 name**, not by string, and cross-checks its
   map against `reference.previous_arm_name`. Reversal: the string check, which then fails on today's
   `B2` — so not a reversal without undoing the ruling.
3. **The translation's trace is one field, `arm_name_translation`, declared in G8's exclusions**
   with the reason (a stamp of the identity, like `job_digest`) and classified in `exclusion_review`.
   Reversal: drop the trace altogether (the stamped digest is on disk); the survey then counts
   translated records by comparing disk and memory instead.
4. **No in-memory naming stamp on a pre-renaming record**: what `read` adds is the translated names
   and, for a renamed arm, the one trace field. Reversal: stamp in memory; G1 and G8 then compare a
   field neither run wrote (+6, +12 values).
5. **Directory resolution prefers the canonical directory when it holds the same readable job**,
   then the digest index, then canonical. Reversal: digest first — which hands G1's `before` capture
   the `after` directory (caught by the gate's by-design pair on the first attempt).
6. **Seven direct `json.loads(metrics.json)` readers routed through `records.read`**
   (`chain._measured_arm_costs`, `analysis.source_records`, `analysis._directories_by_digest`,
   `gate_audit`'s row survey, two in `gate_written_file`, `gate_neutrality._read_record`); readers of
   provenance only, and the two write-back sites, left on the bytes. The analysis module's
   independence contract (no tally imports) is kept; its docstring says a name is not a construction.
   Reversal: per-site translation — the second place the brief forbade.
7. **`records.stamped_as_today`** for a read record written to disk again; used at the one site.
   Reversal: none needed if no tooth writes a read record back.
8. **The reproduction reference regenerated, not translated at load**, by `reference.py
   --rename-arms` (names only; refuses a second application; `load` refuses a file without the
   stamp). Reversal: translate in `load` through the same table and drop the stamp requirement.
9. **The queue's D22 row left in its day's names** (a ruling is the user's; §9). **The harness plan's
   dated amendments left as written**, with amendment 27 recording the renaming and the four
   current-state rows renamed; the V4 and V5 improvement lists got a naming note only.
10. **The census entry was pressed at the button's default** (`optimisation`), not at the seeded
    verdict's `evaluation`; both census records were resumed. Reversal: `--census-entry evaluation`
    on the next press.
11. **G5's path comparison relative to the record's own experiment directory** (from its `tree`
    stamp), not `(basename, sha256)`: which committed artifact a switch named is what must agree,
    and the relative path says it while the bytes are `artifacts_check`'s business. Reversal: the
    `(basename, sha256)` form, one function. **Identity rendering of path strings** under
    `experiment:`: reversal is `_render_string` returning its argument, which orphans the 3 records
    again.

## 8. Limits

- **Directory names on disk keep the old names** (`runs/campaign/evaluation/<config>/A0p/…` holds
  today's `A1`; `…/A1/…` holds `A2`; `…/B3/…` holds `B2`). A reader of the tree by path will be
  misled; a reader through the pool or `records.read` will not. The relocation script and any
  future seeding carry the directories as they are.
- **The stamp survey (`run_stamp_survey.py`) reads the bytes**, by design (T13 wants an
  independent survey); it reports directory names in their day's spelling.
- **Verdicts are records rendered from records (T14).** G8's seeded verdict carried `A1` rows that,
  read today, would name the pinned flat arm; they were the partitioned arm's. The press re-made
  every verdict, and the tally's predicate-trial table (shaped from G8's verdict, not from run
  records) followed; the first `--plan-tables` render of this task, made before the press, showed
  38 such lines and is why the order gates → stages → render matters (§9's trap).
- **The press could not be made 0-run** (G7's tooth by construction); it is all-PASS only after
  the G5 fix of §6(b), made at the orchestrator's instruction under protocol §6.
- The `resume_identity` survey counts 636 "unchanged" records among the 1099; that class includes
  the 6 census records and the 6 pre-A72 `switch_neutrality/before` captures, which carry
  `campaign_arm` (`AR`/`BR`) and no identity; they are read, not translated, and not refused.
- `previous_arm_names()` includes V3's retired `B2`, so `reference.assert_previous_arm_name("B2")`
  accepts the string as V3's arm; its docstring now says the argument is read in V3's namespace and
  the one caller passes `"BR"`.

## 9. What should change elsewhere (proposed; not edited here)

- **Queue, D22** (*"`B2` removed from V4 (Phase B is `BR / B0 / B1 / B3`)"*): a ruling in its day's
  names. The user's call whether a bracketed dated note is added to the row or a D29 records the
  renaming as a ruling; I edited no D-row.
- **G5's worktree-dependent identity and comparison** — fixed on the branch (§6(b)); no issue
  needed. Harness plan amendment 27 could gain one sentence on it at the merge.
- **TRAPS.md, a T16 candidate:** *a name in a record is the name at the time of the run.* Records,
  verdicts, directory names and stage records all carry the vocabulary of their day; a rename
  applied to the code and the documents leaves them spelling another arm — and where the new name
  was another arm's old one (`A1`), the bare string cannot say which. Translate at read through one
  declared table, stamp what is written afterwards, and re-make every verdict before re-rendering
  anything from it. Seen twice here: G8's seeded verdict rows, and G5's tooth-made scratch copy.
- **Harness plan, rule table (A.1):** the corollary to rule (xiv) proposed in amendment 27, if the
  user wants it as a rule.
- **A79 (report-captions) and A80 (report-accuracy-audit)** inherit today's names; A80's row already
  says "arm names after A78".
- **`--gate all` with `--census-entry evaluation`** if the orchestrator wants the seeded verdict's
  census entry back.

## 10. Files, commits, presses

Commits on `A78-arm-renames` (base `abcd15e0`), in order: `b1c3e327` (the translation, the pool's
digest resolution and refusal, the stencil entry state; `gate_audit` and `gate_neutrality` routed
through `records.read`), `81566465` (the renames in code; the self-check's retired-arm check; the
reference regenerated; `resume_identity`'s survey and four teeth), `21d09484` (the report's §1–§3,
§5–§6, Appendices A–B; README; `CHANGES.md`; `renamed_section_diff.py`), `50a35de1` (queue rows
I-20 and I-26 — the only queue edits; harness plan amendment 27; the two improvement lists' naming
notes), `02f641ba` (the trace folded into one excluded field, after G8's first-press FAIL),
`8996b843` (no in-memory stamp), `336b1b05` (the reference's per-arm provenance keys; the diff
script's classification), `a536cc60` (§4 re-rendered), `350a58c4` (`stamped_as_today`; Appendix C
entry), `2113e8d9` (this report), `6f5ba612` (G5's portable comparison and tooth; portable identity
rendering), and the final commit (§4.1 re-rendered at 30 PASS; report and Appendix C updated). No `.py` under `PROCESS/` changed; `harness/child/` changed in two usage
docstrings only, with nothing running. Presses: `--selfcheck`; `--gate all --resume` twice (first at
`50a35de1`, final at `8996b843`), the nine gates the stopped chain did not reach once each after the
final press, `reproduction` twice more after its inputs changed, `resume_identity` and
`predicate_mode` once more after `02f641ba`; `--measure all --resume` after each gate press;
`--plan-tables write` then `check` (IDENTICAL). Bulk artifacts under `runs/` untracked; the verdicts
and stage records are there.

## 11. Change log

- 2026-09-15 — task opened on `abcd15e0`; the translation designed after reading the pool, the
  records, the chain and A72's report; dry-run `--jobs all` at the base first (1075 / 1044).
- 2026-09-15 — renames in code, reference regenerated, teeth added; `--jobs all` 1075 / 1044 after.
- 2026-09-15 — prose: report, README, `CHANGES.md`, queue rows, plans.
- 2026-09-15 — first press: G5 FAIL (worktree paths), G8 FAIL (the trace fields); the latter fixed
  on kept records; G1's pair caught the first directory-resolution rule.
- 2026-09-15 — final press, stages, §4 re-rendered, this report.
- 2026-09-15 — orchestrator's assessment: G5's FAIL blocks the merge (§6), fix it on the branch.
  Done at `6f5ba612`: portable `resolved_switches` comparison with a tooth; portable identity
  rendering of path strings; G5 141 / 0 (4/4), `resume_identity` 1140 / 0; `--measure gate_table`,
  `--plan-tables write`/`check` IDENTICAL: **30 PASS, 0 FAIL, 161 of 161 teeth**; `--jobs all`
  1075 / 1044 before and after the identity change, 1047 after the press; 1102 records, 0 gone.

## 12. Orchestrator's critical assessment (protocol §5)

*Written 2026-09-15 at `df9831f5` by the orchestrating session, by checks that differ from the agent's; gates the merge.*

**Checks.**
1. **The translation at read, exercised directly.** A campaign record on disk under `runs/campaign/evaluation/large_tokamak_nof/A0p/seed001` stamps `job_identity.arm = "A0p"` (`job_digest 3463bf1e…`); `records.read` returns `arm = "A1"` with a re-derived digest (`898b0d84…`). The same record with its arm rewritten to `ZZ` in a scratch copy is refused by name (`RecordError: … neither records.RECORDED_ARM_NAMES nor the matrix knows`). The table is the one the brief asked for: `{'A0p': 'A1', 'A1': 'A2', 'B3': 'B2'}`, `MATRIX_ORDER = (AR, A0, A1, A2, BR, B0, B1, B2)`.
2. **Scope by diff, not by the report.** `git diff --stat abcd15e0 df9831f5`: under `PROCESS/` only `CHANGES.md` (prose, +13/−9; `copy_identity` and `g0prime` PASS in the agent's press); outside the folder only the queue (4 lines, rows I-20 and I-26), the harness plan (amendment 27 and four current-state rows), the two improvement lists' naming notes and the task report; **no D-row line in the queue diff**. `reproduction_reference.json`: 15/13 lines, every changed line an `arm` value, a provenance key or the stamp — names only.
3. **The A76 headline row survives the rename unchanged**: the nof displaced fixed-point-distance table reads `A0/AR 2.624e-08`, `A1/A0 9.665e-02` (yesterday's `A0p/A0`), the same digits as A76's table and as my own recomputation at A76's merge.
4. **Residual old names in the report**: 21 lines, all in Appendix C entries written before the rename (2026-09-10 to 2026-09-15) — history, not current state. One correction made in this commit: the translation line at the head of Appendix C said "entries dated before 2026-09-15", which excluded A76's entry (dated 2026-09-15, written before the rename, in the old names); it now says "entries before the renaming entry".
5. **The G5 fix.** `switch_composition` compared an absolute worktree path inside `resolved_switches` — a latent defect any fresh worktree shows and A73's press could not, because both sides of its comparison were made in one tree. Fixed on the branch as §6 requires: paths rendered relative to the record's own experiment directory, a tooth for a re-rooted path that must agree and a flipped switch that must not; 141/0, 4/4. The identity rendering made portable in `pool.Job.identity` changed the digest of the three hand-composed jobs only (`--jobs all` 1075/1044 before and after, the agent's proof; the rule-xiv field set unchanged). Three orphan records of the first press remain under `runs/gates/_runs/` — harmless, named in the report.

**Findings for the record, none blocking.** The census gate was pressed at the button's default entry (`optimisation`) where the seeded verdict was `evaluation`; both resumed, neither re-made — a button ergonomics point, not a result. G7's tooth re-makes one smoke `AR` evaluation per press by construction (pre-existing; ~1 run per press). The queue's D22 row quotes the arms of its day; a naming line goes at the head of the decisions register at the merge, D-rows themselves untouched. TRAPS gains T16 ("a name in a record is the name at the time of the run; read records through the harness, never by directory name") at the merge.

**Verdict: merge.** The rename is complete in the current-state text and code, provably names-only in §4 (the agent's committed reverse-translation diff: 0 measurement cells), every record kept, 30 PASS / 161 teeth at `df9831f5`; the one FAIL was the gate's own and is fixed, not deferred.
