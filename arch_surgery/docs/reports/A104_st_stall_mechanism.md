# A104 (st-stall-mechanism) — why `st`'s partitioned arm stalls at τ = 1e-8, and what the loop tolerance costs against PROCESS's own loop

> **Document status** — **OPEN.** Task A104 (st-stall-mechanism), 2026-09-30, branch
> `A104-st-stall-mechanism`, worktree `.claude/worktrees/A104-st-stall-mechanism`, base `44bc70f3`.
> Exploratory measurement for the open question OQ-tolerance (queue §5); **proposes nothing as
> decided** — the loop tolerance and the test set are the user's to choose. Measurement M3 (why st's
> loops settle as they do: per-sweep decay, slowest coupling, model-code reading) was **deferred by the
> orchestrator mid-task** and is not part of this report beyond what M0's traces show in passing (§8).
> Scripts under `arch_surgery/st_stall_mechanism/`; records under
> `arch_surgery/idf_probe/runs/st_stall_mechanism/` after hand-back (untracked).

## 0. In plain language (each sentence marked **measured** or **conjecture**)

**Why the loop's test set and tolerance change the optimiser's path on st.** At st's optimum the
objective does not change when three inboard radial-build variables — the bore, the central-solenoid
thickness and the TF-coil nose case — trade against each other: the partitioned arm at τ = 1e-8 ends
up to 96 % away from the flat arm in those variables with the objective equal to within 1.5e-11 relative, and in 10 of
its 20 accepted runs with the nose case at its lower bound, which no other arm reaches (**measured**,
§4). Along such a flat direction the optimiser has nothing to follow but the errors in its
finite-difference gradient, so any loop setting that changes those errors can change where it goes
(**conjecture**). At census τ = 1e-8 the objective's finite-difference derivative on st is wrong in
steps of 5.6e-6 — 5 600 times st's optimiser tolerance — on five or six of fourteen columns, because the
loop stops after a different number of sweeps at the two points of a difference (**measured**, §5.3); at
1e-10 those steps shrink below the tolerance (**measured**), and at 1e-12 the partitioned arm stops
wandering (8 of 24 runs hover, the reference's rate; **measured**, §4).

**Why the partitioned arm is the one that takes longer.** It is not because it leaves more error: from
a converged state the flat and the partitioned loop return bit-identical values at every point tried
(four optima, three configurations), and along the optimiser's own evaluation sequence their largest
errors are equal (**measured**, §5). What differs is *where* the error falls: at both points examined
the partitioned loop puts one of its error steps on the derivative with respect to the bore — one of the
three variables of the flat direction — and the flat loop puts none there (**measured**, Table 10, two
design points); the spurious slope points the way the partitioned arm walks, towards a larger bore
(**measured**), and that this slope is what drives the walk is **conjecture** (no run removed it).

**Why st.** At their optima tok's loops give the exact value at every tolerance and with both test
sets, the reference included, and lad's are exact except for one constraint derivative at 1e-8 that is
the same in both arms (**measured**, §5.1); st's loops are exact at no tolerance above 1e-14, its
coils-block loop shrinking its change only by a factor 0.034 per sweep (**measured**, §3). st's tighter
optimiser tolerance is not what separates it: the error step at 1e-8 exceeds every configuration's
tolerance, tok's included (**measured**). That st also has a direction of exactly flat objective in which
such an error can accumulate unchecked is **conjecture** for tok and lad (not examined there). Why st's
loops do not settle exactly is measurement M3, deferred.

**The reference loop is far looser and converges as well** — because its error is in the constraints
(its constraint derivatives are wrong by 290–550 times the tolerance) while its objective derivative is
within 0.7 times the tolerance (**measured**, §5.3); the flat and partitioned loops at 1e-8 have the
opposite (**measured**). The size of the error, measured as a gradient error against the tolerance, does
**not** predict the stall: the condition declared for M4 on that basis fails its own test (**measured**,
§6).

**The user's key check — is the flat control still comparable to the reference in loop cost at the
tighter tolerances?** Comparable taken as within 10 % in node calls per evaluation, declared before the
counts (**measured**, Tables 1 and 2):

| | tok | lad | st |
|---|---|---|---|
| flat / reference, campaign's displaced entries, census 1e-8 → 1e-14 | 1.13 → 1.33 (not comparable from 1e-8) | 1.00 at every τ | 1.21 → 2.07 (not comparable from 1e-8) |
| flat / reference, optimiser-like entries, census 1e-8 → 1e-14 | 1.14 → 1.71 (not comparable from 1e-8) | 1.00 at every τ | 0.71 → 1.43 (comparable to 1e-12, not at 1e-13) |
| flat / reference in whole optimisations | 1.07 at 1e-8 | 0.99 at 1e-8 | 0.98 at 1e-8; **1.35 at 1e-12** |
| at τ = epsvmc × epsfcn (1e-10 / 1e-11 / 1e-12): flat / reference, displaced; optimiser-like | 1.20; 1.29 | 1.00; 1.00 | 1.86; 0.86 (1.35 in optimisation) |
| there: partitioned / flat | 0.41; 0.48 | 0.47; 0.63 | 0.40; 0.68 (0.42 in optimisation) |
| there: partitioned / reference | 0.50; 0.62 | 0.47; 0.52 | 0.73; 0.59 (0.56 in optimisation) |
| one decade tighter: flat / ref; partitioned / flat; partitioned / ref (displaced; optimiser-like) | 1.20, 1.43; 0.41, 0.45; 0.50, 0.64 | 1.00, 1.00; 0.47, 0.63; 0.47, 0.52 | 2.00, 1.14; 0.38, 0.55; 0.76, 0.63 |

So: the flat control stays comparable to the reference on lad at every tolerance; on st only on the
optimiser-like entries down to 1e-12; on tok not even at 1e-8 on phase A's entries, though its whole
optimisations are (1.07). Tightening the tolerance raises the flat arm's cost much more than the
partitioned arm's — on st's displaced entries from 1e-8 to 1e-12 by 53 % against 14 %, because all of
the extra sweeps are the coils block's and the flat loop repeats every model to give them — so the
partitioned-over-flat ratio flatters the partition as τ tightens and the partitioned-over-reference
ratio does not (**measured**, §3). The whole write set (V4's test) at 1e-6 is comparable on all three
on at least one entry kind (tok 1.07 displaced, lad 1.00, st 1.00 optimiser-like) and the census set is
the cheaper criterion for the partitioned arm at matched delivered accuracy on all three (§6).


---

## 1. Vocabulary

- **Reference loop** (`AR` in phase A, `BR` in phase B): PROCESS as shipped. It sweeps every model,
  and stops when the objective and every constraint agree between two successive sweeps to a relative
  1e-6 (`Caller.check_agreement`, `rtol = 1.0e-6`; two to ten sweeps).
- **Flat loop** (`A0`/`B0`; `A1`/`B1` with the burn time owned by a constant or by the optimiser):
  every model per sweep, stopping when the loop's **test set** moves by less than τ (largest change
  scaled by the component's fixed scale).
- **Partitioned loop** (`A2`/`B2`): three block loops M1 (physics), M2 (coils), M3 (plant), each
  iterated to its own test at τ, feed-forward models once per evaluation.
- **Test set**: the **census set** (V5's default, ruling D32: the couplings a block reads before it
  writes them, measured at run time) or the **whole write set** (`write_set`, V4's predicate, the
  fallback of ruling D39).
- **`epsvmc`**: the optimiser's (VMCON's) stopping tolerance on its convergence measure
  `|∇f·δ| + |Σλ c_eq| + |Σλ c_in|`. Read from the committed input files: **1e-7 (tok), 1e-8 (lad),
  1e-9 (st)** — the orchestrator's figures, confirmed (`loop_runs.epsvmc_of` asserts them against
  the files; M1 reads them from every run's own input-file copy).
- **`epsfcn`**: the finite-difference step, relative, central difference. No input file sets it
  (st's line is commented out); every record stamps 1e-3. Confirmed.
- **Stencil entry** (M0, M2): an evaluation entered from a converged state with one iteration variable
  multiplied by `1 ± epsfcn` — what the optimiser's gradient evaluator does. **Displaced entry**: the
  campaign's phase A entry, every coupling component moved by up to ±10 %.
- **Near band** (M1): the optimiser's measure below `1000 × epsvmc`.

## 2. Scripts, commits, records

| script | measurement | PROCESS runs | committed at |
|---|---|---|---|
| `loop_runs.py` | shared: one evaluation through the V5 harness pool under a chosen loop; record reader (block trace, counts, values) | — | `de76476f` |
| `loop_sweeps_against_reference.py` | **M0** | 415 evaluations (`--press`), made at `de76476f` | `de76476f` (press); tables `ea6ca92c` |
| `optimiser_path_split.py` | **M1** | none (reads the campaign's and the supplementary stage's phase B records) | `ea6ca92c` (first committed at `f7e344f1`) |
| `evaluation_error_at_optimum.py` | **M2** | 2 238 (first part) + 784 (second part: 780 chain evaluations, 4 traced optimisations) runs, made at `f7e344f1` and `4d55d561` (§8) | `f7e344f1`; second part `4d55d561`; tables `ea6ca92c` |
| `stencil_chain_error.py` | **M2**, second part (the evaluator's chain; traced optimisations) | counted in the M2 row | `4d55d561`; tables `ea6ca92c` |
| `tolerance_condition.py` | **M4** | none (reads M0's and M2's records) | `ea6ca92c` (first committed at `f7e344f1`) |

Every run: the V5 harness's warmed evaluation child (`harness/child/evaluate.py`) through
`pool.run_all`, two workers, run kind `smoke`, under this task's own root
(`runs/st_stall_mechanism/`), the campaign's committed artifacts. **No change to the harness, to the
V5 `PROCESS/` copy, to `process/models/`**; no campaign, supplementary or gate record was written,
moved or re-made. The flat and partitioned runs carry the driver's observation-only block trace
(`PROCESS_ARCH_BLOCK_TRACE`, passed as a job `override_env`, which makes them job identities no
campaign record has). Press logs: `runs/_press_logs/A104_press01…07_*.log`.

## 3. M0 — the user's key check: loop sweeps and node calls against the reference loop

**Script** `loop_sweeps_against_reference.py` (`--press` at `de76476f`, 415 of 415 runs `ok`;
`--tables` at `ea6ca92c`). **Entries**, per configuration: the campaign's own phase A displaced entries
of seeds 1, 2, 3 (the campaign's entry reference exit state, displaced by δ = 0.10 on the seed's
stream), and two **stencil** entries mimicking an optimiser evaluation: the same converged reference
state with iteration variable column 0, or column n − 1, multiplied by `1 + epsfcn`. **Loops**: `AR`
once; `A0` (flat), `A1` (flat, burn time pinned; pulsed only) and `A2` (partitioned) under the census
set at τ = 1e-8 … 1e-14 and under the whole write set at τ = 1e-6, 1e-8, 1e-10.

**Reproduction check** (measured): the displaced census-1e-8 cells are the campaign's own jobs (only the
timers and the block trace differ; neither moves a count, gate GC). **33 of 33** reproduce the campaign
record's node calls, sweeps and objective to the bit. And the campaign's own 25 phase A records per arm
give the orchestrator's figures (measured, the script's context table): sweeps per evaluation
reference **4.96 / 5.00 / 4.92** (tok / lad / st), flat control **5.88 / 5.00 / 5.96**; whole-state
exit-audit residual, median, reference **3.3e-8 / 0 / 1.5e-7**, flat control **4.5e-11 / 0 / 5.0e-9**.
All agree with the brief's numbers.

**How the loops end** (measured, block traces): **no loop reached its sweep cap** (20 sweeps per block)
at any τ down to 1e-14, on any entry. On **lad** every census loop ends at a **bit-identical** fixed
point on its test set (residual exactly 0) at every τ, and the whole-state audit reads 0 — lad's
loops are exact, so τ below 1e-8 costs nothing there. On **tok** one displaced entry in three ends
bit-identical; the rest end at τ. On **st** no flat loop ever ends bit-identical: every flat loop and
every partitioned M2 loop ends on "change below τ, not zero"; M1 and M3 end bit-identical. The
partitioned arm's **M2 block is where st's sweeps go**: its census change falls by a factor of about
**0.034 per sweep** (seed 1: 1.8e-3, 6.1e-5, 2.1e-6, 7.1e-8, 2.4e-9, 8.3e-11, 2.8e-12, 9.7e-14),
so each decade of τ costs st's M2 (and st's flat loop) about 0.65 sweeps; M1 and M3 are exact after
three sweeps. *(Why M2 contracts at that rate is measurement M3, deferred; §8.)*

**Table 1 — node calls per evaluation, ratio of means over the entries** (population: 3 displaced
entries, 2 stencil entries per configuration; construction: mean node calls of the measured evaluation
of one arm over the entries of the kind, divided by the other arm's; `flat` is `A1` on tok and lad —
the partitioned arm's pairing, ruling D34 — and `A0` on st; `A0/AR` is the stopping-rule rung, the
user's key check; **comparable** = `A0/AR ≤ 1.10`, declared before the counts were read). D = displaced,
S = stencil.

| test set | τ | tok A0/AR D, S | tok A2/flat D, S | tok A2/AR D, S | lad A0/AR D, S | lad A2/flat D, S | lad A2/AR D, S | st A0/AR D, S | st A2/flat D, S | st A2/AR D, S |
|---|---|---|---|---|---|---|---|---|---|---|
| census | 1e-8 | 1.13, 1.14 | 0.43, 0.52 | 0.49, 0.60 | 1.00, 1.00 | 0.47, 0.61 | 0.47, 0.51 | 1.21, **0.71** | 0.53, 0.69 | 0.64, 0.49 |
| census | 1e-9 | 1.13, 1.29 | 0.43, 0.48 | 0.49, 0.62 | 1.00, 1.00 | 0.47, 0.63 | 0.47, 0.52 | 1.43, 0.71 | 0.47, 0.69 | 0.67, 0.49 |
| census | 1e-10 | 1.20, 1.29 | 0.41, 0.48 | 0.50, 0.62 | 1.00, 1.00 | 0.47, 0.63 | 0.47, 0.52 | 1.57, 0.71 | 0.44, 0.69 | 0.69, 0.49 |
| census | 1e-11 | 1.20, 1.43 | 0.41, 0.45 | 0.50, 0.64 | 1.00, 1.00 | 0.47, 0.63 | 0.47, 0.52 | 1.64, 0.86 | 0.43, 0.63 | 0.70, 0.54 |
| census | 1e-12 | 1.27, 1.57 | 0.40, 0.42 | 0.50, 0.66 | 1.00, 1.00 | 0.47, 0.63 | 0.47, 0.52 | 1.86, 0.86 | 0.40, 0.68 | 0.73, 0.59 |
| census | 1e-13 | 1.27, 1.57 | 0.40, 0.42 | 0.50, 0.66 | 1.00, 1.00 | 0.47, 0.63 | 0.47, 0.52 | 2.00, 1.14 | 0.38, 0.55 | 0.76, 0.63 |
| census | 1e-14 | 1.33, 1.71 | 0.39, 0.40 | 0.51, 0.68 | 1.00, 1.00 | 0.47, 0.63 | 0.47, 0.52 | 2.07, 1.43 | 0.37, 0.47 | 0.77, 0.67 |
| write_set | 1e-6 | 1.07, 1.14 | 0.60, 0.74 | 0.60, 0.74 | 1.00, 1.00 | 0.60, 0.73 | 0.60, 0.73 | 1.21, 1.00 | 0.55, 0.60 | 0.66, 0.60 |
| write_set | 1e-8 | 1.27, 1.43 | 0.55, 0.60 | 0.62, 0.78 | 1.13, 1.33 | 0.60, 0.73 | 0.60, 0.73 | 1.43, 1.00 | 0.57, 0.60 | 0.82, 0.60 |
| write_set | 1e-10 | 1.33, 1.57 | 0.52, 0.56 | 0.63, 0.80 | 1.20, 1.33 | 0.60, 0.64 | 0.60, 0.75 | 1.86, 1.00 | 0.47, 0.76 | 0.88, 0.76 |

(`A1/AR` on the pulsed configurations, beside in the script's output: tok equals `A0/AR` under the
census set; lad census 1.00 D, 0.83 S.)

**Table 2 — the same ratios in the optimisations the campaign made** (M1's script,
`optimiser_path_split.py`, from the phase B records: solve-phase node calls over evaluations, pooled
over each configuration's seed set — 22 / 12 / 20 seeds; the supplementary stage's st records over the
same 20 seeds).

| | tok (census 1e-8) | lad (census 1e-8) | st (census 1e-8) | st (census 1e-12, supplementary) |
|---|---|---|---|---|
| reference `BR`, node calls per evaluation | 67.5 | 72.5 | 68.9 | 68.9 |
| flat `B0` / `BR` | 1.07 | 0.99 | 0.98 | **1.35** |
| partitioned over its flat comparator (`B2/B1`; st `B2/B0`) | 0.52 | 0.53 | 0.51 | 0.42 |
| partitioned / `BR` | 0.52 | 0.49 | 0.50 | 0.56 |

The brief's figures (reference 68.9, flat 67.3 at 1e-8 and 93.2 at 1e-12, partitioned 34.4 and
38.7) read here **68.9, 67.3, 93.3, 34.2, 38.8**; the orchestrator's population was not stated, mine is
the 20-seed set, ratio of sums, which explains the last-digit differences (not verified further).

**The answer to the user's key check** (measured, with the population in each clause):

- **Where comparable is lost.** On the campaign's displaced entries the flat control is **already not
  comparable at τ = 1e-8** on tok (1.13) and st (1.21), and lad stays at 1.00 at every τ (its loops
  are exact). On the optimiser-like stencil entries (two per configuration) the flat control on st is
  *cheaper* than the reference down to τ = 1e-12 (0.71 → 0.86) and loses comparability at **1e-13**
  (1.14); on tok it is 1.14 at 1e-8 already; on lad 1.00 throughout. In the campaign's whole
  optimisations (Table 2) the flat control is comparable at 1e-8 on all three (1.07 / 0.99 / 0.98) and
  **not comparable on st at 1e-12 (1.35)** — the only phase B measurement below 1e-8.
- **At the rule "τ = epsvmc × epsfcn"** (1e-10 tok, 1e-11 lad, 1e-12 st), displaced / stencil:
  flat over reference **1.20 / 1.29** (tok), **1.00 / 1.00** (lad), **1.86 / 0.86** (st; 1.35 in
  st's supplementary optimisations); partitioned over flat **0.41 / 0.48**, **0.47 / 0.63**,
  **0.40 / 0.68** (0.42 in optimisation); partitioned over reference **0.50 / 0.62**, **0.47 / 0.52**,
  **0.73 / 0.59** (0.56 in optimisation). **One decade tighter** (1e-11, 1e-12, 1e-13): flat over
  reference 1.20 / 1.43, 1.00 / 1.00, 2.00 / 1.14; partitioned over flat 0.41 / 0.45, 0.47 / 0.63,
  0.38 / 0.55; partitioned over reference 0.50 / 0.64, 0.47 / 0.52, 0.76 / 0.63.
- **The worry that a tight tolerance biases the comparison** (measured): tightening the census τ from
  1e-8 to the rule moves the partitioned-over-flat ratio by −0.02 (tok), 0 / +0.02 (lad),
  −0.13 / −0.01 (st, D / S) and the partitioned-over-reference ratio by +0.01 / +0.02 (tok), 0 (lad),
  +0.09 / +0.10 (st). The flat arm pays for tightening more than the partitioned arm does — on st's
  displaced entries the flat arm's node calls rise 53 % (119 → 182) and the partitioned arm's 14 %
  (63 → 72), because all of the extra sweeps are M2's and the flat loop repeats every model to give M2
  its sweeps. **The partitioned-over-reference ratio is the one that does not flatter the partition**:
  it rises as τ tightens.
- **The orchestrator's context expectation** (A96: partitioned census at 1e-12 on st ≈ 0.97 of V4's
  partitioned arm at write set 1e-6; V4's flat-to-partitioned 0.61 against 0.42 at census 1e-12). Here,
  on st: partitioned census 1e-12 over partitioned write set 1e-6 = **72 / 65 = 1.11** (displaced),
  **43 / 44 = 0.98** (stencil); flat census 1e-12 over flat write set 1e-6 = **182 / 119 = 1.53**
  (displaced), **63 / 73.5 = 0.86** (stencil); partitioned over flat **0.55 → 0.40** (displaced) and
  **0.60 → 0.68** (stencil). So on the displaced entries the measurements agree with the expectation (the
  tight census τ leaves the partitioned arm's cost within about 10 % of the loose whole-set test and
  raises the flat arm's by half); on the optimiser-like entries they do not (both arms cost about what
  they cost under the whole set at 1e-6, and the ratio moves the other way). The phase B supplementary
  numbers (Table 2) side with the displaced entries: flat ×1.39 (67.3 → 93.3) from 1e-8 to 1e-12,
  partitioned ×1.13 (34.2 → 38.8).

## 4. M1 — the stall, from the existing records

**Script** `optimiser_path_split.py` (`ea6ca92c` (first committed at `f7e344f1`)), no PROCESS run. It reads every phase B record of
the campaign (`BR`, `B0`, `B1`, `B2`, three configurations) and of the supplementary stage (`B0`,
`B2` on st at census 1e-12) through `records.read`; the optimiser's printed measure per iteration
(`stdout.log`, four significant digits), split into attempts by the record's per-attempt iteration
counts (checked: 25 of 25 per arm on tok and st, 24 of 25 on lad — lad seed 3 crashed mid-run); the
net electric power at every evaluation's entry (`entry_census_series.json`) as a one-number
fingerprint of the design point (**the records do not hold the design vector per iteration**, only
the final one; the fingerprint is read at the head of each iteration where the evaluation count maps
onto iterations exactly); the final design vector and objective (hex).

**Rules, declared in the script before the counts were printed.** *Near band*: measure below
`1000 × epsvmc`. *Hovering*: more than 10 iterations in the near band, over all attempts, the stopping
iteration of an accepted run excluded; population the accepted runs. *Path classes*, per start and
pair `a → b`, on attempt 1: `identical` (same printed measures, same length); `early` (the first
differing iteration has either measure at or above the near band); `stall` (split inside the near band,
`b` longer); `shorter` (split inside the near band, `b` not longer); `retried` (either arm used more
than one attempt; the attempt-1 class beside).

**Table 3 — hovering runs** (population: accepted runs, `ifail = 1`).

| configuration | BR | B0 (1e-8) | B1 | B2 (1e-8) | B0 (1e-12) | B2 (1e-12) |
|---|---|---|---|---|---|---|
| tok | 0 of 22 | 0 of 22 | 0 of 22 | 0 of 22 | | |
| lad | 2 of 12 | 2 of 12 | 2 of 12 | 2 of 12 | | |
| st | 7 of 24 | 7 of 24 | — | **15 of 20** | 7 of 24 | 8 of 24 |

Median iterations in the near band: st `BR` 4.5, `B0` 4.0, **`B2` 21.0**, `B0`@1e-12 4.5, `B2`@1e-12
4.5. **The orchestrator's rough count is reproduced exactly** (tok 0; lad 2 of 12 in every arm; st 7 of
24 in `BR` and `B0`, 15 of 20 in `B2`); the supplementary stage adds `B2` at 1e-12: 8 of 24, the
reference's rate.

**Table 4 — path classes** (of 25 starts; the partitioned arm against its path-matched comparator
first).

| configuration | pair | identical | early | stall | shorter | retried |
|---|---|---|---|---|---|---|
| st | B0 → B2 at 1e-8 | 0 | 6 | 8 | 3 | 8 |
| st | B0 → B2 at 1e-12 | 2 | 6 | 1 | 13 | 3 |
| st | BR → B0 at 1e-8 | 0 | 20 | 0 | 0 | 5 |
| st | B0 at 1e-12 → B0 at 1e-8 | 0 | 22 | 0 | 0 | 3 |
| st | B2 at 1e-12 → B2 at 1e-8 | 0 | 17 | 0 | 0 | 8 |
| tok | B1 → B2 | 25 | 0 | 0 | 0 | 0 |
| tok | BR → B0 | 11 | 5 | 0 | 9 | 0 |
| lad | B1 → B2 | 11 | 0 | 0 | 2 | 12 |
| lad | BR → B0 | 10 | 3 | 0 | 0 | 12 |

(tok's 25 identical include its three starts that crash at the first evaluation in every arm; lad's
12 retried include the 11 starts that end `ifail = 5` in every arm.)

**Table 5 — where the accepted runs end** (iteration variables within one finite-difference step,
1e-3 relative, of a bound the input file sets; mapping of the design vector to `ixc` checked by
requiring every value inside its bounds).

| st arm | accepted runs | runs ending at `dr_tf_nose_case`'s lower bound (0.01) | at `dr_cs`'s lower bound (0.03) |
|---|---|---|---|
| BR | 24 | 0 | 0 |
| B0 at 1e-8 | 24 | 0 | 0 |
| **B2 at 1e-8** | 20 | **10** | **6** |
| B0 at 1e-12 | 24 | 0 | 0 |
| B2 at 1e-12 | 24 | 0 | 0 |

(Every other near-bound variable — `hfact` upper, the two Greenwald fractions lower on st; `rmajor`,
`q95`, `dx_tf_turn_steel` on tok and lad — is shared by every arm of its configuration.)

**What M1 shows** (measured unless marked):

- **The stall is a walk along a flat direction, not a stall at a point.** On st's `stall`-class starts
  the partitioned arm's printed measure matches the flat arm's to four digits for 9–11 iterations and
  first differs when the measure reads 6e-10 to 8e-8 (seed 0: 7.86e-8 against 7.81e-8 at iteration 9, then 32 more
  iterations, 30 of them in the near band). But the design point **keeps moving** in those extra
  iterations: the fingerprint moves by 1.5e-2 to 6.9e-1 relative between the split and the end (one
  finite-difference column moves it by 2.4e-3), the final design vectors differ from the flat arm's by
  up to 96 % (`dr_tf_nose_case` 0.254 → 0.0100, `dr_cs` 0.193 → 0.0300, `dr_bore` 0.218 → 0.638 on
  seed 0), and the final objectives agree to 1.5e-11 relative. The optimiser walks along a direction in
  which the objective does not change — the inboard radial build (bore, central-solenoid thickness, TF
  nose case) — until a lower bound stops it (Table 5). At 1e-12 the same arm ends where the flat arm
  ends (design vectors within 1.6e-9 on seed 0).
- **st's path is sensitive at the fourth digit under every loop change**, not only the partition:
  `BR → B0` (20 early of 25), `B0` 1e-12 → 1e-8 (22 early), all splitting at iteration 2–15 with the
  measure between 5e-4 and 1e2. Those path changes leave the optimum (objective differences 1e-11 to
  1e-14 on non-retried starts) and the hovering count unchanged. Only `B2` at 1e-8 hovers more and ends
  elsewhere in the flat direction.
- **Retries** (the orchestrator's counts, confirmed): tok 0 of 88 finished runs; lad 48 of 92
  (12 per arm); st 15 of 75 (`BR` 5, `B0` 2, `B2` 8 of 25 each), plus `B0` 2 and `B2` 3 of 25 in the
  supplementary stage.

## 5. M2 — the evaluation error per loop at the same design point

### 5.1 Two evaluations deep, from the converged state (`evaluation_error_at_optimum.py`)

**Script** `evaluation_error_at_optimum.py` (press at `f7e344f1`; st's second point and part of tok's
and lad's runs were made after the next commit, `4d55d561`, which changed only scripts under
`st_stall_mechanism/` — the tables print both heads; tables at `ea6ca92c`). **Design points**: the
campaign flat arm `B0`'s accepted optimum (census 1e-8) — st seeds 0 and 8, tok seed 0, lad seed 0 —
entered through a **derived input file** (the committed file with each iteration variable's line set to
the optimum's exact value and `epsfcn` set to the step; written under this task's root, the committed
file untouched) and from the optimisation's own final coupling state (`y_before_finalise.json`). The
exact loop's base objective reproduces each optimisation's final `norm_objf` **to the bit** on all four
points (checked, printed). **Per loop**: the base point; each column's `+h` point entered from the
base's exit (the converged state with one variable displaced); its `−h` point entered from the `+h`
exit (the evaluator's order within a column). Steps 1e-3 and 1e-4 at st seed 0, 1e-3 elsewhere
(decision 2, §9). **Exact value**: the flat loop at census τ = 1e-14 (`A1` pinned on tok and lad,
`A0` for the reference arm's comparison); **its exactness is measured**: the partitioned loop at 1e-14
agrees with it to the bit at every point of every design point (the error columns of `A2 census 1e-14`
read 0 everywhere).

**Table 6 — st, `B0` seed 0's optimum; error against the exact loop** (absolute: the objective is
`norm_objf` ≈ −16.59; constraints are normalised; derivative error = non-common part / h, with respect
to the scaled variable; population: 14 columns × 2 signs; entries the largest over them).

| loop | base value error, f / c | h = 1e-3: f common / non-common / derivative error | h = 1e-3: c common / non-common / derivative error | h = 1e-4: f derivative / c derivative error | largest derivative error / epsvmc (1e-3) |
|---|---|---|---|---|---|
| AR (reference) | 0 / 0 | 3.5e-13 / 1.1e-12 / 1.1e-9 | 2.2e-10 / 2.9e-10 / **2.9e-7** | 1.1e-9 / 6.4e-6 | 290 |
| A0 census 1e-8 | 0 / 0 | 5.6e-9 / 1.7e-8 / **1.7e-5** | 8.1e-12 / 2.4e-11 / 2.4e-8 | 1.7e-5 / 2.9e-7 | 17 000 |
| A2 census 1e-8 | 0 / 0 | 5.6e-9 / 1.7e-8 / **1.7e-5** | 8.1e-12 / 2.4e-11 / 2.4e-8 | 1.7e-5 / 2.9e-7 | 17 000 |
| A0 = A2 census 1e-10 | 0 / 0 | 3.5e-13 / 1.1e-12 / 1.1e-9 | 1.1e-12 / 9.8e-13 / 9.8e-10 | 1.1e-9 / 1.0e-8 | 1.1 |
| A0 = A2 census 1e-12 | 0 / 0 | 3.5e-13 / 1.1e-12 / 1.1e-9 | 8.7e-13 / 8.7e-13 / 8.7e-10 | 1.1e-9 / 8.7e-9 | 1.1 |
| A0 = A2 write_set 1e-6 | 0 / 0 | 3.5e-13 / 1.1e-12 / 1.1e-9 | 2.2e-10 / 2.9e-10 / 2.9e-7 | 1.1e-9 / 3.0e-6 | 290 |
| A0 = A2 write_set 1e-8 | 0 / 0 | 0 / 0 / 0 | 2.6e-12 / 3.0e-12 / 3.0e-9 | 0 / 2.4e-8 | 3 |
| A0 = A2 census 1e-14 | 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 | 0 |

st seed 8's optimum reads the same to two digits in every cell (AR 260, census 1e-8 17 000,
census 1e-10 and 1e-12 1.1, write set 1e-6 260 and 1e-8 2.9). **tok** (seed 0): **every loop's value
at every point is the exact value to the bit** — the reference, both test sets at every τ, flat and
partitioned (every cell 0). **lad** (seed 0): every loop exact except census 1e-8, flat and partitioned
alike: constraint derivative error 2.2e-7 = 22 × epsvmc, objective exact.

**What 5.1 shows** (measured):

1. **From a converged entry the flat and the partitioned loop return bit-identical values** — every
   point, every τ, both test sets, all four design points, three configurations. The partitioned
   arrangement does not leave more error than the flat one in one evaluation from a converged state.
2. **The kind of error differs by loop.** The reference loop's error is in the **constraints**
   (derivative error 2.9e-7, 290 × epsvmc; it grows ×22 when the step shrinks ×10, so it is
   non-common error of fixed size, 2.9e-10, divided by the step); census 1e-8's is in the
   **objective** (1.7e-5, 17 000 × epsvmc, the same at both steps — so it is not noise of fixed size:
   it scales with the step, a bias that the + and − points do not share). Neither loop's
   derivative error is below epsvmc, yet `BR` and `B0` at 1e-8 hover no more than the exact loops do
   (Table 3).
3. **Where the loops are exact, nothing hovers**: tok (exact everywhere, 0 hovering), lad (exact
   except one constraint's derivative at 1e-8; the same 2 of 12 hover in every arm).

### 5.2 The block loops along the optimiser's own path (`stencil_chain_error.py --trace-press`)

`B0` and `B2` on st, seed 0, census 1e-8 and 1e-12, re-made with the driver's block trace on. **Each
reproduces its campaign or supplementary record** — iterations per attempt, evaluations per attempt,
`norm_objf` to the bit (4 of 4) — so the trace describes the runs Table 3 counts.

**Table 7 — gradient evaluations in which a block loop stopped after its first sweep with a first-sweep
change that was not zero** (the block accepted the state it was entered with, and the change it found —
below τ — is left in the state; population: every gradient evaluation of the run).

| arm, τ | iterations | gradient evaluations | loops stopped after one sweep, any change | of those, with a nonzero change carried: M2 (largest) | M3 (largest) |
|---|---|---|---|---|---|
| B0 (flat), 1e-8 | 10 | 532 | FLAT 19 | none (all 19 read exactly 0) | — |
| **B2, 1e-8** | 40 | 2 212 | M1 711, M2 1 027, M3 145 | **639 = 29 % (3.3e-10)** | 66 = 3 % (7.4e-9) |
| B0 (flat), 1e-12 | 10 | 532 | FLAT 19 | none | — |
| B2, 1e-12 | 10 | 532 | M1 171, M2 247, M3 19 | 74 = 14 % (3.9e-14) | none |

At 1e-8 the partitioned arm's M2 carries a nonzero change in 16 of each iteration's 56 gradient
evaluations (two problem calls per iteration: the head and the line search), from the first iteration
to the last, changes of 5e-11 to 3.3e-10; at 1e-12 in 7–10 of 56, changes below 4e-14. The flat loop
stops after one sweep only when the sweep changed nothing at all (19 of 532, change exactly 0): the
column the optimiser moved disturbs M1's couplings, the flat loop takes a second sweep, and M2's
couplings are swept again in passing.


### 5.3 Along the optimiser's own evaluation chain (`stencil_chain_error.py --press`)

5.1 enters each stencil point at most two evaluations away from a converged state. VMCON's evaluator
does not: one problem call is the base point, then `+h`, `−h` of column 0, of column 1, …, then the
reconcile call, **each entered from the previous evaluation's exit**. §5.3 runs exactly that sequence
(30 evaluations at st's n = 14, step 1e-3) under all 13 loops, from two starts: **`B0` seed 0's
optimum** entered from `B0`'s own final state, and **`B2` seed 0's end point** (after its 40
iterations, 30 in the near band) entered from **`B2`'s own final state**. 780 runs, all `ok`, made at
`4d55d561`; tables at `ea6ca92c`. The exact loop's chain and the partitioned 1e-14 chain agree **to the
bit at all 30 points** at both starts (exactness, measured).

**Table 8 — st, the chain; errors against the exact loop's chain** (step 1e-3; largest over the 30
points or 14 columns; the second figure of each pair is the `B2` end-point chain).

| loop | objective: derivative error (B0 start; B2 start) | constraints: derivative error | largest / epsvmc |
|---|---|---|---|
| AR | 7.1e-10; 7.1e-10 | 3.7e-7; 2.9e-7 | 370; 290 |
| A0 = A2 in size, census 1e-8 | 1.7e-5; 1.7e-5 | 2.4e-8; 4.0e-8 | 17 000; 17 000 |
| A0 = A2, census 1e-10 | 7.1e-10; 7.1e-10 | 9.8e-10; 8.5e-10 | 0.98; 0.85 |
| A0 = A2, census 1e-12 | 7.1e-10; 7.1e-10 | 8.7e-10; 1.3e-9 | 0.87; 1.3 |
| A0 = A2, write set 1e-6 | 7.1e-10; 7.1e-10 | 3.7e-7; 5.5e-7 | 370; 550 |
| A0 = A2, write set 1e-8 | 0; 0 | 3.0e-9; 1.4e-9 | 3; 1.4 |

**Table 9 — the partition's own contribution: the partitioned chain against the flat chain at the same
setting** (points whose objective and constraints are bit-identical; largest derivative difference,
objective / constraints; B0 start; B2 start).

| setting | bit-identical points (of 30) | derivative difference, objective | derivative difference, constraints |
|---|---|---|---|
| census 1e-8 | 21; 20 | **5.6e-6; 5.6e-6** | 6.6e-10; 3.9e-10 |
| census 1e-10 | 25; 24 | 0; 0 | 5.5e-10; 1.2e-11 |
| census 1e-12 | 29; 29 | 0; 0 | 2.8e-13; 1.7e-13 |
| write set 1e-6 | 23; 23 | 0; 0 | 8.0e-9; 9.4e-9 |
| write set 1e-8 | 26; 25 | 0; 0 | 5.5e-10; 1.2e-11 |

**Table 10 — where census 1e-8's objective derivative error sits** (per column, `B0` start; the `B2`
start reads the same column by column; derivative error against the exact chain, and the sweeps at the
`+h` / `−h` points).

| column | flat error | flat sweeps | partitioned error | partitioned M2 sweeps |
|---|---|---|---|---|
| 0 `temp_plasma_electron_vol_avg_kev` | 0 | 3 / 3 | 0 | 1 / 1 |
| 1 `beta_total_vol_avg` | 0 | 3 / 2 | 0 | 2 / 2 |
| 2 `nd_plasma_electrons_vol_avg` | −1.7e-5 | 2 / 2 | −1.7e-5 | 2 / 1 |
| 3 `hfact` | −5.6e-6 | 2 / 1 | −5.6e-6 | 1 / 1 |
| 4 `dr_cs` | 0 | 5 / 5 | 0 | 5 / 5 |
| 5 `q95` | −1.1e-5 | 5 / 2 | −1.7e-5 | 5 / 2 |
| **6 `dr_bore`** | **0** | 5 / 5 | **−5.6e-6** | 5 / 5 |
| 7 `dr_tf_nose_case` | 0 | 5 / 5 | 0 | 5 / 5 |
| 8 `dr_shld_inboard` | 0 | 5 / 2 | 0 | 5 / 1 |
| 9–11 | 0 | | 0 | |
| 12 `f_nd_plasma_pedestal_greenwald` | 1.1e-5 | 5 / 2 | 1.7e-5 | 5 / 1 |
| 13 `f_nd_plasma_separatrix_greenwald` | 5.6e-6 | 2 / 2 | 5.6e-6 | 1 / 1 |

Also measured along the chain: the same design point evaluated first (the base) and last (the
reconcile call, after 28 stencil evaluations) differs by 7.1e-13 in the objective in every loop but
the two exact-at-the-optimum ones (write set 1e-8, census 1e-14), flat and partitioned alike — history
at one point is negligible. The partitioned loop's M2 accepts its entry after one sweep with a nonzero
change at 9 of 30 chain points at 1e-8 (largest 9.2e-11), M3 at 2–3 (7.4e-9); but the columns on which
the partitioned objective derivative differs from the flat one (5, 6, 12 in Table 10) are columns where
M2 iterated five sweeps at the `+h` point, not columns where it stopped after one.

**What 5.2 and 5.3 show** (measured unless marked):

1. **At census 1e-8 the objective's finite-difference derivative on st is wrong in quanta of 5.6e-6**
   — the objective jumps by 1.1e-8 between the `+h` and `−h` points — on 5 or 6 of 14 columns, in the
   flat and the partitioned loop alike, largest 1.7e-5 (17 000 × epsvmc). The jumps sit on columns
   where the loop stopped after a different number of sweeps, or on a different last sweep, at the two
   points: a truncation that changes discretely from point to point. At 1e-10 the quantum is 7.1e-10
   (the objective's jumps are 1.4e-12), below epsvmc.
2. **The partitioned loop puts one of those quanta on `dr_bore`, the flat loop does not** — at both
   chain starts (Table 10). `dr_bore` is one of the three inboard radial-build variables along which
   the partitioned arm walks at 1e-8 (§4: `dr_bore` 0.218 → 0.638 on seed 0, the objective unchanged to
   1.5e-11). The sign agrees: the spurious derivative is negative, the optimiser (minimising the
   normalised objective) increases `dr_bore`. The flat loop's quanta fall on the plasma variables
   (density, `q95`, the Greenwald fractions, `hfact`).
3. **The reference loop's error is in the constraints, not the objective**: constraint derivative error
   290–370 × epsvmc, objective derivative error 0.7 × epsvmc — and its optimisations hover no more
   than the exact loops'.


## 6. M4 — the condition

**Script** `tolerance_condition.py` (tables at `ea6ca92c`), no PROCESS run; reads M0's and M2's records.
**The declared condition** (written into M2's docstring before any number was read): a loop at a
tolerance is sufficient when its optimiser-relevant error at the optimum — the larger of the
base-point value error and the finite-difference derivative error, objective and every constraint,
worst over the design points — lies below the configuration's `epsvmc`; loosest on M2's grid (census
1e-8, 1e-10, 1e-12; write set 1e-6, 1e-8). **Its declared test**: it must put `BR`, `B0` at 1e-8 and
`B2` at 1e-12 (no excess hovering, Table 3) on one side and `B2` at 1e-8 (hovering) on the other.

**Result: the declared condition fails its test** (measured). On st it rates `BR` at 290 × epsvmc and
`B0` at 1e-8 at 17 000 × — both "insufficient" — and neither hovers more than the exact loops; it cannot
separate `B0` from `B2` at 1e-8 (the same 17 000 ×). The size of the evaluation error, measured the way
the condition measures it, does not predict the stall.

**Table 11 — the declared condition, and the cost there** (node calls per evaluation over `AR`'s, from
M0: stencil entries; displaced entries).

| configuration | epsvmc | test set | loosest sufficient τ, flat and partitioned | flat / AR there | partitioned / AR there |
|---|---|---|---|---|---|
| tok | 1e-7 | census | 1e-8 (every loop exact at the optimum, the reference too) | 1.14; 1.13 | 0.60; 0.49 |
| tok | | write set | 1e-6 | 1.00; 1.00 | 0.74; 0.60 |
| lad | 1e-8 | census | 1e-10 (1e-8 reads 22 × on a constraint derivative, flat and partitioned alike) | 0.83; 1.00 | 0.52; 0.47 |
| lad | | write set | 1e-6 | 1.00; 1.00 | 0.73; 0.60 |
| st | 1e-9 | census | none on the grid (1e-10 and 1e-12 read 1.1 × at h = 1e-3, 9–10 × at h = 1e-4) | — | — |
| st | | write set | none on the grid (1e-8 reads 3 ×) | — | — |

(tok's and lad's flat arm here is `A1`, the partitioned arm's pairing; tok's `A0/AR` equals `A1/AR` on
the census set.)

**A post hoc criterion, labelled as such** (added after the declared one failed; not a result to rule
on without that label): the partition's own, history-dependent contribution — Table 9's largest
difference between the partitioned and the flat derivatives along the optimiser's evaluation chain —
over epsvmc: **census 1e-8: 5 600 × (both chain starts); 1e-10: 0.55 × and 0.012 ×; 1e-12: 3e-4 ×;
write set 1e-6: 8 × and 9.4 ×; write set 1e-8: 0.55 × and 0.012 ×.** It separates what M1 measured:
above 1 at census 1e-8 (hovering, 15 of 20), far below 1 at 1e-12 (8 of 24, the reference's rate).
On st it names **census 1e-10** and **write set 1e-8** as the loosest sufficient settings on the grid;
the partitioned arm's cost there, over `AR`, is **0.49; 0.69** (census 1e-10) and **0.60; 0.82**
(write set 1e-8); the flat arm's **0.71; 1.57** and **1.00; 1.43**. Its prediction for write set 1e-6
(8–9 ×, i.e. V4's criterion) is untested: V4's st records were not read (§8). Whether the path returns
at census 1e-10 in V5 is untested too; A96 measured 3 of 5 seeds returning at 1e-10 on the V4 copy.

**Does one rule fit the three configurations?** The rule "τ = epsvmc × epsfcn" (1e-10, 1e-11, 1e-12)
lies **at or below** the loosest sufficient τ found on every configuration (tok 1e-8, lad 1e-10, st 1e-10
post hoc) — sufficient everywhere on this evidence, and one to two decades tighter than needed on tok
and lad and on st's post hoc reading (measured, on M2's grid). Its cost is in Table 1. A rule "loop
exact at the optimum" is what tok and lad satisfy by nature (their loops reach the exact value); st's
does not at any τ above 1e-14 (Tables 6, 8).

**Matched delivered accuracy, census against write set** (the orchestrator's addition; on the loosest
sufficient settings above; stencil; displaced): tok — partitioned census 1e-8 0.60; 0.49 against write
set 1e-6 0.74; 0.60, flat 1.14; 1.13 against 1.00; 1.00. lad — partitioned census 1e-10 0.52; 0.47
against write set 1e-6 0.73; 0.60, flat 0.83; 1.00 against 1.00; 1.00. st (post hoc) — partitioned
census 1e-10 0.49; 0.69 against write set 1e-8 0.60; 0.82, flat 0.71; 1.57 against 1.00; 1.43. On
every configuration the census set is the cheaper criterion for the partitioned arm at matched
delivered accuracy (by 0.11–0.21 of `AR`'s node calls per evaluation); for the flat arm it is cheaper on
the stencil entries of lad and st, equal on lad's displaced entries, and dearer on tok's entries and on
st's displaced entries.

## 7. The hypotheses: what would have refuted each, and whether it was found

| | hypothesis | what would refute it | found? |
|---|---|---|---|
| H1 | at 1e-8 the partitioned arm follows the flat arm's path to the optimum, then stalls above epsvmc | the path differing before the measure is small; the extra iterations moving the design point materially | **Both found, in part.** 6 of 25 st starts split at measures 1e-5 to 0.46 (`early`; 8 more `retried`); but st's paths split at that level under *every* loop change, including `BR → B0` (20 early) and 1e-12 → 1e-8 on the flat arm (22 early), without hovering or a changed optimum. And on the `stall`-class starts the design point **moves materially** after the split (fingerprint 1.5e-2–6.9e-1, iteration variables up to 96 %, 10 of 20 runs to `dr_tf_nose_case`'s bound) while the objective stays within 1.5e-11. **Reformulated (measured):** not a stall at the optimum but a walk along a direction in which st's objective is flat. |
| H2 | the stall is evaluation error too large for the optimiser's tolerance | the partitioned loop's error not exceeding the flat loop's; the gradient error below epsvmc; the reference's gradient error as large while it does not stall | **Found.** From converged entries the flat and partitioned loops return bit-identical values (all 4 design points, 3 configurations); along the evaluator's chain their largest errors are equal (1.7e-5 objective derivative, 17 000 × epsvmc) and the flat arm does not hover; the reference's constraint derivative error is 290–550 × epsvmc and it does not hover. Error *size* does not explain the stall. |
| H3 | the flat loop leaves less error at the same τ because it over-solves; each block hands an error near τ downstream | the partitioned loop's error not exceeding the flat loop's | **Found** (same evidence). What is true (measured): the flat loop does sweep every block until the whole set passes, and the partitioned M2 does accept its entry after one sweep in 29 % of the stalled run's gradient evaluations (changes ≤ 3.3e-10) — but the objective differences between the arms sit on points where M2 iterated to τ, not where it accepted its entry. |
| H4 | st because its loops contract more slowly, or because its epsvmc is tighter, or both | tok or lad showing the same error at the optimum; the error quantum lying below tok's epsvmc | **Not found; refined.** At their optimum tok's loops are **exact** at every τ and both test sets, the reference too; lad's exact except one constraint derivative at census 1e-8 (22 ×), in both arms, and lad's arms take the same path. st's loops are exact at no τ above 1e-14; st's M2 contracts by 0.034 per sweep (M0). The quantum at 1e-8 (5.6e-6) exceeds every configuration's epsvmc, tok's included, so the tighter epsvmc is not what separates st: whether the loop's value at τ is exact is. |
| — | the orchestrator's counter-observation: the reference loop is far looser and converges as well | (to be tested, not explained away) | **Confirmed and located**: the reference's error is in the constraints (290–370 × epsvmc on the derivative), its objective derivative error 0.7 ×; census 1e-8's is in the objective. And within census 1e-8, the flat and partitioned errors have the same size but different columns (Table 10). What matters on this evidence is **which function and which direction** carries the error, not its size — the direction part is conjecture (§0). |

## 8. Limits, and the deferred measurement

- **M3 deferred** (orchestrator, mid-task): nothing here reads model code or explains *why* st's M2
  contracts at 0.034 per sweep, why its loops never reach a bit-identical fixed point, or what jumps the
  objective by 1.1e-8 quanta at census 1e-8. A later task would still need: the per-coupling residual
  per sweep inside M2 and the flat loop on st (the block trace has the per-module maximum only), the
  coupling that settles last, and the models that write and read it. M0's per-sweep tables (in the M0
  script's output) are what exists.
- **The link between the `dr_bore` derivative error and the walk is conjecture.** It rests on two
  design points and one chain each; no run forced or removed that error. Establishing it would take an
  intervention (e.g. the partitioned arm at 1e-8 with the objective evaluated by the exact loop), which
  is a driver-level change and was not made.
- **Few entries.** M0: 3 displaced and 2 stencil entries per configuration (the stencil entries at the
  input file's design point, not at an optimum). M2: two st optima, one tok, one lad; the 1e-4 step at
  st seed 0 only; the chain on st only, at step 1e-3 only. Ratios in Table 1 are means over 2–3
  entries; Table 2's phase B ratios are the campaign's 12–22-seed populations.
- **The post hoc criterion is post hoc** and rests on st alone. Its write-set-1e-6 prediction (V4's
  criterion, 8–9 × epsvmc) was not checked against V4's st records, and no V5 phase B run was made at
  census 1e-10.
- **The records do not hold the design point per iteration**; M1's "moved materially" uses the net
  electric power at each evaluation's entry as a fingerprint, and the final design vectors.
- **Records straddle commits.** M2's first press ran across `f7e344f1` and `4d55d561`, and every press
  ran with this task's own scripts or report uncommitted in the tree (`tree_git_dirty`; the stamped
  paths are all under `arch_surgery/st_stall_mechanism/` or the report — never the harness, the V5
  `PROCESS/` or `process/models/`). 3 437 records: 415 at `de76476f`, 825 at `f7e344f1`, 2 197 at
  `4d55d561`; all run kind `smoke`, all `ok`.

## 9. Decisions taken alone, with reversals

1. **Kept and revised the stopped agent's M1 script** (`optimiser_path_split.py`): thresholds made
   relative to each run's `epsvmc` (its fixed 1e-5 / 1e-7 replaced by the near band), the hovering rule,
   bound proximity, retries and per-evaluation node calls added. Reversal: its first form is in no
   commit (it was never committed); the classes it printed differ only in the `early`/`stall` boundary.
2. **Step 1e-4 only at st seed 0** in M2 (run budget: each step is 2n evaluations per loop). Reversal:
   add the step to `DESIGN_POINTS` and press.
3. **The design point enters through a derived input file** (the committed file with the optimum's
   iteration-variable values and `epsfcn`), not a harness addition; the job identity does not carry the
   input file, so every M2 run has its own named directory. Checked: the exact loop's base objective
   reproduces each optimisation's `norm_objf` to the bit. Reversal: a `--design-point` option in the
   evaluation child, in its own commit.
4. **"Exact" is the flat loop at census 1e-14**, checked against the partitioned loop at 1e-14 (bit-
   identical at every point). Reversal: another tight loop via `EXACT`.
5. **M2's second part (the chain, the traced optimisations) was added** after 5.1 found the arms'
   values identical — 784 runs the brief did not list. Reversal: drop §5.2–5.3; M4's declared result
   stands without them.
6. **Scripts were committed while presses ran** (to keep the tables' scripts ahead of the numbers),
   so M2's first press straddles two commits differing only in task scripts. Reversal: re-press at one
   commit (`--press` resumes nothing across commits only if the directories are removed first).
7. **"Comparable" = within 10 % in node calls per evaluation** (declared in M0's docstring). Reversal:
   the ratios are printed; any other threshold reads off Table 1.
8. **M4's post hoc criterion** is printed beside the declared one, labelled. Reversal: delete the block
   in `tolerance_condition.py`.
9. **Run kind `smoke`** for every run (the brief allowed `gate` or `smoke`).

## 10. Records

Before hand-back the whole V5 `runs/` directory of this worktree (the seeded campaign, supplementary,
gate and timing records, untouched, and this task's `runs/st_stall_mechanism/` and press logs
`runs/_press_logs/A104_press01…07_*.log`) was moved by `mv` to
`arch_surgery/idf_probe/runs/st_stall_mechanism/` (counted before and after: 4 605 `metrics.json` and 62 777 files, both sides). This
task's records are therefore at `arch_surgery/idf_probe/runs/st_stall_mechanism/st_stall_mechanism/`
(`loop_sweeps_ladder/`, `evaluation_error/` with `chain/`, `traced_optimisations/`, and `tables/` — the
printed tables of every script at `ea6ca92c`).

## 11. Change log

- **2026-09-30** — report written (this agent took over from one stopped with an uncommitted M1 script).
  Commits: `de76476f` (M0 and helper), `f7e344f1` (M1, M2, M4), `4d55d561` (M2 second part),
  `f71fe50b` and `ea6ca92c` (tables). Mid-task instructions from the orchestrator applied: M3 deferred;
  the whole write set added to M0 (τ = 1e-6, 1e-8, 1e-10), M2 (1e-6, 1e-8) and M4.
- **2026-09-30** — the V5 `runs/` moved to `arch_surgery/idf_probe/runs/st_stall_mechanism/` by `mv` on the same filesystem: 4 605 `metrics.json` / 62 777 files before, the same after; `MDA_partitioning_experiment_v5/runs/` no longer exists in the worktree. The scripts' default roots (`loop_runs.ROOT`, `optimiser_path_split.py --runs`) still name the V5 `runs/`; re-reading the tables needs `--runs` / the root pointed at the moved tree.




---

## 12. Orchestrator's critical assessment (protocol §5) — verdict: merge

*Written 2026-09-30 by the orchestrating session under the user's autonomous grant of that day. Checked
differently from the agent. The report's conclusions are inputs to the open question OQ-tolerance, which
is the user's.*

**Checked.** (1) `git diff --name-only 44bc70f3..52096125`: six scripts under
`arch_surgery/st_stall_mechanism/` and this report — **nothing under the V5 folder, the driver copy or
`process/models/`**; worktree clean; `merge-tree`: no conflict; the scripts compile. (2) Records: 3 437 new
`smoke` records under the task's own root; the 553 campaign records present and untouched. (3) **The
report's central new claim, recounted by the orchestrator from the campaign's output files, not from the
agent's scripts**: on st at census 1e-8 the partitioned arm ends at different designs with the same
objective. Seed 0: `B0` ends at `dr_bore` 0.218, `dr_cs` 0.193, `dr_tf_nose_case` 0.254; `B2` at 1e-8 at
0.638, 0.030 (its lower bound) and 0.0100 (its lower bound); `B2` at 1e-12 at `B0`'s values to nine digits.
Over the accepted runs: `dr_tf_nose_case` within 1 % of its lower bound in **10 of 20** `B2` runs at 1e-8
and in **0** of `BR`'s 24, `B0`'s 24, and of both arms' 24 at 1e-12; `dr_cs` at its lower bound in 6 of 20
and 0 elsewhere; the bore's median 0.537 in `B2` at 1e-8 against 0.20 in every other arm and setting. So
the agent's reformulation of H1 stands on the campaign's own records: **a walk along a direction in which
st's objective is flat, to the variables' bounds — not a stall at the optimum.** (4) The hovering counts are
the orchestrator's own of earlier in the day (tok 0; lad 2 of 12 in every arm; st 7 of 24, 7 of 24 and
15 of 20), reproduced by the committed script. (5) Table 2's node calls per evaluation are the
orchestrator's figures to the last digit but one.

**What the orchestrator had wrong, and the report corrects.** H2 and H3 as the orchestrator put them to
the user — the partitioned loop leaves more error because the flat loop over-solves, and the optimiser
stalls when that error exceeds its tolerance — are **refuted**: from a converged state the two loops return
bit-identical values, and along the optimiser's evaluation chain their errors are of equal size; the flat
arm and the reference carry errors far above `epsvmc` and do not wander. The rule "τ = `epsvmc` × `epsfcn`"
was built on that reasoning; it is sufficient on the evidence but its derivation is not what the
measurements support. What is measured: at census 1e-8 on st the objective's finite-difference derivative
carries discrete jumps (the loop stopping after different sweep counts at the two points of a difference)
in both arms, the partitioned arm's fall on the bore — one of the three variables of the flat direction —
and at 1e-10 the jumps are below `epsvmc`. That this is what drives the walk is conjecture, and the report
says so.

**Limits the orchestrator adds.** The post hoc criterion is post hoc and rests on two design points of one
configuration; "census 1e-10 suffices on st" is a prediction, not a measurement — no V5 optimisation was
run at 1e-10 (A96, on V4's copy, found the path returning on 3 of 5 seeds at 1e-10 and seed 1 changing
basin there). M0's ratios are means over two or three entries. M3 is deferred.

**Queue consequences at merge.** A104 merged; OQ-tolerance gains its findings; the orchestrator runs, as a
labelled exploratory stage and not as a campaign, st's phase B at census 1e-10 (`B0`, `B2`, the 25 starts)
so that the prediction is a measurement when the user decides.
