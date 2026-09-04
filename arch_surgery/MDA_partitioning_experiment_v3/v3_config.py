"""V3 experiment configuration — every declared setting in one place.

Copied verbatim (task A41, first commit 913b89f0) from
arch_surgery/MDA_partitioning_experiment_v2/v2_config.py at commit b7dbd2a9,
then modified per V3_DEVELOPMENT_PLAN.md §6–§7 (task A41).  The V2 file is
frozen as the record of what V2 ran; every V3 declaration lives here.

Values here are the V3 EXPERIMENT_PLAN.md declarations (deliverable T1,
task A39).  Changing one after execution begins is an amendment to the
plan, not a tweak: date it there first.
"""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parent.parent
IDF_PROBE = TREE / "arch_surgery" / "idf_probe"
DATA = TREE / "arch_surgery" / "docs" / "data"
RUNS = HERE / "runs"

#: Master switch.  While False, run_experiment.py executes gates and smoke
#: tests only and refuses every campaign stage (the plan is a DRAFT:
#: execution begins only when the user approves it — the user flips this in
#: the same commit that records the dated approval in EXPERIMENT_PLAN.md's
#: status header; V3 plan §7, task A42's precondition).
EXECUTION_APPROVED = False

#: Decks (D17).  st_regression is the k = 0 deck (nothing to lift or pin).
DECKS = ("large_tokamak_nof", "low_aspect_ratio_DEMO", "st_regression")
PULSED = ("large_tokamak_nof", "low_aspect_ratio_DEMO")

#: Campaign shape (V3 plan §3; O2 resolved 2026-09-04: N = 25 everywhere).
N_STARTS = 25          # start000..start024, seed = k
DELTA = 0.10           # D15's calibrated perturbation size
TAU = 1e-6             # the shared tolerance setting (plan §3: same tau)
WORKERS = 3            # campaign pool width (memory-bound; V3 plan §7).
#                        A41's own light runs override to W = 1 through the
#                        V3_WORKERS environment variable (stamped per stage).

#: Pre-declared acceptance parameters (V3 plan §4).
SIMILARITY_FACTOR_F = 10.0   # audit medians AND p90s within this factor
ITER_RATIO_MAX = 1.05        # median paired optimiser-iteration ratio bound

#: O3 (resolved 2026-09-04, option A): the same-optimum check's floor is
#: 1e-6 RELATIVE on norm_objf — the tolerance the correctness gate has used
#: since A25 (provenance: PROCESS's own check_agreement rtol, not a choice
#: made here).  Acceptance: spread <= max(F x yardstick, floor), where the
#: yardstick is the measured R->B0 spread and the floor is applied as
#: OBJF_FLOOR_REL x the nearest-rank median |norm_objf| of the pair's base
#: arm over the compared pairs (operationalization declared in the tally).
OBJF_FLOOR_REL = 1e-6

#: Check 1a (multi-attractor decks): accepted optima are clustered by
#: norm_objf; a RELATIVE gap larger than CLUSTER_GAP_FLOOR_FACTOR x
#: OBJF_FLOOR_REL between adjacent sorted values separates clusters.
CLUSTER_GAP_FLOOR_FACTOR = 10.0

#: Declared median construction for every Phase B check statistic
#: (orchestrator correction 0a8f5af2: V2's lad B2->B3 median proved
#: construction-dependent — statistics.median 1.33 vs nearest-rank 1.40
#: over the same 10 pairs).  The declared construction is NEAREST-RANK
#: (upper-middle): sorted_values[n // 2].  statistics.median may be
#: published beside it as a diagnostic, never as the check value.
MEDIAN_CONSTRUCTION = "nearest-rank upper-middle: sorted_values[n // 2]"

#: Spec generation: a26-mode everywhere (plan §2; A31/A32).
def ystate_for(deck: str) -> Path:
    return DATA / f"ystate_a26_{deck}.json"

def writeset_for(deck: str) -> Path:
    return DATA / f"writeset_a26_{deck}.json"

def postsolve_for(deck: str) -> Path:
    return DATA / f"postsolve_{deck}.json"

def postsolve_nolift_for(deck: str) -> Path:
    """Phase A's block arms run the ORIGINAL deck (the pin owns the burn
    time; A34 refuses pin + lifted deck as two owners), so on the pulsed
    decks their post-solve artifact is the nolift derivation — same node
    set, stamped for the base constraint set."""
    if deck in PULSED:
        return DATA / f"postsolve_nolift_{deck}.json"
    return postsolve_for(deck)

#: Phase A arms (V3 plan §3.1).  A0 = flat control; A1u = V2's A1 exactly
#: (the corrected-audit re-run, A38's arm, the prime's counterfactual);
#: A1 = A1u plus the prime — the V3 intervention's per-call structure.
PHASE_A_ARMS = ("A0", "A1u", "A1")

#: Phase B arms (V3 plan §3.2): as V2's ladder; B2 and B3 carry the prime.
PHASE_B_ARMS = ("R", "B0", "B1", "B2", "B3")

#: O4 (resolved 2026-09-04): where the prime is switched on — A1, B2 and B3
#: only.  R stays PROCESS as shipped; A0/B0/B1 keep upstream order; A1u is
#: the prime-free Phase A counterfactual.  The prime's env value is the
#: variant-point name task A40 implements in process/core/caller.py.
PRIMED_ARMS = ("A1", "B2", "B3")
PRIME_ENV_VALUE = "fw_geometry"

#: Missing-instrumentation ledger.  A stage that needs an entry here refuses
#: with its task name while the entry is False — update when the task merges.
INSTRUMENTATION = {
    "trust_mode": {          # outer loop off for per_module
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
    "single_mda_eval": {     # Phase A: one call_models at a perturbed state
        "available": True,   # merged 2026-09-03: arch_surgery/idf_probe/v2_eval_one.py
        "task": "A34 (merged 2026-09-03)",
        "env": None,
    },
    "restricted_audit": {    # A38: audit over the in-loop write set
        "available": True,   # merged 2026-09-04 (e9e7e965)
        "task": "A38 (merged 2026-09-04)",
        "env": None,
    },
    "prime": {               # D19: PROCESS_ARCH_PRIME variant point (caller.py)
        "available": False,  # owned by task A40 (v3-prime); flipped at its merge
        "task": "A40 (v3-prime, dispatched 2026-09-04)",
        "env": "PROCESS_ARCH_PRIME",
    },
    # H3: n_solver_iterations / ifail / ladder stage / constraint residual
    # vector / active set at EVERY exit.  Built and gated by A41: G7 PASSED
    # with teeth on 2026-09-04 (5 field teeth + 1 block tooth, each refused
    # and naming its field; record runs/phase_b/g7gate/gate.json).  Left
    # False here because the ledger's convention is that an entry flips when
    # its task MERGES (every True entry above is stamped "(merged DATE)")
    # and A41 does not merge itself — the flip, with the merge date, is a
    # one-line orchestrator action at A41's merge.
    "exit_forensics": {
        "available": False,
        "task": "A41 (v3-harness) — G7 PASS 2026-09-04, flip at merge",
        "env": None,
    },
}
