#!/usr/bin/env python
"""A24: what the three scaffolding seams resolve to, measured in the tree.

Run in a fresh subprocess with ``PYTHONPATH`` pointing at the tree under test.
It imports PROCESS, asserts the **exact** tree it got (trap T6 -- the editable
install points at the main checkout, so a prefix test passes on the wrong
tree), and reports:

* the VP5 selection the tree resolved, and whether :func:`subsolve` calls
  through to the model's own solve bit-for-bit when nothing is lifted;
* the registry state -- entry counts, the derived cap, the gap count, every
  array sized by the cap, and ``len(lablcc)``;
* the burn-time residual's identity at its own root, at full precision and
  with no tolerance;
* whether an unrecognised ``PROCESS_ARCH_LIFT`` value is an import-time error
  rather than a silent no-op.

It runs no scenario: this is a statement about the code, not about a solve.
The solve-level statement is the bit-identity gate in ``gates.py``.

Usage
-----
    PYTHONPATH=<tree> python a24_seam_probe.py --outdir <dir> \
        --expect-tree <tree>
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import subprocess
import sys
from pathlib import Path


def _assert_tree(expect: str | None) -> dict:
    import process

    process_file = Path(process.__file__).resolve()
    actual = process_file.parent.parent
    if expect:
        want = Path(expect).resolve()
        if actual != want:
            raise SystemExit(
                f"WRONG TREE: imported {process_file} (tree {actual}), expected "
                f"exactly {want}. Set PYTHONPATH={want} for this subprocess."
            )
    return {"process_file": str(process_file), "tree": str(actual)}


def _vp5() -> dict:
    from process.core.solver.subsolve import (
        LIFT_ENABLED,
        LIFTED_SITES,
        SITE_BURN_TIME,
        SITES,
        subsolve,
    )
    from process.models.pulse import Pulse, burn_time_residual, burn_time_root

    rng = random.Random(20260901)
    n = call_through = returns_x0 = 0
    for _ in range(20_000):
        vs = rng.uniform(-1e4, 1e4)
        v = rng.uniform(-1e2, 1e2)
        tr = rng.uniform(-1e3, 1e3)
        x0 = rng.uniform(-1e4, 1e4)
        if v == 0.0:
            continue
        n += 1
        got = subsolve(
            burn_time_residual,
            x0,
            (vs, v, tr),
            site=SITE_BURN_TIME,
            direct=Pulse.calculate_burn_time,
        )
        want_direct = Pulse.calculate_burn_time(vs, v, tr)
        if got == want_direct and math.copysign(1.0, got) == math.copysign(
            1.0, want_direct
        ):
            call_through += 1
        if got == x0:
            returns_x0 += 1

    return {
        "lift_enabled": LIFT_ENABLED,
        "lifted_sites": sorted(LIFTED_SITES),
        "known_sites": list(SITES),
        "env_PROCESS_ARCH_LIFT": os.environ.get("PROCESS_ARCH_LIFT"),
        "denominator_input_quadruples": n,
        "n_subsolve_equals_direct_call": call_through,
        "n_subsolve_returns_x0": returns_x0,
        # With nothing lifted, subsolve must be the model's own solve on every
        # input; with burn_time lifted it must be the design-vector value on
        # every input.  Stated as counts over a named denominator, not as a
        # boolean.
        "default_path_is_call_through": (not LIFT_ENABLED) and call_through == n,
        "lifted_path_is_design_vector": LIFT_ENABLED and returns_x0 == n,
        "residual_at_root_identity": _residual_identity(
            burn_time_root, burn_time_residual
        ),
    }


def _residual_identity(root, residual) -> dict:
    rng = random.Random(4481)
    n = bad = blind = 0
    for _ in range(100_000):
        vs = rng.uniform(-1e4, 1e4)
        v = rng.uniform(-1e2, 1e2)
        tr = rng.uniform(-1e3, 1e3)
        if v == 0.0:
            continue
        r = root(vs, v, tr)
        if not math.isfinite(r):
            continue
        n += 1
        if residual(r, vs, v, tr) != 0.0:
            bad += 1
        nudged = math.nextafter(r, math.inf)
        if nudged != r and residual(nudged, vs, v, tr) == 0.0:
            blind += 1
    return {
        "denominator_input_triples": n,
        "nonzero_at_root": bad,
        "zero_one_ulp_off_root": blind,
    }


def _registry() -> dict:
    from process.core.model import DataStructure
    from process.core.solver.constraints import ConstraintManager
    from process.core.solver.iteration_variables import (
        ITERATION_VARIABLES,
        initialise_iteration_variables,
    )
    from process.data_structure.numerics import (
        N_ITERATION_VARIABLES_MAX,
        NumericsData,
    )

    keys = set(ITERATION_VARIABLES)
    top = max(keys)
    ids = ConstraintManager.constraint_ids()

    d = DataStructure()
    initialise_iteration_variables(d)
    nums = d.numerics
    arrays = (
        "ixc",
        "lablxc",
        "name_xc",
        "boundl",
        "boundu",
        "scale",
        "scafc",
        "xcm",
        "xcs",
        "itv_scaled_lower_bounds",
        "itv_scaled_upper_bounds",
        "vlam",
    )
    fresh = NumericsData()
    return {
        "n_iteration_variables_registered": len(keys),
        "highest_iteration_variable_key": top,
        "N_ITERATION_VARIABLES_MAX": N_ITERATION_VARIABLES_MAX,
        "cap_is_derived_from_keys": N_ITERATION_VARIABLES_MAX == top,
        "n_gaps_in_1_to_max": len(set(range(1, top + 1)) - keys),
        "n_constraints_registered": ConstraintManager.num_constraints(),
        "highest_constraint_id": max(i for i in ids if isinstance(i, int)),
        "len_lablcc": len(fresh.lablcc),
        "lablcc_last": fresh.lablcc[-1],
        "arrays_sized_by_cap": {a: len(getattr(nums, a)) for a in arrays},
        "denominator_arrays_checked": len(arrays),
        "itvar_178": {
            "name": ITERATION_VARIABLES[178].name if 178 in ITERATION_VARIABLES else None,
            "module": ITERATION_VARIABLES[178].module
            if 178 in ITERATION_VARIABLES
            else None,
            "lablxc_index_177": str(nums.lablxc[177]),
            "boundl_index_177": float(nums.boundl[177]),
            "boundu_index_177": float(nums.boundu[177]),
        },
        "constraint_93_registered": 93 in ids,
    }


def _bad_arm_is_loud(expect_tree: str | None) -> dict:
    """An unrecognised ``PROCESS_ARCH_LIFT`` must raise, not silently no-op."""
    env = dict(os.environ)
    env["PROCESS_ARCH_LIFT"] = "no_such_site"
    proc = subprocess.run(
        [sys.executable, "-c", "from process.core.solver import subsolve"],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(Path(expect_tree).resolve()) if expect_tree else None,
    )
    return {
        "returncode": proc.returncode,
        "raised": proc.returncode != 0,
        "message_names_the_bad_site": "no_such_site" in proc.stderr,
        "stderr_tail": proc.stderr.strip().splitlines()[-1:] or [""],
    }


def _deck_audit(scenarios: list[str]) -> dict:
    """Do any of the study's decks name the appended registry entries?

    An appended entry is inert because ``ixc``/``icc`` select what is active.
    That is a claim about the decks, so it is checked against them rather than
    asserted.
    """
    here = Path(__file__).resolve().parent
    out = {}
    for name in scenarios:
        path = here / "scenarios" / f"{name}.IN.DAT"
        if not path.exists():
            out[name] = {"status": "MISSING"}
            continue
        icc: list[int] = []
        ixc: list[int] = []
        for line in path.read_text(errors="replace").splitlines():
            body = line.split("*", 1)[0].strip()
            if not body or "=" not in body:
                continue
            lhs, rhs = body.split("=", 1)
            key = lhs.strip().split("(")[0].strip().lower()
            if key not in ("icc", "ixc"):
                continue
            for tok in rhs.replace(",", " ").split():
                try:
                    (icc if key == "icc" else ixc).append(int(tok))
                except ValueError:
                    pass
        out[name] = {
            "n_icc_named": len(icc),
            "n_ixc_named": len(ixc),
            "names_constraint_93": 93 in icc,
            "names_itvar_178": 178 in ixc,
        }
    out["no_deck_names_either"] = all(
        isinstance(v, dict)
        and not v.get("names_constraint_93")
        and not v.get("names_itvar_178")
        for v in out.values()
        if isinstance(v, dict) and "n_icc_named" in v
    )
    out["denominator_decks"] = len(scenarios)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--expect-tree", default=None)
    ap.add_argument(
        "--scenarios",
        nargs="*",
        default=[
            "large_tokamak_nof",
            "low_aspect_ratio_DEMO",
            "st_regression",
            "large_tokamak_eval",
        ],
    )
    ap.add_argument("--skip-bad-arm", action="store_true")
    args = ap.parse_args()

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    result: dict = {"pythonpath": os.environ.get("PYTHONPATH")}
    result.update(_assert_tree(args.expect_tree))
    result["vp5"] = _vp5()
    result["registry"] = _registry()
    result["deck_audit"] = _deck_audit(args.scenarios)
    if not args.skip_bad_arm:
        result["unrecognised_arm_is_loud"] = _bad_arm_is_loud(args.expect_tree)

    (outdir / "seam_probe.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
