#!/usr/bin/env python
"""A13: prove each gate can fail before its zeros are accepted (protocol 12).

Trap T11 records this project publishing a ``0`` without the condition that
limits it, and a gate predicate here has once returned PASS on an empty set.  A
zero is evidence only if the same predicate returns non-zero when there is
something to find.

Three checks, one per gate, each using the production predicate unmodified.

**Bit comparator (gates 1 and 2).**  Copy the ``parent`` run directory, perturb
exactly one MFILE float by one unit in the last place -- the smallest change an
IEEE-754 double admits -- and re-run ``compare_a3.compare_pair``.  It must
report exactly one differing line and one differing float.  Then compare two
genuinely different scenarios, which must fail with a large count.

**Acceptance predicate (gate 2).**  Perturb ``norm_objf`` in a copied
``metrics.json`` by one ULP and confirm ``compare_a13.acceptance`` flips to
FAIL.  This is the D6 predicate, which reads the in-memory hex signature rather
than the MFILE, so the MFILE check above does not exercise it.

**Count gate (gate 3).**  Feed ``compare_a13.saving`` two copies of the *same*
census and confirm it reports a saving of zero -- it must not manufacture one
from identical inputs.  Then move a single model evaluation and confirm it
reports exactly one.  Two conservation identities are also checked on the real
runs: the hoisted evaluations must equal (tail runs x tail size), and the
``output()``-path traffic outside every window (trap T7) must be identical in
both arms, since the hoist does not touch it.

Usage:  python a13_gate_sensitivity.py --runs runs/a13
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from compare_a3 import _floats, _mfile_path, _VARNAME, compare_pair  # noqa: E402
from compare_a13 import acceptance, saving  # noqa: E402

#: A results line that is safe to perturb: a plain float, not run metadata.
TARGET = "(rmajor)"


def ulp_perturb(runs: Path, scenario: str) -> dict:
    """Gate 1/2 bit comparator: one ULP in one MFILE float must be seen."""
    src = runs / scenario / "parent"
    dst = runs / scenario / "_ulp"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

    path = _mfile_path(runs, scenario, "_ulp")
    out, done, before, after = [], False, None, None
    for ln in path.read_text(errors="replace").splitlines():
        parts = ln.split()
        if (
            not done
            and len(parts) >= 3
            and _VARNAME.match(parts[1])
            and parts[1].startswith(TARGET)
        ):
            try:
                v = float(parts[2])
            except ValueError:
                out.append(ln)
                continue
            w = math.nextafter(v, math.inf)
            before, after = v.hex(), w.hex()
            out.append(ln.replace(parts[2], f"{w:.17e}", 1))
            done = True
            continue
        out.append(ln)
    if not done:
        return {"status": "TARGET NOT FOUND", "target": TARGET}
    path.write_text("\n".join(out) + "\n")

    res = compare_pair(runs, scenario, "parent", "_ulp")
    return {
        "target_variable": TARGET,
        "value_hex_before": before,
        "value_hex_after": after,
        "comparator_status": res["status"],
        "mfile_lines_differing": res["mfile_lines_differing"],
        "mfile_lines_compared": res["mfile_lines_compared"],
        "mfile_floats_differing": res["mfile_floats_differing"],
        "mfile_floats_compared": res["mfile_floats_compared"],
        "denominator_floats_in_parent_mfile": len(
            _floats(_mfile_path(runs, scenario, "parent"))
        ),
        "detected": res["status"] == "FAIL"
        and res["mfile_floats_differing"] == 1
        and res["mfile_lines_differing"] == 1,
    }


def cross_scenario(runs: Path, a: str, b: str) -> dict:
    fa = _floats(_mfile_path(runs, a, "parent"))
    fb = _floats(_mfile_path(runs, b, "parent"))
    common = set(fa) & set(fb)
    diff = [k for k in common if fa[k] != fb[k]]
    return {
        "scenario_a": a,
        "scenario_b": b,
        "floats_compared": len(common),
        "floats_differing": len(diff),
        "detected": len(diff) > 0,
    }


def acceptance_perturb(runs: Path, scenario: str) -> dict:
    """Gate 2's D6 predicate: one ULP in norm_objf must flip it to FAIL."""
    src = runs / scenario / "parent"
    dst = runs / scenario / "_acc"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    p = dst / "metrics.json"
    m = json.loads(p.read_text())
    before = m["exact"]["norm_objf"]
    if before is None:
        return {"status": "norm_objf ABSENT", "detected": None}
    after = math.nextafter(float.fromhex(before), math.inf).hex()
    m["exact"]["norm_objf"] = after
    p.write_text(json.dumps(m, indent=2))
    baseline = acceptance(runs, scenario, "parent", "parent")
    res = acceptance(runs, scenario, "parent", "_acc")
    return {
        "value_hex_before": before,
        "value_hex_after": after,
        "status_unperturbed": baseline["status"],
        "quantities_compared": res["quantities_compared"],
        "status_perturbed": res["status"],
        "detected": baseline["status"] == "PASS" and res["status"] == "FAIL",
    }


def count_gate(runs: Path, scenario: str) -> dict:
    """Gate 3: no saving from identical inputs; exactly one from one moved eval."""
    stem = runs / scenario
    real_default = stem / "census_default" / "node_census.json"
    real_hoisted = stem / "census_hoisted" / "node_census.json"
    if not (real_default.exists() and real_hoisted.exists()):
        return {"status": "MISSING"}

    sandbox = runs / "_count_sensitivity" / scenario
    if sandbox.exists():
        shutil.rmtree(sandbox)
    for arm in ("census_default", "census_hoisted"):
        (sandbox / arm).mkdir(parents=True)
    d = json.loads(real_default.read_text())

    # (a) identical inputs -> saving must be exactly zero
    (sandbox / "census_default" / "node_census.json").write_text(json.dumps(d))
    (sandbox / "census_hoisted" / "node_census.json").write_text(json.dumps(d))
    null = saving(sandbox.parent, scenario)

    # (b) move one evaluation out of the loop -> saving must be exactly one
    one = json.loads(json.dumps(d))
    one["n_evals_in_loop"] -= 1
    one["n_evals_total"] -= 1
    (sandbox / "census_hoisted" / "node_census.json").write_text(json.dumps(one))
    moved = saving(sandbox.parent, scenario)

    # (c) conservation identities on the real runs
    h = json.loads(real_hoisted.read_text())
    tail = h.get("arch_hoist_tail_resolved") or []
    identity_tail = h["n_evals_hoisted"] == h["n_hoisted_tail_runs"] * len(tail)
    identity_outside = h["n_outside_any_window"] == d["n_outside_any_window"]
    return {
        "null_case_saving_evaluations": null.get("model_evaluations_removed"),
        "null_case_detected_nothing": null.get("model_evaluations_removed") == 0,
        "one_moved_evaluation_reported": moved.get("model_evaluations_removed"),
        "one_moved_evaluation_detected": moved.get("model_evaluations_removed") == 1,
        "denominator_model_evaluations": null.get(
            "denominator_model_evaluations_default_arm"
        ),
        "conservation_hoisted_equals_runs_times_tail": identity_tail,
        "hoisted_tail_size": len(tail),
        "n_hoisted_tail_runs": h["n_hoisted_tail_runs"],
        "n_evals_hoisted": h["n_evals_hoisted"],
        "conservation_output_path_traffic_unchanged": identity_outside,
        "n_outside_any_window": {
            "default": d["n_outside_any_window"],
            "hoisted": h["n_outside_any_window"],
        },
        "detected": (
            null.get("model_evaluations_removed") == 0
            and moved.get("model_evaluations_removed") == 1
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=str(HERE / "runs" / "a13"))
    ap.add_argument("--scenario", default="large_tokamak_nof")
    args = ap.parse_args()
    runs = Path(args.runs).resolve()
    result = {
        "bit_comparator_ulp": {args.scenario: ulp_perturb(runs, args.scenario)},
        "bit_comparator_cross_scenario": cross_scenario(
            runs, "large_tokamak_nof", "low_aspect_ratio_DEMO"
        ),
        "acceptance_predicate_ulp": {
            args.scenario: acceptance_perturb(runs, args.scenario)
        },
        "count_gate": {s: count_gate(runs, s) for s in ("large_tokamak_nof",)},
    }
    (runs / "_gate_sensitivity_a13.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
