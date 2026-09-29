"""Gate G9 -- the output path writes the state the solve handed over -- and the
output-path measurement stage beside it.

G9 binds the removal of upstream's output-time loop from the arms whose matrix
cell turns it off: the state those arms write to their output files is the state
their solve handed over, bit for bit outside the per-run deferred nodes' own
writes, with no output-time sweep run and the accepted objective in the file;
and nothing about the solve changed on the arms that keep the loop.

The second section holds :func:`excluded_by_the_per_run_nodes`, the excluded
set of the restricted audit statistic, which gates G2/G3 and G4 import from
here.  The measurement stage that used to follow it (``output_path_measurements``
with its contrast runs) was retired by the simplification survey's item B5.

Moved verbatim out of ``harness/gates/gates.py`` (its ``G9`` section) by the
code-move task of the simplification survey; written by task **A57
(driver-output-path)**.  Gate name, ``runs_under``, record path and teeth are
unchanged; the gate is constructed by :func:`gate` and registered in
``harness/gates/registry.py``.
"""

from __future__ import annotations

import copy
import datetime as _dt
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping

_EXPERIMENT_DIR = Path(__file__).resolve().parents[2]
if str(_EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(_EXPERIMENT_DIR))

from harness.experiment import arms as arms_mod  # noqa: E402
from harness.core import framework  # noqa: E402
from harness.experiment import input_files as input_files_mod  # noqa: E402
from harness.core import pool as pool_mod  # noqa: E402
from harness.core import records as records_mod  # noqa: E402
from harness.core.config import Campaign, Config  # noqa: E402
from harness.gates.gate_neutrality import _read_record, _same  # noqa: E402
from harness.gates.gates import _with_capture  # noqa: E402

GATES_SUBPATH = framework.GATES_SUBPATH
Gate = framework.Gate
Tooth = framework.Tooth
GateError = framework.GateError
_git_head = framework.git_head


# --------------------------------------------------------------------------
# G9 -- the output path writes the state the solve handed over
# --------------------------------------------------------------------------
#
# What G9 binds is the removal of upstream's output-time loop from the two
# intervention arms, and it binds it in the only way that means anything: not
# "the switch was set" but "the state that reached the output files is the
# state the optimiser accepted".
#
# Three criteria on an arm whose matrix cell turns the loop off:
#
#   (i)   the coupling state immediately before the file-writing call is
#         **bit-identical**, component by component in hex, to the snapshot
#         taken at the entry to the output path -- on every component the
#         per-run deferred nodes do not own.  Those nodes run between the two
#         snapshots by design (that is what "once per run, at the accepted
#         optimum" means), their write set is derived from the same two
#         committed artifacts the restricted audit derives it from, never
#         listed, and the components they move are reported by name rather
#         than waved past;
#   (ii)  the output-time loop ran **0** sweeps;
#   (iii) the objective in PROCESS's own output file is the accepted objective,
#         to the bit.
#
# And on the reference arms, which keep the loop: every field that describes
# the solve equals the reproduction gate's record for the same run.  "Nothing
# changes on BR/B0" is a comparison against a record made before this change,
# not an assertion.  The audit residual is deliberately **not** among those
# fields -- the audit moved to the declared position for every arm, which is
# the other half of this task -- and that exclusion is stated here rather than
# left to be noticed.

#: Fields that describe the solve and must be untouched by an output-path
#: change, compared against the reproduction gate's record run for run.
#: ``exit_audit.residual_max_hex`` is deliberately absent: the audit position
#: moved for every arm in this same change, so the residual is expected to
#: differ and comparing it would test the audit, not the output path.
UNCHANGED_ON_REFERENCE_ARMS: tuple[str, ...] = (
    "node_calls_solve_phase",
    "node_calls_total",
    "n_model_calls",
    "n_arrangement_method_calls",
    "exact.norm_objf",
    "n_solver_iterations",
    "mfile.ifail",
    "exit_forensics.n_attempts",
    "exit_forensics.n_solver_iterations_summed_over_attempts",
)


def output_path_root(campaign: Campaign) -> Path:
    """Where G9's verdict and manifest go.  Its runs are shared-pool jobs."""
    return Path(campaign.runs_dir) / GATES_SUBPATH / "output_path"


def output_path_job(campaign: Campaign, config: Config, arm: str) -> pool_mod.Job:
    """One Phase B arm at seed 0, at the declared audit position."""
    return pool_mod.Job(
        phase="B",
        arm=arm,
        config=config,
        seed=0,
        regime="unperturbed",
        delta=campaign.delta,
        run_kind="gate",
    )


def output_path_run_dir(campaign: Campaign, configuration: str, arm: str) -> Path:
    """Where G9's run of this arm on this configuration is: the pool's directory."""
    return pool_mod.directory_for(
        output_path_job(campaign, campaign.configuration(configuration), arm), campaign
    )


def output_path_jobs(campaign: Campaign) -> list[pool_mod.Job]:
    """Every Phase B arm at seed 0 on every configuration where it is active.

    The intervention arms carry the criteria; the reference arms carry the
    "nothing changes" half.  A skipped arm is skipped **by the configuration's
    own recorded reason**, never by a condition written here.
    """
    jobs: list[pool_mod.Job] = []
    for config in campaign.configurations:
        for arm in arms_mod.active_arms(config, "B"):
            jobs.append(output_path_job(campaign, config, arm))
    return jobs


def _reproduction_planned(campaign: Campaign) -> list[Any]:
    """GR's planned runs with their entries attached, directories resolved."""
    from . import reproduction as reproduction_mod  # noqa: PLC0415

    root = Path(campaign.runs_dir) / reproduction_mod.RUNS_SUBPATH
    planned, _prerequisites = reproduction_mod.plan(campaign, root)
    reproduction_mod.attach_phase_a_entries(planned, root, campaign)
    return planned


def reproduction_run_dir(campaign: Campaign, configuration: str, arm: str, seed: int) -> Path:
    """Where the reproduction gate's run of this arm is: **its** job, resolved.

    The reference arms are compared against GR's record of the same arm; that
    record is GR's job — after-run audit, the gate's overrides — and is found
    by composing that job and asking the pool, not by a directory G9 knows.
    """
    for item in _reproduction_planned(campaign):
        if (
            item.run.configuration == configuration
            and item.run.arm == arm
            and item.run.seed == seed
        ):
            return Path(item.job.outdir)
    raise GateError(
        f"the reproduction gate plans no run of {arm} on {configuration} at "
        f"seed {seed}, so G9 has nothing to compare its reference arm against"
    )


def jobs_read(campaign: Campaign) -> list[pool_mod.Job]:
    """Every job G9 reads: its own runs, and GR's seed-0 records of the reference arms."""
    jobs = output_path_jobs(campaign)
    reference_arms = {
        arm
        for config in campaign.configurations
        for arm in arms_mod.active_arms(config, "B")
        if arms_mod.ARMS[arm].output_loop != "none"
    }
    jobs += [
        item.job
        for item in _reproduction_planned(campaign)
        if item.run.phase == "B" and item.run.seed == 0 and item.run.arm in reference_arms
    ]
    return jobs


def _job_rows(campaign: Campaign) -> list[dict[str, Any]]:
    from . import gates as gates_mod  # noqa: PLC0415

    return gates_mod.job_rows(jobs_read, campaign)


def capture_output_path(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    """Run G9's runs and record where they went.  Nothing is compared here."""
    jobs = output_path_jobs(campaign)
    # The two arms whose matrix cell turns the loop off read the lifted input
    # file.  Checked here, before anything starts, so that "the derived input
    # file is not there" is a refusal at the gate's front door rather than a
    # failed run three jobs in.
    lifted = {}
    for config in campaign.configurations:
        if config.pulsed:
            lifted[config.name] = input_files_mod.assert_lifted(config, campaign)
    results = pool_mod.run_all(jobs, campaign, resume=resume)
    manifest = {
        "captured": _dt.datetime.now().isoformat(timespec="seconds"),
        "tree_git_head": _git_head(),
        "n_runs": len(jobs),
        "lifted_input_files": lifted,
        "runs": [
            {
                "configuration": job.config.name,
                "arm": job.arm,
                "outdir": str(job.outdir),
                "status": (results[i] or {}).get("status")
                if isinstance(results, list)
                else None,
            }
            for i, job in enumerate(jobs)
        ],
        "skipped": {
            config.name: dict(arms_mod.skipped_arms(config))
            for config in campaign.configurations
        },
    }
    path = output_path_root(campaign) / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    manifest["manifest"] = str(path)
    return manifest


def _snapshot(directory: Path, where: str, *, key: str) -> dict[str, Any]:
    path = Path(directory) / f"y_{where}.json"
    if not path.exists():
        raise GateError(
            f"G9 has no {where!r} snapshot for {key}: {path} is not there.  A "
            f"gate that cannot find one of the two states it compares must "
            f"refuse, never pass over an empty comparison (trap T11)."
        )
    return json.loads(path.read_text())


def compare_snapshots(
    entry: Mapping[str, Any],
    written: Mapping[str, Any],
    *,
    excluded: set[str],
) -> dict[str, Any]:
    """Two snapshots of the coupling state, component by component, exactly.

    Floats travel as hex literals in a snapshot, so equality here is bit
    equality and no tolerance is applied or available.  ``excluded`` names the
    components the per-run deferred nodes own; they are compared too, and
    reported separately, so that "the difference is confined to the nodes that
    are *supposed* to run there" is a measurement rather than a premise.
    """
    if entry["components_sha256"] != written["components_sha256"]:
        raise GateError(
            "G9's two snapshots were taken against different component specs "
            f"({entry['components_sha256']} vs {written['components_sha256']}); "
            "comparing them would compare components nobody paired"
        )
    a, b = entry["state"], written["state"]
    names = sorted(set(a) | set(b))
    differing_kept, differing_excluded = [], []
    for name in names:
        if a.get(name) == b.get(name):
            continue
        (differing_excluded if name in excluded else differing_kept).append(name)
    return {
        "n_components": len(names),
        "n_excluded_as_per_run_owned": len(excluded & set(names)),
        "n_compared": len(names) - len(excluded & set(names)),
        "n_differing_outside_the_per_run_write_sets": len(differing_kept),
        "differing_outside_the_per_run_write_sets": differing_kept[:20],
        "n_differing_inside_the_per_run_write_sets": len(differing_excluded),
        "differing_inside_the_per_run_write_sets": differing_excluded[:20],
    }


def per_run_owned_components(
    campaign: Campaign, arm: str, config
) -> tuple[set[str], dict[str, Any]]:
    """Components the per-run deferred nodes write, derived from the artifacts.

    The same derivation the restricted audit uses -- the per-run artifact names
    nodes, the committed run-time write census maps each node to what it writes
    on this configuration -- so the two statistics cannot drift apart.  An arm
    that defers nothing owns nothing, and the whole state is compared.
    """
    entry = arms_mod.ARMS[arm]
    if not entry.defer_per_run:
        return set(), {"defers_per_run": False, "artifact": None}
    artifact = config.per_run_artifact(lifted_input_file=entry.input_file == "lifted")
    nodes = list(json.loads(Path(artifact).read_text())["post_solve_nodes"])
    census = json.loads(
        (Path(campaign.data_dir) / "node_writesets.json").read_text()
    )["per_scenario"]
    if config.name not in census:
        raise GateError(
            f"G9 has no write census for {config.name}; the per-run-owned set "
            f"would be guessed, so it is refused"
        )
    writes = census[config.name]["writes_by_node"]
    owned: set[str] = set()
    for node in nodes:
        owned |= set(writes.get(node, ()))
    return owned, {
        "defers_per_run": True,
        "artifact": str(artifact),
        "per_run_nodes": nodes,
        "n_owned_fields": len(owned),
    }


def output_path_body(campaign: Campaign) -> dict[str, Any]:
    """Compare each run against its criteria, and each reference against GR."""
    rows: list[dict[str, Any]] = []
    passed = True
    n_components = n_component_diffs = 0
    n_reference_values = n_reference_diffs = 0
    for config in campaign.configurations:
        for arm in arms_mod.active_arms(config, "B"):
            key = f"{arm}/{config.name}"
            directory = output_path_run_dir(campaign, config.name, arm)
            record = _read_record(directory, side="G9", key=key)
            entry = arms_mod.ARMS[arm]
            row: dict[str, Any] = {
                "arm": arm,
                "configuration": config.name,
                "matrix_cell": arms_mod.matrix_cell(entry, "output-time loop (MDA_Output)"),
                "status": record.get("status"),
                "output_path": record.get("output_path"),
                "output_loop_sweeps": record.get("output_loop_sweeps"),
                "output_path_entries": record.get("output_path_entries"),
                "audit_position": record.get("audit_position"),
                "audit_position_declared": record.get("audit_position_declared"),
                "exit_audit_residual_max_hex": (record.get("exit_audit") or {}).get(
                    "residual_max_hex"
                ),
                "exit_audit_n_above_tau": (
                    (record.get("exit_audit") or {}).get("restricted") or {}
                ).get("n_above"),
                "outdir": str(directory),
            }
            checks: list[dict[str, Any]] = []
            checks.append(
                {
                    "check": "the audit was taken where the plan declares",
                    "passed": record.get("audit_position")
                    == record.get("audit_position_declared")
                    == "entry_to_write_output_files",
                    "detail": f"{record.get('audit_position')!r}",
                }
            )
            if entry.output_loop == "none":
                row["expected_output_path"] = "finalise_once"
                owned, derivation = per_run_owned_components(campaign, arm, config)
                row["per_run_derivation"] = derivation
                comparison = compare_snapshots(
                    _snapshot(directory, "entry_to_write_output_files", key=key),
                    _snapshot(directory, "before_finalise", key=key),
                    excluded=owned,
                )
                row["state_written_vs_handed_over"] = comparison
                n_components += comparison["n_compared"]
                n_component_diffs += comparison[
                    "n_differing_outside_the_per_run_write_sets"
                ]
                checks += [
                    {
                        "check": (
                            "(i) the state written out is the state the solve "
                            "handed over, component by component in hex, "
                            "outside the per-run deferred nodes' own writes"
                        ),
                        "passed": comparison[
                            "n_differing_outside_the_per_run_write_sets"
                        ]
                        == 0,
                        "detail": (
                            f"{comparison['n_differing_outside_the_per_run_write_sets']}"
                            f" of {comparison['n_compared']} components differ"
                        ),
                    },
                    {
                        "check": "(ii) the output-time loop ran no sweep",
                        "passed": record.get("output_loop_sweeps") == 0,
                        "detail": f"output_loop_sweeps = {record.get('output_loop_sweeps')}",
                    },
                    {
                        "check": "(iii) the output file's objective is the accepted objective, to the bit",
                        "passed": _same_hex(
                            (record.get("mfile") or {}).get("norm_objf"),
                            (record.get("exact") or {}).get("norm_objf"),
                        ),
                        "detail": _hex_detail(
                            (record.get("mfile") or {}).get("norm_objf"),
                            (record.get("exact") or {}).get("norm_objf"),
                        ),
                    },
                    {
                        "check": "the driver resolved the finalise-once path",
                        "passed": record.get("output_path") == "finalise_once",
                        "detail": f"{record.get('output_path')!r}",
                    },
                ]
            else:
                row["expected_output_path"] = "mda_output"
                reference = reproduction_run_dir(campaign, config.name, arm, 0)
                previous = _read_record(
                    reference, side="reproduction gate", key=key
                )
                diffs = []
                for path in UNCHANGED_ON_REFERENCE_ARMS:
                    left = records_mod.resolve_path(previous, path)
                    right = records_mod.resolve_path(record, path)
                    n_reference_values += 1
                    if not _same(left, right):
                        diffs.append({"field": path, "gate_GR": left, "here": right})
                n_reference_diffs += len(diffs)
                row["unchanged_against_the_reproduction_gate"] = {
                    "reference_record": str(reference / "metrics.json"),
                    "n_compared": len(UNCHANGED_ON_REFERENCE_ARMS),
                    "n_differing": len(diffs),
                    "differing": diffs,
                    "fields": list(UNCHANGED_ON_REFERENCE_ARMS),
                    "audit_residual_excluded_because": (
                        "the audit position moved to the declared one for every "
                        "arm in this same change, so the residual is expected "
                        "to differ; the audit is gated by its own criterion "
                        "above and the two residuals are published side by side"
                    ),
                    "audit_residual_here": row["exit_audit_residual_max_hex"],
                    "audit_residual_at_the_previous_position": (
                        previous.get("exit_audit") or {}
                    ).get("residual_max_hex"),
                }
                checks += [
                    {
                        "check": "nothing about the solve changed on the reference arm",
                        "passed": not diffs,
                        "detail": (
                            f"{len(diffs)} of {len(UNCHANGED_ON_REFERENCE_ARMS)} "
                            f"fields differ from the reproduction gate's record"
                        ),
                    },
                    {
                        "check": "the driver resolved upstream's output path",
                        "passed": record.get("output_path") == "mda_output",
                        "detail": f"{record.get('output_path')!r}",
                    },
                    {
                        "check": "the output-time loop actually ran",
                        "passed": (record.get("output_loop_sweeps") or 0) >= 1,
                        "detail": f"output_loop_sweeps = {record.get('output_loop_sweeps')}",
                    },
                ]
            row["checks"] = checks
            row["passed"] = record.get("status") == "ok" and all(
                c["passed"] for c in checks
            )
            passed = passed and row["passed"]
            rows.append(row)
    return {
        "passed": passed,
        "population": (
            f"{len(rows)} run(s) at seed 0 = every optimisation-phase arm on "
            f"every configuration where it is active, each composed from the "
            f"experiment's matrix; {n_components} coupling-state components "
            f"compared in hex on the arms whose matrix cell turns the "
            f"output-time loop off, and {n_reference_values} solve-describing "
            f"values compared against the reproduction gate's records on the "
            f"arms that keep it.  No tolerance is applied to any of them"
        ),
        "n_runs": len(rows),
        "n_components_compared": n_components,
        "n_components_differing": n_component_diffs,
        "n_reference_values_compared": n_reference_values,
        "n_reference_values_differing": n_reference_diffs,
        "unchanged_fields": list(UNCHANGED_ON_REFERENCE_ARMS),
        "runs": rows,
    }


def _same_hex(mfile_value, accepted_hex) -> bool:
    if mfile_value is None or accepted_hex is None:
        return False
    try:
        return float(mfile_value).hex() == accepted_hex
    except (TypeError, ValueError):
        return False


def _hex_detail(mfile_value, accepted_hex) -> str:
    try:
        got = float(mfile_value).hex()
    except (TypeError, ValueError):
        got = repr(mfile_value)
    return f"output file {got}, accepted {accepted_hex}"


def _output_path_teeth(campaign: Campaign) -> tuple[Tooth, ...]:
    """Four breaks, every one on a throwaway copy; no run is ever touched."""

    def an_intervention_run() -> tuple[Path, str, Any]:
        for config in campaign.configurations:
            for arm in arms_mod.active_arms(config, "B"):
                if arms_mod.ARMS[arm].output_loop == "none":
                    directory = output_path_run_dir(campaign, config.name, arm)
                    if (directory / "metrics.json").exists():
                        return directory, f"{arm}/{config.name}", config
        raise GateError("G9 has no intervention run to bite on")

    def one_ulp_before_finalise() -> tuple[bool, str]:
        directory, key, config = an_intervention_run()
        entry = _snapshot(directory, "entry_to_write_output_files", key=key)
        written = copy.deepcopy(entry)
        arm = key.split("/")[0]
        owned, _ = per_run_owned_components(campaign, arm, config)
        target = next(
            (
                name
                for name, value in sorted(written["state"].items())
                if value.get("k") == "f" and name not in owned
            ),
            None,
        )
        if target is None:
            return False, "the snapshot carries no float component outside the per-run write sets"
        before = float.fromhex(written["state"][target]["hex"])
        after = math.nextafter(before, math.inf)
        written["state"][target]["hex"] = after.hex()
        result = compare_snapshots(entry, written, excluded=owned)
        return (
            result["n_differing_outside_the_per_run_write_sets"] == 1
            and result["differing_outside_the_per_run_write_sets"] == [target],
            f"{target} moved by one unit in the last place between the snapshot "
            f"and the file-writing call ({before.hex()} -> {after.hex()}) -> "
            f"{result['n_differing_outside_the_per_run_write_sets']} of "
            f"{result['n_compared']} components differ",
        )

    def missing_snapshot() -> tuple[bool, str]:
        import tempfile  # noqa: PLC0415 - tooth path only

        with tempfile.TemporaryDirectory() as td:
            try:
                _snapshot(Path(td), "before_finalise", key="B2/tooth")
            except GateError as exc:
                return True, f"refused: {str(exc).splitlines()[0][:160]}"
        return False, "a missing snapshot did not refuse"

    def a_sweep_that_should_not_be() -> tuple[bool, str]:
        directory, key, _config = an_intervention_run()
        record = copy.deepcopy(_read_record(directory, side="G9", key=key))
        record["output_loop_sweeps"] = 1
        return (
            record["output_loop_sweeps"] != 0,
            f"a throwaway copy of {key}'s record with output_loop_sweeps = 1 "
            f"fails criterion (ii), which reads the field the driver stamped "
            f"(the run itself recorded 0)",
        )

    def a_moved_objective() -> tuple[bool, str]:
        directory, key, _config = an_intervention_run()
        record = _read_record(directory, side="G9", key=key)
        accepted = (record.get("exact") or {}).get("norm_objf")
        written = (record.get("mfile") or {}).get("norm_objf")
        if accepted is None or written is None:
            return False, f"{key} carries no objective to move"
        nudged = math.nextafter(float(written), math.inf)
        return (
            _same_hex(written, accepted) and not _same_hex(nudged, accepted),
            f"the output file's objective moved by one unit in the last place "
            f"({float(written).hex()} -> {nudged.hex()}) no longer equals the "
            f"accepted {accepted}",
        )

    return (
        Tooth(
            "one_component_moved_by_one_ulp_before_finalise",
            "one float of a throwaway copy of the entry snapshot moved by one "
            "unit in the last place, standing in for the state being touched "
            "between the snapshot and the file-writing call",
            "FAIL, naming the component",
            one_ulp_before_finalise,
        ),
        Tooth(
            "missing_snapshot",
            "one of the two snapshots asked for at a directory that has none",
            "REFUSE, not skip",
            missing_snapshot,
        ),
        Tooth(
            "an_output_time_sweep_under_the_finalise_once_path",
            "a throwaway copy of an intervention run's record with "
            "output_loop_sweeps = 1",
            "FAIL",
            a_sweep_that_should_not_be,
        ),
        Tooth(
            "the_written_objective_moved",
            "the output file's objective moved by one unit in the last place",
            "FAIL",
            a_moved_objective,
        ),
    )


# --------------------------------------------------------------------------
# the per-run nodes' own writes -- the excluded set gates G2/G3 and G4 share
# --------------------------------------------------------------------------
#
# The audit sweep runs every node, including the ones an arm defers to once
# per run; measured from the handed-over state -- which is *before* those
# nodes have run -- their own outputs necessarily move, and a whole-state
# count on such an arm would report that as non-convergence.  The restricted
# count excludes exactly the components those nodes write, derived from the
# same two committed artifacts the audit's own restricted statistic derives
# from: the per-run deferral artifact names the nodes, the run-time write
# census says what each writes on this configuration.  One excluded set per
# configuration, from the committed input file's artifact, so that the count
# is on the same ruler in every arm of that configuration.
#
# (The measurement stage that used to sit here -- ``output_path_measurements``
# with its six contrast optimisations -- was retired by the simplification
# survey's item B5: its sweep-count half is the tally's ``output_loop_sweeps``
# column, and the written-file half is gate ``written_file_gap``'s question.)


def excluded_by_the_per_run_nodes(campaign: Campaign, config) -> tuple[set[str], dict]:
    """Components the per-run deferrable nodes write on this configuration.

    One set per configuration, from the **committed** input file's artifact, so
    that every arm of that configuration is restricted by the same set — which
    is the whole point of a restricted statistic.  The derivation is the audit's
    own: the artifact names nodes, the census maps each node to what it writes.
    """
    artifact = config.per_run_artifact(lifted_input_file=False)
    nodes = list(json.loads(Path(artifact).read_text())["post_solve_nodes"])
    census = json.loads(
        (Path(campaign.data_dir) / "node_writesets.json").read_text()
    )["per_scenario"]
    if config.name not in census:
        raise GateError(
            f"no write census for {config.name}; the excluded set would be "
            f"guessed, so it is refused"
        )
    writes = census[config.name]["writes_by_node"]
    owned: set[str] = set()
    for node in nodes:
        owned |= set(writes.get(node, ()))
    return owned, {
        "artifact": str(artifact),
        "per_run_nodes": nodes,
        "census": str(Path(campaign.data_dir) / "node_writesets.json"),
        "n_fields_named": len(owned),
    }


def gate(campaign: Campaign) -> Gate:
    """G9, as the registry holds it.  The literal is the one ``_plan_gates`` held."""
    return Gate(
        name="output_path",
        plan_name="G9",
        needs_runs=True,
        binds=(
            "the removal of the output-time loop from the arms whose "
            "matrix cell turns it off, on every configuration where they "
            "are active"
        ),
        what_it_proves=(
            "the state those arms write to their output files is the "
            "state their solve handed over — bit for bit, outside the "
            "per-run deferred nodes' own writes — with no output-time "
            "sweep run and the accepted objective in the file; and that "
            "nothing about the solve changed on the arms that keep the "
            "loop"
        ),
        body=lambda *, resume=False: _with_capture(
            capture_output_path, output_path_body, campaign, resume=resume
        ),
        jobs=lambda: _job_rows(campaign),
        # It compares its reference arms against the reproduction gate's
        # own records, so it cannot run before that gate has made them.
        reads_from=("reproduction",),
        teeth=_output_path_teeth(campaign),
    )
