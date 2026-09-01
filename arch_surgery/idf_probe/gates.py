#!/usr/bin/env python
"""F6 -- the correctness and robustness gate library, and A24's bundle gate.

This is the gate machinery Phase B's variant is measured with.  It is written
as a **library first and a command second**, so the next task consumes it
rather than rewriting it: A3 (build-reorder) and A13 (feedforward-hoist) each
grew a gate checker of their own, and a fourth copy of the same predicates is
how three copies drift.

What is reused rather than rewritten
------------------------------------
The bit comparator is ``compare_a3.compare_pair``, imported unchanged.  A3's
own sensitivity check found that its first MFILE line parser anchored on the
first ``(...)`` in a line and so silently dropped about a thousand floats per
scenario; the fixed parser is the one to keep using, not to re-derive.
``compare_a13.acceptance`` is likewise generalised here rather than copied --
:func:`acceptance` below is that predicate with the hoist-specific reporting
fields lifted out into a caller-supplied list.

The gates
---------
**Correctness** -- ``norm_objf`` plus a post-solve feasibility audit, at
matched final accuracy, and **never** on iteration variables.  Decision D6:
some iteration variables are not identified by the problem and differ at an
unchanged optimum, so gating on them generates false alarms.  They are
reported by the bit comparison beside the gate; they are not an acceptance
quantity.

**Matched final accuracy** -- the arms must terminate at a comparable
constraint residual, verified per scenario rather than assumed from a shared
tolerance setting (experiment plan section 3.3).

**Robustness** -- ``ifail`` outcomes across starts, per arm, with the **drop
census reported before any ratio**.  :func:`cost_comparison` structurally
refuses to produce a ratio without being handed a census, because a ratio over
a quietly smaller population is trap T11 and this project has published one
three times.

Denominators
------------
Every count returned by this module carries the population it was counted over
in the same dict.  An empty comparison set is reported as ``EMPTY``, never as a
pass.

Teeth
-----
Protocol section 12: a gate is not accepted until it has been shown capable of
failing.  The ``sensitivity`` subcommand perturbs each predicate by the
smallest amount that should register -- one unit in the last place of one
IEEE-754 double -- using the production predicates unmodified.

Usage
-----
    python gates.py gate        --runs runs/a24
    python gates.py sensitivity --runs runs/a24
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
from compare_a3 import (  # noqa: E402
    _VARNAME,
    _floats,
    _mfile_path,
    compare_pair,
    load,
)

SCENARIOS = [
    "large_tokamak_nof",
    "low_aspect_ratio_DEMO",
    "st_regression",
    "large_tokamak_eval",
]

#: The acceptance quantities, in the order they are reported.  ``norm_objf`` is
#: the objective; ``sqsumsq`` and ``conf_l2`` are the post-solve feasibility
#: audit -- how far off the feasible manifold the returned point sits -- and
#: ``ifail`` is the solver's own verdict.  Iteration variables are deliberately
#: absent (D6).
ACCEPTANCE_EXACT = ("norm_objf", "sqsumsq", "conf_l2")
ACCEPTANCE_MFILE = ("ifail",)


# ---------------------------------------------------------------------------
# Correctness
# ---------------------------------------------------------------------------


def acceptance(
    runs: Path,
    scenario: str,
    ref: str,
    arm: str,
    *,
    report_fields: tuple[str, ...] = (),
) -> dict:
    """Decision-D6 acceptance: ``norm_objf``, feasibility, ``ifail``.

    Compared as hex float literals with **no tolerance**.  Iteration variables
    are never an acceptance quantity.

    Parameters
    ----------
    report_fields :
        ``metrics.json`` keys to report beside the gate for provenance -- the
        resolved arm, say.  They are reported, never gated on.
    """
    mr, ma = load(runs, scenario, ref), load(runs, scenario, arm)
    if mr is None or ma is None:
        return {"status": "MISSING", "arms": {ref: mr is not None, arm: ma is not None}}
    if mr.get("status") != "ok" or ma.get("status") != "ok":
        return {
            "status": "NOT APPLICABLE (run crashed)",
            "run_status": {ref: mr.get("status"), arm: ma.get("status")},
        }

    er, ea = mr.get("exact") or {}, ma.get("exact") or {}
    fr, fa = mr.get("mfile") or {}, ma.get("mfile") or {}
    rows: dict[str, dict] = {}
    for key in ACCEPTANCE_EXACT:
        rows[key] = {ref: er.get(key), arm: ea.get(key)}
    for key in ACCEPTANCE_MFILE:
        rows[key] = {ref: fr.get(key), arm: fa.get(key)}
    for row in rows.values():
        row["identical"] = row[ref] == row[arm]

    # An acceptance quantity that is absent on *both* sides is not evidence of
    # agreement.  `norm_objf` is legitimately None for an evaluation run (fsolve
    # has no objective), so it is counted as present-but-void and named, rather
    # than silently inflating the denominator.
    void = sorted(k for k, r in rows.items() if r[ref] is None and r[arm] is None)
    compared = [k for k in rows if k not in void]
    ok = all(rows[k]["identical"] for k in compared)
    return {
        "status": ("PASS" if ok else "FAIL") if compared else "EMPTY",
        "quantities_compared": len(compared),
        "quantities_void_on_both_sides": void,
        "denominator_acceptance_quantities": len(rows),
        "quantities": rows,
        "note": (
            "iteration variables are deliberately NOT gated on (decision D6); "
            "they are reported by the bit comparison beside this table but are "
            "not an acceptance quantity"
        ),
        "reported_not_gated": {
            k: {ref: mr.get(k), arm: ma.get(k)} for k in report_fields
        },
    }


def feasibility_audit(runs: Path, scenario: str, arm: str) -> dict:
    """Post-solve feasibility of one arm's returned point.

    Not a comparison: the absolute audit the acceptance gate is paired with.
    ``rcm`` holds the constraint residuals at the returned point; the first
    ``n_equality_constraints`` of them are equalities and must be zero, the
    remainder are inequalities.
    """
    m = load(runs, scenario, arm)
    if m is None:
        return {"status": "MISSING"}
    if m.get("status") != "ok":
        return {"status": "NOT APPLICABLE (run crashed)"}
    vals = m.get("values") or {}
    rcm = vals.get("rcm") or []
    meq = m.get("n_equality_constraints")
    if not rcm or meq is None:
        return {"status": "EMPTY", "n_residuals": len(rcm)}
    eqs, ineqs = rcm[:meq], rcm[meq:]
    return {
        "status": "OK",
        "ifail": (m.get("mfile") or {}).get("ifail"),
        "n_equality_constraints": len(eqs),
        "n_inequality_constraints": len(ineqs),
        "n_residuals_audited": len(rcm),
        "max_abs_equality_residual": max((abs(v) for v in eqs), default=None),
        "min_inequality_residual": min(ineqs, default=None),
        "n_inequalities_violated": sum(1 for v in ineqs if v < 0.0),
        "sqsumsq": vals.get("sqsumsq"),
        "conf_l2": vals.get("conf_l2"),
    }


def matched_accuracy(runs: Path, scenario: str, arms: tuple[str, ...]) -> dict:
    """Do the arms terminate at a comparable final accuracy?

    Compared at the *achieved* residual, never at the tolerance setting that
    was asked for (experiment plan section 3.3).  For a bundle expected to be
    bit-identical this is an identity check; for a real variant it is the
    condition without which a cost comparison is unsound.
    """
    rows = {}
    for arm in arms:
        m = load(runs, scenario, arm)
        e = (m or {}).get("exact") or {}
        v = (m or {}).get("values") or {}
        rows[arm] = {
            "sqsumsq_hex": e.get("sqsumsq"),
            "conf_l2_hex": e.get("conf_l2"),
            "sqsumsq": v.get("sqsumsq"),
            "conf_l2": v.get("conf_l2"),
            "ifail": ((m or {}).get("mfile") or {}).get("ifail"),
        }
    present = [a for a in arms if rows[a]["sqsumsq_hex"] is not None]
    hexes = {rows[a]["sqsumsq_hex"] for a in present}
    finite = [rows[a]["conf_l2"] for a in present if rows[a]["conf_l2"] is not None]
    spread = (max(finite) - min(finite)) if finite else None
    return {
        "status": (
            "IDENTICAL"
            if present and len(hexes) == 1
            else ("EMPTY" if not present else "DIFFERING")
        ),
        "arms_compared": len(present),
        "denominator_arms_requested": len(arms),
        "conf_l2_absolute_spread": spread,
        "per_arm": rows,
    }


# ---------------------------------------------------------------------------
# Robustness: ifail across starts, and the drop census
# ---------------------------------------------------------------------------


def collect_starts(runs: Path, scenario: str, arm: str) -> list[dict]:
    """Every start of one arm, as ``metrics.json`` rows.

    A *start* is one perturbed initial design point.  Layout, which the run
    driver writes and which A4's multi-start campaign inherits::

        runs/<scenario>/<arm>/start<k>/metrics.json

    A single-start arm (the deck's own point, written straight into
    ``<arm>/``) is reported as one start named ``start000`` so that the census
    has the same shape either way.
    """
    stem = runs / scenario / arm
    out: list[dict] = []
    for d in sorted(stem.glob("start*")):
        m = load(runs, scenario, f"{arm}/{d.name}")
        if m is not None:
            m = dict(m)
            m["start"] = d.name
            out.append(m)
    if not out:
        m = load(runs, scenario, arm)
        if m is not None:
            m = dict(m)
            m["start"] = "start000"
            out.append(m)
    return out


def _ifail(metrics: dict):
    """``ifail`` as an int where it is integral.

    The MFILE parser hands back a float, so ``str(ifail)`` is ``"1.0"`` and a
    histogram keyed on it does not answer to ``"1"``.  This normalisation
    exists because the first version of :func:`ifail_census` reported
    ``n_ifail_1 = 0`` over a set of four runs that all had ``ifail = 1`` --
    found by the sensitivity check, not by inspection.
    """
    v = (metrics.get("mfile") or {}).get("ifail")
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return v
    return int(f) if f.is_integer() else f


def ifail_census(starts: list[dict]) -> dict:
    """``ifail`` outcomes over a set of starts.  A count, not a rate."""
    hist: dict[str, int] = {}
    for s in starts:
        key = str(_ifail(s))
        if s.get("status") != "ok":
            key = f"crashed({s.get('status')})"
        hist[key] = hist.get(key, 0) + 1
    return {
        "n_starts": len(starts),
        "ifail_histogram": dict(sorted(hist.items())),
        "n_ifail_1": hist.get("1", 0),
        "n_not_ifail_1": len(starts) - hist.get("1", 0),
        "n_crashed": sum(v for k, v in hist.items() if k.startswith("crashed")),
    }


def drop_census(
    starts_by_arm: dict[str, list[dict]],
    *,
    objf_rtol: float = 0.0,
) -> dict:
    """Which starts leave the cost comparison, why, and how many remain.

    Reported **before** any ratio (framework section 2.4, decision D15(c)): a
    start is never silently dropped.  Categories, in the order they are
    applied, each start falling into exactly one:

    ``crashed``
        the run did not complete in some arm
    ``ifail_not_1``
        completed but the solver did not report success in some arm
    ``objf_mismatch``
        succeeded everywhere but ``norm_objf`` differs across arms by more than
        *objf_rtol*.  Decision D15(c) makes this a **robustness finding**, not
        a silent exclusion.  With the default ``objf_rtol = 0`` the test is
        bit-identity, which is what an inert bundle must satisfy.
    ``degenerate_entry``
        kept, but flagged: net electric power at the returned point is not
        positive, where PROCESS's 1990 cost model diverges and the idempotence
        loop's relative predicate becomes arbitrarily tight (issue I-12).  A
        flag, not a drop -- it is reported alongside every cost figure.
    ``kept``
        enters the comparison.
    """
    arms = sorted(starts_by_arm)
    by_start: dict[str, dict[str, dict]] = {}
    for arm in arms:
        for s in starts_by_arm[arm]:
            by_start.setdefault(s["start"], {})[arm] = s

    verdicts: dict[str, str] = {}
    detail: dict[str, dict] = {}
    for name, per_arm in sorted(by_start.items()):
        missing = [a for a in arms if a not in per_arm]
        crashed = [a for a in arms if a in per_arm and per_arm[a].get("status") != "ok"]
        if missing or crashed:
            verdicts[name] = "crashed"
            detail[name] = {"missing_arms": missing, "crashed_arms": crashed}
            continue
        ifails = {a: _ifail(per_arm[a]) for a in arms}
        if any(v != 1 for v in ifails.values()):
            verdicts[name] = "ifail_not_1"
            detail[name] = {"ifail": ifails}
            continue
        objf = {a: ((per_arm[a].get("exact") or {}).get("norm_objf")) for a in arms}
        vals = [float.fromhex(v) for v in objf.values() if v is not None]
        if len(set(objf.values())) > 1:
            worst = (
                (max(vals) - min(vals)) / abs(vals[0])
                if vals and vals[0] != 0.0
                else float("inf")
            )
            if worst > objf_rtol:
                verdicts[name] = "objf_mismatch"
                detail[name] = {"norm_objf_hex": objf, "relative_spread": worst}
                continue
        verdicts[name] = "kept"
        pnet = {
            a: ((per_arm[a].get("mfile") or {}).get("p_plant_electric_net_mw"))
            for a in arms
        }
        if any(v is not None and v <= 0.0 for v in pnet.values()):
            detail[name] = {"degenerate_entry_p_plant_electric_net_mw": pnet}

    counts: dict[str, int] = {}
    for v in verdicts.values():
        counts[v] = counts.get(v, 0) + 1
    n_degenerate = sum(
        1
        for n, v in verdicts.items()
        if v == "kept" and "degenerate_entry_p_plant_electric_net_mw" in detail.get(n, {})
    )
    return {
        "arms": arms,
        "denominator_starts_offered": len(by_start),
        "n_kept": counts.get("kept", 0),
        "counts": dict(sorted(counts.items())),
        "n_kept_but_degenerate_entry_I12": n_degenerate,
        "objf_rtol": objf_rtol,
        "per_start_verdict": verdicts,
        "per_start_detail": detail,
        "note": (
            "reported before any ratio; a start is excluded from the cost "
            "comparison only through this table (decision D15(c))"
        ),
    }


def cost_comparison(census: dict, cost_by_arm: dict[str, dict[str, float]]) -> dict:
    """A ratio between arms, computed only over the census's kept starts.

    *census* is required positionally and is echoed into the result: a cost
    figure that does not carry the population it was computed over is trap
    T11, which this project has published three times.
    """
    kept = [n for n, v in census["per_start_verdict"].items() if v == "kept"]
    arms = census["arms"]
    totals = {
        a: sum(cost_by_arm.get(a, {}).get(n, 0.0) for n in kept) for a in arms
    }
    ref = arms[0]
    return {
        "drop_census": census,
        "n_starts_in_ratio": len(kept),
        "denominator_starts_offered": census["denominator_starts_offered"],
        "totals_over_kept_starts": totals,
        "ratio_to_" + ref: {
            a: (totals[a] / totals[ref]) if totals[ref] else None for a in arms
        },
        "n_kept_but_degenerate_entry_I12": census["n_kept_but_degenerate_entry_I12"],
    }


# ---------------------------------------------------------------------------
# Switch-neutrality of the new seams specifically
# ---------------------------------------------------------------------------


def seam_neutrality(runs: Path, scenario: str, arms: tuple[str, ...]) -> dict:
    """Did the new seams stay unselected, and is that visible in the artifact?

    Reads what each run *resolved*, from the imported modules rather than from
    the environment (``run_one.py``), so a tree that predates a variant point
    reports ``None`` rather than echoing the arm the driver asked for.
    """
    rows = {}
    for arm in arms:
        m = load(runs, scenario, arm) or {}
        rows[arm] = {
            "arch_lift_env": m.get("arch_lift_env"),
            "arch_lift_module_present": m.get("arch_lift_module_present"),
            "arch_lift_sites": m.get("arch_lift_sites"),
            "arch_lift_known_sites": m.get("arch_lift_known_sites"),
            "arch_hoist_name": m.get("arch_hoist_name"),
            "arch_sequence_name": m.get("arch_sequence_name"),
            "itvar_names": (m.get("itvar_names") or []),
        }
    return {
        "per_arm": rows,
        "no_arm_lifted_a_site": all(
            not r["arch_lift_sites"] for r in rows.values()
        ),
        "no_arm_activated_itvar_178": all(
            "t_plant_pulse_burn" not in r["itvar_names"] for r in rows.values()
        ),
        "denominator_arms": len(arms),
    }


# ---------------------------------------------------------------------------
# Teeth (protocol section 12)
# ---------------------------------------------------------------------------

#: A results line safe to perturb: a plain float, not run metadata.
ULP_TARGET = "(rmajor)"


def sensitivity_bit_comparator(
    runs: Path, scenario: str, ref: str, target: str = ULP_TARGET
) -> dict:
    """One ULP in one MFILE float must be seen by :func:`compare_pair`."""
    src, dst = runs / scenario / ref, runs / scenario / "_ulp"
    if not src.exists():
        return {"status": "MISSING"}
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
            and parts[1].startswith(target)
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
        return {"status": "TARGET NOT FOUND", "target": target}
    path.write_text("\n".join(out) + "\n")

    res = compare_pair(runs, scenario, ref, "_ulp")
    return {
        "target_variable": target,
        "value_hex_before": before,
        "value_hex_after": after,
        "comparator_status": res["status"],
        "mfile_lines_differing": res["mfile_lines_differing"],
        "mfile_lines_compared": res["mfile_lines_compared"],
        "mfile_floats_differing": res["mfile_floats_differing"],
        "mfile_floats_compared": res["mfile_floats_compared"],
        "denominator_floats_in_reference_mfile": len(
            _floats(_mfile_path(runs, scenario, ref))
        ),
        "detected": res["status"] == "FAIL"
        and res["mfile_floats_differing"] == 1
        and res["mfile_lines_differing"] == 1,
    }


def sensitivity_cross_scenario(runs: Path, a: str, b: str, arm: str) -> dict:
    """Two genuinely different scenarios must fail with a large count."""
    pa, pb = _mfile_path(runs, a, arm), _mfile_path(runs, b, arm)
    if pa is None or pb is None:
        return {"status": "MISSING"}
    fa, fb = _floats(pa), _floats(pb)
    common = set(fa) & set(fb)
    diff = [k for k in common if fa[k] != fb[k]]
    return {
        "scenario_a": a,
        "scenario_b": b,
        "floats_compared": len(common),
        "floats_differing": len(diff),
        "detected": len(diff) > 0,
    }


def sensitivity_acceptance(runs: Path, scenario: str, ref: str, key: str) -> dict:
    """One ULP in an acceptance quantity must flip :func:`acceptance` to FAIL.

    This exercises the D6 predicate, which reads the in-memory hex signature
    rather than the MFILE, so the MFILE perturbation above does not reach it.
    """
    src, dst = runs / scenario / ref, runs / scenario / f"_acc_{key}"
    if not src.exists():
        return {"status": "MISSING"}
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    p = dst / "metrics.json"
    m = json.loads(p.read_text())
    before = (m.get("exact") or {}).get(key)
    if before is None:
        return {"status": f"{key} ABSENT", "detected": None}
    after = math.nextafter(float.fromhex(before), math.inf).hex()
    m["exact"][key] = after
    p.write_text(json.dumps(m, indent=2))
    base = acceptance(runs, scenario, ref, ref)
    res = acceptance(runs, scenario, ref, f"_acc_{key}")
    return {
        "quantity": key,
        "value_hex_before": before,
        "value_hex_after": after,
        "status_unperturbed": base["status"],
        "status_perturbed": res["status"],
        "quantities_compared": res.get("quantities_compared"),
        "denominator_acceptance_quantities": res.get(
            "denominator_acceptance_quantities"
        ),
        "detected": base["status"] == "PASS" and res["status"] == "FAIL",
    }


def sensitivity_ifail(runs: Path, scenario: str, ref: str) -> dict:
    """A changed ``ifail`` must flip :func:`acceptance` to FAIL."""
    src, dst = runs / scenario / ref, runs / scenario / "_ifail"
    if not src.exists():
        return {"status": "MISSING"}
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    p = dst / "metrics.json"
    m = json.loads(p.read_text())
    before = (m.get("mfile") or {}).get("ifail")
    m["mfile"]["ifail"] = (before or 0) + 1
    p.write_text(json.dumps(m, indent=2))
    res = acceptance(runs, scenario, ref, "_ifail")
    return {
        "ifail_before": before,
        "ifail_after": m["mfile"]["ifail"],
        "status_perturbed": res["status"],
        "detected": res["status"] == "FAIL",
    }


def sensitivity_drop_census() -> dict:
    """The census must find every drop reason, and must not invent one.

    Synthetic starts, because the census's job is bookkeeping over outcomes
    rather than anything PROCESS computes: five starts, one clean, one crashed,
    one with ``ifail = 5``, one whose ``norm_objf`` differs by one ULP, and one
    kept but with non-positive net electric power (issue I-12).
    """

    def row(start, *, status="ok", ifail=1, objf=1.0, pnet=110.0):
        return {
            "start": start,
            "status": status,
            "mfile": {"ifail": ifail, "p_plant_electric_net_mw": pnet},
            "exact": {"norm_objf": float(objf).hex()},
        }

    one_ulp = math.nextafter(1.0, math.inf)
    a = [
        row("start000"),
        row("start001"),
        row("start002"),
        row("start003"),
        row("start004", pnet=-2.0),
    ]
    b = [
        row("start000"),
        row("start001", status="crashed"),
        row("start002", ifail=5),
        row("start003", objf=one_ulp),
        row("start004", pnet=-2.0),
    ]
    census = drop_census({"arm_a": a, "arm_b": b})
    null = drop_census({"arm_a": a, "arm_b": list(a)})
    ratio = cost_comparison(census, {"arm_a": {}, "arm_b": {}})
    # The ifail census over the same synthetic sets.  This is the check that
    # found the histogram-key defect: the MFILE parser returns ``ifail`` as a
    # float, so a census keyed on ``str(ifail)`` reported ``n_ifail_1 = 0``
    # over five starts that all had ``ifail = 1``.
    cen_a = ifail_census([dict(r, mfile=dict(r["mfile"], ifail=float(r["mfile"]["ifail"]))) for r in a])
    cen_b = ifail_census(b)
    return {
        "ifail_census_float_keyed_input": cen_a,
        "ifail_census_counts_successes": cen_a["n_ifail_1"] == 5,
        "ifail_census_mixed_input": cen_b,
        "ifail_census_counts_failures": (
            cen_b["n_ifail_1"] == 3 and cen_b["n_crashed"] == 1
        ),
        "denominator_starts_offered": census["denominator_starts_offered"],
        "counts": census["counts"],
        "n_kept": census["n_kept"],
        "n_kept_but_degenerate_entry_I12": census["n_kept_but_degenerate_entry_I12"],
        "null_case_counts": null["counts"],
        "ratio_reports_its_population": ratio["n_starts_in_ratio"]
        == census["n_kept"]
        and ratio["drop_census"]["denominator_starts_offered"] == 5,
        "detected": (
            census["counts"] == {"crashed": 1, "ifail_not_1": 1, "kept": 2, "objf_mismatch": 1}
            and census["n_kept_but_degenerate_entry_I12"] == 1
            and null["counts"] == {"kept": 5}
            and null["n_kept_but_degenerate_entry_I12"] == 1
            and cen_a["n_ifail_1"] == 5
            and cen_b["n_ifail_1"] == 3
            and cen_b["n_crashed"] == 1
        ),
    }


def sensitivity_residual_identity() -> dict:
    """The extracted residual must be zero at the extracted root, exactly.

    The one thing the bit-identity gate cannot see, because the default path
    never calls the residual.  Checked over pseudo-random inputs at full
    double precision, no tolerance: ``burn_time_residual(burn_time_root(u), u)``
    must be ``0.0``, and must be non-zero one ULP away from the root.
    """
    try:
        from process.models.pulse import burn_time_residual, burn_time_root
    except ImportError as exc:  # pragma: no cover - reported, not raised
        return {"status": f"IMPORT FAILED: {exc}"}

    import random

    rng = random.Random(20260901)
    n, bad, blind = 0, 0, 0
    for _ in range(100_000):
        vs = rng.uniform(-1e4, 1e4)
        v = rng.uniform(-1e2, 1e2)
        tr = rng.uniform(-1e3, 1e3)
        if v == 0.0:
            continue
        root = burn_time_root(vs, v, tr)
        if not math.isfinite(root):
            continue
        n += 1
        if burn_time_residual(root, vs, v, tr) != 0.0:
            bad += 1
        nudged = math.nextafter(root, math.inf)
        if nudged != root and burn_time_residual(nudged, vs, v, tr) == 0.0:
            blind += 1
    return {
        "denominator_input_triples": n,
        "residual_nonzero_at_root": bad,
        "residual_zero_one_ulp_off_root": blind,
        "detected": n > 0 and bad == 0 and blind == 0,
    }


# ---------------------------------------------------------------------------
# A24's bundle gate
# ---------------------------------------------------------------------------

#: A24's arms.  ``parent`` is a ``git archive`` of this branch's parent commit,
#: in which none of the three scaffolding pieces exists.  ``default`` is this
#: branch with every new switch unset.  The whole bundle is inert, so the two
#: must be bit-identical.
A24_ARMS = ("parent", "default")


def bundle_gate(runs: Path, scenarios: list[str]) -> dict:
    return {
        "gate_bit_identity_default_vs_parent": {
            s: compare_pair(runs, s, "parent", "default") for s in scenarios
        },
        "gate_bit_identity_default_vs_parent_probe_on": {
            s: compare_pair(runs, s, "parent_probe", "default_probe")
            for s in scenarios
        },
        "gate_acceptance_default_vs_parent": {
            s: acceptance(
                runs,
                s,
                "parent",
                "default",
                report_fields=("arch_lift_sites", "arch_hoist_name", "tree_git_head"),
            )
            for s in scenarios
        },
        "feasibility_audit": {
            s: {a: feasibility_audit(runs, s, a) for a in A24_ARMS} for s in scenarios
        },
        "matched_final_accuracy": {
            s: matched_accuracy(runs, s, A24_ARMS) for s in scenarios
        },
        "seam_neutrality": {
            s: seam_neutrality(runs, s, (*A24_ARMS, "parent_probe", "default_probe"))
            for s in scenarios
        },
        "robustness_ifail_across_starts": {
            s: {a: ifail_census(collect_starts(runs, s, a)) for a in A24_ARMS}
            for s in scenarios
        },
        "drop_census": {
            s: drop_census({a: collect_starts(runs, s, a) for a in A24_ARMS})
            for s in scenarios
        },
        "sweeps": {
            s: {
                a: {
                    "sweeps_total": ((load(runs, s, a) or {}).get("probe") or {}).get(
                        "sweeps_total"
                    ),
                    "call_models_total": (
                        (load(runs, s, a) or {}).get("probe") or {}
                    ).get("call_models_total"),
                    "n_model_calls": (load(runs, s, a) or {}).get("n_model_calls"),
                    "n_solver_iterations": (load(runs, s, a) or {}).get(
                        "n_solver_iterations"
                    ),
                }
                for a in ("parent_probe", "default_probe")
            }
            for s in scenarios
        },
    }


def bundle_sensitivity(runs: Path, scenarios: list[str]) -> dict:
    return {
        "bit_comparator_one_ulp": {
            s: sensitivity_bit_comparator(runs, s, "parent") for s in scenarios
        },
        "bit_comparator_cross_scenario": sensitivity_cross_scenario(
            runs, scenarios[0], scenarios[1], "parent"
        )
        if len(scenarios) > 1
        else {"status": "NEEDS TWO SCENARIOS"},
        "acceptance_one_ulp_norm_objf": {
            s: sensitivity_acceptance(runs, s, "parent", "norm_objf") for s in scenarios
        },
        "acceptance_one_ulp_sqsumsq": {
            s: sensitivity_acceptance(runs, s, "parent", "sqsumsq") for s in scenarios
        },
        "acceptance_ifail_changed": {
            s: sensitivity_ifail(runs, s, "parent") for s in scenarios
        },
        "drop_census_synthetic": sensitivity_drop_census(),
        "residual_identity": sensitivity_residual_identity(),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("gate", "sensitivity"))
    ap.add_argument("--runs", default=str(HERE / "runs" / "a24"))
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    args = ap.parse_args()
    runs = Path(args.runs).resolve()

    if args.command == "gate":
        result = bundle_gate(runs, args.scenarios)
        out = runs / "_gates_a24.json"
    else:
        result = bundle_sensitivity(runs, args.scenarios)
        out = runs / "_gate_sensitivity_a24.json"
    out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
