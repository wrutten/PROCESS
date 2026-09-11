#!/usr/bin/env python
"""Gate G6 — the evaluation phase's entries, and where a warm arm lands.

Two halves, and they bind the two things the evaluation phase's comparisons
rest on.

**The entries are paired.**  Every evaluation-phase arm is entered from the same
fixed point, displaced by the same seed.  The cost figures the experiment
publishes are *paired differences* — this arm against that arm at the same seed
— so if two arms were entered from even slightly different states, the
difference would be partly the entry and nobody could say how much.  The gate
therefore compares the entry states the runs actually wrote, **byte for byte**,
across the arms of each configuration: the displaced coupling state a seed
produces has to be the same bytes for the flat control, the flat arm that pins
the burn time, and the partitioned arm.

That is not automatic.  The pinned arms do not take their burn time from the
displacement stream directly; they are handed a **constant**, computed as the
reference's converged burn time times that seed's own factor for that component.
Those are two routes to one number, and a gate is the only thing that says they
arrive at the same bits.

**A warm arm lands back on the fixed point.**  Entered from the reference's exit
state and pinned at the reference's own converged burn time, a block arm must
reproduce the reference fixed point: the cross-state maximum scaled residual
below the tolerance, nothing out of its category, and the pinned component
bit-identical.  This is the check that says the block solves and the deferrals
compute the same fixed point as the flat loop rather than a nearby one — and it
is the only check that says so at all, because at a fixed point the *cost*
figures are trivially small and prove nothing.

Criterion inherited, and its source
-----------------------------------
Experiment plan §3.9's G6 row: *"seed-paired entries bit-identical across arms
per configuration; each block arm from the reference snapshot, pinned at the
reference's converged burn time, reproduces the reference fixed point below τ
with the pinned component bit-identical"*, teeth *"as V3"*.  The previous
revision's warm gate states the criterion as *"categorically clean AND
cross-state max residual vs the reference < τ"*, pre-declared, with
``pin_intact_at_exit`` required on the pulsed configurations; its two teeth are
a continuous component bumped by ``3 τ × scale`` and a discrete component
flipped, each of which must make the criterion stop holding.  Both are restated
here; nothing is imported from the previous revision's directories.

One arm is already covered elsewhere and is **not** duplicated silently: the
flat arm that pins the burn time is the reproduction gate's own §7.5 substitute,
because that arm has no record in the previous revision to reproduce.  This gate
runs it too, under its own root, so that the two block arms are compared on one
page — and says so here rather than leaving a reader to discover that the same
construction runs twice.

Written by task **A52 (harness-gates)**.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from . import arms as arms_mod
from . import gates as gates_mod
from . import pool as pool_mod
from . import predicate as predicate_mod
from . import records as records_mod
from .config import Campaign, Config
from .framework import Gate, GateError, Tooth

#: The evaluation-phase arms whose entries must pair, in the plan's order.  The
#: reference arm is deliberately absent: it is entered from the input file's own
#: point and never from a snapshot, which is what "PROCESS as shipped" means.
PAIRED_ARMS: tuple[str, ...] = ("A0", "A0p", "A1")

#: The arms whose warm landing is checked.  Both block arms of the plan's §7.5
#: table: the partitioned arm, and the flat arm that pins the burn time.
WARM_ARMS: tuple[str, ...] = ("A0p", "A1")

#: Which seed the entry pairing is checked at.  The first *displaced* one — an
#: undisplaced entry is the snapshot itself and would pair trivially.
PAIRING_SEED = 1

_HELD: dict[str, Any] = {}


def entry_root(campaign: Campaign) -> Path:
    return Path(campaign.runs_dir) / gates_mod.GATES_SUBPATH / "entry_and_warm"


def _pin(
    config: Config, arm: str, reference: Mapping[str, Any], *, seed: int, delta: float | None
) -> str | None:
    """The constant this arm owns at this seed, or None.

    At the undisplaced point it is the reference's own converged burn time; at a
    displaced one it rides the **same** stream the coupling state rides, so the
    constant and the state the run is entered with are displaced together.
    """
    from . import reproduction as reproduction_mod

    if not config.pulsed:
        return None
    if arms_mod.ARMS[arm].burn_time_owner != "constant":
        return None
    reference_hex = reference["t_plant_pulse_burn_hex"]
    if not delta or seed == 0:
        return reference_hex
    return reproduction_mod.pin_for(reference_hex, seed, delta)


def _entry_state(directory: Path, *, key: str) -> dict[str, Any]:
    path = Path(directory) / "y_entry.json"
    if not path.exists():
        raise GateError(
            f"G6 has no entry state for {key}: {path} is not there.  A gate "
            f"that cannot find one of the states it pairs must refuse, never "
            f"pass over an empty comparison (trap T11)."
        )
    return json.loads(path.read_text())


def compare_entries(
    a: Mapping[str, Any], b: Mapping[str, Any]
) -> dict[str, Any]:
    """Two entry states, component by component, exactly."""
    if a["components_sha256"] != b["components_sha256"]:
        raise GateError(
            "two entry states taken against different component specs "
            f"({a['components_sha256']} vs {b['components_sha256']}); pairing "
            "them would pair components nobody matched"
        )
    left, right = a["state"], b["state"]
    names = sorted(set(left) | set(right))
    differing = [n for n in names if left.get(n) != right.get(n)]
    return {
        "n_components": len(names),
        "n_differing": len(differing),
        "differing": differing[:20],
    }


# --------------------------------------------------------------------------
# the runs
# --------------------------------------------------------------------------


def entry_and_warm_jobs(
    campaign: Campaign, references: Mapping[str, Any]
) -> tuple[list[tuple[str, str, pool_mod.Job]], list[tuple[str, str, pool_mod.Job]]]:
    """The pairing runs and the warm runs, per configuration."""
    pairing: list[tuple[str, str, pool_mod.Job]] = []
    warm: list[tuple[str, str, pool_mod.Job]] = []
    root = entry_root(campaign)
    for config in campaign.configurations:
        reference = references[config.name]
        snapshot = Path(reference["snapshot"])
        for arm in PAIRED_ARMS:
            if arm in config.skips:
                continue
            pairing.append(
                (
                    config.name,
                    arm,
                    pool_mod.Job(
                        phase="A",
                        arm=arm,
                        config=config,
                        seed=PAIRING_SEED,
                        outdir=root / config.name / "pairing" / arm,
                        regime="perturbed",
                        delta=campaign.delta,
                        pin_hex=_pin(
                            config,
                            arm,
                            reference,
                            seed=PAIRING_SEED,
                            delta=campaign.delta,
                        ),
                        entry_state=snapshot,
                        run_kind="gate",
                    ),
                )
            )
        for arm in WARM_ARMS:
            if arm in config.skips:
                continue
            warm.append(
                (
                    config.name,
                    arm,
                    pool_mod.Job(
                        phase="A",
                        arm=arm,
                        config=config,
                        seed=0,
                        outdir=root / config.name / "warm" / arm,
                        regime="unperturbed",
                        delta=None,
                        pin_hex=_pin(config, arm, reference, seed=0, delta=None),
                        entry_state=snapshot,
                        run_kind="gate",
                    ),
                )
            )
    return pairing, warm


def _warm_row(
    config: Config,
    arm: str,
    directory: Path,
    reference: Mapping[str, Any],
    campaign: Campaign,
) -> dict[str, Any]:
    from . import reproduction as reproduction_mod

    record = records_mod.read(directory)
    row: dict[str, Any] = {
        "configuration": config.name,
        "arm": arm,
        "status": record.get("status"),
        "pin_hex": record.get("campaign_pin_hex"),
        "pin_intact_at_exit": record.get("pin_intact_at_exit"),
        "node_calls_single_eval": record.get("node_calls_single_eval"),
        "n_model_calls_sweeps": record.get("n_model_calls_sweeps"),
        "own_audit_residual_max_hex": (record.get("exit_audit") or {}).get(
            "residual_max_hex"
        ),
    }
    if record.get("status") != "ok":
        row["passed"] = False
        row["failed_at"] = f"the run did not finish: status {row['status']!r}"
        return row
    spec = predicate_mod.load_spec(config.coupling_state_path)
    y_reference = predicate_mod.restore_snapshot(
        spec, json.loads(Path(reference["snapshot"]).read_text())
    )
    y_arm = predicate_mod.restore_snapshot(
        spec, json.loads((Path(directory) / "y_exit.json").read_text())
    )
    cross = predicate_mod.cross_residual(spec, y_reference, y_arm, campaign.tau)
    index = predicate_mod.component_index(spec, reproduction_mod.PINNED_COMPONENT)
    pin_identical = (
        None if index is None else float(y_reference[index]) == float(y_arm[index])
    )
    row["cross_state_residual"] = cross
    row["pinned_component"] = reproduction_mod.PINNED_COMPONENT
    row["pinned_component_bit_identical"] = pin_identical
    row["checks"] = {
        "cross_state_maximum_below_tau": cross["max"] < campaign.tau,
        "categorically_clean": bool(cross["categorically_clean"]),
        "pinned_component_bit_identical": pin_identical is not False,
        "pin_intact_at_exit": record.get("pin_intact_at_exit") is not False,
    }
    row["passed"] = all(row["checks"].values())
    return row


def entry_and_warm_body(campaign: Campaign) -> dict[str, Any]:
    """G6: the entries pair, and the block arms land on the fixed point."""
    references = gates_mod.entry_references(campaign, resume=True)
    pairing, warm = entry_and_warm_jobs(campaign, references)
    pool_mod.run_all(
        [job for *_r, job in pairing] + [job for *_r, job in warm],
        campaign,
        resume=True,
    )

    passed = True
    n_compared = 0
    n_mismatched = 0
    pairing_rows: list[dict[str, Any]] = []
    by_config: dict[str, list[tuple[str, pool_mod.Job]]] = {}
    for name, arm, job in pairing:
        by_config.setdefault(name, []).append((arm, job))
    for config in campaign.configurations:
        arms_here = by_config.get(config.name, [])
        if len(arms_here) < 2:
            pairing_rows.append(
                {
                    "configuration": config.name,
                    "arms": [a for a, _ in arms_here],
                    "note": (
                        "fewer than two arms are active here, so there is no "
                        "pair to compare; the skipped arms are recorded with "
                        "their reasons in the configuration"
                    ),
                    "skips": dict(config.skips),
                    "passed": True,
                }
            )
            continue
        anchor_arm, anchor_job = arms_here[0]
        anchor = _entry_state(anchor_job.outdir, key=f"{config.name}/{anchor_arm}")
        for arm, job in arms_here[1:]:
            other = _entry_state(job.outdir, key=f"{config.name}/{arm}")
            comparison = compare_entries(anchor, other)
            row = {
                "configuration": config.name,
                "seed": PAIRING_SEED,
                "pair": [anchor_arm, arm],
                "n_components": comparison["n_components"],
                "n_components_declared": config.n_coupling_components,
                "n_differing": comparison["n_differing"],
                "differing": comparison["differing"],
                "pins": [
                    records_mod.read(anchor_job.outdir).get("campaign_pin_hex"),
                    records_mod.read(job.outdir).get("campaign_pin_hex"),
                ],
            }
            row["checks"] = {
                "every_declared_component_compared": (
                    comparison["n_components"] == config.n_coupling_components
                ),
                "entries_bit_identical": comparison["n_differing"] == 0,
            }
            row["passed"] = all(row["checks"].values())
            n_compared += comparison["n_components"]
            n_mismatched += comparison["n_differing"]
            passed = passed and row["passed"]
            pairing_rows.append(row)

    warm_rows: list[dict[str, Any]] = []
    for name, arm, job in warm:
        config = campaign.configuration(name)
        row = _warm_row(config, arm, job.outdir, references[name], campaign)
        warm_rows.append(row)
        n_compared += 1
        if not row["passed"]:
            n_mismatched += 1
        passed = passed and row["passed"]
    for config in campaign.configurations:
        for arm in WARM_ARMS:
            if arm in config.skips:
                warm_rows.append(
                    {
                        "configuration": config.name,
                        "arm": arm,
                        "skipped": config.skips[arm],
                        "passed": True,
                    }
                )

    _HELD["pairing"] = pairing_rows
    _HELD["warm"] = warm_rows
    _HELD["references"] = references
    _HELD["campaign"] = campaign
    return {
        "passed": passed,
        "criterion": (
            "the displaced entry a seed produces is the same bytes for every "
            "active evaluation-phase arm of a configuration; and each block "
            "arm, entered from the reference's exit state and pinned at the "
            "reference's own converged burn time, reproduces the reference "
            "fixed point — cross-state maximum below the tolerance, "
            "categorically clean, pinned component bit-identical"
        ),
        "criterion_source": (
            "the experiment plan §3.9's G6 row and the previous revision's "
            "pre-declared warm criterion, restated here"
        ),
        "population": (
            f"{len([r for r in pairing_rows if 'pair' in r])} entry pair(s) at "
            f"seed {PAIRING_SEED}; "
            f"{len([r for r in warm_rows if 'skipped' not in r])} warm run(s); "
            f"{len(pairing) + len(warm)} evaluations"
        ),
        "n_compared": n_compared,
        "n_mismatched": n_mismatched,
        "also_covered_elsewhere": (
            "the flat pinned arm's warm landing is the reproduction gate's "
            "§7.5 substitute as well; it is run here too so that both block "
            "arms are compared on one page, and this sentence is why the same "
            "construction appears twice"
        ),
        "entry_pairing": pairing_rows,
        "warm_landing": warm_rows,
    }


# --------------------------------------------------------------------------
# the teeth
# --------------------------------------------------------------------------


def _teeth(campaign: Campaign) -> tuple[Tooth, ...]:
    def _first_warm() -> dict[str, Any] | None:
        rows = [
            r
            for r in (_HELD.get("warm") or [])
            if "checks" in r and r.get("cross_state_residual")
        ]
        return rows[0] if rows else None

    def continuous_bumped() -> tuple[bool, str]:
        row = _first_warm()
        if row is None:
            return False, "the gate made no warm run, so nothing can be bumped"
        config = campaign.configuration(row["configuration"])
        reference = (_HELD.get("references") or {})[config.name]
        spec = predicate_mod.load_spec(config.coupling_state_path)
        y_reference = predicate_mod.restore_snapshot(
            spec, json.loads(Path(reference["snapshot"]).read_text())
        )
        directory = entry_root(campaign) / config.name / "warm" / row["arm"]
        y_arm = predicate_mod.restore_snapshot(
            spec, json.loads((directory / "y_exit.json").read_text())
        )
        bumped = list(y_arm)
        index = next(
            (i for i in spec.idx_continuous if isinstance(bumped[i], float)), None
        )
        if index is None:
            return False, "no continuous float component to bump"
        scale = float(spec.scale[index])
        bumped[index] = bumped[index] + 3.0 * campaign.tau * scale
        cross = predicate_mod.cross_residual(
            spec, y_reference, bumped, campaign.tau
        )
        still_holds = cross["max"] < campaign.tau and cross["categorically_clean"]
        return not still_holds, (
            f"{spec.name(index)} bumped by 3 x tau x its scale in a copy of "
            f"{config.name}'s warm exit state: the cross-state maximum reads "
            f"{cross['max']:.3e} against tau {campaign.tau:.0e}, so the "
            f"criterion must stop holding"
        )

    def discrete_flipped() -> tuple[bool, str]:
        row = _first_warm()
        if row is None:
            return False, "the gate made no warm run"
        config = campaign.configuration(row["configuration"])
        reference = (_HELD.get("references") or {})[config.name]
        spec = predicate_mod.load_spec(config.coupling_state_path)
        y_reference = predicate_mod.restore_snapshot(
            spec, json.loads(Path(reference["snapshot"]).read_text())
        )
        directory = entry_root(campaign) / config.name / "warm" / row["arm"]
        y_arm = predicate_mod.restore_snapshot(
            spec, json.loads((directory / "y_exit.json").read_text())
        )
        flipped = list(y_arm)
        index = spec.idx_discrete[0] if spec.idx_discrete else None
        if index is None:
            return False, (
                "this configuration's coupling state declares no discrete "
                "component, so the discrete tooth cannot bite: that is a "
                "finding about the state, reported rather than passed over"
            )
        value = flipped[index]
        if isinstance(value, bool):
            flipped[index] = not value
        elif isinstance(value, int):
            flipped[index] = value + 1
        elif isinstance(value, str):
            flipped[index] = value + "_x"
        else:
            flipped[index] = None
        cross = predicate_mod.cross_residual(
            spec, y_reference, flipped, campaign.tau
        )
        still_holds = cross["max"] < campaign.tau and cross["categorically_clean"]
        return not still_holds, (
            f"the discrete component {spec.name(index)} flipped in a copy of "
            f"{config.name}'s warm exit state: the comparison reports "
            f"categorically clean = {cross['categorically_clean']}, so the "
            f"criterion must stop holding however small the maximum is"
        )

    def a_doctored_entry() -> tuple[bool, str]:
        rows = [r for r in (_HELD.get("pairing") or []) if "pair" in r]
        if not rows:
            return False, "the gate paired no entries"
        row = rows[0]
        config = campaign.configuration(row["configuration"])
        directory = (
            entry_root(campaign) / config.name / "pairing" / row["pair"][0]
        )
        state = json.loads((directory / "y_entry.json").read_text())
        doctored = json.loads(json.dumps(state))
        name = next(
            (
                k
                for k in sorted(doctored["state"])
                if isinstance(doctored["state"][k], dict)
                and doctored["state"][k].get("k") == "f"
            ),
            None,
        )
        if name is None:
            return False, "no float component in the entry state to doctor"
        before = float.fromhex(doctored["state"][name]["hex"])
        doctored["state"][name] = {"k": "f", "hex": (before * 1.5).hex()}
        comparison = compare_entries(state, doctored)
        return comparison["n_differing"] == 1, (
            f"{name} multiplied by 1.5 in a copy of {config.name}'s "
            f"{row['pair'][0]} entry state: the pairing reports "
            f"{comparison['n_differing']} differing component(s) of "
            f"{comparison['n_components']}"
        )

    return (
        Tooth(
            name="a continuous component bumped by three tolerances",
            what="one continuous float moved by 3 x tau x its measured scale",
            must="make the warm criterion stop holding",
            check=continuous_bumped,
        ),
        Tooth(
            name="a discrete component flipped",
            what="one discrete component changed in a copy of the exit state",
            must=(
                "make the comparison categorically unclean, however small the "
                "maximum is"
            ),
            check=discrete_flipped,
        ),
        Tooth(
            name="a doctored entry state",
            what="one float of one arm's entry state multiplied by 1.5",
            must="be the one and only differing component in the pairing",
            check=a_doctored_entry,
        ),
    )


def entry_and_warm_gate(campaign: Campaign) -> Gate:
    return Gate(
        name="entry_and_warm",
        plan_name="G6",
        needs_runs=True,
        binds="the evaluation phase, on every configuration",
        what_it_proves=(
            "every arm of a configuration is entered from the same displaced "
            "state, to the byte — so a paired cost difference is the arm and "
            "not the entry — and each block arm lands back on the reference "
            "fixed point when entered warm and pinned"
        ),
        body=lambda: entry_and_warm_body(campaign),
        teeth=_teeth(campaign),
    )
