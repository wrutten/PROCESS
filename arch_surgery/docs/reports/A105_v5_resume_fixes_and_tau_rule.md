# A105 (v5-resume-fixes-and-tau-rule) — crashed records kept under `--resume` (I-38), `--jobs` on the reproduction gate's unnamed job (I-36), and the loop tolerance per configuration as a named-rule capability

> **Document status** — **ACTIVE (task report, open).** Branch `A105-v5-resume-fixes-and-tau-rule`, from
> `59f36aed`. Harness only: nothing under the V5 folder's `PROCESS/`, nothing under `process/models/`,
> nothing under `MDA_partitioning_experiment_v4/`, no sibling clone touched. Records relocated to
> `arch_surgery/idf_probe/runs/v5_resume_fixes_and_tau_rule/` (§9).

## 1. Verdict

All three parts are built, each with a tooth, and **no default moved**.

1. **I-38 — done.** A crashed record that is *complete as a crash* is now kept by `--resume`. On the seeded
   campaign, a resumed campaign press **would re-make 0 of 553 records** (`--jobs campaign`). Before the
   change it would have re-made **20 of 553**, every one of them for `status is 'crashed', not 'ok'`.
2. **I-36 — done.** A directory under another gate's root (`runs/gates/<gate>/`, but not the shared pool
   `runs/gates/_runs/`) is never a candidate for an unnamed job. `--jobs reproduction` used to crash with a
   `PoolError` naming five of G1's capture directories; it now lists 29 jobs. `--jobs all` lists **688
   distinct jobs over 29 gates** with rc 0. The reproduction gate still only reads its copy-commit verdict;
   nothing here makes it press.
3. **Tolerance rule — built as a capability, off by default.** `--tau-rule <name>` / `Campaign.tau_rule`
   gives each configuration its own τ = factor × `epsvmc`, read from that configuration's committed input
   file. Two rules are declared:
   - `epsvmc_times_epsfcn` gives tok 1e-10, lad 1e-11, st 1e-12.
   - `epsvmc_times_tenth_epsfcn` gives 1e-11, 1e-12, 1e-13.

   A rule is refused together with `--tau`. With no rule (the default), the seeded campaign resumes **553 of
   553**. `resume_identity` shows that a rule's identity is distinct from both the plain job's and a
   `--tau` job's at the same value, and that the plain identity carries no `tau_rule` key. The six smoke
   runs under the first rule (B0 and B2 at seed 0, phase B, on every configuration) stamp τ = 1e-10 / 1e-11
   / 1e-12 and all finish `ok`.

**Gate table after: 29 PASS, 0 FAIL, 0 not run; 176 of 176 teeth tripped** (it was 166 of 166). On the
way there, one press FAILed: `--gate composition` at `d218b879` (§5.2), with five new teeth undeclared. I
declared them in `2bd27bf5` and the re-press passed. **`--paper-tables check` reads IDENTICAL** after a
re-render in which exactly one line moved: the verification table's `gate_table` stamp line (§6).

**Nothing about which tolerance or test set the experiment uses is decided here.** That is the user's
open question (OQ-tolerance). The smoke counts in §4.4 are plumbing evidence only.

## 2. Part 1 — I-38: a crashed record is kept under `--resume`

**Cause, measured.** The brief said a crashed record "lacks fields the contract owes a finished record".
The seeded crash records do not lack fields: `records.missing_fields` reads `[]` on them, because the
contract owes a non-`ok` record only its `always` fields. They were re-made by the first comparison in
`records.why_not_complete_for`, `status != "ok"`, which re-makes every non-`ok` record.

**What was built.**
- **`pool.why_not_kept`** (`824ea5a6`) is now the one resume decision. It combines the completeness
  contract with the composition check (`why_not_composed_as_today`). `pool.run` keeps a record exactly when
  it returns None, and `pool.job_listing` prints its sentence. Before this, the listing consulted the
  contract alone. Re-listing every gate that declares a job set gave byte-identical output before and after.
- **`--jobs campaign`** lists the campaign press's job set. It is composed exactly as the press composes it
  (`chain.campaign_jobs` per run stage, under `campaign_press_composition`, timers on), and shows what
  `--resume` would keep, without running anything.
- **The crash contract** (`a227e8a5`, `records.why_not_complete_as_a_crash`). A record whose status is not
  `ok` counts as complete only when all of the following hold:
  - `status == "crashed"`;
  - `failure_class` is in `CRASH_KEPT_FAILURE_CLASSES` = (`crashed`, `unconverged`, `unconverged-at-cap`),
    the rows that are results about the models or the arrangement;
  - `traceback_last_line` (the exception and its message) is not empty;
  - the pool's `launcher` block carries `spawned_at`, `returned_at` and `wall_s`.

  On top of that, every comparison an `ok` record goes through still applies: the readable identity, the
  child's stamps, `job_identity`, the digest and its re-derivation, the always-owed fields, and the
  composition check. A crash record missing any of these is re-made, as before.

**Tooth** (`resume_identity`, "a crash is kept only when complete as a crash"). A synthetic complete crash
record is kept. The same record with its traceback emptied, with its launcher removed, or with failure class
`machinery` is re-made, and each refusal names what is missing. TRIPPED.

**Evidence** (`--jobs campaign --json`):

| at | entry references | displaced evaluations | optimisations | all | would re-make |
|---|---|---|---|---|---|
| `824ea5a6` (before the contract; `press01`, `jobs_campaign_before_crash_contract.json`) | 3/3 kept | 275/275 | 255/275 | 533/553 | **20**, all "status is 'crashed', not 'ok'" (tok BR/B0/B1/B2 seeds 5, 20, 21; lad BR/B0/B1/B2 seeds 3, 21) |
| `a227e8a5` (`press03`) | 3/3 | 275/275 | 275/275 | 553/553 | **0** |
| tip `fe5eb615` (`press28`, `jobs_campaign_at_tip.json`) | 3/3 | 275/275 | 275/275 | 553/553 | **0** |

*Caption: one row per commit. The cells are the campaign press's distinct jobs that `--resume` would keep,
over the jobs composed. The population is the 553 seeded campaign records of A102 (v5-campaign). Each
listing is the pool's resume decision (`pool.why_not_kept`), read without running.*

## 3. Part 2 — I-36: `--jobs` on the reproduction gate's unnamed job

**Choice: the rule, not a named directory** (`897bc357`). A directory under another gate's root is never a
candidate for an unnamed job. In `pool.directory_for`, step 2 (resolve by digest) now skips every hit for
which `pool.is_under_another_gates_root` is true, meaning under `runs/gates/<x>/` with `x != _runs`.

**Why the rule.** A directory under a gate's root is that gate's *named* record: G1's `before`/`after`
captures, or an archived straddle made at another commit. If an unnamed job resolves into one, the job
reads a capture made at another commit as its own record. A press without `--resume` would then remove that
capture and re-make it. That is the mirror image of I-29, and it applies to every unnamed job, not only to
GR's substitutes. A named directory under GR's root would have fixed `--jobs reproduction` but left this
hazard open for every other unnamed job.

Hits elsewhere under `runs/` stay candidates:
- the campaign directories under the arms' recorded names (the reason step 2 exists);
- a stage's named directory, such as the input-file stage's baseline evaluation, which GR's AR substitute
  resolved to at the copy commit.

`stage_jobs` now reports a pool refusal as `REFUSED by the pool` (rc 3) instead of crashing.

**Tooth** (`resume_identity`, "an unnamed job never resolves into another gate's root"). In a scratch
`runs/`, a complete record of an unnamed AR job's digest is placed first in one and then in two of G1's
capture directories. The job resolves to its canonical pool directory both times. With a third copy under
`runs/elsewhere/`, it resolves to that copy by digest. On the old code the first case resolves into the
capture, so the tooth bites. TRIPPED.

**Evidence.**
- `--jobs reproduction`:
  - at `59f36aed`, rc 1: `PoolError … 5 directories … hold a record of this job's digest 34d6ec64…`, all
    five under `gates/switch_neutrality/straddles/`;
  - after the change, rc 0: 29 distinct jobs, `--resume` would keep 3.
- The AR substitutes now resolve as follows:

  | configuration | resolves to | listed as |
  |---|---|---|
  | tok, lad | their canonical pool directories | "no record on disk" (their copy-commit records were the input-file stage's baseline evaluations, since re-made under the census set) |
  | st | `_runs/A_AR_st_regression_seed000_gate_52070b81…` | that record, re-make reason "5 declared field(s) missing" |

  These are honest listings. GR never runs them: under `--resume` it reads its verdict.
- Every other gate's listing (13 gates with job sets) is byte-identical across `897bc357`, apart from
  reasons that changed because of Part 1 (`jobs_after_gate_root_rule/` against `jobs_1a/`). In
  `tally_contracts` and `run_kind_separation`, 20 lines now read "the child stamped campaign_timers=True and
  the job's timers is False" where they read "status is 'crashed'". Those two gates compose the campaign
  plainly, so none of their 553 campaign jobs match the timed campaign records (see Limits).
- **`--jobs all` at the tip** (`press29`), rc 0: **688 distinct jobs over 29 gates; 1 293 gate-job
  declarations; 590 jobs read by more than one gate; `--resume` would keep 87**. The low keep count comes
  from the 553 campaign jobs that `tally_contracts` and `run_kind_separation` list under the plain
  composition (Limits). It is not a resume failure: the campaign press's own listing keeps 553 of 553.

## 4. Part 3 — the loop tolerance per configuration, as a capability

### 4.1 What was built (`17a7dc23`)

**The rule** (`config.TauRule`, `config.TAU_RULES`): τ = `factor_multiplier` × [the input file's
`factor_setting`] × `epsvmc`.
- Both `epsvmc` and the factor setting are read from the configuration's **committed** input file by
  PROCESS's own line rule (`config.read_real_setting`: `*` starts a comment, `name = value`). A file that
  sets the variable twice is refused.
- Where the file sets no value, PROCESS's default applies (`PROCESS_OPTIMISER_DEFAULTS`: `epsvmc` 1e-6,
  `epsfcn` 1e-3). These are checked against the copy's `process/data_structure/numerics.py` by the
  composition self-check.
- τ is rounded to 12 significant digits, so that it reads `1e-10` rather than `1.0000000000000001e-11`.

The two declared rules:
- `epsvmc_times_epsfcn`: factor = `epsfcn`.
- `epsvmc_times_tenth_epsfcn`: factor = `epsfcn` / 10, the retry ladder's smallest step.

| rule | `large_tokamak_nof` | `low_aspect_ratio_DEMO` | `st_regression` |
|---|---|---|---|
| `epsvmc` read (line) | 1e-7 (18) | 1e-8 (23) | 1e-9 (42) |
| `epsfcn` read | PROCESS default 1e-3 | PROCESS default 1e-3 | PROCESS default 1e-3 (line 46 is the comment `*epsfcn = 0.001`) |
| τ, `epsvmc_times_epsfcn` | 1e-10 | 1e-11 | 1e-12 |
| τ, `epsvmc_times_tenth_epsfcn` | 1e-11 | 1e-12 | 1e-13 |

*Caption: one column per configuration. The first two rows are what the rule reads from the committed input
file. The last two rows are the τ each declared rule gives, from the composition self-check's note at the
tip (`press07`).*

**Where the rule reaches.**
- `Campaign.tau_rule` (None by default). `Campaign.tau_for(config)` returns the rule's τ, or `campaign.tau`
  when there is no rule.
- `--tau-rule`, refused with `--tau`, both in the runner and in `Campaign.__post_init__`.
- `arms.terms` composes `tau_for(config)`, so the rule reaches the flat and partitioned loops. The reference
  arm composes no tolerance and is untouched.
- `pool.resolve_settings`: a job that names no τ takes the campaign's τ for its configuration and carries
  the rule's name. A job that names its own τ (the supplementary stage, GR's V4 criterion) keeps that τ and
  carries no rule. A job carrying a rule the campaign does not compose is refused.

**Identity and stamps.**
- `Job.tau_rule` is a job-identity field, **rendered only when set** (`IDENTITY_DEFAULTS_WHEN_ABSENT
  ["tau_rule"] = None`). No job without a rule renders it, so no default identity or digest moves.
- The child stamps `campaign_tau_rule`, only when it is given. The pool stamps `tau_rule_derivation`: the
  formula, `epsvmc` and where it was read, the factor setting, and τ.
- The schema declares both fields `when == "tau_rule"`. Only a rule's record owes them, which is decided by
  the stamp or by `job_identity.tau_rule`.
- A rule campaign's chain writes under `runs/campaign_tau_rule_<rule>/`. Without this, its named jobs would
  share readable identity with the default campaign's and a press would remove the default records to make
  room.
- `--run` directories carry `_rule_<name>`. The matrix's stopping-rule cell reads `τ by rule <name>`.

### 4.2 Teeth and checks

- **Composition self-check** (5 new teeth, all TRIPPED in `press07` default, `press08` under the tenth
  rule, `press09` under the first rule, and the `--gate composition` press `press17`):
  - an input file with `epsvmc` doubled doubles τ;
  - an `epsvmc` line turned into a comment falls back to PROCESS's 1e-6;
  - a file setting `epsvmc` twice is refused;
  - a rule together with an explicit τ is refused;
  - an undeclared rule is refused.

  Statements checked: the declared defaults equal the copy's `numerics.py`; every rule × configuration
  derivation equals factor × `epsvmc`; A0/B0/A2/B2 compose exactly `tau_for(config)`; without a rule every
  configuration's τ is the campaign's one τ.
- **Capability** under the first rule (`press09`): 22 arm/configuration pairs probed, PASS.
- **`resume_identity`** adds 6 tolerance-rule identity rows (rule × configuration). Each composes the flat
  control's seed-1 job three ways: no rule, the rule, and `--tau` at the rule's value. The no-rule and
  `--tau` identities carry no `tau_rule`, the rule's identity carries its name and τ, and the three digests
  are distinct. 6/6 hold.
- **`record_completeness` (G7)** gains a third run: a rule-stamped smoke evaluation of `A0` on
  `st_regression` under `epsvmc_times_epsfcn`, τ 1e-12, made once in the shared pool. Its record carries
  every declared field. It stamps the rule in the child, the identity and the derivation, with τ =
  `tau_for(st)`. Two new teeth (the field `campaign_tau_rule` removed, `tau_rule_derivation` removed) are
  each refused by name. 14/14 teeth.

### 4.3 The identity proof: nothing changes without a rule

- **The campaign.** `--jobs campaign` at the tip (no rule) keeps **553 of 553** (§2). The same listing
  under `--tau-rule epsvmc_times_epsfcn` lists every job as RUN: a different identity, under
  `runs/campaign_tau_rule_epsvmc_times_epsfcn/`, never the default records.
- **The gate listings.** All 13 gates with job sets list byte-identically at `17a7dc23` against
  `897bc357`. The one exception is `record_completeness`, which gains its new rule job
  (`jobs_after_tau_rule/`).
- **The records.** No campaign or supplementary record was written during the task (`find -newer`: 0
  files).
- **`resume_identity`** PASS (above).

### 4.4 The smoke pairs (plumbing evidence only — not results; no table is built from them)

The runs were made by `--run --arm {B0,B2} --configuration <c> --seed 0 --run-kind smoke --tau-rule
epsvmc_times_epsfcn`, two at a time (`press05_*`). They were read back with the same command plus
`--resume` at `d218b879` (`press06_*`: each "resumed", no PROCESS run).

| configuration | arm | stamped τ | `epsvmc` from | status | ifail | iterations | evaluations | solve-phase node calls | made at |
|---|---|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | B0 | 1e-10 | line 18 | ok | 1 | 8 | 630 | 45 654 | `17a7dc23` |
| `large_tokamak_nof` | B2 | 1e-10 | line 18 | ok | 1 | 8 | 660 | 23 330 | `17a7dc23` |
| `low_aspect_ratio_DEMO` | B0 | 1e-11 | line 23 | ok | 1 | 16 | 1 240 | 89 838 | `d218b879` |
| `low_aspect_ratio_DEMO` | B2 | 1e-11 | line 23 | ok | 1 | 13 | 1 050 | 37 599 | `d218b879` |
| `st_regression` | B0 | 1e-12 | line 42 | ok | 1 | 10 | 570 | 53 340 | `d218b879` |
| `st_regression` | B2 | 1e-12 | line 42 | ok | 1 | 10 | 570 | 22 092 | `d218b879` |

*Caption: one row per smoke run. Population: one seed (0, unperturbed), phase B, run kind `smoke`, rule
`epsvmc_times_epsfcn`, test set census, timers off, 1 attempt each. All runs are clean trees (`tree_git_dirty
false`). The two commits differ only by a print in the runner, which the children never import (§8 decision
6). This is plumbing evidence that the stamped τ is the expected per-configuration value and that the runs
finish. It is not a result, and no ratio may be read from it.*

## 5. The presses, at the tip

### 5.1 Commands

Every command below ran from the V5 folder with the project environment's Python,
`PYTHONDONTWRITEBYTECODE=1` and `HARNESS_WORKERS=2`. The logs are under `runs/_press_logs/A105/` (relocated,
§9).

| press | command | result |
|---|---|---|
| `press07` | `--selfcheck` | 7/7 PASS (capability included) |
| `press08` / `press09` | `--selfcheck [--no-capability] --tau-rule <rule>` | 6/6 and 7/7 PASS |
| `press10` | `--gate composition --resume` at `d218b879` | **FAIL**: 5 undeclared teeth (below) |
| `press11`–`16` | `--gate {capability, run_path, resume_identity, run_kind_separation, tally_contracts, record_completeness} --resume` at `d218b879` | PASS |
| `press17`–`22` | `--gate composition` at `2bd27bf5`, then `capability`, `run_path`, `resume_identity`, `run_kind_separation`, `tally_contracts` re-pressed at the tip | PASS |
| `press23` | `--measure gate_table --resume` | 29 PASS, 176/176 teeth |
| `press24`–`27` | `--paper-tables check` (refused) → render aside → `write` → `check` | IDENTICAL |
| `press28`, `press29` | `--jobs campaign`, `--jobs all` | 553/553; rc 0 |
| `press30` | `run_stamp_survey.py` | — |

`record_completeness` was pressed once, at `d218b879`. Nothing it reads changed after that: `2bd27bf5`
touched only the composition gate's declaration. That single press made two PROCESS runs, the new rule smoke
evaluation and the tooth's deliberate re-make of its smoke evaluation.

### 5.2 The failed gate

**`--gate composition` FAILed at `d218b879`** with 0 of 53 mismatched. The cause: the five new
tolerance-rule teeth ran and tripped but were not in `gates._selfcheck_gates`'s declared tooth list. This is
the framework working, in the same shape as A71's `run_path` finding. I declared them in `2bd27bf5` and
re-pressed: PASS, 12/12. The FAIL verdict record was overwritten by that re-press. Its log is kept
(`press10_gate_composition.log`).

### 5.3 The gate table after, with the rows that changed

| gate | verdict | population (abridged) | compared | mismatched | teeth |
|---|---|---|---|---|---|
| `composition` | PASS | 8 arms × 3 configurations = 24 pairs | 53 (was 42) | 0 | 12/12 (was 7/7) |
| `run_path` | PASS | unchanged | 12 | 0 | 12/12 |
| `resume_identity` | PASS | 26 Job fields; 12 by-design pairs; 6 tolerance-rule identity rows; 3 recorded-name rows; records read by arm name | 1 222 (was 1 208) | 0 | 13/13 (was 11/11) |
| `capability` | PASS | unchanged | 61 | 0 | 5/5 |
| `record_completeness` | PASS | 3 runs on `st_regression` (was 2), the third under `epsvmc_times_epsfcn` at 1e-12; 97 declared fields in phase B, 92 in phase A (each +2) | 281 (was 185) | 0 | 14/14 (was 12/12) |
| `tally_contracts` | PASS | 20 reference runs; 236 published cells; 94 tables | 538 (302 + 236) (was 506) | 0 | 18/18 |
| `run_kind_separation` | PASS | 1 175 run records under `runs/` (was 1 168), 553 in the published campaign family | 2 281 | 0 | 7/7 |

*Caption: the gate table's rows for the gates re-pressed by this task. The remaining 22 rows are unchanged
from A103's table at `c2295511`/`75b9e9d4`. Total: 29 PASS, 0 FAIL, 0 not run; 176 of 176 teeth tripped.*

The `tally_contracts` population line count and the `run_kind_separation` record count rose because this
task's smoke records are now under `runs/`. These are new records of kinds outside every published
population. None of the 553 campaign records is touched.

## 6. `paper_tables.md`

`--paper-tables check` refused after the re-presses. I rendered the document aside
(`--paper-tables-out`), and the diff showed **exactly one line**. It is line 437, the verification table's
stamp: "the gate_table stage record read 30 record(s) at [`0353c524`, `75b9e9d4`, `c2295511`]" became
"[`0353c524`, `2bd27bf5`, `c2295511`, `d218b879`]".

No cell moved. None of the verification table's gate rows (G0, G1, G6, G5, G9, GT) was re-pressed. I
re-rendered with `write` (`fe5eb615`). `check` then reads IDENTICAL, with the cross-check at 0 mismatched of
178.

## 7. Files changed (all under `arch_surgery/MDA_partitioning_experiment_v5/`)

| file | part | what changed |
|---|---|---|
| `harness/core/pool.py` | 1, 2, 3 | `why_not_kept`, `NO_RECORD_ON_DISK`; `is_under_another_gates_root` and its use in `directory_for`; `Job.tau_rule` and its identity rendering, `resolve_settings` per configuration, readable key, `--tau-rule` on the child command, `tau_rule_derivation` stamp |
| `harness/core/records.py` | 1, 3 | `CRASH_KEPT_FAILURE_CLASSES`, `CRASH_LAUNCHER_FIELDS`, `traceback_last_line`, `why_not_complete_as_a_crash`, used by `why_not_complete_for`; `tau_rule` child stamp and default; schema fields `campaign_tau_rule`, `tau_rule_derivation` (`when == "tau_rule"`) |
| `harness/core/config.py` | 3 | `PROCESS_OPTIMISER_DEFAULTS`, `read_real_setting`, `TauRule`, `TAU_RULES`, `tau_rule_named`, `Campaign.tau_rule` / `tau_for`, `default_campaign(tau_rule=)` |
| `experiment_runner.py` | 1, 2, 3 | `--jobs campaign`; pool refusals in `--jobs`; `--tau-rule` (refused with `--tau`); `--run` prints stamps and counts; press records under `chain_root` |
| `harness/chain.py` | 3 | `chain_root` under a rule |
| `harness/child/{child,evaluate,optimise}.py` | 3 | `--tau-rule` stamped as `campaign_tau_rule`, only when given |
| `harness/experiment/arms.py` | 3 | `tau_for(config)`; stopping-rule text under a rule |
| `harness/gates/gate_resume_identity.py` | 1, 2, 3 | two teeth; tolerance-rule identity rows |
| `harness/gates/gate_records.py` | 3 | rule-stamped smoke run, two field teeth, job listing |
| `harness/gates/selfcheck.py`, `gates.py`, `gate_composition.py` | 3 | the tolerance-rule checks and their five declared teeth; `tau_for` in the composition comparisons |
| `harness/README.md` | 1–3 | §4, §5, §12, §13 |
| `paper_tables.md` | — | the one stamp line (§6) |

## 8. Decisions taken alone, with reversals

1. **Which crash rows are kept.** Kept: `crashed`, `unconverged`, `unconverged-at-cap`. Not kept: `refused`
   (a driver refusal depends on harness inputs that can change without changing the identity) and
   `machinery`. *Reversal:* edit `records.CRASH_KEPT_FAILURE_CLASSES`.
2. **I-36 by the gate-root rule, not by a named directory for GR's substitutes** (§3). *Reversal:* drop the
   filter in `directory_for` and give `reproduction.substitute_ar_jobs` an `outdir` under
   `runs/gates/reproduction/`. That is not an identity field, so no digest moves.
3. **`tau_rule` is a job-identity field**, beyond the brief's "τ in the identity". Without it, a rule's st
   record (1e-12) would share its identity with a `--tau 1e-12` campaign's record. *Reversal:* remove it from
   `JOB_IDENTITY_FIELDS`. No record made without a rule moves either way.
4. **τ rounded to 12 significant digits.** *Reversal:* drop the rounding in `TauRule.derivation`. Only rule
   records' digests depend on it.
5. **Rule campaigns get their own chain root** (`runs/campaign_tau_rule_<rule>/`), because a press would
   otherwise remove the default campaign records. *Reversal:* the branch in `chain.chain_root`. The default
   root is unchanged.
6. **Two smoke runs were made at `17a7dc23` and four at `d218b879`.** The runner's print change was
   committed while the pair runs were in flight. The two commits differ only in `experiment_runner.py`'s
   printing, every record is clean, and all six were read back at `d218b879`. *Reversal:* re-make the two
   tok runs at the tip (two smoke runs).
7. **The rule reads the committed input file, also for arms that run the lifted file.** The lifted file
   differs by the three declared lines, and none of them is `epsvmc` or `epsfcn`. *Reversal:* read
   `arms.input_file_for(...)` in `TauRule.derivation`.
8. **G7's rule run uses the flat control `A0`** (its loop takes the τ) rather than the reference arm.
   *Reversal:* `gate_records.RULE_ARM`.

## 9. Records

`runs/` was moved whole by `mv` on the same filesystem to
`arch_surgery/idf_probe/runs/v5_resume_fixes_and_tau_rule/`. The record count was identical before and
after the move (§Appendix, last entry).

New records made by this task:
- six rule smoke runs, under `single/<config>/<arm>/census_tau<τ>_rule_epsvmc_times_epsfcn/seed000/`;
- G7's rule smoke evaluation, under `gates/_runs/A_A0_st_regression_seed000_smoke_88d091da…`;
- G7's re-made smoke evaluation (its tooth).

Re-written verdict records: `gates/{composition, capability, run_path, resume_identity, record_completeness,
run_kind_separation, tally_contracts}/gate.json` and `gates/gate_table/measurements.json`.

## 10. Limits

- **The tallies, gate bodies and the paper-table renderer that read `campaign.tau` directly are not
  rule-aware.** That covers `tally_evaluation`'s fixed-point distance, `gate_entry`'s cross-residual,
  `reproduction`'s fixed-point row, the tally captions, and `tally.CAMPAIGN_RUNS_SUBPATH`'s survey of
  `runs/campaign/`. Under a rule, `campaign.tau` keeps the test set's declared value. A task that presses a
  rule campaign must make those consumers use `tau_for(config)` and the rule's chain root before any table is
  read from it. Only the composition and capability checks, G5's plan column, the arms, the pool, the child
  and the chain are rule-aware here.
- `tally_contracts` and `run_kind_separation` declare the campaign's jobs under the plain composition (timers
  off), so `--jobs` on them, and `--jobs all`, list the 553 campaign jobs as not kept. This is a listing
  artifact of I-37's class. The reading itself goes through the tally sources, and both gates PASS.
- GR's AR substitutes on tok and lad have no record on this tree. Their copy-commit records were the
  input-file stage's baseline evaluations, since re-made under the census set. GR's verdict is its archived
  read and is unaffected, but `--jobs reproduction` shows them as "no record on disk".
- The smoke pairs are one seed, phase B, timers off, and not a result.

## Appendix — change log (append-only)

- 2026-09-30: `824ea5a6` one resume decision and `--jobs campaign`; before-listing 533/553.
- 2026-09-30 → 2026-10-01: the orchestrating session ended at about 18:04 with the I-38 contract and its
  tooth uncommitted. No press was in flight; only `--jobs` listings and one `resume_identity` trial had run.
  Resumed from disk the next morning.
- 2026-10-01: `a227e8a5` (I-38), `897bc357` (I-36), `17a7dc23` (tolerance rules), `d218b879` (`--run`
  prints), smoke pairs; `--gate composition` FAIL on undeclared teeth, `2bd27bf5` declared them; presses at
  the tip; `fe5eb615` `paper_tables.md` stamp line; this report; `runs/` relocated by `mv` (same
  filesystem): 1 175 `metrics.json` and 17 905 files before, 1 175 and 17 905 after.
