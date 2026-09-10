# A49 (harness-reference) — the reproduction reference, committed

> **Document status** — **OPEN task report.** Task `A49 (harness-reference)`, branch
> `A49-harness-reference` off `architecture_surgery` at `30198919`. Awaiting the orchestrator's
> critical assessment (orchestration protocol §5), which gates the merge. Nothing here is merged
> and nothing here is a campaign result: **no PROCESS run was made by this task.**

---

## 1. Verdict

The reproduction reference is built, committed and verified. It holds **20 entries — 14
optimisations and 6 evaluations — and 270 compared field values**, every one read from a record
made at the previous revision's campaign commit `362c0b47`.

| | |
|---|---|
| **`extract`** | PASS — 20 of 20 records read, 0 refusals, 32 430 bytes written |
| **`verify`** | PASS — the committed file re-derives **byte for byte** from the live records: 32 430 bytes identical, 20 entries, 270 field values |
| **teeth** | 4 of 4 tripped — a missing record, a missing compared field, the arm-name map bypassed, one changed value in the committed file |
| **committed file** | `arch_surgery/MDA_partitioning_experiment_v4/harness/reference/reproduction_reference.json`, sha256 `8fb3f768911e72ab…` |
| **PROCESS runs** | none |

Three things the task found that were not what the brief assumed, all recorded in §5 and §6:
the block-solver totals are **present on every record, including the reference arm's** (they are
the *never-entered* shape there, not absent, so nothing had to be marked "not applicable"); the
evaluation phase spells the objective differently and would otherwise have had **no
bit-comparison of the objective at all**; and the evaluation-phase records carry the
optimiser-attempt count as `0`, which is worth comparing rather than assuming.

---

## 2. Terms used in this report

Project shorthand, spelled out once, so this reads without the queue open beside it.

| term | meaning |
|---|---|
| **the previous revision** | `arch_surgery/MDA_partitioning_experiment_v3/`, whose campaign ran at commit `362c0b47`. Its run records are untracked bulk in the main checkout |
| **configuration** | one optimisation problem, named by its input file's stem: `large_tokamak_nof`, `low_aspect_ratio_DEMO`, `st_regression` |
| **arm** | one column of the experiment's switch matrix — one arrangement of solvers. `BR` is PROCESS as shipped, optimised; `B0` the flat control; `B3` the partitioned architecture; `A0`/`A1` their evaluation-phase counterparts; `B1` the flat control with the optimiser owning the burn time |
| **phase** | **B** is one full optimisation; **A** is one `call_models` evaluation with no optimiser |
| **seed** | which start the run was made from. Seed 0 is the unperturbed start, seed 1 the first perturbed one. The previous revision's directories spell these `start000` and `start001` |
| **node call** | one execution of one model call site — the experiment's unit of cost |
| **coupling state** | the measured set of state fields the in-loop models write (840 / 846 / 827 components on the three configurations); the fixed-point iteration converges it |
| **gate GR** | the reproduction gate: the rewritten harness, driving the experiment's own copy of PROCESS **before any change is made to that copy**, must reproduce the previous revision's twenty runs bit for bit. It runs once, at the copy commit |
| **teeth** | a check's demonstrated ability to fail. A deliberately broken input that the check must catch before its zeros are accepted |
| **the harness plan** | `arch_surgery/docs/plans/V4_HARNESS_IMPLEMENTATION_PLAN.md`; its §7 specifies gate GR and this task's deliverable |
| **T11** | the recorded trap of publishing a number without the population it holds over — three instances in this project. `arch_surgery/docs/TRAPS.md` |
| **I-14, I-15, I-16** | three recorded occasions on which this project destroyed untracked run records; one took with it the evidence behind a correction to a published headline |
| **D24** | the user's decision of 2026-09-10 delegating the harness rebuild to the orchestrator, with the tasks minted in advance |

---

## 3. What was built

Three files, one of them new to the harness package.

**`harness/reference.py`** — the reference half of gate GR, with two stages and their teeth.

- `extract` reads the twenty records of harness plan §7.1 from a `--previous-runs` root and writes
  `harness/reference/reproduction_reference.json`. Per entry: this revision's arm name and the
  previous revision's name for it, the configuration, the phase, the seed, the record's path
  relative to the runs root, the sha256 of the record file's bytes, the commit the record was made
  at, and the compared field values.
- `verify` re-derives the whole document from the live records and requires **byte-for-byte**
  equality with the committed one. Where the two differ it prints the byte offset with sixty
  characters of context on each side, then a field-level account of what moved, entry by entry.
- `REFERENCE_FIELDS` is exported as data, per phase, and `lookup(arm, configuration, seed)` returns
  one entry. Both exist for the run-path task, `A50 (harness-run)`, which imports this module (§8).
- The module docstring carries the entry schema.

**`harness/reference/reproduction_reference.json`** — 32 430 bytes, committed. Beside the entries it
carries a provenance block: what the file is, which gate reads it, the source revision's name,
campaign commit and runs root, the extraction date, the population sentence, the configurations,
the compared-field list per phase with a one-line meaning for each field, the enumerated
per-field population, the arm/configuration pair that is deliberately absent with the reason, the
two arms this reference cannot cover with the gate that covers each instead, and the command that
re-derives it.

**`experiment_runner.py`** — a `reproduction reference` stage in the preflight chain (it reports
what is committed and what it does not cover) and `--reference {show,tables,extract,verify,teeth}`
with `--previous-runs`, so that every path including all the refusals is reachable from the one
entry point rather than by retyping a module invocation (protocol §15). Each stage writes its own
record under `runs/reference/`, which is untracked.

**`harness/README.md` §11** — the plain-language section (§9 below).

Nothing is imported from, and no subprocess is started into, `arch_surgery/idf_probe/` or
`arch_surgery/fixedpoint/`. The previous revision's records are opened as JSON data and nothing
else.

---

## 4. The twenty entries

Produced by `experiment_runner.py --reference tables` at commit `b54580c8`, rendered from the
committed file rather than typed out of a JSON read at a shell prompt.

*Caption: the 20 entries of the committed reproduction reference — one row per reference run of
harness plan §7.1. "Arm" is this revision's name and "previous" the name the record directory
carries; "seed" 0 is the unperturbed start and 1 the first perturbed one. "sha256" is the first 12
characters of the source record file's digest. The two value columns are examples of the compared
fields, not the whole set: the optimisation phase compares 15 fields per record and the evaluation
phase 10, all of them in the committed file. Node calls are model executions during the solve
(optimisation phase) or in the one evaluation (evaluation phase); the objective is a hex float,
exact. Population: 20 records = 14 optimisations + 6 evaluations, over the 3 configurations
large_tokamak_nof, low_aspect_ratio_DEMO, st_regression; seed 0 is the unperturbed start and seed 1
the first perturbed one, every record at MDA_partitioning_experiment_v3 commit `362c0b47`.*

| arm | previous | configuration | phase | seed | sha256 | node calls | objective (hex) |
|---|---|---|---|---|---|---:|---|
| `BR` | `R` | large_tokamak_nof | B | 0 | `be4275bf60e5` | 42567 | `0x1.99999999b822dp+0` |
| `BR` | `R` | low_aspect_ratio_DEMO | B | 0 | `4fa2eed2554e` | 89964 | `-0x1.a00c1e7544537p-2` |
| `BR` | `R` | st_regression | B | 0 | `8021c4df695e` | 39669 | `-0x1.096acf3342eefp+4` |
| `B0` | `B0` | large_tokamak_nof | B | 0 | `e047d0cadd2d` | 43449 | `0x1.99999999b822ap+0` |
| `B0` | `B0` | low_aspect_ratio_DEMO | B | 0 | `55527b8b7cff` | 86877 | `-0x1.a00c1e754455cp-2` |
| `B0` | `B0` | st_regression | B | 0 | `8042790bc631` | 42756 | `-0x1.096acf3342e3cp+4` |
| `B3` | `B3` | large_tokamak_nof | B | 0 | `62b11aff0c4a` | 28055 | `0x1.9999999a4496cp+0` |
| `B3` | `B3` | low_aspect_ratio_DEMO | B | 0 | `aca74d8ba623` | 45496 | `-0x1.a00c0bc88c2c6p-2` |
| `B3` | `B3` | st_regression | B | 0 | `02f29d1be91c` | 23505 | `-0x1.096acf3342e55p+4` |
| `A0` | `A0` | large_tokamak_nof | A | 1 | `4770a57d21ed` | 126 | `0x1.999999999999ap+0` |
| `A0` | `A0` | low_aspect_ratio_DEMO | A | 1 | `10f33904a89b` | 105 | `-0x1.0022622fdbffdp-1` |
| `A0` | `A0` | st_regression | A | 1 | `cf4f579c2e6a` | 126 | `-0x1.4cc35295c7b00p+5` |
| `A1` | `A1` | large_tokamak_nof | A | 1 | `2d8e6a827e29` | 60 | `0x1.999999999999ap+0` |
| `A1` | `A1` | low_aspect_ratio_DEMO | A | 1 | `fe9722302263` | 60 | `-0x1.1b811d4d015dfp-1` |
| `A1` | `A1` | st_regression | A | 1 | `9c9e758c6c8d` | 62 | `-0x1.4cc35295c7b00p+5` |
| `B3` | `B3` | large_tokamak_nof | B | 1 | `d7b3722e373c` | 28037 | `0x1.99999999bb397p+0` |
| `B3` | `B3` | low_aspect_ratio_DEMO | B | 1 | `c577db913942` | 52834 | `-0x1.9fb1afe0ebcf7p-2` |
| `B3` | `B3` | st_regression | B | 1 | `20533a5f88d3` | 134560 | `-0x1.0cf146c754521p+4` |
| `B1` | `B1` | large_tokamak_nof | B | 1 | `d6a46ab09bc9` | 44100 | `0x1.99999999bb397p+0` |
| `B1` | `B1` | low_aspect_ratio_DEMO | B | 1 | `910c4cfd415d` | 81228 | `-0x1.9fb1afe0ebcf7p-2` |

**One row is deliberately short.** `B1` — the flat control with the optimiser owning the burn time
— is absent on `st_regression`. That configuration is steady state: it has no burn-time coupling,
so the arm composes onto its predecessor `B0` there, and the previous revision did not run it. The
absence is written into the committed file with that reason, taken from the configuration's own
recorded skip rather than from a second list. Nineteen entries under a heading that says twenty is
the shape trap **T11** describes.

**Two numbers in the table are worth a reader's eye and are context only, not this task's
finding.** `B3` on `st_regression` costs 23 505 node calls at seed 0 and 134 560 at seed 1 — a
factor of 5.7 between two starts of the same arm on the same configuration. That is the
`st_regression` behaviour task `A43 (st-trust-gap)` examined; nothing here re-opens it. The
reference records what the previous revision measured, whatever it measured.

---

## 5. What each phase's records actually carry

The harness plan's §7.1 names one field list. The two phases record different things, so which
fields each phase's records carry was **enumerated from the records**, not assumed. Every field
named for a phase is carried by every record of that phase, so each denominator below is also the
check: a record lacking a field its phase's list names is a refusal that names the record and the
field, not a quietly shorter comparison.

*Caption: the compared fields, per phase, with the number of records carrying each. "Beyond the
plan" marks a field harness plan §7.1 does not name literally for that phase; §6 gives the reason
for each. 15 fields × 14 optimisations + 10 fields × 6 evaluations = 270 compared values.*

| phase | field | carried by | beyond the plan |
|---|---|---:|---|
| B (optimisation) | `node_calls_solve_phase` | 14 / 14 | |
| B (optimisation) | `node_calls_total` | 14 / 14 | |
| B (optimisation) | `n_model_calls` | 14 / 14 | |
| B (optimisation) | `n_prime_calls` | 14 / 14 | |
| B (optimisation) | `exact.norm_objf` | 14 / 14 | |
| B (optimisation) | `exit_audit.residual_max_hex` | 14 / 14 | |
| B (optimisation) | `module_solve_totals.n_call_models` | 14 / 14 | |
| B (optimisation) | `module_solve_totals.block_sweeps` | 14 / 14 | |
| B (optimisation) | `module_solve_totals.outer_pass_hist` | 14 / 14 | |
| B (optimisation) | `module_solve_totals.inner_sweeps_by_block` | 14 / 14 | |
| B (optimisation) | `n_solver_iterations` | 14 / 14 | |
| B (optimisation) | `mfile.ifail` | 14 / 14 | |
| B (optimisation) | `exit_forensics.n_solver_iterations_summed_over_attempts` | 14 / 14 | |
| B (optimisation) | `exit_forensics.n_attempts` | 14 / 14 | |
| B (optimisation) | `exit_forensics.attempts[].n_solver_iterations` | 14 / 14 | |
| A (evaluation) | `node_calls_single_eval` | 6 / 6 | |
| A (evaluation) | `n_model_calls_sweeps` | 6 / 6 | |
| A (evaluation) | `n_prime_calls` | 6 / 6 | |
| A (evaluation) | `exact.objf` | 6 / 6 | yes |
| A (evaluation) | `exit_audit.residual_max_hex` | 6 / 6 | |
| A (evaluation) | `module_solve_totals.n_call_models` | 6 / 6 | |
| A (evaluation) | `module_solve_totals.block_sweeps` | 6 / 6 | |
| A (evaluation) | `module_solve_totals.outer_pass_hist` | 6 / 6 | |
| A (evaluation) | `module_solve_totals.inner_sweeps_by_block` | 6 / 6 | |
| A (evaluation) | `exit_forensics.n_attempts` | 6 / 6 | yes |

**Seven of §7.1's fields have no evaluation-phase counterpart at all**, and their absence is
structural rather than accidental: an evaluation has no optimiser and no solve phase, so
`node_calls_solve_phase`, `node_calls_total`, `n_model_calls`, `exact.norm_objf`,
`n_solver_iterations`, `mfile.ifail` and `exit_forensics.n_solver_iterations_summed_over_attempts`
are simply not written. They are therefore not in that phase's list, and the extraction never
looks for them there. That is a *declared* narrower list, not a skip: had one of the ten fields the
evaluation list does name been missing from a record, the extraction would have refused.

### 5.1 The block-solver totals are present on every record, including the reference arm's

The task brief expected `module_solve_totals` to be **absent** on flat arms and asked for that to
be recorded as "not applicable" rather than silently omitted. **The records say otherwise**, and
this is a correction rather than a nuance:

*Caption: one row per arm in the reference set; what the block-solver totals block looks like on it,
read from the committed entries. All twenty records carry the block; none is absent.*

| arm | shape of `module_solve_totals` | read as |
|---|---|---|
| `BR` | `n_call_models = 0`, `block_sweeps = 0`, both histograms empty | the block solver is **never entered**: upstream's own loop runs instead. Present and empty |
| `B0`, `B1`, `A0` | one block, named `FLAT` | the flat arm's own shape — one block over every in-loop node, not a missing partition |
| `B3`, `A1` | one entry per block in the schedule (`M1`, `M2`, `PULSE`, `M3`, `FF`) | the partitioned arm |

So no field had to be marked "not applicable": the reference-arm case is a *value* — an explicit
zero and two empty histograms — and it is compared like any other value. That is strictly stronger
than omitting it, because a rewritten harness that accidentally entered the block solver on the
reference arm would move `n_call_models` off zero and the gate would catch it. The distinction
between an omitted field and a zero field is exactly what a reader must be able to make, so the
committed file carries a one-line note per arm saying which of the three shapes it has and why.

---

## 6. Autonomous decisions, with their reversal paths

*Caption: one row per decision taken without asking, what it costs if wrong, and the exact change
that reverses it. None of these changes what is measured; all of them change what the gate compares
or how it is spelled.*

| # | decision | why | reversal |
|---|---|---|---|
| 1 | **Compare `exact.objf` in the evaluation phase**, which §7.1 does not name | §7.1 names `exact.norm_objf` and **no evaluation-phase record carries it** — that phase spells the same quantity `objf`. Without this field the evaluation phase would reproduce on counts alone, with no bit-comparison of the objective anywhere in it. Six of the twenty entries would have had no exact value but the residual | delete one line from `REFERENCE_FIELDS["A"]` in `harness/reference.py` and re-extract |
| 2 | **Compare `exit_forensics.n_attempts` in the evaluation phase**, where §7.1 names it for the optimisation phase only | every evaluation-phase record carries it as `0`. Comparing it states as a measured value what would otherwise be an assumption — that the evaluation entry point starts no optimiser | same: delete one line and re-extract |
| 3 | **The extraction date is an input to the re-derivation, not `today()`** | `verify` re-derives with the date the committed file already carries, so the byte comparison measures the records and nothing else. A stamp that changes daily would make byte-for-byte equality impossible to state | it is already explicit — `--extraction-date` on `extract`, and `verify` reads it from the file |
| 4 | **`verify` defaults its records root to the one the committed file names**; passing a different root is allowed and will FAIL on the provenance line | the root is a real input and the file records which directory the numbers came from. Verifying against a different root and passing would mean the file did not name its own source | pass `--previous-runs` explicitly |
| 5 | **The report's tables are emitted by the script** (`--reference tables`), captions included | protocol §15 and §16, and trap T11: a table typed out of a JSON read at a shell prompt has no committed producer and its caption is written by hand | none needed |
| 6 | **`Check` is imported from `harness/selfcheck.py`** rather than duplicated | one definition of the check-record shape. `A47 (harness-skeleton)`'s report says `A52 (harness-gates)` will promote `Check` to a `Gate`/`Tooth` pair; when it does, both files move together, which is the right coupling | define a local record type in `reference.py` — about fifteen lines |
| 7 | **The arm-name map is inverted from `switches.PREVIOUS_ARM_NAMES`, never written a second time** | the registry holds it one way round; a second copy is a second thing to get wrong. `harness/selfcheck.py` has its own private transcription for a different purpose and was not touched | none needed |
| 8 | **A V4-only arm raises rather than returning its own name** | `AR` and `A0p` have no record in the previous revision. Returning the name unchanged would build a path to a directory that never existed and then report "missing record" for what is really a coverage boundary. The refusal quotes the gate that covers each instead (harness plan §7.5) | remove the two entries from `ARMS_WITHOUT_PREVIOUS_RECORDS` |

### 6.1 A known interaction, stated rather than left to be discovered

The repository's `.pre-commit-config.yaml` runs a JSON formatter (`biome`) over committed JSON at
89-character line width. **Pre-commit is not installed in this checkout** — only `.sample` hooks
exist — so it did not touch the committed reference. If it is ever installed, it may reformat the
file, and `verify` will then FAIL with a byte offset, which is the correct behaviour: the committed
file would no longer be what the script produces. The fix in that case is to re-extract, not to
relax the comparison.

---

## 7. Teeth

Every one was constructed on a **throwaway copy**. Nothing under the main checkout's runs directory
is ever written to, and the copy holds only the twenty record files at their own relative paths.

*Caption: one row per tooth; the deliberate break, which stage must refuse, and what it did.
Produced by `experiment_runner.py --reference teeth` at `b54580c8`. All four tripped; a teeth run
that cannot construct its breaks — because the records are not reachable — reports FAIL rather than
passing over the teeth it could run.*

| tooth | construction | must | result |
|---|---|---|---|
| **missing record** | one of the twenty record files deleted from a throwaway copy (`B1`/`low_aspect_ratio_DEMO`/seed 1) | FAIL, **not skip** | **tripped** — `missing record for B1/low_aspect_ratio_DEMO/seed001: … does not exist. A missing record is a refusal, not a skip` |
| **missing compared field** | one compared field (`node_calls_solve_phase`) deleted from a throwaway copy of one record | FAIL naming the field | **tripped** — the refusal names the record path, the field and where in the record it was missing |
| **name map bypassed** | ask the previous revision's records for `BR` without going through the map; and ask for the two retired arms `A1u` and `B2` | **RAISE** | **tripped, three times** — `BR` raises with the previous revision's own name for it and a pointer to `previous_arm_name()`; `A1u` and `B2` each raise as retired |
| **one value changed in the committed file** | a throwaway copy of the committed reference with one count incremented by 1 (`BR`/`large_tokamak_nof`: `node_calls_solve_phase` 42 567 → 42 568) | `verify` FAIL | **tripped** — verification FAIL |

**A fifth demonstration happened by accident and is worth recording.** Mid-task the provenance
block's shape changed (the "beyond the plan" marker became per-phase, §6 row 1–2). `verify` failed
on the *next* run, naming byte 4838 and the provenance block, before the file was re-extracted.
That is the byte comparison catching a real change to a real file rather than a constructed one.

**Refusals not counted as teeth**, because they are ordinary behaviour rather than constructed
breaks, but each was exercised: an absent runs root on `extract` (`3`, with the path named and the
reason that the records live in the main checkout); an absent committed file on `show` and
`verify` (`3`, naming the command that produces it); and a record whose commit is not the previous
revision's campaign commit (refused by construction — no such record exists in the reference set,
and the check runs on all twenty).

---

## 8. What `A50 (harness-run)` must satisfy against this file

`A50 (harness-run)` builds the run path and runs gate GR. It imports this module. The contract:

*Caption: one row per obligation this file places on the run-path task; "why" is what breaks if it
is not met.*

| obligation | why |
|---|---|
| Read the compared-field list from **`REFERENCE_FIELDS`**, not from a second transcription of harness plan §7.1 | a comparator that keeps its own copy of the list can compare a different set from the one the reference was written with, and the mismatch would be invisible |
| Use **`lookup(arm, configuration, seed)`** to reach an entry, with the arm named as **this revision** names it | the entry carries both names; the map is applied inside. `lookup` raises on a miss and quotes the recorded reason where one exists (for example `B1` on `st_regression`) |
| Compare **all 15 optimisation-phase and all 10 evaluation-phase values**, and report the denominator — 270 over the twenty runs | a count of mismatches without the number of things compared is trap T11's shape, and GR's zeros are otherwise unreadable |
| Treat a **missing run** as a FAIL, exactly as a missing record is here | GR compares twenty runs to twenty entries; nineteen of either is a failed gate, not a smaller gate |
| Add GR's remaining three teeth — the **count** tooth (add 1 to one reproduced count), the **hex** tooth (append a character to one objective hex string) and the **composition** tooth (run `B3` with one switch of its composition deliberately wrong) — to the four demonstrated here | harness plan §7.3 lists seven; the four that belong to the reference are demonstrated in §7 above and the three that belong to the run path cannot be built until runs exist |
| Add the **attempt-summation refusal** (harness plan §7.3, improvement DR7): a record whose per-attempt node calls do not sum to `node_calls_solve_phase` is refused | the reference already carries `n_attempts` and the per-attempt iteration counts, so the summed and per-attempt constructions of the plan's check 2 can be checked against each other rather than trusted |
| State GR's **coverage boundary** in its own record, quoting `ARMS_WITHOUT_PREVIOUS_RECORDS` | `AR` and `A0p` have no reference entry; harness plan §7.5 names the substitute gate for each, and both are already in the committed file. A gate silent about what it does not cover is trap T11's shape |
| Run GR **at the copy commit, before any driver change** | after a driver change the difference between a V4 run and a previous-revision record is no longer attributable to the harness alone, and GR's single-variable argument is gone (harness plan §7.2) |

---

## 9. The README section

One section appended at the end of `harness/README.md` — §11, "The reproduction reference — the
previous revision's numbers, committed". In plain language, for a reader who has not followed the
project: what the file is and what question it answers; why it is committed rather than read from
the records, naming the three destroyed record sets; how to re-derive it, verify it, run its teeth
and emit its tables, with the interpreter and the records root spelled out; that every way of not
being able to compare is a failure and never a skip; the arm-name map and why bypassing it raises;
and a captioned table of the two arms this reference cannot cover with the gate that covers each
instead. No decision, issue or task numbers appear without their meaning beside them.

---

## 10. Reproducing every number in this report

```bash
PY=/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python
cd arch_surgery/MDA_partitioning_experiment_v4
RUNS=/home/wrutten/projects/PROCESS_surgery/arch_surgery/MDA_partitioning_experiment_v3/runs

# §1 verdict, §4 and §5 tables — the committed file and its two tables
$PY experiment_runner.py --reference show
$PY experiment_runner.py --reference tables

# §1 verify — byte-for-byte re-derivation from the live records (~2 s)
$PY experiment_runner.py --reference verify --previous-runs $RUNS

# §7 teeth — the four deliberate breaks (~3 s)
$PY experiment_runner.py --reference teeth --previous-runs $RUNS

# rebuild the committed file (only when the reference set or the field list changes)
$PY experiment_runner.py --reference extract --previous-runs $RUNS

# the preflight, with the new stage in the chain
$PY experiment_runner.py --tree repository --no-capability
```

Exit codes are the runner's: `0` pass, `3` fail. Each stage writes its record under
`runs/reference/`, which is untracked.

*Caption: one row per figure this report cites, the stage that produced it and the commit the
script was at. Every script was committed before its numbers were published (protocol §15).*

| figure | stage | commit |
|---|---|---|
| the 20 entries, the field populations (§4, §5) | `--reference tables`, rendered from the committed file | `b54580c8` |
| the committed file itself, 32 430 bytes, sha256 `8fb3f768911e72ab…` | `--reference extract` | `b54580c8` (first extracted at `a001b670`, re-extracted at the provenance-shape fix) |
| `verify` PASS, 20 entries, 270 field values (§1) | `--reference verify` | `b54580c8` |
| the four teeth (§7) | `--reference teeth` | `b54580c8` |
| the byte-4838 failure (§7) | `--reference verify` against the pre-fix committed file | between `2a087da4` and `b54580c8` |

**Two things about the records root.** It is in the **main checkout**, which this task read and
never wrote to. A task worktree has no such directory, and the default deliberately points at the
worktree's own non-existent path so that the refusal names it rather than guessing at another
checkout.

**Environment.** `PROCESS_surgery_env` throughout. **No PROCESS run was made**, so no tree
assertion was exercised and no measurement subprocess was started; the task reads JSON files and
writes one.

---

## 11. Limits of this task

Stated rather than left to be inferred.

- **The reference is not the gate.** It is the answer sheet. Gate GR — the twenty runs themselves
  and the comparison — is `A50 (harness-run)`'s, and until it runs, nothing here says the rewritten
  harness reproduces anything. This task says only that what must be reproduced is written down,
  committed, and re-derivable byte for byte.
- **`verify` proves the file matches the records, not that the records are right.** If the previous
  revision's campaign carried an error, this file carries it faithfully. That is the correct
  behaviour for a reproduction gate and it is worth saying: GR asks "same instrument?", never "right
  answer?".
- **Two of this revision's arms are outside the reference entirely** (`AR`, `A0p`). The file names
  them and names the gate that covers each; neither substitute is a comparison against a prior
  record, because none exists.
- **The compared fields are the harness plan's list plus two, not everything a record holds.** A
  record carries far more — the per-node census, the entry census, the constraint residual vector,
  the whole design vector. The gate compares the fifteen and ten fields the plan declares, and
  anything outside them could differ without GR noticing. Whether that list should widen is a
  question for the assessment, not something to widen quietly.
- **The extraction and the verification both need the main checkout.** They are not runnable from a
  worktree alone. That is why the file is committed.

---

## 12. Change log (append-only)

- **2026-09-10** — task **A49 (harness-reference)** opened on branch `A49-harness-reference` off
  `architecture_surgery` at `30198919`. Read `CLAUDE.md`, `arch_surgery/docs/TRAPS.md`, the
  orchestration protocol §§1–16, decisions D20/D23/D24 and the A49 queue row, the harness
  implementation plan §4, §6, §7 in full, §10 row H2 and §11 in full, the V4 experiment plan §1.3 /
  §3.2 / §3.5 / Appendix A, `harness/README.md`, and the archived reports of `A46 (process-copy)`
  and `A47 (harness-skeleton)`. Enumerated the twenty records' fields directly from the records
  before writing any code.
- **2026-09-10** — `a001b670`: `harness/reference.py` with the `extract` and `verify` stages, the
  inverted arm-name map with its refusals, `REFERENCE_FIELDS`, `lookup`, and the four teeth;
  `experiment_runner.py` gains `stage_reference` in the preflight chain and
  `--reference {show,extract,verify,teeth}` with `--previous-runs`.
- **2026-09-10** — `cc3ecaa6`: the committed reference, first extraction (32 390 bytes).
- **2026-09-10** — `2a087da4`: `--reference tables`, so the report's two tables and their captions
  are emitted by the committed script rather than typed from a JSON.
- **2026-09-10** — `1b92791a`: `harness/README.md` §11, the plain-language section.
- **2026-09-10** — `b54580c8`: the "beyond the plan" marker is keyed by **phase**, not by field
  name — `exit_forensics.n_attempts` is the plan's field in the optimisation phase and this
  module's addition in the evaluation phase, and keying by name alone misstated the plan in both.
  The reference re-extracted at the new provenance shape (32 430 bytes). `verify` caught the change
  itself, at byte 4838, before the re-extraction.
- **2026-09-10** — this report. `verify` PASS (20 entries, 270 field values, 32 430 bytes
  identical); teeth 4 of 4 tripped; the preflight remains READY against the repository tree with
  the new stage in the chain.

---

## 13. Orchestrator's critical assessment (protocol §5) — 2026-09-10

*Appended by the orchestrating session before merge, against the report at `d9ab7214` and the
module on the same branch. Load-bearing claims re-run, not taken from the report.*

**Verified independently.** (1) `experiment_runner.py --reference verify --previous-runs <the main
checkout's …_v3/runs>`: PASS, 20 entries, 32 430 bytes identical, 270 compared values; the
arithmetic is 15 fields × 14 optimisations + 10 fields × 6 evaluations. (2) `--reference teeth`:
4 of 4 tripped, each refusal naming the record, the field or the arm. (3) The committed JSON: 20
entries — `BR` and `B0` three each, `B3` six, `B1` two, `A0` and `A1` three each — every entry's
`tree_git_head` the full hash of `362c0b47`; entry schema arm / previous_arm / configuration /
phase / seed / group / source_path / source_sha256 / tree_git_head / fields. (4)
`harness/selfcheck.py --tree repository` still PASS on every check; the preflight's new reference
section prints the two arms GR cannot cover (`AR`, `A0p`) with their substitute gates, as harness
plan §7.5 requires. (5) Scope: five files, all under `…_v4/` plus this report; no import of, or
subprocess into, `idf_probe/` or `fixedpoint/`; the main checkout was read only.

**Endorsed.** Comparing the block-solver totals on the reference arm as a *value* (the
never-entered shape: 0 calls, empty histograms) rather than marking them not applicable — it makes
GR sensitive to a harness that entered the block solver under `BR`'s name, the positive-control
shape §7.3 wants. Adding `exact.objf` for the evaluation phase: §7.1 named `exact.norm_objf`, which
no Phase A record carries, and without the addition six of twenty entries would have had no
objective bit-comparison — accepted, and §7.1 is amended to say so. `exit_forensics.n_attempts = 0`
compared as a value in Phase A: accepted for the same reason. The refusal messages name the
population they protect (trap T11), and the name map is the only legal route from `R` to `BR`.

**Limits I hold it to.** (a) The reference is the plan's field list, not the whole record: the
per-node census, the entry census, the constraint residual vector and the design vector are outside
GR; widening it is a plan amendment, not a quiet extension. (b) `verify` measures the live records
against the committed file; it cannot detect a record that was already wrong at `362c0b47` — GR's
twenty runs (A50) are what test that. (c) The `Check` record type is imported from `selfcheck.py`;
A52 (harness-gates) promotes both together. (d) `.pre-commit-config.yaml` would reformat the JSON if
pre-commit were ever installed; `verify` would then FAIL by byte offset, and the remedy is
re-extraction, never a looser comparison — recorded so that nobody relaxes it.

**Consequences drawn (orchestrator, today).** Harness plan §7.1 amended: the evaluation-phase list
gains `exact.objf` and `exit_forensics.n_attempts`, and the reference arm's block-solver totals are
compared as values; §7.4 amended to the §11.1 name `reproduction_reference.json`. A50
(harness-run) reads `REFERENCE_FIELDS` and `lookup()` from this module and carries §8's
obligations into its brief, including GR's remaining teeth (count, hex, composition) and the DR7
attempt-summation refusal.

**Verdict.** Fit to merge; nothing returned.
