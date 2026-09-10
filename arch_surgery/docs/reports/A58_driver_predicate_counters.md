# A58 (driver-predicate-counters) — what the convergence test costs, counted

> **Document status** — **OPEN**. Task **A58 (driver-predicate-counters)**, driver change **DR4**
> of the approved V4 harness plan, plus the one instrument line task **A51 (harness-artifacts)**
> handed over. Branch `A58-driver-predicate-counters`, off `architecture_surgery` at `3fcf1697`.
> Every number below was produced by a committed script, named per figure, at the commit named
> beside it. Archived to `deprecated/` at merge; folder position records lifecycle, not validity
> (trap T3).

---

## 1. The words, spelled out once

This report uses a handful of terms this project has settled on. Each is defined here so the
report reads without the queue open beside it.

| term | meaning |
|---|---|
| **configuration** | one optimisation problem: an input file, an objective, a set of iteration variables and constraints. Three of them: `large_tokamak_nof` and `low_aspect_ratio_DEMO` (pulsed) and `st_regression` (steady-state) |
| **arm** | one setting of the driver's switches. `AR`/`BR` are PROCESS as shipped; `A0`/`B0` replace its stopping rule with the coupling-state one; `A1`/`B3` additionally solve the model set as three blocks |
| **coupling state** | the ~840 state fields the in-loop models write and read from each other. The experiment's convergence test is a max-norm over them |
| **predicate** | the convergence test a loop stops on. There are **two** in this experiment and they are not the same test: the **coupling-state** predicate the flat and partitioned arrangements stop on, and **upstream's own** test, which compares the objective and the constraint vector against the previous sweep's |
| **dispatch sweep** | one walk of PROCESS's model sequence — `Caller._call_models_once`. Every arm's loops are made of these |
| **block** | one group of model nodes the partitioned arm solves to its own fixed point before the next group runs. Five labels: `M1`, `M2`, `PULSE`, `M3`, `FF` |
| **deferral** | running a node less often than every sweep: `per_call` (once per evaluation of the model set) or `per_run` (once per run) |
| **gate** | a check that must pass before a number is believed. Its **teeth** are deliberate breaks the check must catch — a check whose failure mode has never been exercised is an assertion, not a measurement (orchestration protocol §12) |
| **G0′** | the physics stays frozen: the models in the experiment's own copy of PROCESS are byte-identical to base commit `c0ae5b28` |
| **G1** | switch neutrality: with every architecture switch unset, the copy after a driver change behaves byte-identically to the copy before it |
| **GR** | the reproduction gate: the rewritten harness reproduces the previous revision's numbers bit for bit |
| **I-20(a)** | a filed finding: on `st_regression` the `PULSE` block is visited by the schedule 570 times per run executing nothing. The user ruled that this is **disclaimed, not repaired** |

---

## 2. Verdict, in one page

**DR4 landed and the counters answer the question they were built for — in the direction opposite
to the hypothesis.**

*Caption: one row per deliverable, with the verdict and where its numbers are. Every gate was run
from a committed script at the commit named; the "before" capture of G1 is the one artifact that
cannot be re-taken, because it was made at the branch point before any edit.*

| | what | verdict | where | at commit |
|---|---|---|---|---|
| 1 | DR4 in the copy: six counters, plus a public name for the sweep total | landed | §3 | `e02d95e4`, corrected in `59d7150f` |
| 2 | the instrument line, and the census reading the report | landed; read sets identical before and after | §4 | `ec900d97` |
| 3 | provenance and the diff view | `copy_gates.py all` PASS; `PROCESS_diff.py` exit 0, 0 unexplained | §5 | `d2094fd2` |
| 4 | the harness: nine record fields where two nulls stood | landed | §6 | `59d7150f` |
| 5a | **G0′** | **PASS** — 77 model files, 76 identical, 1 approved edit, 4 teeth | §7 | `aebe1c67` |
| 5b | **G1** | **PASS** — 0 of 2 341 values, 0 of 51 319 output-file lines, 6 pairs, 4 teeth | §8 | before `3fcf1697` / after `d2094fd2` |
| 5c | **GR after DR4** | **PASS** — 20/20 runs, 270/270 values, 7 teeth | §9 | `d2094fd2` |
| 5d | `--selfcheck` | **PASS** — 6/6 checks; 16 driver counters resolve on the tree under test | §9.2 | `aebe1c67` |
| 6 | the measurement (not a gate) | published | §10 | `aebe1c67` |
| 7 | this report | — | — | — |

**The headline, and it is a negative result for the standing hypothesis.** The V3 report's central
unexplained finding was that the partitioned arm executes 36–55 % fewer model-node evaluations than
the flat control and is 0–15 % *slower* in wall clock, which means a sweep must cost something not
proportional to the nodes it runs. Improvement-list item 3 named the convergence test as the prime
suspect: the flat loop compares the **whole** coupling state on every one of its sweeps, and the
partitioned arm runs 2.1–2.7× as many sweeps.

Counted, the suspect does not fit. At matched configuration and seed, the partitioned arm evaluates
the test **1.86–2.34×** as often but each evaluation is **0.284–0.285×** as wide, and the product —
the components it actually compares — is **0.53–0.67×** the flat control's. **The partitioned arm
does 33–47 % less component comparison in total, not more.** The predicate moves in the *same*
direction as the node calls (0.52–0.65×), not against them, so it cannot be the term that makes a
cheaper arm slower. Whatever the non-node-proportional cost is, this measurement excludes the
convergence test as its carrier. §10.2.

**Two further findings, both measured rather than assumed.**

- **Upstream's stopping test is 30–59× narrower per evaluation than the experiment's.** `BR`
  compares 27.0 / 22.4 / 14.0 values per test against `B0`'s 840 / 846 / 827. Over a whole run the
  predicate-matched control compares **46× / 51× / 91×** as many values as the reference arm does.
  That is the `BR → B0` rung's predicate cost stated in counts for the first time, and it is the
  reason the two predicates are counted separately and never pooled. §10.3.
- **I-20(a)'s empty block is not an `st_regression` peculiarity — the empty *cost* is.** The
  partitioned arm visits **two** empty blocks per evaluation on **all three** configurations
  (`FF` and `PULSE`, 40.00 % of block visits everywhere). What differs is what an empty visit
  costs: on the two pulsed configurations both blocks are empty *of members* and cost **no sweep at
  all**; on `st_regression` the `PULSE` block keeps its member and has it skipped at the call site,
  so the visit costs a **full walk of the model sequence executing nothing** — 570 of them at
  seed 0, **10.84 %** of that run's block sweeps. That reproduces task A43 (st-trust-gap)'s figure
  for the same seed to the digit. §10.4.

**One defect found in my own work and fixed on the branch, reported rather than hidden.** The first
implementation counted a visit as empty when the block's **membership** was empty. That is not
I-20(a): the routing rule moves `pulse` out of the loop at the *call site*, not out of the block, so
the `PULSE` block is visited with its member still listed and membership called that visit
non-empty — the counter would have reported `0` for the very phenomenon it was built to count. It
is now measured on the node counter across the visit. §3.3.

**Nothing needs the orchestrator's decision.** Three things are handed over for the record: the
I-20(a) extension above (§12), that the predicate hypothesis is now closed on counts (§12), and
that G1's exclusion set has grown from 33 names to 43 and should be reviewed by A52 as one set
rather than extended again (§8.3).

---

## 3. The counters: what each one counts, and where it increments

All line numbers are in `arch_surgery/MDA_partitioning_experiment_v4/PROCESS/process/core/caller.py`
at commit `aebe1c67`.

### 3.1 The declarations

*Caption: one row per module-level counter DR4 adds or renames. "Increments at" is the line that
changes it; "0 with every switch unset" says whether the counter is zero in a run of PROCESS as
shipped — two of them are not, and that is deliberate. All are plain integer increments: none
touches a float and none changes a branch a result depends on.*

| counter | declared | increments at | counts | 0 with every switch unset |
|---|---:|---:|---|---|
| `PREDICATE_EVALUATIONS` | 865 | 1479 | evaluations of the coupling-state test in the solve phase — one per block-loop sweep that reaches its test | yes |
| `COMPONENTS_COMPARED` | 872 | 1480 | summed over those, the components each test walked | yes |
| `PREDICATE_EVALUATIONS_BY_BLOCK` | 877 | 1481 | the same, per block label | yes |
| `COMPONENTS_COMPARED_BY_BLOCK` | 878 | 1484 | the same, per block label | yes |
| `BLOCK_VISITS` | 883 | 1443 | visits the block schedule made to each block | yes |
| `EMPTY_BLOCK_VISITS` | 904 | 1434 | of those, the visits that executed **no model node** | yes |
| `EMPTY_BLOCK_SWEEPS` | 913 | 1437 | dispatch sweeps spent inside those empty visits | yes |
| `UPSTREAM_PREDICATE_EVALUATIONS` | 919 | 1674 | evaluations of **upstream's** stopping test in the solve phase | **no** — it counts the loop upstream already runs |
| `UPSTREAM_COMPONENTS_COMPARED` | 927 | 1675 | summed over those, the values each actually compared | **no**, same reason |
| `DISPATCH_SWEEPS` | 731 | 1883 | sweeps of the model sequence over the whole run | **no** — the cell already existed and already incremented; only its *name* is new |

### 3.2 The coupling-state predicate, and how wide a test is

The block schedule's only convergence test is `spec.residual(y_prev, y, subset=subset)` at
`caller.py:1477`, inside the inner loop of every iterated block. The flat arrangement is the same
code with one block holding every in-loop node, so the flat loop's stopping test and each block
loop's are the **same call site** — which is why one counter covers both.

How many components a test walks is resolved once per block, at `caller.py:1469`:

```python
width = len(subset) if subset is not None else len(spec.keys)
```

`subset` is the block's own write set, taken from the committed per-configuration artifact. The
flat arrangement's single block has no entry in that artifact, so `subset` is `None` and the test
walks the whole coupling state. That is exactly the definition the predicate itself uses:
`ystate.YSpec.subset_indices` returns `range(len(self.keys))` for a `None` subset and the sorted
subset otherwise, and `_residual_aligned` walks precisely those indices. **The counter is the loop
bound, not an estimate of it.**

### 3.3 Empty is measured on the node counter — a defect found and fixed

The first implementation (`e02d95e4`) counted a visit as empty when the block's **membership** was
empty:

```python
if not nodes:
    EMPTY_BLOCK_VISITS[label] = EMPTY_BLOCK_VISITS.get(label, 0) + 1
```

That is a different quantity from I-20(a), and on the phenomenon I-20(a) filed it reports zero. The
routing rule demotes `pulse` to run once per run rather than every sweep, and it does that **at the
call site** — `Caller._node` drops the call — not by removing the node from its block. So on
`st_regression` the `PULSE` block is visited with `nodes == {"pulse"}`, a sweep is charged for it,
and nothing runs. Membership called that visit non-empty.

Measured on the first smoke run at `e02d95e4` (`st_regression`, `B3`, seed 0): `empty_block_visits`
reported `{"FF": 570}` and the node census showed `pulse` executing **2** times in the whole run
against 570 visits to its block. The counter was built to find that and did not.

The fix (`59d7150f`) measures the node counter across the visit — `caller.py:1431-1439`, called at
the three exits of the schedule loop:

```python
def close_visit(label, nodes_before, sweeps_before) -> None:
    if NODE_CALLS[0] != nodes_before:
        return
    EMPTY_BLOCK_VISITS[label] = EMPTY_BLOCK_VISITS.get(label, 0) + 1
    spent = DISPATCH_SWEEPS[0] - sweeps_before
    if spent:
        EMPTY_BLOCK_SWEEPS[label] = EMPTY_BLOCK_SWEEPS.get(label, 0) + spent
```

**And the two kinds of empty visit are kept apart, because they cost different things.** A block the
per-call deferral has emptied of members costs **no** sweep. A block whose members are all skipped
at the call site costs a full walk of the dispatch body — the design-vector injection at its head,
the switch dispatch through every call site, the arrangement method if it is on — executing no
model. Publishing one number for both would charge the free case as if it cost a sweep, which is
this project's trap **T11** inside its own measurement. `EMPTY_BLOCK_SWEEPS` is the cost;
`EMPTY_BLOCK_VISITS` is not.

### 3.4 Upstream's test, counted exactly

`caller.py:1673-1676`:

```python
_objf_agrees = self.check_agreement(objf_prev, objf)
UPSTREAM_PREDICATE_EVALUATIONS[0] += 1
UPSTREAM_COMPONENTS_COMPARED[0] += 1 + (len(conf) if _objf_agrees else 0)
if _objf_agrees and self.check_agreement(conf_prev, conf):
```

Three points, each deliberate.

**Why count it at all.** The plan's check 5 publishes the predicate's cost *per arm*, and the arms
include the reference. Had only the coupling-state predicate been counted, `AR` and `BR` would have
shown `0` — a number that is true of *that* predicate and false of the run, since the reference arms
plainly do evaluate a stopping test. A zero that a reader would read as "this arm's convergence test
is free" is worse than no row.

**Why the width is exact rather than declared.** The pair short-circuits: if the objective has moved
the constraint vector is never compared. Counting the declared width (`1 + len(conf)`) would
overstate the comparison on exactly those evaluations, without saying so — trap T11's shape. Hoisting
the objective half into a name evaluates it once, in the same order, and lets the count be the width
actually walked. `check_agreement` is a pure comparison over two `np.allclose` calls; nothing about
the branch changes, and gate G1 (§8) is what proves that rather than this paragraph.

**Why it is a separate counter and not the same one.** An arm stops on exactly one of the two tests
and they measure different things over different populations. Pooling them would produce an average
of two quantities no arm ever pays together.

### 3.5 The sweep total, and why it changed name

`_SWEEP_CALLS` already existed and already counted every dispatch sweep of a run. It was private,
because its only consumer differenced it across one evaluation to build the per-evaluation
histogram. The per-sweep-overhead question needs the **run total**, and a harness cannot read a
module's private name without coupling itself to an implementation detail. `DISPATCH_SWEEPS` is the
same cell, the same increment and the same value under a public name; the harness reads it there,
and the self-check refuses a tree that does not expose it.

**The total decomposes, and the stage checks the identity rather than asserting it:**

```
dispatch_sweeps = loop sweeps + output-time loop sweeps + the one sweep
                  the per-run deferral spends at the output path
```

The third term is `write_output_files`' own `caller._sweep_block(x, ps)` — the nodes deferred to
once per run, swept once after the solve-phase counter is frozen. **20 of 20 runs decompose with
residual 0** (§10.5). The exit audit's own sweep is outside the total by construction: the counters
are read **before** the audit runs, so the measurement is not charged to the thing it measures.

---

## 4. The instrument line, and the census reading the report

### 4.1 What changed

`arch_surgery/MDA_partitioning_experiment_v4/PROCESS/process/core/_idf_probe_modules.py:697`, in
`summary()`, beside the `writes_by_node` entry that was already there:

```python
"reads_by_node": {n: sorted(f"{a}.{b}" for a, b in v) for n, v in _reads_all.items()},
```

The census instrument attributes every data-structure read and write to the model node that made it.
Its summary reported each node's **write** set by name but only the **count** of its reads. The
names of the reads are what the deferral routing rule is derived from, so `harness/census.py` was
reaching into the instrument's own module-level `_reads_all` dictionary, from inside the same
process. A51 (harness-artifacts) recorded that as a handover rather than making the change itself,
because a driver change made from a harness task would land outside its own neutrality gate.

`harness/census.py:124-160` now reads the report. A summary that does not carry the key is a
**refusal**, not an empty read set: a census silently reporting that no node read anything would
compare as a pass against nothing.

### 4.2 The before/after comparison — identical read sets

*Caption: the runtime read census, per configuration, taken by the committed stage
`experiment_runner.py --artifacts census` before the change (at `e02d95e4`, reading the
instrument's state) and again after it (at `ec900d97`, reading the instrument's report). One
optimisation census per configuration with the read half of the instrument on. "sha256" is of the
`reads_by_node` mapping, serialised with sorted keys. The population is the whole read census, not
a sample.*

| configuration | node read sets | node-field pairs | sha256 before | sha256 after | identical |
|---|---:|---:|---|---|---|
| `large_tokamak_nof` | 23 | 1 569 | `4324ccfe8a44d608` | `4324ccfe8a44d608` | yes |
| `low_aspect_ratio_DEMO` | 23 | 1 575 | `26dff6a174993cec` | `26dff6a174993cec` | yes |
| `st_regression` | 23 | 1 497 | `644644094548cd85` | `644644094548cd85` | yes |
| **total** | **69** | **4 641** | | | **all identical** |

Beyond the read sets, **every top-level key of `census.json` is equal on all three configurations**,
and the census stage's own comparison is unchanged in both directions: **81 compared, 0 mismatched**
before and after, with the same per-configuration lines (22/22, 23/23 and 21/21 node write sets
identical; 5/5 block subsets identical over 840 / 846 / 827 coupling components).

The refusal path was exercised directly: `census._reads_by_node({"nodes": []})` raises
`CensusError` naming the missing key and the change that added it.

**G1 covers the driver half.** With `PROCESS_IDF_PROBE` unset the whole probe module is a no-op, so
the line cannot affect a measured run — and §8 shows that it does not.

---

## 5. The copy's provenance and the diff view

*Caption: the three `PermittedEdit` rows A58 records in `PROCESS/copy_gates.py`, and what each
covers. `PROVENANCE.json` was regenerated at `d2094fd2` so the recorded hunks and post-edit sha256
of every changed file are what the copy-identity gate compares; a row here is documentation, the
hunks are the check.*

| file | kind | name | what it covers |
|---|---|---|---|
| `process/core/caller.py` | counters | the six DR4 counters | §3 |
| `process/core/caller.py` | rename | `DISPATCH_SWEEPS` | §3.5 |
| `process/core/_idf_probe_modules.py` | instrument report | `reads_by_node` | §4 — **the first permitted edit this file has carried** |

`PROCESS_diff.py` gained four mechanism labels, nine annotation rows and a summary paragraph for the
probe file, with `caller.py`'s own paragraph extended.

**`python PROCESS_diff.py --markdown`, at `aebe1c67`** — the two rows this task touches:

| file | + | − | hunks | serves |
|---|---:|---:|---:|---|
| `process/core/_idf_probe_modules.py` | 10 | 0 | 1 | the census instrument reports each node's read set by name, beside the write set it already reported (1) |
| `process/core/caller.py` | 831 | 473 | 50 | … *(all 20 mechanisms, of which this task's three:)* DR4 counters: how often a convergence test was evaluated in the solve phase, and how many components each one walked (4); `DISPATCH_SWEEPS`: the run's count of sweeps of the dispatch body, under a public name (was `_SWEEP_CALLS`) (4); DR4 counters: the block schedule's visits to each block, and the visits that executed no node (issue I-20a: counted and disclaimed, never repaired) (3) |

*Caption: two rows of the diff view's per-file table. "+/−" are lines against the source commit
`f2dc9243` (against the commit, never a working tree); "hunks" is the file's hunk count; "serves"
names the mechanism each hunk is claimed by, with the number of that file's hunks claiming it in
brackets. Population: all 224 files of the copied package; the four files not listed here carry no
A58 hunk.*

**Exit 0, 0 unexplained hunks, 0 files without a summary.** The tooth still trips: one unclaimed
line appended to a throwaway copy of `process/core/constants.py` is reported `UNEXPLAINED`.

**`python PROCESS/copy_gates.py all`, at `aebe1c67`: ALL GATES PASS.**

| gate | verdict | population | teeth |
|---|---|---|---|
| `copy-identity` | PASS | 224 files, 218 identical, 0 missing, 0 added, 0 unexplained differences | 4, all tripped |
| `frozen-physics` (G0′) | PASS | 77 model files, 76 identical, 1 approved (`pulse.py`, D14(b)), 0 unapproved | 4, all tripped |
| `smoke-import` | PASS | the copy imports and resolves to its own tree | 1, tripped (without `PYTHONPATH` the import lands in the main checkout) |
| `edit-behaviour` | PASS | the added existence check refuses typed where the source raised bare | 1, tripped |

*Caption: one row per gate `copy_gates.py` runs. "Population" is what each compared. A tooth is a
deliberate break the gate must catch; "tripped" means it did.*

---

## 6. The harness follows

### 6.1 The record

`harness/records.py` declares **nine** fields where two nulls-with-a-reason used to stand. All are
`when="always"` and present in **both** phases, so a record of a crashed run carries them too.

*Caption: one row per field the run record gains or redefines. "Shape" is what a finished record
carries. Every one is filled from the driver's own counters by
`child.harvest_predicate_counters`, read **before** the exit audit's sweep.*

| field | shape | what |
|---|---|---|
| `predicate_evaluations` | integer | coupling-state test evaluations, solve phase |
| `components_compared` | integer | components those evaluations walked, summed |
| `block_visits` | `{block: n}` | the schedule's visits per block |
| `empty_block_visits` | `{block: n}` | of those, the ones that executed no model node |
| `empty_block_sweeps` | `{block: n}` | dispatch sweeps those empty visits spent |
| `dispatch_sweeps` | integer | sweeps of the model sequence, whole run |
| `upstream_predicate_evaluations` | integer | upstream's stopping test, solve phase |
| `upstream_components_compared` | integer | values it actually compared, summed |
| `predicate_counters` | block | both predicates split out, the mean test width overall and per block, the empty-visit shares, and a sentence per counter |

**The completeness contract is unchanged in kind and stronger in coverage.** `records.SCHEMA` is the
declaration and `records.assert_complete` refuses a finished record missing any declared field; nine
more fields are now inside that contract. `child.stamp_capabilities_absent` no longer says "this
tree cannot supply it" — it stamps the placeholders the way the output-path fields are stamped, and
its docstring now records that nothing in this tree is unsupplied any more, keeping the function
because the next driver capability will be stamped there in exactly this way.

### 6.2 The registry

`switches.DIAGNOSTIC_READBACKS` names the sixteen module-level counters the driver exposes and every
record carries. They are listed **beside** `REGISTRY`, not in it, and **deliberately kept out of**
`default_readbacks()`.

*The reason is worth stating, because the obvious implementation is wrong.* `default_readbacks()` is
what a record's `resolved_switches` block is built from, and G1 excludes that whole block by name.
Putting a counter there would both duplicate it in the record and **hide** it from the gate. A
counter is not a thing the driver *resolved*; it is a thing the driver *reports*. So a second
accessor, `switches.counter_readbacks()`, adds them for the capability probe, and the self-check
uses it: **16 driver counters resolve on the tree under test, each a declared record field**, and a
tree missing one **fails** the check rather than writing a null a reader could not tell from a run
that stopped early.

---

## 7. Gate G0′ — the physics stays frozen in the copy

Run at `aebe1c67` through the harness gate framework, which executes the one implementation in
`PROCESS/copy_gates.py` by path so there is exactly one criterion and one place to look.

| | |
|---|---|
| **verdict** | **PASS** |
| **population** | 77 files under `PROCESS/process/models/` compared byte for byte against `c0ae5b28` (`git cat-file`, never a working tree), plus the file set |
| **result** | 76 identical; 1 differing — `process/models/pulse.py`, the edit decision D14(b) approved; 0 unapproved differences; 0 model files missing, 0 added |

*Caption: gate G0′'s four teeth. Each is a deliberate break that must make the gate FAIL before its
zeros are accepted; the real tree is never touched — the teeth run against a staged copy.*

| tooth | perturbation | result |
|---|---|---|
| `one_byte_changed` | byte 4 of `vacuum.py`, `'o' → 'O'` | TRIPPED |
| `file_removed` | `process/models/vacuum.py` removed | TRIPPED |
| `file_added` | `process/models/_tooth_added.py` added | TRIPPED |
| `approved_file_changed_further` | byte 4 of the approved `pulse.py` | TRIPPED |

`process/models/` was never opened by this task, and neither was the repository-root `process/`.

---

## 8. Gate G1 — switch neutrality

### 8.1 The construction

Six run pairs: three configurations × two reference arms (`BR`, one optimisation; `AR`, one
evaluation), each composed with the **whole** switch vocabulary cleared — which is the condition G1
is about. Every deterministic leaf of the two records is compared without tolerance, floats through
their hex form, plus PROCESS's own output file line by line. Not a curated field list: a curated
list cannot notice a field nobody thought of.

- **`before`** captured at the branch point **`3fcf1697`**, with the copy's driver verified
  byte-identical to that commit first (`git diff 3fcf1697 -- …_v4/PROCESS/ …_v4/harness/` empty).
  6 runs, all `status: ok`. **It cannot be re-taken.**
- **`after`** captured at **`d2094fd2`**, the final driver commit. 6 runs, all `status: ok`.
- Both sides pinned to audit position `after_run`, and a pair whose records disagree about the
  position **refuses** rather than comparing an audit taken at two different places.

### 8.2 The result

| | |
|---|---|
| **verdict** | **PASS** |
| **record values compared** | **2 341**, of which **0 differ** |
| **record values excluded** | 768, every one matched by a name in the exclusion set, each name carrying its reason |
| **output-file lines compared** | **51 319**, of which **0 differ** |
| **output-file lines excluded** | 45 (date, time, username, file prefix, version string, `git describe`, branch, PROCESS's own runtime) |

*Caption: G1's six pairs. "values" and "lines" are `differing / compared` for that pair. Population:
one run per side per cell, at seed 0, unperturbed, with every architecture switch cleared.*

| arm | configuration | values | output-file lines | verdict |
|---|---|---|---|---|
| `BR` | `large_tokamak_nof` | 0 / 498 | 0 / 16 173 | PASS |
| `AR` | `large_tokamak_nof` | 0 / 333 | 0 / 7 | PASS |
| `BR` | `low_aspect_ratio_DEMO` | 0 / 492 | 0 / 16 434 | PASS |
| `AR` | `low_aspect_ratio_DEMO` | 0 / 320 | 0 / 7 | PASS |
| `BR` | `st_regression` | 0 / 405 | 0 / 18 691 | PASS |
| `AR` | `st_regression` | 0 / 293 | 0 / 7 | PASS |

*Caption: G1's four teeth.*

| tooth | perturbation | result |
|---|---|---|
| `one_value_moved_by_one_ulp` | `values.norm_objf` `0x1.99999999b822dp+0 → …ep+0` | TRIPPED — 1 of 498 values differ |
| `one_output_file_line_changed` | line 17 of `large_tokamak_nof.MFILE.DAT` (the exit code) | TRIPPED — 1 of 16 173 lines differ |
| `missing_before_record` | the comparator pointed at a record that does not exist | TRIPPED — refused, not skipped |
| `captures_audited_at_different_positions` | the two sides audited at different positions | TRIPPED — refused |

### 8.3 The exclusion set: 33 names → 43, and what moved

The set gains **exactly ten** names and nothing else: the nine new record fields, plus the retired
`predicate_counters_null_because` key, which exists only on the earlier side.

*Caption: one row per name added to `gates.VOLATILE_RECORD_PATHS`. "Leaves" is how many record
leaves that name matched across the six pairs. "Value after" says what the later side actually
carries — because two of these are **not zero**, and a reader is owed that.*

| name | leaves | value after | reason |
|---|---:|---|---|
| `predicate_evaluations` | 6 | 0 | null before the counter existed; 0 after, because the reference arms never enter the block path — and 0 is still not null |
| `components_compared` | 6 | 0 | same |
| `block_visits` | 6 | `{}` | the reference arms build no block schedule |
| `empty_block_visits` | 6 | `{}` | same |
| `empty_block_sweeps` | 6 | `{}` | same |
| `dispatch_sweeps` | 6 | the run total | the *count* is not new — the driver always incremented this cell and the sweep histogram it feeds **is** compared value for value on both sides. The record *field* is new |
| `upstream_predicate_evaluations` | 6 | **non-zero** | these runs are the reference arms; they stop on upstream's own test |
| `upstream_components_compared` | 6 | **non-zero** | same |
| `predicate_counters` | 156 | the split-out block | absent on the earlier side entirely |
| `predicate_counters_null_because` | 6 | absent | the sentence explaining the absent counters, present only on the earlier side |
| **total** | **210** | | of 768 leaves excluded overall |

**The compared population went *down* by exactly 18, and that is arithmetic rather than a hope.**
A57 (driver-output-path)'s G1 compared 2 359 values; this one compares 2 341. The difference is
three fields × six pairs: `predicate_evaluations`, `components_compared` and
`predicate_counters_null_because` were *present as nulls on both sides* before this task and were
therefore **compared**; they are now excluded because one side carries a number. Nothing else left
the comparison.

**What still carries the neutrality claim.** The two upstream counters are the only excluded fields
whose value is genuinely non-trivial after the change, and what the test they count *decided* is
compared in full: through the per-evaluation sweep histogram (value for value), through
`node_calls_total` and `node_calls_solve_phase`, through the whole `exit_audit` block, and through
51 319 lines of PROCESS's own output file. A driver whose stopping test had started deciding
differently could not have produced 0 there.

**For A52 (harness-gates):** the set is now 43 names and should be reviewed as one set, not
extended again. Ten are this task's, listed above with their leaf counts.

---

## 9. Gate GR after DR4, and the self-check

### 9.1 GR

```
python experiment_runner.py --gate reproduction \
    --lifted-from /home/wrutten/projects/PROCESS_surgery/arch_surgery/MDA_partitioning_experiment_v3/runs/_decks
```

Run at **`d2094fd2`**. **PASS.**

| | |
|---|---|
| **runs reproduced** | **20 / 20** |
| **compared values identical** | **270 / 270** (0 mismatched) |
| **population** | 20 runs (14 optimisations + 6 evaluations) over 3 configurations; 270 compared values, no tolerance on any of them |
| **record contract** | 20 / 20 records carry every declared field — including the nine new ones |
| **coverage substitutes** | `A0p` PASS (2 pulsed configurations, 1 skipped with the reason recorded); `AR` PASS (3 configurations × 4 values = 12 compared values, no tolerance) |

*Caption: GR's seven teeth. Every one is a deliberate break that must make the gate fail, refuse or
raise before its zeros are accepted.*

| tooth | result |
|---|---|
| count — one reproduced count raised by one | TRIPPED |
| hex — one character appended to `exact.norm_objf` | TRIPPED |
| missing reference — a reference file that does not exist | TRIPPED, FAIL not skip |
| missing key — a record with `node_calls_solve_phase` removed | TRIPPED, FAIL not skip |
| bad name map — asking for `BR` without the previous revision's map | TRIPPED, RAISE |
| composition — `B3` run with `PROCESS_ARCH_MDA=flat` | TRIPPED — 7 of 15 compared values differ |
| attempt summation — per-attempt costs that do not add up | TRIPPED, REFUSED |

**The counters moved nothing.** That is the claim GR is here to make about DR4, and 270/270 is what
makes it.

### 9.2 `experiment_runner.py --selfcheck`

**PASS**, 6 of 6 checks, at `aebe1c67`. The two lines this task changed:

- *capability*: `10 composed switch term(s) resolve every readback the registry names, on the tree
  under test` — unchanged — and, new, `16 driver counter(s) resolve on the tree under test, each a
  declared record field`.
- every tooth of every check still trips; the check's own expectations were not moved to make it
  pass.

---

## 10. The measurement — the per-sweep overhead, counted

Not a gate. Produced by the committed stage `python -m harness.gates predicate-counters` at
`aebe1c67`, which runs nothing and reads GR's records. Record:
`runs/gates/predicate_counters/measurements.json`.

### 10.1 The table

*Caption: one row per run of gate GR at commit `d2094fd2` — **20 runs, all finished**, one seed
each, so **no figure here is a campaign statistic and none is quoted as one**. "stops on" is which
of the two predicates that arm's loops use; the evaluation, component and width columns are that
predicate's. "sweeps" is dispatch sweeps over the whole run (analysis loop, block sweeps and output
path; the exit audit's own sweep is excluded by construction). "width" is components compared ÷
evaluations — the average number of components one test walked. "visits" is the block schedule's
visits, "empty" those that executed no model node, "e.sweeps" the dispatch sweeps those empty visits
spent. **Empty block visits are INCLUDED in every visit and sweep count in this table**; on
`st_regression` the `PULSE` block is visited once per evaluation with its member skipped at the call
site, which the user ruled stays and is disclaimed rather than repaired (I-20a).*

| configuration | arm | seed | stops on | sweeps | evaluations | components | width | visits | empty | e.sweeps |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| `large_tokamak_nof` | `A0` | 1 | coupling state | 6 | 6 | 5 040 | 840.0 | 1 | 0 | 0 |
| `large_tokamak_nof` | `A1` | 1 | coupling state | 13 | 12 | 2 895 | 241.2 | 5 | 2 | 0 |
| `large_tokamak_nof` | `BR` | 0 | upstream's objective/constraint test | 2 029 | 1 397 | 37 719 | 27.0 | 0 | 0 | 0 |
| `large_tokamak_nof` | `B0` | 0 | coupling state | 2 071 | 2 069 | 1 737 960 | 840.0 | 630 | 0 | 0 |
| `large_tokamak_nof` | `B1` | 1 | coupling state | 2 102 | 2 100 | 1 764 000 | 840.0 | 660 | 0 | 0 |
| `large_tokamak_nof` | `B3` | 0 | coupling state | 5 502 | 4 839 | 1 156 926 | 239.1 | 3 300 | 1 320 | 0 |
| `large_tokamak_nof` | `B3` | 1 | coupling state | 5 499 | 4 836 | 1 156 225 | 239.1 | 3 300 | 1 320 | 0 |
| `low_aspect_ratio_DEMO` | `A0` | 1 | coupling state | 5 | 5 | 4 230 | 846.0 | 1 | 0 | 0 |
| `low_aspect_ratio_DEMO` | `A1` | 1 | coupling state | 13 | 12 | 2 919 | 243.2 | 5 | 2 | 0 |
| `low_aspect_ratio_DEMO` | `BR` | 0 | upstream's objective/constraint test | 4 286 | 3 044 | 68 069 | 22.4 | 0 | 0 | 0 |
| `low_aspect_ratio_DEMO` | `B0` | 0 | coupling state | 4 139 | 4 137 | 3 499 902 | 846.0 | 1 240 | 0 | 0 |
| `low_aspect_ratio_DEMO` | `B1` | 1 | coupling state | 3 870 | 3 868 | 3 272 328 | 846.0 | 1 218 | 0 | 0 |
| `low_aspect_ratio_DEMO` | `B3` | 0 | coupling state | 8 765 | 7 712 | 1 855 182 | 240.6 | 5 250 | 2 100 | 0 |
| `low_aspect_ratio_DEMO` | `B3` | 1 | coupling state | 10 185 | 8 964 | 2 156 500 | 240.6 | 6 090 | 2 436 | 0 |
| `st_regression` | `A0` | 1 | coupling state | 6 | 6 | 4 962 | 827.0 | 1 | 0 | 0 |
| `st_regression` | `A1` | 1 | coupling state | 15 | 13 | 3 037 | 233.6 | 5 | 2 | 1 |
| `st_regression` | `BR` | 0 | upstream's objective/constraint test | 1 891 | 1 319 | 18 491 | 14.0 | 0 | 0 | 0 |
| `st_regression` | `B0` | 0 | coupling state | 2 038 | 2 036 | 1 683 772 | 827.0 | 570 | 0 | 0 |
| `st_regression` | `B3` | 0 | coupling state | 5 263 | 4 119 | 970 258 | 235.6 | 2 850 | 1 140 | **570** |
| `st_regression` | `B3` | 1 | coupling state | 31 074 | 24 051 | 5 659 602 | 235.3 | 17 550 | 7 020 | **3 510** |

**What the test compares, by arm.** On the **flat** arms (`A0`, `A0p`, `B0`, `B1`) the block schedule
is a single block holding every in-loop node, that block has no entry in the write-set artifact, and
the test therefore compares **the whole coupling state** — 840 / 846 / 827 components, exactly and
on every evaluation, which is why the width column reads `840.0` with no spread. On the
**partitioned** arms the test is restricted to each block's own write set:

*Caption: per-block mean test width on the partitioned arms, with the number of tests each block's
loop ran, from the same 20 runs. Width is exact per block — a block's write set does not change
during a run — so the mean is the value.*

| configuration | arm | seed | `M1` | `M2` | `M3` |
|---|---|---:|---|---|---|
| `large_tokamak_nof` | `A1` | 1 | 258 (4 tests) | 240 (5) | 221 (3) |
| `large_tokamak_nof` | `B3` | 0 | 258 (1 432) | 240 (1 817) | 221 (1 590) |
| `large_tokamak_nof` | `B3` | 1 | 258 (1 432) | 240 (1 815) | 221 (1 589) |
| `low_aspect_ratio_DEMO` | `A1` | 1 | 259 (4) | 244 (5) | 221 (3) |
| `low_aspect_ratio_DEMO` | `B3` | 0 | 259 (2 243) | 244 (2 852) | 221 (2 617) |
| `low_aspect_ratio_DEMO` | `B3` | 1 | 259 (2 609) | 244 (3 318) | 221 (3 037) |
| `st_regression` | `A1` | 1 | 268 (4) | 216 (6) | 223 (3) |
| `st_regression` | `B3` | 0 | 268 (1 362) | 216 (1 367) | 223 (1 390) |
| `st_regression` | `B3` | 1 | 268 (7 883) | 216 (8 358) | 223 (7 810) |

The three iterated blocks sum to 719 / 724 / 707 components against coupling states of 840 / 846 /
827. The remainder is the two blocks no loop iterates: the committed write sets give `FF` 119 / 120
/ 120 components and `PULSE` **2 / 2 / 0**. That last zero is I-20(a) at its source — on
`st_regression` the `pulse` node writes nothing that configuration's coupling state contains, which
is why the routing rule demotes it and why its block is swept empty.

### 10.2 The hypothesis, settled on counts

*Caption: the flat control against the partitioned arm at matched configuration **and matched
seed** — one run against one run per cell, never a campaign mean, and only where both arms have a
run at that seed. Every column is `partitioned ÷ flat`. "evals" is predicate evaluations, "width"
the mean components per evaluation, "comps" their product (components compared over the run),
"sweeps" dispatch sweeps, "nodes" solve-phase model-node executions. **A comps ratio below 1 means
the partitioned arm does less component comparison than the flat one.**  Population: 5 pairs from
GR's 20 runs.*

| configuration | pair | seed | evals × | width × | **comps ×** | sweeps × | nodes × |
|---|---|---:|---:|---:|---:|---:|---:|
| `large_tokamak_nof` | `B0 → B3` | 0 | 2.339 | 0.285 | **0.666** | 2.657 | 0.646 |
| `large_tokamak_nof` | `B1 → B3` | 1 | 2.303 | 0.285 | **0.655** | 2.616 | 0.636 |
| `low_aspect_ratio_DEMO` | `B0 → B3` | 0 | 1.864 | 0.284 | **0.530** | 2.118 | 0.524 |
| `low_aspect_ratio_DEMO` | `B1 → B3` | 1 | 2.317 | 0.284 | **0.659** | 2.632 | 0.650 |
| `st_regression` | `B0 → B3` | 0 | 2.023 | 0.285 | **0.576** | 2.582 | 0.550 |

**The hypothesis predicted the opposite sign.** Item 3's argument was that the partitioned arm runs
2.6–2.8× as many dispatch sweeps and pays a per-sweep cost the flat arm does not, with the
convergence test the prime suspect because the flat loop compares the whole state on every sweep.
The sweeps ratio is confirmed — 2.12–2.66× here. But the width ratio is a near-constant **0.284–0.285**
(the block partition is a property of the configuration, not of the run), and the product is
**0.530–0.666**. The partitioned arm compares **33–47 % fewer components in total**.

**And it tracks the node calls almost exactly.** The comps ratio and the nodes ratio agree to within
0.02 on four of the five pairs (0.666/0.646, 0.655/0.636, 0.659/0.650, 0.576/0.550) and to 0.006 on
the fifth (0.530/0.524). A cost term that scales with the node calls is not a *non*-node-proportional
term. **The convergence test is excluded as the carrier of the per-sweep overhead**, and improvement
item 3's data gap is closed in the negative.

*What this does not say.* It does not say what the per-sweep overhead **is**, only what it is not.
The remaining per-sweep costs the counters do not resolve are the dispatch body's own work — the
design-vector injection at the head of every sweep, the switch dispatch through every call site, the
arrangement method — plus, on `st_regression` alone, 570 sweeps that execute nothing (§10.4). It
also does not say anything about time: nothing here is a timing and none is implied.

### 10.3 The two predicates, side by side

*Caption: the reference arm against the predicate-matched control, per configuration, at seed 0.
"per test" is the mean number of values one evaluation compared; "over the run" is the total. `BR`
stops on upstream's test over the objective plus the constraint vector; `B0` stops on the
coupling-state test over the whole state. One run per cell. `BR`'s **declared** width is
`1 + n_constraints` = 27 / 26 / 19; the measured width is below it wherever the pair
short-circuits, which is discussed below the table.*

| configuration | `BR` per test | `B0` per test | width ratio | `BR` over the run | `B0` over the run | run ratio |
|---|---:|---:|---:|---:|---:|---:|
| `large_tokamak_nof` | 27.0 | 840.0 | 31.1× | 37 719 | 1 737 960 | **46.1×** |
| `low_aspect_ratio_DEMO` | 22.4 | 846.0 | 37.8× | 68 069 | 3 499 902 | **51.4×** |
| `st_regression` | 14.0 | 827.0 | 59.1× | 18 491 | 1 683 772 | **91.1×** |

This is the `BR → B0` rung's predicate cost stated in counts. It is also the clearest reason the two
predicates are never pooled: a mean over 27 and 840 describes no run either arm makes.

**The gap between `BR`'s measured width and its declared one is itself a measurement.** The pair
short-circuits, so a test where the objective has moved never looks at the constraint vector, and
the declared width is `1 + n_constraints`. Measured against declared: `large_tokamak_nof` **27.00
against 27** — the objective agreed at every one of that run's 1 397 tests, so the loop was held
open by the constraint vector alone; `low_aspect_ratio_DEMO` **22.36 against 26**, the objective
agreeing on 85.4 % of its 3 044 tests; `st_regression` **14.02 against 19**, on 72.3 % of its 1 319.
Counting the declared width instead would have overstated upstream's comparison by up to 36 % on
one configuration, silently — which is why §3.4 counts it exactly.

### 10.4 The empty block visits — counted, disclaimed, and larger than filed

*Caption: one row per run with any empty block visit, from GR's 20 runs. "empty" is visits that
executed no model node; "% visits" is their share of all block visits; "e.sweeps" is the dispatch
sweeps those empty visits spent and "% sweeps" their share of the run's charged block sweeps.
**The visit share is not a cost share** — a visit to a block with no members costs no sweep — **the
sweep share is.** One run per row; the two `B3` rows per configuration are seeds 0 and 1.*

| configuration | arm | seed | visits | empty | % visits | e.sweeps | % sweeps | empty blocks | costing a sweep |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| `large_tokamak_nof` | `A1` | 1 | 5 | 2 | 40.00 | 0 | 0.00 | `FF`, `PULSE` | — |
| `large_tokamak_nof` | `B3` | 0 | 3 300 | 1 320 | 40.00 | 0 | 0.00 | `FF`, `PULSE` | — |
| `large_tokamak_nof` | `B3` | 1 | 3 300 | 1 320 | 40.00 | 0 | 0.00 | `FF`, `PULSE` | — |
| `low_aspect_ratio_DEMO` | `A1` | 1 | 5 | 2 | 40.00 | 0 | 0.00 | `FF`, `PULSE` | — |
| `low_aspect_ratio_DEMO` | `B3` | 0 | 5 250 | 2 100 | 40.00 | 0 | 0.00 | `FF`, `PULSE` | — |
| `low_aspect_ratio_DEMO` | `B3` | 1 | 6 090 | 2 436 | 40.00 | 0 | 0.00 | `FF`, `PULSE` | — |
| `st_regression` | `A1` | 1 | 5 | 2 | 40.00 | 1 | 6.67 | `FF`, `PULSE` | `PULSE` |
| `st_regression` | `B3` | 0 | 2 850 | 1 140 | 40.00 | **570** | **10.84** | `FF`, `PULSE` | `PULSE` |
| `st_regression` | `B3` | 1 | 17 550 | 7 020 | 40.00 | **3 510** | **11.30** | `FF`, `PULSE` | `PULSE` |

**I-20(a) reproduces exactly.** On `st_regression` `B3` at seed 0 the `PULSE` block is visited 570
times executing nothing, each visit costing a full sweep of the model sequence: **570 sweeps, 10.84 %
of that run's 5 259 charged block sweeps.** A43 (st-trust-gap) §7.2 measured 10.84 % on `start000`
and 11.12 % campaign-wide from V3's records; this counter reproduces the first figure to the digit
and gives 11.30 % at seed 1, from a different instrument on a different revision's driver.

**Two things I-20(a) did not say, and both matter for A53's captions.**

1. **The empty `PULSE` block is not peculiar to `st_regression`.** The partitioned arm visits it
   empty on **all three** configurations, and `FF` too, so the empty-visit share of block visits is
   **40.00 % everywhere** — two of five blocks, one visit each per evaluation.
2. **What differs is the cost, and only on one configuration.** On the two pulsed configurations
   both empty blocks are empty *of members* — the per-call deferral moved `pulse` and the
   feed-forward nodes into the tail — so the visits cost **no sweep at all**. On `st_regression` the
   burn time is not lifted, `pulse` stays a member of its block, and the per-run routing rule skips
   it at the call site: the block is swept, and nothing runs.

**So a caption that quotes the 40 % visit share as an overhead would be wrong on every configuration
and badly wrong on two.** The figure to quote is the sweep share: **0 % / 0 % / 10.84–11.30 %**.

Nothing about the schedule was changed. Decision D21 rules the visits stay and are disclaimed;
dropping a block whose membership is empty would change the node weights the whole comparison rests
on.

### 10.5 The sweep total decomposes

`dispatch_sweeps = loop sweeps + output-time loop sweeps + the one sweep the per-run deferral spends
at the output path`. **20 runs checked, 0 that do not decompose** (residual exactly 0 on every one).
The third term is `write_output_files`' own `_sweep_block` over the nodes deferred to once per run,
which lands after the solve-phase counter is frozen. A sweep total nobody can decompose is a total
nobody can attribute, so the stage checks the identity and prints any residual rather than absorbing
it.

### 10.6 Timing

None. No timing appears in this report and none is implied. Every figure above is a count or a
ratio of counts, which reproduce bit for bit; the standing rule (issue I-10 — identical work
measured varying by up to 35 % in CPU-seconds on this machine) is why.

---

## 11. Autonomous decisions, each with the way back

*Caption: one row per decision I took without asking, with what it costs to reverse. None changes a
model, a switch's semantics or an arm's composition.*

| # | decision | why | how to reverse |
|---|---|---|---|
| 1 | **Count upstream's stopping test too**, in its own pair of counters | check 5 publishes per arm, and the arms include the reference; a `0` there would read as "this arm's convergence test is free", which is false | delete the two counters, their two record fields and their two G1 exclusions; the reference rows in §10.1 become blank |
| 2 | **Hoist the objective half of upstream's test into a local** so its width is exact | the pair short-circuits; counting the declared width would overstate the comparison on the evaluations where the objective moved, silently | restore `if self.check_agreement(...) and self.check_agreement(...)` and count `1 + len(conf)` unconditionally, with the overstatement stated |
| 3 | **Measure "empty" on the node counter, not on membership**, and split `EMPTY_BLOCK_SWEEPS` out | membership reports `0` for exactly the phenomenon I-20(a) filed (§3.3); and a free empty visit and a sweep-costing one are different costs | revert to `if not nodes` and drop `EMPTY_BLOCK_SWEEPS`; the `st_regression` finding disappears from the record |
| 4 | **Rename `_SWEEP_CALLS` to `DISPATCH_SWEEPS`** rather than adding a second counter | two cells for one quantity drift; the run total is what the question needs and a harness should not read a module's privates | rename back and revert `child.py`'s one-word read; the value is identical either way |
| 5 | **Keep the counters out of `default_readbacks()`**, adding `counter_readbacks()` for the probe | `default_readbacks()` builds `resolved_switches`, which G1 excludes wholesale — a counter there would be duplicated *and* hidden from the gate | fold `DIAGNOSTIC_READBACKS` into `default_readbacks()` and add `resolved_switches` sub-paths to G1's exclusions |
| 6 | **Publish the measurement from GR's runs** rather than making new ones | they exist at this commit, cover every arm on all three configurations, and are made by the committed run path; new runs would cost an hour and add nothing | point the stage at a campaign root once one exists — it takes `--records`-style redirection through its `root` argument |
| 7 | **Put the per-block detail in a `predicate_counters` record block** and the five plan-named fields at top level | §4.4 names five fields; the detail is what makes them readable, and burying the five inside a block would break the plan's own field names | move the block's contents to top level and add the corresponding G1 exclusions |

---

## 12. Handover

**To A52 (harness-gates).**

- **G1's exclusion set is now 43 names**, ten of them this task's (§8.3, with leaf counts). Review it
  as one set; do not extend it again without the same table. Two of the ten are excluded while
  carrying **non-zero** values on the later side — the upstream predicate pair — and §8.3 says what
  still carries the neutrality claim in their place.
- **The measurement stage is registered but is not a gate.** `python -m harness.gates
  predicate-counters` sits beside `output-path-measurements` in the same CLI and needs the same
  wiring into `experiment_runner.py` that A57 asked for (`--gate output_path`, `g0prime`,
  `switch_neutrality`). It reads records and runs nothing, so it can run at any point after a
  campaign.
- **The self-check gained one criterion**: 16 driver counters must resolve on the tree under test.
  It fails, rather than notes, if one is missing.

**To A53 (harness-tally) — the fields, and the disclaimer that is now measured.**

- **Nine new record fields** (§6.1). For the per-sweep-overhead table of plan §3.5 check 5, the
  columns are `predicate_evaluations`, `components_compared`, their ratio, and `dispatch_sweeps`;
  `predicate_counters.coupling_state_predicate.mean_test_width_by_block` gives the per-block split
  without recomputation.
- **The empty-visit disclaimer has a number now, and it is not the obvious one.** The plan requires
  every per-sweep and per-block caption to state the empty visits. **Quote the sweep share, not the
  visit share**: the visit share is 40.00 % on every configuration and is not a cost, because on the
  two pulsed configurations both empty blocks are empty of members and cost no sweep. The cost share
  is **0 % / 0 % / 10.84–11.30 %** (§10.4). A caption saying "40 % of block visits are empty" would
  be true and misleading on all three.
- **Two predicates, never pooled.** Any table with a `BR` row and a `B0` row in the same predicate
  column is averaging 27 with 840. The record carries them as separate fields for this reason.
- **`components_compared` is a cost column that moves *with* the node calls**, not against them
  (§10.2). If the tally reports a per-sweep overhead term, this is not it.

**To A59 (driver-predicate-mode).** DR5 changes the predicate's **denominator**, not its width, so
`COMPONENTS_COMPARED` should be **unchanged** between `frozen` and `mixed` on any run whose
evaluation count is unchanged — which makes it a free consistency check on the mode trial: a `mixed`
run with no decisive pass must reproduce the `frozen` run's counter exactly. `predicate_mode` is
still the **only** entry in `switches.REGISTRY` with `driver_name = None`, unchanged by this task.

**To A60 (driver-attempts).** Unchanged by this task: `attempts_node_calls_available` is still
`false` on every record and `records.assert_attempt_summation` is still the tooth that refuses a
decomposition which does not add up; GR exercises it. **One pattern worth reusing:** §10.5's sweep
decomposition is the same shape as DR7's summation obligation — an identity the stage *checks* and
prints, rather than an invariant it assumes. It found nothing wrong here, which is the point.

**To the orchestrator — two items for the register, neither a decision I can take.**

1. **I-20(a) should be extended, not corrected.** Its finding stands exactly as filed for
   `st_regression`. What it did not say is that the empty `PULSE` visit happens on **all three**
   configurations in the partitioned arm, and that it costs a sweep on **only one** of them (§10.4).
   The filed share (corrected to 10.84 % by A43) is reproduced here to the digit by an independent
   counter on a different revision's driver.
2. **Improvement-list item 3's data gap is closed, in the negative.** The convergence test is *not*
   the non-node-proportional per-sweep cost: the partitioned arm compares 33–47 % **fewer**
   components than the flat control, tracking its node calls to within 0.02 (§10.2). Item 3 asked for
   this to be settled on counts and it is. What the per-sweep overhead **is** remains open, and the
   remaining candidates the counters do not resolve are named in §10.2.

**Run artifacts (I-14).** Everything this report cites lives under
`arch_surgery/MDA_partitioning_experiment_v4/runs/` — `gates/switch_neutrality/{before,after}`,
`gates/reproduction/`, `gates/predicate_counters/`, `gates/g0prime/`, `gates/frozen_physics/`,
`gates/copy_identity/`, `artifacts/census.json`, `census/`, `a58_census_before/` (the before-change
read census, §4.2) and `a58_smoke/` — and is untracked by design. **Relocate it before retiring the
worktree**; `bin/retire_task_worktree.sh` is what does that and a bare `git worktree remove`
destroys it. Two artifacts **cannot be regenerated**: G1's `before` capture, made at the branch point
before any edit, and `a58_census_before/`, made before the census read the instrument's report.

---

## 13. How to re-run everything in this report

From `arch_surgery/MDA_partitioning_experiment_v4/` with
`/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python`. §2's table names the commit each was
run at. G1's "before" capture is the one exception and cannot be re-taken: it was made at the branch
point `3fcf1697`, before any edit, which is what makes it a *before*.

```
# the copy: is it its source commit plus exactly its recorded edits, and is the physics frozen?
python PROCESS/copy_gates.py all                       # §5
python PROCESS_diff.py --markdown                      # §5 (exit 0, 0 unexplained)
python PROCESS_diff.py --teeth                         # §5 (an unannotated hunk must be caught)

# G0' through the harness gate framework
python -m harness.gates g0prime                        # §7

# G1: the 'before' capture was taken at 3fcf1697 BEFORE any edit; only the rest is repeatable
python -m harness.gates switch-neutrality --capture after
python -m harness.gates switch-neutrality --compare     # §8

# GR: does the rewritten harness still reproduce the previous revision, after DR4?
python experiment_runner.py --gate reproduction \
    --lifted-from /home/wrutten/projects/PROCESS_surgery/arch_surgery/MDA_partitioning_experiment_v3/runs/_decks   # §9.1

# the harness's own declarations against the tree it runs
python experiment_runner.py --selfcheck                 # §9.2

# the measurement (needs GR's runs to exist; runs nothing itself)
python -m harness.gates predicate-counters              # §10

# the census, before/after (§4.2).  The 'after' side is what this command gives now;
# the 'before' side was taken at e02d95e4 and is kept in runs/a58_census_before/
python experiment_runner.py --artifacts census
```

---

## 14. Change log

*Append-only.*

| date | what |
|---|---|
| 2026-09-10 | Gate G1's **"before" capture** taken at the branch point `3fcf1697`, with the copy's driver and harness verified byte-identical to that commit first (`git diff` empty). 6 runs, all `status: ok`. It cannot be re-taken. |
| 2026-09-10 | **`e02d95e4`** — DR4 in the copy: `PREDICATE_EVALUATIONS`, `COMPONENTS_COMPARED` and their per-block companions, `BLOCK_VISITS`, `EMPTY_BLOCK_VISITS`, `UPSTREAM_PREDICATE_EVALUATIONS`, `UPSTREAM_COMPONENTS_COMPARED`, and `_SWEEP_CALLS` renamed `DISPATCH_SWEEPS`. |
| 2026-09-10 | The before-change **read census** taken on all three configurations by `experiment_runner.py --artifacts census` and kept in `runs/a58_census_before/`. |
| 2026-09-10 | **`ec900d97`** — `reads_by_node` in the instrument's summary; `harness/census.py` reads the report. Re-run: read sets identical, 69 node read sets, 4 641 node-field pairs, same sha256 per configuration, every top-level key of `census.json` equal; the stage's own comparison 81/0 both times. |
| 2026-09-10 | **`05323a85`** — the copy's provenance and diff view follow: three `PermittedEdit` rows, `PROVENANCE.json` regenerated, four mechanism labels and nine annotation rows in `PROCESS_diff.py`, a summary paragraph for the probe file. `copy_gates.py all` PASS; `PROCESS_diff.py` exit 0. |
| 2026-09-10 | **Defect found in this task's own counter**, on the first smoke run at `e02d95e4`: `EMPTY_BLOCK_VISITS` measured on the block's *membership* reported `{"FF": 570}` and **missed I-20(a)'s `PULSE` block entirely**, because the routing rule skips `pulse` at the call site rather than removing it from the block. Reported, not hidden (§3.3). |
| 2026-09-10 | **`59d7150f`** — the fix and the harness: empty measured on the node counter across the visit; `EMPTY_BLOCK_SWEEPS` split out because a member-empty block costs no sweep and a skipped-member block costs a full walk; nine record fields; `child.stamp_capabilities_absent` loses its null-with-a-reason lines; `switches.DIAGNOSTIC_READBACKS` and `counter_readbacks()`; the self-check's counter criterion; G1's exclusion set 33 → 43; `harness/README.md` §4.1. |
| 2026-09-10 | **`d2094fd2`** — the `predicate-counters` measurement stage, with the sweep-decomposition identity checked rather than assumed; `PROVENANCE.json` regenerated for the corrected counter. |
| 2026-09-10 | **G0′ PASS** at `d2094fd2` and again at `aebe1c67` — 77 files, 76 identical, 1 approved, 4 teeth. |
| 2026-09-10 | **G1 PASS** — before `3fcf1697`, after `d2094fd2`: 0 of 2 341 values, 0 of 51 319 output-file lines, 6 pairs, 4 teeth; 768 values excluded, 210 leaves of them from this task's ten names; the compared population moved 2 359 → 2 341, which is exactly the three previously-null fields × six pairs. |
| 2026-09-10 | **GR after DR4 PASS** at `d2094fd2` — 20/20 runs, 270/270 compared values, 7 teeth, both §7.5 substitutes PASS, record contract 20/20. |
| 2026-09-10 | **`c17ecc4d`** — the measurement gains the seed column (two rows were indistinguishable) and the flat-against-partitioned comparison the check exists to settle. |
| 2026-09-10 | **`aebe1c67`** — the measurement publishes the empty-visit share that **is** a cost (sweeps) beside the one that is not (visits); `PROCESS_diff.py`'s summary corrected to match what was measured — the empty `PULSE` block is on all three configurations and costs a sweep on one. |
| 2026-09-10 | **`5f51c519`** — this report, and `PROCESS_diff.py`'s `caller.py` summary corrected to say what was measured about the empty block rather than what was assumed. |
| 2026-09-10 | **Everything re-run at the head commit `5f51c519`** and unchanged: `copy_gates.py all` PASS; `PROCESS_diff.py` exit 0 with its tooth tripping; G0′ PASS (77 / 76 / 1); G1 PASS (0 of 2 341 values, 0 of 51 319 lines, 6 pairs); GR PASS (20/20, 270/270, 7 teeth, both substitutes, record contract 20/20); `--selfcheck` PASS 6/6 with 16 counters resolving; the measurement identical, 20 of 20 sweep totals decomposing with residual 0. |
| 2026-09-10 | **Self-check PASS** at `aebe1c67`, 6/6, 16 driver counters resolving. **Measurement published** (§10): the partitioned arm compares **0.530–0.666×** as many components as the flat control while running **2.12–2.66×** as many sweeps, tracking its node calls to within 0.02 — **the convergence test is excluded as the per-sweep overhead's carrier**. `st_regression` `B3` seed 0: **570 empty `PULSE` visits, 570 sweeps, 10.84 % of block sweeps**, reproducing A43 (st-trust-gap)'s figure to the digit. |

---

## 15. Orchestrator's critical assessment (protocol §5) — 2026-09-10

*Appended by the orchestrating session before merge, against the report at `e43ff184` and the copy
and harness on the same branch. Every gate and the measurement were re-run by the orchestrator.*

**Verified independently.** (1) **Gate GR after DR4**, re-run from scratch: 20 of 20 runs, **270 of
270 values identical**, both substitutes PASS, seven teeth tripped. (2) **The measurement stage**
(`python -m harness.gates predicate-counters`) on those fresh records: `st_regression` `B3` seed 0 —
570 empty `PULSE` sweeps, **10.84 %** of the run's block sweeps, 3 510 and 11.30 % at seed 1; the
five flat-versus-partitioned pairs give component-comparison ratios **0.530–0.666** against node-call
ratios 0.524–0.650, widths 0.284–0.285 — the report's numbers to the digit. (3) **G1**
(`switch-neutrality --compare`): 6 pairs, 0 of 2 341 values, 0 of 51 319 output-file lines, four
teeth; the compared population fell by exactly the three previously-null fields × six pairs, and the
exclusion set grew 33 → 43 by exactly the nine new fields plus the retired null-reason key. (4)
**G0′** PASS; `PROCESS/copy_gates.py all` ALL GATES PASS; `PROCESS_diff.py` exit 0 over six files, 0
unexplained; `--selfcheck` six checks PASS with the sixteen driver counters resolving. (5) Scope:
fifteen files — three driver files of the copy (`caller.py`, `_idf_probe_modules.py`; `module_solve.py`
untouched as it turned out), the copy's provenance and diff tooling, the harness files the brief
assigned plus one-line touches in `optimise.py` and `evaluate.py`, the README's registry section and
this report; `models/`, the repository-root `process/` and `experiment_runner.py` untouched; no
conflict with trunk.

**Endorsed.** The defect found and fixed on the branch (§3.3) is the report's most valuable
paragraph: a counter built to find I-20(a) that reported `{"FF": 570}` and missed it, because the
routing rule skips `pulse` at the call site rather than by emptying its block. The corrected
definition — empty means *no node executed*, measured on the node counter across the visit — and the
split into `EMPTY_BLOCK_VISITS` and `EMPTY_BLOCK_SWEEPS`, because a member-empty block costs no
sweep and a skipped-member block costs a full walk, is exactly the distinction that keeps the
disclaimer honest: the visit share is 40 % on every configuration and is not a cost; the sweep share
is 0 / 0 / 10.84–11.30 %. The instrument line landed as A51 specified and the census reads the report
with identical results (69 node read sets, 4 641 pairs). The sweep-total decomposition checked on
every record rather than assumed. Two predicates kept as separate fields so that `BR`'s
27-component test and `B0`'s 840-component test can never be pooled.

**Limits I hold it to.** (a) The measurement is one seed per cell; it settles the *sign* of item 3's
hypothesis on counts and claims nothing about a distribution. (b) The exclusion set is now 43 names,
two of them excluded while carrying non-zero values on the later side (the upstream predicate pair);
A52 reviews the set as one table. (c) What the per-sweep overhead *is* remains open — the candidates
the counters cannot resolve are named in §10.2 — and the plan should carry that as an open question,
not as a closed one.

**Consequences drawn (orchestrator, today).** *Issue I-20(a)* is extended in the register, not
corrected: its `st_regression` share stands (reproduced to the digit by an independent counter); the
empty `PULSE` visit occurs on all three configurations and costs a sweep on one. *Improvement item 3*
is closed in the negative: the convergence test is not the non-node-proportional per-sweep cost; the
partitioned arm compares 33–47 % fewer components, tracking its node calls to within 0.02. *A53
(harness-tally)* quotes the sweep share, never the visit share, in every empty-visit disclaimer, and
never pools the two predicates. *A52 (harness-gates)* wires `predicate-counters` beside the other
stages and reviews the 43-name exclusion set. *A59 (driver-predicate-mode)* uses `COMPONENTS_COMPARED`
as the free consistency check between `frozen` and `mixed`. A59 is dispatched off the merged tip.

**Verdict.** Fit to merge; nothing returned. DR4 lands with neutrality and reproduction intact, and
the first question the counters were built to answer is answered.
