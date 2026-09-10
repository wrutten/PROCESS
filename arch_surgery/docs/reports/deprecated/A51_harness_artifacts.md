# A51 (harness-artifacts) — the artifact stages of the V4 harness

> **Document status** — **MERGED, archived.** Task report for A51 (harness-artifacts), rebuild task H4,
> branch `A51-harness-artifacts` (retired) off `architecture_surgery` at `f1f90c20`, merged on 2026-09-10
> (`ed343e46`); the orchestrator's critical assessment (protocol §5) is §12. Folder position records
> lifecycle, not validity (trap T3).

---

## 0. Words used here, spelled out once

A report should read without the queue open beside it (orchestration protocol §4).

| term | meaning |
|---|---|
| **configuration** | one optimisation problem. Three of them: `large_tokamak_nof` and `low_aspect_ratio_DEMO` (pulsed plants), `st_regression` (steady state) |
| **input file** | the file a configuration is read from. Either the **committed** one, which is never edited, or the **lifted** one, derived from it, in which the burn time has become a variable the optimiser owns |
| **coupling state** | the set of data-structure fields the analysis loop drives to a fixed point, and the measured scale of each. 840 / 846 / 827 components on the three configurations |
| **write sets** | which components of the coupling state each block of the partition writes. A block's convergence test is taken over its own components |
| **per-run deferral set** | the model nodes whose outputs nothing the optimiser decides on ever reads, and which therefore run once per run at the accepted optimum instead of once per evaluation of the model set |
| **the census** | a direct runtime observation of what each model node reads and writes, taken by an instrument inside the driver that is switched on by an environment variable and is a no-op when it is not |
| **arm** | one assignment of the driver's switches. `AR` and `BR` are the **reference** arms: PROCESS as shipped, every architecture switch unset |
| **tooth** | a deliberate break, made to show that a check can fail. A check whose failure mode has never been exercised is an assertion, not a measurement (protocol §12) |
| **the driver** | `process/core/caller.py` and `process/core/solver/`: the arrangement of solvers and optimisers, which is the only thing this experiment varies. Every physics and engineering model is frozen |

Three project references appear below. **Trap T1/T7** is this project's recorded hazard that ten
model objects call their own `run()` from inside their `output()` method, so an instrument hooking
`run()` alone attributes post-solve reporting to the analysis loop and invents dependency edges.
**Trap T9** is that a sibling repository regenerates its exported analysis at every merge, so
reading it live catches a half-written state and silently re-pins this study to whatever that tree
holds that day. **Trap T11** is publishing a number without the population or condition that limits
it.

---

## 1. Verdict

Four stages built, all four passing, every check shown able to fail.

*Caption: one row per stage; "compared" is the denominator of things actually compared, "verdict"
the stage's own exit. Population: the three configurations of the campaign. Every number comes from
`experiment_runner.py --artifacts <stage>` at the commit named in §8.*

| stage | what it does | compared | mismatched | verdict |
|---|---|---|---|---|
| `check` | rebuilds every committed artifact's own stamps and cross-checks them against the files it must agree with | **93** individual checks over 19 artifact rows, run where the chain runs it (before the derivation); **95** run after it | 0 | **PASS** |
| `derive-inputs` | derives each pulsed configuration's lifted input file and gates the bytes on the recorded digest | **2** derived files (the 2 pulsed configurations) | 0 | **PASS** |
| `census` | takes a runtime write and read census and compares it with the committed one | **81** (66 node write sets + 15 block subsets) | 0 | **PASS** |
| `per-run` | re-derives every per-run deferral set with the class-level classifier and compares it node by node | **16** node comparisons over 5 (configuration, input file) pairs | 0 | **PASS** |
| `teeth` | the deliberate breaks of all four | **11** teeth | 0 not tripped | **PASS** |

Three results are worth naming on their own.

1. **The lifted input files are reproduced byte for byte.** Both pulsed configurations' derived
   files match the sha256 committed by the previous rebuild task, which measured them from the
   previous experiment revision's own derived files. The burn time behind the third edited line is
   re-measured by a PROCESS run and comes out bit-identical to the previous revision's:
   `2568.1324076519313` s and `10397.38190748901` s, `0x1.41043caef8d92p+11` and
   `0x1.44eb0e25837b3p+13`.

2. **A fresh census reproduces the committed one exactly, on all three configurations**:
   22/22, 23/23 and 21/21 node write sets identical, 862/862, 868/868 and 843/843 fields, **zero**
   differences in either direction. The committed census was measured at a different commit, from a
   file that is not committed; it is reproduced here by a run of the experiment's own copy of
   PROCESS through the new harness.

3. **The class-level classifier reproduces every committed per-run deferral set** — same nodes,
   same order, same `nodes_sha256` — on all five (configuration, input file) pairs, from a
   *different reachability source*. The committed artifacts were derived using a sibling
   repository's generated dependency export; this derivation uses a source scan of the tree under
   test, which trap T9 requires and which is the only source available inside this repository.

**Three findings** are reported, none of which is a difference between a re-derived artifact and a
committed one: a read the instrumented window sees and the source scan does not (§5.4), a preamble
key a run record was silently dropping (§5.5), and two names in a dead-branch list that no longer
exist in the source (§6.3). None changes a published number, and none was absorbed.

---

## 2. What was built

Four modules and a group of runner stages, all reachable from the one entry point.

| file | lines | added here | what it is | owns |
|---|---|---|---|---|
| `harness/artifacts.py` | 1 233 | 1 233 | resolve and validate every committed artifact; the measured ledger; the shared `StageCheck` shape | A51, new |
| `harness/postsolve.py` | 1 222 | 1 237 | the class-level per-run deferral classifier | A51, new |
| `harness/census.py` | 848 | 848 | the runtime write and read census, its child, and the three comparisons | A51, new |
| `harness/input_files.py` | 816 | +670 / −59 | the lifted input file: resolution (A50) **and** the derivation (A51) | A51, extended |
| `experiment_runner.py` | 750 | +226 | `--artifacts {check,derive-inputs,census,per-run,teeth,all}`; the preflight's artifact half replaced | A51, extended |
| `harness/README.md` | 742 | +174 | a new section 12 appended at the end | A47/A49 own the rest |
| `harness/pool.py` | 438 | +27 | a third child entry point, additively, so the census run gets the same isolation | A50's file |
| `harness/predicate.py` | 319 | +13 | one added key and the paragraph explaining it (§5.5) | A50's file |

*Caption: one row per file touched. "lines" is the whole file after this task; "added here" is this
task's diff against the branch point `f1f90c20`. Total: 4 369 insertions, 59 deletions over 8
files.*

---

## 3. `derive-inputs` — the lifted input file

### 3.1 What it derives, and from what

Two of the eight arms hand the burn time to the optimiser. They read an input file that differs
from the committed one in **exactly three lines**:

1. the burn time becomes iteration variable 178 (`ixc = 178` appended);
2. its consistency residual becomes equality constraint 93, **inserted immediately after the last
   existing equality entry**, with the declared equality count raised in the same edit;
3. `t_plant_pulse_burn` is set to the burn time the incumbent's own loop settles on at the
   configuration's own starting design vector.

Line 2's *position* is load-bearing and has already gone wrong once in this project. PROCESS does
not decide which constraints are equalities from the constraints themselves: it takes the first
*n* entries of the constraint list **in the order the input file lists them**. Appending the new
entry at the end of the file therefore turned an equality into the last inequality — a problem in
which nothing forces the burn time onto its own consistency manifold — and the run still returned a
converged solution with an objective that looked right. It was found by reading an inequality count
in a gate table, not by inspecting the file.

Line 3 is a **measurement**. `measure_settled_burn_time` runs one evaluation of the model set
through the pool — fresh subprocess, own working directory, `PYTHONPATH` naming the experiment's
own copy of PROCESS, the exact tree asserted inside the child — and reads the settled burn time off
the run's record.

### 3.2 Which arm measures it, and why that one

**`AR`**: the evaluation-phase reference arm, every architecture switch unset.

The rule the derivation implements is *"the burn time the **incumbent's** own loop settles on"*. The
incumbent is PROCESS as shipped, so the measuring run must carry no architecture switch at all —
that is the reference arm by definition. It is the *evaluation* phase and not the optimisation
phase because the rule asks for the value at the **starting** design vector: one evaluation of the
model set at the input file's own point is exactly that, while an optimisation would move the
design vector before the loop settled anywhere.

The alternative would have been the flat control `A0`, and it is the wrong choice for a reason
worth recording: `A0` stops on the coupling state at the tolerance τ, and the value the lifted
variable must start from is the one the *incumbent's* stopping rule leaves behind, not the one a
tighter rule would. The two arms would give two different starting points and only one of them
makes the lifted arm's entry consistency residual what the previous revision measured — which the
digest gate then decides. It does: `AR` reproduces the digests, so the choice is confirmed by
measurement rather than argued.

### 3.3 Result

*Caption: one row per configuration. "burn time" is the measured value the third edited line
carries, given as a decimal and as an exact hexadecimal float. "position" is where constraint 93
lands in the constraint list, and the equality count is what makes that position an equality.
Population: the three configurations; the digest gate applies to the two pulsed ones.*

| configuration | burn time (s) | hex | equality count | constraint 93 at position | derived sha256 | matches recorded |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 2568.1324076519313 | `0x1.41043caef8d92p+11` | 3 → 4 | 4 of 27 | `8902a6a58bb3…` | **yes** |
| `low_aspect_ratio_DEMO` | 10397.38190748901 | `0x1.44eb0e25837b3p+13` | 4 → 5 | 5 of 26 | `189c5e1e99c2…` | **yes** |
| `st_regression` | — | — | — | — | — | *not applicable, steady state* |

`st_regression` records **"not applicable, steady state"** rather than deriving anything: it has no
burn-time coupling, the arm in which the optimiser owns the burn time composes onto its predecessor
there, and no arm on it reads a lifted input file. That is a stage outcome, not a skipped row —
*not applicable* and *not done* are different results.

### 3.4 A note on the derived file's own text

The derived file's header and its three edit comments are reproduced **verbatim** from the script
that first produced it, task token and all. The harness plan's rule against version and task tokens
in names binds identifiers in this package; it cannot bind the bytes of a file whose byte-identity
with the previous revision's is the very thing being proved. A tidier comment is a different file
and would fail the gate. This is stated in the module docstring so nobody tidies it later.

### 3.5 Teeth

*Caption: one row per deliberate break; all four tripped.*

| break | must be caught by | tripped |
|---|---|---|
| one byte of a throwaway derived file flipped | the digest | yes |
| a baseline evaluation that crashed | the refusal to derive without the measurement | yes |
| a record carrying no settled burn time | the same refusal | yes |
| the constraint appended at the **end** of the file instead of inside the equality block | the digest | yes |

The second and third are the important pair. The input file's own default for the burn time is
1000 s and none of the pulsed configurations sets it, while the settled values are thousands of
seconds. A derivation that quietly fell back on the default would therefore produce a file that
*looks* right and starts the lifted arm at a design point the incumbent never visits — a confound,
not a perturbation. `burn_time_from_record` refuses instead.

---

## 4. `check` — the artifact ledger, measured rather than declared

### 4.1 What changed against the preflight it replaces

The preflight used to ask, per configuration, whether each artifact file existed and whether one
count matched. It now runs `artifacts.check` **instead**. The reason: a file can exist, carry the
declared component count, and still have been built for a different configuration, against a
different component set, or from a generation of the scales nobody can identify. Each of those has
a stamp in the file, and every stamp is now **rebuilt and compared** rather than assumed. What is
kept from the old stage is the human summary of what each configuration is and which arms it skips,
because that is orientation rather than verification.

`check` is also available on its own (`--artifacts check`) and returns its own code.

### 4.2 What is checked, and against what

*Caption: one row per kind of check; "against" is the thing compared with, not the thing checked.
"n" is how many of that check the stage makes over the three configurations. Every check is a
rebuild-and-compare or a cross-file agreement; none is a presence test.*

| check | against | n |
|---|---|---|
| `format` | the string the driver's own loader requires | 13 |
| configuration stamp | the configuration the file is resolved for | 11 |
| `nodes_sha256` rebuilt | the value recomputed over configuration, figure of merit, constraint set and node list | 5 |
| figure of merit **against the input file** | the `minmax` the input file declares | 5 |
| constraint set **against the input file** | the constraints the input file declares, plus constraint 93 exactly where the artifact is the lifted one's | 5 |
| the lift adds exactly one constraint | which of the pair this artifact is | 5 |
| every deferred node is a real call site | the committed node map's call sites | 5 |
| **no deferred node feeds the predicate** | each deferred node's measured write set against the 215 fields the objective branch and the constraint layer read | 5 |
| component count | the count the file declares, the components it lists, and the count the campaign declares — all three at once | 3 |
| `components_sha256` rebuilt | the value recomputed from the components the file lists, through the predicate module's own specification object | 3 |
| **harvest identity** | a block carrying a file hash, a content hash and a design-point count | 3 |
| `predicate_mode` stamped | the preamble key that will name the convergence predicate | 3 |
| write sets paired with the coupling state | the coupling-state spec **rebuilt from its own components** — by content, the way the driver pairs them, not by trusting either file's recorded value | 3 |
| every write-set key is a coupling component | the coupling-state artifact's component list | 3 |
| the write sets cover the whole state | every component; one written by no block is one a block loop would never test | 3 |
| `subsets_sha256` rebuilt | the value recomputed from the subsets the file lists | 3 |
| iteration variables and constraints | the counts the campaign declares | 3 |
| figure of merit | the figure of merit the campaign declares | 3 |
| the committed input file does not already own the burn time | iteration variable 178 absent — a committed file naming it would put two owners on the burn time, which the driver refuses outright | 3 |
| a digest is recorded for the lifted input file | the digests committed in `input_files.py` | 2 |
| `union_sha256` rebuilt | the union of every node's write set | 1 |
| a census for every configuration | the campaign's population | 1 |
| call sites and modules | the node map's own node list | 1 |
| not applicable, steady state | the configuration's own plant model | 1 |

**Total: 93 checks over 19 artifact rows; 0 failed** — the counts above are the recorded run,
in which `check` runs where `--artifacts all` puts it, **before** the input-file derivation, so the
two lifted input files are *pending* and contribute one check each instead of two (§4.4). Run after
the derivation the total is **95, 0 failed**; the condition is stated here rather than left for a
reader to reconcile two numbers (trap T11).

### 4.3 The harvest identity, and the refusal

The coupling-state artifacts carry the **scales** every residual figure in this experiment is
measured against. They were measured once, from a file that is not committed, and they are the
ruler: three earlier revisions' residual figures are quoted on them, so a fresh measurement would
change what the tolerance means without changing any number's appearance.

Accordingly there is **no derivation stage for them in this package** — not disabled, not guarded,
absent — and `check` validates each from the artifact's **own harvest identity**: a hash of the file
it was measured from, a content hash over the coupling-key set, the model sequence and every design
point's exact design vector, and the number of design points. An artifact carrying no such identity
is **refused by name**, because a file that cannot say what produced it cannot be checked at all,
and running on it would put an unidentified ruler under every residual figure the experiment
publishes.

All three configurations' artifacts carry it, and the check reports the contents rather than a
tick: **149 / 297 / 144 design points** on `large_tokamak_nof` / `low_aspect_ratio_DEMO` /
`st_regression`, each with both hashes and a 22-node model sequence.

### 4.4 `predicate_mode`, and *pending* versus *absent*

Two things are recorded rather than failed, and both are worth stating explicitly because a silent
pass and a recorded gap look the same in a total.

**`predicate_mode` is not stamped** on any committed artifact today. The ledger records *"not
stamped — the field arrives with A59 (driver-predicate-mode)"* rather than failing, because there
is currently one convergence predicate and the choice the field would record does not yet exist.
When A59 lands, the check is already in place and the row will report the value.

**A lifted input file that has not been derived yet is `PENDING`, not `ABSENT`.** The two are
different results: a *committed* artifact that is missing is a refusal, since nothing in this
package makes one, while a *derived* one is produced by a stage of this same runner and is
untracked by design. The run path refuses on it independently — `assert_lifted` checks the digest
before any arm reads the file — so this cannot let a campaign start without it. The ledger names
the stage that produces it.

### 4.5 Teeth

*Caption: three deliberate breaks, each on a throwaway copy in a temporary directory; the committed
files are never written to. All three tripped.*

| break | must be caught by | tripped |
|---|---|---|
| `components_sha256` set to zeros | the rebuild from the components the file lists | yes |
| the harvest identity block removed | the refusal on an artifact that cannot say what produced it | yes |
| the figure of merit changed **and the artifact's own `nodes_sha256` recomputed to match** | the comparison with the input file | yes |

The third is the one that earns its place. An artifact that rebuilds its own hash can still be the
wrong problem's: the internal hash proves the file has not been hand-edited, and only the
comparison with the input file proves it describes *this* problem.

---

## 5. `census` — the runtime write and read census

### 5.1 What it does

One PROCESS run per configuration with the driver's census instrument on, through the pool like
every other run in this package. The instrument attributes every read and every write of a
data-structure field to the model node executing at the time. Two entries are available: one full
optimisation (the population the committed census was measured over, and the default) or one
evaluation of the model set (cheaper, one design point).

The instrument is **the driver's**, switched by its own environment variable, and this task did not
change it. Its variables are the one place in the new modules where an environment name is written
literally; every architecture switch is composed through the arm registry, so a switch rename lands
in one place.

### 5.2 The write sets — an exact reproduction

*Caption: one row per configuration. "nodes" are model nodes with a non-empty write set;
"fields" are data-structure fields written. "committed-only" is a field the committed census has
that this run did not write — the benign direction, a field written at a design point this run did
not visit. "this-run-only" is a field this run wrote that the committed census does not record —
the dangerous direction. Population: one full optimisation per configuration under the reference
arm `BR`, at the commit in §8.*

| configuration | nodes identical | fields, this run | fields, committed | committed-only | this-run-only | sweeps | output-path calls refused |
|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | **22 / 22** | 862 | 862 | 0 | 0 | 2 029 | 30 |
| `low_aspect_ratio_DEMO` | **23 / 23** | 868 | 868 | 0 | 0 | 4 286 | 30 |
| `st_regression` | **21 / 21** | 843 | 843 | 0 | 0 | 1 891 | 30 |

Zero differences in either direction, on 2 573 fields over 66 nodes. This is a stronger result than
it may look: the committed census was built from a measurement taken at an earlier commit, from a
35–69 MB file that this repository does not track, and it is reproduced here field for field by a
fresh run of the experiment's own copy of PROCESS through a harness rewritten from scratch.

**The 30 refused calls are trap T1/T7 in live form**, and they are reported rather than assumed.
The instrument refuses any model node entered after the sweep boundary has closed. On every
configuration it refused exactly 30: ten model objects — `costs`, `availability`, `pulse`,
`divertor`, `structure`, `ccfe_hcpb`, `power.acpow`, `vacuum`, `buildings`, `water_use` — three
times each, which is the final output idempotence check calling `run()` from inside `output()`. Had
those been counted, they would have entered the write sets and the dependency closure.

### 5.3 The per-block subsets

*Caption: one row per configuration. An entry is one coupling-state component a block writes;
"blocks identical" compares the committed per-block subsets with this run's census mapped node →
block through the committed node map and intersected with the coupling state's own component list.*

| configuration | blocks identical | coupling components | differences |
|---|---|---|---|
| `large_tokamak_nof` | **5 / 5** | 840 | 0 |
| `low_aspect_ratio_DEMO` | **5 / 5** | 846 | 0 |
| `st_regression` | **5 / 5** | 827 | 0 |

### 5.4 The runtime read census — item 6a(a), and the one finding

The improvement list asks for a committed runtime read census, because the strongest claim in the
deferral derivation rested on a source scan plus a crawl of a dependency model, and a runtime
census turns that into a direct observation. **It needs no driver change**: the instrument already
records reads per node and reports their *count*; the field names are read by the harness from the
instrument's own state inside the same child process that produced them.

The durable fix is a one-line addition to the instrument's summary — `"reads_by_node": {n:
sorted(f"{a}.{b}" for a, b in v) for n, v in _reads_all.items()}`, exactly beside the
`writes_by_node` entry already there, in `_idf_probe_modules.summary()`. It is **not made here**,
because a driver change from a harness task would land outside its own neutrality gate. It is
handed to whichever driver task next touches the instrument (§9).

*Caption: one row per configuration. "read at run time" is the objective/constraint block's own read
set observed during one optimisation; "in the source scan" is the read set the routing rule derives
for that figure of merit. Two constructions are published, because the runtime window is slightly
wider than the two source files (see below).*

| configuration | read at run time | in the source scan | read and listed | read, not listed | of which written by some node | restatement agrees with the driver |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 77 | 215 | 76 | 1 | **0** | yes, 215 / 215 |
| `low_aspect_ratio_DEMO` | 80 | 215 | 79 | 1 | **0** | yes, 215 / 215 |
| `st_regression` | 61 | 215 | 60 | 1 | **0** | yes, 215 / 215 |

**Finding.** On all three configurations the predicate node's runtime read set contains one field
the source scan does not list: `numerics.i_figure_merit`.

*What causes it.* The instrument opens its window at the driver's own call site, not at the
objective function's entry. `caller.py:1234` reads `self.data.numerics.i_figure_merit` to pass it
into `objective_function`, which takes the figure of merit as an **argument** rather than reading it
from the data structure. The read is therefore genuinely inside the instrumented window and
genuinely outside the two source files the scan reads. It is not an error in either.

*What it costs.* Nothing. The routing rule only ever asks about fields **a model node writes** — a
field no node writes cannot make a node live, whatever reads it — and `numerics.i_figure_merit` is
written by no node: it is absent from the committed write census's 1 013-field union and from all
three runtime censuses. It is a configuration selector, not state.

*What was done about it.* The comparison publishes **both constructions**: the raw containment over
every field the block read, and the containment restricted to fields some model node writes, which
is the one that binds. Every read the restriction removes is **listed by name**, never counted
away. The stage fails only on the second. The first recorded run of this stage failed on the raw
construction; the correction is a change to the *check*, made after the cause was established, not
a change to any artifact — no committed file was edited and no number moved.

*And the check the finding prompted.* `artifacts.predicate_read_fields` restates a rule the driver
also implements, and the harness plan is explicit that an inherited criterion's agreement with the
original must be a **result**, not an assumption. `compare_with_driver` now calls the driver's own
`_predicate_read_fields` in a fresh subprocess with the tree under test on the path, asserts that
the child imported that tree, and compares. They agree on **215 / 215 fields on all three
configurations**, which is what rules the restatement out as the cause of the finding above.

### 5.5 A second, smaller finding

`predicate.provenance_of` — the function that copies a coupling-state artifact's preamble into a run
record — listed `harvest_identity` among the keys it copies. **No committed artifact carries that
key**; the block is called `harvest`. So the identity block never reached a record at all, and a run
record named the artifact's digest without naming the measurement its scales came from. Both names
are now listed. This is a one-word additive change to a file this task does not own, made because
`check` refuses on an absent harvest identity and it would be odd for the check to require what the
record then drops. Flagged here for the reviewer rather than folded in silently.

### 5.6 Teeth

*Caption: two deliberate breaks on a throwaway copy of one census; both tripped.*

| break | must be caught by | tripped |
|---|---|---|
| one node's write removed | the per-node comparison: one more committed-only field and one fewer identical node | yes |
| a node writing a field the committed census does not have | the this-run-only count, which is what fails the stage | yes |

---

## 6. `per-run` — the class-level deferral classifier

### 6.1 The derivation

A node whose outputs nothing the optimiser decides on ever reads cannot change what the optimiser
does, so it runs once per run at the accepted optimum instead of once per evaluation. Which nodes
those are is derived in four steps:

1. **Seeds** — what the optimiser's own layer reads: the active figure of merit's own branch of the
   objective function, plus every *active* constraint's read set with closure over local helper
   calls. Taken by parsing the source, never by searching its text (trap T2: `= ` matches `==`).
2. **Backward closure** — a node is *needed* if anything it writes is in the consumed set; when a
   node becomes needed, everything it reads joins that set; repeat to a fixed point. What a node
   writes is the **measured** census. What a node reads is a source scan.
3. **Candidates** — every node that never became needed.
4. **Confirmation** — every read site of every candidate's outputs, anywhere in the tree,
   classified. A live or unclassifiable site is a finding.

### 6.2 The three changes against the derivation it replaces

**(a) Reads are attributed by enclosing class, not by file** — improvement item 6a(a). The previous
derivation decided whether a read site was "internal to the candidate" by testing the file path
against a prefix. `process/models/vacuum.py` holds *two* classes: `Vacuum`, a deferral candidate,
and `VacuumVessel`, a live plant node. A read of a pumping output made inside the vessel class would
have been classified *internal to the candidate* and the node marked dead, with no warning. Here
every site is attributed to the class that encloses it.

The class-to-node map is **derived, not transcribed**: the node names and the container attribute
each invokes are read from the committed node map's own `invocation` strings, and the classes each
attribute can be are parsed from the driver's model container. An attribute constructed from other
attributes owns their classes too — the plasma model is built from twelve of them — and an attribute
that is a property owns every class it can return, which is how the two cost-model implementations
are covered. Measured: **48 classes mapped across 28 nodes**, from 53 assigned container attributes
and 2 properties, with **0 nodes left without a class** — a node the map could not resolve would be
reported rather than skipped.

**(b) The reachability layer is a source scan of the tree under test**, not a live read of a sibling
repository's generated dependency export. Two reasons, and the first is binding: trap T9 forbids
reading that repository's generated output live, and the export is not committed here — so the
previous derivation cannot be re-run from anything this repository holds. The second is that a static
scan takes every branch, which errs towards keeping a node in the loop.

**(c) A disagreement is reported, not raised.** The previous derivation exited on a live read site.
This one records it and fails the stage with the site's file, line, class and function.

### 6.3 The three exclusions, counted rather than applied quietly

A static scan of every read in the tree, taken literally, makes every node needed and the
derivation vacuous. Three kinds of site are excluded, and each is the direction in which a mistake
marks a live node dead — so each is counted and named in the stage record.

*Caption: one row per exclusion, with the count on `st_regression` as an example; the counts are
per configuration and appear in every stage record.*

| exclusion | why | sites excluded (`st_regression`) |
|---|---|---|
| a function reachable from a reporting entry point and from **no** node entry point | trap T1/T7: ten models call their own `run()` from `output()`, so "is this function called at all" is the wrong question. Computed per class from the call graph — **149** such functions in the tree | 964 |
| a file no configuration here executes (the stellarator and inertial-fusion paths, and the neoclassical transport module) | no configuration selects them; the block driver refuses the first outright | 741 |
| a function this configuration's own switches make unreachable | the plant-availability model has three implementations and every configuration selects the default, so the other two's functions are dead code | 61 |

The third is exactly the case the improvement list raises: the availability model reads
`vacuum.n_vac_pumps_high` at four sites, all inside the two non-default branches. Without that
exclusion the closure makes `vacuum` needed and the derivation disagrees with the committed artifact
— which is how the exclusion's necessity was established here, by measurement rather than by
argument. The transcribed function list is re-checked against the model's own source, so a renamed
function shows up as a disagreement rather than as a silently empty exclusion: 11 declared, 11
found.

The scan sees **26 312** candidate read sites in the tree. After the three exclusions, sites are
attributed by enclosing class where the class maps to a node (2 924 on `st_regression`), by the
file's mapped classes where it does not (101), and to no node where the file defines no mapped class
at all (382 — chiefly the constraint layer itself, which is the seed set and not a model). The
counts on the other four pairs are within 5 % of these.

**A third finding, small and stale.** The transcribed list of non-default plant-availability
functions names **11**; this tree's availability model defines **9** of them. `avail_st_centrepost`
and `avail_st_divertor` do not exist here. The list is stale, and harmless in this direction: a name
that does not exist excludes nothing, so the closure keeps every read it would have removed. (The
dangerous direction — a dead branch the list fails to name — is also safe, because it keeps a node
in the loop.) The stage re-checks the list against the source on every run and now says so in its
notes rather than leaving it in the record; it changes no result here.

### 6.4 Result

*Caption: one row per (configuration, input file) pair. "derived" is the set this stage computes;
"committed" is the artifact the driver loads. "units needed" is how many of the closure's units the
seeds reach. Population: 5 pairs — three configurations, with the lifted input file's artifact also
compared on the two pulsed ones.*

| configuration | input file | derived | committed | same set | same order | same `nodes_sha256` | seed fields | units needed |
|---|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | committed | `vacuum, water_use, costs` | same | **yes** | yes | **yes** | 82 | 16 of 19 |
| `large_tokamak_nof` | lifted | `vacuum, water_use, costs` | same | **yes** | yes | **yes** | 85 | 16 of 19 |
| `low_aspect_ratio_DEMO` | committed | `vacuum, water_use, costs` | same | **yes** | yes | **yes** | 83 | 16 of 19 |
| `low_aspect_ratio_DEMO` | lifted | `vacuum, water_use, costs` | same | **yes** | yes | **yes** | 86 | 16 of 19 |
| `st_regression` | committed | `pulse, vacuum, water_use, costs` | same | **yes** | yes | **yes** | 63 | 15 of 19 |

**Zero differences, and no live read site of any deferred node's output on any pair.** The
`nodes_sha256` agreement means the whole tuple the driver hashes — configuration, figure of merit,
active constraint set, node list in order — is bit-identical to the committed one.

The lifted pairs' seed sets are exactly three fields larger than the committed ones on both pulsed
configurations, which is constraint 93's own read set: the lift adds one constraint and the seeds
grow by what it reads, and by nothing else.

The order is taken from the census itself — the instrument records nodes in first-seen order, which
is the order the once-per-run sweep executes them in — rather than from a transcribed sequence list.

### 6.5 One limitation of the cheaper path, measured

`postsolve.stage(use_committed_census=True)` derives from the committed write census instead of
taking a fresh one. It is available and it is **not** the default, for a measured reason: the
committed census lists only nodes with a *non-empty* write set, and on `st_regression` the pulse
model's entire body is guarded off, so it writes nothing and is absent from that file. The
derivation then never proposes it and returns `vacuum, water_use, costs` where the artifact says
`pulse, vacuum, water_use, costs` — measured, by running that path. A runtime census lists every node that *executed*, which is what
the closure needs — a node that runs and writes nothing is precisely a node worth deferring. The
default is therefore the measured census, and the option carries the limitation in its output.

### 6.6 Teeth

*Caption: two deliberate breaks on throwaway copies of one committed artifact; both tripped.*

| break | must be caught by | tripped |
|---|---|---|
| a node removed from the committed set | the node-by-node comparison, naming it derived-only | yes |
| a live node added to the committed set | the node-by-node comparison, naming it artifact-only — the direction that would defer a node the optimiser consumes | yes |

---

## 7. PROCESS runs made

*Caption: one row per kind of run in the full chain. All go through `harness/pool.py`: fresh
subprocess, own working directory, `PYTHONPATH` naming the experiment's copy of PROCESS, the exact
tree asserted inside the child, run kind `gate` — never `campaign`. Wall clock is context and never
evidence; the intervals below are single observations on a shared 16-core machine and are given so
a reader knows how long to wait.*

| purpose | arm | entry | runs | wall clock, this chain |
|---|---|---|---|---|
| the settled burn time behind the lifted input file's third line | `AR` | one evaluation of the model set | 2 (the pulsed configurations) | 5.5 s, 4.6 s |
| the runtime write and read census | `BR` | one full optimisation, instrument on | 3 (one per configuration) | 92.7 s, 189.0 s, 84.1 s |

**5 PROCESS runs for the whole chain**, 376 s of run time in one observation, about 6.5 minutes end
to end. An earlier observation of the same chain gave 438 s; the spread is the machine, which is why
none of it is evidence of anything. The `per-run` stage takes no run
of its own: it resumes the census the previous stage took, and resume means a census on disk for the
same configuration and the same entry carrying at least the halves the caller asks for — a directory
alone is never evidence, and a write-only census cannot stand in for one a read census is wanted
from.

A census under the instrument costs roughly 4–10× a plain run of the same configuration, because the
instrument snapshots the data structure at every node boundary and, with the read half on, overrides
attribute access on every data-structure object. `--no-read-census` switches the expensive half off
when only the write sets are wanted.

---

## 8. How to re-run, and at which commit

Every number in this report was produced by executing committed scripts from the one entry point:

```bash
cd arch_surgery/MDA_partitioning_experiment_v4
PY=/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python

$PY experiment_runner.py --artifacts all          # the whole chain, in order
$PY experiment_runner.py --artifacts check        # the ledger alone, no PROCESS run
$PY experiment_runner.py --artifacts derive-inputs
$PY experiment_runner.py --artifacts census --census-entry optimisation
$PY experiment_runner.py --artifacts per-run
$PY experiment_runner.py --artifacts teeth        # no PROCESS run
$PY experiment_runner.py --selfcheck              # the harness's own gates
$PY experiment_runner.py                          # the preflight
```

Each stage writes its record under `runs/artifacts/<stage>.json`, which is untracked by design.
`--artifacts all` stops at the first failing stage rather than carrying on: a failed gate is a
result, and nothing below it is re-run with different settings.

*Caption: one row per figure group and the stage that produced it, with the commit the stage ran
at. Every commit named here is on branch `A51-harness-artifacts`, off `architecture_surgery` at
`f1f90c20`.*

| figures | stage | script | commit run at |
|---|---|---|---|
| §3.3, §3.5 | `derive-inputs`, `teeth` | `harness/input_files.py` | `2926449f` |
| §4.2, §4.5 | `check`, `teeth` | `harness/artifacts.py` | `2926449f` |
| §5.2–§5.6 | `census`, `teeth` | `harness/census.py` | `2926449f` |
| §6.3, §6.4, §6.6 | `per-run`, `teeth` | `harness/postsolve.py` | `2926449f` |
| §6.5 | `per-run` with the committed census, run on `st_regression` alone | `harness/postsolve.py` | `2926449f` |

`--selfcheck` remains **PASS**, 6 of 6 checks with 27 teeth, and the preflight remains **READY**
with the artifact half replaced.

---

## 9. Autonomous decisions, each with its reversal path

*Caption: one row per decision this task took without asking; "reverse by" is what a reviewer who
disagrees would change, and how much else moves with it.*

| # | decision | why | reverse by |
|---|---|---|---|
| 1 | `AR` measures the settled burn time, not `A0` | the rule names the *incumbent's* stopping rule; and the digests confirm it | change `input_files.BASELINE_ARM`; the digest gate then decides |
| 2 | the derived file's comments keep the previous revision's task token | the digest is the gate, and a tidier comment is a different file | not reversible without re-measuring the digests, which forfeits the comparison with the previous revision |
| 3 | the deferral derivation's reachability layer is a source scan of the tree, not the sibling repository's dependency export | trap T9 forbids the live read and the export is not committed here | commit the export as data and add a second reachability source; the register entry would be the place to record it |
| 4 | three exclusions in the closure — reporting-only functions, unexecuted files, dead switch branches | without them every node is needed and the derivation is vacuous; each is measured and counted | remove any one and re-run `--artifacts per-run`; the disagreement it causes is visible immediately |
| 5 | the census entry defaults to one full optimisation | it is the population the committed census was measured over, and the only entry that can reproduce it | `--census-entry evaluation` |
| 6 | the read census is read from the instrument's state, not its summary | a driver change from a harness task would land outside its own neutrality gate | make the one-line summary addition in a driver task and read the summary instead (§10) |
| 7 | `pool.py` gains a third child entry point (+27 lines) | every PROCESS run must go through the pool, and the census is a PROCESS run | give the census its own launcher — which would then be a second place isolation is implemented |
| 8 | `StageCheck` is defined in `artifacts.py` rather than reusing `selfcheck.Check` | `selfcheck.py` belongs to the parallel driver task this round | promote both into `harness/gates.py` — which is A52's job anyway (§10) |
| 9 | a lifted input file not yet derived is `PENDING`, not `ABSENT` | it is a stage that has not run, not a file that is missing; and the run path refuses on it independently | delete the `pending` field on `Row`; `check` then fails until the derivation has run |
| 10 | the read-census comparison publishes two constructions and binds on the second | the runtime window is wider than the two source files; the cause was established before the check changed, and every excluded read is named | drop `containment_holds_where_it_binds` and fail on the raw construction; the stage then fails on `numerics.i_figure_merit`, which no node writes |
| 11 | one-word additive fix to `predicate.provenance_of` | the check requires a harvest identity the record was silently dropping | revert the one line; the identity then never reaches a record |

---

## 10. Handover

### To A52 (harness-gates)

- `artifacts.StageCheck` is the shape to promote into `gates.Gate` / `gates.Tooth`: it already
  carries `binds`, `population`, `n_compared`, `n_mismatched` and a `teeth` list, and every artifact
  stage returns it. Four stages, **11 teeth**, all tripping.
- **G4 (`audit restriction`) needs "one doctored component from each excluded namespace"**
  (improvement item 6a(c)). The excluded namespaces are now derivable rather than guessed:
  `postsolve.derive(...)["crawl"]["candidate_units"]` returns them per configuration. Measured
  here: `vacuum`, `water_use`, `costs` on both pulsed configurations, and additionally `pulse` on
  `st_regression`.
- `artifacts.compare_with_driver` is the pattern for *"where a criterion is inherited from an
  earlier gate, its agreement with the original is a gate result, not an assumed equivalence"*: it
  runs the driver's own function in a child, asserts the child imported the tree under test, and
  reports the difference. It agrees 215/215 on all three configurations.
- `grep` finds no import of, and no subprocess into, `idf_probe/` or `fixedpoint/` in any of the
  four new modules.

### To A53 (harness-tally) and A54 (harness-analysis)

- `artifacts.check`'s ledger is already a table with a caption and per-row denominators; the same is
  true of every comparison in `census` and `postsolve`. `artifacts.report` and
  `artifacts.ledger_table` render them.
- Every count in every stage record carries the denominator beside it, and every table in this
  report states its population in the caption.

### To A55 (harness-smoke)

- `--artifacts all` is the shape the smoke chain wants: stages in order, each returning a code,
  stopping at the first failure. It is 5 PROCESS runs and about 8 minutes on all three
  configurations; `--census-entry evaluation` reduces the census to ~5 s per configuration for a
  smoke pass.

### To A56 (driver-renames), running in parallel

- `pool.py` gained `ENTRY_POINT["census"]` and two `Job` fields (`census_entry`, `census_read`) plus
  an early branch in `_command`. Additive, +27 lines including comments, no existing behaviour
  touched.
- `predicate.py` gained one key in one tuple, plus the paragraph explaining why (+13 lines, §5.5).
- None of the four new modules writes an architecture switch name literally: environments are
  composed only through `arms.env_for`. The census instrument's own variables
  (`PROCESS_IDF_PROBE`, and its two read-budget variables) are the exception, named in one place in
  `census.py` with the reason — they are the probe's, not the architecture's.

### To A58 (driver-predicate-counters) / A59 (driver-predicate-mode)

- **One line, in `process/core/_idf_probe_modules.py::summary()`**, beside the `writes_by_node`
  entry that is already there:
  `"reads_by_node": {n: sorted(f"{a}.{b}" for a, b in v) for n, v in _reads_all.items()}`.
  It would record, per node, the names of the data-structure fields that node read — the instrument
  already collects them in `_reads_all` and reports only their count. With it the harness reads the
  instrument's *report* instead of its state, which is where a stable interface belongs. Nothing in
  this task depends on it landing; `census.py`'s docstring carries the same note.
- **A59**: `artifacts.check` already tests for `predicate_mode` on the artifact preamble and records
  *not stamped* with A59 named as its owner. When the field is written, the row reports the value
  and no code changes.

---

## 11. Change log

- **2026-09-10** — task opened on branch `A51-harness-artifacts` at `f1f90c20`.
- **2026-09-10** — `763c5dae`: `harness/artifacts.py` (the measured ledger, the harvest-identity
  refusal, three teeth) and `harness/input_files.py`'s derivation (the three-line edit, the input
  file parser, four teeth).
- **2026-09-10** — `f03d313d`: `harness/census.py` (the runtime census and its three comparisons),
  `harness/postsolve.py` (the class-level classifier), and the additive census entry point in
  `harness/pool.py`.
- **2026-09-10** — `7c2b6899`: the four artifact stages on `experiment_runner.py --artifacts`, and
  the preflight's artifact half replaced by `artifacts.check`.
- **2026-09-10** — `bde0b338`: a census resumes only on a census matching the job.
- **2026-09-10** — `c30917d8`: after the first recorded census run, the read-census comparison gains
  the construction that binds and the scan rule is checked against the driver's own (§5.4).
- **2026-09-10** — `c63d720f`: `harness/README.md` section 12.
- **2026-09-10** — `d4c97e6b`: the coupling-state artifact's harvest identity reaches the run record
  (§5.5).
- **2026-09-10** — `2926449f`: the dead-branch function list's disagreement with the source is
  reported in the stage's notes rather than left in the record (§6.3).
- **2026-09-10** — the whole chain re-run from a clean run directory at `2926449f`; every figure in
  §§3–7 is from that run, except §6.5, which is a separate invocation of the same stage at the same
  commit.

---

## 12. Orchestrator's critical assessment (protocol §5) — 2026-09-10

*Appended by the orchestrating session before merge, against the report at `e1a74aaf` and the
stages on the same branch. The chain was re-run by the orchestrator, not read off the report.*

**Verified independently.** (1) `experiment_runner.py --artifacts all` re-run from a clean run
directory on this branch: `check` PASS on every row (93 checks, 0 failed); `derive-inputs` PASS —
both lifted input files byte-identical to the committed digests, `st_regression` recorded not
applicable; `census` PASS — 22/22, 23/23, 21/21 node write sets identical, 862/868/843 fields with 0
differences in either direction, 5/5 block subsets on each; `per-run` PASS — the class-level
classifier reproduces every committed deferral set on all five (configuration, input file) pairs,
same nodes, same order, same digest; **11 of 11 teeth tripped**. (2) Scope: nine files — the four
stage modules, the runner's stages, `pool.py` (+27, a third child entry point), `predicate.py`
(+13, the `harvest` key), the README's appended section and this report; nothing under the copy or
the repository-root `process/`. (3) Composition with A56 (driver-renames), which merged while this
task ran: the only file both branches changed is the README, in disjoint regions; no literal switch
name appears in the four new modules; the one driver function called by name
(`caller._predicate_read_fields`) survived the rename, and the renamed one
(`_post_solve_nodes` → `_defer_per_run_nodes`) is mentioned only in a heritage docstring. The chain
is re-run on the merged tree at the merge; the result is recorded in the queue row.

**Endorsed.** The reachability layer as a source scan of the tree under test rather than a live read
of the sibling's export (trap T9), with the three closure exclusions counted and named per run
rather than applied quietly — and the necessity of the third established by the disagreement it
removes. The read-census finding handled correctly: the cause (`numerics.i_figure_merit` read at the
driver's own call site, written by no node) established before the check changed, both constructions
published, the binding one restricted to fields a node writes, every excluded read named.
`compare_with_driver` as the pattern for an inherited criterion — the harness's restatement agrees
with the driver's own function 215/215 on all three configurations, measured in a child that asserted
the tree. The lifted input file's third line measured by one `AR` evaluation and confirmed by the
digest, which makes the derivation a reproduction and not a transcription. The `harvest` key fix in
`predicate.py`: a one-word additive change in another task's file, flagged rather than folded in.

**Limits I hold it to.** (a) The per-run classifier reproduces the committed sets from a different
reachability source than the one that produced them; agreement is strong evidence, not identity of
method, and the report says so (§6.5). (b) The read census is read from the instrument's state, not
its summary; the one-line driver addition that would make it a stable interface is A58's, and until
then the census depends on an internal of the probe module. (c) The dead-branch function list is a
transcription re-checked against the source on every run; two of its eleven names do not exist at
this commit and exclude nothing. (d) The `check` stage's count differs by two depending on whether
the derivation has run (93 vs 95); the condition is stated.

**Consequences drawn (orchestrator, today).** A58 (driver-predicate-counters) takes the one-line
`reads_by_node` addition to `_idf_probe_modules.summary()` and `census.py` then reads the report,
not the state. A52 (harness-gates) promotes `StageCheck` with `selfcheck.Check` into `Gate`/`Tooth`
and takes G4's per-namespace set from `postsolve.derive` (`vacuum`, `water_use`, `costs`; `pulse` on
`st_regression`). A55 (harness-smoke) uses `--census-entry evaluation` for the smoke pass.

**Verdict.** Fit to merge; nothing returned. Every committed artifact the experiment reads is now
validated by rebuilding what it claims about itself and reproduced by a derivation this repository
can run.
