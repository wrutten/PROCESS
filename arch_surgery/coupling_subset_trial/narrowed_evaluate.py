#!/usr/bin/env python
"""V4's evaluation-phase child, with this trial's substitutions installed first.

Task A89 (coupling-subset-trial).  Runs ``harness/child/evaluate.py`` of the V4
folder **unchanged**, in the same subprocess, after :func:`narrowing.install`
(test set, once-per-run execution, timers) and, with ``--census``, the
read-before-write census of :mod:`rbw_census`.

The entry, the displacement and the **exit audit are not narrowed**: the audit
loads the committed coupling-state artifact through ``--coupling-state`` and
sweeps once more over every component of ``y``.

Writes beside the record: ``narrowing.json`` (the test set per block),
``timing.json`` (the timers frozen at the end of ``call_models``, before the
audit), ``pass_log.jsonl`` with ``--pass-log``, ``rbw_census.json`` with
``--census``.

Usage (the harness's evaluate arguments follow ``--``)::

    python narrowed_evaluate.py --test-set rbw [--pass-log] [--census] -- --tree ... --arm A0 ...
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
V4_DIR = HERE.parent / "MDA_partitioning_experiment_v4"


def main() -> int:
    argv = sys.argv[1:]
    split = argv.index("--")
    own, rest = argv[:split], argv[split + 1 :]
    p = argparse.ArgumentParser()
    p.add_argument("--test-set", required=True)
    p.add_argument("--pass-log", action="store_true")
    p.add_argument("--census", action="store_true")
    args = p.parse_args(own)
    configuration = rest[rest.index("--configuration") + 1]
    arm = rest[rest.index("--arm") + 1]
    outdir = Path(rest[rest.index("--outdir") + 1]).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(HERE))
    sys.path.insert(0, str(V4_DIR))
    import narrowing
    from process.core import caller as caller_mod
    from process.core.solver import module_solve as ms  # the V4 copy, via PYTHONPATH

    narrowing.install(ms, caller_mod, test_set=args.test_set,
                      configuration=configuration, arm=arm, outdir=outdir,
                      pass_log=args.pass_log)
    if args.census:
        import rbw_census

        inner = caller_mod.Caller.call_models

        def call_models(self, xc, m):
            spec, _ = ms.load_spec()
            rbw_census.install(caller_mod, ms, self.data, spec)
            return inner(self, xc, m)

        caller_mod.Caller.call_models = call_models

    sys.argv = [str(V4_DIR / "harness" / "child" / "evaluate.py"), *rest]
    from harness.child import evaluate

    rc = evaluate.main(rest)
    (outdir / "timing.json").write_text(json.dumps(
        narrowing.STATE.get("timers_at_call_end") or {}, indent=1))
    if args.census:
        rbw_census.write(outdir / "rbw_census.json")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
