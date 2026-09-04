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


def _assert_interpreter() -> None:
    """Refuse before any subprocess if this interpreter cannot run PROCESS.

    Every campaign subprocess is launched with ``sys.executable``, so the
    interpreter that starts this file decides the interpreter for all ~500 of
    them.  Started under the wrong one, the FIRST run dies with
    ``PackageNotFoundError: No package metadata was found for process`` and
    every later one would too.  That happened on 2026-09-04's launch (the
    system python3.10 instead of ``PROCESS_surgery_env``'s 3.12), and the
    campaign reported it as "the A0 reference did not converge" — a machinery
    failure wearing a physics result's clothes.

    CLAUDE.md's rule for failure paths: fail with a message naming the fix.
    """
    import subprocess
    probe = (
        "import process, sys; "
        "sys.stdout.write(process.__file__)"
    )
    r = subprocess.run([sys.executable, "-c", probe],
                       capture_output=True, text=True)
    good = r.returncode == 0 and str(cfg.TREE) in (r.stdout or "")
    if good:
        return
    print("=" * 68)
    print("REFUSING TO START — this interpreter cannot run PROCESS.")
    print("=" * 68)
    print(f"  interpreter : {sys.executable}")
    print(f"  version     : {sys.version.split()[0]}")
    why = (r.stderr or "").strip().splitlines()
    print(f"  error       : {why[-1] if why else (r.stdout or 'unknown')}")
    print(f"  needs       : process imported from {cfg.TREE}")
    print()
    print("  Every campaign subprocess inherits this interpreter, so starting")
    print("  here would fail ~500 runs identically.  Run it with the project")
    print("  environment instead (CLAUDE.md, Environments):")
    print()
    print("    /home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python \\")
    print(f"        {Path(__file__).resolve()}")
    print()
    print("  In VSCode: pick the PROCESS_surgery_env interpreter, then Run.")
    raise SystemExit(2)


def main() -> int:
    _assert_interpreter()
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
