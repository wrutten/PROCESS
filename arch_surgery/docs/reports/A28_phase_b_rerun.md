# A28 (phase-b-rerun) — Phase B re-run on the fixed instrument, with a control that can attribute the answer

> **Document status** — **CURRENT · TASK REPORT, open.** Written by task A28 (phase-b-rerun),
> 2026-09-02, on branch `A28-phase-b-rerun` at experiment base commit `c0ae5b28`, branch point
> `dc18c05b`. It is archived to `deprecated/` when the task merges and stays authoritative there
> (trap T3: folder position records lifecycle, not validity). Nothing here is merged; nothing is
> pushed.

| | |
|---|---|
| **Task** | A28 (phase-b-rerun) — re-run Phase B on the instrument A26 (method-fixes) left behind, with the third arm decision **D18** requires, and write up both phases |
| **Branch** | `A28-phase-b-rerun`, worktree `/home/wrutten/projects/PROCESS_surgery_worktrees/A28-phase-b-rerun` |
| **Governed by** | **D5**/**D11** (physics frozen; model edits need approval — none was needed), **D6** (correctness never on iteration variables), **D14** (the baseline is PROCESS as shipped), **D15** (calibrated δ, hoist inside the variant, objf mismatch is a robustness finding, a failed module solve raises), **D17** (`large_tokamak_eval` dropped; timings as context only), **D18** (three arms; `A0′ → A1′` is the headline) |
| **Environment** | `PROCESS_surgery_env` (`/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python`, Python 3.12.14); `PYTHONPATH` pinned to this worktree per subprocess; the **exact** tree asserted inside every subprocess (trap T6) |
| **Date** | 2026-09-02 |

---

*(This document is written in place as each stage completes; §12's change log is append-only.)*
