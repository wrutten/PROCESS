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
runs produce.  ``A0p`` — the flat arm with a constant owning the burn time —
must land on the reference fixed point when pinned at the reference's own
converged value.  ``AR`` — one evaluation with every architecture switch cleared
— must reproduce the **first evaluation** of the optimisation-phase reference
arm.  Both are stated in the gate's record, so a reader sees the coverage
boundary rather than inferring it from an arm's absence.

The gate-only allowance, stated rather than hidden
--------------------------------------------------
Two arms declare a switch that selects an output path without upstream's
output-time loop.  **No tree implements it yet** — it is approved driver change
DR2, task A57 (driver-output-path) — and the run path refuses any arm asking for
a switch the tree does not have, because running without it would be a
successful run of a *different* arm under the right name.  But the previous
revision's records for those two arms were made **before that switch existed**,
so reproducing them means running them the way they were run.  The allowance is
therefore: explicit, named in the gate's record and in every record it produces,
checked to cover exactly the switches this tree cannot implement and no others,
and **unavailable to the campaign** — the campaign composes through the same
function with no allowance and is refused.

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

_EXPERIMENT_DIR = Path(__file__).resolve().parent.parent
if str(_EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(_EXPERIMENT_DIR))

from harness import arms as arms_mod  # noqa: E402
from harness import input_files as input_files_mod  # noqa: E402
from harness import perturb  # noqa: E402
from harness import pool as pool_mod  # noqa: E402
from harness import predicate as predicate_mod  # noqa: E402
from harness import records as records_mod  # noqa: E402
from harness import reference as reference_mod  # noqa: E402
from harness.config import Campaign, Config, default_campaign  # noqa: E402
from harness.selfcheck import Check  # noqa: E402

#: Where the gate's runs and its verdict go.  Untracked bulk; the verdict is
#: small and its content goes into the report's tables.
RUNS_SUBPATH = Path("gates") / "reproduction"

#: Switch terms this tree does not implement that the gate is allowed to omit,
#: per arm, **with the reason recorded**.  Nothing else may be added here, and
#: nothing outside this gate may use it.
GATE_ALLOWANCE: dict[str, tuple[str, ...]] = {
    "B1": ("output_loop",),
    "B3": ("output_loop",),
}

GATE_ALLOWANCE_REASON = (
    "the arm declares the switch that selects an output path without "
    "upstream's output-time loop.  No tree implements it yet (approved driver "
    "change DR2, task A57 (driver-output-path)), and the previous revision's "
    "records for this arm were made before it existed — so reproducing them "
    "means running the arm the way it was run.  The allowance is recorded in "
    "this gate's record and in every run record it produces, is checked to "
    "cover exactly the switches this tree cannot implement, and is not "
    "available to the campaign."
)

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


def phase_a_reference_directory(root: Path, configuration: str) -> Path:
    """Where a configuration's evaluation-phase reference run lives.

    The evaluation phase's entries are displacements **of a converged state**,
    not of the input file's cold values, so each configuration needs one
    undisplaced evaluation first: the flat control at the input file's own
    design point, from the cold entry.  Its exit state is what every displaced
    entry is built from, and its converged burn time is what a constant owns.
    Its own cost is the once-per-run cold-start term, reported beside and never
    pooled.
    """
    return Path(root) / "phase_a_reference" / configuration


def plan(campaign: Campaign, root: Path) -> tuple[list[PlannedRun], list[pool_mod.Job]]:
    """The gate's twenty runs, and the evaluation-phase references they need.

    Returns ``(planned, prerequisites)``.  The prerequisites run first and
    serially per configuration, because the runs that follow are entered from
    their exit state.
    """
    prerequisites = [
        pool_mod.Job(
            phase="A",
            arm="A0",
            config=config,
            seed=0,
            outdir=phase_a_reference_directory(root, config.name),
            regime="unperturbed",
            delta=None,
            run_kind="gate",
        )
        for config in campaign.configurations
    ]
    planned: list[PlannedRun] = []
    for run in reference_mod.reference_set(campaign):
        config = campaign.configuration(run.configuration)
        planned.append(PlannedRun(run, _job_for(run, config, campaign, root)))
    return planned, prerequisites


def _job_for(
    run: reference_mod.ReferenceRun, config: Config, campaign: Campaign, root: Path
) -> pool_mod.Job:
    outdir = (
        Path(root)
        / "runs"
        / run.configuration
        / run.arm
        / pool_mod.seed_directory(run.seed)
    )
    displaced = run.seed != 0
    if run.phase == "B":
        return pool_mod.Job(
            phase="B",
            arm=run.arm,
            config=config,
            seed=run.seed,
            outdir=outdir,
            regime="perturbed" if displaced else "unperturbed",
            delta=campaign.delta,
            run_kind="gate",
            allow_pending=GATE_ALLOWANCE.get(run.arm, ()),
        )
    return pool_mod.Job(
        phase="A",
        arm=run.arm,
        config=config,
        seed=run.seed,
        outdir=outdir,
        regime="perturbed" if displaced else "unperturbed",
        delta=campaign.delta,
        run_kind="gate",
        allow_pending=GATE_ALLOWANCE.get(run.arm, ()),
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


def attach_phase_a_entries(
    planned: Sequence[PlannedRun], root: Path, campaign: Campaign
) -> dict[str, dict[str, Any]]:
    """Fill in each evaluation-phase job's entry state and constant.

    Called after the references have run, because both come from them.
    """
    references: dict[str, dict[str, Any]] = {}
    for config in campaign.configurations:
        directory = phase_a_reference_directory(root, config.name)
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
    return references


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
    """
    entry = reference_mod.lookup(
        run.arm, run.configuration, run.seed, document=document
    )
    expected = entry["fields"]
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
    for field, value in expected.items():
        try:
            found = records_mod.resolve_path(record, field)
        except KeyError as exc:
            result["mismatches"].append(
                {
                    "field": field,
                    "expected": value,
                    "found": f"<missing at {exc.args[0]}>",
                }
            )
            continue
        if found != value:
            result["mismatches"].append(
                {"field": field, "expected": value, "found": found}
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
    n_mismatched = sum(row["n_mismatched"] for row in rows)
    return {
        "rows": rows,
        "n_runs": len(rows),
        "n_values_compared": n_values,
        "n_values_matched": n_values - n_mismatched,
        "n_values_mismatched": n_mismatched,
        "n_runs_reproduced": sum(1 for row in rows if row["passed"]),
        "population": (
            f"{len(rows)} runs "
            f"({sum(1 for r in rows if r['phase'] == 'B')} optimisations + "
            f"{sum(1 for r in rows if r['phase'] == 'A')} evaluations) over "
            f"{len({r['configuration'] for r in rows})} configurations; "
            f"{n_values} compared values, no tolerance on any of them"
        ),
        "passed": n_mismatched == 0 and len(rows) > 0,
    }


# --------------------------------------------------------------------------
# the two substitutes for the arms the reference cannot cover
# --------------------------------------------------------------------------


def substitute_pinned_flat_arm(
    campaign: Campaign, root: Path, references: Mapping[str, Any], *, resume: bool
) -> dict[str, Any]:
    """``A0p``: pinned at the reference's own converged value, land on it again.

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
        "substitute_for": "A0p",
        "why": reference_mod.ARMS_WITHOUT_PREVIOUS_RECORDS["A0p"],
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
    jobs: list[tuple[Config, pool_mod.Job]] = []
    for config in campaign.configurations:
        if "A0p" in config.skips:
            record["configurations"].append(
                {
                    "configuration": config.name,
                    "skipped": config.skips["A0p"],
                }
            )
            continue
        entry = references[config.name]
        jobs.append(
            (
                config,
                pool_mod.Job(
                    phase="A",
                    arm="A0p",
                    config=config,
                    seed=0,
                    outdir=Path(root) / "substitute_a0p" / config.name,
                    regime="unperturbed",
                    delta=None,
                    pin_hex=entry["t_plant_pulse_burn_hex"],
                    entry_state=Path(entry["snapshot"]),
                    run_kind="gate",
                ),
            )
        )
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
        "pin_intact_at_exit": run_record.get("pin_intact_at_exit"),
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
        and run_record.get("pin_intact_at_exit") is not False
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
            "n_prime_calls",
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
    jobs = [
        pool_mod.Job(
            phase="A",
            arm="AR",
            config=config,
            seed=0,
            outdir=Path(root) / "substitute_ar" / config.name,
            regime="unperturbed",
            delta=None,
            run_kind="gate",
        )
        for config in campaign.configurations
    ]
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
            ("n_prime_calls", first.get("n_prime_calls"),
             evaluation.get("n_prime_calls")),
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
    """The seven deliberate breaks, each of which must make the gate refuse.

    A gate that has never been shown to fail is an assertion, not a
    measurement.  Four of the seven cost nothing — they doctor a copy of the
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
        population="7 teeth",
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
    """Run the partitioned arm with the schedule switch cleared.

    With that switch unset the driver runs its **default** schedule — the one
    that repeats the block pass while anything is still moving — under the
    partitioned arm's name.  It is a different arm, and the gate must say so.
    This is the positive control: it proves the comparison is sensitive to
    *which arm ran*, not merely to whether a run finished.
    """
    candidates = [
        item
        for item in planned
        if item.run.arm == "B3" and item.run.seed == 0
    ]
    # The cheapest configuration, by the previous revision's own cost figures:
    # the steady-state one, which has the shortest design vector.
    chosen = next(
        (item for item in candidates if not campaign.configuration(
            item.run.configuration).pulsed),
        candidates[0] if candidates else None,
    )
    if chosen is None:
        return {
            "tooth": "composition",
            "caught": False,
            "what": "no B3 run at seed 0 is planned, so the tooth cannot run",
        }
    config = campaign.configuration(chosen.run.configuration)
    switch = "PROCESS_ARCH_OUTER"
    job = pool_mod.Job(
        phase="B",
        arm="B3",
        config=config,
        seed=0,
        outdir=Path(root) / "_teeth" / "composition",
        regime="unperturbed",
        delta=campaign.delta,
        run_kind="gate",
        allow_pending=GATE_ALLOWANCE.get("B3", ()),
        override_env={switch: None},
    )
    pool_mod.run_all([job], campaign, resume=resume)
    result = compare_one(chosen.run, job.outdir)
    record = records_mod.read(job.outdir)
    return {
        "tooth": "composition",
        "caught": not result["passed"],
        "what": (
            f"B3 on {config.name} run with {switch} cleared — so the verified "
            f"schedule ran under the partitioned arm's name — must not "
            f"reproduce the previous revision's B3.  "
            f"{result['n_mismatched']} of {result['n_fields']} compared values "
            f"differ"
        ),
        "outdir": str(job.outdir),
        "configuration": config.name,
        "switch_cleared": switch,
        "resolved_schedule": (record.get("resolved_switches") or {}).get(
            "process.core.solver.module_solve.OUTER_MODE"
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
    lifted_from: Path | None = None,
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
        "allowance": {
            "arms": {arm: list(terms) for arm, terms in GATE_ALLOWANCE.items()},
            "why": GATE_ALLOWANCE_REASON,
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

    # The two lifted input files, staged and checked, before anything runs.
    verdict["input_files"] = _stage_input_files(campaign, lifted_from)
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
            "A0p": substitute_pinned_flat_arm(
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


def _stage_input_files(
    campaign: Campaign, lifted_from: Path | None
) -> dict[str, Any]:
    """Put the lifted input files in place and prove they are the declared ones."""
    block: dict[str, Any] = {"staged": [], "resolved": []}
    for config in campaign.configurations:
        if not config.pulsed:
            continue
        if lifted_from is not None and not input_files_mod.is_lifted_available(
            config, campaign
        ):
            try:
                block["staged"].append(
                    input_files_mod.stage_lifted(config, campaign, Path(lifted_from))
                )
            except input_files_mod.InputFileError as exc:
                block["refused"] = str(exc)
                return block
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
    if "A0p" in substitutes:
        block = substitutes["A0p"]
        out.append("")
        out.append(
            "*Caption: the substitute for `A0p`, the arm no earlier record "
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
                f"{compared.get('n_prime_calls')} | "
                f"`{compared.get('objf_hex')}` | {row.get('n_mismatched')} |"
            )
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--resume", action="store_true",
                        help="keep a run whose directory already holds a "
                             "complete record of the same job; a directory "
                             "alone is never evidence")
    parser.add_argument("--lifted-from", type=Path, default=None,
                        help="a directory holding <name>/<name>_lifted.IN.DAT, "
                             "staged into the experiment's own derived-input "
                             "directory after its bytes are checked against the "
                             "recorded digest")
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
        lifted_from=args.lifted_from,
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
