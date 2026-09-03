#!/usr/bin/env python
"""V2 Phase A — per-call MDA cost, no optimiser (EXPERIMENT_PLAN.md §3).

FLAT vs BLOCKS at one shared τ, N = 25 seeded coupling-state perturbations
per deck, coupling pinned on the pulsed decks, post-solve nodes absent from
the measured call.  Stages:

``preflight``
    The instrumentation ledger.  Phase A cannot run at all until A34 lands
    (single-MDA-eval mode for both arms; trust mode for BLOCKS; the pin for
    the pulsed decks) and, on the pulsed decks, until A33's a26 write sets
    land.  Each gap refuses by task name — never a silent skip.
``campaign``
    Per deck: the FLAT-converged reference point, the equivalence gate
    (BLOCKS pinned at the FLAT value must reproduce the FLAT fixed point
    within audit resolution, teeth), then N paired single-eval runs per arm
    at seeded ±δ coupling perturbations.  Refuses while preflight refuses
    or while ``EXECUTION_APPROVED`` is False.
``tally``
    Per-node counts, weighting-invariance bracket, audit similarity
    (median AND p90 within factor F), lift residual reported separately,
    entry-distance bins — from the on-disk records.

The campaign/tally bodies are written against A34's declared interface and
raise with a precise message if the interface that lands differs — extending
them then is a one-commit change, and no stage pretends to run on machinery
that does not exist (a failed gate is a result; an unrunnable stage says so).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import v2_config as cfg  # noqa: E402

PA_RUNS = cfg.RUNS / "phase_a"


def stage_preflight() -> int:
    PA_RUNS.mkdir(parents=True, exist_ok=True)
    ledger = {}
    ready = True
    for key in ("single_mda_eval", "trust_mode"):
        led = cfg.INSTRUMENTATION[key]
        ledger[key] = dict(led)
        if not led["available"]:
            ready = False
            print(f"  {key:20s} REFUSED  not built — {led['task']}")
        else:
            print(f"  {key:20s} ready")
    for deck in cfg.DECKS:
        entries = {"ystate_a26": cfg.ystate_for(deck).exists(),
                   "writeset_a26": cfg.writeset_for(deck).exists()}
        if deck in cfg.PULSED:
            led = cfg.INSTRUMENTATION["pin"]
            entries["pin"] = led["available"]
            if not led["available"]:
                print(f"  {deck:24s} pin REFUSED — {led['task']}")
        for name, ok in entries.items():
            if not ok:
                ready = False
                print(f"  {deck:24s} {name} MISSING")
        if all(entries.values()):
            print(f"  {deck:24s} artifacts ready")
    record = {"ledger": ledger, "ready": ready,
              "execution_approved": cfg.EXECUTION_APPROVED}
    (PA_RUNS / "preflight.json").write_text(json.dumps(record, indent=2))
    print(f"\nphase A preflight: {'READY' if ready else 'NOT READY'}")
    return 0 if ready else 3


def stage_campaign() -> int:
    if not cfg.EXECUTION_APPROVED:
        print("REFUSED: execution not approved (v2_config.EXECUTION_APPROVED).")
        return 3
    if stage_preflight() != 0:
        print("\nREFUSED: Phase A instrumentation missing — the ledger above "
              "names the task each gap belongs to (A33/A34).")
        return 3
    raise SystemExit(
        "Phase A preflight is READY: A34's instruments have landed since "
        "this script was committed.  Extend this stage against the interface "
        "A34 actually delivered (its report names the env switches and the "
        "single-eval entry point) — deliberately not implemented on an "
        "untestable path (the A32 lesson: guarded refusal, then extend)."
    )


def stage_tally() -> int:
    root = PA_RUNS / "campaign"
    if not root.exists():
        print("no Phase A campaign records — the campaign has not run")
        return 1
    raise SystemExit(
        "Phase A records exist but the tally is deliberately unimplemented "
        "until the record format A34 delivers is real — extend alongside "
        "stage_campaign."
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", nargs="?", default="preflight",
                    choices=["preflight", "campaign", "tally"])
    args = ap.parse_args()
    if args.stage == "preflight":
        return stage_preflight()
    if args.stage == "campaign":
        return stage_campaign()
    return stage_tally()


if __name__ == "__main__":
    raise SystemExit(main())
