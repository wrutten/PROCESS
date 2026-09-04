# A40 (v3-prime) — the `PROCESS_ARCH_PRIME` variant point: four gates PASS with teeth, and A38's open lad term closes under the prime

> **Document status** — **CURRENT · TASK REPORT, open.** Written by task A40 (v3-prime),
> 2026-09-04, on branch `A40-v3-prime` (worktree
> `/home/wrutten/projects/PROCESS_surgery_worktrees/A40-v3-prime`), branched from
> `architecture_surgery` at `b7dbd2a9`; experiment base commit `c0ae5b28` (D2). Archived to
> `deprecated/` at merge — folder position records lifecycle, not validity (trap T3). Nothing
> is pushed; the branch is not merged (the orchestrator assesses per protocol §5).

| | |
|---|---|
| **Task** | MASTER_TODO row **A40** = V3 plan §8 row T2, decision **D19**: implement the `PROCESS_ARCH_PRIME` variant point (VP6) in `process/core/caller.py` — **the only `process/` change in V3**, driver scope, D11 not triggered, no `process/models/` edit — with additive record stamping in the two runners and the switch added to every cleared-switch list; gate it with **G1** (prime-unset byte identity), **G2** (prime-on fixed-point map), **G3** (prime-on cold chain, nof + st) and **G3c** (the lad carrier census, A35's declared scope gap), each with teeth, from one committed script (protocol §15) |
| **Verdict** | **All four gates PASS; every tooth tripped.** G1: with the switch unset the changed driver is byte-identical to the pre-change driver — 13 559 / 13 455 / 13 493 MFILE floats compared as exact hex, **0 mismatches, 0 differing lines** on all three decks. G2: from each deck's V2 reference exit snapshot, prime on vs off is bit-identical on **840/840, 846/846, 827/827** components in both a `flat_state` and a `per_module` call. G3: the verified cold chain drops from **3 outer passes to 2** on both traced decks, and the one-pass trust exit's in-run audit drops from **244 → 0** (nof) and **124 → 0** (st) components above τ, with the prime-off runs reproducing A35 exactly (nof's in-run max hex `0x1.de05b6285d3f4p-7` bit-for-bit). G3c: A35's two carrier images transfer to `low_aspect_ratio_DEMO` coefficient-exactly from a traced chain (rel. diff 3.8e-14 – 2.9e-12), and **A38's open term `tfcoil.m_tf_coil_superconductor` closes under the prime** — at both prime-on trust exits on lad the audit maximum is exactly `0x0.0p+0` with **0 components ≥ τ**. **The residual-mover set is empty on all three decks.** |
| **Script** | [`arch_surgery/idf_probe/a40_prime_gates.py`](../../idf_probe/a40_prime_gates.py), committed at `0ede9b10` **before any published run**; one comparator defect (a string check, not a measurement) fixed at `f74bb2c4` after the gate failed on it — §7. Driver change: `process/core/caller.py` at `1f176950` |
| **Runs** | **37 fresh-subprocess runs, 37/37 `status: ok`**, strictly serial (one PROCESS subprocess at a time): 6 full R optimisations (G1), 12 fixed-point single evaluations (G2), 10 cold-chain evaluations (G3), 9 evaluations (G3c). Stamps: 3 × `0ede9b10 dirty=False` (the G1 baseline side), 34 × `1f176950 dirty=False`; all 37 on branch `A40-v3-prime`, all with `tree_contains_base_commit=True`. No failure path was taken |
| **Environment** | `PROCESS_surgery_env` (`/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python`); `PYTHONPATH` pinned to this worktree in every subprocess and `process.__file__` asserted to be the worktree's own (traps T6/T10 — all 37 records read `/home/wrutten/projects/PROCESS_surgery_worktrees/A40-v3-prime/process/__init__.py`); a26 ystate + write-set artifacts; τ = 1e-6; runs under `arch_surgery/idf_probe/runs/a40/` (untracked). Reads outside the worktree: V2's Phase A reference snapshots in the main checkout, read-only |
| **Date** | 2026-09-04 |

---

## 1. Verdict table — the four gates

*Caption: one row per gate. "Criterion" is the pre-declared acceptance rule from V3 plan §5;
"measured" is the quantity the committed script recorded, taken from the gate's own JSON
record (named in the last column); "tooth" is the deliberate defect that had to be caught and
was. Counts are dimensionless component or line counts; hex literals are exact IEEE-754
doubles; τ = 1e-6 on the a26 scaled ystate ruler. Populations are per deck as stated —
nothing is pooled across decks.*

| gate | criterion (plan §5) | measured | tooth | verdict | record |
|---|---|---|---|---|---|
| **G1** prime unset, byte identity | MFILE hex floats identical to a run at the pre-T2 commit, 3 decks, both runs fresh at their own commits | 13 559 / 13 455 / 13 493 floats, **0 hex mismatches**; 16 174 / 16 435 / 18 692 lines, **0 differing**; no key present on one side only | 1 ULP on one float of a changed-side copy (`0x1.0000000000000p+0` → `0x1.0000000000001p+0`) → **1 mismatch, caught** on each deck | **PASS** | `g1/g1.json` |
| **G2** prime on, fixed-point map | from each deck's reference exit snapshot, one `flat_state` and one `per_module` call, prime on vs off, exit states bit-identical on N/N (827/840/846) | **840/840, 846/846, 827/827 identical** in *both* call modes; 0 differing on all six comparisons | a 1-ULP doctored `blanket.deg_blkt_inboard_poloidal_plasma` → **1 differing, tripped** on each deck | **PASS** | `g2/g2.json` |
| **G3** prime on, cold chain (nof + st) | verified outer passes 3 → **2**; trust one-pass exit's in-run `exit_audit` **0 above τ**; any residual mover named | nof **3 → 2**, trust audit **244 → 0**; st **3 → 2**, trust audit **124 → 0**; residual-mover set **empty** on both | prime-off must reproduce A35: nof 3 passes ✓, 244 ✓, max hex `0x1.de05b6285d3f4p-7` ✓ (bit-for-bit); st 3 passes ✓, 124 ✓, mantissa tail `f0afff76` ✓ | **PASS** | `g3/g3.json` |
| **G3c** lad carrier census | A35's `trace` + `restarts` stages on `low_aspect_ratio_DEMO`, prime off then on: the carrier coefficients on that deck, and the residual-mover set with the prime | A35's two images reproduce from source coefficients at rel. diff 3.8e-14 – 2.9e-12 on three entries; **A38's open term closes** — prime-on trust exits (cold and δ = 0.10) at audit max exactly `0x0.0p+0`, **0 ≥ τ**; residual-mover set **empty** | parser tooth: a 1-ULP doctored before-hex (`blanket.dz_pf_cryostat`) breaks the scaled recompute while the clean one matches — **tripped** | **PASS** | `g3c/g3c.json` |

Collated verdict `analysis/summary.json`: `all_pass: true`, four `PASS` rows.

---

## 2. The variant point (VP6) — the only `process/` change in V3

`process/core/caller.py` at `1f176950`; 63 inserted lines, nothing removed, nothing else in
`process/` touched (`git show --stat 1f176950` — one file).

**What it primes and why.** `FirstWall.set_fw_geometry` writes `build.dr_fw_inboard` and
`build.dr_fw_outboard` from two pure deck inputs — `c0ae5b28:process/models/fw.py:347-352`
(unchanged in the working tree, same lines):

```
349  self.data.build.dr_fw_inboard = (
350      2 * self.data.fwbs.radius_fw_channel + 2 * self.data.fwbs.dr_fw_wall
351  )
352  self.data.build.dr_fw_outboard = self.data.build.dr_fw_inboard
```

`Build` reads the pair earlier in the executed schedule —
`c0ae5b28:process/models/build.py:836` inside `calculate_vertical_build` (defined at `:152`),
and `:1867`, `:1877`, `:1887` inside `calculate_radial_build` (defined at `:1638`) — so under
a one-pass block schedule it reads the *previous* pass's values. The prime executes that one
method at the head of every sweep so `Build` reads this pass's value. It is a driver choice
about *when* an existing model method runs; **no file under `process/models/` changes** and
`FirstWall`'s own execution is untouched — the prime *duplicates* a run-constant of two
floating-point operations.

**Where it sits.** Module level, beside the VP1 sequence variant point: `_PRIME =
{"off": False, "fw_geometry": True}`, `PRIME_NAME` read from `PROCESS_ARCH_PRIME`
(empty or unset → `"off"`), a `RuntimeError` on an unrecognised value, `PRIME_FW_GEOMETRY`,
and the counter `PRIME_CALLS` (the `NODE_CALLS` one-cell-list pattern) — working tree
`caller.py:70-116` at `1f176950`. The call site is in `Caller._call_models_once` after the
stellarator and IFE early returns and before the tokamak sequence — working tree
`caller.py:1520-1532`; at the base commit the corresponding point is between
`c0ae5b28:process/core/caller.py:279` (the IFE `return`) and `:282` (the `# Tokamak calls`
comment), inside `_call_models_once` defined at `c0ae5b28:process/core/caller.py:249`. The
base-commit file is 530 lines; the working tree's is 1818, which is why the two line numbers
differ so widely.

**Why it is not routed through `Caller._node`.** `_node` is the counted-call wrapper: every
node it dispatches increments `NODE_CALLS`, and `NODE_CALLS` is V2's and V3's *cost unit* —
the acceptance quantity for the whole partition experiment. Routing the prime through `_node`
would add one counted node call per sweep to the block arms and none to the flat arm, which
would inflate every block-arm count against V2's recorded numbers and make the count ratios
non-commensurable with the V2 campaign. The prime is therefore **stamped, not counted**: it
increments its own `PRIME_CALLS` cell, the runners record that as `n_prime_calls`, and the
tally publishes it as a footnote beside the node-call tables and never pools it into them
(V3 plan §2; trap T11 — no silent work). The cost it hides is bounded and disclosed: two
floating-point operations per sweep, identical bits every time.

**The coverage requirement, verified rather than asserted.** Plan §2 states the requirement
(the site must be on every block sweep's path, not only the flat loop's, because
`Caller._sweep_block` runs a block by calling `_call_models_once` with the node filter set)
and leaves T2 to confirm it by counting. Every prime-on run in this task records
`n_prime_calls` and its own `block_sweeps`, and the gate script compares them per run. All
**13 prime-on runs** satisfy `n_prime_calls == block_sweeps`, and all **21 prime-off runs**
that carry the switch record `n_prime_calls == 0`:

*Caption: coverage per prime-on run, all decks and all four gates. `n_prime_calls` is the
stamped invocation counter (whole-run total for `run_one`, the measured call's delta for
`v2_eval_one`, frozen before the uncharged exit audit); `block_sweeps` is the same run's
recorded block-sweep count. Both are dimensionless counts from each run's `metrics.json`, as
collated into the gate records. Every prime-off run in the task records 0 and is not listed.*

| gate | run | deck | `n_prime_calls` | `block_sweeps` | equal |
|---|---|---|---|---|---|
| G2 | `flat_state_on` | nof / lad / st | 1 / 1 / 1 | 1 / 1 / 1 | ✓ |
| G2 | `per_module_on` | nof / lad / st | 4 / 4 / 5 | 4 / 4 / 5 | ✓ |
| G3 | `verified_on` | nof / st | 17 / 21 | 17 / 21 | ✓ |
| G3 | `trust_on` | nof / st | 14 / 17 | 14 / 17 | ✓ |
| G3c | `verified_on_cold` | lad | 16 | 16 | ✓ |
| G3c | `trust_on_cold` | lad | 13 | 13 | ✓ |
| G3c | `trust_on_warm10` | lad | 13 | 13 | ✓ |

**The unrecognised-value raise is in the source but is not gated.** `caller.py:103-108`
(working tree at `1f176950`) raises `RuntimeError` rather than defaulting when
`PROCESS_ARCH_PRIME` holds an unknown
value, which is what the MASTER_TODO row and plan §2 ask for. It is stated here as a property
of the committed source, read from the file — **no stage of `a40_prime_gates.py` exercises
it, and no artifact in `runs/a40/` records it.** The gate script has stages `g1base`, `g1`,
`g2`, `g3`, `g3c`, `analyze` and no smoke stage. A future task adding a smoke stage would
close the gap; this report does not claim the behaviour was measured.

**Stamping and the cleared-switch lists (additive only).** `run_one.py` and `v2_eval_one.py`
gained, at `0ede9b10`:

- `env_PROCESS_ARCH_PRIME` — the raw environment value;
- `arch_prime_name` — read from the **imported module** (`getattr(_caller, "PRIME_NAME",
  None)`), never the environment echoed back (the A3/A13/A24 pattern), so a tree predating the
  variant point reports `None` rather than the arm the driver asked for;
- `n_prime_calls` — `run_one`: the whole-run counter; `v2_eval_one`: the measured call's
  delta, frozen before the uncharged exit audit whose fresh `Caller` also primes.

The three G1 baseline records demonstrate the predating-tree behaviour directly: all three
fields read `None` there, while the changed side at the same environment reads
`arch_prime_name="off"`, `env_PROCESS_ARCH_PRIME=None`, `n_prime_calls=0`. `PROCESS_ARCH_PRIME`
joined `run_a28._ARCH_VARS`, the cleared-switch tuple every environment composer inherits
(`v2_runner._ALL_ARCH_VARS` by import — the frozen V2 directory is not edited — and the
a31…a38 task scripts through `run_a28.env_for`). The gate script's own `CLEARED` tuple carries
it too. V2's records and its `--verify` path are untouched.

---

## 3. Gate G1 — prime unset, byte identity across the change

Staged across two commits per protocol §15 so both sides carry clean stamps. The baseline
optimisations ran at `0ede9b10` (gate script and stamping only, no `process/` change), and
that stage **refuses to run** unless three conditions hold, each recorded rather than
asserted in prose: `caller.py` does not yet contain `PROCESS_ARCH_PRIME`; the worktree is
clean; and `HEAD:process` equals `b7dbd2a9:process`. The recorded hashes are
`cdaef03ee866b63675a9273c3b20718cdcdfc053` on both sides of that last comparison — a git fact
in `g1/baseline_provenance.json`, not a claim. The changed side ran at `1f176950`, whose
`process/` tree hash is `f117a8544a8e2634f347cdbd7d2b80ba88cc8ff8`: the two sides differ in
`process/` exactly and only by the variant-point commit.

Comparator: `compare_a3._floats` — every MFILE float re-parsed and compared as an exact hex
literal — plus whole-line identity with volatile metadata keys excluded; the A3 gate lineage.

*Caption: one row per deck. Each row is one full R optimisation per side (`run_one.py --mode
control`, every architecture switch cleared, identical environments), the two MFILEs compared
float-by-float as exact hex and then line-by-line. Counts are dimensionless. The tooth is a
1-ULP edit to one float on a copy of the changed-side MFILE, which the same comparator must
catch. From `g1/g1.json`.*

| deck | floats compared | hex mismatches | keys on one side only | lines compared | differing lines | changed-side stamp | tooth (1 ULP on a copy) | verdict |
|---|---|---|---|---|---|---|---|---|
| `large_tokamak_nof` | 13 559 | **0** | 0 | 16 174 | **0** | `arch_prime_name="off"`, `n_prime_calls=0` | 1 mismatch — caught | **PASS** |
| `low_aspect_ratio_DEMO` | 13 455 | **0** | 0 | 16 435 | **0** | 〃 | 1 mismatch — caught | **PASS** |
| `st_regression` | 13 493 | **0** | 0 | 18 692 | **0** | 〃 | 1 mismatch — caught | **PASS** |

The tooth doctors the same construction on each deck: the first finite non-zero MFILE value
token, `1` → `1.00000000000000022e+00`, i.e. `0x1.0000000000000p+0` → `0x1.0000000000001p+0`,
producing exactly one hex mismatch. Baseline records carry `arch_prime_name=None`,
`env_PROCESS_ARCH_PRIME=None`, `n_prime_calls=None` — the pre-change tree reporting itself as
such.

---

## 4. Gate G2 — prime on, the fixed-point map is bit-identical

From each deck's V2 Phase A reference exit snapshot — main checkout
`arch_surgery/MDA_partitioning_experiment_v2/runs/phase_a/campaign/<deck>/reference/y_exit.json`,
read-only, each stamped `ba69c05d dirty=False` and each snapshot's sha256 recorded in
`g2.json` — one `flat_state` call and one `per_module` call, prime on vs off, environments
otherwise identical and the pulsed decks pinned at the reference's own burn-time hex
(nof `0x1.41043caef8d92p+11`, lad `0x1.44eb0e25837b3p+13`; st is not pulsed and carries no pin).

*Caption: one row per deck; the two comparison columns are full-component comparisons of the
two arms' exit snapshots (every component kind, not only floats), N being the deck's full a26
spec component count. The coverage column repeats the measured call's `n_prime_calls` against
its block sweeps. The tooth is a 1-ULP doctored copy of one exit-state component, which the
same comparison must trip. From `g2/g2.json`.*

| deck | `flat_state` on vs off | `per_module` on vs off | coverage (on): flat / per_module | tooth | verdict |
|---|---|---|---|---|---|
| `large_tokamak_nof` | **840 / 840 identical**, 0 differing | **840 / 840 identical**, 0 differing | 1 = 1 / 4 = 4 | `blanket.deg_blkt_inboard_poloidal_plasma` `0x1.ff303960c98b5p+6` → `…b6p+6`: 1 differing — tripped | **PASS** |
| `low_aspect_ratio_DEMO` | **846 / 846 identical**, 0 differing | **846 / 846 identical**, 0 differing | 1 = 1 / 4 = 4 | same component, `0x1.02b8589a086aep+7` → `…afp+7`: 1 differing — tripped | **PASS** |
| `st_regression` | **827 / 827 identical**, 0 differing | **827 / 827 identical**, 0 differing | 1 = 1 / 5 = 5 | same component, `0x1.2207dc1466873p+7` → `…74p+7`: 1 differing — tripped | **PASS** |

At a fixed point the pair already holds its run-constant, so the prime writes the identical
bits — measured, on every component of every deck, in both call modes. The exit-audit maxima
agree hex-for-hex between the arms as well (nof flat `0x1.3599f43fc8ddap-32` both ways,
per-module `0x1.9fa768dbe4c0bp-36` both ways; lad exactly `0x0.0p+0` in all four arms; st
`0x1.eae3a0e959de8p-34` in all four).

This is the bit-inertness that licenses **O5** (V3 plan §3, resolved 2026-09-04: no prime-free
Phase B twin arms): after call 1 the prime changes nothing, so a paired B2u/B3u ladder would
cost roughly 150 optimisations to show a difference the dust floor cannot resolve.

---

## 5. Gate G3 — prime on, cold chain (A35's stages, nof + st)

A35's construction exactly: per deck one flat cold reference (traced; the pin source), then
the A1′ block chain from the cold deck entry — a verified outer chain (traced, full census
from pass 1) and a one-pass trust chain — prime off and prime on, pinned at the
flat-converged burn hex on the pulsed deck.

**The operationalization, named** (the gate row requires it, because A35 recorded two). The
quantity here is the **in-run `exit_audit`**: one further full sweep of the complete model set
at the run's exit, residual taken on the a26 ystate ruler, count = `brief.n_above` at
τ = 1e-6. That is the construction A35's critical-assessment section (the second of its two
sections numbered 9) reports as **244 / 124**. The *other* construction there — the
analyzer's snapshot pair, A35's flat-reference exit against the trust exit — reads **243** on
nof at `0x1.de05b6285d0b6p-7`, a documented ±1 near-τ spread. This gate computes the in-run
number, so a reproduced 243 elsewhere is not a discrepancy with anything below.

*Caption: one row per traced deck. "Verified passes" are the block chain's outer passes to
convergence (with the run's block-sweep count beside, both dimensionless). The trust columns
are the one-pass chain's in-run `exit_audit`: the count of a26 spec components with scaled
residual ≥ τ = 1e-6, and the exact hex of the maximum, with the argmax named. "Residual
movers" is the set the gate is required to name — components still above τ at the prime-on
trust exit. Coverage is `n_prime_calls` vs `block_sweeps` on the prime-on runs; every
prime-off run recorded 0. From `g3/g3.json`.*

| deck | verified passes off → on (sweeps) | trust audit, prime OFF: n ≥ τ, max hex (argmax) | trust audit, prime ON: n ≥ τ, max hex (argmax) | residual movers | coverage (on) | verdict |
|---|---|---|---|---|---|---|
| `large_tokamak_nof` | **3 → 2** (25 → 17) | **244**, `0x1.de05b6285d3f4p-7` (`build.dz_tf_upper_lower_midplane`) | **0**, `0x1.51fbaf5134221p-30` (`pf_coil.stress_z_cs_self_midplane_profile`) | **none** (empty set) | verified 17 = 17; trust 14 = 14 | **PASS** |
| `st_regression` | **3 → 2** (28 → 21) | **124**, `0x1.25880f0afff76p-6` (`build.dr_shld_vv_gap_outboard`) | **0**, `0x1.c22fb514702ddp-29` (`superconducting_tfcoil.a_tf_plasma_case`) | **none** (empty set) | verified 21 = 21; trust 17 = 17 | **PASS** |

The two prime-off argmaxes are precisely A35's two named carrier images — the TF-top clearance
on nof and the outboard shield gap on st — and both are gone at the prime-on exit. The
prime-on trust exits sit at 1.23e-9 (nof) and 3.28e-9 (st), roughly three orders of magnitude
below τ; the pin is recorded intact at every nof exit.

*Caption: the G3 teeth. Each row is one required reproduction of an A35 quantity by the
prime-off arm of this task's chain, with the constant the gate script compares against
(`A35_OUTER_PASSES`, `A35_INRUN_N_ABOVE`, `A35_INRUN_MAX_HEX_NOF`,
`A35_INRUN_MAX_HEX_TAIL_ST` at `a40_prime_gates.py:133-138`). A tooth passes only on exact
reproduction — counts equal, hex equal. From `g3/g3.json`.*

| deck | outer passes | n ≥ τ | max hex | reproduced |
|---|---|---|---|---|
| `large_tokamak_nof` | 3 = A35's 3 | 244 = A35's 244 | `0x1.de05b6285d3f4p-7` = A35's, **bit-for-bit** | ✓ ✓ ✓ |
| `st_regression` | 3 = A35's 3 | 124 = A35's 124 | mantissa tail `f0afff76` = A35's printed tail | ✓ ✓ ✓ |

A35 prints st's in-run maximum only by its mantissa tail, which is why the st row compares a
tail and not a full literal; §7 records that this check was wrong on its first execution and
how it was fixed.

The pre-declared claim of plan §2 — *with the prime, no cut edge on these decks carries a
displaced value into a one-pass exit* — therefore holds on both traced decks, with the
residual-mover set empty rather than merely small.

---

## 6. Gate G3c — the lad carrier census, and the verdict on A38's open term

`low_aspect_ratio_DEMO` is the deck A35 never traced and the deck on which A38 left one term
open. Nine runs: one flat cold reference (traced); verified chains traced from the cold entry
and from two displaced-warm entries (δ = 0.10 and δ = 0.05, seed 1 — A35's stream, the pin
displaced by the component's own stream factor); trust runs from the cold and δ = 0.10
entries; all prime off. Then, prime on: verified cold, trust cold, trust δ = 0.10.

### 6.1 A35's two carrier images on lad, source-grounded

A38 showed from *records* that A35's two coefficients transfer to lad (25/25 runs, rel. diff
1.4e-12 – 1.3e-11). This is the source-grounded confirmation from a chain traced on the deck
itself. The predictions are not fitted: they come from the code at the base commit.
`c0ae5b28:process/models/build.py:835-836` adds `0.5 * (dr_fw_inboard + dr_fw_outboard)` into
`z_tf_top`, from which `dz_tf_upper_lower_midplane` is written at `:840`; and
`c0ae5b28:process/models/build.py:1940-1947` writes `dr_shld_vv_gap_outboard` by subtraction,
carrying the outboard displacement with unit magnitude.

*Caption: one row per traced verified entry (prime off), all on `low_aspect_ratio_DEMO`. The
Δ columns are the pair's pass-1 raw displacement in metres. Each image column is the relative
difference between that image's measured pass-2 raw movement and its **source-coefficient**
prediction — 0.5·(Δin + Δout) for the TF-top clearance, |Δout| for the outboard shield gap —
so the number is dimensionless and no coefficient is fitted. From `pass_trace.jsonl` via the
committed closure stage; recorded in `g3c/g3c.json` under `carrier_closure`.*

| entry | Δ`dr_fw_inboard` (m) | Δ`dr_fw_outboard` (m) | `dz_tf_upper_lower_midplane` rel. diff | `dr_shld_vv_gap_outboard` rel. diff |
|---|---|---|---|---|
| cold | 1.800000e-2 | 1.800000e-2 | 6.09e-14 | 3.78e-14 |
| δ = 0.10 | 5.466945e-4 | 5.317004e-4 | 3.64e-13 | 9.33e-13 |
| δ = 0.05 | 2.733472e-4 | 2.658502e-4 | 2.93e-12 | 9.40e-13 |

Six checks, all between 3.8e-14 and 2.9e-12: same code path, same coefficients,
coefficient-exact on the third deck. The cold chain's pass-2 owner tally is **90 M3 + 87 M2
with zero M1 or PULSE movers** out of 177 movers — A35's attribution pattern (its cold tallies
were 88 M2 + 93 M3 on nof and 5 M2 + 77 M3 on st, likewise with zero M1/PULSE), now reproduced
on the third deck.

### 6.2 The open term `tfcoil.m_tf_coil_superconductor` — it closes

**Stated plainly: A38's open term is carried by the first-wall pair, and the prime eliminates
it completely.** With the pair primed and nothing else changed, the term is exactly zero bits
at every prime-on trust exit — including the δ = 0.10 displaced entry, where every other
component of the coupling state is also perturbed. That isolates the pair as its sole source.

**But the map is not linear, and the report does not claim it is.** A38 could not close the
term because a two-coefficient linear fit over 25 seeds left a residual median of 0.067 and a
maximum of 0.92. This task's three-entry check reaches the same conclusion from a different
direction and with far better conditioning: solving (a, b) *exactly* from the cold and
δ = 0.10 entries gives (−21.07, +55.70), which then predicts the δ = 0.05 entry to **1.57e-2**
relative. That is much closer than A38's ensemble fit and still three orders of magnitude
worse than the two direct pair images measured on the very same runs (3.8e-14 – 2.9e-12,
§6.1). A linear image of the pair closes at 1e-13; this one does not. The displacement-ratio
test says the same thing: halving the displacement divides the term's movement by **1.9685**,
where the pair's own inputs halve at 2.000 and both direct images track them at 2.0000000.

The right description is therefore a **nonlinear but pair-driven downstream response**, not a
second independent carrier. It is produced inside block M2 by `cicc_sctfcoil` (the CICC
TF-coil model), consuming `Build`'s pair-displaced radial and vertical build within the same
pass; the write census and the block schedule give writer node `cicc_sctfcoil`, writer block
M2, owner block M2. Priming the pair removes the input displacement, and the response goes to
zero with it.

*Caption: the open term's evidence, all from `g3c/g3c.json` (`open_term`, `carrier_closure`).
Raw movements are the term's pass-2 change in tonnes on the deck's own scale; "scaled" values
are dimensionless residuals on the a26 ystate ruler; hex literals are exact. The
two-coefficient solve is exact by construction from two entries and is then **required to
predict the third**, which is what a linear image of the pair must do and what this term
fails to do. Populations: three traced verified entries (prime off) for the movement rows;
four one-pass trust exits (two prime off, two prime on) for the exit rows.*

| quantity | value |
|---|---|
| writer chain | `cicc_sctfcoil` → `tfcoil.m_tf_coil_superconductor`; writer block **M2**, owner block **M2**; moved by `Build`'s pair-displaced radial/vertical build inside the same pass |
| pass-2 raw movement (cold / δ = 0.10 / δ = 0.05) | 0.623407 / 1.80989e-2 / 9.19415e-3 |
| pass-2 scaled value, and rank | 4.0028e-2 / 1.1621e-3 / 5.9034e-4 — **the pass-2 argmax on all three entries** (A38's records made it lad's restricted argmax in 21 of 25 seeded runs) |
| two-coefficient solve (a, b) from cold + δ = 0.10 | (**−21.07**, **+55.70**); predicts δ = 0.05 at 9.04944e-3 against a measured 9.19415e-3 → rel. error **1.57e-2**, i.e. **not one linear image** (A38's 25-seed fit (17.4, 15.3), residual median 0.067, max 0.92, reached the same verdict from records) |
| displacement ratio, δ = 0.10 over δ = 0.05 | **1.9685** — displacement-carried but mildly nonlinear; the pair's inputs give 2.000 and its two direct images 1.9999999999934 / 2.0000000 |
| trust exit, prime **OFF** | cold: scaled **4.0028e-2** (`0x1.47e807abb1ed5p-5`), **240** components ≥ τ; δ = 0.10: **1.1621e-3** (`0x1.30a27ad23ca7fp-10`), **218** ≥ τ — the term is the top mover at both |
| trust exit, prime **ON** | cold **and** δ = 0.10: audit maximum exactly **`0x0.0p+0`**, **0** components ≥ τ, top-mover set empty — the term and every other mover gone to the bit |
| verified outer passes off → on | **3 → 2** (23 → 16 block sweeps); the prime-on pass-2 receipt is exactly `0x0.0p+0`, 0 ≥ τ |
| residual movers with the prime | **none** — empty set at both prime-on trust exits |

**What this settles for V3 §4.1 in advance of the campaign.** The A0/A1 similarity check has
nothing left to fail on for lad once the prime is in the arm: the entire one-pass deficit A38
measured there (restricted median 9.8e-4, p90 2.19e-3, argmax the TF-coil superconductor mass
in 21 of 25 runs) is pair-carried. The carrier-closure tally construction (T-e) still has no
per-run *linear* coefficient for this term, and §6.2 says why one should not be invented: the
correct per-run prediction on lad under the prime is **zero**, and A35's two images remain
exact for the prime-free A1u arm.

### 6.3 G3c teeth, coverage, and one honest limit on the parser check

The parser tooth (A35's G3 lineage) is a scaled-recompute check on the traced chain: for a
component's recorded before/after hexes, the scaled residual is recomputed and compared with
the recorded one. Doctoring `blanket.dz_pf_cryostat`'s before-hex by 1 ULP breaks the
recompute while the clean value matches — **tripped**.

*Caption: the scaled-recompute check applied to every traced run of G3c, prime off and on.
`n_checked` is the number of pass-2 mover components whose scaled residual was recomputed from
their recorded hexes — a dimensionless count, and it is the population the "0 mismatches"
statement holds over. From `g3c/g3c.json` (`teeth.scaled_recompute_all_traced`).*

| traced run | components checked | mismatches | note |
|---|---|---|---|
| `verified_off_cold` | 142 | **0** | |
| `verified_off_warm10` | 122 | **0** | |
| `verified_off_warm05` | 120 | **0** | |
| `verified_on_cold` | **0** | 0 | **vacuous**: with the prime on there are no pass-2 movers to check |

The fourth row is reported rather than folded into a "four runs, 0 mismatches" statement,
because it checks nothing. Its zero is a *consequence* of the result being reported — the
prime-on chain's pass 2 is bit-clean, so the census has no mover rows to recompute — and
reading it as a fourth passing check would be exactly the aggregate-without-its-condition
error of trap T11. The parser check's real population is **384 components across the three
prime-off traced runs, 0 mismatches**.

Coverage: `n_prime_calls` equals `block_sweeps` on every prime-on run (16 = 16, 13 = 13,
13 = 13) and is 0 on every prime-off run. The burn-time pin is recorded intact at every exit
of all eight chain runs.

Two further items recorded for honesty, neither affecting a verdict. First, the pass-3
receipts of the three prime-off verified chains are exactly `0x0.0p+0` on the cold and δ = 0.10
entries but **4.46e-15** (`0x1.4168b4f20b2ffp-48`) on δ = 0.05 — 0 components ≥ τ in all three,
so the chains are converged, but "bit-clean" is literally true only of the first two. Second,
the pass-1 maximum on the cold entries is reported as `inf` (argmax
`ccfe_hcpb.pnuc_tot_blk_sector`) because the scaled ruler divides by a before-value that is
zero at a cold entry; pass-1 magnitudes on a cold chain are therefore not comparable
quantities and no claim in this report rests on one. Pass-1 *counts* (665 ≥ τ on lad cold) are
unaffected.

---

## 7. One comparator defect, disclosed

The first execution of G3 **failed on its own tooth** at `st_regression`. The measured in-run
maximum was `0x1.25880f0afff76p-6`, whose mantissa ends in A35's printed tail `f0afff76` — but
the check applied `endswith` to the *full* hex literal, including the `p-6` exponent suffix,
and so reported FAIL while every measured quantity had in fact reproduced (3 outer passes,
124 components ≥ τ, and the tail digits themselves). The comparison operator was wrong; the
measurement was not.

Fixed at `f74bb2c4` — `mantissa = hex.split("p")[0]`, then the tail check — with **no run, no
setting and no threshold changed**. The recorded runs were reused unchanged and only the
verdict recomputed, and the records prove it rather than asserting it: `g3.json`'s collation
provenance reads `f74bb2c4`, while all eight of its chain runs carry `tree_git_head =
1f176950`, and `git rev-parse` gives the identical `process/` tree hash
`f117a8544a8e2634f347cdbd7d2b80ba88cc8ff8` at `1f176950` and at `f74bb2c4` (the fix touched
only `a40_prime_gates.py`, 10 insertions, 3 deletions). This is the A38 §6 class of machinery
defect — a defect in the instrument's bookkeeping, not in what it measured — disclosed here
rather than silently absorbed. It is not a gate that was tuned to pass: the gate's criterion,
its constants and its runs are exactly as committed at `0ede9b10`.

---

## 8. Provenance and reproduction

Every run: fresh subprocess, own working directory, `PYTHONPATH` pinned to this worktree, and
the exact tree asserted in-process — all 37 records read `process_file =
/home/wrutten/projects/PROCESS_surgery_worktrees/A40-v3-prime/process/__init__.py` and
`tree_contains_base_commit = true` (traps T6 and T10; the assertion is on the path, never on
`__version__`). Strictly serial: one PROCESS subprocess at a time. Every published quantity in
this report is a count, a name, or an exact hex float; **no wall clock appears anywhere as
evidence**.

*Caption: the task's run inventory and stamps. One row per gate stage; "runs" counts
fresh-subprocess PROCESS executions. All statuses are from each run's own `metrics.json`
(`status` field); stamps are `tree_git_head` / `tree_git_dirty` from the same records. The
prime column tallies `arch_prime_name` as the imported module resolved it. From the 37
`metrics.json` records under `runs/a40/`.*

| stage | runs | composition | status | stamp | `arch_prime_name` |
|---|---|---|---|---|---|
| `g1base` | 3 | 3 full R optimisations, baseline side | 3/3 ok | `0ede9b10` clean | `None` ×3 (tree predates the variant point) |
| `g1` | 3 | 3 full R optimisations, changed side | 3/3 ok | `1f176950` clean | `off` ×3 |
| `g2` | 12 | 3 decks × {flat, per_module} × {off, on} | 12/12 ok | `1f176950` clean | `off` ×6, `fw_geometry` ×6 |
| `g3` | 10 | 2 flat cold refs + 2 decks × {verified, trust} × {off, on} | 10/10 ok | `1f176950` clean | `off` ×6, `fw_geometry` ×4 |
| `g3c` | 9 | 1 flat cold ref + 5 prime-off chains + 3 prime-on chains | 9/9 ok | `1f176950` clean | `off` ×6, `fw_geometry` ×3 |
| **total** | **37** | | **37/37 ok** | 3 × `0ede9b10`, 34 × `1f176950`, all `dirty=False`, all branch `A40-v3-prime` | `off` 21, `fw_geometry` 13, `None` 3 |

Commits on this branch, off `architecture_surgery` at `b7dbd2a9`:

| commit | what | `process/` tree hash |
|---|---|---|
| `b7dbd2a9` | branch point | `cdaef03e…` |
| `0ede9b10` | gate script (1153 lines) + additive runner stamping + `_ARCH_VARS` entry — committed **before any published run** (§15) | `cdaef03e…` (unchanged) |
| `1f176950` | the `caller.py` variant point, +63 lines, one file | `f117a854…` |
| `f74bb2c4` | G3's st tail check compares the mantissa, not the full literal (§7) | `f117a854…` (unchanged) |

*Caption: this branch's commits in order, with the `process/` subtree hash at each
(`git rev-parse <commit>:process`). Equal hashes mean the driver is byte-identical between
those commits; the only change to `process/` on this branch is `1f176950`.*

Reads outside the worktree, all read-only: V2's three Phase A reference exit snapshots in the
main checkout, each stamped `ba69c05d dirty=False` with its sha256 recorded in `g2.json`
(`8aa1db54…` nof, `7ce88737…` lad, `13abcef7…` st). No sibling clone was written.

Reproduction, from the worktree root:

```
cd arch_surgery/idf_probe
python a40_prime_gates.py g1base    # 3 runs, at 0ede9b10 (pre-change driver, asserted)
# -- commit 1f176950 (the caller.py variant point) --
python a40_prime_gates.py g1        # 3 runs + comparison + teeth        (section 3)
python a40_prime_gates.py g2        # 12 runs                            (section 4)
python a40_prime_gates.py g3        # 10 runs                            (section 5)
python a40_prime_gates.py g3c       # 9 runs                             (section 6)
python a40_prime_gates.py analyze   # 0 runs: collation -> analysis/summary.json
```

Failure paths are reachable from the same entry point and none was taken: `g1base` refuses if
`caller.py` already carries the prime, if the worktree is dirty, or if `HEAD:process` differs
from `b7dbd2a9:process`; every stage marks a non-zero return code or a non-`ok` status as a
failure path and reports it.

Which record holds which figure: §3 — `runs/a40/g1/g1.json` (and
`g1/baseline_provenance.json`); §4 — `runs/a40/g2/g2.json`; §5 — `runs/a40/g3/g3.json`;
§6 — `runs/a40/g3c/g3c.json` (closure, census, open term, survival, teeth, coverage);
§1 collation — `runs/a40/analysis/summary.json`. Per-run raw artifacts (`metrics.json`,
`pass_trace.jsonl`, `audit_residual.json`, `y_exit.json`) sit beside each run under
`runs/a40/{g1,g2,chains,refs}/`. Bulk run artifacts stay untracked; this report and the gate
script are what is committed.

---

## 9. Change log

- 2026-09-04 — task opened in worktree `A40-v3-prime`; mandatory reads done (CLAUDE.md,
  TRAPS.md, V3 plan §2/§5/§6, A35 and A38).
- 2026-09-04 — `0ede9b10`: gate script + additive runner stamping + `run_a28._ARCH_VARS` entry
  committed before any run. G1 baseline executed (3/3 ok, clean stamps, `process/` tree hash
  asserted equal to `b7dbd2a9:process`).
- 2026-09-04 — `1f176950`: the `caller.py` variant point, the only `process/` change.
- 2026-09-04 — G1 changed side, G2, G3 and G3c executed (34 runs, all ok). G3 FAILED on its
  own st tail-check comparator; fixed at `f74bb2c4` (§7) and the verdict recomputed from the
  unchanged records. `analyze` collated: all four gates PASS.
- 2026-09-04 — **the executing session terminated on a model rate limit after the gates had
  run and before the task report was committed.** All 37 run records, the four gate JSONs and
  the collation were already on disk; the branch carried the three commits above.
- 2026-09-04 — **resumed by a second session to verify and write up only** — no gate was
  re-run, no driver code changed, no campaign re-executed. Every figure in this report was
  re-read from the JSON records and the git objects, and every `process/` line number was
  re-verified at `c0ae5b28` with `git show`. Three corrections were made to the draft that the
  first session left uncommitted in the working tree: (1) the parser tooth's fourth traced run
  checks **0** components, not a fourth passing check, and is now reported as vacuous with the
  real population named (§6.3); (2) the "unrecognised value raises" behaviour is present in the
  committed source but is **not exercised by any gate stage and has no artifact**, so the
  draft's "smoke-checked with `bogus`" claim was removed and the gap disclosed (§2);
  (3) the δ = 0.05 verified chain's pass-3 receipt is 4.46e-15, not exactly `0x0.0p+0`, so the
  "bit-clean receipt" statement was qualified (§6.3). No measured quantity changed. Report
  committed.
