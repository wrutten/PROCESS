#!/usr/bin/env python
"""V2 experiment — the one-button entry point (EXPERIMENT_PLAN.md App. A 6).

Press Run (F5) in VSCode: no arguments needed.

While ``v2_config.EXECUTION_APPROVED`` is False (the plan is a draft), this
runs the safe subset only: both phases' preflight ledgers plus Phase B's
machinery smoke — and then says exactly what is missing and which task owns
it.  After approval it runs the whole experiment: preflights, Phase A
campaign + tally, Phase B campaign + tally.  Campaign stages refuse rather
than degrade when instrumentation is missing (§15: failure paths reachable
from the same entry point).
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import v2_config as cfg  # noqa: E402
import phase_a  # noqa: E402
import phase_b  # noqa: E402


def main() -> int:
    print("=" * 68)
    print("MDA partitioning experiment V2 — plan: EXPERIMENT_PLAN.md")
    print(f"execution approved: {cfg.EXECUTION_APPROVED}")
    print("=" * 68)

    print("\n--- Phase A preflight " + "-" * 45)
    rc_a = phase_a.stage_preflight()
    print("\n--- Phase B preflight " + "-" * 45)
    rc_b = phase_b.stage_preflight()

    if not cfg.EXECUTION_APPROVED:
        print("\n--- Phase B machinery smoke (not a measurement) " + "-" * 19)
        rc_s = phase_b.stage_smoke()
        print("\n" + "=" * 68)
        print("Draft mode: preflights + smoke only.")
        print("To execute the experiment: approve EXPERIMENT_PLAN.md (dated "
              "status-header edit), flip v2_config.EXECUTION_APPROVED in the "
              "same commit, and press Run again.")
        print("=" * 68)
        return rc_s

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
    return phase_b.stage_tally()


if __name__ == "__main__":
    raise SystemExit(main())
