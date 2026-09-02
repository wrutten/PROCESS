#!/usr/bin/env python
"""A28's analysis: the manifests, the equivalence gate, the ladder, H5.

Everything here is a **count or a bit-comparison**.  Wall clock is read in
exactly one place --- :func:`timings`, which reports a median with an interval,
a repetition count and each run's position in the sequence, and refuses to form
a ratio between arms.  Issue I-10 measured identical work varying by up to 35 %
in CPU-seconds on this machine with the cause unknown; A26 measured a p10-p90
band of 50-143 % of the median against 4 % effects.  No conclusion in this
study rests on a timing.

Order of reporting is fixed and is not a style choice
-----------------------------------------------------
**Manifests, then the gates, then robustness, then the drop census, then any
ratio.**  An architecture that is cheaper on the starts it solves and fails on
more of them has not won (plan §2.5), and a ratio over a quietly smaller
population is trap T11, which this project has published three times.

What the three comparisons contain
----------------------------------
``A0' -> A1'``  the architecture, at matched predicate.  **The headline.**
``R -> A1'``    architecture plus stopping rule.  The user-facing figure only.
``R -> A0'``    the stopping rule alone.

Naming (plan §7a, decision D15(b)): the variant carries the per-module solves,
the burn-time lift **and** the feed-forward hoist, so its headline is *the
proposed architecture* and never *the partition's benefit*.  The hoist is
separable and ``A1p_nohoist`` measures it separately, inside this architecture
rather than in the flat one A13 measured it in.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TREE / "arch_surgery" / "fixedpoint"))

import gates as G  # noqa: E402
import manifest as MF  # noqa: E402
from a25_gates import OBJF_RTOL, gate_scenario  # noqa: E402
from a25_h5 import calibration, compare  # noqa: E402
from accuracy import ACCURACY_STAT, compare as acc_compare, curve  # noqa: E402
from run_a28 import CORE_ARMS, PULSED, SCENARIOS, TAU  # noqa: E402

#: The canonical label of a schedule that is one block over every in-loop node.
_ALL = "ALL_IN_LOOP_NODES"

#: The arm labels, spelled the way the reports spell them.
PRETTY = {
    "R": "R (PROCESS as shipped)",
    "A0p": "A0' (predicate-matched flat control)",
    "A1p": "A1' (the proposed architecture)",
    "A0p_reordered": "A0' with build after physics (diagnostic)",
    "A1p_nohoist": "A1' without the hoist (diagnostic)",
}


# ---------------------------------------------------------------------------
# 1.  Manifests: a comparison that cannot say what it varies does not run
# ---------------------------------------------------------------------------


def descriptor(m: dict, arm: str) -> dict:
    """What an arm was actually built from, read out of its own run record.

    Read from what the run **resolved** --- the imported modules, the committed
    node map, the deck's own figure of merit --- and never from what the driver
    asked for.  An arm that silently failed to select its variant point would
    otherwise describe itself as the arm it meant to be.

    Two framings are deliberate and are stated rather than buried:

    * **R is described as a single iterated block over every in-loop node**,
      because that is what it is: one flat sweep of the whole model sequence,
      repeated until it stops moving.  What differs from ``A0'`` is the test it
      stops on, not the shape of the loop --- which is the whole content of
      decision D18.
    * **R's tolerance is 1e-6**, because ``Caller.check_agreement`` is
      ``np.allclose(..., rtol=1e-6)``.  Both arms stop at a relative 1e-6; they
      differ in *what* they apply it to.
    """
    loop = m.get("arch_loop_nodes") or []
    sched = m.get("arch_block_schedule")
    if sched is None:
        # R: one block, every in-loop node, iterated to idempotence.  That is
        # not a convenient framing, it is what the loop is -- and it is the
        # content of decision D18: R and A0' have the same loop SHAPE and
        # differ in the test it stops on.
        sched_desc = [(_ALL, tuple(sorted(loop)), None, True)]
    else:
        sched_desc = [
            # A single-block schedule's label is canonicalised.  The label of a
            # one-block schedule carries no information --- "FLAT" and "LOOP"
            # are two names for the same partition --- and encoding my own
            # naming as a structural difference would make the descriptor lie
            # about what the two arms differ in.  A multi-block schedule keeps
            # its labels, because there they name the DSM modules and the
            # partition IS the thing being compared.
            (_ALL if len(sched) == 1 else lab, tuple(sorted(ns)), None, it)
            for lab, ns, it in sched
        ]
    tails = m.get("arch_hoist_tails_resolved") or [[], []]
    ys = m.get("arch_module_solve_yspec") or {}
    on = bool(m.get("arch_module_solve_name") not in (None, "off"))
    return MF.arm_descriptor(
        name=arm,
        predicate=(
            "coupling_state_scaled_residual_at_tau" if on
            else "objf_and_conf_np_allclose_rtol_1e-6_equal_nan"
        ),
        node_sequence=m.get("arch_sequence_head") or [],
        block_schedule=sched_desc,
        # R runs at least two sweeps: the first sets the previous value and the
        # second is the first that can agree with it.  The coupling-state arms
        # compare against the state read before the first sweep, so one sweep
        # can converge.  Phase A separated these as A0 and A0f.
        floor=2 if not on else 1,
        tau=1e-6 if not on else m.get("arch_module_solve_tau"),
        inner_tau=1e-6 if not on else m.get("arch_module_solve_inner_tau"),
        hoist=bool(m.get("arch_hoist_name") not in (None, "off")),
        lift=bool(m.get("arch_lift_sites")),
        pre_predicate_tail=sorted(tails[0]),
        post_predicate_tail=sorted(tails[1]),
        loop_nodes=sorted(loop),
        spec_mode=("a18_committed_artifact" if on else None),
        scale_floor=(1.0 if on else None),
        spec_sha256=(ys.get("components_sha256") if on else None),
        inner_cap=(20 if on else 10),
        outer_cap=(20 if on else None),
        global_cap=(200 if on else None),
    )


#: The dimensions that separate a coupling-state arm from ``R``.  All four are
#: **entailed by** replacing the stopping rule, and all four genuinely differ:
#: a coupling-state test needs a spec (there is none to have when the test is
#: on ``objf``/``conf``), has no two-sweep floor, and has its own caps.  They
#: are declared rather than folded into ``stopping_test``, because widening an
#: existing dimension is exactly what ``manifest.py`` forbids.
_PREDICATE_DIMS = ["stopping_test", "sweep_floor", "spec", "caps"]

_PREDICATE_WHY = (
    "R stops when objf and conf agree between sweeps under np.allclose's "
    "hidden atol and equal_nan=True; the coupling-state arms stop when ~840 "
    "measured state components agree at tau.  The other three dimensions are "
    "entailed by that change and are declared rather than hidden inside it: a "
    "coupling-state test needs a per-deck spec, it has no two-sweep floor "
    "because it compares against the state before the first sweep, and its "
    "caps are the block solver's rather than call_models' ten evaluations."
)


def manifests_for(scenario: str, arms) -> dict:
    """Every ordered pair of arms actually run, declared.

    ``manifest.check_all`` refuses the whole run if a pair is missing, which is
    what stops a third arm being added and quietly compared with no
    declaration --- §6.3(iii)'s confound one level up.  The declarations are
    **per deck**, because ``st_regression`` has no burn-time coupler and
    therefore no lift on either side: declaring ``lift`` there would be an
    over-declaration, and ``manifest.py`` refuses that too.
    """
    lifted = scenario in PULSED
    arch = ["block_grouping", "hoist"] + (["lift"] if lifted else [])
    arch_why = (
        "the proposed architecture: per-module block solves, the feed-forward "
        "hoist, and " + (
            "the burn-time lift.  Three things at once, by decision D15(b), "
            "which is why the headline is 'the proposed architecture' and "
            "never 'the partition's benefit' (plan §7a)."
            if lifted else
            "no lift -- this deck has i_pulsed_plant = 0, an empty measured "
            "PULSE write set and therefore k = 0.  It is the control, not a "
            "third replicate."
        )
        + "  block_grouping licenses node_sequence because grouping the "
        "models into blocks also transposes build and physics; A23 measured "
        "that transposition to be exactly reproducing in the flat arm, and "
        "A0p_reordered measures it here."
    )
    m = {
        "R -> A0p": MF.Manifest(
            "R -> A0p", varies=_PREDICATE_DIMS,
            rationale="the stopping rule alone.  " + _PREDICATE_WHY),
        "A0p -> A1p": MF.Manifest(
            "A0p -> A1p", varies=arch, rationale=arch_why),
        "R -> A1p": MF.Manifest(
            "R -> A1p", varies=_PREDICATE_DIMS + arch,
            rationale=(
                "both at once.  Legitimate ONLY as the user-facing figure -- "
                "what someone running PROCESS would actually see -- and never "
                "as the architecture's cost, which is A0p -> A1p."
            )),
    }
    if "A0p_reordered" in arms:
        m["A0p -> A0p_reordered"] = MF.Manifest(
            "A0p -> A0p_reordered", varies=["node_order"],
            rationale=(
                "the build/physics transposition alone, so that the node "
                "order component of A0p -> A1p is measured rather than left "
                "as a caveat."))
        m["R -> A0p_reordered"] = MF.Manifest(
            "R -> A0p_reordered", varies=_PREDICATE_DIMS + ["node_order"],
            rationale="not compared in any result; declared because it was run")
        m["A0p_reordered -> A1p"] = MF.Manifest(
            "A0p_reordered -> A1p", varies=arch,
            rationale=(
                "not a headline: the same architecture step as A0p -> A1p but "
                "from the reordered control.  Reported only as the check that "
                "the step does not depend on which control it starts from."))
    if "A1p_nohoist" in arms:
        m["A1p_nohoist -> A1p"] = MF.Manifest(
            "A1p_nohoist -> A1p", varies=["hoist"],
            rationale=(
                "the hoist's separable share, measured INSIDE this "
                "architecture.  A13's figures were measured in the flat "
                "architecture and quoting them as the share here would be a "
                "units error of the kind trap T11 records."))
        m["R -> A1p_nohoist"] = MF.Manifest(
            "R -> A1p_nohoist",
            varies=_PREDICATE_DIMS + ["block_grouping"]
            + (["lift"] if lifted else []),
            rationale="not a headline; declared because the arm was run")
        m["A0p -> A1p_nohoist"] = MF.Manifest(
            "A0p -> A1p_nohoist",
            varies=["block_grouping"] + (["lift"] if lifted else []),
            rationale=(
                "the architecture without the hoist, at matched predicate.  "
                "The complement of A1p_nohoist -> A1p."))
        if "A0p_reordered" in arms:
            m["A0p_reordered -> A1p_nohoist"] = MF.Manifest(
                "A0p_reordered -> A1p_nohoist",
                varies=["block_grouping"] + (["lift"] if lifted else []),
                rationale="not compared in any result; declared because run")
    return m


def check_manifests(runs: Path, scenarios, arms) -> dict:
    """Build every arm's descriptor from its run and check every pair."""
    out: dict = {"per_scenario": {}, "status": "PASS"}
    for s in scenarios:
        descs = {}
        for a in arms:
            m = G.load(runs, s, a)
            if m is None or m.get("status") != "ok":
                continue
            descs[a] = descriptor(m, a)
        try:
            rec = MF.check_all(manifests_for(s, arms), descs)
        except MF.ManifestViolation as exc:
            rec = {"status": "REFUSED", "error": str(exc)}
        out["per_scenario"][s] = rec
        if rec.get("status") != "PASS":
            out["status"] = "REFUSED"
    return out


def manifest_sensitivity(runs: Path, scenario: str, arms) -> dict:
    """Protocol §12: show the manifest capable of refusing.

    Three ways it must refuse, each one a real failure mode:
    an undeclared difference, an over-declared manifest, and an arm pair with
    no declaration at all.
    """
    descs = {}
    for a in arms:
        m = G.load(runs, scenario, a)
        if m is not None and m.get("status") == "ok":
            descs[a] = descriptor(m, a)
    out: dict = {"scenario": scenario, "arms_available": sorted(descs)}
    if "A0p" not in descs or "A1p" not in descs:
        out["status"] = "NOT RUN -- arms missing"
        return out

    # (i) an undeclared difference: declare only the grouping, when the hoist
    #     (and on a pulsed deck the lift) also differ.
    try:
        MF.Manifest("A0p -> A1p", varies=["block_grouping"],
                    rationale="deliberately incomplete").check(
            descs["A0p"], descs["A1p"])
        out["undeclared_difference"] = {"refused": False}
    except MF.ManifestViolation as exc:
        out["undeclared_difference"] = {"refused": True, "message": str(exc)[:400]}

    # (ii) an over-declared manifest: declare a dimension that does not differ.
    try:
        MF.Manifest("A0p -> A0p", varies=["tau"],
                    rationale="deliberately over-declared").check(
            descs["A0p"], descs["A0p"])
        out["over_declared"] = {"refused": False}
    except MF.ManifestViolation as exc:
        out["over_declared"] = {"refused": True, "message": str(exc)[:400]}

    # (iii) an undeclared arm pair.
    try:
        MF.check_all(
            {"R -> A0p": MF.Manifest("R -> A0p", varies=_PREDICATE_DIMS,
                                     rationale=_PREDICATE_WHY)},
            {k: descs[k] for k in ("R", "A0p", "A1p") if k in descs},
        )
        out["undeclared_arm_pair"] = {"refused": False}
    except MF.ManifestViolation as exc:
        out["undeclared_arm_pair"] = {"refused": True, "message": str(exc)[:400]}

    teeth = [v for k, v in out.items() if isinstance(v, dict) and "refused" in v]
    out["n_teeth"] = len(teeth)
    out["n_that_bit"] = sum(1 for v in teeth if v["refused"])
    out["status"] = "PASS" if all(v["refused"] for v in teeth) else "FAIL"
    return out


# ---------------------------------------------------------------------------
# 2.  Structural gate: do the arms run the same models?
# ---------------------------------------------------------------------------


def model_set_gate(runs: Path, scenarios, arms) -> dict:
    """Every model call site is covered by every arm's schedule.

    ``Caller._node`` **skips** a node whose name is not in the current block's
    set, silently.  So a block schedule that does not name a call site does not
    fail --- it quietly stops computing something the baseline computes, which
    is the failure mode A25's own first variant had in another form.  This
    reads the call-site names out of ``caller.py``'s source and checks that
    each arm's resolved schedule covers all of them, with the denominator.

    It also checks the **cost unit** rather than asserting it: the per-node
    census recorded by ``run_one.py --node-census`` must sum to
    ``node_calls_total``, and nothing may have been run through the flat
    hoisted tail, which does not increment the counter (the accounting error
    A26 §7.3 found).
    """
    import ast

    src = (TREE / "process" / "core" / "caller.py").read_text()
    names, dynamic = set(), 0
    for n in ast.walk(ast.parse(src)):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "_node" and n.args):
            if isinstance(n.args[0], ast.Constant):
                names.add(n.args[0].value)
            else:
                dynamic += 1
    # ``_SEQUENCE_HEADS`` is an ANNOTATED assignment
    # (``_SEQUENCE_HEADS: dict[...] = {...}``), which the parser gives as
    # ``ast.AnnAssign`` and not ``ast.Assign``.  The first version of this
    # function matched only ``ast.Assign``, so ``heads`` came back **empty**
    # and the three head nodes -- plasma_geom, build, physics -- were not in
    # the call-site set at all.  The gate still reported PASS, because a set
    # that does not contain a node cannot notice the node missing.
    #
    # **Its own sensitivity check is what found this**, by removing a node from
    # a schedule and watching the gate go on passing (protocol §12).  It is the
    # fifth consecutive task in this project where the requirement to show a
    # gate capable of failing has caught a defect in the agent's own harness,
    # in every case while the gate was already passing.
    heads = set()
    for n in ast.walk(ast.parse(src)):
        tgt = None
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            tgt = n.target.id
        elif (isinstance(n, ast.Assign) and n.targets
              and isinstance(n.targets[0], ast.Name)):
            tgt = n.targets[0].id
        if tgt == "_SEQUENCE_HEADS" and isinstance(n.value, ast.Dict):
            for v in n.value.values:
                heads |= {e.value for e in v.elts}
    if not heads:
        raise RuntimeError(
            "caller.py's _SEQUENCE_HEADS did not parse, so the head nodes "
            "would be missing from the call-site set and a schedule that "
            "dropped one of them would pass unnoticed.  Refusing to report a "
            "coverage figure over a set this function could not build."
        )
    call_sites = names | heads

    per: dict = {}
    for s in scenarios:
        rows = {}
        for a in arms:
            m = G.load(runs, s, a)
            if m is None or m.get("status") != "ok":
                rows[a] = {"status": "MISSING"}
                continue
            sched = m.get("arch_block_schedule")
            covered = (
                set(m.get("arch_loop_nodes") or [])
                if sched is None
                else {n for _lab, ns, _it in sched for n in ns}
            )
            tails = m.get("arch_hoist_tails_resolved") or [[], []]
            covered |= set(tails[0]) | set(tails[1])
            nc = m.get("node_census") or {}
            rows[a] = {
                "n_call_sites_in_caller_py": len(call_sites),
                "n_dynamic_call_sites": dynamic,
                "n_call_sites_covered": len(call_sites & covered),
                "call_sites_not_covered": sorted(call_sites - covered),
                "covers_every_call_site": not (call_sites - covered),
                "cost_unit": {
                    "sum_counted": nc.get("sum_counted"),
                    "node_calls_total_reported": nc.get(
                        "node_calls_total_reported"),
                    "audit_node_calls_not_charged": nc.get("audit_node_calls"),
                    "identity": (
                        "sum_counted == node_calls_total + audit_node_calls"
                    ),
                    "counted_matches_total": nc.get(
                        "counted_matches_node_calls_total"),
                    "sum_flat_tail_uncounted": nc.get(
                        "sum_flat_tail_uncounted"),
                    "per_node": nc.get(
                        "per_node_counted_through_Caller_node"),
                },
            }
        per[s] = rows
    decided = [
        r for s in per for r in per[s].values() if "covers_every_call_site" in r
    ]
    ok_cover = all(r["covers_every_call_site"] for r in decided)
    ok_unit = all(
        r["cost_unit"]["counted_matches_total"] is not False
        and (r["cost_unit"]["sum_flat_tail_uncounted"] or 0) == 0
        for r in decided
    )
    return {
        "gate": "model-set coverage and cost-unit accounting",
        "call_sites": sorted(call_sites),
        "n_arm_records_checked": len(decided),
        "status": "PASS" if (ok_cover and ok_unit and decided) else "FAIL",
        "coverage_ok": ok_cover,
        "cost_unit_ok": ok_unit,
        "per_scenario": per,
    }


def model_set_sensitivity(runs: Path, scenario: str) -> dict:
    """Show the coverage and cost-unit checks capable of failing.

    Three perturbations, each the smallest that should register, and each aimed
    at a different half of the gate.  The first is the one that found the
    ``AnnAssign`` defect above; the second targets a **head** node
    specifically, because that is the class the defect made invisible.
    """
    import copy
    base = model_set_gate(runs, [scenario], ["A1p"])
    call_sites = set(base["call_sites"])
    m = G.load(runs, scenario, "A1p")
    if m is None:
        return {"status": "NOT RUN"}

    def _try(name, mutate):
        bad = copy.deepcopy(m)
        detail = mutate(bad)
        tmp = runs / "_sensitivity" / scenario / "A1p_doctored"
        tmp.mkdir(parents=True, exist_ok=True)
        (tmp / "metrics.json").write_text(json.dumps(bad))
        rec = model_set_gate(runs / "_sensitivity", [scenario],
                             ["A1p_doctored"])
        return {
            "perturbation": detail,
            "status_of_doctored_record": rec["status"],
            "must_be": "FAIL",
            "bites": rec["status"] == "FAIL",
        }

    def _drop_any(bad):
        for row in bad.get("arch_block_schedule") or []:
            hits = [n for n in row[1] if n in call_sites]
            if hits:
                row[1].remove(hits[0])
                return f"one node ({hits[0]}) removed from the schedule"
        return "no node to remove"

    def _drop_head(bad):
        # A head node -- plasma_geom / build / physics.  This is exactly the
        # class the AnnAssign defect hid, so it is exercised by name.
        heads = {"plasma_geom", "build", "physics"} & call_sites
        for row in bad.get("arch_block_schedule") or []:
            hits = [n for n in row[1] if n in heads]
            if hits:
                row[1].remove(hits[0])
                return f"one HEAD node ({hits[0]}) removed from the schedule"
        return "no head node in the schedule"

    def _uncounted_tail(bad):
        bad.setdefault("node_census", {})
        bad["node_census"]["sum_flat_tail_uncounted"] = 3
        return ("three model calls attributed to the flat hoisted tail, which "
                "does not increment the counter -- the A26 §7.3 accounting "
                "error")

    out = {
        "n_call_sites": len(call_sites),
        "head_nodes_present_in_call_sites": sorted(
            {"plasma_geom", "build", "physics"} & call_sites),
        "drop_any_node": _try("drop_any", _drop_any),
        "drop_head_node": _try("drop_head", _drop_head),
        "uncounted_tail_calls": _try("tail", _uncounted_tail),
    }
    teeth = [v for v in out.values() if isinstance(v, dict) and "bites" in v]
    out["n_teeth"] = len(teeth)
    out["n_that_bite"] = sum(1 for v in teeth if v["bites"])
    out["status"] = "PASS" if all(v["bites"] for v in teeth) else "FAIL"
    return out


# ---------------------------------------------------------------------------
# 3.  The equivalence gate, over three arms
# ---------------------------------------------------------------------------


def gate(runs: Path, scenarios, arms) -> dict:
    """Every non-reference arm against ``R``, per deck, never pooled.

    The gate is **not** bit identity: ``A1'`` solves a problem with one more
    design variable and one more equality constraint on the pulsed decks, so
    the question is whether the arms land on the same optimum.  ``A0'`` solves
    the *same* problem by a different stopping rule, so for it the gate is a
    stronger statement than it needs to be, and that is said rather than
    exploited.

    Reused from A25 unchanged (``a25_gates.gate_scenario``): ``ifail``,
    ``norm_objf`` to PROCESS's own 1e-6 rtol, a post-solve feasibility audit,
    matched final accuracy, and --- for a lifted arm --- the burn-time
    consistency residual **and** that constraint 93 sits inside the deck's
    equality block.
    """
    per: dict = {}
    for s in scenarios:
        per[s] = {}
        for a in arms:
            if a == "R":
                continue
            per[s][a] = gate_scenario(runs, s, "R", a)
    statuses = [
        per[s][a]["status"] for s in per for a in per[s]
    ]
    return {
        "gate": "A28 equivalence gate, three arms",
        "reference": (
            "R -- PROCESS as it currently is (D14(c)): every variant point "
            "unset, the existing objf/conf predicate, the existing flat loop, "
            "the frozen scenario deck"
        ),
        "scenarios_reported_separately": list(scenarios),
        "denominator_arm_gates": len(statuses),
        "status_by_scenario": {
            s: {a: per[s][a]["status"] for a in per[s]} for s in per
        },
        "overall": "PASS" if statuses and all(
            v == "PASS" for v in statuses) else "FAIL",
        "per_scenario": per,
    }


# ---------------------------------------------------------------------------
# 4.  Cost at matched achieved accuracy
# ---------------------------------------------------------------------------


def _starts_of(d: Path) -> list[dict]:
    out = []
    for sd in sorted(d.glob("start*")):
        f = sd / "metrics.json"
        if f.exists():
            r = json.loads(f.read_text())
            r["start"] = sd.name
            out.append(r)
    return out


def _pct(vals, p):
    xs = sorted(v for v in vals if v is not None)
    if not xs:
        return None
    if len(xs) == 1:
        return xs[0]
    k = (len(xs) - 1) * p / 100.0
    lo, hi = math.floor(k), math.ceil(k)
    return xs[lo] if lo == hi else xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def ladder_reference(runs: Path, scenario: str) -> dict:
    """The optimum each ladder rung is checked against, **per start**.

    A rung at a loose tolerance can look cheap by returning a different
    optimum, so every rung is checked against one.  The reference cannot be
    ``R`` at the deck's own point, because the ladder is run from perturbed
    starts as well and each start has its own optimum.

    It is therefore **the flat control's tightest rung at that same start**:
    the best estimate of the optimum this study has for that start, produced
    by the arm with no inner tolerance to over-solve.  The same reference is
    applied to both arms, which is what makes the acceptance symmetric.  Where
    the flat arm has no completed rung at a start, that start is reported as
    having no reference rather than silently accepted.
    """
    d = runs / "ladder" / scenario
    best: dict = {}
    if not d.is_dir():
        return best
    labels = sorted(
        (float(x.name[len("A0p_tau"):]), x.name)
        for x in d.glob("A0p_tau*")
    )
    for _tau, label in labels:  # ascending tau: tightest first
        for st in _starts_of(d / label):
            if st["start"] in best:
                continue
            if st.get("status") != "ok" or G._ifail(st) != 1:
                continue
            o = (st.get("exact") or {}).get("norm_objf")
            if o is not None:
                best[st["start"]] = {
                    "norm_objf": float.fromhex(o), "from_rung": label,
                }
    return best


def rung(runs: Path, scenario: str, label: str, *, ref_objf: dict,
         tau: float, inner_tau: float | None) -> dict | None:
    """One ladder rung: its cost, its achieved accuracy, and its census.

    **The census comes before the numbers.**  The acceptance test is the
    gate's own --- ``ifail = 1``, and ``norm_objf`` within PROCESS's own 1e-6
    relative of :func:`ladder_reference`'s value **for that start** --- applied
    per start, with the dropped starts counted and named.  A rung that keeps no
    start reports no cost.
    """
    d = runs / "ladder" / scenario / label
    starts = _starts_of(d)
    if not starts:
        return None
    kept, dropped = [], {}
    for s in starts:
        if s.get("status") != "ok":
            dropped[s["start"]] = f"crashed:{s.get('status')}"
            continue
        if G._ifail(s) != 1:
            dropped[s["start"]] = f"ifail={G._ifail(s)}"
            continue
        ref = ref_objf.get(s["start"])
        o = (s.get("exact") or {}).get("norm_objf")
        if ref is None:
            dropped[s["start"]] = "no reference optimum at this start"
            continue
        if o is not None:
            rel = (abs(float.fromhex(o) - ref["norm_objf"])
                   / (abs(ref["norm_objf"]) or 1.0))
            if rel > OBJF_RTOL:
                dropped[s["start"]] = f"objf_mismatch rel={rel:.3g}"
                continue
        kept.append(s)
    if not kept:
        return {
            "label": label, "tau": tau, "inner_tau": inner_tau,
            "n_converged": 0, "n_dropped": len(dropped),
            "dropped": dropped, "net_model_evaluations": None,
        }
    # The accuracy comes from the PAIRED audit run of the same start, not from
    # the cost run: the audit takes one further full sweep, which mutates the
    # state, so a run that is audited cannot also be a cost measurement.  The
    # post-run audit is not used at all -- after SingleRun.run() the output
    # path has re-converged the state to MFILE idempotence, which is stricter
    # than any arm's own test, so it reads exactly zero for every arm at every
    # tolerance.  That is measured (§ the gate table) and is why the audit is
    # taken at an optimiser evaluation instead.
    resid, no_audit = [], []
    for st in kept:
        ap = d / st["start"].replace("start", "audit") / "metrics.json"
        if not ap.exists():
            no_audit.append(st["start"])
            continue
        rec = json.loads(ap.read_text()).get("audit_at_call") or {}
        if "residual_max" in rec:
            resid.append(rec["residual_max"])
        else:
            no_audit.append(st["start"])
    return {
        "label": label,
        "tau": tau,
        "inner_tau": inner_tau,
        "n_converged": len(kept),
        "n_dropped": len(dropped),
        "dropped": dropped,
        "denominator_starts_offered": len(starts),
        "net_model_evaluations": sum(
            int(s.get("node_calls_solve_phase") or 0) for s in kept
        ),
        "mean_sweeps": statistics.fmean(
            [float(s.get("n_model_calls") or 0) for s in kept]
        ),
        "achieved_residual_p90": _pct(resid, 90),
        "achieved_residual_p50": _pct(resid, 50),
        "achieved_residual_max": max((r for r in resid if r is not None),
                                     default=None),
        "n_residuals": len(resid),
        "starts_with_no_audit_run": no_audit,
        "accuracy_measured_at": (
            "the return of the first call_models of the solve phase, on the "
            "paired audit run of the same start; the audit sweep is never "
            "charged to the arm"
        ),
    }


def convexity(curve_rec: dict) -> dict:
    """Is this arm's envelope convex in log10(cost) against log10(accuracy)?

    **This is checked rather than assumed, because a whole bias argument rests
    on it.**  The matched-accuracy read interpolates linearly between
    bracketing envelope points, and a chord across a *convex* curve lies
    **above** it --- so an arm with fewer rungs has wider gaps, more of its
    curve replaced by an over-estimate, and is made to look more expensive
    than it is.  If the curve is not convex the argument does not hold and
    must be dropped rather than asserted.

    Reported as the sign of the discrete second difference at each interior
    envelope point, with its denominator.
    """
    pts = curve_rec.get("points") or []
    xs = [math.log10(p["accuracy"]) for p in pts if p["accuracy"] > 0]
    ys = [math.log10(p["cost"]) for p in pts if p["accuracy"] > 0]
    seconds = []
    for i in range(1, len(xs) - 1):
        h1, h2 = xs[i] - xs[i - 1], xs[i + 1] - xs[i]
        if h1 <= 0 or h2 <= 0:
            continue
        # second divided difference; > 0 is convex
        seconds.append(
            2 * ((ys[i + 1] - ys[i]) / h2 - (ys[i] - ys[i - 1]) / h1)
            / (h1 + h2)
        )
    n_pos = sum(1 for v in seconds if v > 0)
    return {
        "n_envelope_points": len(pts),
        "n_interior_points_testable": len(seconds),
        "n_convex": n_pos,
        "n_concave": len(seconds) - n_pos,
        "second_differences": seconds,
        "verdict": (
            "NOT TESTABLE -- fewer than three envelope points"
            if not seconds else
            "CONVEX at every interior point" if n_pos == len(seconds) else
            "CONCAVE at every interior point" if n_pos == 0 else
            "MIXED -- the chord argument does not hold uniformly"
        ),
    }


def ladder(runs: Path, scenarios, *, stat: str = ACCURACY_STAT) -> dict:
    """Cost read off at matched **achieved** accuracy, per deck.

    A26 fix 1, in the driver.  Both arms run across ladders, each run's
    achieved exit residual is recorded beside its cost, and the cost is read
    off the **lower envelope** ``cost(a) = min{cost_i : accuracy_i <= a}``.
    Reading the rungs in tolerance order instead is the wrong construction and
    flipped A26's own sign once, from +21.9 % to −4.3 %.

    Reported on three statistics, not one: an answer that depends on the
    choice of summary is a finding about the summary.
    """
    out: dict = {
        "construction": (
            "lower envelope cost(a) = min{cost_i : accuracy_i <= a}; "
            "interpolated linearly in log10(cost) against log10(accuracy) "
            "between bracketing envelope points; never extrapolated"
        ),
        "accuracy_measure": (
            "the exit audit's coupling-state scaled residual -- ONE further "
            "full sweep of the complete model set past termination, the same "
            "instrument for every arm at every setting.  Not objective "
            "movement: under the lift two of the three decks have an "
            "objective that is a design variable (plan §4.1e), so objective "
            "movement is degenerate there"
        ),
        "cost_unit": "net model evaluations in the solve phase",
        "asymmetry": {
            "what": (
                "the block arm has an inner tolerance the flat arm does not "
                "have, so more settings are tried: 9 rungs against 5.  TWO "
                "one-sided biases follow, BOTH favouring the block arm, and "
                "declaring them is not correcting them"
            ),
            "bias_1_sampling": (
                "a running minimum can only fall as draws are added, never "
                "rise.  Two arms with identical underlying cost-accuracy "
                "behaviour, sampled 9 times against 5, give the 9-sample arm "
                "the lower envelope from sampling alone.  Worse, the four "
                "extra rungs are NOT spread across the accuracy range: all "
                "four sit at outer tau = 1e-6 and vary only the inner "
                "tolerance, so the extra sampling is CONCENTRATED in one "
                "narrow accuracy band -- and 1e-6 is the study's calibration "
                "point, which is plausibly near where the matched-accuracy "
                "readout lands.  The advantage is concentrated where it does "
                "the most work"
            ),
            "bias_2_interpolation": (
                "cost is read between bracketing envelope points by a chord "
                "in log10(cost) against log10(accuracy).  Where the curve is "
                "convex a chord lies ABOVE it, so the arm with fewer points "
                "has wider gaps, more of its curve replaced by an "
                "over-estimate, and is made to look dearer than it is.  Same "
                "direction as bias 1.  Convexity is CHECKED per arm per deck "
                "under 'convexity' rather than assumed; where the curve is "
                "not convex this bias does not apply and is dropped"
            ),
            "the_fix": (
                "a MATCHED-COUNT envelope is computed beside the "
                "all-settings one: the block arm's five JOINT rungs against "
                "the flat arm's five, same knob, same tau values, five draws "
                "each.  Both are reported per deck with denominators.  The "
                "difference between them is a TUNING PREMIUM -- two knobs "
                "against one.  The all-settings envelope answers a "
                "practitioner question ('the best I can do with each'); the "
                "matched-count envelope answers the architecture question "
                "('what does partitioning cost at equal tuning effort').  "
                "They can disagree in sign, and if they do that is a finding "
                "to report rather than reconcile"
            ),
            "why_this_is_not_pedantry": (
                "A26's own analysis flipped sign on an envelope-construction "
                "choice, +21.9 % to -4.3 %, against a final effect of about "
                "4 %.  The construction has demonstrated leverage comparable "
                "to the quantity being measured"
            ),
            "headline_rule": (
                "the ARCHITECTURE headline takes the matched-count number; "
                "the all-settings number is reported beside it and labelled "
                "as the practitioner figure"
            ),
        },
        "per_scenario": {},
    }
    for s in scenarios:
        ref_objf = ladder_reference(runs, s)
        gate_r = G.load(runs / "gate", s, "R")
        gate_objf = None
        if gate_r and (gate_r.get("exact") or {}).get("norm_objf"):
            gate_objf = float.fromhex(gate_r["exact"]["norm_objf"])
        # The rungs are DISCOVERED from what was run, not assumed from a
        # constant: a shortened ladder (a smoke run, or a deck that could not
        # take a rung) must be reported as the ladder it was, with its own
        # denominator, rather than silently reading zeros for the missing ones.
        flat, block = [], []
        ldir = runs / "ladder" / s
        for d in sorted(p.name for p in ldir.glob("*")) if ldir.is_dir() else []:
            if d.startswith("A0p_tau"):
                t = float(d[len("A0p_tau"):])
                r = rung(runs, s, d, ref_objf=ref_objf, tau=t, inner_tau=t)
                if r:
                    flat.append(r)
            elif d.startswith("A1p_joint"):
                t = float(d[len("A1p_joint"):])
                r = rung(runs, s, d, ref_objf=ref_objf, tau=t, inner_tau=t)
                if r:
                    block.append(r)
            elif d.startswith("A1p_inner"):
                t = float(d[len("A1p_inner"):])
                r = rung(runs, s, d, ref_objf=ref_objf, tau=TAU, inner_tau=t)
                if r:
                    block.append(r)
        usable_flat = [r for r in flat if r.get("net_model_evaluations")]
        usable_block = [r for r in block if r.get("net_model_evaluations")]
        rec: dict = {
            "reference_norm_objf_per_start": ref_objf,
            "R_norm_objf_at_the_decks_own_point": gate_objf,
            "acceptance": (
                "per start: status ok, ifail == 1, and norm_objf within "
                f"{OBJF_RTOL:g} relative of the FLAT CONTROL'S TIGHTEST "
                "COMPLETED RUNG AT THAT SAME START.  Not R at the deck's own "
                "point: the ladder is run from perturbed starts too and each "
                "has its own optimum.  Rungs are reported with their drop "
                "census; a rung that keeps no start reports no cost"
            ),
            "rungs_flat_A0p": flat,
            "rungs_block_A1p": block,
            "n_rungs_flat_usable": len(usable_flat),
            "n_rungs_block_usable": len(usable_block),
        }
        usable_joint = [
            r for r in usable_block if r["label"].startswith("A1p_joint")
        ]
        rec["n_rungs_block_joint_only"] = len(usable_joint)
        for st in (stat, "achieved_residual_p50", "achieved_residual_max"):
            if not usable_flat or not usable_block:
                rec[st] = {"status": "NO CURVE"}
                continue
            cf = curve(usable_flat, stat=st)
            cb = curve(usable_block, stat=st)
            entry = {
                "flat_curve": cf,
                "block_curve_all_settings": cb,
                "all_settings_comparison": acc_compare(cf, cb),
                "convexity_flat": convexity(cf),
                "convexity_block_all_settings": convexity(cb),
            }
            if usable_joint:
                cj = curve(usable_joint, stat=st)
                entry["block_curve_matched_count"] = cj
                entry["matched_count_comparison"] = acc_compare(cf, cj)
                entry["convexity_block_matched_count"] = convexity(cj)
                entry["draws"] = {
                    "flat": len(usable_flat),
                    "block_all_settings": len(usable_block),
                    "block_matched_count": len(usable_joint),
                    "matched": len(usable_flat) == len(usable_joint),
                }
                # The tuning premium: what the second knob buys, at each
                # accuracy the flat arm reached.  A ratio of ratios, so it is
                # reported per point rather than as one number.
                prem = []
                for a_row, m_row in zip(
                    entry["all_settings_comparison"]["rows"],
                    entry["matched_count_comparison"]["rows"],
                ):
                    if (a_row.get("ratio_block_over_flat") is None
                            or m_row.get("ratio_block_over_flat") is None):
                        prem.append(None)
                        continue
                    prem.append(
                        a_row["ratio_block_over_flat"]
                        / m_row["ratio_block_over_flat"]
                    )
                entry["tuning_premium_all_over_matched"] = prem
                entry["tuning_premium_note"] = (
                    "below 1 means the extra knob made the block arm look "
                    "cheaper than it does at equal tuning effort; that "
                    "difference is the tuning premium and is not "
                    "architecture"
                )
            rec[st] = entry
        out["per_scenario"][s] = rec
    return out


# ---------------------------------------------------------------------------
# 5.  H5
# ---------------------------------------------------------------------------


def _entry_census_rollup(runs: Path, scenario: str, arms) -> dict:
    """I-12, at the state each call_models was ENTERED with, per arm.

    A25 reported net electric power at the *returned* point; A26 §11.7 asks
    for it at entry, which is where A22 measured the effect.  Both are kept:
    the drop census still flags a degenerate returned point, and this reports
    the entry states, with denominators.
    """
    out = {}
    for a in arms:
        starts = G.collect_starts(runs, scenario, a)
        rows = [
            (s["start"], s.get("entry_census"))
            for s in starts if s.get("entry_census")
        ]
        deg = [n for n, c in rows if c.get("start_is_degenerate")]
        out[a] = {
            "n_starts_with_a_census": len(rows),
            "denominator_starts": len(starts),
            "n_starts_visiting_a_non_positive_entry": len(deg),
            "starts": sorted(deg),
            "total_call_models_entries_audited": sum(
                c.get("denominator_entries_after_the_first", 0)
                for _n, c in rows
            ),
            "total_non_positive_entries": sum(
                c.get("n_non_positive_entries", 0) for _n, c in rows
            ),
            "min_entry_p_net_mw_over_starts": min(
                (c["min_entry_p_net_mw"] for _n, c in rows
                 if c.get("min_entry_p_net_mw") is not None),
                default=None,
            ),
        }
    return out


def _moved_constant_rollup(runs: Path, scenario: str, arms) -> dict:
    """How often a quantity the harvest called constant actually moved.

    A26 §5.4 measured this to matter: on the dropped deck two quantities that
    are not constant had their bit-identity assertion block convergence, and
    that inflated its cost figures by 14-28 %.  The perturbed multi-starts of
    Phase B are exactly where an unperturbed harvest's constancy claim is most
    likely to fail, so it is counted rather than hoped about.
    """
    out = {}
    for a in arms:
        starts = G.collect_starts(runs, scenario, a)
        tot = [s.get("module_solve_totals") for s in starts
               if s.get("module_solve_totals")]
        if not tot:
            out[a] = {"status": "arm has no coupling-state predicate"}
            continue
        names: set = set()
        for t in tot:
            names |= set(t.get("moved_constants") or ())
        out[a] = {
            "n_starts_with_totals": len(tot),
            "n_call_models_total": sum(t["n_call_models"] for t in tot),
            "n_call_models_with_a_moved_constant": sum(
                t["n_call_models_with_moved_constant"] for t in tot),
            "fraction_of_call_models_affected": (
                sum(t["n_call_models_with_moved_constant"] for t in tot)
                / sum(t["n_call_models"] for t in tot)
                if sum(t["n_call_models"] for t in tot) else None
            ),
            "n_distinct_constants_that_moved": len(names),
            "constants_that_moved": sorted(names)[:40],
        }
    return out


def _failure_attribution(runs: Path, scenario: str, arms) -> dict:
    """Why each arm refused a start, and on which component.

    **This is the measurement decision D18 added a third arm for.**  A25 found
    that all 13 starts its variant refused were refusals of non-finite
    intermediate state, and reported that as a property of the architecture ---
    with no control that could have told architecture from stopping rule.  The
    coupling-state predicate scores a component ``inf`` whenever either
    snapshot is not float-viewable, so **any** arm using it refuses a NaN.  If
    ``A0'`` refuses the same starts, the deficit is the predicate; if it does
    not, it is the architecture.

    The component name is read out of the exception the run raised, not
    inferred: ``ModuleSolveFailure`` names the argmax component in its message.
    """
    import re
    out = {}
    for a in arms:
        starts = G.collect_starts(runs, scenario, a)
        rows, comps = {}, {}
        for st in starts:
            if st.get("status") == "ok":
                continue
            tb = (st.get("traceback") or "")
            last = tb.strip().splitlines()[-1] if tb.strip() else ""
            kind = "ModuleSolveFailure" if "ModuleSolveFailure" in tb else (
                last.split(":")[0].split(".")[-1] or "unknown")
            rows[st["start"]] = {"kind": kind, "message": last[:240]}
            m = re.search(r"on ([A-Za-z_][\w.]*)", last)
            if kind == "ModuleSolveFailure" and m:
                comps[m.group(1)] = comps.get(m.group(1), 0) + 1
        out[a] = {
            "denominator_starts": len(starts),
            "n_starts_not_ok": len(rows),
            "per_start": rows,
            "components_named_by_a_module_solve_failure": dict(
                sorted(comps.items(), key=lambda kv: -kv[1])),
            "n_module_solve_failures": sum(
                1 for r in rows.values()
                if r["kind"] == "ModuleSolveFailure"),
        }
    return out


def h5(runs: Path, scenarios, arms) -> dict:
    """The paired multi-start campaign, three arms, per deck.

    Robustness first, then the drop census, then any ratio.
    """
    comparisons = [("R", "A0p"), ("A0p", "A1p"), ("R", "A1p")]
    if "A1p_nohoist" in arms:
        comparisons.append(("A1p_nohoist", "A1p"))
        comparisons.append(("A0p", "A1p_nohoist"))
    out: dict = {
        "cost_unit": (
            "net model evaluations in the solve phase -- individual model "
            "run() invocations, split at the entry to write_output_files"
        ),
        "headline": "A0p -> A1p (the architecture, at matched predicate)",
        "naming": (
            "the variant carries the block solves, the lift AND the hoist "
            "(D15(b)), so its result is 'the proposed architecture' and never "
            "'the partition's benefit' (plan §7a)"
        ),
        "never": "no conclusion rests on a timing; wall clock is not read here",
        "scenarios_reported_separately": list(scenarios),
        "comparisons": {},
        "I12_entry_census": {},
        "moved_constants_under_perturbation": {},
        "failure_attribution": {},
        "failure_attribution_why": (
            "decision D18: A25 reported 13 refused starts as a property of "
            "the architecture with no control that could distinguish it from "
            "the stopping rule.  A0' uses the same stopping rule and the flat "
            "loop, so if it refuses the same starts the deficit is the "
            "predicate and not the architecture"
        ),
    }
    for s in scenarios:
        out["comparisons"][s] = {}
        for ref, arm in comparisons:
            if ref in arms and arm in arms:
                out["comparisons"][s][f"{ref}_vs_{arm}"] = compare(
                    runs, s, ref, arm
                )
        out["I12_entry_census"][s] = _entry_census_rollup(runs, s, arms)
        out["moved_constants_under_perturbation"][s] = _moved_constant_rollup(
            runs, s, arms
        )
        out["failure_attribution"][s] = _failure_attribution(runs, s, arms)
    return out


# ---------------------------------------------------------------------------
# 6.  Timings -- context, never evidence
# ---------------------------------------------------------------------------


def timings(runs: Path, scenarios, arms) -> dict:
    """Median, interval, repetition count and sequence position.  Never a ratio.

    A26 measured the p10-p90 band at 50-143 % of the median against 4 %
    effects, so these resolve nothing about the arms and that is said in the
    same sentence as the numbers.  ``_no_ratio`` is not decoration: the ratio
    of two of these is exactly the quantity issue I-10 recorded moving 6.4 %
    to 4.4 % across runs of identical code.
    """
    out: dict = {
        "what_these_are": (
            "wall and CPU seconds per whole optimisation run, over the "
            "campaign's starts.  CONTEXT, NEVER EVIDENCE: the interval below "
            "is wider than every effect this study argues about, so no ratio "
            "of two of these numbers can resolve one, and none is offered"
        ),
        "per_scenario": {},
    }
    for s in scenarios:
        rows = {}
        for a in arms:
            starts = [x for x in G.collect_starts(runs, s, a)
                      if x.get("status") == "ok"]
            cpu = [x.get("cpu_s") for x in starts if x.get("cpu_s")]
            wall = [x.get("wall_s") for x in starts if x.get("wall_s")]
            seq = [x.get("a28_sequence_position") for x in starts]
            rss = [x.get("maxrss_kb") for x in starts if x.get("maxrss_kb")]
            load = [x.get("loadavg")[0] for x in starts
                    if x.get("loadavg")]
            if not cpu:
                rows[a] = {"status": "no completed runs"}
                continue
            med = statistics.median(cpu)
            p10, p90 = _pct(cpu, 10), _pct(cpu, 90)
            rows[a] = {
                "n_repetitions": len(cpu),
                "cpu_s_median": med,
                "cpu_s_p10_p90": [p10, p90],
                "p10_p90_spread_as_pct_of_median": (
                    100.0 * (p90 - p10) / med if med else None),
                "wall_s_median": statistics.median(wall) if wall else None,
                "sequence_positions": [min(seq), max(seq)] if seq else None,
                "maxrss_kb_max": max(rss) if rss else None,
                "loadavg_1min_range": (
                    [min(load), max(load)] if load else None),
            }
        rows["_no_ratio"] = (
            "deliberately absent.  The ratio of two medians here is the "
            "quantity I-10 recorded moving 6.4 % -> 4.4 % across runs of "
            "identical code"
        )
        out["per_scenario"][s] = rows
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=[
        "manifests", "manifest_sensitivity", "model_set", "gate",
        "gate_sensitivity", "calibration", "ladder", "h5", "timings", "all",
    ])
    ap.add_argument("--runs", required=True)
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    ap.add_argument("--arms", nargs="*", default=list(CORE_ARMS))
    ap.add_argument("--deltas", nargs="*", type=float,
                    default=[0.01, 0.05, 0.10])
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    runs = Path(args.runs).resolve()
    S, A = args.scenarios, args.arms

    def _emit(name, rec):
        dest = Path(args.out) if args.out else runs / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(rec, indent=2, default=str))
        print(f"-> {dest}")

    if args.command in ("manifests", "all"):
        _emit("_manifests_a28.json", check_manifests(runs / "gate", S, A))
    if args.command in ("manifest_sensitivity", "all"):
        _emit("_manifest_sensitivity_a28.json",
              manifest_sensitivity(runs / "gate", S[0], A))
    if args.command in ("model_set", "all"):
        rec = model_set_gate(runs / "gate", S, A)
        rec["sensitivity"] = model_set_sensitivity(runs / "gate", S[0])
        _emit("_model_set_a28.json", rec)
    if args.command in ("gate", "all"):
        _emit("_gate_a28.json", gate(runs / "gate", S, A))
    if args.command in ("gate_sensitivity", "all"):
        from a25_gates import sensitivity as a25_sens
        # Every non-reference arm's gate is shown capable of failing, not just
        # one of them: a tooth that bites on A1' says nothing about the gate
        # applied to A0', which is a different arm pair with a different
        # constraint-93 verdict.
        rec = {}
        for a in A:
            if a == "R":
                continue
            r = a25_sens(runs / "gate", S, ref="R", arm=a)
            # **A tooth that cannot bite is not a tooth that failed, and it is
            # not a pass either.**  The two constraint-93 perturbations watch a
            # quantity that does not exist on an arm without the lift: mutating
            # a null record changes nothing, so the gate correctly still
            # PASSES, and counting that as a failure would be as wrong as
            # counting it as a success.  This is the shape A26 §7.1 found in
            # its own gate -- a watched quantity that is never exercised makes
            # the check an assertion -- so it is named rather than summed.
            g = gate_scenario(runs / "gate", S[0], "R", a)
            c93 = (g.get("checks") or {}).get("constraint_93") or {}
            if c93.get("status") == "NOT APPLICABLE":
                for k in ("constraint_93_off_manifold",
                          "constraint_93_in_inequality_block"):
                    if k in r:
                        r[k]["status"] = "NOT APPLICABLE"
                        r[k]["must_be"] = None
                        r[k]["why_not_applicable"] = (
                            f"arm {a} takes no burn-time lift on {S[0]}, so "
                            f"the deck names no icc = 93 and there is no "
                            f"consistency residual to corrupt.  Reported as "
                            f"inapplicable rather than counted as a pass"
                        )
                verdicts = {
                    k: v for k, v in r.items()
                    if isinstance(v, dict) and v.get("must_be")
                }
                r["_summary"] = {
                    "n_checks_that_must_fail": len(verdicts),
                    "n_that_did_fail": sum(
                        1 for v in verdicts.values() if v["status"] == "FAIL"),
                    "n_not_applicable": 2,
                    "not_applicable": [
                        "constraint_93_off_manifold",
                        "constraint_93_in_inequality_block",
                    ],
                    "all_teeth_bite": all(
                        v["status"] == "FAIL" for v in verdicts.values()),
                }
            rec[a] = r
        summaries = [v["_summary"] for v in rec.values() if "_summary" in v]
        rec["_summary"] = {
            "arms_exercised": [a for a in A if a != "R"],
            "n_checks_that_must_fail": sum(
                x["n_checks_that_must_fail"] for x in summaries),
            "n_that_did_fail": sum(x["n_that_did_fail"] for x in summaries),
            "n_not_applicable": sum(
                x.get("n_not_applicable", 0) for x in summaries),
            "not_applicable_why": (
                "the two constraint-93 perturbations watch a quantity that "
                "only exists on an arm carrying the burn-time lift.  On an arm "
                "without it they are vacuous and are named rather than counted "
                "either way (the shape of A26 §7.1)"
            ),
            "all_teeth_bite": all(x["all_teeth_bite"] for x in summaries),
        }
        _emit("_gate_sensitivity_a28.json", rec)
    if args.command in ("calibration",):
        _emit("_calibration_a28.json",
              calibration(runs / "calibrate", S, args.deltas))
    if args.command in ("ladder", "all"):
        _emit("_ladder_a28.json", ladder(runs, S))
    if args.command in ("h5", "all"):
        _emit("_h5_a28.json", h5(runs / "h5", S, A))
    if args.command in ("timings", "all"):
        _emit("_timings_a28.json", timings(runs / "h5", S, A))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
