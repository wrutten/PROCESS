#!/usr/bin/env python
"""Derive the Phase B variant deck from a frozen scenario deck.

The frozen decks in ``scenarios/`` are **not** edited (decision D9: a scenario
cannot change under a result).  The variant deck is derived from one, written
into the run directory, and carries its provenance in a header comment and in a
JSON sidecar.

Three lines are added, and only three:

``ixc = 178``
    the flat-top burn time becomes a design variable (registry allocation A24).
``icc = 93``
    the burn-time consistency residual becomes an equality constraint, so the
    lifted unknown is determined by the same relation ``Pulse`` used to assign.
``t_plant_pulse_burn = <entry value>``
    the lifted variable's **initial value**.

The third is the one that needs a rule, and the rule is *measured, not chosen*:
**the burn time the baseline's own idempotence loop settles on at this deck's
own starting design vector.**  That is the state the baseline arm itself enters
its first optimiser iteration from, and it is the state at which the variant's
constraint 93 residual is zero -- so the two arms start from the same design
point, rather than the variant starting off its own consistency manifold.  The
plan (section 2.5) asks that the extra variable be initialised from the deck's
own burn time and that the choice be stated rather than tuned; this is that
value, obtained by running the unmodified driver.

Why it cannot simply be left alone: ``times.t_plant_pulse_burn`` defaults to
1000 s and none of the three pulsed decks sets it, while their settled burn
times are several thousand seconds.  ``load_iteration_variables`` reads the
field *before* any model runs, so an unset variant deck would start the lifted
variable at a value the baseline never visits -- and the two arms would not be
starting from the same design point at all.  That is a confound, not a
perturbation.

Why **one sweep** is not enough either, and this is measured rather than
argued: the first sweep computes the burn time from an entry loop voltage that
has not settled, giving 9.7e5 s on ``large_tokamak_nof`` against a settled
value three orders of magnitude smaller.  Both numbers are recorded in the
sidecar so the choice between them is visible.

No bounds are set for 178: the registry defaults ``(1.0, 1.0e8)`` apply, which
is A24's AD1 and is the non-tuned choice.  A deck may override them; none does.

Usage
-----
    PYTHONPATH=<tree> python a25_variant_deck.py \\
        --scenario large_tokamak_nof --outdir <dir> --expect-tree <tree>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent

IXC_BURN_TIME = 178
ICC_BURN_TIME = 93


def entry_burn_time(deck: Path) -> dict:
    """``times.t_plant_pulse_burn`` after one baseline sweep at the deck's own x.

    The models are called through ``Caller._call_models_once`` -- the driver's
    own sequence, with every variant point off -- so this is the value the
    baseline arm itself holds when it enters its first idempotence test.
    """
    from process.core.caller import Caller
    from process.core.solver.iteration_variables import (
        load_iteration_variables,
        load_scaled_bounds,
    )
    from process.main import SingleRun

    sr = SingleRun(str(deck), solver="vmcon", update_obsolete=True)
    load_iteration_variables(sr.data)
    load_scaled_bounds(sr.data)
    nums = sr.data.numerics
    n = int(nums.n_iteration_variables)

    before = float(sr.data.times.t_plant_pulse_burn)
    caller = Caller(sr.models, sr.data)
    caller._call_models_once(nums.xcm[:n])
    after_one_sweep = float(sr.data.times.t_plant_pulse_burn)

    # The value the rule actually takes: what the BASELINE's own idempotence
    # loop settles on at this deck's own starting design vector.  That is the
    # state the baseline arm itself enters its first optimiser iteration from,
    # and it is the state at which the variant's constraint 93 residual is
    # zero -- so the two arms start from the same design point rather than the
    # variant starting off its own consistency manifold.  One sweep is NOT
    # enough: the first sweep's burn time is computed from an entry loop
    # voltage that has not settled, and comes out three orders of magnitude
    # away (measured: 9.7e5 s against a settled 7.2e3 s on large_tokamak_nof).
    m = int(nums.n_equality_constraints) + int(nums.n_inequality_constraints)
    caller.call_models(nums.xcm[:n], m)
    after = float(sr.data.times.t_plant_pulse_burn)

    from process.models.pulse import burn_time_residual

    residual_at_start = float(
        burn_time_residual(
            after,
            sr.data.pf_coil.vs_cs_pf_total_burn,
            sr.data.physics.v_plasma_loop_burn,
            sr.data.times.t_plant_pulse_fusion_ramp,
        )
    )

    return {
        "t_plant_pulse_burn_after_first_sweep": after_one_sweep,
        "constraint_93_residual_at_chosen_start_s": residual_at_start,
        "rule": (
            "the burn time the baseline's own idempotence loop settles on at "
            "the deck's own starting design vector"
        ),
        "n_iteration_variables_baseline": n,
        "ixc_baseline": sorted(int(v) for v in nums.ixc[:n]),
        "n_equality_constraints_baseline": int(nums.n_equality_constraints),
        "n_inequality_constraints_baseline": int(nums.n_inequality_constraints),
        "i_pulsed_plant": int(sr.data.times.i_pulsed_plant)
        if hasattr(sr.data.times, "i_pulsed_plant")
        else int(sr.data.pulse.i_pulsed_plant),
        "t_plant_pulse_burn_before_first_sweep": before,
        "t_plant_pulse_burn_at_baseline_fixed_point": after,
        "t_plant_pulse_burn_at_baseline_fixed_point_hex": after.hex(),
        "vs_cs_pf_total_burn": float(sr.data.pf_coil.vs_cs_pf_total_burn),
        "v_plasma_loop_burn": float(sr.data.physics.v_plasma_loop_burn),
        "t_plant_pulse_fusion_ramp": float(sr.data.times.t_plant_pulse_fusion_ramp),
    }


def write_variant_deck(src: Path, dst: Path, t_burn: float, prov: dict) -> dict:
    """Frozen deck + three lines, with the provenance in the file itself.

    **Where the ``icc`` line goes is not cosmetic.**  PROCESS does not decide
    which constraints are equalities from the constraints themselves: it takes
    the **first ``n_equality_constraints`` entries of ``icc``, in the order the
    input file lists them** (``init.set_active_constraints``), and every deck
    here sets that count explicitly with the obsolete name ``neqns``.  A25's
    first derivation appended ``icc = 93`` at the end of the file, which made
    the burn-time *equality* the twenty-fourth **inequality**: the variant then
    solved a problem in which nothing forced the burn time onto its own
    consistency manifold, and it still returned ``ifail = 1`` on
    ``large_tokamak_nof`` with an objective that looked right.  Found by reading
    ``n_inequality_constraints`` in the gate table (23 -> 24), not by inspection.

    So the line is inserted **immediately after the last existing equality
    ``icc`` line**, and ``neqns`` is raised by one in the same edit.  Commented
    lines do not count towards the position.  On the evaluation deck this is
    also what makes the run possible at all: ``fsolve`` solves the equalities
    alone and needs as many of them as there are variables, so 2 variables + 2
    equalities becomes 3 + 3 rather than 3 + 2.
    """
    lines = src.read_text().splitlines()

    icc_at = [
        i for i, ln in enumerate(lines)
        if re.match(r"\s*icc\s*=", ln) and not ln.lstrip().startswith("*")
    ]
    neq_at = [
        i for i, ln in enumerate(lines)
        if re.match(r"\s*(neqns|n_equality_constraints)\s*=", ln)
        and not ln.lstrip().startswith("*")
    ]
    if len(neq_at) != 1:
        raise AssertionError(
            f"{src.name}: expected exactly one neqns / n_equality_constraints "
            f"line, found {len(neq_at)}"
        )
    neq_line = lines[neq_at[0]]
    m = re.match(r"\s*(neqns|n_equality_constraints)\s*=\s*([0-9]+)", neq_line)
    meq = int(m.group(2))
    if meq < 1 or meq > len(icc_at):
        raise AssertionError(
            f"{src.name}: neqns = {meq} but the deck has {len(icc_at)} icc lines"
        )

    insert_after = icc_at[meq - 1]
    lines[neq_at[0]] = (
        f"{m.group(1)} = {meq + 1}  * A25: was {meq}; constraint 93 appended "
        f"to the equality block"
    )
    lines.insert(
        insert_after + 1,
        f"icc = {ICC_BURN_TIME}  * A25: burn time consistency (EQUALITY -- "
        f"must sit inside the first neqns icc entries)",
    )

    header = [
        "*",
        "* ---------------------------------------------------------------",
        "* A25 (phase-b-variant): DERIVED deck -- do not edit by hand.",
        f"* Generated from {src.name} by a25_variant_deck.py.",
        "* Exactly three things change and nothing else:",
        f"*   icc = {ICC_BURN_TIME} inserted after icc line {meq} (the last equality),",
        f"*       and {m.group(1)} raised {meq} -> {meq + 1} in the same edit.",
        f"*   ixc = {IXC_BURN_TIME} appended -- the burn time becomes a design variable.",
        "*   t_plant_pulse_burn set to the value the BASELINE's own idempotence",
        "*       loop settles on at this deck's own starting design vector:",
        f"*       {t_burn!r} s (measured, not chosen).",
        "* ---------------------------------------------------------------",
        "*",
    ]
    tail = [
        "*",
        "* --- A25 (phase-b-variant): the burn-time lift ------------------",
        f"t_plant_pulse_burn = {t_burn!r}  * A25: baseline entry value, measured",
        f"ixc = {IXC_BURN_TIME}  * A25: t_plant_pulse_burn lifted to the design vector",
    ]
    dst.write_text("\n".join(header + lines + tail) + "\n")

    edit = {
        "n_icc_lines_source": len(icc_at),
        "neqns_source": meq,
        "neqns_variant": meq + 1,
        "icc_93_inserted_after_source_line": insert_after + 1,
        "icc_93_position_in_icc_list": meq + 1,
        "neqns_line_source": neq_line.strip(),
    }
    prov = dict(prov)
    prov["deck_edit"] = edit
    dst.with_suffix(".provenance.json").write_text(json.dumps(prov, indent=2))
    return edit


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--expect-tree", required=True)
    args = ap.parse_args()

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    import process

    pf = Path(process.__file__).resolve()
    actual = pf.parent.parent
    expect = Path(args.expect_tree).resolve()
    if actual != expect:
        raise SystemExit(
            f"WRONG TREE: imported {pf} (tree {actual}), expected exactly "
            f"{expect}. Set PYTHONPATH={expect} for this subprocess."
        )

    src = HERE / "scenarios" / f"{args.scenario}.IN.DAT"
    # SingleRun writes OUT.DAT/MFILE.DAT next to its input, so the probe runs
    # on a copy inside the run directory.
    probe_deck = outdir / f"{args.scenario}.IN.DAT"
    probe_deck.write_text(src.read_text())

    out: dict = {
        "scenario": args.scenario,
        "tree": str(actual),
        "source_deck": str(src),
        "source_deck_bytes": src.stat().st_size,
    }
    try:
        out["entry"] = entry_burn_time(probe_deck)
        out["status"] = "ok"
    except Exception:
        out["status"] = "crashed"
        out["traceback"] = traceback.format_exc()
        (outdir / "deck.json").write_text(json.dumps(out, indent=2))
        print(json.dumps(out, indent=2))
        return 1

    t_burn = out["entry"]["t_plant_pulse_burn_at_baseline_fixed_point"]
    dst = outdir / f"{args.scenario}_lifted.IN.DAT"
    out["deck_edit"] = write_variant_deck(src, dst, t_burn, out)
    out["variant_deck"] = str(dst)
    (outdir / "deck.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
