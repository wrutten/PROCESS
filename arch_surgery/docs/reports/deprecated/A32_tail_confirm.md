# A32 (tail-confirm) — the tail vanishes: 2 802 → 25, every survivor the cold first call

> **Document status** — **CURRENT · TASK REPORT, open.** Written by task A32 (tail-confirm),
> 2026-09-03, on branch `A32-tail-confirm`, branched from `architecture_surgery` at `6b292a2a`.
> Archived to `deprecated/` when the task merges and authoritative there (trap T3).

| | |
|---|---|
| **Task** | Run `st_regression` `A1'` across all 25 starts under the committed a26-mode coupling-state spec and confirm end-to-end that A28's recurring 3+-pass tail (2 802 of 54 480 calls) dissolves, as A31 derived; plus flat-arm (`A0'`) confirmation and a traced verification of *which call* survives |
| **Result** | **CONFIRMED.** 3+-pass calls: **2 802 / 54 480 → 25 / 49 920** — exactly one per run, verified by call index on the heaviest start to be **the cold first call**, whose extra pass converges a genuine continuous component. The moved-constant counter goes to **literal zero in both arms** (A1′ 10 528 → 0; A0′ heaviest-3 9 093 → 0). A31's mechanism (exact-equality flicker on harvest-constants under the A18-mode spec) is demonstrated end-to-end, not just derived |
| **Script** | [`arch_surgery/idf_probe/a32_tail_confirm.py`](../../idf_probe/a32_tail_confirm.py) — stages `gate`, `preflight`, `campaign`, `a0p`, `traced`, `tally`; committed at `99fefded` before the campaign ran; every run's `metrics.json` stamps `tree_git_head 99fefded…, dirty False` |
| **Runs** | 32 fresh-subprocess PROCESS solves: 1 A18-mode gate run, 1 preflight a26 full run, 25 `A1'` campaign starts, 3 `A0'` starts, 1 traced `A1'` start010, plus 1 earlier refused attempt (blocker era). All 30 a26-spec campaign-class runs `status: ok` — denominators carry no drops |
| **Date** | 2026-09-03 |

---

## 1. Verdict

**The tail vanishes, and its survivor is exactly what A31 predicted.** Under the committed
a26-mode spec (`ystate_a26_st_regression.json`), with **nothing else changed** from A28's
campaign configuration:

| quantity | A28 (A18-mode spec) | A32 (a26-mode spec) |
|---|---|---|
| `A1'` runs ok | 25 / 25 | **25 / 25** |
| calls at 3+ outer passes | 2 802 / 54 480 | **25 / 49 920** |
| per-run 3+-pass calls | 1 … 858 (heavy tail) | **exactly 1 in every run** |
| calls with a moved constant | 10 528 / 54 480 | **0 / 49 920** |
| `A0'` (starts 009/010/012) moved-constant calls | 9 093 / 29 490 | **0 / 16 530** |
| `A0'` 3+-pass calls | 0 / 29 490 | 0 / 16 530 |
| `norm_objf` bit-identical to A28 | — | 5 / 25 (`A1'`); not expected — see §5 |

**The surviving 3+-pass call is the cold first call, by call index, not by inference.** The
traced start010 run (A28's heaviest tail: 858 of 11 370 calls at 3+ passes) records 12 930
calls under the a26 spec; **exactly one** reaches pass 3 — **call 1** — and its pass-3 argmax
is `fwbs.p_cp_shield_nuclear_heat_mw`, a *continuous* component whose scaled residual
2.28e-11 is genuine sub-τ convergence from cold staleness, not constant flicker
(`runs/a32/traced/traced.json`).

Independently re-tallied from the raw per-start `metrics.json` files (not through the
script's own tally): all figures above reproduce, and the per-run tail is `[1] × 25`.

## 2. History: the blocker (found at `e8915f40`, lifted at `99fefded`)

The campaign could not start on the driver as first committed — two independent validation
checks refusing a spec/write-set pairing nobody had generated (full demonstration in the
committed record `runs/a32/preflight/blocker.json` of that era and in this report's history
at `4abfaa75`):

- **B1 — the spec loader was mode-blind.** `module_solve.load_spec` rebuilt every ystate
  artifact as `SPEC_MODE_A18`; the a26 artifact's `components_sha256` carries the non-A18
  mode preamble, so the rebuild could never match and `load_spec` refused. No in-tree code
  path had ever loaded an a26-mode artifact (A26's SPEC_MODE_A26 numbers came from
  `fixedpoint/replay.py`, offline).
- **B2 — no a26-generation write set existed**; `load_subsets` (correctly) refuses a write
  set from another spec generation.

**The lift (commit `99fefded`), both under the driver-scope rule** (CLAUDE.md:
`process/core/solver/` is default driver scope; nothing under `process/models/` touched):

1. `load_spec` now passes the artifact's own `spec_mode` and `scale_floor` through to
   `YSpec`. An A18 artifact takes the unchanged path — **gated, not asserted**: §3.
2. `a25_writeset.py` gained `--spec-variant`; its **control** (default invocation, same probe
   census) regenerates the committed A18 write set exactly — every field but
   `tree_git_head` — and `writeset_a26_st_regression.json` is the same measured subsets
   stamped against the a26 spec's sha (`f2f1d2bb…`), with `spec_variant` and
   `ystate_artifact` disclosed in the artifact. The probe census used
   (`runs/a18/st_regression/harvest/probe_modules.json`, main tree) was validated by that
   control; all three surviving census copies (`harvest`, `harvest_rep2`, `harvest_inert`)
   produce the identical `subsets_sha256`.

The same pairing gap exists for the a26 artifacts of the other three decks; closing those is
V2 work (`EXPERIMENT_PLAN.md` Appendix A item 1).

## 3. The gate (protocol §12): switch-neutrality of the driver fix, shown not argued

One **A18-mode** `A1'` start000 run through the fixed driver, exactly A28's configuration,
against A28's recorded start000 — **3 of 3 exact fields equal, 3 of 3 teeth trip**
(`runs/a32/gate/gate.json`, run at clean `99fefded`):

| field | reference (A28) | this run |
|---|---|---|
| `node_calls_solve_phase` | 37 312 | 37 312 |
| `outer_pass_hist` | {1: 9, 2: 560, 3: 1} | identical |
| `norm_objf` (hex) | `-0x1.096acf3342e04p+4` | identical |

So the B1 change is byte-neutral for A18-mode runs on the full campaign path, and the a26
numbers below are attributable to the spec alone. The preflight stage (same commit) records
both blockers **clear**: the a26 spec loads (`spec_mode_attr: "a26"`, sha `f2f1d2bb…`
matched) and the a26 write set pairs, with subsets identical to the A18 generation.

## 4. Campaign detail

All 25 `A1'` starts (A28's exact enumeration: seed = k, δ = 0.10, τ = 1e-6, fresh
subprocess each, exit audit kept on the **A18** artifact — the ruler A28's exit residuals
were measured with). Per-start records under `runs/a32/campaign/A1p/`; comparison rows and
totals in `runs/a32/campaign_summary.json`. Headline per-start pattern: every start's
outer-pass histogram is `{1: n₁, 2: n₂, 3: 1}` — the single 3-pass call per run, cold.

The three `A0'` starts are the heaviest **by the flat arm's own flicker signature**: A28
records zero 3+-pass calls anywhere in `A0'` (0 / 57 030 — the earlier task brief's
"heaviest A0′ tails 010/005/015" was `A1'`'s ranking, corrected here); its flicker lives in
the moved-constant counter, so starts 009/010/012 (3 868 / 3 637 / 1 588 flagged calls in
A28) were run, and all three drop to **zero**.

## 5. What is *not* claimed

- **No cross-arm cost conclusion.** Total `call_models` changed (`A1'` 54 480 → 49 920;
  `A0'` heaviest-3 29 490 → 16 530) because the spec change alters sweep counts, hence
  finite-difference dust, hence optimiser paths. These are reported as observations;
  comparing arms under the a26 spec at matched accuracy is V2's job, on V2's pre-declared
  rules. The `A0'` figure especially sits on a 3-start sample *selected for* being hostile.
- **`norm_objf` bit-identity is not expected across a spec change** (5/25 runs happen to
  land bit-identical; the rest differ in last-ULP-dust-fed trajectories). Equivalence at
  matched accuracy is, again, V2's question.
- The a26-mode spec itself is not re-validated here — that is A26's record; this task shows
  the committed artifact loads, pairs, runs, and dissolves the tail as derived.

## 6. Provenance and reproduction

Every run: fresh subprocess, own working directory, `PYTHONPATH` pinned to this worktree,
tree asserted in-process (`tree_git_head 99fefded…, dirty False` in every campaign-class
record); every published quantity is a count, a name, a hash or a bit-exact float — no
conclusion rests on a timing.

Reproduction, from this worktree (environment `PROCESS_surgery_env`):

```
cd arch_surgery/idf_probe
python a32_tail_confirm.py gate       # §3: the neutrality gate, teeth included
python a32_tail_confirm.py preflight  # §3: both blockers clear (or the refusal, pre-fix)
python a32_tail_confirm.py campaign   # §1/§4: 25 A1' starts + tally
python a32_tail_confirm.py a0p        # §4: the flat-arm starts + tally
python a32_tail_confirm.py traced     # §1: the call-index verification
```

Which stage produced which figure: §1/§4's tables — `campaign`/`a0p`
(`runs/a32/campaign_summary.json`); the call-index verification — `traced`
(`runs/a32/traced/traced.json`); §3 — `gate` (`runs/a32/gate/gate.json`) and `preflight`
(`runs/a32/preflight/blocker.json`). Bulk run artifacts stay untracked; the committed
script regenerates them.

## 7. Change log

- 2026-09-03 — task opened; blocker found before any run (spec loader mode-blind, no a26
  write set); stop-and-report at `e8915f40`/`4abfaa75` with the gate already PASS bit-exact.
- 2026-09-03 — blocker lifted at `99fefded` under the driver-scope rule: mode-aware
  `load_spec`, `--spec-variant` write-set generation (control byte-stable), campaign stages
  extended (`campaign`/`a0p`/`traced`/`tally`).
- 2026-09-03 — full pipeline executed from the clean committed tree: gate PASS (3/3 fields,
  3/3 teeth), preflight CLEAR, 25/25 + 3/3 + 1 traced runs ok. **Tail confirmed dissolved:
  2 802/54 480 → 25/49 920, every survivor the cold first call; moved-constant counter 0 in
  both arms.** Report rewritten from the blocked-state version; independent re-tally from
  raw records agrees on every figure.
