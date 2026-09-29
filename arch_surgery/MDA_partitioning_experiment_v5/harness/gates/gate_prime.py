#!/usr/bin/env python
"""Gate G2 — what the arrangement's method-level move does, in its once-per-evaluation form.

``PROCESS_ARCH_ARRANGEMENT_METHOD`` — *the prime* in the mechanism's own
vocabulary — runs the first-wall model's geometry method, a run-constant of two
input-file values, so that the node which reads those two lengths (``build``,
which the partitioned schedule runs before ``fw``) reads **this** evaluation's
values instead of the previous one's.  V4 executed it at the head of **every
sweep** (about 9–15 stamped calls per evaluation); driver change **DR10** (V5
list item 8, task A99 (v5-schedule-and-prime)) executes it **once per
evaluation, before the first block**, as pre-processing of the sequenced
schedule.  The user: *"It is pre-processing before the partitioned MDAs can
start."*

The gate binds two claims about that form.

**(i) The prime changes nothing once the first-wall model has run.**  From each
configuration's reference exit snapshot, one flat evaluation and one
partitioned evaluation, each with the prime on and with it off.  The exit
states must be bit-identical on **N of N** components (840 / 846 / 827).  This
is the *inertness* claim: after the first evaluation the two lengths are
already the converged ones, so priming them again writes the same bits.  With
the prime on, the method is called **once** — the evaluation count of a
Phase A run — and with it off, not at all.

**(ii) The once-per-evaluation form leaves the same exit states as V4's
per-sweep form.**  Gate GC's job set — both phases, every arm, one seed per
configuration — was run under the per-sweep form (the side labelled ``DR9``)
and again under this form (``DR10``), and GC compared every coupling-state
file bit for bit and every count to the digit, with ``n_arrangement_method_calls``
under the declared rule ``once_per_evaluation``.  That comparison exists only
across the DR10 straddle — the per-sweep form is gone from the tree once DR10
is in it — so this gate reads GC's record of that one straddle
(:func:`gate_count_neutrality.straddle_record_path`) and requires: the straddle
is a real one (two commits), its rule is ``once_per_evaluation``, and every
row whose arm composes the prime (``A2``, ``B2``) has 0 differing components
and a passing prime-count check.  A missing record, or one whose rule is not
DR10's, is a refusal here and not a pass.

Criteria inherited, and where they come from
--------------------------------------------
(i) is the previous revision's G2 criterion restated: experiment plan §3.9,
*"from each deck's reference exit snapshot: one ``flat_state`` call and one
``per_module`` call, prime on vs off, exit states bit-identical on N/N
components — 840 (nof) / 846 (lad) / 827 (st)"*; tooth *"a doctored snapshot
component trips the comparison"*.  The once-per-sweep count check that
criterion carried is replaced by the once-per-evaluation one (V5 plan §7, G2
"kept, re-formed").  (ii) is V5 list item 8's requirement — *"the exit states
of a job set bit-identical to V4's per-sweep form (the G2 construction)"* —
and the V5 plan's G2 row.

**G3 / G3c (``cold_chain``) are dropped** (the user, 2026-09-29, V5 plan §12
Q3): their construction — the prime at every sweep head reproducing A35's
cold-chain counts — does not exist once DR10 lands; (ii) above and GC cover
what they bound.  Their code, previous-revision figures and teeth were removed
from this module by A99; the previous revision's gate records stand in V4's
tree.

Written by task **A52 (harness-gates)**; re-formed by **A99
(v5-schedule-and-prime)**.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from . import gates as gates_mod
from . import reproduction as reproduction_mod
from ..core import pool as pool_mod
from ..core import records as records_mod
from ..core.config import Campaign
from ..core.framework import Gate, GateError, Tooth

#: The switch the gate varies, and the value that turns it on.  Read from the
#: registry rather than written out, so that a rename moves this with it.
PRIME_TERM = "arrangement_method"

#: The two arrangements G2 compares the prime across: the flat control and the
#: partitioned arm.  Both are evaluation-phase arms, because one ``call_models``
#: is all the claim is about.
G2_ARRANGEMENTS: tuple[tuple[str, str], ...] = (("flat", "A0"), ("partitioned", "A2"))

#: The two lengths the prime computes, and therefore the edge it cuts.
CARRIER_COMPONENTS: tuple[str, ...] = (
    "build.dr_fw_inboard",
    "build.dr_fw_outboard",
)

#: The GC straddle that compares the per-sweep form (its before side) with the
#: once-per-evaluation form (its after side): the labels GC declares for DR9
#: and DR10.
PER_SWEEP_TO_PER_EVALUATION: tuple[str, str] = ("DR9", "DR10")

#: The rule GC must have applied on that straddle.
PER_EVALUATION_RULE = "once_per_evaluation"

_HELD: dict[str, Any] = {}


# --------------------------------------------------------------------------
# composing a run with the prime deliberately on or off
# --------------------------------------------------------------------------


def prime_override(*, on: bool) -> dict[str, Any]:
    """The environment override that puts the prime on or off for one run.

    An arm composes the prime from the matrix; this gate needs it varied
    **against** the matrix, which is what ``Job.override_env`` is for.  The
    switch's driver name and its legal value come from the registry, so a rename
    moves them and a value the driver does not accept is refused by the driver's
    own guard rather than resolved three layers down.
    """
    from ..experiment import switches as switches_mod

    switch = switches_mod.REGISTRY[PRIME_TERM]
    name = switch.driver_name
    if name is None:
        raise GateError(
            f"the switch registry gives {PRIME_TERM!r} no driver name, so this "
            f"tree cannot be asked to run with the prime on or off; a gate "
            f"that composed the environment without it would run a different "
            f"arrangement under this gate's name"
        )
    if not on:
        return {name: None}
    values = switch.values
    if not values:
        raise GateError(
            f"the switch registry declares no legal value for {PRIME_TERM!r}"
        )
    return {name: values[0]}


# --------------------------------------------------------------------------
# G2 -- the prime's fixed-point map, and its once-per-evaluation form
# --------------------------------------------------------------------------


def prime_map_root(campaign: Campaign) -> Path:
    """Where G2's verdict goes.  Its runs are shared-pool jobs."""
    return Path(campaign.runs_dir) / gates_mod.GATES_SUBPATH / "prime_map"


def prime_map_jobs(
    campaign: Campaign, references: Mapping[str, Any]
) -> list[tuple[str, str, bool, pool_mod.Job]]:
    """Four runs per configuration: two arrangements × the prime on and off."""
    plan: list[tuple[str, str, bool, pool_mod.Job]] = []
    for config in campaign.configurations:
        reference = references[config.name]
        for arrangement, arm in G2_ARRANGEMENTS:
            if arm in config.skips:
                continue
            for on in (False, True):
                plan.append(
                    (
                        config.name,
                        arrangement,
                        on,
                        pool_mod.Job(
                            phase="A",
                            arm=arm,
                            config=config,
                            seed=0,
                            regime="unperturbed",
                            delta=None,
                            pin_hex=reproduction_mod.entry_pin(config, arm, reference),
                            entry_state=Path(reference["snapshot"]),
                            run_kind="gate",
                            override_env=prime_override(on=on),
                        ),
                    )
                )
    return plan


def prime_map_jobs_read(campaign: Campaign) -> list[pool_mod.Job]:
    """Every job G2 reads: the references and the four runs per configuration."""
    references = gates_mod.entry_references_from_records(campaign)
    return gates_mod.entry_reference_jobs(campaign) + [
        job for *_rest, job in prime_map_jobs(campaign, references)
    ]


def full_state_compare(
    a: Mapping[str, Any], b: Mapping[str, Any]
) -> dict[str, Any]:
    """Two exit snapshots, component by component, exactly.

    The earlier revision's comparison, restated: the union of the two key sets,
    every component compared for equality of its recorded value — floats travel
    as hex literals, so this is bit equality and no tolerance is applied or
    available — and **every kind of component**, not only the floats.
    """
    keys = sorted(set(a) | set(b))
    differing = [k for k in keys if a.get(k) != b.get(k)]
    return {
        "n_components": len(keys),
        "n_differing": len(differing),
        "differing": differing[:20],
        "only_in_first": sorted(set(a) - set(b))[:20],
        "only_in_second": sorted(set(b) - set(a))[:20],
    }


def _exit_state(directory: Path, *, key: str) -> dict[str, Any]:
    path = Path(directory) / "y_exit.json"
    if not path.exists():
        raise GateError(
            f"G2 has no exit state for {key}: {path} is not there.  A gate that "
            f"cannot find one of the two states it compares must refuse, never "
            f"pass over an empty comparison (trap T11)."
        )
    return json.loads(path.read_text())


def per_sweep_form_comparison(campaign: Campaign) -> dict[str, Any]:
    """Part (ii): GC's record of the per-sweep -> once-per-evaluation straddle.

    Read, never made here: the per-sweep form no longer exists in the tree, so
    the comparison can only have been made across the DR10 straddle, by gate
    GC, at that commit.  A missing record or a record of another rule is a
    failing check with the reason, not a pass over nothing.
    """
    from . import gate_count_neutrality as gc_mod

    before_label, after_label = PER_SWEEP_TO_PER_EVALUATION
    path = gc_mod.straddle_record_path(campaign, before_label, after_label)
    out: dict[str, Any] = {
        "record": str(path),
        "straddle_labels": [before_label, after_label],
        "rule_required": PER_EVALUATION_RULE,
    }
    if not path.exists():
        out["passed"] = False
        out["failed_at"] = (
            f"no GC record of the {before_label} -> {after_label} straddle at "
            f"{path}: the once-per-evaluation form has not been compared with "
            f"the per-sweep form, and this gate cannot make that comparison "
            f"itself"
        )
        return out
    record = json.loads(path.read_text())
    straddle = record.get("straddle") or {}
    rows = [
        r
        for r in (record.get("rows") or [])
        if (r.get("prime_calls") or {}).get("primed")
    ]
    n_components = sum(int(r["states"]["n_components_compared"]) for r in rows)
    n_differing = sum(int(r["states"]["n_components_differing"]) for r in rows)
    out.update(
        {
            "gc_verdict_passed": bool(record.get("passed")),
            "gc_tree_git_head": record.get("tree_git_head"),
            "before_commits": straddle.get("before_commits"),
            "after_commits": straddle.get("after_commits"),
            "rule_applied": record.get("prime_calls_rule"),
            "n_primed_pairs": len(rows),
            "primed_pairs": [r["key"] for r in rows],
            "n_components_compared": n_components,
            "n_components_differing": n_differing,
            "prime_counts_after": {
                r["key"]: (r["prime_calls"].get("checks") or {}).get("whole_run")
                for r in rows
            },
        }
    )
    checks = {
        "straddles_two_commits": straddle.get("straddles_a_change") is True,
        "rule_is_once_per_evaluation": record.get("prime_calls_rule") == PER_EVALUATION_RULE,
        "at_least_one_primed_pair": len(rows) > 0,
        "every_primed_pair_bit_identical": (
            len(rows) > 0 and all(r["states"]["n_components_differing"] == 0 for r in rows)
        ),
        "every_primed_pair_count_as_declared": (
            len(rows) > 0 and all(r["prime_calls"].get("passed") for r in rows)
        ),
        "gc_passed": bool(record.get("passed")),
    }
    out["checks"] = checks
    out["passed"] = all(checks.values())
    return out


def prime_map_body(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    """G2: the prime is inert once the first-wall model has run, and its once-per-evaluation form leaves V4's exit states."""
    references = gates_mod.entry_references(campaign, resume=resume)
    plan = prime_map_jobs(campaign, references)
    pool_mod.run_all([job for *_rest, job in plan], campaign, resume=resume)

    by_key = {(c, a, on): job for c, a, on, job in plan}
    _HELD["g2_dirs"] = {
        (c, a): Path(job.outdir) for c, a, on, job in plan if on
    }
    rows: list[dict[str, Any]] = []
    passed = True
    n_compared = 0
    n_mismatched = 0
    for config in campaign.configurations:
        for arrangement, arm in G2_ARRANGEMENTS:
            if arm in config.skips:
                rows.append(
                    {
                        "configuration": config.name,
                        "arrangement": arrangement,
                        "skipped": config.skips[arm],
                    }
                )
                continue
            off_job = by_key[(config.name, arrangement, False)]
            on_job = by_key[(config.name, arrangement, True)]
            off = records_mod.read(off_job.outdir)
            on = records_mod.read(on_job.outdir)
            key = f"{config.name}/{arrangement}"
            comparison = full_state_compare(
                _exit_state(off_job.outdir, key=f"{key}/prime_off")["state"],
                _exit_state(on_job.outdir, key=f"{key}/prime_on")["state"],
            )
            declared = config.n_coupling_components
            row = {
                "configuration": config.name,
                "arrangement": arrangement,
                "arm": arm,
                "entered_from": references[config.name]["snapshot"],
                "statuses": [off.get("status"), on.get("status")],
                "n_components": comparison["n_components"],
                "n_components_declared": declared,
                "n_differing": comparison["n_differing"],
                "differing": comparison["differing"],
                "prime_calls_off": off.get("n_arrangement_method_calls"),
                "prime_calls_on": on.get("n_arrangement_method_calls"),
                "evaluations_on": 1,
                "block_sweeps_on": (on.get("block_loop_totals") or {}).get(
                    "block_sweeps"
                ),
            }
            checks = {
                "both_runs_finished": row["statuses"] == ["ok", "ok"],
                "every_declared_component_compared": (
                    comparison["n_components"] == declared
                ),
                "exit_states_bit_identical": comparison["n_differing"] == 0,
                "prime_off_calls_the_method_zero_times": row["prime_calls_off"] == 0,
                # DR10: once per evaluation -- a Phase A run is one evaluation.
                "prime_on_calls_the_method_once_per_evaluation": (
                    row["prime_calls_on"] == row["evaluations_on"]
                ),
            }
            row["checks"] = checks
            row["passed"] = all(checks.values())
            n_compared += comparison["n_components"]
            n_mismatched += comparison["n_differing"]
            passed = passed and row["passed"]
            rows.append(row)
    per_sweep = per_sweep_form_comparison(campaign)
    passed = passed and per_sweep["passed"]
    _HELD["g2_rows"] = rows
    _HELD["per_sweep"] = per_sweep
    return {
        "passed": passed,
        "criterion": (
            "(i) from each configuration's reference exit snapshot, one flat "
            "and one partitioned call_models with the arrangement's "
            "method-level move on and off: the exit states bit-identical on N "
            "of N components, and the method called once per evaluation when "
            "on and not at all when off; (ii) on gate GC's job set, the "
            "once-per-evaluation form's exit states bit-identical to the "
            "per-sweep form's on every arm that composes the prime, read from "
            "GC's record of the DR9 -> DR10 straddle"
        ),
        "criterion_source": (
            "the experiment plan §3.9's G2 row restated for the "
            "once-per-evaluation form (V5 plan §7, list item 8); nothing is "
            "imported from the earlier revision's directories"
        ),
        "population": (
            f"(i) {len([r for r in rows if 'skipped' not in r])} arrangement/"
            f"configuration pair(s); {len([j for *_r, j in plan])} evaluations; "
            f"{n_compared} components compared, {n_mismatched} differing.  "
            f"(ii) {per_sweep.get('n_primed_pairs', 0)} primed pair(s) of GC's "
            f"{'/'.join(PER_SWEEP_TO_PER_EVALUATION)} straddle; "
            f"{per_sweep.get('n_components_compared', 0)} components compared, "
            f"{per_sweep.get('n_components_differing', 0)} differing"
        ),
        "n_compared": n_compared,
        "n_mismatched": n_mismatched,
        "n_components_compared": per_sweep.get("n_components_compared", 0),
        "n_components_differing": per_sweep.get("n_components_differing", 0),
        "components_declared": {
            c.name: c.n_coupling_components for c in campaign.configurations
        },
        "per_sweep_form": per_sweep,
        "rows": rows,
    }


def _prime_map_teeth(campaign: Campaign) -> tuple[Tooth, ...]:
    def doctored_component() -> tuple[bool, str]:
        rows = _HELD.get("g2_rows") or []
        live = [r for r in rows if "skipped" not in r]
        if not live:
            return False, "the gate compared nothing, so nothing can be doctored"
        row = live[-1]
        job_dir = _HELD["g2_dirs"][(row["configuration"], row["arrangement"])]
        state = dict(json.loads((job_dir / "y_exit.json").read_text())["state"])
        chosen = None
        for name in sorted(state):
            value = state[name]
            if not (isinstance(value, dict) and value.get("k") == "f"):
                continue
            number = float.fromhex(value["hex"])
            if math.isfinite(number) and number != 0.0:
                chosen = (
                    name,
                    value["hex"],
                    math.nextafter(number, math.inf).hex(),
                )
                break
        if chosen is None:
            return False, (
                "no finite non-zero float component in the exit state to "
                "doctor: that is itself a finding, report it"
            )
        name, before, after = chosen
        clean = dict(state)
        state[name] = {"k": "f", "hex": after}
        result = full_state_compare(clean, state)
        return result["n_differing"] == 1, (
            f"one unit in the last place on {name} ({before} → {after}) in a "
            f"copy of {row['configuration']}/{row['arrangement']}'s prime-on "
            f"exit state: the comparison reports "
            f"{result['n_differing']} differing component(s) of "
            f"{result['n_components']}"
        )

    def missing_component() -> tuple[bool, str]:
        rows = _HELD.get("g2_rows") or []
        live = [r for r in rows if "skipped" not in r]
        if not live:
            return False, "the gate compared nothing"
        row = live[-1]
        job_dir = _HELD["g2_dirs"][(row["configuration"], row["arrangement"])]
        state = dict(json.loads((job_dir / "y_exit.json").read_text())["state"])
        dropped = sorted(state)[0]
        short = {k: v for k, v in state.items() if k != dropped}
        result = full_state_compare(state, short)
        caught = result["n_differing"] == 1 and result["only_in_first"] == [dropped]
        return caught, (
            f"component {dropped} removed from one side: the comparison "
            f"reports {result['n_differing']} differing over "
            f"{result['n_components']} — a short state is a differing state, "
            f"not a smaller population silently compared"
        )

    def doctored_straddle_row() -> tuple[bool, str]:
        per_sweep = _HELD.get("per_sweep") or {}
        if not per_sweep.get("passed"):
            return False, "part (ii) did not pass, so a doctored copy of it proves nothing"
        from . import gate_count_neutrality as gc_mod

        path = Path(per_sweep["record"])
        record = json.loads(path.read_text())
        rows = [r for r in record["rows"] if (r.get("prime_calls") or {}).get("primed")]
        row = rows[-1]
        row["states"]["n_components_differing"] = 1
        doctored_path = Path(campaign.runs_dir) / gates_mod.GATES_SUBPATH / "prime_map" / "_tooth_doctored_straddle.json"
        doctored_path.parent.mkdir(parents=True, exist_ok=True)
        doctored_path.write_text(json.dumps(record))
        original = gc_mod.straddle_record_path
        try:
            gc_mod.straddle_record_path = lambda *_a, **_k: doctored_path
            result = per_sweep_form_comparison(campaign)
        finally:
            gc_mod.straddle_record_path = original
            doctored_path.unlink(missing_ok=True)
        return (not result["passed"]) and result["checks"]["every_primed_pair_bit_identical"] is False, (
            f"one differing component written into a copy of GC's "
            f"{'/'.join(PER_SWEEP_TO_PER_EVALUATION)} record on {row['key']}: "
            f"part (ii) reports passed = {result['passed']}"
        )

    return (
        Tooth(
            name="a doctored snapshot component",
            what="one unit in the last place on one float of a prime-on exit state",
            must="be the one and only differing component",
            check=doctored_component,
        ),
        Tooth(
            name="a component missing from one side",
            what="one component deleted from a copy of an exit state",
            must=(
                "be counted as differing rather than quietly shrinking the "
                "population (trap T11)"
            ),
            check=missing_component,
        ),
        Tooth(
            name="a doctored straddle row",
            what="one differing component written into a copy of GC's DR9 -> DR10 record",
            must="make part (ii) fail",
            check=doctored_straddle_row,
        ),
    )


def prime_map_gate(campaign: Campaign) -> Gate:
    return Gate(
        name="prime_map",
        plan_name="G2",
        needs_runs=True,
        binds=(
            "the arrangement's method-level move in its once-per-evaluation "
            "form: inert once the first-wall model has run, and the same exit "
            "states as the per-sweep form"
        ),
        what_it_proves=(
            "entered from the fixed point, a flat and a partitioned "
            "call_models leave the coupling state bit-identical whether the "
            "method runs once before the first block or not at all; and on "
            "GC's job set the once-per-evaluation form leaves every exit state "
            "bit-identical to the per-sweep form's"
        ),
        body=lambda *, resume=False: prime_map_body(campaign, resume=resume),
        jobs=lambda: gates_mod.job_rows(prime_map_jobs_read, campaign),
        reads_from=("count_neutrality",),
        teeth=_prime_map_teeth(campaign),
    )
