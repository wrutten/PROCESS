# A115 (v5-sweep-residual-trace) — what the block loops leave moving when they stop

> **Document status** — **MERGED 2026-10-02 at `a27395be` (`--no-ff`; the orchestrator's assessment at the end, §10); archived.** The one V5 records tree (four campaign run IDs, each now with a `traced_runs/` folder) was moved on with A116 and then A117 and is at `arch_surgery/idf_probe/runs/A117_runs/`; the paths below that begin `runs/` are read from there. Was: **OPEN** (task report, awaiting the orchestrator's assessment). Task A115
> (v5-sweep-residual-trace), 2026-10-02, branch `A115-v5-sweep-residual-trace`, worktree
> `.claude/worktrees/A115-v5-sweep-residual-trace`, base `3211f50e`. Start time recorded
> `2026-10-02T16:11:03+02:00`. Records under `arch_surgery/MDA_partitioning_experiment_v5/runs/<run ID>/traced_runs/`
> (untracked, about 150–190 MB per run ID).

**Commits.** `24cb476c` driver change DR13, the traced-run stage, GC's declaration · `8e94a3a7`
the reading script with the **declaration** (before any trace was read) · `d1e94dc8` statistics
L1–L3 added after the first trace was read, labelled · `5bfdb466` `paper_tables.md` re-rendered.
**Every traced record, the neutrality checks and every gate verdict below were made at `d1e94dc8`**
(clean tree; the 6 test records made at `24cb476c` / `8e94a3a7` were re-made by the full press,
which ran without `--resume`). **Every number in §§3–6 is printed by
`stopping_sweep_residuals.py` at `5bfdb466`** (output kept at
`runs/census_tau1e-08/traced_runs/stopping_sweep_residuals_tables.md`; byte-identical below the
title line to its run at `d1e94dc8`). Neutrality numbers: `experiment_runner.py --traced-runs check`
at `d1e94dc8`. "Measured" = read from records or traces; "inferred" = reasoned to.

## 0. In plain language

- **The conjecture's mechanism is present everywhere, and it does not separate the disturbed cases
  from the undisturbed ones.** Under the census set, at most block stops other written variables
  are still moving by τ or more, and they are read later — by a later block or by the objective and
  constraints (measured, §4). But the same holds on tok, whose optimiser is never disturbed, and the
  declared rate does not separate st's disturbed arms from its undisturbed one (measured, §5). By the
  declaration: **present but not shown to be the cause** — not refuted, not supported.
- **Most of that movement is a one-sweep lag, not unconvergence.** A variable that is not read before
  it is written is computed from the census values the *previous* sweep left; its change at the stop
  is the census change of the sweep before (inferred from the definition, measured below). Where the
  census change at the stop is exactly 0, the next sweep reproduces the whole write set **bit for bit
  in every case observed** (measured, L2: e.g. st `B2` `M3`, write set 1e-8, 5 630 of 5 630). So the
  large out-of-test changes at a stop mostly say the *previous* value was stale, not that the current
  one is (inferred).
- **This is why the two stop tests differ** (measured): under the whole write set a block runs one
  more sweep after its census part has closed — on tok/lad/st `M1` and `M3` and the flat loops, in
  30–96 % of gradient evaluations — and when that census part had changed by exactly 0, the extra
  sweep changes nothing at all. Where the census change at the stop is not 0 (st's coils block `M2`,
  every stop of it; st's flat loop), the out-of-test values carry a real residual of the census set's
  own size (≈ τ), and the lag model's estimate of their next change is at or above τ in 0–3.3 % of them
  (inferred, L3). The difference between the tests on st is therefore *where τ truncates the census
  set*, not out-of-test components left far from convergence (inferred).

## 1. What changed in the driver copy (DR13) and how it was shown neutral

**The change (trace path only).** `PROCESS/process/core/solver/module_solve.py` and `caller.py`
(`PROCESS/CHANGES.md` §§4.2.11, 4.5.19; `copy_gates.PERMITTED_EDIT_FILES`, `PROVENANCE.json`
regenerated with `--task`; `PROCESS_diff.py` annotations): with `PROCESS_ARCH_BLOCK_TRACE` set, every
block-loop sweep is also scored on two parts of the block's write set — `census` (the block's census
test set) and `non_census` (the rest; the flat block's write set is the whole coupling state) — each
with its maximum, worst component, the names at or above τ (≤ 40) and any discrete/constant/NaN
flag; the test's own worst component is named; the evaluation's line carries `objf_hex` and
`conf_hex`. Under the whole write set the census sets come from a new trace-only variable
`PROCESS_ARCH_BLOCK_TRACE_CENSUS_SETS` (refused without the trace and under the census set; loaded by
`load_test_sets` with its checks). **The parts are scored from the two snapshots the loop already
read** (`y_prev`, `y`, before `y_prev = y`) with the predicate's untimed `spec.residual`: no state is
read the loop does not read, no counter or timer is touched. No stop needed (the brief's condition did
not arise). Nothing under `process/models/` changed (G0′ PASS).

**Neutral with the switch unset — G1 (`switch_neutrality`), `3211f50e → d1e94dc8`: FAIL, and the
failure is not the driver's.** Before capture taken at `3211f50e` (clean, before any edit; the
previous captures archived by `mv` under `switch_neutrality/straddles/9ed0da4c__d08e8ab4/` with the
old `gate.json` as `gate_at_c412bbdb.json`). 6 pairs; 4 614 record values compared, **3 differing**,
all `audit_snapshot.wall_s` on the three `BR` runs (e.g. 0.0352 → 0.0335 s); **0 of 51 319
output-file lines** differ; 9/9 teeth. `audit_snapshot` is in G1's *conditional* table (added by
A57) and was excluded at every earlier straddle because the before side lacked it; this is the first
straddle where both sides carry it, and its `wall_s` leaf is a wall clock that `ALWAYS_EXCLUDED` does
not name (the same class as trap T20's first-cross-tree leaves). Not fixed (a failed gate is a result).
The obvious fix — `audit_snapshot.wall_s` into `ALWAYS_EXCLUDED` beside
`evaluation_warmup.*.wall_s` — is the orchestrator's to decide (inferred: it would PASS with 0 of
4 611).

**Neutral with the switch set — GC (`count_neutrality`), straddle `DR12 → DR13`: PASS.** Declared
in `gate_count_neutrality.py`: `STRADDLE = ("DR12", "DR13")`, the DR13 side under the whole write set
with the timers on (as DR12's) and **the block trace on every block-loop arm with the census split**
(`STRADDLE_BLOCK_TRACE`), count and prime rules `identical`. 22 pairs (11 evaluations + 11
optimisations; 16 of them traced); **3 989 count leaves, 0 differing; 33 prime checks, 0 failing;
46 125 coupling-state components, 0 differing**; 4/4 teeth. Record
`runs/census_tau1e-08/gates/count_neutrality/straddles/DR12__DR13.json`.

**Neutral with the switch set — the traced runs themselves (§2): 216 of 216 equal to their campaign
records.**

**Other gates pressed** under `census_tau1e-08`, all `--resume`, all at `d1e94dc8`, teeth all
tripped: `g0prime` PASS (77 files, 4/4), `copy_identity` PASS (224 files, 8 permitted, 12/12),
`edit_behaviour` PASS (1/1), `self_containment` PASS, `composition` PASS (24 pairs), `rungs` PASS,
`run_path` PASS, `resume_identity` PASS (1 264 records read by arm name, 15/15), `capability` PASS
(the new switch read back), `run_kind_separation` PASS (1 292 records; by kind campaign 553, gate
475, smoke 50, supplementary 50, timing 110, **trace 54**; 7/7). Selfcheck PASS (before commit).
Not pressed: the other gates and the other three run IDs' gate tables (A116's).

## 2. The traced-run stage, the job set, the neutrality check

**Stage** `harness/traced_runs.py`, `experiment_runner.py --traced-runs list | press | check`
(`--traced-job-set`, `--configuration`, `--arm`). A traced job is the campaign job composed by the
chain's own constructors under the run ID's settings and the campaign press's composition (timers
on), with `run_kind = "trace"` (new in `records.RUN_KINDS`), its own named `outdir` under
`runs/<run ID>/traced_runs/<job set>/`, and `override_env` carrying the trace file (relative) and,
under the write set, the census artifact. The press refuses unless every traced job's digest differs
from its campaign job's and it resolves to its own folder (`assert_apart`); one compressed trace per
run (`block_trace.jsonl.gz`, written and round-trip-verified with `process_log`'s writer). Reference
arms are not traced (the driver refuses the trace without a block loop).

**Job set and rule** (declared in `traced_runs.JOB_SETS` before any trace was read): every loop arm
(phase A `A0`, `A1`, `A2`; phase B `B0`, `B1`, `B2`; `A1`/`B1` not on st), under each of the four
settings; phase A displaced seeds 1, 2, 3; phase B the three lowest starts accepted by every arm (the
reference included) in all four campaigns — tok 0, 1, 2; lad 0, 1, 5; st 0, 2, 4 (re-derived from the
records by the reading script: agrees on all three, measured). **st's condition triggered the declared
fallback**: B2 at census 1e-8 ends 0.961, 0.939, 0.946 relative from B0's design on seeds 0, 2, 4 —
all above 10 % (measured) — so the lowest ≤ 10 % start, seed 6 (0.0083), had to be added; it is in the
second declared set `sweep_residual_st_more` (st phase B seeds 6, 7, 8: 0.0083, 0.119, 0.959), which I
pressed in full under all four settings. **Ran: 4 run IDs × (48 + 6) = 216 traced runs**, all `ok`.

**Neutrality check** (`--traced-runs check`; `traced_runs/<job set>/neutrality.json` per run ID):
declared count leaves (iterations, evaluations and the sweep histogram, node calls, dispatch sweeps,
block-loop totals, predicate counts, prime count, attempts, `ifail`, `mfile.ifail`, the first
evaluation, `exact` — objective, constraints, design as hex), the coupling-state files component by
component, the campaign record's digest equal to the composed job's, the stamped identities differing
in `run_kind` and `override_env` only, and the trace's lines and per-block sweeps against the record.

| run ID | traced runs | equal | count leaves compared / differing | state components compared / differing | trace consistent |
|---|---:|---:|---|---|---:|
| census_tau1e-08 | 54 | 54 | 4 131 / 0 | 115 566 / 0 | 54 |
| census_tau1e-06 | 54 | 54 | 4 107 / 0 | 115 566 / 0 | 54 |
| write_set_tau1e-08 | 54 | 54 | 4 173 / 0 | 115 566 / 0 | 54 |
| write_set_tau1e-06 | 54 | 54 | 4 149 / 0 | 115 566 / 0 | 54 |

## 3. The declaration (committed at `8e94a3a7`, before any trace was read)

Copied from the script's docstring; the full text is there. *Stop*: the last sweep of one block loop
in one evaluation. *Parts*: `census`, `non_census` of the block's write set; out-of-test = `non_census`
under the census set. *Open*: maximum ≥ τ or a flag. *Downstream*: later block or deferred tail (from
the record's `schedule_resolution`) or the objective and constraints; for the flat block, the objective
and constraints. *Who reads what*: `reads_by_node` of the census stage's run-time read census,
`runs/census_tau1e-08/census/<configuration>/optimisation/census.json` (arm `BR`, seed 0;
`objective_constraints` is the objective layer; sha256 tok `b8697555e4305e1d`, lad `613dd8b304033201`,
st `82ba41fe5774c8be`) — **not a tracked file** (decision 4, §8).

S1 out-of-test maximum at the stop (distribution, share open, ≥ 10τ); S2 one-sweep stops; S3 worst
components in and out of the test; S4 at open stops, whether the worst / any open out-of-test component
is read downstream; S5 finite-difference pairs whose sweep counts differ; S6 the mirror under the
write set (census part at the stop; the sweep `k*` the census part closed; extra sweeps; non-census
maximum at `k*`; exact for the flat block and `M1`, approximate for `M2`, `M3`); S7 per run. **E** =
share of gradient evaluations with ≥ 1 open out-of-test stop read downstream; **E_obj** with the
objective and constraints alone.

**The conjecture's test.** Disturbed (D): st census 1e-8 `B2`; st census 1e-6 `B0`, `B2`. Undisturbed:
st census 1e-8 `B0`; tok, all. **C1** ≥ 5 % of gradient-evaluation stops open out of test in each D
case; **C2** ≥ half of those with an open component read downstream; **C3** E discriminates (D side
≥ 2× the U side) in T1 st/tok arm for arm at both census τ, T2 st 1e-8 `B2`/`B0`, T3 st `B0` 1e-6/1e-8.
**Refuted** if C1 or C2 fails in a D case; **supported** if C1, C2 hold everywhere and every C3
comparison discriminates; otherwise **present but not shown to be the cause**.

## 4. Results against the declaration (measured; `stopping_sweep_residuals.py` at `5bfdb466`)

**C1 and C2 hold in every D case:**

| D case | gradient-evaluation stops open out of test (C1, ≥ 0.05) | of those, an open component read downstream (C2, ≥ 0.5) |
|---|---|---|
| st census 1e-8 `B2` | 24 748 / 36 456 = 0.679 | 21 254 / 24 748 = 0.859 |
| st census 1e-6 `B0` | 28 807 / 34 972 = 0.824 | 18 687 / 28 807 = 0.649 |
| st census 1e-6 `B2` | 68 955 / 124 992 = 0.552 | 59 692 / 68 955 = 0.866 |

**E, gradient evaluations, phase B** (population: the traced runs of the run ID, both job sets; tok
and lad 3 starts, st 6):

| cfg | arm | census 1e-8: E / E_obj / E_live (L1) | census 1e-6: E / E_obj / E_live |
|---|---|---|---|
| tok | B0 | 0.074 / 0.074 / 0.010 (1 880) | 0.274 / 0.274 / 0.249 (1 880) |
| tok | B1 | 0.191 / 0.191 / 0.010 | 0.214 / 0.214 / 0.081 |
| tok | B2 | 0.905 / 0.431 / 0.076 | 0.905 / 0.587 / 0.453 |
| lad | B0 | 0.064 / 0.064 / 0.014 (10 754) | 0.332 / 0.332 / 0.332 |
| lad | B1 | 0.200 / 0.200 / 0.016 (5 000) | 0.202 / 0.202 / 0.063 |
| lad | B2 | 0.900 / 0.501 / 0.184 | 0.925 / 0.600 / 0.527 |
| st | B0 | 0.535 / 0.535 / 0.298 (5 432) | 0.534 / 0.534 / 0.417 (34 972) |
| st | B2 | 1.000 / 0.749 / 0.425 (12 152) | 0.914 / 0.749 / 0.556 (41 664) |

**C3 does not discriminate** in 5 of 6 comparisons: T1 st/tok `B0` 1e-8 **7.18** (discriminates);
`B2` 1e-8 1.11; `B0` 1e-6 1.95; `B2` 1e-6 1.01; T2 st 1e-8 `B2`/`B0` 1.87; T3 st `B0` 1e-6/1e-8 1.00.
**Declared verdict: present but not shown to be the cause.** Not refuted (C1, C2 hold); not supported
(the rate is as high on tok, never disturbed, and T2/T3 fail).

**S1–S4, the shape** (gradient evaluations, census 1e-8; the full per-block tables are in the script's
output §3): the flat loops are open out of the test at 53 % (tok `B0`), 47 % (tok `B1`), 55 % (lad
`B0`), 88 % (st `B0`) of stops; the partitioned blocks: `M1` 64 / 60 / 71 % (tok / lad / st), `M2`
5 / 5 / 36 %, `M3` 88 / 85 / 96 %. One-sweep stops are 0–4 % of flat stops and 6–48 % of block stops;
under the census set every flat one-sweep stop is open (tok 47/47, st 194/194) — at a one-sweep stop
the "change" includes the move of the design point itself (inferred). **Downstream (S4):** `M1`'s open
components reach the objective and constraints (st `B2` 8 670 of 8 670 open stops have one read there;
the worst is read there in 3 689); `M3`'s worst open component is never read by the objective layer, any open one is read by a later
node in 11 712 of 11 712 and by the objective layer in 328 (st); `M2`'s worst open component is read by a later block in 868 of
4 366 (st 1e-8: `build.r_shld_inboard_inner`, read in `M3`) and by the objective in none.
**S3 worst components** (st census 1e-8): `M1` in-test `current_drive.f_c_plasma_bootstrap`, out-of-test
`physics.f_beta_alpha_beam_thermal` and `current_drive.big_q_plasma` — **st's objective quantity
itself is a non-census component of `M1`** (the objective seed of `defer_per_run_st_regression.json` is
`current_drive.big_q_plasma`); `M2` in-test `tfcoil.str_wp`, out-of-test
`superconducting_tfcoil.a_tf_plasma_case`; `M3` `heat_transport.tlvpmw`; flat `B0` in-test
`tfcoil.str_wp`, out-of-test `a_tf_plasma_case`, `f_beta_alpha_beam_thermal`, `big_q_plasma`. On tok and
lad the flat loops' worst out-of-test components are `heat_transport.tlvpmw` and `costs.c243`.

**S5, finite-difference pairs whose total sweep count differs** (both points of a column): flat arms
25–49 %, partitioned 54–83 %, **about as often under the whole write set as under the census set**
(st `B2`: census 1e-8 64 %, 1e-6 54 %; write set 1e-8 70 %, 1e-6 83 %; st `B0` 36 / 39 % against 49 /
45 %). Sweep-count asymmetry alone does not mark the disturbed settings (measured).

**S6, the mirror** (whole write set, gradient evaluations): the census part at the stop is exactly 0 at
every `M1` and `M3` stop on all three configurations at 1e-8 (e.g. st `B2` `M1` 5 992 / 5 992); `M2`
is not (st 2 173 / 5 992 zero). The write set runs **extra sweeps after the census part has closed**
at `M1` 64 / 60 / 71 % and `M3` 88 / 85 / 96 % of stops (tok / lad / st, 1e-8), flat st `B0` 88 %,
median 1 extra.

## 5. What the traces add on why the two stop tests differ (L, added after the first trace, labelled)

**L2 — the extra write-set sweep is a confirmation sweep where the census change was 0** (measured):
whenever the census part closed with a change of exactly 0 and the write set ran another sweep, that
sweep changed **nothing in the whole write set** — in every block, configuration and both write-set τ
(e.g. 1e-8: tok `M3` 1 575/1 575, lad `M3` 4 095/4 095, st `M1` 2 182/2 182, st `M3` 5 630/5 630, st
`B0` 1 892/1 892; 1e-6: lad `M3` 3 238/3 238, st `M3` 2 869/2 869). This is phase A's "one sweep more,
exit state bit-identical" on lad and st, seen in every evaluation of the optimisations. It also says,
over these populations, that the census set captures every carried component of those blocks: had any
carried component been left out, some such sweep would have moved (inferred).

**L1 — where the census change at the stop is not 0 the out-of-test values are not at the fixed point;
elsewhere they are** (the second inferred from L2's mechanism): st `B2` 1e-8 open stops by census change
0 / not 0: `M1` 4 380 / 4 290, `M2` **0 / 4 366**, `M3` 11 384 / 328; st `B0` 1 481 / 3 294; tok `B2`
`M1` 1 161 / 54, `M3` 1 575 / 90. **E_live** (E over stops whose census change is not 0) separates st
from tok at 1e-8 (`B0` 0.298 vs 0.010, ×29; `B2` 0.425 vs 0.076, ×5.6) but not at 1e-6 (×1.67, ×1.23),
nor T2 (×1.43) nor T3 (×1.40) — post hoc, and still not discriminating (measured).

**L3 — those residuals are of the census set's own size** (inferred from the lag model: next change ≈
change at the stop × census change at the stop / census change one sweep earlier): the estimate is ≥ τ
at 1.2 % (st `B0` 1e-6, 284 / 24 080), 2.6 % (st `B0` 1e-8, 86 / 3 294), 0.1 % (st `M2`, 4 / 3 498 and
13 / 10 934), 3.3 % and 1.1 % (tok `B0` 1e-6 and 1e-8), 0 % on every other block where it is defined.

**Reading** (inferred): the test sets differ in *when* they stop, not in what they leave behind beyond
τ. The census test stops one sweep earlier on blocks whose feedback settles exactly (tok, lad, st `M1`
and `M3`), leaving the downstream values exact; the write-set test spends a sweep proving it. Where the
census feedback does not settle exactly (st's coils block `M2` and st's flat loop, A104's 0.034
contraction), both tests truncate at τ — the census test on the census components, the write-set test
on the larger set, i.e. effectively at a tighter census residual by the amplification factor (st `M2`:
non-census ≈ 1.2–36 × census in the format-check trace). So on st the whole write set at 1e-6 behaves
like a tighter census test (inferred; consistent with A104's census 1e-10 being "sufficient", not
tested here). That the objective quantity itself (`big_q_plasma`) is a non-census, lagged component of
`M1` on st, and is open at the stop in thousands of gradient evaluations at both τ, is measured; that
this matters for the optimiser is not.

## 6. Phase A (3 displaced seeds per arm, measured)

Census 1e-8: `A2`'s `M1` and `M3` stop open out of the test on all 3 seeds of every configuration, each
with census change 0 (L1); `M2` open on st only (3/3, census change not 0). Write set 1e-8: `M1` and `M3`
run exactly one extra sweep on every seed (tok, lad, st 3/3), and that sweep changes nothing (L2 3/3
each); st `M2` and st `A0` run one extra sweep with the census part at 1.4e-10 (not 0). Warm-up and
measured trace lines agree in sweeps on all 96 phase A runs.

## 7. The four campaigns untouched (measured)

`find runs/<run ID>/campaign -newermt '2026-10-02T16:11:03'`: **0** files under each of the four.
`--jobs campaign --resume`: **553 of 553 kept, run 0** under each of the four. `--paper-tables check`:
`census_tau1e-06`, `write_set_tau1e-08`, `write_set_tau1e-06` **IDENTICAL** without change;
`census_tau1e-08` refused (the gate verdicts I pressed had moved); re-made `--measure gate_table
--resume` and `--paper-tables write`; **three lines moved, all in the verification table**: the
stage-record commit list gains `d1e94dc8`; `G0` row `at c412bbdb` → `at d1e94dc8` (PASS, 1 of 77, 4/4,
unchanged); **`G1` row PASS `0 of 54985` → FAIL `3 of 55933` at `d1e94dc8`** (§1). No result cell
moved; `check` then IDENTICAL; `paper_cells_recount.py`: 44 rows, 0 mismatched. Committed `5bfdb466`.

Disk `/mnt/c`: 129 GB free at start, 131 GB at end. Traced records 153 / 192 / 150 / 148 MB.

## 8. Everything unexpected, and every decision

**Unexpected.**
1. The one-sweep lag (§5) — found on the first trace read for the format check; it reframes S1.
2. G1 FAILs on `audit_snapshot.wall_s` (§1): a latent hole in G1's exclusion table, exposed by the
   first straddle with the snapshot block on both sides. Not fixed.
3. `PROCESS_diff.py` exited 1 at the base (`3211f50e`): A90's four `evaluators.py` hunks were unclaimed
   and the file had no summary. I added the block-trace annotations and a summary; it now exits 0.
4. `CHANGES.md`'s header count ("seven files, thirty-one recorded edits") was already stale (the
   permitted list has eight files); I noted A115's two additions beside it rather than recount.
5. st's traced starts 0, 2, 4 all fell in one class; the declared fallback added seed 6 (§2).
6. `costs.coecap` on st's flat loop scores out-of-test changes up to 2e12 (scale artifact; its writer is
   a per-run-deferred cost node and the objective does not read it). It inflates S1's maxima on st `B0`
   only.
7. Under census, every flat one-sweep stop is open out of the test — the design-point move, not a
   residual (inferred).

**Decisions.**
1. **Census split under the write set** by a new trace-only variable rather than reading the census
   artifact unconditionally (the existing `PROCESS_ARCH_TEST_SETS` is refused under `write_set`).
2. **Run kind `trace`** added to `records.RUN_KINDS` instead of reusing `gate`/`smoke` (A90, A104): a
   traced record is neither.
3. **Objective and constraints on the trace line** (A104's need: jumps between the points of a
   difference); not used by a declared statistic.
4. **Who-reads-what from the census stage's run-time record** (`census.json`, untracked, sha256 printed),
   not a tracked artifact: no tracked artifact holds per-node reads (the test-set artifact's `detail`
   names one reader per carried component; `defer_per_run_*.json` holds the objective/constraint seeds
   and DSM reads from a sibling export). Reversal: point `read_census` elsewhere.
5. **G1 before capture re-taken at `3211f50e`** (the previous after side straddled two commits, so no
   straddle could be stated from it); old captures moved, not copied.
6. **GC's DR13 side made with the trace on** (`STRADDLE_BLOCK_TRACE`), timers on as DR12's, so the trace
   is the one difference. The 16 traced GC records keep plain `block_trace.jsonl` (not compressed).
7. **L1–L3 added after the first trace**, labelled, declaration and declared verdict unchanged.
8. **`sweep_residual_st_more` pressed in full** (phase B st 6, 7, 8 under all four settings): the
   fallback needed seed 6, and run time allowed.
9. Presses without `--resume` (one commit stamp for every traced record).

## 9. What I did not check

- Whether the out-of-test movement, or the census truncation, **causes** the disturbance: no run removed
  it (an intervention — e.g. the census test plus one confirmation sweep, or the objective read after
  one more sweep — would). The objective/constraint hex on each line was not analysed (no exact reference).
- S6's counterfactual for `M2`/`M3` is approximate (their entry depends on the earlier block's stop).
- The read census is one `BR` optimisation (seed 0) per configuration; a read on a branch that run never
  took is not in it (trap T1 handled by the census's own closure). Reads by the next evaluation's earlier
  blocks are not counted as downstream.
- Population: 3 starts (tok, lad), 6 (st) and 3 phase A seeds per arm; rates are over evaluations, not
  starts, and evaluations within a run are not independent.
- G1/GC and the other gates only under `census_tau1e-08`; I-43's gates not touched.
- The reading script was not independently recounted.

## 10. Orchestrator's critical assessment (protocol §5) — verdict: merge

*Written 2026-10-02 by the orchestrating session. Checked differently from the agent.*

**Checked.** (1) `git diff --stat 3211f50e..43d78ce6`: fifteen files — the driver copy's two loop files
(`caller.py` 38 lines, `module_solve.py` 181), the copy's bookkeeping (`CHANGES.md`, `PROVENANCE.json`, `copy_gates.py`,
`PROCESS_diff.py`), the harness (`traced_runs.py` new, `switches.py`, `records.py`, `gate_count_neutrality.py`, the
runner, the README), `stopping_sweep_residuals.py`, `paper_tables.md` and this report; 0 files under any `models/`
folder and 0 diff lines under the repository's own `process/`. (2) **The `caller.py` hunks read line by line**: every
added statement sits behind `block_trace is not None` (the trace switch) or is an argument passed to a trace function;
the stop decision (`res.converged(tau)`) and the residual it uses are not touched. (3) **The neutrality claim recounted
with the orchestrator's own code and choice of fields** (node calls, iterations, model calls, predicate evaluations,
the objective's hex, `ifail`, attempts, the exit-state digest, and `y_exit.json`'s state component by component): 54
traced runs per run ID, all at `d1e94dc8`, run kind `trace`, **216 of 216 equal to their campaign record**. (4)
**Statistic C1 recounted from the compressed traces**: of the block stops on gradient evaluations, the share with a
change at or above τ outside the test set is 0.68 (st `B2`, census 1e-8), 0.82 (st `B0`, census 1e-6) and 0.55 (st
`B2`, census 1e-6) — the agent's three figures; the split by "census change exactly 0 / not 0" for st `B2` at 1e-8
(M1 4 380 / 4 290, M2 0 / 4 366, M3 11 384 / 328) is the agent's to the unit. (5) **The same rate on cases the agent
names as undisturbed, recounted**: tok `B2` at census 1e-8 0.52, st `B0` at census 1e-8 0.88. So the rate is as high
where the optimiser is not disturbed, which is the agent's reason for "present but not shown to be the cause", and the
orchestrator reads the same. (6) **The confirming-sweep finding (L2) recounted over every evaluation of the `B2`
traces under both write-set settings, all three configurations**: wherever the census part's change was exactly 0 at
the last sweep but one, the last sweep changed nothing in the census part or outside it — st M1 2 262 of 2 262 and M3
5 789 of 5 789 at 1e-8, 1 551 of 1 551 and 2 956 of 2 956 at 1e-6; lad and tok likewise, every block, no exception
(the orchestrator's counts are over all evaluations, the agent's over a subset, so the totals differ and the rate does
not). st's M2 never reaches a census change of exactly 0. (7) `--runs`: the four campaigns hold 553 records each at
their own commits; `--paper-tables check` IDENTICAL for the four documents; no file under the four `campaign/` folders
is newer than the dispatch. (8) The statistics added after the first trace was read are in a separate commit that says
so; the declaration's own verdict was not altered by them.

**What the result is, in the orchestrator's words.** The user's conjecture has two parts. *Other written variables are
still moving when the census test passes, and later blocks or the objective read them*: measured, yes, at most stops.
*That movement is the noise that disturbs the optimiser*: not shown — the same movement is as frequent on tok and on
st's flat arm at 1e-8, which are not disturbed. The traces add a distinction the conjecture did not have: most of the
movement is a one-sweep lag (a variable computed from the couplings the previous sweep left, final as soon as the
couplings stop changing exactly), and a real residual at the stop exists only where the couplings themselves have not
reached an exact fixed point — on st, the coils block always, the flat loop, and part of M1. That the whole-write-set
test removes the disturbance because it forces one more sweep on exactly those loops is inferred, by the agent and by
the orchestrator; no run removed the residual to test it.

**G1 under the default run ID now reads FAIL** (3 of 4 614 values, all `audit_snapshot.wall_s`, a stopwatch reading on
the three reference runs; 0 of 51 319 output-file lines). The gate's exclusion table already excludes wall-clock leaves
by name under issue I-10's rule (`wall_s`, the warm-up block's four); this leaf of the snapshot block is not listed
because no earlier straddle carried the block on both sides. The agent did not change the gate, correctly. It means the
default run ID's gate table reads 28 PASS, 1 FAIL and `paper_tables.md`'s verification table carries the G1 FAIL until
the exclusion is reviewed (issue I-45, into A116's scope).

**The agent's decisions.** The trace-only variable naming the census artifact under the write set, the new run kind
`trace`, and the objective and constraints on each trace line are all inside the trace path and are covered by GC's
DR12 → DR13 straddle (0 of 3 989 count leaves, 0 of 46 125 components). Who-reads-what was taken from an untracked
run-time record (its digest printed) because no committed artifact holds per-node reads: a limit on statistic C2,
which the report states. Annotating A90's unclaimed hunks in `PROCESS_diff.py` repairs a check that already failed at
the base.

**Limits carried.** Three starts on tok and lad, six on st. No intervention: causation is open. The read census is
from one reference optimisation per configuration. Gates pressed under the default run ID only; the four gate tables
are A116's. The objective and constraint values now on each trace line were not analysed: they would give the size of
the objective's jump per evaluation directly, which is the quantity A104 measured by other means.
