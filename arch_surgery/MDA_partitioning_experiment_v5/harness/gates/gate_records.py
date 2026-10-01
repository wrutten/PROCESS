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

import dataclasses
import json
from pathlib import Path
from typing import Any, Mapping

from . import gates as gates_mod
from ..core import pool as pool_mod
from ..core import records as records_mod
from ..core.config import TAU_RULES, Campaign
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

#: The wall-clock fields the contract owes on a record made with the timers
#: on (DR12, A101 (v5-timers-and-once)): each removed from a copy of the
#: forced record, which was made with them on, must be refused by name.
TIMER_FIELDS: tuple[str, ...] = ("timers", "launcher", "campaign_timers")

_HELD: dict[str, Any] = {}


def record_root(campaign: Campaign) -> Path:
    """Where G7's verdict goes.  Its two runs are shared-pool jobs."""
    return Path(campaign.runs_dir) / gates_mod.GATES_SUBPATH / "record_completeness"


def forced_job(campaign: Campaign) -> pool_mod.Job:
    """The optimisation forced to stop unconverged: ``force_maxcal`` is in
    its identity, so it is never mistaken for a converged run of the arm."""
    return pool_mod.Job(
        phase="B",
        arm=FORCED_ARM,
        config=fewest_variables_configuration(campaign),
        seed=0,
        regime="unperturbed",
        delta=None,
        run_kind="smoke",
        force_maxcal=FORCED_MAXCAL,
        # DR12 (A101): with the timers on, so the record owes the timer
        # fields and the contract's tooth on them can bite.
        timers=True,
    )


def evaluation_job(campaign: Campaign) -> pool_mod.Job:
    """The one smoke evaluation whose record the field list is checked on.

    A ``smoke`` job, so it shares no record with any gate's ``A0`` evaluation
    of the same configuration: the run kind is in the identity, and the tooth
    below stales and re-makes this record, which must never touch a gate's.
    """
    return pool_mod.Job(
        phase="A",
        arm=EVALUATION_ARM,
        config=fewest_variables_configuration(campaign),
        seed=0,
        regime="unperturbed",
        delta=None,
        run_kind="smoke",
        timers=True,
    )


#: The fields a record made under a named tolerance rule owes (task A105
#: (v5-resume-fixes-and-tau-rule)): each removed from a copy of the
#: rule-stamped record must be refused by name.
TAU_RULE_FIELDS: tuple[str, ...] = ("campaign_tau_rule", "tau_rule_derivation")

#: The flat control: the arm whose loop the rule's τ reaches (the reference
#: arm composes no tolerance).
RULE_ARM = "A0"


def rule_campaign(campaign: Campaign) -> Campaign:
    """The campaign the rule-stamped run is made under: this one's rule, or
    the first declared rule where this campaign has none."""
    return dataclasses.replace(
        campaign, tau=None, tau_rule=campaign.tau_rule or TAU_RULES[0].name
    )


def rule_evaluation_job(campaign: Campaign) -> pool_mod.Job:
    """One smoke evaluation of the flat control under a named tolerance rule:
    the record that shows a rule's stamps are carried and owed.  The rule's
    name is in its identity, so it shares no record with the plain smoke
    evaluation."""
    return pool_mod.Job(
        phase="A",
        arm=RULE_ARM,
        config=fewest_variables_configuration(campaign),
        seed=0,
        regime="unperturbed",
        delta=None,
        run_kind="smoke",
        timers=True,
    )


def jobs_read(campaign: Campaign) -> list[pool_mod.Job]:
    return [forced_job(campaign), evaluation_job(campaign)]


def job_rows(campaign: Campaign) -> list[dict[str, Any]]:
    """The gate's job listing: its two plain runs under this campaign and the
    rule-stamped one under :func:`rule_campaign`."""
    ruled = rule_campaign(campaign)
    return gates_mod.job_rows(jobs_read, campaign) + pool_mod.job_listing(
        [rule_evaluation_job(ruled)], ruled
    )


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
    forced = forced_job(campaign)
    evaluation = evaluation_job(campaign)
    pool_mod.run_all([forced, evaluation], campaign, resume=resume)
    ruled = rule_campaign(campaign)
    ruled_job = rule_evaluation_job(ruled)
    pool_mod.run_all([ruled_job], ruled, resume=resume)

    rows: list[dict[str, Any]] = []
    passed = True
    n_compared = 0
    n_mismatched = 0
    for label, job, phase in (
        ("optimisation (forced unconverged)", forced, "B"),
        ("evaluation (smoke)", evaluation, "A"),
        (f"evaluation under tolerance rule {ruled.tau_rule} (smoke)", ruled_job, "A"),
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
            "the_timers_were_composed_and_harvested": (
                bool(record.get("campaign_timers"))
                and isinstance(record.get("timers"), dict)
                and bool((record.get("timers") or {}).get("enabled"))
                and isinstance(record.get("launcher"), dict)
            ),
            "every_declared_convergence_ruler_is_present": (
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
        if job is ruled_job:
            derivation = record.get("tau_rule_derivation") or {}
            row["campaign_tau_rule"] = record.get("campaign_tau_rule")
            row["campaign_tau"] = record.get("campaign_tau")
            row["tau_rule_derivation"] = derivation
            checks["the_rule_is_stamped_and_its_tau_composed"] = (
                record.get("campaign_tau_rule") == ruled.tau_rule
                and record.get("campaign_tau") == ruled.tau_for(config)
                and derivation.get("tau") == ruled.tau_for(config)
                and (record.get("job_identity") or {}).get("tau_rule") == ruled.tau_rule
            )
            _HELD["rule"] = record
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
            f"3 runs on {config.name} (the configuration with the fewest "
            f"iteration variables, derived), the third under tolerance rule "
            f"{ruled.tau_rule} at tau {ruled.tau_for(config)!r}; "
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
            "declared fields, every declared ruler, and an explicit 'no attempts' "
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

    def rule_field_tooth(path: str):
        def look() -> tuple[bool, str]:
            record = _HELD.get("rule")
            if record is None:
                return False, "the gate made no rule-stamped record to doctor"
            doctored = _remove_path(record, path)
            refused, why = _refuses(
                lambda: records_mod.assert_complete(doctored, where="a tooth")
            )
            return refused and path in why, (
                f"{path} deleted from a copy of the rule-stamped record: "
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

    def no_ruler() -> tuple[bool, str]:
        record = _HELD.get("B")
        if record is None:
            return False, "the gate made no optimisation record"
        doctored = record
        for ruler in records_mod.AUDIT_RULERS:
            doctored = _remove_path(doctored, f"exit_audit.{ruler}")
        refused, why = _refuses(
            lambda: records_mod.assert_audit_ruler(doctored, where="a tooth")
        )
        return refused, (
            "every convergence ruler's block deleted from a copy of the "
            f"record ({list(records_mod.AUDIT_RULERS)}): "
            f"{'refused' if refused else 'ACCEPTED'}"
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
        job = evaluation_job(campaign)
        directory = pool_mod.directory_for(job, campaign)
        path = directory / "metrics.json"
        if not path.exists():
            return False, "the gate made no evaluation run to stale"
        stale = "0000000000000000000000000000000000000000"
        record = json.loads(path.read_text())
        record["tree_git_head"] = stale
        path.write_text(json.dumps(record))
        pool_mod.run_all([job], campaign, resume=True)
        kept = json.loads(path.read_text()).get("tree_git_head") == stale
        # ``fresh``: this process made the job minutes ago and the pool would
        # otherwise keep it as this press's copy; the tooth is about what
        # happens without resume, so it asks for a fresh run explicitly.
        pool_mod.run_all([job], campaign, resume=False, fresh=True)
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
        for path in FORENSICS_FIELDS + TIMER_FIELDS
    ) + tuple(
        Tooth(
            name=f"the tolerance-rule field {path} removed",
            what="one field a rule-stamped record owes deleted from a copy of it",
            must="be refused by the completeness contract, naming the field",
            check=rule_field_tooth(path),
        )
        for path in TAU_RULE_FIELDS
    )
    return teeth + (
        Tooth(
            name="the whole forensics block removed",
            what="exit_forensics deleted from a copy of the record",
            must="be refused",
            check=whole_block,
        ),
        Tooth(
            name="an exit audit naming no ruler",
            what="every declared ruler's audit block deleted from a copy",
            must=(
                "be refused: an achieved-accuracy figure whose denominator "
                "is not recorded cannot be compared with one whose is"
            ),
            check=no_ruler,
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
        jobs=lambda: job_rows(campaign),
        teeth=_teeth(campaign),
    )
