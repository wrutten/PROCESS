#!/usr/bin/env python
"""Gate G2 — what the arrangement's method-level move does.

One gate about one switch.  ``PROCESS_ARCH_ARRANGEMENT_METHOD`` — *the prime*
in the mechanism's own vocabulary — runs the first-wall model's geometry method
so that the node which reads those two lengths reads **this** pass's values
instead of the previous pass's.

``G2`` — *the prime changes nothing once the first-wall model has run*
    From each configuration's reference exit snapshot, one flat evaluation and
    one partitioned evaluation, each with the prime on and with it off.  The
    exit states must be bit-identical on **N of N** components (840 / 846 /
    827).  This is the *inertness* claim: after call 1 the two lengths are
    already the converged ones, so priming them again writes the same bits.

**G3 / G3c (the cold chain) was dropped in V5** — the user's ruling of
2026-09-29 on the V5 plan's §12 Q3: its construction, the prime at every sweep
head reproducing the earlier census's cold-chain counts, does not exist once
the prime moves to once-per-evaluation pre-processing (list item 8, driver
change DR10); G2's re-formed criterion (the once-per-evaluation form's exit
states bit-identical to the per-sweep form on the gate job set) plus the
count-neutrality gate GC cover what it bound.  Its body, its teeth and the
previous revision's figures it reproduced were removed by task **A98
(v5-reporting-trim)**; V4's copy keeps them.  **G2's re-forming is item 8's
task, not this one's**: the gate below is V4's G2, unchanged.

Written by task **A52 (harness-gates)**.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from ..core import framework
from . import gates as gates_mod
from . import reproduction as reproduction_mod
from ..core import pool as pool_mod
from ..core import records as records_mod
from ..core.config import Campaign
from ..core.framework import Gate, GateError, Tooth

#: The switch the two gates vary, and the value that turns it on.  Read from the
#: registry rather than written out, so that a rename moves this with it.
PRIME_TERM = "arrangement_method"

#: The two arrangements G2 compares the prime across: the flat control and the
#: partitioned arm.  Both are evaluation-phase arms, because one ``call_models``
#: is all the claim is about.
G2_ARRANGEMENTS: tuple[tuple[str, str], ...] = (("flat", "A0"), ("partitioned", "A2"))

_HELD: dict[str, Any] = {}


# --------------------------------------------------------------------------
# composing a run with the prime deliberately on or off
# --------------------------------------------------------------------------


def prime_override(*, on: bool) -> dict[str, Any]:
    """The environment override that puts the prime on or off for one run.

    An arm composes the prime from the matrix; these two gates need it varied
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
# G2 -- the prime's fixed-point map
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
                label = "prime_on" if on else "prime_off"
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


def prime_map_body(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    """G2: the prime is inert once the first-wall model has run."""
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
                "block_sweeps_off": (off.get("block_loop_totals") or {}).get(
                    "block_sweeps"
                ),
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
                "prime_on_calls_the_method_once_per_sweep": (
                    row["prime_calls_on"] is not None
                    and row["prime_calls_on"] == row["block_sweeps_on"]
                    and (row["prime_calls_on"] or 0) > 0
                ),
            }
            row["checks"] = checks
            row["passed"] = all(checks.values())
            n_compared += comparison["n_components"]
            n_mismatched += comparison["n_differing"]
            passed = passed and row["passed"]
            rows.append(row)
    _HELD["g2_rows"] = rows
    return {
        "passed": passed,
        "criterion": (
            "from each configuration's reference exit snapshot, one flat and "
            "one partitioned call_models with the arrangement's method-level "
            "move on and off: the exit states bit-identical on N of N "
            "components, and the method called once per sweep when on and not "
            "at all when off"
        ),
        "criterion_source": (
            "the experiment plan §3.9's G2 row, restated here; nothing is "
            "imported from the earlier revision's directories"
        ),
        "population": (
            f"{len([r for r in rows if 'skipped' not in r])} arrangement/"
            f"configuration pair(s); "
            f"{len([j for *_r, j in plan])} evaluations; "
            f"{n_compared} components compared"
        ),
        "n_compared": n_compared,
        "n_mismatched": n_mismatched,
        "components_declared": {
            c.name: c.n_coupling_components for c in campaign.configurations
        },
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
    )


def prime_map_gate(campaign: Campaign) -> Gate:
    return Gate(
        name="prime_map",
        plan_name="G2",
        needs_runs=True,
        binds=(
            "the claim that the arrangement's method-level move changes "
            "nothing once the first-wall model has run"
        ),
        what_it_proves=(
            "entered from the fixed point, a flat and a partitioned "
            "call_models leave the coupling state bit-identical whether the "
            "method runs at the head of every sweep or not at all"
        ),
        body=lambda *, resume=False: prime_map_body(campaign, resume=resume),
        jobs=lambda: gates_mod.job_rows(prime_map_jobs_read, campaign),
        teeth=_prime_map_teeth(campaign),
    )
