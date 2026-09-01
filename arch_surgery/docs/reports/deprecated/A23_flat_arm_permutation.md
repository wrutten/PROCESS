> **Document status** — **ARCHIVED · FINDINGS CURRENT**
> The task report for A23 (flat-arm-permutation), merged to `architecture_surgery` on 2026-09-01 at
> experiment base commit `c0ae5b28`. **Its position in `deprecated/` records lifecycle, not
> staleness** (trap T3): the 600/600 and 2 400/2 400 nulls are current evidence and they are what
> license Phase A's `A0 → A1` to be described as the module grouping alone.
>
> The orchestrator re-derived the gate independently from the four `result.json` artifacts before
> merging: `G2_A0perm_vs_a18` identical on 149/149, 297/297, 144/144 and 10/10 with zero skips,
> `replay_never_entered_caller` true on all four decks, and the sensitivity arms moving 488/600
> (one ULP) and 575/600 (reversed order). No claim was narrowed.
>
> **Read the scope caveat as binding.** This licenses "one transposition of two adjacent nodes is
> inert", never "node order does not matter"; the reversed-order control is the counterexample on
> the same instrument and the same points. See also **V9a** in `DSM_VALIDATION.md`.

# A23 (flat-arm-permutation) — was the flat arm's node order part of what Phase A measured?

| | |
|---|---|
| **Task** | A23 (flat-arm-permutation) — closes a confound in Phase A's headline `A0 → A1` comparison |
| **Branch** | `A23-flat-arm-permutation`, in the isolated worktree `/home/wrutten/projects/PROCESS_surgery/.claude/worktrees/agent-a243d5dd71a75ece2` |
| **Branch point** | `10a38195` on `architecture_surgery` (protocol §13) |
| **Environment** | `PROCESS_surgery_env`; `PYTHONPATH` pinned to this worktree and the **exact** tree asserted in every subprocess (trap T6) |
| **Date** | 2026-09-01 |
| **What ran** | A replay only — **no PROCESS solve, no new harvest, nothing under `process/` changed** |

**Vocabulary, once.** A *node* is one model entry point the driver calls directly; the *node
order* is the sequence in which a given input deck reaches them, measured at run time. *Arm A0* is
Phase A's flat Gauss-Seidel control and *arm A1* its block Gauss-Seidel treatment. A *design
point* is one harvested entry state plus its design vector, replayed outside the optimiser. The
*feed-forward hoist* runs the nodes that feed nothing back once after the fixed point instead of
on every sweep. *Bit-for-bit* means `==` on floats, integers, strings and lists with **no
tolerance applied anywhere**.

---

## 1. Verdict

**The confound is retired. `A0 → A1` is the module grouping alone.**

Arm A0 replayed in the block arm's node order is **identical to A18's recorded A0 on every design
point of every deck** — sweep counts, model-evaluation counts, the converged flag, the
moved-constant list, the full residual trace and the full exit audit, compared bit-for-bit with no
tolerance anywhere.

| | `large_tokamak_nof` | `low_aspect_ratio_DEMO` | `st_regression` | `large_tokamak_eval` | all four |
|---|---|---|---|---|---|
| design points compared | 149 / 149 | 297 / 297 | 144 / 144 | 10 / 10 | **600 / 600** |
| points differing anywhere | **0** | **0** | **0** | **0** | **0** |

The same holds at **every setting A18 recorded arm A0 under** — the hoist on as well as off, and
the τ ladder at 10⁻⁴ and 10⁻⁸ — for **2 400 of 2 400** design-point comparisons in total (§9).

The permutation itself is small and identical on all four decks: **2 of 21 node positions change**
— `physics` moves from index 2 to index 1 and `build` from index 1 to index 2. That is exactly
A3 (build-reorder)'s transposition, arrived at independently by grouping the nodes by module.

**The null is about this transposition, not about node order in general.** A control arm running
the same nodes in **reverse** differs on 575 of the same 600 points, so the harness plainly does
resolve a reordering; the zero above says this particular one is inert, not that the measurement
is blind (§5).

**What this licenses and what it forbids** is set out in §6, because it is the deliverable A21
needs.

---

## 2. The confound, precisely

`arch_surgery/fixedpoint/arms.py` builds the two arms from the same harvested node order by two
different rules.

- `loop_nodes()` filters the **harvested run-time order** and keeps it, so the flat arm runs
  `plasma_geom, build, physics, <TF turn model>, pfcoil, pulse, …`.
- `build_blocks()` **groups the nodes by module**, giving `M1 = [plasma_geom, physics]`,
  `M2 = [build, <TF turn model>, pfcoil]`, `PULSE`, `M3`, `FF`. Concatenated, its blocks run
  `plasma_geom, physics, build, <TF turn model>, pfcoil, pulse, …`.

So Phase A's `A0 → A1` varied **two** things: the module grouping, and a `build`/`physics`
transposition. Nobody named the second while Phase A was built or measured; the orchestrator found
it after A3 merged, by cross-reading A3's diff against A18's `arms.py`.

A3 measured that transposition in the incumbent driver and found it bit-identical and
sweep-count-identical on all four decks. That is strong evidence but not the same measurement:
A3's driver converges on `objf` and `conf` under `np.allclose(rtol=1e-6)` with a two-sweep floor,
while the flat arm converges on the full coupling state `y` under a scaled per-component test with
a floor of one. Two predicates with different sensitivities can disagree about whether a change of
ordering is visible.

**The permuted order is derived, not written down.** `a23_permute.block_order()` calls
`arms.build_blocks()` and concatenates its blocks in `arms.BLOCK_ORDER`. Both arms therefore share
one definition of what the block order is, and the driver asserts the result is a permutation of
the flat order — same node multiset, no repeats — before running anything, so a bug that dropped or
duplicated a node could not masquerade as a null result.

---

## 3. The harvest-reuse licence, which had to be re-derived

A22 (outer-pass-census) licensed reusing A18's harvest by comparing **git tree hashes** of
`process/`, `arch_surgery/fixedpoint/` and the node map between A18's commit and its own base, and
finding them equal. **That test now fails**, and it fails for two reasons rather than the one the
brief anticipated:

- `process/` has changed since A18 — A3 (build-reorder) rewrote three call sites in
  `process/core/caller.py` as a list the caller walks, and A13 (feedforward-hoist) added the
  deferral hook and routed three more call sites through a `_node` helper.
- `arch_surgery/fixedpoint/` has *also* changed since A18, which the brief did not mention: A22
  added `a22_census.py`, `a22_tables.py`, `run_a22.py` and two optional parameters to `engine.py`.

So the underlying question has to be answered directly: **do A18's harvested design points and
recorded model write-sets still describe the models this replay executes?** Five pieces of
evidence, all machine-checked and all recorded in
`arch_surgery/idf_probe/runs/a23/_licence.json` and in each deck's `result.json`.

### 3.1 The harvest commit is read from the harvest, not assumed

Each deck's `harvest/metrics.json` records the tree and commit the harvest ran at. They are not
all the same commit, which is exactly why this is read rather than assumed:

| deck | harvest commit | model calls harvested | design points |
|---|---|---|---|
| `large_tokamak_nof` | `7d5c1c03` | 2 029 | 149 |
| `low_aspect_ratio_DEMO` | `595bccba` | 4 286 | 297 |
| `st_regression` | `595bccba` | 1 891 | 144 |
| `large_tokamak_eval` | `ad4e4536` | 29 | 10 |

### 3.2 Which files under `process/` differ, and whether any is a model

Comparing each harvest commit against this branch's HEAD:

| harvest commit | files changed under `process/` |
|---|---|
| `7d5c1c03` | `process/core/_idf_probe_harvest.py`, `process/core/caller.py` |
| `595bccba` | `process/core/caller.py` |
| `ad4e4536` | `process/core/caller.py` |

Positively, and separately: the git tree hashes of **`process/models/`, `process/core/solver/` and
`process/data_structure/` are identical** to the harvest commit's in all three cases. So **not one
model changed**, and neither did the constraint, iteration-variable or objective code the engine
calls. That is the substance of the claim; the file list is the audit of it.

The test is framed as an **exemption list, not a whitelist of replay paths**: any changed file not
named with a reason in `run_a23.EXEMPT_CHANGED_FILES` fails the licence. A whitelist would let a
file nobody thought about pass by failing to match a prefix.

### 3.3 The rewritten call sites are not on the replay's execution path — measured, not assumed

The brief's warning is right and matters: if `caller.py` is off the replay's path, then **A3's and
A13's bit-identical gates do not by themselves license this reuse**, because they gated a path
this task does not use. The licence rests on §3.2's file-level disjointness instead — and on a
direct measurement rather than on reading the code.

`a23_permute.py` wraps `Caller.call_models`, `Caller._call_models_once` and `Caller._node` with
counters before `SingleRun` is constructed, and records the totals. On all four decks:

- entries after `SingleRun.__init__`: **0**
- entries after the whole replay: **0**

The replay resolves each node to its own `run()` and calls it directly, so the driver whose call
sites A3 and A13 rewrote is never entered. This is now a number in every result file rather than
an argument.

### 3.4 Both architecture switches are at their upstream defaults

A13's hoist is off unless `PROCESS_ARCH_HOIST` is set and A3's sequence is upstream unless
`PROCESS_ARCH_SEQUENCE` is set. The runner strips both from the subprocess environment; the
replay refuses to start if either is set, **and** additionally asserts the values `caller.py`
actually resolved at import — `SEQUENCE_NAME == "upstream"`, `HOIST_NAME == "off"` — which are
recorded in every result file. Asserting the resolved value rather than the environment variable
is the stronger check: it would catch a default that had been changed in the source.

### 3.5 The coupling-state record is bound to the harvest by content hash

`arch_surgery/docs/data/` — the committed DSM node map and the per-scenario coupling-state
categorisation and scales — is **unchanged since A18 committed it** (`569fcc4f`, the last commit to
touch that path). More strongly, each replay recomputes the harvest's content hash and compares it
with the one stored in `ystate_<scenario>.json`; all four report `OK`. The scales decide which
components are excluded from the convergence test, so a record silently paired with a different
harvest would make every arm declare a convergence that had not happened, with no symptom.

The harvest is copied into this tree before use, because that record identifies it by a path
relative to the tree as well as by content; the source and copy digests are compared and must
agree.

### 3.6 And the empirical half, which is the strongest of the five

Arm A0 was re-run in **A18's own node order** and compared against A18's recorded A0 the same way
the permuted arm is. It is identical on **600 of 600** design points. Had any model the replay
executes moved under the harvest, this would not be zero.

**Conclusion: the reuse is licensed**, on documentary and empirical grounds that are independent
of one another.

---

## 4. Method

For each deck separately — never pooled — one fresh subprocess with its own working directory
replays A18's harvested design points through two flat arms:

| arm | node order | role |
|---|---|---|
| `A0` | `arms.loop_nodes` — A18's order | reproduction gate, and §3.6's licence evidence |
| `A0perm` | `arms.build_blocks` concatenated | the measurement |

Everything else is held to what `replay.py` does for arm A0: `solve_flat` with floor 1, the same
tolerance, the same DSM cross-check subset, the entry state restored and verified field by field
before each arm, and the exit audit run over the **hoist-off** node set so it is identical across
arms. `restore` reported **0** mismatched fields in total, and there were **0** arm errors.

Three comparisons are made, each per design point and bit-for-bit:

- **G1** — our `A0` against A18's recorded `A0`.
- **G2** — our `A0perm` against A18's recorded `A0`. *This is the question.*
- **G3** — our `A0perm` against our own `A0`, inside one process. Independent of A18's file, so a
  defect in reading that file could not make the headline look null.

Compared quantities, in three families: the **counts** (`valid`, `converged`, `cap_hit`, `sweeps`,
`module_sweeps`, `node_calls`, `outer`, `cross_converged_at`, `hoist_tail_node_calls`, and the
sorted moved-constant list); the **residual trace** at *every* sweep (`max`, `argmax` name,
`n_above`, `n_discrete_mismatch`, `n_constant_moved`, `n_nan_new`); and the **exit audit**
(`objf`, constraint L2 and L∞ both at termination and after one further sweep, the audit's own
residual, its node-call count and its named field lists).

Every comparison carries its denominator and **requires `n_compared == n_points`** before it can
report a pass, so a comparison that quietly skipped points cannot publish a zero over a smaller
population (trap T11), and an empty set cannot pass vacuously.

**The denominator below the design points.** At τ = 10⁻⁶ with the hoist off, arm A0 takes
451 + 952 + 495 + 25 = **1 923 sweeps** over the 600 design points, so each of G1, G2 and G3
compares **600 count tuples** of 10 quantities, **1 923 residual-trace rows** of 6 quantities and
**600 exit audits** of 18 quantities — about **28 300 quantities per comparison**, none of them
under a tolerance. "0 points differing anywhere" is a zero over that population, not over the
600 alone.

---

## 5. The gate is capable of failing (protocol §12)

Three checks, all run on the same data as the headline.

**5.1 The comparator, perturbed field by field.** One point's own record is copied and perturbed by
the smallest amount that should register — **one ULP** on each compared float, **+1** on each
compared integer, the converged flag flipped, one `argmax` name changed, one name appended to the
moved-constant and above-tau lists. Twenty perturbations; the comparator caught **20 of 20** on
every deck, with **0 skipped** (a field that could not be perturbed in that record would be
reported as skipped, never counted as caught).

**5.2 The pipeline, perturbed by one ULP.** Arm `A0ulp` is arm `A0` with **one component of the
design vector** advanced by one ULP. The design vector is the right thing to nudge because
`Sweeper.inject` re-imposes it at the head of every pass, so the perturbation cannot be silently
overwritten by the first model that happens to write the same field — nudging a state field
instead risks a false negative that would look like insensitivity.

| deck | points differing / compared | families touched |
|---|---|---|
| `large_tokamak_nof` | 129 / 149 | trace 107, audit 113 |
| `low_aspect_ratio_DEMO` | 222 / 297 | trace 210, audit 222 |
| `st_regression` | 127 / 144 | trace 88, audit 122 |
| `large_tokamak_eval` | 10 / 10 | counts 1, trace 9, audit 8 |
| **all four** | **488 / 600** | — |

A change of one last bit in one input is resolved on **488 of 600** design points. The remaining
**112** are unmoved, and it is worth being exact about why rather than inventing a reason: the
compared quantities are *summaries* — a maximum, a count above τ, a vector norm — and a real
perturbation can round to the same double in all of them. It is not a property of the points'
difficulty: the 112 are spread across every sweep count (1: 6, 2: 14, 3: 58, 4: 28, 5: 6), not
concentrated on points that converge immediately. **The comparator's own resolution is settled by
§5.1**, which perturbs those summaries directly and catches every one; §5.2 measures how often the
engine turns one input bit into a visibly different summary, which is a different and weaker
question.

**5.3 A reordering that is *not* inert.** This is the check that makes the headline mean anything.
Arm `A0rev` runs the same nodes in **reverse**, at τ = 10⁻⁶ with the hoist off:

| deck | points differing / compared |
|---|---|
| `large_tokamak_nof` | 149 / 149 |
| `low_aspect_ratio_DEMO` | 284 / 297 |
| `st_regression` | 133 / 144 |
| `large_tokamak_eval` | 9 / 10 |
| **all four** | **575 / 600** |

With the hoist on the same control gives 564 / 600.

So the flat arm is emphatically sensitive to node order in general. The zero in §1 is a statement
about the `build`/`physics` transposition specifically, and cannot be read as "the engine does not
see ordering".

---

## 6. What this licenses A21 to write, and what it forbids

**Licensed.**

- Phase A's `A0 → A1` comparison **isolates the module grouping**. The sequence permutation that
  `build_blocks` introduces alongside the grouping contributes **nothing** — 0 differing design
  points of 600 at τ = 10⁻⁶ with the hoist off, bit-for-bit, on all four decks reported
  separately; and 0 of 2 400 across all four settings A18 recorded arm A0 under (§9).
- Every A18 quantity derived from arm A0 — sweep distributions, model-evaluation counts, the exit
  audit — is unchanged under the block arm's node order, so the `A0 → A1` deltas may be attributed
  to the grouping without a qualifier about ordering.
- The two arms provably share one definition of the block order, because `A0perm` derives it from
  `build_blocks` rather than restating it.

**Forbidden.**

- **Do not state that node order is immaterial to the flat arm.** Reversing the order changes
  575 of 600 points at τ = 10⁻⁶ with the hoist off, and 564 of 600 with it on. What is inert is one
  transposition of two adjacent nodes, and the claim must be worded that way.
- **Do not extend this to arm A1's internal ordering.** A23 measures the flat arm under the block
  order; it says nothing about reordering *within* a block or about the order of the blocks
  themselves.
- **Do not pool the decks.** Each row above has its own denominator and they are reported
  separately, per D13's per-deck discipline.
- **Do not carry this to Phase B.** Phase B's baseline is PROCESS as shipped (D14c), a different
  driver with a different predicate. A3 covers the incumbent driver; A23 covers the Phase A engine.
  They agree, which is worth saying, but neither substitutes for the other.

---

## 7. Issue I-13, which this work touched but did not change

I-13 records that `arms.hoisted_nodes()` has no figure-of-merit guard, so on `large_tokamak_eval`
Phase A hoists `['water_use', 'costs']` while A13's production hook resolves `['water_use']` alone.

**It does not interact with anything measured here.** Two settings, two reasons.

- **Hoist off — the headline.** `hoisted_nodes()` returns the empty list whenever the hoist is
  off, so it is not consulted at all. `build_blocks` keeps its `FF` block, the feed-forward tail
  appears in the same place in both the flat and the permuted order, and the permutation is the
  same two-node transposition it is on the other three decks.
- **Hoist on — §9's extension.** Here `hoisted_nodes()` *is* consulted, and this run confirms
  I-13 as a measurement rather than a reading: it resolves `['water_use', 'costs']` on **all four**
  decks, `large_tokamak_eval` included, where A13's production hook resolves `['water_use']` alone
  because figure of merit 7 reads `costs.cdirt` and `costs.concost`. The permutation A23 measures
  is unaffected — it is the same `build`/`physics` transposition, now over 19 loop nodes instead of
  21 — and the arm still reproduces A18's hoist-on A0 on 600 of 600 points, because it reproduces
  A18's node set including this defect. **What I-13 says is unchanged: Phase A's `hoist = 1` and
  Phase B's `PROCESS_ARCH_HOIST=feedforward` are not the same architecture on that deck**, and A21
  still owes the reader that sentence.

**Nothing in `arms.py` was changed.** The task's own arm builders are new code in
`a23_permute.py`; `arms.py` is byte-identical to the merged version and is called, not edited.

---

## 8. Autonomous decisions, each with its reversal path

1. **Branch created at `10a38195` after the harness seeded the worktree from upstream `main`
   (I-11, fourth instance).** The worktree arrived at `6df46205` with no `arch_surgery/` directory.
   The check that catches this is the named-tip half, exactly as protocol §13 says: `6df46205`
   *does* descend from the frozen base `c0ae5b28`, so the descent check alone passes on precisely
   the tree it is meant to catch. *Reversal:* none needed; the branch point is recorded above and
   is verifiable with `git merge-base --is-ancestor 10a38195 HEAD`.
2. **An abandoned branch already held the name `A23-flat-arm-permutation`**, checked out in another
   worktree at `4433bc67` — an ancestor of `10a38195`, i.e. strictly behind it, whose only content
   is the queue rows that are already merged. It was renamed to
   `A23-flat-arm-permutation-abandoned-4433bc67` so the required branch name could be used.
   *Reversal:* `git branch -m` back; no commit was lost, and the old ref still exists.
3. **A18's harvests are copied into this tree rather than read in place.** The committed
   coupling-state record identifies a harvest by a tree-relative path as well as by content hash,
   and the in-place path is in another worktree. Source and copy digests are compared and must
   agree. *Reversal:* delete `runs/a23*/<deck>/harvest/`; nothing else depends on the copies.
4. **The comparison was extended beyond the brief to every setting A18 recorded arm A0 under** —
   the hoist on as well as off, and the τ ladder at 10⁻⁴ and 10⁻⁸ — so that the retirement covers
   everything A21 might quote rather than the default alone. *Reversal:* the default-setting result
   in §1 stands alone; §9's rows can simply be dropped.
5. **The τ-ladder passes were run without the sensitivity arms.** The comparator self-test and the
   1-ULP arm are properties of the comparator and the engine, not of τ, and are demonstrated at
   three settings already; running two extra arms over 600 points at each ladder rung would double
   a shared machine's load for a check that cannot come out differently. *Reversal:* rerun with
   `--sensitivity`; the flag is on the same driver.

---

## 9. The other settings A18 recorded arm A0 under

A18 recorded arm A0 at four settings, not one: τ = 10⁻⁶ with the feed-forward hoist off and on,
and the τ ladder at 10⁻⁴ and 10⁻⁸ with the hoist off. The headline in §1 covers the first. The
other three were run the same way so that the retirement covers everything A21 could quote from
arm A0, rather than the default alone.

**All four settings: `A0perm` is identical to A18's recorded `A0` on every design point.**

| setting | reference | points compared | **differing** | A0 sweeps compared |
|---|---|---|---|---|
| τ = 10⁻⁶, hoist off | `replay_tau1e-06_hoist0` | 600 / 600 | **0** | 1 923 |
| τ = 10⁻⁶, hoist **on** | `replay_tau1e-06_hoist1` | 600 / 600 | **0** | 1 885 |
| τ = 10⁻⁴, hoist off | `replay_ladder_tau0.0001` | 600 / 600 | **0** | 1 663 |
| τ = 10⁻⁸, hoist off | `replay_ladder_tau1e-08` | 600 / 600 | **0** | 2 327 |
| **all four settings** | | **2 400 / 2 400** | **0** | 7 798 |

Per deck, the denominators are 149 / 297 / 144 / 10 at every setting; no deck is missing from any
row, and the replay refuses to run a deck whose reference is absent rather than silently omitting
its comparison. The reproduction gate G1 is 0 of 600 at every setting too, so each row carries its
own licence evidence (§3.6). `restore` reported 0 mismatched fields and there were 0 arm errors
throughout.

Two things worth noting rather than burying:

- **The hoist-on run reproduces A18 exactly, defect included.** Its loop has 19 nodes instead of
  21, and `hoisted_nodes()` resolves `['water_use', 'costs']` on all four decks — I-13, confirmed
  by measurement here; see §7.
- **`st_regression` takes 457 sweeps with the hoist on against 495 with it off**, all of the
  difference being the seven numerically degenerate design points I-12 describes. That is A18's and
  A22's result reproduced, not a new one, and it is unaffected by the permutation either way.

The sensitivity arms of §5 were run at the two τ = 10⁻⁶ settings and not on the ladder rungs
(autonomous decision 5, §8).

**Provenance of each pass**, recorded in its own `_licence.json`: the τ = 10⁻⁶ hoist-off pass ran
at commit `5894d1fc` with a clean tree; the other three at `9ff42fbe`. The two ladder passes report
`worktree_dirty: true` — **the only uncommitted path at the time was this report file**, which the
instrument does not read; `arch_surgery/fixedpoint/` and `process/` were at `9ff42fbe` unmodified.
Recorded because a dirty flag that is explained is worth more than one that is quietly suppressed.

---

## 10. What was not done

- **No PROCESS solve and no re-harvest.** Nothing under `process/` was read for anything but its
  git history, and nothing under `process/` was written.
- **No change to `arms.py`, `engine.py`, `replay.py`, `ystate.py` or `nodemap.py`.** The merged
  instrument is called, never edited — including `hoisted_nodes()`, whose defect (I-13) is
  recorded in §7 and deliberately left alone.
- **No timing is used as evidence anywhere in this report.** Every quantity above is a count or a
  bit-comparison.
- **The permuted arm was not given its own exit audit order.** The audit runs over A18's node order
  for every arm, so that a difference in the audit reflects a difference in the terminal state
  rather than a difference in the audit. Auditing `A0perm` in its own order would need a second
  restore and is not something any Phase A number depends on.
- **Arm A1 was not re-run**, and no block-arm quantity was recomputed. A23 changes the flat arm's
  order only; A22 already re-verified A1 against A18 on the same 600 points.
- **`hoisted_nodes()` was not given the figure-of-merit guard** that would make Phase A's hoist and
  Phase B's hook agree on `large_tokamak_eval`. That is I-13's, not this task's.
- **Nothing was merged and nothing was pushed.**

---

## 11. Change log

| | |
|---|---|
| 2026-09-01 | Branch created at `10a38195` after detecting the upstream-`main` seed (I-11). |
| 2026-09-01 | `a23_permute.py` and `run_a23.py` added; harvest-reuse licence assembled and recorded as data. |
| 2026-09-01 | Headline run over all four decks at τ = 10⁻⁶, hoist off: **600 / 600 identical**; three sensitivity checks pass. |
| 2026-09-01 | Extended to the hoist-on setting and the τ ladder: **2 400 / 2 400 identical** across all four settings A18 recorded arm A0 under. |
| 2026-09-01 | A draft explanation of §5.2's 112 ULP-inert points — "they converge in one sweep" — was **checked and found false** (they span every sweep count) and removed rather than published. Recorded here because it is the shape of trap T11 and was caught by measuring the claim instead of asserting it. |
