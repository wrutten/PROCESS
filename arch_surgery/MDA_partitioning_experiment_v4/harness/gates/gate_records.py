#!/usr/bin/env python
"""Gate G7 — a record carries what it declares, in both phases, even when the run fails.

What the gate is about
----------------------
Every number this experiment publishes is read out of a run record.  The record
schema is declared as data in ``harness/core/records.py``: a list of fields, each
saying which phases carry it and whether it is there always or only when the run
finished.  A **completeness contract** refuses a record that is missing one, so
that a summary is never computed over records missing different fields — a
population nobody can state, which is this project's trap T11 in its purest
form.

The contract is only worth what its exercise is worth.  The dangerous record is
not the one from a run that went well; it is the one from a run that **did not
converge**, because that is where fields go missing and where the failure
forensics — the exit code, the iteration count, the retry-ladder rung, the
constraint residual vector and the active set — are the only evidence of what
happened.  So this gate makes a run fail *on purpose* and checks the record it
leaves behind.

How the failure is forced, and why the record can never be mistaken for a measurement
--------------------------------------------------------------------------------------
The harness's own lever: ``--force-maxcal`` caps the optimiser's iteration
budget, so the solver exhausts its whole retry ladder and exits unconverged.
The cap is written into the record as ``force_maxcal``, and **that stamp is the
guard**: every tally, every gate population and every measurement stage filters
records carrying it, because a budget-capped run is a demonstration and not a
measurement.  The gate says so in its own record too.

Both phases, and what "both phases" can mean here
--------------------------------------------------
The schema declares fields per phase, so completeness has to be shown per phase.
The optimisation phase gets the forced-unconverged run.  The evaluation phase
has **no optimiser to leave unconverged** — it runs exactly one ``call_models``
— so its record is checked on an ordinary smoke run, and that asymmetry is
stated here rather than papered over by pretending the two are the same test.
What the evaluation record does carry, and is checked for, is the same schema's
evaluation-phase field list, both convergence rulers, and an explicit
"not applicable" for the per-attempt accounting rather than a missing key.

Criterion inherited, and its source
-----------------------------------
Experiment plan §3.9's G7 row: *"a forced-unconverged smoke run carries every
declared field; a record with a field missing is refused by the tally"*, teeth
*"5/5 field teeth"*.  The previous revision's five fields are
``n_solver_iterations``, ``ifail``, the ladder stage, the constraint residual
vector and the active set; its sixth tooth deletes the whole forensics block.
All six are restated here, and two more are added for the two contracts that
did not exist when that gate was written: the convergence ruler pair, and the
per-attempt cost decomposition.

Written by task **A52 (harness-gates)**.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from . import gates as gates_mod
from ..core import pool as pool_mod
from ..core import records as records_mod
from ..core.config import Campaign
from ..core.framework import Gate, GateError, Tooth

#: The iteration budget the forced run is capped at.  Two is enough for the
#: solver to exhaust its retry ladder and exit unconverged, and small enough
#: that the demonstration costs little.
FORCED_MAXCAL = 2

#: The arm the forced run uses: the reference arm, which sets no architecture
#: switch.  A completeness question is about the record, not about an
#: arrangement, so the arm with nothing composed is the right one.
FORCED_ARM = "BR"

#: The evaluation-phase arm, likewise the reference one.
EVALUATION_ARM = "AR"

#: The five fields the previous revision's gate named, by their paths in this
#: revision's schema.  A record missing any of them must be refused **by name**:
#: "something is missing" is not enough to act on.
FORENSICS_FIELDS: tuple[str, ...] = (
    "n_solver_iterations",
    "mfile.ifail",
    "exit_forensics.ladder_stage",
    "exit_forensics.constraint_residual_vector",
    "exit_forensics.active_set",
)

_HELD: dict[str, Any] = {}


def record_root(campaign: Campaign) -> Path:
    return Path(campaign.runs_dir) / gates_mod.GATES_SUBPATH / "record_completeness"


def fewest_variables_configuration(campaign: Campaign):
    """The configuration with the fewest iteration variables.

    Not :func:`harness.chain.cheapest_configuration`, which is *measured* cost
    in node calls over the records on disk; this is the declared size of the
    problem, and a gate that makes one forced run wants the small problem, not
    a measurement of it.

    Derived, not named: a gate that hard-coded a configuration would have to be
    edited when the configuration list changes, and the list is allowed to
    change by a recorded decision.
    """
    active = [
        config
        for config in campaign.configurations
        if FORCED_ARM not in config.skips and EVALUATION_ARM not in config.skips
    ]
    if not active:
        raise GateError(
            "no configuration has both reference arms active, so the "
            "completeness gate has nothing to run"
        )
    return min(active, key=lambda c: c.n_iteration_variables)


def _remove_path(document: dict[str, Any], path: str) -> dict[str, Any]:
    """A copy of *document* with one dotted path deleted."""
    copy = json.loads(json.dumps(document))
    parts = path.split(".")
    cursor: Any = copy
    for part in parts[:-1]:
        if not isinstance(cursor, dict) or part not in cursor:
            return copy
        cursor = cursor[part]
    if isinstance(cursor, dict):
        cursor.pop(parts[-1], None)
    return copy


def _at(record: Mapping[str, Any], path: str) -> Any:
    """A record's value at a dotted path, or None where the path is absent.

    An evaluation record has no ``mfile`` block at all — it runs no optimiser
    and writes no output file — and asking for one must read as "not there",
    not as an error.  Whether a field that *is* declared is present is the
    completeness contract's question, and this helper never answers it.
    """
    return records_mod.resolve_path(record, path) if records_mod.has_path(record, path) else None


def _refuses(call) -> tuple[bool, str]:
    """Did the contract refuse, and what did it say?"""
    try:
        call()
    except records_mod.RecordError as exc:
        return True, str(exc)[:220]
    except Exception as exc:  # noqa: BLE001 - the wrong refusal is still a failure
        return False, f"refused with {type(exc).__name__}, not a record refusal: {exc}"
    return False, "the contract accepted the doctored record"


def record_completeness_body(
    campaign: Campaign, *, resume: bool = False
) -> dict[str, Any]:
    """G7: the declared fields are there, and a missing one is refused."""
    config = fewest_variables_configuration(campaign)
    root = record_root(campaign)
    forced = pool_mod.Job(
        phase="B",
        arm=FORCED_ARM,
        config=config,
        seed=0,
        outdir=root / config.name / "forced_unconverged",
        regime="unperturbed",
        delta=None,
        run_kind="smoke",
        force_maxcal=FORCED_MAXCAL,
    )
    evaluation = pool_mod.Job(
        phase="A",
        arm=EVALUATION_ARM,
        config=config,
        seed=0,
        outdir=root / config.name / "evaluation",
        regime="unperturbed",
        delta=None,
        run_kind="smoke",
    )
    pool_mod.run_all([forced, evaluation], campaign, resume=resume)

    rows: list[dict[str, Any]] = []
    passed = True
    n_compared = 0
    n_mismatched = 0
    for label, job, phase in (
        ("optimisation (forced unconverged)", forced, "B"),
        ("evaluation (smoke)", evaluation, "A"),
    ):
        record = records_mod.read(job.outdir)
        declared = records_mod.declared_field_names(phase)
        missing = records_mod.missing_fields(record)
        forensics = record.get("exit_forensics") or {}
        row: dict[str, Any] = {
            "label": label,
            "phase": phase,
            "configuration": config.name,
            "arm": job.arm,
            "status": record.get("status"),
            "failure_class": record.get("failure_class"),
            "force_maxcal": record.get("force_maxcal"),
            "ifail": _at(record, "mfile.ifail"),
            "n_declared_fields": len(declared),
            "n_missing_fields": len(missing),
            "missing_fields": missing,
            "exit_audit_rulers": sorted(
                name
                for name in records_mod.AUDIT_RULERS
                if isinstance((record.get("exit_audit") or {}).get(name), dict)
            ),
            "n_attempts": forensics.get("n_attempts"),
            "attempts_node_calls_available": record.get(
                "attempts_node_calls_available"
            ),
            "attempt_accounting": record.get("attempt_accounting"),
            "record": str(Path(job.outdir) / "metrics.json"),
        }
        checks = {
            "the_run_produced_a_record": bool(record),
            "every_declared_field_is_carried": not missing,
            "both_convergence_rulers_are_present": (
                row["exit_audit_rulers"] == sorted(records_mod.AUDIT_RULERS)
            ),
        }
        if phase == "B":
            checks["the_run_did_not_converge"] = (
                row["ifail"] is not None and row["ifail"] != 1
            )
            checks["the_forced_cap_is_stamped"] = (
                record.get("force_maxcal") == FORCED_MAXCAL
            )
            checks["the_five_forensics_fields_are_non_null"] = all(
                _at(record, path) is not None for path in FORENSICS_FIELDS
            )
            summed, why = _refuses(
                lambda: records_mod.assert_attempt_summation(record, where=label)
            )
            checks["the_per_attempt_costs_add_up"] = not summed
            row["attempt_summation"] = "accepted" if not summed else why
        else:
            checks["the_per_attempt_accounting_says_not_applicable"] = (
                row["n_attempts"] == 0
                and row["attempts_node_calls_available"] is not None
            )
        row["checks"] = checks
        row["passed"] = all(checks.values())
        n_compared += len(declared)
        n_mismatched += len(missing)
        passed = passed and row["passed"]
        rows.append(row)
        _HELD[phase] = record

    _HELD["rows"] = rows
    return {
        "passed": passed,
        "criterion": (
            "a forced-unconverged optimisation run and an evaluation run each "
            "carry every field the schema declares for their phase, both "
            "convergence rulers included; and the completeness contract "
            "refuses a record with a field missing, naming the field"
        ),
        "criterion_source": (
            "the experiment plan §3.9's G7 row, restated here, with two "
            "contracts added that did not exist when it was written: the "
            "ruler pair and the per-attempt cost decomposition"
        ),
        "population": (
            f"2 runs on {config.name} (the configuration with the fewest "
            f"iteration variables, derived); "
            f"{rows[0]['n_declared_fields']} declared field(s) in the "
            f"optimisation phase and {rows[1]['n_declared_fields']} in the "
            f"evaluation phase"
        ),
        "n_compared": n_compared,
        "n_mismatched": n_mismatched,
        "the_stamp": (
            f"the forced run carries force_maxcal={FORCED_MAXCAL}.  It is a "
            f"demonstration and never a measurement: every tally and every "
            f"gate population filters records carrying that stamp"
        ),
        "phases_are_not_symmetric": (
            "the evaluation phase has no optimiser to leave unconverged — it "
            "runs exactly one call_models — so its record is checked on an "
            "ordinary smoke run.  What it must carry is its own phase's "
            "declared fields, both rulers, and an explicit 'no attempts' "
            "rather than a missing key"
        ),
        "rows": rows,
    }


# --------------------------------------------------------------------------
# the teeth
# --------------------------------------------------------------------------


def _teeth(campaign: Campaign) -> tuple[Tooth, ...]:
    def field_tooth(path: str):
        def look() -> tuple[bool, str]:
            record = _HELD.get("B")
            if record is None:
                return False, "the gate made no optimisation record to doctor"
            doctored = _remove_path(record, path)
            refused, why = _refuses(
                lambda: records_mod.assert_complete(doctored, where="a tooth")
            )
            names = path.split(".")[-1] in why or path in why
            return refused and names, (
                f"{path} deleted from a copy of the forced-unconverged record: "
                f"{'refused' if refused else 'ACCEPTED'}"
                + (f", naming the field — {why}" if refused else "")
            )

        return look

    def whole_block() -> tuple[bool, str]:
        record = _HELD.get("B")
        if record is None:
            return False, "the gate made no optimisation record"
        doctored = _remove_path(record, "exit_forensics")
        refused, why = _refuses(
            lambda: records_mod.assert_complete(doctored, where="a tooth")
        )
        return refused, (
            "the whole exit_forensics block deleted from a copy of the "
            f"forced-unconverged record: {'refused' if refused else 'ACCEPTED'}"
            + (f" — {why}" if refused else "")
        )

    def one_ruler() -> tuple[bool, str]:
        record = _HELD.get("B")
        if record is None:
            return False, "the gate made no optimisation record"
        doctored = _remove_path(record, "exit_audit.mixed")
        refused, why = _refuses(
            lambda: records_mod.assert_both_rulers(doctored, where="a tooth")
        )
        return refused, (
            "the second convergence ruler's block deleted from a copy of the "
            f"record: {'refused' if refused else 'ACCEPTED'}"
            + (f" — {why}" if refused else "")
        )

    def attempts_that_do_not_add_up() -> tuple[bool, str]:
        record = _HELD.get("B")
        if record is None:
            return False, "the gate made no optimisation record"
        doctored = json.loads(json.dumps(record))
        doctored["attempts"] = [
            {"attempt": 1, "node_calls_solve_phase": 400, "sweeps": 1},
            {"attempt": 2, "node_calls_solve_phase": 550, "sweeps": 1},
        ]
        doctored["attempts_node_calls_available"] = True
        doctored["node_calls_solve_phase"] = 1000
        refused, why = _refuses(
            lambda: records_mod.assert_attempt_summation(doctored, where="a tooth")
        )
        return refused, (
            "per-attempt node calls of 400 + 550 against a run total of 1000 "
            f"in a copy of the record: {'refused' if refused else 'ACCEPTED'}"
            + (f" — {why}" if refused else "")
        )

    def a_stale_run_is_re_made_without_resume() -> tuple[bool, str]:
        """``--resume`` must reach the **runs**, not only the comparison.

        The defect this exists for was live and invisible: every gate body
        hard-coded ``resume=True``, so a verdict computed after a change read
        runs made before it while the option that was supposed to control that
        reached nothing but the reproduction gate.  A gate that compares fresh
        records to stale runs reports a zero over a population that is not the
        one it names.

        The tooth stamps a run's record with a commit that is not this one and
        then asks for the run twice: with ``--resume`` the stamp must survive,
        because resume keeps a complete record of the same job; without it the
        stamp must be gone, because the run was re-made.
        """
        config = fewest_variables_configuration(campaign)
        directory = record_root(campaign) / config.name / "evaluation"
        path = directory / "metrics.json"
        if not path.exists():
            return False, "the gate made no evaluation run to stale"
        job = pool_mod.Job(
            phase="A",
            arm=EVALUATION_ARM,
            config=config,
            seed=0,
            outdir=directory,
            regime="unperturbed",
            delta=None,
            run_kind="smoke",
        )
        stale = "0000000000000000000000000000000000000000"
        record = json.loads(path.read_text())
        record["tree_git_head"] = stale
        path.write_text(json.dumps(record))
        pool_mod.run_all([job], campaign, resume=True)
        kept = json.loads(path.read_text()).get("tree_git_head") == stale
        pool_mod.run_all([job], campaign, resume=False)
        re_made = json.loads(path.read_text()).get("tree_git_head") != stale
        return kept and re_made, (
            f"one run's record stamped with a commit that is not this tree's: "
            f"asked for again with resume it was "
            f"{'KEPT' if kept else 'RE-MADE'} (it must be kept), and without "
            f"resume it was {'RE-MADE' if re_made else 'KEPT'} (it must be "
            f"re-made).  So --resume reaches the runs, not only the comparison"
        )

    teeth = (
        Tooth(
            name="a stale run is re-made without --resume",
            what=(
                "one run's record stamped with a commit that is not this "
                "tree's, then asked for again with and without resume"
            ),
            must="be kept under --resume and re-made without it",
            check=a_stale_run_is_re_made_without_resume,
        ),
    ) + tuple(
        Tooth(
            name=f"the field {path} removed",
            what="one declared field deleted from a copy of the record",
            must="be refused by the completeness contract, naming the field",
            check=field_tooth(path),
        )
        for path in FORENSICS_FIELDS
    )
    return teeth + (
        Tooth(
            name="the whole forensics block removed",
            what="exit_forensics deleted from a copy of the record",
            must="be refused",
            check=whole_block,
        ),
        Tooth(
            name="one convergence ruler and not both",
            what="the second ruler's audit block deleted from a copy",
            must=(
                "be refused: the mixed ruler reads lower wherever its "
                "denominator binds, so a table built from records with one "
                "column here and two there reports a change of ruler as a "
                "change of accuracy"
            ),
            check=one_ruler,
        ),
        Tooth(
            name="per-attempt costs that do not sum to the run total",
            what="400 + 550 against a run total of 1000",
            must="be refused",
            check=attempts_that_do_not_add_up,
        ),
    )


def record_completeness_gate(campaign: Campaign) -> Gate:
    return Gate(
        name="record_completeness",
        plan_name="G7",
        needs_runs=True,
        binds="the declared pairing and the failure forensics, in both phases",
        what_it_proves=(
            "a run that did not converge still carries every field its phase "
            "declares — the exit code, the iteration count, the ladder rung, "
            "the constraint residual vector, the active set, both convergence "
            "rulers and the per-attempt costs — and a record with one missing "
            "is refused by name rather than summarised over"
        ),
        body=lambda *, resume=False: record_completeness_body(campaign, resume=resume),
        teeth=_teeth(campaign),
    )
