# A72 (resume-identity-and-shared-pool) — the job identity, the retired allowance, the shared run pool

> **Document status** — **OPEN.** Task **A72 (resume-identity-and-shared-pool)**, branch
> `A72-resume-identity-and-shared-pool` off `architecture_surgery` at base `77d3c2fd` (after A70
> and A71). Ruling **D27**; issue **I-23**; survey items **B4** and **B1**. The one schema change of
> the programme. Every number below was produced by a committed script or the committed button
> (`experiment_runner.py`, `harness_survey.py`, `run_stamp_survey.py`) at the commit named beside
> it. Folder position records lifecycle, not validity (trap T3).

*Vocabulary is the harness README's §3. "Job", "identity", "digest", "shared pool" as defined in
§2 below; "press", "tooth", `--resume` as in A68's preamble.*

## 1. Verdict in one page

| item | done | what changed | evidence |
|---|---|---|---|
| **I-23** the job digest | yes | `pool.JOB_IDENTITY_FIELDS` (20 names) is the one list of what the pool composes into a run; `Job.identity()`, `Job.key`, `records.job_digest` and the pool's directory derive from it; the pool stamps `job_identity` and `job_digest` into every record after the child returns; `records.is_complete_for` compares the readable six, every identity field the child also stamps, the stamped identity field by field, and the digest (which must re-derive) | gate `resume_identity` PASS 35/35 with 5 teeth tripped at `8d5099a1`; §3, §5 |
| **B4** the allowance retired | yes, harness side | `Job.allow_pending`, `--allow-pending`, `pending_switches_allowed` (schema), `arms.env_for(pending_ok=…)`'s pool caller, the "pending switch" vocabulary row, the tooth *an allowance naming a switch the tree does implement*; `assert_capable`'s refusal and the tooth on it kept | `run_path` 13 → 12 teeth, PASS at `cacf3f78` under `--resume`; the child-side remainder is listed in §9 for A73 |
| **B1** the shared run pool | yes | one directory per job identity under `runs/gates/_runs/`; every run-making gate declares the jobs it reads (`Gate.jobs`), composed from the records on disk by the gate's own constructor; verdicts carry the resolved paths relative to `runs/gates/`; `tally.SOURCES` and `analysis.SOURCES` name job sets, independently | `--gate entry_and_warm`: 19 records under `_runs/`, then `--resume` → **0 runs, 19 kept** (§6); `--jobs all`: 126 distinct jobs over 242 gate-job declarations, 42 read by more than one gate (§7) |
| the schema | 100 → **101** fields | −`pending_switches_allowed`, +`job_identity`, +`job_digest`; B 89 → 90, A 82 → 83 | `records.SCHEMA` at `5555d674`; every pre-A72 record is incomplete under `--resume` (amendment 17 (a)), by construction — a record with no digest is refused (tooth) |
| the registry | 29 → **30** gates, 148 → **152** teeth | new 0-run gate `resume_identity` (5 teeth); `run_path` −1 | `--gates` diff against `77d3c2fd` (§8) |
| the one press | 19 runs planned, **57 made** | the first `--resume` re-made all 19: the identity carried a phase-B default the child does not stamp for an evaluation. Fixed (`1114773d`), the 19 orphaned directories deleted, the gate pressed again (19), `--resume` twice (0, 0) | §6 — a failed proof is reported, not smoothed over |
| lines | 46 318 → **47 783** | +1 465: the identity machinery, the new gate, the `--jobs` listing, the import walk | `harness_survey.py` §1 at `77d3c2fd` and `8d5099a1`; this is a mechanism, not a simplification, and the count says so |

**What A73's press must show** (§10): the from-scratch population under the pool, the saving in
runs against the per-gate-directory count (projected 152 → 132, §7; the survey's 44 of 170 assumed a
looser notion of "the same run" than the identity grants — §7 says which classes and why), G1's
straddle over the kept before capture with the three new conditional exclusions, and the retired
allowance's child-side remainder.

## 2. The identity, and how it is built

**One list.** `harness/core/pool.py::JOB_IDENTITY_FIELDS`:

```
phase, arm, configuration, seed, regime, run_kind,
delta, pin_hex, entry_state, stencil_column, stencil_sign,
predicate_mode, node_census, census_entry, census_read, force_maxcal,
override_env, reproduction_overrides, audit_position, audit_position_caller
```

`configuration` stands for `config.name`. The three fields of `Job` that are **not** identity are
`JOB_NON_IDENTITY_FIELDS = (config, outdir, timeout)`, each with its reason in the source: `config` is
rendered as its name; `outdir` is what the identity *determines*; `timeout` is a limit on the run, not
a property of it — a run that finished under a shorter limit is the same run, and one that reached the
limit has no `ok` record and is never kept. The module refuses to import if the two lists do not
between them name every field of `Job` (`_assert_every_job_field_is_classified`; tooth *an
unclassified job field*).

**One construction.** `Job.identity(runs_dir)` renders the twenty fields as JSON-safe values in the
declared order: a path relative to `runs/` where it lies under it (a seeded or relocated worktree is
the same job — amendment 18's reason for not comparing paths in `runs_provenance`), a mapping with
sorted keys and string values, `None` as null. Two renderings are not the raw field:

- `audit_position` is rendered as the position the run will **stamp**
  (`records.effective_audit_position`): an optimisation's as asked, an evaluation's as
  `after_single_evaluation` whatever the job's default says — because the pool passes no position to
  `evaluate.py` and the child has one — a census's as null; `audit_position_caller` is null off phase B.
  This is the finding of §6.
- `entry_state` is the **path**, not the file's digest (decision 2, §11).

From that dictionary: `Job.key` (the readable half — `phase/arm/configuration/seedNNN/regime/kind`
plus whatever is off its default: `delta=`, `mode=`, `audit=`, `asked_by=`, `stencil=`, `maxcal=`,
`overridden`, `reproduction_overrides`); `records.job_digest` (sha256 of the canonical JSON: sorted
keys, no whitespace, ASCII); and `pool.directory_for` — `runs/gates/_runs/<phase>_<arm>_<configuration>_seed<NNN>_<kind>_<digest[:16]>`
where the job names no `outdir`. `records.job_digest` lives in `records.py` so that a reader can
re-derive a record's digest from its stamped identity without importing the pool.

**Where the stamp is made.** `pool.stamp_identity`, after the child returns: the pool reads
`metrics.json`, adds `job_identity` and `job_digest`, re-evaluates the child's `completeness` block
(computed before the two fields existed), and writes it back. Not by the child — no run-path edit was
made (decision 3). The job's identity and digest are also written into `command.json`.

**What `--resume` compares** (`records.why_not_complete_for`, in order; `is_complete_for` is its
boolean): the record finished; the readable six (`campaign_arm`, `campaign_configuration`,
`campaign_seed`, `campaign_phase`, `regime`, `campaign_run_kind`) against the job; every identity
field the child also stamps (`IDENTITY_FIELDS_STAMPED_BY_THE_CHILD`: those six plus
`campaign_delta`, `campaign_pin_hex`, `campaign_predicate_mode`, `audit_position`) against the job;
the stamped `job_identity` against the job's, field by field, and no extra field; the stamped
`job_digest` equal to the job's **and** re-deriving from the stamped `job_identity`; then
`missing_fields`. Each refusal is a sentence naming the field; `--jobs` prints it (§7).

## 3. The schema change

| | before (`77d3c2fd`) | after (`8d5099a1`) |
|---|---|---|
| `SCHEMA` fields | 100 | **101** |
| optimisation phase (G7's `n_declared_fields`, B) | 89 | **90** |
| evaluation phase (A) | 82 | **83** |
| removed | `pending_switches_allowed` (AB, always) | |
| added | | `job_identity` (AB, always): "every field the pool composed into this run, rendered once (pool.JOB_IDENTITY_FIELDS): what --resume compares"; `job_digest` (AB, always): "sha256 over the canonical JSON of job_identity; the shared pool's directory carries its first sixteen digits" |
| `FORMAT` tag | `run-record-1` | unchanged (decision 8) |

G7's count is derived (`len(records.declared_field_names(phase))`), so it moved with the schema;
nothing was retyped. Consequence, stated and not weakened (amendment 17 (a)): every record made before
`5555d674` lacks `job_digest` and is incomplete under `--resume`. The seeded worktree's 184 records
under the old per-gate directories are in that state; §6's press did not touch them and §9 asks A73
to remove them before the from-scratch press.

The child still writes `pending_switches_allowed` (an empty list) — the field is undeclared now, which
the contract permits — until A73 takes the child-side remainder (§9). G1's conditional exclusion for
it is already in place (§4).

## 4. The shared pool's layout, and how each deliberate second run keeps its identity

**Layout.** `runs/gates/_runs/<identity>/` for every job that names no `outdir` — every run-making
gate's runs, G7's two smoke runs included. Gate verdicts and manifests stay under
`runs/gates/<gate>/`; G4's doctored entry states stay under `runs/gates/audit_restriction/<config>/_entries/`
(their paths are in the doctored jobs' identities). The chain (`--smoke`, the campaign) keeps its
explicit layout under `runs/<kind>/`; its records carry the two identity fields like every other.

**The one job three gates make** is now one construction: `reproduction.entry_reference_job(config)`,
used by `gates.entry_reference_jobs` (G2, G3, G4, G6), GR's prerequisites and G8's reference — where
the survey (§2) counted the cold `A0` seed 0 made three times per configuration under three
directories. Under the pool it is one record, and a job entered from it carries
`gates/_runs/<its directory>/y_exit.json` in its identity.

**Each gate declares the jobs it reads** (`Gate.jobs`, via `gates.job_rows(jobs_read, campaign)`),
composed from the records on disk by the gate's own constructor — `gate_entry.jobs_read`,
`gate_prime.prime_map_jobs_read` / `cold_chain_jobs_read`, `gate_audit.jobs_read` (baselines, then the
doctored runs once a baseline record exists), `gate_composition.jobs_read`, `gate_records.jobs_read`,
`gate_predicate_mode.jobs_read`, `gate_output_path.jobs_read` (its own runs and GR's seed-0 records of
the reference arms, which it compares against), `gate_written_file.jobs_read` (its six and G9's beside
records), `reproduction.jobs_read` (references, the twenty planned, the two substitutes, the
composition tooth's run). `Gate.run` surveys those directories and writes `runs_provenance.jobs`
(key, digest, path relative to `runs/gates/` — trap T12) into the verdict. A gate whose prerequisites
are not made yet says so by name (`GateError` / `ReproductionError`, recorded as
`runs_provenance.jobs_not_composable` when a body refused before making them).

**One run per job per press.** `pool._MADE_THIS_INVOCATION` remembers the digests this process made
or kept; a later gate of the same press composing the same job is served the record — after the same
`is_complete_for` check as everywhere (rule (vii), trap T13: the ledger never decides alone). This
generalises `gates._ENTRY_REFERENCES_MADE`, which did it for one job set and is retired. A caller that
wants the same job made again in the same process says `fresh=True` — G7's tooth *a stale run is
re-made without --resume* is the one caller.

**The deliberate second runs.** Gate `resume_identity` composes one pair per class **from the gate
modules' own job constructors** (stand-in entry-state paths where a real one would be read from a
record: the identity is over the path) and requires the digests to differ — or, for the shared jobs, to
agree. At `8d5099a1`, 13 pairs:

| class | must | identity fields that differ | |
|---|---|---|---|
| G5 switch_by_switch second composition | differ | `override_env` | holds |
| G7 smoke evaluation vs the gates' entry reference | differ | `arm`, `run_kind` | holds |
| G4 two doctored entries | differ | `entry_state` | holds |
| G4 doctored entry vs the undoctored baseline | differ | `entry_state` | holds |
| G4 baseline vs G6 warm of the same arm from the same snapshot (**shared**) | agree | — | holds |
| G1 before vs after capture (same identity; explicit directories must differ) | agree | — | holds |
| GR's B3 seed 0 vs G5's B3 seed 0 | differ | `delta`, `reproduction_overrides`, `audit_position`, `audit_position_caller` | holds |
| GR composition tooth vs GR's planned B3 | differ | `override_env` | holds |
| G8 the two rulers | differ | `predicate_mode` | holds |
| G8 frozen trial run vs G6 pairing run of the same arm and seed | differ | `override_env` (the observer variable) | holds |
| G2 prime off vs prime on | differ | `override_env` | holds |
| written_file_gap's BR vs G9's BR | differ | `audit_position`, `audit_position_caller` | holds |
| entry reference: `gates.entry_reference_jobs` vs GR's prerequisite vs G8's reference (**shared**) | agree | — | holds |

G7's forced-unconverged optimisation vs G4's optimisation (`force_maxcal`, `run_kind`) is composed
too and appears when the two gates' arms coincide on the fewest-variables configuration; at this
campaign they do not (G7's `BR` vs G4's `B3`), so the row is absent by construction rather than
padded.

**G1 is the exception, by layout.** Its two captures are one identity at two commits — the pool's one
directory per identity would put the second on top of the first — so they keep
`runs/gates/switch_neutrality/{before,after}/…` (explicit `outdir`, declared through `runs_under`) and
the before capture is never re-made (amendment 13 rule (ii)). Its exclusion table gains three
**conditional** entries (compared wherever both sides carry the field, excluded where one lacks it):
`job_identity`, `job_digest` — absent on a capture made before A72, and, where both sides carry them,
required equal because the two captures are the same job — and `pending_switches_allowed`, present
until the child stops writing it. Nothing shares with G1's runs anyway: the audit position and the
caller are in the identity.

## 5. The teeth

Registry 29 → 30 gates, 148 → 152 teeth (`--gates` at `77d3c2fd` and `8d5099a1`, §8).

| gate | tooth | what it does | status |
|---|---|---|---|
| `resume_identity` (new) | a matching digest with a different stamped delta | `campaign_delta` doubled in a record whose `job_digest` equals the job's | tripped: "the child stamped campaign_delta=0.2 and the job's delta is 0.1" |
| | a record with no digest | `job_identity` and `job_digest` removed from a complete record | tripped: "carries no job_identity (made before the field existed)" |
| | a digest that does not re-derive from the stamped identity | `job_identity.node_census` flipped, `job_digest` kept | tripped |
| | an unclassified job field | `delta` dropped from `JOB_IDENTITY_FIELDS` | tripped: `TypeError` naming `['delta']` |
| | a by-design pair made to collide | G5's second composition with its `override_env` cleared | tripped: both digests `eeaf038f1ffa3574`, `holds=False` |
| `run_path` | an allowance naming a switch the tree does implement | retired with the allowance (B4) | −1 |
| `run_path` | a run asking for a switch the tree does not implement | kept: the refusal stays, on the doctored registry | tripped |
| `run_kind_separation` | `--resume` does not cross run kinds | rewritten: a record forged as `campaign` with a consistent identity and digest, offered to a `smoke` job; the **only** field that can refuse it is the kind | tripped: "campaign_run_kind is 'campaign', the job's run_kind is 'smoke'" |
| G7 `record_completeness` | a stale run is re-made without `--resume` | unchanged in meaning; asks the pool for a `fresh` run, since this process made the job minutes before | not pressed here (G7 makes runs); A73 |

The self-check (`--selfcheck`) PASS 7/7 at `8d5099a1`, 42 teeth tripped (43 at the base: the
allowance tooth).

## 6. The one press, with denominators, and the resume proof

All at the worktree's root, tree clean, nothing else running (amendment 13 rules (v)/(vi)). Wall
clocks are context.

| # | command | commit | PROCESS runs | outcome |
|---|---|---|---|---|
| 1 | `--gate entry_and_warm` | `cacf3f78` | **19** (3 references + 11 pairing + 5 warm; the population line says "8 entry pair(s) at seed 1; 5 warm run(s); 16 evaluations" — 8 pairs over 11 pairing runs, 3 of them anchors) | PASS 6 717/0; 19 records at `cacf3f78` under `runs/gates/_runs/`, each with `job_identity` and `job_digest`, `completeness.complete` true; entry states rendered relative (`gates/_runs/A_A0_…/y_exit.json`); 75 s |
| 2 | `--gate entry_and_warm --resume` | `cacf3f78` | **19 — re-made, not kept** | the proof **failed**. `--jobs entry_and_warm` said why, per job: "the child stamped audit_position='after_single_evaluation' and the job's audit_position is 'entry_to_write_output_files'". The identity carried `Job.audit_position`'s phase-B default; the pool passes no position to an evaluation and the child stamps its own. 38 s (numba warm) |
| — | fix `1114773d`: `records.effective_audit_position`, rendered in `Job.identity`; the 19 directories at the superseded digests deleted (`rm -rf runs/gates/_runs`, an untracked artifact of a superseded identity rule) | | 0 | `resume_identity` PASS, `run_path --resume` PASS, import walk 57/0 before pressing again |
| 3 | `--gate entry_and_warm` | `1114773d` | **19** | PASS; 19 records at `1114773d` |
| 4 | `--jobs entry_and_warm`, then `--gate entry_and_warm --resume` | `1114773d` | **0** (19 "resumed (complete record of this job kept)", 0 `rc=` lines) | "19 distinct job(s); --resume would keep 19" before; PASS, "runs read: 19 record(s) — 19 at 1114773d [resumed]"; 0.4 s |
| 5 | `--gate entry_and_warm --resume` | `8d5099a1` (final) | **0** (19 resumed) | PASS; the verdict notes the records are at `1114773d`, "which is what --resume asks for" |

**Total PROCESS runs this task: 57**, against the ≈ 19 the brief allowed — 38 of them the cost of
finding and fixing the phase-A defect at the first resume, which the `--jobs` listing would have
caught before press 2 had it been run first. Recorded as a lesson in §10.

**G5 (`switch_composition`) does not share a job with G6**, by name: its six jobs are phase B
(`B/B3/<config>/seed000/unperturbed/gate`, plain and `overridden`), G6's nineteen are phase A;
`--jobs switch_composition` at `1114773d` says "6 distinct job(s); --resume would keep 0", and
`--jobs all` lists G5's plain B3 as shared with `audit_restriction` only. Pressing it under
`--resume` would have made 6 PROCESS runs, so it was not pressed. What G6's 19 records **do** serve
without a run (§7): the three references to G2, G3, G4, GR and G8; the six pairing records of `A0`
and `A1` at seed 1 to GR (its phase-A runs are the same jobs); the two `A0p` seed-0 warm records to
GR's §7.5 substitute; the three `A1` seed-0 warm records to G4 as its baselines; the eleven records
GR shares to the tally's `reference_runs` source.

**Zero-run gates pressed with `--resume` at or after `78c76654`** (rule (xiii), for the gates whose
code changed and make no run): `resume_identity` PASS 35/0; `run_path` PASS 12 teeth;
`recomputation` PASS **1 087/0** over 11 records under 2 declared sources — the tally's and the
analysis's independent job-set declarations resolve to the same 11 records; `run_kind_separation`
PASS 220/0 (203 records under `runs/`, 17 source memberships); `tally_contracts` **FAIL** 81/0 with
60/256 published cells reproduced over 20 reference runs, 6 reproduced whole: the six evaluations GR
shares with G6 exist and reproduce, the fourteen optimisations read `no_record` because GR's runs are
not made — a result, and the right one; 9/10 teeth, *a reference cell moved by one* not tripping
because the cell it moves belongs to a run with no record (196 differing before and after). Gates
whose code changed and **make runs** — G2, G3, G4, G5, G7, G8, G9, `written_file_gap`, GR, G1 — were
not pressed: their old-layout records cannot resume and a press is PROCESS runs; A73's press is
theirs (D27).

`--plan-tables check` at `8d5099a1` **refuses to render**: the `gate_table` stage record predates the
verdicts re-made here (`entry_and_warm`, `resume_identity`, `run_path`, `tally_contracts`,
`recomputation`, `run_kind_separation`), each named with both commits. §4 was not re-rendered: the
population is partial (19 of the pool's jobs made) and a §4 over it would publish the older table or a
smaller one without saying so (trap T14).

## 7. The sharing table, and what A73 should expect

`--jobs all` at `78c76654` (after press 3; G4's doctored jobs composable because its baselines are
G6's warm `A1` records):

```
126 distinct job(s) over 30 gate(s); 242 gate-job declarations;
42 job(s) read by more than one gate; --resume would keep 19
```

Per gate (distinct jobs in its declared set, references included): G7 2 · G2 15 · G3 19 · G4 21 ·
G6 19 · G5 6 · G9 17 (11 own + GR's 6) · `written_file_gap` 12 (6 own + G9's 6) · G8 27 · GR 29
(3 + 20 + 2 + 3 + 1); the three 0-run readers `tally_contracts`, `recomputation`,
`run_kind_separation` 25 each (the two sources).

**Projected runs per full press.** Made by the pool: the 126 distinct jobs; outside it: G1's six
after-capture runs (the before capture kept). **132**, against **152** if every gate made its own as
before (2 + 3 + 12 + 16 + 18 + 16 + 6 + 11 + 6 + 27 + 29 + 6, the per-gate counts at A71's tip
without the twelve G4 re-makes B2 removed and the six contrast runs B5 removed). A saving of about
**20 of 152**, not the survey's 44 of 170, and the difference is the identity being stricter than
"bit-identical `metrics.json`":

- G8's trial runs carry the observer variable in `override_env`; a G6 pairing record has no
  observation file, so they are two jobs (6 runs the survey counted as shared);
- G2's `prime_on` sets the prime switch by `override_env` where G6's warm `A1` composes it from the
  arm — the same environment by two routes, and the identity is over what the pool was handed (3);
- G9, GR, G1 and `written_file_gap` pass `delta=campaign.delta` at seed 0 where G4 and G5 pass
  `None`; the child stamps `campaign_delta` 0.1 against null, so G9's `B3` seed 0 and G4/G5's are
  two jobs (3) — a convention divergence, proposed for the queue in §10, not normalised here because
  `campaign_delta` reaches G1's straddle over the kept before capture;
- GR's fourteen optimisations audit `after_run` under its overrides and were never among the 44.

What **is** shared: the three references (six gates), GR's eight phase-A runs with G6's pairing, G4's
three baselines with G6's warm `A1`, GR's two `A0p` substitutes with G6's warm `A0p`, G9's eleven with
`written_file_gap`'s beside column and GR's reference arms, G5's three plain `B3` with G4's
optimisations. **The exact figure is A73's** (the brief), from the stamp survey over the from-scratch
population.

## 8. Verification

| check | at `77d3c2fd` | at `8d5099a1` |
|---|---|---|
| `--selfcheck` | PASS 7/7, 43 teeth | PASS 7/7, **42** teeth |
| import walk (`harness_survey.py --import-walk`, added here) | — | **57 modules, 0 failures** |
| `--gates` | 29 gates, 5 stages, 148 teeth | **30 gates**, 5 stages, **152 teeth**; diff: `run_path` 13 → 12 teeth, `resume_identity` [harness] 5 teeth "no PROCESS run" inserted after `run_path` |
| `--gate resume_identity` | — | PASS 35/0, 5/5 teeth |
| `--plan-tables check` | — | refuses (stale `gate_table`; §6) — §4 not re-rendered |
| stamp survey (`run_stamp_survey.py`) | 184 records under `runs/` at 8 commits (127 at `f8bce151`) | **203**: the 184 unchanged and untouched (old layout), **19 new at `1114773d`** under `gates/_runs/`, 0 disappeared; the 19 orphans of press 1 (at `cacf3f78`, superseded digests) were deleted before press 3 |
| lines (`harness_survey.py` §1) | 46 318 | 47 783 |

The main checkout was read (`--gates`, `harness_survey.py` at `77d3c2fd`, both write nothing) and
not written; `git status` there is clean.

## 9. Hand-over to A73, by name

1. **B4's child-side remainder** (run-path edits): `child/evaluate.py:133` and
   `child/optimise.py:100` parse `--pending-allowed`; `child/child.py::record_base` takes
   `pending_switches_allowed` and writes the field; `stamp_capabilities_absent`'s docstring keeps the
   nulls-for-unsupplied prose. The pool no longer passes the option. When the child stops writing the
   field, G1's conditional exclusion (§4) makes the straddle read it as one-sided rather than as a
   difference.
2. **Delete the pre-B1 run directories** under `runs/gates/<gate>/` (the 184 old-layout records:
   `reproduction/runs`, `entry_and_warm/*`, `entry_references`, `predicate_mode/*`, `output_path/runs`,
   `prime_map`, `cold_chain`, `audit_restriction/*` bar `_entries`, `switch_composition`,
   `record_completeness`, `written_file_gap/runs`, `exit_audit_diagnosis`) before the from-scratch
   press. No declaration reads them, they cannot resume, and `run_kind_separation`,
   `records_outside_every_source` and the stamp survey count them. G1's `switch_neutrality/before`
   stays.
3. **G1's straddle**: the kept before capture has no `job_identity`; confirm `exclusion_review` lists
   the three new names as conditionally excluded with their leaf counts, and that `pending_switches_allowed`
   moves from compared to excluded when item 1 lands.
4. **Rule (xiii) debt**: G2, G3, G4, G5, G7, G8, G9, `written_file_gap`, GR and G1 had code changed
   here and were not pressed (§6); the D27 press is the press. `--jobs <gate>` before each shows the
   resume decision it will take.
5. **The saving**: `--jobs all` after `--gate all` gives the sharing table; the stamp survey gives the
   run count; §7's 132 is the projection to check.
6. **`exit_audit_diagnosis`** (B3, A73's): untouched — explicit directories, its `Job(...)` calls
   compile against the new dataclass (`outdir` is still accepted).
7. **A7's remainder** `predicate.provenance_of` (from A71) is unchanged.
8. **`tally_contracts`'s tooth** *a reference cell moved by one* trips only over a population in
   which the optimisation runs exist (§6).

## 10. Limits, and what the documents should gain

**Limits.** The saving is projected, not measured (§7). The identity is over the *job* — what the
pool hands the child — so two jobs that compose the same environment by different routes are two
records; the survey's "bit-identical re-makes" was over `metrics.json`, and the two counts will not
agree. G4's doctored jobs and G6's dependents are composable only once a reference record exists, so
`--jobs` before a first press lists prerequisites only and says so. The `_runs/` directory accumulates
orphans when the identity rule changes (press 1's 19 were deleted by hand here); nothing garbage-collects
them, and the stamp survey is what shows them. `Gate.runs_under` survives for G1 alone.

**The queue.** I-23 → close at A73's press with the from-scratch population's `job_digest` on every
record. A new item: **δ at seed 0 is composed two ways** — G9, GR, G1 and `written_file_gap` pass
`campaign.delta`, G4 and G5 pass `None`; the child stamps `campaign_delta` accordingly; under the
identity they are two jobs for one run (3 runs per press). Normalising (`delta=None` whenever the
regime is unperturbed, in `Job.__post_init__`) changes `campaign_delta` on G9/GR/G1's records, which
G1 compares across the kept before capture — so it belongs to a press that re-takes the before
capture, not A73.

**The harness plan.** A new amendment for the identity rule: *(xiv)* **the job identity is the whole
of "the same job"** — every field the pool composes into a run is in `pool.JOB_IDENTITY_FIELDS`, the
record stamps it and its digest, `--resume` compares them and nothing else, and a change to the list
re-makes every record (amendment 17 (a) by construction); a gate's runs are jobs in one pool, a gate
declares the jobs it reads, and a gate that makes the same arm a second way on purpose differs in an
identity field — checked by gate `resume_identity`, one pair per class. Rule (xi)'s `tally.SOURCES`
names job sets. Rule (ii) stands for G1's before capture, now as the pool's one layout exception.

**The improvement list.** `--jobs <gate>` before a `--resume` press: the listing prints the resume
decision per job from the record alone (rule (vii)) and would have saved 38 runs here. Proposed as a
step of the press protocol: *dry-run the resume before pressing it*.

## 11. Autonomous decisions, each with its reversal

1. **Identity over the raw `Job` fields, not the composed environment.** G5's second run composes the
   same environment by hand and *must* be a different job; G8's observer and G2's prime override are
   real inputs to the child. Reversal: render `architecture_environment` instead of `override_env` —
   which collides G5's pair and is therefore not a reversal without redesigning G5.
2. **`entry_state` as a `runs/`-relative path, not the file's digest.** A digest would need the file
   at composition time and would orphan every dependent record whenever a reference is re-made at a
   new commit. Reversal: hash the bytes in `Job.identity` (one branch).
3. **The digest stamped by the pool after the child returns**, with the child's `completeness` block
   re-evaluated. No run-path edit. Reversal: pass `--job-digest` to the child and stamp it there (a
   child edit, A73's territory).
4. **One run per job per invocation** (`_MADE_THIS_INVOCATION`, record-checked), `fresh=True` for the
   one caller that wants otherwise. Reversal: drop the ledger and thread `resume=True` to every gate
   after the first in `--gate all` — which is what T13 warned against.
5. **G1's captures stay in explicit directories** (§4). Reversal: put the commit into G1's identity —
   then every gate's identity would carry it and `--resume` could never cross a commit.
6. **G7's smoke runs go into the pool** (the kind is in the identity; the stale tooth uses `fresh`).
7. **The audit position rendered per phase** (`effective_audit_position`), found by the failed resume.
   Reversal: give `Job` a phase-aware default instead — the same fact in a different place.
8. **`FORMAT` not bumped** — A53's rename and A62's four fields did not bump it either; the digest
   requirement is what re-makes every record. Reversal: `run-record-2`, a child-visible constant.
9. **`tally_contracts` declares the two sources' jobs**, not `("reproduction", "predicate_mode", "output_path")`:
   it reads G8's *verdict*, not its runs, and nothing of G9's.
10. **A new gate `resume_identity`** rather than teeth inside `run_path`: a registry row a reader can
    press alone; 30 gates.
11. **`analysis.SOURCES` resolves through the gate modules' job constructors** — the gate owns its
    population (rule (xi)); the independence kept is *which* gates' job sets are sources and what each
    one is, declared twice; `analysis.read_records` (unused after) removed.
12. **The 19 orphan directories of press 1 deleted** (untracked, at a superseded identity rule).
13. **`harness_survey.py --import-walk`** so that "57 modules, 0 failures" comes from a committed
    script (protocol §15); A71's walk was ad hoc.
14. **`--jobs <gate|all>`** on the button.
15. **`arms.env_for(pending_ok=…)` kept** — the composition self-check's inspection mode, not the
    allowance; the pool's use of it is gone.

## 12. Commits

`5555d674` core (pool, records, framework) · `b3144430` the gates · `f722fc02` the sources, tally
gate, chain · `cacf3f78` gate `resume_identity`, `--jobs`, `--allow-pending` retired, import walk ·
`1114773d` the phase-A audit position (the defect of §6) · `78c76654` README, `Job.key` · `b42c003e`
the evaluation tally's printer · `8d5099a1` `Gate.run` records an uncomposable job set. Base
`77d3c2fd`.
