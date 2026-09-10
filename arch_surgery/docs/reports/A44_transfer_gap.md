# A44 (transfer-gap) — why Phase A's per-call ratio does not predict Phase B's end-to-end ratio

> **Document status** — **OPEN TASK REPORT, complete, awaiting the orchestrator's assessment (protocol §5).** Task A44 (transfer-gap), branch
> `A44-transfer-gap` off `architecture_surgery` at `16a6e87e`. Investigates queue issue I-17.
> Every number below is produced by a stage of
> [`arch_surgery/idf_probe/a44_transfer_gap.py`](../../idf_probe/a44_transfer_gap.py); the
> commit each stage ran at is given in §9. Archived to `deprecated/` at merge (protocol §7);
> read this header, not the folder (trap T3).

| | |
|---|---|
| **Question** | The V3 experiment measured the partitioned architecture twice: **Phase A** as the cost of one evaluation of the coupled models from a perturbed state, with no optimiser, and **Phase B** as the cost of whole optimisations. The plan's *transfer argument* said the two should agree: end-to-end saving ≈ Phase A's per-call saving × an unchanged number of optimiser iterations. Measured, they do not (I-17). What exactly stands between them, and can V4's method be changed so they agree? |
| **Verdict, in one line** | The gap factorises exactly into two terms that the transfer argument never carried: an **evaluation-count** term, which is what Phase B's check 2 (iterations) cannot see, and a **per-evaluation** term, which is uniform in sign on every config and is the regime mismatch the original I-17 hypothesis named. **The preliminary experiment confirms the mechanism on all three configs**: a Phase A evaluation entered at a design-variable step of the optimiser's own size reproduces the in-loop cost per evaluation, the sweep counts and the per-evaluation ratio (within 0.003 of the in-loop value); with Phase A measured there and the multiplier carried in evaluations, the transfer closes to **+0.5 % / −0.3 % / +0.4 %** (nof / lad / st) from +22.6 % / −20.7 % / +6.3 %. A smaller coupling-state perturbation (V4 item 1a's δ = 0.001) does **not** do this. **Third structural result:** on both pulsed configs B1, B2 and B3 have identical evaluation and iteration counts on every converged seed — the partition and the trust step are invisible to the optimiser's trajectory; only the lift moves it. |
| **Report-level finding** | `low_aspect_ratio_DEMO`'s published headline B3/B0 = **0.450** (V3 report §5.5, n = 11) carries one seed on which the flat baseline **failed its first VMCON attempt after 100 iterations and converged on a retry**; the cost of the failed attempt is inside the node-call sum, but check 2 records only the 16 iterations of the retry. Over the ten seeds with no retry in either arm, lad's B3/B0 is **0.659**. Both readings are published here; which one V4 reports is a decision for V4 item 5b, not for this task. |
| **What is not threatened** | Nothing in Phase A. The B3/B0 sign on every config (the block arm executes fewer model-node evaluations end to end). The V3 conclusion that the partition's per-call ratio must not be read as an end-to-end prediction — that stands, and now has a mechanism. |
| **Recommendation for V4** | Worth doing, and small (§7): a stencil-regime entry set in Phase A beside δ = 0.10 (not a second δ amplitude); the A0p arm (item 1c); check 2 in evaluations with per-attempt node calls and both retry readings (item 5b); the transfer restated as ρ_A(stencil) × the evaluation multiplier, expected residual ≤ 5 %. |

---

## 1. What the transfer argument expected

Phase A evaluates the coupled models **once** from a displaced state — every continuous coupling
component multiplied by `1 + δu`, δ = 0.10, seed-paired across arms — and counts the model-node
executions it takes to reach a self-consistent state at tolerance τ = 1e-6. The flat arrangement
(A0, every model in one loop) and the partitioned arrangement (A1: three blocks each solved on its
own, the pulse model hoisted, the burn time pinned, the FirstWall→Build prime) give two counts per
seed; their ratio over 25 seeds is the *per-call ratio* ρ_A:

| config | ρ_A = Σ A1 / Σ A0 (25 seeds) |
|---|---|
| `large_tokamak_nof` (nof) | 0.5217 |
| `low_aspect_ratio_DEMO` (lad) | 0.5680 |
| `st_regression` (st) | 0.5016 |

*Caption: Phase A's per-call ratio, ratio of the 25-seed sums of `node_calls_single_eval` (A1 over
A0), δ = 0.10 warm entries; the V3 report §6 construction, reproduced to four decimals by stage
`factorise`.*

Phase B runs whole optimisations from 25 perturbed starting points under the flat baseline (B0) and
the partitioned arrangement (B3, which also carries the burn-time *lift*: the burn time becomes a
design variable of the optimiser with a consistency constraint, instead of being solved inside the
loop). The transfer argument, V3 plan §5, says: if the optimiser takes the same number of
iterations in both arms (check 2), then

    end-to-end ratio  B3/B0  ≈  ρ_A  ×  (iteration ratio)  ≈  ρ_A .

Check 2 passed at an iteration ratio of 1.00 on every config. The measured end-to-end ratios were
0.640 / 0.450 / 0.533 against the predicted 0.522 / 0.568 / 0.502: an over-prediction of the
saving by +22.6 % on nof, an *under*-prediction by 20.7 % on lad, and +6.3 % on st. V3's own test
of the one hypothesis it had — that in-loop evaluations are shorter than Phase A's — found the
shortening real but cancelling between the arms, and left I-17 open.

## 2. The gap factorises exactly, and the identity is not the finding

Let N be an arm's model-node executions in the solve phase summed over the seeds on which both
arms converged (`node_calls_solve_phase`; the V3 report's cost statistic), and C the number of
`call_models` evaluations the optimiser made over the same seeds (`sweeps_per_eval.n_evaluations`,
asserted equal to the driver's own `module_solve_totals.n_call_models` on every record where the
module-solve driver was on). Then, for any two arms a → b,

    R = N_b / N_a  =  [ (N_b/C_b) / (N_a/C_a) ]  ×  [ C_b / C_a ]  =  ρ_B × ε

**by construction.** ρ_B is the in-loop per-evaluation ratio — the same quantity Phase A measures,
but on the evaluations the optimiser actually made — and ε is the ratio of evaluation counts. The
transfer argument assumes ρ_B = ρ_A and ε = 1. So the gap is

    R / ρ_A  =  (ρ_B / ρ_A)  ×  ε ,

also exactly. The identity says nothing on its own; the finding is **which factor carries the
config dependence**, and the answer is: ε carries all of it, and ρ_B/ρ_A is uniform.

*Caption: the factorisation per config over the identical-converged seed set (both B0 and B3
`status == ok` and MFILE `ifail == 1`). R is the published end-to-end ratio; ρ_A Phase A's per-call
ratio; ρ_B the in-loop per-evaluation ratio; ε the evaluation-count ratio, split into the
deterministic factor `(nvar_B3 + 1)/(nvar_B0 + 1)` from the size of the gradient stencil and the
remaining ratio of VMCON problem-calls. The last column is the gap the transfer argument left.
Stage `factorise` at `6ccffb81`; every R reproduces the V3 report's §5.5 sums as exact integers,
and the stage's teeth (a +1 on one record's node calls, a +1 on one record's evaluation count)
both trip.*

| config | n | R = N_B3/N_B0 | ρ_A | ρ_B | ρ_B/ρ_A | ε | ε: (nvar+1) factor | ε: problem-call factor | gap R/ρ_A |
|---|---|---|---|---|---|---|---|---|---|
| nof | 22 | 0.6395 | 0.5217 | 0.6142 | **1.177** | 1.041 | 1.048 | 0.994 | 1.226 |
| lad | 11 | 0.4504 | 0.5680 | 0.6162 | **1.085** | **0.731** | 1.050 | 0.696 | 0.793 |
| lad, no retry seed | 10 | 0.6594 | 0.5680 | 0.6190 | **1.090** | 1.065 | 1.050 | 1.014 | 1.161 |
| st | 22 | 0.5331 | 0.5016 | 0.5604 | **1.117** | 0.951 | 1.000 | 0.951 | 1.063 |
| st, no retry seed | 21 | 0.5439 | 0.5016 | 0.5632 | 1.123 | 0.966 | 1.000 | 0.966 | 1.084 |

Two things the table settles before any new run:

- **The per-evaluation term has one sign and nearly one size everywhere.** Inside the optimiser
  the block arm's evaluation costs 0.56–0.62 of the flat arm's, never the 0.50–0.57 Phase A
  measured. The uniform "systematic" error V2 saw, and V3 lost, is this term; V3 lost it because
  lad's evaluation-count term happened to swing the other way.
- **The evaluation-count term is where the configs differ, and check 2 cannot see it** (§3).

The once-per-run post-solve executions (three nodes on nof and lad, four on st, executed once at
the end of the solve phase in B2/B3) are inside N; carried separately they move ρ_B in the fourth
decimal (0.6142 → 0.6141 on nof). The output path's two flat sweeps per run are outside N in every
arm.

## 3. The evaluation-count term: three things the iteration count does not carry

**(a) Every VMCON problem evaluation costs 2(nvar + 1) `call_models` evaluations, and the lift adds
one design variable.** `evaluators.fcnvmc2` builds the gradient by *central* differences, one
forward and one backward evaluation per design variable, plus one reconciling evaluation at the
base point; with the function evaluation that is 2 + 2·nvar per problem-call. Stage `factorise`
checks this divisibility on every ok record of every arm and config: it holds without exception.
The burn-time lift raises nvar from 20 to 21 (nof) and 19 to 20 (lad), so B1, B2 and B3 pay
**(nvar+2)/(nvar+1) = +4.8 % / +5.0 %** more evaluations per problem-call than B0 at the same
iteration count. This is structural, exactly predictable, and absent from the transfer argument.
On st there is no lift and the factor is 1.

**(b) A retried optimisation keeps the failed attempt's evaluations in its cost and drops them from
its iteration count.** PROCESS's solver handler retries VMCON with `epsfcn` ×10, then ×0.1, then a
Hessian reset when the first attempt fails. Every evaluation of every attempt goes through
`call_models` and is counted in N and C; `n_solver_iterations` — check 2's statistic — is the
final attempt's. The records carry `n_solver_iterations_summed_over_attempts`, which nothing in
the V3 tally read.

*Caption: the retried runs inside each config's identical-converged set. Problem-calls are
C / 2(nvar+1) for the run; "iters" is check 2's statistic (final attempt); "summed" adds the failed
attempts. From stage `factorise`'s per-seed table.*

| config | seed | arm | attempts | ladder stage | problem-calls | iters | summed | the paired arm |
|---|---|---|---|---|---|---|---|---|
| lad | 1 | B0 | 2 | epsfcn ×10 | 231 | 16 | **116** | B3: 29 problem-calls, 15 iters |
| st | 2 | B0 | 2 | epsfcn ×10 | 96 | 21 | 48 | B3: 77, 39 |
| st | 1, 15 | B2 | 2 | epsfcn ×10 | 204, 230 | 38, 37 | 102, 115 | — (B2, A43's rung) |
| st | 2, 12, 24 | R | 2, 2, 3 | ×10, ×10, ×0.1 | 96, 132, 413 | 21, 15, 83 | 48, 66, 206 | (shipped anchor) |

On lad, seed 1's baseline cost is **7.5 times** what its iteration count suggests, and it is a
quarter of the whole 11-seed B0 sum. That is why lad's ε is 0.731 with the seed and 1.065 without,
and why the published lad headline is 0.450 with it and 0.659 without.

*Caption: the two retried seeds that sit inside a headline cost set, per arm and per VMCON attempt,
from each record's `exit_forensics.attempts` (attempt, ladder stage, `ifail`, iterations). Node
calls are recorded **per run only** — the records carry no per-attempt node-call count, which is the
harness gap §7 names — so the last column is the run total. `ifail` 1 = converged; 2 = VMCON's
line-search / iteration limit failure; 5 = its own convergence-failure code.*

| config | seed | arm | attempt 1 | attempt 2 | run: problem-calls | run: node calls (solve phase) |
|---|---|---|---|---|---|---|
| lad | 1 | R | initial, ifail 2, 100 iters | epsfcn ×10, ifail 1, 16 iters | 231 | 669 207 |
| lad | 1 | B0 | initial, ifail 2, 100 iters | epsfcn ×10, ifail 1, 16 iters | 231 | 655 473 |
| lad | 1 | B1 / B2 / B3 | initial, ifail 1, 15 iters | — | 29 | 81 228 / 73 302 / 52 834 |
| st | 2 | R, B0 | initial, ifail 5, 27 iters | epsfcn ×10, ifail 1, 21 iters | 96 | 210 168 / 218 820 |
| st | 2 | B2 / B3 | initial, ifail 1, 38 / 39 iters | — | 75 / 77 | 128 766 / 93 767 |

**Two readings, and the question each answers.** The accounting reading: check 2's
`n_solver_iterations` records the final attempt only while node calls record every attempt, so the
iteration multiplier says 1.01 where the evaluation multiplier says 0.70 — that mismatch is the
mechanism of lad's reversed sign, and it is a construction defect in the transfer, not in either
arm. The robustness reading: at lad seed 1 **both flat arms failed their first attempt and the
partitioned arm did not**: B0 made 9 240 evaluations at that start against B3's 1 218, and the
difference is genuine cost that B3 avoided — a robustness event, which belongs in the cost story on its own line and must be neither
pooled into a per-evaluation ratio nor deleted from the campaign total. So: **0.659 answers "what
does a converged optimisation cost when both arms converge at the first attempt"**, and **0.450
answers "what did the campaign cost, including the flat arm's failed attempt"**. V4 item 5b's filter
must be able to express both, and the harness change that makes that possible is one field:
node calls recorded **per VMCON attempt**, so a retry can be carried as a term rather than found
afterwards by subtraction.

**Proposed erratum note for V3 report §5.5, for the user to accept verbatim or amend:** *"Erratum
(A44, 2026-09-10): the `low_aspect_ratio_DEMO` converged-set ratio B3/B0 = 0.450 (n = 11) includes
seed 1, on which R and B0 failed their first VMCON attempt (ifail 2 after 100 iterations) and
converged on the epsfcn ×10 retry; the failed attempt's evaluations are in the node-call sum and not
in check 2's iteration count. Over the ten seeds with no retry in either arm the ratio is 0.659. Both
readings are valid answers to different questions and are published side by side in A44's report;
the campaign-level figure stands as the cost including the flat arm's failed attempt."*

**The uniform sign is restored.** V3 report §6 wrote: *"The uniform sign is gone. tok reproduces its
V2 over-prediction to the decimal; st's shrinks from +41.8 % to +6.3 %; and lad reverses — Phase A
now under-predicts by 20 %. Whatever V2's 'systematic' transfer error was, it is not systematic in
V3."* With the retry carried as its own term, the gap is **+22.6 % / +16.1 % / +6.3 %** (nof /
lad-without-seed-1 / st, table in §2): one sign on every config. The "not systematic" reading was
itself the retry-accounting artefact on lad, and I-17's original characterisation — a systematic
over-prediction with a per-evaluation mechanism — stands.

**(c) The optimiser's trajectory changes at the lift, and on st at the partition — never at the
block/trust rungs on the pulsed configs.** Per seed:

- On **both pulsed configs, B1, B2 and B3 have identical evaluation and iteration counts on every
  converged seed** (22/22 on nof, 11/11 on lad). The partition and the trust step are invisible to
  the optimiser there: ε = 1.000 exactly on B1→B2, B2→B3 and B1→B3, and their end-to-end ratios
  *are* their per-evaluation ratios (nof B1→B3 = 0.635; lad 0.651).
- The **lift** moves the trajectory: on nof, 5 of 22 seeds change their problem-call count at
  B0→B1 (net factor 0.994); on lad every seed does (net 1.014 without the retry seed).
- On **st**, which has no lift, problem-calls differ B0→B2 on seeds 1, 2, 9, 12, 15, 16, 19, 24 and
  B2→B3 on 1, 2, 9, 15, 19, 24 (six of the eight at both rungs). The B2→B3 half is task A43's
  question and is not traced here; the split is published so the two tasks reconcile.

## 4. The per-evaluation term: why V3 §6 missed it, and the hypothesis it leaves

V3 §6 tested the "shorter evaluation" hypothesis in **sweeps**: Phase A's flat evaluation takes
1.68× the sweeps of an in-loop one and the block evaluation 1.58×, so the asymmetry predicted only
+6 % on nof. But a block sweep is not a unit of cost. The block arm's sweeps are sweeps of one block
each, and the blocks are unequal: 2 executing nodes (M1: plasma geometry and physics), 3 (M2: build,
TF coil, PF coil) and 12 (M3: everything downstream) on every config, plus the hoisted pulse model
once per evaluation on the pulsed configs.

*Caption: sweeps per evaluation by block, Phase A (25 δ = 0.10 entries) against in-loop Phase B
(identical-converged set), and the resulting nodes executed per block sweep. Executing-node counts
per block from the B3 census (`_executing_nodes_per_block`); in-loop per-evaluation figures use
N − P. Stage `factorise`.*

| config | where | M1 (2 nodes) | M2 (3) | M3 (12) | block sweeps / eval | nodes / block sweep | flat sweeps / eval |
|---|---|---|---|---|---|---|---|
| nof | Phase A, δ = 0.10 | 4.00 | 5.16 | 3.00 | 13.16 | 4.60 | 5.52 |
| nof | in-loop | 2.17 | 2.75 | 2.41 | 8.33 | 5.10 | 3.29 |
| lad | Phase A, δ = 0.10 | 4.00 | 4.88 | 3.00 | 12.88 | 4.63 | 5.00 |
| lad | in-loop | 2.14 | 2.72 | 2.49 | 8.35 | 5.19 | 3.35 |
| st | Phase A, δ = 0.10 | 4.00 | 5.84 | 3.00 | 14.84 | 4.15 | 5.84 |
| st | in-loop | 2.31 | 2.40 | 2.36 | 9.07 | 4.43 | 3.41 |

Phase A's extra block sweeps land in the **small** blocks — M2 takes 5 sweeps from a δ = 0.10
displacement while the 12-node M3 needs 3 — so a Phase A block sweep is cheap (4.1–4.6 nodes) and
an in-loop one dearer (4.4–5.2). In node calls the shortening is 1.68 / 1.49 / 1.71 for the flat
arm against **1.42 / 1.38 / 1.53** for the block arm, and the asymmetry is +18 % / +9 % / +12 % —
the ρ_B/ρ_A column of §2, exactly. Redone in the cost unit, the original I-17 hypothesis accounts
for the per-evaluation term arithmetically. What it does not yet establish is the **mechanism**: that
the per-evaluation ratio is a function of how far the entry state is from the fixed point, such
that a Phase A evaluation made at an entry of the optimiser's own size would reproduce ρ_B. That is
the preliminary experiment.

**Leading hypothesis (regime mismatch).** Phase A enters from a state displaced by 10 % in every
coupling component; the optimiser's evaluations enter from the previous evaluation's fixed point
with one design variable moved by `epsfcn` = 1e-3 (41 of every 42 evaluations are gradient-stencil
points). Near the fixed point both arms sit close to the two-sweep floor of the idempotence
predicate, and the block arm's advantage — which comes from M3 converging in fewer sweeps than the
flat loop — shrinks toward the floor ratio (2 sweeps × 17 in-loop block nodes + 1 hoisted, over
2 × 21 flat nodes: 0.83). Far from the fixed point the flat loop needs many sweeps and M3 does not,
and the ratio falls to 0.5.

**Pre-declared prediction and refutation** (stage `regime`'s docstring, committed before it ran): at
an entry of stencil size the ratio A1/A0 moves from ρ_A(0.10) toward ρ_B, and A1/A0p (A0p = flat +
lift + pin, V4 item 1c, so that A0p→A1 is the same switch set as B1→B3, where ε = 1 exactly) toward
the in-loop B3/B1 ratio (0.635 / 0.651). **Supported** if the stencil-regime ratio is closer to ρ_B
than to ρ_A(0.10) and above ρ_A(0.10); **refuted** if it is at or below ρ_A(0.10) + 0.02;
indeterminate otherwise. The orchestrator's caution is carried: at stencil size the flat arm's own
sweep count also drops toward its floor, so the movement is not guaranteed by the mechanism — that
is what the probe measures.

## 5. Gates before the probe

*Caption: stage `prepare`'s identity gates. The A0 reference at each config's deck point is re-run
under this tree and compared with V3's frozen reference; then seed 1 at δ = 0.10 for A0 and A1 is
re-run through the copied runner (`a44_eval_one.py`, new option unset) and compared with V3's
seed-1 records. Cells: node calls, sweeps, per-block sweeps, exit-audit maxima (hex), burn time
(hex), objective (hex), prime calls; the reference also compares the whole 840/846/827-component
exit state. Teeth: the same comparator against a different record must fail.*

| config | reference vs V3 (8 cells + exit state) | seed 1 A0 vs V3 (8 cells) | seed 1 A1 vs V3 (8 cells + pin) | teeth | verdict |
|---|---|---|---|---|---|
| nof | all equal, 840/840 components | all equal | all equal | fail as required | PASS |
| lad | all equal, 846/846 | all equal | all equal | fail as required | PASS |
| st | all equal, 827/827 | all equal | all equal | fail as required | PASS |

So the tree in this worktree, imported through `PYTHONPATH` with `process.__file__` asserted
against it (trap T6), reproduces the V3 instrument exactly, and the runner extension is inert when
unused.

## 6. The preliminary experiment: the per-call ratio across entry regimes

### 6.1 What ran

Stage `regime`, 472 single-evaluation runs, **472 ok, 0 failed, none retried**: nof 125 + 62,
lad 122 + 59, st 70 + 28 (E0/E2/E3 + E3b). Arms A0, A0p and A1 on the pulsed configs; A0 and A1 on
st, where A0p composes to A0 and is recorded as skipped. Every run is a fresh subprocess under
`PROCESS_surgery_env` with `PYTHONPATH` pinned to this worktree and `process.__file__` asserted
against it; the runner is `a44_eval_one.py` at `6ccffb81` throughout, and the tally checks that no
commit after that touched `process/`, the runner, the committed data artifacts or the scenarios
(`measuring_code_unchanged_across_probe: true`). The stage script itself was edited and committed
while the probe ran (factorise and tally stages only), so the records stamp four different heads;
they also stamp `tree_git_dirty = True` for most of the probe, because the runner's stamp counts
untracked files and the draft of this report was untracked beside it. Both facts are recorded in
`tally.json` under `probe_provenance`.

### 6.2 Cost per evaluation by regime

*Caption: mean model-node executions and dispatch sweeps per single evaluation, per config, regime
and arm, against the in-loop values from Phase B (identical-converged set, N − P over C).
Regimes: **V3_d0.1** the V3 campaign's 25 δ = 0.10 entries (frozen records); **E0** the reference
fixed point re-entered unperturbed; **E2** the same δ-stream at δ = 0.01 and 0.001, seeds 1–10;
**E3** the gradient stencil's forward points, one per design variable (plus the lifted column on the
pinned arms), coupling state at the reference fixed point; **E3b** the stencil's backward points
entered from the forward point's fixed point (the 2 ε step `fcnvmc2` actually takes). n is the
number of A1 entries. "A1 blocks" is sweeps per evaluation in M1/M2/M3. **A1/A0 and A1/A0p are
ratios of the per-evaluation means** — the construction that matches ρ_B, in which the lifted
arm's mean includes its extra stencil column and the column count is ε's business; where the two
arms have different entry counts the ratio of column sums is given in brackets and is larger by
exactly that column-count factor. In-loop rows: B0 / B1 / B3 per-evaluation means and the ratios
ρ_B (B3/B0) and B3/B1. Stage `tally` at `be075584`.*

| config | regime | n | A0 calls/eval | A0 sweeps | A0p calls/eval | A1 calls/eval | A1 sweeps | A1 blocks (M1/M2/M3) | A1/A0 | A1/A0p |
|---|---|---|---|---|---|---|---|---|---|---|
| nof | V3_d0.1 | 25 | 115.92 | 5.52 | — | 60.48 | 13.16 | 4.00/5.16/3.00 | 0.5217 | — |
| nof | E0 | 1 | 21.00 | 1.00 | 21.00 | 18.00 | 4.00 | 1.00/1.00/1.00 | 0.8571 | 0.8571 |
| nof | E2_d0.01 | 10 | 109.20 | 5.20 | 105.00 | 60.00 | 13.00 | 4.00/5.00/3.00 | 0.5495 | 0.5714 |
| nof | E2_d0.001 | 10 | 105.00 | 5.00 | 94.50 | 56.50 | 11.50 | 3.00/4.50/3.00 | 0.5381 | 0.5979 |
| nof | E3 | 21 | 66.15 | 3.15 | 62.00 | 38.81 | 7.52 | 1.90/2.38/2.24 | 0.5867 | 0.6260 | (entries A0 20 / A1 21; ratio of sums 0.6160)
| nof | E3b | 21 | 66.15 | 3.15 | 62.00 | 40.43 | 7.86 | 2.14/2.38/2.33 | 0.6112 | 0.6521 | (entries A0 20 / A1 21; ratio of sums 0.6417)
| nof | **in-loop (V3 Phase B)** | — | 69.16 | 3.29 | 66.94 | 42.48 | 8.33 | 2.17/2.75/2.41 | **0.6142** | **0.6345** |
| lad | V3_d0.1 | 25 | 105.00 | 5.00 | — | 59.64 | 12.88 | 4.00/4.88/3.00 | 0.5680 | — |
| lad | E0 | 1 | 21.00 | 1.00 | 21.00 | 18.00 | 4.00 | 1.00/1.00/1.00 | 0.8571 | 0.8571 |
| lad | E2_d0.01 | 10 | 105.00 | 5.00 | 84.00 | 57.00 | 12.00 | 4.00/4.00/3.00 | 0.5429 | 0.6786 |
| lad | E2_d0.001 | 10 | 105.00 | 5.00 | 84.00 | 55.00 | 11.00 | 3.00/4.00/3.00 | 0.5238 | 0.6548 |
| lad | E3 | 20 | 66.32 | 3.16 | 61.95 | 39.90 | 7.55 | 1.90/2.30/2.35 | 0.6017 | 0.6441 | (entries A0 19 / A1 20; ratio of sums 0.6333)
| lad | E3b | 20 | 68.53 | 3.26 | 63.00 | 42.35 | 8.00 | 2.15/2.35/2.50 | 0.6180 | 0.6722 | (entries A0 19 / A1 20; ratio of sums 0.6505)
| lad | **in-loop (V3 Phase B)** | — | 70.35 | 3.35 | 66.59 | 43.35 | 8.35 | 2.14/2.72/2.49 | **0.6162** | **0.6510** |
| st | V3_d0.1 | 25 | 122.64 | 5.84 | — | 61.52 | 14.84 | 4.00/5.84/3.00 | 0.5016 | — |
| st | E0 | 1 | 21.00 | 1.00 | — | 17.00 | 5.00 | 1.00/1.00/1.00 | 0.8095 | — |
| st | E2_d0.01 | 10 | 102.90 | 4.90 | — | 58.70 | 13.90 | 4.00/4.90/3.00 | 0.5705 | — |
| st | E2_d0.001 | 10 | 96.60 | 4.60 | — | 57.80 | 13.60 | 4.00/4.60/3.00 | 0.5983 | — |
| st | E3 | 14 | 67.50 | 3.21 | — | 38.93 | 8.64 | 2.21/2.07/2.36 | 0.5767 | — |
| st | E3b | 14 | 70.50 | 3.36 | — | 39.36 | 8.79 | 2.21/2.21/2.36 | 0.5583 | — |
| st | **in-loop (V3 Phase B)** | — | 71.65 | 3.41 | — | 40.15 | 9.07 | 2.31/2.40/2.36 | **0.5604** | — |

**The floor (E0).** Re-entered at its own fixed point, the flat loop takes **one** sweep (21
calls) and the block arm one sweep per block plus the hoisted node (18 / 18 / 17 calls): the
idempotence predicate's floor is a single sweep when nothing moves, and the floor ratio is 0.86 /
0.86 / 0.81. Every regime sits between the floor and Phase A's δ = 0.10.

**A smaller coupling-state perturbation is not an in-loop entry (E2).** At δ = 0.001 the flat arm
still needs **5.0 sweeps on nof and lad** (105 calls; 4.6 on st) against the 3.2–3.4 an in-loop
evaluation takes, and the block arm 11–13.6 against 8.3–9.1; M2 still takes 4–4.5 sweeps from a
0.1 % displacement. The ratio moves the **wrong way** on nof and lad (0.522 → 0.550 → 0.538;
0.568 → 0.543 → 0.524) and only on st toward the in-loop value, and it is non-monotone on two of
three configs. Sweep counts are roughly logarithmic in amplitude, so two decades of δ buy about one
sweep in each arm, never the three the stencil regime needs; what governs the count is *which*
components are displaced. The δ-stream displaces every continuous component at once, run-constants
and post-solve-owned outputs included (V3 plan §3.2's disclosure), and that is a different object
from a design-variable step at any amplitude. **This is a measured negative for V4 list item 1a's
specific proposal** — a second amplitude at δ = 0.001 as the representativeness probe — while
confirming its "do not reduce the first" half by another route: δ = 0.10 is the only regime in
which the small blocks do enough work for the carrier to show.

**A design-variable step of the optimiser's own size is an in-loop entry (E3, E3b).** At the
stencil regime every arm's cost per evaluation lands within 1–7 % of its in-loop value — flat
66.2–70.5 against 69.2–71.7, A0p 62.0–63.0 against B1's 66.6–66.9, block 38.8–42.4 against
40.2–43.4 — with the sweep counts (flat 3.15–3.36 vs 3.29–3.41; block 7.5–8.8 vs 8.3–9.1) and the
per-block composition reproduced. The in-loop value lies between E3 (one coordinate moved by ε from
the fixed point) and E3b (moved by 2 ε from the forward point's fixed point), as the stencil's own
step sequence predicts, and closer to E3b. **A1/A0 at E3b is within 0.003 of ρ_B on every config**
(0.611 / 0.618 / 0.558 against 0.614 / 0.616 / 0.560); **A1/A0p is within 0.02 of the in-loop
B3/B1** on both pulsed configs (0.652 / 0.672 against 0.635 / 0.651), which is the one rung where
the evaluation count is identical seed for seed, so its end-to-end ratio *is* its per-evaluation
ratio.

**Verdict under the pre-declared rule: SUPPORTED on all three configs**, on both E3b (declared)
and E3, and on both ratio constructions. Distance of the E3b ratio from ρ_B: −0.003 / +0.002 /
−0.002; from ρ_A(0.10): +0.09 / +0.05 / +0.06.

### 6.3 The transfer, closed

*Caption: the end-to-end ratio predicted as ρ_A × ε — Phase A's per-call ratio at each regime times
the evaluation multiplier ε = [(nvar_B3+1)/(nvar_B0+1)] × [problem-call ratio] from §2 — against the
measured R, with the error as measured/predicted − 1 (positive = the prediction promised more
saving than delivered). lad is shown with and without its retried seed; st likewise. Stage `tally`
at `be075584`.*

| config | set | R measured | eps | rho_A(0.10) x eps | error | rho_A(E3) x eps | error | rho_A(E3b) x eps | error |
|---|---|---|---|---|---|---|---|---|---|
| nof | with_retried | 0.6395 | 1.0411 | 0.5432 | +17.7 % | 0.6108 | +4.7 % | 0.6363 | +0.5 % |
| lad | with_retried | 0.4504 | 0.7309 | 0.4152 | +8.5 % | 0.4398 | +2.4 % | 0.4517 | -0.3 % |
| lad | without_retried | 0.6594 | 1.0652 | 0.6050 | +9.0 % | 0.6409 | +2.9 % | 0.6583 | +0.2 % |
| st | with_retried | 0.5331 | 0.9512 | 0.4771 | +11.7 % | 0.5485 | -2.8 % | 0.5310 | +0.4 % |
| st | without_retried | 0.5439 | 0.9656 | 0.4844 | +12.3 % | 0.5569 | -2.3 % | 0.5391 | +0.9 % |

With Phase A measured at the stencil regime and the multiplier carried in evaluations rather than
iterations, the transfer closes to **+0.5 % / −0.3 % / +0.4 %** (E3b) with E3 bracketing it at
+4.7 % / +2.4 % / −2.8 %, from the +17.7 % / +8.5 % / +11.7 % the δ = 0.10 ratio leaves even after ε
is applied — and from the +22.6 % / −20.7 % / +6.3 % the transfer argument as written leaves. lad
without its retried seed closes to +0.2 %.

### 6.4 What the residual is, and what this probe cannot see

The ±5 % bracket between E3 and E3b is the probe's resolution, and three named things sit inside it:

- **Two of every 2(nvar+1) in-loop evaluations are not stencil points** — the base evaluation
  after a line-search step and the reconciling evaluation — and the line-search step is larger
  than ε. The probe does not mimic them; they are 4.5 % (nvar = 20) to 6.7 % (nvar = 14) of
  evaluations.
- **In-loop each arm enters from its own previous exit.** B3 enters from a trust-mode exit, which
  need not be a joint fixed point (task A43's question on st); the probe enters both arms from the
  flat arm's fixed point, so the pairing is exact but the block arm's entry is slightly kinder than
  in-loop.
- **The problem-call factor** (0.994 / 1.014 / 0.951–0.966) is a Phase B measurement of the
  optimiser's trajectory, not a Phase A quantity; the transfer carries it, it cannot predict it.

Everything the transfer left unexplained on the pulsed configs is now attributed: the
per-evaluation term to the entry regime, measured; the evaluation-count term to the lift's extra
stencil column, exact, and to retries, recorded. On st the evaluation-count term is the partition
changing the optimiser's path on eight of 22 seeds, four of them clean of any retry at the B2→B3
rung; that is A43's subject and is not explained here.

## 7. What this means for V4

**Is it worth changing the method so the phases transfer? Yes — the change is small and it closes
the gap from 6–23 % to about 1 %, bracketed at 5 %.** Concretely, in the order of cost:

1. **Phase A gains a stencil-regime entry set beside δ = 0.10.** Per arm and config: the nvar
   forward stencil points from the reference fixed point (plus the lifted column on the pinned
   arms) and the backward points from the forward exits — deterministic, no seeds, 2(nvar+1)
   single evaluations, of order a minute of PROCESS time per config. The δ = 0.10 stream stays as
   the carrier/prime detector (**item 1a's "do not reduce" half stands**); **item 1a's second
   amplitude should not be adopted as the representativeness probe** — measured here, δ = 0.001
   moves the ratio the wrong way on two configs (§6.2). The representative regime is a
   design-variable step, not a smaller coupling-state perturbation.
2. **Add A0p** (item 1c: flat + lift + pin, frozen deck, no hoist). It composes as the orchestrator
   verified, and A0p→A1 at the stencil regime lands within 0.02 of B1→B3, the rung on which the
   optimiser's evaluation count is identical seed for seed. That is the one-rung transfer test the
   V3 lattice lacked.
3. **Check 2 in evaluations, beside iterations.** The multiplier the transfer needs is the
   `call_models` count over all attempts, and it decomposes into a pre-declarable structural
   factor — the lift's (nvar+2)/(nvar+1) from the central-difference stencil — and a measured
   problem-call factor. **Node calls recorded per VMCON attempt**, retried seeds flagged in the
   failure table, and every cost ratio published with and without them (item 5b's filter must be
   able to express both readings of §3). Pre-declared expectation for the pulsed configs:
   **B1→B2→B3 leaves the evaluation count unchanged** (V3: exactly so on 33 of 33 converged
   seeds); any departure is a finding, not noise.
4. **The transfer, restated for the V4 plan's §5:**
   B3/B0 ≈ ρ_A(stencil) × [(nvar_B3+1)/(nvar_B0+1)] × (problem-call ratio), with E3/E3b as the
   published bracket, ρ_A(stencil) the ratio of per-evaluation means, and the problem-call ratio a
   Phase B measurement expected near 1 absent retries and lift-induced trajectory change. Expected
   residual after the change: ≤ 5 %, measured here at ≤ 1 % on E3b.
5. **What Phase A still cannot predict, and should say so:** the optimiser's response to the lift
   (lad: every seed's trajectory changes at B0→B1) and to the partition on st. Those are Phase B
   results in their own right. The transfer is of the per-evaluation term only.

**If V4 keeps V3's method unchanged**, the residual difference is now explained rather than open:
Phase A at δ = 0.10 measures the block arm's saving in the regime where the flat loop does the most
work and the small blocks the least, and that saving is an upper bound the optimiser never
realises because 41 of every 42 of its evaluations are stencil points near the fixed point.

**Scope, as limits.** One reference point per config (the deck point; Phase B's perturbed starts
were not probed); entries of stencil size only; both arms entered from the flat fixed point; n = nvar
entries per arm; st's B2→B3 trajectory changes untouched; no timing anywhere.

## 8. Autonomous decisions, each with its reversal

1. **The probe is a diagnostic, not a campaign change.** It runs single evaluations at four
   regimes (the reference fixed point re-entered; the V3 δ-stream at 0.01 and 0.001, ten seeds;
   the gradient stencil's forward points; the stencil's backward points entered from the forward
   point's fixed point) and never touches the V3 directory or its records. Reversal: delete
   `runs/a44/` and the two `a44_` scripts; nothing else changed.
2. **The stencil-point entry was added to a copy of the Phase A runner, not to the runner.**
   `a44_eval_one.py` is `v2_eval_one.py` verbatim (commit `e2f84ea0`) plus one option (commit
   `6ccffb81`), gated inert-when-unused by §5. Reversal: V4 either adopts the option into
   `v2_eval_one.py` or discards the copy.
3. **A0p was composed from the driver's existing switches** (`flat_state` + `LIFT=burn_time` +
   `PIN_BURN_TIME`, frozen deck, no hoist, no post-solve, no prime), as V4 item 1c specifies and as
   the orchestrator verified composes legally; on st it composes to A0 and is recorded as skipped.
   Reversal: none needed; it is a probe arm.
4. **Retry accounting is published as two readings, not resolved.** Both are in the summary JSON.
   Reversal: V4 item 5b decides.
5. **st's B2→B3 rung is not traced here.** Its seed split is published for A43, per rung and with
   retry-contaminated seeds flagged (orchestrator's request).
6. **The probe's ratio construction was corrected before the report and both are published.** The
   tally first computed A1/A0 as a ratio of column sums; on the pulsed configs the pinned arms have
   one more stencil entry than A0 (the lifted column), so that construction counts the lift's
   column factor twice — once in the ratio and once in ε. The declared analogue of ρ_B is the ratio
   of per-evaluation means; the verdict is SUPPORTED under both, and the sums are printed beside
   wherever the entry counts differ. Reversal: none; both numbers are in `tally.json`.
7. **The stage script was edited and committed while the probe ran** (the st rung split and the
   tally's provenance and closure blocks; commits `8bf24711`, `6aeaeece`, `c256bc39`, `238520b1`,
   `f2fde775`, `be075584`). The running stage had loaded the script before any edit; the runner,
   `process/`, the data artifacts and the scenarios did not change after `6ccffb81`, which the tally
   checks and records. The probe's records therefore stamp four heads, all with identical measuring
   code. Reversal: re-run `regime` at `be075584` (about 25 minutes at three workers); the resume
   logic would skip every complete record, so delete `runs/a44/*/E*` first.

## 9. Provenance and reproduction

| stage | what it produces | commit run at | output |
|---|---|---|---|
| `factorise` | §2–§4 tables; identity with the published sums; teeth | `be075584` (first run `6ccffb81`; numbers unchanged) | `runs/a44/factorisation.json`, `.md` |
| `prepare` | §5 gates | `127e3d8f` (runner `6ccffb81`) | `runs/a44/prepare.json` |
| `regime` | the probe's 472 run records | launched at `127e3d8f`; runner `6ccffb81` throughout; record heads `127e3d8f`/`8bf24711`/`6aeaeece`/`6ccffb81` (§8 item 7) | `runs/a44/<config>/E*/` |
| `tally` | §6 tables, verdicts, closure, probe provenance, committed summary | `be075584` | `runs/a44/tally.json`, `.md`; [`docs/data/a44_transfer_gap_summary.json`](../data/a44_transfer_gap_summary.json) |

Reproduce with, from this tree under `PROCESS_surgery_env`:

```
python arch_surgery/idf_probe/a44_transfer_gap.py all --workers 3
```

The V3 records are read from the main checkout's untracked
`arch_surgery/MDA_partitioning_experiment_v3/runs/` and never written.

## 10. Change log (append-only)

- 2026-09-10 — task minted (provisional, orchestrator) from the user's investigative brief;
  factorisation from the V3 records; runner copy and extension; gates PASS on three configs;
  probe launched. Report drafted through §5.
- 2026-09-10 — orchestrator review points folded in: identity stated as such; both retry readings
  with the question each answers and the per-attempt table; proposed erratum sentence for V3 §5.5;
  uniform sign restored and cited against V3 §6; B1 = B2 = B3 in the verdict; the 2(nvar+1)
  identity with its tooth; st rung split per rung with retry contamination flagged.
- 2026-09-10 — probe complete (472/472 ok), tally at `be075584`: SUPPORTED on all three configs;
  transfer closed to ≤ 1 % at E3b; §6–§7 written; ratio construction corrected (§8 item 6). Report
  complete, awaiting assessment.
