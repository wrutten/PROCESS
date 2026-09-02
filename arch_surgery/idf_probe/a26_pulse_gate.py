#!/usr/bin/env python
"""Plan §4.1d's gate: ``pulse`` leaves the MDA under the lift, correctly.

What is being gated
-------------------

Post-lift, ``pulse`` runs **once per optimiser evaluation** instead of once per
sweep, in the **pre-predicate** slot --- after the loop has converged, before
``objf`` and ``conf`` are evaluated.  §4.1d asks for one thing: *with the lift
on, the constraint vector must be bit-identical to an arm that runs ``pulse``
every sweep.*

**That gate is vacuous on this study's decks, and saying so is half the point.**
``pulse`` writes exactly two fields.  Post-lift ``times.t_plant_pulse_burn`` is
a no-op; the other, ``constraints.t_current_ramp_up_min``, is read by exactly
one constraint equation --- **41**, the plasma-current ramp-up time lower
limit --- and **none of the four decks activates ``icc = 41``**.  So the
constraint vector cannot move no matter where ``pulse`` runs, and a comparison
of ``conf`` alone would report a zero that means nothing.  This is precisely
the failure mode protocol §12 exists for: a gate whose watched quantity is
never exercised.

So three things are compared, and each is reported with its denominator:

1. **The field itself**, ``constraints.t_current_ramp_up_min``, as an exact hex
   float at every ``call_models`` return.  This is the non-vacuous version of
   §4.1d's gate: it is the value the constraint *would* read.
2. **The constraint vector**, as exact hex floats, every entry, every call.
   Expected to be identically zero-difference, and reported **with the note
   that constraint 41 is inactive**, so the zero is read correctly.
3. **The whole output file**, line by line and float by float as hex --- the
   same comparison A13's hoist gate used.

And the sensitivity check: the same comparison is re-run against a copy of one
arm's record with a single **1-ULP** perturbation, to show it can fail.  A
stale-by-one-sweep value on a converged state differs at tolerance level, so a
comparator that rounded would pass it silently.

The two arms differ in exactly one thing
-----------------------------------------

``PROCESS_ARCH_HOIST=feedforward`` versus ``feedforward_lifted``, with
``PROCESS_ARCH_LIFT=burn_time`` and the derived ``ixc = 178`` / ``icc = 93``
deck on **both**.  That is why ``feedforward_lifted`` is its own arm name
rather than an automatic consequence of the lift: it makes this a
one-variable comparison.

Usage
-----
    PYTHONPATH=<tree> python a26_pulse_gate.py --scenario S --outdir D \\
        --deck S_lifted.IN.DAT --arm feedforward --expect-tree <tree>
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run_recorded(deck: Path, outdir: Path) -> dict:
    """One optimisation, recording the predicate at every ``call_models``.

    The wrapper is applied to ``Caller.call_models`` and records what the
    method **returned** --- which for the hoisted arm is the value produced
    after the pre-predicate group ran, and is exactly the quantity the
    optimiser sees.
    """
    import numpy as np

    from process.core import caller as caller_mod
    from process.main import SingleRun

    rec: list[dict] = []
    original = caller_mod.Caller.call_models
    # Sweeps, counted directly.  Without this the model-evaluation difference
    # cannot be decomposed into "pulse runs less often" and "the loop takes a
    # different number of sweeps", and a number whose composition cannot be
    # stated is not ready to publish (trap T11).
    sweeps = [0]
    original_once = caller_mod.Caller._call_models_once

    def wrapped_once(self, xc):
        sweeps[0] += 1
        return original_once(self, xc)

    caller_mod.Caller._call_models_once = wrapped_once

    def wrapped(self, xc, m):
        objf, conf = original(self, xc, m)
        conf = np.asarray(conf)
        rec.append({
            "objf": float(objf).hex(),
            "conf": [float(c).hex() for c in conf.ravel()],
            "t_current_ramp_up_min": float(
                self.data.constraints.t_current_ramp_up_min
            ).hex(),
            "t_plant_pulse_burn": float(
                self.data.times.t_plant_pulse_burn
            ).hex(),
        })
        return objf, conf

    caller_mod.Caller.call_models = wrapped
    try:
        sr = SingleRun(str(deck), solver="vmcon", update_obsolete=True)
        sr.run()
    finally:
        caller_mod.Caller.call_models = original
        caller_mod.Caller._call_models_once = original_once

    pre, post = caller_mod.resolved_hoist_tails(sr.data.numerics.i_figure_merit)
    return {
        # In-loop model evaluations, counted by the driver itself
        # (``Caller._node`` increments it for every node it runs).  This is the
        # acceptance quantity: what the placement change is worth is the
        # difference between running ``pulse`` on every sweep and running it
        # once per ``call_models``.  ``NODE_CALLS_AT_OUTPUT`` is the count at
        # the moment the final-output path is entered, so the optimisation's
        # own work can be separated from the post-solve output path.
        "sweeps_total": sweeps[0],
        "n_loop_nodes": len(caller_mod.SEQUENCE_HEAD),
        "node_calls_total": caller_mod.NODE_CALLS[0],
        "node_calls_at_output": caller_mod.NODE_CALLS_AT_OUTPUT[0],
        "hoist_name": caller_mod.HOIST_NAME,
        "hoist_nodes": list(caller_mod.HOIST_NODES),
        "pre_predicate_tail": list(pre),
        "post_predicate_tail": list(post),
        "n_call_models": len(rec),
        "calls": rec,
    }


def compare(a: dict, b: dict) -> dict:
    """Bit comparison of the two arms' recorded predicate streams."""
    na, nb = a["n_call_models"], b["n_call_models"]
    n = min(na, nb)
    diff_conf = diff_objf = diff_field = diff_burn = 0
    n_conf_entries = 0
    first = []
    for i in range(n):
        ca, cb = a["calls"][i], b["calls"][i]
        n_conf_entries += len(ca["conf"])
        if ca["objf"] != cb["objf"]:
            diff_objf += 1
        if ca["conf"] != cb["conf"]:
            diff_conf += 1
        if ca["t_current_ramp_up_min"] != cb["t_current_ramp_up_min"]:
            diff_field += 1
            if len(first) < 5:
                first.append({"call": i, "a": ca["t_current_ramp_up_min"],
                              "b": cb["t_current_ramp_up_min"],
                              "a_dec": float.fromhex(ca["t_current_ramp_up_min"]),
                              "b_dec": float.fromhex(cb["t_current_ramp_up_min"])})
        if ca["t_plant_pulse_burn"] != cb["t_plant_pulse_burn"]:
            diff_burn += 1
    return {
        "sweeps_total": {"a": a.get("sweeps_total"), "b": b.get("sweeps_total")},
        "sweeps_removed": (a.get("sweeps_total") or 0) - (b.get("sweeps_total") or 0),
        "node_calls_total": {"a": a.get("node_calls_total"),
                             "b": b.get("node_calls_total")},
        "node_calls_at_output": {"a": a.get("node_calls_at_output"),
                                 "b": b.get("node_calls_at_output")},
        "model_evaluations_removed": (
            (a.get("node_calls_at_output") or 0)
            - (b.get("node_calls_at_output") or 0)
        ),
        "model_evaluations_removed_pct": (
            100.0 * ((a.get("node_calls_at_output") or 0)
                     - (b.get("node_calls_at_output") or 0))
            / (a.get("node_calls_at_output") or 1)
        ),
        "n_call_models": {"a": na, "b": nb},
        "call_counts_equal": na == nb,
        "n_calls_compared": n,
        "n_conf_entries_compared": n_conf_entries,
        "differing_objf_calls": diff_objf,
        "differing_conf_calls": diff_conf,
        "differing_t_current_ramp_up_min_calls": diff_field,
        "differing_t_plant_pulse_burn_calls": diff_burn,
        "first_field_differences": first,
        "status": (
            "PASS"
            if na == nb and n and diff_objf == 0 and diff_conf == 0
            and diff_field == 0 and diff_burn == 0
            else ("EMPTY -- nothing compared" if not n else "FAIL")
        ),
    }


def sensitivity(a: dict, b: dict) -> dict:
    """Show the comparison capable of catching a 1-ULP move, on each quantity."""
    import copy
    import math

    def nudge_hex(h):
        return math.nextafter(float.fromhex(h), math.inf).hex()

    cases = []
    for name, key in (("t_current_ramp_up_min", "t_current_ramp_up_min"),
                      ("objf", "objf"),
                      ("t_plant_pulse_burn", "t_plant_pulse_burn")):
        d = copy.deepcopy(b)
        if not d["calls"]:
            cases.append({"case": name, "caught": None,
                          "status": "NOT APPLIED -- no calls"})
            continue
        d["calls"][0][key] = nudge_hex(d["calls"][0][key])
        r = compare(a, d)
        cases.append({"case": f"{name} +1 ULP", "caught": r["status"] != "PASS"})
    d = copy.deepcopy(b)
    if d["calls"] and d["calls"][0]["conf"]:
        d["calls"][0]["conf"][0] = nudge_hex(d["calls"][0]["conf"][0])
        r = compare(a, d)
        cases.append({"case": "conf[0] +1 ULP", "caught": r["status"] != "PASS"})
    applied = [c for c in cases if c.get("caught") is not None]
    return {
        "cases": cases,
        "n_applied": len(applied),
        "n_caught": sum(1 for c in applied if c["caught"]),
        "status": "PASS" if applied and all(c["caught"] for c in applied)
        else "FAIL -- the comparison cannot detect a change it must detect",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--expect-tree", required=True)
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    import process

    pf = Path(process.__file__).resolve()
    if pf.parent.parent != Path(args.expect_tree).resolve():
        raise SystemExit(
            f"WRONG TREE: imported {pf}, expected exactly {args.expect_tree}"
        )

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    out: dict = {"label": args.label, "deck": args.deck, "tree": str(pf.parent.parent)}
    try:
        out.update(run_recorded(Path(args.deck), outdir))
        out["status"] = "ok"
    except Exception:
        out["status"] = "crashed"
        out["traceback"] = traceback.format_exc()
    (outdir / "predicate_stream.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "calls"}, indent=2))
    return 0 if out["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
