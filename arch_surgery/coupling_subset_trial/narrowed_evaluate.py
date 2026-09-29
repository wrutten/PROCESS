#!/usr/bin/env python
"""V4's evaluation-phase child with the loops' convergence test narrowed.

Task A89 (coupling-subset-trial).  Runs ``harness/child/evaluate.py`` of the V4
folder **unchanged**, in the same subprocess, after one substitution made from
outside that folder: ``module_solve.load_subsets`` — the one place the driver
learns which components of ``y`` each loop tests — is wrapped so that

* every block's test set becomes its V4 write set **intersected** with the
  named test set (``interface`` or ``feedback``, from ``test_sets.json``), and
* the flat arrangement's single block, which V4 tests on the whole of ``y``
  (``subsets.get(label)`` is ``None`` there), tests the named test set.

With ``--test-set full`` nothing is substituted and the run is V4's own.

What is **not** narrowed: the entry, the displacement and the exit audit.  The
audit loads the committed coupling-state artifact through ``--coupling-state``
and sweeps once more over every component, so a component the narrowed test
let move shows up there as a measured residual.

A per-pass log (``pass_log.jsonl`` in the run directory) records, for every
convergence test the loops make, the narrowed residual that decided and the
whole-``y`` residual of the same two snapshots, with the components above τ
outside the narrowed set.  The logging returns the driver's own residual
object unchanged; it adds no model call and no sweep.

Usage (the harness's evaluate arguments follow ``--``)::

    python narrowed_evaluate.py --test-sets test_sets.json --test-set feedback \\
        -- --tree ... --configuration ... --arm A0 ...
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
V4_DIR = HERE.parent / "MDA_partitioning_experiment_v4"
TEST_SETS = ("full", "interface", "feedback")


def main() -> int:
    argv = sys.argv[1:]
    split = argv.index("--")
    own, rest = argv[:split], argv[split + 1 :]
    p = argparse.ArgumentParser()
    p.add_argument("--test-sets", required=True)
    p.add_argument("--test-set", required=True, choices=TEST_SETS)
    args = p.parse_args(own)
    configuration = rest[rest.index("--configuration") + 1]
    outdir = Path(rest[rest.index("--outdir") + 1]).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(V4_DIR))
    from process.core.solver import module_solve as ms  # the V4 copy, via PYTHONPATH

    narrowing = {
        "test_set": args.test_set,
        "test_sets_file": str(Path(args.test_sets).resolve()),
        "configuration": configuration,
        "flat_block_label": ms.FLAT_BLOCK_LABEL,
    }
    if args.test_set != "full":
        chosen = json.loads(Path(args.test_sets).read_text())["configurations"][
            configuration
        ]["sets"][args.test_set]
        original = ms.load_subsets
        log = open(outdir / "pass_log.jsonl", "w")  # noqa: SIM115 - held open

        def narrowed(spec, path=None):
            subsets, provenance = original(spec, path)
            index = {spec.name(i): i for i in range(len(spec.keys))}
            missing = sorted(k for k in chosen if k not in index)
            if missing:
                raise RuntimeError(f"test set names keys y does not have: {missing[:5]}")
            test = frozenset(index[k] for k in chosen)
            new = {label: frozenset(s & test) for label, s in subsets.items()}
            if ms.FLAT_BLOCK_LABEL in new:
                raise RuntimeError("the write sets already name the flat block")
            new[ms.FLAT_BLOCK_LABEL] = test
            narrowing["n_test"] = len(test)
            narrowing["n_by_block"] = {k: len(v) for k, v in sorted(new.items())}
            narrowing["n_by_block_v4"] = {k: len(v) for k, v in sorted(subsets.items())}
            (outdir / "narrowing.json").write_text(json.dumps(narrowing, indent=1))

            inner = spec.residual
            label_of = {v: k for k, v in new.items()}
            counter = {"n": 0}

            def residual(prev, cur, subset=None, **kw):
                res = inner(prev, cur, subset=subset, **kw)
                if subset is None:  # the exit audit's call: not a loop's test
                    return res
                counter["n"] += 1
                full = inner(prev, cur, subset=None, **kw)
                tau = ms.TAU
                sel = set(subset)
                outside = [
                    (spec.name(int(i)), float(v))
                    for i, v in zip(full.idx_c, full.scaled)
                    if int(i) not in sel and v >= tau
                ]
                outside.sort(key=lambda kv: -kv[1])
                log.write(json.dumps({
                    "n": counter["n"],
                    "block": label_of.get(frozenset(subset), "?"),
                    "width": len(sel),
                    "narrow_max": float(res.max),
                    "narrow_converged": bool(res.converged(tau)),
                    "full_max": float(full.max),
                    "full_n_above": int(full.n_above(tau)),
                    "full_argmax": (None if full.argmax is None else spec.name(full.argmax)),
                    "outside_n_above": len(outside),
                    "outside_top": outside[:15],
                }) + "\n")
                log.flush()
                return res

            spec.residual = residual
            return new, provenance

        ms.load_subsets = narrowed
    else:
        (outdir / "narrowing.json").write_text(json.dumps(narrowing, indent=1))

    sys.argv = [str(V4_DIR / "harness" / "child" / "evaluate.py"), *rest]
    from harness.child import evaluate

    return evaluate.main(rest)


if __name__ == "__main__":
    raise SystemExit(main())
