# Query: what carries above-τ cross-pass movement on `st_regression`, when the collapsed DSM has no live back edge?

**From:** `PROCESS_surgery` (architecture experiment). **To:** `PROCESS_code_analysis`.
**Study commit:** `c0ae5b28`; every line number below verified at that commit.
**Status:** a question your pinned instrument can answer authoritatively, plus one
observation that may belong in your registers. Nothing here is a defect claim yet.

## The measurement

Iterating PROCESS's models as a partitioned MDA (blocks M1 = [physics, plasma_geom],
M2 = [coils incl. build, tfcoil-family, pfcoil], M3 = [blanket/fwbs/power/…]) with a
coupling-state displacement predicate at τ = 1e-6:

- On `st_regression`, **2 802 of 54 480** MDA evaluations (5.14 %, 25/25 multi-starts at
  δ = 10 %) still move some coupling-state component by > τ on the **second** full pass —
  after every block has been internally converged once — needing a 3rd–7th pass.
- On the two pulsed decks this happens **exactly once per optimisation** (22/14 080 and
  20/20 370 evaluations): the cold first call, plain entry-state staleness.
- The slowest-decaying component is `superconducting_tfcoil.a_tf_plasma_case`
  (written `tfcoil/resistive.py:320`; the ST deck runs the resistive TF model) — argmax exit
  residual on 22/28 audit records **in a flat single-loop arrangement as well**, so it is a
  property of the coupling structure, not of the blocking.
- The movement is **transient** (bit-exact 0 at every accepted optimum) and **dormant at the
  harvested states** — our A2/A22 censuses correctly measured zero cross-module movement
  there. It wakes only at states far from self-consistency (perturbed starts,
  mid-optimisation finite-difference points).

## What we eliminated by hand (the V1/V2 pattern from our DSM register)

- `physics ← pf_coil.p_pf_electric_supplies_mw`: the only read is `physics.py:2601`, inside
  `outplas()` — output path, not computation. (Writer: `power.py:604`.)
- `build.dr_fw_plasma_gap_{in,out}board`: written by `plasma_geometry` itself
  (`plasma_geometry.py:439-440`) — M1-internal.
- `physics.b_plasma_*_toroidal`: computed from physics-internal quantities only
  (`physics.py:395-408`).

## The two questions

1. **From the pinned dependency data: enumerate every computational-path read** (run path,
   not `output()`) **by `physics` or `plasma_geometry` of any field written by the
   tfcoil family, `build`, or `pfcoil`.** Is there any edge our grep missed — indirect
   attribute paths, helper modules, interop? If yes, that is the carrier, and we would like
   the field names. If no, the collapsed DSM is right that no M2 → M1 edge exists, and
   mechanism 2 below stands.
2. **Does your model of the code admit non-idempotent models** — a model whose output at
   fixed inputs depends on its own execution history (internal warm-started solvers,
   accumulators, cross-sweep stale reads)? No DSM edge can represent that class, yet it
   produces exactly the movement we measure. A concrete in-code example of the pattern, one
   module deep rather than cross-module: `physics.py:387` computes `b_plasma_inboard_total`
   from `b_plasma_inboard_toroidal`, which is only recomputed at `physics.py:395` — a
   one-iteration stale read, so `physics` run twice at identical inputs does not return
   identical output until it self-settles. Whether the TF-coil chain contains a stronger
   instance (an internal solve behind `a_tf_plasma_case`) is precisely what we cannot see
   statically and suspect you can.

## Why we care, and why you might

For us: whether a one-pass (trust-mode) MDA is sound per deck — the answer decides a ~38 %
cost term in a planned revision of our experiment. For you: if mechanism 2 is real, "the
DSM has no back edge here" does not imply "one pass suffices", which is a caveat any
DSM-driven scheduling claim inherits; and the `physics.py:387/395` stale read may merit an
upstream note regardless (benign under iteration; a silent one-iteration lag if anyone ever
runs the model once).

Denominators and artifacts: run records under our `arch_surgery/idf_probe/runs/a28/`
(h5 campaign, ladder audits); censuses reproducible via `a30_critique.py` and
`a28_analysis.py` at our tip. Ask and we will point at exact files.
