#!/usr/bin/env python
"""Gate GR: did rewriting the harness change the measurement?

A rewritten harness that changes the measurement is not a rewrite, it is a new
experiment.  This gate is what proves it did not, and it is a **precondition for
the rewrite being accepted**, not a step of the campaign.

How the argument works, in one paragraph.  The experiment runs its own copy of
PROCESS.  At the commit where that copy is taken and **before any driver change
is made**, the copy *is* the driver the previous revision measured — so if the
rewritten harness drives it and reproduces the previous revision's numbers, the
only thing that has changed between the two sets of numbers is the harness, and
it changed nothing.  That is a single-variable comparison, and it is the whole
argument the rewrite needs.  It also means the gate runs **once**: after a driver
change lands, a difference is no longer attributable to the harness alone.

What is compared, and how exactly.  Twenty runs — fourteen optimisations and six
single evaluations, over the three configurations — against the compared field
values committed in ``harness/reference/reproduction_reference.json``.  Every
value is a **count or a hex float**: exact, with **no tolerance anywhere**.  A
missing run is a FAIL, not a smaller gate; a missing field is a FAIL, not a
skip.

What it cannot cover, and what does.  Two arms are new and the previous revision
never ran them, so no record exists to reproduce.  Each is covered by a
*substitute*: an internal consistency check against a reference the gate's own
runs produce.  ``A1`` — the flat arm with a constant owning the burn time —
must land on the reference fixed point when pinned at the reference's own
converged value.  ``AR`` — one evaluation with every architecture switch cleared
— must reproduce the **first evaluation** of the optimisation-phase reference
arm.  Both are stated in the gate's record, so a reader sees the coverage
boundary rather than inferring it from an arm's absence.

The gate-only overrides, stated rather than hidden
--------------------------------------------------
The gate reproduces the **previous revision**, and in two places that revision
did something the campaign no longer does.  Both are recorded as explicit
**overrides**, not as omissions, and both are refused for a campaign run.

*The output path.*  Two arms — the flat arm with the optimiser owning the burn
time, and the partitioned arm — write their output files without upstream's
output-time loop; that is a column of the matrix.  The previous revision's
records for those arms were made before the switch that selects it existed, so
reproducing them means running them with the loop **on**.  The gate therefore
sets ``output_loop = upstream`` for exactly those two arms, explicitly rather
than by leaving the variable unset, so that the driver reads the value back and
the run record carries what it resolved.

*Where the audit is taken.*  The previous revision took its exit audit **after
the run**; the campaign takes it at the entry to the output path, which is the
position the plan declares for every arm.  The residual is one of the values
this gate compares bit for bit, so reproducing it means auditing where it was
audited.  Every optimisation run of this gate therefore asks for the previous
revision's position, and says so in its record.

The guard is set equality against the matrix, not a list somebody maintains:
the arms with an output-path override must be **exactly** the arms whose matrix
cell says the loop is off.  An arm that gains that cell without gaining an
override — or keeps an override after losing the cell — refuses the gate rather
than running a comparison whose composition nobody checked.  The overrides are
in the gate's own record and in every run record it produces, and the campaign
composes through the same function with none and is refused if it carries one.

Written by task **A50 (harness-run)**; the construction is the harness
implementation plan's §7.  When task A52 (harness-gates) builds the gate
framework, this module is what it registers.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

_EXPERIMENT_DIR = Path(__file__).resolve().parents[2]
if str(_EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(_EXPERIMENT_DIR))

from harness.experiment import arms as arms_mod  # noqa: E402
from harness.experiment import input_files as input_files_mod  # noqa: E402
from harness.child import perturb  # noqa: E402
from harness.core import pool as pool_mod  # noqa: E402
from harness.child import predicate as predicate_mod  # noqa: E402
from harness.core import records as records_mod  # noqa: E402
from harness.experiment import switches as switches_mod  # noqa: E402
from harness.gates import reference as reference_mod  # noqa: E402
from harness.core.config import Campaign, Config, default_campaign  # noqa: E402
from harness.gates.selfcheck import Check  # noqa: E402

#: Where the gate's runs and its verdict go.  Untracked bulk; the verdict is
#: small and its content goes into the report's tables.
RUNS_SUBPATH = Path("gates") / "reproduction"

#: Switch terms this gate sets **differently from the matrix**, per arm, with
#: the reason recorded.  Derived from the matrix rather than listed: see
#: :func:`reproduction_overrides` and :func:`assert_overrides_match_matrix`.
#: Nothing outside this gate may use them, and a campaign run carrying one is
#: refused by ``pool.environment_for``.
OVERRIDDEN_TERM = "output_loop"
OVERRIDDEN_VALUE = "upstream"

REPRODUCTION_OVERRIDE_REASON = (
    "the arm's matrix cell says its output files are written without "
    "upstream's output-time loop, and the previous revision's records for this "
    "arm were made before the switch that selects that path existed — so "
    "reproducing them means running the arm the way it was run, with the loop "
    "on.  It is set explicitly rather than left unset so that the driver reads "
    "the value back and the record carries what it resolved.  Recorded in this "
    "gate's record and in every run record it produces; refused for a campaign "
    "run."
)

#: Where this gate takes its exit audit, and why it is not the campaign's
#: position.  This gate is one of the position's declared callers
#: (:data:`harness.core.records.AUDIT_POSITION_AFTER_RUN_CALLERS`) and names
#: itself on every job it makes, which is what the run pool checks.
REPRODUCTION_AUDIT_POSITION = records_mod.AUDIT_POSITION_AFTER_RUN
GATE_NAME = "reproduction"


def reproduction_overrides(arm: str) -> dict[str, str]:
    """What this gate sets differently from the matrix, for one arm.

    Derived from the arm itself: an arm whose matrix cell turns the output-time
    loop off is run with it on, because that is what the records being
    reproduced were made with.  Every other arm gets nothing.
    """
    entry = arms_mod.ARMS.get(arm)
    if entry is None or entry.phase != "B":
        return {}
    if getattr(entry, OVERRIDDEN_TERM) == "none":
        return {OVERRIDDEN_TERM: OVERRIDDEN_VALUE}
    return {}


def assert_overrides_match_matrix() -> dict[str, list[str]]:
    """Set equality between the overridden arms and the matrix, or refuse.

    The failure this prevents: an arm gains the matrix cell and nobody adds the
    override, so the gate runs it under the campaign's composition against
    records made under the previous revision's and reports a difference as the
    harness's.  Or an arm loses the cell and keeps the override, so the gate
    runs something the matrix no longer describes.  Both are silent; both are
    refused here.
    """
    from_matrix = {
        name
        for name, entry in arms_mod.ARMS.items()
        if entry.phase == "B" and getattr(entry, OVERRIDDEN_TERM) == "none"
    }
    overridden = {
        name for name in arms_mod.ARMS if reproduction_overrides(name)
    }
    if from_matrix != overridden:
        raise ReproductionError(
            f"the arms this gate overrides {sorted(overridden)} are not the "
            f"arms whose matrix cell turns the output-time loop off "
            f"{sorted(from_matrix)}; a gate whose composition does not follow "
            f"the matrix is refused rather than run"
        )
    return {
        "arms": sorted(overridden),
        "term": [OVERRIDDEN_TERM],
        "value": [OVERRIDDEN_VALUE],
    }

#: The coupling component a constant owns when the burn time leaves the loop.
PINNED_COMPONENT = "times.t_plant_pulse_burn"


class ReproductionError(RuntimeError):
    """A refusal to run or to compare.  Never downgraded into a warning."""


# --------------------------------------------------------------------------
# the run plan
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class PlannedRun:
    """One run of the gate: the reference entry it answers, and how to make it."""

    run: reference_mod.ReferenceRun
    job: pool_mod.Job


def entry_reference_job(config: Config) -> pool_mod.Job:
    """A configuration's evaluation-phase reference run, as **the one job**.

    The evaluation phase's entries are displacements **of a converged state**,
    not of the input file's cold values, so each configuration needs one
    undisplaced evaluation first: the flat control at the input file's own
    design point, from the cold entry.  Its exit state is what every displaced
    entry is built from, and its converged burn time is what a constant owns.
    Its own cost is the once-per-run cold-start term, reported beside and never
    pooled.

    This gate, ``gates.entry_references`` (G2, G4, G6 and the cold chain) and
    the predicate trial (G8) all compose it **here**, so under the shared pool
    it is one identity and one record — where before A72 it was three
    directories holding the same run (survey §2).
    """
    return pool_mod.Job(
        phase="A",
        arm="A0",
        config=config,
        seed=0,
        regime="unperturbed",
        delta=None,
        run_kind="gate",
    )


def phase_a_reference_directory(campaign: Campaign, config: Config) -> Path:
    """Where the configuration's reference record is: the pool's directory."""
    return pool_mod.directory_for(entry_reference_job(config), campaign)


def plan(campaign: Campaign, root: Path) -> tuple[list[PlannedRun], list[pool_mod.Job]]:
    """The gate's twenty runs, and the evaluation-phase references they need.

    Returns ``(planned, prerequisites)``.  The prerequisites run first and
    serially per configuration, because the runs that follow are entered from
    their exit state.  Every job runs in the shared pool (``outdir`` None);
    *root* is where the verdict and the teeth's scratch files go.
    """
    prerequisites = [entry_reference_job(config) for config in campaign.configurations]
    planned: list[PlannedRun] = []
    for run in reference_mod.reference_set(campaign):
        config = campaign.configuration(run.configuration)
        planned.append(PlannedRun(run, _job_for(run, config, campaign, root)))
    return planned, prerequisites


def _job_for(
    run: reference_mod.ReferenceRun, config: Config, campaign: Campaign, root: Path
) -> pool_mod.Job:
    displaced = run.seed != 0
    if run.phase == "B":
        return pool_mod.Job(
            phase="B",
            arm=run.arm,
            config=config,
            seed=run.seed,
            regime="perturbed" if displaced else "unperturbed",
            delta=campaign.delta,
            run_kind="gate",
            reproduction_overrides=reproduction_overrides(run.arm),
            audit_position=REPRODUCTION_AUDIT_POSITION,
            audit_position_caller=GATE_NAME,
        )
    return pool_mod.Job(
        phase="A",
        arm=run.arm,
        config=config,
        seed=run.seed,
        regime="perturbed" if displaced else "unperturbed",
        delta=campaign.delta,
        run_kind="gate",
    )


def pin_for(reference_burn_hex: str, seed: int, delta: float) -> str:
    """The constant that owns the burn time at one seed, as a hex float.

    It rides the **same** displacement stream the coupling state rides, so the
    constant and the state a run is entered with are displaced together: the
    reference's converged burn time times that seed's factor for that component.
    Passed as a hex literal so a measured value survives the round trip exactly.
    """
    return (
        float.fromhex(reference_burn_hex)
        * perturb.coupling_state_factor(seed, PINNED_COMPONENT, delta)
    ).hex()


def entry_pin(
    config: Config,
    arm: str,
    reference: Mapping[str, Any],
    *,
    seed: int = 0,
    delta: float | None = None,
) -> str | None:
    """The constant *arm* owns at this entry on *config*, or None where it owns none.

    A steady-state configuration has no burn time to own; an arm whose owner is
    not the constant is handed nothing.  At an undisplaced entry (seed 0, or no
    δ) it is the reference's own converged burn time; at a displaced one it
    rides the **same** stream the coupling state rides (:func:`pin_for`), so the
    constant and the state the run is entered with move together.  The one
    implementation of that rule: the chain and gate G2 both call it.
    """
    if not config.pulsed:
        return None
    if arms_mod.ARMS[arm].burn_time_owner != "constant":
        return None
    reference_hex = reference["t_plant_pulse_burn_hex"]
    if not delta or seed == 0:
        return reference_hex
    return pin_for(reference_hex, seed, delta)


def attach_phase_a_entries(
    planned: Sequence[PlannedRun], root: Path, campaign: Campaign
) -> dict[str, dict[str, Any]]:
    """Fill in each evaluation-phase job's entry state and constant.

    Called after the references have run, because both come from them.
    """
    references: dict[str, dict[str, Any]] = {}
    for config in campaign.configurations:
        directory = phase_a_reference_directory(campaign, config)
        record = records_mod.read(directory)
        references[config.name] = {
            "outdir": str(directory),
            "status": record.get("status"),
            "failure_class": record.get("failure_class"),
            "cold_start_node_calls": record.get("node_calls_single_eval"),
            "cold_start_sweeps": record.get("n_model_calls_sweeps"),
            "t_plant_pulse_burn_hex": record.get("t_plant_pulse_burn_hex"),
            "audit_residual_max_hex": (record.get("exit_audit") or {}).get(
                "residual_max_hex"
            ),
            "snapshot": str(directory / "y_exit.json"),
        }
    for item in planned:
        if item.job.phase != "A":
            continue
        entry = references[item.job.config.name]
        if entry["status"] != "ok":
            raise ReproductionError(
                f"the evaluation-phase reference for {item.job.config.name} did "
                f"not finish (status {entry['status']!r}, taxonomy row "
                f"{entry['failure_class']!r}).  Every displaced entry is built "
                f"from its exit state, so there is nothing to displace: this is "
                f"a result, and the gate stops here rather than running the "
                f"entries from somewhere else."
            )
        item.job.entry_state = Path(entry["snapshot"])
        arm = arms_mod.ARMS[item.job.arm]
        if item.job.config.pulsed and arm.burn_time_owner == "constant":
            item.job.pin_hex = pin_for(
                entry["t_plant_pulse_burn_hex"], item.job.seed, campaign.delta
            )
    # The identity is complete now, so the pool's directory is known: resolve
    # it here so that a comparison over kept records (``--skip-runs``) reads
    # the same place a run would have written.
    for item in planned:
        item.job.outdir = pool_mod.directory_for(item.job, campaign)
    return references


def substitute_a0p_jobs(
    campaign: Campaign, references: Mapping[str, Any]
) -> list[tuple[Config, pool_mod.Job]]:
    """The §7.5 substitute for ``A1``: one warm pinned evaluation per pulsed configuration."""
    jobs: list[tuple[Config, pool_mod.Job]] = []
    for config in campaign.configurations:
        if "A1" in config.skips:
            continue
        entry = references[config.name]
        jobs.append(
            (
                config,
                pool_mod.Job(
                    phase="A",
                    arm="A1",
                    config=config,
                    seed=0,
                    regime="unperturbed",
                    delta=None,
                    pin_hex=entry["t_plant_pulse_burn_hex"],
                    entry_state=Path(entry["snapshot"]),
                    run_kind="gate",
                ),
            )
        )
    return jobs


def substitute_ar_jobs(campaign: Campaign) -> list[pool_mod.Job]:
    """The §7.5 substitute for ``AR``: one cold evaluation per configuration."""
    return [
        pool_mod.Job(
            phase="A",
            arm="AR",
            config=config,
            seed=0,
            regime="unperturbed",
            delta=None,
            run_kind="gate",
        )
        for config in campaign.configurations
    ]


COMPOSITION_TOOTH_WRONG_VALUE = "flat"


def composition_tooth_job(
    planned: Sequence[PlannedRun], campaign: Campaign
) -> tuple[PlannedRun | None, pool_mod.Job | None]:
    """The positive control's job: ``B2`` with its analysis-loop switch wrong.

    Its ``override_env`` puts it in the identity apart from the planned ``B2``
    run it is compared against, so the shared pool never hands the tooth the
    very record it exists to differ from.
    """
    candidates = [
        item
        for item in planned
        if item.run.arm == "B2" and item.run.seed == 0
    ]
    # The cheapest configuration, by the previous revision's own cost figures:
    # the steady-state one, which has the shortest design vector.
    chosen = next(
        (item for item in candidates if not campaign.configuration(
            item.run.configuration).pulsed),
        candidates[0] if candidates else None,
    )
    if chosen is None:
        return None, None
    config = campaign.configuration(chosen.run.configuration)
    switch = switches_mod.REGISTRY["mda"].driver_name
    return chosen, pool_mod.Job(
        phase="B",
        arm="B2",
        config=config,
        seed=0,
        regime="unperturbed",
        delta=campaign.delta,
        run_kind="gate",
        reproduction_overrides=reproduction_overrides("B2"),
        audit_position=REPRODUCTION_AUDIT_POSITION,
        audit_position_caller=GATE_NAME,
        override_env={switch: COMPOSITION_TOOTH_WRONG_VALUE},
    )


def planned_jobs(campaign: Campaign) -> list[pool_mod.Job]:
    """The twenty planned runs as jobs, entries attached from the reference records.

    The tally's ``reference_runs`` source (rule (xi)): the gate's own job set,
    read by the tally through the pool rather than through a directory.
    """
    root = Path(campaign.runs_dir) / RUNS_SUBPATH
    planned, _prerequisites = plan(campaign, root)
    attach_phase_a_entries(planned, root, campaign)
    return [item.job for item in planned]


def planned_directories(campaign: Campaign) -> dict[tuple[str, str, int], Path]:
    """Each planned run's directory, by (configuration, arm, seed)."""
    root = Path(campaign.runs_dir) / RUNS_SUBPATH
    planned, _prerequisites = plan(campaign, root)
    attach_phase_a_entries(planned, root, campaign)
    return {
        (item.run.configuration, item.run.arm, item.run.seed): Path(item.job.outdir)
        for item in planned
    }


def jobs_read(campaign: Campaign) -> list[pool_mod.Job]:
    """Every job this gate reads, by identity, composed from records on disk.

    The references first, then the twenty planned runs with their entries
    attached from the reference records, the two substitutes and the
    composition tooth's run.  Refuses (``ReproductionError``) where a reference
    record is not there yet, because the dependent jobs' identities carry its
    exit state and burn time.
    """
    root = Path(campaign.runs_dir) / RUNS_SUBPATH
    planned, prerequisites = plan(campaign, root)
    references = attach_phase_a_entries(planned, root, campaign)
    jobs = list(prerequisites) + [item.job for item in planned]
    jobs += [job for _config, job in substitute_a0p_jobs(campaign, references)]
    jobs += substitute_ar_jobs(campaign)
    _chosen, tooth_job = composition_tooth_job(planned, campaign)
    if tooth_job is not None:
        jobs.append(tooth_job)
    return jobs


# --------------------------------------------------------------------------
# the comparison
# --------------------------------------------------------------------------


def compare_one(
    run: reference_mod.ReferenceRun,
    outdir: Path,
    *,
    document: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """One run against its reference entry, field for field, no tolerance.

    A run whose record is missing is a **failure of the gate**, not one fewer
    comparison: the gate compares twenty runs to twenty entries, and nineteen of
    either is a failed gate.  So is a record that does not carry a compared
    field.

    A field the committed reference holds but this gate no longer compares is
    reported as **excluded**, by name and with its reason
    (:data:`reference.FIELDS_NOT_COMPARED`) — never dropped silently, and never
    counted as a match.  The reference file itself is not touched: it is the
    previous revision's own numbers, and re-extracting it to remove a field
    would be editing the thing being reproduced.
    """
    entry = reference_mod.lookup(
        run.arm, run.configuration, run.seed, document=document
    )
    not_compared = reference_mod.FIELDS_NOT_COMPARED.get(run.phase, {})
    expected = {
        field: value
        for field, value in entry["fields"].items()
        if field not in not_compared
    }
    excluded = {
        field: {
            "in_the_reference": value,
            "why_it_is_not_compared": not_compared[field],
        }
        for field, value in entry["fields"].items()
        if field in not_compared
    }
    record = records_mod.read(outdir)
    result: dict[str, Any] = {
        "key": run.key,
        "arm": run.arm,
        "previous_arm": entry["previous_arm"],
        "configuration": run.configuration,
        "seed": run.seed,
        "phase": run.phase,
        "group": run.group,
        "outdir": str(outdir),
        "status": record.get("status"),
        "failure_class": record.get("failure_class"),
        "source_record": entry["source_path"],
        "source_sha256": entry["source_sha256"],
        "n_fields": len(expected),
        "n_fields_in_the_reference": len(entry["fields"]),
        "n_excluded": len(excluded),
        "excluded": excluded,
        "mismatches": [],
    }
    if record.get("status") != "ok":
        result["mismatches"].append(
            {
                "field": "<the run itself>",
                "expected": "a finished run",
                "found": f"status {record.get('status')!r}",
            }
        )
        result["n_mismatched"] = len(expected)
        result["passed"] = False
        return result
    # The committed reference keeps the **previous revision's** spelling of
    # every compared field, because its bytes are that revision's numbers and
    # regenerating them would make this a comparison with itself.  Where this
    # revision has renamed a record field to the vocabulary's word for it, the
    # map translates the path -- and the translation is recorded per mismatch,
    # so a "missing field" can never be a name error read as a moved number
    # (the orchestrator's ruling at A56 (driver-renames)'s merge; task A53
    # (harness-tally) made the renames).
    name_map = reference_mod.field_name_map()
    renamed = {f: name_map[f] for f in expected if f in name_map}
    result["renamed_fields"] = renamed
    for field, value in expected.items():
        path = name_map.get(field, field)
        try:
            found = records_mod.resolve_path(record, path)
        except KeyError as exc:
            result["mismatches"].append(
                {
                    "field": field,
                    "this_revisions_path": path,
                    "expected": value,
                    "found": f"<missing at {exc.args[0]}>",
                }
            )
            continue
        if found != value:
            result["mismatches"].append(
                {
                    "field": field,
                    "this_revisions_path": path,
                    "expected": value,
                    "found": found,
                }
            )
    result["n_mismatched"] = len(result["mismatches"])
    result["passed"] = not result["mismatches"]
    return result


def compare_all(
    planned: Sequence[PlannedRun], *, document: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Every run against every entry, with the denominator stated."""
    document = document or reference_mod.load()
    rows = [compare_one(item.run, item.job.outdir, document=document) for item in planned]
    n_values = sum(row["n_fields"] for row in rows)
    n_in_reference = sum(row["n_fields_in_the_reference"] for row in rows)
    n_excluded = sum(row["n_excluded"] for row in rows)
    n_mismatched = sum(row["n_mismatched"] for row in rows)
    return {
        "rows": rows,
        "n_runs": len(rows),
        "n_values_in_the_reference": n_in_reference,
        "n_values_excluded": n_excluded,
        "excluded_fields": {
            phase: dict(fields)
            for phase, fields in reference_mod.FIELDS_NOT_COMPARED.items()
            if fields
        },
        "n_values_compared": n_values,
        "n_values_matched": n_values - n_mismatched,
        "n_values_mismatched": n_mismatched,
        "n_runs_reproduced": sum(1 for row in rows if row["passed"]),
        "population": (
            f"{len(rows)} runs "
            f"({sum(1 for r in rows if r['phase'] == 'B')} optimisations + "
            f"{sum(1 for r in rows if r['phase'] == 'A')} evaluations) over "
            f"{len({r['configuration'] for r in rows})} configurations; "
            f"{n_in_reference} values in the committed reference, "
            f"{n_excluded} of them excluded by name with their reason, "
            f"{n_values} compared, no tolerance on any of them"
        ),
        "passed": n_mismatched == 0 and len(rows) > 0,
    }


# --------------------------------------------------------------------------
# the two substitutes for the arms the reference cannot cover
# --------------------------------------------------------------------------


def substitute_pinned_flat_arm(
    campaign: Campaign, root: Path, references: Mapping[str, Any], *, resume: bool
) -> dict[str, Any]:
    """``A1``: pinned at the reference's own converged value, land on it again.

    The flat arm with a **constant** owning the burn time has no record in the
    previous revision — that revision only ever pinned its partitioned arms — so
    there is nothing to reproduce.  What is checked instead is the construction
    the previous revision already used for its partitioned arms, applied to this
    one: enter from the reference's exit state, pin the burn time at the
    reference's own converged value, and require the run to land back on the
    reference fixed point — cross-state maximum scaled residual **below the
    tolerance**, nothing out of its category, and the pinned component
    **bit-identical**.

    It runs on the pulsed configurations only: where there is no burn-time
    coupling there is nothing for a constant to own, and the arm is recorded as
    skipped.
    """
    record: dict[str, Any] = {
        "substitute_for": "A1",
        "why": reference_mod.ARMS_WITHOUT_PREVIOUS_RECORDS["A1"],
        "criterion": (
            "entered from the reference's exit state and pinned at the "
            "reference's own converged burn time, the arm must reproduce the "
            "reference fixed point: cross-state maximum scaled residual < tau, "
            "categorically clean, and the pinned component bit-identical"
        ),
        "tau": campaign.tau,
        "configurations": [],
        "passed": True,
    }
    for config in campaign.configurations:
        if "A1" in config.skips:
            record["configurations"].append(
                {
                    "configuration": config.name,
                    "skipped": config.skips["A1"],
                }
            )
    jobs = substitute_a0p_jobs(campaign, references)
    pool_mod.run_all([job for _config, job in jobs], campaign, resume=resume)
    for config, job in jobs:
        entry = references[config.name]
        row = _fixed_point_row(config, job, entry, campaign)
        record["configurations"].append(row)
        record["passed"] = record["passed"] and row["passed"]
    record["population"] = (
        f"{len(jobs)} pulsed configuration(s); "
        f"{len(campaign.configurations) - len(jobs)} skipped with the reason "
        f"recorded"
    )
    return record


def _fixed_point_row(
    config: Config, job: pool_mod.Job, entry: Mapping[str, Any], campaign: Campaign
) -> dict[str, Any]:
    run_record = records_mod.read(job.outdir)
    row: dict[str, Any] = {
        "configuration": config.name,
        "outdir": str(job.outdir),
        "status": run_record.get("status"),
        "pin_hex": job.pin_hex,
        "burn_time_constant_intact_at_exit": run_record.get("burn_time_constant_intact_at_exit"),
        "node_calls_single_eval": run_record.get("node_calls_single_eval"),
        "n_model_calls_sweeps": run_record.get("n_model_calls_sweeps"),
        "own_audit_residual_max_hex": (run_record.get("exit_audit") or {}).get(
            "residual_max_hex"
        ),
    }
    if run_record.get("status") != "ok":
        row["passed"] = False
        row["failed_at"] = f"the run did not finish: status {row['status']!r}"
        return row
    spec = predicate_mod.load_spec(config.coupling_state_path)
    y_reference = predicate_mod.restore_snapshot(
        spec, json.loads(Path(entry["snapshot"]).read_text())
    )
    y_arm = predicate_mod.restore_snapshot(
        spec, json.loads((Path(job.outdir) / "y_exit.json").read_text())
    )
    cross = predicate_mod.cross_residual(spec, y_reference, y_arm, campaign.tau)
    index = predicate_mod.component_index(spec, PINNED_COMPONENT)
    pin_identical = (
        None if index is None else float(y_reference[index]) == float(y_arm[index])
    )
    row["cross_state_residual"] = cross
    row["pinned_component"] = PINNED_COMPONENT
    row["pinned_component_bit_identical"] = pin_identical
    row["passed"] = bool(
        cross["max"] < campaign.tau
        and cross["categorically_clean"]
        and (pin_identical is not False)
        and run_record.get("burn_time_constant_intact_at_exit") is not False
    )
    return row


def substitute_reference_evaluation(
    campaign: Campaign,
    root: Path,
    planned: Sequence[PlannedRun],
    *,
    resume: bool,
) -> dict[str, Any]:
    """``AR``: one evaluation with every switch cleared reproduces the first call.

    The previous revision had **no evaluation-phase reference arm at all**, so
    there is nothing to reproduce.  What is checked instead is that one
    evaluation with every architecture switch cleared reproduces the **first
    evaluation** of the optimisation-phase reference arm at its undisplaced
    start — its model executions, its sweeps, the prime's count and the
    objective it returned.  Both sides are then upstream's own loop entered from
    the same state, so any difference is the harness's, which is exactly what
    the check is for.

    **The weaker form, stated.**  The previous revision's records do not carry
    the first evaluation's own quantities — that record reports run totals and a
    binned distribution of sweeps per evaluation, not the first call — so this
    check is anchored on **this gate's own** optimisation-phase reference run
    rather than on the previous revision's record.  That anchor is not
    unchecked: the same run is one of the twenty compared field for field
    against the previous revision, and reproduces it.  What cannot be said is
    that the *first-call* numbers themselves were reproduced from a prior
    record; there is no prior record of them.
    """
    record: dict[str, Any] = {
        "substitute_for": "AR",
        "why": reference_mod.ARMS_WITHOUT_PREVIOUS_RECORDS["AR"],
        "criterion": (
            "one evaluation with every architecture switch cleared must "
            "reproduce the first evaluation of the optimisation-phase "
            "reference arm at its undisplaced start, on that call's model "
            "executions, sweeps, prime count and objective hex"
        ),
        "anchor": (
            "this gate's own BR seed 0 runs, because no record of the previous "
            "revision carries the first evaluation's own quantities.  Those "
            "runs are themselves among the twenty compared against the "
            "previous revision"
        ),
        "compared_fields": [
            "node_calls / node_calls_single_eval",
            "sweeps / n_model_calls_sweeps",
            "n_arrangement_method_calls",
            "objf hex",
        ],
        "configurations": [],
        "passed": True,
    }
    anchors = {
        item.run.configuration: item.job.outdir
        for item in planned
        if item.run.arm == "BR" and item.run.seed == 0
    }
    jobs = substitute_ar_jobs(campaign)
    pool_mod.run_all(jobs, campaign, resume=resume)
    n_values = 0
    n_mismatched = 0
    for job in jobs:
        anchor_record = records_mod.read(anchors[job.config.name])
        first = anchor_record.get("first_call_models") or {}
        evaluation = records_mod.read(job.outdir)
        pairs = [
            ("node_calls", first.get("node_calls"),
             evaluation.get("node_calls_single_eval")),
            ("sweeps", first.get("sweeps"),
             evaluation.get("n_model_calls_sweeps")),
            ("n_arrangement_method_calls", first.get("n_arrangement_method_calls"),
             evaluation.get("n_arrangement_method_calls")),
            ("objf_hex", first.get("objf_hex"),
             (evaluation.get("exact") or {}).get("objf")),
        ]
        mismatches = [
            {"field": name, "expected": expected, "found": found}
            for name, expected, found in pairs
            if expected != found
        ]
        n_values += len(pairs)
        n_mismatched += len(mismatches)
        row = {
            "configuration": job.config.name,
            "outdir": str(job.outdir),
            "anchor_outdir": str(anchors[job.config.name]),
            "status": evaluation.get("status"),
            "compared": {name: found for name, _e, found in pairs},
            "anchor": {name: expected for name, expected, _f in pairs},
            "n_compared": len(pairs),
            "n_mismatched": len(mismatches),
            "mismatches": mismatches,
            "passed": evaluation.get("status") == "ok" and not mismatches,
        }
        record["configurations"].append(row)
        record["passed"] = record["passed"] and row["passed"]
    record["n_values_compared"] = n_values
    record["n_values_mismatched"] = n_mismatched
    record["population"] = (
        f"{len(jobs)} configuration(s) x {n_values // max(1, len(jobs))} values "
        f"= {n_values} compared values, no tolerance"
    )
    return record


# --------------------------------------------------------------------------
# the teeth
# --------------------------------------------------------------------------


def _doctored(document: Mapping[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(document))


def teeth(
    planned: Sequence[PlannedRun],
    campaign: Campaign,
    root: Path,
    *,
    resume: bool,
    run_composition_tooth: bool = True,
) -> Check:
    """The eight deliberate breaks, each of which the gate must notice.

    Seven must make it refuse; the eighth must make it do the other thing an
    exclusion has to be shown to do — report a doctored value as excluded by
    name rather than as a match.

    A gate that has never been shown to fail is an assertion, not a
    measurement.  Five of the eight cost nothing — they doctor a copy of the
    reference or of a record — and the fifth is a name lookup.  The sixth is a
    **real run**: the arm composed with one switch deliberately wrong, which is
    the positive control that proves the gate is sensitive to *which arm* ran
    and not merely to whether a run succeeded.  The seventh is a synthetic
    record whose per-attempt costs do not add up.
    """
    check = Check(
        name="reproduction gate teeth",
        binds="each deliberate break must make the comparison, the reference "
        "lookup or the record contract refuse",
        population="8 teeth",
    )
    document = reference_mod.load()
    reproduced = [item for item in planned if item.job.outdir.exists()]
    if not reproduced:
        check.fail("no run directories exist, so no tooth can be shown to trip")
        return check
    sample = next(
        (item for item in reproduced if item.run.phase == "B"), reproduced[0]
    )

    # 1 — count: add one to a reproduced count.
    doctored = _doctored(document)
    target = _entry_in(doctored, sample.run)
    count_field = next(
        name
        for name, value in target["fields"].items()
        if isinstance(value, int) and not isinstance(value, bool)
    )
    target["fields"][count_field] = target["fields"][count_field] + 1
    result = compare_one(sample.run, sample.job.outdir, document=doctored)
    check.tooth(
        "count",
        not result["passed"],
        f"{sample.run.key}: {count_field} raised by one must not reproduce",
    )

    # 2 — hex: append one character to an objective hex string.
    doctored = _doctored(document)
    target = _entry_in(doctored, sample.run)
    hex_field = next(
        name
        for name, value in target["fields"].items()
        if isinstance(value, str) and value.startswith(("0x", "-0x"))
    )
    target["fields"][hex_field] = target["fields"][hex_field] + "0"
    result = compare_one(sample.run, sample.job.outdir, document=doctored)
    check.tooth(
        "hex",
        not result["passed"],
        f"{sample.run.key}: one character appended to {hex_field} must not "
        f"reproduce",
    )

    # 2b — the excluded residual: doctor it in a copy of the reference and
    #      require the comparison to report it as EXCLUDED — not as a mismatch,
    #      which would mean the exclusion is not in force, and not as a match,
    #      which would mean a doctored value passed.  The tooth is what keeps
    #      "we stopped comparing this" from being indistinguishable from "we
    #      compared it and it agreed".
    dropped_field = next(
        iter(reference_mod.FIELDS_NOT_COMPARED.get(sample.run.phase, {})), None
    )
    if dropped_field is None:
        check.tooth(
            "excluded field",
            False,
            f"phase {sample.run.phase} excludes no reference field, so the "
            f"exclusion cannot be shown to be an exclusion",
        )
    else:
        doctored = _doctored(document)
        target = _entry_in(doctored, sample.run)
        original = target["fields"][dropped_field]
        target["fields"][dropped_field] = str(original) + "0"
        result = compare_one(sample.run, sample.job.outdir, document=doctored)
        named = dropped_field in (result.get("excluded") or {})
        not_a_mismatch = all(
            m["field"] != dropped_field for m in result["mismatches"]
        )
        check.tooth(
            "excluded field",
            named and not_a_mismatch and result["passed"],
            f"{sample.run.key}: {dropped_field} doctored in the reference "
            f"({original!r} -> {original!r}+'0') is reported as excluded with "
            f"its reason, is not among the "
            f"{result['n_mismatched']} mismatch(es), and the run still "
            f"reproduces on its {result['n_fields']} compared values — so the "
            f"field is out of the comparison by name and not by accident",
        )

    # 3 — missing reference: point the comparator at a file that is not there.
    caught, message = _must_refuse(
        lambda: reference_mod.load(Path(root) / "_no_such_reference.json")
    )
    check.tooth(
        "missing reference",
        caught,
        f"a reference file that does not exist must FAIL, not compare over an "
        f"empty set ({message})",
    )

    # 4 — missing key: delete a compared field from a copy of a run record.
    stripped = Path(root) / "_teeth" / "missing_key"
    stripped.mkdir(parents=True, exist_ok=True)
    record = records_mod.read(sample.job.outdir)
    dropped = reference_mod.REFERENCE_FIELDS[sample.run.phase][0]
    record.pop(dropped.split(".")[0], None)
    (stripped / "metrics.json").write_text(json.dumps(record))
    result = compare_one(sample.run, stripped, document=document)
    check.tooth(
        "missing key",
        not result["passed"],
        f"a record with {dropped!r} removed must FAIL, not skip the field",
    )

    # 5 — bad name map: ask the previous revision's records for a name it never
    #     had.  The map is what makes the renamed reference arm legal.
    caught, message = _must_refuse(
        lambda: reference_mod.assert_previous_arm_name("BR")
    )
    check.tooth(
        "bad name map",
        caught,
        f"the previous revision's records are named R, not BR; asking for BR "
        f"without the map must RAISE ({message})",
    )

    # 6 — composition: run the partitioned arm with one switch of its
    #     composition deliberately wrong.
    if run_composition_tooth:
        check.teeth.append(_composition_tooth(planned, campaign, root, resume=resume))
        if not check.teeth[-1]["caught"]:
            check.passed = False
            check.detail.append(
                "TOOTH DID NOT TRIP: composition — "
                + check.teeth[-1]["what"]
            )
    else:
        check.note(
            "the composition tooth was not run in this invocation; it starts a "
            "PROCESS run and is part of the full gate"
        )

    # 7 — attempt summation: a synthetic record whose parts do not add up.
    synthetic = {
        "campaign_run_kind": "gate",
        "failure_class": "ok",
        "node_calls_solve_phase": 1000,
        "attempts": [
            {"attempt": 1, "node_calls_solve_phase": 400},
            {"attempt": 2, "node_calls_solve_phase": 550},
        ],
    }
    caught, message = _must_refuse(
        lambda: records_mod.assert_attempt_summation(synthetic, where="a tooth")
    )
    check.tooth(
        "attempt summation",
        caught,
        f"400 + 550 = 950 against a run total of 1000 must be REFUSED "
        f"({message})",
    )
    check.n_compared = len(check.teeth)
    return check


def _composition_tooth(
    planned: Sequence[PlannedRun], campaign: Campaign, root: Path, *, resume: bool
) -> dict[str, Any]:
    """Run the partitioned arm with its analysis-loop switch set to ``flat``.

    Every other switch of the arm stays as the arm declares it, so the run is
    ``B2`` in name and in composition except for the one thing the arm is
    *about*: the shape of the analysis loop.  It is a different arm, and the
    gate must say so.  This is the positive control: it proves the comparison
    is sensitive to *which arm ran*, not merely to whether a run finished.

    **What this tooth used to be, and why it changed.**  It used to clear the
    switch that chose between running the block schedule once and repeating it,
    because with that switch unset the driver ran the repeated schedule under
    the partitioned arm's name — a wrong arm with a right-looking name, which
    is the failure this gate has to be able to see.  A56 (driver-renames)
    folded that switch into the partitioned value, so the mis-composition it
    perturbed **cannot be written down any more**: there is no setting that
    makes the partitioned loop repeat its schedule, and the old switch name
    raises.  That is a narrowing of what can go wrong, not a loss of coverage
    — but it does mean the positive control now perturbs a different switch,
    and this is where a reader is told so.
    """
    chosen, job = composition_tooth_job(planned, campaign)
    if chosen is None or job is None:
        return {
            "tooth": "composition",
            "caught": False,
            "what": "no B2 run at seed 0 is planned, so the tooth cannot run",
        }
    config = campaign.configuration(chosen.run.configuration)
    switch = switches_mod.REGISTRY["mda"].driver_name
    wrong_value = COMPOSITION_TOOTH_WRONG_VALUE
    pool_mod.run_all([job], campaign, resume=resume)
    result = compare_one(chosen.run, job.outdir)
    record = records_mod.read(job.outdir)
    return {
        "tooth": "composition",
        "caught": not result["passed"],
        "what": (
            f"B2 on {config.name} run with {switch}={wrong_value} — so the "
            f"flat loop ran under the partitioned arm's name, every other "
            f"switch of the arm unchanged — must not reproduce the previous "
            f"revision's partitioned optimisation arm (V3's B3).  {result['n_mismatched']} of "
            f"{result['n_fields']} compared values differ"
        ),
        "outdir": str(job.outdir),
        "configuration": config.name,
        "switch_perturbed": f"{switch}={wrong_value}",
        "resolved_mda": (record.get("resolved_switches") or {}).get(
            "process.core.solver.module_solve.MDA_MODE"
        ),
        "n_fields": result["n_fields"],
        "n_mismatched": result["n_mismatched"],
        "mismatched_fields": [m["field"] for m in result["mismatches"]],
    }


def _entry_in(
    document: Mapping[str, Any], run: reference_mod.ReferenceRun
) -> dict[str, Any]:
    for entry in document["entries"]:
        if (
            entry["arm"] == run.arm
            and entry["configuration"] == run.configuration
            and entry["seed"] == run.seed
        ):
            return entry
    raise ReproductionError(f"the reference has no entry for {run.key}")


def _must_refuse(call) -> tuple[bool, str]:
    """Whether *call* refused, and what it said.  A success is a tooth failure."""
    try:
        call()
    except Exception as exc:  # noqa: BLE001 - the refusal is the result
        return True, f"{type(exc).__name__}: {str(exc).splitlines()[0][:160]}"
    return False, "it did not refuse"


# --------------------------------------------------------------------------
# the stage
# --------------------------------------------------------------------------


def stage(
    *,
    campaign: Campaign | None = None,
    root: Path | None = None,
    resume: bool = False,
    skip_runs: bool = False,
) -> tuple[int, dict[str, Any]]:
    """Run gate GR and write its verdict.  0 PASS, 1 FAIL, 3 refused to start."""
    campaign = campaign or default_campaign()
    root = Path(root or (campaign.runs_dir / RUNS_SUBPATH))
    root.mkdir(parents=True, exist_ok=True)

    verdict: dict[str, Any] = {
        "gate": "GR — the reproduction gate for the harness rewrite",
        "what_it_proves": (
            "the rewritten harness, driving the experiment's own copy of "
            "PROCESS before any driver change, reproduces the previous "
            "revision's numbers bit for bit — so the rewrite changed the "
            "measurement in no respect this experiment compares on"
        ),
        "tree": str(campaign.tree),
        "root": str(root),
        "workers": pool_mod.workers(campaign),
        "reproduction_overrides": {
            "arms": {
                arm: reproduction_overrides(arm)
                for arm in arms_mod.ARMS
                if reproduction_overrides(arm)
            },
            "why": REPRODUCTION_OVERRIDE_REASON,
            "audit_position": REPRODUCTION_AUDIT_POSITION,
            "audit_position_caller": GATE_NAME,
            "audit_position_why": records_mod.AUDIT_POSITION_AFTER_RUN_CALLERS[GATE_NAME],
            "audit_position_note": records_mod.AUDIT_POSITION_AFTER_RUN_WHY,
            "matches_the_matrix": assert_overrides_match_matrix(),
            "available_to_the_campaign": False,
        },
        "coverage_boundary": dict(reference_mod.ARMS_WITHOUT_PREVIOUS_RECORDS),
    }

    if not campaign.is_experiment_copy:
        verdict["refused"] = (
            f"the tree is {campaign.tree}, not the experiment's own copy; the "
            f"gate compares the copy against the previous revision's records "
            f"and nothing else"
        )
        return 3, verdict

    # The two lifted input files, checked before anything runs.
    verdict["input_files"] = _resolve_input_files(campaign)
    if verdict["input_files"].get("refused"):
        verdict["refused"] = verdict["input_files"]["refused"]
        return 3, verdict

    planned, prerequisites = plan(campaign, root)
    verdict["n_planned"] = len(planned)

    if not skip_runs:
        print(
            f"gate GR: {len(prerequisites)} evaluation-phase reference run(s), "
            f"then {len(planned)} reference runs at "
            f"{pool_mod.workers(campaign)} workers",
            flush=True,
        )
        pool_mod.run_all(prerequisites, campaign, resume=resume)
    try:
        references = attach_phase_a_entries(planned, root, campaign)
    except ReproductionError as exc:
        verdict["refused"] = str(exc)
        return 3, verdict
    verdict["phase_a_references"] = references

    if not skip_runs:
        phase_b = [item.job for item in planned if item.job.phase == "B"]
        phase_a = [item.job for item in planned if item.job.phase == "A"]
        pool_mod.run_all(phase_b + phase_a, campaign, resume=resume)

    verdict["comparison"] = compare_all(planned)
    verdict["record_contract"] = _record_contract(planned)
    if not skip_runs:
        verdict["substitutes"] = {
            "A1": substitute_pinned_flat_arm(
                campaign, root, references, resume=resume
            ),
            "AR": substitute_reference_evaluation(
                campaign, root, planned, resume=resume
            ),
        }
    teeth_check = teeth(
        planned, campaign, root, resume=resume, run_composition_tooth=not skip_runs
    )
    verdict["teeth"] = teeth_check.as_record()

    passed = (
        verdict["comparison"]["passed"]
        and teeth_check.passed
        and verdict["record_contract"]["passed"]
        and all(
            block["passed"]
            for block in (verdict.get("substitutes") or {}).values()
        )
    )
    verdict["verdict"] = "PASS" if passed else "FAIL"
    (root / "gate.json").write_text(json.dumps(verdict, indent=2, default=str))
    return (0 if passed else 1), verdict


def _resolve_input_files(campaign: Campaign) -> dict[str, Any]:
    """Prove each pulsed configuration's lifted input file is the declared one.

    The file is derived by ``--artifacts derive-inputs`` and gated on its
    digest there; here it is only asserted present and identical, so that a
    run on a different problem is refused before it is made.
    """
    block: dict[str, Any] = {"resolved": []}
    for config in campaign.configurations:
        if not config.pulsed:
            continue
        try:
            block["resolved"].append(input_files_mod.assert_lifted(config, campaign))
        except input_files_mod.InputFileError as exc:
            block["refused"] = str(exc)
            return block
    return block


def _record_contract(planned: Sequence[PlannedRun]) -> dict[str, Any]:
    """Every record the gate produced, through the record module's refusals.

    Separate from the field comparison on purpose: a record can carry the right
    numbers and still be missing a field a later summary needs, and the two
    failures are not the same failure.
    """
    rows = []
    for item in planned:
        record = records_mod.read(item.job.outdir)
        try:
            records_mod.assert_usable(record, where=item.run.key)
            rows.append({"key": item.run.key, "complete": True})
        except records_mod.RecordError as exc:
            rows.append(
                {
                    "key": item.run.key,
                    "complete": False,
                    "refusal": str(exc),
                    "missing": (
                        records_mod.missing_fields(record)
                        if record.get("campaign_phase")
                        else ["<the record does not name its phase>"]
                    ),
                }
            )
    return {
        "rows": rows,
        "n_records": len(rows),
        "n_complete": sum(1 for row in rows if row["complete"]),
        "population": f"{len(rows)} records of the gate's reference runs",
        "passed": all(row["complete"] for row in rows),
    }


# --------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------


def summary(verdict: Mapping[str, Any]) -> list[str]:
    """The gate's own lines, for a reader watching it run."""
    lines: list[str] = []
    if verdict.get("refused"):
        lines.append(f"  REFUSED — {verdict['refused']}")
        return lines
    comparison = verdict.get("comparison") or {}
    lines.append(
        f"  {comparison.get('n_runs_reproduced')}/{comparison.get('n_runs')} "
        f"runs reproduced; "
        f"{comparison.get('n_values_matched')}/"
        f"{comparison.get('n_values_compared')} compared values identical "
        f"({comparison.get('n_values_mismatched')} mismatched)"
    )
    lines.append(f"  population : {comparison.get('population')}")
    for row in comparison.get("rows", []):
        if not row["passed"]:
            lines.append(
                f"  MISMATCH {row['key']}: "
                + "; ".join(
                    f"{m['field']} expected {m['expected']!r} found {m['found']!r}"
                    for m in row["mismatches"][:6]
                )
            )
    contract = verdict.get("record_contract") or {}
    lines.append(
        f"  record contract: {contract.get('n_complete')}/"
        f"{contract.get('n_records')} records carry every declared field"
    )
    for name, block in (verdict.get("substitutes") or {}).items():
        lines.append(
            f"  substitute {name}: "
            f"{'PASS' if block.get('passed') else 'FAIL'} — "
            f"{block.get('population')}"
        )
    for tooth in (verdict.get("teeth") or {}).get("teeth", []):
        mark = "tripped" if tooth["caught"] else "DID NOT TRIP"
        lines.append(f"  tooth {mark}: {tooth['tooth']} — {tooth['what']}")
    return lines


def tables(verdict: Mapping[str, Any]) -> str:
    """The gate's own tables, in the shape the task report prints them.

    A formatter over the committed verdict record and nothing else: it starts
    no run and recomputes no number, so a table in the report and the record it
    came from cannot disagree.  Every table carries its caption, its population
    and its construction (protocol §16).
    """
    out: list[str] = []
    comparison = verdict.get("comparison") or {}
    rows = comparison.get("rows", [])

    out.append(
        "*Caption: one row per reference run of gate GR.  \"Fields\" is how many "
        "compared values that run's phase carries — 15 for an optimisation, 10 "
        "for an evaluation — and \"mismatches\" how many of them differ from the "
        "previous revision's recorded value.  No tolerance is applied to any of "
        "them: every value is a count or a hex float.  \"Wall\" is the child "
        "process's own elapsed time and is context only; no conclusion of this "
        "experiment rests on a timing.  Population: "
        + str(comparison.get("population", "")) + ".*"
    )
    out.append("")
    out.append(
        "| arm | previous name | configuration | seed | phase | fields | "
        "mismatches | status | wall (s) |"
    )
    out.append("|---|---|---|---:|---|---:|---:|---|---:|")
    for row in rows:
        record = records_mod.read(Path(row["outdir"]))
        wall = record.get("wall_s")
        out.append(
            f"| `{row['arm']}` | `{row['previous_arm']}` | "
            f"{row['configuration']} | {row['seed']} | {row['phase']} | "
            f"{row['n_fields']} | {row['n_mismatched']} | {row['status']} | "
            + (f"{wall:.1f}" if isinstance(wall, (int, float)) else "—")
            + " |"
        )
    by_phase: dict[str, list[int]] = {}
    for row in rows:
        entry = by_phase.setdefault(row["phase"], [0, 0, 0])
        entry[0] += 1
        entry[1] += row["n_fields"]
        entry[2] += row["n_mismatched"]
    out.append("")
    out.append(
        "*Caption: the same comparison summed by phase.  \"Values\" is runs x "
        "fields; \"identical\" is values minus mismatches.  The two phases "
        "compare different field lists because the evaluation phase's records "
        "carry no optimiser fields — 15 fields per optimisation, 10 per "
        "evaluation.*"
    )
    out.append("")
    out.append("| phase | runs | fields each | values | identical | mismatched |")
    out.append("|---|---:|---:|---:|---:|---:|")
    for phase in sorted(by_phase):
        n_runs, n_values, n_bad = by_phase[phase]
        label = "B (one optimisation)" if phase == "B" else "A (one evaluation)"
        out.append(
            f"| {label} | {n_runs} | {n_values // n_runs} | {n_values} | "
            f"{n_values - n_bad} | {n_bad} |"
        )
    out.append(
        f"| **both** | **{comparison.get('n_runs')}** | — | "
        f"**{comparison.get('n_values_compared')}** | "
        f"**{comparison.get('n_values_matched')}** | "
        f"**{comparison.get('n_values_mismatched')}** |"
    )

    out.append("")
    out.append(
        "*Caption: one row per tooth of gate GR (harness plan §7.3).  A tooth is "
        "a deliberately broken input that the gate must refuse; a gate whose "
        "teeth have never been shown to trip is an assertion rather than a "
        "measurement (protocol §12).  Population: "
        + str(len((verdict.get("teeth") or {}).get("teeth", [])))
        + " teeth, all of which tripped.*"
    )
    out.append("")
    out.append("| tooth | what was broken | tripped |")
    out.append("|---|---|---|")
    for tooth in (verdict.get("teeth") or {}).get("teeth", []):
        what = str(tooth["what"]).replace("|", "\\|")
        out.append(
            f"| {tooth['tooth']} | {what} | "
            + ("yes" if tooth["caught"] else "**NO**")
            + " |"
        )

    substitutes = verdict.get("substitutes") or {}
    if "A1" in substitutes:
        block = substitutes["A1"]
        out.append("")
        out.append(
            "*Caption: the substitute for `A1`, the arm no earlier record "
            "covers.  Each row is one configuration; the criterion is the one "
            "quoted in the row above the table.  \"Cross-state max\" is the "
            "largest scaled residual between the arm's exit state and the "
            "reference's, over the coupling state's tested components; the "
            "tolerance is 1e-6.  Population: "
            + str(block.get("population", "")) + ".*"
        )
        out.append("")
        out.append(
            "| configuration | pin (hex) | cross-state max | as hex | argmax | "
            "above τ | categorically clean | pinned component identical | "
            "verdict |"
        )
        out.append("|---|---|---:|---|---|---:|---|---|---|")
        for row in block.get("configurations", []):
            if "skipped" in row:
                out.append(
                    f"| {row['configuration']} | — | — | — | — | — | — | — | "
                    f"skipped: {row['skipped']} |"
                )
                continue
            cross = row.get("cross_state_residual") or {}
            out.append(
                f"| {row['configuration']} | `{row.get('pin_hex')}` | "
                f"{cross.get('max'):.3g} | `{cross.get('max_hex')}` | "
                f"`{cross.get('argmax')}` | {cross.get('n_above_tau')} | "
                f"{cross.get('categorically_clean')} | "
                f"{row.get('pinned_component_bit_identical')} | "
                + ("PASS" if row.get("passed") else "FAIL")
                + " |"
            )
    if "AR" in substitutes:
        block = substitutes["AR"]
        out.append("")
        out.append(
            "*Caption: the substitute for `AR`, the arm no earlier record "
            "covers.  Each row is one configuration; the anchor is this gate's "
            "own `BR` run at seed 0 on that configuration, whose first "
            "evaluation of the model set the arm must reproduce exactly.  Four "
            "values per configuration, no tolerance.  Population: "
            + str(block.get("population", "")) + ".*"
        )
        out.append("")
        out.append(
            "| configuration | node calls (AR / first call of BR) | sweeps | "
            "prime calls | objective hex | mismatches |"
        )
        out.append("|---|---|---|---:|---|---:|")
        for row in block.get("configurations", []):
            compared = row.get("compared") or {}
            anchor_values = row.get("anchor") or {}
            out.append(
                f"| {row['configuration']} | "
                f"{compared.get('node_calls')} / {anchor_values.get('node_calls')} | "
                f"{compared.get('sweeps')} / {anchor_values.get('sweeps')} | "
                f"{compared.get('n_arrangement_method_calls')} | "
                f"`{compared.get('objf_hex')}` | {row.get('n_mismatched')} |"
            )
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--resume", action="store_true",
                        help="keep a run whose directory already holds a "
                             "complete record of the same job; a directory "
                             "alone is never evidence")
    parser.add_argument("--skip-runs", action="store_true",
                        help="compare and run the cost-free teeth against "
                             "records that already exist, starting nothing")
    parser.add_argument("--tables", action="store_true",
                        help="emit the report's tables from the committed "
                             "verdict record and stop; starts nothing and "
                             "recomputes nothing")
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args(argv)
    if args.tables:
        campaign = default_campaign()
        path = Path(campaign.runs_dir / RUNS_SUBPATH / "gate.json")
        if not path.exists():
            print(
                f"there is no verdict record at {path}; run the gate first "
                f"(experiment_runner.py --gate reproduction)"
            )
            return 3
        print(tables(json.loads(path.read_text())))
        return 0
    code, verdict = stage(
        resume=args.resume,
        skip_runs=args.skip_runs,
    )
    print("=" * 74)
    print("gate GR — the reproduction gate for the harness rewrite")
    print("=" * 74)
    for line in summary(verdict):
        print(line)
    print("=" * 74)
    print(f"verdict: {verdict.get('verdict', 'REFUSED')}")
    print("=" * 74)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(verdict, indent=2, default=str))
        print(f"record: {args.json}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
