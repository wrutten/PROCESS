# Registry allocations

The single allocation table for new optimiser entities. **Every task takes its numbers from
here.** Two branches allocating independently would both pick the same next number and merge
into a dict with one entry silently winning.

## Rule (D10)

**Append only. Never reuse a gap.**

`ITERATION_VARIABLES` holds 83 entries over keys 1–177, leaving **94 gaps** (8, 9, 14, 15, 21,
22, 24, 25, 26, 27, 28, 30, …) from retired variables. Reusing one means an existing `IN.DAT`
naming that number silently selects a different variable, with no error. Appending cannot
collide with any existing deck.

There is **no cap to raise**: `N_ITERATION_VARIABLES_MAX = max(ITERATION_VARIABLES.keys())` in
`process/data_structure/numerics.py` is derived, so appending key 178 raises it automatically.
Every array sized by it (`lablxc`, `name_xc`, bounds, scaling) grows with it, and `lablxc` is
populated per index from the registry at `iteration_variables.py:421` — there is no
hand-maintained parallel list.

**Constraints differ in one respect.** 82 are registered over 1–92 against a fixed cap of 500, so
93 is free — but `lablcc` has exactly 92 entries and **must be extended in step** (A1
(stage0-rebaseline) §8). A constraint appended without its label is a silent reporting gap.

## Divergence from upstream

Once `ixc = 178` validates here and not on `ukaea/PROCESS`, a deck written for this fork will not
load upstream. Inherent to lifting anything; state it in the write-up rather than working around
it.

## Allocations

| Task | Iteration variables | Constraints | Purpose | Status |
|---|---|---|---|---|
| *(baseline at `c0ae5b28`)* | 1–177, 83 used | 1–92, 82 used | upstream | — |
| **F2** (framework) | **178** | — | first append; proves the mechanism and the neutrality of an unreferenced entry | not allocated |
| **A4** (burn-time-lift) | 179 | 93 | `t_plant_pulse_burn` + its consistency constraint | reserved, not allocated |
| **A9–A11** (subdriver lift) | 180–183 | 94–97 | up to four lifted residuals, one per site | reserved, not allocated |

*Reserved* means the range is held; *allocated* means the entry exists in the registry. A task
allocates only the numbers it actually uses, and updates this table in the same commit.

## Neutrality expectation

An appended entry that no deck references is **inert** — `ixc` selects which variables are
active, so entry 178 does nothing until a scenario names it. Results for the existing deck should
therefore be byte-identical, which is a claim the neutrality and determinism gates test rather
than something to assume.
