# A110 (v5-warmup-verdict-once): gate `evaluation_warmup` read once (D44), and gate G1's missing path leaf

> **Document status**: **MERGED 2026-10-01 at `c3160245` (`--no-ff`; the orchestrator's assessment at the end, which corrects the stated cause of the `tally_contracts` FAIL); archived.** The one V5 records tree moved on with the next task (A111). Was: **OPEN (task report, awaiting the orchestrator's assessment).** Task A110, branch
> `A110-v5-warmup-verdict-once`, worktree `.claude/worktrees/A110-v5-warmup-verdict-once`, from trunk `ff1abec4`,
> 2026-10-01. Harness only: no change to the driver copy (`MDA_partitioning_experiment_v5/PROCESS/`), to `process/`
> or to V4.
>
> **Commits:**
> - Code: `f3e576d3`, committed before any record was made.
> - Census tables document: `58307581`.
> - Write-set tables document: `e14977c9`.
>
> Every number below is printed by `experiment_runner.py`, by the gate and stage records it writes, at those commits.
> The census presses ran at `f3e576d3`. The write-set presses ran at `58307581`, which differs from `f3e576d3` only in
> `paper_tables.md`.
>
> **Press logs:** `runs/census_tau1e-08/_press_logs/A110/` and `runs/write_set_tau1e-06/_press_logs/A110/`
> (`pressNN_*.log`, `disk_log.txt`). Each of those folders also holds a `START_MARKER`. Gate records were never made on
> a dirty tree. `runs/` was left in place; no records tree was copied.

## 1. Verdict

**Under `census_tau1e-08`: 29 PASS of 29, 180 of 180 teeth tripped.** It was 29 PASS with 177 of 177 teeth; the
three extra teeth are `evaluation_warmup`'s.

Source: `--gate all --resume` (`press06`), then `--measure gate_table --resume` (`press07`), record
`runs/census_tau1e-08/gates/gate_table/measurements.json`.

**Under `write_set_tau1e-06`: 27 PASS, 1 FAIL, 1 not run, of 29; 176 of 180 teeth tripped.** It was 26 PASS, 2 FAIL,
1 not run, with 172 of 177 teeth (A109).

Source: `--gate all --resume --test-set write_set` stops at GT, which refuses by design (`press07`). The eight gates
after GT were then pressed one by one (`press08`–`press15`), and the table was read by `--measure gate_table` (`press16`).

The four teeth not tripped under the write set are GT's four; GT was not run.

| gate | plan | census_tau1e-08 | write_set_tau1e-06 |
|---|---|---|---|
| `g0prime` | G0 | PASS 1/77 (the approved file), 4/4 | PASS 1/77, 4/4 |
| `copy_identity` | — | PASS 8/224 (declared edits), 12/12 | PASS 8/224, 12/12 |
| `edit_behaviour` | — | PASS 0/3, 1/1 | PASS 0/3, 1/1 |
| `self_containment` | — | PASS 0/61, 1/1 | PASS 0/61, 1/1 |
| `composition` | — | PASS 0/53, 12/12 | PASS 0/53, 12/12 |
| `rungs` | — | PASS 0/98, 3/3 | PASS 0/98, 3/3 |
| `provenance` | — | PASS 0/4, 4/4 | PASS 0/4, 4/4 |
| `data` | — | PASS 0/22, 6/6 | PASS 0/22, 6/6 |
| `run_path` | — | PASS 0/12, 12/12 | PASS 0/12, 12/12 |
| `resume_identity` | — | PASS 0/1 224, 14/14 | PASS 0/823, 14/14 |
| `capability` | — | PASS 0/61, 5/5 | PASS 0/61, 5/5 |
| `artifacts_check` | — | PASS 0/119, 3/3 | PASS 0/119, 3/3 |
| `artifacts_derive_inputs` | — | PASS 0/2, 4/4 | PASS 0/2, 4/4 |
| `artifacts_census` | — | PASS 0/81, 5/5 | PASS 0/81, 5/5 |
| `artifacts_per_run` | — | PASS 0/16, 2/2 | PASS 0/16, 2/2 |
| **`evaluation_warmup`** | — | **PASS (read) 0/19 876, 5/5** | **PASS (read) 0/19 876, 5/5** (was FAIL 2 256/19 880, 1/2) |
| `record_completeness` | G7 | PASS 0/281, 14/14 | PASS 0/281, 14/14 |
| `count_neutrality` | GC | PASS 0/50 114, 4/4 | PASS 0/50 114, 4/4 |
| `prime_map` | G2 | PASS 0/17 591, 3/3 | PASS 0/17 591, 3/3 |
| `entry_and_warm` | G6 | PASS 0/6 717, 3/3 | PASS 0/6 717, 3/3 |
| `test_set` | GT | PASS 794/13 424 (its teeth's drops), 4/4 | NOT RUN (refused under the fallback, by design), —/4 |
| `switch_composition` | G5 | PASS 0/156, 4/4 | PASS 0/156, 4/4 |
| **`switch_neutrality`** | G1 | **PASS 0/54 985, 9/9** (was 0/54 988) | **PASS 0/54 967, 9/9** (was FAIL 3/54 970) |
| `reproduction` | GR | PASS (read-once, `d6c246a1`) 0/256, 8/8 | PASS (read-once) 0/256, 8/8 |
| `output_path` | G9 | PASS 0/3 879, 4/4 | PASS 0/3 879, 4/4 |
| `written_file_gap` | — | PASS 0/42, 4/4 | PASS 0/42, 4/4 |
| `tally_contracts` | — | PASS 0/538, 18/18 | **FAIL 9/538, 18/18** (was PASS at A106; see §6, unexpected 1) |
| `run_kind_separation` | — | PASS 0/2 283, 7/7 | PASS 0/1 882, 7/7 |
| `stage_provenance` | — | PASS 0/13, 5/5 | PASS 0/13, 5/5 |

**The write set's one FAIL, `tally_contracts`, is not caused by this task's change.** That gate had not been pressed
under the write set since A106; this is its first press since A109. It reads records that A109's press of G6 re-made
under the write set (§6, unexpected 1).

Runs made: **one PROCESS run under each run ID.** In both, it is G7's stale-run tooth, which re-makes one smoke
evaluation on every press. No other run was made: every gate kept its records under `--resume`, and both G1 presses
kept all six of their after-side records.

## 2. Part 1: `evaluation_warmup` gives its verdict once (D44)

**The diff in words** (`harness/gates/gate_evaluation_warmup.py`, rewritten):
- **What the gate no longer does.** The pressed form archived the cold child's records, composed eleven after-side
  jobs under the pressing run ID's settings, ran them, and compared. The read form does none of this; it composes no
  job and makes no run (`needs_runs=False`, no `jobs`).
- **What it does instead.** It reads the verdict recorded at `c2295511`, verifies it and the files behind it, and
  returns that verdict.
- **Why `c2295511` and not `ff9e73a2`.** The warmed child was introduced at `ff9e73a2` (A102), and the press there
  wrote `gates/evaluation_warmup/gate.json`. A103's `--resume` press at `c2295511` overwrote that file with a verdict
  over the same eleven after records, all stamped `ff9e73a2`, and the same archived before records, stamped `24b78e2d`.
  The verdict's own `runs_are_not_this_commit's` line says so. The gate's code is unchanged between those two commits
  (`git diff ff9e73a2 c2295511 -- gate_evaluation_warmup.py gate_count_neutrality.py` is empty). The `c2295511` record
  is the only verdict of the gate under the default settings that survives, so it is the one read.
- **The three commits are constants in the module:** `VERDICT_COMMIT`, `WARMED_CHILD_COMMIT`, `COLD_CHILD_COMMIT`.

**How the read verifies its archive.** It follows GR's pattern (`registry._run_once`), with more checks than GR's:
1. **The verdict record.**
   - On the first read it is the live `gate.json`. That read copies it to `verdict_at_c2295511.json`, and every later
     read takes the archive. This is GR's rule, because the framework rewrites `gate.json` at every press.
   - It must be stamped `c2295511`, be this gate's own, and name the default settings, `census` at `1e-08`
     (`config.default_campaign`).
   - Its rows must be exactly the gate job set's evaluation half, in order.
   - Anything else refuses. Under the write set before the copy, the read refused on the A106 FAIL record because of
     its `a1db0a0c` stamp. This was observed in a dry run before the commit, not in a press.
2. **The records it names.**
   - Every file the comparison reads — each side's `metrics.json` and the coupling-state files, 66 files over 22
     records — must be on disk.
   - Each must be byte-identical to the SHA-256 in `archive_manifest.json`. The first read wrote that manifest beside
     the verdict archive, as GR's archive is written. It attests "unchanged since the first read", not "unchanged since
     `c2295511`": no digest of those files was recorded then.
   - Each before record must be stamped `24b78e2d` and carry no warm-up block. Each after record must be stamped
     `ff9e73a2` and have been made under the verdict's settings.
3. **The comparison, re-derived.** The read re-runs the comparison from those files with the functions the verdict was
   made with: GC's `compare_counts`, `compare_prime_calls` and `compare_state_files`, and `rederive_agreement`. For
   every pair it reconciles eight numbers with the recorded row: count leaves compared and differing, prime checks and
   failures, components compared and differing, the re-derived agreement, and the pair's PASS. So a verdict whose
   numbers do not follow from its records is caught, whichever side was changed.

The gate returns the recorded verdict, turned to FAIL by any discrepancy above.

What it reads under both run IDs (`census press02`, `write-set press04`; the same population line):

> READ, not pressed (D44): the verdict recorded at c2295511 under the default settings (census/1e-08), PASS; re-derived
> here from its 11 archived evaluation pair(s): 1426 count leaves compared under 41 declared paths, 0 differing; 11
> prime-count check(s), 0 failing; 18450 coupling-state components compared bit for bit, 0 differing; 11 of 11 pairs
> agree with the recorded row and their stamps; 66 of 66 compared files byte-identical to the manifest

The record's `criterion` begins "READ, NOT PRESSED (D44)". Its `read_of_the_recorded_verdict` block states that no run
was made and no job was composed under the run ID's settings, and it repeats the recorded teeth. `runs read: 22
record(s) — 11 at 24b78e2d, 11 at ff9e73a2`.

**Teeth: five, all run live on the archive on every read, all TRIPPED under both run IDs.**

| tooth | kept or new | under both run IDs |
|---|---|---|
| a doctored count on one record (+1 to `node_calls_single_eval` in a copy of an archived after record) | kept | the one and only differing leaf, 1 of 148 |
| a doctored warm-up count | kept | re-derived agreement False, naming `node_calls_single_eval` |
| a doctored archived record (one byte of a copy of an after record's `metrics.json`) | new | the manifest names that file alone, of 66 |
| a doctored recorded verdict (+1 to a row's `counts.n_mismatched` in a copy of the verdict) | new | the reconciliation names `counts.n_mismatched` alone |
| a verdict stamped at another commit (a copy stamped `ff9e73a2`) | new | refused: "stamped ff9e73a2, not c2295511" |

**No tooth was removed.** Both teeth of the pressed form compared copies of real records, and the archive still
provides them. The first could not trip under the write set in the pressed form (A106), because that pair already
differed. In the read form both sides are the census-made archive, so it bites under every run ID. None of the five
passes vacuously: each one runs on the real archive.

**`--resume`.** The read refuses nothing for want of `--resume`, which GR's wrapper does. This is a decision (§6,
decision 2).

**The stale FAIL record under `write_set_tau1e-06`.** It was moved, not deleted, so it is still on disk.
- **What moved, and where.** `gates/evaluation_warmup/gate.json` (A106's FAIL at `a1db0a0c`, SHA-256 `37c4a631…`) and
  `gates/evaluation_warmup/after/` (its eleven write-set after runs) went to
  `gates/evaluation_warmup/superseded_A106_pressed_form/`, by `mv` on the same filesystem; no byte changed.
- **The marker.** `SUPERSEDED.json` in that folder says what the records are, why they are superseded (D44, I-40),
  who moved them and when, and what replaced them. No gate reads them. `run_kind_separation` still counts them, as
  records under the run ID.
- **What replaced them.** The census archive (`verdict_at_c2295511.json`, `archive_manifest.json`, `after/`) was copied
  in by the committed step, through the new `--archive` option:
  `--test-set write_set --copy-archived-records census_tau1e-08 --archive evaluation_warmup --apply`
  (`write-set press02`). 134 files were copied, each SHA-256 checked. The 143 files of `before/` were already present
  with the same bytes. The record is `runs/write_set_tau1e-06/archived_records_copied_evaluation_warmup.json`; the
  whole-copy record of A107 is left as it was made.

**What a fresh run ID inherits.** `archived_records.ARCHIVES`' entry for the gate now copies `before/`, `after/`,
`verdict_at_*.json` and `archive_manifest.json`.

**Why the copy needed `--archive`.** The whole step refuses on this run ID because 67 files differ from the census
folder's. These include `gates/reproduction/gate.json`, which every read rewrites in place, and pool records re-made by
later presses. So the copy gained `--archive <gate>` (repeatable): it copies only the archives named. The conflict rule
is unchanged within them, and a filtered copy writes its record under its own name.

**`--gate all` under the write set** passed `evaluation_warmup`, then G7, GC, G2 and G6, and stopped at GT
(`press07`). It is no longer stopped by this gate.

**Documentation.** The gate's docstring states the read, the record read and why that one, the verification, and the
teeth. The registry's `_instrument_gates` docstring and its `GATE_ORDER` comment are updated, as is `archived_records`'s
docstring. In `harness/README.md`: §8 (the gate's description), §11 (the gate row: "no (read-once)"), §12 (what the
copy carries; `--archive`), §13 (the command) and the change log.

**Untouched.** The per-record check `evaluation_warmup.agrees` (`core/records.py`, `child/evaluate.py`) is unchanged.

## 3. Part 2: gate G1's missing path leaf

**The file's content is still compared. Shown before the leaf was added, and now measured by a committed stage.**
- **Where the leaf comes from.** `audit_snapshot.coupling_state` is set in `child.install_exit_snapshot_hook` as
  `str(coupling_state_path)`. The hook loads that file with `module_solve.load_spec`, the same function and the same
  path the exit audit loads and records as `exit_audit.coupling_state`.
- **What the `audit_snapshot` block carries.** It carries no digest of the artifact itself: its `components_sha256`
  values are digests of the coupling state at each position, which are behaviour and are compared.
- **Where the file's identity is compared.** In the same record, through `exit_audit.components_sha256`: the rebuilt
  spec's digest, which `load_spec` refuses unless it equals the artifact's own.
- **What I did, and why no content comparison was added.** I added the leaf to `ALWAYS_EXCLUDED`'s cross-tree group,
  with that reason. The identity was already compared, so nothing more was needed.
- **The measurement.** The `exclusion_review` stage now measures this, in `PATH_CONTENT_WITNESS` and
  `G1_path_content_witness`. For each coupling-state path name, over G1's pairs, it checks three things: the identity
  leaf is present on both sides; it is compared, meaning excluded by no G1 table at that pairing; and the sibling path
  names the same file.

`--measure exclusion_review --resume` (`census press05`, `write-set press06`) gives the same result under both run IDs:

| path name | identity compared by | pairs carrying the path | identity compared / equal | same file as |
|---|---|---|---|---|
| `exit_audit.coupling_state` | `exit_audit.components_sha256` | 6 | 6 / 6 | — |
| `audit_snapshot.coupling_state` | `exit_audit.components_sha256` | 3 (the BR pairs) | 3 / 3 | `exit_audit.coupling_state` on 3 of 3 |
| `coupling_state_artifact` | `coupling_state_provenance.components_sha256` | 3 (the AR pairs) | 3 / 3 | — |
| `coupling_state_provenance.path` | `coupling_state_provenance.components_sha256` | 3 | 3 / 3 | `coupling_state_artifact` on 3 of 3 |

**The leaf added:** `audit_snapshot.coupling_state`. Its kind ("a path") is in `exclusion_review.ALWAYS_EXCLUDED_KIND`,
which is the import-time consistency check: every always-excluded name must carry a kind. Nothing else counts or lists
the names. The teeth reach `ALWAYS_EXCLUDED` only as the table they compare under.

**Other leaves checked.** I looked for any other path leaf, under `audit_snapshot` or a newer block, that agreed only by
location (T20). The same stage now lists every leaf of G1's pairs that holds an absolute path on either side
(`G1_path_valued_leaves`); it gives the same result under both run IDs.
- **17 names, 16 of them excluded by name:** `audit_snapshot.coupling_state`, `campaign_input_file`,
  `coupling_state_artifact`, `coupling_state_provenance.path`, `exit_audit.coupling_state`,
  `exit_audit.{,frozen.}restricted.{artifact,census}`, `outdir`, `per_run_artifact`, `process_copy_provenance.path`,
  `process_file`, `pythonpath`, `repository`, `tree`.
- **The one still compared is `python`:** the interpreter's path, equal on all 6 pairs. It is the environment, not the
  working tree. The two trees share one interpreter, and a different interpreter would be a real difference, so it is
  **not** added.
- **Under the write set, which straddles two trees,** every excluded path name differs on all its leaves (0 equal), and
  `python` is equal. Nothing in `audit_snapshot` or any newer block holds another path.

**G1 re-pressed** with `--gate switch_neutrality --resume` under each run ID. The before captures are archived and were
not re-made: the before manifest exists, so `_capture_before_if_there_is_none` returns. The six after records were kept
by the pool under each run ID.

| run ID | straddle | records | values compared / differing | lines compared / differing | verdict |
|---|---|---|---|---|---|
| `census_tau1e-08` (`press04`) | "one capture names no commit": the after records sit at two commits, `24b78e2d` (BR, A101's tree) and `d08e8ab4` (AR, A102's tree) | kept | 3 666 / 0 (was 3 669 / 0) | 51 319 / 0 | PASS, 9/9 |
| `write_set_tau1e-06` (`press05`) | `9ed0da4c → 52ea57be`, before in A101's tree, after in A109's | kept | 3 648 / 0 (was 3 651 / 3) | 51 319 / 0 | **PASS**, 9/9 |

The three values fewer under each run ID are the three `audit_snapshot.coupling_state` leaves, one on each BR pair. They
are now excluded by name: 1 718 excluded values under census, 1 740 under the write set. G1 was pressed again inside
each run ID's `--gate all` with the same numbers. The gate table rows read 54 985 (census) and 54 967 (write set):
values plus lines.

## 4. The two tables documents

`--paper-tables write`, each committed, and `--paper-tables check` reads **IDENTICAL** under each. Census: `press08`
and `press11`. Write set: `press17` and `press18`; the write-set cross-check against the stage records reads 0
mismatched of 178. Only the verification table and its stamp line moved in either document; no result cell moved.

- `paper_tables.md` (`58307581`): 1 file, 7 lines out, 7 in. They are the stamp line (now "30 record(s) at
  [0353c524, f3e576d3]") and the G0, G1, G6, G5, G9 and GT rows, re-dated to `f3e576d3`. The G1 row reads 0 of 54 985,
  where it read 54 988. The verdicts are unchanged: all PASS.
- `paper_tables_write_set_tau1e-06.md` (`e14977c9`): 1 file, 6 out, 6 in. They are the stamp line ("28 record(s) at
  [58307581]") and the G0, G1, G6, G5 and G9 rows. **G1 now reads PASS, 0 of 54 967; it read FAIL, 3 of 54 970.** GT
  reads "not pressed", as before.

## 5. Both campaigns are untouched

| check | census_tau1e-08 | write_set_tau1e-06 |
|---|---|---|
| `--jobs campaign --resume` | 553 of 553 kept, run 0 (`press10`) | 553 of 553 kept, run 0 (`press19`) |
| files under `campaign/` modified after this task's `START_MARKER` (`find -newer`, inspection) | 0 of 7 348 | 0 of 7 308 |

`tally_contracts` read all 553 campaign records at `a1db0a0c` and made none.

## 6. Files changed, decisions, limits, the unexpected

**Files changed** (all under `arch_surgery/`):
- `MDA_partitioning_experiment_v5/harness/gates/gate_evaluation_warmup.py`: rewritten to the read form.
- `…/harness/gates/archived_records.py`: the gate's archive entry; `--archive` filtering via `selected(only)`.
- `…/experiment_runner.py`: `--archive`.
- `…/harness/gates/gate_neutrality.py`: one entry in `ALWAYS_EXCLUDED`.
- `…/harness/gates/exclusion_review.py`: the kind; `PATH_CONTENT_WITNESS`, `path_content_witness`,
  `path_valued_leaves` and their printing.
- `…/harness/gates/registry.py`: a docstring and a comment.
- `…/harness/README.md`.
- The two tables documents.
- This report.

**Records changed:**
- **Under census:** `gates/evaluation_warmup/` gains `verdict_at_c2295511.json` and `archive_manifest.json`, and every
  re-pressed gate's `gate.json` was rewritten.
- **Under the write set:** the moves and copies in §2.

**Decisions taken alone, each with its reversal.**
1. **The verdict read is the `c2295511` record, not one "at `ff9e73a2`".** No record at `ff9e73a2` survives; the
   `c2295511` record is a `--resume` read of the `ff9e73a2` after records, and the gate code is identical between the
   two (§2). Reversal: set `VERDICT_COMMIT`, if a record made at `ff9e73a2` turns up.
2. **The read does not require `--resume`. GR's wrapper does.** GR refuses a press without it because such a press would
   re-make twenty jobs; this gate has nothing to re-make, and refusing would make a from-scratch `--gate all` stop at
   gate 16 of 29: the I-40 shape again. Reversal: raise in `body` when `resume` is false.
3. **The manifest of SHA-256 digests is taken at the first read.** No digest was recorded at `c2295511`, so
   "unchanged" means "since the first read", stated in the manifest itself. The re-derivation is what ties the files to
   the recorded numbers. Reversal: delete the manifest check, keeping the stamps and the reconciliation.
4. **The read verifies more than GR's: manifest, stamps, reconciliation.** The brief asked for "whatever GR's rule is"
   at least; GR's rule is the stamp alone, and its teeth are re-read from the record. Reversal: drop checks 2–3 and the
   three new teeth.
5. **`--archive <gate>` was added to the copy step,** because the whole copy refuses on an existing run ID (§2).
   Reversal: remove the option; a future copy of one archive would then need a fresh run ID.
6. **A106's FAIL record and its runs were kept under `superseded_A106_pressed_form/`, with a marker,** not deleted. The
   permission system refused nothing. Reversal: `mv` them back, or delete the folder.
7. **The path-leaf evidence went into the `exclusion_review` stage,** a measurement with no verdict, so that it comes
   from a committed script and is re-measured at every press. Reversal: remove the two blocks.

**Limits.**
- **The census G1 press is not a cross-tree test of the fix.** Its BR after records were made in A101's tree, as the
  before side was, so the leaf agreed there anyway. The write-set press is the cross-tree test: before in A101's tree,
  after in A109's.
- **A future archive of the warm-up gate must keep its manifest beside it.** Rewriting the after records — a log
  compaction that touched `metrics.json`, for instance — would make the read FAIL. That is by design.
- **The census G1 straddle line** still says "one capture names no commit", as A109 noted. The after manifest holds two
  commits (`24b78e2d`, `d08e8ab4`). This is unchanged and was not investigated.

**The unexpected.**
1. **`tally_contracts` FAILs under `write_set_tau1e-06`: 9 of 236 reference cells differ.** It reproduces 17 of GR's 20
   runs; its other 302 checks report 0 mismatched; 18/18 teeth (`press13`). All nine are the three `A2` seed-1
   evaluation runs, three cells each: `node_calls_single_eval` (expected 60 / 60 / 62, found 63 / 63 / 66),
   `n_model_calls_sweeps` (13 / 13 / 15 against 14 / 14 / 16) and `exit_audit.residual_max_hex`.
   - **The records it read.** The tally resolves those three jobs to `gates/_runs/A_A2_<configuration>_seed001_gate_*`,
     records stamped `52ea57be` and `campaign_test_set = write_set`, `campaign_tau = 1e-06`, written 13:30:14–13:30:29.
   - **Who made them.** A109's press of G6 (`entry_and_warm`). Its job listing logged them as "re-made: 4 declared
     field(s) missing: campaign_test_set, loop_test_sets, evaluation_warmup, evaluation_warmup.agrees"
     (`_press_logs/A109/press00_jobs_entry_and_warm_before.log`).
   - **Why they cannot reproduce V4.** They are the write set's evaluations, so they cannot reproduce V4's census-set
     cells.
   - **Why the earlier PASS.** The gate's last verdict before this task was A106's, at `a1db0a0c`, made before those
     records existed. A109 did not re-press it, so its gate table carried A106's PASS.
   - **Under census** the same gate reads PASS, 236 of 236.
   - **What I did.** This task changed nothing the tally reads. It is the same class as I-40: a gate whose
     reproduction contract is about the census set composes its jobs under the run ID's settings, through the shared
     pool. Not changed, per the brief; a failed gate is a result. It does not move the tables documents: their
     verification table does not carry this gate, and no result cell moved.
   - **Inferred, not tested:** a fresh press of `tally_contracts` under any non-default run ID would fail the same way
     once G6 has re-made those three jobs there.
2. `--copy-archived-records` cannot be re-applied to an existing run ID: 67 conflicts (§2). That is what `--archive`
   answers.

**Disk.** C: read 135 GB free at the start (13:50:39), before each write-set press, and at the end (13:58:01).

**Hand-back state.** The records tree is the one V5 tree, left in this worktree at
`arch_surgery/MDA_partitioning_experiment_v5/runs/`. The queue is not edited.

## Orchestrator's critical assessment (protocol §5) — verdict: merge

*Written 2026-10-01 by the orchestrating session. Checked differently from the agent.*

**Checked.** (1) `git diff --stat ff1abec4..6be87961`: ten files, all under the V5 harness, its runner, its README, the
two tables documents and this report; **0 diff lines under the V5 driver copy, `process/` or V4**; worktree clean; the
harness compiles. (2) The two tables documents moved in their verification table only (the stamp line and the gate
rows' commits and counts); no result cell moved; `--paper-tables check` reads IDENTICAL under both settings at the tip.
(3) `--runs` at the tip: `census_tau1e-08` 29 PASS of 29; `write_set_tau1e-06` 27 PASS, 1 FAIL, 1 not run. (4) The
gate's record under each run ID says in its own words that it is read, not pressed (D44), with the verdict's commit
and the re-derived comparison (1 426 count leaves, 0 differing). (5) Both campaigns: `--jobs campaign --resume` keeps
553 of 553 under each setting, and no file under either `campaign/` folder has a modification time after the task
began. (6) The G1 change is one entry in `ALWAYS_EXCLUDED`, with its content witness named.

**D44 is carried out as ruled.** The gate reads one verdict under every run ID and composes no job; `--gate all` under
the write set now stops only at GT's designed refusal. The decisions taken alone are accepted, among them reading
without `--resume` (decision 2), which is what keeps a from-scratch chain from stopping at this gate.

**The cause of the `tally_contracts` FAIL under the write set, corrected.** The report says the three re-made runs
"cannot reproduce V4's census-set cells". V4 has no census set: V4's predicate *is* the whole write set at τ = 1e-6,
and that is exactly why the failure occurs. Read by the orchestrator from the records: the three job digests
(`e09d9d61…`, `e962abd5…`, `0a51a121…`) exist under both run IDs. Under `census_tau1e-08` they are the reproduction
gate's records, made by the V4-identical driver copy at `66bfa240` (13 / 13 / 15 sweeps, no deferred set executed).
Under `write_set_tau1e-06` gate G6's `A2` seed-1 jobs have the **same job identity**, because the run ID's settings are
V4's; the copied reproduction records lacked four fields the record contract now owes, so A109's G6 press re-made them
with today's driver (stamped `52ea57be`; 14 / 14 / 16 sweeps). The difference is the phase A once-execution of the
deferred set (item 5): one dispatch sweep and the three post-processing nodes (four on `st`) per evaluation, which is
the 60 → 63, 60 → 63, 62 → 66 in node calls. So the tally's contract gate compares today's driver with V4's reference
cells on those three jobs and reports a real, intended driver difference as a mismatch. Not a property of the
campaign's records, and not of this task. Filed as I-41. The originals are intact under `census_tau1e-08`.

**What this leaves.** Under `write_set_tau1e-06`: `tally_contracts` FAIL (I-41) and GT not run by design. Neither is in
the tables document's verification table, and no cell of a result table depends on either.
