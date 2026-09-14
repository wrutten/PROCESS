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

Whichever component carries the maximum, this gate **names it**.  A statistic
that reported only "the restricted maximum" without saying which component
carries it would average away the one thing worth deciding about, and the
reason that rule is here is a measured one: for two revisions the maximum on
both pulsed configurations was carried by ``tfcoil.insstrain`` at roughly 7e-3
scaled, in every arm including the reference arm, and was read as a convergence
result.  It was not.  Task **A61 (insstrain-diagnosis)** showed it was the exit
audit's own doing — PROCESS's output path raises the TF-coil stress mesh before
the snapshot is taken, and the audit's sweep then ran the stress model on a
different discretisation than the loop had — and ruling **D25** made the audit
restore the whole data structure before its sweep, so the statistic now
measures the map the loop iterated.  The argmax this gate reports is therefore
the argmax of a convergence statistic again, and the number it carries is what
the handed-over state is actually worth.

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

from ..experiment import arms as arms_mod
from . import gate_output_path
from . import gates as gates_mod
from ..core import pool as pool_mod
from ..child import postsolve as postsolve_mod
from ..core import records as records_mod
from ..core.config import Campaign, Config
from ..core.framework import Gate, GateError, Tooth

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

    Derived from the per-run classifier's own crawl rather than listed, and from
    the **run-time** census rather than the committed one.  That distinction is
    load-bearing and was found by this gate failing: the committed artifact
    records what each node *writes*, and the crawl needs to know what each node
    *ran*.  A node whose body is guarded off on a configuration writes nothing
    and is still executed on every sweep — which is precisely a node worth
    deferring — so a unit list taken from the writers alone drops it, and on the
    steady-state configuration that node is ``pulse``, a whole excluded
    namespace lost in silence.  The committed file's node map is not a
    substitute either: it lists every node the experiment knows, including the
    TF-coil variants this configuration never runs.

    The census is taken with ``resume``, so it reuses the run the artifact
    stages already made rather than starting another.
    """
    from ..child import census as census_mod

    census = census_mod.take(
        config,
        campaign,
        entry=gates_mod.CENSUS_ENTRY["entry"],
        read_census=True,
        resume=True,  # the census is an input to the derivation, not a run of this gate
    )
    writes_by_node = census["writes_by_node"]
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
            "postsolve.derive(...)['crawl']['candidate_units'] on the run-time "
            "write census — derived per configuration, never listed"
        ),
        "census_entry": census.get("entry"),
    }


def _scales(config: Config) -> dict[str, float]:
    """Each component's measured scale, where it has one.

    A discrete component has no scale: it is compared for equality, not for
    distance, so the artifact records none.  Those components are therefore not
    candidates for doctoring — a factor applied to one would not be measurable
    against a scale that does not exist — and :func:`choose_component` refuses
    them on the same ground.
    """
    artifact = json.loads(Path(config.coupling_state_path).read_text())
    return {
        c["key"]: float(c["scale"])
        for c in artifact["components"]
        if c.get("scale") is not None
    }


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


def audit_restriction_body(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    """G4: blind where it must be blind, sighted where it must be sighted."""
    references = gates_mod.entry_references(campaign, resume=resume)
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
        pool_mod.run_all([baseline_job], campaign, resume=resume)
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

        excluded_keys, excluded_detail = gate_output_path.excluded_by_the_per_run_nodes(
            campaign, config
        )
        namespaces = excluded_namespaces(campaign, config)
        namespaces_seen[config.name] = namespaces["candidate_units"]
        scales = _scales(config)
        categories = _categories(config)
        # Every component the audit tests, not only the ones with a scale: the
        # in-loop candidate list is filtered for eligibility afterwards, and a
        # population narrowed here would narrow it twice.
        tested = set(categories)

        # 2. one doctored component per excluded namespace, plus one in-loop.
        plan: list[tuple[str, str, str]] = []  # (label, namespace, component)
        for unit in namespaces["candidate_units"]:
            node_fields = sorted(
                set(namespaces["writes_by_node"].get(unit, ())) & excluded_keys
            )
            if not node_fields:
                # A namespace that writes no component of the coupling state on
                # this configuration excludes nothing, so there is nothing to
                # doctor and nothing the restriction could hide.  That is the
                # certification, not a gap in it -- and it is *recorded*, with
                # the count, rather than left to be inferred from an absence.
                # The live case is `pulse` on the steady-state configuration,
                # whose whole body is guarded off there: it is visited on every
                # sweep and computes nothing.
                rows.append(
                    {
                        "configuration": config.name,
                        "direction": "per_run-owned",
                        "namespace": unit,
                        "component": None,
                        "n_components_owned_here": 0,
                        "why_no_component_is_doctored": (
                            "this namespace writes no component of the coupling "
                            "state on this configuration, so it excludes "
                            "nothing and there is nothing for the restriction "
                            "to hide"
                        ),
                        "passed": True,
                    }
                )
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
        # The doctored entries live **outside** the run directories: a run
        # clears its own directory before it starts, so an entry state written
        # inside one would be deleted by the run that is meant to read it.
        entries_dir = audit_root(campaign) / config.name / "_entries"
        entries_dir.mkdir(parents=True, exist_ok=True)
        for label, unit, component in plan:
            doctored, before, after = doctor_snapshot(snapshot, component)
            entry = entries_dir / f"{label}.json"
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
                    "block_sweeps": (record.get("block_loop_totals") or {}).get(
                        "block_sweeps"
                    ),
                    "block_sweeps_baseline": (
                        baseline.get("block_loop_totals") or {}
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
    optimisation = optimisation_phase_statistic(campaign, resume=resume)
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


#: The arm whose optimisation records the restricted statistic is read from:
#: the full intervention, which is the arm the experiment reports it for.
OPTIMISATION_ARM = "B3"


def optimisation_phase_statistic(
    campaign: Campaign, *, resume: bool = False
) -> dict[str, Any]:
    """Is the restricted statistic in the optimisation records, and what is it?

    The gate makes **one optimisation per configuration** of its own, so that
    the answer does not depend on which other gate happened to run first, and
    then reads every optimisation record any gate has left under ``runs/gates``
    as well — the question is about the **record**: does an optimisation record
    now carry the statistic, and which component carries the maximum?  A reader
    who wants to know *why* that component is there has the argmax named here
    and the decision in improvement item 11.

    Two populations are kept apart and never pooled.  The campaign's declared
    audit position is the entry to the output path; the reproduction gate audits
    where the previous revision audited, after the run, and is the only caller
    allowed to.  Records at the two positions must never share a column without
    saying so, so the verdict counts only the first and lists the second.

    Records stamped ``force_maxcal`` are excluded: they are budget-capped
    demonstrations and never a population.
    """
    root = Path(campaign.runs_dir) / gates_mod.GATES_SUBPATH
    own = [
        pool_mod.Job(
            phase="B",
            arm=OPTIMISATION_ARM,
            config=config,
            seed=0,
            outdir=audit_root(campaign) / config.name / "optimisation",
            regime="unperturbed",
            delta=None,
            run_kind="gate",
        )
        for config in campaign.configurations
        if OPTIMISATION_ARM not in config.skips
    ]
    pool_mod.run_all(own, campaign, resume=resume)
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
                # The audit's own account of what it put back before it swept.
                # Carried on the row so that the tooth which measures the
                # restore's boundary reads a record this gate made, at the
                # declared position, rather than one it found.
                "_instrument": (record.get("exit_audit") or {}).get("instrument"),
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
            if row.get("namespace"):
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

    def the_restore_boundary_is_measured() -> tuple[bool, str]:
        """Where the audit's restore stops, measured on a record and then flipped.

        The audit puts back a **derived** set before its sweep, and one
        namespace is held out of it by a named rule: ``numerics``, the
        optimiser's own account of the run, which the record reads *after* the
        audit.  A rule stated and never exercised is an assertion, so this
        tooth does two things.

        It **measures the boundary** on a record this gate made: a field
        PROCESS's output path changes that is *not* in a held-back namespace —
        the TF-coil stress mesh, which is the case the whole mechanism exists
        for — must be in the restored set and must not be among the fields the
        restore missed; the fields the rule held back must be exactly the
        differing fields in the held-back namespaces, and must still differ
        when the sweep starts, so what the rule costs is visible rather than
        implied.

        Then it **flips the boundary**: the same held-back field name, moved
        into another namespace, must classify as restorable, and the restored
        field's name moved into the held-back namespace must classify as held
        back.  So the rule is the namespace and nothing else — not the field,
        not its value, not where it happens to appear in a record.
        """
        from ..child import child as child_mod

        held_namespaces = set(child_mod.NAMESPACES_THE_AUDIT_DOES_NOT_RESTORE)
        candidate = "tfcoil.n_rad_per_layer"
        # The row this is measured on must show **both** sides of the
        # boundary, so it is chosen for both: the candidate in the restored
        # set, and something actually held back.  A row where the rule held
        # nothing back would show the restore working and say nothing about
        # where it stops, and a tooth that can pass without exercising its
        # subject is the shape this project keeps finding in its own work.
        chosen = None
        fallback = None
        for row in (_HELD.get("optimisation") or {}).get("rows") or []:
            record = row.get("_instrument")
            if not record or not record.get("restored"):
                continue
            if candidate not in (record.get("derived") or []):
                continue
            fallback = fallback or (row, record)
            if record.get("held_back_by_rule"):
                chosen = (row, record)
                break
        chosen = chosen or fallback
        if chosen is None:
            return False, (
                f"no run of this gate carries an exit-audit instrument block "
                f"with {candidate} in its restored set, so the boundary "
                f"between what the audit puts back and what it holds back "
                f"cannot be measured on a record"
            )
        row, instrument = chosen
        start = instrument.get("state_the_sweep_starts_from") or {}
        held = list(instrument.get("held_back_by_rule") or [])
        measured = (
            candidate in (instrument.get("derived") or [])
            and candidate not in (instrument.get("not_restorable") or [])
            and bool(held)
            and all(n.partition(".")[0] in held_namespaces for n in held)
            and sorted(start.get("held_back_by_rule") or []) == sorted(held)
            and not (start.get("the_restore_asked_for_and_missed") or [])
        )
        restorable = lambda name: name.partition(".")[0] not in held_namespaces  # noqa: E731
        moved_held = f"tfcoil.{held[0].partition('.')[2]}" if held else ""
        moved_restored = f"{sorted(held_namespaces)[0]}.n_rad_per_layer"
        flipped = (
            restorable(candidate)
            and not restorable(held[0])
            and restorable(moved_held)
            and not restorable(moved_restored)
        )
        return measured and flipped, (
            f"on {row['arm']}/{row['configuration']}/seed{row['seed']:03d}: "
            f"{candidate} is in the restored set of "
            f"{instrument.get('n_derived')} field(s) and is not among the "
            f"{len(instrument.get('not_restorable') or [])} the restore could "
            f"not put back; the rule held back {held}, all of them in "
            f"{sorted(held_namespaces)}, and all of them still differ when the "
            f"sweep starts "
            f"({start.get('n_outside_the_coupling_state')} field(s) outside "
            f"the coupling state do, "
            f"{start.get('n_of_those_the_restore_asked_for_and_missed')} of "
            f"them because the restore missed them).  Flipped: {moved_held!r} "
            f"classifies as restorable and {moved_restored!r} as held back, so "
            f"the boundary is the namespace and not the field"
        )

    return (
        Tooth(
            name="the restore's boundary, measured and flipped",
            what=(
                "the exit audit's restored set and the one namespace a named "
                "rule holds out of it, read off a record this gate made, and "
                "then the two field names swapped between namespaces"
            ),
            must=(
                "put back the model setting PROCESS's output path changes, "
                "hold back only the optimiser's own accounting, name what it "
                "held back, and classify a swapped name by its namespace"
            ),
            check=the_restore_boundary_is_measured,
        ),
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
        body=lambda *, resume=False: audit_restriction_body(campaign, resume=resume),
        runs_under=("audit_restriction", "entry_references"),
        teeth=_teeth(campaign),
    )
