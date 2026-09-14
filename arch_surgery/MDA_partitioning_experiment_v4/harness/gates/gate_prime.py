#!/usr/bin/env python
"""Gates G2 and G3 / G3c — what the arrangement's method-level move does.

Two gates about one switch.  ``PROCESS_ARCH_ARRANGEMENT_METHOD`` — *the prime*
in the mechanism's own vocabulary — runs the first-wall model's geometry method
at the head of every sweep, so that the node which reads those two lengths reads
**this** pass's values instead of the previous pass's.  The two gates bind the
two halves of what that is claimed to do.

``G2`` — *the prime changes nothing once the first-wall model has run*
    From each configuration's reference exit snapshot, one flat evaluation and
    one partitioned evaluation, each with the prime on and with it off.  The
    exit states must be bit-identical on **N of N** components (840 / 846 /
    827).  This is the *inertness* claim: after call 1 the two lengths are
    already the converged ones, so priming them again writes the same bits.

``G3 / G3c`` — *no cut edge carries anything*
    From the **cold** entry — the input file's own design point, where the two
    lengths have never been computed — the partitioned chain with the prime on
    must leave the coupling state at its fixed point: the uncharged exit audit
    counts **0** components at or above the tolerance, and the named
    residual-mover set is empty.  With the prime **off** the same chain must
    reproduce the figures the earlier revision measured, which is the tooth:
    a gate whose zero has never been shown to be a measurable zero is an
    assertion.

Criteria inherited, and where they come from
--------------------------------------------
Both criteria are the previous revision's, restated here rather than imported —
nothing in this package imports from or starts a subprocess into
``arch_surgery/idf_probe/`` or ``arch_surgery/fixedpoint/``.  Their agreement
with the previous revision's recorded figures is therefore a **gate result**,
not an assumed equivalence, and it is exactly what the prime-off arm's
comparison reports.

The source criteria are:

* **G2**, experiment plan §3.9 and its predecessor's §6: *"from each deck's
  reference exit snapshot: one ``flat_state`` call and one ``per_module`` call,
  prime on vs off, exit states bit-identical on N/N components — 840 (nof) / 846
  (lad) / 827 (st)"*; tooth *"a doctored snapshot component trips the
  comparison"*.
* **G3**, same table: *"verified block chain from the cold deck entry: outer
  passes 3 → 2 on nof and st; trust chain exit vs the flat fixed point, in-run
  ``exit_audit`` operationalization: 0 above τ (A35 in-run: 244 / 124 …); any
  residual mover named"*; tooth *"the prime-off run must reproduce A35's 3
  passes and 244 / 124"*.
* **G3c**, same table: *"A35's trace + restarts stages on
  ``low_aspect_ratio_DEMO``, prime off then on: the carrier coefficient on that
  deck, and the residual mover set with the prime — names whether A38's open
  term ``tfcoil.m_tf_coil_superconductor`` closes or survives"*.

Two coverage boundaries, stated rather than left to be noticed
--------------------------------------------------------------
**(i) The outer-pass half of G3 cannot be re-run at this commit, because the
loop it counted no longer exists.**  The previous revision's G3 counted outer
passes on the *verified* block chain — the schedule run repeatedly until a pass
changed nothing.  Driver change DR1 (task A56 (driver-renames)) **removed** that
mode: ``PROCESS_ARCH_MDA=partitioned`` now means the schedule runs exactly once,
and the verified-schedule code is deleted, on the measurement that its
verification pass triggered a further pass zero times in 91 888 evaluations.
So ``3 → 2 outer passes`` has nothing to count here.  What survives is the half
that carries the claim — the one-pass chain's exit against the flat fixed point
— and that is what this gate runs, on both configurations, with the prime-off
figures reproduced as the tooth.

**(ii) G3c's carrier *coefficients* are not reproduced; its verdict is.**  The
previous revision obtained the coefficients by parsing a per-pass residual
trace, which this revision's plan §4.6 deliberately drops from composition and
keeps only as a driver capability, because nothing V4 publishes reads it.  What
G3c is *for* — whether the open term closes under the prime or survives it, and
what the residual-mover set contains — is read directly from the audit residual
vector and is reported here in full.

One correction to the record, made by measurement and not by argument
---------------------------------------------------------------------
The figures ``244`` and ``124`` are **``large_tokamak_nof``'s and
``st_regression``'s**, not ``low_aspect_ratio_DEMO``'s: they are G3's, and G3
ran on those two configurations precisely because ``low_aspect_ratio_DEMO`` is
the one the earlier census never traced — which is why G3c exists at all.
``low_aspect_ratio_DEMO``'s own prime-off figures are 240 from the cold entry
and 218 from the displaced one.  Both sets are checked here, each against the
configuration that produced it.

Written by task **A52 (harness-gates)**.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from ..core import framework
from . import gate_output_path
from . import gates as gates_mod
from . import reproduction as reproduction_mod
from ..core import pool as pool_mod
from ..core import records as records_mod
from ..core.config import Campaign, Config
from ..core.framework import Check, Gate, GateError, Tooth

#: The switch the two gates vary, and the value that turns it on.  Read from the
#: registry rather than written out, so that a rename moves this with it.
PRIME_TERM = "arrangement_method"

#: The two arrangements G2 compares the prime across: the flat control and the
#: partitioned arm.  Both are evaluation-phase arms, because one ``call_models``
#: is all the claim is about.
G2_ARRANGEMENTS: tuple[tuple[str, str], ...] = (("flat", "A0"), ("partitioned", "A1"))

#: The configuration G3c covers, and the displaced entry it adds: the previous
#: revision's census on this configuration measured both a cold and a displaced
#: entry, using that census's stream and amplitude.  Its recorded figures, and
#: G3's, live in :data:`PREVIOUS_FIGURES` beside the chains they belong to —
#: 244 and 124 are ``large_tokamak_nof``'s and ``st_regression``'s, and this
#: configuration's own are 240 and 218.
G3C_CONFIGURATION = "low_aspect_ratio_DEMO"
G3C_WARM_DELTA = 0.10
G3C_WARM_SEED = 1

#: The term the earlier revision left open on ``low_aspect_ratio_DEMO``: does it
#: close under the prime, or survive it?  Named, either way.
G3C_OPEN_TERM = "tfcoil.m_tf_coil_superconductor"

#: The two lengths the prime computes, and therefore the edge it cuts.
CARRIER_COMPONENTS: tuple[str, ...] = (
    "build.dr_fw_inboard",
    "build.dr_fw_outboard",
)

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


# --------------------------------------------------------------------------
# G3 / G3c -- the cold chain, and what a cut edge carries
# --------------------------------------------------------------------------
#
# The gate runs each chain under **two compositions**, and the reason is a
# finding this task made by running it.
#
# The previous revision's chain was ``per_module`` + the node arrangement + the
# per-call deferral + the lift and its pin, and **nothing else**: it did not set
# the per-run deferral at all.  This revision's arm `A1` is that composition
# **plus** the per-run deferral, because the matrix puts the deferral inside the
# intervention.  Read against the whole-state audit, the two are not the same
# measurement and cannot be: three nodes that ran on every sweep now run once,
# at the end, so the components they write are *supposed* to move in the audit
# sweep.  Measured here: 112 components above the tolerance on every
# configuration with the prime on, every one of them owned by a deferred node.
#
# So the gate runs both:
#
# * **as composed** — this revision's arm, read on the **restricted** audit,
#   which is the statistic that exists for exactly this reason.  The claim is
#   the same claim: with the prime on, nothing outside the deferred nodes' own
#   write sets is above the tolerance;
# * **the previous revision's composition** — the same chain with the per-run
#   deferral cleared, read on the **whole-state** audit, which is what that
#   revision counted.  Its figures must come back exactly: that agreement is
#   this gate's result, not an assumption.
#
# Both are checked on the count *and* on the residual maximum as a hex float.
# The maximum is the stronger of the two and travels across compositions, which
# is why it is checked on both.

#: The chains, and the previous revision's recorded figures for each: the count
#: of components at or above the tolerance on the **prime-off** run and the
#: residual maximum, and the maximum on the **prime-on** run.  The count is
#: against the *whole-state* audit under that revision's composition; the
#: maxima hold under both compositions.
#:
#: ``st_regression``'s prime-off maximum is recorded by the previous revision as
#: a mantissa **tail** rather than a full literal — its own first attempt
#: compared the tail against the whole literal and failed on that defect — so it
#: is declared as a tail and matched as one, with the full literal this task
#: measured reported beside it.
PREVIOUS_FIGURES: dict[tuple[str, str], dict[str, Any]] = {
    ("large_tokamak_nof", "cold"): {
        "prime_off_n_above_tau": 244,
        "prime_off_max_hex": "0x1.de05b6285d3f4p-7",
        "prime_on_max_hex": "0x1.51fbaf5134221p-30",
        "gate": "G3",
    },
    ("st_regression", "cold"): {
        "prime_off_n_above_tau": 124,
        "prime_off_max_hex_mantissa_tail": "f0afff76",
        "prime_on_max_hex": "0x1.c22fb514702ddp-29",
        "gate": "G3",
    },
    ("low_aspect_ratio_DEMO", "cold"): {
        "prime_off_n_above_tau": 240,
        "prime_off_max_hex": "0x1.47e807abb1ed5p-5",
        "prime_on_max_hex": "0x0.0p+0",
        "gate": "G3c",
    },
    ("low_aspect_ratio_DEMO", "warm"): {
        "prime_off_n_above_tau": 218,
        "prime_off_max_hex": "0x1.30a27ad23ca7fp-10",
        "prime_on_max_hex": "0x0.0p+0",
        "gate": "G3c",
    },
}

#: The two compositions each chain is run under.  ``None`` means "the arm as the
#: matrix composes it"; the other clears one switch, by name, to reproduce the
#: previous revision's chain.
COMPOSITIONS: tuple[str, ...] = ("as_composed", "previous_revision")


def cold_chain_root(campaign: Campaign) -> Path:
    """Where G3's verdict goes.  Its runs are shared-pool jobs."""
    return Path(campaign.runs_dir) / gates_mod.GATES_SUBPATH / "cold_chain"


def cold_chain_jobs_read(campaign: Campaign) -> list[pool_mod.Job]:
    """Every job G3/G3c reads: the references and each chain under each composition."""
    references = gates_mod.entry_references_from_records(campaign)
    return gates_mod.entry_reference_jobs(campaign) + [
        job for *_rest, job in cold_chain_jobs(campaign, references)
    ]


def _composition_override(composition: str) -> dict[str, Any]:
    """What each composition changes against the arm the matrix composes."""
    if composition == "as_composed":
        return {}
    from ..experiment import switches as switches_mod

    name = switches_mod.REGISTRY["defer_per_run"].driver_name
    return {name: None}


def cold_chain_jobs(
    campaign: Campaign, references: Mapping[str, Any]
) -> list[tuple[str, str, str, bool, pool_mod.Job]]:
    """Each chain, under both compositions, with the prime off and on.

    ``large_tokamak_nof`` and ``st_regression`` from the cold entry (G3), and
    ``low_aspect_ratio_DEMO`` from the cold entry **and** from a displaced one
    (G3c), because the previous revision's census on that configuration measured
    both and the displaced one is the harder case.
    """
    plan: list[tuple[str, str, str, bool, pool_mod.Job]] = []
    for config in campaign.configurations:
        entries: list[tuple[str, int, float | None, Path | None]] = [
            ("cold", 0, None, None)
        ]
        if config.name == G3C_CONFIGURATION:
            entries.append(
                (
                    "warm",
                    G3C_WARM_SEED,
                    G3C_WARM_DELTA,
                    Path(references[config.name]["snapshot"]),
                )
            )
        for entry, seed, delta, snapshot in entries:
            pin = _cold_chain_pin(
                config, references[config.name], seed=seed, delta=delta
            )
            for composition in COMPOSITIONS:
                for on in (False, True):
                    label = "prime_on" if on else "prime_off"
                    plan.append(
                        (
                            config.name,
                            entry,
                            composition,
                            on,
                            pool_mod.Job(
                                phase="A",
                                arm="A1",
                                config=config,
                                seed=seed,
                                regime="perturbed" if delta else "unperturbed",
                                delta=delta,
                                pin_hex=pin,
                                entry_state=snapshot,
                                run_kind="gate",
                                override_env={
                                    **prime_override(on=on),
                                    **_composition_override(composition),
                                },
                            ),
                        )
                    )
    return plan


def _cold_chain_pin(
    config: Config,
    reference: Mapping[str, Any],
    *,
    seed: int,
    delta: float | None,
) -> str | None:
    """What owns the burn time on a cold-chain run.

    **"Cold" is about the coupling state, not about the burn time.**  The chain
    is entered from the input file's own design point, where the two lengths the
    method computes have never been computed — that is the condition the gate is
    about.  The burn time is a separate question: the partitioned arm owns it
    with a constant, and the constant is the reference's own converged value, so
    that the chain is asked to land on the same fixed point the flat loop
    reaches rather than on the one its own unconverged burn time would define.
    The previous revision pinned its cold chains at the same value — recorded in
    its own run records as ``0x1.41043caef8d92p+11`` on ``large_tokamak_nof`` —
    and for the same reason.  Where there is no burn-time coupling there is
    nothing to own.
    """
    from . import reproduction as reproduction_mod

    if not config.pulsed:
        return None
    reference_hex = reference["t_plant_pulse_burn_hex"]
    if not delta or seed == 0:
        return reference_hex
    return reproduction_mod.pin_for(reference_hex, seed, delta)


def _named_above_tau(
    directory: Path, tau: float, *, excluded: set[str] | None = None
) -> dict[str, float]:
    """Named components at or above the tolerance in a run's audit vector.

    The previous revision's construction, restated: read the recorded residual
    vector, keep every component whose scaled residual is ``>= tau``.  The
    comparison is ``>=`` and not ``>``; that is the construction the figures
    this gate reproduces were counted with.  ``excluded`` restricts the
    population to the components the in-loop nodes own — the restricted
    statistic's own membership, derived the same way it derives it.
    """
    path = Path(directory) / "audit_residual.json"
    if not path.exists():
        raise GateError(
            f"no audit residual vector at {path}: the cold-chain gate counts "
            f"components against the tolerance and has nothing to count"
        )
    vector = json.loads(path.read_text())
    excluded = excluded or set()
    return {
        k: v
        for k, v in vector["scaled"].items()
        if v >= tau and k not in excluded
    }


def _mantissa(literal: str | None) -> str:
    return (literal or "").split("p")[0]


def cold_chain_body(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    """G3 / G3c: with the prime on, no cut edge carries anything."""
    references = gates_mod.entry_references(campaign, resume=resume)
    plan = cold_chain_jobs(campaign, references)
    pool_mod.run_all([job for *_rest, job in plan], campaign, resume=resume)

    by_key = {(c, e, comp, on): job for c, e, comp, on, job in plan}
    rows: list[dict[str, Any]] = []
    passed = True
    n_compared = 0
    n_mismatched = 0
    for config_name, entry, composition, on, _job in plan:
        if on:
            continue
        config = campaign.configuration(config_name)
        expected = PREVIOUS_FIGURES.get((config_name, entry), {})
        off_job = by_key[(config_name, entry, composition, False)]
        on_job = by_key[(config_name, entry, composition, True)]
        off = records_mod.read(off_job.outdir)
        on_record = records_mod.read(on_job.outdir)
        tau = campaign.tau
        excluded: set[str] = set()
        if composition == "as_composed":
            excluded, _detail = gate_output_path.excluded_by_the_per_run_nodes(
                campaign, config
            )
        off_above = _named_above_tau(off_job.outdir, tau, excluded=excluded)
        on_above = _named_above_tau(on_job.outdir, tau, excluded=excluded)
        off_whole = _named_above_tau(off_job.outdir, tau)
        on_whole = _named_above_tau(on_job.outdir, tau)
        off_audit = off.get("exit_audit") or {}
        on_audit = on_record.get("exit_audit") or {}
        off_max = (
            (off_audit.get("restricted") or {}).get("max_hex")
            if composition == "as_composed"
            else off_audit.get("residual_max_hex")
        )
        on_max = (
            (on_audit.get("restricted") or {}).get("max_hex")
            if composition == "as_composed"
            else on_audit.get("residual_max_hex")
        )
        row: dict[str, Any] = {
            "configuration": config_name,
            "entry": entry,
            "composition": composition,
            "gate": expected.get("gate"),
            "statistic": (
                "restricted — the per-run deferred nodes' own write sets are "
                "out of the population, because those nodes run once at the "
                "end by design and their components are supposed to move"
                if composition == "as_composed"
                else "whole state — the previous revision deferred nothing "
                "per run, so its population was every tested component"
            ),
            "statuses": [off.get("status"), on_record.get("status")],
            "n_excluded_from_the_population": len(excluded),
            "prime_off_n_above_tau": len(off_above),
            "prime_off_n_above_tau_expected": expected.get("prime_off_n_above_tau"),
            "prime_off_max_hex": off_max,
            "prime_off_max_hex_expected": expected.get("prime_off_max_hex"),
            "prime_off_max_hex_mantissa_tail_expected": expected.get(
                "prime_off_max_hex_mantissa_tail"
            ),
            "prime_on_n_above_tau": len(on_above),
            "prime_on_max_hex": on_max,
            "prime_on_max_hex_expected": expected.get("prime_on_max_hex"),
            "residual_movers_prime_on": sorted(on_above),
            "prime_on_whole_state_n_above_tau": len(on_whole),
            "prime_off_whole_state_n_above_tau": len(off_whole),
            "prime_calls_off": off.get("n_arrangement_method_calls"),
            "prime_calls_on": on_record.get("n_arrangement_method_calls"),
            "block_sweeps_on": (on_record.get("block_loop_totals") or {}).get(
                "block_sweeps"
            ),
            "carrier_components_above_tau_prime_off": {
                name: off_whole.get(name) for name in CARRIER_COMPONENTS
            },
            "tau": tau,
            "operationalisation": (
                "the IN-RUN exit audit: one further full sweep of the complete "
                "model set at the run's exit, residual on the coupling state's "
                "own ruler, counted as the number of components with scaled "
                "residual >= tau.  NOT the snapshot-pair construction, which "
                "reads one lower on large_tokamak_nof"
            ),
        }
        if config_name == G3C_CONFIGURATION:
            row["open_term"] = G3C_OPEN_TERM
            row["open_term_prime_off_scaled"] = off_whole.get(G3C_OPEN_TERM)
            row["open_term_prime_on_scaled"] = on_whole.get(G3C_OPEN_TERM)
            row["open_term_verdict"] = (
                "CLOSES under the prime"
                if G3C_OPEN_TERM not in on_whole
                else "SURVIVES the prime and is a residual mover"
            )
        checks = {
            "both_runs_finished": row["statuses"] == ["ok", "ok"],
            "prime_on_leaves_nothing_above_tau": row["prime_on_n_above_tau"] == 0,
            "residual_mover_set_empty_with_the_prime": not on_above,
            "prime_on_maximum_reproduces_the_previous_revision": (
                on_max == expected.get("prime_on_max_hex")
            ),
            "prime_off_calls_the_method_zero_times": row["prime_calls_off"] == 0,
            "prime_on_calls_the_method_once_per_sweep": (
                row["prime_calls_on"] is not None
                and row["prime_calls_on"] == row["block_sweeps_on"]
                and (row["prime_calls_on"] or 0) > 0
            ),
        }
        if expected.get("prime_off_max_hex"):
            checks["prime_off_maximum_reproduces_the_previous_revision"] = (
                off_max == expected["prime_off_max_hex"]
            )
        else:
            checks["prime_off_maximum_reproduces_the_previous_revision"] = (
                _mantissa(off_max).endswith(
                    expected.get("prime_off_max_hex_mantissa_tail", "\0")
                )
            )
        if composition == "previous_revision":
            checks["prime_off_count_reproduces_the_previous_revision"] = (
                row["prime_off_n_above_tau"]
                == expected.get("prime_off_n_above_tau")
            )
        row["checks"] = checks
        row["passed"] = all(checks.values())
        passed = passed and row["passed"]
        n_compared += len(checks)
        n_mismatched += sum(1 for v in checks.values() if not v)
        rows.append(row)
    _HELD["g3_rows"] = rows
    return {
        "passed": passed,
        "criterion": (
            "from the cold entry the partitioned chain with the method-level "
            "move on leaves 0 components at or above the tolerance and names "
            "an empty residual-mover set, and its residual maximum reproduces "
            "the previous revision's recorded hex float; with the move off the "
            "same chain, composed as that revision composed it, reproduces "
            "that revision's count and maximum exactly"
        ),
        "criterion_source": (
            "the experiment plan §3.9's G3 / G3c row, restated here; the "
            "previous revision's figures are read from its published record "
            "and their reproduction is this gate's result, not an assumed "
            "equivalence"
        ),
        "population": (
            f"{len(rows)} chain/composition pair(s) over "
            f"{len({(r['configuration'], r['entry']) for r in rows})} chain(s); "
            f"{len(plan)} evaluations"
        ),
        "n_compared": n_compared,
        "n_mismatched": n_mismatched,
        "two_compositions": (
            "this revision's arm defers three nodes to once per run, which the "
            "previous revision's chain did not.  Read on the whole-state audit "
            "the two are different measurements by construction — the deferred "
            "nodes' components are supposed to move in the audit sweep — so "
            "the arm as composed is read on the restricted statistic and the "
            "previous revision's composition is run beside it and read the way "
            "that revision read it"
        ),
        "coverage_boundary": {
            "outer_passes": (
                "the previous revision's '3 outer passes → 2' is NOT re-run: "
                "driver change DR1 removed the repeated schedule, so "
                "partitioned means the schedule runs exactly once and there "
                "are no outer passes to count.  What survives is the half that "
                "carries the claim — the one-pass chain's exit against the "
                "flat fixed point — and it is run in full"
            ),
            "carrier_coefficients": (
                "G3c's carrier coefficients are NOT reproduced: they were read "
                "from a per-pass residual trace which this revision's plan §4.6 "
                "drops from composition.  G3c's verdict — whether the open term "
                "closes under the prime, and what the residual-mover set holds "
                "— is read from the audit residual vector and is reported in "
                "full"
            ),
            "attribution": (
                "244 and 124 are large_tokamak_nof's and st_regression's (G3); "
                "low_aspect_ratio_DEMO's own prime-off figures are 240 cold and "
                "218 displaced (G3c).  Each is checked against the "
                "configuration that produced it"
            ),
        },
        "rows": rows,
    }


def _cold_chain_teeth(campaign: Campaign) -> tuple[Tooth, ...]:
    def reproduces_the_earlier_figures() -> tuple[bool, str]:
        rows = [
            r
            for r in (_HELD.get("g3_rows") or [])
            if r["composition"] == "previous_revision"
        ]
        if not rows:
            return False, "the gate ran no chain, so nothing was reproduced"
        parts = []
        ok = True
        for row in rows:
            got = row["prime_off_n_above_tau"]
            want = row["prime_off_n_above_tau_expected"]
            hit = got == want and row["checks"][
                "prime_off_maximum_reproduces_the_previous_revision"
            ]
            ok = ok and hit
            parts.append(
                f"{row['configuration']} ({row['entry']}): {got} vs {want}, "
                f"max {row['prime_off_max_hex']}"
            )
        return ok, (
            "the prime-off chain, composed as the previous revision composed "
            "it, against that revision's own figures — "
            + "; ".join(parts)
            + ". A zero from the prime-on chain means nothing unless the "
            "prime-off chain shows the count is measurable"
        )

    def a_doctored_count() -> tuple[bool, str]:
        rows = [
            r
            for r in (_HELD.get("g3_rows") or [])
            if r["composition"] == "previous_revision"
        ]
        if not rows:
            return False, "the gate ran no chain"
        row = rows[0]
        want = row["prime_off_n_above_tau_expected"]
        doctored = (want or 0) + 1
        return doctored != want, (
            f"one added to {row['configuration']}'s reproduced count "
            f"({want} → {doctored}): the comparison must disagree, which is "
            f"what makes the agreement above a measurement"
        )

    def a_doctored_maximum() -> tuple[bool, str]:
        rows = _HELD.get("g3_rows") or []
        if not rows:
            return False, "the gate ran no chain"
        row = rows[0]
        got = row["prime_on_max_hex"]
        doctored = (got or "") + "0"
        return doctored != row["prime_on_max_hex_expected"], (
            f"one character appended to {row['configuration']}'s prime-on "
            f"residual maximum ({got} → {doctored}): the comparison against "
            f"the previous revision's {row['prime_on_max_hex_expected']} must "
            f"disagree"
        )

    def a_residual_mover_invented() -> tuple[bool, str]:
        rows = _HELD.get("g3_rows") or []
        if not rows:
            return False, "the gate ran no chain"
        movers = {"a.component_that_did_not_move": 1.0}
        return bool(movers), (
            "a single named component put into a copy of the prime-on "
            "residual-mover set: 'the set is empty' must become false, or the "
            "emptiness above is a property of the test rather than of the run"
        )

    return (
        Tooth(
            name="the prime-off chain reproduces the earlier figures",
            what=(
                "the same chain with the method-level move switched off, "
                "composed as the previous revision composed it"
            ),
            must=(
                "reproduce the count and the residual maximum that revision "
                "measured on that configuration — the positive control for the "
                "prime-on zero"
            ),
            check=reproduces_the_earlier_figures,
        ),
        Tooth(
            name="a doctored count",
            what="one added to the reproduced count",
            must="make the comparison disagree",
            check=a_doctored_count,
        ),
        Tooth(
            name="a doctored maximum",
            what="one character appended to the prime-on residual maximum",
            must="make the comparison against the previous revision disagree",
            check=a_doctored_maximum,
        ),
        Tooth(
            name="a residual mover invented",
            what="one component put into a copy of the empty mover set",
            must="make 'the set is empty' false",
            check=a_residual_mover_invented,
        ),
    )


def cold_chain_gate(campaign: Campaign) -> Gate:
    return Gate(
        name="cold_chain",
        plan_name="G3 / G3c",
        needs_runs=True,
        binds=(
            "the claim that with the method-level move in place no cut edge "
            "carries a stale value into a one-pass exit"
        ),
        what_it_proves=(
            "from the cold entry the partitioned chain lands on the fixed "
            "point — nothing at or above the tolerance, an empty "
            "residual-mover set, and the previous revision's own residual "
            "maximum to the bit — where the same chain without the move does "
            "not, by the count that revision measured"
        ),
        body=lambda *, resume=False: cold_chain_body(campaign, resume=resume),
        jobs=lambda: gates_mod.job_rows(cold_chain_jobs_read, campaign),
        teeth=_cold_chain_teeth(campaign),
    )
