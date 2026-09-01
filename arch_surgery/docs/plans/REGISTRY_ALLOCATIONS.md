# Registry allocations

The single allocation table for new optimiser entities. **Every task takes its numbers from
here.** Two branches allocating independently would both pick the same next number and merge
into a dict with one entry silently winning.

## Rule (D10)

**Append only. Never reuse a gap.**

`ITERATION_VARIABLES` held 83 entries over keys 1–177 at the base commit, leaving **94 gaps**
(8, 9, 14, 15, 21, 22, 24, 25, 26, 27, 28, 30, …) from retired variables. Reusing one means an
existing `IN.DAT` naming that number silently selects a different variable, with no error.
Appending cannot collide with any existing deck. After A24 (phase-b-scaffold) the registry holds
**84 entries over 1–178**, and the gap count is still **94** — no gap was consumed. (A20
(registry-append) reached the same state with a synthetic placeholder and then withdrew it; A24
re-took the same numbers for real content. See *Why F2 allocated nothing the first time* below.)

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
A24 (phase-b-scaffold): **83 constraints over 1–93, `lablcc` 93 entries**, the 93rd being
`"Burn time consistency"`. The `lablcc` edit sits outside `CLAUDE.md`'s default-permitted surface
and is **approved by decision D14(a)** for exactly this append.

One code path does change its iteration count when the constraint registry grows:
`set_active_constraints` in `process/core/init.py` scans `icc[0 : ConstraintManager.num_constraints()]`
— a loop bounded by the *registry size* rather than by the number of constraints the deck names.
Appending 93 widens that scan from 82 to 83 slots. It is inert for every deck that names fewer
than 83 constraints (the four scenarios name 26, 25, 18 and 25 — counted from the decks by A24's
seam probe), and A20's and A24's neutrality gates confirm it empirically. It is nonetheless a latent PROCESS defect: a deck naming more than
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
| **F2** (framework), attempted by A20 (registry-append) | *(none)* | *(none)* | proved the append mechanism, then **withdrew the code** | **WITHDRAWN** 2026-09-01 — see below |
| **F2** (framework), done by A24 (phase-b-scaffold) | **178** `t_plant_pulse_burn`, module `times`, default bounds 1.0 – 1.0e8 | **93** `constraint_equation_93`, label `"Burn time consistency"` | the burn-time lift's design variable and the residual that determines it (variant point VP5); **consumed by A4 (burn-time-lift)** | **ALLOCATED** 2026-09-01 |
| **A9–A11** (subdriver lift) | 179–182 | 94–97 | up to four lifted residuals, one per site | reserved, not allocated |

**Next free: iteration variable 179, constraint 94.**

The entries are **inert until a deck names them**: `ixc` selects which iteration variables are
active and `icc` which constraints. None of the four scenario decks names either number — counted
from the decks rather than assumed (A24's seam probe: 0 of 4 decks name `ixc = 178` or
`icc = 93`, over 26/25/18/25 constraints and 20/19/14/2 iteration variables named). A24's
bit-identity gate confirms the consequence on the results: 0 differing quantities out of 121 295
across the four scenarios.

### Why F2 allocated nothing the first time, and what survives from it

A20 (registry-append) appended iteration variable 178 and constraint 93 as a synthetic
placeholder, gated it on all four scenarios, and the code was then **withdrawn by the user's
ruling** (2026-09-01): synthetic content does not earn a permanent place in a frozen tree.

The three edits stood or fell together and could not be partially kept. Constraint 93's body was
`eq(data.numerics.framework_placeholder, 1.0, …)`, so it existed only to pin a field invented for
it in `process/data_structure/numerics.py`; and the `lablcc` extension existed only to label that
constraint. Withdraw the field and the other two have nothing to act on.

**Nothing was lost by withdrawing it**, because the deliverable was knowledge, not code:

- `N_ITERATION_VARIABLES_MAX` is derived as `max(keys)` and **twelve** arrays sized by it grow in
  step — the earlier table named four.
- Appending is **inert**: 0 differing MFILE lines against a pristine `git archive` of `c0ae5b28`,
  all four scenarios, probe on and off.
- The input-language divergence is **one-way**, measured both directions: a fork deck fed to
  upstream is refused at *input-parse time* with `ProcessValidationError` before any model runs,
  while an upstream deck runs here byte-identically. That is precisely the loud failure that
  reusing one of the 94 gaps would **not** give — decision D10's rationale confirmed by experiment
  rather than argued.

**A24 (phase-b-scaffold) took 178 and 93 for A4**, and needed no invented field:
`t_plant_pulse_burn` already exists in `process/data_structure/times_variables.py`. The append did
require extending `lablcc` in `process/data_structure/numerics.py`, which D10 mandates and which
is therefore not a discretionary edit — that file sits outside the default-permitted surface named
in `CLAUDE.md` and carries an upstream warning that its `lablcc` comments feed code generation, so
the edit is **explicitly approved by D14(a)** and is confined to one appended list entry plus two
enumerating docstring lines.

*Reserved* means the range is held; *allocated* means the entry exists in the registry. A task
allocates only the numbers it actually uses, and updates this table in the same commit.

## Neutrality expectation

An appended entry that no deck references is **inert** — `ixc` selects which variables are
active, so entry 178 does nothing until a scenario names it. Results for the existing deck should
therefore be byte-identical, which is a claim the neutrality and determinism gates test rather
than something to assume.

**Tested and upheld twice.** A20 (registry-append), 2026-09-01, with the synthetic placeholder:
all four scenarios whole-MFILE identical against a `git archive` of the base commit `c0ae5b28`,
**0 differing lines** in every arm, every hex-float signature identical, sweep counts unchanged to
the unit (2029 / 4286 / 1891 / 29). A20's supplementary live check — a scratch deck naming
`ixc = 178` and `icc = 93` solving with `ifail = 1` — established that the mechanism is not merely
decorative.

**Re-tested for the real pair, A24 (phase-b-scaffold), 2026-09-01**, because A20's result does not
transfer to a different pair of numbers attached to a real variable and must not be cited as if it
does. Against a `git archive` of `7a0f3f6e`, probe off and probe on: **0 differing MFILE lines**
out of 16 174 / 16 435 / 18 692 / 15 917, **0 differing hex floats** out of 13 559 / 13 455 /
13 493 / 13 487, `ifail = 1` on all four, and the same sweep counts 2029 / 4286 / 1891 / 29. The
gate was shown capable of failing first: one unit in the last place of one MFILE float is caught
on every scenario. **A24 did not repeat A20's live-deck demonstration** — no deck naming 178 or 93
exists yet, and building one is A4's work, not scaffolding.
