# Registry allocations

The single allocation table for new optimiser entities. **Every task takes its numbers from
here.** Two branches allocating independently would both pick the same next number and merge
into a dict with one entry silently winning.

## Rule (D10)

**Append only. Never reuse a gap.**

`ITERATION_VARIABLES` held 83 entries over keys 1–177 at the base commit, leaving **94 gaps**
(8, 9, 14, 15, 21, 22, 24, 25, 26, 27, 28, 30, …) from retired variables. Reusing one means an
existing `IN.DAT` naming that number silently selects a different variable, with no error.
Appending cannot collide with any existing deck. After A20 (registry-append) the registry holds
**84 entries over 1–178**, and the gap count is still **94** — no gap was consumed.

There is **no cap to raise**: `N_ITERATION_VARIABLES_MAX = max(ITERATION_VARIABLES.keys())` in
`process/data_structure/numerics.py` is derived, so appending key 178 raises it automatically.
Every array sized by it (`lablxc`, `name_xc`, bounds, scaling) grows with it, and `lablxc` is
populated per index from the registry at `iteration_variables.py:421` — there is no
hand-maintained parallel list. **Confirmed by measurement in A20 (registry-append):** the derived
maximum moved 177 → 178 and all **twelve** arrays sized by it (`ixc`, `lablxc`, `name_xc`,
`boundl`, `boundu`, `scale`, `scafc`, `xcm`, `xcs`, `itv_scaled_lower_bounds`,
`itv_scaled_upper_bounds`, `vlam`) grew to 178 in step.

**Constraints differ in one respect.** 82 were registered over 1–92 against a fixed cap of 500,
so 93 was free — but `lablcc` had exactly 92 entries and **must be extended in step** (A1
(stage0-rebaseline) §8). A constraint appended without its label is a silent reporting gap. After
A20 (registry-append): **83 constraints over 1–93, `lablcc` 93 entries.**

One code path does change its iteration count when the constraint registry grows:
`set_active_constraints` in `process/core/init.py` scans `icc[0 : ConstraintManager.num_constraints()]`
— a loop bounded by the *registry size* rather than by the number of constraints the deck names.
Appending 93 widens that scan from 82 to 83 slots. It is inert for every deck that names fewer
than 83 constraints (the four scenarios name 18–26), and A20's neutrality gate confirms it
empirically. It is nonetheless a latent PROCESS defect: a deck naming more than
`num_constraints()` constraints would be silently truncated.

## Divergence from upstream

Once `ixc = 178` validates here and not on `ukaea/PROCESS`, a deck written for this fork will not
load upstream. Inherent to lifting anything; state it in the write-up rather than working around
it. **Measured in A20 (registry-append), both directions:**

- *Fork deck → upstream:* refused at **input-parse time**, before any model runs, with
  `ProcessValidationError`. `icc = 93` gives "Variable 'icc' at line N is not one of (1, 2, …,
  92) (value = 93)"; `ixc = 178` gives "Variable 'ixc' at line N is not on the prescribed range
  (1, 177) (value = 178)". The failure is loud and immediate, never a silent misread.
- *Upstream deck → fork:* loads and runs unchanged. Appending only *widens* the accepted sets —
  `ixc` from `(1, 177)` to `(1, 178)`, `icc` from 82 choices to 83 — and reassigns no existing
  number. Confirmed byte-identical on all four scenarios (whole-MFILE identity, 15 917–18 692
  lines each, 0 differing lines).

The divergence is therefore **one-way**: this fork accepts every upstream deck; upstream does not
accept a deck that names 178 or 93. Upstream `main` at `6df46205` (2026-08-28) still ends at
iteration variable 177 and constraint 92, so the numbers this fork has taken are not yet claimed
upstream.

## Allocations

| Task | Iteration variables | Constraints | Purpose | Status |
|---|---|---|---|---|
| *(baseline at `c0ae5b28`)* | 1–177, 83 used | 1–92, 82 used | upstream | — |
| **F2** (framework), done by A20 (registry-append) | **178** — `framework_placeholder` | **93** — framework placeholder consistency | first append; proves the mechanism and the neutrality of an unreferenced entry | **ALLOCATED** 2026-09-01 |
| **A4** (burn-time-lift) | 179 | 94 | `t_plant_pulse_burn` + its consistency constraint | reserved, not allocated |
| **A9–A11** (subdriver lift) | 180–183 | 95–98 | up to four lifted residuals, one per site | reserved, not allocated |

Next free: iteration variable **179**, constraint **94**.

**A4's and A9–A11's constraint reservations were shifted by one** when F2 took constraint 93.
The queue row for A20 (registry-append) assigns 93 to F2 (`MASTER_TODO.md`, and decision D10 —
"constraints append from 93"), while an earlier version of this table had reserved 93 for A4.
Both cannot hold; the queue row is the later statement, so F2 took 93 and everything below it
moved up one. Nothing was allocated under the old numbering, so no code or deck refers to the
superseded reservations. To reverse: renumber the F2 pair's constraint and restore 93 → A4,
94–97 → A9–A11.

*Reserved* means the range is held; *allocated* means the entry exists in the registry. A task
allocates only the numbers it actually uses, and updates this table in the same commit.

## Neutrality expectation

An appended entry that no deck references is **inert** — `ixc` selects which variables are
active, so entry 178 does nothing until a scenario names it. Results for the existing deck should
therefore be byte-identical, which is a claim the neutrality and determinism gates test rather
than something to assume.

**Tested and upheld, A20 (registry-append), 2026-09-01.** All four scenarios, whole-MFILE
identity against a `git archive` of the base commit `c0ae5b28`: **0 differing lines** in every
arm, and every hex-float signature (`norm_objf`, `conf_l2`, `sqsumsq`, the iteration-variable
vector) identical. Sweep counts are unchanged to the unit (2029 / 4286 / 1891 / 29). The one
supplementary check that the pair is *live* and not merely decorative: a scratch deck naming
`ixc = 178` and `icc = 93` solves (`ifail = 1`, 21 variables against 20, 4 equality constraints
against 3), the placeholder converges to exactly 1.0, constraint 93's residue is written to the
MFILE under its `lablcc` label, and the objective moves by 3.2e-12 relative — below the solver
tolerance, i.e. the same optimum.
