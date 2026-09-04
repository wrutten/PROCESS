#!/usr/bin/env python
"""V3 experiment — the one-button entry point (V3 plan §7).

Copied verbatim (task A41, first commit 913b89f0) from
arch_surgery/MDA_partitioning_experiment_v2/run_experiment.py at commit
b7dbd2a9, then modified for V3 by task A41.

Press Run (F5) in VSCode: no arguments needed.

While ``v3_config.EXECUTION_APPROVED`` is False (the plan is a draft), this
runs the safe subset only: both phases' preflight ledgers, the G7
record-completeness gate, and both phases' machinery smokes — and then says
exactly what is missing and which task owns it.  After the user's dated
approval it runs the whole experiment: preflights, Phase A campaign +
tally, Phase B campaign (whose own stage chain runs G0, G5 and G7 first) +
tally.  Campaign stages refuse rather than degrade when instrumentation is
missing (§15: failure paths reachable from the same entry point).
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import v3_config as cfg  # noqa: E402
import phase_a  # noqa: E402
import phase_b  # noqa: E402


def main() -> int:
    print("=" * 68)
    print("MDA partitioning experiment V3 — plan: EXPERIMENT_PLAN.md")
    print(f"execution approved: {cfg.EXECUTION_APPROVED}")
    print("=" * 68)

    print("\n--- Phase A preflight " + "-" * 45)
    rc_a = phase_a.stage_preflight()
    print("\n--- Phase B preflight " + "-" * 45)
    rc_b = phase_b.stage_preflight()

    if not cfg.EXECUTION_APPROVED:
        print("\n--- G7 record-completeness gate " + "-" * 35)
        rc_g7 = phase_b.stage_g7gate()
        print("\n--- Phase B machinery smoke (not a measurement) " + "-" * 19)
        rc_s = phase_b.stage_smoke()
        print("\n--- Phase A machinery smoke (not a measurement) " + "-" * 19)
        rc_sa = phase_a.stage_smoke()
        print("\n" + "=" * 68)
        print("Draft mode: preflights + G7 + smokes only.")
        print("To execute the experiment: approve EXPERIMENT_PLAN.md (dated "
              "status-header edit), flip v3_config.EXECUTION_APPROVED in the "
              "same commit, and press Run again.")
        print("=" * 68)
        return rc_g7 or rc_s or rc_sa

    if rc_a != 0 or rc_b != 0:
        print("\ninstrumentation missing — campaigns refused (see ledgers)")
        return 3
    rc = phase_a.stage_campaign()
    if rc != 0:
        return rc
    rc = phase_a.stage_tally()
    if rc != 0:
        return rc
    rc = phase_b.stage_campaign()
    if rc != 0:
        return rc
    rc = phase_b.stage_tally()
    if rc != 0:
        return rc
    # Context-only timings run last and never fail the experiment: a timing
    # problem is reported, not fatal (no acceptance quantity rests on it).
    rc_t = phase_b.stage_timing()
    if rc_t != 0:
        print(f"timing stage returned {rc_t} — context only, experiment "
              f"result stands")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
