"""V2 experiment configuration — every declared setting in one place.

Verbatim copy (task A41, first commit) of
arch_surgery/MDA_partitioning_experiment_v2/v2_config.py at commit b7dbd2a9;
content otherwise unchanged.

Values here are the EXPERIMENT_PLAN.md declarations (revision 2).  Changing
one after execution begins is an amendment to the plan, not a tweak: date it
there first.
"""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parent.parent
IDF_PROBE = TREE / "arch_surgery" / "idf_probe"
DATA = TREE / "arch_surgery" / "docs" / "data"
RUNS = HERE / "runs"

#: Master switch.  While False, run_experiment.py executes gates and smoke
#: tests only and refuses every campaign stage (the plan is DRAFT: execution
#: begins only when the user approves it — flip this in the same commit that
#: records the approval in EXPERIMENT_PLAN.md's status header).
EXECUTION_APPROVED = True

#: Decks (D17).  st_regression is the k = 0 deck (nothing to lift or pin).
DECKS = ("large_tokamak_nof", "low_aspect_ratio_DEMO", "st_regression")
PULSED = ("large_tokamak_nof", "low_aspect_ratio_DEMO")

#: Campaign shape (plan §2).
N_STARTS = 25          # start000..start024, seed = k
DELTA = 0.10           # D15's calibrated perturbation size
TAU = 1e-6             # the shared tolerance setting (plan §3: same tau, checked)
WORKERS = 3            # memory-bound: 0.65 GB measured peak RSS, 7 GB RAM

#: Pre-declared acceptance parameters (plan §3/§4; Appendix B until confirmed).
SIMILARITY_FACTOR_F = 10.0   # audit medians AND p90s within this factor
ITER_RATIO_MAX = 1.05        # median paired optimiser-iteration ratio bound

#: Spec generation: a26-mode everywhere (plan §2; A31/A32).
def ystate_for(deck: str) -> Path:
    return DATA / f"ystate_a26_{deck}.json"

def writeset_for(deck: str) -> Path:
    return DATA / f"writeset_a26_{deck}.json"

def postsolve_for(deck: str) -> Path:
    return DATA / f"postsolve_{deck}.json"

#: Phase B arms (plan §4).  B2 = partitioned WITH the outer loop (re-admitted
#: by the user 2026-09-03 pre-campaign); B3 = partitioned trust (no outer
#: loop) — the designed architecture and the headline.  V1/A28's primed arms
#: are different objects (A0' ~ B0; A1' ~ B2 without post-solve).
#: B1 keeps B0's upstream node order: B0 -> B1 must vary the lift and
#: nothing else (the resequencing belongs to the partition step, B1 -> B2).
PHASE_B_ARMS = ("R", "B0", "B1", "B2", "B3")

#: Missing-instrumentation ledger.  A stage that needs an entry here refuses
#: with its task name while the entry is False — update when the task merges.
INSTRUMENTATION = {
    "trust_mode": {          # outer loop off for per_module (Phase A BLOCKS, Phase B A2)
        "available": True,   # merged 2026-09-03
        "task": "A34 (merged 2026-09-03)",
        "env": "PROCESS_ARCH_OUTER=trust",
    },
    "post_solve": {          # optimiser-irrelevant FF nodes out of the per-call path
        "available": True,   # merged 2026-09-03 (4cf488f6)
        "task": "A33 (merged 2026-09-03)",
        "env": "PROCESS_ARCH_POST_SOLVE",
    },
    "pulsed_a26_writesets": {  # a26-generation write sets for the pulsed decks
        "available": True,      # all three decks (A32 + A33, merged 2026-09-03)
        "task": "A33 (merged 2026-09-03)",
        "env": None,
    },
    "pin": {                 # Phase A pulsed decks: pinned burn-time coupling
        "available": True,   # merged 2026-09-03
        "task": "A34 (merged 2026-09-03)",
        "env": "PROCESS_ARCH_PIN_BURN_TIME",
    },
    "single_mda_eval": {     # Phase A: one call_models at a perturbed state, no optimiser
        "available": True,   # merged 2026-09-03: arch_surgery/idf_probe/v2_eval_one.py
        "task": "A34 (merged 2026-09-03)",
        "env": None,
    },
}
