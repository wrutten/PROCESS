#!/usr/bin/env python
"""The loosest loop tolerance at which the evaluation error stays below the optimiser's tolerance, and what each loop costs there.

Task A104 (st-stall-mechanism), measurement **M4**.  No PROCESS run: this reads
the records ``evaluation_error_at_optimum.py`` (M2) and
``loop_sweeps_against_reference.py`` (M0) made, through their own readers.

The condition (declared in M2's docstring before any number was read): a loop at
a tolerance is **sufficient** on a configuration when its optimiser-relevant error
at the optimum -- the larger of the base-point value error (objective, every
constraint) and the finite-difference derivative error (objective, every
constraint), largest over the columns -- lies below that configuration's
``epsvmc``, at the step in question.  "Loosest" is on M2's grid (census 1e-8,
1e-10, 1e-12; write set 1e-6, 1e-8); a loop sufficient at no grid value reads
"none on the grid".  Every design point of the configuration must satisfy it.

Then, per configuration: the cost of each loop at its loosest sufficient
tolerance, as M0's mean node calls per evaluation over the stencil entries (the
optimiser-like entry) and over the displaced entries, each against the reference
loop ``AR`` -- the cost at matched delivered accuracy, census against write set,
flat against partitioned.  M0's grid is finer than M2's on the census set; a
tolerance M0 did not run is printed as such.

Usage::

    PYTHONDONTWRITEBYTECODE=1 python tolerance_condition.py
"""

from __future__ import annotations

import sys

import evaluation_error_at_optimum as m2
import loop_sweeps_against_reference as m0
from loop_runs import EPSVMC, SHORT, Loop


def optimiser_relevant(e: dict, h: float) -> float | None:
    if not e.get("ok") or h not in e.get("per_step", {}):
        return None
    st = e["per_step"][h]
    return max(e["base_f"], e["base_c"], st["grad_err_f"], st["grad_err_c"])


def fmt(v, spec=".2f"):
    return "—" if v is None else format(v, spec)


def main() -> int:
    names = [n for n in m2.DESIGN_POINTS]
    print("## M4 — the loosest sufficient tolerance per loop and step, and the cost there\n")
    for name in names:
        eps = EPSVMC[name]
        flat = "A1" if m2.pulsed(name) else "A0"
        # per loop: worst optimiser-relevant error over the design points, per step
        worst: dict[tuple[str, float], float | None] = {}
        steps_all: set[float] = set()
        for arm, seed, steps in m2.DESIGN_POINTS[name]:
            point = m2.point_label(arm, seed)
            try:
                opt = m2.optimum(name, arm, seed)
            except SystemExit:
                continue
            n = len(opt["xcs"])
            cache: dict = {}
            for loop in m2.loops_for(name):
                if loop in (m2.EXACT[name], m2.EXACT_CHECK[name]) or (loop.arm == "A0" and m2.pulsed(name) and loop.tau == 1e-14):
                    continue
                try:
                    e = m2.errors(name, point, loop, n, cache)
                except Exception as exc:  # noqa: BLE001 - an unmade point is reported, not raised
                    e = {"ok": False, "why": str(exc)}
                for h in steps:
                    steps_all.add(h)
                    v = optimiser_relevant(e, h)
                    key = (loop.label, h)
                    if key not in worst:
                        worst[key] = v
                    elif worst[key] is not None:
                        worst[key] = None if v is None else max(worst[key], v)
        m0_stats = {}
        try:
            cells = m0.summarise(name)
            for label, per in cells.items():
                m0_stats[label] = {
                    k: m0.cell_stats([r for r in per.values() if r["entry_kind"] == k])
                    for k in ("displaced", "stencil")
                }
        except Exception as exc:  # noqa: BLE001
            print(f"(M0 records not readable for {name}: {exc})")
        print(f"### {name} ({SHORT[name]}), epsvmc {eps:g}\n")
        print("Optimiser-relevant error at the optimum (worst over the design points) / epsvmc, per loop and step:\n")
        print("| loop | " + " | ".join(f"h = {h:g}" for h in sorted(steps_all, reverse=True)) + " |")
        print("|---|" + "---|" * len(steps_all))
        labels = sorted({k[0] for k in worst}, key=lambda s: (s != "AR", s.split()[1] if " " in s else "", s.split()[0], -float(s.split()[-1]) if " " in s else 0))
        for label in labels:
            cells_txt = []
            for h in sorted(steps_all, reverse=True):
                v = worst.get((label, h))
                cells_txt.append("—" if v is None else f"{v / eps:.2g}")
            print(f"| {label} | " + " | ".join(cells_txt) + " |")
        print()
        ref = {k: (m0_stats.get("AR", {}).get(k) or {}).get("node_calls_mean") for k in ("stencil", "displaced")}
        print("The loosest sufficient tolerance on M2's grid, and M0's mean node calls per evaluation there against AR "
              "(stencil entries; displaced entries):\n")
        print("| test set | loop | step | loosest sufficient τ | node calls / AR, stencil | node calls / AR, displaced |")
        print("|---|---|---|---|---|---|")
        for ts, taus in (("census", (1e-8, 1e-10, 1e-12)), ("write_set", (1e-6, 1e-8))):
            for arm in (flat, "A2"):
                for h in sorted(steps_all, reverse=True):
                    found = None
                    for t in taus:
                        v = worst.get((Loop(arm, ts, t).label, h))
                        if v is not None and v < eps:
                            found = t
                            break
                    if found is None:
                        print(f"| {ts} | {arm} | {h:g} | none on the grid | — | — |")
                        continue
                    lab = Loop(arm, ts, found).label
                    st = m0_stats.get(lab)
                    rs = None if not st else st["stencil"]["node_calls_mean"]
                    rd = None if not st else st["displaced"]["node_calls_mean"]
                    print(f"| {ts} | {arm} | {h:g} | {found:.0e} | "
                          f"{fmt(None if rs is None or not ref['stencil'] else rs / ref['stencil'])} | "
                          f"{fmt(None if rd is None or not ref['displaced'] else rd / ref['displaced'])} |")
        v = worst.get(("AR", sorted(steps_all, reverse=True)[0])) if steps_all else None
        print(f"\nThe reference loop AR at the default step: optimiser-relevant error / epsvmc = "
              f"{'—' if v is None else format(v / eps, '.2g')}.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
