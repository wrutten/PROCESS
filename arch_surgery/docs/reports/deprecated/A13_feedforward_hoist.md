> **Document status** — **ARCHIVED · FINDINGS CURRENT, WITH ONE CLAIM NARROWED**
> The task report for A13 (feedforward-hoist), merged to `architecture_surgery` on 2026-09-01 at
> experiment base commit `c0ae5b28`. **Its position in `deprecated/` records lifecycle, not
> staleness** (trap T3): the three gate tables and the 6.56 / 6.76 / 6.64 / 2.63 % saving are
> current evidence.
>
> **Orchestrator's narrowing of §6.** The sentence "three decks agree to three significant
> figures" claims more than the arithmetic supports. Applying A2's cost model *on A13's own node
> set and unit* computes the tail's share of model evaluations from **this run's own** sweep and
> call counts — the same quantities the gate counted. The exact match is an **algebraic identity,
> not an independent confirmation**: a prediction recomputed from the measurement it is being
> compared against cannot disagree with it. What §6 does establish, and it is worth having, is
> that **the whole apparent 4.6–8.2 % vs 6.6 % gap is accounted for by node set and unit** — A2's
> band includes `Pulse` and weights by DSM rows — leaving **no unexplained residue**. That is a
> reconciliation, and the report should be read as making that claim and not a stronger one. The
> measured numbers stand exactly as reported.
>
> The predicate finding in §4 is the more important result and is not narrowed: the hoistable node
> set **depends on the active figure of merit**, because `objectives.py` reads `costs.coe` (FOM 6)
> and `costs.cdirt`/`costs.concost` (FOM 7).

# A13 (feedforward-hoist) — running the tail once instead of every sweep

| | |
|---|---|
| **Task** | A13 (feedforward-hoist) — the partition's Stage 1b (D12); framework variant point **VP2**, hook **F7b** |
| **Branch** | `A13-feedforward-hoist`, in the isolated worktree `/home/wrutten/projects/PROCESS_surgery/.claude/worktrees/agent-aa8fb4cdc55ab61df` |
| **Base** | `4433bc67` on `architecture_surgery`; experiment base commit `c0ae5b28` |
| **Environment** | `PROCESS_surgery_env`; `PYTHONPATH` pinned to the tree under test and the **exact** tree asserted in every measurement subprocess (trap T6) |
| **Date** | 2026-09-01 |
| **Status** | Complete — **all three gates pass on all four scenarios**, and each was shown capable of failing first |

**Vocabulary, once.** A *sweep* is one execution of `Caller._call_models_once` — one pass over the
model sequence. A *node* is one model entry point that `_call_models_once` calls directly; each of
the four decks reaches **21** of the 26 call sites in the source, the rest being switch-selected.
A *model evaluation* is one invocation of one node. The *feed-forward tail* is the set of nodes
whose outputs nothing earlier in the loop reads. *Bit-identical* means every MFILE line matches
and every MFILE float matches as a hex literal, with **no tolerance applied anywhere**.

---

## 1. Verdict

**The hoist works, changes nothing, and is worth 6.6–6.8 % of model evaluations on the three
optimisation decks and 2.6 % on the evaluation deck.** Deferring the feed-forward nodes out of the
sweep and running them once after the fixed point is reached leaves **every number in the MFILE
bit-identical** to the parent commit, on all four scenarios, and removes between 2.6 % and 6.8 %
of all model evaluations.

| | `large_tokamak_nof` | `low_aspect_ratio_DEMO` | `st_regression` | `large_tokamak_eval` |
|---|---|---|---|---|
| tail resolved at run time | `water_use`, `costs` | `water_use`, `costs` | `water_use`, `costs` | **`water_use` only** |
| model evaluations, hook off | 42 609 | 90 006 | 39 711 | 609 |
| model evaluations, hook on | 39 815 | 83 918 | 37 073 | 593 |
| **evaluations removed** | **2 794** | **6 088** | **2 638** | **16** |
| **as a fraction of the hook-off total** | **6.56 %** | **6.76 %** | **6.64 %** | **2.63 %** |
| sweeps | 2 029 → 2 029 | 4 286 → 4 286 | 1 891 → 1 891 | 29 → 29 |
| MFILE floats differing, hook on vs parent | 0 of 13 559 | 0 of 13 455 | 0 of 13 493 | 0 of 13 487 |
| `ifail` | 1 → 1 | 1 → 1 | 1 → 1 | 1 → 1 |

**The measured saving is *inside* A2's predicted 4.6–8.2 % band on three decks and below it on the
fourth — but the band and the measurement are not over the same node set, and the comparison is
only meaningful once that is said.** A2's arithmetic hoists `Pulse` **and** the feed-forward
module and counts in DSM-row units; A13 hoists the feed-forward module only, because `pulse` is
the articulation point and cannot leave the loop until the burn-time coupler is lifted (C2a).
Section 6 does the conversion. **Corrected to A13's node set and unit, A2's arithmetic predicts
6.56 / 6.76 / 6.64 / 5.25 % and the measurement returns 6.56 / 6.76 / 6.64 / 2.63 %** — agreement
to three significant figures on three decks, and a named, understood shortfall on the fourth.

**The correctness subtlety is real, it bites on one of the four decks, and it is handled.** The
loop's convergence test is the objective function and the constraint residuals. `objectives.py`
reads `costs.coe` (figure of merit 6) and `costs.cdirt` / `costs.concost` (7), all three written by
the `costs` model — a feed-forward node. `large_tokamak_eval` sets no `minmax` and therefore takes
the default figure of merit **7**. On that deck the hook keeps `costs` **inside** the loop and
hoists `water_use` alone; that is why its saving is 2.6 % and not 5.3 %. See §4.

**The `st_regression` outlier that A22 warned about does not appear, and there is a reason.**
Issue I-12's mechanism — a relative convergence test scaled by a median magnitude, tightened
~10¹⁸-fold by a diverging 1990 cost evaluation — belongs to the *fixed-point engine's* state
predicate, not to PROCESS's own driver, whose predicate is the objective and the constraints and
reads no `costs` field on that deck (its figure of merit is −5, fusion gain). `st_regression`'s
sweep count is **unchanged at 1 891** with the hook on, and its saving, 6.64 %, sits between the
other two optimisation decks. The hoist removes I-12's mechanism from A18's engine; it does not
remove anything from the incumbent driver, because the mechanism was never there.

**What this does not license.** The headline for Phase B remains *the proposed architecture*, never
*the partition's benefit* (plan §7a, D15). This 6.6–6.8 % is the hoist alone, measured against
today's driver on today's decks, and it is separable — which is exactly why quoting a combined
Phase B figure as the partition's would be the units error trap T11 records.

---

## 2. Branch point (protocol §13)

**Issue I-11 recurred for the third time.** The worktree was seeded at `6df46205` — upstream
`main`, with no `arch_surgery/` directory in it at all. Verified before the first commit and
corrected by creating `A13-feedforward-hoist` at `4433bc67` on `architecture_surgery`.
`4433bc67` descends from the frozen base `c0ae5b28` (`git merge-base --is-ancestor`, checked).

Note for the queue: the seeded `HEAD` *did* descend from `c0ae5b28`, because `c0ae5b28` is an
upstream commit and `6df46205` is later upstream `main`. **The descent check alone does not catch
I-11.** What caught it was the second half of the brief's check — that the branch point be at or
after the named tip on `architecture_surgery`. Any future brief that keeps only the descent half
will let I-11 through.

---

## 3. What was built

### 3.1 The variant point

`process/core/caller.py` only. **Nothing under `process/models/` was touched**, so no D11 approval
is required. The shape follows A3's VP1: a variant expressed as data, resolved once at import, the
upstream behaviour as the default, and an unrecognised setting raising rather than defaulting.

```
PROCESS_ARCH_HOIST unset (or "off")  -> nothing is deferred; upstream behaviour
PROCESS_ARCH_HOIST=feedforward       -> nodes in DSM module FF are deferred
PROCESS_ARCH_HOIST=<anything else>   -> RuntimeError at import
```

Verified: `PROCESS_ARCH_HOIST=bogus` raises
`RuntimeError: PROCESS_ARCH_HOIST='bogus' is not a recognised hoist setting; expected one of
('off', 'feedforward') (or unset for 'off')` before any model runs.

Three call sites in `_call_models_once` — `pulse`, `water_use`, `costs` — are routed through a
one-line helper, `self._node(name, run)`, which runs the node now or appends it to the sweep's
deferral list. With the hoist off the list is `None` and the helper is a direct call. `call_models`
clears the list each sweep and runs the **last** sweep's list once, immediately after the
idempotence test passes.

### 3.2 The node set is derived at run time (framework C2a)

The hook carries **no hard-coded node list**. It reads the committed DSM node map
(`arch_surgery/docs/data/dsm_node_map.json`, framework C8 — never the dependency-analysis
repository's live exports, trap T9) and takes the deferrable call sites whose module is in the
hoisted set. Today `HOIST_MODULES = {"FF"}` yields `('water_use', 'costs')`; `pulse` is module
`PULSE` and is therefore *not* hoisted. When a later variant point lifts the burn-time coupler,
adding `PULSE` to that set moves `pulse` into the tail with no list edit — its call site is
already deferrable.

**Agreement with `arch_surgery/fixedpoint/arms.py:hoisted_nodes()` was checked, not assumed.**
That function returns `[n for n in node_order if node_module.get(n) == "FF"]`. Evaluated against
the same committed map over the run-time-measured node order (the 21 executing nodes, from the
census), it returns `['water_use', 'costs']` for every one of the four decks — identical to
`caller.HOIST_NODES`. The two derivations share the map but not the code path: `arms.py` filters
a measured node order, `caller.py` filters its deferrable call sites and then cross-checks. The
production hook additionally **raises at import** if the map assigns a node to a hoisted module,
marks it as executing in `_call_models_once`, and no deferrable call site exists for it — so the
`arms.py` set can never silently exceed what the driver can actually defer.

**One asymmetry, stated because it matters for Phase B:** `arms.py` has no notion of the
predicate guard of §4, so on a deck with figure of merit 6 or 7 the production hook hoists a
*subset* of what `hoisted_nodes()` returns. On `large_tokamak_eval` the two differ:
`hoisted_nodes()` gives `['water_use', 'costs']`, the driver resolves `['water_use']`. If Phase B
runs its engine and the incumbent driver on that deck under the hoist toggle, the two arms are
hoisting different sets unless `arms.py` gains the same guard.

### 3.3 Where the hoist does *not* apply — an autonomous decision

The hoist applies to `Caller.call_models` — the optimiser's evaluation path — and **not** to
`Caller.call_models_and_write_output`, the final-output path. Two reasons: that loop's predicate is
the whole MFILE, which contains every tail output, so deferring the tail there would change what
the loop tests; and `models.write` re-enters every model's `run()` from its `output()` anyway
(trap T7), so the tail runs there regardless and there is nothing to save.

Measured consequence: exactly **2** of each deck's sweeps belong to the output path
(2 029 = 2 027 + 2; 4 286 = 4 284 + 2; 1 891 = 1 889 + 2; 29 = 27 + 2), and those two keep the tail
inline. They are in the denominator of every saving figure quoted above.

**Reversal path:** extend the deferral to `call_models_and_write_output` by setting `self._pending`
there as `call_models` does. It is worth at most 2 sweeps × tail size per run — 4 evaluations out
of 42 609 on `large_tokamak_nof`, 0.009 % — and it would put the tail's outputs out of step with
the MFILE idempotence test. Not done, and not recommended.

---

## 4. The correctness question: does the loop's own predicate read the tail?

**It can, and on one of the four decks it does.** This is the question the brief asked to be
settled either way, and it is the only place where the hoist is not a free lunch.

`Caller.call_models` stops when `objective_function(...)` and `constraint_eqns(...)` both agree
with the previous sweep to `rtol = 1e-6`. If a hoisted node writes something either of those
reads, the loop would be testing state the hoist has deliberately stopped updating.

### 4.1 What the tail writes — measured, not read off a call graph

`a13_tail_writeset.py` fingerprints the **whole data structure — 2 288 fields** — immediately
before and immediately after each candidate node, inside a window opened and closed at the
boundary of `_call_models_once` (trap T7) and at nesting depth 0 only. Union over sweeps:

| node | fields written | of which read by `objectives.py` | of which read by `constraints.py` |
|---|---|---|---|
| `water_use` | 8 | **0** | **0** |
| `costs` | 102 (103 on `st_regression`) | **3** — `costs.cdirt`, `costs.coe`, `costs.concost` | **0** |
| `pulse` *(not hoisted; measured for the future arm)* | 2 (0 on `st_regression`) | 1 — `times.t_plant_pulse_burn` | 2 — `times.t_plant_pulse_burn`, `constraints.t_current_ramp_up_min` |

Denominators: 2 288 data-structure fields fingerprinted; `objectives.py` makes **17** distinct
`data.<ns>.<field>` reads and `constraints.py` **212**. Sweeps fingerprinted: 400 of 2 029 / 400 of
4 286 / 400 of 1 891 / 29 of 29 (the instrument caps at 400 and reports the cap).

Two things fall out. First, **no constraint equation reads anything the tail writes**, on any of
the four decks. Second, `pulse` is disqualified for exactly the reason C2a gives: its two writes
are read by both halves of the predicate. That is an independent, run-time confirmation that the
articulation point cannot join the tail until the burn-time coupler is lifted.

### 4.2 Which figures of merit move across the tail — measured

`a13_predicate_probe.py` evaluates **all 16** figures of merit immediately before and immediately
after each tail node and compares them as hex floats. (`objective_function` is a pure read, so
this cannot perturb the run; `constraint_eqns` is *not* pure — it assigns
`data.cs_fatigue.n_cycle_min` — and is deliberately not called, which is why §4.1 answers the
constraint half by name intersection instead.)

| deck | sweeps | figures of merit moving across `water_use` | across `costs` |
|---|---|---|---|
| `large_tokamak_nof` | 2 029 | none | **6, 7** |
| `low_aspect_ratio_DEMO` | 4 286 | none | **6, 7** |
| `st_regression` | 1 891 | none | **6, 7** |
| `large_tokamak_eval` | 29 | none | **6, 7** |

The measured set is exactly the set the hook declares. **One gap in the denominator, stated:**
figure of merit **15** (plant availability factor) raises on all four decks — it requires
`i_plant_availability != 1` and all four decks set the user-input model — so it was evaluated on
**0** sweeps and this test says nothing about it. It is covered instead by §4.1: `objectives.py`
reads `costs.f_t_plant_available` for figure of merit 15, and that field is **not** in the `costs`
model's measured write set (it is written by `availability`, an M3 node that stays in the loop).
The two methods together close the question; neither closes it alone.

### 4.3 What was done about it

The hook resolves its tail **per run** as the arm's node set less any node the active figure of
merit reads. On `large_tokamak_eval` (figure of merit 7, the default, since that deck sets no
`minmax`) it resolves to `['water_use']` and `costs` keeps running inside the loop. On the other
three it resolves to `['water_use', 'costs']`. The resolved tail is recorded in every run's
`metrics.json` and in the node census, so the shrink is visible rather than silent.

**Autonomous decision.** The alternative was to *raise* on such a deck rather than shrink the
tail. Shrinking was chosen because it keeps every deck runnable and keeps the loop's criterion
exactly upstream's, which is what the gate demands; raising would have made the hook unusable on
a deck the study measures. **Reversal path:** turn the filter in
`caller.resolved_hoist_tail` into a `RuntimeError`; one function, four lines. The cost of the
decision is measured and quoted — 2.63 % instead of 5.25 % on that deck — not hidden.

---

## 5. The gates

Three arms, four scenarios, every run a fresh subprocess in its own working directory with
`PYTHONPATH` pinned to the tree under test and the **exact** tree asserted inside the subprocess
(trap T6). `parent` is a `git archive` extraction of `4433bc67` placed outside the worktree, so it
carries no git metadata and cannot be confused with the branch.

### 5.1 Gate 1 — switch-neutrality: hook off vs. parent commit

Reported **per scenario, never pooled**.

| | `large_tokamak_nof` | `low_aspect_ratio_DEMO` | `st_regression` | `large_tokamak_eval` |
|---|---|---|---|---|
| MFILE lines differing | **0** of 16 174 | **0** of 16 435 | **0** of 18 692 | **0** of 15 917 |
| MFILE floats differing (hex literals) | **0** of 13 559 | **0** of 13 455 | **0** of 13 493 | **0** of 13 487 |
| MFILE keys present in only one arm | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| in-memory signature fields differing | **0** of 4 | 0 of 4 | 0 of 4 | 0 of 4 |
| raw metrics fields differing | **0** of 23 | 0 of 22 | 0 of 17 | 0 of 5 |
| **total quantities compared** | **29 760** | **29 916** | **32 206** | **29 413** |
| `ifail` | 1 = 1 | 1 = 1 | 1 = 1 | 1 = 1 |
| sweeps | 2 029 = 2 029 | 4 286 = 4 286 | 1 891 = 1 891 | 29 = 29 |
| model evaluations | 42 609 = 42 609 | 90 006 = 90 006 | 39 711 = 39 711 | 609 = 609 |

**PASS on all four.** Ten run-metadata keys (date, time, username, host, directory, file prefix,
git tag, branch, commit message, wall-clock runtime) are excluded by name; they are provenance, not
results, and differ between any two runs. No tolerance is applied anywhere.

### 5.2 Gate 2 — correctness with the hook on

The project's acceptance quantity is `norm_objf` plus a post-solve feasibility audit, **never the
iteration variables** (D6). `sqsumsq` is the sum of squares of the constraint residuals at the
returned point — how far off the feasible manifold it sits — and `conf_l2` is the L2 norm of the
same residual vector. All compared as hex floats.

| deck | figure of merit | `norm_objf` | `sqsumsq` | `conf_l2` | `ifail` | verdict |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 1 | `0x1.99999999b822dp+0` = | `0x1.33151db6b60bcp-28` = | `0x1.bf1019d122947p+0` = | 1 = 1 | **PASS**, 4 of 4 |
| `low_aspect_ratio_DEMO` | −14 | `-0x1.a00c1e7544537p-2` = | `0x1.1252a3302408bp-45` = | `0x1.a9db92416f75ep+0` = | 1 = 1 | **PASS**, 4 of 4 |
| `st_regression` | −5 | `-0x1.096acf3342eefp+4` = | `0x1.fb9bad86eb8cbp-45` = | `0x1.c217070dbf5a3p+3` = | 1 = 1 | **PASS**, 4 of 4 |
| `large_tokamak_eval` | 7 | **absent in both arms** | `0x1.60bbbd4c53d2dp-40` = | `0x1.6177e4b755091p+1` = | 1 = 1 | **PASS**, 3 of 4 substantive |

**The `large_tokamak_eval` row needs its qualifier said out loud.** That deck is an evaluation run
and never sets `norm_objf`; the value is `None` in both arms, so that comparison is `None == None`
and carries no information. Its acceptance rests on three quantities, not four — and on the
29 413-quantity bit comparison below, which is where the real evidence for that deck is.

**Matched final accuracy.** No tolerance setting was changed in either arm, and the comparison is
at the returned point, not at a matched tolerance: `sqsumsq` is bit-identical, so the two arms did
not merely stop at the same tolerance, they stopped at the same point.

**Beside the acceptance table, the whole-MFILE bit comparison** — reported separately because a
bit-identical result is a stronger statement than the gate requires, and because a *difference*
would have named the field the dependency analysis missed:

| | `large_tokamak_nof` | `low_aspect_ratio_DEMO` | `st_regression` | `large_tokamak_eval` |
|---|---|---|---|---|
| MFILE lines differing | **0** of 16 174 | **0** of 16 435 | **0** of 18 692 | **0** of 15 917 |
| MFILE floats differing | **0** of 13 559 | **0** of 13 455 | **0** of 13 493 | **0** of 13 487 |
| total quantities compared | 29 760 | 29 916 | 32 206 | 29 413 |

**Hoisting the feed-forward tail changes no number anywhere.** That is the strongest available
statement of the feed-forward property: if any hoisted node's output fed anything back, the
deferred trajectory would diverge and the MFILE would say so. It does not, on 121 295 compared
quantities across the four decks.

### 5.3 Gate 3 — the saving, as a count

Model evaluations, counted by wrapping every model entry point and attributing each depth-0
invocation to one of three disjoint windows: inside `_call_models_once` (the per-sweep cost),
inside `_run_hoisted_tail` (the once-per-`call_models` cost), and outside both (the `output()`-path
traffic of trap T7, which the hoist does not touch).

| | `large_tokamak_nof` | `low_aspect_ratio_DEMO` | `st_regression` | `large_tokamak_eval` |
|---|---|---|---|---|
| nodes executing per sweep | 21 | 21 | 21 | 21 |
| sweeps (all loops) | 2 029 | 4 286 | 1 891 | 29 |
| of which in `call_models` | 2 027 | 4 284 | 1 889 | 27 |
| `call_models` invocations | 630 | 1 240 | 570 | 11 |
| tail size resolved | 2 | 2 | 2 | **1** |
| evaluations in loop, hook **off** | 42 609 | 90 006 | 39 711 | 609 |
| evaluations in loop, hook **on** | 38 555 | 81 438 | 35 933 | 582 |
| evaluations in the hoisted tail | 1 260 | 2 480 | 1 140 | 11 |
| **total, hook on** | **39 815** | **83 918** | **37 073** | **593** |
| **removed** | **2 794** | **6 088** | **2 638** | **16** |
| **denominator (total evaluations, hook off)** | **42 609** | **90 006** | **39 711** | **609** |
| **saving** | **6.56 %** | **6.76 %** | **6.64 %** | **2.63 %** |
| nodes in the first sweep, hook on | 19 | 19 | 19 | **20** |
| sweeps, hook on | **2 029 (unchanged)** | **4 286 (unchanged)** | **1 891 (unchanged)** | **29 (unchanged)** |
| solver iterations | 8 = 8 | 16 = 16 | 10 = 10 | 0 = 0 |
| `output()`-path evaluations (T7) | 33 = 33 | 33 = 33 | 33 = 33 | 33 = 33 |

**No sweep is saved and none is added.** That is the expected result and worth stating plainly: the
hoist removes work *within* each sweep, it does not change how many sweeps the loop needs, because
the predicate never depended on the tail. The saving is exactly

> `removed = tail_size x (in-loop sweeps - call_models invocations)`

— 2 × (2 027 − 630) = 2 794, 2 × (4 284 − 1 240) = 6 088, 2 × (1 889 − 570) = 2 638,
1 × (27 − 11) = 16 — which reproduces all four measured counts exactly. The saving is therefore
governed entirely by the mean sweeps per `call_models`: **3.22 / 3.45 / 3.31 / 2.45**.

**Timings are not evidence and are not used.** For context only, and never as a gate: total driver
wall clock 452 s for 42 runs, single-threaded BLAS, one machine, one repetition each. No conclusion
in this report rests on any of it.

### 5.4 Protocol §12 — every gate shown capable of failing

| check | what was perturbed | what the gate reported | denominator |
|---|---|---|---|
| bit comparator (gates 1, 2) | `(rmajor)` in a copy of the `parent` MFILE, by **one ULP** (`0x1.000000001315cp+3` → `…dp+3`) | **FAIL**, exactly **1** differing line and exactly **1** differing float | 16 174 lines / 13 559 floats |
| bit comparator, gross case | one scenario's MFILE against another's | **11 606** differing floats | 13 441 common floats |
| acceptance predicate (gate 2) | `norm_objf` in a copy of `metrics.json`, by **one ULP** | PASS unperturbed → **FAIL** perturbed | 4 quantities |
| count gate (gate 3), null case | two copies of the *same* census | saving **0** evaluations — no saving manufactured from identical input | 42 609 / 90 006 / 39 711 / 609 |
| count gate (gate 3), unit case | **one** evaluation moved out of the loop | saving reported as exactly **1** | as above |
| count gate, conservation A | — | hoisted evaluations **=** tail runs × tail size on all four (1 260 = 630×2; 2 480 = 1 240×2; 1 140 = 570×2; 11 = 11×1) | — |
| count gate, conservation B | — | `output()`-path traffic **identical** in both arms, 33 = 33, on all four | — |

Conservation A is the check that matters most for gate 3: the hoisted tail runs *outside*
`_call_models_once`, so a census that only watched that method would score it as trap-T7 reporting
traffic and report a saving that is entirely fictitious. The identity confirms the second window is
attributing it correctly. Conservation B confirms the hoist changes nothing on the output path.

---

## 6. Against A2's 4.6–8.2 % — the prediction is not wrong, its node set is different

A2 predicted the hoist at **4.6–8.2 %**, and plan §4.1 records it as "of node-evaluations, A2,
node-count weighting", confidence *firm*. The measurement lands at 6.6 / 6.8 / 6.6 / 2.6 %. Before
that is called agreement or disagreement, two mismatches have to be named — this project has been
burned by quoting a prediction as a measurement (trap T11) and by quoting a number without its
denominator.

**Mismatch 1 — the node set.** A2's cost model is
`C_hoist = S_global × (w_M1 + w_M2 + w_M3) + 1 × (w_Pulse + w_FF)`. It hoists **`Pulse` as well as
the feed-forward module**. A13 hoists `FF` only, because `pulse`'s two writes are read by both the
objective and the constraints (§4.1) — precisely the C2a / D12 point that `pulse` joins the tail
only *after* the burn-time coupler is lifted. A2's number is for an arm that does not exist yet.

**Mismatch 2 — the unit.** A2's node-count column weights by **DSM rows**: `|Pulse| = 1`,
`|FF| = 5`, `|all| = 52`. A13's gate counts **model-call nodes**: the tail is 2 of the 21 nodes a
deck executes. The node map's own docstring warns these are not interchangeable — "52 sweep-executed
rows against 26 model calls" — and here the gap is concrete: of `FF`'s 5 DSM rows, **only 2
correspond to a hoistable driver call site.** Row 38 is `CsFatigue`, which is not a node in
`_call_models_once` at all (it runs nested inside an M2 node), and the map's own `FF` membership
includes `objective_constraints`, flagged `in_call_models_once: false` — the objective and
constraint block, which **is** the convergence test and cannot be hoisted out of the loop that uses
it. Weighting the hoist by all 5 rows credits it with work no driver change can defer.

**Corrected, the two agree.** Applying A2's own arithmetic to A13's node set and unit — the tail is
2 of 21 nodes, deferred on every in-loop sweep but the one that runs after convergence:

| deck | A2 as published (DSM rows, `Pulse` + `FF`) | A2's arithmetic on A13's arm and unit | **measured** |
|---|---|---|---|
| `large_tokamak_nof` | 7.95 % | 6.56 % | **6.56 %** |
| `low_aspect_ratio_DEMO` | 8.20 % | 6.76 % | **6.76 %** |
| `st_regression` | 8.06 % | 6.64 % | **6.64 %** |
| `large_tokamak_eval` | 6.84 % | 5.25 % | **2.63 %** |

Three decks agree to three significant figures. The fourth is short by 2.6 percentage points for a
reason that is named and measured, not unexplained: the predicate guard of §4 keeps `costs` in the
loop on that deck. **A2's measured-cost column — 4.62 / 4.55 / 4.58 / 1.65 % — is not used here.**
It is the weighting I-10 showed moving 6.4 % → 4.4 % across runs of identical code, and this
report's rule is that a wall-clock-derived weight is not evidence.

**What should be corrected in the plan.** The row in §4.1 reading "**4.6-8.2 %** of
node-evaluations · A2, node-count weighting · firm" is wrong in three particulars: the 4.6 % end
comes from *measured-cost* weighting, not node counts; the band is over a node set that includes
`Pulse`; and the unit is DSM rows, not node evaluations. **The measured value for the hoist as it
now exists is 6.56 / 6.76 / 6.64 / 2.63 % of model evaluations**, per deck, never pooled. That
replacement is proposed here, not made — the plan is the orchestrator's.

---

## 7. Autonomous decisions, each with its reversal path

| # | Decision | Why | Reversal |
|---|---|---|---|
| 1 | The hoist applies to `call_models` only, not `call_models_and_write_output` | That loop's predicate is the whole MFILE, which contains the tail's outputs; and `output()` re-enters `run()` there anyway (T7) | Set `self._pending` in that method as `call_models` does. Worth ≤ 4 evaluations of 42 609 (§3.3) |
| 2 | A node the active figure of merit reads is kept in the loop rather than raising | Keeps every deck runnable and keeps the loop's criterion exactly upstream's | Make `resolved_hoist_tail` raise instead of filter (§4.3). Cost of the decision is quoted, not hidden: 2.63 % rather than 5.25 % on `large_tokamak_eval` |
| 3 | The resolved tail is re-derived on every `call_models`, not memoised on the `Caller` | It depends on the deck's figure of merit and a scan may change the deck between calls; the resolution is a three-element comprehension | Memoise behind a sentinel |
| 4 | `pulse`'s call site was made deferrable although `pulse` is not hoisted | C2a requires the set to follow the arm; with the site in place, adding `PULSE` to `HOIST_MODULES` needs no edit here. The site is inert today and covered by gate 1 | Remove the site and the name from `DEFERRABLE_NODES`; the import-time coverage check then raises if a future arm needs it |
| 5 | `caller.py` reads the committed node map from `arch_surgery/` | The alternative is the hard-coded list C2a forbids. The read happens **only** when the hoist is on, so the default path has no dependency on `arch_surgery/` at all | Pass the map path through an environment variable, or inline the mapping |
| 6 | A2's arithmetic was recomputed on A13's node set rather than reporting a bare disagreement | A bare "6.6 % against a predicted 4.6-8.2 %" would have hidden that the two are over different node sets | — |

---

## 8. What was *not* done

- **No `process/models/` change.** The hoist needed none; §3.1 is `caller.py` only. No D11
  approval is required and none was sought.
- **`pulse` was not hoisted.** It is not feed-forward today, measured (§4.1). It joins the tail
  when A4 lifts the burn-time coupler, and the mechanism for that is in place and unused.
- **`call_models_and_write_output` was not changed** (decision 1).
- **No timing claim.** Wall clock appears once, labelled context, with its repetition count.
- **The plan and the queue were not edited.** §6 proposes a correction to plan §4.1; making it is
  the orchestrator's call (protocol §8).
- **`arms.py` was not changed** to carry the predicate guard. The asymmetry is recorded in §3.2 so
  Phase B can decide; changing a merged instrument was out of scope here.
- **No excluding-arm Phase B measurement.** VP2 is a toggle and that arm is a later task (D15).
- **Nothing was pushed, and nothing was merged.**

---

## 9. Reproduction

```
# from the worktree root, with PROCESS_surgery_env
python arch_surgery/idf_probe/run_a13.py --parent-tree <extraction of 4433bc67> \
       --runs arch_surgery/idf_probe/runs/a13
python arch_surgery/idf_probe/compare_a13.py       --runs arch_surgery/idf_probe/runs/a13
python arch_surgery/idf_probe/a13_gate_sensitivity.py --runs arch_surgery/idf_probe/runs/a13
python arch_surgery/idf_probe/a13_predicate_probe.py  --scenario <s> --outdir <d> --expect-tree <tree>
```

Artifacts under `arch_surgery/idf_probe/runs/` are untracked by design. The committed instruments
are `run_a13.py`, `compare_a13.py`, `a13_node_census.py`, `a13_tail_writeset.py`,
`a13_predicate_probe.py` and `a13_gate_sensitivity.py`; `compare_a13.py` and
`a13_gate_sensitivity.py` import A3's bit comparator unchanged, including its MFILE line parser —
A3's own sensitivity check found that anchoring on the first `(...)` in a line silently dropped
about a thousand floats per scenario, and reusing the fixed parser is safer than writing a fourth.

---

## 10. Change log

| date | entry |
|---|---|
| 2026-09-01 | Branch point corrected: worktree seeded at upstream `6df46205` (I-11, third instance), rebranched at `4433bc67` |
| 2026-09-01 | VP2 / F7b implemented in `caller.py`; instruments written; `dc267a56` |
| 2026-09-01 | First arm set discarded and re-run after a mid-flight edit to `caller.py` — the running subprocesses would have imported a mixture of two versions. Stopped with `TaskStop`, never `pkill` (trap T8) |
| 2026-09-01 | All three gates PASS on 4/4; sensitivity checks confirm all three can fail; A2's band reconciled in §6; DSM finding **V10** filed |
