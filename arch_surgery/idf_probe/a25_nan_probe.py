#!/usr/bin/env python
"""Why the variant fails starts the baseline "solves" — measured, not inferred.

Every extra failure the Phase B variant produced in A25's campaign is the same
`ModuleSolveFailure`, on the same module, naming the same field:
``current_drive.eta_cd_dimensionless_hcd_primary``, scored ``inf`` by Phase A's
coupling-state predicate.  13 of 13 across the four decks.

Two things need measuring rather than arguing:

1. **Is the field actually non-finite at those points?**  This runs the
   **baseline** at one of the failing starts, with the same perturbation the
   campaign applied, and reads the field off the returned state.
2. **Does PROCESS's own predicate accept a NaN as converged?**
   ``Caller.check_agreement`` is ``np.allclose(..., equal_nan=True)``, which
   returns ``True`` for two NaN states.  Decision D14(c) says the baseline
   reproduces that defect deliberately, because the baseline is PROCESS as
   shipped.  Demonstrated here rather than quoted.

Usage
-----
    PYTHONPATH=<tree> python a25_nan_probe.py --scenario large_tokamak_eval \\
        --seed 1 --delta 0.1 --outdir <dir> --expect-tree <tree>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent

FIELD = ("current_drive", "eta_cd_dimensionless_hcd_primary")


def _factor(seed: int, ivar: int, delta: float) -> float:
    """The campaign's perturbation factor, reproduced exactly."""
    h = hashlib.sha256(f"a25|{seed}|{ivar}".encode()).digest()
    u = int.from_bytes(h[:8], "big") / float(1 << 64)
    return 1.0 + delta * (2.0 * u - 1.0)


def check_agreement_on_nan() -> dict:
    """Does PROCESS's own idempotence predicate call a NaN state converged?"""
    import numpy as np

    from process.core.caller import Caller

    nan = np.array([float("nan"), 1.0])
    finite = np.array([1.0, 1.0])
    return {
        "check_agreement(nan_state, same_nan_state)": bool(
            Caller.check_agreement(nan, nan.copy())
        ),
        "check_agreement(finite, nan)": bool(
            Caller.check_agreement(finite, nan)
        ),
        "source": "np.allclose(previous, current, rtol=1e-6, equal_nan=True)",
        "reading": (
            "equal_nan=True makes a state that has gone NaN idempotent with "
            "itself, so the loop exits and the solver proceeds.  Phase A's "
            "predicate scores such a component inf and never converges -- the "
            "deliberate inverse (ystate.py module docstring)."
        ),
    }


def baseline_at_start(deck: Path, seed: int, delta: float) -> dict:
    """Run the baseline at one perturbed start and read the field."""
    import process.core.solver.solver_handler as sh
    from process.main import SingleRun

    orig = sh.load_scaled_bounds
    rec: dict = {}

    def perturbed(data):
        orig(data)
        nums = data.numerics
        n = int(nums.n_iteration_variables)
        for i in range(n):
            ivar = int(nums.ixc[i])
            f = _factor(seed, ivar, delta)
            lo = float(nums.itv_scaled_lower_bounds[i])
            hi = float(nums.itv_scaled_upper_bounds[i])
            nums.xcm[i] = min(max(float(nums.xcm[i]) * f, lo), hi)
        rec["n_variables"] = n

    if seed:
        sh.load_scaled_bounds = perturbed

    sr = SingleRun(str(deck), solver="vmcon", update_obsolete=True)
    sr.run()

    ns = getattr(sr.data, FIELD[0])
    v = object.__getattribute__(ns, FIELD[1])
    try:
        f = float(v)
    except (TypeError, ValueError):
        f = None
    return {
        "perturbation": rec,
        "ifail": int(sr.data.numerics.ifail)
        if hasattr(sr.data.numerics, "ifail")
        else None,
        "field": f"{FIELD[0]}.{FIELD[1]}",
        "value_repr": repr(v),
        "value_type": type(v).__name__,
        "is_finite": (f is not None and math.isfinite(f)),
        "is_nan": (f is not None and math.isnan(f)),
    }


def variant_at_start(deck: Path, seed: int, delta: float) -> dict:
    """Run the VARIANT at a failing start, recording why the score is ``inf``.

    Phase A's ``YSpec.residual`` is wrapped **from the harness side** -- nothing
    under ``process/`` is touched -- so the raw pair of snapshots behind an
    ``inf`` score is recorded rather than inferred.  ``inf`` has three possible
    causes in that predicate and they mean different things: a snapshot that is
    not float-viewable, a shape change, or a non-finite value in either
    snapshot.
    """
    import numpy as np

    import process.core.solver.solver_handler as sh
    from process.core.solver import module_solve as ms
    from process.main import SingleRun

    ys = ms._ystate_module()
    orig_residual = ys.YSpec.residual
    found: list = []

    def wrapped(self, prev, cur, subset=None):
        res = orig_residual(self, prev, cur, subset=subset)
        if len(found) < 5 and res.scaled.size and not np.all(np.isfinite(res.scaled)):
            j = int(np.argmax(~np.isfinite(res.scaled)))
            i = res.idx_c[j]
            a, b = prev[i], cur[i]
            found.append({
                "component": self.name(i),
                "category": self.category[i],
                "scale": self.scale[i],
                "previous_repr": repr(a)[:120],
                "current_repr": repr(b)[:120],
                "previous_finite": bool(np.all(np.isfinite(np.asarray(a, dtype=float)))),
                "current_finite": bool(np.all(np.isfinite(np.asarray(b, dtype=float)))),
                "n_nan_new": len(res.nan_new),
                "cause": (
                    "non-finite in the PREVIOUS snapshot"
                    if not np.all(np.isfinite(np.asarray(a, dtype=float)))
                    else "non-finite in the CURRENT snapshot"
                    if not np.all(np.isfinite(np.asarray(b, dtype=float)))
                    else "not float-viewable or shape change"
                ),
            })
        return res

    ys.YSpec.residual = wrapped

    orig = sh.load_scaled_bounds

    def perturbed(data):
        orig(data)
        nums = data.numerics
        for i in range(int(nums.n_iteration_variables)):
            ivar = int(nums.ixc[i])
            f = _factor(seed, ivar, delta)
            lo = float(nums.itv_scaled_lower_bounds[i])
            hi = float(nums.itv_scaled_upper_bounds[i])
            nums.xcm[i] = min(max(float(nums.xcm[i]) * f, lo), hi)

    if seed:
        sh.load_scaled_bounds = perturbed

    status = "ok"
    tb = None
    try:
        SingleRun(str(deck), solver="vmcon", update_obsolete=True).run()
    except Exception:
        status = "crashed"
        tb = traceback.format_exc().strip().splitlines()[-1]
    return {"status": status, "last_line": tb, "inf_scores_seen": found}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--delta", type=float, required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--expect-tree", required=True)
    ap.add_argument("--variant", action="store_true",
                    help="run the variant arm and record why a score is inf")
    ap.add_argument("--deck", default=None, help="override the input deck")
    args = ap.parse_args()

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    import process

    pf = Path(process.__file__).resolve()
    if pf.parent.parent != Path(args.expect_tree).resolve():
        raise SystemExit(f"WRONG TREE: {pf}")

    src = Path(args.deck) if args.deck else HERE / "scenarios" / f"{args.scenario}.IN.DAT"
    deck = outdir / src.name
    deck.write_text(src.read_text())

    out: dict = {
        "tree": str(pf.parent.parent),
        "scenario": args.scenario,
        "seed": args.seed,
        "delta": args.delta,
        "predicate_loophole": check_agreement_on_nan(),
    }
    try:
        if args.variant:
            out["variant_run"] = variant_at_start(deck, args.seed, args.delta)
        else:
            out["baseline_returned_state"] = baseline_at_start(
                deck, args.seed, args.delta
            )
        out["status"] = "ok"
    except Exception:
        out["status"] = "crashed"
        out["traceback"] = traceback.format_exc()

    (outdir / "nan_probe.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
