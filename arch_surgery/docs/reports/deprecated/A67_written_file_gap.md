# A67 (written-file-gap) — the one-call output path writes the same gap

> **Document status** — **ARCHIVED at merge, 2026-09-14.** Task **A67 (written-file-gap)** merged into
> `architecture_surgery` at `f8d67eb4` (branch tip `ec6e5d62`, base `e159d9b6`). Records relocated to
> `arch_surgery/idf_probe/runs/A67_runs/`. The orchestrator's critical assessment is §13. Folder position
> records lifecycle, not validity (trap T3).

---

## 0. The words, spelled out once

*Caption: one row per term this report uses in a particular way. Where the project's vocabulary
already fixes a word, this is that definition and not a new one.*

| term | means |
|---|---|
| **exit audit** | one further full sweep of the whole model set, past termination, on the identical instrument in every arm, charged to no arm; its residual is the largest scaled movement of the coupling state under that sweep, `max_i |Δy_i| / s_i`, with τ = 1e-6 |
| **declared position** | the entry to `write_output_files` — the state the solve handed over, before any output-time work. Every campaign record audits here. Since ruling D25 the audit puts the whole solve-phase data structure back before its sweep and reads 0 components above τ in every arm |
| **`after_run`** | the same instrument taken after the whole run, which is after the output files are written: the solve-phase settings put back for every field outside the coupling state, the coupling state left **as PROCESS wrote it out**. Its residual is the distance between the written file and a fixed point of the solve's own map — a property of PROCESS's output pass, not a convergence statement about any arm |
| **the loop path** (`mda_output`) | upstream's output-time idempotence loop: up to ten flat sweeps before the files are written; the reference arm `BR` (and `B0`) keep it |
| **the one-call path** (`finalise_once`) | the driver change of A57: `finalise` called once on the accepted state, no output-time sweep; arms `B1` and `B3` take it *as the campaign composes them* |
| **campaign-composed** | the arm's environment composed from the switch matrix and nothing else. Gate GR runs `B1`/`B3` with the loop switched back on (a recorded *reproduction override*), so its records say nothing about the one-call path |
| **restricted / whole-state** | the residual over the components not written by the nodes an arm defers to once per run / over every tested component. Both are published, on both rulers (`frozen`, `mixed`), on every run |
| **declared caller** | a stage named in `records.AUDIT_POSITION_AFTER_RUN_CALLERS`, the only stages the run pool lets ask for `after_run` |
| **I-21** | the queue's open issue: what else PROCESS's output pass leaves inconsistent in the written file, and whether the one-call path writes the same ~7e-3 `tfcoil.insstrain` gap as PROCESS as shipped |

---

## 1. Verdict

**Yes: the one-call output path writes the same gap, and nothing else moves.** On both pulsed
configurations, `B1` and `B3` composed exactly as the campaign composes them — `finalise` once,
0 output-time sweeps — show an `after_run` residual with exactly **one** component above τ,
`tfcoil.insstrain`, at 7.119e-03 (`large_tokamak_nof`) and 7.021e-03 (`low_aspect_ratio_DEMO`)
scaled, beside the reference arm's 6.991e-03 and 7.021e-03 on the loop path. Every other tested
component — 817 of 818 on `large_tokamak_nof`, 823 of 824 on `low_aspect_ratio_DEMO` — moves by
exactly `0x0.0p+0` on all six runs. No further component appears by name.

Gate `written_file_gap` **PASS**: 6 of 6 runs finished as the arm the matrix describes, on the
output path its cell names, audited at `after_run` as this gate's declared override; 42 of 42
composition-and-position checks; 4 of 4 teeth tripped. The gate does not pass or fail on the size
of the gap (§3).

*Caption: what the brief asked to be shown, the measurement that settles it, and the section.
Every number is a count or a bit comparison; no conclusion rests on a timing.*

| what had to hold | result | where |
|---|---|---|
| six campaign-composed runs, `after_run` audit, `output_path` per the matrix cell | 6/6 finished; `BR` → `mda_output` (2 sweeps), `B1`/`B3` → `finalise_once` (0 sweeps); no switch override on any run | §4, §6 |
| does the one-call path write the same gap | **yes** — argmax `tfcoil.insstrain` on all six; the written `insstrain` is 0.70–0.72 % from the solved one on every run, both paths | §4, §5 |
| does any further component appear by name | **no** — count above τ is 1 on every run, whole-state and restricted, both rulers; the second-largest component is exactly 0 | §5 |
| `after_run` a position with declared callers, refusal kept and proven | `records.AUDIT_POSITION_AFTER_RUN_CALLERS` (four callers, a reason each); pool refuses any other caller and every campaign run; two `run_path` teeth and one gate tooth | §7 |
| stale "exactly one caller" prose corrected | `records.py` and `optimise.py`; there were three callers, unrefused | §7 |
| the gate in the registry, `ordered_gate_names`, the preflight and `--gate all`; §4.1 row | yes; §4 re-rendered, `--plan-tables check` IDENTICAL | §6, §8 |

---

## 2. How to re-run everything in this report

Every number here is produced by a committed stage of `experiment_runner.py`, run from the
experiment directory under the project interpreter; nothing was computed on a command line.

```bash
PY=/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python
cd arch_surgery/MDA_partitioning_experiment_v4
$PY experiment_runner.py --gate written_file_gap             # the 6 runs and the verdict (§4–§6)
$PY experiment_runner.py --gate run_path --resume            # the two new refusal teeth (§7)
$PY experiment_runner.py --gate switch_neutrality --resume   # G1 over the moved exclusion, 0 runs (§10, decision 3)
$PY experiment_runner.py --gate run_kind_separation --resume
$PY experiment_runner.py --measure gate_table --resume
$PY experiment_runner.py --plan-tables write && $PY experiment_runner.py --plan-tables check
$PY experiment_runner.py --selfcheck
$PY run_stamp_survey.py --json stamps.json                   # §8
```

*Caption: one row per figure in this report and the stage that produced it.*

| figure | stage | record |
|---|---|---|
| the six residuals, argmax, counts, output path, sweeps, instrument (§4) | `--gate written_file_gap` | `runs/gates/written_file_gap/gate.json`, `runs/…/seed000/metrics.json` |
| the written vs solved `insstrain` per run (§5) | `--gate written_file_gap`, block `argmax_written_against_solved` per run: the argmax component read from the run's own snapshot at the declared position (`y_entry_to_write_output_files.json`, hex) against the `(insstrain)` line of its MFILE | `runs/gates/written_file_gap/gate.json` |
| the declared-position column (§4) | gate G9's records, read by the gate and named in its verdict | `runs/gates/output_path/runs/…/metrics.json` |
| teeth (§6, §7) | `--gate written_file_gap`, `--gate run_path` | the two `gate.json` |
| §4.1 of the plan | `--measure gate_table`, `--plan-tables write` | `runs/gates/gate_table/measurements.json`, `EXPERIMENT_PLAN.md` |
| the stamp survey (§8) | `run_stamp_survey.py` | printed histogram and per-record list |

Commits: `09cc9f3e` (the harness change, before any run), `2a91602f` (§4 re-render), `d44ac1e8`
(README), `f1c29f26` and `1adeed66` (the gate's written-against-solved block, added so that §5's
table is a stage's output and not a command line's; the gate re-pressed with `--resume`, 0 runs
re-made, verdict PASS at `1adeed66` reading 6 records at `09cc9f3e`). Every run is at `09cc9f3e`.

---

## 3. What the gate measures, and what it does not accept on

**Measures.** Per run, at `after_run`: the residual's maximum (decimal and hex), argmax and count
above τ, on the restricted and the whole-state statistic and on both rulers; `output_path` and
`output_loop_sweeps` exactly as the driver stamped them; the instrument stamp
(`exit_audit.instrument.restores`, the snapshot position, how many fields were put back, how many
could not be, what the `numerics` rule held back); and, beside it, the declared-position residual
of the same arm, configuration and seed **from gate G9's record** — a run record carries one
audit at one position, so this gate's own records do not carry the declared-position number, and
the verdict says so per run rather than leaving a blank.

**Accepts on.** Four things, none of them the residual's size: **(1)** every run finished and its
`output_path` is the arm's matrix cell (`upstream → mda_output`, `none → finalise_once`), with
`output_loop_sweeps` 0 on the one-call arms and ≥ 1 on the loop arm, and no switch override rode
into the run (`reproduction_overrides` null, `override_env` empty); **(2)** the audit was taken at
`after_run` — the record, the audit block and the declared position agree that it was moved — and
the run's `command.json` stamps the position and this gate as its caller; **(3)** the residual is
*reported*: both rulers, both statistics, each with a hex maximum, a named argmax and an integer
count above τ.

**Does not accept on.** The gap. It is a property of PROCESS's write pass — the TF-coil models
raise the stress mesh 100 → 500 layers when `output=True` and the written `insstrain` is sampled
on that grid (A61) — and the user confirmed on 2026-09-14 (D25, words in the row) that the
experiment measures before the output pass and does not rewrite PROCESS to close it. A gate whose
verdict turned on that number would be a gate on something the experiment has decided not to
change.

**Excluded, with the reason in the verdict.** `st_regression`: GR's `after_run` audit on the loop
path already reads exactly `0x0.0p+0` there (A62 §5.3); `tfcoil.insstrain` is `None` on that
configuration from the first sweep and is tested by exact equality (A61 §3), so there is no gap to
measure on either path; and `B1` composes to `B0` there and is skipped by the configuration's own
recorded reason. The two pulsed configurations are selected by their `pulsed` flag, never named.

---

## 4. The six runs

*Caption: one row per run, seed 0, unperturbed, at `09cc9f3e`, each composed from the matrix with
no override but the audit position. "path" and "sweeps" are `output_path` and `output_loop_sweeps`
as the driver stamped them. The `after_run` columns are the exit-audit residual on the **frozen**
ruler; the `mixed` ruler reads bit-identically on every row (six of six, both statistics), so it is
not repeated. "max" is the largest scaled movement, `|Δy| / s` with `s` the committed frozen scale,
in hex beneath; "above τ" is the count of continuous components at or above 1e-6 out of the
population in parentheses — restricted statistic first (696 kept of 818 on `large_tokamak_nof`,
701 of 824 on `low_aspect_ratio_DEMO`; the per-run deferred nodes' 122 / 123 components excluded),
whole-state second. The declared-position column is gate G9's record of the same cell at
`f8bce151`, restricted statistic; on all six the two records agree on `exact.norm_objf`,
`node_calls_solve_phase` and `n_solver_iterations`, so they are of the same solve. "instrument" is
`exit_audit.instrument.restores`; every row also reads snapshot position
`entry_to_write_output_files`, 85 fields restored, 0 not restorable, `tfcoil.n_rad_per_layer`
among the 85.*

| arm | configuration | path | sweeps | `after_run` max (restricted = whole) | argmax | above τ: restricted / whole | declared-position residual (G9) | instrument |
|---|---|---|---:|---|---|---|---|---|
| `BR` | `large_tokamak_nof` | `mda_output` | 2 | 6.990979e-03 `0x1.ca292b56b673fp-8` | `tfcoil.insstrain` | 1 (696) / 1 (818) | 1.15e-11, `heat_transport.tlvpmw`, 0 above τ | `whole_data_structure_derived_set` |
| `B1` | `large_tokamak_nof` | `finalise_once` | 0 | 7.118926e-03 `0x1.d28bc4431f7fep-8` | `tfcoil.insstrain` | 1 (696) / 1 (818) | `0x0.0p+0`, 0 above τ | same |
| `B3` | `large_tokamak_nof` | `finalise_once` | 0 | 7.118926e-03 `0x1.d28bc4431f7fep-8` | `tfcoil.insstrain` | 1 (696) / 1 (818) | `0x0.0p+0` restricted, 0 above τ (whole: 1.06, `costs.c2244`, 112 — the per-run nodes' own writes, by design) | same |
| `BR` | `low_aspect_ratio_DEMO` | `mda_output` | 2 | 7.021185e-03 `0x1.cc23ee7f371aep-8` | `tfcoil.insstrain` | 1 (701) / 1 (824) | `0x0.0p+0`, 0 above τ | same |
| `B1` | `low_aspect_ratio_DEMO` | `finalise_once` | 0 | 7.021179e-03 `0x1.cc23d7ea8f685p-8` | `tfcoil.insstrain` | 1 (701) / 1 (824) | `0x0.0p+0`, 0 above τ | same |
| `B3` | `low_aspect_ratio_DEMO` | `finalise_once` | 0 | 7.021179e-03 `0x1.cc23d7ea8f685p-8` | `tfcoil.insstrain` | 1 (701) / 1 (824) | `0x0.0p+0` restricted, 0 above τ (whole: 1.00, `costs.cdrlife_cal`, 112 — as above) | same |

Three things in the table worth reading off.

- **The reference rows reproduce A62 §5.3 to the bit** (`0x1.ca292b56b673fp-8`,
  `0x1.cc23ee7f371aep-8`): the same instrument on the same solve gives the same number, one commit
  later and in another worktree.
- **`B1` and `B3` are bit-identical to each other** on each configuration — the lifted problem's
  optimum, written once. They differ from `BR` because they solve a different problem (the burn
  time owned by the optimiser), not because of the output path: the *relative* gap is the same
  0.70–0.72 % on every row (§5).
- **On `B3` the whole-state count at `after_run` is 1, where at the declared position it is 112.**
  At the declared position the per-run deferred nodes have not yet run, so their components move
  in the audit's sweep by design (the restriction exists for exactly this). At `after_run` they
  have run, their outputs are in the state PROCESS wrote, and the sweep moves none of them. That is
  the expected behaviour of the position and is not part of the gap.

---

## 5. The answer to I-21

The one-call output path writes the same gap as PROCESS as shipped, and it is the whole of what
the output pass leaves inconsistent in the written file on these two configurations at seed 0.
`finalise` once — no output-time loop, 0 sweeps stamped — leaves `tfcoil.insstrain` in the MFILE
0.718 % (`large_tokamak_nof`) and 0.702 % (`low_aspect_ratio_DEMO`) from the value the solve
accepted, against 0.720 % and 0.702 % on the loop path; expressed on the frozen scale that is the
7.12e-03 / 7.02e-03 in §4 beside `BR`'s 6.99e-03 / 7.02e-03. The mechanism is the one A61 named:
the TF-coil node's `run(output=True)` sets the stress mesh to 500 layers, which the one-call path
reaches exactly as the loop path does, through `finalise → models.write → *.output()`, and which
`tfcoil.n_rad_per_layer` in the instrument's derived set confirms on every row (85 restored, that
field among them). **No further component appears by name**: on all six runs exactly one component
sits above τ on both statistics and both rulers, and the second-largest scaled movement is
`0x0.0p+0` — so the models that re-enter their own `run()` from `output()` (trap T7) recompute on
the finer mesh nothing else that the coupling state carries, on either path.

*Caption: `tfcoil.insstrain` as the solve accepted it (read from the run's own snapshot at the
declared position, `y_entry_to_write_output_files.json`, exact hex) against the value the same run
wrote to its MFILE (`(insstrain)` line), per run, from the gate's `argmax_written_against_solved`
block; the relative difference is `(written − solved) / |solved|`; "identical" is hex equality and
reads false on all six. It is the same difference §4 reports on the frozen scale, and it is the
table A61 §8 gave for the previous instrument's runs, reproduced here on campaign-composed
`B1`/`B3`. Information beside the residual, never a criterion.*

| run | path | solved | written | relative |
|---|---|---|---|---:|
| `large_tokamak_nof/BR` | loop | `-0x1.80b7efa41808cp-8` (−5.8703384458e-03) | `-0x1.837d15b44626dp-8` (−5.9126070012e-03) | −0.7200 % |
| `large_tokamak_nof/B1` | one call | `-0x1.890cf3480a27bp-8` (−5.9974760007e-03) | `-0x1.8bdf13e1edb32p-8` (−6.0405181447e-03) | −0.7177 % |
| `large_tokamak_nof/B3` | one call | `-0x1.890cf3480a27bp-8` | `-0x1.8bdf13e1edb32p-8` | −0.7177 % |
| `low_aspect_ratio_DEMO/BR` | loop | `-0x1.3c787340bcaf9p-8` (−4.8289567355e-03) | `-0x1.3eb14846f40d4p-8` (−4.8628617723e-03) | −0.7021 % |
| `low_aspect_ratio_DEMO/B1` | one call | `-0x1.3c785efd78f40p-8` (−4.8289520177e-03) | `-0x1.3eb133e7c630bp-8` (−4.8628570292e-03) | −0.7021 % |
| `low_aspect_ratio_DEMO/B3` | one call | `-0x1.3c785efd78f40p-8` | `-0x1.3eb133e7c630bp-8` | −0.7021 % |

What this does for gate G9's claim: G9 says the state the one-call path *hands to* `finalise` is
the accepted state, bit for bit outside the per-run nodes' writes — and it is (its records, read
here, show 0 differing). What this gate adds is that `finalise` then writes one component of that
state on a different mesh, on the one-call path as on the loop path. The two claims are about two
different points in the output path and both hold.

---

## 6. Checks and teeth

*Caption: the gate's per-run checks (seven per run, 42 over six runs, 0 failed) and its four teeth,
each tripped. A tooth doctors a throwaway copy of a real record and hands it to the same
`evaluate_run` function that judged the run, so the tooth is judged by the gate's own code, not by
a restatement of it.*

| check | what it reads | result |
|---|---|---|
| (1a) the run finished | `status`, `failure_class` | 6/6 `ok` |
| (1b) output path = matrix cell | `output_path` vs `arms.matrix_cell(arm, "output-time loop (MDA_Output)")` | 6/6 |
| (1c) sweeps 0 on one-call arms, ≥ 1 on the loop arm | `output_loop_sweeps` | 0, 0, 0, 0 / 2, 2 |
| (1d) no switch override rode in | `reproduction_overrides`, `command.json.override_env` | null / `{}` on 6/6 |
| (2a) audited at `after_run`, moved from the declared position | `audit_position`, `exit_audit.audit_position`, `audit_position_declared` | 6/6 |
| (2b) asked for by this gate | `command.json.audit_position`, `.audit_position_caller` | `after_run`, `written_file_gap` on 6/6 |
| (3) residual reported, argmax named, both rulers, both statistics | `exit_audit.{frozen,mixed}.{brief,restricted}` | 6/6 |

| tooth | doctoring | must | result |
|---|---|---|---|
| `the_declared_position_where_after_run_was_asked` | a copy of `BR/large_tokamak_nof`'s record with `audit_position` set to the declared position | fail (2a) | TRIPPED; the undoctored record passes every check |
| `a_one_call_arm_whose_output_path_reads_mda_output` | a copy of `B1/large_tokamak_nof`'s record with `output_path = mda_output`, 2 sweeps | fail (1b) and (1c) | TRIPPED, both |
| `a_residual_whose_argmax_is_not_named` | the same record's frozen restricted `argmax` set to null; the size untouched | fail (3) | TRIPPED |
| `an_undeclared_caller_asking_for_after_run` | a `Job` for `BR` at `after_run` under caller `a_stage_nobody_declared`, handed to `pool.environment_for` | refuse before any run | TRIPPED (`PoolError`, names the declared callers) |

Registry: `written_file_gap` appears in `ordered_gate_names` (26 gates; after `output_path`, which
it declares in `reads_from` because it reads G9's records for the beside-column), in `--gates` and
the preflight's registry listing, and in `--gate all` (not pressed — the brief forbids it). The
`run_path` self-check gained two teeth (§7), now 14 declared and 14 tripped; the registry's
self-check also asserts that every declared caller of `after_run` is a registered stage.

---

## 7. `after_run` is now a position with declared callers

**What was there.** `records.py`'s comment said `after_run` "survives for exactly one caller", the
reproduction gate; the record note quoted into every `after_run` record said the position "is
refused outside that gate". Nothing enforced either sentence: `pool.Job.audit_position` could be set
by anyone, and **three** stages set it — gate GR, gate G1 (both captures, so the whole `exit_audit`
block is compared rather than excluded) and the `attempts` measurement stage's retry-ladder
demonstration runs. The brief named two of these; the third was found by reading `gates.py`.

**What is there now** (`09cc9f3e`).

- `records.AUDIT_POSITION_AFTER_RUN_CALLERS`: a table, registry name → reason, with four rows —
  `reproduction`, `switch_neutrality`, `attempts`, `written_file_gap`. `records.AUDIT_POSITION_DECLARED`
  and `records.AUDIT_POSITION_AFTER_RUN` name the two positions; `optimise.py` and `pool.py` read
  them from there instead of spelling the strings.
- `records.assert_audit_position_allowed(...)`: three refusals — an unknown position; a **campaign**
  run at any position but the declared one, whoever asks; `after_run` asked for by a caller the
  table does not name, or by no caller. Called by `pool.environment_for` on every path a run takes,
  through `pool.Job.audit_position_caller` (new field, default `None`).
- Each declared caller names itself on every job it makes and stamps the override in its own
  record: GR's verdict `reproduction_overrides` block gains `audit_position_caller`, G1's verdict
  and both manifests gain `audit_position_override`, the ladder manifest gains the same block, and
  this gate's verdict and manifest carry it. Per run, the pool writes `audit_position` and
  `audit_position_caller` into `command.json` beside the record.
- The record itself is unchanged: no `SCHEMA` field, no new record leaf. The override is stamped
  on the record exactly as GR's was — `audit_position ≠ audit_position_declared`, and the note —
  and `--resume` re-made nothing (§8).
- Prose: the `records.py` comments and `AUDIT_POSITION_AFTER_RUN_WHY` (the note quoted into every
  `after_run` record), and `optimise.py`'s module comment and `--audit-position` help text, now say
  what the position reads and who may ask for it. The stale sentence is recorded in both places as
  having said "exactly one".
- Teeth: `run_path` gained *a campaign run asking for the after_run audit position* and *an
  undeclared caller asking for the after_run audit position*, both `PoolError` refusals from
  `environment_for`, declared in `gates._selfcheck_gates` and tripped (14/14). This gate's fourth
  tooth is the undeclared-caller refusal again, from the gate's side.

**A consequence, and how it was handled** (autonomous decision 3, §10). `AUDIT_POSITION_AFTER_RUN_WHY`
is quoted into every `after_run` record as `audit_position_note`, and G1 compared that leaf whenever
both captures carried it and their instrument stamps agreed. Correcting the sentence would therefore
have made the next G1 straddle across a driver change fail on three prose leaves. The leaf is moved
to G1's `ALWAYS_EXCLUDED` set with kind *prose quoted from a harness constant*: it names no driver
behaviour, and what it could witness — `audit_position` itself — is compared, with two captures that
disagree on it refused before any value is. Measured on the seeded captures (`fd480aff → 09cc9f3e`,
`--gate switch_neutrality --resume`, **0 runs re-made**): 2 831 values compared, 0 differing, as
before; 1 632 excluded (was 1 626) of which 951 by the instrument change (was 957) — the six note
leaves (one per pair, both phases) moved from the instrument-conditional group to the always
group on a straddle where they were already excluded. G1 PASS, 9/9 teeth.

---

## 8. Stamp survey

`run_stamp_survey.py` over `runs/` after every press: **184 run records** —
6 at `09cc9f3e` (this task's; every one under `gates/written_file_gap/runs/`), 11 at `3d64625c`,
3 at `47be2b0d`, 16 at `61473c1d`, 3 at `7ad8ea04`, 12 at `b784158c`, 127 at `f8bce151`,
6 at `fd480aff`. The 178 records not at `09cc9f3e` are the seeded A65 records, none re-made: the
resumed presses (`run_kind_separation`, `run_path`, `switch_neutrality`, `gate_table`) each state
the commits of the records they read. The six new records, by path:

```
09cc9f3e  gates/written_file_gap/runs/large_tokamak_nof/BR/seed000/metrics.json
09cc9f3e  gates/written_file_gap/runs/large_tokamak_nof/B1/seed000/metrics.json
09cc9f3e  gates/written_file_gap/runs/large_tokamak_nof/B3/seed000/metrics.json
09cc9f3e  gates/written_file_gap/runs/low_aspect_ratio_DEMO/BR/seed000/metrics.json
09cc9f3e  gates/written_file_gap/runs/low_aspect_ratio_DEMO/B1/seed000/metrics.json
09cc9f3e  gates/written_file_gap/runs/low_aspect_ratio_DEMO/B3/seed000/metrics.json
```

The gate's own verdict: `runs_provenance.n_records = 6`, heads `['09cc9f3e']` — not the 0 that
trap T12 warns of. §4 of the plan re-rendered: 26 PASS, 0 FAIL, 153/153 teeth; the population
marker moved 170 → 176 run records (the 6 new ones) and
gained `09cc9f3e`; four §4.1 rows changed (`written_file_gap` added; `run_path` 12 → 14 teeth;
`switch_neutrality`'s straddle text; `run_kind_separation` 178 → 184 records); no table cell of
§4.2–§4.4 changed. `--plan-tables check`: 1 793 lines, IDENTICAL. `--selfcheck`: 7/7 PASS.

One observation, not this task's to fix: G1's `--resume` press rewrote the `after` manifest's
`tree_git_head` to `09cc9f3e` while the six records it kept are at `b784158c`, so the verdict's
straddle line reads `fd480aff -> 09cc9f3e` and its `runs read` line reads `6 at b784158c`. The
record-level line is the honest one (trap T13), and the two lines are side by side in the verdict.

---

## 9. The runs this task made

**Six PROCESS runs**, all `run_kind = gate`, all at `09cc9f3e`, all `ifail = 1`, at three workers.
Wall clock, as context only and never as evidence (each is one run, unrepeated, on a shared
machine): `large_tokamak_nof` BR 61 s, B1 70 s, B3 72 s; `low_aspect_ratio_DEMO` BR 39 s, B1 46 s,
B3 48 s. No campaign or smoke record; `EXECUTION_APPROVED` untouched; `harness/core/config.py`
untouched; nothing under `…_v4/PROCESS/` or the repository-root `process/` changed (`git diff
--stat e159d9b6..d44ac1e8` names only `harness/`, `EXPERIMENT_PLAN.md` §4 and this report). No
run was retried or tuned; no gate failed.

---

## 10. Autonomous decisions, each with the way back

1. **The caller is stamped in `command.json`, not in the record.** The brief preferred reading what
   the record already carries over adding a `SCHEMA` field; the record's own stamp of the override
   is `audit_position ≠ audit_position_declared` plus the note, which is exactly what GR's records
   carry today, and the *caller* is stamped in the pool's per-run `command.json` and in the caller's
   verdict. Any new record leaf — schema or not — would have cost a conditional G1 exclusion
   (`compare_records` treats a leaf present on one side only as a mismatch unless it is declared).
   *Reversal:* a `SCHEMA` field `audit_position_caller` written by the child; expect `--resume` to
   re-make every record (amendment 17 (a)) and add the name to `FIELDS_ADDED_BY_A_DRIVER_CHANGE`.
2. **Four declared callers, not three.** The `attempts` measurement stage's ladder runs audit at
   `after_run` and would have been refused by the new rule; it is declared with its reason rather
   than moved to the declared position (its runs sit beside GR's population, whose position it
   matches). *Reversal:* remove the row and move `ladder_jobs` to the declared position; three
   ladder runs re-made.
3. **`audit_position_note` moved to G1's always-excluded set** (§7, measured there). The
   alternative — leaving a false sentence in every `after_run` record so G1's compared count stays
   at 2 831 on prose — was rejected; a leaf that cannot witness driver behaviour does not belong in
   a gate that binds the driver. *Reversal:* one dict entry back to the two conditional groups; the
   next G1 straddle then fails on three leaves until the before capture is re-made.
4. **The declared-position column is read from gate G9's records**, declared in `reads_from`, and
   is informational: absent records are stated, never failed on. *Reversal:* drop the column and
   the dependency; or make it a refusal, which would make a six-run gate depend on eleven runs.
5. **Run directories carry `seed000`** (D24), like GR's and unlike G9's `runs/<config>/<arm>`.
6. **A README paragraph** (§8 of `harness/README.md`) on the declared callers and the gate — not
   asked for, but the README is where the gates are explained in plain language and a gate that is
   not there is a gate a reader cannot find. *Reversal:* revert `d44ac1e8`.

---

## 11. Limits

- **Seed 0 only, two configurations, one commit.** Six runs. The gap's *size* is one number per
  cell; its *presence* on the one-call path is what the gate answers, and that does not depend on
  the seed (the mechanism is a mesh setting, not a starting point), but no other seed was run.
- **What this says about the campaign's MFILE-derived values, and what it does not.** The
  experiment's acceptance quantities read from the MFILE are `norm_objf`, `sqsumsq`, `ifail` and
  the iteration variables (`itvarNNN` / `xcmNNN`). Read at the copy (`…_v4/PROCESS/process/`,
  read-only): all four are written by `SolverHandler.output()` in
  `process/core/solver/solver_handler.py`, called from `SolverHandler.run()` **immediately after
  the solve** and before `write_output_files` — from the optimiser's own state (`self.solver.objf`,
  `self.solver.x`, `self.solver.conf`, `self.solver.info`), through `ovarre(NOUT, …)`, which mirrors
  every line into the MFILE. **None of the four is written by a model, and none by a model's
  `output()` that re-enters `run()`** (trap T7); the ten T7 models write their own quantities. The
  only other MFILE `norm_objf` writer is `caller.output_evaluation`, reached from `finalise` in
  evaluation mode only, never in an optimisation. So the written-file gap measured here does not
  reach any acceptance quantity; the record's `mfile.norm_objf` is also checked against the
  accepted `exact.norm_objf` to the bit by gate G9 (check iii). What this gate does **not** say is
  what the gap does to the MFILE quantities the *report* might quote for a reader — TF-coil
  stresses and anything downstream of the 500-layer mesh — which are written by `output()` and are
  not acceptance quantities; their list was not derived here.
- **One instrument version.** Every row is `whole_data_structure_derived_set`; a different restore
  rule would give a different number and must change the stamp (D25's rule).
- **The declared-position column is at `f8bce151`**, G9's seeded records; the three
  solve-describing values compared equal on all six rows, but that comparison is information in
  the verdict, not a criterion.
- **The T7 reading above is by reading the copy's source**, not by counting invocations; the
  writers of the four quantities are unambiguous in the code, but the census method TRAPS T1
  recommends was not applied here because nothing on a `run()` path was being classified.

---

## 12. What the queue, the plan and the improvement list should gain

Not edited by this task; proposed for the orchestrator.

- **Queue, I-21's row:** *"Measured 2026-09-14 (A67 (written-file-gap), records at `09cc9f3e`): the
  one-call path writes the same gap — `after_run` residual 7.119e-03 / 7.021e-03 on campaign-composed
  `B1` and `B3` (`finalise_once`, 0 sweeps) against 6.991e-03 / 7.021e-03 on `BR`, argmax
  `tfcoil.insstrain` on all six, exactly one component above τ, every other component `0x0.0p+0`;
  the written `insstrain` is 0.70–0.72 % from the solved one on every row. No further component
  appears by name. None of the acceptance quantities (`norm_objf`, `sqsumsq`, `ifail`, the iteration
  variables) is written by a model's `output()`; all four are written by `SolverHandler.output()`
  before the output path. Gate `written_file_gap` publishes the number per run and gates only on
  composition and position."* Status: measured; the residual is a standing per-run field, the PROCESS
  bug report is the sibling's.
- **Plan, §3.3's `MDA_Output` paragraph**, one sentence after the A62 landing note: *"Measured on the
  one-call path 2026-09-14 (A67 (written-file-gap), gate `written_file_gap`): `B1` and `B3` as the
  campaign composes them write the same one-component gap — `tfcoil.insstrain`, 7.12e-03 /
  7.02e-03 scaled at `after_run`, every other component exactly 0 — so the gap is a property of
  `finalise`'s `output()` calls and not of the loop; it reaches no acceptance quantity."*
- **Harness plan, Appendix A, amendment 23:** `after_run` is a position with declared callers
  (`records.AUDIT_POSITION_AFTER_RUN_CALLERS`, four rows, a reason each, enforced by
  `pool.environment_for`, two `run_path` teeth); the caller stamped in `command.json` and the
  caller's verdict, no record change; `audit_position_note` classified as harness prose in G1's
  always-excluded set (2 831 compared unchanged); rule: **a stage that needs a non-declared audit
  position is a row in that table, never a `Job` field set in passing** — the brief's "exactly one
  caller" was three, unrefused, because it was a sentence.
- **Improvement list:** item — *the `--resume` G1 press rewrites the `after` manifest's commit
  while keeping records at an earlier one; the verdict shows both, but the straddle line should be
  derived from the records' stamps, not the manifest's* (§8).
- **§3.9's gate table** could gain a row for `written_file_gap` if the orchestrator wants every
  registered gate listed there; it is a harness gate (no `plan_name`) and appears in §4.1 as such.

---

## 13. Change log

| date | change |
|---|---|
| 2026-09-14 | `09cc9f3e` — gate `written_file_gap`; `after_run` declared callers; prose corrected; `audit_position_note` to always-excluded; two `run_path` teeth. Pressed: `--gate written_file_gap` (6 runs, PASS 4/4), `--gate run_path --resume`, `--gate switch_neutrality --resume` (0 runs), `--gate run_kind_separation --resume`, `--measure gate_table --resume`, `--plan-tables write` / `check` (IDENTICAL), `--selfcheck` (7/7), `run_stamp_survey.py` |
| 2026-09-14 | `2a91602f` — plan §4 re-rendered |
| 2026-09-14 | `d44ac1e8` — README §8 |
| 2026-09-14 | `f1c29f26`, `1adeed66` — the gate publishes the argmax component written against solved (§5's table becomes a stage's output); `--gate written_file_gap --resume` (0 runs), `--measure gate_table --resume`, `--plan-tables write` / `check` (IDENTICAL, no change to the committed §4), stamp survey unchanged (184 records, 6 at `09cc9f3e`) |
| 2026-09-14 | this report |

---

## 13. Orchestrator's critical assessment (protocol §5)

*Written 2026-09-14 at the branch tip `cb1ac35a`, before the merge. Checks chosen to differ from the
agent's.*

1. **The gap, computed by a different route.** The gate publishes the `after_run` audit residual. I
   read each of the six run directories directly and compared three numbers the gate does not put
   side by side: `tfcoil.insstrain` in the driver's snapshot at the entry to the output path (the
   accepted state), the same component in `y_exit.json` (the state PROCESS finished with), and the
   value on the MFILE's `(insstrain)` line. On all six runs the MFILE value equals the exit value to
   every printed digit, and the relative distance from the accepted state is 7.18e-03 (`B1`/`B3`) and
   7.20e-03 (`BR`) on `large_tokamak_nof`, 7.02e-03 on all three arms of `low_aspect_ratio_DEMO`. Same
   conclusion as the gate's, reached without its code: the one-call path writes the same gap the loop
   path writes, and the written file carries the post-write value, not the accepted one.
2. **The refusal, probed with my own cases.** Calling the new `assert_audit_position_allowed` directly:
   a campaign run asking for `after_run` is refused even from a declared caller; a gate run with no
   caller or an undeclared one is refused; the declared gate run is allowed; a campaign run at the
   declared position is allowed. The refusal names the caller table.
3. **Trial merge onto trunk (`f8eeb750`)** is clean; the gate appears in `--gates` on the merged tree.
4. **The fourth caller.** The brief named GR and G1; the agent found the `attempts` stage's ladder runs
   also audit at `after_run` unrefused and declared it rather than leaving the table short. Correct,
   and an argument for the table's existence: a rule written in prose had drifted from three callers
   to one in its own comment.
5. **Autonomous decision 3** (`audit_position_note` into G1's always-excluded set) is accepted: it is
   harness prose stamped into the record, and G1 already excludes prose leaves the instrument rewrites
   (A62). The compared count is unchanged (2 831 / 0). **Decision 1** (caller stamped in
   `command.json` and the verdict, not the record) is accepted: it avoids a schema change and its
   re-make of every record, and the stamp is still per run and on disk.
6. **Read-only T7 finding** is the useful one for the plan: `norm_objf`, `sqsumsq`, `ifail` and the
   iteration variables are written by the solver handler from the optimiser's state before any model's
   `output()` runs, so no acceptance quantity of this experiment reads a post-write model value.
   Goes into I-21's row and the plan's §3.3.
7. **Observation 4** (G1's resume press rewrites the `after` manifest's commit while the records stay
   at theirs) is filed as improvement item 13 at the merge.

**Approved for merge.** Records relocate to `arch_surgery/idf_probe/runs/A67_runs/` (path from the
retire script).
