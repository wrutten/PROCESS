#!/usr/bin/env python
"""The evaluation error of each loop at an optimum, split into the part neighbouring evaluations share and the part they do not.

Task A104 (st-stall-mechanism), measurement **M2**.

The design point
----------------
A converged optimum of the campaign's flat arm ``B0`` (census set, τ = 1e-8): its
final design vector (``exact.xcs``, hex) and the coupling state the optimisation
ended in (``y_before_finalise.json``: the exit of its last evaluation, the
reconcile call at that design vector).  Both read only from
``runs/campaign/optimisation/<c>/B0/seed<s>/``.  The design vector enters the
evaluation child through a **derived input file** -- the committed input file with
each iteration variable's line set to the optimum's value (``repr``, exact) and
``epsfcn`` set to the step -- written under this task's runs root; the committed
input file is never edited (D9).  On a pulsed configuration the constant-owning
arms are pinned at the burn time of that coupling state.

The evaluations (``--press``), per loop, mimicking the optimiser's evaluator
---------------------------------------------------------------------------
* **base** -- at the optimum, entered from the optimisation's own final state;
* **+h, column c** -- one iteration variable multiplied by ``1 + h`` (the
  harness's stencil regime, ``h`` = ``epsfcn`` of the derived input file),
  entered from this loop's base exit (the converged state with one variable
  displaced);
* **-h, column c** -- multiplied by ``1 - h``, entered from the +h point's exit,
  which is the order ``Evaluators.fcnvmc2`` evaluates them in;

for every column, at h = 1e-3 (PROCESS's default, the campaign's) and, on st, 1e-4
(:data:`DESIGN_POINTS`).

Loops: the reference ``AR``; the flat ``A0`` (``A1`` on a pulsed configuration,
the partitioned arm's comparator) and the partitioned ``A2`` under the census set
at τ = 1e-8, 1e-10, 1e-12 and under the whole write set at τ = 1e-6, 1e-8; and the
**exact** value, the flat loop at the tightest census τ M0 found every entry to
terminate at on this configuration (:data:`EXACT`).  How exact the exact value is
is measured, not assumed: a second tight loop (:data:`EXACT_CHECK`) is run through
the same chain and the two are compared.

What is computed (``--tables``)
-------------------------------
Against the exact loop, at every point: ``e_f`` (objective, absolute; the
optimiser's objective is ``objf`` as ``call_models`` returns it) and ``e_c`` (every
constraint, absolute: PROCESS's constraints are normalised).  Per column and
step: the finite-difference derivative with respect to ``ln x_c`` (the scaled
variable, ``(f(+) - f(-)) / 2h``) and its error, which is exactly the **non-common
part** ``(e(+) - e(-)) / 2`` divided by ``h``; the **common part** ``(e(+) + e(-)) / 2``
cancels in the difference.  Tabled per loop: the base error, the largest common
and non-common parts over the columns, and the largest derivative error, for the
objective and the constraints, at each step.

The optimiser-relevant error (declared here, before any number was read): the
larger of the base-point value error (objective and constraints) and the
finite-difference derivative error, each against the configuration's ``epsvmc``
-- the measure VMCON stops on (``|∇f·δ| + |Σλ c|``) is built from exactly those
values and derivatives.  It is a proxy: the Lagrange multipliers and the step,
which weight them, are not recorded.  M1's records are its test: the proxy must
put ``BR``, ``B0`` at 1e-8 and ``B2`` at 1e-12 (no excess hovering) on one side and
``B2`` at 1e-8 (hovering) on the other; if it does not, the report says so.

Usage::

    PYTHONDONTWRITEBYTECODE=1 python evaluation_error_at_optimum.py --press --configuration st_regression
    PYTHONDONTWRITEBYTECODE=1 python evaluation_error_at_optimum.py --tables [--json out.json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from loop_runs import (
    CAMPAIGN_RUNS,
    EPSVMC,
    REFERENCE,
    ROOT,
    SHORT,
    Loop,
    campaign_for,
    config_of,
    epsvmc_of,
    evaluation_job,
    press,
    read_evaluation,
    records_mod,
    V5,
)

ERROR_ROOT = ROOT / "evaluation_error"
#: (arm, seed, steps) of each optimum used, per configuration: both steps at st's
#: first optimum; the default step alone elsewhere (the run budget: each step is 2n
#: evaluations per loop, about 6 s each at two workers).
DESIGN_POINTS = {
    "st_regression": [("B0", 0, (1e-3, 1e-4)), ("B0", 8, (1e-3,))],
    "large_tokamak_nof": [("B0", 0, (1e-3,))],
    "low_aspect_ratio_DEMO": [("B0", 0, (1e-3,))],
}
#: The exact value and its check, per configuration (the tightest census τ at which
#: every M0 entry of the flat loop terminated; set from M0's tables).
EXACT = {
    "st_regression": Loop("A0", "census", 1e-14),
    "large_tokamak_nof": Loop("A1", "census", 1e-14),
    "low_aspect_ratio_DEMO": Loop("A1", "census", 1e-14),
}
EXACT_CHECK = {
    "st_regression": Loop("A2", "census", 1e-14),
    "large_tokamak_nof": Loop("A2", "census", 1e-14),
    "low_aspect_ratio_DEMO": Loop("A2", "census", 1e-14),
}


def pulsed(name: str) -> bool:
    return name != "st_regression"


def loops_for(name: str) -> list[Loop]:
    flat = "A1" if pulsed(name) else "A0"
    out = [REFERENCE]
    out += [Loop(a, "census", t) for t in (1e-8, 1e-10, 1e-12) for a in (flat, "A2")]
    out += [Loop(a, "write_set", t) for t in (1e-6, 1e-8) for a in (flat, "A2")]
    out += [EXACT[name], EXACT_CHECK[name]]
    if pulsed(name):
        out += [Loop("A0", "census", 1e-14)]
    seen, uniq = set(), []
    for lp in out:
        if lp not in seen:
            seen.add(lp)
            uniq.append(lp)
    return uniq


def exact_for(name: str, loop: Loop) -> Loop:
    """The exact loop a loop's error is taken against: the pinned one for a pinned arm."""
    if loop.arm in ("AR", "A0"):
        return Loop("A0", "census", 1e-14) if pulsed(name) else EXACT[name]
    return EXACT[name]


def optimum(name: str, arm: str, seed: int) -> dict:
    d = CAMPAIGN_RUNS / "optimisation" / name / arm / f"seed{seed:03d}"
    rec = records_mod.read(d)
    if rec.get("status") != "ok" or (rec.get("mfile") or {}).get("ifail") != 1:
        raise SystemExit(f"{d}: not an accepted optimum")
    xcs = [float.fromhex(h) for h in rec["exact"]["xcs"]]
    names = rec["itvar_names"]
    state = json.loads((d / "y_before_finalise.json").read_text())
    burn = (state["state"].get("times.t_plant_pulse_burn") or {}).get("hex")
    return {
        "dir": d,
        "xcs": xcs,
        "names": names,
        "norm_objf": float.fromhex(rec["exact"]["norm_objf"]),
        "state_path": d / "y_before_finalise.json",
        "burn_hex": burn,
        "input_file": Path(rec["campaign_input_file"]).name,
    }


def point_label(arm: str, seed: int) -> str:
    return f"{arm}_seed{seed:03d}"


def derived_input(name: str, opt: dict, step: float, where: Path) -> Path:
    """The committed input file with the optimum's design vector and the step."""
    text = (V5 / "harness" / "data" / f"{name}.IN.DAT").read_text().splitlines()
    out = []
    set_names = set()
    for line in text:
        m = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*(?:\(\d+\))?)\s*=", line)
        key = m.group(1) if m else None
        if key in opt["names"]:
            value = opt["xcs"][opt["names"].index(key)]
            out.append(f"{key} = {value!r}")
            set_names.add(key)
            continue
        if key == "epsfcn" or re.match(r"^\s*\*\s*epsfcn\s*=", line):
            continue
        out.append(line)
    missing = [n for n in opt["names"] if n not in set_names]
    for n in missing:
        out.append(f"{n} = {opt['xcs'][opt['names'].index(n)]!r}")
    out.append(f"epsfcn = {step!r}")
    where.mkdir(parents=True, exist_ok=True)
    path = where / f"{name}_step{step:.0e}.IN.DAT"
    path.write_text("\n".join(out) + "\n")
    return path


def base_dir(name, point, loop):
    return ERROR_ROOT / name / point / loop.slug / "base"


def stencil_dir(name, point, loop, step, column, sign):
    s = "+" if sign > 0 else "-"
    return ERROR_ROOT / name / point / loop.slug / f"step{step:.0e}" / f"col{column:02d}{s}"


def jobs_for_stage(name: str, stage: str, points=None) -> dict[Loop, list]:
    groups: dict[Loop, list] = {}
    for arm, seed, steps in DESIGN_POINTS[name]:
        opt = optimum(name, arm, seed)
        point = point_label(arm, seed)
        if points and point not in points:
            continue
        inputs = {h: derived_input(name, opt, h, ERROR_ROOT / name / point / "input") for h in steps}
        n = len(opt["xcs"])
        for loop in loops_for(name):
            campaign = campaign_for(loop, ERROR_ROOT)
            pin = opt["burn_hex"] if (pulsed(name) and loop.arm in ("A1", "A2")) else None
            if stage == "base":
                config = config_of(campaign, name, inputs[steps[0]])
                groups.setdefault(loop, []).append(evaluation_job(
                    campaign, config, loop, base_dir(name, point, loop),
                    entry_state=opt["state_path"], pin_hex=pin,
                ))
                continue
            for h in steps:
                config = config_of(campaign, name, inputs[h])
                for c in range(n):
                    if stage == "plus":
                        entry = base_dir(name, point, loop) / "y_exit.json"
                        sign = 1
                    else:
                        entry = stencil_dir(name, point, loop, h, c, 1) / "y_exit.json"
                        sign = -1
                    groups.setdefault(loop, []).append(evaluation_job(
                        campaign, config, loop, stencil_dir(name, point, loop, h, c, sign),
                        regime="stencil", entry_state=entry, stencil_column=c,
                        stencil_sign=sign, pin_hex=pin,
                    ))
    return groups


# --------------------------------------------------------------------------
# tables
# --------------------------------------------------------------------------


def fmt(v, spec=".1e"):
    if v is None:
        return "—"
    return format(v, spec)


def steps_of(name, point):
    return next(st for a, s, st in DESIGN_POINTS[name] if point_label(a, s) == point)


def read_point(name, point, loop, n):
    base = read_evaluation(base_dir(name, point, loop), loop)
    sten = {}
    for h in steps_of(name, point):
        for c in range(n):
            for sign in (1, -1):
                sten[(h, c, sign)] = read_evaluation(stencil_dir(name, point, loop, h, c, sign), loop)
    return base, sten


def errors(name, point, loop, n, cache):
    ex = exact_for(name, loop)
    if loop not in cache:
        cache[loop] = read_point(name, point, loop, n)
    if ex not in cache:
        cache[ex] = read_point(name, point, ex, n)
    base, sten = cache[loop]
    xbase, xsten = cache[ex]
    out = {"loop": loop.label, "exact": ex.label, "ok": True}
    runs = [base, *sten.values(), xbase, *xsten.values()]
    bad = [r["dir"] for r in runs if r.get("status") != "ok"]
    if bad:
        out["ok"] = False
        out["not_ok"] = bad
        return out

    def ef(a, b):
        return a["objf"] - b["objf"]

    def ec(a, b):
        return [x - y for x, y in zip(a["conf"], b["conf"], strict=True)]

    out["base_f"] = abs(ef(base, xbase))
    out["base_f_rel"] = abs(ef(base, xbase)) / abs(xbase["objf"])
    out["base_c"] = max(abs(v) for v in ec(base, xbase))
    per_step = {}
    for h in steps_of(name, point):
        common_f = noncommon_f = grad_f = 0.0
        common_c = noncommon_c = grad_c = 0.0
        for c in range(n):
            p, m = sten[(h, c, 1)], sten[(h, c, -1)]
            xp, xm = xsten[(h, c, 1)], xsten[(h, c, -1)]
            efp, efm = ef(p, xp), ef(m, xm)
            ecp, ecm = ec(p, xp), ec(m, xm)
            common_f = max(common_f, abs(efp + efm) / 2)
            noncommon_f = max(noncommon_f, abs(efp - efm) / 2)
            grad_f = max(grad_f, abs(efp - efm) / (2 * h))
            for a, b in zip(ecp, ecm, strict=True):
                common_c = max(common_c, abs(a + b) / 2)
                noncommon_c = max(noncommon_c, abs(a - b) / 2)
                grad_c = max(grad_c, abs(a - b) / (2 * h))
        per_step[h] = {
            "common_f": common_f, "noncommon_f": noncommon_f, "grad_err_f": grad_f,
            "common_c": common_c, "noncommon_c": noncommon_c, "grad_err_c": grad_c,
        }
    out["per_step"] = per_step
    out["node_calls_base"] = base.get("node_calls")
    out["node_calls_stencil_mean"] = sum(r.get("node_calls") or 0 for r in sten.values()) / len(sten)
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--press", action="store_true")
    p.add_argument("--tables", action="store_true")
    p.add_argument("--configuration", action="append", default=None)
    p.add_argument("--point", action="append", default=None,
                   help="press only these design points (e.g. B0_seed000); all by default")
    p.add_argument("--json", default=None)
    args = p.parse_args(argv)
    names = tuple(args.configuration or ("st_regression",))
    if args.press:
        for name in names:
            epsvmc_of(name)
            for stage in ("base", "plus", "minus"):
                print(f"=== {name}: stage {stage}", flush=True)
                press(jobs_for_stage(name, stage, args.point), ERROR_ROOT)
    if not args.tables:
        return 0
    result = {}
    for name in names:
        eps = EPSVMC[name]
        for arm, seed, STEPS in DESIGN_POINTS[name]:
            opt = optimum(name, arm, seed)
            point = point_label(arm, seed)
            n = len(opt["xcs"])
            cache: dict = {}
            print(f"\n## {name} ({SHORT[name]}), optimum of {arm} seed {seed}; n = {n}; epsvmc {eps:g}\n")
            # checks: the design point entered, the step, the base objective
            ex = EXACT[name]
            xb, xs = read_point(name, point, ex, n)
            heads = set()
            print(f"optimisation's final norm_objf {opt['norm_objf']!r}; exact loop's base objf "
                  f"{xb.get('objf')!r} (relative difference "
                  f"{fmt(abs(xb['objf'] - opt['norm_objf']) / abs(opt['norm_objf']) if xb.get('objf') is not None else None)})")
            steps_seen = sorted({r.get('epsfcn') for r in xs.values() if r.get('epsfcn') is not None})
            print(f"steps stamped by the stencil records: {steps_seen}\n")
            rows = []
            for loop in loops_for(name):
                e = errors(name, point, loop, n, cache)
                rows.append(e)
                for r in [cache[loop][0], *cache[loop][1].values()]:
                    if r.get("tree_git_head"):
                        heads.add(r["tree_git_head"])
            print(f"records made at: {sorted(heads)}\n")
            print("| loop | against | node calls: base / stencil mean | base: e_f (rel) / max e_c | "
                  + " | ".join(f"h={h:g}: f common / non-common / derivative error" for h in STEPS) + " | "
                  + " | ".join(f"h={h:g}: c common / non-common / derivative error" for h in STEPS)
                  + " | largest derivative error / epsvmc (h=1e-3) |")
            print("|---|---|---|---|" + "---|" * (2 * len(STEPS)) + "---|")
            for e in rows:
                if not e["ok"]:
                    print(f"| {e['loop']} | {e['exact']} | not every run ok: {len(e['not_ok'])} | " + "| " * (2 * len(STEPS) + 1))
                    continue
                fs = " | ".join(
                    f"{fmt(e['per_step'][h]['common_f'])} / {fmt(e['per_step'][h]['noncommon_f'])} / {fmt(e['per_step'][h]['grad_err_f'])}"
                    for h in STEPS)
                cs = " | ".join(
                    f"{fmt(e['per_step'][h]['common_c'])} / {fmt(e['per_step'][h]['noncommon_c'])} / {fmt(e['per_step'][h]['grad_err_c'])}"
                    for h in STEPS)
                worst = max(e["per_step"][STEPS[0]]["grad_err_f"], e["per_step"][STEPS[0]]["grad_err_c"])
                print(f"| {e['loop']} | {e['exact']} | {e['node_calls_base']} / {e['node_calls_stencil_mean']:.1f} | "
                      f"{fmt(e['base_f'])} ({fmt(e['base_f_rel'])}) / {fmt(e['base_c'])} | {fs} | {cs} | {worst / eps:.2g} |")
            result.setdefault(name, {})[point] = rows
            # how each block loop ended at the stencil points: sweeps, and the first sweep's change
            print("\nAt the stencil points (every column, both signs, every step): per block, the "
                  "evaluations whose block loop stopped after its **first** sweep, and the first sweep's "
                  "largest scaled change on the block's test set, median [min, max]:\n")
            print("| loop | block: stopped after one sweep / evaluations; first-sweep change median [min, max] |")
            print("|---|---|")
            import statistics  # noqa: PLC0415
            for loop in loops_for(name):
                if loop.arm == "AR" or loop not in cache:
                    continue
                per_block: dict = {}
                for r in cache[loop][1].values():
                    for b, vals in (r.get("residual_per_sweep") or {}).items():
                        d = per_block.setdefault(b, {"one": 0, "n": 0, "first": []})
                        d["n"] += 1
                        d["one"] += 1 if len(vals) == 1 else 0
                        d["first"].append(vals[0])
                txt = "; ".join(
                    f"{b}: {d['one']}/{d['n']}; {statistics.median(d['first']):.1e} "
                    f"[{min(d['first']):.1e}, {max(d['first']):.1e}]"
                    for b, d in per_block.items()
                )
                print(f"| {loop.label} | {txt} |")
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(result, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
