# A45 (v4-harness-plan) — task report

> **Document status** — **CURRENT · OPEN TASK.** Written 2026-09-10 by task
> **A45 (v4-harness-plan)** on branch `A45-v4-harness-plan`, worktree
> `/home/wrutten/projects/PROCESS_surgery_worktrees/A45-v4-harness-plan`, branch point
> `16a6e87e`. The deliverable is
> [`../plans/V4_HARNESS_IMPLEMENTATION_PLAN.md`](../plans/V4_HARNESS_IMPLEMENTATION_PLAN.md).
> **Nothing was built and nothing outside these two documents was changed.**

## Verdict

**What was inventoried.** Every import, subprocess call, filesystem path and environment variable
the V3 experiment harness uses from outside its own directory, at file and function level; the
driver-side instrument in `process/core/caller.py` and `process/core/solver/` that those switches
drive; and the V4 methodology the rewrite must implement (the V4 experiment plan and the V4
improvement list, including items 1c and 1d, which were read **uncommitted** from the main
checkout on 2026-09-10 and may have moved since).

**The finding that shapes the plan.** *The coupling to `idf_probe/` and `fixedpoint/` is tiny;
the convolution is inside the files.* The V3 harness's entire external surface is **three Python
names imported from two modules** (`run_a28._ARCH_VARS`; `a34_instruments.{_cross_residual,
load_spec_offline}`; `v2_eval_one.{perturb_factor, restore_snapshot}`), **three subprocess entry
points** (`run_one.py`, `v2_eval_one.py`, `run_a28.py decks`), **seven committed artifacts**, one
scenario directory, and **one hard-coded absolute path into the main checkout** (gate G0's V2
comparator, `phase_b.py:56-60`). `arch_surgery/fixedpoint/` is not imported at all — it is
reached once, at run time, by an `importlib` file-path load two levels deep, so no static import
scan of the V3 directory finds it. Nineteen of its twenty modules are untouched by V3.

What *is* convoluted: `run_one.py` is 1 126 lines with a single ~1 000-line `main()`;
`v2_eval_one.py` (996 lines) duplicates much of it; arm composition exists **twice**
(`v3_runner.env_for` and `phase_a.env_for_phase_a`) in two `if`-chains that already differ in two
places; and a hand-maintained `INSTRUMENTATION` dict of booleans stands in for a measurement of
what the driver can actually do — and is consulted on one side and not the other.

**What is proposed.** `arch_surgery/MDA_partitioning_experiment_v4/` mirroring V2/V3 at the top
(`V4_EXPERIMENT_PLAN.md`, the report, `experiment_runner.py`, `phase_a.py`, `phase_b.py`,
`analysis.py`, `runs/`) with everything else in a self-contained `harness/` package of 19 modules,
built on four ideas: the V4 plan's §3.2 **switch matrix as data** (one arm composition, and the
rung difference becomes a computed field diff); **capability measured, not declared** (a probe
child reports what the driver resolved, so an arm composing a switch the tree lacks refuses);
**one child-side instrumentation module** shared by the two entry points; and **a reproduction
gate that must show the rewrite did not move the measurement** — **twenty** runs reproducing V3
bit-exactly (amended 2026-09-10), with a `v3_compat` composition and seven teeth including
*"a missing reference must FAIL, not skip"*, plus a named statement of the two arms the gate
cannot cover and what covers them instead (§7.5).

Estimated ≈ 6 570 lines against the V3 stack's measured 8 828 (`wc -l`) — about 26 % smaller. The
gain is self-containment and provability, not the line count; §4.6 of the plan prices what a
smaller harness would cost in lost diagnostics.

**What needs the user.** Eleven decisions, in the plan's §9 and repeated verbatim below. Three
are load-bearing:

- **(2)** the driver loads `arch_surgery/fixedpoint/ystate.py` **by absolute path**, so "all of
  `/fixedpoint` in `/harness`" is not a harness-only decision;
- **(4)** the committed artifacts that define the coupling state derive from **138 MB of
  untracked pickle** that no committed stage can regenerate, in a repository that has destroyed
  untracked run artifacts three times (I-14, I-15, I-16);
- **(1)** the environment-variable names for the two renamed deferral switches, which the V4
  experiment plan explicitly defers to this document — together with the recommendation that the
  **retired names must raise, not be ignored**, since an ignored switch runs the wrong arm under
  the right name.

## Three things found while inventorying that are worth recording independently

1. **`caller.py:583` has no existence check on `node_writesets.json`.** The `per_call` deferral
   path (`caller.py:344-349`) refuses with a message naming the generator; the `per_run` path at
   line 583 reads the same file with no guard, so a missing artifact surfaces as a raw
   `FileNotFoundError`. `NODE_MAP_PATH` is checked on all three of its paths. One-line asymmetry;
   folded into the plan's DR6 rather than filed, because DR6 touches those lines anyway.
2. **Item 6a(b) confirmed by direct inspection.** V3's Phase A records carry no
   `post_solve_totals` key at all and no `env_PROCESS_ARCH_POST_SOLVE` entry, although
   `phase_a.py:173` sets that variable — verified against
   `runs/phase_a/campaign/st_regression/A1/start001/metrics.json` in the main checkout. The V4
   record schema (plan §4.4) closes it.
3. **`v3_runner.py:35` imports `PULSED as A28_PULSED` and never uses it**, and `cfg.PULSED`
   duplicates the same set independently of `run_a28.PULSED`. Two sources for one fact, able to
   drift silently. The V4 design removes both in favour of a `Config.pulsed` field.

## Autonomous decisions, with their reversal paths

*Caption: one row per decision this task took without asking, because it is a presentation or
scoping choice rather than a methodological one. "Reversal" is what it costs to undo.*

| # | decision | why | reversal |
|---|---|---|---|
| AD1 | The plan opens with a **vocabulary table** spelling out every D-number, I-number, arm name, "prime", "hoist", τ and "teeth" at first use | protocol §4 — a report must read without the queue open beside it; this plan is longer than most and the terms are dense | delete §0; nothing downstream depends on it |
| AD2 | Every driver-side change is confined to **one clearly-marked section (§3)** stating at its head that it is *not* harness and needs the user's approval | the brief requires the separation; mixing them would let a harness task make a `process/` change | none needed; it is presentational |
| AD3 | The plan **fixes the two renamed switch names** as `PROCESS_ARCH_DEFER_PER_CALL` / `PROCESS_ARCH_DEFER_PER_RUN` **as a recommendation**, and also puts them in the Decisions list | the V4 experiment plan §3.2 says the names are *"proposed here and fixed by the harness implementation plan"*, but naming is user-visible vocabulary | change two strings in `switches.py` and the V3→V4 map |
| AD4 | The plan **rejects** copying the artifacts or the predicate into `harness/` (R11, R12) rather than presenting them as neutral options | both create a second copy the driver does not read, which is the D14(c) drift failure and would fail *silently* | the alternatives are still written out in decisions (2) and (3) with what changes |
| AD5 | The proposed one-button entry point is named **`experiment_runner.py`**, not V3's `run_experiment.py` | the user named it and the V4 experiment plan's Appendix A lists it; but it collides in basename with the A18-era `arch_surgery/experiment_runner.py`, so the collision is flagged and decision (11) covers the older file | rename; one file |
| AD6 | Task decomposition is proposed as **H1–H8 plus DR1–DR6**, with H2 (the committed GR reference) before H3 (the run path) | GR is the whole safety argument for the rewrite, and it must not depend on untracked bulk that has been destroyed three times | reorder; H2 is small |
| AD7 | Line-count claims are stated from a **measured `wc -l`** of the V3 stack (8 828) with the V4 figure explicitly labelled an estimate | a plan that quotes a reduction percentage from two estimates is a number without its population (trap T11) | none |

## What was deliberately not done

- **No code.** No file created or edited under `process/`, `arch_surgery/idf_probe/`,
  `arch_surgery/fixedpoint/`, `arch_surgery/MDA_partitioning_experiment_v2/` or `…_v3/`.
- **No PROCESS run.** No number in the plan comes from an execution; the only measured figures
  are `wc -l` line counts, `du -sh` file sizes, and record-key inspections of committed and
  untracked V2/V3 artifacts, each named where it is used.
- **No methodology redesigned.** Where the harness forces a methodological choice — the audit
  position, the failure taxonomy row for `AR`'s cap, the `v3_compat` composition requirement on
  DR2–DR5 — the plan states it as a constraint on the driver changes or as a decision, not as a
  change to the experiment plan.
- **No sibling clone written to**, and the sandbox was never overridden. The V4 experiment plan
  and improvement-list items 1c/1d were read read-only from the main checkout as the orchestrator
  instructed; they were **not** copied into this worktree.

## Risks in the proposal, stated

1. **R2 (one child-side instrumentation module) changes both measurement paths at once.** This is
   the single highest-risk item in the plan. It is why gate GR is specified before it, why H2
   commits the reference before H3 builds the run path, and why GR carries a positive control
   (running `B3` *without* the `v3_compat` switches must FAIL, proving the gate is sensitive to
   the thing it is holding fixed).
2. **GR cannot cover an arm whose V4 driver change is not composable back to V3.** If any of
   DR2–DR5 lands as an unconditional change rather than a switch, that arm drops out of GR. The
   plan makes composability a hard design rule on those changes and requires the gate to say
   which arms it could not cover, rather than quietly comparing fewer.
3. **The A18 harvest gap is real today and the plan does not close it** — it asks (decision 4).
   Until it is answered, `ystate_a26_*` can be *verified* from its recorded harvest identity but
   not *regenerated*, and protocol §15's "every stage is a committed script" holds for the use of
   those artifacts, not for their derivation.
4. **Item 1c's `A0p` composes flat + lift + pin, a combination V3 never ran.** The improvement
   list states the driver already permits it (its only refusals being pin ⇒ lift and a deck naming
   iteration variable 178). The plan therefore requires the capability probe to *confirm* that
   composition at preflight rather than assume it, and H1's gate exercises it.

## Change log (append-only)

- **2026-09-10** — task opened; `CLAUDE.md`, `TRAPS.md` and `MASTER_TODO.md` §protocol read.
  Inventory taken at `16a6e87e`; V4 experiment plan and improvement-list items 1c/1d read
  read-only and uncommitted from the main checkout. Plan and this report written and committed.
  Status: awaiting the orchestrator's critical assessment (protocol §5) and the user's decisions
  (1)–(11).
- **2026-09-10 — the orchestrator's critical assessment received (`cb7090fc`) and acted on.**
  Four amendments made to
  [`../plans/V4_HARNESS_IMPLEMENTATION_PLAN.md`](../plans/V4_HARNESS_IMPLEMENTATION_PLAN.md),
  each dated in its Appendix A change log: **(A)** driver change **DR7**, per-attempt node-call
  accounting — §3.2 row, `attempts[]` in the §4.4 record schema, the "retried seeds" and
  "with / without retried seeds" constructions in §4.2's `stats.py`, an attempt-summation tooth in
  §7.3, and DR7 in decision (10) and §10's task table with the note that it lands before H6;
  **(B)** gate GR widened from fifteen to **twenty** runs — `B3 start001` on all three
  configurations and `B1 start001` on the two pulsed ones, so the Phase B perturbation stream
  (keyed on iteration-variable number) is exercised — and a new **§7.5** naming what GR cannot
  cover (`A0p`, `AR`) and the two gates that do; **(C)** decision (2) and §5.3 gain **option (iv)**
  (the predicate is driver code: split `ystate.py`, predicate and residual to
  `process/core/solver/ystate.py`), with the orchestrator's recommendation of (iv) beside A45's
  (i) and DR6 restated conditionally; **(D)** decision (4) gains the binding rule that
  `artifacts --derive` never runs inside a campaign, since the a26 scales are part of the frozen
  ruler. **Nothing was restructured and no other recommendation changed.** A45 accepts (iv) as the
  better of the two predicate options and says so in the row; the user still decides. Still no
  code; status **DRAFT · NOT APPROVED**; decisions (1)–(11) open.

---

## Orchestrator's critical assessment (protocol §5) — 2026-09-10

*Appended by the orchestrating session before any merge and before the plan goes to the user for
approval. Written against the plan at `aeaf9eb7` and this report at `a3f3558a`, with every
load-bearing claim re-checked in the tree, not taken from the report.*

### Verified in the tree

| claim in the plan | checked | result |
|---|---|---|
| `caller.py:245-251` hard-codes `arch_surgery/docs/data/node_writesets.json`; `:356-362` hard-codes `dsm_node_map.json` | read both blocks | **confirmed**, no environment override, no fallback |
| `caller.py:583` reads `node_writesets.json` with no existence check while `:344-349` refuses with a named message | read both | **confirmed** — `per_scenario = json.loads(NODE_WRITESET_PATH.read_text())` unguarded on the `per_run` path |
| `module_solve.py:529-534` loads `arch_surgery/fixedpoint/ystate.py` by path (code, not data) | read | **confirmed**, with the D14(c) rationale in the comment above it |
| `v3_runner.py:35` imports `PULSED as A28_PULSED` and never uses it; `cfg.PULSED` is an independent copy | grep | **confirmed** — six uses of `cfg.PULSED`, zero of `A28_PULSED` |
| the A18 harvest is 138 MB of untracked pickle | `find -size +1M` | **confirmed**: 35 / 69 / 34 MB for nof / lad / st under `idf_probe/runs/a18/`, plus A23 copies |
| `run_one.py` 1 126 lines, `v2_eval_one.py` 996 | `wc -l` | **confirmed** |
| the V3 stack measures 8 828 lines | not re-derived over the same file set | **not disputed** — the plan names its file set, which is what trap T11 asks; the 26 % figure is soft and the plan says so |

### What I endorse without reservation

The inventory's central finding — *the coupling is tiny; the convolution is inside the files* —
is correct and reframes the user's request usefully: self-containment is cheap, and the real work
is deduplication (`run_one.py` / `v2_eval_one.py`) and single composition. The four design ideas
are the right ones: the matrix as data with `rung()` computed rather than asserted; capability
measured by a probe child rather than declared in a hand-edited ledger (V3's `INSTRUMENTATION`
was consulted on one side and not the other — a defect shape, found by this inventory); one
child-side instrumentation module; and a reproduction gate with a `v3_compat` composition and a
positive control. Decisions (3), (5), (6), (7), (8), (9), (11) I would take exactly as
recommended. The retired-name refusal in decision (1) is the load-bearing half and must not be
negotiated away. The A18-harvest finding (decision 4) is real and the plan is right not to
resolve it unilaterally; I add one point below.

### Required before the plan goes to the user — two additions

**A. Per-attempt node-call accounting is missing from the record schema (§4.4) and from the
driver list (§3.2).** Task A44 (transfer-gap) established today, from V3's records, that node
calls are recorded only as run totals while `n_solver_iterations` and `ifail` are per VMCON
attempt — and that this mismatch is most of `low_aspect_ratio_DEMO`'s published headline
(`B3/B0 = 0.450` with one retried `B0` seed, 0.659 without). The V4 experiment plan §3.5 now
requires node calls **per attempt** and ratios published with and without retried seeds; this
amendment landed after A45 read the plan, so the omission is not the agent's error, but the plan
cannot go to the user without it. Needed: **DR7** — a driver stamp of `NODE_CALLS` (and the
sweep histogram) at each retry-ladder attempt boundary, in the shape of the existing
`NODE_CALLS_AT_OUTPUT` freeze (integer-only, switch-neutral); record fields
`attempts: [{stage, epsfcn, n_iterations, ifail, node_calls_solve_phase, sweeps}]`; and the
`stats.py` constructions "retried seeds per arm", "ratio with / without retried seeds" and the
failure table's per-attempt columns. GR must carry a tooth for it (a record whose attempts do not
sum to the run total must be refused).

**B. Gate GR does not exercise the Phase B perturbation path.** Every Phase B reference row in
§7.1 is `start000` — the *unperturbed* start — so `perturb.py`'s Phase B stream (keyed on
iteration-variable number, so that the lifted design vector's extra element leaves shared
variables' factors bit-identical) is tested by nothing in GR. Add one perturbed Phase B seed per
configuration (`B3 start001`, and `B1 start001` on the pulsed configurations since it is where
the two vector lengths meet) → 18–20 runs. State explicitly what covers the two arms GR cannot:
`A0p` (V3 never ran it) is covered by the V4 plan's G6 warm gate — pinned at the reference's
converged burn time, it must reproduce the reference fixed point below τ with the pinned
component bit-identical; `AR` (V3 had no Phase A reference) is covered by a G1-shape check that
`evaluate.py` with every switch cleared reproduces the first `call_models` of `BR start000`
on the counts that call records. A gate that names what it does not cover is honest; one that
is silent about it is trap T11.

### One further option the user should see on decision (2)

The plan offers three homes for the predicate module: env-overridable move (i), leave in
`fixedpoint/` (ii), copy (iii — rightly rejected). There is a fourth: **the predicate is driver
code.** It is the convergence test `module_solve.py` executes on every sweep; its residence in
the research tree is the anomaly, and both (i) and (ii) preserve the anomaly (a code module
reached by filesystem path, in (i) selectable by environment variable — which means the run
record must carry the loaded module's path *and hash* or two runs on different predicates are
indistinguishable afterwards, the same trap improvement item 5a(i) names). **(iv): split
`ystate.py` — the predicate and residual (what the driver needs) move to
`process/core/solver/ystate.py` and are imported normally by both driver and harness; the spec
generation (what only the harness needs) moves to `harness/`.** One implementation, no path hack,
no env override for code, the harness self-contained because it imports the driver anyway, and
nothing in `process/` depends on a version-numbered directory. Cost: a driver change with a
bit-identity gate (the same gate (i) needs), and the split itself. `process/core/solver/` already
holds this experiment's variant points (`module_solve.py`, `subsolve.py`), so it is the permitted
surface. I recommend (iv) over (i); the user decides.

### Secondary notes, none blocking

- **Decision (4):** add to the recommendation that `artifacts --derive` must **never run inside
  a campaign**. The a26 scales `s_i` are part of the frozen ruler; regenerating them from a new
  harvest changes τ's meaning and breaks comparability with V2, V3 and A38. Derivation is a
  provenance stage, and (b) — committing the harvest identity and scales — is the right minimum.
- **DR6's data half becomes moot** if decision (3) is taken as recommended (artifacts stay in
  `docs/data/`); its code half is replaced by (iv) if the user takes it. State DR6 conditionally.
- **DR1 values** keep the word `feedforward` (`off | feedforward | feedforward_lifted`); semantics
  are unchanged and the name says the level. Acceptable.
- **`experiment_runner.py` basename collision** with the A18-era root script is flagged (AD5,
  decision 11); acceptable since the two are never on one import path.
- **Sequencing** (H2 → H3 → H4; DR1 after H3) is right. Fourteen tasks is the honest count.

### Verdict

The plan is fit to go to the user for the eleven decisions **once A and B are added**, which is
returned to the task agent on its own branch (protocol §5). No code is to be written before the
user approves. Nothing in this assessment changes the plan's recommendations except adding option
(iv) to decision (2) and the conditional statement of DR6.
