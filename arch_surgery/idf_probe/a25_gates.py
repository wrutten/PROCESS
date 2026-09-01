#!/usr/bin/env python
"""A25's equivalence gate, its teeth, and the H5 analysis.

The gate is **not** bit identity.  A24's bundle was inert, so identity was the
right test there; A25's variant solves a *different problem* -- one more design
variable and one more equality constraint on three of the four decks -- so the
question is whether the two arms land on the same optimum, not whether they
produce the same bits.

What the gate tests, per scenario, reported separately and never pooled
--------------------------------------------------------------------

1. ``ifail`` is 1 in both arms.
2. ``norm_objf`` agrees to **1e-6 relative**.  That number is not chosen here:
   it is PROCESS's own idempotence ``rtol`` (``Caller.check_agreement``) and it
   is Phase A's first tolerance rung, tau.  Stating the source matters because
   a tolerance picked after seeing the numbers is not a gate.  The **achieved**
   difference is reported per deck beside it, so a deck that only just passes
   says so.
3. A **post-solve feasibility audit** on the returned point of each arm:
   equality residuals near zero, inequality violations counted.  Decision D6:
   never on iteration variables.
4. **Matched final accuracy** (plan section 3.3): the arms are compared at the
   residual they *achieved*, never at the tolerance they were asked for.
5. **The variant's own consistency residual** (plan section 2.5, and not
   optional): with the burn time lifted, constraint 93 must be satisfied at the
   returned point, and constraint 93 must actually be in the deck's equality
   block.  Without both, the variant could "win" by returning a point off the
   manifold -- which is what A25's first derived deck did, silently, while
   still reporting ``ifail = 1``.

Cost is reported in **model node calls** -- individual model ``run()``
invocations, Phase A's and A22's unit -- and never in sweeps (a block sweep
runs one module, not all of them) and never in wall clock.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import gates as G  # noqa: E402

SCENARIOS = G.SCENARIOS

#: Relative tolerance on ``norm_objf``.  PROCESS's own ``check_agreement``
#: rtol, and Phase A's first tau rung.  Not chosen here.
OBJF_RTOL = 1.0e-6

#: Absolute ceiling on an equality residual at the returned point.  PROCESS's
#: own VMCON convergence parameter for these decks is ``epsvmc = 1e-8``; the
#: audit uses 1e-6 on the *normalised* residual, which is looser than the
#: solver's own test and therefore cannot be the thing that makes an arm pass.
EQ_RESIDUAL_ATOL = 1.0e-6

#: Relative tolerance on the burn-time consistency residual, as a fraction of
#: the burn time itself.  Same source as OBJF_RTOL.
C93_RTOL = 1.0e-6


def _rel(a, b):
    if a is None or b is None:
        return None
    a, b = float(a), float(b)
    d = abs(a) if abs(a) > 0.0 else 1.0
    return abs(b - a) / d


def _hexf(v):
    return None if v is None else float.fromhex(v)


def gate_scenario(runs: Path, scenario: str, ref: str, arm: str) -> dict:
    mr = G.load(runs, scenario, ref)
    ma = G.load(runs, scenario, arm)
    out: dict = {"scenario": scenario, "arms": {"reference": ref, "variant": arm}}
    if mr is None or ma is None:
        out["status"] = "MISSING"
        out["present"] = {ref: mr is not None, arm: ma is not None}
        return out
    if mr.get("status") != "ok" or ma.get("status") != "ok":
        out["status"] = "FAIL"
        out["fail_reason"] = "a run did not complete"
        out["run_status"] = {ref: mr.get("status"), arm: ma.get("status")}
        return out

    checks: dict[str, dict] = {}

    # -- 1. ifail --------------------------------------------------------
    ir, ia = G._ifail(mr), G._ifail(ma)
    checks["ifail"] = {
        ref: ir, arm: ia,
        "requirement": "1 in both arms",
        "pass": ir == 1 and ia == 1,
    }

    # -- 2. norm_objf ----------------------------------------------------
    orf = _hexf((mr.get("exact") or {}).get("norm_objf"))
    oaf = _hexf((ma.get("exact") or {}).get("norm_objf"))
    if orf is None and oaf is None:
        checks["norm_objf"] = {
            ref: None, arm: None,
            "status": "VOID ON BOTH SIDES",
            "why": "fsolve evaluation run: this solver has no objective",
            "pass": None,
        }
    else:
        rel = _rel(orf, oaf)
        checks["norm_objf"] = {
            ref: orf, arm: oaf,
            "relative_difference": rel,
            "rtol": OBJF_RTOL,
            "rtol_source": "PROCESS's own check_agreement rtol; Phase A's tau",
            "margin_factor": (OBJF_RTOL / rel) if rel else math.inf,
            "pass": rel is not None and rel <= OBJF_RTOL,
        }

    # -- 3. feasibility audit -------------------------------------------
    fa = {a: G.feasibility_audit(runs, scenario, a) for a in (ref, arm)}
    eq_ok = {}
    for a, rec in fa.items():
        v = rec.get("max_abs_equality_residual")
        eq_ok[a] = (v is not None) and abs(v) <= EQ_RESIDUAL_ATOL
    viol = {a: fa[a].get("n_inequalities_violated") for a in (ref, arm)}
    checks["feasibility"] = {
        "per_arm": fa,
        "max_abs_equality_residual_within_atol": eq_ok,
        "equality_residual_atol": EQ_RESIDUAL_ATOL,
        "n_inequalities_violated": viol,
        "requirement": (
            "equality residuals within atol in both arms, and the variant "
            "violates no more inequalities than the reference does -- "
            "COMPARATIVE ONLY on large_tokamak_eval, which is an fsolve "
            "evaluation run with 0 solver iterations and is infeasible in 3 of "
            "its 23 inequalities at its own solution in BOTH arms (A24)"
        ),
        "pass": all(eq_ok.values()) and (
            viol[arm] is not None
            and viol[ref] is not None
            and viol[arm] <= viol[ref]
        ),
    }

    # -- 4. matched final accuracy --------------------------------------
    acc = G.matched_accuracy(runs, scenario, (ref, arm))
    sq = {a: (G.load(runs, scenario, a).get("values") or {}).get("sqsumsq")
          for a in (ref, arm)}
    checks["matched_final_accuracy"] = {
        "sqsumsq": sq,
        "sqsumsq_ratio_variant_over_reference": (
            (sq[arm] / sq[ref]) if sq[ref] else None
        ),
        "conf_l2": {
            a: (G.load(runs, scenario, a).get("values") or {}).get("conf_l2")
            for a in (ref, arm)
        },
        "conf_l2_note": (
            "reported, NOT compared: the constraint vectors have different "
            "lengths (the variant carries one more equality), and conf_l2 is "
            "dominated by satisfied-inequality slack rather than by "
            "infeasibility.  sqsumsq is the accuracy quantity."
        ),
        "matched_accuracy_helper": acc,
        "requirement": (
            "both arms terminate at an equality residual within the audit's "
            "atol; the achieved values are reported rather than assumed equal"
        ),
        "pass": all(eq_ok.values()),
    }

    # -- 5. the variant's own consistency residual -----------------------
    c93 = ma.get("constraint_93")
    if c93 is None:
        checks["constraint_93"] = {
            "status": "NOT APPLICABLE",
            "why": (
                "this deck names no icc = 93 -- st_regression has "
                "i_pulsed_plant = 0, no burn-time coupler, and is run as the "
                "k = 0 control WITHOUT the lift"
            ),
            "pass": None,
        }
    elif "error" in c93:
        checks["constraint_93"] = {"status": "ERROR", "detail": c93, "pass": False}
    else:
        rel = c93.get("residual_relative_to_burn_time")
        checks["constraint_93"] = {
            **c93,
            "rtol": C93_RTOL,
            "pass": bool(
                c93.get("is_in_equality_block")
                and rel is not None
                and rel <= C93_RTOL
            ),
            "requirement": (
                "constraint 93 sits inside the deck's equality block AND its "
                "residual at the returned point is within rtol of the burn "
                "time.  The first half is not pedantry: PROCESS decides which "
                "constraints are equalities by POSITION in icc, so a deck that "
                "appends icc = 93 at the end makes the consistency relation an "
                "inequality and the variant solves a different problem while "
                "still reporting ifail = 1"
            ),
        }

    decided = [k for k, v in checks.items() if v.get("pass") is not None]
    out["status"] = (
        "PASS" if all(checks[k]["pass"] for k in decided) else "FAIL"
    )
    out["checks_decided"] = len(decided)
    out["denominator_checks"] = len(checks)
    out["checks_not_applicable"] = [
        k for k, v in checks.items() if v.get("pass") is None
    ]
    out["checks"] = checks
    out["cost_node_calls"] = {
        a: G.load(runs, scenario, a).get("node_calls_solve_phase")
        for a in (ref, arm)
    }
    out["diagnostics_not_gated"] = {
        a: {
            "nvar": G.load(runs, scenario, a).get("nvar"),
            "n_equality_constraints": G.load(runs, scenario, a).get(
                "n_equality_constraints"
            ),
            "n_inequality_constraints": G.load(runs, scenario, a).get(
                "n_inequality_constraints"
            ),
            "n_solver_iterations": G.load(runs, scenario, a).get(
                "n_solver_iterations"
            ),
            "n_call_models_sweeps": G.load(runs, scenario, a).get("n_model_calls"),
            "module_solve_totals": G.load(runs, scenario, a).get(
                "module_solve_totals"
            ),
            "arch": {
                k: G.load(runs, scenario, a).get(k)
                for k in (
                    "arch_sequence_name", "arch_hoist_name",
                    "arch_hoist_tail_resolved", "arch_lift_sites",
                    "arch_module_solve_name", "arch_module_solve_tau",
                )
            },
        }
        for a in (ref, arm)
    }
    return out


def gate(runs: Path, scenarios) -> dict:
    per = {s: gate_scenario(runs, s, "baseline", "variant") for s in scenarios}
    return {
        "gate": "A25 equivalence gate",
        "baseline": (
            "PROCESS as it currently is (D14(c)): every variant point unset, "
            "existing predicate, existing flat loop, frozen deck"
        ),
        "scenarios_reported_separately": list(scenarios),
        "status_by_scenario": {s: per[s]["status"] for s in scenarios},
        "overall": (
            "PASS"
            if all(per[s]["status"] == "PASS" for s in scenarios)
            else "FAIL"
        ),
        "denominator_scenarios": len(scenarios),
        "per_scenario": per,
    }


# ---------------------------------------------------------------------------
# Teeth (protocol section 12): every gate shown capable of failing
# ---------------------------------------------------------------------------


def _perturb(rec: dict, path: list, value):
    d = rec
    for k in path[:-1]:
        d = d.setdefault(k, {})
    d[path[-1]] = value
    return rec


def sensitivity(runs: Path, scenarios) -> dict:
    """Show each predicate failing on a deliberately corrupted input.

    The **production** predicates are used unmodified; only the data they read
    is perturbed, by the smallest amount that should register.
    """
    import copy
    import tempfile

    out: dict = {}
    src = runs
    s = scenarios[0]

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        def stage(mutate_variant=None, mutate_baseline=None, scenario=s):
            for arm, mut in (("baseline", mutate_baseline), ("variant", mutate_variant)):
                d = tmp / scenario / arm
                d.mkdir(parents=True, exist_ok=True)
                rec = copy.deepcopy(
                    json.loads(
                        (src / scenario / arm / "metrics.json").read_text()
                    )
                )
                if mut:
                    rec = mut(rec)
                (d / "metrics.json").write_text(json.dumps(rec))
            return gate_scenario(tmp, scenario, "baseline", "variant")

        # -- objf: one unit in the last place of norm_objf ---------------
        def ulp(rec):
            v = float.fromhex(rec["exact"]["norm_objf"])
            rec["exact"]["norm_objf"] = math.nextafter(v, math.inf).hex()
            return rec

        base = stage()
        out["baseline_of_the_check_itself"] = {
            "status": base["status"],
            "note": "the unperturbed copy must reproduce the real gate's verdict",
        }
        r = stage(mutate_variant=ulp)
        out["objf_one_ulp"] = {
            "status": r["status"],
            "objf_check_pass": r["checks"]["norm_objf"]["pass"],
            "relative_difference": r["checks"]["norm_objf"]["relative_difference"],
            "detects": "one ULP is far below rtol, so the gate correctly still "
                       "PASSES; the discriminating perturbation is below",
        }

        # -- objf: 2x rtol ----------------------------------------------
        def big(rec):
            v = float.fromhex(rec["exact"]["norm_objf"])
            rec["exact"]["norm_objf"] = (v * (1.0 + 2.0 * OBJF_RTOL)).hex()
            return rec

        r = stage(mutate_variant=big)
        out["objf_twice_rtol"] = {
            "status": r["status"],
            "objf_check_pass": r["checks"]["norm_objf"]["pass"],
            "relative_difference": r["checks"]["norm_objf"]["relative_difference"],
            "must_be": "FAIL",
        }

        # -- ifail -------------------------------------------------------
        def bad_ifail(rec):
            rec["mfile"]["ifail"] = 5.0
            return rec

        r = stage(mutate_variant=bad_ifail)
        out["ifail_not_1"] = {
            "status": r["status"],
            "ifail_check_pass": r["checks"]["ifail"]["pass"],
            "must_be": "FAIL",
        }

        # -- feasibility: one violated inequality ------------------------
        def violate(rec):
            meq = rec["n_equality_constraints"]
            rec["values"]["rcm"][meq] = -1.0
            return rec

        r = stage(mutate_variant=violate)
        out["one_inequality_violated"] = {
            "status": r["status"],
            "feasibility_check_pass": r["checks"]["feasibility"]["pass"],
            "n_inequalities_violated": r["checks"]["feasibility"][
                "n_inequalities_violated"
            ],
            "must_be": "FAIL",
        }

        # -- feasibility: a blown equality residual ----------------------
        def blow_eq(rec):
            rec["values"]["rcm"][0] = 1.0
            return rec

        r = stage(mutate_variant=blow_eq)
        out["equality_residual_blown"] = {
            "status": r["status"],
            "feasibility_check_pass": r["checks"]["feasibility"]["pass"],
            "accuracy_check_pass": r["checks"]["matched_final_accuracy"]["pass"],
            "must_be": "FAIL",
        }

        # -- constraint 93 off the manifold ------------------------------
        def off_manifold(rec):
            c = rec.get("constraint_93")
            if c:
                c["residual_s"] = 1.0
                c["residual_relative_to_burn_time"] = 1.0 / c["t_plant_pulse_burn_s"]
            return rec

        r = stage(mutate_variant=off_manifold)
        out["constraint_93_off_manifold"] = {
            "status": r["status"],
            "c93_check_pass": r["checks"]["constraint_93"]["pass"],
            "must_be": "FAIL",
            "note": (
                "a 1-second residual on a ~2568 s burn time, i.e. 3.9e-4 "
                "relative -- four hundred times the rtol and still a physically "
                "small number.  This is the check that catches a variant "
                "'winning' off the manifold."
            ),
        }

        # -- constraint 93 in the wrong block ----------------------------
        def wrong_block(rec):
            c = rec.get("constraint_93")
            if c:
                c["is_in_equality_block"] = False
            return rec

        r = stage(mutate_variant=wrong_block)
        out["constraint_93_in_inequality_block"] = {
            "status": r["status"],
            "c93_check_pass": r["checks"]["constraint_93"]["pass"],
            "must_be": "FAIL",
            "note": (
                "this is the real defect A25's first derived deck had, and it "
                "passed every other check"
            ),
        }

        # -- crashed run -------------------------------------------------
        def crash(rec):
            rec["status"] = "crashed"
            return rec

        r = stage(mutate_variant=crash)
        out["variant_crashed"] = {"status": r["status"], "must_be": "FAIL"}

        # -- two genuinely different scenarios ---------------------------
        d = tmp / "cross" / "baseline"
        d.mkdir(parents=True, exist_ok=True)
        (d / "metrics.json").write_text(
            (src / scenarios[0] / "baseline" / "metrics.json").read_text()
        )
        d = tmp / "cross" / "variant"
        d.mkdir(parents=True, exist_ok=True)
        (d / "metrics.json").write_text(
            (src / scenarios[1] / "baseline" / "metrics.json").read_text()
        )
        r = gate_scenario(tmp, "cross", "baseline", "variant")
        out["two_different_scenarios"] = {
            "status": r["status"],
            "pair": [scenarios[0], scenarios[1]],
            "objf_relative_difference": r["checks"]["norm_objf"][
                "relative_difference"
            ],
            "must_be": "FAIL",
        }

    verdicts = {
        k: v for k, v in out.items()
        if isinstance(v, dict) and v.get("must_be")
    }
    out["_summary"] = {
        "n_checks_that_must_fail": len(verdicts),
        "n_that_did_fail": sum(
            1 for v in verdicts.values() if v["status"] == "FAIL"
        ),
        "all_teeth_bite": all(v["status"] == "FAIL" for v in verdicts.values()),
    }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["gate", "sensitivity"])
    ap.add_argument("--runs", required=True)
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    runs = Path(args.runs).resolve()
    if args.command == "gate":
        res = gate(runs, args.scenarios)
        name = "_gate_a25.json"
    else:
        res = sensitivity(runs, args.scenarios)
        name = "_gate_sensitivity_a25.json"
    dest = Path(args.out) if args.out else runs / name
    dest.write_text(json.dumps(res, indent=2, default=str))
    print(json.dumps(res, indent=2, default=str)[:6000])
    print(f"\\n-> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
