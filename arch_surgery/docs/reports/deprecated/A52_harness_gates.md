# A52 (harness-gates) — every verification gate inside the harness, in one framework, on one button

> **Document status** — **ARCHIVED 2026-09-11 — merged into `architecture_surgery` at `d13a54c7`.** Task
> **A52 (harness-gates)**, branch `A52-harness-gates` off `5e64ce0e`; the figures in §1–§13 were taken at
> `5aa83db9` (the agent's from-scratch press) and those in §14 at `eb38c34a` (the orchestrator's press from the
> repository root). Run records relocated to `arch_surgery/idf_probe/runs/A52_runs/gates/` (untracked). The orchestrator's
> critical assessment (protocol §5) is §14. Folder position records lifecycle, not validity (trap T3).

---

## 0. What this task did, and the words it uses

**In one sentence.** The V4 harness could already run the experiment and could already check most
of the things the experiment plan says must be checked — but those checks lived in three shapes, in
four files, reachable by four different commands, and five of the plan's own gates did not exist at
all; this task puts every one of them into a single framework with a single registry behind a
single button, builds the six that were missing, and reviews what the comparing gates had stopped
comparing.

**Vocabulary, spelled out once** (orchestration protocol §4 — a report should read without the
queue open beside it):

| word | meaning |
|---|---|
| **gate** | a check that must pass before a number is believed. It has a criterion, a population, a denominator, and teeth |
| **tooth** | a deliberate break the gate must catch. A check whose failure mode has never been exercised is an assertion, not a measurement (protocol §12) |
| **measurement stage** | the other thing in the registry: it publishes numbers the plan asks for by name and has **nothing to pass**. A different type, so a table cannot be read as a verdict |
| **configuration** | one optimisation problem — one input file. Three of them: `large_tokamak_nof`, `low_aspect_ratio_DEMO`, `st_regression` (pulsed, pulsed, steady state) |
| **arm** | one column of the experiment's switch matrix: one setting of the driver's architecture switches. `AR`/`A0`/`A0p`/`A1` run one model evaluation; `BR`/`B0`/`B1`/`B3` run one optimisation |
| **the coupling state** | the ~840 model quantities the partitioned solver has to agree on. 840 / 846 / 827 components by configuration |
| **the exit audit** | one further full sweep of the whole model set past termination, on the identical instrument in every arm, whose own model calls are never charged to the arm. It says how far from converged the state still was |
| **the restricted audit** | the same maximum with the components the *per-run deferred* nodes write taken out, because those nodes run once at the end by design and their components are supposed to move |
| **the prime** | the arrangement's *method-level* move: the first-wall geometry method run at the head of every sweep, so the node that reads its two lengths reads this pass's values |
| **τ** | the one tolerance every convergence loop uses, 1e-6 |
| **heritage names** | `A<n> (keyword)` labels name the task that did a thing; they appear in docstrings and reports, never in identifiers |

**Project shorthand used below.** *D5* — the physics is frozen; only the driver changes. *D11* — a
minimal structural edit to a model is permitted with the user's approval. *D20* — V4 runs its own
copy of PROCESS. *D23* — one tolerance for every convergence loop. *T11* — a number published
without the condition that limits it; the recurring error this project gates against. *Protocol
§12* — a gate must be shown capable of failing, and every count carries its denominator. *Protocol
§15* — every published number comes from executing a committed script.

---

## 1. Verdict

**Every gate passes, and every tooth trips.** One command, `experiment_runner.py --gate all`, runs
**21 gates** — eleven of the experiment plan's own (GR, G0/G0′, G1 through G9) and ten of the
harness's own checks promoted into the same framework — and returns 0 with **21 PASS, 0 FAIL, and
**109 of 109 teeth tripped** — pressed **from the repository root, from nothing, with no
`--resume`**, so every run it read was made by that press. `--measure all` runs seven measurement
stages and returns 0. `--selfcheck` passes.
`--artifacts all --census-entry evaluation` passes. The preflight is READY. `copy_gates.py all`
passes and `PROCESS_diff.py` exits 0 with the same seven files.

**Gate G1 is a real straddle.** Its "before" capture was made at trunk `5e64ce0e` in the main
checkout and its "after" at `5aa83db9`, so the two sides are two commits **and two trees**. It
PASSES: **0 of 3 164** record values and **0 of 51 319** output-file lines differ, 714 values and 45
lines excluded, each named with its reason. §4.3.

**Every run the gates read was made by the press that read it.** The survey the orchestrator asked
for: of the 150 records under `runs/gates/`, **144 are at `5aa83db9`**, the commit the run was made
at, and **6 at `5e64ce0e`** — gate G1's trunk capture, the one artifact that cannot be re-made. No
gate printed a stale-runs note, because there was nothing to note.

**Six gates that did not exist are built** — G2, G3/G3c, G4, G5, G6, G7 — each inside `harness/`,
each with its runs through the pool, its denominator and its teeth. Where a criterion is inherited
from the previous revision, the criterion is restated here and **its agreement with that revision's
recorded figures is a gate result**: the cold-chain gate reproduces 244 / 240 / 218 / 124 exactly
and every residual maximum to the bit.

**Nothing under `…_v4/PROCESS/` changed.** The diff of this branch against its base touches thirteen
files, all of them in `harness/` or the runner. `copy_gates.py all` passes; `PROCESS_diff.py` exits
0 with the same **seven** changed files and no unexplained hunk; G0′ passes with `pulse.py` as the
one approved difference.

**Three things were found by gates failing before they passed** during the build, and all three are
reported rather than tuned away:

1. **The cold-chain gate cannot be a single comparison.** This revision's partitioned arm defers
   three nodes to once per run; the previous revision's chain did not. Read on the whole-state
   audit they are different measurements by construction — 112 components above τ with the prime
   on, every one owned by a deferred node. The gate now runs **both** compositions and reads each
   the way it must be read.
2. **A switch left unset and a switch set to its default compose different environments and the
   same arm.** The composition gate compares what the driver *resolved*, not only what the harness
   asked for, because of it.
3. **G1's exclusion set had stopped describing itself.** The names excluded because *one particular
   pair of commits* straddled the change that added a field were excluded unconditionally, and so
   went on hiding those fields for ever. Made conditional, they put leaves back into the comparison
   — **416** over the straddle this task ran, and the count is a property of the pairing rather than
   of the table, which the review now says (§5).

Five further defects were found by the orchestrator's review and fixed on the branch; §13 lists
them. Two are worth the verdict's space: **the capability probe's result depended on which
directory the button was pressed from** (the working directory shadowed `PYTHONPATH`, and the
repository's own `process/` package won), and **a genuine two-tree straddle of G1 failed on nine
cross-tree paths that no exclusion named**, because every earlier run of that gate made both
captures inside one worktree.

**One measured item is for the user**, and it is stronger than when it was filed: `tfcoil.insstrain`
sits ~7e-3 above τ in the restricted audit at the accepted point on both pulsed configurations —
and now on the **reference arm `BR` as well as the intervention arms**, which is new. §6.4.

---

## 2. The framework, and what "promoted" means

### 2.1 One file, three shapes, one rule enforced at import

`harness/framework.py` holds `Gate`, `Tooth`, `Check` and a new `Measurement`. `gates.Gate` and
`gates.Tooth` stay where the plan names them, as re-exports, so a reader who looks them up finds
them.

The rule the plan's §6 asks for is enforced rather than reviewed: **`Gate.__post_init__` raises a
`TypeError` when a gate is constructed with no tooth.** "We forgot the tooth" is therefore a failure
when the module loads, not an omission somebody has to catch at review. Every gate writes a verdict
record to `runs/gates/<name>/gate.json` carrying its population, denominator, mismatches and the
result of every tooth.

`Measurement` is deliberately a *different type*. A measurement publishes what the plan asks for by
name and has nothing to pass; giving it the same type as a gate would let a reader take a table for
a verdict. It has no teeth **because it has no criterion**, and it names the gate that guards the
same records.

### 2.2 The promotion: the criteria moved, the numbers did not

`selfcheck.Check` and `artifacts.StageCheck` were the same dataclass, field for field, written
twice. Both are now `framework.Check` — one definition — and `framework.gate_from_check` promotes a
check into the gate framework **by running the same function**. It adds the verdict record, the
registry entry and a declared tooth list; it changes no criterion.

*Caption: the six self-checks and four artifact stages before and after promotion. "Compared" is
each check's own denominator, read from its own output; the two columns are the same number because
the promotion runs the same function. The artifact-check stage's count is 93 before its derivation
stage has run and 95 after — a condition that was already recorded when the stage was written.*

| check | compared, before promotion | compared, after promotion | teeth |
|---|---|---|---|
| composition | 42 | 42 | 7/7 |
| rungs | 98 | 98 | 3/3 |
| capability | 54 | 54 | 14/14 |
| provenance | 4 | 4 | 4/4 |
| data | 17 | 17 | 6/6 |
| run path | 9 | 9 | 12/12 |
| artifacts — check | 93 / 95 | 95 | 3/3 |
| artifacts — derive inputs | 2 | 2 | 4/4 |
| artifacts — census | 81 | 81 | 2/2 |
| artifacts — per-run deferral | 16 | 16 | 2/2 |

**The declared tooth list is the part worth stating.** A promotion that copied whatever teeth the
check happened to run would be a declaration that cannot fail. Instead each promoted gate *names*
the teeth its criterion must run: a declared tooth the check no longer exercises is a tooth that DID
NOT TRIP, and a tooth the check runs that the gate does not declare fails it too. So "the six
self-checks still run the teeth they claim" is a comparison rather than a belief. The
capability check's eleven retired-name teeth are generated from the same switch registry the check
generates them from, so a retired name added later moves both together.

### 2.3 The registry, and the button

`gates.registry(campaign)` returns **every** gate and **every** measurement stage in one dictionary,
each carrying the experiment plan's own label where it has one. `experiment_runner.py` gains:

| option | what it does |
|---|---|
| `--gates` | list every gate and measurement stage, what each binds, its teeth, and whether it starts PROCESS |
| `--gate <name>` | run one gate and stop |
| `--gate all` | run every gate, cheapest first **and after whatever it reads**, stopping at the first failure — so a repository-state failure is reported in seconds rather than after an hour of runs |
| `--resume` | keep a run whose directory already holds a *complete record of the same job*. **It reaches the gates' own runs**, not only `--run`: without it every gate re-makes the runs it reads |
| `--measure <name>` / `--measure all` | run the measurement stages. Gates never run here and measurements never run under `--gate`: the two cannot be confused |
| `--no-teeth` | skip the teeth; the verdict records that it did, and a gate whose teeth were not run is not an accepted gate |
| `--capture before\|after` | gate G1 only (§4.3) |

**The `--outdir` quirk A57 (driver-output-path) recorded is fixed.** `--outdir` now redirects every
gate's *verdict*, which `--gate reproduction` previously ignored. It deliberately does **not**
redirect the gates' own runs: the output-path gate reads the reproduction gate's runs to show that
nothing about the solve changed on the arms that keep the output-time loop, and moving those runs
would break a cross-reference between two gates in order to relocate a small JSON file. That is
stated in the option's own help text.

**Every gate makes its own runs, and `--resume` decides whether it re-makes them.** Without the
flag every run a gate reads is made again, so a verdict is never computed over records made before
the change it is checking; with it, a directory already holding a *complete record of the same job*
is kept — not a retry, because `pool.run` checks the job matches first. Every verdict record carries
`runs_provenance`, the distinct commits its records were made at, and the printed verdict carries a
`runs read` line; records from another commit are expected under `--resume`, **stated either way**,
and a failure without it. Two exceptions, both stated where they happen: the shared cold-flat
reference evaluations are made once per invocation and shared, and gate G1's "before" capture is
never re-made (§4.3).

**The order is derived, not written down.** `GATE_ORDER` is a preference; a gate's `reads_from`
declares which other gates' runs or verdicts it reads, and where the two conflict the dependency
wins.

---

## 3. The gate table — the plan's §4.1, filled in

*Caption: one row per registered gate, emitted by `experiment_runner.py --measure gate_table` from
the verdict records themselves, so no cell here is hand-copied. "Plan" is the label the experiment
plan's §3.9 table uses, empty where the gate is one of the harness's own checks promoted into the
same framework. "Verdict" is PASS/FAIL on the criterion **and** on every tooth tripping.
"Compared" is the denominator and "mismatched" the count that differed; where a gate compares more
than one kind of thing — coupling-state components, record values, output-file lines — the
denominator is their sum and the record names each part. "Teeth" is tripped / declared. **One row
reads 1 mismatched and PASS**: the frozen-physics gate counts the single model file the user
approved under D11 as differing, by name, and passes because it is the approved one. Taken at commit
`5aa83db9`; records under `arch_surgery/MDA_partitioning_experiment_v4/runs/gates/`, which is
untracked by design.*

| gate | plan | verdict | population | compared | mismatched | teeth |
|---|---|---|---|---|---|---|
| `reproduction` | GR | **PASS** | 20 runs (14 optimisations + 6 evaluations) over 3 configurations; no tolerance on any value | 270 | 0 | 7/7 |
| `g0prime` | G0 / G0′ | **PASS** | 77 files under `PROCESS/process/models/` against `c0ae5b28` by `git cat-file`, plus the file set | 77 | 1 (approved) | 4/4 |
| `switch_neutrality` | G1 | **PASS** | straddles `5e64ce0e` → `5aa83db9`, a neutrality result; 6 run pairs = 3 configurations × 2 reference arms; 3 164 record values + 51 319 output-file lines | 54 483 | 0 | 6/6 |
| `prime_map` | G2 | **PASS** | 6 arrangement/configuration pairs; 12 evaluations | 5 026 | 0 | 2/2 |
| `cold_chain` | G3 / G3c | **PASS** | 8 chain/composition pairs over 4 chains; 16 evaluations; 60 individual checks | 60 | 0 | 4/4 |
| `audit_restriction` | G4 | **PASS** | 13 doctored runs over 3 configurations, each against that configuration's undoctored run | 12 | 0 | 5/5 |
| `switch_composition` | G5 | **PASS** | 3 configurations; 6 optimisations; 37 switch names + 10 run values each | 141 | 0 | 3/3 |
| `entry_and_warm` | G6 | **PASS** | 5 entry pairs at seed 1; 5 warm runs; 13 evaluations | 4 204 | 0 | 3/3 |
| `record_completeness` | G7 | **PASS** | 2 runs on `st_regression`; 85 declared fields in the optimisation phase, 78 in the evaluation phase | 163 | 0 | 9/9 |
| `predicate_mode` | G8 | **PASS** | 12 pairs × 2 rulers = 24 runs; 7 600 record values + 84 output-file lines | 7 684 | 0 | 4/4 |
| `output_path` | G9 | **PASS** | 11 runs at seed 0; 3 825 coupling-state components + 54 solve-describing values | 3 879 | 0 | 4/4 |
| `composition` | — | **PASS** | 8 arms × 3 configurations = 24 pairs, compared by role | 42 | 0 | 7/7 |
| `rungs` | — | **PASS** | 11 matrix rows × 8 arms = 88 cells; 6 rung steps | 98 | 0 | 3/3 |
| `capability` | — | **PASS** | every arm/configuration pair whose arm is active, plus the probe started from a directory that shadows the tree | 55 | 0 | 15/15 |
| `provenance` | — | **PASS** | one scratch repository, three states | 4 | 0 | 4/4 |
| `data` | — | **PASS** | 16 committed files + the moved predicate module; 9 declared counts | 17 | 0 | 6/6 |
| `run_path` | — | **PASS** | 2 phases × the declared field list; 2 displacement streams; 4 refusals | 9 | 0 | 12/12 |
| `artifacts_check` | — | **PASS** | 19 artifact rows over 3 configurations | 95 | 0 | 3/3 |
| `artifacts_derive_inputs` | — | **PASS** | 3 configurations; the digest gate applies to the 2 pulsed ones | 2 | 0 | 4/4 |
| `artifacts_census` | — | **PASS** | 3 configurations, one evaluation census each, read half on | 81 | 0 | 2/2 |
| `artifacts_per_run` | — | **PASS** | 5 (configuration, input file) pairs over 3 configurations | 16 | 0 | 2/2 |

**21 PASS, 0 FAIL, 0 not run; 109 of 109 teeth tripped** — from nothing, from the repository root,
with no `--resume`; and identical when pressed from the experiment directory.

*How to read: no number in the experiment's results section is cited unless every row here is PASS
with its teeth tripped. A FAIL is a result and the dependent tables are marked "not produced — gate
X failed".*

**The experiment plan's §4.1 placeholder is not edited by this task** — that file is not on this
task's owned list, and the plan's amendments are the orchestrator's. The table above is the filled
version, and `--measure gate_table` regenerates it, including its markdown form, from the records.
§10 hands that over.

---

## 4. The gates, one by one

### 4.1 GR — the rewrite reproduces the previous revision *(registered, re-run)*

**Criterion** (plan §7.1, inherited unchanged): twenty of the previous revision's records
reproduced **bit-exactly** on every count field and hex float through the rewritten harness against
the copy of PROCESS. No tolerance anywhere.

**Why it is re-run here:** this task changes what an optimisation record contains (§6.3), and a
harness change must not move the measurement.

**Result: PASS.** 20 of 20 runs reproduced; **270 of 270** compared values identical; the record
contract 20/20; both of the plan's §7.5 substitutes (`A0p` warm-equivalence, `AR` first-call) PASS;
**7 of 7 teeth** trip — count, hex, missing reference, missing key, bad name map, composition (7 of
15 values differ when `B3` is run with the flat loop under its name), and the attempt-summation
refusal.

GR is now a registered gate rather than a special case of the runner. Its verdict record carries the
stage's whole verdict inside it, because both write to the same path and a reader who opens that
file must find everything.

### 4.2 G0 / G0′ — the physics stays frozen in the copy

**Criterion** (plan §7.6): every file under `…_v4/PROCESS/process/models/` byte-identical to
`c0ae5b28`, compared against the commit by `git cat-file`, never against a working tree.

**Result: PASS.** 77 model files compared, 76 byte-identical, **one approved difference**
(`process/models/pulse.py`, D14(b) — the burn-time residual extracted into a driver-solvable form,
the arithmetic verbatim), 0 unapproved, 0 missing, 0 added. 4 teeth: a one-byte change, a file
removed, a file added, and a further change to the approved file.

The plan lists G0 and G0′ as two rows; in V4 they state the same criterion, so they are **one
gate** with the label `G0 / G0'`. Two entries for one criterion is how two implementations start.

### 4.3 G1 — switch neutrality, as a real straddle

**Criterion** (plan §3.9): with every architecture switch unset, the copy after a change behaves
byte-identically to the copy before it — every deterministic leaf of the run record and every line
of PROCESS's own output file.

**This run is a genuine straddle, and that took the orchestrator's capture.** G1's two sides are
meant to be two commits, and this task makes no driver change, so the version of this report before
review ran it with both captures at one commit and said so. The orchestrator then made the real
"before" capture at trunk `5e64ce0e` in the main checkout and put it in this worktree. The two
sides are therefore **two commits and two trees**, which is the harder of the two ways to straddle
and the one no earlier run of this gate had ever done.

**It failed first, on 42 of 3 206 values, and the failure was worth having.** The 42 were exactly
two things.

*(a) Nine names that no exclusion named, because every earlier G1 made both captures inside one
worktree*, where a path in one is a path in the other. All are a path or the working tree's own
state, so no pair of captures could ever compare them, and they now sit in the always-excluded
group with their reasons:

| name | leaves | what it is |
|---|---|---|
| `per_run_artifact` | 6 | an absolute path to the per-run deferral artifact — absent on the trunk optimisation records, a path here |
| `process_copy_provenance.path` | 6 | an absolute path to the copied driver |
| `tree_git_branch` | 6 | the branch the tree is on: the working tree's state, different by construction across two trees |
| `coupling_state_artifact` | 3 | an absolute path to the coupling-state artifact |
| `coupling_state_provenance.path` | 3 | the same path inside the provenance block |
| `exit_audit.frozen.restricted.artifact` / `.census` | 6 | absolute paths; DR5's **per-ruler copies** of two leaves that were excluded only under their unprefixed names |
| `exit_audit.mixed.restricted.artifact` / `.census` | 6 | the same, on the second ruler |

**What still carries the artifacts' identity**: `excluded_sha256` on the restricted block and
`components_sha256` on the coupling state are compared, so each file is still checked to be the
*same file*, by content rather than by location. The two ways of straddling — one tree at two
commits, or two trees — now give the same answer, which is the property the fix is for.

*(b) Six leaves that are the record change itself*, and they needed a new kind of condition.
`exit_audit.frozen.n_excluded_from_the_restricted_statistic` and its `mixed` twin read **0** on the
trunk records, because the statistic was never computed there and 0 stood for "not computed"; they
read 122 / 123 here. Both sides carry a number and both are non-null, so the existing condition —
"excluded where one side lacks the leaf" — cannot decide. They are now conditional on a **witness**:
`CONDITIONAL_WITNESS` names the restricted block itself, and the count is excluded exactly where
that block is null on one side. Where both sides carry the block the count is compared like
anything else, and **a tooth shows it**: moving one count by one on a record that carries the block
on both sides is caught and the field is named.

**Result: PASS.** 6 run pairs; **0 of 3 164** record values and **0 of 51 319** output-file lines
differ; **714** values and 45 lines excluded, each named with its reason in the verdict record.

*Caption: one row per run pair. "Values" is that pair's compared record leaves; "lines" its compared
output-file lines. Population: `BR` (one optimisation) and `AR` (one evaluation) on each of the
three configurations, every architecture switch cleared — which is the condition G1 is about.*

| arm | configuration | values | lines |
|---|---|---|---|
| `BR` | `large_tokamak_nof` | 0 / 644 | 0 / 16 173 |
| `AR` | `large_tokamak_nof` | 0 / 461 | 0 / 7 |
| `BR` | `low_aspect_ratio_DEMO` | 0 / 637 | 0 / 16 434 |
| `AR` | `low_aspect_ratio_DEMO` | 0 / 448 | 0 / 7 |
| `BR` | `st_regression` | 0 / 551 | 0 / 18 691 |
| `AR` | `st_regression` | 0 / 423 | 0 / 7 |

**Teeth (6/6).** A 1-ULP move; one changed output line; a missing "before" record refused; two
captures audited at different positions refused; the exclusion this task added shown to be
load-bearing — nulling `exit_audit.restricted` on a record that **carries** it makes 13 of 683
values differ without the exclusion and 0 of 670 with it; and the new witness tooth above. The
load-bearing tooth used to take its sample from the "before" side, which at trunk carries no
restricted block at all — so it could not be built in exactly the run where it matters. It now
takes the side that carries the block.

**A verdict now says which of the two it is.** `_straddle` reads both captures' manifests and
prefixes the population, the verdict record and therefore the plan's gate-table row with either
*"straddles A → B: a neutrality result"* or *"BOTH CAPTURES AT `<commit>`: determinism and exclusion
coverage, NOT a driver-change result"*. A PASS from a self-comparison can no longer read like a
neutrality verdict.

**The "before" capture is never re-made, and the reason is measured.** The gate makes one only when
there is none at all. `pool.run`'s resume consults the **current** completeness contract, and this
task declared `per_run_artifact` in the record schema — so resume judges the trunk capture's
*optimisation* records incomplete (they predate the field) and would re-run them, replacing a
capture that cannot be re-made. Measured here: resume keeps the trunk `AR` records and rejects the
trunk `BR` ones. The evaluation records survive, the optimisation ones would not, and the guard is
that nothing hands that capture to resume.

### 4.4 G2 — the prime's fixed-point map *(new)*

**Criterion, restated from the previous revision's own gate:** *"from each configuration's reference
exit snapshot: one flat call and one partitioned call, prime on vs off, exit states bit-identical on
N/N components — 840 (nof) / 846 (lad) / 827 (st)"*; tooth: *"a doctored snapshot component trips
the comparison"*.

**Population:** 3 reference evaluations (the cold flat control, shared with G4 and G6) + 12
evaluations = 6 arrangement/configuration pairs.

**Result: PASS.** **5 026 components compared** (2 × [840 + 846 + 827]), **0 differing**. Every
declared component was compared on every pair — a short state would have been caught, and is the
second tooth. The method is called once per sweep when on and not at all when off, on every pair.

**Teeth (2/2).** One unit in the last place on one float of a prime-on exit state gives exactly one
differing component of 827 — on `blanket.deg_blkt_inboard_poloidal_plasma`, at
`0x1.2207dc1466873p+7 → 0x1.2207dc1466874p+7`, **the same component and the same two literals the
previous revision's tooth used**. A component deleted from one side is counted as differing rather
than quietly shrinking the population.

### 4.5 G3 / G3c — the cold chain, and the finding that shaped it *(new)*

**Criterion, restated:** from the cold entry, the partitioned chain with the prime on must leave the
coupling state at its fixed point — the in-run exit audit counting **0** components at or above τ,
with the named residual-mover set empty — where the same chain with the prime off does not, by the
figure the previous revision measured.

**The finding, made by the gate failing.** Read on the whole-state audit, this revision's arm and
the previous revision's chain are **not the same measurement and cannot be**. This revision's `A1`
composes `PROCESS_ARCH_DEFER_PER_RUN`; the previous revision's chain did not set it at all (read
read-only from that revision's own run records, which stamp the full environment). Three nodes that
ran on every sweep now run once, at the end, by design — so their components move in the audit
sweep. Measured: **112 components above τ with the prime on, on every configuration, every one of
them owned by a deferred node.**

So the gate runs each chain under **two compositions**:

*Caption: one row per chain and composition. "Prime-off count" is the number of coupling-state
components at or above τ = 1e-6 in the uncharged exit audit with the arrangement's method-level move
switched off, against the figure the previous revision recorded for that configuration; "prime-on"
is the same count with the move on, and the residual maximum as a hex float against that revision's.
The statistic is the **restricted** audit where the arm defers three nodes per run and the
**whole-state** audit where it does not, because the deferred nodes' components are supposed to move
in the audit sweep. Population: 4 chains × 2 compositions × prime on/off = 16 evaluations.*

| gate | configuration | entry | composition | prime-off count | expected | prime-off maximum | prime-on count | prime-on maximum | expected |
|---|---|---|---|---|---|---|---|---|---|
| G3 | `large_tokamak_nof` | cold | as composed | 182 | — | `0x1.de05b6285d3f4p-7` | **0** | `0x1.51fbaf5134221p-30` | `0x1.51fbaf5134221p-30` |
| G3 | `large_tokamak_nof` | cold | previous revision's | **244** | **244** | `0x1.de05b6285d3f4p-7` | **0** | `0x1.51fbaf5134221p-30` | ✓ |
| G3c | `low_aspect_ratio_DEMO` | cold | as composed | 178 | — | `0x1.47e807abb1ed5p-5` | **0** | `0x0.0p+0` | `0x0.0p+0` |
| G3c | `low_aspect_ratio_DEMO` | cold | previous revision's | **240** | **240** | `0x1.47e807abb1ed5p-5` | **0** | `0x0.0p+0` | ✓ |
| G3c | `low_aspect_ratio_DEMO` | δ = 0.10 | as composed | 160 | — | `0x1.30a27ad23ca7fp-10` | **0** | `0x0.0p+0` | `0x0.0p+0` |
| G3c | `low_aspect_ratio_DEMO` | δ = 0.10 | previous revision's | **218** | **218** | `0x1.30a27ad23ca7fp-10` | **0** | `0x0.0p+0` | ✓ |
| G3 | `st_regression` | cold | as composed | 82 | — | `0x1.25880f0afff76p-6` | **0** | `0x1.c22fb514702ddp-29` | `0x1.c22fb514702ddp-29` |
| G3 | `st_regression` | cold | previous revision's | **124** | **124** | `0x1.25880f0afff76p-6` | **0** | `0x1.c22fb514702ddp-29` | ✓ |

**Result: PASS**, 60 individual checks, 0 failed. The previous revision's counts come back
**exactly** — 244 / 240 / 218 / 124 — and every residual maximum matches its recorded hex float to
the bit, on both the prime-off and the prime-on side. That agreement is a gate result, not an
assumption.

**A correction to the brief, made by measurement.** The figures **244 and 124 are
`large_tokamak_nof`'s and `st_regression`'s**, not `low_aspect_ratio_DEMO`'s. They are G3's, and G3
ran on those two configurations *precisely because* `low_aspect_ratio_DEMO` is the one that
revision's census never traced — which is why G3c exists at all. That configuration's own prime-off
figures are **240** cold and **218** displaced. Both sets are checked here, each against the
configuration that produced it.

**G3c's verdict on the open term.** `tfcoil.m_tf_coil_superconductor` — the term the previous
revision left open on this configuration — **CLOSES under the prime**, on both the cold entry
(0.0400 scaled with the prime off) and the displaced one (0.00116 with it off), and is absent from
the residual-mover set with it on. The mover set is empty on every chain.

**Two coverage boundaries, stated in the gate's own record rather than left to be noticed.**

- The previous revision's *"3 outer passes → 2"* **cannot be re-run at this commit**: driver change
  DR1 removed the repeated block schedule, so `partitioned` means the schedule runs exactly once and
  there are no outer passes to count. What survives is the half that carries the claim.
- G3c's carrier **coefficients** are not reproduced: they were read from a per-pass residual trace
  which the V4 plan's §4.6 deliberately drops from composition because nothing V4 publishes reads
  it. G3c's *verdict* — whether the open term closes, and what the mover set holds — is read from
  the audit residual vector and is reported in full.

**Teeth (4/4).** The prime-off chain reproducing the earlier figures is itself the positive control:
a zero from the prime-on chain means nothing unless the count is shown to be measurable. Plus a
doctored count, a doctored maximum, and an invented residual mover.

### 4.6 G4 — the audit's restriction, in every namespace *(new)*

**Criterion** (plan §3.9 and improvement item 6a(c)): a doctored `per_run`-owned component trips the
whole-state audit and **not** the restricted one; a doctored in-loop component trips the restricted
one (or costs more work); **one doctored component from each excluded namespace**, both directions,
every namespace.

**The namespaces are derived, never listed**, from `postsolve.derive(...)["crawl"]["candidate_units"]`
— and from the **run-time** census, not the committed one. That distinction was found by this gate
failing: the committed artifact records what a node *writes*, and the crawl needs what a node *ran*.
A node whose body is guarded off on a configuration writes nothing and is still executed on every
sweep — which is precisely a node worth deferring — so a unit list taken from the writers alone
drops it. On the steady-state configuration that node is `pulse`, and a whole excluded namespace was
being lost in silence. Derived here: `costs`, `vacuum`, `water_use` on both pulsed configurations
and those three plus `pulse` on `st_regression`, which is exactly the set A51 (harness-artifacts)
measured.

**`pulse` on `st_regression` owns no coupling-state component**, so there is nothing to doctor and
nothing the restriction could hide. That is recorded with its count — zero — as the certification,
not skipped as a gap. It is I-20(a)'s empty node in another light.

**Population:** 3 undoctored runs + 12 doctored runs (9 per-run-owned, one per namespace per
configuration; 3 in-loop) + 3 optimisations. **Result: PASS**, 12 of 12 doctored runs satisfying
every check.

*Caption: the components doctored, one per excluded namespace per configuration plus one in-loop
component each, displaced by a factor of 1.5 in the entry snapshot. Each is a continuous float,
non-zero, and **not owned by the design vector** — a component the sweep head re-injects from `x`
would be silently reset and the doctoring would test nothing.*

| configuration | `costs` | `vacuum` | `water_use` | `pulse` | in-loop |
|---|---|---|---|---|---|
| `large_tokamak_nof` | `costs.c21` | `vacuum.dia_vv_vacuum_ducts` | `water_use.energypervol` | — | `blanket.deg_blkt_inboard_poloidal_plasma` |
| `low_aspect_ratio_DEMO` | `costs.blkcst` | `vacuum.dia_vv_vacuum_ducts` | `water_use.energypervol` | — | `blanket.deg_blkt_inboard_poloidal_plasma` |
| `st_regression` | `costs.c21` | `vacuum.dia_vv_vacuum_ducts` | `water_use.energypervol` | writes nothing here (0 components) | `blanket.deg_blkt_inboard_poloidal_plasma` |

**Teeth (5/5).** Both directions; every derived namespace covered on every configuration; the
restricted statistic reaching the optimisation record; and one comparator tooth — the bit-identity
check of a per-run-owned run's restricted maximum, forced to false, must fail that run's check,
which is what makes its agreement a measurement rather than a tautology.

### 4.7 G5 — the matrix equals the arm, composed switch by switch *(new)*

**Criterion** (plan §3.9): the arm composed from the matrix equals the arm composed switch by
switch — `norm_objf` hex, `ifail`, iterations, the pass histogram, the exit-audit hex — with teeth on
`norm_objf` hex and `n_call_models`.

The second composition is a **hand transcription of the plan's own §3.2 column for `B3`**, set one
switch at a time in the plan's row order from a cleared environment. It is written out on purpose: a
table derived from `arms.py` would be `arms.py` checking itself. The second run is driven by that
dictionary name for name, through `Job.override_env`, so it is genuinely the hand-built environment
that reaches the driver.

**Result: PASS.** 3 configurations, 6 optimisations, **141 compared** (37 switch names + 10 run
values each), **0 differing**. 3 teeth: the objective's hex with one character appended; the
model-call count plus one; a switch dropped from the hand-built column, which must read as exactly
one differing name.

**Two findings, both from the gate failing first.**

1. **A switch left *unset* and a switch set to its *default* compose different environments and the
   same arm.** The matrix leaves `PROCESS_ARCH_PREDICATE` unset because the campaign's ruler is the
   driver's default; the hand column set it to `frozen`. The fix is not to write the default into
   the column but to **compare what the driver resolved** — `resolved_switches`, read back from the
   imported modules — so "unset" and "frozen" have to reach the same place or the gate fails. That
   field is now one of the ten compared values.
2. **The plan's burn-time-owner row is marked as applying on the pulsed configurations only.** On
   the steady-state one it is left unset, not set to `loop`. The plan's own footnote is what
   settles it.

### 4.8 G6 — the entries pair, and a warm arm lands *(new)*

**Criterion** (plan §3.9): seed-paired entries bit-identical across arms per configuration; each
block arm, entered from the reference snapshot and pinned at the reference's converged burn time,
reproduces the reference fixed point with cross-state maximum scaled residual below τ and the pinned
component bit-identical. Teeth as the previous revision's.

**Result: PASS.** **4 204 components compared** over 5 entry pairs at seed 1, **0 differing**: the
displaced coupling state a seed produces is the same bytes for the flat control, the pinned flat arm
and the partitioned arm — although the pinned arms reach their burn time through a *constant*
computed as the reference's converged value times that seed's own factor, and the unpinned one
reaches it through the displacement stream. Two routes to one number, and a gate is the only thing
that says they arrive at the same bits.

Five warm runs (both block arms on the pulsed configurations, the partitioned arm on the steady-state
one) land on the reference fixed point: cross-state maximum below τ, categorically clean, pinned
component bit-identical, pin intact at exit.

**Teeth (3/3).** The previous revision's two comparator teeth — a continuous component bumped by
3 τ × its measured scale (reads 3.000e-06 against τ = 1e-06, so the criterion must stop holding) and
a discrete component flipped (makes the comparison categorically unclean however small the maximum
is) — plus a doctored entry state, which must be the one and only differing component of 840.

**Stated rather than left to be discovered:** the flat pinned arm's warm landing is *also* the
reproduction gate's §7.5 substitute. This gate runs it too, under its own root, so that both block
arms are compared on one page.

### 4.9 G7 — a record carries what it declares, even when the run fails *(new)*

**Criterion** (plan §3.9): a forced-unconverged smoke run carries every declared field; a record with
a field missing is refused by the completeness contract; five field teeth.

The failure is forced with the harness's own lever, `--force-maxcal 2`, which caps the optimiser's
iteration budget so the solver exhausts its retry ladder and exits unconverged. **The cap is stamped
into the record as `force_maxcal`, and that stamp is the guard**: every tally, every gate population
and every measurement stage filters records carrying it, because a budget-capped run is a
demonstration and never a measurement.

**Result: PASS.** Two runs on `st_regression` (the configuration with the fewest iteration
variables, derived rather than named). The optimisation record carries **84 of 84** declared fields
with the five forensics fields non-null, `ifail ≠ 1`, both convergence rulers, and per-attempt costs
that sum to the run total. The evaluation record carries **77 of 77**.

**The two phases are not symmetric, and the report says so rather than pretending.** The evaluation
phase has *no optimiser to leave unconverged* — it runs exactly one `call_models` — so its record is
checked on an ordinary smoke run. What it must carry is its own phase's field list, both rulers, and
an explicit "no attempts" rather than a missing key.

**Teeth (8/8).** The previous revision's five field teeth (`n_solver_iterations`, `mfile.ifail`,
`exit_forensics.ladder_stage`, `.constraint_residual_vector`, `.active_set`), each refused **by
name**; the whole forensics block deleted; and two for contracts that did not exist when that gate
was written — one convergence ruler and not both, and per-attempt costs of 400 + 550 against a run
total of 1 000.

### 4.10 G8 and G9 — registered and re-run

Both existed; both are now registered in the one registry, reachable as `--gate predicate_mode` and
`--gate output_path`, and **make their own runs** with resume rather than needing a separate shell
command — nothing about them needs two commits, and a stage that exists only as a shell invocation
is not reproducible (protocol §15).

**G8 (the convergence predicate's second ruler): PASS.** 12 of 12 pairs bit-identical; **0 of 7 600**
record values and **0 of 84** output-file lines differ; 216 values excluded under 17 names; 143
predicate evaluations observed, 66 binding component events, **0 evaluations changed verdict**; 4
teeth. Its neutrality part reads GR's verdict rather than re-measuring it, and now reads it through
the framework's record shape as well as the stage's — a gate that could not read its own evidence
would have reported NO EVIDENCE over a file that has it.

**G9 (the output path): PASS.** 11 runs at seed 0; **0 of 3 825** coupling-state components differ in
hex; **0 of 54** solve-describing values differ from the reproduction gate's records; 4 teeth. The
intervention arms run **0** output-time sweeps and write the accepted objective to the bit.

---

## 5. The exclusion sets, reviewed

A gate that compares two records names the leaves it does not compare, each with its reason. That is
the right shape. A list of names that only ever grows is the same failure one step later, and it had
started: G1's set went 33 → 43 → 48 → 58 names across four driver changes, and each addition was
correct for the pair of commits that made it.

`--measure exclusion_review` classifies every name by kind and **measures** it against the gate's own
captured records: how many leaves it covers on each side, whether both sides carry them, whether
they agree. The measurement alone cannot decide, and the report says why: `tree_git_head` reads
equal whenever two captures happen to be at one commit and differs the moment they are not. So each
name also carries a declared *kind*, and the verdict rests on both.

### 5.1 G1 — 70 names, split into 36 and 34

*Caption: gate G1's exclusions grouped by kind, measured over its 6 run pairs, which straddle
`5e64ce0e` → `3f50d9b5`. "Leaves" is how many record leaves the group covers over that pairing,
counting each leaf once. **The leaf count is a property of the pairing, not of the table**: a name
that is one-sided across a real straddle is excluded there and compared in a self-comparison, so
the same table gives a different count against a different pair of captures. The review says which
pairing it measured. A structural name is excluded however equal it reads; a "field a change adds"
is excluded only where one side actually lacks it — or, for two names, where the block that would
have computed it is null on one side.*

| kind | names | verdict |
|---|---|---|
| a path into a run's own directory, the tree, or an artifact | 18 | **KEPT unconditional** |
| a timing or the machine's state | 7 | **KEPT unconditional** |
| the commit, or the working tree's state | 9 | **KEPT unconditional** |
| the switch vocabulary a rename changes | 2 | **KEPT unconditional** |
| **a field a change adds** (null or absent before, a value after) | **32** | **MADE CONDITIONAL** on the field's own leaf |
| **a count whose zero means "not computed"** | **2** | **MADE CONDITIONAL** on a *witness* — the restricted block |

**Sizes: 59 names before this review, 70 after** — 9 structural names the two-tree straddle exposed
and 2 conditional counts the witness mechanism needed — of which **36 are always excluded** and
**34 conditional**. The set grew because the review found things that were being compared and should
not have been; what shrank is the number of names excluded *unconditionally*, from 59 to 36.

**What the condition recovered, over this pairing:** **416 leaves**. It was 1 040 against a
same-commit pairing, and both numbers are right for the pair they were measured over — which is
exactly why the count now travels with its pairing. The largest contributors over this straddle are
`predicate_counters` (156 leaves), `attempt_accounting` (114) and `attempts[].sweeps_per_eval` (20);
the two witness-conditioned counts recover 6 leaves each, on the evaluation arm, where both commits
computed the restricted statistic and only the optimisation arm did not.

**Three names are inert over this pairing** — `output_loop_null_because`,
`predicate_counters_null_because`, `attempts[].cost_null_because` — matching no leaf on either side.
They are the sentences a record carries *instead of* a counter the driver does not stamp, so they
appear exactly in the case they exist for. **Nothing was deleted from the table**: a name that has
stopped being needed is worth more visible than gone, and the condition is what makes it inert.

**The `[]` list-element matcher is kept and is load-bearing.** Seven of the conditional names are
`attempts[].…`: they exclude one leaf of every attempt and leave the rest of each attempt — the exit
code, the iteration count, the finite-difference step, the rung name — compared element by element.
Excluding `attempts` by its bare name would have taken all of them out.

**The one name this task added, and what it hides, measured.** `exit_audit.restricted` on an
optimisation record is null before this task and a block after (§6.3). The G1 tooth builds the
earlier shape — the same record with the block nulled — and compares it with and without the
exclusion: **13 of 683 values differ without it and 0 of 670 with it**. That count is exactly what
the exclusion hides, and it is recovered anyway wherever both sides carry the field.

### 5.2 G8 — 17 names, all kept

*Caption: gate G8's exclusions by kind, measured over its 12 run pairs. This gate's two sides are the
**same code at the same commit** run twice with one setting changed, so almost nothing is licensed to
differ and the set is small for that reason.*

| kind | names | verdict |
|---|---|---|
| a path | 1 | KEPT |
| a timing or the machine's state | 7 | KEPT |
| the working tree's state | 2 | KEPT |
| the setting being varied, or a stamp of it | 6 | KEPT — this gate varies exactly this setting, so a stamp of it must differ |
| prose, identical on both sides | 1 | KEPT |

**Sizes: 17 before, 17 after.** None is a "field a change adds", because there is no change between
the two sides — which is precisely why the set is 17 against G1's 70 and why the same review reaches
a different answer.

### 5.3 G9 — a list of what it compares, and one deliberate absence

G9's list is the other shape: nine fields it *does* compare on the arms that keep the output-time
loop, against the reproduction gate's own records, so that "nothing changes on `BR`/`B0`" is a
comparison and not an assertion. One field is deliberately **absent** from it:
`exit_audit.residual_max_hex`, because the same change moved the audit position for **every** arm,
so the residual is expected to differ and comparing it would test the audit rather than the output
path. Reviewed and kept absent — and the audit *position* is compared instead, on every row.

**Sizes: 9 compared, 1 deliberately absent, unchanged by this review.**

---

## 6. What the gates measured beyond passing

### 6.1 Self-containment, measured rather than asserted

The binding requirement (harness plan §6): every verification gate is implemented inside `harness/`,
with nothing imported from and nothing invoked as a subprocess into `arch_surgery/idf_probe/` or
`arch_surgery/fixedpoint/`.

`--measure self_containment` *is* the grep, executed and classified.

*Caption: every line of the package and the runner beside it naming either directory. Population:
30 Python files. "Prose" is a docstring or a comment; "executable" is everything else. A row the
stage cannot account for is printed as a finding.*

| | count |
|---|---|
| files scanned | 30 |
| lines naming `idf_probe` or `fixedpoint` | 44 |
| — inside a docstring or a comment (heritage) | 31 |
| — executable code | 13 |
| **imports of either directory** | **0** |
| **unclassified (findings)** | **0** |

The thirteen executable lines, every one classified:

| what | count | why it is not a hit on the requirement |
|---|---|---|
| the **driver's own** census probe, `process/core/_idf_probe*.py`, inside the copied PROCESS tree | 3 | the same three letters, a different module entirely. Told apart by the leading underscore, and said so in the stage |
| this stage's own declaration — the names it searches for and the prose explaining each classification | 5 | a measurement that looks for a string has to contain the string |
| `config.py`'s preflight-only campaign input directory | 1 | a path constant in `repository_tree_campaign()`. **No record is ever made against it**: `is_experiment_copy` is False and `pool.run` refuses every run on that ground, with a tooth |
| `data_provenance.py`'s two declared **source** paths | 2 | provenance strings. The data check fetches the source from the recorded commit with `git cat-file` — the repository at a commit, never the live directory (trap T9) |
| `input_files.py`'s refusal message | 1 | a sentence saying where the previous revision's derived files were, so a reader knows what to point `--lifted-from` at |
| `ystate.py`'s artifact stamp | 1 | a provenance stamp written **into** a generated artifact, naming the generator. Data written out, not a path read in |

**The named exception the plan allows** — the opt-in, labelled cross-check of the previous revision's
composition (`--crosscheck-previous`) — names `MDA_partitioning_experiment_v3`, not either forbidden
directory. It is off by default, is not one of the package's gates, and exists so the transcription
in this package is measured rather than trusted. `reference.py`'s default records root is likewise
that directory, read only by the reproduction reference's `extract` and `verify` stages, never at run
time.

### 6.2 The V3-inherited criteria, and where they agree

*Caption: one row per criterion this task inherited from a V3-era gate. "Agreement" is a **gate
result**, measured at this commit, not an assumed equivalence.*

| criterion | inherited from | agreement measured here |
|---|---|---|
| prime inertness after call 1, N/N components | G2 | 5 026 / 5 026 identical; the 1-ULP tooth lands on the same component and the same two hex literals |
| the cold chain's prime-off count | G3 | **244 / 244**, **124 / 124** |
| `low_aspect_ratio_DEMO`'s carrier census figures | G3c | **240 / 240** cold, **218 / 218** displaced; the open term CLOSES |
| every residual maximum, prime on and off | G3 / G3c | 8 of 8 hex literals identical |
| the restricted audit's blindness and sight | G4 | 12 of 12 doctored runs; every derived namespace |
| `norm_objf` hex / `n_call_models` comparator teeth | G5 | both trip |
| warm equivalence: clean **and** cross-state max < τ | G6 | 5 of 5 warm runs |
| the five forensics fields refused by name | G7 | 5 of 5, each naming its field |
| twenty records reproduced | GR | 270 / 270 |

### 6.3 The restricted statistic now reaches the optimisation record

A57 (driver-output-path) §13 handed over three lines: `optimise.py` was never given the per-run
deferral artifact or the write census, so `exit_audit.restricted` was null on **every** optimisation
record and the number had to be recomputed from the committed residual vector afterwards.
`pool._command` now builds both arguments for the optimisation phase as it already did for the
evaluation phase, and passes the artifact stamped for the input file the job **actually reads** — the
lifted one where the optimiser owns the burn time — so the excluded set is derived from the run that
was made.

Measured: **26 of 26** optimisation records at the plan's declared audit position carry the
statistic. (Those 26 are records, not distinct design points: several gates run the same arm,
configuration and seed under their own roots, and each record is counted once.) Records at the
reproduction gate's position (`after_run`, which only that gate may ask for) are listed and **not**
counted — the two positions never share a column unlabelled.

### 6.4 `tfcoil.insstrain` — improvement item 11, now on the reference arm too

*Caption: the restricted exit-audit maximum at the accepted point, at the plan's declared audit
position, one row per distinct (arm, configuration) the gates ran at seed 0. "Above τ" counts
restricted components at or above τ = 1e-6. Excluded / kept are the restricted statistic's own
denominators.*

| arm | configuration | restricted max | argmax | above τ | excluded | kept |
|---|---|---|---|---|---|---|
| `BR` | `large_tokamak_nof` | 6.991e-03 | **`tfcoil.insstrain`** | 1 | 122 | 696 |
| `B0` | `large_tokamak_nof` | 6.991e-03 | **`tfcoil.insstrain`** | 1 | 122 | 696 |
| `B1` | `large_tokamak_nof` | 7.119e-03 | **`tfcoil.insstrain`** | 1 | 122 | 696 |
| `B3` | `large_tokamak_nof` | 7.119e-03 | **`tfcoil.insstrain`** | 1 | 122 | 696 |
| `BR` | `low_aspect_ratio_DEMO` | 7.021e-03 | **`tfcoil.insstrain`** | 1 | 123 | 701 |
| `B0` | `low_aspect_ratio_DEMO` | 7.021e-03 | **`tfcoil.insstrain`** | 1 | 123 | 701 |
| `B1` | `low_aspect_ratio_DEMO` | 7.021e-03 | **`tfcoil.insstrain`** | 1 | 123 | 701 |
| `B3` | `low_aspect_ratio_DEMO` | 7.021e-03 | **`tfcoil.insstrain`** | 1 | 123 | 701 |
| `BR` | `st_regression` | 4.894e-14 | `physics.f_beta_alpha_beam_thermal` | 0 | 123 | 682 |
| `B0` | `st_regression` | 4.930e-14 | `physics.f_beta_alpha_beam_thermal` | 0 | 123 | 682 |
| `B3` | `st_regression` | 1.604e-11 | `fwbs.p_cp_shield_nuclear_heat_mw` | 0 | 123 | 682 |

**What is new here.** A57 measured this on `B1` and `B3` and concluded it is a property of the
handed-over state rather than of the partition, because the flat and the partitioned arm agree. This
task measures it on **`BR`, PROCESS as shipped**, and on `B0` — and the reference arm shows it too,
at 6.991e-03 on `large_tokamak_nof` and 7.021e-03 on `low_aspect_ratio_DEMO`. The component is above
τ at the accepted point of **upstream's own driver**, with no architecture switch set. That makes the
"property of the handed-over state" reading much harder to argue with, and makes it a statement
about PROCESS rather than about this experiment.

**It is named and not averaged away**, which is what the queue asked of this gate. What it *is* —
a genuinely unconverged coupling, a measured scale too small on the frozen ruler, or a discontinuity
in the TF-coil insulation-strain model at the accepted point — is still **not diagnosed**, and the
decision in improvement item 11 (diagnose before the campaign, or let the campaign measure it) is
still the user's.

---

## 7. The runs this task made

*Caption: PROCESS runs started through `harness/pool.py`, counted from the records on disk after the
from-scratch run — so this is what one press of `--gate all --measure all` costs, not a total over
the task's development. Every run is a fresh subprocess in its own working directory with `PYTHONPATH` naming
the experiment's own copy of PROCESS, and asserts the exact tree it imported before doing any work.
Wall clock is the sum of the children's own timings and is **context, never evidence** (I-10:
identical work has varied by up to 35 % in CPU-seconds on this machine). The six runs of gate G1's
"before" capture were made by the orchestrator at trunk in the main checkout and are counted
separately, because they are the one artifact here that cannot be re-made in this tree.*

| | count |
|---|---|
| evaluation-phase runs (one `call_models` each) | 106 |
| optimisation-phase runs | 46 |
| census runs | 6 |
| **total records on disk, made in this worktree at `5aa83db9`** | **158** |
| gate G1's "before" capture, made at trunk in the main checkout | 6 (3 optimisations, 3 evaluations) |
| of which stamped `campaign_run_kind = gate` | 156 |
| of which stamped `smoke` | 2 |
| of which stamped `force_maxcal` (demonstrations, never a population) | 1 |
| summed in-child wall clock, all runs | ≈ 2 340 s (≈ 39 min), at 3 workers — context only |

No record made by this task is a campaign record; `EXECUTION_APPROVED` is still `False` and every
campaign stage refuses.

---

## 8. How to re-run everything

```bash
PY=/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python
cd arch_surgery/MDA_partitioning_experiment_v4

$PY experiment_runner.py                       # preflight: READY
$PY experiment_runner.py --gates               # what exists and what each binds
$PY experiment_runner.py --selfcheck           # the six promoted self-checks, with teeth
$PY experiment_runner.py --artifacts all --census-entry evaluation
$PY experiment_runner.py --gate all --census-entry evaluation   # every run re-made
$PY experiment_runner.py --gate all --resume --census-entry evaluation   # keep what matches
$PY experiment_runner.py --measure all
$PY PROCESS/copy_gates.py all                  # the copy is still the copy
$PY PROCESS_diff.py                            # seven changed files, none unexplained
```

Gate G1 alone is two steps, and a genuine run of it needs two commits:

```bash
# in a tree at the commit BEFORE the change — the main checkout at trunk, say
$PY experiment_runner.py --gate switch_neutrality --capture before
# then in the tree at the commit after it
$PY experiment_runner.py --gate switch_neutrality --capture after
$PY experiment_runner.py --gate switch_neutrality                    # compare, with teeth
```

`--gate all` makes a "before" capture only if there is **none**, and never re-makes one: a capture
from an earlier commit was written by an earlier record schema, and resume judges it against the
current one (§4.3). Move a "before" capture into place by copying the directory, not by re-running
it.

**To run the gates from nothing**, which is what the figures in this report are:

```bash
cd arch_surgery/MDA_partitioning_experiment_v4
# keep the one artifact that cannot be re-made, and delete the rest
mv runs/gates/switch_neutrality/before /somewhere/safe
rm -rf runs/gates
mkdir -p runs/gates/switch_neutrality && cp -r /somewhere/safe runs/gates/switch_neutrality/before
cd ../.. && $PY arch_surgery/MDA_partitioning_experiment_v4/experiment_runner.py \
    --gate all --census-entry evaluation      # no --resume: every run is made again
```

The reproduction gate reads the committed reference and needs the lifted input files, which
`--gate artifacts_derive_inputs` produces; if they are wanted from the previous revision's own
directory instead, `--gate reproduction --lifted-from <dir>` stages them after checking their bytes
against the recorded digests.

**Exit codes:** 0 everything passed · 1 a gate failed · 2 refused to start (wrong interpreter) · 3
refused (a missing prerequisite, an unknown gate name, or a failed stage).

---

## 9. Autonomous decisions, each with its reversal

*Caption: one row per decision this task took without asking, what it costs, and how to undo it.*

| # | decision | why | reversal |
|---|---|---|---|
| 1 | `Gate`, `Tooth`, `Check` and `Measurement` live in a new `harness/framework.py`; `gates.py` re-exports the first two | the self-check and the artifact stages need `Check` and cannot import `gates.py` without a cycle. A framework that depends on what it frames cannot be imported by all of it | move the four back into `gates.py` and give the two importers a lazy import — about ten lines, and the cycle comes back |
| 2 | a promoted check declares its tooth **names**, and an undeclared tooth fails the gate | a promotion that copied whatever teeth the check ran would be a declaration that cannot fail | drop the declared list and count the teeth instead; the gate then cannot notice a tooth that disappeared |
| 3 | the five new gates live in five modules (`gate_prime`, `gate_audit`, `gate_composition`, `gate_entry`, `gate_records`) rather than in `gates.py` | `gates.py` is already 4 000 lines; a gate per file is reviewable | merge them back; `registry` imports them lazily, so the import graph does not change |
| 4 | `registry(campaign)` holds gates **and** measurements, with `gates_only()` filtering | a reader looking for "what does this package run?" should find one answer, and the queue asked for one registry listing both | split into two functions; every caller then has to know which group a name is in |
| 5 | the cold-chain gate runs **two compositions** rather than choosing one | this revision's arm and the previous revision's chain differ by one switch, and on the whole-state audit that is not a comparable measurement. Choosing either alone would have hidden something | run only the arm as composed and report the previous revision's figures as not reproducible — which would be true and much weaker |
| 6 | G3c's carrier **coefficients** are not reproduced; its verdict is | the coefficients were read from a per-pass residual trace the V4 plan drops from composition | implement a trace parser and run the trace instrument; the plan would need amending first, since it says nothing V4 publishes reads it |
| 7 | G1's change-added exclusions are made **conditional** rather than deleted | deleting them would break a future G1 that legitimately straddles an older commit; keeping them unconditional hides leaves for ever — 416 over this task's straddle | pass `conditional=None` in `neutrality_body`; the gate then compares 416 fewer values |
| 8 | G8 and G9 make their own runs with resume, instead of a separate capture command | a stage that exists only as a shell invocation is not reproducible (protocol §15), and both sides are the same commit | wrap their bodies back to the comparison alone; `python -m harness.gates <name> --capture runs` still works |
| 9 | `--outdir` redirects a gate's **verdict** but not the gates' runs | one gate reads another's runs; moving them to relocate a small JSON would break that | pass the root through as well and give the output-path gate a second option for where to look |
| 10 | the **experiment plan's §4.1 table is not edited** | that file is not on this task's owned list and the plan's amendments are the orchestrator's | §3's table and `--measure gate_table` are ready to paste |
| 11 | the G4 namespaces come from the **run-time** census, taken with resume | the committed census records what a node writes; the crawl needs what a node ran, and the difference is a whole namespace on the steady-state configuration | pass the committed census; `pulse` silently leaves the set |
| 12 | the G7 configuration is chosen as the one with the fewest iteration variables, **derived** | a gate that named a configuration would need editing when the configuration list changes, and the list is allowed to change by a recorded decision | name it |
| 13 | the probe and cross-check children run with `-P` **and** `PYTHONSAFEPATH=1` | either alone would do; together they cover a child started some other way, and neither costs anything. `-I` would be wrong — it drops `PYTHONPATH`, which is the one thing these children need | drop one or both; the decoy tooth then fails, which is the point |
| 14 | the nine cross-tree names go in **always-excluded**, not in the conditional group | they are a path or the working tree's state: no pair of captures could compare them, whether or not a change added them | move them; a two-tree straddle then fails on locations |
| 15 | the two per-ruler counts are conditional on a **witness** rather than on their own leaf | a `0` that means "not computed" cannot be told from a `0` that means "excluded nothing" by looking at it | exclude them unconditionally; the gate then stops comparing a count that is worth comparing, and the new tooth fails |
| 16 | `--gate all` makes a "before" capture when there is none, and the verdict labels it | a button that refuses on a fresh tree is not a button; a PASS that reads like a neutrality verdict when it is not is worse | refuse instead, and require the two captures to be made by hand |
| 17 | the shared cold-flat reference evaluations are made **once per invocation** and shared, through a per-process memo | three gates are anchored on them; without the memo the second and third gate of one `--gate all` would re-make what the first had just made, and the three would be anchored on three different fixed points | drop the memo and let each gate make its own; the cost is nine evaluations instead of three, and the gates stop sharing an anchor |
| 18 | a verdict **fails** when it read runs from another commit and `--resume` was not asked for | that is exactly the defect this fixes: the flag must mean something, and a gate that silently reads stale runs reports a zero over a population that is not the one it names | make it a note instead of a failure; the button then cannot tell a fresh run from a resumed one |
| 19 | the `--gate all` order is **derived** from declared `reads_from` dependencies, with `GATE_ORDER` as a preference | cheapest-first is a preference, not a correctness order, and treating it as one hid a real dependency until the first from-scratch run | hand-sort `GATE_ORDER` and drop `reads_from`; the order is then correct only as long as nobody edits it |

---

## 10. Handover

### To the orchestrator

- **The experiment plan's §4.1 table** can be filled from §3 above, or regenerated with
  `experiment_runner.py --measure gate_table`, which also emits it as markdown. This task did not
  edit the plan.
- **Gate G1 now straddles trunk `5e64ce0e` → this branch, across two trees**, using the "before"
  capture you made. It PASSES 0 of 3 164 values and 0 of 51 319 lines with 714 values excluded. The
  capture is kept and was never handed to resume — and the reason matters: because this task
  declared `per_run_artifact`, resume judges that capture's *optimisation* records incomplete and
  would re-run them. Anyone moving a "before" capture between trees should copy the directory, not
  re-run the stage.
- **The same-commit capture is kept beside it** as `before_same_commit/` and is not read by anything;
  delete it whenever you like.
- **`tfcoil.insstrain` is above τ on `BR`, PROCESS as shipped** (§6.4), not only on the intervention
  arms. That strengthens improvement item 11 and is a statement about PROCESS rather than about this
  experiment. The user's decision on it is still open.
- **The brief's attribution of "244 / 124 on `lad`" is wrong** (§4.5) and is corrected here from the
  previous revision's own records: 244 is `large_tokamak_nof`, 124 is `st_regression`, and
  `low_aspect_ratio_DEMO`'s figures are 240 and 218. Worth correcting in the queue row so it is not
  transcribed again.

### To A53 (harness-tally)

- **Gate records it reads.** `runs/gates/<name>/gate.json` for every gate; in particular
  `reproduction/gate.json` (the twenty reference runs, whose verdict now nests the stage's own under
  `reproduction`), `audit_restriction/gate.json` (the restricted statistic's denominators — excluded
  and kept per configuration — and the argmax by component), `predicate_mode/gate.json` (both
  rulers' audits and the two decisive-pass counts), `attempts/measurements.json` and
  `predicate_counters/measurements.json`.
- **`exit_audit.restricted` is now on optimisation records**, derived by the same code in both
  phases and from the artifact stamped for the input file the run actually read. A residual caption
  must still state the audit position: campaign records are at `entry_to_write_output_files`, the
  reproduction gate's at `after_run`, and the two must never share a table unlabelled.
- **`tfcoil.insstrain` will dominate the restricted statistic on both pulsed configurations, on
  every arm including the reference one.** It must be named in the table, not averaged into a
  maximum.
- **`records.assert_attempt_summation` and `assert_both_rulers` are the contracts to call**, and G7
  shows them refusing. Records stamped `force_maxcal` must be filtered out of every population; one
  exists in `runs/gates/record_completeness/`.
- `gates.COUNT_FIELDS` is the list of (compared, differing) field pairs a verdict can carry, if the
  tally wants to read gate denominators uniformly.

### To A54 (harness-analysis)

- `framework.gate_from_check` is the pattern for promoting a criterion without restating it, if the
  analysis wants its own checks in the same registry.
- `--measure` is where a stage with no verdict belongs; `analysis.py --verify` is a gate and belongs
  under `--gate` with teeth.

### To A55 (harness-smoke)

- **The one-button chain is** `--gate all --resume --census-entry evaluation`, then `--measure all`.
  Both return 0 at this commit. `--gate all` runs cheapest first and stops at the first failure.
- `--artifacts all --census-entry evaluation` passes and takes seconds per configuration.
- The smoke chain can reuse the gates' runs: everything under `runs/gates/` is resume-compatible,
  and `pool.run` checks the job matches before keeping a record.

---

## 11. Limits of what is reported here

- **G1's straddle covers a *harness* change, not a driver change** (§4.3). The driver chain closed
  at A60 (driver-attempts) and this task edits no driver file, so what the gate shows is that the
  harness change between trunk and here moved no measured value — which is the strongest claim
  available at this commit, and not the same claim as "a driver change is inert".
- **The leaf counts in §5.1 hold for one pairing.** 416 over this straddle, 1 040 over a same-commit
  pairing; the review names the pairing it measured and the number does not travel without it.
- **A verdict's staleness check is about the tree's HEAD, not about the code.** It compares the
  commit a record was stamped with against the commit the verdict was written at. Those differ
  whenever HEAD moves during a run — which is a real hazard (§13.1) and also means the check would
  flag records that are perfectly good if a documentation-only commit landed mid-run. It is the
  right check to have; it is not a statement that the *code* changed.
- **The 26 optimisation records carrying the restricted statistic are records, not design points**
  (§6.3): several gates run the same arm, configuration and seed under their own roots.
- **G3c's carrier coefficients are not reproduced** (§4.5), by decision 6. The claim the gate binds
  — no cut edge carries anything — is reproduced in full.
- **The outer-pass half of G3 has nothing to count at this commit** (§4.5), because DR1 removed the
  loop it counted. This is a coverage boundary, stated in the gate's own record.
- **`pulse` on `st_regression` is an excluded namespace that excludes nothing** (§4.6). Its
  certification is a recorded zero, not a doctored component.
- **Every timing in §7 is context.** No verdict in this report rests on one; every acceptance
  quantity is a count or a bit-comparison.
- **The gate populations are what the gates ran, not what the campaign will run.** A gate at seed 0
  and seed 1 says nothing about seed 17.

---

## 12. Change log

- **2026-09-11** — written by task **A52 (harness-gates)** at branch `A52-harness-gates`, base
  `5e64ce0e`. Commits: `3347169c` (the framework, the promotion, the registry, the runner wiring,
  the restricted statistic on optimisation records), `b1d56fc7` (G2, G3/G3c, G4), `acdeb450`
  (G5, G6), `9d4d04ab` (GR, G1, G8, G9 wired and run), `6a2b49d0` (the exclusion review and the
  self-containment measurement), `fe9284f1` (the gate table), `8c70f01c` (the README), `36bc2a08`
  (the output-path measurement's own contrast runs).
- **2026-09-11, revised** after the orchestrator's first review (§13): `3f50d9b5` (five defects),
  `41194bef` (the exclusion review names its pairing).
- **2026-09-11, revised again** after the second (§13, defects 6 and 6a): `c5bcf662` (`--resume`
  threaded into the gates' runs; the runs a verdict read, surveyed), `eb251624` (the gate order
  derived from declared dependencies), `5aa83db9` (README and report). **Every number in this
  report comes from one from-scratch press of `--gate all` at `5aa83db9`** — `runs/gates/` deleted
  but for gate G1's trunk capture, no `--resume`, nothing committed while it ran — followed by
  `--measure all`, `--selfcheck`, `--artifacts all`, the preflight, `copy_gates.py all` and
  `PROCESS_diff.py`, all returning 0. The figures that moved across the two revisions are in §13.

---

## 13. The orchestrator's review, and what it changed

The orchestrator reproduced every number in the first version of this report independently and
found **six** defects across two rounds; a seventh surfaced only when the sixth's fix made a
from-scratch run possible. All are fixed on this branch, and the figures in this report come from a
run of every gate **from nothing** — `runs/gates/` deleted but for gate G1's trunk capture, which
cannot be re-made — with no `--resume`.

The sixth is the one worth reading twice. Every gate body hard-coded `resume=True`, so `--gate all`
without the flag re-made nothing and a verdict computed after a change silently read runs made
before it. The gates had been passing on runs at five different commits. It is trap T11 one level
up: not a count over a population smaller than the one named, but a *verdict* over runs other than
the ones named — and the flag that was supposed to control it reached nothing but gate GR.

*Caption: one row per defect, what it was, and what it now does. "Found by" says how it surfaced —
three of the five were invisible to the way this task had been running the gates.*

| # | defect | found by | fix | now |
|---|---|---|---|---|
| 1 | the capability probe's verdict depended on the working directory: with `-c`, Python puts the cwd ahead of `PYTHONPATH`, so pressing the button from the repository root imported the repository's `process/` instead of the copy — 25 of 54 mismatched | pressing the button from the worktree root | `-P` and `PYTHONSAFEPATH=1` on the probe child and on the cross-check child | PASS from both directories; a new tooth runs the probe from a scratch tree holding a decoy `process/__init__.py` and it still imports the copy |
| 2 | a genuine two-tree straddle of G1 failed on 42 of 3 206 values: 36 cross-tree paths and tree state that no exclusion named, and 6 leaves that are the record change itself | the orchestrator making the real "before" capture at trunk | nine structural names into always-excluded; two counts made conditional on a **witness** | G1 PASS: 0 of 3 164 values, 0 of 51 319 lines, 714 excluded (§4.3) |
| 3 | the load-bearing tooth took its sample from the "before" side, which at trunk carries no restricted block, so it could not be built in the one run where it matters | the straddle, where it DID NOT TRIP | the sampler takes the side that carries the block | TRIPPED in the straddle: 13 of 683 values differ without the exclusion, 0 of 670 with it |
| 4 | a same-commit G1 PASS read like a neutrality verdict in the plan's gate table | review | `_straddle` reads both manifests and prefixes the population, the verdict and the table row | the row now opens "straddles `5e64ce0e` → `5aa83db9`: a neutrality result", or says both captures are at one commit and what that does and does not show |
| 5 | `per_run_artifact` was written on both phases' records and declared in neither | review | declared `("AB", "always")` in `records.SCHEMA` | G7 covers it: 85 declared fields in the optimisation phase, 78 in the evaluation phase |
| 6 | `--gate all` without `--resume` re-made nothing: every gate body hard-coded `resume=True` in sixteen places and the runner's flag reached gate GR and `--run` only, so a verdict computed after a change silently read runs made before it | the orchestrator surveying `tree_git_head` on every record under `runs/gates/` after pressing the button with no flag — runs at five different commits, only GR's re-made | `resume` threaded from the runner through `Gate.run` and `Measurement.run` into every body, every `pool.run_all`, every capture and `entry_references`; `Gate.runs_under` and `framework.survey_heads` put the commits of the records a gate read into its verdict | every run at the new commit; a verdict that reads records from another commit says so, and fails when `--resume` was not asked for. A tooth stales one record and shows it kept with the flag and re-made without it |
| 6a | the `--gate all` order was hand-sorted cheapest-first, and gate G9 reads gate GR's own records — so from nothing, G9 refused for want of records that were about to be made | the from-scratch run, on its first attempt | `Gate.reads_from` declares the dependency and `ordered_gate_names` derives the order, with cheapest-first as the preference between gates that do not depend on each other | GR and the two gates that read it run in that order; an unknown dependency or a cycle raises |

### 13.1 What the new check caught on its first outing, and it was mine

The first from-scratch run under the fixed code **failed on the last gate**, and the cause was not
the gate: I committed the README and this report *while the run was executing*. A run record stamps
`tree_git_head` at the moment its child process starts, so the fifteen records made before the
commit carry `eb251624` and the twelve made after it carry `5aa83db9` — and the verdict, written
last, carries `5aa83db9` too. The gate's own criterion passed completely (12/12 pairs bit-identical,
0 of 7 606 record values and 0 of 84 output-file lines differing, all three parts); it failed
because the staleness check saw records at two commits with no `--resume` asked for, which is
exactly what it is for.

Two things follow, and both are worth more than the inconvenience.

**The check works, and it caught something no count would have.** Every per-gate number in that run
was right. A reader looking only at populations and mismatches would have seen a clean sweep and had
no way to know the tree had moved underneath it.

**The discipline it implies reaches the campaign.** The stamp is taken per child, not per stage, so
*any* commit made while runs are in flight splits a population across two commits. Phase B is 275
optimisations over hours; a single commit in the middle of it would leave the tally reading records
that name two different trees, and nothing in the tally would have to notice. The rule is simple and
was not written down before: **do not commit while measurement runs are executing.** The run was
re-made from nothing with nothing committed during it, and that is the run this report's figures
come from.

*Caption: the figures that moved across the two revisions of this report, and why. Everything not
listed is unchanged.*

| figure | before review | after | why |
|---|---|---|---|
| teeth, total | 106 | **108** | the decoy-package tooth and the witness tooth |
| capability: compared / teeth | 54 / 14 | **55 / 15** | the decoy check and its tooth |
| G7: compared | 161 | **163** | `per_run_artifact` declared in both phases |
| G1: compared / excluded / teeth | 2 289 / 546 / 5 | **3 164 / 714 / 6** | a different and harder pairing — two commits and two trees — with eleven more names in the set |
| G1: what it straddles | one commit | **`5e64ce0e` → `3f50d9b5`** | the orchestrator's trunk capture |
| exclusion set: names | 59 | **70** | 9 cross-tree structural names, 2 witness-conditioned counts |
| exclusion set: always / conditional | 27 / 32 | **36 / 34** | the same |
| leaves recovered by the condition | 1 040 | **416** | measured over a different pairing; both are right for their pair, which is why the review now names it |
| G7: teeth | 8/8 | **9/9** | the stale-run tooth |
| teeth, total | 108 | **109** | the same |
| PROCESS runs made | 166 | **158** in this worktree at one commit, + 6 at trunk | the figures now come from one from-scratch press rather than accumulating across development |
| what the runs are | whatever survived from earlier presses, at five commits | **all 144 gate records at one commit** | `--resume` reaches the runs |

**One thing the review did not change, and it is worth saying.** The promotion's rule that *an
undeclared tooth fails the gate* caught the new decoy tooth the moment it was added: the capability
gate went FAIL with `undeclared_teeth: ['the working directory holds a package that shadows the
tree']` until the name was declared. The mechanism designed to stop a check's declaration drifting
from the check did exactly that, on its first real opportunity.

---

## 14. Orchestrator's critical assessment (protocol §5)

*Written by the orchestrating session on 2026-09-11 after the review round of §13, before the merge. Every number below was re-derived by the orchestrator from its own runs on this branch, not copied from the sections above; where a figure agrees with the agent's it is said to agree, and where the orchestrator's run differs it is the orchestrator's that is quoted.*

### 14.1 What was verified independently, and how

**First version (919491ec).** `--gate all` pressed from `arch_surgery/MDA_partitioning_experiment_v4/`: 21 PASS, 0 FAIL, every per-gate `n_compared` / `n_mismatched` / teeth count identical to the agent's saved verdict records, GR 20/20 runs and 270/270 values from scratch. `--selfcheck` PASS, preflight READY, `copy_gates.py all` PASS, `PROCESS_diff.py` exit 0 with the same seven driver files, merge dry-run against trunk clean, nothing under `…_v4/PROCESS/`, root `process/`, the plans, `harness/data/` or `harness/reference/` changed.

Two further checks the task had not made found the defects of §13:

- **The same button pressed from the repository root** stopped at `capability` with 25 of 54 mismatched: six pairs named the wrong tree honestly (`the probe imported …/A52-harness-gates/process/__init__.py, which is not the tree under test`), nineteen were refusals under the root driver's retired names, and two teeth did not trip. The verdict was honest and the diagnosis correct per pair; what was wrong is that a verdict depended on the working directory. (Defect 1.)
- **A genuine G1 straddle.** The orchestrator made the "before" capture at trunk `5e64ce0e` in the main checkout (`python -m harness.gates switch-neutrality --capture before`, six runs, untracked under that checkout's `runs/`) and placed it in the worktree beside the task's same-commit capture. Compared: FAIL on 42 of 3 206 values, 0 of 51 319 lines — 36 cross-tree paths and tree state no exclusion named, 6 leaves that were the record change itself (`n_excluded_from_the_restricted_statistic`, 0 → 122/123 on the optimisation records), and the fifth tooth unable to build its sample. (Defects 2, 3.) The same-commit run could see none of this, and its PASS read as a neutrality verdict in the gate table. (Defect 4.)

**Second version (0b443b15).** `--gate all --census-entry evaluation` pressed from the **repository root** with no `--resume`: 21 PASS, 108/108 teeth, exit 0; capability 55 compared, 0 mismatched, 15/15 teeth; G1 straddling `5e64ce0e → 3f50d9b5`, 0 of 3 164 values, 0 of 51 319 lines, 6/6 teeth; GR 20/20 runs, 270/270 values, 7/7 teeth. `--selfcheck` PASS, preflight READY.

But a survey of `tree_git_head` on every `metrics.json` under `runs/gates/` showed that this run had **re-made only GR's runs**: the other gates' runs were still those the agent had made at five earlier commits of the branch (`3347169c`, `b1d56fc7`, `acdeb450`, `8c70f01c`, `3f50d9b5`), because `resume=True` was hard-coded in sixteen places in the gate modules and the runner's `--resume` reached GR and `--run` only. A verdict computed after a change was silently reading runs made before it, and the orchestrator's own "from scratch" for the chain had been true of GR and of the comparisons, not of the runs. (Defect 6, §13.) The records were in substance current — every one postdates the task's only run-path change, at `3347169c` — but that is a fact about this branch's history, not a property of the button.

**Third version (eb38c34a; code as at 5aa83db9).** With `resume` threaded through every gate body: `runs/gates/` emptied except the trunk capture, `--gate all --census-entry evaluation` pressed from the repository root with no `--resume`, nothing committed in the worktree while it ran: exit 0, 21 PASS, 0 FAIL, 109/109 teeth, every verdict's `n_compared` / `n_mismatched` / teeth identical to the agent's own from-scratch press at 5aa83db9. Run-stamp survey: 150 records, 144 at `eb38c34a` and 6 at `5e64ce0e` (the trunk capture), every gate's `runs read` line at this commit. G1 straddles `5e64ce0e → eb38c34a`: 0 of 3 164 values, 714 excluded, 0 of 51 319 lines, 6/6 teeth. GR 20/20 runs, 270/270 values, 7/7 teeth. Then `--measure all` exit 0 (six stages), `--selfcheck` 6 PASS, `--artifacts all --census-entry evaluation` exit 0, preflight READY, `copy_gates.py all` PASS, `PROCESS_diff.py` exit 0 with the same seven driver files as at the branch's base, merge dry-run against trunk clean. Working tree clean; the branch touches sixteen files, all under `harness/`, the runner and the report.

**On the method of this verification.** The three full presses (about forty minutes each) reproduced the agent's counts and found nothing by themselves; every defect above came from a check that differed from the agent's — another working directory, a real earlier commit in another tree, a survey of the run stamps. The user pointed this out during the review; from here the orchestrator's review is scope, code reading, the agent's verdict records with their run stamps, and targeted checks the agent did not make, with one GR at a merged tip after a run-path change rather than a repeat per task.

**Insstrain on the reference arm, from the orchestrator's own records.** Restricted exit-audit maximum at the declared audit position, seed 0, argmax `tfcoil.insstrain` in every pulsed row: `BR` 6.991e-3 / 7.021e-3, `B0` 6.991e-3 / 7.021e-3, `B1` 7.119e-3 / 7.021e-3, `B3` 7.119e-3 / 7.021e-3 (`large_tokamak_nof` / `low_aspect_ratio_DEMO`); `st_regression` at 4.9e-14 (`BR`, `B0`) and 1.6e-11 (`B3`) with nothing above τ. §6.4's table is confirmed line for line.

### 14.2 Judgements

1. **The task is accepted.** The claim structure holds: every gate of the plan exists inside `harness/`, each with a population, a denominator and teeth that trip; the promoted checks kept their numbers; the six new gates reproduce the inherited criteria exactly (244 / 240 / 218 / 124 and eight hex maxima). The defects were all in two places the task could not have reached from inside its own worktree — the button's working directory and G1's pairing — and both are now gated rather than assumed.
2. **The agent's correction of the brief stands.** A35's own report (§6, lines 293–294 of `A35_cold_census.md`) puts 244 on `large_tokamak_nof` and 124 on `st_regression`; "on lad" was the orchestrator's transcription error in the queue row, not the plan's data. The queue row and the plan's §3.9 tooth cell are corrected at this merge.
3. **The G1 straddle here binds a harness change, not a driver change.** That is stated in §4.3 and the orchestrator keeps it in view: what the 0 of 3 164 shows is that handing the optimisation phase the per-run artifact moved nothing in the driver's behaviour and that every leaf the two-tree pairing cannot compare is now named. The next *driver* change, should there ever be one, still owes its own before capture at its own earlier commit — the gate no longer makes one for it (it makes a before only when none exists), and the harness plan gains that rule.
4. **The exclusion set's leaf counts are a property of the pairing.** 1 040 recovered leaves over a same-commit pairing, 416 over the two-tree straddle; both are correct and the review now prints which pairing it measured. Any future citation of "leaves recovered" must carry the pairing.
5. **`tfcoil.insstrain` is a statement about PROCESS as shipped**, above τ on `BR` with every switch unset at 6.99e-3 and 7.02e-3, identical to `B0` on the same seed. The user asked why `B0` is then not converged, and **A61 (insstrain-diagnosis)** was dispatched in parallel; its report arrived as this assessment was being finished and classifies the residual as an artefact of the exit-audit instrument — PROCESS's output path raises `tfcoil.n_rad_per_layer` from 100 to 500 before the snapshot, the field is not a coupling-state component and is not restored, and the audit's sweep therefore runs on a different grid than the loop did (0 of 840/846/827 components differ between the loop's last sweep and the audited state; restoring that one field gives exactly zero). That classification is verified at A61's merge, not here; §6.4's measurement stands as a measurement of the instrument as it was.
6. **Defect 6 and the rule it leaves.** `--resume` reaching only GR meant every earlier press of `--gate all` on this branch computed fresh verdicts over runs from up to five earlier commits, and nothing printed said so; the agent's fix makes a verdict name the commits of the runs it read and fail without `--resume` when they are not its own. Its first from-scratch press then failed on G8 because the agent committed the README mid-run — 15 records at one commit, 12 at another, the criterion itself passing. The rule that follows is binding on the campaign and is written into the harness plan at this merge: **do not commit while measurement runs are executing.** The gate order is now derived from declared dependencies (GR before G9 and G8), which only a from-scratch press could have exposed.
7. **`--outdir` redirects verdicts, not runs** (decision 9). Accepted: one gate reads another's runs. The orchestrator used it to keep the review's straddle and capability verdicts off the branch's records, which is exactly its purpose.

### 14.3 Consequences recorded at this merge

- **A53 (harness-tally)**: reads `runs/gates/<name>/gate.json` and the measurement records; `exit_audit.restricted` is populated on optimisation records at the declared position (26 records here, records not design points); `insstrain` is named in every restricted-statistic table, never averaged; records stamped `force_maxcal` are filtered out of every population; `gates.COUNT_FIELDS` is the uniform reader of gate denominators; the witness-conditioned comparison is the pattern for any count whose zero means "not computed".
- **A54 (harness-analysis)**: `framework.gate_from_check` promotes a criterion without restating it; `--verify` belongs under `--gate` with teeth; a stage with no verdict belongs under `--measure`.
- **A55 (harness-smoke)**: the one-button chain is `--gate all --resume --census-entry evaluation` then `--measure all`; the smoke presses it from **both** the repository root and the experiment directory and records both; on a fresh tree G1's verdict is labelled as a self-comparison and that label is expected, not a defect.
- **Experiment plan**: §4.1 filled from `--measure gate_table` at the orchestrator's press (eb38c34a); §3.9's G3 tooth cell corrected (244 nof / 124 st; 240 / 218 lad; the outer-pass half has nothing to count since DR1); change log.
- **Harness plan**: amendment 13 — H5 done; `--resume` reaches every run and a verdict names the commits of the runs it read; the G1 before-capture rule; the working-directory rule for every child that imports the copy; the derived gate order; no commit while runs execute.
- **Records**: this worktree's `runs/` is relocated by the retire script (path in the queue row); the trunk before capture also remains, untracked, under the main checkout's `arch_surgery/MDA_partitioning_experiment_v4/runs/gates/switch_neutrality/before/`.

### 14.4 Limits of this assessment

- The orchestrator's re-runs used the same code path as the agent's; independence is in the operator, the working directory and the pairing, not in a second implementation.
- No timing anywhere above is evidence; the runs were made under CPU contention with other gate runs and the wall clocks are not comparable even as context.
- Gate populations are seeds 0 and 1 and say nothing about the campaign's seed set.
