# A32 (tail-confirm) — the confirming campaign cannot run: the committed driver refuses the a26-mode spec

> **Document status** — **CURRENT · TASK REPORT, open.** Written by task A32 (tail-confirm),
> 2026-09-03, on branch `A32-tail-confirm`, branched from `architecture_surgery` at `6b292a2a`.
> Archived to `deprecated/` when the task merges and authoritative there (trap T3). Nothing
> here is merged; nothing is pushed; no file under `process/` was touched.

| | |
|---|---|
| **Task** | A32 (tail-confirm) — run `st_regression` `A1'` across all 25 starts under the committed a26-mode coupling-state spec (`ystate_a26_st_regression.json`) and confirm end-to-end that A28's recurring 3+-pass tail (2 802 of 54 480 calls) dissolves, as A31 derived; plus the three heaviest `A0'` starts |
| **Result** | **BLOCKED — stop-and-report, per the brief's own clause.** The committed driver cannot load an a26-mode artifact at all: the campaign's first run refuses at spec load with **zero models evaluated**. Lifting the blocker requires a change under `process/`, which this task was forbidden to make ("no process/ change of any kind … if you find you do, stop and report") |
| **Script** | [`arch_surgery/idf_probe/a32_tail_confirm.py`](../../idf_probe/a32_tail_confirm.py) — every number below regenerates from its stages (`gate`, `preflight`); committed at `e8915f40`, and both stages re-executed on that clean tree (every run's `metrics.json` stamps `tree_git_head e8915f40, dirty False` — the audit-trail discipline A30 flagged and A31 adopted) |
| **Runs** | 2 fresh-subprocess PROCESS solves attempted in this worktree: 1 A18-mode gate run (completed, bit-exact against A28), 1 a26-mode campaign-first-run attempt (refused at spec load). 2 further `load_spec`-only subprocesses (A18 control, a26). **0 of 25** `A1'` campaign runs, **0 of 3** `A0'` runs |
| **Date** | 2026-09-03 |

---

## 1. Verdict

**Does the tail vanish: not measured — neither confirmed nor refuted.** A28's recorded
2 802 of 54 480 `A1'` calls at 3+ passes stands as the only measured side; the a26-spec
side of the comparison produced no number because no a26-spec run can start on the
committed driver. There is no per-start table, no outer-pass histogram, no `norm_objf`
comparison and no cost delta, because the denominator of every one of them is **0 runs
executed** (trap T11: the condition in the same sentence as the number).

This is not a solver failure and not a property of the deck. The refusal happens in the
driver's artifact validation, before the first model of the first optimiser evaluation,
for two independent reasons — and both validation checks are doing exactly what they were
built to do. Nobody has ever generated the artifact pairing an a26-mode run needs, and no
in-tree code path has ever loaded an a26-mode artifact: A26's `SPEC_MODE_A26`
measurements ran offline through `arch_surgery/fixedpoint/replay.py`, which re-derives
its specs from the harvest (`YSpec.from_harvest(mode=...)`) and only cross-checks the
committed record (`replay.py:112–125, 312–314, 318–330`). A31's dissolution claim — explicitly
labelled "derived, not run" — is untouched by this finding, and remains unconfirmed
end-to-end.

## 2. The blocker, named to the line

Both citations are to the merged driver at this branch's base `6b292a2a` (these files do
not exist at the frozen physics base `c0ae5b28`; they are the experiment's own driver
code, unchanged by this task).

**B1 — the spec loader rebuilds every artifact as `SPEC_MODE_A18`.**
`process/core/solver/module_solve.py:531` constructs the predicate's spec as

```python
spec = ys.YSpec(keys, category, scale, record.get("n_components"), comps)
```

— no `mode`, no `scale_floor`, so the rebuilt spec always hashes its components the A18
way. But `YSpec.components_sha256` (`arch_surgery/fixedpoint/ystate.py:539–542`)
prepends a preamble for any non-A18 mode — `mode=a26|floor=0x1.0000000000000p+0\n` —
and the a26 artifact's committed `components_sha256` was computed **with** that preamble.
The two can never agree, and `load_spec` raises at `module_solve.py:536`:

> ystate artifact …/ystate_a26_st_regression.json does not rebuild: components_sha256 is
> `640791529040d8f2…` from the rebuilt spec against `f2f1d2bbfd71c4af…` recorded in the
> file. The predicate would not be Phase A's.

Measured (stage `preflight`, hashing through the project's own `YSpec`, never a
re-implementation):

| artifact | committed sha | rebuilt as a18 (the loader's way) | rebuilt mode-aware | loader accepts |
|---|---|---|---|---|
| `ystate_st_regression.json` (A18) | `08fef594…` | `08fef594…` ✓ | `08fef594…` ✓ | **yes** (control) |
| `ystate_a26_st_regression.json` | `f2f1d2bb…` | `64079152…` ✗ | `f2f1d2bb…` ✓ | **no** |

The mode-aware column shows the artifact is internally sound: rebuilt under its own
recorded `spec_mode` and `scale_floor`, its hash matches exactly. The mismatch is
entirely the loader's hard-coded default.

**B2 — there is no a26-generation write-set artifact.**
`module_solve.load_subsets` (`module_solve.py:579–584`) refuses any write set whose
`ystate_components_sha256` differs from the loaded spec's — deliberately: "the two
artifacts are not from the same deck and generation". The only committed write set for
this deck, `writeset_st_regression.json`, pins the A18 generation (`08fef594…`), and the
committed generator (`arch_surgery/idf_probe/a25_writeset.py:70, :134`) is hard-wired to
`ystate_<scenario>.json`. Even with B1 fixed, both arms refuse here — the load site
(`process/core/caller.py:755–757`) serves `A1'` and `A0'` alike.

**Demonstrated four ways** (all recorded in `runs/a32/preflight/blocker.json`,
regenerated by the committed script):
(a) the sha table above; (b) the write-set pairing (pairs with A18: true; with a26:
false); (c) `module_solve.load_spec` in fresh subprocesses under the exact campaign
environment (`run_a28.env_for`, `PYTHONPATH` pinned, tree asserted — traps T6/T10): A18
control loads, a26 raises the RuntimeError quoted above; (d) the campaign's own first
run attempted for real — `A1'` start000, everything exactly A28's invocation except
`PROCESS_ARCH_YSTATE` — crashes on optimiser evaluation 1 at `caller.py:756 →
module_solve.load_spec()`, `status: crashed`, `node_calls_solve_phase: null` — **zero
models evaluated**.

No workaround was attempted. Re-stamping a derived artifact with a recomputed hash would
defeat the exact check built to refuse "a truncated, reordered or hand-edited file", and
the campaign would then not have run "under the committed a26-mode spec" — a failed gate
is a result, not an obstacle.

## 3. The gate (protocol §12): the harness is not the problem

The brief's reproduction gate was run anyway, to isolate the blocker: one **A18-mode**
`A1'` start000 run (A31's proven recipe — `run_a28.env_for`/`run_one.py`, δ = 0.10,
seed 0, τ = 1e-6, fresh subprocess, exit audit on the A18 artifact), through the same
`run_one_a32` function the campaign would have used, with the spec path as its only
experimental parameter. Against A28's recorded start000
(`runs/a28/h5/st_regression/A1p/start000/metrics.json`, main checkout, read-only):
**3 of 3 fields exactly equal.**

| field | reference (A28) | this run |
|---|---|---|
| `node_calls_solve_phase` | 37 312 | 37 312 |
| `outer_pass_hist` | {1: 9, 2: 560, 3: 1} | identical |
| `norm_objf` (hex) | `-0x1.096acf3342e04p+4` | identical |

**Teeth: 3 of 3 perturbations trip** — +1 on the node-call count, +1 on one histogram
bucket, one ULP on the objective each flip the comparison to FAIL (stage `gate`,
recorded in `runs/a32/gate/gate.json`). So the harness reproduces A28 bit-for-bit and
the comparison can fail; the spec loader is the whole of what is missing.

## 4. What would lift the blocker (for the user to authorise — not applied)

1. **B1, one construction call in `process/core/solver/module_solve.py:531`** — pass the
   record's own mode and floor through:

   ```python
   spec = ys.YSpec(
       keys, category, scale, record.get("n_components"), comps,
       mode=record.get("spec_mode", ys.SPEC_MODE_A18),
       scale_floor=float(record.get("scale_floor", ys.SCALE_FLOOR)),
   )
   ```

   `YSpec.mode` is read in exactly three places (`ystate.py:493, :539–542, :560–562`) —
   the sha preamble and the serialisation — and never enters the residual, so the change
   cannot move an A18-mode number; A18 artifacts carry `spec_mode: "a18"` and take the
   unchanged path. That is an argument, not a gate: after the change, switch-neutrality
   is to be **gated** against A28's record per protocol §12 (this task's own gate stage
   is ready to be that gate), not asserted.
2. **B2, an a26-generation write set** — same subsets (the per-module write census does
   not depend on the spec's categorisation), stamped against the a26 spec's
   `components_sha256`; either by extending `a25_writeset.py` to take the spec path, or
   by committing a regenerated `writeset_a26_st_regression.json` with disclosed
   provenance. A26 committed a26-mode ystate artifacts for all four decks, so the same
   pairing gap exists on every deck, not just this one.

Both touch committed evidence (`process/` driver code and/or `docs/data/` artifacts) and
therefore need the user's approval; the follow-up task then extends this script's
`campaign`/`a0p` stages (deliberately left as guarded refusals rather than untestable
code) and re-gates before publishing any number.

## 5. Autonomous decisions, with reversal paths

1. **The gate was run despite the stop** (2 runs, ~90 s): it isolates the blocker to the
   spec loader and is the protocol-12 gate the fixed driver will need. Reversal: delete
   `runs/a32/gate/`; nothing else rests on it.
2. **The campaign stages refuse instead of not existing** — `campaign`/`a0p` re-run the
   preflight and exit 3 with the blocker message while it stands, so the failure path is
   reachable from the committed entry point (protocol §15) and nobody can half-run a
   campaign on this driver state. Reversal: extend the stages after the fix.
3. **Both stages were re-executed on the clean committed tree** (`e8915f40`) after the
   first execution ran with the script still untracked (stamped dirty); the published
   record is the clean generation, and the pre-commit generation agreed on every field
   and boolean. Reversal: none needed — `runs/a32/` holds only the clean generation.
4. **The a26 attempt's exit-audit stayed on the A18 artifact**, as every A32 run's would
   have: it is the yardstick A28's recorded exit residuals were measured with, and
   changing it would have changed the ruler alongside the thing measured.

## 6. Provenance and reproduction

Every run: fresh subprocess, own working directory, `PYTHONPATH` pinned to this
worktree, exact tree asserted in-process (traps T6/T10); every published quantity is a
count, a name, a hash or a bit-exact float — no conclusion rests on a timing.

Reproduction, from this worktree (environment `PROCESS_surgery_env`):

```
cd arch_surgery/idf_probe
python a32_tail_confirm.py gate        # §3: the A18-mode reproduction gate, teeth included
python a32_tail_confirm.py preflight   # §2: the blocker, four ways (exit 3 = BLOCKED)
python a32_tail_confirm.py campaign    # the guarded refusal (exit 3 while blocked)
```

Which stage produced which figure: §2's sha table, write-set pairing, subprocess
outcomes and the run attempt — `preflight` (`runs/a32/preflight/blocker.json`, the
attempt under `preflight/A1p_start000_a26_attempt/`); §3's table and teeth — `gate`
(`runs/a32/gate/gate.json`, run under `gate/A1p_start000/`). Source citations are to
this worktree at `6b292a2a` (driver and instrument files, absent at `c0ae5b28`):
`process/core/solver/module_solve.py` (`:531`, `:536`, `:579–584`),
`process/core/caller.py` (`:755–757`), `arch_surgery/fixedpoint/ystate.py` (`:493`,
`:539–542`, `:560–562`), `arch_surgery/idf_probe/a25_writeset.py` (`:70`, `:134`),
`arch_surgery/fixedpoint/replay.py` (`:112–125`, `:312–314`, `:318–330`). Bulk run
artifacts stay
untracked per the standing rule; the committed script regenerates them.

## 7. Change log

- 2026-09-03 — task opened; mandatory reads done; A28/A31 machinery traced to the spec
  load path.
- 2026-09-03 — blocker found before any run: `load_spec` rebuilds every artifact as
  `SPEC_MODE_A18` and the a26 artifact's preamble'd sha can never match; confirmed
  empirically in the exact campaign environment; second blocker (write-set generation
  pairing) identified behind it. Stop-and-report per the brief.
- 2026-09-03 — `a32_tail_confirm.py` written and committed (`e8915f40`): gate PASS (3/3
  fields bit-exact against A28, 3/3 teeth), preflight BLOCKED (B1 and B2 both standing,
  campaign first run refused at spec load, zero models evaluated); both stages
  re-executed on the clean committed tree; report written.
