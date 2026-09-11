# A52 (harness-gates) — every verification gate inside the harness, in one framework, on one button

> **Document status** — **OPEN.** Task **A52 (harness-gates)**, branch `A52-harness-gates` off
> `architecture_surgery` at `5e64ce0e`. Delivers plan task **H5** of the approved V4 harness plan.
> Numbers in this report were taken at commit `36bc2a08`, the branch's last code commit; this
> report is the only thing committed after it. Folder position records lifecycle, not validity
> (trap T3).

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
106 of 106 teeth tripped**. `--measure all` runs six measurement stages and returns 0.
`--selfcheck` passes. `--artifacts all --census-entry evaluation` passes. The preflight is READY.

**Six gates that did not exist are built** — G2, G3/G3c, G4, G5, G6, G7 — each inside `harness/`,
each with its runs through the pool, its denominator and its teeth. Where a criterion is inherited
from the previous revision, the criterion is restated here and **its agreement with that revision's
recorded figures is a gate result**: the cold-chain gate reproduces 244 / 240 / 218 / 124 exactly
and every residual maximum to the bit.

**Nothing under `…_v4/PROCESS/` changed.** The diff of this branch against its base touches thirteen
files, all of them in `harness/` or the runner. `copy_gates.py all` passes; `PROCESS_diff.py` exits
0 with the same **seven** changed files and no unexplained hunk; G0′ passes with `pulse.py` as the
one approved difference.

**Three things were found by gates failing before they passed**, and all three are reported rather
than tuned away:

1. **The cold-chain gate cannot be a single comparison.** This revision's partitioned arm defers
   three nodes to once per run; the previous revision's chain did not. Read on the whole-state
   audit they are different measurements by construction — 112 components above τ with the prime
   on, every one owned by a deferred node. The gate now runs **both** compositions and reads each
   the way it must be read.
2. **A switch left unset and a switch set to its default compose different environments and the
   same arm.** The composition gate compares what the driver *resolved*, not only what the harness
   asked for, because of it.
3. **G1's exclusion set had stopped describing itself.** 32 of its 59 names were excluded because
   *one particular pair of commits* straddled the change that added a field; excluded
   unconditionally they went on hiding those fields for ever. Made conditional, they put **1 040
   leaves** back into the comparison — G1 compares 2 289 values before and **3 329** after, still 0
   differing.

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
| `--gate all` | run every gate, **cheapest first**, stopping at the first failure — so a repository-state failure is reported in seconds rather than after an hour of runs |
| `--measure <name>` / `--measure all` | run the measurement stages. Gates never run here and measurements never run under `--gate`: the two cannot be confused |
| `--no-teeth` | skip the teeth; the verdict records that it did, and a gate whose teeth were not run is not an accepted gate |
| `--capture before\|after` | gate G1 only (§4.3) |

**The `--outdir` quirk A57 (driver-output-path) recorded is fixed.** `--outdir` now redirects every
gate's *verdict*, which `--gate reproduction` previously ignored. It deliberately does **not**
redirect the gates' own runs: the output-path gate reads the reproduction gate's runs to show that
nothing about the solve changed on the arms that keep the output-time loop, and moving those runs
would break a cross-reference between two gates in order to relocate a small JSON file. That is
stated in the option's own help text.

Every gate makes its own runs, with `--resume` keeping a *complete record of the same job* rather
than re-making it — which is not a retry: `pool.run` checks that the job matches before it keeps
anything. Gate G1 is the one exception and §4.3 says why.

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
`36bc2a08`; records under `arch_surgery/MDA_partitioning_experiment_v4/runs/gates/`, which is
untracked by design.*

| gate | plan | verdict | population | compared | mismatched | teeth |
|---|---|---|---|---|---|---|
| `reproduction` | GR | **PASS** | 20 runs (14 optimisations + 6 evaluations) over 3 configurations; no tolerance on any value | 270 | 0 | 7/7 |
| `g0prime` | G0 / G0′ | **PASS** | 77 files under `PROCESS/process/models/` against `c0ae5b28` by `git cat-file`, plus the file set | 77 | 1 (approved) | 4/4 |
| `switch_neutrality` | G1 | **PASS** | 6 run pairs = 3 configurations × 2 reference arms; 3 329 record values + 51 319 output-file lines | 54 648 | 0 | 5/5 |
| `prime_map` | G2 | **PASS** | 6 arrangement/configuration pairs; 12 evaluations | 5 026 | 0 | 2/2 |
| `cold_chain` | G3 / G3c | **PASS** | 8 chain/composition pairs over 4 chains; 16 evaluations; 60 individual checks | 60 | 0 | 4/4 |
| `audit_restriction` | G4 | **PASS** | 13 doctored runs over 3 configurations, each against that configuration's undoctored run | 12 | 0 | 5/5 |
| `switch_composition` | G5 | **PASS** | 3 configurations; 6 optimisations; 37 switch names + 10 run values each | 141 | 0 | 3/3 |
| `entry_and_warm` | G6 | **PASS** | 5 entry pairs at seed 1; 5 warm runs; 13 evaluations | 4 204 | 0 | 3/3 |
| `record_completeness` | G7 | **PASS** | 2 runs on `st_regression`; 84 declared fields in the optimisation phase, 77 in the evaluation phase | 161 | 0 | 8/8 |
| `predicate_mode` | G8 | **PASS** | 12 pairs × 2 rulers = 24 runs; 7 600 record values + 84 output-file lines | 7 684 | 0 | 4/4 |
| `output_path` | G9 | **PASS** | 11 runs at seed 0; 3 825 coupling-state components + 54 solve-describing values | 3 879 | 0 | 4/4 |
| `composition` | — | **PASS** | 8 arms × 3 configurations = 24 pairs, compared by role | 42 | 0 | 7/7 |
| `rungs` | — | **PASS** | 11 matrix rows × 8 arms = 88 cells; 6 rung steps | 98 | 0 | 3/3 |
| `capability` | — | **PASS** | every arm/configuration pair whose arm is active | 54 | 0 | 14/14 |
| `provenance` | — | **PASS** | one scratch repository, three states | 4 | 0 | 4/4 |
| `data` | — | **PASS** | 16 committed files + the moved predicate module; 9 declared counts | 17 | 0 | 6/6 |
| `run_path` | — | **PASS** | 2 phases × the declared field list; 2 displacement streams; 4 refusals | 9 | 0 | 12/12 |
| `artifacts_check` | — | **PASS** | 19 artifact rows over 3 configurations | 95 | 0 | 3/3 |
| `artifacts_derive_inputs` | — | **PASS** | 3 configurations; the digest gate applies to the 2 pulsed ones | 2 | 0 | 4/4 |
| `artifacts_census` | — | **PASS** | 3 configurations, one evaluation census each, read half on | 81 | 0 | 2/2 |
| `artifacts_per_run` | — | **PASS** | 5 (configuration, input file) pairs over 3 configurations | 16 | 0 | 2/2 |

**21 PASS, 0 FAIL, 0 not run; 106 of 106 teeth tripped.**

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

### 4.3 G1 — switch neutrality *(re-run; exclusion set reviewed)*

**Criterion** (plan §3.9): with every architecture switch unset, the copy after a change behaves
byte-identically to the copy before it — every deterministic leaf of the run record and every line
of PROCESS's own output file.

**Result: PASS.** 6 run pairs; **0 of 3 329** record values and **0 of 51 319** output-file lines
differ; 546 values and 45 lines excluded, each named with its reason. 5 teeth: a 1-ULP move, one
changed output line, a missing "before" record refused, two captures audited at different positions
refused, and a new fifth — §5.

**A limitation to state plainly.** G1's two sides are meant to straddle a *driver* change, and this
task makes none: the driver chain closed at A60 (driver-attempts). Both captures here were therefore
made at **the same commit**, so what this run of G1 shows is that the run path is deterministic and
that the exclusion set covers what it claims — **not** that a driver change is inert, because there
is no driver change between them. Making a genuine "before" capture would need a tree checked out at
`5e64ce0e`, which only the orchestrator can stand up. What *is* measured about the change this task
makes to the record is the fifth tooth, §5.

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

### 5.1 G1 — 59 names, split into 27 and 32

*Caption: gate G1's exclusions grouped by kind, measured over its 6 run pairs. "Leaves" is how many
record leaves the group covers, summed over the pairs, counting each leaf once. A structural name is
excluded however equal it reads; a "field a change adds" is excluded only where one side actually
lacks it.*

| kind | names | leaves covered | verdict |
|---|---|---|---|
| a path into a run's own directory or the tree | 10 | — | **KEPT unconditional** |
| a timing or the machine's state | 7 | — | **KEPT unconditional** |
| the commit, or the working tree's state | 8 | — | **KEPT unconditional** |
| the switch vocabulary a rename changes | 2 | 384 | **KEPT unconditional** |
| **a field a change adds** (null or absent before, a value after) | **32** | **1 040** | **MADE CONDITIONAL** |

**Sizes: 59 names before, 27 always-excluded after, with 32 conditional.** `compare_records` now
takes a conditional set: a name in it is excluded only where one side lacks the leaf — absent, or
null against a value — and compared wherever both sides carry it.

**What that recovered, measured:** G1 compared **2 289** record values before the condition and
**3 329** after — **1 040 leaves** put back, still 0 differing. The largest contributors are
`exit_audit.mixed` (338 leaves), `exit_audit.frozen` (224), `predicate_counters` (156),
`attempt_accounting` (114) and `exit_audit.restricted` (74, this task's own — 74 and not 86, because the two absolute paths inside that block are covered by a structural exclusion already and are not counted twice).

**Three names are inert at this commit** — `output_loop_null_because`,
`predicate_counters_null_because`, `attempts[].cost_null_because` — matching no leaf on either side.
They are the sentences a record carries *instead of* a counter the driver does not stamp, so they
appear exactly in the case they exist for. **Nothing was deleted from the table**: a name that has
stopped being needed is worth more visible than gone, and the condition is what makes it inert.

**The `[]` list-element matcher is kept and is load-bearing.** Seven of the conditional names are
`attempts[].…`: they exclude one leaf of every attempt and leave the rest of each attempt — the exit
code, the iteration count, the finite-difference step, the rung name — compared element by element.
Excluding `attempts` by its bare name would have taken all of them out.

**The one name this task added, and what it hides, measured.** `exit_audit.restricted` on an
optimisation record is null before this task and a block after (§6.3). The fifth G1 tooth builds the
earlier shape — the same record with the block nulled — and compares it with and without the
exclusion: **13 of 690 values differ without it and 0 of 677 with it**. That count is exactly what
the exclusion hides, and it is now recovered anyway wherever both sides carry the field.

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
the two sides — which is precisely why the set is 17 against G1's 59 and why the same review reaches
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

*Caption: PROCESS runs started through `harness/pool.py`, counted from the records on disk. Every
run is a fresh subprocess in its own working directory with `PYTHONPATH` naming the experiment's own
copy of PROCESS, and asserts the exact tree it imported before doing any work. Wall clock is the sum
of the children's own timings and is **context, never evidence** (I-10: identical work has varied by
up to 35 % in CPU-seconds on this machine).*

| | count |
|---|---|
| evaluation-phase runs (one `call_models` each) | 117 |
| optimisation-phase runs | 43 |
| census runs | 6 |
| **total records on disk** | **172** |
| of which stamped `campaign_run_kind = gate` | 170 |
| of which stamped `smoke` | 2 |
| of which stamped `force_maxcal` (demonstrations, never a population) | 1 |
| summed in-child wall clock, all runs | ≈ 2 030 s (≈ 34 min), at 3 workers — context only |

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
$PY experiment_runner.py --gate all --resume --census-entry evaluation
$PY experiment_runner.py --measure all
$PY PROCESS/copy_gates.py all                  # the copy is still the copy
$PY PROCESS_diff.py                            # seven changed files, none unexplained
```

Gate G1 alone is two steps, and a genuine run of it needs two commits:

```bash
$PY experiment_runner.py --gate switch_neutrality --capture before   # at the commit before a driver change
$PY experiment_runner.py --gate switch_neutrality --capture after    # at the commit after it
$PY experiment_runner.py --gate switch_neutrality                    # compare, with teeth
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
| 7 | G1's change-added exclusions are made **conditional** rather than deleted | deleting them would break a future G1 that legitimately straddles an older commit; keeping them unconditional hides 1 040 leaves for ever | pass `conditional=None` in `neutrality_body`; the gate then compares 2 289 values again |
| 8 | G8 and G9 make their own runs with resume, instead of a separate capture command | a stage that exists only as a shell invocation is not reproducible (protocol §15), and both sides are the same commit | wrap their bodies back to the comparison alone; `python -m harness.gates <name> --capture runs` still works |
| 9 | `--outdir` redirects a gate's **verdict** but not the gates' runs | one gate reads another's runs; moving them to relocate a small JSON would break that | pass the root through as well and give the output-path gate a second option for where to look |
| 10 | the **experiment plan's §4.1 table is not edited** | that file is not on this task's owned list and the plan's amendments are the orchestrator's | §3's table and `--measure gate_table` are ready to paste |
| 11 | the G4 namespaces come from the **run-time** census, taken with resume | the committed census records what a node writes; the crawl needs what a node ran, and the difference is a whole namespace on the steady-state configuration | pass the committed census; `pulse` silently leaves the set |
| 12 | the G7 configuration is chosen as the one with the fewest iteration variables, **derived** | a gate that named a configuration would need editing when the configuration list changes, and the list is allowed to change by a recorded decision | name it |

---

## 10. Handover

### To the orchestrator

- **The experiment plan's §4.1 table** can be filled from §3 above, or regenerated with
  `experiment_runner.py --measure gate_table`, which also emits it as markdown. This task did not
  edit the plan.
- **Gate G1's re-run here is a self-comparison** (§4.3): both captures are at one commit, because
  this task makes no driver change. A genuine before/after straddling this task's record change
  needs a tree at `5e64ce0e`. What the change costs G1 is measured by its fifth tooth (13 of 690
  values), and the exclusion is conditional, so a future G1 across a real driver change compares it.
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

- **G1's two captures are at one commit** (§4.3). Its zero is a statement about determinism and
  about the exclusion set's coverage, not about a driver change being inert.
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
  (the output-path measurement's own contrast runs). All numbers in this report were taken at
  `36bc2a08`.
