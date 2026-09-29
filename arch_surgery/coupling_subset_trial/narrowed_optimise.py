#!/usr/bin/env python
"""V4's optimisation-phase child, with the narrowed convergence test installed first.

Task A93 (tolerance-phase-b).  Runs ``harness/child/optimise.py`` of the V4
folder **unchanged**, in the same subprocess, after :func:`narrowing.install`
has replaced the loops' test set — the way :mod:`narrowed_evaluate` wraps the
evaluation child.  Nothing in the V4 folder is edited.

What is and is not narrowed
---------------------------
* **The loops' test set** (``full`` = V4's whole-``y`` test; ``rbw`` = the
  read-before-write census set of ``rbw_sets.json``).  The census was taken on
  the evaluation-phase arms, so the optimisation arm names the census arm
  whose execution order it shares: ``B0`` (flat) uses ``A0``'s ``FLAT`` set,
  ``B2`` (partitioned) uses ``A2``'s ``M1``/``M2``/``M3`` sets.
* **The tolerance** is not set here: it is the arm's environment
  (``PROCESS_ARCH_TAU``), composed by V4's pool from the campaign's ``tau``.
* **Not narrowed**: the seed's displacement of the design vector (the V4
  child's own hook, so a run pairs with the campaign record of the same
  seed), the optimiser, the exit audit (every component of ``y``) and the
  output path.  The per-run deferred nodes are **not** executed after each
  evaluation (``once_per_run=False``): an optimisation runs them once at the
  output path already.

Writes beside the record: ``narrowing.json`` (the test set per block, from
:mod:`narrowing`) and ``narrowed_optimise.json`` (the arm mapping).

Usage (the harness's optimise arguments follow ``--``)::

    python narrowed_optimise.py --test-set rbw --census-arm A0 -- --tree ... --arm B0 ...
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
V4_DIR = HERE.parent / "MDA_partitioning_experiment_v4"

#: Which evaluation-phase arm's census an optimisation arm reads: the one with
#: the same loop shape (flat / partitioned) and execution order.
CENSUS_ARM_FOR = {"B0": "A0", "B2": "A2"}


def main() -> int:
    argv = sys.argv[1:]
    split = argv.index("--")
    own, rest = argv[:split], argv[split + 1 :]
    p = argparse.ArgumentParser()
    p.add_argument("--test-set", required=True, choices=("full", "rbw"))
    p.add_argument("--census-arm", default=None,
                   help="the evaluation-phase arm whose census sets are used; "
                        "defaults to CENSUS_ARM_FOR[arm]")
    args = p.parse_args(own)
    configuration = rest[rest.index("--configuration") + 1]
    arm = rest[rest.index("--arm") + 1]
    outdir = Path(rest[rest.index("--outdir") + 1]).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    census_arm = args.census_arm or CENSUS_ARM_FOR[arm]

    sys.path.insert(0, str(HERE))
    sys.path.insert(0, str(V4_DIR))
    import narrowing
    from process.core import caller as caller_mod
    from process.core.solver import module_solve as ms  # the V4 copy, via PYTHONPATH

    narrowing.install(ms, caller_mod, test_set=args.test_set,
                      configuration=configuration, arm=census_arm, outdir=outdir,
                      pass_log=False, once_per_run=False)
    (outdir / "narrowed_optimise.json").write_text(json.dumps({
        "optimisation_arm": arm, "census_arm": census_arm, "test_set": args.test_set,
        "tau_environment": __import__("os").environ.get("PROCESS_ARCH_TAU"),
        "module_solve_tau": ms.TAU, "once_per_run": False}, indent=1))

    sys.argv = [str(V4_DIR / "harness" / "child" / "optimise.py"), *rest]
    from harness.child import optimise

    return optimise.main(rest)


if __name__ == "__main__":
    raise SystemExit(main())
