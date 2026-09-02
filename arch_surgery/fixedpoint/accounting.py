#!/usr/bin/env python
"""One accounting for model evaluations.  This module is the only definition.

§6.2 of the results report found the study quoting **two** hoist figures that
are not the same measurement --- the driver's 6.56 / 6.76 / 6.64 / 2.63 % and
the replay engine's −6.38 / −6.55 / −13.70 / −5.71 % --- for three separate
reasons, only one of which was ever a defect.  A26 settles it.

The canonical figure is the driver's
--------------------------------------

**The number this study quotes is measured in PROCESS's own driver, over a
whole optimisation run, gated on bit-identity of the entire output file.**  Not
because it is more accurate --- both are exact counts --- but because it is
what a user of PROCESS would actually get, and because it is the one that is
gated on the answer being unchanged.  The replay engine's figure is a
**cross-check** and is reported as one.  It never shares a column or a sentence
with the canonical figure without the accounting stated.

The three reasons they differ, and what happened to each
--------------------------------------------------------

1. **Different populations.**  The driver counts a whole optimisation ---
   2 029 / 4 286 / 1 891 sweeps.  The engine counts the recorded design points:
   every point the optimiser visited, and one in five of its finite-difference
   perturbations.  **Unchanged, and not a defect**: they are two populations by
   design, and that is the point of a cross-check.  It has to be stated at
   every quotation.

2. **Different model sets on one deck** (I-13).  The engine had no
   predicate-layer guard, so on ``large_tokamak_eval`` it hoisted
   ``water_use`` *and* ``costs`` where the driver hoisted ``water_use`` alone.
   **Removed by A26**: the routing rule in :mod:`fixedpoint.arms` is derived
   from the driver's own read set, so the two instruments resolve the same node
   set on every deck.  (That deck is also dropped from the study, D17 --- but
   the fix is not the drop.)

3. **Different accounting.**  The engine's headline model-evaluation total
   counts **in-loop models only** and records the post-loop tail runs in a
   separate field, so it reported −9.52 % where the comparable number is
   −6.38 %.  **Fixed here, in one place**: :func:`net_model_evaluations` is
   what any A26-or-later analysis calls, and it adds the tails back.

The definition
--------------

For one design point and one arm::

    net model evaluations
        = in-loop model calls
        + pre-predicate tail calls      (run once, before objf/conf)
        + post-predicate tail calls     (run once, after conf)

The **exit audit's** extra sweep is *not* included and never is: it is an
instrument, identical across arms at a given setting, and charging it to an arm
would count the measurement as part of what is measured.  It is reported
separately, by name.

Everything a comparison is quoted in is this quantity.  ``module_sweeps`` and
``sweeps`` remain reported --- they say something different, and the hoist is
precisely the effect that a sweep count values at zero (§4.4.3).

Which arm pairs the unit is meaningful across
----------------------------------------------

Model evaluations are commensurable between **any** two arms, because a model
call is a model call whatever loop it sits in --- that is exactly why the unit
was chosen over sweeps, which count a flat pass and a per-block pass as the
same thing when they are not.  What is *not* commensurable is what the arms
are converging, and a cost ratio between two arms that stop on different tests
carries that difference inside it.  Stated per pair, for the three-arm Phase B
(decision D18) and for Phase A's four:

======================  ==================================================
pair                    what its cost ratio contains
======================  ==================================================
``R -> A0`` / ``A0'``   the **predicate's** cost.  R stops on ``objf`` and
                        ``conf`` under ``allclose``; the flat control stops
                        on the coupling state at tau.  Cheaper is not better
                        here --- they stop at different accuracies, and the
                        exit audit is what says by how much
``A0 -> A1``            the **architecture**, one predicate, one accuracy
``A0' -> A1'``          measure.  This is the comparison a headline may use
``R -> A1`` / ``A1'``   both at once.  Legitimate as *the user-facing
                        figure* --- it is what a user would actually see ---
                        and never as the architecture's cost
``A0f -> A0``           the two-sweep floor alone
``R -> A0f``            the predicate alone, floor held
======================  ==================================================

**Iteration counts are never comparable between arms of different dimension**
(§7): the lifted variant solves a problem with one more design variable, so
its optimiser iterations are a diagnostic and not a cost.
"""

from __future__ import annotations

#: The fields a result dict carries, and what each one counts.  Published in
#: every rollup so a reader never has to infer the accounting from a number.
FIELDS = {
    "node_calls": "model evaluations inside the loop, all sweeps",
    "hoist_tail_node_calls": (
        "model evaluations in the hoisted tails, run once each after "
        "convergence (pre-predicate group then post-predicate group)"
    ),
    "audit_node_calls": (
        "the exit audit's one extra full sweep -- an instrument, identical "
        "across arms, never charged to an arm"
    ),
}


def net_model_evaluations(arm_result: dict) -> int:
    """The canonical per-design-point cost of one arm.

    In-loop model calls plus the hoisted tails.  The exit audit is excluded by
    construction; see the module docstring.
    """
    return int(arm_result.get("node_calls", 0)) + int(
        arm_result.get("hoist_tail_node_calls", 0) or 0
    )


def total_net_model_evaluations(points, arm: str) -> int:
    """Summed over a population of design points, for one arm."""
    return sum(net_model_evaluations(p["arms"][arm]) for p in points)


def accounting_record(points, arms) -> dict:
    """The three components, per arm, so a reader can re-derive any ratio.

    Reporting the components rather than only the total is what makes the
    engine's −9.52 % and its −6.38 % visibly the same measurement under two
    accountings, instead of two numbers a reader has to reconcile.
    """
    out = {
        "definition": (
            "net model evaluations = in-loop calls + pre-predicate tail + "
            "post-predicate tail; the exit audit is excluded"
        ),
        "fields": dict(FIELDS),
        "n_points": len(points),
        "per_arm": {},
    }
    for a in arms:
        in_loop = sum(int(p["arms"][a].get("node_calls", 0)) for p in points)
        tail = sum(
            int(p["arms"][a].get("hoist_tail_node_calls", 0) or 0)
            for p in points
        )
        audit = sum(
            int((p["arms"][a].get("audit") or {}).get("audit_node_calls", 0))
            for p in points
        )
        out["per_arm"][a] = {
            "in_loop_model_evaluations": in_loop,
            "tail_model_evaluations": tail,
            "net_model_evaluations": in_loop + tail,
            "audit_model_evaluations_not_charged": audit,
        }
    return out
