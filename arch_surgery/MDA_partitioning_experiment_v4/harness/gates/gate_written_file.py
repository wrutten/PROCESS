#!/usr/bin/env python
"""Gate ``written_file_gap`` — how far the state PROCESS writes out is from a fixed point of its own solve.

What the gate is about
----------------------
PROCESS's output pass changes the state it writes.  On the TF-coil models it
raises the stress mesh from 100 to 500 radial layers when ``output=True``, so
the output file's ``tfcoil.insstrain`` is the 500-layer value while the state
the optimiser accepted carries the 100-layer one (task A61
(insstrain-diagnosis)).  Since ruling D25 the experiment's exit audit at its
**declared** position — the entry to ``write_output_files`` — puts the
solve-phase data structure back before its sweep and reads 0 components above
τ in every arm.  The same instrument taken at ``after_run`` — the solve-phase
settings put back, the coupling state left **as PROCESS wrote it out** — reads
6.99e-03 on ``large_tokamak_nof`` and 7.02e-03 on ``low_aspect_ratio_DEMO``,
argmax ``tfcoil.insstrain``, on the reference arm in gate GR's records (task
A62 (exit-audit-restore), §5.3).  That number is the distance between the
written file and a fixed point of the solve's own map: issue **I-21**'s handle.

What had not been measured is whether the **one-call output path** —
``finalise_once``, which arms ``B1`` and ``B3`` take *as the campaign composes
them* — writes the same gap.  GR's ``B1``/``B3`` records cannot say: that gate
runs them with the output-time loop switched back on, so their ``after_run``
numbers are numbers of the loop path.  This gate makes the six runs that
settle it: at seed 0, unperturbed, on the two pulsed configurations, the arms
``BR`` (the loop, ``mda_output``), ``B1`` and ``B3`` (one call,
``finalise_once``), each composed **exactly as the campaign composes them** —
no override except the audit position — and each asked for
``--audit-position after_run``.

What it publishes, and what it does not accept on
-------------------------------------------------
Per run: the ``after_run`` residual — maximum, argmax, count above τ, on the
restricted and the whole-state statistic and on both rulers — the declared-
position residual for the same arm, configuration and seed from gate G9's
record where that record exists (a run record carries one audit, at one
position, so the same run cannot carry both), ``output_path`` and
``output_loop_sweeps`` as the driver stamped them, and the instrument stamp.

**This gate does not pass or fail on the size of the gap.**  The gap is a
property of PROCESS's write pass; the user confirmed on 2026-09-14 (ruling D25,
words in the row) that the experiment measures before the output pass and does
not rewrite PROCESS to close it.  It is published here as a finding.  The gate
fails only if a run did not finish, its composition is wrong (the output path
the driver resolved is not the arm's matrix cell, or the one-call arms ran an
output-time sweep), the audit position asked for was not honoured or was not
stamped as this gate's override, or the residual is not reported with its
argmax named.

``st_regression`` is excluded, with the reason in the record: gate GR's
``after_run`` audit already reads exactly ``0x0.0p+0`` there on the loop path
(A62 §5.3); the component the gap sits on is ``None`` on that configuration
from the first sweep (A61 §3), so there is no gap to measure on either path;
and ``B1`` composes to ``B0`` there and is skipped by the configuration's own
recorded reason.  The two pulsed configurations are selected by their
``pulsed`` flag, never by name.

The audit position's declared callers
-------------------------------------
``after_run`` is a position with **declared callers**
(``records.AUDIT_POSITION_AFTER_RUN_CALLERS``); this gate is one, names itself
on every job it makes, and the run pool refuses the position for any caller not
in that table and for every campaign run.  The refusal is one of this gate's
teeth and one of the ``run_path`` self-check's.

Task **A67 (written-file-gap)**, 2026-09-14.  Gate G9 (``output_path``) is the
model this gate is built on: same arms at the declared position, whose records
this gate reads for the beside-column and declares in ``reads_from``.
"""

from __future__ import annotations

import copy
import datetime as _dt
import json
from pathlib import Path
from typing import Any, Mapping

from ..core import pool as pool_mod
from ..core import records as records_mod
from ..core.config import Campaign, Config
from ..core.framework import GATES_SUBPATH, Gate, GateError, Tooth, git_head
from ..experiment import arms as arms_mod

GATE_NAME = "written_file_gap"

#: Where every run of this gate audits.  The gate exists to read this position.
AUDIT_POSITION = records_mod.AUDIT_POSITION_AFTER_RUN

#: The arms, in the order the plan's matrix lists them: the loop path, then the
#: two one-call arms.  Every one is composed from the matrix; the only thing
#: this gate sets is the audit position.
ARMS: tuple[str, ...] = ("BR", "B1", "B3")

#: The matrix row that decides which output path an arm takes, and what the
#: driver must stamp for each of its cells.
MATRIX_ROW = "output-time loop (MDA_Output)"
EXPECTED_OUTPUT_PATH: dict[str, str] = {"upstream": "mda_output", "none": "finalise_once"}

#: Why the steady-state configuration is left out, recorded in the verdict.
STEADY_STATE_EXCLUSION_REASON = (
    "gate GR's after_run audit on the loop path reads exactly 0x0.0p+0 on this "
    "configuration (A62 §5.3); the component the gap sits on, "
    "tfcoil.insstrain, is None there from the first sweep and is tested by "
    "exact equality (A61 §3), so there is no gap to measure on either output "
    "path; and B1 composes to B0 there and is skipped by the configuration's "
    "own recorded reason"
)

#: The rulers the audit publishes, both, always.
RULERS: tuple[str, ...] = ("frozen", "mixed")


def root(campaign: Campaign) -> Path:
    return Path(campaign.runs_dir) / GATES_SUBPATH / GATE_NAME


def run_directory(campaign: Campaign, configuration: str, arm: str) -> Path:
    return root(campaign) / "runs" / configuration / arm / pool_mod.seed_directory(0)


def output_path_record_directory(campaign: Campaign, configuration: str, arm: str) -> Path:
    """Gate G9's run of the same arm at seed 0, at the declared position."""
    return Path(campaign.runs_dir) / GATES_SUBPATH / "output_path" / "runs" / configuration / arm


def configurations(campaign: Campaign) -> tuple[list[Config], dict[str, str]]:
    """The pulsed configurations, and the excluded ones with their reason."""
    kept = [config for config in campaign.configurations if config.pulsed]
    excluded = {
        config.name: STEADY_STATE_EXCLUSION_REASON
        for config in campaign.configurations
        if not config.pulsed
    }
    return kept, excluded


def jobs(campaign: Campaign) -> list[pool_mod.Job]:
    """Six jobs: three arms on the two pulsed configurations, seed 0, unperturbed.

    Composed by the pool from the arm and nothing else; a skipped arm would be
    left out by the configuration's own recorded reason, never by a condition
    written here.
    """
    kept, _ = configurations(campaign)
    planned: list[pool_mod.Job] = []
    for config in kept:
        active = arms_mod.active_arms(config, "B")
        for arm in ARMS:
            if arm not in active:
                continue
            planned.append(
                pool_mod.Job(
                    phase="B",
                    arm=arm,
                    config=config,
                    seed=0,
                    outdir=run_directory(campaign, config.name, arm),
                    regime="unperturbed",
                    delta=campaign.delta,
                    run_kind="gate",
                    audit_position=AUDIT_POSITION,
                    audit_position_caller=GATE_NAME,
                )
            )
    return planned


def capture(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    """Make the runs and write where they went.  Nothing is compared here."""
    planned = jobs(campaign)
    results = pool_mod.run_all(planned, campaign, resume=resume)
    _, excluded = configurations(campaign)
    manifest = {
        "captured": _dt.datetime.now().isoformat(timespec="seconds"),
        "tree_git_head": git_head(),
        "n_runs": len(planned),
        "audit_position_override": {
            "position": AUDIT_POSITION,
            "caller": GATE_NAME,
            "why": records_mod.AUDIT_POSITION_AFTER_RUN_CALLERS[GATE_NAME],
            "declared_callers": sorted(records_mod.AUDIT_POSITION_AFTER_RUN_CALLERS),
        },
        "excluded_configurations": excluded,
        "runs": [
            {
                "configuration": job.config.name,
                "arm": job.arm,
                "outdir": str(job.outdir),
                "status": (results[i] or {}).get("status") if isinstance(results, list) else None,
            }
            for i, job in enumerate(planned)
        ],
    }
    path = root(campaign) / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    manifest["manifest"] = str(path)
    return manifest


# --------------------------------------------------------------------------
# reading one run
# --------------------------------------------------------------------------


def _read(directory: Path, name: str, *, key: str) -> dict[str, Any]:
    path = Path(directory) / name
    if not path.exists():
        raise GateError(
            f"{GATE_NAME} has no {name} for {key}: {path} is not there.  A gate "
            f"that cannot find a run it planned must refuse, never skip -- a "
            f"check with no population is not a check (trap T11)."
        )
    return json.loads(path.read_text())


def residual_summary(exit_audit: Mapping[str, Any]) -> dict[str, Any]:
    """The audit's residual on both rulers, whole-state and restricted.

    Read from the record's own summary blocks, which the child derived from the
    residual vector it wrote beside the record; nothing is recomputed here.
    ``skipped`` or ``refused`` audits are returned as such, not as zeros.
    """
    if not exit_audit or exit_audit.get("skipped") or exit_audit.get("refused"):
        return {
            "taken": False,
            "why": exit_audit.get("skipped") or exit_audit.get("refused") or "no exit_audit block",
        }
    out: dict[str, Any] = {"taken": True, "n_components": exit_audit.get("n_components")}
    for ruler in RULERS:
        block = exit_audit.get(ruler) or {}
        brief = block.get("brief") or {}
        restricted = block.get("restricted") or {}
        out[ruler] = {
            "tau": block.get("tau"),
            "whole_state": {
                "max": brief.get("max"),
                "max_hex": block.get("residual_max_hex"),
                "argmax": brief.get("argmax"),
                "n_above_tau": brief.get("n_above"),
                "n_tested": (block.get("detail") or {}).get("n_continuous_tested"),
            },
            "restricted": {
                "max": restricted.get("max"),
                "max_hex": restricted.get("max_hex"),
                "argmax": restricted.get("argmax"),
                "n_above_tau": restricted.get("n_above"),
                "n_kept": restricted.get("n_kept"),
                "n_excluded": restricted.get("n_excluded"),
            },
        }
    return out


def instrument_stamp(exit_audit: Mapping[str, Any]) -> dict[str, Any]:
    instrument = (exit_audit or {}).get("instrument") or {}
    return {
        "restores": instrument.get("restores"),
        "audit_position": instrument.get("audit_position"),
        "snapshot_position": instrument.get("snapshot_position"),
        "n_restored": instrument.get("n_restored"),
        "n_not_restorable": instrument.get("n_not_restorable"),
        "not_restorable": instrument.get("not_restorable"),
        "held_back_by_rule": instrument.get("held_back_by_rule"),
        "n_differing_inside_the_coupling_state": instrument.get(
            "n_differing_inside_the_coupling_state"
        ),
    }


def evaluate_run(
    record: Mapping[str, Any],
    command: Mapping[str, Any],
    *,
    arm: str,
    key: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """The checks on one run, and the row the verdict publishes for it.

    One function for the gate and for its teeth, so a tooth that doctors a copy
    of a record is judged by exactly the code that judges the run.  **No check
    reads the size of the residual.**
    """
    entry = arms_mod.ARMS[arm]
    cell = arms_mod.matrix_cell(entry, MATRIX_ROW)
    expected_path = EXPECTED_OUTPUT_PATH.get(cell)
    exit_audit = record.get("exit_audit") or {}
    residual = residual_summary(exit_audit)
    checks: list[dict[str, Any]] = []

    # (1) the run finished, and it is the arm the matrix describes
    checks.append(
        {
            "check": "(1a) the run finished",
            "passed": record.get("status") == "ok",
            "detail": f"status {record.get('status')!r}, failure class {record.get('failure_class')!r}",
        }
    )
    checks.append(
        {
            "check": f"(1b) the output path the driver resolved is the arm's matrix cell ({cell} -> {expected_path})",
            "passed": expected_path is not None and record.get("output_path") == expected_path,
            "detail": f"output_path {record.get('output_path')!r}",
        }
    )
    sweeps = record.get("output_loop_sweeps")
    if expected_path == "finalise_once":
        checks.append(
            {
                "check": "(1c) the one-call path ran no output-time sweep",
                "passed": sweeps == 0,
                "detail": f"output_loop_sweeps = {sweeps!r}",
            }
        )
    else:
        checks.append(
            {
                "check": "(1c) the loop path ran at least one output-time sweep",
                "passed": isinstance(sweeps, int) and sweeps >= 1,
                "detail": f"output_loop_sweeps = {sweeps!r}",
            }
        )
    checks.append(
        {
            "check": "(1d) no switch override rode into the run: composed from the matrix alone",
            "passed": not record.get("reproduction_overrides") and not command.get("override_env"),
            "detail": (
                f"reproduction_overrides {record.get('reproduction_overrides')!r}, "
                f"override_env {command.get('override_env')!r}"
            ),
        }
    )

    # (2) the audit position was honoured and stamped as this gate's override
    checks.append(
        {
            "check": f"(2a) the audit was taken at {AUDIT_POSITION}",
            "passed": (
                record.get("audit_position") == AUDIT_POSITION
                and exit_audit.get("audit_position") == AUDIT_POSITION
                and record.get("audit_position") != record.get("audit_position_declared")
            ),
            "detail": (
                f"record {record.get('audit_position')!r}, audit block "
                f"{exit_audit.get('audit_position')!r}, declared "
                f"{record.get('audit_position_declared')!r}"
            ),
        }
    )
    checks.append(
        {
            "check": f"(2b) the position was asked for by this gate, stamped beside the record ({GATE_NAME})",
            "passed": (
                command.get("audit_position") == AUDIT_POSITION
                and command.get("audit_position_caller") == GATE_NAME
            ),
            "detail": (
                f"command.json audit_position {command.get('audit_position')!r}, "
                f"audit_position_caller {command.get('audit_position_caller')!r}"
            ),
        }
    )

    # (3) the residual is reported -- never accepted on
    named = residual.get("taken") is True and all(
        isinstance(residual[ruler][stat]["argmax"], str)
        and residual[ruler][stat]["argmax"]
        and isinstance(residual[ruler][stat]["max_hex"], str)
        and isinstance(residual[ruler][stat]["n_above_tau"], int)
        for ruler in RULERS
        for stat in ("whole_state", "restricted")
    )
    checks.append(
        {
            "check": (
                "(3) the residual is reported on both rulers, whole-state and "
                "restricted, each with its maximum in hex, its argmax named and "
                "its count above tau -- its size is published, not gated"
            ),
            "passed": named,
            "detail": (
                "taken; every argmax named"
                if named
                else f"not reportable: {residual.get('why') or 'an argmax or a count is missing'}"
            ),
        }
    )

    row = {
        "arm": arm,
        "configuration": record.get("campaign_configuration"),
        "seed": record.get("campaign_seed"),
        "key": key,
        "matrix_cell": cell,
        "expected_output_path": expected_path,
        "output_path": record.get("output_path"),
        "output_loop_sweeps": sweeps,
        "output_path_entries": record.get("output_path_entries"),
        "status": record.get("status"),
        "audit_position": record.get("audit_position"),
        "audit_position_declared": record.get("audit_position_declared"),
        "audit_position_caller": command.get("audit_position_caller"),
        "reproduction_overrides": record.get("reproduction_overrides"),
        "after_run_residual": residual,
        "instrument": instrument_stamp(exit_audit),
        "exact_norm_objf": (record.get("exact") or {}).get("norm_objf"),
        "node_calls_solve_phase": record.get("node_calls_solve_phase"),
        "n_solver_iterations": record.get("n_solver_iterations"),
        "tree_git_head": record.get("tree_git_head"),
        "wall_s_context_only": record.get("wall_s"),
        "checks": checks,
        "passed": all(c["passed"] for c in checks),
    }
    return checks, row


def declared_position_beside(
    campaign: Campaign, configuration: str, arm: str, row: Mapping[str, Any]
) -> dict[str, Any]:
    """The declared-position residual of the same cell, from gate G9's record.

    A run record carries **one** audit at **one** position, so this gate's own
    records cannot carry the declared-position residual; the statement that
    they do not is made explicitly.  Gate G9 (``output_path``) runs the same
    arm on the same configuration at seed 0 at the declared position, composed
    from the matrix; where its record exists it is read, its commit named, and
    three solve-describing values are compared with this gate's run so a reader
    can see whether the two records are of the same solve.  Where it does not
    exist, that is said; nothing here fails.
    """
    directory = output_path_record_directory(campaign, configuration, arm)
    path = directory / "metrics.json"
    out: dict[str, Any] = {
        "in_this_gate's_record": False,
        "why_not": (
            "a run record carries one exit audit at one position; this run's "
            f"is at {AUDIT_POSITION}"
        ),
        "source": "gate output_path (G9), the same arm and configuration at seed 0, declared position",
        "record": str(path),
    }
    if not path.exists():
        out["available"] = False
        out["why"] = "gate output_path has no record for this cell in this tree"
        return out
    record = json.loads(path.read_text())
    audit = record.get("exit_audit") or {}
    out["available"] = True
    out["tree_git_head"] = record.get("tree_git_head")
    out["audit_position"] = record.get("audit_position")
    out["residual"] = residual_summary(audit)
    out["instrument"] = instrument_stamp(audit)
    same = {
        "exact.norm_objf": (
            (record.get("exact") or {}).get("norm_objf"),
            row.get("exact_norm_objf"),
        ),
        "node_calls_solve_phase": (
            record.get("node_calls_solve_phase"),
            row.get("node_calls_solve_phase"),
        ),
        "n_solver_iterations": (
            record.get("n_solver_iterations"),
            row.get("n_solver_iterations"),
        ),
    }
    out["same_solve_as_this_gate's_run"] = {
        "compared": list(same),
        "equal": [name for name, (a, b) in same.items() if a == b],
        "differing": {name: {"output_path_gate": a, "this_gate": b} for name, (a, b) in same.items() if a != b},
        "note": (
            "information, not a criterion: the two records are at different "
            "commits when the tree has moved between the presses"
        ),
    }
    return out


def written_against_solved(directory: Path, record: Mapping[str, Any], argmax: str | None) -> dict[str, Any]:
    """The argmax component as the solve accepted it, against what the run wrote to its MFILE.

    The solved value is read from the run's own snapshot at the declared
    position (``y_entry_to_write_output_files.json``, hex, exact); the written
    value from the ``(<name>)`` line of the run's MFILE, where ``<name>`` is
    the component's attribute name.  Information beside the residual, in the
    units A61 §8 used, so the same difference is readable as a relative
    number; never a criterion.  A component the MFILE does not carry is
    stated as such.
    """
    out: dict[str, Any] = {"component": argmax}
    if not argmax:
        out["why_not"] = "no argmax to look up"
        return out
    snapshot = Path(directory) / "y_entry_to_write_output_files.json"
    if not snapshot.exists():
        out["why_not"] = f"{snapshot.name} is not beside the record"
        return out
    state = json.loads(snapshot.read_text()).get("state") or {}
    entry = state.get(argmax) or {}
    solved_hex = entry.get("hex")
    out["solved_hex"] = solved_hex
    configuration = record.get("campaign_configuration")
    mfile = Path(directory) / f"{configuration}.MFILE.DAT"
    tag = f"({argmax.split('.')[-1]})"
    written = None
    if mfile.exists():
        for line in mfile.read_text().splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[1] == tag:
                try:
                    written = float(parts[2])
                except ValueError:
                    written = None
                break
    out["mfile_tag"] = tag
    out["written"] = written
    out["written_hex"] = None if written is None else written.hex()
    if solved_hex is None or written is None:
        out["why_not"] = "the snapshot or the MFILE does not carry the component"
        return out
    solved = float.fromhex(solved_hex)
    out["solved"] = solved
    out["identical"] = solved.hex() == written.hex()
    out["relative_difference"] = (
        None if solved == 0 else (written - solved) / abs(solved)
    )
    return out


def body(campaign: Campaign) -> dict[str, Any]:
    """Every planned run, read and checked; the residuals published beside."""
    kept, excluded = configurations(campaign)
    rows: list[dict[str, Any]] = []
    n_checks = n_failed = 0
    passed = True
    for config in kept:
        active = arms_mod.active_arms(config, "B")
        for arm in ARMS:
            if arm not in active:
                rows.append(
                    {
                        "arm": arm,
                        "configuration": config.name,
                        "skipped": arms_mod.skipped_arms(config).get(arm),
                    }
                )
                continue
            key = f"{arm}/{config.name}/seed000"
            directory = run_directory(campaign, config.name, arm)
            record = _read(directory, "metrics.json", key=key)
            command = _read(directory, "command.json", key=key)
            checks, row = evaluate_run(record, command, arm=arm, key=key)
            row["declared_position_residual"] = declared_position_beside(
                campaign, config.name, arm, row
            )
            frozen = (row["after_run_residual"].get("frozen") or {}).get("restricted") or {}
            row["argmax_written_against_solved"] = written_against_solved(
                directory, record, frozen.get("argmax")
            )
            row["outdir"] = str(directory)
            n_checks += len(checks)
            n_failed += sum(1 for c in checks if not c["passed"])
            passed = passed and row["passed"]
            rows.append(row)
    finished = [r for r in rows if r.get("status") == "ok"]
    return {
        "passed": passed,
        "population": (
            f"{len(finished)} run(s) at seed 0, unperturbed = {len(ARMS)} arm(s) "
            f"({', '.join(ARMS)}) x {len(kept)} pulsed configuration(s), each "
            f"composed from the experiment's matrix with no override but the "
            f"audit position, each audited at {AUDIT_POSITION}; {n_checks} "
            f"composition-and-position checks, {n_failed} failed.  The residual "
            f"is published on both rulers, whole-state and restricted, and is "
            f"NOT a criterion: this gate does not pass or fail on the size of the "
            f"gap.  {len(excluded)} configuration(s) excluded with the reason "
            f"stated: {sorted(excluded)}"
        ),
        "n_compared": n_checks,
        "n_mismatched": n_failed,
        "n_runs": len(finished),
        "what_the_residual_means": (
            "the distance between the state PROCESS wrote to its output files "
            "and a fixed point of the solve's own map: the same one-sweep "
            "instrument every arm gets, with the solve-phase data structure put "
            "back for every field outside the coupling state and the coupling "
            "state left as the run ended it.  A property of PROCESS's output "
            "pass (issue I-21), published as a finding; not a convergence "
            "statement about any arm, and never accepted on"
        ),
        "audit_position_override": {
            "position": AUDIT_POSITION,
            "caller": GATE_NAME,
            "why": records_mod.AUDIT_POSITION_AFTER_RUN_CALLERS[GATE_NAME],
            "declared_callers": sorted(records_mod.AUDIT_POSITION_AFTER_RUN_CALLERS),
            "note": records_mod.AUDIT_POSITION_AFTER_RUN_WHY,
        },
        "excluded_configurations": excluded,
        "runs": rows,
        "summary": [
            {
                "arm": r["arm"],
                "configuration": r["configuration"],
                "output_path": r["output_path"],
                "output_loop_sweeps": r["output_loop_sweeps"],
                "frozen_restricted_max_hex": r["after_run_residual"]["frozen"]["restricted"]["max_hex"],
                "frozen_restricted_argmax": r["after_run_residual"]["frozen"]["restricted"]["argmax"],
                "frozen_restricted_n_above_tau": r["after_run_residual"]["frozen"]["restricted"]["n_above_tau"],
                "frozen_whole_max_hex": r["after_run_residual"]["frozen"]["whole_state"]["max_hex"],
                "frozen_whole_argmax": r["after_run_residual"]["frozen"]["whole_state"]["argmax"],
                "frozen_whole_n_above_tau": r["after_run_residual"]["frozen"]["whole_state"]["n_above_tau"],
                "instrument": r["instrument"]["restores"],
                "argmax_written_relative_to_solved": r["argmax_written_against_solved"].get(
                    "relative_difference"
                ),
                "passed": r["passed"],
            }
            for r in finished
            if r.get("after_run_residual", {}).get("taken")
        ],
    }


# --------------------------------------------------------------------------
# teeth
# --------------------------------------------------------------------------


def _teeth(campaign: Campaign) -> tuple[Tooth, ...]:
    """Four breaks, three on throwaway copies of records and one on the pool."""

    def a_run(*, one_call: bool) -> tuple[dict[str, Any], dict[str, Any], str, str]:
        kept, _ = configurations(campaign)
        for config in kept:
            for arm in ARMS:
                if (arms_mod.ARMS[arm].output_loop == "none") != one_call:
                    continue
                directory = run_directory(campaign, config.name, arm)
                if (directory / "metrics.json").exists() and (directory / "command.json").exists():
                    key = f"{arm}/{config.name}/seed000"
                    return (
                        json.loads((directory / "metrics.json").read_text()),
                        json.loads((directory / "command.json").read_text()),
                        arm,
                        key,
                    )
        raise GateError(f"{GATE_NAME} has no {'one-call' if one_call else 'loop'} run to bite on")

    def _failed(checks: list[dict[str, Any]], prefix: str) -> list[str]:
        return [c["check"] for c in checks if c["check"].startswith(prefix) and not c["passed"]]

    def the_declared_position_where_after_run_was_asked() -> tuple[bool, str]:
        record, command, arm, key = a_run(one_call=False)
        doctored = copy.deepcopy(record)
        doctored["audit_position"] = records_mod.AUDIT_POSITION_DECLARED
        doctored["exit_audit"]["audit_position"] = records_mod.AUDIT_POSITION_DECLARED
        checks, _ = evaluate_run(doctored, command, arm=arm, key=key)
        clean, _ = evaluate_run(record, command, arm=arm, key=key)
        tripped = _failed(checks, "(2a)")
        return (
            bool(tripped) and not _failed(clean, "("),
            f"a copy of {key}'s record audited at the declared position where "
            f"{AUDIT_POSITION} was asked fails {tripped}; the run itself passes every check",
        )

    def a_one_call_arm_whose_output_path_reads_mda_output() -> tuple[bool, str]:
        record, command, arm, key = a_run(one_call=True)
        doctored = copy.deepcopy(record)
        doctored["output_path"] = "mda_output"
        doctored["output_loop_sweeps"] = 2
        checks, _ = evaluate_run(doctored, command, arm=arm, key=key)
        tripped = _failed(checks, "(1b)") + _failed(checks, "(1c)")
        return (
            len(tripped) == 2,
            f"a copy of {key}'s record with output_path = 'mda_output' and two "
            f"output-time sweeps fails {tripped} (the run itself stamped "
            f"{record.get('output_path')!r}, {record.get('output_loop_sweeps')} sweeps)",
        )

    def a_residual_whose_argmax_is_not_named() -> tuple[bool, str]:
        record, command, arm, key = a_run(one_call=True)
        doctored = copy.deepcopy(record)
        doctored["exit_audit"]["frozen"]["restricted"]["argmax"] = None
        checks, _ = evaluate_run(doctored, command, arm=arm, key=key)
        tripped = _failed(checks, "(3)")
        return (
            bool(tripped),
            f"a copy of {key}'s record whose frozen restricted argmax is None "
            f"fails {tripped}; the residual's size was left exactly as recorded",
        )

    def an_undeclared_caller_asking_for_after_run() -> tuple[bool, str]:
        kept, _ = configurations(campaign)
        if not kept:
            return False, "no pulsed configuration to compose a job on"
        job = pool_mod.Job(
            phase="B",
            arm="BR",
            config=kept[0],
            seed=0,
            outdir=root(campaign) / "_never",
            regime="unperturbed",
            delta=campaign.delta,
            run_kind="gate",
            audit_position=AUDIT_POSITION,
            audit_position_caller="a_stage_nobody_declared",
        )
        try:
            pool_mod.environment_for(job, campaign)
        except pool_mod.PoolError as exc:
            return True, f"refused: {str(exc).splitlines()[0][:200]}"
        return False, f"the pool composed an environment for an undeclared caller of {AUDIT_POSITION}"

    return (
        Tooth(
            "the_declared_position_where_after_run_was_asked",
            "a throwaway copy of a record with audit_position set to the declared position",
            "FAIL check (2a)",
            the_declared_position_where_after_run_was_asked,
        ),
        Tooth(
            "a_one_call_arm_whose_output_path_reads_mda_output",
            "a throwaway copy of a B1/B3 record with output_path 'mda_output' and two output-time sweeps",
            "FAIL checks (1b) and (1c)",
            a_one_call_arm_whose_output_path_reads_mda_output,
        ),
        Tooth(
            "a_residual_whose_argmax_is_not_named",
            "a throwaway copy of a record whose restricted argmax is null",
            "FAIL check (3)",
            a_residual_whose_argmax_is_not_named,
        ),
        Tooth(
            "an_undeclared_caller_asking_for_after_run",
            f"a job asking for {AUDIT_POSITION} under a stage name the declared-caller table does not hold",
            "REFUSE at the pool, before any run",
            an_undeclared_caller_asking_for_after_run,
        ),
    )


def gate(campaign: Campaign) -> Gate:
    from . import gates as gates_mod  # noqa: PLC0415 - the registry imports this module

    return Gate(
        name=GATE_NAME,
        plan_name=None,
        needs_runs=True,
        binds=(
            "the written-file gap on the one-call output path: BR, B1 and B3 "
            "at seed 0 on the pulsed configurations, campaign-composed, audited "
            "after the run (issue I-21)"
        ),
        what_it_proves=(
            "each run finished as the arm the matrix describes, on the output "
            "path its cell names, audited at after_run as this gate's declared "
            "override; and it publishes -- never gates on -- the distance "
            "between the state PROCESS wrote out and a fixed point of the "
            "solve's own map, argmax named, beside the declared-position "
            "residual of the same cell"
        ),
        body=lambda *, resume=False: gates_mod._with_capture(
            capture, body, campaign, resume=resume
        ),
        runs_under=(f"{GATE_NAME}/runs",),
        # It reads gate G9's records for the declared-position column beside
        # its own, so it follows that gate in the derived order.
        reads_from=("output_path",),
        teeth=_teeth(campaign),
    )
