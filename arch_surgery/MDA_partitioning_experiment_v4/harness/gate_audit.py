#!/usr/bin/env python
"""Gate G4 — the audit's restriction, in both directions and every namespace.

What the gate is about
----------------------
Every run's achieved accuracy is read from an **exit audit**: one further full
sweep of the complete model set past termination, on the identical instrument in
every arm, whose own model calls are never charged to the arm.  The audit is
published two ways.  The **whole-state** statistic is the maximum scaled
movement over every tested component.  The **restricted** statistic is the same
maximum with the components the *per-run deferred* nodes write taken out.

The restriction exists because those nodes run **once per run, at the accepted
optimum, by design**.  A component they own is *supposed* to move in the audit
sweep — that movement is the deferral working, not a convergence failure — so a
similarity statistic that counted it would penalise the arm for doing what the
arm is defined to do.

The restriction is therefore a claim with two halves, and a gate that showed
only one would be worthless:

* **blind where it must be blind** — doctor a component a per-run node owns, and
  the whole-state audit must move by exactly the displacement while the
  restricted audit is *bit-identical* to the undoctored run;
* **sighted where it must be sighted** — doctor a component the in-loop nodes
  own, and the restricted audit must move (or the run must do more work getting
  back to the fixed point).

**And in every excluded namespace, not just one.**  The previous revision's
gate doctored a single ``costs.*`` component, which demonstrates the *mechanism*
in both directions but does not certify any other namespace's *membership* — a
weakness its own improvement list recorded (item 6a(c)).  This gate doctors
**one component from each excluded namespace**, and the namespaces are
**derived**, never listed: they come from the per-run classifier's own crawl
(``postsolve.derive(...)["crawl"]["candidate_units"]``), which on this
experiment's configurations returns ``vacuum``, ``water_use`` and ``costs`` on
the two pulsed configurations and those three plus ``pulse`` on the steady-state
one.  Writing them out here would be a list that stops describing the
derivation the moment the derivation changes.

Membership is derived the same way the audit derives it: the per-run artifact
names **nodes**; the committed run-time write census maps each node to the
fields it writes on this configuration; the intersection with the coupling
state's tested keys is the excluded set.  A prefix rule is deliberately not
used — one configuration's node list contains a node that writes nothing there,
and a prefix would either miss it or over-match.

The second half of this gate: the optimisation record's own statistic
----------------------------------------------------------------------
Until this task the restricted statistic was computed for the **evaluation**
phase only: ``optimise.py`` was never handed the two artifacts, so
``exit_audit.restricted`` was null on every optimisation record and the number
had to be recomputed from the committed residual vector afterwards.  Task
**A52 (harness-gates)** passes both artifacts through ``pool._command`` to
``optimise.py``, so the statistic is now **in the record**, derived by the same
code in both phases.

One consequence is deliberate and is reported rather than smoothed: on both
pulsed configurations the restricted maximum at the accepted point is dominated
by a single component, ``tfcoil.insstrain``, at roughly 7e-3 scaled — far above
the tolerance, identical between the flat and the partitioned arm on the same
seed, and therefore a property of the handed-over state rather than of the
partition (improvement list item 11).  This gate **names it** wherever it is the
argmax.  A statistic that reported only "the restricted maximum" without saying
which component carries it would average away the one thing worth deciding
about.

Criterion inherited, and its source
-----------------------------------
The construction is the previous revision's, restated here rather than imported.
Experiment plan §3.9's G4 row: *"a doctored ``per_run``-owned component trips the
whole-state audit and **not** the restricted one; a doctored in-loop component
trips both; **one doctored component from each excluded namespace**"*, with
teeth *"both directions, every namespace"*.  The previous revision's own
implementation adds the detail this restates: the doctored component is a
continuous float, non-zero, and **not owned by the design vector** — a component
the sweep head re-injects from ``x`` would be silently reset and the doctoring
would test nothing — displaced by a factor of 1.5, and the in-loop side is
binding on *"the restricted statistic moved **or** the run did more work"*,
because at a bit-exact fixed point a re-converged component can land back on
identical bits.

Written by task **A52 (harness-gates)**.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from . import arms as arms_mod
from . import gates as gates_mod
from . import pool as pool_mod
from . import postsolve as postsolve_mod
from . import records as records_mod
from .config import Campaign, Config
from .framework import Gate, GateError, Tooth

#: The arm the gate runs.  The partitioned arm is the one whose restricted
#: statistic the experiment reports, so it is the one the gate binds.
G4_ARM = "A1"

#: How far a doctored component is displaced.  The previous revision's value,
#: unchanged: large enough to be far above any tolerance, small enough that the
#: model set still runs.
TEETH_FACTOR = 1.5

#: How close the whole-state audit's reading of the doctored component must be
#: to the displacement that was injected.  Not a convergence tolerance: the two
#: are the same arithmetic on the same two floats, and the allowance is for the
#: last bits of a division.
DISPLACEMENT_RELATIVE_ALLOWANCE = 1e-9

_HELD: dict[str, Any] = {}


# --------------------------------------------------------------------------
# the excluded namespaces, derived
# --------------------------------------------------------------------------


def excluded_namespaces(campaign: Campaign, config: Config) -> dict[str, Any]:
    """The namespaces the restriction excludes on this configuration.

    Derived from the per-run classifier's own crawl rather than listed.  The
    census is the **committed** one, read as data: the derivation needs to know
    what each node writes, and taking a fresh runtime census here would make a
    gate about the audit depend on a stage about the census.
    """
    committed = json.loads(
        (Path(campaign.data_dir) / "node_writesets.json").read_text()
    )["per_scenario"]
    if config.name not in committed:
        raise GateError(
            f"no write census for {config.name}; the excluded namespaces would "
            f"be guessed, so they are refused"
        )
    writes_by_node = committed[config.name]["writes_by_node"]
    census = {
        "writes_by_node": writes_by_node,
        "node_calls": {node: None for node in writes_by_node},
        "entry": "the committed per-node write census, read as data",
    }
    node_map = json.loads(
        (Path(campaign.data_dir) / "dsm_node_map.json").read_text()
    )
    derived = postsolve_mod.derive(
        config, campaign, lifted=False, census=census, node_map=node_map
    )
    units = list(derived["crawl"]["candidate_units"])
    nodes = list(derived["post_solve_nodes"])
    return {
        "candidate_units": units,
        "post_solve_nodes": nodes,
        "writes_by_node": writes_by_node,
        "derivation": (
            "postsolve.derive(...)['crawl']['candidate_units'] on the "
            "committed write census — derived per configuration, never listed"
        ),
    }


def _scales(config: Config) -> dict[str, float]:
    artifact = json.loads(Path(config.coupling_state_path).read_text())
    return {c["key"]: float(c["scale"]) for c in artifact["components"]}


def _categories(config: Config) -> dict[str, str]:
    artifact = json.loads(Path(config.coupling_state_path).read_text())
    return {c["key"]: c.get("category") for c in artifact["components"]}


def choose_component(
    state: Mapping[str, Any],
    candidates: Sequence[str],
    *,
    categories: Mapping[str, str],
    owned_by_x: Sequence[str],
    where: str,
) -> str:
    """One continuous, non-zero float that the design vector does not own.

    All three conditions matter.  A discrete component cannot be displaced by a
    factor; a zero one cannot be displaced at all; and a component the sweep
    head re-injects from the design vector would be **silently reset** at the
    first model call, so doctoring it would test nothing and the gate would pass
    for the wrong reason.
    """
    owned = set(owned_by_x or ())
    for name in candidates:
        if name in owned:
            continue
        if categories.get(name) != "continuous":
            continue
        value = state.get(name)
        if not (isinstance(value, dict) and value.get("k") == "f"):
            continue
        number = float.fromhex(value["hex"])
        if math.isfinite(number) and number != 0.0:
            return name
    raise GateError(
        f"no eligible component among the {len(candidates)} candidate(s) for "
        f"{where}: every one is discrete, zero, non-finite or owned by the "
        f"design vector.  That is itself a finding — report it rather than "
        f"doctoring something that cannot be doctored."
    )


def doctor_snapshot(
    snapshot: Mapping[str, Any], name: str, *, factor: float = TEETH_FACTOR
) -> tuple[dict[str, Any], float, float]:
    """A copy of the snapshot with one component multiplied, and the two values."""
    document = json.loads(json.dumps(snapshot))
    before = float.fromhex(document["state"][name]["hex"])
    after = before * factor
    document["state"][name] = {"k": "f", "hex": after.hex()}
    return document, before, after


# --------------------------------------------------------------------------
# the runs
# --------------------------------------------------------------------------


def audit_root(campaign: Campaign) -> Path:
    return Path(campaign.runs_dir) / gates_mod.GATES_SUBPATH / "audit_restriction"


def _job(
    campaign: Campaign,
    config: Config,
    label: str,
    entry_state: Path,
    pin_hex: str | None,
) -> pool_mod.Job:
    return pool_mod.Job(
        phase="A",
        arm=G4_ARM,
        config=config,
        seed=0,
        outdir=audit_root(campaign) / config.name / label,
        regime="unperturbed",
        delta=None,
        pin_hex=pin_hex,
        entry_state=entry_state,
        run_kind="gate",
    )


def _pin(config: Config, reference: Mapping[str, Any]) -> str | None:
    if not config.pulsed:
        return None
    if arms_mod.ARMS[G4_ARM].burn_time_owner != "constant":
        return None
    return reference["t_plant_pulse_burn_hex"]


def _restricted(record: Mapping[str, Any]) -> dict[str, Any]:
    block = (record.get("exit_audit") or {}).get("restricted")
    if block is None:
        raise GateError(
            "the run's exit audit carries no restricted statistic; the gate "
            "compares the restricted maximum against the undoctored run and "
            "has nothing to compare"
        )
    return block


def audit_restriction_body(campaign: Campaign) -> dict[str, Any]:
    """G4: blind where it must be blind, sighted where it must be sighted."""
    references = gates_mod.entry_references(campaign, resume=True)
    rows: list[dict[str, Any]] = []
    passed = True
    n_compared = 0
    n_mismatched = 0
    namespaces_seen: dict[str, list[str]] = {}

    for config in campaign.configurations:
        if G4_ARM in config.skips:
            rows.append({"configuration": config.name, "skipped": config.skips[G4_ARM]})
            continue
        reference = references[config.name]
        snapshot = json.loads(Path(reference["snapshot"]).read_text())
        pin = _pin(config, reference)

        # 1. the undoctored run, first and alone: everything else is compared
        #    against it, and its record is where the design vector's own keys
        #    are read from.
        baseline_job = _job(
            campaign, config, "baseline", Path(reference["snapshot"]), pin
        )
        pool_mod.run_all([baseline_job], campaign, resume=True)
        baseline = records_mod.read(baseline_job.outdir)
        if baseline.get("status") != "ok":
            rows.append(
                {
                    "configuration": config.name,
                    "failed_at": (
                        f"the undoctored run did not finish: status "
                        f"{baseline.get('status')!r}"
                    ),
                    "passed": False,
                }
            )
            passed = False
            continue
        baseline_restricted = _restricted(baseline)
        owned_by_x = baseline.get("spec_keys_owned_by_x") or []

        excluded_keys, excluded_detail = gates_mod.excluded_by_the_per_run_nodes(
            campaign, config
        )
        namespaces = excluded_namespaces(campaign, config)
        namespaces_seen[config.name] = namespaces["candidate_units"]
        scales = _scales(config)
        categories = _categories(config)
        tested = set(scales)

        # 2. one doctored component per excluded namespace, plus one in-loop.
        plan: list[tuple[str, str, str]] = []  # (label, namespace, component)
        for unit in namespaces["candidate_units"]:
            node_fields = sorted(
                set(namespaces["writes_by_node"].get(unit, ())) & excluded_keys
            )
            if not node_fields:
                rows.append(
                    {
                        "configuration": config.name,
                        "namespace": unit,
                        "failed_at": (
                            "the namespace writes no component of the coupling "
                            "state on this configuration, so there is nothing "
                            "to doctor.  That is a finding about the namespace, "
                            "not a reason to skip it"
                        ),
                        "passed": False,
                    }
                )
                passed = False
                continue
            component = choose_component(
                snapshot["state"],
                node_fields,
                categories=categories,
                owned_by_x=owned_by_x,
                where=f"{config.name}/{unit}",
            )
            plan.append((f"per_run_{unit}", unit, component))

        in_loop_candidates = sorted(tested - excluded_keys)
        in_loop = choose_component(
            snapshot["state"],
            in_loop_candidates,
            categories=categories,
            owned_by_x=owned_by_x,
            where=f"{config.name}/in-loop",
        )
        plan.append(("in_loop", None, in_loop))

        jobs: list[tuple[str, str, str, pool_mod.Job, float, float]] = []
        for label, unit, component in plan:
            doctored, before, after = doctor_snapshot(snapshot, component)
            directory = audit_root(campaign) / config.name / label
            directory.mkdir(parents=True, exist_ok=True)
            entry = directory / "doctored_entry.json"
            entry.write_text(json.dumps(doctored))
            jobs.append(
                (
                    label,
                    unit,
                    component,
                    _job(campaign, config, label, entry, pin),
                    before,
                    after,
                )
            )
        pool_mod.run_all([job for *_r, job, _b, _a in jobs], campaign, resume=False)

        for label, unit, component, job, before, after in jobs:
            record = records_mod.read(job.outdir)
            row: dict[str, Any] = {
                "configuration": config.name,
                "direction": "per_run-owned" if unit else "in-loop",
                "namespace": unit,
                "component": component,
                "doctored_from_hex": before.hex(),
                "doctored_to_hex": after.hex(),
                "scale": scales.get(component),
                "status": record.get("status"),
            }
            n_compared += 1
            if record.get("status") != "ok":
                row["passed"] = False
                row["failed_at"] = f"the run did not finish: {record.get('status')!r}"
                rows.append(row)
                passed = False
                n_mismatched += 1
                continue
            audit = record.get("exit_audit") or {}
            restricted = _restricted(record)
            vector = json.loads((Path(job.outdir) / "audit_residual.json").read_text())
            expected = abs(after - before) / scales[component]
            got = vector["scaled"].get(component)
            row.update(
                {
                    "expected_scaled_displacement": expected,
                    "whole_state_scaled_at_the_component": got,
                    "whole_state_max_hex": audit.get("residual_max_hex"),
                    "whole_state_max_hex_baseline": (
                        baseline.get("exit_audit") or {}
                    ).get("residual_max_hex"),
                    "restricted_max_hex": restricted.get("max_hex"),
                    "restricted_max_hex_baseline": baseline_restricted.get("max_hex"),
                    "restricted_argmax": restricted.get("argmax"),
                    "restricted_argmax_baseline": baseline_restricted.get("argmax"),
                    "n_excluded": restricted.get("n_excluded"),
                    "n_kept": restricted.get("n_kept"),
                    "block_sweeps": (record.get("module_solve_totals") or {}).get(
                        "block_sweeps"
                    ),
                    "block_sweeps_baseline": (
                        baseline.get("module_solve_totals") or {}
                    ).get("block_sweeps"),
                }
            )
            if unit:
                checks = {
                    "the_component_is_in_the_excluded_set": component in excluded_keys,
                    "the_whole_state_audit_reads_the_displacement": (
                        got is not None
                        and expected > 0
                        and abs(got - expected)
                        <= DISPLACEMENT_RELATIVE_ALLOWANCE * expected
                    ),
                    "the_whole_state_maximum_moved": (
                        row["whole_state_max_hex"] != row["whole_state_max_hex_baseline"]
                    ),
                    "the_whole_state_maximum_is_at_least_the_displacement": (
                        float.fromhex(row["whole_state_max_hex"] or "0x0p+0")
                        >= expected * (1 - DISPLACEMENT_RELATIVE_ALLOWANCE)
                    ),
                    "the_restricted_maximum_is_bit_identical": (
                        row["restricted_max_hex"] == row["restricted_max_hex_baseline"]
                    ),
                    "the_restricted_argmax_is_identical": (
                        row["restricted_argmax"] == row["restricted_argmax_baseline"]
                    ),
                }
            else:
                checks = {
                    "the_component_is_not_in_the_excluded_set": (
                        component not in excluded_keys
                    ),
                    "the_restricted_statistic_moved_or_the_run_did_more_work": (
                        row["restricted_max_hex"] != row["restricted_max_hex_baseline"]
                        or (
                            (row["block_sweeps"] or 0)
                            > (row["block_sweeps_baseline"] or 0)
                        )
                    ),
                }
            row["checks"] = checks
            row["passed"] = all(checks.values())
            if not row["passed"]:
                passed = False
                n_mismatched += 1
            rows.append(row)

        rows.append(
            {
                "configuration": config.name,
                "direction": "baseline",
                "restricted_max_hex": baseline_restricted.get("max_hex"),
                "restricted_argmax": baseline_restricted.get("argmax"),
                "restricted_n_above_tau": baseline_restricted.get("n_above"),
                "whole_state_max_hex": (baseline.get("exit_audit") or {}).get(
                    "residual_max_hex"
                ),
                "n_excluded": baseline_restricted.get("n_excluded"),
                "n_kept": baseline_restricted.get("n_kept"),
                "excluded_namespaces": namespaces["candidate_units"],
                "excluded_detail": excluded_detail,
                "passed": True,
            }
        )

    _HELD["rows"] = rows
    _HELD["namespaces"] = namespaces_seen
    optimisation = optimisation_phase_statistic(campaign)
    _HELD["optimisation"] = optimisation
    return {
        "passed": passed and optimisation["passed"],
        "criterion": (
            "a doctored per-run-owned component trips the whole-state audit "
            "and not the restricted one; a doctored in-loop component trips "
            "the restricted one (or costs more work); one doctored component "
            "from each excluded namespace, both directions, every namespace"
        ),
        "criterion_source": (
            "the experiment plan §3.9's G4 row and improvement item 6a(c), "
            "restated here; nothing is imported from the earlier revision"
        ),
        "population": (
            f"{sum(1 for r in rows if r.get('direction') not in (None, 'baseline'))} "
            f"doctored run(s) over "
            f"{len([c for c in campaign.configurations if G4_ARM not in c.skips])} "
            f"configuration(s), each against that configuration's undoctored "
            f"run; namespaces derived per configuration"
        ),
        "n_compared": n_compared,
        "n_mismatched": n_mismatched,
        "excluded_namespaces_by_configuration": namespaces_seen,
        "optimisation_phase_statistic": optimisation,
        "rows": rows,
    }


# --------------------------------------------------------------------------
# the optimisation record's own restricted statistic
# --------------------------------------------------------------------------


def optimisation_phase_statistic(campaign: Campaign) -> dict[str, Any]:
    """Is the restricted statistic in the optimisation records, and what is it?

    The gate reads whatever optimisation records the other gates have already
    made — the reproduction gate's, the output-path gate's — rather than
    starting runs of its own, because the question is about the **record**, not
    about a new measurement: does an optimisation record now carry the
    statistic, and which component carries the maximum?  A reader who wants to
    know *why* that component is there has the argmax named here and the
    decision in improvement item 11.

    Records stamped ``force_maxcal`` are excluded: they are budget-capped
    demonstrations and never a population.
    """
    root = Path(campaign.runs_dir) / gates_mod.GATES_SUBPATH
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("metrics.json")):
        try:
            record = json.loads(path.read_text())
        except Exception:  # noqa: BLE001 - a half-written record is not a row
            continue
        if record.get("campaign_phase") != "B" or record.get("status") != "ok":
            continue
        if record.get("force_maxcal") is not None:
            continue
        restricted = (record.get("exit_audit") or {}).get("restricted")
        rows.append(
            {
                "arm": record.get("campaign_arm"),
                "configuration": record.get("campaign_configuration"),
                "seed": record.get("campaign_seed"),
                "audit_position": record.get("audit_position"),
                "carries_the_restricted_statistic": restricted is not None,
                "restricted_max": (restricted or {}).get("max"),
                "restricted_max_hex": (restricted or {}).get("max_hex"),
                "restricted_argmax": (restricted or {}).get("argmax"),
                "restricted_n_above_tau": (restricted or {}).get("n_above"),
                "n_excluded": (restricted or {}).get("n_excluded"),
                "n_kept": (restricted or {}).get("n_kept"),
                "record": str(path),
            }
        )
    at_declared = [
        r for r in rows if r["audit_position"] == "entry_to_write_output_files"
    ]
    carrying = [r for r in at_declared if r["carries_the_restricted_statistic"]]
    argmaxes: dict[str, int] = {}
    for row in carrying:
        if row["restricted_n_above_tau"]:
            argmaxes[row["restricted_argmax"]] = (
                argmaxes.get(row["restricted_argmax"], 0) + 1
            )
    return {
        "passed": bool(at_declared) and len(carrying) == len(at_declared),
        "what_it_shows": (
            "every optimisation record audited at the plan's declared position "
            "carries the restricted statistic, and the component that carries "
            "the maximum is named rather than averaged into it"
        ),
        "population": (
            f"{len(at_declared)} optimisation record(s) at the declared audit "
            f"position, from the gates' own runs; "
            f"{len(rows) - len(at_declared)} at the reproduction gate's "
            f"position (after_run) are listed but not counted, because the two "
            f"positions must never share a column unlabelled; records stamped "
            f"force_maxcal are excluded as demonstrations"
        ),
        "n_records_at_the_declared_position": len(at_declared),
        "n_carrying_the_statistic": len(carrying),
        "argmax_above_tau_by_component": argmaxes,
        "note": (
            "a component named here above the tolerance is improvement list "
            "item 11's subject: measured, not diagnosed, and visible rather "
            "than averaged away"
        ),
        "rows": rows,
    }


# --------------------------------------------------------------------------
# the teeth
# --------------------------------------------------------------------------


def _teeth(campaign: Campaign) -> tuple[Tooth, ...]:
    def direction(which: str):
        def look() -> tuple[bool, str]:
            rows = [
                r
                for r in (_HELD.get("rows") or [])
                if r.get("direction") == which and "checks" in r
            ]
            if not rows:
                return False, f"the gate made no {which} run, so nothing was shown"
            ok = all(r["passed"] for r in rows)
            parts = [
                f"{r['configuration']}/{r.get('namespace') or 'in-loop'}: "
                f"{r['component']}"
                for r in rows
            ]
            return ok, (
                f"{len(rows)} doctored {which} run(s) — " + "; ".join(parts)
            )

        return look

    def every_namespace() -> tuple[bool, str]:
        seen = _HELD.get("namespaces") or {}
        rows = [
            r
            for r in (_HELD.get("rows") or [])
            if r.get("direction") == "per_run-owned"
        ]
        covered: dict[str, set[str]] = {}
        for row in rows:
            covered.setdefault(row["configuration"], set()).add(row["namespace"])
        missing = {
            name: sorted(set(units) - covered.get(name, set()))
            for name, units in seen.items()
        }
        ok = bool(seen) and not any(missing.values())
        return ok, (
            "the derived excluded namespaces, each doctored: "
            + "; ".join(
                f"{name}: {sorted(covered.get(name, set()))} of {sorted(units)}"
                for name, units in seen.items()
            )
            + (f"; not covered: {missing}" if any(missing.values()) else "")
        )

    def the_statistic_reaches_the_record() -> tuple[bool, str]:
        block = _HELD.get("optimisation") or {}
        n = block.get("n_records_at_the_declared_position") or 0
        carrying = block.get("n_carrying_the_statistic") or 0
        return bool(n) and carrying == n, (
            f"{carrying} of {n} optimisation record(s) at the declared audit "
            f"position carry the restricted statistic; argmax above the "
            f"tolerance by component: {block.get('argmax_above_tau_by_component')}"
        )

    def an_excluded_component_read_as_kept() -> tuple[bool, str]:
        rows = [
            r
            for r in (_HELD.get("rows") or [])
            if r.get("direction") == "per_run-owned" and "checks" in r
        ]
        if not rows:
            return False, "the gate made no per-run-owned run"
        row = rows[0]
        doctored = {**row["checks"], "the_restricted_maximum_is_bit_identical": False}
        return not all(doctored.values()), (
            f"the restricted maximum of {row['configuration']}'s "
            f"{row['component']} run read as moved rather than bit-identical: "
            f"the check must fail, which is what makes its agreement above a "
            f"measurement rather than a tautology"
        )

    return (
        Tooth(
            name="a doctored per-run-owned component",
            what=(
                "one component a per-run deferred node writes, multiplied by "
                f"{TEETH_FACTOR} in the entry snapshot"
            ),
            must=(
                "move the whole-state audit by exactly the displacement and "
                "leave the restricted audit bit-identical"
            ),
            check=direction("per_run-owned"),
        ),
        Tooth(
            name="a doctored in-loop component",
            what=(
                "one component the in-loop nodes own, multiplied by "
                f"{TEETH_FACTOR} in the entry snapshot"
            ),
            must="move the restricted audit, or cost the run more work",
            check=direction("in-loop"),
        ),
        Tooth(
            name="every excluded namespace doctored",
            what="one component from each derived excluded namespace",
            must=(
                "cover every namespace the derivation returns, on every "
                "configuration — the weakness improvement item 6a(c) recorded"
            ),
            check=every_namespace,
        ),
        Tooth(
            name="the restricted statistic reaches the optimisation record",
            what=(
                "the per-run artifact and the write census handed to the "
                "optimisation phase's audit"
            ),
            must=(
                "populate exit_audit.restricted on every optimisation record "
                "at the declared audit position, with its argmax named"
            ),
            check=the_statistic_reaches_the_record,
        ),
        Tooth(
            name="an excluded component read as kept",
            what=(
                "the bit-identity check of one per-run-owned run's restricted "
                "maximum, forced to false"
            ),
            must="fail that run's check",
            check=an_excluded_component_read_as_kept,
        ),
    )


def audit_restriction_gate(campaign: Campaign) -> Gate:
    return Gate(
        name="audit_restriction",
        plan_name="G4",
        needs_runs=True,
        binds="the similarity statistic, on every configuration",
        what_it_proves=(
            "the restricted audit is blind to exactly the components the "
            "per-run deferred nodes own — one doctored component from each "
            "derived namespace — and sighted to the components the in-loop "
            "nodes own; and that the statistic is in the optimisation record "
            "with the component that carries it named"
        ),
        body=lambda: audit_restriction_body(campaign),
        teeth=_teeth(campaign),
    )
