# A54 (harness-analysis) — every published cell, computed a second time, and compared

> **Document status** — **OPEN.** Task **A54 (harness-analysis)**, plan item **H7**. Branch
> `A54-harness-analysis`, off `architecture_surgery` at `06a85fa0` (the tip after A53
> (harness-tally)'s merge). Code at `9f29757f` and `12ba1054`; every number below was produced by
> `experiment_runner.py --gate recomputation --resume` and
> `experiment_runner.py --measure recomputed_tables --resume` at **`12ba1054`**, over run records
> made at **`cd62c510`** (A53's press, seeded into this worktree under amendment 15). **No PROCESS
> run was made by this task.** Folder position records lifecycle, not validity (trap T3).

---

## 0. What this task did, and the words it uses

**In one sentence.** The tally computes the experiment plan's §4 tables from the run records; this
task writes a **second implementation** of every one of those cells that shares no line of
construction with it, compares the two cell by cell over the tally's own emitted output, and puts
that comparison behind a gate with seven teeth — **1 847 values compared, 0 mismatched.**

**Why a second implementation at all.** Twice in this project a declared definition reached one
implementation and not the other and nothing failed (queue issues **I-18**, **I-19**). A gate that
compared the tally with itself would have passed both times. The only check that catches that shape
is a recomputation that cannot agree by construction — so `analysis.py` imports **no** part of
`stats.py`, `tally.py`, either tally stage, or `tables.py`, and the gate proves it by parsing its
own source.

*Caption: the words this report uses, each defined once. "New" marks a word this task adds to the
harness's vocabulary (`harness/README.md` §3).*

| word | what it means here | |
|---|---|---|
| **tally** | the first implementation: `tally_evaluation.py` and `tally_optimisation.py`, which emit the plan's §4 tables from the run records. A measurement stage — it has nothing to pass | — |
| **analysis** | the second implementation: `analysis.py`, which recomputes the same cells from the same records through its own constructions | — |
| **construction** | one declared way of computing a published number — which median, which population, what counts as an accepted optimum. The tally's live in `stats.py`, one function per declaration; the analysis re-derives each from that docstring | — |
| **cell** | one value of one row of one emitted table, plus the table's own denominator | — |
| **a cell from a construction** | a cell whose value is a number a construction produced — a median, a ratio, a count | **new** |
| **a cell composed as a string** | a cell a table builds by joining several values into text — `"3/3"`, `"[18, 68]"`, `"BR 0 · B0 0 · B3 0"`. Agreement here is weaker evidence than agreement on a number, so it carries its own denominator | **new** |
| **source** | a named subtree of `runs/gates/` whose records are a comparable set, with the sentence saying why. Two exist | — |
| **arm group** | within a source, a set of arms and the seeds at which *all* of them ran — the population the plan's "every arm converged" construction actually applies to | — |
| **independence** | that `analysis.py` imports none of the tally's modules. A **checked criterion** of the gate, not a comment | **new** |

---

## 1. Verdict

**`recomputation`: PASS at `12ba1054`.**

*Caption: the gate's own numbers, read from `runs/gates/recomputation/gate.json`. "Compared" is
every value the criterion put side by side; the three lines below it are what that number is made
of. Run records at `cd62c510`; this tree at `12ba1054`, which is what `--resume` is for and what
the verdict states.*

| quantity | value |
|---|---|
| verdict | **PASS** |
| values compared | **1 847** |
| values mismatched | **0** |
| — of which table cells | 1 809 over 168 rows of **65 tables** |
| — of which published values beside the tables | 37 (16 similarity verdicts × 2 readings, 5 seed sets) |
| — of which the independence check | 1 |
| teeth | **7 / 7 tripped** |
| run records read | **33**, all at `cd62c510` |
| declared sources read | 2 (`reference_runs`, `paired_entries`) |
| populations where the two implementations differ | **0** |
| PROCESS runs made | **0** |

**The 1 809 table cells split two ways** — 1 357 produced by a construction, 452 composed as a
string. The split is reported and never added into one number: two implementations landing on the
same median is evidence about a rule; two implementations landing on the same `"[18, 68]"` is
partly evidence about a format string.

**One ratio recomputed by hand, outside both implementations.** The published `B3` cost ratio
against `B0` on `large_tokamak_nof` is `0.6456995558010541`. The two records' solve-phase node
calls, read straight out of their `metrics.json`, are `28055` and `43449`, and
`28055 / 43449 = 0.6456995558010541` — bit-identical to the published cell. One number, checked by
a third route that is neither implementation.

---

## 2. What the second implementation is, and what makes it one

`harness/analysis.py` — 3 317 lines, no import of `stats.py`, `tally.py`, `tally_evaluation.py`,
`tally_optimisation.py` or `tables.py`. It imports `framework` (the `Gate`/`Check`/`Measurement`
shapes and `survey_heads`), `config` (the campaign's declared constants) and the arm-matrix order.

**Every construction is re-derived from its declaration.** `stats.py`'s docstrings are written to
be read as the specification — "nearest-rank, upper-middle", "`max(F × yardstick, floor)`",
"a seed is retried when **either** side of the pair retried" — and this module implements each from
that sentence and from the record fields `records.py` declares. Twenty-eight constructions, named
for what they do rather than for what they are called in `stats.py`: `middle`, `ninetieth`,
`extremes`, `at_an_accepted_optimum`, `ratio_three_ways`, `cost_with_and_without_retried`,
`objective_clusters`, `restricted_audit`, `empty_visit_sweep_share`, and the rest.

**Every population is re-derived too**, not imported: the two declared sources with their path
filter, the `force_maxcal` exclusion, the seed-complete arm-group split, and `retried` counted from
`attempts[]`. A population the two derive differently is a **finding** the verdict prints, never
something reconciled in silence. §4 reports what was found.

**What it reads from the tally is output, not code**: `runs/gates/tally_evaluation/measurements.json`
and `…/tally_optimisation/measurements.json`, table by table, row by row keyed by the table's own
key columns, cell by cell. **No tolerance anywhere** — `_same` is exact equality, with NaN equal to
NaN, so a difference in the last bits of a float is a mismatch by construction. That is deliberate:
a tolerance here would be a place for a drift to hide.

**Independence is a checked criterion, not a comment.** The gate parses `analysis.py`'s own source
and fails if it imports any of the five forbidden modules. It is one more thing compared, so it is
in the denominator. Tooth 7 shows the scanner names all three of a doctored import list and names
nothing in a source that imports only the framework.

---

## 3. The comparison, table kind by table kind

*Caption: one row per kind of table the two implementations emit, with the instances of it at this
commit and the cell positions compared in them. "From a construction" and "composed as a string"
are the two denominators of §1, split per kind. Rows = 0 is a table with a real denominator and no
row, which is a result: no seed fell outside a converged set on any arm group.*

| table kind | instances | rows | cells from a construction | cells composed as a string |
|---|---|---|---|---|
| cost per call | 6 | 14 | 98 | 56 |
| matched accuracy | 6 | 28 | 224 | 84 |
| ownership rung A0 → A0p | 2 | 2 | 12 | 4 |
| per-sweep overhead | 11 | 27 | 296 | 54 |
| failure taxonomy | 6 | 14 | 42 | 14 |
| the predicate trial | 1 | 12 | 120 | 12 |
| the seed set | 5 | 5 | 20 | 15 |
| the failure table | 5 | **0** | 0 | 0 |
| same optimum (check 1) | 3 | 6 | 42 | 18 |
| iteration multiplier (check 2) | 3 | 6 | 42 | 18 |
| the attempt summation identity | 5 | 13 | 91 | 52 |
| cost (check 4) | 3 | 9 | 99 | 9 |
| achieved accuracy at the accepted optimum | 5 | 26 | 182 | 104 |
| the lift closed (check 3) | 4 | 6 | 24 | 12 |
| **total** | **65** | **168** | **1 292** | **452** |

The 65 tables and the 6 tables **not produced** (each `B1·B3` arm group carries no `B0` run, and
checks 1, 2 and 4 are all anchored on it) are the same 65 and the same 6 on both sides. Neither
implementation emits a table the other does not.

### What cannot be recomputed from the records

**One table of the 65 — *the predicate trial*, 132 cell positions — is not built from run records
at all.** Its decisive-pass counts come from an observer that watches each predicate evaluation
*while the run happens* and reads it again on the other ruler; nothing in a record afterwards
reconstructs them. The analysis recomputes that table's **shaping** from the same gate verdict the
tally read (`gates/predicate_mode/gate.json`), and the gate's verdict names the table so a reader
can see that those cells check the table and not the measurement. The other 1 612 cell positions
come from the run records on both sides.

---

## 4. Populations: what the two implementations agree about, and what differs

**Nothing differs.** Source by source and phase by phase:

*Caption: one row per population each implementation derives independently. "Analysis" is derived
here from the declaration; "tally" is read out of the tally's own stage record. The seed sets are
the optimisation-phase arm groups' converged sets.*

| population | analysis | tally |
|---|---|---|
| `reference_runs`, evaluation phase | 6 records | 6 |
| `reference_runs`, optimisation phase | 14 records | 14 |
| `paired_entries`, evaluation phase | 8 records | 8 |
| records stamped `force_maxcal` | 0 | 0 |
| seed-complete arm groups | 5, with converged sets `[0]`/`[1]` as listed | identical, all 5 |
| similarity verdicts | 16 | 16, identical on median and p90 |

**Two latent differences found, neither of which bites on this population**, both reported here
rather than reconciled:

1. **The `n` column of the two accuracy tables is built two ways.** In `matched accuracy`
   (evaluation phase) `n` counts the *values* — the finished runs that carry a restricted maximum.
   In `achieved accuracy` (optimisation phase) `n` counts the *runs*. The comparison is **silent on
   the `n` column across all 54 rows of the two accuracy tables**, so over this population the two
   constructions coincide — every finished record here carries a restricted maximum, which is why.
   They would diverge on a record whose restricted block is null, a case the plan's own caption
   anticipates ("a run whose restricted block is null carries no count at all"). Same heading, two
   constructions; it should be one, and this population cannot tell them apart.
2. **The `instrument` column's separator differs between the two tables** — `";"` in the evaluation
   phase, `"; "` in the optimisation phase. Presentation only, but it is an emitted cell, and this
   implementation had to reproduce both to compare.

---

## 5. The teeth

*Caption: one row per deliberate break the criterion must catch, and what it did. All seven ran in
the verdict at `12ba1054`; a tooth that does not trip fails the gate.*

| # | the break | what the gate must do | result |
|---|---|---|---|
| 1 | one integer cell of the tally's published output raised by 1 | report the mismatch — proves the comparison reads the tally | **TRIPPED** — 1 mismatch, naming the table, row and column |
| 2 | the pooled ratio recomputed against **Σ arm** instead of **Σ reference**, for a whole recomputation | report the mismatches — proves the comparison reads the records through this module's own rules | **TRIPPED** — 20 mismatches; first is `cost (check 4) … B3 with_pooled`: 1.5487 against the published 0.6457 |
| 3 | no table on either side | refuse | **TRIPPED** — "the comparison is empty: 0 table(s) and 0 cell(s)…" |
| 4 | a record stamped `force_maxcal` in a population | refuse | **TRIPPED** — refused by name, naming the record |
| 5 | `attempt_accounting.retried` disagreeing with `attempts[]`, in **both** directions | follow `attempts[]`, never the stored flag | **TRIPPED** — computes `False` for the stored `True`, `True` for the stored `False` |
| 6 | two records carrying different `tree_git_head` | refuse without `--resume`; state the straddle with it | **TRIPPED** — refused, and stated under `--resume` |
| 7 | a source importing `harness.stats`, `harness.tally_optimisation`, `harness.tables` | name all three, and name nothing in a source importing only the framework | **TRIPPED** |

**7 / 7.** Teeth 1 and 2 are deliberately the two halves of one claim: a doctored *published cell*
proves the comparison reads the tally, and a doctored *construction* — applied to a whole
recomputation, not to one cell — proves it reads the records. A comparison that agreed with
anything would pass neither.

**Two further refusals exercised outside the tooth list**, because they are refusals of the stage
rather than of the criterion: `--verify` without `--resume` on this seeded worktree refuses and
names both commits; `read_tally_output` against a directory with no stage record refuses and names
the `--measure` to run first.

---

## 6. The two entry points, and where they are registered

*Caption: what this task adds to `gates.registry`, as one contiguous block beside the tally's.*

| name | kind | under | what it is |
|---|---|---|---|
| `recomputation` | `Gate`, 7 teeth, no PROCESS run | `--gate` | the criterion of §1, promoted by `framework.gate_from_check` without restating it |
| `recomputed_tables` | `Measurement`, no verdict | `--measure` | this implementation's own 65 tables, 1 744 cells, each with its own caption and denominator |

`--gate all` and `--measure all` pick both up from the registry with no further wiring;
`recomputation` is last in `GATE_ORDER` and declares `reads_from = ("reproduction",
"entry_and_warm")`, so it runs after the gates whose records it summarises. `analysis.py` also has
its own button — `--verify`, `--teeth`, `--tables` — for running the comparison or the teeth alone.

**The `recomputed_tables` stage refuses a table of its own** built without a caption, without an
integer denominator, or without a sentence saying what the denominator counts. That is the same
rule `tables.py` enforces for the tally, implemented a second time, which is the point.

---

## 7. Autonomous decisions, each with its reversal

*Caption: one row per decision this task took without asking, why, and how to undo it.*

| # | decision | why | reversal |
|---|---|---|---|
| 1 | the gate is named `recomputation` and the stage `recomputed_tables` | named for what they do; no task number and no version token (the user's 2026-09-10 ruling) | rename both in `analysis.py` and the one registry block |
| 2 | the analysis reads the tally's **output** and refuses when it is absent, rather than producing it | importing either tally module to produce it would forfeit the independence the whole gate rests on | let the gate import the tally stage and call it; the comparison then agrees by construction and proves nothing |
| 3 | **independence is a checked criterion with its own tooth**, not a comment | it is the property every number in §1 depends on, and an unchecked property is an assertion (protocol §12) | drop `forbidden_imports` and tooth 7; the claim then rests on review |
| 4 | cell counts are split into **from a construction** and **composed as a string** | agreement on a rendered `"[18, 68]"` is partly agreement about a format string, and adding the two into one denominator would overstate the evidence | report one number; the denominator then mixes two kinds of evidence |
| 5 | the similarity verdicts and the seed sets are compared **beside** the table cells | they are published values in the stage records; a comparison over the tables alone would leave them unverified | compare only `tables`; 37 published values then go unchecked |
| 6 | tooth 2 alters the construction by **replacing this module's ratio function for the length of the tooth** and restoring it | a tooth that edited one output cell would prove less than one that runs a whole recomputation with the wrong rule | doctor a single cell instead; the tooth then exercises the comparison and not the pipeline |
| 7 | *the predicate trial* is recomputed from the same **gate verdict**, and the verdict says so | the alternative is to leave 132 cells unverified; reshaping them from the same source at least checks the table | drop the table from the analysis; the comparison then reports it as "only in the tally" |
| 8 | the two latent population differences of §4.1 and §4.2 are **reported, not fixed** | they are in the tally, and the physics-frozen discipline applies to the tally too: a task that quietly edits the implementation it is verifying is not verifying it | change the tally's `n` construction and separator; the comparison then agrees for a different reason |
| 9 | the registry additions are **one contiguous block**, as A53's were | A62 (exit-audit-restore) is merging in parallel | scatter them; the merge conflicts inside a dictionary |

---

## 8. Handover

*This task edited no plan, no queue row and no improvement item; those are the orchestrator's.*

### To the orchestrator — what the plans should gain

- **Harness plan, Appendix A — a new amendment: H7 delivered.** `analysis.py` with `--verify`
  (gate `recomputation`, seven teeth), `--teeth` and `--tables` (stage `recomputed_tables`);
  **1 847 values compared, 0 mismatched, over 65 tables and 33 run records at `cd62c510`**;
  independence from the tally's modules a checked criterion rather than a convention. §4.3's
  "the tally and the analysis start from the records, not from each other" is realised, and
  `--verify` is the only thing in the package that can catch the I-18/I-19 shape.

- **A gate cannot declare that it reads a measurement stage.** `Gate.reads_from` names gates, and
  `ordered_gate_names` raises on a dependency the gate registry does not hold — so
  `recomputation`'s real dependency on `tally_evaluation` and `tally_optimisation` is expressible
  only as a comment and a place in `GATE_ORDER`. On a **seeded** worktree this does not bite — A53's
  relocated gate records carry the two stages' `measurements.json` with them — but on a tree with no
  tally output `--gate all` reaches `recomputation` last and **refuses**, naming the `--measure` to
  run first. The sharper case is **staleness, which nothing refuses**: the gate checks the commit of
  the *run records* it reads, not the freshness of the tally's stage records against them, so a tally
  record left over from before a change that moves cells would be compared against a recomputation of
  the new records and report mismatches that are really a stale file. Either the chain becomes
  `--measure tally_evaluation tally_optimisation` → `--gate recomputation`, or the framework gains a
  measurement dependency a gate can declare. This is a fork and belongs to the orchestrator.

- **`Gate.runs_under` is relative to `runs/gates`, not to `runs/`** — one directory apart from what
  a `tally.Source.subpath` is relative to. A wrong one there surveys an empty tree and the verdict
  reports **"0 record(s)"** instead of the straddle, silently, with no failure: the staleness check
  in `Gate.run` is gated on `n_records > 0`. This task hit it and fixed it (the constant now derives
  the gate-relative form), but the shape is a latent trap for every later gate and is worth a line
  in the plan or in `TRAPS.md`.

- **The `n` column of `matched accuracy` and `achieved accuracy` is built two ways** (§4.1). They
  agree over all 54 rows of this population and would not on a record whose restricted block is null —
  which A62 makes more likely, not less. One construction, please, in `stats.py`.

- **A62 (exit-audit-restore) moves every `exit_audit.*` cell in parallel with this task.** The
  analysis reads the instrument's version **through the record** (`audit_instrument`, from
  `audit_snapshot`'s own fields) and never assumes it, exactly as `stats.audit_instrument` does, so
  the two implementations stay comparable across that merge and a caption that names the instrument
  stays true. What will change after A62 is the *values* in the accuracy tables on both sides, and
  the gate should be re-run at the merged tip — 0 mismatches there is the statement that A62's new
  instrument reached both implementations.

- **The `recomputation` verdict is not in the plan's §4.1 gate table yet** — `gate_table` fills
  itself from the verdict records, so it appears automatically once the gate has run.

### To A55 (harness-smoke)

- **The chain order matters, and the seeded tree hides it.** A53's relocated gate records carry
  `runs/gates/tally_evaluation/measurements.json` and `…/tally_optimisation/…` with them, so on a
  seeded worktree `--gate all --resume` finds what `recomputation` needs. On a tree without them it
  reaches `recomputation` last and **refuses**, naming the `--measure` to run first. Safer either
  way: run `--measure tally_evaluation` and `--measure tally_optimisation` before the gates, so the
  comparison is against a tally record made from the same run records the gate reads. Nothing
  refuses a *stale* tally record — only a run-record straddle is refused.
- **Neither entry point starts a PROCESS run.** `recomputation` and `recomputed_tables` are pure
  readers: `needs_runs=False`, and this whole task made 0 runs.
- **`--resume` is load-bearing.** Without it the gate refuses a population whose records were made
  at another commit, and names both. That is the right behaviour and a smoke must not route around
  it (amendment 13 rule (i)).
- The analysis has its own button for a fast check without the registry:
  `python -m harness.analysis --teeth` runs the seven breaks in a few seconds.

---

## 9. Limits of what is reported here

- **0 mismatches over 1 847 values is a statement about these records.** The population is 33 gate
  runs at one or two seeds per arm — `EXECUTION_APPROVED` is False and no campaign record exists.
  It says the two implementations agree *on what these records exercise*, and nothing about
  constructions no record here reaches.
- **Several constructions are untested by this comparison because nothing in these records triggers
  them.** No run retried, so the with/without-retried split is two identical columns on both sides
  and the retry-specific path of `cost_with_and_without_retried` is exercised only by tooth 5's
  synthetic record. No seed failed, so **the failure table has 0 rows in all five instances** and
  its seven columns are compared over nothing. No pair hopped clusters and none fell below cluster
  resolution, so `hop_rate` and `below_resolution` are compared at 0 on both sides.
- **452 of the 1 809 compared cells are composed strings.** Agreement there is partly agreement
  about a format, not about a construction. The two denominators are reported apart for exactly
  that reason and should not be added.
- **132 cell positions — the whole predicate-trial table — are not recomputable from run records.**
  Both implementations read them from the same gate verdict, so their agreement checks the table's
  shaping and not the measurement behind it. The verdict says so by name.
- **The exact-equality rule cuts both ways.** Its strength is that no drift can hide under a
  tolerance; its cost is that a future change to a summation order in either implementation would
  be reported as a mismatch even where the declared construction is unchanged. That is the intended
  trade, but it is a cost a later reader
  should know about.
- **The independence check reads imports, not behaviour.** It would not catch a construction copied
  into `analysis.py` by hand rather than imported. What guards against that is that the
  constructions here are written from the docstrings and are named differently; it is not a
  machine-checked property and is not claimed as one.
- **Nothing here is timed.** No conclusion rests on a clock; every quantity in this report is a
  count or an exact comparison, and both reproduce bit-for-bit.
- **The records were not re-made.** They are A53's, at `cd62c510`, seeded under amendment 15; the
  verdict states that straddle rather than leaving it to be assumed, and `--resume` is what admits
  it. No PROCESS run was made by this task, so nothing here re-verifies the runs themselves — that
  is GR's and the gates' business, and their verdicts stand from A53's press.

---

## 10. Change log

| commit | what |
|---|---|
| `9f29757f` | `harness/analysis.py`; gate `recomputation` and stage `recomputed_tables` registered in `gates.py` as one contiguous block; `GATE_ORDER` gains the gate last; `harness/README.md` §10, §5 and a new §14 |
| `12ba1054` | the similarity verdicts and the seed sets — published values beside the tables — compared and counted in the same denominator |
