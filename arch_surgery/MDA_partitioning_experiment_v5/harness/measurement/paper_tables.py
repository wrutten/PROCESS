#!/usr/bin/env python
"""The paper's one document, computed from the campaign's run records.

**The one generator** (V5 list item 10, the user's ruling of 2026-09-29: *"this
v5 reporting approach is approved"*; V5 plan §8).  It writes one file,
:data:`PAPER_NAME`, beside the report — the tables the paper *Structuring
fusion MDAO with DSMs* (§3, Case 2: PROCESS) prints, each as a Markdown grid
and as LaTeX rows for the paper's ``tabular`` bodies — and nothing else renders
a table in this revision.  ``check`` refuses when the rendered file and the
records disagree.

Main text
    the switch matrix (from ``arms.matrix(campaign)``, the same data every arm is
    composed from); the configurations table; phase A module sweeps per
    evaluation with the ratio columns on **`A2/A1` (pulsed) and `A2/A0`
    (`st_regression`)** — the ratio of the means, the per-run median and the
    ``[min, max]`` bracket, all on that pair (**D34**, the user, 2026-09-29,
    superseding the `A2/A0` convention of 2026-09-28); phase B optimiser
    iterations and phase B module sweeps per optimisation on `B2/B0` with the
    rungs beside.

Appendix
    the two module tables in wall clock and the cost breakdown of plan §6,
    filled from the records' ``timers`` block (item 9, driver change DR12,
    A101 (v5-timers-and-once); ``timing.tables_over``) — context, never
    evidence (D33); the per-arm success table (plan §5 B5); and **one
    verification table**, one row per check of plan §8, each verdict read from the gate
    records through the ``gate_table`` stage record where the gate exists and
    "not pressed" otherwise.

**A cell is a module's sweeps per run** (the user, 2026-09-28), averaged over
the ``n`` runs of the arm; the ratio column is the ratio of the means
(Σ intervened / Σ control over the paired runs); beside it the per-run
ratio's median with its ``[min, max]``.  There is no total row: sweeps of
different modules do not add.  **Nothing here is a new construction**: every
number is the tally's own building block applied to the tally's own
population, and every cell the stage records also hold is compared with them
exactly before anything is written (:func:`cross_check`, shown able to fail
on each run by :func:`_cross_check_tooth`, protocol §12).

**`CHARGED_ONCE` is retired** (plan §2, item 5).  V4 charged `A2`'s
post-processing cell with one execution by construction, because its phase A
census stopped before the output pass; since item 5's driver change (A101
(v5-timers-and-once), decision D35) the deferred nodes are executed once
after convergence *by the run* and the cell reads the measured count — 1 on
every run, checked as the one integer every run reads.

Written by task **A98 (v5-reporting-trim)**, 2026-09-29, extending the
paper-tables module of 2026-09-28; the stage-record stamp check and the
population marker are moved here from the removed ``plan_tables.py``.
"""

from __future__ import annotations

import copy
import datetime as _dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import dataclasses

from harness.core import framework
from harness.core.config import EXECUTION_APPROVED, Campaign
from harness.experiment import arms as arms_mod
from harness.measurement import stats as stats_mod
from harness.measurement import tally as tally_mod
from harness.measurement import tally_evaluation as tally_a
from harness.measurement import tally_optimisation as tally_b

#: The generated file, beside ``EXPERIMENT_REPORT.md``.
PAPER_NAME = "paper_tables.md"

#: The paper's configuration labels.
SHORT = {
    "large_tokamak_nof": "tok",
    "low_aspect_ratio_DEMO": "lad",
    "st_regression": "st",
}

#: The paper's names for the three machines (``3 results.tex``, §3.2.3).
FULL = {
    "large_tokamak_nof": "Large tokamak",
    "low_aspect_ratio_DEMO": "Low aspect ratio DEMO",
    "st_regression": "Spherical tokamak",
}

#: The paper's rows, each the node group(s) it is formed from.  A row over two
#: groups is one sweep count only where both groups were swept equally often
#: in a run; otherwise the run is refused (:func:`_row_sweeps`).
ROWS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("M1", ("M1",)),
    ("M2", ("M2",)),
    ("M3", ("M3",)),
    ("Feedforward", ("PULSE", "FF")),
    ("Post-processing", (stats_mod.ONCE_PER_RUN_GROUP,)),
)

#: Phase A cells printed as the integer every run reads, not as a mean: the
#: partitioned arm's feedforward and post-processing rows run a fixed number
#: of times per evaluation by construction (once each: the tail after M3,
#: and the once-per-run set at the evaluation's exit since item 5).  A run
#: reading anything else, or two runs reading different integers, is a
#: refusal, not a rounded mean.
EXACT_CELLS = {("A2", "Feedforward"), ("A2", "Post-processing")}

PHASE_A_SOURCE = tally_mod.ACCEPTANCE_REGIME
PHASE_B_SOURCE = "campaign_optimisation"
PHASE_B_PAIR = tally_b.HEADLINE_PAIR

#: The iteration quantity (summed over attempts; plan §5 B3, context beside ε).
ITERATIONS_LABEL, ITERATIONS = tally_b.PATH_QUANTITIES[0]


def phase_a_pair(pulsed: bool) -> tuple[str, str]:
    """**D34**: the published phase A pair — `A1 → A2` on a pulsed
    configuration, `A0 → A2` on a steady-state one where `A1` is inactive."""
    return ("A1", "A2") if pulsed else ("A0", "A2")


class PaperTablesError(RuntimeError):
    """The document cannot be stated over the records as they are."""


# --------------------------------------------------------------------------
# the stage-record stamp check (trap T14), moved here from plan_tables
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Section:
    """One stage record a part of the document is built from."""

    number: str
    heading: str
    stage: str
    #: Whether the stage's record must say **which records it read**, and be
    #: refused when they have moved since (issue I-22 (a), trap T14).
    records_read_required: bool = False


#: The verification table is built from the ``gate_table`` **stage** record,
#: which was made from the verdicts at the moment that stage ran.  A gate
#: re-run afterwards would be published as it was — the same PASS or FAIL —
#: unless the consumer refuses a record its sources have outrun, which this
#: generator does through :func:`assert_gate_table_current` before it reads
#: one.  The harness's ``stage_provenance`` self-check breaks a scratch copy
#: of the records four ways and requires that call to refuse each.
GATE_TABLE_SECTION = Section(
    number="V",
    heading="Verification",
    stage="gate_table",
    records_read_required=True,
)


def stage_record(records_dir: Path, stage: str) -> dict[str, Any]:
    """One stage's own record, or a refusal naming the stage that makes it."""
    path = Path(records_dir) / stage / "measurements.json"
    if not path.exists():
        raise PaperTablesError(
            f"stage {stage!r} has written no record at {path}.  The document's "
            f"{stage} cells are that stage's own output and are never typed by "
            f"hand: run `experiment_runner.py --measure {stage}` first."
        )
    try:
        return json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001
        raise PaperTablesError(f"{path} is not readable JSON: {exc}") from exc


def assert_stage_read_what_is_there(
    record: Mapping[str, Any], records_dir: Path, section: Section
) -> str:
    """Refuse to build a part from a stage record its sources have outrun.

    The check is the framework's, not this module's, so that it is one
    mechanism: the stage declares what it reads, the framework stamps it, and
    every consumer refuses the same way.
    """
    try:
        return framework.assert_records_read_are_current(
            record,
            records_dir,
            stage=section.stage,
            remedy=(
                f"Re-run `experiment_runner.py --measure {section.stage} "
                f"--resume` and render again: the {section.heading} table is "
                f"that stage's output, and a table built from a record older "
                f"than the verdicts it summarises publishes the older verdict "
                f"without saying so."
            ),
        )
    except framework.StaleRecordError as exc:
        raise PaperTablesError(str(exc)) from exc


def assert_gate_table_current(records_dir: Path) -> str:
    """The ``gate_table`` stage record under *records_dir*, checked against the
    verdict records it names; the sentence that says so, or a refusal."""
    record = stage_record(records_dir, GATE_TABLE_SECTION.stage)
    return assert_stage_read_what_is_there(record, Path(records_dir), GATE_TABLE_SECTION)


# --------------------------------------------------------------------------
# the population marker, moved here from plan_tables
# --------------------------------------------------------------------------


def _survey(paths: Sequence[Path]) -> dict[str, Any]:
    """Commit, run kind, audit position, ruler and instrument over *paths*."""
    heads: dict[str, int] = {}
    kinds: dict[str, int] = {}
    positions: set[str] = set()
    rulers: set[str] = set()
    instruments: set[str] = set()
    total = 0
    for path in paths:
        try:
            record = json.loads(Path(path).read_text())
        except Exception:  # noqa: BLE001 - a half-written record is not a row
            continue
        total += 1
        heads[str(record.get("tree_git_head"))] = heads.get(str(record.get("tree_git_head")), 0) + 1
        kinds[str(record.get("campaign_run_kind"))] = kinds.get(str(record.get("campaign_run_kind")), 0) + 1
        if record.get("audit_position"):
            positions.add(str(record["audit_position"]))
        if record.get("campaign_predicate_mode"):
            rulers.add(str(record["campaign_predicate_mode"]))
        instrument = (record.get("exit_audit") or {}).get("instrument") or {}
        if instrument.get("restores"):
            instruments.add(str(instrument["restores"]))
    return {
        "n_run_records": total,
        "records_by_commit": dict(sorted(heads.items())),
        "records_by_run_kind": dict(sorted(kinds.items())),
        "audit_positions": sorted(positions),
        "predicate_modes": sorted(rulers),
        "exit_audit_instrument": sorted(instruments),
    }


def population_marker(campaign: Campaign, records_dir: Path) -> dict[str, Any]:
    """What every cell is over, measured from the records themselves.

    The commit, the record count, the audit position, the convergence ruler and
    the exit-audit instrument version, all read from the run records of the
    tally's published sources rather than written down here.
    """
    present = tally_mod.campaign_present(campaign)
    published = tally_mod.published_sources(campaign)
    by_source: dict[str, int] = {}
    paths: list[Path] = []
    seen: set[str] = set()
    for source in published:
        n = 0
        for directory in tally_mod.source_directories(campaign, source):
            path = Path(directory) / "metrics.json"
            if path.exists():
                n += 1
                if str(path) not in seen:
                    seen.add(str(path))
                    paths.append(path)
        by_source[source.name] = n
    gates = _survey(sorted(Path(records_dir).rglob("metrics.json")))
    return {
        "verdict_commit": framework.git_head(),
        "campaign_present": present,
        "population_family": "campaign" if present else "gate",
        "published_sources": by_source,
        **_survey(paths),
        "gate_runs": gates,
        "execution_approved": EXECUTION_APPROVED,
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
    }


# --------------------------------------------------------------------------
# the population, as the tally forms it
# --------------------------------------------------------------------------


def with_runs(campaign: Campaign, runs_dir: Path | None) -> Campaign:
    """The campaign reading its run records from *runs_dir*.

    Run records are untracked and a relocated tree holds them elsewhere; this
    points the read at such a copy.  Nothing else of the campaign changes, and
    nothing is written there.
    """
    if runs_dir is None:
        return campaign
    return dataclasses.replace(
        campaign,
        runs_dir=Path(runs_dir),
        derived_input_dir=Path(runs_dir) / "input_files",
    )


def _population(campaign: Campaign, source_name: str, phase: str) -> stats_mod.Population:
    present = tally_mod.campaign_present(campaign)
    if not present:
        raise PaperTablesError(
            f"no campaign record under {campaign.runs_dir}; the paper's tables "
            f"are over the campaign and are not filled from gate runs"
        )
    sources = {s.name: s for s in tally_mod.published_sources(campaign)}
    if source_name not in sources:
        raise PaperTablesError(
            f"source {source_name!r} is not published (published: {sorted(sources)})"
        )
    source = sources[source_name]
    rows, refusals = tally_mod.source_rows(campaign, source)
    if refusals:
        raise PaperTablesError(
            f"[{source_name}] {len(refusals)} record(s) refused by the record "
            f"contract; first: {refusals[0]}"
        )
    population = tally_mod.population_for(
        rows, phase=phase, what=f"{source.name} — {source.what}", campaign_present=present
    )
    population.assert_no_forced_budget()
    return population


def _row_sweeps(sweeps: Mapping[str, float], groups: Sequence[str], where: str) -> float | None:
    present = sorted({sweeps[g] for g in groups if g in sweeps})
    if not present:
        return None
    if len(present) != 1:
        raise PaperTablesError(
            f"{where}: groups {[g for g in groups if g in sweeps]} were swept "
            f"{present} times; one row cannot state them as one sweep count"
        )
    return present[0]


def _summary(reference: list[float], arm: list[float]) -> dict[str, Any]:
    return stats_mod.per_seed_ratio_summary(reference, arm)


def _mean(values: Sequence[float]) -> float | None:
    return (sum(values) / len(values)) if values else None


# --------------------------------------------------------------------------
# the main-text tables
# --------------------------------------------------------------------------


def phase_a(campaign: Campaign) -> list[dict[str, Any]]:
    """Module sweeps per evaluation, ``AR A0 A1 A2``, on D34's pair per configuration."""
    population = _population(campaign, PHASE_A_SOURCE, tally_a.PHASE)
    blocks: list[dict[str, Any]] = []
    for config in campaign.configurations:
        by_seed = tally_a._by_arm_and_seed(population, config.name)
        if not by_seed:
            continue
        base, arm = phase_a_pair(config.pulsed)
        finished = {
            a: {k: r for k, r in rows.items() if stats_mod.finished(r)}
            for a, rows in by_seed.items()
        }
        every = [r for rows in finished.values() for r in rows.values()]
        groups = tally_a.node_grouping(campaign, config.name, every, phase=tally_a.PHASE)
        sweeps = {
            a: {
                k: stats_mod.module_sweeps(stats_mod.per_node_census(r, phase=tally_a.PHASE), groups)
                for k, r in rows.items()
            }
            for a, rows in finished.items()
        }
        paired = sorted(set(finished.get(base, {})) & set(finished.get(arm, {})))
        rows_out: list[dict[str, Any]] = []
        for label, members in ROWS:
            row: dict[str, Any] = {"row": label, "groups": list(members)}
            for a in tally_a.LADDER:
                values = [
                    v
                    for k, s in sorted(sweeps.get(a, {}).items())
                    if (v := _row_sweeps(s, members, f"{config.name} {a} seed {k}")) is not None
                ]
                row[a] = _mean(values)
                if (a, label) in EXACT_CELLS and values:
                    if len(set(values)) != 1 or float(values[0]) != int(values[0]):
                        raise PaperTablesError(
                            f"{config.name} {a} {label}: the runs read {sorted(set(values))}; "
                            f"the cell is printed as one integer and is refused"
                        )
                    row[f"{a}_exact"] = int(values[0])
            left = [_row_sweeps(sweeps[base][k], members, config.name) for k in paired]
            right = [_row_sweeps(sweeps[arm][k], members, config.name) for k in paired]
            row["summary"] = None if any(v is None for v in left + right) else _summary(left, right)
            rows_out.append(row)
        blocks.append(
            {
                "configuration": config.name,
                "pair": [base, arm],
                "n_per_arm": {a: len(rows) for a, rows in finished.items()},
                "n_pairs": len(paired),
                "groups": {str(g["group"]): list(g["nodes"]) for g in groups},
                "rows": rows_out,
            }
        )
    return blocks


def _phase_b_groups(campaign: Campaign) -> list[tuple[str, dict, list[int]]]:
    population = _population(campaign, PHASE_B_SOURCE, tally_b.PHASE)
    out: list[tuple[str, dict, list[int]]] = []
    for config in campaign.configurations:
        whole = tally_b._by_arm_and_seed(population, config.name)
        if not whole:
            continue
        groups = tally_b.arm_groups(whole)
        if len(groups) != 1:
            raise PaperTablesError(
                f"{config.name}: {len(groups)} arm groups in {PHASE_B_SOURCE}; a "
                f"campaign has one per configuration"
            )
        arms, seeds = groups[0]
        by_arm = tally_b.restrict(whole, arms, seeds)
        converged = stats_mod.every_arm_converged(by_arm, seeds)
        out.append((config.name, by_arm, converged))
    return out


def _without_exit_audit(record: Mapping[str, Any]) -> dict[str, int]:
    """Phase B's whole-run census less the exit audit's one sweep.

    The exit audit is the harness's accuracy instrument, not part of any
    architecture (**D36**: excluded from every evaluation count).  Phase B's
    ``per_node_counted`` includes it: the audit is one sweep of the complete
    node set, so it adds exactly 1 to every node.  That premise is checked on
    the record, never assumed — ``audit_node_calls`` must equal the number of
    nodes counted — and the run is refused otherwise.  The output path
    (MDA_Output in ``BR``/``B0``, the deferred nodes' one execution in ``B2``)
    is architecture and stays in.
    """
    counted = stats_mod.per_node_census(record, phase=tally_b.PHASE)
    audit = (record.get("node_census") or {}).get("audit_node_calls")
    if audit is None or int(audit) != len(counted):
        raise PaperTablesError(
            f"{stats_mod._label(record)}: the exit audit made {audit} node "
            f"call(s) over {len(counted)} counted node(s); subtracting one "
            f"sweep presumes they are equal, and the run is refused"
        )
    below = sorted(n for n, v in counted.items() if v < 1)
    if below:
        raise PaperTablesError(
            f"{stats_mod._label(record)}: node(s) {below} were counted 0 times, "
            f"so the audit's sweep did not execute them"
        )
    return {n: v - 1 for n, v in counted.items()}


def phase_b(campaign: Campaign) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Iterations per configuration, and module sweeps per run; B2 against B0."""
    base, arm = PHASE_B_PAIR
    iterations: list[dict[str, Any]] = []
    modules: list[dict[str, Any]] = []
    for configuration, by_arm, converged in _phase_b_groups(campaign):
        seeds = [
            s
            for s in converged
            if s in by_arm.get(base, {})
            and s in by_arm.get(arm, {})
            and stats_mod.finished(by_arm[base][s])
            and stats_mod.finished(by_arm[arm][s])
        ]

        def runs_of(a: str) -> list[tuple[int, Mapping[str, Any]]]:
            return [
                (s, by_arm[a][s])
                for s in converged
                if s in by_arm.get(a, {}) and stats_mod.finished(by_arm[a][s])
            ]

        row: dict[str, Any] = {"configuration": configuration, "n": len(converged)}
        for a in tally_b.LADDER:
            values = [tally_b._path_value(r, ITERATIONS) for _, r in runs_of(a)]
            row[a] = _mean([v for v in values if v is not None])
        pairs = [
            (tally_b._path_value(by_arm[base][s], ITERATIONS), tally_b._path_value(by_arm[arm][s], ITERATIONS))
            for s in seeds
        ]
        pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
        row["summary"] = _summary([x for x, _ in pairs], [y for _, y in pairs])
        iterations.append(row)

        records = [r for a in by_arm for _, r in runs_of(a)]
        groups = tally_a.node_grouping(campaign, configuration, records, phase=tally_b.PHASE)
        sweeps = {
            a: {s: stats_mod.module_sweeps(_without_exit_audit(r), groups) for s, r in runs_of(a)}
            for a in by_arm
        }
        measured = {
            a: {
                s: stats_mod.module_sweeps(stats_mod.per_node_census(r, phase=tally_b.PHASE), groups)
                for s, r in runs_of(a)
            }
            for a in by_arm
        }
        rows_out: list[dict[str, Any]] = []
        for label, members in ROWS:
            out: dict[str, Any] = {"row": label, "groups": list(members)}
            for a in tally_b.LADDER:
                out[f"{a}_measured"] = _mean(
                    [
                        v
                        for sw in measured.get(a, {}).values()
                        if (v := _row_sweeps(sw, members, configuration)) is not None
                    ]
                )
                values = [
                    v
                    for s, sw in sweeps.get(a, {}).items()
                    if (v := _row_sweeps(sw, members, f"{configuration} {a} seed {s}")) is not None
                ]
                out[a] = _mean(values)
            left = [_row_sweeps(sweeps[base][s], members, configuration) for s in seeds]
            right = [_row_sweeps(sweeps[arm][s], members, configuration) for s in seeds]
            out["summary"] = None if any(v is None for v in left + right) else _summary(left, right)
            rows_out.append(out)
        modules.append(
            {
                "configuration": configuration,
                "n": len(converged),
                "arms": sorted(by_arm, key=lambda a: tally_b.LADDER.index(a) if a in tally_b.LADDER else 99),
                "groups": {str(g["group"]): list(g["nodes"]) for g in groups},
                "rows": rows_out,
            }
        )
    return iterations, modules


#: "Models" is the node map's collapsed-DSM rows executed in a sweep, read and
#: never typed: 52 at the dependency-analysis pin the node map was generated
#: at, the constraints evaluation's row included (D40, the user, 2026-09-30:
#: "Print 52").  Until then the generator subtracted one declared constraint
#: row to print the paper's earlier 51; the committed node map does not label
#: rows by kind, so that subtraction was the one typed number in the document
#: and is gone.


def cases(campaign: Campaign, optimisation: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    """How the three configurations differ: objective, design variables,
    constraints, the cross-module coupling (the burn time) and the number of
    models.

    The objective, the variable and constraint counts and ``pulsed`` are the
    report's problem-definition table, read from the ``tally_optimisation``
    stage record.  Derived here: the objective's variable (the field the
    configuration's committed per-run artifact names as the objective) and
    the cross-module coupling's variable (the one iteration-variable name
    every lifted run carries and no flat run does), refused where the runs
    disagree; and the number of models — the committed node map's DSM rows
    executed in a sweep, the constraints evaluation's row included (D40).
    """
    import ast  # noqa: PLC0415

    table = _stage_table(optimisation, f"problem definition — {PHASE_B_SOURCE}")
    by_config = {r["configuration"]: r for r in table["rows"]}
    node_map = json.loads((Path(campaign.data_dir) / "dsm_node_map.json").read_text())
    executed = ((node_map.get("units") or {}).get("dsm_rows") or {}).get("executed_in_a_sweep")
    if not isinstance(executed, int):
        raise PaperTablesError("the node map states no units.dsm_rows.executed_in_a_sweep; Models would be guessed")
    models = executed
    out: list[dict[str, Any]] = []
    for configuration, by_arm, converged in _phase_b_groups(campaign):
        row = dict(by_config[configuration])
        pulsed = str(row["pulsed"]).startswith("yes")
        lifted: set[str] = set()
        if pulsed:

            def names(arm: str) -> set[frozenset[str]]:
                return {
                    frozenset(((by_arm[arm][s].get("mfile") or {}).get("itvar_names") or {}).values())
                    for s in converged
                    if s in by_arm.get(arm, {}) and stats_mod.finished(by_arm[arm][s])
                }

            flat, partitioned = names(PHASE_B_PAIR[0]), names(PHASE_B_PAIR[1])
            if len(flat) != 1 or len(partitioned) != 1:
                raise PaperTablesError(
                    f"{configuration}: the runs of one arm carry different "
                    f"iteration-variable sets; the lifted variable is not one name"
                )
            lifted = set(next(iter(partitioned)) - next(iter(flat)))
            if len(lifted) != 1:
                raise PaperTablesError(f"{configuration}: the lift adds {sorted(lifted)}, not one variable")
        artifacts = sorted(
            {
                Path(str(r.get("per_run_artifact"))).name
                for arm in by_arm
                for r in by_arm[arm].values()
                if r.get("per_run_artifact") and not str(r.get("per_run_artifact")).count("lifted")
            }
        )
        if len(artifacts) != 1:
            raise PaperTablesError(f"{configuration}: per-run artifacts {artifacts}; one expected")
        seeds = json.loads((Path(campaign.data_dir) / artifacts[0]).read_text())["seeds"]
        seeds = ast.literal_eval(seeds) if isinstance(seeds, str) else seeds
        objective_fields = [str(f) for f in seeds["detail"]["objective"]]
        if len(objective_fields) != 1:
            raise PaperTablesError(f"{configuration}: the objective reads {objective_fields}; one field expected")
        row["models"] = models
        row["objective_variable"] = objective_fields[0].split(".")[-1]
        row["lifted_variable"] = next(iter(lifted)) if lifted else None
        row["pulsed_bool"] = pulsed
        out.append(row)
    return out


# --------------------------------------------------------------------------
# the appendix tables
# --------------------------------------------------------------------------


#: The wall-clock tables of plan §6: their titles and captions (A98 declared
#: them as placeholders with every cell empty; A101 (v5-timers-and-once)
#: fills them through ``timing.tables_over`` from the records' ``timers``
#: block, driver change DR12).  The rows are ``timing.PHASE_A_ROWS`` /
#: ``PHASE_B_ROWS`` / ``BREAKDOWN_ROWS``; the ``rows`` here are the plan's
#: names, kept for the caption and checked against the module's.
WALL_CLOCK_TABLES: tuple[dict[str, Any], ...] = (
    {
        "key": "wall_phase_a",
        "title": "phase A in wall clock, ms per evaluation",
        "arms": tally_a.LADDER,
        "rows": (
            "M1", "M2", "M3", "Feedforward", "Post-processing",
            "MDA convergence test", "dispatch", "objective and constraints",
            "unattributed residual", "Total",
        ),
        "caption": (
            "Per configuration, arms as columns, ms per `call_models` evaluation: each module's "
            "own model time, the block loops' convergence test (read plus residual) and dispatch "
            "(the sweep body less its nodes and its test), the objective-and-constraints layer, "
            "the unattributed residual, and the evaluation's measured wall as Total; ratio of "
            "means and per-run median with [min, max] as the count tables. Harness-only costs — "
            "the exit-audit sweep, the state snapshots, the census hooks, the record assembly — "
            "are excluded from every cell (plan §6). Context, never evidence (D33)."
        ),
    },
    {
        "key": "wall_phase_b",
        "title": "phase B in wall clock, s per optimisation",
        "arms": tally_b.LADDER,
        "rows": (
            "M1", "M2", "M3", "Feedforward", "Post-processing",
            "MDA convergence test", "dispatch", "objective and constraints",
            "optimiser own time", "fixed per run", "unattributed residual", "Total",
        ),
        "caption": (
            "As the phase A table, per whole optimisation in seconds, with the optimiser's own "
            "time (solve-phase wall less every evaluation) and the fixed per-run term (process "
            "start, imports, numba cache load, input parse, output writing, the once-per-run "
            "schedule derivation); Total is the run's wall less the harness-only costs (plan §6)."
        ),
    },
    {
        "key": "cost_breakdown",
        "title": "cost breakdown, phase B",
        "arms": ("s per optimisation", "ms per evaluation", "share of total"),
        "rows": (
            "model evaluation (the modules summed)",
            "MDA overhead per sweep: convergence test",
            "MDA overhead per sweep: dispatch",
            "optimiser overhead per iteration",
            "fixed per run",
            "Total",
        ),
        "caption": (
            "Per configuration and arm: seconds per optimisation and ms per evaluation with the "
            "share of the total. Whether the architecture changes the overhead is read off the "
            "B0 and B2 columns of the per-sweep rows, normalised per evaluation (plan §6)."
        ),
    },
)

WALL_CLOCK_CONTEXT = (
    "**Context, never evidence (D33).** The wall-clock instrument of plan §6 (list item 9, "
    "driver change DR12, A101 (v5-timers-and-once)): observation-only timers in the driver copy "
    "(`PROCESS_ARCH_TIMERS=on`) per node, block loop, evaluation and run, harvested into every "
    "campaign record, with the launcher's independent wall beside. Excluded from every cell and "
    "measured separately: the exit-audit sweep, the state snapshots, the record assembly and the "
    "harness's set-up before the run. The rows are `harness/measurement/timing.py`'s; the "
    "repeatability stage (three repetitions at W = 1) and D38's validity check are that module's "
    "stages and their records say whether the campaign's timings may be printed here. "
    "The phase A rows are **warmed** (A102 (v5-campaign), plan §6): the evaluation child runs a "
    "discarded warm-up evaluation on the same entry, re-enters the entry bit-exact, resets the "
    "counters and times the measured evaluation, so the module rows carry no numba cache load; "
    "the fixed per-run term (process start to the warm-up's first evaluation) is stamped in every "
    "record and is not a row of the phase A table."
)


#: Where the appendix's wall-clock tables take their timings from (**D42**, the
#: user, 2026-09-30, on the validity check's result: "This is the reason why
#: these are in the appendix. Report them with the spread (as is done in table
#: format, matching count reporting, already). I will note that.").  The
#: campaign's own records, whatever the validity check reads; its outcome and
#: the one-worker repetitions' spread are printed beside the tables instead
#: of sending a phase to the one-worker pass (D38's remedy, not run).  The
#: other value, ``"validity"``, is D38's rule as A102 (v5-campaign) built it.
WALL_CLOCK_TIMINGS_FROM = "campaign"
WALL_CLOCK_TIMINGS_FROM_VALUES = ("campaign", "validity")


def wall_clock(campaign: Campaign) -> dict[str, Any]:
    """The three appendix tables' data over the campaign's two populations
    (``timing.tables_over``; the pairing key is the seed)."""
    from . import timing as timing_mod  # noqa: PLC0415

    source = wall_clock_source(campaign)
    # D41 (the user, 2026-09-30): the wall-clock tables are built the way the
    # count tables are.  Phase B is over the one seed set per configuration on
    # which every arm reached an accepted optimum (``_phase_b_groups``, the
    # count tables' own); phase A over every paired evaluation, as its count
    # table.  Without this the phase B table paired every finished run.
    seed_sets = {configuration: set(converged) for configuration, _by_arm, converged in _phase_b_groups(campaign)}
    records: list[Mapping[str, Any]] = []
    for phase, source_name, tally_phase in (("A", PHASE_A_SOURCE, tally_a.PHASE), ("B", PHASE_B_SOURCE, tally_b.PHASE)):
        if phase in source["phases_from_the_one_worker_pass"]:
            of_phase = list(timing_mod.seed_set_records(campaign, phase))
        else:
            of_phase = list(_population(campaign, source_name, tally_phase).records)
        if phase == "B":
            of_phase = [
                r for r in of_phase
                if int(r.get("campaign_seed")) in seed_sets.get(str(r.get("campaign_configuration")), set())
            ]
        records += of_phase
    tables = timing_mod.tables_over(campaign, records, key_of=lambda r: int(r.get("campaign_seed")))
    tables["source"] = source
    tables["workers_stamped"] = sorted(
        {str((r.get("launcher") or {}).get("workers")) for r in records if r.get("status") == "ok"}
    )
    return tables


def wall_clock_source(campaign: Campaign) -> dict[str, Any]:
    """Where the appendix timings come from, per phase (D38): the campaign's
    records, unless the validity stage's record found a campaign timing of the
    phase outside the W = 1 repetitions' range, in which case the one-worker
    timing pass over the seed set (``timing.seed_set``).  Refuses where the
    validity stage was never pressed: the tables would not say whether their
    timings may be printed (A102 (v5-campaign))."""
    from . import timing as timing_mod  # noqa: PLC0415

    validity = timing_mod.validity_record(campaign)
    if validity is None:
        raise PaperTablesError(
            "the timing validity stage has not been pressed (--timing validity): the wall-clock "
            "tables cannot say whether the campaign's timings may be printed (D38)"
        )
    if WALL_CLOCK_TIMINGS_FROM not in WALL_CLOCK_TIMINGS_FROM_VALUES:
        raise PaperTablesError(f"WALL_CLOCK_TIMINGS_FROM = {WALL_CLOCK_TIMINGS_FROM!r} is not one of {WALL_CLOCK_TIMINGS_FROM_VALUES}")
    outside = timing_mod.phases_outside(validity)
    return {
        "timings_from": WALL_CLOCK_TIMINGS_FROM,
        "phases_outside_the_repetitions_range": outside,
        "phases_from_the_one_worker_pass": outside if WALL_CLOCK_TIMINGS_FROM == "validity" else [],
        "validity_rows": list(validity.get("rows") or []),
        "validity_n_within": validity.get("n_within"),
        "validity_n_outside": validity.get("n_outside"),
        "validity_tree_git_head": validity.get("tree_git_head"),
    }


def _validity_lines(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    """The validity check's own rows, one per job: the W = 1 repetitions'
    range of Total, its spread, the campaign's Total of the same job and the
    factor between them.  Context beside the wall-clock tables (D42)."""
    if not rows:
        return []
    lines = [
        "**the validity check, per job** — One row per repeatability job (one seed per configuration and "
        "arm, both phases): Total over the three W = 1 repetitions as [min, max] with the spread "
        "(max − min over the median), the campaign's Total of the same job, and the campaign's Total "
        "over the repetitions' median. Phase A in ms per evaluation, phase B in s per optimisation.",
        "",
        "| phase | configuration | arm | seed | W = 1 repetitions [min, max] | spread | campaign | campaign / W = 1 median | within |",
        "|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for r in rows:
        reps = r.get("repetitions_total_s") or {}
        unit = 1000.0 if str(r.get("phase")) == "A" else 1.0
        lo, hi, med, camp = reps.get("min"), reps.get("max"), reps.get("median"), r.get("campaign_total_s")
        if None in (lo, hi, med) or not med:
            lines.append(f"| {r.get('phase')} | `{r.get('configuration')}` | {r.get('arm')} | {r.get('seed')} | — | — | — | — | — |")
            continue
        camp_cell = f"{camp * unit:.2f}" if camp is not None else "—"
        factor = f"{camp / med:.2f}" if camp is not None else "—"
        lines.append(
            f"| {r.get('phase')} | `{r.get('configuration')}` | {r.get('arm')} | {r.get('seed')} | "
            f"[{lo * unit:.2f}, {hi * unit:.2f}] | {100.0 * (hi - lo) / med:.1f} % | {camp_cell} | {factor} | "
            f"{'yes' if r.get('within_the_repetitions_range') else 'no'} |"
        )
    return lines + [""]


def _wall_clock_lines(campaign: Campaign) -> list[str]:
    from . import timing as timing_mod  # noqa: PLC0415

    tables = wall_clock(campaign)
    source = tables["source"]
    from_pass = source["phases_from_the_one_worker_pass"]
    source_line = (
        f"**Where these timings come from (D38).** The validity check (`--timing validity`, at "
        f"`{str(source['validity_tree_git_head'])[:8]}`) found {source['validity_n_within']} of the campaign's "
        f"timings of the repeatability seeds within the W = 1 repetitions' range and "
        f"{source['validity_n_outside']} outside. "
        + (
            "Phase " + " and ".join(from_pass) + " timings are therefore from the one-worker timing pass "
            "over the seed set (`--timing seed-set`: the campaign's jobs re-run at W = 1 with the timers on, "
            "every count identical to the campaign record's, a differing job refused); "
            if from_pass
            else (
                "Every timing is the campaign's own, made with several workers at once and reported with "
                "its spread (D42, the user, 2026-09-30: the one-worker pass D38 would send "
                + ("phase " + " and ".join(source["phases_outside_the_repetitions_range"]) if source["phases_outside_the_repetitions_range"] else "no phase")
                + " to is not run; the table below is the check's own rows); "
                if source["timings_from"] == "campaign"
                else "Every timing is the campaign's own; "
            )
        )
        + "the worker counts the records are stamped with: W = " + ", ".join(tables["workers_stamped"]) + ". "
        "Phase B is over the count tables' seed set (every arm at an accepted optimum; D41)."
    )
    lines = ["### Tables — wall clock (plan §6)", "", WALL_CLOCK_CONTEXT, "", source_line, ""]
    lines += _validity_lines(source["validity_rows"])
    for spec in WALL_CLOCK_TABLES:
        lines += [f"**{spec['title']}** — {spec['caption']}", ""]
    lines += timing_mod.render_markdown(
        tables,
        caption_w=(
            f"W = {', '.join(tables['workers_stamped'])} (as stamped); pairing key = the seed; the ratio is of the means over the "
            f"paired runs and the bracket the per-run ratio's median with [min, max]; exclusions "
            f"as stated above"
        ),
    )
    return lines


def per_arm_success(optimisation: Mapping[str, Mapping[str, Any]], campaign: Campaign) -> list[dict[str, Any]]:
    """The per-arm success table (plan §5 B5), read from the stage record.

    One block per configuration: the ``per-arm success`` table the
    optimisation tally emits — accepted optima of the starts offered, the
    other starts by outcome class, the seed set and the starts lost to one
    arm alone.  Reported, no expectation (item 3 as reduced).
    """
    blocks = []
    for config in campaign.configurations:
        found = [t for name, t in optimisation.items() if name.startswith(f"per-arm success — {config.name} — {PHASE_B_SOURCE}")]
        if not found:
            continue
        table = found[0]
        blocks.append({"configuration": config.name, "columns": [c["key"] for c in table["columns"]], "rows": list(table["rows"])})
    return blocks


#: The one verification table (plan §8): one row per check, in the plan's
#: order.  ``gate`` names the registry entry whose verdict the row reads
#: through the ``gate_table`` stage record; ``None`` marks a check that is not
#: a gate, whose cell is stated by :func:`verification` from the tally's
#: records where a construction exists and "not pressed" otherwise.
VERIFICATION_ROWS: tuple[tuple[str, str, str | None], ...] = (
    ("physics frozen", "G0", "g0prime"),
    ("switch neutrality", "G1", "switch_neutrality"),
    ("matched accuracy — whole-state audit at 0 components above τ", "A1", None),
    ("fixed-point distance between arms", "A2", None),
    ("same optimum, attributed where it fails", "B1", None),
    ("entry pairing", "G6", "entry_and_warm"),
    ("arm composition", "G5", "switch_composition"),
    ("output-path equivalence", "G9", "output_path"),
    ("the test set's teeth", "GT", "test_set"),
)


def _matched_accuracy_verdict(evaluation: Mapping[str, Mapping[str, Any]]) -> tuple[str, str]:
    """Plan §5 A1 on the tally's evaluation stage record: per configuration,
    the declared pair's whole-state similarity verdict (median and p90 within
    F; the `matched accuracy by configuration` table's cell on D34's pair)
    **and** 0 runs with a component above τ on both arms of the pair (the
    `matched accuracy` table's count column).  Returns (verdict, detail)."""
    by_configuration = [t for name, t in evaluation.items() if name.startswith("matched accuracy by configuration")]
    if not by_configuration:
        return "not pressed", "no `matched accuracy by configuration` table in the stage record"
    parts: list[str] = []
    verdicts: list[str] = []
    for row in by_configuration[0]["rows"]:
        configuration = str(row["configuration"])
        base = str(row["reference"])
        pair_verdict = str(row.get(f"A2_over_{base}_verdict") or "—")
        above: dict[str, Any] = {}
        for name, t in evaluation.items():
            if not name.startswith(f"matched accuracy — {configuration} — "):
                continue
            for r in t["rows"]:
                if r["arm"] in (base, "A2"):
                    above[r["arm"]] = r.get("n_runs_with_a_component_above_tau")
        clean = all(above.get(a) == 0 for a in (base, "A2")) if len(above) == 2 else None
        if pair_verdict not in ("PASS", "FAIL") or clean is None:
            verdict = "—"
        else:
            verdict = "PASS" if (pair_verdict == "PASS" and clean) else "FAIL"
        verdicts.append(verdict)
        parts.append(
            f"`{SHORT.get(configuration, configuration)}` A2/{base}: similarity {pair_verdict}, "
            f"runs with a component ≥ τ {base} {above.get(base)} / A2 {above.get('A2')} → **{verdict}**"
        )
    if not verdicts:
        return "not pressed", "the table has no configuration row"
    overall = "PASS" if all(v == "PASS" for v in verdicts) else ("FAIL" if "FAIL" in verdicts else "—")
    return overall, "; ".join(parts) + " (whole-state statistic, D36; the second half of the rule is the count column)"


def _exp(value: Any) -> str:
    return "—" if value is None else f"{float(value):.1e}"


def _same_optimum_verdict(optimisation: Mapping[str, Mapping[str, Any]]) -> tuple[str, str]:
    """Plan §5 B1 with its attribution, read from the optimisation tally's
    stage record (the `same optimum by rung` table): per configuration, each
    judged pair's verdict, and where the headline pair fails, how many of its
    seeds hop, the ladder step their difference enters at, and the steps that
    add nothing.  Returns (verdict, detail)."""
    found = [t for name, t in optimisation.items() if name == f"same optimum by rung — {PHASE_B_SOURCE}"]
    if not found:
        return "not pressed", "no `same optimum by rung` table in the stage record"
    by_configuration: dict[str, list[Mapping[str, Any]]] = {}
    for r in found[0]["rows"]:
        by_configuration.setdefault(str(r["configuration"]), []).append(r)
    passed: list[str] = []
    failed: list[str] = []
    parts: list[str] = []
    for configuration, rows in by_configuration.items():
        short = SHORT.get(configuration, configuration)
        judged = [r for r in rows if r["role"] == "judged"]
        if not judged:
            continue
        verdicts = ", ".join(f"{str(r['pair']).split(' (')[0]} {r['verdict']}" for r in judged)
        headline = judged[-1]
        if all(r["verdict"] == "PASS" for r in judged):
            passed.append(short)
            parts.append(
                f"`{short}` {verdicts} (objf p90 {_exp(headline['r_p90'])} ≤ {_exp(headline['threshold_p90'])}; "
                f"{headline['hops']} hops of {headline['n']})"
            )
            continue
        failed.append(short)
        text = (
            f"`{short}` {verdicts} at {headline['fails_at']} (objf p90 {_exp(headline['r_p90'])} > "
            f"{_exp(headline['threshold_p90'])}): {headline['hops']} hops of {headline['n']} "
            f"({headline['across_clusters']} across clusters; seeds {headline['hop_seeds']}), entering at "
            f"{headline['hops_enter_at']}"
        )
        quiet = [r for r in rows if r["role"] == "step" and not r["hops"]]
        for r in quiet:
            text += (
                f"; {r['pair']} adds none: objf median {_exp(r['r_median'])}, p90 {_exp(r['r_p90'])}, "
                f"same path on {r['same_path']} of {r['n']}"
            )
        if " (" in str(headline["pair"]):
            text += f" — {str(headline['pair']).split(' (', 1)[1][:-1]}"
        if headline.get("yardstick_hops_too") not in (None, "—"):
            text += f"; the yardstick BR → B0 also hops on {headline['yardstick_hops_too']} of these seeds"
        parts.append(text)
    if not parts:
        return "not pressed", "the table has no judged row"
    verdict = " · ".join(
        x for x in (
            ("PASS " + ", ".join(passed)) if passed else "",
            ("FAIL " + ", ".join(failed)) if failed else "",
        ) if x
    )
    return verdict, (
        "; ".join(parts)
        + " (hop: objective difference above the floor; * = a retried arm; the tally's "
        "`same optimum by rung` table, plan §5 B1)"
    )


def verification(
    records_dir: Path,
    optimisation: Mapping[str, Mapping[str, Any]],
    evaluation: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """The verification table's rows, every gate verdict read from the
    ``gate_table`` stage record after :func:`assert_gate_table_current`;
    A1 from the evaluation tally's stage record (D36), B1 from the
    optimisation tally's."""
    current = assert_gate_table_current(records_dir)
    table = stage_record(records_dir, GATE_TABLE_SECTION.stage)
    by_gate = {row["gate"]: row for row in table.get("rows") or []}
    rows: list[dict[str, Any]] = []
    for check, label, gate in VERIFICATION_ROWS:
        row: dict[str, Any] = {"check": check, "label": label, "gate": gate}
        if gate is not None:
            found = by_gate.get(gate)
            if found is None:
                row.update(verdict="not pressed", detail=f"`{gate}` is not in the gate table")
            elif found.get("verdict") == "NOT RUN":
                row.update(verdict="not pressed", detail=f"`{gate}` has no verdict record")
            else:
                teeth = f"{found.get('n_teeth_tripped')}/{found.get('n_teeth')} teeth"
                compared = found.get("n_compared")
                mismatched = found.get("n_mismatched")
                counts = f"{mismatched} of {compared} mismatched" if compared is not None else str(found.get("population") or "")[:80]
                head = str(found.get("tree_git_head") or "")[:8]
                row.update(verdict=str(found.get("verdict")), detail=f"`{gate}` at `{head}`: {counts}; {teeth}")
        elif label == "B1":
            verdict, detail = _same_optimum_verdict(optimisation)
            row.update(verdict=verdict, detail=detail)
        elif label == "A2":
            row.update(verdict="reported, no rule", detail="the tally's fixed-point distance table (plan §5 A2)")
        elif label == "A1":
            if evaluation is None:
                row.update(verdict="not pressed", detail="no evaluation stage record handed to the verification")
            else:
                verdict, detail = _matched_accuracy_verdict(evaluation)
                row.update(verdict=verdict, detail=detail)
        else:
            row.update(verdict="not pressed", detail="no construction for this row")
        rows.append(row)
    return {"rows": rows, "records_read": current}


# --------------------------------------------------------------------------
# the comparison with the stage records
# --------------------------------------------------------------------------


def _stage_tables(records_dir: Path, stage: str) -> dict[str, Mapping[str, Any]]:
    path = Path(records_dir) / stage / "measurements.json"
    if not path.exists():
        raise PaperTablesError(f"{path} is not present; nothing to compare against")
    return {t["table"]: t for t in json.loads(path.read_text())["tables"]}


def _stage_table(tables: Mapping[str, Mapping[str, Any]], prefix: str) -> Mapping[str, Any]:
    found = [t for name, t in tables.items() if name.startswith(prefix)]
    if len(found) != 1:
        raise PaperTablesError(f"{len(found)} stage table(s) named {prefix!r}…; expected exactly one")
    return found[0]


def cross_check(
    built: Mapping[str, Any],
    evaluation: Mapping[str, Mapping[str, Any]],
    optimisation: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Every cell the stage records also hold, compared exactly.

    Phase A: each single-group row's per-arm mean against the tally's module
    sweeps table (``module sweeps per run — <configuration> —
    campaign_displaced``), and — since D34's pair is the tally's own reference
    (`A1` on a pulsed configuration, `A0` on `st`) — the pooled ratio and the
    pair count too, where the stage's reference is the pair's base.  Phase B:
    the iteration row's arm means, pooled ratio, median, bracket and n against
    the optimiser's path table; each single-group module row's arm means
    (before the exit audit is taken out) and pair count against the module
    sweeps table.  Floats are compared with ``==``.
    """
    compared = 0
    mismatches: list[str] = []

    def same(where: str, mine: Any, theirs: Any) -> None:
        nonlocal compared
        compared += 1
        if mine != theirs:
            mismatches.append(f"{where}: paper {mine!r}, stage {theirs!r}")

    for block in built["phase_a"]:
        c = block["configuration"]
        table = _stage_table(evaluation, f"module sweeps per run — {c} — {PHASE_A_SOURCE}")
        stage_rows = {r["module"]: r for r in table["rows"]}
        for row in block["rows"]:
            present = [g for g in row["groups"] if g in stage_rows]
            if len(present) != 1:
                continue
            theirs = stage_rows[present[0]]
            for a in tally_a.LADDER:
                same(f"A {c} {row['row']} {a} mean", row[a], theirs.get(f"{a}_mean"))
            if theirs.get("reference") == block["pair"][0] and row["summary"]:
                same(f"A {c} {row['row']} pooled", row["summary"]["pooled"], theirs.get("ratio"))
                same(f"A {c} {row['row']} pairs", row["summary"]["n"] + row["summary"]["n_dropped"], theirs.get("n_pairs"))

    path = _stage_table(optimisation, f"the optimiser's path over the configurations — {PHASE_B_SOURCE}")
    by_config = {r["configuration"]: r for r in path["rows"] if r["quantity"] == ITERATIONS_LABEL}
    for row in built["phase_b_iterations"]:
        c = row["configuration"]
        theirs = by_config.get(c)
        if theirs is None:
            mismatches.append(f"B {c} iterations: no stage row")
            continue
        same(f"B {c} iterations n", row["n"], theirs.get("n"))
        for a in tally_b.LADDER:
            same(f"B {c} iterations {a}", row[a], theirs.get(a))
        s = row["summary"]
        same(f"B {c} iterations pooled", s["pooled"], theirs.get("ratio_pooled"))
        same(f"B {c} iterations median", s["median"], theirs.get("ratio_median"))
        same(f"B {c} iterations bracket", _stage_bracket(s), theirs.get("ratio_bracket"))

    for block in built["phase_b_modules"]:
        c = block["configuration"]
        table = _stage_table(optimisation, f"module sweeps per run — {c} — {PHASE_B_SOURCE} ·")
        stage_rows = {r["module"]: r for r in table["rows"]}
        for row in block["rows"]:
            present = [g for g in row["groups"] if g in stage_rows]
            if len(present) != 1:
                continue
            theirs = stage_rows[present[0]]
            for a in tally_b.LADDER:
                same(f"B {c} {row['row']} {a} mean", row[f"{a}_measured"], theirs.get(f"{a}_mean"))
            same(f"B {c} {row['row']} pairs", row["summary"]["n"], theirs.get("n_pairs"))
    return {"compared": compared, "mismatched": len(mismatches), "mismatches": mismatches}


def _cross_check_tooth(
    built: Mapping[str, Any],
    evaluation: Mapping[str, Mapping[str, Any]],
    optimisation: Mapping[str, Mapping[str, Any]],
) -> bool:
    """True if the comparison catches one altered cell on each side it reads."""
    bites = []
    for phase, key in (("phase_a", "A2"), ("phase_b_iterations", "B2"), ("phase_b_modules", "B2_measured")):
        doctored = copy.deepcopy(dict(built))
        target = doctored[phase][0]
        target = target["rows"][0] if "rows" in target else target
        target[key] = (target[key] or 0.0) + 1.0
        bites.append(cross_check(doctored, evaluation, optimisation)["mismatched"] > 0)
    return all(bites)


# --------------------------------------------------------------------------
# the page
# --------------------------------------------------------------------------


#: The rounding, one rule per table (the user, 2026-09-28), set by the size of
#: each quantity's sampling uncertainty over the campaign's starts — the counts
#: themselves are exact: phase A means and iterations to one decimal, every
#: ratio, median and bracket to two decimals, phase B module sweeps as integers
#: (the user: *"just round to integers"*).  The comparison with the stage
#: records reads the raw values.
RATIO_DECIMALS = 2
MEAN_DECIMALS = 1


def decimals(value: Any, places: int) -> str:
    if value is None:
        return "—"
    return f"{float(value):.{places}f}"


def sig(value: Any) -> str:
    return decimals(value, RATIO_DECIMALS)


def mean_1dp(value: Any) -> str:
    return decimals(value, MEAN_DECIMALS)


def _stage_bracket(s: Mapping[str, Any] | None) -> str:
    """The bracket as the stage tables spell it, for the comparison only."""
    if not s or s.get("min") is None:
        return "—"
    return f"[{s['min']:.3f}, {s['max']:.3f}]"


def _bracket(s: Mapping[str, Any] | None) -> str:
    if not s or s.get("min") is None:
        return "—"
    return f"[{sig(s['min'])}, {sig(s['max'])}]"


def _median_bracket(s: Mapping[str, Any] | None) -> str:
    if not s or s.get("median") is None:
        return "—"
    return f"{sig(s['median'])} {_bracket(s)}"


def _n_text(n_per_arm: Mapping[str, int]) -> str:
    counts = sorted(set(n_per_arm.values()))
    if len(counts) == 1:
        return str(counts[0])
    return ", ".join(f"{a} {n}" for a, n in n_per_arm.items())


def _tex(text: str) -> str:
    return text.replace("—", "--").replace("→", "$\\rightarrow$")


def _module_lines(
    blocks: Sequence[Mapping[str, Any]], ladder: Sequence[str], pair_of, n_of, mean
) -> tuple[list[str], list[str]]:
    md: list[str] = []
    tex: list[str] = []
    for block in blocks:
        c = block["configuration"]
        base, arm = pair_of(block)
        ratio_head = f"{arm}/{base}"
        md += [
            f"**`{SHORT.get(c, c)}`** ({c}, n = {n_of(block)}; pair {base} → {arm})",
            "",
            f"| Module | {' | '.join(ladder)} | {ratio_head} | {ratio_head} med [min, max] |",
            "|---|" + "---:|" * len(ladder) + "---:|---:|",
        ]
        tex += [
            f"\\multicolumn{{{len(ladder) + 3}}}{{l}}{{\\texttt{{{SHORT.get(c, c)}}} ($n = {n_of(block)}$, {ratio_head})}} \\\\",
            "\\hline",
        ]
        for row in block["rows"]:
            cells = [str(row[f"{a}_exact"]) if f"{a}_exact" in row else mean(row[a]) for a in ladder]
            s = row["summary"]
            md.append(f"| {row['row']} | {' | '.join(cells)} | {sig(s and s['pooled'])} | {_median_bracket(s)} |")
            tex.append(_tex(f"{row['row']:<15} & {' & '.join(cells)} & {sig(s and s['pooled'])} & {_median_bracket(s)} \\\\"))
        tex.append("\\hline")
        md.append("")
    return md, tex


def _groups_note(blocks: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = []
    for block in blocks:
        g = block["groups"]
        ff = [n for k in ("PULSE", "FF") for n in g.get(k, [])]
        post = g.get(stats_mod.ONCE_PER_RUN_GROUP, [])
        lines.append(
            f"- `{SHORT.get(block['configuration'], block['configuration'])}`: "
            f"Feedforward = {', '.join(f'`{n}`' for n in ff) or '— (none)'}; "
            f"Post-processing = {', '.join(f'`{n}`' for n in post) or '— (none)'}"
        )
    return lines


#: Objective names the table prints shorter than the stage record states them.
OBJECTIVE_SHORTER = {"Plasma major radius": "Major radius"}


def _case_lines(rows: Sequence[Mapping[str, Any]], *, md: bool) -> list[str]:
    out = []
    for r in rows:
        c = r["configuration"]
        short = SHORT.get(c, c)
        name = f"{FULL.get(c, c)} (`{short}`)" if md else f"{FULL.get(c, c)} (\\texttt{{{short}}})"

        def code(name: str) -> str:
            return f"`{name}`" if md else f"\\texttt{{{name.replace('_', '\\_')}}}"

        name_of = str(r["objective"]).split(" (")[0]
        name_of = OBJECTIVE_SHORTER.get(name_of, name_of)
        sense = {"minimise": "min.", "maximise": "max."}[str(r["sense"])]
        objective = f"{sense} {name_of[:1].lower()}{name_of[1:]} ({code(r['objective_variable'])})"
        variables = f"{r['nvar']} → {r['nvar_lifted']}" if r["nvar"] != r["nvar_lifted"] else str(r["nvar"])
        total, total_lifted = (int(str(r[k]).split()[0]) for k in ("constraints", "constraints_lifted"))
        constraints = f"{total} → {total_lifted}" if total != total_lifted else str(total)
        coupling = code(r["lifted_variable"]) if r["pulsed_bool"] else "none (steady state)"
        if md:
            out.append(f"| {name} | {r['models']} | {objective} | {variables} | {constraints} | {coupling} |")
        else:
            cells = [name, str(r["models"]), objective, variables, constraints, coupling]
            cells = [x.replace("→", "$\\rightarrow$").replace("₀", "$_0$").replace("ₚₗₐₛₘₐ", "$_\\mathrm{plasma}$") for x in cells]
            out.append(" & ".join(cells) + " \\\\")
    return out


def _tabular(kind: str, rows: Sequence[str], *, ratio_head: str = "") -> list[str]:
    """The rows inside the paper's ``tabular``, with its column spec and header
    (the column specs are the paper's own, ``3 results.tex``)."""
    spec, header = {
        "A": ("l|rrrr|rc", f"Module & AR & A0 & A1 & A2 & {ratio_head} & {ratio_head} med [min, max]"),
        "I": ("l|rrrr|rc", "Configuration & BR & B0 & B1 & B2 & B2/B0 & B2/B0 med [min, max]"),
        "B": ("l|cccc|cc", "Module & BR & B0 & B1 & B2 & B2/B0 & B2/B0 med [min, max]"),
    }[kind]
    body = list(rows)
    if kind == "I":
        body = [*body, "\\hline"]
    return [f"\\begin{{tabular}}{{{spec}}}", "\\hline", f"{header} \\\\", "\\hline", *body, "\\end{tabular}"]


def switch_matrix_lines(campaign: Campaign) -> tuple[list[str], list[str]]:
    """The switch matrix, from the same data every arm is composed from; the
    stopping-rule row reads the campaign's test set and τ (``arms.matrix``
    with the campaign), never a typed cell."""
    order = list(arms_mod.MATRIX_ORDER)
    md = [f"| | {' | '.join(f'**{a}**' for a in order)} |", "|---|" + "---|" * len(order)]
    tex = [f"\\begin{{tabular}}{{l|{'c' * len(order)}}}", "\\hline", " & " + " & ".join(order) + " \\\\", "\\hline"]
    for row, cells in arms_mod.matrix(campaign).items():
        md.append(f"| {row} | {' | '.join(str(c) for c in cells)} |")
        tex.append(_tex(f"{row} & " + " & ".join(str(c).replace('✓', '$\\checkmark$').replace('τ', '$\\tau$') for c in cells) + " \\\\"))
    tex += ["\\hline", "\\end{tabular}"]
    return md, tex


def render(campaign: Campaign, records_dir: Path) -> dict[str, Any]:
    """The page, and the comparisons it was written under."""
    a = phase_a(campaign)
    iterations, modules = phase_b(campaign)
    built = {"phase_a": a, "phase_b_iterations": iterations, "phase_b_modules": modules}
    evaluation = _stage_tables(records_dir, "tally_evaluation")
    optimisation = _stage_tables(records_dir, "tally_optimisation")
    case_rows = cases(campaign, optimisation)
    success = per_arm_success(optimisation, campaign)
    verified = verification(records_dir, optimisation, evaluation)
    check = cross_check(built, evaluation, optimisation)
    tooth = _cross_check_tooth(built, evaluation, optimisation)
    marker = population_marker(campaign, records_dir)
    commits = ", ".join(f"`{h[:8]}`" for h in marker["records_by_commit"]) or "—"
    configurations = [c.name for c in campaign.configurations]

    lines = [
        "# Paper tables — Case 2: PROCESS",
        "",
        "> **Document status** — **GENERATED, never hand-edited.** Written whole by "
        "`harness/measurement/paper_tables.py` (`experiment_runner.py --paper-tables write`) "
        "from the campaign's run records and the stage records, and compared whole by "
        "`--paper-tables check`, which refuses when this file and the records disagree. "
        "The one document of V5 list item 10: the main-text tables of "
        "`Structuring-fusion-MDAO-with-DSMs/3 results.tex` and the appendix tables of the V5 "
        "plan §8; each table is a Markdown grid and, where the paper prints it, LaTeX rows for "
        "the paper's `tabular` body.",
        "",
        f"*Over the **campaign** population — {marker['n_run_records']} run records at "
        f"{commits}; sources `{PHASE_A_SOURCE}` (phase A) and `{PHASE_B_SOURCE}` (phase B); "
        f"the exit audit at position(s) {', '.join(f'`{p}`' for p in marker['audit_positions'])} "
        f"on the ruler(s) {', '.join(f'`{r}`' for r in marker['predicate_modes'])}.*",
        "",
        "**Conventions.** A module cell is that module's **sweeps per run** — per `call_models` "
        "evaluation in phase A, per whole optimisation in phase B — averaged over the arm's n "
        "runs. Every model node of a module runs once per sweep, so a sweep ratio does not depend "
        "on whether one counts model calls or DSM rows. The ratio column is the **ratio of the "
        "means** (Σ intervened / Σ control over the paired runs); the next column is the per-run "
        "ratio's median with its [min, max]. **The phase A pair is `A2/A1` on the pulsed "
        "configurations and `A2/A0` on `st` (D34)**: the comparison at matched accuracy and the "
        "same fixed point; phase B's is `B2/B0`. **Feedforward** is the pulse node and the "
        "feed-forward tail (run once per evaluation after M3, no iteration); **Post-processing** "
        "is the once-per-run set — nodes no objective or constraint depends on, which the "
        "partitioned arm defers. **`A2`'s Post-processing cell is measured, not charged**: V4 "
        "charged it 1 by construction (`CHARGED_ONCE`, retired); since item 5's driver change "
        "(A101, D35) the run executes the deferred set once after convergence and the census "
        "counts it, so the cell reads the measured 1. There is **no total row**: sweeps of "
        "different modules do not add. "
        "Rounding: phase A sweep means and phase B iteration means to one decimal, phase B module "
        "sweeps to integers, every ratio, median and bracket to two decimals; `A2`'s phase A "
        "Feedforward and Post-processing cells are the one integer every run reads (checked). "
        "`—` is a group that does not exist on the configuration or an arm inactive there "
        "(`A1`/`B1` on `st`).",
        "",
        "Node groups per configuration (phase A; phase B's are restated in its section only where "
        "they differ):",
        "",
        *_groups_note(a),
        "",
        f"**Comparison with the stage records.** {check['compared']} cells these tables share with "
        f"the tally's stage records compared exactly — phase A's per-arm means and, on D34's pair "
        f"(the tally's own reference), its pooled ratios and pair counts; phase B's iteration "
        f"cells and its module means before the exit audit is taken out: "
        f"**{check['mismatched']} mismatched of {check['compared']}**; the comparison caught a "
        f"doctored cell on each of the three sides: **{'yes' if tooth else 'NO'}**.",
        "",
        "## Main text",
        "",
        "### Table — the switch matrix",
        "",
        "One column per arm, one row per switch, from `harness/experiment/arms.py`'s matrix — the "
        "data every arm is composed from, printed rather than transcribed. `⁺`-marked rows are "
        "pulsed configurations only; on `st` the arms `A1`/`B1` compose to `A0`/`B0`.",
        "",
    ]
    md, tex = switch_matrix_lines(campaign)
    lines += md + ["", "```latex", *tex, "```", ""]

    lines += [
        "### Table — how the three configurations differ",
        "",
        "One row per configuration. Objective, design variables and constraints are the tally's "
        "problem-definition table (the runs' own stamps); `a → b` is the flat arms (`BR`, `B0`) → "
        "the arms with the burn time taken out of the MDA (`B1`, `B2`), which add the burn time as "
        "an iteration variable and its consistency constraint. The objective's variable and the "
        "cross-module coupling's variable are derived from the committed per-run artifact and the "
        "runs. Models is the committed node map's collapsed-DSM rows executed in a sweep "
        "(`units.dsm_rows.executed_in_a_sweep`), the constraints evaluation's row included (D40).",
        "",
        "| Configuration | Models | Objective | Design var. | Constraints | Cross-module coupling |",
        "|---|---:|---|---:|---:|---|",
        *_case_lines(case_rows, md=True),
        "",
        "```latex",
        "\\begin{tabular}{l|c|l|c|c|l}",
        "\\hline",
        "Configuration & Models & Objective & Design var. & Constraints & Cross-module coupling \\\\",
        "\\hline",
        *_case_lines(case_rows, md=False),
        "\\hline",
        "\\end{tabular}",
        "```",
        "",
        "### Table `tab:phaseA_results` — phase A, module sweeps per evaluation",
        "",
        "Mean sweeps of each module in one `call_models` evaluation over the n displaced-entry runs "
        "per arm; the ratio is of the means over the runs both arms of the pair finished — "
        "`A2/A1` on the pulsed configurations, `A2/A0` on `st` (D34).",
        "",
    ]
    md, tex = _module_lines(a, tally_a.LADDER, lambda b: tuple(b["pair"]), lambda b: _n_text(b["n_per_arm"]), mean_1dp)
    lines += md + ["```latex", *_tabular("A", tex, ratio_head="A2/A1 (A2/A0 on st)"), "```", ""]

    lines += [
        "### Table `tab:phaseB_iterations` — phase B, optimiser iterations",
        "",
        "Mean optimiser iterations per run, summed over the optimiser's retry attempts, over the n "
        "seeds on which every arm reached an accepted optimum; `B2/B0` is the ratio of the means.",
        "",
        "| Configuration | n | BR | B0 | B1 | B2 | B2/B0 | B2/B0 med [min, max] |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    tex = []
    for row in iterations:
        c = row["configuration"]
        cells = [mean_1dp(row[x]) for x in tally_b.LADDER]
        s = row["summary"]
        lines.append(f"| `{SHORT.get(c, c)}` | {row['n']} | {' | '.join(cells)} | {sig(s['pooled'])} | {_median_bracket(s)} |")
        tex.append(_tex(f"\\texttt{{{SHORT.get(c, c)}}} ($n = {row['n']}$) & {' & '.join(cells)} & {sig(s['pooled'])} & {_median_bracket(s)} \\\\"))
    lines += ["", "```latex", *_tabular("I", tex), "```", ""]

    lines += [
        "### Table `tab:phaseB_results` — phase B, module sweeps per optimisation",
        "",
        "Mean sweeps of each module over one whole optimisation, rounded to integers. Every attempt "
        "and the output path, which is architecture (MDA_Output's sweeps in `BR`/`B0`, none in "
        "`B1`, the deferred nodes' one execution in `B2`). The exit audit's one sweep of every node "
        "is the harness's accuracy instrument and is **subtracted** (1 per node, checked on each run "
        "against the record's `audit_node_calls`; D36). Over the n seeds on which every arm reached "
        "an accepted optimum; `B2/B0` is the ratio of the means.",
        "",
    ]
    if any(b["groups"] != x["groups"] for b, x in zip(modules, a)):
        lines += ["Node groups (phase B):", "", *_groups_note(modules), ""]
    md, tex = _module_lines(modules, tally_b.LADDER, lambda b: PHASE_B_PAIR, lambda b: b["n"], lambda v: decimals(v, 0))
    lines += md + ["```latex", *_tabular("B", tex), "```", ""]

    lines += ["## Appendix", ""]
    lines += _wall_clock_lines(campaign)

    lines += [
        "### Table — per-arm success",
        "",
        "Per configuration and arm: the starts offered, the accepted optima (`status == ok`, "
        "`ifail == 1`), the other starts by outcome class, the one seed set every phase B table is "
        "over, and the starts lost to this arm alone. Reported, no expectation (plan §5 B5; item 3 "
        "as reduced). The tally's `per-arm success` table, republished.",
        "",
    ]
    for block in success:
        c = block["configuration"]
        cols = block["columns"]
        lines += [f"**`{SHORT.get(c, c)}`** ({c})", "", f"| {' | '.join(cols)} |", "|" + "---|" * len(cols)]
        for r in block["rows"]:
            lines.append("| " + " | ".join(str(r.get(k, "")) for k in cols) + " |")
        lines.append("")

    lines += [
        "### Table — verification",
        "",
        "One row per check of plan §8, in its order. A gate's verdict is read from its record "
        "through the `gate_table` stage record, which this generator refuses when the verdict "
        "records have been re-made, removed or added to since the stage ran; `not pressed` is a "
        "gate with no verdict record (a declared placeholder that refuses, or one never pressed) "
        "or a rule that is not yet a construction. A verdict is PASS only with every tooth tripped.",
        "",
        f"*{verified['records_read']}*",
        "",
        "| check | plan | verdict | detail |",
        "|---|---|---|---|",
    ]
    for r in verified["rows"]:
        lines.append(f"| {r['check']} | {r['label']} | **{r['verdict']}** | {r['detail']} |")
    lines.append("")

    return {"markdown": "\n".join(lines), "cross_check": check, "tooth": tooth, "built": built, "verification": verified}


def paper_path(campaign: Campaign) -> Path:
    """Beside ``EXPERIMENT_REPORT.md`` — the experiment folder, whatever runs dir is read."""
    return Path(__file__).resolve().parents[2] / PAPER_NAME


def _refuse_on_mismatch(result: Mapping[str, Any]) -> None:
    check = result["cross_check"]
    if check["mismatched"] or not result["tooth"]:
        raise PaperTablesError(
            f"the comparison with the stage records failed: {check['mismatched']} "
            f"of {check['compared']} mismatched, tooth "
            f"{'bites' if result['tooth'] else 'DOES NOT BITE'}; first: {check['mismatches'][:3]}"
        )


def write(campaign: Campaign, records_dir: Path, *, path: Path | None = None) -> dict[str, Any]:
    """Render, refuse on a cross-check mismatch, write the file (``paper_path``
    unless *path* names another — a render into a runs directory, as a check
    against test data that must not become the committed document)."""
    result = render(campaign, records_dir)
    _refuse_on_mismatch(result)
    out = Path(path) if path is not None else paper_path(campaign)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(result["markdown"] + "\n")
    return {**result, "path": str(out), "written": True}


def check(campaign: Campaign, records_dir: Path, *, path: Path | None = None) -> dict[str, Any]:
    """Render and **refuse** unless the file on disk is byte-identical to the
    rendering and the cross-check passes (item 10: ``check`` refuses when the
    rendered file and the records disagree)."""
    result = render(campaign, records_dir)
    _refuse_on_mismatch(result)
    out = Path(path) if path is not None else paper_path(campaign)
    committed = out.read_text() if out.exists() else ""
    identical = committed == result["markdown"] + "\n"
    if not identical:
        raise PaperTablesError(
            f"{out} does not match what the records now produce"
            + ("" if out.exists() else " (the file does not exist)")
            + "; `--paper-tables write` renders it again.  Nothing was written."
        )
    return {**result, "path": str(out), "identical": True}


def report(result: Mapping[str, Any]) -> None:
    check_ = result["cross_check"]
    print(
        f"  cross-check with the stage records: {check_['mismatched']} mismatched "
        f"of {check_['compared']} compared; tooth {'bites' if result['tooth'] else 'DOES NOT BITE'}"
    )
    for line in check_["mismatches"][:10]:
        print(f"    {line}")
    for row in result.get("verification", {}).get("rows", []):
        print(f"  verification {row['label']:<3} {row['verdict']:<18} {row['check']}")
    if "identical" in result:
        print(f"  {result['path']}: {'IDENTICAL' if result['identical'] else 'DIFFERS'}")
    if result.get("written"):
        print(f"  written: {result['path']}")
