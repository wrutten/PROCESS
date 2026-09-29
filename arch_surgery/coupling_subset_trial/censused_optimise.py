#!/usr/bin/env python
"""V4's optimisation-phase child, with the read-before-write census observing it.

Task A92 (optimisation-path-census).  Runs ``harness/child/optimise.py`` of
the V4 folder **unchanged**, in the same subprocess, with :mod:`rbw_census`
installed on the first ``call_models`` and every ``call_models`` bracketed as
one evaluation (:func:`rbw_census.begin_evaluation` /
:func:`rbw_census.end_evaluation`).  Nothing is narrowed: the loops test what
the arm's environment says they test, the burn time is owned by whoever the
arm says owns it, and the once-per-run set runs where the driver runs it.
The census only observes reads and writes, so the run is expected to
reproduce its campaign record on every count and on the objective's bits;
``optimisation_path_census.py --check-reproduction`` prints that comparison,
and a mismatch is a finding.

Writes beside the record: ``rbw_census.json`` (the run's union per block, the
format A89's census wrote) and ``rbw_census_per_evaluation.json`` (the
per-evaluation series).

Usage (the harness's optimise arguments follow ``--``)::

    python censused_optimise.py -- --tree ... --arm B0 --seed 1 ...
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
V4_DIR = HERE.parent / "MDA_partitioning_experiment_v4"


def main() -> int:
    argv = sys.argv[1:]
    split = argv.index("--")
    rest = argv[split + 1 :]
    outdir = Path(rest[rest.index("--outdir") + 1]).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(HERE))
    sys.path.insert(0, str(V4_DIR))
    import rbw_census
    from process.core import caller as caller_mod  # the V4 copy, via PYTHONPATH
    from process.core.solver import module_solve as ms

    rbw_census.enable_per_evaluation()
    inner = caller_mod.Caller.call_models

    def call_models(self, xc, m):
        spec, _ = ms.load_spec()
        rbw_census.install(caller_mod, ms, self.data, spec)
        rbw_census.begin_evaluation(xc)
        try:
            return inner(self, xc, m)
        finally:
            rbw_census.end_evaluation()

    caller_mod.Caller.call_models = call_models

    sys.argv = [str(V4_DIR / "harness" / "child" / "optimise.py"), *rest]
    from harness.child import optimise

    try:
        rc = optimise.main(rest)
    finally:
        rbw_census.write(outdir / "rbw_census.json")
        rbw_census.write_per_evaluation(outdir / "rbw_census_per_evaluation.json")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
