# A41 (v3-harness) — the V3 harness: a verbatim copy of V2's, then the V3 constructions; G4 and G7 pass with teeth, the verifier is given teeth of its own, and three defects in the delivered state are reported rather than repaired silently

> **Document status** — **CURRENT · TASK REPORT of an OPEN task.** Written by task A41
> (v3-harness), 2026-09-04, on branch `A41-v3-harness` in worktree
> `/home/wrutten/projects/PROCESS_surgery_worktrees/A41-v3-harness`, from the mint commit
> `b7dbd2a9`. **Not merged**; the orchestrator assesses per protocol §5 and archives this
> file to `deprecated/` at merge. Folder position records lifecycle, not validity (trap T3).
> Experiment base commit `c0ae5b28`; **no file under `process/` is touched by this task**.
> Nothing is pushed.

| | |
|---|---|
| **Task** | V3 development plan §8 deliverable T3: the `arch_surgery/MDA_partitioning_experiment_v3/` directory — first commit a **verbatim copy of the V2 harness** (user directive, diff legibility), then the config / runner / phase-script modifications as separate commits; H3 exit forensics in the shared runners; the tally constructions T-a … T-e; gates **G4** and **G7** with teeth; `--verify` |
| **Verdict** | **The harness is built and its two owned gates PASS with teeth.** G7 (record completeness): a deliberately unconverged run carries all five H3 fields, and **6 of 6** teeth are refused with the missing field named. G4 (audit restriction): a doctored post-solve-owned component moves the whole-state audit from `0x1.2345ac5dd4c80p-32` to `0x1.f72fd02c36fa8p-2` while the restricted maximum stays **bit-identical** at `0x1.eae3a0e959de8p-34`; a doctored in-loop component moves both and costs one extra block sweep (5 → 6). Both directions shown. The carried V2 gates (entry-state extension, G6 warm equivalence) also pass at the V3 commit. **Three defects in the state this task inherited are reported below, one of them repaired here because it is this task's own file** |
| **Findings** | **(1)** `--verify` as delivered could not fail — it read only `runs/phase_*/campaign/**`, which cannot exist while `EXECUTION_APPROVED` is `False`; executed, it printed *0 cells checked, 0 mismatches* and exited 0. Fixed here (`--mode smoke`) and given **its own teeth** (`--teeth`). **(2)** The V3 directory had **no `.gitignore`**, so `git status --porcelain` was never empty and **every V3 record stamped `tree_git_dirty: true`** on an otherwise clean tree. Repaired (V2's one-line file, restored). **(3)** The check-1 (same-optimum) construction in `phase_b.py` **does not match** the construction A39's `EXPERIMENT_PLAN.md` §4.2 declared after this branch point: the harness computes an **absolute** `\|Δ norm_objf\|` with a floor of `1e-6 ×` the median `\|norm_objf\|`; the plan declares a **per-pair relative** `r = \|Δ\| / max(\|objf\|ₐ, \|objf\|ᵦ)` with the floor `1e-6` on that relative quantity. **Reported, not repaired** — see §7 |
| **Scripts** | [`arch_surgery/MDA_partitioning_experiment_v3/`](../../MDA_partitioning_experiment_v3/): `v3_config.py`, `v3_runner.py`, `phase_a.py`, `phase_b.py`, `run_experiment.py`, `v3_report_analysis.py`, `.gitignore`. Additive H3 instrumentation in [`arch_surgery/idf_probe/run_one.py`](../../idf_probe/run_one.py) and [`arch_surgery/idf_probe/v2_eval_one.py`](../../idf_probe/v2_eval_one.py). Every number below comes from executing one of these (protocol §15) |
| **Runs** | **37 fresh-subprocess PROCESS runs in this resumption**, all `rc = 0` and `status: ok`, W = 1 throughout (A40 holds the machine's heavy slot). Every cited number comes from the clean-tree set of 15 at `1e5eaf46`: G7's forced-unconverged optimisation (1), the Phase A machinery smoke on `st_regression` (11 single-MDA evaluations), the Phase B machinery smoke (3 optimisations). The 22 earlier runs at `66d702af` and `9e95bb05` reproduce them bit-for-bit and are cited only as reproductions |
| **Environment** | `PROCESS_surgery_env` (`/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python`, 3.12.14); `PYTHONPATH` pinned to **this worktree** for every measurement subprocess and the exact tree asserted in-process via `--expect-tree` (traps T6 / T10); a26 artifacts; τ = 1e-6; δ = 0.10; `runs/` untracked |
| **Date** | 2026-09-04 |

---

## 1. Verdict

The V3 harness exists, refuses everything it is not yet licensed to run, and the two gates
this task owns pass with teeth that were shown to bite. Nothing in it is a measurement:
every run below is machinery at smoke scale, and the report says so at every table. The
campaign is A42's and is not approved; the prime is A40's and is not built, so the harness
refuses `A1`, `B2` and `B3` by name rather than composing them silently.

Three defects were found in the state this resumption inherited. Two are in this task's own
files and are repaired here, each in its own commit with the measurement that shows the
repair works. The third is a divergence between this harness and a plan that was merged to
trunk **after** this branch point; it is reported with both constructions written out, and
it is left for the orchestrator to adjudicate — repairing it here would be choosing between
two declarations, which is not this task's to do.

## 2. The verbatim copy, and exactly what changed after it

The user's directive (development plan §7 / §8 T3) was that the first commit be a verbatim
copy of the V2 harness, so that every later modification reads in history as a diff against
V2. It is.

**Verified, not assumed.** Each of the six copied files was diffed against its V2 original
in the main checkout (read-only). The only difference in any of them is a three-line
provenance block plus a blank line, inserted inside the existing module docstring, naming
the source path and the commit copied from:

```
Verbatim copy (task A41, first commit) of
arch_surgery/MDA_partitioning_experiment_v2/<file> at commit b7dbd2a9;
content otherwise unchanged.
```

There is **no other difference** — not a renamed identifier, not a reflowed line. The V2
files themselves are byte-identical between this worktree and the main checkout, so the
comparison is against the frozen V2 record and not against a local copy of it.

*Caption: one row per harness file; the V2 original it was copied from at `913b89f0`, the
line counts before and after all of A41's work, the added/removed line counts against V2 at
this report's HEAD, and what the modification does. Line counts are exact and reproduce
bit-for-bit; they are structure, not measurement.*

| V2 original | V3 file | V2 lines | V3 lines | vs V2 | what changed after the copy, and why |
|---|---|---|---|---|---|
| `v2_config.py` | `v3_config.py` | 84 | 153 | +89 / −20 | `EXECUTION_APPROVED = False`; the V3 arm sets (`A0`/`A1u`/`A1`, `R`…`B3`), `PRIMED_ARMS` and `PRIME_ENV_VALUE` (O4/D19); the O3 floor `OBJF_FLOOR_REL`, the check-1a `CLUSTER_GAP_FLOOR_FACTOR`, the declared `MEDIAN_CONSTRUCTION`; the `INSTRUMENTATION` ledger with `prime` and `exit_forensics` |
| `v2_runner.py` | `v3_runner.py` | 231 | 263 | +83 / −51 | `PROCESS_ARCH_PRIME` added to the cleared-switch list and set on `B2`/`B3`; a primed arm **refuses to compose** while the prime instrument is absent; `V3_WORKERS` pool override, stamped; `--force-maxcal` passthrough for G7 only |
| `phase_a.py` | `phase_a.py` | 1160 | 1593 | +723 / −290 | three arms instead of two; the restricted audit requested on every run (T-a); **gate G4** and its teeth; the T-e carrier closure; the T-d per-block split; the G7 completeness contract on every Phase A record; G6 run for both block arms |
| `phase_b.py` | `phase_b.py` | 485 | 960 | +614 / −139 | **gate G7** and its teeth; the declared nearest-rank median with `statistics.median` published beside as a diagnostic; T-b taxonomy with denominators and the deck-invalid-seed statistic; T-c floor and clustering; check 3 and check 4; T-d |
| `run_experiment.py` | `run_experiment.py` | 75 | 84 | +22 / −13 | draft mode runs preflights + G7 + both smokes and then names what is missing and which task owns it |
| `v2_report_analysis.py` | `v3_report_analysis.py` | 497 | 768 | +654 / −383 | the V3 constructions restated independently (never imported from the tally); `--mode smoke`; `--teeth` |

Two files outside the directory changed, both **purely additive** (+156 and +72 lines, zero
deletions): `arch_surgery/idf_probe/run_one.py` and `v2_eval_one.py` carry the H3 exit
forensics. These are the shared instruments, which the plan (§6 H3) names explicitly; V2's
own record fields and its `--verify` are untouched, so V2's frozen records remain readable
by the code that wrote them.

*Caption: A41's commits in order, from the mint commit. The first is the verbatim copy; the
last two are this resumption's.*

| commit | what |
|---|---|
| `b7dbd2a9` | (mint commit — branch point, not A41's) |
| `913b89f0` | **verbatim copy** of the V2 harness into `MDA_partitioning_experiment_v3/` |
| `e660d2b1` | `v3_config.py` — the V3 declarations in one place |
| `e55521fb` | `v3_runner.py` — arms from nothing, `PROCESS_ARCH_PRIME` cleared and set |
| `06faf5bb` | H3 exit forensics in the shared runners — additive |
| `cfa03b58` | `phase_a.py` — three arms, G4 teeth, T-a / T-d / T-e |
| `31f112b4` | `phase_b.py` + `run_experiment.py` — G7, T-b / T-c / T-d, declared medians |
| `66d702af` | `v3_report_analysis.py` — independent recomputation with `--verify` |
| `9e95bb05` | `--verify` made exercisable (`--mode smoke`) and given teeth (`--teeth`) |
| `1e5eaf46` | the V3 directory's `.gitignore` — the clean-tree stamp |

## 3. Gates and teeth

A gate whose teeth were not shown to bite is not a gate (protocol §12). Every tooth below
was executed, and its refusal recorded, in the same script run that produced the gate's own
verdict.

### 3.1 G7 — record completeness (this task's gate)

One `st_regression` optimisation is forced unconverged with `--force-maxcal 2` (a flag that
exists for this gate and is stamped into the record; it is never a campaign parameter). The
H3 block must carry all five fields at that unconverged exit.

*Caption: G7's run and its teeth, from `runs/phase_b/g7gate/gate.json` at `1e5eaf46`
(`tree_git_dirty: false`). Each tooth deletes one field, or the whole block, from a copy of
the record and requires the tally's completeness check to refuse it **and name what is
missing**. Verdict PASS requires the run complete and all six teeth refused.*

| quantity | value |
|---|---|
| exit | `ifail = 2` (forensics) and `ifail = 2.0` (MFILE, the independent source) — agreeing |
| ladder stage at exit | `epsfcn_x0.1` (attempt 3 of 3; `epsfcn` 0.001 → 0.01 → 0.0001, each attempt recorded) |
| `n_solver_iterations` | 2 at the last attempt, 6 summed over attempts (both recorded) |
| constraint residual vector | 18 components — 3 equality, 15 inequality — with their `icc` numbers and hex floats |
| active set | `icc` {16, 17, 33}, at the solver's own tolerance `1e-8` |
| fields present | **5 / 5** |
| teeth | **6 / 6 refused**, each naming its field: the five fields individually, plus the whole `exit_forensics` block |
| verdict | **PASS** |

### 3.2 G4 — audit restriction (this task's gate)

A38's construction, re-run inside the V3 harness on the prime-free block arm `A1u`. Three
runs from the same reference exit snapshot: a baseline, one with a post-solve-owned
component doctored by ×1.5, one with an in-loop component doctored by ×1.5. The excluded set
is derived — post-solve nodes → the committed run-time write census → the a26 spec's keys —
never a prefix; on `st_regression` that is **123 excluded, 682 kept** of the spec's 805
continuous components (827 total, 22 discrete), `sha256 dea7fd6e…`.

*Caption: G4's two directions on `st_regression`, from
`runs/phase_a/smoke/st_regression/restricted_teeth/gate.json` at `1e5eaf46`. Bit-comparisons
and one scaled residual; the restricted statistic must be **blind** to the post-solve
displacement and **sighted** to the in-loop one. Machinery smoke — these are gate results on
real runs, not campaign measurements.*

| | baseline | post-solve doctored (`costs.c21` ×1.5) | in-loop doctored (`superconducting_tfcoil.a_tf_plasma_case` ×1.5) |
|---|---|---|---|
| whole-state audit max (hex) | `0x1.2345ac5dd4c80p-32` | `0x1.f72fd02c36fa8p-2` — **moved** | `0x1.2399223e1e93bp-32` — **moved** |
| restricted audit max (hex) | `0x1.eae3a0e959de8p-34` | `0x1.eae3a0e959de8p-34` — **bit-identical** | `0x1.1262727efeac2p-36` — **moved** |
| restricted argmax | `superconducting_tfcoil.a_tf_plasma_case` | unchanged | `fwbs.p_cp_shield_nuclear_heat_mw` |
| block sweeps | 5 | — | **6** (more work) |
| the doctored component's own scaled residual | — | expected `0.49139333029136534`, measured `0.49139333028665044` (agree to 1e-11 relative) | — |
| checks | — | 7 / 7 | 3 / 3 binding (5 / 5 recorded) |
| verdict | | | **PASS** |

The in-loop direction is accepted on **`restricted moved OR more work`** — A38's OR
semantics, carried verbatim: at a bit-exact fixed point a re-converged component can land on
identical bits, so requiring movement alone would be a gate that fails for a correct
implementation. Here both halves are true independently, so the OR is not load-bearing on
this deck and the report says which half held.

### 3.3 The V2 gates the harness carries, re-run at the V3 commit

*Caption: the entry-state extension gate and the G6 warm-equivalence gate on `st_regression`,
from the same Phase A smoke at `1e5eaf46`. Both are V2/A36 constructions re-run unchanged;
thresholds are declared in the record before the gate run is launched.*

| gate | criterion (declared before the run) | measured | teeth | verdict |
|---|---|---|---|---|
| entry-state extension | audit ≤ `0x1.c22fb514702ddp-29`, `block_sweeps == 1`, `node_calls == 21`; entry read back bit-exactly, no skipped components | audit `0x1.eae3a0e959de8p-34`, sweeps 1, node calls 21, 0 entry mismatches | 1 hand perturbation (×1.5 on a continuous non-design component): audit `0x1.1262727efeac2p-36`, sweeps 2 — **tripped** | **PASS** |
| G6 warm equivalence, arm `A1u` | categorically clean **and** cross-state max residual vs the reference < τ = 1e-6 | cross max `0x1.c22fb514702ddp-29` (3.28e-9), 0 above τ, 0 discrete mismatches, 0 constants moved, 0 new NaN | 2 perturbations (a continuous bump at 3τ scale, a discrete flip): **2 / 2 tripped** | **PASS** |

G6 is run for **each** block arm present. With the prime unbuilt, `A1` refuses and only
`A1u` runs; at A42 the same loop covers `A1` as well, which together with the entry gate on
`A0` is the plan's "all three arms".

### 3.4 The verifier's own teeth

`v3_report_analysis.py` is the independent recomputation protocol §15 requires. As delivered
it read only the campaign records, which cannot exist while `EXECUTION_APPROVED` is `False`.
Executed, it printed:

```
--verify: 0 cells checked, 0 mismatches      (exit 0)
```

That is a pass that cannot fail. Two additive changes were made — no construction altered.
`--mode smoke` points the same recomputation and the same cell-by-cell comparison at the
machinery-smoke records; `--teeth` doctors one recomputed cell at a time in memory (never the
records, never the on-disk tally) and requires `--verify` to refuse it and name the cell.

*Caption: the verifier exercised against the Phase A machinery smoke at `1e5eaf46`. A tooth
with no corresponding cell in these records is reported as "not applied" and is **not**
counted as a pass.*

| | result |
|---|---|
| `--mode smoke --verify` | **11 cells checked, 0 mismatches** |
| tooth: Phase A `n_paired_ok` +1 | trips — *`A/st_regression/n_paired_ok: analysis 3 vs tally 2`* |
| tooth: Phase A restricted median ×1.5 | trips — *`…/restricted/A0/median: 7.958e-09 vs 5.305e-09`* |
| tooth: unweighted count ratio +1e-12 | trips — *`…count_ratio[A0->A1u]: 0.492063492064492 vs 0.49206349206349204`* |
| tooth: restricted-recompute mismatch injected | trips — *`recomputed restricted max differs from the runner's on 1 runs`* |
| tooth: Phase B check-2 median ×1.5 | **not applied** — no Phase B campaign records exist |
| verdict | **PASS** (4 / 4 applied teeth trip, baseline rc = 0) |

## 4. The tally constructions T-a … T-e

Every construction is declared in `v3_config.py` or stamped into the tally's own output, and
restated independently in `v3_report_analysis.py` — which deliberately does not import the
tally code, so a tally bug cannot vouch for itself. The restricted maximum is **recomputed
from the raw per-component vector** (`audit_residual.json`) and compared bit-for-bit against
the runner's own `exit_audit.restricted.max`; a disagreement is a `--verify` mismatch.

**The declared median.** For **every Phase B check statistic** the median is
**nearest-rank, upper-middle: `sorted_values[n // 2]`** — `MEDIAN_CONSTRUCTION` in
`v3_config.py`, stamped into `runs/phase_b/tally.json` under `declared.median_construction`
and into `runs/report_analysis*.json` under `declared`. `statistics.median` is computed and
published beside it as `median_statistics_diagnostic`, **never** as the check value. The
Phase A audit distributions use `statistics.median` instead, and the Phase A tally stamps
that difference explicitly in `quantile_definitions` rather than leaving it to be inferred.
p90 is nearest-rank, element `ceil(0.9 n)`, in both phases.

*Caption: the five declared tally constructions, where each lives, and what the Phase A
machinery smoke on `st_regression` produced for it (2 seeds, arms A0 and A1u — machinery,
**not** a measurement; A38's merged measurement of this arm is the number to cite).*

| | construction | where | smoke output |
|---|---|---|---|
| **T-a** | similarity over the restricted component set, whole-state audit published beside; excluded set derived nodes → write census → spec keys | `phase_a.py` `_tally`, `excluded_keys` | restricted medians A0 `5.31e-09` / A1u `1.02e-03`; whole-state A0 `5.31e-09` / A1u `0.241`. The restriction removes the post-solve charge: A1u's whole-state statistic is 236× its restricted one |
| **T-b** | declared both-converged pairing, A30 taxonomy with denominators, deck-invalid-seed statistic | `phase_b.py` `stage_tally` | Phase A analogue: taxonomy `ok: 2/2` per arm on a denominator of 2 |
| **T-c** | check 1 with floor, check-1a clustering and hop rates | `phase_b.py` `stage_tally`, `_clusters` | no Phase B campaign records — not exercised (see §7 finding 3) |
| **T-d** | per-block node-call split as a first-class artifact | `phase_a.py` `_per_block_split`, `phase_b.py` | A0 M1 24 / M2 36 / M3 144 / post-solve 48 = 252; A1u M1 16 / M2 36 / M3 72 = 124 |
| **T-e** | per-run carrier closure from `perturbation.json`, no new field | `phase_a.py` `_closure` | `build.dr_shld_vv_gap_outboard` = −Δ_out, A35's `st` image: relative difference **6.72e-08** median over 2 runs; the restricted argmax **is** that closed image in 2 / 2 runs |

The tally also carries a **parser tooth** of its own: it doctors one excluded and one kept
component in a copy of a real `audit_residual.json` and requires the whole-state statistic to
move in both cases and the restricted statistic to move only for the kept one — 4 / 4 checks,
**PASS**, on `runs/phase_a/smoke/st_regression/A1u/start001/audit_residual.json`.

## 5. What the harness refuses, and why that is the deliverable

*Caption: the refusal surface, exercised end to end through the one-button entry point
(`run_experiment.py`, draft mode) at `9e95bb05`, rc = 0. Every refusal names the task that
owns the gap; nothing degrades silently into a different arm.*

| stage | state | refusal text |
|---|---|---|
| `v3_config.EXECUTION_APPROVED` | `False` | Phase A `campaign` returns 3: *"REFUSED: execution not approved … Run 'smoke' for the machinery test"* |
| `INSTRUMENTATION["prime"]` | `False` (A40) | Phase A preflight NOT READY; arm `A1` refuses to compose; Phase B `B2`/`B3` REFUSED on all three decks |
| `INSTRUMENTATION["exit_forensics"]` | `False` | Phase B preflight NOT READY — see §7 finding 4 |
| `st_regression` / `B1` | k = 0 | *"B1 degenerates to B0 on this deck (plan §3.2) — skipped by design"*, and **not** counted as an instrumentation gap |
| a primed arm on a tree without the variant point | — | `SystemExit` with the reason: the switch would be silently ignored and the run would measure the wrong arm (the T6 / T10 hazard shape) |
| tally, any `ok` record missing an H3 field | — | the tally **refuses** (returns 2) and names the record — G7's contract |

The Phase B machinery smoke runs one baseline optimisation per currently runnable arm family
— `R` and `B0` on `st_regression`, `B1` on `large_tokamak_nof` — and reports `B2`/`B3` as
refused by name. All three are `status: ok` with complete exit forensics (`3 / 3`
`machinery_ok`). Their solve-phase node calls are 39 669 / 42 756 / 44 142 and their
objective hex floats `-0x1.096acf3342eefp+4` / `-0x1.096acf3342e3cp+4` /
`0x1.9999999a4496cp+0`; these are **machinery, not measurements** — they exist to show the
path runs and to be reproduced. They were, exactly, across the `66d702af` and `1e5eaf46`
executions.

## 6. What is deliberately not done here

- **The campaign is not run.** Phase A's three arms × 25 seeds × 3 decks and Phase B's five
  arms are **A42's** (`v3-campaign`), blocked on A39–A41 merging *and* the user's dated
  execution approval. `EXECUTION_APPROVED` stays `False` in this branch; flipping it is the
  approval commit's job, not a harness commit's.
- **The prime is not implemented and not measured.** The `PROCESS_ARCH_PRIME` variant point
  in `process/core/caller.py`, and gates G1, G2, G3 and G3c, are **A40's** (`v3-prime`).
  A41 touches no file under `process/`. The harness names the variable, clears it from every
  composed environment, sets it on the primed arms, and refuses those arms until A40 merges.
- **G0, G5, G6 are implemented but not executed at scale.** G0 (driver neutrality against
  V2's recorded R) and G5 (B3 combined-switch equivalence) are A42's to run; G6 is run here
  on one deck for one arm as part of the smoke.
- **No robustness claim, no timing claim.** The timing block exists and is context-only; no
  number in this report rests on wall clock (I-10, trap T5). Every wall-clock figure the
  console printed is labelled as progress information at the point of printing.

## 7. Findings

**1 — `--verify` could not fail (repaired here).** Delivered, `v3_report_analysis.py --verify`
read only `runs/phase_*/campaign/**` and reported *0 cells checked, 0 mismatches*, exit 0.
Protocol §12 does not accept a check that cannot fail. Repaired at `9e95bb05` by
`--mode smoke` (the same recomputation, the same comparison, pointed at the smoke records and
writing its own output file so the campaign artifact is never clobbered), by `--teeth`, and
by making `verify()` say so when it checks zero cells instead of exiting 0 in silence.
Default behaviour is unchanged.

**2 — the missing `.gitignore` (repaired here).** V2's harness directory carries a one-line
`.gitignore` (`runs/`). The verbatim copy took the six `.py` files and not that file. Because
`run_one.py` stamps `tree_git_dirty` from `git status --porcelain`, and `runs/` is untracked
by design, **every V3 record — gates, smokes, and A42's campaign — stamped `dirty: true` on
an otherwise clean tree.** A38's own recheck treats `tree_git_dirty is False` as a provenance
criterion and the plan §7 asks for clean-tree stamps; both were unreachable here. Restored at
`1e5eaf46`; measured afterwards: `git status --porcelain` is empty, and all 11 Phase A smoke
records plus the G7 gate record now carry the single stamp `1e5eaf46 dirty=False`. The gate
numbers reproduce **bit-for-bit** across the dirty and clean runs, so nothing already
measured is invalidated — but the stamp now tells the truth.

**3 — check 1's construction diverges from the merged experiment plan (reported, not
repaired).** A41 branched at `b7dbd2a9`; A39's `EXPERIMENT_PLAN.md` merged to trunk
afterwards (`3eb3be30` / `a7918f37`) and declares in §4.2 check 1 a construction the
development plan had left unstated. The two do not agree:

*Caption: the same-optimum check as the merged experiment plan declares it against as the
delivered harness computes it. Both use F = 10 and both derive a floor from `OBJF_FLOOR_REL`
= 1e-6; they differ in what quantity the distribution is taken over.*

| | `EXPERIMENT_PLAN.md` §4.2 check 1 (merged) | `phase_b.py` `stage_tally` (delivered) |
|---|---|---|
| per-pair statistic | **relative**: `r = \|Δ norm_objf\| / max(\|objf\|ₐ, \|objf\|ᵦ)`, "the per-pair denominator … fixed now as the larger magnitude of the two sides" | **absolute**: `abs(f_b − f_a)` |
| floor | `1e-6`, relative on `norm_objf` | `floor_abs = 1e-6 × rank_median(\|objf\|)` of the pair's **base arm over the compared pairs** |
| yardstick | the R→B0 **relative** spread | the R→B0 **absolute** spread |
| acceptance | `r_quantile ≤ max(F × yardstick_quantile, floor)` at median **and** p90 | same shape, on the absolute quantities |

The two are not a rescaling of one another: `median(δᵢ / mᵢ) ≠ median(δᵢ) / median(mᵢ)` in
general. The harness's own check **1a** already uses the plan's relative-to-larger-magnitude
form (`_clusters`), so the primitive is present and the divergence is confined to check 1's
statistic. **Nothing is changed here**: choosing between two written declarations is an
adjudication, not a repair, and no campaign number has been computed under either. It must be
settled before A42 cites a check-1 number — the plan is the later and more specific document,
so the expected resolution is that `phase_b.py` adopts the per-pair relative form and
`v3_config.OBJF_FLOOR_REL`'s docstring is corrected with it.

**4 — the `INSTRUMENTATION` ledger needs two flips at merge, not one.** `exit_forensics` is
left `False` although its declared flip condition is met (the instrument is built and G7
passes with teeth), because the ledger's own convention is that an entry flips when its task
**merges** — every `True` entry is stamped `(merged DATE)` — and A41 does not merge itself.
The entry's comment now records the G7 result and the pending action.

The second flip is `prime`. **A40 (v3-prime) merged to `architecture_surgery` while this task
was running** (`1f176950` … `fa5cec0e`, 2026-09-04), so the `PROCESS_ARCH_PRIME` variant point
now exists on trunk. It does **not** exist on this branch, which is off `b7dbd2a9`, and the
harness is therefore correct as it stands: arm `A1` and arms `B2`/`B3` refuse by name on this
branch because on **this** tree the switch would indeed be silently ignored. At merge both
entries flip:

```python
"prime":           {"available": True, "task": "A40 (merged 2026-09-04)", ...}
"exit_forensics":  {"available": True, "task": "A41 (merged <date>)",     ...}
```

Until they do, Phase A and Phase B preflight both report NOT READY for gaps that will not
exist on the merged tree. Neither flip is made here: a ledger entry that claims an instrument
this branch does not contain would be exactly the silent-wrong-arm failure the refusals are
built to prevent.

**5 — `EXPERIMENT_PLAN.md` is absent from this branch,** for the same branch-point reason: it
is A39's deliverable, merged to trunk after `b7dbd2a9`. `v3_config.py` and
`run_experiment.py` both reference it by name, and it appears in the V3 directory when this
branch merges. Not a defect; recorded so the absence is not read as a missing deliverable.

## 8. Provenance

Every number in this report comes from executing a committed script (protocol §15). The
stages, and the commit each ran at:

*Caption: what was executed, from which entry point, at which commit. W = 1 throughout —
A40 holds the machine's heavy slot. "Machinery smoke" runs are stamped as such in their own
records and their numbers are never published as measurements.*

| entry point | stage | commit | result |
|---|---|---|---|
| `phase_b.py g7gate` | G7 + 6 teeth | `1e5eaf46` (clean) | PASS |
| `phase_a.py smoke` | reference, entry gate, G6 warm gate, **G4**, 2-seed campaign, tally | `1e5eaf46` (clean) | rc 0; all gates PASS |
| `phase_b.py smoke` | R, B0, B1 machinery + B2/B3 refusals | `1e5eaf46` (clean) | rc 0 |
| `v3_report_analysis.py --mode smoke --verify` | independent recomputation | `1e5eaf46` | 11 cells, 0 mismatches |
| `v3_report_analysis.py --mode smoke --teeth` | the verifier's teeth | `1e5eaf46` | PASS, 4/4 applied |
| `run_experiment.py` (one button, draft mode) | preflights + G7 + both smokes, 11 runs | `9e95bb05` | rc 0; G4 hex values **identical** to the `1e5eaf46` run |
| `phase_a.py smoke` | first execution of G4 (this resumption), 11 runs | `66d702af` (dirty — see finding 2) | same verdicts, same hex values as `1e5eaf46` |
| `phase_b.py smoke`, `phase_b.py g7gate` | the pre-interruption session's runs, 4 runs | `66d702af` (dirty) | same verdicts; `node_calls_solve_phase` 39669 / 42756 / 44142 and the objective hex floats reproduce **exactly** at `1e5eaf46` |

Bulk artifacts are under `arch_surgery/MDA_partitioning_experiment_v3/runs/` and stay
untracked; the verdicts and numbers above are the committed record of them. Console logs of
each stage are in that directory beside the records.

## 9. Change log

- 2026-09-04 — task A41 dispatched at mint commit `b7dbd2a9`. Harness built in seven commits
  `913b89f0` … `66d702af`; the Phase B machinery smoke and the G7 gate executed; the Phase A
  smoke (and with it gate G4) **not** executed; `--verify` **not** executed. **The session
  terminated on a model rate limit, mid-verification, before writing this report.**
- 2026-09-04 (resumption) — the delivered state verified against the artifacts rather than
  assumed: the verbatim-copy commit diffed file-by-file against the frozen V2 harness (only
  the permitted provenance block differs); G7's PASS and its six teeth read from the gate
  record; the declared nearest-rank median confirmed implemented **and** stamped into both
  tally outputs; `EXECUTION_APPROVED` and the ledger confirmed to make every campaign stage
  refuse. Then the missing work: the Phase A smoke executed, which executes **G4 with its
  teeth** — PASS, both directions, numbers in §3.2; `--verify` executed, found unable to
  fail, repaired and given teeth (`9e95bb05`); the missing `.gitignore` found and restored
  (`1e5eaf46`), and all cited gates re-run on the clean tree so their records carry an honest
  stamp. Three findings reported in §7, one of them (check 1's construction) left for
  orchestrator adjudication rather than repaired. Not merged; nothing pushed.
- 2026-09-04 (same resumption, later) — **A40 (v3-prime) observed merged to
  `architecture_surgery`** (`1f176950` … `fa5cec0e`) while this task was open. Nothing on this
  branch changes: the prime does not exist on a tree off `b7dbd2a9`, so the harness's refusals
  are correct here. §7 finding 4 rewritten to name **both** ledger flips owed at A41's merge
  (`prime` and `exit_forensics`) rather than only `exit_forensics`.

## Orchestrator assessment (pre-merge, 2026-09-04)

**Verified independently.** The verbatim-copy claim was re-checked by diffing all six files
in `913b89f0` against `git show b7dbd2a9:…` — the V2 files **as they stood at this branch
point**: **+4 provenance lines, 0 removals, on every one of the six**. (A first attempt
compared against the V2 files as they stand *today* and appeared to show a 17-line
divergence in `v3_report_analysis.py`; that is session `f1`'s later additive change to the
V2 file, committed at `6f05f819` after this branch point, not a divergence in the copy.
The check was wrong, not the copy.) The `--mode smoke --verify` pass reproduces 11/11 cells
with 0 mismatches and 4/4 applied verifier teeth trip.

**Findings adjudicated.**

1. **check 1 diverged from the plan — the task was right to report it, and the plan wins.**
   `EXPERIMENT_PLAN.md` §4.2 declares a **per-pair relative** statistic
   r = |Δ `norm_objf`| / max(|objf|ₐ, |objf|ᵦ) with the plain 1e-6 relative floor (O3); the
   harness computed an **absolute** delta against a floor scaled by an ensemble median of
   |`norm_objf`|. These are different constructions, and normalising a per-pair statistic by
   an ensemble median is precisely the class of ambiguity this project spent the day
   correcting elsewhere. **Adjudicated for the plan** — it carries the pre-declared
   acceptance rule and the user's O3 resolution is explicitly a *relative* tolerance.
   Fixed in `10a2ff36`; the absolute delta is retained beside the relative one, published
   but never accepted against. **This change is the orchestrator's, not the task agent's**,
   and is verified two ways: the arithmetic on representative values (identical → r = 0;
   1e-10 apart → passes; a real st attractor hop at 1.26e-2 → fails; and with V2's
   machine-noise yardstick of 3.3e-15 the floor dominates the bound, which is exactly what
   O3 exists to fix), and the harness's own verifier and teeth re-run clean afterwards.
2. **check 2 owed the plan's iteration totals.** The `EXPERIMENT_PLAN` amendment requiring
   summed iterations beside every median was committed *after* this branch point, so the
   harness could not have carried it. Added (orchestrator, same commit series): arm sums,
   sum ratio, per-arm iteration medians, the contributing seed list, and a
   `sum_vs_median_directions_agree` flag. Validated against V2's real lad numbers — it
   returns **False** for B0→B1 (median 0.833 against sum ratio 1.009, the case that
   prompted the amendment) and **True** for B0→B3.
3. **The missing `.gitignore` was a genuine defect, found and repaired by the task**: V3's
   directory lacked V2's `runs/` ignore, so `git status --porcelain` was never clean and
   **every V3 record stamped `tree_git_dirty: true`**. Repaired at `1e5eaf46` and all cited
   gates re-run clean. This is exactly the provenance-hygiene failure the project's
   clean-stamp discipline exists to catch, caught before any campaign number existed.
4. **`--verify` could not fail, and the task gave it teeth.** It read only
   `runs/*/campaign/**`, which cannot exist pre-approval, so it reported "0 cells checked,
   0 mismatches" and exited 0 — a green light over an empty population (trap T11). The task
   added `--mode smoke` and its own `--teeth`, and honestly reports the one Phase B tooth
   as "not applied" rather than counting it as passing.
5. **G4 had been implemented but never executed** at the interruption; the task executed it
   and it PASSes in both directions with 7/7 and 3/3 binding checks.
6. **The ledger owes two flips at merge, not one** (`prime` from A40, which merged while
   this task ran, and `exit_forensics`), correctly left unflipped here — a ledger claiming
   an instrument the branch lacks is the silent-wrong-arm failure the refusals prevent.
   Recorded as owed to A42's preflight.

**Merge approved.**
